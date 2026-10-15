# Beautiful PDF Generation for Area and Project Notes in Bob CLI: Critique, Architecture, and Implementation Blueprint

- **Date:** October 15, 2026
- **Researcher:** `research.4m.gem`
- **Scope:** `bob ref create`, Area & Project note rendering, PDF generation engine selection, GTD review workflow
- **Repository:** `bob-cli` (Workspace 15)

---

## 1. Executive Summary

This investigation evaluates how to add first-class support to `bob-cli` for creating beautiful, publication-grade PDF documents from Obsidian **Area Notes** and **Project Notes**. 

Bryan currently relies on `bob ref create` to produce PDFs from external sources (arXiv papers, web articles, captured conversations) and from local Markdown documents. These PDFs are placed into the Highlights intake pipeline (`xlib/`), moved into the library (`lib/`), and read and annotated on an iPad or MacBook using the Highlights app. Annotations later synchronize back into the Bob vault via `bob ref scan`.

Recently, Bryan applied this workflow to a living Obsidian project note—generating `~/bob/lib/chat/sase_blog_v1.pdf` from `~/bob/sase_blog.md`. An inspection of this artifact reveals severe visual and structural defects:
1. **Raw internal metadata leakage**: Dataview inline fields (`[fresh:: 2026-10-15]`, `[created:: ...]`, `[id:: ...]`, `[dependsOn:: ...]`) and block anchors (`^prj`, `^intro-proposal`) appear verbatim throughout the document.
2. **Broken Obsidian transclusions and assets**: Vault image links (`![[img/20260802_144938.png|400]]`) and note embeds (`![[ref/...#^ref]]`) fail to resolve and print as broken text strings.
3. **Degraded task representations**: Custom GTD task states (`[/]` in-progress, `[*]` next, `[?]` blocked, `[-]` cancelled) degenerate into raw ASCII brackets or awkward bullets rather than styled status badges.
4. **Table of Contents pollution**: Pandoc's `--number-sections` and `--toc` treat transient task queue groupings (`0.1.1 Next & In Progress`, `0.1.2 Blocked`, `0.1.3 Done & Canceled`) as numbered document chapters.
5. **Dated typographic presentation**: The current Pandoc + XeLaTeX toolchain formats notes like an unstyled 1990s academic paper in Latin Modern / DejaVu Serif rather than an executive dashboard or polished project brief.

### Key Strategic Recommendations

1. **Critique of the Proposal**: Expanding `bob ref create` to handle Area and Project notes is **justified and valuable for the Highlights review cycle** (reading and annotating a project note on an iPad with an Apple Pencil, with annotations syncing back to Obsidian). However, forcing all note PDF exports through `bob ref create` creates an architectural mismatch: it treats the user's canonical vault state as an external reading queue item, forces intake into `lib/chat/`, stamps a page-1 marker, and creates circular reading tasks.
   - **Recommended Adjustment**: Decouple the **Note PDF Rendering Engine** from the **Highlights Reference Intake Pipeline**. `bob ref create` should use this engine when given a vault note, automatically defaulting metadata and parentage. Simultaneously, a clean, direct command (`bob note pdf <note>` or `bob export <note>`) should be exposed for exporting and printing without Highlights pipeline side-effects.

2. **Engine Selection**: We recommend **Headless Chromium + HTML5/CSS3 Print Templates**, reusing and extending the web-clip rendering architecture already present in `bob-cli` (`scripts/web_clip/web_clip_render.py` and `scripts/web_clip/template/reader.css`).
   - *Why not XeLaTeX?* LaTeX makes flexbox-style task cards, color-coded status badges, multi-column logs, and SVG icons painfully complex, slow to compile (8–15s), and fragile across OS font configurations.
   - *Why not Typst?* Typst is fast and modern, but would introduce an unmanaged external binary dependency that is not standard across macOS and Linux, and still requires transpiling Obsidian Markdown.
   - *Why Chromium?* `bob-cli` already ships with bundled variable fonts (Inter, JetBrains Mono, Source Serif 4), Chromium launcher logic, and `@page` CSS print support. Headless Chromium handles emojis natively (🧱, ⛓️, 🗓️, 🛠️, ❌), executes in <1 second, perfectly mirrors Obsidian's Electron-based visual model, and produces standards-compliant tagged PDFs with automatic outline bookmarks.

