# Quick-Opening Reference PDFs in Highlights: Architecture and Design for `bob-mac-refs`

- **Date:** 2026-10-08
- **Author:** researcher gem (`research.44.gem`)
- **Status:** Complete Proposal & System Specification
- **Repo Targets:** `bobs-org/bob-cli`, `bobs-org/bob-mac-capture` (or new sibling `bobs-org/bob-mac-refs`)
- **Target File:** `sase/repos/research/202610/bob_mac_refs_highlights_launcher__gem.md`

**Recommendation in one line:** Build a native macOS floating HUD (`bob-mac-refs` or unified `bob-mac`) that queries `bob-cli`'s reference index over JSON, caches entries in-memory with FSEvents invalidation, presents a two-pane master-detail interface featuring live `PDFKit` cover thumbnails and lifecycle-tiered default sorting, and dispatches directly to Highlights via `NSWorkspace`.

---

## 0. Executive Summary

Bryan uses the **Highlights** app on macOS to read all reference materials (academic papers, AI chat transcripts, web articles, e-books, and research reports). While Highlights renders and annotates PDFs effectively, finding and opening specific references is plagued by severe friction: Highlights' `<Ctrl+O>` shortcut summons the standard macOS `NSOpenPanel` file dialog. This file dialog is semantically blind: it forces manual folder traversal through `~/bob/lib/`, exposes only sanitized file stems (e.g. `2403.12345v1.pdf`), lacks reading lifecycle awareness, hides author and topic metadata, and provides no fuzzy search across titles or annotations.

This report evaluates Bryan's proposal to create a new Swift HUD application (`bob-mac-refs`), inspired by `bob-mac-capture`, to provide instant, global, keyboard-driven access to reference PDFs.

### Key Conclusions:
1. **The proposal is fundamentally sound and high-leverage**, addressing a daily productivity bottleneck in Bryan's knowledge loop.
2. **Crucial Architectural Adjustment:** Do **not** scan `~/bob/lib/` directly from Swift. Per established architectural decision `decisions:mac-capture-is-a-thin-client`, `bob-cli` must remain the sole authority for metadata parsing, reading-state derivation, and identity mapping. The Swift app must be a pure presentation and orchestration thin client querying `bob-cli` via JSON.
3. **Packaging Strategy:** While a standalone `bob-mac-refs` app is viable, **unifying Capture and Refs under a single `bob-mac` desktop suite** (or extracting shared infrastructure into a `BobMacCore` Swift package) eliminates massive boilerplate duplication across Carbon hotkeys, launch-at-login, menu bar items, code signing, and IPC.
4. **Sorting Dual-Engine:**
   - **Default View (Zero-Query):** Sorted strictly by **Reading Lifecycle Tiers** (`In Progress` $\to$ `Next Up` $\to$ `Queued` $\to$ `Recently Read` $\to$ `Archive`), keeping Bryan's active reading context front and center.
   - **Filtered View (Query Active):** Sorted by a **Hybrid Relevance Score** where title/author/identifier match quality dominates, modulated by gentle state and recency boosts so active readings break ties over archival records.
5. **UI Aesthetics & Visual Cognition:** Implement a two-column floating HUD featuring an embedded, asynchronous **`PDFKit` page-1 visual thumbnail**, distinct color-coded semantic pills for reference types (`papers`, `chat`, `articles`, `books`), and multi-action keyboard triggers (`↵` to Highlights, `⌘↵` to Obsidian note, `⌥↵` to Finder, `Space` for Quick Look).

---

## 1. Problem Analysis: The Friction in Today's Workflow

### 1.1 Highlights App on macOS
Highlights is a purpose-built PDF reader optimized for research workflows. When opening documents:
- macOS invokes `open -a Highlights <path>` or `NSWorkspace.shared.open([url], withApplicationAt: highlightsAppURL)`.
- Highlights automatically restores document scroll position, active page, and annotations based on macOS extended attributes and internal state.
- Highlights provides no internal library browser, workspace manager, or quick-switcher. Its native document open command `<Ctrl+O>` / `<Cmd+O>` opens standard macOS AppKit `NSOpenPanel`.

### 1.2 The Root Causes of NSOpenPanel Failure
1. **Filesystem vs. Knowledge Disconnect:** Reference PDFs in Bob live under partitioned subdirectories:
   - `~/bob/lib/papers/`
   - `~/bob/lib/chat/`
   - `~/bob/lib/blogs/` (or `articles/`)
   - `~/bob/lib/books/`
   - `~/bob/xlib/` (pending intake)
   Navigating nested directories in `NSOpenPanel` requires repetitive mouse clicks or clumsy path entry.
