# Per-note Ready concentration: a soft cap of 5, with LOAD as the glance

## Bottom line

This is a good idea, and the vault already proves it. Cap **Ready intake** in each
`[[area]]` / `[[project]]` note at a configurable **N (default 5)**. Treat it as
**concentration pressure**, the sibling of the global `plan.max_ready: 100` volume
cap: same soft-limit language (red when strictly over, never a refusal), a new
glance, and the existing GTD remedies (split with `Ctrl+Shift+Alt+N`, defer with
`Ctrl+Shift+P`).

Do **not** invent a new plugin, a stored `ready_count` field, or a hard block on
moves. Extend the surfaces that already speak this language:

| Surface | What to add |
| --- | --- |
| In-note `<!-- bob:task-status-badges:v1 -->` row | `⚪ 61/5 open` with a `⚠` when over |
| `dash.md` chip row | a **LOAD n** chip, red when *n* > 0, listing the notes |
| `Ctrl+Shift+M` picker | a `6/5` pill on every destination, red when the move would overflow |
| Keymap notices | a `ready 6/5` chip on the existing `.bob-nh-notice` card |
| CLI | `bob projects load` (beautiful, areas + projects) plus a READY column on `bob projects list` |

Count **note-local Ready `[ ]` intake**, not all open tasks, not SHOWN, and not
freshness-gated dash READY. That one choice keeps morning `Alt+F` review from
fighting the cap, matches the `⚪ open` badge Bryan already sees in the note, and
is exactly GTD's "parallel next actions sitting here."

Live on 2026-10-01, after excluding `^prj` and recurring tasks, **four project
notes** are over 5 (`sase` 61, `sase_remote` 11, `sase_pager` 7, `sase_usage` 7).
Most of the 41 active projects already sit at or under the cap. The feature
would light up the actual holding tanks, not the whole vault.

## The question

During morning GTD, Bryan wants no area/project note to hold more than N Ready
tasks (configurable, default 5). If a note is over, the remedies are split
(`Ctrl+Shift+Alt+N` create-project-from-task) and de-prioritize (`Ctrl+Shift+P`).
The request is:

1. Make overloaded notes obvious.
2. Toast when an Obsidian keymap would violate the cap (the example is moving a
   task into a note that already has ≥ N Ready tasks).
3. Badge / diagnostics on `~/bob/dash.md` and/or in the project notes themselves.
4. A visually appealing CLI view of per-note Ready counts and violations.
5. Lead the design: intuitive, reliable, beautiful.

This report critiques that plan, names justified requirement changes as **ADJ-n**,
and recommends an implementation that fits the contracts already in bob-cli and
bob-plugins.

## What is already true

Measured 2026-10-01 against the live vault (`~/bob`), `docs/plan.md`,
`docs/projects.md`, `docs/task-status-hooks.md`, `docs/freshness.md`,
bob-ledger-tools 1.14.0, bob-navigation-hotkeys 1.49.0, and `bob_gtd.md`.

