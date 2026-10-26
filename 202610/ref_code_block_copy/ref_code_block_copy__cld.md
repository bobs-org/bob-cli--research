# Copying Code Blocks from Bob Refs' Copy Card, and `⌘Y` in Highlights

- **Date:** 2026-10-26
- **Researcher:** cld (one of five independent researchers; lead synthesizes)
- **Request:** Let the Copy card (the "copy mode" that `⌘Y` opens in Bob Mac Capture's
  Bob Refs panel) copy the contents of code blocks. This will probably only work for
  references that `bob ref create` rendered from Markdown, and may require keeping the
  source Markdown somewhere nearby. Also add a `⌘Y` key in Highlights that opens Bob Refs
  with copy mode active for the current PDF. Lead the design, critique the plan, adjust
  requirements where justified, and recommend a solution.
- **Code inspected:** bob-cli `66f9d67f`, bob-mac-capture `1311536` (2026-10-25,
  "ephemeral Highlights-key session on focused page"). No bob-plugins changes are needed.
- **Data:** the live library (`bob ref list -R all -A -f json` on athena, 2026-10-26),
  `pdftotext`/`mutool` runs against library PDFs, and fence statistics over the 533
  Markdown reports in the bob-cli research sidecar. I use those reports as a proxy for
  the agent-report PDFs, which are rendered from the same kind of file.

---

## 0. Verdict

**Build it. Bryan's instinct to keep the Markdown is right, but "read the PDF directly"
is a dead end.**

1. **Code comes from bob, recorded when the PDF is rendered.** `bob ref create` already
   runs pandoc with two bob-owned Lua filters. A third filter records every code block
   (text, language, section) and drops an invisible PDF destination before it. bob then
   reads the destinations back for page numbers and stores a manifest. The PDF text
   layer is never read for copying.
2. **The source Markdown is preserved, but not beside the PDF.** Each source goes into a
   hidden, git-synced, write-once store, `.bob/ref-sources/<type>/<birth-stem>--<hash12>/`,
   holding `source.md` and `code.json`. A `source_markdown` provenance field in the ref
   note points to it. `lib/<stem>.md` is already Highlights' sidecar filename, and an
   indexed `.md` would leak report checkboxes into the task system.
3. **The Copy card gains `C` (Code block…) and `M` (Markdown source).** `C` opens a
   picker modelled on the existing `H` highlight picker, with a live code preview well.
   When Bob knows which page you are reading, the picker opens with the code on that page
   selected.
4. **`⌘Y` in Highlights opens a Highlights-key session**, like today's `⌘T`. It starts
   from fresh defaults, selects the focused PDF, opens the Copy card for it, and buffers
   keys you type while the Highlights read finishes. The key yields to the panel when it
   is visible, so `⌘Y ⌘Y` keeps meaning "copy the default row".
5. **The headline gesture is `⌘Y C ↵`:** copy the code block on the page you're reading,
   exactly as written. `⌥↵` copies it as fenced Markdown.

The scope is worth it. **473 of the 531 PDF-backed references (89%) are Markdown-born
agent reports.** **83% of reports contain fenced code (2,334 blocks).** **48% of those
blocks wrap in the PDF, and 57% depend on leading indentation**, so selecting them in
Highlights pastes broken text today.

---

## 1. What exists today (verified)

