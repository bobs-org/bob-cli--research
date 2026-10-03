# Ctrl+Shift+P Task Card: A One-Key Front Door on Bob's Existing Property Engine

- **Role:** lead researcher (consolidated report), 2026-10-03
- **Question:** Should the panel that `Ctrl+Shift+P` opens in Obsidian be migrated to a
  new, redesigned panel that needs as few keypresses as possible, loses no current
  functionality, and is intuitive, reliable, and beautiful? Critique the plan, adjust the
  requirements where justified, and recommend a solution.
- **Inputs:** four independent reports in this directory (`__cdx`, `__cld`, `__grk`,
  `__gem`), plus my own verification against `bob-plugins` master `79d5975`
  (bob-navigation-hotkeys **1.71.0**), `bob-cli` master `f3e64a6`, the vault's
  `.obsidian/hotkeys.json`, `~/.config/bob/config.yml`, a read-only tally of the vault's
  Schedule Logs, and the decision records `task-lanes-are-sticky` and
  `rotten-keeps-use-priority-decay`.

Line numbers refer to `bob-plugins: plugins/bob-navigation-hotkeys/main.js` unless
another file is named.

---

## TL;DR

1. **Yes, redesign it, but do not build a new panel.** Build a new **front door**. All
   four reports agree on this independently. Only stage one, the property list, is slow.
   Everything behind it is about 5,900 lines of tested write semantics: date, reason,
   Work Log, cancel, refresh, Depends-on, block-ID, and the counted, Task Link, and
   `^prj` writers. Replace stage one with a compact **Task Card**. Keep every stage and
   writer behind it, and keep the old filtered list as the **search mode**. Nothing is
   lost by construction.
2. **The card opens focused, not in a search box.** Visible one-key accelerators include
   `1`–`4`, which write that P-level **and the exact date printed under it**. `0` clears
   the priority. `⌃↵` keeps taking the recommendation. `↵` opens Schedule…, `b` opens
   Blocked by…, `f` opens Review every…, `x` opens Cancel…, and `⌥N` commits or
   releases the lane. **Any other key types into the classic search**, so no old typing
   habit can turn into a different write.
3. **Impact.** The most common explicit gesture, picking a P-level, drops from about
   **6 gestures and two visual searches to 2** (`⌃⇧P 2`). Cancel drops from 6 to 3,
   Depends on from 5 to 2, and a counted batch P-level from 7 to 3. The `⌃↵`
   recommendation stays at 2.
4. **Keep the Schedule Log reason prompt, but make it cheap.** Two reports wanted it
   opt-in. The vault shows reasons are a real habit (79–216 typed
   reasons, depending on how entries are classified), so keep it:
   - Type the reason inline (`3 waiting on API` ↵), or press `⇧↵` to skip it.
   - Fold the reason and the Work Log summary into **one** review screen.
5. **Two must-fix items surfaced while verifying.** Neither is in any report as stated.
   - **(a)** `bob-cli-3z` is real. The "Refresh every" stage throws on open. It also
     breaks the approved-decay card's *Less often* picker (intervals of 90+ days). The
     docs make `Ctrl+Shift+P → refresh` the trial's "see it less often" outcome, and the
     trial **starts 2026-10-05**. Fix it this weekend. I corroborated the bead.
   - **(b)** On **Task Link** bullets the picker opens only *after* an async note read.
     Any accelerator typed in that gap lands in the Vim editor (`x` deletes a
     character). The card must open synchronously.
6. **Timing.** Fix `bob-cli-3z` before 10-05. Build the card during the Oct 5–18
   freshness trial, behind a setting that is off by default. Turn it on **on or after
   2026-10-19**, when the decay card activates, so the trial is not confounded.

---

## 1. What Ctrl+Shift+P Is Today

**Wiring.** The vault binds literal `Ctrl+Shift+P` (on every OS) to
`bob-navigation-hotkeys:set-bullet-property` ("Set bullet property"). The command has no
default hotkey (`:31910`). A physical capture listener handles Vim counts.
`openBulletPropertyPicker` (`:36323`) routes by context and opens
`BulletPropertyPickerModal` (`:24359`). That modal subclasses `FilteredPickerModal`
(`:15912`), the same chrome used by the child-note, task-move, and Pomodoro pickers:

- `bob-cnp-modal`, up to **960×840**
- a search input focused in `setTimeout(0)` (`:16005`)
- a results list and a keycap footer

Properties come from `~/.config/bob/config.yml`:

- `scheduled` (date)
- `dependsOn`
- `priority`, with P1–P4 stored as `high`/`medium`/`low`/`lowest` and rolled in windows
  of 2–7, 8–30, 31–90, and 91–365 days

The config can also hold arbitrary list properties.

**Entry contexts.**

| Cursor / gesture | Target |
| --- | --- |
| `#task` line | That task's inline fields |
| `#task … ^prj` lifecycle task | `scheduled` goes to project YAML and propagates; other fields stay inline |
| Plain bullet | Inline fields; no lane, cancel, or refresh rows |
| `N<Ctrl+Shift+P>` (Vim count) | The task plus the next N tasks (N+1 targets), with mixed states and one undo step |
| Dedicated Task Link bullet | The linked task(s) in their own note, up to N sibling links, clamped at the Pomodoro |
| Anywhere on a `⛓️ **DEPENDS ON:**` line, ledger chips, palette `edit-task-dependencies` | Skips stage one; opens the Depends-on stage |
| Multi-task selection, prose with several links, non-bullet | Refused with a notice |

**Stage-one rows and their unstable order** (`showPropertyStage`, `:24467`):

