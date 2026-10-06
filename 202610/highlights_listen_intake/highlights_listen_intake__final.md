# `bob highlights create --listen`: one intake gesture for everything you read or hear

- **Date:** 2026-10-06
- **Lead researcher:** consolidated from five independent reports (`__cdx`, `__cld`, `__grk`,
  `__mus`, `__gem`) plus the lead's own verification against source.
- **Question:** Add `--listen` to `bob highlights create`. It should run a configurable command
  (for Bryan, `sase-listen render <target> -e full`) that publishes a podcast episode to the
  AntennaPod feed, alongside the Highlights PDF and its ref note. `create` should accept every
  target `sase-listen render` accepts, including PDF URLs and arXiv. The listen command's output
  should be shown in full. Is this a good idea? What should change? What should be built?
- **Snapshots read:**
  - bob-cli `ce54258`
  - sase-listen `f8154ad`
  - chezmoi `8efdb68`
  - Bryan's vault and sase-listen library on athena, read-only.

---

## 0. Bottom line

1. **Build it. The leak it fixes is real.** On athena, sase-listen rendered 13 URL episodes on
   2026-10-05 and 2026-10-06. All were `full` editions and all were published to the feed. They
   cover 12 distinct sources, and **9 of those 12 have no ref note of their own**. That includes
   5 arXiv papers. One paper was rendered twice: once as `/pdf/2602.16844` (8.8 min), and once
   as `/abs/2602.16844v1` (a 2-minute abstract-only reading from before sase-listen's arXiv fix).
   Bryan is already listening to far more than he tracks.
2. **Make `create` the single front door for every target kind.** The kinds are Markdown, local
   PDF, web article, PDF URL, and arXiv. `clip` becomes a permanent hidden alias that runs the
   same code. Without this, Bryan gets three overlapping commands that each half-support listening.
3. **`-L, --listen` runs a configured command template and gives it the terminal.** The template
   is a one-line string, split like a shell would split it but never run through a shell. Bob
   gets the audio back through one contract: *"write the finished audio to `{audio}`."*
   sase-listen already meets it with `--output`, which writes the MP3 atomically *before* it
   publishes. Bob therefore never parses output, never passes `--json`, never scrapes the
   library, and needs **no upstream change**.
4. **The command must vary by target kind.** `sase-listen render <file.md> -e full` exits 2.
   Generated editions exist only for URLs and PDFs. So the literal requested command breaks
   `create`'s original Markdown use case. Two config keys handle this: `listen_command`, and an
   optional `listen_markdown_command`.
5. **Ref notes keep coming from `scan`. This is the most important correction to the request.**
   The Mac is the single writer of `ref/` notes, fed by the `xlib/` bridge. "Tracked" at create
   time means a marker-stamped PDF (plus MP3) queued in `xlib/`. The ref note appears on the
   Mac's next scan, which runs at most 15 minutes later while the Mac is awake.
6. **Reliability rules:**
   - Capture fails fast, before any money is spent.
   - If the listen step fails, Bob keeps the PDF and exits 1 with a one-line retry.
   - Ctrl-C writes nothing and exits 130.
   - Re-running `-L` on an already-captured source *attaches* audio instead of refusing.
   - `--dry-run` never runs the listen command, because sase-listen's own `--dry-run` still
     spends Gemini writer tokens.

The full recommended solution is in §8.

---

## 1. What exists today (verified)

### 1.1 bob-cli

| Fact | Evidence |
| --- | --- |
| `create` accepts only an existing `.md` file. It renders with pandoc and XeLaTeX, stamps a page-1 `/Text` marker, and installs atomically. The default target is `xlib/chat/<stem>.pdf`. `create` never writes `ref/`. | `create.rs:21` (`DEFAULT_REF_TYPE = "chat"`), `:519` (`validate_markdown_path`); `docs/highlights-ref-sync.md` |
| Companion audio discovery checks, in order: `--audio`, then frontmatter `audio.episode_id`, then the sibling `<stem>_narration.md` hash matched against sase-listen library manifests, then same-stem audio. The copy lands beside the PDF: identical bytes are reused, different bytes need `--force`, and an occupied `lib/` slot is refused. | `docs/highlights-ref-sync.md` "Listen cards in PDFs" |
| **Late pairing already exists.** If audio is waiting in `xlib/<rel>` while `lib/<rel>.pdf` already exists, scan moves the audio there and adds `audio:` plus a `![[…]]` embed to the ref note. The note's `audio` field comes from the companion file, **never from a marker key**. | `docs/highlights-ref-sync.md` "Companion audio on scan" |
| `clip <URL>` has two paths. HTML goes through the pinned uv/Playwright/Defuddle adapter. Direct-PDF URLs are downloaded unchanged. Default `ref_type` is `blogs`, URLs are deduped by `source_url`, and the marker always includes `id`. | `clip.rs:31`; `docs/highlights-clip.md` |
| The adapter detects a PDF only by `application/pdf`. sase-listen also accepts `application/x-pdf`, and octet-stream or missing types when the first 1 KiB contains `%PDF-`. | `web_clip_adapter.py:1202-1208` vs sase-listen `web/fetch.py:16-43` |
| The adapter calls `discover_browser()` and fails **before** it probes for a PDF. A PDF download that never uses a browser still requires one. | `web_clip_adapter.py:1332-1344` |
| `embed_marker` **appends** to `/Annots`, but readers treat the **first** standalone page-1 `/Text` note as the marker. An imported PDF that already has a sticky note would get the wrong marker. | `stamp.rs:307-362`, `marker.rs:4-34` |
| Markdown renders into `.<stem>.<pid>.render.pdf` **inside the target directory** (`xlib/…`). `bob_xlib_pull` rsyncs `xlib/` with no excludes. | `create.rs:600-611`; chezmoi `home/bin/executable_bob_xlib_pull:177` |
| The only `obsidian://` link Bob puts in a PDF is the listen card's ▶ Play button, which points at audio. **No PDF links to its ref note today.** The ref note links to the PDF through its `^ref` task. | `create.rs:26`; grep of `highlights_ref/` |
| Command-string config precedent: `pre_scan_hook` and `gkeep.token_command` run via `sh -c`. Neither interpolates user data. | `hooks.rs:55`, `gkeep/config.rs:218` |
| The crate has no HTTP client (`reqwest`/`ureq`) and no shell-words crate. `libc` is present. | `Cargo.toml` |
| An existing caller depends on the positional argument: the SASE `research-highlights` hook runs `bob highlights create --include-id <report.md>`. | chezmoi `dot_config/sase/sase.yml:19` |
| CLI rules: every public long option needs a short alias, and options stay sorted. A command is never renamed or removed; the old name becomes a permanent hidden alias with byte-identical behavior. | `sase/memory/cli_rules.md` |

### 1.2 The intake bridge

athena and apollo each queue PDFs in a gitignored `~/bob/xlib/`. On the MacBook, a 15-minute
cron runs `bob highlights scan`. Its pre-scan hook `bob_xlib_pull` drains both hosts with
`rsync -a --remove-source-files --ignore-existing`. Scan then moves PDFs and same-stem audio into
`lib/` and writes `ref/` notes, which reach the other machines through vault git
(`docs/vault-git-sync.md` "Highlights bridge").

### 1.3 sase-listen `render`

| Fact | Evidence |
| --- | --- |
| `SOURCE` can be a narration script, a Markdown file, a local PDF (by suffix or `%PDF-` magic), a `kind:path` artifact ref, or an http(s) article or PDF URL. | `cli/render.py:44-50`, `pipeline.py:720-800` |
| **`-e brief`/`full` exits 2 (USAGE) for anything that is not a URL or PDF**, including Markdown and narration scripts. | `pipeline.py:780-789` |
| `full` is an AI-written **adaptation** with a ~2,400-word budget. It is not a transcription. `verbatim` is a deterministic reading that omits code, tables, math, and references. | `writer/author.py`, `docs/web-articles.md` |
| arXiv support is pure string logic (`web/arxiv.py`, 46 lines). It recognizes the hosts `arxiv.org`, `www.`, and `export.`; the paths `/abs/`, `/html/`, and `/pdf/<id>[.pdf]`; and both old- and new-style IDs, keeping any version suffix. Every form is fetched as `https://arxiv.org/pdf/<id>`, with no fallback to the abstract page. The rewrite is skipped when `--html` is given. | `web/arxiv.py`, `web/store.py:208-236`, `tests/test_arxiv.py` |
| **Publishing rule.** `--publish`/`--no-publish` win when given. Otherwise the episode is published only when `feed.auto_publish` is set **and** its kind is `research` or `article`. Generated URL/PDF editions are `kind: article`. Plain Markdown is not. | `pipeline.py:266-274`, `writer/author.py:78` |
| **Publish failures.** With auto-publish, a failure is only a warning, and a remote failure is also queued, and the render still exits 0. With explicit `--publish`, the failure is queued for a remote host and then **raised**, so the exit is non-zero. | `pipeline.py:2394-2430` |
| **`-o/--output`** copies the MP3 through `.tmp-<name>` and a rename, right after the library commit and **before** publishing. | `pipeline.py:2376-2386` |
| **`--dry-run` still runs `load_source`, including the WRITE stage**, before it returns the plan. That spends Gemini writer tokens unless the script is already cached. | `pipeline.py:2103-2126`, `:642-660` |
| `--json` turns off the live checklist and prints a single object. | `docs/cli.md` |
| Exit codes: 0 ok, 1 unexpected, 2 usage, 3 config, 4 synthesis, 5 quality gate, 6 lint, 130 interrupted. On Ctrl-C, chunks already in flight finish and stay cached. | `errors.py:9-16`, `docs/cli.md` |
| The feed keeps 90 days or 200 episodes (`feed.retention_days`, `feed.max_episodes`). The library lives on each host separately. | `docs/podcast-feed.md:98-103` |
| The URL episode ID is `slug(title)-sha256("url:<canonical>#<edition>")[:6]`. A local PDF is keyed by its content hash (`pdf:<sha>`). | `library.py:37-42`, `pipeline.py:790-800` |

### 1.4 Bryan's configuration and vault

- chezmoi `home/dot_config/bob/config.yml` has a `highlights:` section containing only
  `pre_scan_hook: PATH="$HOME/bin:$PATH" bob_xlib_pull`. There is no listen setting yet.
- chezmoi `home/dot_config/sase-listen/config.yml` sets `feed.host: apollo` with
  `host_ssh: [apollo, apollo-do]`, `auto_publish: true`, and a `pass`-managed key and token.
  **No sase-listen config change is needed.**
- `lib/` contains `chat` 285 PDFs and 3 MP3s, `docs` 11, `blogs` 6, and `papers` 5. All 5 paper
  refs were made by hand, with short title stems such as `ea_graph` and `log_is_the_agent`, and
  most use a legacy `url:` key. The vault `.gitignore` un-ignores `*.mp3`, so **audio in `lib/`
  is git-tracked**. cld measured the vault `.git` at about 1.35 GiB. Episodes average about
  4.3 MB, and full editions run 8–14 minutes.

---

## 2. Where the five reports disagreed, and the resolution

| Question | Positions | Resolution (with evidence) |
| --- | --- | --- |
| Does `render <md> -e full` work? | grk: "harmless, ignored". cdx, cld: exits 2. | **It exits 2** (`pipeline.py:780`). Markdown needs its own template. |
| Does bare `render <url> -e full` publish? | mus: no (auto_publish defaults false). gem: yes unless `--no-publish`. grk: yes via Bryan's `auto_publish: true`. cdx, cld: depends on the kind. | **With Bryan's config, URL/PDF `full` editions already auto-publish (kind `article`); Markdown does not.** Auto-publish failures still exit 0. Put **`--publish` in the template** so publishing also covers Markdown and a failed publish is a non-zero exit. |
| Should Bob's `--dry-run` forward `--dry-run` to sase-listen? | mus, gem: yes, as a free cost preview. cdx, cld, grk: no. | **No.** sase-listen's dry-run runs the writer (`pipeline.py:2103-2126`). Bob's dry-run prints the resolved argv and never spawns it. |
| Who writes the ref note, and when? | cdx: Bob writes it synchronously, before listening, and later migrates links on intake. All others: `scan`. | **`scan`.** The Mac is the single `ref/` writer. A note written on athena would race that scan, point `^ref` at a PDF that is not in `lib/` yet, and need new link-migration machinery. "Tracked" at create time = a marker-stamped PDF queued in `xlib/`. |
| Where do HTML article URLs go? | grk, mus: reject on `create` and point to `clip`. cld, cdx, gem: `create` accepts them. | **`create` accepts them, through clip's existing pipeline.** Bryan asked for parity, and most of what he listens to is web articles (7 of 12 sources). |
| What happens to `clip`? | cld: permanent hidden alias. cdx: stays visible, shares code. grk, gem: stays and also gets `--listen`. | **Hidden alias** (cli_rules). The short options of the two commands combine with no collisions (§5.1). This is flagged for Bryan as Q1. |
| How does Bob get the audio? | gem: scan the library for the newest manifest. mus: `-o` plus a `--dry-run --json` preflight. cld, grk: an `{audio}`/`{output}` path contract. cdx: hook only, plus an optional result file. | **The `{audio}` path contract.** It is atomic, written before publish, works with any TTS tool, and needs no parsing. |
| What shape should the config take? | gem: `sh -c` string (allows injection through URLs). mus: Bob composes sase-listen flags from `listen_edition`/`listen_publish` keys (that *is* depending on sase-listen). cld, cdx: YAML argv list. grk: whitespace-split string. cdx: a wrapper script in chezmoi. | **A one-line string with placeholders, split shell-style but never executed by a shell.** It matches the readability of Bryan's existing hooks without the injection risk. A YAML list is also accepted. A wrapper script stays possible, but nothing requires one. |
| Order of stages? | cld, gem: listen, then install. cdx: install, then listen. grk: listen, then install, keeping nothing on failure. | **Capture to scratch, then listen, then install audio and PDF together.** If the listen step fails, keep the PDF and exit 1. On Ctrl-C, write nothing (§5.6). |
| `--listen` with `--no-audio`? | Four reports: they conflict. cdx: independent flags. | **Independent.** `-L -n` means "publish the episode but keep the MP3 out of the vault". This is the storage opt-out, with no new flag. `--listen` still conflicts with `--audio`. |
| arXiv filename stem? | grk, cdx: the ID (`2608_25174`, `arxiv_2602_16844v2`). cld: a short title stem. | **A short title stem** (`model_based_agentic_software_engineering`), matching Bryan's hand-made paper refs. The ID is the fallback. Dedupe goes by arXiv ID. |
| How should the arXiv PDF be fetched? | grk: a new native Rust GET. cld: the adapter's direct-PDF path. gem: copy sase-listen's source cache. | **The adapter's direct-PDF path**, which already has private-host and redirect checks, so no HTTP crate is needed. Never read sase-listen's `sources/` directory, because that is coupling to its internal layout. |
| `kind:path` artifact refs? | cdx: a configurable artifact reader. Others: refuse. | **Refuse in v1, with a hint.** Research reports already reach Highlights through the `research-highlights` hook. |
| Should audio go into the vault (git)? | cld: yes, but flags the growth. cdx: not automatically. Others: yes, without discussing cost. | **Yes by default**, because the feed prunes after 90 days and the library is per-host. `-L -n` opts out. Growth is flagged for Bryan as Q2. |

---

## 3. Is this a good idea?

**Yes.** The Highlights loop is the vault's reading ledger: a PDF, then a `ref/` note, then a
`^ref` task, then synced annotations. Listening has become a second reading channel that
bypasses that ledger. §0 shows the numbers. One gesture that captures and narrates makes every
listened source searchable, linkable, reviewable on the `^ref` cadence, and ready to highlight
later. The architecture favors this: sase-listen owns fetching, writing, TTS, and the feed, and
Bob owns intake, markers, and audio-to-note binding. The integration is thin glue between two
mature halves.

**Weak spots in the plan as stated:**

1. **The literal command breaks Markdown.** See §2, row 1.
2. **"Ref note alongside the PDF" puts the boundary in the wrong place.** `create` and `clip`
   never write `ref/`, and the Mac scan does. Also, *no PDF links to its ref note today*. The ref
   note's `^ref` task links to the PDF. If Bryan wants a clickable PDF → note link, that is new
   work (Q3). The "Highlights note" that create *does* write is the page-1 marker.
3. **Widening `<target>` silently merges `create` and `clip`.** Leaving two front doors with
   different defaults (`chat` vs `blogs`) and different `--listen` support would be confusing.
   This needs an explicit decision.
4. **"Show the output in full" conflicts with "Bob needs a result"** unless the contract is
   chosen carefully. `--json` hides the checklist, and scraping human output is fragile. The
   `{audio}` path contract resolves this.
5. **"Use that PDF" hides several traps:**
   - The marker is appended instead of placed first.
   - An already-stamped PDF would get a second marker.
   - PDF URLs need a browser they never use.
   - PDFs of 95 MiB or more fail later, at vault sync.
   - The detection gaps with sase-listen (§1.1).
6. **A flag alone does not mean "always tracking."** Every one of the 9 untracked sources came
   from running `sase-listen render` directly. The flag needs backstops (§5.8).
7. **Words matter.** sase-listen produces narration, which is text-to-speech. "Transcription" is
   speech-to-text. Help text and notes should say **"AI audio edition"**, and `full` is an
   *adaptation*.
8. **Every `--listen` costs money and minutes.** A full edition is about 3 minutes of
   wall-clock time and roughly $0.11–0.19 of TTS, plus writer tokens. It has to stay opt-in and
   be safe to retry, which sase-listen's chunk and script caches make cheap.

---

## 4. Requirement adjustments (deliberate changes to the request)

> **A1. `create` is the single front door, and `clip` becomes a permanent hidden alias.**
> `create` classifies `<TARGET>` and routes it. `clip <URL>` keeps working forever, byte-for-byte
> identical to `create <URL>`. Direct-PDF URLs now default to `papers` instead of `blogs`. This
> deliberately reverses the 2026-10-01 sibling-command choice. That choice was right for a single
> new target kind. With five kinds and a flag that applies to all of them, one door is simpler.

> **A2. "Same targets as `sase-listen render`" means Markdown, local PDF, web article URL, PDF
> URL, and arXiv URL.** `kind:path` refs and bare narration scripts are refused with hints.
> There is no bare `arxiv:<id>` shorthand, because sase-listen does not have one either.

> **A3. The listen command is chosen per target kind.** `listen_command` serves URL and PDF
> kinds. The optional `listen_markdown_command` serves Markdown, which sase-listen reads as
> written. A Markdown report with a sibling `<stem>_narration.md` is narrated from that script,
> using the same stem rule as discovery.

> **A4. Bob does not write `ref/`.** Create time leaves a marker-stamped PDF, plus MP3 when there
> is one, in `xlib/<type>/`. Scan writes the note, with `audio:` and the player embed. The
> "Highlights note" means the page-1 marker.

> **A5. Publishing is explicit, but it lives in Bryan's template, not in Bob.** Bob has no
> `--publish` flag and no default command. Without configuration, `--listen` fails with a snippet
> Bryan can paste.

> **A6. "Shown in full" means the listen command owns the terminal.** Bob inherits stdin,
> stdout, and stderr. It frames the block with one dim header and one footer, and never
> captures, prefixes, or reflows anything in between.

> **A7. A listen failure keeps the PDF. Ctrl-C keeps nothing.** Re-running with `-L` attaches
> audio to what was already captured.

> **A8. arXiv gets first-class metadata, not just URL recognition.**
> - Title, authors, and published date come from the arXiv API. This is fail-soft: if the API is
>   unavailable, Bob falls back to the PDF's Info title.
> - `source_url` is the human-facing `https://arxiv.org/abs/<id>`.
> - `ref_type` is `papers`.
> - Dedupe uses the version-less ID, and also checks the legacy `url:` key.

> **A9. Listening is not reading.** The default status stays `ready`. `--listen` never touches
> `^ref` state. Setting `next` would flood the sticky Next lane.

> **A10. Audio is paired into the vault by default. `-L -n` publishes without pairing.**

---

## 5. Design

### 5.1 Command surface

The existing `create` and `clip` options combine with no short-alias collisions. Help keeps
clip's current order: alphabetical by short option, with uppercase first.

```text
bob highlights create [OPTIONS] <TARGET>

Turn TARGET into a Highlights-ready PDF in the intake queue; with -L, also narrate it as a
podcast episode and pair the audio with the PDF.

Arguments:
  <TARGET>  Markdown file, PDF file, or http(s) URL (web article, PDF, or arXiv paper)

Options:
  -A, --author <NAME>     Override the extracted author
  -a, --audio <PATH>      Pair this audio file instead of discovering one
  -b, --bob-dir <PATH>    Bob vault root; defaults to BOB_DIR or ~/bob
  -d, --dry-run           Print the plan, marker, and listen command; write nothing, run nothing
  -f, --force             Overwrite an existing intake PDF/audio (never a library PDF)
  -H, --html <FILE>       URL targets: use a page saved from a browser
  -i, --include-id        Markdown targets: embed the file stem as marker id (others always do)
  -L, --listen            Narrate TARGET with highlights.listen_command (an AI audio edition,
                          published by that command) and pair the audio with the PDF
  -l, --lib-dir <PATH>    Highlights PDF library
  -N, --name <STEM>       Output filename stem and marker id [default: derived from TARGET]
  -n, --no-audio          Don't pair audio with the PDF (with -L the episode is still published)
  -o, --output <PDF>      Complete path for the PDF, including the .pdf filename
  -P, --parent <NOTE>     Bare Obsidian note target for the marker parent [default: obsidian_ref]
  -p, --published <DATE>  Override the extracted publish date (YYYY-MM-DD)
  -r, --ref-dir <PATH>    Reference note output directory
  -s, --status <STATUS>   Lifecycle status embedded in the marker [default: ready]
  -T, --title <TITLE>     Override the extracted title
  -t, --ref-type <DIR>    Library subdirectory [default: chat for Markdown, blogs for web pages,
                          papers for PDFs and arXiv]
  -x, --xlib-dir <PATH>   Highlights PDF intake directory
```

Constraints:

- `--listen` conflicts with `--audio`.
- `--output` conflicts with `--ref-type` and `--name`, as today.
- Rules that depend on the target kind are planner errors that fit on one line, for example
  "`--html` applies to URL targets" and "`--include-id` applies to Markdown targets".
- `--ref-type` loses its clap `default_value`, because the default now depends on the target
  kind.
- The positional argument keeps its place, so the `research-highlights` hook keeps working
  unchanged.
- In completion, the arg id changes from `md-file` to `target`, and completion offers `*.md` and
  `*.pdf`.
- Bob's `--force` is **never** passed through to sase-listen, where `--force` bypasses
  structural lint.

### 5.2 Target classifier

Rules apply in order, and the first match wins. Every kind then flows into the same planner,
dedupe, installer, and summary.

| Kind | Detected by | How Bob gets the PDF | Default `-t` | Default stem | `source_url` | Listen `{target}` |
| --- | --- | --- | --- | --- | --- | --- |
| arXiv | `http(s)` URL where the ported `arxiv_paper_id()` returns an ID | adapter direct-PDF fetch of `https://arxiv.org/pdf/<id>`, plus arXiv API metadata | `papers` | short title stem, else the ID | `https://arxiv.org/abs/<id>` | cleaned URL as typed (sase-listen canonicalizes it the same way) |
| Web URL | any other `http(s)` URL | existing clip adapter, which picks HTML (reader template) or PDF (bytes kept unchanged) | `blogs` for HTML, `papers` for PDF | URL slug, then title | cleaned URL | cleaned URL |
| Local PDF | existing file with a `.pdf` suffix or `%PDF-` in its first 1 KiB | copy into scratch; **the original is never modified** | `papers` | file stem, snake_cased | none | absolute path of the **original** (sase-listen keys it by content hash) |
| Markdown | existing `.md`/`.markdown` file | pandoc/XeLaTeX, **rendered in scratch** | `chat` | file stem | none | sibling `<stem>_narration.md` if one exists, else the `.md` |
| *refused* | `*_narration.md` | — | — | — | — | hint: pass the report; its narration is discovered |
| *refused* | ref-shaped (`kind:path`) and not an existing path | — | — | — | — | hint: pass the artifact's file path |
| *refused* | anything else | — | — | — | — | names the accepted shapes |

### 5.3 arXiv: match sase-listen, then go further

- **Recognition.** Port `web/arxiv.py` to `highlights_ref/arxiv.rs` as pure string logic with no
  new crates, with MIT attribution. Copy sase-listen's `tests/test_arxiv.py` vectors byte for
  byte. Keep them in a conformance table in the docs, following the precedent of the priority
  marks contract (`c2aec57`), so the two tools can't drift apart unnoticed. Without this port,
  `clip https://arxiv.org/abs/…` captures the abstract page. That was the failure behind
  Bryan's 2-minute episode.
- **Fetch.** Use the adapter's direct-PDF path, after moving browser discovery behind the PDF
  probe (§5.4).
- **Metadata (fail-soft).** Add an `arxiv_id` request field to the adapter, as an additive
  protocol change. The adapter queries `export.arxiv.org/api/query?id_list=<id>` and returns
  `title`, `author` (the first three names, then "et al."), and `published`. If the API fails,
  fall back to the PDF's Info `/Title`, then a humanized ID, and print a warning. The
  `-T`/`-A`/`-p` overrides always win.
- **Stem.** Take the title text before any colon, snake_case it, drop a leading article, and cap
  it at about 5 words. `-N` overrides it.
- **Dedupe key.** `arxiv:<id without version>`, compared against `source_url` and legacy `url:`
  in ref notes and queued markers. A hand-made note without a PDF (the 31 in `ref/ai/**`) only
  produces an "also referenced by …" warning.

### 5.4 Local PDFs and PDF URLs: "use that PDF", safely

1. Copy the PDF into a 0700 scratch directory, stamp the copy, and install it atomically. Never
   reflow or re-typeset a paper.
2. **Insert the marker first** in `/Annots`: change `push` to `insert(0, …)`. Rendered PDFs
   don't change, and imported PDFs that already carry a sticky note work correctly.
3. If page 1 already has a note that parses as a Bob marker, refuse with
   `already a Highlights PDF; use bob highlights sync`.
4. Refuse PDFs that already live in `lib/` or `xlib/`. With `-L`, attach audio instead (§5.7).
5. Refuse files of 95 MiB or more, the vault-sync limit, and warn at 50 MiB, at create time. Note
   that sase-listen separately caps PDFs at 64 MiB / 400 pages with no OCR. A capture can
   therefore succeed while its audio fails. That counts as partial success, not an intake error.
6. If lopdf can't load the file (encrypted or unparseable), fail closed with
   `hint: qpdf --decrypt in.pdf out.pdf`.
7. Adapter fixes:
   - Probe for a PDF **before** `discover_browser()`; a direct-PDF response reports
     `browser: none`.
   - Widen PDF detection to `application/x-pdf` and to octet-stream or missing types with
     `%PDF-` magic, to match sase-listen.
   - Keep Bob's stricter public-network and redirect rules.

### 5.5 The listen contract and chezmoi config

This goes in chezmoi `home/dot_config/bob/config.yml`:

```yaml
highlights:
  pre_scan_hook: PATH="$HOME/bin:$PATH" bob_xlib_pull
  # `bob highlights create --listen` narrates the target with this command. The line is
  # split like a shell would split it, but never run through one.
  #   {target}  URL, PDF, or Markdown (or its _narration.md) to narrate
  #   {audio}   file the command must write the finished episode audio to
  # The command's own output streams to the terminal unchanged.
  listen_command: sase-listen render {target} --edition full --publish --output {audio}
  # sase-listen generates editions only for URLs and PDFs; Markdown is read as written.
  listen_markdown_command: sase-listen render {target} --publish --output {audio}
```

**Resolution.** `BOB_HIGHLIGHTS_LISTEN_COMMAND`, then `highlights.listen_command`. The Markdown
key resolves the same way and falls back to `listen_command`. There is **no built-in default**.
Running `--listen` without configuration fails before anything is written:

```text
bob highlights: error: --listen needs highlights.listen_command in ~/.config/bob/config.yml
hint: for sase-listen, add under highlights:
  listen_command: sase-listen render {target} --edition full --publish --output {audio}
```

**Validation, at config load.** Errors use the existing `ConfigError::Invalid` style:

- The value is a non-empty string, split with POSIX shell-word rules so quotes work, or a YAML
  list of strings.
- `argv[0]` contains no placeholder. A leading `~` in it is expanded.
- `{target}` appears at least once.
- `{audio}` appears exactly once. It may be embedded in a token, as in `--output={audio}`.
- Unknown `{…}` tokens are errors, which catches typos like `{url}` or `{output}`.

**Spawn** (in a new `highlights_ref/listen.rs`):

- Substitute placeholders into whole argv elements, then `Command::new(argv0).args(rest)`.
- Inherit stdin, stdout, and stderr. Run in the caller's working directory. `{target}` and
  `{audio}` are always absolute paths or cleaned URLs.
- Set `BOB_HIGHLIGHTS_LISTEN=1` in the child's environment. This is reserved for a future
  recursion guard.
- No Bob-side timeout: full editions legitimately take minutes.
- Before spawning, flush Bob's own output so the framing line lands above the child's.

**Ctrl-C** uses `system(3)` semantics:

- Bob ignores SIGINT and SIGQUIT while it waits.
- The child resets both to `SIG_DFL` in `pre_exec`. If the child inherited `SIG_IGN`, Python
  would never install its KeyboardInterrupt handler, and sase-listen's graceful Ctrl-C (which
  finishes and caches in-flight chunks) would be lost.

