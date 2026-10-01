# From Web URL to a Durable, Readable Highlights Reference PDF

Research date: 2026-10-01  
Researcher: cdx  
Scope: a reliable `bob` workflow that turns a public web URL into a readable PDF, feeds the existing Highlights intake pipeline, and ultimately creates a Bob vault reference note.

## Executive conclusion

This is a good idea if the PDF is treated as an **immutable reading and annotation snapshot**, not as a perfect archival copy of the live site and not as the only searchable representation of the source.

The best implementation is a new, explicit command such as:

```text
bob highlights create-url <URL>
```

It should:

1. open the URL in an isolated, temporary Chrome/Chromium profile through the Chrome DevTools Protocol;
2. wait for the document to become genuinely article-like, with bounded timeouts;
3. run a vendored Mozilla Readability build against the rendered DOM;
4. sanitize and normalize the extracted HTML;
5. place that content into a Bob-owned print template and render it with Chrome's PDF engine;
6. embed the same page-1 marker used by the existing Highlights pipeline, including `source_url`, `author`, and `published` metadata;
7. atomically place the PDF in `xlib/web/`; and
8. leave `bob highlights scan` to move it into `lib/web/` and create `ref/web/<name>.md` in the established, guarded workflow.

I would implement the browser controller in Rust with a pinned CDP crate such as `headless_chrome`, rather than adding a Node/Playwright runtime to the installed `bob` command. Playwright is the stronger reference implementation and should inform behavior and tests, but a Rust CDP client fits this repository's deployment model better. Chrome's PDF API exposes the important controls—print backgrounds, margins, CSS page size, document outlines, and tagged PDFs—through both Playwright and the CDP wrappers ([Playwright `page.pdf`](https://playwright.dev/docs/api/class-page#page-pdf), [`headless_chrome` PDF options](https://docs.rs/headless_chrome/latest/headless_chrome/types/struct.PrintToPdfOptions.html)).

Do **not** make raw `curl`/Pandoc URL ingestion the main path, do **not** print arbitrary site chrome by default, and do **not** silently fall back to producing a PDF of an access-denied page. Those are all attractive shortcuts that fail the reliability requirement.

## What already exists in bob-cli

The current implementation provides a very strong base:

- `bob highlights create <md-file>` renders through Pandoc and XeLaTeX, with a three-level table of contents, PDF outline bookmarks, wrapped code, stable fonts, and atomic PDF installation.
- It embeds a standalone page-1 `/Text` annotation containing marker fields such as `status`, `parent`, `title`, and optionally `id`.
- The default target is `xlib/<ref_type>/<stem>.pdf`; `scan` moves that PDF to the corresponding `lib/` path and creates the corresponding note in `ref/`.
- The intake path refuses destructive collisions, including an already archived library PDF or a Markdown/TextBundle sidecar that Highlights owns.
- Reference-note sync already recognizes the standard user fields `source_url`, `author`, and `published`. These are precisely the important provenance fields for a captured article.
- Generated notes already get `type: "[[ref]]"`, a required `parent`, `source_pdf`, a content hash, pipeline metadata, and the managed Highlights region.
- The cross-machine `xlib/` bridge and scheduled Mac scan already solve delivery from athena/apollo into the Mac's Highlights library.

This means the work should be an additional **source adapter and renderer**, not a second reference-note system. Reusing marker embedding, target planning, collision checks, reporting, atomic writes, `scan`, and note synchronization is substantially safer than independently creating `~/bob/ref/` notes.

## Empirical finding from the example URL

I tested the example URL on 2026-10-01:

```text
https://openai.com/index/open-source-codex-orchestration-symphony/
```

A bounded `curl -L` request returned HTTP 403 in this environment with both a purpose-specific user agent and a current Chrome-like user agent. The returned body was roughly 10 KB and Pandoc reduced it to only 46 bytes of plain text—clearly not the article. A browser-backed reader was able to expose the full article, title, authors, date, headings, code, and images ([the source page](https://openai.com/index/open-source-codex-orchestration-symphony/)).

That single case does not prove every raw HTTP client will fail from Bryan's machines, but it does demonstrate that the proposed example is already a bad basis for a fetch-only implementation. A command that saves the 403/challenge page as if it were the article would appear to succeed while corrupting the knowledge workflow. Browser acquisition and content validation are requirements, not polish.

## Requirements I would adjust

### 1. Define the output as a reading snapshot, not a faithful website archive

“Convert a URL to PDF” is ambiguous. There are two different products:

- a visual facsimile of the website, including its navigation, banners, cookie dialogs, comments, and responsive layout; or
- a stable, typeset representation of the primary article.

The requested “beautiful and readable” result strongly favors the second. Reader mode should be the default. A raw-page mode can exist as an explicit escape hatch for content Readability cannot represent, but it should not be the automatic fallback.

### 2. Preserve the existing two-stage intake contract

The URL command should produce an intake PDF; it should not write a reference note directly. On the Mac, the existing scan immediately or eventually moves `xlib/web/...pdf` into `lib/web/` and creates `ref/web/...md`. On other hosts, the existing `bob_xlib_pull` bridge provides the same result.

This is a slight adjustment to the apparent “one command creates the note” requirement. It is justified because the established scan path contains the collision guards, library move, marker merge, sidecar handling, and guarded vault write behavior. If immediate completion matters, a future convenience command can compose `create-url` and `scan` on a machine that owns the Highlights library; it should still call the existing operations rather than bypass them.

### 3. Make PDFs immutable after intake

The default must never refresh or overwrite a previously annotated PDF. Highlights annotations and page links are tied to a particular pagination. Updating the source page and regenerating the PDF can invalidate both.

For a URL already present in the library, the command should report the existing PDF/note and stop. A future “recapture” operation should create a new versioned snapshot and a new reference note or explicitly link it as a successor; it should never reuse `--force` to replace the annotated library object.

### 4. Limit the first release to public article-like pages

The MVP should explicitly exclude paywall bypass, authenticated sessions, private browser profiles, infinite-scroll feeds, multi-page sites, and interactive applications. Headless browsers do not make these cases safe or deterministic. An interactive, headful opt-in can be considered later, but importing a person's normal Chrome profile would expose cookies, history, and credentials to the capture process and should not be the default.

### 5. Store capture provenance

In addition to the already-supported `source_url`, `author`, and `published`, add a standard synced user field such as `captured_at`. Show the source URL and capture time visibly in the PDF too. The PDF is a time-specific representation of a mutable source; that fact should never be implicit.

## Candidate approaches

| Approach | Readability | Dynamic/blocked pages | Output control | Operational cost | Verdict |
| --- | --- | --- | --- | --- | --- |
| Print the live page with Chrome | Inconsistent; includes site chrome | Best available locally, though bot protection can still refuse it | Good PDF controls, poor content selection | Browser required | Useful explicit `page` mode, not the default |
| Raw HTTP fetch → Pandoc/XeLaTeX | Often good typography, poor boilerplate removal | Fails JS-only sites and can receive challenge pages; the example returned 403 here | Excellent and already implemented | Smallest code change | Insufficient as the reliable primary path |
| Raw HTTP fetch → Readability → Pandoc/XeLaTeX | Good for server-rendered articles | Still fails pages that require a browser | Excellent, reuses current renderer | Moderate | Good fast path only; not enough alone |
| Browser DOM → Readability → Bob HTML/CSS → Chrome PDF | Consistent reader view | Best general coverage; still honest about auth/bot limits | Excellent, including tagged PDF and outlines | Browser plus CDP integration | **Recommended** |
| Browser DOM → Readability → Pandoc/XeLaTeX | Consistent reader view | Same acquisition coverage as above | Existing typography and TOC, but extra HTML-to-AST conversion can lose web structures | Browser plus existing toolchain | Sensible fallback if Chrome pagination proves poor |
| WeasyPrint | Good when given clean HTML | No live JavaScript; separate Python/Pango stack | Strong paged-media and PDF/A support | New runtime and native dependencies | No advantage for this use case |
| Hosted conversion API | Varies | Convenient, but remote services are still identifiable as bots and can be blocked | Varies | Credentials, privacy, cost, service dependency | Optional backend only, never the default |

### Why not direct browser printing?

Chrome can produce selectable, linked, tagged PDFs with document outlines. Playwright documents that `page.pdf()` uses print CSS and supports explicit margins, backgrounds, CSS page sizing, `outline`, and `tagged` output ([API](https://playwright.dev/docs/api/class-page#page-pdf)). CSS paged media also provides the right primitives for page size, margins, breaks, widows, and orphans ([MDN](https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Paged_media)).

The weakness is not the PDF engine; it is the input DOM and CSS. Printing the live page delegates the result to every site's print stylesheet. Many sites include navigation, related stories, subscription prompts, sticky UI, enormous hero images, or no useful print stylesheet at all. The output changes when the site deploys a CSS revision. A Bob-owned reader template produces a consistent artifact.

### Why Readability?

Mozilla Readability is the extraction algorithm behind Firefox Reader View. Its `parse()` result includes cleaned article HTML, text, title, byline, site name, language, excerpt, and publication time. It also resolves relative links when given the source URL. The project explicitly warns that its output is **not** a security sanitizer and recommends sanitization plus a restrictive Content Security Policy ([Mozilla Readability README](https://github.com/mozilla/readability#readme)).

There are promising native Rust ports. For example, `readabilityrs` reports 119/130 compatibility with Mozilla's corpus and includes useful normalization for code, lazy images, footnotes, and math ([crate documentation](https://docs.rs/crate/readabilityrs/latest)). `legible` similarly returns HTML, CommonMark, normalized text, and metadata while emphasizing the same sanitation requirement ([crate documentation](https://docs.rs/legible/latest/legible/)).

I would still vendor the upstream JavaScript implementation for the first version. The browser already supplies the DOM it expects, upstream behavior is the reference, and the source can run in the loaded page through CDP. A native port is worth reevaluating later if binary size or extraction latency matters, using a corpus rather than intuition.

### Why Chrome/CDP in Rust rather than Playwright in production?

Playwright is an excellent orchestration library and its documentation is the clearest specification for the desired behavior. It can use installed Google Chrome via the `chrome` channel, or manage browser binaries itself ([browser configuration](https://playwright.dev/docs/browsers#google-chrome--microsoft-edge)). Managed Playwright browsers consume hundreds of megabytes and introduce a Node/package installation lifecycle ([binary management](https://playwright.dev/docs/browsers#managing-browser-binaries)).

`bob` is a compiled Rust CLI. A pinned Rust CDP client keeps the executable's control path in Rust, can discover a locally installed Chrome/Chromium, defaults to a temporary profile, supports request interception and JavaScript evaluation, and exposes the same PDF settings. `headless_chrome` currently provides these capabilities and a high-level PDF method ([crate documentation](https://docs.rs/headless_chrome/latest/headless_chrome/)). The browser binary remains an explicit prerequisite, checked by `bob highlights doctor`, with a configuration/environment override analogous to `BOB_PANDOC_COMMAND`.

This choice is not free: CDP/browser-version compatibility and browser discovery need integration tests on Linux and macOS. If that proves fragile in a spike, use a pinned Playwright helper rather than inventing a custom CDP layer. The architecture above is independent of the controller library.

### Why not WeasyPrint or a hosted browser?

WeasyPrint is a strong static paged-media engine, but it intentionally has no JavaScript/live rendering and brings Python, Pango, and related native dependencies ([design](https://doc.courtbouillon.org/weasyprint/stable/going_further.html), [installation](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html)). That makes it a poor acquisition engine and a redundant output engine here.

Hosted browser services can generate PDFs or extracted Markdown, but they add credentials, content disclosure to a third party, quotas, cost, and another availability boundary. Cloudflare's own Browser Run documentation also states that its requests are always identifiable as bots, so it cannot promise to bypass the class of protection seen in this investigation ([PDF endpoint notes](https://developers.cloudflare.com/browser-run/quick-actions/pdf-endpoint/)). A remote backend could be a later opt-in for machines without Chrome, not the default contract.

## Proposed command and user experience

### Command shape

Use a separate subcommand rather than overloading the existing Markdown positional:

```text
bob highlights create-url <URL> \
  [-b|--bob-dir PATH] \
  [-d|--dry-run] \
  [-m|--mode reader|page] \
  [-o|--output PDF] \
  [-P|--parent NOTE] \
  [-s|--status STATUS] \
  [-t|--ref-type DIR] \
  [-x|--xlib-dir PATH]
```

Recommended defaults:

- `--mode reader`
- `--ref-type web`
- `--parent obsidian_ref`
- `--status ready`
- `--output` absent, so the PDF participates in normal intake

The proposed public options follow the repository rule that every long option gets a short alias and help output stays alphabetized. Avoid exposing tuning flags for Readability thresholds, navigation events, image waits, font loading, or Chrome arguments until real cases demonstrate a user need. Those are implementation policy, not a stable CLI contract.

`--dry-run` necessarily performs network/browser reads so it can know the final URL, title, metadata, and derived filename; it must promise only **no filesystem writes** and clearly report that network access occurred.

### Naming and duplicate identity

Derive a human-readable, collision-resistant stem from the extracted title plus the canonical/final URL, for example:

```text
open-source-codex-orchestration-symphony--7d3a09c2.pdf
```

The short hash should be computed from a normalized canonical URL, not the mutable page body. The visible title remains natural. Before writing, scan existing marker/reference metadata for the same `source_url`; report the existing object rather than creating a duplicate. The hash is a collision guard, not the only deduplication mechanism.

Do not trust `<link rel=canonical>` blindly when it changes origin. Retain the user-requested URL, final redirected URL, and declared canonical URL internally; choose the same-origin canonical URL when valid, otherwise the final URL. The selected value becomes `source_url` and is printed visibly.

### Successful output

Success should resemble the current `create` report:

```text
created Highlights-ready web PDF
pdf: /.../bob/xlib/web/open-source-codex-orchestration-symphony--7d3a09c2.pdf
title: An open-source spec for Codex orchestration: Symphony
source_url: https://openai.com/index/open-source-codex-orchestration-symphony/
author: Alex Kotliarskyi, Victor Zhu, and Zach Brock
published: 2026-04-27
captured_at: 2026-10-01T...
pages: ...
next: bob highlights scan
```

### Marker projection

Embed at least:

```text
- status: ready
- parent: obsidian_ref
- title: An open-source spec for Codex orchestration: Symphony
- source_url: https://openai.com/index/open-source-codex-orchestration-symphony/
- author: Alex Kotliarskyi, Victor Zhu, and Zach Brock
- published: 2026-04-27
- captured_at: 2026-10-01T...
```

Use the existing marker renderer rather than interpolating YAML-like strings. Omit absent metadata instead of inventing it. Normalize a publication timestamp only when parsing is unambiguous; otherwise keep the source string or omit the field with a warning.

## Detailed pipeline

### 1. Validate before launching

- Accept only `http` and `https` URLs.
- Reject credentials embedded in the URL.
- Reject fragments for identity purposes while retaining them only if they intentionally select article content.
- Reject localhost, loopback, link-local, and private-network destinations by default, including redirect targets. This reduces SSRF and router/intranet probing risk. A future explicit private-network opt-in can be considered.
- Resolve the output/intake plan and preflight obvious collisions before spending time rendering where possible.

### 2. Launch an isolated browser

- Use a new temporary browser profile/context for every capture.
- Keep the browser sandbox enabled.
- Do not load Bryan's ordinary Chrome profile, extensions, or cookies.
- Disable downloads and popups; close unexpected targets.
- Bound total navigation time, DOM size, rendered article length, image bytes, page count, and final PDF bytes.
- Discover Chrome/Chromium predictably and add a doctor check plus an environment/config override for its path.

The browser controller should be treated as untrusted-content infrastructure even though this is a personal CLI.

### 3. Decide when the page is ready

Do not use an unbounded “network idle” wait. Playwright itself discourages treating `networkidle` as a general readiness criterion because modern pages may keep connections alive ([navigation API note](https://playwright.dev/docs/api/class-page#page-reload)). A bounded policy is more reliable:

1. wait for `DOMContentLoaded`;
2. allow a short settle interval;
3. poll for an article candidate/title/text threshold;
4. wait for `document.fonts.ready` with a cap;
5. attempt to settle visible article images with per-resource and global caps; and
6. stop at the total deadline.

Detect common failure content—HTTP error documents, browser interstitials, CAPTCHA/challenge titles, login walls, nearly empty extraction, or extracted text dominated by access-denied language. On detection, exit nonzero and leave no PDF or note.

### 4. Extract and sanitize

- Run vendored Mozilla Readability against a clone of the rendered document.
- Pull the article result and page metadata back into Rust as structured JSON.
- Resolve relative links and image URLs against the final document URL.
- Sanitize with a narrow allowlist. Preserve semantic headings, paragraphs, lists, links, images/picture/source, figures/captions, tables, code/pre, blockquotes, emphasis, details/summary, footnotes, sub/sup, and safe MathML/SVG only if explicitly tested.
- Remove scripts, event handlers, forms, embedded frames, object/embed, refresh directives, `javascript:`/`file:` URLs, and arbitrary inline styles.
- Add a restrictive CSP to the generated print document.

Sanitization is a hard requirement. Both upstream Readability and Rust ports document that extraction cleans for readability but does not make hostile HTML safe.

### 5. Build a Bob-owned article document

Generate a standalone HTML document containing:

- the title;
- site name, author, publication date, and capture time;
- a visible source link;
- an optional compact table of contents for documents with enough headings;
- the sanitized article body; and
- a small provenance footer.

The print stylesheet should define:

- Letter and A4-friendly page geometry with roughly 0.75–0.85 inch margins;
- a readable serif body around 10.5–11 pt and a sans-serif heading stack;
- a monospace stack with wrapping/overflow handling equivalent to the current Pandoc filter;
- `break-inside: avoid` for modest figures, blockquotes, tables, and code blocks, while allowing very tall blocks to split;
- `overflow-wrap: anywhere` for URLs and identifiers;
- sane table scaling and repeating table headers where supported;
- bounded image dimensions with captions;
- visible link styling that still prints well in grayscale;
- `orphans`/`widows` values and heading break control; and
- explicit light color scheme and `print-color-adjust` policy.

Avoid remote web fonts. They create another availability/privacy boundary and can delay or destabilize output. Prefer good system stacks or bundle a small set of redistributable fonts if cross-machine visual identity becomes important.

### 6. Render and post-process

Render through Chrome with:

- print background enabled;
- document outline enabled;
- tagged PDF enabled;
- a fixed page format unless the command later exposes a deliberate paper option;
- page numbers and a short source hostname in the footer; and
- no browser-default URL/date header.

Then load the result with `lopdf`, confirm it has at least one page, embed the existing page-1 marker annotation, and atomically install it through the same helper used by Markdown `create`.

`headless_chrome` and Playwright expose outline/tagged PDF switches over the underlying Chrome print API, so this does not require a second PDF library beyond the already-used `lopdf` post-processing.

### 7. Hand off to the existing pipeline

Write to `xlib/web/<stem>.pdf`. The normal scan then moves it to `lib/web/<stem>.pdf` and creates `ref/web/<stem>.md`. The resulting note should have a required parent, `type: "[[ref]]"`, `ref_type: web`, the source metadata, the PDF task link, and the managed Highlights region.

This also preserves the existing safety invariant that a same-stem Markdown file beside the PDF is owned by Highlights as a sidecar. Do not write extracted Markdown beside the PDF.

## Failure behavior

The command should fail closed:

- browser missing: tell the user exactly what executable was searched and how to configure it;
- navigation/redirect disallowed: report the final attempted URL without writing;
- access challenge/login wall: report “page did not yield article content,” not success;
- extraction too small or ambiguous: recommend explicit `--mode page` after manual review;
- image failures: succeed only if the article text is sound, list missing images, and render visible placeholders rather than silently collapsing context;
- target/library/sidecar collision: reuse the current refusal messages and do not overwrite;
- render/marker validation failure: remove the temporary result and leave the target absent;
- duplicate `source_url`: identify the existing PDF/reference note and exit successfully without creating another object, unless a later explicit recapture workflow exists.

Raw-page mode should still add the provenance block and marker and should still use Bob's print constraints. It is an explicit user choice, not an automatic way to conceal extraction failure.

## Security and privacy critique

Opening arbitrary URLs is a materially larger attack surface than converting local Markdown:

- the page runs hostile JavaScript in a real browser;
- subresources can probe local services or leak the machine's IP;
- HTML/images/SVG can target parser or renderer bugs;
- remote resources can hang, expand enormously, or produce huge PDFs;
- authenticated profiles would expose private data;
- extracted HTML is unsafe until sanitized; and
- a browser can download files or launch popups unless controlled.

Mitigations should include the isolated profile, enabled sandbox, scheme/private-network policy, request interception, no personal cookies, CSP, HTML sanitizer, process/resource deadlines, output caps, and atomic no-partial-write behavior described above. Never pass `--no-sandbox` as a convenience default.

This workflow also creates a personal copy of third-party material. For private research that is ordinarily the user's responsibility, but the CLI should preserve attribution and source URLs, avoid defeating paywalls/access controls, and avoid presenting the snapshot as republishable content.

## Product critique: is PDF the right artifact?

### Where PDF is the right choice

- It freezes pagination, which makes Highlights annotations and page links durable.
- It preserves code, figures, and layout better than a bare text clipping.
- It remains readable if the site changes or disappears.
- It fits the current `xlib → lib → ref` model and existing annotation sync.

### Where PDF is weak

- Binary snapshots are larger, hard to diff, and expensive to regenerate.
- Obsidian workflows are strongest on Markdown; full-text PDF search/indexing is not as portable or controllable.
- Reader extraction can omit interactive diagrams, comments, footnotes, or unusual layouts.
- A PDF is a snapshot of the rendered/extracted page, not cryptographic proof of what the publisher served.
- The source can change, so citations need both URL and capture date.

I would therefore keep the PDF and reference note as the MVP, but add a short extracted excerpt to the visible PDF and potentially to reference-note frontmatter/body later. If full-text vault search becomes a real need, add a separate, explicitly named source-snapshot area under the reference note or vault—not a same-stem `.md` beside the library PDF, because Highlights owns that path. Do not make full extracted Markdown part of the first release before deciding how it is updated, searched, synced, and distinguished from human notes.

## Implementation shape in bob-cli

Suggested boundaries:

- `src/native/highlights_ref/create_url.rs`: CLI, URL plan, browser/extraction orchestration, reporting.
- `src/native/highlights_ref/web_browser.rs`: browser discovery, isolated launch, request policy, readiness, Readability evaluation.
- `src/native/highlights_ref/web_document.rs`: sanitation, metadata normalization, HTML template, print CSS.
- `src/native/highlights_ref/vendor/readability.js` and license file: pinned upstream source.
- refactor reusable target planning, collision checks, marker composition/embedding, temporary output, and atomic installation from `create.rs` into shared helpers.

Do not initially unify Markdown and URL rendering behind an overly generic abstraction. Share the genuine invariants—target/marker/install/reporting—while allowing Markdown to remain Pandoc/XeLaTeX and web articles to use HTML/Chrome. They have different failure modes and inputs.

Add `source_url`, `author`, `published`, and `captured_at` to the URL marker composition explicitly. The first three already participate in standard reference-note sync; `captured_at` would need to join that catalog and its tests.

## Verification strategy

### Unit tests

- URL validation, normalization, redirect/canonical selection, slug/hash naming.
- metadata normalization and omission rules.
- private/local address rejection, including IPv4, IPv6, and redirect cases.
- sanitation of scripts, event handlers, dangerous schemes, iframe/object/embed, forms, hostile SVG, and malicious `srcset`.
- challenge/login/error-page detection.
- reader HTML template escaping and CSP.
- marker round trip for all source fields.
- current collision rules, especially archived PDFs and Highlights sidecars.

### Integration corpus

Maintain a small checked-in HTML fixture corpus and a live, non-blocking smoke list covering:

- the example OpenAI article;
- static semantic articles;
- client-rendered articles;
- code-heavy pages with long lines;
- tables, nested lists, blockquotes, figures/captions, lazy images, footnotes, and math;
- non-English and right-to-left text;
- a 403/challenge page;
- a login wall;
- a non-article landing page; and
- a deliberately hostile document.

Live sites should not be the only CI oracle. Keep rendered-DOM or extracted fixtures for deterministic regression tests, then run live smoke tests separately because remote sites and bot policies change.

### PDF assertions

- nonzero pages and bounded page/file size;
- visible title/source/author/date text;
- working HTTP links;
- PDF outline present;
- tagged PDF catalog present where Chrome supports it;
- page-1 marker readable by `bob highlights marker`;
- `scan --dry-run` maps `xlib/web/...` to `lib/web/...` and `ref/web/...md`;
- actual scan creates a note with `parent`, `type`, `ref_type`, provenance, and PDF task;
- long code/URLs do not overflow; and
- annotation round-trip remains compatible with a real Highlights-authored sidecar on the Mac.

Use a pinned browser in CI for visual/golden checks. Do not expect byte-for-byte identical PDFs across arbitrary Chrome, OS, and font versions; compare structural properties and targeted rasterized pages instead.

## Rollout

1. **Spike the browser path** against the example URL, one static article, one JS-heavy article, and one challenge page. Prove extraction, sanitation, PDF rendering, marker embedding, and `scan --dry-run` before designing extra options.
2. **Land reader mode only**, with Chrome discovery in `doctor`, strict failures, deterministic naming, and no authenticated profile support.
3. **Exercise on the Mac with real Highlights**, verifying selectable text, page links, annotations, TextBundle behavior, and that `lopdf` post-processing preserves Chrome's outline/tagging.
4. **Add explicit raw-page mode** only after real extraction failures show it is useful.
5. **Evaluate full-text Markdown storage or interactive capture** as separate product decisions, based on observed use rather than folding them into the MVP.

## Final recommended solution

Implement `bob highlights create-url <URL>` as a browser-backed reader snapshot producer that feeds the current Highlights intake system.

Use a pinned Rust CDP controller with a locally installed, sandboxed Chrome/Chromium and a fresh temporary profile. Extract the rendered DOM using vendored Mozilla Readability, sanitize it in Rust, render a carefully designed Bob HTML/CSS document to a tagged PDF with an outline, then reuse the existing `lopdf` page-1 marker, collision guards, atomic installation, `xlib` routing, and `scan`-generated reference notes. Embed and visibly print the canonical source URL, author, publication date, and capture time. Fail closed on access challenges, weak extraction, unsafe destinations, and duplicates. Keep `reader` as the default, make whole-page printing explicit, and never overwrite an annotated library PDF.

That design gives the desired one-URL ergonomics and a consistently beautiful result without creating a parallel vault-writing path. It also makes the unavoidable limitations honest: it is an immutable personal reading snapshot of a public article, not a universal web archiver or paywall bypass.
