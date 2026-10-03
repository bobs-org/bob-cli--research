# Ctrl+Shift+P should become a task action card, not a new command palette

Researcher: `grk`. Independent report. Do not treat this as the swarm synthesis.

- **Question:** Should the panel that opens on Obsidian `Ctrl+Shift+P` be migrated to a new redesigned panel that takes as few keypresses as possible, without losing current functionality, and that is intuitive, reliable, and beautiful? Critique the plan, adjust requirements where justified, and recommend a design.
- **Evidence:** bob-navigation-hotkeys 1.71.0 (`plugins/bob-navigation-hotkeys/{main.js,styles.css,manifest.json}`), vault `hotkeys.json` binding, `~/.config/bob/config.yml` `properties:`, `docs/projects.md` (picker, rolls, schedule log), `docs/task-dependencies.md` §6, `docs/freshness.md`, `docs/plan.md`, `docs/capture.md`; glossary Schedule Log / Task Dependency Link / Task Freshness; `FreshnessDecayCardModal` + `scripts/test-navigation-decision-card.cjs`; `FilteredPickerModal` / `BulletPropertyPickerModal`; Nielsen Norman Group on accelerators and heuristic 7; Raycast Action Panel; Hick–Hyman choice time.
- **Date of evidence:** bob-navigation-hotkeys **1.71.0**, decay card from 1.69.0 / handlers 1.70.0.

## Bottom line

Yes: make `Ctrl+Shift+P` faster. No: do not migrate it onto a new panel that reimplements the writers.

The chord is already the right verb. The chrome is the wrong noun. `set-bullet-property` opens `BulletPropertyPickerModal`, a subclass of the giant child-note **command palette** (`bob-cnp-modal`, up to 960×840), with the search box focused, for a **closed set of about six actions**. That is a category error. The in-product design that already solves “fewest keypresses on a closed set” is the review **decision card** (`FreshnessDecayCardModal`, ~560px, letter/number accelerators, Esc writes nothing).

**Recommended solution:** keep every writer, planner, counted/link session, and nested stage. Replace only the *stage-1 chrome* with a compact **task action card** in the decay-card family:

1. Stop focusing the search box on open (this is the single highest-leverage change).
2. Put visible accelerators on every row, matching the decay card: `1`–`4` apply P-levels immediately, `n` lane, `s` scheduled, `d` depends, `r` refresh, `x` cancel, `^↵` recommended roll, `0` / `^D` clear.
3. Size it like the decay card, with a status header that shows the task you are about to rewrite.
4. Keep the existing filtered picker for stages that actually have many values (dates, vault-wide Depends on).
5. Make Esc mean *back* inside the modal, and make the schedule-reason prompt **opt-in**.

The existing test files stay the acceptance suite. A greenfield panel is how this feature dies in review.

## Is this a good idea?

### What is right in the request

- **The chord is a daily driver.** Vault `hotkeys.json` binds `bob-navigation-hotkeys:set-bullet-property` to `Ctrl+Shift+P`. Capture’s `p:<N>` is defined as the same P-level as “press `Ctrl+Shift+P` and choose the `P2` row” (`docs/projects.md`). Morning review copy points at it for defer / drop / refresh (`docs/freshness.md`, `docs/plan.md`). Frequency is the correct reason to optimize keypresses.
- **One contextual chord is better than a new global keymap.** Bryan’s nav map is already dense (Alt+N lane, Alt+F keep, Ctrl+Shift+M move, Ctrl+Shift+Enter link, Ctrl+Shift+J/K jump, Ctrl+Enter roll). Dumping each picker row into its own chord would fight NN/G’s shortcut guidance (limit modifiers; one- and two-key accelerators beat stacked chords) and would lose counted `N<Ctrl+Shift+P>` and Task-Link sessions.
- **Functionality must not regress.** The picker is not a label chooser. It is the interactive front of schedule logs, work logs, cancel logs, priority rolls and decay, future-date Blocked + today’s-link prune, `^prj` YAML, vault-wide Depends on, freshness stamps, lane commit/release, and stale-guarded counted batches. Those writers are the product.
- **Beautiful belongs in the brief.** The current panel inherits child-note-picker chrome built for “search a vault of files.” A six-row list inside a 960×840 modal with a focused search box and a footer of `↑↓ ^N ^P ↵ ^D ^↵ ^R esc` looks like a tool the user has not finished. The decay card already shows what “keyboard-first and beautiful” means in this codebase.