| Fact | Where | Consequence |
| --- | --- | --- |
| The Copy card uses fixed letters `I T W U L X D N O P F R S`, `1`–`9` for notes, `A` for all notes, and `H` for the highlight picker. **`C` and `M` are free** | `RefsCopy.swift` (`RefsCopyKey.parse`) | New rows fit without re-lettering anything |
| `H` opens a 9-row window (36 pt rows). Digits copy the visible window, arrows scroll, `A` copies all, group headers are non-selectable, and `⌥` swaps previews in place | `RefsHighlightPicker.swift`, `docs/refs.md` §Copy card | The code picker is the same interaction with a different payload |
| Inside the card, `↵` or `⌘Y` copies the selected row. The default row is the Marker ID, else the Wiki link | `RefsCopyKeyMap`, `RefsCopyCatalog.defaultKey` | `⌘Y ⌘Y` must keep this meaning |
| A copy checks the pasteboard write, hides Refs, shows a glass HUD, and returns focus to the frontmost app | `docs/refs.md` | `⌘Y … ↵` in Highlights lands the text back in Highlights' world |
| The panel is 1344 × 798 pt on a MacBook, and the card covers the inspector column | `docs/refs.md` §The panel | About 640 × 700 pt: room for a list and a real code preview |
| `HighlightsTakeover` registers keys only while Highlights (or the override app) is frontmost. `⌘T` steps aside while the panel is visible (`yieldsToVisiblePanel`). `HotKeyAction` uses ids 1–4 | `HighlightsTakeover.swift`, `RefsHighlightsTabsKey.swift`, `HotKeyRegistry.swift` | `⌘Y` becomes action 5 with the same yield rule |
| `⌘T` from Highlights is an **ephemeral session**: fresh defaults, Tabs on, focused PDF selected, nothing remembered. The page comes from Highlights' window title (`name.pdf – Page 5 of 25`) | commit `1311536`, `HighlightsWindowTitle.pageNumber(fromTitle:)` | `⌘Y` reuses the session and gets the page for free |
| Pandoc renders fenced blocks through fvextra `Highlighting` with `breaklines,breakanywhere` | `create.rs` `PANDOC_HEADER_INCLUDES` | Long lines wrap in the PDF with continuation glyphs |
| Bob already uses Lua filters that write JSON reports (`-M bob-return-links-report=<path>`) and TeX anchors that emit named PDF destinations (`\special{pdf:dest (…)}`) | `return_links.lua`, `return_links.tex` | The manifest filter is the same pattern. `lopdf` is already a dependency |
| The vault-note snapshot route passes `CodeBlock`s through, stripping only U+FE0F | `note_snapshot/note.lua` ~L531 | Both Markdown routes can share one manifest filter |
| `CreatePlan.source_markdown` holds the Markdown in memory during create, but **it is never persisted** | `create.rs:287` | Persistence is new work |
| The PDF marker already carries create-time provenance into the note: `source_note`, `captured`, `return_links`, `research` | `highlights_ref/mod.rs` `COMMON_USER_FIELDS` | A `source_markdown` field follows the same path, including queued intake |
| **`lib/<stem>.md` is Highlights' Markdown sidecar export.** `lib/chat` holds 142 of them, and create refuses a same-stem `.md` beside an output PDF "because Highlights would interpret it as a sidecar" | `docs/highlights-ref-sync.md`, live `lib/chat/*.md` | The source cannot live "next to" the PDF under that name |
| The vault `.gitignore` is an allowlist. `!*.md` matches at any depth. Bob machine data lives in allowlisted `.bob/<feature>/` paths (`gkeep`, `stats`, `themes`, `relations`). `xlib/` is ignored | `~/bob/.gitignore` | `.bob/ref-sources/**/source.md` is already tracked; `code.json` needs one allowlist line |
| Task-status walkers skip dot-directories and `done/` | `task_status_hooks/parse.rs` `should_skip_directory` | `.md` files under `.bob/` don't become tasks. Obsidian also ignores dot-folders |
| A 2026-10 Accessibility read of Highlights' menu bar found `⌘O`, `⌃Tab`/`⌃⇧Tab`, `⇧⌘\`, `⌘0`–`⌘5`, `⌘I` and `⌥⌘T` bound. **`⌘Y` was not checked** | prior research, `highlights_tab_switcher__cld` F13 | Phase 0 must confirm `⌘Y` is free in Highlights |

---

## 2. Measurements

### 2.1 The library

| Quantity (athena, 2026-10-26) | Value |
| --- | --- |
| Indexed `ref/` rows / PDF-backed | 1,133 / **531** |
| PDF-backed by type | chat **473** (all `origin: agent-report`), blogs 26, papers 18, docs 11, notes 3 |
| Rows with `research_ref` | 1 |

Markdown-born references (agent reports and vault-note snapshots) are the overwhelming
majority. "Markdown only" is not much of a limitation.

### 2.2 Code in reports (533 research-sidecar reports as proxy)

| Quantity | Value | Design consequence |
| --- | --- | --- |
| Reports with ≥ 1 fenced block | **445 (83%)** | `C` will appear on most cards |
| Blocks per report (when any) | median **4**, p90 **11**, max **21** | Digits alone can't reach every block, so the picker needs a scrolling window |
| Total blocks / median lines / p90 lines | 2,334 / 7 / 24 | Rows show one or two lines. The preview well shows about 15 |
| Blocks over 40 lines / single-line | 59 / 265 | The preview must fade out cleanly |
| Blocks with a line over 80 chars (wraps in the PDF at about 80 mono columns) | **1,115 (48%)** | The PDF copy is wrong for half the blocks |
| Blocks with leading-space indentation | **1,338 (57%)** | Indentation must survive exactly (YAML, Python, trees) |
| Top languages | `text` 798, `markdown` 314, none 239, `yaml` 174, `mermaid` 152, `bash` 107, `json` 93, `rust` 76, `md` 56, `swift` 51 | Untagged and `text` blocks are first-class. Mermaid (rendered as figures) needs its source copyable |
| Most repeated first lines | `---` ×70, `{` ×57, `anchor: \|-` ×23, a box-drawing rule ×17 | Row titles must use the first *meaningful* line, not line 1 |
| Reports containing Markdown checkboxes | **123 (23%)** | An Obsidian-indexed copy would inject tasks |
| Source size | median 30.2 KB, p95 49.7 KB, 16 MB for 533 files | Storing every source costs about 14 MB of text, which git compresses well |

### 2.3 What the PDF text layer actually contains

- **Wrapped lines break apart.** `pdftotext` on a mockup block in
  `lib/chat/refs_panel_ctrl_y_copy_card.pdf` emits `↪` continuation glyphs and stray `⌋`
  marks. One wrapped line's tail (`Se… │`) comes out on its own line, after content from
  the next row.
- **Characters disappear.** A source block containing `cool😎.` reads `cool.` in the PDF
  text, because DejaVu Sans Mono has no emoji glyph.
