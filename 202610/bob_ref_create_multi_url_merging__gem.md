# Research & Design: Multi-URL Web Article Merging for `bob ref create`

**Researcher**: `research.4i.gem`  
**Date**: October 2026  
**Status**: Completed Research & Proposal  
**Artifact Target**: `research:202610/bob_ref_create_multi_url_merging__gem.md`  

---

## 1. Executive Summary

This report evaluates and designs the proposal to extend `bob ref create` to accept multiple URLs simultaneously, merging two or more web articles/pages into a single unified reference note and Highlights-ready PDF.

### Key Conclusions & Critiques

1. **The Multi-URL Merging Concept is Sound and High-Value**:
   Multi-part blog series, tutorials, and multi-chapter web documentation currently fragment reading workflows in Bob. Capturing them as separate reference notes creates separate reading tasks, fragments the morning GTD review walk, and scatters Highlights annotations across multiple PDFs. Consolidating them into a single, structured reference document directly serves the core reading workflow.
2. **Critique of `-n|--name` (Flag Collision)**:
   The proposal suggests adding `-n|--name` to set the reference note name. In `bob ref create`, `--name` **already exists** with the short flag `-N`. Furthermore, the lowercase flag `-n` is **already occupied by `--no-audio`** (a boolean flag that skips companion audio discovery). Reassigning `-n` from a flag to an option taking a value would be a breaking change, disrupting user muscle memory and existing automation. The canonical flag should remain `-N, --name`.
3. **Critique of Changing `-o|--output` to `-o|--output-directory`**:
   `-o, --output <PDF>` currently specifies an exact, complete file path for the generated PDF. Renaming or redefining `-o|--output` as a directory breaks existing scripts, documentation, and regression tests. Instead, we should introduce a dedicated `-O, --output-dir <DIR>` (or `--output-directory <DIR>`) option that composes cleanly with `-N, --name <STEM>`, while preserving `-o, --output <PDF>` for exact-path overrides.
4. **The Common URL Prefix Heuristic Must Be Semantic, Not String-Based**:
   Requiring `-N|--name` *iff* URLs share no "long enough and useful" common prefix is an elegant UX contract—**provided** the common prefix analysis is semantic and path-aware. A naive character-by-character Longest Common Prefix (LCP) cuts mid-word (e.g., `https://example.com/ca` from `cats` and `cars`), matches generic protocols and hosts (`https://en.wikipedia.org/wiki/`), or captures scaffolding segments like `/posts/` and `/blog/` that lead to namespace collisions. A robust prefix algorithm must tokenize paths, enforce host identity, evaluate meaningful directory slugs against Bob's existing `SKIPPED_SEGMENTS` filter, and check word-boundary prefixes on diverging slugs before concluding whether a name is required. Crucially, this check must run *synchronously at CLI startup* to fail fast in sub-milliseconds rather than waiting for headless browser extraction.
5. **The Generation Strategy Must Assemble HTML at the Adapter Layer, Not Stitch PDFs**:
   To fulfill the mandate that the feature be *beautiful*, articles must be merged within Bob's Playwright/Defuddle web-clip adapter into a unified reader HTML document with an overall title, table of contents, chapter/part dividers, normalized heading hierarchies, namespaced anchor IDs, and continuous pagination. Post-hoc PDF stitching produces an ugly, fragmented document with restarting page numbers and duplicate mastheads.

---

## 2. Analysis of the Existing `bob ref create` Architecture

To ground the design, we analyze how `bob ref create` currently handles ingestion, metadata extraction, staging, and sync.

