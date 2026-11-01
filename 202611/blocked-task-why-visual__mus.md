# Why a task is Blocked, at a glance — visual design research (`__mus`)

**Swarm:** 5-researcher round (`mus` report; peers write `__cdx` / `__cld` / `__grk` / `__gem` independently).
**Question:** make it visually obvious *why* a task is Blocked in Obsidian — critique the
`[1]`/`[2]`/`[3]`/`[4]`-for-priority + `[&]`-for-deps + `[?]`-only-for-scheduled sketch,
adjust requirements where justified, and recommend a solution that is intuitive, reliable, and beautiful.
**Verdict up front:** the goal is right and worth building, but the sketch as stated conflates two
orthogonal dimensions (lane/cause vs. priority) into one checkbox channel, leaves project-blocking
unaddressed, and collides with the reserved palette. Keep storage unchanged; render **cause in the
checkbox** (`[?]` scheduled, `[&]` depends-on, `[^]` project, display-only) and keep **priority in the
suffix signal bars** (monochrome, no new hues). Details and spec sketch below.

## 1. Current state (what the vault actually does today)

### 1.1 The checkbox is the lane; Blocked is derived, never authored

From [docs/concepts/tasks-and-lanes.md](/home/bryan/.local/state/sase/workspaces/bobs-org/bob-cli/bob-cli_15/docs/concepts/tasks-and-lanes.md),
[docs/reference/vault-format.md](/home/bryan/.local/state/sase/workspaces/bobs-org/bob-cli/bob-cli_15/docs/reference/vault-format.md),
and [docs/task-status-hooks.md](/home/bryan/.local/state/sase/workspaces/bobs-org/bob-cli/bob-cli_15/docs/task-status-hooks.md):

| Checkbox | Lane | Tasks type | Who writes it |
|---|---|---|---|
| `[ ]` | Ready | `TODO` | default; Alt+N release returns here |
| `[*]` | Next (sticky commitment) | `ON_HOLD` | link under today's open Pomodoros |
| `[/]` | Pending / In Progress (sticky) | `IN_PROGRESS` | `=x` close outcome, Alt+[/Alt+] |
| `[?]` | Blocked (derived) | `ON_HOLD` | reconcile from causes; hand-set `[?]` without a cause is repaired |
| `[x]`/`[X]` | Done | `DONE` | completion gestures |
| `[-]` | Cancelled | `CANCELLED` | cancel gesture |

Note that Next and Blocked share Tasks type `ON_HOLD` — only the symbol distinguishes them.
The installed Tasks registry must contain exactly one compatible `?` status
(`nextStatusSymbol: " "`, `type: ON_HOLD`); a missing/duplicated/incompatible definition
makes reconcile refuse before any write.

### 1.2 `[?]` conflates three causes (plus combinations)

Per [docs/task-status-hooks.md](/home/bryan/.local/state/sase/workspaces/bobs-org/bob-cli/bob-cli_15/docs/task-status-hooks.md) ("Blocked is derived state")
and [docs/task-dependencies.md](/home/bryan/.local/state/sase/workspaces/bobs-org/bob-cli/bob-cli_15/docs/task-dependencies.md) §5:

1. **Open dependencies** — any open prerequisite on the managed `⛓️ DEPENDS ON:` first-child line
   (AND, finish-to-start; Done/Cancelled stop blocking; unresolved/broken/non-task/self links never block;
   cycles keep every member Blocked with a warning).
2. **Future schedule** — a valid `[scheduled:: YYYY-MM-DD]` strictly after the effective daily anchor
   (`BOB_DAY_FILE` date, else local date / `BOB_NOW`). Today and past dates do not block.
3. **Project inheritance** — while the note's `^prj` task is Blocked for its own dep/schedule reasons,
   every open resident is Blocked with a `project_dependency` / `project_schedule` reason and one
   machine-owned `#prj_is_blocked` tag (recursive through `parent:` ancestors; a hand-set `[?]` on
   `^prj` alone blocks nobody).

