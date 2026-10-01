# Morning GTD walk: NEW → PENDING → NEXT → scheduled-due → READY

Researcher: `grk`. Independent report. Do not treat this as the swarm synthesis.

## Bottom line

1. **Do it, with a narrower scheduled rule and a hard split between the walk and dash gating.** Folding Pending and Next into the `]s` / `[s` / Ctrl+Alt+J/K walk, in front of Ready maintenance, is the right GTD order and matches the already-filed Next task `^wip-next-refresh` in `bob_gtd.md`. The original freshness plan scoped the queue to Ready on purpose and called adding Next/Pending “a one-line change”; it is more than one line, but it is the deferred half of that design, not a new product.

2. **Keep Ready’s default interval at 7.** The new config keys for Pending and Next should default to 1. Do not give every task that merely *has* a `scheduled` field interval 1. “Refresh on the day it is due” is already `RESURFACED`. Applying `scheduled_interval: 1` to leftover past `scheduled` dates would put **59** currently-fresh Ready tasks on a daily leash.

3. **Do not strip the cutover `[fresh::]` stamps.** There are **zero** `[refresh:: N]` fields and **zero** `task_refresh` frontmatter values in the vault. The “artificial refresh properties” are the staggered seed dates on `[fresh::]`. Deleting them recreates the 199-task NEW flood the seed existed to prevent. Leave the stamps; stop *re-seeding* as a load tactic.

4. **The load bomb is Pending/Next, not Ready.** Visible in-scope counts today (2026-10-01): Ready 200 (1 NEW, 199 FRESH), Pending 50, Next 30 (4 never stamped). Caps are 10 and 15. Interval 1 on those lanes adds ~80 glances a morning until the lanes are released down to cap. The walk is still the right tool; a one-time release pass is a prerequisite for a 10-minute ritual, not an implementation detail.

