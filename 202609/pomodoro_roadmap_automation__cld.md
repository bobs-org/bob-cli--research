# Pomodoros, roadmap and automation: let the tools hold the line, not the morning ritual

- **Research date:** 2026-09-29
- **Researcher:** `cld` (one of five independent researchers; the lead will synthesize)
- **Question:** Should Bryan change how he tracks pomodoros, work, time and the day's roadmap in the
  `## Pomodoros` section of his Bob daily notes (e.g. `~/bob/2026/20260929.md`)? Keep it simple, or
  simpler; add complexity only where it pays for itself.
- **Starting point:** the prior consolidated report
  `sase/research:202609/pomodoro_ledger_and_daily_roadmap/pomodoro_ledger_and_daily_roadmap.md`
  ("the prior report"), plus the user's list of its gaps:
  - no automation;
  - no `roadmap.base` / `dash.md` badge option;
  - no review of keymaps, `bob capture` / Bob Mac Capture syntax, or `bob task-status-hooks`.
- **What I examined:**
  - today's daily note, the daily template, `gtd_daily.md`, `dash.md`, and the vault's `.base` files;
  - `bob.md`, `sase.md` and `sase_goals.md`;
  - the zorg-era `now*` / `soon*` / `pomodoro.md` notes;
  - the Obsidian hotkeys and deployed Bob plugin bundles;
  - the `bob-cli` docs (`task-status-hooks.md`, `capture.md`, `projects.md`, `dataview.md`, `README.md`);
  - the in-flight `=x<N>!<M>` epic (`bob-cli-2k`) and its plan;
  - **every git revision** of the daily notes from 2026-08-26 to 2026-09-29, analyzed at theme level (new in
    this report);
  - primary sources on Obsidian Bases, Dataview and Tasks;
  - a few behavioral-science meta-analyses not used before.
- **Not verified:**
  - I could not open the `bob-plugins` or `bob-mac-capture` sources: neither has a local primary clone, so
    `sase repo open` failed. Plugin behavior below comes from the `bob-cli` docs and the deployed bundles in
    `~/bob/.obsidian/plugins/`.
  - The dataviewjs and `.base` snippets are untested sketches.

---

## Bottom line

1. **Keep the ledger. Stop migrating it.**
   - The completed-block log is still the best thing in the system.
   - The chaos comes from the *open* placeholders. Today there are 21 named themes and ~78 links, and every
     morning the "Migrate unfinished Pomodoro tasks" chore copies all of them forward by hand.
   - `bob task-status-hooks` **already** implements the decay the prior report asked for:
     - unlinked Next tasks drop to Ready;
     - stale In Progress area/project tasks drop to Ready after a one-day grace, taken from yesterday's note.
   - The manual migration is the only thing defeating that decay. **Deleting one chore is the single
     highest-value change,** and it costs nothing.
2. **The day really holds about 3 themes, whatever the size of the list.**
   - The median number of *open themes actually worked* per day was **3** in every period: when 12 themes
     were open (late Aug), 15 (mid-Sep) and 22 (last 9 days).
   - The share of open themes that got any block fell from 29% to 13%.
   - 28 of 80 theme names created since 2026-08-26 were never worked, and `GATES` has sat open for 35 days
     without a block.
   - So cap the planned list at **GTD + 3 themes**. That cap matches measured throughput; it isn't an
     aspiration.
3. **Don't build a second or third horizon system.**
   - The vault already has "Next / Later" machinery:
     - P1–P4 priorities roll a future `scheduled` date. The task goes Blocked and resurfaces later.
     - `Ctrl+Shift+P` deferral also **prunes the task's link from today's open Pomodoros**.
     - Project-level `^prj` scheduling hides a whole project.
     - `bob randomize` re-rolls whatever is overdue.
   - The prior report's `roadmap.md` Now/Next/Later would duplicate all of that by hand. So would a
     task-level `[horizon:: …]` field.
   - The piece that is genuinely missing is small: **which ≤5 bets are "Now" this week.**
4. **A `roadmap.base` works, but only at the project level.**
   - Bases rows are still *files only* in Obsidian 1.14.3. There are no task or list-item rows and no inline
     `key:: value` fields.
   - So a Base cannot show tasks tagged Now/Next/Later.
   - It *can* show project notes with a `roadmap: now|next` property. That fits well: most live themes
     already have sub-project notes (`sase_goals`, `sase_decks`, `sase_remote`, `sase_memory` …), and
     `projects.base` / `bob projects sync` already use this file-level pattern.
   - The count/badge belongs in the **existing dataviewjs chip bar** at the top of `dash.md`. Bases cannot
     render a value inline.
5. **Automate the guardrails, not the plan.**
   - The prior report relied on three new habits: a morning pick, a capture habit and a weekly review. The
     planning habit it replaces already lapsed on 2026-09-09.
   - Meta-analyses find intention changes only weakly change behavior. Defaults and visible self-monitoring
     reliably do.
   - So the automation should make violations **visible where you already look**: the daily note, the dash,
     tmux and the capture preview.
   - It should add **drop/defer gestures to the tools you already use**: the `=x` close, `Ctrl+Shift+P` and
     capture.
   - It should **not** silently rewrite the plan from a 15-minute cron.
6. **Recommendation:** a closed daily list plus a project-level Base roadmap plus visible budgets, rolled out in
   phases.
   - **Phase 0** is no-code and takes about 30 minutes.
   - **Phase 1** is five small `bob-cli` changes.
   - **Phase 2** is optional.

   Details are in §9.

---

## 1. What changed since the prior report

