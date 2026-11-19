# Log-history navigation (`Ctrl+N` / `Ctrl+P`) for schedule, work, rotten, and cancel prompts

Researcher: `mus` · 2026-11-19 · bob-cli / bob-plugins / bob-mac-capture

## Summary

The request is a good idea and should be built, with adjustments. Re-typing the
same schedule reasons, work summaries, keep reasons, and cancel reasons across
tasks is real toil, and the four prompts already share one visual language
(single-line input + live formatted preview + `↵` commits / `esc` cancels), so
one history interaction can cover them all. But the request as written
under-specifies the surface, the storage, and the keybinding, and each of those
needs a correction before implementation:

1. There are not 3 histories but **4**, and not "several" inputs but **at
   least 7 inputs** mapping onto those 4 histories.
2. `Ctrl+N` / `Ctrl+P` cannot be a global history binding: those chords already
   move the highlight in every filtered picker list in the vault.
3. History must not be a new vault store. The vault already *is* the history
   (every committed log entry), and the persisted layer should be a small
   capped MRU plus a vault scan for seeding — with `bob` as the only source
   the Mac client may read, per the thin-client rule.

Recommended: per-kind global MRUs (schedule / work / rotten / cancel),
shell-style recall (`Up`/`Down` plus `Ctrl+P`/`Ctrl+N` aliases **only inside
the single-line reason inputs**, where no list consumes those chords),
filter-as-you-type against the MRU with the existing live preview, one commit
writes one history entry, and Mac reads the same history through a new
read-only `bob` JSON surface instead of a Swift-local store.

## Where the prompts actually are

All paths below were read in this session. Line references are to the current
checkouts.

### Obsidian — Task Card / review / lane prompts (bob-navigation-hotkeys + block-id-prompt)

- **Schedule reason + Work summary (combined review form).**
  `plugins/bob-navigation-hotkeys/src/370-picker-schedule-work-log.js` —
  `renderScheduleReviewForm()` renders two inputs: `Reason for this date
  (optional)` and `Work summary (optional · …)`, with live preview in
  `renderScheduleReviewPreview()`. Commit path is `confirmScheduleReview()`.
- **Work summary alone (scheduling Pending/Next).**
  Same file — `showSchedulingWorkLogStage()` / `renderSchedulingWorkLogPreviewItem()`
  / `confirmSchedulingWorkLog()`. This input writes a **Work Log** entry, not a
  schedule entry, even though it is reached from a scheduling gesture.
- **Cancel reason.** `plugins/bob-navigation-hotkeys/src/380-picker-cancel-and-lane.js`
  — `showCancelReasonStage()` (`Why cancel it? (optional · ↵ to skip)`),
  preview `renderCancelReasonPreviewItem()`, commit `confirmCancelReason()`.
- **Release summary (lane release).**
  Same file — `showLaneReleaseReasonStage()` (`Why is this pending?
  (optional · ↵ to skip)`). This also writes a **Work Log** entry.
- **Keep reason (rotten).**
  `plugins/bob-navigation-hotkeys/src/192-freshness-refresh-summary-modal.js`
  (`Why keep them? (optional · ↵ logs 🤷)`, single and batch paths) backed by
  the `RottenKeepReasonStage` model (`buildRottenKeepPromptModel`), plus the
  decay card in `plugins/bob-navigation-hotkeys/src/060-decay-card-modal.js`.
  Every counted keep / stay / step / drop writes one `🥀 **ROTTEN LOG**` entry;
  blank logs `🤷 no reason given`.
- **Move-to-Next work summary (Task Link lane).**
  `plugins/bob-navigation-hotkeys/src/196-task-link-lane-modal.js`
  (`TaskLinkLanePromptModal`: `What did you get done?`, live preview via
  `taskLinkLanePromptState()`).
- **Unlink-task work summary (In Progress unlink).**
  `plugins/block-id-prompt/src/090-prompt-modals.js` (`WorkSummaryPromptModal`,
  `bid-wlp`: `What did you get done?`, preview `workSummaryPromptState()`).

### Mac capture panel (bob-mac-capture)

