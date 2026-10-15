---
title: "bob ref create with several URLs: compilations, naming, and output options"
researcher: cld
date: 2026-10-15
repo: bob-cli
---

# `bob ref create` with several URLs: compilations, naming, and output options

## TL;DR

Merging several web pages into one reference is a good idea, and Bryan's own library
already shows the need. **23 of 635 external reference notes already list several
URLs** (for example `spotify_bg_agents` holds the three parts of Spotify's background
coding agents series). Those notes are link collections from the pre-Highlights era.
Today's pipeline cannot express them, because it produces one PDF per URL.

I would build it, with four adjustments to the requested plan:

1. **Do not add `-n|--name`.** `bob ref create` already has `-N, --name STEM`, and the
   PDF stem *is* the reference note's name: `bob ref scan` writes
   `ref/<type>/<stem>.md`. `-n` is already `--no-audio`, and every `-n` under
   `bob ref` means "no-…". Keep `-N` and make it the name used for a merge.
2. **Do not turn `-o` into `--output-directory`.** `-o/--output FILE` is the convention
   in pandoc, curl, gcc, percollate (the closest prior art) and bob itself
   (`bob completion bash|zsh -o FILE`). The goal behind the change, "set the name and the
   location together", already works with `-N` plus `-t`, or with
   `-o DIR/NAME.pdf`. If a directory option is still wanted later, add it the way curl
   did: a separate `-O, --output-dir DIR` that combines with `-N`. Never repurpose `-o`.
3. **Replace "common prefix" with a stricter, word-based rule.** A literal string
   prefix gives a junk name every time (`https_engineering_atspotify_com_2025_1`). The
   rule I recommend: take the *words* every URL's slug starts with. If there are none,
   use the name of the folder every URL lives in. Accept the result only when it has
   **at least two meaningful words**; otherwise require `-N`. In a prototype run against
   Bryan's real multi-URL notes plus 12 synthetic series and trap cases, it produced no
   bad names. It also fires rarely: 1 of Bryan's 14 real bundles. So `-N` is the normal
   path, and the derived name is a convenience for series like `…/foo-part-1`,
   `…/foo-part-2`.
4. **Fix list-aware dedupe first.** A merged reference has to record every URL. The
   natural field is a list-valued `source_url`, which the marker grammar and
   `bob ref find` already support. But import dedupe (`sources.rs`) reads only
   scalar values today, so a merged reference would be invisible to `bob ref create`,
   background ingest, and `bob capture` URL routing. That gap is already documented in
   `docs/ref.md`, and it must close before merging ships.

Scope v1 to **web article URLs only**: no local files, PDF URLs, or arXiv, and `-H`
cannot be combined with several targets. Merge at the **HTML level**: capture each
article, then typeset one document with the existing print template. That gives a
cover page, a linked contents list, one page break per part, PDF bookmarks per part,
and per-part running footers. The recommended solution is in the last section.

---

## 1. What exists today (verified in the code)

