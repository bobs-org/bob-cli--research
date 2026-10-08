# Bob References: a native, keyboard-first doorway into Highlights

Independent research by **cdx**, 2026-10-08. Scope: implementation choices, interaction design, ranking, metadata, and reliability. No other report or researcher findings from this swarm were consulted. This is research and a proposed design; no product code or vault files were changed.

## Decision in brief

Build the native picker. Bob already has the valuable part: reference identity and reading metadata. A custom panel can present that material much better than an ordinary file dialog while keeping Highlights as the reader.

My recommended packaging adjustment is to **ship a separate References feature inside the existing Bob Mac Capture menu-bar app first**, with its own hotkey, controller, model, and process lanes. The user-facing panel is named **Bob References**. This avoids another installation, login item, menu-bar icon, and independent update path. Keep the feature modular enough to become `bob-mac-refs` later if independent deployment proves useful. This is a change to the suggested standalone-app requirement, not a claim that the standalone idea is bad.

The core experience is: hotkey → type a few recognizable words → see the reference's type and enough context to recognize it → Return opens the original PDF in Highlights. Initial ordering helps resume recent work; typed queries prioritize textual relevance. The picker stays responsive even when metadata or preview work fails.

## What the current system provides

### Bob has a semantic reference library, not just a PDF directory

The reference pipeline maps `lib/<kind>/<stem>.pdf` to `ref/<kind>/<stem>.md`, preserving deeper subdirectories. The first library-relative directory supplies `ref_type`; a PDF directly under `lib/` has no derived type. Paths are configurable through Bob's existing vault and Highlights configuration, so `~/bob/lib/` is a default, not a path to hard-code. [Local evidence: `docs/highlights-ref-sync.md`, “Default Paths” and “Required Parent, Type, and Ref Type”; `src/native/highlights_ref/io.rs`.]

Existing `bob ref list` and `bob ref show` are read-only and emit schema-versioned JSON. The list row already exposes:

- Title, reference type, origin, note path, parent, author, publication/capture/addition dates.
- Effective reading state and its evidence, plus pending/conflicting status synchronization.
- Source URLs, DOI/arXiv identity, `source_pdf`, companion audio.
- Annotation and comment counts, scan snapshot timestamp, diagnostics, and supersession information.

The index reads notes, not PDFs. It is therefore **not an exhaustive inventory of openable local PDFs**. It can contain legacy references with no PDF, and a PDF can exist without a note. `source_pdf` is extracted metadata, not an existence check. Annotation counts describe the last imported snapshot, not current unsaved or unscanned edits in Highlights. [Local evidence: `docs/ref.md`; `src/native/ref_library/{mod,row,show}.rs`.]

Important current defaults: `bob ref list` selects queued/started references when no filter is supplied, caps at 50, and sorts by reading state before dates. `-A` lifts the cap but does not alone change the default state selection. A complete prototype metadata fetch must explicitly use:

```sh
bob ref list -R all -A -f json
```

Do not quietly inherit the reading queue or treat that list's order as picker relevance. `bob ref find` is a duplicate/identity lookup: its candidate matching uses title-token Dice similarity and retains at most five candidates. It is unsuitable as the primary search-as-you-type endpoint, particularly for partial tokens. [Local evidence: `docs/ref.md`; `src/native/ref_library/{list,resolve}.rs`.]

I checked the installed `bob` against the repository's synthetic `tests/fixtures/ref_library/vault`, not the live vault. An explicit all-state/all-row query returned schema 1, 32 rows, and `truncated: false`; only 5 rows had a non-null `source_pdf`. This demonstrates the note/PDF distinction in fixtures; it is not a statement about Bryan's actual library. One Linux invocation took approximately 10 ms. This is neither a Mac latency measurement nor evidence for performance on a large library.

The current public row has a scalar optional `author`. It does **not** expose tags, an abstract, page count, file size, or a PDF availability field. Rich display of these requires added optional catalog fields or separate lazy document inspection; do not pretend they already exist.

### The Mac app supplies a strong starting point, with specific limits

Bob Mac Capture already uses a resident accessory app, a prewarmed nonactivating `NSPanel`, SwiftUI presentation, direct `Process` calls to Bob, a vault watcher, settings, launch at login, signing/install scripts, and signposts. Its current deployment floor is macOS 26. Reuse that floor initially; do not require a newer OS merely for visual styling. [Local evidence: linked `bob-mac-capture` `README.md`, `Package.swift`, `AppDelegate.swift`, `CapturePanelController.swift`.]

