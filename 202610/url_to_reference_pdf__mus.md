# URL → Reference PDF for the Bob Vault: Research and Recommendation

Researcher: mus (`__mus`). Independent report; conclusions are my own.

Request: a reliable way to turn a web URL (e.g.
`https://openai.com/index/open-source-codex-orchestration-symphony/`) into a
beautiful, readable PDF usable as a Highlights reference PDF in `~/bob/`, with a
new reference note in `~/bob/ref/`, inspired by `bob highlights create -i`
(which does this for local Markdown files).

## 1. How `bob highlights create` works today (verified from source)

I read `src/native/highlights_ref/create.rs` (`plan_create`, `render_and_install`,
`embed_marker`, `compose_marker`) plus `cli.rs`, `mod.rs`, `note.rs`, and
`docs/highlights-ref-sync.md`, and probed the environment. The facts that matter:

- **Render pipeline.** `create <MD_FILE>` renders Markdown with
  `pandoc --standalone --toc --toc-depth=3 --number-sections
  --pdf-engine=xelatex --highlight-style=tango`, DejaVu font family,
  `geometry:margin=0.85in`, a bundled Lua filter that gives long inline code
  legal line-break points, and an `fvextra` preamble so fenced code blocks wrap
  instead of running off the page. Local images resolve via `--resource-path`
  pointed at the Markdown file's directory.
- **Highlights integration.** After pandoc renders, bob opens the PDF with
  `lopdf` and appends a standalone `/Text` annotation on page 1 containing the
  marker (`status`, `parent`, `title`, optional `id`). That marker is the entire
  contract `bob highlights scan/sync` uses to file the PDF and generate the
  `ref/` note. Because the marker is embedded with `lopdf` *after* rendering,
  **any** PDF can be made Highlights-ready, not just pandoc output.
- **Intake flow.** Default target is `<xlib-dir>/<ref-type>/<stem>.pdf`;
  `scan` moves it to `lib/<ref-type>/` and writes
  `ref/<ref-type>/<stem>.md` with pipeline frontmatter (`source_pdf`,
  `source_pdf_sha256`, marker hash, `pipeline_version`). Collision rules are
  strict: existing target, existing `<stem>.md` sidecar, and existing library
  destination all refuse without `--force` (a pre-existing `<stem>.md` is
  refused because scan would treat it as the annotation sidecar).
- **Environment (this Linux box).** `pandoc 3.1.3` and a TeX Live base are
  installed; `wkhtmltopdf` is installed; **no Chromium/Chrome exists**; the
  binary has **no HTTP client dependency** (`Cargo.toml`: chrono, clap, fs2,
  hex, lopdf, regex, rquickjs for dataview JS, serde, sha2, similar — no
  reqwest/ureq/curl bindings). So URL fetching is entirely new dependency
  surface.
- **Provenance gap.** `source_url` appears in `COMMON_USER_FIELDS` in `mod.rs`
  but `compose_marker` only writes `status`/`parent`/`title`/`id`. Today
  `create` records **no source URL, no retrieval date, no author** anywhere.
  A URL importer must add that; otherwise archived web PDFs are
  indistinguishable from local files and the original link rots silently.
- **Decisive fetch experiment.** `curl` against the motivating example URL
  returns **HTTP 403 (Cloudflare challenge)**, even with a full Chrome
  User-Agent string. A naive "GET the HTML and convert it" implementation
  fails on exactly the page that motivated this request. Any design must treat
  bot-walled pages as the normal case, not the edge case.

## 2. Critique of the plan: is this a good idea?

**Yes, with adjusted expectations.** The core instinct is right: the Highlights
loop (PDF in `lib/` → annotate → `ref/` note with managed body) is the vault's
reading workflow, and web articles currently have no on-ramp to it. Reusing the
`create` render path gives every archived article the same typography, TOC, and
marker contract as the rest of the library — visual consistency is a genuine
feature for a reference collection.

But four corrections are needed before anyone builds:

1. **"Beautiful and readable" and "faithful to the page" are opposing goals —
   pick readability.** A casual reader imagines the PDF looking like the blog.
   For a *reference* PDF the right target is the opposite: strip navigation,
   cookie banners, newsletter boxes, and site chrome; keep title, author, date,
   body text, code blocks, images, and links. That is article extraction
   (Readability-style), not screenshotting. State this in the requirements or
   the implementer will optimize for the wrong thing.
