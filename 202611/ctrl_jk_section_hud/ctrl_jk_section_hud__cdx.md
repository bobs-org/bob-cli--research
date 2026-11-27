# Keeping your place during Obsidian heading jumps

Independent research by **cdx**, 2026-11-27. Scope: design and implementation research, not a deployed change. No other researcher's report, transcript, summary, or findings were consulted.

**Recommendation in brief.** Add a temporary, passive outline to the existing Bob Navigation Hotkeys heading commands. Show the landed heading, its actual previous and next jump targets, a little surrounding structure, and an explicit wrap indication. Keep editor focus and existing navigation behavior. The strongest version of this idea is a small orientation aid that appears when needed; a complete interactive table of contents on every jump would add too much competing activity.

**What the implementation actually does today.**

I inspected `bob-plugins` at commit `dd9ecff1eb559ec257aa0eaa25465adde72278de`, after opening it through `sase repo`. The user supplied the Ctrl+J/K bindings; I did not inspect the live vault's hotkey or Vim configuration or run an interactive Obsidian session. That distinction matters: the plugin registers heading commands without default hotkeys, and these commands are the appropriate integration point regardless of how they are invoked.

| Observed behavior | Design consequence |
| --- | --- |
| `jump-to-next-section-header` and `jump-to-prev-section-header` call `jumpToSectionHeader(editor, direction)`. | Add feedback to these callbacks, rather than a document-wide Ctrl+J/K listener. Palette invocations and remapped keys should behave consistently. |
| The target comes from the current editor text, not a vault read. | The outline must reflect unsaved edits too. |
| The scanner recognizes ATX headings H1–H6, with up to three leading spaces, outside initial YAML frontmatter and fenced code. | Initially describe the feature as an outline of **navigable sections**. A different parser could disagree with the commands. |
| Next selects the first heading strictly after the cursor; previous selects the last heading strictly before it. | From within a section's body, previous goes to that section's own heading. Do not accidentally replace this with “previous sibling section.” |
| Both directions wrap. With one heading, a jump can land on that same heading. | Make wraps and “only section” explicit. A direction arrow alone is ambiguous. |
| Successful jumps set column zero and request top alignment via CodeMirror. No successful-jump outline is shown. | Preserve the familiar landing position and add orientation there. |
| Section jumps do not select a bracket-walk family. | The new feedback must not change `[[`/`]]` or review/lane/bank navigation state. |

