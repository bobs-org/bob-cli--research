# Daily-note mini stats: a day-mirror strip, not a nested dashboard

> **Research query:** How should Bob render a compact, fast, beautiful mini-dashboard of daily statistics at the bottom of canonical daily notes, inspired by `dash_stats.md` / the `bob-stats` block, without slowing the file Bryan opens all day? Is putting a stats dashboard on the daily note a good idea? What should change in the requirements? What is the recommended solution?

**Researcher:** grk (independent swarm report).  
**Date:** 2026-10-24.  
**Inputs:** `dash_stats.md`, screenshot `~/tmp/screenshots/20261024_145006.png`, `_templates/daily.md`, today's ledger `2026/20261024.md`, `docs/stats.md`, `docs/dashboard.md`, bob-ledger-tools stats/plan sources, prior consolidated research `202610/bob_daily_stats/bob_daily_stats.md`, vault + plugin inventory.

## Bottom line

**Build a two-row day-mirror strip. Do not embed `dash_stats`.**

The full Stats page is a weekly instrument. Its tiles report window means (`4h 10m /day`, `▼ 17%`), it draws a focus chart, a day-detail panel, and a "Where the time went" drill-down, and it revalidates by spawning `bob stats show -a -f json` (~180–370 ms, ~221 KB for 4w). Putting that object at the bottom of the daily note Bryan keeps open all day would be slow, tall, and a scoreboard. The original Stats research already named that failure mode as requirement **R9**: home interpretation in the weekly prune, because daily is where numbers become targets.

A *day-mirror strip* is a different product, and it is worth building:

1. **Same engine, new layout.** Extend the existing `bob-stats` fence with `layout: day`. The plugin keeps calling `apiStatsFetch` (schema-1 JSON, LRU cache of 8, stale-while-revalidate). The renderer paints this day's point, not the window headline.
2. **Speak `bob-plan`'s chip language**, not the Stats tile-card language. Plan chips already live at the top of the daily note (forward: TODAY / PENDING / NEXT / READY). The strip sits after `## Pomodoros` (rear-view: what this day has become).
3. **Cap it at ~96 px and six facts.** No range chips, no focus chart, no table, no deltas, no targets. Click **STATS ↗** to open `dash_stats` with this day pinned — the inverse of the page's existing **Open daily note**.
4. **Change the revalidation policy for day layout.** Today's daily note is the hottest file in the vault. The current Stats block throttles a full `bob` spawn to once per 3 s of *any* metadata-cache `changed` event. That is acceptable on a page you visit. It is not acceptable on a page you edit all day.

This honors the screenshot's beauty (metric hues, hollow-today spark, area bar, honest `–`) while taking perhaps a twelfth of the vertical space and sharing the fetch already paid if Stats is open.

## Is this a good idea?

**Yes, if it is a mirror of this day's ledger. No, if it is a nested `dash_stats`.**

### Why a daily strip earns a place

- Bryan already asks these questions mid-day. The Pomodoros heading runs a Dataview inline query that sums `[t::]` on closed rows — that is `worked`, computed a second way. The weekly prune in `gtd_daily.md` says to check Stats for hours, created vs closed, and keep rate. A strip at the bottom of today is the mid-day peek at those same facts without leaving the ledger.
- The doing surface and the planning surface are already split: `bob-plan` at the top of the daily note, ten badges on `dash.md`, the review footer in the status bar, the full instrument on `dash_stats.md`. The daily note is missing only the *retrospective* glance. That hole is real.
- The engine, JSON contract, hues, quality flags, and cache already exist. The incremental work is a layout, a revalidation policy, a template fence, and CSS. That is a plugin change plus three lines in `_templates/daily.md`. It is not a new stats engine.
- Self-monitoring helps when the data is already there (Harkin et al., 2016, *Psychological Bulletin*, d ≈ 0.40). The vault already holds the minutes, completions, creations, and review journal. The strip adds no logging habit.

