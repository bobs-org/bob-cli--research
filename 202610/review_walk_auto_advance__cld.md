# Auto-advancing the `]s` review walk after answering gestures

> **Research request (paraphrased).** During the GTD morning review (`]s` walk), Ctrl+Enter
> already completes a landed PRE row and jumps to the next one. Bryan wants that for any review
> item closed with Ctrl+Enter. He also wants other gestures that answer the item to jump
> automatically: Ctrl+Shift+Enter, and Ctrl+Shift+P when the chosen Task Card option removes the
> item from the review stack. He asks me to find and propose any further gestures, critique the
> plan, adjust the requirements where justified, and recommend an implementation.

**Researcher:** cld · **Date:** 2026-10-06 · **Read:**
- bob-plugins (linked repo, `origin/master` at `b662018`)
- bob-cli `docs/freshness.md` §6 and `docs/getting-started.md`
- decision records `review-walk-is-tiered`, `task-lanes-are-sticky`, `ready-is-freshness-gated`,
  `rotten-keeps-use-priority-decay`, and `decay-decisions-are-available-immediately`
- prior research `research:202610/gtd_pre_post_checklist_tiers/gtd_pre_post_checklist_tiers.md`
- a live `bob freshness list -f json`

Nothing in the vault, bob-cli, or bob-plugins was modified.

All file references below are relative to the bob-plugins repo root unless they start with
`docs/`, which means bob-cli. **nav** is `plugins/bob-navigation-hotkeys/src/`, **tsc** is
`plugins/task-status-cycler/src/`, **bip** is `plugins/block-id-prompt/src/`, and **led** is
`plugins/bob-ledger-tools/src/`.

---

## TL;DR

1. **It's a good idea, and smaller than it looks.**
   - Nav already has one advance primitive: `jumpToDueTask(1, { fromStamp: this.reviewAnchor })`
     (nav `520-…:394`).
   - Nav also has a walk anchor that is already designed so that *"`]s` after an Alt+N release,
     Ctrl+Shift+Enter, or a roll continues from the successor"* (nav `470-…:747-753`).
   - Auto-advance is therefore "call that primitive at the end of each answering gesture". It
     must sit behind the landing guard that Ctrl+Enter already uses (`reviewLanding`, nav
     `535-…:65`).
2. **Base the rule on outcomes, not on a list of keys.**
   - `docs/freshness.md` §6 already lists the eight review outcomes, one key each.
   - Only one outcome moves on by itself today: *still right*, via Ctrl+Alt+F.
   - The rule I'd adopt: **an answer that takes the landed item out of today's walk advances the
     walk.** Two exceptions stay put on purpose: Alt+F (the stay variant of keep) and hand edits.
3. **The real hazard is toggles, not navigation.** Ctrl+Enter, Alt+N, and Ctrl+Shift+Enter are
   all toggles. With auto-advance, a fast double press either undoes the answer you just gave,
   or answers the *next* item before you have seen it. The design needs a busy/settle guard;
   nothing protects against this today.
4. **Recommendation:**
   - Add one nav helper that captures the origin before the write and continues after commit.
   - Expose it through nav api v3 `reviewWalk` so task-status-cycler and block-id-prompt can
     use it.
   - Use a small, tested policy table (§4).
   - Let Ctrl+Enter cross tier boundaries instead of stopping at the end of PRE.
   - On PRE/POST checklist rows, advance only on outcomes that actually resolve the row.
   - Keep Alt+F/Ctrl+Alt+F unchanged.

---

## 1. What exists today (verified in code)

### 1.1 The walk machinery

