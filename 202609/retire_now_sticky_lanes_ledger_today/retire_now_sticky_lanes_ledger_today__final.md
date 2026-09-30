# Retire `#now`: sticky Next/Pending lanes and a Today set derived from the ledger

- **Date:** 2026-09-30 (day one of the planned `#now` trial, 2026-09-30 → 2026-10-13)
- **Question:** Was `#now` a mistake? Should `bob task-status-hooks` stop keeping Next `[*]` and WIP `[/]` in sync
  with today's Task Links, should `dash.md` move to mutually exclusive Today / Pending / Next sections (then Ready),
  and should Today come from a file-path filter or a hooks-managed `#today` tag?
- **Inputs:** five independent reports, all in this directory (`__cdx`, `__cld`, `__grk`, `__mus`, `__gem`), plus
  my own checks of:
  - bob-cli: hooks transition code, capture docs, the native query engine;
  - bob-plugins: `bob-ledger-tools`, `block-id-prompt`;
  - the installed Obsidian Tasks 8.4.0 bundle;
  - the live vault;
  - a dry run of tomorrow's hooks pass;
  - September's daily ledgers;
  - the two decision records and the `#now` plans.

---

## Bottom line

1. **Yes, retire `#now`. Your direction is better than the design it replaces.** Three of the five reports agree
   (cdx, cld, gem). grk and mus want to keep `#now` through its trial. I side with retiring it, for these reasons:
   - The `#now` design protects work only if you remember a gesture *before* dropping a link. Your design protects
     it *by default*: unlinking never forgets. The research that justified `#now` argued that defaults beat
     intentions.
   - It leaves each marker with one job:
     - the ledger says what is **Today**;
     - the checkbox says which **lane** a task is in (Ready → Next → Pending);
     - dependencies and schedules say whether it is **actionable**.
   - Under the "keep `#now`" alternative, derived `[*]` would just repeat the Today set. grk concedes the NEXT
     section would then go away.
   - Your own behavior already points this way:
     - The one bulk `#now` tagging covered exactly the 73 `[/]` and `[*]` tasks (48 + 25), and those tags were
       stripped the same day.
     - You cancelled a separate "submitted" status with the note "WIP status should fill this role".
     - You logged "WIP and Next sections should not show `#now` tasks!".
2. **Neither of your two Today mechanisms is the right one. Derive Today from the ledger when the dash renders.**
   - **A file-path filter can't answer the question.** It selects tasks that *live in* the daily note, not tasks
     *linked from* it. Two reports ran it live: 1 result, the `^gtd` task.
   - **A `#today` tag would work but is the wrong design.** It keeps a second copy of the ledger on task lines and
     rewrites line text every 15 minutes.
   - gem argues the tag is required because a query can't see links. That premise is false. Tasks evaluates
     `filter by function` with `new Function`, so it can call a plugin API. The dash already calls
     `bob-ledger-tools` from DataviewJS.
3. **The real cost is losing automatic forgetting.**
   - Nothing will leave Next or Pending unless you act.
   - At September's rates the lanes grow about **2–3 tasks a day, 15–20 a week**.
   - So caps, a one-key release and a weekly prune are required parts of the design, not follow-ups.
4. **Four requirement adjustments, marked ADJ in §4:**
   - Today means links under today's **open** Pomodoros, not "anywhere in today's daily file".
   - Every unlink gesture must preserve the lane, not only the hooks.
   - Explicit release is a separate key.
   - A blocked or deferred task comes back as Ready (re-triage), not to its old lane.
5. **Decide before about 06:00 on 2026-10-01.**
   - I reproduced cld's dry run. The first hooks pass after tomorrow's daily note exists will demote **48 `[/]` and
     25 `[*]`** tasks to Ready.
   - If you are adopting this plan, pause the hooks cron line tonight. Otherwise treat the reset as the cutover
     triage and use the appendix to recover.

---

## 1. Where the reports disagreed, and how I resolved it

