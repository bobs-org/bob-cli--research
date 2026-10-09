# Idle pomodoro preview for Bob Mac Capture

Researcher: `grk`. Independent design research for showing today's current and future Pomodoros — with expanded task trees — in Bob Mac Capture when the draft is empty. Peer swarm reports were not consulted.

## Verdict

Do it. The empty capture panel is the most frequent "what am I doing" surface Bryan already summons, and today it is a blank editor. Filling that idle state with the running session and the rest of today's planned sessions turns `⌃⇧⌘I` into a glanceable now-and-next card without adding a new hotkey or a second app.

Ship it as a dedicated **idle-today** surface, cache-first, with Bob as the only vault reader. Treat "blazing fast" as a hard latency budget: the panel must order-front from memory, and a `bob` spawn may only refresh in the background.

The original fold-and-cache sketch is directionally right. Several of its details would make the panel slow, jumpy, or visually noisy. The adjustments below are the design.

## Bottom line

1. **Idle-today is a read view**, served by an additive `bob capture-pomodoros --expand` payload, decoded by a new Swift presentation type. It is a sibling of live capture preview, not a dry-run of an empty draft.
2. **Paint from cache on the first frame.** Fingerprint the daily file *and* every resolved task note. Stat those files locally; spawn `bob` only when a fingerprint misses. Prefetch at launch, after capture, on filtered FSEvents, and at day rollover.
3. **Pack to the screen, then fold, then scroll.** Attempt the full task tree; hide managed Work/Schedule logs next; collapse to a single task line last. Apply that ladder *progressively* (current session stays richest; later futures fold first). Scroll is the last resort when even single-line rows overflow the visible frame.
4. **Look like a session card, not a diff.** Reuse status glyphs, pomodoro headline tokens, numbered close badges, and the plan-budget capsules. Leave the green/red mutation gutter on live capture preview.

---

## 1. Is this a good idea?

Yes. Three properties of the current system make the idle panel the right place for this glance:

- Bryan already opens the capture panel constantly, including when he has not yet decided what to type. `prepareForPresentation()` currently clears leftover success chrome for an empty draft and leaves `previewState = .idle`, which hides the preview pane entirely (`hasAuxiliaryContent` is false). The first paint is an editor, a footer, and nothing about today.
- The ledger already *is* Today. Decision `today-is-read-from-the-ledger` defines today as Task Links under today's **open** Pomodoros. Decision `mac-capture-is-a-thin-client` already makes the panel a renderer of Bob JSON. An idle-today card is the same contract pointed at a read-only discovery command.
- The Mac app already pays a `bob capture-pomodoros` spawn on every show (`CapturePanelController.show()` → `refreshCurrentPomodoroTaskLinkCount()`), and already grows the window to the preview's natural height (`CapturePanelWindowSizer`, `CapturePreviewFullHeightTests`). The idle card can ride both rails.

The idea earns its keep if the empty panel answers, in under a frame, "what is running, what is queued, and what are those tasks actually." It fails if the first paint waits on disk, if the window jumps after a spinner, or if a wall of Work Log history buries the task titles.

That is why cache-first and packing are part of the product, not optimizations to add later.

## 2. Critique of the original plan

The request asks for: default preview on popup; cache when the daily file is unchanged; full task trees if they fit; otherwise two global fold levels (drop logs, then single-line); expand the window so the user never scrolls.

### What to keep

- **Default on popup.** The empty draft is the home state. `prepareForPresentation()` is the hook.
- **Full tree first.** When two or three current tasks plus a couple of planned sessions fit, showing Depends-On, notes, and sub-bullets is exactly the information capture needs.
- **Logs fold before titles.** Work Log and Schedule Log are history. They are the correct first thing to drop. Bob already knows those markers (`parse_managed_task_log_marker` in `src/native/capture/sub_bullet.rs`).
- **Window grows to content.** The sizer already preserves the panel's top edge and clamps to the visible frame minus `panelScreenMargin` (24 pt). Idle-today should use that, not a new geometry policy.

### What to change

These are explicit requirement adjustments.

