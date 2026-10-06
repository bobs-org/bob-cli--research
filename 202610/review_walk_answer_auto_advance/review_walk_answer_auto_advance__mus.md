# GTD morning-review keymap auto-advance (`]s` walk): research

Researcher: mus (`__mus`). Independent swarm report. Peer reports (`__cdx`, `__cld`, `__grk`, `__gem`) were not consulted.

Question: during the `]s` morning review walk, which keymaps/actions that close or
remove the current review item should automatically jump to the next/first review
item, and what is the best way to implement it? The request specifically names
`<ctrl+enter>` (already done for PRE, proposed for all closes), `<ctrl+shift+enter>`,
and `<ctrl+shift+p>` (Task Card options that remove the item), and asks for other
candidates plus a general critique and recommended solution.

## 1. What the walk is today (ground truth)

Sources: `bob-navigation-hotkeys` sources in the linked `bob-plugins` checkout,
`task-status-cycler` sources, plugin READMEs/manifests, and the `review-walk-is-tiered`
decision record (read via `sase memory read`).

- The walk is one shared tier-ordered queue from `bob-ledger-tools`
  `api.freshness.queue()`: `PRE → NEW → PROJECTS → PENDING → NEXT → RETURNED →
  REFERENCES → ROTTEN → POST`. `]s`/`[s` (vim) are `jumpToDueTask(+1/−1)`,
  `]S`/`[S` are first/last endpoints, `Ctrl+Alt+J/K` are the same jumps.
  `N]s` is N steps. Notices name tier rank and confirmation age; stepping into
  ROTTEN/POST carries a boundary preamble.
- Walk state is two fields on the nav plugin: `reviewLanding` (exact
  `{path,text,key,tier,day}` of the last landing; guards the PRE/POST
  `Ctrl+Enter` claim) and `reviewAnchor` (built by `buildReviewAnchor` on every
  landing and every `Alt+F`/`Ctrl+Alt+F` stamp; holds handled keys plus
  `afterKeys`/`beforeKeys` so the next `]s` continues from the successor even
  though the Tasks cache lags). Both are day-gated (`reviewAnchorIsCurrentDay`).
- Pure planner `planReviewJump` resolves cursor-on-live-entry → neighbor, else
  anchor → first surviving successor (`]s`) / last surviving predecessor (`[s`),
  else first/last entry. `landOnReviewQueueEntry` resolves the entry to a live
  line (`resolveReviewQueueLine`) and moves the cursor, same-note or cross-note.
- Tiers are due-only: anything stamped today drops out. Checklist membership is
  exact `#gtd`+`#pre`/`#post` tokens; checklist rows resolve only by completion
  through Tasks (never by stamp), need freshness ns v7 `checklistTiers` + cycler v2.
- Current advance matrix (this is the key baseline):
  - `Alt+F` = keep/stamp, no advance. On a checklist row: complete in place.
  - `Ctrl+Alt+F` = stamp/complete, then exactly one `jumpToDueTask(1,
    {fromStamp: reviewAnchor})`. On PRE it crosses into the next tier; on POST it
    advances within POST. Decay-card `Keep/Drop/LessOften/level` picks inherit
    this (advance iff the press was `Ctrl+Alt+F`); `Reword` never advances.
  - `Ctrl+Enter` on the exact PRE/POST landing row: handed from cycler to nav
    (`claimReviewWalkCtrlEnter` → `completeReviewChecklistRow({advance: true,
    withinGroup: true})`). Advances **within the group only**: next live row of
    the same tier, no wrap, no tier crossing. Final PRE row stays put with a
    `]s → <next-tier>` hint; POST advances with `Ctrl+Enter` or `Ctrl+Alt+F`
    while `Alt+F` stays and counts remaining; last POST closes the review.
  - `Ctrl+Enter` elsewhere (cycler close of a task, Task-Link close/strike,
    Depends-On prerequisite close): no anchor update, no advance.
  - `Ctrl+Shift+Enter` (block-id-prompt: link/unlink task ↔ today's Pomodoro +
    freshness stamp): no anchor update, no advance.
  - `Ctrl+Shift+P` Task Card: modal; `Ctrl+Enter` applies the recommended
    roll/decay/cancel, `Enter` opens Schedule, `Alt+N` lane row, `x` cancel row,
    `f` review-every row, `b` depends-on row, digits set priority, `Ctrl+D`
    delete property, `Esc/q/Ctrl+[` close without writing. Successful intents
    close the modal. No review-anchor/advance integration on any row.
  - `Alt+N` lane commit/release (editor command): stamps, prunes Pomodoro links
    on release; no anchor update, no advance.
  - Schedule-review commit (`Enter`, `Shift+Enter` skip-reason): writes
    `scheduled`/Schedule Log; no advance.

