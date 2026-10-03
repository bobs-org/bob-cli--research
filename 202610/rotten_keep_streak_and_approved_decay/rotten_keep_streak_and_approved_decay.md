# Counting Alt+F keeps and asking, once, what to do about them

> **Research query:** Should I start tracking every explicit refresh of an Obsidian task
> (its `fresh` property updated with the Alt+F keymap) in a new `refresh_count` property,
> rendered as an icon like `fresh`, to enable a future user-approved auto-decay for tasks
> that keep getting manually refreshed, the way repeated priority rolls already decay?
> Critique the plan, call out any justified requirement changes, and recommend an
> intuitive, reliable, and beautiful design.

![Infographic "When keep becomes a decision": 176 of 177 Ready tasks are implicit P0; a keeps streak counts Alt+F keeps on due Ready tasks, shows as faint dots in the freshness mark and a leaf when a choice is due, and after 3 keeps a decision card (Not now, Less often, Reword, Drop, Keep) feeds the existing priority ladder](rotten_keep_streak_and_approved_decay_infographic.png)

## Bottom line

**Yes, build it. Change what the number means, and decide where the decay leads, before
writing any code.** Bob decays every "not now" gesture: priority rolls step down
P1 → P4 → cancel. Alt+F ("still right") is the only review answer that has no
consequence, however often you give it. A counter on Alt+F closes that loophole.

