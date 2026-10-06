---
audio:
  edition: brief
  duration_s: 269.82
  chapter_count: 3
  episode_id: auto-advancing-the-morning-review-41b6ed
---

# Auto-advancing the `]s` morning review after an answering gesture

> **Research query:** What is the best way to make more keymaps in the `]s` GTD morning review
> in Obsidian jump automatically to the next (or first) review item? Specifically: closing an
> item with `<ctrl+enter>` in any review group, not only PRE; `<ctrl+shift+enter>`; and
> `<ctrl+shift+p>` when the chosen Task Card option removes the item from the review stack.
> Which other keymaps or actions should also advance, is the plan a good idea, would a
> different approach be better, and what requirement adjustments and recommended solution are
> justified?

<div class="listen">

♫ **Brief audio edition** · 4 min · 3 chapters · [Narration
script](review_walk_answer_auto_advance_narration.md)

</div>

![Infographic titled "Answer once. Advance once.": when ]s lands on a row and your action resolves it, the walk moves to the next remaining item, but only for a gesture begun on the current review landing after a successful write, and ]s remains the skip key. On the NEW through ROTTEN tiers, Ctrl+Enter complete, Alt+N commit or release, Ctrl+Shift+Enter link to Today, a final resolving Ctrl+Shift+P Task Card commit, and the existing Ctrl+Alt+F keep advance. Alt+F keep, Esc or a cancelled dialog, refused or no-op writes, unlink or reopen, and Reword or status cycling stay. Ctrl+Enter stops at the PRE and POST checklist boundary while Ctrl+Alt+F can still cross. One shared navigation helper captures the landing, lets the existing writer commit, evaluates the outcome, and advances once. v1 requires blocking double presses, rejecting stale callbacks, and a Ctrl+O return. Ctrl+Shift+M move comes later.](review_walk_answer_auto_advance_infographic.png)

## Bottom line

