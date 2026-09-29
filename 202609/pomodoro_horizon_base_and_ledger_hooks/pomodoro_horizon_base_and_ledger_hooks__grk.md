# Pomodoro ledger, task horizons, and the automations the last paper skipped

- **Researcher:** grk
- **Date:** 2026-09-29
- **Question:** Should Bryan change how he tracks pomodoros, work, time, and the day's roadmap — and if so, what should change, including automation (`bob capture`, Bob Mac Capture, Obsidian keymaps, `bob task-status-hooks`) and a `roadmap.base` / dash-chip design the previous paper did not consider?
- **Prior paper (shared input):** `sase--research` `202609/pomodoro_ledger_and_daily_roadmap/pomodoro_ledger_and_daily_roadmap.md` (consolidated 2026-09-29), plus vault highlights in `~/bob/ref/chat/pomodoro_ledger_and_daily_roadmap.md`.
- **This report:** independent vault measurements, tooling audit, and a recommended design that keeps the ledger, caps today, and stores the inventory on the tasks themselves.

## Headline

**Change the process, and automate the constraint.** Keep `## Pomodoros` and the completed ledger exactly as they are. Stop using the *open* part of that section as a rolling backlog. Do **not** create a second markdown file of copied task links (`roadmap.md` as a cut-paste bucket list). Put the inventory on the tasks with `[horizon:: now|next|later]`, show counts as chips on `dash.md` (the same widget already used for WIP / NEXT / READY), and use `roadmap.base` for *project notes* grouped by horizon. Enforce the daily cap in `bob capture`, Bob Mac Capture, the existing Ctrl+Shift+P / Ctrl+Shift+Enter keymaps, and `bob task-status-hooks` — which already runs every 15 minutes on the Mac.

The previous paper's diagnosis is right. Its recommended *storage* (a hand-maintained `roadmap.md`) and its *deferral of tooling* are the parts to replace. The planning ritual already lapsed on 2026-09-09; another ritual that depends on cut-paste will lapse the same way. The constraint has to live in the tools that currently dump work onto today.

---

## 1. Independent measurements (2026-09-29)

All figures below are from this run, against `~/bob/2026/202609*.md`, `bob query --tasks` with `dash.md` as origin (so they match the dashboard chips), and git history of `2026/20260925.md`.

### 1.1 Capacity is stable

| Metric | September 1–29 |
| --- | --- |
| Logged days | 29 |
| Completed blocks | 208 |
| Tracked minutes | 8,295 |
| Mean minutes / day | **286** |
| Mean completed blocks / day | **7.2** |
| Today so far (`20260929.md`) | 6 blocks, **210** minutes |

Block names on completed entries this month (top): GTD 46, REMOTE 17, SHIT 15, SASE 10, GOALS 10, BOB 9, TOOL 8. Distinct completed theme names: 52.

Time share of completed named blocks:

| Bucket | Minutes | Share |
| --- | --- | --- |
| GTD (name contains `GTD`) | 1,750 | **21.1%** |
| Reactive (`SHIT`, `FIXES`, `RELAUNCH`, `RESTARTS`) | 1,205 | **14.5%** |
| Everything else | 5,340 | **64.4%** |

That is about **five of seven** daily blocks for chosen work, plus a standing GTD tax and a reactive tax. A closed daily list sized at three themes + GTD fits this record. Variable block length is already the working style (today includes 15m, 25m, 35m, 75m).

### 1.2 The open queue is a mid-day artifact that migration erases at night

End-of-day files for Sep 1–28 have **zero** open named placeholders. Today's still-open file has **22** named open entries and **74** unique task links under them (75 unique block links in the whole section, 7 of them only under completed blocks).

Git of `20260925.md` at 19:27 (`757056a0`) still had **19** open named entries and **60** open links. The next morning's file is clean. Migration is doing its job as a *copier*, and that is the problem: the queue survives as status inflation and as tomorrow's paste, while the daily note looks tidy in git.

Open names on today, in file order:

`GTD`, `BOB`, `GOALS`, `SASE`, `DECKS`, `SASE` (again), `READ`, `MISC`, `FINAL`, `RENAME`, `TOOL`, `CLEANUP`, `REMOTE`, `SERVICE`, `NEW FEATURES`, `SUDO`, `FAST TESTS`, `QUEUE`, `SCHEDULE`, `AUDIT MEMORY`, `GATES`, `LATER`.

`LATER` and `NEW FEATURES` sitting in *today's* ledger is the design admitting it is an inventory. Inventory labels do not belong on a closed daily list.

### 1.3 Status chips are already lying, in the way Little's Law predicts

`bob query --tasks` with `dash.md` origin (global `#task` filter, dash Query File Defaults: not blocked, not `#hide`, scheduled today or earlier):

| Query | Task lines |
| --- | --- |
| `status.type is IN_PROGRESS` | **50** |
| `status.name includes Next` | **25** |
| `status.type is TODO` | **171** |
| `not done` | **246** |

