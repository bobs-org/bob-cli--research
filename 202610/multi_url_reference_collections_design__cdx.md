# Multi-URL reference capture: an ordered reading collection

Independent research and design recommendation by **cdx**, 2026-10-15.

This report was researched independently. No report, transcript, or findings from the other researchers in this swarm were consulted. Repository observations refer to bob-cli commit `ba717105385bc15513a23f27591d0ccdfa96b36e`. This is a design investigation, not an implementation; the examples and acceptance cases below describe proposed behavior.

## Judgment

**Yes: merging a deliberately chosen group of pages into one reading reference is a good feature.** It fits a tutorial, multipart essay, or short reading packet particularly well. The right product model is an **ordered collection**: one PDF, one reference note after scan, one reading task, and several independently attributed source articles. The contents must remain separate and navigable inside the PDF.

I would implement this in `bob ref create` through multiple positional URLs. I would change three parts of the proposed requirements:

1. **Reuse the existing `-N/--name`.** It already names the output stem; `-n` already means `--no-audio`. Reassigning it would break existing invocations.
2. **Add `-O/--output-directory`; retain `-o/--output` as an exact PDF path.** Reinterpreting an old file argument as a directory is an avoidable compatibility trap. Directory output and `--name` work together without taking over `-o`.
3. **Define “a useful common prefix” as an explicit, conservative URL-path naming policy.** Software cannot prove usefulness from a URL. Do not promise a semantic “if and only if” that arbitrary URL syntax cannot establish. Also accept existing explicit naming information from `--title` or a full `--output` filename, rather than requiring a redundant `--name`.

These adjustments preserve the requested outcome while making the CLI more predictable. A first release should accept several HTML article/page URLs, preserve their order, and publish only a complete collection. It should not silently crawl a series, combine summaries, or append to a previously annotated PDF.

## What exists today, and why it matters

The current command is farther along than the proposed flag changes assume:

| Area | Observed behavior | Design consequence |
| --- | --- | --- |
| Name | `-N/--name STEM` already exists; it conflicts with `--output`. Validation allows an ASCII filename stem, with one optional `.pdf` suffix. | Extend the existing concept; do not add a competing name option or quietly turn it into a free-form title. |
| Audio | `-n/--no-audio` already exists. | Lowercase `-n` is occupied. |
| Title | `-T/--title TITLE` already exists, separate from the filename stem. | A collection has a human title and a filesystem identity; both concepts already have flags. |
| Output | `-o/--output PDF` specifies the whole path and conflicts with `--name` and `--ref-type`. | A directory option is additive, not merely a spelling change. |
| Target | Exactly one `TARGET`, parsed as an `OsString`, supports Markdown, local PDF, PDF URL, arXiv, and HTML article routes. | Keep single-target routing intact and dispatch the new multiple-target route separately. |
| Lifecycle | Create installs an intake PDF; scan later moves it into the library and creates the note/reading task. | “Create one reference” must preserve that lifecycle. Do not also write a note directly from the new route. |
| Provenance | HTML capture stamps one scalar `source_url`. | A collection needs all source URLs carried through the PDF marker, scan, sync, lookup, and dedupe. |
| Lookup | Reference-library lookup already accepts scalar or list-valued `source_url` and legacy `url`. Creation dedupe and intake lookup read scalars only. | Emitting a list without updating its consumers produces a deceptively incomplete feature. |
| Rendering | A pinned Playwright/Defuddle adapter sanitizes and localizes article content, then renders a Bob-owned reader template. PDF output already enables outlines and tags. | Reuse this typography and extraction pipeline; no new rendering stack is necessary. |