| Fact | Where | Why it matters |
| --- | --- | --- |
| `-N, --name STEM` exists: "Output filename stem [default: derived from TARGET]", validated as `[A-Za-z0-9][A-Za-z0-9_.-]*` (one trailing `.pdf` stripped) | `src/native/highlights_ref/create.rs` (`command()`), `clip_url.rs::validate_name` | The requested `--name` already exists. The stem becomes the PDF filename, the marker `id`, and (after `scan`) the ref note filename `ref/<type>/<stem>.md` (`stamp.rs::plan_default_target`) |
| `-n, --no-audio` exists. Under `bob ref`, `-n` is also `--no-hooks` | `create.rs`, `highlights_ref/cli.rs::no_hooks_arg` | `-n` means "no-…" here. Reassigning it would break the pattern and existing muscle memory |
| `-o, --output PDF` = "Complete path for the generated PDF, including the .pdf filename"; it conflicts with `-t` and `-N` | `create.rs` | `-o` already carries a name. `-o DIR/NAME.pdf` sets name and location together today |
| `bob completion bash/zsh -o, --output FILE` | `src/native/completion/cli.rs` | Within bob, `-o` already means "output file" |
| Web-article stem = last path segment that isn't noise (`index`, `blog`, `posts`, `p`, `article(s)`, `amp`, `en`, `en-us`, `home`, `default`, ≤2 chars, all digits, dates), with any `YYYY-MM-DD-` prefix stripped, then `snake_case`; fallbacks: title, then `<host>_<YYYYMMDD>` | `clip_url.rs::stem_from_url`, `clip.rs::capture_article` | The multi-URL name should build on this slug so that a merged name reads like a sibling of the single-URL names |
| Default-target identity already takes a **list** of dedupe keys (`DefaultTargetIdentity::Url { keys: Vec<String>, … }`) | `stamp.rs` | The `_2`, `_3` suffix walk already supports a multi-key identity |
| The marker grammar supports inline lists (`topics: [linux, performance]`); `MarkerValue::List` renders to the marker and to frontmatter | `model.rs`, `marker.rs::parse_value`, `docs/highlights-ref-sync.md` | A list-valued `source_url` round-trips with no new field |
| `bob ref find` / `list` read `source_url` and `url` as "scalars or lists" | `docs/ref.md` §Identity, `ref_library/identity.rs` | Library lookup already understands list-valued URLs |
| **Import dedupe reads only scalar values**: `value.as_string()` for note frontmatter and intake markers | `sources.rs::collect_ref_note_sources`, `collect_intake_sources` | Lists are skipped silently. `docs/ref.md` documents this gap ("A list-only match can therefore import again"). It feeds `create`, `ingest_url` (capture worker, Keep pull) and `url_routing/verdict.rs` |
| The web adapter extracts to `article.json` + `assets/`, and a separate `web_clip_render.render()` builds one HTML page and prints it in Chromium (`outline=True`, `tagged=True`) | `scripts/web_clip/web_clip_adapter.py::run_capture`, `web_clip_render.py` | Merging at the HTML level is a small, natural extension: same template and fonts, one print |
| Localized images are named `img-001.<ext>`, `svg-001.svg` **per capture** | `web_clip_adapter.py::_localize_images` | Merged renders **must** namespace assets per part, or images collide |
| The template already uses `@page` margin boxes (`@bottom-left` title, `@bottom-right` `counter(page) / counter(pages)`) | `scripts/web_clip/template/reader.css` | Per-part running footers can use named pages (Chrome 85+) together with margin boxes (Chrome 131+) |
| The SASE file hook `research-highlights` runs `bob ref create --include-id -P "$SASE_FILE_HOOK_PROJECT"` with **one** appended path per call | chezmoi `dot_config/sase/sase.yml`; SASE `docs/configuration.md` ("the matched absolute file path is appended as its final arg") | A variadic `TARGET` cannot accidentally merge hook files |
| No caller outside bob-cli's own tests uses `ref create -o` | grep over bob-plugins, bob-mac-capture, chezmoi | Changing `-o` breaks no external caller, but it would rewrite about 15 test call sites that use `-o <exact path>` as their main seam |

## 2. Is this a good idea?

### Evidence that the need is real

`bob ref list -R all -A -o external -f json` returns 635 external refs. **23 have more
than one URL.** The groupings fall into recognizable shapes:

| Shape | Examples from the library (name → URLs) |
| --- | --- |
| A multi-part series | `spotify_bg_agents` → `…/2025/11/spotifys-background-coding-agent-part-1`, `…/context-engineering-background-coding-agents-part-2`, `…/2025/12/feedback-loops-background-coding-agents-part-3` |
| Several pages of one docs topic | `zettlr_files` → `docs.zettlr.com/en/core/{workspaces,files,file-manager}`; `pandoc_custom_rw` → `pandoc.org/custom-{readers,writers}.html`; `cc_chat_buffer` → `codecompanion…/{configuration,usage}/chat-buffer` |
| One theme across one author's posts | `claude_vs_codex`, `paddo_gastown_beads` |
| A paper plus its code or explainer (mixed kinds) | `opendev` → arXiv PDF + GitHub repo; `master_pdl` → Medium post + arXiv PDF |
| Internal `go/` links | about 8 (private hosts; capture refuses them anyway) |

So Bryan has been bundling for a long time. The Highlights pipeline can't express a
bundle today, and this feature restores it.

### What a merge gains

- **One reading task, one highlight surface, one narration.** A series you read in one
  sitting becomes one `^ref` task, one PDF to annotate, and with `-L` one listen
  episode, instead of three queue rows.
- **Better reading.** Consistent typography, continuous page numbers, a contents page,
  and bookmarks per part.
- **One identity.** `bob ref find <any part URL>` reaches the bundle.

### What a merge costs, and how to address it

| Cost | Severity | Mitigation |
| --- | --- | --- |
| **A compilation is effectively immutable once annotated.** Adding "part 4" later means re-rendering, which moves page coordinates under existing Highlights annotations | Medium | Document it: merge what you will read as one unit; for an ongoing series, capture parts separately under the same `-P`. A future `--append` would need annotation migration and is out of scope |
| Per-part progress is lost (one `^ref` checkbox) | Low | That is the point of merging; Highlights annotations still show where you are |
| Per-part metadata (title, author, date) lives only in the PDF | Low | The cover's contents list and each part's masthead keep it; frontmatter keeps every URL in `source_url` |
| Dedupe gets harder (one note, many keys) | Medium | List-aware dedupe (Phase 0), which also fixes an existing documented bug |
| One part failing (bot wall, thin page) fails the whole merge | Medium | All-or-nothing with a precise `part 2/3 (<url>)` error. Rerun after fixing, or drop the part. Per-part `-H` replay is a v2 option |
| Long runtime (N browser captures) | Low | Sequential, one progress line per part (`capturing 2/3 engineering.atspotify.com…`) |

