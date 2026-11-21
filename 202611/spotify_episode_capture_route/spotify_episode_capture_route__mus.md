# Smarter `bob ref create` for Spotify URLs — research report

Researcher: mus · 2026-11-21 · for `bob#^smarter-spotify-refs`
Related: `bob#^auto-spotify-record-notes` (link Spotify URLs to podcast records)

## TL;DR

Yes, do it — but as a small dedicated **Spotify route** (episode first, show
second), not as adapter tuning. The generic web-article engine is the wrong
tool for `open.spotify.com`: the pages are a JS shell, so today's capture
produces a near-empty PDF keyed under an opaque 22-character filename with no
author, no date, and share-link query junk in `source_url`. A browser-free
route that fetches the page HTML and reads its `<meta>` tags (exactly as the
existing arXiv route does with its API) fixes all of that with no new auth,
no browser, and no template magic. Keep everything else — dedupe, reread,
overwrite, `--listen`, intake — untouched by reusing the existing machinery
through a canonical dedupe key.

Recommended scope: `episode/` + `show/` URLs now; `track/`/`album/`/
`playlist/`/`artist/` refuse with a clear hint until Bryan asks. No Spotify
OAuth, no transcript fetching, no new ref type, no automatic podcast-record
linking in the same change.

## What Spotify refs look like today

Example: `ref/blogs/4ugvfwty2i8hgagsvt7pjc.md` (task `sase#^ref-4ugvfwty2i8hgagsvt7pjc`),
from `https://open.spotify.com/episode/4UgVFWty2I8hGAgSvT7pjC?...`:

- Ref-note frontmatter: `ref_type: blogs`, correct `title`, but **no `author`,
  no `published`**, and `source_url` retains share params
  (`?si=...&sci=spotify%3Acard-config%3A...`).
- The Highlights section is empty (`<!-- highlights:begin -->` … nothing).
- The installed PDF (`lib/blogs/4ugvfwty2i8hgagsvt7pjc.pdf`, 44 KB) contains
  exactly **two text objects** — the title and a frontmatter dump — plus the
  episode cover image and link annotations. The full episode description
  (2.7 KB, sponsors, summary, 16 timestamps, related-episode links) that
  Spotify serves in plain HTML is entirely absent.
- The filename stem is the lowercased Spotify ID, not a human name.

So the ref "works" (it files, it dedupes itself, the task closes) but the
artifact is decorative: nothing to read, nothing to highlight, nothing to
search. For a podcast episode the description-with-timestamps *is* the
article, and we throw it away.

## Issues found (each verified)

1. **Wrong engine for the page shape.** `target.rs::fetch_and_route` sees
   `text/html` 200 and sends every Spotify URL down the web-article route
   (`create_article_route` → adapter `capture` → headless-browser reader
   mode). Spotify's page is a JS app shell; reader mode extracts the chrome
   and misses the server-rendered `<meta>` payload. Evidence: the PDF above;
   contrast with `curl` returning the complete description, title, image,
   duration, and release date with no browser at all.
2. **Opaque IDs become filenames.** `clip_url.rs::stem_from_url` falls back
   to the URL slug, and `is_hex_id_word` only matches `[0-9a-f]`. Spotify IDs
   are base62 (`4UgVFWty2I8hGAgSvT7pjC` contains g/h/i/s/t/u/v/w…), so the
   "opaque" guard never fires and the 22-char ID becomes the stem, the note
   name, the PDF name, and (via `reference-ids-follow-file-stems`) the
   reference id. Compare arXiv, which never lets `2602.16844` near a
   filename. Human cost is real: ref tasks read as alphabet soup in plans
   and the walk.
3. **Share params pollute identity.** `validate_and_clean` strips `utm_*` et
   al but keeps Spotify's `si`, `sci`, `nd`, `dlsi`. The example's stored
   `source_url` still carries `si` + `sci`. Consequence: the same episode
   shared from two devices (different `si`) gets two dedupe keys and two
   refs. Canonical identity should be
   `https://open.spotify.com/episode/<id>` (case-preserved in display,
   normalized for dedupe).
