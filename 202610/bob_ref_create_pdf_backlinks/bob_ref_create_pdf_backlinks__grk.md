# Return tickets for `bob ref create` PDFs

- **Researcher:** grk
- **Date:** 2026-10-07
- **Question:** How should `bob ref create` add in-document backlinks so a reader who follows a local Markdown link in the rendered PDF can jump back to where they came from? The sketched plan is: find local links, resolve their destinations, stamp a unique alphanumeric ID onto the rendered link text, and plant a matching reverse link at the destination. Critique that plan, adjust requirements that need adjusting, and recommend a design that is intuitive, reliable, and beautiful.
- **Verdict:** The *goal* is right. The *mechanism* is not. Do not splice IDs into the author's link text. Do not invent opaque alphanumeric tokens as the default visual. Do not mutate the Markdown source. Instrument the pandoc Lua filter that `create` already runs, plant ISO-standard reverse `/GoTo` named destinations, and render Wikipedia-style return pills at the destination — unlabeled `↩` when there is one inbound prose link, lettered `↩ a b` when there are several. Skip generated and author-written tables of contents. Hide the pills from copy/extract so Highlights sidecars stay clean.

---

## 1. In one breath

`bob ref create report.md` already produces a hyperlinked PDF. Pandoc 3.1.11.1 + XeLaTeX + `hyperref` (the stack in `src/native/highlights_ref/create.rs::render_temp_pdf`) turns `[Findings](#findings)` into a PDF Link annotation whose action is `/S /GoTo /D (subsection.1.1)`. Headings already have named destinations and outline bookmarks. `colorlinks=true`, `--toc`, `--toc-depth=3`, and `--number-sections` are on. The outbound jump works today.