**A1. Cache key is the daily file plus every resolved task note.**
Task bodies live in area/project notes. A daily file that has not changed can still sit above a Work Log that grew, a status that hooks rewrote, or a Depends-On line that landed. Caching on daily-file bytes alone will serve stale trees, which is worse than a blank pane. Bob must return a `sources[]` fingerprint list (`relative_path`, `mtime_ms`, `size`). The app stats those paths itself (no spawn) and treats a full match as a hit.

**A2. Progressive packing, with the two named folds as the density ladder.**
A global "everyone drops to single-line because one task has a 40-line Work Log" policy throws away the current session to save a future placeholder. Pack in this order, stopping as soon as estimated height fits the screen budget:

1. Full trees for every current and future session.
2. Drop Work Log and Schedule Log regions, current last.
3. Single-line futures, last planned session first.
4. Single-line current tasks.
5. Collapse remaining futures to one `N more planned` row.
6. Allow the existing auxiliary `ScrollView` to scroll.

The two fold views in the request are steps 2 and 3–4. The extra steps (5–6) are required because a 14-inch visible frame cannot promise "never scroll" for a day with eight named placeholders and twenty links.

**A3. Scroll is the last resort, not a forbidden state.**
The preview pane already lives in `auxiliaryScrollRegion` (`CapturePanelView`). The window already stops at the screen. "Never scroll" is physically false for a large day. The contract is: grow first, fold second, scroll only after single-line still overflows. Never clip.

**A4. Dedicated expand payload; empty `bob capture --dry-run` is the wrong tool.**
Live preview is a planner. It diffs before/after, rolls priority seeds, and currently short-circuits empty drafts to `.idle` on purpose (`CapturePanelModel.editorTextDidChange`). An empty dry-run would either error, no-op, or pretend a capture happened. Idle-today is a reader. Grow `bob capture-pomodoros` additively with `--expand` / `-e` so the cheap default (the close-comma `task_link_count` path) stays a list.

**A5. First paint never waits on `bob`.**
Replacement research (`research:202608/bob_mac_capture_replacement`) set R6: sub-100 ms perceived pop-up, cold, every time. A `bob capture --dry-run` spawn measured ~5 ms on athena for a trivial draft; expanding N task notes will be slower, and Mac spawn cost was never the 5 ms number. The panel already `orderFront`s, then refreshes pomodoro count in the background. Idle-today must do the same: memory cache (and a Refs-style disk snapshot for cold launch) paints immediately; a miss still paints the last snapshot and refreshes behind a quiet caption, never a pane-collapsing spinner.

**A6. Distinct visual language from mutation diffs.**
`PomodoroBlockView` / `TaskBlockView` / `BlockDiffCard` are after-state diffs of a capture that is about to write. Idle-today has no before/after. Reusing the green/red gutter would look like the vault is mutating when the user has typed nothing. New `IdleTodayPresentation` + `IdleTodayView`, sharing `CaptureEditorPalette.taskStatus`, `CapturePomodoroLineTokens`, close-row number badges, and the plan-budget capsules.

**A7. Number the current session's Task Links with the `=x` lineup.**
`number_task_links` already defines that order, and the panel already fetches `task_link_count` so close-comma assist can type `=x1,2`. Showing those numbers on the idle card teaches the close grammar and makes the current session feel like the close card's quiet twin.

**A8. Tick remaining time locally.**
The Hammerspoon menu-bar indicator already derives a countdown from `bob pomodoro --show-stale` and ticks between polls. Bob should emit `ends_at` (local civil datetime) on the current entry. Swift ticks remaining / overdue without another spawn. A cache hit that is two minutes old is still the right session; only the clock face moves.

**A9. Show the plan-budget meter on idle.**
`plan_budget` is already computed from the same daily file the scan reads. Themes 3/3 · Links 4/10 is the other thing Bryan needs before capturing. Cheap, on-payload, and already has a Swift presentation (`CapturePlanBudgetPresentation`).

**A10. Per-task expand is always available.**
When packing drops a log region or a body, the row still offers a fold control (the existing TaskBlockView pattern: a count chip that inlines the hidden lines). Auto-pack chooses the default; the user can open one task without changing the others.