The accepted thin-client decision keeps capture semantics in Bob and presentation in Swift. Its literal scope is capture; applying the same boundary to references is my design recommendation, not an already accepted reference-specific policy. Bob should decide membership, metadata, status, PDF association, and diagnostics. Swift should own local opening, previews, keyboard/focus behavior, cache orchestration, and retrieval ranking.

Do not create a second current `HotKeyManager` instance unmodified. It installs an application-wide hotkey event handler and invokes its callback without extracting the pressed `EventHotKeyID`; registration also uses a fixed ID. Two instances are not a proven dispatcher for two different actions. Add one registry that routes distinct event IDs to Capture or References, with tests for that routing. This is an integration prerequisite identified by code inspection, not a reproduced production defect. [Local evidence: `Sources/BobMacCapture/HotKeyManager.swift`.]

### Highlights can remain the reader

Highlights' current FAQ says it is not scriptable. Its vendor changelog also documents a `highlights://` file/page URL scheme, originally introduced in 2015. These facts can coexist: a URL handler is not a general scripting API. Prefer standard macOS document opening for ordinary launches; reserve the older URL scheme for an optional, separately tested page-link action. [Highlights FAQ](https://highlightsapp.net/faq/), [Highlights changelog](https://highlightsapp.net/changelog/).

