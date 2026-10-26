# Copying code-block contents from the Refs copy card (`cmd+Y`) — research

Scope: add support for targeting (copying) code-block contents from the copy
mode activated from the bob-mac-capture ref panel via `cmd+Y`, restricted to
refs whose PDF was rendered from Markdown via `bob ref create`, plus a new
`cmd+Y` keymap in the Highlights app that opens the ref panel with copy mode
for the current PDF. Lead the design: intuitive, reliable, beautiful.

Findings below are from independent inspection of `bob-cli` (`src/native/
highlights_ref/create.rs`, `src/native/ref_library/show.rs`,
`docs/ref.md`, `docs/highlights-ref-sync.md`, `docs/highlights-create.md`)
and `bob-mac-capture` (`Sources/RefsCore/RefsCopy.swift`,
`Sources/BobMacCapture/Refs/RefsPanelModel.swift`,
`RefsKeyRouter.swift`, `RefsCopyCardView.swift`, `HighlightsTakeover.swift`,
`docs/refs.md`, `docs/keyboard.md`). No peer swarm report was opened.

## TL;DR recommendation

Do it, but narrower than proposed — and store the **projected** Markdown, not
the user's original file, in a hidden vault-synced sidecar.

1. **Source of truth:** at `bob ref create` time, persist the exact
   `projected.md` bytes that pandoc rendered (vault-note projection or
   external-`.md` file, after `-S` section filtering and Mermaid collection)
   as a hidden sidecar, e.g. `<vault>/.bob/ref-sources/<stem>.md`, with a
   SHA-256 recorded in the PDF marker and/or ref-note frontmatter. Dot-dir
   keeps it out of Obsidian and out of the `ref/` index (which already skips
   hidden dirs), while git still syncs it. This is the adjustment to "copy
   the markdown files to some nearby location": nearby-but-hidden beats
   beside-the-PDF, because `lib/**/*.md` would surface as junk notes in
   Obsidian.
2. **Contract (thin-client rule):** extend `bob ref show -f json` additively
   with a `code_blocks[]` array (`index`, `language`, `lines`,
   `preview_first_lines`, `content_hash`, `source` enum) plus
   `code_source: markdown | none | unavailable_stale`. Mac decodes with
   `decodeIfPresent`; an older `bob` yields the existing "needs newer bob"
   row, mirroring `marker_id unsupported`. No Swift-side Markdown parsing —
   per `decisions:mac-capture-is-a-thin-client`, `bob` owns extraction.
3. **Copy-card UX:** add one fixed key `C` ("Code…") in a new `code` group,
   mirroring the existing `H` highlight picker. `C` opens a code picker with
   the same 9-row window, arrows/wraparound, `A`-copies-all semantics
   (scoped to the picker), and HUD confirmations. Default payload is **raw
   code contents** (no fences); holding `Option` swaps to **fenced block with
   language tag**. Rows preview `language · N lines · first line`. When no
   Markdown source exists the `C` row is hidden and other keys do not move —
   the card's existing "rows that do not apply are hidden without moving the
   other keys" rule.
4. **Highlights `cmd+Y`:** add a `RefsHighlightsCopyKey` setting (default
   `cmd+Y`, `Off` available), implemented exactly like the existing
   `RefsHighlightsOpenKey` (`cmdO`/`ctrlO`/`off`) takeover: only while
   Highlights is frontmost, and stepping aside when the Refs panel is already
   visible. It opens Refs, selects the current PDF's ref via the existing
   `fileName` tab match, and opens the copy card with the code picker
   pre-opened. No match → panel opens library-focused with a HUD hint, never
   an error dialog.
5. **Backfill + lifecycle:** `bob ref scan` backfills missing sidecars only
   when it can do so deterministically (vault-note re-projection is *not*
   deterministic across days — mark those `unavailable_stale` instead of
   guessing); `bob ref rename` moves the sidecar as a companion (like audio);
   `reread --force` writes `<stem>__vN` sidecars; `overwrite` regenerates in
   place. Ship behind the additive JSON fields so old/new mixes degrade
   gracefully.

## 1. Current state

### 1.1 Copy card (`cmd+Y` in Refs)

