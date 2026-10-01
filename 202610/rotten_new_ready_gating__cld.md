# Gating READY on freshness: NEW section, ROTTEN note, and why not a `#rotten` tag

Researcher: cld · 2026-10-01 · repos: bob-cli, bob-plugins (`bob-ledger-tools`), the Bob vault

## Bottom line

1. **The goal is right, and it is a small step from what has already shipped.** A Ready task that
   nobody has confirmed should not sit in READY next to confirmed work. The proposal splits the
   visible, non-Today Ready lane into three exclusive buckets: **NEW** (on the dash), **READY**
   (on the dash) and **ROTTEN** (on its own note). Because each task lands in exactly one bucket,
   the dash sections stay mutually exclusive. The 2026-09 freshness research turned down dash
   sections only because they would *overlap* READY, and a split does not, so that objection
   does not apply here.
2. **Don't write a `#rotten` tag, and don't change `bob task-status-hooks`.** Nothing needs
   preprocessing. `bob-ledger-tools` already exposes `api.freshness.state(task)`, which returns
   `new | resurfaced | stale | fresh | null`. It already reloads open Tasks queries when the
   due set changes at local midnight (`TODAY_RELOAD_EVENT`). `~/bob/freshness.md` already uses
   it in a live Tasks query. A stored tag would repeat the `#today` tag that the accepted
   decision `today-is-read-from-the-ledger` turned down: a second copy of derived state, write
   churn, races and staleness. It would also be wrong between hooks runs, and those run **only
   on the MacBook**, every 15 minutes by cron.
3. **Adjustments I recommend.** Each is marked **ADJ** below.
   - "WIP" is now **PENDING**. It was renamed on 2026-09-30, so NEW goes between TODAY and
     PENDING.
   - **RESURFACED** tasks (deferrals whose `scheduled` date has arrived) belong in **NEW**, not
     ROTTEN. Otherwise every P-level deferral comes back off the dash. That breaks the tickler,
     and it breaks `blocked.md`'s promise that these tasks "land on the Dashboard tomorrow".
   - **Rename `freshness.md` to `rotten.md`** instead of adding a third review note. The
     **NEW and ROTTEN chips replace the REVIEW chip.**
   - Rename stale → rotten **everywhere** (Rust, JS, JSON, config, docs, glossary), and do it
     now, while freshness is one day old and nothing outside depends on it.
   - Gate through **one new API member**, `api.freshness.bucket(task)`. Every query should
     **fail open**: if ledger-tools is missing, READY shows what it shows today.
   - The READY chip, the daily `bob-plan` READY badge and the READY section must use the same
     gate, so the chip always matches the section.
4. **The real cost is behavioral, not technical.** After this change, a Ready task stays on
   the dash only while somebody re-confirms it every interval. On the live vault, the 199
   seeded tasks rot at 15–48 a day starting tomorrow. If no review happens, READY is down to
   about 11 tasks (recurring tasks only) by **2026-10-08**. That is the intended honesty, but
   it is a new obligation. Ship it with an escalation on the ROTTEN chip, plus `task_refresh`
   on the two big notes, and treat it as a two-week trial with a stated rule for when to
   reopen it.

