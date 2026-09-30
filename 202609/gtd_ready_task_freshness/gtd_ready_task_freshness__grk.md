# Ready-task freshness: a daily glance that does not re-read the whole backlog

- **Researcher:** grk
- **Date:** 2026-09-30
- **Question:** How should Bob implement “task freshness” so yesterday’s captures (especially `bob gkeep pull` inbox items) get a human glance the next morning, without forcing a daily re-read of every Ready task? Is the proposed design a good idea, and what should change?

## Headline

**Yes, build freshness. Treat it as a review queue, not as a new lane.**

The pickup-daughter case is real, and the old “open `dash.md` READY and grind each project down to ≤5” habit is the wrong instrument for it. A last-confirmed date plus an interval is the right primitive. Several of the original requirements should change so the primitive survives Obsidian Tasks’ field parser, matches Bob’s existing log-child pattern, and does not let a 7-day stamp hide an unprocessed inbox item.

The recommended system is:

1. **Inbox is a daily, path-based queue.** `gkeep_inbox.md` (and `mac_inbox.md`) stay due every morning until the task leaves that note.
2. **Filed Ready tasks get a last-confirmed date** (`fresh`) and a refresh interval (default 7 days, overridable on the project and on the task).
3. **The morning review walks INBOX, then PENDING, then NEXT, then STALE Ready.** READY itself stays an inventory, not a daily reading list.
4. **Keymaps jump vault-wide among stale Ready tasks and stamp “I looked” without other edits.** Supported Bob keymaps that already rewrite a Ready task also stamp.

This is the Obsidian reincarnation of the old Zorg `@FRESHNESS` notes, moved from files to tasks for inbox items, and kept file/project-scoped for interval defaults.

## Verdict

The idea is sound for this vault, and it is the missing piece of epic `bob-cli-2y`’s morning ritual.

`bob-cli-2y` (plan `plan:202609/retire_now_sticky_lanes.md`, phase `dash-lanes`) already rebuilt the dash as mutually exclusive TODAY / PENDING / NEXT / READY and replaced the `#now` chores with:

- daily: PENDING → NEXT → READY in ≤5 minutes
- weekly: prune NEXT ≤15 and PENDING ≤10

That solves lane growth. It does not solve “I captured something in Keep last night and it is now a Ready checkbox among 186 others.” READY is still an inventory of every doable `[ ]` task that is not Today. Glancing that inventory every morning is how the pickup-daughter task would have been seen. It is also how a filed `sase.md` bug from 2026-09-09 gets reread for the 21st consecutive day.

Freshness splits those jobs. Inbox processing stays daily. Confirmation of already-filed Ready work becomes periodic. The dash keeps READY as a pull list.

Live vault snapshot, 2026-09-30, `bob query --format json --tasks` with `dash.md` origin (same Query File Defaults the dash uses: not templates, not `#hide`, not dependency-blocked, `scheduled` today or earlier):

| Set | Count |
| --- | ---: |
| Dash-visible Ready (`status.type is TODO`) | 186 |
| of those in `gkeep_inbox.md` | 65 |
| of those filed in other notes | 121 |
| Notes that contain Ready tasks | 27 |
| Notes with >5 Ready | 6 |
| Recurring Ready (7 of them in `gtd_daily.md`) | 10 |
| Dash-visible Next | 26 |
| Dash-visible Pending | 52 |
| Ready created 2026-09-29 | 1 |
| Ready created 2026-09-30 | 1 |
| Steady-state 7-day wave (`186 / 7`) | ~27 / day |

`gkeep_inbox.md` is 35% of visible Ready, with items dated 2026-09-09 through 2026-09-29 and **zero** block IDs. Yesterday’s capture volume is currently tiny; the drowning hazard is the unprocessed inbox pile, not the daily drip. Freshness that treats “never confirmed” as stale will put all 65 inbox tasks in the morning queue until they are filed, completed, scheduled, or cancelled. That is the correct pressure. A 7-day stamp that can snooze them is the incorrect one.

