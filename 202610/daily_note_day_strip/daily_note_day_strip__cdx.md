# A compact daily statistics footer for Bob

Researcher: **cdx** · 2026-10-24 · Independent research and recommendation

## Decision in brief

**Build it as a quiet, date-bound “Day in numbers” section after the daily ledger.** Show three daily values—Worked, Reviewed, Done—and one small area-allocation strip. Keep trends, comparisons, detailed breakdowns, and configuration on the full Stats page. Implement a new `bob-daily-stats` fence inside the existing Bob Ledger Tools plugin, backed by the existing `bob stats` JSON engine and an improved shared request/cache service.

This is a good idea as an end-of-day reflection aid and a quick check that recorded work matches your recollection. It is a less convincing idea as an always-visible productivity scoreboard. The design should make reflection convenient without encouraging repeated score checking or making note navigation expensive.

This report contains research and a proposed design, not an implemented feature. No vault or product source files were changed. No peer report, transcript, or findings were consulted.

## 1. What exists, and what it implies

### Directly inspected evidence

- The supplied `~/tmp/screenshots/20261024_145006.png` screenshot: six overview tiles, a large focused chart, day detail, and an area/project breakdown. The useful visual vocabulary is restrained metric color, strong numbers, small labels, and a compact allocation bar. The complete page is much too tall to transplant into a frequently opened note.
- `dash_stats.md`: a short note with parent `[[dash]]`, a description of recent weeks, and an empty `bob-stats` fence. The dashboard is already a plugin renderer, not a collection of DataviewJS charts.
- `_templates/daily.md` and `2026/20261024.md`: a daily review task, an existing `bob-plan` block, then a `## Pomodoros (…)` heading whose inline Dataview expression totals completed session durations. The ledger currently reaches the end of the note. Daily Notes uses `_templates/daily` and `YYYY/YYYYMMDD`.
- Bob's statistics documentation, Rust engine and report schema, and the Bob Ledger Tools source fragments for statistics fetching, rendering, and area attribution.
- Read-only `bob stats` calls on Apollo and a controlled reproduction of multi-request scheduling using the plugin's existing test harness.

The vault files above were read from an audited checkout of the synced repository, not from an unsaved Mac editor buffer. Source revisions and links are listed in §10. Live CLI output provided a separate observation of Apollo's vault.

### Important findings

**The footer needs a different time meaning.** The full dashboard's headline normally summarizes complete days in a range. Worked, Reviewed, and Done use daily medians; today is excluded from that summary and represented by a separate provisional point. The screenshot's Worked headline is **4h 10m/day**, while its selected day detail is **3h 05m**. A small copy of the existing tile would still show the wrong quantity for a daily note. [L1, L3]

I verified this with an explicit current-day request: `range.days` was `0` because there were no complete days; `summary.headline.value` was `null`; the daily Worked point nevertheless contained `185`, display `3h 05m`, and `provisional: true`. **Render the matching point, never `summary.headline`, even for a one-day request.**

**Most required data already exists.** Bob supplies daily metric values, display strings, quality, reasons, definitions, area/project/theme parts, labels, hues, and closed-session facts. There is no justification for another statistics engine, task parser, journal, or daily data-entry habit. [L1–L4]

**The note already has planning and a time total.** The footer adds the most value by combining recorded time with review answers, completed tasks, and allocation. Adding another live agenda, timer, task list, or review-queue counter would duplicate existing surfaces. Keep the current Pomodoros heading unchanged during the initial rollout; reconsider its repeated total only after using the footer.

**Small rendering does not imply cheap computation.** `StatsIndex::read` reads the eligible Markdown vault and journal inputs before evaluating a requested date range. A one-day query still needs tasks elsewhere in the vault, archives, hierarchy, and review events. Date range and selected metrics reduce result size and some processing, but do not turn the operation into a read of one daily file. [L2]

## 2. Critique and explicit requirement adjustments