- **Heuristics can't find blocks.** A naive "all-monospace line at the left margin"
  detector on `ace_refresh_loop_and_link_rail_regression.pdf` found 14 "code blocks". All
  of them were monospace table cells (`10:36`, `10:38 10.17`).

The PDF can locate a block, which is useful for backfill (§7). It cannot be the
**source** of the copied text.

---

## 3. Critique: is this a good idea?

**Yes.** Agent reports carry commands, configs, schemas, and mockups that Bryan pastes
into terminals, agent prompts, and notes. Copying them from Highlights is unreliable for
about half the blocks today, and fails *silently*: the paste looks plausible but has the
wrong indentation and stray `↪` glyphs. A one-gesture, exact copy closes that gap. The
building blocks are already in place: bob's Lua-filter and anchor machinery, the Copy
card and `H` picker, and the Highlights-key session with page awareness.

What I would change about the plan as stated:

| Plan element | Assessment |
| --- | --- |
| "Only Markdown→PDF refs" | Correct for v1, and it covers 89% of PDF-backed refs. **Widen it slightly:** both Markdown routes (plain Markdown and vault-note snapshots) produce the manifest. Web clips come later; PDFs and arXiv papers never do |
| "Copy the Markdown to some nearby location" | **Preserve it: yes. Nearby: no.** `lib/<stem>.md` is Highlights' sidecar name. Any indexed `.md` exposes 23% of reports' checkboxes to Obsidian Tasks and Dataview. `xlib/` is not in git. Use a hidden, write-once store (§5) |
| "Unless we can read the PDF directly" | **No** (§2.3). The PDF stays a locator, never the source of copied text |
| Copying the source is enough | **Not quite.** Pages, and the exact set of blocks that reached the PDF, are only known at render time. Snapshots can expand transclusions and drop sections with `-S`, and Mermaid becomes figures. Store a render-time **manifest** next to the source |
| `⌘Y` in Highlights opens copy mode for the current PDF | **Yes**, as a Highlights-key session, configurable (Command-Y / Off), yielding to the visible panel. Add a type-ahead buffer so `⌘Y C ↵` never types `c` into the search field (§6.4) |
| "Lead the design" | The design leans on what the card already teaches: fixed letters, a picker layer, `⌥` alternates, hide-on-copy with a HUD. It adds one new visual element, the preview well |

Risks I designed against:

| Risk | Failure | Answer |
| --- | --- | --- |
| Wrong text | The paste is subtly corrupted (indentation, wraps, missing glyphs) | Copy only exact pandoc `CodeBlock` text recorded at render time (§4) |
| Wrong block | The page has several blocks, or the page guess is off | Page-aware preselection plus a full preview of exactly what will be copied (§6.3) |
| Wrong reference | The Highlights read is slow or ambiguous, or keys leak into search | The session freezes the target from the focused tab's full path, buffers keys while resolving, and shows explicit failure states (§6.4) |
| Source/PDF drift | The source is edited after rendering | The store is write-once and content-addressed. The manifest is captured from the very render that produced the PDF |
| Vault pollution | Sources show up as notes or tasks | A hidden dot-directory store, plus walker regression tests (§5) |
| Lifecycle breakage | Rename, intake, or overwrite lose the source | The pointer never needs moving. The provenance field travels like `source_note` (§5.3) |
| Key conflict | `⌘Y` already does something in Highlights | Phase 0 Accessibility menu read. The setting can turn it Off |

---

## 4. Design decision A: where does the copied text come from?

| Option | Verdict | Why |
| --- | --- | --- |
| **PDF text layer** (PDFKit or `pdftotext`) | Rejected | Wraps, lost glyphs, and table cells that look like code (§2.3) |
| **PDF plus font and shading heuristics** | Rejected | Still can't undo wrapping or recover dropped glyphs, and it's fragile across render profiles |
| **Embed the source in the PDF** (`/EmbeddedFiles`) | Rejected as primary | Unverified whether Highlights' PDFKit saves preserve it. Opaque to agents. It also adds a PDF write path |
| **Store the source; parse it with pandoc at read time** | Rejected | The Mac app would depend on pandoc. A parse can disagree with what was rendered (transclusions, `-S`, Mermaid). It still gives no page numbers |
| **Link to the research artifact** | Rejected as the store | Covers only agent reports, the research repos aren't on the Mac, and `research_ref` is set on 1 row |
| **Store the source plus a render-time manifest** | **Chosen** | The manifest matches the PDF exactly, pages come from anchors, and reading it is a cheap JSON read through `bob` |

### 4.1 The manifest

The pandoc run already uses `--lua-filter` reports. Add a code-block filter shared by the
plain-Markdown route and the vault-note snapshot profile:

- Walk every `CodeBlock` in document order, **before** the diagrams swap filter turns
  Mermaid into figures. Record `n`, `lang` (first class), the raw info string and
  attributes (for example `title=`), the exact `text` (pandoc's: LF line endings, tabs
  kept, no trailing newline), the source line range where available, and a `kind`
  (`code` or `mermaid`).
- Track the enclosing section as printed (number and title, using the numbering rule in
  `number_from_top_level`).
