# Ctrl+Y in Bob Refs: a Copy menu for references, excerpts, and identifiers

Independent research by **cdx**, 2026-10-14. This is design research, not an implementation. No other report or researcher findings from this swarm were consulted. Sources were the local bob-cli and bob-mac-capture checkouts, audited project memory, and primary product documentation. I did not inspect Bryan's live reference library, run the app on macOS, or measure interaction latency; the examples and dimensions below are proposals.

**Assessment.** This is a good idea if it becomes a small, predictable “Copy…” surface. It should help answer three recurring questions: “How do I point someone or another note at this reference?”, “How do I reuse a useful passage?”, and “Which identifier or file location does this tool need?” The strongest feature is a source-linked excerpt that preserves the distinction between the author's words and Bryan's own comment. The marker ID is useful, but should not dominate the design.

I recommend retaining the requested **Ctrl+Y**, opening a compact menu inside the existing Refs panel, and assigning stable letters to common outputs. Add an annotation chooser for individual highlights and notes. Keep the current search, selection, and panel open after a successful copy, with a short confirmation. This preserves the panel's fast browsing workflow.

The requirements need three explicit adjustments: scalar outputs get one letter after Ctrl+Y; choosing among arbitrarily many annotations needs a second chooser; the default ID action copies the reference note's `id` and is named accordingly, rather than claiming to have read the live PDF marker. These are explained below, together with an optional way to support exact live marker access.

**What the implementation already gives us.** The following are source observations, not assumptions about the app.