### What is wrong in the request as written

- **“Migrate to a new redesigned panel” overstates the cut.** `plugins/bob-navigation-hotkeys/main.js` is **48,384 lines**. `scripts/test-navigation-hotkeys.cjs` alone has **511** tests; roll/decay, stamps, dependencies, and the decision card add hundreds more. The stage machine (`properties` → `value` / vault Depends on → `reason` / `blockid` / `cancel-reason` / `lane-release-reason` / `schedule-work-log`) is battle-tested. Rebuilding it behind a new DOM is a multi-month epic whose likely outcome is a pretty shell with silent writer bugs. The chrome is maybe two hundred lines of `onOpen` / `handleKeydown` / CSS.
- **“As few keypresses as possible” is unbounded.** Flattening every optional prompt (schedule reason, In-Progress work summary, cancel reason, block-id) would lose the logs the rest of the system reads (decay streak classification, unlink summaries, cancel history). The bound should be: *one key after the chord for the trained closed set; never more stages than today; optional prompts are skippable or opt-in.*
- **The panel is already a “redesign” of Obsidian’s command palette.** It is `FilteredPickerModal`, the same class as child notes, task moves, Pomodoro moves, yank-path, and link candidates. Treating Ctrl+Shift+P as “we need a new modal primitive” ignores that the primitive is right for *search-heavy* pickers and wrong for *this* one.
- **Discovery and speed are in tension, and the current UI picked the slow default.** Autofocus on the filter (`FilteredPickerModal.onOpen` → `this.inputEl.focus()`) makes letter accelerators impossible: `2` becomes a query, not P2. Power-user speed requires the card to start in *command mode*, with `/` as the filter accelerator. That is how Raycast’s Action Panel and the decay card both work.

### Would I take a different approach?

Yes. I would **not** migrate onto a new panel. I would **re-skin stage 1 as a task action card** that shares visual language with `FreshnessDecayCardModal`, leave every writer on `setBulletPropertyValue` / the counted and link planners / the Depends-on stage, and spend the keypress budget on (a) accelerators, (b) Esc-back, (c) skipping the extra Enter on explicit dates.

I would also **not** push these actions into Obsidian’s own command palette. Palette commands have no counted session, no Task-Link resolution, no current-value pills, and no `^↵` preview. The dedicated command `Edit task dependencies` already exists with no default hotkey (`docs/task-dependencies.md` §6.1); that is the right amount of palette surface.

## Requirement adjustments

Call-outs the lead should adopt or explicitly reject.

