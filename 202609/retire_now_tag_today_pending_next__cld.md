# Retire `#now`, make Next and Pending sticky, derive Today: critique and recommendation

- **Research date:** 2026-09-30, day one of the planned `#now` trial (2026-09-30 → 2026-10-13)
- **Researcher:** `cld`
- **Question:** Should Bryan retire the `#now` tag and change the model to this?
  - `bob task-status-hooks` stops demoting Next (`[*]`) and In Progress (`[/]`) tasks.
  - A derived **Today** notion ("tasks linked in today's daily") replaces the demotion.
  - `dash.md` shows mutually exclusive **Today / Pending / Next** sections above Ready.

  If so, should Today be a query-side path filter or a hooks-managed `#today` tag? Critique the plan, adjust the
  requirements where justified, and recommend a solution.
- **Evidence I checked myself:**
  - bob-cli: `docs/task-status-hooks.md`, `docs/plan.md`, `docs/capture.md`, `src/native/task_status_hooks/sync.rs`,
    `src/native/capture_active_tasks.rs`, `src/native/capture_link_tasks.rs`.
  - bob-plugins: surveyed read-only for every `#now`, link and status gesture.
  - The installed Obsidian Tasks 8.4.0 bundle.
  - The live vault: `dash.md`, today's and yesterday's daily notes, `bob.md`, `sase.md`, `gtd_daily.md`,
    `_templates/daily.md`.
  - A dry run of tomorrow's first hooks pass.
  - The decision records `decisions:now-tag-is-user-owned` and `decisions:task-status-is-derived`.
  - Both prior research reports behind `#now`.

---

## Bottom line

1. **Yes, retire `#now`. Your direction is better than the design it replaces, but only with guardrails your plan
   doesn't mention yet.**
   - `#now` fixed the status-lock trap with a **gesture you must remember before you drop a link**.
   - Your plan fixes it with a **default**: unlinking never forgets. The research that justified `#now` argued
     exactly this, that defaults beat intentions.
   - Day one already shows the gesture failing:
     - no `#task` line in the vault carries `#now`;
     - the new "Pick today … + NOW" chore is still open;
     - you expressed this week's bets as a `BETS` Pomodoro, not as tags.
2. **The real cost is that you delete the system's only automatic forgetting.**
   - Today the hooks quietly decay whatever you stop linking. After the change, nothing leaves Next or Pending
     unless you act.
   - In September intake ran at about 2× closures, so Next will grow by several tasks a day unless you release them.
   - Treat these as **required**, not nice-to-have:
     - a visible **cap** on NEXT and PENDING (retarget the existing NOW cap machinery);
     - a **one-key release** gesture;
     - a **weekly prune**.
3. **Make Today query-time, not a `#today` tag.** Today is a fact about the daily note, not about the task.
   - The ledger already is the source of truth, and bob-cli computes this exact set in three places.
   - A machine-written tag would copy that fact onto about 10 task lines a day in hand-edited notes like `sase.md`,
     up to 15 minutes late unless every link writer learns the tag.
   - Expose the set from `bob-ledger-tools` and filter the dash queries with it.
   - The one real engineering problem is refresh: Tasks only re-renders when a note's *tasks* change, so the plugin
     must nudge the dash when only links change.
4. **Adjust one requirement: Today = Task Links under today's *open* Pomodoros, not "anywhere in today's daily
   file".** Your own swarm scenario needs this. Closed sessions keep their 🍅 links, so under the whole-file
   definition a task you worked this morning could never leave Today until midnight.
5. **Act before tomorrow morning.** Suppose tomorrow's ledger carries today's four open entries. The first hooks
   run after the 2026-10-01 daily note exists will demote **48 `[/]` and 25 `[*]` tasks** to Ready. With zero
   `#now` tags, nothing will mark them. Either pause the Mac hooks cron job until the sticky-status change lands, or
   accept the reset and re-promote from the list in the appendix.

---

## 1. What I verified