| Piece | Where | What it does |
| --- | --- | --- |
| `planReviewJump(queue, {cursor, anchor, …})` | nav `480-…:16` | Pure planner. Order: cursor entry ± 1 (text-first match), else the anchor's first surviving `afterKeys` entry, else rank 1. Handled keys are never matched, so a lagging Tasks cache cannot make it step from a stale position. |
| `landOnReviewQueueEntry(entry)` | nav `520-…:279` | Moves the cursor, opening the note through leaf reuse if needed. Records **`reviewLanding = {path, text, key, tier, day}`**. |
| `jumpToDueTask(direction, {fromStamp})` | nav `520-…:394` | The `]s`/`[s` command. After every successful landing it sets `reviewAnchor = buildReviewAnchor(queue, [landedKey], rank, today)` (`:460`), with the comment *"so a later release, roll, or stamp continues from here"*. |
| `buildReviewAnchor` | nav `470-…:754` | Stores handled keys plus the ordered `afterKeys`/`beforeKeys` from the queue snapshot. This is why a write followed by `]s` already lands on the right successor. |
| `refreshTaskFreshness(cm, {advance})` | nav `520-…:514` | Alt+F (stay) and Ctrl+Alt+F (`advance: true`), which ends with `jumpToDueTask(1, {fromStamp: this.reviewAnchor})` (`:816`, `:934`; links in `530-…:207`). |
| `maybeAdvanceFreshnessDecayWalk` | nav `530-…:685` | Decay-card outcomes advance exactly once after commit, but only when the card was opened by Ctrl+Alt+F, and never for Reword. **This is the existing "advance after a modal write" precedent.** |
| `claimReviewWalkCtrlEnter(editor)` | nav `535-…:65` | The Ctrl+Enter claim. It requires the landing to be from today, in the active editor, on the same path, with the cursor line text equal to `landing.text`. The tier must be PRE or POST. It then calls `completeReviewChecklistRow({advance: true, withinGroup: true})` (`:168`). |
| Cycler side | tsc `140-…:135`, `160-…:4` | The Vim `<C-CR>` handler asks nav api v2 `claimReviewWalkCompletion` first. **The command path `handleToggleOpenDoneCommand` (tsc `160-…:27`) never asks**, so Ctrl+Enter from insert mode or the hotkeys.json command never hands off to the walk. |

**Takeaway.** Advancing, cache-lag safety, and "continue from where I was" are already solved.
The landing guard is also solved, but only Ctrl+Enter uses it. What's missing is **calling the
primitive from the other answer gestures**, plus a guard against toggle double presses.

### 1.2 Which gestures move on today

| Gesture | On a landed item today |
| --- | --- |
| `]s` `[s` `N]s` `]S` `[S` | Navigation only |
| Alt+F | Keeps (stamp) and **stays**. On a PRE/POST row it completes in place. |
| Ctrl+Alt+F | Keeps and **advances**. On PRE it completes and advances *across* tiers; on POST it walks the remaining POST rows, then "Review closed". |
| Decay card opened via Ctrl+Alt+F | **Advances**, except Reword |
| Decay card opened via Alt+F | Stays |
| Ctrl+Enter on PRE/POST landing | Completes and **advances within the group only**. The last PRE row stays put with a `]s → NEXT-TIER` hint (`535-…:307`). |
| Ctrl+Enter on any other tier | Completes and **stays** (no claim) |
| Alt+N (commit/release, `N<Alt+N>`) | Writes and **stays** |
| Ctrl+Shift+Enter (link to today) | Writes and **stays** (block-id-prompt never calls nav) |
| Ctrl+Shift+P Task Card writes (`1`–`4`, `0`, Enter→date, Ctrl+Enter recommendation, `x`, `b`, `f`, Alt+N, Ctrl+D) | Writes, closes the card, and **stays**. No card path references `reviewAnchor` or `reviewLanding`. |
| Ctrl+Shift+M move | Writes and **jumps to the destination note** (`650-…:525`) |

### 1.3 The review outcomes are already specified

`docs/freshness.md` §6, "Review outcomes, one key each", lists these. I added the "Auto-advances
today?" column.

| Outcome | Key | Auto-advances today? |
| --- | --- | --- |
| still right | Ctrl+Alt+F / Alt+F | **yes** (Ctrl+Alt+F) |
| see it less often | Ctrl+Shift+P `f` | no |
| not now | Ctrl+Shift+P `1`–`4` | no |
| do today | Ctrl+Shift+Enter / Alt+N | no |
| route to a project | Ctrl+Shift+M | no (goes to destination) |
| drop | Ctrl+Shift+P `x` | no |
| sequence | Ctrl+Shift+P `b` | no |
| wording wrong | edit, then Alt+F | no (correct: an edit is not an answer) |

The list is also missing one outcome: **already done** (Ctrl+Enter).

The landing hints don't match this list either:

- The lane hint says *"Still next? **Alt+F** keep · Alt+N release · Ctrl+Shift+Enter today"*
  (led `120-freshness-footer.js:222-223`, nav fallback `480-…:369`), but §6 says keep with
  Ctrl+Alt+F.
