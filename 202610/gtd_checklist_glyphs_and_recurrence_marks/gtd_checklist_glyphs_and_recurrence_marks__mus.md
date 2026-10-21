# In-place icons for `#gtd #pre` / `#gtd #post` and the `repeat` field

Researcher: mus (independent swarm report, suffix `__mus`).
Question: how to render nice intuitive icons in place of the PRE/POST
checklist tags, and what (if anything) to do about the `repeat` task
property. Lead the design; critique the plan; end with a recommended solution.

## TL;DR recommendation

Do both, display-only, in `bob-ledger-tools`, following the
`docs/task-tag-marks.md` / `docs/date-marks.md` mark architecture exactly:

1. **PRE/POST: one combined glyph per pair.** `#gtd #pre` renders as a
   single sunrise icon; `#gtd #post` (without `#pre`) renders as a single
   sunset icon. Constant violet tag-family ink, not a status color.
2. **`repeat`: collapse the whole `[repeat:: RULE]` / `(repeat:: RULE)`
   field to a single monochrome repeat glyph, no visible label.**
   The full rule moves to the tooltip; cursor/click reveals the raw field
   for editing. Ship this icon-only form first; defer compact labels
   (`Mon`, `30d`) to a follow-up only if the at-a-glance cadence is missed.

No storage change, no new tags or fields, no Rust / `bob-cli` change, no
Tasks-setting change. One session toggle restores today's rendering.

## Current state (verified in this checkout and vault)

**PRE/POST membership** is exact whole-token tags, case-insensitive:
`#gtd` plus `#pre` is PRE; `#gtd` plus `#post` without `#pre` is POST
(`docs/freshness.md` section 4, `checklist(t)`; decision
"Review Walk Is Tiered"; vectors CL5/CL6). Checklist scope admits status
symbols `space * / ?`; recurring, canonical daily-note, and Today-linked
rows are admitted; hidden, dependency-blocked, future-scheduled, and
template/conflict rows are not. Rows resolve only by completion, never by
a stamp.

**Vault shape.** All live PRE/POST rows are in `gtd_daily.md` (about 15
open rows at the time of reading): one `#gtd #post` Morning-review row,
one `#gtd #pre` SASE-cleanup row, one `#gtd #post` weekly-prune row, and
roughly twelve `#gtd #pre` daily habits. Every one carries
`[repeat:: every day when done]` (or `every week on Monday when done` for
the prune row) plus `[created::]` and usually `[scheduled::]`. Counts
from the vault: 952 of 973 `[repeat::]` occurrences are exactly
`every day when done` (about 98%), with 4x `every week on Monday when
done`, 4x `every 30 days when done`, 4x `every 28 days`, 5x
`every month on the 1st`, 2x `every week on Sunday`, 2x `…`. So the
field that costs the most space carries the least information.

**How it renders today.** Each checklist row shows two violet tag pills
(`#gtd`, `#pre` or `#post`) plus the full 30-character
`[repeat:: every day when done]` text, plus created/scheduled marks. A
typical row is 150 to 400 characters; the Morning-review POST row is the
longest line in the daily note. The two pills cost about 9 characters
plus pill chrome; the repeat field costs about 31 characters including
the trailing space. Across the visible `gtd_daily.md` Tasks section that
is on the order of 450 characters of pure repetition.

**Parsers.** `bob-cli` (`src/native/dataview/tasks/task.rs`,
`src/native/freshness/*`, `src/native/task_fields.rs`), Tasks in
Dataview format (`taskFormat: dataview`, `globalFilter: #task`,
`removeGlobalFilter: false` in
`.obsidian/plugins/obsidian-tasks-plugin/data.json`), and Dataview all
read the stored `#gtd #pre` / `#post` tokens and the `[repeat::]`
field. Tasks emoji-format recurrence (`🔁`) is the established symbol
for this concept (`src/native/dataview/tasks/render.rs` renders the CLI
`repeat` column as `🔁`; Tasks `recurrenceSymbol` is `🔁`), but the vault
stores the Dataview form, so Obsidian currently shows raw
`[repeat:: …]` text, not the emoji.