---

## 3. What the code does today

Evidence from this workspace, 2026-10-09.

### Empty draft hides preview

`CapturePanelModel.editorTextDidChange` trims the draft and, when it is empty, sets `previewState = .idle`, clears parse/completion, and returns without spawning. `CapturePanelView.hasAuxiliaryContent` is false while preview is idle (unless a picker, stash, chip, or error is up), so the preview card is not in the tree. `prepareForPresentation()` for an empty draft calls `resetAnalysisState()`, which again forces `.idle`.

There is currently no idle content to cache.

### Show path already spawns `capture-pomodoros`

```
CapturePanelController.show()
  model.prepareForPresentation()
  model.refreshCurrentPomodoroTaskLinkCount()   // async bob capture-pomodoros
  panel.makeKeyAndOrderFront
  model.requestFocus(.editor)
```

`BobProcessClient.capturePomodoros()` requests `capture-pomodoros --format json`, schema 1. Swift decodes only `line`, `name`, `is_current`, `task_link_count` — a deliberately minimal slice for close-comma assist. The CLI already returns much more (`ref`, `state`, `slug`, `time_range`, `placeholder`, `child_count`, `warnings`, `day_file`).

Default `capture-pomodoros` lists **open** entries only. Current is the unique open *timed* entry. Future, in Bob's own words (`next_future_pomodoro`), is the first open *placeholder with no time range*. "All future pomodoros" is every remaining open placeholder in document order after that rule, which is also every open untimed entry in a healthy ledger.

### Live preview is a debounced planner

`scheduleAnalysis` waits 50 ms, runs `capture-parse`, then `capture --dry-run --no-clip --format json`. `CapturePreviewPaneHeightPolicy` holds the last settled height while `.loading` so the window does not collapse on every keystroke. That policy is for mutation previews. Idle-today should not enter `.loading` on a cache hit at all.

Timeout is 20 s (`BobProcessClient.defaultTimeout`). Fine as a wedge bound; useless as a popup budget.

### Window growth and scrolling already exist

- `CapturePanelLayout.previewMinimumHeight = 92`
- `panelScreenMargin = 24`
- Live panels clamp to the screen's visible frame; the 720 pt `panelMaximumContentHeight` is a no-screen fallback only
- The sizer keeps `maxY` and width, nudges back inside `visibleFrame`
- Auxiliary content is in a vertical `ScrollView` with `.scrollBounceBehavior(.basedOnSize)`
- Editor budget (`CaptureEditorHeightBudget`) reserves auxiliary space and never lets the editor shrink below one line

Idle-today's height budget is:

```
visibleFrame.height
  − 2 × panelScreenMargin
  − titlebar safe-area inset
  − editor (one line when empty)
  − footer
  − section spacing / padding
```

On a 14-inch MacBook that is roughly 700–900 pt. Callout-sized rows are ~18–22 pt. Full trees of the current session plus a few planned ones will often fit after logs drop. A LATER-style day will not.

### Vault watching is coarse

`VaultTargetWatcher` watches the whole vault with FSEvents (`kFSEventStreamCreateFlagFileEvents | NoDefer`, 0.3 s debounce) and today refreshes **capture-targets** on any event. While the panel is visible it also refreshes the pomodoro count. The callback ignores event paths.

Idle-today refresh must filter to `sources[]`. A keystroke in an unrelated note must not spawn `--expand`.

### Task trees and logs are already parsed in Bob

| Need | Existing code |
| --- | --- |
| Scan today's ledger | `capture_pomodoros::scan` |
| Current vs future | unique open timed → `is_current`; open untimed placeholder → future |
| Pomodoro child range | `pomodoro_block_range` |
| Numbered Task Links | `capture_pomodoro_close::number_task_links` / `classify_numbered_line` |
| Resolve `[[note#^id]]` | close planner `CloseVault` + `vault_links::LinkResolution` |
| Find the task | `lookup_task` → `NoteTaskScan::by_block_id` |
| Full child block | `NoteTask.block_end` / `task_block_extent` |
| Work / Schedule Log markers | `parse_managed_task_log_marker` (emoji + `**WORK LOG**` / `**SCHEDULE LOG**`, legacy labels) |
| Depends-On line | `task_dependencies::is_dependency_line` |
| Plan budget | `plan_budget::compute_for_daily` |
| Clean task text | `note_tasks::clean_description` (picker already uses this) |