| ID | Adjustment | Why it is justified |
| --- | --- | --- |
| **ADJ-1** | Do **not** replace writers, planners, or the stage machine. Replace stage-1 chrome and key dispatch. | 48k-line plugin, 511+ tests, byte-parity with `bob capture` / hooks. The failure mode of a “new panel” is a second writer. |
| **ADJ-2** | Bound “fewest keypresses” as: **one key after `Ctrl+Shift+P` for the closed trained set**; nested search UIs only when the value set is large (dates, vault tasks). | Unbounded minimization deletes Schedule Log / Work Log / Cancel Log, which decay and review still parse. |
| **ADJ-3** | **Do not autofocus the search input** on stage 1. `/` (or `i`) opens filter mode. | Letter accelerators cannot coexist with a focused text field. This is the enabling change. |
| **ADJ-4** | **Unify accelerators with the decay card:** `1`–`4` are P-levels that write immediately; Enter activates the selected row; `^↵` remains recommended roll; Esc writes nothing on the card. | Muscle memory already exists from Alt+F-at-limit (`docs/projects.md` “Not now / 1–4”). Two UIs with two P-level languages would be the unreliability. |
| **ADJ-5** | Size the panel like the decay card (**~560–640px**, height to content), not `bob-cnp-modal`’s 960×840. Do not change the child-note / move pickers. | Shared `FilteredPickerModal.onOpen` adds `bob-cnp-modal` to every subclass. The property picker is a 6-item inspector trapped in a file switcher’s frame. |
| **ADJ-6** | **Esc in a nested stage goes back** to stage 1 (discarding any pending write). Esc on stage 1 dismisses. Esc in filter mode leaves filter. | Today Esc always closes the modal. A wrong property choice costs a full reopen. Raycast Action Panel uses Esc as back. Reason-stage “Esc cancels the date too” is preserved by discarding pending state on the way back. |
| **ADJ-7** | Make the **schedule-reason prompt opt-in** (Shift+Enter from the date row, or a `?` after the date). A plain date pick writes immediately. If the task already keeps a Schedule Log, append `🤷 no reason given` — the same empty-Enter rule as today. | Every explicit date currently costs an extra Enter even when the user has nothing to say (`docs/projects.md` “Schedule-log reason prompt”). Priority picks already skip the prompt because the software chose the date. Opt-in keeps log completeness without taxing the common path. |
| **ADJ-8** | Keep **Alt+N, Alt+F, Ctrl+Shift+M, Ctrl+Shift+Enter** as dedicated chords. The card is the overflow inspector + mnemonic launcher, not their replacement. | Those chords are already one-press. Duplicating them as the only path would slow the highest-frequency non-property actions. |
| **ADJ-9** | Do **not** add one Obsidian command per row. | Counted/link context, current-value display, and `^↵` preview do not survive the palette. |
| **ADJ-10** | Do **not** bundle a `main.js` extract with the redesign. Optional later, own PR. | Reviewability. The redesign is CSS + stage-1 keydown + a compact `onOpen`. |
| **ADJ-11** | Keep **Vim counts** as `N<Ctrl+Shift+P>` *before* the modal. Inside the card, digits `1`–`4` are P-levels, never a second count. | Counts already mean “this task plus the next N.” Reusing digits inside the modal would collide with ADJ-4. Refresh `14` is `r` then `14`, or `/` then `14`. |

## What is already true

