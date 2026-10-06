# `bob highlights create --listen`: one front door for everything you read *and* listen to

- **Date:** 2026-10-06
- **Researcher:** cld (one of five independent reports; peers write `__cdx`, `__grk`, `__mus`,
  `__gem`)
- **Question:** Add `--listen` to `bob highlights create` so that it runs a configurable listen
  command (by default `sase-listen render <target> -e full`), which publishes a podcast episode to
  Bryan's AntennaPod feed alongside the Highlights PDF and its ref note. Widen `create` to accept
  every `<target>` that `sase-listen render` accepts (including PDF URLs and arXiv), show the
  listen command's output in full, and make the result intuitive, reliable, and beautiful. Is
  this a good idea? What would I change? What should be built?

---

## 0. Bottom line

1. **Build it. The evidence says the gap is real and growing.** On athena alone, sase-listen
   rendered **13 article/paper episodes in the last two days** (2026-10-05 and 2026-10-06), and
   **10 of them have no ref note in `~/bob/ref/`**, including 6 episodes covering 5 arXiv papers
   (§1.4). Bryan is listening to far more than he is tracking.
2. **Make `create` the single front door. `clip` becomes a permanent hidden alias.**
   `bob highlights clip` already does most of the URL half: HTML articles and direct-PDF URLs.
   This reverses the 2026-10-01 "sibling command" decision on purpose. That decision was right
   for one new target kind. With five kinds (Markdown, web page, PDF URL, arXiv, local PDF) and a
   cross-cutting `--listen`, one command that classifies its target is easier to use than three
   commands that each half-support listening (§3, A1).
3. **`-L, --listen` runs a configured argv template and inherits the terminal. It gets the audio
   back through a single contract: "write the finished audio to `{audio}`."** sase-listen already
   satisfies that contract with its existing `-o/--output` flag, which copies the MP3 atomically
   before it publishes. So bob never parses sase-listen's output, never needs `--json` (which
   would hide the live checklist), never scrapes its library, and needs **no upstream change**
   (§4.5).
4. **The PDF is the durable part; the audio attaches to it.** The stage order is:
   plan → capture (fails fast, before any money is spent on TTS) → listen → render Markdown →
   install audio then PDF together.
   - If the listen command fails, bob still queues the PDF, exits 1, and prints a retry hint.
   - Re-running with `-L` on a target that's already captured *attaches* audio instead of
     refusing.
   - Ctrl-C writes nothing and exits 130 (§4.6, §4.7).
5. **`-e full` doesn't work for Markdown in sase-listen today.** `render <file.md> -e full` exits
   2 ("Generated brief and full editions are available for article URLs and PDF files"). So the
   config needs a `markdown_command` variant. For Markdown, bob narrates the sibling
   `<stem>_narration.md` when one exists (§1.2, A3).
6. **Publish explicitly.** `feed.auto_publish: true` only covers `kind: research` and
   `kind: article`. Plain Markdown episodes would silently stay out of the feed. The chezmoi
   template therefore passes `--publish` (A4).
7. **"Always tracking" needs a backstop beyond a flag.** Two more pieces:
   - `create <url>` *without* `-L` binds an existing sase-listen episode for that URL. Markdown
     already gets this kind of discovery.
   - `doctor` reports listened-but-untracked episodes, with ready-to-paste commands.

   Together these close the "I just ran `sase-listen render` directly" leak. That leak accounts
   for all 10 untracked episodes (§3, A13).

Requirement adjustments are collected in §3. The recommended solution and phased plan are in §7.

---

## 1. What exists today (verified)

### 1.1 bob-cli (`src/native/highlights_ref/`)

| Piece | Fact | Where |
| --- | --- | --- |
| `create <MD_FILE>` | Only `.md` (`validate_markdown_path`). Renders with pandoc/XeLaTeX into `render_temp_path` (a dotfile **inside the target dir**), stamps the page-1 marker, installs atomically. Default target `xlib/chat/<stem>.pdf`. | `create.rs:191-441, 519, 600` |
| Companion audio | Discovery order: `--audio PATH` → frontmatter `audio.episode_id` → sibling `<stem>_narration.md` sha256 matched against `<library>/*/manifest.json` `source.sha256`/`script.sha256` → existing same-stem audio. The copy lands beside the PDF. It reuses identical bytes, refuses different bytes without `--force`, and refuses an occupied `lib/` slot. | `create.rs:674-846`, `audio.rs:186-416` |
| Listen card | `<div class="listen">` becomes a callout with a **▶ Play** link (`obsidian://open?vault=…&file=lib/…mp3`). The link is only added when audio is bound at render time. | `create.rs:32-145, 617-672` |
| `clip <URL>` | HTML articles go through the pinned uv+Playwright adapter (Defuddle plus a Bob print template). **Direct-PDF URLs are already supported:** the adapter probes `Content-Type` and downloads the PDF unchanged (`kind: "pdf"`). Default `ref_type` is `blogs`. URLs are deduped against ref-note `source_url` and queued xlib markers. The stem comes from the URL slug. | `clip.rs`, `scripts/web_clip/web_clip_adapter.py:1155-1400` |
| Direct-PDF quirk | The adapter calls `discover_browser()` and fails with `browser` **before** it probes for a PDF. A PDF download never launches a browser, yet it still requires one. | `web_clip_adapter.py` (capture orchestration) |
| Marker stamping | `embed_marker` **appends** to an existing `/Annots` array. Highlights and bob treat the **first** standalone `/Text` annotation on page 1 as the marker. | `stamp.rs:307-372`, `marker.rs` (`read_pdf_marker`) |
| Config | `highlights:` has `pre_scan_hook` (a shell string, run via `sh -c` with inherited stdio), `audio_link_template`, and `audio_library`. The test seam is `BOB_CONFIG_FILE`. | `config/mod.rs:19, 353-362, 494-535`, `hooks.rs:40-77` |
| Vault size guard | `vault_sync` refuses files ≥ 95 MiB. | `vault_sync.rs:31` |
| CLI rules | Every public long option needs a short alias. Options are sorted. A command is never hard-renamed or removed; the old spelling becomes a permanent hidden alias with byte-identical behavior. | `sase/memory/cli_rules.md` |
| Existing caller | The SASE `research-highlights` file hook runs `bob highlights create --include-id <report.md>`. | chezmoi `dot_config/sase/sase.yml:17-19` |