Any combination can hold simultaneously. Recovery recomputes the lane from current inputs
(Ready unless linked-today/recent-activity justifies Next/Pending); there is no stored
"previous status". Every automatic Blocked→Ready recovery writes `[unblocked:: today]` unless a
freshness WRITE skip applies (out of scope, unstamped, scheduled-tickler, landing Next/Pending).

Scale: [docs/task-tag-marks.md](/home/bryan/.local/state/sase/workspaces/bobs-org/bob-cli/bob-cli_15/docs/task-tag-marks.md) counted
(2026-10-08) ~3,406 `#task` lines, ~470 open — **383 `[?]`**, 19 `[*]`, 7 `[/]`, 63 `[ ]`.
So the ambiguous symbol dominates the open vault. The complaint is real: at scan distance every
open task looks the same red `[?]`.

### 1.3 The why is already stored — just not glanceable

- **Deps:** the `⛓️ DEPENDS ON:` line is the source of truth; `[dependsOn::]`/`[id::]` are derived
  projections; each open prerequisite carries a generated `🧱 BLOCKS:` mirror (never read back).
  bob-ledger-tools renders miniature status-colored chips plus a `waiting on N` / `✓ all clear`
  summary (never written to Markdown). Counts count open prerequisites only.
- **Schedule:** `[scheduled::]` renders as the date mark `⧗ Fri` / `⧗ today` (monochrome hourglass +
  relative label; scheduled-today is the only emphasized state). Tooltip gives the exact date,
  distance, and `Ctrl+Shift+P to reschedule`.
- **Project:** `#prj_is_blocked` tag + `^prj`'s own dep/schedule state + propagated `scheduled` fields.
- **Priority:** `[priority:: high|medium|low|lowest]` (+ off-ladder `highest`) renders as the
  **signal-staircase mark** — 4/3/2/1 filled bars for P1–P4, knocked-out `!` for `highest`, nothing
  for P0 (no field). Monochrome by design (`--text-muted` fill, 26% track, `--text-normal` urgent,
  faint resting on closed tasks). Tooltip names the P-label *only when the ladder config is known*,
  else the bare value. The Task Card level strip and notices reuse it via `api.priorityMarks` v1.

So the data model is sound; the gap is purely **scan-distance disambiguation of `[?]`**.

### 1.4 The display language already reserves every hue

[docs/task-tag-marks.md](/home/bryan/.local/state/sase/workspaces/bobs-org/bob-cli/bob-cli_15/docs/task-tag-marks.md) ("Ink") fixes the palette so each
channel has one meaning:

| Hue | Already means |
|---|---|
| red | Blocked (line tint, blocked chips) |
| orange | attention: due freshness, ROTTEN, repair flags, Pending chip |
| yellow | In Progress (line tint, half-ring progress mark) |
| green | Next (line tint), fresh `✓ today` |
| blue | Ready lane |
| violet accent | tags (`#prj`, `#gtd`) and links |
| cyan/teal | inline code chips; teal identity hash = "tracked task, nothing else" |
| grey | priority and date marks, cancelled |

And the family principles, repeated across the date-, priority-, tag-, link-, and today-marks
contracts: **display-only** (stored Markdown never changes); **shape carries meaning, color whispers**;
**truthful or neutral** (stale/unknown renders nothing, never a confident wrong mark);
**reversible** (cursor/click reveals raw text, source mode raw, session toggle, bare vault unchanged);
**one glyph definition** (CSS masks shared by every surface); **color is never the only signal**.

Any proposal adding four new priority hues must survive this table. There is no free hue.

### 1.5 Priority and schedule are coupled in storage

Per [docs/projects.md](/home/bryan/.local/state/sase/workspaces/bobs-org/bob-cli/bob-cli_15/docs/projects.md) ("Priority property and scheduled rolls"):
the picker shows P-levels but stores Tasks-native values (`P1→high`, `P2→medium`, `P3→low`,
`P4→lowest` — because a literal `[priority:: P2]` would hide earlier scheduled/id/dependsOn fields
from right-to-left Tasks parsing). Choosing P1–P4 **also rolls a `scheduled` date** in that level's
window (default 2–7 / 8–30 / 31–90 / 91–365 days; windows are **configurable** in
`~/.config/bob/config.yml`, parsed by `parse_priority_property` in
`src/native/config/mod.rs`). No field = implicit **P0** ("do it now", highest urgency, no rolled
date). `highest` is off-ladder (urgent `!`). Clearing priority keeps the rolled date (explicit
commitment once written). Capture `$<N>` writes the same field+roll+schedule-log entry.