- **The queue kept growing.** At peak today (2026-09-29) there were 21 open named placeholders and 78 open
  links. 80 distinct links were queued at some point today.
  - Of those 80 links, **60 point into `sase.md`**. See §3.4 for why that matters for Bases.
  - 50 of the linked tasks are In Progress `[/]` and 25 are Next `[*]`.
- **The prior report's own task is done.** `bob#^pomodoro-ledger-daily-roadmap` was completed at 14:31 today.
  Completing it produced a duplicate struck link in the finished GTD block, which you deleted by hand 18 s
  later. I filed that incidental defect as **`bob-cli-2l`** (see §8).
- **`bob-cli-2k` is in flight.** It adds `=x<N>!<M>`: close the running Pomodoro and choose, by number, which
  Task Links stay in progress (`<N>`) and which are completed (`!<M>`). Phases .1 and .2 have landed. Phases .3
  (wiring), .4 (docs) and .5 (Mac close card) are in progress. That grammar is the natural home for a "drop"
  outcome (§7.2).

---

## 2. Where the prior report fell short

The user named three gaps: automation, Bases, and keymaps/capture/hooks. These are the others I found. Each one
changes the recommendation.

| # | Shortcoming | Why it matters | Where addressed |
|---|---|---|---|
| 1 | **Its fix was three new habits** (morning pick, `@route^id` capture habit, weekly review) | The failure it diagnosed *was* a lapsed habit ("plan daily Pomodoros", last done 09-09). Intention changes of d ≈ 0.66 produce behavior changes of only d ≈ 0.36 (Webb & Sheeran 2006). Defaults average d ≈ 0.68 (Jachimowicz et al. 2019). Visible, recorded progress monitoring improves goal attainment (Harkin et al. 2016). Design for defaults and visibility, not resolve. | §6, §7 |
| 2 | **It missed the existing horizon machinery** | P1–P4 rolls, `Ctrl+Shift+P` defer-and-prune, project `^prj` scheduling and `bob randomize` already implement Next and Later. A hand-kept `roadmap.md` Next/Later would be a third system beside statuses and priorities. | §4, §5 |
| 3 | **It kept a copy step** ("cut yesterday's open entries into `roadmap#Now`") | That is the migration chore pointed at a different file. `task-status-hooks` already decays unpicked work on its own. The simplest fix is to *delete* the copy, not move it. | §6 |
| 4 | **It ignored the vault's history with horizon lists** | Both earlier attempts at hand-kept horizon lists died (see the notes after this table). | §5 |
| 5 | **It measured links, not themes** | The failure unit is the *theme* placeholder that is never closed (created with `#name`, carried daily). Theme-level data gives the cap directly: 3/day, stable (§3). | §3 |
| 6 | **It ignored `=x` carry semantics** | Every close carries every uncompleted link into a new same-named placeholder. `=x<N>` adds "deferred", which is also carried. No outcome says "not today", so a session end can never shrink the day. | §7.2 |
| 7 | **WIP inflation's mechanism went unexplained** | A close starts each worked link (`[/]`), and while the link sits in a carried placeholder the task stays `[/]`. Result: 50 of today's 80 linked tasks are `[/]`. Stop the carry and area/project `[/]` decays after one day's grace. No new rule is needed. | §6 |
| 8 | **It added a `highlight::` field** | Ledger order already encodes priority. `=` starts "the first entry in document order that is open, a placeholder, and untimed", and the `=x` diagnostic calls it "next up". Placing the highlight first needs no new field. | §6 |
| 9 | **Capture was treated as a habit, not a choke point** | 91% of queued links entered on their creation day through `@route:id` / `#name`. Bob Mac Capture already shows vault-aware diagnostics in its preview (e.g. `no running Pomodoro`), so capture can warn at the moment of decision. | §7.2 |
| 10 | **Its trial metrics were counted by hand** | Hand-counted success metrics are themselves a lapsing habit. The budget view (§7.4) and a git-history stats script can measure them automatically. | §9 |
| 11 | **Its roadmap needed a cap nothing enforced** ("≤5 Now") | Without a visible counter the cap is advisory. The dash chip makes it visible (§7.4). | §7.4 |

**The two earlier horizon lists (shortcoming 4):**

- The zorg-era `now_*.md`, `soon_*.md` and `maybe_*.md` horizon notes, and `pomodoro.md`'s "rollover
  pomodoros" with a weekly `@FRESHNESS` review, all stopped being maintained. For example, `now_sase.md` was
  last generated in February.
- `sase_blog_blockers.md`, the structure note cited by `bob#^better-roadmaps`, was cancelled two days after it
  was created.

A new hand-maintained `roadmap.md` needs a forcing function, or it will be the third example.

---

## 3. Fresh measurements (theme-level, from git history)

**Method:**

- I parsed every git revision of each daily note from 2026-08-26 to 2026-09-29, when named themes began: 35
  days and 1,514 revisions. The vault commits every ~15 s through `bob vault-sync`.
- A **theme** is a named open untimed placeholder (`- [ ] () — NAME`) seen in any revision that day.
- It counts as **worked** if a completed block with the same name exists at end of day.
- Link staleness uses days since the last 🍅, or since the link was first queued if it never got one.
- The scripts are ad hoc and live in `/tmp`, so they are not durable. If a trial is run, they would become
  `bob` code (§9).

### 3.1 Throughput is fixed at about 3 themes/day, whatever the list size

| Period | Open themes/day (median) | Open themes actually worked (median) | Distinct themes worked incl. unplanned (median) | Share of open themes worked | Peak open links (median) |
|---|---|---|---|---|---|
| Aug 26 – Sep 9 | 12 | **3** | 4 | 29% | 19 |
| Sep 10 – 20 | 15 | **3** | 3 | 17% | 42 |
| Sep 21 – 29 | 22 | **3** | 4 | 13% | 63 |