### 1.2 sase-listen (`sase-org/sase-listen` @ `f8154ad`, 2026-10-06)

- **`render SOURCE`** accepts:
  - a narration script;
  - a Markdown file (normalized to a verbatim reading);
  - a local PDF (suffix or `%PDF-` magic);
  - a `kind:path` artifact ref (read through `sase artifact read`);
  - an http(s) article or PDF URL. (`cli/render.py:45-50`, `pipeline.py:720-886`)
- **arXiv** (landed today, `eb05e7c`):
  - Recognized hosts: `arxiv.org`, `www.arxiv.org`, `export.arxiv.org`.
  - Recognized paths: `/abs/<id>`, `/html/<id>`, `/pdf/<id>[.pdf]`, with old- or new-style IDs and
    any version suffix kept.
  - Every form is fetched as `https://arxiv.org/pdf/<id>`. A failed fetch never falls back to the
    abstract page.
  - It's pure string logic in `web/arxiv.py` (46 lines), with 12 positive and 9 negative test
    vectors in `tests/test_arxiv.py`.
- **Editions:** `-e brief|full|verbatim`. `brief` and `full` are Gemini-written and **only valid
  for URL and PDF sources**. For any other source, `load_source` raises exit 2 when
  `edition in {"brief","full"}` (`pipeline.py:780-789`). That includes Markdown files and
  narration scripts.
- **Output modes:**
  - Default: a Rich live checklist on stderr when stderr is a TTY (plain lines otherwise), then a
    summary on stdout.
  - **`--json` disables progress** and prints exactly one JSON object (`docs/cli.md`).
- **`-o, --output PATH`:** after the episode is committed to the library, the MP3 is copied to
  `.tmp-<name>` and then moved into place. This happens **before** the publish stage
  (`pipeline.py:2376-2386`).
- **Publishing:**
  - `should_publish` is `--publish`/`--no-publish` when given. Otherwise it's
    `auto_publish && kind in {research, article}` (`pipeline.py:266-274`).
  - With explicit `--publish` and an unreachable remote host, the episode is queued in the outbox
    and the render **exits non-zero after `-o` has already written the audio**
    (`pipeline.py:2407-2420`).
- **Exit codes:** 0 ok, 1 unexpected, 2 usage, 3 config/credentials, 4 synthesis failed,
  5 quality gate, 6 structural lint, 130 interrupted. Ctrl-C finishes in-flight chunks so they
  stay cached.
- **Episode ID:** `slugify(title)-sha256(source_key)[:6]`. For URLs, `source_key` is
  `url:<canonical>#<edition>`. Library manifests record `source.url`, `source.sha256`, `script.*`,
  `audio.file`, and `created_at`.

### 1.3 Bryan's configuration (chezmoi)

- `dot_config/bob/config.yml` → `highlights: { pre_scan_hook: PATH="$HOME/bin:$PATH" bob_xlib_pull }`.
  It has no listen setting.
- `dot_config/sase-listen/config.yml` → feed host `apollo` (SSH to `apollo` and `apollo-do`),
  `auto_publish: true`, and the Gemini key from `pass`.
- `bob_xlib_pull`, run by cron on the Mac, rsyncs **everything** in athena's and apollo's
  `~/bob/xlib/` (no excludes, `--remove-source-files`). The Mac's scan then moves PDFs and
  same-stem audio to `lib/` and writes `ref/` notes.

### 1.4 Vault and library evidence (athena, read-only)

| Observation | Number |
| --- | --- |
| `lib/` PDFs by type | chat 285, docs 11, blogs 6, **papers 5** |
| Paper refs | All 5 hand-made: short stems (`ea_graph`, `memory_os`, `human_mem_arch`, `log_is_the_agent`, `filesystem_memory`), an ad hoc **`url:`** key (not `source_url`), arXiv `/pdf/` or `/abs/` URLs |
| Other arXiv refs | 31 hand-made `ref/ai/**` notes with `url: https://arxiv.org/...` and no PDF |
| sase-listen library on athena | 17 episodes. **13 are URL renders (all `full`), and only 3 match a vault `url`/`source_url`.** The 10 untracked episodes include 6 for 5 arXiv papers. |
| Duplicate identity | One paper rendered twice: `arxiv.org/pdf/2602.16844` (8.8 min) and `arxiv.org/abs/2602.16844v1` (2.0 min; an abstract-only reading from before today's arXiv fix) |
| Episode size and length | Full editions run 8–14 min. Episodes average 4.3 MB (max 6.7 MB). TTS estimate is $0.11–0.19 per full episode; writer tokens are billed separately. |
| Vault git | `.git` packs total **1.35 GiB**. `*.mp3` is git-tracked (`.gitignore` un-ignores it). 3 MP3s are already in `lib/chat/`. |
| arXiv API | `export.arxiv.org/api/query?id_list=2608.25174` returns title, 4 authors, and `published` 2026-08-25. The PDF is 5.07 MB with Info `/Title` present and no `/Text` annotations. |

---

## 2. Is this a good idea? Critique

**Yes, and it's overdue.** The Highlights loop (PDF → `ref/` note → `^ref` lifecycle task →
annotation sync) is the vault's reading ledger. Listening has quietly become a second reading
channel that bypasses that ledger. The numbers in §1.4 show the leak. Tying the two together
makes each listened article searchable, linkable, and reviewable on the `^ref` cadence. It also
leaves a PDF to highlight later and a durable copy of the audio. The library is per-machine, and
the feed prunes episodes after 90 days or 200 episodes.