Swift already tokenizes pomodoro headlines and task rows without owning grammar (`CapturePomodoroLineTokens`). Status glyphs live in `CaptureEditorPalette.taskStatus`. Close-card number badges live in `PreviewPane.closeNumberBadge`.

### Caches already in the app

- `CaptureTargetsCache` (in-memory last-good, stale-on-error)
- Refs snapshot file (atomic 0600 JSON in Application Support, schema version, quarantine on corrupt)
- PDF inspector cache keyed by `(path, fileSize, mtime)`
- Panel geometry cache (`latestContentMetrics`) so a re-show does not wait for SwiftUI to re-emit

Idle-today should look like Refs: memory first, disk for cold launch, last-good on error, never block show.

### Thin-client rule

Decision `mac-capture-is-a-thin-client`: Bob owns grammar, completion, preview, and vault mutation. The app owns presentation, process orchestration, hotkey, settings. It may filter or rank what Bob returned. It must not parse the daily file or task notes to decide what a Work Log is.

Consequence: Bob tags regions. Swift hides tagged regions. Swift does not regex `🛠️ **WORK LOG**`.

---

## 4. Recommended solution

### 4.1 Command and JSON

Grow `bob capture-pomodoros` additively.

- Default invocation stays a cheap open-entry list (close-comma assist, pickers).
- New `-e, --expand`: also resolve Task Link trees, tag regions, emit `sources[]`, emit `plan_budget`, emit current `ends_at`.
- `schema_version` stays **1**. New keys are omitted by older Bob; the Mac uses `decodeIfPresent` and simply skips idle-today if `sources` / expanded `tasks` are absent.
- Human `--expand` prints a compact tree so the payload is debuggable without JSON.

Do not add a `bob capture` subcommand (TEXT would swallow it). A new sibling such as `capture-idle-preview` is a reasonable alternative if `--expand` threatens the cheap path's tests; the payload is the same. Prefer the flag first because the Mac already calls this command, the scan is identical, and CLI surface stays smaller.

#### Payload sketch

```json
{
  "ok": true,
  "schema_version": 1,
  "day_file": "/Users/bryan/bob/2026/20261009.md",
  "relative_day_file": "2026/20261009.md",
  "day_key": "20261009",
  "count": 4,
  "warnings": [],
  "sources": [
    {"path": "2026/20261009.md", "mtime_ms": 1728480000123, "size": 8421},
    {"path": "sase.md", "mtime_ms": 1728480100456, "size": 120034}
  ],
  "plan_budget": {
    "themes": {"count": 3, "cap": 3},
    "links": {"count": 4, "cap": 10}
  },
  "current": {
    "ref": "27:a1b2c3d4",
    "name": "CAPTURE",
    "time_range": "0945-1015",
    "ends_at": "2026-10-09T10:15:00",
    "task_link_count": 2
  },
  "pomodoros": [
    {
      "ref": "27:a1b2c3d4",
      "line": 27,
      "role": "current",
      "name": "CAPTURE",
      "slug": "capture",
      "time_range": "0945-1015",
      "placeholder": false,
      "is_current": true,
      "task_link_count": 2,
      "headline": "- [ ] (**0945-1015** [t:: 30m]) — CAPTURE",
      "notes": [],
      "tasks": [
        {
          "index": 1,
          "block_link": "[[sase#^idle-preview]]",
          "resolved": true,
          "relative_target": "sase.md",
          "block_id": "idle-preview",
          "line": 12,
          "status_symbol": "/",
          "status_name": "In Progress",
          "status_type": "in_progress",
          "text": "Idle pomodoro preview",
          "headline": "- [/] #task Idle pomodoro preview ^idle-preview",
          "regions": [
            {"kind": "depends_on", "lines": ["- Depends on: [[bob-cli#^x]]"]},
            {"kind": "body", "lines": ["- design the idle card"]},
            {"kind": "schedule_log", "lines": ["- 🗓️ **SCHEDULE LOG**", "\t- *2026-10-09* — 🍅 pulled"]},
            {"kind": "work_log", "lines": ["- 🛠️ **WORK LOG**", "\t- *2026-10-08* — sketched JSON"]}
          ]
        }
      ]
    },
    {
      "role": "future",
      "name": "READ",
      "placeholder": true,
      "is_current": false,
      "task_link_count": null,
      "tasks": []
    }
  ]
}
```