### Alternatives I considered

1. **Separate refs grouped by a shared parent** (`-P series_note`). Per-part progress,
   appendable, trivial dedupe. But it doesn't give one PDF or one narration, and it
   clutters the queue. It doesn't meet the goal. It remains the right choice for
   *ongoing* series, and the docs should say so.
2. **Variadic `TARGET` = batch** (one ref per URL, like `wget a b`). Tools that produce
   documents merge their inputs: pandoc concatenates inputs, wkhtmltopdf and pdfunite
   merge, and percollate "bundles all web pages in a single file" by default, with
   `--individual` for batch. `create` makes *a* reference, so merging is the consistent
   reading, and a shell loop already does batch. **Rejected.**
3. **An explicit `-m/--merge` flag.** It adds ceremony for no safety gain. The name
   requirement already makes accidental merges rare (most sets need `-N`), and when a
   name *is* derived (`…-part-1`, `…-part-2`), merging is almost certainly what was meant.
   **Rejected.**
4. **Concatenating separately printed PDFs (lopdf) instead of one HTML render.** That
   would give duplicate fonts, N "page 1"s, no unified contents, and seams. It is still
   the right tool for v2 *mixed* bundles (an arXiv PDF part), but not for articles.
   **Rejected for v1.**

**Verdict: build it.** Scope v1 to web articles, and document it as "merge what you'll
read as one".

## 3. Requirement adjustments (explicit)

| # | Requested | Adjusted to | Why |
| --- | --- | --- | --- |
| A1 | Add `-n\|--name` | **Keep the existing `-N, --name`.** Update its help to say it names the reference (PDF stem and ref note). It is required for several URLs unless a name can be derived | `--name` exists. `-n` is `--no-audio`. Under `bob ref`, `-n` always means "no-…" (`--no-hooks`, `--no-audio`). CLI rules: never break existing spellings |
| A2 | `-o\|--output` → `-o\|--output-directory` | **Keep `-o, --output PDF` unchanged.** For several URLs, `-o PDF` also satisfies the name requirement (its file stem is the name). Optional, deferred: a curl-style `-O, --output-dir DIR` that combines with `-N` or the derived name | `-o FILE` is the convention (pandoc, curl, gcc, percollate, `bob completion -o FILE`). curl solved exactly this problem by adding a separate `--output-dir` (7.73.0) that works alongside `-o`/`-O`. A semantic flip cannot honor the "old spelling keeps byte-identical behavior" rule. `-N` + `-t` and `-o DIR/NAME.pdf` already combine name and location. About 15 test sites use `-o` as their seam |
| A3 | Require `-n` iff the URLs share no long enough, useful common prefix | **Require `-N` (or `-o`) unless the word-based shared-name rule in §4 finds at least two meaningful words** | A character prefix produces junk. URL prefixes are mostly scheme, host, and date folders, so "long enough" cannot be measured in characters (§4.1) |
| A4 | (unstated) target kinds | **v1: two or more http(s) web article URLs only.** Local files, a mix of local files and URLs, arXiv URLs, and URLs that classify as PDF are usage errors with a clear message. Several targets cannot be combined with `-H` | Merging at the HTML level needs article captures. Mixed bundles are real (`opendev`, `master_pdl`) but need PDF concatenation; that is v2 |
| A5 | (unstated) metadata | **`source_url` becomes a list for compilations** (scalar for one URL, unchanged), and **list-aware dedupe ships first** | No new field. The library side already reads lists; dedupe silently skips them today |
| A6 | (unstated) title | **`-T`, else the words every part title shares (at least two meaningful words, original casing), else the humanized name** | The title shows in `bob ref list` and on the cover; it is derived after capture, so it never blocks |

## 4. Naming several URLs

### 4.1 Why not a literal common prefix

A character-level prefix fails the way Python's `os.path.commonprefix` does: it
compares characters, so `/usr/lib` and `/usr/local/lib` give `/usr/l`. Python added
`commonpath` (3.5) to compare whole path parts instead, and `commonprefix` is deprecated
in 3.15. Over URLs it is worse:

- Scheme and host dominate. Every pair on one host shares 20+ characters
  (`https_codecompanion_olimorris_dev`), so "long enough" in characters means nothing.
- Date folders split series: `…/2025/11/…part-1` vs `…/2025/12/…part-3` gives
  `https_engineering_atspotify_com_2025_1`.
- It cuts words in half: `intro-to-rust` vs `internals-of-go` gives `…_int`.