| Observation | Why it matters | Local source inspected |
| --- | --- | --- |
| ⌘K already offers Copy Wiki Link and Copy PDF Path. Its menu is an `NSMenu` anchored below the selected result. | Reuse the actions and copy service; Ctrl+Y is another entrance to copying, not a competing implementation. | [RefsActionsMenu.swift](https://github.com/bobs-org/bob-mac-capture/blob/44051a0039a711035ff67b5383c4116d294c4ee1/Sources/BobMacCapture/Refs/RefsActionsMenu.swift), [RefsPanel.swift](https://github.com/bobs-org/bob-mac-capture/blob/44051a0039a711035ff67b5383c4116d294c4ee1/Sources/BobMacCapture/Refs/RefsPanel.swift#L137) |
| Copying currently calls `NSPasteboard.general.clearContents()` and `setString`, discards the returned result, then shows a 1.5-second footer toast. | The existing toast duration is suitable. Reporting success needs a checked write result. | [RefsActionsMenu.swift](https://github.com/bobs-org/bob-mac-capture/blob/44051a0039a711035ff67b5383c4116d294c4ee1/Sources/BobMacCapture/Refs/RefsActionsMenu.swift), [RefsPanelModel.swift](https://github.com/bobs-org/bob-mac-capture/blob/44051a0039a711035ff67b5383c4116d294c4ee1/Sources/BobMacCapture/Refs/RefsPanelModel.swift#L775) |
| A `RefItem.id` is the reference **note path**, deliberately used because PDF stems can repeat. | It must never supply the menu's “Reference ID” value. | [RefsModel.swift](https://github.com/bobs-org/bob-mac-capture/blob/44051a0039a711035ff67b5383c4116d294c4ee1/Sources/RefsCore/RefsModel.swift#L268) |
| The backend already reads frontmatter `id` into `RefRow.id`, but marks it `skip_serializing`. | The requested identifier is already parsed in bob; the app needs an additive JSON field, not a second parser. | [row.rs](https://github.com/bobs-org/bob-cli/blob/f24d5e7daf3e8349dd03505da413317934f2cf41/src/native/ref_library/row.rs#L45), [mod.rs](https://github.com/bobs-org/bob-cli/blob/f24d5e7daf3e8349dd03505da413317934f2cf41/src/native/ref_library/mod.rs#L531) |
| The inspector requests `bob ref show <path> -f json -c`. It then keeps only `kind == highlight` with a nonempty comment. | An “all highlights and notes” browser cannot reuse the displayed inspector notes as its complete dataset. Plain highlights, standalone notes, and images need separate handling. | [RefsFetching.swift](https://github.com/bobs-org/bob-mac-capture/blob/44051a0039a711035ff67b5383c4116d294c4ee1/Sources/RefsCore/RefsFetching.swift#L46), [RefsInspector.swift](https://github.com/bobs-org/bob-mac-capture/blob/44051a0039a711035ff67b5383c4116d294c4ee1/Sources/RefsCore/RefsInspector.swift#L83) |
| `ref show` already emits `quote`, `comment`, `asset`, `block_id`, `link`, `own_notes`, annotation parse status, and exclusion counts. Swift currently ignores several of these. | Much of the feature is client decoding and presentation. Existing backend annotation semantics can remain authoritative. | [docs/ref.md](https://github.com/bobs-org/bob-cli/blob/f24d5e7daf3e8349dd03505da413317934f2cf41/docs/ref.md#L228), [show.rs](https://github.com/bobs-org/bob-cli/blob/f24d5e7daf3e8349dd03505da413317934f2cf41/src/native/ref_library/show.rs#L30), [RefsInspector.swift](https://github.com/bobs-org/bob-mac-capture/blob/44051a0039a711035ff67b5383c4116d294c4ee1/Sources/RefsCore/RefsInspector.swift#L38) |
| Inspector hydration waits 120 ms, is cancellable, and caches show results by note path and snapshot time. | Ctrl+Y may arrive before hydration finishes. Copy loading must bind to the reference selected when the menu opened. | [README inspector contract](https://github.com/bobs-org/bob-mac-capture/blob/44051a0039a711035ff67b5383c4116d294c4ee1/README.md#L1377), [RefsInspectorLoader.swift](https://github.com/bobs-org/bob-mac-capture/blob/44051a0039a711035ff67b5383c4116d294c4ee1/Sources/BobMacCapture/Refs/RefsInspectorLoader.swift#L435) |
| PDF summaries are display excerpts: summary paragraphs cap at 360 characters, abstracts at 420, and summary bullets at three. | Copying a displayed excerpt must say “excerpt”; it cannot promise a complete abstract or summary. | [RefsInspector.swift](https://github.com/bobs-org/bob-mac-capture/blob/44051a0039a711035ff67b5383c4116d294c4ee1/Sources/RefsCore/RefsInspector.swift#L306) |
| The panel is normally 880 × 560 pt, with adaptive colors, an existing glass shell, and Reduce Motion / Reduce Transparency behavior. | Fit the menu into the existing visual language. No new floating window or extra layer of glass is needed. | [RefsVisualTokens.swift](https://github.com/bobs-org/bob-mac-capture/blob/44051a0039a711035ff67b5383c4116d294c4ee1/Sources/BobMacCapture/Refs/RefsVisualTokens.swift), [RefsPanelView.swift](https://github.com/bobs-org/bob-mac-capture/blob/44051a0039a711035ff67b5383c4116d294c4ee1/Sources/BobMacCapture/Refs/RefsPanelView.swift) |

The project decision “Bob Mac Capture Is A Thin Client Of bob” also governs this work. Reference identity and annotation parsing belong in bob's JSON interfaces; Swift owns presentation, keyboard routing, and clipboard writing. The existing PDFKit preview is a reasonable source for a clearly labeled preview excerpt. It is not a reason to invent a Swift PDF-marker parser.

**What outside products and macOS suggest.** Apple's menu guidance favors clear action labels, important actions first, logical grouping, and consistent icon treatment. Its keyboard guidance says to respect standard shortcuts. Those principles support a compact, labeled menu and argue against a large novelty interface. The in-panel menu proposed here is my design choice, not an Apple-prescribed component. [Apple menus](https://developer.apple.com/design/human-interface-guidelines/menus), [Apple keyboards](https://developer.apple.com/design/human-interface-guidelines/keyboards/).

There is a real shortcut collision: macOS text editing uses Control-Y to paste from the app-local clipboard populated by Control-K. Refs already repurposes several Control keys for navigation, so the requested binding is defensible in this specific panel. It should be documented as a Refs command and should not become a global shortcut or override an annotation-search editor. During marked-text composition, pass it through. Preserve ⌘C for ordinary selected text rather than redefining it as “copy reference.” [Apple's Mac keyboard shortcuts](https://support.apple.com/en-us/102650).

Zotero provides a useful precedent for copying a reference in a chosen format: its Quick Copy supports bibliography entries, citations, and export formats such as BibTeX and RIS. The implication for Bob is to name the copied output clearly. It is not a reason to build a citation-style engine into this feature. [Zotero Quick Copy](https://www.zotero.org/support/creating_bibliographies#quick_copy).

Zotero's annotation-to-note workflow retains citations and links back to the PDF. Its templates distinguish highlighted text, citation, and comment. This supports making provenance the default for a Bob excerpt while providing explicit plain-text and comment-only alternatives. [Zotero PDF reader](https://www.zotero.org/support/pdf_reader#adding_annotations_to_notes), [Zotero note templates](https://www.zotero.org/support/note_templates#annotations).

**The menu I would ship.** Use the user-facing name **Copy…**, not “Yank.” Display the reference title and kind at the top so it is always clear whose data will be copied. Use ten stable letter assignments, arranged in three groups. A normal scalar action is `Ctrl+Y`, then one letter; no Return is required.

| Key | Menu label | Clipboard payload and useful preview | Availability |
| --- | --- | --- | --- |
| `l` | Copy note link | Bob's `link` verbatim, such as `[[ref/books/example]]`. Preview the actual target. | Available from the library row. |
| `u` | Copy source URL | The primary valid HTTP(S) source URL. Preview its host and meaningful path. | Disabled if no valid public source is stored. |
| `o` | Copy Obsidian link | An `obsidian://open` URI made with the existing URL builder and configured absolute note path. | Available when the note path resolves. Label the preview “Opens this vault on this Mac.” |
| `i` | Copy reference ID | The exact nonempty frontmatter `id`, exposed as JSON `reference_id`; no brackets or prefix. | Disabled with “No reference ID” when absent; “Bob update needed” if the field is unsupported. |
| `t` | Copy title | The display title's text, using `TaskDisplayText.text`; no subtitle, kind chip, or disambiguation suffix. | Available from the library row. |
| `p` | Copy PDF path | Absolute filesystem path, as the existing action does. No quotes, escaping, or `file://` conversion. | Validate path safety; show “PDF missing on this Mac” if the file is absent. |
| `c` | Copy source credit | A readable line with known author, known publication date, title, and primary source URL. Missing metadata is omitted. | Available with a title; not labeled APA, Chicago, or a formal citation. |
| `h` | Highlights & notes… | Opens the annotation chooser described below. Preview the known count, or “Loading annotations…”. | Requires parsed annotation data; loading, absent, and unparsed are distinct states. |
| `n` | Copy my written notes | `own_notes` verbatim, preserving Markdown and paragraph breaks, excluding generated annotations and tasks. | Enabled only when nonempty. This is not the inspector's commented-highlight list. |
| `b` | Copy reference brief | Deterministic Markdown: title, known byline/date, source URL, local note link, and an optional labeled **summary excerpt** or **abstract excerpt**. | No new AI generation; an unavailable excerpt is omitted. |

The first group is links (`l/u/o`), the second is identity and location (`i/t/p/c`), the third is reusable material (`h/n/b`). The letters and row positions do not change between reference types. Keep missing common options visible but disabled, with a short reason. Do not let asynchronously arriving metadata change what a letter means or move a row underneath the pointer.

For `u`, use stored `source_url` precedence represented by bob's ordered URLs, and accept only HTTP(S) URLs. Show the chosen value before copying; do not silently exchange it for a DOI or arXiv resolver URL. If future metadata exposes an explicit preferred source, use that. The extended formats drawer can offer all stored source URLs. Do not treat a raw opaque identity key as a usable URL.

For `o`, reuse `ObsidianOpenURL.url(forAbsolutePath:)` and URL components rather than constructing an escaped URI by string concatenation. This link and the PDF path are local capabilities, not public sharing URLs. The ordinary note link should remain the first action because it is the natural output inside the Bob vault. [Existing ObsidianOpenURL.swift](https://github.com/bobs-org/bob-mac-capture/blob/44051a0039a711035ff67b5383c4116d294c4ee1/Sources/CaptureCore/ObsidianOpenURL.swift).

For `c`, call it “source credit” rather than “citation”: Bob does not consistently have journal, publisher, volume, issue, or a structured author list. An illustrative payload is `Brendan Gregg · Systems Performance · https://example.com/book`. A known publication date can be inserted; a git-added date must never substitute for it. This action should be useful with partial metadata, without manufacturing bibliographic certainty.

For `b`, the brief is a small handoff to another person or an AI conversation. It should not silently include every highlight, private annotation, task, frontmatter key, or the full PDF. It is an authored formatting operation over known fields, not an inferred synopsis. Preserve the excerpt label and any truncation indicator. If complete excerpts become a requirement, extend extraction to retain full content separately; never strip an ellipsis and claim completeness.

**The important ID distinction.** There are at least four different things a user could mean by “ID”: the app's row identity (note path), frontmatter/marker `id`, an annotation's `h-…` block ID, and an external DOI or arXiv identifier. They must have different labels and separate fields.

Bob's marker is the first standalone `/Text` note annotation on PDF page 1. The grammar allows an `id` property; `bob ref create -i` can stamp it. The marker and reference frontmatter participate in synchronization that can be pending or conflicting. Therefore the reference note's current `id` is not proof of the PDF's current marker value. [Marker grammar and sync contract](https://github.com/bobs-org/bob-cli/blob/f24d5e7daf3e8349dd03505da413317934f2cf41/docs/highlights-ref-sync.md#L432).

My deliberate requirement adjustment is to ship **Copy reference ID** first, with an explanatory preview such as “From note metadata; PDF marker may differ.” Expose the already parsed scalar as `reference_id` in `ref list`/`ref show`. An absent ID must not fall back to a filename, path, generated UUID, or DOI. Note titles and IDs often resemble a PDF stem, but resemblance is not authority.

If copying the **exact live marker ID** is a must-have, do that honestly as a separate action in the extended formats drawer. Extend the existing read-only `bob ref marker <pdf>` with machine-readable JSON, returning marker properties and source provenance, then request it on demand. Its current public interface has no JSON-format option. Do not scrape human output, read the PDF marker in Swift, or run `scan -w` to manufacture a value. If adding `-f/--format human|json`, follow the project's CLI help/alias rules and retain current human behavior. This is a larger backend change than exposing `reference_id`, and should be selected only if the literal live-PDF distinction matters to Bryan. [Existing command contract](https://github.com/bobs-org/bob-cli/blob/f24d5e7daf3e8349dd03505da413317934f2cf41/docs/highlights-ref-sync.md#L104).

**Choosing an individual highlight or note.** `h` enters an annotation browser inside the same overlay. This is the one justified exception to “one key copies everything”: a reference can have hundreds of passages, and the panel currently has no individually selected annotation. Assigning all passages permanent letter keys would be neither possible nor learnable.

The browser shows all live annotations, including uncommented highlights, standalone notes, and image annotations. Keep source document order, show page labels as supplied by bob, and use visible text labels such as “Highlight,” “Your note,” and “Figure.” Search covers quote and comment text. A counter says `Showing 1–9 of 42 annotations`; it must not borrow the inspector's three-note pagination setting.

Give the visible nine rows `1–9`. One digit copies that row in the default **excerpt with source** format. Page Down or Next changes the visible slice and its digits; the row content and digit labels update together. Up/Down and Return are equivalent accessible paths. Search has a real field, entered by `/` or a click; when that field is editing, digits are text and Return copies the selected match. Esc first leaves search editing, then returns to the Copy menu, then closes it. This avoids making it impossible to search for a page number or a date.

For the currently focused annotation, show additional one-key outputs: `q` copies the quote's plain text, `m` copies only Bryan's comment, `l` copies bob's annotation block link, and `e` copies the complete excerpt with source. Disable quote/comment actions when their corresponding content is absent. These keys belong to the annotation list's focus mode, not the search editor. The footer names the active format; no hidden “last used format” changes what a number key copies.

The default Markdown excerpt has three visually separate parts:

```markdown
> Latency is not throughput.

My note: Compare this with SLO notes.

— [[ref/books/example#^h-2b91f0a4c7de]] · Page 12
```

This illustrative example follows Bob's existing generated annotation format. Use the annotation `link` from bob rather than rebuilding it from a title or an ordinal. Prefix every line of a multiline quote with `>`; preserve the comment's paragraph breaks. A standalone note contains the user's text plus source link, without pretending that it is an author's quotation. A quote-only alternative copies the complete quote string without adding attribution, typographic quotation marks, or Markdown wrappers.

Image annotations need honest options. In the first release, copy the annotation block link or, where `asset` exists, the Obsidian asset embed and separate comment; label this “Figure link/embed.” Do not call a textual link “image copied.” Actual image bytes can be a later format using a typed pasteboard item, with an explicit missing-asset state. A picture cannot be reduced to a nonexistent quote string. [Bob annotation and asset formats](https://github.com/bobs-org/bob-cli/blob/f24d5e7daf3e8349dd03505da413317934f2cf41/docs/highlights-ref-sync.md#L915).

Add `Copy all excerpts` as a labeled button in this browser, with the count and payload size visible. It is a deliberate bulk action, not a root shortcut that might unexpectedly copy a book's worth of text. Exclude marker mirrors, preamble, and removed/tombstoned highlights using the existing backend parser. An unparsed managed region is an unavailable structured export, not an empty collection and not an excuse to silently substitute raw Markdown.

Annotations are the last Highlights-scan snapshot, not unsaved live PDF annotations. State that near the browser's header, with the snapshot time when known. A refresh may reread the reference note; it does not automatically scan or write PDFs. Useful data can remain available when the local PDF is missing, because the saved reference note is the source of annotation text. [Reference-library snapshot semantics](https://github.com/bobs-org/bob-cli/blob/f24d5e7daf3e8349dd03505da413317934f2cf41/docs/ref.md#L46).

**Other useful copy formats, without overloading the first menu.** A broad inventory is worthwhile; putting it all at the top level is not. Add a small “More formats…” disclosure after the first release if actual use warrants it. Keep extensions outside the ten stable root shortcuts.

| Candidate | Likely use | Recommendation |
| --- | --- | --- |
| DOI value and DOI resolver URL | Pasting into scholarly lookup tools or sharing a durable external identity. | High-value extension; distinguish the value from the URL and use the known identity fields. |
| arXiv ID and arXiv abstract URL | Paper retrieval, capture, comparison, or citation tooling. | High-value extension; preserve a stored version suffix where it is present. |
| Markdown public link `[Title](URL)` | Emails, GitHub comments, web notes, and plain-text writing. | High-value extension; escape label/URL syntax correctly. |
| Absolute note path / vault-relative note path | Terminal commands, editor navigation, debugging. | Useful, but distinguish both from reference ID and PDF path. |
| PDF file URL / PDF file object | Clickable local paths or attaching a file to Finder/Mail. | Useful later; a file object uses typed pasteboard data and is a different promise from text. |
| Annotation block ID, wikilink, or embed | Linking or embedding a specific passage in Obsidian. | Block link belongs in the initial annotation chooser; raw ID/embed can be extended formats. |
| Reading-task link | Returning to the task that controls reading progress. | Useful when the task is unambiguous; use the existing task link, since v2 tasks may live elsewhere. |
| Narration/audio path or URL | Passing the listening asset to a player or script. | Useful for narrated references; remain disabled when absent or unsafe. |
| Parent link, aliases, and topics | Filing, tag reuse, or note templates. | Lower priority; expose only when a concrete workflow appears. |
| Metadata JSON | Agent handoff or automation. | Later, with a documented safe field allowlist; avoid a raw frontmatter dump. |
| Bibliography, BibTeX, RIS, citekey | Academic publishing. | Defer formal export until metadata completeness and an authoritative exporter exist. Do not invent citekeys from marker IDs. |
| PDF outline, page count, summary excerpt | Document orientation and discussion. | Reasonable additional formats, clearly labeled; preserve hierarchy where available and distinguish excerpts from full sections. |
| Full PDF text | Feeding a document to another tool. | Defer: extraction, layout, encrypted PDFs, OCR, size, and fidelity are a separate feature. |
| New AI-generated summary | A newly authored synthesis. | Outside this copy feature; introduces generation, provenance, latency, and possible network use. |
| Complete marker property list | Repairing or duplicating a PDF marker. | Specialized; if offered, bob must provide the authoritative rendered representation. Do not synthesize lifecycle status from display chips. |

**Make it beautiful through clarity.** Use a small, calm card on the existing panel surface. Its title is “Copy from [reference title]”; a second line gives kind and source context. The letter keycaps form a right-aligned column, labels form the main column, and secondary text shows a short actual value or unavailable reason. Use the kind tint only in the small header glyph; the action list uses adaptive system text and selection colors. A single hairline separates groups.

An illustrative root layout is:

```text
┌─────────────────────────────────────────────────────┐
│  Copy from Systems Performance                      │
│  Book · Brendan Gregg                               │
│                                                     │
│  Note link       [[ref/books/example]]           l   │
│  Source URL      example.com/book                u   │
│  Obsidian link   Opens this vault on this Mac     o   │
│  ────────────────────────────────────────────────   │
│  Reference ID    example                         i   │
│  Title           Systems Performance             t   │
│  PDF path        …/lib/books/example.pdf          p   │
│  Source credit   Author · Title · URL             c   │
│  ────────────────────────────────────────────────   │
│  Highlights & notes…   42 annotations             h   │
│  My written notes      3 paragraphs               n   │
│  Reference brief       Metadata + excerpt         b   │
│                                                     │
│  Press a letter to copy · ↑↓ then ↵ · Esc back       │
└─────────────────────────────────────────────────────┘
```

The wireframe shortens “Copy…” labels for space; accessible names retain the action verb. Secondary previews can elide long strings visually, but clipboard payloads remain complete. Render local paths with middle truncation, public links with the host visible, and identifiers in a modest monospaced style. Do not make the whole interface monospaced.

Start the prototype around 520 pt wide, with 36 pt rows, a 54 pt header, a 28 pt footer, and modest group spacing. This can fit ten rows in approximately 490 pt; clamp to the current panel bounds and permit scrolling on smaller screens. These are proposed dimensions, not measured layout results. Use the existing well radius and colors rather than adding another glass window. A stable centered card is preferable to following a selected row near the panel's bottom edge.

The root list is deliberately compact. Hover or arrow focus can show the full payload preview in an adjacent or expandable preview area, but direct letters must never require hovering. The annotation browser gets more of the panel's content area because identifying a passage needs readable text. On narrow panels, replace the content well for the duration of the chooser rather than depending on the inspector column, which can disappear below 760 pt.

Success closes the Copy overlay, keeps Refs open, restores the same reference and query, and replaces the footer hint with `Copied reference ID`, `Copied excerpt · Page 12`, or the appropriate outcome for 1.5 seconds. Keep a visible, clickable `Copy… ⌃Y` affordance and a `Copy…` item in ⌘K for discovery; avoid adding still more text to an already long footer hint string.

Opening and closing can use the app's existing short animation rhythm; suppress movement under Reduce Motion. Under Reduce Transparency, use an opaque system background; Increase Contrast must retain a clear focus outline and readable disabled-state explanations. Expose the overlay's title, action buttons, disabled reasons, and selection to VoiceOver. On dismissal return accessibility focus to the invoker, and announce the copy outcome without reading an entire private passage aloud. These reuse accessibility accommodations already present in the panel rather than adding a separate aesthetic system. [Existing panel accessibility implementation](https://github.com/bobs-org/bob-mac-capture/blob/44051a0039a711035ff67b5383c4116d294c4ee1/Sources/BobMacCapture/Refs/RefsPanelView.swift), [Mac display accessibility settings](https://support.apple.com/en-ie/guide/mac-help/unac089/27/mac/27).

**Implementation choices and tradeoffs.**

| Approach | Strengths | Costs or limits | My judgment |
| --- | --- | --- | --- |
| Extend the existing ⌘K `NSMenu` only | Least code; native pointer, keyboard, and accessibility behavior. | Mixed open/scan/copy actions; no dedicated rapid-copy surface; weak payload previews. | Good low-cost alternative, but underserves the requested interaction. |
| Add a dedicated native `NSMenu` for Ctrl+Y | Reuses anchoring and hide-on-resign suspension; plain key equivalents can be configured. | Must verify actual unmodified-letter activation during popup tracking, existing local-monitor interaction, and non-US layouts; richer annotation browsing still needs another UI. | A credible smaller implementation. Do not reject it merely for looking native. |
| Add an in-panel Copy overlay and annotation browser | Stable keys, clear value previews, unified transitions, no popup-tracking handoff, good room for excerpt provenance. | More focus, event-routing, accessibility, and visual tests. | Recommended given the explicit priority on intuitive, reliable, beautiful design. |
| A separate floating palette/window | Potentially reusable across apps. | Another focus owner and dismissal boundary; more room for panel coordination bugs. | Unnecessary for this scope. |

Apple exposes `NSMenuItem.keyEquivalent` and `keyEquivalentModifierMask`; this makes a native prototype possible. It does not by itself prove how every unmodified key behaves while this app's popup tracks. If schedule pressure favors native menus, prototype `Ctrl+Y → l` first on a Mac with the existing local monitor enabled. Do not replace menu items with arbitrary custom views and assume native keyboard/accessibility behavior survives. [NSMenuItem API](https://developer.apple.com/documentation/appkit/nsmenuitem), [Modifier mask API](https://developer.apple.com/documentation/appkit/nsmenuitem/keyequivalentmodifiermask).

For the recommended overlay, add a pure copy catalog and formatter to RefsCore, a focused state model, and a small SwiftUI presentation. A possible state shape is `closed → root(reference snapshot) → annotations(reference snapshot, filter, page) → closed`. A copy action produces a payload or a typed unavailable/loading/error state before it touches AppKit. The UI and ⌘K call the same copy service. Keep actions typed rather than a set of independently copied strings scattered through views.

Route keys in this order: marked-text / active text editor rules; active Copy overlay; normal Refs commands; normal text handling. When the root is active, letters and arrows belong to it and must not change the original reference query. Unknown printable keys are consumed there, with a quiet hint if needed; they must not invisibly edit the search field behind the card. Cmd-Q and other ordinary app-level commands should retain their usual handling. Ctrl+Y again closes the root; auto-repeat on the opening event must not toggle it repeatedly.

Use logical characters for letter mnemonics, with deliberate handling of Caps Lock, rather than assuming US hardware positions from `keyCode`. The existing router is based on key codes, so this is a concrete extension to its event input. Ignore accidental extra Command/Option combinations; while a real text editor is active, Control-Y keeps its editing meaning. Document that the Refs library filter is a command-oriented field, while the new annotation filter is a normal editor. Test both non-US Latin layouts and IME composition rather than claiming support from inspection alone.

Freeze the target using the note path plus the loaded library/snapshot generation when the menu opens. On background refresh, keep that target; do not reread `selectedItem` at copy time and accidentally copy another reference. Retain an explicit operation token for lazy loads, and discard their results after dismissal or a target change. If the same target's content changes while the chooser is open, offer a refresh or reopen; do not silently relabel numeric annotations underneath the user's next keypress.

**Data changes should be small and additive.** In bob-cli, expose `reference_id` from the existing frontmatter parser in schema-1 reference rows, present as `null` when absent. Keep path identity unchanged. In Swift, add optional decoding for it and distinguish a missing key from a present null so older bob versions say “Bob update needed,” while a supported row with no ID says “No reference ID.” Audit reference JSON fixtures and parity checks affected by the added field.

Decode `own_notes`, annotation `block_id`/`link`/`asset`, parse status, exclusion counts, and snapshot provenance. On opening the material actions, fetch `bob ref show <exact note path> -f json` **without `-c`**. Either keep a separate copy-detail loader or add a details mode; include the mode in cache keys so a cached comments-only response cannot satisfy a full-annotation request. Keep the existing inspector behavior unless its scope is separately changed.

Use a separate process lane for copy-detail fetching, because canceling a `refs-show` inspector request should not cancel a copy request for the frozen reference. The existing response includes full structured content; a new `ref copy` command is unnecessary for the proposed first release. No new persistence of copied text is needed, and there should be no new clipboard-content telemetry. The formatting logic can remain local over authoritative JSON; if another client later needs the same exports, move shared export policy into bob rather than duplicating it.

**Reliability is part of the design.** Construct and validate the entire payload before clearing the general pasteboard. For text use a plain-string representation; for a later actual-file or image action use the proper typed representation. Perform AppKit interaction on the appropriate UI execution context. Change `RefsPasteboardWriting.copy` to return a result or throw, and show success only after a successful write. Apple's APIs return a success flag; the current implementation discards it. [setString return behavior](https://developer.apple.com/documentation/appkit/nspasteboard/setstring%28_%3Afortype%3A%29), [writeObjects return behavior](https://developer.apple.com/documentation/appkit/nspasteboard/writeobjects%28_%3A%29).

Cancel, absent data, a failed lookup, and a disabled action must leave the clipboard untouched. After the pasteboard has been cleared, an OS write failure may already have replaced or emptied its previous contents; do not promise rollback that AppKit does not provide. Do not read and restore a previous clipboard snapshot, which can overwrite a concurrent copy from another app. Report `Could not copy; try again` and keep the chooser open.

Disable unavailable choices with explanations; distinguish “Loading,” “No annotations,” “Annotations unavailable,” “PDF missing,” and “Unsupported by this Bob version.” Do not write an empty string as a substitute. Never truncate a successful copied passage to match the visual preview. For very large bulk exports, show the size and require an explicit bulk action, or refuse above a documented bound; avoid a vague success toast for silently partial content.

Missing or locked PDFs should disable PDF-dependent formats only. A saved block link, note title, source URL, or annotation snapshot can still be usable. Path safety should reuse the existing vault-relative validation, with no shell invocation or manual quoting. Local note/PDF URLs are copied exactly as local outputs; a public-sharing action must not accidentally return them.

**What should be verified before implementation is considered done.** These are meaningful acceptance cases, not a request to run tests for this research report.

- Every root key maps to the documented output; opening/canceling never copies; disabled shortcuts never erase the clipboard; Ctrl+Y has no effect outside Refs. IME and actual text-editor passthrough remain correct.
- Open on reference A, refresh or move the background selection to B, then copy: the payload is still A. A slow result arriving after dismissal cannot reopen the card or change the clipboard.
- Duplicate PDF stems remain distinct by note path. `RefItem.id` can never leak into `reference_id`. Missing scalar IDs remain missing.
- Full-detail decoding includes uncommented highlights and standalone notes, retains separate quote/comment fields and stable links, and ignores removed/marker-mirror blocks. Comments-only and full-detail caches cannot contaminate each other.
- Exact copied strings preserve Unicode, multiline quotes, Markdown comments, and complete paths. Titles/URLs with brackets, parentheses, spaces, percent signs, `#`, `+`, and non-ASCII characters are represented correctly in their chosen format.
- Pasteboard failure returns an error and no success toast. Empty and oversize payload decisions occur before clearing it. Actual image/file formats advertise the correct pasteboard types if implemented later.
- Annotation digits copy the displayed slice; filtering numbers works while editing; Escape returns through the chooser without clearing the original Refs query or scope. Arrow/Return, pointer clicks, VoiceOver, and Full Keyboard Access can complete the same tasks.
- Design snapshots cover light/dark, increased contrast, reduced transparency/motion, long titles and paths, empty states, loading, errors, narrow panels, and dense annotation results.

The mac-capture repository requires compilation, not merely visual review. Portable core checks cover catalog/formatting logic; AppKit and SwiftUI changes also need a scratch Mac build with `bundle.sh` and `just typecheck-tests`, and macOS CI runs actual tests. If the Mac is unavailable, report that the macOS targets remain unverified. This research changed no Swift or Rust and does not claim those checks have been run.

For a quick usability check, ask Bryan to perform four concrete tasks with representative references: copy a reference ID, copy a public source link, find and copy one commented excerpt, and reuse his written notes. Check whether he can predict each payload from the label, whether he notices local versus public links, and whether he expects Ctrl+Y to copy text immediately. Observe errors and extra navigation; do not infer that more options means more value. These results should decide whether DOI/arXiv, file objects, or formal citations deserve prominent positions later.

**Critique of the original plan.** A dedicated copy surface is useful because the panel has a selected reference and already exposes relevant metadata. The risk is turning a quick-open panel into an export workbench. A sprawling alphabet menu, unpredictable per-type shortcuts, overlong public/local link lists, and fake “copy citation” output would make the panel harder to learn. Keeping a compact root and a focused annotation browser addresses that risk.

I would not replace this with a global launcher command or redefine ⌘C. I would also not abandon Ctrl+Y solely because macOS uses it in text editing: the requested shortcut can coexist with the current panel's command-oriented Control bindings if its scope is explicit. A click and ⌘K entrance are necessary because the shortcut alone is undiscoverable. A native Ctrl+Y menu is a credible smaller alternative if the richer overlay proves too expensive; the underlying catalog and payload contracts should remain identical.

The adjusted requirements are therefore explicit: **(1)** one key after Ctrl+Y for a scalar or named aggregate format; **(2)** another chooser for arbitrary annotations; **(3)** reference-note ID by default, with literal live marker ID available only through an authoritative backend extension; **(4)** saved annotation snapshot semantics; **(5)** common missing options stay visible with reasons; **(6)** successful copying keeps Refs open; **(7)** image copying, full PDF text, and formal citation export are separate capabilities; **(8)** copy output preserves provenance by default and offers plainly labeled raw alternatives.

**Recommended solution.** Implement the ten-action **Copy…** overlay inside Bob Refs, bound locally to **Ctrl+Y**, with stable letter keys, a selected-reference header, real value previews, and the existing 1.5-second footer confirmation. Reuse the current copy actions through one checked pasteboard service. Add `reference_id` to bob's JSON and fetch complete `ref show` details for material actions. Provide a source-linked annotation chooser whose visible digits copy complete excerpts, whose focused quote/comment/link alternatives are explicit, and whose search obeys normal text editing. Freeze the target during every operation, keep snapshot provenance visible, and verify compilation, routing, clipboard failures, accessibility, and appearance on macOS. This gives Bryan fast copying now while keeping the feature understandable as the library and export formats grow.
