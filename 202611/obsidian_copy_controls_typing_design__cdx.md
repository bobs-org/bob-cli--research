# Copyable text in Obsidian: typing, interaction, and implementation

Researcher: cdx  
Date: 2026-11-19  
Status: independent research and design recommendation; no feature installed or implemented.

## Decision in brief

This is a good idea for text that belongs beside its explanation: a command in a runbook, an address in a contact note, a search expression, or a reusable message. Make it an explicitly marked **copy control**, with its literal text stored at the point of use. A compact button with a copy icon communicates the action better than a navigation link.

For Bob, I recommend a small `bob-copy` plugin in the existing `bob-plugins` monorepo. Its everyday authoring form should be ordinary inline code with a short opt-in prefix:

```markdown
`copy: ssh apollo`
`copy[Connect]: ssh apollo`
```

The first displays the text with a copy icon; the second displays **Connect** with a copy icon and offers a preview of `ssh apollo`. Add a fenced form for multiline payloads and a keyboard command that converts selected text into either form. The source is self-contained: no IDs, separate button definitions, YAML, JavaScript, or URL encoding for a typical instance.

**Best existing alternative:** Copy Text Protocol already provides labeled clipboard links and a creation command. It is the right immediate trial if avoiding custom maintenance matters most. Its source is less pleasant to edit, and its current implementation has edge cases worth resolving before treating it as the polished final design. Generic Buttons also has a native copy action; Meta Bind is possible but introduces more configuration and, for its documented inline-JavaScript approach, another plugin.

## Scope and evidence

I independently inspected current upstream source for Copy Text Protocol, Copy Inline Code, and Buttons; official Meta Bind documentation; Obsidian help and developer documentation; the Clipboard API; accessibility guidance; and Bob's existing plugin source. I did not inspect any other swarm researcher's report, findings, or conversation.

These are source and documentation findings, supplemented by a small local Markdown parsing experiment. I did **not** test any candidate inside a running Obsidian instance or against a real system clipboard. Desktop, mobile, theme, and editor compatibility remain acceptance tests, not claims of demonstrated compatibility. Upstream checkout manifests and marketplace pages can differ; the pinned revisions below identify what I inspected.

## What already exists

| Approach | Creating a new instance | Strength | Limitation for this request | Verdict |
| --- | --- | --- | --- | --- |
| Ordinary fenced code block | Type a normal Markdown fence and its text | Familiar, readable, useful baseline; Obsidian has a code-block copy affordance | Takes block space; separate compact labels are not its purpose | Use when the payload should already be displayed as a block |
| Copy Inline Code | Put the text in backticks | Very little authoring friction; copy icons in Reading view and the editor | Broadly augments ordinary inline code; no independent label/payload model | Good if “the displayed snippet is the copied snippet” is sufficient |
| Copy Text Protocol | Type a link or run its clipboard-to-link command | Closest existing match: local payload, label, copy icon, hover preview | Encoded URLs are awkward to revise; creation depends on clipboard contents; source-level edge cases | Best off-the-shelf trial |
| Buttons | A `button` fence with `name`, `type copy`, and `action` | Native clipboard action; builder and styling options | Inline use references a separately defined button ID | Reasonable if Buttons is already part of the workflow |
| Meta Bind | YAML button definition; optional inline `BUTTON[id]` reference | Broad, configurable interactive-note system | Documented inline buttons reference definitions; documented JS route needs JS Engine and JavaScript enabled | Excess machinery solely for static text copying |
| A focused Bob copy plugin | Opt-in inline notation or conversion command; fence for multiple lines | Direct authoring, deliberate visual design, no external definition registry | Owns parser, editor, accessibility, and upgrade maintenance | Recommended for the full requested experience |

**Built-in baseline.** Obsidian's own release notes document a code-block copy button in preview mode. That supports testing ordinary fences before adding anything; it does not establish that the button remains available in every editing context. [Obsidian release note](https://obsidian.md/changelog/2021-09-14-desktop-v0.12.16/).

