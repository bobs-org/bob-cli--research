# `bob highlights create --listen`: research, critique, and recommended design

- **Research date:** 2026-10-06
- **Question:** How should `bob highlights create` grow a `--listen` option that shells out to
  `sase-listen render <target> -e full`, so every AI-narrated paper/article shows up as a tracked
  ref note (plus PDF) in the Obsidian vault and as an episode in the AntennaPod feed?
- **Evidence:** `bob-cli` source (`src/native/highlights_ref/create.rs`, `clip.rs`, `clip_url.rs`,
  `audio.rs`, `stamp.rs`, `src/native/config/mod.rs`), `sase-listen` source and docs
  (`cli/render.py`, `web/store.py`, `web/arxiv.py`, `docs/web-articles.md`, `docs/podcast-feed.md`,
  `docs/configuration.md`), the chezmoi `dot_config/bob/config.yml`, and the prior
  `gemini_tts_api_key_and_cost` research note. All behavior below was read from source, not assumed.

## 1. What exists today

### 1.1 `bob highlights create` (markdown in, PDF out)

`create.rs` renders **one local `.md` file** into a Highlights-ready PDF
(`validate_markdown_path` rejects anything without a `.md` extension). The pipeline:

1. `plan_create` derives title/marker, picks a target via `plan_exact_output` (`--output`) or
   `plan_default_target` (`<xlib>/<ref-type>/<stem>.pdf`, i.e. the **Intake** workflow), and plans a
   companion-audio copy.
2. `create_pdf` renders with pandoc to a temp file, copies the audio **beside the PDF first**, then
   `stamp_and_install`s the page-1 marker. Audio copy happens before install so a failed copy aborts
   before the PDF lands; a failed install deletes the just-copied audio. Ordering is already atomicity-aware.
3. `print_next_step` tells the user to run `scan`/`sync` — **`create` never writes the ref note**.
   The ref note (with `audio:` frontmatter + `![[...]]` embed) is produced later by scan/sync pairing
   audio that sits beside the PDF (`discover_companion_audio`, `maybe_insert_audio_embed`).

Audio discovery order in `plan_audio_copy` is already sase-listen-aware: explicit `--audio`, then
frontmatter `audio.episode_id` resolved against the sase-listen library, then a sibling
`<stem>_narration.md` SHA-256 matched against library manifests (`BOB_HIGHLIGHTS_AUDIO_LIBRARY` env,
then `highlights.audio_library` config, then `$XDG_DATA_HOME/sase-listen/library`, then
`~/.local/share/sase-listen/library`), then same-stem audio beside target/source. **`--listen` output
therefore slots into machinery that already knows how to find it** — the new work is producing the
episode and getting the bytes beside the PDF, not teaching scan about a new audio kind.

Related: `create` already renders a `<div class="listen">` card as a LaTeX callout with a Play link
(`PANDOC_CODE_BREAK_FILTER`, `play_uri`, `BOB_HIGHLIGHTS_AUDIO_LINK_TEMPLATE`). A `--listen` run over
a Markdown source that contains a listen card gets a working Play button for free once audio is bound.

### 1.2 `sase-listen render <target> -e full` (anything in, MP3 out)

From `cli/render.py` and `docs/web-articles.md`, `render` accepts a **much wider** source than bob does:
narration-script/Markdown file, local PDF file, `kind:path` ref, or `http(s)` URL. For URLs:

- A URL is treated as PDF when the content type is `application/pdf`/`application/x-pdf`, or when an
  octet-stream/missing type carries `%PDF` bytes. Otherwise it must be public HTML (`text/html`,
  `application/xhtml+xml`); login/JS-only pages fail with a `--html FILE` retry hint. Pages under 150
  extracted words are rejected.
- **arXiv is special-cased** (`web/arxiv.py`, `web/store.py::acquire`): `/abs/`, `/html/`, `/pdf/`
  forms on `arxiv.org`/`www`/`export`, old- and new-style IDs, query/fragment ignored, version suffix
  kept — all normalize to `https://arxiv.org/pdf/<id>` and **share one cached source, script, and episode**.
  A failed PDF fetch does **not** fall back to the abstract page.
- The fetched/extracted source is cached under `$XDG_DATA_HOME/sase-listen/sources/` as `source.pdf`
  (or `page.html`) + metadata including `pdf_sha256`; re-renders reuse it, `--refresh` refetches.
  Editions: URL/PDF default is `brief`; `-e full` is an AI adaptation within a ~2,400-word budget
  (**not** a word-for-word transcript; that is `verbatim`), brief targets ~600 words. Writer = Gemini
  text API (token cost), synthesis = Gemini TTS chunk cache (re-renders are cheap).

Three output facts matter for the design:

1. **`-o/--output PATH` copies the finished MP3 to a caller-chosen path** ("Copied to ..." is printed).
   This gives bob the episode bytes at a deterministic location with **no output parsing**.