**Accepting the audio:**

- `{audio}` is `<scratch>/<stem>.mp3`, in a 0700 directory **outside `xlib/`**, so the rsync can
  never grab sase-listen's `.tmp-*` file.
- After the command exits, the file must exist, be at least 1 KiB, and pass a magic sniff:
  `ID3` or an MPEG frame sync for MP3, `ftyp` for M4A, `OggS` for Ogg/Opus.
- Accepted audio then goes through the existing `plan_audio_copy` rules: identical-bytes reuse,
  `--force` to overwrite, and refusal when the `lib/` slot is occupied.

**Why this contract:**

- It uses sase-listen's own documented, atomic flag, which runs before publish, so a publish
  failure can't take the audio with it.
- It needs no knowledge of sase-listen's JSON schema, library layout, or URL canonicalization.
- Any TTS tool can satisfy it with a two-line wrapper.
- If Bob later wants the episode ID or duration, an optional `{result}` placeholder can be added
  once sase-listen has something like `render --result-file`. Existing configs keep working.

### 5.6 Stage order and failure semantics

```text
plan ─▶ preflight ─▶ acquire* ─▶ listen ─▶ render† ─▶ install (audio, then PDF) ─▶ summary
        (exe on PATH,  (network,     (minutes,  (Markdown;    (atomic; existing
         dedupe,        fails before  costs $)   ▶ Play bound  rollback of audio
         collisions,    any TTS)                 to real audio) on PDF failure)
         audio slot)
* URL, arXiv, and local-PDF kinds acquire into scratch.  † Markdown renders after listen.
```