Apple documents asynchronous opening of file URLs in a specifically selected application, with a completion result. That lets the picker request Highlights explicitly without changing the system PDF default. [NSWorkspace document-opening API](https://developer.apple.com/documentation/appkit/nsworkspace/open%28_%3Awithapplicationat%3Aconfiguration%3Acompletionhandler%3A%29?changes=_7).

Highlights also recently advertised Siri-assisted PDF discovery. Treat this as a cheap alternative worth trying on the installed Mac, not a verified replacement for a deterministic Bob-aware selector: the announcement does not demonstrate Bob reading-state metadata, custom ranking, or this keyboard interaction. [Vendor announcement, September 14, 2026](https://highlightsapp.net/blog/2026/09/14/Siri-AI/).

## Critique and alternatives

The plan addresses a real workflow mismatch: a general open dialog organizes files, whereas Bryan needs to retrieve references by meaning. The strongest justification for native work is the combination of **Bob metadata, predictable ranking, and an always-ready keyboard surface**. Merely moving a filename list into Swift would provide much less value.

| Approach | What it buys | Main cost or limitation | Judgment |
| --- | --- | --- | --- |
| Finder/Spotlight plus Highlights as the default reader | Immediate, no custom app | Generic file scope and little Bob context; association changes apply beyond this workflow | Useful baseline |
| Alfred scoped PDF workflow | Folder/type scope, hotkey, explicit Highlights opening | Rich Bob data needs a script adapter; custom split-pane presentation and ranking remain constrained | Best low-effort option if Alfred is already in use |
| Raycast Bob extension | Searchable list, details, actions, custom filtering | Dependency on a launcher; exact visual/focus behavior belongs partly to Raycast | Serious substitute if Raycast is already preferred |
| References panel in the existing native Bob host | Full design control with shared installation and resident infrastructure | Multi-hotkey routing and panel arbitration must be added cleanly | Recommended first delivery |
| Standalone `bob-mac-refs` | Clean feature identity and independent releases | Second install/login item; duplicated infrastructure or a new shared package | Sound later choice if separation has practical value |
| DEVONthink/Zotero/another reference manager | Broad library organization | Migration and another system of record for a narrow retrieval problem | Disproportionate to this request |

Alfred explicitly supports folder/type-specific File Filters, a hotkey-to-file-open template, and selecting the app used by its Open File action. This can solve a large portion of the raw selection problem quickly. [Alfred scoped search](https://www.alfredapp.com/help/workflows/getting-started/simple-folder-search/), [Alfred Open File action](https://www.alfredapp.com/help/workflows/actions/open-file/).

Raycast's List API provides search, selection, loading state, and a details area; its opening action accepts an application. A Bob adapter would be a viable richer alternative, not merely a shell-script workaround. There is no evidence in the inspected material that Bryan already uses either launcher, so I would not add that dependency solely for this feature. [Raycast List API](https://developers.raycast.com/api-reference/user-interface/list), [Raycast actions](https://developers.raycast.com/api-reference/user-interface/actions).

### Explicit requirement adjustments

1. **Replace “new resident app” with “dedicated References feature in the current native host” initially.** Preserve standalone extraction as an architectural option, without undertaking a generic shared-app framework now.
2. **Replace “as much data as possible everywhere” with progressive disclosure.** Dense rows should support scanning; the selected reference gets the richer detail pane. Optional data must not delay opening or dominate the screen.
3. **Use all locally available library PDFs as the default retrieval scope, regardless of reading state.** Finished and dropped materials remain useful for lookup. Reading-queue browsing is an explicit filter.
4. **Inventory PDFs as well as notes.** Unindexed PDFs remain selectable with honest fallback metadata. Notes with missing PDFs appear in an availability view, rather than polluting the default openable list.
5. **Treat opening as retrieval, not a reading-state gesture.** Opening a PDF does not mark it Started, clear review state, or mutate its task.
6. **Defer full-PDF content search, automatic summaries, page-resume tracking, favorites, and recommendation logic.** Start with reliable metadata retrieval, recent-open history, and a selected-document preview. Add richer search only after actual retrieval failures justify it.
7. **Allow a configurable global shortcut instead of assuming an in-app Control-O binding.** Recommend Control-Shift-Command-R as an initial candidate, subject to a real conflict check; never steal an occupied binding.

## The panel: recognizable, calm, fast

### Layout

Use a stable split panel around **900 × 590 points** on a normal display, bounded by the screen's visible frame and comfortable margins. Approximately 55% is the results list, 45% the detail pane. On a narrow display, collapse details behind an explicit Details control rather than crushing title readability. Remember a user resize. Keep height stable while typing; changing result counts or preview completion should not bounce the panel around.

Illustrative content below is invented, not a live library record:

```text
┌────────────────────────────────────────────────────────────────────────────┐
│  ⌕  Search references…                                  All types ▾        │
│  Library · 1,240 PDFs                  Available · All reading states       │
├──────────────────────────────────────┬─────────────────────────────────────┤
│ RECENTLY OPENED                      │ PAPER              In progress       │
│ ▸ Coordination without a coordinator│                                     │
│   Paper · J. Rivera · 2025            │ Coordination without a coordinator  │
│   Opened yesterday                   │ J. Rivera · 2025 · example.org       │
│                                      │                                     │
│   Notes on local-first retrieval     │ [ first-page preview ]               │
│   Chat · Agent report                │ 18 pages · 2.4 MB                    │
│   Opened 3 days ago                  │                                     │
│                                      │ Your context                         │
│ CONTINUE READING                     │ Research systems                     │
│   Designing durable indexes          │ 9 annotations · 3 comments           │
│   Article · A. Chen                  │ Snapshot from 2 days ago             │
│                                      │                                     │
│ NEW IN LIBRARY                       │ Added Sep 19 · Opened yesterday       │
│   …                                  │ Open PDF in Highlights   ↵           │
├──────────────────────────────────────┴─────────────────────────────────────┤
│  ↑↓ Select     ↵ Open in Highlights     ⌘↵ Open note     Esc Clear / Close   │
└────────────────────────────────────────────────────────────────────────────┘
```

Do not show invented counts when real metadata is absent. Keep the full selected title readable through wrapping even when its list row must truncate. Loading the preview should preserve the detail pane's reserved geometry.

### Result rows

Use roughly 58–68-point two-line rows, with 7–9 visible rows plus lightweight section headers. Each row has:

- A small, consistent SF Symbol and a **text type label**: Paper, Article, Chat, Book, Other. Preserve an unfamiliar raw category in details rather than silently calling it an Article. Top-level PDFs say Unclassified.
- The human title as the strongest text. Highlight matched ranges with restrained emphasis.
- A secondary line with author or source, and an appropriate date when known.
- One compact reading-state cue. Show the section-relevant date as a short trailing cue only when space allows.

Use type and origin separately: a Chat can say “Agent report” in details. The present Bob index derives `agent-report` origin from the `chat` path/type; it is not proof that every conversation there is a generated report. Do not infer an LLM vendor from a filename suffix, and do not call an ordinary conversation an AI report without explicit evidence.

Avoid thumbnail carpets: a consistent type glyph is usually more recognizable at row size than a miniature PDF page. The large preview belongs to the selection.

### Selected-reference detail

Present available information in this order:

1. Full title, type, reading state, author, publication date, and source domain.
2. First-page preview, page count, and file size; all loaded lazily.
3. “Your context”: parent/collection, available tags, short existing note/abstract excerpt, annotation/comment counts, last scan date.
4. Added/captured/finished dates with correct labels, and “Opened from Bob References” history.
5. Companion audio availability, with an explicit Listen action when the local file is readable; never autoplay.
6. Expandable technical details: PDF path, note path, DOI/arXiv identifier, source URLs, provenance and diagnostics.

Absence stays absence. Publication date is not file modification time. A scan snapshot is not reading progress. A nonzero highlight count is not a percentage read. Do not add a completion bar or estimated reading time without a defined and useful source of truth.

Make the default preview a read-only first-page image, not a second annotation editor. A details action may expand it, but PDF navigation and editing remain in Highlights. Apple provides a PDFKit page-thumbnail API suitable for this recognition cue. [PDFKit thumbnail API](https://developer.apple.com/documentation/pdfkit/pdfpage/thumbnail%28of%3Afor%3A%29?changes=_1_8).

Expose secondary actions through a visible Actions button and Command-K: Open reference note, Reveal PDF in Finder, Open source, Copy link, Refresh. Only offer actions with the required data. Show a short exact explanation for a disabled action, such as “No reference note yet.” Copying is discoverable through Actions; Command-C in the search field continues to copy selected search text.

### Keyboard and focus contract

| Input | Behavior |
| --- | --- |
| Global shortcut | Show and focus search on the current display; repeat while visible closes it |
| Printable text | Edit search without moving focus to a row |
| Down/Up, Control-N/P | Move selection while search remains the typing destination |
| Control-J/K | Optional aliases consistent with existing picker behavior, active only in this panel |
| Page Down/Up | Move by a viewport |
| Command-Down/Up | Last/first result; do not override native Control-A/E field editing |
| Return | Open selected available PDF in Highlights |
| Command-Return | Open the matching Obsidian reference note, when one exists |
| Command-K | Open Actions |
| Escape | Dismiss Actions first; otherwise clear a nonempty query; otherwise close |
| Tab/Shift-Tab | Normal focus traversal, including filters and Actions |
| Mouse | Single click selects, double click opens; hover never changes keyboard selection |

Navigation clamps at the ends; no unexpected wrap from the bottom to the top. Return during IME composition belongs to the text system, not opening. Preserve ordinary selection, paste, undo, and field shortcuts.

Start a fresh invocation with a blank query. A canceled search may be retained briefly for an explicit “Resume search” action, but old filters should not invisibly narrow the next invocation. Show all active filters as removable chips and provide Clear filters.

On cancellation, restore the previous app naturally; do not make the helper the main active application merely to receive typing. On opening, transfer activation to Highlights only after dispatching the selected document. Only one Bob auxiliary panel is visible at once; invoking References while Capture is open must preserve its unsent draft. Use separate async work lanes so a reference refresh cannot cancel a capture submission.

### Visual direction

Use system text colors, a clean SF typography hierarchy, semantic selection highlighting, a quiet divider, and one accent. Type differences rely on text and symbols as well as color. Place subtle material in the frame/search chrome; keep the content surface calm and legible. Avoid a glass effect on every row, large gradients, or decorative status colors that compete with titles.

Apple's current guidance places Liquid Glass in controls/navigation and calls for restraint and accessibility-aware materials. Use native components where they help and standard content backgrounds where they improve scanning. [Apple materials guidance](https://developer.apple.com/design/human-interface-guidelines/materials).

Support dark/light appearance, Increase Contrast, Reduce Transparency, Reduce Motion, scalable text, and VoiceOver. Selection changes should announce title/type/state without rereading the whole detail pane. Announce result counts after a short pause, not on every keystroke. Showing and filtering must work with animation disabled.

## Ordering: browsing and retrieval need different rules

### Blank query: resume, continue, discover

Default scope is all available PDFs, with no hidden reading-state or type filter. Use a small, deduplicated sequence of sections:

1. **Recently opened:** at most six successful opens from this panel within 30 days, newest first. Do not reconstruct this from PDF modification dates or pretend it is Highlights-wide history.
2. **Continue reading:** remaining references whose Bob reading state is Started, followed by queued references with effective status Next. Order each group by panel open time when available, then real added/captured date descending, then title. This section uses explicit Bob evidence, not inferred attention.
3. **New in library:** at most five remaining items with known addition/capture dates within 14 days, newest first. Undated files do not get fabricated “new” dates.
4. **All other references:** the remaining available PDFs in stable, localized title order, with PDF-relative path as the final deterministic tie-breaker.

The six/five caps and 30/14-day windows are initial design parameters to trial, not research-established optimal numbers. Deduplicate by PDF identity across sections. A recent finished paper can legitimately outrank an unread backlog item. “All other” must remain scrollable/searchable; it is not a hidden backend cap.

At first use, omit the empty recent section. Continue/New still give useful entry points; if those are empty, show the alphabetical library. Offer explicit views for Reading queue, Recent, and Title through one View control. Type and availability filters are separate. Do not reorder everything by filesystem mtime: annotation edits, sync, conversion, and metadata work can all change it without indicating a retrieval preference.

Do not sync local open history into reference notes or use it as task state. A bounded local record keyed by vault identity and logical PDF path is sufficient. Let the user clear it from Settings. Update history only after the open API accepts the request; previewing or selecting a row does not count. UI copy should say “Opened from Bob References,” reflecting the limited observation.

### Typed query: explainable relevance

As soon as meaningful text is present, flatten the browse sections into **one ranked result list**. Keeping Recent ahead of a perfect title match defeats search. Reading state should not be a search boost; an exact match to a dropped reference is still an exact match.

For version one, search human titles, filename stems, author, source domain, DOI/arXiv identifiers and precomputed URL aliases, types, and available tags. Do not search the full PDF or every imported quotation by default. Long bodies generate noisy hits and create substantial indexing work. A later explicit “Search text” mode can return page/snippet matches if users regularly remember passages rather than titles.

Normalize case, diacritics, punctuation, whitespace, and filename underscores/hyphens consistently. Keep original text/range mappings for highlighting. Require every free-text token to find evidence somewhere in the supported fields; type and state chips apply additional AND filters. Values selected inside a type filter are ORed. Avoid a bespoke operator language in the first release.

Recommended lexicographic match tiers, best first:

| Tier | Definition | Reason |
| --- | --- | --- |
| 0 | Exact canonical identifier/URL alias, full normalized title, or filename stem | Strong explicit intent |
| 1 | All tokens match complete title/stem words or their prefixes | Handles ordinary incomplete typing with high precision |
| 2 | All tokens are covered by literal substring/prefix evidence across title, author, tags, source, or type | Supports mixed queries such as `rivera coordination` or `paper retrieval` |
| 3 | All tokens have an admissible fuzzy match in those metadata fields | Recovers abbreviated/noncontiguous typing |

Within a tier, prefer title evidence over filename, then author/tags, then domain/type; prefer contiguous runs and word-boundary starts, and penalize gaps. Use a deterministic tuple of match-quality metrics rather than adding an unbounded recency weight to an arbitrary fuzzy score. Panel open recency breaks ties only after comparable textual quality; normalized title and PDF path finish the tie-break.

Short-query policy: one character uses prefixes only; two characters allow literal matches but no broad subsequence matching. Fuzzy matching starts with tokens of at least three characters. A short token in a multi-token query still needs literal/prefix evidence. Treat quoted phrases as ordinary text initially, or implement phrase semantics once in the frontend search module with explicit tests; do not quietly add multiple competing search parsers.

This first fuzzy pass handles subsequences, not every misspelling. Transposition/edit-distance tolerance is a measured follow-up if failed-query examples justify it. Do not claim that a fuzzy algorithm already handles all typos. Match highlights and a small reason such as “Author match” help explain results without exposing numeric scores.

Examples that should pass the ranking evaluation:

- `coord` finds a title word beginning Coordination before a recent unrelated reference.
- `rivera coordination` can combine author and title evidence.
- A pasted DOI selects its exact reference before fuzzy title matches.
- A perfect title match from a finished or dropped reference outranks an approximate queued match.
- `chat retrieval` can use type plus title; choosing the Chat chip gives an unambiguous type restriction.
- Empty or whitespace-only input returns browse ordering, not an arbitrary fuzzy order.

On each query edit, select the new highest-ranked result. Once the user navigates, keep that selected ID stable until the next query edit. Detail hydration must never change ranks. Background refreshes preserve the selected ID and should defer disruptive section/rank changes while the user is navigating. If an item disappears, show its unavailable state rather than opening whatever moved into the old row index. Zero results means no selection and a disabled Open action.

## Architecture and data contracts

### Add an explicit PDF catalog to Bob

For a disposable visual prototype, fetch `bob ref list -R all -A -f json` and join it with a directory inventory. For production, recommend a new **read-only `bob ref catalog`** command that performs this join in Bob and returns a versioned picker-oriented envelope. This is a proposed endpoint, not an existing command.

Reuse the existing Highlights configuration, PDF traversal, reference index, status derivation, and source-PDF parsing. The present PDF walker recognizes case-insensitive PDF extensions, skips `.git`, and does not follow symlink entries. Preserve that behavior initially and document it; do not accidentally introduce recursion loops or a second unrelated discovery policy. Improvements to exclusions belong in the shared Bob layer. [Local evidence: `src/native/highlights_ref/{model,doctor,io}.rs`.]

The catalog should enumerate library PDFs first and associate note metadata through normalized `source_pdf` paths. The canonical metadata-bearing note wins when there are superseded note companions. Several notes pointing to one PDF are one selectable PDF with explicit companion-note metadata; conflicting authoritative associations deserve a diagnostic. Same title or DOI does not by itself justify dropping two distinct PDF files: editions and annotated copies can differ.

Each PDF entry should include:

```json
{
  "id": "vault-key:lib/papers/coordination.pdf",
  "pdf_relative_path": "lib/papers/coordination.pdf",
  "pdf_absolute_path": "/Users/example/bob/lib/papers/coordination.pdf",
  "availability": "available",
  "note_paths": ["ref/papers/coordination.md"],
  "metadata_source": "reference_note",
  "title": "Coordination without a coordinator",
  "ref_type": "papers",
  "reading_state": "started",
  "author": "J. Rivera",
  "annotation_count": 9,
  "comment_count": 3,
  "snapshot_at": "2026-10-06T10:00:00",
  "diagnostics": []
}
```

Illustrative schema only: real row types should reuse the current metadata model, support null/absent fields, and clearly define their timestamp formats. Include existing identity keys, dates and provenance, optional tags/excerpts, roots, coverage counts, generation time, and `truncated`/pagination information in the envelope. Opening requires the locally resolved PDF URL; identity is not a guessed Highlights URL. Resolve vault identity from the app's configured vault, not the machine-specific absolute prefix.

An unindexed PDF remains a catalog entry: library-folder type, humanized filename fallback, no invented reading state, and `metadata_source: filename`. PDF title/author metadata may later enrich it lazily, with explicit provenance. An orphan note with no available library PDF belongs in a separate Unavailable view with “Open note” as its useful action. A note with no PDF should not appear as an enabled Highlights action.

Do not fabricate `lib/<note-stem>.pdf` solely to satisfy a note association. The pipeline's conventional mapping can suggest an exact association only after checking the corresponding file and handling ambiguity. Configured external library roots and absolute `source_pdf` values require the same shared resolver.

The catalog never runs `scan`, intake hooks, downloads, vault sync, or PDF marker parsing/write-back as a side effect of opening the panel. PDF membership and lightweight file facts can be obtained without opening every PDF. Existing note-derived state remains authoritative. No new public command may replace current `list` or `find` behavior; follow the CLI rules for excellent help, alphabetical options/subcommands, and short aliases for public long flags.

### Keep the Swift feature small and independent

A `ReferenceCore` module can hold Codable contract models, normalized search documents, ranking, and local history/cache logic. A `ReferencesPanelModel` and `ReferencesPanelController` own presentation. Reuse or lightly generalize process transport, executable resolution, settings, panel hosting, signposts, installation, and FSEvents plumbing; do not attach references to capture grammar or clone the large capture view model.

No resident server, embedded database service, Rust/Swift FFI, Spotlight metadata dependency, or network service is justified initially. Load a compact catalog in memory and search it locally. Rebuilding the library per keystroke would squander the small-process advantage and complicate ordering races. SQLite/FTS becomes interesting only if measured catalog size or explicit content search requires it.

Launch should load a versioned last-good cache and start a background catalog refresh. Prewarm the panel before the hotkey. Root/path/schema changes invalidate inappropriate cache entries. Apply a refreshed catalog atomically after complete decoding; malformed output does not erase the last-good list. Unknown optional fields are ignored; an unsupported major schema gives a clear upgrade diagnostic.

Watch both configured note and library roots. Debounce filesystem bursts and rebuild off the main thread; a note snapshot write and a PDF rename may arrive in separate events. Revalidate on wake and manual Refresh, and use an age-based refresh as a fallback when watching fails. Apple documents event coalescing and situations requiring recursive rescan, so filesystem events should invalidate a snapshot rather than be treated as a perfect transaction log. [FSEvents programming guide](https://developer.apple.com/library/archive/documentation/Darwin/Conceptual/FSEvents_ProgGuide/UsingtheFSEventsFramework/UsingtheFSEventsFramework.html).

Cache thumbnails by file identity/path plus size and modification time, not title. Annotation changes can replace a PDF in place, so a content digest or inode alone is not a stable logical reference identity. Logical library-relative path works initially; preserve history across a known rename only with trustworthy rename/association evidence. Otherwise start fresh rather than misattaching a history record. Do not hash all PDF bytes during every launch.

Load preview/page count only for the settled selection, after roughly 100–150 ms without navigation. Use bounded off-main-thread work and cancellation/generation checks. Serialize access to any reused PDFDocument; do not assume PDFKit objects can be mutated or shared concurrently without constraints. A bad preview must never block Return. A later Quick Look helper can provide more process isolation if problematic PDFs justify it.

The existing personal app's signed/hardened local installation model is a practical starting point. App Sandbox/App Store distribution would need a separate design for vault authorization, bookmarks, and subprocess access; don't claim dropping sandbox entitlements into the current CLI architecture automatically solves those constraints.

### Open the original PDF explicitly in Highlights

Resolve the installed Highlights application through Launch Services/bundle identity, with a Settings override to a chosen `.app` if necessary. Verify the actual bundle identifier on the target Mac; it was not inspected on this Linux host. Apple exposes application resolution by bundle identifier and handles multiple installation candidates through system heuristics. [Application-resolution API](https://developer.apple.com/documentation/appkit/nsworkspace/urlforapplication%28withbundleidentifier%3A%29?changes=_5).

At Return, capture the selected logical ID and its PDF URL, revalidate that the file is still present/readable, and request:

```swift
NSWorkspace.shared.open(
    [pdfURL],
    withApplicationAt: highlightsApplicationURL,
    configuration: configuration,
    completionHandler: completion
)
```

Use `URL(fileURLWithPath:)` for files and the concrete application URL. Do not concatenate shell commands from titles or paths. A manual smoke test can use `/usr/bin/open -a Highlights /absolute/path/to/file.pdf` with argv separation; production should use AppKit directly.

Keep selection/query visible with an Opening state until dispatch succeeds; prevent repeated Return from issuing duplicates. The completion callback may arrive on a concurrent queue, so UI changes return to the main actor. On reported failure, retain the panel and show Retry, Locate Highlights, or Open note as appropriate. On accepted dispatch, update local open history and dismiss. **Acceptance does not prove Highlights rendered the intended page**, so the app should not advertise stronger verification. [Apple opening completion contract](https://developer.apple.com/documentation/appkit/nsworkspace/open%28_%3Awithapplicationat%3Aconfiguration%3Acompletionhandler%3A%29?changes=_7).

Open the library original, not a temp/exported copy: Highlights annotations must stay on the PDF that Bob's scan reads. Preview is read-only. Never silently fall back to Preview, redownload a file, write a PDF marker, or claim that dispatch changed reading state.

## Reliability states and validation

| Situation | Product behavior |
| --- | --- |
| No local PDFs | Honest empty library state and path setting; not “nothing to read” |
| No search matches | Show active filters and Clear filters; no enabled Open action |
| Catalog refresh fails | Keep last-good results, show a quiet stale-data banner and Retry |
| A PDF exists without a note | Selectable fallback row; disable Open note with explanation |
| Note exists but PDF is absent | Unavailable view; offer Open note; explain local availability |
| PDF replaced/moved during selection | Revalidate captured ID/URL; preserve the error context; never open another row by index |
| Conflicting reading metadata | Explicit unknown/conflict cue, with detail; still open an available PDF |
| PDF encrypted/corrupt or preview fails | Placeholder with reason; opening stays independent when the file is available |
| Highlights missing | Locate app/settings action and retained query |
| Hotkey conflict | Settings diagnostic and menu action remain usable |
| Vault sync/watcher burst | Debounced refresh; stable selection; no user-facing duplicate storm |
| Capture is submitting | Preserve its operation and draft; references work has separate lanes |

Use the current vault sync architecture. `xlib/` is an out-of-band intake queue and not part of the default library scope. A new capture on another machine may be waiting for Mac transfer and scan; the picker should not label this “library loss” or initiate those workflows. A future Intake view can expose locally present PDFs explicitly, but it should be separately scoped because intake files can move. [Local evidence: `docs/vault-git-sync.md`, “Highlights bridge.”]

Before investing in polish, validate three real user tasks: reopen yesterday's reference, find one by partial remembered title/author, and retrieve a finished old reference. Compare the full sequence from hotkey to opening against the current dialog and, if already installed, a scoped launcher workflow. Search ranking should be evaluated against a small fixed set of real query/desired-reference pairs, including collisions and unsuccessful queries; do not tune only to the illustrative examples above.

Suggested acceptance targets, **not measured results**:

- Warm hotkey to focused, populated panel: p95 under 100 ms.
- Query edit to ranked results: p95 under 50 ms with 10,000 metadata entries.
- Opening dispatch does not await a thumbnail, Git date backfill, network, or vault scan.
- First launch remains interactive during catalog work; a cached launch displays usable data immediately.
- Entire primary workflow works with keyboard and VoiceOver, with no focus theft on Escape.

Tests should cover catalog PDF/note reconciliation, relative/absolute/custom roots, case variants, duplicates, unindexed files, invalid metadata, exclusions/symlinks, and partial filesystem changes. Ranking fixtures should cover short prefixes, mixed fields, exact identifiers, finished/dropped matches, stable tie-breaks, and zero results. Mac integration checks should cover distinct hotkeys, IME composition, fast typing at panel opening, stale asynchronous results, Spaces/full-screen/multiple displays, missing Highlights, already-open PDFs, spaces/Unicode/#/% in paths, and repeated Return. Verify actual Highlights behavior for cold launch and already-open files; the documented API alone cannot establish those details.

Do not require a huge automated test campaign for this research deliverable. These are implementation acceptance checks for the proposed behavior; only the existing fixture command and source/document review were performed during this research.

## Delivery sequence and remaining uncertainty

1. **Prove document dispatch and focus on the real Mac.** Minimal panel plus one original PDF; test cold/running Highlights and cancellation. This addresses the biggest platform unknown before data/design expansion.
2. **Build the read-only catalog and deterministic search module.** Expose all PDFs and honest metadata. Validate retrieval queries against fixtures and a bounded real-library sample.
3. **Ship the useful panel.** Global shortcut, title/type/state rows, recent/continue/new browsing, relevance search, keyboard actions, errors, cache, and background refresh. This already solves the stated problem.
4. **Add visual recognition and selected detail.** Lazy first page, page count, bounded context excerpt, snapshot labels, accessible typography, and adaptive layout. Trial the row density and section caps with Bryan.
5. **Observe missed retrievals before expanding scope.** Full-text search, pins, annotations-as-search, page links, or standalone packaging need a concrete user benefit rather than speculative completeness.

This is a suggested delivery order, not a SASE implementation plan or a request to create task beads. No tasks were filed, no Mac package was built, and no live vault was modified.

Remaining uncertainties: actual Mac library size and metadata completeness; preferred installed launcher; installed OS/Highlights version and bundle identifier; cold/duplicate-document behavior; which title/type queries Bryan actually uses; desirability of a separate installed app. None prevents a reasonable design recommendation, but Mac integration and ranking trial should precede implementation claims.

## Evidence record

External sources were checked on 2026-10-08 and linked adjacent to the claims they support. Vendor capabilities are documented capabilities, not local runtime verification. Design parameters, ranking tiers, and performance targets are this report's recommendations.

Local source revisions inspected:

- `bob-cli`: `b0f2960d4210b2abd9627895aa8c585fcf1c81ea`; `docs/ref.md`, `docs/highlights-ref-sync.md`, `docs/vault-git-sync.md`; `src/native/ref_library/{mod,row,list,resolve,show}.rs`; `src/native/highlights_ref/{doctor,io}.rs`.
- Linked `bob-mac-capture`: `838e043f44b7ac8257b962578b7424e4c1e09092`; `README.md`, `Package.swift`; `Sources/BobMacCapture/{AppDelegate,CapturePanelController,HotKeyManager,VaultTargetWatcher}.swift`; `Sources/CaptureCore/BobProcessClient.swift`.
- Audited memory reads: `obsidian.md`, `cli_rules.md`, `sase_artifacts.md`, `glossary:ref-note`, `decisions:mac-capture-is-a-thin-client`.
- Read-only runtime check: installed Bob's all-state JSON list against `tests/fixtures/ref_library/vault`, with schema 1 and 32 returned fixture rows. No peer report, chat transcript, or indirect peer finding was used.

## Recommended solution

Implement **Bob References as a dedicated native panel in the existing Bob Mac Capture host**, backed by a new read-only Bob PDF catalog and local deterministic metadata search. Give it a configurable global shortcut, clear type labels, concise results, a rich but lazy selected-reference pane, and explicit opening of the original PDF in Highlights. Blank input favors recent opens and continuing work; typed input favors textual relevance, with recency only as a tie-breaker. Keep PDF availability, annotation freshness, and reading state honest, and preserve capture operations when switching panels.

That is a worthwhile custom feature because Bob already owns the reference context. Reuse the host first, validate dispatch/focus on the Mac, and keep standalone `bob-mac-refs` packaging available if independent use later makes it preferable.
