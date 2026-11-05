# Close/Cancel Tasks Directly From Successor Menus — Research Report

Researcher: **mus** · 2026-11-05 · bob-cli workspace `bob-cli_40`

> Research query: let people close tasks directly from successor menus (Obsidian
> and bob-mac-capture). The sketch proposes a new `<Ctrl+X>` keymap to close and
> `<Ctrl+Shift+X>` to cancel, so that successors visibly already-complete or
> obsolete can be terminally resolved at review time instead of waiting for them
> to go rotten and reappear in a morning GTD review. Lead the design: intuitive,
> reliable, beautiful. Critique the plan, adjust requirements with callouts, end
> with a recommended solution.

---

## 1. TL;DR and recommended solution

**Yes, build it — but not exactly as sketched.** Closing obviously-done and
cancelling obviously-obsolete successors inside the successor picker is a good,
small, high-leverage addition. It removes a real papercut (see §2), it fits the
existing "offers are never auto-linked, only explicitly picked" contract
(`decisions:unblocked-tasks-are-offered`), and both surfaces already have a
picker worth extending.

**Recommended solution in one paragraph:** keep the successor picker a
pull-in picker, and add two scoped, explicitly-targeted terminal actions on the
*currently marked or highlighted offer rows*: **Close (Done)** and **Cancel
(Cancelled)**. Accept the proposer's `Ctrl+X` / `Ctrl+Shift+X` mnemonic in the
**Obsidian successor picker only**, scoped strictly to that modal (not a global
hotkey), with per-row buttons as the discoverable primary and the keys as
accelerators. On the **Mac Pull-In card** use the same verbs but Mac-idiomatic
presentation: explicit Close/Cancel buttons plus `⌃X` / `⇧⌃X` key equivalents
that rhyme without hijacking `⌘X` cut. Both clients send the closed/cancelled
offer keys back through the *existing* successor-pick plumbing; **bob-cli does
the writes** through the shared task-completion engine (tree close, ledger
retirement, dependent recovery — recovery only, never a second cascade of
links in the same gesture). Second-order unblocks resurface through the normal
freshness tiers (TICKLER/ROTTEN), never a nested picker. CLI gets additive
`--pull-in` selection syntax plus JSON `close_keys`/`cancel_keys`, never a new
`bob capture` subcommand. No silent behavior, no auto-link, no confirm dialog;
`Esc` still means "none", and every write revalidates.

**Requirement adjustments (called out explicitly, per the brief):**

1. **ADJ-1 — Do not register global `Ctrl+X` / `Ctrl+Shift+X` hotkeys.**
   Scope both chords to the successor picker modal/card only. A global
   `Ctrl+X` would fight cut, the Pomodoro-entry merge `Ctrl+X` (see §5.2), and
   mobile (no Control key). The proposer's keys survive, but fenced inside the
   picker.
2. **ADJ-2 — Cancel is a first-class sibling, not a Shift-variant
   afterthought.** The sketch treats cancel as "close with Shift". Cancel has
   different semantics (Cancel Log, no completion date, different recovery
   copy, recurring-task refusal path), different undo expectations, and
   deserves its own button, hint, preview line, and JSON result — not just a
   modifier.
3. **ADJ-3 — Close/cancel from the picker never produces its own successor
   offers in the same gesture.** A close that unblocks further tasks recovers
   them (rank, tag strip, `[unblocked::]` per the WRITE rule) and stops. No
   nested picker, no chained `-p` round. The deferred work resurfaces via
   existing freshness tiers. This is the single most important reliability
   rule; see §6.3.
4. **ADJ-4 — No new capture grammar, no new `bob task` verb.** The sketch does
   not ask for grammar, but a naive implementation might add `!`-family syntax
   or a `bob task close` command to "support" the picker. Do not. The picker
   path rides the existing `successors.pick` / `--pull-in` contract with
   additive close/cancel key lists. A standalone close/cancel-by-key command
   can come later if CLI triage demands it; it is out of scope here.
5. **ADJ-5 — Muted/unselectable rows can never be closed or cancelled from the
   picker.** Still-blocked, scheduled-later, already-planned, hidden-count,
   and sub-project-waiting rows stay inert. Only `selectable` offer rows are
   eligible, and picking a stale/changed row fails closed with a notice.

If you only read one more section, read §8 (the concrete contract) and §9
(phased rollout).

---

## 2. Is this a good idea? Critique of the plan

### 2.1 The problem is real

