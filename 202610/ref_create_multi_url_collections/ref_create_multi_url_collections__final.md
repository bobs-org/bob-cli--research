# `bob ref create` with several URLs: one reference, one PDF

Consolidated report, 2026-10-15. It merges four independent reports (cdx, cld, grk, gem,
in this directory) with the lead's own research. Code references are to bob-cli `ba71710`.

## Bottom line

**Build it.** Merging a series or a reading packet into one reference is a good idea, and
the vault shows the need. On 2026-10-11, Bryan captured Stripe's two-part "Minions" series
as two references, a minute apart (06:07 and 06:08). He then gave part 2 a Depends-On link
to part 1 by hand. That leaves two PDFs, two `^ref` tasks, and a task-graph edge, all for
one piece of reading. Long before Highlights, he had already bundled sources this way: 23
of his 635 external reference notes list several URLs.

The proposed flag changes are the wrong way to get there. The design should change in
five places:

1. **Do not add `-n|--name`. Reuse the existing `-N, --name`.** It already names both the
   PDF and the ref note `scan` writes, and `-n` is already `--no-audio`. The real problem
   is discoverability. Bryan's shell history has **no** `-N` or `-t` uses but **six**
   `-o ~/bob/xlib/<type>/<name>.pdf` uses. Five of those six are exactly `-N <name>`, and
   the sixth wrote into a mistyped `xlib/paper/` directory.
2. **Keep `-o, --output PDF` as it is, and don't add `--output-directory` in v1.** The goal
   behind the request, setting the name and the location together, is already met by `-N`
   (with `-t` for the type), or by `-o DIR/NAME.pdf`.
3. **Replace "a long enough common prefix" with a word-based rule over URL slugs.** Use the
   words every URL's slug starts with, or else a multi-word folder they all share. On
   Bryan's library, directory-based variants produce junk names such as `core`,
   `configuration`, and `pdf`. The word rule names the Stripe series correctly and rarely
   fires otherwise.
4. **Read "iff" as "unless a documented rule, `-o`, or `-T` supplies a name".** Software
   can't judge whether a prefix is "useful". It can apply a predictable rule and fail fast
   with a clear hint.
5. **Make list-valued `source_url` work everywhere first.** Import dedupe reads only scalar
   URLs today, which is a gap the docs already record. Without that fix, a merged
   reference is invisible to `create`, the ingest queue, and `bob capture` routing.

v1 scope: two or more web-article URLs. They are captured one by one, composed into **one**
reader document, printed once, and installed only if every part succeeds. The recommended
solution is in the last section.

---

## 1. Is it a good idea?

### Evidence of need

| Evidence | What it shows |
| --- | --- |
| `ref/blogs/minions_stripes_one_shot_end_to_end_coding_agents{,_part_2}.md`, both captured 2026-10-11, both queued under `sase`. Part 2 carries `⛓️ DEPENDS ON` part 1 in `sase.md` | Today's workaround for a series costs two PDFs, two reading tasks, and a manual dependency edge. This is the clearest real use case |
| `bob ref list -R all -A -o external -f json`: 23 of 635 external refs list several URLs. 14 are on public hosts and 9 are internal `go/` links | Bundling is an old habit (`spotify_bg_agents`, `zettlr_files`, `pandoc_custom_rw`, `cc_chat_buffer`, …). The Highlights pipeline can't express it today |
| Bryan's shell history: `-L` appears in 10 of 28 `bob ref create` invocations | One narration per series matters, so a merged reference should support `--listen` |
| The prior research's `web_url_reference_pdf_capture__final.md` listed "multi-page article stitching" as out of scope for v1 | This feature is that deferred item |

### What a merge gains, and what it costs

A merge gives **one `^ref` task, one PDF to annotate, one listen episode, and one identity**:
`bob ref find <any part URL>` reaches it. It also reads better, with consistent typography,
continuous page numbers, and a contents page.

The costs are real and should be stated in the help and docs:

- **A collection is a snapshot.** Adding a part later shifts the pages under existing
  Highlights annotations. `create` must not become an updater. An ongoing series is better
  captured part by part under the same `-P`.
- **Progress is tracked per collection, not per part.** That is the point of merging.
- **Dedupe gets harder,** because one note now has many URL keys (§6).

### Alternatives considered