**What's wrong or underspecified in the plan as stated:**

1. **"Add `--listen` to `create`" doesn't by itself mean "always tracking."** Every one of the 10
   untracked episodes came from running `sase-listen render` directly. A flag only helps when
   Bryan uses bob as the front door. To make tracking "always," add two backstops:
   - auto-binding of existing episodes;
   - a doctor reconcile report.

   A shell alias helps with habit too (§4.10).
2. **The `<target>` requirement quietly merges two commands.** `create` handles Markdown and
   `clip` handles URLs. Widening `create` without deciding what happens to `clip` would leave two
   overlapping front doors with different defaults (`chat` vs `blogs`). Decide it explicitly
   (A1).
3. **`-e full` isn't a property of sase-listen; it's a property of the target kind.** The literal
   command `sase-listen render <target> -e full` fails for Markdown, which is the input
   `create` exists for. The config has to model this (A3).
4. **"Show the output in full" conflicts with "bob needs a result" unless the contract is
   chosen carefully.** `--json` hides the live checklist, and parsing human output is fragile.
   The `{audio}` output-path contract resolves this cleanly (A5).
5. **"Published to a feed" depends on sase-listen's `auto_publish` and on the episode kind.**
   Plain Markdown episodes (`kind: document`) aren't auto-published. Pass `--publish` explicitly
   in the template (A4).
6. **"Use that PDF" hides several reliability traps:**
   - The marker is appended after existing annotations.
   - A large PDF fails at sync time instead of at create time.
   - An already-stamped PDF would get a second marker.
   - PDF downloads currently require a browser.

   All of these are fixable (§4.4).
7. **arXiv support should go *beyond* sase-listen.** Matching sase-listen's URL recognition is
   the minimum. The ref note also needs a real title, authors, a date, and a short stem. The
   arXiv API provides all of them in one request (§4.3).
8. **Cost to watch: audio in the vault's git history.** At about 5 MB per episode, every listened
   article adds to `.git`, which is already 1.35 GiB. At 2 per day that's about 3.6 GB per year.
   I still recommend copying the audio, because the vault is the only durable, synced home for it.
   But this is the main long-term cost, and it's Bryan's call (§8).

---

## 3. Requirement adjustments (deliberate changes to the request)

> **A1. `create` becomes the single front door, and `clip` becomes a permanent hidden alias.**
> `create` classifies `<TARGET>` and routes it. `bob highlights clip <URL>` keeps working
> forever, identically to `create <URL>`, per `cli_rules.md`. The 2026-10-01 research chose a
> sibling command because URL-only options would double `create`'s help. That cost is now worth
> paying: five target kinds and a cross-cutting `--listen` belong behind one door. Behavior change:
> **direct-PDF URLs default to `papers`, not `blogs`**. `lib/blogs/` contains only web pages
> today.

> **A2. v1 targets = sase-listen's targets, minus `kind:path` artifact refs.**
> - Supported: Markdown, local PDF, http(s) article URL, PDF URL, and arXiv URL.
> - Not supported in v1: refs. They're SASE-internal, and research reports already reach
>   Highlights through the `research-highlights` file hook. Refs would also add bob's first runtime
>   dependency on `sase`, and pandoc needs a real file path for relative images.
> - A ref-shaped target that isn't a file fails with
>   `hint: bob highlights create "$(sase artifact path <ref>)"`.
> - Adding refs later is a 10-line resolver.

> **A3. The edition is per target kind. Markdown uses `markdown_command` and prefers its
> narration script.** URLs and PDFs run `command` (`--edition full`). For a Markdown target, the
> listen command runs `markdown_command` on its sibling `<stem>_narration.md` if one exists. The
> stem rule is the same one discovery uses. Otherwise it runs on the Markdown itself, which
> sase-listen reads verbatim. This avoids rendering a second, worse episode of a research report
> that already has an agent-written narration.

> **A4. The configured template publishes explicitly (`--publish`).** The feed requirement is
> encoded in Bryan's config, not in bob, and not dependent on `auto_publish` or the episode kind.

> **A5. The listen contract is "write the finished audio to `{audio}`."** bob doesn't parse
> stdout, doesn't pass `--json`, doesn't scrape the library, and needs no upstream change.
> sase-listen satisfies the contract with `--output {audio}`. Any other tool can satisfy it with a
> two-line wrapper.

> **A6. "Show the output in full" means the listen command owns the terminal while it runs.**
> - bob inherits stdin, stdout, and stderr, so sase-listen's live checklist, retry countdowns,
>   Ctrl-C behavior, and final summary appear exactly as if Bryan ran it himself.
> - bob frames the section with one dim header line and one footer line. It never captures,
>   filters, or reflows that output.
> - bob's own summary prints afterward.

> **A7. A listen failure keeps the PDF; Ctrl-C keeps nothing.** If the listen command fails, bob
> installs the captured PDF (tracking is the point), exits 1, and says how to retry audio only.
> Ctrl-C means "stop": bob writes nothing and exits 130. sase-listen's chunk cache makes the re-run
> cheap.

> **A8. `-L` on an already-captured reference attaches audio instead of refusing.** If the
> source URL already has a ref note, or the planned PDF is already queued or archived, `-L` runs
> the listen command and drops the audio in the late-pair slot `xlib/<rel>.mp3`. `scan` already
> attaches that audio to the note. Without `-L`, today's refusals stay.

> **A9. "Highlights note" means the page-1 marker plus the ref note that `scan` writes.**
> - `create` still never writes `ref/`. The Mac's 15-minute scan does, which is the same
>   boundary as today.
> - Imported PDFs are copied into `xlib/<type>/<stem>.pdf`, with the marker inserted **first**.
>   The original is never modified.
> - Imports ≥ 95 MiB are refused (the vault-sync limit), and imports ≥ 50 MiB get a warning.

