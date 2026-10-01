# URL to a Highlights-ready Bob reference PDF

- **Researcher:** grk
- **Date:** 2026-10-01
- **Question:** What is the most reliable way to turn a web URL (for example `https://openai.com/index/open-source-codex-orchestration-symphony/`) into a beautiful, readable PDF that becomes a Bob vault reference, with a note under `~/bob/ref/`, in the spirit of `bob highlights create -i`?
- **Verdict:** The idea is sound and should be built, but **not** as “print the webpage and write a ref note.” Reuse the existing Highlights intake pipeline. Fetch with a real Chrome, extract the article, typeset through the current pandoc/xelatex `create` path, stamp the page-1 marker, and let `scan` / `bob_xlib_pull` create the note.

---

## 1. In one breath

Bryan already has two PDF factories in this vault:

| Factory | What it produces | Where it shows up |
| --- | --- | --- |
| `bob highlights create` → pandoc + XeLaTeX (`xdvipdfmx`) | ~100–200 KB, clean selectable text, DejaVu typography, TOC/bookmarks | `lib/chat/` (236 PDFs) |
| Manual Chrome “Save as PDF” / print on the MacBook (`Skia/PDF` or Quartz PDFContext) | 0.6–19 MB, visual snapshot of the live page | `lib/blogs/` (4 PDFs) and several `lib/docs/` files |

The user request is to automate the second factory so a URL becomes a first-class Highlights reference. That is a good idea. The current manual blog path is the wrong template for the default engine.

Chrome-print PDFs in this vault already demonstrate the failure mode that matters for Bob: Highlights extracts **broken, letter-spaced text** into the sidecar, and `bob highlights scan` then copies that damage into `ref/`. A Steve Kinney article sidecar contains fragments such as `p ublished`, `spectru m`, `q uery`, `RAPTO R`, `stru ctures`. Those are webfont / tracking artifacts from Skia/Quartz print, not Highlights bugs.

The PDF that should land in `~/bob/lib/blogs/` is therefore **the article, typeset like a `create` PDF**, with `source_url` and `id` in the page-1 marker. Chrome is required as a **fetcher/renderer** (JavaScript, cookies, Cloudflare), not as the typesetter.

A new command `bob highlights clip <url>` should share create’s marker, collision, and xlib-intake code. It should **not** write `~/bob/ref/*.md` itself.

---

## 2. Critique of the plan

The plan as stated is: URL → beautiful readable PDF → reference PDF in the vault → new note in `~/bob/ref/`, inspired by `bob highlights create -i`.

**What is right**

- PDF is the correct object. Bob’s reading/annotation surface is Highlights Pro on the MacBook. Reference notes are generated from PDF markers plus sidecars. A Markdown-only clip (Obsidian Web Clipper) would skip that loop.
- `create -i` is the right inspiration: derive a stable `id`, embed a page-1 `/Text` marker, write into `xlib/<ref_type>/`, let scan move the file to `lib/` and materialize `ref/<ref_type>/<id>.md`.
- Doing this inside `bob highlights`, not as a one-off script, keeps doctor, dry-run, collision refusal, and the Mac intake bridge.

**What is wrong or incomplete**

1. **“Create the ref note” is the wrong command boundary.** `create` never writes `ref/`. `scan` does, on the MacBook, after `bob_xlib_pull` drains athena/apollo `xlib/` queues. Writing the note from the conversion command would race scan, skip intake collision checks, and produce a note whose `source_pdf` path is wrong until a later scan self-heals.
2. **Printing the live page is the wrong default.** It matches how the four existing blog PDFs were made. It also matches their bad sidecar text, huge git objects (`netclode.pdf` is 19 MB; chat PDFs are ~100 KB), cookie banners, and nav chrome. “Beautiful and readable” for this vault means **readable in Highlights and extractable into Obsidian**, not pixel-faithful to openai.com.
3. **The example URL is a fetch problem before it is a PDF problem.** From this host, `curl` of that OpenAI index URL returns HTTP 403, `cf-mitigated: challenge`, and a noscript body “Enable JavaScript and cookies to continue.” `web_fetch` returned empty. Any design that starts with `reqwest`/`curl`/pandoc-from-URL will fail the motivating example.
4. **`create` is Markdown-shaped.** It requires a `.md` file, shells out to pandoc/xelatex, and derives title from frontmatter / H1 / stem. A URL brings engine choice, Chrome discovery, bot-wall detection, slugification, `source_url`, image download, and timeout. Those options do not belong on `create`’s already-long flag set.
5. **Linux athena is not the machine that can print Cloudflare-gated pages.** `~/bin/chrome` is a wrapper that calls `/usr/bin/google-chrome-stable` on Linux; that binary is not installed here. Headless Chrome from a server IP will often keep failing the same challenge. The MacBook, with a real Chrome and an optional dedicated profile, is the clip host for hard pages. athena remains the right host for Markdown `create`.