2. **Opaque File Stems:** File names on disk are frequently machine slugs or sanitized identifiers:
   - `2310.06825.pdf` (Mistral 7B paper)
   - `2026-09-12-anthropic-sonnet-update.pdf`
   - `research_swarm_listen_card.pdf`
   Searching for "Albert Jiang" or "Mistral Architecture" in Finder/NSOpenPanel fails because author and descriptive metadata reside in the Obsidian frontmatter (`ref/...md`) or PDF metadata marker, not the filename.
3. **Lifecycle Blindness:** NSOpenPanel has zero awareness of GTD or reading states. It cannot distinguish between:
   - A paper Bryan is actively reading today (`wip` / `[/]`).
   - A paper queued for his next Pomodoro (`next` / `[*]`).
   - A paper finished six months ago (`read` / `[x]`).
   - An intake PDF waiting to be processed (`xlib`).
4. **Context Switching Costs:** To open a reference today, Bryan must either:
   - Switch to Obsidian, search via Dataview or Quick Switcher, find the `#ref` task line `- [ ] #task #ref [[lib/...pdf]]`, and click the link; or
   - Switch to terminal, run `bob ref find` or `bob ref show`, copy the path, and run `open -a Highlights ...`; or
   - Open Finder / Highlights open panel and manually hunt down the file.
   Each detour fractures cognitive focus.

---

## 2. Critique of the Proposal & Alternative Approaches

### 2.1 Critique of the Core Idea
The user's intuition is spot-on: a dedicated, system-wide hotkey triggering a fast, focused selection panel is the canonical macOS solution for high-frequency resource access (exemplified by Spotlight, Alfred, Raycast, and Bryan's own `bob-mac-capture`).

However, four alternative implementation vectors must be critically weighed against the proposed Swift app:

| Alternative | Pros | Cons | Verdict |
| :--- | :--- | :--- | :--- |
| **Option A: Raycast Extension** | • Fast TypeScript/React UI<br>• Zero Swift compilation or macOS CI requirements<br>• Built-in fuzzy search & hotkey | • Hard dependency on Raycast app & Node.js runtime<br>• Fixed UI templates (cannot embed custom `PDFKit` canvas or custom audio player)<br>• 150–250ms cold-start latency<br>• Incompatible with standalone Bob distribution | **Rejected** (Violates autonomy & aesthetic control) |
| **Option B: Obsidian Plugin / Modal** | • Native access to vault metadata<br>• Built with existing `bob-plugins` tooling | • Scoped only to Obsidian window (useless when focused in Highlights, Safari, or Terminal)<br>• Multi-step window switching required<br>• Cannot intercept system-wide hotkeys cleanly | **Rejected** (Does not solve global workflow need) |
| **Option C: Terminal CLI / TUI (`fzf`)** | • Trivial to implement (`bob ref list \| fzf`)<br>• Zero GUI code<br>• Immediate keyboard response | • Requires open terminal or iTerm hotkey drop-down<br>• No graphical rendering of PDF covers or rich typography<br>• Disconnected from macOS visual polish | **Companion Only** (Great for CLI, insufficient for primary UI) |
| **Option D: Standalone `bob-mac-refs` App** | • Total UI control<br>• Decoupled development from Capture<br>• Native macOS performance (<10ms) | • Duplicates infrastructure (Hotkeys, Process client, Settings, Menu bar, CI)<br>• Two separate background daemons running on Mac | **Acceptable** (Viable, but duplicate maintenance) |
| **Option E: Unified `bob-mac` Suite (or Shared SwiftPM Package)** | • Single desktop daemon & menu bar item<br>• Shared `BobMacCore` (`BobProcessClient`, `HotKeyManager`, `VaultTargetWatcher`)<br>• Consistent design tokens and typography<br>• Independent panels for Capture (`⌃⇧⌘I`) and Refs (`⌃⇧⌘R`) | • Requires refactoring `bob-mac-capture` into a multi-panel app or monorepo | **Recommended Best Architecture** |

### 2.2 Recommendation on Application Packaging
Rather than building an isolated, redundant second app with its own cloned `HotKeyManager.swift`, `BobProcessClient.swift`, and `AppDelegate.swift`, the recommended approach is:
1. **Short term:** Create `bob-mac-refs` as a sibling repo or target that imports a shared `BobMacCore` package (or extracts the common components from `bob-mac-capture`).
2. **Medium term:** Merge into a unified **`bob-mac`** desktop client supporting two global hotkeys:
   - `⌃⇧⌘I` $\to$ **Bob Capture Panel** (Quick GTD task / note / pomodoro capture)
   - `⌃⇧⌘R` $\to$ **Bob References Panel** (Quick reference PDF finder & inspector)

This consolidation ensures a single 30MB resident memory footprint, unified launch-at-login (`SMAppService`), and single-click update management.

---

## 3. Required Adjustments to Proposed Requirements

The user's prompt outlined initial requirements. Here are the necessary technical and architectural adjustments:

### Adjustment 1: Respect `decisions:mac-capture-is-a-thin-client`
- **Initial Proposal:** "...writing a new bob-mac-refs Swift app... that allows me to select one of the PDFs in the `~/bob/lib/` directory."
- **Why Direct `lib/` Scanning Fails:** The PDF files in `lib/` contain raw binary streams. They do **not** contain the derived reading status (`reading_state: started|queued|finished`), the GTD checkbox mark (`^ref`), author attribution, linked Obsidian notes, companion audio paths, or annotation counts. If the Swift app attempted to read `ref/*.md` frontmatter directly, it would duplicate the parsing logic, regexes, and normalization rules in `bob-cli`—violating core SASE decision `mac-capture-is-a-thin-client`.
- **Adjustment:** The Swift app must spawn `bob ref list --all -f json` (or a dedicated `bob ref picker -f json` endpoint) to receive fully normalized, validated JSON. The Swift app owns presentation, filtering, and process launch; `bob-cli` owns data and state truth.

### Adjustment 2: Surface Pending Intake PDFs (`xlib/`)
- When Bryan clips a web article or captures an arXiv link, `bob ref create` drops the PDF into `~/bob/xlib/` before the next `bob ref scan`.
- If the launcher only inspected `lib/`, recently captured references would be invisible until a manual or scheduled scan ran.
- **Adjustment:** The backend must include queued `xlib` PDFs with an explicit `[Intake]` badge. Bryan can open and read a freshly captured paper immediately without waiting for a library sync.

### Adjustment 3: Multi-Action Keyboard Dispatch
- Opening in Highlights is the primary action, but not the only one. A researcher frequently needs to open the synthesis note in Obsidian or reveal the file in Finder.
- **Adjustment:**
  - `Return` (`↵`): Open PDF in Highlights (Primary).
  - `Cmd+Return` (`⌘↵`): Open reference note in Obsidian via `obsidian://open?vault=...&file=...`.
  - `Option+Return` (`⌥↵`): Reveal PDF in macOS Finder.
  - `Cmd+C` (`⌘C`): Copy formatted Markdown reference link (`[[ref/papers/slug\|Title]]`) or citation.
  - `Space` (`␣`): Trigger macOS Quick Look preview.

### Adjustment 4: In-Memory Cache with FSEvents Invalidation
- Spawning a CLI subprocess on every hotkey press adds 20–50ms latency.
- Spawning a CLI process on every keystroke during typing is unacceptable.
- **Adjustment:** Pre-warm an in-memory array of `ReferenceItem` structs in Swift on app launch. The hotkey displays the panel in **<5ms**. File system changes in `~/bob/ref/`, `~/bob/lib/`, and `~/bob/xlib/` are observed by `VaultTargetWatcher` (using macOS `FSEventStreamCreate`) with a 300ms debounce, triggering an asynchronous background refresh.

---

## 4. Classification & Reference Type Taxonomy

References in Bob fall into distinct conceptual and physical categories under `~/bob/lib/<ref_type>/` and `~/bob/ref/<ref_type>/`. The UI must make these distinctions immediately obvious through visual iconography, color badges, and filtering tags.

### 4.1 Taxonomy Matrix

| Ref Type (`ref_type`) | Real-World Content | Visual Badge | SF Symbol Icon | Accent Color | Primary Metadata |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`papers`** | Academic papers, arXiv preprints, conference proceedings | `PAPER` | `graduationcap.fill` | Indigo (`#6366F1`) | Authors, Year, arXiv ID / DOI |
| **`chat`** | AI dialogues (Claude, Gemini, ChatGPT transcripts rendered to PDF) | `CHAT` | `bubble.left.and.bubble.right.fill` | Emerald (`#10B981`) | Model/Platform, Turn count, Date |
| **`blogs` / `articles`** | Clipped web articles, technical essays, Substack posts | `ARTICLE` | `newspaper.fill` | Amber (`#F59E0B`) | Publication domain, Author, Date |
| **`books`** | Textbooks, monograph chapters, technical manuals | `BOOK` | `book.closed.fill` | Rose (`#F43F5E`) | Author, Publisher, Year |
| **`reports`** | SASE research reports, organizational briefs, system analyses | `REPORT` | `chart.bar.doc.horizontal.fill` | Blue (`#3B82F6`) | Author agent/role, Target system |
| **`zorg` / `legacy`** | Migrated legacy references | `LEGACY` | `archivebox.fill` | Gray (`#6B7280`) | Era date, Legacy status |

