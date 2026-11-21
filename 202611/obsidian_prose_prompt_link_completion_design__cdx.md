# Obsidian links in Bob's prose prompts: design and implementation research

Researcher: **cdx** · 2026-11-21 · Independent investigation

**Decision:** Proceed. Add a reusable, explicitly attached link-completion component to Bob-owned fields that store Markdown prose. Typing `[[` should open a small suggestion surface without leaving the field. The important engineering work is destination-aware insertion, keyboard ownership, and preserving edits—not drawing a menu.

The requirement should become **“link completion in every eligible prose field”**, rather than every text-shaped control. Ship note names, aliases, and named-note headings first; support existing block IDs where the writer permits them. Preserve the existing Mac capture engine and use Obsidian's metadata APIs inside Obsidian. Share the behavior contract and fixtures across platforms, rather than passing arbitrary prose through the capture grammar.

## Evidence and limits

I inspected these checkouts independently; I did not consult any peer report, transcript, or findings:

| Repository | Revision inspected | Relevant evidence |
| --- | --- | --- |
| bob-cli | `e11f2a0c5e9fa1cb0aefe01a4ccb1ca1785e0af1` | `src/native/capture_links.rs`, `capture_complete/engine.rs`, `capture_complete/tests/work_log.rs`, `capture_language/markers.rs`, `note_catalog/tiers.rs`, current mirrored prompt documentation |
| bob-plugins | `70e23b76d66d1da75f9b821c9aa16cecf75175d2` | Intention editor, work-summary dialogs, schedule-review fields, shared log-recall controller, plugin build validation |
| bob-mac-capture | `109c30db300df4a9a161ee2152e3b4676decdeaf` | Native editor and event-note editor structure; existing completion and native replacement integration |
| obsidianmd/obsidian-api | `737629a51f6b4d30f8336fa3d38f3df006e322d4` | Public declarations for suggestion widgets, metadata, link generation, and search |

I also checked official Obsidian Help, W3C accessibility guidance, and MDN browser API documentation. SASE's audited memories supplied field definitions, the Mac thin-client rule, the Esc/q/Ctrl+[ convention, and artifact handling requirements. This is source and design research: no live-vault changes, UI prototype, performance benchmark, or assistive-technology test was performed. Timing targets below are proposed acceptance criteria, not measured results.

## 1. Why this is a good idea—and where it can go wrong

