# Freshness-gated READY: NEW on the dash, ROTTEN in `rotten.md`, no `#rotten` tag

## Bottom line

1. **The plan is a good idea, and all six analyses agree.** The `[fresh::]` stamp exists so that
   READY can mean "a human endorsed this recently". Without the split it never will. Mixing
   unconfirmed captures, expired confirmations, and confirmed work under one heading teaches Bryan
   to distrust the heading. Splitting them costs almost nothing, because the evaluator, its memo,
   the midnight refresh, and a live Tasks-query example (`freshness.md`) have already shipped.
   (See [Is this a good idea](#is-this-a-good-idea).)
2. **Don't write a `#rotten` tag, and don't change `bob task-status-hooks`.** All six analyses
   agree here too. Rotten is a function of the calendar, so a stored tag is wrong from local
   midnight until the next hooks run. The hooks run only on the MacBook, every 15 minutes, and
   only while it is awake. The tag would also be wrong after every Alt+F unless every stamping
   surface learned to strip it. This is the `#today` tag that
   `decisions:today-is-read-from-the-ledger` already rejected. The "preprocessing" already
   exists: it is `api.freshness` in bob-ledger-tools, which Tasks `filter by function` can call.
   (See [why read-time filters beat a rotten tag](#why-read-time-filters-beat-a-rotten-tag).)
3. **Implement it as a read-time partition of the visible Ready lane.** Every task lands in
   exactly one place:

   | Evaluator state | Surface |
   | --- | --- |
   | `new` | `dash.md` → **NEW Tasks** (new section, between TODAY and PENDING) |
   | `resurfaced` | `rotten.md` → **RETURNED** group |
   | `stale` (shown as **rotten**) | `rotten.md` → **ROTTEN** group |
   | `fresh` | `dash.md` → **READY Tasks** |
   | `null` (recurring or daily-note Ready tasks) | `dash.md` → **READY Tasks** (exempt, unchanged) |

   (See the [contract](#contract).)
4. **Change the badges in the same release as the queries.** The READY chip and the daily
   `bob-plan` READY badge must count the gated set. A new NEW chip and a ROTTEN ↗ chip replace
   REVIEW. `freshness.md` becomes `rotten.md`, so there is one review page, not two. (See ADJ-3
   and ADJ-4 in [Requirement adjustments](#requirement-adjustments).)
5. **The real cost is the habit, not the code.** Starting tomorrow, the 199 seeded tasks rot
   15–48 a day (≈28 on average). With no reviews, READY shrinks to the 11 recurring tasks by
   2026-10-08 ([verified below](#live-numbers)). That is the intended honesty, but it makes the
   morning review a condition for seeing the backlog at all. Ship it as a
   [two-week trial with a stated keep rule](#trial-and-keep-rule).

The adjustments to the request are marked **ADJ-n** in
[Requirement adjustments](#requirement-adjustments). The full design is in
[Recommended solution](#recommended-solution).

![Infographic of the recommendation: the visible Ready pool splits four ways, with NEW tasks (no freshness stamp) going to the dash's NEW section, FRESH tasks staying in READY along with recurring and daily-note tasks, and RETURNED and ROTTEN tasks moving to rotten.md behind a ROTTEN badge; the dash order TODAY, NEW, PENDING, NEXT, READY; computing at read time with no #rotten tag and no new hooks writes; honest counts, with NEW and ROTTEN replacing REVIEW and freshness.md becoming rotten.md; review as the real cost, with 199 seeded fresh tasks reaching 0 by Oct 8 with no reviews; and the two-week trial from Oct 5 to Oct 18, 2026 with its keep rule](freshness_gated_ready_dash_infographic.png)

## What is already true

### Evidence

| # | Fact | Evidence |
| --- | --- | --- |
| E1 | Freshness is "computed at read time, never stored". The states are NEW (no stamp), RESURFACED (`fresh < scheduled ≤ today`, which beats STALE), STALE (`today ≥ fresh + interval`), and FRESH. In scope means TODO, lane-visible, non-recurring, not in a daily note, and not Today. Tiers are NEW and DUE (RESURFACED + STALE), and the queue orders NEW before DUE. | `docs/freshness.md` §4 |
| E2 | Only human gestures stamp. Scheduling a task into the future stamps it, and it becomes Blocked. When the hooks return it from Blocked to Ready, they never stamp, so it comes back RESURFACED. | `docs/freshness.md` §5 |
| E3 | bob-ledger-tools api v3 exposes `freshness.{state,isDue,tier,rank,queue,counts,stampLine,…}`. Every member is synchronous and never throws. The plugin is **not** desktop-only (`isDesktopOnly: false`). | `plugins/bob-ledger-tools/main.js`, `manifest.json` |
| E4 | The memo rebuilds when the Tasks array, the local date, a note's `task_refresh`, or the config changes. A midnight-rollover path (`refreshFreshnessForRollover`) fires `obsidian-tasks-plugin:reload-open-search-results` when the due set changes, so open queries re-filter without any file write. | `main.js` `freshnessEnsureMemo`, `TODAY_RELOAD_EVENT` |
| E5 | The live dash sections are TODAY / PENDING / NEXT / READY. Exclusivity is already a plugin filter (`isToday === true` vs `!== true`), not a tag. "WIP Tasks" was renamed PENDING on 2026-09-30. The chips are PENDING, NEXT, READY, BLOCKED ↗, REVIEW ↗ (`freshness.md`), and TODAY ↗. | vault `dash.md`; vault commit `a0d6635c` |
| E6 | `freshness.md` is already a live Tasks query (`isDue`, `rank`, `tier`) grouped NEW → DUE. The status-bar click fallback is `openLinkText("freshness")`. The `gtd_daily.md` morning chore links [[freshness\|REVIEW]]. | vault; `main.js` |
| E7 | READY is counted only in JavaScript: `readyCountFromTasks` covers TODO, visible, unblocked, non-Today tasks and has no freshness term. Its cap `plan.max_ready: 100` is a soft "backlog pressure" signal. | `main.js:3025`; `docs/plan.md` "READY backlog"; `plan:202610/ready_badge.md` |
| E8 | **The review gestures act on editor lines.** Alt+F and Alt+Shift+F stamp the task under the cursor, or a Task Link's target. `]s` walks the vault-wide queue by opening each source note. Rows rendered by a Tasks query on `dash.md` or `rotten.md` are maps you click through, not places where the gesture runs. | `bob-navigation-hotkeys/main.js` `refreshTaskFreshness`, nav-review section |
| E9 | `bob task-status-hooks` runs only on the MacBook, by cron every 15 minutes. Its writes go through a lock, a byte re-check, a quiet window, and retries, because they race with editors and the git sync. Hooks change checkbox bytes, never inline fields or tags. | `docs/vault-git-sync.md`; `docs/task-status-hooks.md` |
| E10 | Bryan has already filed this feature and three siblings in `bob_gtd.md`: `^hide-rotten-tasks` ("Hide rotten tasks in [[dash]]! Show them in [[rotten]]!"), `^scheduled-are-stale` ("Make sure scheduled tasks are treated as stale!"), `^wip-next-refresh` (1-day interval for WIP/NEXT), and `^prj-task-count-warn`. | vault `bob_gtd.md` lines 21–24 |
| E11 | The in-flight fresh-mark epic `bob-cli-3a` gives STALE and RESURFACED the same `due` tone (`⟳`, orange). Its rule is "store absolute, show relative". | `docs/freshness.md` §11; bead `bob-cli-3a` (IN_PROGRESS) |
| E12 | Live config has no `freshness:` block, so `stale_daily_budget` is unset. No consumer of `bob freshness` JSON or the `stale` state exists in bob-cli (outside `src/native/freshness/`), in Bob Mac Capture, or in the vault. "stale" is also used in nav and the cycler with unrelated meanings (stale sessions, stale coordinates). | `~/.config/bob/config.yml`; greps |

### Live numbers

Lead-verified, read-only, 2026-10-01.

| `BOB_NOW` | fresh | rotten (`stale`) | new | resurfaced |
| --- | ---: | ---: | ---: | ---: |
| 2026-10-01 | 199 | 0 | 1 | 0 |
| 2026-10-02 | 173 | 26 | 1 | 0 |
| 2026-10-03 | 147 | 52 | 1 | 0 |
| 2026-10-08 | 0 | 199 | 1 | 0 |

- **No reviews and no hooks runs are simulated.** Blocked deferrals therefore never return, so
  RESURFACED stays 0 here. The 2026-09 research expected about 6–17 returns a day.
- **The decay is staggered, not a cliff.** The cutover seed bin-packed stamps into 7 daily
  buckets, so the steady-state review load is about pool ÷ interval ≈ 28 rotten a day, plus
  arrivals. September averaged about 28 new `#task` lines a day (cld).
- **READY today is 211 headless:** 199 fresh, 11 recurring (exempt), and the 1 task captured this
  morning (NEW). The pool is concentrated: `gkeep_inbox.md` (65) and `sase.md` (60) hold 63% of it
  (cld).
- **Headless queries fail the way the reports predicted.** In `bob query -o dash.md`, a filter on
  `…freshness?.state?.(task) === "new"` returns **0**, and one on
  `…freshness?.isDue?.(task) !== true` returns **211**. The native engine does run
  `filter by function` (mus is right), but `globalThis.app.plugins` does not exist there (cdx is
  right). NEW and ROTTEN come back empty and READY falls back to unfiltered. This is the same
  accepted cost as "headless sees an empty Today".

## Is this a good idea

**Yes.**

### What it gets right

- **READY becomes a claim, not a pile.** Today READY means "every TODO task not in Today". After
  the change it means "confirmed within its interval, safe to pull".
- **The inbox moves to where Bryan already looks.** NEW is the one tier the ritual never caps or
  skips. Today it sits behind a REVIEW chip and a second note.
- **Review debt becomes visible without polluting the board.** Rotten work stays one click away
  through a counted chip, the same pattern as BLOCKED ↗ → `blocked.md`.
- **It needs no new mechanism, no migration, and no backfill.** Day one looks almost identical
  (1 NEW, 0 rotten), and the sections fill as tasks age, so this is the cheapest moment to land
  it.
- **Exclusivity is preserved.** The split carves READY into disjoint pieces whose union is today's
  READY. The 2026-09 research rejected dash INBOX/STALE sections only because they would overlap
  READY (V7), and a split does not.

### Risks to accept or mitigate

The reports caught 1–3; the lead added 4 and 5.

1. **Seeing the backlog now depends on reviewing it.** If Bryan skips the review, READY empties
   and `rotten.md` becomes the next pile that dies, as the zorg-era `now_*`/`soon_*` lists did.
   Mitigations:
   - make the ROTTEN chip escalate (ADJ-8);
   - give the two big notes longer intervals (`sase.md` → `task_refresh: 14` is a reasonable
     start; that is Bryan's call);
   - do a one-time triage of `gkeep_inbox.md`;
   - run it as a trial with a keep rule (see [Trial and keep rule](#trial-and-keep-rule)).
2. **Headless views diverge further from the dash.** `bob query` READY stays ungated. The headless
   review path remains `bob freshness list`.
3. **"Rotten" passes judgment.** It describes the *confirmation*, not the task, and a rotten task
   may be perfectly valid. Tooltips should say "not confirmed in N days". The word itself is still
   an improvement (ADJ-5).
4. **Gating gives the READY cap a perverse incentive (lead).** `max_ready` was built as backlog
   pressure ([E7](#evidence)). Once READY counts only confirmed tasks, *skipping review lowers the
   READY count* and can turn an over-cap chip green. Every report says "make the chip match the
   section", and it must. But the counterweight has to be explicit:
   - the ROTTEN chip escalates;
   - the READY tooltip shows the whole lane (`READY 120/100 · lane 210 = 3 new + 87 rotten + 120`).
5. **The dash sections are views, not workbenches (lead, [E8](#evidence)).** The keymaps run on
   editor lines, so the review itself is still the `]s` / Alt+Shift+F walk, which goes NEW → DUE in
   queue order. The new surfaces *show* the queue; they do not replace the walk. The recommended
   layout keeps the dash and the walk in the same order (NEW on the dash first, then `rotten.md`'s
   DUE), so no walk-order change is needed. This is also one of the reasons for ADJ-2.

### Would I take a different approach

Only on the mechanism (see
[why read-time filters beat a rotten tag](#why-read-time-filters-beat-a-rotten-tag)). Several
alternatives were weighed:

- **"Dim, don't hide":** keep rotten rows in READY, marked with the bob-cli-3a `⟳` mark. It fails
  the goal. READY stays a 200-row scroll and its count stays meaningless.
- **Grouping one READY section** into FRESH, NEW, and ROTTEN groups. It still puts rotten work on
  the board, which is the thing the request is trying to stop.

Keep "dim, don't hide" as the fallback if the trial fails (see
[Trial and keep rule](#trial-and-keep-rule)), never a stored tag.

## Why read-time filters beat a rotten tag

This is the mechanism question: read-time filters versus a `#rotten` tag.

### Options compared

| Option | Verdict | Why |
| --- | --- | --- |
| **A. `#rotten` (and/or `#new`) written by `task-status-hooks`** (the original idea) | **Reject** | See [below](#why-the-tag-is-the-wrong-cache). |
| **B. Read-time Tasks filters through `api.freshness`** | **Recommend** | Uses the existing evaluator, memo, and midnight reload. Updates the moment a stamp or the calendar changes. Writes nothing. |
| C. A stored `[rotten::]` / `[freshness::]` field | Reject | Same staleness as A. An unknown trailing field also hides Tasks fields: the placement trap proven in 2026-09. |
| D. A status symbol or lane for "needs review" | Reject | Breaks "freshness never changes a lane" and collides with sticky lanes and derived Blocked. |
| E. Inline date math in each query (regex on `fresh::`) | Reject | A third evaluator; both contracts say every surface must call the shared one. |
| F. A generated or materialized `rotten.md` (copied or moved lines) | Reject | Stale between runs, and moving lines destroys project context and Work Logs. |
| G. One `bob-dashboard` block rendered by the plugin | Fallback only | Already named as the Today decision's fallback in case the Tasks reload event proves fragile. |

### Why the tag is the wrong cache

The reasons below are merged from all five reports and checked against the code.

1. **The repo has already decided this question.** Freshness is "never stored" ([E1](#evidence)),
   `today-is-read-from-the-ledger` rejected a hooks-managed `#today` tag for its "churn, races,
   and staleness", and bob-cli-3a restates "store absolute, show relative" (E11).
   - *Correction:* gem says `now-tag-is-user-owned` records a cron tagging trial that failed. It
     does not. That record only rejects cron sweeps as an alternative. The applicable precedent is
     the `#today` rejection.
2. **The tag is wrong in both directions between runs.**
   - About 15–48 tasks (≈28 on average) rot at each midnight but stay in READY until the next
     MacBook hooks pass.
   - A rotten task Bryan confirms with Alt+F stays hidden until that pass. If he works on apollo
     with the Mac asleep, the confirmation never shows up.
   - Mobile never runs the hooks at all.
3. **Fixing the lag spreads the problem across every writer.** Every stamping surface would have
   to strip `#rotten` in the same write: nav (Alt+F, Alt+N, Ctrl+Shift+P, Ctrl+Shift+M, `!`), the
   cycler, block-id-prompt, and capture (`stamp_fresh`). That changes the placement contract and
   its two-language conformance vectors. Miss one writer and FRESH tasks wear the tag
   indefinitely.
4. **It turns the hooks into a text writer.** Hooks today swap checkbox bytes (E9). A tag adds
   about 50 time-driven line rewrites a day across about 27 notes, each a git-synced diff in the
   most fragile part of the line (the trailing Tasks suffix).
5. **It leaks.** A tag shows in rendered text, the tag pane, search, Dataview `tags`, copies, and
   templates. A filter predicate is invisible until rendered.
6. **It buys almost nothing.** The only gain would be plugin-free filtering:
   - the dash already depends on ledger-tools for Today;
   - the READY cap is already computed in JavaScript;
   - headless readers already have `bob freshness list`.

**When a stored marker would become justified:** a surface that must show the gate with no plugin
code, such as a client without ledger-tools or a Bases view. Neither exists today. Record this as
the reopen condition.

## Requirement adjustments

These are the adjustments to the request, called out. Each adjustment states the original
requirement, then the change. The rationale for several of them is in
[Disagreements and resolutions](#disagreements-and-resolutions).

- **ADJ-1: "above the WIP tasks section" → between TODAY and PENDING.** The WIP section is now
  PENDING (renamed 2026-09-30). Order: TODAY → **NEW** → PENDING → NEXT → READY.
- **ADJ-2: RESURFACED (returned deferrals) also leave READY, and go to `rotten.md` under their own
  RETURNED heading.** The request names only new and rotten tasks, so returned deferrals would
  otherwise be orphaned or misfiled. They count toward the ROTTEN chip, and the tooltip shows the
  split. Update `blocked.md`'s TOMORROW caption to match. This also satisfies
  `^scheduled-are-stale`. Verify with one S11-style vector, then close that task with this work.
- **ADJ-3: there is one review note.** Rename `freshness.md` to `rotten.md` rather than adding a
  third review surface. Move the one-key decision table over and keep the old aliases.
- **ADJ-4: chips.**
  - Add **NEW** (an in-page anchor, red while above 0).
  - Add **ROTTEN ↗** (external, to `rotten.md`).
  - Drop **REVIEW**.
  - The **READY** chip and the daily `bob-plan` READY badge count the gated set, so each chip
    equals its section.
- **ADJ-5: vocabulary.** Change user-facing text to "rotten" now: headings, chips, the status bar,
  `bob freshness list` human output, docs, and the glossary. Then rename the machine contract in a
  follow-up phase:
  - `FreshState::Stale` → `Rotten`;
  - the JS state `"stale"` → `"rotten"`;
  - JSON `counts.stale` → `counts.rotten` with `schema_version: 2`;
  - `stale_daily_budget` → `rotten_daily_budget`, accepting the old key with a lint for one
    release;
  - keep `resurfaced`, `refresh`, and `task_refresh`.
- **ADJ-6: out-of-scope Ready tasks stay in READY.** This covers recurring tasks and Ready tasks
  in daily notes. The partition applies only to the freshness scope.
- **ADJ-7: fail open.**
  - Without ledger-tools (missing, old, or throwing), READY shows exactly what it shows today.
  - NEW and `rotten.md` render empty.
  - The NEW and ROTTEN chips show `–`, so an absent plugin cannot be mistaken for a clean queue.
- **ADJ-8: the ROTTEN chip escalates.** Orange while above 0. Red once any rotten or returned task
  is at least one full interval past its `due_on` (a missed cycle). It carries the meter
  (`ROTTEN 23 · ✓ 12`, or `✓ 12/15` with a budget).
- **ADJ-9: NEW is never capped or truncated.** Render `0` when it is empty, and never hide the
  section, so a broken filter cannot pass for "all clear".
- **ADJ-10: freshness scope does not grow in this change.** `^wip-next-refresh` (a 1-day interval
  for Next and Pending) is a separate decision. At today's counts (49 PENDING, 32 NEXT) it would
  add about 80 must-review items every morning. If adopted later, it lands in the evaluator and
  `bucket`, and `rotten.md` keeps working because it filters on `bucket`, not on
  `status.type is TODO`.

Everything else stays as it is:

- Freshness never changes a lane, a status, Today, a schedule, or a priority.
- Hooks, capture, and Bob Mac Capture are unchanged. Capture's active-task completion already
  excludes Ready tasks.

## Recommended solution

### Contract

The contract lives in bob-cli `docs/freshness.md` and is mirrored in bob-ledger-tools.

```text
state(t)   = NEW | RESURFACED | STALE ("rotten" in all user-facing text) | FRESH | null   (unchanged)
bucket(t)  = "new"    if state(t) = NEW
           | "rotten" if state(t) ∈ {RESURFACED, STALE}
           | null     otherwise (FRESH, or out of scope)

dash NEW    = bucket(t) = "new"
dash READY  = today's READY predicate ∧ bucket(t) ≠ "new" ∧ bucket(t) ≠ "rotten"   (fail-open)
rotten.md   = bucket(t) = "rotten", grouped RETURNED (resurfaced) then ROTTEN, each by queue rank

Invariant: visible READY-lane total = NEW + RETURNED + ROTTEN + READY  (no task in zero or two places)
```

- **Bucket vectors.** Add them next to the S-vectors in `docs/freshness.md` §10:
  - S1 (no `fresh`) → `new`;
  - S11 (resurfaced) → `rotten`;
  - S3 and S4 (stale) → `rotten`;
  - S2, S5, S7, and S12 → `null`;
  - every S13 out-of-scope row → `null`.
- **Headless.** `bob freshness list -f json` rows gain an additive `bucket` field, so headless
  output uses the dash's words.
- **cld's variant.** If Bryan prefers returned deferrals on the board, the change is one line:
  `resurfaced → "new"`. Group NEW by `state` into NEW and `↩ RETURNED`, and reorder the walk to
  NEW → RETURNED → ROTTEN.

### bob-ledger-tools changes

These changes are in bob-plugins, and they land first.

1. **Make lookups O(1).**
   - Add a `key → {state, bucket}` map to `freshnessBuildMemo`, using the same path+block-id or
     path+line key as `rank`.
   - Have `state`, `isDue`, `tier`, and `bucket` read it, falling back to today's per-row
     evaluation only on a miss.
   - Cache the config snapshot by file mtime, or once per tick, instead of a `readFileSync` and
     YAML parse on every call.
   - Stop calling `freshnessEnsureMemo` twice per call.
2. **Add `api.freshness.bucket(task)`.** It is additive: `freshness.version` 1 → 2, api stays v3.
   It never throws and returns `null` on failure.
3. **Gate the READY count.** `readyCountFromTasks` and `readyBudgetFromTasks` take a bucket
   predicate and skip `"new"` and `"rotten"`. When the predicate is absent or throws, they count
   as today (fail-open) rather than reporting a partial count.
4. **Add a ROTTEN chip model and update the status bar.**
   - The model's count is `resurfaced + stale`. Its tooltip reads `ROTTEN 31 · 4 returned ·
     27 rotten · oldest 9d · ✓ 12 today`. It goes red per ADJ-8, using `due_on` from the queue
     rows.
   - The status bar reads `⟳ 3 new · 31 rotten · ✓ 12 today`.
   - The click fallback becomes `openLinkText("rotten")`.
5. **Tests** (in `test-ledger-tools-freshness.cjs` and `test-ledger-tools-ready-badge.cjs`):
   - the bucket vectors;
   - a recurring task stays in the READY count;
   - the plugin-absent fallback;
   - chip count equals section count;
   - midnight rollover moves a task FRESH → rotten with no write.

### Vault changes

**`dash.md` Tasks blocks.** The frontmatter `TQ_extra_instructions` already applies the shared
filters: not blocked, `#hide`, not future-scheduled, and self-exclusion.

````markdown
### TODAY Tasks
(unchanged)

### NEW Tasks

```tasks
status.type is TODO
filter by function globalThis.app?.plugins?.plugins?.["bob-ledger-tools"]?.api?.freshness?.bucket?.(task) === "new"
```

### PENDING Tasks
(unchanged)

### NEXT Tasks
(unchanged)

### READY Tasks

```tasks
status.type is TODO
filter by function globalThis.app?.plugins?.plugins?.["bob-ledger-tools"]?.api?.isToday?.(task) !== true
filter by function !["new", "rotten"].includes(globalThis.app?.plugins?.plugins?.["bob-ledger-tools"]?.api?.freshness?.bucket?.(task))
```
````

- **No `isToday` filter on NEW.** Today tasks are out of freshness scope, so their bucket is
  already `null`.
- **The READY filter fails open.** If the API is missing, `bucket` returns `undefined` and every
  task stays in READY.
- **Chip row.** NEW (in-page, red while above 0) · PENDING · NEXT · READY (shared gated badge) ·
  BLOCKED ↗ · ROTTEN ↗ (orange or red per ADJ-8) · TODAY ↗.
  - Delete the REVIEW computation and its CSS. Add `.task-count-rotten` and `.task-count-new`
    accents.
  - Pass an explicit `destination: "Rotten Tasks"`, because external chips' aria text otherwise
    defaults to "Blocked Tasks" (cld).
  - Update the inline READY fallback count to the same predicate.

**`rotten.md`** is created by renaming `freshness.md`:

- Frontmatter: `parent: "[[gtd]]"`, aliases `Rotten Tasks`, `Freshness review`, and `Review`.
- A one-line dataviewjs summary, e.g. `31 rotten · 4 returned · oldest 9d · ✓ 12 today`.
- One purpose line: "Ready tasks whose confirmation expired or whose deferral came back. Start
  with `]s` / Alt+Shift+F. Everything confirmed lives on the [[dash|Dashboard]]."
- The existing one-key decision table, moved from `freshness.md`.
- Two Tasks blocks:
  - `## RETURNED Tasks`: `bucket === "rotten" && state === "resurfaced"`.
  - `## ROTTEN Tasks`: `bucket === "rotten" && state !== "resurfaced"`, sorted by `rank`, then
    `group by path` so Bryan can clear one note at a time (63% of the pool lives in two notes).
  - Both use `not done`, `short mode`, and `hide toolbar`.
- One line stating that recurring, Blocked, Today, and daily-note tasks never appear here, so
  nobody files "missing task" bugs.

**Other vault edits:**

- `gtd_daily.md` morning chore: "clear [[dash#NEW Tasks|NEW]] to 0 (`]s`, Alt+Shift+F), then
  [[rotten|ROTTEN]] until 0 or the budget; PENDING → NEXT; …".
- The `blocked.md` TOMORROW caption, per ADJ-2.
- Grep for any other `[[freshness…]]` links and fix them.
- Optional, Bryan's call: `task_refresh: 14` on `sase.md`, and a one-time `gkeep_inbox.md` triage.

### bob-cli docs and memory

- **`docs/freshness.md`:**
  - §4: add `bucket` and the vectors.
  - §6: the ritual reads NEW on the dash, then ROTTEN.
  - §8: add the new surfaces.
  - Add the user-facing term "rotten" and its relation to `stale` until the machine rename lands.
- **`docs/plan.md` "READY backlog":** READY excludes bucket `new` and `rotten`. `max_ready` now
  bounds the *confirmed* backlog, and the ROTTEN chip is its counterweight.
- **Memory.** These edits are plan steps that go through `/sase_memory_write`:
  - A **new decisions record**, e.g. *"READY Shows Only Confirmed Tasks; NEW And ROTTEN Are
    Read-Time Views"*:
    - Claim: the partition, read-time only, never a tag, with the dash sections TODAY / NEW /
      PENDING / NEXT / READY.
    - Rejected: the `#rotten` tag via hooks, a stored field, a status symbol, inline date math,
      dim-not-hide.
    - Cost: review becomes required for visibility, and headless READY is ungated.
    - Reopens when: a plugin-free surface must show the gate, or the trial fails.
  - Mark `today-is-read-from-the-ledger` as partly superseded, for its section list only.
    Decision records are immutable, so do not edit its claim.
  - Update the glossary `freshness` strand to the "rotten" wording and the new surfaces.

### Sequencing

One epic, in this order:

1. **`ledger-bucket`** (bob-plugins): the [bob-ledger-tools changes](#bob-ledger-tools-changes),
   including the performance prerequisite. It can land while bob-cli-3a finishes; the two touch
   different functions, but coordinate on `main.js`.
2. **`dash-gating`** (vault plus docs): the [vault changes](#vault-changes) and the
   [bob-cli docs and memory](#bob-cli-docs-and-memory) changes. Deploy with
   `bob plugins sync -r "$PWD"`. Live-verify on athena or apollo and on the Mac.
3. **`vocab-rotten`** (bob-cli plus bob-plugins, after bob-cli-3a closes): the ADJ-5 machine
   rename, the schema bump, and the config-key alias.
4. **Optional later:** the dependency-return rule, and cld's walk-order variant if the RESURFACED
   placement is flipped.

### Acceptance

- **Partition, on one pinned `BOB_NOW` snapshot.** Compare by path + line + status symbol:
  - `NEW ∪ RETURNED ∪ ROTTEN ∪ READY′` equals the old READY;
  - the sets are pairwise disjoint;
  - the 11 recurring tasks are in READY′.
- **Counts cross-check.** `bob freshness list -f json` counts match the rendered sections and chips
  in Obsidian.
- **Behavior, without hooks:**
  - Alt+F on a rotten task moves it to READY immediately, with no hooks run.
  - Advancing the date moves a task to ROTTEN with no file write.
  - `bob task-status-hooks --dry-run` reports nothing for this feature.
- **Fail-open.** With ledger-tools disabled, READY equals today's list and the NEW and ROTTEN chips
  show `–`.
- **Performance.** A dash re-render after a single task edit stays imperceptible on the live vault.
  Measure before and after the memo change.

### Trial and keep rule

Run for two weeks, **2026-10-05 → 2026-10-18**. Track NEW, RETURNED, ROTTEN, and READY counts
daily. **Keep it** if:

- the ROTTEN chip is red on no more than 3 mornings;
- READY holds at least about 30 confirmed tasks on most mornings;
- there is no "I lost a task I needed" case.

If READY collapses while ROTTEN grows:

1. First lengthen intervals on the big notes, or set `stale_daily_budget` (renamed
   `rotten_daily_budget` after phase 3).
2. Then consider dim-not-hide: rotten rows at the bottom of READY with the bob-cli-3a `⟳` mark.

Do not fall back to a stored tag.

### Open questions for Bryan

1. Should returned deferrals live in `rotten.md`'s RETURNED group (recommended) or on the dash as
   a NEW subgroup (cld)?
2. Is renaming `freshness.md` to `rotten.md` acceptable? The alternative is keeping
   `freshness.md` as a stub that links to both new surfaces.
3. Is `task_refresh: 14` on `sase.md` and a `gkeep_inbox.md` triage before the trial acceptable?
4. Should `^wip-next-refresh` be declined for now (recommended) or trialed on one note?

## Disagreements and resolutions

Where the reports disagreed, and how the lead resolved each disagreement:

| Topic | Positions | Resolution | Why |
| --- | --- | --- | --- |
| **Where RESURFACED goes** | `rotten.md`, as a separate RETURNED group (cdx, grk, mus, gem). NEW on the dash, as a `↩ RETURNED` subgroup (cld). | **`rotten.md`, RETURNED group first** (ADJ-2) | (a) The contract already puts RESURFACED in the DUE tier with STALE, and bob-cli-3a gives both the same `due` tone. (b) The `]s` walk is NEW → DUE, so the dash and the walk stay in the same order; cld's layout needs its own ADJ-9 walk-order change. (c) Bryan's own filed task says "Make sure scheduled tasks are treated as stale!" (`^scheduled-are-stale`). (d) NEW stays a clean "never confirmed" signal, and the uncapped must-clear set does not grow by 6–17 returns a day. cld's cost is real: `blocked.md` promises TOMORROW tasks "land on the Dashboard tomorrow", so that line must change to "land in [[rotten]] (RETURNED)". If Bryan wants returns on the board, cld's variant is a one-function change (see [Contract](#contract)). |
| **NEW position** | Between TODAY and PENDING (cld, grk, mus, gem). Above TODAY, as the first section (cdx). | **TODAY → NEW → PENDING → NEXT → READY** (ADJ-1) | "Above WIP" read literally is "above PENDING". TODAY is work already pulled and stays first. NEW is the gate before pulling more. |
| **READY predicate** | `isDue?.(task) !== true` (cdx, grk). `bucket?.(task) ?? null === null` (cld). `state === "fresh"` (mus). `isReady` = fresh only (gem). | **"Not review-due", fail-open** | **mus's and gem's predicates would make the 11 recurring Ready tasks vanish.** Their state is `null`, so they would match neither READY, NEW, nor ROTTEN. gem's `readyCountFromTasks` sketch has the same bug. Out-of-scope rows must stay in READY. |
| **API shape** | Existing `state` and `isDue` (cdx, grk, mus). New `bucket(task)` (cld). `isNew`, `isRotten`, `isReady` helpers (gem). | **One additive `api.freshness.bucket(task)`** returning `"new"`, `"rotten"`, or `null` | One function encodes the surface decision. The dash, `rotten.md`, the READY count, and the chip counts all call it, so a chip matches its section by construction. Changing the RESURFACED placement, adding a dependency-return rule, or adding WIP/NEXT freshness later is then a plugin change, not a vault-query rewrite. |
| **stale → rotten rename** | User-facing labels only; keep `stale` in machine contracts (cdx, grk, gem). Rename everywhere now, with a schema bump (cld, mus). | **Labels now; the machine rename as its own small phase after bob-cli-3a lands** (ADJ-5) | Bryan said "let's start using the term". The feature is one day old. The live config key is unset. No external JSON consumer exists (E12). "stale" is overloaded elsewhere. So the end state should be one vocabulary. Separating the phase keeps the dash split from colliding with the in-flight fresh-mark epic. |
| **Fate of `freshness.md`** | Rename it to `rotten.md` (cld, gem). Turn it into a stub (grk). Keep both with distinct roles (mus). Keep it during a transition (cdx). | **Rename `freshness.md` → `rotten.md`** and keep the `Review` / `Freshness review` aliases (ADJ-3) | Once NEW is on the dash, a combined NEW + DUE page duplicates both new surfaces, and two review notes over one queue will drift. Obsidian does not resolve `openLinkText` targets or [[freshness\|…]] links through aliases, so update the plugin fallback and the `gtd_daily.md` chore in the same change. |
| **REVIEW chip** | Replace it with ROTTEN (cdx, gem). Replace it with NEW + ROTTEN (cld, grk). Keep it, reworded (mus). | **NEW + ROTTEN replace REVIEW** (ADJ-4) | Three chips would count overlapping sets. The status bar keeps the combined `new · rotten · ✓ today` line. |
| **ROTTEN chip escalation** | Red whenever nonzero (mus). Orange above 0, red once any task is a full interval overdue (cld). Orange (gem, grk). | **cld's two-step rule** (ADJ-8) | A normal day has about 28 newly rotten tasks, so "red whenever nonzero" would be red every morning and stop meaning anything. A missed *cycle* is the real alarm, and it is what counters risk 4. |
| **Dependency-unblocked tasks** | Add a "returned" rule for dependency returns (cld ADJ-8). Not raised (the others). | **Defer** | Under the recommended layout, a dependency return with an old stamp already lands visibly in `rotten.md`. Review is appropriate there, because context can change while a task is blocked. Only 14 open tasks carry `dependsOn`. If needed, it becomes a later `bucket` and grouping rule. |
| **Performance** | Add a memoized state map (cdx). The same, plus a cached config read (cld). Not raised (grk, mus, gem; gem calls it "sub-millisecond"). | **A prerequisite, not an optimization** | Lead-verified: each `state(task)` call runs `freshnessEnsureMemo()` **twice** (once directly and once inside `apiFreshnessRowFor`). Each run re-reads and YAML-parses `~/.config/bob/config.yml` synchronously on desktop. The call then does `tasks.indexOf(task)` over the whole Tasks list and rebuilds the row, including `task.isBlocked(all)`. The dash runs NEW and READY filters over roughly 450 TODO candidates, plus sort and group calls and the chip counts, on every Tasks re-render. gem's "sub-millisecond" claim does not hold for the current code. |
| **Mobile** | Read-time "runs identically on mobile" (gem). | **True, with one caveat** | On mobile, ledger-tools does not read `~/.config/bob/config.yml` and uses defaults. That is identical today because no `freshness:` block exists, but a configured global interval would diverge. Note interval overrides (`task_refresh`) still apply everywhere. |

## About this report

- **Date:** 2026-10-01
- **Lead:** consolidated from five independent reports (`__cdx`, `__cld`, `__grk`, `__mus`, `__gem`)
  plus the lead's own checks of the code, the vault, and live commands
- **Repos at time of writing:** bob-cli `61785b7`, bob-plugins `dbe3bdd` (bob-ledger-tools 1.9.2),
  vault `70124c88`
- **Question:** How should NEW and rotten tasks leave `dash.md`'s READY section, with NEW in a new
  dash section and rotten tasks in `~/bob/rotten.md` behind a ROTTEN badge? Is preprocessing with
  `bob task-status-hooks` and a `#rotten` tag the right mechanism? Is the plan a good idea at all?

## Sources

- **bob-cli:**
  - `docs/freshness.md` §§1–8 and §11;
  - `docs/plan.md` "READY backlog";
  - `docs/task-status-hooks.md`, `docs/vault-git-sync.md`;
  - `src/native/freshness/`, `src/native/dataview/tasks/js.rs`;
  - bead `bob-cli-3a`.
- **bob-plugins:**
  - `plugins/bob-ledger-tools/main.js`: `api.freshness`, `freshnessEnsureMemo`,
    `freshnessBuildMemo`, `apiFreshnessState`, `apiFreshnessRowFor`, `loadFreshnessConfig`,
    `readyCountFromTasks`, `refreshFreshnessForRollover`, `TODAY_RELOAD_EVENT`;
  - `plugins/bob-ledger-tools/manifest.json`;
  - `plugins/bob-navigation-hotkeys/main.js`: the nav-review section and `refreshTaskFreshness`.
- **Vault (read-only):** `dash.md`, `freshness.md`, `blocked.md`, `bob_gtd.md`, `gtd_daily.md`;
  the history of `dash.md` (`a0d6635c`).
- **Live commands:**
  - `bob freshness list -f json` with `BOB_NOW` set to 2026-10-01…10-15;
  - `bob query -o dash.md -t …`, probing the NEW and READY predicates headless;
  - `~/.config/bob/config.yml`.
- **Memory:** `decisions:today-is-read-from-the-ledger`, `decisions:now-tag-is-user-owned`,
  glossary `freshness`.
- **Plans and research:**
  - `plan:202610/ready_badge.md`;
  - [`research:202609/ready_task_freshness_review/ready_task_freshness_review.md`](../../202609/ready_task_freshness_review/ready_task_freshness_review.md),
    rows V7 and "Review surface";
  - the five swarm reports in this directory: [cdx](freshness_gated_ready_dash__cdx.md),
    [cld](freshness_gated_ready_dash__cld.md), [grk](freshness_gated_ready_dash__grk.md),
    [mus](freshness_gated_ready_dash__mus.md), and [gem](freshness_gated_ready_dash__gem.md).