Almost doubling the list did not move the number of planned themes worked at all. Everything past about three is
inventory that has to be re-read each day.

### 3.2 Themes are created freely and rarely retired

- **80** distinct theme names appeared as open placeholders. **28 (35%) were never worked**, for example `ACP`,
  `BEADS`, `GATES`, `SCHEDULE`, `WAIT` and `PERF`.
- On today's list, the themes that have gone longest without a completed block of the same name are:
  - `GATES`: 35 days, the whole window;
  - `AUDIT MEMORY`: 30;
  - `LATER`, `QUEUE`, `SCHEDULE`: 20 each;
  - `FAST TESTS`, `SUDO`: 15;
  - `RENAME`, `NEW FEATURES`: 14;
  - `SERVICE`: 13;
  - `CLEANUP`: 12;
  - `TOOL`, `REMOTE`: 11.

  Only `GTD`, `BOB` and `GOALS` were worked today.
- The most-worked block names over the window were:
  - `GTD`: 50 blocks;
  - `REMOTE`: 17;
  - `SHIT`: 15, a reactive block;
  - `MEMORY`: 13;
  - `BOB`: 12;
  - `MEMORY WEBS`: 10;
  - `SASE` and `GOALS`: 10 each.

  Most of the real work maps onto existing project notes.

### 3.3 Links go stale fast

Days since each of today's 80 queued links last got a 🍅:

| ≤ 2 days | 3–6 | 7–13 | ≥ 14 |
|---|---|---|---|
| 14 | 20 | 22 | 24 |

- **46 of 80 (58%) have gone ≥ 7 days without a 🍅.** Ten days ago the figure was 21 of 53.
- A 7-day "stale" rule would flag more than half the queue today. After the change it would flag almost
  nothing, which is what makes it a useful alarm.

### 3.4 Where the linked tasks live

| Note | Links |
|---|---|
| `sase.md` | 60 |
| `bob.md` | 10 |
| `sase_memory.md` | 3 |
| other sub-project notes (`sase_goals`, `sase_remote`, `sase_clean`, `sase_pager`, `sase_agent_history`, `sase_art_links`, the daily itself) | 1 each |

What this means for Bases:

- Three-quarters of the queued tasks sit in one file, so a file-level Base cannot split them into horizons.
- The *themes* map mostly onto sub-project notes that already exist:
  - GOALS → `sase_goals`
  - DECKS → `sase_decks`
  - REMOTE → `sase_remote`
  - MEMORY → `sase_memory`
  - CLEANUP → `sase_clean`
  - FINAL → `sase_final_polish`
  - AUDIT MEMORY → `sase_memory_audit`
  - BOB → `bob`
- The themes with no note (`QUEUE`, `GATES`, `SUDO`, `SCHEDULE`, `FAST TESTS`, `SERVICE`) are almost exactly the
  stale ones.

---

## 4. Can a `roadmap.base` (with a badge on `dash.md`) do this?

### 4.1 What Bases can and cannot do (verified 2026-09-29)

Sources: Obsidian help, the changelog and the forum; links are in the Sources section.

- **Rows are files, never tasks or list items.**
  - The Table view is "a row for each file". The plugin API's `BasesEntry` exposes only `file`.
  - The "Bases: support for tasks" feature request is still open. The Obsidian team's explanation (2025-06-28)
    is that the metadata cache stores only a task's location, and "the actual task details are in the file
    contents, which aren't read by bases".
  - No changelog entry from 1.9.0 through 1.14.3 (2026-09-29) adds task or list-item rows, and the public
    roadmap does not list the feature.
- **Only frontmatter properties plus `file.*`.**
  - There is no `file.tasks`, `file.lists` or body access.
  - Inline `key:: value` fields are not readable.
  - A formula therefore cannot count tasks that carry a marker.
- **Views:** Table, Cards, List, Map, and **Kanban**. Kanban "display[s] files as cards organized into columns
  based on a grouped property". It is in the 1.14 early-access builds, while the public build is 1.13.7. Whether
  dragging a card rewrites the grouped property is not documented.
- **Embedding:** `![[x.base#View]]` embeds one named view. Inside an embed, `this` is the embedding note.
- **Counts:**
  - There is no built-in "Count" summary; use `Filled` on `file.name` or a custom `values.length` summary.
  - The toolbar shows the result count.
  - Nothing renders one Base value *inline*, for example in a heading.
- **Plugins:** `registerBasesView` (1.10+) lets a plugin draw custom views, but the rows are still files.
  - TaskNotes (mature, about 1.8M downloads) makes each task its own note. That would break `bob capture`,
    Task Links, the hooks and Work Logs.
  - Simple Tasks (v0.4.3, 139 downloads) shows the tasks of the files a Base selects. It is too immature.

### 4.2 Options

| Option | How | Verdict |
|---|---|---|
| **A. Task-level horizon in Bases** (`[roadmap:: now]` on task lines) | Not possible natively; Bases can't see list items or inline fields | ✗ |
| **B. Task-level horizon via Dataview/Tasks** (`[roadmap:: now]` or `#now` on tasks, queried in a note) | Works technically. But Tasks stops parsing trailing fields at the first unknown one, so a custom field placed after `[scheduled::]`/`[priority::]` would hide them unless it sits to their left. Bob's writers append fields, and it duplicates Next `[*]` and P-levels. | ✗ (third status system) |
| **C. Hand-kept `roadmap.md`** (prior report) | Now/Next/Later headings holding link lists | ◐ Works, but it is a manual list with the zorg failure mode, and Next/Later duplicate P-levels |
| **D. Project-level `roadmap.base`** | A `roadmap: now\|next` frontmatter property (plus optional `rank`) on project notes. The Base lists bets; tasks stay in their notes. | ✓ **Recommended.** Native, editable in-cell, Kanban-ready, and it composes with `projects.base`, `bob projects sync` and `^prj` scheduling |
| **E. TaskNotes (task per note)** | Converts tasks to files | ✗ Breaks Bob's task-line toolchain |

