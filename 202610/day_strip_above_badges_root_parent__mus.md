# Day strip above the badges with root-parent working time

Research: move the day strip above the `bob-plan` badges, restore the old
tile look with only the overlap fixed, re-render the working-time bar by
root parent, reflect that in `dash_stats.md`, obsolete the `## Pomodoros`
heading total and the `rollup` frontmatter key, and add four glossary
strands. Ends with a recommended solution and explicit requirement
adjustments.

Swarm: `mus` report. Independently researched; no peer report consulted.

## Bottom line

**Do it, but not as written. Ship a three-part change with two reversals
of the request.**

1. **Placement: yes to above the badges, but move the whole strip, not
   just the facts line.** Order from top: facts line, then the
   working-time bar, then the badges, then `## Pomodoros`. The bar is the
   separator the request wants. Do not interleave facts above and bar
   below the badges; that splits one component across the plan block and
   breaks the screen-reader group label.
2. **Look: do not restore the old tile wall.** Fixing only the 30 px
   `<button>` overlap keeps ~60 history marks, a full-width bar, a legend,
   `Stats ↗`, and a chevron competing with the ledger at the top of the
   most-edited note. Keep the shipped two-line grammar
   (`docs/stats.md` "Day strip", epic `bob-cli-bz`), restore exactly one
   old affordance: per-fact day-scoped context on hover/focus, which the
   old sparkline provided and the new tooltip already mostly covers.
   The overlap fix alone is to delete `<button>` from the strip, which
   `bob-cli-bz` already did; reverting to buttons reintroduces the bug.
3. **Aggregation: yes to root parent, computed in the Rust engine as a
   new additive `root` dimension, not in the plugin.** Aggregate by area
   iff the task's residence note is an area note; otherwise aggregate by
   the outermost project whose parent is an area note. Replace the
   `rollup: subprojects` reporting behaviour with this, deprecate the key
   first, and remove the heading total only for new daily notes.

The rest of this report justifies each call, names the files and
functions that must change, and drafts the four glossary strands.

## Context: what shipped and what "old" means

### Shipped (epic `bob-cli-bz`, closed 2026-10-25)

- Plan `plan:202610/day_strip_under_the_badges.md`: two calm lines under
  the `bob-plan` badges, in Live Preview and Reading view, hosted inside
  the rendered `bob-plan` block.
- Line 1: five facts `worked, reviewed, done, created, review_closed`
  (`DAY_STRIP_METRIC_IDS` in
  `plugins/bob-ledger-tools/src/239-plugin-day-strip-model.js`), rendered
  `LABEL value` by `paintDayStrip` in `239-plugin-day-strip-render.js`.
- Line 2: segmented bar of `worked` minutes by **area**
  (`dayStripMix` → `statsPanelHomeRows(worked, report, "area", point)` →
  `statsPanelHomeAreaRows`), legend top-3 areas plus `+N`, meta
  `so far · HH:MM` on today only.
- No `<button>` elements, no history marks, no collapse, no `Stats ↗`;
  every fact and the mix are `span[role=link]`.
- Contract in `docs/stats.md` § "Day strip"; mount in
  `239-plugin-day-strip-plan-host.js`; registry in
  `239-plugin-day-strip-registry.js`; fence in
  `239-plugin-day-strip-fence.js`.

### Old (pre-`bz`, epic `bob-cli-bp` era)

- Five tiles × (label + value + 8 history marks), full-width colored bar
  belonging only to Worked, legend, `Stats ↗`, collapse chevron.
- Root cause of the clutter screenshot was layout, not density: Obsidian's
  `app.css` gives every `<button>` `height: 30px` plus inline-flex,
  padding, background, shadow. The strip reset background/border/shadow
  but not height, so labels/values/14 px marks overflowed a 30 px box.
  The preview harness did not load the Obsidian baseline, so geometry
  checks passed while the screenshot showed overlap. Repro was
  `button { display: inline-flex; height: 30px }`.
- The `bz` fix was therefore two things at once: kill `<button>`
  (correct) and delete density (a design choice). The request "just fix
  the overlap" asks to keep the first and revert the second.

### Why a straight revert is the wrong restoration

- At the top of the note, the old wall is ~104 px of chrome plus 60 tiny
  marks competing with the ledger the user is about to edit. At the
  bottom it was a receipt; at the top it is a header. Headers must be
  quiet.
- History marks invite day-to-day comparison on the most-opened page.
  That is the scoreboard risk prior Stats research flagged (R9): daily
  presence turns mirrors into targets. The Stats page already offers the
  8-day window one click away with the day pinned.