**Existing mark precedent.** `docs/task-tag-marks.md` (hash glyph for
`#task`, open-book for `#task #ref`) and `docs/date-marks.md` (plus,
hourglass, check, circle-slash + short labels) define the architecture
to reuse: Live Preview `ViewPlugin` + `Decoration.replace` over exact
byte ranges, reading-view markdown post-processor (sort order 50) that
annotates `a.tag` in place, one shared CSS mask per glyph
(`viewBox 0 0 16 16`, stroke ~1.8-1.9, round caps), monochrome or single
constant ink, tooltip lines joined with `\n` that never contain `::`
(because Dataview re-scans `innerHTML`), `role="img"` + `aria-label`,
cursor-or-click reveals raw text, source mode raw, session toggle,
without-plugin vault unchanged, PDF export via `print-color-adjust`,
conformance vectors plus a Bryan live-verification checklist, Tasks
query results handled CSS-only. Any new mark must follow this contract
or explain why it diverges.

## PRE/POST design

**Recommended glyphs: sunrise for PRE, sunset for POST** (Lucide
`sunrise` / `sunset`, drawn in the same stroked 16x16 language as the
hash and book: arrow + horizon + sun rays, `stroke-width` about 1.8,
round caps and joins, used as a CSS mask). Rationale:

- The metaphor is already in the product: PRE is the opening checklist
  walked before NEW, POST is the closing checklist walked after ROTTEN
  (`docs/concepts/freshness-and-the-review-walk.md`, tiers
  PRE → … → POST). Sunrise = "open the day", sunset = "close the day".
  No learning curve for the one person who matters.
- They form a symmetric visual pair (same sun, arrow up vs down),
  which is exactly the relationship PRE/POST have. Door, flag, play,
  and chevron alternatives do not pair as cleanly, and `▶`/`✓`-family
  shapes collide with the checkbox (done), the Next/Ready lane tints,
  and the date-mark check.
- Both are proven at small sizes in Lucide; the sun disc plus horizon
  line stays legible at `0.8em`, unlike a filled tag silhouette (blob)
  or `list-todo` (too busy) — both already rejected in
  `docs/task-tag-marks.md` for the same reason.

**One slot, not two.** `#gtd #pre` (three tokens counting `#task`) must
render as `#task`-hash + one sunrise, not hash + two pills. Same for
POST. Eligibility must mirror `checklist(t)` exactly: whole-token,
case-insensitive (`#GTD #Pre` pairs; `#gtd/pre`, `#gtd/pre`,
`#pressed_juice` never pair), `#gtd #pre #post` resolves to PRE (match
CL6, with the existing `checklist_tag_conflict` lint as the signal),
only on task lines (quote- and list-aware, same
`freshnessTaskStatus`-style gate as TT4/TT5), skipped inside inline code
and code blocks, skipped on plain bullets/paragraphs/headings. A lone
`#gtd` (as in `best_practice.md` prose or any non-checklist task) keeps
its violet pill: the pill is then the honest signal that the row is not
a checklist row.

**Ink: constant violet tag-family, never status colors.** The mark says
"review tier", not state. It must not use red (Blocked), orange
(attention/ROTTEN), yellow (In Progress), green (Next/fresh), or blue
(Ready) — the same hue table as `docs/task-tag-marks.md` section "Ink".
Violet keeps the "this came from a tag" affordance next to the teal
`#task` hash and the violet `#prj` pill, and it is the only hue whose
meaning ("tag-derived grouping") survives. Tones follow the family
rule: full ink at rest, hover capsule, 40% mix toward `--text-faint` on
closed rows (`x X -`), transitions off under
`prefers-reduced-motion`. One open question for implementation: verify
the violet stays legible on the red Blocked line tint, since several
PRE rows are `[?]` — the same check the teal hash already passes, but
re-verify with the sunrise/sunset geometry.