Consequence: **most scheduled-blocked tasks also have a priority**, and most P1–P4 tasks are
scheduled-blocked at birth. Any design assigning the checkbox to *both* priority and cause needs a
precedence rule — the sketch has none (see §2.4).

## 2. Critique of the sketch, bullet by bullet

### 2.1 "`[1]`, `[2]`, `[3]`, `[4]` in distinct colors for `priority`" — reject as stated

Three independent objections, any one of which is enough:

1. **It destroys the lane signal.** The checkbox interior currently encodes the lane — the single
   most important fact about a task (is it committed? started? blocked?). Repurposing it for
   priority means a Next+P2 task shows `[2]` instead of `[*]`: at a glance you can no longer tell
   committed work from backlog. The line tint (red/yellow/green/blue) is too subtle to carry the
   lane alone, and P0 tasks (no field — the *most* urgent!) would show a bare `[ ]`, i.e. the
   highest-priority work gets the plainest box. That is backwards.
2. **There is no free hue, and the ladder is configurable.** Four distinct, light/dark-legible,
   color-blind-safe hues that avoid red/orange/yellow/green/blue/violet/cyan/grey do not exist in
   this palette — and the P-labels themselves are config-defined (`label: P1 … value: high …`
   in `src/native/config/mod.rs`; Bryan can rename levels or change windows). Hard-coding
   `[1]`–`[4]` bakes today's default ladder into the checkbox; the current signal bars deliberately
   key off the **stored Tasks value** so they stay robust without config, with P-labels only as a
   tooltip refinement when the ladder is known. The sketch also has no answer for `highest`
   (off-ladder urgent) or P0 (absent field).
3. **It duplicates information in the wrong channel.** Priority already has a compact, learned,
   well-placed home: the suffix signal bars (same silhouette as the nav priority notice's Lucide
   `signal-*` icons; reused on the Task Card strip via `api.priorityMarks`). Priority belongs with
   the other suffix facts (freshness, dates); the checkbox belongs to lane+cause. Orthogonal
   dimensions deserve orthogonal channels. Doubling priority into the checkbox adds noise on every
   line (430+ prioritized lines per the priority-marks rejected-alternatives note) for zero new
   information, while *removing* the lane fact the checkbox exists to convey.

A narrower version of the instinct is salvageable (see §4): keep the bars, optionally give them a
*single-family* emphasis ramp (P1 slightly stronger, P4 quieter — weight/opacity, not four hues),
and put the P-label where it is already learned (tooltip + Task Card). Do not mint four hues.

### 2.2 "Stop rendering the priority icon?" — no, keep it

The signal bars should stay, for the reasons in §2.1 plus: they work on non-Blocked tasks
(Ready/Next/Pending — exactly where priority guides *choice* of work); they handle `highest` and
P0 correctly (urgent `!`; P0 silence is honest: absence of deferral); they are monochrome-grey so
they never fight the lane tint; they degrade gracefully when the ladder is unknown (mobile, missing
config); and they are already API-reused (`api.priorityMarks` v1 `model`/`render`, `decorative` and
`inheritColor` options). Removing them to "pay for" checkbox numbers trades a correct, learned,
low-noise mark for a noisier, lossier one. The priority-marks contract explicitly rejected "P-label
beside the glyph doubles the width on every line" and "marks on P0 tasks would glyph nearly every
line" — both objections apply with more force to checkbox numbers.

### 2.3 "`[&]` for depends-on-blocked" — accept the glyph, reject stored-status mechanics