3. **Preprocessing Pipeline**: A dedicated Rust preprocessor in `bob-cli` should parse Obsidian Markdown AST into semantic HTML:
   - Extract the `^prj` outcome line into a prominent **Project Hero Card** at the top of Page 1.
   - Scrub low-level plumbing (`[fresh::...]`, `^slug`, `#task`, `#prj`) while elevating priority and schedule fields into badges.
   - Render task lanes as clean modern cards with semantic status pills.
   - Transclude vault images (`![[img/...]]`) and block embeds directly from `~/bob/`.
   - Exclude operational task lane headings from the document Table of Contents.

---

## 2. Ground Truth Analysis: Deconstructing `sase_blog_v1.pdf`

To understand the problem concretely, we analyzed the source project note (`~/bob/sase_blog.md`) alongside the generated PDF (`~/bob/lib/chat/sase_blog_v1.pdf`) produced by `bob ref create`.

```
Obsidian Vault Note                      Current Pandoc Pipeline                 Generated PDF (sase_blog_v1.pdf)
┌─────────────────────────────┐         ┌─────────────────────────┐             ┌──────────────────────────────┐
│ Frontmatter (type: project) │         │ pandoc --standalone     │             │ 0.1 Tasks                    │
│ - [ ] #task #prj Outcome... │ ──────> │   --toc --number-sect   │ ──────────> │   0.1.1 Next & In Progress   │
│ ## Tasks                    │         │   --pdf-engine=xelatex  │             │ □ #task #prj Outcome [fresh] │
│ ### Next & In Progress      │         │   DejaVu Serif font     │             │ • [?] #task Review [depends] │
│ ![[img/screen.png|400]]     │         │ (Raw source passthrough)│             │ – ![[img/screen.png|400]]    │
└─────────────────────────────┘         └─────────────────────────┘             └──────────────────────────────┘
                                                                                  ❌ Broken images
                                                                                  ❌ Raw Dataview tags
                                                                                  ❌ Corrupted numbering
```

### 2.1 Concrete Flaws in the Rendered Output

#### 1. Leaking Internal Dataview Plumbing
In Obsidian, inline Dataview fields (`[key:: value]`) and block identifiers (`^id`) are either parsed into metadata tables or hidden by styling. In `sase_blog_v1.pdf`, they are rendered as literal text:
```text
□ #task #prj My SASE post, in my own voice, is live on https://sase.sh! [fresh:: 2026-10-15]
[created::2026-06-11] #hide [id:: sase_blog__prj] ^prj
– BLOCKS: [[sase_post_blog#^prj]]
```
This forces the reader to mentally parse internal system tags (`#hide`, `#task`, `#prj`), synchronization dates (`[fresh:: 2026-10-15]`), and database keys (`[id:: sase_blog__prj]`).

#### 2. Complete Failure of Image and Transclusion Embeds
Line 99 of `sase_blog.md` contains:
```markdown
- Some good examples of using stashed prompts! [created::2026-08-02]
  - ![[img/20260802_144938.png|400]]
  - ![[img/20260802_144945.png|400]]
```
Although `/home/bryan/bob/img/20260802_144938.png` exists on disk (702 KB), standard Pandoc does not recognize Obsidian `![[...]]` wiki-embed syntax. The generated PDF renders:
```text
– ![[img/20260802_144938.png|400]]
– ![[img/20260802_144945.png|400]]
```
The images are completely missing from the PDF.

#### 3. Breakdown of Task Status Semantics
Bob notes use extended checkbox markers for GTD task states:
- `- [ ]` = Ready / Open
- `- [*]` = Next
- `- [/]` = In Progress / WIP
- `- [?]` = Blocked
- `- [x]` = Completed
- `- [-]` = Cancelled

Pandoc's default markdown reader only recognizes `[ ]` and `[x]`. Non-standard markers are emitted as literal bullet items:
```text
• [/] #task #ref [[ref/chat/sase_launch_post_outline|...]]
• [?] #task Review [[lib/chat/...]]
• [-] #task Launch agent to create ~/bob/zk/ notes...
```
Furthermore, Pandoc converts `- [ ]` into an empty unicode box `□` and `- [x]` into `⊠`, losing the visual hierarchy of an active task board.