```
┌───────────────────────────────────────────────────────────────────────────────────┐
│                                 bob ref create                                    │
│                                                                                   │
│  1. Parse CLI Args (TARGET, -P parent, -N name, -A author, -p published, etc.)   │
│  2. Syntactic URL classification & Early Dedupe Check (sources.rs)                │
│  3. Web Clip Adapter (scripts/web_clip/web_clip_adapter.py via uv)                │
│     ├─ Headless Chrome (Playwright) extracts DOM snapshot                         │
│     ├─ Defuddle extracts reader content & metadata (title, author, published)     │
│     ├─ Pillow normalizes images                                                   │
│     └─ web_clip_render.py prints reader PDF                                       │
│  4. Target Planning (pdf_target.rs / stamp.rs):                                   │
│     └─ xlib/<ref_type>/<stem>.pdf (with collision handling: stem_2, stem_3)       │
│  5. Marker Stamping: Embed page-1 JSON metadata (title, source_url, parent, id)   │
│  6. Companion Audio: Bind --listen or --audio companion file                      │
└────────────────────────────────────────┬──────────────────────────────────────────┘
                                         │
                                         ▼
┌───────────────────────────────────────────────────────────────────────────────────┐
│                                  bob ref scan                                     │
│                                                                                   │
│  1. Moves PDF: xlib/<ref_type>/<stem>.pdf ──► lib/<ref_type>/<stem>.pdf           │
│  2. Writes Reference Note: <vault>/Highlights/<ref_type>/<stem>.md                │
│  3. Frontmatter derived from page-1 marker (source_url, ref_type, parent, etc.)   │
│  4. Injects reading task in parent note / reference note: - [ ] #ref #pdf ...     │
└───────────────────────────────────────────────────────────────────────────────────┘
```

### 2.1 Positional Targets and Argument Parsing

In `src/native/highlights_ref/create.rs`, the positional argument `target` is declared as:
```rust
Arg::new("target")
    .value_name("TARGET")
    .required(true)
    .value_parser(clap::builder::OsStringValueParser::new())
    .help("Markdown file, PDF file, PDF URL, arXiv paper URL, or web article URL")
```
It accepts exactly one target. Multiple targets currently cause Clap to emit `error: unexpected argument '<TARGET_2>' found`.

### 2.2 Existing Stem Derivation (`clip_url.rs`)

For single URLs, `bob ref create` derives a default filename stem from the URL path via `stem_from_url`:
- It parses URL path segments from right to left (most specific to least specific).
- It strips known file extensions (`.html`, `.htm`, `.php`, `.pdf`, etc.).
- It filters out segments that are:
  - Empty or `<= 2` characters;
  - Pure numeric or date strings (`YYYY-MM-DD`, `YYYYMMDD`);
  - In `SKIPPED_SEGMENTS`: `["index", "default", "home", "post", "posts", "p", "article", "articles", "blog", "amp", "en", "en-us"]`.
- If a segment passes, it converts it to snake_case (`snake_case(&candidate)`).
- If no segment passes, it falls back to adapter title extraction (`extracted_title`), and finally to `host_YYYYMMDD`.

### 2.3 Reference Library & Identity Support for Multiple URLs

A key architectural finding in `bob-cli` is that `src/native/ref_library/mod.rs` and `src/native/ref_library/identity.rs` **already anticipate multiple `source_url` values** on reference notes:
```rust
let mut urls = front.get_all("source_url");
urls.extend(front.get_all("url"));
let stored = stored_identity(&urls);
```
`stored_identity` accepts a slice of URLs and indexes dedupe keys for all of them. However, intake tracking (`sources.rs`) and marker stamping (`stamp.rs`, `model.rs`) currently assume a scalar string `source_url`. Extending the ingestion pipeline to emit list-based `source_url` values fits naturally into Bob's data model.

---

## 3. Critique of the Proposed Plan

We evaluate the user prompt's specific proposals, identify potential issues, and formulate justified adjustments.

### 3.1 Critique: Adding a New `-n|--name` Option

The prompt states:
> *"To support this change, we should add a new `-n|--name` option to the `bob ref create` command that allows the user to specify the name of reference note."*