- Emit `\BobCodeAnchor{n}` before each block and `\BobCodeAnchorEnd{n}` after it. These
  are invisible named destinations, built exactly like `\BobReturnAnchor`, plus
  `\nopagebreak` so the start anchor stays on the block's page.
- Write the JSON through `-M bob-code-report=<path>`, the same pattern as return links.

After the PDF exists, bob reads the `/Dests` name tree with `lopdf`, maps `bob-code-n` and
`bob-code-n-end` to physical page indices, and writes `code.json`. Reading the finished
PDF works for both routes: pandoc runs XeLaTeX in its own temp dir on the plain route,
while the snapshot route runs XeLaTeX in bob's scratch dir.

Bob also computes a **`summary`** for each block: the first meaningful line, skipping
blank lines, `---`, lone braces, and pure box-drawing rules. It also computes **`fenced`**,
the block wrapped in a fence one backtick longer than any run inside it. That matters for
the 370 `markdown`/`md` blocks, which often contain fences themselves. The Mac app
presents these values and computes neither, per `decisions:mac-capture-is-a-thin-client`.

```json
{
  "schema_version": 1,
  "source": { "kind": "markdown", "sha256": "5d3b…", "bytes": 41213 },
  "pdf": { "pages": 24, "sha256_at_render": "9a1c…" },
  "blocks": [
    {
      "n": 2, "kind": "code", "lang": "yaml", "info": "yaml",
      "summary": "refresh:", "lines": 14,
      "text": "refresh:\n  interval_ms: 250\n…",
      "fenced": "```yaml\nrefresh:\n…\n```",
      "section": { "number": "3", "title": "Root cause" },
      "page": 7, "page_end": 7, "page_source": "anchor",
      "source_lines": [88, 103]
    }
  ]
}
```

`page_source` is `anchor` (new renders), `text_match` (backfill, §7), `section` (only the
outline is known), or `null`. Every consumer treats pages as a hint, never as identity.

---

## 5. Design decision B: where does the Markdown live?

### 5.1 Options

| Location | Verdict | Why |
| --- | --- | --- |
| `lib/<rel>.md` beside the PDF | Rejected | That name is Highlights' sidecar export |
| `lib/<rel>.source.md` | Rejected | Obsidian indexes it, so 23% of reports would inject checkbox tasks into Tasks and Dataview. Every bundle mover (rename, intake, overwrite, `ref_history`) would also need to learn it |
| `lib/<rel>/.x.source.md` (dot-file beside the PDF) | Rejected | Hidden companions are easy to miss in `mv` and Finder, and the bundle movers still need changes |
| `xlib/` | Rejected | Not in git, so the Mac never sees it |
| **`.bob/ref-sources/<type>/<birth-stem>--<hash12>/`** | **Chosen** | Hidden from Obsidian and the task walkers. Synced by git like other `.bob/` data. Write-once, so nothing moves on rename. Readable by name |

### 5.2 Layout and pointer

```
~/bob/.bob/ref-sources/
  chat/
    ace_refresh_loop_and_link_rail_regression--5d3be944e47e/
      source.md     # exact input bytes (snapshot: the note's bytes at capture)
      code.json     # render-time manifest (§4.1)
```

- `hash12` is the first 12 hex digits of the SHA-256 of `source.md`. The full digest is
  in `code.json`, and `bob ref doctor` verifies it.
- The directory keeps the **birth stem**. After a rename it honestly reads "captured as".
  Identity comes from the pointer, never from the directory name.
- The pointer is a provenance field, `source_markdown: chat/ace_refresh…--5d3be944e47e`.
  It is written to the ref note frontmatter, and **also to the PDF marker** like
  `source_note` and `captured`, so queued intake can file it.
- Vault `.gitignore`: add `!/.bob/ref-sources/**/*.json`. `source.md` is already covered
  by `!*.md`.
- Vault-note snapshots store the note's raw bytes as `source.md`. The manifest reflects
  the projected document, so transcluded blocks are included and `-S`-dropped sections
  are not.

### 5.3 Lifecycle

| Event | Store | Pointer |
| --- | --- | --- |
| Create with inline intake | Written under the create locks (temp file then rename; idempotent) and staged in the same scoped commit as the PDF and note | Frontmatter and marker |
| Create queued in `xlib/` | Written at create time; vault sync or the intake commit carries it | Marker; intake copies it into frontmatter |
| `bob ref rename` | Untouched | Unchanged |
| `-f overwrite` | New directory (new hash). The old one stays for the `ref_history/` copy | Repointed inside the overwrite transaction. A rollback leaves at most an orphan directory |
| Reread `__vN` | New directory | The new note's own pointer |
| Dry run | Nothing written | — |
| Deletion or manual cleanup | Orphans remain | `bob ref doctor` lists orphans and dangling pointers |

The marker field adds one line to the page-1 note in Highlights (for example
`- source_markdown: chat/…--5d3be944e47e`). That is the same kind of line as `captured:`,
and it is the price of handling queued intake uniformly. *Alternative if Bryan objects:*
keep the pointer frontmatter-only, and have intake relink by matching `code.json`'s
`pdf.sha256_at_render` against the untouched queued PDF.

---

## 6. UX design

### 6.1 Principles

