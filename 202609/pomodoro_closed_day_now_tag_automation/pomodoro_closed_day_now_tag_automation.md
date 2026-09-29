# Close the day, tag the week, let the tools hold the line: Pomodoro ledger, Now roadmap, and guardrail automation

- **Research date:** 2026-09-29
- **Question:** Should Bryan change how he tracks Pomodoros, work, time and the day's roadmap in the
  `## Pomodoros` section of his Bob daily notes (e.g. `~/bob/2026/20260929.md`)? Keep it simple, or make it
  simpler. Add complexity only where it pays for itself.
- **Starting point:** the earlier consolidated report, `pomodoro_ledger_and_daily_roadmap.md` in the `sase`
  research sidecar (**"the prior report"**), and the gaps the user listed in it:
  - it proposed no automation;
  - it never considered a `roadmap.base` with a `dash.md` badge, or Dataview properties on tasks;
  - it never looked at Obsidian keymaps, `bob capture` / Bob Mac Capture syntax, or `bob task-status-hooks`.
- **Inputs:**
  - Five independent reports in this directory: `__cdx`, `__cld`, `__grk`, `__mus` and `__gem`.
  - The user's own annotations on the prior report, in `~/bob/ref/chat/pomodoro_ledger_and_daily_roadmap.md`.
  - My own checks. I verified the claims the reports disagree on against:
    - the `bob-cli` docs;
    - the `bob-plugins` source;
    - live `bob capture-parse` and `bob query` runs;
    - a scratch-vault parser test (§1).

---

## Bottom line

1. **Yes, change it, but less than most of the reports propose.**
   - Keep the completed ledger exactly as it is:
     - the heading and its time total;
     - variable-length blocks, 🍅 marks and notes;
     - `se`, `=` and `=x`.

     It is an honest, low-friction record of your time. Every report agrees on this.
   - The chaos is the **open** half of the section. It has become the capture inbox, the backlog, the status
     source and the plan all at once.
2. **The highest-value change deletes a chore: stop migrating.**
   - `bob task-status-hooks` already decays unpicked work, which I verified in its docs:
     - a Next task no longer linked from today's open Pomodoros resets to Ready on the next run (every 15 min);
     - an In Progress task in an area/project note resets after a one-day grace period.
   - The daily "Migrate unfinished Pomodoro tasks" copy is the only thing defeating that decay.
   - Carry at most three chosen entries forward by hand. Leave the rest in yesterday's note.
3. **Cap today at GTD + 3 themes (about 10 Task Links). The first theme is the highlight.**
   - `__cld`'s theme-level git analysis shows you work a median of **3 planned themes a day**, whether 12, 15 or
     22 are open. The cap matches measured throughput; it is not an aspiration.
   - Drop the `highlight::` field. You marked it "I'm not sure about this", and ledger order already does the
     job: `=` starts the first open entry, which the `=x` diagnostic calls "next up".
4. **The roadmap needs one new marker: a `#now` tag on tasks.**
   - With it, `dash.md` renders a full Now / Next / Later roadmap:
     - **Now:** tasks tagged `#now`, about 15 at most;
     - **Next:** the READY view that already exists;
     - **Later:** tasks deferred with P1–P4. `Ctrl+Shift+P` and capture's `p:<N>` already roll them 2–365
       days out, and they resurface on their own.
   - No `roadmap.md` of copied links, and no Later bucket to maintain.
5. **Use a tag, not a `[roadmap:: now]` field, and not `roadmap.base`.**
   - **The field is unsafe as written.** Bob's property writer puts new fields at the far right of the line. My
     parser test shows that a custom field there silently erases the task's `priority` and `created` for
     Obsidian Tasks, the dash and `bob query`. A tag is safe anywhere; the vault already relies on this with
     `#hide`.
   - **`roadmap.base` can't see tasks.** Obsidian Bases rows are files, never tasks. And 60 of today's 80 queued
     links point into a single note, `sase.md`.
   - **The badge has to be DataviewJS either way.** `roadmap.base` stays an optional project-level view for
     later.
6. **Automate visibility and gestures. Never rewrite the plan from cron.**
   - Show the budget where you already look:
     - a `NOW` and a `PLAN` chip on `dash.md`;
     - a one-line live budget in the daily note;
     - a tmux suffix;
     - the capture preview.
   - Add the missing gestures:
     - a "drop" outcome for `=x`;
     - `Ctrl+Shift+P` / toggle-`#now` from a ledger link line.
   - `bob capture` warns when it would overfill today, and refuses only when it would create a *new* theme
     beyond the cap.
7. **Roll it out in phases:**
   - **Phase 0:** no code, about 30–45 minutes, and it is most of the value.
   - **Phase 1:** small, additive `bob-cli` / `bob-plugins` / Bob Mac Capture changes.
   - **Phase 2:** only if the two-week trial (2026-09-30 → 2026-10-13) says it's needed.

**Net effect.**

- The Pomodoros section shrinks from about 110 lines to about 20.
- Three morning chores become one.
- The new parts are one tag, one view file, two chips, one dash section and one weekly task.

---

## 1. What I verified this round

The reports disagreed mostly on *mechanics*. I checked each contested mechanic directly.