The plan is a good product idea with a bad default implementation if it copies “Print to PDF” and writes the note immediately.

---

## 3. Justified requirement adjustments

These change the user’s wording. They are deliberate.

| Original implication | Adjustment | Why |
| --- | --- | --- |
| The conversion command creates `~/bob/ref/…md` | Clip writes `~/bob/xlib/<ref_type>/<id>.pdf` only. The next Mac `scan` (15-minute cron, or `bob_xlib_pull`) creates the note. Optional `--scan` only when clip runs on the MacBook. | Matches `create`. Preserves intake, dirty-target checks, and `source_pdf` library paths. |
| Default look = browser print of the live page | Default engine = **reader extract → Markdown → existing pandoc/xelatex create**. `--engine print` is the escape hatch. | Sidecar text quality, file size, and “readable article” all favor XeLaTeX. Existing blog prints are the cautionary sample. |
| Default `ref_type` like `create` (`chat`) | Default `ref_type=blogs` for http(s) article URLs. Direct PDF links default to `papers` if the path looks like arXiv/PDF, else stay `blogs`. Always overridable with `-t`. | Vault already has `ref/{ai,blogs,chat,docs,papers}` and `lib/{blogs,chat,docs,papers}`. Web articles are blogs. Chat is for research PDFs from `create -i`. |
| Marker `id` optional (`create` needs `-i`) | Clip **always** embeds `id`, derived from the URL slug. | `create -i` exists specifically so research PDFs have stable ids. A URL clip without `id` is the less useful variant. |
| Source link as ad-hoc `url:` | Marker field is **`source_url`**, already in `COMMON_USER_FIELDS`. Do not mint a parallel `url` key. | Docs and code already list `source_url`. One live blog note used custom `url` via `highlights_marker_fields`; that is legacy, not the contract. |
| Parent inferred from topic | Keep `-P/--parent`, default `obsidian_ref` (same as `create`). | Live notes use `sase_ref`, `memory_ref`, `obsidian_ref`. The tool cannot guess. |
| One engine for every URL | Three input shapes: (1) article HTML, (2) already-a-PDF, (3) bot wall / extraction failure. | arXiv and many docs are PDFs. The OpenAI example is a bot wall. Pretending they are the same command path will produce empty or huge files. |
| Hosted “URL to PDF” APIs | Out of scope. Local Chrome + local pandoc only. | Sending Bryan’s reading list through a third-party renderer is the wrong privacy default for a personal vault. |

A Markdown-only clip into the vault (Defuddle / Obsidian Web Clipper) is a **different product**. It is a good companion later. It does not satisfy “reference PDF for Highlights.”

---

## 4. How `bob highlights create -i` actually works

Code: `src/native/highlights_ref/create.rs`. Docs: `docs/highlights-ref-sync.md`.

1. Read a `.md` file. Title = YAML `title`, else first `# ` H1, else stem.
2. If `-i/--include-id`, marker `id` = filename stem (UTF-8, nonempty). Research hook example: `bob highlights create --include-id 202608/xprompt_role_binding/xprompt_role_binding.md` → `id: xprompt_role_binding`.
3. Compose a page-1 marker list:

   ```text
   - status: ready
   - parent: obsidian_ref
   - title: <document title>
   - id: xprompt_role_binding
   ```

   Parent is stored bare; generated frontmatter later wraps it as `[[obsidian_ref]]`.