Evidence: [command registration](https://github.com/bobs-org/bob-plugins/blob/dd9ecff1eb559ec257aa0eaa25465adde72278de/plugins/bob-navigation-hotkeys/src/490-plugin-lifecycle.js), [jump implementation](https://github.com/bobs-org/bob-plugins/blob/dd9ecff1eb559ec257aa0eaa25465adde72278de/plugins/bob-navigation-hotkeys/src/610-plugin-jumps-and-counted-keys.js), [scanner and wrap logic](https://github.com/bobs-org/bob-plugins/blob/dd9ecff1eb559ec257aa0eaa25465adde72278de/plugins/bob-navigation-hotkeys/src/130-fences-and-status.js), [heading expression](https://github.com/bobs-org/bob-plugins/blob/dd9ecff1eb559ec257aa0eaa25465adde72278de/plugins/bob-navigation-hotkeys/src/010-requires-and-config.js), and [scroll helper](https://github.com/bobs-org/bob-plugins/blob/dd9ecff1eb559ec257aa0eaa25465adde72278de/plugins/bob-navigation-hotkeys/src/170-open-task-jump.js).

I ran the existing `scripts/test-navigation-hotkeys-section-nav.cjs`: **9 tests passed**, including three section-navigation tests and six adjacent task-navigation tests. Additional small probes against the exported helpers confirmed that Setext headings and blockquoted headings are excluded, duplicate titles remain distinct positions, an unclosed fence hides subsequent headings, and a heading-shaped line inside a multiline HTML comment is currently included. This scanner is intentionally small, not a complete Markdown parser. The comment behavior is a concrete limitation, not an assertion about Obsidian's own Outline.

**Is the feature a good idea?**

Yes. The problem is remembering the relationship between destinations after an abrupt scroll. Showing the destination alone confirms a jump but does little to answer “what is immediately before or after this?” Showing nearby named destinations addresses the reported problem directly. This follows recognition-over-recall and timely-feedback principles; it is a design inference, not a measured result for Bryan's workflow. [Nielsen's usability heuristics](https://www.nngroup.com/articles/ten-usability-heuristics/) support these principles and also caution against irrelevant visual competition.

There are three risks worth designing around. First, an outline that opens, animates, and disappears on every repeated keypress can become more distracting than the original problem. Second, a large tree demands a second navigation task just to understand a simple jump. Third, the feature can become a miniature editor with collapse controls, search, click targets, pinning, and its own keyboard mode. Those are useful elsewhere but unnecessary for this request.

A brief outline also cannot solve every orientation problem. If Bryan loses his place while reading or scrolling between jumps, a persistent breadcrumb or sidebar is the better tool. If the problem is returning to where a sequence started, jump history is a separate need. This report does not assume section jumps currently record such history: the inspected heading method does not explicitly invoke the custom jump-history integration. Do not promise Ctrl+O behavior without testing that path.

**Alternatives and what they teach us.**

| Approach | What it does well | Fit for this request |
| --- | --- | --- |
| Keep Obsidian's core Outline open | A full, persistent heading map with click navigation. | Best zero-build baseline; costs sidebar space and a gaze shift. It is worth comparing with the prototype, not automatically opening/closing on each jump. |
| Quiet Outline | Search, expansion control, remembered state, and keyboard navigation. | A capable permanent outline, but its documented surface is a separate outline view. Exact integration with Bob's jump targets still needs work. |
| Dynamic Outline or a floating TOC | Puts structure beside the note; Dynamic Outline documents active-heading indication, keyboard control, and auto-hide behavior. | Strong visual precedent. Its published feature list does not establish an API for showing precisely Bob's just-computed target after these commands. Evaluate before adopting a dependency. |
| Sticky breadcrumb | Shows the current containing hierarchy with very little space. | Good for “where am I?”, insufficient alone for “what does the next jump reach?” |
| Destination highlight only | Keeps attention in the document and is inexpensive. | Helpful reinforcement; no neighboring-section information. |
| Modal heading picker | Excellent for choosing a distant destination. | Too much focus and keyboard disruption for each already-decided jump. |
| Transient local outline in the editor pane | Shows position and immediate destinations at the moment of uncertainty. | Best fit if it is passive, bounded, and updated in place. |

The first three alternatives are documented by [Obsidian Outline](https://obsidian.md/help/plugins/outline), [Quiet Outline's published plugin page](https://community.obsidian.md/plugins/obsidian-quiet-outline), and [Dynamic Outline's published plugin page](https://community.obsidian.md/plugins/dynamic-outline). These are feature descriptions, not results of local compatibility testing. I would not install or fork an additional outline plugin solely for this feature.

VS Code provides another useful precedent: breadcrumbs show the enclosing symbol path, while a dropdown supplies nearby symbols. My inference is to combine a short hierarchy cue with nearby named destinations, while retaining Bob's keyboard workflow. There is no need to reproduce VS Code's interaction model. [VS Code code navigation](https://code.visualstudio.com/docs/editing/editingevolved).

**Proposed experience.**

On a successful heading jump, show a small card within the active editor pane. The card uses the note name, an optional ancestor breadcrumb, a highlighted current row, and neighboring headings in document order. The heading immediately above and below the current row must be the actual previous and next targets from that landing, including descendants. Do not show siblings while the keys traverse every heading.

A schematic for a longer note, with seven displayed heading rows:

```text
┌──────────────────────────────────────────┐
│ Project Atlas                    5 of 12  │
│ Current work                             │
│                 · 1 earlier ·            │
│   Current work                           │
│     Research                             │
│       Reading                     prev ↑ │
│ ▎ ● Implementation                       │
│       Editor integration          next ↓ │
│       Verification                       │
│   Later                                  │
│                 · 4 later ·              │
└──────────────────────────────────────────┘
```

The bold/tinted current row and small leading marker say “you are here”; it is not a selection awaiting Enter. The two neighbor labels describe jump destinations. Prefer words and arrows to hardcoded key labels unless the actual bindings can be resolved reliably. A user who remaps the commands should not receive false instructions.

For seven or fewer headings, show the whole outline. For longer notes, show a contiguous window of at most seven headings, normally three before and three after the landing, clamped at the ends. Indicate omitted counts. Use the nearest preceding shallower heading to compute each parent, including skipped levels such as H2 → H4; do not invent missing ancestors. If the current parent is outside the slice, show it in the breadcrumb. Visual indentation may be capped to protect title width, while accessible text retains the actual heading level.

Keep the list in linear document order at the boundaries. When landing on the last heading, the footer can say `Next: Introduction ↻`; when landing on the first, `Previous: Appendix ↻`. When a jump actually wraps, briefly show `↻ Wrapped to start` or `↻ Wrapped to end`. Do not silently rotate the tree into a circular list. “Previous target” at the first heading is not necessarily the section just visited, so avoid using “came from” as its label.

For a single heading, show `Only section` rather than a wrap celebration or duplicated previous/next rows. With no headings, use one replaceable `No section headings in this note` message. Neither case should stack notices during key repeat.

**Appearance and placement.**

The visual treatment should feel like a small piece of Obsidian's own chrome: an opaque theme surface, a thin border, restrained shadow, approximately 8–10 px corner radius, readable text, and one accent color for the current location. Start around 300–340 px wide with 26–30 px rows; these are prototype values, not usability findings. Use Obsidian theme variables and test real light and dark themes. Avoid blurred glass, a rainbow of heading levels, gradients that wash out text, large icons, or a second progress visualization that competes with the titles.

Previous and next titles deserve strong readability, not barely visible gray. Other context can be quieter. Wrap long current and adjacent titles up to two lines; farther titles may ellipsize. Keep complete plain-text labels in the accessible representation. Duplicate titles use parent context, adding a line number only when needed to distinguish otherwise identical entries. Authored section numbers and emoji remain part of the label.

Prefer the unused right gutter beside the text, at the top of the editor viewport. The panel belongs to the active leaf, not the entire application window. When no gutter fits it, allow a bounded top-right overlay below the destination heading's first two rendered lines, with no document reflow. For a narrow pane, use a compact bottom-corner version with current/previous/next plus the breadcrumb. Geometry must keep the destination heading and caret unobscured. If even that cannot fit at large zoom, reduce to a single-line location receipt; retain the explicit peek and full Outline routes.

Choose the placement once per visible jump sequence and recompute only on pane resize or window migration. Do not chase the caret around the screen. The cost of the fallback is temporary coverage of some body text; compare that against a thin bottom strip during the visual prototype. Placement is the largest unresolved visual question because I have not observed Bryan's actual pane widths or theme.

**Timing and keyboard behavior.**

Use **2.4 seconds after the last heading command** as the initial default. Show immediately after a successful landing, replace the content in place on subsequent commands, and restart one timer. Add at most a short opacity fade around 120 ms when ending the sequence; do not replay an entrance animation for each press. Respect reduced-motion preferences and avoid adding smooth scrolling to the jump. These values need user evaluation, not claims of a universal optimum. [W3C guidance on interaction-triggered animation](https://www.w3.org/WAI/WCAG21/Understanding/animation-from-interactions).

Process each command normally, including OS repeat; only coalesce visual updates to the latest result per frame. Debouncing navigation itself would discard intentional jumps. Do not depend on a Ctrl keyup event for dismissal, since focus changes and command-palette invocations make that fragile.

The card is passive: no focus transfer, tab stops, interactive tree semantics, pointer capture, or arrow/Enter handlers. Let pointer events pass through to the editor. Hide it when ordinary editor work resumes, on a user scroll, pane/file switch, an external document replacement, or another modal taking over. Distinguish the jump's own selection/scroll update from subsequent user activity so the panel does not dismiss itself immediately. Dismissal must not consume the underlying editor action or affect Vim mode.

Provide an explicit **Peek section context** command, with no compulsory default keybinding, which shows the same information without moving the cursor. When invoked inside a section body, identify its containing heading and calculate the two command destinations from the actual cursor; previous may be that same containing heading. Before the first heading, state `Before first section` rather than pretending the cursor is inside one. Offer one simple display preference: **Brief**, **Until next editor action**, or **Off**. Explicit peek can remain available when automatic display is off. The untimed choice gives leisurely access to the same context without creating a pinned panel.

For a complete document tree, leave Obsidian's existing Outline as an explicit separate surface. A future interactive expansion can be evaluated separately. A temporary message should not be the only way to obtain essential information; W3C's timing guidance specifically discusses temporary notifications that have an alternative untimed route. [Timing Adjustable](https://www.w3.org/WAI/WCAG22/Understanding/timing-adjustable.html).

The governing decision `decisions:q-and-ctrl-bracket-mirror-esc` requires Esc, q, and Ctrl+[ parity for Bob panels that handle dismissal. Do not accidentally create an Esc-only panel here. The passive status display should have **no dismissal key scope**: normal editor activity hides it as a side effect, and q/Esc/Ctrl+[ retain their editor behavior. This interpretation depends on keeping it noninteractive. Any later focusable or pinned panel must use the shared panel dismissal convention, including consuming q outside that panel's own text controls.

Also preserve `decisions:successor-jump-parks-the-walk`: Ctrl+J already pins a successor inside its picker. A global listener would risk displaying unrelated heading UI or stealing the pin. Feedback belongs after the heading command's successful navigation, not after observing a raw keystroke.

**Implementation approach and reliability.**

Extend `bob-navigation-hotkeys`; no new service, CLI subprocess, network request, or vault mutation is needed. Edit its source fragments and generated build through the repository's established workflow, not the deployed vault files. The present plugin has no settings tab, so the proposed display preference needs a deliberate small configuration surface; do not bury it in an undocumented JSON field or add dozens of cosmetic settings.

The architecture can remain small:

```text
existing heading command + editor/view
        ↓
one heading index for this exact buffer
        ↓
pure navigation result: target, ordinal, wrap
        ↓
existing cursor placement and scroll
        ↓
passive context renderer + one expiry timer
```

Pass the command callback's editor/view context through the route. Build one ordered heading model containing source position, level, display label, and parent index. Use it both to choose the target and to build the outline; avoid scanning once for navigation and again for display. Position, not heading text, is the identity within that buffer version. Duplicate `## Notes` headings must remain distinct.

For the first version, enrich the existing scanner and preserve its target set. Explicitly document its ATX scope; Setext and headings in quotes/callouts are not silently added just because another outline parser supports them. The HTML-comment result identified above deserves a separately explicit scanner correction and regression case if addressed during implementation. Changing which lines the keys visit is a behavior change, even when it fixes an inconsistency. Whatever parser policy is chosen, change navigation and display together.

Do not source the active editing outline solely from `metadataCache`, disk, rendered heading elements, or a viewport-limited syntax tree. A saved representation is not guaranteed to describe the current editor buffer. Obsidian documents that only the viewport and some surrounding text are rendered, so DOM scraping cannot enumerate the file. CodeMirror also documents that `syntaxTree(state)` can be incomplete and that forcing more parsing has a work budget and can fail. [Obsidian viewport documentation](https://docs.obsidian.md/Plugins/Editor/Viewport), [CodeMirror syntax-tree reference](https://codemirror.net/docs/ref/#language.syntaxTree).

A full grammar-based index is a credible later improvement if exact Obsidian Markdown parity becomes a requirement. It is larger work than displaying the existing navigation context. Do not promise it through a quick regex patch or silently force the entire document to parse on every keypress.

Cache the index per editor and immutable document version when CodeMirror is available; invalidate on document change. Do not cache only by file path or modification time, because unsaved panes can differ. In a generic-editor fallback without a reliable change token, rescan current text. Render only the small visible slice. Store expiry, render generation, and ownership per view, hide stale displays on leaf switch, and clean up timers/elements/listeners on view destruction and plugin unload. An old timeout must never clear a newer sequence.

Use the source view's owning document and window, including for timers and motion preferences. Obsidian explicitly warns that `document` and even `activeDocument` can refer to the wrong window for a given element. [Pop-out window guidance](https://docs.obsidian.md/plugins/guides/pop-out-windows). Access to `editor.cm` is a compatibility boundary already present in the existing scroll helper; Obsidian documents this route but notes it is not exposed by the typed Editor API. Keep it isolated, feature-detected, and covered by runtime checks. [Communicating with editor extensions](https://docs.obsidian.md/Plugins/Editor/Communicating%20with%20editor%20extensions).

A custom pane-local surface is preferable to a standard stacked `Notice`: it supplies stable ownership and placement. Reuse Bob's typography and restrained notice styling. The existing [lane notice](https://github.com/bobs-org/bob-plugins/blob/dd9ecff1eb559ec257aa0eaa25465adde72278de/plugins/bob-navigation-hotkeys/src/543-lane-walk-notice.js) already demonstrates replacing a previous navigation notice, but it recreates the notice through the global document and should not be copied wholesale for this use.

A subtle destination-line tint for roughly 500–700 ms can reinforce the current outline row. Bob already has a CodeMirror line-decoration implementation for [open-notes landings](https://github.com/bobs-org/bob-plugins/blob/dd9ecff1eb559ec257aa0eaa25465adde72278de/plugins/bob-navigation-hotkeys/src/676-plugin-open-notes-uri.js). Reuse the pattern with appropriate per-window ownership and timer cleanup; do not manipulate virtualized `.cm-line` elements directly. If the tint adds visual noise, remove it before weakening the neighbor information.

Render headings as text, with conservative inline-format normalization. Do not invoke arbitrary Markdown processors, embeds, Dataview, HTML, or links to build this small feedback surface. If normalization is uncertain, displaying literal markup is better than changing the title's meaning.

Outline failures must not prevent or undo a valid jump. Keep display work after target placement, guard against stale view/document identity before painting, and fail quietly to preserved navigation if the display cannot render. Do not turn each rendering error into another toast.

**Accessibility and measurable acceptance.**

Keep the visual list a passive list, not an ARIA tree requiring a new interaction mode. Add a separate concise polite status announcement, coalesced after rapid commands settle: destination title, ordinal, optional wrap, and neighboring names. Do not reannounce all seven headings on every key repeat. Verify this in the actual app with a screen reader; avoid duplicating whatever the editor already announces. W3C describes status messages that can be conveyed without moving focus. [Status Messages](https://www.w3.org/WAI/WCAG22/Understanding/status-messages.html).

Selection must be visible through a marker and weight as well as color. Check contrast and large text in both themes. Reduced motion should remove unnecessary transitions without reducing the time available to read. The untimed display preference and explicit peek are part of the design, not later polish.

| Acceptance area | Evidence to require before shipping |
| --- | --- |
| Navigation parity | Same landing lines, wrap behavior, direction, column, and top alignment with the feature on and off. No bracket-walk state changes. |
| Shared targets | Every displayed immediate neighbor equals the result of invoking the corresponding command from that position. Test body cursors and both wrap boundaries. |
| Parsing | YAML, backtick/tilde fences, longer closing fences, incomplete fences, duplicate/empty titles, indentation, skipped levels, H1–H6, CRLF, and the deliberately chosen Setext/comment/quote policy. |
| Editing | Unsaved heading insertion, deletion, rename, and external document replacement cannot leave old labels pointing at new positions. |
| Keyboard ownership | Vim normal/insert modes, command-palette invocation, held Ctrl+J/K, rapid reversal, and Ctrl+J inside a successor picker. No swallowed typing or changed selection. |
| Lifecycle | Two panes showing different notes, two panes of one note, pop-out windows, pane close, mode switch, plugin unload, and expired timers after a newer jump. |
| Presentation | Short/long notes, deeply nested headings, long duplicate names, narrow panes, large zoom, light/dark themes, and reduced motion. The landed heading and caret remain visible. |
| Accessibility | Polite, coalesced speech; no focus movement; equivalent untimed context; selection understandable without color. |
| Failure behavior | Renderer and optional CodeMirror support failures preserve the underlying heading jump. No note bytes or undo history are changed by feedback. |

An ad hoc Node timing probe, on this host rather than a Mac or Obsidian renderer, measured the existing `split + getSectionHeaderJumpLine` operation over synthetic notes with one heading per 20 lines. Across 20 measured iterations after three warm-ups, medians were **0.325 ms for 1,000 lines**, **2.306 ms for 10,000**, and **24.394 ms for 100,000**; maxima were 16.308, 8.138, and 34.105 ms. This is not a stable benchmark or end-to-end latency claim. It indicates why repeated whole-buffer work should be avoided for large files and why measurements must include the first jump after an edit. No overlay implementation was benchmarked.

A useful product experiment is to compare (a) current behavior with Outline open, (b) a destination tint, and (c) the proposed local outline on several representative notes. Ask Bryan to predict the next target, reverse direction, cross a hierarchy boundary, and recognize a wrap. Observe incorrect extra jumps, time spent searching for the current section, and whether the card hides text he immediately wants to read. Do not optimize for screenshots alone. The feature succeeds when he needs fewer recovery jumps and rarely notices the interface itself.

**Explicit adjustments to the requested requirements.**

1. Interpret “outline of the file” as a complete outline for small notes and a clearly marked local window for large notes. A full transient tree cannot remain both brief and readable at arbitrary size.
2. Trigger from the heading commands, not literal Ctrl+J/K events. This preserves remapping and existing modal meanings of those keys.
3. Keep the first version passive. Searching, clicking headings, collapsing branches, and pinning introduce another control surface and are deferred.
4. Preserve wrapping and show it explicitly. The request is about orientation, not a change to traversal behavior.
5. Include an untimed mode and a no-movement peek. A fixed short timeout alone does not serve every reading pace.
6. Scope the initial model to the existing navigable ATX headings. Broader Markdown support is a separately visible behavior decision; scanner limitations must not be concealed by a prettier outline.
7. Target desktop editing modes first, because the current commands are editor callbacks. Reading-view navigation and mobile interaction are additional scope requiring their own target and focus contracts.
8. Treat placement, row count, and timing as prototype defaults to validate in Bryan's real workspace. They have not been proven by a usability study or live Obsidian test in this research.

**Recommended solution.**

Implement a **temporary section-context outline inside Bob Navigation Hotkeys**, fed by the exact same live-buffer heading model as the existing jumps. Default to seven or fewer rows, unmistakable current-heading emphasis, actual previous/next destinations, a short ancestry cue, and explicit wrap feedback. Update one pane-local display in place for about 2.4 seconds after the last jump, preserve focus and all key semantics, and provide explicit peek plus an untimed preference. Keep the full Outline available for deliberate exploration. This directly addresses losing one's place while retaining the speed and calm of the current keyboard workflow; expand it into an interactive navigator only if use demonstrates a separate need.
