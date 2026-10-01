# NEW, READY, and rotten: how to surface freshness on the dash

## Bottom line

Split the Ready lane **at read time**, the same way Today already splits it. Do not write a `#rotten` tag, a `[rotten::]` field, or any other stored freshness-derived marker.

- **READY** on `dash.md` becomes the confirmed, in-lease backlog: visible Ready tasks whose evaluator state is `fresh` (plus the small out-of-scope remainder: recurring, daily-note Ready).
- **NEW** becomes a dash section **below TODAY and above PENDING**, using `api.freshness.state(task) === "new"`.
- **Rotten** (evaluator `stale`) plus **resurfaced** live in a new query note `~/bob/rotten.md`, reached from a **ROTTEN** chip that replaces today's REVIEW chip.
- `bob task-status-hooks` stays out of this. The plugin API and Tasks `filter by function` already compute the predicate.

This is a good idea **now that `[fresh::]` exists**. The original freshness design kept READY as the full backlog and hung a REVIEW chip off it. That was the right launch posture. The payoff of the stamp is a READY list you can actually pull from. Bryan has already filed that as `bob_gtd#^hide-rotten-tasks`.

## The question

The `[fresh:: YYYY-MM-DD]` stamp is live. Its point, as restated here, is to make it obvious which Ready tasks are **really ready**.

The proposed product:

1. New and rotten tasks leave the READY section.
2. New tasks get a **NEW** section on `~/bob/dash.md`, above WIP.
3. Rotten tasks go in a new `~/bob/rotten.md`, linked from dash with a **ROTTEN** badge.
4. A first implementation thought: `bob task-status-hooks` writes a `#rotten` tag so Tasks can filter on it.

This report critiques that plan, names justified requirement changes, and recommends an implementation.

## What is already true

Measured 2026-10-01 against the live vault, `docs/freshness.md`, bob-ledger-tools 1.9.2, and `dash.md`.

| Fact | Evidence |
| --- | --- |
| Freshness state is computed at read time and never stored. Automation never stamps. | `docs/freshness.md` §4–§5; glossary: Task Freshness |
| Evaluator states: `new` (no stamp), `resurfaced` (scheduled arrived after the stamp), `stale` (lease expired), `fresh`. In-scope is visible non-recurring Ready, not Today, not a daily note. | `docs/freshness.md` §4; `src/native/freshness/state.rs`; `api.freshness.state` |
| The plugin already exposes `state`, `isDue`, `tier`, `rank`, `counts` for Tasks `filter by function`. | bob-ledger-tools `api.freshness`; `freshness.md` already uses `isDue` / `rank` / `tier` |
| Dash exclusivity is already a plugin-API filter, not a tag. TODAY is `isToday === true`; PENDING / NEXT / READY are `isToday !== true`. | live `dash.md` lines 413–442 |
| A `#today` tag was considered and rejected: write churn, races, staleness between the 15-minute hooks pass, and a second copy of the ledger on every task line. | `decisions:today-is-read-from-the-ledger` |
| Hooks never stamp freshness and do not write tags. | `docs/freshness.md` §5 "Automation — never stamps"; `docs/task-status-hooks.md` |
| `~/bob/freshness.md` already lists NEW + DUE with the shared evaluator. Dash already has a REVIEW chip that links there. Desktop status bar: `⟳ N due · N new · ✓ N today`. | live `freshness.md`; `dash.md` chipsAfterReady; ledger-tools status bar |
| `~/bob/rotten.md` does not exist. | filesystem |
| After today's seed, the queue is empty: 199 in-scope fresh, 0 new, 0 stale, 0 resurfaced, 210 dash READY (native `bob query`), 391 refreshed today. | `bob freshness list -f json` |
| Next on this exact product is already filed: `Hide rotten tasks in [[dash]]! Show them in [[rotten]]!` (`bob_gtd#^hide-rotten-tasks`). Sibling Next tasks: scheduled-as-stale, WIP/NEXT 1-day refresh. | `bob_gtd.md` |
| Next's Tasks type is `ON_HOLD`, Pending is `IN_PROGRESS`, Ready is core `TODO`. READY queries therefore do not include Next. | vault Tasks `data.json` (same shape as the parity fixture) |
| Headless `bob query` cannot call `globalThis.app.plugins…`. `isToday === true` fail-closes (TODAY is empty); `isToday !== true` fail-opens (READY still includes Today). | `decisions:today-is-read-from-the-ledger` cost; live `--tasks-note dash.md` TODAY count 0 |
| `bob plan` JSON has no READY count. The READY cap lives in Obsidian (`readyBudget` / `renderReadyBadge`). | `docs/plan.md`; ledger-tools `readyCountFromTasks` |