| Alternative | Verdict |
| --- | --- |
| Separate refs plus a dependency (today's workaround) | Still right for ongoing series. Wrong for "read these together": it splits the PDF, the narration, and the task |
| Several targets as a batch, one ref per URL (like `wget a b`) | Rejected. Document tools merge their inputs (pandoc, pdfunite, percollate bundles by default), and a shell loop already does batch. Two targets are a clap error today, so no script depends on either meaning |
| An explicit `--merge` flag | Rejected as ceremony. The naming gate already makes an accidental merge rare, and a derived name only appears when the URLs really look like one series |
| Concatenating separately printed PDFs (qpdf/lopdf) | Rejected for articles. Page counters restart, mastheads repeat, and metadata and outlines conflict. It stays the right tool for a later PDF/arXiv-part feature |
| A collection note that links to N PDFs | Rejected. It splits highlights, the `^ref` task, and listen |
| A bundling gesture in `bob capture` / Mac Capture | Out of scope. The Stripe pair isn't in shell history, so it probably arrived through capture or the jobs queue. A capture-side gesture is a later, separate design that crosses repos |

---

## 2. Requirement adjustments (explicit)

| # | Requested | Adjusted to | Why |
| --- | --- | --- | --- |
| **A1** | Add `-n\|--name` | **Keep `-N, --name STEM` and rewrite its help:** "Reference name: the PDF filename and the ref note `bob ref scan` writes" | `--name` exists (`create.rs:300`), and its stem becomes the PDF name, the marker `id`, and `ref/<type>/<stem>.md`. `-n` is `--no-audio` (`create.rs:307`), so taking it would make `-n` swallow the next argument as a name. Bryan never used `-N` because its help says only "Output filename stem" |
| **A2** | `-o\|--output` → `-o\|--output-directory` | **Keep `-o, --output PDF` unchanged; no directory option in v1.** With several URLs, the `-o` filename also counts as the name | All six of Bryan's `-o` uses were intake paths that `-N` (and `-t`) express more briefly, and more safely: one had the typo `paper/`. Turning `-o` into a directory would make `-o x.pdf` create a directory named `x.pdf/`. Every report rejected that flip. If a non-intake directory use appears later, add curl-style `-O, --output-directory DIR` (`-O` is free) that conflicts with `-o` and `-t` |
| **A3** | Require the name iff no long, useful common prefix | **Require a name unless `-o`, the slug-word rule (§3), or `-T` supplies one.** Explicit naming is always allowed | A character prefix is junk on every real bundle (§3.1). Usefulness can't be proven, but a documented rule is predictable. Using `-T` as a fallback mirrors the single-URL order, `-N` → URL slug → title (`clip.rs:351-355`) |
| **A4** | (unstated) target kinds | **v1 accepts only http(s) web-article URLs.** Local files, arXiv URLs, and URLs that turn out to be PDFs are errors, each with a one-line reason | Merging at the HTML level needs article captures. Mixed bundles are real (`opendev`, `master_pdl` pair an arXiv PDF with a page) but need PDF stitching: v2 |
| **A5** | (unstated) metadata | **`source_url` becomes an ordered list for collections** (it stays a scalar for one URL), and **list-aware import dedupe ships first** | No new field. `find` already reads lists. `create`, ingest, and routing silently skip them (`sources.rs:138,211,305`; documented at `docs/ref.md:138-142`) |
| **A6** | (unstated) option interactions | **`-L` works and narrates the staged collection PDF. `-H` with several URLs is an error in v1** | `-L` follows the Markdown precedent of passing the staged PDF as `{target}` (`docs/highlights-create.md:353-356`), and Bryan uses it on about a third of his captures. Zipping `-H` files to URLs by position silently misattributes content if the order is wrong |
| **A7** | (unstated) overlap | **Refuse when any part already belongs to a PDF-backed or queued reference.** Warn and continue for legacy notes without a PDF | One URL, one reference. Shared keys among PDF-backed notes raise `duplicate_identity` in the library (`ref_library/mod.rs:718-760`), and the prior design made URL dedupe a hard stop |

---

## 3. Naming a collection

### 3.1 Why not a literal common prefix

A character prefix of URLs is dominated by the scheme, the host, and date folders, and it
cuts words in half:

- Spotify's three parts give `https_engineering_atspotify_com_2025_1`.
- `cats` and `cars` give `ca`.

Python's `os.path.commonprefix` makes the same mistake (`/usr/lib` and `/usr/local/lib`
give `/usr/l`), which is why `commonpath` exists. Path-segment prefixes are better, but on
real URLs the shared folders are mostly site structure (`docs`, `core`, `configuration`,
`pdf`, `engineering`).