1. A lane row is pinned first.
2. A refresh row comes next, when the freshness API is present.
3. Config properties follow, with defined ones first.
4. Cancel is pinned last.
5. Then, on a prioritized task, `scheduled` is hoisted to index 0
   (`promoteScheduledRowForPrioritizedTask`, `:24304`).

Positions therefore depend on task state, so Bryan has to type filter text. The filter
is permissive: per cld, `pr` also matches Cancel. In the priority stage, typing `2` keeps
P1 on top, because P1's detail text "2–7 days" contains a 2.

**Stages behind stage one** (all kept by this recommendation):

- the date stage: 10 presets, typed ISO / `M/D` / `+Nd|w|m` dates, and a pinned
  `🎲 Pn roll` row
- the Schedule-reason prompt
- the scheduling Work Log prompt, for Next/Pending targets
- the priority stage
- the vault-wide Depends-on stage: CURRENT/RESULTS/BLOCKED, `Tab` marks, `＋ id`
  prompts, and cycle guards
- the block-ID stage
- the refresh stage: 2/3/7/14/30/90/180/365, use-default, or typed 1–365
- the cancel-reason stage, which refuses recurring tasks
- the lane-release Work Log prompt

**Keys today:**

- `↑↓` and `⌃N`/`⌃P` move the selection.
- `↵` chooses.
- `⌃↵` takes the recommended roll: a same-level roll, a decay, or a cancel past P4,
  frozen at open.
- `⌃R` re-rolls.
- `⌃D` deletes the selected property.
- `Esc` always closes and writes nothing.

**Side effects live in the writers, not in stage one.** This is why replacing only the
front door is safe:

- future dates prune today's Pomodoro links and make the task Blocked
- `^prj` propagation
- freshness stamps (Cancel deliberately does not stamp)
- Blocked-dependent recovery
- Schedule, Work, and Cancel Log grammar
- stale-preimage refusals
- one undo step per gesture

---

## 2. Evidence: How the Panel Is Used

I re-ran cld's read-only tally of the vault's Schedule Logs and it matches within
today's drift:

| Schedule Log entry kind | Count | Produced by |
| --- | ---: | --- |
| `🎲 Pn roll` (same level) | 516 | `⌃↵` recommendation or the pinned roll row |
| `🎲 P0 → Pn` | 458 | Priority pick on an unprioritized task, **or** `bob capture p:N` (cannot be told apart) |
| `🎲 Pn → Pm` | 157 | Re-prioritizing in the picker |
| `🎲 Pn randomize` | 449 | `bob randomize` (CLI, not the panel) |
| Typed reasons (not 🎲 or 🤷) | 79 by cld's narrower parse; 216 by mine (e.g. "Launched `sase-10w`!", "I don't have access yet.", "Or today?") | Date stage + reason prompt |
| `🤷 no reason given` | 41 | Skipped prompt on a task that already keeps a log |