WIP + NEXT = **75** items that the dashboard presents as "active." At about five closures a day that is a ~15-day wait, which matches the previous paper's age-of-queue story. The chips on `dash.md` are the right *UI*; they are pointed at the wrong *set*.

`gtd_daily.md` still has "Migrate unfinished Pomodoro tasks" scheduled for today and completed through 2026-09-28. "Review WIP + NEXT … plan daily Pomodoros" and "Review READY tasks" are still sitting on **2026-09-10**, last completed **2026-09-09**. Today's `^gtd` checkbox is In Progress; yesterday's was cancelled.

### 1.4 What the tooling actually does today

| Surface | Behavior that creates or hides the pile |
| --- | --- |
| `bob capture` `@route:id` | New Next (`[*]`) task **and** a ledger link under today's current/first open Pomodoro. `#name` creates `- [ ] () — NAME` when no open match exists. |
| `bob capture` `@route^id` | Ready task with a block ID and **no** ledger link. Already the "not for today" spelling. |
| `s:<N>` / `p:<N>` | Existing terminal markers. Priority rolls a scheduled window via the same machinery Ctrl+Shift+P uses. **Do not overload `p:` as a horizon.** |
| `bob task-status-hooks` | Open-ledger links are the source of truth for Next. Unreachable Next/In Progress reset toward Ready. Deletes childless Pomodoros, de-dupes links, repairs 🍅. Cron on the Mac: `10,25,40,55 * * * * bob task-status-hooks --retry-timeout 120`. |
| `block-id-prompt` Ctrl+Shift+Enter | Links the task under the current/next Pomodoro and promotes to Next. |
| `bob-navigation-hotkeys` Ctrl+Shift+P | Edits `scheduled`, dependency, and `priority`. Future `scheduled` already **prunes** the task from today's open Pomodoros. |
| `dash.md` | DataviewJS chip bar + Tasks queries for WIP / NEXT / READY. `![[projects.base]]` and `![[refs.base]]` already embed Bases files. Daily notes set `alt_file: "[[dash]]"`. |
| Project notes | `<!-- bob:task-status-badges:v1 -->` count row (`⚪ open · 🔵 next/wip · 🔴 blocked · 🟢 done/canceled`), written by the same hooks family. |
| `now.md` / `soon.md` | Zorg-era next-action files, `generated_from_zorg: true`, last source mtime 2026-01-08. Dead layer. Horizon fields on live `#task` lines replace them. |
| Bob Mac Capture | Delegates grammar to `bob capture-parse`. Semantic palette already has `.schedule` and `.priority`. `:id` / `#name` / `=<X>` / `=x` are first-class. |

The heading `## Pomodoros` is load-bearing (`is_pomodoros_heading`, plugin `POMODOROS_HEADING_RE`, capture, `bob pomodoro`, tmux). Leave it.

---

## 2. Where the previous paper is right

The consolidated `pomodoro_ledger_and_daily_roadmap.md` is a good diagnosis. These claims hold up against this run's numbers:

1. **The completed ledger is fine.** Time ranges, `[t::]`, ALL-CAPS names, 🍅, short notes. Variable length is Flowtime-shaped focus, which the 2023–2026 break-taking trials do not punish relative to strict 25/5.
2. **The open section is doing four jobs:** today's plan, the activity inventory, the Next/In Progress source, and the capture inbox. Cirillo's To Do Today / Activity Inventory / Records split is the right conceptual cut.
3. **Capture into today + migrate + lapsed selection** is the growth engine. End-of-day cleanliness is a trick of the copier.
4. **A closed daily list** (Forster) sized from the ledger's own median (planning-fallacy literature: Buehler, Griffin & Ross 1994) is the right daily shape: one highlight-scale outcome, at most two other themes, GTD, about ten links.
5. **Do not rename the heading. Do not add a second time tracker. Do not calendar-block the whole day** (`gtd_ideas.md` already `@REJECTED` an "ideal calendar" as GCal noise).
6. **Status coupling is load-bearing.** A `## Roadmap` section *inside* the daily note would silently demote today's picks, because hooks only promote from open entries under `## Pomodoros`. Sub-headings would also break the heading total (`meta(task.section).subpath`).

Keep those conclusions.

---

## 3. Shortcomings of the previous paper (the ones this report is for)

The user already named the two biggest holes. There are more.

### 3.1 No automation, and tooling explicitly deferred

§7.7 of the prior paper parks capture guards, plan-load in `bob pomodoro` / tmux, Dataview hit-rate, and hooks-reading-`roadmap#Now` behind "after the habit holds for two weeks." The habit that was supposed to *select* already died on 2026-09-09. Capture still writes into today; migrate still copies; hooks still promote whatever is linked. A two-week trial of *willpower against those three machines* is the same design that produced 22 open names.

The Mac already runs `task-status-hooks` four times an hour. That is the enforcement bus. Use it in week one.

### 3.2 `roadmap.md` as a copied bucket list