Rules for the expander:

- Include the current open timed Pomodoro when it exists, then every other **open** entry that is a placeholder (untimed). Skip completed. If several timed opens exist, keep today's warning, mark none `current`, and still list every open placeholder as future.
- A Task Link is a dedicated sub-bullet whose only contents are a block link — the same classifier as `classify_numbered_line` (plain, deferred, embedded). Index numbers appear only on the current entry and match `number_task_links`.
- Resolve through the existing vault linker. Unresolved links still render: `resolved: false`, `text` empty, `headline` is the daily-file bullet, one warning on that row. The card never fails closed.
- Task `regions` are a partition of `contents[task_line .. block_end]`, tagged by Bob. `depends_on` and `body` survive the first fold. `work_log` and `schedule_log` are the first fold. Unknown direct children are `body`.
- `sources[]` is the unique set of the daily file plus every successfully resolved task note. Unresolved links contribute no extra source. Paths are vault-relative so the app can join them to `BOB_DIR`.
- `ends_at` is naive local civil time on `day_key`. Swift interprets it in the Mac's current calendar. Omit `ends_at` on untimed entries.
- Duplicate tasks linked under current and a future appear in both places. The ledger is the source of truth.
- Non-link children of the Pomodoro (session notes) go in `notes[]`, shown under the headline at every density except a fully collapsed future.

`--expand` must not scan the whole vault. It reads the daily file once, then each distinct resolved note once.

### 4.2 Mac cache: blazing fast

New `IdleTodayCache` actor, plus a Refs-style on-disk snapshot.

**Hit path (the popup path):**

1. `show()` / `prepareForPresentation()` for an empty draft.
2. If memory has a snapshot whose `day_key` matches today:
   - `stat` each `sources[]` path (mtime_ms + size).
   - Full match → publish snapshot, set `previewState` to a new `.idleToday(IdleTodayPresentation)`, **zero `bob` spawns**.
3. Disk snapshot is loaded at process start (AppDelegate, next to panel `prewarm()`), so the first hotkey after reboot is also a hit when the vault has not changed.
4. Editor focus is requested in the same `show()` as today. Idle-today must not steal first responder.

**Miss / stale-while-revalidate:**

- Publish the last snapshot immediately (even if fingerprints miss), with a quiet `Updating…` caption only when the snapshot is known dirty.
- Spawn `capture-pomodoros --expand` on the existing `pomodoros` lane so it cancels in-flight expands and does not collide with parse/preview lanes.
- On success, replace memory + disk, update `currentPomodoroTaskLinkCount` from the same payload (one spawn serves close-comma assist too).
- On failure, keep last-good, same as `CaptureTargetsCache`.

**Prefetch so popup is almost always a hit:**

| Trigger | Action |
| --- | --- |
| `applicationDidFinishLaunching` after `prewarm()` | expand once |
| Successful capture | expand (the daily file just changed) |
| Filtered FSEvents on a `sources[]` path | debounce 0.3 s (existing watcher latency), then expand |
| Day key change (`day_key` vs local calendar date, or `BOB_NOW` in tests) | drop cache, expand |
| Panel show with empty draft and dirty fingerprints | expand (already on the show path) |
| Panel show with a retained non-empty draft | keep today's cheap count path; do not block typing with `--expand` |

Filter FSEvents by path. The current whole-vault refresh of capture-targets can stay; idle-today must not ride every event.

**What the cache stores:** the decoded JSON (or the Swift `IdleTodaySnapshot`), the fingerprint list, `day_key`, `fetchedAt`. Remaining-time is derived at render from `ends_at` + `Date()`, so a two-minute-old cache still shows a live countdown.