The 2026-09-30 freshness research (`research:202609/ready_task_freshness_review`) recommended **source-note jumps, a status bar, a dedicated review note, and one dash chip** — and rejected dash INBOX/STALE sections because they would fight TODAY / PENDING / NEXT / READY exclusivity. That recommendation launched the feature. This request is the next product step: **READY means confirmed**.

## Critique of the proposed plan

### What is right

**READY should stop mixing three jobs.** Today it is (1) the confirmed backlog you pull from, (2) the unconfirmed inbox, and (3) the expired-lease maintenance list. The stamp exists specifically so those can diverge. A 210-task READY list that is "all fresh today" is already a planning surface; a 210-task READY list that is 30 new + 40 rotten + 140 confirmed is a lie.

**NEW belongs on the planning board.** Arrivals are the one freshness tier the ritual refuses to cap or skip (`docs/freshness.md` §6). Putting them on dash, above PENDING, makes "acknowledge yesterday's captures before pulling more work" the default glance, not a side quest in `freshness.md`.

**Rotten does not belong on dash.** Expired leases are maintenance. They should remain reachable (chip + `]s`) without occupying the pull-from-READY board. A dedicated `rotten.md` matches how `blocked.md` already works: an overflow note with an external chip.

**"Rotten" is a better user-facing word than "stale".** The vault already uses "stale" for overdue Pomodoros, quiet-period hooks retries, badge snapshots, and seed refusals. Rotten names *Ready-lane decay* without that collision. Keep the evaluator/JSON name `stale` in v1.

### What is wrong: writing `#rotten` with the hooks

This is the same design that `today-is-read-from-the-ledger` already rejected, with worse timing properties.

1. **The predicate is a function of today, the interval, `scheduled`, Today membership, and lane.** It changes at local midnight, on Alt+F, on a deferral rolling in, on a Task Link, and on a note's `task_refresh`. A tag written every 15 minutes is a cache of that function. Caches of "today" go stale at 00:01.

2. **Hooks are the wrong writer.** They reconcile Blocked from dependencies and future `scheduled` dates. They do not stamp freshness, and they must not author a freshness-derived tag. A hand Alt+F at 00:02 would leave `#rotten` on a confirmed line until the next pass; a midnight rollover would leave confirmed-looking lines in READY until the next pass. The dash would lie in both directions.

3. **Placement is hostile.** Trailing tags are part of the Tasks suffix (`HASH_TAG_AT_END`). `stamp_fresh` rebuilds `head + [fresh::] + [refresh::] + suffix`. A hooks-owned `#rotten` sitting in that suffix is another writer on the same line as the stamper, the cycler, capture, and grouping. `#hide` is user-owned. A machine tag beside it teaches the wrong lesson about who owns visibility.

4. **The only real benefit is headless Tasks filters** (`tags do not include #rotten`). That benefit is imaginary here. The READY cap is computed in JavaScript (`readyBudget`), which already has the evaluator. Native `bob plan` does not count READY. Native `bob query` already fail-opens on `isToday` filters; a tag would make headless READY *different from* the live dash during the hooks lag, which is worse than today's known empty-Today limitation.

5. **Write churn on the whole Ready pool every night** as leases expire, then again as they are confirmed. Vault-sync already pays for human stamps (20–40 lines a morning). Multiplying that by a machine pass over every expired task is the cost the read-time design avoided.

Do not preprocess rotten tasks onto disk. The preprocessing is `freshnessEvaluate`.

### What is incomplete: three due states, not two