**Why D is not over-engineering:**

- It adds one property to about 5–15 notes and one `.base` file. The vault already has four Bases, two of them
  embedded in `dash.md`.
- "Later" needs no value. A project with no `roadmap` property is backlog, and a project that should come back
  on a date already has `^prj` priority/scheduling.
- The **badge** is a dataviewjs chip, because the chip bar already exists (§7.4).

**Its one real cost:** tasks for a bet should live in that bet's note. Two-thirds of today's sase work is in
`sase.md`, so either:

- capture new work into the bet note (`@sase_decks^id`, which the capture grammar supports today); or
- move tasks over time. Moving a block by hand breaks existing `[[sase#^id]]` links. `bob move-done-tasks`
  already repairs links when it archives, and `bob.md` already lists "Add new `<ctrl+shift+m>` keymap to move a
  task to another file!" A link-repairing move is the Phase 2 enabler (§9).

Until then, a bet note can carry a short "working set" bullet list of `[[sase#^…]]` links. It is bounded, one
per bet, and deleted when the bet leaves Now.

---

## 5. The minimal model: one home per job

| Job | Home | Status |
|---|---|---|
| Record what happened (time, themes, 🍅, notes) | Completed entries in `## Pomodoros` | **Keep as is** |
| Today's plan (a closed list) | Open placeholders in `## Pomodoros`: GTD + ≤ 3 themes. The first placeholder is the highlight. | **Change: cap it, no migration** |
| This week's bets | `roadmap: now` (≤ 5, ranked) on project notes, shown by `roadmap.base` | **New (small)** |
| Shortlist after that | `roadmap: next` (≤ ~10) | New (optional) |
| Backlog | Ready tasks in area/project notes | Keep |
| Later / resurface on a date | P1–P4 priority rolls, `^prj` scheduling, `bob randomize` | **Keep, and use as the defer gesture** |
| Statuses | `task-status-hooks` (Next = linked today; `[/]` decays) | Keep; stop overriding it by migrating |

The whole process fits on an index card:

> **Today is closed:** GTD + at most 3 themes, the first one being the highlight. Nothing is copied forward.
> Leftovers stay in yesterday's note and decay on their own.
> **This week is ≤ 5 bets** in `roadmap.base`.
> **Everything else is backlog or a P-level.**

---

## 6. The process

**Morning (≤ 5 min; replaces three `gtd_daily` chores).**

1. From the daily note, press `Ctrl+,` (alt file → `dash`). The Roadmap "Now" view is the first section.
2. Pick ≤ 3 themes, normally one per Now bet. For each, link 1–4 tasks:
   - in Bob Mac Capture, a batch draft of `@route:id#theme` lines (`@route:id` links an existing task; the `^`
     spelling only completes In Progress/Next tasks);
   - or `Ctrl+Shift+Enter` on the task line in Obsidian.
3. Put the highlight first; `=` will start it.
4. Yesterday's open placeholders are **not** copied.
   - To continue one, re-link its tasks the same way. They are still `[/]` today, thanks to the one-day
     recent-activity grace, so the `^` picker lists them first.
   - Anything not picked decays automatically:
     - Next → Ready on the next hooks run;
     - area/project `[/]` → Ready the day after.
   - Nothing is lost. The task is still in its note, and yesterday's ledger still shows what was planned.

**During the day.**

- `=` starts the next placeholder.
- `=x`, or `=x<N>!<M>` once it lands, closes the session.
- A link you won't finish today goes one of three ways:
  - **drop** it: delete the bullet, or use `~<K>` in the close once added (§7.2);
  - **defer** it: `Ctrl+Shift+P` → P1/P2, which also prunes it from the ledger;
  - leave it, and it simply won't be carried tomorrow.
- **Reactive work** (`SHIT`, `FIXES`, `RELAUNCH`) gets its own block *when it happens*. It doesn't count
  against the cap, because the cap applies to *future* placeholders.
- **New ideas:** capture into the bet's or area's note (`@route^id`, or plain `@route`). Use `@route:id` only
  when it belongs to one of today's themes.

**Weekly (Monday, 25–40 min; one recurring task).**

1. Re-rank `roadmap: now` (≤ 5) and `next` in `roadmap.base`. Cells are editable in the table view.
2. Clear anything flagged stale: 💤 links, and Now bets with no 🍅 in 7 days.
3. Run `bob randomize --dry-run`, then apply.
4. Review READY (moved here from the daily list).
5. Glance at hours per bet and at created vs. closed. Intake ran at about 2:1 in September (prior report), so
   the weekly prune is not optional.

**`gtd_daily.md` edits.**

- Delete "Migrate unfinished Pomodoro tasks…", "Review READY tasks" and "Review WIP + NEXT … plan daily
  Pomodoros".
- Add one line: `Pick today: ≤3 themes from [[dash#Roadmap|Now]] (highlight first)`.
- Add a weekly `[repeat:: every week on Monday when done]` review task.

---

## 7. Automation catalog

Each item has a verdict, a cost (S/M/L) and a phase. The rule of thumb:

- **visibility and gestures:** automate;
- **structural cleanup that loses nothing:** automate (the hooks already do);
- **removing or deferring the user's plan:** only through an explicit command or gesture, with a dry-run.