### 4.2 Category Scoping Mechanics
The user can narrow the visible list using three intuitive mechanisms:
1. **Header Scope Bar:** Clickable/navigable tab pills at the top: `[All] [Papers] [Chat] [Articles] [Books] [Queue]`.
2. **Keyboard Shortcut Scoping:** `⌘1` for All, `⌘2` for Papers, `⌘3` for Chat, `⌘4` for Articles, `⌘5` for Books, `⌘0` for Active Queue.
3. **Inline Filter Syntax:** Typing `@paper`, `@chat`, `@article`, or `@book` directly in the search bar immediately filters by that category without leaving the keyboard.

---

## 5. Sorting & Ranking Strategy

The prompt requests: *"Think hard about how we should sort the PDFs that are shown by default vs when a filter has been typed in by the user."*

This distinction is fundamental to search UX: **Default view is a reading queue; filtered view is an information retrieval engine.**

```
+---------------------------------------------------------------------------------+
|                                 USER INTENT                                     |
+---------------------------------------+-----------------------------------------+
|     DEFAULT VIEW (Zero-Query)         |        FILTERED VIEW (Query Active)     |
|  "What should I be reading next?      |     "Find that specific paper/topic     |
|   What was I reading just now?"       |      I have in my mind right now."      |
+---------------------------------------+-----------------------------------------+
|  Primary Driver:                      |  Primary Driver:                        |
|  Reading Lifecycle State + Recency    |  Fuzzy Match Quality + State Boost      |
+---------------------------------------+-----------------------------------------+
```

### 5.1 Default View (Zero-Query / On Open)

When Bryan presses the hotkey without typing, the list must represent his **active reading priorities**. Alphabetical sorting here is counterproductive (it surfaces obscure files starting with numbers or symbols).

#### The 5-Tier Lifecycle Ladder:
1. **Tier 1: In Progress (`reading_state: started` / `wip` / `[/]`)**
   - *Rationale:* References Bryan has already cracked open and is currently working through.
   - *Order:* Most recently opened/touched first.
   - *Visual Section:* `▼ IN PROGRESS (N)`
2. **Tier 2: Up Next (`reading_state: queued`, `status: next` / `[*]`)**
   - *Rationale:* Items explicitly promoted to the Next lane during daily review.
   - *Order:* Date added / promoted descending.
   - *Visual Section:* `▼ NEXT UP (N)`
3. **Tier 3: Active Reading Queue (`reading_state: queued`, `status: ready` / `[ ]`)**
   - *Rationale:* The confirmed backlog of unread materials awaiting attention.
   - *Order:* Date added descending (newest captures at the top).
   - *Visual Section:* `▼ QUEUED (N)`
4. **Tier 4: Recently Finished (`reading_state: finished` / `read` / `[x]`)**
   - *Rationale:* References completed within the last 14–30 days, frequently revisited for citation or synthesis note verification.
   - *Order:* Date finished descending.
   - *Visual Section:* `▼ RECENTLY READ (N)`
5. **Tier 5: Archive & Dropped (`dropped` / `[-]`, older `finished`)**
   - *Rationale:* Historical reference vault. Collapsed or placed at the bottom so they do not crowd active tasks.

*Default Selection:* The topmost item in **Tier 1** (or Tier 2 if none in progress) is automatically highlighted, allowing Bryan to hit `HotKey` $\to$ `Return` in under half a second to instantly resume reading.

---

### 5.2 Filtered View (Query Typed by User)

When Bryan types a search query (e.g. `"vaswani"`, `"flash"`, `"attention"`, or `"1706.03762"`), the user intent pivots from browsing a queue to locating a specific target.

If sorting remained dominated by lifecycle tiers, an active paper vaguely matching a query would overshadow the exact paper Bryan searched for. Therefore, **Relevance Score must dominate**, but reading state acts as an intelligent tie-breaker.

#### Hybrid Scoring Formula
Each reference $R$ receives a composite score $S(R, Q) \in [0, 150]$ against query $Q$:

$$S(R, Q) = S_{\text{match}}(R, Q) + B_{\text{state}}(R) + B_{\text{recency}}(R)$$

#### 1. Match Quality Component ($S_{\text{match}} \in [0, 100]$):
- **Exact Match (100 pts):** Exact match on arXiv ID (`1706.03762`), DOI, note id, or exact title.
- **Title Prefix / Word-Boundary Match (85 pts):** Query matches the start of the title or starts a major title word (e.g. `"atten"` matches `"Attention Is..."`).
- **Acronym Match (80 pts):** Query matches uppercase acronym (e.g. `"RAG"` matches `"Retrieval-Augmented Generation"`).
- **Author Match (75 pts):** Query matches author surname (e.g. `"vaswani"`, `"gregg"`, `"karpathy"`).
- **Title Substring / Fuzzy Token Match (50–70 pts):** Dice coefficient / fuzzy substring matching on title tokens.
- **Topic / Parent / URL Match (40 pts):** Query matches tags, topics, parent note name, or source URL domain.