#### Finding
1. **`--name` Already Exists**:
   `bob ref create` already implements `--name` (`src/native/highlights_ref/create.rs:300-305`):
   ```rust
   Arg::new("name")
       .long("name")
       .short('N')
       .value_name("STEM")
       .help("Output filename stem [default: derived from TARGET]")
   ```
   Specifying `--name` already defines the filename stem in `xlib/<ref_type>/<stem>.pdf`, which `bob ref scan` directly uses to name the reference note: `<ref_dir>/<ref_type>/<stem>.md`.
2. **Short Flag `-n` is Already Allocated to `--no-audio`**:
   `src/native/highlights_ref/create.rs:307-313`:
   ```rust
   Arg::new("no-audio")
       .long("no-audio")
       .short('n')
       .action(ArgAction::SetTrue)
       .conflicts_with("audio")
       .help("Skip companion audio discovery and copy")
   ```
   `-n` is a boolean flag.

#### Critique & Impact
- If `-n` is reassigned to `--name`, any command or script that currently passes `-n` (to suppress audio discovery) will break: Clap will either complain that `-n` requires a value or will consume the next positional argument (the target URL) as the stem name!
- In `sase/memory/cli_rules.md`, Bob commands must maintain strict stability and avoid breaking flag renames.
- Standard CLI convention in GNU/Unix tools frequently reserves uppercase `-N` when lowercase `-n` represents a flag or number. Bob has already adopted `-N` across documentation and tests.

#### Recommended Adjustment
- **Retain `-N, --name` as the Canonical Option**: Do not break `-n, --no-audio`.
- Keep `--name` as the long flag. If Bryan insists on lowercase `-n` for `--name`, `--no-audio` must be migrated (e.g., to `--no-audio` without a short flag or `-X`), but our strong recommendation is to preserve `-N, --name` to maintain 100% backward compatibility and consistency across all help text.

---

### 3.2 Critique: Changing `-o|--output` to `-o|--output-directory`

The prompt states:
> *"We should also change the `-o|--output` option to `-o|--output-directory` so these two options can be used together."*

#### Finding
Currently, `-o, --output` takes a complete file path including the `.pdf` extension:
```rust
Arg::new("output")
    .long("output")
    .short('o')
    .value_name("PDF")
    .conflicts_with("ref-type")
    .conflicts_with("name")
    .help("Complete path for the generated PDF, including the .pdf filename")
```
It conflicts with `--name` and `--ref-type` because specifying the full file path (`/tmp/my_paper.pdf`) inherently specifies both the destination directory and the filename stem.

#### Critique & Impact
- **Breaking Change**: Hard-renaming `--output` to `--output-directory` or changing its semantics from file path to directory path violates the CLI rule: *"Never hard-rename or remove a command: the old spelling becomes a permanent hidden alias with byte-identical behavior..."*.
- Many existing tests (`tests/cli/highlights/create.rs`) and external scripts rely on `bob ref create <target> -o <path.pdf>` to output to an explicit PDF file (e.g., outside the intake tree).
- If `-o` expects a directory, running `bob ref create <target> -o /tmp/custom.pdf` would create a *directory* named `/tmp/custom.pdf/` and place `/tmp/custom.pdf/<name>.pdf` inside it.

#### Recommended Adjustment
- **Introduce `-O, --output-dir <DIR>` (or `--output-directory`)**:
  - Add `-O, --output-dir <DIR>` specifically for directory targeting.
  - When `-O, --output-dir` is provided, it **composes seamlessly** with `-N, --name`:
    `bob ref create <URL1> <URL2> -O /custom/dir -N my_series` -> `/custom/dir/my_series.pdf`.
  - Retain `-o, --output <PDF>` as the full-path option (conflicting with `-N, --name` and `-t, --ref-type`).
  - Alternatively, make `--output` polymorphic: if the path ends in `.pdf`, treat as full file path; if it exists as a directory or ends in `/`, treat as output directory. However, having distinct options (`-o, --output <PDF>` vs `-O, --output-dir <DIR>`) is much clearer, safer, and self-documenting.