Intentions and work summaries benefit from links because the reference is useful at the moment of writing: “Finish [[release checklist]]” or “Resolved the issue described in [[incident review]].” Requiring the author to leave the prompt to find a filename breaks that moment. `[[` is already Obsidian's documented trigger, including when the user's preferred output is Markdown-link syntax. There is no need for a new sigil. [Obsidian internal links](https://help.obsidian.md/links)

The product risk is promising editor behavior in a field that is not an editor. Short prompts currently save on Enter. Work-log fields also recall entire prior summaries using arrow keys. A superficial autocomplete implementation can save prematurely, overwrite the draft with history, replace the wrong occurrence of a query, or create a link relative to the wrong note. These are more consequential than imperfect fuzzy ranking.

There is also a distinction between text and prose. A relation label, filename, command argument, email recipient, executable path, or copied shell snippet may accept arbitrary characters while still treating those characters as literal data. Adding a link picker there is distracting or changes the meaning of the field. Automatic global attachment to all inputs would make this distinction impossible to enforce.

I would not turn this into automatic entity linking, AI suggestions, a graph browser, or a universal mini-editor. The explicit `[[` gesture gives excellent intent detection. A small completion component is enough.

## 2. What already exists

### A substantial link engine is already in Bob

`capture_links.rs` recognizes incomplete and complete links, embeds, aliases, named and same-note headings/blocks, and vault-wide heading/block queries. It skips escaped and code-literal links, produces replacement ranges and post-insertion cursor positions, and caps results at 20. Note candidates use vault-relative paths; alias matches produce canonical target-plus-display-text links. Existing tests cover closing-bracket reuse, scope resolution, archive ordering, and excluded directories. [Engine and tests](https://github.com/bobs-org/bob-cli/blob/e11f2a0c5e9fa1cb0aefe01a4ccb1ca1785e0af1/src/native/capture_links.rs)

This is useful precedent, but the surrounding command is capture-specific. `capture_complete/engine.rs` derives the current note from the capture route, falling back to the inbox. A prompt about yesterday's intention or a task residing elsewhere has a different destination. Sending its text to `capture-complete` unchanged is not a safe generic integration. [Destination selection and restrictions](https://github.com/bobs-org/bob-cli/blob/e11f2a0c5e9fa1cb0aefe01a4ccb1ca1785e0af1/src/native/capture_complete/engine.rs#L130)

Two implementation details deserve attention before reuse:

- `NoteIndex::read` walks Markdown paths and reads their contents, including headings and block previews. It is not a persistent lightweight metadata lookup. A shell-completion comment mentions about 300 ms for this work; that is repository commentary, not a benchmark from this investigation. Do not assume a subprocess per keystroke will meet an interactive budget. [Index implementation](https://github.com/bobs-org/bob-cli/blob/e11f2a0c5e9fa1cb0aefe01a4ccb1ca1785e0af1/src/native/capture_links.rs#L211), [shell fast-path rationale](https://github.com/bobs-org/bob-cli/blob/e11f2a0c5e9fa1cb0aefe01a4ccb1ca1785e0af1/src/native/capture_complete/shell.rs#L38)
- The existing note-field replacement covers the inner link through `inner_end`. When editing a target before a heading or alias, that is wider than a target-only replacement. Generic prose completion should explicitly test preservation of existing subpaths and authored display text; copying the old range rule unexamined is insufficient. This is a source-level design concern, not a reproduced live-app bug. [Replacement construction](https://github.com/bobs-org/bob-cli/blob/e11f2a0c5e9fa1cb0aefe01a4ccb1ca1785e0af1/src/native/capture_links.rs#L572)

### The plugin prompts are several distinct integration points

| Surface | Implementation evidence | Integration consequence |
| --- | --- | --- |
| Intention, summary, reflection stages | `bob-ledger-tools/src/297c-plugin-intention-card-editor.js` and `297cc-plugin-intention-card-editor-paint.js` | Intention/summary use inputs; reflection uses an auto-growing textarea. Enter saves; reflection's Shift+Enter inserts a newline. Stage repaint can replace the input element. |
| Unlink-task work summary | `block-id-prompt/src/090-prompt-modals.js`, `WorkSummaryPromptModal` | Enter directly calls submit. Log recall attaches to the same input and modal scope. |
| Release-to-lane summary | `bob-navigation-hotkeys/src/190-summary-modals.js`, `LaneReleaseSummaryModal` | Another prose input, not an alias of the unlink dialog. |
| Schedule reason plus work summary | `bob-navigation-hotkeys/src/370-picker-schedule-work-log.js` | Two fields can exist together, with explicit focus cycling, recall, and form reconstruction. |
| Keep/cancel reasons | `192-freshness-refresh-summary-modal.js`, `195-rotten-keep.js` | Relevant additional prose entry points; classify by final writer behavior. |
| Record fields, task titles, notebook descriptions | Record-card stages and task/notebook dialogs | Eligibility must follow field schema: prose can support links, while slugs and identifiers cannot. |
| Mac event-note text | `BobMacCapture/GcalNoteEditorTextView.swift` | A separate native text view; existing capture completion does not automatically attach here. |

The first three rows are directly evidenced by the [intention keyboard handler](https://github.com/bobs-org/bob-plugins/blob/70e23b76d66d1da75f9b821c9aa16cecf75175d2/plugins/bob-ledger-tools/src/297c-plugin-intention-card-editor.js#L672), [stage renderer](https://github.com/bobs-org/bob-plugins/blob/70e23b76d66d1da75f9b821c9aa16cecf75175d2/plugins/bob-ledger-tools/src/297cc-plugin-intention-card-editor-paint.js#L113), and [work-summary modal](https://github.com/bobs-org/bob-plugins/blob/70e23b76d66d1da75f9b821c9aa16cecf75175d2/plugins/block-id-prompt/src/090-prompt-modals.js#L385). The table is a starting inventory, not a claim that every prompt has been exhaustively audited.

Log recall is an especially important existing abstraction. Its shared `attachLogRecall` controller owns optional capture-phase key listeners and a modal scope handler. Arrow/Ctrl+N/P navigation immediately fills the field with a recalled summary. Completion must coordinate with that controller, not merely install another listener and hope registration order works. [Recall controller](https://github.com/bobs-org/bob-plugins/blob/70e23b76d66d1da75f9b821c9aa16cecf75175d2/plugins/bob-navigation-hotkeys/src/184-log-recall-band.js#L256)

### Link kinds are not universally interchangeable

Capture-close work-log text deliberately suppresses block suggestions. Its validator explains that a block link could be treated as a Task Link. This restriction is specific evidence about capture-close entries, not proof that every task-summary writer rejects blocks. A general component must accept capabilities from each host and preserve its writer's constraints. [Completion guard](https://github.com/bobs-org/bob-cli/blob/e11f2a0c5e9fa1cb0aefe01a4ccb1ca1785e0af1/src/native/capture_complete/engine.rs#L147), [validation messages](https://github.com/bobs-org/bob-cli/blob/e11f2a0c5e9fa1cb0aefe01a4ccb1ca1785e0af1/src/native/capture_language/markers.rs#L1120)

## 3. Explicit adjustments to the request

1. **Scope by meaning:** “every Bob-owned Markdown prose field,” with an audited coverage list. Exclude filters, paths, identifiers, dates, numeric fields, command payloads, email addressing, and literal code/copy payloads. Do not intercept Obsidian's own note editor or other plugins' controls.
2. **Field capabilities:** notes and aliases everywhere eligible; headings where meaningful; existing block IDs only where permitted. Unknown or multiple destinations disable same-note shorthand suggestions. This preserves `[[` as the common trigger without pretending every writer accepts every link kind.
3. **Insertion only:** selecting a suggestion edits the draft. It neither saves the prompt nor navigates, creates a note, creates a block ID, or mutates the target. Manual unresolved links remain possible, subject to the host's existing validation.
4. **Phase richer searches:** start with Markdown notes, aliases, and target-scoped headings. Add permitted existing blocks next; defer attachments, vault-wide content search, block-ID creation, and `((` task actions. Preserve manually authored advanced syntax throughout.
5. **Separate rollout from aspiration:** begin in the actual intention/reflection and work-log prompts, then complete the classified prose inventory. Existing Mac capture behavior remains supported; additional Mac prose surfaces require a separate adapter and compile/CI verification.
6. **Keep formatting policy explicit:** Obsidian prompts should use public link generation honoring Obsidian preferences. Mac retains Bob's documented wikilink output. This intentional difference concerns serialization, not what a selected destination means.

These are recommended product decisions, not already accepted project policy.

## 4. Proposed interaction

### Opening, searching, and accepting

On the second unescaped `[` at a collapsed caret, show a compact panel associated with that token. Keep focus in the text field. Listen to input, composition, selection, and caret changes; keydown alone misses paste, speech input, undo, and middle-of-text editing. Pasting a complete link should not open a menu after its closing brackets. Moving the caret inside an existing link target should permit editing it.

The initial list can show a small deterministic set of relevant notes: the known destination and a few in-session recently accepted targets. With no useful context, offer ordinary note-name ordering and “Type a note name.” Do not manufacture popularity by collecting new cross-session usage history.

Search title/stem, alias, and path. For a nonempty query, prefer exact matches, then prefixes/word boundaries, then weaker matches; use context and recency only to break comparable matches. Show one best row per canonical file unless choosing a distinct alias would change the insertion. Alias rows display the alias as primary text and identify the canonical note below it. Obsidian itself inserts an alias as display text attached to a canonical target. [Obsidian aliases](https://help.obsidian.md/aliases)

Disambiguation must be visible before acceptance. Two notes named “Planning” need folder context; a hidden path suffix is not enough. Let `/` narrow by path. Keep result ordering deterministic and preserve the selected canonical identity when metadata refreshes. Do not let a late refresh silently change the row under an imminent Enter.

**Ranking adjustment:** current Rust link completion places living/archive/hidden tiers before match quality. I would change that ordering for deliberate, nonempty prose queries so an exact historical title is not buried by weaker active-note matches. Preserve existing tiers for empty discovery. If this later changes Mac capture too, treat it as an explicit behavioral change with fixture coverage, not an incidental refactor. [Current ranking](https://github.com/bobs-org/bob-cli/blob/e11f2a0c5e9fa1cb0aefe01a4ccb1ca1785e0af1/src/native/capture_links.rs#L271)

### Keyboard ownership

One routing path should enforce: **IME composition → link completion → history recall → host stage → host modal**. Busy-write guards remain authoritative before starting new editing actions. The following is the proposed contract for new prompt integrations:

| Gesture while completion is open | Result |
| --- | --- |
| Up/Down; Ctrl+P/N where supported | Move the highlighted suggestion without changing draft text; do not enter recall. |
| Enter with a valid current row | Insert only, close suggestions, keep the prompt open and caret in the field. The next deliberate Enter can save normally. |
| Enter during loading/no results/stale results | Close the suggestion layer and consume this key; preserve text. A later Enter has the host's normal meaning. |
| Ctrl/Cmd+Enter, if the host uses it to save | In the new prompt component, handle like Enter while suggestions are open; consume it without saving. Show the current key meaning. Preserve established capture-specific combined actions separately. |
| Esc or Ctrl+[ | Close suggestions only; leave token, draft, selection, and host stage intact. The next escape goes to the next layer. |
| Tab / Shift+Tab | Close suggestions without insertion and follow the host's focus traversal. This is a deliberate choice for multi-field forms. |
| Left/Right/Home/End, modified selection movement | Retain native caret behavior; recompute or dismiss when leaving the token. |
| Shift+Enter | Retain the host's documented newline behavior; the new line ends the active token. |
| `q` in the field | Type `q`. The project's outside-text q-as-Esc rule still applies. |
| Pointer selection | Apply the clicked row using the recorded token span without losing focus first. |
| Blur/outside click | Dismiss without acceptance or mutation. |

Handle key repeats so holding Enter after insertion cannot immediately save. Suppress reopening the same unchanged token after dismissal or undo; resume on a meaningful edit or explicit caret re-entry. Do not put the trigger on an arbitrary cooldown timer.

When a user types `#` with a note highlighted, make the action explicit: choose that note's target and transition to its headings, without saving. Manual `[[Note#` works too. Existing-block selection uses `#^` only in capable fields. If there is no valid highlighted note, `#` remains literal and resolution follows the text already typed. Keep custom display text after `|` under the author's control; target suggestions should not appear while editing that display text.

### A restrained visual design

Use the existing field and modal typography, spacing, and theme colors. Show at most six rows at once, with scrolling for a bounded result set. Each row has one small note/heading/block icon, a readable primary name, and a quiet path/context line. Match emphasis should be typographic, not a rainbow of badges. Reserve a small Alias or H2 marker for information that changes the interpretation of the row.

For a short single-line prompt, align the panel to the input's leading edge. For a multiline field, position near the caret when reliable, clamped inside the modal and viewport; fall back to the field edge if caret geometry is uncertain. Place it in the same document/window and modal accessibility tree. Flip above when needed. Do not resize the whole dialog on every result update or cover the text being edited.

Illustrative content, not a screenshot of existing UI:

```text
Work summary
┌──────────────────────────────────────────────────────────┐
│ Finished the review for [[plat▏                           │
└──────────────────────────────────────────────────────────┘
  ┌───────────────────────────────────────────────────────┐
  │ Link a note                                           │
  │ ▸ ▱ Platform migration                                │
  │     projects/platform-migration                       │
  │   ▱ Platform                               Alias      │
  │     areas/developer-platform                          │
  │   ▱ Platform review                                   │
  │     archive/2025/platform-review                      │
  ├───────────────────────────────────────────────────────┤
  │ ↑↓ Choose   ↵ Insert   Esc Dismiss                     │
  └───────────────────────────────────────────────────────┘
```

The highlighted row uses a subtle accent fill plus a visible selection edge. Normal and selected text must remain legible in light, dark, and increased-contrast themes. Keep the filename visible when shortening a long path; expose the complete destination to assistive technology. A restrained one-line insert preview is useful only when an alias, heading, or duplicate name makes the result ambiguous.

Use quiet inline states: “Finding notes…” after a short delay, “No matching notes — keep typing,” and “Suggestions unavailable; your text is kept.” No toast on each keystroke. Completion failure must never replace a host's write error or erase a retained retry. No animations are necessary; if added, keep them brief and honor reduced motion.

## 5. Correctness contract

The component needs an explicit input model, approximately:

```text
attachProseLinks({
  inputElement,
  modalScope,
  sourcePaths,          // actual eventual write destinations
  fieldCapabilities,   // note, alias, heading, existingBlock, embed
  provider,
  applyTextEdit,        // one undoable edit, then host's normal change pipeline
  routeKeys,
  onDispose
})
```

This is a suggested interface, not an API that currently exists.

**Destination is mandatory context, not a UI guess.** An intention belongs to the pinned day/period; a work summary belongs to the task's residence, even when launched from a daily-note link. A scheduling form may write the same prose to several task notes. Use absolute canonical targets for multi-destination output. Do not resolve `[[#Heading]]` against whichever note happens to be active. If the source destination is unknown, disable local-heading/local-block suggestions and explain that a note name is needed; ordinary named targets remain available.

**Edits operate on spans.** Snapshot input identity, value/revision, selection, token span, source context, and request generation. Acceptance must revalidate them. Never perform a global string replacement or blindly apply an old response. Replace only the active target or subpath, preserve the prefix/suffix and authored alias, reuse existing `]]`, and place the caret at the specified boundary. Token recognition must respect escapes, code spans/fences, adjacent links, and malformed nested openers.

Examples that should become shared test vectors:

| Before, with `▏` indicating the caret | Action | Expected property |
| --- | --- | --- |
| `Discuss [[pla▏ tomorrow` | Select Planning | Insert a closed link without swallowing unrelated prose; define the incomplete-token boundary conservatively. |
| `Discuss [[pla▏]] tomorrow` | Select Planning | Reuse the closing pair exactly once. |
| `[[Old▏#Overview|our plan]]` | Change note target | Preserve the authored heading and label; do not silently rewrite their spelling. |
| `[[Plan#Over▏|our plan]]` | Choose Overview | Replace the heading component only. |
| `😀 Review [[pl▏]]` | Select Planning | Emoji and surrounding text remain byte-for-byte intact. |
| `` `[[pla▏` `` | Type | No suggestions inside code. |
| `[[#O▏` with several write destinations | Type | No guessed same-note candidate. |
| `[[Plan|pla▏]]` | Type | Edit display text without target suggestions. |

The first example exposes a real ambiguity: spaces belong in filenames and prose. Do not claim a regex can always infer where an unclosed link ends. Prefer a session-tracked opening span and edits before the caret; preserve existing right-hand text unless a parsed closing delimiter gives a reliable whole-token boundary. Test this separately from replacing an existing closed token.

**Offset units must be explicit.** DOM selection offsets use UTF-16 units; the existing Rust engine returns UTF-8 byte spans; native Swift selections use their own string/range representations. Never pass an integer range across these boundaries without conversion and boundary checks. Normalize search keys separately from stored text so case folding or Unicode normalization never corrupts insertion offsets or path spelling.

**One undo step is a release criterion.** `setRangeText` is a useful range-edit primitive, but calling it and dispatching an input event is not evidence that the browser's native undo history is correct. A small insertion-adapter spike must prove insertion → typing → undo → redo on the actual supported Obsidian/Electron versions. If a guarded `execCommand('insertText')` compatibility path is required, isolate it: the API is deprecated, although MDN documents its undo-buffer behavior. Do not present it as a portable foundation. Mac should continue using the native text-view transaction path. [Range replacement](https://developer.mozilla.org/en-US/docs/Web/API/HTMLTextAreaElement/setRangeText), [undo caveat](https://developer.mozilla.org/en-US/docs/Web/API/Document/execCommand)

**Composition wins.** Suspend selection and submission handling while IME composition is active, observing composition lifecycle events as well as `isComposing`. Resume after the committed input arrives. Existing prompt guards are a good starting point, not a substitute for real CJK testing. [Keyboard composition state](https://developer.mozilla.org/en-US/docs/Web/API/KeyboardEvent/isComposing)

**No target mutation.** Candidate lookup and acceptance only read metadata and modify the draft. A deleted/renamed candidate must be re-resolved by identity or refused with text retained. Do not add IDs to blocks, create files, or follow links as a side effect. Suggestions use safe text rendering, not HTML assembled from filenames or aliases.

## 6. Implementation options and recommendation

| Approach | Strength | Cost or failure mode | Verdict |
| --- | --- | --- | --- |
| Independent picker in each modal | Fast first demo | Divergent key handling, ranking, range edits, and accessibility | Reject |
| Global observer that attaches to every input | Broad apparent coverage | Cannot know writer semantics; affects filters, code, third-party UI, and ownership | Reject |
| Embed or borrow Obsidian's private Markdown editor | Potentially native-looking | Private API/lifecycle coupling and large editor behavior change | Reject for this feature |
| Attach `AbstractInputSuggest` everywhere | Public UI abstraction for some controls | Public declaration covers input/contenteditable, not textarea; whole-field suggestions are not a complete inline-token contract | Useful spike, not universal foundation |
| Call existing `capture-complete` for every prompt | Reuses Rust candidate logic | Capture routing/grammar, disk scans, offset transport, and version requirements leak into simple prose | Reject as-is |
| Shared prose controller with platform providers | Explicit context, testable edits, low-latency local Obsidian metadata | Requires adapters and a maintained cross-platform contract | **Recommend** |

### Obsidian provider and distribution

Use `Vault.getMarkdownFiles()`, `MetadataCache.getFileCache()`, `parseFrontMatterAliases()`, `getFirstLinkpathDest()`, and `FileManager.generateMarkdownLink()` through public APIs. The last API takes the **source path** and respects link preferences. `fileToLinktext()` is useful where an explicitly wikilink-only host needs a safe target. Do not construct a bare alias target or assume basename uniqueness. [Public API declarations](https://github.com/obsidianmd/obsidian-api/blob/737629a51f6b4d30f8336fa3d38f3df006e322d4/obsidian.d.ts#L4409)

Build a compact in-memory catalog lazily and update it on vault/metadata changes. Search names/aliases/paths without reading every note body on each input. Fetch cached headings/blocks only for a resolved target. Metadata not yet available should yield a loading/partial state, not “this note has no headings.” Candidate count should be bounded; refresh must not displace a manually selected identity.

Use a common source module bundled into each participating plugin, plus small host attachments and shared CSS. This avoids requiring a navigation plugin merely to complete an intention. Separate plugin bundles may each hold a small metadata index; accept that cost initially rather than introducing a global singleton protocol. Measure memory before optimizing it.

**This requires a real build change:** the current fragment builder insists that source fragments remain inside each plugin's `src/` tree, including symlink targets. An arbitrary `../../shared` fragment will be rejected. Add a narrowly scoped, deterministic shared-module input to the builder, with build tests and generated output checks. Do not manually copy the implementation into three plugins. [Build containment checks](https://github.com/bobs-org/bob-plugins/blob/70e23b76d66d1da75f9b821c9aa16cecf75175d2/scripts/build-plugins.mjs#L68)

A versioned runtime API hosted in `bob-navigation-hotkeys`, analogous to log recall, is a reasonable lower-effort alternative if Bryan accepts that enabled-plugin dependency. I prefer bundling for this broadly expected text feature. Either approach needs explicit disposal on stage repaint, modal close, plugin unload, and document/window change.

`AbstractInputSuggest` can be evaluated as a presentation adapter for single-line fields, but the inspected public constructor accepts `HTMLInputElement | HTMLDivElement`, not `HTMLTextAreaElement`. Do not hide that gap with a cast or replace reflection textareas with contenteditable solely to fit it. A small controller-owned listbox using supported DOM and Obsidian scope APIs gives both field types the same behavior. [Suggestion type contract](https://github.com/obsidianmd/obsidian-api/blob/737629a51f6b4d30f8336fa3d38f3df006e322d4/obsidian.d.ts#L1169)

### Bob and Mac provider

Leave capture syntax under Bob's ownership. For new native prose inputs, expose a prose-only adapter around the existing Rust link scanner and candidate logic, taking an explicit destination and capability set. Do not fabricate capture routes or parse prose as capture commands. Retain Bob-produced replacement text/ranges and exact stale-response guards in the native client. Design any added command and JSON contract under the project's CLI rules, with additive compatibility handling.

This recommendation consciously permits an Obsidian metadata provider and a Rust provider. It does **not** port capture grammar into Swift. Cross-platform shared fixtures should cover canonical destination identity, alias handling, syntax boundaries, range behavior, and capability restrictions. Platform-specific serialization and native metadata sources can differ explicitly. If future requirements demand byte-identical ranking and serialization everywhere, revisit one portable core after measuring costs; a daemon, FFI, or WASM rollout is disproportionate for the initial prompt feature.

### Accessibility is part of the component

For single-line inputs use the editable-combobox/listbox relationship with a persistent accessible name, expanded state, controlled popup, and active descendant. Keep DOM focus in the input; expose highlighted rows and announce counts politely, without narrating the whole list on every keystroke. Acceptance and dismissal must be explicit; blur must not accept a row. [W3C combobox guidance](https://www.w3.org/WAI/ARIA/apg/patterns/combobox/)

For reflection, preserve native multiline textbox semantics. ARIA 1.2 describes combobox text input as single-line, while textbox supports multiline and autocomplete relationships. Do not blindly apply the single-line role to a textarea. Validate its associated listbox/active-descendant behavior in VoiceOver and NVDA, with a plainly described keyboard interaction. This is a known validation requirement, not a claim that a set of attributes alone guarantees accessibility. [WAI-ARIA 1.2 combobox and textbox definitions](https://www.w3.org/TR/wai-aria-1.2/)

## 7. Validation and rollout

Begin with a bounded spike in two real hosts: one work-summary input with recall and the reflection textarea with its existing save/newline behavior. Prove keyboard routing, native undo, IME handling, popup placement, and screen-reader usability before building the entire inventory. An isolated autocomplete demo will not expose these conflicts.

Then ship a vertical slice: common controller/provider, note and alias selection, named-note headings, destination context, and both hosts. Integrate the remaining prose prompts through the same attachment API. Add a small coverage registry recording field identity, writer destination, allowed kinds, and the reason for any exclusion. New prose fields should declare their policy rather than relying on a document-wide observer.

The subsequent increment adds existing blocks in audited hosts, broader syntax search if warranted, and native event-note/prose adapters. No promise of block-ID creation or attachment browsing is needed to deliver useful completion now.

Required evidence before release:

- **Token/edit fixtures:** escaped openers, inline/fenced code, multiple links, aliases, existing closers, incomplete tokens with following prose, target/subpath editing, noncollapsed selection, emoji, combining marks, and RTL text.
- **Destination fixtures:** duplicate basenames, unknown destination, a daily-note launch writing to another task note, yesterday/period navigation, and multi-task writes. Verify generated links resolve to the selected target from every output location.
- **Integration tests:** Enter inserts once without saving; repeats cannot save; Esc/Ctrl+[ dismiss one layer; q types; Tab leaves without insertion; recall cannot replace the draft while link completion owns the keys; stage repaint disposes old listeners.
- **Race/error tests:** delayed responses after typing/blur/close, rename/delete during lookup, absent metadata, provider errors, and stale write retries. Draft, cursor, and host retry state survive.
- **Real UI checks:** light/dark/increased contrast, long paths, small modal, multiline scrolling, secondary Obsidian window, keyboard-only use, CJK IME, VoiceOver/NVDA, and undo/redo. Unit stubs cannot establish these properties.
- **Performance targets:** initial affordance in one frame where practical; warm-query results at p95 under 50 ms; no long main-thread task attributable to searching; no per-keystroke full-vault read. Benchmark representative small and large synthetic catalogs and the actual vault locally, without recording its text. Revisit targets using measured hardware behavior.

Use existing plugin build/test checks and deploy through `bob plugins sync` when implementation lands. Any Rust changes need focused scanner/range/contract tests. Any Mac changes must compile and pass the project's exact-SHA macOS CI requirements. This research itself changes no product code and requires no product test run.

The main unresolved implementation risk is the DOM insertion adapter's undo behavior. The next is textarea accessibility and modal-scope precedence. Both can be settled by the initial real-host spike. The coverage inventory is also unfinished; claiming universal support before that inventory would be premature.

## Recommended solution

**Build one explicit prose-link component for Bob's eligible prompts, starting with intentions/reflections and work summaries.** Use a quiet six-row suggestion surface triggered by `[[`, canonical destination identity, visible path disambiguation, and an Enter-to-insert-only layer above history recall and prompt submission. Keep all suggestions optional and all edits undoable.

Use local public Obsidian metadata APIs and a shared bundled controller inside plugins. Preserve Bob's existing authority in Mac Capture; extend it with an explicit prose context only for additional native fields. Notes, aliases, and named-note headings form the first useful release; permit existing blocks only where the writer's semantics are safe. Finish the eligible-field inventory as part of rollout, and explicitly exclude non-prose inputs. This delivers the requested reach and polish without turning every prompt into a second editor or making link acceptance a hidden write operation.