> **A10. arXiv gets first-class metadata, not just URL recognition.**
> - Title, authors, and `published` come from the arXiv API (fail-soft).
> - `source_url` is the human-facing `https://arxiv.org/abs/<id>`.
> - `ref_type` is `papers`.
> - The stem is a short form of the title (`ea_graph`-style).
> - Dedupe uses the arXiv ID and ignores the version.

> **A11. Dedupe also reads the legacy `url:` key.** Highlights refs with a `source_pdf` block a
> recapture. Hand-made notes without a PDF (the 31 in `ref/ai/**`) only produce a warning
> ("also referenced by …").

> **A12. Default status stays `ready`.** Listening isn't reading. Setting `next` would push every
> listened item into the Next lane (sticky lanes, soft cap 15). Use `-s` when it's wanted.

> **A13. Backstops for "always."**
> - `create <url>` without `-L` auto-binds an existing library episode whose `source.url`
>   matches. `--no-audio` opts out.
> - `bob highlights doctor` reports article episodes with no ref note and prints
>   `bob highlights create <url>` lines.
> - Optional: a chezmoi alias `listen='bob highlights create --listen'`, so the short habit goes
>   through bob.

---

## 4. Design

### 4.1 Command surface

Options are sorted, every long option has a short alias, and existing spellings are unchanged.
`-L` is free (`-l` is `--lib-dir`).

```text
bob highlights create [OPTIONS] <TARGET>

Turn TARGET into a Highlights-ready PDF in the intake queue; optionally narrate it as a podcast episode

Arguments:
  <TARGET>  Markdown file, PDF file, or http(s) URL (web article, PDF, or arXiv paper)

Options:
  -a, --audio <PATH>      Pair this audio file instead of discovering one
  -A, --author <NAME>     Override the extracted author
  -b, --bob-dir <PATH>    Bob vault root; defaults to BOB_DIR or ~/bob
  -d, --dry-run           Print the plan, marker, and listen command; write nothing and run no listen command
  -f, --force             Overwrite an existing intake PDF (never a library PDF)
  -H, --html <FILE>       URL targets: use a page saved from a browser; `-` reads stdin
  -i, --include-id        Markdown targets: embed the file stem as marker id (other targets always do)
  -L, --listen            Also narrate TARGET with highlights.listen and pair the episode audio with the PDF
  -l, --lib-dir <PATH>    Highlights PDF library; defaults to BOB_HIGHLIGHTS_LIB_DIR or lib
  -N, --name <STEM>       Output filename stem and marker id [default: derived from TARGET]
  -n, --no-audio          Skip audio discovery and pairing
  -o, --output <PDF>      Complete path for the generated PDF, including the .pdf filename
  -P, --parent <NOTE>     Bare Obsidian note target for the marker parent [default: obsidian_ref]
  -p, --published <DATE>  Override the extracted publish date (YYYY-MM-DD)
  -r, --ref-dir <PATH>    Reference note output directory; defaults to BOB_HIGHLIGHTS_REF_DIR or ref
  -s, --status <STATUS>   Lifecycle status embedded in the marker [default: ready]
  -T, --title <TITLE>     Override the extracted title
  -t, --ref-type <DIR>    Library subdirectory [default: chat for Markdown, blogs for web pages, papers for PDFs and arXiv]
  -x, --xlib-dir <PATH>   Highlights PDF intake directory; defaults to BOB_HIGHLIGHTS_XLIB_DIR or xlib
```

Clap constraints and validation:

- `--listen` conflicts with `--audio` and `--no-audio`. `--output` conflicts with `--ref-type`
  and `--name`, as today.
- Rules that depend on the target kind are checked in the planner, with one-line errors. For
  example, `--html applies to URL targets` and `--include-id applies to Markdown targets`.
- The positional keeps its position, so the `research-highlights` hook
  (`create --include-id <report.md>`) doesn't change.
- `completion/kinds.rs`: the arg id changes from `md-file` to `target`, and completion offers
  `*.md` and `*.pdf` files.

### 4.2 Target resolution: one classifier, five kinds

The rules are checked in order, and the first match wins. Every kind flows into the same planner,
dedupe, installer, and summary.

| Kind | Detected by | PDF acquisition | Default `ref_type` | Default stem | `source_url` | Listen `{target}` |
| --- | --- | --- | --- | --- | --- | --- |
| **arXiv** | `^https?://` and the ported `arxiv_paper_id()` | adapter direct-PDF fetch of `https://arxiv.org/pdf/<id>` plus arXiv API metadata | `papers` | short title | `https://arxiv.org/abs/<id>` | the cleaned URL as typed (sase-listen canonicalizes identically) |
| **Web URL** | `^https?://` | existing clip adapter; it decides HTML (reader template) vs PDF (download unchanged) | `blogs` (HTML) / `papers` (PDF) | URL slug, then title | cleaned URL | cleaned URL |
| **Local PDF** | existing file with `.pdf` or `%PDF-` in the first 1 KiB | copy to scratch, never touching the original | `papers` | file stem, snake_cased | none (v1) | absolute path to the **original** PDF (sase-listen caches by content hash) |
| **Markdown** | existing `.md` file | pandoc/XeLaTeX (unchanged), rendered in scratch | `chat` | file stem | none | sibling `<stem>_narration.md` if present, else the `.md` |
| *(refused)* narration script | `*_narration.md` | — | — | — | — | hint: pass the report; its narration is discovered |
| *(refused)* artifact ref | `^[A-Za-z_][\w+.-]*:.+` and not an existing path | — | — | — | — | hint: `"$(sase artifact path <ref>)"` |

### 4.3 arXiv: match sase-listen, then go further