The recommended storage is "cut today's open buckets into `roadmap.md` as-is." That creates a **second copy** of task identity. The tasks already live in `bob.md`, `sase.md`, `sase_goals.md`, … with block IDs. A second list of `[[sase#^card-blocks]]` lines will drift the first time someone completes a task in the project note and forgets the roadmap, or reorders the roadmap and forgets the project note.

Morning pick in that design is still a **migrate**. The destination changed from "tomorrow's daily" to "`roadmap#Now`." The motion that already dominates GTD time (21% of September minutes) stays.

### 3.3 `roadmap.base` was not considered — and Bases cannot list checkbox tasks

Bryan already uses Bases as a vault primitive: `projects.base`, `refs.base`, `eat.base`, `podcasts.base`, all embedded from `dash.md`. Official Bases help: a view's rows are **files**; columns are note/file properties; layouts are table / list / cards / kanban / map. Community "task" Bases plugins (Task Base, TaskNotes, Canvas Bases) work by making **one note per task**. Bryan's work unit is an inline `#task` checkbox with a `^block-id` inside a project note.

So:

- `roadmap.base` is the right tool for **project notes** (`type: project`, optional `horizon` frontmatter), in the same way `projects.base` already tables them. This is also what `bob#^better-roadmaps` asked for: support for roadmaps / structure notes like `sase_blog_blockers`.
- `roadmap.base` **cannot** be the Now / Next / Later rendering of checkbox tasks. That rendering has to be Dataview TASK queries or Tasks `filter by function` over `[horizon:: …]` on the task line — the same pattern `dash.md` already uses for status chips.

A `.base` that pretends to be a paste-buffer for `[[note#^id]]` children is the wrong primitive.

### 3.4 Dash chips were not reused

`dash.md` already has a DataviewJS chip bar with counts, colors, hover, and jump targets for WIP / NEXT / READY / BLOCKED. Daily notes point at it (`alt_file: "[[dash]]"`). Adding NOW / SOON / LATER chips there is a copy of an existing widget, not a new surface. The prior paper's `roadmap.md` would have been a third place to look (daily + dash + roadmap).

### 3.5 Dataview properties on tasks were not used as the inventory axis

The vault already treats `[key:: value]` as the task metadata bus: `created`, `scheduled`, `priority`, `completion`, `id`, plus plugin-managed SCHEDULE LOG / WORK LOG children. `src/native/task_fields.rs` scans `[key:: value]` and `(key:: value)` for every consumer (toggle, projects sync, picker). Adding `[horizon:: now]` is a new key on an existing scanner, queryable by Dataview as `task.horizon` and styleable by the existing `dataview-properties.css` snippet.

Status (`[ ]` / `[*]` / `[/]` / `[?]`) and horizon (`now` / `next` / `later`) are **different axes**. The prior paper overloaded Next to mean "on today's ledger" and used markdown headings to mean Now/Next/Later. That collision is why a closed daily list kept fighting hooks.