| Claim | Evidence | Consequence |
|---|---|---|
| Stopping migration makes work decay without new code | `docs/task-status-hooks.md`: "resets any Next task that is no longer reachable from the final open-Pomodoro graph". An area/project `[/]` is reset unless it appears in *recent activity* (today's ledger, or the one previous daily). The previous daily is "read-only … never written". `sase.md` is `type: [[project]]` and holds 40 `[/]` tasks. | `__cld` was right. No rollover command, sweep or backfill is needed. `__grk`'s "hooks delete yesterday's entries" would break a documented invariant. |
| A custom inline field at the end of a task hides Tasks metadata | Scratch vault with the vault's Tasks settings (`taskFormat: dataview`), queried with `bob query --tasks 'priority is high'` (table below) | A `[roadmap::]`/`[horizon::]` field needs a writer fix *and* a placement rule in every writer. A tag needs neither. |
| Bob's picker appends new fields at the far right | `bob-plugins` `upsertBulletProperty` inserts at `getBulletPropertyAppendIndex` (just before `^id`). The plugin's own comment warns that "Tasks-format parsers read trailing fields right to left". `~/.config/bob/config.yml` repeats the warning. | `__cdx`'s warning is confirmed. `__grk`/`__mus`/`__gem` would have shipped a bug. |
| Tags are already safe between fields | The live line `… [created::2026-08-26] #hide [priority:: high] ^prj` parses with priority High, the created date, and tags `#prj #hide` | `#now` follows an existing vault pattern |
| Capture accepts `#now` today | `bob capture-parse 'Fix thing #now @sase^fix-x'` → mode `task`, body `Fix thing #now`, block ID `fix-x`, no diagnostics. With `#now` *after* the route marker, it becomes a `legacy_bullet_marker` diagnostic. | No new capture syntax is needed; put the tag before `@route` |
| The dash chip bar can count a tag in one line | `dash.md` DataviewJS uses the Tasks plugin's `plugin.getTasks()` and already filters with `t.tags.includes("#hide")` | `counts.now = active.filter(t => t.tags.includes("#now")).length` |
| P-levels are already horizons | `config.yml`: P1 = 2–7 days, P2 = 8–30, P3 = 31–90, P4 = 91–365. Future `scheduled` → Blocked, hidden from READY. `Ctrl+Shift+P` with a future date **prunes the task's link from today's open Pomodoros** (`shouldPrune` in the picker). | "Later" already exists and resurfaces on its own, which a static Later list never does |
| `=x` has no "not today" outcome | `docs/capture.md`: worked-on *and* deferred links are both "carried" into a new placeholder | A session close can never shrink the day. `__cld`'s drop outcome fills a real gap. |
| Obsidian already has a "drop from today" gesture | `bob-plugins` d98f677 (2026-09-24): Ctrl+Shift+Enter on a Task Link line deletes the link and sets the task Open | Teach it; don't rebuild it |
| `Ctrl+Shift+P` can't act from a ledger link line | `getInlinePropertyWriteContext` edits the cursor's own line; it never resolves a Task Link to its task | `__cld`'s K1 is a real gap, and the key enabler for triage *from* the daily note |
| Where today's queued work lives | `sase.md` is one flat list of 257 tasks in auto-maintained status sections (`### Next & In Progress`, `### Blocked`, …), with no theme sections | Theme bundles exist *only* in the daily ledger. A project-level Base can't split them. |
| Your reaction to the prior report | Highlights: **"Yes!"** on "≤3 themes besides GTD … inventory labels (`SASE`, `MISC`, `LATER`, `NEW FEATURES`) belong elsewhere". **"I'm not sure about this"** on the `highlight::` line. | Keep the cap; drop the highlight field |
| The queue is still growing | While this research ran, today's note gained a new timed `TOOL` theme. It still holds 21 other open entries, including two `SASE` buckets and a 23-link `LATER` bucket. | The problem is live, not historical |

**Parser test** (Tasks settings copied from the vault; `bob query` implements Tasks v8 parsing natively):

| Task line (after `- [ ] #task …`) | `priority` seen | `created` seen |
|---|---|---|
| `A [created::…] [priority:: high] [roadmap:: now] ^a`, where the picker would place it | **Normal (lost)** | **none (lost)** |
| `B [roadmap:: now] [created::…] [priority:: high] ^b` | High | yes |
| `C [created::…] [priority:: high] #now ^c` | High | yes |
| `D [created::…] #now [priority:: high] ^d` | High | yes |

---

## 2. Why today feels chaotic (the measurements that matter)

These come from the reports' independent vault and git-history work. Where they overlap, they agree to within
rounding.

- **Capacity is stable.**
  - About 7 blocks and 270–300 tracked minutes a day.
  - `GTD` takes about 17–21% of the time; reactive blocks (`SHIT`, `FIXES`, `RELAUNCH`) about 13–15%.
  - That leaves about 5 blocks a day for chosen work.
- **Throughput is fixed at about 3 themes a day, however long the list** (`__cld`, 1,514 git revisions):

  | Period | Open themes/day (median) | Planned themes actually worked (median) | Share of open themes worked | Peak open links (median) |
  |---|---|---|---|---|
  | Aug 26 – Sep 9 | 12 | **3** | 29% | 19 |
  | Sep 10 – 20 | 15 | **3** | 17% | 42 |
  | Sep 21 – 29 | 22 | **3** | 13% | 63 |

- **Themes are created freely and rarely retired.**
  - 80 theme names were created since 2026-08-26, and 28 of them were never worked.
  - `GATES` has been open for 35 days without a block.
- **Links go stale.** 46 of today's 80 queued links (58%) have gone 7 or more days without a 🍅.
- **Most of the queue is captured, not chosen.**
  - 91% of queued links entered a ledger on the day the task was created, through `@route:id` or `#name`.
  - "Migrate unfinished …" ran daily, but "Review WIP + NEXT … plan daily Pomodoros" was last done on
    2026-09-09.
- **The end-of-day file hides the pile.**
  - Migration empties it every night, so closed days look clean.
  - Only mid-day peaks, from git or a live count, show the growth.
- **Status labels inflate.**
  - Today there are about 50 `[/]` and 25 `[*]` tasks, because hooks promote everything linked from an open
    entry.
  - By Little's Law, at about 5 closures a day that is a queue of roughly 15 days.
- **Removing work from the list feels like losing it.**
  - Unlinking a task demotes it, and nothing else remembers that it mattered this week.
  - That is the quiet incentive to hoard, which `__gem` calls the "status-lock trap".
  - The fix is not to weaken the decay. It is to give dropped work a visible home: `#now`.

The diagnosis is the same as the prior report's: one list is doing four jobs, and two of those jobs (capture
inbox and status source) keep refilling it. What changes is the cure. The data says: **delete the copier, cap the
list, and put guardrails where work enters**. It does not say "add a second list to maintain".