4. **Metadata left on the floor.** The adapter returns no author/published
   for Spotify pages, so the note ships without them — yet the page carries
   `og:title`, full `description`, `og:image`, `music:duration` (5197 s),
   `music:release_date` (2026-11-18T18:08:00Z), `og:audio` (30 s preview
   MP3), and the show link (`/show/2Bho9xCbOQMWMJ7UKmqCzD`). A show page
   additionally carries show title, host line, and its own description.
5. **Multi-episode sets can't name themselves.** `docs/highlights-create.md`
   already admits "a Spotify set whose slugs share no meaningful start"
   needs `-N`. With ID slugs that is *every* Spotify set. Title-derived
   stems fix the single case; collections additionally need a show-aware
   fallback (shared show → `<show>_<date-or-count>`), else keep the `-N`
   requirement honestly.
6. **Browser dependency for a browser-less job.** Today's route needs `uv`
   + Chrome/Playwright and up to 300 s of adapter time for a page whose
   useful bytes arrive in one `curl`. On hosts with no browser this fails
   closed with a hint — for zero benefit.
7. **Beauty gap.** Even the parts that survive (title + cover) render in the
   generic article template: no show attribution, no duration/date line, no
   chapter list from the timestamps, no "Play on Spotify" affordance. An
   episode PDF should read like liner notes, not a broken article print.

## Recommended design

Mirror `arxiv.rs`, the codebase's own precedent for "one host deserves a
route": syntactic recognition → dedicated metadata fetch → dedicated PDF
build → existing install/dedupe/intake machinery.

### 1. Recognize: `spotify.rs` beside `arxiv.rs`

- Parse `open.spotify.com/<kind>/<id>[?...]`, kinds `episode`, `show`,
  `track`, `album`, `playlist`, `artist` (and `spotify:` URIs → canonical
  HTTPS form for display). Only `episode` and `show` proceed; the rest get
  `unsupported Spotify URL kind … (only episodes and shows are captured;
  save the page and pass --html FILE)` — the same shape as today's
  unsupported-content-type errors.
- Canonical display URL: scheme + host + `/<kind>/<id>`, fragment and
  `si`/`sci`/`nd`/`dlsi`/`utm_*` stripped. Dedupe key: same, lowercased
  host, no trailing slash. This plugs into `collect_recorded_source_urls` /
  `check_dedupe` / reread / overwrite with no new machinery, and fixes
  issues 2–3 in one move.
- Stem: `title_stem(episode title)` (existing helper), falling back to
  `show_stem + date` when the title is missing. Never the raw ID. This
  aligns with `reference-ids-follow-file-stems` instead of fighting it.

### 2. Fetch: plain HTML, no browser, no auth

- Reuse `fetch::fetch_url` into scratch (20 s budget, arXiv-style), then
  parse `<meta>` tags in Rust (no new dependency: string/regex scan of
  `og:title`, `name="description"`, `og:image`, `og:url`, `music:duration`,
  `music:release_date`, `og:audio`, first `/show/<id>` link for episodes).
- Degrade like `fetch_metadata` does: metadata failure warns and continues
  (title-only fallback), never hard-fails the capture. If Spotify changes
  its markup, the route fails back to today's article engine with a
  `warning:` line rather than erroring — the adapter stays the safety net,
  it just stops being the default.
- Do **not** call the Spotify Web API. It needs OAuth, token storage, and
  renewal — a whole new secret lifecycle for data the public page already
  hands out. (Bryan's `sase-spotify` agent access is a chat-tool grant, not
  a daemon credential `bob` may reuse; and its skill forbids agents from
  touching the login file. Keep that boundary.)