- Buttons are the actual bug. Any restoration that brings back
  `<button>` needs a height/padding reset that tracks every future
  Obsidian `app.css` change. Spans with `role=link` are immune by
  construction; the preview asserts `no <button>`.
- What the old look did well and the new look should absorb: each tile
  answered "and how does today compare" at a glance. The new tooltip
  (`metric.definition`, `date: display + so far`, tracking/reason/
  warning lines in `dayStripBuildFact`) already carries most of that.
  The gap is day-scoped context without leaving the note. Recommendation:
  keep two lines, enrich the tooltip with one prior-day delta for
  `worked` only (e.g. `Yesterday 4h 10m`), computed from the already
  fetched `D-7..D` report. No marks, no extra row.

## Placement: above the badges with the bar as separator

### Request

> Move the day strip to above the badges instead of below them ... the
> working time bar can act as a natural separator.

### Analysis

Current DOM (below badges):

```text
bob-plan block
  badges (TODAY / PENDING / NEXT / READY, theme, lints)
  div.bob-day-strip
    div.bob-day-strip-facts
    div.bob-day-strip-mix-row (bar + legend ... meta)
## Pomodoros
```

Proposed DOM (whole strip above badges):

```text
bob-plan block
  div.bob-day-strip
    div.bob-day-strip-facts
    div.bob-day-strip-mix-row
  badges
## Pomodoros
```

Visual rhythm becomes: quiet facts → one touch of area/root color (the
bar) → colored badges → ledger. The bar is a full-width rule with hue
segments, so it reads as a separator without adding chrome. Spacing
contract flips: `.bob-plan-has-day-strip > .bob-plan` bottom margin
moves to a top margin on the badges container, strip keeps
`margin-bottom: ~1rem` only in the below variant; in the above variant
the strip needs `margin-bottom: ~.5rem` and the badges keep their own
bottom margin.

Why whole-strip-above, not facts-above/bar-below:

- The strip root is `role=group` with one `aria-label`
  (`dayStripAriaLabel`: "Day stats for ..., Time by area: ..."). Splitting
  facts and bar across the badges splits the accessible group and forces
  two tab stops with a badges group in between.
- `dayStripPlanHost` repaints synchronously from cache and gates fetches
  on visibility. One stable child appended before the badges is one
  insertion point to protect from `paintPlanBlock`'s `el.empty()` on
  every 5 s repaint. Two insertion points double the protection logic.
- The skeleton-height guarantee (skeleton equals loaded height at every
  matrix width) is measured per strip. Split hosts need two coupled
  skeletons.

Reliability notes:

- `paintPlanBlock` empties the block on note/Tasks changes. The host must
  survive that whether it is first or last child. The `bz` repair (cold
  automatic host spawns 0 before visibility callback, sync cache paint,
  detached/excluded release, no-observer fallback) is placement-agnostic;
  moving the insertion point does not reintroduce the bug, but the
  plan-host tests
  (`test-ledger-tools-day-strip-plan-host.cjs`,
  `test-ledger-tools-day-strip-hosts.cjs`) must add above-variant cases.
- Future daily notes without a `bob-plan` block (pre-2026-09-29) still
  show no automatic strip; the `bob-day-stats` fence stays the explicit
  path. No fence stand-down.
- Mobile still renders nothing, never an error card.

Alternative considered and rejected: keep below badges. Below is calmer
(color badges, then quiet facts, then one color touch) and matches the
shipped contract. But the request's separator intuition is right: above,
the bar earns its pixels twice (data + divider), and the badges sit
directly above `## Pomodoros`, which is where the eye goes to work. The
cost is one design-contract rewrite and preview-matrix re-baseline, both
small relative to the aggregation work.

Adjustment: move the whole strip above the badges; keep two lines; keep
no buttons/history/collapse/`Stats ↗`. Update `docs/stats.md` "Where it
renders", the `.bob-plan-has-day-strip` margin rule direction, and the
preview harness containers (mock badges move below the strip).

## Working-time bar: aggregate by root parent

### Definitions (proposed glossary sense)

- **Ancestry**: walk scalar `parent:` wikilinks from the task's residence
  note toward its ancestors, resolving each link with Bob's link rules.
  List-form, missing, self, and unresolvable parents end the walk; stop
  after 16 notes or on a repeat. This is the walk in
  `src/native/pomodoro_homes/resolve.rs` (`HomeResolver::resolve_note`,
  `MAX_PROJECT_DEPTH = 16`).
- **Top-level project**: a project note (`type: [[project]]`, `^prj`)
  whose own `parent` resolves to an area note (`type: [[area]]`), not to
  another project. A project whose parent is a project is a subproject,
  never top-level.