| Question | Positions | Resolution |
|---|---|---|
| Retire `#now`? | Retire: cdx, cld, gem. Keep through the trial: grk, mus | **Retire** (§3.4) |
| How to compute Today | Read-time from the ledger: cdx, cld, grk, mus. Hooks-managed `#today`: gem | **Read-time.** gem's "impossible" claim fails (§2, rows 2 and 4) |
| Today's scope | Open Pomodoros: cld, grk, mus. Open **and** completed: cdx | **Open only.** Closed 🍅 lines are history. Counting them means you can't park a task you worked this morning without deleting history. |
| Where Today is evaluated | Tasks `filter by function` calling a ledger API: cld. One `bob-dashboard` block rendering all lanes: cdx. A DataviewJS Today section: grk, mus | **Tasks filter plus a refresh event** (verified in §5). cdx's single component is the fallback. |
| Stop Next `[*]` decay too, or only `[/]`? | Both: cdx, cld, gem. Only `[/]`: grk. Neither: mus | **Both.** Otherwise `[*]` just repeats Today (§3.4). |
| Caps | NEXT 15 in all reports that set caps. PENDING: 10 (cld), 5 (gem), 15 (grk) | **NEXT 15, PENDING 10.** Soft caps: red chips and lints, never refusals. |
| Tomorrow's decay | cld: pause the cron. grk: wait until after it before judging counts | **Pause if adopting** (§7) |
| Blocked recovery | cdx, cld: recovery goes to Ready; accept it as re-triage | **Accept and document it.** Revisit only if it bites. |
| Transcluded dependencies in Today | gem: they inherit Today. grk: direct links only | **Direct links only.** Hooks still promote dependencies to Next. |

Two framing corrections:

- **grk calls your diagnosis "inverted". It isn't.** You said `#now` became necessary *because* the hooks kept
  deriving WIP/Next from links. That is exactly the decision record's reasoning: statuses decay, so "this matters
  this week" can't live in a checkbox.
- **mus's objection doesn't apply to your plan.** mus argues "Next absorbs `#now`" fails because Next is cleared
  when its link goes away. Your plan removes that clearing.

---

## 2. What I verified

| # | Finding | Evidence | Source |
|---|---|---|---|
| 1 | A path filter finds the task's own file, not incoming links | `bob query --tasks 'path includes 2026/20260930'` returns 1 task (`^gtd`) against 7 live open-ledger links | cdx, mus |
| 2 | Tasks queries can call plugin APIs | Tasks 8.4.0 compiles `filter by function` with `new Function(...)`. The dash already uses `moment()` in its query defaults and `bob-ledger-tools` `api` in DataviewJS. | cld; confirmed |
| 3 | Adding or removing a link line doesn't refresh Tasks queries | `Cache.indexFile` notifies only when a file's task list changes. Task identity includes line number, but `^gtd` sits **above** `## Pomodoros`, so link edits never shift a task line. | cld; confirmed, plus the line-position detail |
| 4 | **A refresh hook already exists** | Every Tasks `QueryRenderChild` subscribes to `obsidian-tasks-plugin:reload-open-search-results` on `app.workspace` and re-reads its query. A plugin can fire it with `app.workspace.trigger(...)`. | new |
| 5 | **A bare `app.` breaks headless queries** | Native `bob query --origin dash.md` fails: `Error: app is not defined`. With `globalThis.app?.plugins?.…`, it degrades cleanly: Pending returns all 53 `[/]`. | new |
| 6 | `bob-ledger-tools` has the right shape but is incomplete | `api` v1 has `caps`, `planBudget`, `nowBudget`. It re-renders on `metadataCache` `changed` and Tasks `cache-update`. `planBudget()` is async unless given content. Link targets are not resolved to vault paths (`planCanonicalTarget`). | cld; confirmed |
| 7 | Making the hooks sticky is a small change | Decay is exactly two branches in `sync.rs`: `transition()` returns `Clear` for `[*]` with no desired status, and `task_transition()` returns `ClearInProgress`. All status writes are single-character `PlannedChange { status_byte_offset, replacement }`. | cld, mus; confirmed |
| 8 | A `#today` tag would be a new, riskier kind of write | Every hooks write today is a one-byte checkbox swap. A tag means inserting and stripping text on hand-edited lines every time a link changes and at every day rollover. That is not "the same pipeline" (gem). | mus; confirmed |
| 9 | Tomorrow's decay | `BOB_DAY_FILE=<today's open entries as 20261001.md> BOB_NOW=2026-10-01 bob task-status-hooks --dry-run -f json` gives `cleared` 25, `cleared_in_progress` 48 and `unblocked` 24. Cron runs at `:10,:25,:40,:55`. | cld; reproduced (the `unblocked` count is new) |
| 10 | Ctrl+Shift+Enter picks link or unlink from the **checkbox** | `openPomodoroTaskLink`: `*` unlinks; `/` shows the Work Log prompt, then unlinks and demotes; ` ` or `?` links. A sticky `[*]` that isn't linked today would be unlinked instead of linked. | cld, cdx; confirmed |
| 11 | **`=x` has no "worked it, now park it" outcome** | The outcomes are: in progress (🍅, carried, `[/]`), deferred (carried), complete, and dropped (not carried, *never started*). Parking a swarm task takes two steps: close it, then unlink the carried line. | new |
| 12 | **Growth rate** | September dailies: 209 distinct tasks linked (about 7 new a day). 122 closed, 69 of them the same day they were first linked. 87 are still open (53 `[/]`, 26 `[*]`). With no releases, a sticky lane grows about 1.9 a day (09-01 → 09-28) to 2.9 a day (09-16 → 09-28). | new; corrects cld's +5 a day |
| 13 | The `#now` trial never had a curated set | The 73 tags came from `plan:202609/tag_open_pomodoro_now.md`, deliberately over the cap. `plan:202609/remove_now_tags.md` stripped them. The cohort was exactly 48 In Progress + 25 On Hold. | grk; confirmed |
| 14 | bob-cli already uses this ordering | The capture `^` picker's groups: `queued` (dedicated link under an open Pomodoro today) > `in_progress` > `next` > `now` > `note` | cld; confirmed |