#### 2. Reading State Boost ($B_{\text{state}} \in [-10, +20]$ pts):
When multiple candidates match well, active items should float above archival ones:
- `started` (`wip`): **+20 points**
- `next`: **+15 points**
- `queued` (`ready`): **+10 points**
- `intake` (`xlib`): **+8 points**
- `finished` (`read`): **+0 points**
- `dropped` (`abandoned`): **-10 points**

#### 3. Recency Boost ($B_{\text{recency}} \in [0, +5]$ pts):
- Added, opened, or completed within last 7 days: **+5 points**
- Added within last 30 days: **+2 points**

#### Example in Action:
Bryan types `"transformer"`:
- Paper A: *"Transformer-XL"* (`finished` 2 years ago) $\to$ Match: 85 + State: 0 + Recency: 0 = **85**
- Paper B: *"A Survey on Efficient Transformers"* (`started` yesterday) $\to$ Match: 85 + State: 20 + Recency: 5 = **110**
- Paper C: *"Transformers in Vision"* (`queued` last week) $\to$ Match: 85 + State: 10 + Recency: 2 = **97**
- Result Order: **Paper B (Started) $\to$ Paper C (Queued) $\to$ Paper A (Finished)**.
- If Bryan instead types `"transformer-xl"`, Paper A scores an exact title match (100) and easily beats Paper B (60), ensuring precision is never compromised.

---

## 6. Information Architecture & User Interface Design

The interface must be **intuitive, reliable, and beautiful**—matching the clean, tactile aesthetic of macOS AppKit/SwiftUI system overlays and the existing `bob-mac-capture` application.

### 6.1 Window & Geometry Specifications
- **Window Class:** Borderless floating `NSPanel` (`styleMask: [.nonactivatingPanel, .fullSizeContentView, .titled, .resizable]`).
- **Window Level:** `.floating` (stays above Highlights and Obsidian without stealing application menu focus).
- **Material & Blur:** `NSVisualEffectView` with `.hudWindow` / `.underWindowBackground` material, dark mode vibrancy, 14pt corner radius, and subtle 1pt border (`Color.white.opacity(0.12)`).
- **Default Dimensions:** Width: **880 pt**, Height: **540 pt** (fixed height or clamped budget between 480pt and 640pt so typing never causes jarring window resizes).
- **Layout Division:**
  - **Left Master List:** 400 pt width.
  - **Divider:** 1 pt hairline separator (`Color.white.opacity(0.08)`).
  - **Right Detail Inspector:** 479 pt width.

---

### 6.2 Visual Wireframe & Layout

```
+-------------------------------------------------------------------------------------------------------------+
|  🔍  attention is all                                                                 [ 3 matches / 142 ] ✖ |
+-------------------------------------------------------------------------------------------------------------+
|  [ All (⌘1) ]  [ Papers (⌘2) ]  [ Chat (⌘3) ]  [ Articles (⌘4) ]  [ Books (⌘5) ]   | Filter: [ Queue only ] |
+--------------------------------------------------+----------------------------------------------------------+
|  LIST PANE (400 pt)                              |  INSPECTOR & PREVIEW PANE (479 pt)                       |
+--------------------------------------------------+----------------------------------------------------------+
|  ▼ IN PROGRESS                                   |  [PAPER]  [● IN PROGRESS]  [arXiv:1706.03762]            |
|  +--------------------------------------------+  |                                                          |
|  | [PAPER] ● Attention Is All You Need        |  |  Attention Is All You Need                               |
|  | Ashish Vaswani, Noam Shazeer, et al.  2017 |  |  Ashish Vaswani, Noam Shazeer, Niki Parmar, et al.       |
|  | ♫ Audio summary · 14 highlights            |  |  Published: Jun 12, 2017 · Added: Sep 15, 2026           |
|  +--------------------------------------------+  |  ------------------------------------------------------- |
|                                                  |  +-----------------------+  DOCUMENT SUMMARY             |
|  ▼ NEXT UP                                       |  |                       |  • Source: arXiv preprint     |
|  +--------------------------------------------+  |  |   [ PDF PAGE 1        |  • Vault Note:                |
|  | [PAPER] ◉ FlashAttention: Fast & Memory... |  |  |     THUMBNAIL         |    ref/papers/attention.md    |
|  | Tri Dao, Daniel Y. Fu, et al.         2022 |  |  |     RENDERED VIA      |  • Reading Status:            |
|  | 8 highlights                               |  |  |     PDFKit            |    ref_task: [/] (wip)        |
|  +--------------------------------------------+  |  |     CANVAS ]          |                               |
|                                                  |  |                       |  • Annotations:               |
|  ▼ QUEUED                                        |  |                       |    14 highlights, 3 comments  |
|  +--------------------------------------------+  |  +-----------------------+                               |
|  | [PAPER] ○ FlashAttention-2: Faster Attn... |  |  ------------------------------------------------------- |
|  | Tri Dao                               2023 |  |  ♫ COMPANION AUDIO SUMMARY AVAILABLE                     |
|  | Queued since Oct 01, 2026                  |  |  [ ▶ Play Summary (4m 12s) ]  lib/papers/attention.mp3   |
|  +--------------------------------------------+  |  ------------------------------------------------------- |
|                                                  |  RECENT HIGHLIGHT EXCERPT                                |
|  ▼ RECENTLY READ                                 |  "The dominant sequence transduction models are based    |
|  +--------------------------------------------+  |   on complex recurrent or convolutional networks..."     |
|  | [ARTICLE] ✓ The Illustrated Transformer    |  |                                                          |
|  | Jay Alammar                           2018 |  |                                                          |
+--------------------------------------------------+----------------------------------------------------------+
|  [↵] Open in Highlights   |   [⌘↵] Open Obsidian Note   |   [⌥↵] Show in Finder   |   [Space] Quick Look    |
+-------------------------------------------------------------------------------------------------------------+
```