The request says "a new task or a rotten task." The evaluator has a third in-scope due state: **resurfaced**. A short P1 deferral that returned is due the morning it returns, even if the stamp is still inside its interval (`docs/freshness.md` §4, tickler rule). It is not new and it is not rotten-by-age. It is also not "really ready."

**Justified adjustment:** resurfaced tasks leave READY and join `rotten.md`, grouped above rotten, sorted by the existing queue order (`due_on`, path, line). They are DUE, not NEW.

### What is slightly off: "above the WIP section"

Live dash headings are **TODAY, PENDING, NEXT, READY**. The lane decision says dash labels say PENDING; `[/]` remains In Progress. `bob_gtd.md` still says "WIP" in leftover `#now` requirements.

**Justified adjustment:** read "WIP" as **PENDING**. Put NEW **below TODAY and above PENDING**:

```text
TODAY     committed on today's open Pomodoros
NEW       unconfirmed Ready arrivals (uncapped)
PENDING   sticky in-progress
NEXT      sticky committed, not today
READY     confirmed Ready backlog
```

TODAY stays first. It is work already pulled. NEW is the gate before pulling more.

### What would duplicate: keep `freshness.md` as a third list

Today `freshness.md` is the combined NEW + DUE query. If dash grows a NEW section and `rotten.md` holds DUE, a third Tasks list of the same rows is three places to click and three places to drift.

**Justified adjustment:** `rotten.md` takes the DUE query and the ritual table. The REVIEW chip becomes ROTTEN and points at `rotten.md`. `freshness.md` becomes a short stub that links to `dash#NEW Tasks` and `rotten.md` (keep the path for old links and the status-bar fallback until the plugin fallback is updated). Do not keep two live review queues.

## Alternatives

| Approach | Verdict |
| --- | --- |
| **A. Query-time plugin filters** (recommended). Dash NEW + READY `!isDue`; `rotten.md` for `stale`/`resurfaced`. Same pattern as Today. | Fits the architecture. Live the moment the stamp or the calendar changes. |
| **B. `#rotten` (or `#new`) via `task-status-hooks`.** | Reject. See above. Reopens the rejected `#today` tag. |
| **C. A stored `[rotten::]` / `[freshness::]` field.** | Reject. Unknown Dataview keys at the end of the line hide Tasks fields (the original freshness placement trap). Even placed correctly, it is still a written cache of a read-time state. |
| **D. Physically move rotten tasks into `rotten.md`.** | Reject. Tasks live in project/area notes; grouping already moves them between status headings. A second move destroys project context and Work Logs. |
| **E. `group by function` on one READY section** (FRESH / NEW / ROTTEN). | Reject for rotten (user wants it off dash). Weak for NEW: grouping still shows the rows in the READY heading the chip opens. |
| **F. Dataview `TASK WHERE !fresh`.** | Reject. Dataview cannot apply interval precedence, the tickler rule, Today, or lane visibility. The shared evaluator would fork. |
| **G. Keep READY whole; only the REVIEW chip** (2026-09-30 recommendation). | Right for launch. Wrong now that the stamp exists and Bryan has filed hide-from-READY. READY would still be the mixed list. |
| **H. One `bob-dashboard` code block instead of Tasks queries.** | The Today decision's fallback if Tasks reload is fragile. Do not take it for this feature. The Today filters already prove `filter by function` + `TODAY_RELOAD_EVENT` works. |
| **I. A sixth checkbox status "Needs Review".** | Rejected in the original freshness research. Status is for lanes; hooks own Blocked. |

## Justified requirement adjustments

Called out so they are not mistaken for the original request.