The two files land milliseconds apart, so the Mac's pull nearly always takes them together.
Late pairing covers the rare split.

| Where it stops | What is written | Exit | What Bob says |
| --- | --- | --- | --- |
| Not configured, exe missing, bad template | nothing | 1 | error plus config snippet |
| Dedupe hit, no `-L` | nothing | 1 | today's message plus `hint: add -L to attach audio` |
| Capture fails (bot wall, thin page, network) | nothing | 1 | today's clip `hint:` lines |
| Ctrl-C during listen (child exits 130 or is killed by SIGINT) | nothing | 130 | `re-run the same command; the listen tool resumes from its cache` |
| Listen fails, no audio | **PDF** | 1 | `PDF queued without audio (listen command exit 4; see its output above)` plus a `retry:` line |
| Listen exits non-zero *after* writing valid audio (for sase-listen, a failed explicit `--publish`) | **PDF + audio** | 1 | `audio paired; listen command exited N after writing it — see its output above` |
| Listen exits 0, but audio is missing or invalid | **PDF** | 1 | contract-violation message naming the template key |
| Audio slot conflict found late | **PDF** | 1 | existing `target audio already exists …; pass --force` |

Bob never claims that an episode is "published" or "on your phone". sase-listen's own summary
already prints the publish result and the AntennaPod refresh hint. AntennaPod's default refresh
interval is long, documented at 12 hours, so "refresh the feed" is the honest wording.