---

## 3. Critique of the plan

### 3.1 What is right

- **The daily note already is the Today list.**
  - Adding a Task Link is an explicit choice, and the PLAN chip already shows capacity.
  - A second, hand-kept marker adds nothing.
- **A sticky Pending fixes a real gap.**
  - Today, an area or project `[/]` resets once neither today's nor yesterday's ledger links it.
  - Ctrl+Shift+Enter and the `=x` drop both push toward demotion.
  - Agent-swarm work that takes hours or days has no quiet place to wait. Pending is GTD's Waiting-For list plus WIP.
- **The review order is right.**
  - Pending → Next → Ready is Kanban's pull rule: "stop starting, start finishing".
  - It matches the order capture's picker already uses (§2, row 14).
- **One lane per task fixes the dash's duplicates.** This is the complaint you logged in `^improve-gtd-process`.
- **Most of the machinery already exists.** Picker precedence, the monotonic promotion rules, and the NOW
  cap/chip/meter/lint plumbing can all be retargeted rather than rewritten.

### 3.2 What needs correcting

1. **Today is a separate dimension from lane status.**
   - A Today task can be Next, Pending, or briefly Ready (a hand-typed link before promotion).
   - So "every Task Link is Pending or Next" is better stated as events:
     - linking a Ready task makes it Next;
     - linking a Next or Pending task leaves it alone;
     - working it makes it Pending;
     - unlinking never changes its lane.
   - Done, cancelled, struck and unresolved links need explicit, tested rules.
2. **Stopping the hooks is not enough.** Several unlink paths demote a task right away:
   - Ctrl+Shift+Enter on a `[*]` or `[/]` task, or on a link line (`applyTaskLinkOpen`);
   - the `@route+id!` toggle.

   If those stay as they are, Pending still gets wiped before any hooks pass runs. Ctrl+Shift+Enter must toggle on
   **whether a link exists**, not on the checkbox.
3. **One checkbox can't hold both a lane and a blocked state.**
   - The hooks overwrite `[ ]`, `[*]` or `[/]` with `[?]` and store no previous status.
   - When the block clears, the task goes back to its derived rank, which is Ready unless it's linked.
   - Accept this as re-triage for now: a deferral means "not now", so coming back as Ready is honest.
   - Don't defer a Pending task to hide it. Unlinking it is the parking gesture.
   - If lanes do need to survive blocking later, make Blocked a separate overlay. Don't add a hidden
     previous-status field; the Blocked decision already rejected that.
