# Splitting READY: NEW section in dash, rotten tasks in rotten.md

Research report — researcher `mus` (independent swarm contribution).
Date: 2026-10-01. Context: the `[fresh::<date>]` freshness system has
landed since the September review (Rust evaluator, `bob freshness
list | seed`, `api.freshness` in bob-ledger-tools, stamping keymaps,
REVIEW chip, `freshness.md` review note). This report asks how to make
"which READY tasks are really ready" visible: a NEW section in
`~/bob/dash.md`, a new `~/bob/rotten.md`, a ROTTEN badge, the
stale→rotten rename, and whether `bob task-status-hooks` should
preprocess anything (e.g. a `#rotten` tag).

No peer swarm report (`__cdx`, `__cld`, `__grk`, `__gem`) was located,
opened, or consulted.

## 1. TL;DR verdict

The plan is a good idea and worth building. Its core insight is right:
today the READY section mixes three things with different morning
meanings — tasks nobody has looked at (NEW), tasks whose review lease
expired or whose deferral came back (due), and tasks that were recently
confirmed (FRESH) — and only the third group is "really ready" to pick
up. Splitting them makes the dash honest.

I would build it with these adjustments:

1. **No preprocessing at all — reject the `#rotten` tag.** Freshness
   state is already computed at read time in both engines. Three Tasks
   `filter by function` predicates using the existing
   `api.freshness.state(task)` mirror give you NEW / ROTTEN / READY
   with zero writer changes, zero write churn, and zero midnight-rot.
   The hooks command stays exactly as it is. (§5)
2. **Partition, don't filter.** Define
   `READY′ = FRESH`, `NEW = NEW-state`, `ROTTEN = STALE ∪ RESURFACED`.
   The three sets are mutually exclusive and jointly equal today's
   READY backlog, so the accepted `today-is-read-from-the-ledger`
   exclusivity decision is preserved, not amended. RESURFACED stays a
   named subgroup *inside* rotten.md ("came back from a deferral"),
   because that tells Bryan why it is due. (§4, §6)
3. **Rename `stale`→`rotten` all the way down, in one release, with a
   JSON schema bump** — display strings, docs, Rust `FreshState`,
   the JS mirror, `bob freshness` output, and (with a one-release
   fallback) the `stale_daily_budget` config key. Bryan owns every
   consumer of these contracts, so a clean rename is cheaper than a
   permanent dual vocabulary. (§7)
4. **Place the NEW section directly after TODAY Tasks (above PENDING).**
   There is no "WIP tasks" section in dash.md today — the closest
   match is PENDING (`[/]`, i.e. work in progress). NEW-first ordering
   matches the morning ritual (clear NEW uncapped, then DUE, then
   PENDING → NEXT planning). Add a NEW chip next to the ROTTEN chip
   for symmetry. (§6)
5. **Do not extend scope to WIP/NEXT 1-day intervals now**, despite the
   live `^wip-next-refresh` task in `bob_gtd.md`. 32 NEXT + 49 PENDING
   tasks at a 1-day interval would put ~80 tasks in the daily due set
   on day one. Lane caps plus the weekly prune remain the pressure
   valve for committed work; revisit under the same condition the
   September review set (the prune keeps getting skipped). (§8)

Recommended solution is in §9.

## 2. What I verified (and the numbers behind this report)

All commands run 2026-10-01 against the live vault (`BOB_DIR=~/bob`,
i.e. `/home/bryan/bob`):

- `bob freshness list` → `REVIEW 0 due · 0 new · 0 resurfaced ·
  0 stale · ✓ 391 today` (JSON: `fresh: 199`, `refreshed_today: 391`,
  `schema_version: 1`). The seed landed and the review queue is at
  zero: **every in-scope Ready task is FRESH today**. The split changes
  almost nothing on day one and pays off as tasks age — the ideal time
  to land it.
