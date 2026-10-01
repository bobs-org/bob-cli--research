# Freshness-aware READY: derived views, not a `#rotten` tag

**Researcher:** cdx  
**Date:** 2026-10-01  
**Scope:** independent code, contract, and live-vault investigation; no peer reports or transcripts consulted

## Executive conclusion

The product idea is good: `READY` should be a trusted action list, not a mixture of
reviewed tasks and tasks whose wording, priority, project, schedule, or dependencies
have not been reconfirmed. Splitting NEW from reviewed READY and moving review-due work
to a dedicated page makes that distinction visible.

The proposed `#rotten` preprocessing is not the right implementation. Freshness is
already deliberately computed at read time, and `bob-ledger-tools` already exposes the
exact synchronous, memoized classification needed by Obsidian Tasks queries. A stored
tag would duplicate that state, lag behind midnight/config/frontmatter changes, create
large periodic vault rewrites, and be briefly or permanently wrong after any refresh
gesture. `bob task-status-hooks` should remain responsible for ledger-derived status and
structural reconciliation, not become a second freshness engine.

The best implementation is to partition the existing visible Ready population through
the existing freshness API:

- `NEW` (`state === "new"`) appears in a new first dashboard task section.
- `READY` contains tasks that are not review-due. This means FRESH tasks plus existing
  freshness-exempt Ready tasks such as recurring tasks.
- `rotten.md` contains both RESURFACED and ROTTEN tasks, grouped separately so a task
  that just returned from scheduling is not mislabeled as old.
- The dashboard READY badge must count the same filtered population as its section.
- A ROTTEN badge should count `resurfaced + stale` and link to `rotten.md`.

Use **ROTTEN** in user-facing text, but retain the current machine value `"stale"` and
JSON field `stale` for now. Renaming a public API value is unrelated migration risk; it
can be done later with an API/schema version and compatibility alias if desired.

## What exists now

### The freshness contract already defines the needed source of truth

At bob-cli commit `c857c30`, `docs/freshness.md` defines freshness as a read-time
evaluation, never stored. Its in-scope population is a visible, non-recurring,
non-daily-note Ready task that is not Today. The states are:

| State | Meaning | Review due? |
|---|---|---:|
| NEW | no valid `fresh` date | yes |
| RESURFACED | scheduled date arrived after the last confirmation | yes |
| STALE | confirmation is at least the effective interval old | yes |
| FRESH | confirmed more recently than its interval | no |
| `null` / out of scope | not a freshness-eligible Ready task | no freshness judgment |

The effective interval is already correctly derived from task `[refresh:: N]`, note
`task_refresh`, then `freshness.interval`. Missing, malformed, and future `fresh` values
already have defined behavior and lints. Reimplementing any of this in a hook or in a
dashboard regular expression would create a third classifier.

The JavaScript mirror at bob-plugins commit `58b6200`
(`plugins/bob-ledger-tools/main.js`) exposes:

```text
api.freshness.state(task)
api.freshness.isDue(task)
api.freshness.tier(task)
api.freshness.rank(task)
api.freshness.queue()
api.freshness.counts()
```

It builds rows from the Tasks cache, memoizes the queue and rank map, watches task and
`task_refresh` changes, re-reads configuration, and invalidates at local midnight. The
plugin also triggers Tasks-query reloads when the due-key set changes for reasons that
Tasks itself would not observe. This is exactly the machinery a dynamic dashboard needs.

### The dashboard and review page are already close to this design

The live `dash.md` has task sections in this order:

1. TODAY
2. PENDING
3. NEXT
4. READY

There is no section literally named WIP, so “above WIP” is ambiguous in the request.
The least surprising interpretation is to place NEW immediately before TODAY, making
it the first task section. PENDING is the renamed In Progress lane, while TODAY is the
actual active-work view.

The existing `freshness.md` already renders the review queue with the freshness API and
groups NEW before DUE. The dashboard already has a REVIEW badge, and the status bar
already displays due/new/refreshed counts. A new `rotten.md` is therefore a focused
view of existing derived data, not a reason to create new task metadata.

### Live snapshot and counterfactual aging

Read-only observations on 2026-10-01:

- `bob query --format json --tasks-note dash.md` reported 49 PENDING, 32 NEXT, and
  210 READY tasks; TODAY was empty at the time of the read.
- `bob freshness list --format json` reported 199 in-scope FRESH tasks, 0 NEW,
  0 RESURFACED, 0 STALE, and 391 tasks refreshed that day.
