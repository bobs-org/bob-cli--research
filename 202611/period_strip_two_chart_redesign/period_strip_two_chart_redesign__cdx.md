# Period stats strips: a task-type timeline and a clear root-parent ranking

Independent research by **cdx**, 2026-11-10. Scope: weekly, quarterly, ISO-year, and all-time period-note strips; their relationship to the Day strip; the Bob reporting contract and chezmoi configuration. No peer swarm reports, transcripts, or findings were consulted. This is a design recommendation, not an implementation: product code, the vault, and chezmoi configuration remain unchanged.

The proposal is a good idea. Separating task types from root parents gives each chart one understandable purpose. I recommend retaining the chronological chart, changing its colored breakdown to actual task types, and adding a compact **ranked horizontal bar chart of the top five root parents**. A visible `Types | Roots | Both` control should select whole chart panels. Keep the facts above them and the existing child-note table below them. The important qualification is that the current data called `theme` is not always an actual task-type breakdown; address this before simply recoloring the timeline.

**What the screenshot and source establish.** The supplied screenshot, `~/tmp/screenshots/20261110_095225.png`, shows **2026-Q3**, rather than a weekly note: W27–W39, 414h worked, and thirteen weekly columns. Judge the design against quarterly density from the outset, as well as seven-day weeks. The image shows a crowded line combining lowercase roots and uppercase type/name components, many thin stacked slices, closely packed time labels, and a very small unlabeled switch. The large Properties block is Obsidian note chrome; reducing that is a separate presentation preference, not a reason to squeeze the chart further.

I inspected bob-cli at `cf7c0605`, bob-plugins at `1b39478`, and chezmoi at `22e432bc`. The relevant findings are:

| Existing behavior | Implication |
| --- | --- |
| `bob periods show` performs one day-grouped Stats computation and supplies facts, lanes, columns, children, catalogs, and quality states. | Extend this report; do not add a vault scanner or a CLI call per chart or child. |
| `columns[].stack` contains root-parent minutes. The plugin hardcodes root ordering and colors for columns. | The current chart is a root chart. Changing it requires a data-contract extension as well as styling. |
| Period lanes include `root_parent` and `theme`; the painter shows three legend entries per lane plus `+N`. | A short legend is not a top-N chart: the hidden categories still occupy the columns. |
| Period rendering reads the Day-strip preference, with `both`, `roots`, and `themes`, but paints the parts chart unconditionally. | A switch exists, but does not express the requested chart visibility. |
| The shared setter repaints Day-strip records; the period painter's memoization key omits lane view. | Explicitly repaint period records and include view/content dependencies in the render key. |
| Quarter/year/all-time type lanes fold `(unnamed)` and parts below 2% into `other`; weekly lanes do not. | A new timeline needs period-wide folding membership, not a different legend for each column. |
| Columns are 48px high, with 1px gaps and a 2px minimum for every segment. | Small contributions can be visually overstated. Exact geometry matters as much as color. |
| Year rendering has a four-quarter fallback, but CSS switches at only 110px container width. | That is too late to make dense weekly content useful in normal narrow panes. |
| Chezmoi's `home/dot_config/bob/config.yml` declares BUILD, CHORE, FIX, MEET, PLAN, READ, WRITE; it currently has no `stats:` block. | Add the proposed limit to this source file during implementation. |

A source-level color mismatch also belongs in this redesign: period legend markers emit `bob-period-strip-hue-*` and `bob-period-strip-theme-hue-*`, while the stylesheet defines the shared `bob-day-strip-*` hue classes. Fallback to faint gray is consistent with the screenshot's gray markers. Reuse the working shared color implementation rather than adding another palette. These are source observations, not claims that I reproduced them in the user's running Obsidian installation.

**Give the charts different jobs.** A type timeline answers “When did I work, and what kind of work was it?” A root ranking answers “Where did the period's time go?” Separate headings remove the need to decode case, dot shape, or a combined legend.

