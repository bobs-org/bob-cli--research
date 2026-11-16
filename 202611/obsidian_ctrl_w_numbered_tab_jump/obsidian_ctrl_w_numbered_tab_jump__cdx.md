# Numbered Obsidian tabs: a direct destination inside the Ctrl+W family

Researcher: **cdx** · 2026-11-16 · Independent research for the five-researcher swarm.

**Recommendation:** add window-wide tab addressing to the existing Bob window prefix. Put small, persistent number hints immediately before each tab title, emphasize them while Ctrl+W is armed, and focus the exact existing tab in its existing split. Reuse the prefix, layout adapter, and hint painter already implemented for `bob-cli-m0`.

The idea is good for Bryan's visible, spatial workspace. Its main weakness is the assumption that an arbitrary decimal number can also be an immediate single-key command. I recommend **1–9 as immediate literal destinations, plus `0` to open an exact-number chooser for every tab**. Thus tab 4 is `Ctrl+W 4`; tab 12 is `Ctrl+W 0 12 Enter`. This is an explicit adjustment to the requested syntax for destinations above nine, discussed below. Never make 9 mean “last,” and never wait on a typing timeout to distinguish 1 from 12.

## Evidence and limits

I read the `bob-cli-m0` epic through `sase bead read`, its approved plan through `sase artifact read`, and the current linked `bob-plugins` source. I did not consult any report, transcript, or findings from the other four researchers in this swarm.

The inspected Bob plugin revision is `0e16e304142f94c70c78357f7bdfe4ded19d0db5`. The epic was still marked in progress when read, although all six phase beads were closed; the report therefore describes the inspected implementation, not a claim that the epic had completed landing. Its existing documentation already explains arming restrictions, held-Ctrl suffixes, cancellation, Linux behavior, and the visual hint. [S1][S2]

I independently inspected the official Obsidian API repository at `879c936660fcc45c90ee28ea6b4ef7068006477c` (package version 1.14.4), and Pane Relief at `646034ad2af6256fe8764e51668b588359185702`. The prior Bob plan names Obsidian 1.15.1 as its real-app test target; API declarations alone do not establish every runtime detail on that build. [S1][S7][S8]

**Verification performed:** the five existing window-prefix model, action, input, command, and hint-view test files pass: 62 tests, exit 0. A direct call to the existing key normalizer confirms ordinary digits, held-Ctrl digits, and numpad digits are currently consumed as unmapped suffixes. No implementation changes were made. I did not run a live Obsidian session or test the proposed badge design against themes; those remain acceptance work, not demonstrated results.

## What the existing feature gives us

The approved prefix deliberately reserved digits for later. Its current verbs are `h/l` for neighboring split focus, `w` for cycling splits, `H/L` for moving the current tab, and `v` for splitting the current note. Physical Ctrl is intentional; this is not a Command-on-Mac substitution. Window navigation does not add a Bob Ctrl+O jump. [S1][S2]

The implementation already supplies:

- A pure snapshot of split identities, geometry, leaf identities, titles, pin state, and selection; a reading-order helper sorts splits by horizontal position, then vertical position. [S3]
- A live adapter with stable identities for leaf objects and a `focusWindowPrefixLeaf` method using `workspace.setActiveLeaf(leaf, {focus: true})`. [S4]
- One temporary Obsidian `Scope`, a queue, repeat/composition guards, cancellation, a ring, a delayed card, and success feedback. The normal hint delay is 300 ms. [S3][S5]
- A persistent underline identifying the focused split, plus a real-Obsidian scratch-vault harness. [S6][S10]

This is a small extension of a coherent interaction system, but it is more than adding nine entries to a key table. The new responsibility is maintaining a truthful association among **the painted hint, the selected number, and the leaf object**.

Obsidian itself documents numbered shortcuts for tabs, including the browser convention that 9 selects the last tab. Pane Relief independently provides window-level numbered navigation and optional numbering, also treating 9 as last. Those are useful precedents, not exact matches for a literal Nth-tab requirement. [S8][S9]

## Resolve the product contract first

**Scope: number tabs across the main window's central area.** Each tab gets a unique ordinal across all eligible splits. Do not restart at 1 in every split. Otherwise pressing 3 from the left side could never identify the third tab visible on the right without an additional split-selection step.