### 3.2 The recommended rule

Help text, in one sentence:

> With several URLs and no `-N`, bob names the reference after the words every URL's slug
> starts with, or failing that the folder they all share, ignoring dates, ids, part numbers,
> and filler. It needs two meaningful words (or one, when the pages differ only by a part
> or page number); otherwise pass `-N` or `-T`.

Precisely, as a pure function with no network access, called where the missing-`-P` check
runs today:

1. **Same site.** Every cleaned URL (`validate_and_clean`) has the same host, lowercased
   and without `www.`. If not, there is no derived name.
2. **Slug per URL.** Use exactly the segment `stem_from_url` picks today (`clip_url.rs:250`):
   the last segment that isn't noise (`SKIPPED_SEGMENTS`, ≤2 characters, all digits,
   dates). Also skip `@handle` and `~user` segments. Strip the page extension and any
   `YYYY-MM-DD-` prefix. If any URL has no slug (a site root, `item?id=…`), there is no
   derived name.
3. **Shared slug start.** Split the slugs into lowercase `[a-z0-9]+` words and take the
   longest word prefix they all share. Trim from both ends: filler words
   (`a an the of and or to in on for with from by at vs`), series words
   (`part pt chapter ch section episode ep lesson vol volume no series page`), and number
   or hex-id words.
4. **Gate.** Accept when there are **at least two meaningful words and at least one is not
   generic**. The generic list is small, documented, and table-tested: `getting started
   introduction overview guide tutorial reference docs configuration usage core …`. Also
   accept **one word of four or more letters, not generic, when the URLs differ only by a
   part or page number** (`raft-part-1`/`raft-part-2`, `/essay?page=1`/`?page=2`).
5. **Folder fallback.** If step 4 fails and every URL has the same folder path, apply the
   same cleaning and gate to that folder's last segment. Multi-word folders are series
   titles (`/patterns-of-distributed-systems/…`). One-word folders are site structure
   (`core`, `configuration`, `tutorial`, `book`) and never qualify.
6. **Finish.** Apply `snake_case` (80-character cap) and `validate_name`, then the usual
   `_2`/`_3` collision walk.

The stem waterfall for collections is: **`-N` → the `-o` filename → this rule →
`snake_case(-T)` → error.** All of it runs before any fetch.

### 3.3 Evidence: five rules on Bryan's data

The lead prototyped each report's stated rule (Python approximations of the prose specs,
not the reports' own code) and ran them over two corpora.

**Corpus A: 51 labeled sets.** These are the 14 public real bundles, the Stripe pair, and
36 synthetic series and traps drawn from all four reports. An *ok* is the expected name or
an accepted "pass `-N`". A *bad* is a wrong name. A *miss* is "pass `-N`" where a good name
existed.

| Rule | ok | bad | miss | Characteristic failures |
| --- | --- | --- | --- | --- |
| grk: shared path segments only | 38 | 8 | 5 | **Misses the Stripe pair** and every flat `-part-N` series. Names `introduction`, `configuration`, `core`, `tutorial`, `book`, `wiki` |
| gem: deepest folder, then slug-token prefix | 35 | 15 | 1 | `learning`, `introduction_to`, `how_to`, `the_log`, `item`, `wiki`, `custom` |
| cdx: slug or topic folder, letter thresholds | 44 | 6 | 1 | `core`, `configuration`, `tutorial`, `book` |
| cld: slug words, else multi-word folder, ≥2 words | 49 | 2 | 0 | `getting_started`, `user_guide` (generic folders) |
| **lead: cld + same host + generic gate + one-word series** | **51** | **0** | **0** | Tuned on this corpus, so this row is not independent proof |

**Corpus B (held out): all 2,987 same-host pairs of separate refs** in the library (208
hosts). Any name derived for two unrelated refs is a likely false positive.

| Rule | Pairs named | Most common names |
| --- | --- | --- |
| grk | 726 | `pdf` ×561 (arXiv `/pdf/`), `engineering` ×55, `abs`, `docs`, `configuration`, `core` |
| gem | 149 | `engineering`, `docs`, `configuration`, `core`, `main`, `latest` |
| cdx | 134 | `engineering`, `configuration`, `core`, `main`, `latest`, `blob` |
| cld | 10 | see below |
| lead | 10 | the same 10 as cld |

The ten pairs named by cld and lead are:

- the Stripe series (correct);
- three pairs from Fowler's "Exploring Gen AI" series, named `exploring_gen_ai` (correct);
- four `claude_code` pairs (an accurate topic);
- one `agentic_ai` pair (coincidental but descriptive);
- one `so_i_switched_to_neovim` pair, which is the same Medium article stored once with
  `%40` and once with `@`. Duplicate-input refusal should catch that; see §6.

**Conclusions:**

- The word rule fires rarely. 13 of 14 real bundles need `-N`, because Bryan names bundles
  by meaning (`claude_vs_codex`, `spotify_bg_agents`).
- It fires on real series.
- On real data it essentially never produces a bad name. That matters because names stick:
  the stem names the PDF, the note, and every wikilink, and there is no `bob ref rename`.
- A false "pass `-N`" costs ten keystrokes. A bad name costs a manual rename across `lib/`,
  `ref/`, and links. Hence the strict gate.

The one-word series branch (step 4) is the most droppable refinement. It never fired on
real data.

### 3.4 Messages

When no name is found, exit 2 with an `error:` plus a `hint:`, the same shape as the
missing-`-P` error. Nothing touches the network:

```text
bob ref create: error: these 3 URLs need a reference name
  1  engineering.atspotify.com/2025/11/spotifys-background-coding-agent-part-1
  2  engineering.atspotify.com/2025/11/context-engineering-background-coding-agents-part-2
  3  engineering.atspotify.com/2025/12/feedback-loops-background-coding-agents-part-3
hint: their slugs share no common start; pass -N <name> (or -T <title>)
```

When something was shared but too thin, say so: `hint: they only share "custom"; pass -N
<name>`. A derived name is always printed with its source, in normal and dry-run output,
and never needs confirmation: `name: tokio_internals (words every URL starts with; -N
overrides)`.

As a cheap extra, when step 3 sees series numbers out of argument order, print a warning
(`URLs are in part order 2, 1; the PDF follows argument order`). Never re-sort.

### 3.5 Title, author, date (derived after capture, never blocking)

- **Title:** `-T` if given. Otherwise the longest prefix every part title shares, cut at a
  word boundary. Treat `—`, `–`, `:`, `|`, `(` and `,` as boundaries, then trim trailing
  separators and ordinals (`Part`, `2`, `II`). Require at least two meaningful words.
  Otherwise use the humanized name.
  - The real Stripe titles are "Minions: Stripe’s one-shot, end-to-end coding agents" and
    "…agents—Part 2". Note the em dash with no spaces. They yield **"Minions: Stripe’s
    one-shot, end-to-end coding agents"**. The humanized stem would give "minions stripes
    one shot end to end coding agents", which is much worse.
  - Never use part 1's title for the whole collection.
- **Author:** one value if every part agrees. Otherwise the existing formatter ("A and B",
  "A, B, and C", "A et al."). `-A` overrides only the collection-level value.
- **Published:** the earliest part date. `-p` overrides it. Each part's own date stays on
  its page.
- **Captured:** today.

---

## 4. CLI contract

```text
Usage: bob ref create [OPTIONS] <TARGET>...

  <TARGET>...       Markdown file, PDF file, PDF URL, arXiv paper URL, or web article URL;
                    two or more web article URLs become one reference
  -N, --name <STEM> Reference name: the PDF filename and the ref note `bob ref scan` writes
                    [default: derived from TARGET; for several URLs, the words their slugs share]
  -o, --output <PDF>  unchanged; with several URLs its filename is the name
```

No option is added or renamed, so the alphabetical help test (`tests/cli/help_options.rs`)
stays as it is. `after_help` gains a **Several URLs** paragraph (the naming sentence,
all-or-nothing, "for material you'll read as one unit", and the cap) plus two examples:

```bash
bob ref create https://example.com/2024/01/tokio-internals-part-1 \
               https://example.com/2024/02/tokio-internals-part-2 -L -P sase
bob ref create URL1 URL2 URL3 -N spotify_bg_agents -P sase
```

Parsing: use `.num_args(1..)` with normal option parsing, so options can come before or
after the URLs. No trailing-var-arg mode and no comma splitting. Targets stay `OsString`,
so single-target local paths don't regress. The `research-highlights` SASE file hook
appends one path per call, so it can never merge files by accident.

**Fail-fast order.** Nothing touches the network before step 7.