---

### 6.3 List Item Cell Design
Each row in the master list is packed with high-signal metadata while maintaining clean visual breathing room:
- **Row Height:** 64 pt.
- **Top Line:**
  - Type Pill: e.g. `[PAPER]` (compact 10pt bold text in colored rounded pill).
  - Status Glyph: `●` Amber for Started, `◉` Cyan for Next, `○` Blue for Queued, `✓` Green for Finished.
  - Document Title: Semibold 13pt SF Pro Text. Query match characters highlighted with accent color and semibold weight (using `AttributedString`).
- **Middle Line:**
  - Primary Authors (truncated with `et al.`), followed by Publication Year or Added Date (11pt SF Pro Text, secondary gray).
- **Bottom Line:**
  - Auxiliary badges: `♫` glyph if companion audio is attached, `✎ 14` for annotation count, dim vault path.

---

### 6.4 Detail Inspector & Visual PDF Preview
The right pane turns the tool from a standard file switcher into a rich research dashboard:

1. **Native `PDFKit` Page-1 Thumbnail:**
   - Leveraging Apple's `PDFKit` (`PDFDocument(url:)?.page(at: 0)`), the inspector renders a crisp, high-resolution thumbnail of the actual PDF cover or title page.
   - *Why this is essential:* Human visual memory recognizes document formatting, two-column IEEE/ACM layouts, journal header banners, and introductory diagrams dramatically faster than reading textual titles.
   - Rendered asynchronously with an in-memory `NSCache` so list scrolling remains buttery smooth at 60 fps.
2. **Metadata Grid:**
   - Full author list.
   - Exact publication date and capture timestamp.
   - ArXiv ID, DOI, and source URL (clickable).
   - Reading state source (e.g. `ref_task:[*]` in agreement with `frontmatter:next`).
3. **Audio Companion Card:**
   - If a same-stem companion audio file exists (`lib/<type>/<stem>.mp3` or `.m4a`), display an embedded audio player pill with play/pause and duration preview.
4. **Highlights & Notes Sneak-Peek:**
   - Displays the count of synchronized Highlights and comments.
   - Shows the quote text of the most recent highlight (retrieved via `bob ref show` or snapshot metadata).
5. **Action Bar:**
   - Highlights the primary action: `Open in Highlights (↵)` styled with a prominent accent fill.
   - Secondary action pills: `Obsidian (⌘↵)`, `Finder (⌥↵)`, `Copy Link (⌘C)`.

---

## 7. System Architecture & Technical Contract

Adhering strictly to `decisions:mac-capture-is-a-thin-client`, the architecture separates data authority from presentation:

```
+-------------------------------------------------------------------------------+
|                                  macOS System                                 |
|                                                                               |
|  [ Global HotKey: ⌃⇧⌘R ] ----> [ BobMacRefs App (Swift / AppKit / SwiftUI) ]  |
|                                      |                     |                  |
|                                      v                     v                  |
|                            [ In-Memory Cache ]     [ NSWorkspace.shared ]     |
|                                      ^                     |                  |
|                                      |                     +--> Open in       |
|                            [ VaultTargetWatcher ]               Highlights.app|
|                              (FSEvents stream on                              |
|                               ~/bob/ref, lib, xlib)                           |
+--------------------------------------|----------------------------------------+
                                       |
                   Spawns on cache miss or FSEvent invalidation
                                       |
+--------------------------------------v----------------------------------------+
|                                 bob-cli Core                                  |
|                                                                               |
|       `bob ref picker --format json`  (or `bob ref list --all -f json`)       |
|                                       |                                       |
|                                       v                                       |
|    [ Ref Library Index: reads ref/*.md, ^ref tasks, lib/ PDFs, xlib/ intake ] |
+-------------------------------------------------------------------------------+
```