The glyph choice itself is good and I recommend keeping it: `&` is the capture sigil for
prerequisites (`&note:block-id` adds a prerequisite; see [docs/capture.md](/home/bryan/.local/state/sase/workspaces/bobs-org/bob-cli/bob-cli_15/docs/capture.md)),
so `[&]` is mnemonic ("this waits on & links"), single-character, typeable, visually distinct from
`?`, and — unlike `[1]`–`[4]` — it does not collide with any existing lane symbol. It also extends
naturally to the missing third cause: `[^]` for project-inherited blocking (matches `^prj` and
`^block-id`; points "up" at the parent project).

But it must be **display-only**, never a stored checkbox change. Minting `[&]` (and `[1]`–`[4]`,
`[^]`) as real Tasks statuses would require: N new registry entries in
`.obsidian/plugins/obsidian-tasks-plugin/data.json` (each with `nextStatusSymbol` + `type`);
updates to every status-symbol switch in Rust (`lane(t)` in freshness evaluation, reconcile's
transition-precedence table, `stamp_fresh` refusals, archive/complete classification via
`statusSettings.customStatuses`, guard rails, `bob task reroll` grouping); the JS mirrors
(`freshnessTaskStatus`, `checklistKindForText`, stage pools/rankers, Task Card writers); the
vault-format, hooks, and capture contracts plus their vector tables; and a vault-wide migration of
hundreds of `[?]` lines with no undo except `git revert`. And for what? The cause is already
derived at read time — storing it just creates a second source of truth that rots (exactly why
Blocked is derived today). Display-only checkbox *appearance* overrides get 100% of the glance
value at ~1% of the risk, and stay reversible/toggleable like every other mark family.

HTML-escaping note for implementers: `&` inside a rendered checkbox glyph is fine as a CSS/text
glyph, but any `aria-label`/tooltip builder must escape it (`&amp;`) — trivial, just don't forget.

### 2.4 "`[?]` only for scheduled" — incomplete: project-blocking is the unaddressed third

Reserving `[?]` for future-scheduled blocking is the right *direction* (minimal migration, matches
the "waiting on time = ?" mental model), but as stated it strands project-inherited blocking —
arguably the most confusing cause today, because the reason lives on a *different line* (`^prj`,
possibly in an ancestor note) and the resident's own row shows no local evidence except the
`#prj_is_blocked` tag. Options are (a) lump project-blocked under `[?]` (keeps today's ambiguity for
whole notes at a time), or (b) give it its own face (`[^]`). I recommend (b): three causes, three
faces, one precedence rule for combinations (§4.2). Combined-cause tasks (dep+scheduled is common;
dep+project and triple combinations occur) show the highest-precedence face while the tooltip and
the existing chips/date-marks enumerate *all* reasons — the checkbox answers "what kind of stuck at
a glance", the row answers "exactly what".

Also note the precedence gap flagged in §1.5: a task that is both P2 and scheduled-blocked matches
both the `[2]` rule and the `[?]` rule. The sketch picks no winner. In the recommended design the
conflict cannot arise (checkbox never shows priority), which is another reason to keep the channels
separate.

### 2.5 General: is this a good idea? Yes — with the channels fixed

The goal is sound: 383 identically-dressed `[?]` rows *are* the open vault, and the three causes
demand different actions (close/chase a prerequisite vs. wait for a date vs. fix the project).
Making the checkbox name the cause shortens every scan and teaches the dependency model for free.
The risks are all in *how*: new stored statuses (high migration + rot risk), four new hues (palette
collision + accessibility failure — color can never be the only signal), lane erasure (checkbox =
priority loses Next/Pending), configurable-ladder bake-in, and the missing project/combined-cause
spec. All are avoidable with a display-only, shape-first design that reuses reconcile's derivation
instead of duplicating it. Beauty falls out of restraint: three quiet checkbox faces in the existing
lane inks, priority whispering in the suffix, no new colors.

## 3. Required adjustments to the sketch (what I would change and why)

