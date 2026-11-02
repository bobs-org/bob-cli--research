# Unified Task Decay: One Ladder From WIP To Dropped

_Researcher: cld · 2026-11-02 · scope: bob-cli, bob-plugins (bob-navigation-hotkeys,
bob-ledger-tools), chezmoi `bob/config.yml`, SASE memory_

## TL;DR

- **The screenshot bug is a plugin wiring bug, not a missing config.** The decay card
  reads `this.config` on the navigation plugin, but nothing ever assigns
  `plugin.config`. Only the picker modals get a config, and the plugins load it on each
  gesture. So `findFreshnessDecayPriorityProperty(undefined)` returns `null` on every
  install, and the card always says "no priority ladder is configured" and draws no
  1–4 rows. The handler tests hide this because they set `plugin.config = decayConfig()`
  by hand. I reproduced the screenshot's rows exactly in Node (§2).
- **Fixing the wiring alone would still offer P2, not P1.** The card's "Not now"
  chooses the first level whose `min_days` is greater than the review interval. With
  your new `interval: 3`, P1 (`min_days: 3`) fails that test, so it lands on P2. On an
  unprioritized task, the Task Card's `Ctrl+Enter` assigns P1. **Yes, always step Ready
  down to P1.** That makes the two gestures agree.
- **The plan is a good idea, and your review journal backs it up.** Over 22 review
  mornings, Next tasks were kept 88 times. Five Next rows were kept 11–12 times each.
  The vault has **zero** Next Rotten Log entries, because every Next reason was left
  blank and blank writes nothing. The Pending lane holds 17 tasks against a soft cap of
  8. Today, nothing gives a stuck WIP or Next task a reason to move.
- **Recommended design:** one *decay ladder*, Pending → Next → Ready → P1 → P2 → P3 →
  P4 → dropped.
  - A *stay* leaves a task on its rung. On a lane it is a due Alt+F keep, counted in
    `[keeps::]`. On a P-level it is either a keep or a same-level `Ctrl+Enter` roll,
    which keeps its own Schedule Log count.
  - Each rung allows two stays. After that, the default answer (Enter on the card, or
    Ctrl+Enter on the Task Card) moves the task one rung down.
  - Alt+F on the card means **Stay**. It writes a log entry and resets the count.
  - Enter never drops a task.
  - Every counted keep, Stay, and step writes one rung-qualified Rotten Log entry, with
    a default reason when you leave it blank.
- **Config:** extend the existing `freshness.decay.keeps` from one integer to a
  per-lane map (`pending`, `next`, `ready`, each a number or `false`). Also set the
  priority property's existing `decay.rolls: 2` explicitly. **Do not add the map to
  chezmoi until the parsers accept it.** Today a mapping value makes `bob freshness`
  exit 2 and ledger-tools fall back to defaults marked invalid (§5.6).
- **Adjustments to your requirements**, each flagged ⚠ in §4:
  - Early (not-yet-due) keeps neither count nor prompt.
  - `rolls: 2` changes today's effective default of one same-level roll.
  - The bottom rung (P4) never drops on Enter.
  - Today-linked WIP is not "rotten".
  - The log calls the `[/]` lane "Pending"; ask Bryan whether he prefers "WIP".
  - Rung changes made by automation must clear `[keeps::]` too.

---

## 1. What exists today

Bob has two decay mechanisms. They were built separately and count different things.