- **Root parent**: the task's aggregation home. If the task lives in an
  area note, the root parent is that area note. If it lives in a project
  note, the root parent is the outermost ancestor project that is a
  top-level project (walk up while the parent is a project; stop at the
  highest project whose parent is an area). Buckets stay buckets:
  `@unlinked` (no dedicated Task Link), `@unfiled` (link target has no
  area/project), `@review:*` (review sessions, never attributed from
  task links).

Examples:

- Task in `dev.md` (area) → root `dev`.
- Task in `sase.md` (project, parent `[[gtd]]` area) → root `sase`.
- Task in `sase_blog.md` (project, parent `[[sase]]`) → root `sase`.
- Chain `gtd` area → `sase` project → `sase_blog` project, task in
  `sase_blog` → root `sase`.
- Subarea chain `gtd` → `gtd_sub` (area, parent `[[gtd]]`) → `proj`
  (parent `[[gtd_sub]]`), task in `proj` → root `proj` (its parent is an
  area, `gtd_sub`). Task living directly in `gtd_sub` → root `gtd_sub`.
  Two tasks under the same top area but different subareas therefore
  split by subarea/project root, which is intended: the root is the
  highest finite container, not the topmost area.
- `@review:GTD` sessions → root `@review:GTD` (area for hue purposes is
  the resolved review name's top-level area per R4; display stays
  `GTD review`).
- Inboxes (`mac_inbox.md`, area with parent `inbox.md`) → root is the
  inbox area itself. This is correct: untriaged work should be visible
  as its own root, not folded into a top area.

### Why root parent is the right grain

- **Area-only** (today) over-merges: `sase` (job-adjacent product work),
  `bob` (tooling), and `job_apply` all sit under one area hue today and
  disappear into a single segment. Bryan thinks in projects; the bar
  should too.
- **Project-only** over-splits: every subproject becomes a sliver, and
  the legend's top-3 + `+N` fills with `sase_blog`-scale fragments.
  Root parent is the stable middle: finite containers that survive
  subproject churn.
- **Theme** is orthogonal (session names, not residence) and already has
  its own button. Do not conflate naming with filing.

### Where to compute it

**Engine (Rust), new additive `root` dimension. Do not group in the
plugin.**

Current engine shape (`src/native/stats/homes.rs`, `report.rs`):

- `Home { key, label, kind, area, area_label, subarea, hue,
  pre_rollup_chain }`; `HomeKind::{Project, Area, Bucket}`.
- Per-session splits produce `project: Vec<(key, minutes)>`,
  `area: Vec<(key, minutes)>`, plus apportioned variants; points carry
  `parts: { area, project, theme, ... }`,
  `parts_display`, `apportioned`; catalog `report.homes` maps key →
  `{ label, kind, area, subarea, path, hue, project_label, rolled_up }`.
- Plugin groups projects under top-level area for display and reads hue
  from `statsPanelHomeHue(report, key)` / catalog area hue.

Options:

| Option | Change | Verdict |
| --- | --- | --- |
| A. New `root` dimension in engine | `SessionSplit` gains `root`, `root_apportioned`, `lead_root`; points gain `parts.root`, `apportioned.root`; catalog gains `root_parent` per entry or a derived map | **Recommended.** Sums stay correct under multi-home splits (R5), apportioned tint keeps working, `in:`/`exclude_in:` can match roots, sessions drill-down and `sessions` list stay consistent, both surfaces (strip + Stats block) share one truth. Additive: keep `area`/`project` parts for compat and for the "update bob" fallback. |
| B. Plugin-only grouping of `project` parts by catalog parent chain | JS walks `homes[key].path` → parent frontmatter (not in report) or guesses from `area` + `rolled_up` | Rejected. The report does not ship parent links, so the plugin cannot walk ancestry without refetching notes. Duplicates the 16-hop resolver in JS, drifts from Rust, breaks apportioned math and `in:` filters. |
| C. Reuse `project` dimension with rollup rewritten to mean root | Change `rollup: subprojects` semantics to root grouping | Rejected. Overloads a deprecated key, breaks `in: [sase_blog]` pre-rollup filtering (H10) and the `rolled_up` descendant-count copy. |

Concretely, for each attributed session the engine already knows every
task home's full `Home` (with `pre_rollup_chain` and `area`). Root for
one task home is:

1. If `home.kind == Area` → `home.key`.
2. If `home.kind == Project` → walk `pre_rollup_chain` from the residence
   upward: collect consecutive project notes, stop before the first area
   note; the root is the last (highest) project in that run. If the
   residence's parent chain hits a non-project/non-area or ends, fall
   back to the residence key.
3. If bucket → the bucket key.