### 5.7 Re-runs, attach mode, and backfill

With `-L`, a dedupe or collision hit becomes an attach instead of a refusal:

- **The source already has a ref note** with `source_pdf: lib/<rel>.pdf`: run the listen command
  and drop the audio into the late-pair slot `xlib/<rel>.mp3`. The next scan moves it, adds
  `audio:`, and embeds the player. All of that is existing behavior.
- **The PDF is still queued in `xlib/`:** put the audio beside it.
- **The note already has audio:** still run the command, which re-publishes. That matters after
  the feed's 90-day pruning. Pair nothing, and report `audio: kept [[…]]`.

The same rule backfills the hand-made paper refs, for example
`bob highlights create https://arxiv.org/abs/2605.21997 -L`. It never re-stamps or overwrites an
annotated library PDF.

### 5.8 Backstops for "always tracking"

The flag only covers sources that go through Bob, but the observed leak came entirely from
running sase-listen directly. Two cheap backstops close it:

1. **Bind existing episodes without `-L`.** For URL and PDF kinds, `create <url>` pairs an
   existing library episode whose manifest `source.url` matches Bob's dedupe key, including
   arXiv IDs. The newest `created_at` wins, and `--no-audio` opts out. This extends today's
   Markdown discovery, which already reads `highlights.audio_library`. It is a soft,
   config-overridable dependency on the library layout, used only where a miss is harmless.