---

## What already exists

### The GTD surfaces freshness has to sit on

- **`~/bob/dash.md`** — chip bar plus Tasks blocks for TODAY / PENDING / NEXT / READY. Note-wide `TQ_extra_instructions` group by path. READY is every remaining TODO that is not Today.
- **`~/bob/gtd_daily.md`** — daily chores already include “Import inbox tasks from Google Keep” and the new `bob-cli-2y` morning review. The cancelled `#now` chores are still in the file as `[-]`.
- **`bob gkeep pull`** — writes `- [ ] #task {title} [created::{date}]` plus Source children and a `%%gkeep:v1:…%%` marker into `gkeep_inbox.md`. It does not write a block ID, a project, a `scheduled` date, or any confirmation date. New Keep notes are Ready and unconfirmed on arrival.
- **Lanes** (`decisions:task-lanes-are-sticky`) — Ready `[ ]` → Next `[*]` → Pending `[/]`. Blocked `[?]` is derived from `dependsOn` or a future `scheduled` date and recovers to Ready as re-triage. Release (Alt+N) is the only human demotion. Hooks no longer lower Next/Pending.
- **Today** (`decisions:today-is-read-from-the-ledger`) — computed at read time from open Pomodoro Task Links. Never written onto task lines.
- **Priority windows** — P1–P4 roll a future `scheduled` date and therefore Blocked. That is a tickler, not a review. `bob randomize` is the bulk version. Using `scheduled` as freshness would hide the task from the dash and mark it Blocked, which is the opposite of “still Ready, skip rereading.”
- **Project frontmatter** — `bob-project-tasks` already materializes `task_count` / `open_task_count`. `Ctrl+Shift+P` already writes project-level `scheduled`. A project-level `refresh:` integer fits that slot.
- **Keymaps** — `Ctrl+Shift+J/K` jump **in the current note** among Ready / Pending / Next. `Ctrl+Shift+P` already has pinned lane and Cancel rows. Alt+N commits/releases. There is no vault-wide “next task that needs a glance” command. `Ctrl+0` opens dash Tasks.

### Historical `@FRESHNESS` (this is the same idea, one layer up)

Zorg already had file-level freshness. Migrated notes still carry it. `now_gtd.md` is typical:

```text
- 241213 241207#0G @FRESHNESS
  * last_refreshed_on::1900-01-01
  * recur::7d
  * tick::2024-12-07
```

Inbox and Keep used `recur::1d`. There were open P0s to add a vim map that updated `last_updated::` and `tick::`. The generated tag page `#context/freshness` still lists 42 notes. `gkeep_inbox`’s original purpose sentence was: *this file’s main purpose is to contain a @FRESHNESS note that reminds me to clear Keep.*

The dash-READY morning habit replaced those file ticks after the Zorg→Obsidian conversion. The new proposal is the same loop (last confirmed + interval + jump + stamp), aimed at Ready **tasks** so a single Keep capture cannot hide inside a file-level “I reviewed `gkeep_inbox`” stamp.

A completed Bob task from 2026-08-03, “Add support for P2 and P3 tasks w/ auto-scheduling and freshness dates,” is a **different** use of the word: it means the P-level scheduled window. Glossary must keep those apart. `bob query` docs also say “vault freshness is owned by `bob vault-sync`”; that is git-sync, not this.

### What OmniFocus got right (and what to steal)

