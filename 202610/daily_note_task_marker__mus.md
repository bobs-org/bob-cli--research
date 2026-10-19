# Marking tasks that live in today's daily file — design research

Researcher: mus. Independent report for the 5-researcher swarm.
Scope: how to render a marker on tasks residing in today's daily file,
wherever those tasks are viewed in Obsidian. Intuitive, reliable, beautiful.

## TL;DR

Yes, build it — but build a **daily-note residence marker**, not a "today"
marker. Residence (the task line lives in today's `YYYY/YYYYMMDD.md`) and
Today (the task is linked under today's open Pomodoros) are different sets,
and the vault's architecture decisions keep them different on purpose. The
existing Task Link decorations (amber half-ring `◐` for In Progress targets,
faint `🔓` for unblocked-today links) already own the "today as work"
meaning. The new mark should own the quieter "this task lives in the daily
note" meaning, in neutral grey, display-only, with a session toggle, across
Live Preview, Reading view, and Tasks query results.

## 1. What "already similar" exists today

There are two ledger-link decorations in `bob-ledger-tools`, both
display-only and both gated on today's daily note. They are the pattern to
copy — and the namespace to avoid colliding with.

### 1.1 In Progress half-ring on Task Links (`docs/plan.md`, "In Progress marks and the Task Link lane toggle")

- Where: every Task Link under an **open** Pomodoro in **today's** daily note
  whose target task is `[/]`, rendered as an amber half-ring `◐` immediately
  before the link token — the same slot `🍅` takes under closed Pomodoros.
- Next (`[*]`) targets show nothing. Blocked, Ready, done, unresolved,
  struck, embedded, nested, fenced, off-Pomodoros, and yesterday's-note links
  show nothing ("truthful or neutral").
- Implementation: pure core `progressMarkMatchFromBody`,
  `progressMarkLinkFromBody`, `progressMarkLinks`, `buildProgressMarkElement`,
  `ProgressMarkWidget` in
  `plugins/bob-ledger-tools/src/137-progress-marks.js`; Live Preview
  extension plus Reading-view post-processor plus `api.progressMarks` v1
  (`expect`, `refresh`, `isEnabled`) in
  `plugins/bob-ledger-tools/src/268-plugin-progress-marks.js`.
- Key rejections worth reusing: the mark is **rendered, never written** —
  writing `◐` into the ledger would repeat the `#today`-tag mistake (churn,
  races, staleness) and break every dedicated-Task-Link parser, which accepts
  only `🍅` and `!` prefixes. Without the plugin the vault looks exactly as
  before.

### 1.2 Unblocked hand-off glyph (`plugins/bob-ledger-tools/src/139-unblocked-glyph.js`, `271-plugin-unblocked-glyph.js`)

- Where: live Task Links under today's open Pomodoros whose Tasks-cache task
  is open **and** had a prerequisite completed today — faint text glyph `🔓`
  after the link, tooltip naming the prerequisite
  (`unblockedGlyphTooltip`, `unblockedTodayLinks`,
  `buildUnblockedGlyphElement`, `UnblockedGlyphWidget`).
- Reuses `progressMarkLinks` for the live-link definition, so both marks
  share one meaning of "live Task Link". Derived from the Tasks cache on
  every build; never stored.

### 1.3 The wider mark family (contracts to mirror)

- `docs/date-marks.md`: four monochrome date marks (`+`, hourglass, check,
  circle-slash), store-absolute/show-relative, shape-carries-meaning,
  reversible, one shared CSS-mask glyph definition, tooltips never contain
  `::` (Dataview re-scans `innerHTML` for inline fields).
- `docs/task-tag-marks.md`: `#task` becomes a small teal `⌗` glyph; one
  constant identity ink that never encodes state; full hue-reservation table
  (red = Blocked, orange = attention/ROTTEN/Pending chip, yellow = In
  Progress, green = Next/fresh-today, blue = Ready lane, violet = tags/links,
  cyan = inline code, grey = priority/dates/cancelled, teal = tracked task).
- Freshness marks (`plugins/bob-ledger-tools/src/130-freshness-marks.js`,
  `styles.css` `.bob-fresh-mark`): quiet by default, louder only when it
  matters; closed tasks rest faint.

Takeaway: every accepted mark follows the same five principles —
**display-only, truthful-or-neutral, quiet-by-default, reversible, one shared
glyph definition**. The new mark must too, or it will feel foreign.

## 2. What "in today's daily file" can mean (disambiguation)

The request reads naturally two ways, and they need different marks:

| Reading | Set | Answers |
|---|---|---|
| A. Residence (recommended reading) | task lines whose file is today's canonical daily note (`YYYY/YYYYMMDD.md`) | "where does this task live?" |
| B. Linkage (Today set) | tasks with a dedicated Task Link under today's open Pomodoros, wherever they live | "what is on today's plate?" |

Evidence for A as the literal request: "tasks that are **in** today's daily
file" plus "when I view those tasks in Obsidian" (i.e. viewed elsewhere —
Tasks results, embeds, backlinks — the residence is not obvious there).

Evidence B matters anyway: if the requester actually wants "highlight my day's
lineup at the home note," that is a different, arguably more useful feature
("Today-at-home"), but it must not be built under the name "in the daily
file."

Why the distinction is load-bearing: `decisions:today-is-read-from-the-ledger`
explicitly rejected both a file-path filter ("it measures residence, not
work") and a hooks-managed `#today` tag (write churn, races, staleness) as
definitions of Today. Marking residence with Today language would reintroduce
exactly the confusion that decision removed. Daily-note tasks are also
explicitly **outside** freshness review scope (`docs/freshness.md`: canonical
daily-note tasks and Today-linked tasks are excluded from the walk;
`walk_scope(t)` requires `¬in a canonical daily note ∧ ¬Today(t)`), outside
the per-note Ready list (plan vector R7), and the canonical `^gtd` row is
excluded from stats. Residence is journal metadata, not work state — the mark
must say so visually.

Practical note on volume: the tasks that live in a daily note on any given day
are few — `^gtd` / `#gtd #pre` / `#post` checklist rows, plus ad-hoc captured
journal tasks. The marker will be rare by construction, which is good: a rare
mark can stay quiet without becoming noise.

## 3. Critique: is this a good idea?

**Yes, with the scope narrowed.** Spotting daily-resident tasks in foreign
surfaces (a `dash` Tasks query, `blocked.md`, search, an embed) answers a real
question — "why is this task exempt from review / where do I edit it?" — that
today requires opening the task or reading a path column. Cost is low because
residence needs no Tasks-cache join (see §5).

Risks, honestly stated:

1. **Glyph overload.** A task line already stacks checkbox tint, `⌗`,
   priority/date/freshness marks, dependency chips, and (on links) `◐`/`🔓`.
   A loud new glyph would tip busy lines into confetti. Mitigation: grey,
   0.8em, one fixed slot (§6).
2. **Today confusion.** Anything amber/green, anything labeled "today" as a
   work state, and anything shaped like `◐`/`🔓` will read as lane or ledger
   state. Mitigation: neutral ink, calendar/journal shape, "daily note"
   wording (§6).
3. **Hue exhaustion.** Per the `task-tag-marks.md` inventory, every
   saturated hue already means something. There is no free accent color.
   Mitigation: do not take one — use `var(--text-muted)` grey, the only
   unclaimed ink, same family as priority/date marks.
4. **Midnight and custom daily-note setups.** Hardcoding `YYYY/YYYYMMDD.md`
   breaks custom Daily Notes folder/format and flips wrong at midnight.
   Mitigation: reuse `todayDailyPath` + `getDailyNotesOptions` +
   `isTodayDailyFile` from
   `plugins/bob-ledger-tools/src/020-time-and-pomodoro.js` /
   `040-editor-and-daily.js`, never a regex alone (`PLAN_DAILY_PATH_RE` in
   `050-plan-budget.js` is a shape test, not a today test).
5. **Embed ambiguity.** In Reading view `ctx.sourcePath` is the host note, not
   the embedded note's path; a daily task embedded in a project note would
   mis-mark if gated on host path only. Mitigation: v1 marks native lines by
   host path and Tasks results by `task.path`; embeds explicitly out of scope
   until the embed-source resolution is specified and tested.

What I would **not** do instead: a written tag/field (`#today`, `#daily`,
`[today::]`, emoji prefix) — rejected for the same reasons as the written-`◐`
alternative (parser breakage, reconcile churn, Dataview rescan hazards); a
per-task colored background tint (fights the Blocked-red / Next-green / In
Progress-yellow line tints); or a Bases/Dataview-column-only solution (helps
dash but not the daily note itself or Live Preview editing, where the
question also arises).

## 4. Requirement adjustments (explicit)

1. **Rename the feature** from "today marker" to **daily-note residence
   mark**. Tooltip, command, CSS class, and docs all say "daily note," never
   bare "today" as a work claim. Proposed tooltip line 1:
   `In today's daily note`, line 2 (Reading/native only):
   the vault-relative daily path. No `::` anywhere in the tooltip.
2. **Gate on today's computed daily path only**, honoring the Daily Notes
   plugin's folder/format via the existing helpers — not "any daily-shaped
   file," not "any file under `YYYY/`." Yesterday's and tomorrow's daily
   tasks get no mark; history stays clean.
3. **Display-only, plus a session toggle** (`Toggle daily-note task marks`,
   default on, `body` class gate like `bob-progress-marks` /
   `bob-unblocked-glyphs`). No writer, no command that stamps residence, no
   `api` write surface.
4. **Three hosts in v1, embeds deferred**: Live Preview task lines, Reading
   view task lines, Tasks query results. Embeds, Bases cells, Canvas, and
   search-result snippets are named non-goals until v2 vectors exist.
5. **Open and closed tasks share one glyph; closed rests faint**, following
   the date-mark `resting` tone (`li.task-list-item[data-task=x]` pattern in
   `styles.css`). Do not hide the mark on done tasks — provenance ("I did
   this in today's note") is part of the point — but drop it to ~55%
   opacity.

## 5. Reliability design

- **Model is a path equality, not a cache join.** For native lines the host
  file is known (`view.file.path` / `ctx.sourcePath` → `isTodayDailyFile`).
  For Tasks results the `Task.path` is known — compare normalized
  (`sameVaultPath`) against `todayDailyPath(new Date(), getDailyNotesOptions(app))`.
  No `getTasks()` dependency means no cold-cache gaps, no 4-second optimistic
  hints, and no resolver divergence — strictly more reliable than `◐`/`🔓`.
- **Rollover.** Recompute the expected path on each decoration build from
  `new Date()` (local), and subscribe to the same refresh triggers the
  progress/unblocked mixins use (doc change, viewport change, metadata-cache
  resolve, plus a day-boundary timer if the plugin already runs one for
  freshness; otherwise a lightweight midnight `setTimeout` re-render).
  Conformance vector: open today's note at 23:59, wait past midnight, marks
  vanish without reload.
- **Never throw, never blank the line.** Every helper synchronous and total
  (bad input → no mark), mirroring the `try/catch → null/[]` discipline in
  `137-progress-marks.js` / `139-unblocked-glyph.js`. A failing mark path
  must leave the task line untouched.
- **Conformance vectors first**, in the style of `docs/plan.md` P1–P14:
  today's-note open task (mark), yesterday's note (none), future daily file
  (none), non-canonical note (none), custom Daily Notes folder/format
  (mark), fenced code block resembling a task (none), Tasks result hosted in
  today's note (mark), same result with plugin toggle off (none), midnight
  rollover (mark clears), closed daily task (faint mark), `^gtd` row (mark —
  it is still a daily resident; stats exclusion is orthogonal).

## 6. Beauty design (the part that has to earn its pixels)

- **Shape carries meaning; color whispers.** Proposed glyph: a minimal
  journal/calendar-page outline with a single header rule — the date-mark
  family's monochrome language, not a second `◐` and not a third emoji
  (emoji `🔓` was a deliberate one-off for the hand-off; repeating emoji here
  would cheapen both). Drawn as a CSS mask from one `viewBox 0 0 16 16`
  stroked path (`stroke-width ~1.7`, round caps), shared by all three hosts —
  the same "one glyph definition" rule as date/tag marks.
- **Ink: `var(--text-muted)` grey.** The only hue that promises nothing in
  this vault. It reads on red Blocked, yellow In Progress, green Next, and
  blue Ready tints without fighting any of them, and it degrades gracefully
  to "quiet metadata" on crowded lines. No theme hook in v1 beyond the
  standard `--bob-daily-mark-color` override hook left unset by default
  (mirrors `--bob-progress-mark-color`).
- **Size and slot.** `0.8em` interface-font inline box (the
  `.bob-date-mark`/`.bob-fresh-mark` metrics), `vertical-align` tuned so line
  height never shifts. Slot: immediately **after the checkbox, before the
  task text** for native lines (a fixed pre-text adornment zone shared with
  `⌗`, ordered `⌗ → daily-mark → text → date/freshness marks`, so existing
  marks never reflow when the new one appears); for Tasks results, prepended
  to the description cell with the same ordering. Entrance: none (it is
  static metadata, not an event — unlike `◐`'s 160 ms entrance). Hover: full
  opacity with a 12% tint capsule; `prefers-reduced-motion` respected
  trivially since there is no animation.
- **Cursor and click pass through** to the underlying task text (the
  mousedown-to-place-cursor listener pattern from `ProgressMarkWidget` /
  `UnblockedGlyphWidget`, minus any link-opening behavior). Source mode shows
  raw text; toggle restores instantly; without the plugin nothing changes.
- **Live verification checklist** (for the implementing turn, in Obsidian):
  light + dark legibility on all four lane tints; mark survives cursor-on-line
  (it covers no source text, so no rebuild on `selectionSet`); Reading view
  matches Live Preview; Tasks `dash` result shows the same grey mark;
  yesterday's note shows none; toggle flips instantly; screen reader gets the
  `role="img"` + `aria-label`, never the raw path alone.

## 7. Options considered

| Option | Verdict |
|---|---|
| Grey calendar-outline residence mark (this report) | Recommended — quiet, truthful, cheap, no hue collision |
| Amber/green "TODAY" pill on daily-resident tasks | Rejected — collides with ledger Today and lane colors; reintroduces the path-filter Today the decisions retired |
| Written `#today` / `[today::]` / emoji prefix | Rejected — parser breakage, reconcile churn, Dataview rescan risk; same rejection as written-`◐` |
| Today-at-home mark (mark home tasks linked today) | Valuable but separate feature — needs Tasks-cache join, optimistic hints, and its own vectors; propose as fast-follow, not v1 |
| Line-tint or background wash for daily tasks | Rejected — fights the four lane tints; fails non-text contrast discipline |
| Dataview/Bases column only | Rejected as sole surface — misses the editing surfaces where the question arises |

## 8. Recommended solution

Build **v1: a quiet grey daily-note residence mark** in `bob-ledger-tools`,
owned by a short design doc modeled on `docs/date-marks.md` /
`docs/task-tag-marks.md` (display contract + conformance vectors + live
verification list), implemented as one pure core fragment (path gate +
listener-free DOM builder + Live Preview widget) plus one plugin mixin
(Live Preview extension, Reading post-processor, Tasks-results pass,
session toggle, `body.bob-daily-marks` gate), with the exact reliability
rules in §5 and the exact visual spec in §6.

Explicitly defer: embeds and Bases cells (unresolved source-path semantics),
any "Today-at-home" linkage mark (real need, separate vectors and cache
dependency — file as the follow-up), and any written form of residence.

Source anchors inspected for this report: `docs/plan.md` (In Progress marks,
Today conformance, READY backlog), `docs/date-marks.md`,
`docs/task-tag-marks.md`, `docs/freshness.md` §§4–5/10b (daily-note and
Today exclusions, `[unblocked::]` WRITE rule), `docs/task-status-hooks.md`
(ledger definition), `docs/task-dependencies.md` §§7/12–13 (chips, Task Link
model, consumption), `plugins/bob-ledger-tools/src/137-progress-marks.js`,
`139-unblocked-glyph.js`, `268-plugin-progress-marks.js`,
`271-plugin-unblocked-glyph.js`, `060-today.js`, `050-plan-budget.js`,
`020-time-and-pomodoro.js` (`todayDailyPath`, `isTodayDailyFile`),
`040-editor-and-daily.js`, `styles.css` mark sections; memory
`decisions:today-is-read-from-the-ledger`,
`decisions:task-lanes-are-sticky`,
`decisions:unblocked-tasks-resurface-as-ticklers`,
`glossary:task-link`, `glossary:pomodoro`, `glossary:capture`,
`glossary:task-freshness`.