- The PRE hint *"Ctrl+Alt+F done → next · ]s skip"* never mentions Ctrl+Enter.

### 1.4 Volume

The live walk at the time of research (2026-10-06) had **184 entries**:

- PENDING 3, NEXT **34** (cap 15), RETURNED 7, REFERENCES 28, ROTTEN 111, POST 1, PRE 0 (already
  done today).
- That is **72 commitment rows**.

At these numbers, NEXT alone needs about 19 releases to get back under its cap, and none of
those releases advance today. The decision record budgets "about 25 lane decisions a day at the
caps". Each non-keep answer currently costs an extra `]s`, and leaves you parked on an item you
have already answered.

---

## 2. Critique of the plan

### 2.1 Is it a good idea? Yes.

- **It finishes a pattern that is already half built.** Ctrl+Alt+F, the decay card, and
  checklist Ctrl+Enter already move on. Alt+N, Ctrl+Shift+Enter, and the Task Card are the
  documented answers for the lanes ("keep / release / today"), yet two of those three stop you
  on the spot. That inconsistency is a cost in its own right: you have to remember which answers
  move on.
- **It removes a "parked" state.** After an answer you sit on a resolved item. That's where
  side-quests start: editing, checking a project, reading a reference. Then `]s` has to rely on
  the anchor to find its way back. Auto-advance keeps the walk the default next thing.
- **There is strong precedent:**
  - mutt's `$resolve` (default *yes*): "the cursor will be automatically advanced to the next
    (possibly undeleted) message whenever a command that modifies the current message is
    executed".
  - Gmail's auto-advance: after archive, delete, or mute, it shows the next conversation.
  - OmniFocus's Review perspective: "Mark Reviewed … presents the next project in the list".

  Note the split. mutt advances on *any* modification. Gmail advances only on actions that
  *remove the item from the list*. OmniFocus advances only on the reviewed gesture. Bryan's own
  qualifier ("a task card option … that removes the review item from the review stack") is the
  Gmail rule, and I think it's the right one (§2.2).

### 2.2 What I'd change about the framing

1. **Base it on outcomes, not keymaps.** "Which keymaps imply iteration" invites a growing list.
   Use the predicate *"this gesture answered the landed item, so it is out of today's walk"*,
   implemented once in nav. Every current and future gesture then calls one helper. The §4
   table is the policy, and new gestures opt in with one line.
2. **"Removes the item from the stack" is nearly always true, except on checklist rows.**
   - Every Task Card write stamps `[fresh:: today]`, except `x`, which closes the task
     (`docs/freshness.md` §5 table; §6 says "every row except 'edit' stamps by itself").
   - So on the seven non-checklist tiers, *every* committed card write takes the item out of
     the walk. Your qualifier only matters on **PRE/POST rows**. Per the decision record,
     those "resolve only by completion through Tasks, never by a stamp".
   - On those rows, a priority or refresh edit leaves the row due. Only completion,
     cancellation, a future schedule, or a new open dependency resolves it.