## 2. Critique of the plan as stated

The plan's instinct is right — a review walk where every disposition leaves the
cursor sitting on a now-dead row forces a manual `]s` after every decision, which
is exactly the friction a morning walk should not have — but the plan as stated
("anytime we close the current review item using this keymap, jump") is too broad
in three ways, and too narrow in one.

1. **"Close" is not the trigger; "handled while walk-active" is.** Outside a walk,
   `Ctrl+Enter` must keep its current in-place semantics. The only safe trigger is
   *walk-active*: a current-day `reviewAnchor`/`reviewLanding` exists **and** the
   cursor is on a live queue entry (or a Task Link whose target is). Every
   auto-advance must be gated on that. The existing PRE claim already does this
   shape (landing + day + cursor + queue match); generalize it, don't drop it.
2. **Not every close removes the item from today's walk.** A close always removes
   it (closed tasks are in no tier), but several named candidates do not always
   remove it: `Ctrl+Shift+Enter` *unlink* removes the Today link without changing
   the lane and still stamps (so in practice it does drop out today — but it does
   not resolve the review decision); a Task Card *priority set* or *review-every
   set* stamps (drops out today) yet the natural reading of "removes from the
   review stack" misses them; a *schedule pick that stays open/near* still drops
   out via the stamp even though the task remains open. An action-allowlist ("these
   three keymaps always advance") will both over-fire (unlink-then-still-undecided)
   and under-fire (stamped-but-not-listed). Prefer *post-write verification* (is the
   handled key gone from a fresh queue read?) over a pure keymap allowlist, with the
   keymap as the call-site and the queue-diff as the guard.
3. **Within-group vs global advance matters only at group boundaries, but that is
   exactly where the UX lives.** While PRE rows remain, global-successor and
   next-in-group are the same rows (the queue is tier-ordered, so PRE's successor
   is the next PRE). The difference appears at the last PRE row (stay + `]s` hint
   today vs cross into NEW automatically) and at POST (advance-within-POST vs
   close-the-review on the last row). Unifying on "always global jump" without
   preserving the POST-close and ROTTEN-boundary notices would regress the closeout
   ritual (`]S` closes on POST; `Alt+F done · closes the review`). Keep those two
   special cases.
4. **Too narrow: the same logic already covers the biggest wins the request does
   not name.** `Alt+N` release/commit stamps (drops the item today) and is a core
   walk verb on PENDING/NEXT tiers — leaving it non-advancing while
   `Ctrl+Shift+Enter` advances would be incoherent. Schedule-commit-to-future
   (which additionally hides the task via the future-schedule exclusion) and the
   decay-card path (already advance-aware) belong in the same helper. Conversely,
   things that look like dispositions but are not must stay put: `Esc/q/Ctrl+[`
   (no write), row navigation (`arrows`, `Ctrl+P/N`, digits, `b/f/x` row *opens*),
   `Ctrl+R` preview refresh, `Ctrl+D` property delete, Depends-On stage open,
   cancelled prompts (Work Log `Esc`, lane-release `Esc`, schedule-review cancel),
   refused writes, and `Reword` (leaves focus for editing).

Net: the idea is good; the trigger needs narrowing (walk-active + actually-handled),
the target set needs widening (all walk-removing dispositions, not three keymaps),
and the landing behavior needs to stay tier-aware (boundary notices, POST close).

## 3. Candidate keymap/action inventory

Gate for all rows below: walk-active (current-day anchor/landing + cursor on a live
queue entry or link-to-entry) AND the write succeeded AND the handled key is gone
from the fresh queue (or the action provably closes/removes it). Failed, cancelled,
refused, or still-due outcomes never advance.

| # | Keymap / action | Removes item today? | Advance today? | Proposed |
|---|---|---|---|---|
| 1 | `Ctrl+Enter` close task at cursor (cycler) | yes (closed) | no | **yes — advance to global successor** |
| 2 | `Ctrl+Enter` on Task Link (close/strike linked task; second press reopens) | close: yes; reopen: re-adds (still stamped? reopen stamps too — drops out, but semantically returns it) | no | **close: yes; reopen: no** (stay; the item just came back) |
| 3 | `Ctrl+Enter` on PRE/POST landing (existing) | yes | within-group only | **extend: global successor at group end** (keep POST-close on last POST) |
| 4 | `Ctrl+Enter` on Depends-On line (closes/reopens prerequisite) | closes the prerequisite, not the dependent under cursor | no | **advance only if the prerequisite was the walked item** (rare; same gate decides) |
| 5 | `Ctrl+Shift+Enter` link task → today (commit-ish + stamp) | yes | no | **yes** |
| 6 | `Ctrl+Shift+Enter` unlink task from today | stamps → yes, but review-undecided | no | **weak yes, or no**: prefer **no advance** — unlinking is not a disposition; the keep/release decision is still pending. If implemented, it falls out of the generic rule anyway; call this out as the one deliberate exception. |
| 7 | `Ctrl+Shift+Enter` on Task Link bullet (delete link) | target stamped only when its line is rewritten; link row itself is not a queue entry | no | **no** (cursor is on a Pomodoro, not the walked task) |
| 8 | Task Card `Ctrl+Enter` recommendation apply (roll/decay/cancel) | roll-to-future/cancel: yes; simple roll: stamp → yes | no | **yes when handled key is gone** (covers all three uniformly) |
| 9 | Task Card `x` cancel row | yes | no | **yes** |
| 10 | Task Card `Alt+N` lane row (commit/release) | stamp → yes | no | **yes** |
| 11 | Task Card schedule commit (date pick) | future: yes (excluded); near: stamp → yes | no | **yes when gone from fresh queue** |
| 12 | Task Card `f` review-every set/clear | stamps → yes | no | **yes** (it is the explicit "ask me later" disposition) |
| 13 | Task Card `b` depends-on add that blocks the task | Blocked tasks are walk-excluded → yes | no | **yes when blocked**; pure add-without-block still stamps → yes by the generic rule |
| 14 | Task Card `Enter` (opens Schedule stage) / digits / `Ctrl+R` / `Ctrl+D` / closes | no write yet / no removal | no | **no** |
| 15 | `Alt+N` editor commit/release | stamp → yes | no | **yes** (the largest unlisted win; PENDING/NEXT core verb) |
| 16 | Schedule-review commit (`Enter` / `Shift+Enter`) | as #11 | no | **yes when gone** (same helper as #11) |
| 17 | `Alt+F` keep (advance=false) | yes, deliberately stays | no (by design) | **no change** — it is the stay-put counterpart to `Ctrl+Alt+F` |
| 18 | `Ctrl+Alt+F` keep-and-advance | yes | already advances | **no change** (reuse its helper) |
| 19 | Decay-card Keep/Drop/LessOften/level (`Ctrl+Alt+F` origin) | yes | already advances (except Reword) | **no change** |
| 20 | `Ctrl+Shift+M` move task | moves note, stays due | no | **no** |
| 21 | `]`/`[` checklist skip, `[s` backward, `]S`/`[S` endpoints | navigation, no write | n/a | **no change** |

Counted (`N…`) and Task-Link sessions: advance once after the whole batch (skip all
handled keys), not per target — the existing `finishFreshStamp`/`refreshTaskFreshnessOnLinks`
shape already does this.

## 4. Design: one walk-aware advance helper, thin call sites

Recommended shape (mirrors the existing `Ctrl+Alt+F` path, which is the proven
pattern: `finishFreshStamp` → anchor → single `jumpToDueTask(1, {fromStamp})` with
stale-retry inside `jumpToDueTask`):

- New nav-hotkeys helper, e.g. `maybeAdvanceReviewWalk(queueBefore, handledRefs,
  {dateText})`: match refs via `matchFreshStampRefs`, `buildReviewAnchor`,
  re-read queue, if the handled keys are gone (or the action was a close) and the
  fresh queue is non-empty and the current tier is not end-of-POST, call
  `jumpToDueTask(1, {fromStamp: anchor})`; on last-POST show the existing closed
  notice instead of wrapping; on empty show the upkeep-meter notice. Exactly one
  jump per gesture; never on cancel/refusal/still-due.
- Call sites (thin, walk-gated inside the helper so non-walk behavior is
  byte-identical): cycler `Ctrl+Enter` close path (needs a nav API or a
  lead-in/lead-out handoff — cycler owns the chord; nav owns the walk; a
  `noteReviewHandled(refs)` API keeps the plugin boundary clean), block-id-prompt
  `Ctrl+Shift+Enter` link path, Task Card commit resolutions (#8–#13, after modal
  close, from editor context), `Alt+N` toggle, schedule-review commit.
- Notices: reuse `buildReviewJumpNotice` + `buildReviewBoundaryNotice` (+ POST tail)
  so auto-lands are indistinguishable from `]s` lands. Keep the `✓ Done · …`
  prefix lines the checklist path already emits.
- Focus discipline for the card: advance after `this.close()`, awaiting the editor;
  if the card was opened outside a walk, the helper is a no-op by construction.
- No new modes, chords, settings, or second keymaps. The `Alt+F` vs `Ctrl+Alt+F`
  split stays as the explicit stay/advance pair for keeps; everything else becomes
  implicitly advance-on-handled, which is learnable precisely because the gate
  ("it moves iff the item just left today's walk") is uniform.

Why not the alternatives: (a) per-keymap `advance: true` flags alone would
re-create the current inconsistency (three flags today, five tomorrow, POST-close
handled three ways); (b) a separate "review mode" toggle adds state Bryan must
manage each morning for no benefit over the anchor gate that already exists; (c) a
new `Ctrl+Alt+Enter`-style explicit-advance chord preserves manual `]s` forever and
contradicts the request.

## 5. Edge cases and risks (must be in the acceptance bar)

- Walk-inactive presses change nothing (most `Ctrl+Enter`s in the vault).
- Cancelled/failed writes never advance: Work Log `Esc`, lane-release `Esc`,
  schedule-review cancel, decay-card dismiss, stale preimage, Tasks-command-missing,
  Cancelled-link notice, `not-task/not-open` from `completeTaskAtCursor`.
- Reopen (`Ctrl+Enter` second press on a struck link) stays.
- Recurrence: closing a recurring task spawns its next occurrence — the anchor's
  handled-key mechanism must skip the just-closed key, not land on the fresh
  occurrence as "successor" confusion; verify against the recurrence path.
- Cross-note Task-Link closes: land via the leaf-reuse path like `]s` does.
- POST last row: close notice, no wrap. Empty queue: upkeep-meter notice, no wrap.
- Counted batches and multi-link sessions: one jump, all keys skipped.
- Double-advance: decay-card + stamp paths must share the single helper call.
- The `groupWalk` expression in `completeReviewChecklistRow` reads as
  `(withinGroup && pre) || post` — confirm intended precedence while touching it;
  the recommended rewrite subsumes it into the global-successor helper plus the
  POST-close special case.

## 6. Recommended solution

Adopt the uniform rule: **while walk-active, any successful disposition whose
handled item just left today's walk advances exactly once to the global successor
(first surviving `afterKey`, with the existing ROTTEN-boundary/POST-close/empty
notices); everything else stays.**

Concrete scope (MVP = rows 1, 3, 5, 8–12, 15, 16 above; explicitly exclude row 6
unlink-advance, row 14, rows 17–21):

1. Add `maybeAdvanceReviewWalk` (or equivalent) next to `finishFreshStamp`/
   `maybeAdvanceFreshnessDecayWalk`, reusing `matchFreshStampRefs`,
   `buildReviewAnchor`, `jumpToDueTask(1, {fromStamp})`, and the notice builders.
2. Extend the PRE/POST `Ctrl+Enter` claim from within-group to global-successor,
   keeping last-POST close semantics.
3. Route `Ctrl+Enter` closes (via a minimal cycler→nav handoff),
   `Ctrl+Shift+Enter` links, `Alt+N` toggles, schedule commits, and Task Card
   walk-removing commits through it — each gated on walk-active + write-success +
   handled-key-gone.
4. Leave `Alt+F` (stay), `Ctrl+Alt+F`/decay-card (already advance), pure navigation,
   non-committal card rows, moves, cancels, refusals, and reopens exactly as they are.
5. Tests: walk-active gate (inactive = no movement), close-advances,
   unlink-stays, last-PRE-crosses-with-boundary, last-POST-closes, empty-queue
   notice, counted-batch single jump, cancelled-prompt no-advance, reopen
   no-advance. The existing `planReviewJump`/anchor vectors are the harness to extend.

This keeps the previously shipped PRE behavior as the special case of the general
rule, answers the `Ctrl+Shift+Enter` / Task Card asks without an ever-growing
keymap allowlist (the fresh-queue check decides), and avoids the two real hazards —
teleporting outside a walk and skipping undecided items — by construction.