| Claim | Evidence | Consequence |
|---|---|---|
| `#now` is unused on day one | `grep` over the vault finds `#now` only inside `dash.md`'s own query. NOW = 0 via the dash's own query defaults. | Retiring it migrates no data |
| The morning pick hasn't happened | `gtd_daily.md`: "Pick today: ≤3 themes from yesterday + NOW" is still `[ ]` (scheduled 2026-09-30) | The new habit hasn't started either. Evidence that the pre-drop gesture is friction. |
| You already model "bets" in the ledger | Today's note has open `BOB`, `CLEANUP`, **`BETS`** and `GTD`: 4 entries, 7 links. Yesterday had 21 open entries and 92 links. | Stopping migration worked on the first try. Tagging didn't happen. |
| You already rejected a separate "submitted" status | `bob.md` `^submitted-status` was cancelled today: "No need for this. WIP status should fill this role." | Pending = `[/]` matches your stated intent |
| The dash duplicates tasks today | `bob.md` `^improve-gtd-process`: "WIP and Next sections should not show `#now` tasks!" | Your plan's mutual exclusivity answers a complaint you already logged |
| Dash counts today | Dash defaults: WIP **53**, NEXT **27**, READY **186**, NOW **0** | Starting with sticky statuses means starting with about 80 committed tasks, which is over any sane cap |
| Tomorrow's decay | `BOB_DAY_FILE=<copy of today's open entries as 20261001.md> BOB_NOW=2026-10-01 bob task-status-hooks --dry-run -f json` → `cleared_in_progress` **48** (39 in `sase.md`) and `cleared` **25** | These are the statuses your plan wants to keep. The appendix lists them. |
| When the decay fires | The Mac cron runs hooks at `:10,:25,:40,:55`. The command exits without writing when the current daily note is missing (`docs/task-status-hooks.md`, Guard rails). | The first demoting run follows the creation of tomorrow's daily note (about 06:00) |
| The hooks change is small | `sync.rs::transition()` returns `Clear` for a `[*]` with no desired status. `task_transition()` returns `ClearInProgress` for the area/project rollback. | Stickiness is roughly two branches plus tests and docs |
| bob-cli already has your section order | `capture_active_tasks.rs` / `docs/capture.md`: picker groups in precedence `queued` (a dedicated link under an open Pomodoro today) > `in_progress` > `next` > `now` > `note` | That is Today > Pending > Next > (Ready) already, mutually exclusive by precedence |
| "Linked today" has several definitions | Hooks: all open Pomodoros plus dependency closure. Plan budget: open, non-exempt entries. Picker: dedicated links under open Pomodoros. bob-plugins NAV recovery: today **and** yesterday, including completed Pomodoros. | Define Today once, in `docs/plan.md`, with shared JS/Rust conformance vectors like the plan budget has |
| Ctrl+Shift+Enter uses **status** as the link toggle | bob-plugins BIP `openPomodoroTaskLink`: `[ ]`/`[?]` → link + `[*]`; `[*]` → unlink + `[ ]`; `[/]` → Work Log prompt, unlink + `[ ]`. On a link line, `applyTaskLinkOpen` also demotes. | This breaks as soon as Next is sticky: a sticky `[*]` that isn't linked today would be demoted instead of linked. It must become a link-presence toggle. |
| `#now` code size | bob-plugins: about 900 lines in navigation-hotkeys, about 235 in ledger-tools, about 500 in tests (6–8 files). bob-cli: `#now` code in about 20 Rust source files plus tests (capture grammar, completion, picker groups, close/start rows, plan budget, config). Mac capture renders `now` fields and captions. | A real but mechanical removal. Much of it (caps, chip, meter, lint) can be **retargeted** to NEXT, not deleted. |
| Tasks `filter by function` can call plugin APIs | Tasks 8.4.0 compiles expressions with `new Function(...)`, so globals such as `app` and `moment` are in scope. The dash already relies on `filter by function` and `moment()`. | A query-side Today filter needs no Tasks change |
| Tasks re-renders only on task changes | Tasks' `Cache.indexFile` calls `notifySubscribers()` only when `!listsAreIdentical(old, new)` | Adding or removing a link line (no task change) leaves the dash stale. Plan for a refresh (§4). |
| Transcluded dependencies are mostly reading tasks | About 280 whole-bullet `![[…#^…]]` edges, most of them under old dailies or pointing at `ref/…#^ref` reading tasks tagged `#hide` | Sticky dependency promotion rarely inflates the visible dash |
| Daily-note tasks rarely linger | The only open `#task` in any daily note is today's `^gtd` | A daily-note carve-out from stickiness is cheap insurance, not a big behavior change |

---

## 2. Critique: is this a good idea?

### 2.1 What the plan gets right

- **It removes the hoarding incentive by construction.**
  - The trap: unlinking demoted a task and nothing remembered it, so you kept everything linked, and the ledger
    grew to 92 links.
  - `#now` answered that with a second marker you had to apply *before* dropping. Under your plan, dropping is
    free: the task stays Next or Pending.