---

### 3.3 Critique: Multi-Target Scope and Mixed Types

The prompt specifies accepting multiple URLs for web articles. But what happens if a user passes:
- Multiple local Markdown files?
- Multiple PDF files?
- A mix of a web URL and a local PDF?

#### Recommendation
1. **Initial Scope**: Explicitly restrict multi-target ingestion to **web articles** (HTTP/HTTPS URLs).
2. **Fail Fast on Mixed Types**: If the user passes multiple targets and they are not all web URLs (e.g., mixing a URL with a local `.md` or `.pdf`), emit an immediate, clear error:
   ```
   bob ref create: error: multi-target capture only supports web article URLs; received mixed targets
   ```
3. **Future Extension**: Merging multiple Markdown files via Pandoc can be added in a follow-up phase using Pandoc's native multi-file inputs, but should not complicate the initial web-clip merge release.

---

## 4. Deep Design: The Common URL Prefix Heuristic

The prompt specifies:
> *"When multiple URLs are provided, we should require the `-n|--name` option iff there is no way for us to use some (long enough and useful) common prefix that all of the URLs share. Think hard about the best way to meet this requirement."*

### 4.1 Pitfalls of Naive String Longest Common Prefix (LCP)

Consider naive character-by-character LCP across raw URL strings:

| Example URLs | Naive Raw String LCP | Resulting Stem | Assessment |
| :--- | :--- | :--- | :--- |
| `https://a.com/cars`<br>`https://a.com/cats` | `https://a.com/ca` | `ca` | **Terrible**: Cuts mid-word; `ca` is meaningless. |
| `https://nytimes.com/art1`<br>`https://wsj.com/art2` | `https://` | `https` | **Terrible**: Only scheme matches. |
| `https://en.wikipedia.org/wiki/Apple`<br>`https://en.wikipedia.org/wiki/Banana` | `https://en.wikipedia.org/wiki/` | `wiki` | **Terrible**: Generic host/scaffolding; causes collisons for all Wikipedia merges. |
| `https://blog.com/posts/2026/01/p1`<br>`https://blog.com/posts/2026/01/p2` | `https://blog.com/posts/2026/01/p` | `posts_2026_01_p` | **Ugly**: Scaffolding segments and partial tokens. |

### 4.2 Semantic Multi-URL Prefix Algorithm

To be reliable and beautiful, the algorithm must operate on **parsed URL components and token boundaries**, reusing and extending Bob's established `clip_url` rules.

```
                           URLs: [WebUrl, ...]
                                    │
                                    ▼
                         All hosts identical?
                           (lowercased, no www.)
                                   / \
                             No   /   \   Yes
                                 ▼     ▼
                          Return None  Extract decoded path segments
                          (--name req) (strip page extensions .html, .php)
                                       │
                                       ▼
                       Find Longest Common Directory Prefix
                          (matching path segments)
                                       │
                        Reverse scan common segments:
                      Does segment pass stem_from_segment?
                     (not in SKIPPED_SEGMENTS, not date, >2 chars)
                                      / \
                                Yes  /   \  No
                                    ▼     ▼
                           Return Stem   Are diverging segments the
                          (e.g. series)  final slugs of each URL?
                                                / \
                                          Yes  /   \  No
                                              ▼     ▼
                                    Compute Token-Boundary  Return None
                                    Prefix of Slugs         (--name req)
                                    (e.g. raft-part-1 & 2 -> raft)
                                              │
                                   Passes length (>=4) and
                                    stem_from_segment?
                                            / \
                                      Yes  /   \  No
                                          ▼     ▼
                                    Return Stem Return None
```

#### Detailed Algorithmic Steps

1. **Host Verification**:
   - Normalize each URL host (lowercase, remove `www.`).
   - If any URL has a different host, **return `None`** (immediately requires `--name`). Merging articles across different websites cannot have a coherent URL-derived series name.