Then `root` minutes for the session follow the same R5 split as
`project`/`area` (even shares across distinct linked tasks, remainder to
ledger order; apportioned when ≥2 distinct roots). `lead_root` mirrors
`lead_project`. The catalog needs, per project key, its root key so the
plugin can link rows to home notes and show "includes N sub-projects"
analogs; the simplest additive field is `root: <key>` on each catalog
entry plus a `roots: { <root-key>: { count } }` summary, or reuse
`rolled_up` only for exact-rollup homes and add the new count separately.
Hue for a root: if the root is an area, its area hue; if a project, its
top-level area's hue (same rule as today: `color:` only on top-level
areas, `area_color_invalid` lint otherwise, FNV-1a fallback). Buckets
stay gray except `@review:*`, which inherits its area hue per R4.

`rollup: subprojects` interaction: root aggregation makes rollup
redundant for reporting. Deprecate, do not silently reinterpret (see
"Obsolete" below). While deprecated, rollup and root coexist: `project`
parts keep rollup behaviour, `root` parts ignore it. Filters
`in:`/`exclude_in:` keep matching `pre_rollup_chain` so
`in: [sase_blog]` still measures the child on its own even when its
report row folds into `sase`.

Edge cases the engine must pin in vectors:

- Subarea chains (above), inbox areas, closed/canceled projects (still
  valid homes), archived `done/*` and `ref` notes (walked through, never
  homes), self/cycle parents (stop), missing parents (stop, residence is
  root), review bridge (`[[#^gtd]]` same-day unnamed session →
  `@review:GTD`, root is the bucket).
- Multi-home sessions spanning two roots in one area: `area` shows one
  segment, `root` shows two, `apportioned` marks both. The strip bar and
  the Stats area-bar ordering (hue-slot order via
  `statsPanelHomeAreaRows`) gain a root analog ordered by hue slot, then
  label, buckets last in gray.

Performance: one extra `Vec<(String, i64)>` per session and one extra
parts map per point. The Markdown pass dominates (`docs/stats.md`
budgets ~370 ms on the live vault; homes-parts added ~5%). Root adds no
I/O and no new note reads beyond the existing resolver cache. No schema
bump required if the shape is additive (`parts.root` optional), but the
report is additive JSON either way; consumers ignore unknown dimensions.

### Display contract deltas (both surfaces)

- Bar segments: one per root, ordered by hue slot then label, buckets
  last gray (mirror `statsPanelHomeAreaRows`). Fixed width `~7.5em` on the
  strip; Stats page keeps its full-width area bar component with a root
  mode.
- Legend: top-3 roots by minutes plus `+N`; area tasks use catalog
  `project_label` (`"bob · area tasks"`); rolled-grouped roots show
  descendant count ("includes N sub-projects").
- Tooltip/`title`: "Time by root parent" plus one `<label> <display>`
  line per segment including overflow.
- Aria: "... Time by root parent: sase 3h 50m, dev 1h 35m." plus
  `No Pomodoros` empty state.
- Honest states unchanged except the dimension name; `not_tracked`,
  `missing`/warning, `0m`, redefined-`worked` (no `parts.root` → omit
  mix), future-day, skeleton, stale, unavailable, mobile rules all carry
  over.

## Stats dash: third button or new default

Current toggle (`239-plugin-stats-homes-render.js`
`statsPanelHomeToggle`): `Areas & projects` vs `Themes`, with
`homesView` persisted per view (`areas` default when available, else
`themes`). Pomodoro metrics open on "Where the time went".

Recommendation: **replace the default with root, keep three choices.**

- Choices: `Roots` (default when `parts.root` present) ·
  `Areas & projects` · `Themes`.
- Rationale: the request offers "third button or always root unless
  theme". Always-root-unless-theme collapses two distinct questions
  (which grain answers "where did the time go" vs which dimension am I
  inspecting) and strands users who need the area roll-up for GTD-cost
  review. Three buttons preserve the area view for the weekly prune
  ("check hours by area") while making root the first answer for daily
  sense-making. State migration: if stored `homesView === "areas"` and
  `parts.root` exists, keep `areas` (do not yank existing users); new
  views default to `roots`. Availability: `roots` disabled with the same
  "Update bob" note when the report predates the dimension, exactly like
  `areas` today.
- Copy: button label `Roots`; header `Where the time went · <span> · <total>`;
  tooltip/disclosure "Grouped by root parent · from Task Links" (extends
  the existing "Grouped by today's note tree · from Task Links" footer,
  R10). Keyboard: same `homesView` focus keys plus one new
  `panel-home-view-roots` key.
- Alternative rejected: two buttons with `Areas & projects` silently
  redefined as roots. That breaks the H-vector contract and every
  screenshot/test that asserts area rows, and it removes the only
  area-grain view without an explicit decision record.