4. **You lose automatic forgetting. This is the cost that matters.**
   - At about 7 new links a day and about 4 closures a day, the lanes grow 15–20 a week (§2, row 12).
   - That is less than cld's estimate, but it still passes a 15 cap within a week.
   - More than half of drive-by links close the same day, so "every link becomes Next" costs less than grk and
     mus feared.
   - The rest need a release gesture as cheap as linking, plus a daily review that allows "release" as an outcome,
     not only "pull".
5. **The existing statuses aren't authored choices.**
   - About 80 current `[/]` and `[*]` tasks came from the old derivation rules.
   - Freezing them turns an accident of implementation into a permanent queue.
   - Triage them once, at cutover (§7).
6. **Two one-day-old decision records get reversed.**
   - `now-tag-is-user-owned` is retired.
   - `task-status-is-derived` is narrowed.
   - Records are immutable, so write new superseding records through `/sase_memory_write`. Don't edit the old ones.

### 3.3 What you actually lose (more than "a link without `#now`")

| Lost | Severity | Mitigation |
|---|---|---|
| Automatic decay of stale Next and `[/]` | **High** | Caps with red chips, a one-key release, a weekly prune. Later, a stale report. |
| `[/]` meaning "worked on recently" | Medium | Later: days since the last 🍅. Until then, sort Pending oldest first. |
| Ctrl+Shift+Enter as unlink-and-demote in one key | Medium | Split it: Ctrl+Shift+Enter links and unlinks; Alt+N releases (§6) |
| A lane surviving a Blocked period | Low–medium | Re-triage (§3.2, item 3) |
| Linking without committing | Low (you accept it) | Release at close time, or Alt+N afterward |
| Capture's "this week, not today" (`#now` on new text) | Low (unused) | Alt+N during review. Add a capture spelling only if you miss it. |

### 3.4 The dissent: keep `#now` until the trial ends (grk, mus)

grk proposes keeping `#now` and derived Next, stopping only the `[/]` rollback, and showing Today / Pending / Now /
Ready. What they get right:

- sticky `[/]`;
- Today computed from the ledger;
- exclusive dash sections;
- drop gestures that preserve `[/]`.

All four are in the recommendation below. Where I disagree:

- **Derived `[*]` repeats information.** It would mean "on today's graph", which is the Today set. The hooks would
  write a status the dash doesn't show. Your model gives `[*]` a meaning nothing else carries: committed, but not
  today.
- **The trial can't test your proposal.**
  - Its kill rule is "if NOW is ignored, delete the tag and keep decay". That fallback brings back the hoarding
    incentive.
  - Your variant is the better fallback, and nothing in the trial would compare the two.
  - The only `#now` data so far is the bulk load and strip of your whole `[/]`/`[*]` population. That says your
    "now" set is the in-flight set.
- **It's cheaper to remove now.** The `#now` surface is one to two days old. It touches about 23 Rust files and
  about 1.6k plugin lines including tests, and much of that (caps, chip, meter, lint) can be retargeted to NEXT.
  It only gets more entangled from here.

The sound part of the dissent is **sequencing**. Ship first the pieces every report endorses: sticky `[/]`, the
Today predicate, and the unlink fixes. Remove `#now` last.

### 3.5 Other approaches, rejected

- **Hooks-managed `#today` (gem).** It keeps a second copy of the ledger and brings the following problems:
  - write churn in hand-edited notes such as `sase.md`;
  - races with open editors and multi-machine sync;
  - a machine-owned tag next to user tags;
  - stale membership after a missed run.

  It is acceptable only as a stopgap if the read-time predicate fails.
- **A separate Submitted or Waiting status.** You already cancelled it.
- **No promotion on link**, keeping links purely "Today". Dropping a link would then send the task to Ready, which
  is the status-lock trap again. Promotion on link is what makes dropping safe.
- **Age-based Next decay.** A reasonable later guardrail if the weekly prune fails, but never for Pending. It also
  needs a multi-day ledger lookback the hooks don't have.
- **gem's "perfect GTD alignment" overstates it.** Ready is closer to GTD's Next Actions list, Next is closer to a
  Kanban committed column, and Pending is Waiting-For. The model is good either way.