- The 11-task difference between 210 dashboard READY and 199 in-scope FRESH is exactly
  11 recurring Ready tasks. These are intentionally exempt from freshness because a
  recurring completion creates the next occurrence and must not copy a freshness stamp.

Re-evaluating the unchanged vault at future dates with `BOB_NOW` shows why this change
will be behaviorally significant, not merely cosmetic:

| Evaluation date | Fresh | Rotten (current `stale`) | New | Resurfaced |
|---|---:|---:|---:|---:|
| 2026-10-02 | 173 | 26 | 0 | 0 |
| 2026-10-05 | 106 | 93 | 0 | 0 |
| 2026-10-08 | 0 | 199 | 0 | 0 |

This is a counterfactual with no intervening reviews, but it illustrates the intended
pressure: after one interval, READY would contain only the 11 exempt recurring tasks.
That is defensible if the morning review is a real operating habit. If it is not, the
change turns `rotten.md` into a 199-item shadow backlog and makes READY look misleadingly
empty. The UI should make both counts obvious during rollout.

## Critique of the proposal

### What is good

1. **It makes READY truthful.** The current checkbox lane says a task is available;
   freshness says a human still endorses it as written. Combining both predicates makes
   the dashboard a better action surface.
2. **It gives arrivals a deliberate intake point.** Creation intentionally does not
   stamp `fresh`, so NEW is an honest inbox rather than silently accepted work.
3. **It creates healthy pressure without changing status.** A task can remain Ready as
   a lane while disappearing from the dashboard's reviewed-Ready view. This respects
   the accepted “sticky lanes; only Blocked is derived” decision.
4. **It makes review debt visible.** A ROTTEN badge and page prevent removed READY rows
   from simply vanishing.

### What needs adjustment

1. **RESURFACED is missing from the requested partition.** A task may be neither new nor
   age-rotten but still require review because its scheduled date arrived after its last
   confirmation. It should leave READY and appear on `rotten.md` in a separate RETURNED
   group. Calling it rotten without distinction loses useful causal information.
2. **Recurring and daily-note exemptions must be explicit.** A strict “no stamp means
   NEW” dashboard filter would incorrectly hide recurring tasks forever. I recommend
   applying NEW/ROTTEN only to the established freshness scope and keeping out-of-scope
   Ready tasks in READY. The live discrepancy is currently 11 recurring tasks.
3. **The READY badge must change with the section.** Today it counts the whole visible
   TODO lane through `readyCountFromTasks`. Filtering only the Markdown query would make
   the badge disagree with the list and with its `max_ready` cap.
4. **The current REVIEW badge becomes redundant.** NEW on the dashboard, ROTTEN on a
   dedicated page, a ROTTEN badge, and the freshness status bar already cover the state.
   I recommend replacing the dashboard REVIEW chip with ROTTEN rather than accumulating
   overlapping navigation. Keep `freshness.md` as the combined review/status-bar target
   during a transition.
5. **“Rotten” should be a label, not a new persistence concept.** The word is vivid and
   may be useful for the personal workflow, but the underlying fact remains “review
   overdue.” Keep neutral internal state and use ROTTEN in headings, badge copy, and
   explanations.
6. **An unbounded first section can dominate the dashboard after imports.** The existing
   review contract says NEW is never capped, which is correct for intake integrity. Do
   not silently limit it; instead show its count prominently and accept that a large
   import creates a visible triage obligation.

## Implementation options

| Option | Correct at midnight/config changes | Writes task files | Preserves interactive Tasks rows | Sources of truth | Assessment |
|---|---:|---:|---:|---:|---|
| Add/remove `#rotten` in `task-status-hooks` | only after next successful hook | many | yes | Rust evaluator + tag reconciler | Reject |
| Filter Tasks blocks through `api.freshness` | yes | none | yes | existing Rust/JS contract | Recommend |
| Generate `rotten.md` as a materialized task list | only after regeneration | generated-note churn | awkward/duplicated rows | evaluator + generated snapshot | Reject |
| Render custom DataviewJS rows from `queue()` | yes | none | usually loses native Tasks controls | existing API | Useful only if Tasks queries cannot express the view |

### Why `#rotten` is the wrong cache

`#rotten` looks simple because Obsidian Tasks can filter tags natively, but it creates
more lifecycle than it removes:

- A task becomes rotten because the clock crossed a date. Nothing on the task changed.
  The tag is wrong until the next hook succeeds.
- Changing task `[refresh::]`, note `task_refresh`, global configuration, schedule, or
  Today membership can change the result immediately. Every such input becomes an
  invalidation path for the tag.
- Alt+F and the many supported task gestures refresh in one write. They would also have
  to remove `#rotten` in that same write or expose a stale tag until cron catches up.