| Original direction | Recommended adjustment | Why |
| --- | --- | --- |
| A mini-dashboard at the bottom of daily files | A default-open, natively foldable **daily summary**, after a new level-two heading | Makes the boundary clear, keeps the ledger usable, and creates a natural reflection point. |
| Take inspiration from Stats | Reuse its typography, hues, metric definitions, and allocation language; omit the analysis controls | Shrinking every existing panel would preserve complexity and make text harder to read. |
| Daily statistics | Bind to the **containing note's calendar date**, including historical notes | “Today” must not leak into an old note or an embedded daily note. |
| Render faster, perhaps | Make low overhead an acceptance requirement and measure it on the Mac | A screenshot cannot establish a performance problem; source inspection and Apollo measurements show where costs actually lie. |
| Show daily accomplishment | Use neutral recorded facts, with no score, goals, streak, ranking, or red/green daily delta | Minutes and task counts are imperfect proxies for useful work; unfinished days are particularly misleading comparisons. |
| Add the feature to daily files | Update the template and pilot on selected notes; offer explicit, idempotent insertion for older notes | Avoid rewriting the entire historical vault or modifying notes merely because they are opened. |
| Implied everywhere availability | Desktop rendering first; honest fallback on mobile and without the plugin | The current service spawns `bob`; the plugin's mobile-compatible manifest does not make that process boundary available on mobile. [L4] |
| Possibly capture a permanent daily record | Treat the footer as a **current projection of dated records**, not an immutable historical snapshot | Edits, reopening tasks, corrected logs, and hierarchy changes can revise past values or attribution. A frozen record is a separate feature. |

I would take a different approach if the real need is “keep today's totals visible while working anywhere”: an optional sidebar or a small command-opened view would better match that goal. For the stated request, the footer is preferable. The existing review status bar is already dense, and adding another persistent badge would increase ambient attention cost.

Success should mean “I understand how this day went in a glance,” not “I opened the dashboard more often.” Try it for roughly a week, then assess whether it helped reflection or merely added visual clutter.

## 3. Proposed visual and interaction design

### Default composition

Place this after the complete Pomodoros section:

````markdown
## Day in numbers

```bob-daily-stats
```
````

The fence name is proposed, not currently implemented. It is a new processor in the existing plugin, not a new plugin. A dedicated name gives it a clear date-specific contract and prevents older versions of the existing `bob-stats` parser from silently ignoring an unfamiliar mode and displaying the full dashboard.

Illustrative layout, using the values observed during this research:

```text
Day in numbers
Sat 24 Oct · So far                         Full stats ↗

  WORKED                REVIEWED                DONE
  3h 05m                10                      6

  ━━━━━━━━━━━━━━━ dev ━━━━━━━━━━━━━━━━━━━ gtd ━━━━━━━
  ● dev  1h 20m          ● gtd  1h 45m       Details ›
```

This is a wireframe, not a measured render. The bar's segment widths represent shares of **recorded time**, not progress toward a work target. The example includes GTD review time; “Worked” must not be relabeled “Deep work” or “Focus time.” The small “So far” label distinguishes a provisional day without a blinking indicator or running counter.

### Visual specification

- One calm region, not three nested cards. Use the note background or a subtle secondary surface, a fine separator, and generous horizontal alignment.
- At a typical 560–700 px note width, target roughly **160–200 px total height including the section heading**, not a hard clipping limit. At 320–400 px, allow wrapping and roughly 200–260 px when necessary. Text zoom and long translated/configured labels may increase height.
- Three equal columns with tabular numerals, approximately 22–26 px values and readable 12–14 px labels. Do not achieve compactness through tiny fonts. Below a usable minimum column width, stack label/value rows.
- Keep numbers and labels in Obsidian's normal text colors. Use the existing orange/violet/green accents sparingly to identify metrics. Area colors remain a separate semantic palette.
- A 6–8 px allocation strip adds a useful visual signature without introducing axes, legends, medians, or a second chart. Show at most three named legend entries initially; a `+N areas` disclosure exposes the remainder. Do not fabricate a formatted “Other” total in JavaScript.
- Preserve the existing area's stable ordering and supplied hue. Unlinked/unfiled buckets stay visible and neutral; never normalize them away to imply that all time was classified. The full labeled list remains available by keyboard and touch.
- No animation, chart library, hover-only information, or global keyboard shortcuts. Render the small strip with CSS or the existing lightweight primitives. Use Obsidian CSS variables for text, surfaces, borders, and spacing so light/dark/community themes remain coherent. [E1]
- Color cannot be the only carrier of meaning. Text identifies every metric and area; use explicit words for missing/stale/partial states. Validate contrast and 200% text enlargement. These follow W3C accessibility guidance, not an aesthetic preference alone. [E2]