Every one of the 26 test sets below got a junk character prefix.

### 4.2 The recommended rule (one help sentence)

> With several URLs and no `-N`, bob names the reference after the words every URL's
> slug starts with, or, failing that, after the folder they all share. Dates, numbers,
> ids, and filler like `blog/`, `posts/`, `part` are ignored. Fewer than two meaningful
> words means you pass `-N`.

Precisely:

1. **Slug per URL.** Use exactly the segment `stem_from_url` picks today: walk the path
   from the end, skip noise segments (`SKIPPED_SEGMENTS`, ≤2 characters, all digits,
   `YYYYMMDD`/`YYYY-MM-DD`), plus (new) `@handle` and `~user` segments; strip the page
   extension and any `YYYY-MM-DD-` prefix. Host, query, and fragment never count. If any
   URL has no slug (`news.ycombinator.com/item?id=…`, a site root), there is no derived
   name.
2. **Shared slug start.** Split each slug into lowercase `[a-z0-9]+` words and take the
   longest word prefix every slug shares. Trim filler from both ends:
   `a an the of and or to in on for with from by at vs`,
   `part pt chapter ch section episode ep lesson vol volume no series`, plus pure-number
   and hex-id words.
3. **Shared folder (fallback).** If step 2 fails *and* every URL has the same folder
   path (identical up to the slug), use that folder's last segment, run through the same
   cleaning and trimming. The insight: **folder names with several words are series
   titles** (`/series/building-a-rust-service-with-nix/part-1`); **one-word folders are
   site structure** (`guide`, `book`, `core`, `configuration`, `introduction`).
4. **Gate.** Accept only with **at least two meaningful words** (words that aren't
   filler). Otherwise, require `-N`.
5. **Finish.** Convert with `snake_case` (80-character cap at a `_` boundary), check with
   `validate_name`, then plan with the usual `_2`/`_3` suffix walk using every part's
   dedupe key as the identity.

The rule is syntactic: no network calls. The "name required" error fires before any
fetch or browser launch, in the same place the missing-`-P` check fires today.

### 4.3 Evidence from the prototype

I ran four candidate rules over Bryan's 14 real multi-URL notes (public URLs only) plus
12 synthetic series and trap cases. Summary:

| Rule | Real (14) | Synthetic (12) | Bad names produced |
| --- | --- | --- | --- |
| Literal character prefix | 14 junk | 12 junk | all |
| Word prefix over the whole path (no folder logic) | 1 (`guide_introduction` ✗) | 7 | `guide_introduction`, `book_ch04` |
| Longest shared run of words anywhere in the path | 2 (`chat_buffer`, `background_coding`) | 8 | `hard_way` (Kubernetes vs Linux "the hard way"), `error_handling` (Rust vs Go posts) |
| **Recommended: slug start, else shared multi-word folder, at least 2 words** | **1 (`chat_buffer` ✓)** | **6 (all ✓)** | **none** |

Recommended-rule results in detail:

| Set | URLs (abridged) | Result |
| --- | --- | --- |
| real `cc_chat_buffer` | `…/configuration/chat-buffer.html`, `…/usage/chat-buffer` | `chat_buffer` (slug) |
| real `spotify_bg_agents` | `…/spotifys-background-coding-agent-part-1`, `…/context-engineering-background-coding-agents-part-2`, … | require `-N` |
| real `baml_intro` | `…/guide/introduction/what-is-baml`, `…/why-baml` | require `-N` (folder `introduction` is one word) |
| real `pandoc_custom_rw` | `pandoc.org/custom-readers.html`, `custom-writers.html` | require `-N` (shares only `custom`) |
| real `zettlr_files`, `nnn`, `claude_vs_codex`, … (10 more) | — | require `-N` |
| series in a folder | `/series/building-a-rust-service-with-nix/part-1`, `/part-2` | `building_a_rust_service_with_nix` (folder) |
| dated slugs | `/2024/01/tokio-internals-part-1/`, `/2024/02/tokio-internals-part-2/` | `tokio_internals` |
| ISO-prefixed slugs | `/blog/2023-06-23-raft-from-scratch-1/`, `/blog/2023-07-02-raft-from-scratch-2/` | `raft_from_scratch` |
| flat series | `/building-a-compiler-part-1`, `/building-a-compiler-part-2` | `building_a_compiler` |
| Medium series | `/@a/agentic-workflows-for-swe-dc8e…`, `/@a/agentic-workflows-in-practice-0a1b…` | `agentic_workflows` |
| cross-post | `a.dev/posts/zero-copy-parsing-in-rust`, `medium.com/@me/zero-copy-parsing-in-rust-1a2b…` | `zero_copy_parsing_in_rust` |
| Rust book chapter | `/book/ch04-01-what-is-ownership.html`, `/book/ch04-02-…` | require `-N` |
| traps | `intro-to-rust`/`internals-of-go`; `how-to-use-x`/`how-to-build-y`; `kubernetes-the-hard-way`/`linux-the-hard-way`; `the-log-…`/`the-log-revisited`; HN `item?id=` | require `-N` |