2. **`--json` emits exactly one JSON object** (`result_to_json`: `episode_id`, `title`, `audio_path`,
   `manifest_path`, `duration_s`, `published`, `publish_queued`, …; `plan_to_json` for `--dry-run`:
   `episode_id`, cost/duration estimates, chunk cache stats). But `--json` mode collapses the rich
   live/plain progress UI — it is either machine-readable or human-beautiful, not both in one invocation.
3. **Render does not necessarily publish.** `publish` defaults to `None` (config `feed.auto_publish`
   defaults to `false`, and auto-publish only covers `kind: research` refs anyway). Without `--publish`,
   the episode sits in the library and the summary says "saved in your library; publish it with
   `sase-listen publish <episode>`" — or, on failure to reach the host, `publish_queued` ("run
   `sase-listen publish --pending`"). The user's stated goal (episode in the AntennaPod feed) is
   **not** satisfied by bare `render <target> -e full`.

Feed mechanics (`docs/podcast-feed.md`): publishing copies MP3 + cover + chapters JSON into
`<feed-dir>/episodes/<episode-id>/` and atomically regenerates `feed.xml` (RSS 2.0, locked/private).
The render summary already prints "Published to the local feed." / "Published to \<host\> — refresh the
feed in AntennaPod" — i.e. the "show output in full" requirement already covers the publish
confirmation **if** bob streams render's stdio instead of capturing it.

Cost context (prior `gemini_tts_api_key_and_cost` note): paid-tier Flash TTS ≈ $0.81/audio-hour through
2026, $1.62 after; free tier is $0 but lets Google use content for product improvement — fine for public
arXiv papers, questionable for private vault notes. Every `--listen` invocation spends real money or real
quota; the design must make that visible **before** synthesis, not after.

### 1.3 Config today

`src/native/config/mod.rs` (`RawHighlights` → `HighlightsConfig`) already owns `highlights.pre_scan_hook`,
`highlights.audio_link_template`, `highlights.audio_library`, each with `BOB_HIGHLIGHTS_*` env overrides
and a rename-rejection precedent (`pre_scan_command` → error telling the user the new name). The chezmoi
source of truth is `home/dot_config/bob/config.yml` (`highlights.pre_scan_hook` is set there today).
New keys follow an established pattern; nothing structural needs inventing.

`bob highlights clip` is the precedent for URL intake: `validate_and_clean` (public http(s) only,
private/loopback/link-local rejected), tracking-param stripping, `source_url` recorded in the marker
(`MARKER_EXTRA_ORDER`), dedupe against recorded URLs, direct-PDF fetch via `clip_adapter`, and a guard
refusing library-direct writes. Any URL→PDF path in `create --listen` should reuse, not re-derive, these rules.

## 2. Critique: is this a good idea?

**Yes, with adjustments.** The core loop — "everything I listen to is a tracked ref note" — closes a real
gap: today a rendered episode leaves no vault trace unless the user hand-builds one, so listened papers
rot out of the system silently. And the architecture is favorable: sase-listen already owns fetching,
arXiv normalization, caching, TTS, and feed publishing; bob already owns PDF intake, marker stamping,
and audio→ref-note binding. The integration is thin glue between two mature halves, not a new subsystem.

Concerns, in rough severity order:

1. **The plan as stated does not reach the phone.** Bare `render -e full` does not publish (see §1.2.3).
   Without `--publish` (or a follow-up `sase-listen publish`), the user gets an MP3 in a library dir and
   no AntennaPod episode. The single most important correction: `--listen` must publish by default.
2. **`create` is the wrong home for half the request.** `create` renders md→PDF and never writes ref
   notes; "support URLs/arxiv + reuse the PDF + still write the note in the right place" duplicates what
   `clip` already does for URLs (fetch, clean, dedupe, marker `source_url`, intake placement). Bolting a
   second URL→PDF fetcher onto `create` forks the SSOT validation/dedupe logic and will drift. The URL/PDF
   half belongs in `clip` (or a shared intake path both call); `create --listen` should stay "md file in,
   episode + PDF out".
3. **`-e full` is an adaptation, not a transcription.** If the goal is "tracking what I listened to", a
   2,400-word adaptation is arguably the *right* granularity for a ref note anchor — but the request's
   language ("AI audio transcriptions") suggests the user may believe `full` is verbatim. Say the word
   "adaptation" in help text and the report, and consider whether `verbatim` should be one config click away.
4. **Cost × latency × surprise.** A full-edition render is minutes of TTS + writer tokens, every
   invocation. A bare `--listen` flag with no pre-flight is a footgun: typos, retries, and `--force`
   re-runs each cost money. `--dry-run` must exercise the listen plan for free (see §4).