| # | Fact | Evidence |
| --- | --- | --- |
| E1 | Bryan already filed this as Next work: `Show warnings when projects contain >5 ready tasks!` (`bob_gtd#^prj-task-count-warn`). A completed sibling, `^diagnostics`, asked for "project/area files have >=5 ready tasks" plus the global READY/scheduled caps. | `~/bob/bob_gtd.md` lines 22, 34–37; today's ledger links `[[bob_gtd#^prj-task-count-warn]]` |
| E2 | Global READY already has a **soft** cap `plan.max_ready: 100`. The badge shows `READY n/cap`, turns red only when strictly over, refuses nothing, and lives in ledger-tools (`readyBudget` / `renderReadyBadge`). `bob plan` JSON has no READY count. | `docs/plan.md` "READY backlog"; `~/.config/bob/config.yml`; `plan:202610/ready_badge.md` |
| E3 | NEXT (15) and PENDING (10) are the same pattern: soft, red when over, whole-lane pressure in the tooltip. Live vault is already over both (NEXT 31/15, PENDING 50/10). | `bob plan -f json`; `docs/plan.md` lints `next_cap_exceeded` / `pending_cap_exceeded` |
| E4 | Area/project notes already show a **written snapshot** badge row under `## Tasks`: `⚪ open · 🔵 next/wip · 🔴 blocked · 🟢 done/canceled`. The open chip counts root `[ ]` blocks remaining in that container's intake. Hooks regenerate it. | `docs/task-status-hooks.md` "Status Grouping"; `src/native/task_status_groups/emit.rs` `render_badges`; live `sase.md` shows `⚪ 61 open` |
| E5 | `bob projects list` prints OPEN (all open `#task` lines) and SHOWN (open, non-`^prj`, non-hidden, not `[?]`, not future-scheduled). SHOWN includes NEXT and PENDING. Areas are omitted. | `docs/projects.md`; `src/native/projects/output.rs`; live `sase` OPEN 262 / SHOWN 124 |
| E6 | Ready `[ ]` is the Tasks intake. NEXT `[*]` and PENDING `[/]` are sticky lanes; Blocked `[?]` is derived. Releasing with Alt+N is what returns Next/Pending to Ready. Deferring with `Ctrl+Shift+P` (future `scheduled`) derives Blocked and leaves intake. | `decisions:task-lanes-are-sticky`; `docs/projects.md` "Deferring a task" |
| E7 | Dash READY is freshness-gated: visible TODO minus NEW and ROTTEN, minus Today. Confirming with Alt+F moves a task from NEW into READY **without changing the checkbox**. Recurring tasks are out of freshness scope. | `decisions:ready-is-freshness-gated`; `docs/freshness.md` §4; live `dash.md` READY query uses `freshness.bucket === null` |
| E8 | `Ctrl+Shift+M` already moves tasks only into areas and open projects, appending under `## Tasks`. The picker is the `bob-cnp-*` modal with status pills and calendar-clock chips. Notices use `.bob-nh-notice` cards with `is-warn` / `is-ok` chips. Plan-budget already suffixes some notices (`· plan T/3 · L/10 🔴`). | bob-navigation-hotkeys `TaskMoveDestinationPickerModal`; `styles.css` `.bob-cnp-status-pill`, `.bob-nh-notice-chip.is-warn`; block-id-prompt `planBudgetNoticeSuffix` |
| E9 | `bob-project-tasks` materializes `task_count` / `open_task_count` in project frontmatter from the `## Tasks` section, counting `[ ]`, `[/]`, `[*]` (not Ready-only, not freshness). Live `sase.md` has `task_count: 269`, `open_task_count: 124`. | `plugins/bob-project-tasks/main.js`; live `sase.md` frontmatter |
| E10 | Capture routes are top-level `[[area]]` and non-terminal `[[project]]` notes. Create-project-from-task is `Ctrl+Shift+Alt+N`. | `docs/capture.md` capture-targets; `docs/projects.md`; navigation-hotkeys `create-project-note-from-task` |
| E11 | GTD's official rule is **at least one** parallel next action per project, not an upper bound. Sequential steps belong in project support / `dependsOn`, not on the next-action list. Practitioners report gridlock around 4–5 NAs on one project. | [Allen, Managing Projects](https://gettingthingsdone.com/2017/05/managing-projects-with-gtd/); [Allen on action lists](https://gettingthingsdone.com/2010/02/managing-projects-tips-from-david-allen/); GTD forum threads on multiple NAs |
| E12 | The weekly prune chore already looks for the **dual**: "projects with no Next or Ready task." Overloaded and starved are two ends of the same review. | `~/bob/gtd_daily.md` weekly prune task |
| E13 | `plan.strict` is the only hard refusal in this family, and it only refuses extra Pomodoro themes. Lane caps never refuse capture, moves, or stamps. Invalid plan config falls back with a warning everywhere except `bob plan` (exit 2). | `docs/plan.md` Config; `src/native/config/plan.rs` |
| E14 | Bob Mac Capture is a thin client of `bob`. Any capture-time warning belongs in bob's JSON; the Mac app only renders it. | `decisions:mac-capture-is-a-thin-client` |

### Live numbers (2026-10-01)

Ungated Ready-pool query (the native READY query: TODO, not blocked, not `#hide`,
not future-scheduled, not templates/conflicts), then drop `^prj` and recurring:

| Note | Kind | Ready `[ ]` | vs N=5 |
| --- | --- | ---: | --- |
| `gkeep_inbox.md` | area (Keep drain) | 65 | over, **exempt candidate** |
| `sase.md` | project (parent of ~30 children) | 61 | over |
| `sase_remote.md` | project | 11 | over |
| `sase_pager.md` | project | 7 | over |
| `sase_usage.md` | project | 7 | over |
| `cash.md` | area | 5 | at cap |
| `bob.md` | project | 5 | at cap |
| `sase_bug_bash.md` | project | 5 | at cap |
| 21 other notes | area/project | 1–4 | under |

- 41 active projects, 13 area notes, 84 project notes scanned (including done).
- Freshness today: 199 fresh, 1 new, 0 rotten, 0 resurfaced. Almost every Ready
  `[ ]` in the table is already confirmed, so gating would barely change the
  over-list this morning.
- `gtd_daily.md` showed 7 in the raw READY query; all 7 are `repeat::` habits
  and drop out of a well-defined Ready-intake count.
- `sase.md`'s own badge already agrees: `⚪ 61 open · 🔵 63 next/wip · 🔴 137 blocked`.
  OPEN 262 / SHOWN 124 on `bob projects list` are the wrong denominators for this
  cap (they mix Next, Pending, and hidden).
- Histogram: 8 notes at 1, 5 at 2, 3 at 3, 2 at 4, 2 at 5, then the four
  (plus inbox) over. The default of 5 is already the cluster edge of the healthy
  vault.

`sase.md` is not an accident. It already has a generated Sub-projects line with
dozens of children. The 61 remaining Ready tasks are the "not yet split"
remainder — exactly the situation the feature is for.

## Critique of the proposed plan

### What is right

**Concentration is a different axis from volume.** `plan.max_ready: 100` asks
"is the whole backlog too big?" This feature asks "is too much of it sitting in
one note?" Those can fail independently. A 90-task READY spread across 30 notes
is healthy; 61 of them in `sase.md` is not. The morning glance needs both.

**Five is a good default.** It is not a GTD law (Allen's floor is one parallel
NA, with no official ceiling). It is a *prompt*: "are these really all next, or
is this two projects and a handful of sequential steps wearing a `[ ]`?" The
live histogram says 5 is where the vault's healthy projects already live.
Configurable is required (`sase.md` will need an override until it is split).

**The remedies named in the request are the right ones.** Split
(`Ctrl+Shift+Alt+N`) and defer (`Ctrl+Shift+P` → future `scheduled` → derived
Blocked, which grouping already lifts out of intake). Both already exist, already
stamp freshness, already write schedule logs. The new work is *signal*, not a
new editing verb.

**A toast on the move keymap is the right moment.** `Ctrl+Shift+M` is the
gesture that *concentrates* Ready work into a note. Catching it in the
destination picker (before commit) is better than catching it after. The
existing picker already knows how to show a status pill and a calendar chip per
row.

**Showing it on dash and in the note is right.** Dash is the morning board;
the note is where Bryan stands when deciding to split. CLI is the headless
twin of both, matching how `bob plan` / `bob freshness list` / `bob projects list`
already work.

### What is wrong, or too vague

**"Ready tasks" is ambiguous in this vault today.** After
`decisions:ready-is-freshness-gated`, dash READY is the confirmed/exempt subset
of `[ ]`. The in-note `⚪ open` chip is the `[ ]` intake, including NEW. OPEN
on `bob projects list` is every open checkbox. SHOWN adds Next and Pending.
If the cap uses the wrong denominator, the signal lies:

- Counting OPEN/SHOWN would paint `sase` as 262/124 over forever, including
  committed Next/Pending work that must not be split away.
- Counting freshness-gated dash READY would make **Alt+F during morning
  review** the thing that trips the cap. That fights the ritual that just
  shipped (`gtd_daily` "clear NEW to 0 first"). Confirming a task does not add
  a next action; it only endorses one that is already sitting there.
- Counting intake `[ ]` (the `⚪ open` chip, minus `^prj` and recurring)
  matches what Bryan sees in the note, ignores sequential/Blocked work, and
  does not move when a stamp lands. That is the GTD next-action pile.