- The Mac hook runs every 15 minutes and uses guarded, lock-coordinated, recoverable
  writes because concurrent Obsidian and sync edits are real hazards. Adding hundreds
  of time-driven tag changes increases conflict surface and Git noise for no semantic
  gain.
- Tags are durable user-visible taxonomy. A derived cache can leak through copies,
  templates, search, backups, and temporary hook failures.
- It contradicts the freshness contract's explicit “computed at read time, never
  stored” rule and the broader accepted preference to compute Today from its ledger
  rather than stamp derived facts onto tasks.

If the plugin API proved unreliable on a required client, a reserved cache such as
`#bob/rotten` could be reconsidered, but only with a complete ownership contract,
same-write removal in every stamper, dry-run reporting, and recovery behavior. There is
no current evidence that this complexity is needed.

## Proposed design

### 1. Treat the dashboard as a partition of visible Ready

For a task that passes the dashboard's existing Ready predicates (TODO status,
unblocked, visible, not future-scheduled, not Today):

| Freshness result | Surface |
|---|---|
| `new` | `dash.md#NEW Tasks` |
| `resurfaced` | `rotten.md#RETURNED Tasks` |
| `stale` | `rotten.md#ROTTEN Tasks` |
| `fresh` | `dash.md#READY Tasks` |
| `null` | `dash.md#READY Tasks` (explicit exemption) |

This is exhaustive and avoids disappearing tasks. The invariant should be testable:

```text
visible Ready total
  = NEW + RESURFACED + ROTTEN + reviewed READY

reviewed READY
  = FRESH + freshness-exempt visible Ready
```

### 2. Use the existing API in Tasks blocks

The intended queries are conceptually:

```tasks
# NEW Tasks
status.type is TODO
filter by function globalThis.app?.plugins?.plugins?.["bob-ledger-tools"]?.api?.freshness?.state?.(task) === "new"
sort by function globalThis.app?.plugins?.plugins?.["bob-ledger-tools"]?.api?.freshness?.rank?.(task) ?? Number.MAX_SAFE_INTEGER
```

```tasks
# READY Tasks
status.type is TODO
filter by function globalThis.app?.plugins?.plugins?.["bob-ledger-tools"]?.api?.freshness?.isDue?.(task) !== true
```

```tasks
# rotten.md
not done
filter by function ["resurfaced", "stale"].includes(globalThis.app?.plugins?.plugins?.["bob-ledger-tools"]?.api?.freshness?.state?.(task))
sort by function globalThis.app?.plugins?.plugins?.["bob-ledger-tools"]?.api?.freshness?.rank?.(task) ?? Number.MAX_SAFE_INTEGER
group by function globalThis.app?.plugins?.plugins?.["bob-ledger-tools"]?.api?.freshness?.state?.(task) === "resurfaced" ? "1 · RETURNED" : "2 · ROTTEN"
short mode
hide toolbar
```

The READY expression is intentionally failure-open: on an older or unloaded
ledger-tools plugin, it preserves the old Ready list instead of hiding the entire
backlog. NEW and ROTTEN fail empty. The dashboard badge should visibly show unavailable
state when the API is absent so this degradation is not mistaken for a clean review
queue.

`rotten.md` should have `parent: "[[gtd]]"` per vault convention, explain the RETURNED
versus ROTTEN groups, and include the same one-key review outcomes currently documented
in `freshness.md`.

### 3. Make badge counts use the same partition

Change the shared READY budget in bob-ledger-tools to count visible Ready tasks only
when `api.freshness.isDue(task)` is false. Out-of-scope/null rows remain included. This
keeps the dashboard section, daily `bob-plan` badge, `max_ready`, tooltip, and click
target coherent.

Add a ROTTEN badge model whose count is:

```text
freshness.counts().resurfaced + freshness.counts().stale
```

Its tooltip should retain the split, for example `ROTTEN 31 · 4 returned, 27 overdue`,
and its target should be `rotten`. Place it adjacent to READY because they are
complementary views of the Ready lane. Replace the current REVIEW dashboard chip;
continue using the status-bar freshness control as the entry to the combined
`freshness.md` queue.

Do not use `counts.fresh` directly as the READY badge: it excludes the 11 currently
exempt recurring tasks and therefore would not match the proposed READY section.

### 4. Optimize the already-public classifier rather than add metadata