“Vertical window” should mean the tab's existing **tab group**, not an operating-system window or a note path. A jump selects a destination leaf and gives its content keyboard focus. It changes neither the leaf's parent nor its position among siblings. Focus is allowed to cross splits; the tab itself stays put. Obsidian's own terminology distinguishes tabs, tab groups, and popout windows. [S7][S9]

Number all main-area tabs, including pinned tabs, two instances of the same file, PDFs, Canvas, graph, and empty tabs. File-only numbering would leave unexplained gaps in the visible strip and make unrelated view types change the interpretation of “Nth tab.” Use each leaf's display title; a file is not the identity of a tab.

Exclude sidebars, hover editors, mobile, and popouts for this iteration, matching the existing prefix boundary. Keep ordinary stacked tabs eligible if the adapter can identify their order and paint their header correctly; an unsupported theme or stacking presentation must have a visible chooser fallback. Never exclude an inactive tab just because its content element is hidden.

**Order: spatial groups, then tabs within each group.** For the intended side-by-side layout, walk the left split's tab strip left to right, then the next split. Reuse the existing split ordering so `w` and numeric hints tell the same story. Its exact nested-layout order is column-first: left coordinate, then top coordinate. Do not casually describe that as row-major reading order. Tabs within a group follow their actual visual/model order, including pins in their current positions. [S3][S4]

Do not use title sorting, MRU order, or permanently allocated numeric IDs. Changing focus must never renumber tabs. Opening, closing, moving, or reordering tabs may change positional ordinals, but only between gestures. The model's stable object ID and the user's positional number are different things.

Example adapted from the workspace described in the approved epic plan:

```text
Left split                                  Right split
[1 20261115] [2 dash] [3 sase_blog*]       |   [4 sase_blog_contents']

Ctrl+W 4

[1 20261115] [2 dash] [3 sase_blog']       |   [4 sase_blog_contents*]
```

Here `*` means focused; `'` means selected in an unfocused split. The lists, widths, pins, and leaf objects are unchanged. Only the destination selection and keyboard focus change.

## Is this the right approach?

**Yes, for visually locating an already-open tab.** The gesture matches the existing window-navigation family, avoids reaching for the mouse, and turns recognition of a title into a short deterministic action. It is particularly useful for the two-split arrangement that motivated the epic. It also separates two intentions cleanly: lowercase/navigation keys focus; existing uppercase move keys carry a tab.

It is less useful when the target is buried among dozens of clipped tabs. Numbers still require a visual search, and positional numbers change when earlier tabs close. For that workload, an open-tab picker searchable by title is the better primary interface. This feature should complement such a picker and ordinary previous/next-tab navigation; it should not become a general tab-management application.

| Approach | Main benefit | Main cost | Judgment |
| --- | --- | --- | --- |
| One ordinal across the main window | One destination, regardless of current split | Closing an early tab shifts later numbers | Recommended for this request |
| Restart numbers in each split | Short, locally stable ranges | Requires focus-split then choose-tab; duplicate visible numbers | Reasonable alternative if Bryan mostly stays within one split |
| Split number plus local tab number | Scales across many groups | More syntax and another visual concept | Too much for the current two-split workflow |
| Stable assigned slots or per-file favorites | Strong muscle memory | Gaps, persistence, duplicate-file ambiguity; no longer Nth tab | Separate future feature if specifically wanted |
| Letter hinting | Avoids decimal limits | Conflicts with established window verbs or needs a new layer | Good general navigation technique, unnecessary here |
| Native numeric commands / Pane Relief | Existing functionality | Different scope/conventions and no shared Bob prefix snapshot | Useful reference, weaker integration |

I would not add an external plugin dependency for this. Pane Relief demonstrates that numbered navigation is viable, but its history, maximization, and movement machinery is much broader than the requested extension, and its numbering styles decorate view headers rather than furnishing this exact tab-strip contract. [S8]

## Make the decimal boundary explicit

There is no parser trick that makes both `Ctrl+W 1` execute immediately and `Ctrl+W 12` mean twelve: the first input is a prefix of the second. The implementation must choose a delimiter, a separate entry mode, a finite hint alphabet, or a timeout.