Day strip follows the same default: roots when present, areas as fallback
for old reports (`hasAreaParts` check gains a `hasRootParts` first
branch in `dayStripMix`). No per-strip toggle; the strip is a glance, the
page is the control.

## Obsolete two things

### 1. `## Pomodoros (…)` heading total

Today each daily note's H2 carries a live Dataview inline query, e.g.:

```text
## Pomodoros (`= durationformat(...)`)
```

summing `t` over completed rows under the section. The day strip's
`WORKED` fact now duplicates it.

- Do not bulk-rewrite 580 daily notes. The query is live text in every
  existing file; a bulk edit is git noise across the vault for zero
  semantic gain, and `vault-git-sync` would sync hundreds of touched
  files across athena/apollo/Mac.
- Change the daily template (`~/bob/_templates/daily.md`) so new notes
  use a bare `## Pomodoros`. Document in `docs/plan.md` that the heading
  total is retired for new notes and the strip is the source of truth;
  old notes keep their query until naturally superseded. Optionally add
  a one-shot `bob task archive`-style migrator only if Bryan asks; do
  not invent one in this change.
- Reliability note: the Dataview query and `worked` already agree by
  construction (both sum closed `[t::]`; engine F7 pins parity). Removing
  the query loses no verification; the parity test stays.

### 2. `rollup: subprojects` frontmatter

`Rollup::{Off, Subprojects, Invalid}` in
`src/native/pomodoro_homes/{facts,resolve}.rs`, honoured in
`HomeResolver::resolve_note` (highest opted-in project wins) and
surfaced as `rolled_up` counts, `rollup_invalid` lints, and
`docs/pomodoro-homes.md` R2 / `docs/projects.md` "Rollup (reporting
only)". Root aggregation subsumes its reporting job.

- Phase it: (a) document `rollup` as deprecated (still honoured for
  `project` parts, ignored for `root` parts); (b) emit the existing
  `rollup_invalid` lint unchanged but add a deprecation hint pointing at
  roots; (c) after one release train, remove parsing/recognition and
  treat the key as unknown (today's behaviour for unknown keys is to
  ignore). Do not reinterpret `rollup: subprojects` as root in place;
  that silently changes `in:` filter results for `H9`/`H10` vectors.
- Test fallout is bounded but real: `pomodoro_homes/tests.rs`
  (`rollup_accepts_only_off_or_subprojects`,
  `rolled_home_keeps_the_pre_rollup_note_chain`), `stats/homes.rs` H3/H8–H10
  vectors, `tests/fixtures/stats/*`, and the shared conformance vectors
  (`tests/fixtures/pomodoro_homes/vectors.json`,
  `rollup-archive-review`, `rollup-depth-and-parent-shapes`). Update
  vectors to assert both `project` (rollup) and `root` (rollup-free)
  splits during deprecation; delete rollup cases on removal.
- Docs: `docs/pomodoro-homes.md` R2 becomes a "Retired" section, not a
  silent delete; `docs/projects.md` keeps the `rollup` marker line only
  while deprecated. Per `docs.md`, behaviour changes go to the contract
  plus only the guide steps made incorrect.

## Glossary strands (drafts for `sase memory write`)

Four new `type: reference` strands in the `glossary` web. Titles and
aliases follow the request; bodies follow the existing strand style
(definition, residence/derivation rule, what it is not, linked terms).

### `glossary:top-level-project` — "Top-Level Project" (aka top project)

> A project note (`type: [[project]]`) whose own scalar `parent:`
> wikilink resolves to an area note, not to another project. Its `^prj`
> line carries the project's date and dependency links; while that line
> is Blocked, every open resident is Blocked
> (`decisions:projects-block-from-prj-line`). A project whose parent is
> another project is a subproject, never top-level however large. The
> top-level project is the finite container root aggregation reports
> under. Not a top-level area, not a theme, not a rollup group.

Links: `[[glossary:project-note]]`, `[[glossary:area-note]]`,
`[[glossary:root-parent]]`.

### `glossary:root-parent` — "Root Parent"

> The task's aggregation home for the working-time bar and the Stats
> roots view. Walk the task's `parent:` ancestry (see
> `glossary:top-level-project`): if the residence note is an area note,
> the root parent is that area; if it is a project note, the root parent
> is the outermost top-level project on that chain; buckets
> (`@unlinked`, `@unfiled`, `@review:*`) are their own roots. Two tasks
> in different subprojects of one top-level project share a root; two
> tasks in different areas never do. Computed at read time from today's
> note tree (`decisions` R10 analogue); moving a task regroups past
> minutes but never changes totals. Not a home (homes are per-task
> attributions; roots are per-session roll-ups), not a theme, not a lane.