### Interactions

1. **Full stats** opens the existing Stats page with this date selected and Worked focused. Activating a metric can open that metric for the same date. Date-preserving navigation requires a small internal navigation API; the existing “Open Stats” command only opens the page. Do not pretend a date-carrying link already exists.
2. **Details** expands an inline, bounded disclosure using the already returned report: definitions, quality explanations, and the complete allocation list. No new subprocess should be necessary for simple disclosure.
3. Keep source-note navigation separate from numeric drill-down. Area names in the expanded list can open their supplied home paths, using existing Cmd/Ctrl-click conventions.
4. Native heading folding is sufficient for hiding the section. Avoid adding a second disclosure just to show the three numbers.
5. A quiet Refresh action belongs in details or the unavailable/stale state, not in a permanent toolbar. Preserve focus and scroll position when data updates.

### What stays off the default footer

- **Created, Dropped, Net:** useful for periodic backlog analysis, but not a concise account of a day. Net is flow, not a backlog census or success score.
- **Review closed and habits:** available on the full page, but already adjacent to review workflows. Today's `review_closed` currently formats an unmet condition as `missed`; showing that as a failure while the day is ongoing would be unnecessarily judgmental. If added later, agree on engine-owned day-state wording such as “Not closed yet.”
- **Sparklines, deltas, streaks, targets:** send these to full Stats. Comparing an incomplete day to complete days is a poor default, and several tiny charts add scanning effort.
- **Sessions:** available in detail, but largely redundant with recorded time in the headline row.
- **Theme/area toggle:** keep v1 to areas, matching the current main panel. Themes remain available in full Stats; if demand emerges, make the chosen dimension a preference rather than another always-visible control. Theme hues must come from Bob's supplied catalog, not a new client hash. [L8]

## 4. Metric and date contract

| Display | Authoritative meaning | Important limit |
| --- | --- | --- |
| Worked | Built-in `worked`: minutes in closed Pomodoros; recorded duration first, range estimate as partial fallback | Open/planned sessions contribute nothing; GTD review is included. |
| Reviewed | Built-in `reviewed`: distinct answered row keys in decision tiers on that date | Not visits, skips, all gestures, or the number of tasks remaining; journal gaps are not zero. |
| Done | Built-in `done`: non-recurring DONE tasks with that completion date; daily `^gtd` excluded | Includes reading/reference and project kinds; does not mean every checked box in the daily note. |
| Allocation strip | The selected day's Worked `parts.area`, labeled/colored through `homes` | Area, project, and theme are alternative decompositions; never add them together. Historical grouping follows the current note tree. |

Use report-provided labels, definitions, units, display strings, part displays, and quality. Built-ins can be redefined in config. If Worked has been replaced by a non-Pomodoro or incompatible metric, show its supplied scalar definition and omit the misleading time strip. Do not hard-code the assumption that an ID always retains its default meaning.

Resolve D from the block context's source path with the same canonical `YYYY/YYYYMMDD.md` rule as Bob, including a valid calendar date and matching folder year. Do not use the active tab, file modification time, execution time, or an unchecked `new Date('YYYY-MM-DD')` conversion. The latter can shift local dates across timezones. If frontmatter date disagrees, use the canonical path and surface the discrepancy in details. An embed must keep the source daily note's date.

Request an explicit inclusive date range and daily grouping, for example:

```sh
bob stats show worked reviewed done -f json -g day \
  -r 2026-10-24..2026-10-24
```

For each metric, select the point whose `date` and `end` both equal D. Never substitute a bucket, nearest date, or current-day value when the point is absent. Do not fake historical dates by changing `BOB_NOW`; that alters the engine's clock semantics instead of requesting a date.

- **Current day:** render the supplied provisional point and “So far.” Closed sessions only; refreshing is not a live timer.
- **Past day:** render that date without the provisional label. Corrections can change it later. Done is derived from current task records and their completion dates, not an append-only completion-event history.
- **Future day:** show “This day has not started” without requesting a fully future range or inventing zeros. The current CLI rejects fully future explicit ranges.
- **Noncanonical/invalid source:** show a small explanatory state and the Stats link; do not silently fall back to today.
- **No record / not tracked:** display `—` with its supplied reason, not `0`.
- **Real zero:** show `0m` or `0`; a known empty ledger is different from missing input.
- **Partial:** show the supplied display plus a visible approximation/partial indicator with its reason in details. Do not apply an approximation sign merely because today is provisional.
- **Stale/error:** retain a matching cached result with “Last updated …; refresh failed” and Retry. Without a matching result, show a compact unavailable state. Never show another date's result while loading.
- **Unsaved edits:** the subprocess reads disk, so the summary follows saved records. Do not copy the parser into the editor merely to update a number before save. Revalidate after committed writes; explain this delay in details if necessary.

These states should occupy approximately the same footprint as the successful view so the page does not jump when the report arrives.

## 5. Performance evidence

I ran the installed `bob 0.3.1` on Apollo against the default live vault, sequentially, three times per request. Elapsed time includes subprocess startup, vault parsing, calculation, and JSON serialization. These are **small observational samples**, not cold-cache benchmarks, UI timings, or Mac p95 results. The vault and host were not isolated from other activity.

| Request | Elapsed ms, three runs | Median | JSON bytes |
| --- | --- | ---: | ---: |
| One day, Worked/Reviewed/Done | 542.8, 459.9, 384.8 | 459.9 ms | 8,626 |
| One day, those three plus Review closed | 409.7, 450.0, 452.3 | 450.0 ms | 10,476 |
| One day, all 11 visible metrics | 451.9, 530.0, 489.2 | 489.2 ms | 17,630 |
| Four weeks, all 11 visible metrics | 476.0, 569.4, 505.3 | 505.3 ms | 334,799 |

The observed ordering of the two smaller requests is noise, not evidence that adding a metric makes computation faster. The useful conclusion is that the proposed three-metric payload is about **39 times smaller** than the four-week payload, while computation remains on the order of half a second. Reducing view complexity helps payload parsing, DOM work, and visual density, but **avoiding redundant fetches matters more than removing one metric**.

There is no evidence here that the current full page is unacceptably slow in Obsidian. Its actual rendering cost still needs profiling on the Mac. Likewise, no persistent index, daemon, SQLite store, or precomputed daily JSON files are justified by these measurements alone.

## 6. Shared service changes required before daily use

The existing service has good foundations: `execFile` rather than a shell command, defensive schema decoding, a 20-second timeout, an eight-entry in-memory LRU, stale results, and `MarkdownRenderChild` cleanup. Reuse them. However, wider daily-note use exposes several concrete issues. [L4, L5]

### Observed implementation concerns

