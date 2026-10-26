# Day strip vs the trailing 7-day average: design research

> **Research query:** Show a visual indication of how each numeric metric in the
> day strip compares to the average of the previous 7 days for the same metric.
> Lead the design so it is intuitive, reliable, and beautiful. Is this a good
> idea, would a different approach be better, and which requirement adjustments
> are justified? End with a recommended solution.
>
> Researcher: mus. Independent report; no peer reports consulted.

## Bottom line

**Yes, build it — narrower and quieter than the raw request implies.** The data
is already on hand (the strip's required coverage is exactly D−7…D, see F3), so
this is a presentation feature with no new fetch and no new tracking habit. The
recommended form is a one-line muted caption under each numeric value giving a
**signed absolute delta vs the trailing 7-day mean** (e.g. `+45m vs 7d avg`,
`≈ avg`), in neutral ink with a caret glyph, with the full sentence in the
tooltip and accessible label. No red/green, no percentages on small counts, no
comparison on the boolean fact, and the caption is suppressed whenever the
baseline is thin. That fits the strip's "quiet facts, never targets" lineage
while answering the actual question — *am I having a normal day?* — at a glance.

Readers in a hurry: [Is this a good idea?](#is-this-a-good-idea) →
[options compared](#options-compared) →
[recommended solution](#recommended-solution).

## Verified facts (this repo, this week)

- **F1 — Strip geometry and content.** The day strip is the first child of the
  rendered `bob-plan` block on canonical daily notes: line 1 holds five facts
  (`worked`, `reviewed`, `done`, `created`, `review_closed`, in that order),
  each stacking a small uppercased label over a large tabular value, sharing
  the line in columns split by hairlines and folding to three columns below
  ~34em. Height budget at 16px base: ≤56px one-line, ≤80px wrapped once. There
  are explicitly "no history marks" today. Every fact links to Stats with D
  pinned. (`docs/stats.md`, "Day strip".)
- **F2 — Units and directions of the five facts.** Builtin registry
  (`src/native/stats/registry.rs`, `BUILTINS`): `worked` = minutes,
  direction up; `reviewed` = count, up; `done` = count, up; `created` =
  count, **neutral**; `review_closed` = bool, up. Four of five facts are
  numeric; the closeout fact is boolean (green check / red ✕ / yellow
  half-ring / `–`).
- **F3 — The baseline is already fetched.** The strip reuses the cached default
  Stats report only when its daily series covers every date D−7…D; otherwise
  past days explicitly request `bob stats show -a -f json -g day -r <D-7>..<D>`.
  The seven prior daily points plus D are therefore already in hand in every
  state where the strip renders values. No new CLI flag, range, or fetch is
  needed. (`docs/stats.md`, "Day strip → Data".)
- **F4 — The engine's averaging conventions.** `summarize()` in
  `src/native/stats/series.rs` excludes provisional (today) and null points,
  counts `days_with_data` over real observations only, and `mean()` is the
  rounded integer mean over those days. Window headlines use the daily
  **median**, not the mean. Existing delta vocabulary: `≈ same` within ±1%,
  multipliers at ≥2×/≤0.5×, `new` against a zero prior, `–` against a null
  prior, `▼ 100%` for a drop to zero, sign-crossing as a raw amount.
  (`docs/stats.md`, "Display"; `series.rs`.)
- **F5 — Value ownership.** "Bob owns every value: labels, values, part
  displays, and definitions all come from the report." And: "Consumers never
  recalculate a display string, summary, percentage, or delta — the report
  carries them all." (`docs/stats.md`.) Anything the strip shows beyond fixed
  copy should arrive computed from `bob`, not be derived in the plugin.
- **F6 — The Stats page already does window-vs-prior.** Reports carry
  `summary.prior` + `delta` and the Stats UI has a "vs prior" comparison
  series. The strip's D-vs-trailing-7d is a *different* comparison (one point
  vs its own trailing baseline), so it adds information rather than
  duplicating the page — but the page is where full distributions, quartiles,
  and charts already live, which bounds how much the strip needs to show.
- **F7 — Lineage: facts, never targets.** The original day-strip research
  converged on five neutral tiles with *no deltas or percentages*, and the
  shipped spec kept "no history marks". This request knowingly revisits that
  decision. The constraint that survives intact: the strip must inform, not
  keep score — no goals, streaks, or target framing.
- **F8 — Release path.** CLI/engine changes ride the daily release train
  (one version per NY day after full CI on the exact SHA; agents never edit
  the version or CHANGELOG). A report-side addition ships on that train; a
  plugin-only render ships with the plugins. No synchronous coupling needed if
  the strip degrades gracefully when the field is absent.

## Is this a good idea?

**Yes, in a narrowed form.** Three reasons it earns its pixels, and four risks
that set the design constraints.

Why it works:

1. **It answers the strip's natural question.** A bare `done 2` on a Tuesday
   means nothing without a baseline; `done 2 · ≈ avg` vs `done 2 · −3 vs 7d
   avg` turns five numbers into situational awareness. Glanceable maintenance
   displays sustain behavior better than destination-only dashboards (the same
   Li/Dey/Forlizzi, Consolvo/UbiFit, Harkin lines the earlier strip research
   established — not re-litigated here).
2. **The marginal cost is ~zero.** By F3 the baseline points are already in
   memory; by F4 the averaging semantics exist. This is the cheapest
   comparison feature this codebase will ever get.
3. **Seven days is the right window.** It covers each weekday exactly once, so
   weekday/weekend rhythm mostly washes out — a 3-day average would inherit
   whatever part of the week you are in. It also matches the data the strip
   already guarantees (D−7…D), so the window choice and the fetch coverage
   agree exactly.

Risks, and what the design must do about each:

1. **Scoreboard on the working surface.** The daily note is opened dozens of
   times a day; tinting numbers good/bad converts a quiet ledger into a
   performance review (Etkin-style undermining; the prior R9 instinct that
   kept targets off the daily note). → *Neutral ink, absolute deltas, no
   hue-coded judgment; `created` is direction-neutral by definition (F2), so
   any coloring scheme would lie about at least one fact.*
2. **Provisional-today distortion.** At 10:00, `worked` is a partial day being
   compared against seven complete days; *every* morning would read "below
   average" under a naive delta. → *The strip already says `so far · HH:MM`;
   the caption and tooltip must keep that framing (comparison of a partial
   against completes), never present today as final.*
3. **Small-number noise.** `done` and `created` are low integers; `1 vs avg
   0.4` is "+150%" under percentage math — technically true, informationally
   garbage. → *Absolute deltas for counts, percentages never; an ≈ band around
   the mean.*
4. **Clutter and height.** The strip's budget (F1: 56/80px) is its beauty; a
   second row of captions spends ~14px of it. → *One short caption per fact,
   tabular numerals, no extra chrome; accept a small documented budget change
   rather than shrinking the values.*

### Would I take a different approach?

Considered and rejected, so the recommendation is explicit about the road not
taken:

- **Not tooltip-only** ("avg 3.1/day" in `title`). Zero visual change is
  tempting and I recommend adding the tooltip anyway — but hover text alone
  fails the request, is undiscoverable on touch, and hides the feature from
  everyone who never hovers. Complement, not solution.
- **Not sparklines.** Seven tiny bars under each value would be beautiful and
  show shape, not just level. Rejected: it breaks the height budget badly
  (~+20px), quadruples renderer complexity for five facts × two widths, adds
  visual noise to the hottest note in the vault, and per-point history inside
  the strip contradicts F7's "no history marks" lineage more aggressively than
  a single delta number does. Shape belongs on the Stats page (F6), which
  already charts it.
- **Not red/green direction coloring.** Rejected for three independent
  reasons: `created` is direction-neutral (coloring it moralizes inbox flow);
   red/green reintroduces the scoreboard F7 retired; and hue-as-meaning fails
  colorblind users unless duplicated by glyph/word — at which point the hue
  carries no information. Caret + words carry the meaning; ink stays neutral.
- **Not median instead of mean.** The engine headlines medians (F4) and medians
  resist outlier days — tempting. But the user asked for the *average*, means
  react to genuinely heavy/light weeks (which is what "am I having a normal
  week?" wants), and with n=7 the median of bursty counts (`done`) is often a
  dead 0/1 that makes every normal day look eccentric. Mean it is, computed
  the engine's way (F4: over days-with-data, provisional excluded).
- **Not a time-of-day-adjusted expectation** ("you usually have 2h by 10am").
  Intraday curves differ by weekday, require intraday history the ledger does
  not keep, and would be the single most complex and least trustworthy number
  on the strip. The honest framing is "partial vs complete" stated plainly.
- **Not Stats-page-only.** The page already answers this for analysts (F6);
  the request is specifically about the glanceable surface. Both can coexist
  because the comparisons differ (point-vs-trailing vs window-vs-prior).

## Options compared

| Option | What the eye sees | + | − |
| --- | --- | --- | --- |
| **A. Caption delta (recommended)** | `+45m vs 7d avg` under value, muted, caret | Absolute, honest at small n; fits fold; accessible text | +~14px height; needs budget change |
| B. Caret only | `▲` / `▼` / `=` dot, tooltip has numbers | Zero height cost | Cryptic; threshold choices hidden; fails "intuitive" |
| C. Sparkline | 8 mini-bars under value | Shows shape, beautiful | Height, complexity, noise; contradicts F7 lineage |
| D. Tooltip only | Nothing new visible | Zero layout risk | Not a visual indication; undiscoverable |
| E. Relative fill bar | Underline fill ∝ value/avg | Subtle, no text growth | Implies false precision; breaks at 34em fold; poor a11y |
| F. Page-only | Nothing on strip | Zero strip risk | Ignores the request; glance lost |

## Requirement adjustments (explicit)

1. **"Average" = rounded mean over days-with-data, not over 7 calendar slots.**
   Null (`missing`), `not_tracked` (pre-tracking days, F4 `since` semantics),
   and provisional points are excluded from the baseline; the divisor is the
   count of real observations. Rationale: a new metric's first week must not
   average four real days with three phantom zeros.
2. **Minimum-coverage gate: ≥4 of 7 days with data, else no caption.** Below
   that the "average" is a guess wearing a number's clothes. The fact still
   renders; only the comparison is suppressed (same philosophy as omitting,
   not faking, `hide`-suppressed metrics).
3. **Boolean fact excluded.** `review_closed` keeps its mark; a "vs average"
   on met/missed days is streak framing by another name (F7).
4. **Absolute deltas, never percentages, for counts and minutes.** Counts show
   signed integers (`+2`, `−1`); minutes reuse display formatting (`+45m`,
   `−1h 10m`). Borrow the engine's delta words where they fit: `≈ avg`
   inside the tolerance band, `new` when the mean is 0 and today is nonzero,
   no caption when today is null. Percentages appear nowhere on the strip.
5. **Tolerance band before declaring a difference.** Counts within ±0.5 of the
   mean read `≈ avg`; minutes within ±5m or ±5% (whichever is larger) read
   `≈ avg`. Rationale: integer counts jitter by nature; a `+1` on `done`
   against a 3.4 mean is noise, and the strip must not cry wolf by 10am.
6. **Neutral ink for all captions.** One muted secondary color, identical for
   above/below and across all four metrics. No green/red, no direction tint —
   even for direction-up metrics, because "above average" is not "good"
   (a 6h day during a rest week is information, not praise).
7. **Height budget grows modestly and explicitly.** 56px → ~70px one-line,
   80px → ~94px wrapped, at 16px base. Alternative (shrinking values to hold
   56px) would damage the strip's primary job — reading today's numbers — to
   subsidize the secondary one. Name the new budget in docs.
8. **Values computed engine-side, rendered plugin-side.** Per F5, `bob` adds
   the trailing-mean + delta words to the report (additive schema-1 fields);
   the strip renders them like every other value and writes only its fixed
   `vs 7d avg` / `≈ avg` copy. The strip treats absent fields as "no caption"
   so old-`bob` reports and new plugins mix safely across the release train
   (F8).

## Recommended solution

**One muted caption per numeric fact; engine-owned numbers; strict
suppression rules; full sentences in tooltip and accessible name.**

### 1. What renders (per numeric fact)

Under each numeric value, one caption in small muted tabular type:

- `▲ +45m vs 7d avg` — above the band (worked example).
- `▼ −1 vs 7d avg` — below the band (done example; signed integer for counts).
- `= ≈ avg` — inside the tolerance band (adjustment 5).
- `▲ new vs 7d avg` — mean is 0 over ≥4 real zero days and today is nonzero
  (borrows the engine's `new` word, F4).

The caret (`▲`/`▼`/`=`) is the *same* neutral ink as the caption text — it is
a direction glyph, not a verdict color. `review_closed` gets no caption. The
`so far · HH:MM` meta, skeleton, stale-muting, `–`/`⚠` states, `hide`
omission, and the 34em three-column fold all behave exactly as today (F1);
captions fold with their fact and never merge across hairlines.

### 2. What the tooltip and screen reader say

Every caption's `title` and the fact's accessible name carry the full honest
sentence, with the partial-day framing for today made explicit:

- Today: `Worked 1h 20m so far today · 7-day average 2h 10m (complete days
  only)`.
- Past day D: `Done 4 on Oct 19 · 7-day average 2.3 (Oct 12–18, 6 days with
  data)`.
- Suppressed baseline: no caption, and the tooltip says only today's sentence
  plus `7-day average unavailable (only 2 days with data)`.

Rationale: the number on the strip is the glance; the sentence is the truth.
"Complete days only" is the three-word cure for the provisional-today
distortion, and naming the baseline dates answers "average of *when*?"
without a docs trip.

### 3. Baseline and suppression rules (normative)

For fact metric M on date D, baseline = rounded mean (F4 `mean()`) over
{M's complete, non-null daily values on D−7…D−1}:

| Situation | Caption |
| --- | --- |
| ≥4 of 7 days with data, D has a value | Delta caption per §1 |
| ≤3 of 7 days with data | None (tooltip notes why) |
| D value null (`missing`/`not_tracked`) | None; fact shows `–` (+`⚠` if missing) as today |
| Baseline mean null (no usable days) | None |
| Metric hidden by `stats.hide` | Fact omitted entirely, as today |
| Stale cached frame | Caption renders but muted with the numerals (F1) |
| Future note | No strip at all, as today |

Mean display precision: minutes reuse `display` formatting; counts show one
decimal in tooltips (`2.3`) but deltas stay integral (`+2`, `−1`, else `≈
avg`). The bool, ratio, and signed units need no strip handling — the strip's
five facts are fixed (F1), and custom metrics never appear there.

### 4. Data contract (engine side, additive)

New optional per-point (or per-metric-trailing) schema-1 fields, e.g.
`trailing7: {mean, mean_display, days_with_data, delta_words}` on each of the
four numeric metrics' D point, computed with `summarize`-adjacent code so the
null/provisional exclusion (F4) is shared, not re-implemented. The plugin
renders `delta_words`-style fields verbatim and derives nothing. Absent
`trailing7` (older `bob`, F8) → no caption, no error, no layout shift beyond
the missing line. No new CLI flag: the D−7…D coverage the strip already
requires (F3) is exactly the input.

Why engine-side rather than averaging eight points in the plugin: F5 forbids
consumer-side derivation (divergent formatting is how "the strip says 2h, the
page says 3h" trust failures start), minutes formatting (`4h 05m`) and the
`≈`/`new` vocabulary already live in the engine, and the same field becomes
reusable by the Stats page later. Cost is one release-train ride (F8).

### 5. Beauty notes (so it lands beautiful, not just correct)

- Captions in the existing muted secondary token, ~0.72× the value size,
  tabular numerals; carets drawn from the same glyph set as the rest of the
  theme (no emoji, no colored dots).
- Baselines aligned across the four captions so the row reads as one line of
  small print, not four independent footnotes.
- No animation on delta appearance (values already draw-once where
  appropriate, F1); respect reduced-motion by default since nothing moves.
- Verify the light/dark + narrow/wide matrix in the existing fixture-driven
  browser preview (`node scripts/preview-stats-block.cjs`) before shipping —
  the harness already exists (F1 docs), so beauty is checked, not hoped for.

### 6. Phased plan

1. **Engine:** add `trailing7` fields + unit tests on the fixture vaults
   (null/provisional exclusion, 4-day gate, `new`/`≈` words); schema-1 minor,
   train release (F8).
2. **Plugin:** render caption + tooltip + aria; suppression-first (absent
   field → today's strip exactly). Narrow-fold and stale-state checks in the
   preview matrix.
3. **Live week:** ship captions on, watch for the two failure modes that
   matter — mornings that always read below average (tolerance too tight) and
   captions nobody can explain (words too clever). Tune the band, not the
   concept.
4. **Three-week check:** does the glance change any decision (stop earlier,
   close out review sooner, file fewer noise tasks)? If it only decorates,
   keep it anyway only if it stays quiet — the exit criterion is *harmless*,
   not *transformative*, because the strip's job is orientation.

### 7. Success and exit criteria

- Success: any fact's comparison is explainable from its tooltip alone; zero
  new fetches attributable to captions; no height/layout regressions at
  410/540/700px in the preview matrix; no increase in "strip says X, page
  says Y" reports (single-source values, F5).
- Exit (remove captions, keep everything else): sustained below-average
  mornings cause visible chasing behavior, or tolerance tuning cannot stop
  wolf-crying on bursty counts. The feature must be removable in the plugin
  alone (render gate), without an engine revert.

### Open questions (for Bryan, not blockers)

1. Should `worked`'s caption use a slightly wider band (±10m) since Pomodoro
   days are lumpy by construction? Starting recommendation: no — one band
   rule for all minutes, tune after the live week.
2. Past-day strips (memory lane: "what was Oct 19 like?") get the same
   caption with past-tense tooltips (§2). Any objection, or should comparison
   be today-only? Starting recommendation: both — the baseline math is
   identical and receipts benefit most.
3. The `+N` legend counter and root-parent bar are untouched by this proposal.
   A per-segment vs-average exists nowhere in this plan — deliberately; say
   the word if the bar should ever get the same treatment.

## Sources

All claims grounded in this repo: `docs/stats.md` ("Day strip", "Data",
"Display", "Ranges, grouping, summaries, display", "Schema-1 contract",
"Browser preview and fixtures"), `src/native/stats/registry.rs` (`BUILTINS`,
`Direction`, `MetricUnit`), `src/native/stats/series.rs` (`summarize`,
`mean`, `median`, `build_metric_series`), prior file
`sase/repos/research/202610/daily_note_day_strip/daily_note_day_strip.md`
(lineage only — its no-deltas conclusion is the decision this report proposes
revisiting, per F7). No peer reports consulted.