1. **The card stays the card.** Nothing is reordered or re-lettered. `C` and `M` are new
   fixed letters, and `⌘Y ⌘Y` still copies the default row.
2. **You see exactly what you'll paste.** Every code row previews real lines, and the
   picker's preview well shows the selected block as it will paste: no wrapping, true
   indentation.
3. **Start where the reader is.** When Bob knows Highlights' current page, the code on
   that page is preselected and marked.
4. **Exact by default, Markdown on request.** `↵` copies the raw code; `⌥↵` copies it
   fenced.
5. **Absence explains itself.** Pressing `C` on a reference without code says why,
   following the card's existing hidden-row rule.

### 6.2 The Copy card: two new rows

A new **Document** group sits between Files and Your Notes:

```
 [ ] COPY                                                     Highlights · p. 7
      Why `sase ace` Is Slow: A Chronic Refresh Loop Plus an Acute Link-Rail…
 ▌[I] Marker ID       ace_refresh_loop_and_link_rail_regression
  [T] Title           Why `sase ace` Is Slow: A Chronic Refresh Loop…
  [W] Wiki link       [[ref/chat/ace_refresh_loop_and_link_rail_regression]]
 ──────────────────────────────────────────────────────────────────────────
  [N] Note path       ref/chat/ace_refresh_loop_and_link_rail_regression.md
  [P] PDF path        ~/bob/lib/chat/ace_refresh_loop_…_regression.pdf
  [F] PDF file        ace_refresh_loop_and_link_rail_regression.pdf
  [R] Reading task    [[obsidian_ref#^ref-ace-refresh-loop-and-link-rail-…]]
 ──────────────────────────────────────────────────────────────────────────
  [C] Code block…     6 blocks · 2 on this page · bash, yaml, rust
  [M] Markdown        source · 41 KB · captured Oct 20
 ──────────────────────────────────────────────────────────────────────────
  YOUR NOTES  3
  [1] Note 1          ↳ This is the regression, not the loop          p. 4
  [A] All your notes  3 notes · Markdown
  [H] Pick a highlight…   12 highlights
 ↵ copies Marker ID · ↑↓ choose · ⌥ alternates · esc back
```

- **`C` Code block…** opens the picker. Its preview counts blocks and lists up to three
  languages, adding "N on this page" when the page is known.
- **`M` Markdown** copies the whole preserved source as text. **`⌥M`** copies its `~`
  path, which works on athena too because the vault is `~/bob` on both hosts, so it can
  go straight into an agent prompt.
- Hidden reasons (shown when the key is pressed):
  - "No Markdown source on file — code copy works for Markdown-born references" (PDF,
    arXiv, web clip, or a pre-feature ref without backfill).
  - "No code blocks in this reference".
  - "Code copy needs a newer bob" (field absent from an older `bob`).
  - While loading, the existing pending state: "Waiting for code… esc cancels".

### 6.3 The `C` picker

```
 [ ] COPY › CODE                                     6 blocks · Highlights p. 7
      Why `sase ace` Is Slow: A Chronic Refresh Loop Plus an Acute Link-Rail…
  2  Reproduction
  [1] bash    sase ace --profile 2>&1 | tee ace.log                   p. 5
              3 lines
  3  Root cause
 ▌[2] yaml    refresh:                                              ● p. 7
              interval_ms: 250 · 14 lines
  [3] rust    fn refresh_loop(state: &mut AppState) {             ● p. 7–8
              41 lines
  4  Link rail
  [4] text    ┌─ link rail ──────────────────────────────┐            p. 9
              12 lines
 ╭ yaml ──────────────────────────────────────────────── 14 lines · p. 7 ╮
 │ refresh:                                                              │
 │   interval_ms: 250                                                    │
 │   jitter_ms: 40                                                       │
 │   on_focus: true                                                      │
 │   …                                                                   │
 │                                                   +6 more lines       │
 ╰───────────────────────────────────────────────────────────────────────╯
 ↵ copy · ⌥↵ as fenced Markdown · 1–9 copy · ↑↓ more · esc back
```

- **Rows** (36 pt, the `H` picker metrics). Line 1 has a keycap, a language chip (none
  for untagged blocks), bob's `summary` in 11.5 pt monospace (the card's existing preview
  font), and a right-aligned page pill. Line 2 has the second meaningful line or the
  `title=` attribute, plus the line count. Mermaid rows read
  `mermaid  flowchart LR · diagram source`.
- **Group headers** are the printed section number and title, non-selectable, drawn
  exactly like `H` picker groups.
- **`●` marks blocks on Highlights' current page.** VoiceOver reads "on this page".
- **Preview well.** It shows the selected block in 12 pt monospace with no wrapping,
  clipping long lines with a trailing fade. It fills the remaining card height (about 15
  lines on a MacBook), fades the last two lines when truncated, and adds a
  `+N more lines` pill. Rounded 12 pt corners with a quiet fill, using semantic colors
  for light and dark mode. While `⌥` is held it shows the fences, the same in-place swap
  as the card.
- **Initial selection.** With page *P* known, select the first block whose
  `[page, page_end]` contains *P*. Otherwise take the first block after *P*, else the
  last block before it, and scroll that block to the top of the window. Without a page,
  select block 1.
