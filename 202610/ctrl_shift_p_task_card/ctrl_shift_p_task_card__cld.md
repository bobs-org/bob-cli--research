# Ctrl+Shift+P Redesign: From "Set bullet property" to a One-Keystroke Task Card

- **Researcher:** cld (one of four in the swarm), 2026-10-03
- **Question:** Should the Obsidian `Ctrl+Shift+P` panel be replaced by a redesigned
  panel that needs as few keypresses as possible, without losing any current
  functionality? If so, how? Critique the plan, adjust the requirements where justified,
  and recommend a solution.
- **Read:** `bob-plugins` master `79d5975` (`plugins/bob-navigation-hotkeys/main.js`,
  `styles.css`, README, tests); `bob-cli` master `f3e64a6` (`docs/projects.md`,
  `docs/task-dependencies.md`, `docs/freshness.md`, `docs/plan.md`, `docs/capture.md`,
  `src/native/note_ready/render.rs`); `~/.config/bob/config.yml`; the Bob vault's
  `.obsidian/hotkeys.json`; and read-only tallies of the vault's Schedule, Work, and
  Cancel Logs.

All line numbers below refer to `bob-plugins: plugins/bob-navigation-hotkeys/main.js`
unless another file is named.

---

## TL;DR

1. **Yes, do it. The panel deserves the attention.** It is Bob's main write surface for
   scheduling. The vault holds about 1,200 picker-shaped Schedule Log entries. The most
   common explicit gesture, picking a P-level (for example P0 → P2), takes about **six
   keystrokes and two visual searches** today. It could take **two**: `Ctrl+Shift+P`,
   then `2`.
2. **Do not build a brand-new panel.** Build a new **front door**. Only stage one (the
   property list) is slow. Everything behind it is about 5,000 lines of hard-won,
   well-tested write semantics: the date, reason, Work Log, cancel, refresh,
   Depends-on, and block-ID stages, plus the counted, Task Link, and `^prj` writers. It
   also covers Schedule and Cancel Logs, Pomodoro pruning, Blocked recovery, and
   freshness stamping. Replace the front door, keep every stage behind it, and keep the
   old filtered list reachable as "search mode". That way nothing is lost by
   construction.
3. **Change the panel's job from "pick a property" to "choose an outcome".** The
   recommended **Task Card** opens on a summary of the task. It shows a previewed
   recommendation (`⌃↵`), a **P-level strip** where `1`–`4` write instantly the exact
   date shown under each level, and a short, fixed-order action list:
   - `↵` Schedule…
   - `b` Blocked by…
   - `f` Review every…
   - `⌥N` Commit/Release
   - `x` Cancel…

   Typing any other letter falls back to today's fuzzy-filter list, so old typing
   habits keep working.
4. **The key map was chosen with a habit-collision audit (§7.4).** No sequence Bryan
   could have learned on today's panel turns into a different *write* on the new one.
   The only mismatches open a stage that writes nothing until confirmed.
5. **Requirement adjustments** (§5.2): define "no lost functionality" as
   *reachability plus write-semantics parity*, not key-sequence parity. Share one key
   vocabulary with the approved-decay card, which goes live on 2026-10-19. Make every
   one-key write show its result before the keypress (WYSIWYG). Make type-ahead
   reliable. Ship after the 2026-10-05 → 10-18 freshness trial.
6. **Side finding (bug filed as `bob-cli-3z`).** The current "Refresh every" value stage
   passes a bare string as a footer hint. `renderFooter` then throws before the results
   render. The vault has **zero** `[refresh:: N]` fields although the row shipped in nav
   1.44.0, which suggests the row has never worked in real Obsidian.

---

## 1. What Ctrl+Shift+P Is Today

### 1.1 Wiring

- `hotkeys.json` binds `Ctrl+Shift+P` to `bob-navigation-hotkeys:set-bullet-property`.
  The plugin registers the command with no default hotkey (`main.js:31910`).
- `openBulletPropertyPicker` (`:36323`) routes by context, then opens
  `BulletPropertyPickerModal` (`:24359`, about 5,900 lines). The modal extends the
  shared `FilteredPickerModal` (`:15912`): a header, a search input, a results list, and
  a footer of keycap hints.
- The properties come from `~/.config/bob/config.yml` (chezmoi-managed): `scheduled`
  (date), `dependsOn` (`local_task_id`), and `priority` (levels P1–P4 →
  `high`/`medium`/`low`/`lowest`, with roll windows 2–7, 8–30, 31–90, and 91–365 days).
  The config schema also accepts arbitrary list-valued properties.

### 1.2 Entry Contexts ("Sessions")

