# Keep streaks, not a lifetime `refresh_count`: graduate the review interval

Researcher: `grk`. Independent report. Do not treat this as the swarm synthesis.

- **Date:** 2026-10-03
- **Question:** Should every explicit Alt+F freshness refresh write a new `refresh_count` property, rendered like `[fresh::]`, so later (user-approved at decay time) auto-decay can fire on tasks that keep being manually refreshed? Critique the plan, adjust requirements where justified, and recommend a design.
- **Evidence:** `docs/freshness.md` §§2–6, 11; `docs/projects.md` “Recommended roll and priority decay”; glossary: Task Freshness; `decisions/review-walk-is-tiered`; placement helpers (`src/native/freshness/placement.rs`, ledger-tools `stampLine`); nav `refresh-task-freshness` / `refreshTaskFreshness`; freshness mark CSS/widget; live `bob freshness list -f json` and `bob query` on 2026-10-03; prior research `research:202609/ready_task_freshness_review`, `research:202610/tiered_morning_review_walk`, `research:202610/freshness_gated_ready_dash`; [tasksh review](https://taskwarrior.org/docs/review).

## Bottom line

1. **Track explicit keeps. Do not store a lifetime `refresh_count` that increments on every Alt+F.** The instrument you need is a **due-Ready keep streak**, stored as `[keeps:: N]` next to `[fresh::]` / `[refresh::]`, folded into the existing freshness mark. A lifetime counter that also counts lane daily keeps would put ~93 Next/Pending tasks over any small threshold in three days and fight sticky lanes.

2. **Do not copy priority decay onto rotten refreshes.** Rolling “not now” is avoidance; Alt+F means “still right.” Those are opposite signals. Priority decay demotes, then cancels. Rotten-keep decay should **lengthen the review interval** (7 → 14 → 30 → 90), user-approved at the moment Alt+F would otherwise rubber-stamp. That is tasksh’s own advice, automated: “If you find yourself making no changes to the tasks, perhaps you should review less often.”

3. **Ship the streak and the mark now; do not turn on intercept during the 2026-10-05 → 2026-10-18 freshness trial.** Today’s 52 rotten tasks are all in `gkeep_inbox.md`, all still on the 2026-09-25 seed stamp, never human-kept. Counting from this week captures the first real keep cycle. Interval graduation can land after the trial’s keep rule has been scored.

The adjustments are marked **ADJ-n**. The design is in [Recommended solution](#recommended-solution).

## Is this a good idea

### What is right

- **The failure mode is real, and it is not “tasks I keep deferring.”** Priority decay already covers RETURNED + `Ctrl+Enter`: after `rolls` same-level rolls, the next recommended roll is `P2 → P3 decay`, and past P4 it cancels (`docs/projects.md`). The hole is ROTTEN + Alt+F: “still right” with no other change, every interval, forever. The original freshness research already named this: “Refresh is not clarification. Glancing at a task and pressing Refresh, without deciding whether it belongs to today, is a failed review.” (`research:202609/ready_task_freshness_review` §2). The walk decision named the same risk on lanes: “the rubber-stamp risk of a daily lane queue” (`decisions/review-walk-is-tiered`).
- **A stored, visible streak makes rubber-stamping honest.** The freshness mark already has one glyph lifecycle (`✓` / draining ring / `⟳`) and is loud only when due (`docs/freshness.md` §11). Folding a small keep tally into that mark tells you, in the same glance, “this lease has been renewed without the task changing.” That is the missing affordance. Ctrl+Shift+P → refresh 14/30/90 already exists as “see it less often”; people do not take it. A mark that fills toward a graduation is how the path of least resistance becomes the path that asks the question.
- **User-approved at decay time is the right constraint.** Priority decay never silently rewrites: `Ctrl+Enter` takes a *previewed* recommendation, and `↵` on `scheduled` never decays. Rotten-keep decay must work the same way: the chord that currently means keep (Alt+F) changes meaning at the threshold, with an explicit “keep anyway” escape that resets the streak. Silent interval bumps or silent P-level drops would hide history behind the editor, the same class of mistake a `#rotten` tag would have been (`research:202610/freshness_gated_ready_dash`).
- **The field belongs on the line, next to `fresh` / `refresh`.** Freshness has no out-of-line key (few block IDs, hooks move blocks). A child “refresh log” would add a line per keep; Ready keeps are weekly and lane keeps would be daily. Priority decay can derive a streak from the Schedule Log because rolls are rare. Keeps are not rare. An inline integer, omitted at 0, is the same shape as `[refresh:: N]`.

### What is wrong in the request as written

- **`refresh_count` names the wrong thing.** In this system `refresh` already means the interval in days (`[refresh:: 14]`, the Ctrl+Shift+P refresh row, `setRefreshLine`, `task_refresh`). A `refresh_count` field reads as “how many times the interval was set,” which is the rare gesture, not the daily/weekly keep. The ritual word is **keep** (“keep with Alt+F”, tooltip `Alt+F keep`, `Alt+F to confirm`).
- **“Every time `fresh` is updated via Alt+F” mixes four different events.**
  1. First confirmation of NEW (inbox processing).
  2. Daily lane keep of Pending/Next (the sticky-lanes daily review).
  3. Early confirm of a still-FRESH Ready task (including “wording wrong: edit, then Alt+F”).
  4. Due-Ready keep of ROTTEN (the rubber-stamp you want to catch).
  Alt+F and Alt+Shift+F are the same function (`refreshTaskFreshness`, `advance` flag). Many other gestures also stamp `fresh` (`docs/freshness.md` §5): Alt+N, Ctrl+Shift+P rows, Ctrl+Shift+M, Ctrl+Enter roll/decay, cycler, capture. A counter that increments on (1)+(2)+(3)+(4), or on every stamp, cannot drive decay.
- **Copying the priority-decay ladder onto refreshes is a category error.** A roll says “not now.” A keep says “this is still correctly specified and still belongs in Ready.” Demoting P-level, then cancelling, punishes correctly parked backlog. Implicit-P0 inbox tasks (no `priority` field) cannot enter that ladder at all — and those are exactly today’s rotten pile.
- **A lifetime count does not reset when the task actually changes.** Priority decay’s streak is derived: only consecutive `🎲 <L> roll` entries count; a typed reason, a priority-row pick, or a decay stops it. A monotonically increasing `refresh_count` would fire decay on a task you rewrote last week. Decay needs a streak with reset rules, not a total.

### Would I take a different approach

I would still add an inline field and fold it into the freshness mark. I would not:

- add a `🔁 REFRESH LOG` child (too much volume; the Schedule Log is opt-in and sparse);
- write a `#kept` / `#rotten` tag or a hooks-maintained marker (read-time freshness already forbids this);
- teach Obsidian Tasks the new key (same reason `fresh` stays out of `try_take_dataview_field`: native `bob query` must mirror Tasks);
- make Alt+F open a picker on every keep (the one-key walk dies);
- auto-drop priority or auto-cancel as the default recommendation;
- count lane daily keeps toward Ready graduation.

The one structural alternative worth taking seriously: **spaced repetition with no stored streak** — each keep writes the next interval immediately (7→14 on the first rotten keep). That is Anki “Good.” It is too chatty once you add user-approval (a prompt every week), and too silent without it. A short streak *inside* each interval step, then one approved graduation, is SM-2 with a learning-steps threshold. That is the design below.

## Live vault (2026-10-03)

`bob freshness list -f json`, schema 3, `freshness.interval: 7`, lane intervals 1, no budget.

| Population | Count | Notes |
| ---: | ---: | --- |
| Walk | 150 | NEW 4 + PENDING 60 + NEXT 33 + RETURNED 1 + ROTTEN 52 |
| In-scope Ready split | 166 | 109 FRESH + 4 NEW + 52 ROTTEN + 1 RESURFACED |
| Dash Ready (`status.type is TODO`) | 177 | includes recurring / exempt |
| Refreshed today | 7 | 4 of them upkeep (outside the lanes) |
| `[refresh::]` in the walk | **0** | every Ready-due row is `interval_source: config` (7) |
| `task_refresh` on `gkeep_inbox.md` | **null** | the 2026-09-30 inbox-note override was never applied |

**All 52 rotten tasks are in `gkeep_inbox.md`.** They were created in 2026-09, seeded `[fresh:: 2026-09-25]`, and are 0 or 1 day overdue. They have not been human-kept since cutover. The rubber-stamp problem has not fired yet; the first real keep cycle is this week. sase.md dominates the *walk* (72 rows) because of daily lane review, not because it is rotting.

This is load-bearing:

- A naive Alt+F counter would be dominated by the 93 due lane rows, not by the 52 inbox ideas.
- Interval graduation is exactly what those 52 unrouted Keep ideas need, once they start being kept.
- There is no existing `[refresh::]` population to migrate.

## How the pieces actually work today

### Alt+F is a pure stamp

`bob-navigation-hotkeys` commands `refresh-task-freshness` (Alt+F) and `refresh-task-freshness-and-advance` (Alt+Shift+F) both call `refreshTaskFreshness`. The stamper is `api.freshness.stampLine(line, dateText)`. Counted `N<Alt+F>` and Task-Link targets share `planFreshStampBatch`. A same-day restamp on a canonical line is `changed: false`. Nothing else is written. There is no count, no log, no prompt.

### Many other gestures stamp, on purpose

`docs/freshness.md` §5: a supported human rewrite of an open task stamps as the last transformation of the line. Capture, cycler, Alt+N, Ctrl+Shift+P, Ctrl+Shift+M, and recommended roll/decay all stamp. Automation never does. **Only the pure keep should increment a keep streak. Every other stamp should reset it.** That is the Schedule-Log rule, translated to a field that cannot be derived.

### Placement is the correctness blocker, again

Obsidian Tasks and both Rust parsers read fields from the end of the line and stop at the first unknown key. `fresh` and `refresh` are therefore *scan-run extenders*, not Tasks keys: they sit immediately before the trailing Tasks suffix, and `stamp_fresh` / `stampLine` rebuild

```text
head [fresh:: D] [refresh:: N]?  <Tasks suffix, bytes untouched>
```

Any new field that is *not* in that extender set, if it ever lands at the end of the line, hides `created`, `priority`, `scheduled`, `id`, and `dependsOn`. The new field **must** join `fresh` / `refresh` in `tasks_suffix_start` / `freshnessTasksSuffixStart`, be removed and rebuilt by the same helper, and stay out of `TASKS_KEYS`.

Canonical output becomes:

```text
head [fresh:: D] [refresh:: N]? [keeps:: K]?  <Tasks suffix>
```

`K` is omitted when 0. Invalid values lint `keeps_invalid` and behave as 0. A `keeps` inside the Tasks suffix lints `fresh_misplaced` (same repair: the next stamp). Do not add `keeps` to the Tasks parser.

### The freshness mark is the display contract

Display-only, ledger-tools only, store absolute / show relative (`docs/freshness.md` §11). `[refresh:: N]` already folds into the same widget as `/{N}d` when it is the adjacent, valid, square-bracketed field. Leftover Dataview pills of `fresh` / `refresh` are flagged for repair. A second widget for a count would fight that contract. The count folds the same way `refresh` does.

### Priority decay is the UX analog, not the product analog

| | Priority decay | Rotten-keep decay (proposed) |
| --- | --- | --- |
| Signal | “not now” (avoidance) | “still right” (confirmation without change) |
| Gesture | `Ctrl+Enter` on `scheduled` | Alt+F / Alt+Shift+F on a due Ready task |
| Streak source | Schedule Log, derived, newest-first | `[keeps:: N]`, stored, because there is no sparse log |
| Reset | any non-roll reason | any non-keep stamp (picker, lane, capture, cycler, interval edit) |
| At threshold | previewed decay to next P-level | previewed lengthen to next interval preset |
| Past the last step | cancel (`🍂 decayed past P4`) | chooser: hide, cancel, or keep anyway — **do not silent-cancel** |
| Escape | re-pick the P-level or type a reason | “keep anyway” row, or Ctrl+Shift+P → refresh |
| Implicit P0 | no recommendation | works; interval does not need a P-level |
| Lane tasks | n/a | do not count; daily keep is the lane ritual |

## Requirement adjustments

**ADJ-1. Name the field `keeps`, not `refresh_count`.** Store `[keeps:: N]` immediately after `[refresh:: N]` (after `[fresh::]` when there is no task interval). Vocabulary: *keep* is the gesture, *refresh* is the interval, *stamp* is the write of `fresh`. If a Dataview-facing alias is wanted later, `keep_count` is the fallback; `refresh_count` collides with `refresh`.

**ADJ-2. Store a due-Ready keep *streak*, not a lifetime Alt+F total.** Increment only when all of these hold:

- the gesture is Alt+F or Alt+Shift+F (including counted and Task-Link forms of that command);
- the target is in-scope Ready (`[ ]`), evaluator state **ROTTEN**;
- `stampLine` would actually change the line (not already `fresh` = today).

Do **not** increment on: NEW first confirmation; Pending/Next daily keeps; RESURFACED (the ritual’s “not now” is a priority roll); FRESH early confirms; same-day no-ops; seed (already past); any §5 stamper other than this command.

**ADJ-3. Reset `keeps` to absent on every non-keep stamp.** `stampLine` (the current helper, used by capture, cycler, picker, Alt+N, roll/decay) clears it. `setRefreshLine` clears it (choosing 14/30/90 *is* the graduation, taken early). A keep of a non-ROTTEN task preserves the existing value and does not increment. This is the Schedule-Log reset rule, with one field instead of a log.

**ADJ-4. Fold the streak into the existing freshness mark. Do not add a second icon.** See [Mark](#mark). Dataview pills of `keeps` while marks are on are repair flags, same as leftover `fresh` / `refresh`.

**ADJ-5. Decay lengthens `[refresh::]`, it does not drop priority.** Ladder = the existing refresh-row presets that sit above the current interval: from 7, **14 → 30 → 90**. After 90, the chooser offers keep-anyway, `#hide`, or cancel — never a silent cancel. Reuse `setRefreshLine` so placement, stamping, and `/14d` on the mark all fall out. Do not invent a second interval field.

**ADJ-6. At threshold, Alt+F *is* the approval, the way `Ctrl+Enter` is.** Do not keep Alt+F as a silent stamp once `keeps >= rolls` and then hope a Notice gets read. Open a tiny suggester whose default row is the next interval. Enter (or a second Alt+F) accepts, writes `refresh`, stamps, clears `keeps`. A “keep anyway” row stamps and clears `keeps` without lengthening. Esc writes nothing (the task stays due; `]s` can skip). Alt+Shift+F after accept jumps as it does today.

**ADJ-7. Default `rolls: 3`, intercept off until the freshness trial is scored.** Three weekly keeps ≈ a month of “this is still a weekly item” before offering 14d. `rolls: 1` is a prompt every rotten keep; too heavy. `rolls: 0` would mean “every keep graduates,” which is the Anki-Good extreme — config-legal, not the default. Do not enable intercept between 2026-10-05 and 2026-10-18 (`docs/freshness.md` §13 keep rule: red on no more than 3 mornings, ~30 confirmed tasks, no lost-needed-task). Counting during the trial is useful data; changing Alt+F’s meaning would confound it.

**ADJ-8. Counted `N<Alt+F>` increments, and at threshold it must not silently keep the whole batch.** Phase A (intercept off): counted sessions increment each ROTTEN target independently. Phase B: if any target is at threshold, the Notice/suggester previews the mix (`4 tasks · 2 keep · 2 → 14d`), one guarded write, same as counted `Ctrl+Enter` roll/decay (`4 tasks · 2 roll · 1 decay · 1 cancel`). Recurring cancel already refuses a mixed batch; we do not need that here because lengthen never cancels.

**ADJ-9. Adjacent, not this feature: set `task_refresh` on `gkeep_inbox.md`.** The 2026-09-30 research recommended a short note interval on inbox notes so a tired Refresh cannot snooze an unrouted idea for a week. It is still unset; 52/52 rotten live there on the 7-day default. A note-level 2 or 3 would shrink that pile without any new field. Call it out in rollout; do not block `keeps` on it.

## Mark

One widget, one lifecycle, no new color except the due capsule already used.

Anatomy today: `[glyph][label][/{N}d?]`. Add `[pips]` when `keeps >= 1` and the mark’s tone is `due` or `today` on an in-scope Ready task. Hide pips on `resting` and on lane rows.

Default `rolls: 3`:

| `keeps` | Pips | Reading |
| ---: | --- | --- |
| absent / 0 | (none) | ordinary lease |
| 1 | ●○○ | one rotten keep toward graduation |
| 2 | ●●○ | one keep left |
| ≥ 3 (at threshold) | ●●● | next Alt+F offers 14d (or the next step) |

Pips use `currentColor`, 0.8em, same tabular family. Unfilled pips are the existing track opacity (0.26). At threshold the due capsule is already orange; do not add a second loud color. Tooltip gains one line, `due` tone only: `Kept 3 times · next Alt+F offers 14d`. Never put `::` in the tooltip (existing rule).

When `rolls > 5` or `keeps` is shown with intercept off and has grown past a handful, fall back to a tabular `×N` instead of an unbounded pip row. With intercept on and resets working, `N` stays in `1..rolls`.

After a graduation, `[refresh:: 14]` folds in as `/14d` (source `task`). The mark *looks* different: that is the beauty payoff. A lifetime `×47` numeral next to every task would be noise.

Click / cursor still reveals the raw `[keeps:: N]` for editing, same as `fresh`. The mark never writes.

## Recommended solution

Two phases, one contract. Phase A is enough to start tracking. Phase B is the decay you described, with the meaning of Alt+F changing only after the trial.

### Phase A — streak + mark (build now)

**Contract (`docs/freshness.md`).**

- New optional field `[keeps:: N]`, integer ≥ 1, omitted at 0, canonical position after `refresh`.
- Extender keys: `fresh`, `refresh`, `keeps`.
- `stamp_fresh` / `stampLine`: rebuild as today, **clear `keeps`** (reset). Backward compatible: every current caller is a non-keep stamp.
- New `keepLine(line, dateText, { increment })` (Rust `keep_fresh`): stamp today; if `increment` and the line was not already today, set `keeps` to old+1 (old default 0); if not `increment`, preserve existing `keeps`.
- Nav Alt+F / Alt+Shift+F call `keepLine` with `increment` iff the pre-stamp evaluator state is Ready ROTTEN. Other plugins keep calling `stampLine`.
- Lints: `keeps_invalid`, and `fresh_misplaced` when `keeps` sits in the Tasks suffix.
- JSON: bump freshness schema to 4; queue rows gain `keeps: number | null`. `api.freshness` namespace v5 adds `keepLine` / `readKeeps`. Config may already parse `freshness.keep_decay` (see Phase B) with `enabled: false`.
- No vault migration. Absent means 0. Seed is never re-run.

**Mark.** Fold `keeps` the way `refresh` is folded (adjacent, square-bracketed, valid). Pips as above. Repair-flag leftover `keeps` pills in Live Preview.

**Tests.** Placement vectors P-keep-1..n next to P1–P18 (preserve, increment, clear, omit-at-0, suffix-safe, counted batch). Mark vectors M-keep-* for pips, fold, tooltip. Nav: Alt+F on ROTTEN increments; Alt+F on NEW / FRESH / `[/]` / `[*]` does not; Ctrl+Shift+P priority row clears; same-day restamp does not increment.

**What Bryan sees.** A rotten inbox task kept once shows `⟳ 8d` plus one filled pip. Kept twice, two pips. Nothing else in the ritual changes. The walk, the dash, READY gating, and Alt+F latency stay as they are.

### Phase B — interval graduation (after the trial, or behind `enabled: false`)

```yaml
freshness:
  interval: 7
  keep_decay:
    enabled: false   # flip after 2026-10-18, once Phase A has real streaks
    rolls: 3         # consecutive ROTTEN keeps at the current interval
    # next step is the smallest refresh-row preset strictly greater than
    # the current effective Ready interval: 14, 30, 90
    # after 90: no further interval; chooser offers keep-anyway / hide / cancel
```

`enabled: false` / absent: Alt+F always keeps; pips still fill; `keeps` may grow past `rolls` (display `×N`). That is Phase A.

`enabled: true`, `keeps >= rolls`, gesture is a pure keep of Ready ROTTEN:

1. Do not stamp immediately.
2. Open a one-step suggester (the refresh-row value stage is the existing UI; pin the recommended next preset as the selected row, labeled `14d · kept 3 times`). Extra rows: `keep anyway`, and at the last step `hide` / `cancel`.
3. Accept → `setRefreshLine(next)` (stamps, writes `[refresh::]`, **clears keeps** because `setRefreshLine` goes through `stamp_inner`). Hide/cancel reuse the existing picker rows. Keep-anyway → `keepLine(..., { increment: false })` after clearing keeps (a reset, then a stamp).
4. Alt+Shift+F then jumps from the walk anchor, as today.
5. Esc: no write.

A decay does not count as a keep at the new interval (same as “a decay is not the first roll at the new level”). The next ROTTEN keep at 14d starts `keeps` at 1.

Config invalid values: lint, fall back to intercept off. `rolls: 0` means every ROTTEN keep opens the chooser. `keep_decay: false` is the off switch, mirroring `decay: false` on priority.

**Do not** graduate lane intervals. Lane cadence stays `pending_interval` / `next_interval`. A `[refresh:: 14]` on a Next task is already “once Ready” (`describeRefreshRow`: `every 1 d (next lane) · 14 d once Ready`). Graduation writes that Ready return value; the daily lane walk is unchanged.

### What this does not do

- It does not auto-defer, auto-cancel, or auto-`#hide`.
- It does not change NEW, RETURNED, or lane walk order.
- It does not put `keeps` into dash chips or `bob freshness` human rows in v1 (JSON is enough; human list can grow a `kept 3` suffix later if the tally is useful in the terminal).
- It does not backfill streaks from git history or from `(today - created) / interval`. Seeded age is not a keep.

### Implementation map

| Layer | Change |
| --- | --- |
| `docs/freshness.md` | fields table, placement rebuild, who-stamps (keep vs reset), mark anatomy, new vectors, schema 4, `keep_decay` config |
| bob-cli `placement.rs` | extender key, `keep_fresh`, clear-on-`stamp_fresh`, vectors |
| bob-cli `state.rs` / `cli.rs` | plumb `keeps` into JSON rows |
| bob-cli `config/freshness.rs` | parse `keep_decay` (enabled/rolls); unknown keys still ignored |
| ledger-tools `api.freshness` v5 | `keepLine`, `readKeeps`, mark fold + pips, repair CSS includes `keeps` |
| nav | Alt+F / Alt+Shift+F / counted / links call `keepLine` with ROTTEN increment; Phase B suggester |
| cycler, block-id-prompt, capture | no call-site change (`stampLine` resets) |
| vault | none at cutover; optional `task_refresh` on `gkeep_inbox.md` (ADJ-9) |

Two implementations stay in lockstep under the new vectors, same as `fresh` / `refresh`.

### Why this is the beautiful version

The freshness mark already tells a three-beat story: confirmed today, lease draining, due. Pips add a fourth beat *inside* “due”: how many times this exact lease has been renewed without the task changing. Graduation writes `[refresh:: 14]`, the mark grows `/14d`, the pips empty, and the task quietly leaves the weekly pile. No second icon, no child log, no machine tag, no surprise P-drop. Alt+F stays one key until the mark is full; then it asks, once, with a default you can accept with the same chord.

That is the same grammar as priority decay, pointed at the signal Alt+F actually produces.

## Critique summary

| Request | Verdict |
| --- | --- |
| Track explicit Alt+F refreshes | **Yes**, as a ROTTEN-Ready streak |
| Property named `refresh_count` | **No** — `keeps` (ADJ-1) |
| Lifetime increment on every Alt+F | **No** — due-Ready only, reset on other stamps (ADJ-2, ADJ-3) |
| Render like `fresh` | **Yes** — fold into the existing mark, pips not a second widget (ADJ-4) |
| Later auto-decay, user-approved at decay time | **Yes** — Alt+F becomes the approval; default action is lengthen interval (ADJ-5, ADJ-6) |
| Same mechanism as repeat priority rolls | **UX analog only.** Product is interval graduation, not P-level decay |
| Count lane daily keeps | **No** — would decay Next/Pending in three days |
| Enable decay immediately | **No** — Phase A during the 2026-10-05 trial, Phase B after (ADJ-7) |

Build Phase A. Leave Phase B wired in config and off. Revisit intercept once the freshness trial’s keep rule has a score, and once a week of real `keeps` values exists to look at.
