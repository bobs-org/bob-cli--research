# Pomodoro Day-Preview in bob-mac-capture: research (`__mus`)

Researcher: mus. Date: 2026-10-09. Scope: default (empty-draft) preview showing the
current pomodoro (if any) plus all future pomodoros, with resolved task contents,
caching, adaptive folding, and window-height expansion.

Evidence below is from code I actually read this session: `CapturePanelModel.swift`
(empty/draft gating, preview lanes, presentation hooks), `CapturePanelView.swift`
(layout constants), `CapturePanelWindowSizer.swift`, `VaultTargetWatcher.swift`,
`TaskBlockView.swift` / `PomodoroBlockView.swift` / `BlockDiffCard` presentation,
`BobProcessClient.swift` (`captureLivePreview` lane), `CaptureModels.swift`
(`CapturePomodoroBlock`, `CaptureTaskBlock`, `CaptureCommandSuccess`), bob-cli
`src/native/capture_pomodoros.rs` (read-only ledger lister), `src/native/pomodoro.rs`
(ledger parsing), `src/native/note_tasks.rs` (task extents), the thin-client decision
record (`decisions:mac-capture-is-a-thin-client`), and glossary entries for Pomodoro,
Task Link, Work Log, and Schedule Log.

## 1. What the request is asking for

1. When the capture panel pops up with no input typed, show a preview by default:
   the current pomodoro (if any) and all future pomodoros from today's daily file.
2. Cache that preview aggressively keyed on "daily file contents haven't changed",
   because the panel must stay blazing fast.
3. For every task link in those pomodoros, show as much of the task as fits without
   scrolling the preview pane, expanding the window height as needed.
4. Otherwise fold, in priority order: (a) hide each task's Work Log and Schedule Log
   but keep all other sub-bullets; (b) collapse each task to a single line.
5. Lead the design: intuitive, reliable, beautiful.

## 2. Where this plugs into the existing architecture

- **Thin-client contract is load-bearing.** Per the accepted decision, bob-cli owns
  capture grammar, preview computation, and vault mutation; the app owns
  presentation, orchestration, hotkey, and packaging, and renders what `bob`
  returns over JSON. Any new preview semantics must land in bob-cli (plus
  `docs/capture.md`) first, with additive JSON the app decodes tolerantly
  (`decodeIfPresent`, fixed `schema_version`). The app must not parse daily files,
  resolve task links, or detect Work/Schedule Log sections in Swift.
- **Today's empty state shows nothing.** `CapturePanelModel.hasDraft` is
  `!plainDraft.trimmingCharacters(...).isEmpty`, and every preview path is gated on
  it: `scheduleAnalysis` early-returns, `submit`/`preview` return, and
  `prepareForPresentation()` calls `resetAnalysisState()` (preview `.idle`) when
  there is no retained draft. So the requested feature is a genuinely new state —
  call it `dayPreview` — not a tweak to the live-preview debounce.
- **The building blocks already exist on both sides.** bob-cli has a read-only
  `bob capture-pomodoros --format json` (document order, `is_current`,
  `task_link_count`, `--all` for completed, empty-list-with-warning for missing
  file/section), a `number_task_links` routine, linked-task resolution
  (`capture_pomodoro_close/linked_tasks.rs`), task extents
  (`task_block_extent` in `note_tasks.rs`), and batch `task_blocks`/`pomodoro_blocks`
  after-states already rendered by `TaskBlockView`/`PomodoroBlockView` on the shared
  `BlockDiffCard`. The app already has a screen-budget sizer
  (`CapturePanelWindowSizer`), a vault FSEvent watcher (`VaultTargetWatcher`), and a
  fold pattern (`CaptureTaskBlockPresentation`: runs of unchanged rows collapse past
  `foldThreshold = 24`, minimum run 4, expandable, reset on identity change).

## 3. Critique: is this a good idea?

**Yes, with three corrections.** Showing the day when the panel opens converts a
blank box into context: "what am I in, what's next, what did I attach to it." The
panel already pops up dozens of times a day; a stale-free day view removes a vault
round-trip the user would otherwise do by hand. The risk is not the idea, it is
latency, ambiguity, and unbounded content — all fixable:

1. **Latency risk is real but bounded.** The decision record measured
   `bob capture --dry-run --format json` at ~5 ms on athena; a day-preview that
   resolves N task links across M project notes will cost several file reads, still
   far below the 20 s `BobProcessClient.defaultTimeout`, but no longer "one tiny
   spawn". That is why the cache and the single-endpoint design (section 5) matter:
   per-task fan-out from Swift (one `capture-link-tasks` per link) would multiply
   spawns and JSON parses on every popup. One bob call returning the whole day view
   keeps popup cost at one spawn.