**Tooltip and labels.** No `::` anywhere (Dataview rule). Suggested:
PRE tooltip `#gtd #pre · opening checklist`, accessible label
`Opening checklist (PRE)`; POST tooltip `#gtd #post · closing checklist`,
label `Closing checklist (POST)`. Keep the `#gtd #pre` / `#gtd #post`
literal in line 1 so tag search stays discoverable, exactly as the hash
tooltip keeps `#task`.

**Surfaces.** Same two hosts as the hash: Live Preview widget
(`Decoration.replace` over the whole `#gtd … #pre` span, whitespace
handling to be pinned in the contract — simplest: cover from `#gtd`
start to `#pre`/`#post` end inclusive so no orphan pill or double space
remains, and reveal the whole span on any inclusive cursor touch);
reading view post-processor annotates the two `a.tag` anchors in place
(first becomes the icon, second hidden in place like the `#ref` hiding
rule, both kept in the DOM for copy and Dataview round-trip). Tasks
query results: the rows that matter (`gtd_daily.md` section, `dash.md`
excludes its own path) are rarely inside Tasks results, but specify it
anyway — CSS-only, same-body-class mechanism, icon (not hidden), because
unlike `#task` (zero information in Tasks results) the tier *is*
information there.

**Pickers and display text.** Strip `#gtd #pre` / `#post` from display
strings the same way `#task` (and the `#ref` partner) are already
stripped in task pickers, the Task Card header, and inbox-route
subtitles. Stored lines keep both tags so Tasks, Dataview,
`bob query`, grep, and `bob-cli` keep working.

## `repeat` design

