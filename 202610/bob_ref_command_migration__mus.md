# `bob highlights` → `bob ref`: research and recommended implementation

Researcher: mus (independent swarm report, `__mus` suffix).
Date: 2026-10-06. Scope: help decide the best way to migrate the
`bob highlights` command to a new `bob ref` command that keeps every
existing subcommand and adds read/tracking/annotations visibility for
agents recommending reading material and for reading Highlights-app
annotations. Ends with a recommended solution.

All code paths below were read in this workspace checkout
(`src/native/highlights_ref/`, `src/runner.rs`, `src/native/completion/`,
`docs/highlights-ref-sync.md`, `docs/highlights-clip.md`) and checked
against the live vault (`~/bob/ref`, `~/bob/lib`) and `bob query`.
Nothing in any peer swarm report was consulted.

## 1. What `bob highlights` is today

- **Six subcommands**, all native Rust under `src/native/highlights_ref/`
  (~20 modules plus `tests/`): `clip`, `create`, `doctor`, `marker`,
  `scan`, `sync`. CLI construction lives in
  `src/native/highlights_ref/cli.rs`; dispatch in `mod.rs`
  (`COMMAND_NAME = "bob highlights"`); registration in `src/runner.rs`
  (`name: "highlights"`, `NativeCommand::Highlights`); shell completion
  reuses the same `build_cli()` via `src/native/completion/tree.rs`.
- **Pipeline**: `create`/`clip` write intake PDFs into `xlib/<ref-type>/`
  with a page-1 `/Text` marker annotation; `scan` moves intake into
  `lib/<ref-type>/` (with sidecars, TextBundles, companion audio) and
  writes/updates `ref/<ref-type>/<stem>.md`; `sync`/`marker` handle one
  PDF; `doctor` checks prerequisites. Marker write-back to PDFs is
  opt-in (`--write-pdf` / `--write-pdfs`). Full contract in
  `docs/highlights-ref-sync.md` (~900 lines) and `docs/highlights-clip.md`.
- **Config surface**: `BOB_DIR`, `BOB_HIGHLIGHTS_LIB_DIR`,
  `BOB_HIGHLIGHTS_XLIB_DIR`, `BOB_HIGHLIGHTS_REF_DIR`,
  `BOB_HIGHLIGHTS_PRE_SCAN_HOOK` env vars plus `highlights:` keys in
  `bob/config.yml` (`pre_scan_hook`, `audio_library`,
  `audio_link_template`). The legacy `pre_scan_command` key is a hard
  error, i.e. renames have been breaking before and were deliberately
  made loud.
- **Operational coupling**: the MacBook 15-minute cron job
  (`maybe_bob_highlights_sync -w`, see `docs/vault-git-sync.md`) and the
  `bob_xlib_pull` pre-scan hook invoke `bob highlights scan` by name.
  Any rename must keep those working untouched.
- **Status model** (already the read/tracking/finished vocabulary the
  request wants): marker/frontmatter `status` ∈ `ready, next, wip,
  read, abandoned, legacy` (plus deprecated `unread→ready`,
  `done→read` aliases), bidirectionally reconciled with the `^ref` task
  checkbox (`[ ]=ready, [*]=next, [/]=wip, [x]=read, [-]=abandoned`).
  `legacy` has no checkbox and falls back to `[ ]`.
- **Vault reality** (measured this session via `bob query` against
  `~/bob/ref`, 590 notes): `read` 285, `legacy` 282, `abandoned` 17,
  `next` 5, `ready` 1, `wip` 0. Two facts fall out of this: (a) nearly
  half the corpus is `legacy` notes with heterogeneous frontmatter (old
  `url:`/`source_note:`/`source_path:` shapes, some without `ref_type`
  or pipeline fields — see e.g. `ref/ai/agent_ref/build_effective_agent.md`
  vs. generated `ref/blogs/netclode.md`), so any new listing command
  must degrade gracefully on legacy notes; (b) the tracking states the
  request wants (`next`, `ready`) are currently almost unused (6 notes
  total), so the "tracking / plan to read" workflow is greenfield
  behaviorally even though the states exist.
- **Annotations already sync**: Highlights text, comments, standalone
  notes, and TextBundle image selections render into the managed
  `<!-- highlights:begin/end -->` region as `[!quote]`/`[!note]`
  callouts with stable `^h-…` block IDs. Reading annotations is
  therefore a *rendering/reporting* problem over files that already
  exist, not a new sync problem — with one caveat (the known Highlights
  TextBundle creation bug documented in `highlights-ref-sync.md`:
  image-bearing PDFs sometimes never get a sidecar until a one-time
  manual export).