1. **Every ordinary cache hit starts revalidation.** `fetchedAt` is stored but not consulted for a freshness decision. Repeated note mounts can therefore keep launching full vault reads even when nothing relevant changed. A same-key request already in flight returns that promise before considering the cached frame, so a warm view can also wait unnecessarily.
2. **One pending slot is insufficient for multiple dates.** I reproduced A fetching, then uncached B pending, then uncached C pending. After resolving A and C, B's promise remained unsettled. The source replaces the pending object and its waiters when a different key arrives. This is a real integration risk for multiple open daily notes, not just a hypothetical performance concern.
3. **Metric selection currently retains `-a`.** The helper returned `["stats","show","-a","-f","json","-r",D+".."+D,"worked","done"]` for an explicit metric request. CLI selection prioritizes `--all`. Adding IDs alone does not deliver the smaller payload. The new service request must choose explicit IDs **or** `-a`.
4. **Refresh scheduling is broad.** Metadata changes trigger refresh; mounted views, rather than actually visible interested views, control eligibility. The three-second timer is set once instead of reset on every event, so its behavior is closer to coalesced throttling than a trailing debounce. Do not assume a footer below the fold is automatically free.
5. **Existing presentation helpers can assume period data.** For example, `statsPanelHasHomes` inspects `parts_summary`; a today-only request can have area parts on its daily point without complete-day summary parts. Daily allocation must inspect the selected point.

### Recommended service behavior

- Introduce a normalized request key covering vault identity, explicit date/range, grouping, metric selection, and relevant config revision. Keep the civil “today”/generation context separately so midnight invalidates provisional state.
- Keep the bounded in-memory report cache in the plugin/service, not in an individual Markdown child. Closing and reopening the daily note should reuse it. Do not write metric values into notes or a synced cache.
- Paint a matching cached frame immediately. Fetch only on a miss, known invalidation, explicit retry, or a bounded foreground recheck for missed external changes. Rendering a cached frame must not itself request another fetch.
- Use a per-key in-flight map plus a bounded FIFO/interest queue, with one process at a time initially. Same-key consumers share work. Every waiter must receive its own result or explicit cancellation; no request is silently replaced by a different day. Cancel queued interests when no view needs them.
- Record an input generation when work starts. If a relevant mutation arrives during the fetch, publish the result as potentially stale and arrange one subsequent refresh; do not mark it fresh or lose the event.
- Conservatively invalidate on relevant Markdown creation/modification/deletion/rename, review-journal changes, theme-journal changes, Tasks settings, and Bob configuration. A task completed today may live anywhere, including an archive; invalidating only the daily note is incorrect.
- Coalesce bursts, especially review gestures and Git sync. Start with roughly a one-second quiet window and a minimum interval of several seconds between recomputations while a visible view needs them; measure and tune. Hidden views retain a dirty flag and refresh when visible.
- Hidden `.bob` journals need explicit coverage: local append notifications plus an appropriate filesystem/sync signal or bounded foreground revalidation. Ordinary Markdown metadata events alone are not a complete cross-host invalidation strategy. Obsidian documents that hidden folders require Adapter-level access. [E5]
- Mount a lightweight reserved-size shell, then acquire data only when the view is visible or approaching the viewport. Use the correct leaf scroll container and owner document for pop-out windows. `IntersectionObserver` supports this without a manual scrolling/polling loop; it does not replace leaf visibility or lifecycle management. [E3]
- Handle rollover once at the shared service level. The note's date remains fixed; only whether it is provisional changes. Revalidate after sleep/foreground return and compare the returned `today` to the expected local date.
- Release view listeners, observers, pending interests, and focus state through the child lifecycle; keep only bounded shared cache data. Obsidian's Component guidance explicitly makes resource ownership and cleanup part of plugin correctness. [E4]

A clean warm mount should initiate **zero subprocesses** within its validity window. No footer out of view should cause periodic vault scans just because the note remains open.

## 7. Alternatives considered