- **Keys.** `1`–`9` copy the visible window positions. `↵` or `⌘Y` copies the selection
  and `⌥↵` copies the fenced form. `↑↓` and `⌃N/P/J/K` move and scroll. `A` copies every
  block fenced, in order, under its section headings (cheap, and consistent with `H`).
  `esc` or `⌃[` returns to the card.
- **Payload.** Exact `text` (no trailing newline, so pasting into a shell never adds a
  final Return). `⌥` gives `fenced`. Both come from bob.
- **HUD.** "Copied yaml · 14 lines · p. 7", "Copied Mermaid source · p. 9", or "Copied
  yaml · fenced".

Syntax coloring is deliberately out of v1. Monochrome code in the panel's own monospace
type, with a language chip, is calm and legible, and it needs no Swift tokenizer. If it
proves wanted later, bob can supply token spans from pandoc's highlighter.

### 6.4 `⌘Y` in Highlights

| Step | Behavior |
| --- | --- |
| Registration | `HotKeyAction.refsHighlightsCopy = 5`, default **Command-Y**, Settings › References "Copy key in Highlights: Command-Y / Off". Registered only while Highlights (or the override app) is frontmost **and Bob Refs is hidden** (`yieldsToVisiblePanel`) |
| Show | Opens Bob Refs as a Highlights-key session (fresh defaults, Tabs on, nothing remembered), exactly like `⌘T`. The card column immediately shows the Copy header and "Finding your PDF in Highlights…" |
| Resolve | When the Tabs snapshot loads, select the **focused** tab (matched by its full path) and open the Copy card for it, with `focusPage` taken from the window title |
| Type-ahead | Keys typed while resolving (`C`, digits, `↵`, `⌥↵`, `M`, …) are **buffered** and replayed into the card in order. They never reach the search field. `esc` cancels and hides. After about 2 s without a result, show the failure state and drop the buffer |
| Failure states | Accessibility not granted: the existing Tabs explainer card. No document open: "Highlights has no open document". Focused tab unmatched or a collision: "“x.pdf” isn't a Bob reference — nothing to copy". Read failed: "Couldn't read Highlights · ⌘R retries" |
| After copy | Hide, show the HUD, and focus stays with Highlights. `⌘V` works immediately, and the session is forgotten |
| Conflicts | Takeover registration failures reuse "Refs hotkey conflict: …" |

### 6.5 Gestures

| Goal (reading in Highlights) | Keys |
| --- | --- |
| Marker ID of this PDF (unchanged habit) | `⌘Y ⌘Y` or `⌘Y I` |
| **The code block on this page** | **`⌘Y C ↵`** |
| The next block on this page | `⌘Y C ↓ ↵`, or its digit |
| The same block, fenced for Obsidian or an LLM | `⌘Y C ⌥↵` |
| The whole Markdown source | `⌘Y M` |
| Source path for an agent prompt | `⌘Y ⌥M` |

Inside Bob Refs (not from Highlights), `⌘Y C` works on the selected row. Page
preselection applies whenever the row is Highlights' current tab and its page is known,
for example in the Tabs scope.

---

## 7. Backfill for existing references

The new pipeline covers every future create. Most of the existing 473 chat references
can be recovered too.

- **Candidates.** 429 of 473 (91%) have a same-stem `.md` in one of the five research
  repos on athena. For research-hook creates, `--include-id` derives the id from the
  report filename. 45 stems have more than one candidate.
- **Verification without re-rendering.** Parse each candidate with pandoc (AST only, the
  same manifest filter, no XeLaTeX). Then locate each non-Mermaid block, in order, in the
  library PDF's text, comparing with whitespace and wrap glyphs normalized away.
  - In an 8-report sample (37 blocks, 5 of them Mermaid), every report's blocks were
    found in order on plausible pages.
  - Of the 32 non-Mermaid blocks, 21 matched at ≥ 99% similarity, 7 at 91–98%, and 4 at
    70–88% (wrapped box-drawing, a missing emoji, or post-render edits).
  - Accept a candidate when its title matches and at least 80% of blocks match at
    ≥ 85%. Pages come from the match (`page_source: text_match`). Unmatched blocks keep
    `page: null`.
- **Command.** A one-off `bob ref` subcommand. Proposed spelling:
  `bob ref backfill-sources -s DIR… [-d]`, with short aliases and alphabetical options
  per `cli_rules.md`. Dry-run first; then write the store entries and pointers and commit
  in batches. Ambiguous stems take the single passing candidate, or are skipped with a
  reason.

Backfill is a fast-follow. It is not required for v1, because the `C` row explains a
missing source.

---

## 8. bob CLI surface

```
bob ref code <REF> [N] [-b DIR] [-f human|json|markdown|raw] [-p PAGE] [-r DIR]
```

- With no `N`: a colored human list grouped by section. Each line shows `n`, language,
  page, line count, and summary, followed by a `hint: bob ref code <ref> 2 | pbcopy`
  line.
- With `N`: prints block `N` **raw** (the default format when `N` is given), so
  `bob ref code x 2 | pbcopy` reproduces the card's copy.