- **It's one axis plus one derived fact, instead of three overlapping "soon" markers.**
  - Before: `[*]` (linked today), `[/]` (worked in the last day or so) and `#now` (weekly promise). All three
    answered some version of "what should I do soon?", which is why the dash showed tasks twice.
  - After: the checkbox answers **how committed or how far along** (Ready → Next → Pending), and the ledger answers
    **whether it's on today's plan** (Today).
- **The review order is right.**
  - Pending → Next → Ready is Kanban's pull policy: "stop starting, start finishing".
  - Pending is also GTD's Waiting-For list, reviewed daily, which covers the agent-swarm case.
- **Much of it already exists.** The capture picker's precedence, the hooks' monotonic promotion, and the NOW
  cap/chip/meter/lint plumbing can all be retargeted.

### 2.2 Where it's weaker than it looks

1. **No more automatic forgetting.**
   - Every task you link, including every `@route:id` capture (91% of queued links entered the ledger on the day the
     task was created), becomes sticky Next until you finish, release, defer or cancel it.
   - At about 10 links a day in and about 5 closures a day out, Next grows by about 5 a day, roughly 70 in two weeks.
   - The pile moves from the ledger to the statuses. It becomes visible there, but it doesn't disappear.
   - `#now` had the same property, but it also had a cap and a weekly re-tag.
2. **It depends on a daily review, the exact habit that lapsed.**
   - "Review WIP + NEXT … plan daily Pomodoros" was last done on 2026-09-09.
   - The review only survives if it stays short (capped lists) and each decision is one key.
3. **Next now mixes "committed" with "linked once in passing".**
   - Reactive work (`SHIT`, `FIXES`, `RELAUNCH` blocks) that you link for an hour becomes a standing commitment
     unless you complete or release it.
   - That's acceptable only if releasing is as cheap as linking.
4. **`[/]` stops meaning "worked recently".** The WIP chip no longer measures activity, and a Pending task's age is
   invisible. That's fine for the agent-swarm case, but "Pending since 12 days" should eventually be visible
   (Phase 2 stale report).
5. **It reverses two decision records that are one day old.**
   - `now-tag-is-user-owned` is retired entirely.
   - `task-status-is-derived` is narrowed: Blocked stays derived, but Next and In Progress become
     "promoted automatically, demoted only by a gesture".
   - Records are immutable once accepted, so this needs new superseding records written through
     `/sase_memory_write`, not edits.
   - Note that the earlier research's own fallback, "if NOW is ignored, delete the tag and keep decay", would bring
     back the hoarding incentive. Your variant is the better fallback.

### 2.3 What you actually lose (a longer list than "a link without `#now`")

| Lost | Severity | Mitigation |
|---|---|---|
| Linking without committing | Low (you accept it) | Release at `=x` time, or Alt+N afterwards |
| Automatic decay of stale Next and In Progress | **High** | Caps and red chips, a weekly prune, a Phase 2 stale report |
| `[/]` as a recent-activity signal | Medium | Phase 2: days since the last 🍅, computed from the dailies |
| Capture's "this week, not today" intent (`#now … ^`) | Low (unused so far) | Link with `:` then unlink, or Alt+N in the review. Add a capture token only if you miss it. |
| Ctrl+Shift+Enter as "unlink and demote" in one key | Medium | Split it: Ctrl+Shift+Enter becomes link/unlink only; Alt+N becomes release (§6) |
| Commitment across a Blocked period | Low to medium | A Blocked task recovers to its derived rank (Ready unless recently linked), not to its pre-block Next or Pending state. This already happens today but will be more noticeable. Defer = "not now", so returning as Ready is right. Revisit the dependency case only if it bites. |
| Two horizons (week vs. today) | Low | Next is the week; Today is the day; P-levels are later |

### 2.4 Would I take a different approach?

- **Not a fundamentally different one.** I considered and rejected these:
  - **Keep `#now` and just de-duplicate the dash sections.** Cheapest, but it keeps the gesture that isn't
    happening. It also lets 73 statuses decay tomorrow with nothing tagged.
  - **A Today checkbox status.** Impossible without hidden memory. A Pending task linked today would have to
    overwrite `[/]` and then "remember" it at unlink. The Blocked design already rejected hidden previous-status
    fields for this reason.
  - **Age-based decay for Next**, e.g. back to Ready after N days without a 🍅.
    - It's a reasonable *later* guardrail if the weekly prune fails.
    - Never apply it to Pending: you explicitly want Pending never wiped.
    - It would also need a multi-day ledger lookback that the hooks don't have today.
  - **A separate Waiting/Submitted status for agent work.** You already cancelled it. Pending plus a one-line Work
    Log note at unlink ("swarm running epic X; review tomorrow") covers it.