**What this means for the design:** Bryan's own bundles would need `-N` in 13 of 14
cases. Real bundles are named by meaning (`claude_vs_codex`, `spotify_bg_agents`), not
by URL structure, and no syntactic rule recovers that. So:

- `-N` is the main path. Its error message must make the fix obvious.
- The derived name must never be *bad*, because names stick. The stem becomes the PDF
  filename, the ref note filename, and the target of wikilinks, and there is no
  `bob ref rename`. A false "name required" costs about ten keystrokes; a bad derived
  name costs a manual rename across `lib/`, `ref/`, and links. Hence the strict gate.
- I rejected the "shared run anywhere" rule despite one more real hit (Spotify →
  `background_coding`), because the same flexibility names loosely related sets
  `hard_way` and `error_handling`. A prefix is also what a reader expects: you can see
  it by lining up the URLs.

### 4.4 Messages

Missing name (exit 2, a usage error like a missing `-P`, raised before any network
call):

```text
bob ref create: error: these 3 URLs need a reference name; pass -N/--name
hint: their slugs share no two-word start, for example: bob ref create -N spotify_bg_agents -P ai <URL>...
```

When something was shared but was too thin, say so: `…; they only share "custom"`. The
hint uses the existing one-line `hint:` convention.

A derived name is always reported with its source, so it is never a surprise:

```text
name: tokio_internals (shared by every URL; -N overrides)
```

### 4.5 Title

- `-T` wins.
- Otherwise, the longest word prefix every part title shares, in original casing, with
  trailing separators (`: , - – — | (`) and ordinal tails (`Part`, `1`, `I`) trimmed.
  Accept with at least two meaningful words. Example: "Building a Compiler, Part 1:
  Lexing" + "Building a Compiler, Part 2: Parsing" → "Building a Compiler".
- Otherwise, `humanize_stem(name)` with the first letter capitalized
  ("Claude vs codex"), reported as `title: … (from the name; -T sets one)`.

The title is derived after capture, so it never blocks.

## 5. CLI surface

```text
bob ref create [OPTIONS] <TARGET>...
```

- `TARGET` gains `num_args(1..)`. Help: "Markdown file, PDF file, PDF URL, arXiv paper
  URL, or web article URL; two or more web article URLs merge into one reference."
- `-N, --name STEM`: "Reference name: the PDF filename stem, which also names the ref
  note [default: derived from TARGET; for several URLs, the words they share]".
- `-o, --output PDF`: unchanged. With several URLs, its file stem is the name.
- `-T`, `-A`, `-p`, `-s`, `-P`, `-t`, `-f`, `-i`, `-a`, `-n`, `-L`, `-d`: unchanged
  meaning; with several URLs they apply to the compilation.
- `-H, --html`: with more than one `TARGET`, error:
  `--html replays one page; pass a single URL TARGET`.
- After-help gains a **Merging** paragraph and an example:
  `bob ref create https://ex.com/2024/01/tokio-internals-part-1 https://ex.com/2024/02/tokio-internals-part-2 -P sase`
  plus `… -N spotify_bg_agents -P ai`.

**Fail-fast order for several URLs.** Everything before step 8 makes no network call.

1. Every target is an http(s) URL, else `merging takes URLs only: <path> is a local file`.
2. No arXiv URLs, by the existing syntactic check (v1), else
   `arXiv papers can't be merged yet; capture <url> separately`.
3. Clean and dedupe the URLs. If two give the same key:
   `URL 2 and URL 3 are the same page (<key>)`.
4. `-H` conflicts with several targets. Validate `-N`, `-t`, and `-p` as today.
5. Resolve `-P` (as today).
6. Name: `-N`, `-o`, or the derived name; otherwise the error in §4.4.
7. Library dedupe for each part (§7), then plan the default target with all keys.
   Validate `listen_command` if `-L`.
8. The classification fetch per URL (`curl`). Any part that turns out to be a PDF:
   `part 2/3 is a PDF (<url>); merging supports web articles only`.
9. Capture each part, then compose, stamp, and install (§6).

## 6. Pipeline and adapter protocol

Additive changes; the adapter ships embedded in the binary, so both sides move in
lockstep.

- **`capture` gains `"render": false`**: write `article.json` + `assets/` into the
  part's workdir and skip printing. The response is the same, without `pdf_bytes`.
  Headed retries, fidelity checks, and bot-wall handling are reused unchanged.