- `docs/refs.md` §"Copy card" + `RefsCopy.swift`: fixed keys `I T W U L X
  D N O P F R S A H` plus `1–9` for visible commented highlights.
  `RefsCopyKey::parse` is the closed alphabet; free letters include `B C E
  G J K M Q V Y Z`, so `C` is available and mnemonic.
- Groups are `identity / sources / files / notes`. A `code` group slots in
  after `files`, before `notes`, without renumbering anything.
- `1–9` already means "visible commented highlights"; `A` means "all notes
  as Markdown"; `H` means "pick a highlight…". The picker pattern (windowed
  9 rows, arrows scroll, `A` copies all *within the picker*, `Esc` returns to
  the card) is the proven template for a second pickable collection.
- `Option` swaps every row to its alternate in place (`Option-W` titled
  wiki-link, `Option-P` absolute PDF path, `Option-1–9` quote-only). A
  raw-vs-fenced code alternate fits this muscle memory exactly.
- Rows preview the exact copied value; failed pasteboard writes keep the card
  open so `Return` retries; success hides Refs and shows a glass HUD. Any
  code row must obey the same contract.
- Capacity math (`RefsCopyCardLayout::noteCapacity`,
  `highlightWindowSize`, `RefsVisualTokens::copyCardMetrics`) already
  parametrizes window sizes — a code picker reuses it with a second capacity,
  it does not need new visual tokens.

### 1.2 Highlights takeover

- `HighlightsTakeover.swift` + `RefsHighlightsOpenKey` (`cmdO` default) +
  `RefsHighlightsTabsKey` (`cmdT` default): Carbon hotkeys registered only
  while Highlights (or the Settings override bundle) is frontmost;
  `cmdT` yields to the visible panel. Adding a third key follows ~30 lines
  of existing pattern, plus a Settings picker row and `HotKeyAction` case
  (`refsHighlightsCopy = 5`). The `off` option is load-bearing: if `cmd+Y`
  collides with a Highlights menu item on some version, Bryan can turn the
  takeover off and the global Refs hotkey still works.
- Matching "current PDF" already exists: the Open-PDF refresh flow matches
  `editor_saved_first` or open-tab `fileName` via the read-only
  Accessibility tab reader (`docs/refs.md` §"Open PDFs in Highlights"). The
  `cmd+Y`-from-Highlights path reuses that matcher; no new AX surface.

### 1.3 `bob ref create` Markdown → PDF pipeline

- Two Markdown routes (`create.rs` help text + `docs/highlights-create.md`):
  vault-note → projected reading snapshot (tasks condensed, `[?]` lanes,
  `-S` filtering, first-H1 title extraction) → `projected.md` in private
  `ScratchDir`; external `.md` → pandoc with
  `--resource-path=<source-parent>`. Both go through the same pandoc→LaTeX
  (`PANDOC_HEADER_INCLUDES` with `fvextra` `breaklines,breakanywhere`) →
  xelatex → stamp marker → file to `lib/<kind>/<stem>.pdf`.
- Today `projected.md` is **discarded** with the scratch dir unless
  `BOB_HIGHLIGHTS_KEEP_WORKDIR=1` (debug only). Only provenance survives:
  vault notes get `source_note: "[[route]]"` + `source_path` frontmatter and
  a `source_note` marker field; external `.md` files leave only
  `source_url`/filename heuristics. There is deliberately no durable copy of
  the rendered bytes.
- Companion precedent exists: `--audio` lands `<stem>.<ext>` beside the PDF
  before install, with reuse/force/refuse rules, and `rename` moves note +
  PDF + companions. A code-source sidecar wants the same lifecycle, not a
  new one.
- LaTeX uses `Highlighting`+`fvextra` wrapping and a `Code`-break Lua filter
  (`allowbreak` after `/ _ % - . : ,`). Good for print; fatal for
  copy-from-PDF fidelity (see §2).

## 2. Why PDF-direct extraction is the wrong source

Reading code out of the PDF (`pdftotext`, `pdfgrep`, Highlights selection)
fails exactly where code matters:

- **Wrapped lines are indistinguishable from real newlines.** `fvextra`
  `breaklines,breakanywhere` reflows long log/command lines to the page
  width. The PDF has no "soft wrap" marker; reconstructing the original line
  is guesswork. Copying a wrapped `kubectl`/`curl` line as two lines
  produces a broken command.