| | **Keep decay (freshness)** | **Roll decay (priority ladder)** |
|---|---|---|
| Gesture | Alt+F / Ctrl+Alt+F on a due task | `Ctrl+Enter` (recommended roll) on the Task Card |
| Counts | `[keeps:: N]` on the line: consecutive *due Ready* ROTTEN or TICKLER keeps | Same-level `🎲 P2 roll` entries, newest first, in the Schedule Log (derived, never stored) |
| Limit | `freshness.decay.keeps` (default **3**), Rust + ledger-tools | `decay.rolls` / `levels[].rolls` on the priority property (default **1**), navigation plugin only (Rust ignores these keys: `src/native/config/mod.rs::ignores_decay_and_rolls_keys`) |
| At the limit | Consent card: Not now (= the roll ladder's recommendation, or "P0 entry"), Less often, Reword, Drop, Keep, 1–4 | The recommendation changes from "roll P2" to "P2 → P3 decay", and past P4 to cancel |
| Lanes | Pending and Next never count (`decide` requires `lane == ready`, `src/native/freshness/state.rs::decide_for`) | n/a |
| Log | Counted Ready keeps → `🥀 ROTTEN LOG` `· kept N×`. Next keeps → `· kept in Next` only when a reason is typed. Pending → Work Log prompt, never the Rotten Log. | Schedule Log `🎲 …` entries, with `· kept N×` tails when the card wrote them |

These records and docs encode the current rules. Each claim below is something the new
design reverses, so it needs a superseding record (§8):

- `decisions:rotten-keeps-use-priority-decay`: limit 3; "Counting non-Ready lanes" is
  rejected; Keep *adds one* and asks again.
- `decisions:rotten-keeps-are-logged`: Pending never writes the Rotten Log; the card's
  dismissals never write a Rotten Log entry.
- `decisions:next-keeps-ask-an-optional-rotten-reason`: a blank Next reason writes no
  entry; Next keeps never count. Its own "Reopens when" says "…or Bryan wants Pending
  keeps in the Rotten Log too". That condition is now met.
- `decisions:task-lanes-are-sticky`: "Only release (Alt+N, or the Ctrl+Shift+P lane
  row) lowers Next or Pending". It rejects "Age-based Next decay… never for Pending".
- `docs/freshness.md` §2a and `docs/projects.md` "Approved-decay decision planner".

## 2. The screenshot bug: verified root causes

**Repro.** I loaded `plugins/bob-navigation-hotkeys/main.js` with Obsidian stubs,
constructed the plugin, and ran the real planner and row builder. The config was the
chezmoi `config.yml`, converted to JSON. The scratch script is
`/tmp/cld_scratch/repro.cjs`.

```text
plugin.config after construct: undefined
prototype members mentioning config: []

== production (this.config undefined)
  [Enter] Not now: no priority ladder is configured (unavailable)
  [L] Less often: review every 7 days instead of 3
  [E] Reword: edit the task · start the count over
  [D] Drop: cancel · dropped after 3 keeps
  [Alt+F] Keep: say why · logs 🥀 · asks again next review

== with Bryan's config loaded
  [Enter] Not now: P0 → P2 · back in 20 days (9–31)
  ...
  [1] P1: back in 6 days (3–8)   [2] P2 …   [3] P3 …   [4] P4 …
```

The first block matches the screenshot row for row.

### 2.1 Root cause A: the card never loads the config

- `530-plugin-freshness-refresh-and-decay.js` calls
  `findFreshnessDecayPriorityProperty(this.config)` at lines 157, 365, 558, and 589.
  These are the card build plus three revalidation and commit paths.
- `540-plugin-decay-picker-and-cancel.js:24` passes `this.config` into the Less-often
  picker.
- The only `this.config =` in the plugin is in `340-picker-core.js:9`, on
  `BulletPropertyPickerModal`. Every other gesture calls `loadBulletPropertyConfig()`
  on demand: `500-…:498`, `550-…:419`, `396-…:258`.
- `scripts/test-navigation-decision-card-handlers.cjs:299` sets
  `plugin.config = decayConfig();`, so the suite passes while production can never
  reach a priority row.

Two follow-on effects come from this:

- **Revalidation is also blind.** The commit-time check compares two `null`
  serializations, so a real ladder change would never be noticed.
- **The footer is wrong.** It always says "1–4 pick a P-level instead"
  (`060-decay-card-modal.js:59`), even when there are no level rows. That is the
  dangling promise visible in the screenshot.

### 2.2 Root cause B: the entry level is interval-aware and disagrees with Ctrl+Enter

- `resolveFreshnessDecayP0EntryLevel` (`040-priority-roll.js:906`) picks the first
  level with `min_days > interval`. Your cadence change today (chezmoi `3873ee30`,
  "Update freshness cadence", `interval: 3`) makes P1 (3–8) ineligible, so the answer
  is P2.
- `planPriorityRollRecommendation`'s P0 "assign" branch (`040-priority-roll.js:42`)
  uses `levels[0]`, which is P1.
- The same unprioritized task therefore gets P1 from the Task Card's `Ctrl+Enter` but
  P2 from the decay card.
- **Answer to "always use P1, right?": yes.** On a ladder, the next rung down from Ready
  is the first level. I recommend removing the interval scan and keeping
  `freshness.decay.enter` only as an optional override (it is unset in your config).

### 2.3 Likely root cause C (not verified in Obsidian): focus versus the Enter label

- The card focuses the **Keep** row when it opens (`focusKeepRowOrFirst`). The
  screenshot shows the purple focus ring on Keep.