### 7.1 Backend CLI Endpoint (`bob-cli`)

`bob-cli` already contains the robust `ref_library` indexing module (`src/native/ref_library/`).

We will leverage or extend `bob ref list` with an additive verb or flags:
```bash
bob ref picker --format json
# or:
bob ref list --all --include-intake --format json
```

#### JSON Response Schema (Schema Version 1):
```json
{
  "ok": true,
  "schema_version": 1,
  "command": "ref picker",
  "generated_at": "2026-10-08T17:30:00",
  "vault_dir": "/Users/bryan/bob",
  "library": {
    "total": 142,
    "started": 3,
    "queued": 45,
    "finished": 82,
    "dropped": 12
  },
  "refs": [
    {
      "id": "attention_is_all_you_need",
      "title": "Attention Is All You Need",
      "author": "Ashish Vaswani, Noam Shazeer, Niki Parmar, et al.",
      "published": "2017-06-12",
      "added": "2026-09-15",
      "finished": null,
      "ref_type": "papers",
      "reading_state": "started",
      "status": "wip",
      "status_source": "ref_task:[/]",
      "pdf_path": "/Users/bryan/bob/lib/papers/attention.pdf",
      "pdf_exists": true,
      "is_intake": false,
      "note_path": "ref/papers/attention.md",
      "url": "https://arxiv.org/abs/1706.03762",
      "arxiv": "1706.03762",
      "doi": null,
      "audio_path": "/Users/bryan/bob/lib/papers/attention.mp3",
      "annotation_count": 14,
      "comment_count": 3,
      "recent_quote": "The dominant sequence transduction models are based on complex recurrent...",
      "topics": ["deep-learning", "transformers", "nlp"]
    }
  ]
}
```

### 7.2 Swift Process Client & Cache Architecture

```swift
// Swift Data Model
public struct ReferencePickerItem: Identifiable, Decodable, Sendable {
    public let id: String
    public let title: String
    public let author: String?
    public let published: String?
    public let added: String?
    public let finished: String?
    public let refType: String
    public let readingState: String  // "started", "queued", "finished", "dropped", "intake"
    public let status: String?
    public let pdfPath: String
    public let pdfExists: Bool
    public let isIntake: Bool
    public let notePath: String
    public let url: String?
    public let arxiv: String?
    public let doi: String?
    public let audioPath: String?
    public let annotationCount: Int
    public let commentCount: Int
    public let recentQuote: String?
    public let topics: [String]
}
```

#### Cache & Invalidation Lifecycle:
1. **Startup:** `BobProcessClient` spawns `bob ref picker --format json` in a background queue. On completion, deserializes `[ReferencePickerItem]` into memory.
2. **File Watching:** `VaultTargetWatcher` registers an `FSEventStream` over `~/bob/ref`, `~/bob/lib`, and `~/bob/xlib`.
3. **Debounced Refresh:** On filesystem changes, a 300ms debounce fires, refreshing the cache asynchronously without locking the UI.
4. **Hotkey Summon:** When the user hits `⌃⇧⌘R`, the UI renders immediately from the in-memory array. Latency from hotkey press to screen presentation is **< 10 milliseconds**.

---

### 7.3 Interacting with Highlights & macOS

```swift
// Dispatching to Highlights App
final class HighlightsLauncher {
    static let highlightsBundleID = "com.sophia.Highlights"
    
    static func openPDF(atPath path: String) {
        let fileURL = URL(fileURLWithPath: path)
        guard FileManager.default.fileExists(atPath: path) else {
            NSSound.beep()
            return
        }
        
        let workspace = NSWorkspace.shared
        if let appURL = workspace.urlForApplication(withBundleIdentifier: highlightsBundleID) {
            let config = NSWorkspace.OpenConfiguration()
            config.activates = true
            workspace.open([fileURL], withApplicationAt: appURL, configuration: config) { _, error in
                if let error = error {
                    NSLog("Failed to open PDF in Highlights: \(error)")
                    workspace.open(fileURL) // fallback to default handler
                }
            }
        } else {
            // Fallback if Highlights is not found by bundle ID
            workspace.open(fileURL)
        }
    }
    
    static func openObsidianNote(vaultPath: String, notePath: String) {
        // Encodes obsidian://open?vault=...&file=...
        let vaultName = URL(fileURLWithPath: vaultPath).lastPathComponent
        guard let encodedVault = vaultName.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed),
              let encodedFile = notePath.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed),
              let uri = URL(string: "obsidian://open?vault=\(encodedVault)&file=\(encodedFile)")
        else { return }
        NSWorkspace.shared.open(uri)
    }
    
    static func revealInFinder(atPath path: String) {
        let fileURL = URL(fileURLWithPath: path)
        NSWorkspace.shared.activateFileViewerSelecting([fileURL])
    }
}
```

