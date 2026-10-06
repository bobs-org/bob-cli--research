# `bob highlights create --listen`: intake papers you will hear

- **Researcher:** grk
- **Date:** 2026-10-06
- **Question:** How should `bob highlights create` grow a `--listen` option that publishes a podcast episode (via a configurable `sase-listen render` hook) alongside a Highlights-ready PDF and the vault ref note, including PDF URLs and arXiv, without depending on `sase-listen` by name?
- **Verdict:** Build it. The goal is right and the plumbing is mostly already there. Treat `--listen` as an opt-in *audio generation* step on intake, expand `create`'s target from Markdown-only to local PDFs / PDF URLs / arXiv, keep `scan` as the Obsidian note writer, and bind the renderer through a placeholder command template in chezmoi — never through a hardcoded binary.

---

## 1. In one breath

Bryan already has three cooperating machines for this product, and none of them generate audio on intake:

| Piece | What it does today | Gap |
| --- | --- | --- |
| `bob highlights create <md>` | Pandoc/XeLaTeX PDF into `xlib/<ref-type>/`, page-1 marker, optional *discovery* of an existing sase-listen MP3 | Source must be a `.md` file. No TTS. |
| `bob highlights clip <URL>` | Reader PDF (or a direct PDF download) into `xlib/blogs/`, provenance marker | HTML articles. Direct PDF URLs work; **arXiv `/abs/` is captured as the abstract page**. No TTS. |
| `sase-listen render SOURCE -e full` | Fetch/extract, write a full-edition script, synthesize, master, save to the listen library, auto-publish `kind: article` and `kind: research` to the AntennaPod feed | Knows nothing about `xlib/`, markers, or ref notes. |

`create` already *binds* companion audio (`--audio`, `audio.episode_id`, narration-hash match, sibling MP3) and `scan` already moves `.mp3`/`.m4a`/`.ogg`/`.opus` with the PDF and embeds `![[lib/…mp3]]` on the ref note. `bob_xlib_pull` rsyncs the whole `xlib/` tree, so companions already travel Mac-ward.

`--listen` is the missing *generation* gesture: "this source is something I will hear, so make the episode now, park the PDF+MP3 in intake, and let the existing scan write the tracking note." That is a good idea. The naive reading of the request — hard-wire `sase-listen`, have `create` write the Obsidian note, re-typeset a paper PDF through pandoc — is the wrong implementation.

---

## 2. Critique of the plan

The plan as stated: add `--listen` to `bob highlights create`, run `sase-listen render <target> -e full`, publish to the AntennaPod feed, support the same targets sase-listen does (especially PDF URLs and arXiv), skip PDF generation when the target already is a PDF, still write the Highlights note in the right place, show renderer output in full, and configure the renderer in chezmoi rather than depending on `sase-listen` by name.

### What is right

- **The goal is the vault, not the earbuds.** AntennaPod is how Bryan hears papers. The Bob ref note is how he remembers he heard them, highlights them later, and keeps a `^ref` task. Pairing those two artifacts is the whole product.
- **Opt-in flag, not a new default.** Full-edition Gemini TTS is minutes and dollars. `create` without `--listen` must stay the fast pandoc path.
- **Configurable renderer.** bob-cli already treats sase-listen as a *library on disk* (`highlights.audio_library`, `BOB_HIGHLIGHTS_AUDIO_LIBRARY`), never as a required binary. Generation should follow the same pattern as `highlights.pre_scan_hook`: a command string in `~/.config/bob/config.yml`, chezmoi-managed.
- **Pass the target through.** sase-listen already rewrites arXiv `/abs|html|pdf/<id>` to `https://arxiv.org/pdf/<id>`, caches by canonical URL, extracts with pdfminer, writes `kind: article` scripts, and auto-publishes because `feed.auto_publish: true` is already in chezmoi. Bob should not reimplement TTS, the writer, the feed, or AntennaPod.
- **Reuse intake.** `create`/`clip` write `xlib/`; Mac `scan` (after `bob_xlib_pull`) writes `lib/` + `ref/`. That boundary was the clip research conclusion and it still holds.
- **Show the renderer live.** sase-listen's live checklist (fetch → write script → plan → synthesize → gates → master → save → publish) is the beautiful part of waiting. `--json` disables it. Inherit stdout/stderr; do not capture.