| # | Sketch says | Adjustment | Why |
|---|---|---|---|
| A1 | `[1]`-`[4]` in the checkbox for prioritized tasks | Drop. Checkbox never shows priority; priority stays in the suffix signal bars | Preserves the lane (Next/Pending/Blocked); P0/`highest` have no sane number; avoids baking the configurable ladder into chrome |
| A2 | Distinct color per priority | Drop (or reduce to a monochrome emphasis ramp). No new hues | Every hue is taken; 4 hues fail contrast, color-blindness, and color-never-the-only-signal; shape already carries the level |
| A3 | Stop rendering the priority icon | Keep the signal bars | Learned, compact, config-robust, API-reused, and the only at-a-glance priority on non-Blocked lanes where choice happens |
| A4 | `[&]` for dep-blocked | Accept, as display-only appearance (storage stays `[?]`) | Mnemonic matches capture `&`; distinct, typeable, no lane collision |
| A5 | `[?]` only for scheduled | Accept, plus add `[^]` for project-inherited blocking (display-only) | Otherwise the most confusing cause (reason on another line or note) stays ambiguous; `^` matches `^prj` and `^block-id` |
| A6 | (unstated) combined causes | Add precedence `&` over `^` over `?`; checkbox shows one face, tooltip and chips list all | Dep-plus-scheduled is the common case since priority rolls write both; actionable beats structural beats temporal |
| A7 | (unstated) storage | No stored change. `[?]`, `[priority::]`, `[scheduled::]`, Depends-On line, `#prj_is_blocked` unchanged; reconcile stays the sole writer | A stored cause is a second source of truth that rots; display-only is reversible, toggleable, migrates zero lines |

## 4. Recommended solution (display-only cause faces plus untouched priority channel)

### 4.1 Principles (inherit the family contract)

Display-only; shape carries meaning and color only whispers; truthful-or-neutral under stale cache;
reversible (session toggle, source mode raw, click and cursor reveal `[?]`); one glyph definition
shared by Live Preview, reading view, embeds, hover previews, Dataview `TASK` views, and Tasks query
results; color never the only signal (every face differs in glyph, with an `aria-label` plus tooltip
naming the cause in words); no new palette entries — Blocked faces reuse the existing red Blocked ink
and the existing grey suffix inks.

### 4.2 The three faces and the precedence rule

Storage on every concerned line remains `- [?]`. What the eye sees depends on the reconciled cause
set for that task today (same derivation as `bob task reconcile`: open dep, future-valid
`scheduled`, or project inheritance, evaluated against the effective daily anchor):

- Scheduled-only goes `[?]`, unchanged. The adjacent `⧗ Fri` or `⧗ today` date mark already says
  when; the tooltip reads `Blocked - scheduled Fri, Oct 9 - in 2 days` plus the reschedule hint.
- Has open deps, with or without other causes, goes `[&]`. Tooltip: `Blocked - waits on N` naming
  the first prerequisite plus the total, with scheduled and project follow-ups when present. The
  existing depends-on chips remain the detail row.
- Project-inherited only, with no own open dep and no own future schedule, goes `[^]`. Tooltip:
  `Blocked - project <name> waits on ...` naming the ancestor `^prj` reason. The
  `#prj_is_blocked` tag and the `^prj` row stay as corroboration.

Precedence is `&` over `^` over `?` because actionability scans best: something I can unblock by
closing a task, then something requiring a project fix, then something that just needs time. The
checkbox is the summary; the row (chips plus date mark plus tag) is the full enumeration. Never rely
on the face alone for the complete reason set. Flag: if whole-note outages feel dominant, `^` over
`&` is a one-line swap; the vectors below pin whichever is chosen.

If any priority emphasis is still wanted after living with cause faces, do it inside the existing
bars (for example P1 fill at full `--text-muted`, P4 at 70 percent — one family, shape primary)
behind the same session toggle, never as checkbox numbers or hues.

### 4.3 Tones, ink, and why it stays beautiful

Faces render in the existing Blocked red (line tint plus checkbox ink), exactly as `[?]` does
today — no new color to learn, legible on both themes because it already is. The `&`, `^`, `?`
interiors are drawn as text glyphs in the same checkbox box metrics Tasks already uses, so the
rhythm of the task list does not shift (no line-height change, same as the chips contract).
Closed tasks rest faint per the existing resting rule; the cause face never appears on closed,
non-task, or unknown-status rows. Priority bars and date marks keep their current monochrome grey;
scheduled-today keeps its sole emphasis state. At a glance a blocked row now reads as red
cause-face plus grey facts: two channels that never compete. Reduced motion, print
(`print-color-adjust: exact`), and mobile follow the existing marks handling; short-mode Tasks
results get glyph-only faces via the same CSS-only technique the priority and date marks use (no JS
DOM mutation where CSS suffices).