1. Two or more targets select the collection route. One target behaves exactly as today.
2. Every target is an http(s) URL and none is syntactically arXiv. `-H` is absent.
3. Clean every URL and refuse duplicate dedupe keys, naming both positions (`URL 1 and URL 3
   are the same page`). Allow at most **20** URLs, because of the 95 MiB vault limit,
   timeouts, and accidental `$(cat …)` lists.
4. Resolve `-P` and validate `-N`, `-t`, and `-p`, as today.
5. Run the name waterfall (§3.2), or fail with the error in §3.4.
6. Run list-aware dedupe on every part (§6), then plan the default target with all keys and
   run the listen preflight.
7. Classify each URL with `curl`. A part that is a PDF fails with
   `part 2/3 is a PDF (<url>); merging supports web articles only`.
8. Capture the parts sequentially, compose, stamp once, and install.

---

## 5. Building one beautiful PDF

Every report agreed: **merge at the HTML level and print once.** The seam already exists.
The adapter writes `article.json` and then calls `web_clip_render.render(article_json,
out_pdf, launcher)` (`web_clip_adapter.py:1583-1593`, `web_clip_render.py:441`), which
prints with `outline=True, tagged=True` (`web_clip_render.py:419`).

**Pipeline.** Use cld's shape: Rust orchestrates, and the adapter's v1 single-capture
contract stays byte-identical.

- `capture` gains `"render": false`. It writes `article.json` plus `assets/` into
  `part-N/` and skips printing. Headed retries, fidelity checks, and bot-wall handling are
  reused unchanged.
- A new `compose` op takes the ordered `article.json` paths and collection metadata, calls
  `render_collection()`, and prints once.
- This beats grk's single `capture_many` op because Rust gets per-part progress lines,
  per-part timeouts, and clean `part N/M` failure attribution for free. Tests can also fake
  each op separately.

**Layout.** Build on `reader.css` (Source Serif 4, Inter, JetBrains Mono); don't fork the
look.

- **Opening page.** The site kicker when all parts share a site, the collection title, a
  byline, and a meta line (`2 articles · N words · ~M min · captured October 15, 2026`).
  Then a **Contents** list: numbered entries linking to `#part-N`, each with a muted
  `site · author · date` line. The Highlights marker stays on page 1.
  - Chromium has no `target-counter()`, so the contents can't show page numbers in a
    single pass. gem's mockup with page numbers isn't feasible in v1.
- **Each part** is a `<section id="part-N">` with `break-before: page`, so every part
  starts at the top of a page with no blank leaves. Inside: a small `Part 2 of 3` kicker,
  the existing masthead (title, dek, byline, source link), and the body through the
  existing `shift_headings`.
- **Outline.** Parts are top-level bookmarks with their sections nested underneath. Check
  this against the real PDF; don't assume CSS produces it.
- **Footer.** The collection's short title on the left, and `counter(page) /
  counter(pages)` on the right across the whole volume. Per-part running footers through
  named pages need Chrome 131+ margin boxes; the pinned Playwright 1.62 should qualify. Add
  them only after a prototype render proves the template's cascade quirk is handled.
- **Isolation.**
  - Prefix every imported `id` and local `#fragment` with the part (`#p2-fn1`), including
    SVG references, because two pages both have `#introduction` and `#fn1`.
  - Resolve each part's relative links against its own final URL.
  - Rename assets `p2-img-001.jpg`. The localizer names them per capture (`img-001`,
    `svg-001`, at `web_clip_adapter.py:1118,1134`), and the offline route forbids `/` in
    asset names.
- **PDF Info:** the collection's title and author.

---

## 6. Provenance, dedupe, and identity

**Marker** (no new keys; inline lists already round-trip):

```text
- title: Minions: Stripe’s one-shot, end-to-end coding agents
- id: minions_stripes_one_shot_end_to_end_coding_agents
- source_url: ["https://stripe.dev/blog/minions-stripes-one-shot-end-to-end-coding-agents", "https://stripe.dev/blog/minions-stripes-one-shot-end-to-end-coding-agents-part-2"]
- captured: 2026-10-15
```

URLs containing `,`, `[` or `]` are already forced into JSON quoting
(`io.rs:242`); add a round-trip test anyway. `scan` copies the list into frontmatter.

**Phase 0 (ships on its own): list-aware import dedupe.** In `sources.rs`, push one
`RecordedSource` per item of a list-valued `source_url`/`url`, for both note frontmatter
and intake markers. This one change reaches `create`, `ingest_url` (the capture worker and
Keep pull), and `url_routing/verdict.rs`. It also fixes today's documented gap for the 23
legacy list notes. Then delete the gap paragraph in `docs/ref.md`.