- **New `compose` op**:
  `{"op": "compose", "parts": [{"article_json": …}, …], "compilation": {"title", "author", "published", "captured", "name"}, "out_pdf": …}`
  calls a new `web_clip_render.render_compilation()`.
- **Rust: a new `create_compilation_route`** beside `create_article_route`. It uses one
  `ScratchDir` with `part-1/ … part-N/` subdirectories, runs captures sequentially, then
  `compose`, then the shared `stamp_and_install`.
- **All or nothing.** Nothing touches the vault until the final atomic install, as today.
  On failure: `bob ref create: error: part 2/3 (engineering.atspotify.com/…): <adapter message>`
  plus `nothing was written to the vault`.
- **`--dry-run`** captures each part (network, as single-URL dry runs do today), skips
  compose and install, and prints the plan with every part's metadata.
- **Timeouts and budgets.** Each part keeps its own adapter timeout. The combined PDF
  keeps the 95 MiB cap; the per-capture image budget applies per part, and compose
  rechecks the total.
- **`-L, --listen`.** `{target}` is the staged compilation PDF, the same precedent as
  the Markdown route, because a listen renderer cannot take N URLs. Attach mode applies
  only when every part's key resolves to the same existing compilation.

## 7. Metadata, marker, and dedupe

Example marker (no new keys):

```text
- status: ready
- parent: sase
- title: Tokio Internals
- id: tokio_internals
- source_url: ["https://example.com/2024/01/tokio-internals-part-1/", "https://example.com/2024/02/tokio-internals-part-2/"]
- author: Jane Doe
- published: 2024-01-08
- captured: 2026-10-15
```

- `source_url` holds the cleaned URLs in argument order. It stays a scalar for a single
  URL, so nothing changes for the common case.
- `author`: one value if all parts agree, else the existing display formatter
  ("A and B", "A, B, and C", "A et al.").
- `published`: the earliest part date (labelled "first part" in reports). Each part's
  own date appears on its page.
- `-A` and `-p` override the compilation-level values only.

**Phase 0 (prerequisite): list-aware dedupe.** In `sources.rs`, read `MarkerValue::List`
items for `source_url`/`url`, both in note frontmatter and in intake markers, and push
one `RecordedSource` per item. That one change flows into `create`, `ingest_url`
(capture worker, Keep pull), and `url_routing/verdict.rs`. It also fixes the existing
documented gap for the 23 legacy list notes: they now warn as legacy hits instead of
importing again silently. Then delete the gap paragraph in `docs/ref.md`.