2. **Empty-state ambiguity must be designed away.** Today empty means "type to
   capture". If empty suddenly also means "here is your day", the user needs an
   unmistakable visual register shift (read-only cards + explicit header such as
   "Today — type to capture"), and typing must instantly replace the day view with
   the normal live preview. Never reuse the draft-preview card styling 1:1 for the
   day view or users will think the panel is about to capture their whole day.
3. **"Show everything that fits" needs a cap, or one giant task eats the day.**
   Full task definitions with all sub-bullets are unbounded (long Work Logs are the
   norm, not the exception). Global folding ("all full, else all no-logs, else all
   single-line") is simple and predictable, but a single verbose task can force
   every other task into single-line mode. I recommend keeping the requested global
   priority as the default while allowing per-task greedy upgrade where it is cheap
   (see section 6) — or at minimum capping lines per task before measuring fit.

## 4. Adjustments to the requirements (called out)

1. **[ADJUSTMENT] Cache key must cover task notes, not just the daily file.** The
   request says "when the daily file's contents haven't changed at all". Task bodies
   live in area/project notes, not in the daily file (the daily file holds only the
   task *link*). A daily-file-only key serves stale task text after any task edit.
   Bob must compute the cache key over all inputs (daily file + every resolved task
   note, or a hash thereof) and return it; the app keys on that.
2. **[ADJUSTMENT] Define "current" and "future" precisely.** Glossary: past =
   closed with timespan, current = open with timespan, planned = open placeholder.
   Recommend: *current* = the open entry whose time range contains now, else the
   first open entry (the session the user is about to start); *future* = open
   entries after current in document order, excluding completed. "All future" should
   gain a sane cap (recommend: next 3–5 open entries, with a "+N more" row) so a
   heavily-planned day cannot blow the screen budget on first paint.
3. **[ADJUSTMENT] Fold is per-task-budget, measured top-down — and Work/Schedule
   Log folding must be server-marked.** The request's two folded views are a good
   priority order, but the app cannot find "the Work Log" by string-matching
   `🛠️ **WORK LOG**` in Swift without violating the thin-client rule and breaking
   on grammar changes. Bob must return fold ranges (byte/line ranges tagged
   `work_log` / `schedule_log`) or, simpler, pre-rendered variants. I recommend
   structured ranges over tripled payloads (section 5).
4. **[ADJUSTMENT] Timestamps make "unchanged content" insufficient for cache
   reuse.** Close-preview code already notes `closed_at`/timing goes stale while
   hidden. A day view contains time ranges and possibly "ends in N min" captions:
   cache entries need an `as_of` timestamp; the app re-renders captions
   client-side and refetches when older than ~60 s or across a day rollover,
   even with identical content.
5. **[ADJUSTMENT] "Expand the window as necessary" is bounded by the screen, then
   folds.** The sizer already clamps to `availableScreenHeight - 2*screenMargin`.
   The correct algorithm is: measure day view at full verbosity → if it fits the
   screen budget (minus one-line editor + footer + margins), grow the window and
   show full → else try no-logs → else single-line → else scroll the preview pane
   internally (never grow the window past the screen, never steal editor space
   below one line).

## 5. Design: the recommended solution

**One new read-only bob endpoint; one new app empty-state; cache by content hash.**

### 5.1 bob-cli: `bob capture-day-preview --format json` (name negotiable)

- Read-only. Reads today's daily file (`BOB_DAY_FILE`/`BOB_DIR`/`BOB_NOW`
  conventions, same as `capture-pomodoros`), scans the Pomodoros section in
  document order, resolves each current/future entry's task links through the
  existing linked-task resolution, and returns task blocks with structured lines.
- Returns, per pomodoro: `line`, `name`, `time_range`, `status`
  (`running`/`queued`/`completed`/`other` — reuse `CapturePomodoroBlockStatus`),
  `is_current`, and per task: full verbatim lines plus `fold_ranges` tagging
  `work_log` and `schedule_log` spans (reusing the `task_block_extent`/child-span
  machinery, never Swift string matching).
- Returns cache metadata: `content_hash` over daily file + all resolved task-note
  bytes (plus schema version), `day_file`, `as_of` timestamp. Missing daily file
  or missing Pomodoros section returns success + empty list + warning, mirroring
  `capture-pomodoros` — the panel renders an encouraging empty state, never red.
- Additive JSON only; human format optional. Document in `docs/capture.md` first.

Why a new command rather than overloading `capture --dry-run ""`: empty-draft
semantics inside `capture` would tangle the submit guards (`hasDraft`, pending
separators, clipboard lanes) and risk turning a no-op into a routable capture.
A separate read-only command keeps the `preview`/`submit` lanes untouched and gives
the app a distinct cancellable lane (`day-preview`).

### 5.2 App: empty-state loader in `CapturePanelModel` + views

- On `prepareForPresentation()` with no draft: show last cached day view instantly
  (if hash still valid per section 5.3), then fire one `day-preview` call on its
  own lane (cancellable by the first keystroke). First keystroke cancels it and
  runs the normal debounced parse/completion/live-preview; the day view never
  lingers beside a draft.