1. **No stored `#rotten` / `#new` / extra field.** Read-time only.
2. **"WIP" means PENDING.** NEW sits under TODAY, above PENDING.
3. **Resurfaced leaves READY** and appears in `rotten.md` (DUE), grouped separately from rotten.
4. **`rotten.md` is a query note**, like `freshness.md` and `blocked.md`. It does not own task lines.
5. **User-facing ROTTEN; evaluator/JSON stay `stale`** (`counts.stale`, `FreshState::Stale`, `stale_daily_budget`) until a schema bump. Glossary: Rotten = the `stale` freshness state.
6. **Replace the REVIEW chip with ROTTEN.** Add a NEW chip (uncapped, accent when `new > 0`) so collapsed dash still shows arrivals. REVIEW's combined `due · new · ✓ today` string is the status bar's job.
7. **`readyBudget` / READY chip count exclude `isDue`.** Otherwise the chip still says `210/100` while READY shows only confirmed rows. Recurring and daily-note Ready stay in the count (they stay in the section).
8. **Fail-open without the plugin**, matching Today: `isDue?.(task) !== true` keeps today's READY if ledger-tools is missing; NEW/`rotten.md` go empty. Document this next to the Today limitation.
9. **Do not expand freshness scope in this change.** Sibling Next tasks (`^scheduled-are-stale`, `^wip-next-refresh`) stay separate. Future-scheduled tasks remain Blocked (`blocked.md`). Next/Pending stay out of the Ready-only evaluator. When those land, `isDue` grows with the evaluator and `rotten.md` should filter on `isDue && state !== "new"`, not on `status.type is TODO`, so it keeps working.
10. **NEW is uncapped and never skipped.** No `limit`, no budget on the NEW section. The existing `stale_daily_budget` (still named that in config) may meter rotten.md; it still must not hide rows.

## Recommended solution

### Product

READY on the dash is the **confirmed Ready backlog**. NEW is the **uncapped intake**. Rotten + resurfaced are **review debt** in `rotten.md`. Freshness still never changes a checkbox, a lane, Today, a schedule, or a priority. It only changes **which exclusive dash query shows the row**.

Morning ritual, unchanged in substance, now matches the board:

1. `bob gkeep pull`
2. Clear NEW on dash (`]s` / Alt+Shift+F until 0 new) — never capped
3. Work ROTTEN / `rotten.md` until empty or the budget meter is met
4. PENDING → NEXT → READY as today's pull

### Implementation (small, in the existing groove)

**1. Vault `dash.md` Tasks blocks** — extra_instructions already supply `#hide`, templates, `is not blocked`, not-future-`scheduled`, hide-self. Add:

```tasks
### NEW Tasks
status.type is TODO
filter by function globalThis.app?.plugins?.plugins?.["bob-ledger-tools"]?.api?.isToday?.(task) !== true
filter by function globalThis.app?.plugins?.plugins?.["bob-ledger-tools"]?.api?.freshness?.state?.(task) === "new"
sort by function task.file.path
sort by function task.lineNumber
```

```tasks
### READY Tasks
status.type is TODO
filter by function globalThis.app?.plugins?.plugins?.["bob-ledger-tools"]?.api?.isToday?.(task) !== true
filter by function globalThis.app?.plugins?.plugins?.["bob-ledger-tools"]?.api?.freshness?.isDue?.(task) !== true
```

Section order: TODAY, **NEW**, PENDING, NEXT, READY.

**2. Vault `~/bob/rotten.md`** — new note, `parent: [[gtd]]`, ritual table moved from `freshness.md`:

```tasks
not done
filter by function globalThis.app?.plugins?.plugins?.["bob-ledger-tools"]?.api?.freshness?.state?.(task) === "stale" || globalThis.app?.plugins?.plugins?.["bob-ledger-tools"]?.api?.freshness?.state?.(task) === "resurfaced"
sort by function globalThis.app?.plugins?.plugins?.["bob-ledger-tools"]?.api?.freshness?.rank?.(task) ?? 0
group by function globalThis.app?.plugins?.plugins?.["bob-ledger-tools"]?.api?.freshness?.state?.(task) ?? "?"
short mode
hide toolbar
```

Optional tiny helpers on `api.freshness` (`isNew`, `isRotten` including resurfaced) to keep the queries readable; not required.

**3. Dash chips** (dataviewjs in `dash.md`, plus ledger-tools):

- NEW chip before PENDING, value = `counts.new`, accent when `new > 0`, target `dash#NEW Tasks`
- READY chip uses `readyBudget` after it excludes `isDue`
- ROTTEN chip replaces REVIEW: value = `stale + resurfaced` (or `due - new`), orange, external ↗ to `rotten.md`
- TODAY chip unchanged

**4. bob-ledger-tools**