**Toasting "anytime we use any keymap that would violate"** is too broad and
will fatigue. Many keymaps can raise the count (promote a bullet, release
Alt+N, unblock, unscheduling, capture, gkeep pull, restore a project into its
parent). A toast on every one, every time a note is already over, trains Bryan
to dismiss notices. The useful moments are (1) *choosing a destination* and
(2) *crossing the cap*. Standing in an already-over note and completing a
Blocked dependent should not pop a toast; the badge is enough.

**Hard-blocking a move would be a mistake.** Capture inboxes overflow; that is
their job. `sase.md` is over *now* and still has to receive the occasional
task until it is split. Every other Bob lane cap is soft. `plan.strict` exists
only for extra Pomodoro themes, and even that is off. Refusing `Ctrl+Shift+M`
would fight GTD capture.

**Areas are not projects.** PARA/GTD areas of responsibility (cash, job, love,
body) naturally hold a standing set of next actions and never complete.
Capture inboxes (`inbox`, `mac_inbox`, `gkeep_inbox`) are processing buckets,
not split candidates. Applying the same "create a new project" remedy to
`gkeep_inbox.md` (65 Keep drains) is the wrong action; the right action is
*process and route*. The request says "area/project" in one breath; the
implementation should still distinguish them.

**Writing the count into frontmatter would go stale.** `bob-project-tasks`
already does this for a coarser number, and `docs/task-status-hooks.md`
already warns that the badge row is a snapshot until the next hooks pass.
Ready-intake is a function of checkbox, hide, schedule, dependencies, and
recurrence — the same class of "computed at read time" facts as Today and
freshness. A `ready_count:` field would be `#today` / `#rotten` all over
again.

**Dash does not need a new Tasks section of the overloaded tasks.** READY is
already grouped by path (`TQ_extra_instructions: group by path`). A chip plus
a short list of *notes* is the glance; dumping those tasks into a seventh
lane would fight TODAY / NEW / PENDING / NEXT / READY exclusivity the same
way a dash INBOX section was rejected in the freshness research.

**`bob projects list` cannot be the only CLI.** It skips areas, and its SHOWN
column is the wrong number. Extending it is useful; a dedicated load view is
the one Bryan will actually enjoy looking at.

## Requirement adjustments

These change the request. Each is marked so a lead can accept or reject it
without unpicking the rest.

**ADJ-1. Soft limit, never refuse.** Red when count > N; at N is fine (same
rule as `max_ready` / `max_next` / `max_pending`). Moves, captures, releases,
and stamps always succeed. Optional `bob projects load --check` exits 1 for
scripts; the default human command exits 0.

**ADJ-2. Count note-local Ready intake, not dash READY and not OPEN/SHOWN.**
A task counts if it is a root `#task` in an `[[area]]` or `[[project]]` note
with status `[ ]` (Ready), not `#hide`, not recurring, not `^prj`, and not
already grouped into Next/WIP, Blocked, or Done. That is the `⚪ open` badge
minus lifecycle and habits. Tooltip may show `61/5 · 1 new` for freshness
composition; the cap itself does not wait on a stamp.

**ADJ-3. Cap is per note file, not per heading and not rolled up through
`parent`.** Topic containers under `## Tasks` share one budget. Child projects
have their own. `sase.md` at 61 with healthy children is the intended signal.

**ADJ-4. Exempt capture inboxes from the split-project cap.** Default exempt
routes: `inbox`, `mac_inbox`, `gkeep_inbox`. They can still appear in the CLI
in a dim "inbox" group. Their remedy is process-to-zero, not `Ctrl+Shift+Alt+N`.
`recur.md` is similarly a habit parking lot; exclude it by the recurring-task
rule in ADJ-2, and optionally by name.

**ADJ-5. Same default N for areas and projects, with an optional `area_cap`
and a per-note override.** Frontmatter `max_ready: 20` on `sase.md` (mirror
`task_refresh`) keeps the parent holding tank from dominating every glance
until it is split. Without an override, `sase.md` will be red every morning,
which is honest but loud.