Today's managed-Done flow (`docs/task-dependencies.md` §12) is deliberately
conservative: predecessors recover, offers sit unlinked unless explicitly
picked, and unpicked rows "resurface through the existing freshness rules"
(§12, `decisions:unblocked-tasks-are-offered`). In practice that means a
successor you can already see is dead — a duplicate, a superseded plan, a task
finished by other means — must be either (a) pulled in and then closed (two
gestures plus a lane raise and a freshness stamp you did not want), or
(b) ignored and re-triaged tomorrow (NEW → TICKLER → ROTTEN walk tiers per
`glossary:task-freshness`, tiers PRE → NEW → PROJECTS → PENDING → NEXT →
RECURRING → TICKLER → ROTTEN → POST). The proposer's framing ("wait for them
to go rotten and show up in a morning review") is slightly overstated —
unpicked rows resurface through *all* freshness tiers, and auto-unblocked rows
come back as TICKLER via `[unblocked::]` (`decisions:unblocked-tasks-resurface-as-ticklers`),
not only as ROTTEN — but the direction is right: **the picker shows you the
task, gives you no terminal verb, and bills you a future review.** A
close/cancel verb at the point of recognition is the cheapest place to pay.

### 2.2 What is good about the sketch

- **Right place.** The successor picker is the one moment both the
  predecessor context ("why am I looking at this?") and the candidate set are
  on screen. Navigating away to close one row loses that context.
- **Right verbs.** Done vs Cancelled already exists everywhere else (Ctrl+Enter
  / Task Card cancel / `x!` / `!` vs nav cancel / `Alt+[` into Cancelled /
  relation cancel-labels). Reusing them keeps the mental model to "the same
  close, one step earlier".
- **Right instinct on symmetry.** A paired chord (`Ctrl+X` / `Ctrl+Shift+X`)
  mirrors the existing `Enter` (pull in) vs `Shift-Return` (skip) style of
  two-outcome pickers and the Task Card's bare-`x` cancel mnemonic (§5.3).

### 2.3 What is wrong or risky about the sketch as written

1. **The keys as global hotkeys would be a mistake.** `Ctrl+X` is cut in any
   focused editor/input, and it is *already taken* inside this codebase's
   picker family: the Pomodoro-entry move picker uses `Ctrl+X` to merge
   (`200-filtered-picker-modals.js` `PomodoroEntryMovePickerModal#handleKeydown`,
   footer copy "Ctrl+X absorbs/appends", tests in
   `test-navigation-hotkeys-pomodoro-move-pickers.cjs`). A global binding also
   has no meaning on mobile and collides with user `hotkeys.json`
   customization. The fix is scoping (ADJ-1), not new chords.
2. **Close ≠ cancel with Shift.** The sketch implies cancel is just "close
   harder". In this vault they are different writers (completion date +
   tree-close + retirement vs Cancel Log + `[-]` + different recovery copy and
   notices), different idempotency (`already_done` no-op vs already-cancelled
   handling), and different guards (recurring tasks: capture `!` refuses
   recurring lines per `docs/capture.md` §"Completing tasks with '!'"; nav
   cancel routes recurring tasks to Obsidian Tasks per
   `240-cancel-and-lanes.js`). Collapsing them into one modifier invites one
   code path with a flag — the exact shape that later produces "cancel wrote a
   completion date" bugs. ADJ-2 keeps them as two verbs sharing only target
   resolution and revalidation.
3. **"Close them then" hides a cascade question the sketch never asks.**
   Closing an offer row *is itself a managed-Done-shaped write*: it can unblock
   dependents, empty a project (`project_finished` pull-ins, §12.10), or drain
   a leaf project's last planned task (`keep_moving`, §12.15 K1–K8). Does the
   picker then open a *second* picker for those? Chain `x!`-style? Silently
   recover? The sketch is silent, and every option except "recover only, no
   cascade" (ADJ-3) either nests modals (fragile across the walk-hold
   machinery, `holdReviewWalkForSuccessorPicker`) or auto-links work the
   decisions explicitly forbid auto-linking. Name the rule; do not cascade.
4. **The beauty bar is load-bearing, not decorative.** A picker that gains two
   destructive verbs without row-level affordances (which rows are eligible?
   what will `Ctrl+X` do to the highlighted vs marked set? what did it just
   do?) will produce mis-closes. The current picker earns trust through
   footer hints, `pull in N` counts, plan-budget meter, folded-count lines,
   and per-row destination details (`206-successor-picker-modal.js`
   `renderFooter`/`renderResults`; Mac `CapturePullInChoiceView.swift`
   "You can see what Return will do"). Close/cancel must meet that bar, not
   ride as invisible chords.