I recommend this exact table:

| Input after Ctrl+W | Result |
| --- | --- |
| `1` through `9` | Focus that literal global ordinal immediately; 9 always means ninth |
| `0` | Open “Go to tab” in the existing hint surface; no activation yet |
| In that chooser: digits, then `Enter` | Focus the exact ordinal, including 1–9 and any larger valid ordinal |
| In the chooser: `Backspace` | Remove a digit; empty buffer stays in the chooser |
| `Esc`, `Ctrl+[`, or `q` | Cancel through the existing exit path |
| Missing ordinal / zero / empty Enter | Stay armed; concise inline explanation; no substitute destination |

The chooser lists tab numbers and titles grouped by split, scrolls to the matching row as digits are typed, and highlights the exact candidate. Typing never changes focus until Enter. It should work for any catalog size, using a scrollable list rather than adding unbounded rows to the existing key grid. This first iteration needs numeric entry only; do not build fuzzy search merely to solve the decimal boundary.

The 1–9 behavior remains identical when the tenth tab opens. There is no “1 suddenly waits,” “pad every label to two digits,” or speed-dependent selection. The general chooser also makes a clipped tab discoverable without scrolling its tab strip first.

**Explicit requirement adjustment:** N above 9 uses `Ctrl+W 0 N Enter`, not bare `Ctrl+W N`. Show this in the armed card and in the tab's shortcut description. For an overflow tab, the armed badge may show the actual suffix `0·12↵`, with the idle badge showing ordinal `12`; reserve the expanded slot width so arming causes no title movement. The card must say “1–9 jump · 0 then number, Enter,” not simply “type a number.” If that extra chrome proves too wide in the visual spike, use a compact overflow mark beside `12` and make the exact suffix explicit in the card and chooser. Never present `12` as though typing bare `12` were supported.

This is the design's largest compromise. If direct numeric access beyond nine dominates actual use, I would instead choose **uniform `Ctrl+W N Enter` for every tab**, accepting one extra key to keep a single syntax. I would choose that over a timeout parser. For the four-tab motivating layout, the immediate 1–9 path plus explicit overflow is the better default.

## The visual design

The tab strip should continue to look like Obsidian. Add a compact numeric text mark immediately before the title, after the existing icon, with an approximately 4 px gap. Keep the file icon, pin, dirty indicator, title, and close affordance intact. Putting the hint before the title means a long ellipsized filename cannot hide its shortcut.

Use tabular numerals, medium weight, and roughly 0.85–0.9 times the tab's current font size rather than an unscalable fixed miniature. A small rounded keycap boundary can appear while armed. At rest, prefer quiet ink over a filled pill on every tab. Use theme variables for colors and spacing; use sufficient text contrast, not very low opacity, to achieve restraint. Small hint text should meet a 4.5:1 contrast target in the supported light and dark themes. [S11]

```text
Resting:         [icon]  4  sase_blog_contents          [close]
Ctrl+W armed:    [icon] [4] sase_blog_contents          [close]
```

Reserve the hint slot while idle. Arming changes color/border emphasis, not width or the position of close buttons. At 0 ms, emphasize destination hints across all main-area tab bars while retaining the existing focused-split ring. At the existing 300 ms delay, reveal the familiar card with one extra compact “Tabs” row. Do not add nine duplicate command rows or replace the split minimap.

On success, the native selected-tab state and existing focused-split underline carry most of the feedback. A brief destination hint/ring emphasis is enough; avoid a toast for every jump, a flying title animation, or dimming the documents. Disable transitions under reduced motion.

Distinguish **selected within its group** from **keyboard focus**: several groups can display a selected tab at once, but only one owns keyboard focus. The existing underline already addresses this distinction. Avoid giving every locally selected badge the same strong accent as the globally focused destination. [S6]

Badges are not new buttons or extra tab stops. Clicking the existing tab continues to work; dragging, middle-click close, and the context menu keep their current hit areas. Keep decorative duplicate text out of the accessible name, and add a descriptive association such as “Tab 4; window shortcut Control W, 4” without replacing Obsidian's filename label or tab role. Append/remove only Bob's own accessibility reference. The chooser needs an accessible number-entry label, candidate status, and a clear cancellation announcement. A screenshot cannot establish screen-reader correctness.