**What "daily file unchanged" means after A1:** if the daily file fingerprints match *and* every task-note fingerprint matches, skip the spawn. If the daily file matches and one task note moved, spawn. There is no half-refresh in v1; N note reads are cheap next to a missed popup frame.

### 4.3 Packing

Bob emits one structured tree. Swift picks a density per card.

```
enum IdleTaskDensity { case full, withoutLogs, singleLine }
```

Height estimate, good enough to pick before first layout:

```
rowHeight     ≈ 20 pt (callout, 1× display; 1/scale on Retina via existing round-to-pixel)
cardChrome    ≈ 28 pt caption + 8 pt padding
full(task)    = 1 + sum(region line counts)   rows
withoutLogs   = 1 + body + depends_on         rows
singleLine    = 1                             row
```

Budget = screen-derived auxiliary ceiling from `CaptureEditorHeightBudget` inverted: everything the sizer will actually give the preview after editor + footer + chrome.

Packer (pure, unit-tested, no SwiftUI):

1. Assign `full` to every task.
2. While estimated total > budget, drop `work_log`/`schedule_log` from the last future card, then earlier futures, then current.
3. While still over, convert those same cards to `singleLine`, last future first.
4. While still over, replace remaining future cards with one summary row.
5. Return the assignment plus `allowsScroll` if still over.

Then render. If `onGeometryChange` reports a height still above the sizer's clamp, drop one more step (at most one extra pass) and hold the previous pane height meanwhile — the same trick `CapturePreviewPaneHeightPolicy` uses, applied to idle-today.

Do not offscreen-render three complete variants. Do not ask Bob to pick a fold; Bob cannot see font metrics, wrapping, display scale, or the editor's measured height.

### 4.4 Visual design

The empty panel should feel like a quiet instrument cluster, not a dump of Markdown and not a capture diff.

**Chrome.** Same `.thinMaterial` rounded card as live preview, so switching from idle-today to a typed preview is a content swap inside a familiar pane, not a new window region. No "Preview" label. The content is the label.

**Identity strip (always on, even at maximum fold).** One row:

- Running: play.circle.fill in `CaptureEditorPalette` pomodoro-start tint, `NAME`, `HH:MM–HH:MM`, remaining `12:34` (or overdue `+01:12` in red, matching the Hammerspoon policy's overdue feel).
- Idle with futures: dashed circle, `No session running`, `Next up · NAME`.
- Nothing planned: the green calm of the menu-bar `NO POMODORO` — `No sessions planned today`.
- Missing daily file: Bob's existing warning string, one line, secondary.

Plan-budget capsules sit on the right of that strip (Themes 3/3, Links 4/10), green/red as today.

**Current card.** Caption `Running · NAME · line N` with play.circle.fill. Headline tokenized by `CapturePomodoroLineTokens` (checkbox, time range, em-dash name). Numbered task rows using `closeNumberBadge` geometry so `=x1` is visually the same 1. Status glyph from `taskStatus`. Full / without-logs densities render region lines with indent guides reused from `BlockDiffCard`, **without** the diff gutter or change washes. Work/Schedule log rows, when shown, sit at `.secondary` so the eye hits the task title and Depends-On first. Unresolved links: one warning caption, raw wikilink, `exclamationmark.triangle`.

**Future cards.** Caption `Queued · NAME`. Dashed circle, secondary rail. No numbers. Empty futures still appear (`nothing queued` in caption style) so the day's plan is visible. The next-up future (first future in document order, i.e. `next_future_pomodoro`) may carry a small `Next` capsule — the same marker `capture-complete` already uses on start-name rows.

**Density transitions.** No animation (live preview's rule: the pane updates, it does not perform). Fold chips (`12 lines`) match TaskBlockView. Expanding a fold focuses the editor afterward so typing is never trapped in the card.

**Empty / error.** Bob missing: last snapshot + the existing "Bob is not resolved" status, same as Refs. Expand failure: last snapshot, no modal. Multiple timed opens: Bob's warning in orange caption, cards still listed.

**Accessibility.** One combined label per card: `Running CAPTURE, 12 minutes remaining, 2 tasks, Idle pomodoro preview, In Progress`. Fold chips expose `Show work log`. Countdown updates are `.accessibilityValue` only, not a re-announcement every second.

**What this is not.** It is not a second editor. It is not click-to-capture in v1 (clicking a task to insert `@route:id` would be a natural follow-up; it is out of this request). It is not the Hammerspoon menu-bar indicator; that stays the always-visible countdown.

### 4.5 Panel state machine

| Draft | Preview |
| --- | --- |
| Empty, cache hit | `.idleToday(snapshot)` immediately |
| Empty, cache miss | last snapshot or identity strip; expand in background |
| Non-empty | today's live `.loading` / `.ready` / `.failed` path; idle-today stays cached but unmounted |
| Draft deleted back to empty | remount idle-today from memory, no spawn if fingerprints still match |
| Retained non-empty draft on re-show | live preview refresh (timing goes stale); idle-today stays out of the tree |

Replace `refreshCurrentPomodoroTaskLinkCount()` on the empty-show path with the expand fetch (which includes the count). Keep the cheap `capture-pomodoros` call when the retained draft is non-empty, so typing `=x` is not waiting on task-tree I/O.

### 4.6 Latency budget

| Path | Budget | How |
| --- | --- | --- |
| Panel order-front, cache hit | no `bob` spawn; first frame from memory | R6 |
| Fingerprint check | stats only, well under 1 ms for tens of files | `sources[]` |
| Background `--expand` | p95 < 100 ms on Bryan's vault for a typical day | one daily read + one read per distinct task note |
| Cache miss first paint | identity strip or last snapshot, never a spinner that collapses the pane | stale-while-revalidate |
| Typing | unchanged: 50 ms debounce, parse + dry-run | idle-today unmounted |

If Mac `--expand` p95 blows 100 ms, shrink work: skip `plan_budget` only after measuring it as the culprit (it should not be); never move parsing into Swift. A resident daemon remains premature until this budget fails in production, same conclusion as the 2026-08 replacement research.

---

## 5. Alternatives considered

**Empty `bob capture --dry-run` as the idle preview.** Reuses the live-preview decoder and `task_blocks` / `pomodoro_blocks`. Those blocks are cumulative diffs of a planned write. An empty draft is not a write. The empty path is also explicitly idle today. Rejected.

**New `bob capture-idle-preview` sibling.** Cleaner name, isolated tests. Costs another protocol command for a payload that is an expanded pomodoro list. Keep in reserve if `--expand` tangles the cheap list tests.

**Swift reads the daily file and task notes itself.** Fastest miss path, and it breaks `mac-capture-is-a-thin-client` the same way the Hammerspoon Lua grammar did. Rejected.

**Global all-or-nothing fold.** Simple. One fat Work Log then forces every future session to a single line. Progressive packing is the same two densities with a better assignment.

**Bob picks the fold, given a height hint.** Height is a function of fonts, wrapping, scale, editor measurement, and safe-area inset. Bob would guess, Swift would relayout anyway. Bob tags; Swift packs.

**Daemon / FFI / staticlib.** Zero spawn cost, stable ABI, aarch64 cross-compile. The replacement research rejected this at 5 ms spawn. Cache-first makes spawn *not the popup path*. Revisit only if fingerprint hits still feel slow (they should not: they are `stat`).

**Disk cache only, no fingerprints.** Would spawn on every show or serve stale trees. Fingerprints are the whole trick.

**Daily-file hash only, as requested.** See A1. Necessary, not sufficient.

**Reuse `BlockDiffCard` with all rows `.unchanged`.** Gets indent guides for free and paints a dead diff. A thin idle card that *shares* the indent-guide subview is fine; sharing the diff gutter is not.

---

## 6. Implementation sketch

Phase 1 is Bob, because the Mac cannot invent trees.

1. **`capture-pomodoros --expand`** in `src/native/capture_pomodoros.rs`. Reuse scan, `pomodoro_block_range`, `number_task_links`, `lookup_task`, `parse_managed_task_log_marker`, `is_dependency_line`, `plan_budget::compute_for_daily`. Tests: current+futures, completed omitted, unresolved link, log tagging, fingerprint set, multiple timed opens, missing daily note (empty list + warning, same as today).
2. **Docs:** `docs/capture.md` discovery section. Help text, options alphabetical, `-e` alias. JSON additive, schema 1.
3. **Swift decode** of the new keys with `decodeIfPresent`. Older Bob → idle-today stays hidden, close-comma still works.
4. **`IdleTodayCache` + disk snapshot.** Stat-before-spawn tests with a fake filesystem. Corrupt file quarantines like Refs.
5. **`IdleTodayPresentation` + packer tests.** Density assignment tables: "fits full", "drops logs on last future", "single-line futures, current keeps body", "summary row", "allowsScroll".
6. **`IdleTodayView`.** Identity strip, current card, future cards, budget capsules, local countdown, fold chips. Design tests next to `PomodoroBlockDesignTests` / `CapturePreviewFullHeightTests`.
7. **Wire `prepareForPresentation` / `show` / `editorTextDidChange` empty path / AppDelegate prefetch / filtered FSEvents / capture-success.** Empty show sets `currentPomodoroTaskLinkCount` from the expand payload.
8. **Measure on the Mac.** Signpost `idle-today-hit` vs `idle-today-expand`. Confirm order-front does not wait. If expand is fat, profile note reads before anything clever.

bob-cli lands first (thin-client rule). The Mac phase decodes and presents. An older Bob on the Mac is a graceful no-op.

---

## 7. Risks

- **Popup height jump.** First show after a miss grows the window when expand returns. Mitigation: disk cache after first launch; on a true miss, grow once from the identity strip, never collapse-then-grow through `.loading`.
- **Editor squeezed.** A tall idle card must not steal the last line of editor. `CaptureEditorHeightBudget.minimumEditorHeight` already protects this; keep it.
- **Stale trees.** Fingerprints miss a same-size same-mtime rewrite (rare on APFS). Accept; FSEvents still fire on the write. Do not content-hash every task note on the hit path.
- **Obsidian save storms.** Typing in a linked task note invalidates correctly. 0.3 s debounce matches today's watcher. Filter to `sources[]` so the rest of the vault is quiet.
- **Huge Work Logs.** Packing drops them first. Full density is still in the payload so a fold chip can open one log without a spawn.
- **Midnight.** `day_key` mismatch drops the cache. A panel left open across midnight should refresh; a 60 s calendar timer or the next show is enough. Do not tick day-key every second.
- **Contract drift.** Expand must use `number_task_links` and the managed-log parser. A second "what is a Task Link" implementation will desync from `=x`.
- **Visual noise.** Some days have many empty placeholders. Empty futures stay one caption line. That is the day's plan; hiding them would lie.

---

## 8. Follow-ups (out of scope)

- Click a task row to insert `@route:id` (or `:` picker already on that task). Natural, not required to glance.
- Click the current card to prefill `=x`. Tempting; teach via numbers first.
- Sync remaining-time copy with the Hammerspoon item (overdue badge at +10 min, 1 Hz flash). Nice, separate.
- Interactive "show logs" remembered per block id across popups. Skip until the default packing feels wrong.

---

## 9. Recommended solution (single paragraph)

Ship an idle-today card as the empty-draft preview of Bob Mac Capture. Bob grows `capture-pomodoros --expand` with tagged task regions, plan budget, `ends_at`, and a `sources[]` fingerprint list; the Mac paints a cached snapshot on the first frame, stats those sources to skip a spawn, and only then refreshes in the background. The window grows to the card; a pure packer walks the requested density ladder (full tree → drop Work/Schedule logs → single-line) from later futures toward the current session so the running work stays richest; the existing auxiliary scroller is the last resort. The card reuses palette, headline tokens, close-lineup numbers, and budget capsules, and it leaves mutation diffs to live capture preview. Prefetch at launch, after capture, on filtered FSEvents, and at day change so the hotkey path is a cache hit. That is the design that is intuitive (now-and-next on the panel Bryan already opens), reliable (one scanner, additive JSON, last-good cache), and fast enough to stay beautiful.