| # | Fact | Evidence |
| --- | --- | --- |
| E1 | Vault binds `bob-navigation-hotkeys:set-bullet-property` to `Ctrl+Shift+P`. The plugin command itself declares no default hotkey. | `~/bob/.obsidian/hotkeys.json`; `addCommand({ id: "set-bullet-property", name: "Set bullet property" })` in `main.js` ~31909 |
| E2 | Stage 1 is a filtered list built from `config.yml` `properties:` (`scheduled`, `dependsOn`, `priority`) plus pinned **lane**, **refresh**, and **Cancel** rows. Defined properties sort first. Prioritized tasks promote `scheduled` so `Ctrl+Shift+P` then `Ctrl+Enter` rolls with no navigation. | `createBulletPropertyItems`; `showPropertyStage`; `promoteScheduledRowForPrioritizedTask`; `~/.config/bob/config.yml` |
| E3 | The modal subclasses `FilteredPickerModal`, which always applies `bob-cnp-modal` (width `min(92vw, 960px)`, height `min(82vh, 840px)`) and focuses search. | `FilteredPickerModal.onOpen`; `styles.css` `.modal.bob-cnp-modal` |
| E4 | Nested stages already in the machine: `properties`, `value` (dates / P-levels / refresh presets), vault Depends on, `blockid`, `reason`, `cancel-reason`, `lane-release-reason`, `schedule-work-log`. | `this.stage =` assignments in `BulletPropertyPickerModal` |
| E5 | Stage-1 keys today: arrows / `^N` `^P`, Enter, `^D` delete, `^↵` recommended roll, `^R` re-roll, Esc dismiss, type-to-filter. No letter mnemonics. | `BULLET_PROPERTY_STAGE_ONE_HINTS`; `handleKeydown` |
| E6 | Date presets: Today, Tomorrow, In 2/3 days, This Saturday/Sunday, Next Monday, In 1 week, In 2 weeks, In 1 month, plus typed `+3d` / `6/24` / ISO. Refresh presets: 2, 3, 7, 14, 30, 90, 180, 365, plus “use default” and typed 1–365. | `createBulletPropertyDateItems`; `REFRESH_ROW_PRESET_DAYS` |
| E7 | Priority write is already a one-shot from the *value* stage: choosing P1–P4 writes `[priority::]` + rolled `scheduled` + deterministic 🎲 Schedule Log, no reason prompt. `p:<N>` in `bob capture` is defined as the same row. Ctrl+D on the priority row clears to implicit P0 without touching `scheduled`. | `docs/projects.md` “Priority property and scheduled rolls” |
| E8 | `Ctrl+Enter` on `scheduled` is already the fewest-key path for a prioritized task (chord + chord). Recommendation is frozen at open; `^R` re-rolls. Counted and Task-Link sessions use batch recommendations. | `docs/projects.md` “Recommended roll”; `priorityRollRecommendation` comments |
| E9 | Explicit date picks always open a reason stage. Empty Enter writes the date; if a Schedule Log already exists it records `🤷 no reason given`; Esc cancels the date too. Pending/Next scheduling may then open a Work Log stage. | `docs/projects.md` “Schedule-log reason prompt”; `showScheduleReasonStage`; `showSchedulingWorkLogStage` |
| E10 | Depends on is a full vault-wide picker (CURRENT / RESULTS / BLOCKED, Tab marks, `⛓ N · M open` pill). Cursor on a Depends-On line **skips stage 1**. Ledger chips and `Edit task dependencies` reuse the same stage. | `docs/task-dependencies.md` §6 |
| E11 | Lane commit/release is also Alt+N. In-Progress release still prompts for an optional Work Log. Refresh writes through `api.freshness.setRefreshLine` (also stamps). Cancel is pinned last, refused on recurring tasks. | `describeLaneRow`; `toggle-task-lane`; `docs/freshness.md` |
| E12 | The review **decision card** is a second, smaller, accelerator-first modal in the same plugin: Keep / Not now / Less often / Reword / Drop / P1–P4, Esc writes nothing, keys shown on the row. | `FreshnessDecayCardModal`; `.modal.bob-decay-card-modal` width 560px; `docs/projects.md` |
| E13 | `FilteredPickerModal` is also the chrome for child notes, task-move, Pomodoro move/rename/merge, yank-path, and link candidates. Changing its default size or autofocus would regress those flows. | subclasses at `ChildNotePickerModal`, `TaskMoveDestinationPickerModal`, … |
| E14 | Entry points the redesign must keep: `#task` line, Depends-On line (skip to deps), dedicated Task Link (edits the linked task), `N<Ctrl+Shift+P>` counted, counted Task Links clamped at the Pomodoro, `^prj` YAML scheduled, chip `＋`/`×`, palette `edit-task-dependencies`. | README; `docs/task-dependencies.md` §6.1; `docs/projects.md` |

### Keystroke inventory (today vs action card)

Counts are *keys after the chord*, assuming a trained user. `Ctrl+Shift+P` itself is one chord in every row.

| Goal | Today (typical) | Action card | Notes |
| --- | --- | --- | --- |
| Recommended roll on a prioritized task | `^↵` (1) | `^↵` (1) | Already optimal; keep. |
| Apply P2 | filter `pr` + ↵ + ↵ on P2, or arrows (3–6) | `2` (1) | Matches decay card and `p:2`. |
| Clear priority | arrows to priority + `^D` (2–4) | `0` or `^D` on strip (1) | Implicit P0; does not unschedule. |
| Lane commit (Ready) | ↵ if lane is first (1), else arrows | `n` (1) | Alt+N remains the zero-panel path. |
| Schedule tomorrow | nav to scheduled + ↵ + nav Tomorrow + ↵ + ↵ skip reason (4–7) | `s` then `tom`/↵, **no reason stage** (2–3) | ADJ-7. Shift+Enter still logs a reason. |
| Refresh 14d | nav refresh + ↵ + nav 14 + ↵ (4–6) | `r` then `14` ↵ (2) | Digits on the card are P-levels, so 14 is a value-stage query. |
| Depends on | nav + ↵, or type `dep` (2–4) then search | `d` then type (1 + search) | Search UI is the right tool here. Skip-from-Depends-On-line stays. |
| Cancel | nav to last row or type `cancel` + ↵ + ↵ skip reason (3–6) | `x` then ↵ to skip reason (1–2) | Destructive; keep the optional reason. |
| Wrong property, recover | Esc + reopen chord (2 + chord) | Esc back to card (1) | ADJ-6. |

