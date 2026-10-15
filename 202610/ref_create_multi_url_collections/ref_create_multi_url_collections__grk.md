# Merge multiple URLs in `bob ref create`

Researcher: `grk`. Independent report. Do not treat this as the swarm synthesis.

- **Question:** How should `bob ref create` accept several URLs and merge those pages into one Highlights PDF / reference note? The seed plan adds `-n|--name`, renames `-o|--output` to `-o|--output-directory`, and requires `--name` iff the URLs share no useful common prefix. Lead the design. Critique the plan. Adjust requirements where justified. Recommend a solution.
- **Evidence:** `src/native/highlights_ref/{create.rs,clip.rs,clip_url.rs,clip_adapter.rs,pdf_target.rs,stamp.rs,sources.rs,model.rs}`; `scripts/web_clip/{web_clip_adapter.py,web_clip_render.py,template/reader.css}`; `docs/{highlights-create.md,highlights-clip.md,highlights-ref-sync.md,ref.md}`; `tests/cli/{highlights/create.rs,help_options.rs}`; `sase/memory/cli_rules.md`; glossary Reference Note / Reference Task; prior research `research:202610/web_url_reference_pdf_capture/web_url_reference_pdf_capture__final.md`; curl 7.73 `--output-dir` (Daniel Stenberg, 2020-09-10); wget `-O` vs `-P`; pandoc multi-input concatenation; Python `os.path.commonpath`; lopdf merge examples.
- **Date of evidence:** bob-cli tree as of 2026-10-15.

## Bottom line

Yes: merge is a good idea. No: do not add `-n|--name`, and do not rename `-o|--output`.

Those two flag changes collide with a CLI that already exists and is tested. `-N|--name STEM` already names the PDF, the marker `id`, and the eventual `ref/<type>/<stem>.md`. `-n` is `--no-audio`. `-o|--output` is a complete `.pdf` path and is required to keep that meaning. The "use name and output together" problem is already solved by `-N` plus default intake (`xlib/<ref-type>/<stem>.pdf`), or by a single `-o path/to/file.pdf`.

**Recommended solution:** `bob ref create URL [URL…]` merges web-article URLs into one reader-mode PDF, printed once.

1. Keep `-N|--name STEM` and `-o|--output PDF` byte-identical. Keep `-n|--no-audio`.
2. Require `-N` for a merge only when neither `-o` nor a *useful path-segment stem* can name the file. Compute that stem from cleaned URLs *before any fetch*, using host match + path-segment LCP + a pagination-query exception. Fail closed with a copy-pasteable hint when the stem is not useful.
3. Merge at article HTML, then print once through the existing Bob reader template, so page numbers, footer, and masthead are one document. Do not concatenate separately printed PDFs.
4. Stamp `source_url` as a YAML list and teach create/ingest/routing to index list-valued URLs the way `bob ref find` already does. Without that, a merged capture cannot dedupe.

## Is this a good idea?

### What is right in the request

A series, a paginated essay, and a saved multi-page walled article are one piece of reading. Bob's reference model agrees: one Reference Note, one `^ref` task, one Highlights PDF, one listen episode. Capturing part 1 and part 2 as two refs splits the queue, splits highlights, and splits audio. Merge is the GTD-correct shape.

The three design goals in the request are the right ones:

- **Intuitive:** `bob ref create URL1 URL2 -P sase` should just work when the URLs obviously share a document, and should ask for `-N` when they do not.
- **Reliable:** never silently invent a generic stem (`blog`, `posts`, the host, a string prefix of two unrelated slugs). Fail before the browser if the name is not known.
- **Beautiful:** one typeset book, not a staple of N PDFs each with its own masthead and restarting `n / N`.

Requiring an explicit name when auto-naming would be guesswork is the correct fail-closed instinct. It matches web-article capture's existing contract: "Reliable means never silently wrong" (`docs/highlights-clip.md`).

### Where the seed plan as written is wrong

**The flags it wants already exist, under different letters, with different meanings.**

Current `bob ref create` help (verified in `create.rs` and `tests/cli/help_options.rs`):