### 7.1 `bob task-status-hooks`: can it automate cleanup or flag violations?

**What it already does, and should keep doing** (every 15 min on the Mac, `:10/:25/:40/:55`):

- de-duplicates links across open Pomodoros;
- removes canceled-task bullets;
- retires completed links (`~~[[…]]~~`) and repairs 🍅;
- deletes childless placeholders;
- promotes linked tasks to Next;
- clears unlinked Next;
- rolls back stale area/project `[/]`;
- derives Blocked.

This *is* automated cleanup. Once migration stops, it also becomes the decay mechanism.

| Proposal | Verdict | Cost | Phase |
|---|---|---|---|
| **H1. Read-only `ledger_budget` and `stale_links` in JSON and human output.** Open future placeholders vs. cap, open links vs. cap, links with no 🍅 in `stale_days`. This needs a lookback over N previous dailies; today it reads only one. | ✓ The cheapest source of truth for tmux, capture and the Mac app; no vault writes | S–M | 1 |
| **H2. Machine-owned budget row under `## Pomodoros`** (like `<!-- bob:task-status-badges:v1 -->` in project notes), e.g. `` `🎯 3/3 themes` · `🔗 9/10 links` · `💤 0 stale` `` | ◐ Visible and idempotent, and it follows an existing pattern. But it is a 15-min-stale snapshot and yet another machine region in a hand-edited note. Every ledger parser (`bob`, block-id-prompt, bob-ledger-tools, task-status-cycler) must be shown to ignore a non-list line before the first entry. Prefer the live view in §7.4; build this only if that view proves unreliable. | M | 2 |
| **H3. 💤 marker on stale links** (machine-owned like 🍅) | ◐ The clearest in-place signal. It changes the Task Link body contract, though: every `strip_pomodoro_markers` equivalent across both repos must strip 💤 too. Worth it only if stale links keep reappearing after Phase 0. | M–L | 2 |
| **H4. Auto-defer or remove stale links or excess themes from cron** | ✗ It would silently rewrite the plan you are looking at. It would race unsaved buffers, which the hooks docs admit they cannot observe. And the Next→Ready decay already makes unpicked work harmless. | — | never |
| **H5. Explicit stale-link deferral** (`bob randomize --stale-ledger 7 --priority 2`, or `bob pomodoro prune`) with `--dry-run`: assign the P-level, roll the date, write a `🎲`/`💤` Schedule Log reason, and prune from the ledger (the same semantics as `Ctrl+Shift+P`) | ✓ Reuses randomize's planner, seed, Schedule Log and lock; one command for the weekly review | M | 2 |

### 7.2 `bob capture` grammar and Bob Mac Capture

**Where it gets decided.** 91% of queued links came in through `:`-capture on the day the task was created, and
`#name` minted 80 theme names. Capture is where "is this for today?" gets decided.

**Where warnings can surface.**

- `capture-parse` is purely lexical and never reads the vault, so it can't warn about a budget.
- `bob capture` (real and `--dry-run`) and the vault-aware completion path can. That path already puts a
  vault-derived diagnostic (`no running Pomodoro`) into the Mac preview.
- Mac capture delegates grammar to `bob`, so a new diagnostic appears in the preview without new app grammar.

| Proposal | Semantics | Verdict | Cost | Phase |
|---|---|---|---|---|
| **C1. Budget guard on new future placeholders** | When `#name` would *create* a named future Pomodoro, or implicit linking would add a link, beyond the configured caps: warn (`ledger_over_budget`, with counts) in `bob capture` output/JSON and in the Mac preview. An optional `strict: true` makes creating a new theme an error with the hint "capture to `@route^id`, defer with `p:1`, or start it now with `=`". Starting a session (`=`, `#name=`) is never blocked, because reactive blocks are legitimate. | ✓ Puts the "closed list" rule at the moment of choice. It is a default change, not a habit change. | S–M | 1 |
| **C2. A drop list for the `=x` close selection** | `=x[<N>][!<M>][~<K>]`: links in `<K>` are **removed from today's ledger** (not carried, not started). The hooks then demote them. Example: `=x1!3~4,5`. Today, every outcome except "complete" carries the link forward. | ✓ The missing fourth outcome; small if done as a follow-up to `bob-cli-2k` (same lexer, numbering and Mac close card) | S–M | 1 |
| **C3. Pull a theme from yesterday by name** | Whole item `<name[=X]`: move yesterday's open placeholder `NAME`, with its children, into today (or start it with `=X`). Completion lists yesterday's open placeholders. It turns the migration's "copy all" into "pull one, on purpose". | ◐ Nice ergonomics. Relinking with `^route:id#name` already works, and a leading `<` needs a collision check. Build only if relinking feels slow. | M | 2 |
| **C4. Show the implicit destination** | With no running session, bare `@route:id` links under the *first open entry*. In a short ledger that is the highlight, or the template's seeded `GTD` placeholder, which is first. The preview should say "→ under GOALS (next up)". | ✓ Prevents silent pile-ups on the highlight | S | 1 |
| **C5. `r:now` / `r:next` token on project-note creation** (`@sase^queue+ r:now`) | Writes `roadmap:` into the new project note's frontmatter | ◐ Convenient but rare; the Base cell edit is enough | S | 2 |

The existing gestures already cover the rest:

- `@route^id` captures to the backlog;
- `p:<N>` captures with a horizon;
- `@route+id!` toggles a task in or out of today;
- `=` / `=x` / `+N` / `++N` drive the session lifecycle.

No new "horizon" syntax is needed.

### 7.3 Obsidian keymaps and plugins

