# Beautiful PDFs from area and project notes (`bob ref create`)

- **Researcher:** grk
- **Date:** 2026-10-15
- **Question:** How should `bob ref create` grow so area notes and project notes become beautiful, Highlights-ready PDFs? The current look is `~/bob/lib/chat/sase_blog_v1.pdf`. Is the idea sound, what should change, and what should be built?
- **Verdict:** Build it, but treat it as a **reading projection plus a typesetter**, not as “make pandoc dump prettier.” Printing a live GTD note through XeLaTeX/DejaVu will never look like a document. The high-leverage work is a vault-aware preprocessor; the typesetter should then move from XeLaTeX to a Bob-owned **Typst** template that matches the web-article house style and embeds real CID fonts.

---

## 1. In one breath

`bob ref create sase_blog.md` did exactly what the Markdown route is specified to do: feed the file to pandoc with `--toc --number-sections --pdf-engine=xelatex`, DejaVu fonts, 10 pt, 0.85 in margins, `linestretch=1.08`, stamp a page-1 Highlights marker, install into `xlib/chat/`. The resulting six-page PDF is a faithful dump of a working project note. That is why it looks bad.

Two factories already exist in this vault:

| Factory | Engine | Look | Font embedding | Used for |
| --- | --- | --- | --- | --- |
| Markdown `create` | pandoc + XeLaTeX (`xdvipdfmx`) | Academic default, DejaVu, numbered `0.1` sections | CID TrueType (Highlights-clean) | 385 `lib/chat/` PDFs |
| Web-article `create` | Defuddle → Bob HTML → headless Chrome | Source Serif 4 / Inter / JetBrains Mono, masthead, 34 em column | **Type 3** (Skia; PDFKit historically mangles quotes) | Recent `lib/blogs/` captures, e.g. `diataxis_fr_compass_and_howto.pdf` (2026-10-15) |

The visual target already exists: today’s Bob-owned **web-article** PDFs. The Highlights-safe text layer already exists: the **Markdown** PDFs. The work is to get both properties on area and project notes, which are a third input shape the Markdown route has never been taught to read.

A live measurement of the vault: **102** area/project notes, **102** with no `title:` frontmatter, **95** with no `# ` H1. Title derivation therefore falls through to the file stem (`sase_blog`). That is a systematic title failure, not a one-off.

---

## 2. What `sase_blog_v1.pdf` actually is

Inspected 2026-10-15 on athena. Source: `~/bob/sase_blog.md` (`type: "[[project]]"`, parent `[[sase]]`). PDF: 6 pages, 78 KB, `Creator: LaTeX via pandoc`, `Producer: xdvipdfmx`, fonts DejaVu Serif/Sans Mono + Latin Modern Math.

Defects, grouped by cause:

**Content (the majority).** The PDF is a GTD working file.

- Page 1 opens on the `^prj` task, then a generated status-chip row (`2 open · 1 next/wip · …`), then open tasks carrying `[fresh::]`, `[created::]`, `[id::]`, `#task`, `#hide`, `^block-ids`, **BLOCKS** / **DEPENDS ON** children.
- Pages 2–4 are Done & Canceled tasks with cancel logs, schedule-roll histories, and work logs. That is operational residue, not reading material.
- Wikilinks render as literal `[[ref/chat/sase_launch_post_outline|…]]`. Image embeds render as `![[img/20260802_144938.png|400]]`. The Contents section is the unresolved pointer `Draft: [[sase_blog_contents]]`. The actual prose of the post lives in `~/bob/sase_blog_contents.md` and never enters the PDF.
- The status-group chips are Markdown links to `#Tasks#Next%20&%20In%20Progress`. Those fragments are legal in HTML and (barely) in LaTeX; they are **syntax errors in Typst**.

**Typography (real, but secondary).**

- Title is the snake_case stem, because there is no YAML `title` and no H1 (`extract_title` in `create.rs`).
- `--number-sections` numbers from the first body heading. The body starts at `## Tasks`, so the TOC is `0.1 Tasks`, `0.1.1 Next & In Progress`, …, `0.5 Later Posts`.
- DejaVu Serif at 10 pt / 1.08 stretch / 0.85 in margins is a compact technical default, not a reading face. Headings, body, and chrome share one family.
- No masthead, no running footer, no 34 em measure. Compare page 1 of `lib/blogs/diataxis_fr_compass_and_howto.pdf`: site kicker, display title, byline, provenance rule, linked contents, then a serif column.