The win is not shaving the roll path. The win is turning **every other daily path** from a filter-and-stage hunt into a labeled key.

## Alternatives considered

### A. Greenfield new panel (the request, literal)

Rebuild the UI from scratch, porting functionality across.

**Reject as the implementation strategy.** The writers are the risk. A new DOM that calls the same `setBulletPropertyValue` / `applyLaneToggleFromPicker` / `openLinkedDependencyStage` / `applyRefreshIntervalFromPicker` is fine; a new write path is not. The request’s “don’t lose functionality” clause is only credible if the acceptance tests are the files that already exist.

### B. Keep the command palette, add aliases (`p2`, `tom`, `x`)

Raycast-style: keep search focused, make queries first-class commands.

**Reject as the primary model; keep as `/` filter mode.** It preserves today’s muscle memory and is excellent for dates (`tom`, `+3d`). It fails the “one key” bar for P-levels and lane: you still type then Enter, and it does not show current state as well as a card. NN/G accelerators are supposed to be *visible next to the command*. A blank search box hides them.

### C. More global hotkeys (`Ctrl+Shift+1`…, `Ctrl+Alt+P`, …)

**Reject.** The keymap is already crowded. NN/G: fewer modifiers, show shortcuts in the menu, accelerators are *alternates* not the only path. Counted sessions and Task-Link mode have nowhere to hang extra chords.

### D. Radial / mouse toolbar / always-on inspector

**Reject.** Bryan is Vim-normal in the editor. Fitts’s-law pointer travel is the opposite of this brief. An always-on inspector fights note reading.

### E. Put every action in Obsidian’s command palette

**Reject.** No session, no pills, no roll preview, no Depends-on skip, no `^prj` targeting. Palette is for launching; this is for inspecting-and-writing the task under the cursor.

### F. Action card + keep writers (recommended)

Stage 1 becomes a compact, unfocused, labeled card. Value stages that search many things keep `FilteredPickerModal` behavior (search focused, current date/deps chrome). Nested prompts remain, with ADJ-6/7. Same class (`BulletPropertyPickerModal`) so every existing `picker.stage` test still addresses the object it knows.

This is also how Raycast itself is factored: **Root Search** for large spaces, **Action Panel** for the closed set on the current item, shortcuts printed on the right, type-to-filter only once the panel is open.

## Recommended solution

### Shape

One modal, two faces:

| Face | When | Chrome | Focus |
| --- | --- | --- | --- |
| **Task action card** | Stage 1 (`properties`), and the skip-to-deps case’s parent if we ever show it | Decay-card family, ~560–640px, height to content | The card / selected row, **not** an input |
| **Value picker** | Dates, refresh presets, vault Depends on, block-id, optional reason / work-log | Existing `bob-cnp-*` (or a slightly narrower variant) | Search input, as today |

Do not invent a third visual language. Lift the decay-card tokens (key glyph, recommended pill, muted unavailable, compact header) into a shared `bob-key-card-*` namespace used by both `FreshnessDecayCardModal` and stage 1 of `BulletPropertyPickerModal`. `bob-cnp-*` stays the search-picker language.

### Stage-1 layout