## 2. Critique of the plan

**The rename is a good idea.** "highlights" names a macOS app; the
command long ago outgrew it — `clip` (web articles), `create` (Markdown
→ PDF), chat transcripts, and papers have nothing to do with the
Highlights app. `bob ref` names the vault concept it actually manages
(`type: "[[ref]]"` notes, `ref_type` lanes, `ref/` directory), matches
how the glossary already talks about reference notes/tasks, and is
shorter for agents to invoke. The main use case is also real: an agent
recommending reading today must hand-roll `bob query` DQL over `ref/`
and know the status vocabulary, checkbox mapping, and legacy-note
gotchas — a dedicated command removes that tacit knowledge.

**But three adjustments are needed before this is shaped as "migrate":**

1. **It must be an alias-promotion, not a migration.** Project CLI
   rules (`sase/memory/cli_rules.md`) are explicit: never hard-rename
   or remove a command — the old spelling becomes a permanent hidden
   alias with byte-identical behavior and no deprecation output, and
   help/diagnostics print only the canonical path. `highlights` stays
   working forever (cron job, muscle memory, scripts, the
   `bob-cli--research` history that cites it). Cost is small: one extra
   runner entry plus clap alias wiring. Do not print deprecation
   warnings — they would break the cron log contract.
2. **Don't build a parallel query engine.** `bob query` (native
   Dataview DQL + Tasks) can already answer "what has Bryan read" and
   "what is queued" over `ref/` frontmatter — I verified both shapes
   this session. New `ref` reporting commands should be thin,
   opinionated views over the same frontmatter (status + ref_type +
   title + source), not a second query language. Anything fancier than
   filtering/sorting/limiting should just print the equivalent
   `bob query` invocation or defer to it.
3. **Don't add new state.** The request's "tracking / plan to read /
   finished" maps 1:1 onto existing states (`ready`/`next` = tracking,
   `wip` = reading, `read` = finished, `abandoned` = dropped) and the
   `^ref` checkbox already owns transitions through sync. Adding new
   frontmatter fields, new statuses, or state-changing `track`/`start`/
   `finish` subcommands would fork the source of truth (marker ↔
   frontmatter ↔ checkbox three-way merge is already the most delicate
   code in the module) and collide with the `review-walk-is-tiered`
   decision, under which REFERENCES-lane review already walks
   unstamped references on the reference cadence. The new surface
   should be **read-only views**; state changes keep flowing through
   the existing gesture (checkbox edit + `scan`/`sync`).

A further caution: the existing subcommand names (`scan`, `sync`,
`marker`, `doctor`, `clip`, `create`) are pipeline jargon. Keeping them
byte-identical under the alias is required, but the new read-only
commands are the chance to use plain verbs (`list`, `show`,
`annotations`) so agents can guess them.

## 3. What the new commands should be (adjusted requirements)

Proposed minimal set — all read-only, all with `--format json`
(or `--json`) for agents plus colored human output per CLI rules:

| Command | Purpose | Notes |
| --- | --- | --- |
| `bob ref list [--status S]... [--ref-type T]... [--limit N] [--sort FIELD] [--format json]` | Answer "what has he read / what's queued" | Filter on the six statuses + `unread`/`done` aliases; group or column for `ref_type`; must include legacy notes with blank columns rather than skipping them; default sort stable (path order, like scan) |
| `bob ref show <note-or-pdf>` | One reference's metadata + reading state | Accept either `ref/…md` path or `lib/…pdf` path (or bare stem); print resolved pair, status from all three sources (marker, frontmatter, `^ref` checkbox) when they disagree, provenance (`source_url`/`author`/`published`/`captured`), annotation count |
| `bob ref annotations <note-or-pdf> [--format json\|markdown]` | Read Bryan's annotations | Render from the **note's managed region** (already synced, no PDF/sidecar parsing, works offline on any host); each item: page, kind (highlight/comment/standalone/image/removed), text, comment, `^h-…` block id. Never re-parse the sidecar — that keeps one parser and avoids the TextBundle-missing failure mode surfacing in a read path |

Explicitly **out of scope** (at least initially): state-changing
tracking commands; full-text search inside annotation bodies (Dataview
`query` covers it); renaming `BOB_HIGHLIGHTS_*` env vars or
`highlights:` config keys (see §4); renaming the `highlights_*`
frontmatter pipeline fields (they are load-bearing merge state
referenced by tests and old notes — renaming them buys nothing and
risks the base/hash reconciliation).