5. **Thin-client discipline applies.** Per
   `decisions:mac-capture-is-a-thin-client`, bob-cli owns grammar, preview,
   and vault mutation; the Mac owns presentation and orchestration. A
   close-from-successor feature therefore lands **bob-cli first** (engine +
   JSON + docs), Mac second (decode + present). A Swift-side close writer is a
   rejected alternative up front.

### 2.4 Would I take a different approach?

Three alternatives were considered and rejected, one partially adopted:

- **(Rejected) A separate "triage successors later" queue.** A tray of held
  offers was explicitly rejected when offers were designed ("no separate queue
  is needed", `decisions:unblocked-tasks-are-offered` Rejected alternatives).
  Reopening it for closes reintroduces the retrieval problem that decision
  closed. Do not.
- **(Rejected) Auto-close "obviously done" offers.** Nothing in the vault can
  reliably know a task is done without a human reading it (similar-tasks
  research holds the same line: heads-up only, never auto-act,
  `decisions:similar-tasks-are-a-settled-heads-up`). Every terminal write here
  must be an explicit keypress on an explicit row — the same consent rule as
  the decay ladder (`decisions:task-decay-is-one-ladder`: "nothing moves
  without a keypress").
- **(Rejected) Close-by-link (`Ctrl+Enter` on the offer row's link).**
  Tempting (it reuses the universal close gesture), but inside a picker the
  row is not an editor link, the destination/slot semantics differ (close
  writes the *note*, not the day plan), and overloading the picker's `Enter`
  family risks mis-pulls. Keep `Enter` = pull in, always.
- **(Partially adopted) Per-row hover/button-only, no keyboard.**
  Buttons alone solve discoverability and mobile, but review-walk users live
  on keys, and the request explicitly wants keys. Adopt buttons *and* keys:
  buttons are the contract, keys the accelerator — the same split the picker
  already uses (click toggles mark; `Tab`/`Enter` accelerate).

So: the sketch's direction survives; its keys survive in narrowed scope; its
missing cascade rule, cancel semantics, and cross-client contract are supplied
below.

---

## 3. How successors work today (what the design must plug into)

### 3.1 The offer pipeline (bob-cli source of truth)

- **Rule home.** `src/native/task_complete/successors.rs` (`plan_successors`,
  `SuccessorInput`/`SuccessorPlan`, `OfferGroup`, `SuccessorSelection`) is the
  pure planner; `docs/task-dependencies.md` §12 is the contract. One gesture =
  one offer set; only picked offers link, raise to Next, and stamp `[fresh::]`.
- **Triggers.** Managed-Done gestures only (§12.1): Ctrl+Enter variants,
  nav walk Ctrl+Enter, `bob capture` closes (`x` with embeds, `x*`, `x!`,
  `^route:id=x…`), `!note:id` completes, complete-label commits, `Alt+]/Alt+[`
  into Done. **Cancel never offers** (cancel recovers only; `cancelled` /
  `not_linked: cancelled` verdicts; `successors.rs` `is_cancel_recovery`,
  `prepare_cancelled_project_contexts`). Parks (`x*`) offer only `relation`
  rows (§12.18). Ctrl+Enter on a Depends-On line offers nothing.
- **Groups.** `hand_off`, `project`, `project_finished` (§12.10),
  `keep_moving` (§12.15), `relation` (§12.18, successor-label edges),
  `note_pull` (§12.20). Obsidian nav keeps an allow-list and drops unknown
  groups (`206a-successor-picker-model.js`), so **any new group would need
  `api.successors` v4** — a reason to carry zero new groups (this design adds
  none).
- **Selection.** Obsidian picker API §12.13 (`successors.pick(model)` →
  `{picks: [{key, destination?}]}` / `null`; v3); CLI §12.14 (`-p, --pull-in`
  `all|none|K1,K2…`). `bob capture` never prompts or auto-links.
- **Second-order effects already specified.** Picked links land *before*
  retirement so retirement strikes/moves predecessors around them
  (`docs/capture.md` `!` execution step 6). Unpicked rows recover and
  resurface via freshness. Keep-moving rows are last in mixed pickers with
  their why-caption and fold line.

### 3.2 The Obsidian picker (bob-plugins, read via `sase repo open`)

- **Modal.** `SuccessorOfferPickerModal extends FilteredPickerModal`
  (`bob-navigation-hotkeys/src/206-successor-picker-modal.js`, 816 lines).
  Footer hints today: `Tab` toggle-and-move · `Ctrl+A` mark group · `↵` pull
  in · `Esc` none, plus `Ctrl+Shift+Enter` retarget when the destination
  picker API exists. Model helpers in `206a-successor-picker-model.js`.
- **Key handling today** (`handleKeydown`): `Enter` (guarded 350 ms,
  marked-else-highlighted apply), `Tab`/`Shift-Tab`, arrows, `Ctrl+A` mark
  group, `Ctrl+Shift+Enter` retarget. **No `Ctrl+X` / `Ctrl+Shift+X` handling
  exists in this modal.** Base `FilteredPickerModal#handleKeydown` handles
  `Ctrl+N/P` + `Enter` only; the `Ctrl+X` merge chord lives solely in
  `PomodoroEntryMovePickerModal` — same file family, different modal. So the
  proposed chords are *free inside this modal* but *taken elsewhere*,
  reinforcing ADJ-1 (scope, don't globalize).
- **Walk integration.** Closes during the `]s` walk hold the walk
  (`beginReviewSuccessorGestureOwner` / `holdReviewWalkForSuccessorPicker` /
  `releaseReviewSuccessorGestureOwner` mixin); a close/cancel extension must
  participate in the same hold (it is the same gesture, still open) and must
  not release-and-reacquire mid-gesture.
- **Task Card precedent.** `314-task-card-key-model.js`: bare `x` = cancel
  row, `Ctrl+Enter` = apply recommendation, `Ctrl+D` = clear relations,
  input-focus guard (keys return `null` inside text inputs). The successor
  picker cannot copy bare-`x` because its filter input is always focused —
  hence a modifier is genuinely required in Obsidian, and the proposer's
  `Ctrl+X` is the natural modified form of the Task Card `x`.

### 3.3 The Mac Pull-In card (bob-mac-capture, read via `sase repo open`)

- **Card.** `CapturePullInChoiceView.swift` (~996 lines) + `CapturePullInChoice.swift`
  (~1092 lines): full-width sibling of the capture picker, filter bar, context
  line, fixed-height list, footer keycap hints + action buttons. Design fixtures
  assert the documented keyboard contract (line ~887): "Up, Down, Control-N, or
  Control-P moves … Space marks … Command-A marks … Return pulls in … /
  Shift-Return skips … Control-Return pulls in and opens … Escape goes back".
- **Implication.** The Mac already has a two-button + hints pattern and a
  `Shift-Return` skip verb. Close/cancel slot in as two more buttons with
  `⌃X` / `⇧⌃X` equivalents — no `⌘X` (cut), no new modal, height policy
  unchanged (fixed budget from open; filtering never resizes panel).

### 3.4 Close vs Cancel vs Park vs Drop (the four verbs this touches)

| Verb | Symbol | Writer today | Offers? | Successor-picker relevance |
|---|---|---|---|---|
| Close / Done | `[x]` | Ctrl+Enter, `x!`, `!`, complete-labels; tree close + `[completion::]` + retirement + recovery + offers | Yes (managed Done) | **New: close an offer row** |
| Cancel | `[-]` | nav Task Card cancel, `Alt+[` into Cancelled, cancel-labels; Cancel Log + `[-]` + `[cancelled::]` + recovery, never offers | No (recover only) | **New: cancel an offer row** |
| Park | `[/]` | `x*`, `@route+id!` unlink | Relation rows only | Out of scope; do not add |
| Drop | `x~` | close-line `~<K>` | No | Out of scope; do not add |

Recurring guard: capture `!` refuses `[repeat::]`/`(repeat::)`/`🔁` lines;
nav cancel reroutes recurring tasks to Obsidian Tasks (`240-cancel-and-lanes.js`).
Close/cancel-from-successor must reuse those exact guards, not reimplement them.

---

## 4. CLI and docs constraints (memory reads)

- **`cli_rules.md`** (read 2026-11-05): no new subcommand under `bob capture`
  (free-text swallows it); `capture-*` protocol names are frozen siblings that
  grow only additively; every public long option gets a short alias; never
  rename/remove a command. Consequence: the CLI surface for this feature is
  **flags on existing commands** (`--pull-in` family) and **additive JSON**,
  not `bob capture close-successors` or `bob task close`.
- **`docs.md`** (read 2026-11-05): behavior change → contract/reference page
  (`docs/task-dependencies.md` §12.x) plus only the guide steps made
  incorrect; new hotkey → plugin reference; design decision → decision record;
  `just docs-check` gates. Consequence: this feature needs a §12.x contract
  delta, plugin-reference hotkey rows, and a decision record — not a new guide.
- **`decisions:mac-capture-is-a-thin-client`** (read 2026-11-05): bob-cli owns
  capture grammar, completion, preview, mutation; Mac renders. Consequence:
  the close/cancel *writers* and their JSON live in bob-cli; the Mac only
  decodes `close_keys`/`cancel_keys`-style additive fields with
  `decodeIfPresent` and submits them on the one aggregate `bob capture` call.

---

## 5. Keymap analysis: why scoped `Ctrl+X` / `Ctrl+Shift+X` (with buttons)

### 5.1 Candidates considered

| Chord (Obsidian) | Mnemonic | Conflicts | Verdict |
|---|---|---|---|
| `Ctrl+X` / `Ctrl+Shift+X` (proposed) | Modified Task-Card `x` | Cut when filter text selected; `Ctrl+X` taken in Pomodoro-entry picker (different modal, safe); user `hotkeys.json` may bind `Ctrl+Shift+X` globally | **Accept, scoped to successor modal + buttons primary.** Precedent for hijacking editing keys in pickers (`Ctrl+A` already means mark-group, not select-all). Mitigate cut by documenting, keeping `Esc`/click paths, and never hijacking outside the modal. |
| Bare `x` / `X` | Task Card parity | Types into filter; unavailable | Reject. |
| `Alt+X` / `Alt+Shift+X` | — | `Opt+X` types `≈` on macOS US layout; non-portable | Reject as primary (acceptable as *additional* Linux/Windows alias only if cheap; not recommended). |
| `Ctrl+D` / `Ctrl+Shift+D` | — | `Ctrl+D` = clear-relations on Task Card, delete-char in Emacs bindings; confusing across modals | Reject. |
| `Ctrl+Enter` for close | — | Free in successor modal today, but `Ctrl+Enter` *means* close/apply across the vault; using it to close an *offer* while `Enter` pulls in invites the worst mis-press in the set (pull vs close differ by one modifier under time pressure) | Reject for close. Reserve `Ctrl+Enter` semantics: do not blur pull vs terminate. |
| `Delete`/`Backspace` | — | Destructive without modifier; filter-editing hazard | Reject. |

### 5.2 Why scoping resolves the apparent `Ctrl+X` collision

The `Ctrl+X`-merges-Pomodoro binding lives in `PomodoroEntryMovePickerModal`,
not in `SuccessorOfferPickerModal` and not in the base class. Two modals never
coexist (one `activeSuccessorPicker` / one move session at a time; both tear
down on unload via `closeSuccessorPickerForUnload`-style paths). A chord
scoped to `SuccessorOfferPickerModal#handleKeydown` therefore cannot fire the
merge path. State this in the contract so a future base-class refactor does
not promote it: "**`Ctrl+X` close is a successor-picker-modal binding, never a
base `FilteredPickerModal` binding.**"

### 5.3 Mac key equivalents

macOS reserves `⌘X`/`⇧⌘X` for cut; `⌃X`/`⇧⌃X` (Control, not Command) are free
of the clipboard and match the existing card's `Control-Return` / `Control-N/P`
vocabulary. Render hints as `⌃X close` · `⇧⌃X cancel`, with real buttons for
pointer/touch and VoiceOver labels ("Close highlighted offers", "Cancel
highlighted offers"). Do not mirror the exact `Ctrl` glyph; follow the card's
existing `Control-` wording in fixtures (`CapturePullInChoiceView.swift` ~L887).

### 5.4 Discoverability and beauty (both clients)

- Obsidian footer becomes: `Tab` toggle-and-move · `Ctrl+A` mark group ·
  `↵` pull in · **`Ctrl+X` close · `Ctrl+Shift+X` cancel** · `Esc` none (+
  `Ctrl+Shift+Enter` retarget when available). Row affordance: on highlight,
  show two muted inline actions (`Close ⌃X` / `Cancel ⇧⌃X`) at the row's
  trailing edge; muted rows show why they are ineligible on hover/focus instead
  of the actions. After commit, the existing receipt/notice line gains one
  clause: `· closed 2 "…" · cancelled 1 "…"` (Obsidian `successorNotice` v3
  additive; Mac choice-result summary additive).
- Filter-input safety: when the filter has a non-collapsed selection, `Ctrl+X`
  still closes (picker semantics win, consistent with `Ctrl+A` precedent) —
  but the footer hint and an empty-filter onboarding caption must say so, and
  the Mac filter (which uses `⌘X` for cut) is unaffected because its chords
  use Control.

---

## 6. Reliability design (the hard part)

### 6.1 Target resolution: marked else highlighted, selectable only

Reuse the picker's existing `prospectiveKeys()` rule verbatim: marked keys
win; otherwise the highlighted row; `Esc`/empty selection = none. Close/cancel
apply to the same resolved set the `Enter` path would pull. Eligibility =
`row.selectable` (today's `allowed` set in `pickSuccessorOffers` settle).
Ineligible targets (still-blocked with `reason`, scheduled-later, hidden
fold-ins, already-planned, sub-project-waiting) are never closable from the
picker — the button/key is a no-op with the row's existing `mutedReason`
notice, exactly as `Enter` on a muted row is a no-op today.

### 6.2 The write path (one atomic staged batch)

Conceptually one gesture, one batch, in this order against the staged snapshot:

1. **Validate the predecessor gesture** exactly as today (anchors, C set,
   destinations). Nothing about offers changes the predecessor plan.
2. **Resolve close/cancel targets** to task identities (note path + block id),
   refresh each target's live line (same preimage check the destination
   retarget path uses: `refreshSuccessorPickerTaskContext`-style re-read; any
   changed/missing source aborts *that row* with a notice, never the gesture).
3. **Run the existing writers per row**: close rows through the shared
   task-completion engine (tree close incl. embedded `![[…]]` recursion with
   Blocked/recurring/unknown left open + reported; `[completion::]` only with
   the global-filter tag; ledger retirement to running-else-last-completed
   entry; dependent recovery); cancel rows through the existing cancel writer
   (Cancel Log with reason prompt? — see §6.4; `[-]` + `[cancelled::]`;
   `#hide` removal on emptied projects; recovery only).
4. **Apply the predecessor's picks** (links + Next + `[fresh::]`, clearing
   `[unblocked::]`/`[keeps::]` on picked existing tasks) at §12.3 anchors.
5. **Commit atomically.** Any failed row rolls the whole gesture back (the
   capture batch rule: "any failure rolls the whole batch back",
   `docs/capture.md`). CLI dry-run reports `would close` / `would cancel`
   rows without writing, mirroring `would link` / `would surface`.

### 6.3 No cascade in the same gesture (ADJ-3, normative)

Closing/cancelling an offer row **recovers** (rank fix, `#prj_is_blocked`
strip, `[unblocked::]` per WRITE rule, `#hide` removal) and **stops**. It does
not compute new offers, open a nested picker, or consume `--pull-in` slots for
second-order dependents. Rationale: (a) the decisions forbid auto-linking —
a second picker that nobody asked for is auto-link pressure with extra steps;
(b) the walk-hold machinery (`reviewSuccessorGestureOwner`) assumes one
picker per gesture; (c) the JSON/CLI contract stays one-level (`offers` in,
`picks`+`closes`+`cancels` out). Deferred dependents are not lost: they carry
`[unblocked::]` and return as TICKLER tomorrow, or immediately as NEW if
unstamped — the same fate as unpicked rows today. Document one sentence in
§12: "**Terminal actions on offers recover; they do not offer.**"

### 6.4 Cancel reason: prompt or not?

Nav cancel today asks for a reason (Task Card cancel stage; `240-cancel-and-lanes.js`
`planTaskCancelBatch` requires `dateText`, reasons optional-per-config). A
picker-speed cancel must not open a second modal per row. Recommendation: **no
per-row reason prompt in the picker**; cancelled rows get the standard
undated-reason-free Cancel Log entry (or the configured default), and the
receipt names them so Bryan can annotate afterward. The full Task Card cancel
(with reason) remains one click away via the row's note link. This trades a
small log-quality loss for keeping the gesture atomic — call it out in the
decision record.

### 6.5 Guards that must be reused, not reinvented

- Recurring lines: refuse with the existing teaching notices (complete in
  Obsidian Tasks; cancel via Tasks), never silently skip.
- Custom open statuses (`[>]` etc.): `is_completable_status` (`src/native/task_complete/mod.rs`)
  gates closes; cancel gates on the cancel writer's open-task set.
- Already-Done/Cancelled between picker open and commit: revalidation turns
  the row into `already_done`-style no-write + notice (capture `!` precedent:
  `action: "already_done"`, nothing written).
- Block-id-less rows: closable/cancellable (no link needed); only *pull-in*
  needs `^id` (`needsBlockId` stays a pull-in-only affordance).
- `plan.link_unblocked: false` kills *linking*, not closing: with linking off,
  `Enter` degrades to recovery-only while `Ctrl+X`/cancel still terminate —
  say so explicitly, because operators will ask.

### 6.6 Undo and idempotency

Obsidian file writes in this family are single-undo per gesture (decay card:
"Step and Drop also log … in the same undo as the task change"). Keep that:
predecessor close + picks + offer closes/cancels = **one undo stop** in
Obsidian, one aggregate `bob capture` transaction in CLI/Mac. Re-pressing the
same chord after commit is a no-op with notice (rows are no longer selectable).

---

## 7. What changes where (inventory)

| Layer | Change | Notes |
|---|---|---|
| `docs/task-dependencies.md` §12 (+§12.13/§12.14 deltas) | Offer-row terminal actions: eligibility, target rule, write order, no-cascade rule, dry-run copy, vectors | Contract first; SO vectors gain close/cancel cases |
| `src/native/task_complete/successors.rs` + `verdicts.rs` + `output.rs` | `SuccessorSelection` gains `close_keys`/`cancel_keys`; planner validates keys against selectable set; output adds `closed[]`/`cancelled[]` rows + `would close/cancel` dry-run | No new `OfferGroup`; no grammar change |
| `bob capture` CLI (`-p/--pull-in` + JSON) | Additive selection syntax for close/cancel keys (e.g. `-p` stays pull; new `--close`/`--cancel` or `-p` `x:`/`c:` prefixes — bikeshed at plan time, additive either way); JSON `successors.{picks,closes,cancels}` | `cli_rules.md`: flags only, short aliases, additive JSON |
| Obsidian `206-successor-picker-modal.js` + `206a-…-model.js` | Scoped `Ctrl+X`/`Ctrl+Shift+X` in `SuccessorOfferPickerModal#handleKeydown` only; row buttons; footer hints; settle result `{picks, closeKeys, cancelKeys}` | `api.successors` stays v3 if result shape is additive; otherwise v4 with fallback |
| Obsidian plugin reference | Hotkey rows for the two chords (picker-scoped), updated footer copy | `docs.md` routing: plugin reference |
| Mac `CapturePullInChoice{,.swift}` + `CaptureCore` models | Decode additive `closes`/`cancels`; buttons + `⌃X`/`⇧⌃X`; result submits keys on the one aggregate `bob capture` | Thin-client: no Swift writer |
| Tests | Rust SO vectors; JS picker key tests (marked/highlighted/muted/stale); Mac decoding + fixture contract test; e2e: close-offer recovers-without-offer, cancel-offer never offers | Reuse shared vectors (`docs/task-dependencies.md` §12.12) |
| Decision record | `decisions:` entry for offer-row terminal actions (scope, cascade ban, reasonless picker-cancel, key scoping) | Immutable; link evidence |

Explicitly **not** changing: capture grammar (`!`, `x!`, `x*`), `bob task *`
verbs, `OfferGroup` set, `api.successors` picker trigger conditions, decay
ladder, freshness intervals, `plan.link_unblocked` spelling, global hotkeys.

---

## 8. Recommended concrete contract (for the plan author)

1. **Eligibility.** Any row with a selectable offer `key` in any group
   (`hand_off`, `project`, `project_finished`, `keep_moving`, `relation`,
   `note_pull`) may be closed or cancelled. Folded-count lines and muted rows
   may not.
2. **Targeting.** Marked keys, else highlighted row — identical to `Enter`.
   `Esc` / no-target = none (no writes of any kind, including predecessor
   picks? No — `Esc` today means none *for offers* but the predecessor close
   already happened; keep that: `Esc` abandons offer-side writes only).
3. **Keys.** Obsidian: `Ctrl+X` close, `Ctrl+Shift+X` cancel, handled in
   `SuccessorOfferPickerModal#handleKeydown` before `super`, with
   `preventDefault` + `stopPropagation`, ignored when the modal is not the
   active picker or a retarget sub-picker is open. Mac: `⌃X` / `⇧⌃X` on the
   Pull-In card + buttons. Both: pointer-accessible buttons always; keys never
   the only path (mobile/a11y).
4. **Writes.** Close rows = managed-Done-equivalent write *minus offers*:
   tree close, completion stamp, retirement, recovery. Cancel rows = cancel
   write *minus offers*: Cancel Log (reasonless in picker), `[-]`,
   `[cancelled::]`, recovery. Shared: revalidate-then-write, atomic batch,
   one undo / one transaction, dry-run `would` rows.
5. **No cascade.** Terminal writes recover; they do not offer. Second-order
   dependents return via freshness tiers.
6. **Receipts.** Human output appends `closed N "…"` / `cancelled N "…"` lines
   with the same quoting as `completed` lines; JSON adds additive
   `closed[]`/`cancelled[]` with `key`, `note`, `block_id`, `previous_status`,
   and `recovered` counts; notices append one clause. Older Mac builds ignore
   unknown fields (`decodeIfPresent`) and simply never send the new keys.
7. **Docs.** §12.x "Terminal actions on offers" + §12.13/§12.14 deltas + SO
   vectors + plugin-reference rows + decision record. No guide rewrite beyond
   corrected steps.

---

## 9. Rollout (smallest safe order)

1. **bob-cli contract + engine** (planner validation, writers, output, vectors,
   `just docs-check`). CLI-usable immediately via flags; Obsidian/Mac ignore
   until they upgrade.
2. **Obsidian picker** (modal keys + buttons + settle + notice + reference
   docs + JS tests). Gate on `api.successors` additive-vs-v4 decision; keep
   v3 fallback (older bob = keys hidden, picker behaves as today).
3. **Mac card** (decode + buttons + equivalents + fixtures + Swift tests),
   gated by macOS CI per repo convention (`scripts/dev/macos-ci-check`,
   exact-SHA watch with `/sase_monitor`).
4. **Decision record + changelog-adjacent docs.** (No CHANGELOG/Cargo version
   edits by agents per `decisions:bob-cli-releases-ride-a-daily-train` —
   releases ride the train.)

---

## 10. Open questions for Bryan (non-blocking)

1. **Cancel reasons in the picker: truly reasonless?** (§6.4 recommends yes.)
   If you want reasons, the picker needs a one-line reason field, not a
   second modal — bigger design, do it later.
2. **Should `Ctrl+Shift+X` also work when only *muted* rows are highlighted?**
   Recommend no (notice with `mutedReason`). Confirm.
3. **CLI flag shape:** separate `--close`/`--cancel` flags vs `-p` prefixes?
   Recommend separate flags for readability (`--pull-in` stays pure), but
   either is additive — plan author picks.
4. **Keep-moving groups:** closing a `keep_moving` offer (a leaf project's
   ready task) is allowed under §8.1 — confirm you want terminal verbs there
   too, not pull-only.

---

## 11. Evidence (what was actually read)

- `docs/task-dependencies.md` §12–§12.1 (offer pipeline, triggers, exclusions),
  §12.2 rule, §12.13/§12.14 (picker API/CLI), §12.10/§12.15/§12.18/§12.20
  (groups); `docs/capture.md` (`!` complete execution steps 1–6, `x` close
  grammar, `@route+id!` park, cancel/complete label commits); `docs/decay-ladder.md`
  card keys; `docs/task-merge.md` §3 offers (merge-offer precedent).
- `src/native/task_complete/successors.rs` (planner, `OfferGroup`,
  `SuccessorSelection`, cancel-recovery paths), `mod.rs`
  (`is_completable_status`, `is_recurring_task_line`), `verdicts.rs`.
- `bob-plugins` (via `sase repo open`): `206-successor-picker-modal.js`
  (full 816-line read: footer, `handleKeydown`, `prospectiveKeys`,
  `applySelection`, `pickSuccessorOffers` settle, walk-hold mixin),
  `206a-successor-picker-model.js`, `314-task-card-key-model.js` (bare-`x`
  cancel, input guard), `200-filtered-picker-modals.js` (base vs
  `PomodoroEntryMovePickerModal` `Ctrl+X` merge — the collision that scoping
  resolves), `240-cancel-and-lanes.js` (cancel writer guards),
  `manifest.json` description (picker/notice v2/v3 copy).
- `bob-mac-capture` (via `sase repo open`): `CapturePullInChoiceView.swift`
  (layout/height policy, documented keyboard contract ~L887),
  `CapturePullInChoice.swift` (row/glyph/selection model).
- Memory (via `sase memory read`, audited): `decisions:unblocked-tasks-are-offered`,
  `decisions:task-decay-is-one-ladder`, `decisions:mac-capture-is-a-thin-client`,
  `decisions:unblocked-tasks-resurface-as-ticklers` (linked),
  `glossary:successor-offer`, `glossary:task-successor`, `glossary:task-decay`,
  `glossary:task-freshness`, `cli_rules.md`, `docs.md`.

Peer reports in this swarm were not consulted (per the brief); any convergence
with `__cdx`/`__cld`/`__grk`/`__gem` is independent.

---

*End of report — researcher mus.*
