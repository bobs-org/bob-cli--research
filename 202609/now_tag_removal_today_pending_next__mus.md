# Removing `#now` for Today/Pending/Next: file-path filter vs `#today` tag

- **Research date:** 2026-09-30 (researcher mus, independent swarm report)
- **Question:** Should the one-day-old `#now` tag be removed, with `bob task-status-hooks`
  relieved of WIP/Next sync, the dash's Now/WIP/Next sections replaced by mutually
  exclusive Today/Pending/Next sections, Next absorbing `#now`'s weekly-bet role, and
  Pending/WIP made sticky (never wiped by the hooks)? The two candidate mechanisms for
  the "tasks linked in today's daily file" query are (a) a file-path filter or
  (b) a hooks-managed `#today` tag.
- **Bottom line:** The plan as written should not be adopted. Its single strongest
  premise is wrong: **a Tasks file-path filter cannot list tasks linked from today's
  daily note** — it lists tasks physically residing in it, which I verified live
  (1 result vs ~9 open ledger links). The `#today` tag can express the query but
  converts a one-byte checkbox reconciler into a line-text tag writer with daily
  write amplification, editor/sync races, and a second manual lifecycle — the exact
  failure modes the `#now` research rejected for hooks-managed horizons. And the
  surrounding plan reintroduces the status-lock trap `#now` was built to escape:
  Next decays daily so it cannot hold weekly bets, and sticky Pending re-inflates
  the ~50-task `[/]` pile. Recommendation: **keep `#now` through its agreed two-week
  trial (2026-09-30 → 2026-10-13), and fill the "what is linked today" need read-only**
  with a ledger-backed Today view (DataviewJS via the existing Ledger Tools API
  pattern, or `bob query` JSON), not with tag writes or path filters.

## 1. What I verified

### 1.1 A path filter finds residence, not linkage

Live runs against `~/bob` with the native engine (`--origin dash.md`, so the dash's
own `TQ_extra_instructions` defaults apply):

| Query (`--tasks`, `--origin dash.md`) | Count (2026-09-30) |
|---|---|
| `status.type is IN_PROGRESS` (WIP) | 53 |
| `status.name includes Next` (NEXT) | 27 |
| `status.type is TODO` (READY) | 186 |
| `tags include #now` (NOW) | 0 |
| `tags include #today` | 0 |
| `path includes 20260930` | **1** |

Today's ledger (`~/bob/2026/20260930.md`) has ~9 open task-link lines across its
BOB/CLEANUP/BETS/GTD entries (plus 6 closed entries with 🍅/struck links). The path
filter returns exactly 1 task: the `- [ ] #task [[gtd_daily]]` line physically
located in the daily note. The ~80-queued-link pattern from the prior research holds:
linked tasks live in `sase.md`, `bob.md`, etc. — their `task.file.path` is the area
note, never the daily. **No `path`/`folder` predicate in Tasks can see a
`[[note#^block]]` reference edge.** The native parser (`src/native/dataview/tasks/parse.rs`)
supports only per-task fields (path, folder, tags, status, dates, priority, …) plus
`filter by function` over the task object — there is no backlink/referrer field, and
the task object carries no "referenced from" data.

Consequence: option (a) is not a smaller change. It is not implementable as a Tasks
query at all. The only path-based route is out-of-band: DataviewJS that reads today's
daily file, extracts `[[…#^…]]` tokens, and joins them against `plugin.getTasks()` by
block ID — custom JS with a per-day path computation (`moment().format("YYYY/YYYYMMDD")`),
no `bob query` parity, and a second implementation to keep in sync (the `#now`
decision already pays this cost once for Rust + JS and warns about it).

### 1.2 The hooks are a single-byte checkbox writer today

`src/native/task_status_hooks/compose.rs` applies `PlannedChange`s that are
`{ file_index, status_byte_offset, replacement }` — one checkbox character (`' '`,
`'*'`, `'/'`, `'?'`). Managing `#today` would be a new mutation class: inserting or
stripping a tag in task-line text while preserving trailing Dataview fields, block
IDs (`^id`), aliases, and scheduling metadata. The vault's own precedent says this is
the dangerous edit: the `#now` decision records a scratch-vault test where a
far-right custom field silently erased `priority` and `created` under right-to-left
Tasks parsing, and `bob-plugins`' `upsertBulletProperty` carries the same warning.
Tag insertion point (before vs after trailing fields) would need a rule in every
writer (hooks, keymaps, capture), not just one.

Write amplification is also qualitatively different. Checkbox reconciliation converges:
after one run the vault is stable and later runs are no-ops. A `#today` mirror
churns every task line touched by every added/removed link, every day, across the
whole vault — including tasks in ordinary notes the `[/]`-rollback currently leaves
alone. The hooks run unattended every 15 minutes, so these text edits land behind
open editors and multi-machine sync far more often than today's idempotent byte
flips. The prior synthesis explicitly rejected cron/hooks rewriting the plan for
exactly this reason ("read-only JSON diagnostics; live views in Obsidian").

### 1.3 Statuses decay by design; tags persist by design