The full design is under [Recommended solution](#recommended-solution).

---

## 1. What exists today (evidence)

| # | Fact | Evidence |
| --- | --- | --- |
| E1 | Freshness state is **computed at read time, never stored**: NEW (no stamp), RESURFACED (`fresh < scheduled ≤ today`), STALE (`today ≥ fresh + interval`), FRESH. A task is in scope only if it is TODO, visible in a lane, non-recurring, outside daily notes, and not in Today. | `docs/freshness.md` §4 |
| E2 | Only human gestures stamp. Automation (hooks, `projects sync`, `gkeep pull`, …) never stamps. "Freshness never changes a lane, Today, schedule, or priority." | `docs/freshness.md` §5; glossary `freshness` |
| E3 | `bob-ledger-tools` api v3 has `freshness.{state,isDue,tier,rank,queue,counts,…}`. All of them are synchronous and never throw. | `plugins/bob-ledger-tools/main.js` ≈L4700–4716 |
| E4 | `freshnessEnsureMemo()` rebuilds when the Tasks array, the local date, note `task_refresh` or the config changes. When the due set changes on rollover, it fires `obsidian-tasks-plugin:reload-open-search-results`, so open Tasks queries re-filter without any file write. | `main.js` `freshnessEnsureMemo`, `TODAY_RELOAD_EVENT` |
| E5 | `~/bob/freshness.md` is already a live Tasks query: `filter by function …freshness?.isDue?.(task)`, grouped NEW / DUE. The dash's **REVIEW** chip links to it. | vault `freshness.md`, `dash.md` |
| E6 | The dash sections are **TODAY / PENDING / NEXT / READY**, and they are exclusive by decision. "WIP Tasks" was renamed to "PENDING Tasks" on 2026-09-30 (vault commit `a0d6635c`). | `dash.md`, `decisions:today-is-read-from-the-ledger` |
| E7 | That decision turned down a hooks-managed `#today` tag as "a second copy of the ledger rewritten on task lines every 15 minutes, with churn, races, and staleness". | `decisions:today-is-read-from-the-ledger` |
| E8 | The freshness research turned down dash INBOX/STALE sections because "a dash section would violate the exclusivity decision (V7)". The alternatives it weighed were overlay sections. | `research:202609/ready_task_freshness_review/ready_task_freshness_review.md`, rows "Review surface", V7 |
| E9 | The same research kept *text writes out of the hooks* on purpose. They "today only swap checkbox bytes". | same report, row "Automated Blocked → Ready" |
| E10 | `bob task-status-hooks` runs **only on the MacBook**, by cron at `10,25,40,55 * * * *`. Writes use a lock, a byte re-check, a 2-second quiet window and retries, because they race with editors and the 15-second git sync. | `docs/vault-git-sync.md` "Mac scheduled maintenance"; `docs/task-status-hooks.md` "Retries" |
| E11 | The in-flight freshness-mark epic `bob-cli-3a` states the same principle for display: "Store absolute, show relative … Storing it would rot overnight." | `plan:202610/fresh_mark.md`; bead `bob-cli-3a` (IN_PROGRESS) |
| E12 | READY is counted **only in JS**. The dash chip and the daily `bob-plan` badge share `readyCountFromTasks` in ledger-tools. Rust has no native READY count. `READY_QUERY` in Rust is the freshness *universe*, not the dash READY. | `docs/plan.md` "READY backlog"; `main.js` `readyCountFromTasks`; `src/native/dataview/tasks/mod.rs` |
| E13 | `blocked.md`'s TOMORROW section says: "One-off tasks that land on the [[dash\|Dashboard]] tomorrow." | vault `blocked.md` |
| E14 | Capture's active-task completion already leaves out Ready tasks, so Bob Mac Capture is unaffected. | `src/native/capture_active_tasks.rs`, `capture_complete.rs` tests |

### Live numbers (2026-10-01, cutover day)

`bob freshness list -f json` with `BOB_NOW` stepped forward. No reviews are assumed, and
hooks-driven Blocked → Ready returns are not simulated.

| Date | rotten (stale) | fresh | Note |
| --- | --- | --- | --- |
| 10-01 | 0 | 199 | seed day; `refreshed_today` 391 |
| 10-02 | 26 | 173 | |
| 10-03 | 52 | 147 | |
| 10-04 | 78 | 121 | |
| 10-05 | 93 | 106 | |
| 10-06 | 113 | 86 | |
| 10-07 | 151 | 48 | |
| 10-08 | 199 | 0 | the whole seeded pool is rotten |

- **The pool is concentrated.** 199 in-scope tasks sit in 27 notes, but `gkeep_inbox.md`
  (65) and `sase.md` (60) hold **63%** of them.
- **No interval overrides yet.** No note sets `task_refresh` and no task sets `refresh`, so
  every task uses the default 7 days.
- **Other open TODO tasks.** About 445 open `[ ]` task lines exist outside `_templates` and
  `_conflicts`. Of the open `[ ]` tasks, 11 are recurring and 0 are in daily notes; both kinds
  are out of scope and stay in READY.
- **Arrivals.** About 28 `#task` lines were created per day in September (841 in total), and
  220 of them are still open `[ ]` outside the daily notes. The 2026-09 research expected about
  6–17 resurfacing deferrals a day.
- **Dependencies.** 14 open tasks carry `dependsOn`, and no open task uses `due`.

---

## 2. Is this a good idea?

**Yes, with an eyes-open caveat.** What it gets right:

- **READY becomes a claim, not a pile.** Today READY is "every TODO task not in Today", about
  210 rows. After the change it means "confirmed within its interval". The READY count also
  becomes informative: `max_ready: 100` turns into "how many tasks I'm willing to reconfirm
  each interval". That is a better backlog-pressure signal than raw size.
- **The inbox moves to where Bryan already looks.** Today NEW tasks are one click away behind
  the REVIEW chip, which only shows a count. A NEW section on the dash puts them right below
  TODAY, which matches the morning ritual ("until 0 new" comes first).
- **It is GTD-shaped.** The inbox (NEW) is not a next-actions list (READY), and tickler items
  go back to the inbox when they come due. That last point is why RESURFACED belongs in NEW
  (ADJ-2).
- **It costs no new mechanism.** It reuses the evaluator, the memo and the reload path that
  already run `freshness.md` and the status bar.

Risks to accept or mitigate:

1. **Review becomes mandatory for visibility.** Before, skipping the review only made a
   counter grow. After, skipping the review empties READY (see the table: zero by 10-08
   without reviews). The loop is honest, but it can also feed avoidance: rotten.md could
   become the next pile that dies, as the zorg-era `now_*`/`soon_*` lists did. Mitigations:
   - the ROTTEN chip escalates (ADJ-7);
   - longer intervals on the two big notes (`sase.md` → `task_refresh: 14` is a reasonable
     start);
   - route the 65 `gkeep_inbox.md` tasks out of the inbox note;
   - set the two-week keep rule in §6.4.
2. **Unblocked dependents can now vanish.** The freshness spec put off a "dependency returned"
   rule: "add a rule for them only if you miss one". Under gating, a task whose blocker just
   closed usually comes back *rotten*, which means **off the dash**, at exactly the moment it
   becomes actionable. Before, it at least reappeared in READY. 14 open dependents makes this
   small but real; ADJ-8 closes the gap.
3. **Headless and dash views diverge more.** `bob query --origin dash.md` cannot call plugin
   code, so headless READY will still include NEW and rotten tasks. This is the same accepted
   cost as "Headless `bob query` sees an empty Today". The headless review path is
   `bob freshness list`.
4. **"Rotten" passes judgment.** It describes the *confirmation*, not the task, and a rotten
   task may be perfectly valid. The word is still better than "stale" (see ADJ-4), and the
   nudge toward pruning is welcome. Tooltips should read "not confirmed in N days".

Would I take a different approach? **No**, as long as the gate is a **read-time view** and not a
stored marker, which is where the tag idea goes wrong. I considered "dim, don't hide": the
`bob-cli-3a` lease mark inside READY. It does not meet the goal. READY stays a 200-row scroll
and its count stays meaningless. It is a good complement, though: the fresh mark shows how
much lease is left on tasks that *are* in READY.

---

## 3. How to implement it: options compared

| Option | What it is | Verdict |
| --- | --- | --- |
| **A. `#rotten` (and `#new`) tag written by `task-status-hooks`** (the original idea) | The hooks evaluate freshness and add or remove a tag on task lines. Dash queries filter on the tag. | **Reject.** See §3.1. |
| **B. Read-time gate through `api.freshness`** | Tasks queries call `api.freshness.bucket(task)`. Nothing is written. | **Recommend.** |
| C. A status symbol or lane for rotten | For example a `[r]` checkbox. | **Reject.** It breaks "freshness never changes a lane", collides with the sticky-lane rules and with Blocked derivation, and forces hooks writes. |
| D. Inline date math in each dash query | Regex `fresh::` from `originalMarkdown`, resolve `task.file.property('task_refresh')`, compute with moment. | **Reject.** It would be a third evaluator. `docs/plan.md` and `docs/freshness.md` both require "every other surface calls one of those two". |
| E. One `bob-dashboard` block rendered by ledger-tools | Chips and sections come from a single plugin render. | **Fallback only.** It is already named as the fallback in `today-is-read-from-the-ledger`, if the Tasks reload event ever proves fragile. |
| F. ROTTEN as a folded callout at the bottom of the dash | No new note. | Inferior. The query still renders on every dash refresh, and it breaks the BLOCKED↗ pattern. |

### 3.1 Why a `#rotten` tag is the wrong tool here

1. **The repo has already decided this question.** `#today` was turned down for exactly this
   shape of problem (E7). Freshness is specified as "computed at read time, never stored"
   (E1), and `bob-cli-3a` repeats the principle for its display (E11). A tag would be the
   third such stored copy, and the first one written by automation.
2. **The tag is wrong between runs, and badly so after a review.** Suppose Bryan presses Alt+F
   on a rotten task:
   - it stays tagged, and so hidden from READY, until the next hooks run;
   - that run happens only on the MacBook, at most every 15 minutes, and only while the Mac
     is awake (E10);
   - if he works on apollo with the Mac asleep, the confirmation is invisible indefinitely.
   The symmetric failure also happens: at midnight about 28 tasks rot, but stay in READY until
   the next run.
3. **Fixing (2) spreads the problem.** To clear the tag on stamp, `stampLine` (JS) and
   `stamp_fresh` (Rust) would have to strip `#rotten`. That changes the placement contract,
   whose rule is "the suffix bytes themselves are never changed", along with its 18
   conformance vectors in both languages. Every stamping surface (nav, cycler, block-id-prompt,
   capture) would then also change task tags.
4. **It adds write churn and conflict surface.** At the live pool size it means about 28
   additions plus about 28 removals a day, spread across 27 notes, each one a git-synced
   diff. Those are text writes in a command that today swaps only checkbox bytes (E9), and
   every one goes through the lock, quiet-period and retry machinery that exists only because
   such writes race with editors (E10).
5. **It leaks into everything.** The tag shows up in the rendered task text, the tag pane,
   capture completion text and hooks change rows. It also lands in the Tasks suffix (a
   trailing tag), the most fragile part of the line.
6. **It buys almost nothing.**
   - The only benefit is that a plugin-free Tasks query or a headless `bob query` could filter
     on it.
   - The dash already depends on ledger-tools for Today. The headless consumer already has
     `bob freshness list -f json`.
   - Obsidian's global tag search is the one thing a tag adds, and `rotten.md` covers that.

**When a stored marker would become justified:** if the dash had to work with no plugin code
at all, for example on a mobile client without ledger-tools or in a Bases view that cannot call
plugin code. Neither applies today. That is the reopen condition to write into the decision
record.

---

## 4. Adjustments to the requirements

Each item states the original requirement, the change, and why.

- **ADJ-1: "above the WIP tasks section" becomes "between TODAY and PENDING".** The WIP
  section was renamed PENDING on 2026-09-30 (E6). The new order is TODAY → **NEW** → PENDING →
  NEXT → READY, which is also the morning ritual read top to bottom.
- **ADJ-2: RESURFACED tasks go to NEW, not ROTTEN, and not READY.** The request only
  classifies new and rotten tasks, so returning deferrals are left ambiguous.
  - **Not ROTTEN.** Every P-level deferral, which is how "not now" is answered during review,
    would come back into a note Bryan has to visit. That breaks `blocked.md`'s "land on the
    Dashboard tomorrow" (E13) and defeats the tickler.
  - **Not READY.** The task has not been re-confirmed; the spec makes it due "as soon as it
    returns". Among about 170 confirmed tasks it would be buried, which is the same burial
    problem freshness was built to fix.
  - **NEW** follows GTD's tickler → in-basket rule. Show it as a sub-group, NEW / RETURNED
    (`↩`), so "never seen" stays distinguishable.
- **ADJ-3: `freshness.md` becomes `rotten.md`, and NEW + ROTTEN replace the REVIEW chip.**
  Once NEW moves to the dash, `freshness.md` (NEW + DUE) and `rotten.md` would be two review
  notes over the same queue, with three chips (REVIEW, NEW, ROTTEN) counting overlapping sets.
  - Rename the note and keep `Freshness review` / `Review` as aliases, so existing links
    resolve.
  - Move its decision-key table over.
  - Point the status-bar click fallback (`openLinkText("freshness")` in ledger-tools) and the
    two `gtd_daily.md` chore lines at `rotten`.
- **ADJ-4: rename stale → rotten everywhere, now.** That covers:
  - the `stale` state and `counts.stale` (Rust and JS);
  - `stale_daily_budget` → `rotten_daily_budget` (unset in the live config, so the rename is
    free);
  - the S-vectors and P-vectors text, `bob freshness list` human and JSON output, the
    nav-hotkeys notices, the status bar, `docs/freshness.md` and the glossary strand.

  Rename everything rather than only the labels:
  - A UI that says "rotten" over code that says "stale" is a permanent translation tax.
  - "stale" is heavily overloaded in this codebase: stale plans, stale bytes and stale hints
    in the hooks, web-clip and vault-sync. "rotten" is unique and easy to grep.
  - Freshness landed today, so the only JSON consumers are humans. Bump `bob freshness list`
    to `schema_version: 2`.

  **Sequence it after `bob-cli-3a` lands**, because that epic is editing the same plugin, docs
  and "due" vocabulary right now.
- **ADJ-5: one shared gate, `api.freshness.bucket(task)` → `"new" | "rotten" | null`.**
  - `new` covers NEW and RESURFACED; `rotten` is the renamed STALE; `null` is FRESH or out of
    scope.
  - The dash, `rotten.md`, `readyCountFromTasks`, and the inline READY fallback in `dash.md` all
    call it. Nobody hand-writes `["new","resurfaced"].includes(state(...))` in vault queries.
  - Add bucket vectors to `docs/freshness.md` §10 (see §6.1).
  - Rust gets a matching `bucket` field on `bob freshness list` rows, so headless output uses
    the same words.
- **ADJ-6: fail open.** READY's filter is `(…bucket?.(task) ?? null) === null`. If ledger-tools
  is missing, old, or throwing, READY shows exactly what it shows today. NEW and `rotten.md`
  show nothing, and the NEW/ROTTEN chips show `–`. A gate that fails *closed* would hide the
  whole backlog whenever a plugin load fails.
- **ADJ-7: the ROTTEN chip escalates; `max_ready` keeps its meaning.**
  - **NEW** is red while it is above 0. This replaces REVIEW's `new > 0` rule.
  - **ROTTEN** is orange while above 0 and red once any rotten task is at least one full
    interval past due, i.e. a missed cycle; `days_overdue` is already in the queue. It also
    carries the refreshed-today meter: `ROTTEN 23 · ✓ 12` (`✓ 12/15` with a budget).
  - **READY** stays `n/max_ready` over the *gated* set, so the chip still equals the section
    (E12).
- **ADJ-8 (should-have, phase 2): a dependency return counts as RETURNED.** If any `dependsOn`
  target was completed after `fresh(t)` (its Tasks `done` date satisfies
  `fresh < done ≤ today`), treat the task like RESURFACED. It lands in NEW instead of silently
  rotting off the dash (risk 2). This extends the existing tickler rule to the other Blocked
  input. Hand unblocks already stamp.
- **ADJ-9 (optional): the `]s` walk order matches the dash.** Order the queue NEW → RETURNED →
  ROTTEN (today it is NEW → DUE by `due_on`), so Alt+Shift+F clears the dash's NEW section
  before it starts on rotten.md. This changes vector S14. Make `budget_met` require the NEW
  *section* to be empty (`new + resurfaced == 0`).

Everything else stays as it is:
- Freshness still never changes a lane, a status, Today, a schedule or a priority.
- Recurring tasks and daily-note tasks are out of scope and stay in READY.
- PENDING and NEXT have no freshness; they keep their caps and the weekly prune.

---

## 5. Edge cases checked

| Case | Behavior under the recommendation |
| --- | --- |
| Midnight rollover with no file change | The memo date changes, the due set changes, `TODAY_RELOAD_EVENT` fires, and open dash and `rotten.md` queries re-filter (E4). No write is involved. |
| Alt+F on a rotten task | The stamp rewrites the line. Tasks re-indexes the file and the next filter pass sees `fresh`. The task moves back to READY right away, on any machine. |
| A rotten task is linked to today | Ctrl+Shift+Enter or capture `plan_task_link` stamps it. Today tasks are out of scope anyway, so it shows in TODAY only. |
| New capture with an explicit route and priority | NEW until confirmed, by design ("creation never stamps"). It is *more* visible than READY, and confirming it takes one Alt+F. |
| Recurring Ready task, Ready task in a daily note | `state === null`, so the bucket is `null` and it stays in READY. |
| `#hide`, `_templates`, `_conflicts`, future `scheduled`, dependency-blocked | Out of scope, and already filtered out of READY. |
| ledger-tools not loaded | Fail open: READY looks as it does today (ADJ-6). |
| Headless (`bob query`, agents) | READY is ungated, as Today is today. Use `bob freshness list` (with ADJ-5 `bucket`). |
| Bob Mac Capture | No change. Completion already leaves out Ready tasks (E14). |
| Performance | See the note below. |

**Performance.** Each `api.freshness.state(task)` call:
- re-reads `~/.config/bob/config.yml` synchronously, through `freshnessEnsureMemo` →
  `loadFreshnessConfig` (also flagged in `plan:202610/fresh_mark.md`);
- runs `tasks.indexOf(task)` over roughly 3,500 tasks;
- recomputes the row.

The dash would call it about 445 × 2 times per re-render, and Tasks re-renders on every task
edit. `bucket()` should instead be an O(1) lookup in a `key → bucket` map built once per memo,
and the config read should be cached by mtime. Put the cheap `status.type is TODO` line first in
each query.

---

## 6. Recommended solution

### 6.1 Contract (bob-cli `docs/freshness.md`, mirrored in ledger-tools)

```text
state(t)   = NEW | RESURFACED | ROTTEN | FRESH | null   (STALE renamed ROTTEN; rules unchanged,
             plus ADJ-8: RESURFACED also when a dependsOn target was done after fresh(t))
bucket(t)  = "new"    if state ∈ {NEW, RESURFACED}
           | "rotten" if state = ROTTEN
           | null     otherwise (FRESH, or out of scope)

Dash READY   = today's READY predicate ∧ bucket(t) = null      (fails open)
Dash NEW     = bucket(t) = "new"        (grouped NEW / ↩ RETURNED)
rotten.md    = bucket(t) = "rotten"     (ordered by queue rank; grouped by note)
```

Suggested bucket vectors (B), using the existing S-vector setup:

- **B1:** S1 (no `fresh`) → `new`
- **B2:** S11 (resurfaced) → `new`
- **B3:** S3 and S4 → `rotten`
- **B4:** S2, S5, S7 and S12 → `null`
- **B5:** every S13 out-of-scope row → `null`
- **B6 (ADJ-8):** `fresh 2026-10-01`, a dependency done on 2026-10-06 → `new`
- **B7:** the same task with the dependency done on 2026-09-30 → per S-rules.

### 6.2 Surfaces

**`dash.md` (vault).** TQ defaults as today, then:

````markdown
### TODAY Tasks
(unchanged)

### NEW Tasks

```tasks
status.type is TODO
filter by function globalThis.app?.plugins?.plugins?.["bob-ledger-tools"]?.api?.freshness?.bucket?.(task) === "new"
group by function (globalThis.app?.plugins?.plugins?.["bob-ledger-tools"]?.api?.freshness?.state?.(task) === "resurfaced") ? "↩ RETURNED" : "NEW"
sort by function globalThis.app?.plugins?.plugins?.["bob-ledger-tools"]?.api?.freshness?.rank?.(task) ?? 0
```

### PENDING Tasks
(unchanged)

### NEXT Tasks
(unchanged)

### READY Tasks

```tasks
status.type is TODO
filter by function globalThis.app?.plugins?.plugins?.["bob-ledger-tools"]?.api?.isToday?.(task) !== true
filter by function (globalThis.app?.plugins?.plugins?.["bob-ledger-tools"]?.api?.freshness?.bucket?.(task) ?? null) === null
```
````

**Chip row.** `NEW` (in-page, red while above 0), `PENDING`, `NEXT`, `READY` (shared badge,
gated count), `ROTTEN ↗` (orange or red per ADJ-7, with `✓ n` today), `BLOCKED ↗`, `TODAY ↗`.
Drop `REVIEW`. Pass an explicit `destination: "Rotten Tasks"`, because `renderChip` defaults
external chips' aria text to "Blocked Tasks".

**`rotten.md` (vault).** Rename it from `freshness.md`:
- `parent: "[[dash]]"`, with aliases `Rotten Tasks`, `Freshness review` and `Review`;
- a one-line dataviewjs summary: `23 rotten · oldest 9d · ✓ 12 today`;
- the existing decision-key table;
- a query with `filter by function …bucket?.(task) === "rotten"`, sorted by `rank` and grouped
  by path, so Bryan can clear one note at a time (63% of the pool lives in two notes).

**Status bar.** `⟳ 3 new · 23 rotten · ✓ 12 today`. The click fallback opens `rotten`.

**Ritual (`docs/freshness.md` §6 and `gtd_daily.md`).**
1. Morning: `bob gkeep pull`, then clear the dash's NEW section to 0. That step is never
   skipped.
2. Clear ROTTEN↗ down to the budget.
3. Then PENDING → NEXT → link and release.
4. Weekly: any rotten task more than one interval overdue gets a decision: cancel, P4, or a
   longer `task_refresh` for its note.

### 6.3 Work by repo (one epic; sequence after `bob-cli-3a` lands)

1. **`vocab-rotten`** (bob-cli and bob-plugins, a pure rename):
   - stale → rotten in Rust `freshness/*`, `config/freshness.rs` (`rotten_daily_budget`) and
     the CLI human and JSON output (`schema_version: 2`);
   - ledger-tools evaluator, counts and status bar; the nav-hotkeys notices; the
     `test-*freshness*.cjs` vectors; `docs/freshness.md`.
2. **`bucket-api`** (bob-plugins, then bob-cli docs):
   - `api.freshness.bucket` with a memoized key map and a cached config read;
   - `freshness.version` → 2, additive;
   - `readyCountFromTasks` applies the gate (fail-open);
   - counts expose `new`, `resurfaced` and `rotten`;
   - B-vectors in both languages; a `bucket` field in `bob freshness list` JSON;
   - a `docs/plan.md` "READY backlog" sentence: "…and freshness-gated tasks (bucket `new` or
     `rotten`)".