**ADJ-6. Toast on crossing, and on increasing an already-over note, for a
short allow-list of keymaps — not "any keymap."** Required: `Ctrl+Shift+M`
(the request's example). Also: bullet-to-task promotion into `## Tasks`
(`Ctrl+Shift+]`), Alt+N release into Ready, create-project-from-task when the
*new* note would start over N. Do **not** toast on Alt+F / Alt+Shift+F
(ADJ-2 makes this a no-op anyway), on unattended hooks recovery, or on every
edit in an already-over note. Prefer the picker chip over the post-commit
toast when both exist.

**ADJ-7. Do not persist Ready counts in frontmatter.** Live evaluator in
ledger-tools; snapshot only in the hooks-owned badge row that already exists
(`⚠ 61/5 open`). Leave `bob-project-tasks` alone.

**ADJ-8. New config, not a reuse of `plan.max_ready`.** That key is the global
backlog cap of 100. A nested `plan.note_ready` block keeps the two axes from
colliding and has room for `exempt` / `area_cap`.

**ADJ-9. No new dash Tasks lane.** One **LOAD n** chip, red iff n > 0, whose
tooltip lists the overloaded notes and whose click opens a compact `### LOAD`
list of wikilinks (or jumps to `bob_gtd#^prj-task-count-warn` until that
section exists). Chip order stays NEW, PENDING, NEXT, READY, **LOAD**,
BLOCKED, ROTTEN, TODAY.

**ADJ-10. CLI covers areas and projects.** `bob projects list` gains a READY
column (projects only, backward compatible). New `bob projects load` is the
beautiful view and the JSON contract.

**ADJ-11. Out of scope: starved notes (0 Ready).** The weekly prune already
asks for "projects with no Next or Ready task." A future LOAD tooltip can
mention starved counts; do not ship it in v1.

## Alternatives considered

| Alternative | Why not (for v1) |
| --- | --- |
| Hard-block `Ctrl+Shift+M` / capture when dest is at cap | Fights GTD capture; `sase.md` and inboxes must still accept work |
| Count freshness-gated dash READY | Alt+F during morning review trips the cap; NEW piles look healthy |
| Count OPEN or SHOWN | Mixes Next/Pending/hidden; `sase` 262/124 is not a next-action pile |
| Count only P0 (no priority field) | Deferral already removes the task from intake via Blocked; double-counting the medicine |
| New `bob-note-ready` plugin | Six plugins already; this is an evaluator + three renderers |
| `ready_count` in YAML via bob-project-tasks | Stale between hooks; wrong predicate (all open statuses) |
| Dash section of the overloaded *tasks* | Seventh lane; READY already groups by path |
| Auto-suggest which tasks to split | Beautiful later; v1 is the signal. Create-project-from-task is already the verb |
| Kanban WIP of 3 | Stricter than the vault's healthy cluster (many notes already at 4–5); 5 matches the filed task |
| Fold into the READY chip tooltip only | Hidden; the request is to make overloaded *notes* obvious at a glance |
| Reuse `bob plan` JSON | `bob plan` is the daily ledger. This is a vault-wide note scan, like `bob projects list` |

## Recommended solution

Ship **Note Ready Concentration** as one shared evaluator and three renderers,
in the same two-language pattern as plan budget and freshness.

```text
                    ~/.config/bob/config.yml
                    plan.note_ready.cap: 5
                              │
                              ▼
                 ┌────────────────────────┐
                 │  noteReady evaluator   │
                 │  Rust  ⟷  JS vectors   │
                 └────────────┬───────────┘
            ┌─────────────────┼─────────────────┐
            ▼                 ▼                 ▼
     bob projects load   ledger-tools api   hooks badge row
     bob projects list   dash LOAD chip     ⚠ 61/5 open
                         picker pill
                         notice chip
```

### 1. Definition

For each Markdown file whose frontmatter `type` is `[[area]]` or `[[project]]`
(bare `[[area]]` / `[[project]]` accepted, same scan skips as `bob projects`):

```text
count(note) = number of root #task blocks in that file such that
              status is Ready `[ ]`
          and not #hide
          and not recurring
          and not the ^prj lifecycle task
          and not sitting in a generated Next/WIP, Blocked, or Done group

cap(note)   = frontmatter max_ready
              else area_cap if kind is area
              else plan.note_ready.cap
              else 5

over(note)  = count > cap
              and note is not in plan.note_ready.exempt
```

Exactly at the cap is fine. Hidden, blocked, future-scheduled, Next, Pending,
done, cancelled, and habits do not count. That is GTD: only parallel next
actions in this note.

Conformance vectors (shared Rust/JS, same style as freshness placement):

| # | Note contents (roots) | count |
| --- | --- | ---: |
| 1 | 4× `[ ] #task`, 1× `^prj` | 4 |
| 2 | 5× `[ ] #task` | 5 (not over) |
| 3 | 6× `[ ] #task` | 6 (over) |
| 4 | 6× `[ ]` of which 2 are `#hide` | 4 |
| 5 | 3× `[ ]`, 2× `[*]`, 2× `[/]`, 4× `[?]` | 3 |
| 6 | 7× `[ ]` with `repeat::` | 0 |
| 7 | 6× `[ ]` in an exempt inbox | 6, `over: false`, `exempt: true` |
| 8 | 6× `[ ]` with frontmatter `max_ready: 10` | 6, not over |
| 9 | `[ ]` under a `### Backend` topic plus 3 in main intake | 4 (per file) |

### 2. Config

```yaml
plan:
  max_ready: 100          # existing global READY volume cap
  note_ready:
    cap: 5                # per-note Ready intake; default 5
    # area_cap: 8         # optional; default is cap
    exempt: [inbox, mac_inbox, gkeep_inbox]
```

Validation matches the rest of `plan:`: integers ≥ 1, exempt is non-empty
strings (route stems). Unknown keys ignored. Invalid block: `bob projects load`
exits 2; Obsidian falls back to defaults and says so once on the chip tooltip,
never breaking a keymap.

Per-note override, residence not parent, same integer range:

```yaml
# sase.md
max_ready: 20
```

### 3. CLI — the beautiful view

`bob projects load` is read-only. Human output, color when stdout is a TTY
(`cli_rules.md`), `NO_COLOR` respected.

```text
Note ready  ·  4 over  ·  cap 5  ·  41 projects  ·  13 areas

  NOTE              KIND      READY
  sase              project    61/5  ████████████████████  over
  sase_remote       project    11/5  ██████░░░░░░░░░░░░░░  over
  sase_pager        project     7/5  ████░░░░░░░░░░░░░░░░  over
  sase_usage        project     7/5  ████░░░░░░░░░░░░░░░░  over
  cash              area        5/5  ███░░░░░░░░░░░░░░░░░
  bob               project     5/5  ███░░░░░░░░░░░░░░░░░
  sase_bug_bash     project     5/5  ███░░░░░░░░░░░░░░░░░
  dev               area        4/5  ██░░░░░░░░░░░░░░░░░░
  …

  inbox  gkeep_inbox  65  (exempt)
```

Rules that make it pleasant:

- Sort: over first, then count descending, then name. Under-cap notes can hide
  behind `--over` (default: show over + at-cap + a short under tail, or show
  all; I recommend **all notes with count > 0**, compact).
- Bar is count/max(count, cap) in 20 columns so a 61/5 bar is full, not 12×
  overflowing.
- `over` in red, at-cap in yellow, under in dim green. Kind in cyan.
- `--over` lists only violators. `--check` exits 1 when `over_count > 0`.
- `-f json` with `schema_version: 1`, `ok`, `caps`, `over_count`, `notes[]`
  (`path`, `kind`, `count`, `cap`, `over`, `exempt`).

`bob projects list` gains a READY column next to SHOWN, colored the same way,
projects only. Help text points at `load` for areas and the bar view.

Options, alphabetically, each with a short alias: `-b/--bob-dir`,
`-c/--check`, `-f/--format`, `-h/--help`, `-o/--over`.

### 4. Dash — LOAD chip

Ledger-tools grows `api.noteReadyReport()` and `api.renderLoadBadge(parent, options)`,
versioned next to `readyBudget` / `renderReadyBadge` (api v3 freshness
namespace stays; this is a sibling, not a freshness feature).

Chip: **LOAD n**, where n is the number of non-exempt notes with `over`.
Primary number is the note count, not the task sum (61+11+7+7 would look like
another READY). Red (`task-count-over`) iff n > 0. Tooltip:

```text
LOAD 4 · sase 61/5 · sase_remote 11/5 · sase_pager 7/5 · sase_usage 7/5
4 notes over the per-note Ready cap of 5. Open LOAD.
```

Click opens `dash#LOAD` (a short DataviewJS or Markdown list of those
wikilinks, not a Tasks query). Fallback when the plugin is old: omit the chip,
never a silent zero. Unavailable Tasks cache: `LOAD –`.

Place it after READY and before BLOCKED. Do not add this count to `bob plan`
or the daily `bob-plan` block in v1 (daily notes are not the concentration
board). A later tale can put a muted `LOAD 4` on the status bar.

### 5. In the project/area note

Reuse the hooks-owned badge row. Today:

```markdown
<!-- bob:task-status-badges:v1 -->
[`⚪ 61 open`](#…#Tasks) · [`🔵 63 next/wip`](#…) · …
```

v1.1 of the same marker (still `v1` if the parser already ignores unknown
trailing text; otherwise keep the marker and change only the open chip):

```markdown
[`⚠ 61/5 open`](#…#Tasks) · [`🔵 63 next/wip`](#…) · …
```

- Under or at cap: `⚪ 4/5 open` / `⚪ 5/5 open`.
- Over: `⚠ 61/5 open`.
- Exempt notes keep `⚪ 65 open` with no `/cap`.
- Counts stay a snapshot; the next `bob task-status-hooks` pass heals them,
  as today.

Optional live overlay in reading view (ledger-tools, same CSS as dash chips)
can color that chip without waiting for hooks. Do not add a second row.

### 6. Picker and notices (the keymap moment)

**`Ctrl+Shift+M` destination picker** is the flagship.

Each area/open-project row gets a trailing pill `4/5` or `61/5`, using the
existing `.bob-cnp-status-pill` geometry. Over rows use the warn/error tone
already used for canceled status icons. The subtitle can read
`3 selected tasks · 4 destinations over 5`. Do not hide or disable over
destinations. After commit, the existing move notice gains a chip:

```text
Moved 3 tasks → sase
[ready 64/5]  [+3]   is-warn
Split with Ctrl+Shift+Alt+N · defer with Ctrl+Shift+P
```

If the move *crosses* the cap, the chip is the notice's accent. If the note
was already over and the count rose, same chip, quieter copy (`still over`).
If the destination stays ≤ cap, no extra chip (green `ready 4/5` is noise).

**Other allow-listed keymaps** (ADJ-6) append the same chip through one helper,
`noteReadyNoticeChip(path, before, after)`, shared by navigation-hotkeys and
the cycler. Block-id-prompt already does this for plan budget
(`planBudgetNoticeSuffix`); copy that degrade-to-empty pattern.

**Create-project-from-task** is the remedy. Do not toast the *source* note
(its count dropped). Do toast if the *new* project would open with count > N
("this split is still over 5 — pick fewer children").

Capture (`bob capture`, Mac Capture JSON): a warning field
`note_ready: { path, count, cap, over }` on the response, never a refusal.
Mac Capture renders it; it does not compute it.

### 7. Reliability

- **One predicate, two implementations**, pinned by the vectors in §1.
  Headless `bob projects load` is the oracle; ledger-tools matches it the
  way `readyCountFromTasks` matches `docs/plan.md`.
- **Read-time.** No YAML field, no `#over` tag, no extra hooks writer beyond
  the existing badge row.
- **Unavailable is `–` / omit, never a silent 0.** Same contract as READY.
- **Mobile:** ledger-tools is not desktop-only. Config missing → defaults.
  Hooks still run on the MacBook; the snapshot badge can lag on iPhone, the
  live dash chip will not if Tasks data is there.
- **Performance:** one pass over area/project notes, or a fold over the
  already-loaded Tasks cache in Obsidian. 84 project files + 13 areas is
  cheap. Memoize on the Tasks array identity + local date + config, same as
  freshness.
- **`^prj` never counts.** Lifecycle outcome is not a next action.
- **Do not count tasks in `dash.md`, dailies, templates, `_conflicts`, or
  `done/`.**

### 8. Beauty notes (so the implementation does not ship a table and call it done)

- Dash LOAD chip uses the same geometry, type ramp, and red-over language as
  READY. It must not introduce a new shape.
- Picker pills are tabular-nums, fixed min-width, so rows do not dance as
  counts go from `4/5` to `11/5`.
- CLI bars use the existing `Styler` (cyan names, red `over`, dim separator
  `·`). Twenty-column bars, not 61 hash marks.
- Notices reuse `.bob-nh-notice-chip.is-warn` (orange) for over; do not
  invent a third notice family.
- The in-note `⚠` is the only new glyph, and only when over. Empty buckets
  still show `0` on the other chips so the row stays stable.

### 9. Suggested landing (PR DAG)

A single medium epic, three tales, matching how READY badge then freshness
gating landed:

| Tale | What | Repos |
| --- | --- | --- |
| 1 | Config + Rust evaluator + `bob projects load` + READY column on `list` + docs | bob-cli |
| 2 | JS evaluator + vectors + dash LOAD chip + in-note badge `n/cap` | bob-cli (vectors/docs) + bob-plugins (ledger-tools, hooks emit) |
| 3 | Picker pills + notice chips on the allow-list + capture JSON warning | bob-plugins (+ bob-mac-capture only if the JSON field should render in v1) |

Tale 1 is useful the next morning from the terminal, even if Obsidian lags.
Do not ship toasts without the dash chip: a notice with no durable glance
teaches nothing by afternoon.

Keep rule for a two-week trial, same spirit as freshness-gated READY: the
LOAD chip is red on no more than ~3 weekday mornings after the first split
pass on `sase.md` (or after setting its `max_ready` override); Bryan uses
`Ctrl+Shift+M` picker pills at least once to *avoid* an overloaded dest;
no lost-task case from a refusal (there is none).

## What I would not do

I would not block keymaps. I would not count gated READY. I would not apply
the split-project sermon to `gkeep_inbox.md`. I would not write `ready_count`
into YAML. I would not add a seventh dash lane. I would not start with a
clever auto-splitter.

The vault's own `⚪ 61 open` on `sase.md` is already the number. Put `/5`
next to it, put `LOAD 4` on the dash, put `61/5` on the move picker, and
give the terminal a bar chart. Then the morning review has a new question
with a verb attached: *which note is a pile, and do I split or defer?*

## Sources

- Live vault, 2026-10-01: `bob projects list`, `bob plan -f json`,
  `bob freshness list -f json`, native Tasks READY query grouped by path,
  `~/bob/dash.md`, `~/bob/sase.md`, `~/bob/gkeep_inbox.md`,
  `~/bob/gtd_daily.md`, `~/bob/bob_gtd.md`, `~/bob/cash.md`
- bob-cli: `docs/plan.md`, `docs/projects.md`, `docs/task-status-hooks.md`,
  `docs/freshness.md`, `docs/capture.md`, `src/native/config/plan.rs`,
  `src/native/projects/`, `src/native/task_status_groups/`,
  `sase/memory/cli_rules.md`
- Decisions: `ready-is-freshness-gated`, `task-lanes-are-sticky`,
  `task-status-is-derived`, `mac-capture-is-a-thin-client`
- bob-plugins: ledger-tools `readyBudget` / `renderReadyBadge` /
  `dashboardLaneBudget`; navigation-hotkeys move picker + notice CSS;
  bob-project-tasks frontmatter counts
- GTD: [Managing projects with GTD](https://gettingthingsdone.com/2017/05/managing-projects-with-gtd/)
  (at least one parallel NA; sequential steps stay in project plans);
  [Managing Projects — tips from David Allen](https://gettingthingsdone.com/2010/02/managing-projects-tips-from-david-allen/)
  (sequential NAs dull the list; 4–5 NAs on one project caused gridlock
  for practitioners)
- Prior Bob research: `research:202610/freshness_gated_ready_dash` (read-time
  partition, no stored tags, soft READY cap as volume pressure)