2. **A `bob highlights doctor` reconcile row.** It lists article episodes that have no ref note,
   as ready-to-paste `bob highlights create <url>` lines. Today it would list the 9 sources in
   §0, and running those lines backfills them without paying for TTS again.

Optional habit help in chezmoi: `alias listen='bob highlights create --listen'`. A sase-listen
post-render hook that calls Bob would be the strongest "always". It is deferred: it couples the
two tools, and the reconcile report should first show whether leakage continues.

### 5.9 What it looks like

Bob's framing lines go to stderr, dim. The summary uses the existing `success_prefix` and
`key: value` style. The middle block belongs to the listen command and is never modified.

```text
$ bob highlights create https://arxiv.org/abs/2608.25174 -L
capturing arxiv.org · arXiv 2608.25174 …
✓ captured PDF · 23 pages · 4.8 MB · metadata: arXiv
── listen ─ sase-listen render https://arxiv.org/abs/2608.25174 --edition full --publish --output /tmp/bob-listen-48121/model_based_agentic_software_engineering.mp3
   [sase-listen's own live checklist and summary, unmodified — including its
    "Published to apollo — refresh the feed in AntennaPod" line]
── end listen ─ exit 0 · 3m 21s
✓ created Highlights-ready PDF with audio
pdf: ~/bob/xlib/papers/model_based_agentic_software_engineering.pdf
audio: ~/bob/xlib/papers/model_based_agentic_software_engineering.mp3 (from listen command)
title: Model-Based Agentic Software Engineering
author: James C. Davis, Kelechi Kalu, Huiyun Peng, et al.
published: 2026-08-25
source_url: https://arxiv.org/abs/2608.25174
status: ready
parent: obsidian_ref
id: model_based_agentic_software_engineering
ref: ref/papers/model_based_agentic_software_engineering.md (written by the next scan)
next: bob highlights scan
```