2. **"Reliable for any URL" is not achievable; scope it.** Observed failure
   classes: Cloudflare/bot-wall 403s (demonstrated above), JavaScript-rendered
   pages with empty static HTML, paywalls/logins, video/interactive-first
   pages, and link-rot of the live page afterward. The requirement should be
   "reliable for normal editorial article pages, with a graceful, explicit
   fallback for the rest" — not universal conversion.
3. **A web PDF without provenance is a liability.** Web content changes, moves,
   and gets paywalled. Every imported PDF must carry `source_url`,
   `retrieved_at`, and (when extractable) author/published date, surfaced in
   both the marker/frontmatter and the ref note body. This closes the gap noted
   in §1 and makes the archive auditable years later.
4. **Do not bypass the existing pipeline — extend it.** The worst outcome would
   be a second PDF renderer with different fonts, no TOC, and no marker. The
   new work should end at "produce a Markdown file plus metadata, then call the
   exact existing render-and-embed path." That keeps one visual standard and
   reuses all collision/scan/note machinery for free.

One thing I would explicitly **not** do: store the live URL as the reference
(e.g. a note containing only a link) instead of a PDF. Links rot, go
paywalled, and can't be highlighted in the Highlights app — which defeats the
stated purpose of the `ref/` workflow.

## 3. Options evaluated

### Option A — Fetch → Readability extraction → Markdown → existing pandoc pipeline (recommended)

Fetch the page over HTTPS, run an article-extraction algorithm (Mozilla
Readability family), emit clean Markdown with a metadata header, then feed it
through the *unchanged* `render_and_install` + `embed_marker` path. New code is
confined to "URL → Markdown + metadata + slug"; everything downstream is
reused, so output PDFs are typographically identical to today's library.

- Pros: single visual standard; TOC/bookmarks/marker/code-wrapping all
  inherited; no new renderer or browser dependency in the base case; Markdown
  intermediate is debuggable (`--dry-run` can print it); works fully offline
  after fetch.
- Cons: extraction is heuristic — drops complex layouts, embedded demos,
  tables, math, and captions on some pages; needs an HTTP client + extractor
  (new deps or a subprocess); **fails on bot-walled pages** like the example
  URL with a plain fetcher (§1 experiment), so it needs the §4 fallback story.
- Remote images need downloading + rewriting to local files so
  `--resource-path` resolves them; that is straightforward but must be
  designed in (rewrite `![alt](https://…)` → local `assets/` dir, with
  failures degrading to link-only rather than aborting).

### Option B — Headless Chromium `--print-to-pdf`, then embed marker via lopdf

Render the page in a real browser and print to PDF (works against Cloudflare
far more often than curl, preserves original styling), then reuse only the
`embed_marker` half of the pipeline.

- Pros: highest fidelity to the original page; sidesteps most bot-walls;
  handles JS-rendered content.
- Cons: **Chromium is installed on neither machine I can verify** (absent on
  this Linux box; MacBook status unknown — open question for implementer);
  print-CSS output of blog pages is usually *less* readable than an extracted
  article (headers/footers/cookie text baked in); output no longer matches the
  library's typography; page-1 marker embedding still works but TOC/bookmarks
  depend on the site; heavier, slower, and harder to make deterministic.
- Verdict: right as a **fallback mode** (`--mode print`), wrong as the
  default.

### Option C — wkhtmltopdf

Installed here, but it uses a decade-old WebKit: poor modern CSS, no ES6,
frequent rendering breakage, and the project itself recommends Chromium-based
tooling. Strictly worse than B on fidelity and worse than A on readability.
**Do not choose.**

### Option D — Raw HTML archive (SingleFile/monolith-style) as the artifact

Maximum fidelity, zero readability gain, unreadable in Highlights/Obsidian
PDF flows, and bypasses the whole `ref/` pipeline. Only makes sense as an
*additional* preservation copy, never as the reference PDF. Optionally save the
raw HTML next to the PDF for pages likely to be disputed — cheap insurance,
not the deliverable.

### Option E — Hosted reader proxy (e.g. Jina Reader-style HTTPS API)

Outsources fetching + extraction to a third party: one GET returns clean text,
no browser needed, often defeats bot-walls.

- Pros: tiny implementation, surprisingly robust.
- Cons: external service dependency for a personal archive tool; privacy (URLs
  of interest leak to a third party); rate limits/ToS changes; if it degrades,
  every import breaks at once. Acceptable as an *optional* `--via` fallback,
  not as the primary path.

### Option F — Markdown-only import, no PDF

Cheapest, but the Highlights app annotates PDFs and the `ref/` pipeline keys
off `lib/` PDFs. A markdown-only import orphans the article from the reading
workflow the request is explicitly about. Reject as the deliverable (though the
fetched Markdown should still be retained — see §5).