**Recommended: icon-only collapse.** The entire `[repeat:: RULE]` (and
parenthesized `(repeat:: RULE)`) field renders as one small monochrome
repeat glyph (Lucide `repeat`, the stroked twin of Tasks' `🔁`), no
visible label. Tooltip holds the full rule reworded without `::`, e.g.
`Repeat every day when done`; accessible label `Repeats every day when
done` (or `Recurring: …`). Cursor or click anywhere on the mark reveals
the raw field for editing; the mark covers exactly the field span,
delimiters included.

Why icon-only instead of icon-plus-label:

- 98% of occurrences are the identical string `every day when done`.
  Any label (even `daily`) repeats per-row information the tooltip and
  the `⧗` scheduled mark already carry. The prune row's title ("Weekly
  prune") already distinguishes the one weekly row; the monthly/date
  rows are distinguishable by title plus scheduled date.
- A short-label scheme (`daily` → nothing, `every week on Monday` →
  `Mon`, `every 30 days` → `30d`, `every month on the 1st` → `1st`)
  requires parsing free-English recurrence strings. That grammar
  belongs to Tasks, not to us; every new phrasing Bryan types is a new
  branch, a new test vector, and a new way to lie. Icon-only has no
  grammar and cannot misrender a rule it does not understand.
- It matches precedent: `#task` (3,400 identical tokens) collapsed to
  a glyph with zero label because the token carries no per-row
  information. `repeat` on this vault is the same shape: 952 identical
  tokens plus a handful of exceptions better served by tooltip.
- Space saving is the point of the request: icon-only reclaims about
  30 characters per checklist row (about 450 characters across the open
  `gtd_daily.md` section), turning three-line wrapped rows into
  one-liners. Icon-plus-label gives back half the saving for almost no
  information.

**Ink: quiet monochrome grey, same family as `created +`.**
Recurrence is metadata, not state or identity. Do not tint by cadence
(daily vs weekly color-coding would invent a legend nobody asked for and
collide with lane/state hues). Resting tone on closed tasks follows the
family 40% rule. The glyph must read beside the teal hash, the violet
PRE/POST icons, and the date marks without competing: thin stroked
arrows at the same `0.8em` / `vertical-align: -0.1em` metrics as the
existing marks.

**Eligibility.** Any `[repeat:: …]` / `(repeat:: …)` field in the Tasks
suffix of a task line (both bracket and paren forms exist in the
scanners: `src/native/task_fields.rs`, freshness placement rule,
`task_complete` refusal check). Detection is the existing
`is-recurring` predicate, not a value parse: any value pairs, including
`…` and malformed values, because the mark is truthful about presence,
and the tooltip shows whatever is stored. Skip code spans/blocks; skip
non-task lines. If a line ever carries two repeat fields, mark each
(the repair-flag path, not the display path, owns the duplication
complaint).

**Tasks results and CLI.** Tasks query rows render recurrence via the
`🔁` component already; the Dash `short mode` + `hide …` presets govern
whether it appears there — out of scope for this mark, and explicitly a
non-goal (same non-goals list as `docs/task-tag-marks.md`: storage,
Rust CLI/TUI, `bob query`, search/backlinks/tag pane, source mode).
`bob dataview` CLI keeps rendering `🔁 RULE` text
(`src/native/dataview/tasks/render.rs`): terminal output has no
tooltip, so the text must stay there.

**Deferred label scheme (only if missed).** If after a week Bryan finds
he scans cadence without hovering, add a compact label *beside* the
icon for non-daily rules only, reusing the date-mark label grammar
(lowercase words, capitalized months): `Mon`, `1st`, `30d`. Daily rows
stay icon-only. This keeps the common case beautiful and pays the
grammar cost only for the exceptions. Do not ship this in phase 1.

## Critique of the plan (is this a good idea?)

**Yes, with the scope tightened as above.** The value proposition is
strong: the most-opened note in the vault (`gtd_daily.md`, every
morning) has its longest lines made of pure boilerplate — two pills
plus a 30-character constant plus created/scheduled stamps. Display-only
glyphs buy readability every day at zero migration cost, and the
reversibility story (cursor reveals raw, toggle restores pills, no
plugin = today's vault) is already proven by three shipped mark
families. The risk profile is lower than it looks: unlike the tiered
walk (two evaluators kept in sync under vectors), this is one JS+CSS
surface with no Rust, no evaluator, no lane/bucket/state change.

Adjustments I would insist on (calling them out as requested):

1. **Treat the pair as one slot.** Rendering `#gtd` and `#pre` as two
   separate icons preserves the noise the request wants to remove and
   doubles the icon-learning burden. One sunrise, one sunset.
2. **Keep violet for PRE/POST; grey for repeat.** Do not color PRE/POST
   by "morning vs evening" warmth (orange/blue) — those hues already
   mean attention and Ready. Shape carries the distinction; ink carries
   only the family.
3. **Icon-only repeat first; labels later or never.** The request is
   unsure what repeat should become — the data answers it: 98% daily
   means any visible label is noise 98% of the time. The tooltip plus
   the scheduled mark cover the exceptions.
4. **Do not touch storage, Tasks settings, or the global filter.**
   Rewriting ~15 lines (or ~970 repeat fields) to emoji/properties, or
   flipping `removeGlobalFilter` / `hide tags`, breaks `bob-cli`
   parsers, capture, Tasks edit modals, Dataview queries, and `bob query`
   for a cosmetic win. The display-contract principle ("Display-only:
   stored form stays the only stored form") exists precisely for this
   temptation.
5. **Specify Tasks-results behavior even though it barely triggers.**
   Unspecified surfaces are where mark projects rot: pick CSS-only
   icons for PRE/POST in Tasks results (information-preserving) and
   leave repeat to Tasks' own `🔁` rendering there.
6. **One implementation pass, not two.** PRE/POST and repeat share
   eligibility machinery (task-line gate, code exclusion, cursor
   reveal, toggle, post-processor order). Two separate fragments that
   each scan every task line double the Live Preview cost and invite
   overlapping-range bugs (cf. TT16 disjointness vector). One core
   scan, two glyph kinds.

What I would *not* do: per-cadence repeat colors, sunrise/sunset with
different inks, hiding lone `#gtd`, hiding repeat in a way that loses
the tooltip rule, or a settings UI with per-mark switches beyond the
one existing session toggle. Each adds knobs without adding mornings.

## Implementation sketch (for the plan author)

- New display contract `docs/gtd-marks.md` (PRE/POST) plus a repeat
  section or a sibling `docs/repeat-marks.md`, written in the style of
  `docs/task-tag-marks.md` / `docs/date-marks.md`: What-you-see,
  Principles, glyph geometry, ink table, anatomy/tones, tooltip,
  eligibility, surfaces/interaction, Tasks results, toggle/lifecycle,
  rejected alternatives, conformance vectors, live-verification list.
- Mirror in `bob-plugins`: pure core (`13x-*.js` style range/eligibility
  functions reusing `freshnessTaskStatus` and code-exclusion helpers)
  plus plugin mixin (`26x/27x-*.js` style setup/extension/post-processor/
  toggle), `fragments.json` order respected, `npm run build` +
  `npm run build:check`, shared CSS in `styles.css` on
  `body.bob-gtd-marks` / `body.bob-repeat-marks` (or one body class).
  No `api` namespace addition without a consumer (per the task-tag-marks
  precedent).
- Conformance vectors to pin: whole-token case-insensitive pairing
  (`#GTD #Pre` pairs; `#gtd/pre`, `#pressed_juice` do not); `#pre`
  wins over `#post` with lint; cursor-touch reveal boundaries;
  code-span exclusion; lone `#gtd` untouched; both bracket and paren
  repeat forms; tooltip contains no `::`; idempotent re-annotation;
  toggle off strips document-wide; disjointness from hash/date/priority
  ranges; Tasks-results CSS selectors (Tasks 8.4.0 `data-tag-name`).
- Live verification (Bryan in Obsidian): light + dark ink legibility,
  Blocked-tint (`[?]`) legibility for all three new glyphs, hover
  capsule on both hosts, cursor/click reveal, typing stays raw until
  the boundary, `j`/`k` no-jitter, reading view + embeds + hover
  previews, `dash.md` Tasks results, toggle round-trip, closed-row
  ghost, coexistence with priority/date/fresh marks on one line, iOS,
  PDF export.

## Open questions for Bryan

- Sunrise/sunset vs alternatives: does the pair read instantly, or
  would you prefer a more literal open-checklist / close-checklist
  metaphor (e.g. door-open / flag)? My vote is sunrise/sunset, but it
  is the one genuinely aesthetic call here.
- Is icon-only repeat acceptable for the weekly-prune and monthly rows,
  or do you want the deferred compact label from day one? My vote is
  icon-only first; the scheduled mark (`⧗ Mon`, `⧗ 1st`) already shows
  the next occurrence next to it.
- Violet for PRE/POST: keep the tag-family affordance, or go fully
  monochrome like the date marks? My vote is violet (it still reads as
  "these were tags"), but monochrome is the quieter option.

## Sources inspected

- `docs/task-tag-marks.md`, `docs/date-marks.md`,
  `docs/freshness.md` sections 3-4 and 10-13, `docs/develop/decisions.md`
  ("Review Walk Is Tiered"), `docs/concepts/freshness-and-the-review-walk.md`.
- Vault: `gtd_daily.md` (live checklist rows), `done/gtd_daily_done.md`
  (repeat distribution: 952x daily), `dash.md` (Tasks query surfaces),
  `.obsidian/plugins/obsidian-tasks-plugin/data.json` (Dataview format,
  `globalFilter #task`, `removeGlobalFilter false`).
- `bob-plugins` (`sase repo open bob-plugins`): `src/138-task-tag-marks.js`,
  `src/264-plugin-task-tag-marks.js`, `src/136-date-marks.js`,
  `src/266-plugin-date-marks.js`, `styles.css` patterns; Tasks
  `recurrenceSymbol 🔁` and Dataview `repeat::` serializer in the
  installed Tasks bundle.
- `bob-cli`: `src/native/dataview/tasks/task.rs` + `render.rs`
  (`repeat` → `🔁` column), `src/native/task_fields.rs`,
  freshness evaluators and CL-vector tests.