Open-task state (cld's census): 345 open tasks carry `[priority::]` (P2 = 68%) and
there are 33 Depends-On lines. My recount confirms **0** `[refresh:: N]` fields anywhere
in the vault.

What the evidence implies:

- **P-level picks and the `⌃↵` recommendation dominate.** Make both one key.
- **Hand-picked dates come third**, and most of them carry a typed reason. That argues
  *against* making the reason prompt opt-in (§6).
- **Dependencies and refresh are rare.** One key into their existing stages is enough.
- **Caveats:** capture `p:N` inflates `P0 → Pn`. Logs record writes, not abandoned
  attempts or navigation. A 20–30-use manual tally during the pilot (cdx) would refine
  this; no telemetry is needed.

---

## 3. New Findings From the Lead's Verification

1. **`bob-cli-3z` is confirmed and wider than filed.**
   - The bug: `showRefreshValueStage` passes `footerHints: ["↵ apply · esc back"]`, a bare
     string (`:24971`), and `renderFooter` calls `hint.keys.forEach`. So the stage
     throws before its results render. This fits the vault having zero `[refresh::]`
     fields even though the row shipped in 1.44.0.
   - **The decay card is also hit.** Its *Less often* picker
     (`openFreshnessDecayLessOftenPicker`, about `:35303–35394`, used for 90+ day
     intervals) reuses `showRefreshValueStage` without overriding `footerHints`. It then
     calls `picker.open()`, which throws into a catch that shows "Could not update task".
   - **Why the timing matters:** `docs/freshness.md` lists `Ctrl+Shift+P → refresh →
     14 / 30 / 90` as the "see it less often" review outcome for the trial that starts
     **2026-10-05**.
   - I added a `+1` to `bob-cli-3z` with this evidence.
2. **Task Link sessions open asynchronously.** `openBulletPropertyPicker` hands off to
   `void this.openLinkPicker(...)`, which awaits `resolveLinkPickerTargets` and reads the
   target notes before any modal exists (`:32607`, `:32545`). Keys typed in that gap go
   to CodeMirror in Vim normal mode.
   - Today that is mostly harmless, because the first keys are filter text.
   - With bare-key accelerators it is not: `x` deletes a character and `s` substitutes.
     And Task Link bullets under today's Pomodoros are where Bryan works all day.
   - cld flagged the `setTimeout(0)` focus race as "unverified". This gap is definite.
3. **`2` on a P2 task is not the same as `⌃↵`.**
   - `⌃↵` writes `🎲 P2 roll`. That entry *counts* toward the roll streak and can
     decay.
   - A priority pick of the current level writes `🎲 P2`, which is classed as "other"
     and **resets** the streak (`docs/projects.md` streak table).
   - Both can preview a similar date, so the card must name the difference ("roll ·
     step 1/2" vs "re-pick · resets streak").
4. **Reasons are a habit, not a tax.** See §2. The docs' contract is "the log records
   every scheduled change the picker makes; the prompt appears only when the reason is
   not already known." A design that captures the reason **inline** honours that
   contract with fewer keys.
5. **The decay card's keys bind the vocabulary.** `FreshnessDecayCardModal` (`:4383`)
   uses:
   - `↵` = Not now
   - `l` = Less often
   - `e` = Reword
   - **`d` = Drop**
   - `1`–`4` = P-levels
   - `⌥F` = Keep

   It ignores `event.repeat`. Any Task Card that binds `d` to *Depends on* would give
   one key opposite meanings across two sibling cards, and one of those meanings is
   destructive. This rules out grk's and gem's `d`.

---

## 4. Critique: Is This a Good Idea?

**Yes.** It is Bob's main scheduling write surface and it is used many times a day. The
two dominant outcomes are a two-stage hunt for one and a chord for the other. The gain
is real and compounds. `bob ready` and `docs/plan.md` already advertise it as *the*
"sequence / defer / drop" tool.

**But the plan as written has four problems.** All four reports reached the same view
on each.

1. **"Migrate to a new panel" puts the risk in the wrong place.** `main.js` is 48,384
   lines, and `test-navigation-hotkeys.cjs` alone has about 511 tests.
   - A new panel would have to re-derive the session model (single, counted, link,
     `^prj`, plain), stale guards, batch transactions, and every log rule. That is the
     riskiest 80% of the work, and it buys none of the speed.
   - The likely failure mode is a second writer.
   - The chrome is about 200 lines of `onOpen`/`handleKeydown`/CSS (grk).
2. **"As few keypresses as possible" is unbounded.** Minimized literally, it deletes the
   reason, Work Log, and cancel prompts. The streak classifier, review, and history all
   read those logs.
3. **The panel is noun-first.** "Set bullet property" asks *which property?* before
   *what do you want?* Three of its six rows are not properties (lane, refresh, cancel),
   and its most-used action is a chord on one row. The redesign should be **outcome
   first**.
4. **The chrome is a category error** (grk). It puts a closed set of about six actions
   inside a 960×840 vault-scale search palette with a focused text box, which makes
   accelerators impossible. Bob already has the right pattern: the ~560px decay card
   with keycaps on its rows.

**Approaches all four reports reject:**

- many new global chords (no preview of the rolled date, a crowded keymap, no counted or
  Task Link context)
- pushing rows into Obsidian's command palette (no session, no pills, no preview)
- a radial menu, mouse toolbar, or always-on inspector (wrong for a Vim user)
- a greenfield modal or a new plugin

---

## 5. Requirement Adjustments (Explicit)

| # | Original | Adjusted to | Why | Source |
| --- | --- | --- | --- | --- |
| RA1 | "Migrate to a new, redesigned panel" | Replace **stage one** with a Task Card inside `BulletPropertyPickerModal`. Keep every later stage, writer, and planner. Keep the classic list as search mode. Keep the command ID `set-bullet-property` and the binding. | All the speed is in stage one; all the risk is in the writers. Existing tests stay the acceptance suite. | all four |
| RA2 | "Don't lose any functionality" | Every capability stays **reachable**, and every write keeps **identical stored semantics** (logs, prunes, stamps, recovery, undo, stale refusals). Key sequences may change, but **no old sequence may produce a different write**. | Without a definition, the requirement either blocks the redesign or gets quietly violated. | cld, cdx |
| RA3 | "As few keypresses as possible" | Fewest **gestures and visual searches** for **frequent** outcomes, with **no blind writes**: every one-key write shows its exact result beforehand. | Writing the wrong date with one key is worse than taking two keys. The preview is part of "intuitive". | cld, cdx, grk |
| RA4 | (new) | **Stable geometry.** Rows never reorder by task state. Unavailable rows dim with a reason; they are not removed. | Lets positional and key memory form. Today's order changes with state. | cld, cdx |
| RA5 | (new) | **One vocabulary** across the Task Card, the decay card, and capture: `1`–`4` = `p:N` = decay-card levels; schedule-stage bare `N` = `s:N`; `x` = cancel/drop on both cards. | One mental model; avoids the `d` = Drop vs Depends clash. | cld, grk, lead |
| RA6 | (new) | **Type-ahead safe.** Keys pressed right after `⌃⇧P` act on the card and never leak into Vim. This includes Task Link sessions, whose targets resolve asynchronously. Held-key repeats and IME composition never write. | "Reliable" for a panel used at speed. | cld, lead |
| RA7 | (new) | **Keep reason capture on by default, but make it cheap:** inline reason, `⇧↵` to skip, and one combined review. | Typed reasons are an established habit (§2). | lead (rejects grk/gem opt-in) |
| RA8 | (new) | **Fix `bob-cli-3z` before 2026-10-05. Ship the card on or after 2026-10-19.** | The trial depends on the refresh stage working, and a UI change mid-trial confounds it. | cld, lead |
| RA9 | (new) | **No module/build restructure in this epic.** Keep the plain-`main.js` + `__testHelpers` convention. | Reviewability. A split is a separate change. | grk, cdx (rejects gem's `src/` tree) |

---

## 6. Where the Reports Disagreed, and the Resolution

| Question | Positions | Resolution and reason |
| --- | --- | --- |
| **Focus model** | cdx: keep the text input focused; no bare-key writes; optional `Mod+1…4`. cld, grk, gem: open in command mode with bare keys. | **Command mode**, with **any unbound printable key falling into search mode** (cld's hybrid). The decay card already proves bare keys in this plugin. WCAG 2.1.4's character-key concern is met because the keys are active only while the dialog has focus. Typing still works for anyone who types. |
| **Which letters** | grk: `n s d r x`. gem: `t m w l x d f r s`. cld: `b f x` + `⌥N`, with the habit letters `s p d c r l n o` left unbound. | **cld's habit-safe set.** A bound letter that *writes* and is also the first letter of an old filter habit leaks the rest of the habit into Vim after the modal closes. Example: `next↵` with `n` bound becomes "lane toggle, then `ext↵` typed into the editor". `d` is also Drop on the decay card. |
| **What `↵` does on open** | gem: `↵` commits the recommendation. cld: `↵` opens Schedule…. grk: `↵` activates the selected row. | **`↵` opens Schedule… (the default focus), and writes nothing.** `⌃↵` already makes the recommendation one gesture. Prioritized tasks already open the date stage on `↵` today (scheduled is hoisted), so the habit is preserved. |
| **Esc** | grk: Esc goes back from nested stages. cdx and cld: Esc always closes. | **Esc closes and writes nothing** (habit + the documented promise). **`⌫` on an empty input, or a visible "← Back", returns to the card.** Once the card exists, back-then-key and reopen-then-key cost the same gestures. Back only wins for counted sessions, and `⌫` covers that. |
| **Schedule reason** | grk, gem: opt-in. cdx: one combined review. cld: inline reason in the date input. | **Inline reason + `⇧↵` skip + one combined review** (cld + cdx). This keeps the habit visible in §2 and costs at most one key over opt-in. |
| **Raw-markdown live diff** (gem) | | **Rejected as primary UI.** It shows field syntax to the user. Use one human-readable effect line instead (cdx): date, priority change, Blocked, link prune, propagation scope. |
| **Hide or dim unavailable rows** | cdx: hide inapplicable rows. cld: dim them. | **Dim with a reason** for availability that depends on state. For structurally different contexts (plain bullet, Depends-On entry) the dimmed layout still keeps geometry stable. |
| **Accelerators beyond the card** | cdx: optional `Mod+1…4`. cld: global `Alt+1..4` maybe later. | **Not in v1.** Bare digits on the card are one key. Revisit global chords only after the card's semantics have proven out. |

---

## 7. Recommended Design: The Task Card

### 7.1 Principles

1. **Outcome first.** The likely decisions are visible without typing.
2. **One key per frequent outcome.** Rare outcomes are one key away from their existing
   stage.
3. **WYSIWYG.** Every instant key shows its exact write beforehand: date, level, lane.
4. **Stable geometry.** The same rows sit in the same places with the same keys, every
   time.
5. **Habit-safe.** Any key that is not an accelerator types into the classic search.
6. **Nothing new behind the glass.** Card keys call the existing stage methods and
   writers.

### 7.2 Layout

Single prioritized Next task (the sketch uses frozen example dates):

```text
╭──────────────────────────────────────────────────────────────────────╮
│ ◉ Write the onboarding guide                                     [×] │
│   Work_ship · NEXT · P2 · Tue Oct 6 · in 3d · ⛓ 1 open · ↻ 7d        │
├──────────────────────────────────────────────────────────────────────┤
│ ⌃↵  🎲 Roll P2 → Wed Oct 21 · in 18d                     step 1 / 2  │
│     today ●━━━━━━[░░░░░░░░░░░░░░░▲░░░░░░░░░░]━━━━━      ⌃R re-roll   │
│                   8d                         30d                     │
├──────────────────────────────────────────────────────────────────────┤
│  1  P1          2  P2 ●         3  P3           4  P4          0  P0  │
│  Oct 8 · 5d     Oct 24 · 21d    Nov 30 · 58d    Mar 2 · 150d   clear │
│                 re-pick                                   keeps date │
├──────────────────────────────────────────────────────────────────────┤
│▸ ↵   📅  Schedule…                                 Tue Oct 6 · in 3d │
│  b   ⛓  Blocked by…                                     1 of 1 open │
│  f   ↻  Review every…                                   7d · default │
│  ⌥N  ⤓  Release to Ready                               Next → Ready │
│  ─────────────────────────────────────────────────────────────────── │
│  x   ⊘  Cancel task…                                 optional reason │
├──────────────────────────────────────────────────────────────────────┤
│ type to search · ⌫ back · ⌃D clear · esc close                       │
╰──────────────────────────────────────────────────────────────────────╯
```

The parts, top to bottom:

- **Header = the task you are about to rewrite.**
  - The task text, cleaned of `#task`, inline fields, and `^id`, clamped to two lines.
  - Below it: the note, a lane chip coloured like the dashboard chips, the P-level, the
    scheduled weekday with relative distance (red when overdue), the `⛓` pill, and the
    refresh interval.
  - Task Link sessions read `via Task Link · <target note>`. `^prj` reads `project`.
  - Counted sessions read `4 tasks`, with a disclosure listing the targets and showing
    any clamp.
- **Recommendation banner.** Shown only when `⌃↵` has a recommendation, rendered from
  the existing preview model.
  - A slim timeline bar makes the window tangible: today, the level's window band, a
    tick at the rolled date, and a hollow tick at the current date.
  - A decay reads `🎲 P2 → P3 decay · …`.
  - A terminal cancel reads `⊘ Cancel: decayed past P4` in the error colour, never as a
    "roll".
  - In counted sessions it shows the batch mix (`4 tasks · 2 roll · 1 decay · 1 cancel`)
    before `⌃↵` is offered.
- **P-level strip.**
  - One segment per configured level, so it grows with the config.
  - Each segment shows the keycap, the label, and **the exact date that key will
    write**, rolled once at open through the injected random. Counted and link sessions
    show a date span instead.
  - The current level has an accent ring and the caption **re-pick**, because it resets
    the roll streak (§3.3).
  - `0 P0` reads "clear · keeps date".
- **Action list.**
  - Fixed order, with a keycap column like the decay card's.
  - Focus starts on **Schedule…**.
  - Cancel sits below a divider in the error colour.
  - Configured custom list properties appear under a **More** divider. They are reachable
    with `↑↓` or search and get no letter keys.
- **Footer.** Minimal, because the keys are printed on the rows.

### 7.3 Key Map (Card Face)

| Key | Outcome | Writes on press? | Same meaning elsewhere |
| --- | --- | --- | --- |
| `1`–`4` (up to the configured level count) | Set level N and roll **exactly the date shown** | Yes. Next/Pending targets still get the optional Work Log prompt first. | `bob capture p:N`; decay card `1`–`4`; Linear |
| `0` | Clear priority (implicit P0); `scheduled` untouched | Yes | Linear `0`; today's `⌃D` on priority |
| `⌃↵` | Take the recommendation (roll, decay, or cancel); batch-aware | Yes (unchanged) | Today's `⌃↵` |
| `⌃R` | Re-roll the banner and strip previews | No | Today's `⌃R` |
| `↵` | Open the focused row (Schedule… by default) | No | |
| `b` | **B**locked by… (the existing Depends-on stage) | No | |
| `f` | Review every… (the existing refresh stage) | No | decay card `l` (consider an `f` alias there) |
| `x` | Cancel task… (the existing cancel-reason stage; recurring refusal unchanged) | No | add `x` as an alias for Drop on the decay card |
| `⌥N` | Commit to Next / Release to Ready (an In Progress release prompts for the Work Log first) | Yes | editor `Alt+N` |
| `⌃D` | Clear the focused row's property (default focus is Schedule, so `⌃⇧P ⌃D` unschedules) | Yes | Today's `⌃D` |
| `↑↓`, `⌃N`/`⌃P` | Move over the action list | No | Today |
| `/` or any other printable | **Search mode**: today's filtered list, seeded with that character | No | Today's stage one |
| `⌫` on an empty input, or "← Back" | Return to the card from search or a nested stage | No | |
| `Esc` | Close, write nothing (every stage) | No | Today |

**Habit-safety audit.** Condensed from cld §7.4; I re-checked it against the decay card.

| Old sequence after `⌃⇧P` | New result | Verdict |
| --- | --- | --- |
| `⌃↵`, `⌃R ⌃↵` | Identical | ✅ preserved |
| `↵` on a prioritized task | Date stage | ✅ preserved |
| `pr…`, `sc…`, `dep…`, `can…`, `ref…`, `com…`, `rel…`, then `↵` | Search mode, same rows, same `↵` | ✅ preserved |
| `↵` on an unprioritized Ready/Next task (lane row was first) | Date stage, nothing written | ⚠️ safe mismatch. Use `⌥N`, or `Alt+N` directly, which is shorter. |
| `⌃D` on the first row of an unprioritized task | Unschedules (one undo step); used to be a no-op | ⚠️ visible and undoable |
| Any digit | P-level write | ✅ new; no prior habit starts with a digit |

### 7.4 Schedule Stage and One Review

The schedule stage stays the existing date stage: presets, the pinned `🎲` row, `⌃R`,
and `⌃↵`. Additions:

- **Shared grammar** (cld):
  - a bare `N` means in N days (`0` = today, `1` = tomorrow), matching `s:N`
  - `Nd`/`Nw`/`Nm` work without `+`
  - `mon`…`sun` mean the next occurrence after today
  - the old ISO, `M/D`, and `+N…` forms are unchanged
- **Resolved preview.** The preview row always shows the weekday, ISO date, distance,
  and the year when it rolls over.
- **Inline reason.** `3 waiting on API review` ↵ commits directly, because the reason
  is now known.
- **`⇧↵` skips the reason.** It applies today's empty-reason rule: `🤷` only on tasks
  that already keep a log.
- **One combined review** (cdx). A bare date + `↵` opens a single review screen instead
  of up to two serial prompts:
  - **Reason** (optional, focused).
  - **Work summary** (optional), shown only when an explicitly targeted Next/Pending task
    qualifies, with the qualifying count.
  - Effect lines: Blocked, link prune, propagation.
  - "Nothing written yet".
  - `↵` commits both fields. Blank fields follow the existing per-target rules.

Priority picks and the recommendation never prompt for a reason: the software chose the
date, as today.

### 7.5 Contexts

- **`^prj`.** The header says "project". Schedule writes YAML and propagates, and the
  effect line shows the propagation scope.
- **Plain bullet.** The strip, Schedule, and custom properties are active. Lane, Cancel,
  and Review every are dimmed. Blocked by is dimmed unless the property is already
  defined.
- **Closed task.** No banner. Lane and Cancel are dimmed.
- **Blocked `[?]`.** Lane is dimmed; the chip reads `BLOCKED · waits on N` or
  `scheduled …`.
- **Depends-On line, ledger chips, palette `edit-task-dependencies`, decay-card *Less
  often*.** These still open their stage directly. The card is skipped, and Esc closes.
- **Counted and Task Link sessions use the same keys.** Digits apply per-target frozen
  rolls through the existing batch writers, and `b` keeps add-to-all/remove-from-all.
- **Honest scope label (cdx).** For a *linked* batch, Depends on still edits only the
  **first** linked task, as today, and the label must say so. Real bulk linked
  dependency editing is a separate enhancement.

### 7.6 Visual Spec ("Beautiful" Means Restraint)

- **Size.** Width `min(600px, 92vw)`, height to content (bounded around 75vh). Use a
  picker-specific class such as `bob-task-card-modal`. **Do not** change the shared
  `bob-cnp-modal` or `FilteredPickerModal` defaults, which would regress the child-note
  and move pickers.
- **One width across the whole flow.** Keep the same width for the card and its
  date/refresh/review stages so nothing jumps. Only the vault-wide Depends-on stage may
  widen.
- **One family with the decay card.** Lift its tokens (keycap, recommended pill, muted
  unavailable, compact header) into a shared `bob-key-card-*` namespace. `bob-cnp-*`
  stays the search-picker language.
- **Theme-native colour.** Use only Obsidian CSS variables:
  - The banner uses an accent tint
    (`color-mix(in srgb, var(--interactive-accent) 12%, transparent)`) with a 3px accent
    bar.
  - Cancel and terminal decay use `--text-error`.
  - P-level hues ramp red, orange, yellow, blue at about 15% tint. Reuse the ledger chip
    colours if they exist.
  - That is one accent, one warning, one danger.
- **Type.** `tabular-nums` for dates; weekday + date + relative distance everywhere a
  date appears.
- **Motion.** Only the existing ~0.12s hover/focus fade, and none under
  `prefers-reduced-motion`.
- **Not:**
  - illustration-heavy chrome
  - a floating HUD
  - network fonts
  - raw Markdown as the primary text
  - a hard-coded dark mockup palette
- **Accessibility.**
  - `role="dialog"` with a title and a visible close button.
  - The strip is a `radiogroup`. Rows are `listbox`/`option` with `aria-keyshortcuts`.
  - Search mode is a proper combobox using `aria-activedescendant`, and selection never
    writes.
  - Focus returns to the editor on close.
- **Mobile.** The plugin is not desktop-only, so taps on rows work; keys are extras. The
  compact width is also the mobile fix.
- **Receipts.** Keep the existing notice cards: the rolled date, distance, and chips.

### 7.7 Reliability Spec

1. **Synchronous readiness.** Register card keys on the modal's `scope` and focus the
   card element **synchronously in `onOpen`**, keeping `setTimeout` only as a fallback.
   Test: dispatch `2` right after `open()` without flushing timers, and the P2 write
   must happen.
2. **Open the shell before async work.**
   - Task Link sessions must open the card shell synchronously, in a "resolving…" state,
     then fill it.
   - While resolving, the shell **swallows keys and ignores writing accelerators**; never
     buffer a digit into a write the user has not seen.
   - Test: a link session with a delayed read, where `x` must not reach the editor.
3. **No repeat or phantom writes.**
   - Ignore `event.repeat` and `isComposing`.
   - Keep the single-flight guard (the `opening` / `settled` pattern), so a double press
     writes once.
   - The opening chord can never activate.
4. **WYSIWYG writes.** Digits pass the strip's frozen preview into the existing hooks:
   - `precomputedRoll` for a single task
   - `precomputedRollByLine` for a counted session
   - `precomputedByPath` for a link session

   Repainting, search, and review never re-roll; only `⌃R` does. If a target changed
   underneath, refuse and rebuild for fresh approval (the existing stale pattern).
5. **Truthful outcomes.**
   - One gesture is one undo step for local and counted edits.
   - Cross-note link writes keep their preflight, rollback, and cleanup-warning
     semantics. Never claim global undo.
   - A digit on a Task Link target can prune today's link, and `Ctrl+Z` in the daily
     note does not undo the target-note write. The notice must say what changed.
6. **Pure, table-tested core.**
   - `planTaskCard(context)` and `resolveTaskCardKey(model, event)` are tested for every
     session × availability × key, following `planFreshnessDecayCard`.
   - Add a **DOM-stub render harness** that opens the card and every stage through
     `renderAll` at least once. Today's tests never do, which is how `bob-cli-3z`
     shipped.
7. **Performance targets** (measure on the real vault): first useful paint ≤ ~100 ms
   warm and search updates ≤ ~50 ms. Previews are bounded: one frozen roll per visible
   level per target, and no vault scans to paint the strip.
8. **Explicitly rejected:** swallowing keystrokes for a few hundred ms after an instant
   write closes the card. The habit audit makes it unnecessary, and timing hacks are a
   source of flakiness.

### 7.8 Keystrokes: Today vs Task Card

Gestures include `⌃⇧P` and a Vim count digit; a chord counts as one.

| Goal | Today | Task Card |
| --- | ---: | ---: |
| Take the recommendation (prioritized task) | 2 | 2 |
| P0 → P2 on a Ready task | 6 (`⌃⇧P p r ↵ ↓ ↵`) | **2** (`⌃⇧P 2`) |
| P2 → P3 | 6–7 | **2** |
| P-level on a Next/Pending task, skipping the Work Log | 7–8 | **3** |
| Clear priority | 4–6 | **2** (`⌃⇧P 0`) |
| Unschedule | 2–4 | **2** (`⌃⇧P ⌃D`) |
| In 3 days, no reason | 5 (prioritized) / 8 (unprioritized) | **4** (`⌃⇧P ↵ 3 ⇧↵`) |
| In 3 days, with a reason | 5 / 8 + text | **4 + text** (`⌃⇧P ↵ 3 ␣reason ↵`) |
| Cancel, no reason | 6 (`⌃⇧P c a n ↵ ↵`) | **3** (`⌃⇧P x ↵`) |
| Open Depends on | 5 | **2** (`⌃⇧P b`) |
| Review every 14 days | 8 (and currently crashes) | **5** (`⌃⇧P f 1 4 ↵`) |
| Commit Ready → Next | 2 (`⌃⇧P ↵`, when the lane row is first) | 2 (`⌃⇧P ⌥N`), or **1** with `Alt+N` |
| Counted: P2 on 4 tasks | 7 | **3** (`3 ⌃⇧P 2`) |
| Recover from the wrong stage | Esc + reopen (+ count) | **1** (`⌫`) |

Visual search matters as much as the counts. In keystroke-level-model terms, the P-level
path drops from two "find the row" operators to none, because the digits never move.

---

## 8. Parity Checklist: What Must Not Change

If any row below regresses, the redesign failed, however pretty it is.

- **Targeting.**
  - Counted N+1 semantics, skipping non-tasks, and clamp notices.
  - Counted Task Links stop at the Pomodoro boundary.
  - Task Link edits the target note.
  - Depends-On-line entry skips the card.
  - Selections and prose are refused.
- **Priority.**
  - Tasks-native stored values (`high`…`lowest`), never `P2`.
  - Per-target independent batch rolls.
  - Clearing to implicit P0 leaves `scheduled` intact.
  - `bob capture p:N` parity with card digits.
- **Recommendation.**
  - The frozen `⌃↵` preview, the decay ladder and terminal cancel, `⌃R`, and the
    composition of batch recommendations.
  - Streak classification (`🎲 roll` counts; picks, typed reasons, and `🤷` reset).
- **Logs.** Schedule, Work, and Cancel Log grammar, opt-in markers, blank-input rules,
  and the 🎲/🤷/🍂 tags that the next `⌃↵` reads.
- **Scheduling side effects.**
  - Future date → Blocked + prune today's open-Pomodoro links.
  - `^prj` YAML + propagation.
  - Unscheduling removes only propagated dates.
- **Lane.** Sticky-lane rules (`task-lanes-are-sticky`): only release, via Alt+N or this
  lane action, lowers Next/Pending. Release cleans today's links. A Pending release
  offers the Work Log.
- **Refresh.** Presets, use-default, and typed 1–365 through `setRefreshLine`.
- **Freshness.** Stamping per `docs/freshness.md` (Cancel never stamps).
- **Dependencies.**
  - CURRENT/RESULTS/BLOCKED, `Tab` marks, `＋ id` prompts, and cycle validation over the
    whole proposed batch.
  - Counted add-to-all/remove-from-all.
  - `⌃D` removes the line + field + legacy children, with recovery.
- **Cancel.** Recurring-task refusal, `[-]` + `[cancelled::]`, Cancel Log, block-ID
  prune, and Blocked-dependent recovery.
- **Safety.** Stale-preimage refusals, one undo step locally, and cross-note rollback and
  cleanup warnings. Opening, searching, highlighting, and Esc write nothing.

---

## 9. Implementation Plan and Rollout

All UI work lives in **bob-plugins** (`bob-navigation-hotkeys`). Deploy with
`bob plugins sync`, never by editing `~/bob`. bob-cli changes are docs and hint strings
only. No config schema change and no `hotkeys.json` change.

| Phase | When | Scope | Size |
| --- | --- | --- | --- |
| 0 | **Before 2026-10-05** | Fix `bob-cli-3z`: give the refresh stage proper `{keys,label}` hints, harden `renderFooter` against malformed hints, and verify the decay card's *Less often* picker. Add the DOM-stub render harness. Patch release. | small |
| 1 | During the trial | Pure `planTaskCard` + `resolveTaskCardKey`, built from the existing describers (`createBulletPropertyItems`, the counted and link variants, `describeLaneRow`, `describeRefreshRow`, `describeCancelTaskRow`, recommendation and batch previews, `withDependencyPropertyPills`). Per-level frozen previews follow `planFreshnessDecayExplicitLevelPicks` (`:3542`). Full table tests. | medium |
| 2 | During the trial, **off by default** | The card face in `BulletPropertyPickerModal`: renderer, CSS, scope keys, synchronous focus, the link-session shell, and dispatch into the existing stage methods and writers. Search mode is the existing `showPropertyStage`, seeded; `⌫` goes back. A `taskCard` setting gates it. Nav **2.0.0** (the stage-one keyboard contract changes). | large |
| 3 | During the trial, behind the same setting | Schedule-stage grammar (bare N, unsigned units, weekdays), inline reason, `⇧↵`, and the combined reason + Work summary review. | medium |
| 4 | **2026-10-19 or later** | Turn the card on by default. Add `x` (and optionally `f`) aliases to the decay card. Update docs: README; `docs/projects.md`; `docs/task-dependencies.md` §6.1; `docs/freshness.md` review outcomes; `docs/plan.md:522`; `bob ready` hint strings at `src/native/note_ready/render.rs:405,541` (e.g. `defer ⌃⇧P 1–4 · drop ⌃⇧P x · sequence ⌃⇧P b`); and the Schedule Log glossary strand, which names the keymap. Use the memory-write workflow for that strand. | small |
| 5 | Optional, later | cdx's **value results in search mode** (`p2`, `tomorrow`, `+7d`, `every 14`) and a real bulk linked-dependency editor, each with its own tests. | medium |

**Pilot.** Keep the setting for one to two weeks as the rollback, and tally 20–30 real
uses against the old paths. Watch for:

- accidental digit writes
- whether `⌃⇧P ↵` → Schedule breaks a lane habit
- whether the combined review keeps reason and work summary distinct

After that, search mode stays permanently as the classic fallback, so no rollback flag
is needed.

---

## 10. Open Questions for Bryan

1. **Do you use `⌃⇧P ↵` to commit a Ready task to Next?** On unprioritized tasks the
   lane row is first today. The new `↵` opens Schedule instead. That is safe, but it is
   a habit break, and `Alt+N` is the one-gesture replacement.
2. **Key letters.** Are `b` (blocked by), `f` (review frequency), and `x` (cancel)
   acceptable? They were chosen for habit safety first and cross-card consistency
   second.
3. **Reason default.** Keep the prompt on by default (recommended, given 79–216
   typed reasons), or make it opt-in as grk and gem proposed?
4. **Same-level digit.** Should `2` on a P2 task keep writing a deliberate re-pick that
   resets the streak (recommended; it is today's semantics, made visible), or become a
   no-op?
5. **Name.** "Task card" or "Triage"? The command ID stays `set-bullet-property`, and
   the palette label could read "Task card (set properties)".

---

## 11. Recommended Solution

**Keep `Ctrl+Shift+P`, its command ID, and every stage, planner, and writer behind it.
Replace only stage one with a compact, decay-card-family Task Card.**

- **The card:**
  - opens focused (synchronously, even for Task Links) and names the task in its header
  - shows the frozen `⌃↵` recommendation with a timeline bar
  - offers a P-level strip where `1`–`4` write the exact dates shown and `0` clears
  - lists a fixed action list: `↵` Schedule…, `b` Blocked by…, `f` Review every…,
    `⌥N` lane, `x` Cancel…
  - sends every other key to today's search list, so no old habit writes something
    different
- **Behind the card:** the schedule stage learns the capture-compatible grammar and an
  inline reason, and the two optional log prompts merge into one review.
- **Timing:** fix `bob-cli-3z` before the trial starts on Oct 5, build behind a setting
  during the trial, and switch it on from Oct 19.

The result cuts the dominant explicit gesture from about six keystrokes to two, keeps
the recommendation at two, loses no functionality by construction, and gives Bob's
busiest panel one calm, stable, theme-native face that matches the decay card.

---

## Sources

**Swarm reports (this directory):**

- `ctrl_shift_p_task_card__cdx.md`: compact action palette; parity table; combined
  review; preview freezing; outcome truthfulness; W3C focus guidance.
- `ctrl_shift_p_task_card__cld.md`: Task Card; vault usage tally; habit-safety audit;
  shared vocabulary; trial timing; `bob-cli-3z`.
- `ctrl_shift_p_task_card__grk.md`: action card in the decay-card family; category-error
  critique; requirement adjustments ADJ-1…11; Raycast and NN/G framing.
- `ctrl_shift_p_task_card__gem.md`: Fast-HUD; parity inventory; keystroke benchmark.
  Its opt-in reasons, `d`/`t`/`m` letters, plain-`↵` commit, raw-diff footer, and `src/`
  restructure are not adopted (§6).

**Code and docs (lead-verified):**

- `bob-plugins` `79d5975`, `plugins/bob-navigation-hotkeys/main.js`:
  - `FreshnessDecayCardModal` `:4383` (keys `↵ l e d 1–4 ⌥F`, repeat guard)
  - `FilteredPickerModal` `:15912` (`setTimeout` focus, `renderFooter`)
  - `promoteScheduledRowForPrioritizedTask` `:24304`
  - `BulletPropertyPickerModal` `:24359`
  - `showRefreshValueStage` `:24955–24971`
  - `set-bullet-property` `:31910`
  - `resolveLinkPickerTargets` `:32545`
  - `openLinkPicker` `:32607`
  - `openFreshnessDecayLessOftenPicker` `:35303–35394`
  - `openBulletPropertyPicker` `:36323`
- `bob-cli` `f3e64a6`:
  - `docs/projects.md`: streak classification table; Schedule-log reason prompt
  - `docs/freshness.md`: trial protection (Oct 5–18; activation 2026-10-19) and review
    outcomes
  - `docs/capture.md:100–101` (`s:<N>`, `p:<N>`)
  - `docs/plan.md:522`
  - `src/native/note_ready/render.rs:405,541`
- Vault: `.obsidian/hotkeys.json` (`Ctrl+Shift+P` → `set-bullet-property`); a read-only
  Schedule Log tally on 2026-10-03.
- Decision records: `task-lanes-are-sticky` (release only via Alt+N or the picker's lane
  row); `rotten-keeps-use-priority-decay` (decay card; Enter never cancels).
- Bead: `bob-cli-3z`, with a lead `+1` covering the decay-card *Less often* impact and
  trial timing.

**External** (cited by the reports):

- Nielsen Norman Group:
  [Accelerators](https://www.nngroup.com/articles/ui-accelerators/),
  [Heuristic 7](https://www.nngroup.com/articles/flexibility-efficiency-heuristic/), and
  [Recognition vs recall](https://www.nngroup.com/articles/recognition-and-recall/)
- [Raycast Action Panel](https://manual.raycast.com/action-panel)
- W3C: [combobox](https://www.w3.org/WAI/ARIA/apg/patterns/combobox/),
  [modal dialog](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/), and
  [WCAG 2.1.4 character-key shortcuts](https://www.w3.org/WAI/WCAG22/Understanding/character-key-shortcuts.html)
- Linear priority keys `0`–`4` ([shortcuts](https://shortcutref.com/en/linear/))
- Obsidian [`Scope` usage](https://forum.obsidian.md/t/how-to-correctly-use-scope/105155)
- Card, Moran & Newell, *The Psychology of Human-Computer Interaction* (1983), for the
  keystroke-level model