**Overflow and narrow tabs:** count all eligible tabs, not only headers currently visible through horizontal clipping. Preserve icon-only pinned tabs. Keep the small hint unshrunk where space permits; let the title ellipsize. If a strip cannot expose its hints, the number chooser remains the truthful full inventory. Stacked-tab rotation, icon-only themes, text scaling, and long titles are required visual checks. Do not promise support for every third-party vertical-tab plugin without an adapter.

## Implementation design: one catalog, one action

**A shared tab catalog.** Build a pure ordered array once per relevant layout generation:

```text
{ ordinal, leafId, groupId, title, pinned, shortcut }
```

Use that same array to paint badges, populate the chooser, describe shortcuts, and resolve a selected ordinal. Keep live leaf objects in the existing adapter maps. A renamed title must not change identity; two tabs showing the same path remain distinct entries.

The current snapshot obtains group leaves by filtering `iterateRootLeaves` output. Public declarations promise iteration, but do not specify visual ordering. Verify its order against actual `WorkspaceTabs` children/tab headers in the real-app spike, including drag reorder and pin transitions. If internal ordered children are needed, isolate that dependency in the adapter and test it. Never derive identity from a filename, title text, or a global DOM `nth-child` selector. [S4][S7]

Also separate catalog enumeration from **whether the current focus can arm Ctrl+W**. Today `snapshotWindowPrefixLayout()` returns null when the active leaf is outside the main root. Persistent badges must not disappear or get reassigned merely because the user clicks a sidebar. Enumerate the main-area catalog independently; use the existing arming gate when accepting the gesture. [S4][S5]

**Freeze the mapping during a gesture.** Record the catalog generation, ordered leaf identities, group membership, source leaf, and numeric target at arm/selection time. Before dispatch, verify that the target still exists in the same group and that the relevant catalog still matches what was painted. If it does not, cancel and refresh with “Tabs changed — try again.” Do not select whoever now occupies that ordinal.

This matters in the existing code: `runWindowPrefixMappedKey` takes a fresh snapshot, and `executeWindowPrefixPlan` plans again after checking the source leaf/group. That is appropriate to inspect for spatial verbs, but insufficient for painted ordinal targets. A target could change while the source remains unchanged. Numeric plans must carry and validate the captured destination identity instead of blindly recomputing `N` against a new list. Existing external layout-change cancellation helps, but it is not a substitute for this last check. [S4][S5]

**Focus the existing leaf.** For a loaded target, the essential action is:

```javascript
workspace.setActiveLeaf(targetLeaf, { focus: true });
```

For a deferred target, use the public `loadIfDeferred()` when appropriate, then revalidate gesture ownership and target membership before setting focus. `revealLeaf()` is another public foreground/loading operation; use it only if the live spike shows it is needed for the intended presentation. Do not add both calls mechanically. The API explicitly documents deferred views, so checking only `leaf.view.file` would miss valid destinations. [S7]

After any asynchronous load, a canceled or superseded operation must not steal focus back. Keep a session token and narrow expected-event handling; the existing broad self-caused-event suppression must not hide an unrelated user layout change during an await. Verify active leaf and content focus after activation, including stacked-tab visibility. Bound the wait and surface failure without opening a replacement tab.

Never call `openLinkText`, `openFile`, `getLeaf(true)`, duplicate, detach, reparent, or restore the whole layout to implement this jump. Activating the original leaf is what preserves pin, editor identity, undo history, folds, cursor, scroll, view mode, and per-tab history. Preserve each view's normal focus behavior; do not unconditionally focus a Markdown editor on PDF or Canvas destinations. Do not add a Bob Ctrl+O jump; ordinary Obsidian focus/MRU bookkeeping may still occur. [S1][S7]

**Own only the decoration.** Header element access and DOM classes such as `tabHeaderEl` are not part of the inspected public type surface. This is the fragile boundary, whereas leaf activation is public. Wrap header lookup and span insertion in one feature-detected adapter. Insert a namespaced sibling near the title; never rewrite the title text, patch `getDisplayText()`, or renumber using an independent CSS counter. [S7][S8]