1. **Do it.** [The idea is sound](#critique-of-the-plan), and most of the machinery already
   exists.
   - The walk already records a landing (`reviewLanding`) and an anchor (`reviewAnchor`). The
     anchor was built so that "a later release, roll, or stamp continues from here"
     ([nav](#abbreviations) `520:459`).
   - Today [only three answers move on](#which-answers-move-on-today): Ctrl+Alt+F, the decay
     card it opens, and checklist Ctrl+Enter.
   - Every other answer leaves you parked on a row you have already answered, and costs an extra
     `]s`.
2. **Base the rule on outcomes, not keys.**
   - The rule: *a gesture that started on the row `]s` just landed on, and that committed a write
     taking that row out of today's walk, advances the walk exactly once.*
   - Keymaps are only call sites. The rule is also the exact form of your "Task Card option that
     removes the item" [qualifier](#a6-details).
3. **[Widen the scope](#requirement-adjustments) to answers you didn't name:**
   - Alt+N commit/release, the highest-volume answer right now (NEXT holds 34 tasks against a
     cap of 15);
   - every [committing Task Card stage](#task-card-commits);
   - Ctrl+Shift+M move (phase 2, [your call](#open-questions-for-bryan)).
4. **Narrow the scope in five places:**
   - It applies only on the [current walk landing](#a2-conditions), never in ordinary daytime
     use.
   - Ctrl+Shift+Enter [advances on *link* only](#a5-exclusions).
   - On PRE/POST rows, [only completion or a real deferral, cancellation, or
     block](#a6-details) advances.
   - Alt+F stays the explicit "stay" answer.
   - Escape, refused or no-op writes, Reword, reopen, unlink, and status cycling all stay put.
5. **One deliberate deviation from your literal ask ([A4](#a4-details)).**
   - Ctrl+Enter should advance on every tier, but it should **not carry you across the
     checklist ↔ non-checklist boundary**.
   - The shipped D3 rule exists because one habitual extra Ctrl+Enter would close a real task.
     Once Ctrl+Enter also advances on non-checklist rows, that accident would also move you away
     from the row it closed.
   - Keeping the stop costs at most one `]s` per morning, and Ctrl+Alt+F still crosses.
   - If you disagree after trying it, it is a one-branch change.
6. **Architecture:**
   - Nav owns [one helper](#the-nav-helper): *capture before the write, continue after the
     final commit* (nav api v3 `reviewWalk`).
   - The writers keep writing: the cycler, block-id-prompt, Alt+N, and the Task Card.
   - Nav reuses `jumpToDueTask(1, { fromStamp })`.
   - Resolution is decided from the outcome the writer reports, plus the line after the write. It
     is **not** decided from a fresh queue read (the Tasks cache lags), and **not** from a
     passive file watcher.
7. **The real hazard is toggles, not navigation.**
   - Ctrl+Enter, Alt+N, and Ctrl+Shift+Enter are all toggles.
   - With auto-advance, a fast double press either **reverts the answer** (the second press hits
     the old row before the landing finishes) or **answers the next row unseen**.
   - [A busy/settle guard ships in v1](#risks-and-mitigations), or the feature doesn't ship.

## Critique of the plan

Is this a good idea? **Yes.** These reasons come from all five reports, plus one new point.

- **It finishes a half-built pattern.** The anchor exists precisely so that release, today, and
  roll continue from the successor. Only the final `]s` is missing.
- **It removes the "parked" state.**
  - Sitting on an answered row is where side quests start.
  - It is also where you have to wonder whether the next `]s` continues or restarts.
- **It removes a structural bias toward rubber-stamping (new point).**
  - Today the *only* one-key answer that advances is keep (Ctrl+Alt+F). Release, today, defer,
    and drop each cost a second key.
  - `review-walk-is-tiered` names "the rubber-stamp risk of a daily lane queue" as a cost. It
    reopens if "the lane keep rate stays above 90%".
  - Making every answer equally cheap removes a nudge toward keep, which keeps the record's own
    reopen metric honest.
- **There is precedent** (cited by `__cld` and `__cdx`; I did not re-verify these):
  - mutt `$resolve` advances after any command that modifies the current message.
  - Gmail auto-advance moves on after archive, delete, or mute, which are the actions that
    remove the item from the list.
  - OmniFocus "Mark Reviewed" presents the next project.
  - The W3C modal-dialog pattern lets focus move to the next logical step once a dialog has
    completed its task.

  Your qualifier is the Gmail rule, and that is the right rule.

### Where the request is over- or under-specified

1. **"This keymap" is overloaded.**
   - Ctrl+Enter already has four meanings: the PRE/POST claim, the ordinary close/reopen
     toggle, the Task Card's "apply recommendation", and the Task Link/Pomodoro close.
   - Ctrl+Shift+Enter means link *or* unlink.
   - Ctrl+Shift+P is a menu of a dozen outcomes.
   - A keymap allowlist will fire when it shouldn't and miss cases where it should. An outcome
     rule won't.
2. **"Anytime" must mean "on the current walk landing".** These keys are used all day. A
   "review mode" flag or a remembered anchor alone is not enough.
3. **"Removes the item from the stack" is an evaluator question, and the cache answers it late.**
   Ctrl+Alt+F already handles this by marking handled keys on the pre-write queue instead of
   re-querying membership. Reuse that.
4. **"Next/first" means the next remaining entry in walk order.**
   - At the end of the queue it wraps to the first skipped entry, with the existing wrap notice.
   - In code that is `jumpToDueTask(1, { fromStamp })`, never `endpoint: "first"`, which
     restarts the queue.
5. **Crossing the end of PRE with Ctrl+Enter reverses a documented decision.**
   - The decision is recorded in three places: plan D3, docs §6 step 2, and the test
     `Ctrl+Enter stays in PRE while Ctrl+Alt+F still crosses into NEW`.
   - Reversing it must be an explicit choice, not a side effect ([A4](#a4-details)).
6. **Auto-advance won't "review all items from all groups" by itself.**
   - ROTTEN stays optional upkeep, and skipped rows remain.
   - POST closeout stays deliberate and never wraps.

### Risks and mitigations

| Risk | Mitigation |
| --- | --- |
| **Toggle double press** (Ctrl+Enter open↔done, Alt+N Ready↔Next, Ctrl+Shift+Enter link↔unlink). Before the landing finishes, the second press hits the old row; its text has changed, so the guard misses, and the ordinary toggle **reverts the answer**. After the landing, the second press answers the next row unseen. | An in-flight flag, plus a short settle window after each auto-landing (start at about 300 ms and tune it live). During either, `capture()` returns `busy`, and the caller swallows the key with no write. Also ignore `event.repeat` wherever a DOM event exists. |
| **A stale landing fires hours later.** | The landing stays valid only while it is unconsumed, from today, and you haven't left its note. Clear it on any `file-open` that the walk or the gesture didn't cause (nav already listens at `490:298`), and when the walk is empty or closed. |
| **An async callback steals focus** (the action finishes after you navigated, or after a newer `]s`). | Each capture carries a landing epoch. `continue()` refuses when the epoch is stale or the plugin has unloaded. One action produces at most one jump. |
| **Lost context** (you wanted a follow-up on the answered row). | Push the answered row onto nav's Vim jump history before every auto-advance, so `<C-o>` returns to it. Alt+F remains the stay answer. |
| **Cross-note undo** (`u` is buffer-local). | `<C-o>` then `u` for edits in the same buffer. Cross-file writes were never in the editor undo stack anyway. Accept the rest. |
| **Cache lag, and recurrence inserting a row above the completed one.** | Use handled keys plus the pre-write `afterKeys`, and filter to live lines (`filterLiveReviewEntries`). Never plan from the cursor after the write. |
| **Two toasts stack** (the gesture's own toast and the landing toast). | Compose one toast instead: `✓ <outcome> · <task>`, then the boundary, then the landing. `completeReviewChecklistRow` already builds this composition. |
| **Plugin version skew.** | Feature-detect nav `api.version >= 3 && api.reviewWalk`; an older nav keeps today's behavior. Keep `claimReviewWalkCompletion` for older cyclers. |

## Requirement adjustments

Explicitly called out:

| # | You asked | I recommend | Why | Kind |
| --- | --- | --- | --- | --- |
| **A1** | A list of keymaps that imply iteration | One outcome rule behind one nav helper. The [gesture policy table](#gesture-policy) is its first list of callers. | Future gestures opt in with one call, and it matches the docs §6 outcome list. | reframe |
| **A2** | Advance "anytime" these keys close an item | Only when the gesture **started** on today's walk landing ([A2 conditions](#a2-conditions) below the table). | These keys are used all day. | narrow |
| **A3** | Ctrl+Enter advances on any review item | Yes, on every tier. Non-checklist rows go through the cycler's ordinary close (transclusion propagation, finalize, `[?]` refusal). Reopen never advances. | "Already done" is a real outcome, and it is missing from the docs §6 list. | as asked |
| **A4** | Ctrl+Enter jumps to the next or first item | Keep D3, generalized ([A4 details](#a4-details) below the table). | The boundary is where Ctrl+Enter changes meaning, from "tick the chore" to "close a real commitment". With auto-advance, an accidental close would also move you off the row it closed. The stop costs at most one `]s` a morning. | **deviation** (one branch to reverse) |
| **A5** | Ctrl+Shift+Enter advances | Only after a successful **link** ([A5 exclusions](#a5-exclusions) below the table). | Unlink isn't an answer, and with sticky lanes it leaves the task due. | narrow |
| **A6** | Ctrl+Shift+P advances if the option removes the item | Advance after the card's **final** commit when the landed row is resolved ([A6 details](#a6-details) below the table). | Your qualifier, made exact. | sharpen |
| **A7** | (not asked) | Alt+N commit/release advances, including counted `N<Alt+N>`, which jumps once past every handled key. A Pending release advances only after its Work Log prompt is confirmed. | It is the documented release / do-today answer, and the highest volume right now. | widen |
| **A8** | (not asked) | Ctrl+Shift+M started on a landing advances instead of focusing the destination; the toast names the destination. Phase 2. | "Route to a project" is a docs §6 outcome. Triage first, organize later. | widen (your call) |
| **A9** | (not asked) | Alt+F stays the one "stay" answer, including the decay card it opens. Ctrl+Alt+F and Reword are unchanged. | An escape hatch without a new modifier. | preserve |
| **A10** | (not asked) | The busy/settle guard and `<C-o>` back to the answered row ship in v1. | See the [risks](#risks-and-mitigations). | safety |
| **A11** | (not asked) | Fix the hints and the outcome list ([A11 details](#a11-details) below the table). | The lane hints advertise Alt+F, which doesn't advance. | fix |

### A2 conditions

All of these must hold when the gesture starts:

- the same note as the landing;
- the cursor is on the landed row, with its text unchanged;
- the landing is unconsumed;
- you haven't left the note since landing.

### A4 details

- Ctrl+Enter never auto-advances across the checklist ↔ non-checklist boundary:
  - from the end of PRE into NEW;
  - from the last non-checklist row into POST;
  - when a wrap would land back on a skipped PRE row.
- Instead it stays, and the toast names the next step (`]s → NEW`).
- Ctrl+Alt+F still crosses.

### A5 exclusions

Never advance after:

- unlink, including the Pending Work-summary unlink;
- Task Link deletion;
- a partial failure;
- a cancelled block-ID prompt.

Linking a PRE/POST row doesn't advance either, because a Today-linked checklist row stays due.

### A6 details

- "Resolved" means the row is closed, stamped today, or scheduled after today, or a `b` commit
  reports that it is now Blocked.
- On non-checklist rows, that is every committed write.
- On PRE/POST rows, it is only a cancel, a future schedule or roll, or a new open prerequisite.
- These always stay: Esc, `q`, Ctrl+[, Ctrl+R, Back, opening a stage, and no-op writes.

### A11 details

- The lane hint becomes `Ctrl+Alt+F keep · Alt+N release · Ctrl+Shift+Enter today`.
- The PRE hint becomes `Ctrl+Enter done · ]s skip`.
- Add "already done (Ctrl+Enter)" to the docs §6 outcome list.

## Gesture policy

This is the answer to "which other keymaps?". The rule is evaluated only when the gesture
started on the landing ([A2](#a2-conditions)) and committed a write.

| Gesture | Non-checklist landing (NEW…ROTTEN) | Checklist landing (PRE/POST) | Phase |
| --- | --- | --- | --- |
| Ctrl+Enter, close | **advance**, but stop at the checklist boundary ([A4](#a4-details)) | advance within the group (existing). Stops at the end of PRE; POST closes on its last row. | 1 |
| Ctrl+Enter, reopen | stay | stay | — |
| Ctrl+Alt+F / Alt+F | advance / stay (unchanged) | advance / stay (unchanged) | — |
| Alt+N commit/release (including counted) | **advance** | stay: a lane change doesn't resolve a checklist row | 1 |
| Ctrl+Shift+Enter, link | **advance** once the whole link succeeds, including the block-ID prompt | stay | 1 |
| Ctrl+Shift+Enter, unlink or Task Link deletion | n/a | stay | — |
| [Task Card commits](#task-card-commits) (list below the table) | **advance if resolved**, which in practice is every committed write | advance only if the row is now closed, scheduled after today, or Blocked | 1 |
| Task Card `x` cancel, after its reason stage | **advance** | **advance** | 1 |
| Task Card Esc, `q`, Ctrl+[, Ctrl+R, Back, or opening a stage | stay | stay | — |
| Decay card opened by Ctrl+Alt+F / by Alt+F | advance except Reword / stay. Unchanged, but routed through the shared tail. | n/a | 1 (refactor) |
| Ctrl+Shift+M move | **advance** instead of focusing the destination | stay | 2 |
| Ctrl+Shift+] demote `#task` → bullet | candidate: the "not a task" outcome; it has its own picker | stay | later, optional |
| Alt+[ / Alt+] status cycling | stay: an exploratory, multi-press gesture | stay | — |
| Create a project note from a task; `!` transclusion; Ctrl+6; Ctrl+Shift+O; yank | stay: these aren't answers, or they start editing | stay | — |
| Hand edits, mouse checkbox clicks, the Tasks modal, hooks, sync, capture, the CLI | stay: no gesture can be attributed | stay | — |

### Task Card commits

The Task Card commits in that row:

- `1`–`4` and `0`;
- the schedule commit;
- Ctrl+Enter (apply recommendation);
- `f` and `b`;
- the lane row;
- Ctrl+D;
- a More-property commit.

The Task Card is only the entry surface. The same commits reached by mouse or from the command
palette get the same policy (from `__cdx`).

## What exists today

Verified.

### Walk machinery

| Piece | Where | Role |
| --- | --- | --- |
| `planReviewJump(queue, {cursor, anchor, …})` | nav `480:16` | Pure planner. Its order is: the cursor entry ±1, else the anchor's first surviving `afterKeys` entry, else rank 1. It skips handled keys, so a lagging cache never steps from a stale row. |
| `landOnReviewQueueEntry(entry)` | nav `520:279` | Resolves the live line, then moves the cursor: `setEditorCursor` in the same note, or a leaf-reuse open in another note. Sets `reviewLanding = {path, text, key, tier, day}`. |
| `jumpToDueTask(dir, {fromStamp, endpoint})` | nav `520:394` | Backs `]s`, `[s`, `]S`, and `[S`. It rereads the queue once after a stale landing, resets the anchor after every landing, and adds the boundary and POST-tail notices. |
| `buildReviewAnchor` | nav `470:754` | Holds the handled keys plus the ordered `afterKeys`/`beforeKeys`, taken from the queue *before* the write. |
| `refreshTaskFreshness({advance})` | nav `520` | Alt+F keeps and stays; Ctrl+Alt+F keeps and advances. |
| `maybeAdvanceFreshnessDecayWalk` | nav `530:685` | The decay card advances once after commit, but only when Ctrl+Alt+F opened it, and never for Reword. This is the existing precedent for advancing after a modal write. |
| `claimReviewWalkCtrlEnter` → `completeReviewChecklistRow({withinGroup: true})` | nav `535:65`, `:168` | The Ctrl+Enter claim (detailed below the table). |
| Cycler handoff | tsc `140:129`, `160:4` | Vim `<C-CR>` offers the key to nav api v2 first. The non-Vim `toggle-task-open-done` command (tsc `160:27`) never asks; it is unbound in the vault (plan D1/D8). |

**The Ctrl+Enter claim.** Nav claims Ctrl+Enter only when all of these hold:

- the landing is from today;
- the editor is active and on the same path;
- the cursor line's text equals the landing's text;
- the tier is PRE or POST.

It then walks the live rows of the same group. On the last PRE row it stays put and shows
`]s → NEW`.

### Which answers move on today

| Gesture on a landed row | Today |
| --- | --- |
| `]s` `[s` `N]s` `]S` `[S` | Navigation only. |
| Ctrl+Alt+F | Keeps or completes, then advances. It crosses from PRE into the next tier; on POST it walks the rows, then closes. |
| Alt+F | Keeps or completes, and stays. |
| Decay card | Advances only when Ctrl+Alt+F opened it, and never for Reword. |
| Ctrl+Enter on a PRE/POST landing | Completes, and advances within the group only. |
| Ctrl+Enter on any other tier | Completes in place. |
| Alt+N commit/release | Stamps, and stays. |
| Ctrl+Shift+Enter | Link stamps (when it rewrites the line) and adds the task to Today. Unlink never stamps. Both stay. |
| Ctrl+Shift+P Task Card commits | Writes, closes the card, and stays. Every commit stamps, except the cancel row, which closes the task. |
| Ctrl+Shift+M | Stamps each moved open task, then focuses the destination (nav `650:515–525`). |

### Facts that settle disagreements between the reports

Checked in code.

- **Unlink never stamps.**
  - `applyPomodoroTaskUnlink` (bip `120:516`) has no `stampLine`.
  - `docs/freshness.md` §5 lists unlink under block-id-prompt's "never stamps".
  - `__mus` said otherwise.
- **Task Card `f` stamps.**
  - `setRefreshLine` "also stamps" (nav `360:98`, `510:431`; the `docs/freshness.md` §5 table).
  - `__gem` said otherwise.
- **Every committed Task Card write takes a non-checklist row out of the walk.**
  - Every commit stamps the rewritten open task, except the cancel row, which closes it
    (`docs/freshness.md` §5).
  - So your qualifier only matters on **PRE/POST rows**, which "resolve only by completion
    through Tasks, never by a stamp" (`decisions:review-walk-is-tiered`).
- **Ctrl+Shift+M stamps each moved open task** (`docs/freshness.md` §5; nav `650:423`). `__mus`
  thought the task stays due.
- **The link outcome is invisible to a line diff.**
  - Ctrl+Shift+Enter on an already-Next task that already has a block ID can leave its source
    line unchanged, because the stamp only applies when the line is rewritten.
  - What resolves the row is the Today link in the daily note.
  - So the link path must *report* its outcome (from `__cdx`).
- **On a non-checklist landing, Ctrl+Shift+Enter always links.** Today-linked tasks are in no
  tier except PRE/POST, so a landed non-checklist row is never already linked, apart from cache
  lag.
- **The two Ctrl+Enter close paths differ.**
  - The ordinary close, `toggleActiveCheckboxOpenDoneAndPropagate` (tsc `160:204`), propagates
    to an embedded transclusion and finalizes both identities.
  - `completeTaskAtCursor` (tsc `160:99`), which the PRE/POST claim uses, does not propagate,
    and it accepts `[?]`.
  - Routing every tier through the claim, as `__gem` proposes, would therefore lose the
    propagation.
- **The `groupWalk` precedence is intended.**
  - `withinGroup && tier === "pre" || tier === "post"` (nav `535:223`) parses as
    `(withinGroup && pre) || post`.
  - That matches plan D4: all three keys walk the POST rows. `__mus` flagged it; it is not a
    bug.
- **The lane hint advertises the wrong keep key.**
  - It reads "Still next? **Alt+F** keep · Alt+N release · Ctrl+Shift+Enter today" (led
    `120:220–223`, nav fallback `480:371`).
  - `docs/freshness.md` §6 says to keep with Ctrl+Alt+F; Alt+F is the stay variant.
  - The PRE hint never mentions Ctrl+Enter (from `__cld`).
- **Review landings do not visibly record a `<C-o>` jump.**
  - Same-note landings use `setEditorCursor`.
  - `scripts/test-navigation-jump-history.cjs` never exercises `jumpToDueTask`.
  - The move commit shows how to record an origin (`createVimJumpContextWithOrigin`, nav
    `650:505`).
  - This is not verified live. Treat "`<C-o>` returns to the answered row" as something to
    build, not something to assume.

### Volume

Live, 2026-10-06: `bob freshness list -f json` returned 184 walk entries:

- PENDING 3, NEXT 34, RETURNED 7, REFERENCES 28, ROTTEN 111, POST 1;
- PRE 0 (already done today).

Getting NEXT back under its cap of 15 takes about 19 releases, and none of them advance today.
In steady state, the decision record budgets about 25 lane decisions a day.

## Implementation design

### Approaches considered

| Approach | Verdict |
| --- | --- |
| Bind each key to "action, then `]s`" | **Reject.** Async prompts and cancellation break it, and it risks double handling. |
| A passive watcher that jumps when the landed entry leaves the queue (vault, Tasks, or editor events) | **Reject.** It can't tell a gesture from typing, sync, or hooks, so it jumps mid-edit. It also races the cache. |
| A second "advance" chord for every gesture (Ctrl+Alt+N, …) | **Reject.** It doubles the chord surface, when the point is to remove keystrokes. |
| A global "review mode" toggle | **Reject.** The landing already *is* the mode, scoped to one row, with nothing to switch off. |
| A dedicated OmniFocus-style triage card | **Not now.** It is a big build, and it loses the in-note context that landing on the source line keeps. |
| Nav performs every write (extend the claim everywhere) | **Reject** beyond checklist rows. It would duplicate the writers. |
| **Capture before / continue after in nav; writers report their outcomes** | **Recommended.** |

### The nav helper

New fragment `536-plugin-review-advance.js`, nav 2.5.0.

**`captureReviewGesture(editor)`** is synchronous and never throws. It reuses the claim's guard
prefix (nav `535:65–89`) and returns one of three values:

- `null` when not on a landing, and the gesture behaves normally;
- `{busy: true}` while an advance is in flight or inside the settle window, and the caller
  swallows the key with no write;
- a frozen origin `{epoch, path, line, text, key, tier, day, queueBefore, anchor}`.

**`continueReviewWalkAfter(origin, outcome)`** is async, never throws, and resolves to
`{advanced}`. It:

1. **refuses** when the origin is null or consumed, when the day changed, or when
   `origin.epoch !== this.reviewLandingEpoch` (a newer landing or `]s` happened);
2. **stays** when `reviewOutcomeResolves(origin.tier, outcome)` is false;
3. **stops at the boundary**, for Ctrl+Enter only: when the planned successor is across the
   checklist boundary, it shows the `]s → LABEL` toast (reusing
   `formatReviewChecklistGroupEndNotice`);
4. **consumes** the landing and adds every handled key to the anchor, including counted refs
   through `matchFreshStampRefs`;
5. **records** the origin in the Vim jump history, following the `createVimJumpContextWithOrigin`
   precedent;
6. **jumps**: sets the in-flight flag, runs `jumpToDueTask(1, { fromStamp: anchor })` with the
   outcome line prepended to the landing toast, clears the flag, and opens the settle window.

**Outcome kinds:**

- `complete`;
- `cancel`;
- `link-today`;
- `lane`;
- `card {afterLine, blocked?}`;
- `move {refs}`;
- `decay {action, advance}`.

**`reviewOutcomeResolves(tier, outcome)`** is a pure function, exported in `helpers`.

- **Checklist tier.** It returns true for `complete`, `cancel`, a card whose after-line is closed
  or scheduled after today, or `blocked: true`. Everything else is false.
- **Non-checklist tier:**
  - `complete`, `cancel`, `link-today`, `lane`, and `move` return true.
  - `card` returns true when the after-line is closed, carries today's `[fresh::]` stamp, or is
    scheduled after today.
  - An unchanged line returns false. This also covers project-frontmatter-only edits.

**Shared tail.** Move the advance in `finishFreshStamp`, `maybeAdvanceFreshnessDecayWalk`, and
`completeReviewChecklistRow` onto the same tail. Then every path jumps exactly once and composes
its notices the same way.

**Landing lifetime.**

- Clear `reviewLanding` when:
  - a `file-open` of another path happens that the walk or the gesture didn't cause (in
    `trackOpenedFile`);
  - the walk is empty or shows "Review closed";
  - an answer consumes it.
- Bump `reviewLandingEpoch` on every landing.

**Nav api v3.** In `createDependencyNavApi` (nav `480:901`), bump `version: 2 → 3` and add:

```js
reviewWalk: Object.freeze({
  version: 1,
  capture(editor) { /* origin | {busy: true} | null; sync; never throws */ },
  continue(origin, outcome) { /* Promise<{ok, advanced}>; never throws */ },
}),
```

- Keep `claimReviewWalkCompletion` as it is.
- ledger-tools checks `>= 1` and the cycler checks `>= 2`, so the bump is safe.
- Update the tests that assert the api version.

### Where to wire it

| Gesture | Capture point | Continue point |
| --- | --- | --- |
| Ctrl+Enter, checklist row | the existing claim | the existing group walk in `completeReviewChecklistRow`; only the notices and the tail are shared |
| Ctrl+Enter, non-checklist row | tsc `handleVimTaskToggleOpenDone`, after the claim declines (tsc `140:135`) | after `toggleActiveCheckboxOpenDoneAndPropagate` resolves `true` *and* the transition was a close: `{kind: "complete"}` |
| Alt+N | the start of `toggleTaskLane` (nav `510:293`) | after `toggleTaskLaneOnTasks` (nav `510:626`) succeeds, including any Work Log prompt: `{kind: "lane", refs}` |
| Ctrl+Shift+Enter | the top of bip `openPomodoroTaskLink` (bip `120:12`), before the presence check and the block-ID prompt | after `applyPomodoroTaskLink` (bip `120:408`) returns `true`: `{kind: "link-today"}`. Never after unlink. |
| Task Card | `openBulletPropertyPicker` (nav `550:205`), which passes the origin and line index into the modal | Task Card close (details below the table) |
| Ctrl+Shift+M (phase 2) | when the move session is created | `commitTaskMoveSession` (nav `650:354`): with an origin, skip `focusTaskMoveDestination` and continue with `{kind: "move", refs}` |
| Decay card | unchanged | route `maybeAdvanceFreshnessDecayWalk` through the shared tail |

**Task Card close.** In the modal's `onClose` (nav `350:608`):

- read the after-line at the captured line index;
- once focus has returned (for example with `setTimeout(0)`), call
  `continue(origin, {kind: "card", afterLine, blocked})`.

This covers every stage commit without touching each writer.

**Cycler sketch:**

```js
const nav = this.app.plugins?.plugins?.["bob-navigation-hotkeys"]?.api;
const walk = Number(nav?.version) >= 3 ? nav.reviewWalk : null;
const origin = walk ? walk.capture(view.editor) : null;
if (origin && origin.busy) return; // swallow the key: no write
// … existing dispatch …
const closing = isTranscludedCompletionClosableStatus(taskStatus);
const wrote = await this.toggleActiveCheckboxOpenDoneAndPropagate(editor, file, taskStatus);
if (wrote && closing && origin) void walk.continue(origin, { kind: "complete" });
```

### Tests

These go in bob-plugins `scripts/`; add every new file to the `npm test` list.

**New `test-navigation-review-advance.cjs`:**

- the `reviewOutcomeResolves` matrix: checklist and non-checklist tiers × each outcome kind;
- guard misses: wrong day, path, or text; a consumed landing; a note left since landing; a newer
  epoch;
- Esc and no-op writes stay;
- the busy sentinel, both in flight and in the settle window;
- counted refs make one jump;
- wrap, an empty queue, and a POST closeout that never wraps;
- a lagging cache that still lists the answered row;
- a recurrence row inserted above the completed one.

**Extend `test-navigation-checklist-ctrl-enter.cjs`:**

- the D3 regression: the last PRE row stays, and Ctrl+Alt+F crosses;
- Ctrl+Enter advancing on non-checklist tiers;
- the boundary stop into POST.

**Cycler and block-id-prompt suites:**

- api v3, v2 only, and absent;
- the busy sentinel swallows the key;
- unlink and reopen never continue;
- transclusion propagation still runs.

**Task Card:**

- a write versus Esc on close;
- a priority change on a checklist row stays;
- a future schedule advances;
- a frontmatter-only edit stays.

**Decay card:**

- opened by Alt+F, it stays;
- Reword stays;
- exactly one jump.

**Build and smoke test:**

- Run `npm run build`, then `npm test`, then `bob plugins sync`.
- Smoke-test on the desktop:
  - Vim normal mode;
  - same-note and cross-note landings;
  - a nested modal cancel;
  - `<C-o>` after an auto-advance.

### Docs

- **bob-cli `docs/freshness.md`:**
  - §6 steps 2, 3, and 5;
  - mark "→ next" in the outcome list and add "already done: Ctrl+Enter";
  - a §13 rollout-log entry.
- **The rest of bob-cli:**
  - the walk paragraph in `docs/getting-started.md`;
  - api v3 in `docs/task-dependencies.md` §9;
  - the Task Card note in `docs/projects.md`.
- **bob-plugins READMEs and manifests:** nav 2.5.0, cycler 1.26.0, block-id-prompt 1.22.0, and
  ledger-tools for the hint strings.

## Where the reports disagreed and how I resolved it

| Question | Positions | Resolution |
| --- | --- | --- |
| Should Ctrl+Enter cross the end of PRE? | cdx, cld, mus, gem: cross. grk: keep the D3 stop. | **Keep the stop** ([A4](#a4-details)). D3's hazard gets *worse* once Ctrl+Enter also advances on non-checklist rows, because the accidental close moves you away from the evidence. A ~300 ms settle window doesn't cover a rhythmic extra press one or two seconds later. Generalize D3 to "never across the checklist boundary". |
| Should Ctrl+Enter advance on non-checklist tiers? | cdx, cld, mus, gem: advance. grk: defer ("completing is a drop"). | **Advance.** Completing means "already done"; drop is `x`. You asked for it, and A4 plus the guard contain the risk. |
| How does Ctrl+Enter reach nav? | gem: drop the claim's tier gate, so nav runs `completeTaskAtCursor`. cld, cdx, grk: the cycler keeps its own close, then notifies nav. | **The cycler keeps its close.** Verified: `completeTaskAtCursor` skips transclusion propagation and accepts `[?]`. |
| How is the write's effect checked? | gem: after the write, check that the cursor text still equals `landing.text`. mus: check that the key is gone from a fresh queue read. | **Neither works.** After the write the line text has changed, so gem's check always fails, and the fresh queue lags. Capture before the write, then decide from the writer's outcome plus the line after the write. |
| Does unlink stamp? | mus: yes. cdx, grk: no. | **No** ([verified](#facts-that-settle-disagreements-between-the-reports)). Unlink never advances. |
| Does Task Card `f` stamp? | gem: no. The others: yes. | **Yes** ([verified](#facts-that-settle-disagreements-between-the-reports)). `f` resolves the row. |
| Task Card `b` | gem: never advance. cld: advance on any write. grk, mus, cdx: depends on the outcome. | On non-checklist rows the commit stamps, so the row is resolved. On checklist rows, advance only if the row becomes Blocked. The card closes on commit either way, and `<C-o>` returns. |
| Ctrl+Shift+M | cld, grk, gem: advance. cdx: phase 2, keep the destination focus. mus: no, thinking the task stays due (wrong). | **Advance, in phase 2,** after asking you ([open question 2](#open-questions-for-bryan)). |
| A decay card opened by Alt+F | grk: advance when on a landing. The others: stay. | **Stay.** Alt+F is the stay answer. |
| A busy/settle guard | cld: explicit. cdx: reentrancy and held keys. The others: silent. | **Required in v1.** |
| A new decision record | cld: yes. grk: no, it's keymap behavior. | **Yes, a short one after shipping.** This is a policy that spans nav, the cycler, and block-id-prompt, and future agents will re-propose its rejected alternatives. Write it through `/sase_memory_write`. |

## Open questions for Bryan

1. **PRE → NEW with Ctrl+Enter ([A4](#a4-details)).** Keep the stop, as I recommend, or cross
   like Ctrl+Alt+F? Either way it is one branch.
2. **Move during review ([A8](#requirement-adjustments)).** Should it advance, or keep landing in
   the destination so you can place the task?
3. **A kill switch.** Do you want a key in `~/.config/bob/config.yml` that turns auto-advance
   off? I recommend no: Alt+F, `<C-o>`, and a plugin rollback are enough.
4. **The Alt+F / Ctrl+Alt+F pair.** Once every other answer advances, Alt+F could become the only
   keep key, and advance. I'd wait a week of use before touching that pair again.

## Recommended solution

Build one short-lived, landing-scoped "answer, then advance" helper in bob-navigation-hotkeys,
and have [every answering gesture](#gesture-policy) call it.

1. **The rule.**
   - When a gesture that started on the row `]s` just landed on commits a write that takes that
     row out of today's walk, nav advances exactly once.
   - It lands on the next remaining walk entry from the anchor, with the usual boundary, wrap,
     and POST notices.
   - Alt+F is the one answer that stays. Escape, refusals, no-op writes, unlink, reopen, Reword,
     and status cycling also stay.
2. **The mechanism.**
   - Nav api v3: `reviewWalk.capture()` before the write, then
     `reviewWalk.continue(origin, outcome)` after the final commit.
   - Resolution comes from the writer's reported outcome plus a pure predicate on the line after
     the write.
   - No queue re-query, no watcher, no mode, and no new chords.
   - Move the existing Ctrl+Alt+F, decay, and checklist advances onto the same tail.
3. **Phase 1.** One plan, roughly nav +350–450 lines, the cycler and block-id-prompt about +40
   each, and about 600 lines of tests (`__cld`'s estimate). It contains:
   - the helper and its guards: busy/settle, the epoch, the landing lifetime, and `<C-o>`;
   - Ctrl+Enter on non-checklist tiers, through the cycler, keeping its
     [checklist-boundary stop](#a4-details);
   - Alt+N;
   - Ctrl+Shift+Enter link;
   - the Task Card close predicate;
   - the decay and Ctrl+Alt+F refactor;
   - the [hint and docs fixes](#a11-details).
4. **Phase 2:**
   - Ctrl+Shift+M advance, if you agree;
   - optionally, Ctrl+Shift+] demote;
   - one merged toast.
5. **After shipping.** Write a short decision record through `/sase_memory_write`: "Answering a
   walk landing advances the walk; Alt+F stays; Ctrl+Enter never crosses the checklist
   boundary".

The result is the smoother morning you asked for: every real answer takes one key, `]s` remains
the skip key, and each jump traces back to a decision you finished.

## About this report

> **Research request (paraphrased).** During the GTD morning review (`]s` walk), Ctrl+Enter
> already completes a landed PRE row and jumps to the next one. Bryan wants that whenever a
> review item is closed with Ctrl+Enter. He also wants other gestures that answer the item to
> jump automatically, naming Ctrl+Shift+Enter, and Ctrl+Shift+P when the chosen Task Card option
> removes the item from the review stack. He asked for more candidate gestures, a critique of
> the plan, explicit adjustments to the requirements, and a recommended solution.

**Consolidated report** · lead researcher · 2026-10-06

### Inputs

- Five independent reports: `__cdx`, `__cld`, `__grk`, `__mus`, and `__gem`, in this directory.
- My own verification against:
  - bob-plugins `b662018`: nav 2.4.0, task-status-cycler 1.25.0, block-id-prompt 1.21.2, and
    ledger-tools freshness namespace v7;
  - bob-cli `1d4d9fd`: `docs/freshness.md` §§5–6;
  - the decision records `review-walk-is-tiered` and `task-lanes-are-sticky`;
  - `plan:202610/ctrl_enter_checklist_walk.md`;
  - a live `bob freshness list -f json`.

Nothing in the vault, bob-cli, or bob-plugins was modified.

### Abbreviations

File references are relative to the bob-plugins plugin `src/` directories, with line numbers at
`b662018`:

- **nav** is `bob-navigation-hotkeys`;
- **tsc** is `task-status-cycler`;
- **bip** is `block-id-prompt`;
- **led** is `bob-ledger-tools`.

"Checklist" means the PRE and POST tiers. "Non-checklist" means NEW through ROTTEN.

## Sources

**Code** (bob-plugins `b662018`):

- nav:
  - `470-keydown-and-freshness.js:747–900`
  - `480-review-jump-and-nav-api.js:16`, `:365–376`, `:862`, `:901–952`
  - `490-plugin-lifecycle.js:127–150`, `:285–300`
  - `510-plugin-link-commit-and-lane.js:293`, `:386–431`, `:626`
  - `520-plugin-lane-links-and-review.js:270–520`, `:816`, `:934`
  - `530-plugin-freshness-refresh-and-decay.js:207–220`, `:685`
  - `535-plugin-review-checklist-walk.js` (whole file)
  - `540-plugin-decay-picker-and-cancel.js:194`, `:232`, `:307`
  - `350-picker-task-card.js:300–420`, `:608`
  - `360-picker-schedule-review.js:98`
  - `550-plugin-cancel-and-counted-property.js:205`
  - `650-plugin-move-commit.js:354`, `:423`, `:500–545`, `:630`
  - `670-plugin-project-files.js:691`
- tsc:
  - `010-core.js:48–51`
  - `030-task-toggles.js:1–30`
  - `140-plugin-vim.js:129–215`
  - `160-plugin-completion.js:1–300`
- bip: `120-plugin-pomodoro-links.js:12–90`, `:408–510`, `:516–640`
- led:
  - `120-freshness-footer.js:195–245`
  - `170-plugin-lifecycle.js:239–264` (freshness api v7)
- `scripts/test-navigation-jump-history.cjs` and the `package.json` test list

**Docs** (bob-cli `1d4d9fd`): `docs/freshness.md` §5 "Who stamps" and §6 "Review ritual".

**Plans and memory:**

- `plan:202610/ctrl_enter_checklist_walk.md` (D1–D8)
- `decisions:review-walk-is-tiered`
- `decisions:task-lanes-are-sticky`

**Live data:** `bob freshness list -f json` on 2026-10-06 (184 entries).

**Researcher reports** (this directory):

- [`review_walk_answer_auto_advance__cdx.md`](review_walk_answer_auto_advance__cdx.md): the
  coordinator token design, the action inventory, and the Today-link and frontmatter subtleties.
- [`__cld.md`](review_walk_answer_auto_advance__cld.md): the outcome rule, the toggle
  double-press hazard, the policy table, the hint bug, and the volume figures.
- [`__grk.md`](review_walk_answer_auto_advance__grk.md): the D3 fence, the link/unlink split, and
  the gesture classification.
- [`__mus.md`](review_walk_answer_auto_advance__mus.md): the walk-active gate and the
  counted-batch single jump.
- [`__gem.md`](review_walk_answer_auto_advance__gem.md): `<C-o>` recovery, boundary notices, and
  Ctrl+Shift+] as a candidate.

**External** (as cited by `__cld` and `__cdx`; I did not re-verify them):

- [mutt manual, `$resolve`](http://www.mutt.org/doc/manual/)
- [Gmail auto-advance](https://www.makeuseof.com/auto-advance-feature-in-gmail-how-to-use-it/)
- [OmniFocus review, Mark Reviewed](https://support.omnigroup.com/documentation/omnifocus/mac/2.7/en/review/)
- [W3C APG modal dialog](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/)

**Not verified:**

- live Obsidian behavior;
- whether same-note review landings already record a `<C-o>` jump;
- the real latency between a write and its landing, which sets the settle window;
- whether Obsidian hotkey commands fire on key auto-repeat.