- `readyCountFromTasks`: skip `apiFreshnessIsDue(task)` (or equivalent row state) in addition to Today / blocked / `#hide` / future schedule
- Status-bar click fallback: `rotten.md` when due>0 and new==0, else dash NEW, else today's `freshness.md` stub
- Midnight rollover already rebuilds the memo and fires `TODAY_RELOAD_EVENT`; the new filters ride that
- Tests: READY count drops when a fixture task is `stale`/`new`; NEW/`isDue` filters; fail-open when `freshness` is missing

**5. bob-cli docs, not hooks**

- `docs/freshness.md` §8: READY is confirmed-fresh; NEW is a dash section; DUE lives in `rotten.md`; user-facing "rotten" = evaluator `stale`
- `docs/plan.md`: READY backlog definition excludes `isDue`
- Glossary strand: Rotten alias; one line that freshness still does not change lanes
- **No `task-status-hooks` change**

**6. `freshness.md`**

Keep the path. Replace the Tasks block with links to `dash#NEW Tasks` and `[[rotten]]`. Move the outcome-key table to `rotten.md` (NEW's outcomes are the same keys, used from dash).

### What not to do in this slice

- Do not rename JSON `stale` or `stale_daily_budget`
- Do not put future-scheduled Blocked tasks in `rotten.md` (that is `blocked.md`; sibling `^scheduled-are-stale` is the tickler/RESURFACED question)
- Do not put Next/Pending in NEW or rotten until `^wip-next-refresh` changes `in_scope`
- Do not add a "Needs Review" status
- Do not generate `_generated/rotten.md` transclusion dumps

### Risks

- **Dash weight.** Five sections. Mitigated because NEW is usually a handful (0 this morning after seed) and rotten is off-board.
- **Exclusivity decision.** TODAY / PENDING / NEXT / READY becomes TODAY / NEW / PENDING / NEXT / READY. NEW is a split of READY, still exclusive. Record that in a short decision follow-up; do not silently fork the claim.
- **Chip vs list mismatch** if `readyBudget` is not updated in the same change. Ship the count change with the query change.
- **Headless READY still includes due tasks** in `bob query`, same class of bug as Today. Accept, or later teach the native engine `freshness.state` rather than inventing a tag.
- **Rubber-stamping NEW to empty the section** without actually confirming. Unchanged from the original ritual; wording stays "confirm."
- **Empty NEW is a success state.** Render `0` , never hide the section, so a missing filter cannot be mistaken for "all clear."

### Success

- Yesterday's captures sit in NEW, not READY, until a human gesture stamps them.
- A task whose lease expired overnight disappears from READY at local midnight without a hooks write, and appears in `rotten.md`.
- Alt+F on that line returns it to READY without a tag-strip.
- A resurfaced P1 roll appears in `rotten.md` the morning it returns, even if `[fresh::]` is still young.
- `READY n/100` counts the same rows the READY section shows.
- `bob task-status-hooks --dry-run` is a no-op for this feature.

## Sources

- Live vault (read-only): `dash.md`, `freshness.md`, `bob_gtd.md`, Tasks settings; `bob freshness list -f json`; `bob query --tasks-note dash.md`
- bob-cli: `docs/freshness.md`, `docs/plan.md`, `docs/task-status-hooks.md`, `src/native/freshness/state.rs`, `src/native/dataview/tasks/mod.rs` (`READY_QUERY`)
- bob-plugins: `plugins/bob-ledger-tools/main.js` (`api.freshness`, `readyCountFromTasks`, Today filters)
- Decisions: `today-is-read-from-the-ledger`, `task-lanes-are-sticky`, `task-status-is-derived` (Blocked remains derived; freshness is not a status)
- Glossary: Task Freshness
- Prior research: `research:202609/ready_task_freshness_review/ready_task_freshness_review.md` (launch recommendation this change deliberately evolves)

## About this report

- **Date:** 2026-10-01
- **Researcher:** grk (independent swarm member)
- **Question:** Best way to keep new and rotten tasks out of dash READY, show NEW on dash, show rotten in `rotten.md`; critique of using `task-status-hooks` + `#rotten`; is the plan a good idea.
