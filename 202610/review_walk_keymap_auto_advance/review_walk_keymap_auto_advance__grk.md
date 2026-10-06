# Auto-advance the `]s` walk after resolving keymaps

Researcher: `grk`. Independent report. Do not treat this as the swarm synthesis.

> **Research query:** Integrate more Obsidian keymaps with the GTD morning review that `]s` starts and continues. Ctrl+Enter already completes and advances inside the PRE group; generalize that "close then jump" behavior to any Ctrl+Enter that closes the current review item, and to other keymaps whose action implies the item has left the review stack (Ctrl+Shift+Enter, and Ctrl+Shift+P when the chosen Task Card option removes the item). Find other keymaps that should auto-jump. Critique the plan. Adjust requirements if justified. Recommend a solution.

## Bottom line

1. **Do it, as a shared "resolve then jump" helper on the existing walk landing, not as a pile of per-keymap jumps.** The idea is good. The morning already has three verbs: **stay** (Alt+F), **skip** (`]s`), **resolve-and-go** (Ctrl+Alt+F). Most other resolving keys already record a walk *anchor* so the next `]s` continues, then leave Bryan sitting on a dead row. That extra `]s` is the friction. Promoting it into the resolving gesture matches how Ctrl+Alt+F and PRE Ctrl+Enter already work.

2. **Do not make Ctrl+Enter complete every review tier.** **ADJ-1.** PRE/POST Ctrl+Enter is a *checklist closer*. On NEW / PROJECTS / PENDING / NEXT / RETURNED / REFERENCES / ROTTEN, Ctrl+Enter's native meaning is "toggle this task done." That is a drop, not a keep. The shipped PRE design (`plan:202610/ctrl_enter_checklist_walk.md` D3) stays on the last PRE row *because* one extra Ctrl+Enter must not close a real commitment. Keep that fence. Auto-jump after a *successful ordinary close of the exact landing* is optional and later; it is not the same feature as PRE walk-complete.

3. **Do not auto-jump on every Ctrl+Shift+Enter.** **ADJ-2.** That chord is a *link presence toggle*, not "do today." Linking an unlinked Ready/Blocked task stamps and promotes to Next — that resolves the row. Unlinking a task that is already on today never writes the checkbox and often leaves it due in NEXT. Jumping then would skip a row Bryan just pulled off today.

4. **Gate on the current walk landing (D2), and jump only when the write actually resolves that landing.** **ADJ-3.** "In the middle of a GTD morning review" is already a recorded object: `reviewLanding` from `landOnReviewQueueEntry`. Inventing a second session flag would desync from `]s`. Jumping from a random Ctrl+Shift+P in the afternoon is the failure mode D2 was written to prevent.