- Do **not** fetch transcripts. Coverage is uneven, provenance is murky,
  and a 90-minute transcript dwarfs the liner-notes PDF this feature owns.
  The description's timestamp list already yields chapters (16 timestamps
  in the example). Revisit only if Bryan asks.

### 3. Render: an episode liner-notes template, not an article print

Required elements (all from verified meta fields):

- Hero: cover (`og:image`), episode title, show name linked to the show
  URL, one metadata line: `Show · 1h 26m · Released 2026-11-18 · Listen on
  Spotify (link)`.
- Description body with `MM:SS`/`H:MM:SS` timestamps converted to a chapter
  list (or inline bold lead-ins where the description is prose-first).
- Links section: every `https://` in the description as a real annotation
  (penname, newsletter, sponsor links in the example), so `bob ref code`
  / `bob ref links` keep working — per `code-copy-reads-render-time-catalog`,
  the render-time catalog is the contract, so the new template must emit
  its links/code spans through the same path the article template uses.
- Footer: canonical URL + captured stamp (same provenance line as today).

Explicitly out: binding the `og:audio` 30-second preview as companion
audio. A 30 s teaser filed as *the* episode audio will mislead every
downstream reader (`--listen` narration, feed publishing, "has audio"
badges). Mention the preview URL in the PDF instead. `--listen` keeps
working unchanged for full narration.

For `show/` URLs: one page with show art, show description, and a
"latest episodes" line is enough for v1 — or refuse-and-hint if the show
page's episode list proves markup-fragile during implementation. Do not
gold-plate a show directory.

### 4. Fit with existing contracts (do not renegotiate them)