- **Where I differ from your sketch:** Today is query-time, it is scoped to open Pomodoros, and the guardrails
  are part of the design rather than follow-ups.

---

## 3. Adjusted requirements (my changes are marked **ADJ**)

| # | Requirement | Source |
|---|---|---|
| R1 | Retire `#now`: tag semantics, capture token, Alt+N toggle, picker row, NOW chip, section and meter | yours |
| R2 | Hooks never demote `[*]` or `[/]` because a link disappeared. They still promote `[ ]` → `[*]` on link, `=x` still makes `[/]`, and Blocked stays derived and overriding. | yours |
| R3 | Pending (`[/]`) is never wiped by automation | yours |
| R4 | Dash sections Today / Pending / Next (then Ready) are mutually exclusive, with precedence Today > Pending > Next > Ready | yours; **ADJ:** Ready also excludes Today, so a hand-typed link doesn't show a task twice before promotion |
| R5 | **ADJ.** Today = tasks with a Task Link under today's **open** Pomodoros (all open entries, GTD included; direct links only; struck links excluded). It is not "any link in today's file". | your swarm example requires it; it matches the hooks, plan budget and picker |
| R6 | **ADJ.** Today is computed at query time from the ledger. It is never written to task lines. | §4 |
| R7 | **ADJ.** Stickiness excludes tasks that live in canonical daily notes (today's `^gtd`), which keep the current derived clearing | avoids a stale `[*]` per unfinished day |
| R8 | **ADJ.** Visibility caps: `plan.max_next` (default 15, the renamed `max_now`) and `plan.max_pending` (default 10). Counts are status ∧ ¬Today under the dash defaults. They show as red chips, `bob plan` meters and lints (`next_cap_exceeded`, `pending_cap_exceeded`), and never refuse anything. | the replacement for decay |
| R9 | **ADJ.** Gestures: unlinking never changes status, and one explicit key releases Next or Pending → Ready (§6) | makes R2 livable |
| R10 | **ADJ.** Unlinking a Pending task offers the existing Work Log prompt (blank skips) as a "why is this pending" note | turns the swarm case into a reviewable record |
| R11 | **ADJ.** Rituals: daily review Pending → Next → Ready (≤ 5 minutes); weekly prune of NEXT and PENDING to their caps, replacing the NOW re-tag | review is the only exit path now |
| R12 | **ADJ.** Keep the `[/]` symbol and `IN_PROGRESS` type. Label the section "Pending" and rename the registry name only if you want to. | avoids churning queries and highlights sync |
| R13 | **ADJ.** Supersede both decision records with new ones before or alongside the code | the decisions web's immutability rule |

---

## 4. How to implement Today

| | **A. `#today` tag managed by hooks** | **B. Query-time via a `bob-ledger-tools` API (recommended)** | C. Inline `app.metadataCache` JS in the dash | D. DataviewJS that generates Tasks blocks |
|---|---|---|---|---|
| Source of truth | A copy on task lines | The ledger itself | The ledger | The ledger |
| Freshness | Up to 15 minutes, unless **every** link writer also writes the tag (capture link, `=x` carry and drop, start drops, Ctrl+Shift+Enter, `^^`, deferral prune, Cancel, hand edits) | Instant computation; needs a dash refresh nudge (below) | Same staleness as B, with no fix | Dataview auto-refresh re-runs it |
| Writes | About 2 edits per task per day in `sase.md` and other hand-edited notes; git and sync churn; races with open editors | None | None | None |
| Parser and archive risk | Tag placement rules; a completed task archived with `#today` keeps it forever unless stripped at completion | None | None | None |
| Convention | A tag you must never type (hooks strip it). Conflicts with the vault's "tags are user markers" convention (`#hide`, `#inbox`, the retired `#now`). | Fits | Fits | Fits |
| Open-Pomodoro accuracy | Exact (hooks already compute it) | Exact (reuses the plan-budget entry model) | Hard: nested list and section logic on one query line | Exact, if it uses B's API |
| Headless (`bob query`, agents) | Works | Needs `bob plan -f json` to list `today_tasks` | No | No |
| Mobile | Works (text) | Works: plugins are `isDesktopOnly: false` | Works | Works |
| Complexity | Hooks, capture and plugins all learn a tag | One API, three filter lines, one refresh hook | Long, brittle one-liners | A hack stacked on a hack |

**Recommendation: B.** Expose Today from the plugin that already models the ledger in JavaScript, and keep Rust as
the reference definition.

- **API** (`bob-ledger-tools`, `api.version` 2):
  - `todayKeys(): Set<"path#blockId">`
  - `isToday(task): boolean`, taking a Tasks task and matching `task.path` plus the ID from `task.blockLink`
  - `todayRank(task): number`, for ledger-order sorting
  - `nextBudget()` / `pendingBudget()`, replacing `nowBudget()`
- **Computing the set:** reuse `computePlanBudget`'s entry model (it already keys links as `target\0blockId`), but
  include exempt `GTD` entries. Resolve each target with `metadataCache.getFirstLinkpathDest(target, dailyPath)`,
  which ledger-tools doesn't do yet.
- **Caching:** the cache must be **synchronous**, because Tasks can't await inside `filter by function`. Refresh it
  on `vault` `modify`/`create` for today's daily note and on day rollover.
- **Refresh:** when the key set changes, nudge open Tasks queries to re-render. The least-internal route still
  needs a spike: re-trigger Tasks' `obsidian-tasks-plugin:cache-update` event with `getTasks()`, or re-render the
  leaves showing `dash.md`.
  - Without this, pulling a Pending task into today leaves it in the Pending section until the next task edit.
  - That would be a visible bug in the one workflow this redesign is for.
- **Failure mode:** if the plugin or API is missing, `isToday` returns `undefined`.
  - The Today section is then empty, and Pending, Next and Ready show everything.
  - Nothing disappears; you only get duplicates.
- **Rust side:** define Today once in `docs/plan.md`, next to the plan budget:
  - add `today_tasks` to `bob plan -f json` for agents and headless use;
  - reuse the same definition for the capture picker's `queued` group;
  - share conformance vectors with the JS mirror.

---

## 5. Status rules after the change

These are changes to the `docs/task-status-hooks.md` precedence table. The Changed column marks the rows that move.

| Existing | Condition | Result | Changed? |
|---|---|---|---|
| done, canceled, non-task, unknown | any | unchanged | no |
| `[ ]`, `[*]`, `[/]` | open dependency and/or future `scheduled` | `[?]` | no |
| `[?]` | no blocking reason | derived recovery rank (Next if directly recent, In Progress via a stronger path, else Ready) | no (see §2.3) |
| `[ ]` | directly linked under today's open Pomodoros, or a dependency of such a task | `[*]` | no |
| `[ ]` / `[*]` | desired In Progress on a dependency path | `[/]` | no |
| `[*]` | unreachable | **unchanged** (was `[ ]`); still `[ ]` for tasks in canonical daily notes | **yes** |
| `[/]` in an area/project note | no recent activity | **unchanged** (was `[ ]`) | **yes** |

- Everything structural stays: dedupe, canceled-link removal, completed-link retirement, empty-Pomodoro deletion,
  🍅 repair and status grouping.
- The previous-daily "recent activity" machinery survives only to feed Blocked recovery rank. The `KeptNext` grace
  path becomes moot.

---

## 6. Gestures after the change

| Gesture | Effect on Today | Effect on status |
|---|---|---|
| **Link**: Ctrl+Shift+Enter on a task line that isn't linked today; `^^`; capture `@route:id` / `^route:id`; the Mac `^` picker | joins Today | `[ ]`/`[?]` → `[*]`; `[*]` and `[/]` unchanged (today `[/]` can't be linked this way, so fix that) |
| **Unlink**: Ctrl+Shift+Enter on a link line, or on a task line that is linked today; `=x~K`; `=~K`; deleting the line by hand | leaves Today | **unchanged**; unlinking a `[/]` task offers the Work Log note (R10) |
| `=x` worked / deferred / `!M` | carried / carried / leaves | → `[/]` / unchanged / done |
| **Release**: Alt+N, repurposed from the `#now` toggle ("N" for Next); a Ctrl+Shift+P row in the `#now` row's slot | leaves Today if linked | `[*]` → `[ ]`; `[/]` → `[ ]` via the Work Log prompt |
| **Commit without today**: Alt+N on a Ready task | none | `[ ]` → `[*]` |
| Defer (Ctrl+Shift+P P1–P4 or a date; capture `p:N`) | pruned | → `[?]`; returns as Ready (unchanged) |
| Cancel | pruned | `[-]` (unchanged) |