3. **`dash-gating`** (vault):
   - the NEW section and the READY filter in `dash.md`, plus the inline READY fallback count;
   - chips;
   - `freshness.md` → `rotten.md`;
   - the `gtd_daily.md` chores;
   - `task_refresh: 14` on `sase.md` (Bryan's call);
   - live-verify that the chip counts equal the section counts on athena/apollo and the Mac.
4. **`dependency-return`** (ADJ-8, both languages and vectors) and optionally **`walk-order`**
   (ADJ-9). These can follow a week later.
5. **Memory** (part of the plan's steps, so plan approval authorizes it under the
   `sase_memory_write` rules):
   - Update the glossary `freshness` strand: "stale" → "rotten", and add "due tasks leave
     READY: NEW on the dash, ROTTEN on `rotten.md`".
   - Add a decisions record, for example *"READY Shows Only Confirmed Tasks; NEW And ROTTEN Are
     Read-Time Views"*:
     - **Claim:** the gate is read-time and never a tag. The four exclusive sections become
       five: TODAY / NEW / PENDING / NEXT / READY.
     - **Rejected alternatives:** a `#rotten` tag via hooks, a status symbol, inline query date
       math, dim-not-hide.
     - **Cost:** review is required for visibility.
     - **Reopens when:** a plugin-free surface must show the gate, or the trial fails.
   - Mark `today-is-read-from-the-ledger` as `superseded-in-part` for its section list only.

**`bob task-status-hooks`: no change.**

### 6.4 Trial and keep rule

Run it for two weeks, 2026-10-05 → 2026-10-18, and **keep it** if:
- ROTTEN is red on no more than 3 mornings;
- READY holds at least about 30 confirmed tasks on most mornings, which shows reviews are
  keeping up;
- no reported case of "I lost a task I needed" that a NEW, RETURNED or dependency-return path
  should have caught.

If READY collapses and ROTTEN grows, first lengthen the intervals on the large notes. Only then
consider **dim-not-hide** (rotten tasks shown at the bottom of READY with the `bob-cli-3a`
mark) as the fallback. Don't fall back to a stored tag.

---

## Sources

- bob-cli `docs/freshness.md` (§§1, 4, 5, 6, 8–10), `docs/plan.md` ("READY backlog"),
  `docs/task-status-hooks.md` ("Retries"), `docs/vault-git-sync.md` ("Mac scheduled
  maintenance"), `src/native/dataview/tasks/mod.rs` (`READY_QUERY`),
  `src/native/freshness/`.
- bob-plugins `plugins/bob-ledger-tools/main.js`:
  - the `api.freshness` namespace;
  - `freshnessEvaluate`, `freshnessTierForState`, `freshnessEnsureMemo` and
    `freshnessBuildMemo`;
  - `readyCountFromTasks`, `TODAY_RELOAD_EVENT`, and the status-bar fallback
    `openLinkText("freshness")`.
- bob-plugins `plugins/bob-navigation-hotkeys/main.js`: the nav-review section, and Alt+F /
  Alt+Shift+F acting on editor lines.
- Vault (read-only):
  - `dash.md` and its history (`a0d6635c`, WIP → PENDING);
  - `freshness.md`, `blocked.md` and `gtd_daily.md`;
  - live `bob freshness list -f json` with `BOB_NOW` 2026-10-01…10-15.
- Memory: `decisions:today-is-read-from-the-ledger`, `decisions:task-lanes-are-sticky`,
  `decisions:task-status-is-derived`, glossary `freshness`.
- Prior research: `research:202609/ready_task_freshness_review/ready_task_freshness_review.md`.
  Plans: `plan:202610/fresh_mark.md` (bead `bob-cli-3a`) and `plan:202610/ready_badge.md`.