4. Default target: `~/bob/xlib/<ref-type>/<stem>.pdf` (`ref-type` defaults to `chat`). `--output` can point at an exact `.pdf` path; `--output` conflicts with `--ref-type`.
5. Collision rules: refuse an existing same-stem `.md`/`.textbundle` beside the target (Highlights would treat it as a sidecar). Refuse an already-occupied library destination for intake targets. Existing target PDF requires `--force`.
6. Shell out to pandoc (`BOB_PANDOC_COMMAND` or `PATH`), XeLaTeX, DejaVu fonts, TOC depth 3, numbered sections, tango highlighting, `fvextra` wrapping for code, a Lua filter that allows breaks in long inline code, margins 0.85in, 10pt.
7. Load the PDF with `lopdf`, append a 24×24 page-1 `/Text` annotation containing the marker, atomic-rename into place.
8. Print `next: bob highlights scan` for intake/library targets.

`scan` then: optional `highlights.pre_scan_hook` (`PATH="$HOME/bin:$PATH" bob_xlib_pull` on the MacBook) → move `xlib/<rel>` to `lib/<rel>` → write `ref/<rel>.md` with `type: "[[ref]]"`, `ref_type`, pipeline hashes, and a `#task #ref [[lib/…pdf]] #hide ^ref` lifecycle line.

This is the pipeline clip must join at step 3, not reinvent at step 8.

---

## 5. What the vault already does with web pages

Measured on `~/bob` (2026-10-01):

**Blogs (Chrome print, then Highlights marker by hand)**

- `lib/blogs/steve_kinney_agent_memory.pdf` — 679 KB, Creator Chrome 148, Producer macOS Quartz PDFContext. Ref note `url: "https://stevekinney.com/writing/agent-memory-systems"`. Sidecar text is visibly corrupted by print encoding.
- `lib/blogs/build_with_muse_code.pdf` — 825 KB, Skia/PDF m151, Chrome 151. Title from the live page: “Meet Muse Spark 1.2 and Muse Code…”.
- `lib/blogs/harness_for_rsi.pdf` — 3.9 MB, Skia/PDF m150, Lil’Log.
- `lib/blogs/netclode.pdf` — **19.6 MB**, Quartz PDFContext, Chrome 149.

Markers for these were authored in Highlights (`status`, `parent`, sometimes `url`), not by `bob highlights create`. `create` today cannot emit `source_url`.

**Chat (the `create` factory)**

- 236 PDFs under `lib/chat/`.
- Producer `xdvipdfmx`, Creator “LaTeX via pandoc”.
- Sizes ~97–187 KB.
- Sidecar highlight text is clean English when highlights exist (`artifact_link_derivation.md` quotes are coherent).

**Docs**

- Mix of Chrome prints (`charm_vhs_readme.pdf`, `sase_INSTALL.pdf`, `sase_AGENTS_v2.pdf`) and other sources.

**Papers**

- arXiv GenPDF / pikepdf. These are real papers, not clipped HTML.

**Intake bridge** (`docs/vault-git-sync.md`)

- `xlib/` is gitignored. athena and apollo each hold a source queue.
- Mac `bob_xlib_pull` rsyncs nonempty queues with `--remove-source-files --ignore-existing`, then scans.
- `lib/*.pdf` **are** git-tracked (`~/bob/.gitignore` un-ignores `*.pdf`). Chrome-print bloat becomes a vault-sync cost. A 19 MB blog post is a process bug, not a one-off.

So: Bryan already clips the web to PDF by printing in Chrome on the Mac, drops the file into the Highlights library, types a page-1 marker, and lets scan build `ref/blogs/`. Automating that is the request. Changing the typesetter is the quality fix.

---

## 6. Stress test: the OpenAI example

URL: `https://openai.com/index/open-source-codex-orchestration-symphony/`

From this Linux workspace:

- `curl -I` → **HTTP 403**, `cf-mitigated: challenge`, Cloudflare `cf-ray`, managed JS challenge.
- Body is a 9.8 KB challenge shell. Noscript text: “Enable JavaScript and cookies to continue.”
- No article HTML is present to extract.

Implications:

- A “reliable” clipper that only does HTTP GET will fail this URL every time.
- Headless Chrome **may** pass if it looks like a real browser; it often will not, especially from a datacenter-like fingerprint or with `navigator.webdriver` set.
- A persistent Chrome user-data-dir, on the MacBook, where Bryan has already loaded openai.com in a normal window, is the honest fix. Persist `cf_clearance`. Do not build a Cloudflare-bypass product.
- Clip must detect the challenge page (title/body heuristics: “Just a moment…”, “Enable JavaScript and cookies to continue”, `#challenge-error-text`, tiny body) and fail with a specific error: *bot wall; rerun on the MacBook with `--chrome-profile` after opening the URL once in that profile.*

This URL is a good acceptance test. It is a bad first unit test. Fixture HTML (`file://` or `--html-file`) should cover extraction and marker embedding without the network.

---

## 7. Option space

### A. Chrome `--print-to-pdf` of the live URL

```text
chrome --headless=new --no-pdf-header-footer --print-to-pdf=out.pdf URL
```

Then `lopdf` stamp, write xlib.

- **Pros:** Matches today’s blog files. Figures, code highlighting, and layout survive. One binary. Chrome CLI is documented (`--dump-dom`, `--print-to-pdf`, `--timeout`, `--no-pdf-header-footer`).
- **Cons:** Nav/chrome/cookie UI; webfont text-extraction damage (already in the vault); 10–100× size vs `create`; no Readability; headless CF failures; `wkhtmltopdf` 0.12.6 is on PATH here and must not be used (QtWebKit, unmaintained, no modern CSS, no CF).
- **Use as:** `--engine print` fallback, and as the implementation for “extraction failed / not an article.”

### B. Chrome `--dump-dom` → Readability → Markdown → existing `create` pandoc path (**recommended default**)

1. Discover Chrome the way `create` discovers pandoc: `BOB_CHROME_COMMAND`, else `~/bin/chrome`, else platform paths (`Google Chrome.app` on Mac, `google-chrome-stable` on Linux).
2. `chrome --headless=new --dump-dom --timeout=30000 [--user-data-dir=<bob profile>] URL`.
3. Reject challenge / empty / non-article pages.
4. Extract with a sync Mozilla Readability port in-process. **`legible` 0.5.1** (Apache-2.0, August 2026) returns title, byline, published time, HTML, CommonMark, and `is_probably_readerable`. `readabilityrs` is a similar port. **Defuddle** (kepano; engine under Obsidian Web Clipper) is the best Markdown extractor in this family but is JavaScript; keep it as a later `--extractor defuddle` that shells `npx defuddle parse --markdown` if legible quality is weak on a corpus.
5. Download article images into a temp dir (never next to the output PDF — a sibling `.md` is a Highlights sidecar). Rewrite to relative paths. pandoc `--resource-path` already points at the Markdown parent in `create`.
6. Write temp Markdown with `title:` frontmatter. Call the existing `create_pdf` planner with `include_id`, `ref_type=blogs`, and extra marker keys `source_url`, optional `author` / `published`.
7. Delete temps. Print the same success block `create` prints, plus `source_url`.

- **Pros:** Reuses the typesetter Bryan already likes; clean Highlights text; small git objects; marker/intake/doctor stay one code path; no tokio. bob-cli is a **synchronous** CLI (`clap` + `lopdf`, no `reqwest`, no runtime). `chromiumoxide` 0.9 would drag in tokio, generated CDP (~60K lines), and a long compile. Shelling Chrome is the same architectural move as shelling pandoc.
- **Cons:** Loses original layout; image pipeline is extra work; reader can drop asides, comment threads, or SPA content that is not “an article”; still needs Chrome for JS-heavy and CF-gated pages.
- **This is the default.**

### C. Readability rewrite of the DOM, then Chrome `Page.printToPDF`

Load page, replace `body` with extracted article HTML, apply a print stylesheet (serif, ~40rem measure, hide remaining chrome, wrap code), print.

- **Pros:** Images stay in the print without a download step; can look like a “reader mode PDF.”
- **Cons:** Still a Skia PDF. Unless the rewrite forces system fonts and kills letter-spacing, sidecar text will rot the same way. Needs CDP, not just `--print-to-pdf`.
- **Use as:** a later `--engine print-reader` if visual fidelity with inlined figures beats LaTeX for some sites.

### D. Playwright / website2pdf / url2pdf

Current industry default for “URL to PDF” (Playwright `page.pdf()`, `printBackground`, A4 margins). Python `website2pdf` 1.0 (2026-08) is a thin Playwright wrapper.