- **Ligatures, hyphenation, and glyph coverage.** `glyph_coverage`
  (`create.rs`) substitutes fonts per character; `---`/`--`/`"..."` and
  code ligatures (`->`, `!=`) may round-trip as typographic glyphs.
  Hyphenation is enabled for prose (`\hyphenpenalty=10000` mitigates but the
  LaTeX `Code` filter inserts `\allowbreak{}` at separators).
- **Page breaks and headers/footers.** A 60-line block spans pages with
  running heads and `↩ p. N` return pills interleaved; stitching drops or
  duplicates lines.
- **Mermaid and `listen` Divs render as figures**, not text — the PDF holds
  pixels where the Markdown held a fenced `mermaid` block. "Code blocks" in
  the PDF sense and "fenced blocks" in the Markdown sense already diverge.
- **Highlights selection is line-box based.** Multi-page drag selection in
  Highlights adds line breaks per visual row. Users report this as "copying
  code from a PDF never pastes clean" — the request itself concedes we can
  "probably only" serve Markdown-born refs.

Verdict: PDF parsing is a fallback at best (e.g. best-effort `pdftotext`
region for non-Markdown PDFs should explicitly *not* ship). The Markdown
sidecar is the reliable path, and keeping it is good practice anyway:
reproducible builds, audit ("what bytes produced page 4?"), and the narrate
(`-L`) path already passes `projected.md` as `{target}` — the file exists,
we just throw it away.

## 3. Sidecar design (the core adjustment)

### 3.1 What to store

Store the **projected Markdown** (post-snapshot, post-`-S`, post-Mermaid
collection, pre-pandoc), not the user's original file:

- For vault notes the original keeps changing; the PDF froze a dated
  projection (`<stem>_<YYMMDD>`). Copying today's note contents when the PDF
  shows last month's snapshot is a correctness bug. Projected bytes match
  the pages.
- For external `.md`, projected == file bytes (plus resource-path
  resolution), so nothing is lost.
