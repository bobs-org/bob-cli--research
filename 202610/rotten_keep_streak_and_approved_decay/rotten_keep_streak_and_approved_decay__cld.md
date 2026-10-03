# Counting Alt+F refreshes and decaying tasks that are only ever kept

*Researcher: cld · 2026-10-03 · scope: bob-cli, bob-plugins (ledger-tools, navigation-hotkeys), vault*

## TL;DR

**Yes, build it. It closes the one loophole in the decay system.** Every "not now" path in Bob
decays: priority rolls step down P1 → P4 → cancel. The one exception is Alt+F, "still right". A
task can be Alt+F'd every week forever and nothing ever pushes back. The vault data makes this
sharper than you might expect. **177 of the 178 open Ready tasks have no priority (implicit P0).**
So the existing decay ladder currently governs about 0.6% of the Ready backlog. The backlog that
most needs pruning sits entirely outside it.

I would change five things about the request as written (details in §3):

1. **Count a streak, not a lifetime total.** The number should mean "reviews in a row where you
   said *still right* and changed nothing else". Every real decision clears it.
2. **Only count the keeps the walk asked for.** That means Alt+F / Alt+Shift+F on a *due* Ready
   task (ROTTEN or RETURNED). NEW first-confirmations, lane keeps, same-day repeats, and off-cycle
   presses don't count.
3. **Name it `keeps`, not `refresh_count`.** `[refresh:: 14]` already means "review interval".
   `[refresh:: 14] [refresh_count:: 3]` reads as if the two are related, and the name is long on
   already-long lines. "Keep" is already the review vocabulary ("Alt+F keep"). This is a soft
   recommendation; the design works with either name.