#### 4. Corrupted Section Numbering & Outline
Pandoc is invoked with `--toc` and `--number-sections`. Because `sase_blog.md` starts with lead metadata and an `H2` (`## Tasks`) without a preceding `H1`, Pandoc's LaTeX writer numbers the headings starting at chapter 0:
```text
0.1 Tasks
0.1.1 Next & In Progress
0.1.2 Blocked
0.1.3 Done & Canceled
0.2 Screenshots
0.3 Contents
0.4 Outline
0.5 Later Posts
```
This degrades the PDF bookmarks. When Bryan opens the document in Highlights on an iPad, the table of contents is dominated by operational task buckets rather than the intellectual content of the note (Requirements, Outline, Architecture).

#### 5. Unstructured Log Bullet Lists
Project and area notes contain structured logs for schedule rolls, cancellations, and work logs:
```text
– CANCEL LOG
  ∗ 2026-10-15 — Rolled 8 times since 08-25...
– SCHEDULE LOG
  ∗ 2026-10-12 → 2026-10-16 — P1 roll · in 4 (2–7) days
  ∗ 2026-10-10 → 2026-10-12 — P1 · in 2 (2–7) days
  ∗ 2026-10-08 → 2026-10-10 — P1 roll · in 2 (2–7) days
```
In `sase_blog_v1.pdf`, these logs consume nearly three full pages as raw bullet lists. For closed tasks with multiple schedule rolls, the history completely overwhelms the active content.

---

## 3. Critique of the Plan: Is `bob ref create` the Right Tool?

The user request proposes:
> *"I would like to add much better support to the `bob ref create` command for creating beautiful PDF files from area notes / project notes."*

### 3.1 The GTD Domain Conflict: "Reference" vs. "Vault State"

In GTD methodology and Bob's architecture:
- **Reference Material (`ref`)**: External, read-only information captured from the outside world (academic papers, articles, saved chats, books). It lives in `lib/<ref_type>/<stem>.pdf` and has an associated reading task tracked in a parent note.
- **Area / Project Notes**: Internal, mutable systems of record. They are the *containers* of work, holding active tasks, project boundaries, and logs.

When a user runs:
```bash
bob ref create ~/bob/sase_blog.md -P sase_blog
```
The command assumes the standard reference capture pipeline:
1. It renders the source into a PDF.
2. It stamps a Highlights page-1 marker (`highlights-ref-mvp-3`) containing metadata.
3. It places the PDF in intake (`xlib/chat/sase_blog_v1.pdf`) and then library (`lib/chat/sase_blog_v1.pdf`).
4. It creates a reference note (`ref/chat/sase_blog_v1.md`).
5. It inserts a reference task into `-P sase_blog`:
   ```markdown
   - [ ] #task #ref [[ref/chat/sase_blog_v1|sase_blog]] [created::2026-10-15] ^ref-sase-blog-v1
   ```

### 3.2 Where the Proposal Succeeds

**The Highlights iPad Review Cycle:**
Bryan’s primary motivation is to review and annotate complex project notes and area plans while away from his workstation (e.g., sitting with an iPad and Apple Pencil). 
- In this review workflow, the project note *is* being treated as reading material for an editing pass.
- Bryan makes highlights, writes margin notes, and sketches diagrams in Highlights app.
- When `bob ref scan` runs, those annotations sync cleanly into `ref/chat/sase_blog_v1.md`.
- In this context, stamping the page-1 marker and linking the reference back to `sase_blog.md` is not a bug—it is an elegant, closed-loop review mechanism.

### 3.3 Where the Proposal Breaks Down

If `bob ref create` is the *only* mechanism for rendering note PDFs:
1. **Circular / Awkward Parent Requirements**: The user must explicitly pass `-P sase_blog` when converting `sase_blog.md`. If omitted, `bob ref create` errors out because `-P` is mandatory. For an area note like `sase.md`, there is no parent area—the note *is* the root area.
2. **Category Misclassification**: Markdown currently defaults to `ref_type: chat` (`lib/chat/`). A project note or area note is not a chat log; placing it in `lib/chat/` pollutes the chat archive.
3. **Inability to Export Without GTD Side Effects**: If Bryan simply wants to generate a clean PDF of `sase_blog.md` to send to a collaborator, archive at a milestone, or print out, running `bob ref create` will pollute his vault with a new `^ref` task and reference note.

### 3.4 Recommended Architectural Split

We recommend a **two-tier architecture**:

```
                       ┌──────────────────────────────┐
                       │   Bob Note Renderer Engine   │
                       │   (Rust Preprocessor + CSS)  │
                       └──────────────┬───────────────┘
                                      │
                 ┌────────────────────┴────────────────────┐
                 ▼                                         ▼
   ┌───────────────────────────┐             ┌───────────────────────────┐
   │       bob note pdf        │             │      bob ref create       │
   │  (Direct Export / Print)  │             │ (Highlights Intake Flow)  │
   ├───────────────────────────┤             ├───────────────────────────┤
   │ • Standalone PDF output   │             │ • Detects vault note type │
   │ • No page-1 marker        │             │ • Injects page-1 marker   │
   │ • No vault task creation  │             │ • Routes to lib/projects/ │
   │ • Fast, clean, direct     │             │ • Auto-resolves parent    │
   └───────────────────────────┘             └───────────────────────────┘
```

1. **Core Renderer (`bob note render / export`)**: A vault-aware note rendering engine that turns any Bob Markdown note into a beautiful PDF.
2. **`bob ref create` Integration**: When `bob ref create` receives a file whose frontmatter has `type: "[[project]]"` or `type: "[[area]]"`:
   - It routes rendering through the specialized Note Renderer instead of generic Pandoc.
   - It automatically defaults the `parent` (`-P`) to the note itself (or its `parent` frontmatter).
   - It defaults `ref_type` to `projects` or `notes` instead of `chat`.
   - It stamps the page-1 marker so Highlights sync functions seamlessly.

---

## 4. Technology Selection: Evaluating PDF Rendering Engines

We evaluated four candidate rendering engines for turning preprocessed Markdown/HTML into PDF documents on Linux and macOS.

| Criterion | 1. Pandoc + XeLaTeX (Status Quo) | 2. Headless Chromium + CSS (Recommended) | 3. Typst (v0.15.1) | 4. WeasyPrint / PagedJS |
| :--- | :--- | :--- | :--- | :--- |
| **Visual Polish & Styling** | Poor. Rigid academic layout; complex macros required for cards/pills. | **Exceptional.** Full CSS flexbox, grid, rounded corners, box shadows, cards. | **Very High.** Clean modern layout, native shapes, programmatic scripting. | High. CSS Paged Media support, but engine bugs on complex CSS. |
| **Emoji & Unicode Handling** | Fragile. Requires fontspec / Noto Color Emoji; often crashes XeTeX. | **Flawless.** Native browser emoji and colored glyph rendering. | Good, but color emoji support requires specific font fallback setup. | Mediocre. Font fallback issues common on Linux. |
| **Rendering Latency** | Slow: 8–15 seconds per compile. | **Fast: 600ms – 1.2s** using headless browser. | **Instant: 100ms – 300ms**. | Slow: 3–6 seconds (Python runtime overhead). |
| **System Dependencies** | Heavy (`texlive`, `xelatex`, multiple `.sty` packages). | **Zero new deps.** Chrome/Chromium is already required for Bob web-clip. | New dependency. Binary not standard on macOS without Homebrew/Cargo. | Heavy Python C-extensions (pango, cairo, libffi). |
| **Code Reuse in `bob-cli`** | Partial (reuses `render_temp_pdf`). | **High.** Reuses `web_clip_render.py`, `reader.css`, and bundled fonts. | None. Requires writing a new Typst generator. | None. |
| **PDF Bookmarks & Metadata** | Supported via `hyperref`. | **Native.** `page.pdf(outline=True)` maps H1–H6 to PDF outline. | Native support for PDF outlines and metadata. | Supported via CSS extensions. |

### Why Headless Chromium is the Decisive Winner

1. **Parity with Obsidian**: Obsidian is built on Electron (Chromium). Its visual language—callouts (`> [!info]`), tags, checkboxes, and task cards—is authored in HTML and CSS. Using Chromium allows us to directly translate Obsidian styling into a printable stylesheet with 100% fidelity.
2. **Existing Infrastructure in `bob-cli`**:
   `bob-cli` already ships with:
   - `scripts/web_clip/web_clip_render.py`: A battle-tested headless Chromium print coordinator that sets `@page`, loads local fonts offline via a private URL scheme (`bob-clip.invalid`), and invokes `page.pdf()`.
   - Embedded variable fonts: Inter, JetBrains Mono, and Source Serif 4 are compiled into the `bob-cli` binary (`include_bytes!`).
   - Browser preflight checks in `bob ref doctor`.