| Short | Long | Meaning today |
| --- | --- | --- |
| `-N` | `--name STEM` | Output filename stem; marker `id`; eventual note basename |
| `-n` | `--no-audio` | Skip companion-audio discovery |
| `-o` | `--output PDF` | Complete path including the `.pdf` filename |
| `-t` | `--ref-type DIR` | Intake subdirectory under `xlib/` / `lib/` |
| `-T` | `--title TITLE` | Human title, independent of the stem |

`-o` already conflicts with `--name` *on purpose*: "`--output` cannot be combined with `--ref-type` or `--name` because those only participate in default target derivation" (`docs/highlights-create.md`, `create.rs` `conflicts_with("name")`). The stem of an exact output path *is* the name.

Stealing `-n` for `--name` would silently invert `--no-audio` for every existing invocation of `bob ref create … -n`. Renaming `-o|--output` to `-o|--output-directory` would invert every `-o file.pdf` (the dry-run tests in `tests/cli/highlights/create.rs` pass `nested/custom-name.pdf` and require a `.pdf` suffix). CLI rules freeze command spellings as hidden aliases with byte-identical behavior; even if that sentence names commands, applying the same spirit to options still forbids changing what `-o` and `-n` do.

curl is the cautionary tale. `-o/--output` has meant "this file" since curl 4.0 (1998). When people wanted a directory *plus* a name, curl 7.73 *added* `--output-dir` and left `-o` alone (Daniel Stenberg, 2020-09-10). wget splits the same way: `-O` is the document, `-P/--directory-prefix` is the directory. pandoc's `-o/--output` is a file; multiple inputs concatenate into it; jgm has refused magic output-name derivation from several inputs (pandoc#3250). Bob should do the same: keep `-o` as a file.

**"Name of the reference note" is not a new concept.** `create` never writes `ref/` notes. `scan` does, using the PDF stem as `id` and as `ref/<type>/<stem>.md` (`docs/highlights-ref-sync.md`). `-N|--name` is already that name. `-T|--title` is already the human title. Adding a third identifier would split identity across stem, id, and note basename, which the pipeline treats as one token.

**A naive "common prefix of the URL strings" is a false friend.** `https://example.com/cat` and `https://example.com/catalog` share the string `https://example.com/cat`. Path-*segment* LCP of `/cat` vs `/catalog` is empty, which is the correct refusal. Python's `os.path.commonpath` exists specifically because string prefix is not a path prefix.

**Always requiring `--name` for every merge would also be too loud.** `…/my-series/part-1` and `…/my-series/part-2` have an obvious stem. Forcing `-N my_series` on that pair is busywork. The interesting work is the usefulness test, not a blanket requirement.

### Would I take a different approach?

I would still ship multi-URL merge on `bob ref create`. I would:

- Reuse `-N|--name`. Leave `-n` and `-o` alone.
- Auto-name only from *parsed, cleaned URL structure*, before the network, with a conservative usefulness test.
- Treat an explicit `-o file.pdf` as supplying the name, so `-N` is not required in that case.
- Merge HTML, print once. Reject PDF-concatenation as the v1 renderer.
- Restrict v1 to web-article URLs (the request's "articles / web pages"). Mixed Markdown/PDF/arXiv in one argv is a later, separate gesture.
- Close the documented list-valued `source_url` gap in the same change, because a merged marker that `find` can see and `create` cannot is a silent duplicate factory.
- Leave `bob capture`, `ref jobs`, and `ingest_url` single-URL. Merge is an explicit `create` gesture.

I would skip: renaming flags; `--output-directory`; a new note-name distinct from the stem; interactive name prompts; title-LCP filenames (titles arrive after the browser); concatenating N Chromium prints with lopdf.

## Requirement adjustments

Call-outs the lead should adopt or explicitly reject.

| ID | Adjustment | Why it is justified |
| --- | --- | --- |
| **ADJ-1** | **Do not add `-n|--name`.** Reuse `-N|--name STEM`. | `-n` is `--no-audio`. `-N|--name` already names the PDF, marker `id`, and scan's note basename. A new flag is a collision, not a feature. |
| **ADJ-2** | **Do not rename `-o|--output` to `-o|--output-directory`.** Keep the complete `.pdf` path, the `.pdf` suffix check, cwd/`~` resolution, and the conflict with `--ref-type` / `--name`. | Byte-identical option meaning. curl/wget/pandoc all keep `-o` as a file. Directory + stem is already `-t` + `-N` (intake) or `-o dir/name.pdf` (escape hatch). |
| **ADJ-3** | **Require `-N` iff the merge has no name from `-o` and no useful shared stem.** An exact `-o file.pdf` names the file; do not also demand `-N`. | The seed's "iff no useful prefix" is right for the default-intake path. `-o` is already a name. |
| **ADJ-4** | **Compute the shared stem from cleaned URL *path segments*, never from the raw URL string, never from titles, never from the host alone.** Algorithm below. Fail before any fetch when it returns none. | String LCP is wrong. Titles arrive too late and collide (`Attention Is All You Need` vs `Attention Is All You Want`). Host-only names every NYT pair `nytimes_com`. Fail-closed matches clip. |
| **ADJ-5** | **v1 merge accepts only web-article `http(s)` URLs.** Two or more targets that are mixed kinds, local files, arXiv, or sniffed PDFs error with a hint to capture them separately. | The request is articles/web pages. HTML concatenation is the beautiful path; a PDF body cannot join that typesetting. Pandoc already concatenates Markdown; that can be a follow-up. |
| **ADJ-6** | **Merge at `article.json` HTML and print once.** One masthead, one footer title, continuous `n / N`, part H1s, `break-before: page` between parts after the first, a linked contents list. | lopdf can staple pages (upstream merge example) but cannot rewrite Chromium margin-box page numbers or collapse N mastheads. Beauty is the print, not the staple. |
| **ADJ-7** | **All-or-nothing.** Any blocked/thin/network/dedupe hit writes nothing. CLI order is page order. Duplicate argv URLs collapse with a warning. Cap at 20 URLs. | Matches `--listen` ("if the listen command fails nothing is written"). A half-series PDF is worse than a refusal. 95 MiB vault-sync limit plus adapter timeout make an unbounded list unsafe. |
| **ADJ-8** | **Stamp `source_url` as a YAML list when N≥2, and index list values in create/ingest/routing.** | `bob ref find` already indexes `source_url` / `url` lists (`docs/ref.md`). Create and `collect_recorded_source_urls` only read scalars via `MarkerValue::as_string()`. A merged list that find can see and create cannot will re-import. This is a documented gap; merge makes it load-bearing. |
| **ADJ-9** | **`--listen` on a merge treats `{target}` as the staged merged PDF**, same as the Markdown route. `{title}` is the combined title. | `sase listen render` of URL 1 would narrate part 1. Markdown already passes the staged PDF as `{target}` (`docs/highlights-create.md`). |
| **ADJ-10** | **Make `-H|--html` repeatable and zip with URLs by index.** Count must match. `-H -` stays single-URL only. | Paywalled series are saved as N HTML files. One `--html` for N URLs is ambiguous. |
| **ADJ-11** | **Do not add `--output-dir`.** CLI rules require a short alias for every public long option; `-o` is taken; `-O` collides with curl/wget folklore. | The intake default plus `-o file.pdf` cover the real cases. curl's `--output-dir` exists because curl's default destination is cwd; Bob's default destination is already `xlib/<ref-type>/`. |
| **ADJ-12** | **Leave capture, jobs, and `ingest_url` single-URL.** | Background ingest has fixed defaults and no name override (`docs/highlights-create.md`). Two capture URLs are two jobs. Merge is deliberate. |

## What exists today (verified)

### One target, five kinds

`bob ref create <TARGET>` classifies one positional (`create.rs` `Arg::new("target").required(true)`): Markdown → pandoc/XeLaTeX into `xlib/chat/`; local PDF / PDF URL / arXiv → stamp-as-is into `xlib/papers/`; web article → pinned adapter into `xlib/blogs/`. `-P/--parent` is required. `bob ref clip` is a hidden alias with the same options.

### Naming a single article

For a web URL, stem resolution is already a waterfall (`clip.rs`):

1. `-N/--name` if present (`validate_name`: `[A-Za-z0-9][A-Za-z0-9_.-]*`, optional `.pdf` suffix stripped).
2. `stem_from_url`: last non-noise path segment, `snake_case`, cap 80. Noise = `index/default/home/post/posts/p/article/articles/blog/amp/en/en-us`, page extensions, date parts, length ≤ 2, all digits.
3. `snake_case` of the extracted title.
4. `<host>_<YYYYMMDD>`.

Default intake then walks `<stem>`, `<stem>_2`, … `<stem>_999` so a different reference suffixes and the same reference refuses (`stamp.rs` `plan_default_target`). `-o` skips that walk and keeps the exact path.

This waterfall is the code the merge stem must reuse, not replace.

### Output vs name

`-o/--output` is a complete PDF path. Relative from cwd, `~` expanded, `.pdf` required. It cannot combine with `-N` or `-t`. Writing into a custom folder today is `-o ~/Desktop/series.pdf`, not `-o ~/Desktop` plus a name.

### Provenance and the list-valued gap

URL routes stamp scalar `source_url` (cleaned URL). Scan copies it into the note as a standard user field. `bob ref find` indexes scalars *and* lists. Create's import dedupe and `sources.rs` `collect_recorded_source_urls` / `collect_intake_records` call `as_string()`, so a YAML list is invisible to import. `docs/ref.md` already warns about this. Merge must close it or it ships a duplicate bug.

### Adapter and print template

Protocol v1: one JSON `capture` request (`url`, optional `html_path`, `workdir`, `out_pdf`, `dry_run`) → one PDF. The adapter writes `article.json` (title, author, site, html, source_url, word_count, …) and `web_clip_render.assemble` builds one masthead + one `.article-body`. `@page` Letter, footer short title on the left, `counter(page) / counter(pages)` on the right, first page suppresses the title. Headings shift so the article's highest heading is `h2`. Direct-PDF captures return `kind: "pdf"` and skip the template. Dry-run still launches the browser; it skips image localization and the print.

There is no `capture_many` and no extract-without-print op. A merge needs an additive adapter op or a `skip_render` field.

### Deduping

Every URL is checked against scalar note `source_url`/`url` and intake markers *before* fetch. A PDF-backed hit refuses; `--force` only overwrites the same intake target; `--listen` attaches. Private hosts, userinfo, and non-http(s) already fail closed.

## The naming problem

The seed asks to require `-N` "iff there is no way for us to use some (long enough and useful) common prefix that all of the URLs share." That is the right question. The answer is a *useful shared stem*, not a prefix of the URL strings.

### Why string LCP fails

| Pair | String LCP | Wanted |
| --- | --- | --- |
| `/cat` and `/catalog` | `/cat` | refuse (different slugs) |
| `http://example.com/a` and `https://example.com/a` | `http` | same article after cleaning |
| `https://www.example.com/a` and `https://example.com/a` | `https://` | same article (`www.` already stripped) |
| `/posts/foo` and `/posts/foo-bar` | `/posts/foo` | refuse |

Work on *parsed* URLs after `validate_and_clean` (fragment and tracking query already gone, host lowercased, `www.` stripped).

### Algorithm: `shared_stem(urls) -> Option<String>`

Run after cleaning and after collapsing duplicate `dedupe_key`s (warn, keep first). If fewer than two unique URLs remain, this is not a merge: fall through to today's single-URL path.

1. **Same normalized host.** If hosts differ, return `None`. Two sites in one PDF is a collection the user must name.
2. **Path segments.** Percent-decode, drop empties, strip a trailing page extension from the last segment only. Longest common *segment* prefix (zip-until-mismatch, same family as `os.path.commonpath`).
3. **Identical paths (query is the only difference).** Let the remaining query keys (already minus tracking) be compared as sorted `(k,v)` pairs.
   - Differing keys ⊆ `{page, p, pg, part, chapter, section}` → this is pagination of one document. Stem from the last path segment, *even if* that segment is in `SKIPPED_SEGMENTS` (`/article?page=1` with `/article?page=2` → `article`). If the path is empty, return `None`.
   - Any other differing key (`id`, `v`, `slug`, …) → `None`. `/wiki?id=France` and `/wiki?id=Germany` share a path and must not auto-name `wiki`.
4. **Different paths.** Drop noise from the LCP using the existing `stem_from_segment` rules (skipped words, date parts, length ≤ 2, all digits). If at least one useful segment remains, `snake_case` the *last* useful segment and return it. If the LCP is only noise, return `None` — do not fall back to the host or to a skipped word.
5. **Validate.** The candidate must pass `validate_name`, be nonempty after `snake_case`, and not equal the snake_cased host. Otherwise `None`.

`-N` always wins when present. `-o file.pdf` supplies the stem from the filename; skip this function.

Do **not** use title LCP for the filename. Titles are allowed to dress the PDF *after* capture (see below).

### Worked examples

| URLs (cleaned) | Result | Why |
| --- | --- | --- |
| `…/posts/my-series/part-1`, `…/posts/my-series/part-2` | `my_series` | LCP `[posts, my-series]`; `posts` skipped; last useful `my-series` |
| `…/3/tutorial/introduction.html`, `…/3/tutorial/controlflow.html` | `tutorial` | LCP `[3, tutorial]`; `3` dropped |
| `…/essay?page=1`, `…/essay?page=2` | `essay` | identical path, pagination keys |
| `…/article?page=1`, `…/article?page=2` | `article` | identical path, pagination; skipped word allowed only here |
| `…/wiki?id=France`, `…/wiki?id=Germany` | **require `-N`** | identical path, non-pagination query |
| `…/posts/abc/first`, `…/posts/xyz/second` | **require `-N`** | LCP `[posts]` is noise |
| `paulgraham.com/ds.html`, `paulgraham.com/vb.html` | **require `-N`** | empty LCP |
| different hosts | **require `-N`** | host mismatch |
| `…/cat`, `…/catalog` | **require `-N`** | segment LCP empty (string LCP would have lied) |
| three copies of the same URL | single-URL path | duplicates collapsed |

When the function returns `None`, fail before the browser:

```text
bob ref create: error: these URLs do not share a useful name; pass -N/--name
  https://paulgraham.com/ds.html
  https://paulgraham.com/vb.html
  shared path: /  (too generic)
hint: bob ref create URL1 URL2 -N pg_essays -P sase
```

When it returns a stem, print it so a disliked guess is cheap to override:

```text
name: my_series (shared path /posts/my-series)
```

Dry-run shows the same line.

### Title, author, published (after capture, not for the filename)

| Field | Rule |
| --- | --- |
| Title | `-T` if given; else strip a trailing part marker from each extracted title (`, Part N`, ` - Part N`, ` (N/M)`, ` \| page N`) and if the remainders are equal and nonempty, use that; else the first URL's title |
| Author | `-A` if given; else the unique extracted authors, displayed with the existing `A`, `A and B`, `A, B, and C`, `A et al.` helper |
| Published | `-p` if given; else the earliest `YYYY-MM-DD` among parts |
| Site | the shared site if every part agrees; else omit |
| Word count | sum |

Part titles always appear as in-document `h1`s regardless of the masthead title.

## CLI design

```text
bob ref create [OPTIONS] <TARGET>...
```

Examples that should appear in `--help`:

```bash
# series with an obvious path stem (no -N)
bob ref create \
  https://example.com/posts/my-series/part-1 \
  https://example.com/posts/my-series/part-2 \
  -P sase

# two essays, no useful prefix
bob ref create https://paulgraham.com/ds.html https://paulgraham.com/vb.html \
  -N pg_essays -P sase

# exact output path supplies the name
bob ref create URL1 URL2 -o ~/Desktop/pg_essays.pdf -P sase

# walled series, saved pages in URL order
bob ref create URL1 URL2 -H p1.html -H p2.html -N series -P sase
```

Help changes, all additive:

- Positional: `<TARGET>...` — "Markdown file, PDF file, or URL; several web article URLs merge into one PDF".
- `-N, --name` help grows: "Output filename stem [default: derived from TARGET; required for a merge with no useful shared path]".
- `-o, --output` help stays "Complete path for the generated PDF, including the .pdf filename".
- `-H, --html` help: repeatable; one file per URL, same order.
- `after_help` gains a "Merge:" paragraph with the iff rule, the 20-URL cap, all-or-nothing, and the two examples above.

`bob ref clip` inherits this through the existing alias. Completion keeps TARGET as a URL/file; several positionals are already how `bob ref find <QUERY>...` works.

### Dispatch

| argv | Behavior |
| --- | --- |
| 1 target | today's path, unchanged |
| 2+ web article URLs | merge |
| 2+ after duplicate collapse = 1 | warn, single-URL path |
| 2+ mixed kinds or non-articles | error, hint |
| merge, no `-N`, no `-o`, `shared_stem` = None | error, hint, exit 1, no network |
| merge + `-o` | exact path, no `-N` required |
| merge + `-N` | default intake under that stem |
| merge + `-o` + `-N` | clap conflict, unchanged |
| merge + `--listen` | narrate staged merged PDF |
| any URL already in library (PDF-backed) | refuse the whole merge; list the hits |
| all URLs already the same intake PDF | `--force` overwrite or `--listen` attach, as today |

## Merge pipeline (beauty)

### Why not staple PDFs

lopdf 0.40 can merge documents (upstream `merge.rs` / `pdfutil merge`): renumber objects, rebuild `/Pages`, drop outlines. What it cannot do is make N Chromium prints look like one book. Each part would keep its own masthead, its own `@page` margin boxes, and a `1 / K` that no longer matches the bound volume. Highlights quote quality also depends on a Bob-owned template (`web_url_reference_pdf_capture` final report): restapling N templates does not get worse, but it also does not get *better*, and the page-number lie is visible on every leaf.

### What to build instead

Additive adapter op, protocol still 1:

```json
{
  "protocol": 1,
  "op": "capture_many",
  "urls": [
    {"url": "https://…/part-1", "html_path": null},
    {"url": "https://…/part-2", "html_path": "/abs/p2.html"}
  ],
  "workdir": "…",
  "out_pdf": "…/render.pdf",
  "dry_run": false,
  "captured": "2026-10-15",
  "overrides": {"title": null, "author": null, "published": null}
}
```

One process, one browser. Visit in argv order. Headed fallback, once triggered, stays headed. Per-URL extract, fidelity, image localization into `assets/p{i}_*`. If any URL is `kind: pdf`, `blocked`, `thin`, or otherwise fails, the op fails and Rust writes nothing.

Then one print of a combined document:

```html
<header class="masthead">…series title, byline, date range, N parts · M words…</header>
<nav class="contents">
  <p class="contents-label">In this document</p>
  <ol>
    <li><a href="#part-1">Part 1 title</a></li>
    <li><a href="#part-2">Part 2 title</a></li>
  </ol>
</nav>
<section class="part" id="part-1">
  <h1 class="part-title">Part 1 title</h1>
  <p class="part-provenance"><a href="…">url</a> · N words</p>
  <div class="article-body">…shifted headings…</div>
</section>
<section class="part" id="part-2">…</section>
```

CSS additions in `reader.css`:

```css
.part + .part { break-before: page; }
.part-title { font-family: "Source Serif 4", Georgia, serif; font-size: 18pt; }
.contents { break-after: avoid; }
```

Footer short title is the *series* title. `counter(page) / counter(pages)` now counts the bound volume. First page still suppresses the footer title. Part-1 follows the masthead on page 1; later parts start a new leaf.

Same-document `#part-N` links become PDF internal links under Chromium print. That contents list is the cheap TOC; a two-pass TOC with leaders is not worth it.

### Timeouts and size

Keep `BOB_WEB_CLIP_TIMEOUT_SECS` as the *per-page* budget (default 300). Overall deadline is `N * per-page`, reported as `capturing 2/4 example.com…`. The 95 MiB refusal stays: a merged print that exceeds it fails closed with the existing hint. Warn at 50 MiB as today.

### Dry-run

Fail-fast naming and dedupe still run. Then `capture_many` with `dry_run: true` visits each URL (consistent with single-URL dry-run launching the browser) and skips localization + print. Report:

```text
ok would create Highlights-ready PDF (merge of 3 URLs)
name: my_series (shared path /posts/my-series)
source:
  1. https://example.com/posts/my-series/part-1
  2. https://example.com/posts/my-series/part-2
  3. https://example.com/posts/my-series/part-3
pdf: /home/bryan/bob/xlib/blogs/my_series.pdf
title: My Series
…
writes: none
next: bob ref scan
```

## Provenance, scan, dedupe

Marker extras already accept `MarkerValue::List` (`model.rs` renders `[a, b]`). For N≥2:

```yaml
- source_url: [https://example.com/posts/my-series/part-1, https://example.com/posts/my-series/part-2]
```

`as_frontmatter_value` already emits the same flow list, so scan can copy the shape into the note without a new field. Do **not** invent `source_urls` beside `source_url`. `find` already reads that key as a list.

Required companion changes, same PR:

- `sources.rs` `collect_ref_note_sources`, `collect_intake_sources`, `collect_intake_records`: take every string in a `MarkerValue::List`, not only `as_string()`.
- `frontmatter.rs` note-side import: use `value_as_string_set` (already list-aware) instead of scalar `as_string()` for `source_url` / `url`.
- `url_routing/verdict.rs` inherits the fix through `collect_recorded_source_urls`.
- Dedupe identity for a merge is the *set* of keys. `DefaultTargetIdentity::Url { keys: all_dedupe_keys }` already takes a `Vec`. A collision on *any* key refuses the merge. `--force` still only overwrites the planned intake PDF.

Identity for the default-target walk stays "these source URLs". Two merges that share one URL are the same reference for refusal purposes, which is what we want.

## Alternatives considered

| Alternative | Verdict |
| --- | --- |
| Seed plan: `-n|--name` + `-o|--output-directory` | Reject. Flag collisions, breaking tests, worse than curl's own history. |
| Always require `-N` for N≥2 | Acceptable conservative fallback if the usefulness test feels too clever in review; worse daily UX for `part-1`/`part-2`. Prefer the algorithm. |
| String LCP of the raw URLs | Reject. `/cat` vs `/catalog`. |
| Title LCP for the stem | Reject. Arrives after fetch; collides on shared openings. Titles dress the masthead only. |
| Host + date fallback (`example_com_20261015`) | Reject for merges. Fine as last resort for a *single* URL with no slug; for two URLs it hides a naming failure. |
| Interactive prompt for the name | Reject. create is scripted (`ref jobs`, tests, capture retries). Fail with a hint. |
| N Chromium prints + lopdf staple | Reject as v1 renderer. Keep in mind as a PDF-only follow-up (local chapter files), not for articles. |
| pandoc/XeLaTeX of concatenated Markdown | Reject for articles (SVG/WebP, the original clip research). Fine as a later `create a.md b.md` follow-up; pandoc already concatenates inputs. |
| Collection note pointing at N PDFs | Reject. Splits highlights, the `^ref` task, and listen. |
| `capture_many` vs N× `capture` + local combine | Prefer `capture_many` (one browser, headed state, cookies). N× capture is the compatibility fallback if the op slips; it is slower and more challenge-prone. |
| New field `source_urls` | Reject. `source_url` already has list semantics in `find`. |
| Merge in `bob capture` / `ingest_url` | Reject for v1. No name override, no parent UX for "these N URLs are one ref". |
| `--output-dir` long option | Reject. Needs a short alias; `-o` taken; default intake already is a directory. |

## Implementation sketch

Small, testable pieces, in order:

1. **`shared_stem` in `clip_url.rs`** with a table-driven unit test of every row in the worked examples. No I/O. Land this first; it is the design.
2. **List-valued URL indexing** in `sources.rs` + a create-dedupe test that a note with `source_url: [a, b]` refuses both `a` and `b`. Fixes the documented gap even without merge.
3. **clap:** `target` `.num_args(1..)`; `-H` `.action(ArgAction::Append)`; help/README/`docs/highlights-create.md`/`docs/highlights-clip.md`. `help_options.rs` still expects `-N, --name`, `-n, --no-audio`, `-o, --output` in that order.
4. **Dispatch in `create.rs` / `clip.rs`:** classify all targets; merge vs single vs error; fail-fast name; fail-fast dedupe of every key.
5. **Adapter `capture_many` + combined `assemble`.** Fixture HTML for two articles; assert one PDF, two part titles, continuous page count, assets prefixed `p0_`/`p1_`.
6. **Marker list + scan round-trip** in the existing create/scan CLI tests.
7. **`--listen`:** `{target}` = staged merged PDF; a stub listen command as in today's listen tests.
8. **Docs:** the iff rule, the 20-URL cap, `-H` zipping, "capture/jobs stay single-URL".

Out of scope for the first PR: Markdown concatenation, PDF-chapter stapling, `--output-dir`, capture-grammar merge syntax, raising the 95 MiB limit.

## Test plan

- Unit: `shared_stem` table, including the `/cat` vs `/catalog` trap and the wiki-`id` trap.
- CLI help: `<TARGET>...` present; `-n, --no-audio` still there; `-o, --output` still "complete path"; no `--output-directory`.
- Merge dry-run with a useful LCP: exit 0, `name: my_series (shared path …)`, `writes: none`.
- Merge dry-run without LCP and without `-N`: exit 1, no adapter spawn (guard with a sentinel adapter).
- Merge with `-o file.pdf` and no `-N`: accepted.
- Merge with `-o` and `-N`: clap conflict, exit 2.
- Merge with `-n` still means `--no-audio`.
- Two `--html` files zipped; one `--html` for two URLs errors; `-H -` with two URLs errors.
- Any URL already in the library: whole merge refuses, both URLs named in the error.
- List-valued `source_url` on an existing note refuses a re-import of the second URL.
- Adapter fixture: `capture_many` of two articles prints one PDF; a thin second article writes nothing.
- Scan of a merged intake PDF writes a list `source_url` and a single `^ref` task.

## Risks

- **Timeouts.** Four headed retries in one 20-minute window. Mitigate with per-page budget and a progress line `capturing k/N host…`.
- **95 MiB.** Image-heavy series will hit it. Fail closed; the hint already exists.
- **Challenge pages.** URL 2 of a series may 403 after URL 1 succeeded. All-or-nothing plus headed-sticky is the honest behavior; `--html` is the escape hatch.
- **Listen cost.** A merged PDF is longer; that is the point. Markdown already narrates long renders.
- **Flow-list YAML in a PDF annotation.** Long URL lists make a large page-1 `/Text` note. Cap at 20 URLs keeps this bounded. If a real series exceeds that, the user is doing something this feature should refuse.
- **`return_links`.** Web articles do not run the pandoc Lua filter. No change.
- **Default-target suffixing.** A merge named `tutorial` can still become `tutorial_2` when a different reference owns the stem. Print `renamed:` as today.

## Recommended solution

Ship multi-URL merge on `bob ref create` as an article-only, all-or-nothing, HTML-then-print-once feature.

Keep the flag surface:

```text
bob ref create <TARGET>...
  -N, --name STEM          already exists; required for a merge iff
                           there is no -o and no useful shared path stem
  -n, --no-audio           unchanged
  -o, --output PDF         unchanged complete path; supplies the name
  -H, --html FILE          repeatable, zipped with URLs
  -P, --parent NOTE        still required once
  -T, --title TITLE        series title override
```

Name a merge with this waterfall:

1. `-o file.pdf` → filename stem.
2. `-N STEM` → validated stem.
3. `shared_stem(cleaned URLs)` as specified (same host, segment LCP, pagination exception, existing noise rules).
4. Else error, no network, copy-pasteable hint.

Render one Bob-owned reader PDF with a series masthead, a linked contents list, and paged parts. Stamp `source_url` as a list. Index that list everywhere create currently reads a scalar.

Do not rename `-o`. Do not steal `-n`. Do not staple Chromium prints. Do not auto-name from a string prefix, a host, or a title.

That is the version I would implement.