| Cursor / gesture | What the panel edits |
| --- | --- |
| `#task` line | That task (inline fields) |
| `#task … ^prj` lifecycle task | `scheduled` goes to project **frontmatter** and propagates to tasks; other fields stay inline |
| Plain bullet | Inline fields; no lane, cancel, or refresh rows; `dependsOn` only if already defined |
| `N<Ctrl+Shift+P>` (Vim count) | The task plus the next N tasks (counted session; aggregated "mixed" states; batch writes in one undo step) |
| Dedicated Task Link bullet | The **linked** task(s) in their own note (link session; up to N sibling links) |
| Anywhere on a `⛓️ **DEPENDS ON:**` line | Skips stage one; opens the owning task's Depends-on stage |
| Palette `Edit task dependencies`, ledger-tools chips, nav api v1 | Same Depends-on stage via `initialProperty: "dependsOn"` |
| Selection spanning tasks, prose with several links, non-bullet | Refused with a short notice |

### 1.3 Stage One: Rows and Their (Unstable) Order

Rows are built in `showPropertyStage` (`:24467`):

1. **Lane** (`Commit to Next` / `Release to Ready`): pinned first. Shown for Ready,
   Next, and In Progress; hidden for Blocked and closed tasks. Releasing an In Progress
   task asks for an optional Work Log summary first.
2. **Refresh every** (`[refresh:: N]` via `api.freshness.setRefreshLine`): pinned
   second when the freshness API is present.
3. **Config properties.** *Defined properties sort before undefined ones*, then follow
   config order (`createBulletPropertyItems`, `:17683`).
4. **Cancel task**: pinned last. Shown when at least one target is an open task.
5. **Then the whole list is reordered.** On a task with a priority, the `scheduled` row
   is hoisted to index 0 (`promoteScheduledRowForPrioritizedTask`, `:24304`).

So **row positions depend on task state**: status, which fields are set, whether
priority is set, and whether the freshness API is loaded. Positional muscle memory
cannot form, so Bryan has to type filter text.

### 1.4 Stages Behind Stage One

| Stage | Reached from | What it does |
| --- | --- | --- |
| Date value | `scheduled` row | 10 presets (Today … In 1 month), a typed date (`YYYY-MM-DD`, `M/D`, `+Nd/w/m`), and a pinned `🎲 Pn roll` row on prioritized tasks (`⌃R` re-rolls). |
| Schedule reason | after choosing a typed or preset date | Optional reason → `🗓️ **SCHEDULE LOG**`. An empty reason on a task that already keeps a log writes `🤷 no reason given`. `Esc` writes nothing. |
| Scheduling Work Log | after any scheduling gesture on Pending/Next targets | Optional `🛠️ **WORK LOG**` summary |
| Priority value | `priority` row | P1–P4. Writes the field plus a rolled `scheduled` date and a `🎲` Schedule Log entry immediately (no reason prompt). |
| Depends on (vault-wide) | `dependsOn` row, or a Depends-On line | CURRENT/RESULTS/BLOCKED sections, `Tab` marks, `＋ id` prompts, a stale reopen, and the `⛓ N · M open` pill |
| Block ID | inside the Depends-on flows | Validates a fresh `^id` in the target note |
| Refresh value | refresh row | Presets 2/3/7/14/30/90/180/365, "use default", or a typed 1–365 |
| Cancel reason | cancel row | `[-]` + `[cancelled::]`, an optional `❌ **CANCEL LOG**`, Pomodoro prune, and Blocked-dependent recovery |
| Lane release reason | lane row on In Progress | Optional Work Log entry |

### 1.5 Keys Today

- **Base keys.** `↑↓` and `⌃N`/`⌃P` move the selection, `↵` chooses, `esc` dismisses
  everything (it never goes "back").
- **`⌃↵`** on `scheduled` (in either stage) takes the **recommended roll**: a same-level
  roll, a decay, or a cancel past the last level, from the Schedule Log streak.
- **`⌃R`** re-rolls the previewed date.
- **`⌃D`** deletes the selected property.
- **`Tab`** marks rows in the Depends-on stage.

### 1.6 Side Effects That Must Ride Along Unchanged

- Future `scheduled` dates prune today's open-Pomodoro links, and future-scheduled
  tasks become Blocked.
- A `^prj` schedule propagates to its tasks.
- Every rewritten open task gets a freshness stamp.
- Cancels and dependency removals run Blocked-dependent recovery.
- The rich notice cards (rolled date, distance, chips) stay as they are.
- Stale-preimage refusals reopen the stage, and each gesture is one undo step.

These all live in the **writers**, not in stage one. That is the main reason to replace
only the front door.

---

## 2. Evidence: How the Panel Is Used

Read-only tally of managed-log entries across the vault (all time):