- Each available row has its own `keydown` handler for Enter, which calls
  `stopPropagation()` and runs `choose(row.action)`.
- So with Keep focused, Enter should run **Keep**, even though the kbd chip and
  "recommended" badge put Enter on **Not now**. The content-level `Enter → notNow`
  handler never sees the event.
- Fix: focus the recommended row, so the focus ring, the kbd chip, and the Enter
  behaviour all agree. Check this in the vault before shipping.

## 3. Evidence: is this a good idea?

These figures come from a read-only census of `~/bob` and the review journal
(`~/bob/.bob/stats/review/*.jsonl`, 1,388 answers from 2026-10-12 to 2026-11-02, 22
review days).

| Signal | Value | Reading |
|---|---|---|
| Open lanes | Pending `[/]` **17** (cap `max_pending: 8`), Next `[*]` 7, Ready 52, Blocked 520 | WIP is over twice its soft cap; nothing pushes it down |
| NEXT-tier answers | **88 keep** / 49 today / 17 sequence / 8 defer / 7 done / 2 release / 1 drop | Keep is the most common Next answer (51%) |
| Keeps per NEXT row (journal key = file:line, approximate) | 13 rows kept ×1, … **5 rows kept ×11–12** | Rubber-stamping, the risk `review-walk-is-tiered` named |
| PENDING-tier answers | 97 done / 61 today / 23 keep / 5 defer | Most WIP moves; a few rows are kept 3–4× |
| Next Rotten Log entries in the vault | **0** | Every Next reason was blank, so nothing was logged |
| Counted Rotten Log entries | 4 (2 are `🤷`) | Little history to learn from yet |
| TICKLER answers | **415 defer** / 39 done / 24 drop / **5 keep** | P-level tasks "stay" by being re-rolled, not kept |

What this tells me:

1. **Lane decay addresses a real failure.** The sticky-lanes decision accepted "no
   automatic forgetting" and named its cost: a daily review with release, plus a weekly
   prune. In practice the journal shows only 2 lane-change answers (Alt+N) on NEXT rows
   in 22 days, against 88 keeps. A consented default step-down is the "forgetting" that
   sticky lanes lack, and it keeps Bryan in control.
2. **Always logging fixes a data hole.** Optional-blank logging produced nothing for
   Next. With a default entry, every keep leaves a trace.
3. **Priority rungs already decay by rolls.** Alt+F keeps on a resurfaced P-level task
   are rare (5 out of 498). The roll ladder (`rolls`) is the stay that matters on P1–P4.
   So "2 keeps per priority" in practice means `rolls: 2`.
4. **Expected load.** At current rates (Next ≈ 4 keeps/day, Pending ≈ 1/day) and an
   allowance of 2, about one in three keeps of a chronically kept task becomes a card.
   That is roughly 1–2 cards per morning at steady state. No lane task carries
   `[keeps::]` today, so lane counts start at 0 and the first cards appear on the third
   due review after rollout. Expect a one-time wave on days 3–6.

## 4. Critique: what I would keep, change, or flag

**Keep as asked:**

- Two keeps per lane.
- WIP → Next → Ready → P1 as the defaults.
- Ready decays at 2, not 3.
- Always log, with a default reason that names the rung and count.
- Pending keeps log to the Rotten Log instead of prompting for a Work Log.
- A "keep the status" option that resets the count.

**Risks to design around:**

1. **Muscle memory.** Below the limit, "Alt+F, Enter" means *keep with no reason*. At
   the limit the same keystrokes mean *step down*. The Ready card already works this
   way (Enter is "Not now"), but lanes make it a daily event. Mitigations:
   - The walk landing notice and the 🍂 mark announce the decision before the press.
   - Enter is ignored until the opening chord is released, or about 300 ms. The card
     already has a gesture lock.
   - Every step is one undo with a "Ctrl+Z undoes" notice.
   - Alt+F on the card means Stay, so "Alt+F, Alt+F, Enter" is the explicit
     keep-it-here path.
2. **"Swarm work needs a quiet place to wait"** (sticky lanes). WIP waiting on agents
   can legitimately sit in Pending. Stay with a reason ("epic sase-1qt running") resets
   the count. If that becomes a daily tax, `pending: 3` or `pending: false` is one line
   of config.
3. **Decision churn.** Five records change in part, so write one umbrella record (§8)
   rather than five amendments.
4. **Version skew across three codebases** (Rust, ledger-tools, navigation): gate lane
   cards on capability versions (§7).

**Adjustments I recommend. These depart from the literal request:**