Links: `[[glossary:top-level-project]]`, `[[glossary:area-note]]`,
`[[glossary:project-note]]`.

### `glossary:day-strip` — "Day Strip"

> The two-line receipt under (proposed: above) the `bob-plan` badges on
> canonical daily notes: line 1, five `LABEL value` facts (`worked`,
> `reviewed`, `done`, `created`, `review_closed`); line 2, the
> working-time bar plus legend and `so far · HH:MM` on today. Rendered by
> `bob-ledger-tools` inside the plan block in Live Preview and Reading
> view; never writes note bytes. Clicking a fact or the mix opens
> `dash_stats.md` with that day pinned. The explicit
> ` ```bob-day-stats ` fence embeds the same strip anywhere. Not the
> Stats page, not the `## Pomodoros` ledger, not a Dataview query.

Links: `[[glossary:stats-dash]]`, `[[glossary:root-parent]]`.

### `glossary:stats-dash` — "Stats Dash" (aka stats dash)

> Shorthand for `~/bob/dash_stats.md` (aliases Stats, Dashboard Stats):
> one empty ` ```bob-stats ` fence rendering the schema-1 `bob stats`
> report, opened from the dashboard STATS chip. Home of the focus chart,
> the "Where the time went" panel (Roots / Areas & projects / Themes),
> and day pinning. The day strip links here; it never duplicates its
> controls. Not the dashboard (`dash.md`), not `bob stats` CLI output.

Links: `[[glossary:day-strip]]`.

Creation route (not done in this research turn): `sase memory write`
per the memory skill, one strand file each under
`sase/memory/glossary/<slug>.md` with `type: reference` frontmatter and
aliases above. Do not hand-edit memory files without that skill.

## Design: intuitive, reliable, beautiful

Intuitive:

- One component, one place: the whole strip lives on one side of the
  badges. Facts read `LABEL value` like the badges above/below them.
  The bar answers exactly one question ("where did the working time
  go, by root") and its tooltip lists every segment including `+N`
  overflow. Every fact and the mix deep-link to the Stats page with day
  pinned and the right panel revealed. No history, no collapse, no
  second link affordance to learn.
- Roots use project labels users already read (`sase`, `bob`,
  `job_apply`, `gtd · area tasks` for area-resident work). Buckets keep
  fix-it copy (`link the task to attribute it`, `file the task in an
  area or project`), so an unfamiliar segment teaches its own repair.

Reliable:

- Engine owns the math; plugin owns layout. No JS chain-walking, no
  duplicated 16-hop logic, no drift between strip and page.
- Additive rollout: old reports without `parts.root` render the area bar
  with zero code-path errors (`omitted` mix → line 2 holds only meta on
  today, absent on past days). New reports render roots. The preview
  matrix covers both plus skeleton/empty/stale/unavailable/redefined-
  `worked`/many-roots/long-labels/wide-values at 410/540/700 px ×
  light/dark, asserting no-overflow, no-overlap, baseline alignment,
  skeleton-height parity, height budget, fits-on-one-line at ≥540, and
  no-`<button>`.
- Refresh budget unchanged: cache-first paint, visibility-gated fetch,
  visible∧dirty∧aged re-run, one spawn at a time per cache key. Moving
  the host above the badges does not change the gate; add above-variant
  host tests (first-visible, first-offscreen, detached/excluded,
  no-observer fallback, rollover repaint).

Beautiful:

- Frame: no card/border/rule/background/shadow/radius on the strip;
  separation is spacing only. Above-badge variant: strip
  `margin-bottom: ~.5rem`, badges keep their bottom margin to
  `## Pomodoros`.
- Type: `font-interface`, `~.875em`, `~1.45` line height; labels
  `~.75em` uppercase `~.06em` tracking 600 muted; values `1em` 600 normal
  tabular; legend names muted, minutes normal tabular; meta faint
  tabular. Same tokens light/dark.
- Rhythm: facts wrapping flex, `column-gap ~1em`, baseline-aligned;
  line 2 `~.25em` below; mix bar fixed `~7.5em` × 5 px fully rounded
  with 2 px gaps; legend dots `.5em`; narrow widths ellipsis, never wrap.
- Colour: root hues only (area-hue slots via top-level area; buckets
  gray; review inherits area hue). No status/metric/red-green encoding.
- Motion: none; values swap in place; `prefers-reduced-motion` hygiene
  kept. Hover pill (`--background-modifier-hover`) with negative-margin
  padding so text never shifts; `:focus-visible` 2 px accent outline.
- Height budget (16 px base): ≤48 px one-line, ≤72 px wrapped at 410.
  Skeleton is transparent-text placeholders with identical line boxes.