**Name the chips SOON for the middle bucket.** The Tasks status is already called Next (`[*]`, green chip). Horizon values can still be `now|next|later` in the field (ProdPad language, and the user's request). The dashboard labels should be **NOW / SOON / LATER** so the two "next"s do not share a word.

### 3.6 Capture default is the leak, and a habit-change will not plug it

The prior paper's "change most likely to keep the fix working" is "use `@route^id` when it is not for today." Bare `@route:id` is the *convenient* spelling, it is what Mac Capture completes to, and it is what created 91% of today's queued links on their created date (prior paper's measurement; this run did not re-count created-vs-first-ledger, and has no reason to doubt it). Asking a tired evening capture to pick the inconvenient spelling is the same class of failure as asking a morning review of 70 items to select.

The default has to stop landing work on the closed list. The convenient spelling should write a task *with a horizon* and leave the ledger alone unless the day is under cap *and* the operator asked for today (`#THEME`, `=<X>`, or an explicit today marker).

### 3.7 Theme bundles vs individual tasks

The valuable planning unit on the daily note is the **named bundle** (GOALS = three tasks from three files). A per-task horizon does not by itself remember that those three are one bet. The prior paper preserved bundles by copying them intact into `roadmap.md`. That is the one thing copy-paste got right.

v1 does **not** need a `[theme:: GOALS]` field. Morning pick is "look at the NOW chip, pull one or two co-related tasks onto a named Pomodoro." Project file plus human grouping is enough when NOW is ~15 items. A `theme` field is a v2 if co-scheduling across files stays painful.

### 3.8 Highlight-above-heading was already doubted

Bryan's own highlight on the prior PDF: the `highlight::` line above `## Pomodoros` is marked *I'm not sure about this.* Putting a Dataview inline field in the daily *body* also risks someone later wrapping it in a list and confusing parsers. **Frontmatter `highlight:`** (or `highlight_task: "[[sase_goals#^epic-roadmap]]"`) is queryable, ignored by ledger tooling, and stays out of the section the plugins own.

### 3.9 Status coupling was described, then left in place

If Next continues to mean "linked from an open Pomodoro," then a cap on open Pomodoros is a cap on how many tasks may be Next. That is correct for a closed list — **if capture and Ctrl+Shift+Enter cannot exceed the cap.** The prior paper left both doors open and hoped the morning pick would push overflow into `roadmap.md` after the fact.

Hooks should also **stop promoting** a task that is over the cap or marked `[horizon:: later]`, and they should **make the violation visible in the daily note** (badge + warning callout). Visibility is the piece the current 15-minute cron can ship first.

### 3.10 Weekly review of 25–50 minutes on top of an already-failing `gtd_daily`

`gtd.md` already caps weekly review at **four pomodoros**. September GTD is 21% of tracked time. Adding a long weekly on the same file that cannot keep "plan pomodoros" alive is extra weight. The weekly job is: re-rank `[horizon::]`, cap NOW, glance at created vs closed. That can be one repeating task, 25 minutes, on a Saturday/Sunday — not three new bullets on the weekday list.

### 3.11 Priority / randomize already encode a time window

`p:<N>` and Ctrl+Shift+P roll `[scheduled::]` in priority windows and can Block a task. Using priority *as* Now/Next/Later would fight `bob randomize` and the existing P0–P3 schedule log. Horizon is a separate field.

### 3.12 ProdPad Now/Next/Later is for initiatives, not a dump of features

Janna Bastow's format groups **problems / initiatives** by confidence horizon; a board of feature cards in three columns is a feature board wearing the costume ([ProdPad glossary](https://www.prodpad.com/glossary/now-next-later-roadmap/), [invention note](https://www.prodpad.com/blog/invented-now-next-later-roadmap/)). For this vault that means:

- `roadmap.base` rows = **project notes** (the initiative / structure-note layer `^better-roadmaps` wants).
- `[horizon::]` on tasks = execution inventory inside those bets.
- Daily Pomodoros = today's closed list, which is a Kanban *today* column, not a product roadmap.

Copying 22 named buckets into `roadmap.md#Now` would be the costume.

---

## 4. Options (kept short)

| Option | Verdict |
| --- | --- |
| A. Restart the daily review on the 70-item open section | The review is the thing that lapsed. |
| B. Prior paper as written: capped ledger + copied `roadmap.md` + capture habit, tooling later | Diagnosis yes; storage duplicates; habit is the weak link. |
| C. Note-per-task Bases (TaskNotes / Task Base) | Fights the whole `#task` + block-id + capture + hooks stack. |
| D. Revive `now.md` / `soon.md` | Stale zorg dumps. |
| E. `## Roadmap` section in the daily note | Breaks promotion and/or the heading total. |
| **F. Horizon field on tasks + dash chips + `roadmap.base` on projects + cap enforced in capture/hooks/keymaps + no migrate** | **Recommended.** Inventory stays on the objects that already exist. Today stays a closed list. The machines that currently fill today are the machines that stop. |

---

## 5. Recommended solution

### 5.1 The rule

> **The daily note holds the record of what you did and a closed list of what you will do today. The inventory lives on the tasks (`[horizon:: now|next|later]`) and on project notes (`horizon` frontmatter), rendered from `dash.md` and `roadmap.base`. Capture, keymaps, and `task-status-hooks` keep today under cap. Nothing is copied forward.**

Three layers, one source of truth each:

| Layer | Object | Where it lives | Cap |
| --- | --- | --- | --- |
| Today (closed list) | Named open Pomodoros + their task links | `## Pomodoros` in the daily note | ≤ 3 themes + GTD; ≤ ~10 links; one open *timed* entry (already enforced) |
| Execution inventory | `#task` lines | `[horizon:: now\|next\|later]` on the task | NOW ≈ week's bets, ~15 tasks; SOON uncapped but pruned weekly; LATER is the junk drawer with a weekly age prune |
| Initiative roadmap | Project notes | `horizon` in frontmatter, `roadmap.base` views | NOW ≈ 5 projects / structure notes |

Next-the-status (`[*]`) means **on today's closed list**. Horizon-next means **soon, not today**. The dashboard says SOON for the latter.

### 5.2 Daily note shape

Keep the template almost as it is (`_templates/daily.md`): one seeded GTD placeholder. Add frontmatter, not a body highlight line:

```yaml
highlight: "Decide the goals-epic phase order and file its beads"
highlight_task: "[[sase_goals#^epic-roadmap]]"
```

During the day the open section looks like this — and *only* like this:

```markdown
## Pomodoros (`= …unchanged formula…`)
<!-- bob:pomodoro-cap:v1 -->
`🎯 1/4 themes` · `10/10 links` · `210m done`

- [x] (**0735-0800** [t:: 25m]) — GTD
	- 🍅 [[#^gtd]]
- [ ] (**0830-0920** [t:: 50m]) — GOALS
	- [[sase_goals#^epic-roadmap]]
	- [[bob#^better-roadmaps]]
- [ ] () — DECKS
	- [[sase#^card-blocks]]
	- [[sase#^p-key-for-decks]]
- [ ] () — GTD
	- [[#^gtd]]
```

Rules for the open part:

- GTD is standing. It does not count against the two extra themes, and it stays in the template.
- The highlight's theme is one of the three. Work it first when the day is calm.
- Urgent reactive work (`SHIT`, `RELAUNCH`, `RESTARTS`) gets an honestly named *timed* block **when it happens**. It does not need a pre-staged bucket. September already spent 14.5% of minutes here; a pre-staged OPS theme would just become another carried bucket.
- Do not copy the same links into every consecutive block. Continue the theme; 🍅 and a one-line note show motion.
- Inventory names (`LATER`, `NEW FEATURES`, `MISC`, `QUEUE`, second `SASE`) are illegal on the daily note. Hooks should warn if they appear.

### 5.3 `dash.md`: chips, then Bases

Above the existing WIP / NEXT / READY widget, add three chips in the same DataviewJS pattern:

| Chip | Count | Jump target |
| --- | --- | --- |
| NOW | `#task` with `[horizon:: now]`, not done, not `#hide`, scheduled today or earlier | `dash#NOW` |
| SOON | `[horizon:: next]` | `dash#SOON` |
| LATER | `[horizon:: later]` | `dash#LATER` |

Implementation: extend the existing `plugin.getTasks()` pass (or Dataview `dv.pages().file.tasks`) by parsing `[horizon:: …]` / `(horizon:: …)` the same way `task_fields.rs` already does. Color NOW with the in-progress yellow, SOON with a distinct accent (not the Next-status green), LATER muted.

Sections below the current READY query:

```tasks
not done
description includes [horizon:: now]
```

…and the same for `next` / `later`. (Tasks plugin has no first-class custom field; `description includes` is enough for v1. Dataview `TASK WHERE horizon = "now"` is the prettier long-term query once `bob query` / the live plugin are the viewer.)

Keep `![[projects.base]]`. Add `![[roadmap.base]]` under it (or replace the "Active & Waiting" mental slot for *bets*).

### 5.4 `roadmap.base` (projects, not checkboxes)

Mirror `projects.base`:

```yaml
filters:
  and:
    - note.type == link("project")
    - file.inFolder("_templates") == false
formulas:
  horizon_badge: if(horizon = "now", "🟢 NOW", if(horizon = "next", "🔵 SOON", if(horizon = "later", "⚪ LATER", "—")))
views:
  - type: table
    name: 🗺 Horizons
    groupBy:
      property: horizon
    # …
  - type: table
    name: 🟢 NOW
    filters:
      and:
        - horizon == "now"
```

If the installer is on a Bases version with kanban, a kanban grouped by `horizon` is the ProdPad-shaped view. Rows stay files. Editing `horizon` in the table *is* the weekly re-rank for projects.

`sase_blog_blockers`-style structure notes get `horizon: now` when they are a current bet, and they drop off NOW when cancelled or done — which that note already is (`status: canceled`).

A markdown `roadmap.md` is optional and, if created, is a **query shell** only:

```markdown
# Roadmap
![[roadmap.base]]
## NOW
```tasks
not done
description includes [horizon:: now]
```
```

It must not grow hand-maintained `[[note#^id]]` children. If that starts happening, delete the markdown file and keep dash + the `.base`.

### 5.5 Automations to implement (this is the actual change)

Ship in this order. Week-one trial should include steps 1–3. Steps 4–6 can land during the same two weeks as they fit.

#### 1. `bob task-status-hooks`: cap badge, visible violation, stop-migrate

Already on a 15-minute cron (`docs/vault-git-sync.md`). Extend it:

- Count open named entries and unique open task links under `## Pomodoros` for the current daily note.
- Write a managed block, same style as `<!-- bob:task-status-badges:v1 -->`:

```markdown
<!-- bob:pomodoro-cap:v1 -->
`🎯 3/4 themes` · `8/10 links`
```

- When `themes > 4` (GTD + 3) or `links > 10`, also write a live callout the daily note cannot ignore:

```markdown
> [!warning] Daily cap exceeded (22 themes / 74 links). Target is ≤4 themes / ≤10 links. Capture will refuse new ledger links until this is under cap.
```

  Use `> [!error]` if over 2× cap. CSS in `task-statuses.css` (or a new snippet) can tint the Pomodoros heading when the marker is present.

- **Stop-migrate:** on the first hooks run of a new local date (or an explicit `bob task-status-hooks --close-day` at shutdown), delete leftover *open untimed* Pomodoro entries from *yesterday's* daily note. Keep completed entries. Do not copy children anywhere. The tasks remain in their project notes with whatever horizon they have; if they had none, hooks backfill `[horizon:: now]` on any task that was linked from those deleted entries before deletion (so the NOW chip inherits the old pile once, then you prune weekly). After that one-time backfill, the copier is gone.

- **Do not promote** a reference to Next if it is `[horizon:: later]`. Warn. Optionally strip that bullet from the open ledger (same family as "future scheduled prunes from today's open Pomodoros," which Ctrl+Shift+P already does).

- **Warn** on illegal inventory names (`LATER`, `NEW FEATURES`, `MISC`, `QUEUE` as Pomodoro names) so the daily note cannot quietly become a backlog again.

- Leave Next meaning "on today's open ledger." Do **not** treat `horizon:: now` as a Next source. That would re-inflate the green chip.

Human output already prints `N open pomodoros · N direct references`. Surface the cap in that line too (`22 open pomodoros (cap 4) · 74 direct references (cap 10)`) so the cron log and a dry-run are enough to see violations without opening Obsidian.

#### 2. Capture grammar: `h:now` / `h:next` / `h:later`, and a cap guard

Add a terminal marker next to `s:<N>` and `p:<N>` in `capture_language/markers.rs`:

| Token | Writes | Ledger? |
| --- | --- | --- |
| `h:now` | `[horizon:: now]` | Only if combined with `#THEME` / `=<X>` / an explicit today operator, **and** under cap |
| `h:next` | `[horizon:: next]` | Never |
| `h:later` | `[horizon:: later]` | Never |
| default (no `h:`) | `[horizon:: next]` on **new** tasks | Never, unless an explicit today operator is present |

**Cap guard for today-operators** (`@route:id`, `@route:id#THEME`, `#name` creating a new named placeholder, Ctrl+Shift+Enter equivalent via capture):

- If open named entries are already 4 and the `#THEME` does not match an existing open name → **error**, suggest `h:now`.
- If unique open links are already 10 → **error**, write the task with `h:now` and no ledger link, print "day is full; task landed on NOW chip."
- `#name` that would create a 5th theme is the specific leak (`NEW FEATURES`, second `SASE`, `LATER`). Refuse creation; require an existing open name or `h:`.

Keep `@route^id` as Ready + optional `h:`. Keep `p:` / `s:` orthogonal; combining `h:later` with `p:3` is valid (someday, low priority, randomized schedule).

`=x` / `+N` / `++N` stay session operators and do not touch horizon.

This is a **breaking default** for `@route:id` (today it always links). Document it loudly in `docs/capture.md`. It is the leak. A compatibility flag `BOB_CAPTURE_LEDGER_DEFAULT=today` can cover the two-week trial if the new default feels too sharp; the recommended trial runs **with** the guard on.

#### 3. Bob Mac Capture

The app already classifies schedule and priority tokens and shows pomodoro-start / close / link presentations. For this design:

- Add `CaptureSemanticCategory.horizon` (new color, same family as `.priority`).
- Complete `h:` to `h:now` / `h:next` / `h:later`.
- Preview footer: `today 3/4 · 8/10` from a tiny `bob capture-parse` / pomodoro status JSON field (hooks or `bob pomodoro --json` can expose counts).
- When a draft would exceed cap, the preview states the rewrite (`#THEME` dropped, `h:now` applied) **before** Return, matching how other capture errors already become notices.

No new hotkey on the Mac side until the grammar exists; the menu bar is a client of `bob capture-parse`.

#### 4. Obsidian keymaps (`bob-plugins`)

| Chord | Change |
| --- | --- |
| **Ctrl+Shift+P** | Add **Horizon** to the existing scheduled / dependency / priority picker (`now` / `next` / `later`). Choosing `later` also prunes today's open-ledger links (same path as a future `scheduled` date). Choosing `now` does **not** add a ledger link; it only sets the field. Adding to today stays Ctrl+Shift+Enter. |
| **Ctrl+Shift+Enter** | If the day is at cap, **notice and refuse** the new link (or retarget an existing open theme if the user is already on one). Set `[horizon:: now]` so the task still shows on the NOW chip. |
| **Ctrl+Shift+M** on a Pomodoro sub-bullet | Already moves bullets between open Pomodoros / new named ones. At cap, creating a *new* named destination must refuse the same way capture does. |
| CSS (`task-statuses.css` or `dataview-properties.css`) | Style `[horizon:: later]` muted; style the cap callout. Optional: a `cm-line` decoration when the daily note's open count is over cap, driven by the HTML comment marker. |

Do not add a fourth status symbol. Horizon is a field, not `[n]` / `[s]` / `[l]`.

#### 5. `bob pomodoro` / tmux

Once hooks (or the pomodoro parser) expose counts, append `3/4 · 8/10` to the tmux segment. Over cap: invert/warn in the status line. This is the glanceable version of the daily-note badge for when Obsidian is not focused.

#### 6. Morning pick and weekly, shrunk

Replace three `gtd_daily` items (migrate, review READY, review WIP+NEXT / plan Pomodoros) with one:

```markdown
- [ ] #task Pick today: open [[dash]]; pull ≤2 NOW themes onto today's Pomodoros; set frontmatter highlight  [repeat:: every day when done]
```

Standing contingency (Parke, Weinhardt, Brodsky, Tangirala & DeVoe 2018): *if the highlight is blocked on agents, work the next open theme or GTD for one block, then reassess. Do not pull a fourth theme.*

Weekly, one task, `[repeat:: every week on Sat]` (or Sunday), 25 minutes:

1. Re-rank `[horizon::]` so NOW is the week's bets (~15 tasks, ~5 project notes in `roadmap.base`).
2. Anything with no 🍅 in three weeks and still `now` → `next` or `later` (or cancel).
3. Glance at created vs closed for `sase*` / `bob*` (intake is still the deeper problem; a research-reading budget belongs here).

Evening optional: set tomorrow's `highlight` frontmatter. That is vault idea `^z-241003-0b`, shrunk to one field, and it is the Ivy Lee night-before list without a six-item fantasy.

### 5.6 One-time transition (~30–45 minutes of human time, plus the backfill)

1. **Stop migrating tonight.** Let hooks' first new-day run (step 1) backfill `[horizon:: now]` onto tasks that were in yesterday's open entries, then delete those open entries.
2. **Triage the NOW chip once.** Most of today's 74 links will land on NOW. Demote the obvious later work to `h:later` / Ctrl+Shift+P Horizon with a counted `N<Ctrl+Shift+P>` if needed. Aim for ≤15 on NOW before tomorrow's pick.
3. **Set `horizon: now` on the two or three project notes that actually are this week's bets** (`sase.md`, `bob.md`, `sase_goals.md` are the likely ones). Create `roadmap.base`. Embed it on `dash.md`.
4. **Edit `_templates/daily.md`:** keep GTD only; add empty `highlight` / `highlight_task` frontmatter keys.
5. **Expect Next/In Progress to collapse** toward the closed list. The 50 + 25 dash counts should fall toward "today's 10 links + a couple of in-progress leftovers." That is the point of the green/yellow chips meaning something again.

### 5.7 Two-week trial (2026-09-30 → 2026-10-13)

| Signal | Today | Target |
| --- | --- | --- |
| Peak open named entries (mid-day git, not EOD) | 22 (today); 19 on 2026-09-25 19:27 | **≤ 4** |
| Peak open task links mid-day | 74; 60 on 2026-09-25 19:27 | **≤ ~10** |
| Morning pick completed | plan-pomodoros last done 2026-09-09 | **≥ 10 of 14** |
| Dash IN_PROGRESS + Next | 75 | **≤ ~15** |
| Capture refusals / cap notices | n/a | **seen and obeyed** (if zero refusals *and* cap exceeded, the guard is not wired) |
| NOW chip size after weekly | n/a (field does not exist yet) | **≤ ~15** after the first Saturday |

Keep the change if the next block is usually obvious and the daily note no longer grows a LATER bucket. If the highlight in frontmatter is unused, drop the field and keep the cap. If `roadmap.base` is ignored because project `horizon` is stale, drop the `.base` and keep task chips — task horizon is the load-bearing inventory.

### 5.8 Risks

- **NOW chip becomes the new pile.** Weekly cap + hooks warning when NOW > 15 (a second badge on `dash.md`, even a static DataviewJS "NOW 37 (cap 15)" in red) is the defense. Intake in September is still ~2 created per 1 closed on sase/bob (prior paper); a daily cap cannot absorb that without a weekly prune.
- **Breaking `@route:id`.** Document it; Mac preview makes it visible; compatibility env var exists for a week if needed.
- **Horizon / Next naming.** Chips say SOON. Field values stay `next`. Mention this once in `docs/capture.md` and the picker labels.
- **One-time backfill dumps 74 tasks onto NOW.** Budget the first Saturday for that triage. Do not skip it.
- **Hooks write a callout into the daily note** while the editor is open. They already do guarded writes and retries for this reason. Keep the cap block a small, idempotent managed region (like the badge marker), not a rewrite of the whole ledger.

### 5.9 Deliberately not in v1

- `[theme:: GOALS]` on tasks.
- Treating `roadmap.base` or `horizon:: now` as a Next source for hooks.
- Strict 25/5, calendar overlay, second time tracker, renaming `## Pomodoros`.
- Note-per-task migration.
- A markdown bucket list.
- Overloading `p:` / `priority`.
- Highlight as a body `highlight::` line.

---

## 6. Why this is simpler day to day

Daily motion after the tools land:

1. Open the daily note (GTD placeholder already there) and `dash`.
2. Pull at most two NOW themes onto named Pomodoros (or start GTD).
3. Work. `se` / `=` / `+N` / `=x` unchanged.
4. New ideas go through capture as `h:next` / `h:later` (the default). They show on SOON/LATER, not on today.
5. Go to bed. Yesterday's open placeholders disappear. No migrate.

That is fewer moving parts than "cut yesterday into `roadmap.md#Now`, then pull back, then remember to use `^` instead of `:`." The extra structure (one inline field, one `.base`, one badge) is paid for by deleting the copier.

---

## 7. Implementation sketch (for a later plan, not this turn)

| Piece | Repo |
| --- | --- |
| `h:` marker, cap guard, default horizon on new tasks | `bob-cli` `capture_language` + `docs/capture.md` |
| Cap badge, callout, stop-migrate, later-horizon prune, illegal names | `bob-cli` `task_status_hooks` |
| Counts on `bob pomodoro` / tmux | `bob-cli` `pomodoro.rs`, `scripts/tmux_bob_pomodoro` |
| Horizon in Ctrl+Shift+P; cap on Ctrl+Shift+Enter / Ctrl+Shift+M new names | `bob-plugins` `bob-navigation-hotkeys`, `block-id-prompt` |
| Palette, completion, preview footer | `bob-mac-capture` `CaptureEditorPalette`, parse presentations |
| `roadmap.base`, dash chips, daily template frontmatter, CSS | vault (`~/bob`), via the usual plugins-sync / manual vault edit |
| `gtd_daily` swap | vault |

Coordinate capture-contract changes across `bob-cli` and `bob-mac-capture` as that linked repo's description already requires.

---

## Sources

**Local (read-only this run):**

- `~/bob/2026/202609{01..29}.md` and git history of `2026/20260925.md` (mid-day `757056a0`)
- `~/bob/_templates/daily.md`, `gtd_daily.md`, `gtd.md`, `gtd_ideas.md`
- `~/bob/dash.md`, `projects.base`, `refs.base`, `eat.base`
- `~/bob/bob.md` (`^better-roadmaps`, `^pomodoro-ledger-daily-roadmap`)
- `~/bob/now.md`, `soon.md`, `sase_blog_blockers.md`, `pomodoro.md`
- `~/bob/ref/chat/pomodoro_ledger_and_daily_roadmap.md` (highlights, including the doubted highlight line)
- `~/bob/.obsidian/plugins/obsidian-tasks-plugin/data.json` (global filter `#task`, custom statuses)
- `~/bob/.obsidian/snippets/task-statuses.css`, `dataview-properties.css`
- Prior consolidated paper: `sase--research` `202609/pomodoro_ledger_and_daily_roadmap/pomodoro_ledger_and_daily_roadmap.md`
- `bob-cli`: `docs/capture.md`, `docs/task-status-hooks.md`, `docs/vault-git-sync.md`, `src/native/task_fields.rs`, `src/native/capture_language/markers.rs`, `src/native/task_status_hooks/`, `src/native/task_status_groups/emit.rs`
- `bob-plugins`: README (keymap surface), `bob-ledger-tools`, `bob-navigation-hotkeys`, `block-id-prompt`
- `bob-mac-capture`: README, `CaptureEditorPalette.swift`

**Methods:**

1. Cirillo, F. *The Pomodoro Technique* (Activity Inventory / To Do Today / Records). <https://www.pomodorotechnique.com/>
2. Forster, M. *Do It Tomorrow* — closed lists; new work waits until tomorrow except genuine unplanned-urgent. Summary: <https://en.wikipedia.org/wiki/Mark_Forster_(author)>; principles recap: <https://learn.microsoft.com/en-us/archive/blogs/paulcornell/do-it-tomorrow-the-principles>
3. Buehler, R., Griffin, D., & Ross, M. (1994). Exploring the "planning fallacy." *JPSP* 67(3), 366–381.
4. Parke, M. R., Weinhardt, J. M., Brodsky, A., Tangirala, S., & DeVoe, S. E. (2018). When daily planning improves employee performance. *J. Appl. Psych.* 103(3), 300–312. Contingency planning stays useful on high-interruption days.
5. Benson, J., & DeMaria Barry, T. *Personal Kanban* (visualize, limit WIP); Little's Law.
6. Knapp, J., & Zeratsky, J. *Make Time* daily Highlight. <https://maketime.blog/article/choose-a-highlight-to-make-time-every-day/>
7. Bastow, J. Now/Next/Later as confidence horizons for **initiatives**, not a feature dump. <https://www.prodpad.com/glossary/now-next-later-roadmap/> · <https://www.prodpad.com/blog/invented-now-next-later-roadmap/>
8. Obsidian Bases: rows are files, columns are properties. <https://obsidian.md/help/bases> · <https://obsidian.md/help/bases/views>
9. Biwer et al. (2023); Smits, Wenzel & de Bruin (2025); Göksu, Wiradhany & de Bruin (2026) — self-regulated / Flowtime breaks vs strict Pomodoro; no reason to force 25/5 here.
10. Masicampo & Baumeister (2011) — a specific plan for unfinished goals reduces intrusion; a 74-link heap does the opposite.

---

## Recommended solution (summary)

Keep the completed `## Pomodoros` ledger and its toolchain. Treat the open part as a **closed daily list** (≤3 themes + GTD, ≤10 links). Store the inventory as **`[horizon:: now|next|later]` on tasks** and **`horizon` on project notes**, rendered as **NOW / SOON / LATER chips on `dash.md`** plus **`roadmap.base`** (files, not checkboxes). Delete migrate. Default capture writes a horizon and stays off the ledger; `#THEME` / `=<X>` / Ctrl+Shift+Enter may add to today only under cap. `task-status-hooks` (already every 15 minutes) writes a cap badge, a warning callout when the rule is broken, refuses to promote `later` tasks, and drops yesterday's open placeholders. Ctrl+Shift+P gains Horizon; Mac Capture colors and previews `h:`. Trial two weeks against mid-day git counts, not end-of-day cleanliness.