| Situation | Behaviour |
| --- | --- |
| A part is already a PDF-backed ref (alone or inside a compilation) | Refuse, naming the part and the ref: `part 1/3 is already captured as ref/blogs/foo.md; drop it or capture the others` |
| A part is queued in `xlib/` | Refuse. `--force` is allowed only when the queued intake has exactly the same key set |
| A part is recorded only by a legacy note with no PDF | Warn and continue (today's legacy rule); the dry run lists `legacy:` |
| The same set is already a compilation, with `-L` | Attach the episode |
| Later `bob ref create <one part URL>` | Refuse: already captured |
| Later `bob capture <part URL>` | Routes as `in_library` |
| `bob ref find <part URL>` | Finds the compilation (already works) |

Absorbing an existing single ref into a compilation (`--absorb`) is v2. In v1, refusing
is the reliable choice.

## 8. The compiled PDF

Build on `reader.css` and `assemble()`; don't fork the look.

- **Cover (page 1).** The site kicker when all parts share a site; the compilation title
  (styled like the masthead title, but *not* a heading element, so the bookmarks stay
  clean); a byline of authors; a meta line `3 articles · 8,940 words · ~39 min · captured October 15, 2026`;
  then **Contents**: a numbered list, each entry linking to `#part-N` with its title, a
  muted `site · author · date · ~12 min` line, and the dek if there is one. Chromium
  has no `target-counter()`, so the contents list has links but no page numbers; a
  two-pass render could add them later. The Highlights marker stays on page 1 as
  today.
- **Each part.** `<section class="part" id="part-N">` with `break-before: page` and
  `page: part-N`. A small kicker reads `Part 2 of 3`, followed by the existing masthead
  (site, `h1` title, dek, byline, provenance with the source link, captured date, word
  count) and the body passed through the existing `shift_headings` (top level becomes
  `h2`).
- **Bookmarks.** With `outline=True`, the parts are top-level bookmarks with their
  sections nested beneath.
- **Running footers.** One named page per part:
  `@page part-N { @bottom-left { content: "<short compilation title> · Part N" } }`,
  with the cover's left footer suppressed. The right footer keeps
  `counter(page) / counter(pages)` across the whole document. The template note about
  margin-box ordering across stylesheets applies, so emit these rules in the
  page's inline `<style>` and **confirm with a quick prototype render**.
- **Assets.** Rewrite each part's `assets/img-001.jpg` to `assets/p2-img-001.jpg`. The
  route handler forbids `/` in asset names, so use a prefix, not a subdirectory.
- **PDF Info.** Title = compilation title; Author = compilation author.

## 9. Output (illustrative)

Success:

```text
ok created Highlights-ready web PDF from 3 articles
pdf: /home/bryan/bob/xlib/blogs/spotify_bg_agents.pdf
name: spotify_bg_agents (from -N)
title: Spotify's Background Coding Agent (shared by every part title; -T overrides)
parts:
  1. Spotify's Background Coding Agent (Part 1)
     engineering.atspotify.com · Nov 2025 · 2,950 words · fidelity ok
  2. Context Engineering for Background Coding Agents (Part 2)
     engineering.atspotify.com · Nov 2025 · 3,410 words · fidelity ok
  3. Feedback Loops for Background Coding Agents (Part 3)
     engineering.atspotify.com · Dec 2025 · 2,580 words · fidelity ok
author: …
published: 2025-11-… (first part)
captured: 2026-10-15
status: ready
parent: ai
id: spotify_bg_agents
pages: 31 · images: 14/15 · size: 3.1 MB · fidelity: ok
next: bob ref scan
```

Use the existing `Styler` (green `ok`, muted per-part metadata lines). The progress
lines go to stderr on a TTY only (`capturing 2/3 engineering.atspotify.com…`,
`composing 3 articles…`), matching today's `fetching …` and `capturing …` lines.

## 10. Risks and open questions

1. **Named pages combined with margin boxes in the pinned Chromium.** Both are
   supported (`page` since Chrome 85, margin boxes since 131), but the template already
   records a cascade-order quirk. Prove it with a fixture before you depend on it. If
   it fails, use one footer for the whole compilation.
2. **List quoting in the marker.** URLs may contain `,` or `]`. Verified:
   `io.rs::can_render_plain_marker_list_string` already forces JSON quoting for values
   containing `,`, `[`, or `]`. Still add a round-trip test with such a URL
   (marker → scan → frontmatter → dedupe).
3. **Frontmatter readers outside bob-cli.** bob-plugins and Dataview queries that read
   `source_url` as a string will see a list for compilations only. The grep found no
   `ref create` callers there, but **audit `source_url` readers in bob-plugins before
   Phase 3.** Fallback if that's painful: keep `source_url` as part 1 (scalar) and add
   `source_urls` (list). That is uglier, and I'd avoid it unless the audit forces it.
4. **`published` semantics.** Earliest part (my pick) or omit when parts differ? Bryan's
   call.
5. **v2 mixed bundles** (arXiv or PDF part plus article). There is real demand
   (`opendev`, `master_pdl`). Approach: render the cover and article parts in
   Chromium, render a divider page per PDF part, then concatenate with lopdf and build
   the outline. The design above leaves room: parts are typed, and v1 just accepts one
   kind.
6. **Record the decision.** If accepted, this belongs in the `decisions` memory web
   (for example "Several create targets merge into one compilation; names come from
   shared slug words or `-N`"). Create it through `/sase_memory_write`; I have not
   written it.

## 11. Implementation plan

| Phase | Change | Tests |
| --- | --- | --- |
| 0 | List-aware `source_url`/`url` in `sources.rs` (notes and intake markers); remove the gap paragraph in `docs/ref.md` | Unit: a list note gives N `RecordedSource`s; CLI: `create <url-in-list-note>` warns or refuses correctly; `bob capture --dry-run '<url>'` reports `in_library` for a PDF-backed list note |
| 1 | New `compilation_name.rs` (pure functions: slug, folder, trim, gate); variadic `TARGET`; the fail-fast validations of §5; help text for `-N` and `TARGET`; a Merging section in after-help | Table-driven unit tests using every row of §4.3; CLI: name-required exits 2 with no network calls (fake `curl` asserts it is never called), duplicate URL, local file + URL, `-H` with several targets, arXiv in the list; the help-options alphabetical test stays green |
| 2 | Adapter: `render: false`; `compose` op; `render_compilation()` (cover, contents, parts, named-page footers, asset prefixes); `--self-test` fixture with two articles | Adapter self-test: two fixture articles → one PDF whose outline has two top-level entries, with no asset collisions; the cover contains links to `#part-1` and `#part-2` |
| 3 | `create_compilation_route`: dedupe all parts, plan with all keys, sequential captures, compose, stamp, install, `-L` (`{target}` = staged PDF), reports | CLI with `BOB_WEB_CLIP_ADAPTER` fake: the marker carries a list `source_url`; `scan` writes the list into frontmatter; a later single-part `create` refuses; a failing part 2 leaves the vault untouched; the `_2` walk; the dry-run report |
| 4 | Docs: a "Merging several URLs" section in `docs/highlights-create.md` (rules, examples, the "merge what you read as one" guidance); the usage line in `docs/highlights-ref-sync.md`; live check on athena with one real 2–3 part series | Live: `create` → `scan` → open in Highlights; the bookmarks and footers look right |

## 12. Recommended solution

**Ship a compilation mode for `bob ref create`: two or more web article URLs become one
reference with one Highlights PDF.**

1. `bob ref create [OPTIONS] <TARGET>...`. With two or more http(s) web article URLs,
   bob captures each article and typesets one PDF with the existing reader template:
   a cover, a linked contents list, each part starting on a new page with its own
   masthead, one bookmark per part, and per-part footers. It is installed at
   `xlib/<ref-type>/<name>.pdf`, ready for `bob ref scan`. v1 refuses local files,
   arXiv URLs, PDF parts, and `-H` with several targets, each with a one-line reason.
2. **Name.** Use the existing `-N, --name`, which names both the PDF and the ref note.
   Without `-N` or `-o`, bob derives a name only from words every URL's slug starts
   with, or from the multi-word folder they all share, ignoring dates, ids, and filler.
   It accepts the result only with at least two meaningful words. Otherwise it exits 2,
   before any network call, with a `hint:` showing `-N`. Derived names are always
   printed with their source.
3. **Output options stay as they are.** `-o, --output PDF` keeps its meaning, and its
   stem also satisfies the name requirement. No `--output-directory`. If one is ever
   needed, add curl-style `-O, --output-dir DIR` that combines with `-N`; never
   repurpose `-o`.
4. **Title.** `-T`, else the words every part title shares, else the humanized name.
5. **Metadata.** `source_url` becomes a list of all part URLs (no new field). Author is
   merged; `published` is the earliest part's date; `captured` is today.
6. **Dedupe.** Phase 0, shipped first: import dedupe reads list-valued `source_url`/`url`,
   which fixes a documented bug and makes compilations visible to `create`, ingest, and
   `bob capture`. Any part already captured refuses, naming that ref.
7. **Reliability.** All or nothing in private scratch; errors name `part N/M`; one TTY
   progress line per part; `-L` narrates the staged compilation PDF.
8. **Docs.** State plainly that a compilation is for material you'll read as one unit.
   An ongoing series is better captured part by part under the same `-P`.

## Sources

- Code: `src/native/highlights_ref/{create.rs, clip.rs, clip_url.rs, stamp.rs, sources.rs, model.rs, marker.rs, cli.rs}`,
  `src/native/ref_library/identity.rs`, `src/native/completion/cli.rs`,
  `scripts/web_clip/{web_clip_adapter.py, web_clip_render.py, template/reader.css}`;
  docs `docs/highlights-create.md`, `docs/highlights-ref-sync.md`, `docs/ref.md`.
- Library data: `bob ref list -R all -A -o external -f json` (635 refs, 23 with several
  URLs), read on 2026-10-15. The naming prototype was a Python script over that export;
  results are in §4.3.
- Linked repos (opened via `sase repo open`): chezmoi `home/dot_config/sase/sase.yml`
  (research-highlights file hook); grep over bob-plugins and bob-mac-capture for
  `ref create` callers; SASE `docs/configuration.md` (file hooks append one path per
  call).
- percollate (opened via `sase repo open gh:danburzo/percollate`): `README.md` (bundles
  by default, `--individual`, implicit cover and TOC for more than one page) and
  `src/util/output-path.js` (unnamed bundles become `percollate-<timestamp>`, title
  "Untitled", which is the anti-pattern a persistent library must avoid).
- [curl `--output-dir` docs (added 7.73.0)](https://gogs.librecmc.org/OWEALs/curl/src/eacc69258fcc184edbd412ef46e2f72cafd6cb18/docs/cmdline-opts/output-dir.d);
  [Daniel Stenberg, "store the curl output over there"](https://daniel.haxx.se/blog/?p=14630).
- [Chrome: page margin boxes when printing (Chrome 131)](https://developer.chrome.com/blog/print-margins);
  [Chrome 131 release notes](https://developer.chrome.com/release-notes/131);
  [caniuse: CSS `page` property (Chrome 85+)](https://caniuse.com/mdn-css_properties_page);
  [MDN: `page`](https://developer.mozilla.org/docs/Web/CSS/page).
- [Ned Batchelder, "What's the point of os.path.commonprefix?"](https://nedbatchelder.com/blog/201003/whats_the_point_of_ospathcommonprefix);
  [Ruff: os-path-commonprefix (deprecated in 3.15)](https://docs.astral.sh/ruff/rules/os-path-commonprefix/);
  [Seth Larson, "Deprecate confusing APIs like os.path.commonprefix()"](https://sethmlarson.dev/deprecate-confusing-apis-like-os-path-commonprefix).