### 4.4 Eligibility and truthfulness (reuse, do not re-derive)

Eligible rows: open `#task` task lines with reconciled cause set non-empty, outside code, fences,
comments, and frontmatter, exactly like the date and priority marks code-exclusion rules. Non-task
lines, plain checklists, embeds, and managed edge rows (Depends-On, BLOCKS, LINKS, Schedule-Log
children) never get faces. Cause inputs must be the same resolvers reconcile uses: Tasks-cache plus
open-buffer override for unsaved edits; valid-date shape plus strictly-future boundary; resolved-task
(not non-task, missing, or archived-closed) open prerequisites; recursive `^prj` inheritance with
`#prj_is_blocked` as corroboration, never as input; malformed, unresolved, and broken links
contribute nothing (the warning chips stay the signal for those). Midnight rollover relabels faces
like date marks do today. Stale or unknown state renders the stored `[?]` with no face rather than
a guessed one: missing Tasks cache, unreadable config (ladder unknown affects only the P-label words
in tooltips, never the face), ambiguous basenames, duplicate block ids, and mid-edit transients.
This neutral-on-stale rule is the main reliability guarantee.

### 4.5 Surfaces, interaction, accessibility

Live Preview uses a `Prec.highest` decoration swapping only the checkbox interior glyph
(selection or cursor reveals raw `[?]`; mousedown places the cursor, never writes) — the same
pattern as priority and date marks. Rendered views (reading, embeds, hover, canvas, Dataview
`TASK`) post-process the checkbox span in place (sort order 50, idempotent, `innerHTML`-safe);
Tasks query results go through CSS on the row's existing `data-task` plus a cause attribute set by
the same bounded frame pass date marks use (no global MutationObserver; degrade to native `[?]`
when the pass exhausts). Each face carries `role="img"`, a words-first `aria-label`
(`Blocked, waiting on 2 tasks`; `Blocked by project Seedlings, scheduled ...`;
`Blocked until Fri, Oct 9`), tooltip lines joined with newline containing no `::` (Dataview
re-scans `innerHTML`), and visible-focus plus keyboard parity with the existing marks.
Screen-reader and grayscale users get the identical reason the sighted user gets — color is
redundant by construction. Clicking a face never acts (display surfaces never act): it reveals
`[?]` for editing or follows the existing chip and Task-Card affordances (`+` opens the Depends-on
stage, `x` removes a prerequisite, `Ctrl+Shift+P` reschedules). No new click behavior to learn.
One session toggle (on by default) flips one body class, refreshes editors, and re-triggers the
Tasks re-render event — instant off restores today's `[?]` everywhere, mirroring the existing
priority, date, and tag toggles.

### 4.6 Conformance sketch (vectors the implementation should pin)

Cause model per task: causes in `{dep(n, first), project(name, reason), scheduled(date)}`
evaluated at the daily anchor; face is `[&]` for dep, else `[^]` for project, else `[?]`.