A fact none of the five reports put at the centre changes how the decay should work.
**`docs/projects.md` defines a task with no priority field as "implicit P0, the highest
priority: do it now, with no rolled date."** On 2026-10-03, **176 of the 177 open,
visible Ready tasks have no priority field** ([census](#live-vault-census)). In practice
the Ready backlog is a pile of tasks whose stored priority says "do it now". A task you
keep confirming and never start disproves that claim. So the keep streak is the missing
top rung of the existing ladder: **keeps are to P0 what rolls are to P1–P4.** When the
keeps run out, the task enters the ladder you already have. You don't need a second decay
system.

My recommendation, with the requirement changes
[called out below](#requirement-adjustments):

1. **Store a keep streak, not a lifetime total** (`[keeps:: N]`; the name is a soft
   change). Alt+F or Alt+Shift+F on a Ready task that the walk lists as **due** (ROTTEN or
   RETURNED) adds one. Any other Alt+F leaves the count alone. **Every other stamp clears
   it**, because every other stamping gesture is a decision. See the
   [counting rule](#counting-rule).
2. **Fold it into the existing [freshness mark](#display) as faint pips** (`◔ 3d ••`).
   Don't add a second icon. At the decision point the due capsule's `⟳` becomes a leaf
   (`🍂 8d •••`).
3. **Approval happens in a [decision card](#the-decay-decision-card), at the moment of
   decay.** When a due task has used its keeps (default 3), Alt+F opens a small card
   instead of stamping. The card is the review-outcome menu from `docs/freshness.md` §6,
   shown at the one moment it matters:
   - **↵ Not now** (recommended): P0 enters the ladder (P0 → P2 by default), with the
     rolled date previewed.
   - **L Less often**: review every 14 days instead of 7.
   - **E Reword**: start the count over.
   - **D Drop**: cancel, with a 🍂 entry in the Cancel Log.
   - **⌥F Keep**: still right; the card asks again at the next review.
   - **Esc** writes nothing. **↵ never closes a task.**
4. **Ship counting and pips first; the card comes second.**
   [The arithmetic](#rollout-and-the-trial) makes the first card impossible before about
   2026-10-27, after the freshness trial ends on 2026-10-18.

## Is this a good idea

**Yes, and it's the right next step.**

- **It closes the only consequence-free answer.** The cheapest gesture in the walk is
  also the only one with no memory. The tiered-walk decision lists the rubber-stamp risk
  as a cost. The original freshness research put it plainly: "glancing at a task and
  pressing Refresh, without deciding whether it belongs to today, is a failed review."
  This counter is the feedback loop for that.
- **The existing ladder can't reach the backlog.** With 176 of 177 Ready tasks at P0,
  priority decay currently applies to about 0.6% of Ready.
- **The information can't be derived at read time.** `fresh` resets on each keep.
  `created` measures existence, not neglect (gkeep sets it from Keep capture time). A
  stored event count is the only cheap, line-local, sync-safe source. It is history, not
  classification, so it doesn't reopen the "classification stays read-time" rule.

### Where the request as written goes wrong

1. **"Every time" mixes four different events.** Alt+F means first triage on NEW, a
   daily lane keep on Pending/Next, an early confirm on a still-FRESH task (including
   "edit, then Alt+F"), and the due-Ready rubber stamp you want to catch. A lifetime
   total of all four would be dominated by daily lane keeps. A sase.md Next task would
   reach any threshold in three days, which the sticky-lanes decision forbids.
2. **A total never forgets.** A task you rewrote, committed, worked, or re-prioritized
   last week would still carry its old count, and the decay would fire on the wrong
   tasks. Priority decay works because its streak resets on every deliberate decision.
   This needs the same rule.
3. **A standalone icon "like fresh" would be a second widget for the same concept** (the
   review lease) on lines that are already dense.
4. **`refresh_count` reads as "how many times the interval was set."** In this system
   `refresh` already means the interval, the picker row, `setRefreshLine`, and
   `task_refresh`.

### The strongest objection

From cdx: a count may measure conscientiousness rather than neglect. A diligent reviewer
piles up keeps, while someone who ignores review piles up nothing.
[The design below](#design) answers this three ways:

- It counts only keeps that the walk asked for. Ignored tasks stay ROTTEN and out of
  READY, which is already their penalty.
- The consequence is a question, not a penalty.
- The default answer is reversible (a deferral returns as RETURNED).

Even so, "kept 3×" is evidence about urgency, not value. The card copy must say
"kept 3 reviews in a row", never "no progress".

## Requirement adjustments

Each change to the request as written is called out here.

| # | You asked for | I recommend | Why |
| --- | --- | --- | --- |
| **A1** | Track **every** explicit refresh | A **keep streak**: consecutive bare due-Ready keeps since the last decision. | The decay has to react to current behaviour. This mirrors "only reasonless same-level rolls build a streak; any deliberate decision resets it". |
| **A2** | Every Alt+F counts | +1 only when the pre-write queue lists the target **exactly** (path + line + raw text) as lane `ready`, tier `rotten` or `returned`. Otherwise Alt+F just stamps and leaves the count alone ([counting rule](#counting-rule)). | NEW is a baseline, not a repeat. Lane keeps run daily and the sticky-lanes decision forbids lane decay. Same-day and off-cycle presses weren't asked for. Exact matching is the mark's own "truthful or neutral" rule. |
| **A3** | Property `refresh_count` | **`[keeps:: N]`** | Avoids the `[refresh:: 14] [refresh_count:: 3]` misreading, it's half the length, and "keep" is already the gesture word. Soft: say the word and nothing else changes. |
| **A4** | Its own icon, like `fresh` | **Pips folded into the freshness mark**, plus a leaf glyph at the decision point ([display](#display)). | One mark per concept. "Loud only when actionable." |
| **A5** | Future auto-decay (unspecified) | **Proposed automatically, applied only on an explicit choice in a card** ([decision card](#the-decay-decision-card)), feeding the **existing** priority ladder. P0 enters at the first level whose shortest window outlasts the review interval (P2 at 7 days). | One ladder, one config shape, one log vocabulary, one 🍂 ending. Deferral is what actually shrinks READY and CROWDED. A longer interval leaves the false "do it now" in place. |
| **A6** | (implicit) Every Alt+F surface | Counted `N<Alt+F>` and Task Link sessions count below-limit targets and **skip** at-limit ones (`1 needs a decision`). | Decisions happen one task at a time, and a batch can never bypass one. Skipped targets stay due, so `]s` returns to them. |
| **A7** | (implicit) Lanes | **Out of scope.** Lane keeps neither count nor clear. A commit (Alt+N) clears as a normal stamp. | `task-lanes-are-sticky`. |
| **A8** | (implicit) A lifetime history | Not stored. Each decision writes a dated Schedule Log or Cancel Log entry carrying `kept N×`. Vault git history covers offline analysis. | A lifetime total has no decision value and adds line clutter. A scalar on a git-synced vault isn't an exact global count anyway (cdx). |

## What exists today

Every fact in this section was verified; the last column gives the evidence.

| Fact | Why it matters | Evidence |
| --- | --- | --- |
| `[fresh:: D]` is the last human confirmation and `[refresh:: N]` is the per-task review interval. Both sit just before the Tasks suffix and are rebuilt by one helper per language (`stamp_fresh` / `set_refresh`; `api.freshness.stampLine` / `setRefreshLine`). | A new field must join that run of fields, or it hides Tasks fields from both parsers. `refresh_count` would sit right next to `refresh`, a different concept. | `docs/freshness.md` §§2–3 |
| Many gestures stamp: Alt+F/Alt+Shift+F ("their only change"), Alt+N, every Ctrl+Shift+P row, Ctrl+Shift+M, Ctrl+Enter roll/decay, the cycler, block-id-prompt, capture `plan_task_link` and `=x`→`[/]`. Automation never stamps. | Alt+F is the only *pure* keep. Every other stamp comes from a decision or from work. | `docs/freshness.md` §5 |
| The ritual already lists one-key review outcomes: still right (Alt+F), see it less often (refresh 14/30/90), not now (priority roll), do today, route, drop, wording wrong (edit, then Alt+F). | The decay card doesn't need new outcomes. It needs to surface these at the right moment. | `docs/freshness.md` §6 |
| Implicit P0 is "the highest priority: do it now". The picker has no P0 row. Picking P2 writes `🎲 P0 → P2 · in **12** (8–30) days`. "There is no recommendation for implicit P0." | P0 is on the ladder. It just has no recommendation. The keep streak supplies one. | `docs/projects.md` "Priority", "Recommended roll and priority decay" |
| The roll streak is derived from the Schedule Log. Bare same-level rolls (including ↵ on the pinned roll row) count, and any deliberate decision resets the streak. The classifier reads only the head before the first ` · `. | This gives the reset and keep-anyway semantics to copy. A trailing `· kept 3×` segment can't disturb classification. | `docs/projects.md`; nav `classifyScheduleLogRollReason` (~L2470) |
| Alt+F reads `queueBefore` (rows carry `tier`, `lane`, `originalMarkdown`) **before** writing. Today it applies one stamper to every target (`planFreshStampBatch`, ~L30126) and only uses the queue afterwards for the notice and walk anchor. `matchFreshStampRefs` (~L30222) accepts a **line-number-only** match. | Deciding per target whether a keep counts is feasible, but needs a small refactor. Counting must require an exact path + line + raw match, because a line-only match under Tasks-cache lag could credit the wrong task. | nav `refreshTaskFreshnessOnTasks` (~L32835) |
| The freshness mark is `[glyph][label][interval?]` with tones `today`/`aging`/`due`/`resting`. Principles: "loud only when actionable", "truthful or neutral". An adjacent `[refresh::]` folds in as `/14d`, and leftover pills get a dashed repair border. | The count belongs inside this widget, under the same folding and repair rules. | `docs/freshness.md` §11; ledger-tools `freshnessMarkModel` (~L5860) |
| "Keep" is already the gesture word: lane tooltips and notices say `Alt+F keep · Alt+N release · Ctrl+Shift+Enter today`. | Supports naming the field `keeps`. | ledger-tools ~L5988; nav ~L30054 |
| Decisions: sticky lanes reject "age-based Next decay — only if the trial fails, never for Pending". The tiered walk keeps tiers out of buckets and chips. The Ready cap rejects auto-defer ("the fix stays split, sequence, defer, or drop by hand"). Gated READY says "stamps remain the only write". | No lane counting, no new tier or chip, and every consequence goes through an explicit choice. The stored field needs a new decision record that amends "stamps remain the only write". | `decisions:task-lanes-are-sticky`, `review-walk-is-tiered`, `note-ready-cap-counts-the-lane`, `ready-is-freshness-gated` |
| Trial 2026-10-05 → 10-18: "Don't change the ritual mid-trial." | Counting can go live during the trial because no gesture changes. The card cannot. | `docs/freshness.md` §13 |

### Live vault census

Live vault, 2026-10-03 (my census plus `bob freshness list -f json`, schema 3):

| Measure | Value |
| --- | --- |
| Open, non-hidden `[ ] #task` lines outside `_templates`, `_conflicts`, and daily notes | 177 (11 recurring) |
| …with no `priority` field (implicit P0) / `high` | **176** / 1 |
| …with `[refresh:: N]` | 0 (every Ready interval is the 7-day config default) |
| `fresh` stamp dates | spread evenly 2026-09-25 → 10-01 (15–26 per day, the seed stagger); 15 unstamped |
| Walk queue | 150: 4 NEW, 60 PENDING, 33 NEXT, 1 RETURNED, 52 ROTTEN |
| ROTTEN by note | **all 52 in `gkeep_inbox.md`**, none kept by a human yet |
| Existing `keeps` / `kept` / `refresh_count` / `refreshes` fields | none |

Ready review runs at about 166 ÷ 7 ≈ **24 Ready reviews per day** in steady state. A naive
counter would mostly see the 93 lane rows that come due every day. The rubber-stamp
problem has not fired yet: the first real keep cycle happens this week.

## Design

### Counting rule

The whole contract in three lines:

> **`keeps`** = how many reviews in a row the walk asked "still right?" about this Ready
> task and you answered only with Alt+F. Absent means 0.

- **+1:** Alt+F / Alt+Shift+F (single, counted, or Task Link) on a target the pre-write
  queue lists exactly as Ready with tier `rotten` or `returned`, and keeps below the limit.
  The count goes in the same single-line write as the stamp.
- **Unchanged:**
  - Alt+F on NEW (the first confirmation is the baseline), on not-yet-due Ready, on lane
    rows, on out-of-scope rows, or on any target the queue can't match exactly. In every
    one of these cases the press stamps without counting.
  - A same-day repeat. It's no longer due, so it's uncounted and the stamp is a no-op.
  - Done or cancel. Closing doesn't stamp, so the count stays on the closed line as
    history.
  - Automation, hooks, `randomize`, seed.
- **Cleared:** every other stamp: Alt+N, every Ctrl+Shift+P row (including the refresh
  interval row and the decay card's own writes), Ctrl+Shift+M, Ctrl+Enter roll/decay,
  cycler open-status writes and reopen, Ctrl+Shift+Enter / `^^`, and capture
  `plan_task_link` / `=x`→`[/]`.

**Implementation shape.**

- **Clearing:** `stampLine` / `stamp_fresh` / `setRefreshLine` / `set_refresh` drop
  `keeps`. task-status-cycler, block-id-prompt, nav's other gestures, and Rust capture
  get correct reset behaviour **with no caller changes**.
- **Counting:** one new pure helper, `api.freshness.keepLine(line, dateText, { counted })`
  (freshness namespace v5), is the only code that ever increments. It also refuses to
  count without a prior `fresh`.
- **Nav:** computes `counted` per target from `queueBefore` before planning. This needs a
  per-target stamper in `planFreshStampBatch`, and the exact match is
  `entry.path === path ∧ entry.line === line + 1 ∧ entry.originalMarkdown === raw`.

**Failure is always an under-count.** An old ledger-tools, a lagging cache, or a lost
sync can only keep or drop the count. A missed keep postpones a decision by one lease.
This is the freshness contract's own "a missing stamp only means you see the task once
more".

### Storage and placement

```text
- [ ] #task Rename queue input [fresh:: 2026-10-08] [keeps:: 2] [created:: 2026-09-12] ^rq
- [ ] #task Learn Rust macros [fresh:: 2026-10-08] [refresh:: 14] [keeps:: 1] [priority:: low]
```

- **Field:** `[keeps:: N]` with N an integer from 1 to 999. `0` is never written; absent
  means 0. No vault migration and no backfill (seeded ages are not keeps).
- **Canonical order:** `head [fresh:: D] [refresh:: N]? [keeps:: K]? <Tasks suffix>`.
  `keeps` becomes a **run-extending, non-suffix key** in both scanners (Rust
  `suffix_start_inner` / `remove_fields`; JS `freshnessTasksSuffixStart` /
  `freshnessRemoveFields`). It must never be added to the Tasks key set. Because it sits
  left of every Tasks field, no Tasks field is ever hidden (`docs/freshness.md` §3
  invariance).
- **Reader and lints:**
  - `read_freshness` / `readFreshness` return `keeps` (the first valid value).
  - `keeps_invalid` covers non-integers, 0, and values over 999. These read as 0, and the
    next keep or stamp normalizes them.
  - `keeps_duplicate`.
  - `fresh_misplaced` now also covers a `keeps` inside the Tasks suffix (the next write
    repairs it).
- **Version skew is cosmetic, not lossy.** cdx's probe showed that today's helper treats
  an unknown field as part of the head and moves `fresh`/`refresh` to its right. A
  pre-v5 writer would therefore turn the field into a repair pill without losing data.
  Ship Rust and ledger-tools together. Nav needs `api.freshness.version >= 5` for
  `keepLine` and otherwise falls back to `stampLine` (an uncounted stamp).
- **Recurring tasks** are refused as they are today, so the count can never be copied
  into the next occurrence.
- **Dataview** parses `keeps` as a number, so `TASK WHERE keeps >= 3` works.

### The decay decision card

**Trigger.** Alt+F (or Alt+Shift+F in the walk) on a single due Ready task with
`keeps ≥ freshness.decay.keeps` (default 3), with decay enabled. **Nothing is written
yet.** The card is built on the Ctrl+Shift+P picker's modal, styles, preimage guard, and
undo, and it delegates every write to an existing writer.

```text
╭────────────────────────────────────────────────────────────────────╮
│ 🍂  Kept 3 reviews in a row                                        │
│     Rename queue input · gkeep_inbox.md · captured 6 weeks ago     │
├────────────────────────────────────────────────────────────────────┤
│ ↵   Not now      P0 → P2 · back in 17 days (8–30)      recommended │
│ L   Less often   review every 14 days instead of 7                 │
│ E   Reword       edit the task · start the count over              │
│ D   Drop         cancel · 🍂 dropped after 3 keeps                 │
│ ⌥F  Keep         still right · asks again next review              │
╰────────────────────────────────────────────────────────────────────╯
  Esc changes nothing · 1–4 pick a P-level instead
```

| Row | Writes (each through its **existing** writer) | Effect on `keeps` |
| --- | --- | --- |
| **↵ Not now** (preselected) | P0: a priority pick into the entry level with a rolled `scheduled`. Schedule Log: `🎲 P0 → P2 decay · in **17** (8–30) days · kept 3×`. Prioritized: exactly what `planPriorityRollRecommendation` returns, with the same trailing segment. **If the ladder's answer is cancel, ↵ shows a same-level roll instead. Cancel is only ever the D row.** | cleared (it's a stamp) |
| **L Less often** | `setRefreshLine` to the next refresh preset above the current interval (14 / 30 / 90) | cleared |
| **E Reword** | stamp + clear, then put the cursor at the end of the task text (the "wording wrong" outcome from `docs/freshness.md` §6, with the count reset) | cleared |
| **D Drop** | the existing cancel writer. Cancel Log: `🍂 dropped after 3 keeps` | kept on the closed line |
| **⌥F Keep** | `keepLine(counted)`: stamp, and the count goes 3 → 4 | grows; asks again at the next due review |
| **1–4** | a priority pick at that level (existing row semantics) | cleared |
| **Esc** | nothing; the task stays due and stays the walk anchor | unchanged |

**Why the recommendation is "Not now", not "Less often".**

- The evidence the card acts on is "kept three times, never pulled into Next". That
  contradicts the task's *urgency* (implicit P0, "do it now"), not its review cadence.
- Deferral corrects the false claim, and it takes the task out of READY and CROWDED
  until the date arrives (future `scheduled` ⇒ Blocked ⇒ RETURNED on return).
- The task then rides the existing roll ladder to its existing 🍂 ending.
- Lengthening the interval (grk, mus) leaves a "do it now" task sitting in READY and
  counting against the note cap, with a longer silence. It's the right answer for
  standing or slow-burn items, so it stays one key away.

**P0 entry level.** Defer into the first configured level whose `min_days` exceeds the
task's review interval: **P2** with defaults (interval 7; P1 = 2–7, P2 = 8–30), **P3**
for a `[refresh:: 30]` task. A shorter deferral would come back before the review it
replaces. Optional fixed override: `decay.enter: P1`.

**Why ⌥F Keep adds one instead of resetting.** This mirrors the ladder exactly: ↵ on the
pinned roll row is "explicit same-level roll; counts toward the streak". A bare repeat
keeps the pressure on, and a deliberate decision (L, E, any picker row) resets it. A
standing task you really want to keep should get a longer interval, not a weekly card.
Keep anyway also leaves a trace (`keeps > limit`) for calibration.

**Approval and safety rules.**

- Decay happens only on ↵ / L / D / 1–4 inside the card.
- Esc writes nothing.
- The card is announced before you press anything (see [Display](#display)).
- Key repeat is already filtered.
- ↵ never cancels.
- Single-note decisions are one editor transaction. Undo follows the picker's existing
  cross-note behaviour.

**Walk integration.**

- Alt+Shift+F resolves the card and then advances. Esc leaves the anchor where it was.
- The landing notice (`buildReviewJumpNotice`) adds `· kept 2×`. At the limit it adds a
  second line: `Kept 3× · Alt+F asks: not now · less often · reword · drop`.

**Batches** (counted, Task Link) never open the card. Ctrl+Shift+P → Ctrl+Enter on the
`scheduled` row of a P0 task at the limit offers the same `P0 → P2 decay` preview: one
shared planner, one answer. This is optional for the first card release.

**Not in v1:** a "Do today" row (needs block-id-prompt's API and an open Pomodoro; Esc →
Ctrl+Shift+Enter already works) and a "Route" row (Esc → Ctrl+Shift+M).

### Display

This section answers the request's "beautiful" goal.

**Mark anatomy:** `[glyph][label][interval?][keeps?]`. No new tone.

| State | Renders | Notes |
| --- | --- | --- |
| no keeps | `◔ 3d` | unchanged, and still most tasks |
| aging, 2 keeps | `◔ 3d ••` | pips in `--text-faint` |
| confirmed today, 2 keeps | `✓ today ••` | the check stays green; **pips never turn green** (no achievement styling) |
| due, 1 keep | `(⟳ 8d •)` orange capsule | pips inherit the orange at reduced opacity |
| **due, keeps ≥ limit, decay on** | `(🍂 8d •••)` | the **only new visual state**: lucide `leaf` in the 16-unit glyph box at the same 1.9 stroke, `data-decide="true"` |
| over the limit (kept anyway) | `(🍂 8d •••+1)` | pips cap at the limit (or at 3 when decay is off), then `+N` |

- **Pips:** filled dots only (≈0.34em, 0.14em gap, tabular baseline). Hollow "remaining"
  dots (grk) would put three marks on every task kept once. No red and no extra border
  (gem): the due capsule is already the one loud tone, and the leaf, a glyph change, also
  works for color-blind readers.
- **Tooltip:** one added line, and the key hint changes at the limit.

  ```text
  Confirmed Thu, Oct 1 · 7 days ago
  Due for review since Thu, Oct 8 · every 7 days
  Kept 3 reviews in a row · Bob asks at 3
  Alt+F to decide
  ```

  Below the limit the added line reads `Kept 2 reviews in a row · Bob asks at 3`, and
  the hint stays `Alt+F to confirm`.
- **Folding:** `keeps` folds when it is the only `keeps` field, square-bracketed, valid,
  and starts one space after the last folded field. Otherwise it stays a Dataview pill
  with the dashed repair border (extend the selector to `data-dv-norm-key="keeps"`).
  Rendered views (Tasks results on `dash.md`/`rotten.md`, reading view) fold the same
  way. Cursor or click reveals the raw field, and the mark never writes.
- **Notices:**
  - `Fresh ✓ 1 task · kept 2× · 21 due (3 new) · ✓ 13 today`
  - At the limit: `… · kept 3× — next review asks`
  - Batch: `Fresh ✓ 4 tasks · 1 needs a decision · …`
- **No dash chip, no tier, no `rotten.md` group.** Those were settled carefully, and the
  leaf on ROTTEN rows is enough. Revisit after a month of data.

### CLI and config

`bob freshness list`:

- **Human rows:** gain `kept 2×` and `· decide`, and the header gains
  `decides after 3 keeps`.
- **JSON (schema 3 → 4):**
  - Each row gains `keeps` (integer, 0 when absent) and `decide`
    (`keeps ≥ limit ∧ tier ∈ {rotten, returned} ∧ decay on`).
  - The payload gains `counts.decide` and `config.decay`.
- `decide` is an annotation, never a tier or bucket, so the partition and comparators
  are untouched.
- No new subcommand or option.

```yaml
freshness:
  interval: 7
  # Alt+F on a due Ready task adds one keep; any other stamp clears them.
  # Once a task has `keeps` keeps, its next due Alt+F asks instead:
  # not now / less often / reword / drop / keep. `decay: false` counts but never asks.
  decay:
    keeps: 3
    # enter: P2   # optional fixed P0 entry level (default: first level whose
    #             # min_days exceeds the task's review interval)
```

This mirrors the priority property's `decay: { rolls }` / `decay: false`. Absent, `true`,
or `{}` means enabled with 3. `keeps: 0` means every due re-confirmation asks. Invalid
values follow `docs/freshness.md` §2: `bob freshness` exits 2, and ledger-tools falls
back and marks the config `invalid`.

### Reliability checklist

- **One atomic line write per keep:** stamp and count together, through the existing
  editor transaction and the cross-note preimage guard.
- **Exact-match gate:** nav must not count on a line-number-only queue match. When a
  match is ambiguous or stale, the press stamps without counting.
- **Idempotent per day:** once stamped today the task isn't due, so it's never counted
  twice.
- **No Rust increment path.** Rust reads, lints, clears, and reports. Increments happen
  only in JS, behind one pure helper.
- **Conformance vectors** pinned in `docs/freshness.md` and used verbatim by both
  languages (sketch from cld, with my additions):
  - K1 first keep writes 1. K2 increments. K3 works alongside `refresh`.
  - K4: same-day is byte-identical.
  - K5: an uncounted keep preserves the count. K6–K7: `stamp_fresh` / `set_refresh`
    clear it.
  - K8: misplaced is repaired. K9: invalid becomes 0 + lint.
  - K10: NEW never counts. K11: recurring and closed are refused or preserved.
  - K12: Tasks fields are identical before and after.
  - **K13:** a stale-cache line-only match does not count.
  - MK vectors for pips, the leaf, and tooltips.
  - D vectors for the planner: P0 → P2 at 7 days, P0 → P3 at 30 days, P2 streak 1 → P2 →
    P3 decay, cancel replaced by a roll on ↵, and the `kept N×` segment classifying
    unchanged.
- **Sync:** a conflicting edit can lose an increment, which is an under-count, never a
  phantom count.
- **Mac Capture:** no grammar or contract change. Capture edits go through Rust
  `stamp_fresh`, which now clears, and that is correct because a capture edit is
  work or a decision. Verify that capture previews render `keeps` the way they render
  `fresh`.
- **Known limit:** hand edits aren't monitored. "Edit, then Alt+F" on a due task counts
  as a keep. The card's **E Reword** row is the cheap correction, and a false positive
  costs at most one early card.

## Rollout and the trial

- **Phase A, counting and display (can land now):**
  - The contract in `docs/freshness.md` (§§1–5, 7, 11, 12) and the Rust reader, lints,
    and clearing.
  - ledger-tools namespace v5 (`keepLine`, reader, folding, pips, tooltip, repair CSS).
  - Nav's per-target exact-match counting and the notices.
  - JSON schema 4.
  - Pips are a display-only change, so note them in the trial log. If you want a
    pristine trial, hold the pips (not the counting) until 2026-10-19.
- **Phase B, the card (after 2026-10-18, before about 10-24):** the
  [decision card](#the-decay-decision-card), the leaf, the walk notice line, batch skip,
  the `kept N×` Schedule/Cancel Log segments, the P0 entry rule in the shared planner,
  and optional Ctrl+Shift+P parity.
- **The arithmetic protects the trial.** A card needs three counted keeps a full lease
  apart and then a fourth due review. If counting starts 2026-10-06, the first card can
  appear about **2026-10-27**.
- **Expect a first wave.** The seed staggered the backlog across one week (15–26 stamps
  per day). Tasks that are only ever kept therefore reach their first card in the same
  week, up to about 24 a day in the worst case. Each card costs one key. Decayed tasks
  come back through **RETURNED, a commitment tier**, spread across 8–30 days. Watch the
  RETURNED count for two weeks after the wave. If it crowds the commitments, raise the
  entry level or `keeps`.
- **Phase C, calibrate after a month.** Use `counts.decide` and the decision log
  entries. If more than half of cards end in ⌥F Keep, raise `keeps` to 4. If most end in
  Drop, lower it to 2.
- **Memory (through `/sase_memory_write` when the plan lands):**
  - A new decision record, "Rotten keeps decay through the priority ladder": keeps is a
    stored streak, and decay is user-approved and enters the ladder. It amends the
    `ready-is-freshness-gated` clause "stamps remain the only write".
  - Glossary updates: the Task Freshness strand now says "never changes … schedule or
    priority", but the card's writes are picker writes. Add a *Keep streak* strand.
- **Adjacent, not blocking (grk):** `gkeep_inbox.md` holds all 52 ROTTEN tasks and has
  no `task_refresh`. A 2–3 day inbox interval would make unrouted ideas reach a decision
  sooner. That is a vault choice.

## Where the five reports agree and where I came down

| Question | cdx | cld | grk | mus | gem | **Resolution** |
| --- | --- | --- | --- | --- | --- | --- |
| Lifetime total or streak | lifetime + separate sparse REVIEW LOG for decay | streak | streak | streak-ish (resets on listed gestures) | streak-ish (inconsistent: writes from the 1st or the 2nd keep) | **Streak.** Four of five agree, and it follows the roll-streak rule. |
| What counts | every successful Alt+F, including lanes and same-day | due Ready (ROTTEN + RETURNED) | ROTTEN only | "due"; contradicts itself on lanes (D1 vs D8) | every Alt+F | **Due Ready: ROTTEN + RETURNED.** A RETURNED Alt+F is a bare keep where the ritual says to roll. |
| Reset mechanism | context fingerprint in the log | any non-keep stamp clears (inside `stampLine`, so no call-site changes) | same as cld | explicit list of resetting gestures | progress/reschedule list | **Clear inside the stamp helpers** (cld/grk). It covers every list the others wrote with no new call sites. |
| Name | `refresh_count` | `keeps` | `keeps` | `refresh_count` | `refresh_count` | **`keeps`** (soft; the design is identical under either name). |
| Display | history glyph + numeral beside the mark | faint pips folded in; leaf at the threshold | pips with hollow "remaining" dots | `×N` affix from N ≥ 2 | `· N×` badge that turns red at the threshold | **Filled faint pips + leaf** (cld). No red, no hollow dots, no second widget. |
| Default decay action | none (Keep is the default) | priority ladder; P0 enters at P2 | lengthen the interval 7→14→30→90 | lengthen the interval | priority if prioritized, else interval backoff | **Priority ladder, with P0 entering it.** "Less often" stays a row. See [the decision card](#the-decay-decision-card). |
| Approval gesture | card with Keep preselected | card with ↵ = recommendation, Alt+F = keep anyway | suggester; ↵ or a second Alt+F takes the recommendation | picker row | Alt+F executes the decay; Ctrl+Z undoes | **Card: ↵ = recommendation, ⌥F = keep, Esc = nothing.** |
| Batches | a review sheet | skip at-limit targets ("1 needs a decision") | preview the mix | — | — | **Skip** (cld): simplest and impossible to bypass. |
| Trial | observe first | counting OK; the arithmetic guards the card | Phase A now, intercept after | Phase 1 instrument | 4 phases | **Counting now, card after 10-18.** |

### Specific corrections

- gem's "unprioritized" track and grk's "implicit P0 can't enter the ladder" both misread
  P0. It is the top rung, and a priority pick already writes `P0 → P2`.
- cdx's advice not to "invent a ladder" for no-priority tasks has the same root.
- gem's "Alt+F executes the decay, undo with Ctrl+Z" is notification, not approval.
- cdx's Keep-preselected card turns the card into a two-key rubber stamp.

## Alternatives considered

| Alternative | Verdict | Why |
| --- | --- | --- |
| Lifetime `refresh_count` on every Alt+F (as requested) | Rejected | Dominated by lanes, never forgets, can't drive a fair decay. cdx agrees it can't drive decay directly. |
| Lifetime count + sparse dated REVIEW LOG for decay evidence (cdx) | Strongest alternative; rejected for v1 | It can audit and fingerprint rewording, but it adds structural multi-line writes to a one-key gesture, makes the mark read child blocks, and needs a new log grammar. Decision-time log entries already give an audit trail. Revisit if hand-edit false positives prove common. |
| Interval graduation as the default decay (grk, mus) | Kept as the **L** row | Leaves the false "do it now" in READY and in the note cap. A second ladder (7→14→30→90→?) would need its own terminal. |
| Dual track: priority demotion if prioritized, interval backoff if "unprioritized" (gem) | Rejected | Built on a misreading of P0. Two decay products for one signal. |
| Alt+F silently executes the decay; Ctrl+Z undoes (gem) | Rejected | That is notification, not approval at the time of decay. |
| Card with Keep preselected (cdx) | Rejected | The card becomes a two-key rubber stamp. Safety comes from ↵ never cancelling and every outcome being reversible. |
| Standalone icon or history glyph + numeral beside the mark (request, cdx) | Rejected | A second widget for one concept on dense lines. |
| Count lane keeps / decay Next | Deferred | Reopens `task-lanes-are-sticky`. |
| Store outside the vault, infer from git history, or proxy from `created` | Rejected | Invisible to Rust and mobile, fragile at render time, or measures existence rather than neglect. |
| New DECIDE tier, dash chip, or `rotten.md` group | Deferred | Tiers and chips are settled; data first. |

## Open questions for Bryan

1. **Name:** `keeps` (recommended) or `refresh_count`?
2. **Limit:** is 3 right (about a month of weekly keeps before the card)?
3. **P0 entry:** the interval-aware rule (→ P2 at 7 days) or a fixed `enter: P1`?
4. **⌥F Keep:** +1 and ask again next review (recommended, mirrors pinned rolls), or
   reset and ask again after 3 more?
5. **Trial:** pips during 10-05 → 10-18, or counting silently until 10-19?
6. **Lifetime total:** confirm you don't need one. A keep streak plus decision-time log
   entries replace it.

## Recommended solution

Build a **keep streak with a user-approved decision card that feeds the existing
priority ladder**:

1. **Field:** `[keeps:: N]`, placed after `fresh`/`refresh` and before the Tasks suffix,
   absent at 0, linted when invalid, never written by automation
   ([storage and placement](#storage-and-placement)).
2. **Counting** ([counting rule](#counting-rule)):
   - Alt+F / Alt+Shift+F on a task the pre-write queue lists **exactly** as due Ready
     (ROTTEN or RETURNED) adds one, at most once a day. Any other Alt+F leaves the count
     alone.
   - Every other stamp clears it. Make `stampLine` / `stamp_fresh` / `setRefreshLine` /
     `set_refresh` drop `keeps`, and add one `api.freshness.keepLine` (namespace v5)
     used only by Alt+F.
3. **Decay:** at `freshness.decay.keeps` (default 3), the next due Alt+F opens a
   [card](#the-decay-decision-card) instead of stamping:
   - **↵ Not now**: P0 → P2 (the first level whose window outlasts the interval).
     Prioritized tasks take their normal ladder step, but a roll replaces cancel. Logged
     as `🎲 … decay · in **N** (…) days · kept 3×`.
   - **L** Less often. **E** Reword. **D** Drop (`🍂 dropped after 3 keeps`).
   - **⌥F** Keep (+1, asks again next review). **Esc** writes nothing.
   - Batches skip decision targets.
4. **Display:** faint filled pips inside the freshness mark (`◔ 3d ••`), never green or
   red. At the decision point the due capsule's `⟳` becomes a leaf (`🍂 8d •••`). Add
   one tooltip line, a walk-notice line, and `keeps`/`decide` in `bob freshness list`
   (JSON schema 4). See [Display](#display) and [CLI and config](#cli-and-config).
5. **Scope limits:** no lane counting, no new tier or chip, no lifetime total, no silent
   decay. ↵ never closes a task.
6. **Rollout** ([rollout and the trial](#rollout-and-the-trial)):
   - Counting and display first, in one epic: contract + Rust, then ledger-tools v5,
     then nav.
   - The card after the 2026-10-18 trial ends; it can't fire before about 10-27.
   - Write the decision record and glossary updates through `/sase_memory_write`.
   - Recalibrate `keeps` after a month.

This keeps Alt+F a one-key gesture for every honest keep. It asks once, at the moment a
"do it now" claim has been disproved three times, with the same grammar Bob already uses
for rolls. It shows all of this as two quiet dots and, when it matters, a leaf.

## Sources

_Lead synthesis · 2026-10-03 · merges the cdx, cld, grk, mus, and gem reports plus my own
checks against bob-cli `6b64231`, bob-plugins `ac5419c` (navigation-hotkeys 1.66.0,
ledger-tools freshness namespace v4), the accepted decision records, and the live vault._

- **bob-cli `6b64231`:**
  - `docs/freshness.md` §§1–7, 11, 13.
  - `docs/projects.md`, "Priority" and "Recommended roll and priority decay".
- **Decision records (audited reads):** `task-lanes-are-sticky`, `review-walk-is-tiered`,
  `note-ready-cap-counts-the-lane`, `ready-is-freshness-gated`; glossary `Task Freshness`.
- **bob-plugins `ac5419c`, bob-navigation-hotkeys:**
  - `planFreshStampBatch` (~L30126), `matchFreshStampRefs` (~L30222).
  - `refreshTaskFreshnessOnTasks` / `refreshTaskFreshnessOnLinks` (~L32835–32990).
  - `classifyScheduleLogRollReason` / `countPriorityRollStreak` (~L2470–2520).
- **bob-plugins `ac5419c`, bob-ledger-tools:** `freshnessMarkModel` (~L5860), the lane
  keep tooltip (~L5988), freshness namespace v4 (~L7887), `styles.css` mark and repair
  rules.
- **Live vault 2026-10-03:** `bob freshness list -f json` (schema 3) and a read-only
  census of open task lines.
- **Swarm reports in this directory:** `__cdx` (lifetime count + review log; placement
  probe; consent and batch reliability), `__cld` (keep streak, P0 ladder entry, pips and
  leaf, trial arithmetic), `__grk` (streak, interval graduation, inbox interval), `__mus`
  (instrument-first phasing, lints), `__gem` (decay paradigms, mark CSS sketch).