### What is wrong or incomplete

1. **"Transcription" is the wrong word.** sase-listen is TTS *narration* (article → script → speech). Transcription is speech → text. The feed items are AI audio *editions*. Say that in help and docs.

2. **"Create the ref note" is still the wrong command boundary.** `create` never writes `ref/`. `clip` never writes `ref/`. `scan` does, on the Mac, after intake. Writing the Obsidian note from `create --listen` would race scan, skip dirty-target checks, and stamp `source_pdf:` with an `xlib/` path that scan then has to heal. The "Highlights note" that *must* be written at create time is the page-1 `/Text` marker (status, parent, title, id, `source_url`). The Obsidian ref note remains scan's job. This is the same adjustment the clip work made, and it is still correct.

3. **`create` is Markdown-shaped today.** `validate_markdown_path` requires a `.md` file and then shells out to pandoc. A paper PDF must *not* go through XeLaTeX. A PDF URL must be fetched and stamped. Those are clip-like intake paths sharing `stamp.rs`, not "run pandoc on a URL."

4. **HTML article URLs do not belong on `create`.** `clip` already owns reader-mode capture, bot-wall retries, fidelity checks, and `--html` replay. sase-listen's targets include HTML URLs; bob's HTML intake is `clip`. Expanding `create` into a second web clipper duplicates the hard part. PDF URLs and arXiv are the gap.

5. **clip already downloads direct PDFs — and will silently clip an arXiv abstract.** `scripts/web_clip/web_clip_adapter.py` probes `application/pdf` and writes the bytes without re-rendering. `https://arxiv.org/pdf/<id>` therefore already works as `clip`. `https://arxiv.org/abs/<id>` is HTML, so clip would capture the abstract page. The "same special support for arXiv" is a URL rewrite, about forty lines of pure string logic in sase-listen's `web/arxiv.py`. Bob needs that rewrite on the *PDF fetch* path, independently of the renderer, because the renderer is configurable and may not be sase-listen.

6. **`--json` and "show output in full" fight.** `sase-listen render --json` emits one object and *always* disables progress. Parsing `episode_id` / `audio_path` from JSON is how the research-audio xprompt binds library files. For an interactive `create --listen`, the contract should be **`--output`**: the template writes the MP3 to a path bob planned. No JSON. Live TTY. Binding is "the file `{output}` exists after exit 0."

7. **Depending on sase-listen's library layout after a live render is fragile.** Today's create discovery walks `<library>/<id>/manifest.json`. That is correct for *already-rendered* research reports. For `--listen`, requiring bob to know episode-id scheme, `audio.file`, and `$XDG_DATA_HOME/sase-listen/library` reintroduces a direct dependency. `{output}` removes it.

8. **Double-fetch is acceptable; coupling to `source.pdf` is not.** If bob fetches the arXiv PDF for intake and then the renderer fetches it again, that is a few extra megabytes and sase-listen will cache. Reading sase-listen's `sources/<slug>/source.pdf` after render would bake in an implementation directory. A later optional `{pdf}` placeholder can pass `--html {pdf}` for users who want to skip the second GET. v1 should not.

9. **`--listen` on create alone misses "articles."** The stated goal is articles *and* papers. Papers are create-shaped (PDF/arXiv). Articles are clip-shaped. The same flag and the same config key should land on `clip` in the same change.

10. **kind:path refs and narration scripts are sase-listen targets, not Highlights intake targets.** `sase-listen render research:202610/foo.md` is a SASE artifact. `sase-listen render notes_narration.md` is already how research audio works, and create already binds that MP3. Do not teach `create` to `sase artifact read`. Fail with a hint.

11. **A new `bob highlights listen` subcommand is tidier help and the wrong verb.** The user asked for `--listen` on `create` because the gesture is *intake*. A sibling subcommand would split "make the PDF" from "make the audio" and invite people to listen without a ref. Keep one intake command; make listen a flag.

---

## 3. Justified requirement adjustments