- Render with the existing card language (`PomodoroBlockView` caption rows,
  `BlockDiffCard`, wrap-don't-truncate, no animation) plus a distinct day header
  ("Today — type to capture") and a "+N more" overflow row. Reuse the fold UX from
  `TaskBlockView` (expandable folds, reset on identity change, VoiceOver labels).
- Height: measure ideal day-view height through the existing metrics pipeline;
  grow via `CapturePanelWindowSizer` up to the screen budget; fold down
  full → no-logs → single-line before ever scrolling internally.

### 5.3 Caching (the "blazing fast" requirement)

- In-memory cache keyed by `content_hash`: hash hit → render synchronously, zero
  spawns. Hash miss → one spawn.
- Freshness check on every popup must be cheaper than the spawn it avoids: `stat`
  daily file (mtime+size) as a fast path — unchanged stat reuses the hash without
  re-reading; changed stat (or any FSEvent from `VaultTargetWatcher` on the vault)
  triggers one `capture-day-preview` call whose returned hash becomes the new key.
  Because task notes are transitive inputs, also subscribe the watcher to resolved
  task-note paths from the last response (bounded list), not just the daily file.
- Stale-while-revalidate: show cached cards immediately with a subtle
  recalculating indicator only if the refetch takes more than a frame or two;
  never flash `.loading` over warm content. Cap cache age with `as_of` (refetch
  past ~60 s for live countdown correctness; always refetch across day rollover).

### 5.4 Performance budget (proposed acceptance bar)

- Warm popup (hash valid): first paint from cache, no spawn on the critical path.
- Cold popup: one `capture-day-preview` spawn; target well under the existing
  preview feel (single-digit-ms grammar spawns are the precedent; budget low
  hundreds of ms p95 on Mac hardware, measured, not assumed).
- Verify with the panel's existing signpost instrumentation (`CaptureSignpost`)
  around the new lane.

## 6. Folding detail: why the requested order works, and one refinement

Full → no-logs → single-line is the right priority: Work/Schedule Logs are
append-only history and usually the longest spans, while "all other sub-bullets"
(acceptance criteria, checklists, Depends-On lines, child tasks) are the actionable
context the user wants while planning a session. Single-line-last preserves
at-a-glance identity ("which tasks are in this pomodoro") when nothing else fits.

Refinement: apply the ladder **per task, greedily, in pomodoro order** rather than
globally all-or-nothing where cheap to do so — fill current pomodoro full first,
then future ones downgrade in reverse order. A strict global ladder lets one
10-line Work Log demote five crisp tasks; greedy keeps the common case (short day,
one verbose task) beautiful. If greedy is deemed too clever for v1, ship the global
ladder exactly as requested — it is predictable and easy to explain — and add
greedy as a follow-up.

## 7. Reliability notes

- New endpoint is read-only and dry-run-equivalent: it never writes the vault, so
  showing it on every popup is safe by construction.
- Decode tolerantly (`decodeIfPresent`, unknown enums → `.other`/`.unchanged`,
  malformed task → skip row, never fail the day) and pin `schema_version`.
- Empty/error states: no pomodoros → calm empty illustration + hint, not an error
  card; bob-unresolved → existing "Bob is not resolved" path; in-flight fetch
  cancelled on type, on panel dismiss, and superseded by newer generations
  (reuse the existing `analysisGeneration` pattern).
- Accessibility: combined-element cards with summaries, "Show all lines" actions,
  and the day header exposed as a heading.

## 8. Recommended solution (summary)

Ship it, with the adjustments in section 4. Concretely:

1. bob-cli first: new read-only `capture-day-preview --format json` returning
   current + next-N open pomodoros with resolved task blocks, server-marked
   `work_log`/`schedule_log` fold ranges, `content_hash` over all input files,
   `as_of`, and empty-with-warning (not error) for missing file/section.
2. App: new empty-state day view on popup (cached-first, one cancellable lane,
   killed by first keystroke), rendered in the existing card language with a
   distinct "Today — type to capture" header, window grown via the existing sizer
   up to the screen budget, folding full → no-logs → single-line (global ladder
   v1; greedy per-task upgrade as fast follow).
3. Cache: key on bob-returned `content_hash`; fast-path `stat` + FSEvent
   invalidation covering daily file *and* resolved task notes; stale-while-
   revalidate with `as_of` expiry (~60 s) and day-rollover refetch.
4. Acceptance: warm popup paints from cache with no spawn; cold popup costs one
   spawn inside a low-hundreds-of-ms p95 budget; no scroll in any ladder step that
   fits the screen; zero grammar/parsing code in Swift — all folding metadata
   comes from bob.

The requested requirements survive essentially intact; the material changes are:
cache key covers task notes (not just the daily file), current/future get exact
definitions plus a display cap, fold spans are server-marked, timestamps bound
cache reuse, and window growth stops at the screen before internal scrolling.