## Critique of the request as written

| # | Request clause | Verdict | Reason |
| --- | --- | --- | --- |
| 1 | Move strip above badges, bar as separator | Accept with fix: whole strip above | Split placement breaks the accessible group and doubles host-protection logic. Bar-as-separator works only as the strip's bottom edge directly above badges. |
| 2 | Restore old look, just fix overlap | Reject revert; accept overlap-fix principle | Overlap fix = no buttons (already shipped). Old density at the top of the editing surface is header clutter plus scoreboard pressure. Restore context via enriched tooltip, not marks/chevron/link. |
| 3 | Change where/how the bar renders | Accept: re-render by root, same component | Bar stays line 2 of the strip; only its grouping changes. No new component, no new mount. |
| 4 | Root-parent definition | Accept with subarea clarification | Definition is sound; pin the subarea reading (residence area = its own root; highest project whose parent is any area = root). Without this, `gtd_sub` cases are ambiguous. |
| 5 | Stats dash: third button or always-root | Decide: three buttons, Roots default | Always-root removes the area grain the weekly prune needs. Three buttons preserve both; default Roots for new views, respect stored `areas`. |
| 6 | Four glossary strands | Accept; drafts above | Names collide with nothing existing; aliases (`top project`, `stats dash`) are safe. Create via memory skill, not direct file writes. |
| 7 | Drop `## Pomodoros` heading total | Accept for new notes only | Bulk rewrite is sync noise; template-only retirement plus docs note is sufficient. Strip becomes source of truth going forward. |
| 8 | Remove `rollup` frontmatter support | Accept as deprecate-then-remove | Silent removal breaks `in:` filters and vectors. Deprecation hint + one-train delay is the safe path. |
| 9 | Lead the design | Done in this report | Visual contract deltas, honest states, and acceptance criteria above are the design lead. |

## Recommended solution (phased)

### Phase 0 — Decisions and memory (small)

1. Record the placement (whole-strip-above), no-revert (two-line
   grammar kept), and roots-default (three buttons) choices where the
   project records decisions (decision web, not inline edits to
   immutable records).
2. Create the four glossary strands via the memory skill with the drafts
   above.

### Phase 1 — Engine: additive `root` dimension (bob-cli)

1. `src/native/pomodoro_homes/resolve.rs`: add `root_for_home(home) ->
   String` following the walk rule; expose `pre_rollup_chain` use already
   present. `facts.rs`: no frontmatter change.
2. `src/native/stats/homes.rs`: extend `SessionSplit` with
   `root`/`root_apportioned`/`lead_root`; populate in `split_from_homes`
   and `split_from_kept`; extend catalog entry with `root: Option<String>`
   (or per-key root map); keep `area`/`project` untouched.
3. `src/native/stats/{compute,report,render,metrics}.rs`: thread
   `parts.root`, `parts_display.root`, `apportioned.root`,
   `parts_summary.root` through; additive serialization (omit when
   empty); update H-vector docs table with `H16 root ...` rows;
   deprecate `rollup` in docs strings (hint text, no behaviour change).
4. Vectors: `tests/fixtures/pomodoro_homes/vectors.json` +
   `src/native/pomodoro_homes/tests.rs` (subarea, inbox, cycle, review
   bridge root cases); `src/native/stats/homes.rs` tests (H3 analogue by
   root, multi-root apportion, `in: [child]` still measures child).
5. Gates: the repo's configured `just check` (and `just check-full` if
   the project names it as the long gate); `bob stats show worked -f json`
   golden diffs gain `root` without losing `area`/`project`.

### Phase 2 — Plugin: roots view + strip above badges (bob-plugins)

1. `239-plugin-stats-panel-models.js`: add `statsPanelHomeRootRows`
   (hue-slot order, buckets last), `hasRootParts`, root label/row helpers
   reusing `statsPanelHomeCatalog`; keep area/project helpers.
2. `239-plugin-stats-homes-render.js`: three-way toggle
   (`roots`/`areas`/`themes`), default `roots` when available, persisted
   `homesView` migration (respect stored `areas`), `panel-home-view-roots`
   focus key, "Update bob for roots" fallback, footer copy "Grouped by
   root parent · from Task Links".
3. `239-plugin-day-strip-model.js`: `dayStripMix` prefers
   `parts.root` (title "Time by root parent"), falls back to `parts.area`;
   legend top-3 roots + `+N`; aria "... Time by root parent: ...".
4. `239-plugin-day-strip-plan-host.js` + `registry.js` + `render.js`:
   insert host before badges; flip margin rule; no other logic change.
   Styles: above-variant spacing, same type/rhythm/colour/motion budget.