```
┌──────────────────────────────────────────────────────────────┐
│  ⬡  Ship the thing                          Ready · P2       │
│     sase.md  ·  Fri 2026-10-17  ·  ⛓ 2 · 1 open  ·  ⟳ 3d    │
│     ^↵  P2 roll to 2026-10-28 · in 25d · 8–30 · 1/1          │
├──────────────────────────────────────────────────────────────┤
│  n    Commit to Next                 lane · Ready → Next     │
│  s    Scheduled                      2026-10-17 · Fri        │
│                                                              │
│  Priority                                                    │
│     [0 P0]   [1 P1]   [2 P2 current]   [3 P3]   [4 P4]       │
│      clear    2–7d         8–30d        31–90d    91–365d    │
│                                                              │
│  d    Depends on                     ⛓ 2 · 1 open           │
│  r    Refresh every                  default 7d              │
│  x    Cancel task                    optional reason         │
├──────────────────────────────────────────────────────────────┤
│  / filter   ↵ open   ^↵ roll   ^R re-roll   ^D clear   esc   │
└──────────────────────────────────────────────────────────────┘
```

Design notes that make it *beautiful* rather than a restyled list:

- **Status header is the task.** Title, note, lane chip, P-level, scheduled weekday+date, dep pill, freshness mark. Counted sessions replace the title with `3 tasks` / `↗ Tasks · Ship it · 2 links` (existing subtitle helpers). This is what the giant palette never did: tell you *what you are about to rewrite* without reading the row pills.
- **Priority is a strip, not four rows and not a second stage.** `1`–`4` write immediately with the same deterministic 🎲 log as today’s value-stage pick (E7). `0` clears. The strip is the discoverable form of the decay card’s 1–4.
- **Recommended roll stays a third line on the header (and on `s`)**, already designed (`.bob-cnp-roll-preview`, loud when selected). Do not hide it behind the date stage.
- **Cancel is last, red, labeled `x`.** Matches “drop” on the decay card (`d` there is Drop; here `d` is Depends, so cancel cannot steal `d`). Recurring stays unavailable with the existing notice.
- **Lane uses `n`**, the same letter as Alt+N. In-Progress still opens the Work Log stage (information we do not have a deterministic stand-in for).
- **Footer is short.** Row glyphs carry the accelerators (NN/G: show the shortcut next to the command). The current footer tries to teach arrows, emacs, Enter, delete, roll, re-roll, and Esc at once.

### Key dispatch (stage 1, filter closed)

| Key | Action | Writes? |
| --- | --- | --- |
| `1`–`4` | Apply that P-level to the session (single / counted / link), same as choosing the value-stage row | Yes, immediately |
| `0` | Clear priority (`^D` on the priority property) | Yes |
| `n` | Lane commit, or open the In-Progress Work Log stage | Yes, or prompt |
| `s` | Open scheduled value picker | No |
| `d` | Open Depends on (or the linked-task stage in link mode) | No |
| `r` | Open refresh value picker | No |
| `x` | Open cancel-reason stage (refuse recurring, as today) | No |
| `^↵` / `Ctrl+Enter` | Recommended roll / decay / cancel, frozen at open | Yes |
| `^R` | Re-roll the previewed date | No |
| `^D` | Delete the *selected* property (scheduled YAML on `^prj`, Depends-On line, priority, …) | Yes |
| `↵` | Activate the selected row (same as today) | Depends |
| `/` or `i` | Filter mode: focus search, existing `filterItem` plus aliases (`p2`, `tomorrow`, `cancel`, `refresh`) | No |
| `Esc` | Dismiss | No |
| arrows, `^N` `^P` | Move selection | No |

Filter mode: letters go to the query; `Esc` returns to command mode without closing; Enter runs the selected row. This is ADJ-3 plus a compatibility hatch for anyone who currently types `pri` / `can` / `dep`.

Value stages keep today’s handleKeydown (date typing, `^R`, Tab marks on Depends on). On date/refresh stages, **do** focus search: that set is large and type-to-value is the fewest keys (`tom`, `+3d`, `14`).

### What must not change (acceptance)

If a row below turns red in review, the redesign failed, however pretty it is.