| Approach | Strength | Main drawback | Judgment |
| --- | --- | --- | --- |
| Embed the current `bob-stats` block and hide panels with CSS | Fast visual experiment | Wrong summary semantics; still builds/fetches full-page content; depends on internal DOM | Reject as the product implementation. |
| Add `view: daily` to `bob-stats` | Shares one processor and namespace | Older versions silently ignore unknown fence options; page state and daily state become easy to mix | Viable with strict dispatch/version rollout, but a separate thin processor is clearer. |
| **New daily fence in Bob Ledger Tools, same engine/service** | Explicit day contract, small rendering, shared metric authority | Requires cache/scheduler hardening and a small new component | **Recommended.** |
| Dataview/DQL/DataviewJS mini-dashboard | Easy for simple indexed counts | Must reproduce Bob-specific closed-session, journal, archive, quality, and attribution semantics | Poor fit here; the existing native engine is the stronger starting point. |
| Generate Markdown totals when sessions close or nightly | Instant portable text; potentially works on mobile | Stale historical corrections, cross-host writes/conflicts, more mutation paths, snapshot ambiguity | Reserve for an explicit frozen/export requirement. |
| Separate sidebar/status bar | Available away from the daily note | Competes with existing review UI and raises persistent attention cost | Later optional entry point if footer discoverability proves inadequate. |
| New incremental engine/database | Could reduce repeated compute time | Considerable consistency/invalidation complexity with no demonstrated need yet | Profile first; defer. |

Dataview can query its existing index, so it would be inaccurate to claim every Dataview view necessarily reads the entire vault from disk. The reason to reject it here is duplicated domain semantics, not a blanket claim that Dataview is slow. Its API documents page/index queries and rendering as separate capabilities. [E6]

## 8. Integration and rollout boundaries

**Plugin work is primary.** Add the small processor/model/renderer and scoped CSS in the `bob-plugins` source repository. Share report decoding, spawning, cache, and request scheduling; do not share the full page's tile model unchanged. Put hand-edited changes in source fragments, update `fragments.json`, regenerate `main.js`, and deploy via the repository's required `bob plugins sync` workflow. Do not edit generated vault plugin files directly.

**No initial Rust command is required.** The existing explicit metric IDs, inclusive range, `-g day`, and schema already provide the proposed v1 data. Future additions such as current-day checklist wording, a compact engine-owned formatted remainder, or a smaller projection endpoint need deliberate additive contract work, not local JavaScript approximations.

**The full-page handoff needs explicit design.** Add a method such as `openStatsForDay({day, metric, newLeaf})` that opens/focuses the page and applies an explicit day selection to the intended leaf. This is a proposed internal API. Avoid global “last selected date” leaking into every Stats leaf. For v1 it is acceptable to open a one-day full report; comparative navigation can then be chosen there.

**A new `##` heading is a structural boundary, not mere decoration.** Bob defines the ledger up to the next level-two heading. Add the footer after the final Pomodoro, and verify that start/close/insert/move/archive operations continue inserting inside the ledger rather than below the footer. Review the original daily note and template together. [L7]

**Rollout:** validate with fixtures and the browser preview; deploy the plugin; add the fence to the template and one pilot daily note; then offer an idempotent insertion action for older canonical notes. Do not backfill all years just to make historical viewing possible. Do not mutate daily files on read. Keep the full Stats page as the detailed destination.

**Platform scope:** Reading view and Live Preview are the initial rendered modes. Source mode keeps the simple marker. Test the fence's editing behavior near the cursor; do not promise that a rendered widget remains visible while editing its source. Mobile should show a short desktop-only explanation, not repeated missing-binary errors or fabricated zeros. Synced mobile snapshots would be a separately scoped follow-on only if requested.

## 9. Acceptance checks and unresolved questions

### Correctness and reliability gates

- Compare each displayed value and label against the matching CLI daily point, including the real current-day case with null summary and non-null point.
- Verify past, today, future, leap day, invalid path, folder/year mismatch, frontmatter mismatch, embedded note, and two daily notes open in separate leaves.
- Cover closed versus open/planned Pomodoros; estimated durations; task completion outside the daily note and in archives; reference/project kinds; recurring exclusions; journal duplicate/gap cases; zero/missing/not-tracked distinctions.
- Confirm daily allocation from points when `parts_summary` is absent, all-unlinked time, long area labels, custom metric redefinitions, and missing older-schema optional fields.
- Reproduce A/B/C queued requests, same-key warm/in-flight consumers, eviction, errors, teardown, and a mutation during computation. Every interested view settles with the right date.
- Test saves, deletions, renames, journal-only remote sync, config changes, timezone/local-midnight rollover, and wake from sleep. Invalidating only the visible daily file must fail a test involving completion in another note.
- Assert opening/refreshing/folding the dashboard does not modify note bytes or append journal events.
- Preserve all ledger editing and capture insertion behavior after the new heading.