| Proposal | Current state | Verdict | Cost | Phase |
|---|---|---|---|---|
| **K1. `Ctrl+Shift+P` from a ledger link line.** Resolve the Task Link under the cursor to its task. Counted `N<Ctrl+Shift+P>` → P1/P2 defers N linked tasks at once, straight from the daily note. | The picker works on task lines and already prunes today's links. I could not verify whether it resolves a link line (plugin source unavailable). | ✓ Makes the weekly prune, and any in-day triage, a few keystrokes where the problem is visible | M | 1–2 |
| **K2. Budget-aware `Ctrl+Shift+Enter`** (block-id-prompt "Toggle task Pomodoro link") | Inserts under the current/first open entry | ✓ Show a red chip in the Notice when the day is over its link cap. Optionally, a counted variant opens the existing `Ctrl+Shift+M` Pomodoro picker to choose the theme. | S | 1–2 |
| **K3. `roadmap` row in the `Ctrl+Shift+P` picker** on a `^prj` task, writing project frontmatter the same way `scheduled`/`priority` do | Doesn't exist | ◐ Base table cells (and Metadata Menu, already installed) edit properties with no code | S | 2 |
| **K4. Move a task to another file with link repair** (already on `bob.md` Future Work) | Doesn't exist; `move-done-tasks` has link-repair code | ✓ The enabler for moving bet tasks out of `sase.md` | M–L | 2 |
| **K5. "Pull this placeholder into today"** on a previous daily note (the Obsidian twin of C3) | `N<Ctrl+Shift+M>` moves sub-bullets within a note | ◐ Same case as C3 | M | 2 |
| `Ctrl+,` (alt file → dash), `Ctrl+Shift+J/K` (jump open tasks) | Exist | Use as is: dash with the roadmap is one key from the daily note | — | 0 |

### 7.4 Templates, Dataview and the dash badge (Phase 0, no Rust)

**V1. A live ledger budget in every daily note.**

- Add a small `dataviewjs` block to `_templates/daily.md` **above** `## Pomodoros`, so no ledger parser sees
  it.
- The block calls a shared view file. Dataview's `dv.view()` loads `_meta/views/ledger_budget.js`. Sketch,
  untested:

```js
// _meta/views/ledger_budget.js — call: await dv.view("_meta/views/ledger_budget", {file: optionalPath})
const CAP_THEMES = 3, CAP_LINKS = 10;
const page = input?.file ? dv.page(input.file) : dv.current();
const top = page.file.tasks.where(t => !t.parent && String(t.section?.subpath ?? "").startsWith("Pomodoros"));
const future = top.where(t => t.status === " " && /^\(\)\s*—\s*(?!GTD\b)/.test(t.text));
const links = top.where(t => t.status === " ")
  .flatMap(t => t.children)
  .where(c => /\[\[[^\]]*#\^/.test(c.text) && !c.text.includes("~~")).length;
const over = future.length > CAP_THEMES || links > CAP_LINKS;
dv.paragraph(`${over ? "🔴" : "🟢"} **Plan** ${future.length}/${CAP_THEMES} themes · ${links}/${CAP_LINKS} links`);
```

- The template block is just
  ```` ```dataviewjs\nawait dv.view("_meta/views/ledger_budget")\n``` ````.
- It is live, costs one line per daily note, and is tunable in one file. It is the in-place alarm the zorg
  horizon lists never had.
- Staleness needs history. It can be added here by walking the last 14 daily pages' completed Pomodoro children,
  or it can come from H1.

**V2. The dash badge.**

- Extend the existing chip bar at the top of `dash.md` with:
  - `NOW n/5`: projects with `roadmap: "now"`, via `dv.pages()` on the `type`/`roadmap` frontmatter;
  - `TODAY k/3`: the same computation as V1 against today's file.
- Chips go red over cap, and clicking NOW opens `roadmap.base`.
- The existing WIP chip (47 today) should fall on its own once migration stops. That is a free success signal.

**V3. A `## Roadmap` section first in `dash.md`**, embedding `![[roadmap.base#🎯 Now]]` above `## Tasks`.

**V4. `roadmap.base`.** Sketch, untested; it follows the conventions of the existing `projects.base`.

```yaml
filters:
  and:
    - note.type == link("project")
    - file.inFolder("_templates") == false
    - status.containsAny("wip", "waiting")
formulas:
  title_link: if(note.title, file.asLink(note.title), file.asLink())
  rank_value: if(rank, rank, 99)
properties:
  formula.title_link:
    displayName: Bet
  note.roadmap:
    displayName: Horizon
views:
  - type: table
    name: 🎯 Now
    filters:
      and:
        - roadmap == "now"
    order: [formula.title_link, rank, open_task_count, parent]
    sort:
      - property: formula.rank_value
        direction: ASC
  - type: table
    name: 🗺️ Roadmap
    filters:
      or:
        - roadmap == "now"
        - roadmap == "next"
    groupBy:
      property: roadmap
      direction: DESC   # "now" sorts before "next" when descending
    order: [formula.title_link, rank, open_task_count, parent, file.mtime]
```

- When Kanban reaches the public build, add a Kanban view grouped by `roadmap`.
- `open_task_count` is already written by `bob projects sync`.

### 7.5 `bob projects sync`, `bob pomodoro` / `tmux-pomodoro`