The capture panel has exactly **one** free-text log-reason input today: the
inline pull-in cancel field in
`Sources/BobMacCapture/CapturePullInChoiceView.swift` (`CapturePullInReasonField`:
`Why cancel? (optional)`, text managed by `CapturePanelModel`
`updatePullInReasonText()` / `confirmPullInReason()` /
`restorePullInReason()`). There is no schedule-reason, work-summary, or
keep-reason field in the panel; capture expresses those through draft grammar
(`$`, `x`, `~` handling in `bob capture`) and through `bob`'s returned
previews, which the panel renders verbatim. This matters for scope: the Mac
work is one field, not four, and per
`decisions:mac-capture-is-a-thin-client` it must not parse grammar, compute
previews, or own a history store — it renders what `bob` returns.

### `bob` (Rust) — the log writers

`src/native/capture_schedule_log.rs` (`entry_text()`, `priority_roll_reason()`,
`randomize_reason()`), `src/native/capture_work_log.rs` (stamped
`*YYYY-MM-DD HH:MM* — summary` entries), `src/native/task_cancel/line.rs`
(`CancelLogOutcome`), and `src/native/task_children.rs` (managed-child order:
Cancel, Depends-On, BLOCKS, LINKS, then Schedule / Work / Rotten logs) are the
ground truth for entry grammar. The glossary strands read for this report
(`glossary:schedule-log`, `glossary:work-log`, `glossary:rotten-log`,
`glossary:task-decay`, plus `decisions:task-decay-is-one-ladder` and
`decisions:rotten-keeps-are-logged`) confirm: logs are newest-first direct
children, `🤷 no reason given` is a real written body for blank keeps, and
freshness gestures never write the Work Log.

## Critique 1 — the keybinding as specified collides