- **Recognition.** Port `web/arxiv.py` exactly, as a new `highlights_ref/arxiv.rs` with no new
  crates. Copy sase-listen's 21 test vectors into a conformance table in
  `docs/highlights-create.md`. This follows the "contract with conformance vectors" precedent
  from `c2aec57`, so the two tools can't drift apart unnoticed.
- **Fetch.** Go through the adapter's direct-PDF path with the browser requirement removed (§4.4).
  arXiv never needs Chromium.
- **Metadata (fail-soft).**
  - Add an optional `arxiv_id` request field to the adapter, as an additive protocol v1 change.
    The adapter queries `export.arxiv.org/api/query?id_list=<id>` and fills `title`, `author`, and
    `published`, with `metadata_sources: arxiv`.
  - Author format: the first three names, then `et al.`
  - If the API is unavailable, fall back to the PDF Info `/Title`, then a humanized stem, with a
    warning.
  - `-T/-A/-p` overrides still win.
- **Stem.**
  - Start from the part of the title before the colon, when there is one.
  - Convert it to snake_case and drop a leading article.
  - Cap it at 5 words and trim trailing stopwords.
  - Examples: "EA-Graph: Artifact-Anchored …" → `ea_graph`, "The Log is the Agent" →
    `log_is_the_agent`, "Model-Based Agentic Software Engineering" →
    `model_based_agentic_software_engineering`.
  - `-N` overrides it.
- **Dedupe key.** `arxiv:<id-without-version>`, compared against the `source_url` *and* legacy
  `url:` values of refs and queued markers. The two renders of 2602.16844 show why the version has
  to be ignored.

### 4.4 Local PDFs and PDF URLs: "use that PDF," safely

1. **Never touch the original.** Copy it into a 0700 scratch dir, stamp the copy, and install it
   atomically at the planned target.
2. **Insert the marker first.** Change `embed_marker` from `push` to `insert(0, …)`.
   - This doesn't change anything for rendered PDFs, which have no prior `/Text` notes.
   - It fixes imported PDFs that already carry a sticky note. Today, that note would win as "the
     marker."
3. **Refuse already-stamped PDFs.** If page 1 already has a standalone note that parses as a
   marker, the error is: `already a Highlights PDF (marker found); use bob highlights sync`.
4. **Refuse PDFs that already live in `lib/` or `xlib/`.** The hint points to `sync` or `scan`. With
   `-L`, attach audio instead (A8).
5. **Size guard at create time.** Refuse ≥ 95 MiB (`vault_sync::LARGE_FILE_LIMIT_BYTES`) and warn
   at ≥ 50 MiB. Don't wait for vault sync to fail later.
6. **Handle encrypted or unparseable PDFs.** If lopdf fails to load the file, fail closed with
   `hint: qpdf --decrypt in.pdf out.pdf`.
7. **Probe PDFs before discovering a browser.** In the adapter, move `discover_browser()` after
   `_probe_pdf`. Direct-PDF responses report `browser: none`. This fixes "PDF URL fails with
   `browser`" on hosts without Chrome. apollo has no Chrome, per the 2026-10-01 research.

### 4.5 The listen contract

**Config.** This lives in Bryan's chezmoi `dot_config/bob/config.yml`. It's an argv list with no
shell, so URL metacharacters (`&`, `?`, `;`) can't break or inject anything.

```yaml
highlights:
  pre_scan_hook: PATH="$HOME/bin:$PATH" bob_xlib_pull
  # `bob highlights create --listen` narrates the target with one of these argv
  # templates (run directly, no shell) and pairs the audio it writes with the PDF.
  #   {target}  URL, PDF, or Markdown/narration script to narrate
  #   {audio}   file the command must write the finished episode audio to
  # The command's own output streams to the terminal unchanged.
  listen:
    command: [sase-listen, render, "{target}", --edition, full, --publish, --output, "{audio}"]
    # sase-listen writes brief/full editions only for URLs and PDFs; Markdown
    # (or its sibling _narration.md) is read as written. Falls back to `command`.
    markdown_command: [sase-listen, render, "{target}", --publish, --output, "{audio}"]
```

**Validation** happens at config load. Errors are named with their config path, matching the
existing `ConfigError::Invalid` style.

- Each template is a non-empty list of strings, and `argv[0]` contains no placeholder.
- `{target}` appears at least once. `{audio}` appears exactly once and may be embedded, as in
  `--output={audio}`.
- Unknown `{…}` tokens are errors, which catches typos like `{url}`.
- A leading `~` in `argv[0]` is expanded.
- There's no built-in default command, because bob shouldn't depend on sase-listen. If `--listen`
  is passed without config, bob prints an error plus this snippet:

  ```text
  bob highlights: error: --listen needs highlights.listen.command in ~/.config/bob/config.yml
  hint: for sase-listen, add:
    highlights:
      listen:
        command: [sase-listen, render, "{target}", --edition, full, --publish, --output, "{audio}"]
  ```

**Running the command** (`highlights_ref/listen.rs`):

- **Spawn.** Substitute each placeholder into whole argv elements, then call
  `Command::new(argv0).args(rest)`. stdin, stdout, and stderr are all `Stdio::inherit()`.
  - The command runs in the current working directory. `{target}` and `{audio}` are always
    absolute.
  - The child gets the extra environment variable `BOB_HIGHLIGHTS_LISTEN=1`. A future sase-listen
    hook can use it to avoid recursion.
- **Ctrl-C, with `system(3)` semantics.**
  - bob ignores SIGINT and SIGQUIT while it waits. Use `libc`, which is already a dependency.
  - The child resets both signals to `SIG_DFL` in `pre_exec`. If it inherited `SIG_IGN`, Python
    would skip installing its KeyboardInterrupt handler and sase-listen's graceful Ctrl-C would be
    lost.
  - As a result, sase-listen gets the terminal's SIGINT, finishes its in-flight chunks, and exits
    130. bob then exits 130 itself and doesn't die halfway through.