- **Pros:** Waits for `networkidle`, injects CSS, stealth plugins exist.
- **Cons:** Node or Python runtime in a Rust CLI; Playwright browser cache; same Skia output as C if you print; overkill if Chrome CLI dump-dom is enough for the default engine.
- **Do not take as a bob-cli dependency.** Acceptable only as an optional helper script if Chrome CLI cannot wait long enough for a class of SPAs.

### E. Obsidian Web Clipper / Defuddle Markdown notes, no PDF

Official clipper, MIT, Defuddle extraction, templates, vault frontmatter.

- **Pros:** Best Markdown. Bryan already lives in Obsidian.
- **Cons:** No Highlights, no `lib/` PDF, no `#ref` lifecycle task, no sidecar annotation sync. Does not implement the request.
- **Later companion**, not the solution.

### F. Hosted APIs (Cloudflare Browser Run, Rendex, PDFShift, Jina Reader)

- **Reject** for default. Privacy, cost, and a personal corpus of URLs. Cloudflare’s own `/pdf` endpoint is ironic for the openai.com example and still leaves the vault dependent on a network vendor.

### G. Direct PDF URL / `Content-Type: application/pdf`

Download bytes (curl is enough), stamp marker with the existing `embed_marker`, intake as `papers` or user `-t`. This is how `lib/papers/` already gets arXiv PDFs, minus the stamp automation.

Treat this as a first-class branch of `clip`, not an afterthought.

---

## 8. Why reader → pandoc beats print for *this* vault

Highlights sidecar for `steve_kinney_agent_memory` (Chrome print):

```text
> n December
2025, Hu et al. p
ublished “Memory in the Age of AI
> Agents”—a 107-page survey
…
> There’s a spectru
where you land on that spectru
m matters:
…
> RAPTO
R’s recursive abstractive tree. These stru
ctures enable
> m
ulti-hop reasoning
```

`bob highlights` already tries to heal hyphenation when rendering notes (`docs/highlights-ref-sync.md`: `through-` + `put` → `throughput`). It cannot heal **inserted spaces inside words**. Those spaces become the Obsidian quote callouts. That is the reading surface.

Pandoc/XeLaTeX PDFs in `lib/chat/` do not show this damage. They also already have:

- hyperlinked TOC and PDF bookmarks
- code wrapping (`fvextra` + Lua filter) — important for technical blogs
- DejaVu, so extraction is UTF-8 and stable
- a marker stamp path that is tested

“Beautiful” in Bob already has a house style. Clip should join it.

---

## 9. Recommended solution

### Command

```text
bob highlights clip <url>
    [-b|--bob-dir PATH]
    [-C|--chrome PATH]
    [-d|--dry-run]
    [-e|--engine reader|print]
    [-f|--force]
    [-l|--lib-dir PATH]
    [-o|--output PDF]
    [-P|--parent NOTE]
    [-p|--chrome-profile PATH]
    [-r|--ref-dir PATH]
    [-s|--status STATUS]
    [-t|--ref-type DIR]
    [-x|--xlib-dir PATH]
    [--timeout MS]
```

Keep subcommands alphabetically sorted (`clip` sits beside `create`). Give every public long option a short alias (CLI rules). Do not overload `create`’s required `MD_FILE`.

`BOB_CHROME_COMMAND` mirrors `BOB_PANDOC_COMMAND`. `--chrome-profile` is a dedicated user-data-dir, **not** Bryan’s logged-in daily Chrome profile (Chrome 136+ refuses remote debugging against the default profile without a separate `--user-data-dir`; using the live profile while Chrome is open will lock/corrupt it).

### Default behavior

```text
bob highlights clip \
  https://stevekinney.com/writing/agent-memory-systems
```

should:

1. Engine `reader`.
2. `ref_type=blogs`.
3. `id=agent-memory-systems` (last nonempty path segment, slug-safe; if the segment is `index` or empty, fall back to `host-path` slug, truncated, plus a short hash on collision).
4. Marker:

   ```text
   - status: ready
   - parent: obsidian_ref
   - title: Memory Systems for AI Agents: …
   - id: agent-memory-systems
   - source_url: https://stevekinney.com/writing/agent-memory-systems
   ```

   Add `author` / `published` when extraction supplies them.