On failure, the receipt is the same, but the headline changes:

```text
── end listen ─ exit 4 · 1m 02s
! PDF queued without audio — listen command failed (see its output above)
pdf: ~/bob/xlib/papers/model_based_agentic_software_engineering.pdf
retry: bob highlights create https://arxiv.org/abs/2608.25174 -L
```

The ref note that scan writes later:

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
---
# Model-Based Agentic Software Engineering

- [ ] #task #ref [[lib/papers/model_based_agentic_software_engineering.pdf]] #hide ^ref

![[lib/papers/model_based_agentic_software_engineering.mp3]]
```

**Dry run (`-d`).** Prints the plan, the marker, the audio destination, and the resolved listen
argv, with `{audio}` shown as its scratch path. It then prints `listen: would run …` and
`writes: none`. URL dry-runs keep clip's documented probe behavior. Nothing is synthesized,
published, or written.

**`doctor` rows**, styled like the existing `pre_scan_hook:` row:

- `listen_command: none (optional)` when nothing is configured; this never fails.
- `ok (sase-listen → ~/.local/bin/sase-listen; {target} {audio})` when it resolves.
- `fail` when the executable is missing or the template is invalid.

---

## 6. Alternatives rejected

| Alternative | Why not |
| --- | --- |
| A new `bob highlights listen <target>` | Listening is a property of capturing a reference. A separate verb would duplicate every capture option and invite listening without a ref. |
| Keep `create` Markdown-only; put `--listen` on `create` and `clip`; add an `import` for PDFs | Three front doors, two of them with `--listen`, and arXiv defaults split across them. Bryan asked for `create <target>`. |
| Built-in `sase-listen` default command, or Bob composing sase-listen flags | Violates "don't depend directly on sase-listen". The error-plus-snippet makes setup a single paste. |
| `sh -c` template | URLs contain `&`, `?`, and `;`. Interpolating them into a shell invites breakage and injection. |
| Run with `--json` and parse `audio_path` | Turns off the live checklist that Bryan asked to see. |
| Parse the human summary, or diff the library before and after | The summary is not a contract. Diffing breaks on canonical-URL drift and on concurrent agent renders. |
| Read `sase-listen/sources/<slug>/source.pdf` to avoid a second download | Couples Bob to an internal cache directory. Fetching twice is a few MB. An optional `{source}` placeholder (passing `--html <captured file>`) can come later if needed. |
| Bob writes the ref note immediately (reference-first) | Races the Mac scan, which is the single writer. It would point `^ref` at a PDF not yet in `lib/` and need link migration. Queuing the stamped PDF already guarantees tracking. |
| Write nothing if the listen step fails | Tracking is the goal. A queued PDF plus "re-run `-L`" loses nothing. |
| Forward Bob's `--dry-run` to sase-listen's `--dry-run` as a free cost preview | It isn't free: it runs the Gemini writer. |
| `--listen[=EDITION]` / `--edition` | The edition belongs in config. Add it later via an `{edition}` placeholder if per-call overrides turn out to be needed. |
| Default `-s next` when listening | Would flood the sticky Next lane. Listening isn't reading. |
| Link-only: never copy the MP3 into the vault | The feed prunes after 90 days, and the library is per-host. Kept available as `-L -n`; revisit if git growth hurts (Q2). |

---

## 7. Pre-existing issues found along the way

1. **Temp files land inside `xlib/`.** `create` renders `.<stem>.<pid>.render.pdf` beside the
   target, atomic writers use `.<name>.<pid>.tmp`, and `bob_xlib_pull` rsyncs everything with
   `--remove-source-files`. A cron tick during a render could move a partial dotfile, and Bob's
   install would then fail. Fix: render in scratch, which this design does anyway. Optionally
   also add `--exclude='.*'` to the rsync.
2. **The marker is appended, not prepended.** This is already latent for direct-PDF clips (§5.4).
3. **A direct-PDF capture requires a browser it never uses.** That breaks PDF URLs on hosts
   without Chrome, such as apollo, per the 2026-10-01 research.
4. **`clip https://arxiv.org/abs/<id>` captures the abstract page.** Fixing it takes the same
   `arxiv.rs`.