| Proposal | Verdict | Cost | Phase |
|---|---|---|---|
| **P1. `bob tmux-pomodoro` / `bob pomodoro` budget suffix**, e.g. `· 🔴21` when open future placeholders exceed the cap. Caps come from `~/.config/bob/config.yml` (`ledger: {max_themes: 3, max_links: 10, stale_days: 7}`), the same file the P-levels use, so bob and the plugins share one definition. | ✓ Always on screen; the cheapest persistent nudge | S | 1 |
| **P2. `bob projects sync` writes `last_pomodoro` and `pomodoros_7d`** (and optionally `minutes_7d`) per project, from 🍅 links resolved to tasks in that note. `roadmap.base` then flags a Now bet with 0 🍅 in 7 days (⚠️) and shows **time per bet**. The ledger alone can't do this today, because ALL-CAPS theme names are free text. | ✓ Turns the Base into a planned-vs-actual scoreboard (Shape Up's "appetite"). It uses the same frontmatter-count pattern as `task_count`. | M | 2 |
| **P3. Theme stats command** (`bob pomodoro stats --since`): the §3 analysis (themes open vs. worked, stale links, hours per theme) from git history or the notes | ◐ Makes the trial self-measuring. The notes alone give end-of-day state, and git gives the peaks. | M | 2 (or run ad hoc during the trial) |

---

## 8. Incidental finding (filed)

**`bob-cli-2l` (task, bug, ready): completed-reference relocation duplicates a Task Link that is already in the
destination completed Pomodoro.**

- Completing `^pomodoro-ledger-daily-roadmap` at 14:31:36 retired the open GTD placeholder's link *into* the
  completed GTD block, which already had `🍅 [[bob#^pomodoro-ledger-daily-roadmap]]`.
- The block ended up with two struck copies, one missing its 🍅, and you deleted one by hand 18 s later.
- The timestamp points at the Obsidian Ctrl+Enter retirement path rather than the 15-minute cron. The parity
  contract in `docs/task-status-hooks.md` should be checked too.
- It's minor, but it is exactly the kind of manual ledger cleanup this report is trying to remove.

---

## 9. Recommended solution

### Phase 0: this week, no code (about 30–45 min)

1. **Stop migrating.** Make the three `gtd_daily.md` edits in §6. Leftover placeholders stay in yesterday's
   note.
2. **Cap today:**
   - GTD + ≤ 3 themes, highlight first;
   - reactive blocks when they happen;
   - capture non-today work into its note (`@route^id` / `@route`), or give it a horizon (`p:1`/`p:2`).
3. **Create `roadmap.base`** (§7.4 V4):
   - set `roadmap: now` (with `rank`) on ≤ 5 existing project notes;
   - set `roadmap: next` on a handful more;
   - add a `parent:` property if the vault's note rules require one.
4. **Add the budget view** (V1) to `_templates/daily.md`, and the NOW / TODAY chips plus the Roadmap embed to
   `dash.md` (V2, V3).
5. **One-time cleanup of today's 21 themes.** No mass migration or re-filing is needed:
   - Keep ≤ 3 for tomorrow, by relinking.
   - For themes worth remembering that have no note (`QUEUE`, `SUDO` …), either:
     - create the sub-project (`@sase^queue+`) and give it `roadmap: next`; or
     - defer their tasks with `N<Ctrl+Shift+P>` → P2.
   - Let the rest decay. Git history and today's note keep the record.
6. **Add the weekly review** recurring task (§6).

### Phase 1: small `bob-cli` changes, in order of leverage

1. **P1**: tmux/`bob pomodoro` budget suffix, plus the shared `ledger:` caps in `config.yml`.
2. **C1 + C4**: capture budget warning and implicit-destination preview; this is where most of the queue enters.
3. **C2**: the `~<K>` drop list, as a follow-up to `bob-cli-2k` (same parser, numbering and Mac close card).
4. **H1**: read-only `ledger_budget` / `stale_links` in `task-status-hooks` JSON, which feeds P1, C1 and the Mac
   app.
5. **K2**: budget chip in the `Ctrl+Shift+Enter` Notice. **K1** if the picker doesn't already resolve link
   lines.

### Phase 2: only if Phase 0/1 hold and friction remains

1. **P2**: per-project 🍅/minutes in frontmatter, making the Base a planned-vs-actual scoreboard.
2. **H5**: an explicit stale-link deferral command for the weekly review.
3. **K4**: move a task with link repair (to relocate bet tasks out of `sase.md`).
4. Then **C3/K5** (pull a theme from yesterday), **H2/H3** (a written badge row or 💤 marker), **K3/C5**
   (roadmap property gestures). Build these only if the live view and the relinking prove insufficient.

### Deliberately not doing

- Cron auto-deferral or trimming (H4).
- Task-level horizon fields (options A/B).
- TaskNotes.
- A `highlight::` field.
- A hand-kept `roadmap.md` Next/Later list.
- Renaming `## Pomodoros`, which `bob`, the plugins, capture and tmux all match on.
- Strict 25/5 cycles.
- Calendar time-blocking.

### Two-week trial (2026-09-30 → 2026-10-13): signals and decision rule