5. Write `~/bob/xlib/blogs/agent-memory-systems.pdf`.
6. Print `next: bob highlights scan` (athena) or rely on the Mac 15-minute hook.

For the OpenAI URL, same shape, `id=open-source-codex-orchestration-symphony`, **after** a Chrome session that actually received the article HTML.

### Internals to share with `create`

Extract from `create.rs` (it is already one file with planner + pandoc + `embed_marker`):

- `plan_create` / intake vs library vs external
- `compose_marker` — extend with optional extra projection keys (`source_url`, …)
- `embed_marker` + `atomic_save_pdf`
- collision / sidecar refusal
- success / dry-run printer

Clip is a front-end that produces either a temp Markdown file (reader) or a temp unstamped PDF (print / direct PDF), then the shared installer.

### Doctor

`bob highlights doctor` should report Chrome the way it reports vault paths: ok / missing / overridden. Missing Chrome is a **warning** for people who only run `create`, a **failure** only if we add a clip-specific doctor mode. Prefer: always show `chrome: ok|missing` so Mac setup is obvious.

### Tests (no network)

- Dry-run of `clip` against a `file://` HTML fixture: plan paths, marker contains `source_url` and `id`, `writes: none`, pandoc/chrome not invoked.
- Readerable fixture → temp markdown title/H1.
- Challenge-page fixture → explicit error, no PDF.
- Direct PDF fixture → stamp marker, skip pandoc.
- `--engine print` dry-run still refuses occupied library destinations.
- `--output` + `--ref-type` conflict, same as `create`.
- Never write a sibling `.md` next to the PDF.

Linux CI should not require Chrome or a live openai.com fetch. MacBook validation (same bar as current Highlights docs): one real CF-gated article, one static blog, one arXiv PDF URL, then `scan --dry-run`.

### Where to run it

| Host | Markdown `create` | URL `clip` |
| --- | --- | --- |
| athena | Yes (pandoc/xelatex present) | Static/simple HTML only, until Chrome is installed. CF-gated URLs will fail. |
| MacBook | Yes | **Preferred.** Real Chrome, Highlights, `bob_xlib_pull`, 15-minute scan. |

Install Chrome on athena later if clip-from-Linux becomes routine; still keep a Bob-specific Chrome profile.

### What not to build in v1

- Auto `scan` from athena.
- Cookie-banner click scripts and generic stealth/bypass.
- Hosted renderers.
- Writing a Markdown clip note in parallel with the PDF (sidecar collision).
- Playwright/tokio inside bob-cli.
- Guessing `parent` from domain.

---

## 10. Risks and limits

- **Reader misses the page.** SPAs, docs with a huge sidebar and a small article node, tweet threads, and “app” pages will fail `is_probably_readerable`. Error must recommend `--engine print` or “this is not an article.”
- **Images.** Without a download pass, pandoc drops remote figures. With a download pass, hotlink-protected CDNs 403. Accept missing images in v1 rather than blocking the PDF; print engine remains the figure-heavy fallback.
- **Paywalls / login.** Only a Chrome profile that already has the session will work. Document that. Do not store passwords in bob-cli.
- **Git size.** Defaulting to print would regress vault-sync. Reader default is also a sync fix.
- **Marker field drift.** One blog note used `url`. Clip should write `source_url`. A later doctor warning for `url` without `source_url` is optional cleanup, not v1.
- **Filename collisions.** Two URLs with the same last segment (`/intro/`) need the hash suffix. Refuse to overwrite library copies without `--force`, same as `create`.
- **Legal / ToS.** This is personal offline reading of pages Bryan can already open. Stay a local browser, not a scraper farm.

---

## 11. Would I do something else?

If the goal were “save the web into Obsidian,” I would install Obsidian Web Clipper (Defuddle) and skip PDFs.

That is not this vault’s reference system. Papers, blogs, docs, and chat already orbit Highlights PDFs plus `ref/` notes plus a `#ref` lifecycle task. A URL clipper that does not emit a Highlights-ready PDF would be a second, weaker library.

The smallest design that is still correct:

1. New `bob highlights clip <url>`.
2. Chrome dump-dom (or PDF download).
3. `legible` → temp Markdown.
4. Existing `create` typesetter + marker + xlib intake.
5. Mac scan creates `ref/blogs/<id>.md`.