### Product and performance gates

- On the actual Mac, measure uncached first appearance, cached reopening, visible refresh during rapid review, and typing with an off-screen footer. Report main-thread/render time separately from subprocess wall time.
- Provisional design budgets: warm paint p95 under about 50 ms; no added UI-thread task over 50 ms; a one-day cold result around one second or better on the target Mac. These are targets to validate, not measured promises.
- Within cache validity, repeatedly reopen the same day and verify zero extra subprocesses. Several same-day views should share one fetch; distinct dates must not starve.
- Check light/dark themes, a narrow split, pop-out windows, 200% text zoom, keyboard-only use, and understandable missing/stale states. Expanded details may grow; the default footer must remain compact.
- Reuse the existing fixture-driven Stats browser preview infrastructure to compare the proposed layout with the screenshot rather than introducing a new preview stack. [L1, L6]

Open questions are small enough not to block a prototype: whether you prefer areas or themes after seeing the compact strip; whether three metrics feel useful after a week; and whether mobile rendering is actually needed. My defaults are areas, three metrics, desktop. I have not measured the Mac renderer, inspected unsaved editor state, or built the new component, so beauty and interaction quality still need a real preview review.

## 10. Source trail and reproducibility

### Local sources

All code was read locally after the required repository-open workflow. Links below pin the source revisions used; they are not claims about later releases.