---

## 8. Recommended solution

**Ship this as one epic in three independently shippable phases. `create` becomes the single
intake door. `-L/--listen` is a configurable step that owns the terminal, and its only contract
with the tool is "write the audio to `{audio}`". Ref notes stay with `scan`, and publishing stays
with the listen tool.**

### Phase 1: one front door (no listening yet)

- Add the target classifier from §5.2 (`highlights_ref/target.rs`) and `highlights_ref/arxiv.rs`
  with the conformance vectors.
- Move clip's URL acquisition behind `create`.
  - `clip` becomes a hidden permanent alias.
  - The `ref_type` default depends on the target kind.
  - URL and PDF kinds always stamp `id`.
  - Merge the option sets as in §5.1.
- Import local PDFs safely (§5.4):
  - copy the file, never mutate the original;
  - insert the marker first;
  - refuse an existing marker;
  - apply the 95/50 MiB guards;
  - fail closed on encrypted files.
- Adapter changes:
  - probe for a PDF before discovering a browser;
  - widen PDF detection;
  - add the `arxiv_id` metadata request;
  - generate short-title stems.
- Dedupe by arXiv ID ignoring the version, and read the legacy `url:` key.
- Render Markdown in scratch.
- Docs: replace `docs/highlights-clip.md` with a `docs/highlights-create.md` that contains the
  kind table and the arXiv conformance table. Update the README, the help text, and
  `completion/kinds.rs`.

### Phase 2: `-L, --listen`

- `config/mod.rs`: add `listen_command` and `listen_markdown_command`, with env overrides and
  the validation from §5.5.
- `listen.rs`:
  - template split and substitution;
  - inherited stdio;
  - SIGINT/SIGQUIT discipline;
  - `BOB_HIGHLIGHTS_LISTEN=1`;
  - exit-status mapping;
  - audio magic sniff.
- `create.rs`:
  - the stage order and failure table from §5.6;
  - attach mode from §5.7;
  - the framing and summary from §5.9;
  - dry-run;
  - `-L -n` publish-only.