These change the user's wording. They are deliberate.

| Original implication | Adjustment | Why |
| --- | --- | --- |
| `create` writes the Obsidian ref note | `create --listen` writes `xlib/<ref-type>/<stem>.pdf` + companion `<stem>.mp3` (marker-stamped). The next Mac `scan` writes `ref/<ref-type>/<stem>.md` with `audio:` and the player embed. | Matches `create` and `clip`. Preserves intake, collision checks, and `source_pdf:` library paths. `bob_xlib_pull` already rsyncs MP3s (`rsync -a --remove-source-files --ignore-existing` of the whole `xlib/` tree). |
| Hard-wire `sase-listen render <target> -e full` | Config template `highlights.listen_command`, required placeholders `{target}` and `{output}`. Chezmoi supplies `sase-listen render {target} -e full -o {output}`. Bob has **no default binary name**. | Honors "do not depend directly on sase-listen." `-e full` and `--publish` stay in *Bryan's* config / sase-listen config (`feed.auto_publish: true` already). |
| `create` accepts every sase-listen `SOURCE` | `create <target>` accepts: existing `.md`, local `.pdf`, `http(s)` PDF URL, arXiv paper URL. HTML article URLs error with `hint: bob highlights clip --listen <URL>`. `kind:path` refs error. | PDF/arXiv is the actual gap. HTML is clip. Artifact refs are sase-listen's job. |
| When the target is a PDF, skip PDF creation | Copy/fetch the original bytes, stamp the page-1 marker with lopdf, install via existing `stamp_and_install`. Never pandoc a paper. | Re-typesetting a paper destroys figures, layout, and Highlights quote quality. Clip already does this for `kind: pdf`. |
| Show sase-listen output in full | Inherit stdout and stderr, stdin null, no `--json`, no timeout of our own. `create --dry-run` prints the expanded argv and does **not** run the renderer (and does not fetch). | `--json` kills the live checklist. Dry-run of create today does not invoke pandoc; listen must match. TTS on dry-run would still bill the writer. |
| `--listen` only on `create` | Same flag, same config, on `clip` as well. | Goal names articles. Clip is the article intake command. |
| Default `ref-type` stays `chat` | Markdown keeps `chat`. Local PDF / PDF URL / arXiv default to `papers`. Clip stays `blogs`. Always overridable with `-t`. | Vault already has `lib/papers` and `ref/papers`. Chat is for research-report PDFs. |
| Marker `id` stays optional (`-i`) | PDF/URL/arXiv intake **always** embeds `id` (stem / arXiv id with `/` → `-`). Markdown keeps today's `-i` behavior. | Clip always embeds `id`. Papers need a stable identity for scan and for the listen card. |
| Bob reimplements arXiv inside the renderer call | Bob rewrites arXiv for *its own PDF fetch*. The renderer receives the **original** `{target}` so sase-listen's rewrite/cache still keys on the canonical PDF URL. | Renderer is configurable. Bob still has to obtain bytes for `xlib/`. Two independent rewrites of a 40-line pure function beat a hidden coupling. |
| Parse render JSON for `episode_id` | Plan the companion path first. Substitute `{output}`. After exit 0, require that file to exist and to be an allowed audio extension. Then the existing atomic audio-copy/reuse logic is a no-op because the file is already at dest. | Removes library-layout coupling. Works for any renderer that can write an MP3 to a path. |
| "AI transcriptions" | Docs and help say **AI audio edition** / **narration**. | Accurate, and it matches sase-listen's brief/full/verbatim edition vocabulary. |

A Markdown-only "I listened to this" note without a PDF is a different product. It would skip Highlights. Out of scope.

---

## 4. How the pieces actually work

### 4.1 `bob highlights create` today

Code: `src/native/highlights_ref/create.rs`, `audio.rs`, `stamp.rs`. Docs: `docs/highlights-ref-sync.md`.