2. **Segment Tokenization & Page Extension Stripping**:
   - Parse each URL path into segments `[s_0, s_1, ..., s_k]`.
   - Percent-decode segments.
   - For the terminal segment, strip known extensions (`.html`, `.htm`, `.php`, `.shtml`, `.pdf`).
3. **Directory-Level Common Segment Analysis**:
   - Find the common path segments across all URLs: `common_segments = [c_0, ..., c_m]`.
   - Scan `common_segments` in **reverse order** (from deepest directory to root):
     - Check each segment against Bob's `stem_from_segment(seg)`:
       - Reject if in `SKIPPED_SEGMENTS` (`blog`, `posts`, `p`, `articles`, `docs`, `en`, `wiki`, `index`, `default`, etc.).
       - Reject if it is a pure date (`2026`, `2026-10-15`, `10`).
       - Reject if length `<= 2`.
     - If a segment passes and `snake_case(seg).len() >= 4`, **return `Some(snake_case(seg))`**.
     - *Example*:
       - `https://martinfowler.com/articles/patterns-of-distributed-systems/heartbeat.html`
       - `https://martinfowler.com/articles/patterns-of-distributed-systems/generation.html`
       - `common_segments` = `["articles", "patterns-of-distributed-systems"]`.
       - `patterns-of-distributed-systems` is valid and not skipped -> returns `patterns_of_distributed_systems`.
4. **Terminal Slug Token-Boundary Prefix Analysis**:
   - If directory segments yield no useful stem (e.g. common directory is only `/p/` or `/posts/`), check the diverging segments if they represent the final content slugs.
   - Strip leading date prefixes (`strip_date_prefix`) from each slug.
   - Compute character-level LCP across the slugs.
   - **Enforce Token Boundary**:
     - Do not accept partial words! The LCP must break on a delimiter (`-`, `_`, or `.`).
     - *Example*: `raft-part-1` vs `raft-part-2` -> LCP is `raft-part-`.
     - *Counter-example*: `cats` vs `cars` -> LCP is `ca` (no delimiter) -> rejected.
   - **Strip Trailing Series Scaffolding**:
     - Remove trailing delimiters (`-`, `_`).
     - Strip trailing series markers from the prefix: `-part`, `-pt`, `-chapter`, `-ch`, `-vol`, `-volume`, `-section`, `-series`, `-v`.
     - *Example*: `raft-part-` -> `raft-part` -> `raft`.
     - *Example*: `reflections-on-tooling-1` and `-2` -> `reflections-on-tooling`.
5. **Length and Utility Validation**:
   - The final candidate must satisfy:
     - `candidate.len() >= 4` characters;
     - Must contain at least 3 ASCII alphanumeric characters;
     - Must pass `stem_from_segment(&candidate)` (not in `SKIPPED_SEGMENTS`);
     - Must not be a pure number.
   - If it satisfies all checks, **return `Some(snake_case(&candidate))`**.
   - Otherwise, **return `None`** (requiring `--name`).

### 4.3 Fail-Fast CLI Validation

When multiple URLs are provided and `--name` is omitted:
1. Bob executes `common_url_stem(&urls)` immediately after argument parsing.
2. If `common_url_stem` returns `None`, Bob exits immediately (exit code 2) with a helpful error:
   ```
   bob ref create: error: multiple URLs share no common path stem; --name is required
   hint: pass -N <name>, for example `-N distributed_systems`
   ```
3. If `common_url_stem` returns `Some(stem)`, Bob prints:
   ```
   derived name: distributed_systems (from common URL prefix)
   ```
   and proceeds.

This ensures zero wasted compute: no headless browser launches, no network fetches, and no partial scratch state if the name cannot be inferred.

---

## 5. Designing a "Beautiful" Multi-Page Document

The user requested:
> *"Make sure you design this feature so it is intuitive, reliable, and (last but not least) beautiful!"*

