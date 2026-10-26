**Reference code copying: preserve the source, extend the Copy card**

Independent research by **cdx**, 26 October 2026. This report was developed without consulting the other researchers' reports, conversations, or findings. It is design research, not an implementation or a measured Mac usability test.

**Recommendation.** Build this feature. Preserve the Markdown that produced each new reference PDF, collect a source-backed code catalog during creation, and add **C · Code blocks** beside the existing **H · Highlights** picker in Bob Refs. In Highlights, **⌘Y** should open the ordinary Copy card for the exact current PDF; **C**, then a digit or Return, copies a block. Copy plain code by default; holding Option offers a fenced Markdown version. Do not extract PDF text as a silent fallback.

This is a worthwhile improvement because it connects the material being read to the next action: pasting an example into an editor, a terminal, a conversation, or a note. The value comes from trustworthy text and fast targeting. A clever PDF extractor that occasionally changes indentation would undermine that value. The hard part is managing the source's lifecycle and identifying the correct document, not drawing a copy button.

**What the current implementation already provides.** I inspected bob-cli at `66f9d67f6573048b76a1d34274a95e7fc4b438c2`, bob-mac-capture at `13115362fa18bc539901734c807120d23b69ece5`, and the chezmoi checkout at `027a28b96fb8067ae081796f5e1a75894f2f099d`. These identify the observations below; implementation should recheck the current revisions.

| Finding | Consequence | Repository evidence |
|---|---|---|
| The Copy card freezes the selected reference, loads notes asynchronously, and rejects responses for another card token. | Reuse this machinery for a separate code-loading state. | Mac `Sources/BobMacCapture/Refs/RefsPanelModel.swift:2227` and `:2816` |
| H opens a window of up to nine highlights. Digits copy immediately; arrows and Ctrl-N/P/J/K navigate; Escape returns one level. | A sibling C picker is learnable without introducing another top-level mode. | Mac `Sources/RefsCore/RefsHighlightPicker.swift`; `Sources/RefsCore/RefsCopy.swift:885`, `:1218`; `docs/refs.md:426` |
| Option swaps a row's displayed payload; successful pasteboard writes dismiss Refs and show a HUD. Failed writes preserve the card and retry payload. | Reuse both the alternate-payload convention and copy completion. | Mac `RefsCopy.swift:100`; `RefsPanelModel.swift:2871`; `BobPanelCoordinator.swift:101` |
| Native Highlights takeover keys already exist for opening Refs and Tabs, including configurable bundle identity. | Extend the Mac app's existing hotkey integration. A new Hammerspoon script is unnecessary. | Mac `HighlightsTakeover.swift`; `HotKeyRegistry.swift`; `AppDelegate.swift:637` |
| The bounded Accessibility reader obtains the selected tab's `AXDocument`, main-window flag, and a page number parsed from the window title. | Current-document targeting is feasible; page-aware copying would need an additional code-to-page map. | Mac `Refs/AXHighlightsTabsReader.swift:454` |
| Tab matching tries resolved paths, then filenames. | The new copy launch must be stricter than browsing: a filename-only match is insufficient to silently target code. | Mac `Sources/RefsCore/RefsHighlightsTabs.swift:295` |
| Markdown creation retains source text in its in-memory plan, but renders by reopening the original path. The inspected install path publishes PDF/audio rather than a persistent Markdown source companion. | Preserve one immutable input snapshot and render/index that same snapshot, eliminating an input-change race. | CLI `src/native/highlights_ref/create.rs:3330`, `:4710`, `:4846`, `:5249` |
| Vault-note snapshots distinguish original source from projected Markdown. Projection can omit content and expand transclusions. | Copy blocks from the reading snapshot, not from today's live note or all of the original note. | CLI `note_snapshot/plan.rs:43`; `create.rs:2679`; `note_snapshot/profile.rs` |
| Intake and rename enumerate supported companions explicitly. | A new source bundle will not move automatically merely because it has a matching stem. | CLI `doctor.rs:1094`; `intake.rs:671`; `rename/plan.rs:1641` |
| Overwrite already has staged publication, recovery, and scoped commit handling. | Extend that transaction to source bundles rather than add a second independent write path. | CLI `overwrite/execute.rs:1`, `:108`; `overwrite/recovery.rs` |