- `bob plan` → `TODAY 8 · PENDING 49/10 · NEXT 32/15`. Lanes are far
  over cap (a triage problem, not this report's problem, but it bears
  directly on adjustment 5 above).
- `bob query --format json --tasks-note dash.md` parses all four dash
  Tasks blocks headless. A probe with an inline
  `filter by function task.lineNumber >= 0` returned results, so the
  **native engine evaluates `filter by function` headless** — new
  NEW/ROTTEN/READY′ predicates can be verified in CI and against the
  live vault without opening Obsidian.
- `dash.md` today: chips PENDING / NEXT / READY / BLOCKED(external) /
  REVIEW(external → `freshness.md`) / TODAY, then sections TODAY,
  PENDING, NEXT, READY Tasks. The READY block is
  `status.type is TODO` + `isToday !== true` plus the shared
  `TQ_extra_instructions` frontmatter defaults (not blocked, no
  `#hide`, scheduled ≤ today, self-exclusion). There is **no WIP
  section**; "WIP" appears in the vault only as the `next/wip`
  group badge language and a `bob_gtd.md` requirements line.
- `freshness.md` (the REVIEW target) already demonstrates the pattern
  this proposal copies: `isDue`, `rank`, `tier` from
  `api.freshness` inside Tasks `filter/sort/group by function`.
- `bob-cli` source: `src/native/freshness/state.rs` names the JS
  mirror as `api.freshness.state, queue, counts` with states
  `new / resurfaced / stale / fresh`, tiers `new / due`, and the
  read-time-only contract. Nothing is stored; there is no field, tag,
  or sidecar to preprocess.
- The live `bob_gtd.md` project (itself in TODAY) carries four
  sibling tasks that bound this report's scope: `^hide-rotten-tasks`
  (this proposal), `^scheduled-are-stale`, `^wip-next-refresh`,
  `^prj-task-count-warn`. §8 dispositions each.
- `rotten.md` does not exist yet. `blocked.md` is the structural
  template to copy (frontmatter `TQ_extra_instructions`, one-line
  purpose statement, pointer back to the dashboard, one Tasks block
  per section).

## 3. Critique: is this a good idea?

Yes — with the adjustments in §4. Three reasons it is right:

- **It fixes a real dishonesty in READY.** A NEW task ("never
  confirmed, may be misworded, misrouted, or already done") and a
  rotten task ("confirmed once, lease expired") are not actionable in
  the same way a FRESH task is. Showing all three under one heading
  trains Bryan to distrust the heading. The split makes READY mean
  "reviewed recently, safe to commit to" — which is what "really
  ready" should mean.
- **It costs nothing at query time.** The evaluator already runs for
  the REVIEW chip, the status bar, and `freshness.md`. Three more
  `filter by function` calls over the same cached state are noise.
  No migration, no backfill, no seed: day-one behavior is identical
  (0 NEW, 0 rotten today) and the sections populate naturally.
- **It matches the existing ritual order.** Morning review already
  goes NEW → DUE → PENDING → NEXT. The dash will finally read in the
  order Bryan works.

Three risks to name honestly:

- **The rename has a blast radius.** `stale` appears in Rust enums,
  JS API names, `bob freshness` human+JSON output, the status bar,
  `docs/freshness.md` vectors, and the `stale_daily_budget` config
  key. A half-finished rename (docs say rotten, CLI says stale) is
  worse than no rename. §7 makes it atomic.
- **READY′ will still look big.** 199 FRESH tasks today against the
  100 soft cap: the split does not shrink the backlog, it labels it.
  Backlog pressure still needs intervals, deferral, and cancellation
  (§5.7 of the September final). Do not sell this as a load fix; it
  is a clarity fix.
- **Two homes for "due" work.** `freshness.md` (REVIEW target, grouped
  NEW → DUE queue) and the new `rotten.md` (NEW lives in dash,
  rotten subset here) will overlap by construction. Keep `freshness.md`
  as the *working* review queue (it has the rank order and the ritual
  text) and `rotten.md` as the *backlog* view (grouped by note, for
  browsing and pruning). Say so in one line at the top of each note,
  or one of them will rot.

## 4. Adjustments to the requirements (marked ADJ)

| # | Requirement as stated | Change |
|---|---|---|
| R1 | New and rotten tasks leave the READY section. | **ADJ — partition precisely:** READY′ shows only FRESH-state tasks. NEW-state tasks go to the NEW section. STALE **and** RESURFACED go to rotten.md. The three sets are disjoint and their union is exactly today's READY backlog, so TODAY / PENDING / NEXT / READY′ / NEW exclusivity holds and no task silently disappears from the dash system. Verify by set comparison (§9.5). |
| R2 | NEW tasks section above the WIP tasks section. | **ADJ — placement:** no WIP section exists in dash.md. Put `### NEW Tasks` directly after TODAY Tasks (i.e. above PENDING, the `[/]` work-in-progress lane). Rationale: NEW is the uncapped must-clear morning queue and the ritual reads TODAY → NEW → PENDING → NEXT. Alternative (NEW directly above READY, keeping backlog together) is defensible; pick one and document it. |
| R3 | Rotten tasks in a new `~/bob/rotten.md`, linked from dash.md with a ROTTEN badge. | Keep, with two additions: mirror `blocked.md`'s structure (frontmatter `TQ_extra_instructions`, purpose line, "everything actionable lives on the dashboard" pointer), and give rotten.md **two** sections — RESURFACED (deferrals that came back, highest urgency) and ROTTEN (expired leases, oldest first) — instead of one undifferentiated list. |
| R4 | Preprocess rotten tasks somehow; first thought is a `#rotten` tag via `bob task-status-hooks`. | **ADJ — do not preprocess anything; reject the tag.** §5 gives six reasons. No hooks change, no new writes, no migration. |
| R5 | Rename stale → rotten. | **ADJ — rename everywhere at once** (code, CLI, docs, notes), including RESURFACED's home inside rotten.md but keeping `resurfaced` as the subgroup name. Bump `bob freshness` JSON `schema_version` to 2 and rename `stale_daily_budget` → `rotten_daily_budget` with a one-release fallback to the old key. |
| R6 | (implied) REVIEW chip / freshness.md stay as they are. | **ADJ — update both to the new vocabulary** (chip text, `freshness.md` header counts, status-bar strings) so the vault never says "stale" after the rename. Keep `freshness.md` as the working queue; rotten.md is the browsing view. |

## 5. Why not the `#rotten` tag (the preprocessing question, answered)

The request asks me to "think hard about the best way" — I did, and
the best way is *no* preprocessing. Six independent reasons:

1. **It would violate two settled read-time-derivation rules.**
   `today-is-read-from-the-ledger` ("Today is … never a tag, task-line
   field, or file-path filter") and the freshness contract itself
   ("computed at read time, never stored", `docs/freshness.md` §4).
   Freshness state changes at midnight, on interval edits, on
   frontmatter edits, and on every Alt+F stamp — none of which runs
   the hooks. A stored tag is guaranteed to lie between hooks runs;
   a computed predicate cannot.
2. **The hooks run at the wrong times.** Hooks run after capture,
   session close, and sync writes. Rot sets in continuously (midnight
   rollover re-evaluates the whole queue with no vault write at all).
   Event-driven tagging of a time-driven property is a category
   error; the REVIEW chip and status bar already re-evaluate at
   midnight without touching a line.
3. **Tag removal is the killer.** Adding `#rotten` is easy; removing
   it when a task becomes FRESH is not. Every writer that stamps
   (nav Alt+F/Alt+Shift+F/Alt+N/Ctrl+Shift+P/Ctrl+Shift+M, cycler,
   block-id-prompt, capture edit paths) would also have to strip the
   tag — a coordinated cross-repo change (bob-cli + three plugins) to
   replicate what `state()` already returns. Miss one writer and
   FRESH tasks wear a rotten badge indefinitely.
4. **It expands the hooks' write contract into the danger zone.**
   Today the hooks swap checkbox bytes and move whole lines/blocks;
   per the landed contract, automation *never* writes inline fields.
   Tag insertion/removal needs full line-rewrite machinery, and any
   placement bug replays the trailing-field trap the September review
   proved in both engines (an unknown field at line end hides
   `created`, `scheduled`, `dependsOn` — `state.rs` and Tasks 8.4.0
   both stop parsing left of it). Tags at line end are suffix-safe
   only while nobody misplaces them; the `fresh_misplaced` lint exists
   because humans do.
5. **A tag pollutes user-visible query space.** `#rotten` would show
   in tag panes, tag searches, Dataview `tags` arrays, and every
   existing `tags do not include …` exclusion list that doesn't know
   about it. A `filter by function` predicate is invisible until
   rendered, exactly like `isToday` today.
6. **There is nothing to gain.** Both engines already evaluate the
   predicate: Obsidian via `api.freshness.state(task)` (named in
   `state.rs` as the JS mirror, alongside the `isDue`/`rank`/`tier`
   already used in `freshness.md`), headless via the Rust evaluator
   (`bob freshness list --format json`) and native `filter by
   function` (verified working in §2). Preprocessing buys zero new
   capability.

Rejected alongside: a nightly-generated rotten.md (goes stale between
runs, conflicts with live Tasks blocks, and reinvents the REVIEW chip
pipeline); a Dataview `TABLE` listing instead of Tasks blocks (loses
checkbox interaction, the dash's native idiom); deriving NEW/rotten
from `created` age or mtime (relitigated and rejected in September:
Keep `created` predates the pull; mtime counts automation as
attention).

## 6. Recommended design

### 6.1 The partition (one predicate, three uses)

Over the current READY backlog scope (TODO-type, lane-visible,
non-recurring, non-daily-note, non-Today — unchanged):

```text
state(t) = NEW        → dash ### NEW Tasks
         | RESURFACED → rotten.md ## RESURFACED Tasks
         | STALE      → rotten.md ## ROTTEN Tasks   (renamed "rotten")
         | FRESH      → dash ### READY Tasks (renamed meaning, same heading)
```

`state()` is the existing per-task evaluator in both engines; only
the `"stale"` label changes to `"rotten"` (§7). Queue order inside
each home reuses the existing rank: NEW by (path, line); rotten by
(due_on, path, line).

### 6.2 dash.md changes

- New `### NEW Tasks` block after TODAY Tasks:
  `status.type is TODO` + `isToday !== true` +
  `filter by function …api?.freshness?.state?.(task) === "new"`,
  sharing the frontmatter `TQ_extra_instructions`.
- READY block gains one line:
  `filter by function …api?.freshness?.state?.(task) === "fresh"`.
- Chips: add NEW (count `counts.new`, anchor `#NEW Tasks`) and ROTTEN
  (count `due − new`, i.e. resurfaced + rotten, external link to
  `rotten.md`, following the BLOCKED→`blocked.md` pattern). ROTTEN
  turns over (red) whenever it is nonzero — unlike REVIEW, which is
  over only while NEW > 0 — because rotten backlog is never "fine".
  The shared ledger-tools badge (`renderReadyBadge`/`readyBudget`)
  and the inline fallback count FRESH-only from now on.
- `docs/plan.md` §"READY backlog" is updated: READY is the FRESH
  subset; the cap (`max_ready`) now bounds confirmed backlog. Note
  the consequence: 199 FRESH today already exceeds 100, so the chip
  will read over-cap on landing day — correct signal, not a bug.

### 6.3 rotten.md (new, mirrors blocked.md)

Frontmatter: `parent: [[dash]]`, purpose alias, and
`TQ_extra_instructions` (exclude `_templates`, self-path, `#hide`,
scheduled ≤ today — same as dash; Blocked/future-scheduled tasks are
out of scope by construction since they never enter the partition).
Body: one purpose line ("Tasks whose review lease expired or whose
deferral came back. Confirm, defer, or drop them; the working queue
with ritual text is [[freshness]]."), then:

- `## RESURFACED Tasks` — `_… came back from a deferral_`,
  `state === "resurfaced"`, sort by `rank`.
- `## ROTTEN Tasks` — `_confirmed once, lease expired_`,
  `state === "rotten"`, sort by `rank`, `group by path`.

No other sections. Recurring, Blocked, Today, and daily-note tasks
cannot appear (evaluator scope excludes them) — say so in one line so
nobody files "missing task" bugs.

### 6.4 What does not change

- `bob task-status-hooks`: no change. (The September "test that
  hooks preserve the field" still covers it.)
- Writers/keymaps: no change. Stamping already moves tasks between
  the new homes automatically at next render.
- `bob capture`, Mac Capture, ledger-tools Today/lane code: no change.
- Morning ritual text: unchanged in substance; it already reads in
  NEW → DUE → PENDING → NEXT order, and the dash will now match it.

## 7. The rename, made atomic

`stale` → `rotten` in one release, owned end to end:

- Rust: `FreshState::Stale` → `Rotten`, `as_str "rotten"`, tier
  `"due"` unchanged, queue/count internals renamed, vectors in
  `docs/freshness.md` (§4, §10) reworded.
- JS mirror: same renames in `api.freshness` (`state`, `tier`,
  `counts`, status bar, REVIEW chip text).
- `bob freshness list`: human output `ROTTEN`/`rotten Nd`; JSON
  `counts.stale` → `counts.rotten`, queue `state: "rotten"`,
  `schema_version: 1 → 2`.
- Config: `freshness.stale_daily_budget` → `rotten_daily_budget`;
  accept the old key for one release with a lint, then remove.
- Docs/notes/memory: `docs/freshness.md`, `docs/plan.md`,
  `freshness.md`, `dash.md` comments, the Task Freshness glossary
  strand, and the September final's terminology note.
- Keep `resurfaced` and `refresh`/`task_refresh` names: they are not
  the word being retired, and renaming them adds churn with no
  clarity win.

Why all-at-once instead of display-only: Bryan is the sole consumer
of every contract involved (CLI JSON, dataviewjs call sites, config
keys). A permanent display/machine vocabulary split would force
every future grep, vector, and bug report to translate. The schema
bump + config fallback make the one-time cost explicit and finite.

## 8. Disposition of the three sibling tasks in bob_gtd.md

These share the vault with this proposal and constrain it; each gets
a recommendation so the lead can sequence them:

- `^scheduled-are-stale` ("scheduled tasks treated as stale"):
  **already true — no work.** A deferral that returns evaluates
  RESURFACED by the tickler rule (`fresh < scheduled ≤ today`) and
  will land in rotten.md under its own heading. A future-scheduled
  task is Blocked and correctly invisible everywhere until it
  returns. Close as satisfied-by-construction after verifying one
  S11-style vector against the renamed evaluator.
- `^wip-next-refresh` ("WIP and NEXT tasks refresh every 1 day"):
  **decline for now.** Freshness v1 is Ready-scoped by accepted
  decision; Next/Pending already have a daily ritual (PENDING → NEXT
  linking), lane caps, and the weekly prune. At today's counts a
  1-day interval puts ~80 committed tasks in the due set every
  morning and destroys the NEW-must-reach-zero invariant the whole
  ritual depends on. The per-note `task_refresh` override already
  lets Bryan opt individual hot notes into shorter leases without a
  scope change. Revisit if the weekly prune keeps getting skipped —
  the exact condition the September review set.
- `^prj-task-count-warn` (">5 ready tasks per project warnings"):
  **small additive hooks/plan lint, independent of this proposal.**
  Per-note open-task counts already exist in project frontmatter
  (`task_count`/`open_task_count`); warn when FRESH+NEW+rotten in one
  note exceeds 5. Sequence after the split so the warning can name
  which subset is overgrown.

## 9. Recommended solution (phased)

1. **Contracts (no code).** Update `docs/freshness.md` vectors for
   the rename (S3/S4/S11/S14 wording, `state: "rotten"`), update
   `docs/plan.md` READY-backlog definition to FRESH-only plus the
   NEW/ROTTEN homes, and record a decision note (partition preserves
   dash exclusivity; no stored tags for derived review state —
   cites §5) plus the glossary strand edit, via the memory-write
   procedure.
2. **Rename.** Rust evaluator + `bob freshness` (human, JSON
   schema 2, config fallback lint) with the existing Rust/JS
   conformance tests updated; ledger-tools `api.freshness` strings,
   status bar, REVIEW chip.
3. **Vault surfaces.** NEW block + READY predicate + NEW/ROTTEN chips
   in `dash.md` (shared badge path first, inline fallback second);
   new `rotten.md` per §6.3; `freshness.md` header reworded with the
   one-line working-queue-vs-browsing-view distinction.
4. **Counts follow.** `readyBudget`/`renderReadyBadge` go FRESH-only;
   verify the REVIEW chip, status bar, and `bob freshness list`
   agree on one vault snapshot.
5. **Verify by partition, not by eyeball.**
   - `bob query --tasks-note dash.md` and `--tasks-note rotten.md`
     parse clean headless;
   - independent set check on one pinned `BOB_NOW` snapshot:
     `READY′ ∪ NEW ∪ ROTTEN == old READY` exactly (same technique as
     the `tasks_real_vault_parity` acceptance: path + zero-based
     line + status symbol);
   - `bob freshness list --format json` (`due`, `new`, `resurfaced`,
     `rotten`) cross-footed against the three rendered sections;
   - manual Obsidian pass (chips navigate, sections render, no task
     in two homes) — desktop Obsidian is unavailable in this
     environment, so this step stays manual acceptance.
5. **Trial two weeks.** Success: NEW reaches 0 before planning daily;
   no task lives in two homes or zero homes; no hooks/keymap write
   touches the new predicates; the rename leaves no "stale" string in
   user-facing surfaces (`grep -ri stale` clean outside history and
   the one-release config fallback).

## 10. Open questions for Bryan

1. NEW placement: directly after TODAY (recommended, matches the
   ritual) or directly above READY (keeps backlog together)?
2. Should the ROTTEN chip be over/red whenever nonzero (recommended)
   or only past a threshold (e.g. the old budget number)?
3. Confirm the old `stale_daily_budget` key can die after one release,
   or must it live on as a permanent alias?
4. `^wip-next-refresh`: confirmed declined, or do you want one hot
   note opted into `task_refresh: 1` as an experiment instead?

## Sources consulted (independent)

- Live vault `/home/bryan/bob`: `dash.md` (chips + all four Tasks
  blocks), `freshness.md`, `blocked.md` (rotten.md template),
  `bob_gtd.md` (four sibling requirement tasks); `rotten.md`
  confirmed absent.
- Live commands: `bob freshness list` (human + `--format json`),
  `bob plan`, `bob query --format json --tasks-note dash.md`,
  `bob query` with inline `filter by function` (native evaluation
  confirmed).
- bob-cli tree: `docs/freshness.md` (contract), `docs/plan.md`
  (READY backlog, lanes, Today), `docs/dataview.md` (native Tasks +
  `by function` support), `docs/task-status-hooks.md` (write
  contract), `src/native/freshness/state.rs` (states, tiers,
  read-time rule, JS mirror names).
- Prior research (not this swarm): `sase/repos/research/202609/`
  `ready_task_freshness_review__final.md` (lead-consolidated) and my
  own `ready_task_freshness_review__mus.md`. No `__cdx`/`__cld`/
  `__grk`/`__gem` file from any swarm was located, opened, or read.