- **L1 — Metric definitions, quality, range semantics, UI contract, and preview instructions:** bob-cli `8a7b02e1b9a61b79bf8f3ced17a02d2e605ba1a8`, [docs/stats.md](https://github.com/bobs-org/bob-cli/blob/8a7b02e1b9a61b79bf8f3ced17a02d2e605ba1a8/docs/stats.md).
- **L2 — Full vault input pass and canonical daily date:** [src/native/stats/index.rs](https://github.com/bobs-org/bob-cli/blob/8a7b02e1b9a61b79bf8f3ced17a02d2e605ba1a8/src/native/stats/index.rs), [compute.rs](https://github.com/bobs-org/bob-cli/blob/8a7b02e1b9a61b79bf8f3ced17a02d2e605ba1a8/src/native/stats/compute.rs).
- **L3 — Report and CLI selection:** [report.rs](https://github.com/bobs-org/bob-cli/blob/8a7b02e1b9a61b79bf8f3ced17a02d2e605ba1a8/src/native/stats/report.rs), [cli.rs](https://github.com/bobs-org/bob-cli/blob/8a7b02e1b9a61b79bf8f3ced17a02d2e605ba1a8/src/native/stats/cli.rs).
- **L4 — Fetching, cache, queue, desktop boundary:** bob-plugins `1202c6a0b1b47cdd973eb5d97d19ff3407bfb596`, [236-plugin-stats-data.js](https://github.com/bobs-org/bob-plugins/blob/1202c6a0b1b47cdd973eb5d97d19ff3407bfb596/plugins/bob-ledger-tools/src/236-plugin-stats-data.js), especially `statsBuildArgs`, `apiStatsFetch`, and `scheduleStatsRevalidate`.
- **L5 — Fence parsing, tile model, view lifecycle, daily breakdown:** [237-plugin-stats-models.js](https://github.com/bobs-org/bob-plugins/blob/1202c6a0b1b47cdd973eb5d97d19ff3407bfb596/plugins/bob-ledger-tools/src/237-plugin-stats-models.js), [238-plugin-stats-block.js](https://github.com/bobs-org/bob-plugins/blob/1202c6a0b1b47cdd973eb5d97d19ff3407bfb596/plugins/bob-ledger-tools/src/238-plugin-stats-block.js), and `239-plugin-stats-panel-models.js` / `239-plugin-stats-homes-render.js` in that same directory.
- **L6 — Verification infrastructure:** `bob-plugins/scripts/test-ledger-tools-stats-data.cjs`, `ledger-tools-harness.cjs`, `preview-stats-block.cjs`, and Stats fixtures at the L4 revision. The A/B/C reproduction used the real built plugin API, mocked `statsSpawnFetch`, and controlled promise resolution; the result was A/C spawned, C settled, B unsettled after A/C completed.
- **L7 — Ledger boundaries and the existing Stats note contract:** [docs/reference/vault-format.md](https://github.com/bobs-org/bob-cli/blob/8a7b02e1b9a61b79bf8f3ced17a02d2e605ba1a8/docs/reference/vault-format.md), [docs/dashboard.md](https://github.com/bobs-org/bob-cli/blob/8a7b02e1b9a61b79bf8f3ced17a02d2e605ba1a8/docs/dashboard.md).
- **L8 — Audited project memory:** `obsidian.md`, `sase_artifacts.md`; glossary entries for Pomodoro, Pomodoro Theme, Task Link, Morning GTD Review Footer; decisions `theme-hue-is-pin-exempt-area-hash`, `theme-prefs-live-in-per-host-journal`, and `today-is-read-from-the-ledger`. No related research artifact or peer findings were read.
- **User input / vault snapshot:** supplied screenshot `~/tmp/screenshots/20261024_145006.png`; private `bobs-org/bob` revision `9806841331b790be9257b635ee155faf41adba1e`, specifically `dash_stats.md`, `_templates/daily.md`, `2026/20261024.md`, and `.obsidian/daily-notes.json`. Only the structural evidence needed for this report is reproduced.

Benchmark method: Python `subprocess.run([...], capture_output=True, check=True, timeout=20)` around each request, timed with `time.perf_counter()`, three sequential runs; report byte count is `len(stdout)`. The full-page comparison command was `bob stats show -a -f json -r 4w`. A current-day observation returned Worked `3h 05m`, Reviewed `10`, Done `6`, and area parts dev `1h 20m` / gtd `1h 45m`. Those are observations, not stable fixtures.

### External primary documentation, consulted 2026-10-24

- **E1 — Obsidian styling:** [About styling](https://docs.obsidian.md/Reference/CSS%20variables/About%20styling). Built-in CSS variables support integration with Obsidian themes.
- **E2 — Accessibility:** [W3C WCAG 2.2](https://www.w3.org/TR/wcag/), especially use of color, contrast, and text resizing.
- **E3 — Viewport-triggered work:** [MDN Intersection Observer API](https://developer.mozilla.org/en-US/docs/Web/API/Intersection_Observer_API). Asynchronous intersection observation supports lazy work; use the appropriate root and cleanup.
- **E4 — Plugin resources:** [Obsidian: Manage plugin lifecycle](https://docs.obsidian.md/plugins/guides/lifecycle-management). Component ownership and registered cleanup prevent orphaned resources.
- **E5 — Vault access:** [Obsidian Vault API guide](https://docs.obsidian.md/Plugins/Vault). Distinguishes display reads/caching and hidden-folder Adapter access.
- **E6 — Dataview capabilities:** [Dataview Codeblock Reference](https://blacksmithgu.github.io/obsidian-dataview/api/code-reference/). Index-based queries and separate rendering APIs.

## Recommended solution

**Implement a small `bob-daily-stats` renderer inside Bob Ledger Tools, placed after `## Day in numbers` at the bottom of new daily notes. Default to Worked, Reviewed, and Done for that note's date, plus a thin area-allocation strip and a date-preserving link to full Stats. Use Bob's existing daily points and formatting without changing metric definitions.**

Make shared cache freshness, multi-date request correctness, and visibility-aware refresh part of the first implementation. Keep the view read-only, show provisional/missing/stale states honestly, and avoid persistent computed values. Pilot on a few notes and measure the actual Mac before adding history charts, mobile snapshots, or a new indexing layer. This delivers the useful part of the idea while preserving the daily note as a place to work and reflect.