**Pipeline (working as designed).** Pandoc Lua filters today handle code wrapping and return-link pills (`return_links.lua` is `FORMAT:match("latex")` only). There is no wikilink filter, no embed resolver, no task-field stripper, no area/project detection.

Listen (`-L`) narrates the **staged PDF**, not the Markdown source. A dump of `[fresh:: 2026-10-15] [id:: sase_blog__prj] ^prj` is a bad commute episode even if the type is later improved.

---

## 3. Critique of the plan

The implied plan: “`bob ref create` should emit beautiful PDFs from area/project notes; look at `sase_blog_v1.pdf` and make that better.”

**What is right**

- PDF is the correct object. Bryan reads and annotates in Highlights Pro; `scan` turns those annotations into `ref/` notes; `-L` binds commute audio to the same PDF. A Markdown-only “export” would skip that loop.
- `create` is the correct command. It already owns marker composition, collision walks, scratch staging, audio binding, and intake install. A new `bob note pdf` would duplicate that contract. CLI rules also say not to invent a sibling under a different noun for the same write.
- “Beautiful” is a real product requirement. The web-article template proves Bob already cares about print design; the Markdown route was left on pandoc defaults.
- Doing this inside bob, not as a one-off pandoc wrapper, keeps `doctor`, `--dry-run`, and the Mac `xlib` → `scan` bridge.

**What is wrong or incomplete**