Evidence: the [current CLI and parsing](https://github.com/bobs-org/bob-cli/blob/ba717105385bc15513a23f27591d0ccdfa96b36e/src/native/highlights_ref/create.rs#L237), [name validation and stem rules](https://github.com/bobs-org/bob-cli/blob/ba717105385bc15513a23f27591d0ccdfa96b36e/src/native/highlights_ref/clip_url.rs#L230), [pipeline documentation](https://github.com/bobs-org/bob-cli/blob/ba717105385bc15513a23f27591d0ccdfa96b36e/docs/highlights-create.md), [source readers](https://github.com/bobs-org/bob-cli/blob/ba717105385bc15513a23f27591d0ccdfa96b36e/src/native/highlights_ref/sources.rs#L91), and [library indexing](https://github.com/bobs-org/bob-cli/blob/ba717105385bc15513a23f27591d0ccdfa96b36e/src/native/ref_library/mod.rs#L381).

Project CLI memory additionally requires excellent help, alphabetical options, a short alias for every public long option, and permanent hidden aliases when commands are renamed. Its rename rule explicitly concerns commands; retaining existing option semantics here is my compatibility recommendation, not a claim that the memory explicitly prohibits every option change.

## Is one reference really the right abstraction?

It is right when the pages are one reading commitment: parts of one tutorial, an author's short series, or a curated packet the user intends to read together. One reading task and one annotation document reduce friction. The fact that reference notes already gather source links makes a collection a reasonable extension.

It is less suitable for an evolving research bibliography. Independent papers have different authors, dates, reading states, and annotation histories. A project note linking separate references serves those cases better. Therefore merge only on an explicit multi-URL invocation; never infer merging from a shared domain or from several quick captures. Help should say that multiple URLs produce **one collection**, not several references.

A collection is a snapshot. Adding a source later can shift every subsequent page and invalidate Highlights page references and annotation geometry. Do not turn `create` into an updater. For an already scanned collection, refuse replacement through the existing library protection; the user can create a new snapshot under a new name. A PDF retained in intake can follow the current guarded `--force` rules only when it is demonstrably the same collection.

## Proposed CLI contract

```sh
# A sufficiently specific shared topic prefix can name the collection.
bob ref create \
  https://example.org/posts/building-a-database-part-1 \
  https://example.org/posts/building-a-database-part-2 \
  -P bob

# An unrelated reading packet needs an explicit name or title.
bob ref create \
  https://one.example/essay \
  https://two.example/article \
  -N reading_packet -T 'A few essays on memory' -P bob

# Explicit title can supply the collection stem when --name is absent.
bob ref create URL1 URL2 -T 'A few essays on memory' -P bob

# Directory + stem are independent; the directory is used exactly as given.
bob ref create URL1 URL2 -N memory_packet -O ./exports -P bob

# Existing exact-path usage remains available.
bob ref create URL1 URL2 -o ./exports/memory_packet.pdf -P bob
```

Proposed usage: `bob ref create [OPTIONS] <TARGET>...`. One target follows today's behavior. Two or more targets must all be public HTTP(S) HTML-page URLs for the first release. Keep file targets as native `OsString`s: accepting URL lists must not regress non-UTF-8 local paths on the single-target route.

Use a normal variadic positional, such as Clap's `.num_args(1..)`, with `get_many`, and normal option parsing. Do not use trailing-var-arg behavior that consumes flags following the first URL. `URL1 URL2 -P bob` and `-P bob URL1 URL2` should both work. Do not split arguments on commas: commas can be URL data. The existing shell quoting expectations still apply to `&` and wildcard characters. Clap documents the distinction between multiple values and trailing arguments in its [Arg reference](https://docs.rs/clap/latest/clap/struct.Arg.html#method.num_args).

For the new directory option:

- `-O/--output-directory DIR` conflicts with exact `-o/--output PDF`.
- It combines with `--name`, `--title`, and `--ref-type`.
- Default output remains `<xlib>/<ref-type>/<stem>.pdf`. Explicit directory output is `<DIR>/<stem>.pdf`, with no hidden extra type directory.
- Expand `~` and resolve relative paths from the caller's working directory as existing exact output does. Reject an existing non-directory path. Create directories only when installation is ready.
- Reuse collision suffixing for directory-derived filenames: a different collection occupying the requested stem yields `_2`, `_3`, etc., with the existing visible rename explanation. An exact file output remains exact and never silently gains a suffix.
- Classify the actual destination through existing intake/library/external path rules. Files outside intake/library still require the appropriate existing sync workflow; directory output must not imply that scan finds arbitrary export directories.

Keep `--name` as a validated stem. For a natural-language name, `--title` is the ergonomic input. On the multi-URL route, resolve the stem in this order: `--name`; exact output filename; a valid stem derived from explicit `--title`; inferred common URL topic; otherwise an actionable usage error. Keep current exact-output conflicts rather than allowing a filename and a contradictory `--name`. For the human collection title: `--title`, then a humanized explicit/inferred stem. Do not adopt the first article's title for the whole collection.

This introduces a title-to-stem fallback for collections without changing single-target title derivation. If an explicit title produces an empty stem under the current ASCII slugger, explain that `--name` is needed. Broadening Unicode filename policy would be a separate compatibility decision, not a hidden side effect of this feature.

If Bryan strongly prefers lowercase `-o` for directories, the alternative is an intentional short-option migration: keep legacy `--output` as an exact file option and give it another short spelling. That still breaks old `-o` scripts. I do not recommend extension-based guessing, existence-based guessing, or making both long spellings aliases for different semantics.

## A common-prefix policy that is useful and explainable

### Why raw longest common prefix is wrong

`https://a-very-long-publisher.example/articles/2026/` can be long while saying nothing about the selected articles. `.../learning-rust` and `.../learning-ruby` share characters inside a word, not a collection name. Numeric IDs, tracking parameters, and dates can make a prefix appear specific. Comparing only extracted titles has different problems: metadata may change, titles often start with publisher boilerplate, and the command cannot reject a missing name until after expensive capture.

URLs also do not promise topic semantics. RFC 3986 distinguishes authority, hierarchical path segments, and query data, and leaves ordinary segment meaning to the application. The following is a Bob naming policy, not a URL-standard deduction. [RFC 3986, path syntax](https://datatracker.ietf.org/doc/html/rfc3986#section-3.3).

### Recommended deterministic algorithm

Implement one pure function returning `InferredName { stem, display_title, evidence }` or `NeedsName { reason }`. Do not use an LLM, fuzzy similarity, a shared substring, or a network request to decide whether a name is required.

1. **Validate and normalize identities first.** Reuse `validate_and_clean` for every URL. Preserve CLI order. Reject duplicate dedupe keys with both argument positions; a tracking or fragment variant is not a second article. Do not silently deduplicate a user's list.
2. **Require the same normalized authority for automatic inference.** Scheme spelling does not contribute words. Reuse established host normalization, retain meaningful subdomains, and distinguish non-default ports. Unrelated domains require explicit naming even when they happen to use similar slug words.
3. **Parse paths into real segments before decoding.** Decode valid text for naming, strip known page extensions and recognized date prefixes, and tokenize slug words on actual separators. Never allow encoded `/` or other reserved delimiters to create new hierarchy. Keep all this naming normalization separate from source identity normalization.
4. **Generate two kinds of candidates.** First, the longest common *whole-token* prefix of the final informative slug in every URL. Second, the deepest useful segment or contiguous topic phrase in their common directory path. Ignore boilerplate directory wrappers such as `blog`, `posts`, `articles`, `docs`, `guides`, `category`, locale directories, and date directories as naming material. A topic directory below them still counts.
5. **Trim only recognized incomplete endings.** Remove a trailing `part`, `chapter`, `page`, or ordinal separator left hanging at divergence, plus stranded function words such as `a` or `of`. Recognize numbering only in an explicit series position. Do not remove arbitrary numbers inside names such as `http2`, `3d`, or a meaningful version.
6. **Apply an explicit quality gate.** Reject dates, pure numbers, UUID/hash-like strings, boilerplate-only phrases, and publisher/domain-only names. A general slug prefix qualifies with at least two informative words and at least eight alphabetic characters in total, or one non-generic word with at least eight letters. A complete shared topic-directory segment, or a topic followed only by consistently recognized part/chapter numbering, may qualify with one word of at least four letters. This admits `rust` in a demonstrable Rust series without accepting a short accidental character prefix.
7. **Prefer the qualifying slug phrase, then the deepest qualifying directory topic.** Use the existing slugger and its 80-character cap, rechecking the final stem after conversion/truncation. Return the exact evidence, e.g. `common slug words: building a database` or `shared topic directory: rust`. If neither qualifies, require explicit naming.

The four/eight-character thresholds and small boilerplate list are proposed product defaults, not empirically established semantics. Keep them internal, documented, and table-tested. Avoid a public confidence slider in v1. A user should be able to predict the decision from `--help` and override it with one flag.

**Deliberate requirement adjustment:** date-separated paths may yield the same useful leaf-slug prefix even though the raw full URLs have no such literal prefix. That is a better interpretation of the desired convenience. Conversely, a technically meaningful short term may still fail the quality gate. A conservative, explainable false negative is preferable to silently naming a collection `introduction` or a publisher's hostname. Explicit naming is always permitted, even when inference succeeds.

Do not use page-title inference as a second automatic escape hatch in v1. It would make the requiredness rule dependent on network state and publisher metadata. Extracted titles belong in the PDF contents, not in a changing preflight policy.

### Proposed acceptance cases

All examples are synthetic; paths in one row share `https://example.org` unless stated otherwise. Expected outcomes describe the proposed policy, not current code.

| Inputs | Outcome | Reason |
| --- | --- | --- |
| `/posts/building-a-database-part-1`, `/posts/building-a-database-part-2` | `building_a_database` | Whole words; remove the incomplete series label. |
| `/distributed-systems/consensus`, `/distributed-systems/replication` | `distributed_systems` | Shared topic directory. |
| `/guides/rust/ownership`, `/guides/rust/borrowing` | `rust` | A complete substantive topic segment, below a generic wrapper. |
| `/posts/rust-part-1`, `/posts/rust-part-2` | `rust` | Consistent explicit series suffix provides stronger evidence. |
| `/2024/building-a-database-part-1`, `/2025/building-a-database-part-2` | `building_a_database` | Matching leaf topic, dates excluded. |
| `/posts/postgresql-indexes`, `/posts/postgresql-storage` | `postgresql` | A sufficiently long non-generic whole word. |
| `/posts/learning-rust`, `/posts/learning-ruby` | Explicit name | Only generic `learning` is shared; never invent `learning_ru`. |
| `/articles/2026/10/one`, `/articles/2026/10/two` | Explicit name | Shared path is boilerplate and a date. |
| `/introduction-to-trees`, `/introduction-to-graphs` | Explicit name | Generic lead phrase; no shared topic. |
| `/p?id=101`, `/p?id=102` | Explicit name | Arbitrary query parameters are not a naming vocabulary. |
| `/posts/12345678`, `/posts/12349999` | Explicit name | Numeric prefixes are not topics. |
| `/machine-learning`, `/machine-learning-systems` | `machine_learning` | The shorter complete slug is a valid token prefix of both. |
| `/http2-part-1`, `/http2-part-2` | `http2` | Preserve meaningful embedded digits. |
| Same useful slug prefix on different hosts | Explicit name | Not a common publisher/path context. |
| Same URL with distinct `utm_` values or `#section` fragments | Duplicate-input error | Existing URL identity cleaning makes them one source. |
| Matching non-Latin paths with no usable ASCII stem | Explicit `--name` if slug conversion is empty | Preserve readable source titles; do not generate an empty filename. |

Put `learning`, `introduction`, and similar generic lead words explicitly in the naming vocabulary used by these cases. Their rejection must not depend on an undocumented intuition in one branch of the code.

Name-required errors should happen before fetching or launching a browser and explain the actual rejected evidence:

```text
Cannot name this collection from its URLs.
Their shared path contains only “articles / 2026 / 10”.
Pass --name <stem> or --title <title>.
```

Successful inference should be visible in normal output and the dry run, with no confirmation prompt:

```text
Collection: building_a_database  ·  2 sources
Name from common slug words: “building a database”
```

## Build one document from captured articles

### Preferred approach: extract separately, compose once

Separate the current adapter's capture/extraction phase from final printing. Each article becomes a typed, ordered document record containing requested/final URL, title, author, publication date, sanitized body, localized assets, fidelity, and warnings. Compose those records into one offline HTML document and print it once with the existing reader template, then stamp exactly one Highlights marker on page 1.

The current Python adapter already constructs an `article` dictionary immediately before rendering; that is a useful extraction seam. Defuddle's documented output provides article HTML and bibliographic metadata, so the necessary representation is aligned with the current tool rather than a new scraping layer. [Defuddle documentation](https://defuddle.md/docs), [current extraction/render seam](https://github.com/bobs-org/bob-cli/blob/ba717105385bc15513a23f27591d0ccdfa96b36e/scripts/web_clip/web_clip_adapter.py#L1499).

I would keep Rust responsible for arguments, naming, dedupe, destination planning, and installation. Extend the versioned adapter protocol with a distinct collection operation and an ordered result shape; retain today's v1 single-capture contract for existing callers and test adapters. The new operation can orchestrate extraction records internally and return one final staged PDF plus per-source metadata. Refactor shared extraction so the ordinary single-page route uses the same core. Do not invoke public `bob ref create` recursively: that would install intermediate PDFs, trigger duplicate checks at the wrong level, and mix terminal output with protocol data.

A single print naturally produces continuous page numbers, one title/author dictionary, one outline tree, and one accessibility structure. Playwright supports print CSS, CSS page sizing, embedded outlines, and tagged PDF output; Bob already enables the relevant switches. These features provide the mechanism, not a guarantee of a good outline or accessible reading order: verify the generated artifact. [Playwright PDF documentation](https://playwright.dev/python/docs/api/class-page#page-pdf), [current renderer](https://github.com/bobs-org/bob-cli/blob/ba717105385bc15513a23f27591d0ccdfa96b36e/scripts/web_clip/web_clip_render.py#L393).

### Why not concatenate independently finished PDFs?

It is a tempting small patch, but it joins page trees without automatically designing a new document. Per-part page counters restart, title/author metadata conflicts, bookmarks and tagged structures need deliberate handling, and each stamped input might contain a competing marker. qpdf's documentation explicitly says document-level information is taken from the primary input and describes limitations for outlines and tags. That makes naive concatenation a poor default for this HTML-only feature. [qpdf page-selection behavior and limitations](https://qpdf.readthedocs.io/en/stable/cli.html#page-selection).

A careful PDF merger is appropriate for future arbitrary PDF inputs, where preserving original pagination and graphics matters. It is a different engineering problem. Do not add a PDF merge dependency to solve composition that the current HTML renderer can already perform.

### The document should feel intentionally edited

Use the existing Source Serif 4 / Inter / JetBrains Mono print template, its restrained blue accents, bundled fonts, code wrapping, figure handling, and margins. The collection-specific additions should be small:

- A compact opening page containing the collection title, “N articles”, capture date, and a linked numbered contents list with each source's title and host. This doubles as front matter; do not add a separate decorative cover.
- A fresh page for each article, using `break-before: page`, not a right-hand-page rule that inserts blank leaves. Preserve each article's title, author/date if known, source link, and then its content. CSS explicitly supports forced page breaks between blocks. [W3C CSS Fragmentation](https://www.w3.org/TR/css-break-3/#break-between).
- A real outline hierarchy: collection, articles, then article sections. Shift body headings relative to their article, avoiding duplicate lead titles. Start with structural HTML and verify the PDF outline rather than assuming heading CSS controls bookmarks.
- Continuous `page / total` counters and a collection-title footer. Per-article running headers can wait; do not depend on unverified CSS running-string support.
- Keep long provenance URLs clickable and wrap them safely. Do not make the opening contents a wall of query strings. A small source list at the end can retain full links if space is needed.

Namespace every imported HTML `id` by source position and rewrite matching local fragment links, including SVG fragment references where applicable. Two pages often both contain `#introduction` or `#fn1`. Resolve each page's relative links against its own validated final URL before combining them. Retain ordinary cross-page hyperlinks as external links in v1; do not add a graph-rewriting feature.

Similarly, isolate source assets. The current localizer can emit names such as `svg-001.svg`, so blindly copying all scratch directories into one `assets/` directory loses images. Rewrite to a flat source-prefixed or content-addressed asset namespace compatible with the offline resource allowlist. Preserve sanitization, restricted rendering origins, private-network checks, and per-source browser cleanup; composition must not reopen live website resources during printing.

## Provenance and identity are part of the feature

### Persist all source URLs in the existing marker model

Use scalar `source_url` for existing single-source documents and an ordered list for collections:

```text
- status: ready
- parent: bob
- title: Building a database
- id: building_a_database
- source_url: ["https://example.org/part-1", "https://example.org/part-2"]
- captured: 2026-10-15
```

This reuses `MarkerValue::List`, which the marker renderer and frontmatter snapshot already support. Keep `id` as the filename-derived reference identity; do not repurpose it into a hash. No second note or per-source reading task is created. [Marker value types](https://github.com/bobs-org/bob-cli/blob/ba717105385bc15513a23f27591d0ccdfa96b36e/src/native/highlights_ref/model.rs#L39), [marker composition](https://github.com/bobs-org/bob-cli/blob/ba717105385bc15513a23f27591d0ccdfa96b36e/src/native/highlights_ref/stamp.rs#L579).

Update **every relevant reader**, not only library `find`: creation dedupe from notes, dedupe from queued intake PDFs, intake records used by `find -i`, destination ownership checks, and automatic routing shared with capture/jobs. Preserve order in the document representation; lookup may index its flattened URLs.

For validated redirects, retain requested and final URLs as per-source aliases. A practical extension within today's scalar/list marker model is an optional ordered `resolved_source_url` list aligned with `source_url`, written only when at least one final URL differs. Shared source-reading code should understand these aligned pairs, index both spellings, and validate equal lengths. Never flatten those aliases into extra “articles”. A failed redirect validation still aborts the capture; publisher-provided canonical tags alone must not replace source identity.

For the aggregate author and publication fields, use an explicit collection override if supplied; otherwise retain a common value only when all articles agree and omit it when they differ. Every article keeps its own attribution in its masthead. Collection `--title`, `--author`, and `--published` must not be passed as overrides that overwrite every article's extracted metadata. The first article's author or date is not automatically the collection's author/date. `captured` belongs to the assembled snapshot.

Per-article bibliographic details can remain visible in the PDF and typed adapter response in v1. A structured frontmatter array of objects would require a deliberate extension of the current marker model, which supports scalar/list values rather than mapping objects. It is unnecessary for the requested feature.

### Distinguish overlap from an identical collection

Existing dedupe treats a shared URL as the same reference. Applying that unchanged means an already captured Part 1 prevents creating Parts 1–3. That is unhelpful for an explicit collection operation.

Recommended behavior:

| Situation | Proposed result |
| --- | --- |
| Same normalized URL appears twice in one invocation | Refuse before capture and identify both positions. |
| Two inputs redirect to the same final source | Refuse after resolution, before publication; report both inputs. |
| Existing collection has the same ordered source identities | Existing “already captured/queued” handling; never create another copy just because the requested name changed. |
| A selected source also exists as a standalone reference | Show the overlap and create the explicitly requested collection; do not delete, hide, or rewrite the standalone reference. |
| Existing collection shares only some sources | Show the overlap and create the new snapshot. |
| Same sources requested in a different order | A distinct ordered collection; order is user intent. |
| Automatic quick capture later sees a source already in a collection | Treat it as known and point to the containing reference, as source lookup does today; do not silently queue another copy. |

Use normalized ordered source sequences for collection identity. Compare requested aliases before network work where possible, then recheck final identities after redirects. A persistent digest is optional; comparing vectors is sufficient for the initial implementation. Keep source membership keys separate from “this is the identical document” checks. The existing `DefaultTargetIdentity::Url` tests whether **any** key overlaps, so giving it a vector of collection URLs without changing its semantics is incorrect. [Destination identity implementation](https://github.com/bobs-org/bob-cli/blob/ba717105385bc15513a23f27591d0ccdfa96b36e/src/native/highlights_ref/stamp.rs#L294).

Also update library supersession. Today two PDF-backed references sharing a URL earn `duplicate_identity`, and a PDF-less note can be hidden as superseded by any PDF-backed note sharing one key. Expected collection membership should not create duplicate warnings or hide an independently meaningful legacy reference. Preserve the established single-source migration behavior; restrict collection supersession/duplicate decisions to actual document equivalence, not one member overlap. This is a required integration change, not cosmetic cleanup. [Current supersession logic](https://github.com/bobs-org/bob-cli/blob/ba717105385bc15513a23f27591d0ccdfa96b36e/src/native/ref_library/mod.rs#L721).

## Reliability and a disciplined first release

Validate parent, all URL syntax, explicit names/dates, unsupported option combinations, and destination shape before starting expensive work. Infer or require a name at that point. Sequentially extract sources with the existing browser fallback/fidelity policy, using isolated per-source scratch areas. Start sequentially; a few parallel browsers are not worth making ordering, challenge retries, memory, and timeouts harder to reason about in v1.

Finish extraction, asset localization, composition, PDF validation, and marker construction in scratch. If any member fails, fail the collection and publish no final PDF. An image loss that is already a fidelity warning may remain a clearly reported warning; do not silently promote it to a successful perfect capture, and do not silently omit an article. Recheck final source identity and destination ownership at publication. Use a guarded no-clobber installation for ordinary writes and the existing narrow `--force` rules; a prior existence check followed by an overwriting rename is not a complete concurrency guarantee.

Preserve the current aggregate PDF size policy: warn around 50 MiB and refuse at the vault's 95 MiB limit. Check the combined output, not just each source. Count resource budgets at collection scope as well: reusing a per-page 60 MiB image budget across an unbounded list multiplies peak storage. Use per-source capture deadlines plus a separate bounded render deadline. Do not run N sources under the current single-adapter 300-second deadline unchanged. No network operation may wait indefinitely.

An ordinary failure message should identify the source position, URL, and stage, and state whether publication happened. Treat disk errors after a final rename honestly; “no writes” is only a promise for failures before publication, not a claim that multi-file filesystem transactions exist. Initially no reusable cross-run capture cache is necessary. Prefer correct rollback and clean scratch over a new resume database.

For `--dry-run`, retain today's documented meaning: HTML URLs can be fetched and extracted; final PDF/audio installation is skipped, and image localization/PDF rendering remain skipped. Report the inferred name and evidence, ordered sources, destination, overlap decisions, and planned marker. It cannot promise a final page count, size, or visual fidelity. A missing explicit name should still fail before browser/network work. [Current dry-run contract](https://github.com/bobs-org/bob-cli/blob/ba717105385bc15513a23f27591d0ccdfa96b36e/docs/highlights-create.md#L113).

First-release scope should be explicit:

| Capability | Recommendation |
| --- | --- |
| Multiple HTML article/page URLs | Support, in argument order, using existing extraction/fidelity acceptance. Do not promise arbitrary dashboards or every page layout. |
| Single Markdown/PDF/arXiv/URL | Preserve current behavior. |
| Multiple local files or PDF/arXiv URLs | Reject clearly; PDF preservation/merging is a later design. Detect obvious cases early and late PDF redirects before publication. |
| `--html FILE` with multiple URLs | Reject before capture: one saved file cannot unambiguously map to several URLs. A manifest could solve this later. |
| `--listen` with multiple URLs | Reject before capture in v1. The current narration contract has one `{target}`; silently narrating just the first URL is unacceptable. Later narrate the complete staged collection through a verified PDF/text input contract. |
| `--audio PATH` | May bind one explicitly supplied companion to the whole collection through the existing guarded install flow; never attach it to each article. |
| `--no-audio` | Retain its existing spelling and behavior. |
| Appending, scraping pagination, sorting series parts, following links | Exclude. The user supplies the complete ordered source list. |

The narration and HTML-replay restrictions are scope adjustments, not technical impossibilities. State them in help rather than shipping options that appear to work but apply to one arbitrary member.

## A small, polished terminal flow

Use the current styling and TTY detection. A stable per-source counter, useful title, and a final artifact path communicate more than animation. Collapse successful per-source details where appropriate, retain explicit warnings, and emit readable plain text without terminal control sequences when redirected.

```text
Collection  Building a database · 3 articles
Name        building_a_database · common URL topic

  1/3  Storage basics                         example.org
  2/3  Indexes and queries                     example.org
  3/3  Transactions                           example.org

Created xlib/blogs/building_a_database.pdf
3 articles · 42 pages
Next: bob ref scan
```

Do not display a note path as already created. When a source is blocked, preserve the existing actionable browser-saved-page guidance, while explaining that multi-source `--html` replay is not yet supported. No confirmation is needed for a valid capture. Explicit user naming always wins over inference.

## Implementation boundaries and validation

This is more than making one positional variadic, but it does not require rebuilding the reference system. A practical implementation sequence is:

1. Introduce a shared typed source representation for scalar/list URL metadata, aligned redirect aliases, ordered document equivalence, and lookup membership. Update intake, create, routing, and library supersession readers together, with regression tests for old notes and markers.
2. Add the pure collection-name policy and variadic CLI dispatch. Add the directory option through the existing path-planning/workflow classification, preserving old flag meanings and aliases.
3. Split extraction from rendering in the adapter, add a versioned collection operation, and build one offline reader document. Keep a single extraction implementation shared with the existing route.
4. Integrate one-marker stamping and guarded installation. Add user-facing output, help, examples, completion metadata, and explicit unsupported-combination errors.

Important files are `src/native/highlights_ref/{create,clip,clip_url,clip_adapter,sources,stamp,marker,model}.rs`, `src/native/ref_library/{mod,identity,find}.rs`, `scripts/web_clip/{web_clip_adapter,web_clip_render}.py`, and `scripts/web_clip/template/reader.css`. Completion currently has a path-specific `output -> *.pdf` rule: preserve that and add directory completion for the new option. Test both canonical `ref create` and existing hidden aliases. Update `docs/highlights-create.md`, `docs/highlights-clip.md`, and the identity/dedupe explanation in `docs/ref.md`.

Tests should prove user outcomes rather than duplicate helper implementations:

- Table-test every naming case above, permutations of the same input set, explicit-name precedence, percent escapes, URL queries, Unicode-to-empty stems, and three or more sources. Naming must use all sources; a useful prefix shared by only the first two is insufficient.
- CLI regression cases for `-N`, `-n`, `-o`, `-O`, option placement after URLs, exact file/directory conflicts, single-target routing, and short/long help and completion.
- Deterministic offline adapter fixtures covering two articles with duplicate anchors and filenames, differing authors/dates, relative links, SVG references, long code, tables, image failure, redirected duplicate sources, and blocked middle articles.
- An end-to-end collection capture → `find -i` for **each** URL → scan → library `find` for **each** URL → sync round trip. Assert ordered source preservation, one PDF, one marker, one note, and one reading task.
- Identity cases for an existing part, partial overlap, an identical ordered collection, reordered inputs, expected overlap without `duplicate_identity`, and legacy supersession that remains correct for genuine single-source replacements.
- Failure at extraction, render, size validation, and publication, with no partial collection or replacement of annotated library bytes. Include a destination race and guarded `--force` behavior.
- Inspect the actual PDF: clickable contents, correct outline destinations after stamping, continuous page counters, selectable text, complete article bodies, no blank separator leaves, and correct tag/reading order. Use a short-document fixture and a long-document fixture; visual snapshots alone do not prove source completeness.

For implementation verification, `just check` is the repository's Rust gate; `just check-web-clip-adapter` separately covers the pinned Python adapter and its offline/browser fixtures. The latter can skip browser-backed checks when no browser is discovered, so a green exit without fixture execution is not visual PDF validation. These commands were inspected as verification guidance; they were not run for this report because no implementation changed.

## Recommended solution

Implement **ordered multi-URL HTML collections in `bob ref create`**, preserving the existing create → scan lifecycle. Reuse `-N/--name`, keep `-n/--no-audio` and exact-path `-o/--output`, and add `-O/--output-directory`. Accept an explicit title or output filename as sufficient naming intent; otherwise infer a name only from a documented, conservative common URL-topic prefix, failing before capture when it does not qualify.

Extract every selected page with the existing safeguards, compose one carefully typeset reader document with linked contents and article-level attribution, render once, and stamp once. Persist every source, distinguish collection identity from source overlap, and update dedupe, intake lookup, and supersession together. Publish only a complete collection. Keep arbitrary PDF merging, saved-page manifests, append/update operations, and collection narration outside the first release.

This is a worthwhile feature when treated as a durable reading document with a small, explicit contract. Its quality will depend less on clever title guessing than on trustworthy provenance, stable ordering, navigable typography, and preserving the user's existing library.