The Office for National Statistics recommends columns for time series and ordinary bars for categorical comparisons, with a zero baseline and a logical, usually descending, order. It also explains that middle stacked segments are harder to compare because they lack a shared baseline. This supports a type timeline paired with a root ranking rather than a second stack of tiny slices. [ONS bar-chart guidance](https://service-manual.ons.gov.uk/data-visualisation/chart-types/bar-charts), [ONS stacked-bar guidance](https://service-manual.ons.gov.uk/data-visualisation/chart-types/stacked-bar-charts).

| Approach | Assessment |
| --- | --- |
| Two stacked timelines, one per dimension | Closest literal extension and useful for root trends; duplicates chronology and total heights, needs two legends, and still makes root comparisons difficult. |
| One timeline whose dimension toggles | Compact, but cannot provide a useful Both view and repeatedly changes what the chart means. |
| Type timeline plus ranked root bars | Recommended: complementary questions, direct root labels, bounded default height, and good use of a narrow note column. |
| Root pie/donut or treemap | Weaker for close comparisons, long names, and accessible interaction; adds visual novelty without improving the task. |
| Five root sparklines/small multiples | Consider later for an explicit root-trend workflow; too much machinery for the first strip revision. |

The tradeoff is explicit: the root chart summarizes the **whole selected period**, not root changes inside each week/day. Root trends remain available in Stats and child notes. If root-by-week changes are actually the primary question, two aligned timelines are the alternative: choose roots once from parent-period totals and use identical y scales. Never recompute “top five” independently in every child column.

**A proposed visual arrangement.** Integrate the strip with the note: its background, native typeface, understated separators, and no enclosing dashboard cards or shadows. Task-type colors should be the main color signal. Root bars can be quiet ink/tinted bars with direct labels and small existing home-color markers; they do not need five new competing hues.

This is a structural sketch, not a rendering or a claim about the screenshot's underlying data:

```text
WORKED          REVIEWED       DONE          CREATED       REVIEW CLOSED
41h 20m         38             27            31            5 of 7
 typical 39h     typical 35     typical 24    typical 30

Worked time                                 Types   Roots   [Both]

Task types · by day                              so far · 14:32
BUILD 18h    READ 9h    MEET 6h    PLAN 5h    …
              ┌─┐
       ┌─┐    │ │    ┌─┐
  ┌─┐  │ │ ┌─┐│ │ ┌─┐│ │                  stacked by type
  └─┴──┴─┴─┴─┴┴─┴─┴─┴┴─┴────
  Mon  Tue  Wed Thu Fri Sat Sun

Root parents · top 5                             % of Worked
sase          ━━━━━━━━━━━━━━━━━━               24h 00m   58%
bob           ━━━━━━                            8h 00m   19%
gtd           ━━━                               4h 00m   10%
writing       ━━                                2h 00m    5%
reading       ━                                 1h 00m    2%
Other roots · 4 roots                            2h 20m    6%
                                                   All roots ↗
```

Use exact Bob-supplied strings in the product; the sketch's percentages are rounded and illustrative. A two-line type legend may wrap. A `+N` without visible meaning should not be the only way to discover hidden contributions: `Other types · 2h` should show its duration and expose members on focus or through a details disclosure.

Start with a **104–120px timeline plot** and approximately **28px per root row**, then tune in the actual note container. These are design targets, not measured acceptance results. Both will be taller than today's strip; that is justified if every additional row is readable. A comfortable 300–380px total at normal note width is a better target than forcing five facts, two breakdowns, and chronology into the old height. Single-panel views stay smaller. Avoid a strict height cap that clips long names or enlarged text.

Give the type chart a quiet unit cue, a zero baseline, and at most a few light guides. Keep exact values visible for seven-day weeks when they fit; denser views can show group totals and reveal column values on keyboard focus or hover. Use tabular digits and right-aligned durations. Preserve review/closeout markers in one quiet row.

Round only the outer boundary of a whole stack. Do not round every slice into a capsule, impose minimum slice heights, or insert layout gaps between numeric segments. SVG or precisely positioned HTML can work; the essential property is that segment heights sum to the true column height. A column-sized interaction target makes tiny slices accessible without inflating their values.

**The data trap: themes, types, and labels differ.** Stats currently calls `pomodoro_components`, which splits the entire session name at `+` and uppercases every component. `theme_minute_parts` apportions minutes across those components. Separately, `pomodoro_themes::routing::type_components` knows which components are actual types under the configured vocabulary. The former does not use the latter. Merely replacing root stacks with existing `theme` parts therefore does not reliably meet “task types only.”

For example, under the checked chezmoi vocabulary:

| Recorded session | Current name-component split | Recommended actual-type projection |
| --- | --- | --- |
| 30m `BUILD + SASE` | BUILD 15m, SASE 15m | BUILD 30m |
| 61m `BUILD + READ + SASE` | BUILD 21m, READ 20m, SASE 20m | BUILD 31m, READ 30m |
| 30m `SASE` | SASE 30m | Unclassified 30m |
| 30m unnamed | `(unnamed)` 30m | Unclassified 30m |

The right column is a **proposed accounting policy**, not current behavior. Assign counted minutes to the session's recognized type components; labels do not consume a share. Multiple recognized types share minutes with a documented deterministic integer split and consistent remainder rule. Normalize and deduplicate identities with the existing type rules. This is time attributed from recorded session names, not a count of tasks by type.

Add a true `task_type` dimension/projection without silently changing legacy `theme` meanings. Retain legacy parts for old clients and custom `themes:` metrics. Compute the projection during existing session evaluation, using the same counted contribution and clock through metric/home filters. Do not filter already-split `theme` aggregates: after BUILD and SASE each receive 15m, a period aggregate cannot generally reconstruct which labels accompanied which types. Include today's provisional data through the same path.

Use **Unclassified** as a neutral contribution, explained as “No task type recognized under the current type configuration.” It is neither a fabricated type nor missing time. Earlier quarters may contain large amounts: SASE and other old names visible in the screenshot are not in today's configured vocabulary. Do not guess that SASE meant BUILD, discard those minutes, infer historical types from current task fields, or rewrite the ledger to make the chart colorful.

This follows the current configured vocabulary, matching the existing classifier. Vocabulary edits can therefore reclassify historical views. Explain this in the chart definition/details and invalidate caches when configuration changes. Immutable historical classification would need a separate recording/migration policy; it is outside this visual redesign. Root attribution similarly follows the current note tree, rather than a frozen historical snapshot.

For consistency, the Day strip and Stats Types drill-down should consume the same additive true-type projection when available. This is a justified scope expansion: otherwise BUILD 30m in the period chart can lead to BUILD 15m in its drill-down. Preserve old payloads and clearly label legacy presentation with older Bob binaries; do not call an old name-component breakdown the new type accounting.

**Precisely what top N means.** Rank named root parents by counted Worked minutes across the **entire selected period**, including today's provisional contribution when the report does. Sort descending integer minutes, then canonical root key for ties. Do not rank rounded percentages or labels. N limits named root rows, not colors, legend labels, or the underlying Stats data. Omit zero-valued roots; fewer than N roots means fewer rows.

Every percentage uses all Worked time for that period, never just the selected roots. Give ranked bars the same zero-to-100%-of-Worked scale so a 60% bar means the same thing in adjacent notes. Without background tracks they read as a categorical chart rather than a completion meter. Direct duration and share labels make small bars useful without exaggerating them.

Remaining named roots appear in a quiet **Other roots** summary with count, minutes, and share. A text footer rather than an extra ranked bar keeps the main chart to N bars. Its details and `All roots` action reveal the full list. Treat `@unfiled` and `@unlinked` as separately labeled attribution summaries rather than spending named-root slots on them or hiding them in Other. They still count in the denominator. With no named roots, state that and show any attribution time rather than an unexplained empty panel.

For valid additive attribution, top roots + other named roots + attribution buckets must equal Worked. If upstream data violates that invariant, surface a quality warning and retain the known numbers; never silently rescale to 100%. Displayed rounded percentages can differ slightly from 100%; geometry uses integer minutes. Synthetic rows need an explicit kind and separate identity: bare `other` could collide with a real root or historical name.

**Keep type clutter consistent.** Maintain one order, color map, and folded-membership set for the selected period. Use Bob's canonical type hues; a type moving up the ranking must not acquire a new color. Legend and columns share the order. A type missing on one day has zero height, not a different rank.

Initially preserve the established policy of all weekly types and below-2% folding for longer periods, applied to the new true-type projection. Keep Unclassified separate from Other types, so an incomplete taxonomy cannot masquerade as ordinary small categories. Select folded membership from parent totals and apply it to all child columns and responsive fallbacks, conserving each total. ONS advises about five segments per stack; the checked vocabulary has seven types, so treat this as a readability warning, not permission to silently drop two meaningful types. Evaluate a seven-type fixture before adding another configurable limit. [ONS guidance on avoiding crowded stacks](https://service-manual.ons.gov.uk/data-visualisation/chart-types/stacked-bar-charts).

**Make the switch control complete panels.** Replace the tiny period glyph with a visible single-choice control, `Types | Roots | Both`, labeled “Breakdown.” Default to Both without a saved choice. Retain the existing device-local preference and enum (`themes`, `roots`, `both`) so the saved choice survives, but display Types to the user. Reuse the choice with the Day strip and repaint every affected mounted strip synchronously.

| Choice | Below the facts |
| --- | --- |
| Types | Task-type timeline with legend/details |
| Roots | Root-parent ranking with remainder/attribution summaries |
| Both | Type timeline followed by root ranking |

Facts, off-clock hint, coverage, errors, and the separate child table are independent of the choice. Roots hides the timeline; child navigation remains in note links and the parts table. This resolves the ambiguity of “root parents only”: hiding just a legend while leaving the other dimension's chart visible is not acceptable.

Use native radios styled as a small segmented control, or implement complete radio-group behavior if Obsidian styling makes native controls impractical: one selected value, Tab into/out, arrows to select, Space to activate, visible focus. Restore focus after repaint, including Live Preview. [WAI-ARIA radio-group pattern](https://www.w3.org/WAI/ARIA/apg/patterns/radio/).

View changes must not spawn Bob, rewrite Markdown, or invalidate numerical caches. Configuration changes affecting N or classification do require fresh reports. Include view and a report generation/content identity in the paint key: totals alone cannot detect a redistribution between types. N changes need repaint even when Worked is unchanged.

Do not make exact information hover-only. The focused column should expose its date/range, Worked amount, type breakdown, quality, and review state in readable details or an accessible description. Root labels and values remain directly readable. A Details disclosure can contain a semantic chart-data table including omitted categories. Existing `title` attributes alone are inadequate for touch/keyboard use. Check meaningful graphics and selected/focus states against contrast requirements in both themes; color must not be the only identity cue. [WCAG non-text contrast](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast).

**Apply one design to the existing hierarchy.** These are ISO periods; avoid introducing calendar-month note semantics.

| Period | Type chronology | Narrow-container treatment |
| --- | --- | --- |
| Week | Seven days with short dates and durations when they fit | Keep seven columns; wrap facts/legend and expose exact details on focus. |
| Quarter | Thirteen or fourteen ISO weeks, month ticks, review marks | Keep weeks; suppress repetitive durations before shrinking text. |
| Year | Fifty-two or fifty-three weeks grouped by quarter | Switch to four quarters with correctly aggregated type stacks. |
| All time | Quarters grouped by year | Switch to yearly aggregates when quarters no longer fit. For exceptionally long histories use an accessible bounded plot scroller, not silent truncation. |

Choose fallback from actual container width and tested minimum column/interaction widths, including gaps, rather than viewport width or the current 110px threshold. A weekly overview may tolerate 8–10px plot columns when group captions and focus details carry the text; seven-day labels need more room. Measure actual breakpoints. Bob should provide alternative aggregates; JavaScript selects a prepared layout rather than recalculating reporting values. Captions must name the unit: by week, by quarter, or by year.

The root ranking remains the whole selected period's top N at every width. Do not recalculate it from the visible chronology fallback. In narrow panes put each root label above its bar, retain right-aligned values, and allow two-line labels or an accessible full name. Keep panel order consistent; side-by-side desktop panels are unnecessary initially.

**Preserve the reporting boundary.** Rust owns identity, counted minutes, shares, labels, classification, folding, and ranking. The plugin owns layout, geometry, selection, focus, and navigation. Preserve the read-only one-report architecture and existing period boundaries.

A suitable additive contract is a new `strip` presentation object inside the schema-1 period report, with its own small version/capability indicator. It can hold true-type series and prepared column sets, ranked roots, effective limit, remainder/attribution rows, and display/quality metadata. Finalize names during implementation, but fix these meanings first. Keep `lanes`, `columns[].stack`, `children[].stack`, `homes`, and `theme_hues` intact for old consumers and briefs. Repurposing `stack` from roots to types without a dimension tag is a silent break.

New plugins should feature-detect the object. With old Bob, retain coherent legacy rendering and a quiet “Updated charts need a newer Bob” explanation; never show root data beneath a Types heading. The current decoder demands top-level `schema_version === 1`, so an unnecessary bump would break mixed-version rollout. Additive fields support backend-first delivery. A genuinely incompatible change must follow the project's breaking-change/release policy.

During implementation add this **proposed, not yet existing** setting to chezmoi's `home/dot_config/bob/config.yml`, merging with any `stats:` block added since this research:

```yaml
stats:
  period_strip:
    root_parent_limit: 5
```

Make 5 both the product default and explicit personal value. Validate in Rust as a positive integer; reject zero, negatives, floats, booleans, and malformed containers with an actionable error. Missing values use the default. Available positive named roots naturally cap the result. Deliberately large N creates a longer chart; it does not lose data. Return the effective limit in the report so report selection and client configuration cannot disagree. Device-local view choice is distinct from this source-controlled content limit.

Do not restrict all Stats root summaries to five. Keep `bob periods brief`, child `mostly` summaries, and parts-table root breakdowns intact unless separately redesigning them. The setting controls this strip's ranking. Also separate Worked data dependencies from fact visibility: `stats.hide` hiding the Worked tile must not accidentally remove the data needed by both charts.

The likely implementation locations, pinned to the revisions above, are:

| Repository/location | Purpose |
| --- | --- |
| bob-cli `src/native/stats/metrics.rs`: `pomodoro_components`, `theme_minute_parts`, Pomodoro evaluation | Add true-type attribution beside legacy component attribution, preserving totals, filters, and clocks. |
| bob-cli `src/native/pomodoro_themes/routing.rs`: `type_components`; `src/native/plan_budget/mod.rs`: `normalize_component` | Reuse classification and identity. |
| bob-cli `src/native/stats/report.rs`, `compute.rs`, `series.rs` | Carry additive type parts and catalog/display metadata through grouping. |
| bob-cli `src/native/periods/report.rs`: `build_report`, `build_lanes`, `build_parts`, `stack_value` | Produce the new strip projection and responsive resolutions in the existing pass; preserve old stacks. |
| bob-cli `src/native/config/stats.rs` | Nested setting, validation, default. |
| bob-plugins `plugins/bob-ledger-tools/src/239-plugin-period-strip-{model,render,parts,fence}.js` | Projection consumption, panels, memoization, navigation and states. |
| bob-plugins `239-plugin-day-strip-lanes.js`, `239-plugin-time-lanes-model.js`, Day/Stats type consumers | Shared preference, all-host repaint, hues, and consistent type drill-downs. |
| bob-plugins `plugins/bob-ledger-tools/styles.css` | Correct geometry, legibility, existing hue classes, focus/contrast, responsive behavior. |
| chezmoi `home/dot_config/bob/config.yml` | Explicit `stats.period_strip.root_parent_limit: 5`. |
| bob-cli `docs/periods.md`, `docs/stats.md`, `docs/task-types.md`; bob-plugins `docs/bob-ledger-tools.md` | Contract, Unclassified/Other meanings, interaction. Follow docs-memory workflow before edits. |

No new charting dependency is needed. Existing pure models, DOM/SVG helpers, roving navigation, fixture tests, and Chromium preview harness are enough. Modify source fragments and build `main.js` through the committed build system; do not edit generated entrypoints manually.

**Verification and remaining uncertainty.** I ran the existing focused Node tests in bob-plugins:

```sh
node --test scripts/test-ledger-tools-period-strip.cjs \
  scripts/test-ledger-tools-period-parts.cjs \
  scripts/test-ledger-tools-day-strip-lanes.cjs
```

All **32 tests passed**. They provide a baseline for period models, navigation, shared cached fetches, grouping, and Day-strip preferences. They do not verify the proposed feature, real-browser proportional geometry, or the missing period-switch propagation. I did not run a feature implementation, a live-vault timing benchmark, or an Obsidian visual acceptance session. The screenshot is direct visual evidence; source inspection supports the other findings.

Implementation acceptance should cover observable invariants and real UI behavior:

- **Attribution:** type-plus-label, multiple types with odd minutes, duplicate normalized components, unnamed/label-only history, no vocabulary, filters, and off-clock sessions. True-type parts conserve counted minutes without changing legacy `theme` results.
- **Ranking:** N=1, N=5, N above root count, ties, all zero, no named roots, unfiled/unlinked, duplicate labels, and a real root called `other`. Ranked rows plus remainder equal underlying attribution.
- **Period arithmetic:** week 53, fourteen-week Q4, ISO boundaries, current/future periods, pre-tracking and missing versus zero days, and both responsive resolutions. Narrowing never changes totals or type membership.
- **Interaction:** all modes change whole panels immediately in multiple Day/period hosts, without extra CLI calls; saved choice and focus persist; keyboard navigation and modified clicks reach the correct child. A non-day column's Stats action should use the whole child period, not only its start day.
- **Caching/compatibility:** same-total redistribution repaints; N/vocabulary edits refresh; stale data remains visibly stale; optional fields are additive; old/new backend/plugin pairings stay coherent.
- **Visual:** extend `scripts/preview-period-strip.cjs` and its template with seven types, long root names, one dominant root, many tiny slices, sparse data, Unclassified-heavy historical quarters, and all period kinds. Check light/dark at about 320/410/700/1000px containers, enlarged text, all modes, and actual Live Preview/Reading view. Assert no overflow and accurate proportions, not merely element presence.

Do not blindly retain the preview's old 240/306px height budgets when deliberately adding a readable ranking. Revise budgets explicitly and keep compact expectations for single-panel modes. After implementation run relevant Rust/CLI tests and plugin build/tests/docs checks, deploy through `bob plugins sync`, and apply chezmoi through its normal workflow. CLI changes ship through the release train; do not hand-edit version or changelog for coordination.

**Explicit requirement adjustments.** First, use a period-total root ranking rather than another timeline: trade immediate root trends for readability. Second, disclose omitted roots and attribution buckets despite limiting named rows to N. Third, make the three-way switch visible and panel-wide while retaining the existing local preference. Fourth, literal task types require a true-type projection, consistent Day/Stats drill-down semantics, and honest unmatched history. Fifth, allow Both more height and give year/all-time charts meaningful narrow aggregation. These are recommendations, not claims that the original request already specified them.

The main scope risk is the type/label accounting change. Review its additive contract and regression coverage before landing the visual layer. If implementation capacity is constrained, the root ranking and switch/geometry improvements can ship first with the old chart honestly labeled; do not ship a falsely named type chart as a shortcut. The completed feature should still meet the full request.

**Recommended solution.** Build one read-only period-strip family with a task-type stacked timeline, a directly labeled top-N root-parent ranking, and explicit Types/Roots/Both control. Set `stats.period_strip.root_parent_limit: 5` in chezmoi when implementing, retain all attribution, and disclose the remainder. Compute true type attribution and numerical presentation in Bob, preserve legacy JSON meanings, and keep the plugin responsible for presentation and interaction. This is a worthwhile redesign: its beauty should come from clear hierarchy, accurate proportions, restrained color, and readable labels—not additional decorative charts.