## 4. Implementation notes (from the code)

- **Alias mechanics**: register `ref` as the canonical runner entry and
  keep `highlights` as a hidden alias with byte-identical behavior
  (runner + `NativeCommand::Highlights` dispatch + completion tree +
  `COMMAND_NAME` in help/diagnostics printing only `bob ref`). Keep
  `subcommand_required(true)` and the existing six subcommand names and
  flags byte-identical, including short flags (`-d/-w/-n/-j/-v/-p`)
  which CLI rules require. Keep the parent-level `--no-hooks`
  accepted-and-ignored semantics for `create`/`marker`/`sync`.
- **Config/env**: the safest course is to leave `BOB_HIGHLIGHTS_*` and
  `highlights:` keys untouched (canonical command renames do not
  require config renames; the cron job and MacBook setup keep working).
  If new `ref:` keys are desired, accept both with `highlights:` as
  fallback — never a hard rename (the `pre_scan_command` hard-error
  precedent shows how much breakage a rename causes). Same for
  `highlights:begin/end` body markers and `highlights_*` frontmatter:
  leave them; they are format, not branding.
- **Docs**: `docs/highlights-ref-sync.md` and
  `docs/highlights-clip.md` stay as the pipeline contracts; add a short
  `docs/ref.md` (or extend README command table + `getting-started.md`
  row) documenting only the new read-only commands plus the
  `status → meaning` table agents need. Every code example in docs that
  invokes the command should use the canonical `bob ref` spelling for
  new commands while pipeline examples keep working under both.
- **Completion**: new subcommands register in the same `build_cli()`
  so `bob <TAB>` and `bob completion` pick them up; keep alphabetical
  order within the group and short aliases on every new long option.
  `bob ref` itself stays in the Integrations section (it is still the
  Highlights/PDF pipeline); do not move sections as part of this change.
- **Tests**: existing `tests/cli/highlights/*` suites must pass
  unmodified (they pin the alias behavior); add new suites for
  `list`/`show`/`annotations` covering: legacy-note tolerance, the
  status-alias normalization, marker/frontmatter/checkbox disagreement
  display, sidecar-less and annotation-less notes, and JSON shape
  stability. Note the suite needs the `BOB_NOW`-style determinism the
  module already uses for `created`/`highlights_synced_at`.
- **Cross-repo**: no `bob-mac-capture` coordination needed — it is a
  thin client of the capture grammar/JSON interfaces, not of
  `highlights`. No vault-format change, so no plugin changes.
- **Performance**: `scan` already parallelizes (`--jobs`); `list` over
  ~590 notes is a frontmatter scan, trivially fast, but it should read
  notes directly rather than shelling to `bob query` so output stays
  stable and offline-safe.

## 5. Recommended solution

1. **Promote `bob ref` as the canonical name; keep `bob highlights` as
   a permanent hidden alias** with byte-identical behavior and no
   deprecation output (CLI-rules compliant). Help, diagnostics, logs,
   and all new docs print only `bob ref`.
2. **Move all six existing subcommands unchanged** under the canonical
   name. Change zero flags, zero config keys, zero env vars, zero
   frontmatter fields, zero body markers in this step. The cron job,
   pre-scan hook, and MacBook setup keep working with no edits.
3. **Add three read-only subcommands**: `ref list`, `ref show`,
   `ref annotations`, each with human-colored and `--format json`
   output, per the table in §3. These are the entire agent-facing
   "what has he read / what's queued / what did he annotate" surface.
4. **Document the tracking workflow instead of building it**: `ready` →
   queue, `next` → up next, `wip` → reading, `read` → finished, driven
   by the existing `^ref` checkbox + `scan`/`sync` round-trip, reviewed
   in the REFERENCES tier of the morning walk. Revisit state-changing
   helpers only if Bryan reports friction after a month of the
   read-only commands.
5. **Verify**: full existing highlights suites green via both spellings,
   new suites for the three commands, `just check` (or the repo's
   configured gate), plus a live-vault dry check (`ref list --status
   read`, `ref show` on one generated and one legacy note,
   `ref annotations` on an annotated note) confirming legacy tolerance.

Net assessment: yes, do it — the rename is justified and the
agent-reading-list use case is real — but keep the change surface
small: new canonical name + hidden alias + three read-only views, and
nothing else moves.