- The key behavioral change is in bob-plugins' BIP: Ctrl+Shift+Enter must branch on **whether the task is linked
  under today's open Pomodoros**, not on its checkbox.
- Update the Notice copy from "Next tasks become Open" to "unlinked · stays Next". Update the `=x` drop row text
  from "the next hooks run demotes Next → Ready; `#now` keeps it in view" to "stays Next/Pending".

---

## 7. The dash

- **Chips:** `TODAY n` · `PENDING n/10` · `NEXT n/15` · `READY n` · `BLOCKED n` · `PLAN t/3 · l/10`.
- **Sections:** in chip order. Keep the existing `TQ_extra_instructions` defaults (not blocked, not `#hide`, not
  future-scheduled, not `_templates`).

````markdown
### Today Tasks

```tasks
not done
filter by function app.plugins.plugins["bob-ledger-tools"]?.api?.isToday?.(task) === true
sort by function app.plugins.plugins["bob-ledger-tools"]?.api?.todayRank?.(task) ?? 0
```

### Pending Tasks

```tasks
status.type is IN_PROGRESS
filter by function !app.plugins.plugins["bob-ledger-tools"]?.api?.isToday?.(task)
sort by created
```

### Next Tasks

```tasks
status.name includes Next
filter by function !app.plugins.plugins["bob-ledger-tools"]?.api?.isToday?.(task)
sort by priority
```