| # | Adjustment | Why |
|---|---|---|
| ⚠ A1 | **Early (not-due) keeps do not count, prompt, or log.** They stamp quietly with an "early · not counted" notice. Only due keeps (walk landings and exact due rows) prompt and always log. Today Next prompts even for early keeps. | Every log line then carries a truthful `N×`, and every prompt means a counted decision. Counting needs an exact pre-write queue match to guard against Tasks-cache lag, and early rows are not in the queue. This also cuts down on mashing Enter. The alternative is to log early keeps as the existing uncounted `· kept in Next` form. |
| ⚠ A2 | **Priority levels count stays in two counters**: Alt+F keeps in `[keeps::]`, same-level rolls in the Schedule Log. Both are limited to 2. | The data shows P-level stays are rolls. The roll ladder already has a well-specified, self-healing Schedule-Log streak (15 conformance vectors). Folding rolls into `[keeps::]` is possible later (§6, option U2) but not needed now. |
| ⚠ A3 | **`rolls: 2` is a behaviour change.** Today each level grants 2 *windows*: entering, then 1 roll. "2 keeps per level" means 2 same-level rolls, so 3 windows. With your windows, a task that is rolled at every review goes from P1 to cancelled in about 1.8 years on average today, and about 2.7 years with `rolls: 2`. | You asked for 2 explicitly. Confirm you mean 2 rolls, not 2 windows. |
| ⚠ A4 | **At P4 the default never drops.** Enter re-defers at P4, as today's card substitutes, and **D Drop** is marked recommended. | This keeps the `rotten-keeps-use-priority-decay` invariant "Enter can defer but never cancels". |
| ⚠ A5 | **Today-linked WIP is outside decay.** Alt+F on a task linked under today's open Pomodoro stamps quietly. Task Link sessions stop asking for a Work summary. | You are working on that task today, so it is not rotting. The Work Log keeps its proper writers: Ctrl+Shift+Enter, Alt+N release, `=x`. |
| ⚠ A6 | **Any rung change clears `[keeps::]`, including automation.** Reconcile's `MarkNext`, `MarkInProgress`, and Unblock transitions must clear it. | Otherwise a Ready streak leaks into Next after a hand-made link. This amends "automation never touches keeps" (`task_status_hooks/model.rs` `Transition`). |
| ⚠ A7 | **The log names the lane "Pending"** (with WIP as an alias in the glossary). | It matches the dash chips, walk tier, successor picker, and R12. Your choice; it costs one string. |
| A8 | "WIP should be considered rotten" means *logged in the Rotten Log*, **not** moved to the ROTTEN tier. | Tiers and buckets stay structural (`review-walk-is-tiered`). |

## 5. Design

### 5.1 Vocabulary

- **Rung:** where a task sits on the ladder.
  - A `[/]` task's rung is **Pending**, and a `[*]` task's rung is **Next**.
  - A `[ ]` task with no priority sits on **Ready** (implicit P0).
  - A task with `[priority::]` that is Ready, or Blocked behind its rolled date, sits on
    its **P-level**.
  - Blocked is an overlay, never a rung. A Next task with a priority is on Next; when it
    steps down it lands on its P-level.
- **Stay:** an answer that leaves the task on its rung.
  - A **keep** is a due Alt+F, counted in `[keeps::]`.
  - A **roll** is a same-level recommended roll on a P-level, counted from the Schedule
    Log.
- **Allowance:** how many stays in a row a rung permits (Bryan: 2 everywhere).
- **Step:** move one rung down. **Stay** on the card: keep it here and restart the
  count.

| Rung | Stay gesture(s) | Default at the allowance | What a step writes |
|---|---|---|---|
| Pending `[/]` | due Alt+F | Enter → **Next** | `[/]`→`[*]`, stamp (clears keeps), Rotten Log step entry. New writer. |
| Next `[*]` | due Alt+F | Enter → **Ready** | `[*]`→`[ ]`, stamp, Rotten Log step entry. Reuses the Alt+N release plan; a due row has no live links. |
| Ready `[ ]` (P0) | due Alt+F | Enter → **P1** | `[priority:: high]` + roll in P1's window (existing assign writer). Schedule Log `🎲 P0 → P1 decay · in 5 (3–8) days · kept 2×`, Rotten Log step entry. |
| P1…P3 | due Alt+F, or Ctrl+Enter same-level roll | Enter (card) / Ctrl+Enter (Task Card) → **next P-level** | Existing decay writer + Schedule Log `🎲 P2 → P3 decay …` + Rotten Log step entry |
| P4 | as above | Enter re-defers at P4; **D Drop** recommended; `Ctrl+Enter` cancels past P4 (unchanged) | Drop: existing cancel writer + Cancel Log `🍂 dropped after 2 keeps at P4` + Rotten Log entry |