### Why the naive plan fails

| Risk | Evidence in this vault | What goes wrong |
| --- | --- | --- |
| **Nested weekly dashboard** | Screenshot of `dash_stats`: six tiles + bar chart + day detail + stacked homes. Default fetch is 4 weeks of every visible metric. | The daily note is ~60–80 lines. The Stats page is taller than the ledger. You would scroll past an analysis surface to reach nothing — the file already ended at the last Pomodoro. |
| **Scoreboard psychology** | Original Stats research, R9: "Weekly is where the numbers inform decisions; daily is where they become targets." Tiles currently show `▼ 17%` / `▼ 22%`. | A red delta under today's heading trains "I am behind" every time the file opens. The weekly prune is the place for that comparison. |
| **Spawn on the hot path** | `apiStatsFetch` always runs `bob stats show -a -f json`. Release-mode vault pass is ~180–370 ms. `scheduleStatsRevalidate` starts a 3 s timer on the first `metadataCache.changed` of any file, then spawns again. | Today's daily note is edited constantly (capture, pomodoro close, review answers). Mounting a Stats view there would spawn `bob` throughout the day, even when the strip is below the fold. |
| **Git churn** | 3,054 daily notes under `20*/`. Vault git-syncs across athena, apollo, and the Mac. Original research rejected nightly frontmatter snapshots for this reason. | Writing computed numbers into the file repeats the `#today`-tag mistake (`today-is-read-from-the-ledger`): copies of derived facts that go stale and pollute sync. |
| **Yet another dashboard** | `dash.md`, review footer, `bob-plan`, `bob ready`, `dash_stats`. | A third visual language on the daily note (plan chips + Dataview heading + Stats cards) is clutter. The strip must look like `bob-plan`, not like a second Stats page. |
| **DataviewJS / Tracker / Bases** | Dataview is already on the heading and is the slow community pattern (Obsidian Rocks, 2025: Dataview gets sluggish on large vaults; Reddit 2024: DataviewJS in a daily template froze Live Preview for seconds). Tracker has been stale since 2024. Bases has no native chart through 1.14. | A second implementation of metric definitions. Bob-cli owns every number (`docs/stats.md`: "the plugin only lays them out"). |

The screenshot is the right *inspiration* (hues, sparks, honest empty states, area attribution) and the wrong *object to embed*.

## Explicit requirement adjustments

Call these out as changes to the request, not as silent scope creep.