---

## 4. Adjusted requirements (my changes are marked ADJ)

| # | Requirement | Origin |
|---|---|---|
| R1 | Retire `#now`: its meaning, capture token and completion, Alt+N toggle, the Ctrl+Shift+P row, picker group, NOW chip, section and meter | yours |
| R2 | The hooks never demote `[*]` or `[/]` because a link disappeared. They still promote Ready → Next on link, `=x` still sets `[/]`, and Blocked stays derived and overrides both. | yours |
| R3 | Dash sections Today / Pending / Next / Ready are mutually exclusive, in that precedence | yours. **ADJ:** Ready also excludes Today |
| R4 | **ADJ.** Today means open tasks with a *dedicated*, non-struck Task Link under today's **open** Pomodoros, GTD entry included. Completed Pomodoros and transcluded dependencies don't count. | your swarm case needs it. It matches the plan budget and picker. |
| R5 | **ADJ.** Today is computed at read time from the ledger. It is never written to task lines. No path filter, no `#today`. | §5 |
| R6 | **ADJ.** *Every* unlink path keeps the lane: Ctrl+Shift+Enter (made a link-presence toggle), `=x~K`, start `~K` drops, hand deletion | §3.2, item 2 |
| R7 | **ADJ.** Release is a separate one-key gesture (Next or Pending → Ready). Unlinking a Pending task offers the existing Work Log prompt ("why is this pending?"). | replaces decay |
| R8 | **ADJ.** Soft caps: `plan.max_next` = 15 (the renamed `max_now`) and `plan.max_pending` = 10. Each counts the whole lane, Today included, so counts don't swing during the day. Shown as red chips, `bob plan` meters and lints. Nothing is ever refused. | replaces decay |
| R9 | **ADJ.** Tasks that live in daily notes (`^gtd`) keep today's derived clearing | avoids a stale `[*]` per day |
| R10 | **ADJ.** A blocked or deferred task comes back as Ready. Documented, not hidden. | §3.2, item 3 |
| R11 | **ADJ.** Rituals: a daily review of Pending → Next → Ready of 5 minutes or less, where release is a normal outcome, and a weekly prune to the caps | review is now the only way out |
| R12 | **ADJ.** Keep the `[/]` symbol and In Progress type. Only the section label says "Pending". | avoids query, CSS and plugin churn |
| R13 | **ADJ.** New decision records supersede `now-tag-is-user-owned` and narrow `task-status-is-derived` | the decisions web's immutability rule |

---

## 5. How to implement Today