Nothing steps without a gesture. Freshness stamps alone never change a rung.

### 5.2 Counting rules

- A keep counts once per review when it is an exact due row on the pre-write queue for
  its rung:
  - Pending → tier `pending`
  - Next → tier `next`
  - Ready or P-level → tier `rotten` or `tickler`
- Unblock ticklers stay uncounted (`unblock_keeps`).
- Counting still goes through the single helper `api.freshness.keepLine(…, {counted:
  true})`.
- `[keeps:: N]` is cleared by: every rung change (human or automatic), Stay, Reword,
  Less often, an explicit level pick, and a typed reschedule. That covers today's
  generic-stamp rule plus A6.
- `decide = decay enabled for the rung && due && keeps ≥ allowance(rung)`. Rust and JS
  compute it identically. The JSON row exposes `rung` and `allowance`.
- Counted `N<Alt+F>` and Task Link sessions skip at-limit targets ("N need a
  decision"), now including lane targets. Decisions stay one task at a time.

### 5.3 The decay card, generalized and redesigned

The card stays a keyboard-first modal. It is titled for the rung, and the recommended
row gets focus.

```text
🍂  Kept 2× in Next
    Ship the release notes · sase.md · captured 3 weeks ago
    🥀 Pending 2 · Next 2 · last Nov 4 — waiting on Alice's review

 ↵      Move to Ready                       recommended
        Next → Ready · back in the walk in 3 days
 Alt+F  Stay in Next
        say why · logs 🥀 · count starts over
 E      Reword       edit the task · count starts over
 D      Drop         cancel · dropped after 2 keeps in Next
 1–4    Pick a level P1 back in 6 days · P2 back in 20 days · …

 Esc changes nothing · ↵ never drops
```

- **Header line 3:** per-rung lifetime tallies, derived at read time from the Rotten
  Log. This answers "how many times was it kept in each status". It is display-only,
  like the current "N keeps logged".
- **L (Less often):** appears only on Ready and P-levels. Lane cadence is lane-wide
  (`pending_interval` / `next_interval` override the per-task chain), so on lanes the
  row is hidden, not greyed out.
- **The footer** is built from the rows that exist. No "1–4" hint without level rows.
- **The Stay reason stage** reuses `RottenKeepReasonStage`, titled "Stay in Next?".
  Blank Enter logs `🤷 no reason given`; Esc returns to the choices.

### 5.4 Rotten Log grammar: a complete keep-and-decay timeline

Newest first, as today. Machine-written steps carry the 🍂 emoji, the same convention as
🎲 in the Schedule Log.

```markdown
- [ ] #task Ship the release notes [fresh:: 2026-11-08] ^notes
  - 🥀 **ROTTEN LOG**
    - *2026-11-08* — 🍂 Next → Ready · after 2 keeps
    - *2026-11-06* — 🤷 no reason given · kept 2× in Next
    - *2026-11-04* — waiting on Alice's review · kept 1× in Next
    - *2026-11-03* — 🍂 Pending → Next · after 2 keeps
    - *2026-11-02* — 🤷 no reason given · kept 2× in Pending
    - *2026-11-01* — still mid-refactor · kept 1× in Pending
```

| Entry | Grammar (tail after ` · `) |
|---|---|
| Counted keep | `<reason> · kept N× in Pending\|Next\|Ready` or `… kept N× at P1…P4` |
| Stay (reset) | `<reason> · stayed in Next after N keeps` |
| Step | `🍂 <From> → <To> · after N keeps` (rolls on the Task Card keep their Schedule Log entry only) |
| Drop | `🍂 <Rung> → dropped · after N keeps` (plus the existing Cancel Log line) |
| Legacy, still parsed | `<reason> · kept N×` (pre-ladder Ready) and `<reason> · kept in Next` (pre-ladder Next) |

Grammar changes touch two strict JavaScript regexes: navigation's `ROTTEN_LOG_ENTRY_RE`
(`010-requires-and-config.js:406`) and ledger-tools'
`135-freshness-rotten-log.js:13/290`. Rust only counts entries under the marker
(`note_snapshot/visibility.rs` `LogKind::Rotten`), so it needs no parser change. Its
reading-view "KEPT" rows should label step entries. "N keeps logged" counts keep and
Stay entries, not steps.

### 5.5 Prompts by surface

| Surface | Today | Proposed |
|---|---|---|
| Due Pending keep | Optional Work Log summary | "Keep in Pending?" reason → Rotten Log, blank → `🤷` |
| Due Next keep | Optional reason; blank writes nothing | Reason → Rotten Log, blank → `🤷`, counts |
| Due Ready / P keep | Reason, blank → `🤷`, counts | Same, rung-qualified tail |
| Early keep, any rung | Next prompts; others quiet | Quiet stamp, uncounted (A1) |
| Today-linked or Task Link session target | Work summary for Pending | Quiet stamp (A5) |
| Counted `N<Alt+F>` batch | Work summary, then Keep reason | One Keep reason for the counted targets; at-limit targets skipped |

### 5.6 Configuration

**Shape:** extend `freshness.decay`, which already exists with Rust and JS parsers and
JSON exposure.

- `keeps` accepts its legacy integer, meaning every lane, or a map
  `{pending, next, ready}`.
- Each value is an integer 0–999 or `false`. `false` means that lane never asks but
  still counts.
- The default for an absent key is **2**.
- `ready` covers every Ready-lane task, including prioritized ones.
- P-level rolls stay where the roll ladder is defined (the priority property's
  `decay.rolls`). There, set explicitly to 2, with code default 1 → 2.

I considered and rejected a new top-level `decay:` block and moving `rolls` into
`freshness:` (§6).

**chezmoi `home/dot_config/bob/config.yml`.** ⚠ Apply this **only after** the Rust and
ledger-tools parsers accept the map. Today a map value is a config error.

```yaml
freshness:
  interval: 3 # Ready backlog review cadence
  pending_interval: 1 # [/] lane daily review; false = not walked
  next_interval: 2 # [*] lane daily review; false = not walked
  project_interval: 1 # Bryan's ^prj review cadence (personal setting, not a built-in default)
  # rotten_daily_budget: 15 # counts upkeep outside the lanes; never hides tasks
  # Task decay (docs/freshness.md §2a): after `keeps` due Alt+F keeps in a row, the
  # next one opens the decay card. Enter moves the task one rung down (Pending →
  # Next → Ready → P1 → … → P4; never drops), Alt+F stays and restarts the count,
  # D drops. Every keep, stay, and move writes a 🥀 ROTTEN LOG entry.
  decay:
    keeps: # keeps in a row per lane; false = that lane never asks
      pending: 2 # [/] WIP → Next
      next: 2 # [*] Next → Ready
      ready: 2 # [ ] Ready → P1 (a prioritized task → its next P-level)
```

And on the priority property, replacing the commented `# decay: / rolls: 1` lines. This
key is valid today, so it can land first if you want the explicit value now:

```yaml
    # Ctrl+Enter on `scheduled` takes the recommended roll: `rolls` same-level rolls
    # per level (read from the Schedule Log), then the next roll decays one level
    # (P2 → P3); past the last level it cancels. Matches freshness.decay.keeps.
    decay:
      rolls: 2
```

Side note: this host's `~/.config/bob/config.yml` still has `interval: 7` /
`next_interval: 1`. The chezmoi source on origin has 3 / 2 (commit `3873ee30`), so
`chezmoi update` has not run here yet. The Mac already has the new values: the
screenshot shows "instead of 3".

### 5.7 Reliability and safety

- **One transaction per answer.** Each answer writes the line, its Rotten Log entry,
  and any Schedule or Cancel Log entry together, as one undo, with the existing
  preimage revalidation. Stale input writes nothing and rebuilds the card.
- **Enter guard and focus fix** (§4 risk 1, §2.3).
- **Mixed versions:**
  - New navigation with an old ledger: no lane `decide`, so lane keeps are uncounted
    but still log.
  - Old navigation with a new ledger: no 🍂 on lane rows unless
    `freshnessDecayCard.version ≥ 3`.
- **No backfill.** Legacy entries parse as they are; lane counts start at 0.

## 6. Options considered

| Question | Options | Recommendation |
|---|---|---|
| One counter or two on P-levels | **U1** two counters, both limited to 2 (A2) · **U2** fold same-level rolls into `[keeps::]` so Ctrl+Enter reads the same number. That needs the roll writer to increment instead of clear, retires the Schedule-Log streak, and rewrites the 15 vectors in `docs/projects.md`. | **U1 now.** Revisit U2 only if "2 keeps vs 2 rolls" confuses in practice. |
| Where the allowance lives | **C1** extend `freshness.decay.keeps` + explicit `rolls` · **C2** new top-level `decay:` block covering lanes and levels (new loader ×3, moves Task Card config) · **C3** move `rolls` into `freshness:` | **C1.** Smallest contract change; each knob sits next to the gesture it governs. |
| What the card's Alt+F does | **K1** Stay = reset to 0 (your request) · **K2** today's Keep = +1, asks again next review | **K1.** The Stay entry keeps the trace that K2's `keeps > limit` used for calibration, and it avoids a daily nag on a task you consciously kept. |
| Card default at a P-level | **D1** always step down (P2 → P3) · **D2** today's "recommended roll" (may be "roll at P2") | **D1.** Matches "after 2, default moves down". A same-level roll is still one key away via 1–4. |
| Early keeps | **E1** quiet, uncounted (A1) · **E2** prompt + uncounted `· kept in Next` | **E1** |

## 7. Implementation plan

Suggested as one epic with five phases. Phase 0 can ship today on its own.

**Phase 0: hotfix (bob-plugins, navigation; small)**

1. Replace `this.config` with a per-gesture `loadBulletPropertyConfig()` at all 5
   sites (`530` ×4, `540` ×1), or add one cached `getBulletPropertyConfig()` method
   that all of them use.
2. Make P0 entry `levels[0]`, honouring `enter` only when it is set
   (`resolveFreshnessDecayP0EntryLevel`).
3. Build the footer from the rows; focus the recommended row.
4. Tests:
   - Drop `plugin.config =` injection from `test-navigation-decision-card-handlers.cjs`.
   - Add a regression test that loads the config through the fs stub and asserts that
     Not now plus 4 level rows render.
5. Update the `docs/projects.md` "Not now" bullet. Then `npm run build`, `npm test`,
   and `bob plugins sync`.

**Phase 1: contract (bob-cli; medium)**

- `src/native/config/freshness.rs`: `decay.keeps` as an integer or map, with `false`
  per lane, default 2.
- `src/native/freshness/state.rs::decide_for`: lanes, `rung`, `allowance`.
- `src/native/freshness/cli.rs`: JSON schema 14 → 15 (`config.decay.keeps` becomes an
  object; rows gain `rung` and `allowance`). This is a contract break, so the commit
  gets `!` per `decisions:bob-cli-releases-ride-a-daily-train`. Human rows show
  `kept 2× in Next · decide`.
- `src/native/task_status_hooks/`: clear `[keeps::]` on MarkNext, MarkInProgress, and
  Unblock (A6).
- `tests/fixtures/freshness_keeps/vectors.json`: lane, map-config, and rung-change
  vectors.
- Docs: `docs/freshness.md` §§2/2a/7/10a/11, `docs/reference/vault-format.md` (Rotten
  Log grammar), `docs/develop/decisions.md`.

**Phase 2: ledger-tools mirror (small–medium)**

- `090-freshness-config.js` and `100-freshness-evaluate.js`: map config, lane `decide`,
  `rung`.
- `130` marks: pips and the 🍂 leaf on lane rows, gated on the card capability.
- `135-freshness-rotten-log.js`: new grammar plus per-rung tallies.
- Freshness namespace v12 → v13 with a `decayLadder` capability.

**Phase 3: navigation behaviour (large)**

- `195-rotten-keep.js`: lane counting in `classifyRottenKeepTarget`, rung-qualified
  `formatRottenLogEntryText`, always-log, rung titles.
- `197`: remove the Work-Log path from Alt+F.
- `520` / `532`: routing, lane card trigger, and lane batch skips.
- `050`: per-rung step planner plus the Stay action.
- `530`: commit adapters with the new Pending→Next writer, the release-based Next→Ready
  step, and step entries.
- `060`: rung copy, Enter guard, focus.
- `010`: `ROTTEN_LOG_ENTRY_RE`.
- Card capability v3.
- Tests: rotten-keep, rotten-log, decision-card×3, decay-planner, keep-counting.

**Phase 4: docs, memory, config (small)**

- Glossary and decision record (§8).
- Plugin docs: `bob-navigation-hotkeys.md`, `task-card.md`.
- The chezmoi edit (§5.6), then `chezmoi update -a --force` on each host.

## 8. Memory changes (route through `/sase_memory_write` when implementing)

**New glossary term, proposed text:**

> **Task Decay** (aka decay, decay ladder, step down)
>
> The rule that an open task cannot stay where it is indefinitely without an answer.
> Every in-scope open task sits on one rung of the decay ladder: Pending (`[/]`, WIP) →
> Next (`[*]`) → Ready (`[ ]`, implicit P0) → P1 → P2 → P3 → P4 → dropped. A Ready or
> Blocked task with a priority sits on its P-level. A *stay* leaves the task on its
> rung: a due Alt+F keep (the [[keep-streak]]) or, on a P-level, a same-level roll
> (counted from the [[schedule-log]]). Each lane allows `freshness.decay.keeps.<lane>`
> keeps and each P-level `rolls` rolls (Bryan: 2 and 2). At the allowance, the next due
> Alt+F opens the decay card: Enter moves the task one rung down, Alt+F stays and
> restarts the count, D drops, E rewords, 1–4 picks a level, and L (Ready and P-levels)
> reviews less often. `Ctrl+Enter`'s recommended roll follows the same ladder. Enter
> never drops, and nothing decays without a gesture. Every counted keep, stay, and move
> writes one [[rotten-log]] entry naming the rung and count (`kept 2× in Next`,
> `stayed in Next after 2 keeps`, `🍂 Next → Ready · after 2 keeps`); a blank reason
> logs `🤷 no reason given`. Freshness stamps never change a rung. Blocked is derived
> and never a rung. This is not `bob task reroll`, Ready-cap triage, or Zorg decay.

**Strands to update:**

- `glossary:keep-streak`: rung-scoped; lanes count; rung changes clear it, automation
  included.
- `glossary:rotten-log`: new grammar; Pending logs; blank always logs; step entries.
- `glossary:task-freshness`: one sentence pointing to Task Decay.

**New decision record `task-decay-is-one-ladder`.** It supersedes in part:

- `rotten-keeps-use-priority-decay`: limit, lane rejection, Keep +1, Not now.
- `rotten-keeps-are-logged`: Pending exclusion, dismissals never logging.
- `next-keeps-ask-an-optional-rotten-reason`: blank writes nothing, Next uncounted.
- `task-lanes-are-sticky`: claim 4 "only release lowers", plus automation clearing
  keeps.

The record should cite this report and the §3 journal numbers as evidence.

## 9. Open questions for Bryan

1. `rolls: 2` (3 windows per level, ≈ 2.7-year tail) or keep 1 (2 windows)? See A3.
2. Do you want early keeps quiet (A1), or prompted and logged as uncounted?
3. Should the lane be called "Pending" or "WIP" in log entries and card titles (A7)?
4. Is 2 days of WIP keeps too short for agent epics? `pending: 3` is the obvious knob.

## 10. Recommended solution

1. **Ship Phase 0 now** as an independent fix:
   - Load the bullet-property config in the decay card.
   - Make Ready's decay enter P1 (`levels[0]`).
   - Fix the footer and focus.
   - Add the regression test that stops injecting `plugin.config`.

   This alone turns the screenshot into a working "Enter → P1 · back in ~6 days" card.
2. **Adopt one decay ladder** (Pending → Next → Ready → P1–P4 → dropped) under one
   glossary term, **Task Decay**.
   - Each rung allows **2** stays: due Alt+F keeps in `[keeps::]` on lanes, plus
     same-level rolls via the existing Schedule-Log ladder on P-levels.
   - At the allowance, Enter on the card (or Ctrl+Enter on the Task Card) **moves one
     rung down**.
   - Alt+F on the card **stays and resets the count**, with a logged reason.
   - Enter never drops.
3. **Make the Rotten Log the complete, rung-qualified timeline.**
   - Every counted keep logs; a blank reason logs `🤷 no reason given · kept N× in
     <Rung>`.
   - Every Stay logs `stayed in <Rung> after N keeps`, and every step logs
     `🍂 From → To · after N keeps`.
   - The card header shows per-rung tallies.
   - Pending stops prompting for a Work Log on Alt+F.
4. **Configure it explicitly.**
   - Extend `freshness.decay.keeps` to a per-lane map (`pending: 2`, `next: 2`,
     `ready: 2`) and set the priority `decay.rolls: 2`.
   - Land the parsers (Phases 1–2) before writing the map into chezmoi.
5. **Implement in order:** contract (Rust + vectors, JSON schema 15) → ledger-tools
   mirror (namespace v13) → navigation behaviour (card capability v3) → docs, memory,
   and config. Gate the user-visible lane cards on the capability versions so mixed
   installs stay truthful.
