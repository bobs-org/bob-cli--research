# Idle Pomodoro Agenda in Bob Mac Capture — Research, Critique, and Recommended Design

*Researcher: cld · 2026-10-09 · repos: bob-cli (Rust), bob-mac-capture (Swift, linked)*

## 0. TL;DR

- **Yes, build it.** The capture panel is the Bob surface Bryan opens most. An empty
  panel is wasted space, and Today is already defined as "the Task Links under today's
  open Pomodoros" (`decisions:today-is-read-from-the-ledger`). Showing that ledger in the
  idle panel turns the blank bar into a "Now / Next / Later" view at almost no runtime
  cost.
- **Cache key adjustment.** Keying the cache on the daily file alone is unsafe. Task
  bodies live in `sase.md`, `bob.md`, and so on. A Work Log entry added there changes
  nothing in the daily file, so a daily-file key would show stale content. The cache
  must be invalidated by **any vault change**, and the app already has an FSEvents
  watcher on the vault root. The thing worth caching is the **decoded snapshot and its
  fold plan** in the app. Neither the `bob` spawn nor the daily-file read is worth
  caching: the endpoint costs about 10 ms, runs off the hotkey path, and replaces a
  spawn the app already makes on every show.
- **Fold adjustment.** Choosing one global fold level is not enough. On 45 real days,
  the requested design (full, then no-logs, then one line, applied to every task at
  once) still has to **scroll on 19 of 45 mornings** on a 14" laptop. I recommend a
  **focus gradient** instead:
  - Fold the farthest Pomodoros first, in Bryan's order: logs, then one line.
  - Add a fourth tier: **one line per Pomodoro**.
  - Fold Now and Next last.
  - Result in simulation: Now and Next keep at least the no-logs view on **43–45 of 45
    days**, and scrolling is needed on at most 1 day.
- **Window adjustment.** Grow the window **down from a fixed eye line**. Today the
  panel is re-centred on every show (`panel.center()`), so a tall agenda would push the
  editor up the screen by a different amount each day. Pinning the top costs very
  little room for Now and Next (43/45 vs 44/45 days in the simulation).
- **Thin-client split** (`decisions:mac-capture-is-a-thin-client`):
  - **bob owns meaning.** It decides which entries are running, next, and later. It
    supplies the `=x` and `=` numbers, resolves Task Links to task blocks, and flags
    Work Log and Schedule Log subtrees. All of this comes from one additive flag:
    `bob capture-pomodoros --tasks/-t -f json`.
  - **The app owns pixels.** It measures rows, plans folds, and renders them.

---

## 1. What exists today (facts)

### 1.1 Mac app (bob-mac-capture)

| Fact | Where |
|---|---|
| One `NSPanel` is built at launch (`prewarm()`) and reused; the hotkey path is "a pre-warmed non-activating `NSPanel`; subprocess work is kept off that path". | `AppDelegate.swift:80-87`, `CapturePanelController.swift:249-251, 405-427`, `README.md:288-289` |
| `show()` runs `prepareForPresentation()`, then `refreshCurrentPomodoroTaskLinkCount()` (spawns `bob capture-pomodoros`), then `replayLatestContentMetricsForPresentation()`, then `makeKeyAndOrderFront`. `showCapturePanel()` also spawns `capture-targets`. **So every show already pays two background spawns.** | `CapturePanelController.swift:259-275`, `AppDelegate.swift:587-599` |
| An empty draft sets `previewState = .idle`, and the auxiliary region is gated on `previewState != .idle`. The idle panel is just the editor ("Type to capture…") and the footer ("Ready"). | `CapturePanelModel.swift:744-755`, `CapturePanelView.swift:434-443, 565-568, 677, 775-783` |
| Documented design principle: "A fresh popup is a compact, Spotlight-like bar — a one-line editor plus persistent footer actions, no empty preview placeholder, no dead space." **This feature changes that principle; update the README.** | `README.md:290-291` |
| Height is measured by SwiftUI (`onGeometryChange`) and applied by AppKit `setFrame`. The screen limit is `visibleFrame − 2×24`. The auxiliary region is a `ScrollView`, so content beyond the screen limit scrolls. | `CapturePanelView.swift:163-238, 472-494, 596-618`, `CapturePanelController.swift:328-386`, `CapturePanelWindowSizer.swift:17-69` |
| **On every show the panel is re-centred**: `pendingRecenter = true`, then `panel.center()`. AppKit's `center()` puts the window "slightly above center vertically" (empirically about ¼ to ⅓ of the leftover space above). A taller panel therefore starts higher on screen. | `CapturePanelController.swift:314, 373-376`; Apple `NSWindow.center()` docs |
| Width is user-resizable; height is locked to measured content. | `CapturePanelController.swift:282-287` |
| Caches: `CaptureTargetsCache` (last good response, marked stale on failure), picker indexes per session, Refs snapshot on disk, and others. The only watcher is `VaultTargetWatcher`, an FSEvents stream on the vault root. It uses 0.3 s latency plus a 0.3 s trailing debounce, ignores paths, and any event triggers a refresh. | `CaptureTargetsCache.swift:22-69`, `VaultTargetWatcher.swift:13-111`, `AppDelegate.swift:562-585` |
| The app already decodes `capture-pomodoros` (`CapturePomodorosResponse`), but only to read `task_link_count` of the current entry for the close-comma typing aid. | `CaptureModels.swift:4849-4927`, `CapturePanelModel.swift:670-699` |
| Reusable presentation pieces: <br>• `CaptureEditorPalette.taskStatus` (status → SF Symbol + colour) <br>• `CapturePomodoroLineTokens` (byte-preserving tokenizer for Pomodoro and task rows) <br>• `BlockDiffCard` (3 pt rail, indent guides) <br>• `CapturePomodoroBlockPresentation` glyphs: `play.circle.fill` (running), `circle.dashed` (queued) <br>• Pink is the `pomodoroStart` colour; quaternary capsules are used for number badges. | `CaptureEditorPalette.swift:16-50`, `CapturePomodoroLineTokens.swift:24-108`, `BlockDiffCard.swift`, `CapturePomodoroBlockPresentation.swift:12-93` |
| Prior latency target: warm hotkey to focused editor **p50 < 50 ms, p95 < 100 ms**, and pop-up latency equal to "a single `orderFrontRegardless()` — one frame". | `research:202608/bob_mac_capture_replacement/bob_mac_capture_replacement.md` §4.8 |

