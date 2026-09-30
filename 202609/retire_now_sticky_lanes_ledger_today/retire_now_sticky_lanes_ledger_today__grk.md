# Keep `#now`. Query Today from the ledger. Stop wiping parked `[/]`.

- **Researcher:** grk
- **Date:** 2026-09-30
- **Question:** Was adding `#now` a mistake? Should `bob task-status-hooks` stop syncing Next/WIP from Pomodoro Task Links, and should `~/bob/dash.md` switch from overlapping Now/WIP/Next sections to mutually exclusive Today/Pending/Next sections, with either a file-path filter or a machine-managed `#today` tag filling the "tasks linked from today's daily file" query?

---

## Recommendation

**No: `#now` was not a mistake. The 73-tag bulk load and strip on day one of the trial was.** Keep the tag as the weekly bet. Keep Next `[*]` derived from today's open Pomodoro Task Links. Stop the scoped In Progress rollback so a parked `[/]` survives unlinking. Replace the overlapping dash sections with mutually exclusive **Today / Pending / Now / Ready** queries, where Today is ledger-link identity from the same `bob-ledger-tools` parse that already feeds the PLAN chip.

Do not collapse `#now` into the Next checkbox. Do not have hooks manage a `#today` tag. Do not use a Tasks `path`/`filename` filter for this query: that selects tasks *living in* the daily note, not tasks *linked from* it.

---

## 1. Live vault, evening of 2026-09-30

| Signal | Value | Reading |
| --- | --- | --- |
| `bob plan` | `PLAN 3/3 · 6/10`, `NOW 0/15` | The closed-day cap is in force. The weekly tag is empty. |
| `#now` tasks | **0** | The 73-tag cohort from `plan:202609/tag_open_pomodoro_now.md` is gone (`plan:202609/remove_now_tags.md`). |
| Unblocked WIP `[/]` | **53** in 7 notes | Still the ~50-task pile measured on 2026-09-29. |
| Unblocked Next `[*]` | **27** in 5 notes | Still the ~25-task pile. Today's open ledger has **6** Task Links. |
| Unblocked Ready | 186 | Backlog. |
| Blocked | 290 | Unchanged role; out of scope here. |
| Today's open themes | BOB, CLEANUP, BETS (+ exempt GTD) | Matches the GTD+3 rule. |

Today's open Task Links, from `~/bob/2026/20260930.md`:

- BOB: `bob#^fuzzy-capture-task`, `bob#^improve-gtd-process`
- CLEANUP: `sase#^clean-prompt-history`, `sase#^fix-split-epic`
- BETS: `sase#^linker`, `sase#^memory-file-versions`
- GTD (exempt): `^gtd`

`gtd_daily.md` already encodes the intended morning pick:

> Pick today: ≤3 themes from yesterday + [[dash#NOW Tasks|NOW]] (highlight first)

and a Monday chore to re-tag NOW to ≤15.

The two-week trial named in `research:202609/pomodoro_closed_day_now_tag_automation` is **2026-09-30 → 2026-10-13**. This is day one. Rolling recent activity still sees `2026/20260929.md`, which held ~73 live links, so the 53 `[/]` tasks have not yet had a night to decay. Evaluating "WIP wipe is the problem" against tonight's counts attributes yesterday's queue to a rule that has not had a chance to fire.

---

## 2. The diagnosis in the request is inverted

The request says `#now` was deemed necessary in order to *preserve* `task-status-hooks` keeping WIP/Next in sync with Pomodoro Task Links.

The accepted decision says the opposite.

`decisions:now-tag-is-user-owned`:

> `#now` is a plain Obsidian tag on a `#task` line that marks one of this week's bets. … Nothing adds it implicitly … and no hook, cron job, or sync strips it. It is independent of the checkbox: `bob task-status-hooks` only counts it, it never makes a task Next.

`research:202609/now_tag_vs_in_progress_status.md`:

> `[/]` is a footprint. `#now` is a promise. The report adds `#now` so that `[/]` can go back to telling the truth.

The *status-lock trap* measured on 2026-09-29 was: unlinking demotes the task, nothing else remembers that it mattered this week, so everything stays linked (~50 `[/]`, ~25 `[*]`, ~80 queued links). `#now` is the safety net that makes unlinking cheap. Derived Next/WIP can then decay. The closed-day ledger (GTD + 3 themes, ≤10 links) is the daily cap. The tag is the weekly cap.

Collapsing the weekly bet into Next `[*]` puts both questions back on one checkbox. That is the trap, restored.

What actually went wrong today is documented in two vault-data plans:

1. `plan:202609/tag_open_pomodoro_now.md` tagged **all 73** tasks linked from 2026-09-29's open Pomodoros, including the 23-link `LATER` inventory bucket, and *intended* `NOW 73/15` over cap.
2. `plan:202609/remove_now_tags.md` then stripped those 73 tokens.

That is not a weekly review. It is "yesterday's queue = this week's bets", which is the same identification the tag was invented to break. After the strip, NOW is 0, so the dash section looks like a mistake. The mechanism was never given a curated ≤15 set.

---

## 3. Critique of the proposed plan

The proposed shape:

1. Stop hooks from syncing WIP/Next to Pomodoro Task Links.
2. Query "tasks associated with task links in today's daily file" via a path filter or a hooks-managed `#today` tag.
3. Replace dash Now/WIP/Next with mutually exclusive Today/Pending/Next.
4. Morning GTD: review Pending/Next, pull into today, then Ready.
5. Move `#now`'s job onto Next status.
6. Do not wipe Pending/WIP, so an in-progress task can leave the daily file while a swarm runs.

### What is right

**Mutually exclusive dash sections are a real upgrade.** `~/bob/dash.md` currently stacks overlapping Tasks queries:

```text
NOW:   tags include #now
WIP:   status.type is IN_PROGRESS
NEXT:  status.name includes Next
READY: status.type is TODO
```

A `[/]` `#now` task appears in NOW and WIP. A `[*]` task on today's ledger appears in NEXT. Chip counts and section membership disagree with how a morning review actually walks the list. Today / Pending / Now / Ready, each task in at most one section, matches the review the request describes.

**The parked-WIP case is a real gap.** A task that is started, will be finished the next time it is looked at, and should leave today's face (agent swarm for a few hours, or longer) has no first-class home. Current rules:

- Open-Pomodoro links seed Next; `[/]` is left alone (`docs/task-status-hooks.md`).
- Area/project `[/]` resets to `[ ]` once the identity is absent from *rolling recent activity*: today's ledger (open **and** completed, non-retired) plus the previous daily.
- `Ctrl+Shift+Enter` on a Task Link deletes the link and sets the task Open (`research:202609/pomodoro_closed_day_now_tag_automation` §1).
- Close/start `~<K>` drops (`plan:202609/start_drop_queued_links.md`) also leave demotion to the hooks.

A few hours of swarm work is already covered if the 🍅 link remains under today's *completed* Pomodoro: PLAN only counts *open* links, and recent activity still protects `[/]`. The hole is: **remove the link from the daily file entirely, and still find the task in a Pending section days later.** `#now` covers visibility (the task stays in NOW) but NOW is designed to be in-your-face with a cap of 15. Pending as a quieter parking lot is a justified extra bucket.

**Morning review order is right:** parked in-progress and weekly bets before Ready.

### What is wrong

**Repurposing Next as the weekly bet deletes the only materialized "on today's ledger" status and then has to reinvent it.** Next `[*]` today *is* "reachable from today's open Pomodoros" (direct links plus transcluded `![[note#^id]]` dependencies). The request's unfilled need after stopping that sync is exactly the query Next already answers, minus In Progress, which outranks it on the checkbox.

**A Tasks file-path filter does not work here.** `path includes 2026/20260930` / `filename includes 20260930` select tasks whose *own* file is the daily note. Daily Task Links point at `bob.md`, `sase.md`, … The Pomodoro checkboxes in the daily file are not `#task` lines, so they miss the global filter. Path filters are the wrong axis.

**A hooks-managed `#today` tag is the alternative the `#now` decision already rejected.** From `decisions:now-tag-is-user-owned`, rejected:

> `#now` as a Next source, or tools that backfill it. … hooks or cron that sweep leftovers into a horizon edit history behind open editors and multi-machine sync.

`#today` added and stripped by `task-status-hooks` every 15 minutes is that backfill, on a tag. It creates a second source of truth next to the ledger, races Obsidian buffers (the hooks already defer on a two-second quiet interval for grouping writes), and puts a machine-owned token on the task line beside user-owned `#now` / `#hide`.

**Stopping Next derivation plus stopping WIP wipe re-authors both active statuses.** `decisions:task-status-is-derived` exists because authored `[B]` Blocked died unused, Next was derived from open Pomodoros two days later, and In Progress rollback followed so the checkbox could decay. Making Next the weekly bet and Pending a sticky `[/]` returns to authored checkboxes with a weekly review as the only drain. The 53 WIP / 27 Next piles are what that looks like before the drain.

**"Every task link is Next or WIP" is a loss the request treats as fine; it is the status-lock.** Drive-by and reactive work (the report's ⚪ cell: `[/]` without `#now`) needs to fall off the weekly face. If every link is a weekly bet, the ledger cannot shrink.

**Day-one trial reversal is premature.** The trial's own kill rule (`research:202609/pomodoro_closed_day_now_tag_automation` recommended solution) is: *if NOW is ignored, delete the tag and keep only the capped ledger.* NOW was never curated. It was bulk-filled to 73, emptied to 0, and then questioned. The PLAN half of the same epic is already working (3/3 · 6/10). Throw away the unused tag after a real Monday review, not tonight.

**Project-note grouping and the `^` picker both assume current Next.** Area/project notes get `### Next & In Progress` from the same hooks run (`docs/task-status-hooks.md` Status Grouping). Capture's active-task picker lists In Progress, Next, then Ready `#now` (`src/native/capture_active_tasks.rs`). If Next becomes the weekly bet, those surfaces start listing weekly commitments instead of today's queue, and Ready `#now` support becomes a second copy of Next.

---

## 4. How to query "tasks linked from today's daily file"

This is the only new query the dash needs. Four candidates:

| Approach | Does it select the right tasks? | Cost |
| --- | --- | --- |
| Tasks `path` / `filename` filter | No. Own-file, not incoming Task Links. | Cheap and wrong. |
| Hooks-managed `#today` tag | Yes, if hooks stay correct. | Dual source of truth; editor races; rejected backfill pattern. |
| Keep derived Next as the index | Partial. Next is the open-Pomodoro *graph*, and `[/]` linked today is *not* Next on the checkbox. | Already built; misses WIP-on-today and over-includes dependency-only Next. |
| Ledger identity via `bob-ledger-tools` / DataviewJS | Yes. Same parse as PLAN: distinct `(target, block_id)` under today's **open** non-exempt Pomodoros. | One definition, already on the dash as the PLAN chip. |

Obsidian Tasks *can* filter on links (`task.outlinks`, `query.file.outlinks`, since Tasks 7.21.0; see [Links](https://publish.obsidian.md/tasks/Getting+Started/Links) and [discussion #2392](https://github.com/obsidian-tasks-group/obsidian-tasks/discussions/2392)). That still does not help a query *in `dash.md`*: `query.file` is `dash.md`, not `YYYY/YYYYMMDD.md`. A `filter by function query.file.outlinks.some(...)` would see the dashboard's outlinks. Native `bob query` currently hydrates `file.outlinks` as `[]` (`src/native/dataview/tasks/js.rs`), so even a query *in* the daily note would not match under the native engine.

Generating a Tasks block of `path includes sase.md OR path includes bob.md` from the daily's outlinks (the DataviewJS trick in that same discussion) is also too coarse: `sase.md` holds on the order of 250 tasks. Block-id identity is required.

The dash already has the right seam. `bob-ledger-tools` exports `api.planBudget()` and `api.nowBudget()`; `dash.md` uses both for chips. Extend that API with today's open Task Link identities — the same set `docs/plan.md` calls **Links** — and resolve them against `plugin.getTasks()` by vault-relative path plus block id. Render the Today section in DataviewJS (or a `bob-plan`-style processor) so it does not depend on a Tasks instruction that cannot see another file's block links.

**Today's membership rule (recommended):** open, non-exempt Pomodoro Task Links in the current daily, same as the PLAN link cap. Completed 🍅 links stay history; they keep `[/]` via recent activity but do not occupy Today. Transcluded dependencies stay in the project note unless they are themselves linked. That keeps Today ≤ ~10 and aligned with the budget Bryan already looks at.

If Tomorrow's review needs the dependency graph too, expose it as an option. Default to direct links.

---

## 5. Parked WIP, without re-authoring Next

The request's swarm example is the requirement that should change.

**Justified adjustment:** stop *scoped In Progress rollback* in area/project notes. Keep Next promotion and Next clearing. Keep derived Blocked.

Consequences:

- Dropping a Task Link demotes `[*]` → `[ ]` on the next hooks run (today's queue stays honest).
- `[/]` stays `[/]` until Bryan completes, cancels, or cycles it.
- Pending on the dash is then `status.type is IN_PROGRESS` minus Today.
- A swarm can leave the daily file and remain in Pending.

This is a smaller reopening of `decisions:task-status-is-derived` than "Next and In Progress are both authored." The decision's claim is that Next, In Progress, *and* Blocked are derived. Reopen it only for In Progress rollback, with an explicit new record: `[/]` is a footprint Bryan parks; Next remains ledger-derived; Blocked remains dependency/schedule-derived.

**Also change the drop gestures** so they stop setting the task Open when it is already `[/]`:

- `Ctrl+Shift+Enter` on a link line: remove the link; leave `[/]` alone; still allow `[*]` → `[ ]` (or leave that to hooks).
- `=x~<K>` / `=~<K>`: same. `plan:202609/start_drop_queued_links.md` already says start drops do not write the task note; close drops should match.

Without that, the hooks change is undone by the keymap the next time Bryan parks work from the daily note.

**Do not leave Pending uncapped with no review.** 53 sticky `[/]` is the 2026-09-29 pile, frozen. Add a Monday line next to the NOW re-tag: prune Pending. A red Pending chip with a soft cap (same 15, or a separate `plan.max_pending`) is enough; do not enforce in capture.

A user-owned `#parked` tag is an alternative that keeps `[/]` derived. It is a third tag and another weekly chore. Sticky `[/]` plus a Pending section is fewer markers, and the checkbox already means "started."

`#now` remains available when parked work is also a weekly bet. Those tasks sit in Pending (WIP wins mutual exclusion) and still count toward NOW 15. That is correct: they are this week's work, just not today's face.

---

## 6. Naming: do not rename Next to mean `#now`

The request uses "Next" for two different jobs:

| Request word | Current Bob meaning | Proposed in the request |
| --- | --- | --- |
| Next | Derived `[*]`: on today's open-Pomodoro graph | Weekly bet (today's `#now`) |
| Pending / WIP | Derived `[/]`, wiped after one daily of grace | Sticky in-progress parking lot |
| Today | Not a section; approximated by NEXT + some WIP | Ledger Task Links |
| Now | `#now` tag, weekly bet | Deleted |

If Next the *checkbox* becomes the weekly bet, every surface that says "Next" today (status groups, badges `🔵 next/wip`, capture `^` picker, hooks JSON `marked_next`, `docs/task-status-hooks.md`) has to be rewritten, and the word "Next" in GTD/roadmap language (Now / Next / Later) collides with a checkbox that used to mean "queued this session."

Keep the checkbox names. Change the *dash section* names:

| Dash section | Membership (mutually exclusive, first match wins) |
| --- | --- |
| **Today** | Identity in today's open non-exempt Task Links (ledger API). Any checkbox. |
| **Pending** | `[/]` and not in Today. |
| **Now** | `#now`, not done, not blocked, not `#hide`, scheduled empty or ≤ today, and not in Today or Pending. |
| **Ready** | `[ ]` (TODO), not `#now`, not in Today. |

NEXT as a dash section goes away. The `[*]` checkbox remains, and almost every `[*]` will sit in Today because that is what the hooks still derive. A `[*]` that is somehow not linked (hand-set, hooks lag) belongs in Ready or in a small "queued" fold under Today; do not keep a fifth chip for it.

Later remains P1–P4 / Blocked, as today.

---

## 7. Alternatives considered

### A. Delete `#now`, author Next, query Today, sticky WIP (the request)

Works as a closed system: Next is the weekly list, Today is the daily list, Pending is parked. It throws away two accepted decisions, the NOW meter/toggle/capture completion work in epic `bob-cli-2o`, and the ability to have drive-by ledger work that is not a weekly bet. It also needs the same weekly prune `#now` already has, just on a checkbox the hooks currently overwrite. **Reject unless a real two-week trial shows NOW ignored after a curated ≤15 set.**

### B. Machine `#today` plus keep `#now` and derived statuses

Today's query becomes a Tasks one-liner (`tags include #today`). Pays the backfill/editor-race cost for a marker the ledger already stores. **Reject.**

### C. Path filter plus keep everything else

Does not select the right tasks. **Reject.**

### D. Keep everything, including WIP rollback; only make dash sections exclusive

Smallest change. Today via ledger API; Pending = `[/]` not in Today (a 1-day window); Now = `#now` remainder. The swarm-for-days case still has to use `#now` or a leftover completed-Pomodoro link. **Insufficient for the parked requirement the request called out.**

### E. Recommended: keep `#now` and derived Next/Blocked; stop WIP rollback; exclusive dash; ledger Today query

See §8.

### F. Trial kill switch (already written)

If after 2026-10-13 NOW is unused, delete the tag and keep the capped ledger. Do not pre-execute that kill switch on the evening of day one.

---

## 8. Recommended solution

### Product rule (one index card)

> **Today is the open ledger** (GTD + ≤3 themes, ≤10 Task Links). **Pending is started work that left the ledger** (`[/]`, not wiped). **This week is `#now`** (≤15, user-owned). **Ready is everything else.** Blocked stays derived. Next `[*]` stays the hooks' spelling of "on today's graph," and the dash no longer shows a Next *section*.

### Dash (`~/bob/dash.md`)

1. Chips, in order: **TODAY** (count/10, from `planBudget().links`), **PENDING** (`[/]` minus Today), **NOW** (existing `nowBudget()`), **PLAN** (keep; or fold into TODAY), **READY**, **BLOCKED**.
2. Sections with the same names, mutually exclusive, first match wins, using the table in §6.
3. Implement Today in DataviewJS (or a ledger-tools renderer) by resolving `planBudget` link identities to `plugin.getTasks()`. Do not use a Tasks `path` filter. Do not add `#today`.
4. Extra instructions on `dash.md` already exclude `_templates`, `#hide`, blocked, future scheduled, and self. Keep those as global defaults; apply Today/Pending/Now/Ready *after* them.

### `bob task-status-hooks`

1. **Keep** Next promotion from open-Pomodoro Task Links and transcluded dependencies.
2. **Keep** vault-wide Next clearing when unreachable.
3. **Keep** derived Blocked, grouping, duplicate/canceled/completed-link cleanup, 🍅 markers, empty-Pomodoro removal.
4. **Stop** the scoped area/project `[/]` → `[ ]` rollback. Leave `[/]` until a terminal status or an explicit cycle.
5. Do not add, strip, or infer `#now` or any `#today`.
6. Record a new decision strand that supersedes only the In Progress rollback clause of `task-status-is-derived`. Leave `now-tag-is-user-owned` in force.

### Drop gestures (bob-plugins + capture)

- Unlink / `~<K>` drop: never write `[/]` → `[ ]`. Next demotion stays with the hooks.
- Notices can say "stays in Pending" the way they already say "stays in NOW" for `#now` rows.

### Morning GTD (`gtd_daily.md`)

Rewrite the pick chore to:

1. Pending (parked `[/]`): resume, complete, or leave parked.
2. Now (`#now` not already in Today/Pending): pull into today's ≤3 themes.
3. If the day still has room, Ready.

Keep the Monday NOW re-tag (≤15). Add "prune Pending" to that same chore.

### What Bryan does this week (no new tag, no epic)

1. Do **not** bulk-tag yesterday's queue.
2. Alt+N (or type `#now`) on **at most 15** tasks that are actually this week's bets.
3. Keep today's ledger at GTD+3 / ≤10 links (already true tonight).
4. Park swarm work by dropping its Task Link; expect it in Pending, not on the daily face.
5. On 2026-10-13, look at the trial table. If NOW is still 0 because it was never curated, that is process failure, not evidence the tag is the wrong marker.

### Deliberately not doing

- Deleting `#now` during the trial.
- Hooks-managed `#today` / `#next`.
- `[roadmap::]` / `[horizon::]` fields (parser-unsafe; already rejected).
- A hand-kept `roadmap.md`.
- Stopping Next derivation.
- Treating a Tasks path filter as a backlink query.
- Making every Task Link a weekly bet.

---

## 9. Requirement adjustments (called out)

These differ from the request. Each is required by evidence above.

1. **Keep `#now`.** The unused-tag feeling is the 73→0 vault-data swing, not a design failure. Revisit only after the trial's kill rule actually triggers.
2. **Keep Next `[*]` derived from today's open Pomodoros.** It is the index the request would otherwise rebuild. Stop *showing* it as a dash section.
3. **Stop only WIP rollback, not the whole status sync.** Parked `[/]` is the new requirement; derived Next and Blocked still earn their keep.
4. **Today = open-ledger Task Link identity via ledger-tools, not a path filter and not `#today`.**
5. **Mutual exclusivity is a dash query order, not a new checkbox.** Status + tag + ledger membership remain independent facts.
6. **Drive-by Task Links that are not `#now` remain allowed.** Losing that is the status-lock.
7. **Pending needs a weekly prune (and a chip), even though it is not wiped by hooks.** Otherwise 53 `[/]` becomes the new NOW pile.
8. **Do not judge WIP counts until 2026-10-01**, when `20260929.md` drops out of rolling recent activity. Tonight's 53 is still yesterday's grace window.

---

## 10. If the trial later kills `#now`

Then — and only then — the request's collapse is the right fallback, with these constraints carried forward:

- Next becomes authored (weekly bet); hooks must stop both promoting and clearing it.
- Today remains a ledger-identity query (still no path filter, still no `#today` tag).
- Pending remains sticky `[/]`.
- The `^` picker lists Next + Pending; Ready `#now` support is deleted with the tag.
- `plan.max_now` counts Next instead of the tag; Alt+N cycles `[*]` instead of a token.
- Write a new decision strand; mark `now-tag-is-user-owned` superseded. Do not edit it in place.

That is a three-repo epic of similar size to `bob-cli-2o`. It is not tonight's work.

---

## Sources

**Vault and live commands (2026-09-30 evening, read-only):**

- `bob plan -f json` → `PLAN 3/3 · 6/10`, `NOW 0/15`, themes BOB/CLEANUP/BETS, daily `2026/20260930.md`
- `bob query --format json --tasks` counts: NOW 0; unblocked WIP 53; unblocked Next 27; unblocked Ready 186; Blocked 290
- `~/bob/2026/20260930.md` `## Pomodoros` (open links listed in §1)
- `~/bob/dash.md` chip bar and NOW/WIP/NEXT/READY Tasks blocks
- `~/bob/gtd_daily.md` pick-today and weekly-NOW chores

**Accepted decisions and docs:**

- `sase memory read decisions:now-tag-is-user-owned decisions:task-status-is-derived glossary:task-link glossary:pomodoro`
- `docs/task-status-hooks.md` (promotion, rolling recent activity, `[/]` rollback, grouping, precedence table)
- `docs/plan.md` (NOW query, link identity, caps)
- `docs/dataview.md` (`bob query --tasks` JSON)

**Code:**

- `src/native/capture_active_tasks.rs` (`^` picker: `[/]`, `[*]`, Ready `#now`)
- `src/native/dataview/tasks/mod.rs` `NOW_QUERY`
- `src/native/dataview/tasks/js.rs` (empty `file.outlinks` in native engine)
- `bob-plugins` `plugins/bob-ledger-tools/main.js` (`api.planBudget`, `api.nowBudget`)

**Prior research and plans (unrelated to this swarm's peer drafts):**

- `research:202609/pomodoro_closed_day_now_tag_automation/pomodoro_closed_day_now_tag_automation.md`
- `research:202609/now_tag_vs_in_progress_status.md`
- `plan:202609/pomodoro_plan_budget_now_tag.md` (epic `bob-cli-2o`)
- `plan:202609/tag_open_pomodoro_now.md` (73-tag bulk load)
- `plan:202609/remove_now_tags.md` (73-tag strip)
- `plan:202609/start_drop_queued_links.md` (start `~<K>` drops; demotion left to hooks)

**Obsidian Tasks:**

- [Links](https://publish.obsidian.md/tasks/Getting+Started/Links) (`task.outlinks`, `query.file.outlinks`)
- [Custom Filters](https://publish.obsidian.md/tasks/Scripting/Custom+Filters)
- [Discussion #2392](https://github.com/obsidian-tasks-group/obsidian-tasks/discussions/2392) (tasks in files the query note links to — file-level, not block-level)
- [Discussion #3749](https://github.com/obsidian-tasks-group/obsidian-tasks/discussions/3749) (`task.outlinks` / `link.destinationPath`)