| # | Stored row (anchor 2026-10-07) | Face | Notes |
|---|---|---|---|
| CB1 | `- [?] #task A ^a` plus open depends-on link | `[&]` | tooltip `Blocked - waits on 1` plus target name |
| CB2 | `- [?] #task B [scheduled:: 2026-10-09]` | `[?]` | adjacent `Fri` mark; tooltip with exact date, distance, reschedule hint |
| CB3 | resident of project whose `^prj` waits on open dep; own row clean | `[^]` | tooltip names ancestor project plus its reason |
| CB4 | open dep plus future scheduled | `[&]` | precedence; tooltip lists both; chips plus date mark corroborate |
| CB5 | project reason plus future own scheduled, no own dep | `[^]` | precedence; tooltip lists both |
| CB6 | dep on Done or archived target only | face follows derived state, never the raw link | closed prerequisites do not block |
| CB7 | broken or unresolved dep link only | no face change plus warning chip | broken links never block per R4 and R5 |
| CB8 | hand-set `[?]` with no cause | no face (and reconcile repairs the `[?]`) | faces follow causes, not the symbol |
| CB9 | closed task or plain checklist with dep-looking children | no face | closed and non-task rows never faced |
| CB10 | P2 plus scheduled future | `[?]` plus 3-bar suffix mark | priority-or-cause conflict resolved by channel split |
| CB11 | Next plus P1 (`[*]` plus `[priority:: high]`) | `[*]` unchanged plus 4-bar mark | lane preserved; priority never touches the box |
| CB12 | P0 dep-blocked (no priority field plus open dep) | `[&]`, no bars | the urgent-but-stuck case the `[1]`-`[4]` sketch renders worst |
| CB13 | `highest` plus scheduled future | `[?]` plus urgent `!` mark | off-ladder handled |
| CB14 | stale cache, duplicate id, ambiguous basename | stored `[?]` unadorned | neutral under uncertainty |
| CB15 | rollover at midnight (scheduled date becomes today) | face clears with the recovery | relabel in place like date marks |

### 4.7 Rollout and live verification

Phase 1: Live Preview plus reading-view faces with toggle, tooltips, and CB1–CB15 vectors in
bob-ledger-tools tests (mirroring the priority and date-marks vector style). Phase 2: Tasks-results
CSS plus bounded frame pass, Dataview `TASK` views, embeds and hover. Phase 3 (optional, only if
cause faces prove insufficient in practice): single-family priority emphasis ramp inside the bars.
Live checks (Bryan in Obsidian): faces legible in light and dark; cursor and click reveal `[?]`;
toggle restores `[?]`; closed rows rest; faces plus bars plus hourglass sit cleanly on one line;
midnight rollover without reload; mobile renders; screen reader announces causes; grayscale still
disambiguates; `dash.md` and `blocked.md` results match editor faces; no new hue visible anywhere.

## 5. Risks, open questions, and sources

Risks: (1) cause computation duplicating reconcile logic and drifting — mitigate by citing the
hooks and dependency contracts vectors verbatim and testing against the same fixtures; (2) Tasks
re-render fragility — mitigate with the CSS-first plus bounded-frame pattern date marks already
use; (3) over-eager faces on ambiguous rows — mitigate with the neutral-on-stale rule.
Open questions for Bryan: (a) precedence `&` over `^` over `?` versus `^` over `&` when both
hold — recommended the former but it is one line to swap; (b) whether any priority emphasis ramp
is wanted at all after cause faces land — default no; (c) face for triple-cause rows —
recommended still one face plus full tooltip, no combined glyph.
Sources inspected (all in this checkout): `docs/task-status-hooks.md` (derived Blocked, anchor,
transition table, `?` registry contract), `docs/task-dependencies.md` sections 1–7 and 13–15
(Depends-On source of truth, semantics, chips, project inheritance, BLOCKS mirror),
`docs/projects.md` (priority property plus scheduled rolls; priority marks contract plus vectors
PM1–PM17), `docs/date-marks.md` (scheduled, created, completion, cancelled, recurrence contracts
plus Tasks frame pass), `docs/task-tag-marks.md` (ink palette plus hue reservations plus vault
counts), `docs/task-link-marks.md` and `docs/today-marks.md` (ring and mark family patterns),
`docs/reference/vault-format.md` (lane table, anatomy, field ownership),
`docs/concepts/tasks-and-lanes.md` and `docs/concepts/projects-and-dependencies.md` (lane and cause
mental models), `docs/capture.md` (`&`, `*`, `$<N>` grammar), `docs/getting-started.md`
(vault and registry requirements), `docs/freshness.md` (`lane(t)` mapping, sticky lanes,
`[unblocked::]`), `src/native/config/mod.rs` and `src/native/config/freshness.rs` (configurable
priority ladder), `tests/cli/capture/priority.rs` (priority-plus-scheduled coupling in practice).
No linked or sidecar repos were read (unneeded — the display contracts in this repo are
authoritative for the design question); no peer swarm report was sought or consulted.