- **`{audio}`.** It's `<scratch>/<stem>.mp3`, where the scratch dir is a 0700 dir outside `xlib/`
  (`ClipWorkdir`-style). That way `bob_xlib_pull` can never pick up a partial file.
- **Accepting the audio.** The file must exist, be at least 1 KiB, and pass a magic sniff:
  - MP3: `ID3` or an MPEG frame sync;
  - M4A: `ftyp`;
  - Ogg/Opus: `OggS`.

  An error page written as `.mp3` is rejected. Accepted audio then goes through the existing
  `plan_audio_copy_for_source` rules: identical-bytes reuse, `--force` to overwrite, and refusal
  when the `lib/` slot is occupied.
- **Exit-status mapping:**
  - **0 with valid audio:** success.
  - **0 without audio:** contract violation. The message is "listen command exited 0 but wrote no
    audio to {audio}".
  - **130 or SIGINT:** interrupted.
  - **Non-zero with valid audio:** pair the audio and exit 1. This is the "`--publish` failed after
    `--output`" case. sase-listen has already printed its `publish --pending` hint.
  - **Non-zero without audio:** failed.
- **Preflight.** Before any capture, bob confirms `argv[0]` resolves on `PATH`. This uses the same
  helper as `doctor`'s `pre_scan_hook` row. A missing tool fails in milliseconds, before anything
  is written.

**Why this contract** (alternatives in §5):

- `--output` is sase-listen's own, documented, atomic flag. It runs before publishing, so a publish
  failure can't take the audio with it.
- It needs no change to sase-listen and no knowledge of its JSON schema, library layout, or URL
  canonicalization.
- Any TTS tool can meet it.
- If bob ever wants the episode ID or duration, an optional `{result}` placeholder can be added
  later, filled by a future `sase-listen render --json-file FILE`, without breaking existing
  configs.

### 4.6 Stage order and failure semantics

```text
plan ─▶ preflight ─▶ capture* ─▶ listen ─▶ render† ─▶ install (audio, then PDF) ─▶ summary
         (listen exe,   (network;     (minutes,   (Markdown     (atomic; rollback
          dedupe,        fails fast    costs $)    only; Play    audio on PDF
          collisions)    before TTS)               link bound)   failure — existing)
* URL/arXiv/local-PDF kinds   † Markdown renders after listen so the ▶ Play link points at real audio
```

Both files land within milliseconds of each other, so the Mac's 15-minute `bob_xlib_pull` can't
pull one without the other. Late pairing still covers the rare split.

| Where it stops | Written | Exit | What bob says |
| --- | --- | --- | --- |
| Listen not configured, or exe missing | nothing | 1 | error plus config snippet |
| Dedupe: already captured, no `-L` | nothing | 1 | today's clip message plus `hint: add -L to attach audio` |
| Capture fails (bot wall, thin, network, browser) | nothing | 1 | today's clip `hint:` lines |
| Listen interrupted (Ctrl-C) | nothing | 130 | `re-run the same command; sase-listen resumes from its cache` |
| Listen fails, no audio | **PDF** | 1 | `PDF queued; audio failed (listen command exit 4). Re-run with -L to add audio only.` |
| Listen fails after writing audio | **PDF + audio** | 1 | `audio paired; listen command exited 1 after writing it (see its output above)` |
| Listen exits 0, no or invalid audio | **PDF** | 1 | contract-violation message naming the template |
| Audio slot conflict | **PDF** | 1 | existing `target audio already exists …; pass --force` |

**Dry run (`-d`).** It prints the full plan, the marker, the resolved listen argv (with `{audio}`
shown as its scratch path), and the audio destination. It **never runs the listen command**,
because sase-listen's own `--dry-run` spends Gemini writer tokens.

### 4.7 Attach mode (A8): listening to something you already captured

With `-L`, a dedupe or collision hit stops being a refusal:

- **The URL already has a ref note.** Read its `source_pdf` (`lib/<rel>.pdf`) and put the audio at
  `xlib/<rel>.mp3`. On the next scan, it moves the audio, adds `audio: "[[lib/<rel>.mp3]]"`, and
  inserts the `![[…]]` embed after the `^ref` line. This is existing late-pair behavior
  (`docs/highlights-ref-sync.md` "Companion audio on scan").
- **The PDF is already queued in `xlib/`.** Put the audio beside it.
- **The note already has `audio`.** Still run the listen command, which re-publishes. That matters
  when the feed pruned the episode after 90 days. Pair nothing, and report `audio: kept [[…]]`.

The same rule also enables backfill for the 5 hand-made paper refs, which already have PDFs:
`bob highlights create https://arxiv.org/abs/2605.21997 -L` gives `log_is_the_agent` an episode
and an embed.

### 4.8 What it looks like

This transcript is illustrative. The middle block is sase-listen's own output, unmodified. bob's
framing lines go to stderr in dim text, and its summary goes to stdout in the existing
`ok …` / `key: value` style.