**Overlap policy.**

| Situation | Behavior |
| --- | --- |
| A part is already a PDF-backed ref, standalone or inside a collection | Refuse, naming the part and the ref: `part 1/2 is already captured as ref/blogs/…md` |
| A part is queued in `xlib/` | Refuse. `--force` applies only when the queued PDF has exactly the same ordered sources |
| The same ordered sources already form a collection | Today's `already captured` / `already queued`; `-L` attaches the episode |
| A part appears only in a legacy note without a PDF | Warn and continue. The library then marks that note `superseded_by` the collection (`ref_library/mod.rs:762-781`), which gives the 23 legacy bundles a clean migration path |
| Later, `bob ref create <one part URL>` or `bob capture <part URL>` | Refused or routed `in_library`; `find` returns the collection |

cdx argued for creating the collection anyway on partial overlap. The library would then
put `duplicate_identity` on both notes, and the overlap would break the one-URL,
one-reference invariant that `find`, routing, and the prior capture design depend on.
**Refusing is the reliable v1.**

The cost shows up immediately: the Stripe pair can't be re-bundled without first removing
both refs, both `^ref` tasks, and the Depends-On edge in `sase.md`. An `--absorb` for
unread, unannotated refs is a possible v2 (open question 1).

**Consumers checked.**

- **bob-plugins** has no `source_url` readers.
- **Bob Mac Capture** decodes `urls: [String]` from `bob ref list` JSON, so it is already
  list-ready. Its Open Source and Copy actions use `urls.first`
  (`RefsCopy.swift:281`, `RefsActionsMenu.swift:88`), so a collection opens part 1. That
  is acceptable for v1, with a "Sources ▸" submenu as polish later.

**Side finding.** Dedupe keys don't normalize `%40` against `@`:
`medium.com/%40edominguez.se/…` and `medium.com/@edominguez.se/…` are stored as different
keys on two notes for the same article. That matters for the duplicate-input check, and for
routing generally. It is worth a small follow-up bug.

---

## 7. Reliability and output

- **All or nothing.** Every part is captured into private scratch, and nothing touches the
  vault until the final guarded install. On failure:
  `bob ref create: error: part 2/3 (engineering.atspotify.com/…): <adapter message>` plus
  `nothing was written`. Never silently drop a part.
- **Budgets.**
  - Each part keeps `BOB_WEB_CLIP_TIMEOUT_SECS` (300 s). Compose gets its own bounded
    deadline.
  - The image budget is checked per part and again at collection scope.
  - The combined PDF keeps the 50 MiB warning and the 95 MiB refusal.
- **`--dry-run`** keeps today's meaning: web articles load in the browser, while
  localization and the print are skipped. It reports the name and its source, the ordered
  parts, the destination, overlap decisions, and the planned marker. A missing name still
  fails before any browser starts.
- **`-L`** narrates the staged collection PDF as `{target}`, with the collection title as
  `{title}`. Check once that the contents page and footers narrate acceptably. The
  Markdown route already relies on this path.
- **Progress** goes to stderr on a TTY only: `capturing 2/3 engineering.atspotify.com…`,
  then `composing 3 articles…`. Success output uses the existing `Styler`:

```text
ok created Highlights-ready PDF from 2 web articles
name: tokio_internals (words every URL starts with; -N overrides)
title: Tokio Internals (shared by every part title; -T overrides)
parts:
  1/2  Tokio Internals, Part 1: The Scheduler      example.com · N words · fidelity ok
  2/2  Tokio Internals, Part 2: The Reactor        example.com · N words · fidelity ok
pdf: ~/bob/xlib/blogs/tokio_internals.pdf
pages: N · images: N/N · size: N MB
next: bob ref scan
```

---

## 8. Where the reports disagreed, and the resolution