1. **The example is a content problem wearing a typesetting costume.** Swapping DejaVu for Source Serif 4 on the current AST still prints schedule logs, block IDs, and unresolved `[[sase_blog_contents]]`. A pretty GTD dump is still a GTD dump.
2. **Area/project notes are not the Markdown `create` was built for.** The Markdown route’s customers today are research/chat notes (385 PDFs). Those are already linear documents. Area/project notes are databases of tasks plus a few reading sections. One render path cannot serve both without a projection step.
3. **Reusing the Chromium blog printer as the Markdown engine copies a known Highlights failure mode.** Oct 1 research (`web_url_reference_pdf_capture`) found Chrome/Skia prints extract as `p ublished`, `spectru m`, `RAPTO R` in Highlights sidecars. Lead consolidation noted the PDF text layer itself was intact and asked for a one-day Mac spike on a Bob-owned template. That spike is still the right experiment. What is now known, 14 days later: the Bob-owned template **still embeds Type 3 fonts**. `pdffonts` on `diataxis_fr_compass_and_howto.pdf` (captured today, `Producer: Skia/PDF m155`) shows `SourceSerif4-Regular` and `Inter-Regular` as Type 3. Variable woff2 `@font-face` is exactly the Skia branch that emits Type 3 instead of `/FontFile2` (confirmed by Chromium/Skia behavior and by [tkhquang, 2026-03](https://tkhquang.dev/blog/posts/every-letter-in-this-pdf-is-a-drawing): static TTFs embed as TrueType; variable/woff2 become Type 3 drawings).
4. **“Just improve the LaTeX template” inherits the Mac TeX tax.** `docs/highlights-create.md` already documents BasicTeX missing `needspace.sty` and a user-mode `tlmgr` ritual. `RENDER_TEX_PACKAGES` is 24 files. Doctor treats missing packages as warnings because Markdown render is optional per host. Growing that surface is the wrong direction.
5. **Return links are LaTeX-shaped.** `return_links.lua` no-ops unless `FORMAT` is latex, and the pills are TikZ. An engine switch is a rewrite of that feature, not a flag change.
6. **Title identity is the stem.** `extract_title` is frontmatter `title`, then first ATX H1, then stem. Area/project notes almost never have the first two. `-T` is an escape hatch, not a default.

The idea is a good product. The implementation that only restyles the current dump is a bad one.

---

## 4. Justified requirement adjustments

These change the user’s wording. They are deliberate.

| Original implication | Adjustment | Why |
| --- | --- | --- |
| Make the current PDF dump look better | Default area/project output is a **reading projection**. `--full` keeps today’s forensic dump (with better type). | The dump is unreadable on purpose: it is a working file. Listen and Highlights need a document. |
| Beauty = fonts and margins | Beauty = (1) the right sections, (2) resolved links/embeds, (3) a house-style typesetter. (1) and (2) outrank (3). | `sase_blog_contents.md` never appears in `sase_blog_v1.pdf`. That is the actual missing content. |
| One render for every `.md` | Detect `type: [[area]]` / `[[project]]` and project; leave chat/research Markdown on the document path (wikilinks/embeds still resolved). | 385 chat PDFs are already documents. Do not strip their body the way a project note must be stripped. |
| Chromium blog template as the Markdown engine | **Do not** print Markdown through Chrome until Type 3 embedding is fixed **and** a Mac Highlights quote spike passes. | Same Highlights/PDFKit failure the Oct 1 research documented. Markdown does not need Chrome today. |
| Keep XeLaTeX forever | Move Markdown PDF to **Typst**, keep XeLaTeX as a fallback for one release. | Single binary, ~20–30× faster in published pandoc benchmarks, CID Type 0C fonts (Highlights-class), already on PATH here (`typst 0.15.1`). |
| Title = filename | Humanize the stem (`sase_blog` → `SASE Blog`); use `-T` / YAML `title` when present; put the `^prj` line in the masthead as the dek, not as a task. | 95/102 notes have no H1. |
| Numbered sections | Off for notes. `--number-sections` is why the TOC is `0.1`. | Notes are not articles with H1-as-title. |
| Tasks rendered as raw lines | Compact open-task list (checkbox + description only). Collapse Done & Canceled behind `--full`. Strip `[id::]`, `[fresh::]`, `[created::]`, `[dependsOn::]`, `^block-ids`, `#task`, `#hide`. | Those fields are for Obsidian plugins, not for a reader or a TTS engine. |
| Wikilinks as source syntax | Resolve `[[note\|alias]]` → alias, `[[note]]` → display name, `![[img/…]]` → image, `![[note]]` / `[[note]]` of a Markdown child → **one-level transclusion** for reading sections. | The Contents/Outline drafts are the document. |
| New subcommand | Stay on `bob ref create`. Optionally accept a bare note name (`sase_blog`) in addition to a `.md` path. | Same intake contract. Capture-targets already know how to resolve notes. |
| Default `ref_type=chat` | Keep `chat` unless `-t` is passed. Do not invent `projects` as a library folder in this change. | Identity and scan paths stay stable. |

A Markdown-only clip into the vault (Obsidian export, “Print to PDF” from the app) remains a different product. It does not satisfy Highlights + listen.

---

## 5. Two layers

```
area/project note ──► reading projection ──► typesetter ──► stamp ──► xlib/
research .md      ──► light projection  ──►    same     ──►  same ──► xlib/
```

Stamp, collision, audio, scan, and the page-1 marker do not change. The new work is everything left of “typesetter,” plus swapping the typesetter.

### 5.1 Reading projection (Rust + one pandoc Lua filter)

Run **before** pandoc, on a scratch copy, so the vault file is never rewritten.

For `type: [[area]]` / `[[project]]` (default; `--full` skips this):

1. **Masthead metadata:** kind (`Project` / `Area`), humanized title, `^prj` / area purpose as dek, parent, captured date, open/done counts. Drop YAML from the body (pandoc already consumes it as metadata; pass the masthead fields explicitly).
2. **Strip machine syntax** from every task line: Obsidian `[key:: value]` fields, trailing `^id`, `#task`, `#hide`, `#prj`, `#ref` tags that are workflow, not content.
3. **Tasks section:** keep open / next / blocked as a short checklist. Drop the generated chip row (`[⚪ n open](#Tasks)` …) entirely — those `#Tasks#…` fragments are also the Typst-breaker. Done & Canceled omitted unless `--full`.
4. **Wikilinks:** display text in the body; optional PDF link to an already-captured `lib/**.pdf` when `bob ref find` has a hit. Dead vault links become plain text plus a `warning:` line (same shape as return-link dead links).
5. **Embeds:** images resolved via `--resource-path` (vault root). Markdown transclusion **one level**, only for non-task notes (`sase_blog_contents`, outline drafts). Do not recurse into other project notes.
6. **Logs:** schedule / cancel / work-log callouts dropped unless `--full`.
7. **Headings:** do not number. Do not invent an H1 if the projection already supplies a title via `--metadata title=`.

For ordinary Markdown (chat/research): steps 4–5 only (wikilinks, images), plus stop numbering if the file has no H1.

Implementation sketch: a Lua filter is enough for wikilinks/embeds/field-stripping and matches the existing `PANDOC_CODE_BREAK_FILTER` / `return_links.lua` pattern. Transclusion and title/masthead belong in Rust next to `extract_title`, because they need vault path resolution (`parent_notes`, `vault_links`).

### 5.2 Typesetter options

Evaluated against Bob’s actual constraints: Highlights text extraction, `-L` TTS, `lopdf` stamp, Mac + Linux, doctor, return links, images, speed, house style.

| Engine | Visual match to blogs | Highlights text | Mac install | Vault Markdown | Return links | Speed | Verdict |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **XeLaTeX (today)** | Poor (DejaVu, 0.1 numbering) | Proven clean (385 PDFs) | Painful (BasicTeX + `tlmgr --usermode`) | Works, ugly | Already shipped (TikZ) | Slow (seconds) | Keep as fallback only |
| **XeLaTeX + Inter/Source Serif via fontspec** | Better type, same dump | Likely clean | Same TeX tax; fonts must exist on the Mac | Same | Keep Lua+TikZ | Slow | A local maximum. Do not invest here. |
| **Chromium + `reader.css`** | Perfect (it *is* the house style) | **Type 3 risk**; Oct 1 PDFKit quotes broken; still Type 3 today | Chrome already required for articles | Needs HTML wrap; `#Tasks#…` would work | Must rewrite pills in HTML | Fast enough | Right for articles. Wrong default for Markdown until static TTF embedding is proven on a Mac spike. |
| **WeasyPrint** | CSS, real OpenType | Usually clean | Pango/Cairo tax; not installed | Extra Python engine | CSS | Medium | Third stack. Reject. |
| **Quarto** | Can drive Typst or LaTeX | Depends on engine | Installed here (`1.9.37`) but heavy | Overkill | Engine-dependent | Medium | Wrapper around the same choice. Reject. |
| **Typst via pandoc** | Custom template can match blogs | CID Type 0C (same class as XeLaTeX). Verified: `pandoc --pdf-engine=typst -V mainfont=Inter` embeds `Inter-*-Identity-H` CID Type 0C; `pdftotext` is clean; poppler raster is clean | Single binary (`brew install typst` / cargo). Already on athena. | **Hard-fails** on raw area/project notes (`#link(<Tasks#Next%20&%20In%20Progress>)` is a Typst syntax error). Projection is a prerequisite, not a polish. | Must port Lua filter from latex to typst raw | ~20–30× faster than XeLaTeX in published pandoc 3 + Typst benchmarks ([slhck, 2025-10](https://slhck.info/software/2025/10/25/typst-pdf-generation-xelatex-alternative.html): 357 ms vs 9.7 s) | **Recommended Markdown engine.** |

Live checks on this host (2026-10-15):

- `typst 0.15.1` at `~/.cargo/bin/typst`; `pandoc 3.1.11.1` (Debian) already lists a `typst` writer.
- `pandoc --pdf-engine=typst` **without** `-V mainfont=…` dies: pandoc’s default template passes `font: ()`, and Typst 0.15 rejects an empty fallback list. Bob must pass fonts or ship a template. That is a one-line contract, not a blocker.
- Clean Markdown through Typst+Inter: tagged PDF 1.7, 26 KB, `Creator: Typst 0.15.1`, CID Type 0C. Poppler (`pdftoppm`) renders a modern, tight page; the in-session PDF viewer smashed the same file (a CID CFF viewer bug, not a Typst bug). XeLaTeX+DejaVu on the same source is the familiar “academic default.”
- Raw `sase_blog.md` through Typst: pandoc exit 43, unclosed Typst labels on the status-chip links. Projection is mandatory for this engine.

Debian pandoc 3.1 vs Typst 0.15 is a real compatibility seam (empty `font`, older template). Ship a **Bob Typst template** and invoke `pandoc -t typst --template=bob.typ --pdf-engine=typst`, rather than depending on `--print-default-template=typst`.

---

## 6. Recommended solution

### 6.1 Product

`bob ref create <area-or-project-note> -P <parent>` produces a Highlights-ready **reading PDF**:

- Masthead in the web-article language (small Inter kicker `PROJECT` / `AREA`, Source Serif 4 title, `^prj` dek, provenance line).
- Body in a ~34 em serif column, Inter headings, JetBrains Mono code, page `n / N` footer.
- Open tasks as a short checklist; reading sections (Requirements, Outline, Contents, Later Posts, …) with wikilinks resolved and Markdown children inlined one level.
- TOC of real headings, unnumbered.
- Same stamp / scan / listen contract as today.

`--full` is the “print the working file” escape hatch for debugging, not the default.

Chat/research Markdown gets the same typesetter and wikilink/image filter, without the GTD strip.

### 6.2 Engine

**Typst** for Markdown. **Chromium** stays the article engine.

Match the blog typeface trio by vendoring **static OTF/TTF** of Source Serif 4, Inter, and JetBrains Mono next to the existing woff2 set (fontsource publishes both; OFL already vendored). Typst cannot consume the woff2 slices. Static faces also unlock a later Chromium fix (see §6.4).

Port return links to Typst in the same Lua filter by emitting Typst raw instead of `\BobBack{…}` when `FORMAT` is typst. Until that port lands, area/project reading PDFs can ship **without** return pills (those notes have almost no `#heading` citations of the kind the feature was built for). Chat Markdown keeps XeLaTeX until the port is done, **or** Typst ships with return links off (`bob-return-links: false` already exists).

Doctor: add a `typst:` row. Keep the `xelatex` / `latex_packages` rows as fallback health.

Config: `BOB_PDF_ENGINE=typst|xelatex` (test seam, like `BOB_PANDOC_COMMAND`). Default `typst` once stamp+Highlights are verified; `xelatex` otherwise.

### 6.3 Phases

**Phase A — projection on XeLaTeX (ship first).** Smallest change that makes `sase_blog` readable. Humanized title, no section numbers, strip machine fields, drop chip row and done-logs, resolve wikilinks, inline one-level Markdown embeds, resolve images. Keep DejaVu for this phase so Mac TeX does not grow. Re-render `sase_blog` and compare listen output.

This phase is the one that turns `Draft: [[sase_blog_contents]]` into the actual post.

**Phase B — Typst house template.** Bob `template.typ`: masthead, fonts, measure, footer, heading styles aligned with `reader.css`. `pandoc -t typst --template … --pdf-engine=typst`. Verify `lopdf` stamp round-trip (Typst 0.15 PDFs are 1.7 tagged; poppler already warns `Suspects object is wrong type (boolean)` — stamp must be tested, not assumed). Verify Highlights quote text on a Mac. Verify `-L` narration. Then flip the Markdown default.

**Phase C — return-link port and XeLaTeX demotion.** Port the Lua filter. XeLaTeX becomes fallback. Doctor still checks it.

**Phase D (optional, parallel) — fix article Type 3.** Serve static TTF to Chromium instead of variable woff2. Re-capture one blog, `pdffonts` should show CID TrueType / Type 0, not Type 3. Re-run the Oct 1 Highlights quote spike. If quotes come out clean, the two factories share a typeface and Markdown *could* later print through HTML for perfect visual parity. Do not block A–C on this.

### 6.4 What I would not do

- Print area/project notes through Chrome “because the blog PDFs look better.” They look better and they are the wrong font object for Highlights.
- Restyle XeLaTeX with eisvogel / Tufte / fontspec and call it done. The Mac package story is already a support load; the dump problem remains.
- Add WeasyPrint or Quarto as a third engine.
- Write `ref/` notes from `create`. Scan still owns that.
- Transclude the whole vault. One level, reading sections only.
- Number sections, or use the file stem as the display title.

### 6.5 CLI sketch (after A+B)

```text
bob ref create sase_blog.md -P sase
bob ref create sase_blog -P sase              # note-name resolution
bob ref create sase_blog.md -P sase --full    # forensic dump
bob ref create sase_blog.md -P sase -T "The first SASE post"
```

New flags need short aliases (CLI rules). `--full` / `-F` is the one new reading-mode flag. Do not add `--engine` to the public help until the fallback is real; keep it as `BOB_PDF_ENGINE`.

Help text should say that area and project notes are projected into a reading PDF; `--full` prints the working file.

---

## 7. Is this a good idea?

Yes, with the projection. The use cases that justify it:

- Commute listen of a project’s thinking (`-L`), not of its schedule log.
- Highlights annotation of Requirements / Outline / drafted Contents, which then sync into a `ref/` child of the project (already how `sase_blog_v1` is parented: `parent: "[[sase_blog]]"`).
- A printable snapshot of an area (`job`, `cash`, `dev`) that a human can read.

It is a weak idea as “pretty-print my GTD database.” Nobody wants a beautiful cancel log.

I would take this approach over “improve pandoc flags” because the vault already has a house style, a Highlights constraint, a TeX support problem, and a Typst binary. The missing piece is a note compiler, not a better `\geometry`.

---

## 8. Open spikes (do not skip)

1. **Mac Highlights quote test on a Typst PDF.** Same spike the Oct 1 consolidation asked for, now aimed at Typst CID Type 0C rather than Chrome Type 3. One page, highlight a sentence, `scan`, read the sidecar. Pass/fail gates Phase B.
2. **`lopdf` stamp on Typst 0.15 output.** Marker round-trip, page count unchanged, no encryption. The poppler `Suspects` warning is a flag.
3. **Static TTF vs woff2 in Chromium print.** If static faces embed as TrueType, article PDFs get Highlights-clean text without leaving Chrome. That is a blog-pipeline win independent of this work.
4. **Listen text source.** Confirm `sase listen render` reads the PDF text layer (docs say `{target}` is the staged PDF for Markdown). If it can take Markdown instead, projection still matters for Highlights but TTS could skip PDF extraction.

---

## 9. Sources

**This vault and tree (primary).**

- `~/bob/lib/chat/sase_blog_v1.pdf` and `~/bob/sase_blog.md`, `~/bob/sase_blog_contents.md`
- `~/bob/lib/blogs/diataxis_fr_compass_and_howto.pdf` (Bob-owned Chromium template, 2026-10-15)
- `~/bob/lib/blogs/harness_for_rsi.pdf` (legacy live-page print)
- `src/native/highlights_ref/create.rs` (`render_temp_pdf`, `PANDOC_HEADER_INCLUDES`, `extract_title`)
- `src/native/highlights_ref/return_links.lua`, `return_links.tex`, `render_tex.rs`
- `scripts/web_clip/template/reader.css`, `scripts/web_clip/fonts/README.md`
- `docs/highlights-create.md`, `docs/highlights-ref-sync.md`
- Prior research: `202610/web_url_reference_pdf_capture/web_url_reference_pdf_capture__grk.md` and `__final.md` (Oct 1; Chrome vs XeLaTeX, Highlights quote damage)

**External.**

- [Typst with Pandoc, slhck, 2025-10-25](https://slhck.info/software/2025/10/25/typst-pdf-generation-xelatex-alternative.html) — 27× vs XeLaTeX, template workflow
- [Pandoc Typst templates, Imaginary Text, 2025-03](https://imaginarytext.ca/posts/2025/typst-templates-for-pandoc/) — `-V template=` vs pandoc’s own template
- [Imprint, Typst forum, 2026-06](https://forum.typst.app/t/imprint-branded-pdfs-from-markdown-with-typst-as-the-engine/9156) — pandoc `-t typst` + house template, TOC/numbering off by default
- [Every letter is a drawing, tkhquang, 2026-03](https://tkhquang.dev/blog/posts/every-letter-in-this-pdf-is-a-drawing) — Chrome variable/woff2 → Type 3; static TTF → `/FontFile2`
- Chromium issue 375395119 — Skia Type 3 embedding change
- [Highlights features](https://highlightsapp.net/features/) — sidecar Markdown export is the scan input; selectable text is the contract

---

## 10. Recommendation (one paragraph)

Keep `bob ref create` as the command and the Highlights intake contract. Add a **reading projection** for area and project notes so the PDF is a document (human title, `^prj` dek, stripped GTD fields, collapsed done-work, resolved wikilinks, one-level transclusion of content notes). Typeset that projection with a **Bob Typst template** in the web-article typeface trio, embedding real CID fonts. Land the projection on XeLaTeX first so `sase_blog` becomes readable this cycle; flip the engine after a Mac Highlights quote test and an `lopdf` stamp test. Do not print Markdown through Chromium while the blog pipeline still emits Type 3 fonts. `--full` preserves the forensic dump. That is the smallest path that makes the motivating PDF beautiful in the sense Bryan actually needs: readable, highlightable, and listenable.