| Signal | Today | Target | Measured by |
|---|---|---|---|
| Open future placeholders on the daily note (peak) | 21 | ≤ 4 (GTD + 3) | V1 view / P1 / git stats |
| Share of open themes worked | 13% | ≥ 70% | git stats (§3 method) |
| Planned themes worked/day | 3 | still ~3 (throughput shouldn't drop) | git stats |
| Links ≥ 7 d without 🍅 on the daily note | 46 | ≈ 0 | V1 / H1 |
| `[/]` + `[*]` vault-wide | ~76 (dash: 47 WIP) | ≤ ~15 | dash chips |
| `roadmap: now` bets | — | ≤ 5, each with ≥ 1 🍅/week | Base / P2 |

- **Keep the change** if the morning pick stays under about 5 minutes, "what's next?" is answered by `=`, and
  the budget view is green most days.
- **If the view is often red:**
  - because of *capture*, build C1 in strict mode;
  - because of *carry*, build C2.
- **If the Now bets drift** (no 🍅 for a week), shrink Now to 3. Otherwise the Base adds nothing, so drop it and
  keep only the capped ledger, which is the minimal variant.
- **If picking from the Base is slow** because tasks still live in `sase.md`, prioritize K4 before anything else
  in Phase 2.

**Net effect.** The daily note shrinks from about 110 Pomodoros-section lines to about 20. The morning chore list
loses two items overall: three are deleted and one "pick" is added. The only new artifacts are one `.base` file,
one property, one view file and one weekly task. The rules are enforced by things you already look at, not by
willpower.

---

## Sources

**Local evidence (read-only):**

- `~/bob/2026/20260826.md` … `20260929.md` and their full git history (1,514 revisions), via `git log` /
  `git show`
- `~/bob/_templates/daily.md`, `gtd_daily.md`, `dash.md`, `projects.base`, `refs.base`, `bob.md`, `sase.md`,
  `sase_goals.md`, `sase_blog_blockers.md`, `now.md`, `soon.md`, `now_sase.md`, `pomodoro.md`
- `~/bob/.obsidian/{core-plugins,community-plugins,hotkeys}.json`, and the deployed
  `plugins/{bob-navigation-hotkeys,block-id-prompt}/main.js`
- `bob-cli`: `README.md`, `docs/task-status-hooks.md`, `docs/capture.md`, `docs/projects.md`, `docs/dataview.md`,
  `docs/plugins.md`, `docs/vault-git-sync.md` (Mac crontab)
- `bob-cli-2k` epic bead and `plan:202609/close_task_selection.md`
- The prior report: `sase` research sidecar,
  `202609/pomodoro_ledger_and_daily_roadmap/pomodoro_ledger_and_daily_roadmap.md`

**Obsidian / Dataview / Tasks:**

1. Bases syntax (rows are files; properties): <https://obsidian.md/help/bases/syntax>
2. Bases views (Table, List, Cards, Kanban, Map): <https://obsidian.md/help/bases/views>
3. Bases functions (no `file.tasks` / body access): <https://obsidian.md/help/bases/functions>
4. Embedding a base / named views: <https://obsidian.md/help/bases/create-base>
5. Obsidian changelog, 1.9.0 → 1.14.3 (2026-09-29): <https://obsidian.md/changelog/>
6. Forum, "Bases: support for tasks" (open; staff explanation 2025-06-28):
   <https://forum.obsidian.md/t/bases-support-for-tasks/103074>
7. Forum, inline `key:: value` properties (open):
   <https://forum.obsidian.md/t/native-support-for-inline-intext-properties-key-value-a-la-dataview/17092>
8. Plugin API, `registerBasesView` / `BasesEntry`: <https://docs.obsidian.md/plugins/guides/bases-view>,
   <https://docs.obsidian.md/Reference/TypeScript+API/BasesEntry>
9. Dataview, metadata on tasks and list items:
   <https://blacksmithgu.github.io/obsidian-dataview/annotation/metadata-tasks/>
10. Tasks, Dataview format (right-to-left field parsing stops at unknown fields):
    <https://publish.obsidian.md/tasks/Reference/Task+Formats/Dataview+Format>
11. TaskNotes: <https://tasknotes.dev>

**Behavioral evidence (new in this report):**

12. Webb, T. L., & Sheeran, P. (2006). Does changing behavioral intentions engender behavior change? A
    meta-analysis of the experimental evidence. *Psychological Bulletin*, 132(2), 249–268. Intention change
    d = 0.66 → behavior change d = 0.36. <https://pubmed.ncbi.nlm.nih.gov/16536643/>
13. Jachimowicz, J. M., Duncan, S., Weber, E. U., & Johnson, E. J. (2019). When and why defaults influence
    decisions: a meta-analysis of default effects. *Behavioural Public Policy*, 3(2), 159–186. 58 studies,
    d = 0.68.
    <https://www.cambridge.org/core/journals/behavioural-public-policy/article/when-and-why-defaults-influence-decisions-a-metaanalysis-of-default-effects/67AF6972CFB52698A60B6BD94B70C2C0>
14. Harkin, B., Webb, T. L., Chang, B. P. I., et al. (2016). Does monitoring goal progress promote goal
    attainment? A meta-analysis of the experimental evidence. *Psychological Bulletin*, 142(2), 198–229. 138
    studies; stronger effects when progress is physically recorded.
    <https://www.apa.org/pubs/journals/releases/bul-bul0000025.pdf>
15. Halder, S., Zimmermann, I., Körte, L., Mehlig, L., Schmiedmayer, P., & Grüning, D. (2026). How do people
    plan digitally: an in-the-wild investigation of task planning through a smartphone app. arXiv:2609.15904.
    Of 24,265 tasks, only 26.4% went straight from creation to completion and 32.0% were abandoned, which
    argues for designing an explicit drop path. <https://arxiv.org/abs/2609.15904>

**Carried over from the prior report (used as it cited them):**

16. Forster, *Do It Tomorrow*: the closed list.
    <http://markforster.squarespace.com/blog/2011/1/24/review-of-the-systems-do-it-tomorrow.html>
17. Cirillo, *The Pomodoro Technique*: the Activity Inventory, To Do Today and Records split.
    <https://www.pomodorotechnique.com/>
18. Benson & DeMaria Barry, *Personal Kanban*: visualize and limit WIP. <https://personalkanban.com/>
19. Masicampo & Baumeister (2011): specific plans remove the intrusion of unfinished goals.
    <https://pubmed.ncbi.nlm.nih.gov/21688924/>
20. Singer, *Shape Up*, "Bets, Not Backlogs": <https://basecamp.com/shapeup/2.1-chapter-07>