4. **Render it inside the existing freshness mark, not as a second icon.** Keeps show as quiet
   pips after the age label (`◔ 3d ••`). At the decision point the mark's glyph becomes a leaf
   (🍂 is already Bob's "decayed" symbol).
5. **Make decay a user-approved decision card that feeds the existing priority ladder.** Don't
   build a second ladder. When a due task has used its keeps (default 3), Alt+F opens a small card
   instead of stamping. **↵ takes the recommended decay** (P0 enters the ladder at P2 by default;
   prioritized tasks get their normal ladder step). The other choices are *less often*, *drop*, and
   *keep anyway* (Alt+F again). Esc writes nothing.

The implementation is small and cheap to keep reliable:

- One inline field.
- One new JavaScript helper (`api.freshness.keepLine`).
- A one-line semantic change to the existing stamp helpers in both languages: any non-keep stamp
  clears `keeps`.
- A decision card that delegates every write to existing writers.

The rules are simple to state. **Alt+F either adds one or leaves the count alone. Every other
stamp clears it.** No other plugin or capture path needs code changes to get correct reset
behavior.

---

## 1. What exists today (grounding)

### 1.1 The freshness machinery

- `[fresh:: YYYY-MM-DD]` holds the last human confirmation. `[refresh:: N]` is the per-task review
  interval. The interval chain is task → note `task_refresh` → `freshness.interval` (7), or the
  lane interval (1) for walked Pending/Next tasks (`docs/freshness.md` §§1–2).
- **One placement helper per language.**
  - Rust: `stamp_fresh` / `set_refresh` in `src/native/freshness/placement.rs`.
  - JavaScript: `api.freshness.stampLine` / `setRefreshLine` in bob-ledger-tools
    (`freshnessStampLine`, `plugins/bob-ledger-tools/main.js` ~L4305). It is exported under
    freshness namespace v4 (~L7887).
  - The canonical form puts `fresh` and `refresh` immediately before the Tasks suffix (§3), so
    Tasks fields stay parseable.
- **Who stamps** (§5): Alt+F / Alt+Shift+F, *"their only change"*. All other stamping gestures
  rewrite something else about the task as well:
  - Alt+N commit/release.
  - Ctrl+Shift+P priority, scheduled, Depends-on, delete-property, lane, and refresh rows.
  - Ctrl+Shift+M moves and the Ctrl+Enter recommended roll/decay.
  - Alt+[ / Alt+] to an open status.
  - Ctrl+Shift+Enter / `^^` when they rewrite the line.
  - `bob capture` `plan_task_link` and the `=x` → `[/]` rows.

  Every one of these is a decision. Automation never stamps.
- **Alt+F** is `refreshTaskFreshness` in navigation-hotkeys (~L32742):
  - It handles the cursor task, counted `N` targets, and dedicated Task Links.
  - Before writing it reads `queueBefore` (the review queue with each entry's `tier` and `lane`) so
    it can compute the notice and the walk anchor (`matchFreshStampRefs`, ~L30222).
  - **So the plugin already knows at press time whether each target was due, and in which tier.**
- **The freshness mark** (§11; `freshnessMarkModel` / `buildFreshnessMarkElement`, ~L5860/L6037):
  - Anatomy: `[glyph][label][interval?]`.
  - Four tones: `today`, `aging`, `due`, `resting`.
  - Principles: "loud only when actionable"; "truthful or neutral".
  - An adjacent `[refresh:: N]` already folds into the mark. Leftover pills get a dashed orange
    repair border.

### 1.2 The priority decay ladder (`docs/projects.md`, "Recommended roll and priority decay")

- Ctrl+Shift+P → Ctrl+Enter on `scheduled` takes the recommendation: a same-level roll, a decay
  to the next level, or a cancel past the last level.
- **The streak is derived from the Schedule Log, never stored.** "Only reasonless, same-level
  recommended rolls build a streak; any deliberate scheduling decision resets it."
- The recommendation is user-approved at the time of decay: the row previews `🎲 P2 → P3 decay ·
  in 45 (31–90) days` before you press Ctrl+Enter.
- The planner is pure and reusable: `planPriorityRollRecommendation` (navigation-hotkeys ~L2619).
- **No recommendation exists for implicit P0.**

### 1.3 Live vault numbers (`bob freshness list -f json` and `bob query`, 2026-10-03)

| Measure | Value |
| --- | --- |
| Open Ready `[ ]` `#task` tasks (no `#hide`, `_templates`, `_conflicts`, daily notes) | 178 |
| …with a `priority` field | **1** (`high`); 177 are P0 |
| …with `[refresh:: N]` | 0 |
| …with `fresh` | 162 |
| In-scope Ready (`due` + `fresh`) | 57 + 109 = 166 |
| Walk queue | 150: 4 NEW, 60 PENDING, 33 NEXT, 1 RETURNED, 52 ROTTEN |
| ROTTEN `fresh` dates | all `2026-09-25` / `2026-09-26` (the cutover seed wave) |
| Interval sources in the queue | all `config` 7d for Ready |
| Existing `keeps` / `kept` / `refresh_count` / `refreshes` fields | none (no name collision) |

Steady-state Ready review load is about 166 ÷ 7 ≈ **24 Ready reviews a day**. That is the
population the counter observes.

---

## 2. Critique: is this a good idea?

### Why it is worth doing

1. **It closes the loophole.** Rolls decay and keeps don't, so the cheapest gesture is also the
   only one with no consequence. A one-key "still right" plus no memory is the exact shape of
   rubber-stamping. The tiered-walk research named rubber-stamping as a top risk
   (`research:202610/tiered_morning_review_walk`). This counter is its missing feedback loop.
2. **The existing ladder can't reach the backlog.** With 177/178 Ready tasks at P0, nothing in
   READY ever enters the priority ladder unless you pick a priority by hand. Keeps are the natural
   on-ramp.
3. **The information can't be derived at read time.** `fresh` resets on each keep, so age-since-
   confirmation hides chronic neglect. `created` measures existence, not neglect: an old task may
   have been worked, re-scoped, or deferred. A persisted event count is the only cheap,
   line-local, sync-safe source. It is history, like `fresh`, not classification, so it doesn't
   collide with the "classification stays a read-time evaluation" rule.

### Risks and how the design handles them

| Risk | Mitigation |
| --- | --- |
| **Lifetime counts punish living tasks.** A task you re-scoped last week still carries 9 old keeps. | Streak semantics: every decision clears it (A1). |
| **Inflation from noise**: double presses, counted batches, daily lane keeps, off-cycle presses. | Count only due Ready keeps; same-day repeats are idempotent (A2). |
| **Friction on the fastest gesture.** | The card appears only at the threshold. It is announced in advance by the mark (leaf glyph), the tooltip, and the walk notice. ↵ costs the same one key as Alt+F. |
| **Guilt / gamification.** Streak counters invite "don't break the streak" behavior in the wrong direction. | Neutral pips, never green, no flames or badges, no dash chip. The card copy is factual ("Kept 3× without a change"), not scolding. |
| **Line clutter / raw-view noise.** | Short field name; folded into the mark; absent at zero, which covers most tasks. |
| **Two-implementation burden** (Rust plus JavaScript). | Rust only clears and reads; increments are JavaScript-only. Conformance vectors are pinned in `docs/freshness.md` like P/S/M. |
| **Mid-trial ritual change** (trial 2026-10-05 → 10-18; "Don't change the ritual mid-trial"). | Arithmetic: a decision needs 3 keeps a full lease apart, so the first card can't appear until ≥ 21 days after counting starts, which is after the trial. Pips during the trial are display-only. |
| **No calibration data.** | Ship the counter early, because counting *is* the data collection. Tune `keeps` after the first month of decisions. |
| **"Stamps remain the only write"** (the `ready-is-freshness-gated` decision). | Amended, not violated: keeps is written in the same single-line write as the stamp. This needs a new decision record (see §7). |

### Would I take a different approach?

I'd keep your core idea, a persisted count driven by Alt+F, but change what it means and where it
leads. The alternatives I weighed are in §6. The two most tempting ones:

- **Derive the streak from a log**, like the priority streak. This means one child bullet per keep
  (`🔄 REVIEW LOG`). It would be self-auditing and dated. But it adds roughly 50 bullets a year per
  chronically kept task. It turns a one-line Alt+F into a multi-line structural write (riskier
  across Task Links). The mark would also need to read child blocks on every render. The inline
  count gets all the decision-relevant information. The decision itself writes a dated log entry
  (Schedule Log or Cancel Log) carrying `kept 3×`, so the audit trail exists at the moment that
  matters.
- **Auto-lengthen the interval on each keep**, spaced-repetition style (7 → 14 → 28 …). It is
  zero-friction, but it has no user approval, which contradicts your requirement. It also hides
  the symptom: the task stays in READY, counts against the per-note cap, and reads as "confirmed
  work" forever. I keep it as one *option* on the decision card ("less often").

---

## 3. Requirement adjustments (called out)

| # | Your requirement | Adjusted to | Why |
| --- | --- | --- | --- |
| **A1** | Track *every* explicit refresh. | Track a **keep streak**: consecutive bare keeps since the last decision. Any non-Alt+F stamp clears it. | Decay must react to *current* neglect. This mirrors the priority rule: "only reasonless same-level rolls build a streak; any deliberate decision resets it." |
| **A2** | Every Alt+F counts. | Alt+F counts **+1 only when the walk says the target is a due Ready task** (tier `rotten` or `returned`, lane `ready`) and `fresh < today`. Otherwise Alt+F just stamps and leaves the count **unchanged**. | NEW is first triage, not a repeat. Lane keeps run on a daily cadence, so 7 lane keeps ≠ 7 weekly keeps, and the sticky-lanes decision rejects lane decay. Same-day presses carry no new information. Off-cycle presses weren't asked for. |
| **A3** | Property named `refresh_count`. | **`[keeps:: N]`** (recommended). | It avoids confusion with the `[refresh:: N]` interval, is half the length, and matches the existing "keep" vocabulary. If you prefer `refresh_count`, nothing else in the design changes. |
| **A4** | Render as its own icon "like `fresh`". | **Fold it into the freshness mark** as pips. The glyph changes to a leaf at the decision point. | One mark per task for one concept (the review lease). A second widget doubles visual noise on dense task lines. |
| **A5** | Future auto-decay (unspecified). | **User-approved decision card on the Alt+F that would exceed the limit, feeding the existing priority ladder.** P0 enters at the first level whose shortest window outlasts the review interval (P2 at the 7d default). | One ladder, one config, one log vocabulary, one 🍂 ending. Deferral (not interval-lengthening) is what actually shrinks READY. |
| **A6** | (implicit) Applies everywhere Alt+F works. | Counted batches and Task Link sessions **skip** targets that need a decision (chip: `1 needs a decision`). They stay due, so the walk returns to them. | A decision must be made one task at a time and must never be bypassed by a batch. |
| **A7** | (implicit) Lanes. | Pending/Next are **out of scope**: lane keeps don't count. | `task-lanes-are-sticky` rejects "Age-based Next decay — only if the trial fails, never for Pending." Revisiting that is its own decision. |

---

## 4. Design

### 4.1 Semantics: what moves the count

> **`keeps`** = how many reviews in a row the walk asked "still right?" about this Ready task and
> you answered only with Alt+F. Absent means 0.

| Gesture | Effect on `keeps` |
| --- | --- |
| Alt+F / Alt+Shift+F on a target the pre-write queue lists with tier `rotten` or `returned` (lane `ready`), `fresh < today`, and keeps below the limit | **+1** (same write as the stamp) |
| Same, but keeps ≥ limit and decay enabled | **no write**: opens the decision card (§4.3) |
| Alt+F on a NEW task (no prior `fresh`) | unchanged (absent). First confirmation is the baseline. |
| Alt+F on a lane task (tier `pending`/`next`), a not-yet-due Ready task, a Blocked task, or a task not matched in the queue (stale cache) | unchanged (stamp only) |
| Alt+F twice the same day | unchanged (the stamp is already today: no churn, never a double count) |
| **Every other stamping gesture** (the whole §5 table) | **cleared** |
| Hooks, `randomize`, `projects sync`, `gkeep pull`, other automation | unchanged (automation never stamps) |
| Cancel / done | unchanged; the count stays on the closed line as history |
| Hand edit | not monitored. Ctrl+Shift+P → `keeps` → Ctrl+D clears it if you reworded the task. |

Two properties make this reliable:

- **The reset needs no new call sites.** task-status-cycler, block-id-prompt, nav's non-Alt+F
  gestures, and Rust `bob capture` all already route through `stampLine` / `stamp_fresh`. Making
  those helpers clear `keeps` gives every decision gesture correct reset behavior with zero
  caller changes. Only Alt+F switches to the new `keepLine`.
- **Failure is always an under-count.** Possible causes: ledger-tools too old, queue match failed
  because of Tasks-cache lag, or a sync conflict where "remote wins". In each case the count stays
  or drops. *A missed keep only postpones a decision by one lease.* This is the same "a missing
  stamp only means you see the task once more" principle the freshness contract already uses.

### 4.2 Storage and placement

- **Field:** `[keeps:: N]`, a positive integer 1–999. `0` is never written: absent means 0.
- **Canonical line:** `head [fresh:: D] [refresh:: N]? [keeps:: K]? suffix`. This extends the §3
  rule. `keeps` joins `fresh` / `refresh` as a run-extending (non-suffix) key in both scanners:
  Rust `suffix_start_inner`, and JavaScript `freshnessTasksSuffixStart` plus
  `freshnessRemoveFields`.
- **Why this is safe for Tasks:** both Rust parsers and Obsidian Tasks read trailing fields
  right-to-left and stop at the first unknown key. `keeps` sits *left* of every Tasks field, like
  `fresh` (vector P5's logic), so no Tasks field is ever hidden.
- **Reader:** `read_freshness` / `readFreshness` gain `keeps` (the first valid value) and lints:
  - `keeps_invalid`: non-integer, 0, or > 999. Treated as 0; the next keep or stamp normalizes it.
  - `keeps_duplicate`.
  - `fresh_misplaced` now also covers a `keeps` field inside the Tasks suffix (repaired on the
    next write).
- **Dataview:** `keeps` parses as a number, so ad-hoc queries work (`TASK WHERE keeps >= 3`).
- **Recurring tasks:** refused as today, so the count is never written there and never copied
  into the next occurrence.

### 4.3 Decay: the decision card

**Trigger.** You press Alt+F (or Alt+Shift+F in the walk) on a single due Ready task with
`keeps ≥ freshness.decay.keeps` (default 3). Nothing is written yet. A compact card opens, built
on the Ctrl+Shift+P picker's modal, styles, undo, and preimage machinery:

```text
╭──────────────────────────────────────────────────────────────────╮
│ 🍂  Kept 3× without a change                                     │
│     Rename queue input · bob.md · created 6 weeks ago            │
├──────────────────────────────────────────────────────────────────┤
│ ↵    Not now        P0 → P2 decay · in 17 (8–30) days   recommended
│ L    Less often     every 7 → 14 days                            │
│ D    Drop           cancel · 🍂 dropped after 3 keeps            │
│ ⌥F   Keep anyway    kept 4× · asks again next review             │
╰──────────────────────────────────────────────────────────────────╯
  Esc writes nothing · 1–4 pick a P-level instead
```

| Row | Writes (each through its *existing* writer) | Effect on keeps |
| --- | --- | --- |
| **↵ Not now** (preselected) | P0: a priority pick into the entry level (below) with a rolled `scheduled`. Prioritized tasks: exactly what `planPriorityRollRecommendation` returns (roll, decay, or cancel). Schedule Log reason gains a `kept N×` segment: `🎲 P0 → P2 decay · kept 3× · in **17** (8–30) days`. | cleared (it's a stamp) |
| **L Less often** | `setRefreshLine` with the next of 14 / 30 / 90 above the current interval (the existing refresh-row presets) | cleared |
| **D Drop** | the existing cancel writer; Cancel Log `🍂 dropped after 3 keeps` | kept on the closed line as history |
| **⌥F Keep anyway** (Alt+F again) | `keepLine(counted)`: stamp, keeps + 1 | 3 → 4; asks again at the next due review |
| **1–4** | priority pick at that level (existing row semantics) | cleared |

Design notes:

- **"User approved at the time of decay"** holds literally. Decay happens only on ↵ / L / D / 1–4
  inside the card. Esc cancels with no write, matching the picker's Esc semantics.
- **Pressing Alt+F twice to insist** is easy to remember and hard to do by accident: key repeat is
  already filtered (`event.repeat`), and the card is announced in advance.
- **The Schedule Log streak classifier is unaffected.** It splits on the first ` · `, so the head
  stays `P0 → P2 decay` (→ "decay", which stops the roll streak) or `P2 roll` (→ "roll", which
  counts). The `kept 3×` segment lives after the separator. Add a vector for it.
- **P0 entry level.** The rule is: *defer into the first configured level whose `min_days`
  exceeds the task's review interval.* With defaults (interval 7; P1 = 2–7, P2 = 8–30) that is
  **P2**. With `[refresh:: 30]` it is P3. The rationale:
  - A deferral shorter than the lease the task just burned returns before the next review would
    have, so it would be pointless.
  - About a month of bare keeps is evidence against "this week" (P1).
  - It spreads returns over 8–30 days instead of 2–7. Otherwise the first wave would flood the
    RETURNED *commitment* tier.

  The card shows the level, and 1–4 override it in one key. If you prefer a fixed rule, use
  `decay.enter: P1|P2|…`.
- **The same recommendation appears in Ctrl+Shift+P.** On a P0 task with `keeps ≥ limit`, the
  `scheduled` row gets the same `P0 → P2 decay` preview, so Ctrl+Shift+P → Ctrl+Enter is an
  equivalent route. This uses one shared planner and avoids two answers to one question.
- **Walk integration.** Alt+Shift+F resolves the card, then advances. The landing notice
  (`buildReviewJumpNotice`) adds `· kept 2×` to the detail. At the limit it adds a second line:
  `Kept 3× · Alt+F decides — not now · less often · drop`.
- **Batches** (counted `N<Alt+F>`, Task Link sessions) never open the card. They keep every target
  below the limit and skip the rest with a `1 needs a decision` chip. Those tasks stay due, so
  `]s` lands on them.
- **An optional "Do today" row** (Ctrl+Shift+Enter semantics) completes the GTD *do / defer /
  drop* set. I'd leave it out of v1: it needs block-id-prompt's API and an open Pomodoro, and Esc
  → Ctrl+Shift+Enter already works.

### 4.4 Display: "beautiful"

**Mark anatomy:** `[glyph][label][interval?][keeps?]`, with no new tone.

| State | Renders as | Notes |
| --- | --- | --- |
| aging, 0 keeps | `◔ 3d` | unchanged (most tasks) |
| aging, 2 keeps | `◔ 3d ••` | pips in `--text-faint` |
| confirmed today, 2 keeps | `✓ today ••` | check stays green; **pips stay faint, never green** (no achievement styling) |
| due, 1 keep | `(⟳ 8d •)` orange capsule | pips inherit the orange at reduced opacity |
| **due, keeps ≥ limit** | `(🍂 8d •••)` orange capsule, **leaf glyph** | `data-decide="true"`; the only new visual state |
| kept anyway (5, limit 3) | `(🍂 8d •••+2)` | pips cap at the limit, then `+N` |
| `decay: false` | `◔ 3d ×2` | no limit to show progress against, so a plain count |

- **Pips** are filled dots only (0.34em, 0.14em gap), with no hollow "remaining" dots. Hollow dots
  would put three marks on every task with one keep. Filled-only stays quiet, and the leaf already
  signals the threshold.
- **The leaf** is lucide `leaf`, scaled into the 16-unit glyph box with the same 1.9 stroke. It
  reuses 🍂, already Bob's "decayed" sign in Cancel Logs. Glyph and capsule both differ from
  `⟳`, so color-blind readability is preserved per §11.
- **Tooltip:** one new line before the key hint, and the key hint changes at the limit:

  ```text
  Confirmed Thu, Oct 1 · 7 days ago
  Due for review since Thu, Oct 8 · every 7 days
  Kept 3× without a change · decides at 3
  Alt+F to decide
  ```

  Below the limit the line reads `Kept 2× without a change · decides at 3` and the hint stays
  `Alt+F to confirm`. On a fresh task at the limit, line 2 reads `Next review Thu, Oct 15 · decides
  then`.
- **Folding:** keeps folds when it is the only `keeps` field, is square-bracketed, valid, and
  starts one space after the mark's last folded field (`fresh` or `refresh`). Otherwise it stays a
  Dataview pill, and the repair CSS (`[data-dv-norm-key="keeps"]`) gives it the dashed orange
  border. Rendered views (Tasks results on `dash.md` / `rotten.md`, reading view) fold it the same
  way.
- **Notices:**
  - `Fresh ✓ 1 task · kept 2× · 21 due (3 new) · ✓ 13 today`.
  - On reaching the limit: `Fresh ✓ 1 task · kept 3× — next review decides · …`.
  - Batch: `Fresh ✓ 4 tasks · 1 needs a decision · …`.
- **No dash chip, no new tier, no `rotten.md` group.** The chip list and walk tiers were settled
  carefully, and the leaf on ROTTEN rows is enough. Revisit after a month.

**CLI (`bob freshness list`)**:

```text
bob freshness · Thu 2026-10-29 · every 7d · pending 1d · next 1d · decides after 3 keeps

  REVIEW 61 due · 1 new · 9 pending · 14 next · 6 returned · 31 rotten · 4 decide · ✓ 12 today
  …
  ROTTEN 31
    a.md:2   Rename queue input   rotten 3d · fresh 2026-10-19 · every 7d · kept 2×
    c.md:9   Learn Rust macros    due today · fresh 2026-10-22 · every 7d · kept 3× · decide
```

JSON:

- Each row gains `keeps` (integer, 0 when absent) and `decide` (bool:
  `keeps ≥ limit ∧ tier ∈ {rotten, returned} ∧ decay enabled`).
- `counts.decide`.
- `config.decay` (`{ "keeps": 3 }` or `false`).
- `schema_version: 4`.

`decide` is an annotation, never a tier or a bucket, so the `B = NEW ∪ RETURNED ∪ ROTTEN ∪ READY`
partition and the tier comparators are untouched.

### 4.5 Config

```yaml
freshness:
  interval: 7
  pending_interval: 1
  next_interval: 1
  # Alt+F on a due Ready task adds one keep; any other stamp clears them.
  # After `keeps` keeps, the next due Alt+F asks for a decision instead
  # (not now / less often / drop / keep anyway). `decay: false` counts
  # keeps but never asks.
  decay:
    keeps: 3
    # enter: P2   # optional: fixed P0 entry level (default: first level
    #             # whose min_days exceeds the task's interval)
```

- This mirrors the priority property's `decay: { rolls: 1 }` / `decay: false` shape.
- `decay` absent, `true`, or `{}` means enabled with 3 keeps. `keeps: 0` means every due
  re-confirmation decides.
- Invalid values follow §2's existing rules: `bob freshness` exits 2; ledger-tools falls back and
  marks the config `invalid`.

### 4.6 Reliability checklist

- **One atomic line write** per keep. Stamp and count change together, through the existing
  editor transaction and cross-note preimage checks.
- **Idempotent per day**: `fresh == today` ⇒ no increment (vector K4).
- **The pure helper owns placement.** `keepLine(line, dateText, { counted })` is the only code that
  writes `keeps`. Nav decides `counted` from the queue match. The helper also refuses to increment
  without a prior `fresh` (defensive against NEW).
- **Version skew:** nav requires `api.freshness.version >= 5` for `keepLine`. Below that it falls
  back to `stampLine`, which never invents counts. All plugins deploy together via
  `bob plugins sync`.
- **Sync conflicts:** remote wins (vault-git-sync policy). A lost increment is an under-count.
- **Mac Capture:** no grammar or contract change. Capture's edits go through Rust `stamp_fresh`,
  which now clears keeps. That is correct, because a capture edit is a decision. One thing to
  verify during implementation: capture previews and Mac Capture renderings should treat `keeps`
  the way they treat `fresh`. I didn't confirm how previews render inline fields.

### 4.7 Contract and code changes (where)

| Area | Change |
| --- | --- |
| `docs/freshness.md` | §1 define *keep* / *keep streak*. §2 field + `decay` config. §3 placement + `keeps` in the run. §4 `decide` annotation. §5 "Who stamps" gains a keeps column (+1 / unchanged / clear). §6 add "decide" to the review outcomes. §7 CLI + schema 4. §11 mark anatomy, pips, leaf, tooltip. §12 vectors. |
| Rust | `placement.rs`: `keeps` in `suffix_start_inner` / `remove_fields`; `stamp_fresh` / `set_refresh` drop it; `read_freshness` reads it plus lints. `state.rs` / `cli.rs`: `keeps`, `decide`, `counts.decide`, header. `config/freshness.rs`: `decay`. No Rust increment path (no Rust surface keeps). |
| bob-ledger-tools | freshness namespace **v5**: `keepLine`; `stampLine` / `setRefreshLine` clear keeps; reader; mark fold + pips + leaf + tooltip; repair CSS; JavaScript vectors. |
| bob-navigation-hotkeys | Alt+F: per-target `counted` from `queueBefore`; notices; batch skip; decision card; P0 recommendation in the shared planner (also used by the `scheduled` row); landing-notice chip; `kept N×` Schedule Log segment; `keeps` property row (Ctrl+D). |
| task-status-cycler, block-id-prompt, `bob capture` | **No code change.** They inherit "clear on stamp" through the helpers. |
| `docs/projects.md` | Decay section: a second entry point (keeps → ladder) and the P0 entry-level rule. |
| Memory | New decision record. Glossary *Task Freshness* update plus a *Keep streak* strand. (Via `/sase_memory_write`; out of scope for this research.) |

### 4.8 Conformance vectors (sketch)

D = 2026-10-08, limit 3. "keep" means `keepLine(…, {counted: true})`.

- **K1 first keep:** `- [ ] #task Buy milk [fresh:: 2026-10-01] [created::2026-09-29]` →
  `… [fresh:: 2026-10-08] [keeps:: 1] [created::2026-09-29]`
- **K2 increment:** `[fresh:: 2026-10-01] [keeps:: 2]` → `[fresh:: 2026-10-08] [keeps:: 3]`
- **K3 with refresh:**
  `[fresh:: 2026-09-24] [refresh:: 14] [keeps:: 1] [priority:: low]` →
  `[fresh:: 2026-10-08] [refresh:: 14] [keeps:: 2] [priority:: low]`
- **K4 same day:** `[fresh:: 2026-10-08] [keeps:: 2]` → byte-identical, `changed: false`
- **K5 uncounted keep preserves:** `{counted: false}` on `[fresh:: 2026-10-05] [keeps:: 2]` →
  `[fresh:: 2026-10-08] [keeps:: 2]`
- **K6 stamp clears (both languages):** `stamp_fresh` on
  `[fresh:: 2026-10-01] [keeps:: 2] [created::2026-09-29]` →
  `[fresh:: 2026-10-08] [created::2026-09-29]`
- **K7 set_refresh clears:** `set_refresh(K2 input, 14)` → `[fresh:: 2026-10-08] [refresh:: 14]`
- **K8 misplaced:** `- [ ] #task A [created::2026-09-01] [keeps:: 2] [fresh:: 2026-10-01]` →
  `- [ ] #task A [fresh:: 2026-10-08] [keeps:: 3] [created::2026-09-01]` (input lints
  `fresh_misplaced`)
- **K9 invalid:** `[keeps:: two]` reads 0 + `keeps_invalid`. A keep writes `[keeps:: 1]` and drops
  the bad field.
- **K10 NEW never counts:** `- [ ] #task New` keep → `- [ ] #task New [fresh:: 2026-10-08]`
- **K11 refusals:** recurring is unchanged; closed is unchanged (keeps preserved on `[x]` / `[-]`).
- **K12 Tasks invariance:** for every K vector, both Rust parsers extract identical Tasks fields
  before and after (the §3 invariance rule).
- **MK1–MK7 marks:** the table in §4.4 as models (pips count, `data-decide`, glyph `leaf`, tooltip
  lines).
- **D1–D4 decision planner:**
  - D1: P0 at interval 7 → `P0 → P2`.
  - D2: P0 with `[refresh:: 30]` → `P0 → P3`.
  - D3: P2 with roll streak 1 → `P2 → P3 decay`.
  - D4: a `kept 3×` segment classifies as decay / roll exactly as without it.

---

## 5. Rollout and the trial

- **The arithmetic protects the trial.** With `keeps: 3` and every Ready interval at 7 days
  (0 overrides today), a decision needs a first counted keep at day *d*, then *d*+7, *d*+14, and a
  due review at *d*+21.
  - If counting ships 2026-10-06, the earliest card is about **2026-10-27**, after the trial ends
    2026-10-18.
  - Ship counting + display as early as convenient (that is the data collection). The card can
    land any time before ~10-24 without touching the trial ritual.
  - Pips appearing mid-trial is a small display change. Note it in the trial log; it doesn't change
    any gesture.
- **Expect a synchronized first wave.**
  - The cutover seed bin-packed the backlog into a 7-day cycle, so tasks that are only ever kept
    hit their first decision in the same week (~24/day at today's 166 in-scope Ready). In the
    worst case, where everything is kept, that is about 24 decisions a day for one week, starting
    ~4 weeks after counting begins.
  - Each decision costs the same single key as a keep (↵). The P2 windows (8–30 days) then spread
    returns out and **break the seed's weekly lockstep**, a useful side effect.
  - The seed's first human keep counts as 1. That is acceptable: the seeded backlog is the most
    suspect.
- **Calibrate after the first month.** Use `counts.decide` plus decision outcomes. Each decision
  writes a Schedule Log or Cancel Log line with `kept N×`, and keep-anyway leaves `keeps > limit`
  on the line.
  - If more than half of decisions end in *keep anyway*, raise `keeps` to 4.
  - If most end in *drop*, lower it to 2.

---

## 6. Alternatives considered

| Alternative | Verdict | Why |
| --- | --- | --- |
| Lifetime `refresh_count`, every Alt+F +1 (as requested) | Rejected | Punishes re-scoped or worked tasks; inflated by lanes, batches, off-cycle presses; can't drive a fair decay. |
| Streak derived from a dated `REVIEW LOG` child | Rejected | Structural multi-line writes, outline noise, mark must parse children. Decision-time log entries give the audit trail anyway. |
| Store counts outside the vault (plugin data, sidecar DB) | Rejected | Not visible to Rust or mobile; needs stable task identity (most tasks lack block IDs); splits the source of truth. |
| Derive neglect from vault git history | Rejected for runtime | Expensive and fragile at render time. Fine as an offline analysis later. |
| Proxy by `created` age | Rejected | `created` comes from Keep capture time; it measures existence, not neglect. |
| Automatic interval backoff (spaced repetition) | Rejected as primary; kept as the "less often" option | No approval; keeps READY bloated; never ends. |
| A separate interval ladder (7 → 14 → 30 → 90 → cancel) | Rejected | A second ladder, config, and vocabulary. About 420 days to drop, with the task in READY the whole time. |
| Decay by refusal notice + Ctrl+Shift+P (no card) | Close second | Cheaper, but less discoverable, and the picker is busy. The card is focused and reuses the picker's writers. |
| Count lane keeps / decay Next | Deferred | Reopens `task-lanes-are-sticky` ("Age-based Next decay … never for Pending"). Different cadence. Needs "worked since" detection. |
| New DECIDE tier, dash chip, or `rotten.md` group | Deferred | Tiers, chips, and the partition are settled. The leaf mark is enough until data says otherwise. |
| Per-note opt-out (`task_decay: false`) | v2 if needed | Standing reminders belong in recurring tasks or long intervals. Add it only if real notes need it. |

---

## 7. Open questions for you

1. **Name:** `keeps` (my recommendation) or your `refresh_count`?
2. **Limit:** is a default of 3 right (about 4 weekly confirmations without action ≈ one month)?
3. **P0 entry:** the interval-aware rule (→ P2 at 7d), or a fixed `enter: P1`?
4. **Card scope:** include "Do today" in v1?
5. **Decision record:** I'd record "Keeps are a stored streak of bare due keeps; decay is
   user-approved and routes through the priority ladder." It partly supersedes the
   `ready-is-freshness-gated` clause "stamps remain the only write". OK to write it when the plan
   lands?

---

## 8. Recommended solution

Ship a **keep streak with a user-approved decision point that feeds the existing priority
ladder**:

1. **Field:** `[keeps:: N]`, placed canonically after `fresh` / `refresh` and before the Tasks
   suffix. It is absent at 0, linted when invalid, and never written by automation.
2. **Counting rule (the whole thing in two lines):**
   - Alt+F / Alt+Shift+F on a task the walk lists as a due Ready task (ROTTEN or RETURNED) adds
     one, at most once a day. Any other Alt+F leaves the count unchanged.
   - Every other stamping gesture clears it. This is implemented by making `stampLine` /
     `stamp_fresh` / `setRefreshLine` drop `keeps`, plus one new `api.freshness.keepLine` used
     only by Alt+F (freshness namespace v5).
3. **Decay:** once `keeps` reaches `freshness.decay.keeps` (default 3), the next due Alt+F opens a
   decision card instead of stamping:
   - ↵ **Not now**: P0 enters the ladder at the first level whose window outlasts the review
     interval (P2 by default). Prioritized tasks take their normal roll / decay / cancel step,
     logged as `🎲 … · kept 3× · …`.
   - **L** Less often (14 / 30 / 90).
   - **D** Drop (`🍂 dropped after 3 keeps`).
   - **Alt+F** Keep anyway (count +1; asks again next review).
   - **Esc** writes nothing.

   Batches skip decision targets; the walk returns to them. Ctrl+Shift+P → Ctrl+Enter offers the
   same P0 recommendation.
4. **Display:**
   - Faint filled pips folded into the existing freshness mark (`◔ 3d ••`), never green.
   - At the decision point the orange `due` capsule swaps `⟳` for a 🍂 leaf (`🍂 8d •••`).
   - The tooltip says `Kept 3× without a change · decides at 3 / Alt+F to decide`.
   - The walk notice and `bob freshness list` (`kept 2×`, `decide`; JSON schema 4 with `keeps`,
     `decide`, `counts.decide`) say the same.
5. **Scope limits:** no lane counting, no new tier or chip, no stored dates, no automatic decay.
6. **Rollout:**
   - Land the contract (docs + Rust), then ledger-tools v5, then nav, in one epic. Counting can go
     live during the 2026-10-05 → 10-18 trial, since it changes no gesture.
   - The first card can't appear before ~2026-10-27.
   - Write the new decision record and the glossary updates through `/sase_memory_write`.
   - Recalibrate `keeps` after the first month of decisions.