The adjustments are marked **ADJ-n**. The design is in [Recommended solution](#recommended-solution).

## Is this a good idea

### What is right

- **The proposed walk is GTD’s daily order.** Inbox (NEW) → Waiting-for / WIP (PENDING) → Next actions (NEXT) → tickler (due scheduled) → a slice of Someday/Maybe (Ready due). The current ritual is the reverse of that for the expensive part: NEW → ROTTEN (Ready maintenance) → *then* PENDING → NEXT. `research:202610/gtd_morning_review_pomodoro_cutover` already called that “upside down.” Putting committed lanes before Ready rot is the correction.
- **One keymap should own that order.** `]s` / `[s` (vimrc) and Ctrl+Alt+J/K already walk `api.freshness.queue()` in source notes. Alt+Shift+F already stamps and advances. Dash rows are click-through maps and do not receive Alt+F (`docs/freshness.md` §5–§6; nav-review in bob-navigation-hotkeys). Extending the queue is how the keys start matching the morning chore.
- **Interval 1 on Pending/Next is the right primitive for “always.”** Sticky lanes are not a daily review by themselves. A Pending task stamped yesterday is still Pending this morning; without a short lease the keymap never lands on it. Default 1 means “not confirmed today” ⇒ due, which is exactly a daily lane review that drops out of the walk the moment you Alt+F / Alt+N / schedule / release.
- **Ready sort by cadence, then lateness, then recency is coherent.** A 1-day Ready task is a high-touch item; it should beat a 7-day task that is only slightly late. Among the same cadence, catch up the more overdue stamp. Among the same cadence and lateness, prefer the newer `created` (still-warm captures over fossil someday). That is a better Ready ordering than today’s `(due_on, path, line)`, which ignores interval and `created`.
- **This lets you retire seed-as-chunking.** The 7-bucket `bob freshness seed` exists because walking 199 Ready tasks on day one is unbearable. A walk that *starts* with the committed lanes, and that sorts remaining Ready by interval, does the chunking in the evaluator. You do not need fake dates for that going forward.

### What is wrong or incomplete in the request as written

- **“Any task that has a `scheduled` property” is the wrong trigger.** Future `scheduled` already means Blocked and out of scope. Past `scheduled` lingers on 59 in-scope Ready tasks, all of them already confirmed on or after that date (0 `RESURFACED` today, because the seed raised stamps to avoid it). Interval 1 on “has scheduled” would make those 59 due every day. The English goal — “refreshed on the day they are due” — is the existing tickler rule `fresh < scheduled ≤ today` (`docs/freshness.md` §4, S11). That work shipped as `^scheduled-are-stale` (done 2026-10-01).
- **“Remove artificial `refresh` properties” names a field that is not in the vault.** Vault scan 2026-10-01: 0 `[refresh::]`, 0 `task_refresh:`. 544 lines carry `[fresh::]`. The seed wrote staggered *fresh* dates, not interval overrides. Stripping `fresh` is a different, harmful operation.
- **The walk cannot “always” include every Pending and Next regardless of freshness** and also use a refresh interval. Those conflict. Interval 1 plus “due only” is the resolution: you see each lane member once a day, then it leaves the queue when confirmed. Tasks already stamped today (all 50 Pending, 26 of 30 Next) correctly skip until tomorrow.
- **Dash gating and the walk must not share one `bucket`.** `dash.md` NEW is `status.type is TODO` plus `bucket === "new"`. `rotten.md` is `not done` plus `bucket === "rotten"`. If Pending/Next become in-scope and `bucket` follows `state`, they clone onto `rotten.md` while remaining on PENDING/NEXT. The 2026-10-01 gated-Ready decision forbids that kind of double home.
- **Pending 50 / Next 30 vs caps 10 / 15.** A faithful interval-1 walk tomorrow is ~80 lane glances plus ~26 Ready from the first seed bucket. That is not a 10-minute ritual until the lanes are released. The sticky-lanes decision already named “a daily review with release and a weekly prune” as the cost of no automatic forgetting. This walk *is* that daily review; it does not replace the release work.

### Would I take a different approach

I would still use one vault-wide queue and the existing keys. I would not:

- add a second keymap family for lanes (Ctrl+Shift+J/K already walks Ready/Pending/Next *inside one note* and is a different job);
- walk dash sections (rows are not stampable);
- put Pending/Next onto `rotten.md`;
- encode the order as stored tags or a new checkbox status;
- change Ready’s default 7-day lease to 1.

The one structural alternative worth considering and rejecting: **walk every Pending/Next unconditionally, freshness-be-damned.** That makes Alt+Shift+F on a just-stamped Pending jump to the next Pending even though it is already confirmed today, and it fights the “due for review” contract the keys are named for. Interval 1 is the same daily habit with a consistent rule.

## Requirement adjustments

**ADJ-1. Keep Ready `freshness.interval` default 7.** The request’s “all of these default to 1” applies to the *new* keys (Pending, Next), not to the Ready backlog. Ready-at-1 is the old 186-task morning walk.

**ADJ-2. Do not add `scheduled_interval` as an `interval()` fallback on “has `scheduled`.”** Implement “due scheduled tasks” as their own walk *tier*: in-scope Ready `RESURFACED`, after Next, before other Ready-due. The evaluator rule stays `fresh < scheduled ≤ today`. `^scheduled-are-stale` already did the state; this request is walk order. If a config key is still wanted later, make it a boolean `resurfaced_first` (default true), not an interval.

**ADJ-3. Split the walk queue from dash/rotten buckets.** `bucket()` / dash NEW / dash READY / `rotten.md` / `counts.new|resurfaced|rotten|due` stay **Ready-only**. The keymap queue gains Pending/Next due rows with `bucket: null` and a `lane` (or `walk_tier`) field. Otherwise the gated-Ready partition `B = NEW ∪ RETURNED ∪ ROTTEN ∪ READY` breaks.

**ADJ-4. Do not delete existing `[fresh::]` stamps.** There is nothing to strip on `[refresh::]`. Treat “we won’t need to seed fake dates anymore” as a rollout policy (no second seed), not a vault rewrite. Re-stamping every Ready task as today would delay Ready review for 7 days and then cliff; stripping stamps would dump 199 into NEW.

**ADJ-5. Unstamped Pending/Next are due in their lane tier, not in dash NEW.** Dash NEW stays `status.type is TODO`. A missing stamp on `[*]` / `[/]` means “due now” in PENDING/NEXT. Today that is 4 Next tasks, including `^wip-next-refresh` itself.

**ADJ-6. Within Pending and Next, sort oldest `created` first.** The request’s “created later” tie-break is for Ready. Stuck WIP should surface before yesterday’s new Next. Dash PENDING already sorts by `created` ascending; match that. Next dash sorts by priority; for the walk, overdue DESC then created ASC is enough and keeps the comparator in the evaluator.

**ADJ-7. NEW (Ready, no stamp) still sorts before every lane.** Keep NEW uncapped and first. Current NEW sort `(path, line)` is fine; prefer `created` DESC then path/line so this morning’s Keep pull leads. One NEW task today.

**ADJ-8. Land this before the 2026-10-05 trial, and keep `rotten_daily_budget` off until lanes are at cap.** The gated-Ready trial (red chip ≤ 3 mornings, ~30 confirmed, no lost task) will be confounded if the walk suddenly includes 80 lane rows counted as ROTTEN. ADJ-3 prevents the chip lie; the trial still needs the ritual text updated so Bryan is not doing dash PENDING/NEXT *and* the keymap.

**ADJ-9. A one-time Pending/Next release pass is in scope as an operator step, not as code.** Caps 10/15 vs 50/30 is why the 10-minute budget fails. The walk should still list every due lane task (hiding overflow trains you to ignore it). Release with Alt+N until the walk is ~10 + ~15 + NEW + Ready-due.

**ADJ-10. JSON `schema_version` stays 2 if counts keep their Ready meaning.** Add optional config keys and optional queue fields. Do not reuse `counts.due` for the walk length. Add `counts.pending_due`, `counts.next_due`, and `counts.walk` (or `review`). Bump to 3 only if you change `due`’s meaning; do not.

## What is already true

| # | Fact | Evidence |
| --- | --- | --- |
| E1 | Review jumps are `jump-to-next-due-task` / `jump-to-prev-due-task` (Ctrl+Alt+J/K). `~/bob/obsidian_vimrc.md` maps `]s` / `[s` onto those commands. `planReviewJump` walks whatever `api.freshness.queue()` returns; it does not sort. | bob-navigation-hotkeys `main.js` ~24735, 24253, 27199; vault `obsidian_vimrc.md` 33–36 |
| E2 | Queue order today: NEW by `(path, line)`, then DUE (RESURFACED+ROTTEN) by `(due_on, path, line)`. FRESH and out-of-scope are omitted. | `docs/freshness.md` §4; `state.rs` `queue`; ledger-tools `freshnessQueue` |
| E3 | `in_scope` is Ready-only: TODO, lane-visible, non-recurring, not a daily note, not Today. S13 explicitly nulls `[*]`, `[/]`, future `scheduled`, `#hide`. | `docs/freshness.md` §4 / S13; `state.rs` `evaluate`; JS `freshnessEvaluate` |
| E4 | Interval precedence is `[refresh:: N]` → note `task_refresh` → `freshness.interval` → 7. Config has only `interval` and `rotten_daily_budget`. Live config has **no** `freshness:` block, so interval 7, budget off. | `docs/freshness.md` §2; `config/freshness.rs`; `~/.config/bob/config.yml` |
| E5 | `bob freshness list` evaluates `READY_QUERY` rows only (`status.type is TODO`, not blocked, not `#hide`, not templates/conflicts, scheduled empty or ≤ today). Next/Pending never enter the CLI queue. `refreshed_today` is the exception (all statuses). | `dataview/tasks/mod.rs` `READY_QUERY`; `freshness/cli.rs` `collect_list` |
| E6 | `bucket()` is `new` / `rotten` / null. Dash NEW = TODO + `bucket === "new"`. Dash READY = TODO + not Today + `bucket === null`. `rotten.md` = `not done` + `bucket === "rotten"` (RETURNED vs ROTTEN by `state`). | vault `dash.md`, `rotten.md`; decision `ready-is-freshness-gated` |
| E7 | `isDue` is `state ∈ {new, resurfaced, rotten}`. `rank` is the queue rank. Changing queue membership without changing `bucket` is how you extend the walk without cloning lanes onto `rotten.md`. | ledger-tools `apiFreshnessIsDue`, `apiFreshnessRank` |
| E8 | Original plan: “Scope is Ready only, as requested. Next and Pending are already walked every morning. Because the predicate is lane-parametric, adding them later is a one-line change.” Gated-Ready epic explicitly left “Freshness for Next/Pending” and “a changed review walk order” out of `bob-cli-3b`. | `plan:202609/task_freshness_review.md`; `plan:202610/freshness_gated_ready.md` |
| E9 | Stamps already apply in every lane (“a Next, Pending, or Blocked task may come back to Ready later”). Seed stamped non-Ready open tasks as *today* so returns are RESURFACED/ROTTEN, never NEW. | `docs/freshness.md` §5, §7 |
| E10 | Morning chore today: clear NEW (`]s`, Alt+Shift+F), then ROTTEN until 0 or budget, then PENDING → NEXT; link today’s work, release the rest. | vault `gtd_daily.md` line 18; `docs/freshness.md` §6 |
| E11 | `^wip-next-refresh` is open Next: “Make WIP and NEXT tasks have a refresh interval of 1 day!” `^scheduled-are-stale` and `^keymaps` are done. | vault `bob_gtd.md` |
| E12 | JSON schema 2, freshness namespace v3. New optional fields keep schema 2; bump only for breaking object changes. | `freshness/cli.rs` `SCHEMA_VERSION`; ledger-tools `api.freshness.version === 3` |
| E13 | Ctrl+Shift+J/K is in-note navigation of Ready / In Progress / Next, plus Pomodoro moves. It is not the review walk. | bob-plugins README; nav hotkeys |

## Live numbers (2026-10-01, read-only)

`bob freshness list -f json`: `due 1`, `new 1`, `fresh 199`, `resurfaced 0`, `rotten 0`, `refreshed_today 393`, config interval 7, budget off, queue length 1.

Vault scan of open `#task` lines outside `_templates` / `_conflicts`:

| Lane | Open | Hide | Recurring | Daily | Future scheduled | In-scope-ish (not those) | Of those, no `fresh` | Of those, `fresh` today |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Ready `[ ]` | 450 | 239 | 11 | 0 | 0 | 200 | 1 | 48 |
| Pending `[/]` | 64 | 14 | 0 | 0 | 0 | 50 | 0 | 50 |
| Next `[*]` | 31 | 0 | 0 | 1 | 0 | 30 | 4 | 26 |
| Blocked `[?]` | 269 | 0 | 2 | 0 | 256 | 13 | — | — |

Ready `[fresh::]` histogram (the 7-bucket seed): 26/26/26/15/20/38/48 on 2026-09-25 through 2026-10-01. First Ready-due wave is **26 on 2026-10-02** at interval 7.

Ready with `scheduled ≤ today`: **59**, of which RESURFACED (`fresh < scheduled ≤ today`): **0**. 28 of those 59 were stamped today.

Caps (`config.yml` `plan:`): `max_pending: 10`, `max_next: 15`, `max_ready: 100`.

`[refresh::]` count: **0**. `task_refresh:` notes: **0**.

Walk size if this shipped tonight with interval 1 on Pending/Next, Ready unchanged, stamps left in place:

| Morning | NEW | Pending due | Next due | RESURFACED | Ready ROTTEN | Walk |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2026-10-01 (today) | 1 | 0 (stamped today) | 4 (unstamped) | 0 | 0 | ~5 |
| 2026-10-02 | 1 | 50 | 30 | 0 | 26 | ~107 |
| Steady, after release to cap | ~arrivals | ≤10 | ≤15 | returns | ~200/7 ≈ 28 | ~50–60 |

107 glances on Friday is why ADJ-9 exists. After release: ~10 min is plausible (lane review + ~28 Ready), which is what the freshness research budgeted before lanes joined the walk.

## How the walk should work

### Scope

```text
walk_in_scope(t) =
    lane-visible
    ∧ ¬recurring
    ∧ ¬canonical daily note
    ∧ ¬Today(t)
    ∧ status ∈ { Ready `[ ]`, Pending `[/]`, Next `[*]` }

ready_in_scope(t) = walk_in_scope(t) ∧ Ready
```

Lane-visible stays the existing predicate (not done, not dependency-blocked, no `#hide`, not `_templates`/`_conflicts`, no `scheduled` after today). Blocked stays out. Today stays out (already on the TODAY section / being worked). Recurring stays out.

`bucket()` and dash/rotten/`counts.due` use `ready_in_scope`. The keymap queue uses `walk_in_scope`.

### Interval

```text
interval(t) =
    task [refresh:: N]
    else note task_refresh
    else Pending → freshness.pending_interval   # default 1
    else Next    → freshness.next_interval      # default 1
    else freshness.interval                     # default 7
    else 7
```

Task and note overrides still win, so a Pending task you want to glance at weekly can carry `[refresh:: 7]`. Invalid values lint and fall through, same as today.

**Not in this chain:** `scheduled_interval` (ADJ-2). RESURFACED does not care about interval; it is due on `scheduled`.

New `interval_source` values: `pending`, `next`, plus the existing `task` / `note` / `config` / `default`.

Config sketch (`~/.config/bob/config.yml`, unknown keys already ignored):

```yaml
freshness:
  interval: 7          # Ready default; days before a confirmed Ready task is due
  pending_interval: 1  # Pending `[/]` default
  next_interval: 1     # Next `[*]` default
  # rotten_daily_budget: 15
```

Chezmoi currently has no `freshness:` block; adding one is part of rollout, same as the original freshness plan.

### State

Unchanged formulas, now evaluated for Pending/Next too:

- no `fresh` → NEW (Ready) or due-in-lane (Pending/Next, ADJ-5)
- `fresh < scheduled ≤ today` → RESURFACED (Ready; Pending/Next with a due scheduled date are rare because future scheduled is Blocked, but if it happens RESURFACED still wins)
- `today ≥ fresh + interval` → ROTTEN
- else FRESH (omitted from the walk)

Due-on / days-overdue stay as today. For Pending/Next at interval 1, stamped Monday ⇒ due Tuesday (`today ≥ fresh + 1`).

### Walk order (the comparator)

Five tiers, then a per-tier key. This is the conformance vector the request’s example pins.

```text
walk_tier(t) =
    1 NEW          if Ready ∧ no fresh
    2 PENDING      if Pending ∧ due
    3 NEXT         if Next ∧ due
    4 RETURNED     if Ready ∧ RESURFACED
    5 READY        if Ready ∧ ROTTEN

NEW:      created DESC, path, line          # ADJ-7
PENDING:  days_overdue DESC, created ASC, path, line   # ADJ-6
NEXT:     days_overdue DESC, created ASC, path, line
RETURNED: due_on ASC (scheduled), created DESC, path, line
READY:    interval ASC, days_overdue DESC, created DESC, path, line
```

Missing `created`: sort last in a DESC key and first in an ASC key (treat as far past). That matches “unknown capture date is old.”

**Ready example (the request, as a vector).** Today 2026-10-08, all Ready ROTTEN:

| id | interval | overdue | created | rank in READY tier |
| --- | ---: | ---: | --- | ---: |
| A | 1 | 0 | 2026-09-01 | 1 |
| D | 7 | 3 | 2026-09-25 | 2 |
| C | 7 | 3 | 2026-09-20 | 3 |
| B | 7 | 1 | 2026-09-10 | 4 |

A before B (lower interval beats a 7-day task that is 1 day late). C before B (same interval, more overdue). D before C (same interval, same overdue, created later). Replace S14 with this plus the five-tier ordering.

### Notices and status bar

`buildReviewJumpNotice` today prints `Review 3/23 · NEW` / `· stale 4d` / `· resurfaced`. Extend:

- `· PENDING` / `· NEXT` / `· returned` / `· every 7d · 3d overdue`

Status bar stays Ready-honest: `⟳ N due · N new · ✓ N today`. Optional second segment `P n · * n` from `counts.pending_due` / `counts.next_due` so the walk length is visible without painting PENDING as ROTTEN.

Human `bob freshness list`: keep NEW / DUE groups for Ready, and add PENDING / NEXT groups (or one WALK listing in tier order). Headless review should match the keys.

### Surfaces that change vs stay

| Surface | Change |
| --- | --- |
| `docs/freshness.md` §2, §4, §6, S14, JSON | Contract. New keys, walk tiers, split bucket vs walk. |
| `src/native/config/freshness.rs` | Parse `pending_interval`, `next_interval` (1–365, default 1). |
| `src/native/freshness/state.rs` | Use `status`; expand scope; interval_for; five-tier `queue`. `created` is already on the row and currently `dead_code`. |
| `src/native/freshness/cli.rs` | Feed walk rows (Ready ∪ Pending ∪ Next from `OPEN_QUERY` filtered), not only `READY_QUERY`. Additive JSON fields. |
| `src/native/freshness/scan.rs` | Build walk rows from open tasks with symbol ` ` / `/` / `*`. |
| ledger-tools `freshnessEvaluate` / `freshnessQueue` / `freshnessRowFromTask` | Mirror. Carry `statusSymbol`, `created`. `bucket` Ready-only. |
| `rotten.md`, dash NEW/READY | **No query change** if `bucket` stays Ready-only. |
| nav `planReviewJump` | Unchanged algorithm. Notice strings + tests for new states. |
| `obsidian_vimrc.md` | Unchanged maps. |
| `gtd_daily.md` | Ritual: NEW → PENDING → NEXT → returned → Ready-due; then link/release still on the same keys. |
| chezmoi `config.yml` | Add the block. |
| decision `ready-is-freshness-gated` | New record for walk order; mark the “NEW then ROTTEN then PENDING → NEXT” sentence superseded for the *keymap*, not for dash section order. Dash stays TODAY → NEW → PENDING → NEXT → READY. |
| Vault `[fresh::]` | Leave. |
| Vault `[refresh::]` | Nothing to remove. |

Both languages keep sharing vectors in `docs/freshness.md`. That is non-negotiable; drift here would desync `]s` from `bob freshness list`.

## Implementation shape

One small epic, three sequential phases (same plugins + contract file; do not parallelize):

1. **contract-eval (bob-cli, medium).** Config keys, scope, interval_for, queue comparator, S-vectors including the A/D/C/B example, CLI list groups, JSON additive fields. `just check` on bob-cli.
2. **ledger-walk (bob-plugins, medium).** JS mirror, `freshnessRowFromTask` gains symbol/created, `bucket` stays Ready-only, `queue()` is the walk, tests in `test-ledger-tools-freshness.cjs` and `test-navigation-freshness.cjs`. Notice copy. Deploy with `bob plugins sync`.
3. **ritual-rollout (vault + chezmoi + memory, small).** Config block, `gtd_daily.md` wording, decision/glossary sentence, Bryan checklist. No vault rewrite of stamps. Operator step: Alt+N release Pending/Next to cap before 2026-10-05.

Nav does not own the sort. If phase 1’s `queue()` is wrong, `]s` is wrong; fix the evaluator, not `planReviewJump`.

## Critique of alternatives

| Alternative | Why not |
| --- | --- |
| Second keymap for lanes | `]s` is already the review finger memory. Two walks means skipping one. |
| Walk dash sections in order | Alt+F does not stamp query rows. E8 in the gated-Ready research. |
| Put Pending/Next on `rotten.md` | Double home; breaks exclusivity and the ROTTEN chip. |
| `scheduled_interval: 1` on any scheduled field | 59 extra daily Ready tasks, 0 of which are RESURFACED today. |
| Unconditional Pending/Next inclusion | Fights “due”; double-visits tasks stamped earlier the same morning. |
| Ready interval default 1 | Returns the 186-task morning. |
| Strip `[fresh::]` seed dates | 199 NEW. |
| Restamp all Ready as today | 7 quiet days, then a 199 cliff; also wrecks the trial ramp (26/day). |
| Per-note `task_refresh: 1` on project notes | Would also hit Ready tasks in those notes. Lane defaults belong in config. |
| Store walk rank on the line | Classification stays read-time. Same reason `#rotten` was rejected. |
| Change `bob task-status-hooks` | Hooks must not stamp or classify freshness. Unchanged. |

## Risks

- **107-glance Friday.** Mitigate with ADJ-9 (release to cap) before treating the trial as a fair test. The walk should still *show* overflow.
- **Rubber-stamping lanes.** Alt+Shift+F on Pending only confirms wording; it does not link or release. Keep Alt+N / Ctrl+Shift+Enter one key away. Word the Pending/Next notice as “still in this lane?” not “still a Ready idea?”
- **Bucket leak.** A single missed `is_todo` check in `bucket()` dumps Next onto `rotten.md`. Pin with a vector: `[*]` ROTTEN ⇒ `bucket null`, still in `queue()`.
- **Two evaluators.** Same mitigation as today: one doc, shared vectors, Rust + JS tests.
- **Confounding the gated-Ready trial.** ADJ-3 and ADJ-8. If this misses Oct 5, wait rather than mid-trial changing what “due” means on the chip.
- **JSON consumers.** `queue()` grows. `bob freshness list` is the only in-repo consumer besides the plugin. Additive counts protect the chip.

## Recommended solution

Adopt **one vault-wide freshness walk** whose membership is Pending, Next, and Ready, and whose order is NEW → PENDING → NEXT → RETURNED → READY, driven by config defaults 1 / 1 / 7.

1. **Keep the keys.** `]s` / `[s` / Ctrl+Alt+J/K / Alt+F / Alt+Shift+F. Sort in `api.freshness.queue()` (Rust `queue` + JS `freshnessQueue`). Do not add keymaps.
2. **Add `freshness.pending_interval` and `freshness.next_interval`, default 1.** Task `[refresh::]` and note `task_refresh` still win. Ready `freshness.interval` stays 7.
3. **Do not add `scheduled_interval`.** RETURNED (Ready RESURFACED) is tier 4. That is “refresh on the day it is due.”
4. **Split walk from dash.** `bucket` / dash / `rotten.md` / `counts.due` stay Ready-only. Queue rows for Pending/Next carry `lane` and `bucket: null`.
5. **Ready-due comparator:** `interval ASC`, `days_overdue DESC`, `created DESC`, path, line. That is the A/D/C/B example.
6. **Pending/Next comparator:** `days_overdue DESC`, `created ASC`, path, line.
7. **Ritual text:** morning is the walk, then link/release as you go (Alt+N is a review outcome, not a later phase). Weekly prune still clears leftover Ready-due and looks for projects with no Next or Ready.
8. **Vault:** leave `[fresh::]` stamps; there are no `[refresh::]` overrides to delete; do not re-seed.
9. **Operator:** release Pending/Next to 10/15 before the first interval-1 morning you care about measuring.
10. **Trial:** ship before 2026-10-05 so the gated-Ready two-week window measures this ritual, not the old NEW→ROTTEN→lanes split.

Success: yesterday’s captures still hit NEW first; every Pending and Next not confirmed today is in the same finger memory as Ready-due; due scheduled Ready tasks beat other Ready rot; a 1-day Ready task beats a 7-day task that is slightly late; dash NEW/READY/ROTTEN counts still mean Ready; the 10-minute budget holds once lanes are at cap.

## Sources

- Vault, 2026-10-01: `bob freshness list -f json`; `gtd_daily.md`; `bob_gtd.md`; `obsidian_vimrc.md`; `dash.md`; `rotten.md`; `~/.config/bob/config.yml`; a read-only scan of `#task` lines for status / `fresh` / `refresh` / `scheduled` / `created`.
- bob-cli: `docs/freshness.md`; `src/native/freshness/{state,cli,scan,seed}.rs`; `src/native/config/freshness.rs`; `src/native/dataview/tasks/mod.rs` (`READY_QUERY`); `sase/memory/decisions/ready-is-freshness-gated.md`; `sase/memory/decisions/task-lanes-are-sticky.md`; `sase/memory/glossary/task-freshness.md`.
- bob-plugins: `plugins/bob-navigation-hotkeys/main.js` (nav-review, `planReviewJump`, Ctrl+Alt+J/K); `plugins/bob-ledger-tools/main.js` (`freshnessEvaluate`, `freshnessQueue`, `api.freshness`); `scripts/test-navigation-freshness.cjs`.
- Plans: `plan:202609/task_freshness_review.md`; `plan:202610/freshness_gated_ready.md`.
- Prior research (not this swarm): `research:202609/ready_task_freshness_review/ready_task_freshness_review.md`; `research:202610/freshness_gated_ready_dash/freshness_gated_ready_dash.md`; `research:202610/gtd_morning_review_pomodoro_cutover/gtd_morning_review_pomodoro_cutover.md`.
- External prior art already adopted by the freshness design: Taskwarrior `tasksh review`; OmniFocus Review perspective; GTD daily vs weekly review.

## About this report

- **Date:** 2026-10-01
- **Researcher:** `grk` in the 5-researcher swarm on morning GTD walk order and lane refresh intervals
- **Question:** How should `[s` / `]s` and Ctrl+Alt+J/K walk NEW, Pending, Next, then Ready (by interval, overdue, created); how should Pending/Next/scheduled default intervals work; should the staggered seed dates / artificial refresh fields go away; is the plan a good idea?