| # | You asked for | I recommend | Why |
| --- | --- | --- | --- |
| **A1** | Mini-dashboard inspired by `dash_stats.md` | **A day-mirror strip** that shares the engine and hues, and drops the page chrome (range chips, focus chart, definition panel, table, window means, deltas). | The page answers "how did the last weeks go?" The daily note answers "what has this day become?" Those are different densities and refresh rates. |
| **A2** | Put it at the bottom of daily files | **In-flow, after `## Pomodoros`, via an explicit `bob-stats` fence with `layout: day` in `_templates/daily.md`.** Not a sticky overlay, not the status bar, not a post-processor that injects widgets into notes that do not opt in. | Matches `bob-plan` (empty fence, template-only). Status bar already holds the review footer, which answers a different question (walk remaining, not day's reviewed count). Invisible injection is undebuggable. |
| **A3** | Maybe render faster because the daily file opens often | **Share the existing Stats cache; do not fetch a second range; revalidate day-layout views on a 30 s active-leaf throttle plus journal-append and pomodoro-close, never on raw vault-wide `changed`.** First open of a session may pay ~200 ms behind the existing skeleton. Later opens are cache hits. | The vault pass is one-shot and already ~200 ms regardless of `-r 7d` vs `-r 4w`. Range only changes JSON size and paint cost. A second fetch would *add* latency. The 3 s metadata throttle is the real footgun. |
| **A4** | (implied) Show the same six tiles | **This day's point for the overview six, with sessions folded into Worked (`3h 05m · 10`) and Review closed as a ✓/○ mark.** No `/day` suffix. No delta glyphs. | Tiles on `dash_stats` are window aggregates. A daily strip that showed `4h 10m /day` while the heading showed `3h 05m` would look broken. Deltas are the scoreboard. |
| **A5** | (implied) Historical daily notes too | **Template going forward only.** Optional hand-add or a tiny backfill of the last 4 weeks (the default Stats window). Never mass-edit 3,054 daily notes. Notes whose date is outside the cached window render a quiet **STATS ↗** chip and do not spawn a custom-range fetch. | `bob-plan` itself is on 26 notes, not the whole history. Old ledgers stay fast. `dash_stats` remains the way to inspect 2024. |
| **A6** | (new, from original R9) | **Keep interpretation on `dash_stats` / the Monday prune.** The strip is facts. The page is the instrument. Click-through carries `pinnedDay`. | Preserves R9's intent without refusing the daily glance. |
| **A7** | (new) | **Do not replace the Dataview heading in v1.** Later, bob-ledger-tools can paint the live `[t::]` sum itself so Dataview leaves the hot path. | That heading is local, correct for `worked` (prior research F7: 957/957 closed rows carry `[t::]`), and useful while scrolling Pomodoros. Mixing that rewrite into this feature is a second product. |

## What exists today (inventory)

### Daily note shape

Canonical path: `YYYY/YYYYMMDD.md`, `type: [[day]]`. Template `_templates/daily.md`:

1. Frontmatter (`parent`, `date`, `id`, …).
2. Title and prev/next.
3. `^gtd` task.
4. Empty `bob-plan` fence — live TODAY/PENDING/NEXT/READY chips, in-process, no `bob` spawn, ~32 px.
5. `## Pomodoros` with a Dataview inline duration formula.
6. Ledger rows. **The file ends here.** There is no footer, journal, or extra section.

Today (`2026/20261024.md`) is 59 lines; yesterday is 71. The "bottom of the daily file" is immediately under the last Pomodoro, including the open placeholder. That is the right seat: rear-view while lining up the next session.

`bob-plan` adoption is template-era only (26 files). Do the same for the strip.

### Stats engine and page

- `bob stats` is read-only. One vault pass feeds every metric. Today is provisional. Missing is `null`, never zero. No caches written to the vault. The review journal under `.bob/stats/review/` is the only thing Stats records.
- Overview six: `worked`, `reviewed`, `done`, `created`, `net`, `review_closed`. Sessions, habits, keep_rate, review_time are in the same report when the plugin fetches `-a`.
- Obsidian: empty ` ```bob-stats ` fence on `dash_stats.md`. Fence YAML already accepts `range`, `metrics`, `focus` (`STATS_FENCE_KEYS`). There is no `layout` key.
- Fetch: always `stats show -a -f json` plus range flags. LRU 8, stale-while-revalidate, one in-flight spawn, 20 s timeout. Desktop-only (`child_process`); Bob plugins never reach mobile, so that constraint is already accepted.
- Revalidate: any `metadataCache.changed`, vault create/delete/rename, journal append, midnight rollover. Debounce constant is 3 s, implemented as a *leading throttle* (first event arms the timer; events during the wait are dropped; after fire, the next event arms again).
- View state is per `sourcePath` and includes `pinnedDay`. Chart click already pins a day and offers **Open daily note**. The inverse link does not exist.
- Visual language: metric hues (orange / violet / green / blue / gray, the one hex exception in the stylesheet), 2 px accent start border, 14% tint — the same chrome family as `.bob-plan-chip`. Tile grid is `minmax(9.5rem, 1fr)`. Sparks use hollow bars for today.

Measured cost (from `docs/stats.md`, live `~/bob`):

| Path | Time / size |
| --- | --- |
| `bob stats -f json` (4w, athena, post-homes) | 182 ms median (178–188) |
| `bob stats` human overview (apollo, 2026-10-11) | 340 ms |
| 4-week JSON | 220,827 bytes |
| `-r all` JSON | 1.90 MiB, 1,093 sessions |

The pass cost barely depends on range. Paint cost and JSON size do. A day strip that fetches `-r 7d` while `dash_stats` fetches `-r 4w` would miss the cache and spawn twice.

### Competing glances (do not duplicate)

| Surface | Question | Why the strip is not this |
| --- | --- | --- |
| `bob-plan` | What is the plan right now? | Forward, caps, lanes. |
| Review footer | How much of the `]s` walk is still due? | Queue position, not day's reviewed count. |
| Pomodoros heading | How many minutes are closed in *this file*? | Local `worked` only. |
| `dash.md` | What should I work on? | Lanes and collections. |
| `dash_stats.md` | How did the last weeks go? | Window means, compare, drill-down. |

The strip's question: **What has *this calendar day* become?**

## Options considered

| Option | Verdict | Why |
| --- | --- | --- |
| **0. Embed the full `bob-stats` block** (empty fence, maybe `range: 7d`) | Reject | Tall, slow, scoreboard, 3 s respawn on the hot file. Fence metrics already do not shrink the fetch (`-a` is unconditional). |
| **1. Dataview / DataviewJS in the template** | Reject | Second metric implementation, no review journal, known Live Preview stalls on daily templates. The heading formula is the most Dataview this file should carry. |
| **2. Nightly write of numbers into frontmatter or a `## Stats` section** | Reject | Git-sync churn, stale during the day, violates "derive at read time." Same class of mistake as storing Today on the task. |
| **3. Status-bar / sticky overlay** | Reject | Fights the review footer. Not "at the bottom of daily files." Hidden when you are in another note, which is fine for a footer and wrong for a day log. |
| **4. Plugin post-processor on every `type: day` note, no fence** | Reject for v1 | Works on history for free, but undebuggable, surprising on 2024 notes, and easy to double-render once a fence exists. Keep the `bob-plan` contract: if the fence is absent, the widget is absent. |
| **5. New fence language `bob-day-stats`** | Fallback | Empty fence cannot accidentally paint the full page. Slightly more API surface. Prefer option 6 unless host-path defaulting feels too clever in review. |
| **6. Same `bob-stats` fence, explicit `layout: day`** | **Recommend** | One processor, one cache, one CSS family. Template is authored once, so the YAML is cheap insurance against the empty-fence footgun. Tests can pin the key. |
| **7. Distinct `bob stats day` CLI** | Later, not v1 | CLI rules would allow a sibling under `stats`, but the strip should reuse the default 4w `-a` report so it shares the cache with `dash_stats`. A compact JSON flag is a later optimization if paint or parse shows up in profiles. |
| **8. Compute today's `worked`/`sessions` in the plugin from the open file, engine for the rest** | Reject | Mixed sources will disagree with `dash_stats` for a few seconds and violate "bob-cli owns every display string." Keep the heading as the live local sum. |