OmniFocus Review is the production version of this loop ([Omni Group, “OmniFocus at School: Reviews”](https://www.omnigroup.com/blog/omnifocus-at-school-reviews); [Inside OmniFocus weekly review](https://inside.omnifocus.com/peter-akkies)):

- Each project has a last-reviewed date and a review frequency (default one week).
- A Review perspective is a **queue of due projects**, with a badge count.
- Mark Reviewed snoozes that project for its interval.
- People who stay sane **spread** reviews across the week rather than clearing a 186-item pile in one sitting.
- Inbox zero is a separate daily step from project review.

GTD’s own weekly review is “get clear (inbox), get current (projects), get creative.” The original proposal collapses inbox-zero and get-current into one stale-task list. Keep the primitive unified; keep the **queues** visually split.

---

## Critique of the original plan

The original plan is right about the failure mode and right about the primitive. It is too coarse in five places.

### 1. Inbox glance and backlog confirmation are different SLAs

Pickup-daughter must surface **tomorrow morning**, every time, until the task is filed or done. A filed `sase.md` cleanup can wait a week. One `[fresh::]` date plus a default 7-day interval gives both behaviors only if inbox notes cannot be snoozed for a week.

If the morning review is “stamp whatever is stale,” a tired pass over `gkeep_inbox.md` that hits Refresh on each line hides the daughter pickup for seven days. That is worse than the old READY grind, because the grind at least kept the item on the page.

**Adjustment:** inbox membership is path-based and daily. Refresh on an inbox task may record a glance for metrics, and it still appears in INBOX tomorrow. Leaving inbox (move, complete, cancel, or a future `scheduled` date) is what clears it.

### 2. Do not require every Ready task to carry the property

“Every ready task have some new property” forces a 186-row backfill on day one and a writer on every capture path. Missing confirmation already means “never glanced.” Capture and `bob gkeep pull` should keep writing only `[created::]`. Hooks should never write freshness (same reason Today is not written onto task lines: unattended passes must not author review state).

Day-one consequence: all 186 Ready tasks are stale. That is honest, and it is also unusable as a daily ritual. Cutover therefore **seeds filed Ready** and leaves inbox unseeded. See [Cutover](#cutover).

### 3. Do not put an unrecognized Tasks field on the `#task` line

Obsidian Tasks (Dataview format), and Bob’s native port in `src/native/dataview/tasks/task.rs`, peel trailing `[key:: value]` fields **right to left** and stop at the first unrecognized key. Recognized keys today are `priority`, `start`, `created`, `scheduled`, `due`, `completion`, `cancelled`, `repeat`, `onCompletion`, `id`, `dependsOn`. `fresh` and `refresh` are not among them. Tasks does not ship custom date fields (obsidian-tasks #2920 was closed as not planned).

If `[fresh:: 2026-09-30]` is the rightmost field, `created` / `scheduled` / `priority` / `id` / `dependsOn` stop parsing. The dash, `bob query`, and dependency handling would go blind on every stamped task. Bob’s own docs already warn about this for invented priority *values* (`docs/projects.md`).

If the field sits *left* of the recognized ones, those still parse, but the unknown field remains in `description` and shows up in dash short mode.

`start` as a stand-in would parse, and it would also distort Tasks urgency and collide with recurrence. A `#fresh/…` tag would be visible noise.

**Adjustment:** store last-confirmed (and the optional per-task interval) on a **managed child bullet**, the same way Schedule Log, Work Log, and Cancel Log already work. The `#task` line stays Tasks-legal. The dash query calls a ledger-tools API, not `description includes`.

### 4. Derived Ready is re-triage; do not stamp it

The request says any change that makes a task Ready, including blocked → ready, should update freshness. Sticky-lane policy says a Blocked task recovering to Ready is **re-triage**. The hooks do that unattended every 15 minutes on the MacBook when a `scheduled` date arrives or a dependency closes. Auto-stamping that pass would hide the newly-doable task for seven days — the same class of miss as an unglanced inbox item.

**Adjustment:** only **human** Bob keymaps stamp. Hooks, `bob gkeep pull`, `bob capture` of new text, `bob projects sync`, and `bob vault-sync` never stamp. Alt+N **release** (Next/Pending → Ready) is a human glance: stamp. Hand unblock (`option+]`) is a human glance: stamp. Schedule-arrival unblock is not.

### 5. `Ctrl+Shift+J/K` cannot be the stale jump

Those chords already mean “next/previous open task **in this note**,” and on a Pomodoro entry they move the entry. Stale Ready tasks currently live in 27 files. The review jump has to be **vault-wide**: resolve the stale set, open the source note, put the cursor on the `#task` line, wrap, and report counts. New commands, new chords. Do not overload J/K.

### 6. Per-project Ready ≤5 is a WIP cap, not freshness

The old habit mixed three policies: glance inbox, confirm backlog, and keep each project’s Ready list small. Freshness does the first two. The third belongs with the weekly prune (or a later lint: “READY in this note >5”). Do not make “stamp fresh” the way a 48-task `sase.md` Ready list gets ignored.

### 7. Recurring chores are already a checklist

Ten dash-visible Ready tasks are recurring; seven live in `gtd_daily.md`. They already appear every day via `repeat` / `scheduled`. Putting them in STALE duplicates the morning chore list.

**Adjustment:** exclude `isRecurring` from STALE. Keep them out of the vault-wide stale jump.

---

## Justified requirement changes

These are the places this research disagrees with a literal reading of the request. Each is a requirement change, not an implementation detail.

| # | Original | Change | Why |
| - | -------- | ------ | --- |
| A | Every Ready task must have a `fresh` date | **Missing means stale.** Writers fill it when a human confirms. | Cutover, inbox, capture, and gkeep stay simple. |
| B | `[fresh:: date]` (and a Dataview interval) on the `#task` line | **Managed child bullet** plus project frontmatter / config interval. Optional `[refresh:: N]` lives on that child, not on the `#task` line. | Tasks right-to-left parser. Dash short mode. Matches Work/Schedule/Cancel logs. |
| C | One stale list covers inbox and backlog | **Two dash sections, one primitive.** INBOX is path-based and daily. STALE is filed Ready past interval. | Pickup-daughter cannot be 7-day snoozed. |
| D | Default interval 7 days for every Ready task | **7 days for filed work. Inbox notes `refresh: 1`.** Config default `plan.refresh_days: 7`. | Historical `@FRESHNESS` already used 1d vs 7d this way. |
| E | Any Ready-making change stamps, including blocked → ready | **Human keymaps stamp. Hooks do not.** Release and hand-unblock stamp. Derived unblock stays stale. | Re-triage policy; unattended hooks must not author review. |
| F | Morning READY grind is replaced by freshness | **Retarget the `gtd_daily` chore** to INBOX → PENDING → NEXT → STALE. READY remains the pull inventory. | READY-as-review is the habit being retired. |
| G | Next/previous out-of-date via existing in-note jump | **New vault-wide commands.** | Stale set is cross-note. |
| H | Daily cap N as a later escape hatch | **Ship counts on day one. Cap only filed STALE, never INBOX.** Default cap off. | Inbox must not be the thing you skip when tired. |
| I | Freshness applies to Ready | **Ready only, plus the exclusions in C/G.** Next/Pending already have a daily 5-minute lane review and a weekly prune. | Do not double-review sticky lanes. |

---

## Alternatives considered

**Keep grinding READY every morning.** Works for pickup-daughter. The user already named the cost: rereading stable tasks, friction, skipped days. Reject.

**Inbox-only dash section, no freshness on filed tasks.** Fixes pickup-daughter with almost no new metadata. Leaves the “I never look at `sase.md`’s 48 Ready tasks” problem to a weekly review that the user does not currently do. Insufficient on its own; keep it as the INBOX half of the design.

**Project-level review only (OmniFocus / old `@FRESHNESS`).** One `fresh:` date on the note, interval on the note, walk projects. Less write churn, better sibling context, matches history. A file-level stamp on `gkeep_inbox.md` is exactly how 65 items go unglanced. Use project-level for **interval defaults**; keep last-confirmed at **task** grain so inbox processing is per capture.

**Use `scheduled` as next-review.** Already means Blocked + hidden from dash. That is a tickler. Freshness must leave the task Ready and pullable.

**Use Tasks `start` date as last-confirmed.** First-class parse, wrong semantics, urgency side effects, recurrence collision. Reject.

**Spaced repetition (7 → 14 → 30 → 90 on each stamp).** Attractive once 7-day STALE is too big. Do not ship it first. Project `refresh:` already covers “this area is someday.” Revisit if the two-week trial fails on time, not on misses.

**A new checkbox status “Needs Review.”** Status is for lanes. Freshness is orthogonal authored metadata. A status would fight hooks and Alt+N.

**Age-based Next decay.** Already rejected by `bob-cli-2y` except as a trial-failure fallback, and never for Pending. Out of scope.

---

## Recommended solution

### Data model

**Last confirmed** is a managed direct child of a `#task` line, newest stamp in place (one bullet, overwritten, not appended):

```markdown
- [ ] #task Pick up our daughter at 7:15 [created::2026-09-30]
	- 🌱 **FRESH**  [on:: 2026-09-30]
```

Optional per-task interval override on the same child:

```markdown
	- 🌱 **FRESH**  [on:: 2026-09-30]  [refresh:: 3]
```

Rules:

- Calendar date, local day, `YYYY-MM-DD`, same strict parser as `created` / `scheduled` (`src/native/task_fields.rs`).
- Absent child ⇒ last confirmed is missing ⇒ stale (if the task is in scope).
- `refresh` on the child is an integer ≥ 0. `0` means “always stale while Ready” (escape hatch for a single hot item). Omit it to inherit.
- Do not put `fresh` / `on` / `refresh` on the `#task` line.

**Interval resolution**, first hit wins:

1. Task child `[refresh:: N]`
2. Note frontmatter `refresh: N` (project or area)
3. `plan.refresh_days` in `~/.config/bob/config.yml` (default **7**)

Seed inbox notes:

```yaml
# gkeep_inbox.md, mac_inbox.md
refresh: 1
```

Someday/maybe notes can set `refresh: 30` or `90` later; do not require it for v1.

A Ready task is **stale** when:

```text
status is TODO
AND not Today
AND not recurring
AND not #hide
AND dash-visible (same TQ filters as READY)
AND (
      path is an inbox note
      OR last_confirmed is missing
      OR today - last_confirmed >= interval
    )
```

Inbox tasks match the first clause every morning regardless of `[on::]`. Filed tasks match the date math.

**Refreshed today** = in-scope Ready tasks whose `[on::]` equals local today. Inbox stamps count here so the morning chip moves even when INBOX does not shrink.

### Glossary strand (new)

Add to the project glossary web via `/sase_memory_write` (Edit And Republish) when the feature ships, not before:

**Task freshness** (aka freshness, stale, last confirmed)

A Ready task is *fresh* when a human has confirmed, on calendar date `[on::]`, that it still needs doing and still looks right (description, priority, parent, schedule). A Ready task is *stale* when that confirmation is missing or older than the task’s refresh interval. Default interval is 7 local days; a task-child `[refresh:: N]` or the note’s `refresh` frontmatter overrides it. Inbox notes use `refresh: 1` and stay in the INBOX queue until the task leaves that note. Freshness is authored by Bob keymaps; `bob task-status-hooks` never writes it.

Disambiguate in the strand body: git-sync “vault freshness”; Zorg `@FRESHNESS` file ticks; P2/P3 scheduled windows.

### Morning process

Order, after the existing weather/email/Keep-pull chores:

1. **INBOX** — every open Ready task in `gkeep_inbox.md` and `mac_inbox.md`. Expected actions: do, move (`Ctrl+Shift+M`) onto a project, schedule (`Ctrl+Shift+P`), commit to Next (Alt+N), or cancel. Refresh is allowed and does not clear the row.
2. **PENDING → NEXT** — unchanged from `bob-cli-2y` (link today’s work, release the rest).
3. **STALE** — filed Ready past interval. Glance, then one of: refresh-only, edit (which stamps), release/commit, defer with a P-level, cancel. Stop when the section is empty or the optional filed-STALE cap is hit.
4. **READY** — pull list when choosing work, not a daily reading assignment.

Replace the `gtd_daily.md` morning-review line accordingly. Keep the weekly prune for lane caps. Add one weekly line only if filed STALE stays red: “clear remaining STALE.” Do not introduce a full GTD weekly review until the daily loop is proven.

Optional later: a per-day cap **N on filed STALE only**, with leftover rolling to the next morning (they remain stale). INBOX is never capped.

### Dash

Keep TODAY / PENDING / NEXT / READY. Add:

| Chip | Value | Target |
| --- | --- | --- |
| INBOX | count of inbox-path Ready | `dash#INBOX Tasks` |
| STALE | `stale/ready` or a single stale count, red when >0 after the morning window | `dash#STALE Tasks` |
| (on STALE heading or chip aria) | `refreshed today: K` | — |

READY chip stays the full filed TODO count so inventory remains visible.

Tasks blocks (headless `bob query` will see empty Today and unfiltered-by-API STALE, same limitation as TODAY today):

```tasks
### INBOX Tasks
not done
path includes gkeep_inbox.md OR path includes mac_inbox.md
status.type is TODO
sort by created
```

```tasks
### STALE Tasks
status.type is TODO
path does not include gkeep_inbox.md
path does not include mac_inbox.md
filter by function API?.isStale?.(task) === true
sort by function API?.staleRank?.(task) ?? 0
```

`staleRank`: missing `[on::]` first, then oldest `[on::]`, then path + line (stable, group-by-path friendly).

Implement the functions on `bob-ledger-tools` `api` as **additive** methods on the existing version 2 object (`isToday` already taught this pattern). Optional chaining keeps an older dash from throwing. Do not invent a second JS implementation in `dash.md`.

### Keymaps (`bob-navigation-hotkeys`)

New commands:

| Command | Suggested chord | Behavior |
| --- | --- | --- |
| Jump to next stale Ready | `Ctrl+Alt+J` | Vault-wide. Opens source note, cursor on the `#task` line, wraps. Notice: `stale 12 · inbox 4 · refreshed today 9`. |
| Jump to previous stale Ready | `Ctrl+Alt+K` | Same set, reverse. |
| Refresh current Ready task | `Ctrl+Alt+R`, and a **pinned row** on `Ctrl+Shift+P` | Upsert the FRESH child `[on:: today]`. No other fields. Counted `N<Ctrl+Alt+R>` stamps the next N in-note Ready tasks. Inbox: notice that it remains in INBOX. |

`Ctrl+Alt+J/K` are unbound in the current `hotkeys.json`. `Ctrl+Shift+J/K` stay in-note / Pomodoro-move. `Ctrl+0` can later grow a sibling “open STALE section” if useful; not required for v1.

**Auto-stamp** (Ready tasks only, after a successful write) on:

- `Ctrl+Shift+P` property writes (scheduled, dependsOn, priority)
- `Ctrl+Shift+M` move (including out of inbox — that is processing)
- Alt+N release to Ready
- `option+]` hand unblock to Ready
- the Refresh command itself

Do not auto-stamp on link/unlink (`Ctrl+Shift+Enter`), capture of new text, gkeep pull, or any hooks pass. Linking raises Next and leaves the Ready review set anyway.

Counted sessions stamp each affected Ready task independently.

### CLI (optional, cutover-only)

A small `bob freshness seed` (or a plugin command) that upserts `[on:: today]` on **filed** dash-visible Ready tasks and skips inbox paths. `--stagger` distributes `[on::]` over the past 7 days by a stable hash of `path#line` so the first week is ~`121/7 ≈ 17` filed STALE per day instead of a 121-item cliff. Dry-run first. Not on `bob nightly`.

Rust should parse/write the child through `task_fields` so seed and the plugin cannot drift. No need for a daily `bob freshness` report in v1; the dash chips are the report.

### Implementation sketch

One epic, four phases, after `bob-cli-2y` rollout (the dash and chores are still moving):

1. **Model + API** — child-bullet grammar, interval resolution, `bob-ledger-tools` `isStale` / `staleRank` / `freshnessBudget()` (`stale`, `inbox`, `refreshedToday`, maybe `filedStale`). Tests: missing child, inbox path, interval 1 vs 7, recurring exclusion, unrecognized-field non-regression on the `#task` line.
2. **Dash + chores** — INBOX / STALE sections and chips; `gtd_daily.md` copy; `refresh: 1` on inbox notes; `plan.refresh_days: 7` in chezmoi `config.yml`.
3. **Keymaps** — jump, refresh, pinned picker row, auto-stamp list above, Notices.
4. **Cutover** — seed filed Ready; Bryan walks INBOX to a small number; two-week trial.

Glossary strand and a short `docs/freshness.md` ship in phase 1–2. Capture/gkeep need **no** format change.

### Cutover

1. Ship the feature with missing = stale.
2. Set `refresh: 1` on `gkeep_inbox.md` and `mac_inbox.md`.
3. Run seed `--stagger` on filed Ready so STALE starts at ~17/day, not 121.
4. Process INBOX as real GTD (65 items). Freshness will keep them in the morning list until that happens; it will not empty Keep for you.
5. Trial, parallel to `bob-cli-2y`’s two-week keep rule: on at least 10 of 14 days, INBOX glance happens, filed STALE is cleared or under a self-chosen cap, morning review (INBOX + lanes + STALE) stays ≤10 minutes, and no known same-day miss of a new capture. If STALE time blows the budget, add a filed cap and a Monday leftover pass **before** changing the default interval.

### Risks

- **Tasks parser:** any future temptation to put `[fresh::]` on the `#task` line. Pin a regression test that a FRESH *child* does not change `created`/`scheduled`/`priority` parse of the parent.
- **Write churn:** ~17–27 child-bullet edits on a typical morning, plus inbox processing. `bob vault-sync` already expects this class of edit. Batch stamps in one undo where the editor allows.
- **API dual implementation:** `isStale` must use the same child grammar in JS (ledger-tools) and Rust (seed). Share fixtures.
- **Inbox pile:** freshness does not shrink 65 Keep tasks. Without inbox processing, every morning still starts with 65 glances. That is GTD working as designed, and it is the first week’s real work.
- **Rubber-stamp:** Refresh-only is for filed tasks that still look right. The pinned picker row should read “Confirm still Ready,” not “Snooze.”
- **Naming collision:** “freshness” already means three other things in this repo. The glossary strand is not optional.

---

## Recommended solution (short)

Build **task freshness** as authored last-confirmed metadata on a managed `🌱 **FRESH**` child, with interval inheritance (task child → note `refresh:` → `plan.refresh_days` default 7). Missing confirmation means stale. Inbox notes are a separate daily INBOX queue that a 7-day stamp cannot hide. Dash chips show stale count and refreshed-today count. New vault-wide `Ctrl+Alt+J/K` jumps and `Ctrl+Alt+R` / `Ctrl+Shift+P` confirm. Human Ready-editing keymaps stamp; hooks, capture, and gkeep do not. Seed filed Ready at cutover; leave inbox unseeded. Retarget the `gtd_daily` morning review to INBOX → PENDING → NEXT → STALE, and leave READY as the pull inventory.

That catches last night’s Keep capture tomorrow morning, stops rereading the other 121 filed Ready tasks every day, and stays inside Bob’s existing Tasks-parser, log-child, ledger-tools API, and keymap patterns.
