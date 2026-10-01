# Web URL → Highlights Reference PDF: Consolidated Research and Recommendation

## Bottom line

1. **Build it, but as *capture into the existing Highlights pipeline*, not as "conversion".**
   The new command produces one marker-stamped PDF in `~/bob/xlib/blogs/`. The existing
   `bob highlights scan` then moves it to `lib/blogs/` and writes `ref/blogs/<slug>.md`, the
   same as Markdown `create` does today ([how create and scan work](#how-create-and-scan-work)).
   All five researchers agree on this boundary.
2. **The hard part is getting the page, not making the PDF.** The motivating URL returns a
   Cloudflare 403 challenge to `curl` (all five researchers, and the lead with two different
   Chrome user agents), to headless Chromium in both headless modes, to Defuddle's fetcher, and
   to Claude's WebFetch ([fetch results](#fetching-the-example-url-blocks-every-headless-client)).
   A headless-only design fails the example. Bryan's real browser on the Mac has to be a
   first-class way to capture a page.
3. **"Reliable" has to mean "never silently wrong."** On the OpenAI page, all three extractors
   tested (Defuddle, Readability, trafilatura) dropped both diagrams without warning, and two of
   them took an embedded tweet's author as the byline
   ([extractor comparison](#defuddle-wins-extraction-but-every-extractor-is-heuristic)). The
   command must detect challenge pages, compare what the page showed with what was kept, and
   fail or warn loudly.
4. **Which renderer to use is the one real
   [disagreement](#where-the-reports-disagreed).** grk, mus, and gem would reuse the
   pandoc/XeLaTeX `create` typesetter. cdx and cld would print a Bob-owned HTML template with
   Chromium. The evidence cuts both ways:
   - **Against LaTeX:** it hard-fails on SVG and WebP images (cld and gem both reproduced
     pandoc exit 43). It also renders emoji and CJK as missing glyphs, and numbers sections
     "0.1" because articles start at H2 ([pipeline comparison](#four-rendering-pipelines-compared)).
   - **For Chromium:** it handles all of that natively, renders about 10× faster, and the
     page-1 marker round trip through bob's `lopdf` 0.40 is verified.
   - **For LaTeX:** Highlights pulls **clean** quote text from LaTeX PDFs. It pulls **broken**
     quotes ("Hu et al. p ublished") from the Chrome-printed blog PDFs already in the vault.
   - **New finding (lead):** the text layer inside those broken PDFs is actually intact. mutool
     extracts "published", "spectrum", and "RAPTOR" cleanly. The damage happens when Highlights
     (via macOS PDFKit) reads those particular Chrome prints. It isn't an inherent property of
     Chromium-made PDFs, and nobody has tested whether a Bob-controlled template avoids it
     ([Highlights text quality](#highlights-text-quality-is-the-deciding-question)).
5. **Recommendation:** add a new subcommand, `bob highlights clip <URL>`
   ([recommended solution](#recommended-solution)).
   - A pinned `uv run --script` adapter, modeled on the existing `bob gkeep` adapter, handles
     capture, extraction, and rendering: Playwright drives Chromium, a vendored Defuddle bundle
     runs inside the page, a fidelity check compares the extraction with the page, and a
     Bob-owned print template renders the PDF.
   - Rust keeps the Highlights contract: target planning, collision refusal, the marker (now
     with `id`, `source_url`, `author`, `published`, `captured`), and atomic install.
   - **The renderer choice depends on a roughly one-day
     [spike on the Mac](#the-gating-spike-on-the-mac):** highlight passages in
     template-rendered PDFs and check the quote text. If the quotes come out clean, ship the
     Chromium template. If not, swap only the render stage for the fallback described here:
     Defuddle Markdown, then normalize images, then the existing pandoc/XeLaTeX path.

![Infographic of the proposed web URL to reference PDF workflow: capture a URL or saved browser HTML, run Defuddle extraction with a fidelity check, write a reader PDF with a provenance marker to xlib/blogs, and let the Mac's bob highlights scan create lib/blogs PDFs and ref/blogs notes; reliable means never silently wrong (blocked pages, missing content, broken highlights); a Mac test of clean Highlights quotes chooses between the Chromium reader template and pandoc plus XeLaTeX; captures keep source URL, capture date, author, and publication date, refuse duplicates, protect annotated PDFs, and download direct PDFs without re-rendering; build bob highlights clip URL](web_url_reference_pdf_capture_infographic.png)

## Is this a good idea

**Yes.** The Highlights loop (PDF → `ref/` note → `^ref` lifecycle task → annotation sync) is
one of the vault's strongest workflows. Web articles are under-represented in it only because
getting them in is manual and produces ugly output
([today's manual flow](#how-web-pages-reach-the-vault-today)). One-command capture would:

- give each article an immutable snapshot that survives link rot;
- record provenance in standard fields instead of ad hoc ones;
- cut PDF size by 3–6× compared with today's Chrome prints;
- let agents feed the library ("save the sources you cited").

PDF is the right artifact for this vault, because Highlights annotates PDFs and the `ref/`
pipeline is keyed off `lib/` PDFs. A Markdown-only clip, such as Obsidian Web Clipper, would
skip that loop. It's a good companion, not a replacement.

### Critique of the plan's framing

What's wrong or underspecified in the framing (see also the
[requirement adjustments](#requirement-adjustments)):

1. **"Convert a URL to a PDF" mixes up two different products.** One is a facsimile of the
   website (navigation, banners, the site's own print CSS). The other is a re-typeset copy of
   the article. "Beautiful and readable" means the second. Reader mode should be the default,
   and printing the whole page should be an explicit choice, never an automatic fallback.
2. **"Creates a reference note" puts the boundary in the wrong place.** `create` never writes
   `ref/`; `scan` does, on the Mac, after the `xlib` bridge has run
   ([how create and scan work](#how-create-and-scan-work)). If the capture command wrote the
   note itself, it would race scan, skip the intake and collision guards, and write a wrong
   `source_pdf` path until a later scan fixed it.
3. **"Reliable" can't mean "works for every URL."** Bot walls, JavaScript apps, paywalls, and
   video-first pages are normal cases, not edge cases. Reliability has to mean deterministic
   success on ordinary article pages, plus a specific, actionable failure for everything else.
   It must never produce a PDF of a Cloudflare interstitial or a two-paragraph teaser.
4. **"Beautiful" is cheap; "trustworthy" isn't.** The prettiest pipeline (reader mode) is also
   the one that silently dropped the OpenAI diagrams. Beauty comes from a good template. Trust
   needs the fidelity check, metadata hygiene, and an editing loop.
5. **Pages already change in the vault's current flow, and nothing records it.** A snapshot of a
   mutable page needs `source_url` plus a capture date, both in the note and printed visibly in
   the PDF.

## Requirement adjustments

These are deliberate changes to the request.

> **A1. The reference note is created by the existing `scan`, not by the new command.**
> The command writes `xlib/blogs/<slug>.pdf`, and the Mac's 15-minute scan (or a manual
> `bob highlights scan` / `bob_xlib_pull`) creates `ref/blogs/<slug>.md`. This keeps one note
> generator and works unchanged for captures made on agent hosts. A Mac-only `--scan`
> convenience can come later, delegating to the same scan code. Never scan on athena or apollo,
> because that would bypass the bridge to the Mac.

> **A2. "Beautiful and readable" means reader-mode re-typesetting of the article.** Printing the
> whole page (`--mode page`) is an explicit escape hatch for layouts extraction can't represent.
> It's never an automatic way to hide an extraction failure.

> **A3. "Reliable" means "never silently wrong," not "works for every URL headlessly."**
> Fail closed on challenge pages, login walls, and thin extractions (under about 300 words). Warn
> when large images or code blocks the page showed were dropped. Every failure names the next
> step (`--html`, `--from-chrome`, `--mode page`).

> **A4. Provenance is mandatory.** Stamp `source_url`, `author`, and `published`, which are
> already standard fields, plus a new **`captured: YYYY-MM-DD`**. Add `captured` to
> `COMMON_USER_FIELDS` so edits sync both ways. Omit a field rather than write a wrong one. Print
> the source URL and capture date in the PDF's masthead too. *(The reports proposed `captured`,
> `captured_at`, `retrieved_at`, and `date_saved`; pick one and never mint a parallel `url` key.)*

> **A5. URL captures get their own defaults.**
> - `ref_type` is **`blogs`**, which matches the existing `lib/blogs/` and `ref/blogs/`. Neither
>   `chat` nor a new `web` directory, which would split four existing refs. Use `-t docs` and
>   similar for other kinds.
> - `id` is always stamped.
> - The slug is the URL's last meaningful path segment in the vault's snake_case style
>   (`open_source_codex_orchestration_symphony`), falling back to the title for `index`-style
>   paths, with `--name` to override.

> **A6. Library PDFs are immutable, and captures are deduplicated by URL.** Highlights
> annotations depend on pagination. Never replace an annotated library PDF, not even with
> `--force`. If a ref already carries the same normalized `source_url`, report it and stop. A
> recapture is a later, explicit feature that makes a new versioned snapshot.

> **A7. URLs that already point at a PDF are downloaded and stamped, not re-rendered.**

> **A8. No third-party renderer by default.** Jina Reader works on the OpenAI page, but it sees
> every URL, is rate-limited, and is another dependency. At most it's a later, explicit opt-in.

> **A9. No second copy of the article text in the vault in v1.** gem proposed storing the
> extracted Markdown in `~/bob/sources/web/`, to make article bodies searchable. That's a real
> gap (see [environment facts](#environment-facts-that-affect-the-design)), but a second copy
> raises questions about which copy is canonical and adds linter and Dataview noise. It also
> must never sit at `<stem>.md` beside the PDF, which is the Highlights sidecar slot. In v1,
> `--keep-source DIR` writes `article.html`, `article.md`, and the assets **outside** the vault
> for debugging and hand fixes. If full-text search matters later, first evaluate indexing the
> PDFs in Obsidian (Omnisearch with Text Extractor), so the text isn't duplicated.

> **Out of scope for v1:** headless capture of logged-in or paywalled pages (use the
> real-browser path), multi-page article stitching, X threads, video transcripts, stealth or
> bot-bypass, and guessing `parent` from the domain.

## What exists today

Everything in this section was verified.

### How create and scan work

This covers `bob highlights create` and `scan`.

- `create <MD_FILE>` renders through pandoc and XeLaTeX (`src/native/highlights_ref/create.rs`):
  - layout: `--toc --toc-depth=3 --number-sections`, DejaVu fonts, 0.85in margins;
  - code: an `fvextra` preamble wraps code blocks, and a Lua filter adds break points in long
    inline code;
  - marker: `lopdf` adds a page-1 `/Text` marker (`status`, `parent`, `title`, plus `id` with
    `-i`), then the file is installed atomically.
  - The default target is `xlib/<ref_type>/<stem>.pdf`, and the default `ref_type` is `chat`.
  - It refuses an existing same-stem `.md` or `.textbundle`, because Highlights would treat that
    file as the sidecar. It also refuses an occupied library destination, and an existing target
    without `--force`.
- `compose_marker` writes only `status`, `parent`, `title`, and `id`. However, `source_url`,
  `author`, and `published` are already **standard synced user fields** (`COMMON_USER_FIELDS`
  in `mod.rs`; `docs/highlights-ref-sync.md`). Unknown marker keys round-trip into frontmatter.
  So a web capture only has to stamp these keys, and scan carries them into the note with no new
  note-writing code.
- `scan` moves `xlib/<rel>` to `lib/<rel>` and writes `ref/<rel>.md`. The note gets:
  - frontmatter: `type: "[[ref]]"`, `ref_type`, `source_pdf`, hashes, and `pipeline_version`;
  - the lifecycle line `- [ ] #task #ref [[lib/…pdf]] #hide ^ref`;
  - a managed `<!-- highlights:begin/end -->` region.

  (gem's sample note, with `#pdf #type/ref`, `^reading-task`, `note_type`, and `url:`, doesn't
  match what scan actually writes.)
- **Delivery bridge** (`docs/vault-git-sync.md`): `xlib/` is gitignored. athena and apollo each
  keep their own queue. On the Mac, a 15-minute cron runs `scan`, whose pre-scan hook
  `bob_xlib_pull` rsyncs both queues over and then scans. The `lib/*.pdf` files **are**
  git-tracked; vault-sync refuses files of 95 MiB or more and warns at 50 MiB.
- **Precedent for a non-Rust helper:** `bob gkeep` runs the embedded `scripts/gkeep_adapter.py`
  through `uv`, with a JSON protocol and a `BOB_GKEEP_ADAPTER` override as the test seam
  (`src/native/gkeep/adapter.rs`). `bob highlights doctor` already reports whether pandoc is
  available.

### How web pages reach the vault today

Bryan prints the page from Chrome on the Mac, renames it, drops it into `lib/blogs/`, and types
a marker by hand. The result is **4 blog refs against 236 `create`-made chat PDFs.**

| PDF | Size / pages | Defects |
| --- | --- | --- |
| `lib/blogs/netclode.pdf` | **20 MB** / 64 p | no title or URL in the marker; note titled "netclode" |
| `lib/blogs/harness_for_rsi.pdf` | 3.9 MB / 28 p | browser date/URL header, site navigation |
| `lib/blogs/build_with_muse_code.pdf` | 0.8 MB / 15 p | alt-text junk ("Hero image") on page 1 |
| `lib/blogs/steve_kinney_agent_memory.pdf` | 0.7 MB / 21 p | ad hoc `url:` key, not `source_url`; corrupted quotes (see [Highlights text quality](#highlights-text-quality-is-the-deciding-question)) |

By contrast, the chat PDFs from `create` are about 100–200 KB, use the xdvipdfmx producer, and
yield clean quotes.

### Environment facts that affect the design

- **apollo:** no Chrome or Chromium, and no Playwright cache (lead checked). `pandoc` 3.1.3,
  `xelatex`, `mutool`, `node`, and `uv` are present. `rsvg-convert` is absent, and so is
  `pdftotext`.
- **athena:** `~/bin/chrome` wraps `/usr/bin/google-chrome-stable`, which isn't installed (grk).
- **Mac:** Google Chrome is installed; the blog PDFs above came from Chrome 148–151 on macOS.
  Whether pandoc and XeLaTeX are installed there is **unverified**. chezmoi has no Brewfile that
  records it.
- bob-cli has no HTTP client and no async runtime (`Cargo.toml`).
- The Obsidian vault has no plugin that indexes PDF text (no Omnisearch or Text Extractor). So
  the body of a PDF can't be searched in Obsidian until it's highlighted.

## What the evidence shows

### Fetching the example URL blocks every headless client

| Channel (OpenAI Symphony URL) | Result | Who tested |
| --- | --- | --- |
| `curl`, default or Chrome-like UA | **403**, `cf-mitigated: challenge`, about a 10 KB body ("Enable JavaScript and cookies to continue") | cdx, grk, mus, gem, cld, lead |
| `curl` with gem's exact Mac Chrome/129 UA, and with a Chrome/141 UA | **403**, 10,162 bytes both times | lead (re-test of gem's claim) |
| Playwright `chrome-headless-shell`, and full Chromium in new-headless mode with `AutomationControlled` disabled | **403** "Just a moment…" | cld |
| `defuddle parse <url>`, Claude WebFetch | **403** | cld |
| `openai.com/news/rss.xml` | 200, metadata only (title, `pubDate` 2026-04-27) | cld, lead |
| Jina Reader `r.jina.ai` | 200; `X-Return-Format: html` returned the rendered DOM | cld |
| Lil'Log, stanislas.blog (netclode) in headless Chromium | load fine | cld |

**gem's claim doesn't reproduce.** gem reported that a Mac Chrome UA let Defuddle extract the
full article. From apollo, the lead re-ran that exact UA and got a 403 challenge every time.
Treat it as a one-off (a different egress IP or a transient Cloudflare state), not as a
strategy. Two more points from cld:

- When cld replayed the captured OpenAI DOM at its real origin from apollo, 117 static-asset
  requests also got a 403. Faithful page printing is impossible headlessly on bot-walled sites.
- cld didn't use stealth or anti-detection plugins and recommends against them: they're an arms
  race, fragile, and at odds with site terms.

### Defuddle wins extraction but every extractor is heuristic

cld ran a direct comparison on the same rendered OpenAI DOM:

| Extractor | Author | Published | Diagrams (page has 2) | Embedded ~7k-word `SPEC.md` |
| --- | --- | --- | --- | --- |
| **Defuddle 0.19.4** (Obsidian Web Clipper's engine) | ✓ | ✗ (took an embedded tweet's date) | **0** | ✓ kept |
| Mozilla Readability 0.6.0 | ✗ (tweet author) | none | **0** | ✗ dropped |
| trafilatura | ✗ (tweet author) | ✓ | **0** | ✗ dropped |

On friendlier pages, Defuddle was excellent:

- **Lil'Log:** 18 of 18 images, plus MathJax converted to 42 native MathML elements.
- **netclode:** 18 images and 17 code blocks.

cdx (vendor upstream Readability) and grk (the `legible` Rust Readability port) recommended
Readability-family extractors, but without a comparison like this. The only head-to-head data
favors Defuddle. It needs three additions:

- **metadata layering:** JSON-LD and `article:*` meta first, then Defuddle, then a visible date
  near the H1, ignoring any candidates inside embeds;
- **overrides:** `--title`, `--author`, `--published`;
- **a fidelity check** that compares the page with the extraction (see the
  [pipeline](#pipeline)).

### Four rendering pipelines compared

The comparison is cld's; gem reproduced the LaTeX failures.

![The same Lil'Log article through four pipelines: A current Chrome print, B headless page print, C Defuddle Markdown to pandoc/xelatex, D Defuddle to Chromium reader template](url_to_highlights_pdf_compare__cld.png)

| Pipeline | Lil'Log | netclode | OpenAI (DOM via Jina) | Notes |
| --- | --- | --- | --- | --- |
| A. Chrome Print-to-PDF (current flow) | 28 p, 3.9 MB | 64 p, **20 MB** | works only in the real browser | browser header and footer, nav, collapsed TOC |
| B. Headless print of the live page | 31 p, 3.5 MB | 60 p, 19 MB | blocked or unstyled | `<details>` printed collapsed |
| C. Defuddle Markdown → existing `create` | 23 p, **22 s** | — | 32 p, 0.1 MB, **no images** | **SVG and WebP abort the whole render (exit 43)**; emoji and CJK become tofu; "0.1 / 0.10" numbering |
| D. Defuddle → Chromium Bob template | 25 p, **1.7 s** | 53 p, **3.3 MB** | 31 p, 2.3 MB, 2 diagrams rescued | SVG, WebP, MathML, CJK, and tables native; PDF outline; `n / N` footers |

**What the comparison shows:**

- **LaTeX fails loudly, and the failures are fixable, but they're a long tail.** Each one needs
  its own fix:
  - images: WebP → PNG/JPEG, and SVG → PDF/PNG via `resvg` or `cairosvg`; `rsvg-convert` is
    absent on apollo;
  - glyphs: font fallback chains for emoji and CJK;
  - headings: `--shift-heading-level-by` or no numbering;
  - structure: lossy HTML → Markdown conversion for complex tables, `<details>`, and figures.
- **Chromium renders all of these natively.** The Chrome CLI alone produces outline bookmarks
  (`--generate-pdf-document-outline`), and CSS margin boxes (Chrome 131+) produce `n / N` page
  footers.
- **Panel D has one template bug and one typography problem.** The template bug is a dek that
  repeats the first paragraph, which is fixable. The typography problem is justified,
  auto-hyphenated text, which matters for highlights (see
  [Highlights text quality](#highlights-text-quality-is-the-deciding-question)).

### Highlights text quality is the deciding question

This subsection carries the lead's new evidence.

grk's strongest argument against Chromium output is that **Highlights pulls broken quotes from
Chrome-printed PDFs**. The vault confirms it. The sidecar
`lib/blogs/steve_kinney_agent_memory.md` contains `Hu et al. p` / `ublished`, `spectru` / `m`,
`RAPTO` / `R`, and `stru` / `ctures`, and the ref note renders these as "p ublished". By
contrast, sidecars sampled from the 92 xdvipdfmx chat PDFs break lines only at word
boundaries, never inside a word.

**The lead's added check:** `mutool draw -F txt` on pages 1–3 of the same Steve Kinney PDF
extracts clean text: "2025, Hu et al. published", "spectrum", "RAPTORʼs", "structures enable
multi-hop". So:

- the PDF's text layer is correct. The words are split by how PDFKit, which Highlights uses,
  segments glyph runs in **these particular Chrome prints of live sites** (site webfonts,
  letter-spacing or kerning, justified text, drop caps; these causes are plausible but
  unverified);
- the evidence doesn't show that a Chromium-printed **Bob template** with controlled fonts would
  be damaged. It doesn't show that it would be clean either;
- mutool isn't a proxy for PDFKit, so Linux can't settle this. It can only be settled on the Mac
  in Highlights, and it is the gating test in [the gating spike](#the-gating-spike-on-the-mac).

Separately, three more text-layer hazards are proven, and the template must handle them:

- **Auto-hyphenation leaks into quotes.** cld counted 104 hyphenated line ends in 25 pages, and
  bob's healer joins `self-` + `improvement` into "selfimprovement". Fix: `hyphens: manual` and
  ragged-right text.
- **Invisible characters.** U+2060 word joiners appear in OpenAI's link text. Fix: strip
  U+200B–U+200D, U+2060, and U+FEFF during normalization.
- **Hidden content.** `<details>` elements and fixed-height scroll boxes print only their
  visible part. Fix: force them open and unclamp the scroll boxes.

### Size and marker compatibility

- **Image encoding drives size.** Chromium re-encodes WebP and PNG as lossless Flate. Localizing
  images as JPEG (≤1600 px, q≈82, with `srcset` and `<source>` stripped) lets them pass through
  as DCT: netclode drops from 20 MB to **3.3 MB** at full resolution (cld). SVG stays vector.
- **The marker survives a Chromium PDF.** cld stamped a page-1 marker containing `source_url`
  with `lopdf` 0.40.0 (bob's exact pin) on three Chromium PDFs; the PDFs were tagged and had an
  outline. `bob highlights marker` read it back verbatim, and the outline survived. **No new PDF
  plumbing is needed.**

## Where the reports disagreed

The table also shows how this report resolves each disagreement.

| Topic | Positions | Resolution |
| --- | --- | --- |
| **Renderer** | pandoc/XeLaTeX (grk, mus, gem) vs Chromium plus a Bob template (cdx, cld) | Chromium template **gated on the Mac test in [the gating spike](#the-gating-spike-on-the-mac)**. The LaTeX path is the defined fallback, and only the render stage changes. |
| **Plain fetch of the example** | gem: works with a Mac UA. Everyone else: 403. | 403. The lead's re-test of gem's exact UA failed. |
| **Extractor** | Readability vendored (cdx), `legible` Rust port (grk), Defuddle (cld, gem) | **Defuddle** run inside the page. It's the only one with comparative evidence. |
| **Browser control** | Rust CDP `headless_chrome` (cdx); shelling out to the Chrome CLI (grk); uv + Playwright adapter (cld); Node (gem) | **uv + Playwright adapter** (see [implementation shape](#implementation-shape)). It has an in-repo precedent and supports in-page injection, lazy-image scrolling, and request routing for `--html` replays. Node isn't needed, because the Defuddle bundle is injected into the page. The Chrome CLI can't scroll or inject. `chromiumoxide` brings in tokio. `headless_chrome`, which is synchronous, is the all-Rust alternative if a Python dependency is unwanted. |
| **Hard pages** | Fresh temporary profile, no auth (cdx); persistent dedicated Bob Chrome profile (grk); real-browser DOM via `--html`/`--from-chrome` (cld, gem); `--from-file` (mus) | Fresh temporary profile for headless captures. **Real-browser DOM** for hard pages. Reusing Cloudflare clearance cookies in a headless profile is fragile (clearance is tied to the browser and IP that solved the challenge), so it's not the main path. |
| **Command** | `create-url` (cdx, mus), `clip` (grk), `create <URL>` (cld), `ingest` (gem) | **`bob highlights clip <URL>`**: a sibling of `create` that shares its internals (see [command surface](#command-surface)). |
| **`ref_type`** | `blogs` (grk, mus, cld) vs `web` (cdx, gem) | `blogs` ([A5](#requirement-adjustments)). |
| **Source Markdown in the vault** | yes (gem); keep it somewhere (mus); defer (cdx); `--keep-source DIR` (cld) | Defer; `--keep-source DIR` outside the vault ([A9](#requirement-adjustments)). |
| **`--scan`** | yes (gem); Mac only (grk); later (cdx) | Later, Mac only ([A1](#requirement-adjustments)). |
| **Hash suffix on every filename** | always (cdx) | Only on collision. Deduplicate by `source_url` ([A6](#requirement-adjustments)). |

## Recommended solution

Build **`bob highlights clip <URL>`** as a capture front end to the existing Highlights intake:

1. **Capture** with headless Chromium in a fresh profile, or from Bryan's real browser (`--html`
   now, `--from-chrome` next). Download direct PDFs as they are.
2. **Extract** with vendored Defuddle run inside the page, with layered metadata, overrides, and
   a **fidelity check**. Fail closed on challenge pages and thin extractions.
3. **Render** with a **Bob-owned Chromium print template**: localized JPEG images, no
   auto-hyphenation, bundled fonts, an outline, and `n / N` footers. This holds **only if the
   one-day Mac spike shows clean Highlights quotes.** Otherwise render with the existing
   pandoc/XeLaTeX typesetter after image normalization.
4. **Stamp and install** with the existing Rust marker, collision, and atomic-install code. Stamp
   `id`, `source_url`, `author`, `published`, and `captured`, and default `ref_type` to `blogs`.
5. **Let the existing `scan` create `ref/blogs/<slug>.md`.**

Use a pinned `uv` + Playwright adapter for the browser work, following the `bob gkeep`
precedent. Keep Rust as the only owner of the Highlights contract. Don't print the live page by
default, don't write notes from the clip command, don't call hosted services, and treat the
OpenAI example as a real-browser acceptance test, not a `curl` problem.

### Command surface

Follows `cli_rules.md`: options sorted the way `create`'s help sorts them, a short alias for
every long option, and colored output. Options marked † are deferred to Phase 3 (see
[phasing](#phasing)).

```text
bob highlights clip [OPTIONS] [URL]

Arguments:
  [URL]  http(s) URL to capture; recorded as source_url (optional with --from-chrome)

Options:
  -A, --author <NAME>        Override the extracted author
  -b, --bob-dir <PATH>       Bob vault root; defaults to BOB_DIR or ~/bob
  -C, --from-chrome          † macOS: capture the front Chrome tab's rendered DOM and URL
  -d, --dry-run              Fetch and extract, then print plan, marker, metadata sources and fidelity report; write nothing
  -f, --force                Overwrite an existing intake PDF (never a library PDF)
  -H, --html <FILE>          Render an already-saved DOM (SingleFile, Save Page As); `-` reads stdin
  -k, --keep-source <DIR>    † Also write article.html, article.md and assets to DIR
  -l, --lib-dir <PATH>       Highlights PDF library
  -m, --mode <MODE>          † reader (default) | page
  -N, --name <STEM>          Output filename stem [default: snake_case of the URL slug]
  -o, --output <PDF>         Complete path for the generated PDF
  -P, --parent <NOTE>        Marker parent [default: obsidian_ref]
  -p, --published <DATE>     Override the extracted publish date (YYYY-MM-DD)
  -r, --ref-dir <PATH>       Reference note output directory
  -s, --status <STATUS>      Lifecycle status [default: ready]
  -T, --title <TITLE>        Override the extracted title
  -t, --ref-type <DIR>       Library subdirectory [default: blogs]
  -x, --xlib-dir <PATH>      Highlights PDF intake directory
```

Why a separate subcommand rather than `create <URL>`:

- `create`'s positional argument and help are Markdown-shaped.
- The URL-only options (`-A -C -H -k -m -N -p -T`) would roughly double `create`'s help.
- Clip's failure modes (network, bot walls, extraction) are different.

The code is still shared: clip calls `create`'s planner, collision checks, marker composer, and
installer. Avoid tuning flags (timeouts, Readability thresholds, Chrome arguments); those are
implementation policy, not a CLI contract.

Example output:

```text
$ bob highlights clip https://lilianweng.github.io/posts/2026-07-04-harness/ -N harness_for_rsi
ok created Highlights-ready web PDF
pdf: ~/bob/xlib/blogs/harness_for_rsi.pdf
title: Harness Engineering for Self-Improvement
author: Lilian Weng · published: 2026-07-04 · captured: 2026-10-01
source_url: https://lilianweng.github.io/posts/2026-07-04-harness/
pages: 25 · images: 18/18 · size: 3.7 MB · fidelity: ok
next: bob highlights scan
```

### Pipeline

Capture, extraction, and rendering are separate stages that can be swapped independently.

1. **Validate.**
   - Accept only `http(s)`. Reject credentials embedded in the URL.
   - Reject loopback, link-local, and private-network destinations, including redirect targets.
   - Run the Rust planner first (target, collisions, dedupe by `source_url`), so no time is spent
     rendering into a refused target.
2. **Capture** (adapter), in this order:
   - **`--html FILE`** (SingleFile or Save Page As), or **`--from-chrome`** (AppleScript
     `execute javascript` on the front tab). The `--from-chrome` route needs Chrome's *Allow
     JavaScript from Apple Events*, which is a security trade-off. `--html` replays are served at
     the real URL through Playwright request routing, so relative links and images resolve.
   - **Otherwise, headless Chromium** with a fresh temporary profile and the sandbox **on**.
     Playwright defaults Linux Chromium to `--no-sandbox`, so set `chromium_sandbox=True`.
     Downloads and popups are blocked.
     - Readiness is bounded: `DOMContentLoaded`, then a short settle, then polling for an article
       candidate, then capped waits for `document.fonts.ready` and images. Don't wait
       open-endedly for `networkidle`.
     - Before extraction, scroll the page to trigger lazy images, set `img.loading="eager"`, and
       open every `<details>`.
   - **If the response is `Content-Type: application/pdf`,** download it and skip to step 6
     ([A7](#requirement-adjustments)).
   - **Challenge detection** covers "Just a moment…", `#challenge-error-text`, a 403 or 503 with
     Cloudflare markers, a tiny body, and login-wall phrases. On detection, exit nonzero with no
     PDF and print: *"blocked by bot protection; open the page in Chrome and rerun with
     `--from-chrome`, or save it and pass `--html`."*
3. **Extract.** Inject a vendored, pinned Defuddle bundle (MIT, about 770 KB, includes the math
   pipeline) and run it inside the page. Apply metadata layering, then the overrides. Sanitize the
   result with an allowlist (no scripts, event handlers, iframes, forms, or `javascript:` URLs).
   Defuddle, like Readability, is not a sanitizer.
4. **Fidelity check.** Before extraction, record:
   - large media below the H1 (300 px wide or more, excluding embeds);
   - `<pre>` blocks;
   - visible word count.

   Then compare these with what extraction kept, and print warnings in both human and JSON
   output. For example: `warning: page showed 2 large images below the title; extraction kept 0
   (try --mode page or --keep-source)`. Phase 3 adds *image rescue*: dropped images are
   re-inserted after the nearest surviving text block, which would have fixed the OpenAI
   diagrams.
5. **Normalize and render (reader mode).**
   - **Links and text:** absolutize URLs; strip zero-width characters and "(opens in a new
     window)" suffixes; drop a leading heading that repeats the title; unclamp scroll boxes.
   - **Images:** localize each one (`currentSrc` or the largest `srcset` candidate). Downscale to
     1600 px at most, convert rasters to JPEG q≈82, keep SVG, skip images under 64 px, and strip
     `srcset` and `<source>`.
   - **Template masthead:** site · title · short dek (only if it isn't a prefix of the body) ·
     byline · published · source URL · captured.
   - **Template typography:**
     - text: serif body at 10.5–11 pt with 1.5 leading, a measure of about 70 characters,
       `text-align: left`, and `hyphens: manual`;
     - fonts: bundled OFL fonts so Mac and Linux output match;
     - blocks: `break-inside: avoid` on figures, and wrapped `pre` with `overflow-wrap:
       anywhere`;
     - page footer: margin boxes showing the short title and `n / N`.
   - **Print:** with `outline` and `tagged` on, the PDF's `/Title` and `/Author` set, and no
     browser header or footer.
6. **Stamp and install (Rust).**
   - Reuse `compose_marker` (extended with optional extra keys), `embed_marker`, and
     `atomic_save_pdf`.
   - The marker carries `status`, `parent`, `title`, `id`, `source_url`, and, when known,
     `author`, `published`, and `captured`.
   - Print `create`'s success block, then let scan do the rest.

### Implementation shape

- **`scripts/web_capture_adapter.py`**, a PEP 723 script:
  - **Dependencies:** pinned `playwright` and `pillow`, plus `[tool.uv] exclude-newer`. It's
    embedded in the binary and run through `uv run --quiet --script`.
  - **Protocol v1:** one JSON request on stdin, one JSON response on stdout, logs on stderr.
  - **`ping` op:** reports versions, the browser path, and fonts.
  - **`capture` op:** takes `{url, html_path?, mode, out_pdf, workdir, overrides,
    keep_source_dir?}` and returns `{title, author, published, site, word_count, pages,
    warnings, fidelity, blocked?}`.
  - **`BOB_WEB_ADAPTER`** replaces the `uv run` invocation, the same way `BOB_GKEEP_ADAPTER`
    does; it's the Rust test seam.
- **Rust:**
  - new file `src/native/highlights_ref/clip.rs`;
  - factor the planner, marker, and installer out of `create.rs` into shared helpers, and give
    them a "stamp an already-rendered PDF" entry point, which direct-PDF URLs also use.
  - Don't over-generalize. Markdown keeps pandoc/XeLaTeX; only target, marker, install, and
    report are shared.
- **Browser provisioning:**
  - **Mac:** use the installed Chrome (`channel="chrome"`), no download.
  - **Linux:** `doctor` prints the exact `playwright install chromium-headless-shell` command
    (about 115 MB, into a bob-owned cache), or `BOB_CHROME` points at a system Chromium. No
    surprise auto-downloads.
  - **SASE agent hosts:** point `TMPDIR` and `--user-data-dir` at a short path. SASE's deep
    per-agent `TMPDIR` made full Chromium abort with "Socket path too long" (cld).
- **`bob highlights doctor`** gets rows for uv, the adapter ping, the browser, and fonts. A
  missing browser is a warning, because people who only run `create` don't need one.

### The gating spike on the Mac

Settle the renderer on the Mac first; the spike takes about a day.

Before building the MVP, render three articles: Lil'Log, netclode, and the OpenAI post captured
from real Chrome. Render each through:

- **(a)** a prototype of the Chromium Bob template;
- **(b)** Defuddle Markdown → image normalization → the existing `create`;
- **(c)**, as a zero-code baseline, Safari Reader → File → Export as PDF.

Stamp markers, run scan, and in Highlights make about 10 highlights per PDF. Make them cross line
breaks, links, italics, inline code, and image captions. Then compare the quote text in the
sidecars and ref notes with the source.

- **Pass:** (a) produces no split or dropped words. **Ship the Chromium template.**
- **If (a) fails:** retry with `font-kerning: none`, `font-variant-ligatures: none`,
  `letter-spacing: normal`, and system fonts instead of bundled ones. If it still fails, **ship
  (b)**. The adapter then returns sanitized Markdown plus localized PNG/JPEG/PDF images, Rust
  calls the existing pandoc path with `--shift-heading-level-by=-1` (or without
  `--number-sections`), and emoji and CJK font fallbacks are added. Confirm first that pandoc and
  XeLaTeX are installed on the Mac.
- Either way, capture, extraction, the fidelity check, the CLI, and the marker contract are the
  same. The spike only picks the render stage.

### Phasing

| Phase | Scope |
| --- | --- |
| **0: now, no code** | For simple static blogs: `npx defuddle parse <url> --md -o /tmp/x/<slug>.md`, then `bob highlights create /tmp/x/<slug>.md -t blogs -i`. Expect failures on SVG/WebP and on bot-walled sites. When stamping markers by hand, use `source_url`, not `url`, and migrate the Steve Kinney note's `url:` key. |
| **1: spike and refactor** | [The gating spike](#the-gating-spike-on-the-mac) on the Mac. In Rust, extract the shared stamp-and-install helper and add extra marker keys plus `captured` to the standard fields, with tests that stamp a fixture PDF. |
| **2: MVP** | Adapter, headless capture, Defuddle, fidelity warnings, the chosen renderer, challenge detection, `--html`, `--name`, the metadata overrides, `--dry-run`, direct-PDF URLs, dedupe by `source_url`, doctor rows, and fake-adapter tests. |
| **3: real browser and escape hatches** | `--from-chrome`, `--mode page` (live print with cleanup CSS and the same image recompression), image rescue, `--keep-source`, small per-host rules for repeat offenders such as openai.com, and a Mac entry point (a Shortcuts or Raycast hotkey, or a Bob Mac Capture action) that **spawns `bob highlights clip`**. That entry point is consistent with `decisions:mac-capture-is-a-thin-client`. |
| **Later, only if needed** | Mac-only `--scan`, an opt-in `--via jina`, recapture/versioning, and PDF full-text search. |

### Tests

- **Rust (fake adapter, no network, no Chrome):**
  - planning and defaults (`blogs`, `id`, snake_case slug);
  - marker keys round-trip through `bob highlights marker`;
  - collisions and the never-write-a-sibling-`.md` rule;
  - dry-run, the blocked-page error, and the direct-PDF branch;
  - dedupe by `source_url`;
  - the `--output`/`--ref-type` conflict.
- **Adapter `--self-test`** on checked-in DOM fixtures: Lil'Log (math, images), netclode (code,
  JPEG recompression), OpenAI (embed metadata, dropped diagrams), a challenge page, and a hostile
  document.
- **Live sites as non-blocking smoke tests only.** Bot policies change.
- **One manual Mac acceptance pass per renderer change:** open the PDF in Highlights, highlight
  across line breaks, run scan, and check the note's quote text and frontmatter.

### What not to build

- Writing `ref/` notes from clip.
- Printing the live page by default.
- Stealth plugins.
- Reusing Bryan's everyday Chrome profile. Since Chrome 136, remote debugging is refused on the
  default profile anyway, and the profile exposes cookies and credentials.
- `wkhtmltopdf`. It's installed on apollo, but it was archived in 2023 and uses 2012-era WebKit.
- WeasyPrint. It runs no JavaScript and adds a new native stack.
- tokio-based CDP crates.
- Hosted renderers by default.
- Extracted Markdown beside the PDF.

### Risks and limits

- **The Highlights text layer** is the biggest unknown. [The gating
  spike](#the-gating-spike-on-the-mac) settles it before the rest is built.
- **Extraction will keep missing things on some sites.** The fidelity warnings, `--mode page`,
  and per-host rules contain it; they don't eliminate it.
- **Bot walls drift.** Headless success rates will change over time. Capturing from the real
  browser is the durable answer, and it's legitimate because Bryan is saving what he can already
  see.
- **Running a browser on untrusted pages is a real attack surface.** Mitigations: the sandbox on,
  a temporary profile, the private-network block, HTML sanitization, a CSP in the template, and
  hard caps on time, DOM size, image bytes, page count, and PDF bytes.
- **`--from-chrome` needs a global Chrome toggle** that lets any app with Apple Events permission
  run JavaScript in tabs. SingleFile → `--html` avoids that.
- **Git size.** Use JPEG localization; never print raw page images losslessly. Vault-sync refuses
  files of 95 MiB or more.
- **Upkeep:** keep Playwright, Defuddle, and the fonts pinned, and re-run the spike checklist
  whenever the template changes.
- **Copyright:** snapshots stay in the private vault, for personal reference only.

### Open questions for Bryan

1. **Page size:** Letter, to match the existing PDFs, or a narrower page for reading on an iPad
   in Highlights?
2. **Look:** are you fine with web refs looking different from the LaTeX research PDFs? That
   difference is a useful hint about where a PDF came from.
3. **Default `parent`** for web refs: `obsidian_ref`, or a new `blog_ref` / `web_ref` hub? The
   existing blog refs use `sase_ref` and `memory_ref`.
4. **Where to clip:** is Mac-only clipping enough, or should athena and apollo get a Chromium
   install so agents can clip static pages?
5. **`--from-chrome` vs SingleFile:** are you OK enabling Chrome's *Allow JavaScript from Apple
   Events*, or would you rather save pages with SingleFile and pass `--html`?
6. **Jina:** is an explicit `--via jina` opt-in ever acceptable, given that a third party sees
   the URL?

## Report details and sources

### About this report

- **Date:** 2026-10-01
- **Lead researcher:** consolidation of five independent reports (`__cdx`, `__cld`, `__grk`,
  `__mus`, `__gem`, all in this directory) plus the lead's own verification on apollo.
- **Question:** What's the most reliable way to turn a web URL (for example
  `https://openai.com/index/open-source-codex-orchestration-symphony/`) into a beautiful,
  readable PDF that becomes a reference in `~/bob/`, with a note under `~/bob/ref/`, in the
  spirit of `bob highlights create -i`? Is it a good idea, what would change, and what should be
  built?

### Researcher reports

These are all in this directory:

- `web_url_reference_pdf_capture__cdx.md` (security, immutability, readiness policy, Chrome PDF
  options);
- `__cld.md` (fetch, extractor, and renderer experiments; size study; marker round trip; figure
  `url_to_highlights_pdf_compare__cld.png`);
- `__grk.md` (vault evidence for broken quotes, `create` internals, command boundary);
- `__mus.md` (provenance gap, requirement scoping, fallback ladder);
- `__gem.md` (XeLaTeX SVG/WebP crash reproduction, the case for searchable Markdown, tiered
  capture).

### Lead verification on apollo

All of these checks ran on 2026-10-01:

- `curl` of the OpenAI URL with Chrome/129 and Chrome/141 Mac UAs: 403, 10,162 bytes. RSS: 200.
- `mutool draw -F txt` on `~/bob/lib/blogs/steve_kinney_agent_memory.pdf` pages 1–3 (clean
  text) vs its Highlights sidecar `lib/blogs/steve_kinney_agent_memory.md` (split words).
- Quote text sampled from the 92 `~/bob/lib/chat/*.md` sidecars: no mid-word splits.
- `mutool info` on the blog PDFs.
- Tooling check: no Chrome or Chromium, no Playwright cache, no `rsvg-convert`; pandoc, xelatex,
  mutool, node, and uv present. Vault plugins: no PDF text indexer.
- Code and docs: `src/native/highlights_ref/{create,mod}.rs`, `src/native/gkeep/adapter.rs`,
  `docs/highlights-ref-sync.md` (standard synced fields; unknown keys round-trip),
  `docs/vault-git-sync.md` (xlib bridge, 95/50 MiB limits), `bob highlights create -h`,
  `sase/memory/cli_rules.md`, `decisions:mac-capture-is-a-thin-client`.

### External sources

- [kepano/defuddle](https://github.com/kepano/defuddle) · [defuddle.md](https://defuddle.md/)
- [Obsidian Web Clipper](https://obsidian.md/clipper)
- [Mozilla Readability](https://github.com/mozilla/readability#readme) (not a sanitizer)
- [Chrome headless CLI](https://developer.chrome.com/docs/automation-and-testing/headless-cli)
- [Playwright `page.pdf`](https://playwright.dev/docs/api/class-page#page-pdf) ·
  [Playwright browsers](https://playwright.dev/docs/browsers)
- [`headless_chrome` crate](https://docs.rs/headless_chrome/latest/headless_chrome/)
- [CSS paged media (MDN)](https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Paged_media) ·
  [CSS page margin boxes](https://doppio.sh/guide/css-page-margin-boxes)
- [Cloudflare Browser Run PDF endpoint](https://developers.cloudflare.com/browser-run/quick-actions/pdf-endpoint/)
  (always identifiable as a bot)
- [Jina Reader](https://jina.ai/reader/)
- [SingleFile CLI](https://github.com/gildas-lormeau/single-file-cli)
- [percollate](https://github.com/danburzo/percollate) (prior art: Readability + Puppeteer →
  PDF)
- [wkhtmltopdf](https://github.com/wkhtmltopdf/wkhtmltopdf) (archived)
- [Chromium AppleScript support](https://www.chromium.org/developers/applescript/)
- [Safari Reader → Export as PDF](https://www.makeuseof.com/how-to-save-webpage-as-pdf-safari-mac/) ·
  [MacMost: turn anything into a PDF](https://macmost.com/how-to-turn-almost-anything-into-a-pdf-on-a-mac.html)
