# Mini daily dashboard for Obsidian daily notes

Research: how to render a compact daily-statistics dashboard at the bottom of
daily files, inspired by `dash_stats.md`, that costs less space and less
open-time. Ends with a recommended solution.

Observed context: `dash_stats.md` is a 16-line note whose body is one empty
` ```bob-stats ` fence. It renders six headline tiles (Worked, Reviewed, Done,
Created, Net flow, Review closed), a focus chart with typical-range band and
rolling median, day detail, and a "Where the time went" panel — roughly two
thousand vertical pixels (see `~/tmp/screenshots/20261024_145006.png`). Daily
notes live at `~/bob/2026/YYYYMMDD.md` (580 files in `2026/`), end with the
`## Pomodoros` section, and already embed one ` ```bob-plan ` block plus a
Dataview inline query in that heading. Vault is 3.8 GB.

## Bottom line

**Build it: a tiles-only `bob-stats` mini mode (3 tiles, 7-day sparklines,
"today so far" first), embedded at the bottom of the daily template.** No new
CLI surface, no new data engine, no daily logging habit. All new work is one
small render path in `bob-ledger-tools` plus a template edit. Details in
[Recommended solution](#recommended-solution).

## What `dash_stats.md` costs today

### Render anatomy (all read, no changes)

- Fence parsing + tile models + spark geometry live in
  `plugins/bob-ledger-tools/src/237-plugin-stats-models.js`
  (`statsParseFenceOptions` already accepts `range`, `metrics`, `focus`;
  unknown keys ignored; `statsOverviewIds` resolves which tiles to show).
- Block lifecycle in `.../src/238-plugin-stats-block.js`: `renderStatsBlock`
  paints a skeleton, then `apiStatsFetch` resolves `{report, stale, error}`.
  `renderStatsResult` **always** renders header (range chips, nav, compare,
  Custom, table toggle) + tiles + focus chart + context panels + footer.
  There is **no compact mode today** — a fence `metrics: [worked, done]`
  shrinks the tile row but still draws the full chart and panels.
- Data in `.../src/236-plugin-stats-data.js`: every fetch spawns
  `bob stats show -a -f json [-r range] [-o offset] [-c] [metric ids...]`
  (`statsBuildArgs`). Cache key is the full argv; LRU size 8
  (`STATS_CACHE_SIZE`). Stale-while-revalidate: a cached entry paints
  instantly as stale while one background spawn refreshes it; at most one
  spawn in flight, one coalesced follow-up; concurrent same-arg callers share
  the flight; timeout 20 s. Desktop `bob` resolution tries
  `stats.bob_path`, then `~/.cargo/bin/bob`, `~/.local/bin/bob`,
  `/opt/homebrew/bin/bob`, `/usr/local/bin/bob`, then PATH (macOS GUI has no
  shell PATH). **Spawning needs the desktop app** (`bobSpawnJson`:
  `"Spawning bob needs the desktop app."`) — on mobile the block renders an
  error card with Retry, never data.
- Revalidation triggers (`setupStatsBlock`): **any** `metadataCache`
  `"changed"` event repaints **all** mounted stats views (debounced 3 s,
  `STATS_REVALIDATE_DEBOUNCE_MS`), plus vault create/delete/rename, plus a
  1-minute rollover check. Each repaint with warm cache paints stale
  instantly and fires one background spawn.
- The engine contract is documented in `docs/stats.md` (metric catalog, JSON
  schema 1, honest states); the block contract in `docs/dashboard.md`
  (`dash_stats.md` = empty fence; Open Stats command opens it). Metric ids
  from `bob stats metrics`: `worked, reviewed, done, created, net, dropped,
  habits, keep_rate, review_time, sessions, review_closed`.

### Measurements (this host, 2026-10-24)

| Command | Wall | Output |
| --- | --- | --- |
| `bob stats -r 7d` (text overview) | 1.06 s | terminal glance |
| `bob stats show -a -f json -r 4w` | 0.45 s | 334,799 bytes |
| `bob stats show -a -f json -r 7d` | 0.41 s | 111,106 bytes |
| `bob stats show worked done -f json -r 7d` | 0.44 s | 52,259 bytes |
| repeat of the 7d full fetch | 1.73 s | same bytes |

Two findings: (1) **metric filtering does not speed up the CLI** (0.41 vs
0.44 s) — cost is dominated by the vault scan, not the metric count; JSON
size halves but wall time does not. (2) Wall time varies ~4x run to run on
this shared host (0.41–1.73 s), so any "renders faster" claim must rest on
architecture (cache hits, smaller DOM), not on one timing. Corpus note:
a `-r all` report is ~1.9 MiB / 1,093 closed sessions per `docs/stats.md`.

Real-data sanity check via `bob query` (Dataview, most recent `#daily`
notes, completed-task counts — matches the `done` tile's order of
magnitude):

| day | done |
| --- | --- |
| 20261024 | 10 |
| 20261023 | 13 |
| 20261022 | 4 |
| 20261021 | 8 |
| 20261020 | 14 |
| 20261019 | 11 |
| 20261018 | 10 |

### How daily notes render today (the perf baseline)

- ` ```bob-plan ` is rendered in-process from the Tasks API and metadata
  cache (no `bobSpawnJson` call in the plan path) — fast and spawn-free.
- The `## Pomodoros` heading carries a Dataview inline query over
  `this.file.tasks` — already a per-open scan of the note's own tasks.
- So **no subprocess runs to open a daily note today**. Embedding a stock
  ` ```bob-stats ` block would introduce the first spawn (~0.4–1.7 s,
  skeleton first, SWR after) into the most-opened page in the vault, plus a
  background respawn on nearly every edit (debounced 3 s) for as long as the
  note is open. That is the design's central risk, and it is fixable (see
  revalidation policy below).

## Options

| | Vehicle | Space | Open-time cost | Reliability | Beauty / fit |
| --- | --- | --- | --- | --- | --- |
| A | New `bob-stats` mini mode (tiles only, fixed 7d) | 1 row, ~120 px | 1 background spawn/day-open; instant after (SWR) | Reuses honest states, skeleton, error card | Same tile chrome as Stats page |
| B | DataviewJS via `bob-ledger-tools` api | 1 row possible | Re-runs on every vault change, no debounce | Hand-rolled states; breaks if api shifts | Custom CSS to match |
| C | Static snapshot written by rollover/nightly | ~5 lines text | Zero | Stale intraday; writer + backfill to build | Plain text, no sparks |
| D | `![[dash_stats]]` embed or link | Embed: full page; link: 1 line | Embed pays full cost | Free | Embed duplicates page; link gives no glance |
| E | Do nothing | — | — | — | Weekly prune stays manual |

Notes:

- **A reuses the most machinery**: fence parsing, `statsOverviewIds`,
  tile/spark models, SWR cache, in-flight sharing, skeleton, error model,
  the existing fixture/preview harness
  (`scripts/preview-stats-block.cjs`, `test-ledger-tools-stats-*.cjs`).
  New code is one render branch + CSS, in one repo, deployed by the existing
  `bob plugins sync` path.
- **B looks cheap but is the worst performer**: DataviewJS re-evaluates on
  vault changes without the 3 s debounce and without flight-sharing, and it
  duplicates tile/spark/error rendering by hand.
- **C is the only zero-render-cost option**, but "today so far" is the
  whole point of a dashboard on today's note (the engine already labels
  today provisional and computes intraday values — the text overview prints
  `today so far - Worked 3h 05m ...`). A frozen-yesterday snapshot answers a
  different question. C also needs a new writer, backfill, and conflict-safe
  vault writes — more new machinery than A, for a worse answer.
- **D-embed** should be rejected explicitly: it renders the full ~2000 px
  page inside every daily note and doubles spawn load for zero benefit.

## Critique: is this a good idea?

Yes — with the adjustments below. Reasons:

1. **The glance has a real job.** The weekly prune already says "check hours
   and created vs closed" by eye; a 3-tile strip moves that check from a
   destination page to the page Bryan already stares at.
2. **The engine already answers the intraday question.** Tiles carry
   sparklines with the provisional-today bar, and the CLI prints "today so
   far". No new metrics, no new logging.
3. **Risks are bounded and known**: one extra spawn per note-open (SWR makes
   it background + once), one extra repaint source (fix with mini-specific
   revalidation policy), mobile (fix with quiet fallback), 580 old notes
   (fix by template-only rollout).

The main trap to avoid: copying `dash_stats.md` thinking ("it renders, just
embed it"). The full block — range chips, chart, day detail, Where-the-time
went, keyboard handlers — is a destination page, not a footer. Shrinking it
with CSS alone keeps all the cost and interaction surface. The mini must be a
render branch, not a stylesheet.

## Explicit requirement adjustments

1. **Lead with "today so far", not /day averages.** Tiles headline the
   window average (`4h 10m /day`). On a daily note the first question is
   "how is today going". Mini tiles headline today's value, keep the 7-day
   spark for context, and keep the delta line. No engine change: the report
   already ships daily buckets including provisional today.
2. **Three metrics, fixed, fence-overridable.** Default
   `metrics: [worked, done, created]` at `range: 7d` — the prune's "hours
   and created vs closed" in one row. (`net` is derivable at a glance;
   `review_closed`/`reviewed` belong to the morning review, not the footer.)
3. **No controls, no chart, no panels, no table.** Mini is read-only glance;
   every tile links to `dash_stats` for drill-down. This is where the space
   and DOM savings come from.
4. **Template-only rollout.** Add the fence to the daily template
   (`~/bob/_templates/daily.md`) so only new days get it. Do not rewrite the
   580 existing daily notes — git noise with zero benefit.
5. **Mini-specific revalidation: focus/rollover, not keystroke.**
   The stock block repaints on every metadata change (3 s debounce). A block
   living in the note being actively edited would respawn `bob stats`
   all day. Mini keeps the SWR cache but revalidates on window focus,
   explicit retry, and day rollover — not on `metadataCache changed`.
   Stale-by-minutes is fine for a glance; the Stats page stays live.
6. **Quiet mobile fallback.** Stock behavior is an error card with Retry.
   Embedded in every daily note, that card would shout daily on mobile.
   Mini renders one muted line ("Stats · desktop only") linking to
   `dash_stats`, no `role=alert`, no retry button.
7. **No targets, streaks, or goals.** The system deliberately has no numeric
   reopen triggers that need daily scoreboard pressure; keep it a mirror,
   not a scoreboard. No new CLI flags, so `cli_rules.md` imposes nothing;
   docs touch `docs/dashboard.md` (child-page contract) only.

## Recommended solution

Add a mini render branch to the existing `bob-stats` block in
`bob-plugins`, and a 5-line fence at the bottom of the daily template.

**Fence** (appended after the Pomodoros section by the template):

    ```bob-stats
    mini: true
    metrics: [worked, done, created]
    range: 7d
    ```

**Plugin work** (`plugins/bob-ledger-tools/src/`, fragments build —
never hand-edit `main.js`; `npm run build` + `npm run build:check`;
`AGENTS.md`-mandated `bob plugins sync` after):

1. `237-plugin-stats-models.js`: accept `mini` in `statsParseFenceOptions`
   (boolean, default false; unknown keys already ignored so this is
   backward-compatible).
2. `238-plugin-stats-block.js`: in `renderStatsBlock`, when
   `fence.mini`, skip header controls/chart/panels/table/keyboard; render
   tiles-only with today-first headlines + a `Stats ↗` link tile-footer to
   `dash_stats`. Mini views skip the `metadataCache changed` revalidation
   path (keep rollover + focus + retry); reuse `statsCacheStore`,
   `apiStatsFetch`, skeleton, and error model, with the quiet mobile
   fallback from adjustment 6.
3. `styles.css`: `.bob-stats-mini` — one responsive row, same tile hues and
   spark geometry; narrow-pane wrap to a compact column.
4. Fixtures + preview: extend `scripts/fixtures/stats/` (mini case incl.
   all-null and mobile-no-spawn states) and `preview-stats-block.cjs`
   matrix; add to `test-ledger-tools-stats-block.cjs`.
5. Template: append the fence to `~/bob/_templates/daily.md` (vault file,
   not repo). Docs: note the mini contract in `docs/dashboard.md`.

**Phased plan**: (1) mini branch + preview screenshots, dark/light +
narrow; (2) template edit, live on new daily notes for a few days;
(3) revalidation/mobile review from real use; (4) backfill old notes only
if asked — default no.

**Acceptance**: first open of the day shows skeleton then tiles with zero
interaction blocked (spawn is background); second open paints from cache
with no spawn; typing in the note fires no spawn; mobile shows one muted
line; `just check`-equivalent gates in both repos pass
(`npm run validate` for plugins; repo's `just docs-check` if dashboard docs
change).

## Evidence and provenance

- Screenshot: `~/tmp/screenshots/20261024_145006.png` (full Stats page).
- Vault: `~/bob/dash_stats.md`, `~/bob/dash.md` (Tasks-api + ledger-api
  dataview precedent), `~/bob/2026/20261024.md`,
  `~/bob/_templates/daily.md`.
- Plugin: `plugins/bob-ledger-tools/src/236-plugin-stats-data.js`
  (spawn/SWR/cache), `237-plugin-stats-models.js` (fence/tiles/sparks),
  `238-plugin-stats-block.js` (lifecycle/render), `docs/bob-ledger-tools.md`.
- Engine: `docs/stats.md`, `docs/dashboard.md`, `src/native/stats/`,
  `bob stats metrics`.
- Decisions honored: `today-is-read-from-the-ledger` (read-time
  derivation, no stored state), `bob-cli-releases-ride-a-daily-train`
  (no CLI change needed at all), and the scoreboard warning from the prior
  daily-stats research (mirror, not scoreboard).