1. Require a `.md` file. Title = YAML `title`, else first `# ` H1, else stem.
2. Plan `xlib/<ref-type>/<stem>.pdf` (default `ref-type=chat`) or an exact `--output`.
3. Discover companion audio, first hit wins: `--audio PATH` → frontmatter `audio.episode_id` in the sase-listen library → sibling `<stem>_narration.md` SHA-256 vs `source.sha256`/`script.sha256` → existing sibling/target MP3. `--no-audio` skips.
4. Pandoc + XeLaTeX to a temp PDF, with the listen-card Lua filter turning `<div class="listen">` plus a bound companion into a ▶ Play callout.
5. Atomic-copy audio beside the PDF, then `stamp_and_install` the page-1 marker.
6. Print `pdf:`, `audio:`, `audio_link:`, `next: bob highlights scan`.

It does not write `ref/`. It does not run TTS.

### 4.2 `bob highlights clip` today

Code: `clip.rs`, `clip_url.rs`, `scripts/web_clip/web_clip_adapter.py`.

- HTML: Playwright + Defuddle + Bob print template.
- Direct PDF: HEAD/ranged GET for `application/pdf`, download bytes, `pdf_info_title` from lopdf, stamp marker with `source_url`, `id`, `captured`.
- Dedupe on cleaned `source_url` against ref notes and queued intake. `--force` still will not overwrite a duplicate URL.
- Default `ref-type=blogs`. Always embeds `id`.

No arXiv rewrite. No `--listen`.

### 4.3 sase-listen `render` today

Repo: `gh:sase-org/sase-listen` (opened for this research).

```text
sase-listen render SOURCE [-e {brief,full,verbatim}] [-o OUT.mp3]
  [--publish|--no-publish] [--html FILE] [--refresh] [--progress …] [--json]
```

`SOURCE` is a narration script, Markdown, local PDF, `kind:path` ref, or `http(s)` URL. URL/PDF defaults to AI `brief`; `-e full` is a ~2,400-word adaptation; `verbatim` is a deterministic reading. arXiv hosts `arxiv.org` / `www.arxiv.org` / `export.arxiv.org`, paths `/abs|html|pdf/<id>` (old and new ids, optional `.pdf`, version suffix kept), fetched as `https://arxiv.org/pdf/<id>`. Failed PDF fetch does not fall back to the abstract.

`--output` copies the mastered MP3 to PATH *and* still saves the library episode. `--publish` / `feed.auto_publish` publishes `research` and `article` kinds. Chezmoi already has:

```yaml
# ~/.config/sase-listen/config.yml
feed:
  auto_publish: true
  host: apollo
  base_url: https://apollo.tail297af1.ts.net:8443
```

URL/PDF brief+full sets `script.meta.kind = "article"`, so a paper render publishes to AntennaPod without bob asking.

Live progress is TTY-native. `--json` is the agent contract (`episode_id`, `audio_path`, `published`, …) and turns progress off.

### 4.4 Config surface today

`HighlightsConfig` (`src/native/config/mod.rs`) already has `pre_scan_hook`, `audio_link_template`, `audio_library`. Env overrides: `BOB_HIGHLIGHTS_PRE_SCAN_HOOK`, `BOB_HIGHLIGHTS_AUDIO_LIBRARY`, `BOB_HIGHLIGHTS_AUDIO_LINK_TEMPLATE`.

Chezmoi `home/dot_config/bob/config.yml` currently:

```yaml
highlights:
  pre_scan_hook: PATH="$HOME/bin:$PATH" bob_xlib_pull
```

`pre_scan_hook` is a `sh -c` string because it is a vault-side side effect with env assignments. A listen renderer is an argv with a URL. **Do not use `sh -c` for listen.** URLs and paths must not go through a shell.

### 4.5 CLI rules that constrain the flag

From `sase/memory/cli_rules.md`:

- Every public long option needs a short alias.
- Options sorted alphabetically in help.
- Help must be excellent.
- Colored output when it helps.

`--listen` / `-L` ( `-l` is `--lib-dir`, `-n` is `--no-audio` on create, `-a` is `--audio`). Insert between `--lib-dir` and `--no-audio` in create help. Clip help inserts the same pair alphabetically.

---

## 5. Recommended design

### 5.1 User-visible command