| Topic | Positions | Resolution |
| --- | --- | --- |
| Directory option | cdx and gem add `-O`; cld defers; grk rejects | **Defer.** Shell history shows the need is naming, which `-N` covers |
| Naming algorithm | Folder first (gem, grk); slug words plus multi-word folder (cld); mixed thresholds (cdx) | **cld's core plus three refinements**, based on §3.3. grk's rule misses the motivating Stripe case |
| Same host required | cdx, grk, gem yes; cld no | **Yes.** A cross-host pair is a curated packet, so name it explicitly |
| `-T` satisfies naming | cdx yes; others silent | **Yes, as the last fallback**, matching the single-URL order |
| Collection title | cdx: humanized stem; grk: else part 1's title; cld: shared title words | **cld**, with boundaries that understand em dashes. Never part 1's title |
| Author and date when parts differ | cdx: omit; cld, grk: combine, earliest | **Combine authors; earliest date.** Each part keeps its own on its page |
| Duplicate input URLs | grk: collapse and warn; cdx, cld: refuse | **Refuse.** It is almost always a paste error |
| Overlap with an existing ref | cdx: create anyway; cld, grk, gem: refuse | **Refuse** (§6) |
| `--listen` | cdx: reject in v1; others: narrate the staged PDF | **Support** |
| `--html` | grk: repeatable, zipped by position; cdx, cld: reject | **Reject in v1.** Pairing needs verification against each saved page's recorded URL |
| Adapter shape | cld: `render:false` plus `compose`; grk: `capture_many`; gem: `urls[]` in capture | **cld** (§5) |
| Part 1 placement | grk: below the masthead on page 1; others: opening page, then a page per part | **Opening page, then every part on a fresh page**, for symmetric part starts |
| URL cap | grk: 20; others: none | **20** |

**Corrections to individual reports:**

- **cld** says no caller outside tests uses `-o`. That holds for scripts, but Bryan uses it
  interactively. cld's sample title for the Spotify set contradicts its own rule, because
  those titles share no prefix.
- **gem** places notes at `Highlights/<type>/`; the real location is `ref/<type>/`. gem's
  contents page with page numbers isn't feasible in one Chromium pass.
- **cdx** would drop `-L` in v1, which Bryan uses on about a third of his captures.

---

## 9. Implementation plan

| Phase | Change | Key tests |
| --- | --- | --- |
| 0 | List-aware `source_url`/`url` in `sources.rs`; remove the gap paragraph in `docs/ref.md` | A list note yields N sources. `create` of a URL from a list note warns or refuses. `bob capture --dry-run` reports `in_library` for a PDF-backed list note |
| 1 | New pure `collection_name.rs`; variadic `TARGET`; the fail-fast validations of §4; help for `-N` and `TARGET`; the after-help paragraph | Every row of §3.3 plus permutations. A missing name exits 2 without spawning `curl` or the adapter (a sentinel fake proves it). Duplicate URLs, a local file in the list, arXiv in the list, `-H` with several URLs. `-n` still means `--no-audio`. `-o` plus `-N` is still a clap conflict |
| 2 | Adapter: `render:false`, the `compose` op, `render_collection()` (opening page, contents, parts, isolation); a two-article self-test fixture | One PDF whose outline has two top-level entries. No asset or `id` collisions. Contents links resolve. No blank leaves. Continuous counters |
| 3 | `create_collection_route`: dedupe, plan, sequential capture, compose, stamp, install; `-L`; reports | With a `BOB_WEB_CLIP_ADAPTER` fake: the list `source_url` survives scan, giving one note and one `^ref` task. A later single-part `create` refuses. A failing part 2 writes nothing. The `_2` walk. The dry-run report |
| 4 | Docs (`highlights-create.md` "Several URLs", `highlights-clip.md`, `ref.md`); a live check on athena | A live run on a real two- or three-part series, not the already-captured Stripe pair: `create -L` → `scan` → open in Highlights, check bookmarks and footers, play the episode |

Verification gates: `just check` and `just check-web-clip-adapter`. The latter can skip
browser fixtures when no browser is found, so a green run is not visual validation. Once
the design is accepted, record it in the `decisions` memory web through
`/sase_memory_write`, for example "Several create targets merge into one reference; names
come from shared slug words, `-N`, `-o`, or `-T`".

## 10. Open questions for Bryan

1. **The Stripe pair.** Leave it as two refs, or remove both and recapture them as one?
   Removing means deleting both notes and PDFs, plus the two `^ref` tasks and the
   Depends-On edge in `sase.md`. Is a v2 `--absorb` for unread, unannotated refs worth
   designing?
2. **A directory option.** Is there a real use outside intake? If so, add
   `-O, --output-directory DIR` later; never repurpose `-o`.
3. **The one-word series branch.** Keep it (`raft-part-1/2` → `raft`) or drop it? It never
   fired on real data.
4. **Published date.** Earliest part, or omit it when the parts differ?

---

## Recommended solution

Ship **ordered multi-URL collections in `bob ref create`**:

1. **`bob ref create [OPTIONS] <TARGET>...`.** Two or more http(s) web-article URLs, in
   argument order, become **one reference**: one intake PDF at
   `xlib/<ref-type>/<name>.pdf`, then (after `scan`) one note and one `^ref` task. One
   target behaves exactly as today. v1 refuses local files, arXiv URLs, PDF parts, `-H`,
   duplicate URLs, and more than 20 URLs, each with a one-line reason.
2. **Naming.** Keep `-N, --name` and rewrite its help so it plainly names the reference.
   The stem comes from `-N`, then the `-o` filename, then the slug-word rule (§3.2), then
   `-T`. Otherwise exit 2 before any network call, with a `hint:`. The rule needs the same
   host and at least two meaningful words, one of them specific, from the start of every
   slug or from a shared multi-word folder. One word is accepted only for a part-numbered
   series. Derived names are always printed with their source.
3. **Output flags.** `-o, --output PDF` and `-n, --no-audio` don't change. No
   `--output-directory` in v1.
4. **The document.** Capture each part with the existing engine (`render:false`), then
   compose one reader document and print it once: an opening page with a linked contents
   list, each part on a fresh page with its own masthead, one bookmark per part,
   continuous page numbers, and namespaced ids and assets. Stamp once.
5. **Identity.** Ship list-aware import dedupe first (Phase 0). `source_url` becomes the
   ordered URL list. Any part already in a PDF-backed or queued reference refuses the
   whole collection; legacy PDF-less notes are superseded.
6. **Reliability.** All or nothing in scratch. Errors name `part N/M`. Per-part timeouts
   apply, and size limits are checked on the combined PDF. `-L` narrates the staged
   collection PDF.
7. **Docs.** Say plainly that a collection is for material you'll read as one unit, and
   that an ongoing series is better captured part by part.

---

## Sources

- **bob-cli `ba71710`:**
  - `src/native/highlights_ref/create.rs` (`command()`: 236-375)
  - `clip.rs` (stem waterfall: 340-362)
  - `clip_url.rs` (`SKIPPED_SEGMENTS`: 18, `validate_name`: 230, `stem_from_url`: 250)
  - `sources.rs` (scalar reads: 138, 211, 305)
  - `stamp.rs` (`DefaultTargetIdentity`: 39, `candidate_is_same_reference`: 294,
    `validate_ref_type`: 559)
  - `io.rs:242`
  - `src/native/ref_library/mod.rs` (`apply_supersession`: 718-782)
  - `scripts/web_clip/web_clip_adapter.py` (protocol v1: 56; asset names: 1118, 1134;
    render seam: 1583-1593)
  - `scripts/web_clip/web_clip_render.py` (`print_pdf`: 393-438, `render`: 441)
  - `docs/ref.md` (Identity: 114-142)
  - `docs/highlights-create.md` (dry run: 115-129, listen placeholders: 353-360)
  - `bob ref create --help`
- **Linked repos** (opened with `sase repo open`): bob-mac-capture `Sources/RefsCore/{RefsDecoding,RefsCopy}.swift`
  and `Sources/BobMacCapture/Refs/RefsActionsMenu.swift`; bob-plugins (no `source_url`
  readers).
- **Vault data, 2026-10-15:**
  - `bob ref list -R all -A -o external -f json`: 635 refs, 23 with several URLs, 2,987
    same-host pairs.
  - The two Stripe Minions ref notes and their task lines in `sase.md`.
  - `~/.zsh_history`, filtered to `bob ref create`: 28 invocations, 6 with `-o`, 10 with
    `-L`, none with `-N` or `-t`.
- **Naming prototype:** a lead-written Python script implementing approximations of the
  five rules, run over the two corpora in §3.3.
- **Prior research:** `research:202610/web_url_reference_pdf_capture/web_url_reference_pdf_capture__final.md`
  (A3 "never silently wrong", A6 URL dedupe and immutable library PDFs, multi-page
  stitching out of scope).
- **External** (via the individual reports): curl `--output-dir` (7.73.0) and Daniel
  Stenberg's post; percollate's README (bundling by default, `--individual`);
  Python `os.path.commonprefix` vs `commonpath`; Chrome 131 print margin boxes; CSS `page`
  (Chrome 85+); W3C CSS Fragmentation `break-before`; Playwright `page.pdf` (`outline`,
  `tagged`); qpdf page-selection limitations; RFC 3986 §3.3.
- **Individual reports:** `ref_create_multi_url_collections__{cdx,cld,grk,gem}.md` in this
  directory.