### Ready Tasks

```tasks
status.type is TODO
filter by function !app.plugins.plugins["bob-ledger-tools"]?.api?.isToday?.(task)
```
````

- **Sort choices:** Pending sorts oldest-created first, so long-running in-flight work surfaces. Next sorts by
  priority.
- **Project notes:** the `### Next & In Progress` groups stay correct unchanged. They become each project's
  committed list.

---

## 8. Change surface by repository

| Repo | Change | Size |
|---|---|---|
| bob-cli (hooks) | Remove the `[*]` Clear branch outside daily notes; remove `ClearInProgress`; update tests and the docs table and "Rolling Recent Activity" text | Small. **Ship this first.** |
| bob-cli (plan) | Define Today in `docs/plan.md`; add `today_tasks` to `bob plan -f json`; replace the NOW meter, `max_now` and `now_cap_exceeded` with NEXT/PENDING meters, caps and lints; update `plan_budget` in the hooks JSON | Medium; mostly retargeting |
| bob-cli (capture) | Remove the `#now` token (markers, editor spans, `now_tag` completion, the usage error), the picker's `now` group, the `tasks[].now` / `pomodoro_start` `now` fields and the "stays in NOW" captions; update `=x~K` docs; reword the plan warning ("…queue it with ^, or defer with p:<N>") | Medium, mechanical |
| bob-plugins | Remove `#now` (about 1.6k lines including tests); add the ledger-tools Today API, budgets and refresh; make Ctrl+Shift+Enter a link-presence toggle; retarget Alt+N and the Ctrl+Shift+P row to release/commit; reword Notices | Medium to large |
| bob-mac-capture | Drop the `#now` palette span and captions; tolerate the absent `now` fields and group | Small; coordinate the contract (thin-client rule) |
| Vault | `dash.md` chips and sections; `gtd_daily.md` pick and weekly-review wording; `config.yml` `plan.max_next` / `max_pending` | Small |
| Memory | New decision records superseding `now-tag-is-user-owned` and narrowing `task-status-is-derived` (through `/sase_memory_write`) | Small |

---

## 9. Migration: tonight's decision

Suppose you carry today's open entries forward. The first hooks run after tomorrow's daily note appears will then
reset 48 `[/]` and 25 `[*]` tasks (appendix). Those include "Revoke leaked Telegram token", "Release v0.18.0" and
"Fix failing sase (schema mismatch)". Two acceptable paths:

- **Recommended: pause, then triage once.**
  - Comment out the `task-status-hooks` line in the Mac crontab tonight (`docs/vault-git-sync.md` has the backup
    and restore procedure).
  - Ship the sticky-hooks change (Phase 1a below).
  - Then triage the dash once, down to the caps (≤ 10 Pending, ≤ 15 Next); release everything else with the new key.
  - Resume the cron job.
  - Cost: a day or two without automatic Blocked recovery and ledger cleanup. `=x` and the keymaps still apply
    their immediate status changes.
- **Acceptable: let it reset.**
  - Treat the decay as the triage. Everything becomes Ready, and nothing leaves its note.
  - Once sticky hooks ship, re-promote the few real keepers from the appendix, the hooks log
    (`/var/tmp/bob_task_status_hooks.log` lists every clear), or the run's recovery directory.
  - Don't re-promote before Phase 1a lands: the current hooks would reset them again.