What is missing is a *document-level* way back. PDF history lives in the viewer, not in the file. ISO 32000-1 §12.6.4.11 only requires four named actions (`NextPage`, `PrevPage`, `FirstPage`, `LastPage`). Acrobat's `GoBack` is explicitly non-portable: "any document using them is not portable" and an unrecognized named action "shall take no action." Firefox's PDF.js still does not implement `GoBack` as of May 2026 (mozilla/pdf.js#21239).

Highlights, the actual reader, is a better situation than the spec. Version 1.5 (March 2016) added "back and forward buttons." Version 1.2 made in-PDF links clickable; later releases kept fixing "inactive page links" and "navigating PDFs using internal links." Apple PDFKit exposes both `PDFView.goBack()` / `canGoBack` and `PDFActionNamedName.goBack`. So the Mac toolbar may already restore the previous view after a tap. That is worth proving on the MacBook in thirty minutes before we sprinkle chrome on every heading.

Even if toolbar-back works on the Mac, an in-document return still earns its keep: iPad chrome hides, same-page jumps may not push history, and a pill sitting on the heading the reader just landed on is the affordance they can see without hunting a toolbar. The motivating corpus is the research reports `create` is for. A sample of 32 notes under this sidecar's `202610/` contains **356** `[text](#anchor)` links (about 20–33 per long report). Those are prose cross-references like `[Identity matching](#identity-is-messy)`, exactly the "jump away, want to come back" gesture.

The user's ID-in-the-link-text sketch is a first draft of Wikipedia footnote backrefs. Wikipedia got the pairing right and the placement right. Splicing the token *into the link phrase* is the part to drop.

```
today                 recommended

See Findings.         See Findings.
      |                     |
      v                     v
1.1 Findings          1.1 Findings              [↩]
                      (pill jumps to the "See Findings" line)
```

---

## 2. Critique of the plan

The plan as stated: search the Markdown for local links, figure out the destination, add a unique alphanumeric ID to the rendered local link text, and add a new local link at the destination whose visible text is that same ID and whose target is the original link.

### What is right

- **The job is round-trip navigation, not prettier underlines.** Outbound local links already exist in the PDF. The missing object is a return that does not depend on the reader noticing Highlights' Go menu.
- **Pairing both ends of a jump with a shared token is a real pattern.** Wikipedia footnotes do this: a superscript in the prose, a `^` / `a b c` cluster at the note ([Help:Footnotes](https://en.wikipedia.org/wiki/Help:Footnotes)). `hyperref`'s `backref` / `pagebackref` and `biblatex`'s `backref=true` do the bibliography version of the same idea. Heiko Oberdiek's standard answer on TeX.SE is "the viewer has GoBack, and if you must encode a return, plant an explicit destination at the origin."
- **Do this at render time, in the existing Lua filter.** `create` already writes `PANDOC_CODE_BREAK_FILTER` into scratch and passes `--lua-filter`. Listen-cards, relative-link stripping, and inline-code breaking already live there. A second pass over the pandoc AST is the right layer. Regex over the `.md` file will smash fenced code, nested brackets, and images.
- **Unique per *occurrence*, not per destination.** Two prose links to `#findings` are two different places to return to. Wikipedia's `a b c` exists for this. A single "back to Findings" button cannot name the origin.

### What is wrong or incomplete

1. **Splicing the ID into the rendered link text is the ugly part, and it is also the buggy part.** `[Identity matching](#identity-is-messy)` should still read "Identity matching" in the PDF. Turning it into "Identity matching 3k" fights the sentence, collides with section numbers (`--number-sections` is already on), and looks like a defect. The ID belongs *beside* the link as chrome, or only at the destination.

2. **Those IDs will leak into Highlights sidecars.** Bob's reading loop is: annotate in Highlights → sidecar text → `bob ref scan` → `ref/` quote blocks. Injected `3k` / `a1` glyphs ride in the content stream. A highlight over "see Identity matching 3k" becomes a bad quote. Prior clip research already treated sidecar text quality as a hard constraint (Skia/Quartz letter-spacing was rejected for that reason). Any visible ticket must be wrapped in `/ActualText` (LaTeX `accsupp`, installed on this host at `accsupp.sty`) and verified with a real sidecar. If Highlights ignores ActualText, the tickets have to become non-text (vector pills) or they do not ship.

3. **Do not rewrite the Markdown source.** A unique ID in the `.md` would pollute the vault, churn git, and break wikilink-sensitive tooling. The PDF is a derived artifact. The filter sees the AST; the source file stays byte-identical.

4. **Opaque alphanumeric IDs (`3k`, `7m`, truncated hashes) are worse than sequential letters.** They look like error codes. They do not sort. They do not scan. Wikipedia uses `a b c`. One-to-one jumps need no ID at all, only `↩`. Content-addressed IDs are for *stable citations across re-renders*; these PDFs are one-shot reading copies. Sequential letters assigned in document order are the right default. Call the hash scheme out as a rejected alternative.

5. **Tables of contents will drown the feature.** Pandoc's generated TOC (`--toc`) is not in the AST, so a Lua `Link` walker will not see it — good. Author-written TOCs *are* in the AST. `docs/randomize.md` and `docs/highlights-ref-sync.md` open with a bullet list of `[Usage](#usage)` links. If every one of those grows a return ticket, every heading in the PDF grows a matching reverse link. The outline bookmarks and Highlights' sidebar TOC (macOS 13+, iOS 2022.1) already cover that jump. **Skip list items whose only content is a single local link.** That is the TOC heuristic.

6. **"Figure out which part of the document they link to" is already solved for headings, and nowhere else.** Pandoc emits `\section{Overview}\label{overview}` and `\hyperref[findings]{Findings}`. XeLaTeX resolves the label to hyperref's numbered dest (`section.1`, `subsection.1.1`, …). A probe PDF from this host's pandoc/xelatex confirms nine `/GoTo` annotations, a `/Names /Dests` tree, and outline items pointing at those dests. What the filter still has to do is *plant a new named dest at the source occurrence* (`bob.r.a`) so the return has somewhere ISO-standard to land. Empty `\hypertarget` dests sit on the baseline; they must be raised (`\Hy@raisedlink` / `\MakeLinkTarget`) or the jump hides the origin line under the chrome. This is a documented hyperref footgun.

7. **`GoBack` is the intuitive action and the unreliable one.** `\Acrobatmenu{GoBack}{↩}` is one line, needs no IDs, and does the right thing when the reader arrived from the outline rather than from a prose link. It is also not in ISO 32000-1 Table 209. Evince ignores it. PDF.js ignores it. Chrome's viewer ignores it. PDFKit *defines* `goBack`, so Highlights might honor it — that is an experiment, not a contract. The portable return is a `/GoTo` to a source named dest. Do not ship a dead `↩` that no-ops in a viewer we have not tested.

8. **Many-to-one dests cannot be a single reverse link unless you use viewer history.** TeX.SE repeats this (Heiko, Ulrike Fischer): the document does not know, at click time, which origin you used. Either the viewer pops history (`GoBack`) or the dest shows one reverse link per origin. The user's "same ID at both ends" is the second option. It is justified only when a dest has two or more *prose* inbounds.

9. **Footnotes already round-trip.** Pandoc `Note` inlines become `hyperref` footnotes: the superscript jumps down, the footnote number jumps back. Do not double-instrument them. They are not `Link` nodes with `#…` targets.

10. **Relative file links and wikilinks are not local to this PDF.** The listen-card filter already drops relative targets (`report_narration.md`) because the source file is not in the PDF. `[foo](other.md)` and `[[Some Note]]` have no destination in the rendered document. Intra-doc Obsidian `[[#Heading]]` is not parsed by default pandoc markdown on 3.1.11.1 (no `wikilinks_title_after_pipe`). A later pass can add that extension; v1 should stick to `[text](#id)` and same-file `#id` fragments.

11. **The feature is Markdown-`create` only.** Local PDFs, PDF URLs, arXiv, and `bob ref clip` articles are stamped or Chrome-printed. There is no pandoc AST to walk. Do not pretend a post-hoc lopdf rewrite can recover heading dests from a paper. Scope the work to the XeLaTeX route.

12. **Highlights already has back/forward, a Go menu, and a TOC sidebar.** Shipping loud IDs on every link without checking whether toolbar-back already restores the view would add chrome to fight chrome. The in-document pill still wins on iPad and as a visible "you are here, tap to return" target. It should be *quiet*.

---

## 3. Justified requirement adjustments

These change the user's wording. They are deliberate.

| Original implication | Adjustment | Why |
| --- | --- | --- |
| Search the Markdown file and rewrite link text | Walk the pandoc AST in the existing Lua filter; leave the `.md` untouched | Regex over Markdown is wrong. The PDF is derived. Vault source must not grow tickets. |
| Add the unique ID *to the rendered local link text* | Keep the author's phrase as the outbound link. Plant an invisible raised named dest at the origin. Put visible chrome at the destination. Add a source-side letter only when that dest has two or more prose inbounds | Mutating the phrase is ugly, collides with numbered sections, and pollutes sidecar quotes. Wikipedia puts the cluster at the destination. |
| Unique alphanumeric ID (`3k`-style) | Sequential lowercase letters `a … z, aa …` in document order. One-to-one dests get a bare `↩` with no letter | Letters scan. Hashes look like defects. One-shot PDFs do not need content-addressed IDs. |
| Every local link gets a ticket | Only *prose* local links: `Link` nodes inside `Para`/`Plain` whose target is `#…` and which resolve to an identifier in this document. Skip TOC-shaped list items, skip `Header` contents, skip footnotes, skip URLs, skip relative files, skip listen-card relative links | Author TOCs would stamp every heading. Generated `--toc` is already clickable and has outline bookmarks. |
| A reverse link whose visible text *is* the ID | Destination grows a small filled pill, right-aligned on the heading line, using the listen-card palette (`BobListenFill` `#EEF3FA`, `BobListenRule` `#3B6EA8`). One inbound: `[↩]`. Several: `[↩ a] [↩ b]`. Each pill is a `/GoTo` to that origin's named dest | Bigger tap target than a superscript. Visually related to the existing listen card. Heading-line `\hfill` keeps the body copy clean. |
| Dest chrome is part of the heading text | Emit `\subsection[Title]{Title\hfill pills}` (optional argument = TOC + bookmarks; body = title plus pills). Wrap pill glyphs in `accsupp` `/ActualText={}` | Tickets must not appear in the PDF outline, the printed TOC, or extracted quotes. |
| Use whatever "back" the PDF format offers | Primary action is ISO `/GoTo` to a `bob.r.<ticket>` named dest. Treat `\Acrobatmenu{GoBack}` as a MacBook experiment, never as the only action | `GoBack` is not in ISO Table 209. Dead controls are worse than no control. PDFKit *might* honor it; prove that before relying on it. |
| All `bob ref create` targets | Markdown XeLaTeX route only | Other routes have no AST. |
| New CLI flag to turn it on | Default on for Markdown `create`. No flag in v1. Add `--no-backlinks` later only if a real document is harmed | Quiet default. Avoids inventing a short alias for an opt-out nobody has asked for yet (`cli_rules.md` would require one). |
| Resolve "any local link" | v1 resolves pandoc auto-identifiers on `Header` (and explicit `{#id}` on headers). Span/Div identifiers if cheap. Unresolved `#foo` stays a dead outbound (pandoc already does this) and gets **no** return pill; stderr warning counts them | Do not invent dests. Do not fail the render. |
| IDs are user-facing names | Tickets are chrome, not content. Never speak them in the listen-card narration, never put them in the page-1 marker, never put them in `ref/` | They are not part of the document's meaning. |

A Markdown-only "add `↩` by hand" convention in the source is a different product. Authors should keep writing `[Findings](#findings)`.

---

## 4. How `create` already renders local links

Code: `src/native/highlights_ref/create.rs` (`render_temp_pdf`, `PANDOC_HEADER_INCLUDES`, `PANDOC_CODE_BREAK_FILTER`). Docs: `docs/highlights-create.md`, `docs/highlights-ref-sync.md`.

The Markdown route:

1. Title from `-T`, YAML `title`, first H1, or stem.
2. Scratch Lua filter (code-break + listen-card).
3. `pandoc --standalone --toc --toc-depth=3 --number-sections --pdf-engine=xelatex -V colorlinks=true` with DejaVu fonts, 10pt, 0.85in margins, tango highlighting.
4. lopdf stamps the page-1 `/Text` Highlights marker and atomically installs into `xlib/`.

A live probe on this host (pandoc 3.1.11.1, XeLaTeX via xdvipdfmx 20240305) of

```markdown
See [Findings](#findings) and [Detail](#detail).
Also see [Findings](#findings) again.
## Findings
### Detail
```

produced:

- LaTeX: `\hyperref[findings]{Findings}` plus `\subsection{Findings}\label{findings}`.
- PDF Link annotations, `/S /GoTo /D (subsection.1.1)` (and `section.1`, `subsubsection.1.1.1`).
- Catalog `/Names /Dests` with those names; `pdfinfo -dests` lists them; `mutool` outline uses `#nameddest=section.1`.
- `pdftotext` extracts "See Findings and Detail." — the link phrase is ordinary text, which is what we want to preserve.
- Nine `/GoTo` actions on a one-page file (generated TOC + body + the second Findings mention).

So: **outbound local links are a solved problem.** The new work is origin dests + dest pills, not "make `#` links work."

The listen-card filter already classifies targets: a URL scheme is external, `#` is local, anything else relative. Relative links inside `<div class="listen">` are stripped. Reuse that classifier.

Geometry is `margin=0.85in`. Tufte `\marginpar` tickets will collide with the edge and with code blocks. Inline heading-line pills are the layout that actually fits.

`accsupp.sty` and `fvextra.sty` are present in TeX Live on this host. New preamble macros belong next to `\BobListenCard` / `\BobListenPlay` so the visual language stays one family.

---

## 5. What the PDF spec and Highlights actually support

### Portable (do this)

ISO 32000-1 §12.6.4.1 / §12.3.2.3: a Link annotation with a **GoTo** action to a **named destination**. That is what pandoc already emits, and what Highlights has been fixing since 2015 ("Links inside the PDF are clickable again"; 2020 "broke navigating PDFs using internal links"; 2024 "inactive page links"; 2025 "certain types of internal links"). A reverse link that is another GoTo to a dest we planted at the origin will follow the same path.

### Non-portable (experiment, do not depend on)

ISO 32000-1 §12.6.4.11 Table 209 named actions: `NextPage`, `PrevPage`, `FirstPage`, `LastPage` only. Note: "Conforming readers may support additional, nonstandard named actions, but any document using them is not portable. If the viewer … does not recognize the name, it shall take no action."

`GoBack` / `GoForward` are Acrobat extras, also listed in the hyperref manual's "Acrobat-specific behavior" and invoked with `\Acrobatmenu{GoBack}{…}`. Known gaps: Evince, TeXworks, PDF.js (issue 21239, still open/closed-as-feature as of May 2026), Chrome's viewer.

Apple PDFKit *does* define `PDFActionNamedName.goBack` and `PDFView.goBack()` / `canGoBack`. Highlights is a PDFKit app (page history, TOC sidebar, Go menu). Version 1.5 literally shipped "back and forward buttons." A one-page prototype with `\Acrobatmenu{GoBack}{↩}` opened in Highlights on the MacBook is the right experiment. If it restores the previous *view* (page + scroll + zoom), a dest pill can be GoBack for the one-to-one case. If it is a no-op or only a page flip, keep `/GoTo`.

### Viewer chrome that already exists

- Highlights Mac: back/forward since 2016; Go menu since the Big Sur redesign; TOC sidebar since Ventura.
- Highlights iOS: TOC view since 2022.1; toolbars hide during reading.
- Preview.app: Cmd-[ / Cmd-] previous view.
- PDFKit page history is documented as filling when the app calls `go(to:)` — tapping a Link annotation typically does.

Phase 0 of implementation is this experiment, not code.

---

## 6. Alternatives considered

| Approach | What it is | Why it loses (or when it wins) |
| --- | --- | --- |
| **A. User's plan: ID spliced into link text + matching dest ID** | `See Findings 3k` … heading `3k` | Ugly, extraction-hostile, TOC-toxic, hash IDs opaque. The pairing idea survives; the splicing does not. |
| **B. Viewer GoBack only, no document chrome** | Teach the toolbar; ship nothing | May already work on Mac. Fails on hidden iPad chrome, on PDF.js, and as an in-text "I landed, now what" cue. Keep as a complement, not the product. |
| **C. `\Acrobatmenu{GoBack}{↩}` on every heading** | One dest control, no IDs | Most intuitive. Not portable. Risk of a dead control. Prototype on Highlights; do not ship as the only mechanism. |
| **D. `hyperref`/`biblatex` `backref`** | Page numbers at the dest | Built for bibliographies. Page numbers force a two-pass aux file and do not land on the *occurrence*. Wrong object. |
| **E. Running header "Back" button on every page** | Always-visible GoBack | Loud. Wrong when you did not jump. Dead if GoBack is unsupported. |
| **F. Tufte margin tickets** | Pills in the margin aligned to dest | 0.85in margins; collisions with code/tables. Beautiful in a Tufte class we do not use. |
| **G. Post-process with lopdf: extra Link annots, no glyphs** | Extraction-safe, coordinate-based | We would have to locate every origin/dest box after xelatex. Fragile vs font/line-breaking. Marker stamping is already the lopdf job; do not add geometry reconstruction. |
| **H. JavaScript view-stack (Beamer `\hLink`)** | Push view, pop on Back | Acrobat JS only. Highlights will not run it. |
| **I. Recommended: origin named dests + dest return pills + letters only when n>1** | Wikipedia backrefs, listen-card paint, ISO GoTo | Wins on beauty, tap size, extraction (with accsupp), TOC/bookmark hygiene, and Highlights' known GoTo support. |

Rejected but kept in the pocket: Crockford-base32 two-character hashes if a future workflow starts *citing* ticket IDs across re-renders. Not v1.

---

## 7. Recommended solution

Call them **return tickets**, not backlinks. "Backlink" in this vault already means graph/wikilink direction. A ticket is a round-trip token.

### 7.1 Behavior, by case

**Prose local link, dest is a heading, one inbound**

```
See Findings.                         ← ordinary colored hyperlink, unchanged
                                        invisible raised dest bob.r.a at the
                                        start of "Findings"

1.1  Findings                    [↩]  ← pill, listen-card blue, /GoTo bob.r.a
                                        heading bookmark and TOC still say
                                        "Findings"
```

**Same dest, several prose inbounds**

```
See Findings↩a in the intro and
Findings↩b in the recap.

1.1  Findings              [↩ a] [↩ b]
```

Letters appear on the *source* only in this case, as a superscript after the link, same paint as the pill. They are not inside the link phrase.

**TOC list, generated TOC, outline, footnotes, URLs, other files**

No tickets. No dest pills. Existing behavior.

**Unresolved `#missing`**

Outbound stays (dead, as today). No origin dest, no dest pill. One stderr line: `return-tickets: N unresolved local link(s)`. Render still succeeds.

### 7.2 Visual language

Reuse the listen-card tokens already in `PANDOC_HEADER_INCLUDES`:

- Fill `#EEF3FA`, rule `#3B6EA8`, `\sffamily\scriptsize`.
- Glyph: `↩` (U+21A9, in DejaVu). Fallback: `\leftarrow`.
- Shape: a tight `\colorbox{BobListenFill}` pill with a little padding, so the `/Rect` of the Link annot is tappable on iPad. Not a raw superscript.
- Placement: `\hfill` on the heading line, so the pill sits on the right of the title. Several pills share that right edge, thin space between them.
- Body links stay hyperref's `colorlinks` (today: colored text, `/Border [0 0 0]`). Do not recolor them. Red/blue pairing: phrase = go there, blue pill = come back.

### 7.3 Mechanics

Two Lua passes in the existing filter (pandoc 3.1 supports returning a list of filters; the listen-card tests already run this file):

1. **Collect.** Walk blocks. Record every `Header` identifier (and explicit `{#id}`). Record every prose `Link` whose `target` matches `^#` and whose identifier exists. Skip a `BulletList`/`OrderedList` item whose trimmed inlines are a single such Link (TOC heuristic). Skip links inside `Header`. Skip listen-card Divs (they already become `RawBlock`).
2. **Assign.** Document-order tickets `a, b, …, z, aa`. Each prose link gets `bob.r.<ticket>`. Group by dest identifier.
3. **Rewrite.**
   - `Link`: prefix `RawInline` latex `\Hy@raisedlink{\hypertarget{bob.r.a}{}}` (via a preamble wrapper `\BobOrigin{bob.r.a}` so we do not smash `makeatletter` in the AST). If that dest's inbound count > 1, append a superscript letter (ActualText-empty) that is *not* a second outbound link.
   - `Header` with inbounds: replace with `RawBlock` latex
     ```latex
     \subsection[Findings]{Findings\texorpdfstring{\hfill\BobReturn{bob.r.a}{}}{}}\label{findings}
     ```
     or, when n>1, `\BobReturn{bob.r.a}{a}\,\BobReturn{bob.r.b}{b}`.
   - Keep `.unnumbered` / unlisted classes as starred forms. Map levels 1–5 to `section`…`subparagraph` (pandoc article default: `#` is `\section`, matching today's `--metadata title=` + body H1).

Preamble (next to the listen-card macros):

```latex
\usepackage{accsupp}
\makeatletter
\newcommand{\BobOrigin}[1]{\Hy@raisedlink{\hypertarget{#1}{}}}
\newcommand{\BobReturn}[2]{%
  \hyperlink{#1}{%
    \colorbox{BobListenFill}{%
      \sffamily\scriptsize\color{BobListenRule}%
      \BeginAccSupp{method=plain,ActualText={}}%
      \,\textleftarrow\if\relax\detokenize{#2}\relax\else\,#2\fi\,%
      \EndAccSupp{}}}}
\makeatother
```

(`\textleftarrow` if `↩` is flaky in the PDF string; prefer the Unicode glyph in DejaVu and keep `\textleftarrow` as fallback.)

Dest names: `bob.r.a` prefix, ASCII, no collision with hyperref's `section.1`, `page.1`, `Doc-Start`.

### 7.4 What "beautiful" means here

- The sentence still reads as the author wrote it.
- The dest pill is the same family as the listen card, so the PDF has one chrome language, not three.
- One inbound is a single hook arrow, no ID soup.
- Several inbounds copy Wikipedia, which readers already understand.
- Bookmarks, printed TOC, and extracted quotes do not grow arrows.
- iPad tap targets are pills, not 6pt superscripts.

### 7.5 Phase 0, before merging chrome

On the MacBook, in Highlights, with a stock `bob ref create` PDF that already has internal links (no tickets):

1. Tap a prose `#` link that lands several pages down. Does toolbar Back restore the origin *view*?
2. Tap a `#` link that lands on the same page, below the fold. Same question.
3. Hide the toolbar (iPad, or full screen). Is there any in-document way back today?
4. Open a one-off PDF whose only extra is `\Acrobatmenu{GoBack}{↩}` on a heading. Does that pill work?

If (1) is yes and (3) is rarely a problem, ship dest pills only (no source letters). If (1) is no, ship the full origin-dest pair. If (4) is yes, the unlabeled `↩` can be GoBack; letters remain `/GoTo`. Record the four answers in the implementation plan. Do not skip this.

---

## 8. Implementation sketch

All of this stays inside the Markdown route of `bob ref create`. No new subcommand. No marker field. No `scan` change.

1. **Extend `PANDOC_HEADER_INCLUDES`** with `accsupp`, `\BobOrigin`, `\BobReturn`. Keep listen-card colors as the single palette.
2. **Extend `PANDOC_CODE_BREAK_FILTER`** with the two-pass collector/rewriter. Keep `Code` and `Div` (listen) as the first filter in the returned list so listen-cards still compile to `\BobListenCard` before tickets look at Links.
3. **Tests, matching the ones already around line 2228 of `create.rs`:**
   - Pandoc `--to=latex --lua-filter`: a para link to `#findings` plus `## Findings` emits `\BobOrigin{bob.r.a}` and `\BobReturn{bob.r.a}{}`. The heading's optional argument does not contain `\BobReturn`. A bullet-only `[Findings](#findings)` list does **not** emit a return. Two prose links to the same dest emit `a` and `b`. An HTTP link is untouched. A listen-card relative link is still stripped.
   - Live xelatex (skip if missing, same as `highlights_create_renders_pdf_with_outline_and_marker_when_available`): `mutool`/`pdfinfo -dests` shows `bob.r.a`; a Link annot `/D (bob.r.a)` exists; outline title is still "Findings" without `↩`; `pdftotext` does not contain `↩` or the letter if ActualText worked (and if it does contain them, fail the test — that is the sidecar-leak detector we can run without Highlights).
4. **Docs:** a short "Return tickets" subsection in `docs/highlights-create.md`, next to "Listen cards in PDFs." One before/after example. State the TOC skip and the Markdown-only scope.
5. **MacBook verification:** Phase 0 answers, plus one real research report (`bob ref create` of a `202610/*.md` with ~30 local links) opened in Highlights: tap, return, highlight a heading, inspect the sidecar for leaked tickets.

CLI: no new flag in v1. If a later document hates the pills, add `--no-backlinks` with a short alias then, alphabetically, per `sase/memory/cli_rules.md`.

Clip / stamped PDFs: out of scope, documented as such.

---

## 9. Risks

- **ActualText ignored by Highlights.** Then tickets leak into quotes. Mitigation: the `pdftotext` test plus one sidecar inspection. Fallback: draw the pill as a tiny `\includegraphics` of a vector PDF so the content stream has no ticket glyphs.
- **Raised dest still lands one line low.** Classic `\hypertarget` baseline bug. Mitigation: `\Hy@raisedlink` / `\MakeLinkTarget`; visual check in Highlights, not only in `pdfinfo`.
- **Raw-latex headers drift from pandoc's writer** (unnumbered, `--shift-heading-level`, languages). Mitigation: only replace a Header when it actually has inbounds; leave the rest to pandoc. Cover `.unnumbered` in the latex test.
- **Letter overflow.** A dest with 40 inbounds becomes a soup. Unlikely in this corpus (unique dests per report ~12–16, inbounds per dest usually 1–3). Cap visible pills at 8 and collapse the rest to `+n` unlinked text if it ever happens.
- **`↩` missing in a fallback font.** DejaVu is already `mainfont`/`sansfont`. Still provide `\textleftarrow`.
- **Dead GoBack if someone "simplifies" to Acrobat menus.** Do not.

---

## 10. Would I take a different approach?

Yes, relative to the sketch: I would not put IDs in the link text, I would not use opaque alphanumerics, I would not touch the Markdown file, and I would not start by assuming the viewer has no Back.

I would start from three facts this repo already has:

1. Outbound `#` links already compile to portable `/GoTo` annotations.
2. Highlights has followed those annotations for a decade and already ships Back/Forward.
3. The existing Lua filter plus listen-card paint is a complete visual and technical home for dest chrome.

From there the product is small: **origin dest + dest pill**, Wikipedia letters only when a dest is crowded, TOC skipped, extraction hidden, Markdown route only.

That is less than the sketch in visible noise and more than the sketch in reliability. It is also the version I would want to read.

---

## Sources

- `src/native/highlights_ref/create.rs` — `render_temp_pdf`, `PANDOC_HEADER_INCLUDES`, `PANDOC_CODE_BREAK_FILTER`, listen-card tests
- `docs/highlights-create.md`, `docs/highlights-ref-sync.md`
- Live pandoc 3.1.11.1 + XeLaTeX probe on this host: `\hyperref[findings]{Findings}` → PDF `/GoTo /D (subsection.1.1)`; `pdfinfo -dests`; decompressed annots via `mutool clean -d`
- ISO 32000-1:2008 §12.6.4.11 Table 209 (named actions) and the note on nonstandard names
- Heiko Oberdiek / Ulrike Fischer, TeX.SE: "Going back when using hyperref", "How to jump to a hyperlink and back", `backref` vs `GoBack`
- hyperref manual, "Acrobat-specific behavior" (`GoBack`, `\Acrobatmenu`)
- mozilla/pdf.js#21239 (2026-05-08), Named Action `GoBack` unsupported
- Apple PDFKit: `PDFView.canGoBack` / `goBack(_:)`; `PDFActionNamedName.goBack`
- Highlights changelog: v1.0.1 links clickable; v1.2 page-links; v1.5 back and forward buttons (2016-03-15); 2020 internal-link navigation fix; 2022.1 / Ventura TOC sidebar; 2024 inactive page links; 2025 internal links in comments
- Wikipedia [Help:Footnotes](https://en.wikipedia.org/wiki/Help:Footnotes) — `^` / `a b c` backlink cluster
- Corpus: 356 `[…](#…)` links across 32 notes in this research sidecar's `202610/` tree
- TeX Live on this host: `accsupp.sty`, `fvextra.sty`, `hyperref.sty` resolved by `kpsewhich`