5. **"Same values for `<target>` as render" is over-broad.** Render accepts `kind:path` refs and narration
   scripts — meaningless as Highlights intake. Promise parity only for the documented intake set:
   local `.md`, local `.pdf`, `http(s)` article/PDF URLs, arXiv URLs. Everything else is an explicit error,
   not a forwarded string.
6. **Do not shell out to a bare `sase-listen` and do not parse its human output.** Both halves of that are
   already decided practice in this codebase: `pandoc_command()` resolves `BOB_PANDOC_COMMAND` → `$PATH`
   with a named-hint error, and render offers `--json` + `-o` precisely so callers never scrape rich text.

## 3. Adjustments to the requirements (explicit)

1. **Publish by default.** `--listen` invokes `render … --publish` (config-overridable, §4). Rationale:
   without it the headline goal fails silently. The `publish_queued` state must surface as a warning with
   the `publish --pending` recovery command, not as success.
2. **Split the target work: URL/PDF intake lives with `clip`, not `create`.** `create --listen` accepts
   a local `.md` file (unchanged positional) and renders the episode from that same file; accepting a
   local `.pdf` / URL / arXiv ID in `create` should be implemented as intake-through-clip-shared-code
   (validation, dedupe, `source_url` marker, xlib placement, marker stamp) with "skip pandoc" semantics,
   or deferred to `clip --listen` in phase 2. Do not write a second fetcher.
3. **Configurable command, edition defaulting to `full`.** `highlights.listen_command` (default
   `sase-listen`, env `BOB_HIGHLIGHTS_LISTEN_COMMAND`) satisfies "no hard dependency"; add
   `highlights.listen_edition` (default `full`, env `BOB_HIGHLIGHTS_LISTEN_EDITION`) so the inevitable
   "I wanted verbatim for this one" does not require a code change. Flagship behavior stays `-e full`.
4. **"Shown in full" = inherited stdio, plus a structured pre-flight.** One invocation cannot be both
   rich-progress and JSON. Run the real render with stdout/stderr **inherited** (user sees the identical
   live checklist/summary sase-listen prints, including publish + "Copied to" lines), and get
   machine-readable facts from a free `render --dry-run --json` pre-flight (episode id, cost/duration
   estimates) plus `-o <beside-pdf path>` for the bytes. Never `--json` the expensive invocation.
5. **No new flag for publish opt-out in v1.** Publish default comes from config
   (`highlights.listen_publish`, default true, env `BOB_HIGHLIGHTS_LISTEN_PUBLISH`); a `--no-publish`
   spelling can be added when someone asks. Keeps the CLI surface to one flag per CLI rules (every long
   option needs a short alias; `-L` is free — `-l` is taken by `--lib-dir`).

## 4. Recommended design

### 4.1 CLI surface

```text
bob highlights create TARGET [--listen/-L] [existing flags...]
```

- `MD_FILE` positional is generalized to `TARGET` but phase 1 accepts **local `.md` only** (same
  validation as today); `.pdf`/URL/arXiv inputs route through the shared clip intake (§3.2) and are an
  explicit error until that lands. This keeps the shipped increment coherent instead of half-supporting
  five input kinds.