| Entry kind (Schedule Log unless noted) | Count | Produced by |
| --- | ---: | --- |
| `🎲 Pn roll` (same-level) | 516 | `⌃↵` recommended roll, or the pinned roll row |
| `🎲 P0 → Pn` | 457 | Priority row on an unprioritized task, **or** `bob capture … p:N` (indistinguishable) |
| `🎲 Pn randomize` | 443 | `bob randomize` (CLI; not the panel) |
| `🎲 Pn → Pm` (re-prioritize) | 157 | Priority row on a prioritized task |
| Typed reason | 79 | Date stage + reason prompt |
| `🤷 no reason given` | 41 | Date stage + skipped prompt on a task that keeps a log |
| Work Log entries | 148 | Mostly the Pomodoro completion copy; some from picker prompts |
| Cancel Log, typed reason | 4 | Cancel row (an empty reason writes no log, so this undercounts) |

Current open-task state: 911 open `#task` lines, 345 carrying `[priority::]` (P2 = 235,
or 68%; P1 = 82; P3 = 23; P4 = 5), 529 carrying `[scheduled::]`, 33 Depends-On lines,
410 `[cancelled::]` fields, and **0** `[refresh::]` fields.

What this says:

- **Choosing a P-level is the dominant explicit gesture**, followed by the
  recommended roll. Hand-picked dates come third, at about 120 entries. Dependencies
  and refresh are rare. The design should make P-levels and the recommendation cost one
  key, and hand-picked dates cost very few.
- `⌃↵` is already a two-gesture flow and is clearly used (516 entries). **It must not
  regress.**
- Caveats: capture `p:N` inflates the P0 → Pn count, and log entries record only what
  was written, not cancelled attempts or navigation.

---

## 3. Why It Feels Slow (Diagnosis)

1. **It asks noun-first.** "Set bullet property" asks *which property?* before *what do
   you want?* The panel has outgrown its name: three of its six rows are not properties
   (lane, refresh, cancel), and its most valuable action (the recommended roll) is a
   modifier chord on one row.
2. **Every write except `⌃↵` needs at least two stages.** A P-level needs the row, then
   the level list.
3. **The order depends on state** (§1.3), so Bryan must type a filter. The filter is
   permissive subsequence matching (`fuzzyMatchesText`, `:16867`): `pr` also matches
   the Cancel row because its search text contains "drop … Ready". It only works
   because of the row order.
4. **Digits do not select P-levels.** Typing `2` in the priority stage keeps P1 on top,
   because P1's detail text "2–7 days" contains a 2.
5. **Possible type-ahead race.** The input is focused in a `setTimeout(0)` (`:16005`),
   so a key typed in the first frame can land in the editor, which is in Vim normal
   mode. This is unverified in Obsidian, but cheap to rule out (§7.9).
6. **`esc` always nukes** (safe, but there is no "back"). The refresh stage even
   advertises `esc back`, which is not true. That same stage is the one with the crash
   (`bob-cli-3z`).

---

## 4. Precedents Worth Borrowing

- **The approved-decay card** (`FreshnessDecayCardModal`, `:4383`) is Bob's own
  precedent for a one-key card. `↵` = Not now (recommended), `L` = Less often,
  `E` = Reword, `D` = Drop, `1`–`4` = P-level, `⌥F` = Keep, and repeats are ignored.
  The redesign should **share its vocabulary**, especially `1`–`4`.