Either way, **skip the `#now` tagging step** of the old Phase 0, and reword the two `gtd_daily.md` chores that point
at `dash#NOW Tasks`.

---

## 10. Risks

- **NEXT goes red and stays red.**
  - This is the expected failure. First make the weekly prune stricter.
  - Then consider age-based Next decay (never Pending), or a capture-time default of "release on `=x` drop".
- **The review lapses again.**
  - Then this model fails the same way the old one did, only more visibly.
  - Keep the review ≤ 5 minutes and let the chips nag.
- **Dash staleness.** If the refresh nudge proves fragile, fall back to re-opening the dash, or have DataviewJS
  render the three sections (option D).
- **Several definitions of "today".** Fold them into one documented definition with shared test vectors. Otherwise
  the picker, the hooks, the chips and NAV recovery will disagree at the edges (GTD entries, dependency closure,
  closed sessions).
- **Three-repo contract churn** for a design that is one day old. Sequence it so each step is useful on its own
  (below).

---

## Recommended solution

**Retire `#now`. Let the checkbox say how committed a task is and the ledger say whether it's today. Replace decay
with caps and a one-key release.**

1. **Tonight (no code).**
   - Pause the Mac `task-status-hooks` cron job, or accept the reset (§9).
   - Don't tag anything `#now`.
2. **Phase 1a: bob-cli hooks, small, first.**
   - `[*]` and `[/]` are never demoted for lack of a link, except for tasks in canonical daily notes.
   - Promotion, `=x` → `[/]`, derived Blocked and all ledger cleanup are unchanged.
   - Write the superseding decision records alongside, through `/sase_memory_write`.
   - Resume the cron job and triage to the caps.
3. **Phase 1b: define Today once.**
   - Today = direct, non-struck Task Links under today's **open** Pomodoros, including GTD.
   - Document it in `docs/plan.md` with shared vectors.
   - Add `today_tasks` to `bob plan -f json`.
   - Retarget NOW → NEXT/PENDING meters, caps (15/10) and lints.
4. **Phase 1c: bob-plugins and the dash.**
   - Add the `bob-ledger-tools` Today API (synchronous cache plus a Tasks refresh nudge).
   - Rebuild the dash as Today / Pending / Next / Ready with the chips from §7.
   - Make Ctrl+Shift+Enter link/unlink only, with the Work Log note when unlinking Pending.
   - Make Alt+N and the Ctrl+Shift+P row release/commit.
   - Remove `#now`.
5. **Phase 1d: capture and Mac cleanup.** Remove the `#now` token, the `now` group and fields, and the NOW
   captions; update the `=x~K` wording. Coordinate the removals across both repos.
6. **Phase 2, only if the trial asks for it:**
   - a stale report (days since the last 🍅 for Pending and Next);
   - a capture spelling for "commit without today";
   - age-based Next decay.
7. **Trial:** two weeks from when Phase 1c lands.
   - **Keep it if:**
     - PENDING ≤ 10 and NEXT ≤ 15 on at least 10 of 14 days;
     - the morning review runs on at least 10 of 14 days, in 5 minutes or less;
     - releases happen, i.e. the gesture is actually used;
     - the PLAN chip is mostly green.
   - **If NEXT stays red,** tighten the weekly prune before adding any decay.

---

## Appendix: tasks the first 2026-10-01 hooks run would demote

This comes from a dry run that assumed tomorrow's ledger carries today's four open entries (`BOB`, `CLEANUP`,
`BETS`, `GTD`). Use it for the §9 triage.

**`[/]` → `[ ]` (48).**

- `bob`:
  - `^better-capture-stop`
  - `^capture-stop`
  - `^solo-id-capture`
  - `^better-roadmaps`
- `sase`:
  - `^fix-telegram-leak`
  - `^fix-v-key`
  - `^release-v18`
  - `^better-sidebar`
  - `^agents-sub-tabs`
  - `^recovery-panel`
  - `^final-ux`
  - `^fix-schema-mismatch`
  - `^p-key-for-decks`
  - `^quote-keymap`
  - `^card-blocks`
  - `^xprompt-in-header`
  - `^routine-groups`
  - `^bead-triage-job`
  - `^fix-muse-waits`
  - `^agent-clan-summaries`
  - `^usage-service`
  - `^harden-services`
  - `^dot-separators`
  - `^clean-core`
  - `^critique-research-swarm`
  - `^output`
  - `^bead-art-links`
  - `^just-fix-tui-screenshots`
  - `^tui-speedup-again`
  - `^tui-screenshot`
  - `^stale-epic-approved`
  - `^better-sbd-alias`
  - `^services`
  - `^fix-claude-monitors`
  - `^work-kills-waiting`
  - `^fast-tests`
  - `^comma-big-h`
  - `^read-final-research`
  - `^green-check-full`
  - `^stop-wait-renames`
  - `^q-weight`
  - `^sudo`
  - `^hold`