```bash
# Markdown research report: PDF as today, plus a full-edition episode
bob highlights create report.md --listen

# Local paper: stamp the original, do not re-typeset
bob highlights create ~/papers/systems-performance.pdf --listen

# arXiv abstract URL: fetch the PDF, stamp, narrate, publish
bob highlights create https://arxiv.org/abs/2608.25174 --listen

# Direct PDF URL
bob highlights create https://arxiv.org/pdf/2608.25174 --listen

# Article (same flag, other command)
bob highlights clip https://example.com/posts/some-article/ --listen

# Preview: classify, plan paths, print argv, write nothing, do not TTS
bob highlights create https://arxiv.org/abs/2608.25174 --listen -d
```

Success report (after the inherited sase-listen checklist):

```text
✓ created Highlights-ready PDF
pdf: /home/bryan/bob/xlib/papers/2608.25174.pdf
audio: /home/bryan/bob/xlib/papers/2608.25174.mp3 (from listen)
listen: sase-listen render https://arxiv.org/abs/2608.25174 -e full -o /home/bryan/bob/xlib/papers/2608.25174.mp3
title: Attention Is All You Need
source_url: https://arxiv.org/abs/2608.25174
status: ready
parent: obsidian_ref
id: 2608.25174
pages: 15
next: bob highlights scan
```

`--dry-run` uses the usual `would create` prefix, prints the same fields, `listen: would-run …`, `writes: none`.

### 5.2 Target classification

A small `TargetKind` in `highlights_ref` (shared by create; clip keeps URL validation but reuses arXiv + PDF fetch):

| Input | Kind | PDF pipeline | Default `-t` | Marker extras |
| --- | --- | --- | --- | --- |
| path ending `.md` (file exists) | `markdown` | pandoc/XeLaTeX as today | `chat` | none (today) |
| path ending `.pdf` (file exists) | `pdf-file` | copy bytes → stamp | `papers` | none, or `source_url` if later added |
| `http(s)` URL whose arXiv rewrite or content-type/`%PDF-` sniff is a PDF | `pdf-url` | GET → stamp | `papers` | `source_url`, `captured`, `author`/`published` when known |
| arXiv `/abs|html|pdf/<id>` | `arxiv` (subtype of `pdf-url`) | rewrite to `https://arxiv.org/pdf/<id>`, GET → stamp | `papers` | `source_url` = cleaned original URL (the one Bryan pasted), `id` = paper id with `/` → `-` |
| other `http(s)` URL | reject | — | — | hint to `clip --listen` |
| anything else | reject | — | — | name the four accepted shapes |

Fetch rules, aligned with clip + sase-listen:

- Public `http`/`https` only; reuse `clip_url::reject_private_host`.
- Size cap 64 MiB (sase-listen's `MAX_PDF_BYTES`).
- Accept `application/pdf`, `application/x-pdf`, or octet-stream/missing type with `%PDF-` in the first 1 KiB.
- User-Agent: a bob-specific string, not a silent curl clone.
- No OCR, no Playwright on this path. Bot-walled PDFs fail closed with `hint: download the PDF and pass the local file`.
- Title: PDF Info `Title` (clip already has `pdf_info_title`), else humanized stem, else `arXiv:{id}`.
- Stem: arXiv id (`hep-th-9901001` from `hep-th/9901001`); otherwise reuse clip's `stem_from_url` / `--name`.
- Dedupe PDF URLs the same way clip dedupes `source_url`.

Do not add `reqwest` if a tiny `ureq` (or even a tightly-wrapped `curl` with a test seam) will do. The clip adapter's Playwright GET is the wrong dependency for arXiv. Put a `fetch_pdf(url) -> Vec<u8>` behind a function so tests inject bytes.

Copy sase-listen's arXiv tests (`tests/test_arxiv.py` cases) as Rust unit tests. Hosts, old ids, version suffixes, query/fragment ignore, no fallback for `/list/` or `/src/`.

### 5.3 Config contract

```yaml
# ~/.config/bob/config.yml  (chezmoi: home/dot_config/bob/config.yml)
highlights:
  pre_scan_hook: PATH="$HOME/bin:$PATH" bob_xlib_pull
  listen_command: sase-listen render {target} -e full -o {output}
```

Resolution, first hit wins, matching other highlights keys:

1. `BOB_HIGHLIGHTS_LISTEN_COMMAND` (empty value disables / errors on `--listen`)
2. `highlights.listen_command` in the Bob config file
3. **nothing** — `--listen` then fails:

   ```text
   bob highlights: error: --listen requires highlights.listen_command
     hint: add to ~/.config/bob/config.yml:
       highlights:
         listen_command: sase-listen render {target} -e full -o {output}
   ```

Parse rules:

- Whitespace-split into argv. **No `sh -c`.**
- `{target}` and `{output}` must each appear as a complete token (or as a substring replaced inside a token). Missing either is a config error, caught before any fetch or TTS.
- Optional later: `{pdf}` for `--html {pdf}`. Not in the chezmoi default.
- First token is the program; `command -v` it the way `pre_scan_program` does. Missing executable is a clear error.
- `{target}` is the **user's original string** (the arXiv abs URL, the markdown path, the PDF path). `{output}` is the planned companion path with a lowercased extension, default `.mp3`.

Why this shape beats an argv array in YAML: Bryan's other highlights hooks are one-liners, chezmoi diffs stay readable, and `-e full -o {output}` is exactly the command he quoted.

Why this shape beats `sh -c`: a URL with `?` or `&` must not hit a shell. Placeholder substitution after split makes `{target}` one argv word.

Feed publication stays in sase-listen config. bob does not grow `--publish`. Bryan already auto-publishes.

### 5.4 Execution order (reliability)

Plan first, mutate last, TTS in the middle with the vault still untouched:

1. Classify target. Fail closed (HTML URL, missing file, bad scheme).
2. Resolve listen argv if `--listen`. Fail if `--listen` with `--audio` or `--no-audio`. Fail if the template is missing.
3. Plan `TargetPlan` (intake path, sidecar guard, library destination). Same collision rules as create/clip, plus the companion audio library-destination check create already has.
4. `--dry-run`: print plan, expanded argv, marker, `writes: none`. Stop. No fetch, no pandoc, no TTS.
5. Obtain PDF bytes in a temp file (pandoc render, local copy, or HTTP GET). Do not install yet.
6. If `--listen`: spawn the argv with `stdin: null`, `stdout/stderr: inherit`, `cwd` unchanged (the renderer has its own config). Wait. Nonzero → delete temps → exit 1 with `listen command failed with exit N`. Ctrl-C reaches the child; bob exits 130 if the child does.
7. Confirm `{output}` exists and `audio::is_audio_companion_path`. If the renderer wrote elsewhere, that is a contract miss — error, do not hunt the library.
8. `stamp_and_install` the temp PDF onto the intake target (marker + optional Info title/author).
9. If `{output}` is already the dest path, skip the copy (treat as the planned dest). If the renderer cannot write in-place, copy atomically the way `plan_audio_copy` does today.
10. On any install failure after listen succeeded, keep the MP3 if it is already in `xlib/` (it is the expensive artifact) and report `pdf:` failure separately. Prefer: write audio to a temp next to dest, install PDF, then rename audio — so a failed stamp does not leave a stray MP3. Mirror create's current "delete audio this run created" rule.

`--force` overwrites dest PDF *and* dest audio when bytes differ, same as today's `--audio` path.

Markdown `--listen` still generates the PDF. The renderer gets the `.md` path. `-e full` on a plain Markdown file is ignored by sase-listen's source-stage picker (edition only changes URL/PDF stages); that is harmless in the template. Research reports that already have a library episode keep working *without* `--listen` via discovery. `--listen` on those will re-enter sase-listen's chunk cache and is usually cheap.

### 5.5 What bob does not do

- Does not import sase-listen, does not parse manifests, does not call `sase artifact read`.
- Does not write `ref/` notes.
- Does not pass `--json`, `--progress`, `--publish`.
- Does not re-encode the MP3 or rewrite ID3 tags.
- Does not fetch HTML articles.
- Does not OCR scanned PDFs. If the renderer later fails "extracted PDF text is too short," that error streams through inherit and bob's exit is the child's.

### 5.6 Doctor and help

`bob highlights doctor` gains a `listen_command:` row:

- `none` when unset (not a failure; `--listen` is opt-in)
- `ok (sase-listen; template: …)` when the program is on PATH
- `fail` when `--listen` would be unable to run (missing `{target}`/`{output}`, executable not found)

Help after-text for create should show three examples (md, local pdf, arXiv) and one sentence that scan writes the ref note. Clip help gets one `--listen` sentence.

### 5.7 Module layout

Keep this inside `highlights_ref`, not a new crate:

- `arxiv.rs` — pure URL rewrite + stem (unit-tested, no I/O)
- `listen.rs` — template expand, spawn inherit, dest checks
- `pdf_fetch.rs` — HTTP GET + sniff (test seam)
- `create.rs` — classify target, branch pandoc vs stamp, call listen
- `clip.rs` — add `--listen` after capture, same listen helper
- `config/mod.rs` — `listen_command: Option<String>`
- docs: `docs/highlights-ref-sync.md` (create), `docs/highlights-clip.md` (clip flag), README env table `BOB_HIGHLIGHTS_LISTEN_COMMAND`

Share stamp, collision, marker extras, and audio dest planning. Do not fork them.

---

## 6. Alternatives considered

| Alternative | Why it loses |
| --- | --- |
| Hard-code `sase-listen` argv in Rust with a `PATH` lookup | Violates the "do not depend directly" rule. A template is the same number of lines in chezmoi and keeps bob reusable. |
| `sh -c` like `pre_scan_hook` | URLs are not safe in a shell. Env-assignment sugar is not needed. |
| YAML argv array | Worse to edit; no gain over a split template. |
| Run `--json` and parse `audio_path` | Kills the live checklist the user asked to see. |
| Discover the new episode in `audio_library` after a live render | Couples to sase-listen's id scheme and manifest shape. `{output}` is the integration. |
| `bob highlights listen` subcommand | Splits intake. User asked for a flag on create. Help is already long; a flag is still smaller than a verb people have to remember. |
| Have create write `ref/` immediately | Races scan; wrong `source_pdf`; skipped on Linux where scan is a no-op until the Mac pull. |
| Re-typeset PDFs with pandoc | Destroys the paper. Clip already refuses this. |
| Teach create to clip HTML | Duplicates Playwright/Defuddle. Hint to `clip --listen`. |
| Pass `--html {pdf}` by default | sase-listen-specific flag. Offer `{pdf}` later. Double-fetch is fine. |
| Default `--listen` on | Costs money. Papers Bryan will only highlight should stay quiet. |
| Timeout wrapper | Full editions of long papers legitimately take many minutes. Inherit and wait. |
| `kind:path` support on create | Requires `sase artifact read` inside bob. Research reports already enter through Markdown `create --include-id` plus the audio xprompt. |

---

## 7. Risks and limits

- **Cost and time.** `-e full` on a 40-page paper is a real Gemini bill and a long wait. Dry-run must not write the script (sase-listen `--dry-run` still runs the writer). Bob dry-run therefore does not spawn.
- **Two fetches.** Bob GET + sase-listen GET. Cached on the listen side the second time Bryan re-renders. v1 accepts this.
- **Abstract-page disaster if rewrite is skipped.** Without arXiv rewrite, bob would either reject `/abs/` as HTML or (if someone sent it to clip) store the abstract. Tests for the rewrite are load-bearing.
- **Playwright vs native GET.** Native GET will lose to Cloudflare-gated PDF hosts. Fail closed; local file is the escape hatch. arXiv itself is fine.
- **`--ignore-existing` on `bob_xlib_pull`.** If a dest MP3 already exists on the Mac with different bytes, the new one will not overwrite. Same as PDFs today. Document it. `--force` on create only affects the machine that ran create.
- **AntennaPod replacements.** sase-listen already warns that a same-title re-publish does not replace a downloaded file until Bryan deletes the download. bob should not try to paper over that; the inherited renderer output already says it.
- **Markdown `-e full`.** Harmless extra flag for sase-listen; a different renderer might reject unknown flags. Bryan's template is his problem; bob does not sanitize flags.
- **Scan lag.** A paper heard tonight may not have a ref note until the Mac's next scan tick. That is today's create/clip contract. If it hurts, a later `--scan` flag (Mac-only) is a follow-up, not v1.

---

## 8. Recommended solution (do this)

**Ship `--listen` as an opt-in intake flag on `create` and `clip`, driven by `highlights.listen_command`, with `create` expanded to PDF files and PDF/arXiv URLs that are stamped rather than re-typeset. Leave Obsidian note writing to `scan`. Leave feed publication to sase-listen.**

Concrete work, in order:

1. **bob-cli config**
   - Add `highlights.listen_command: Option<String>` and `BOB_HIGHLIGHTS_LISTEN_COMMAND`.
   - Reject templates missing `{target}` or `{output}`.
   - Doctor row.

2. **`arxiv.rs` + PDF fetch**
   - Port sase-listen's pure rewrite (hosts, old/new ids, version suffix).
   - Native GET with private-host rejection, 64 MiB cap, `%PDF-` sniff.
   - Unit tests from sase-listen's `test_arxiv.py` table.

3. **`create` target expansion**
   - Rename positional help from `MD_FILE` to `TARGET`.
   - Branch: markdown → pandoc; local pdf / fetched pdf → stamp original.
   - Default `-t papers` for PDF kinds; always embed `id`; `source_url` + `captured` for URLs.
   - HTML URL: error + clip hint.

4. **`--listen` / `-L`**
   - Conflicts with `--audio` and `--no-audio`.
   - Expand template, inherit stdio, require `{output}` on success.
   - Dry-run prints `listen: would-run` and does not spawn.
   - Install PDF+audio after the child exits 0.
   - Same flag on `clip`, run after the adapter PDF exists in temp, before stamp/install.

5. **chezmoi**
   - One line on `highlights:`:

     ```yaml
     listen_command: sase-listen render {target} -e full -o {output}
     ```

   - No sase-listen config change. `auto_publish: true` already publishes article editions to Apollo's feed.

6. **docs**
   - `docs/highlights-ref-sync.md` listen-card section grows a "Generating audio" subsection.
   - README env table.
   - Clip doc: one paragraph.

7. **tests** (CLI, no live TTS)
   - Help alphabetical (`-L, --listen` after `--lib-dir`).
   - Dry-run with a fake `listen_command` that would `touch {output}` — assert it did not run, `writes: none`.
   - Fake renderer writes a tiny MP3 to `{output}`; create a local PDF target; assert dest PDF+MP3, marker contains `id` and (for URLs) `source_url`, pandoc not invoked.
   - `--listen` without config → exit 1, hint names `listen_command`.
   - `--listen --audio` / `--listen --no-audio` → clap conflict.
   - HTML URL → hint contains `clip`.
   - arXiv rewrite unit tests.
   - Config parse + env override.
   - Clip `--listen` dry-run prints the argv.

No live Gemini in CI. The fake renderer *is* the integration test.

---

## 9. Is this a good idea?

Yes. The vault already tracks what Bryan highlights. It does not yet track what he *hears*, except when a research swarm left a library MP3 that create happened to discover. `--listen` closes that loop with one gesture he will actually use:

```bash
bob highlights create https://arxiv.org/abs/2608.25174 --listen
```

That command should: fetch the real paper (not the abstract), stamp a Highlights marker, fill the room with sase-listen's checklist, drop PDF+MP3 in `xlib/papers/`, publish the full edition to AntennaPod through the feed he already subscribed, and let tonight's Mac scan write `ref/papers/2608.25174.md` with a player under the PDF task.

The adjustments above keep that gesture intuitive (one flag, one template, targets that look like sase-listen's), reliable (plan → TTS → stamp, fail closed, no shell, no note-writer race), and beautiful (live renderer, original paper PDF, papers/ not chat/, inherited color, no JSON sidecar).

Follow-ups, not v1: `{pdf}` to skip the second fetch; Mac-only `--scan`; arXiv rewrite inside `clip` even without `--listen` so `clip https://arxiv.org/abs/…` stops capturing abstracts (do this in the same PR if it stays small — it is the same `arxiv.rs`).