### 1.2 bob-cli

| Fact | Where |
|---|---|
| Daily file: `BOB_DAY_FILE`, else `<bob>/YYYY/YYYYMMDD.md` from `BOB_NOW` or the local clock. There is no early-morning day boundary. | `src/native/pomodoro.rs:251-256`, `src/native/env.rs:337-367` |
| `capture_pomodoros::scan()`: column-0 `- [?]` entries. A `()` body is a placeholder. **Current** = the only open entry with a time range (if several exist, none is current and a warning is emitted). **Next future** = the first open untimed placeholder. | `src/native/capture_pomodoros.rs:335-349, 403-494` |
| `bob capture-pomodoros -f json` (schema 1): open entries by default, `-a` adds completed ones. Fields: `ref, line, state, name, slug, time_range, placeholder, is_current, child_count, task_link_count`. **No task details.** | `src/native/capture_pomodoros.rs:60-120, 183-264`; `docs/capture.md` Discovery commands |
| Lineup rules: `list_queued_links` gives the start lineup (`=` / `=~K` numbers). `number_task_links` gives the close numbering (`=x1*2!3`). **They are different functions**, so the app must not guess numbers. | `src/native/capture_pomodoro_start.rs:60-119`, `src/native/capture_pomodoro_close/selection.rs:629-665` |
| `today_tasks` already resolves "dedicated Task Links under open Pomodoros". It uses `VaultLinkResolver` (exact path first, then a lazy basename walk) and `note_tasks::scan(...).by_block_id(...)`, and returns the task line only. It re-reads and re-scans each target note per link (no memoization). | `src/native/plan_budget/today.rs:60-188`, `src/native/vault_links.rs:146-233` |
| Task-block extent and line depth: `note_tasks::task_block_extent`, `task_block_line_range`, `block_depths`. The `task_blocks` JSON line shape is `{text, depth, change, before}`. | `src/native/note_tasks.rs:391-422`, `src/native/capture/task_blocks.rs:450-495`, `src/native/capture/block_diff.rs:13-121` |
| Managed log matchers (`🛠️ **WORK LOG**`, `🗓️ **SCHEDULE LOG**`, legacy spellings): `parse_managed_task_log_marker`, `ManagedTaskLogKind {Schedule, Work}`. | `src/native/capture/sub_bullet.rs:282-374` |
| CLI rules: `capture-*` protocol names "may only grow additively"; every long option gets a short alias; options are kept alphabetical. `capture-pomodoros` currently uses `-a -b -f -h`, so **`-t` is free**. | `sase memory read cli_rules.md` |

### 1.3 Measurements on athena (release `bob`, live vault, `hyperfine -N`)

| Command | Mean | Note |
|---|---:|---|
| `bob capture-pomodoros -f json` | **2.8 ms** | the spawn the app already makes on each show |
| `bob capture --dry-run --no-clip -f json -- hello` | 5.9 ms | live-preview cost |
| `bob capture --dry-run --no-clip -f json -- =` | **10.8 ms** | resolves the next Pomodoro's 5 queued links, including the 110 KB `sase.md` (a good proxy for the agenda endpoint) |
| `bob capture-targets --format json` | 8.6 ms | |
| `bob plan -f json` | **320.8 ms** | full `TaskIndex` read, twice. **Do not build the agenda on `bob plan`.** |

All numbers are from athena, not the Mac (the same caveat as the 2026-08 research). A
`find` of the vault's 6,214 `.md` files takes about 13 ms. Over the last ~6 weeks
(Sep 1 – Oct 9), **97%+ of Task Link targets resolve by exact path**
(`bob`, `sase`, `done/sase_done`, …). Only a handful of one-off notes need the
basename walk.

### 1.4 Vault survey: how much content are we fitting? (last 45 daily notes)

I resolved every dedicated Task Link in each day's `## Pomodoros` and counted
task-block lines in three forms: full, without Work and Schedule Log subtrees, and one
line per task.

| Per day | median | p90 | max |
|---|---:|---:|---:|
| Pomodoros | 8 | 13 | 28 |
| Linked tasks | 16 | 26 | 92 |
| Full task-block lines | 43 | 73 | 285 |
| Lines without logs | 24 | 36 | 157 |