`Ctrl+N` / `Ctrl+P` already mean "move the highlight" in every filtered list
in the vault: Command Mode (`docs/bob-command-mode.md`: "`↑` / `↓` and
`Ctrl+P` / `Ctrl+N` … move"), Copy Card (`docs/copy-card.md`), the successor
picker (`scripts/test-navigation-successor-picker.cjs`: "`Ctrl+N` / `Ctrl+P`
move the highlight like ArrowDown / ArrowUp"), Pomodoro theme rows, album
catalog rows, and the Task Card's own value/filter stages (keydown dispatch in
`plugins/bob-navigation-hotkeys/src/450-picker-keydown.js`:
`handleKeydown()`). Two more collisions: on macOS, Mission Control's "Switch
to Desktop N" shortcuts steal `Ctrl+N` when enabled
(`docs/window-keys.md`), and `Ctrl+[` / `q` / `Esc` are the universal
close-without-write chords that must keep working from inside any reason
field.

The good news: the collision is avoidable because the reason inputs that need
history are **not list stages**. `showCancelReasonStage()`,
`showSchedulingWorkLogStage()`, `showLaneReleaseReasonStage()`, the schedule
review form, the keep form, and the two Work-summary modals all set
`items: []` (or render a dedicated form) — there is no highlight to move, so
`Ctrl+N` / `Ctrl+P` are currently dead keys there. The rule should therefore
be scoped, not global:

- Inside a **single-line log-reason input** (the 7 inputs above, plus the Mac
  pull-in reason field): `Ctrl+P` = previous history, `Ctrl+N` = next
  history; `Up` / `Down` are aliases with identical behavior. This matches
  readline / shell / VS Code QuickInput muscle memory, which is exactly the
  audience.
- Everywhere a picker list is visible (Task Card values, successor offers,
  relation stage, theme rows): `Ctrl+N` / `Ctrl+P` keep their existing
  highlight meaning and never touch history.
- While composing (IME `isComposing`) or with any other modifier (`Alt`,
  `Meta`, `Shift`), the chords do nothing — same guard the pickers already
  use for `~` and quick-roll keys.

Do not add `Ctrl+R` reverse-search or `Tab`-to-accept in v1. `Tab` already
cycles focus between the two schedule-review fields
(`cycleScheduleReviewFocus()`); overloading it to accept a history row would
break keyboard-only completion of the combined form. History recall must never
auto-fill: the input starts empty (or with the per-task suggestion, if any)
and only an explicit history keystroke replaces its contents. Accidental
writes of someone else's reason are the worst failure mode here; explicit
recall plus the existing live preview is the guard.

## Critique 2 — filtering and live preview: yes, both, because both already exist

The question in the brief ("should we filter / live-preview?") is already
answered by the codebase: every one of these prompts **already live-previews
the exact bytes that will be written** (`renderScheduleReviewPreviewItem()`,
`renderCancelReasonPreviewItem()`, `renderSchedulingWorkLogPreviewItem()`,
the lane/keep/work-summary `updatePreview()` paths, and the Mac
`accessibilityLabel` "will be cancelled: …" suffix). Typing already
re-renders on every `input` event with `appendHighlighted()` query
highlighting in list stages. Removing that for history would be a regression;
the right move is to extend it:

- As the user types, filter the per-kind MRU by case-insensitive substring
  and show at most ~8 matches newest-first under the existing preview row,
  reusing the current row styles (`bob-cnp-schedule-reason-row`,
  `bob-cnp-cancel-reason-row`, `bid-wlp-*` / `bob-tll-*` families) and the
  `aria-live="polite"` preview region.
- The top preview row keeps showing the **formatted entry** (`*date* —
  reason`, `*stamp* — summary`, `· kept N×` tail for keeps), not the raw
  string, so what-you-see is what will be prepended under the log marker.
- Filtering never writes and never reorders the MRU; it only narrows the
  visible window. `Esc` with a non-empty filter first clears the filter,
  second restores the pre-recall typed text, third closes without writing
  (standard staged-Esc; matches the existing "Esc keeps the task open"
  contract on `getCancelReasonHints()`).
- Keep the `::` inline-field warning exactly where it is (every preview path
  already renders `"::" creates a Dataview inline field on this bullet`).
  History entries containing `::` stay selectable but keep the warning; they
  are common in schedule reasons that mention times.

## Critique 3 — the storage as specified leaks and splits

"Stored separately, for all tasks" is right about the shape (one MRU per log
kind, global across tasks) but wrong if it implies a new vault note or a
client-local-only list:

- A vault note or frontmatter list would sync conflicts, pollute search, and
  fight `bob vault-sync`. A Swift-local or `localStorage`-only list would
  strand the Mac panel and violate the thin-client decision.
- Free-text reasons are the most sensitive strings in the vault (cancel
  reasons name people and projects). A global MRU surfaces task A's reason on
  task B by design — that is the requested feature — but it must therefore be
  capped, deduped, skippable, and never auto-inserted (see above), and it must
  exclude the non-reasons: empty input, `🤷 no reason given` (the blank-keep
  fallback), pure date/emoji auto-bodies (`🎲 … roll` schedule bodies from
  `priority_roll_reason()` / `randomize_reason()`), and entries over ~200
  characters.

Precedents read in this session point to the shape that fits:

- Per-host vault-synced journals (`decisions:theme-preferences-live-in-a-per-host-journal`,
  `decisions:relation-label-prefs-live-in-a-per-host-journal`:
  `.bob/themes/<host>.jsonl`, `.bob/relations/<host>.jsonl`, last-writer-wins,
  `bob` the only writer) — right for synced preferences, heavy for 4 high-
  churn MRUs.
- Plugin `saveData` recents (emoji: `emojiRememberRecent()` /
  `emojiRecordRecent()` in `plugins/bob-emoji/src/050-plugin.js`, best-effort
  persistence, session list survives failure) — right for device-local
  ordering, wrong as the cross-client source.
- The vault itself as seed: every committed log entry is already parseable by
  the `task_children` / schedule-log / work-log / rotten-log grammars, so a
  fresh device can rebuild a useful history without any import step.

## Adjustment — the brief omits the rotten history and mis-maps the work history

Call this out explicitly, because building exactly what the brief says would
ship two bugs:

1. **There must be 4 histories, not 3.** The brief lists schedule / work /
   cancel but the opening paragraph includes rotten ("schedule log, work log,
   rotten log, and/or cancel log"). Keep reasons are the single most-repeated
   strings in the system (weekly-kept reading tasks re-log the same 2–3
   reasons; see `decisions:task-decay-is-one-ladder` journal evidence: 88 Next
   keeps over 22 days). Shipping history for the other three and not for keeps
   would miss the highest-frequency win. Add `rotten` as the fourth MRU.
2. **Two "scheduling" inputs write to the Work history, not the Schedule
   history.** `showSchedulingWorkLogStage()` and both unlink/release prompts
   (`WorkSummaryPromptModal`, `TaskLinkLanePromptModal`,
   `showLaneReleaseReasonStage()`) all prepend under `🛠️ **WORK LOG**`. Their
   recall source must be the **work** MRU even when the gesture started from
   the Task Card's schedule flow. The mapping is input→log-kind, not
   gesture→log-kind:
   - schedule MRU ← schedule-review reason field only;
   - work MRU ← schedule-review summary field, scheduling work-log stage,
     lane-release stage, unlink prompt, move-to-Next prompt;
   - rotten MRU ← keep-reason fields (single, batch, decay card Keep/Stay);
   - cancel MRU ← cancel-reason stage (Obsidian) + pull-in reason field (Mac).
   Steps/drops that also write a Cancel Log entry (decay-card D) do not write
   the cancel MRU unless the user typed in a cancel field; the MRU records
   typed strings, not derived `🍂 … → dropped` bodies.

## Recommended solution

### A. Data: 4 capped global MRUs, vault-seeded, `bob`-served

- **Shape.** Four ordered lists: `schedule`, `work`, `rotten`, `cancel`.
  Each entry: `{ body, firstUsed, lastUsed, uses }`. Ordering is
  last-used-first; ties break by `uses` then lexicographically (stable, no
  jitter while typing). Cap 50 per kind; dedupe case-insensitively on
  normalized trim (`normalizeScheduleReasonText()` /
  `normalizeLaneWorkSummary()` equivalents already exist — reuse them).
- **Write rule.** Exactly one MRU append per committed prompt, in the same
  transaction path that already writes the log (`confirmScheduleReview()`,
  `confirmSchedulingWorkLog()`, `confirmCancelReason()`, keep `submit()`,
  `submitPomodoroWorkSummary()`, pull-in confirm). Blank, `🤷`, auto-roll
  (`🎲`), and `::`-only bodies never enter the MRU. Counted/batch sessions
  write one entry per commit, not one per task.
- **Read rule.** `bob` owns the lists and serves them read-only over the
  existing versioned JSON surfaces the panels already consume (agenda /
  preview JSON for Obsidian via `bob-ledger-tools`, subprocess JSON for the
  Mac panel). Obsidian plugins keep a session copy and persist it with the
  existing best-effort `saveData` recents pattern; on load they seed from
  `bob` first, then from a bounded vault scan of existing log children
  (newest-first, same parsers), so a fresh install is useful on day one and
  an offline vault still recalls the session list. No new vault file, no new
  frontmatter, no Swift-owned file.
- **Sync/privacy posture.** Session recall is device-local (like emoji
  recents); the vault scan is the cross-device story (committed entries
  travel with the vault through the existing git sync). Do not sync the MRU
  counters through `.bob/*.jsonl` in v1 — churn is too high for a
  last-writer-wins journal, and the vault scan already converges. Revisit only
  if Bryan reports "my Mac doesn't know my Obsidian reasons" after a week of
  use.

### B. Interaction: scoped chords + filter + preview (the beautiful part)

- **Recall.** In any log-reason input: `Ctrl+P` / `Up` = older, `Ctrl+N` /
  `Down` = newer, cycling with wrap; the first recall from an empty input
  shows the newest entry, from a non-empty input shows the newest entry that
  is not the current text (so the user's partial typing is never lost —
  stash it as the "draft" at the new end of the cycle, shell-style).
- **Filter.** Typing filters the MRU (substring, case-insensitive) into a
  capped suggestion row set under the existing formatted preview; `Up`/`Down`
  while filtered moves through matches only. Highlight matches with the
  existing `appendHighlighted()` helper.
- **Preview.** The top row always renders the formatted entry with the
  current stamp/date logic untouched (render-time clock for work stamps,
  `valueBaseDate` day for schedule/cancel/rotten — the tests pin this:
  `test-navigation-hotkeys-work-log-stamp-closeout.cjs`,
  `test-navigation-roll-decay.cjs`). Effects lines ("Prepends under 🛠️
  **WORK LOG** …", "Adds ❌ **CANCEL LOG** as the first child") stay as-is.
- **Commit/cancel.** `↵` commits input + writes MRU; `esc` staged
  (clear-filter → restore-draft → close-without-write). Footer hints gain one
  affordance line: `Ctrl+P / Ctrl+N history` alongside the existing
  `↵`/`esc` hints (`getCancelReasonHints()`,
  `getSchedulingWorkLogHints()`, `getLaneReleaseReasonHints()` equivalents
  plus the keep/Task-Link/Unlink footers).
- **Mac.** Same chords in `CapturePullInReasonField` via the existing
  `CaptureKeyCommandRouter` / `CapturePickerFilterField` focus path; the list
  comes from the `bob` history payload already attached to the pull-in
  preview, and `updatePullInReasonText()` otherwise stays untouched. No new
  Swift persistence. Respect reduced-motion and VoiceOver labels the way the
  current field does (`accessibilityLabel`, `↵ · Esc back` caption).

### C. What not to build

- No per-task histories (the brief explicitly rejects this; per-task would
  also never accumulate enough repeats to matter).
- No automatic MRU insertion into empty inputs, no "most common" default
  body, no reordering of the MRU by filter, no `Tab`-accept, no `Ctrl+R`.
- No history for auto-generated bodies, stamps, block IDs, relation labels,
  or Pomodoro names — each already has its own recents/vocabulary path
  (Pomodoro theme recents, emoji recents, relation-label vocabulary).

## Edge cases the plan must cover

- Empty vault / fresh device: seed from scan finds nothing → history keys do
  nothing (no beep, no toast); the prompts behave exactly as today.
- Unreadable history (ambiguous log parents — cf. `test-navigation-refresh-modal.cjs`
  "gates unreadable history"): keep prompt disabled as today; history recall
  stays available because the MRU is independent of the target parse.
- Batch/count (`N<Alt+F>`, counted cancel, link sessions): one prompt, one
  preview, one MRU write; the preview's "each of the N tasks" copy already
  handles this.
- Long / multiline paste: single-line inputs already reject newlines; cap
  recall insertion at the same ~200-char limit and trim.
- Mission Control / Vim / IME: documented above; also ensure the chords are
  ignored with `event.repeat` for the Mac field (held key must not spin
  history) while matching the pickers' repeat behavior for lists.

## Verification sketch

Unit (existing harnesses, no new infra): MRU normalize/dedupe/cap vectors;
recall-order vectors (newest-first, filter narrowing, wrap, draft-restore);
exclusion vectors (blank / `🤷` / `🎲` / `::`-only / >200 chars never
persisted); mapping test that each of the 7 inputs reads the right MRU kind;
Mac view-model test that the reason field renders history rows from the
`bob` payload without writing. E2E: one Obsidian session test per prompt
(recall → preview → commit → re-recall on a second task) plus the pull-in
cancel field. Manual: VoiceOver pass on the new hint line, Mission Control
`Ctrl+N` enabled pass, IME pass.

## Verdict

Yes — build it. The pain is real, the prompts already share the interaction
shape that makes history cheap, and the vault already contains the seed data.
Build the 4-MRU version with scoped `Ctrl+N` / `Ctrl+P` (+ `Up`/`Down`
aliases), filter-as-you-type over the existing live preview, and `bob`-served
reads for both Obsidian and the Mac panel. Do not ship the brief verbatim
(3 histories, global chords): the rotten omission and the list-navigation
collision would each be a user-visible bug on day one.