| Option | Right tasks? | Writes | Freshness | Headless | Verdict |
|---|---|---|---|---|---|
| Tasks `path` / `filename` filter | **No** (the task's own file) | none | — | yes | reject |
| Hooks-managed `#today` | yes, if the hooks are current | line-text edits for every link change and day rollover | up to 15 minutes late | yes | stopgap only |
| **Synchronous `bob-ledger-tools` predicate in `filter by function`** | yes | none | instant, via the refresh event | through `bob plan -f json` | **recommend** |
| One `bob-dashboard` block rendering all four lanes (cdx) | yes | none | instant | same | fallback if the Tasks route proves fragile |

### 5.1 The API (`bob-ledger-tools`, `api.version` 2)

- **Functions:**
  - `todayKeys()` returns a set of `"path#blockId"` keys;
  - `isToday(task)` matches a Tasks task by `task.path` and its block ID;
  - `todayRank(task)` returns ledger order, for sorting;
  - `nextBudget()` and `pendingBudget()` replace `nowBudget()`.
- **Computing the set:**
  - Reuse `computePlanBudget`'s entry model, but include exempt entries such as GTD.
  - Count only dedicated links: the list item's body is one block link once 🍅 is stripped, the same rule `=x`
    numbering uses.
  - Resolve each target with `metadataCache.getFirstLinkpathDest(target, dailyPath)`. The plugin doesn't do this
    yet.
- **The cache must be synchronous**, because Tasks can't await inside a filter. Recompute it on `metadataCache`
  `changed` for today's daily note (already subscribed) and at midnight rollover.
- **Refresh:** when the key set changes, call
  `app.workspace.trigger("obsidian-tasks-plugin:reload-open-search-results")`.
  - Every open Tasks block then re-reads its query (§2, row 4). This settles cld's open "needs a spike" question.
  - The event is internal to Tasks, so pin the behavior with a test and keep cdx's component as the fallback.
- **Mirror in Rust:**
  - Define Today once in `docs/plan.md`, next to the plan budget.
  - Add `today_tasks` to `bob plan -f json` for agents and headless use.
  - Share conformance vectors between the JS and Rust versions, as the plan budget already does.
  - This also brings the other "linked today" definitions into line: the hooks, the plan budget, the picker, and
    NAV recovery.

### 5.2 The dash

Keep `TQ_extra_instructions` as the note-wide defaults. Use `globalThis.app?.` so headless `bob query` degrades
instead of failing (§2, row 5):

````markdown
### Today Tasks
```tasks
not done
filter by function globalThis.app?.plugins?.plugins?.["bob-ledger-tools"]?.api?.isToday?.(task) === true
```

### Pending Tasks
```tasks
status.type is IN_PROGRESS
filter by function globalThis.app?.plugins?.plugins?.["bob-ledger-tools"]?.api?.isToday?.(task) !== true
```

### Next Tasks
```tasks
status.name includes Next
filter by function globalThis.app?.plugins?.plugins?.["bob-ledger-tools"]?.api?.isToday?.(task) !== true
```

### Ready Tasks
```tasks
status.type is TODO
filter by function globalThis.app?.plugins?.plugins?.["bob-ledger-tools"]?.api?.isToday?.(task) !== true
```
````

- **Why the sections can't overlap:**
  - `[/]` is IN_PROGRESS, `[*]` Next is ON_HOLD, and `[ ]` is TODO, so the three status sections are disjoint.
  - The lower three sections all exclude Today.
- **If the plugin is missing:** Today is empty and nothing disappears.
- **Chips:** `TODAY n`, `PENDING n/10`, `NEXT n/15`, `READY n`, `BLOCKED n`, `PLAN t/3 · l/10`. The chip bar
  should use the same predicate.
- **Sort order:** Pending oldest-created first, so long-running work surfaces. Next by priority.

---

## 6. Status rules and gestures after the change

**Hooks.** Only these rows of `docs/task-status-hooks.md` change:

- An unreachable `[*]` stays `[*]`. Tasks in daily notes still clear to `[ ]`.
- An area or project `[/]` with no recent activity stays `[/]`.
- The `KeptNext` grace path becomes moot.

Promotion on link, `=x` → `[/]`, derived Blocked, grouping, duplicate/cancelled/completed-link cleanup, and 🍅
repair are unchanged.

| Gesture | Today | Lane |
|---|---|---|
| **Link** (Ctrl+Shift+Enter on a task not linked today, `^^`, capture `@route:id` or `^route:id`, the Mac `^` picker) | joins | Ready or Blocked → Next. Next and Pending unchanged. |
| **Unlink** (Ctrl+Shift+Enter on a linked task or link line, `=x~K`, start `~K`, hand delete) | leaves | **unchanged**. For `[/]`, offer the Work Log note. |
| `=x` in progress / deferred / complete | carried / carried / leaves | → `[/]` / unchanged / done |
| **Release** (Alt+N, freed from `#now`; the Ctrl+Shift+P row in the `#now` slot) | leaves if linked | `[*]` → `[ ]`. `[/]` → `[ ]` through the Work Log prompt. |
| **Commit without Today** (Alt+N on a Ready task) | none | `[ ]` → `[*]` |
| Defer (a P-level or a date) / Cancel | pruned | → `[?]`, returns as Ready / `[-]` |

**Parking a swarm task** (§2, row 11): close with `=x` (the task becomes `[/]` and its link is carried), then unlink
the carried line and add a one-line Work Log note. It then sits in Pending. A dedicated "worked, don't carry" close
outcome is a nice-to-have. Add it only if the two steps get annoying.

Update the Notice and help text to match: "unlinked · stays Next". Replace the `=x` drop row's "`#now` keeps it in
view" with "stays Next/Pending".

---

## 7. Cutover

**Tonight.** The first hooks pass after the 2026-10-01 daily note is created (around 06:00) demotes 48 `[/]` and
25 `[*]` tasks (§2, row 9).

- **If you're adopting this plan, pause.**
  - Comment out the `task-status-hooks` crontab line (`docs/vault-git-sync.md` has the procedure).
  - Ship Phase 1, triage down to the caps, then resume the cron job.
  - Cost: a day or two without automatic Blocked recovery and ledger cleanup. Keymaps and `=x` still apply their
    immediate status changes.
- **If the pass has already run,** treat the reset as the triage.
  - Re-promote keepers from the appendix or `/var/tmp/bob_task_status_hooks.log`.
  - Do this only *after* Phase 1 ships, or the old hooks reset them again.

**Phases.** Each phase is useful on its own. The ones every report endorses come first.

1. **bob-cli hooks.** Remove the two decay branches, keeping the daily-note carve-out. Update tests and
   `docs/task-status-hooks.md`. Write the superseding decision records alongside.
2. **Define Today once.** Document it in `docs/plan.md` with shared vectors and add `today_tasks` to
   `bob plan -f json`. Retarget the NOW meter, cap and lint to NEXT and PENDING.
3. **bob-plugins and the dash.**
   - Add the ledger-tools v2 API with its synchronous cache and refresh event.
   - Rebuild the Today / Pending / Next / Ready sections and the chips.
   - Make Ctrl+Shift+Enter toggle on link presence, and make Alt+N and the Ctrl+Shift+P row release or commit.
   - Remove `#now`.
   - Ship the gesture change together with the new sections, so there's no stretch where the keys still demote.
4. **Capture and Mac cleanup.** Remove the `#now` token and completion, the picker's `now` group, the `now` fields
   and the "stays in NOW" captions. Mac capture renders these from bob's JSON, so land the removal in both repos
   together.
5. **Vault.**
   - Update the `gtd_daily.md` chores: daily "Pending → Next → Ready, release freely"; weekly "prune NEXT ≤ 15 and
     PENDING ≤ 10".
   - Set `plan.max_next` and `plan.max_pending` in `config.yml`.

**Trial.** Two weeks from when Phase 3 lands. Keep the design if, on at least 10 of 14 days:

- NEXT is at most 15 and PENDING at most 10;
- the morning review runs in 5 minutes or less;
- the release gesture actually gets used.

If NEXT stays red, tighten the weekly prune first. After that, consider age-based Next decay, never for Pending.

---

## Recommended solution

**Retire `#now`.**

- **The ledger says what is Today.** Compute it at read time with a synchronous `bob-ledger-tools` predicate. Use it
  in `filter by function` on the dash, and mirror it in `bob plan -f json`.
- **The checkbox says which lane a task is in:**
  - linking makes a Ready task Next;
  - working it makes it Pending;
  - unlinking never changes its lane, whether through the hooks, a keymap, or a capture drop;
  - only an explicit one-key release sends a task back to Ready.
- **Dependencies and schedules still derive Blocked.** A task that recovers from Blocked is re-triaged to Ready.
- **Replace decay with visible limits:**
  - NEXT 15 and PENDING 10 as soft caps;
  - a daily review in which release is a normal outcome;
  - a weekly prune.
- **Rebuild the dash** as mutually exclusive Today / Pending / Next / Ready. The status sections are disjoint by
  type, and each lower section excludes Today.
- **Don't** use a file-path filter (it answers a different question) or a `#today` tag (a second copy of the
  ledger).