Today (2026-10-09, 16:10): no Pomodoro is running. Three placeholders are open: FIX
(5 links), SASE (2), BOB (1). Their 8 tasks total 14 full lines.

---

## 2. Critique: is this a good idea?

### 2.1 Why it is a good idea

1. **The ledger is already the source of truth for Today.** Showing it in the idle
   panel adds a view, not a new concept, and it strengthens the habit of linking work
   into Pomodoros.
2. **It makes session operators easy to use.** `=x1*2!3`, `=~2`, `=#bob` and `==#fix`
   all refer to numbers and names that are currently invisible until you type. If the
   idle view shows the exact numbers bob will use, the next keystrokes need no look-up.
   This is the strongest argument for the feature, and it was not in the original ask.
3. **Near-zero marginal cost.** The app already spawns `capture-pomodoros` on every
   show. Replacing that call with `capture-pomodoros --tasks` keeps the spawn count the
   same.
4. **Fits the architecture.** One additive bob flag, one decoder, one view. No new
   grammar, no daemon, no Swift parsing of the vault.

### 2.2 Risks and how the design handles them

| Risk | Why it matters | Mitigation in this design |
|---|---|---|
| The capture bar becomes a dashboard | The panel's job is a capture in under 2 s, and a tall agenda can distract | The editor stays first, focused, and in a fixed place. The agenda uses calm secondary typography; only the running card has colour. The first keystroke replaces it. A Settings toggle turns it off. |
| **The editor moves** | `center()` on each show plus a tall panel means the input line lands in a different place each day | A fixed eye line; the window grows downward only (§4.6) |
| Requested folds still overflow | 19/45 laptop mornings would scroll with global tiers (§4.4) | A focus gradient plus a fourth tier ("one line per Pomodoro"); scrolling is a last-resort safety net |
| Stale content | Task blocks live outside the daily file | FSEvents on the vault root, revalidation on show, refresh after submit, midnight and wake refresh, and a check that the snapshot is for today |
| Pop-in or jump on show | The first layout of a new snapshot is measured asynchronously | Measure and plan **while hidden**; show reuses the settled metrics (one frame) |
| Big jump on first keystroke | The panel shrinks from agenda height to compact height | The top edge stays pinned, so only the bottom edge moves, once. This is a deliberate mode switch, like Spotlight. The existing loading-height hold (`CapturePreviewPaneHeightPolicy`) must **not** hold the agenda's height. |
| A third definition of "current" | `bob pomodoro` (used by the menu-bar indicator) takes the *last* open timed line. `scan()` requires exactly one. | The agenda uses `scan()`, the same rule as capture. A "multiple open timed Pomodoros" warning shows in the agenda instead of guessing. |

**Verdict:** a good idea once the adjustments below are made. Without them it would
either scroll most laptop mornings, or move the input line around, or show stale task
bodies.

---

## 3. Adjustments to the requirements (explicitly called out)

| # | Original requirement | Adjustment | Why |
|---|---|---|---|
| **A1** | "Cache it when the daily file's contents haven't changed" | Invalidate on **any vault change** (existing FSEvents watcher), plus show, submit, wake, and midnight. Cache the **decoded snapshot and fold plan** in the app. Compare bob's stdout bytes to skip re-decoding and re-rendering when nothing changed. No bob-side disk cache. | Task bodies live in other notes (≈88% of links target non-daily notes). The bob call is ~10 ms and runs off the critical path. A validated mtime cache would need a stat walk that costs about as much as the work itself (`docs/task-dependencies.md` §12.7). |
| **A2** | Three levels: full, no logs, one line | Keep the levels and their order, but apply them **progressively, bottom-up (farthest first)**, not globally. Add **tier 3: one line per Pomodoro** (name plus inline task titles). Scrolling is only a safety net. | Global tiers scroll on 19/45 laptop mornings. The focus gradient keeps Now and Next detailed on 43–45/45 days. |
| **A3** | "Expand the height of the window as necessary" | Expand **downward from a fixed eye line**, at about where the compact panel appears today. Don't re-centre a tall panel. | Keeps the input line in the same place every time. In simulation the lost room barely affects Now and Next (§4.4). |
| **A4** | Show tasks for current and future Pomodoros | Also show the **`=x` / `=` numbers** bob uses, and label the running entry **Now** and the first placeholder **Next** (`=` starts it). | Makes the agenda actionable, at no extra cost. |
| **A5** | "Full task definition" | Show the task line as clean text: bob's `text`, which already strips `#task`, inline fields, and `^id`. Show children with indentation and light markdown styling. Cap any single child bullet at 4 wrapped lines in tiers 0 and 1. | Raw `[created::…] ^id` is noise. One giant bullet should not force every other task down a tier. |
| **A6** | (not specified) | A task linked in two open Pomodoros is shown in full **once**, at its first (nearest) occurrence. Later occurrences show one line with "↑ also above". | Avoids paying twice for the same block. |
| **A7** | (not specified) | Show struck (retired) links in the running Pomodoro as **one dim summary line**. Show unresolved, ambiguous, and non-task links as a warning row. Show a done task still linked to a future Pomodoro as one struck line. | Reliability: never silently drop a link. |
| **A8** | (not specified) | Empty state: one quiet line, "No Pomodoros left today · `=#NAME` starts one". Failure state: keep the last good snapshot with a "stale" clock glyph if it is for today; otherwise hide the agenda. | Distinguishes "nothing planned" from "failed to load". Never shows yesterday's agenda. |
| **A9** | (implicit) | Hide the agenda whenever the draft is non-empty or a picker, stash, or prompt owns the auxiliary region. Bring it back when the draft is cleared. Add a Settings toggle, on by default. | Matches the request; gives an escape hatch. |