- One each:
  - `sase_agent_history#^read-research`
  - `sase_clean#^work-all-beads`
  - `sase_goals#^epic-roadmap`
  - `sase_pager#^fix-file-follow`
  - `sase_remote#^use-sase-screenshot-to-fix`

**`[*]` → `[ ]` (25).**

- `bob`:
  - `^web-capture`
  - `^capture-project-files`
- `sase`:
  - `^no-more-index-lock`
  - `^stash-trash`
  - `^target-alias-providers`
  - `^light-prompt-history`
  - `^tui-cli`
  - `^node-finder`
  - `^agent-renames`
  - `^multi-line-alternations`
  - `^bead-read`
  - `^fix-agent-tab-snap`
  - `^web-piw-completion`
  - `^improve-monitors`
  - `^bulk-gate-cmds`
  - `^fast-tale-status`
  - `^q-weight-phases`
  - `^q-weights-prj`
  - `^q-weight-cap`
  - `^schedule`
  - `^q-weights-metadata`
- `sase_art_links#^artifact-event-store`
- `sase_memory`:
  - `^feature-flags`
  - `^review-sase-art`
  - `^memory-beads`

---

## Sources

**Local evidence (read-only):**

- bob-cli:
  - `docs/task-status-hooks.md` (Sync Rules, Rolling Recent Activity, the precedence table, Guard rails);
  - `docs/plan.md` (NOW query, caps, surfaces);
  - `docs/capture.md` (the `=x` outcome table, `~K` drop, picker groups, `#now` grammar);
  - `docs/vault-git-sync.md` (Mac cron schedule);
  - `src/native/task_status_hooks/sync.rs` (`task_transition`, `transition`);
  - `src/native/capture_active_tasks.rs` and `src/native/capture_link_tasks.rs` (queued, in_progress, next and now
    groups);
  - a `grep` for `#now` / `has_now_tag` / `max_now`.
- bob-plugins, read-only survey of these plugins:
  - `plugins/block-id-prompt/main.js` (`openPomodoroTaskLink`, `applyTaskLinkOpen`);
  - `plugins/bob-navigation-hotkeys/main.js` (Alt+N, the Ctrl+Shift+P `#now` row, recovery ranking);
  - `plugins/bob-ledger-tools/main.js` (`api`, `computePlanBudget`, `nowBudget`);
  - `plugins/task-status-cycler/main.js`;
  - manifests (`isDesktopOnly: false`).
- Vault:
  - `dash.md`;
  - `2026/20260929.md`, `2026/20260930.md`;
  - `bob.md` (`^submitted-status`, `^improve-gtd-process`);
  - `sase.md`, `sase_goals.md`, `gtd_daily.md`, `_templates/daily.md`;
  - `.obsidian/plugins/obsidian-tasks-plugin/` (`data.json` status registry; `main.js` 8.4.0: `new Function`
    evaluation, `listsAreIdentical` notify guard);
  - live `bob query --tasks` counts;
  - a `bob task-status-hooks --dry-run -f json` simulation for 2026-10-01.
- SASE memory: `decisions:now-tag-is-user-owned`, `decisions:task-status-is-derived`, and the glossary terms
  Pomodoro, Task Link, Schedule Log and Work Log.
- Prior research:
  - `research:202609/pomodoro_closed_day_now_tag_automation/pomodoro_closed_day_now_tag_automation.md`: the
    status-lock trap, the 2:1 intake ratio, the throughput of about 3 themes a day, "defaults beat intentions", the
    `#now` rationale;
  - `research:202609/now_tag_vs_in_progress_status.md`.

**Method references** (carried from the prior report, which cites them in full):

- Benson & DeMaria Barry, *Personal Kanban* (visualize work, limit WIP), and Little's Law (Kanban University,
  2022): <https://kanban.university/wp-content/uploads/2022/09/Exploring-Littles-Law-KGS-2022.pdf>.
- Allen, *Getting Things Done*: the daily and weekly review and the Waiting-For list.
- Webb & Sheeran (2006): changing intentions changes behavior only weakly.
  <https://pubmed.ncbi.nlm.nih.gov/16536643/>.
- Jachimowicz et al. (2019): default effects meta-analysis.