- **Do it in this order:**
  1. pause the hooks cron tonight;
  2. sticky hooks;
  3. the Today definition;
  4. plugins and dash;
  5. capture cleanup;
  6. new decision records superseding `now-tag-is-user-owned` and narrowing `task-status-is-derived`.

---

## Appendix: what the first 2026-10-01 hooks pass would demote

This comes from cld's dry run. My reproduction gives the same counts. It assumes tomorrow's ledger carries today's
open BOB, CLEANUP, BETS and GTD entries.

- **`[/]` → `[ ]` (48)**
  - `bob`: `better-capture-stop`, `capture-stop`, `solo-id-capture`, `better-roadmaps`
  - `sase`: `fix-telegram-leak`, `fix-v-key`, `release-v18`, `better-sidebar`, `agents-sub-tabs`,
    `recovery-panel`, `final-ux`, `fix-schema-mismatch`, `p-key-for-decks`, `quote-keymap`, `card-blocks`,
    `xprompt-in-header`, `routine-groups`, `bead-triage-job`, `fix-muse-waits`, `agent-clan-summaries`,
    `usage-service`, `harden-services`, `dot-separators`, `clean-core`, `critique-research-swarm`, `output`,
    `bead-art-links`, `just-fix-tui-screenshots`, `tui-speedup-again`, `tui-screenshot`, `stale-epic-approved`,
    `better-sbd-alias`, `services`, `fix-claude-monitors`, `work-kills-waiting`, `fast-tests`, `comma-big-h`,
    `read-final-research`, `green-check-full`, `stop-wait-renames`, `q-weight`, `sudo`, `hold`
  - one each: `sase_agent_history#read-research`, `sase_clean#work-all-beads`, `sase_goals#epic-roadmap`,
    `sase_pager#fix-file-follow`, `sase_remote#use-sase-screenshot-to-fix`