5. Preview: move mock badges below strip in both Live Preview and Reading
   cells; add many-roots and old-report (area-only) cases; keep all seven
   assertions plus `roots` tooltip/aria checks. Attach PNGs as artifacts
   on the phase bead.
6. `239-plugin-stats-panel-render.js`: roots table (bar + rows +
   descendant counts + sessions drill-down + fix-it copy for buckets).

### Phase 3 — Contracts and template

1. `docs/stats.md`: Day-strip placement (above), line 2 "by root
   parent", fallback note, focus-chart "Roots" panel docs.
2. `docs/pomodoro-homes.md` R2: mark rollup deprecated, define root with
   the subarea rule; `docs/projects.md`: rollup marker deprecation note;
   `docs/plan.md` + `docs/dashboard.md`: heading-total retirement for new
   notes, strip as source of truth.
3. Daily template: new notes use bare `## Pomodoros`. No bulk rewrite.
4. `docs/reference/json-outputs.md` + CLI reference if `root` appears in
   human output; `just docs-check`.

### Phase 4 — Removal (one train later)

Remove `rollup` recognition (treat as unknown key), delete rollup
vectors, and close the deprecation. Only after the roots view has ridden
the release train and no `rollup_invalid` lints remain in the wild.

## Acceptance

- Strip renders above badges in both views on today + past + skeleton +
  empty + stale + unavailable + many-roots + old-report at 410/540/700 ×
  light/dark with zero overflow/overlap, baselines aligned, skeleton
  height parity, height budget met, facts on one line at ≥540, no
  `<button>`, screenshots inspected.
- `bob stats -f json` on the golden vaults shows `parts.root` summing to
  `worked` alongside unchanged `area`/`project`; `in: [child]` still
  measures the child; apportioned tint appears exactly for multi-root
  sessions.
- Stats page defaults to Roots on new views, respects stored Areas, falls
  back with "Update bob" on old reports; strip shows roots with area
  fallback.
- New daily notes template bare `## Pomodoros`; old notes untouched.
- `rollup` deprecated with hint, not reinterpreted; removal deferred.
- Both repos' configured gates pass (`just check` family in bob-cli;
  `npm run build`, `npm test`, `npm run validate`, `npm run docs:check`
  in bob-plugins; `bob plugins sync` after plugin commits).

## Evidence and provenance

- Epic: `sase bead read bob-cli-bz` (closed 2026-10-25; plan
  `plan:202610/day_strip_under_the_badges.md`).
- Strip model/painter: `239-plugin-day-strip-model.js`
  (`DAY_STRIP_METRIC_IDS`, `dayStripMix`, `dayStripMetaText`,
  `dayStripAriaLabel`, `dayStripModel`), `239-plugin-day-strip-render.js`
  (`paintDayStrip`), hosts/registry/fence fragments, `styles.css`
  Day-strip section.
- Stats panel: `239-plugin-stats-panel-models.js`
  (`statsPanelHomeRows`, `statsPanelHomeAreaRows`, `statsPanelHomeHue`,
  `statsPanelHomeCatalog`, `statsPanelHasHomes`),
  `239-plugin-stats-homes-render.js` (`statsPanelHomeToggle`,
  `Areas & projects`/`Themes`), `239-plugin-stats-panel-render.js`
  (`statsPanelPomodoro`, `statsPanelHomeTable`).
- Engine: `src/native/pomodoro_homes/{mod,facts,resolve,session}.rs`
  (`resolve_note`, `pre_rollup_chain`, `Rollup::Subprojects`,
  `MAX_PROJECT_DEPTH`), `src/native/stats/{compute,homes,report}.rs`
  (`parts.area/project/theme`, `HomeCatalogEntry`, H2/H3 vectors),
  `docs/stats.md` (§§ Homes fixture, Obsidian Stats block, Day strip),
  `docs/pomodoro-homes.md` (R1–R10), `docs/dashboard.md` (child pages),
  `docs/plan.md` / `docs/reference/vault-format.md` (ledger, Today).
- Prior swarm research read as shared context (not peer consultation):
  `research:202610/daily_note_day_strip/` (mus report and final),
  `research:202610/bob_daily_stats/` (heading-total parity F7,
  `## Pomodoros (= durationformat(...))` query shape),
  `research:202610/pomodoro_area_project_attribution/`.
- Glossary strand format verified via `sase memory read
  glossary:area-note glossary:project-note` and
  `sase/memory/glossary/` listing; reference-memory bodies read via
  `sase memory read` (`sase_beads.md`, `cli_rules.md`, `docs.md`,
  `obsidian.md`, `sase_artifacts.md`, glossary web).