- `ref_type` default stays `blogs`; `-t` override unchanged. No new top
  level type, no migration, no `lib/` reshuffle. (If Bryan later wants
  `lib/podcasts/`, that's a separate migration, not this feature.)
- Marker: map show name → `author`, release date → `published`
  (semantically honest: the podcast *is* the author line). If duration/show
  URL deserve frontmatter keys, that means extending `MARKER_EXTRA_ORDER`
  in `stamp.rs` plus every marker reader — price it during implementation
  and prefer body-only rendering if the touch-list sprawls. Do not smuggle
  new keys past `compose_marker`'s ordering.
- `--html` replay, `-A`/`-p` overrides, `-d` dry run, `-o`, `-k`, `-f`
  reread/overwrite, `--audio`, `--listen`, collections: all keep working
  because the route reuses `plan_default_target`, `TargetPlan`, and the
  install sequence. Dry run prints the same `source:`/`author:`/
  `published:` lines, now populated.
- `bob ref scan`/`sync`/`doctor`: add one doctor row only if the route
  gains a health-checkable dependency — it has none (plain HTTPS), so
  probably no row. Say so in the plan.
- Mac contract (`mac-capture-is-a-thin-client`): unaffected — Mac renders
  what `bob` returns; template-internal link spans are already the
  currency. No cross-repo change; still, flag the template in the
  `bob-mac-capture` direction only if annotation anchor shapes change
  (they shouldn't).

### 5. Tests and docs (implementer must)

- Unit: URL grammar (each kind, `spotify:` URIs, junk params stripped,
  dedupe-key canonicalization incl. case/`si` variants), base62-ID
  opaqueness (regression test for issue 2: `4UgVFWty2I8hGAgSvT7pjC` yields
  `None` from `stem_from_url`), meta-parse fixtures from a saved episode
  page + a show page, timestamp→chapter conversion.
- CLI: dry-run golden lines for an episode URL (stub fetch at the
  `fetch_url` seam, following the arXiv test pattern), plus the
  track-kind refusal hint test.
- Docs: `docs/highlights-create.md` — Spotify joins the TARGET list
  alongside arXiv with its own short section; move the "Spotify set needs
  `-N`" caveat to resolved-or-restated. The implementer must read the
  `cli_rules` and `docs` memory strands first (new-URL-kind help text and
  `docs/` edits both touch governed contracts).

## Critique of the request (is this a good idea?)

Yes — with three adjustments:

1. **Lead with episodes, not "Spotify URLs" in general.** The vault need
   is podcast episodes (Bryan's actual refs + the `podcast_ref.md` legacy).
   Tracks/albums/playlists are music-library objects, not reading material;
   capturing them as PDFs is category confusion. The plan above says so
   explicitly instead of promising a universal Spotify handler.
2. **"Beautiful" should mean liner notes, not article fidelity.** Chasing
   pixel-parity with Spotify's web player (embed iframe look, dynamic
   widgets) is how we got the current empty PDF. The Bob-owned print
   template is the beauty lever: typography, cover, chapters, links.
3. **Don't couple to podcast records.** `^auto-spotify-record-notes`
   (auto-linking refs to `podcasts/` records) is a separate detection +
   data-model change. Ship the capture fix first; record-linking reads the
   new `author`/show fields later. One bead per idea.

What I'd refuse: OAuth in `bob` (secret lifecycle for public data),
transcript scraping (weight + rights + flakiness), a `podcasts` ref type
(migration cost, zero retrieval benefit while the corpus is small), and
adapter-side heuristics ("if host is Spotify, regex the HTML") — host
special-casing inside the generic browser engine is exactly how the
current failure hides. A named route with named tests is cheaper to own.

## Alternatives considered and rejected

| Option | Verdict |
|---|---|
| Tune the web-clip adapter for Spotify (selectors, waits) | Still a browser for static HTML; slow, flaky, host-fragile |
| oEmbed only (`/oembed?url=`) | Verified thin: title + thumbnail + iframe, no description/duration/date |
| Spotify Web API + OAuth | Richest data, but new secrets/renewal; unjustified for public meta |
| Manual `-T`/`-A`/`-p` flags (document, don't build) | Works today, keeps every future capture equally broken |
| Full-episode audio/transcript capture | Out of scope: DRM, size, rights; description + chapters suffice |

## Open questions for Bryan (small, answerable)

1. Keep `blogs/` as the home for episode refs, or mint `podcasts/`? (I
   recommend staying put.)
2. For `show/` URLs: minimal show card (my v1) or refuse-with-hint until
   episodes prove the route?
3. Should a 5+-episode set from one show auto-name from the show
   (`<show>_<n>-episodes_<date>`), or is keeping the explicit `-N`
   requirement fine?

## Evidence appendix (observed, not inferred)

- `open.spotify.com/oembed?url=…episode/4UgV…` → JSON: `title` "Software
  factories and code reviews with Harjot Gill", `thumbnail_url`
  `image-cdn-fa.spotifycdn.com/…`, `type: rich`. No description, duration,
  or date. (Show-URL oEmbed returned episode-titled payload in one probe —
  another reason not to build on oEmbed alone.)
- Plain `curl` of the episode page (228 KB) → `og:title`,
  `name="description"` (2,686 chars incl. 16 `MM:SS` timestamps),
  `music:duration=5197`, `music:release_date=2026-11-18T18:08:00Z`,
  `og:audio` 30 s MP3, `og:image`, show link `/show/2Bho9xCbOQMWMJ7UKmqCzD`.
- Installed PDF for the example ref: 2 text objects (title + frontmatter
  dump), cover image, 5 link annotations (episode/show/turbopuffer links).
  Ref note Highlights block empty; frontmatter `author`/`published` absent.
- Code: routing in `src/native/highlights_ref/target.rs::fetch_and_route`;
  stem rules in `clip_url.rs` (`is_hex_id_word` hex-only);
  article flow in `clip.rs::capture_article`; arXiv precedent in
  `arxiv.rs`; marker key order in `stamp.rs::MARKER_EXTRA_ORDER`;
  collection caveat in `docs/highlights-create.md`.