- **`[*]` → `[ ]` (25)**
  - `bob`: `web-capture`, `capture-project-files`
  - `sase`: `no-more-index-lock`, `stash-trash`, `target-alias-providers`, `light-prompt-history`, `tui-cli`,
    `node-finder`, `agent-renames`, `multi-line-alternations`, `bead-read`, `fix-agent-tab-snap`,
    `web-piw-completion`, `improve-monitors`, `bulk-gate-cmds`, `fast-tale-status`, `q-weight-phases`,
    `q-weights-prj`, `q-weight-cap`, `schedule`, `q-weights-metadata`
  - `sase_art_links#artifact-event-store`
  - `sase_memory`: `feature-flags`, `review-sase-art`, `memory-beads`

## Sources

- **Swarm reports** (this directory):
  - `__cdx`: canonical identity partition, unlink paths, cutover inventory;
  - `__cld`: guardrails, the Tasks refresh gap, the dry-run appendix, the gesture table;
  - `__grk`: the keep-`#now` dissent, the bulk-tag history, sticky `[/]` only;
  - `__mus`: path-filter test, the write model of a `#today` tag, the trial argument;
  - `__gem`: caps and the `#today` design (not adopted).
- **bob-cli:**
  - `src/native/task_status_hooks/{sync.rs,model.rs}` (`task_transition`, `transition`, `PlannedChange`);
  - `docs/task-status-hooks.md` (Rolling Recent Activity, `BOB_DAY_FILE`, `BOB_NOW`);
  - `docs/capture.md` (the `=x` outcome table, picker groups, linking an existing task);
  - `docs/vault-git-sync.md` (cron schedule);
  - `src/native/dataview/tasks/js.rs` (no `app` global).
- **bob-plugins:**
  - `plugins/bob-ledger-tools/main.js` (`api` v1, `computePlanBudget`, `planBlockLinks`, `planCanonicalTarget`,
    its event subscriptions);
  - `plugins/block-id-prompt/main.js` (`openPomodoroTaskLink`).
- **Obsidian Tasks 8.4.0 bundle:**
  - `new Function` evaluation of `filter by function`;
  - the `Cache.indexFile` `listsAreIdentical` guard and `TaskLocation.identicalTo`, which includes `lineNumber`;
  - `QueryRenderChild`'s subscription to `onReloadOpenSearchResults`;
  - `obsidianEvents` is `app.workspace`.
- **Vault (read-only):**
  - `dash.md`, `2026/20260930.md`, the September dailies, `bob.md` (`^submitted-status`, `^improve-gtd-process`);
  - `bob query` counts: WIP 53, NEXT 27, READY 186, NOW 0;
  - `bob task-status-hooks --dry-run` for today and a simulated 2026-10-01.
- **SASE memory and plans:**
  - `decisions:now-tag-is-user-owned`, `decisions:task-status-is-derived`;
  - glossary: Pomodoro, Task Link, Work Log;
  - `plan:202609/tag_open_pomodoro_now.md`, `plan:202609/remove_now_tags.md`.