The UI screenshot in Mac `docs/images/refs-browse-dark.png` and `RefsCopyCardView.swift` support retaining the existing quiet, rounded panel, reference identity tile, muted metadata, and restrained selection color. A code editor bolted onto a new floating window would create unnecessary visual and interaction cost.

**Why PDF extraction should not supply the copy payload.** PDF text represents positioned glyphs rather than the original code's whitespace structure. The pypdf maintainers explicitly discuss ambiguities involving whitespace, line breaks, ligatures, and reading order. This supports avoiding extraction as an exact-code contract; it does not mean every PDF extractor always fails. [pypdf text-extraction documentation](https://pypdf.readthedocs.io/en/stable/user/extract-text.html#why-text-extraction-is-hard)

I ran two small local probes, using Pandoc **3.1.11.1**, XeLaTeX, and `pdftotext`. They used synthetic input, temporary files inside the workspace, and no live vault changes. The PDF probe reproduced relevant renderer settings—XeLaTeX, Tango highlighting, DejaVu Sans Mono, and the current `fvextra` wrapping declaration—but did not invoke the entire `bob ref create` pipeline or Highlights. It establishes a concrete failure mode, not a benchmark of all PDFs.

| Probe | Observed result | Design implication |
|---|---|---|
| Fenced Makefile with a tab before `printf` → ordinary Pandoc JSON | The tab became four spaces. | Even collecting ordinary Pandoc `CodeBlock.text` is insufficient unless reader options preserve tabs. |
| Same input with `--preserve-tabs` | The tab survived. | Preserve tabs explicitly in the collection path and cover Makefiles in tests. |
| Fenced block nested under a list | Markdown container indentation was removed; program indentation remained. | A semantic code block is the correct copy unit, not an arbitrary raw line slice. |
| CRLF input and a fenced block's closing delimiter | Pandoc normalized line endings and omitted the delimiter-separating final newline. An intentional extra blank line survived. | Define clipboard normalization precisely; do not advertise byte-for-byte copying of the entire Markdown source. |
| An unclosed fence with the current `markdown` reader | No CodeBlock was emitted. | Support the rendering dialect's actual blocks, not a separately assumed CommonMark interpretation. |
| Makefile and long Python line → PDF → `pdftotext`, default and `-layout` | Neither result preserved the tab, the uninterrupted long line, or trailing spaces. Default output lost indentation; layout output introduced wrap artifacts. | Layout-aware extraction does not restore the source reliably enough for this feature. |

Pandoc documents its default tab expansion and provides `--preserve-tabs`. It also supports code-block attributes and multiple fence syntaxes, which is another reason to use the renderer's reader rather than a triple-backtick regex. [Pandoc reader options](https://pandoc.org/MANUAL.html#reader-options), [fenced code attributes](https://pandoc.org/MANUAL.html#extension-fenced_code_attributes)

A minimal reproduction of the first probe is:

```python
import json, subprocess
md = '```make\nall:\n\tprintf "hello"\n```\n'
for extra in ([], ['--preserve-tabs']):
    result = subprocess.run(
        ['pandoc', '-f', 'markdown', '-t', 'json', *extra],
        input=md.encode(), capture_output=True, check=True)
    print(json.loads(result.stdout)['blocks'][0]['c'][1].__repr__())
# Default: 'all:\n    printf "hello"'
# Preserve: 'all:\n\tprintf "hello"'
```

**Source storage is a first-class part of the feature.** Keep the original source even if code extraction later improves. It supports recovery, inspection, future export, and avoiding host-local source paths. However, retaining Markdown alone does not guarantee a reproducible PDF: linked images, fonts, renderer versions, and transcluded notes are separate dependencies. This feature should promise retained text, not a complete archival build environment.