```text
$ bob highlights create https://arxiv.org/abs/2608.25174 -L
capturing arxiv.org (arXiv 2608.25174)…
ok captured PDF · 23 pages · 4.8 MB · metadata: arxiv
── listen ─ sase-listen render https://arxiv.org/abs/2608.25174 --edition full --publish --output /tmp/bob-listen-48121/model_based_agentic_software_engineering.mp3
♫ Model-Based Agentic Software Engineering (Full)
  ✓ Fetch article   arxiv.org · 9,812 words                          4s
  ✓ Write script    2,377 words · 8 chapters · 1 attempt            52s
  ✓ Plan episode    31 chunks · about 10 min
  ✓ Synthesize      31/31                                        2m 10s
  ✓ Quality gates   ✓ Master audio   ✓ Save episode   ✓ Publish  apollo
♫ Ready in 3m 21s · 10:12 of audio · ≈$0.13
  ~/.local/share/sase-listen/library/model-based-agentic-software-engineering-full-1c9e2a/…mp3
  Published to apollo — refresh the feed in AntennaPod to download it.
  Copied to /tmp/bob-listen-48121/model_based_agentic_software_engineering.mp3
── end listen ─ exit 0 · 3m 21s
ok created Highlights-ready PDF with audio
pdf: ~/bob/xlib/papers/model_based_agentic_software_engineering.pdf
audio: ~/bob/xlib/papers/model_based_agentic_software_engineering.mp3 (from listen command)
title: Model-Based Agentic Software Engineering
author: James C. Davis, Kelechi Kalu, Huiyun Peng, et al.
published: 2026-08-25
captured: 2026-10-06
source_url: https://arxiv.org/abs/2608.25174
status: ready
parent: obsidian_ref
id: model_based_agentic_software_engineering
pages: 23 · size: 4.8 MB
next: bob highlights scan
```

The ref note that `scan` writes later looks like this:

```markdown
---
status: ready
parent: "[[obsidian_ref]]"
type: "[[ref]]"
ref_type: papers
audio: "[[lib/papers/model_based_agentic_software_engineering.mp3]]"
title: "Model-Based Agentic Software Engineering"
id: model_based_agentic_software_engineering
source_url: "https://arxiv.org/abs/2608.25174"
author: "James C. Davis, Kelechi Kalu, Huiyun Peng, et al."
published: 2026-08-25
captured: 2026-10-06
…
---
# Model-Based Agentic Software Engineering

- [ ] #task #ref [[lib/papers/model_based_agentic_software_engineering.pdf]] #hide ^ref

![[lib/papers/model_based_agentic_software_engineering.mp3]]
```

### 4.9 `doctor`

New rows follow the existing `pre_scan_hook:` row style:

```text
listen command: ok (sase-listen → ~/.local/bin/sase-listen; placeholders {target} {audio})
listen markdown command: ok (sase-listen; no --edition)
listen library: warning — 10 article episodes have no ref note (bob highlights doctor -v lists them)   ← Phase 3
```

When nothing is configured, the row reads `listen command: none (optional)`. It never fails
`doctor`.

### 4.10 Habit backstop (optional, chezmoi)

```sh
alias listen='bob highlights create --listen'   # listen https://arxiv.org/abs/…
```

---

## 5. Alternatives considered

| Alternative | Verdict | Why |
| --- | --- | --- |
| Keep `create` Markdown-only and add `--listen` to both `create` and `clip`; add an `import` for local PDFs | Rejected | Three front doors, two of them carrying `--listen`, and arXiv defaults split across them. The user asked for `create <target>`. |
| A new `bob highlights listen <target>` | Rejected | Listening is an attribute of capturing a reference, not a separate workflow. It would duplicate every capture option. |
| `{result}` JSON contract via a new `sase-listen render --json-file FILE` | Deferred | Exact and rich (episode ID, duration, published), but it needs an upstream change first. `{audio}` is enough for v1, and `{result}` can be added later as an optional placeholder. |
| Run the command with `--json` | Rejected | `--json` disables the live checklist, which violates "show the output in full". |
| Parse sase-listen's human summary (the MP3 path line) | Rejected | That output isn't a contract and would break on any UI polish. |
| Diff the sase-listen library before and after the run | Rejected as the primary channel | Breaks on canonical-URL drift (redirects, `rel=canonical`) and on concurrent agent renders. It's kept only as the *no-`-L`* discovery matcher (A13), where a miss is harmless. |
| Shell-string template like `pre_scan_hook` | Rejected | Interpolated URLs contain `&`, `?`, and `;`. With an argv list, bob never has to quote anything. |
| Built-in `sase-listen` default command | Rejected | The user asked bob not to depend on sase-listen directly. The error plus snippet makes setup a single paste. |
| sase-listen post-render hook that calls bob (covers *every* render) | Deferred (Phase 3, only if the reconcile report shows continued leakage) | It's the strongest "always," but it couples sase-listen to bob and needs a recursion guard (`BOB_HIGHLIGHTS_LISTEN=1` is reserved for this). |
| bob hands sase-listen its captured bytes (`--html {snapshot}`) | Deferred | One fetch, the same content for the PDF and the audio, and bot-walled pages get audio too. But it needs per-kind argv. All 13 URL episodes on athena show that sase-listen fetches ordinary articles fine. |
| All-or-nothing: no PDF if listen fails | Rejected | Tracking is the goal. A queued PDF plus "re-run `-L` to add audio" loses nothing. |
| Link-only: record the episode and don't copy the MP3 into the vault | Considered | Saves about 5 MB of git per episode. But the vault is the only synced, durable home for the audio (the feed prunes, the library is per-host). Revisit if `.git` growth hurts (§8). |
| `--listen[=EDITION]` | Deferred | The edition belongs in config. A per-call override can come later through an `{edition}` placeholder. |
| Default `-s next` when listening | Rejected | It would flood the Next lane. See A12. |

---

## 6. Pre-existing issues found along the way

1. **Temp files land inside `xlib/`, where `bob_xlib_pull` rsyncs everything.**
   - `create` renders `.stem.<pid>.render.pdf` into the target dir, and the atomic writers use
     `.<name>.<pid>.tmp`.
   - If the Mac's cron runs during that window (sub-second to about a second), rsync can move a
     partial dotfile. Scan would treat the `.render.pdf` as an intake PDF, and bob's own install
     would fail with ENOENT.
   - The probability per create is low, but it's real for agent-run creates on athena.
   - Fix: render into the scratch dir, which this design does anyway. Optionally add
     `--exclude='.*'` to `bob_xlib_pull`'s rsync.
2. **The marker is appended, not prepended** (§4.4.2). This is latent for direct-PDF clips today.
3. **Direct-PDF capture needs a browser it never uses** (§4.4.7).
4. **The `atomic_copy` error text says "image asset"** even when it's copying audio. This is
   cosmetic; fix it while touching the code.