- Add the `doctor` row.
- **chezmoi:** add the two keys from §5.5 to `home/dot_config/bob/config.yml`, then apply them
  through the normal chezmoi workflow. sase-listen's config needs no change.

### Phase 3: "always" backstops and polish (each optional)

- Bind existing episodes without `-L` for URL and PDF kinds, and add the `doctor` reconcile of
  untracked episodes (§5.8).
- Upstream sase-listen `render --result-file`, plus an optional `{result}` placeholder for the
  episode ID and duration on the note.
- A `{source}` placeholder so audio and PDF share the captured bytes, which also helps on
  bot-walled pages.
- A PDF → ref-note backlink, if Bryan wants one (Q3).
- A listen card in the web-clip masthead.

### Tests (no live TTS in `just check`)

- **Classifier:** every row of §5.2, including look-alikes: `notarxiv.org`, a `.md` that is
  really a PDF, refs vs paths, and `*_narration.md`.
- **arXiv:** sase-listen's vectors byte for byte, the stem heuristic on the 5 real paper titles,
  and version-insensitive dedupe.
- **Listen runner,** using a fake command through `BOB_CONFIG_FILE` that writes a tiny MP3 to
  `{audio}`:
  - paths with spaces and URLs with `&` stay single argv elements;
  - exit 0 with audio, exit 0 without audio, a zero-byte file, and an HTML file named `.mp3`;
  - a non-zero exit with audio, exit 4 without audio, and exit 130;
  - a missing executable is caught at preflight;
  - an unknown placeholder or a missing `{audio}` is rejected at config load;
  - dry-run never spawns the command;
  - Bob's `--force` is never forwarded.
- **Signals:** send SIGINT to the process group while the fake command sleeps. Assert that the
  child sees it, Bob exits 130, and nothing was written.
- **Attach mode:** an existing note with and without audio, a queued `xlib` PDF, a library PDF,
  and scan late-pairing the dropped audio.
- **Import:**
  - a PDF with an existing sticky note gets the Bob marker first;
  - an existing Bob marker is refused;
  - the size guard trips;
  - the original's bytes are unchanged;
  - pandoc is never invoked for PDF kinds.
- **Compatibility:** `create --include-id <report.md>` output is unchanged without `-L`.

### Live verification gate

1. On athena, build from the tree and run against a scratch vault (`-b /tmp/…`) with a scratch
   `BOB_CONFIG_FILE` whose template omits `--publish`. Use one target of each kind:
   - an arXiv `/abs/` URL;
   - an HTML article;
   - a local PDF;
   - a Markdown report with a narration sibling.
2. Confirm that each PDF and its MP3 land together and that `scan --no-hooks` writes `audio:`
   and the embed.
3. Publish exactly one real episode with the real chezmoi config.
4. Confirm the episode appears in AntennaPod after a manual refresh.

---

## 9. Open questions for Bryan

1. **Hide `clip`, or keep it visible?** Recommendation: a hidden permanent alias, so there is one
   front door. Keeping it visible is harmless but redundant.
2. **Is audio in vault git acceptable?** An episode is about 4–7 MB. At the burst rate of the
   last two days (about 6 per day) that is roughly 10 GB/year. At 2 per day it is about 3.6
   GB/year, on top of about 1.35 GiB today. Recommendation: pair by default, use `-L -n` per
   call when the vault copy isn't wanted, and revisit with an `lib/**/*.mp3` git exclusion plus
   rsync, or with LFS, if growth hurts.
3. **"The ref note that is linked to from the PDF":** did you mean the existing link (the ref
   note's `^ref` task links to the PDF), or a clickable link *inside* the PDF that opens the
   note? The second doesn't exist today. It is feasible as an Obsidian-URI link annotation, but
   it is out of scope for v1.
4. **Default `--parent` for papers?** Your hand-made paper refs use `sase_ref` and `memory_ref`,
   while the default is `obsidian_ref`. A per-`ref_type` parent default in config is possible.
   Recommendation: keep using `-P` for now.
5. **Listen-failure policy:** keep the PDF and exit 1 (recommended), or all-or-nothing?

If accepted, two choices deserve a `decisions` record: folding `clip` into `create`, and the
`{audio}` listen contract that keeps Bob independent of sase-listen.

---

## Sources

- Researcher reports in this directory: `highlights_listen_intake__{cdx,cld,grk,mus,gem}.md`.
  - cdx: reference-first framing, artifact-ref parity, and the failure taxonomy.
  - cld: vault and library evidence, the `{audio}` contract, attach mode, and signal handling.
  - grk: the scan boundary, rejecting `sh -c`, and the "transcription" wording.
  - mus: cost visibility and the explicit publish requirement.
  - gem: the `ref_type` taxonomy and the alias-collision check.
- bob-cli `ce54258`:
  - `src/native/highlights_ref/{create,clip,stamp,marker,hooks}.rs`
  - `scripts/web_clip/web_clip_adapter.py`
  - `docs/highlights-ref-sync.md`, `docs/vault-git-sync.md`
  - `sase/memory/cli_rules.md`
- sase-listen `f8154ad`:
  - `src/sase_listen/pipeline.py` (266-274, 642-660, 720-800, 2103-2126, 2376-2430)
  - `cli/render.py`, `web/{arxiv,store,fetch}.py`, `writer/author.py`
  - `docs/podcast-feed.md`
- chezmoi `8efdb68`:
  - `home/dot_config/bob/config.yml`
  - `home/dot_config/sase-listen/config.yml`
  - `home/bin/executable_bob_xlib_pull`
  - `home/dot_config/sase/sase.yml`
- Read-only on athena: `~/bob/{lib,ref}` and `~/.local/share/sase-listen/library/*/manifest.json`.
- Prior research: `202610/web_url_reference_pdf_capture/web_url_reference_pdf_capture__final.md`
  (the sibling-command rationale) and `202610/gemini_tts_api_key_and_cost.md` (TTS pricing).
- External sources:
  - AntennaPod, "Refreshing podcasts" (default refresh interval), via the cdx report.
  - arXiv, "Versions" help page, via the cdx report.
