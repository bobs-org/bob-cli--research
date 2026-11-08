# Cmd+Enter page-jump from ref-note quotes/annotations → Highlights

Researcher: mus · 2026-11-08 · bob-cli + bob-plugins (linked checkout)

Request: extend the existing `<cmd+enter>` "open corresponding PDF in Highlights"
keymap — today it works when a **ref task** is selected — so it also works when a
**quote/annotation in a ref note** is selected (the blocks that annotation-created
tasks link to via `#task`-in-annotation `[[#^h-…|🔖]]` links), jumping to the
appropriate page; make the keymap's availability discoverable the same way it is
for ref tasks; show an explanatory Obsidian toast on each jump. Lead the design:
intuitive, reliable, beautiful. Critique the plan, adjust requirements where
justified, end with a recommended solution.

## TL;DR

- **Yes, build it — with adjustments.** Quote→page jumping is the highest-value
  gap in the current Highlights handoff: today every jump lands at the PDF's
  last position, so verifying a quote or working a `#task`-from-annotation in a
  long PDF means re-finding the passage by hand.
- **Mechanism: open a `highlights://<abs-path>#page=N` URL first, fall back to
  the current file-open when the page is unknown or the URL handoff fails.**
  The URL scheme is Highlights' own documented backend for page links
  (`highlights://Users/test.pdf#page=3`,
  [Version 1.2 changelog](https://highlightsapp.net/changelog/2015/01/03/Version-1.2/);
  fetched 2026-11-08). AppleScript is not an option
  ([FAQ: "Is Highlights scriptable? No, not yet."](https://highlightsapp.net/faq/)).
- **Biggest requirements adjustment: there is no editor affordance to copy.**
  I verified the plugin sources — no status-bar, gutter, or decoration signals
  Highlights availability on ref-task lines today (only docs plus the Reading
  Board's PDF button). So "do the same thing as ref tasks" must be read as
  "design one affordance and apply it to **both** contexts." I recommend a small
  status-bar + gutter affordance, macOS/desktop only, zero vault writes.
- **Recommended build is plugin-only (no `bob-cli` change, no resync churn),
  with an optional Phase 2** that replaces heading-parsing with recorded data
  (`bob ref show -f json` already returns per-block `page_label`; a future
  `bob ref locate` or embedded anchor would remove parser duplication).

## 1. Current state (verified in this session)

### 1.1 The existing keymap

- Command `bob-navigation-hotkeys:open-reference-pdf-in-highlights`
  ("Open reference PDF in Highlights (or link in new tab)") is registered with
  **no default hotkey** in
  `plugins/bob-navigation-hotkeys/src/490-plugin-lifecycle.js:83-89`.
  The vault binds it to `Meta+Enter` in `~/.obsidian/hotkeys.json` (verified:
  `"bob-navigation-hotkeys:open-reference-pdf-in-highlights": [{"modifiers":
  ["Meta"], "key": "Enter"}]`). Docs explicitly warn not to re-record it as
  `Mod` (`docs/highlights.md:19-25`,
  `docs/bob-navigation-hotkeys.md:623-640`): a registered default would lose to
  Obsidian's built-in `Mod+Enter`; the custom vault binding runs first and the
  plugin delegates to `editor:open-link-in-new-leaf` for non-reading targets.
- Handler `openReferencePdfInHighlightsOrLink()` + resolver live in
  `plugins/bob-navigation-hotkeys/src/677-plugin-ref-pdf-open.js`. Verified
  behavior:
  - Source-mode only (`getMode() !== "source"` → delegate). In current Obsidian
    Live Preview reports `"source"`, so Source + Live Preview are covered;
    Reading view delegates.
  - Cursor must be editor-focused (`.cm-editor` containment check).
  - Recognizes: `#task #ref` reading-task lines (any lane mark, any `#REF`
    casing), dedicated Task Links / managed embeds / struck / 🍅-prefixed links
    that resolve to a reading task (`parseRefPdfBlockLinkLine`), v1 direct-PDF
    links, and own-note `source_pdf` fallback.
  - PDF resolution order per line: wikilink-to-PDF → linked managed-ref-note's
    `source_pdf` → legacy-ref error → own-note `source_pdf` → "Reading task
    links no reference PDF".
  - Opener `openReferencePdfPath()`: validates `source_pdf` (no `..`, no
    absolute, `.pdf` only), checks existence via vault adapter, requires desktop
    base path + macOS (`Highlights is macOS-only`), then
    `/usr/bin/open -b net.highlightsapp.universal <abs>` with `-a Highlights`
    retry. **No vault writes on any path** (harness asserts `replaceRange`,
    `modify`, `process` throw).
  - Toasts today: `Opened <file> in Highlights` / `Reference PDF not found:` /
    `Unsafe source_pdf:` / `… has no source_pdf (legacy reference)` /
    `Reading task links no reference PDF` / `Highlights is macOS-only:` /
    `Could not open …`. Delegation is silent (one `executeCommandById`).
- Additive API `api.openReferencePdf(path)` (`src/480-…-nav-api.js:905-945`,
  `version` unchanged at 3) lets the Reading Board hand a PDF to Highlights;
  the Board gates its PDF button on macOS + API presence
  (`244-plugin-reading-board-block.js:60-64`, `readingBoardOpenPdf`). This is
  the closest thing to an "affordance" anywhere in the product.
- Coverage: `scripts/test-navigation-hotkeys-ref-pdf.cjs` (13 tests: lanes,
  Task-Link forms, embeds, delegation cases, unsafe paths, retry, off-macOS,
  api). Any extension should grow this harness, not invent a new one.

### 1.2 What a quote/annotation block looks like (verified)

Rendered ref note (vault example via `bob ref show … -f markdown/json`,
frontmatter `source_pdf: lib/papers/….pdf`, managed region
`<!-- highlights:begin -->…<!-- highlights:end -->`):

```md
### Page 1

> [!quote] We define goals broadly as desired outcomes …

> > [!note] Comment “at any altitude”!

^h-04d5acf4e72f

### Page 2
…
```

Key facts for the design:

- Page headings are **H3** (`### Page N`) in unsectioned regions; in
  **sectioned** regions (card signature `[!summary|section]` + `^s-<id>`) the
  H3s are section titles and page captions drop to **H4** (`#### Page N`),
  resetting at every H3 (`src/native/highlights_ref/region.rs:100-169`). A
  naive "nearest `### Page`" scan breaks on sectioned notes — the resolver must
  mirror this rule.
- Block ids are `^h-<hex>` lines (`region_block_id`, `is_valid_block_id`).
  Grouped multi-page highlights render one block with a caption like
  `> [!quote|Pages 11–12]`; the block's page label is the range
  (`sidecar_render.rs:594-604`, `group_page_label`). Jump target = **first**
  page of the range.
- Annotation-created tasks render as
  `- [ ] <text> [[#^h-abc123|🔖]] [h:: <processed_id>] [created::DATE]`
  (same-note) or `[[ref/papers/note#^h-abc123|🔖]]` (routed)
  (`annotation_tasks.rs:329-365`, `SOURCE_LINK_ALIAS = "🔖"`). Live vault
  example: `- Goals should be used to maintain an agent ChangeLog!
  [[ref/papers/…#^h-3b3e9bd6eb64|🔖]] [h:: 450bd…] [created::2026-10-13]`.
  These lines are **not** `#ref` reading tasks, so today's resolver delegates
  on them — that is the gap, alongside bare quote blocks.
- `bob ref show <REF> -f json` (run this session) already returns per
  annotation `{page_label, kind, quote, comment, block_id, link}` plus
  `source_pdf`. Example: `{"page_label":"Page 1","block_id":"h-ec921544b3b2",…}`.
  The data the plugin needs exists in recorded form; the only question is
  whether the plugin parses fast local markdown or shells to the CLI ( §5 ).

## 2. Page-jump mechanism

| Option | Verdict |
|---|---|
| `highlights://<abs>#page=N` via `/usr/bin/open` | **Use (primary).** Documented scheme, page-accurate, no new deps, same `child_process` path as today. |
| `open -b … <file>` (status quo) | **Keep as fallback** when page unknown / URL handoff fails. Never regress to worse than today. |
| AppleScript / direct scripting | Reject. Officially unsupported. |
| Obsidian's built-in PDF viewer at page | Reject for this keymap. Highlights owns the annotation truth; splitting viewers confuses the "where do I verify this quote" mental model. A viewer fallback is fine only where Highlights is unavailable (non-macOS), and that should be a notice, not a silent redirect. |
| Copy link instead of jumping | Reject as default; acceptable as a *secondary* affordance at most (e.g. keep clipboard untouched — jumping is the request). |

Construction details (must be nailed in implementation, verified on a Mac):

1. `highlights://` + absolute path minus leading `/` + `#page=N`, e.g.
   `/Users/bryan/bob/lib/papers/x.pdf`, page 3 →
   `highlights://Users/bryan/bryan/bob/lib/papers/x.pdf#page=3` (per the
   documented `highlights://Users/test.pdf#page=3` shape). Percent-encode
   spaces/unicode (`%20`, UTF-8); keep `/` separators literal.
2. Launch with `/usr/bin/open "<url>"` (no `-b`/`-a` — the scheme routes to
   Highlights). Keep the existing two-attempt file-open as the fallback chain:
   URL → bundle file-open → named file-open → `Could not open …` notice.
3. The one semantic risk to verify on-device: whether `#page=N` means
   **PDF-index page** or **printed label page**. Highlights' own export
   headings conflate the two for most papers but not for front-matter /
   roman-numeral books. Sidecar parsing keeps both a `page_label` and an
   optional explicit `page_index` from the `#page=N` fragment
   (`sidecar_render.rs:2654-2683`); linked-style exports carry the explicit
   index, simple `## Page N` exports fall back to the label number, and ranges
   (`Pages 11–12`, `pp. 11–12`) have **no** single index — first-number is the
   sane jump. Acceptance testing must include one roman-numeral-front-matter
   PDF; if label≠index there, document "jumps to PDF page N" and consider
   Phase 2's recorded `page_index`.

## 3. Cursor-context resolution (the core design)

Keep today's task/Task-Link/embed paths byte-for-byte, then add quote contexts
in one resolver. Precedence for the cursor line (first match wins):

1. **Reading task / Task Link / embed** → today's path (file open; page jump
   not attempted — a reading task names a whole paper, and guessing a page
   would be wrong).
2. **Annotation-task line** (`[[#^h-…|…]]` or `[[ref/…#^h-…|…]]` + `[h:: …]`):
   extract the block id + target note, load that note's text
   (`cachedRead`-style, same helper family as today's link resolution), find
   the `^h-…` line, take the enclosing block's page (rule §3.1). Same-note and
   routed forms both supported.
3. **Inside the managed region** (`highlights:begin/end`): enclosing block =
   nearest `^h-…` line at/after the cursor's quote group (scan down ≤ ~15 lines
   for the block terminator, else scan up for the previous terminator and take
   the next block). Page = nearest preceding page caption above the block
   start. Cursor directly on a page-caption line → that caption's page.
   Cursor on `^h-…` line itself → its own block's page.
4. **Preamble blocks** (before the first page caption): page unknown → file
   open with the existing `Opened <file> in Highlights` toast (no fake page).
5. **`### Removed highlights` subtree / `^h-` tombstones / `unparsed`**: refuse
   with a notice (`No page for removed highlight — opened nothing` or fall
   back to file open? I recommend **refuse, don't open**: opening a stale page
   for a deleted annotation is a lie. Call this out in docs.)
6. **Anything else** → today's silent delegation (never steal the key).

### 3.1 Page-caption rule (mirror `region.rs`, don't invent)

- Determine sectioned-ness: region contains a `[!summary|section]` depth-1
  callout followed by a `^s-` line. If sectioned → captions are `#### …`
  (any H4 that matches a page label), H3s ignored except as resets. If not →
  captions are `### …` H3 (excluding `Removed highlights`, case-insensitive).
- Label → number: `Page N` / `Page: N` / `p. N` / `p N` (case-insensitive,
  `label_page_number`); ranges `Pages A–B` / `pp. A–B` → **A**. If no integer
  parses (custom labels, section titles) → page unknown → file-open fallback.
- Grouped `[!quote|Pages 11–12]` headers corroborate but do not override the
  caption; caption wins.

## 4. Affordance ("make it clear when the keymap is available")

**Finding: there is nothing to copy.** I searched the nav-hotkeys sources for
`statusBar`, gutter, decoration, hover, and hint paths tied to Highlights:
zero editor affordances. Availability is communicated only by docs
(`docs/highlights.md`, `bob-navigation-hotkeys.md:613-614`) and, outside the
editor, the Reading Board's conditional PDF button. So the request's parenthetical
rests on a false memory — worth telling Bryan plainly — and the real task is:
*design one affordance, apply it identically to ref-task lines and quote blocks.*

Recommendation (minimal, beautiful, cheap):

- **Status-bar segment** (desktop only): when the cursor rests on a resolvable
  line (reading task today; quote/annotation-task/page-caption after this
  change) and the vault is on macOS, show `📖 ⌘↵ p. N` (or `📖 ⌘↵` when the
  page is unknown / reading-task scope). Hidden otherwise (non-macOS, unresolvable
  lines, non-markdown views). Clicking it fires the same command. This is one
  small pill, no modal chrome, and it teaches the key without nagging.
- **Gutter tick** (Source/Live Preview, same predicate): a faint book-mark dot
  in the theme's accent at resolvable lines via a CodeMirror 6 decoration in
  the existing `676-plugin-open-notes-uri.js` decoration pattern. No text
  inserted, no vault writes, no layout shift.
- Explicitly **not**: hover popups (noisy over quotes), auto-toasts on cursor
  move (spam), rewriting line text (vault writes violate the
  `open-pdf-writes-are-coordinated` decision and the handler's never-write
  invariant), or a registered default hotkey (loses to `Mod+Enter`).

Both surfaces share one `isHighlightsResolvable(line, note)` predicate with the
jump resolver so affordance and action can never disagree — the classic
beautiful-reliable pairing.

## 5. Toast design

Keep Obsidian `Notice` (transient, ~4s, existing import) with page-aware text:

- Page jump success: `Opened <basename> · p. <N> in Highlights`
  (range blocks: `Opened <basename> · pp. <label> (p. <N>) in Highlights` —
  or simply `p. <N>`; decide in polish, keep the filename first).
- Fallbacks keep today's exact strings (`Opened <basename> in Highlights`)
  so existing muscle memory and tests don't churn: preamble, reading tasks,
  page-unknown.
- Failures keep today's exact error strings; add one: `No page for removed
  highlight` (refuse path) and reuse `Reference PDF not found:` /
  `Highlights is macOS-only:` unchanged.
- Never toast on delegation (non-contexts stay silent — a toast on every
  `Cmd+Enter` in prose would be anti-beautiful).

## 6. Reliability notes

- **Never-write invariant** extends to the new paths: heading scans and
  cross-note reads use cached reads only; the harness's throwing
  `replaceRange`/`modify`/`process` stubs must cover quote contexts too.
- **Keybinding layering untouched**: no `hotkeys:` default; vault
  `Meta+Enter` stays; delegation preserves built-in behavior everywhere the
  predicate is false, including Reading view, canvas, and non-`ref/` notes
  (annotation-task links can live outside `ref/` — resolve cross-note, don't
  gate the *cursor* note to `ref/`).
- **Stale-edit guard**: re-read the note text at invocation (today's code reads
  `editor.getValue()` fresh — keep that; don't cache page maps across edits).
- **Performance**: heading scan is O(lines above cursor), bounded; no
  subprocess on the hot path. Do **not** shell to `bob ref show` per keypress
  in Phase 1 (spawn latency on every `⌘↵`); Phase 2 can add it as a
  *fallback* when the heading scan yields no page (bounded `timeout`, failure
  → file open), or better, a purpose-built `bob ref locate <note> <block>`
  that answers in ms from the same parser the JSON already uses.
- **Tension to record**: `code-copy-reads-render-time-catalog` says clients
  "never … re-parse Markdown at read time" (for code/anchors). Heading
  scanning technically re-parses markdown at read time — but for page captions,
  not code, and the recorded alternative (JSON/anchor) is Phase 2 precisely
  because it needs a CLI/render change. Name the tension in the plan; Phase 1
  accepts it narrowly, Phase 2 resolves it.

## 7. Critique: is this a good idea? What would I change?

**Yes — with five adjustments (all marked [ADJUSTMENT]):**

1. [ADJUSTMENT] **Jump to page via URL scheme, not just file open.** The bare
   request ("jump to the appropriate page") already implies this, but pin the
   mechanism: URL first, file fallback. File-only would ship motion without
   progress.
2. [ADJUSTMENT] **Scope to Source + Live Preview cursor lines; Reading view
   delegates.** "Selected" in Reading view has no cursor line to resolve; a
   click-handler there is a separate feature with its own hit-testing. Don't
   let it block the cursor feature.
3. [ADJUSTMENT] **Removed-highlight cursor refuses with a notice; preamble
   falls back to file open.** Both are edge contexts the request doesn't
   mention; silently page-jumping either would be a reliability lie.
4. [ADJUSTMENT] **Build the missing affordance once for both contexts**
   (status-bar + gutter, §4) instead of "doing the same thing as ref tasks,"
   which doesn't exist. Also update `docs/highlights.md` (add quote contexts +
   page semantics + toasts) and the nav-hotkeys facts line that currently
   promises only "opens its source_pdf".
5. [ADJUSTMENT] **Different default for annotation-task lines outside `ref/`:**
   resolve cross-note (don't require the cursor note to be a reference note).
   Follow-up tasks live in area/project/daily notes; gating to `ref/` would
   strand the feature where it's most used.

What I'd **not** do: a separate keymap for quotes (one key, one mental model);
a picker/confirmation step (kills flow — the toast *is* the confirmation);
auto-opening on navigation (aggressive, breaks reading flow); writing page
anchors into notes at jump time (write amplification for a read gesture).

## 8. Recommended solution (build order)

**Phase 1 — plugin-only (ship this):**

1. Extend `677-plugin-ref-pdf-open.js` resolver with §3 precedence
   (annotation-task links → managed-region blocks → page captions), reusing
   `resolveReferencePdfFromTaskLine` for `source_pdf`.
2. Add `buildHighlightsPageUrl(absPath, page)` + URL-first launch with
   file-open fallback; page-aware toasts (§5).
3. Add shared predicate → status-bar pill + gutter tick (§4), macOS/desktop
   gated, zero writes.
4. Extend `test-navigation-hotkeys-ref-pdf.cjs`: quote/comment/block-id lines,
   page-caption lines, ranges (first-page), preamble fallback, removed-refuse,
   sectioned H4 captions, routed `[[ref/…#^h-…]]` tasks, delegation
   non-regression. Docs: `highlights.md` + nav-hotkeys facts/commands lines.
5. Acceptance on a Mac: roman-numeral-front-matter PDF (label-vs-index check),
   spaces-in-filename PDF (encoding check), legacy ref, missing PDF, off-macOS,
   Reading-view delegation, `Meta+Enter` vs built-in `Mod+Enter` coexistence.

**Phase 2 — recorded truth (only if Phase 1's heading scan proves brittle):**

- `bob ref locate <note> <block-id>` → `{source_pdf, page_index, page_label}`
  from the same Rust parser that feeds `ref show -f json` (which already emits
  both fields — verified this session), or an invisible render-time anchor per
  block. Plugin prefers recorded data, keeps heading scan as offline fallback.
  No resync churn in Phase 1 either way.

## 9. Open questions for Bryan

1. Page semantics: PDF-index page vs printed label — ok to define jump target
   as "PDF page N (what Highlights' `#page=N` means)" and note book
   front-matter may differ from printed numerals?
2. Removed-highlight cursor: refuse-with-notice (my recommendation) or silent
   file-open fallback?
3. Reading-view click support: explicitly out of scope for v1, or do you want
   click-to-page in Reading view specced now?

## Evidence & sources

- Plugin: `sase/repos/linked/bob-plugins/plugins/bob-navigation-hotkeys/src/677-plugin-ref-pdf-open.js`
  (full read), `src/490-plugin-lifecycle.js:83-89`, `src/480-review-jump-and-nav-api.js:905-945`,
  `src/244-plugin-reading-board-block.js:60-64,584`, `docs/highlights.md`,
  `docs/bob-navigation-hotkeys.md:613-640`, harness
  `scripts/test-navigation-hotkeys-ref-pdf.cjs`, vault binding
  `~/bob/.obsidian/hotkeys.json` (`Meta+Enter`).
- CLI/render: `src/native/highlights_ref/annotation_tasks.rs:329-365`
  (task-line format, `🔖` alias), `mod.rs:188,210-231` (constants),
  `region.rs:100-169,463-480` (H3/H4 + section rule, `^h-` ids),
  `sidecar_render.rs:2654-2730` (label/index parsing, ranges),
  `sidecar_render.rs:594-604` (group captions), live `bob ref show -f json`
  output (per-block `page_label` + `block_id`, verified 2026-11-08).
- Highlights: URL scheme + `#page=` shape via
  [Version 1.2 changelog](https://highlightsapp.net/changelog/2015/01/03/Version-1.2/);
  scriptability via [FAQ](https://highlightsapp.net/faq/) ("No, not yet").
- Memory consulted: `open-pdf-writes-are-coordinated` and
  `code-copy-reads-render-time-catalog` decision descriptors from project
  instructions (bodies not re-read; relevance flagged in §6). No peer reports
  consulted; no vault writes performed (read-only `bob ref show`, skill use
  logged per `bob_ref` skill).