---

## 8. Implementation Roadmap

The implementation cleanly divides into four phases:

### Phase 1: `bob-cli` Backend & JSON Contract
1. Add `bob ref picker` subcommand (or enhance `bob ref list` with `--picker` / `--include-intake`).
2. Include absolute PDF paths, intake status, and snapshot annotation teasers in the JSON output.
3. Add Rust unit tests in `tests/cli/ref_library/` verifying output structure and intake inclusion.

### Phase 2: Core Engine & Swift Library (`BobMacCore` / `RefsCore`)
1. Implement `ReferencePickerItem` Decodable models in Swift.
2. Implement in-memory fuzzy search and the hybrid scoring algorithm ($S_{\text{match}} + B_{\text{state}} + B_{\text{recency}}$).
3. Connect `VaultTargetWatcher` (FSEvents) to trigger background cache invalidations.
4. Add SwiftPM unit tests covering scoring edge cases and lifecycle ordering.

### Phase 3: SwiftUI Interface & PDFKit Rendering
1. Build `ReferencePanelView` and `ReferencePanelController` (`NSPanel`, floating,HUD vibrancy).
2. Build list cells with ref type pills, reading status chips, and typography hierarchy.
3. Build the inspector card with async `PDFKit` cover page generation and `NSCache`.
4. Implement full keyboard navigation (Arrows, `Ctrl+N`/`Ctrl+P`, `Tab`, `Return`, `Esc`).

### Phase 4: System Integration, Menu Bar & Hotkeys
1. Register global hotkey `⌃⇧⌘R` (via Carbon `RegisterEventHotKey`).
2. Wire multi-action dispatch: `Return` (Highlights), `⌘Return` (Obsidian), `⌥Return` (Finder), `Space` (Quick Look).
3. Add menu bar status item with recent references list and settings.
4. Configure launch-at-login via `SMAppService`.
5. Package and notarize using Xcode / `Scripts/bundle.sh`.

---

## 9. Failure Modes, Edge Cases, and Mitigations

| Failure Mode / Edge Case | Cause / Trigger | Technical Mitigation |
| :--- | :--- | :--- |
| **Missing Highlights.app** | Highlights not installed or installed in non-standard location | Verify bundle ID `com.sophia.Highlights`; if unresolvable, fallback gracefully to `NSWorkspace.shared.open(fileURL)` (default macOS PDF reader) with a dim notification. |
| **Missing PDF File on Disk** | Reference note exists in `ref/` but PDF was moved or deleted from `lib/` | Mark row with `[Missing PDF]` warning pill in dim red; disable `Return` action and offer `⌘Return` to open/repair the Obsidian note. |
| **Intake PDF without Note** | PDF sitting in `xlib/` before `bob ref scan` has executed | Show `[Intake]` pill; allow instant opening in Highlights; indicate that highlights sync will activate on next scan. |
| **Giant Vault Scaling (10,000+ PDFs)** | Searching and rendering large library freezes UI | Swift in-memory cache handles 10,000 structs in <2MB RAM. List uses SwiftUI `LazyVStack` or AppKit `NSTableView` with row recycling. PDF thumbnails are lazy-loaded on selection change only. |
| **Corrupted / Password-Protected PDF** | PDF cannot be rendered by `PDFKit` | `PDFDocument(url:)` fails gracefully; inspector displays clean fallback document glyph without crashing. |
| **Concurrent Vault Modification** | `bob ref scan` moves files while picker is open | `VaultTargetWatcher` debounces events; row selection gracefully re-anchors to matching `id` rather than stale index. |

---

## 10. Conclusion & Final Recommendation

Developing a dedicated reference launcher is an **outstanding architectural investment** that will eliminate daily friction in Bryan's research workflow. 

### Final Recommendations Summary:
1. **Adopt the Thin-Client Architecture:** Let `bob-cli` remain the single source of truth for library indexing, reading states, and metadata resolution.
2. **Unify the Desktop Footprint:** Build the reference launcher as a sibling panel or unified component of the `bob-mac` desktop suite to maximize code reuse with `bob-mac-capture` and maintain a single resident menu bar daemon.
3. **Implement Dual-Mode Sorting:**
   - **Default View:** Strictly tiered by GTD reading lifecycle (`In Progress` $\to$ `Next Up` $\to$ `Queued` $\to$ `Recently Read`).
   - **Filtered View:** Composite relevance scoring with state boosts.
4. **Deliver a Visually Stunning Inspector:** Pair high-density typography with an asynchronous **`PDFKit` cover page preview**, semantic category color pills, and companion audio playback.
5. **Empower Power-User Actions:** Primary `Return` opens in Highlights; secondary shortcuts provide seamless bridges to Obsidian notes, Finder, and citekey copying.