### 5.1 Architecture: Adapter-Level Assembly vs. PDF Post-Stitching

| Criterion | Adapter-Level HTML Assembly (Recommended) | Post-Hoc PDF Stitching (Rejected) |
| :--- | :--- | :--- |
| **Visual Unity** | Single cohesive typography, master cover masthead, uniform margins and fonts. | Disjointed: each article has its own huge title masthead on page 1. |
| **Table of Contents** | Interactive TOC with internal clickable anchor links jumping directly to parts. | Requires external PDF outline manipulation; links often break. |
| **Page Numbering** | Continuous Arabic numbering (e.g., "Page 1 of 24") across the whole series. | Fragmented: restarts at "Page 1" for every merged article unless re-rendered. |
| **Running Headers & Footers** | CSS `@page` accurately shows document title on even pages and current part on odd pages. | Each PDF has fixed baked-in headers/footers that clash. |
| **Resource Efficiency** | Single Chromium print run, images deduplicated across parts. | Multiple browser instances, multiple PDF renders, separate stitch step. |

**Verdict**: The Python web-clip adapter (`web_clip_adapter.py` and `web_clip_render.py`) must handle the multi-article assembly natively.

### 5.2 Document Layout and Typographic Hierarchy

To make the resulting PDF gorgeous in Highlights and desktop viewers, we define the following layout structure:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        COVER / MASTER MASTHEAD                         │
│                                                                        │
│   Raft Consensus Algorithm: Complete Guide                             │
│   By Diego Ongaro, John Ousterhout · October 2026 · 14,200 words       │
│   Sources: 3 articles from raft.github.io                              │
│                                                                        │
│   ──────────────────────────────────────────────────────────────────   │
│   TABLE OF CONTENTS                                                    │
│   • Part 1: Introduction and Core Replicated State Machines ...... p. 1│
│   • Part 2: Leader Election and Safety Guarantees ................ p. 8│
│   • Part 3: Cluster Membership Changes and Log Compaction ........ p.16│
│   ──────────────────────────────────────────────────────────────────   │
└────────────────────────────────────────────────────────────────────────┘
                                 │
                         (Page Break: Always)
                                 │
┌────────────────────────────────────────────────────────────────────────┐
│                        PART 1: CHAPTER HEADER                          │
│                                                                        │
│   Part 1                                                               │
│   Introduction and Core Replicated State Machines                      │
│   Published 2014-05-20 · https://raft.github.io/part1.html             │
│                                                                        │
│   Body text starts here with elegant drop cap, shifted headings        │
│   (original h1 -> h2, original h2 -> h3), optimized reader fonts...    │
└────────────────────────────────────────────────────────────────────────┘
```

#### Key Typographic Elements

1. **Master Masthead**:
   - Document Title (from `--title`, `--name`, or derived series title).
   - Unified byline: aggregated authors (or unique list of authors) and date range.
   - Provenance box listing each source URL and capture date.
   - Aggregate reading statistics: total parts, total word count, estimated reading time.
2. **Interactive Table of Contents**:
   - Rendered directly below the master masthead.
   - Each part title links to `#part-1`, `#part-2`, etc.
3. **Part Dividers (`<section class="article-part">`)**:
   - `page-break-before: always;` (or `break-before: page;`) forces each article to start cleanly at the top of a fresh page.
   - Part indicator badge (e.g. `Part 1 of 3`).
   - Article-specific title and original publication date.
   - Clickable source link to the original article URL for that specific part.
4. **Heading Level Normalization**:
   - The master document title uses `<h1>`.
   - Each article's title uses `<h2>`.
   - Any internal `<h1>` tags within an article's body are shifted to `<h3>`, `<h2>` to `<h3>`, etc., preventing internal article subheadings from competing visually with the chapter title.