Per `docs/task-status-hooks.md` and the derived-status decision (accepted 2026-07-16):

- Next `[*]` = linked from today's **open** Pomodoros (or via a transcluded
  dependency path). An unreachable `[*]` is cleared to `[ ]` vault-wide on the next
  run — including after its Blocked reason lifts ("does not recover to its status
  from before blocking because no hidden previous-status field is stored").
- `[/]` in area/project notes resets to `[ ]` once neither today's ledger nor the
  previous daily links it (one-day grace via read-only recent activity).
- Blocked `[?]` overrides both while an open `dependsOn` or future `scheduled` exists.

`#now` (accepted 2026-09-29) is the complement: user-owned, week-long, never a Next
source, never changed by hooks. `[/]` is a footprint, `#now` a promise.

### 1.4 The current dash sections are already status-partitioned

`~/bob/dash.md` sections: NOW (`tags include #now`), WIP (`status.type is
IN_PROGRESS`), NEXT (`status.name includes Next`), READY (`status.type is TODO`).
WIP/NEXT/READY are mutually exclusive by construction — Next is `ON_HOLD` type
(confirmed in the vault's Tasks settings: `*` Next and `?` Blocked are both
`ON_HOLD`), so `TODO` excludes it — and the note frontmatter excludes blocked,
`#hide`, templates, future-scheduled, and the dash itself. NOW intentionally overlaps
the other three (a task can be `#now` + `[/]`). Any Today/Pending/Next replacement
must reproduce this exclusion scaffolding plus its own mutual-exclusion logic.

### 1.5 `#now` was decided yesterday; its trial has not run

The `#now` decision was accepted 2026-09-29 with a two-week trial 2026-09-30 →
2026-10-13 and explicit reopen conditions (NOW ignored → delete the tag and keep
only the capped ledger; promotion from Ready too slow → consider `#next`; parser-safe
task properties appear). Today's live NOW count is 0 — the tag has no content yet.
Removing it today aborts the experiment before any evidence exists, and the revert
surface is wide: capture grammar + completion + editor spans (`markers.rs`,
`line.rs`, `item.rs`, `completion.rs`, `editor_parse.rs`), `plan_budget` NOW
counting/caps, the `NOW_QUERY` constant and whole-token predicate mirrored in Rust
and JS, the dash NOW chip + `### NOW Tasks`, Ledger Tools `nowBudget`/`planBudget`
APIs, the plugins' Alt+N toggle and Ctrl+Shift+P `#now` row, and `docs/plan.md` +
`docs/capture.md`. That is a large diff to then likely re-add if the underlying
queue problem resurfaces.

## 2. Critique of the plan

**The core idea — "Next absorbs `#now`" — does not work.** Next is derived from
today's open ledger and cleared when the link goes away. A weekly bet that must
survive days without a link cannot live in Next; keeping it visible would require
keeping its link in the daily file, which is precisely the status-lock trap (keep
everything linked → ~50 `[/]` + 25 `[*]`, ~15-day queue at 5 closures/day) that
motivated `#now`. The proposal's parenthetical ("every task link is either
WIP/Pending or — by default — Next") concedes the collapse: with no unlinked-Next
state, there is no weekly pool, only today's list.

**Sticky Pending re-inflates the pile.** The agent-supervision use case (remove the
link, keep the task visible in Pending while a swarm works for hours) is real, but
making `[/]` sticky in general removes the decay that the prior report's central
recommendation ("stop migrating; let decay work") depends on. The measured steady
state without decay is ~53 WIP today. A sticky `[/]` needs a replacement pruning
mechanism or it becomes the next pile with nothing but eyeballing to say so — the
same cost the `#now` decision already accepted for the tag, but now paid in the
status column where it blocks the `Next & In Progress` groups and the `^` capture
picker.

**The morning-review workflow is circular as specified.** If Pending/Next are derived
from today's ledger, "review Pending/Next to pull tasks into today" reviews work
already in today. If instead Pending = unlinked `[/]` and Next = unlinked `[*]`,
then the Today section (linked tasks, any status) plus Pending plus Next plus Ready
is indeed a coherent mutually exclusive partition — but it contradicts the
"every link is Pending-or-Next" parenthetical, and the Today section still needs
the unimplementable linkage query (see §1.1). The proposal needs to pick one
partition; see §3.

**"I don't need an untagged link" deserves a second look.** Today an untagged link
is the drive-by: reactive/incidental work that should decay without ceremony
(`#now` × `[/]` table: "Drive-by … Let it decay; nothing is lost"). Forcing every
link to be Pending-or-Next promotes every drive-by into the plan. The `#now` system
keeps this distinction for free.

**Smaller points.** (i) Removing WIP/Next sync from the hooks while keeping Blocked
derivation splits one precedence table (`docs/task-status-hooks.md` §transition
table) into authored and derived halves sharing the same checkbox — hand edits to
`[*]`/`[/]` would stick until a Blocked derivation overwrites them, producing the
inconsistent-between-runs vault the derived-status decision accepted as the cost of
full derivation, but now without the reconciler. (ii) The "Today" need is currently
met, imperfectly but today, by opening the daily note itself — the ledger *is* the
list of linked tasks. A dash section duplicates it; that is only worth it if the
render is automatic (see §4).

## 3. Adjustments if the plan proceeds anyway

If Bryan still wants Today/Pending/Next, the requirements need these corrections:

1. **Drop the file-path filter.** It cannot work (§1.1). The choice is `#today`
   tag vs a read-only rendered view (§4). Do not spend implementation time on path
   predicates.
2. **Fix the partition explicitly.** The only coherent mutually exclusive set is:
   - **Today** = linked from today's open Pomodoros (any status);
   - **Pending** = `[/]` AND NOT Today;
   - **Next** = `[*]` AND NOT Today;
   - **Ready** = TODO AND NOT Today (plus the existing blocked/hide/template/date
     exclusions on all four).
   Abandon "every link is Pending-or-Next": every link is **Today**, subdivided by
   status only in the sense that Pending/Next show the *unlinked* residue. The
   morning review then reads sensibly: Today = already pulled; Pending + Next =
   carry candidates; Ready = refill pool.
3. **Scope sticky-`[/]` narrowly or not at all.** Either keep the recent-activity
   rollback and bless one explicit gesture for the supervision case (e.g. a
   `scheduled` date + `#hide`-free "parked" convention, or simply leaving the link
   in a named `— SUPERVISION` block, which costs one ledger line), or accept that
   sticky `[/]` needs its own cap + Monday prune — i.e. all of `#now`'s lifecycle
   cost with none of its query simplicity.
4. **Do not let hooks own `#today` silently.** If a `#today` tag exists, only the
   hooks write it, writes are whole-token with the `#now` matching rule (preceded
   by start/whitespace, followed by end/whitespace; never `#today/x`), removal is
   part of the same guarded snapshot/retry path as checkbox writes, and dry-run
   reports tag edits. Budget for conflicts with the Task Status Cycler keymaps and
   `bob capture` link edits touching the same lines.
5. **Run the `#now` trial first regardless.** The decision's own reopen clause
   already provides the exit ("NOW ignored → delete the tag and keep only the
   capped ledger"). Deleting before 2026-10-13 discards the only agreed evaluation.

## 4. Recommended solution

**Keep `#now` through its trial. Add a read-only Today view. Change nothing in the
hooks' status rules.**

1. **Today view without writes.** Today's linked tasks are computable at render
   time from the ledger: extend the Bob Ledger Tools API in the style of the
   existing `nowBudget()`/`planBudget()` (which the dash chips already consume) with
   today's linked task identities, and render a `### Today Tasks` DataviewJS section
   from `plugin.getTasks()` joined by vault-relative-path + block ID — the same
   identity the hooks use for duplicate ownership. No tag, no path predicate, no
   write amplification, no editor races, no second lifecycle. If a plugin API change
   is too heavy, a `bob query --format json` + small script producing the same join
   is the fallback; either way the source of truth stays the ledger file.
2. **Supervision case without sticky statuses.** Park long-running agent work in a
   named open block (e.g. `— SUPERVISION`) or defer with a near-term P-level; both
   keep the task visible without touching rollback semantics. Revisit only if this
   proves annoying in practice during the trial.
3. **Evaluate on 2026-10-13 per the decision.** If NOW is ignored, delete the tag
   (the decision says so). If promotion from READY proves too slow, the
   pre-registered next step is a `#next` tag — not Next-status-as-horizon. If the
   Today view proves its worth, keep it; it composes with either outcome.
4. **If removal is ordered despite this:** choose the `#today` tag over the path
   filter, with the partition and write-ownership rules in §3, and budget it as a
   medium project (new hooks mutation class + tests, plugin keymap coordination,
   dash query rewrite, docs) — not a cleanup.

## Sources and method

- Live `bob query --tasks … --origin dash.md --format json` runs against `~/bob`
  on 2026-09-30 (counts quoted in §1.1; `path includes 20260930` → 1 task,
  physically resident).
- `~/bob/dash.md` (chip bar + four Tasks sections + `TQ_extra_instructions`),
  `~/bob/2026/20260930.md` (open/closed ledger entries), vault Tasks settings
  (`*` Next and `?` Blocked are `ON_HOLD`; `filter` is `#task`).
- `docs/task-status-hooks.md` (sync rules, rolling recent activity, transition
  table), `docs/plan.md` (NOW query, caps), `docs/dataview.md` (native Tasks surface).
- `src/native/task_status_hooks/sync.rs` + `compose.rs` (ledger-driven derivation,
  single-byte writes); `src/native/dataview/tasks/{mod,parse,filter}.rs`
  (NOW_QUERY, supported predicates — no referrer field).
- Memory: `#now Is A User-Owned Weekly Bet` (accepted 2026-09-29, trial to
  2026-10-13), `Active Task Statuses Are Derived` (accepted 2026-07-16);
  `research:202609/now_tag_vs_in_progress_status.md` and
  `research:202609/pomodoro_closed_day_now_tag_automation/…md` (status-lock trap,
  footprint-vs-promise, parser-safety test).
- I did not consult any peer swarm report (per instructions); shared sources above
  were used independently.