## Recommended solution

### Shape

Two rows, chip chrome, after the last Pomodoro.

```
┌──────────────────────────────────────────────────────────────────────────┐
│ [WORKED 3h 05m · 10] [REVIEWED 57] [DONE 21] [CREATED 23] [NET +1] [POST ✓] [STATS ↗] │
│ ▓▓▓▓▓░░░░ gtd 1h 45m  ·  dev 1h 20m     ▁▂▃▅▂▄█  17–24                  │
└──────────────────────────────────────────────────────────────────────────┘
```

- **Row 1 (~32 px).** Overview chips in catalog order. Worked uses minutes display from the day's point and appends session count when `sessions` is in the report. Review closed is a boolean mark (`✓` met / `○` missed / `–` missing), not a "7 of 7 days" window ratio. **STATS ↗** is the same Browse-row chip pattern used on `dash.md` (`STATS ↗` is already label-only there).
- **Row 2 (~36 px).** One 8 px stacked area bar for this day's `worked` parts (catalog hues, unfiled/unlinked last and gray) plus a 7-bar spark of the last six complete days and today, taken from the *already-fetched* 4w points. Today is hollow if `provisional`. No second fetch.
- **Height budget:** ≤ 96 px including margins. Wrap chips on a narrow pane the way `bob-plan` already wraps. No chart, no homes accordion, no session list, no range chips, no table, no definition disclosure.
- **Honest states:** `–` for missing / not_tracked; never a silent zero. Skeleton on first paint (already implemented). Error is a one-line hint with Retry, not the full Stats error card.
- **Today vs past.** Today: muted "live" is unnecessary if the spark's hollow bar and the heading already say so. Past days: solid numbers. Dates outside the cached window: row 1 collapses to **STATS ↗** only.