Refresh after layout readiness and relevant layout changes; title changes can be handled by rename/file events and a narrowly scoped header observer if needed. Coalesce work into one animation frame, read geometry before writing styles, and ignore the observer's own inserted spans to prevent loops. A header rerender must reattach the same mapped hint, not create duplicates. Clear owned nodes, attributes, subscriptions, observers, and strong references on unload. Paint failure should leave a clear chooser fallback, not silently leave misleading numbered chrome.

**Reuse the existing keyboard owner.** Extend `normalizeWindowPrefixKeydown`, the planner dispatch, and the existing Scope. Do not install a competing global digit listener or nine permanent Ctrl+digit hotkeys. Held Ctrl should work for the entire sequence, including chooser digits and Enter. Read a literal digit from `event.key`; allow Shift when the layout requires it to produce that digit. Numpad digit values work naturally with this policy. Preserve composition/repeat guards and Meta/Alt cancellation; do not translate a locale's punctuation into a number merely because `event.code` is `Digit1`. MDN explains why `key` reflects the produced character and keyboard layout. [S5][S12]

Keep the accepted Linux decision: the prefix does not override an already-handled native Ctrl+W Close tab binding. Do not quietly rebind it as part of this work. In insert mode, ordinary Ctrl+W remains the editor's word deletion behavior. [S1][S2]

**Likely code seams:** extend the pure model in `266-window-prefix-model.js`, catalog/activation in `267-window-prefix-actions.js`, Scope states in `687-plugin-window-prefix.js`, command integration in `688-plugin-window-prefix-commands.js`, and presentation in `473-window-hint-view.js` plus styles. A dedicated tab-hint fragment would keep ownership clean and respect the repository's 1000-line fragment limit. Regenerate the committed entrypoint rather than editing `main.js`. Documentation belongs alongside `docs/window-keys.md`; implementation must follow that repo's build, verification, and deployment instructions. No Rust CLI or Mac Capture change is indicated by this scope. [S2][S3][S4][S5][S6][S13]

## Acceptance work that would justify shipping

Start with a small real-Obsidian spike for header mapping, ordered tabs, deferred activation, and focus. Reuse the scratch-vault harness rather than experimenting in Bryan's real vault. Then add focused tests around the new invariants; the existing passing tests establish a baseline, not coverage of this feature. [S10]

| Case | Required result |
| --- | --- |
| Cross-split selection | Exact target leaf focused; parent, sibling order, split widths and all other group selections unchanged |
| Same file open twice | The hinted instance selected; no deduplication or reopening |
| Source or target closes/moves while armed | Cancel, refresh hints, and never substitute another ordinal |
| Catalog changes without a delivered event | Dispatch-time generation/membership check still rejects stale input |
| Rename or header rerender | Identity remains; title/hint repaired without duplication |
| Already active target | Harmless success; exit prefix; no scroll or history reset |
| Deferred target, cancellation during loading | Correct view loads; canceled token never applies late focus |
| 9, 10, 12, 100+ tabs | 9 remains ninth; overflow is explicitly entered; all catalog entries reachable |
| Missing number, empty Enter, repeated keys | No accidental tab switch, text insertion, or extra command |
| Normal/visual versus insert mode | Existing arming boundary remains intact |
| Held Ctrl, numpad, shifted digit layout, IME | Same documented suffix semantics; no key leak into editor/native commands |
| Tab strip scrolling, narrow pins, stacked tabs | Correct numbering; destination revealed; chooser covers hidden headers |
| Sidebar, modal, popout, blur, plugin unload | Correct exclusion/cancellation; no leaked Scope or badge |
| Light/dark, zoom/text scaling, reduced motion | Readable hints, intact hit areas, no arm-time layout jump |

Measure refresh and activation cost with a representative large layout. A reasonable proposed target is one coalesced refresh per frame and no new work on ordinary text typing; do not claim a measured latency budget until profiled. Inspect before/after screenshots at one, two, and three splits. Keyboard focus, accessibility, and identity preservation need behavioral checks in addition to those screenshots.

## Sources