## 4. Requirement adjustments (explicit, as asked)

1. **Rename the deliverable's promise**: "URL → clean, consistently-styled
   reference PDF + ref note with provenance," not "URL → beautiful PDF of the
   page." (Justification: §2.1.)
2. **Scope reliability**: must succeed on standard editorial/article HTML;
   bot-walled, JS-app, paywalled, and video-first pages must fail *loudly with
   a named reason* and offer the fallback ladder (§5), never silently produce
   a 2-paragraph "article" from a challenge page. (Justification: 403
   experiment in §1.)
3. **Mandatory provenance fields**: `source_url`, `retrieved_at`, plus
   author/published-date when extractable, in marker/frontmatter and note.
   Requires extending `compose_marker`/note frontmatter — small schema change.
   (Justification: provenance gap in §1.)
4. **Default ref-type for web imports should be `blogs`** (matching the
   existing `lib/blogs/` + `ref/blogs/` convention), not `chat`; slug the
   filename from the article title with a domain/date disambiguator, and reuse
   the existing collision refusals for re-imports/dupes.
5. **Keep the fetched Markdown**: store it outside the `<stem>.md` sidecar
   path (which scan owns — writing there trips the collision guard), e.g.
   embedded in the ref note's unmanaged region or as `<stem>.source.md` after
   confirming scan ignores that suffix. It is the only debuggable record of
   what the extractor saw.
6. **No silent network writes on `scan`**: fetching must happen only in the new
   explicit command; `scan`/`sync` stay offline. (Keeps scheduled scans
   hermetic.)

## 5. Recommended solution

**New subcommand `bob highlights create-url <URL>` built as a thin front-end
to the existing `create` pipeline (Option A primary, B as fallback):**

1. **Fetch tier 1 (plain HTTPS, browser UA, timeouts, redirect + size caps).**
   On bot-wall/JS-shell signals (403/challenge text, trivially short
   extraction), abort with a specific error instead of archiving junk.
2. **Extract** with a Readability-class algorithm → title, byline, date, body.
   Download remote images to a staging dir, rewrite links local; image
   failures degrade to captioned links.
3. **Stage a Markdown file** (frontmatter: title/author/published/source_url/
   retrieved_at) in temp, derive slug from title, then call the **existing**
   `plan/render/embed` code unchanged — same pandoc flags, same Lua filter,
   same page-1 marker — plus the §4.3 provenance fields. Target
   `xlib/blogs/<slug>.pdf`; from there `scan`/`sync` behave exactly as today.
4. **Fallback ladder, explicit and ordered**: `--mode print` (headless
   Chromium `--print-to-pdf` + existing `embed_marker` — needs a MacBook
   Chromium-availability check first); `--via reader-proxy` (opt-in hosted
   extraction); `--from-file` (user saves the page/Markdown manually, still
   gets the full render + marker + note flow — this alone unblocks the
   motivating openai.com URL on day one).
5. **Record, don't guess**: `--dry-run` prints fetch status, extracted title,
   slug, target, and the staged Markdown path; re-running the same URL hits
   the existing collision refusal (correct dedupe semantics for free).

**Phasing.** Phase 1 (small, no new renderer risk): `create` gains provenance
fields + slug helper, and `--from-file` works end-to-end — usable immediately
even for Cloudflare-walled pages via manual save. Phase 2: integrated
fetch+extract (new HTTP/extractor dependency — note `Cargo.toml` currently has
no HTTP stack, so dependency choice is the main design decision; a spike
comparing a Rust extractor against shelling out to the repo's existing
`uv`-Python pattern from `scripts/gkeep_adapter.py` is warranted). Phase 3
(optional): Chromium print fallback after confirming availability on the
MacBook.

**Open questions for the implementer** (not blockers for Phase 1): Chromium
presence on the MacBook; whether `scan` ignores a `<stem>.source.md`
companion (verify before keeping source Markdown next to the PDF);
exact extractor crate choice; and the CLI-rules review in
`sase/memory/cli_rules.md` before adding the subcommand.

## 6. Bottom line

The plan is a good idea once rescoped: don't convert "the page" to PDF,
**ingest the article into the Highlights pipeline**. Implementation risk sits
almost entirely in fetching/extraction (proven hostile by the 403 on the
example URL), not in PDF generation — so keep all PDF generation exactly where
it is and put every new line of code on the URL→Markdown side, with provenance
and an honest fallback ladder. Phase 1 alone (`--from-file` + provenance)
delivers most of the value with near-zero risk.