5. **Namespaced Anchor IDs**:
   - When merging multiple web pages, internal IDs (like `<h2 id="intro">` or `<a href="#footnote-1">`) frequently collide.
   - The adapter must prefix internal IDs and links: `#part1-intro`, `#part2-intro`.
6. **Running Footers via CSS Paged Media (`@page`)**:
   - Dynamic running footer displays:
     ```css
     @page {
       @bottom-left {
         content: "Raft Consensus Algorithm";
       }
       @bottom-right {
         content: counter(page);
       }
     }
     @page :first {
       @bottom-left { content: none; }
       @bottom-right { content: none; }
     }
     ```

---

## 6. Metadata, Vault Integration, and Sync Lifecycle

### 6.1 PDF Page-1 Marker Schema

Bob embeds a machine-readable JSON marker in the PDF's page-1 metadata (`highlights_marker_base`).

For multiple URLs, `source_url` is stored as a JSON array (represented in Rust as `MarkerValue::List`):
```json
{
  "title": "Raft Consensus Algorithm",
  "source_url": [
    "https://raft.github.io/part1.html",
    "https://raft.github.io/part2.html",
    "https://raft.github.io/part3.html"
  ],
  "author": "Diego Ongaro, John Ousterhout",
  "published": "2014-05-20",
  "captured": "2026-10-15",
  "parent": "sase",
  "status": "ready"
}
```

### 6.2 Reference Note Frontmatter (`note.md`)

When `bob ref scan` synchronizes the PDF into the vault, `model.rs` formats the marker projection into Obsidian YAML frontmatter:
```markdown
---
title: "Raft Consensus Algorithm"
source_url:
  - https://raft.github.io/part1.html
  - https://raft.github.io/part2.html
  - https://raft.github.io/part3.html
author: Diego Ongaro, John Ousterhout
published: 2014-05-20
captured: 2026-10-15
parent: "[[sase]]"
note_type: reference
ref_type: blogs
source_pdf: lib/blogs/raft_consensus_algorithm.pdf
source_pdf_sha256: 4f3b...
pipeline_version: highlights-ref-mvp-3
---

# Raft Consensus Algorithm

- [ ] #ref #pdf [[lib/blogs/raft_consensus_algorithm.pdf]] #hide ^ref

## Contents

1. [Part 1: Introduction and Core Replicated State Machines](https://raft.github.io/part1.html)
2. [Part 2: Leader Election and Safety Guarantees](https://raft.github.io/part2.html)
3. [Part 3: Cluster Membership Changes and Log Compaction](https://raft.github.io/part3.html)

## Highlights

<!-- highlights:begin -->
<!-- highlights:end -->
```

### 6.3 Intake Deduplication (`sources.rs`)

`sources.rs` maintains an index of already captured or queued sources to prevent duplicate clipping.
- **Update Required in `collect_intake_sources`**:
  Currently, `sources.rs` does:
  ```rust
  if let Some(url) = projection.get("source_url").and_then(|v| v.as_string()) { ... }
  ```
  It must be updated to inspect both `MarkerValue::String` and `MarkerValue::List`:
  ```rust
  if let Some(val) = projection.get("source_url") {
      for url in val.as_string_list() {
          if let Ok(cleaned) = validate_and_clean(&url) {
              recorded.push(RecordedSource { ... });
          }
      }
  }
  ```
- **Preflight Check**:
  When `bob ref create <U1> <U2> ...` is invoked, Bob checks each URL against `recorded`. If *any* of the URLs is already captured or queued, Bob refuses (or warns under `--force`), pinpointing the exact offending URL:
  ```
  bob ref create: error: URL already captured: https://raft.github.io/part1.html (in lib/blogs/raft_part_1.pdf)
  hint: pass --force to recapture
  ```

### 6.4 Companion Audio (`--listen`)

`bob ref create <URLs...> --listen`:
- The listen subsystem (`super::listen`) passes the rendered PDF to `sase listen render`.
- Because the PDF is a single unified document with continuous text, `sase listen render` naturally generates a single audio edition covering the entire series, perfectly bound beside the PDF in `xlib/<ref_type>/<stem>.mp3`.