---

## 4. Design

### 4.1 Responsibility split

```
                 ┌─────────────── bob (meaning) ───────────────┐
 vault ──read──► │ scan() roles · lineup/close numbers ·        │ ──JSON──┐
                 │ link resolution · task block · log flags     │         │
                 └──────────────────────────────────────────────┘         ▼
 ┌──────────────────────── Bob Mac Capture (pixels) ─────────────────────────────┐
 │ CaptureAgendaStore (snapshot + bytes digest, refresh triggers)                │
 │ CaptureAgendaPresentation (pure: sections, rows per tier, dedupe, summaries)  │
 │ CaptureAgendaFitPlanner (pure arithmetic: heights × budget → tier per row)    │
 │ CaptureAgendaView (hidden measuring pass → planned rows → render)             │
 └───────────────────────────────────────────────────────────────────────────────┘
```

The app never decides what is running, what a Task Link is, what number a link has,
or where a Work Log starts. bob tells it. The app only decides how much of what bob
returned fits on screen, which the thin-client record explicitly allows ("may filter or
rank what `bob` returned").

### 4.2 bob contract: `bob capture-pomodoros --tasks` (additive, schema 1)

Why extend `capture-pomodoros` rather than add a command:

- It already selects the day file the way capture does, lists **open** entries by
  default (exactly current plus future), owns the `is_current` rule and its warning,
  and is the call the app already makes on show.
- An additive flag fits the CLI rule for `capture-*` names. With `-t`, the options
  stay alphabetical: `-a -b -f -h -t`.
- Human output for `--tasks` becomes a nice terminal agenda for free.

Sketch, with new fields marked ★ (values illustrative):

```json
{
  "ok": true, "schema_version": 1,
  "day_file": "/Users/bryan/bob/2026/20261009.md", "relative_day_file": "2026/20261009.md",
  "date": "2026-10-09",                                        // ★
  "completed_summary": {"count": 5, "minutes": 160},           // ★ footer "5 done · 2h 40m"
  "count": 3,
  "pomodoros": [
    {
      "ref": "46:ae8bb2f6", "line": 46, "state": "open", "status_symbol": " ",
      "name": "FIX", "slug": "fix", "selectable": true, "time_range": null,
      "placeholder": true, "is_current": false, "child_count": 5, "task_link_count": null,
      "role": "next",                                          // ★ running | next | later | open_timed
      "starts_at": null, "ends_at": null,                      // ★ local ISO, timed entries only, midnight wrap resolved
      "items": [                                               // ★ direct children in ledger order
        {
          "kind": "task_link",                                 // task_link | retired_link | note
          "index": 2,                                          // the number this entry's operator uses:
                                                               //   =x numbering on the running entry,
                                                               //   start-lineup numbering (= / =#name / ~K) on placeholders
          "ledger_line": 48, "block_link": "[[sase#^just-install-venv]]", "embedded": false,
          "resolution": "resolved",                            // resolved | missing | ambiguous | not_a_task | duplicate | unreadable
          "relative_target": "sase.md", "line": 812, "block_id": "just-install-venv",
          "text": "Use `just install-venv` instead of `install` so `install` can be used for dev install!",
          "status_symbol": "/", "status_name": "In Progress", "status_type": "in_progress",
          "children": [                                        // task block minus the task line
            {"text": "\t- 🛠️ **WORK LOG**", "depth": 1, "log": "work"},
            {"text": "\t\t- *2026-10-08* — Running research on athena.", "depth": 2, "log": "work"}
          ],
          "children_truncated": false,                         // safety valve (e.g. > 200 lines)
          "ledger_notes": [{"text": "\t\t- epic on athena", "depth": 1}],
          "warning": null
        }
      ]
    }
  ],
  "warnings": []
}
```

Rules for the bob phase:

- **Reuse, don't re-derive:**
  - `scan()` for entries and roles; `next_future_pomodoro` for `next`.
  - `number_task_links` for the running entry's `index`; `list_queued_links` for
    placeholders.
  - `VaultLinkResolver` and `note_tasks` for resolution.
  - `task_block_extent` and `block_depths` for `children`.
  - `parse_managed_task_log_marker` to tag a log subtree (marker line plus all
    descendants) with `log: "work" | "schedule"`.
- **Performance:**
  - Read and scan each target note **once** per invocation. Unlike `today_tasks`,
    memoize by path.
  - Exact-path resolution first; never touch `TaskIndex` or dataview.
  - Gate: p95 ≤ 15 ms on athena for a 10-Pomodoro / 25-link day, recorded in
    `docs/capture.md` like the dependency-preview budgets.
- **Determinism:** no timestamps or `now`-dependent fields in the output. The same
  vault must produce the same bytes, which is what makes the app's byte-compare cache
  work. The countdown is computed in the app from `starts_at` / `ends_at`.
- **Fail soft:**
  - A missing day file or section gives `ok` with an empty list (today's behaviour).
  - Per-link problems become `resolution` plus `warning`, never a command failure.
- **Docs and tests:**
  - Extend `docs/capture.md` → Discovery commands.
  - Add CLI tests with a fixture vault covering: running plus queued entries,
    duplicates across entries, struck links, `[[#^self]]` links, embedded links,
    missing and ambiguous links, logs, and multiple open timed entries.
  - Check in a golden JSON fixture the Mac tests can copy.

### 4.3 Caching and freshness ("blazing fast")

**Critical path (hotkey → visible, focused panel): zero new work.**

- The agenda is already decoded, planned, and laid out in the hidden panel.
- `show()` replays cached metrics and orders the panel front: one frame, as today.

| Layer | What is cached | Invalidated by |
|---|---|---|
| L0 view | The laid-out agenda inside the pre-warmed panel and its measured content metrics | A new snapshot, a panel width change, a screen or scale change, Dynamic Type |
| L1 app store | `CaptureAgendaStore` holds the last good decoded snapshot plus a SHA-256 of bob's stdout bytes. **Identical bytes mean no decode, no publish, no re-layout.** | Triggers listed below |
| L2 bob | Nothing persistent. Per-invocation memo of note reads. | n/a |

Refresh triggers. Each is a background spawn on lane `agenda`, which cancels the
previous one and uses a generation counter:

1. App launch (prefetch, so the first hotkey press after login already has data).
2. `VaultTargetWatcher` event, **whether or not the panel is visible**. Today the
   pomodoro count refreshes only while visible. One debounced ~10 ms spawn per vault
   change is negligible, and it means the hidden panel is already up to date.
3. Panel show: stale-while-revalidate. Render the cache, revalidate, and swap only if
   the bytes differ. This replaces today's `refreshCurrentPomodoroTaskLinkCount()`
   spawn; derive `currentPomodoroTaskLinkCount` from the snapshot.
4. After a successful submit. The capture just changed the vault, and FSEvents adds
   0.3–0.6 s of latency.
5. Wake or unlock (`NSWorkspace` notifications) and a timer at the next local
   midnight. **Never show a snapshot whose `date` is not today.**

**Settle while hidden.** When a new snapshot arrives while the panel is hidden, run
`panel.contentView?.layoutSubtreeIfNeeded()` so the measuring pass, the planner, and
`receiveContentMetrics` all settle before the next hotkey press. Without this, the
first show after an Obsidian edit lays out asynchronously and visibly resizes after
the first frame.

**Time-dependent display** (the "12m left" countdown and the progress hairline) uses
a `TimelineView(.periodic(by: 30))` only while visible, computed from
`starts_at`/`ends_at`. bob is never re-spawned because time passed. Which entry is
running depends only on the file, not the clock.

Budget summary:

| Path | Cost |
|---|---|
| Hotkey → panel | unchanged (one frame; 0 spawns on the critical path) |
| Spawns per show | unchanged (2: `capture-targets` plus agenda, which replaces `capture-pomodoros`) |
| Freshness after an Obsidian edit | ≤ ~0.7 s via FSEvents; ≤ ~20 ms after show via revalidation |
| Idle CPU | one ~10 ms spawn per debounced vault change, usually a byte-identical no-op |

*Optional later (measure first):* let bob return `sources` (the files it read) so the
watcher can skip vault events that touch none of them. Not needed for v1, because
correctness is simpler with "any change means refresh".

### 4.4 The fit algorithm (the heart of the feature)

**Tiers per task row:**

| Tier | Content | Fold affordance |
|---|---|---|
| 0 Full | task line plus every child, logs included (logs in tertiary text) | none |
| 1 No logs | task line plus children minus the Work and Schedule Log subtrees | trailing tertiary chips: `hammer 3` / `calendar 2` (number of hidden entries) |
| 2 One line | task title only, single line, tail-truncated | trailing `+N` (hidden child lines) |
| 3 Pomodoro line | the whole Pomodoro on one row: `◌ SASE  Dynamic AGENTS.md · Plan epic roadmap…` | task count |
| ∞ Overflow | the auxiliary `ScrollView` scrolls, with a bottom fade | never clip silently |

**Degradation order: a "focus gradient".** Each step works **bottom-up**, and planning
stops as soon as the total height is within budget:

1. All rows: tier 0 → 1 (logs fold first, as Bryan specified).
2. Rows of **Later** Pomodoros: → 2.
3. **Later** Pomodoros: → 3, the farthest first.
4. Rows of **Next**: → 2.
5. Rows of **Now**: → 2.
6. Overflow, so scroll.

This keeps Bryan's priority (logs before one-line) and adds a second rule: **detail
fades with distance in time**. Visually there is at most one boundary per tier, moving
up from the bottom, so the view reads as intentional rather than ragged. The planner
is O(rows) arithmetic, deterministic, and pure, so it belongs in `CaptureCore` with
exhaustive unit tests.

**Simulation on 45 real days.**

Method:
- Every dedicated Task Link was resolved against the live vault.
- Row costs: ~100 characters per visual line at ~740 pt width; one row ≈ 19 pt;
  Pomodoro header ≈ 1.4 rows; a tier-3 Pomodoro line ≈ 1.15 rows; ~150 pt of chrome.
- Budgets assume a hidden Dock: 13" ≈ 919 pt and 14" ≈ 945 pt visible height.
- "Morning" means all of the day's Pomodoros are still ahead. This is an upper bound,
  because logs written later that day are included. "Midday" means the second half.

| Scenario | Global tiers (as requested): days that **scroll** | Focus gradient: days that scroll | Focus gradient: Now + Next keep ≥ no-log detail |
|---|---:|---:|---:|
| Morning, 14", fixed eye line | **19 / 45** | 1 / 45 | 43 / 45 |
| Morning, 14", full height (re-centred) | 9 / 45 | 0 / 45 | 44 / 45 |
| Morning, 27" external, fixed eye line | 1 / 45 | 0 / 45 | 45 / 45 |
| Midday, 14", fixed eye line | 1 / 45 | 0 / 45 | 44 / 45 |
| Midday, 13", fixed eye line | — | 0 / 45 | 44 / 45 |

What the numbers say:

- **Three global tiers are not enough** on a laptop.
- **The focus gradient gives the same no-scroll guarantee at every screen size and
  spends the detail where it matters.**
- **The fixed eye line costs Now and Next almost nothing** (43 vs 44 of 45). It mostly
  lowers detail in Later: share of tasks shown in full on a 14" morning is 17% vs 26%.

**Measuring heights reliably.** Text wraps, so per-row heights must be measured, not
estimated.

- Render the tier 0, 1 and 2 variants of each row in a **hidden measuring stack**:
  `.hidden()` in a zero-height `.background`, at the same width and fonts.
- Collect heights by row ID through a `PreferenceKey` / `onGeometryChange`.
- Feed them to the planner, then render the planned rows once.
- This only happens when the snapshot, width, or scale changes. Thanks to "settle
  while hidden" (§4.3), it does not happen on show.
- Rejected:
  - `ViewThatFits(in: .vertical)` only picks the first child that fits as a whole, so
    it cannot express per-row progressive folding.
  - Iterative render, measure, re-render passes flicker and can oscillate.

**Budget:**

```
budget = eyeLineToBottom − 2·margin − chrome(editor one line, footer, spacing)
```

- The budget comes from the screen and the eye line. **It never depends on the current
  window height**, so there are no resize feedback loops (the controller already
  guards against these).
- Keep one row of slack for rounding.

### 4.5 Visual design

*Illustrative, adapted from the 2026-10-09 ledger (BOB shown as if running).*

```
┌──────────────────────────────────────────────────────────────────────────┐
│  Type to capture…                                                         │ ← editor, unchanged, fixed eye line
│                                                                           │
│ ▌▶ BOB                                    14:10–14:35 · 12m left    =x    │ ← Now card: 3pt pink rail, faint pink wash
│ ▌━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━──────────────                     │   2pt progress hairline
│ ▌ 1 ◐ Use `just install-venv` instead of `install` so …                   │   number capsule · status glyph · text
│ ▌      🛠 Work log                                                         │   tier 0: log in tertiary text
│ ▌        Oct 8 — Running research on athena.                              │
│ ▌ 2 ◉ Add `bob mac` command to manage bob-mac-capture                     │
│ ▌   ✓ 2 done this session · Shampoo · Reboot apollo                       │   retired links: one dim line
│                                                                           │
│  ◌ FIX  · next                                               =  starts it │ ← Next: dashed-circle glyph, hint keycap
│   1 ◉ Launch ~/.sase/plans/202610/agents_archive_view.md!                 │
│   2 ◐ Use `just install-venv` instead of `install` …   ↑ also in Now      │   dedupe: full block shown once
│   3 ◉ Fix muse reply streaming!                                           │
│   4 ◉ Allow `%auto` to approve nested epics again!                        │
│   5 ◉ Re-launch all failed agents on apollo!                              │
│        ⛓ Depends on: Fix apollo                                           │   non-log children stay in tier 1
│                                                                           │
│  ◌ SASE   Dynamic AGENTS.md · Plan epic roadmap for goals   🛠 1     2    │ ← Later, tier 3: one line per Pomodoro
├──────────────────────────────────────────────────────────────────────────┤
│ 5 done · 2h 40m today                          Stash 0   Discard   …      │ ← footer: "Ready" becomes a day summary
└──────────────────────────────────────────────────────────────────────────┘
```

**Typography**
- Pomodoro name in `.subheadline.weight(.semibold)` with slight tracking.
- Times use `.monospacedDigit()`.
- Task rows in `.callout`, proportional. Inline code spans keep `.monospaced`, using
  the tokenizer's `code` role.
- Child bullets in `.callout` secondary; logs in `.footnote` tertiary.
- Proportional text fits ~15–20% more characters per line than the monospaced diff
  cards. The diff cards stay monospaced, because a diff is a different job.

**Colour**
- One accent only: the running card uses the existing `pomodoroStart` pink (rail,
  progress, play glyph), the same language as the `=` start preview.
- Status glyphs and colours come from `CaptureEditorPalette.taskStatus`: ◐ orange in
  progress, ◉ blue next, ○ todo, ⏸ blocked, ✓ green done.
- Everything else uses system `.secondary` / `.tertiary` on `.thinMaterial`, like the
  existing `PreviewPane`.

**Glyph vocabulary**, reused rather than invented:
- `play.circle.fill`: running. `circle.dashed`: queued. `hammer`: Work Log.
  `calendar`: Schedule Log. `arrow.turn.left.up`: "also above".
- `exclamationmark.triangle`: unresolved link.
- `clock.badge.exclamationmark`: stale snapshot, or more than 10 minutes overdue. The
  overdue state mirrors the menu-bar indicator's semantics.
- Number badges use the quaternary capsules already in the start and close previews,
  so `1 2 3` look identical to what `=x` and `=` will show next.

**Numbers** appear only on Now (for `=x`) and Next (for `=` and `=~K`). Later
Pomodoros are addressed by name (`=#sase`), so they show no numbers. This reduces
visual noise.

**Indentation.** Children indent 14 pt per depth, with the 1 px separator indent guides
from `BlockDiffCard`. List markers (`- `) are not drawn; depth carries the structure.
Child checkboxes (`- [ ] …`) render as small status glyphs.

**Motion**
- None on show.
- When the agenda updates while visible, a 120 ms cross-fade, disabled under Reduce
  Motion.
- The first keystroke swaps the agenda for the capture preview immediately, with no
  height hold.

**Accessibility**
- Each Pomodoro is an accessibility container, e.g. "Running Pomodoro BOB, 14:10 to
  14:35, 12 minutes left, 2 tasks".
- Folded chips are announced, e.g. "Work log hidden, 3 entries".
- Increase Contrast raises washes to the `BlockDiffCard` 0.22 levels.
- Reduce Transparency is respected through the materials.

### 4.6 Window placement: a fixed eye line

- Replace `panel.center()` on show with a computed frame whose **top edge sits at a
  fixed eye line**: roughly where `center()` puts today's compact panel, about
  18–21% of the visible height from the top.
- The agenda grows **down** from there, clamped at `visibleFrame.minY + margin`.
- The existing `CapturePanelWindowSizer.frame` already keeps `maxY` fixed when height
  changes, so only the show-time placement changes.
- Effect: the input line is in the same place whether the agenda is empty, tall, or
  absent, and the compact capture bar looks unchanged.
- **Alternative (offered, not recommended):** slide the top up only when the agenda
  needs more room. That buys ~8 rows on a 13–14" laptop at the cost of the input line
  moving on busy days.

### 4.7 When the agenda shows

`agendaVisible = settings.showAgenda && !hasDraft && snapshot?.date == today &&
!pickerVisible && !isStashPickerPresented && !inlinePromptVisible`.

- A whitespace-only draft counts as empty, matching `editorTextDidChange`.
- When visible, the agenda is the auxiliary region's only content.
- A retained draft (Escape) reopens without the agenda, exactly as the user left it.

---

## 5. Alternatives considered and rejected

| Alternative | Why rejected |
|---|---|
| Parse the daily file in Swift | Violates the thin-client decision and creates a second definition of current, next, and lineup numbering |
| Build on `bob plan -f json` | 320 ms here (full vault `TaskIndex`, twice); returns task lines only; no Pomodoro structure |
| bob-side disk cache keyed on the daily file's mtime | Incorrect (misses linked-note edits) and pointless (~10 ms off the critical path); a correct cache needs a stat walk costing about as much |
| bob decides the fold (`--max-lines N`) | bob cannot know pixel heights, wrapping, width, or screen size; every resize would need a re-spawn |
| bob returns three pre-rendered tier strings | Triples the payload; the app can derive every tier from one tree plus `log` flags |
| A resident `bob` daemon or FFI | Premature per the decision record; spawn cost is not the bottleneck |
| `ViewThatFits` with three global variants | Cannot fold per row or per Pomodoro; scrolls on 19/45 laptop mornings |
| A fixed-height scrolling list (Raycast style) | Directly contradicts "no scrolling"; hides Later behind a gesture |
| Agenda in a separate HUD or the menu-bar dropdown | Loses the main benefit (numbers visible exactly when you type `=x`/`=`); a menu-bar consumer can reuse the JSON later anyway |

---

## 6. Implementation plan (phased, each phase shippable)

1. **bob-cli: contract.**
   - `capture-pomodoros --tasks/-t`: roles, items, index, resolution, children with
     `log`, ledger notes, `date`, `starts_at`/`ends_at`, `completed_summary`.
   - Human `--tasks` output (coloured agenda).
   - `docs/capture.md` Discovery section; CLI tests; golden fixture; perf note.
   - Keep schema 1 (additive); per-note read memo.
2. **Mac: data plumbing (no UI).**
   - `CaptureAgenda` decodables in `CaptureCore` (`decodeIfPresent` everywhere, so an
     older `bob` without `--tasks` simply yields no agenda).
   - `CaptureAgendaStore` with byte-digest compare, lane `agenda`, the five triggers,
     and settle-while-hidden.
   - Derive `currentPomodoroTaskLinkCount` from the snapshot and remove the separate
     fetch.
3. **Mac: planner and view.**
   - `CaptureAgendaPresentation` and `CaptureAgendaFitPlanner` in `CaptureCore`, with
     table-driven tests: each degradation step, dedupe, empty, overflow, and determinism.
   - `CaptureAgendaView`: hidden measuring pass plus planned render.
   - Integration into `hasAuxiliaryContent` / `auxiliaryContent`.
   - Fixed eye-line placement in `CapturePanelController`.
4. **Polish.**
   - Empty, stale, and warning states; footer day summary; Settings toggle;
     accessibility labels.
   - Signposts `agenda-refresh` / `agenda-plan` / `agenda-measure`.
   - Design snapshot tests like `RefsPanelDesignTests` / `CapturePickerDesignTests`.
   - Update the README principle at `README.md:290-291`.
   - Once accepted, a decisions record, e.g. "The idle capture panel shows the ledger
     agenda with a focus-gradient fold".

Phases 2–4 are gated by macOS CI, because agent hosts have no Swift toolchain (the
cost called out in `decisions:mac-capture-is-a-thin-client`). Measure **on the Mac**
with signposts before tuning anything: the athena numbers are a lower bound for spawn
cost there.

---

## 7. Open questions for Bryan

1. **Fixed eye line vs slide-up** (§4.6). Recommended: fixed.
2. **Numbers on Later Pomodoros?** Recommended: no, only Now and Next.
3. **Footer day summary** ("5 done · 2h 40m") instead of "Ready"? Recommended: yes;
   cheap and calm.
4. **Ledger notes** under a link in the Pomodoro, e.g. "epic on athena": show them in
   tiers 0 and 1 as italic secondary lines? Recommended: yes.
5. **v2 interactions** (not in v1):
   - Hold ⌥ to peek at everything at full detail in a scroll view.
   - Click a row to open the task in Obsidian.
   - ⌘1…9 to insert the Nth link into the draft.

---

## 8. References

- Code and docs cited inline (bob-cli `src/native/…`, `docs/capture.md`;
  bob-mac-capture `Sources/…`, `README.md`).
- SASE records: `decisions:mac-capture-is-a-thin-client`,
  `decisions:today-is-read-from-the-ledger`, glossary `pomodoro`, `task-link`,
  `work-log`, `schedule-log`, `mac-pom`; memory `cli_rules.md`.
- Prior research: `research:202608/bob_mac_capture_replacement/bob_mac_capture_replacement.md`
  (§4.8 latency budget, §§2.2–4.3 thin-client rationale).
- Apple, [`ViewThatFits.init(in:content:)`](https://developer.apple.com/documentation/swiftui/viewthatfits/init(in:content:).md):
  picks the first child that fits the proposal; no partial folding.
- Fatbobman, [Mastering ViewThatFits](https://fatbobman.com/en/posts/mastering-viewthatfits)
  (ideal-size measurement, truncation pitfall).
- Apple, [`NSWindow.center()`](https://developer.apple.com/documentation/appkit/nswindow/center().md),
  and the Cocoa-dev thread [NSWindow Centering Problem](https://lists.apple.com/archives/Cocoa-dev/2008/May/msg00505.html)
  (placement "slightly above center"; ~¼–⅓ above empirically).
- Measurements: `hyperfine -N` on athena, 2026-10-09; vault survey and fit simulation
  scripts were ad-hoc Python over the 45 most recent daily notes (method in §1.4 and
  §4.4).

---

## 9. Recommended solution

Build an **idle Pomodoro agenda** as the default content of the empty capture panel:

1. **bob (meaning).** Add `bob capture-pomodoros --tasks/-t` (additive, schema 1).
   - It returns each open Pomodoro's role (Now, Next, Later), its dedicated Task Links
     with the exact `=x` / `=` numbers bob uses, each link's resolved task (clean text,
     status, children with Work and Schedule Log subtrees flagged), ledger notes,
     retired links, and warnings.
   - Output is deterministic bytes from one memoized read of the daily file plus each
     linked note.
   - Target ≤ 15 ms p95; never use `bob plan`.
2. **Mac (pixels).**
   - A `CaptureAgendaStore` keeps the last decoded snapshot in memory and refreshes in
     the background on: launch, every vault FSEvent (visible or not), panel show
     (stale-while-revalidate, replacing today's `capture-pomodoros` spawn), submit,
     wake, and midnight.
   - Byte-identical output is a no-op.
   - New snapshots are measured and planned **while the panel is hidden**, so the
     hotkey still costs one frame and zero critical-path spawns.
3. **Fit.**
   - A pure `CaptureAgendaFitPlanner` folds by a **focus gradient**, bottom-up:
     - logs everywhere,
     - then Later tasks to one line,
     - then Later Pomodoros to one line each,
     - then Next, then Now to one line,
     - and only then scroll.
   - Heights come from a hidden SwiftUI measuring pass of the real rows.
   - On 45 real days this never scrolls except on one extreme 28-Pomodoro day, and
     keeps Now and Next detailed on 43–45 of 45 days even on a 13–14" laptop.
4. **Window.** Grow **downward from a fixed eye line** so the input line never moves.
   The first keystroke swaps the agenda for the normal live preview, with no
   height hold.
5. **Look.**
   - The Now card gets the only accent (pink rail, progress hairline, countdown).
   - Next gets a dashed glyph and an "`=` starts it" hint.
   - Later is calm secondary text.
   - Status glyphs and number capsules are shared with the existing previews.
   - Fold chips say exactly what is hidden; repeats are shown once.
   - Unresolved links are visible; an empty day gets a one-line state and a stale
     snapshot gets a stale glyph.
   - The footer becomes a quiet "5 done · 2h 40m" day summary.

Ship it in four phases: bob contract, then Mac plumbing, then planner and view, then
polish. Measure on the Mac with signposts, and record the accepted fold policy as a
decisions record.