3. **Emoji Support**: Bob project notes are filled with Unicode emoji (`🧱`, `⛓️`, `🗓️`, `🛠️`, `❌`, `🎲`, `⚪`, `🔵`, `🔴`, `🟢`). XeLaTeX consistently struggles with mixed-script colored emojis. Chromium renders them natively with zero configuration.

---

## 5. Domain Preprocessing: Transforming Bob Notes into Print Layouts

Raw Markdown cannot be fed directly to a print engine. A dedicated preprocessing layer must parse the note structure and output clean HTML.

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          Bob Note Preprocessing Stages                          │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│   1. Frontmatter & Hero Extraction                                              │
│      ├── Parse YAML: type, parent, status, task_count                           │
│      ├── Extract ^prj task line -> Construct Hero Banner Card                   │
│      └── Suppress ^prj line from regular task list                              │
│                                                                                 │
│   2. GTD Task Sanitation & Transformation                                       │
│      ├── Strip: [fresh::...], [created::...], [id::...], [dependsOn::...], ^id │
│      ├── Elevate: [priority:: high] -> Badge; [scheduled::...] -> Date Tag      │
│      ├── Map Checkboxes: [/] -> WIP, [*] -> NEXT, [?] -> BLOCKED, [-] -> CANCEL│
│      └── Convert Child Logs: WORK LOG, SCHEDULE LOG -> Collapsible Detail Cards │
│                                                                                 │
│   3. Vault Link & Embed Resolution                                              │
│      ├── Resolve ![[img/...|width]] -> Absolute disk path (~/bob/img/...)       │
│      ├── Resolve ![[note#^block]] -> Transclude referenced block content        │
│      └── Resolve [[note|label]] -> Formatted cross-reference link               │
│                                                                                 │
│   4. Outline & TOC Curation                                                     │
│      ├── Mark operational headings (#Tasks, ###Blocked) with .no-toc            │
│      └── Preserve content headings (#Requirements, ##Outline) in PDF Outline    │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 5.1 The Project Hero Card
In a Bob project note, the lead line is the `^prj` task:
```markdown
- [ ] #task #prj My SASE post, in my own voice, is live on https://sase.sh! [fresh:: 2026-10-15] [created::2026-06-11] #hide [id:: sase_blog__prj] ^prj
	- 🧱 **BLOCKS:** [[sase_post_blog#^prj]]
```
In the PDF, this should not appear as a stray checkbox. Instead, it should be extracted into a **Project Hero Banner** at the top of the first page:

```html
<header class="project-hero">
  <div class="project-meta-line">
    <span class="badge badge-parent">AREA: SASE</span>
    <span class="badge badge-status badge-wip">STATUS: IN PROGRESS</span>
    <span class="badge badge-counts">4 OPEN · 8 CLOSED</span>
  </div>
  <h1 class="project-title">sase_blog</h1>
  <div class="project-outcome">
    <span class="outcome-icon">🎯</span>
    <span class="outcome-text">My SASE post, in my own voice, is live on https://sase.sh!</span>
  </div>
  <div class="project-dependencies">
    <span class="dep-pill dep-blocks">🧱 Blocks: sase_post_blog</span>
  </div>
</header>
```

### 5.2 Task Cards and Status Lanes
The `## Tasks` section in Bob notes contains the status chip summary line:
```markdown
[`⚪ 3 open`](#Tasks) · [`🔵 1 next/wip`](#Tasks#Next%20&%20In%20Progress) · [`🔴 2 blocked`](#Tasks#Blocked) · [`🟢 8 done/canceled`](#Tasks#Done%20&%20Canceled)
```
In the HTML print template, this becomes a high-level KPI dashboard bar:
```html
<div class="task-summary-dashboard">
  <div class="kpi-card kpi-open"><span class="kpi-num">3</span><span class="kpi-label">Open</span></div>
  <div class="kpi-card kpi-active"><span class="kpi-num">1</span><span class="kpi-label">Active / Next</span></div>
  <div class="kpi-card kpi-blocked"><span class="kpi-num">2</span><span class="kpi-label">Blocked</span></div>
  <div class="kpi-card kpi-closed"><span class="kpi-num">8</span><span class="kpi-label">Closed</span></div>
</div>
```

Individual task lines should be rendered as distinct cards:
- **Checkbox Glyphs**:
  - `[ ]` &rarr; `<span class="task-check task-ready"></span>`
  - `[*]` &rarr; `<span class="task-check task-next">★</span>`
  - `[/]` &rarr; `<span class="task-check task-wip">◐</span>`
  - `[?]` &rarr; `<span class="task-check task-blocked">?</span>`
  - `[x]` &rarr; `<span class="task-check task-done">✓</span>`
  - `[-]` &rarr; `<span class="task-check task-cancelled">✕</span>`
- **Metadata Scrubbing**: All internal bracketed tokens (`[fresh:: ...]`, `[created:: ...]`, `[id:: ...]`, `[dependsOn:: ...]`) and block IDs (`^prj`) are removed from the visible task description.
- **Priority and Schedule**: If `[priority:: high]` or `[scheduled:: 2026-10-19]` is present, they render as compact badge pills beside the task title.

### 5.3 Formatting Audit and Schedule Logs
Sub-bullets like `WORK LOG`, `SCHEDULE LOG`, and `CANCEL LOG` should not render as standard bullet points. In CSS, they should be styled as compact, muted audit boxes:

```html
<div class="task-log schedule-log">
  <span class="log-title">🗓️ Schedule History</span>
  <ul class="log-entries">
    <li><span class="log-date">2026-10-12 → 2026-10-16</span> P1 roll · in 4 days</li>
    <li><span class="log-date">2026-10-10 → 2026-10-12</span> P1 · in 2 days</li>
  </ul>
</div>
```
*Design Rule for Long Logs*: When rendering to PDF, historical schedule rolls longer than 3 entries should be truncated with a summary tag (`+ 5 earlier rolls`), preventing pages of dead schedule rolls from cluttering the document.

### 5.4 Vault Asset and Embed Resolution
The preprocessor must inspect all image embeds:
- Syntax: `![[img/20260802_144938.png|400]]`
- Resolution: Check `$BOB_DIR/img/20260802_144938.png` or search the vault attachments index.
- Output: `<img src="https://bob-clip.invalid/assets/img/20260802_144938.png" style="max-width: 400px;" />`

The Chromium route handler intercepts `https://bob-clip.invalid/assets/**` and streams the image directly from the vault directory on disk.

---

## 6. CLI Interface & UX Design

Following `sase/memory/cli_rules.md`, all new CLI subcommands and options must:
- Have clear, consistent `-h/--help` output.
- Keep options sorted alphabetically.
- Give every public long option a short alias.
- Preserve backward compatibility (never hard-rename or remove existing commands).

### 6.1 Enhancing `bob ref create` for Vault Notes

When `bob ref create <TARGET>` is invoked:
1. **Target Detection**: The command checks if `<TARGET>` is a local Markdown file inside `$BOB_DIR`. If so, it reads the frontmatter:
   - If `type == "[[project]]"` or `type == "[[area]]"`:
     - Automatically switch the rendering engine to the **Note Print Engine** (HTML/CSS + Chromium).
     - **Default Parent**: If `-P/--parent` is not specified, default to the note itself (for a project) or its frontmatter `parent`.
     - **Default Ref Type**: Default `-t/--ref-type` to `projects` (for project notes) or `notes` (for area notes), rather than `chat`.
     - **Title Derivation**: Default to the frontmatter `title` or the clean note stem.

### 6.2 Adding Direct Export: `bob note pdf`

To allow printing or exporting a note without Highlights intake side-effects, add a dedicated subcommand under the `note` noun:

```text
Usage: bob note pdf [OPTIONS] <NOTE>

Export an Area note or Project note to a publication-quality PDF

Arguments:
  <NOTE>  Note title, basename, or path in the vault (e.g. sase_blog, ~/bob/sase_blog.md)

Options:
  -c, --compact            Omit closed and canceled tasks from the export
  -d, --dry-run            Preview preprocessing and print statistics without writing PDF
  -f, --force              Overwrite an existing output file
  -o, --output <PDF>       Destination PDF path [default: ./<note_stem>.pdf]
  -s, --status-logs        Include detailed schedule and work logs [default: compact summary]
  -t, --theme <THEME>      Visual theme: light, dark, or print-bw [default: light]
  -h, --help               Print help
```

---

## 7. Recommended Implementation Blueprint

We propose implementing this functionality in four clean phases:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                               Implementation Phases                             │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│   Phase 1: Rust Note Preprocessor Module (`src/native/note_render/`)            │
│   • Implement Markdown AST visitor for Obsidian dialect                         │
│   • Parse and strip Dataview inline fields (`task_fields.rs` integration)       │
│   • Resolve `![[img/...]]` against vault attachments                            │
│   • Extract Project Hero Card from `^prj` line                                  │
│                                                                                 │
│   Phase 2: Note Print HTML/CSS Template (`scripts/note_print/`)                 │
│   • Create `note_print.css` with `@page` styling and CSS Grid dashboard        │
│   • Design modern task cards, status badges, and timeline log boxes             │
│   • Reuse bundled variable fonts (Inter, JetBrains Mono, Source Serif 4)        │
│                                                                                 │
│   Phase 3: Chromium Render Integration                                         │
│   • Extend `web_clip_render.py` to support `render_note(html_payload, out_pdf)` │
│   • Offline asset routing for vault images (`_route_handler`)                   │
│   • Generate PDF with outlines enabled (`outline=True`)                         │
│                                                                                 │
│   Phase 4: CLI Wiring & Highlights Marker Stamp                                 │
│   • Implement `bob note pdf <NOTE>` subcommand                                  │
│   • Update `bob ref create` to detect vault notes and invoke note renderer      │
│   • Stamp Highlights marker on page 1 for reading sync                          │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Phase 1: Rust Preprocessor (`src/native/note_render/`)
Create a new module `src/native/note_render/` in `bob-cli`:
- `ast.rs`: Parses frontmatter, headings, tasks, and text blocks.
- `sanitize.rs`: Reuses `src/native/task_fields.rs` to detect and strip inline fields while preserving priority and scheduling.
- `vault_resolver.rs`: Resolves image paths using `src/native/vault_links.rs`.
- `html_emit.rs`: Generates semantic HTML with appropriate CSS classes (`.project-hero`, `.task-card`, `.status-wip`, `.log-box`).

### Phase 2: HTML/CSS Print Template (`scripts/note_print/`)
Author `note_print.css` leveraging Chromium's `@page` capabilities:
- Paper format: Letter with 0.75in margins.
- Typography: Inter for headings and UI chips; JetBrains Mono for code spans; Source Serif 4 or Inter for narrative prose.
- Page Headers/Footers: Clean running header with note title and dynamic page numbering (`counter(page)`).
- Visual Task Cards: Discrete cards with 1px border (`#e1e4e8`), subtle background tint for active tasks (`#f6f8fa`), and color-coded status badges.

### Phase 3: Headless Chromium Invocation
Extend the existing Python adapter runner (`scripts/web_clip/`):
- Accepts the preprocessed HTML payload.
- Launches headless Chrome with `--headless=new --disable-gpu`.
- Sets print options:
  ```python
  page.pdf(
      path=out_pdf,
      format="Letter",
      print_background=True,
      outline=True,
      prefer_css_page_size=True,
      display_header_footer=False
  )
  ```
- Exits cleanly and returns the generated PDF bytes to Rust.

### Phase 4: CLI Integration & Highlights Stamping
1. In `src/native/highlights_ref/create.rs`:
   - Detect if the target Markdown file is an area or project note.
   - If true, invoke `render_note_pdf` instead of `render_temp_pdf` (Pandoc/XeLaTeX).
   - Once the PDF is produced, stamp the page-1 marker using `src/native/highlights_ref/stamp.rs` as usual.
2. In `src/native/`:
   - Expose the public subcommand `bob note pdf` for standalone exports.

---

## 8. Summary & Conclusion

The desire to generate beautiful PDFs from Obsidian Area and Project notes addresses a genuine and powerful GTD workflow: taking complex project plans onto an iPad for focused, distraction-free review with an Apple Pencil.

The current implementation in `bob ref create` fails because it treats structured Obsidian knowledge graphs as generic Markdown prose, piping them into a rigid Pandoc/XeLaTeX pipeline that cannot parse Dataview fields, fails to resolve vault image embeds, corrupts section numbering, and renders an archaic visual layout.

By adopting **Headless Chromium + HTML5/CSS3** (reusing `bob-cli`'s existing web-clip engine) and introducing a **Rust-based Obsidian note preprocessor**, `bob-cli` can produce stunning, executive-ready PDF dashboards that honor Obsidian's visual model, showcase project outcomes, and seamlessly participate in the Highlights review ecosystem.