---

## 7. Recommended Solution & Implementation Plan

### 7.1 Proposed CLI Syntax

```
bob ref create <TARGETS...> [OPTIONS]
```

- **Arguments**:
  - `<TARGETS...>`: One or more targets. If multiple targets are given, all must be HTTP/HTTPS URLs.
- **Options**:
  - `-N, --name <STEM>`: Output filename stem [default: derived from TARGET common prefix]. Required for multiple URLs if no common prefix can be derived.
  - `-O, --output-dir <DIR>`: Output directory for the generated PDF. Composes with `-N, --name`.
  - `-o, --output <PDF>`: Complete path for the generated PDF, including `.pdf` filename (conflicts with `--name`, `--ref-type`, `--output-dir`).
  - `-n, --no-audio`: Skip companion audio discovery (unmodified, boolean flag).
  - `-T, --title <TITLE>`: Override the derived master document title.
  - `-A, --author <NAME>`: Override the derived author.
  - `-p, --published <DATE>`: Override the derived publish date.
  - `-P, --parent <NOTE>`: Area or project note that owns the reading task (required).

### 7.2 Implementation Phases

```
┌────────────────────────────────────────────────────────────────────────┐
│ Phase 1: CLI & Prefix Engine (Rust: create.rs, clip_url.rs)            │
│ • Update clap definition: Arg::new("target").num_args(1..)            │
│ • Implement common_url_stem(&[WebUrl]) -> Option<String>               │
│ • Add -O, --output-dir option                                          │
│ • Enforce fail-fast check: if targets > 1 && !has_name && stem.is_none │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ Phase 2: Web Clip Adapter Protocol (Python: adapter & render)          │
│ • Extend CaptureRequest with urls: list[str]                           │
│ • Playwright fetches articles sequentially in single browser session   │
│ • Defuddle extracts readability DOM for each URL                       │
│ • web_clip_render.py builds unified HTML with Master Masthead, TOC,    │
│   Part dividers, and CSS paged media                                   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ Phase 3: Metadata, Markers, & Dedupe (Rust: sources.rs, stamp.rs)      │
│ • Support MarkerValue::List for source_url in markers & frontmatter    │
│ • Multi-URL deduplication indexing in collect_intake_sources           │
│ • Render ## Contents list in default reference note body               │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ Phase 4: Verification & Test Suite                                     │
│ • Unit tests for common_url_stem heuristics (diverse URL shapes)       │
│ • CLI regression tests for -N/--name requirement                       │
│ • Integration tests for multi-URL capture and note generation          │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Summary Comparison of Approaches

| Decision Area | Initial Proposal | Recommended Architecture | Rationale |
| :--- | :--- | :--- | :--- |
| **Name Option** | Add `-n\|--name` | Keep `-N, --name` (canonical) | `-n` is already `--no-audio`. Reassigning breaks backward compatibility. |
| **Output Option** | Change `-o\|--output` to `-o\|--output-directory` | Add `-O, --output-dir`, preserve `-o, --output` | Prevents breaking existing tests and scripts that pass a full `.pdf` path. |
| **Common Prefix Requirement** | Require `-n` iff URLs share no common prefix | Require `-N` iff `common_url_stem` finds no semantic directory or token prefix | Naive string LCP produces unusable stems. Semantic path analysis guarantees high-quality naming. |
| **Validation Timing** | Not specified | Immediate fail-fast in Clap handler | Avoids launching heavy Chromium browsers if the command is missing required arguments. |
| **Document Generation** | Not specified | Adapter-level unified HTML assembly | Generates a table of contents, continuous page numbering, and consistent typography. |
| **Reference Note Body** | Not specified | Add `## Contents` section with markdown links to parts | Provides immediate access to original web articles from within Obsidian. |

---

*End of Research Report.*