**Copy Inline Code.** The inspected implementation uses a Markdown postprocessor and CodeMirror widgets, with a configurable Lucide icon, hover visibility, and filters. It handles asynchronous clipboard success/failure. Its icon factory creates a clickable span without native button semantics, keyboard activation, or a tab stop in the inspected code. The editor reads source slices while Reading view reads rendered code text, so edge-case whitespace parity deserves testing. These observations are reasons to evaluate it carefully, not evidence that routine copying fails. [Upstream README](https://github.com/ozavodny/obsidian-copy-inline-code-plugin/blob/f885d1108c5f8950cfb28752ec95483caca358f0/README.md), [icon implementation](https://github.com/ozavodny/obsidian-copy-inline-code-plugin/blob/f885d1108c5f8950cfb28752ec95483caca358f0/src/copy-icon.ts), [editor implementation](https://github.com/ozavodny/obsidian-copy-inline-code-plugin/blob/f885d1108c5f8950cfb28752ec95483caca358f0/src/copy-inline-code-view-plugin.ts).

**Copy Text Protocol.** It supports links such as:

```markdown
[Connect](<obsidian://copy?text=ssh%20apollo>)
```

Its creation command takes the payload from the clipboard and uses selected editor text as the label. Its source includes clipboard fallbacks, editor decorations, Reading-view treatment, and a modifier-hover preview. That is substantial existing functionality, not a hypothetical workaround. However, the label is interpolated into Markdown without escaping. Reproducing that expression with the label `Release ] notes` produced a broken label in a CommonMark parser. The preview also flattens newlines and truncates after 100 characters, so it cannot show the entire payload's exact whitespace. The clickable icon is a span. These findings are from source and a parser experiment, not an Obsidian UI test. [Pinned implementation](https://github.com/jldiaz/copy-protocol-plugin/blob/31fba5e798e1d55f128768d8602eb3000bfcb34a/src/main.ts).

**Buttons.** Its inspected `src/buttonTypes/copy.ts` really does call `navigator.clipboard.writeText(action)`. Do not assume this plugin requires a script to copy. Its inline model still refers to a button definition elsewhere, and the copy function does not await or handle the clipboard promise. The reviewed checkout's manifest is 0.9.13; older summaries or forks are not adequate evidence that the upstream project is deprecated. [Copy action](https://github.com/shabegom/buttons/blob/0fc70f37ff983353925882f0aebb51cb63e05ac6/src/buttonTypes/copy.ts), [README and inline model](https://github.com/shabegom/buttons/blob/0fc70f37ff983353925882f0aebb51cb63e05ac6/README.md).

**Meta Bind.** Its official guide describes YAML button blocks, an interactive builder, and inline references to a same-note definition or settings template. The documented action list I inspected has no dedicated clipboard action. Copying through its documented `inlineJS` action entails JS Engine plus enabling JavaScript. A shared command could avoid embedding scripts in every note, but per-instance payloads would still need a contract. [Button guide](https://www.moritzjung.dev/obsidian-meta-bind-plugin-docs/guides/buttons/), [inline JavaScript requirements](https://www.moritzjung.dev/obsidian-meta-bind-plugin-docs/reference/buttonactions/inlinejs/).

**Raw HTML and CSS are not a complete solution.** Obsidian sanitizes note HTML, including executable content. Styling a link cannot itself write to the clipboard; an active plugin must supply the behavior. A `javascript:` link or an HTML `onclick` snippet is therefore a poor product foundation. [Obsidian HTML limitations](https://obsidian.md/help/html).

## Critique of the request

### Where it pays off

Copy controls reduce selection errors for punctuation-heavy commands and long identifiers. More importantly, they put reusable text beside the context that explains when to use it. The value is not simply saving one keyboard shortcut: it is making the intended copy boundary explicit.

An independent label is worthwhile for long text. However, concealing the entire payload behind “Connect” makes correctness harder to inspect. Therefore a label must come with a preview and an accessible edit path. A button labeled “Copy” repeated fifteen times is poor information design; prefer the payload itself or a meaningful noun/action label such as “Address” or “Connect.”

### Where I would take another approach

If there are only a few visible multiline snippets, use ordinary code blocks first. If the same phrases are needed throughout many applications, a system text-expansion or snippet tool may be a better retrieval interface than opening Obsidian to find a button. If the desired value is the active note's path or a task reference, Bob already has a Copy Card; do not create a parallel templating system for that problem.

Bob's current `Cmd+Y` Copy Card already exposes paths, file names, task block IDs, and configured templates. It deliberately copies without writing the vault. This feature should complement that card with **note-local literal snippets**, preserving its existing command and key behavior. [Copy Card reference](https://github.com/bobs-org/bob-plugins/blob/36d48017f9a16edaf21346fb0276c530836e08f4/docs/copy-card.md).

The biggest cost of a custom solution is long-term editor integration. The clipboard call is small; selection behavior, source/rendered parity, pop-out windows, and theme compatibility are the work. Do not build a generic button framework merely to support this request.

### Explicit adjustments to the requirements

1. **A copy action should look and behave like a button**, even when compact enough to sit in prose. Reserve ordinary links for navigation.
2. **Use literal plain text in version one.** No evaluated JavaScript, template variables, shell execution, HTTP requests, or automatic clipboard reads. This keeps “what will be copied?” answerable locally.
3. **Support two text shapes:** inline text and multiline text. Trying to squeeze both into one URL or escaped single-line string makes creation unpleasant.
4. **Provide keyboard creation and keyboard activation.** Easy to type should also mean easy to reuse without reaching for a mouse. Leave the hotkey configurable; do not take `Cmd+Y`, normal Copy, or another existing Bob binding.
5. **Specify whitespace and newline behavior.** “Some text” is too vague when that text may be a command, path, or message.
6. **Keep all payloads in note source.** Labeling or collapsing content is presentation, not secrecy. Ordinary secret credentials belong in a password manager; this feature does not add protection to a synced note.
7. **Defer shared snippet IDs, dynamic references, rich-text copying, clipboard history, Publish support, and automatic paste.** They can be separate future decisions if actual use demonstrates a need.

These adjustments narrow implementation while adding the interactions necessary for the requested reliability and polish.

## Recommended authoring experience

### 1. The quick form: type what you want to copy

```markdown
Server: `copy: ssh apollo`
Email: `copy: bryan@example.com`
```

Typing `copy: ` inside a code span is sufficient. Ordinary code remains ordinary code. There is no mandatory modal or configuration file.

Offer a small completion for the `copy` prefix inside an inline-code editing context. Accepting the suggestion inserts `copy: ` and leaves the caret after the space. It must not intercept Tab when no completion is open, trigger in fenced examples, or transform content merely because it was pasted. Direct typing remains available when completion is disabled.

### 2. The labeled form: keep the text beside its name

```markdown
`copy[Connect]: ssh apollo`
`copy[Search]: from:alice@example.com subject:(quarterly review)`
```

The visible control is a quiet copy icon plus **Connect** or **Search**. Its payload is still right there when editing the source. Moving or duplicating the source moves or duplicates the entire definition; no IDs can collide.

Why this grammar over alternatives:

| Syntax family | Assessment |
| --- | --- |
| `[Label](obsidian://copy?text=...)` | Familiar outer Markdown, but URL encoding taxes every subsequent edit; useful compatibility alternative |
| `[Label](copy:...)` | Shorter URI, same encoding problem, plus a custom navigation-like scheme |
| `COPY[label\|text]` in normal prose | Few characters, but collides with Markdown punctuation and requires parsing ordinary prose |
| `copy[Label]: text` inside backticks | Reuses Markdown's literal-text container; short, readable, and explicitly opt-in |
| An inline reference to a separate definition | Good for shared reusable objects; unnecessarily splits a new one-off instance across two locations |
| YAML or JSON for every instance | Precise but imposes quoting, indentation, or escape overhead on routine creation |

### 3. The multiline form: a tiny literal block

````markdown
```bob-copy Address
123 Example Street
Example City, NY 10001
```
````

The text following `bob-copy` on the opening fence is an optional plain label. The body is literal text. Render this as a small snippet card: label and copy action above a short preview. A collapsed preview clearly shows the line count and offers “Show text.” Avoid requiring YAML `text: |` for the common case.

### 4. A selection command makes the syntax optional to learn

Provide **Bob: Make copyable**:

- With selected text, wrap it in the appropriate inline or fenced representation in one undoable editor transaction. A multiline selection selects the fenced form automatically.
- With no selection, insert an empty inline skeleton and place the caret at the payload position. Nothing touches the clipboard.
- If the selection is inside an existing ordinary code span and covers its payload, annotate that span rather than nesting backticks.
- With the caret inside an existing copy control, open **Edit copy text…** with a label input, literal text area, and rendered preview.

The editor handles fence length, special label characters, and table escaping. Saving changes the note once; canceling leaves it untouched. For an editor opened before intervening document changes, validate or map its source range before saving so stale offsets cannot overwrite unrelated text.

Do not introduce a global `/copy` trigger solely for this feature. It would broaden the editor's trigger vocabulary and need conflict handling. The inline prefix and a discoverable command are sufficient.

## The visual and interaction design

Beauty here means that a page still feels like a note. Use the theme's text, border, background, accent, and font variables. Avoid saturated default fills, emoji-sized icons, raised dashboard buttons, and individually configured colors on each instance.

A representative layout, with `⧉` standing in for a proper Lucide copy icon:

```text
Server access    [ ⧉ ssh apollo ]       [ ⧉ Connect ]

                                        Copy text
                                        ssh apollo

After success    [ ✓ ssh apollo ]       [ ✓ Connect ]

┌ Address ────────────────────── ⧉ Copy ┐
│ 123 Example Street                    │
│ Example City, NY 10001                │
└───────────────────────────────────────┘
```

Use a restrained rounded rectangle: approximately 5–6 px radius, a 1 px subtle border, and a 14–16 px icon. Use the body font for a custom label and the code font when displaying the literal payload. Keep short inline controls on the text baseline. Reserve icon space so hover and success never shift surrounding words. Long labels can truncate visually but retain their full accessible name and preview.

State behavior:

| State | Appearance and behavior |
| --- | --- |
| Rest | Copy icon always visible, quiet background, no animation |
| Hover or keyboard focus | Slight border/background emphasis; preview available without a modifier key |
| Writing clipboard | Suppress duplicate activation while the operation is pending; no premature checkmark |
| Success | Icon becomes a check for roughly one second; label and control width stay unchanged; polite “Copied” announcement |
| Failure | No success styling; persistent concise error with retry and a selectable full-text fallback |
| Editing | Source visible for the touched token; editing remains ordinary Markdown |

A preview may abbreviate long content, but must say it is abbreviated and provide an explicit full preview. Preserve line breaks in that preview. Show a trailing-newline indicator when present; do not secretly flatten a multiline command into one line. Previewing never copies.

Implement a native `<button type="button">` with an accessible name such as “Copy Connect.” Enter and Space activate it when focused; focus remains there. Provide **Bob: Copy text at cursor** for editor and Vim workflows, with no default hotkey until conflicts are checked. That command uses the same parser as clicking and never guesses at an unrelated nearby snippet. These semantics follow the distinction between an action button and a navigation link. [WAI button pattern](https://www.w3.org/WAI/ARIA/apg/patterns/button/).

Touch must not depend on hover. Use larger, well-separated targets in block cards and a touch-friendly full preview/edit action. Aim for 24 px desktop targets where layout permits and roughly 44 px block-card controls on touch. Inline prose has a WCAG target-size exception; that is not an excuse to make a tiny icon the only hit area. The whole labeled control should activate. [WCAG target-size guidance](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html).

For Live Preview, the widget must be present when the cursor is elsewhere **on the same line**. When a selection enters its source range, show the source. Test pointer ordering so a click on the widget copies before an editor selection change can destroy it. Never use copy-on-mousedown, which interferes with drag selection. Use an explicit edit context-menu action and normal keyboard movement into the source; avoid a double-click-to-edit scheme that first copies accidentally.

The optional editor/full-preview panel follows Bob's existing dismissal policy: Esc, Ctrl+[, and q outside text controls share the same close/back dispatch; q remains text inside the inputs. This respects `decisions:q-and-ctrl-bracket-mirror-esc`, read through the audited memory command during this research.

## The text contract

Before implementation, freeze the following small contract and its fixtures:

- An inline control is recognized only inside an actual Markdown inline-code token, with an exact lowercase `copy: ` or `copy[Label]: ` prefix. The single space after the colon is syntax; all subsequent characters are payload. Extra leading or trailing payload spaces are preserved.
- A label is optional, plain text, and nonblank. Within the label, support `\]` and `\\` to represent a closing bracket and a backslash. The payload itself has no custom backslash escapes: `\n` copies two characters, not a newline. No interpolation or recursive parsing occurs.
- Use Markdown code-span rules to obtain the inline token's content consistently in both renderers. Longer backtick delimiters support literal backticks. The command serializer handles delimiter selection and padding.
- Markdown inline code normalizes physical line endings to spaces. Therefore the creation command emits a fence for text containing a newline. Handwritten multiline inline code follows Markdown's documented normalization; it is not the exact-multiline form.
- For `bob-copy` fences, copy the literal body after Markdown container indentation is removed, normalize note line endings to LF, and remove **exactly one structural final LF** before the closing fence. An extra blank line before the closing fence preserves one intended trailing LF. Do not call `trim()` or `trimEnd()`. Use a closed fence and preserve any additional blank lines.
- Refuse an empty payload rather than silently clearing the clipboard. All-whitespace payloads remain possible but should have an explicit “whitespace only” preview.
- Percent signs, plus signs, ampersands, dollar signs, quotes, braces, Unicode, and shell-looking content are literal. “Copy” never runs or pastes that content.
- Invalid or incomplete syntax stays visible as text. A quiet diagnostic can explain it while editing; opening a note must not create a flood of error notices.

The block newline rule is a deliberate product choice, not an Obsidian guarantee. Removing the structural newline avoids adding an invisible Enter to ordinary copied shell commands while allowing an author to request one explicitly. The UI should reveal the resulting line count and trailing newline.

CommonMark explicitly normalizes newlines and certain boundary spaces inside code spans. Raw editor slicing and Reading-view `textContent` are therefore not interchangeable without normalization. [CommonMark code spans](https://spec.commonmark.org/0.31.2/#code-spans).

### Local parsing experiment

I used the environment's Python `markdown_it` parser in CommonMark mode, enabling its table rule. This validates the syntax rationale, not Obsidian's exact parser or clipboard behavior.

| Input case | Observed parser content |
| --- | --- |
| Simple and labeled forms | Preserved their `copy` prefix and payload |
| Two intended leading/trailing payload spaces | Preserved; the fixed prefix prevents accidental outer-space stripping |
| Payload containing a backtick, with padded double-backtick delimiters | Preserved the literal backticks after Markdown normalization |
| Windows-style path with backslashes | Preserved the literal backslashes |
| A pipe inside an escaped table-cell code span | Became a literal pipe, demonstrating that editor normalization must account for table context |
| A physical newline inside inline code | Became a space |
| Fenced body with one closing-boundary newline | Parser body ended in one LF |
| Same fence with an extra blank line | Parser body ended in two LFs |
| Copy Text Protocol's generated link with `Release ] notes` as label | Failed to render the intended labeled link |

Do not claim raw byte preservation across platforms: the contract concerns the specified Unicode text and newline convention. Operating-system clipboard representations and destination applications may apply their own line-ending conversions.

## Implementation recommendation and boundaries

Create a focused `bob-copy` plugin under `bob-plugins/plugins/`, rather than putting generic snippet rendering into the existing navigation plugin or bob-cli. Its behavior is local to Obsidian's editor and clipboard, and does not need a subprocess, daemon, vault-wide index, or network call. Reuse existing Bob visual and error-handling conventions without coupling the feature to task parsing.

Suggested components:

1. **Pure codec and model:** parse canonical inline content and fenced bodies, validate labels, serialize selections, and produce one immutable `{label, text}` value.
2. **Reading-view adapter:** a Markdown postprocessor for inline code and a code-block processor for `bob-copy`. Do not replace text inside arbitrary DOM nodes or activate examples within other fenced blocks. Make rendering idempotent.
3. **Live Preview adapter:** CodeMirror 6 decorations/widgets using syntax-tree context and the current editor buffer. Rebuild for relevant document, viewport, selection, and mode changes. Respect IME composition. A raw regular expression over the entire note is insufficient.
4. **Commands and editor:** insertion/conversion, edit, copy at cursor, and modest prefix completion. Use one editor transaction for a creation or edit.
5. **Clipboard and feedback:** one helper that takes the model's exact `text`, writes it on an explicit user gesture, and returns success/failure. Use the widget's owning window/document for pop-out windows. Dispose timers and listeners with the component lifecycle.

Obsidian's documented decorations support inserted and replacement widgets; its guidance favors viewport-driven view plugins when suitable. Inline widgets and multiline block replacement have different layout constraints: use a StateField/direct decorations when a block replacement affects viewport structure, rather than treating it as an oversized inline widget. [Obsidian decorations](https://docs.obsidian.md/Plugins/Editor/Decorations).

`navigator.clipboard.writeText` returns a promise that resolves after the clipboard update and can reject. Announce success only after fulfillment. Test in Obsidian's actual desktop and mobile environments; a browser API's support table is not proof that every embedded webview behaves identically. Start with that API and an honest failure path, adding a platform adapter only if real compatibility tests require it. [Clipboard writeText](https://developer.mozilla.org/en-US/docs/Web/API/Clipboard/writeText).

Bob already contains a suitable pattern: its Copy Card validates the payload, checks API availability, awaits the write, and returns a typed success/failure result. Use the pattern; do not import task-specific resolution just to copy a string. [Existing clipboard implementation](https://github.com/bobs-org/bob-plugins/blob/36d48017f9a16edaf21346fb0276c530836e08f4/plugins/bob-navigation-hotkeys/src/641-plugin-copy-card.js).

Avoid registering a global `obsidian://copy` protocol for the custom version unless external activation becomes an explicit requirement. Local controls need only local click handlers; avoiding a second route also avoids disagreement over percent-decoding, vault targeting, and dispatch. If compatibility with Copy Text Protocol is later wanted, add a deliberate importer that decodes once and writes canonical note-local syntax.

When the plugin is disabled, source remains legible code. Printing/PDF should remove interactive chrome and reveal the literal text, including text hidden by a label; a printed “Connect” button alone is useless. Do not promise interactive Obsidian Publish support. Keep a source-view fallback for embedded contexts that have not been verified.

The monorepo is the source of truth. Implementation work must follow its fragment/build conventions where applicable and deploy through `bob plugins sync`; never patch plugin files directly in the vault. This research makes no source or vault changes.

## What must be validated before shipping

| Area | Decisive acceptance cases |
| --- | --- |
| Exact payload | Unicode/emoji, combining characters, RTL text, pipes, backticks, backslashes, quotes, percent sequences, leading/trailing spaces, multiline and final LF; parse/serialize round trips |
| Mode parity | Reading view and Live Preview copy the same value; Source mode stays editable; copy-at-cursor works from the live unsaved buffer |
| Editor behavior | Same-line caret outside control; selection entering control; drag selection; IME; undo/redo; multiple cursors; two adjacent controls; pasted unfinished syntax |
| Context | Paragraphs, list items, blockquotes/callouts, tables, note embeds, and pop-out windows; code examples/frontmatter remain inert; unsupported contexts fall back visibly |
| Clipboard | Fulfilled/rejected/unavailable API; repeated rapid activation; no false success; retry and selectable fallback; no clipboard read during creation |
| Accessibility | Tab/focus traversal, Enter/Space, screen-reader naming/status, visible focus, touch targets, zoom and reduced motion |
| Appearance | Light/dark themes, long labels, small panes, high contrast, no layout shift, print/PDF with full text |
| Lifecycle/performance | Many snippets in a long note, scroll/re-render, edit while a preview is open, plugin unload/reload; no duplicated widgets or leaked listeners |

Start with a disposable note containing a command, a labeled query, a two-line address, literal backticks, and adjacent controls in a table. Validate actual Obsidian behavior before expanding the syntax. This is the most useful technical spike because it tests the difficult integration boundary, not merely whether a mocked clipboard function was called.

Deliver in reviewable slices: first the syntax/round-trip fixtures and dual-renderer spike; then creation/editing and reliable feedback; then accessibility, touch, export, and theme acceptance. Do not turn the spike into a shipping feature until the supported-mode matrix is explicit. No task beads or implementation changes were created as part of this research.

## Source snapshot ledger

These source revisions were opened through `sase repo open`; no repository files were fetched through web/API shortcuts.

| Repository | Inspected commit | Particularly relevant files |
| --- | --- | --- |
| `bobs-org/bob-plugins` | `36d48017f9a16edaf21346fb0276c530836e08f4` | `docs/copy-card.md`; navigation Copy Card model/clipboard mixin; `bob-emoji` EditorSuggest; editor-rendering examples; `AGENTS.md` |
| `jldiaz/copy-protocol-plugin` | `31fba5e798e1d55f128768d8602eb3000bfcb34a` | `README.md`, `src/main.ts`, `manifest.json` (1.1.6) |
| `ozavodny/obsidian-copy-inline-code-plugin` | `f885d1108c5f8950cfb28752ec95483caca358f0` | `src/main.ts`, `src/copy-inline-code-view-plugin.ts`, icon/widget/clipboard modules, manifest (2.1.0) |
| `shabegom/buttons` | `0fc70f37ff983353925882f0aebb51cb63e05ac6` | `README.md`, `src/buttonTypes/copy.ts`, copy builder in `src/modal.ts`, manifest (0.9.13) |

Official documentation linked beside claims was consulted on 2026-11-19. Existing marketplace feature descriptions were discovery aids; source inspection informed the detailed implementation assessments. No installation, end-to-end UI validation, or clipboard write was performed.

## Recommended solution

Build **Bob Copy** as a small plugin in `bob-plugins`: explicit `copy: text` and `copy[Label]: text` inline-code controls, a literal `bob-copy` fenced form for multiline text, and a **Make copyable** command for selected text. Render quiet native buttons with an always-visible copy icon, honest success/failure feedback, full payload inspection, and equal keyboard support. Store each definition entirely in the note and keep copying free of note mutations.

This is justified by the requested typing experience and Bob's established plugin infrastructure. If the priority changes to “working today with no custom maintenance,” use **Copy Text Protocol** as the first trial, with the escaping and accessibility checks above. Keep ordinary code blocks for already-visible long snippets and the existing Copy Card for contextual file/task references. The new feature should remain one dependable action: **copy exactly the declared text**.