- Mermaid ` ```mermaid ` fences: store as-is; the picker can label them
  `mermaid · figure on p. ~N` and copy the diagram source — genuinely useful,
  and impossible from the PDF.

Also store a small manifest alongside or in the PDF marker: `sha256`,
`fence_count`, `created_by_bob_version`. The copy UI can then say "source
matches this PDF" vs "stale".

### 3.2 Where to store

| Option | Upside | Downside | Verdict |
|---|---|---|---|
| Beside PDF as `<stem>.md` | Mirrors audio companion; trivial `rename` | Surfaces as a real note in Obsidian (`lib/` is in the vault); pollutes search/open-quick-switch; needs ignore rules on every client | Reject |
| Beside PDF as `<stem>.source.md` | Same tooling | Same Obsidian pollution, worse (two dots) | Reject |
| Inside ref-note frontmatter | Atomic with note; no extra file | Notes are already large; frontmatter parsers + `ref show` pay per-read cost; multi-KB code × many refs bloats the index | Reject |
| Embedded in PDF (XMP / embedded file) | Travels with the PDF | Requires PDF rewrite on backfill; Highlights coordination holds (§decisions) make writes expensive; extraction needs a PDF parser on the Mac | Reject |
| Hidden vault dir `.bob/ref-sources/<stem>.md` | Out of Obsidian index and `ref/` index (both skip dot-dirs, verified in `docs/ref.md` coverage + Obsidian exclusion history); git-synced like `.bob/themes`; one lookup rule | New directory; needs `rename`/`scan`/`doctor` awareness | **Adopt** |
| Re-derive on demand (re-project vault note / re-read `.md` path) | No storage | Non-deterministic (note edited since; external file moved); network for URLs; violates frozen-snapshot rule | Reject as primary; allow as explicit `ref scan --backfill` best-effort only |

Recommended path: `<vault>/.bob/ref-sources/<stem>.md` (byte-identical to
`projected.md`), lookup key = ref `id` (= PDF stem = note stem). Ref-note
frontmatter gains two scalar fields (`source_md: <relpath>`,
`source_md_sha256: <hex>`) so `ref show` and `doctor` can verify without
scanning the dir; `rename` rewrites both plus the file, exactly as it
rewrites `source_pdf` today.

Size: engineering notes with code are 20–200 KB projected; 500 such refs ≈
10–100 MB in git. Acceptable, but set a guardrail: sidecars over 1 MB still
stored (code books exist), picker previews truncated, `doctor` warns over
5 MB.

### 3.3 Lifecycle

- `create`: write sidecar after successful pandoc, before stamp+install, in
  the same transaction that installs PDF+note+task (one commit). `-k`
  (queued intake) writes the sidecar into `xlib/` next to the queued PDF;
  `scan -i` files it alongside.
- `scan`: backfills only when deterministic — external `.md` still present
  with matching mtime/hash, or `BOB_HIGHLIGHTS_KEEP_WORKDIR` artifact
  available. Vault-note snapshots are *never* re-projected silently;
  missing sidecar → `code_source: unavailable_stale` + `doctor` hint
  (`ref scan --backfill-md` for explicit best-effort).
- `rename`: move sidecar + rewrite `source_md` like `source_pdf` (already
  tested path for PDF+companions).
- `recapture reread`: new `<stem>__vN.md` sidecar (readings are independent).
- `recapture overwrite`: regenerate in place, move authored prose per
  existing `ref_history/` rule.
- `-o <exact path>`: sidecar goes to `.bob/ref-sources/<custom-stem>.md`
  keyed by the custom stem; no vault-note `-N` interaction.
- `sync`/`doctor`: verify `sha256`; report `source_md_missing`,
  `source_md_stale`, `source_md_oversize` diagnostics; never auto-delete a
  sidecar for a live ref.

## 4. UX design (intuitive, reliable, beautiful)

### 4.1 Entry points

| Entry | Behavior |
|---|---|
| Refs panel, `cmd+Y` on a row | Opens copy card exactly as today. New `C` row visible iff `code_blocks[]` non-empty. Focus stays on card; `C` opens the code picker. |
| Refs panel, `cmd+Y` with code picker pinned (proposed: `cmd+Y` twice, or `C` remembered per session) | Power users who live in code can set the card to open directly in code mode. Do not change the default: marker-ID/wiki-link default must not move (existing muscle memory). |
| Highlights, new `cmd+Y` | Opens Refs (or focuses it), selects the current PDF's ref, opens the copy card with code picker pre-opened when blocks exist; otherwise opens the card normally with a one-line HUD "No code blocks in this PDF's Markdown source". `Esc` ladder unchanged: picker → card → panel. |

Do **not** add code rows to the top-level card as `B1..B9`: digits are taken
by highlight notes and the card promises fixed keys. One mnemonic letter
(`C`) plus a picker preserves the card's spatial stability, which is the
whole point of fixed-letter design.

### 4.2 Picker rows

Each row: `[n] <language> · <L lines> · <first meaningful line truncated to
~60 cols>`; detail right-aligned `p. ~N` only when a cheap mapping exists
(see §4.4 — else omit page numbers rather than lie). Preview (help line)
shows the first ~5 lines verbatim, truncated with `… +M more`. Empty blocks
and `mermaid` blocks appear with honest labels (`empty`, `mermaid figure`);
whitespace-only blocks are hidden like uncommented quotes are.

Payloads:

- `Return` / click / digit: **raw contents**, exact bytes between the
  fences, trailing newline preserved, no language tag. Pasting into an
  editor or REPL just works.
- `Option-Return` / `Option`-digit / `Option`-click: **fenced block**
  (<code>```lang</code> … <code>```</code>) for pasting into Markdown/chat.
  Mirrors `Option-1–9` quote-only vs note-block duality.
- `A` in picker: all blocks joined by a blank line, raw; `Option-A`: all
  blocks fenced. Mirrors highlight picker's `A`.
- Announcements + HUD: "Copied Code 3 · python · 42 lines" /
  "Copied Code 3 fenced" / "Copied 7 code blocks". Same pasteboard-verify
  + retry-on-`Return` behavior as notes.

Search: the picker reuses the card's type-to-filter (match on language +
first line). With >9 blocks the window pages exactly like highlights
(`Ctrl-D` next page affordance already exists for notes; replicate the
`+N more` row).

### 4.3 What "no code" looks like

- PDF has no Markdown source (paper, arXiv, web article, scanned PDF): `C`
  row hidden; `hiddenReason` = "This PDF was not rendered from Markdown —
  code copy needs a Markdown source". Same tone as existing
  "No PDF path for this reference".
- Source missing/stale (old ref, pre-feature): row visible-but-disabled with
  tag `missing`, help "Source Markdown not saved for this reading — see
  `bob ref scan --backfill-md`". Never silently offer PDF-extracted text as
  code.
- Zero fenced blocks in source: row hidden; no empty picker.

### 4.4 Page numbers: approximate or absent

Pandoc→LaTeX pagination is not invertible without a sync map (SyncTeX is
not emitted for this pipeline and would be fragile across xelatex runs).
Do not block the feature on page mapping. Ship v1 with **ordinal labels**
(`Code 1/2/3…` in document order) and optional `≈p. N` only if a cheap
heuristic clears a bar (e.g. `ref show` already emits per-section `pages`
for highlights — reuse section→page when the block's section is known,
prefix with `≈`). A wrong page number is worse than none.

### 4.5 Beauty notes (fit the existing card, don't restyle it)

- Reuse `RefsCopyKeycap` glyph `C`, `copyCardRowHeight` /
  `copyCardPickerRowHeight`, group separators, `~`-abbreviated paths, and
  the glass HUD. No new colors, fonts, or corner radii.
- Language tags lowercase, monospaced where the card already uses mono for
  previews; keep the `Comment:`/`— provenance` idiom out of code payloads
  (code must paste clean — no provenance line appended).
- Accessibility: same `Announcement("Copy menu…")` + per-row labels as note
  rows; code preview exposed as `accessibilityValue` so VoiceOver reads the
  first line, not 200 lines.

## 5. Highlights `cmd+Y` details and conflicts

- Default `cmd+Y`, options `ctrl+Y`?/`off`, in Settings › References next to
  the Open/Tabs pickers. Implementation = third `HotKeyConfiguration` +
  `HotKeyAction.refsHighlightsCopy` + `HighlightsTakeover.sync` third leg.
  When the Refs panel is visible the takeover steps aside (same
  `yieldsToVisiblePanel` rule as `cmdT`) so `cmd+Y` inside the panel keeps
  meaning "copy card".
- Conflict check: Highlights' menu bar today uses `cmdO` (Open),
  `cmdT`? (new tab behavior varies by version) — `cmdY` is unclaimed in the
  versions Bryan runs (verify on the Mac at implementation time; the `off`
  setting + `doctor` hotkey-conflict surfacing already handle a future
  Highlights update that claims it). This mirrors how `cmdO` was chosen over
  stealing Open.
- "Current PDF" resolution: reuse `AXHighlightsTabsReader` fileName match;
  ties (same file open twice) → frontmost tab wins, same rule as refresh
  toasts. If Accessibility is untrusted or Highlights isn't running, the
  hotkey opens Refs library-focused — never prompts for permission inline
  (the Tabs filter's `needsPermission` row already teaches that flow).
- After opening: `selectedID := matchedRef`, `openCopyCard(preopen: .code
  if blocks else .none)`. If the PDF is an intake-queued file with no ref
  note yet, select nothing and show the existing scan-receipt affordance.

## 6. Critique — is this a good idea? What would I change?

**Yes, with the scope above.** Copying code out of rendered PDFs is a real,
daily papercut for Markdown-born engineering refs, and the copy card is the
right home: it already solves discovery (which ref), payload choice
(raw vs fenced), and paste verification. Storing `projected.md` also pays
for itself in reproducibility and debugging.

Adjustments to the proposal as written:

1. **Store projected Markdown, not the input file.** The request says "copy
   the markdown files we used to generate the PDFs to some nearby location".
   The input file drifts (vault note) or disappears (temp download); the
   projection is what the PDF shows. Store that.
2. **Hidden sidecar, not "nearby".** Beside-the-PDF `.md` pollutes Obsidian.
   `.bob/ref-sources/` is nearby (same vault, same git sync) without
   polluting search. Call this out explicitly — it is the largest deviation,
   and it is justified by the Obsidian-index evidence above.
3. **Limit to Markdown-born refs in v1 — loudly.** The request hedges
   ("probably only…", "unless we can read the PDF directly"). Decide: no PDF
   parsing in v1. A degraded "best effort PDF text" mode would ship
   corruption as a feature and erode trust in the card's "previews the exact
   value it copies" promise.
4. **Do not copy code *blocks* from Highlights annotations.** Highlights
   underlines/highlights are prose quotes; code inside a highlight
   annotation stays an annotation (existing `H` picker). The new picker is
   source-document code only. Mixing the two would confuse "what I
   highlighted" with "what the doc contains".
5. **Keymap choice: `C`, not `Y`, inside the card.** `cmd+Y` opens the card;
   `Y` inside the card is unbound and would be a second way to say "copy".
   `C` (code) parallels `H` (highlight picker) and keeps the card's alphabet
   pronounceable.
6. **Considered alternative — "Open source in Obsidian and copy there":**
   zero new code (the `O` Obsidian link already exists; vault-note sources
   open directly). Rejected as primary because (a) external-`.md` sources
   have no vault note, (b) the projection differs from the live note, and
   (c) context-switching out of Highlights/Refs breaks the "stay in flow"
   goal. Keep it as the documented fallback.
7. **Considered alternative — clipboard via `bob ref show --code N`:** ship
   the CLI (`bob ref show <ref> --code 3 [--fenced] -f json|raw`) regardless
   — the Mac is a thin client, so the endpoint must exist anyway, and
   terminal users get the feature for free. But CLI alone fails the
   "beautiful" bar; the card is the product.

Non-goals for v1: editing code in the picker, executing it, images of code,
OCR of figures, or syncing *back* edits to the sidecar. The sidecar is
read-only after create (except lifecycle moves).

## 7. Implementation sketch (phased, thin-client order)

- **Phase 0 — contract:** `bob ref show -f json`: add `code_source`,
  `code_blocks[]` (cap content at, say, 256 KB per block in JSON; CLI
  `--code N --raw` streams full bytes to stdout for huge blocks).
  `schema_version` stays `1` (additive). `bob ref show --code --fenced`
  human output for scripts.
- **Phase 1 — persistence:** `create` writes `.bob/ref-sources/<stem>.md` +
  frontmatter `source_md{,_sha256}`; `rename`/`scan`/`recapture`/`doctor`
  handle it; `scan --backfill-md` best-effort importer; `docs/` updated
  (`highlights-create.md`, `highlights-ref-sync.md` JSON section).
- **Phase 2 — Mac card:** `RefsCopyKey.code`, `RefsCopyGroup.code`,
  `RefsCopyCatalog` code section + `RefsCodePicker` state reusing
  `highlightWindowSize`/metrics; `RefsCopyCardView` code rows; HUD +
  announcements; design tests mirroring `RefsCopyCardDesignTests`.
- **Phase 3 — Highlights key:** `RefsHighlightsCopyKey`,
  `HotKeyAction.refsHighlightsCopy`, takeover wiring, Settings UI, conflict
  surfacing; Tabs-reader match → `openCopyCard(preopen: .code)`.
- **Acceptance:** goldens for fenced/tilde/info-string edge cases
  (unclosed fence, fence inside `markdown` example block — cf.
  `diagrams.rs` over-match notes), CRLF, BOM, 4-space indented blocks
  (pandoc treats as code — include), large-block truncation, empty/mermaid
  labels, rename/reread/overwrite round-trips, old-`bob` fallback row, and
  the no-source states. Mac side: `portable-check` + Mac `typecheck-tests`
  per that repo's `AGENTS.md`.

## 8. Open questions for Bryan (answer before build)

1. Confirm hidden `.bob/ref-sources/` over beside-the-PDF `.md` (my
   recommendation)? The tradeoff is Obsidian pollution vs one new hidden
   dir.
2. Raw-by-default vs fenced-by-default for `Return`? I recommend raw (paste
   into editor) with `Option` for fenced, mirroring quote-only alternates —
   veto if you paste into Markdown more often.
3. Should `A` in the code picker copy all blocks, or is that a footgun for
   50-block docs (huge pasteboard)? Cap + confirm, or drop `A` in v1?