- **`bob capture`** already uses `p:<N>` (N = the picker's P-level row) and `s:<N>`
  (N days from today; `docs/capture.md:100–101`). The card's digits and the schedule
  stage's bare-integer days should mean exactly the same things.
- **Linear** sets issue priority with bare number keys `0`–`4` (0 = no priority) when
  no text field is focused ([Linear shortcuts](https://shortcutref.com/en/linear/),
  [Linear docs](https://linear.app/docs/select-issues)). This is a strong external
  precedent for "digits = priority, 0 = clear".
- **Leader key / which-key** (Emacs, Neovim). One chord opens a small keyed menu that
  shows every continuation. It fits a Vim user, and it keeps one entry point instead of
  a dozen global chords.
- **Obsidian modals.** Add keys to the modal's existing `scope` rather than replacing
  it; replacing it breaks `esc`, `↵`, and arrow handling
  ([Obsidian forum: using `Scope`](https://forum.obsidian.md/t/how-to-correctly-use-scope/105155)).

---

## 5. Critique of the Plan

### 5.1 Is This a Good Idea?

**Yes.** Bryan uses this panel constantly, and the evidence says its top two outcomes
(P-level and recommended roll) cover most uses. Today one of them needs about six
keystrokes and two visual searches. The gain is real and repeats many times a day.

I would change the plan in four ways:

1. **Replace the front door, not the house.** A brand-new panel would have to re-derive
   the session model (single, counted, link, `^prj`, plain), the stale guards, the
   batch transactions, and every log rule. That is the riskiest 80% of the work for
   none of the speed gain. Add a new `card` stage to `BulletPropertyPickerModal`, route
   its keys into the existing stage methods and writers, and keep today's stage one as
   *search mode*.
2. **Re-centre the panel on outcomes (verbs).** The card is organized around what Bryan
   decides during triage: *defer by priority*, *take the recommendation*, *schedule*,
   *sequence*, *review less often*, *commit/release*, *cancel*. These match the review
   outcomes already written in `docs/freshness.md` §6 and the `bob ready` footer
   ("sequence / defer / drop Ctrl+Shift+P"). Keep the command ID so `hotkeys.json` and
   the API callers keep working. Rename the palette label to "Task card (set
   properties)".
3. **One vocabulary across both cards.** The decay card activates on 2026-10-19 and
   already uses `1`–`4` and `↵`. Ship the Task Card with matching meanings, and add one
   alias to the decay card (`x` = Drop) before 10-19. Then the two cards never disagree.
4. **Respect the freshness trial.** `Ctrl+Shift+P` is how several trial review outcomes
   are recorded (refresh, defer, drop). Changing that UI between 10-05 and 10-18 would
   confound the trial. Build during the trial and ship on 10-19, together with the
   decay card.

### 5.2 Requirement Adjustments (Explicit)

| # | Original requirement | Adjusted to | Why |
| --- | --- | --- | --- |
| RA1 | "Migrate to a new, redesigned panel" | Migrate **stage one** to a new card. Keep every later stage and writer. Keep the classic list as search mode. | All the speed gain is in stage one; all the risk is in the writers. |
| RA2 | "Don't lose any functionality" | Every capability stays **reachable**, and every write keeps **byte-identical semantics** (logs, prunes, stamps, recovery, undo). Exact old **key sequences** may change, but an old sequence never turns into a *different write* (§7.4). | Without this definition the requirement either blocks the redesign or is quietly violated. |
| RA3 | "As few keypresses as possible" | As few **gestures and visual searches** as possible for the **frequent** outcomes, with **no blind writes**. Every one-key write shows its exact result before the press. | Picking the wrong date with one key is worse than taking two keys. The preview is part of "intuitive". |
| RA4 | (new) | **Stable layout.** Rows never reorder by task state; unavailable rows dim instead of disappearing. | Lets position and key memory form. |
| RA5 | (new) | **Shared vocabulary** with the decay card and `bob capture` (`1`–`4` = `p:N`; schedule-stage `N` = `s:N`) | One mental model across surfaces |
| RA6 | (new) | **Type-ahead safe.** Keys pressed right after `Ctrl+Shift+P` act on the card and never leak into the Vim editor. Held-key repeats never write. | "Reliable" for a panel used at speed |
| RA7 | (new) | **Ship after the trial** (10-19), and fix `bob-cli-3z` first | Avoids confounding the trial, and the refresh row must work before it gets a key |

---

## 6. Options Considered

| Option | P-level | Date + reason | Risk | Effort | Verdict |
| --- | --- | --- | --- | --- | --- |
| **A. Tune the current list**: stable order, digits select levels in the value stage, better ranking | 4 | ~6 + text | low | small | Worthwhile but timid. Stays noun-first with two stages. |
| **B. Task Card front door** over the existing stages (leader-key style) | **2** | **4 + text** | low–medium | medium–large | **Recommended** |
| **C. Global chords per action** (e.g. `Alt+1..4` priority in the editor) | 1 | n/a | medium | small | Fastest raw, but no preview of the rolled date, more global hotkeys, and nothing to discover. Possible later as an *addition* once the card's semantics are proven. |
| **D. Command line in the panel** (`p2`, `s3 why`, `x obsolete`, like capture grammar) | 3 | 4 + text | medium (parsing ambiguity) | medium | Powerful, but costs more keys for the top action. Best folded into B's search mode later. |
| **E. Full rewrite** as a new modal class | 2 | 4 + text | **high** | xlarge | Same UX as B, with the writer risk. Reject. |

Key counts treat a chord as one gesture and include `Ctrl+Shift+P`.

---

## 7. Recommended Design: The Task Card

### 7.1 Principles

1. **Outcome first.** The most likely decisions are visible without typing.
2. **One key per frequent outcome.** Rare outcomes are one key away from a stage.
3. **WYSIWYG.** Every instant key shows its exact write beforehand (date, level, lane).
4. **Stable geometry.** The same rows sit in the same places with the same keys, every
   time.
5. **Habit-safe.** Anything that is not an accelerator types into the classic search,
   so old fingers still work.
6. **Nothing new behind the glass.** Card keys call the existing stage methods and
   writers.

### 7.2 Layout (single prioritized task, dark theme)

```text
╭──────────────────────────────────────────────────────────────────────╮
│ ◉ Write the onboarding guide                                         │
│   Work_ship · NEXT · P2 · 📅 Tue Oct 6 · in 3d · ⛓ 1 open · ↻ 7d     │
├──────────────────────────────────────────────────────────────────────┤
│ ⌃↵  🎲 Roll P2 again          Wed Oct 21 · in 18 d        step 1/1   │
│     today ●━━━━━━━━[░░░░░░░░░░░░░░▲░░░░░░░░░]━━━━━━     ⌃R re-roll   │
│                     8 d                      30 d                    │
├──────────────────────────────────────────────────────────────────────┤
│  1  P1          2  P2  ●        3  P3           4  P4          0  P0  │
│  Oct 8 · 5d     Oct 21 · 18d    Nov 30 · 58d    Mar 2 · 150d   clear │
├──────────────────────────────────────────────────────────────────────┤
│▸ ↵  📅 Schedule…                                 Tue Oct 6 · in 3d   │
│  b  ⛓  Blocked by…                                   1 of 1 open     │
│  f  ↻  Review every…                                 7 d · default   │
│  ⌥N ⤓  Release to Ready                                Next → Ready  │
│  x  ⊘  Cancel task…                                                  │
├──────────────────────────────────────────────────────────────────────┤
│ type to search · ⌃D clear · ↑↓ move · esc close                      │
╰──────────────────────────────────────────────────────────────────────╯
```

The parts, top to bottom:

- **Header.** The task text, cleaned of `#task`, inline fields, and `^id`, clamped to two
  lines. A breadcrumb of the note name, then chips: lane (colored like the dashboard
  lane chips), priority, scheduled with relative distance (red when overdue), the
  dependency pill, and the refresh interval.
- **Recommendation banner.** Shown only when today's `⌃↵` has a recommendation, and
  rendered from the same preview model (`getStageOneRollPreview`).
  - Decay reads `🎲 P2 → P3 decay · Sat Nov 14 · in 42 d`.
  - A terminal cancel renders in the error color as `⊘ Cancel — decayed past P4`.
  - A slim **timeline bar** makes the window tangible. It shows today, the level's
    window band, a tick at the rolled date, and a hollow tick at the current schedule.
- **P-level strip.** One segment per configured level, so it grows if the config does.
  Each segment shows the digit keycap, the label, and **the exact date pressing it will
  write**, rolled once at open with the injected random, as the decay card does. The
  current level carries an accent ring, and `0 P0 clear` sits at the end.
- **Action list.** Fixed order with a keycap column, as on the decay card. The focus
  starts on **Schedule…**, so `↵` opens the date stage. Unavailable rows (for example
  Blocked by on a plain bullet, or Cancel on a closed task) are dimmed, not removed, so
  the geometry stays stable.
- **Footer.** Minimal, because the keys are on the rows themselves.

### 7.3 Key Map

| Key | Outcome | Writes on press? | Same meaning elsewhere |
| --- | --- | --- | --- |
| `1`–`9` | Set P-level N (config order) and roll its window: **exactly the date shown in the strip** | yes. Pending/Next targets still get the optional Work Log prompt first, unchanged. | `bob capture p:N`; decay card `1`–`4`; Linear |
| `0` | Clear priority (implicit P0). `scheduled` is untouched, as with today's `⌃D` on priority. | yes | Linear `0`; docs' "implicit P0" |
| `⌃↵` | Take the recommendation (roll, decay, or cancel). Batch-aware. | yes (unchanged) | today's `⌃↵` |
| `⌃R` | Re-roll the banner date (and the strip dates) | no | today's `⌃R` |
| `↵` | Open the focused row (Schedule… by default) | no | |
| `b` | **B**locked by… (the existing Depends-on stage) | no | |
| `f` | Review every… (the existing refresh stage, *f*requency) | no | |
| `x` | Cancel task… (the existing cancel-reason stage) | no | decay card Drop (add an `x` alias there) |
| `⌥N` | Commit to Next / Release to Ready (an In Progress release still prompts for a Work Log first) | yes | editor `Alt+N` |
| `⌃D` | Clear the focused row's property (default focus Schedule, so `⌃⇧P ⌃D` unschedules) | yes | today's `⌃D` |
| `↑↓`, `⌃N`/`⌃P` | Move focus over the action list | no | today |
| any other printable | **Search mode**: today's filtered property list, seeded with that character | no | today's stage one |
| `⌫` on an empty search | Back to the card | no | |
| `esc` | Close and write nothing (in every stage, as today) | no | today |

Counted (`N<⌃⇧P>`) and Task Link sessions use **the same keys**. Each key applies to
every target through the existing batch writers: per-target rolls for digits, batch
recommendations for `⌃↵`, and add-to-all/remove-from-all for `b`. The strip then shows a
date span (`Oct 9 – Oct 28`) instead of one date, and the banner shows the existing mix
summary (`4 tasks · 2 roll · 1 decay · 1 cancel`).

### 7.4 Habit-Safety Audit

The rule: **an accelerator may only be a key that no plausible old habit starts
with**, unless the old and new outcomes are identical. Old habits start with the first
letters of today's row labels and filter words: `s`, `p`, `d`, `c`, `r`, `l`, `n`, `o`.
**Those letters stay unbound**, so they type into search exactly as before. `b`, `f`,
`x`, and the digits are habit-free.

| Old sequence after `⌃⇧P` | Old result | New result | Verdict |
| --- | --- | --- | --- |
| `⌃↵` / `⌃R ⌃↵` | recommended roll | identical | ✅ preserved |
| `↵` on a prioritized task (scheduled row first) | date stage | date stage | ✅ preserved |
| `↵` on a Ready, unprioritized task (lane row first) | Commit to Next | date stage, nothing written | ⚠️ safe mismatch |
| `↵` on a Next / In Progress, unprioritized task | Release to Ready | date stage, nothing written | ⚠️ safe mismatch |
| `pr…`, `sc…`, `dep…`, `can…`/`drop…`/`obs…`, `ref…`, `com…`/`rel…`/`lane…`/`next…`, then `↵` | that row's stage or action | search mode, same rows, same `↵` | ✅ preserved |
| `⌃D` on the first row of a prioritized task (scheduled) | unschedule | unschedule | ✅ preserved |
| `⌃D` on the first row of an unprioritized task (lane) | "not a property" no-op | unschedule (one undo step) | ⚠️ behavior change, undoable |
| `↓↓ ↵` (positional) | state-dependent | some stage opens; nothing written | ⚠️ safe mismatch |
| any digit | (no habit: digits only filtered) | writes a P-level | ✅ new; no collision |

Two alternatives I rejected:

- **`s`/`p`/`d` as accelerators.** They are mnemonic, but the habit `dep↵` would land
  in a Cancel or Depends stage with the leftover letters typed as a reason or a search,
  and the next `↵` would write it.
- **Plain `↵` taking the recommendation.** It saves nothing, because `⌃↵` is already
  one gesture. It would also turn the habit "`↵` opens the date list" into an
  immediate write, with the rest of that habit (arrow keys and reason text) leaking into
  the Vim editor.

### 7.5 Keystrokes: Today vs Task Card

Gestures include `⌃⇧P`; a chord counts as one.

| Goal | Today | Task Card |
| --- | ---: | ---: |
| P0 → P2 on a Ready task | 6 (`⌃⇧P p r ↵ ↓ ↵`) | **2** (`⌃⇧P 2`) |
| P2 → P3 on a prioritized task | 6–7 | **2** |
| Take the recommendation | 2 | 2 |
| Re-roll, then take | 3 | 3 |
| In 3 days, with a reason | 7–9 + text | **4 + text** (`⌃⇧P ↵ "3 why…" ↵`) |
| In 3 days, no reason | 7–9 | **5** (`⌃⇧P ↵ 3 ↵ ↵`) |
| Unschedule | 2–4 | **2** (`⌃⇧P ⌃D`) |
| Clear priority | 4–6 | **2** (`⌃⇧P 0`) |
| Cancel (no reason) | 6 (`⌃⇧P c a n ↵ ↵`) | **3** (`⌃⇧P x ↵`) |
| Open Depends on | 5 | **2** |
| Refresh every 14 days | 6 | 5 (`⌃⇧P f 1 4 ↵`) |
| Counted: P2 on 4 tasks | 7 | **3** (`3 ⌃⇧P 2`) |

Visual search matters as much as the counts. In keystroke-level-model terms, the
P-level path drops from two "find the row" mental operators to one, because the digits
never move.

### 7.6 Schedule Stage (Small, Compatible Upgrades)

The stage is still the existing date stage: the same presets, the pinned `🎲` row, `⌃R`,
`⌃↵`, the reason stage, and the Work Log stage. Additions:

- **Bare `N` = in N days** (`0` = today, `1` = tomorrow), matching `bob capture s:N`.
- `Nd` / `Nw` / `Nm` also work **without** `+`; the old `+Nd`, `M/D`, and ISO forms are
  unchanged.
- Weekday names `mon`…`sun` mean the next occurrence after today.
- **Inline reason.** In `9 waiting on the API review`, the first token is the date and
  the rest is the reason. `↵` commits directly, skipping the reason stage, because the
  reason is now known. That is the existing rule: "the prompt appears only when the
  reason is not already known." A bare date + `↵` still opens the reason stage as today.
- The parsed preview row always shows the resolved weekday, ISO date, and distance, plus
  the reason and where it will be logged, before anything is written.

### 7.7 Contexts

- **`^prj`.** The header shows "project"; Schedule writes frontmatter, exactly as today.
- **Plain bullet.** The strip, Schedule, and custom properties are active. Lane, Cancel,
  and Refresh are dimmed. Blocked by is dimmed unless already defined.
- **Closed task.** No banner. Lane and Cancel are dimmed. The other keys behave as they
  do today.
- **Blocked `[?]`.** Lane is dimmed, as today (no lane row). The header chip shows
  `BLOCKED · scheduled …` or `waits on N`.
- **Depends-On line, palette command, chips.** These still open the Depends-on stage
  directly. The card is skipped, as stage one is skipped today.
- **Custom list properties** from `config.yml` get rows under a "More" divider, reachable
  with `↑↓` or search. They get no letter keys, which keeps the habit audit clean.

### 7.8 Visual Spec ("Beautiful")

- **Width and type.** Width `min(560px, 92vw)`; it reuses the `bob-cnp` font and spacing
  tokens so it feels related to Bob's other pickers. Dates use `font-variant-numeric:
  tabular-nums` so they align.
- **Colors.** Use only Obsidian CSS variables, so light and dark themes, and custom
  themes, work:
  - Banner: an accent tint
    (`color-mix(in srgb, var(--interactive-accent) 12%, transparent)`) with a 3px
    accent bar on the left.
  - Cancel row and terminal-cancel banner: `--text-error`.
  - P-level hues ramp from warm to cool (`--color-red`, `--color-orange`,
    `--color-yellow`, `--color-blue`) at about 15% tint. Reuse the ledger-tools chip
    colors if they already exist.
- **Keycaps.** Same styling as the decay card's key column, so both cards look like
  siblings.
- **Motion.** Only an ~80 ms background fade on focus; none under
  `prefers-reduced-motion`.
- **Accessibility.** `role="dialog"`, the strip as a `radiogroup`, and the action rows
  as `listbox`/`option` with `aria-keyshortcuts`. Every key has a visible keycap.
- **Receipts.** Keep the existing notice cards (P-level, rolled date and distance,
  chips). They are already good.

### 7.9 Reliability Spec

1. **Synchronous readiness.** Register card keys on the modal's existing `scope` and
   focus the card element synchronously in `onOpen`, keeping today's `setTimeout`
   focus only as a fallback. Test: dispatch `2` right after `open()` without flushing
   timers, and the P2 write must happen.
2. **No repeat writes.** Ignore `event.repeat` and `isComposing`, and keep the existing
   single-flight `opening` guard so a double press cannot write twice.
3. **WYSIWYG writes.** Digits pass the strip's preview into the existing writers:
   `precomputedRoll` for a single task (`:38931`), `precomputedRollByLine` for counted
   sessions, and `precomputedByPath` for link sessions (`applyLinkPickerPropertyValue`,
   `:32761`). If the target changed underneath, refuse and reopen fresh (the existing
   stale pattern).
4. **One gesture, one undo step.** Inherited from the existing transactions.
5. **Pure model plus pure key resolver.** `planTaskCard(context)` and
   `resolveTaskCardKey(model, event)` are table-tested for every session ×
   availability × key, following `planFreshnessDecayCard`.
6. **DOM-stub render tests.** Today's node tests never run `renderAll` (`resultsEl` is
   null), which is how `bob-cli-3z` slipped through. Add a minimal DOM stub that renders
   the card and every stage at least once.
7. **Explicitly rejected:** swallowing keystrokes for a few hundred ms after an instant
   write closes the card. The habit audit makes it unnecessary, and timing hacks are
   their own source of flakiness.

---

## 8. Implementation Plan (Suggested Epic, Size Large)

| Phase | Repo | Scope | Size |
| --- | --- | --- | --- |
| 0 | bob-plugins | Fix `bob-cli-3z` (refresh footer hint) and harden `renderFooter` against non-object hints. Add the DOM-stub render harness. | small |
| 1 | bob-plugins | Pure `planTaskCard` and `resolveTaskCardKey`, built from the existing describers: `createBulletPropertyItems`, `createCountedBulletPropertyItems`, `createLinkPickerPropertyItems`, `describeLaneRow`, `describeRefreshRow`, `describeCancelTaskRow`, the roll recommendation and batch previews, and `withDependencyPropertyPills`. Per-level preview rolls follow the `planFreshnessDecayExplicitLevelPicks` pattern (`:3542`). Full table tests. | medium |
| 2 | bob-plugins | A `card` stage in `BulletPropertyPickerModal`: renderer, CSS, scope keys, dispatch into the existing stage methods (`showValueStage`, `showCancelReasonStage`, `showRefreshValueStage`, `showLocalTaskValueStage`, `applyLaneToggleFromPicker`, `maybeOfferPriorityWorkLog` with precomputed rolls, `applyRecommendedRoll` and its batch variants, `deleteSelectedProperty`). Search mode = the existing `showPropertyStage` seeded with the typed key, plus `⌫` back. Handler suite. Nav **2.0.0**, because the stage-one keyboard contract changes. | large |
| 3 | bob-plugins | Schedule-stage grammar (bare N, unsigned units, weekdays, inline reason) with tests | small–medium |
| 4 | both | Decay card: add the `x` alias for Drop, and optionally `f` for Less often. Update the docs: the bob-plugins README row; bob-cli `docs/projects.md`, `docs/task-dependencies.md` §6.1, and `docs/freshness.md` §6 review outcomes; and the `bob ready` hint strings in `src/native/note_ready/render.rs:405,541` (e.g. `defer ⌃⇧P 1–4 · drop ⌃⇧P x · sequence ⌃⇧P b`). Run `bob plugins sync`. | small |

**Rollout:** phases 0–3 can land during the trial, behind the existing stage one (for
example, a `card: false` default for one week). Switch the card on 2026-10-19, together
with the decay card. Search mode stays permanently as the classic fallback, so no
separate rollback flag is needed after the first week.

---

## 9. Risks and Open Questions for Bryan

1. **Do you use `⌃⇧P ↵` to commit a Ready task to Next** (today the lane row is first
   on unprioritized tasks)? If so, the new `↵` opens Schedule instead. It is safe, but
   it is a habit break. `⌥N` (in the card or the editor) is the replacement.
2. **Should `↵` on an unprioritized task do something bolder?** One option is the decay
   card's "Not now" (enter P2 by the refresh interval). I recommend **no**: keep `↵`
   non-writing and let the digits carry the defer intent.
3. **Typed `sat` on a Saturday:** today or next week? I propose next week; `0` already
   means today.
4. **Key letters:** are `b` (blocked by), `f` (review frequency), and `x` (cancel) the
   right mnemonics? They were chosen for habit safety first, mnemonics second.
5. **Name:** "Task card" or "Triage"? The command ID stays `set-bullet-property` either
   way.
6. **Risk: a slower first paint** from four extra preview rolls plus header parsing.
   This is negligible (pure string work on one line, already done for `⌃↵`). Measure it
   anyway in the handler suite.

---

## 10. Recommendation

Build **Option B: a Task Card front door on the existing `Ctrl+Shift+P` modal**.

- **Keys.** Instant WYSIWYG P-levels on `1`–`4` (and `0` to clear). The recommendation
  stays on `⌃↵`. A fixed action list sits behind `↵` (Schedule), `b`, `f`, `⌥N`, and
  `x`. Every other key falls back to today's search list.
- **Behind the card.** Keep every existing stage and writer untouched, and add a small
  capture-compatible date grammar to the schedule stage.
- **Alignment and timing.** Align the key vocabulary with the decay card and
  `bob capture` before 2026-10-19, and ship that day after fixing `bob-cli-3z`.

This cuts the most frequent explicit gesture from about six keystrokes to two. It keeps
`⌃↵` at two, it makes no old habit write something different, it loses no
functionality by construction, and it gives the panel one calm, stable,
theme-native layout.

---

## Sources

- Linear priority shortcuts: [shortcutref.com/en/linear](https://shortcutref.com/en/linear/),
  [linear.app/docs/select-issues](https://linear.app/docs/select-issues),
  [pie-menu.com/shortcuts/linear](https://www.pie-menu.com/shortcuts/linear)
- Obsidian modal scopes:
  [forum.obsidian.md: How to correctly use Scope](https://forum.obsidian.md/t/how-to-correctly-use-scope/105155)
- Keystroke-level model: Card, Moran & Newell, *The Psychology of Human-Computer
  Interaction* (1983). Its operators are used only qualitatively here.
- Code and docs: `bob-plugins` `plugins/bob-navigation-hotkeys/main.js`
  (`:3542`, `:4383`, `:15082`, `:15912`, `:16005`, `:16867`, `:17683`, `:21913`,
  `:22779`, `:24304`, `:24359`, `:24467`, `:24955`, `:29876`, `:30796`, `:31910`,
  `:32761`, `:36323`, `:38931`); `bob-cli` `docs/projects.md`,
  `docs/task-dependencies.md` §6, `docs/freshness.md` §2a/§6, `docs/capture.md`
  (`s:<N>`, `p:<N>`), and `src/native/note_ready/render.rs`.
- Filed during this research: `bob-cli-3z` (refresh value stage footer crash).