3. **Make the landing the scope, not a "review mode".** The guard Ctrl+Enter uses ("the cursor
   is on the exact row `]s` just put you on") is the right boundary. Alt+N, Ctrl+Shift+Enter,
   and Ctrl+Shift+P are used all day outside the review, and must behave exactly as before
   there.
4. **Read "next/first" as "next remaining, then wrap".**
   - The next item is the next remaining entry in walk order. At a tier boundary, that is the
     *first* entry of the next tier.
   - At the end of the queue it wraps to the first remaining (skipped) entry, with the existing
     wrap notice. This is exactly `planReviewJump` with the anchor.
   - When nothing remains, it shows the existing empty / "Review closed" notice and stays.

### 2.3 Risks and mitigations

| Risk | Why it matters | Mitigation |
| --- | --- | --- |
| **Toggle double press** | Ctrl+Enter (open↔done), Alt+N (Ready↔Next), and Ctrl+Shift+Enter (link↔unlink) are toggles. The write and the jump are async (tens to hundreds of ms). A second press before the landing hits the old line, whose text has changed so the guard misses, and runs the **normal toggle, which reverts the answer**. A second press after the landing **answers the next item unseen**. Ctrl+Alt+F has a milder form of the second case today. | Nav keeps `reviewAdvanceInFlight` plus a short settle window (≈300 ms after an auto-landing). While either is active, `reviewWalk.capture()` returns a **busy** sentinel and callers swallow the key with no write. Ignore `event.repeat` where a DOM event exists; the decay card and counted-key handlers already do this (nav `060-…:119`, `610-…:493`). |
| Undo across notes | After a cross-note advance, Ctrl+Z in the new note doesn't undo the write in the old one. | Call `captureActiveFilePosition()` (and the Vim jumplist bridge) before every auto-advance, so `<C-o>` returns to the answered item; then `u`. Verify this for same-note landings too: those use `setEditorCursor` and may not push a jump. |
| Two actions on one item | Example: Alt+N, then add a dependency. Auto-advance moves you away after the first. | Every Task Card write already closes the card, so the card already treats a write as terminal. Use `<C-o>` to go back, or Alt+F as the deliberate "stay" answer. No new modifier. |
| Surprise outside the walk | A stale landing could fire hours later, for example when the last landed row is completed in the afternoon. | The landing is valid only while it's unconsumed, from today, the walk isn't closed, and **you haven't left the landed note** (clear it on `file-open` of another path not caused by the walk or the gesture). |
| "Edit, then answer" | After a reword, the line text differs from `landing.text`, so the guard misses. | Accept this in v1: Ctrl+Alt+F still advances, because it uses the anchor, not the landing. Optional later fallback: same path, same day, same line number, still a task. |
| Notice overload | The gesture's own toast plus the landing toast stack. | v1 accepts the two stacked toasts. Merging later reuses the `doneLine + boundary + landing` composition already in `completeReviewChecklistRow`. |
| Plugin version skew | cycler and block-id-prompt call into nav. | Feature-detect `api.version >= 3 && api.reviewWalk`. Older nav means today's behavior. Older callers with new nav means no change; the v2 `claimReviewWalkCompletion` stays. |
| Tasks cache lag | The fresh queue may still list the answered row. | Already solved: handled keys plus `afterKeys` (§1.1). Counted gestures must add *all* their targets' keys to the anchor, as `finishFreshStamp` does (`530-…:216`). |
| Faster walks mean more rubber-stamping | The decision record lists "the rubber-stamp risk of a daily lane queue". | Neutral. Auto-advance speeds up *answers*, not skips, and keeps (the rubber stamp) already advance. Skips (`]s`) are unchanged. |

### 2.4 Alternatives considered

| Option | Verdict |
| --- | --- |
| **A. One nav helper called at the end of each answering gesture, guarded by the landing** (capture origin before the write, continue after commit) | **Recommended.** Explicit, testable, and reuses `jumpToDueTask` and the anchor. Unchanged outside the walk. |
| B. Passive watcher: auto-jump when the landed entry disappears from the queue (vault, Tasks-cache, or editor events) | Rejected. It can't tell a gesture from a hand edit, mouse click, or sync, so you'd get jumps mid-typing. It also races the Tasks cache. It violates the spirit of the "explicit gesture, never a timer" rule in the decay decisions. |
| C. An "advance" twin for every gesture (Alt+N vs Ctrl+Alt+N, …), as Alt+F/Ctrl+Alt+F does | Rejected. It doubles the chord surface and burns scarce chords. Keep the one existing pair. |
| D. A global "review mode" in which every task write anywhere advances | Rejected. The landing guard *is* the mode, scoped to one row, with nothing to forget to turn off. |
| E. A dedicated review/triage modal (an OmniFocus-style card with single-key answers) | Not now. It's a big build and loses the in-note context (children, logs, siblings) that the source-line landing deliberately keeps. Possible later evolution: when the Task Card is opened on a landing, show the walk position and also offer keep and today. |
| F. Extend the Ctrl+Enter *claim* pattern everywhere (nav performs every write) | Rejected beyond checklist rows. Nav would re-implement or proxy cycler and block-id-prompt writers. "Writers write, nav navigates" is cleaner. |

---

## 3. Requirement adjustments (explicitly called out)

| # | You asked | I recommend | Why |
| --- | --- | --- | --- |
| **R1** | A list of keymaps that "imply iteration" | **One outcome rule** ("an answer that takes the landed item out of today's walk advances") behind one nav helper, with a policy table (§4) as the spec. | Keeps future gestures consistent, and matches the outcome list in §6 of the docs. |
| **R2** | Advance "anytime" these keys close a review item | **Only when the gesture starts on the row `]s` just landed on**: same day, same note, same line text, landing unconsumed, note not left since landing. | These keys are used all day outside the review. |
| **R3** | Ctrl+Enter "jumps to the next/first review item" | **Ctrl+Enter crosses tier boundaries**, from PRE into NEW/PROJECTS/… and on every other tier. This **removes** the documented rule "It never leaves PRE" (§6 step 2, nav README). The boundary toast reports skipped PRE rows (`PRE done · 1 skipped → NEW 1/4 …`). POST keeps its group walk, then "Review closed". | Matches Ctrl+Alt+F on PRE, which already crosses. One mental model. |
| **R4** | Ctrl+Shift+Enter advances | **Advance on *link* (do today) only.** Unlink never advances. On a PRE/POST row, linking does **not** advance, because a Today-linked checklist row stays due. | Lane/Ready landings are never Today-linked, so on them the gesture is always "link". Checklist rows resolve only by completion (decision record). |
| **R5** | Ctrl+Shift+P advances "if the option removes the item" | **Advance on any committed card write on non-checklist tiers**, since every write stamps or closes. On checklist rows, advance only on `x` cancel, a future date (Enter→date, `1`–`4` roll, recommendation roll), recommendation cancel, or `b` with an open prerequisite. Esc, `q`, Ctrl+[, Ctrl+R, and Back never advance. | §2.2 point 2. |
| **R6** | (not asked) | **Alt+N advances** (commit Ready→Next, release Next/Pending→Ready, counted `N<Alt+N>`). A Pending release advances only after its Work Log prompt is confirmed; Esc means no write, so no advance. | Alt+N is the documented *release* answer for the lanes. NEXT is at 34 against a cap of 15. |
| **R7** | (not asked) | **Ctrl+Shift+M move advances instead of focusing the destination** when started on a landing. The toast names the destination. Outside the walk, behavior is unchanged. | "Route to a project" is a documented review outcome. Triage first, organize later. *(Judgment call; see Q2.)* |
| **R8** | (not asked) | **Alt+F stays the one "stay" answer**, including a decay card it opens. **Ctrl+Alt+F is unchanged.** | Alt+F/Ctrl+Alt+F is an explicit, recently re-mapped pair (`7cd25ea`, 2026-10-04). Keeping one stay answer gives an escape hatch without a modifier. |
| **R9** | (not asked) | **A busy/settle guard** that swallows answer keys while an advance is in flight and ≈300 ms after an auto-landing. Also make `<C-o>` return to the answered item. | Toggle double-press and undo (§2.3). Without this I would not ship it. |
| **R10** | (not asked) | **Fix the landing hints:** lanes become `Still next? Ctrl+Alt+F keep · Alt+N release · Ctrl+Shift+Enter today`, PRE becomes `Ctrl+Enter done · ]s skip`, POST becomes `Ctrl+Enter done · closes the review`. Add "already done (Ctrl+Enter)" to the §6 outcome list. | The hints currently advertise the non-advancing Alt+F, and never mention Ctrl+Enter. |
| **R11** | (not asked) | **The non-Vim Ctrl+Enter command path also consults the walk**: `handleToggleOpenDoneCommand`, tsc `160-…:27`. | Today only the Vim `<C-CR>` mapping claims, so insert mode or a hotkeys.json binding silently doesn't advance. |
| **R12** | (not asked) | **Write a successor decision record** after shipping: "Answering a landed walk item advances the walk; Alt+F is the stay answer". | It's a cross-plugin UX policy that `review-walk-is-tiered` doesn't cover. Records are immutable, so add a new one rather than editing. |

---

## 4. Proposed gesture policy (the answer to "which other keymaps")

The rule is evaluated only when the gesture **started on the current landing** and **committed a
write**. "Checklist" means the landed tier is PRE or POST.

| Gesture | Non-checklist landing (NEW…ROTTEN) | Checklist landing (PRE/POST) | Change |
| --- | --- | --- | --- |
| Ctrl+Enter (complete) | **advance** | **advance** (PRE crosses tiers; POST walks POST rows, then closes) | new / changed |
| Ctrl+Alt+F (keep → next) | advance | advance (completes) | unchanged |
| Alt+F (keep) | stay | stay (completes in place) | unchanged |
| Decay card via Ctrl+Alt+F / via Alt+F | advance (not Reword) / stay | n/a | unchanged |
| Alt+N commit/release (incl. counted) | **advance** | stay (row still due) | new |
| Ctrl+Shift+Enter: link (do today) | **advance** | stay (Today-linked rows stay due) | new |
| Ctrl+Shift+Enter: unlink | n/a (lane landings are never linked) | stay | — |
| Ctrl+Shift+P `1`–`4`, `0`, Enter→date, Ctrl+Enter recommendation, `f`, `b`, Alt+N, Ctrl+D | **advance** | advance only if the write resolves the row (future date, cancel, open dependency); else stay | new |
| Ctrl+Shift+P `x` (drop) | **advance** | **advance** | new |
| Ctrl+Shift+P Esc / `q` / Ctrl+[ / Ctrl+R / Back | stay (no write) | stay | — |
| Ctrl+Shift+M move (incl. counted) | **advance** (instead of focusing the destination) | stay | new |
| Alt+] / Alt+[ status cycling | stay (exploratory multi-press) | stay | — |
| Ctrl+Shift+O child bullet, `!` transclusion, Ctrl+6 block ID, yank path | stay (not answers) | stay | — |
| Hand edits, `dd`, mouse checkbox clicks, Tasks' own commands | stay (can't be attributed safely) | stay | — |
| Mac capture / `bob capture` / CLI writes | stay (outside the editor; stale-landing handling covers them) | stay | — |

For checklist rows, a pure predicate `checklistRowResolvedBy(afterLine, today)` can decide
whether a Task Card write resolved the row. It returns true when the status is closed, when
`scheduled` is later than today, or when the line is gone. A new open dependency arrives as an
explicit outcome. This avoids enumerating card outcomes per stage.

---

## 5. Recommended solution

### 5.1 The rule (one sentence for the docs)

> When a gesture that **started on the row `]s` just landed on** commits a write that takes
> that row out of today's walk, nav jumps to the next remaining walk entry (wrapping, with the
> usual boundary and wrap notices). Alt+F is the one answer that stays.

### 5.2 Architecture: "writers write, nav navigates"

Add a new nav fragment, `536-plugin-review-advance.js`. Insert it after `535` in
`fragments.json` and keep it under the 1000-line cap. It holds three pieces.

**`captureReviewGestureOrigin(editor)`** is synchronous and never throws.

- It reuses the guard prefix of `claimReviewWalkCtrlEnter`: landing from today, active
  view/editor, same path, and cursor line text equal to `landing.text`.
- It returns `Object.freeze({path, text, key, tier, line, day, anchor: this.reviewAnchor})`
  or `null`.
- It returns the sentinel `{busy: true}` while an advance is in flight or inside the settle
  window.

**`continueReviewWalkAfter(origin, outcome)`** is async, resolves to `{advanced}`, and never
throws. `outcome` is `{kind, refs?, afterLine?}`. It:

1. returns early if `!origin`, or if `reviewOutcomeAdvances(origin.tier, outcome)` is false;
2. marks the landing consumed: `this.reviewLanding = null`;
3. extends `origin.anchor` with the keys of any counted `refs`, using `matchFreshStampRefs`;
4. calls `captureActiveFilePosition()`;
5. sets `reviewAdvanceInFlight` and runs
   `await this.jumpToDueTask(1, {fromStamp: anchor})`;
6. clears the flag and opens the settle window.

**`reviewOutcomeAdvances(tier, outcome)`** is a pure function exported in `helpers`, and is
the §4 table as code.

**Nav api v3.** In `createDependencyNavApi` (nav `480-…:901`), bump `version: 2 → 3` and add:

```js
reviewWalk: Object.freeze({
  version: 1,
  capture(editor) { /* → origin | {busy:true} | null; sync; never throws */ },
  continue(origin, outcome) { /* → Promise<{ok, advanced}>; never throws */ },
}),
```

Keep `claimReviewWalkCompletion` as is, for older cyclers. ledger-tools only checks
`version >= 1`, and the cycler checks `>= 2`, so the bump is safe.

### 5.3 Where to wire it

| Gesture | Capture point | Continue point |
| --- | --- | --- |
| Ctrl+Enter, checklist rows | inside the existing claim (nav `535-…:65`) | `completeReviewChecklistRow` (nav `535-…:168`). Keep the live-group scan, but when no live successor remains in PRE, fall through to the cross-tier `planReviewJump` (the Ctrl+Alt+F branch) and stop returning at `:307`. |
| Ctrl+Enter, other tiers | cycler `handleVimTaskToggleOpenDone` (tsc `140-…:129`) **and** `handleToggleOpenDoneCommand` (tsc `160-…:27`), via `nav.reviewWalk.capture` | after `toggleActiveCheckboxOpenDoneAndPropagate` resolves `true` while closing (tsc `160-…:204`): `continue(origin, {kind: "complete"})`. The cycler keeps its exact close semantics: transclusion propagation, `finalizeClosedTasks`, and the `[?]` refusal. |
| Alt+N | `toggleTaskLane` start (nav `510-…:293`) | after a successful `toggleTaskLaneOnTasks`. Task Link lines are never landings. |
| Task Card | `openBulletPropertyPicker` (nav `550-…:205`). Pass the origin into the modal. | Modal `onClose` (nav `350-…:608`). If the landed line changed or vanished since open, defer `continue(origin, {kind: "card", afterLine})` with `setTimeout(0)`, so focus has returned to the editor first. The line diff covers every stage commit (schedule review, cancel reason, lane release reason, refresh, dependency, delete) without touching each writer. A `b` commit passes `{kind: "depends-on", blocked: true}` explicitly. |
| Ctrl+Shift+M | when the move session is created (picker open) | `commitTaskMoveSession` (nav `650-…:354`). With an origin, skip `focusTaskMoveDestination` (`:525`) and continue with `{kind: "move", refs}`. |
| Ctrl+Shift+Enter | bip `openPomodoroTaskLink` (bip `120-…:12`), before the block-ID prompt | after a successful `applyPomodoroTaskLink` (bip `120-…:408`): `continue(origin, {kind: "link-today"})`. Never after `applyPomodoroTaskUnlink` (`:516`) or Task Link mode. |
| Decay card | unchanged | unchanged |

When `capture` returns `{busy: true}`, the caller consumes the key with **no write**. That is
the double-press guard.

### 5.4 Landing lifetime

`reviewLanding` is set on every landing, as today. It is cleared when:

- an answer consumes it;
- another landing replaces it;
- the day changes (already checked);
- the walk reports empty or "Review closed";
- a `file-open` of a different path happens that the walk or the gesture didn't cause
  (`trackOpenedFile` in nav `490-…` already listens).

### 5.5 Notices and hints

- v1: the gesture keeps its own toast ("Moved 1 task to X", the cancel notice, the
  stamp/upkeep notice). `jumpToDueTask` adds the normal landing toast with its boundary and
  wrap preambles.
- Later: one merged toast, `✓ <outcome> · <task>` + boundary + landing, as
  `completeReviewChecklistRow` already does.
- Update the hint strings in led `120-freshness-footer.js:206-223` and the nav fallback
  `480-…:365-376` (R10).

### 5.6 Docs and decision

Update these:

- `docs/freshness.md` §6: steps 2, 3, and 5, and the outcome list (mark "→ next" on every row
  except Alt+F and edit; add *already done: Ctrl+Enter*);
- `docs/getting-started.md` (the review paragraph);
- the bob-plugins README rows for nav, cycler, and block-id-prompt;
- the change log at the end of `docs/freshness.md`.

After shipping, add the successor decision record (R12) through `/sase_memory_write`.

### 5.7 Tests

Tests use the repo's `scripts/test-*.cjs` harnesses:

- **New `scripts/test-navigation-review-advance.cjs`:**
  - the `reviewOutcomeAdvances` matrix, checklist and non-checklist;
  - guard misses (wrong day, path, or line text, a consumed landing, a note left since
    landing);
  - Esc / no write means no jump;
  - busy sentinel during the in-flight period and the settle window;
  - counted refs added to the anchor;
  - wrap and empty queue;
  - lagging cache (the answered row still in the queue).
- **Extend `scripts/test-navigation-checklist-ctrl-enter.cjs`:** PRE→NEW crossing with skipped
  rows reported; POST unchanged; non-checklist tiers.
- **Extend the cycler and block-id-prompt suites:** api v3 present, absent, and v2-only; the
  busy sentinel swallows the key; unlink never continues.
- **Task Card:** the line diff on close (write vs Esc) and the deferred continue after focus
  returns.
- **Run:** `npm run build`, `npm run build:check`, `npm test`, then `bob plugins sync`.

### 5.8 Order of work

All of this fits one plan. If it's split, ship it in value order:

1. **Core helper and guards** (`536`, api v3, busy/settle, landing lifetime, `<C-o>`), plus
   **Ctrl+Enter on all tiers with PRE crossing** (R3, R11) and the hint fixes (R10).
2. **Alt+N and Ctrl+Shift+Enter**: the lane "release" and "today" answers, the highest volume
   at NEXT 34/15.
3. **The Task Card line diff, and move** (R5, R7).
4. Optional: merged toasts, and the "edit, then answer" fallback for the guard.

Rough size: nav +300–450 lines (most of it in `536` and wiring), cycler and block-id-prompt
about +40 lines each, led hint strings, and about 600 lines of tests.

---

## 6. Open questions for Bryan

1. **Ctrl+Enter at the end of PRE:** should it cross into the next tier, as recommended (R3),
   or keep the deliberate "stop at the end of PRE" pause the current implementation documents?
2. **Move during review:** should it advance (R7), or keep jumping to the destination so you
   can place the task inside the project?
3. **Alt+F:** should it stay the one "stay" answer (R8)? Alternatively, once everything else
   advances, make Alt+F advance on landings and retire Ctrl+Alt+F. I'd wait a week of use
   before touching that pair again.
4. **Kill switch:** nav has no settings tab and reads `~/.config/bob/config.yml`. Do you want a
   config key to turn auto-advance off, or is Alt+F plus `<C-o>` enough? I lean towards no
   knob.

---

## 7. Sources

**Code** (bob-plugins `b662018`):

- nav:
  - `470-keydown-and-freshness.js:747-900`
  - `480-review-jump-and-nav-api.js:16-200, 365-376, 901-952`
  - `490-plugin-lifecycle.js:325-333`
  - `520-plugin-lane-links-and-review.js:279-520, 780-938`
  - `530-plugin-freshness-refresh-and-decay.js:150-260, 600-720`
  - `535-plugin-review-checklist-walk.js`
  - `350-picker-task-card.js:319-400, 608`
  - `510-plugin-link-commit-and-lane.js:293`
  - `550-plugin-cancel-and-counted-property.js:205`
  - `650-plugin-move-commit.js:354-600`
- tsc: `010-core.js:48-52`, `140-plugin-vim.js:129-215`, `160-plugin-completion.js:1-250`,
  `180-plugin-editor-edits.js:339-430`
- bip: `120-*.js:12-80, 408, 516`
- led: `120-freshness-footer.js:206-223`

**History:** `2c3eb4c` (Ctrl+Enter checklist navigation), `252ec0e` (PRE/POST
complete-and-advance), `7cd25ea` (Ctrl+Alt+F remap).

**Docs** (bob-cli): `docs/freshness.md` §5–6 (the review ritual and the outcome list) and
`docs/getting-started.md`.

**Memory:** `decisions:review-walk-is-tiered`, `decisions:task-lanes-are-sticky`,
`decisions:ready-is-freshness-gated`, `decisions:rotten-keeps-use-priority-decay`, and
`decisions:decay-decisions-are-available-immediately`.

**Prior research:** `research:202610/gtd_pre_post_checklist_tiers/gtd_pre_post_checklist_tiers.md`
(F7 `[?]` and Ctrl+Enter, F8 the recurrence line shift, F9 the text-first cursor match).

**Live data:** `bob freshness list -f json` on 2026-10-06 (184 walk entries).

**External:**
- [mutt manual — `$resolve`](http://www.mutt.org/doc/manual/)
- [Gmail auto-advance (MakeUseOf)](https://www.makeuseof.com/auto-advance-feature-in-gmail-how-to-use-it/)
- [Gmail auto-advance direction setting (Google System blog)](http://googlesystem.blogspot.com/2010/10/go-to-next-gmail-message-after.html)
- [OmniFocus 2 for Mac manual — Review / Mark Reviewed](https://support.omnigroup.com/documentation/omnifocus/mac/2.7/en/review/)
- [Omni Group blog — Getting active with OmniFocus: reviewing](https://www.omnigroup.com/blog/Getting_active_with_OmniFocus_reviewing)

**Not verified:**
- live Obsidian behavior;
- whether same-note review landings already push a `<C-o>` jump;
- the exact async latency between the write and the landing (this sets the settle window);
- whether Obsidian hotkeys fire on key auto-repeat for the commands involved.