---

## 7. Recommended solution

**Ship `create` as the single front door, then `-L/--listen` as a configurable, terminal-owning
step whose only contract is "write the audio to `{audio}`," then the "always" backstops.** It's
three phases, each shippable on its own.

### Phase 1: One front door (no listening yet)

- Add `highlights_ref/target.rs` (the classifier in §4.2) and `highlights_ref/arxiv.rs` (a port of
  sase-listen's logic plus its conformance vectors).
- Move clip's URL acquisition behind `create`. `clip` becomes a hidden permanent alias.
  - Defaults depend on the target kind: `chat`, `blogs`, or `papers`.
  - URL and PDF kinds always stamp `id`.
- Import local PDFs (§4.4):
  - copy, never mutate;
  - insert the marker first;
  - refuse an existing marker;
  - apply the 95 MiB / 50 MiB size guards;
  - fail closed on decryption problems.
- Adapter changes:
  - probe for a PDF before discovering a browser;
  - fetch arXiv API metadata (additive `arxiv_id` request field);
  - generate short-title stems.
- Dedupe reads legacy `url:`. arXiv dedupes by ID and ignores the version.
- Render Markdown in the scratch dir.
- Update help, `completion/kinds.rs`, and docs: fold `highlights-clip.md` into a new
  `docs/highlights-create.md` that holds the kind table and the arXiv conformance table. Update
  the README command list.

### Phase 2: `-L, --listen`

- `config/mod.rs`: add `RawListen { command, markdown_command }` with the validation in §4.5.
- `listen.rs`:
  - argv substitution;
  - inherited stdio;
  - SIGINT/SIGQUIT discipline (ignore in the parent, `SIG_DFL` in the child's `pre_exec`);
  - the `BOB_HIGHLIGHTS_LISTEN=1` environment variable;
  - the exit-status mapping;
  - audio magic sniffing.
- `create.rs`: the stage order and failure table from §4.6, attach mode from §4.7, the output
  framing from §4.8, and dry-run behavior.
- No-`-L` discovery for URL and PDF kinds: match library `source.url` with bob's dedupe key
  (including arXiv IDs). The newest `created_at` wins. `--no-audio` opts out.
- `doctor` rows from §4.9.
- **chezmoi:** add the `highlights.listen` block from §4.5 to `dot_config/bob/config.yml`.

### Phase 3: Backstops and polish (each optional)

- `doctor` reconcile of untracked article episodes, plus a `-v` listing of
  `bob highlights create <url>` commands.
- A `{snapshot}` hand-off (`--html`) so bot-walled pages get audio from the same bytes as the PDF.
- A listen card in the web-clip masthead when audio is bound.
- Upstream sase-listen: brief/full editions for local Markdown, which would remove the need for
  `markdown_command`; `--json-file` for an optional `{result}`.
- `--source-url` for local PDFs, and auto-detection of arXiv-ID filenames (`2608.25174v1.pdf`).
- The sase-listen post-render hook, only if reconcile shows continued leakage.

### Test plan

- **Classifier:** every row of §4.2, including look-alikes (`notarxiv.org`, a `.md` that's
  actually a PDF, refs vs `C:`-style paths, `*_narration.md`).
- **arXiv:** sase-listen's 12 positive and 9 negative vectors, byte for byte; plus the stem
  heuristic on the 5 real paper titles; plus version-insensitive dedupe.
- **Listen runner:** use a fake listen command through `BOB_CONFIG_FILE` (a shell fixture that
  writes a tiny valid MP3 to its `{audio}` argument). Cover:
  - paths with spaces and URLs with `&` stay single argv elements;
  - exit 0 with audio, exit 0 without audio, a zero-byte file, and an HTML-as-mp3 file;
  - a non-zero exit with audio, exit 4 without audio, and exit 130;
  - a missing executable caught at preflight;
  - an unknown placeholder or missing `{audio}` rejected at config load.
- **Signals:** an integration test sends SIGINT to the process group while the fake command
  sleeps. It asserts the child sees SIGINT, bob exits 130, and nothing was written.
- **Attach mode:** an existing ref note with and without `audio`; a queued xlib PDF; a library
  PDF; and scan late-pairing the dropped audio.
- **Import:** a PDF with an existing sticky note gets our marker first; a PDF with an existing
  marker is refused; the 95 MiB guard works; the original's bytes are unchanged.

### Live verification gate (as in the 2026-10-01 clip work)

On athena, build from the tree and run against a scratch vault (`-b /tmp/…`) with a scratch
`BOB_CONFIG_FILE` whose template omits `--publish`:

- an arXiv URL;
- an HTML article;
- a local PDF;
- a Markdown report with a narration sibling.

Check that the files landed together in xlib and that a `--no-hooks` scan writes `audio:` plus
the embed. Then publish exactly one real episode with the real chezmoi config, and confirm it
arrives in AntennaPod.

---

## 8. Open questions for Bryan

1. **Should `clip` be hidden or stay visible?** I recommend hiding it as a permanent alias, so
   there's one front door. Keeping it visible is harmless but redundant.
2. **Is the vault MP3 growth acceptable?** It's about 5 MB per listened item. At 2 per day that's
   about 3.6 GB per year on a 1.35 GiB repo. If not, the alternatives are link-only mode or moving
   audio out of git (an `lib/**/*.mp3` exclusion plus rsync, or LFS).
3. **What should the default `--parent` be for papers?** Your hand-made paper refs use
   `sase_ref` and `memory_ref`, while the default is `obsidian_ref`. A per-`ref_type` parent
   default in config is possible, but I'd keep `-P`.
4. **Is the listen-failure policy right?** I recommend keeping the PDF and exiting 1 with a retry
   hint. The alternative is all-or-nothing.