- `--listen` / `-L`: "Render this source as a podcast episode with `<listen_command> render <target>
  -e <edition> --publish` and bind the MP3 beside the PDF." Conflicts with `--no-audio` (listen
  *produces* the companion audio; combining them is nonsense — same `conflicts_with` pattern as
  `--audio`/`--no-audio` today). Composes with `--audio`? No — `--audio` means "use this file instead
  of discovering one"; `--listen` means "synthesize one". Make them conflict too, and say so in help.
- `--dry-run` runs the **free** pre-flight only: `render --dry-run [--json]` (writes the cached script,
  reports cost/duration/chapters) + prints the bob-side plan (target PDF, beside-PDF audio dest, publish
  intent). Zero synthesis, zero spend. This is the cost-visibility answer from §2.4.

### 4.2 Execution order (Markdown source)

1. Resolve `listen_command` (config → env → `$PATH`, `pandoc_command()` pattern; missing binary is an
   error naming `highlights.listen_command` and `BOB_HIGHLIGHTS_LISTEN_COMMAND`).
2. Compute the PDF target plan first (exact/default output, collision rules unchanged) so the
   beside-PDF audio destination `<target>.mp3` is known.
3. Pre-flight: `listen_command render <md> -e <edition> --dry-run --json` (captured, parsed). Print
   episode id, estimated minutes, estimated cost. Abort cleanly on non-zero exit with the child's stderr
   tail surfaced.
4. Pandoc-render + stamp the PDF exactly as today (unchanged; listen card keeps working via `play_uri`
   once audio exists).
5. Real render: `listen_command render <md> -e <edition> [--publish] -o <beside-pdf.mp3>` with stdio
   **inherited**. Append advice: renders run minutes; do not `Ctrl-C` lightly (sase-listen cache makes
   resume cheap — re-running reuses synthesized chunks).
6. Reuse byte-identity semantics: if the dest MP3 exists with identical bytes, reuse; different bytes
   require `--force` (mirrors today's audio-copy refusal). On render failure, remove nothing the user
   owned; on install failure after a fresh `-o` copy, remove the fresh copy (mirrors `audio_created`
   rollback).
7. Summary (styled, per CLI-rules color): `episode: <id>`, `audio: <path>`, `published: yes|queued
   (run sase-listen publish --pending)`, then the existing `pdf/title/status/parent` lines and next step.

### 4.3 Execution order (PDF/URL/arXiv target — phase 2, via shared clip intake)

1. Classify: local `.pdf` path vs URL string. URLs go through `clip_url::validate_and_clean` (SSOT
   scheme/host/tracking rules) + recorded-URL dedupe; arXiv needs no bob-side parsing — forward the raw
   string, sase-listen normalizes all `/abs|html|pdf` forms to one episode.
2. Obtain PDF bytes **without a second downloader**: `listen_command script <target> --json` reports
   `source_dir`; for PDF sources `<source_dir>/source.pdf` is the exact bytes sase-listen extracted from
   (plus `pdf_sha256` for verification). Copy → xlib intake target (`plan_default_target` /
   `plan_exact_output`, Intake workflow; never Library-direct, per clip's guard), `stamp_and_install`
   the marker with `source_url` extra (MARKER_EXTRA_ORDER already supports it).
3. Render with `-o <beside-pdf.mp3>` as in §4.2 (for URL targets the render source is the URL string
   itself, preserving sase-listen's cache identity). Scan then pairs audio→note as it does for every
   other intake PDF — no scan changes needed.

### 4.4 Config (chezmoi-owned)

```yaml
highlights:
  listen_command: sase-listen        # BOB_HIGHLIGHTS_LISTEN_COMMAND overrides
  listen_edition: full               # full | brief | verbatim; BOB_HIGHLIGHTS_LISTEN_EDITION
  listen_publish: true               # BOB_HIGHLIGHTS_LISTEN_PUBLISH (true/false)
```

New `RawHighlights` keys + `HighlightsConfig` accessors + the `pre_scan_command` rename-rejection
precedent if names ever change. Chezmoi diff is three lines in `home/dot_config/bob/config.yml`; the
binary default must work with zero config (PATH-resolved `sase-listen`), since config-file absence
already means defaults.

### 4.5 Reliability notes

- Timeouts: do not wrap the child in a bob-side timeout — renders legitimately run many minutes; killing
  them wastes the spend. Document expected durations in `--help` (brief ≈ minutes, full ≈ longer).
- Failure taxonomy to implement and test: listen binary missing; non-zero exit (surface exit code +
  last stderr lines, keep PDF if already installed — episode can be re-bound by re-run since `-o`
  + cache make it idempotent); `publish_queued` → warning, exit 0 with recovery hint (debatable: warn,
  don't fail — the vault state is complete); dry-run must never synthesize (assert `--dry-run` +
  `--json` argv in tests via a stub `listen_command` script).
- The stub-command test pattern is the whole test strategy: point `BOB_HIGHLIGHTS_LISTEN_COMMAND` at a
  fixture script that logs argv and emits canned `--json`, then assert argv composition, `-o` placement,
  conflict errors, and dry-run purity. No network, no TTS in `just check`.

### 4.6 Beauty notes

- Inherit, don't re-render: sase-listen's live checklist + green "Ready in …" + publish lines are
  already good; bob piping them through its own formatter would be strictly worse. Bob's own summary
  stays in the existing `success_prefix` style with the three listen lines from §4.2.
- Help text must say "adaptation" (not transcription) for `full`, state the publish default, name the
  three config keys + env vars, and show one end-to-end example. Keep options alphabetical with `-L`
  in sort position per CLI rules.

## 5. Recommended solution (build order)

1. **Phase 1 (this change):** `--listen/-L` for local `.md` only + §4.4 config + inherited-std render
   with `--publish` default + dry-run pre-flight + stub-command tests + README + chezmoi 3-line diff.
   Explicit error for non-`.md` targets naming the phase-2 plan.
2. **Phase 2:** PDF/URL/arXiv intake via the shared clip path (§4.3), reusing validation/dedupe/marker
   machinery; ref note continues to come from scan/sync untouched.
3. **Phase 3 (only on demand):** `--no-publish`, per-invocation `--edition` override, `clip --listen`.

The result: `bob highlights create paper.md --listen` yields a stamped PDF in xlib, an MP3 beside it, a
Play-linked listen card, a published feed episode, and — after the unchanged scan — a ref note with the
episode embedded. Every listened paper tracked, no new subsystems, no scraped output, no hardcoded binary.