- Counted `N<Ctrl+Shift+P>` and Task-Link sessions, including clamp notices and “via Task Links”.
- Depends-On line skips stage 1; chips and `edit-task-dependencies` still open the vault stage.
- Vault Depends on: CURRENT/RESULTS/BLOCKED, Tab marks, `#hide` ranking, stale reopen, `＋ id` prompts, `^D` deletes the line + field + legacy children with recovery.
- `^prj`: `scheduled` writes YAML and propagates; other properties stay inline; Ctrl+D unschedules the project date.
- Future `scheduled` → Blocked + prune today’s open Pomodoro links; due recovers as today.
- Priority → Tasks-native values (`high`/`medium`/`low`/`lowest`), never `P2` in the field.
- Decay ladder, frozen recommendation, `^R`, counted/link batch composition, recurring-cancel refusal.
- Schedule Log / Work Log / Cancel Log grammar, including 🎲 / 🤷 / 🍂 classification that the next `Ctrl+Enter` reads.
- Freshness: property/lane/depends/delete/refresh writes still `stampLine` / `setRefreshLine`; Cancel still does not stamp (`docs/freshness.md` table).
- Stale-content guards: “a counted task changed while the picker was open.”
- Notices with the existing chips (Blocked, recovered, mixed, plan budget suffix where already present).
- `bob capture p:<N>` parity with card `1`–`4`.

### Reliability

- **One undo step per commit**, as today (composed batch for counted roll/decay/cancel).
- **Previewed dates are frozen at open**; accelerators that roll must reuse `priorityRollRecommendation` / counted/link batches, not roll a fresh date at keydown. `2` on a task that already has P2 still rolls a new window (today’s value-stage behavior) unless we explicitly decide “same level is a no-op” — I would **keep the write** and the 🎲 log, because that is how people bump a P2.
- **Unavailable states are visible and inert**, like the decay card’s muted rows (recurring cancel, unencodable path, mixed counted property that cannot delete). Do not bind an accelerator that silently no-ops; show the same Notice the row would have shown.
- **Opening chord must not activate.** The decay card already ignores repeat Alt+F so the triggering press cannot approve. Stage-1 digits need the same `event.repeat` guard so a stuck key cannot apply P2.

### Implementation cut (so this is actually shippable)

Work lives in **bob-plugins** (`bob-navigation-hotkeys`). bob-cli docs (`docs/projects.md`, `docs/task-dependencies.md` §6, `docs/freshness.md` keymap table) update in the same change set so the keymap page matches the card. No config.yml schema change for v1; P-levels still come from `properties.priority.levels`.

**Phase 1 — chrome and keys (the actual feature).**

- Compact modal class on stage 1 only (`bob-key-card-modal` / reuse decay-card width).
- Header with current lane / P / date / deps / freshness.
- Do not focus search; `/` does.
- Accelerator dispatch in `BulletPropertyPickerModal.handleKeydown` when `stage === "properties"` and filter is closed.
- Esc-back from nested stages (`showPropertyStage({ clearQuery: false })` already exists and is used on failed opens).
- Tests: new cases next to `test("Ctrl+Shift+P shows a pinned lane row…")` and the decision-card key tests (`scripts/test-navigation-decision-card.cjs` is the pattern: keydown → writer → Esc writes nothing). Existing 511 hotkeys tests stay green.

**Phase 2 — keypress cuts that touch prompts.**

- ADJ-7: date pick writes without the reason stage; Shift+Enter / `?` keeps it. Empty-log completeness (`🤷` when a log already exists) still runs inside the writer, not the UI.
- Priority strip in the card so `1`–`4` do not even open a value stage.
- Search aliases in filter mode (`p2`, `tomorrow`, `cancel`, `refresh`).

**Phase 3 — polish.**

- Date-stage letter hints (`t` today, `m` tomorrow) only if they do not fight ISO / `+3d` typing. Easy to get wrong; ship only with tests against `createBulletPropertyTypedDateItem`.
- Shared CSS extract of decay-card + action-card tokens. Optional `main.js` split: **not** in this epic (ADJ-10).

Deploy with `bob plugins sync` as usual. No vault `hotkeys.json` change.

### What I would measure after landing

Because this is a daily chord, ship behind nothing — but watch for a week:

- Accidental P-level writes from leftover filter-mode expectations (mitigation: `/` hint in the footer, first-week Notice optional, **not** a permanent tutorial).
- Esc-back vs “Esc means die” muscle memory on the reason stage. Keep discarding pending writes (nothing hits disk until confirm), so the worst case is “I have to pick the date again,” which is still cheaper than today’s full reopen.
- Whether `n` vs Alt+N splits lane use. That is fine; both must keep working.