---

## 3. Where the reports agree (settled)

- Keep:
  - `## Pomodoros`; the name is matched by `bob`, the plugins, capture and tmux;
  - the ledger format and variable-length blocks;
  - 🍅, Work Logs and Schedule Logs.
- Don't adopt:
  - strict 25/5 cycles;
  - a second time tracker;
  - calendar time-blocking;
  - note-per-task tools (TaskNotes).
- The open section becomes a **closed daily list** (Cirillo's To Do Today; Forster's closed list). It is sized
  from the ledger's own record, not from ambition (the planning fallacy).
- Automation ships **with** the process. The prior report's "tooling only after the habit holds" was its biggest
  mistake, because the habit it relied on had already lapsed.
- Obsidian Bases rows are **files**. A `.base` can't list checkbox tasks or read inline `key:: value` fields.
- The dash's existing DataviewJS chip bar is the right place for a badge.
- `@route:id` / `#name` capture is the main inflow. `task-status-hooks` should report plan violations, not
  silently choose, prune or migrate.

---

## 4. Where the reports disagree, and how I resolved it

| Issue | Positions | Resolution | Why |
|---|---|---|---|
| **Inventory marker on tasks** | `[roadmap:: now\|next\|later]` (`__cdx`); `[horizon:: …]` (`__grk`, `__mus`, `__gem`); none, project-level only (`__cld`) | **`#now` tag, one value** | The tasks to pick from live in one file (`sase.md`), so a project-level marker can't select them. A field breaks Tasks parsing unless every writer is fixed (§1). A tag is parser-safe, typeable in capture today, counted by the existing chip code, and follows the `#hide` precedent. |
| **Next and Later tiers** | Explicit values (`__cdx`, `__grk`, `__mus`, `__gem`); existing P-levels (`__cld`) | **Next = unmarked READY; Later = P1–P4 deferral** | P-levels already *are* horizons, with a keymap, capture syntax, a Schedule Log, `bob randomize`, and automatic resurfacing. Static Later lists have died twice in this vault: the zorg-era `now_*/soon_*/maybe_*` notes and `sase_blog_blockers.md`. Add a `#next` tag only if weekly promotion from READY proves too slow. |
| **`roadmap.base`** | Task-level views (`__mus`, which isn't technically possible); project-level (`__cld`, `__grk`, `__gem`); defer (`__cdx`) | **Defer. Optional, project-level only** | It is useful only once this week's bets have their own notes that hold their own tasks. Today the bets are mostly bundles of `sase.md` tasks. |
| **Where the roadmap renders** | Generated `roadmap.md` (`__cdx`); dash sections (`__grk`); an embedded Base (`__gem`, `__cld`) | **`dash.md`: NOW chip + NOW section; READY and BLOCKED already exist** | The dash is one key (`Ctrl+,`) from every daily note. A query-only `roadmap.md` is fine if you want a dedicated tab, but it must never hold hand-maintained links. |
| **Yesterday's leftovers** | Explicit command that marks them `[-]` (`__cdx`); hooks delete them + backfill a horizon (`__grk`); cron sweeps them into roadmap (`__gem`); send-back keymap (`__mus`); leave them, and they decay (`__cld`) | **Leave them in yesterday's note; carry at most 3 by hand** | Decay already works (§1). Cron edits to history race unsaved buffers and multi-machine sync. The old migrate gesture (cut/paste) is cheap and keeps bundles intact; its only flaw was having no cap. |
| **Highlight** | `highlight::` line (`__cdx`, `__mus`, `__gem`, prior); frontmatter (`__grk`); ledger order (`__cld`) | **Ledger order** | You doubted the line. `=` already starts the first open entry. Adding a field adds a ritual. |
| **Status coupling** | Keep Next tasks that are in roadmap Now (`__gem`); keep Next = today (everyone else) | **Next stays "linked from today"** | `__gem`'s variant re-inflates the NEXT chip. Its `@route~id` form would create a Next task that hooks reset on the next run. |
| **Capture default** | Breaking change: `@route:id` stops linking (`__grk`); silent diversion to roadmap (`__gem`); warning (`__cdx`, `__cld`); Mac "For today?" toggle, default off (`__mus`) | **Warn at the cap; refuse only a *new* theme beyond the cap (configurable)** | Visible feedback at the moment of choice is the default-plus-monitoring lever. Silent diversion hides where a task went. `#name` creating new buckets (`NEW FEATURES`, a second `SASE`, `LATER`) is the specific leak. |
| **New capture syntax** | `r:now` (`__cdx`); `h:now` (`__grk`, `__gem`); `@route~id` (`__gem`); `@route!id` (`__mus`); none (`__cld`) | **None for horizons; add a drop outcome to `=x`** | `#now` in the body already works. The genuinely missing outcome is "drop this link from today" at close time. |
| **Hooks writing into the daily note** | Managed cap block + warning callout (`__grk`); read-only diagnostics (`__cdx`, `__cld`, `__mus`) | **Read-only JSON diagnostics; live views in Obsidian** | A block written by cron is a snapshot up to 15 minutes stale. It lands in a hand-edited section, and every ledger parser must be taught to skip it. |
| **Caps** | 1 highlight + 2 + GTD (prior, `__cdx`, `__gem`); 3 + GTD (`__cld`, `__grk`, `__mus`) | **GTD + 3 distinct themes, the first being the highlight; ≈10 links; NOW ≤ 15 tasks** | These are the same number stated two ways. NOW ≈ one week of multi-day tasks at about 6 🍅 links a day. |
| **Agent-supervision theme** | `SUPERVISION` / `REVIEW` themes (`__gem`) | **Not needed** | The prior report did account for agent work (several links per block). A standing "if blocked on agents → next theme or GTD" rule covers it. |

---

## 5. The recommended system

### 5.1 The rule (fits on an index card)

> **Today is closed:** GTD plus at most 3 themes. The first theme is the highlight. Nothing is copied forward by
> default.
> **This week is `#now`:** at most about 15 tasks. Dropping a link from today never loses it, because `#now` keeps
> it in view.
> **Everything else is READY (next) or deferred with a P-level (later).**

### 5.2 One home per job

| Job | Home | Change |
|---|---|---|
| Record what happened (time, themes, 🍅, notes) | Completed entries in `## Pomodoros` | **None** |
| Today's plan | Open entries in `## Pomodoros`: GTD + ≤ 3 themes, ≈10 links | **Cap it; stop migrating** |
| This week's pool ("Now") | `#now` on task lines, rendered on `dash.md` | **New: one tag** |
| Backlog ("Next") | Ready tasks in area/project notes: the dash's READY view | None |
| Later, resurfacing on its own | P1–P4 via `Ctrl+Shift+P` / `p:<N>`; `bob randomize` | None; use it as *the* defer gesture |
| Statuses | `task-status-hooks`: Next = linked today; `[/]` decays | None; stop overriding it by migrating |

### 5.3 Capture: four intents, all with today's grammar

| Intent | Capture | Result |
|---|---|---|
| Today | `Fix the deploy @sase:fix-deploy` (optionally `#THEME`, `=X`) | Next task plus a Task Link in today's ledger |
| This week | `Fix the deploy #now @sase^fix-deploy` | Ready task tagged `#now`; today untouched |
| Backlog | `Fix the deploy @sase^fix-deploy` | Ready task; today untouched |
| Later | `Fix the deploy @sase^fix-deploy p:2` | Deferred 8–30 days, logged in the Schedule Log, resurfaces automatically |

For work that isn't for today, the one habit is **`^` instead of `:`**. The Phase 1 capture warning (§6.3) makes
that visible when you forget.

### 5.4 The daily note

````markdown
- [/] #task [[gtd_daily]] [created::2026-09-30] ^gtd

```dataviewjs
await dv.view("_meta/views/plan_budget")
```

## Pomodoros (`= …unchanged formula…`)

- [ ] () — GTD
	- [[#^gtd]]
- [ ] () — GOALS              ← first named theme = today's highlight
	- [[sase_goals#^epic-roadmap]]
	- [[bob#^better-roadmaps]]
- [ ] () — DECKS
	- [[sase#^card-blocks]]
	- [[sase#^p-key-for-decks]]
- [ ] () — BOB
	- [[bob#^solo-id-capture]]
````

- **Reactive work** (`SHIT`, `RELAUNCH`) gets an honestly named block *when it happens*. It is never pre-staged.
- **Inventory labels** (`SASE`, `MISC`, `LATER`, `NEW FEATURES`) are not themes.
- **Don't copy the same links into every block.** Continue the theme, and let 🍅 and a one-line note show what
  moved.
- **The `dataviewjs` line** sits above the heading, so no ledger parser sees it. It renders something like
  `🟢 Plan 3/3 themes · 7/10 links`, or 🔴 when over the cap. An alternative is to append the same numbers to the
  heading's existing inline expression.

### 5.5 Rituals

**Morning pick (≤ 5 minutes).** This replaces three `gtd_daily` chores.

1. Glance at yesterday's open entries.
   - Cut **at most 3** that you'll continue into today, below GTD. This is the old migrate motion, with a cap.
   - Leave the rest; they are yesterday's honest history.
2. If you carried fewer than 3, fill up from the dash's **NOW** section:
   - Ctrl+Shift+Enter on the task, then `Ctrl+Shift+M` / `=NAME` to group it under a theme;
   - or use a Bob Mac Capture batch of `^route:id#theme` lines.
3. Put the highlight theme first after GTD.
4. **Standing contingency** (Parke et al. 2018): if the highlight is blocked on agents, work the next theme or
   GTD for one block, then reassess. Do not pull a fourth theme.

**During the day.** Any link that won't happen today goes one of three ways:

- **Keep it close:** make sure the task has `#now`, then press Ctrl+Shift+Enter on the link line. That already
  deletes the link and reopens the task.
- **Defer it:** `Ctrl+Shift+P` → P1/P2 on the task. This already prunes its link from today.
- **Let it go:** do nothing, and it won't be carried tomorrow.

**Weekly (one GTD block, 25–40 min, Monday).**

1. Re-tag NOW down to 15 or fewer. Remove `#now` from anything with no 🍅 in 7 days that isn't this week's bet.
2. Promote from READY.
3. Bulk-defer with P-levels.
4. Look at three numbers: hours, created vs. closed, and the reading backlog.
   - Closure ran at 0.47 of intake in September, so the prune is not optional.
   - Planning can't fix intake. A research/reading budget is the lever. For example, this question spawned two
     five-agent swarms in one day.

**`gtd_daily.md` edits.**

- Delete:
  - "Migrate unfinished Pomodoro tasks";
  - "Review READY tasks";
  - "Review WIP + NEXT … plan daily Pomodoros".
- Add:
  - `Pick today: ≤3 themes from yesterday + [[dash#NOW Tasks|NOW]] (highlight first)`;
  - one `[repeat:: every week on Monday when done]` review task.

---

## 6. Automation catalog (answering the specific asks)

**Principle:**

- Automate **visibility** and **gestures**.
- Automate structural cleanup that loses nothing; the hooks already do this.
- Anything that removes or defers *your plan* happens only through an explicit gesture, with a preview.

### 6.1 Obsidian views: `dash.md` and the daily template (Phase 0, no Rust)

**V1. `_meta/views/plan_budget.js`.** One shared Dataview view, used by the daily template and the dash. This is
an untested sketch:

```js
// usage: await dv.view("_meta/views/plan_budget", {file: optionalPath})
const CAP_THEMES = 3, CAP_LINKS = 10;
const page = input?.file ? dv.page(input.file) : dv.current();
const open = page.file.tasks.where((t) => !t.parent && t.status === " " &&
  String(t.section?.subpath ?? "").startsWith("Pomodoros"));
const names = new Set(open.values
  .map((t) => (t.text.match(/—\s*(.+)$/) ?? [])[1]?.trim())
  .filter((n) => n && n !== "GTD"));
const links = new Set(open.values.flatMap((t) => t.children ?? [])
  .filter((c) => !c.text.includes("~~"))
  .flatMap((c) => c.text.match(/\[\[[^\]|]*#\^[^\]|]+/g) ?? []));
const over = names.size > CAP_THEMES || links.size > CAP_LINKS;
dv.paragraph(`${over ? "🔴" : "🟢"} **Plan** ${names.size}/${CAP_THEMES} themes · ${links.size}/${CAP_LINKS} links`);
```

- It counts **distinct** names, so today's two `SASE` buckets count once. The duplicate itself is a lint item
  (§6.4).
- The numbers are advisory. `bob`'s JSON (§6.4) is authoritative wherever the two differ.

**V2. Dash chips.** Add these to the existing chip bar:

- `NOW n/15`: `counts.now = active.filter(t => t.tags.includes("#now")).length`. It turns red over the cap and
  jumps to `dash#NOW Tasks`.
- `PLAN k/3 · l/10`: V1 run against today's daily. It turns red over the cap and jumps to today's note.

The WIP chip (about 50 today) should fall on its own once migration stops. That drop is a free success signal.

**V3. A `## NOW Tasks` section** above the existing WIP / NEXT / READY sections:

````markdown
```tasks
not done
tags include #now
group by filename
sort by priority
```
````

The dash's existing query defaults (not `#hide`, scheduled today or earlier) already exclude deferred tasks.

**Optional: a query-only `roadmap.md`.** Three queries, no links:

- NOW: `tags include #now`;
- NEXT: READY without `#now`, with a limit;
- LATER: `scheduled after today`, grouped by month.

Build it only if you want a dedicated tab.

### 6.2 Obsidian keymaps (`bob-plugins`)

| # | Change | Why | Phase |
|---|---|---|---|
| K1 | **`Ctrl+Shift+P` on a Task Link line edits the linked task.** Counted `N<Ctrl+Shift+P>` covers the next N links. | Today it edits the cursor line itself (§1). Deferring or triaging from the daily note is where the pile is visible, and it is how the first transition day and every weekly prune become a few keystrokes. | 1 |
| K2 | **"Toggle `#now`" command**, counted, on task lines *and* Task Link lines. Bind one free chord, or add it as an entry in the `Ctrl+Shift+P` picker. | Tagging while you drop a link from today is the safety net that ends hoarding. Typing `#now` by hand works in Phase 0 and on mobile. | 1 |
| K3 | **Budget in the Ctrl+Shift+Enter Notice**, e.g. `linked · plan 4/3 🔴`. Warn, don't refuse; honor the same `strict` setting as capture. | Makes the rule visible at the exact moment of breaking it | 1 |
| — | Ctrl+Shift+Enter on a link line = drop from today (shipped 2026-09-24); `Ctrl+Shift+M` / `=NAME` to group; `Ctrl+,` to the dash | Already exist; teach them as the process's gestures | 0 |
| K4 | Move a task to another note with link repair (already on `bob.md`'s Future Work) | Needed only if bets move out of `sase.md` into their own notes (§7) | 2 |

**Rejected:**

- three new chords for pick / send-back / highlight (`__mus`);
- a destination-switch modal (`__gem`);
- a separate horizon picker with three values.

Capture batches plus Ctrl+Shift+Enter already cover the pick. Revisit only if the pick regularly takes more than
5 minutes.

### 6.3 `bob capture` and Bob Mac Capture

| # | Change | Notes | Phase |
|---|---|---|---|
| C1 | **Plan-budget warning** in `bob capture` / `--dry-run` output and JSON. Add `plan_budget {themes, links, caps}` plus stable warning codes. **Strict mode** (config) refuses `#name` creating a new theme beyond the cap, with the hint "use `^`, add `#now`, or defer with `p:<N>`". | `capture-parse` is lexical only, so the warning must come from the vault-aware paths. The Mac preview already shows vault diagnostics such as "no running Pomodoro". Starting a session (`=`, `#name=`) is never blocked, because reactive blocks are legitimate. | 1 |
| C2 | **A drop outcome for `=x`**, e.g. `=x1!3~4,5`: links in `~<K>` leave today, are not carried and are not started. The hooks then demote them. | This is the missing fourth outcome; today every outcome except "complete" carries the link. It is a follow-up to `bob-cli-2k` (same lexer, numbering and Mac close card). The exact spelling belongs to that epic. | 1 |
| C3 | **Show the implicit destination** in the preview: "→ under GOALS (next up)" | Prevents silent pile-ups under the first open entry | 1 |
| C4 | **Treat `#now` as a first-class token**: a semantic span/color in the Mac palette, a `capture-complete` candidate, and acceptance after the route marker too | It works before `@route` today. This makes it discoverable and removes the ordering trap. | 1 |
| C5 | Pull a theme from yesterday by name (`<NAME`) | Nice ergonomics; build only if cut/paste feels slow | 2 |

Bob Mac Capture stays a thin client. Every item above arrives through `bob`'s parse, complete and dry-run JSON.
Coordinate each contract change across both repos, as the linked-repo rule requires.

**Rejected:**

- the breaking `@route:id` default and its environment-variable escape hatch (`__grk`);
- silent diversion to a roadmap (`__gem`);
- `h:` / `r:` / `~id` / `!id` horizon tokens.

### 6.4 `bob task-status-hooks`: can it flag violations or automate cleanup?

It already automates the safe cleanup: dedupe, canceled-link removal, completed-link retirement, childless-entry
deletion, 🍅 repair and status decay. Extend it **read-only** (Phase 1):

- **H1: a `plan_budget` block in JSON and human output**, with stable warning codes and exit 0:
  - `plan_theme_cap_exceeded` and `plan_link_cap_exceeded`, counting distinct open names excluding GTD;
  - `duplicate_open_pomodoro_name`;
  - `inventory_label_open`, from a configurable list such as `LATER`, `MISC`, `NEW FEATURES`;
  - `subheading_in_pomodoros`: a `###` inside the section breaks the heading's time total;
  - `now_cap_exceeded`;
  - `stale_link`: no 🍅 in N days. This needs a lookback over N dailies; today the hooks read only one.
- **An actionable hint on the multi-open-timed hard error** (`__mus`). Name both entries and suggest `=x`.
- **Shared caps** in `~/.config/bob/config.yml`, e.g. `ledger: {max_themes: 3, max_links: 10, max_now: 15,
  stale_days: 7, strict: false}`. `bob` and the plugins then share one definition, as they already do for
  P-levels.

**Never:**

- auto-defer, prune or delete from cron;
- write into yesterday's note, which is a documented read-only invariant;
- treat `#now` as a Next source, which would re-inflate NEXT;
- write callouts into the daily note.

### 6.5 `bob pomodoro` / `tmux-pomodoro` (Phase 1)

Append the H1 budget to the always-visible segment, e.g. `🍅 GOALS 23m · 3/3 · 9/10`, inverted when over the cap.
It is the cheapest persistent nudge, and it works when Obsidian isn't focused.

### 6.6 Measuring the trial (Phase 2, or run ad hoc)

`bob pomodoro stats --since` would turn `__cld`'s one-off `/tmp` analysis into a command:

- themes open vs. worked, from git peaks;
- stale links;
- hours per theme.

Then the trial measures itself instead of relying on hand counts, which are another habit that would lapse.

---

## 7. `roadmap.base`: what it can and can't do, and when it's worth building

- **What Bases can do:**
  - one row per **file**;
  - columns from frontmatter and `file.*` only;
  - no task or list-item rows, and no inline `key:: value` fields;
  - no inline value rendering, so a Base can't be a badge in a heading.
- **What it can't do.** `__cld` reports that the "Bases: support for tasks" request is still open, and that no
  changelog entry through 1.14.3 adds task rows.
- **So a Base can only be a *project-level* roadmap.** That would mean `roadmap: now|next` frontmatter on ≤ 5
  project notes, table or Kanban views, and `projects.base` conventions. `__cld` §7.4 and `__grk` §5.4 have
  usable sketches.
- **Why not now:**
  - 60 of 80 queued links live in `sase.md`, so the project row "sase: now" would tell you nothing about which
    tasks to pick;
  - it would be a second "Now" to keep in sync with `#now`.
- **Build it when either of these holds:**
  - at least 3 of the week's bets have their own sub-project notes that hold their own tasks (K4 makes the move
    safe);
  - the `bob#^better-roadmaps` structure-note idea returns.

  At that point it answers "which bets this month?", and `#now` keeps answering "which tasks this week?".
- **Bundles in the meantime.** If a theme's tasks must travel together, make the theme an **epic task with
  transcluded children** (`- ![[#^card-blocks]]`), a pattern the vault already uses in about 10 notes. Linking
  the epic promotes its whole tree. Keep epics small, because every child becomes Next.

---

## 8. Shortcomings of the prior report, beyond the ones you named

| # | Shortcoming | Effect | Fixed by |
|---|---|---|---|
| 1 | Its cure was three new habits (pick, capture spelling, weekly review), with tooling deferred | The failure it diagnosed *was* a lapsed habit. Intention changes move behavior only weakly (Webb & Sheeran 2006); defaults (Jachimowicz et al. 2019) and recorded self-monitoring (Harkin et al. 2016) do better. | §6: warnings and chips where you already look |
| 2 | It missed the horizon machinery that already exists: P1–P4 rolls, `Ctrl+Shift+P` prune, `bob randomize` | Its `roadmap.md` Next/Later would have been a third system next to statuses and priorities | Later = P-levels |
| 3 | It kept a copy step: "cut yesterday's open entries into `roadmap#Now`" | This is the migrate chore aimed at a new file, and Now would have inherited the whole pile | Leave leftovers; they decay; carry ≤3 |
| 4 | It measured links, not themes | Missed that throughput is flat at about 3 themes a day, which is the natural cap | §2 |
| 5 | It ignored `=x` carry semantics | No close outcome can shrink the day | C2 drop outcome |
| 6 | It added a `highlight::` field | You doubted it; ledger order already encodes it | §5.4 |
| 7 | It didn't check metadata/parser safety | Any "add a field" design silently hides `priority` / `scheduled` | §1 parser test; `#now` tag |
| 8 | It ignored the vault's history with horizon lists (zorg `now/soon/maybe`, `sase_blog_blockers`) | Hand-kept horizon lists have died twice | Generated views only; nothing hand-kept |
| 9 | It didn't address the loss aversion behind hoarding | Unlinking demotes, so everything stays linked | `#now` safety net plus the drop gestures |
| 10 | Its metrics were hand-counted and end-of-day | End-of-day files hide the peak | H1 / V1 live counts; mid-day git stats |
| 11 | It never priced the pick | Removing the copy must keep *continuing* a theme cheap, or migration creeps back | Capped cut/paste; capture batches; C5 if needed |

**Incidental.** `__cld` found and filed **`bob-cli-2l`**: completed-reference relocation duplicates a Task Link
that is already in the destination block. It is small, but it is exactly the kind of manual ledger cleanup this
redesign is meant to eliminate.

---

## 9. Risks

- **NOW becomes the next pile.**
  - Defenses: the red chip, `now_cap_exceeded`, and the weekly re-tag.
  - If NOW is red most days, shrink the cap or make the weekly review stricter. Do not add tiers.
- **Decay feels like loss.**
  - About 40 `[/]` tasks in `sase.md` will drop to `[ ]` within a day or two. That is intended: Next and WIP
    regain their meaning.
  - Tasks never leave their notes, Work Logs stay, and anything that matters gets `#now`.
- **Warnings get ignored.** If capture warnings fire daily and the plan stays red, turn on `strict`. The data says
  capture is where the pile starts.
- **Count drift between DataviewJS and `bob`.** The views are advisory, and `bob`'s JSON is the definition. Keep
  the rules simple (distinct names, unique block links) so they agree.
- **Three-repo change surface.** Every Phase 1 item is additive and lands behind existing contracts. The Mac app
  only decodes new JSON fields and must tolerate older `bob` builds that don't send them.
- **Intake still outruns closure.** No daily-planning scheme absorbs a 2:1 intake ratio. The weekly prune and a
  research/reading budget are the real levers.

---

## Recommended solution

**Keep the ledger. Close the day. Tag the week. Let the tools, not the morning ritual, hold the line.**

### Phase 0: this week, no code (about 30–45 minutes)

1. **Stop migrating.**
   - Make the `gtd_daily.md` swap in §5.5: three chores out; one pick and one weekly review in.
   - From tomorrow (2026-09-30), carry **at most 3** of today's open entries by hand. Leave the other 18 or so
     where they are; hooks will decay their statuses.
2. **Tag this week.**
   - While today's queue is still visible, add `#now` to **≤ 15** tasks you really want this week. Open each
     link and type the tag before the fields or the `^id`.
   - The `LATER` bucket's tasks simply decay to READY. Defer the ones that should resurface with `Ctrl+Shift+P`
     → P2/P3 during the first weekly review.
3. **Make the rules visible.**
   - Add `plan_budget.js` (V1) and its one-line call above `## Pomodoros` in `_templates/daily.md`.
   - Add the `NOW` and `PLAN` chips and the `## NOW Tasks` section to `dash.md` (V2, V3).
4. **Capture with intent** (§5.3):
   - `:` = today;
   - `#now … ^` = this week;
   - `^` = backlog;
   - `p:<N>` = later.
5. **Put GTD + ≤ 3 themes in the daily note, highlight first.** Create reactive blocks only when they happen.

### Phase 1: small, additive code, in order of leverage

1. **H1 + shared caps.** A read-only `plan_budget` in `task-status-hooks` JSON, with `ledger:` caps in
   `config.yml`.
2. **Where you look:**
   - the tmux / `bob pomodoro` budget suffix;
   - the capture budget warning, strict mode for new themes, and the implicit-destination preview (C1, C3),
     rendered by Bob Mac Capture.
3. **Gestures:**
   - the `=x` drop outcome as a `bob-cli-2k` follow-up (C2);
   - `Ctrl+Shift+P` and toggle-`#now` from Task Link lines (K1, K2);
   - the budget in the Ctrl+Shift+Enter Notice (K3);
   - first-class `#now` in capture completion and colors (C4).

### Phase 2: only if the trial shows friction

- `bob pomodoro stats`;
- move-with-link-repair (K4), then a project-level `roadmap.base`;
- a `#next` tag;
- pull-a-theme-from-yesterday (C5);
- an explicit, previewable "close day" command that marks leftover placeholders `[-]` (`__cdx`), only if old open
  placeholders become noise.

### Deliberately not doing

- `[roadmap::]` / `[horizon::]` fields;
- task-level Bases;
- a hand-kept `roadmap.md`;
- a `highlight::` field;
- cron that rewrites plans or yesterday's note;
- treating `#now` as a Next source;
- breaking `@route:id`;
- renaming `## Pomodoros`;
- strict 25/5 cycles;
- calendar blocking;
- TaskNotes.

### Two-week trial (2026-09-30 → 2026-10-13)

| Signal | Today | Target | Measured by |
|---|---|---|---|
| Peak distinct open themes (excl. GTD) | 21 | **≤ 3** | V1 / H1 / git |
| Peak open Task Links | 74–75 | **≤ ~10** | V1 / H1 / git |
| Share of planned themes worked | 13% | **≥ 70%** | git stats (`__cld` method) |
| Planned themes worked per day | 3 | still about 3 | git stats |
| Morning pick completed | last "plan" done 2026-09-09 | **≥ 10 of 14 days**, ≤ 5 min | `done/gtd_daily_done.md` |
| `[/]` + `[*]` vault-wide | ≈ 75 | **≤ ~15** | dash chips |
| NOW after each weekly review | — | **≤ 15**, each with ≥ 1 🍅 that week | NOW chip |

**Decision rules:**

- **Keep it** if the next block is usually obvious (`=` answers "what now?"), the plan chip is green most days,
  and nothing piles up on the daily note.
- **If the plan is often red:**
  - because of **capture**, turn on `strict`;
  - because of **carry**, prioritize the `=x` drop outcome.
- **If NOW is ignored,** delete the tag and keep only the capped ledger. That is the minimal variant, and it
  still captures most of the gain.
- **If picking is slow,** build C5 (pull a theme) or use epic tasks for bundles before anything else in Phase 2.

This is simpler day to day than what you do now:

- one capped list instead of a 110-line queue;
- one pick instead of three chores;
- one tag instead of a second backlog.

The extra structure is paid for by deleting the copier, not by adding willpower.

---

## Sources

**Local evidence (read-only this round):**

- `~/bob/2026/20260929.md` (live state at the time of writing); `~/bob/ref/chat/pomodoro_ledger_and_daily_roadmap.md`
  (your highlights and comments)
- `~/bob/dash.md` (chip bar and query defaults); `~/bob/sase.md` (structure, `type`, `[/]` count);
  `~/bob/.obsidian/plugins/obsidian-tasks-plugin/data.json`; vault-wide `grep` for `#now`, `[roadmap::`,
  `[horizon::`, and transcluded sub-tasks
- `~/.config/bob/config.yml` (P-level windows; the right-to-left parser warning)
- `bob-cli`: `docs/task-status-hooks.md` (Rolling Recent Activity, status tables), `docs/capture.md` (grammar
  table, `=x` carry rules, `@route+id!` toggle, "next up"); live `bob capture-parse` and `bob query --tasks` runs;
  scratch-vault parser test
- `bob-plugins`: `bob-navigation-hotkeys/main.js` (`upsertBulletProperty`, `getInlinePropertyWriteContext`,
  `shouldPrune`); commit `d98f677` (Ctrl+Shift+Enter drop)
- `sase bead list` (`bob-cli-2k`, `bob-cli-2l`)
- Prior report: `sase--research` `202609/pomodoro_ledger_and_daily_roadmap/pomodoro_ledger_and_daily_roadmap.md`
- The five component reports in this directory; their own source lists hold the full citations

**Obsidian / Dataview / Tasks:**

1. Obsidian, Introduction to Bases, Bases syntax, and Views (rows are files; note/file/formula properties):
   <https://obsidian.md/help/bases>, <https://obsidian.md/help/bases/syntax>, <https://obsidian.md/help/bases/views>
2. Obsidian forum, "Bases: support for tasks" (open; per `__cld`):
   <https://forum.obsidian.md/t/bases-support-for-tasks/103074>
3. Tasks, Dataview format (trailing fields are parsed right to left):
   <https://publish.obsidian.md/tasks/Reference/Task+Formats/Dataview+Format>
4. Dataview, Metadata on Tasks and Lists: <https://blacksmithgu.github.io/obsidian-dataview/annotation/metadata-tasks/>

**Methods and behavioral evidence:**

5. Cirillo, *The Pomodoro Technique*: the Activity Inventory / To Do Today / Records split.
   <https://www.pomodorotechnique.com/>
6. Forster, *Do It Tomorrow*: closed lists.
   <http://markforster.squarespace.com/blog/2011/1/24/review-of-the-systems-do-it-tomorrow.html>
7. Buehler, Griffin & Ross (1994), the planning fallacy. *JPSP* 67(3), 366–381.
   <https://doi.org/10.1037/0022-3514.67.3.366>
8. Webb & Sheeran (2006), intention change → behavior change (d = 0.66 → 0.36). *Psych. Bull.* 132(2).
   <https://pubmed.ncbi.nlm.nih.gov/16536643/>
9. Jachimowicz, Duncan, Weber & Johnson (2019), default effects meta-analysis (d ≈ 0.68). *Behavioural Public
   Policy* 3(2).
10. Harkin et al. (2016), monitoring goal progress promotes attainment. *Psych. Bull.* 142(2).
    <https://www.apa.org/pubs/journals/releases/bul-bul0000025.pdf>
11. Parke, Weinhardt, Brodsky, Tangirala & DeVoe (2018), contingency planning on high-interruption days. *J. Appl.
    Psych.* 103(3), 300–312.
12. Masicampo & Baumeister (2011), specific plans remove the intrusion of unfinished goals.
    <https://pubmed.ncbi.nlm.nih.gov/21688924/>
13. Benson & DeMaria Barry, *Personal Kanban* (visualize, limit WIP); Little's Law (Kanban University 2022).
    <https://kanban.university/wp-content/uploads/2022/09/Exploring-Littles-Law-KGS-2022.pdf>
14. Singer, *Shape Up*, "Bets, Not Backlogs": <https://basecamp.com/shapeup/2.1-chapter-07>; Bastow, Now/Next/Later
    is for initiatives: <https://www.prodpad.com/blog/invented-now-next-later-roadmap/>
15. Biwer et al. (2023); Smits, Wenzel & de Bruin (2025); Göksu, Wiradhany & de Bruin (2026): self-regulated or
    Flowtime breaks are no worse than strict Pomodoro (carried from the prior report).