That is `create -i` for the web, with a fetch/extract front-end and `source_url` on the marker.

Ship `--engine print` in the same PR so the OpenAI marketing layout and image-heavy posts have an explicit, slightly ugly escape hatch. Do not make it the default.

---

## 12. Suggested first implementation slice

Small enough to land, large enough to use:

1. Refactor `create.rs` just enough to stamp an already-rendered PDF and to accept extra marker fields. No URL logic yet. Tests: stamp a fixture PDF.
2. `clip` dry-run + `file://` HTML fixture through `legible` + shared planner. No Chrome required in CI.
3. Chrome dump-dom integration, challenge detection, image download best-effort, MacBook validation on a non-gated blog and on the OpenAI URL with `--chrome-profile`.
4. `--engine print` and direct-PDF download.
5. Docs: `docs/highlights-ref-sync.md` plus doctor Chrome line. Default `ref_type=blogs`. Always `id` + `source_url`.

Stop there. Do not add Defuddle, Playwright, or note writing until this loop is boring.

---

## Sources

**This repo / vault (primary)**

- `src/native/highlights_ref/create.rs` — pandoc/xelatex, marker embed, intake planner, `-i` id rule
- `src/native/highlights_ref/cli.rs`, `mod.rs` — `COMMON_USER_FIELDS` includes `source_url`, `author`, `published`
- `docs/highlights-ref-sync.md` — create/scan/doctor contract, xlib → lib → ref
- `docs/vault-git-sync.md` — `bob_xlib_pull`, 15-minute Mac scan, gitignored `xlib/`
- `~/bob/.gitignore` — PDFs tracked; `xlib/` not
- `~/bob/lib/blogs/*.pdf` producers (Skia/PDF, Quartz PDFContext, Chrome on macOS)
- `~/bob/lib/chat/*.pdf` producers (`xdvipdfmx`, LaTeX via pandoc)
- `~/bob/ref/blogs/steve_kinney_agent_memory.md` and `~/bob/lib/blogs/steve_kinney_agent_memory.md` — `url` custom field and corrupted sidecar text
- `~/bin/chrome` — wrapper to Chrome.app / `google-chrome-stable` (binary missing on this Linux host)
- Live fetch of the example OpenAI URL: HTTP 403 Cloudflare managed challenge

**External**

- Chrome headless CLI: dump-dom, print-to-pdf, timeout, no-pdf-header-footer — https://developer.chrome.com/docs/automation-and-testing/headless-cli
- kepano/defuddle (Obsidian Web Clipper extractor) — https://github.com/kepano/defuddle and https://defuddle.md/
- Obsidian Web Clipper — https://obsidian.md/clipper and https://github.com/obsidianmd/obsidian-clipper
- `legible` 0.5.1, Rust Readability port with Markdown output — https://docs.rs/legible/0.5.1/legible/
- `readabilityrs` 0.1.4 — https://lib.rs/crates/readabilityrs
- `chromiumoxide` 0.9.1 (rejected for v1: tokio/CDP compile cost) — https://docs.rs/chromiumoxide/0.9.1/chromiumoxide/
- Playwright as 2026 HTML-to-PDF default — https://rendex.dev/blog/best-html-to-pdf-tools-2026
- `website2pdf` 1.0 Playwright wrapper — https://pypi.org/project/website2pdf/
- Cloudflare challenge behavior for automated Chrome — https://simplescraper.io/learn/bypass-cloudflare-in-puppeteer
- Chrome 136+ debugging requires a non-default `--user-data-dir` — noted in headless-browser references around `--remote-debugging-port`

---

## Recommendation (short)

Build **`bob highlights clip <url>`**. Default engine: **Chrome dump-dom → `legible` → existing pandoc/XeLaTeX create → page-1 marker with `id` + `source_url` → `~/bob/xlib/blogs/<id>.pdf`**. Let the Mac scan create `~/bob/ref/blogs/<id>.md`. Keep `--engine print` for layout-faithful failures. Do not print-by-default, do not write the ref note in the clip command, do not call hosted APIs, and treat the OpenAI example as a Chrome-profile acceptance test rather than a `curl` problem.