All repository content below was read from checkouts opened through `sase repo open`, not fetched from GitHub file URLs. Links pin the inspected revisions for later review.

[S1]: https://github.com/bobs-org/bob-cli--plans/blob/main/202611/obsidian_ctrl_w_window_prefix.md
[S2]: https://github.com/bobs-org/bob-plugins/blob/0e16e304142f94c70c78357f7bdfe4ded19d0db5/docs/window-keys.md
[S3]: https://github.com/bobs-org/bob-plugins/blob/0e16e304142f94c70c78357f7bdfe4ded19d0db5/plugins/bob-navigation-hotkeys/src/266-window-prefix-model.js
[S4]: https://github.com/bobs-org/bob-plugins/blob/0e16e304142f94c70c78357f7bdfe4ded19d0db5/plugins/bob-navigation-hotkeys/src/267-window-prefix-actions.js
[S5]: https://github.com/bobs-org/bob-plugins/blob/0e16e304142f94c70c78357f7bdfe4ded19d0db5/plugins/bob-navigation-hotkeys/src/687-plugin-window-prefix.js
[S6]: https://github.com/bobs-org/bob-plugins/blob/0e16e304142f94c70c78357f7bdfe4ded19d0db5/plugins/bob-navigation-hotkeys/src/688-plugin-window-prefix-commands.js
[S7]: https://github.com/obsidianmd/obsidian-api/blob/879c936660fcc45c90ee28ea6b4ef7068006477c/obsidian.d.ts
[S8]: https://github.com/pjeby/pane-relief/tree/646034ad2af6256fe8764e51668b588359185702
[S9]: https://obsidian.md/help/tabs
[S10]: https://github.com/bobs-org/bob-plugins/blob/0e16e304142f94c70c78357f7bdfe4ded19d0db5/scripts/obsidian-window-prefix-e2e.cjs
[S11]: https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html
[S12]: https://developer.mozilla.org/en-US/docs/Web/API/KeyboardEvent/key
[S13]: https://github.com/bobs-org/bob-plugins/blob/0e16e304142f94c70c78357f7bdfe4ded19d0db5/plugins/bob-navigation-hotkeys/src/473-window-hint-view.js

- **S1:** Audited source of record: `plan:202611/obsidian_ctrl_w_window_prefix.md`, plus `bead:bob-cli-m0`. The plan's approved Linux choice is `keep`; no decisions-memory change was authorized by that epic. The artifact identity is authoritative if its repository presentation changes.
- **S2–S6:** Bob documentation and implementation: prefix contract, pure model, live adapter, input ownership, and focused-split decoration.
- **S7:** Official API declarations: `iterateRootLeaves`, `setActiveLeaf`, `revealLeaf`, `WorkspaceLeaf.parent`, `loadIfDeferred`, and the deliberately sparse public `WorkspaceTabs` interface.
- **S8:** Pane Relief's `README.md`, `src/Navigator.ts`, `src/pane-relief.ts`, and `src/styles.scss`; an independent implementation precedent, not a runtime compatibility guarantee.
- **S9:** Official Obsidian help, browsed 2026-11-16: tab/group terminology, numbered native shortcuts, and stacked tabs.
- **S10:** Existing real-Obsidian test harness, inspected but not run in this research.
- **S11–S12:** W3C contrast guidance and MDN keyboard-event semantics, browsed 2026-11-16.
- **S13:** Existing hint painter, inspected for reuse of its ring, card, minimap, and motion behavior.

## Recommended solution

**Ship a main-window, leaf-based numeric focus extension inside the existing Ctrl+W system.** Use quiet persistent ordinal hints beside tab titles, immediate 1–9 selection, and a clearly advertised `0 → number → Enter` chooser for overflow and clipped tabs. Preserve the exact tab and group; freeze the painted mapping for each gesture and refuse stale destinations.

The intentional requirement adjustments are: numbers are global across central splits; non-file tabs count; “same vertical window” means unchanged tab-group membership; destinations above nine have an explicit entry mode; and sidebars/popouts/mobile remain outside the current prefix scope. These choices keep the common gesture short, make the failure cases predictable, and concentrate the visual design in the tab strip and the hint surface Bryan already knows.