The adjustments are marked **ADJ-n**. The design is in [Recommended solution](#recommended-solution).

## Is this a good idea

### What is right

- **The walk already continues after a resolve; it just waits for another key.** `buildReviewAnchor` is documented to exist so that `]s` after an Alt+N release, Ctrl+Shift+Enter, or a roll continues from the successor instead of restarting at rank 1 (`bob-navigation-hotkeys` `src/470-keydown-and-freshness.js`). Ctrl+Alt+F is the one gesture that already calls `jumpToDueTask(1, { fromStamp: this.reviewAnchor })` after `finishFreshStamp`. Everything else does half the job. The user is asking to finish that job.
- **PRE Ctrl+Enter proved the pattern and the toast.** Nav 2.4.0 / cycler 1.25.0 / nav api v2 `claimReviewWalkCompletion` already: (1) cycler offers Ctrl+Enter to nav, (2) nav claims only the exact PRE/POST landing, (3) completes through Tasks so recurrence fires, (4) lands on the next live same-group row, (5) toasts `✓ Done · … · Ctrl+Enter → next PRE`. That is the UX to copy, not a new chord.
- **The ritual's own outcome table is an allowlist waiting to be wired.** `docs/freshness.md` §6: still right (Ctrl+Alt+F / Alt+F); less often (Ctrl+Shift+P `f`); not now (Ctrl+Shift+P `1`–`4`); do today (Ctrl+Shift+Enter / Alt+N commit); release (Alt+N); route (Ctrl+Shift+M); drop (Ctrl+Shift+P `x`); sequence (Ctrl+Shift+P `b`); wording wrong (edit, then Alt+F). Keep (Ctrl+Alt+F) already advances. Stay (Alt+F) must not. The rest are the gap.
- **Lane review is the highest-friction slice.** Default `next_interval` / `pending_interval` is 1 day, so PENDING and NEXT are daily. The landing notice already asks "Still next? Alt+F keep · Alt+N release · Ctrl+Shift+Enter today". Keep advances; release and today do not. That is the inconsistency Bryan is feeling.
- **Anki/GTD both treat "I decided" as "show me the next card."** Skip stays explicit (`]s`). Stay stays explicit (Alt+F). Resolve-and-go should be the default for every *write that answers the review question*.

### What is wrong or incomplete in the request as written

- **"Anytime Ctrl+Enter closes the current review item, jump" collides with D3.** The shipped rule is: Ctrl+Enter *never leaves PRE*. Last chore stays put with `PRE done` and `]s → NEW`. The reason is written in `plan:202610/ctrl_enter_checklist_walk.md` D3: the next tier is keep / release / today, not complete; a habitual extra press would close a real task. Generalizing "close then jump" across the PRE → NEW boundary reopens that bug. Tests in `scripts/test-navigation-checklist-ctrl-enter.cjs` (`Ctrl+Enter stays in PRE while Ctrl+Alt+F still crosses into NEW`) lock it.
- **Ctrl+Enter on a NEW/ROTTEN landing already "closes" via the cycler, without claiming.** `claimReviewWalkCompletion` returns `null` for non-checklist tiers (`claim declines … not checklist tier` / `ROTTEN tier`). The cycler then runs `toggleActiveCheckboxOpenDoneAndPropagate`, which refuses `[?]` and does not fire the PRE recurrence path. Treating that as a review outcome would make "drop by completing" an unadvertised default on every commitment row. That is a different product decision from PRE walk-complete.
- **Ctrl+Enter on the Task Card already means "apply the recommended roll."** `resolveTaskCardKey` maps Ctrl+Enter / Cmd+Enter to `apply-recommendation` (`src/310-task-card-previews.js`; `docs/projects.md`). Editor Ctrl+Enter and card Ctrl+Enter are different surfaces. After a successful recommended roll the card closes; *that* is the moment to jump, because a future `scheduled` plus a stamp removes the row. Do not also try to complete the task.
- **Ctrl+Shift+Enter is a toggle, and unlink is not a review resolution.** `block-id-prompt` `src/120-plugin-pomodoro-links.js`: unlinked → link to today's Pomodoro, Ready/Blocked become Next, stamp if the line was rewritten; already linked → unlink, never write the checkbox, In Progress first asks for a Work Log. Sticky-lanes policy (`decisions:task-lanes-are-sticky`) forbids unlink from lowering the lane. A NEXT-tier task that is already linked will *leave today* and often *stay due*. Auto-jump on that press is wrong.
- **"Task Card option that removes the item from the stack" is the right test, and it is not a key, it is an outcome.** Schedule-to-today, Depends-on that does not block, Review-every that does not stamp, Esc, Backspace, preview refresh (`Ctrl+R`), and a disabled row must not jump. Cancel, a future schedule, a priority roll, a refresh-interval write (which stamps), a successful lane toggle, and Drop on the decay card must.
- **"Next/first review item" must not mean `endpoint: "first"`.** `[S` / `jumpToDueTask(1, { endpoint: "first" })` ignores the anchor and restarts the queue. The user wants the *successor* of the resolved row, wrapping only when the remaining queue wraps, which is already `jumpToDueTask(1, { fromStamp: reviewAnchor })`.

### Would I take a different approach

I would still keep `]s` as the only walk chord and add auto-advance as a *post-commit* of resolving writers. I would not:

- add `]d` / a second "decide and go" keymap (the keys already exist; they just forget to jump);
- watch `vault.modify` and jump whenever the landing key disappears (Tasks cache lag, recurrence inserts, and unrelated edits would false-fire; the stamp path already teaches that the jump must use the *pre-write* queue plus handled keys);
- make Ctrl+Enter the universal review closer on every tier (D3 exists specifically to stop that);
- introduce a "review session" boolean, a time window, or a `gtd_daily.md` file check. The landing is the session;
- auto-jump after Alt+F (stay is the whole point of that chord);
- auto-jump after Reword on the decay card (focus stays for editing; `maybeAdvanceFreshnessDecayWalk` already skips `reword`);
- auto-jump after a cancelled Work Log / lane-release / Unlink prompt (Escape must leave the row due, as Ctrl+Alt+F already does).

The one alternative worth taking seriously: **outcome-only observer inside nav** ("after any nav write, if the landing key is gone from a live re-read, jump"). Reject as the *only* mechanism, because Ctrl+Shift+Enter lives in block-id-prompt, Ctrl+Enter close lives in the cycler, and the Tasks cache is stale by design (`finishFreshStamp` comment: the jump reads the queue fresh but continues from the handled successor). Use live re-read as a *guard* on ambiguous Task Card commits, not as the dispatcher.

## Requirement adjustments

**ADJ-1. Keep PRE/POST Ctrl+Enter as a same-group closer. Do not cross PRE → NEW.** Last PRE row stays, with the existing `]s → {LABEL}` toast. Ctrl+Alt+F remains the key that crosses. If Bryan later wants Ctrl+Enter to behave like Ctrl+Alt+F on PRE, that is the one-branch change D3 already named — do not sneak it in under "generalize close then jump."

**ADJ-2. Ctrl+Shift+Enter auto-jumps only on a successful *link* (do today) of a walk landing, never on unlink, never on Depends-On refusal, never on a selected Task Link deletion.** Link path: stamp + Next is a resolve. Unlink path: the row usually remains due. Task-Link-on-a-bullet deletion is not a review close of the landing.

**ADJ-3. Auto-advance is gated on today's walk landing, plus the write's targets including that landing (or a counted batch that includes it).** Cheap checks first, same order as D2: landing exists, `day` is today, active file matches, and either the cursor line still is the landing text *or* the writer just rewrote that line. A `j`/`k` move off the row, an edit, or a new local day returns every keymap to its non-review meaning.

**ADJ-4. Classify each gesture as stay / skip / resolve-and-go / outcome-based. Do not jump from "the keymap was pressed."** See [Gesture table](#gesture-table). Resolve-and-go jumps even if a lagging queue still lists the row (handled keys already cover that). Outcome-based re-reads live lines (the PRE Ctrl+Enter `filterLiveReviewEntries` trick) and jumps only if the landing is no longer a live queue entry.

**ADJ-5. One helper, one toast family, one api bump — not a new keymap.** Nav owns the jump. Cycler and block-id-prompt *notify* after their own successful writes. Do not import `main.js` across plugins. Nav api becomes v3 with `notifyReviewWalkResolved`.

**ADJ-6. Counted sessions advance once, past every handled key, the way `N` Ctrl+Alt+F already does.** `N` Alt+N, `N` Ctrl+Shift+P, and Task Link batches that include the landing add every written key to the anchor, then one `jumpToDueTask`. They do not jump N times.

**ADJ-7. Do not auto-complete `[?]` commitments.** D5 (claimed Ctrl+Enter completes `[?]` PRE chores because hooks leave them blocked overnight) stays PRE/POST-only. Ordinary Ctrl+Enter on a `[?]` NEW/ROTTEN row still no-ops.

**ADJ-8. Footer and §6 copy should tell the truth after this ships, but ledger-tools is a second patch.** Today's PRE hint is `Ctrl+Alt+F done → next · ]s skip`, which under-sells Ctrl+Enter on a landing. PENDING/NEXT hints name keep / release / today and do not say which of those already advance. Update `docs/freshness.md` §6 in the same change as nav; leave the footer for a follow-up so this does not grow a ledger namespace bump unless the hint strings are considered part of `reviewEntryView`.

**ADJ-9. No new decision record.** This is keymap behavior inside `decisions:review-walk-is-tiered`. It adds no tier, no queue, no stamp rule. Same call as `plan:202610/ctrl_enter_checklist_walk.md` D8.

**ADJ-10. Optional later: ordinary Ctrl+Enter close of a non-checklist landing also jumps.** Only after ADJ-1 is locked in tests. Only if the cycler actually closed (not reopened) the exact landing. Never through `completeTaskAtCursor`, never on Pomodoro completion, never on a Task Link that is not the landing. Default recommendation: **defer this**. Completing a commitment is a drop; drop already has Ctrl+Shift+P `x`. If Bryan wants "done in two minutes, next card," take this as a fast follow, not the first slice.

## What exists today

Verified 2026-10-06 against this workspace (`bob-cli_12`), opened `bob-plugins` (`sase repo open bob-plugins`), `docs/freshness.md` §6, `plan:202610/ctrl_enter_checklist_walk.md`, and `research:202610/gtd_pre_post_checklist_tiers/gtd_pre_post_checklist_tiers.md`.

| # | Fact | Evidence |
| --- | --- | --- |
| E1 | Walk order is PRE → NEW → PROJECTS → PENDING → NEXT → RETURNED → REFERENCES → ROTTEN → POST. `]s` / `[s` / `[S` / `]S` call `jumpToDueTask`. | `decisions:review-walk-is-tiered`; nav `src/490-plugin-lifecycle.js` commands; `docs/freshness.md` §6 |
| E2 | A successful landing records `reviewLanding` `{path, text, key, tier, day}` and `reviewAnchor`. | nav `src/520-plugin-lane-links-and-review.js` `landOnReviewQueueEntry` |
| E3 | Ctrl+Alt+F stamps (or completes a checklist row) then `jumpToDueTask(1, { fromStamp })`. Alt+F does the same write without the jump. Escape on the Pending Work Log prompt writes nothing and does not advance. | `refreshTaskFreshness`; `finishFreshStamp`; `src/530-plugin-freshness-refresh-and-decay.js` |
| E4 | PRE/POST Ctrl+Enter is a *claim*, not a default. Cycler `handleVimTaskToggleOpenDone` asks nav api v2 `claimReviewWalkCompletion` first. Nav claims only today's exact PRE/POST landing, completes via cycler `completeTaskAtCursor` (accepts ` `, `*`, `/`, `?`, never stamps), and with `withinGroup: true` stays inside the group. | cycler `src/140-plugin-vim.js`, `src/160-plugin-completion.js`; nav `src/535-plugin-review-checklist-walk.js`; `docs/task-dependencies.md` §9 |
| E5 | Last PRE Ctrl+Enter stays; Ctrl+Alt+F on that row still crosses into NEW. Last POST Ctrl+Enter / Ctrl+Alt+F closes the review; Alt+F stays and counts remaining POST rows. | `test-navigation-checklist-ctrl-enter.cjs`; `docs/freshness.md` §6 steps 2 and 5 |
| E6 | Alt+N commit/release *stamps* through `planTaskLaneBatch` (`stampLine` last). Release unlinks from today. It does **not** call `jumpToDueTask`. The next `]s` uses the landing's anchor. | nav `src/230-schedule-review.js`; `src/510-plugin-link-commit-and-lane.js`; comment on `buildReviewAnchor` |
| E7 | Ctrl+Shift+Enter lives in block-id-prompt, which never talks to nav. Link rewrites stamp; unlink does not write the checkbox. | `plugins/block-id-prompt/src/120-plugin-pomodoro-links.js`; README Block ID Prompt row |
| E8 | Task Card (`Ctrl+Shift+P`) rows: Schedule, Depends on (`b`), Review every (`f`), lane (`Alt+N`), Cancel (`x`), plus `1`–`4` / `0` priority, Ctrl+Enter recommendation, Ctrl+D delete property. Successful commits close the card. None of them call `jumpToDueTask`. Review every and lane/priority/schedule/move stamp rewritten open tasks. Cancel does not stamp (closed lines refuse the stamper). | `src/310-task-card-previews.js`; `src/350-picker-task-card.js`; `docs/freshness.md` §6 writers table |
| E9 | Decay card on a single exact at-limit Ready row: Keep / Not now / Less often / Drop / Reword. Ctrl+Alt+F-opened cards advance on every choice except Reword; Alt+F-opened cards do not. Esc dismisses with no write and no advance. | `maybeAdvanceFreshnessDecayWalk`; `openFreshnessDecayCard` |
| E10 | Ctrl+Shift+M move stamps rewritten open tasks and focuses the destination. No review jump. | README nav row; `src/650-plugin-move-commit.js` |
| E11 | Queue membership is read-time. Stamped today drops out. Closed / cancelled / Blocked (`lane === null` except checklist) drop out. Recurring non-checklist never enters. PRE/POST resolve only by completion. | ledger `src/100-freshness-evaluate.js`; glossary `task-freshness` |
| E12 | Nav api is frozen v2: `openDependencyStage`, `removeDependency`, `claimReviewWalkCompletion`, plus `freshnessDecayCard` capability. Plugins never import each other's `main.js`. | `createDependencyNavApi`; `docs/task-dependencies.md` §9 |

## Gesture table

"Landing" means ADJ-3. "Leaves stack" means the row is no longer due after a correct live evaluation (closed, cancelled, stamped today, future-scheduled, or Blocked).

| Gesture | Surface | Resolves the review question? | Leaves stack? | Auto-jump? | Notes |
| --- | --- | --- | --- | --- | --- |
| `]s` / `[s` / `[S` / `]S` / Ctrl+Alt+J/K | nav walk | skip / move | no | already *is* the jump | Do not double-jump |
| Alt+F | nav stamp / PRE complete | yes (keep / complete) | usually yes | **no** | Stay is the chord |
| Ctrl+Alt+F | nav stamp / PRE complete | yes | yes | **already yes** | Template |
| Ctrl+Enter on PRE/POST landing | cycler → nav claim | yes (complete) | yes | **already yes, same group only** | Keep D3; ADJ-1 |
| Ctrl+Enter off landing | cycler | not a review act | maybe | **no** | D2 |
| Ctrl+Enter on NEW/ROTTEN landing | cycler toggle done | drop, unadvertised | if it actually closed | **defer** (ADJ-10) | Do not claim `[?]` |
| Ctrl+Enter on Task Card | recommendation roll | yes (not now) | usually yes (future date + stamp) | **yes**, after successful apply | Different meaning from editor Ctrl+Enter |
| Ctrl+Shift+Enter **link** of landing | block-id-prompt | yes (do today) | yes if stamp/promote | **yes** (ADJ-2) | Notify nav |
| Ctrl+Shift+Enter **unlink** | block-id-prompt | no | often no | **no** | |
| Ctrl+Shift+Enter on Depends-On | block-id-prompt | n/a | no | **no** | Already refused |
| Alt+N commit/release of landing | nav | yes (today / not this lane) | yes (stamps) | **yes** | Highest-value gap |
| Task Card lane row | same writer as Alt+N | yes | yes | **yes** | |
| Task Card `x` cancel | nav cancel | yes (drop) | yes | **yes** | After reason stage commits |
| Task Card `1`–`4` / `0` | priority writer | yes if date moves | if scheduled becomes future | **outcome-based** | `0` keeps scheduled |
| Task Card Schedule commit | schedule writer | yes if deferred | if date is strictly future | **outcome-based** | Esc on the stage: no |
| Task Card `f` Review every | `setRefreshLine` (stamps) | yes (less often) | yes on successful write | **yes** | |
| Task Card `b` Depends on | dependency writer | maybe | if the row becomes Blocked | **outcome-based** | Sequence is often "stay and edit" |
| Decay Keep / Not now / Less often / Drop | decay card | yes | yes | **yes if the opening press was Ctrl+Alt+F; also yes from a landing even on Alt+F** | **ADJ-11** below |
| Decay Reword | decay card | partial (stamps, then edit) | yes | **no** | Keep current exception |
| Decay Esc | decay card | no | no | **no** | |
| Ctrl+Shift+M move of landing | nav move | yes (route) | yes if stamp | **yes** | Jump from the destination to the next due row |
| Ctrl+Shift+J/K Ready/Next nav | nav | no | no | **no** | Different queue |
| Alt+] / Alt+[ cycle | cycler | no (status only) | only if it leaves an open lane | **no** | Not a review decision |
| `!` transclusion toggle | nav | no | no | **no** | Never rewrites a task line (`docs/freshness.md` §6) |
| Ctrl+D on Depends on | nav | maybe | if last open prereq is removed, recovery may *return* the row | **no** | Restores work; stay |
| Pomodoro Ctrl+Enter | cycler | no | n/a | **no** | |

**ADJ-11. Decay card opened with Alt+F from a walk landing should also auto-advance after Keep / Not now / Less often / Drop.** Today advance follows the *opening* chord (`cardCtx.advance`), so an Alt+F at-limit press stays after Keep. During a `]s` walk that is the same extra `]s` the user is trying to remove. Reword still stays. Esc still stays. Counted sessions still skip the card.

## Critique of the plan in general

The plan as stated is **directionally right and underspecified in the two places that will hurt**.

**Right:** stop requiring `]s` after a decision. Use the landing as the review-context gate. Treat Task Card as a menu of outcomes, not as a single keymap. Look for other resolving keys (Alt+N, decay, move, Review every).

**Underspecified:** "this keymap" (Ctrl+Enter) has four meanings already (PRE claim, ordinary toggle, Task Card recommendation, Pomodoro/Task-Link close). "Ctrl+Shift+Enter" has two directions. "Removes the review item from the stack" is an *evaluator* question, and the Tasks cache will lie for a beat — which is why Ctrl+Alt+F does not re-query membership; it marks handled keys on the pre-write queue.

**Risk of doing it as a keymap allowlist without a helper:** every new writer (the next decay action, the next card row) forgets to jump, and we are here again. The helper is the feature; the table above is its first caller list.

**Risk of doing it too broadly:** afternoon property edits start teleporting Bryan through the remaining rotten pile. D2 exists because PRE chores stay due all day. The same is true of a NEXT task Bryan opens at 16:00 to tweak a schedule.

**Risk of changing D3 in the same patch:** one extra Ctrl+Enter after stretches completes a NEW capture. That is worse than an extra `]s`.

## Implementation sketch

### Helper (nav)

Add `advanceReviewWalkAfterResolve(options)` next to `completeReviewChecklistRow` / `finishFreshStamp` (likely `src/535-plugin-review-checklist-walk.js` or a new mixin under 1000 lines):

1. Refuse unless `reviewLanding` is today's (`laneReleaseDateText`).
2. Build handled keys from `options.keys` (required), which must include the landing key or a counted superset that includes it.
3. `this.reviewAnchor = buildReviewAnchor(queueBefore, keys, rank, today)`.
4. If `options.mode === "force"` (resolve-and-go): `return this.jumpToDueTask(1, { fromStamp: this.reviewAnchor })`.
5. If `options.mode === "if-gone"` (outcome-based): `filterLiveReviewEntries` on the landing; jump only when it is not live.
6. Compose the toast as `[doneLine, optional boundary, landing notice]` the way Ctrl+Alt+F already does. Reuse `buildReviewJumpNotice` with `omitActionHint` when the first line already named the key.
7. Never use `endpoint: "first"`. Empty remaining queue → existing empty/closed notices, no wrap into a completed POST.

Call it from, in the first slice:

- `toggleTaskLaneOnTasks` / `toggleTaskLaneOnLinks` / `applyLaneToggleFromPicker` after a successful plan (force).
- Task Card: cancel commit, refresh-interval commit, recommendation apply, priority commit that wrote a future date (force if the writer stamped; if-gone otherwise).
- `maybeAdvanceFreshnessDecayWalk`: treat a current landing as `advance: true` except Reword (ADJ-11).
- Ctrl+Shift+M after a successful move of a landing key (force).

PRE/POST Ctrl+Enter stays on `completeReviewChecklistRow({ withinGroup: true })`. Do not route it through the new helper's cross-tier jump.

### Nav api v3

```js
{
  version: 3,
  freshnessDecayCard,
  openDependencyStage(ref),
  removeDependency(parentRef, target),
  claimReviewWalkCompletion(editor),          // unchanged: PRE/POST only
  notifyReviewWalkResolved({ keys, mode }),   // thenable { ok, reason? } | null if no landing
}
```

- Cycler: after a **deferred** ADJ-10 close, or not at all in slice 1.
- block-id-prompt: after a successful **link** (`planTargetTaskUpdate` with `hasChanges` or a successful insert) whose source line matches the landing. Feature-detect `api?.version >= 3` and `typeof notifyReviewWalkResolved === "function"`. Unlink never notifies.
- Unload api (`createDependencyNavApi(null)`) declines both claim and notify.

Keep `claimReviewWalkCompletion` PRE/POST-only. Folding all Ctrl+Enter into that claim would run `completeTaskAtCursor` on commitments, including `[?]`, which ADJ-7 forbids.

### What not to hook

Vim counts on walk keys, insert-mode Ctrl+Enter, the unbound `toggle-task-open-done` command (same out-of-scope as the checklist plan), `!`, Ctrl+Shift+J/K (Ready/Next file nav and Pomodoro reorder), section jumps, tab close.

### Tests (bob-plugins)

New `scripts/test-navigation-review-advance.cjs` on the `npm test` list. Land through real `jumpToDueTask`, like the checklist suite.

1. **Landing gate.** Alt+N on a NEXT landing jumps to the successor and toasts. `j` to another NEXT row, then Alt+N: lane changes, no jump, landing uncleared or cleared without a walk step.
2. **D3 regression.** Last PRE Ctrl+Enter still stays with `]s → NEW`. Ctrl+Alt+F still crosses.
3. **Claim still declines NEW/ROTTEN.** Ordinary Ctrl+Enter is not claimed.
4. **Task Card cancel** of a landing closes the card and jumps; Esc does not.
5. **Task Card recommendation** (Ctrl+Enter) of a landing jumps; Ctrl+Enter with no recommendation notices and stays.
6. **Decay Reword** stays; Decay Keep from a landing jumps even if opened with Alt+F.
7. **Counted Alt+N** handles both keys and jumps once to the first not-handled successor.
8. **Yesterday's landing** does not claim or notify.
9. **block-id-prompt notify mock:** link + v3 api jumps; unlink does not call it; api v2 is a no-op.
10. Existing `test-navigation-checklist-ctrl-enter.cjs`, `test-navigation-freshness.cjs`, `test-navigation-task-card-*.cjs`, `test-navigation-hotkeys-lane-toggle.cjs` stay green.

### Docs

- `docs/freshness.md` §6: add one sentence under the outcome table: resolving gestures that write (keep-and-advance, release, do-today *link*, drop, less-often, not-now, route) jump to the next due row when they fire on the walk landing; Alt+F stays; `]s` skips; Ctrl+Enter still does not leave PRE.
- `docs/task-dependencies.md` §9: api v3 + `notifyReviewWalkResolved`.
- `docs/getting-started.md`: one clause that release / today / drop continue the walk.
- README nav / cycler / block-id-prompt rows and manifest bumps (nav 2.5.0, block-id-prompt if it notifies, cycler only if ADJ-10 ships).
- §13 rollout log dated on deploy.

### Ship order

1. Nav helper + Alt+N + Task Card resolving commits + decay ADJ-11. Biggest morning win, one plugin.
2. Docs.
3. block-id-prompt notify on link.
4. Optional ADJ-10 cycler close-of-landing.
5. Optional footer hint strings (ledger).

Do not parallelize 1 with a D3 change.

## Recommended solution

**Build a single `advanceReviewWalkAfterResolve` helper in bob-navigation-hotkeys, gated on today's `reviewLanding`, and call it from every writer that already answers the review question.** Keep PRE/POST Ctrl+Enter as the same-group closer it is today. Teach Ctrl+Shift+Enter to notify nav only when it *links* a landing. Teach the Task Card to notify only after a commit whose outcome removes or stamps the landing. Leave Alt+F, Reword, Esc, unlink, and off-landing keypresses alone.

That is the smallest change that matches the walk's existing architecture (landing + anchor + `fromStamp` jump), preserves the PRE safety fence that was the whole point of last week's Ctrl+Enter work, and removes the extra `]s` after keep / release / today / drop / defer — the keys Bryan actually uses in PENDING and NEXT.

Slice 1 is nav-only and is enough to feel the ritual change tomorrow morning. Slice 3 (block-id-prompt) is required before "Ctrl+Shift+Enter today" on the landing notice becomes true. Slice 4 (Ctrl+Enter drop-and-go on commitments) should wait until Bryan has used slice 1 and still wants it.

## Sources and limits

- **bob-plugins** (opened path `sase/repos/linked/bob-plugins`): nav `src/310-task-card-previews.js`, `350-picker-task-card.js`, `470-keydown-and-freshness.js`, `480-review-jump-and-nav-api.js`, `490-plugin-lifecycle.js`, `510-plugin-link-commit-and-lane.js`, `520-plugin-lane-links-and-review.js`, `530-plugin-freshness-refresh-and-decay.js`, `535-plugin-review-checklist-walk.js`, `540-plugin-decay-picker-and-cancel.js`, `230-schedule-review.js`; cycler `src/140-plugin-vim.js`, `160-plugin-completion.js`; block-id-prompt `src/120-plugin-pomodoro-links.js`, `070-daily-and-activation-plans.js`; ledger `src/100-freshness-evaluate.js`, `110-freshness-queue.js`, `120-freshness-footer.js`; `scripts/test-navigation-checklist-ctrl-enter.cjs`; README.
- **bob-cli:** `docs/freshness.md` §§2, 6, 13; `docs/getting-started.md`; `docs/task-dependencies.md` §9; `docs/projects.md` Task Card / Ctrl+Enter recommendation.
- **Plans and prior research (audited):** `plan:202610/ctrl_enter_checklist_walk.md`; `research:202610/gtd_pre_post_checklist_tiers/gtd_pre_post_checklist_tiers.md`.
- **Memory:** `decisions:review-walk-is-tiered`, `task-lanes-are-sticky`, `ready-is-freshness-gated`, `decay-decisions-are-available-immediately`, `rotten-keeps-use-priority-decay`; glossary `task-freshness`.
- **Not verified in a live Obsidian session:** cursor placement after a Task Card close, after a cross-note Ctrl+Shift+M, and after block-id-prompt link of a landing in another file. The helper should land through the existing `landOnReviewQueueEntry` path, which already opens the successor note.
- Nothing in the vault, bob-cli, or bob-plugins was modified by this research.