Clicking a metric chip opens `dash_stats` with that metric focused and this day pinned. Ctrl/Cmd opens a new leaf. That is the beautiful symmetry with **Open daily note**.

### Fence and template

In `_templates/daily.md`, after the GTD placeholder Pomodoro:

````markdown
```bob-stats
layout: day
```
````

Add `layout` to `STATS_FENCE_KEYS`. Allowed values: `page` (default, today's `dash_stats` behavior) and `day`. Unknown values ignored (current parser already drops unknown keys).

Day identity: host path `YYYY/YYYYMMDD.md` first, else frontmatter `date:`. If neither parses, fall back to `page` layout rather than guess "today."

Do not put `range:` or `metrics:` in the daily fence. Inheriting the session default is what makes the cache hit. A fence that asked for `7d` would miss the 4w entry `dash_stats` already paid for.

No mass backfill. If yesterday should show the strip during the first week, add the fence to the last 4 weeks in one explicit vault edit, or live with template-only until those days age in.

### Data path

```
daily note (layout: day) ─┐
                          ├─► apiStatsFetch(default 4w, -a) ─► LRU cache ─► schema-1 report
dash_stats (layout: page)─┘                                              │
                                                                         ▼
                                                    day layout slices points[date == host day]
                                                    page layout keeps tiles / chart / panels
```

- Slice `metric.points` (and `sessions` filtered by `date`) in the plugin. Do not recompute minutes.
- Display strings, hues, parts, and quality come from the report. The plugin does not format `4h 05m`.
- If the day's point is absent from the cached window, do not spawn `YYYY-MM-DD..YYYY-MM-DD` in v1. Show the quiet chip. Historical browsing stays fast; `dash_stats` Custom range remains the escape hatch.

### Performance contract (the feature's actual design constraint)

Day-layout views **must not** subscribe to the vault-wide `metadataCache.changed` path that page layout uses.

| Event | Page layout (`dash_stats`) | Day layout (daily note) |
| --- | --- | --- |
| First paint, cache miss | Spawn, skeleton | Spawn, skeleton |
| First paint, cache hit | Instant, stale-while-revalidate | Instant, **no** background revalidate unless the leaf is active |
| Any vault `changed` | 3 s throttle, then spawn | Ignore |
| This daily file changed | (same) | 30 s throttle, only if this leaf is active |
| Review journal append | 3 s throttle | 30 s throttle, active leaf |
| Capture pomodoro close / `x` | 3 s (via `changed`) | Immediate coalesce into the existing in-flight spawn |
| Leaf deactivate | Keep mounted, keep throttling | Freeze. Next activate may revalidate if > 30 s old |
| Midnight rollover | Existing 60 s poll | Same |
| Historical day (date < today) | n/a | Fetch once from cache; never revalidate |

Rationale: a 30 s stale "Done 21" while you close the 22nd task is fine — the checkbox in the other note is the live object. A 200 ms `bob` child on every capture is not.

Target for "open today's daily note, cache warm": paint < 16 ms (DOM only). Target for "open today's daily note, cold session": one spawn, skeleton, then the strip; no second spawn from `bob-plan` (it does not spawn `bob`).

Do not grow `STATS_CACHE_SIZE` for v1. One 4w report serves every mounted day strip whose date falls in the window.

### Visual contract

Reuse `.bob-plan` geometry and `.bob-stats` hues:

- Chip: `border-inline-start: 2px solid var(--bob-stats-tile-hue)`, 14% tint, small-caps label, tabular-nums value, 7 px radius — copy `.bob-plan-chip`, swap the accent custom property for the metric hue.
- Do not use the 9.5 rem Stats tile cards. Those are a 2×3 grid meant to be clicked as a focus picker. The strip is not a picker; the chip *is* the link.
- Area bar: reuse `.bob-stats-home-area-bar` at 8 px height, no row labels except the two largest names to the right of the bar.
- Spark: seven existing `.bob-stats-bar` ticks, today hollow. No y-axis, no legend.
- Light/dark: the hex hues already have `.theme-dark` overrides. Do not add a third palette.
- Accessibility: `role="region"` with an aria-label that concatenates the six values (plan blocks already do this). Chips are real `<a>`/`<button>`s, not clickable divs.

Beauty here is restraint: the same family as the plan chips, a single colored bar that answers "where did the 3h 05m go," and a spark that answers "is today unusual" without a percent.

### What v1 does not do

- Deltas, `/day` means, compare-to-prior, keep-rate, habits grid, theme drill-down, session accordion.
- Writing the fence into historical notes automatically.
- Replacing the Dataview heading.
- A new CLI verb or a compact JSON schema.
- Magic "empty `bob-stats` on a daily note implies day layout." Explicit `layout: day` in the template is cheaper to test and document. Revisit magic defaulting only if empty-fence accidents show up.

### Implementation sketch

**bob-plugins (bob-ledger-tools), one phase:**

1. `statsParseFenceOptions`: accept `layout: day|page`.
2. `renderStatsResult`: if `layout === "day"`, paint `statsDayStrip(doc, view, report)` and return. Page path unchanged.
3. Pure helper `statsDayStripModel(report, day)` — day's point per overview id, sessions count, area parts, last-7 spark from worked. Unit-test in `scripts/test-ledger-tools-stats-block.cjs` with the existing canonical fixture (pin a day that exists in `canonical.json`).
4. Revalidation split: `scheduleStatsRevalidateForFile` no-ops for day-layout views; new `scheduleDayStatsRevalidate` with the table above.
5. **STATS ↗** / chip click: `statsViewStateFor("dash_stats.md").pinnedDay = day; focus = id;` then `openLinkText("dash_stats")`. Confirm page layout already honors `pinnedDay` on first paint (chart pin does); if it only pins after a click, that is part of this change.
6. CSS under a `.bob-stats-day` root so page styles cannot stretch the strip.
7. `preview-stats-block.cjs`: add a `layout: day` frame at daily-note width (~700 px) to the light/dark matrix.

**bob-cli docs (same change window, no CLI flags):**

- `docs/stats.md` — new "Day strip" subsection under Obsidian Stats block: fence, height budget, revalidation, click-through.
- `docs/dashboard.md` — the daily note is the inverse of **Open daily note**.
- `docs/reference/plugins/bob-ledger-tools.md` — processor behavior.
- `docs/reference/vault-format.md` — daily template includes the fence.
- Decision record only if you want R9 formally superseded. I would instead write a short addendum: R9 still governs *interpretation*; the strip is a mirror. A new decision is justified if reviewers want that on the roster.

**vault:** `_templates/daily.md` only. `bob plugins sync` after the plugin change.

**Not in v1:** `src/native/stats/` changes. The engine already returns per-day points.

### Tests that would catch the footguns

- Empty fence still paints *page* layout (dash_stats regression).
- `layout: day` with a host path `2026/20261011.md` slices the golden fixture's Oct 11 provisional point, not the window headline.
- `layout: day` does not call `statsHeader` / chart / table.
- Day-layout mounted + synthetic `metadataCache.changed` on an unrelated file does not call `statsSpawnFetch`.
- Chip click sets `pinnedDay` on the dash_stats view state.
- Unknown `layout: banana` ignored, page default.

## Critique of the plan in general

The instinct is right: the Stats page is beautiful, the daily note is the file that is always open, and a glance at today's numbers belongs near the ledger. The mistake would be treating "mini" as "the same widget, CSS-shrunk" or "the same widget, `range: 7d`."

Three deeper points:

1. **You already rejected this once, for a good reason.** Original R9 put Stats in the weekly prune so daily files would not become scoreboards. Reversing R9 without dropping deltas and window means would undo that. The strip is how you get the glance *and* keep R9.
2. **The performance worry is the revalidate policy, not first paint.** A 200 ms skeleton on the first open of the morning is fine. A 200 ms child process every 3 s of capture is the bug. Design the event table first; the CSS second.
3. **Do not grow the daily note's jobs.** Top = plan. Middle = ledger. Bottom = mirror. Heading = live local minutes. Footer in the status bar = walk. `dash_stats` = weeks. If a later idea wants keep-rate or a habits grid on the daily note, it has run out of budget: that belongs on the page.

A cheaper experiment, if you want to feel the idea before the plugin work: open today and `dash_stats` in a split for a week, and notice how often you actually look at the page during the day. If the answer is "only at the prune," skip the strip. If the answer is "I keep flipping to it to see hours and net," the strip will pay for itself.

I would still build it. The screenshot's area bar and hollow-today spark are the parts worth stealing, and they compress cleanly. The rest of that page is a destination, not a footer.

## Recommended solution (one paragraph)

Ship `layout: day` on the existing `bob-stats` fence, authored in `_templates/daily.md` after the Pomodoros section; paint a two-row chip strip (this day's overview six, sessions folded into Worked, Review closed as a mark, a stacked area bar, a 7-day spark) from the shared schema-1 cache; open `dash_stats` with the day pinned on **STATS ↗**; revalidate day-layout views on a 30 s active-leaf throttle rather than vault-wide metadata changes; write no numbers into the file; backfill at most the current 4-week window. Keep `dash_stats` as the weekly instrument. That is the intuitive, reliable, and beautiful version of the request.

## Sources

- Vault: `~/bob/dash_stats.md`, `~/bob/_templates/daily.md`, `~/bob/2026/20261024.md`, `~/bob/gtd_daily.md` (Weekly prune row), `~/tmp/screenshots/20261024_145006.png`.
- bob-cli: `docs/stats.md` (engine, schema-1, performance table, Obsidian block), `docs/dashboard.md`, `docs/reference/vault-format.md` (day notes), `docs/reference/cli/stats.md`, `src/native/stats/range.rs`.
- bob-plugins: `plugins/bob-ledger-tools/src/236-plugin-stats-data.js` (fetch, cache, 3 s throttle), `237-plugin-stats-models.js` (fence keys, tile model), `238-plugin-stats-block.js` (processor, page paint), `290-plugin-today-and-location.js` (`bob-plan`), `styles.css` (`.bob-plan`, `.bob-stats`).
- Prior research: `202610/bob_daily_stats/bob_daily_stats.md` (R9, F7, F10, reject nightly snapshots and DataviewJS).
- External: Harkin et al. 2016 (progress monitoring); Choe et al. 2014 (tracking too many things); Ke et al. 2023 / Few 2013 via goalsandprogress.com (≤5–7 live metrics); Obsidian Rocks 2025 (Dataview vs Bases performance); Reddit r/ObsidianMD 2024 (DataviewJS daily-template stalls).