`freshnessBuildMemo` currently stores all evaluated rows and an O(1) rank map, but
`apiFreshnessState(task)` rebuilds/evaluates a row on each call. A Tasks block can call
it once per candidate and group/sort can call it again. Add an evaluated-state map to
the memo keyed by the same path+block-id/path+line identity used for rank. Then
`state`, `isDue`, and `tier` are O(1) lookups for cached Tasks objects. This is an
internal optimization; no API change is required.

### 5. Acknowledge the headless `bob query` limitation

The native Tasks JavaScript sandbox does not expose a live Obsidian
`globalThis.app.plugins` registry. This is already observable: the live dashboard uses
`isToday`, while a headless `bob query --tasks-note dash.md` cannot reproduce that API
call. Freshness-filtered blocks would have the same limitation.

Do not solve this with a tag merely to make headless queries easy. Instead:

1. Keep Rust/JavaScript freshness conformance vectors as the semantic proof.
2. Test the Rust partition from `bob freshness list -f json` and the JavaScript
   partition through bob-ledger-tools pure-helper tests.
3. Add a gated live-Obsidian acceptance check for the actual Tasks blocks.
4. Document the native `bob query --tasks-note` fallback (NEW/ROTTEN empty; READY old
   unfiltered behavior when the plugin namespace is absent).
5. If exact headless dashboard rendering becomes important, inject a minimal synthetic
   freshness API into the sandbox from the existing Rust evaluator. That is a separate
   parity feature, not a prerequisite for the vault UX.

## Requirement adjustments I recommend

These are deliberate changes or clarifications to the request:

1. Define **ROTTEN** as the user-facing replacement for STALE, but keep `"stale"` in
   machine contracts until a versioned migration.
2. Put RESURFACED tasks on `rotten.md` under **RETURNED**, and include them in the
   ROTTEN badge total; otherwise they fall through the proposed UI.
3. Apply NEW/ROTTEN only to the established freshness scope. Keep recurring and other
   explicitly exempt visible Ready tasks in READY.
4. Interpret “above WIP” as immediately above TODAY, because the live dashboard no
   longer has a WIP heading. If PENDING was intended, move NEW there instead; this is
   presentation-only.
5. Replace the dashboard REVIEW badge with ROTTEN to avoid two dashboard links to
   overlapping review debt. Keep `freshness.md` and the status-bar entry during the
   transition.
6. Do not cap or truncate NEW. Large NEW is intake debt that should remain visible.

## Delivery and acceptance plan

1. **Contract/docs:** Update `docs/freshness.md` with user-facing ROTTEN terminology,
   the Ready partition, resurfaced placement, and exemption rule. Update the READY
   definition in `docs/plan.md` because `max_ready` semantics change.
2. **bob-ledger-tools:** Add the memoized state map, filter the shared READY budget by
   review-due state, add/test the ROTTEN badge view model, and retain API v3/freshness
   v1 because public shapes do not need to change.
3. **Vault:** Add `rotten.md`; add NEW above TODAY; filter READY; replace REVIEW with
   ROTTEN; preserve `freshness.md` as the combined review page.
4. **Tests:** Cover the exhaustive partition, recurring exemption, malformed/future
   stamps as NEW, resurfaced precedence, per-task/note/config intervals, midnight
   rollover, plugin-unavailable degradation, badge/list equality, and the strict
   `max_ready` over-cap boundary.
5. **Deploy:** Run the bob-plugins test suite, `bob plugins sync`, and manual Obsidian
   acceptance. Verify on consecutive effective dates with `BOB_NOW` fixtures rather
   than waiting for midnight.
6. **Observe for one interval:** Track daily NEW/RETURNED/ROTTEN/READY counts. The
   unchanged-vault projection reaches 199 rotten in seven days, so this observation is
   essential evidence that the review habit and 7-day default are sustainable. If not,
   tune intervals or enable `stale_daily_budget`; do not restore false-ready tasks.

Acceptance should require that every visible Ready task appears in exactly one of NEW,
RETURNED, ROTTEN, or READY; badge counts equal their target views; stamping a task moves
it to READY immediately without running hooks; and advancing the effective date moves
it to ROTTEN without modifying any task file.

## Recommended solution

Implement the proposal as **derived, freshness-aware views backed by
`bob-ledger-tools`**, not as `#rotten` preprocessing. Add NEW above TODAY, filter READY
with `freshness.isDue`, create `rotten.md` with separate RETURNED and ROTTEN groups,
update the shared READY count/cap to match the filtered section, and add a ROTTEN badge
counting returned plus age-rotten tasks. Preserve recurring/out-of-scope Ready tasks,
keep `"stale"` as the compatibility-facing machine value, replace the redundant REVIEW
dashboard chip, and retain `freshness.md` as the combined transition/review surface.