## Critique of “beautiful”

Beautiful here is **restraint**:

- Theme-native CSS variables, already the rule in `styles.css` (“built on Obsidian CSS variables so it stays theme-native in light/dark”).
- Compact, height-to-content, no empty acreage.
- One accent (roll / current), one warning (decay), one danger (cancel). The decay card already uses orange recommended + muted unavailable; copy that, do not invent a fourth palette.
- Tabular dates, weekday, relative offset — the scheduled row already has this; promote it to the header.
- Motion stays at the existing 0.12s hover, gated on `prefers-reduced-motion`.
- Mobile: plugin is not desktop-only (`isDesktopOnly: false`). Taps on rows still work; accelerators are extras. Compact width is the mobile fix the 960px palette never had.

A bespoke illustration-heavy UI, a floating HUD, or a non-Obsidian font stack would fight every other Bob modal and fail “intuitive.”

## Sources

### In-tree (authoritative for behavior)

- `plugins/bob-navigation-hotkeys/main.js` — `FilteredPickerModal`, `BulletPropertyPickerModal`, `FreshnessDecayCardModal`, stage machine, `handleKeydown`, `createBulletPropertyItems`, date/refresh presets.
- `plugins/bob-navigation-hotkeys/styles.css` — `.modal.bob-cnp-modal`, `.bob-decay-card-*`, `.bob-cnp-roll-preview`, property pills.
- `plugins/bob-navigation-hotkeys/manifest.json` — v1.71.0.
- `scripts/test-navigation-hotkeys.cjs` (511 tests), `test-navigation-roll-decay.cjs`, `test-navigation-decision-card.cjs`, `test-navigation-dependencies*.cjs`, `test-navigation-stamps.cjs`.
- `docs/projects.md` — picker, P-levels, `Ctrl+Enter` ladder, schedule-log reason prompt, decision card.
- `docs/task-dependencies.md` §6 — Depends on stage entry points and chrome.
- `docs/freshness.md` — which picker rows stamp.
- `~/.config/bob/config.yml` — `properties:` list the card must still honor.
- `~/bob/.obsidian/hotkeys.json` — `Ctrl+Shift+P` → `set-bullet-property`.

### External (authoritative for the interaction model)

- Nielsen Norman Group, [Accelerators Maximize Efficiency in User Interfaces](https://www.nngroup.com/articles/ui-accelerators/) (2024): accelerators are *additional* paths for frequent tasks; they must be discoverable.
- Nielsen Norman Group, [Flexibility and Efficiency of Use (Heuristic 7)](https://www.nngroup.com/articles/flexibility-efficiency-heuristic/): faster expert path plus slower guided path; show shortcuts next to commands.
- Nielsen Norman Group, [UI Copy: Command Names and Keyboard Shortcuts](https://www.nngroup.com/articles/ui-copy/): prefer one- and two-key shortcuts; limit stacked modifiers.
- Hick–Hyman choice reaction: unlabeled growth in *n* is costly; **labeled access keys** (the decay card’s `1`–`4`, `L`, `E`, `D`) bypass visual search. Grouping beats deletion ([Laws of UX / Hick’s Law](https://www.nngroup.com/articles/split-buttons/) also: print shortcuts on the menu; keep menus under ~10–12).
- [Raycast Action Panel](https://manual.raycast.com/action-panel): closed contextual actions, shortcuts on the right, type-to-filter once open, Esc back, primary action vs full panel — the same split as “card vs date/deps picker.”

## Recommendation (one paragraph)

Keep `Ctrl+Shift+P` as the one contextual chord, keep every writer and test, and **stop presenting a six-action inspector as a vault-scale command palette**. Stage 1 becomes a decay-card-family **task action card**: no search focus, visible accelerators aligned with the review card (`1`–`4` apply P-levels now), compact header that names the task, Esc-back, opt-in schedule reasons. Dates and Depends on keep the filtered picker, because those value sets are actually large. That is the design that is faster, still complete, and already looks like Bob.