- `-p PAGE` keeps only blocks that touch a page. `-f markdown` prints fenced blocks under
  section headings (for agents). `-f json` prints the envelope plus `code.json` (the
  Mac's contract).
- Resolves `REF` exactly like `bob ref show`. Read-only.

Additive changes elsewhere:

- `bob ref show`: a `source` object (`kind`, `key`, `path`, `sha256`, `bytes`,
  `code_blocks`). Human output gains a `source` metadata row and the Markdown digest gains
  a `- **Source:** …` bullet.
- `bob ref doctor`: a `ref_sources` row for dangling pointers, hash mismatches, orphans,
  and Markdown-born refs without a source (with the backfill hint).
- Docs: `docs/ref.md` (`ref code`, the `show` source object), `docs/highlights-create.md`
  (preservation, manifest, store), `docs/highlights-ref-sync.md` (marker field).
- Releases ride the daily train (agents don't touch the version or `CHANGELOG.md`). All
  JSON growth is additive, and the app decodes with `decodeIfPresent`.

The Mac fetches `bob ref code <path> -f json` as soon as the card opens, in parallel with
the existing notes fetch, and keeps a small LRU like the inspector's. The list snapshot
needs no change.

---

## 9. Requirement adjustments (explicit)

| # | Original | Adjustment | Why |
| --- | --- | --- | --- |
| **R1** | Copy the Markdown "to some nearby location" | Write-once, git-synced **`.bob/ref-sources/<type>/<birth-stem>--<hash12>/`**, pointed to by a `source_markdown` provenance field. **Not** beside the PDF | `lib/<stem>.md` is Highlights' sidecar. An indexed `.md` would leak 23% of reports' checkboxes into tasks. `xlib/` isn't in git. A write-once store survives rename, intake, and overwrite with no file moves |
| **R2** | Keep the Markdown | Keep the Markdown **plus a render-time manifest** (blocks, sections, pages) | Only the render knows which blocks reached the PDF and on which pages. Reading a JSON file needs no pandoc on the Mac |
| **R3** | "Unless we can read the PDF directly" | **Never** copy from the PDF text layer. Use it only to locate blocks during backfill | Measured wraps, dropped glyphs, false positives (§2.3) |
| **R4** | Markdown-made refs only | v1 covers both pandoc routes (Markdown files and vault-note snapshots). Backfill covers about 91% of existing agent reports. Web clips come later; PDFs and arXiv papers never | Maximizes coverage without inventing data |
| **R5** | Target code blocks in copy mode | A **`C` picker** modelled on `H`, page-aware, with a preview well. **Mermaid is included** as diagram source. `⌥` gives fenced Markdown | Up to 21 blocks per report means a single keypress can't reach them all. Fenced copies paste cleanly into Obsidian and LLM chats |
| **R6** | — | Add **`M`**: copy the whole preserved Markdown (`⌥M` copies its path) | Makes "always have the original" usable from the same place |
| **R7** | `⌘Y` in Highlights opens copy mode for the current PDF | Kept, as a **Highlights-key session** (fresh, ephemeral, focused PDF), **configurable**, **yielding to the visible panel**, with a **type-ahead buffer** and explicit failure states. `⌘Y` opens the standard card, **not** the code picker | Predictability: `⌘Y ⌘Y` and the default row keep their meaning, and `⌘Y C ↵` is one extra key for the code case |
| **R8** | — | **bob owns** block identity, language, summary, fenced form, and pages. The app presents and picks | `decisions:mac-capture-is-a-thin-client` |
| **R9** | — | **Phase 0 must confirm** `⌘Y` is free in Highlights' menus and that the window title's page is the physical page for bob PDFs | The prior menu inventory didn't cover `⌘Y` |

---

## 10. Alternatives considered and set aside

- **`⌘Y` opens straight into the code picker whenever the page has code.** Faster by one
  key, but `⌘Y`'s result would depend on page content, and `⌘Y ⌘Y` would silently change
  meaning. Rejected for predictability.
- **A page-aware default row** (the card's `↵` copies this page's code). The same
  objection: the original Copy card research chose a fixed default specifically because
  a sticky or contextual default becomes a trap.
- **Number badges on code blocks in the PDF** ("#3", so picker numbers match the page).
  Attractive, but it changes every future PDF, risks polluting the text layer, and
  conflicts with window-relative digits. Revisit only if the preview well proves
  insufficient.
- **"Repair copy"**: select part of a block in Highlights, press `⌘Y`, and Bob
  preselects the matching block (or even the exact lines). Elegant, but reading
  Highlights' selection through Accessibility is unverified. Good later experiment.
- **Making the PDF's own copy clean** (ActualText to hide break glyphs). That would only
  help future PDFs, depends on PDFKit honoring ActualText, and doesn't restore missing
  glyphs. It complements this feature but cannot replace it.
- **A compact copy-only popover** instead of the full panel. Rejected to keep one copy
  surface, and because the request names the ref panel.

---

## 11. Risks and open questions

| Item | Plan |
| --- | --- |
| `⌘Y` already bound in Highlights | P0: Accessibility read of the menu bar on the Mac, and check that the Carbon hotkey takes precedence. If bound, default to Off and offer an alternative |
| The window title's page may be a label rather than an index | P0: check a bob PDF whose contents span several pages. Bob's pandoc output numbers pages in arabic from 1, so label and index should agree |
| Anchor page off by one (anchor at a page bottom, block on the next page) | `\nopagebreak` plus an end anchor, and treat pages as ranges. P0: re-render 20 reports in scratch and compare anchor pages with text-match pages |
| A walker indexes `.bob/ref-sources/**/source.md` | Phase 1 regression tests: a `- [ ] #task` line there must never appear in `bob plan`, task-status hooks, `bob query`, or link repair |
| Extra line in the marker's page-1 note | Ask Bryan. The frontmatter-only alternative is in §5.3 |
| Sources hold content the PDF omits (HTML comments) | Acceptable: a private vault that already holds the PDFs. Document it |
| Old `bob` paired with a new app | The `C` and `M` rows hide with "needs a newer bob" |

Questions for Bryan: (1) is the marker line acceptable? (2) should `M` default to the
text or to the path? (3) do you already use `⌘Y` in Highlights? (4) should backfill run
across the whole library, or on demand?

---

## 12. Recommended solution

**Adopt the design above, in this order:**

| Phase | Repo | Scope | Done when |
| --- | --- | --- | --- |
| **P0 spike** (about 2 h) | Mac + athena | `⌘Y` is free in Highlights and wins as a Carbon hotkey; the title page is the physical page; anchor accuracy on 20 scratch re-renders; walker tests sketched | Findings recorded; go or no-go on `⌘Y` |
| **P1 Store + manifest** | bob-cli | Code-block Lua filter and anchors on both pandoc routes; `lopdf` destination read; write-once `.bob/ref-sources` writer inside the create locks and commit; `source_markdown` in marker and frontmatter; intake, overwrite, and reread wiring; vault `.gitignore` line for `code.json`; walker regression tests | A new report's `code.json` matches every fence byte for byte, with correct pages; rename, queued intake, and overwrite all keep a valid pointer |
| **P2 Read surface** | bob-cli | `bob ref code` (human, json, markdown, raw; `-p`); `ref show` source object and row; `doctor` row; docs | `bob ref code x 2 \| diff - <(fence 2)` is empty; the JSON contract is tested |
| **P3 Card + picker** | bob-mac-capture | Decode the new fields; `C` and `M` rows in a Document group; a `RefsCodePicker` (RefsCore, pure, unit-tested); preview well; HUD strings; light and dark render fixtures; VoiceOver labels; docs `refs.md` | `⌘Y C ↵` from the panel copies exact text; fixtures reviewed |
| **P4 Highlights `⌘Y`** | bob-mac-capture | `HotKeyAction` 5, setting, takeover sync with yield, session arming, type-ahead buffer, failure states; docs `refs.md` and `keyboard.md` | On page 7, `⌘Y C ↵` copies page 7's block, even when typed within 150 ms of `⌘Y`; Highlights stays frontmost |
| **P5 Backfill** | bob-cli | The verified backfill command, run on athena (dry run, review, write) | Most of the 429 candidates attached; skips reported with reasons |
| Later | both | Web-clip manifests (from the reader-mode DOM, with section-level pages); "repair copy" from a Highlights selection; optional syntax coloring | — |

Once P1 lands, consider recording two decisions with `/sase_memory_write`: **"Reference
sources are preserved write-once in `.bob/ref-sources`"** and **"Code copy reads bob's
render-time manifest, never the PDF text layer"**. Both are the kind of choice a later
agent might otherwise undo.

The result: while reading any agent report in Highlights, **`⌘Y C ↵` puts the code
block you're looking at on the clipboard exactly as it was written**, with the card
showing it first. Bob also keeps every report's original Markdown, one keypress (`M`)
away.

---

## Appendix: method

- Library: `bob ref list -R all -A -f json`, aggregated by `ref_type` and `origin`.
- Fence statistics: a CommonMark-style fence scan over 533 `.md` files in the bob-cli
  research sidecar, counting blocks, languages, line lengths over 80 characters, leading
  indentation, and checkbox lines.
- PDF evidence: `pdftotext -layout` on `lib/chat/refs_panel_ctrl_y_copy_card.pdf`;
  `mutool draw -F stext` font runs on `lib/chat/ace_refresh_loop_and_link_rail_regression.pdf`.
- Backfill sample: report text via `sase artifact read`; normalized (NFKC, whitespace and
  `↪`/`⌋` stripped) in-order matching against `pdftotext` output. Similarity is a
  `difflib` ratio over a 1.2× window, rescaled so 1.0 is a full match.
- Code: bob-cli `create.rs`, `return_links.{lua,tex,rs}`, `note_snapshot/note.lua`,
  `highlights_ref/mod.rs`, `task_status_hooks/parse.rs`; bob-mac-capture `RefsCopy.swift`,
  `RefsHighlightPicker.swift`, `HighlightsTakeover.swift`, `RefsHighlightsTabsKey.swift`,
  `HotKeyRegistry.swift`, `RefsPanelModel.swift`, `RefsHighlightsTabs.swift`.