Never put the source at `<stem>.md` next to `<stem>.pdf`. Highlights explicitly owns that Markdown/TextBundle sidecar and overwrites it on saves. Bob also discovers that name as annotation input. The collision could destroy the source and import its contents as annotations. [Highlights sidecar documentation](https://highlightsapp.net/how-to/mac/sidecar-files/)

My proposed layout is a Bob-owned sibling directory:

```text
lib/chat/example.pdf
lib/chat/example.md                 # Highlights annotation export, if present
lib/chat/example.source/
    original.md                    # Exact captured source bytes
    render.md                      # Only when projected input differs
    manifest.json                  # Version, digests, generation, code catalog
```

For ordinary external Markdown, the manifest points to `original.md` as the render input; avoid duplicating identical text. For a projected vault-note snapshot, preserve original and projected text and index the projected input. A manifest holds capture time, source kind, reader/options/version, source digests, a generation token, and ordered code entries. Text files in `lib/` are companion assets, not new reference notes; explicitly ensure that note discovery excludes them. Do not add vault-note frontmatter to preserved source bytes.

Each code entry needs an opaque occurrence ID, document ordinal, heading breadcrumb, optional language, line count, exact defined copy text, and a content digest. An ID such as `generation/c0004` is sufficient: stability within one captured reading matters; stability across edits is unnecessary. Two identical snippets remain distinct occurrences. Avoid using the mutable reference marker ID as their identity: current rename policy re-keys that ID to the new stem.

Collect code through a Bob-owned Pandoc pass using the same reader dialect and explicit tab preservation, before visual filters replace or decorate blocks. Pandoc Lua exposes `CodeBlock.text` and attributes, and applies filters in command-line order. Bob already has a precedent in `diagrams_collect.lua`. The new collection pass should additionally walk headings and nested blocks in document order. [Pandoc Lua filters](https://pandoc.org/lua-filters.html#codeblock)

There are two reasonable implementation techniques: collect and render from a shared parsed AST, or run two reader passes over the same frozen bytes with deliberately documented options. Prefer a shared AST if integrating it is modest; otherwise the frozen-byte two-pass approach avoids a large renderer refactor. In either case, preserve tab semantics for collection and explicitly test visual tab width in the PDF. Stage resources so relative image paths still resolve. Do not copy a file and then render a later reread of its mutable original.

Collection includes fenced and indented blocks recognized by that route, with and without language labels, inside lists and blockquotes. It includes shell sessions, JSON, configuration, and plain text, without guessing whether they are executable. Inline code spans are outside the first version. Mermaid blocks should remain available as **Diagram source · Mermaid**, collected before the existing diagram substitution, since recovering their source is useful; distinguish them from code visibly printed in the PDF. Empty blocks need no copy target, while whitespace-only content must not be silently trimmed into emptiness. Raw HTML/TeX that is not a CodeBlock is outside the initial contract.

The clipboard contract should say: **copy the captured block's text, with Markdown fences/container syntax removed, Unicode and meaningful whitespace preserved, and line endings normalized to LF**. Preserve tabs, spaces, blank lines, and trailing spaces represented in the block. Do not unescape code as prose, normalize Unicode, remove shell prompts, add citations, or append an extra newline. The original file remains byte-preserved separately. This avoids both a false byte-exact claim and accidental formatting changes in pasted programs.

Source preservation must participate in each existing lifecycle operation:

| Operation | Required behavior |
|---|---|
| New create | Stage source, catalog, and PDF together; publish a validated set. A source/catalog write failure must not be reported as a fully successful source-backed capture. |
| Queued intake | Keep the bundle beside the queued PDF in `xlib/`; move it through the same locked, collision-checked, recoverable ingest path. `xlib/` is not vault-synced, so this is still a local queue. |
| Filed reference | Commit source companions alongside PDF/note in the existing scoped ingest commit so another host can copy offline after sync. |
| Explicit external output | Retain a sibling bundle at the chosen output path. Refs availability still requires a managed reference; external output alone does not create one. |
| Rename | Move the `.source/` directory with the PDF, update locators, and retain generation/code IDs. Extend target collision checks and rollback. |
| Reread | Give the new reading its own source generation; never repoint the old reading to new source text. |
| Overwrite | Replace PDF and source generation in the same overwrite transaction; roll back both on failure. Preserve the prior source with overwrite recovery/history as appropriate. An overwrite from an unsupported input must retire the old code catalog rather than leave stale code attached to the replacement PDF. |
| Annotation save or sync | Preserve source generation and catalog. Ordinary annotation changes must not make code unavailable. |
| Deletion or recovery | Apply existing bundle policy consistently, including source companions; add diagnostics for missing, conflicting, or corrupt bundles. |

A plain full-PDF hash is unsuitable as the live source-validity test: Highlights annotations and Bob marker changes alter PDF bytes. Bind the source generation to a managed PDF marker field and reference metadata, and preserve it through sync and rename. Validate manifest digests independently. A source-generation mismatch must disable source code copying until repaired. Prove this binding survives real Highlights save/export and existing marker rewrites before relying on it; that preservation is a proposed requirement, not a verified property of a new field. Cache validation against file changes, and treat incomplete cross-host sync as temporarily unavailable rather than guessing. A PDF hash at creation can be retained for provenance, but should not reject every later annotated PDF.

**The interaction should feel like an extension of Copy.** The reference identity stays visible throughout. Add a fixed **C · Code blocks · 12** row near H, with an understated code symbol. Loading C should not block copying a title, link, or existing highlight. Once loading settles, hide an inapplicable row in the same way the current card hides unavailable options; pressing C directly still explains why it is unavailable. Announce a positive code count to assistive technology, rather than making discoverability depend entirely on a hidden keyboard shortcut.

Entering C opens a child picker with the same numbered-window and navigation conventions as H. Do not skip the picker when only one block exists: a preview is worthwhile, and the same gesture should behave consistently. Keep the root card's existing default selection and repeated-⌘Y behavior. In particular, adding code must not silently change what `⌘Y`, then Return copies for experienced users.

A compact layout, preserving the current card's typography and materials, could look like this:

```text
COPY › CODE BLOCKS  12
Reliable worker queues

[ /  Filter code or headings… ]

Retry policy
  1   Python · 9 lines       def retry(operation):
  2   YAML · 6 lines         retry:
Worker setup
▸ 3   Shell · 4 lines        python -m worker

Shell · Worker setup                          4 lines
┌────────────────────────────────────────────────────┐
│ python -m worker \\                                 │
│   --concurrency 4 \\                                │
│   --queue critical                                 │
│                                                    │
└────────────────────────────────────────────────────┘
↵ Copy code   ⌥ Copy fenced Markdown   / Filter   esc Back
```

This is an interaction wireframe, not a rendered visual specification. Use the existing card header, keycaps, selection treatment, and reference tile. The preview should use a legible system monospace font and a subtly differentiated surface. It can scroll horizontally for long lines; do not visually wrap code into ambiguous new source lines by default. Display line numbers only as UI decoration and exclude them from every payload. Keep a fixed preview region so moving selection does not repeatedly resize the card. On smaller screens reduce the visible row count and preview height before shrinking type. Reuse the existing panel bounds and measured-height system rather than expand the entire app around code.

Syntax coloring is optional polish, not a launch dependency. A small, restrained palette may help; source text and clipboard payload must stay independent from highlighting. Unknown languages remain clean monospace. Respect light/dark appearance, increased contrast, reduced motion, and VoiceOver. Announce heading, language, ordinal, and line count; do not automatically speak hundreds of code lines on every arrow movement.

| Gesture in the code picker | Result |
|---|---|
| Up/Down, Ctrl-N/P/J/K | Select and preview, using the existing picker navigation behavior. |
| 1–9 | Copy the block in that visible numbered position, matching H. |
| Return or ⌘Y | Copy selected block. |
| Hold Option | Preview and label the fenced Markdown alternative; Option-Return, Option-digit, or Option-click copies it. |
| Click a numbered row | Copy, matching current picker rows; hover can preview without changing the frozen copy target unexpectedly. |
| Escape | Back to Copy; another Escape returns to the inspector; the panel's next Escape dismisses. |
| / | Focus a local code filter. While editing, letters/digits are text rather than copy shortcuts. Return leaves filtering and selects the result; a subsequent Return copies. Escape first leaves filter focus. |

Filter by heading, language, and code text. Retain source order within results; searching should not repeatedly reshuffle snippets as late responses arrive. Keep selection by entry ID, and make visible-window digits clearly temporary. This small filter is justified for long generated reports, although H currently has no equivalent. Do not turn all typing into search, because that would conflict with fixed-letter and digit copying.

The fenced alternative should use a fence longer than any conflicting delimiter run inside the payload and include a safe language label when known. The preview/footer must make the changed format clear while Option is held. Omit provenance from both ordinary code and fenced code; users already have the existing link-copy actions when they need a citation. Do not add “copy all code” initially: unrelated snippets, outputs, and alternate solutions are not one coherent program. Multi-block copying can be designed later if real use demonstrates the need.

On success, use the current glass HUD, e.g. **Copied Python · 9 lines**, then restore the originating context. On pasteboard failure preserve the selected ID, text, and alternate for a deliberate retry. Never report success after a failed pasteboard write or silently copy a truncated preview. No auto-paste or execution belongs in this feature.

**⌘Y in Highlights needs an explicit launch intent.** Add a native `refsHighlightsCopy` action to the existing registry/takeover system and a presentation source representing “copy the current document.” The user-visible setting should allow the takeover to be disabled. Verify the actual Highlights menu/shortcut interaction on the Mac; the research did not establish whether every installed Highlights version leaves ⌘Y unbound.

Capture the foreground process identity and current-document request before showing Refs. Obtain a fresh bounded Accessibility snapshot, resolve the selected document in the main/focused window by canonical file path, and select its exact reference. `bob ref show` resolution already recognizes `source_pdf` paths; use that authority or an equivalently strict existing library lookup. Do not silently fall back to the last selected reference, the first visible result, a window title, or an unrelated file with the same basename. The existing browsing matcher permits a filename fallback; this launch flow must explicitly bypass it or require the user to select an ambiguous candidate.

Stash ordinary Refs search, scope, selection, and scroll position, as the Highlights Tabs presentation already does. Open the exact document even when the previous library filter would hide it. Present a brief loading card if resolution is pending, and enter Copy only after the target is established. No clipboard write occurs merely because the shortcut was pressed. Deactivation, Escape, a newer launch request, or a tab switch while resolving cancels that request; stale callbacks must not open another document's card. Once Copy is open, keep its target frozen until it closes.

The takeover must yield while Refs is visible because Refs is a nonactivating panel and Highlights can remain frontmost. Otherwise the global ⌘Y would intercept the card's existing “copy selection” shortcut. Follow the established visible-panel yielding pattern. Also avoid launching over a Highlights modal save/permission sheet; present a small actionable explanation rather than misidentify the document behind it.

If Accessibility is unavailable, reuse the app's permission affordance, with normal manual Refs browsing still available. If the PDF is outside the library or ambiguous, show the filename and a clear resolution state; never auto-import it. If it is managed but has no saved source, the ordinary Copy card still works. C explains **“Original Markdown was not saved for this reference.”** Missing synchronized files should instead say **“Saved source is not available on this Mac yet.”** A corrupt or mismatched catalog is a third state, **“Saved source needs repair.”** These distinctions make the feature understandable without exposing manifest internals.

**Current-page targeting is desirable, but should not block the first version.** The existing reader's page number is a useful hint, not a code mapping. A heading's source line, snippet ordinal, PDF text search, or document percentage cannot reliably determine where a wrapped, multipage block appears. Ship heading breadcrumbs, first-line previews, and filtering first.

As a subsequent enhancement, assign named destinations or layout anchors to collected blocks during rendering and derive physical PDF page ranges after final pagination. Support blocks spanning pages. Bind that map to the same source/render generation. Then initially select the block whose range contains the current page, without filtering away other blocks or changing their document order. If several blocks share the page, select the first and retain explicit choice. If page information is absent or unverified, use normal document order. Display `p. N` only when the map is verified; distinguish physical pages from printed labels. Bob's return-link machinery offers related label infrastructure, but it does not establish that a ready-made block-page map already exists.

**Backend boundary and compatibility.** Bob should own extraction, source resolution, identity validation, and the copy payload. Swift should own presentation, key routing, and pasteboard writes. This follows the accepted thin-client decision and avoids competing Markdown parsers.

I recommend a focused read-only endpoint, provisionally **`bob ref code REF -f json`**, rather than appending potentially large source code to every library row or annotation response. `ref` is the existing noun group for reference membership. Follow the project's help, completion, and public-option alias rules when finalizing the command. The command name and sample below are proposals, not existing interfaces.

```json
{
  "schema_version": 1,
  "reference": "ref/chat/example.md",
  "generation": "opaque-capture-token",
  "status": "available",
  "blocks": [
    {
      "id": "opaque-capture-token/c0001",
      "ordinal": 1,
      "heading_path": ["Build", "Makefile"],
      "language": "make",
      "line_count": 2,
      "text": "all:\n\tprintf \"hello\"",
      "markdown": "```make\nall:\n\tprintf \"hello\"\n```",
      "page_range": null
    }
  ]
}
```

Explicit states should distinguish available, empty, unsupported input, source missing, and invalid source; an older installed Bob lacking the endpoint becomes an app compatibility state with an update hint. Existing Copy rows continue working. Large inputs need documented response limits or paginated catalog/selected-block retrieval; never truncate a payload while claiming it is complete. Start with a bounded complete response for ordinary documents, using evidence from actual report sizes to choose limits. A later lazy-payload optimization must request the generation and block ID together so a recapture cannot substitute a different block under an old selection.

The CLI can read the saved catalog without requiring Pandoc on the copying Mac. Rebuilds use the captured input and compatible parser settings, explicitly, rather than quietly substituting a newly parsed catalog on a user's keypress. Resolve companions within the expected bundle, reject traversal/symlink escapes, and do not treat embedded source text or paths as instructions. These are ordinary data-integrity constraints, not a reason to add extra user confirmations to copying.

**Adjustments to the requested scope.** These changes are intentional:

- Make preservation of the captured Markdown mandatory for newly supported captures, instead of an optional convenience or pointer to the original host's file.
- Define eligibility by verified captured source, not by reference type such as `chat` or `papers`. Begin with direct Markdown creation, including the plain Markdown route; enable projected-note captures once the projected-input fixtures pass. Web captures with a trustworthy intermediate source can join later without a new UX.
- Exclude automatic PDF/OCR/AI reconstruction from ordinary code copying. An approximate extraction feature, if ever desired, deserves its own name and explicit review.
- Keep Highlights ⌘Y as entry to the full Copy card, exactly as requested, rather than make its behavior change depending on whether the PDF contains code. C is the discoverable next step.
- Defer page mapping, inline-code targeting, and multi-block aggregation. Include a local code filter because it directly addresses targeting in long references.
- Do not silently backfill old references from same-named Markdown files or today's live source. An old reference needs an explicit, provenance-checked source attachment, or a fresh reread. Prefer reread for annotated material; do not regenerate old PDFs merely to enable this feature.

The retention change means source comments and frontmatter that were invisible in the PDF will also be retained and synced. That is consistent with preserving the original file, but should be stated in creation documentation. It is not grounds for prompting on every normal create. Full dependency/asset archival is a separate requirement.

**Delivery and acceptance.** Implement in cohesive increments, each leaving a coherent contract:

1. Source bundle and code catalog for the direct Markdown route, including frozen-input rendering, lifecycle moves, overwrite recovery, generation binding, and JSON endpoint. Test source mutation during rendering and all cleanup paths.
2. Mac C picker, Option alternative, filtering, older-Bob behavior, cancellation, exact payload writes, and existing Copy-card regressions.
3. Native Highlights ⌘Y launch intent with exact-document resolution, saved-view restoration, modal/permission handling, and takeover yielding. These are part of the first complete feature, not optional polish.
4. Enable projected-note sources after original/projected/transcluded-code fixtures prove the correct reading content is indexed. Add verified page targeting separately if targeting tests show it materially reduces effort.

The core correctness fixtures should include Makefile tabs, leading/trailing spaces, blank lines, CRLF, Unicode, long lines, no-language blocks, indented/list/quote blocks, longer backtick and tilde fences, repeated identical snippets, empty blocks, malformed fences, and Mermaid replacement. Verify fenced alternatives with code containing backticks. Test a source edited or deleted after capture, two reads of the same source, rename with ID re-keying, interrupted intake, overwrite rollback, source replacement by a non-Markdown route, and a Highlights annotation save that changes PDF bytes while code remains available.

Mac integration tests must cover two PDFs sharing a basename, multiple windows/tabs, stale callbacks, a filtered-out current reference, unavailable Accessibility, a modal dialog, repeated hotkeys, delayed source reads, huge blocks, pasteboard failure, Option release before retry, and returning to a preserved Capture draft. No code should be copied from a stale cached reference after a failed current-document lookup. Test both keyboard-only use and a first-time mouse user who discovers C from the card.

A useful manual acceptance task is: open a multi-example Markdown-generated PDF in Highlights, find and copy a known Makefile block with ⌘Y → C, paste into an editor, and compare the resulting text—including its tab—to the catalog payload. Repeat after annotation, rename, cross-host sync, and overwrite. Compare pixels separately for light/dark, increased contrast, small-screen layout, long titles, and loading/empty/error states. Swift changes require `just portable-check` and compilation of the macOS targets; on a non-Xcode host follow the linked repository's scratch-Mac build/typecheck workflow and CI test gate. No Swift was changed or compiled for this research.

Aspirational latency targets are a visible response to ⌘Y within roughly 100 ms and a usable warmed code picker within roughly 300 ms. These are design targets, not measured results. Keep the existing bounded Accessibility read and process timeouts, render a loading state promptly, and measure cold/warm behavior on the Mac before assigning performance acceptance thresholds.

**Evidence limits.** I inspected the three checkouts, read the relevant accepted architecture/identity/ingest/PDF-write memories through audited SASE reads, reviewed official Pandoc/pypdf/Highlights documentation, and ran the local parsing/PDF probes above. I did not inspect Bryan's live reference corpus, run a real Highlights shortcut test, measure Mac latency, validate a new marker field's preservation, or consult any peer researcher. The remaining implementation spikes are generation-token survival through Highlights and marker sync, exact current-window resolution under modal/focus changes, and code-preview sizing on the actual Mac. None requires guessing at missing source text.

**Recommended solution.** Proceed with a source-preserving code catalog and a **C · Code blocks** child of the existing Copy card. Make **Highlights ⌘Y** resolve the exact active PDF and open that card without changing normal Copy defaults. Copy defined source text by default, offer fenced Markdown through Option, and preserve the existing successful-copy HUD and focus behavior. Put lifecycle correctness and trustworthy whitespace ahead of page-location cleverness; add verified page awareness only after the dependable source-backed flow is working.
