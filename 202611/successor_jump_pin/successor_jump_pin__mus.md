# Jump successor (`Ctrl+J`) for the successor panel — research report

Researcher: mus · 2026-11-20 · question: add a `<Ctrl+J>` keymap to the successor
panel (Obsidian + capture panel) that marks a single "jump successor" to focus in
Obsidian after the triggering close settles.

TL;DR: yes, build it — but build it **client-side only, as a single orthogonal
slot that never links, never closes, and never touches bob's wire format**, with
`Ctrl+J` toggling jump on the highlighted offer in both hosts, and the jump
running **after** all staged writes settle, resolved against post-write note text.
Override (replace, don't merge) the capture-panel open intent when a jump is set,
exactly as requested. Details and the few requirement adjustments are below.

## 1. What the "successor panel" is today (two hosts, one contract)

There is no single shared component. There are two clients over one offer/key
contract (see `decisions:unblocked-tasks-are-offered` — every would-be link is
offered, nothing preselected, only picked rows link):

**Obsidian — `SuccessorOfferPickerModal` + verdict layer.**

- Picker: `plugins/bob-navigation-hotkeys/src/206-successor-picker-modal.js`
  (model `206a`, copy `206b`, verdicts `206c`, render `206d`).
- Staged close descriptors/normalization:
  `plugins/task-status-cycler/src/089g-successor-offer-close.js`
  (`normalizeSuccessorChoices`), apply:
  `089i-successor-offer-close-apply.js`, integration
  `137a-successor-offer-close-integration.js`.
- Entry: managed Done (`Ctrl+Enter` on task / Task Link, docs in
  `plugins/task-status-cycler/docs/task-status-cycler.md` §§ "Successor offers
  and take-backs") → nav `api.successors` v3/v4 picker.
- Current keys (picker): `Tab` toggle-and-move, `Space` toggle (empty filter),
  `Ctrl+A` mark group, `Enter` pull in / apply, `Ctrl+X` stage Done,
  `Ctrl+Shift+X` stage Cancel + reason, `Ctrl+Shift+Enter` retarget destination,
  `Esc` arm-then-discard verdicts, `Ctrl+N/P` + arrows navigate,
  `Ctrl+[` mirrors `Esc`. Verdicts and marks are **mutually exclusive per row**
  (`successorSetVerdict` deletes the mark; `toggleMark` converts a verdict to a
  mark via `successorConvertVerdictToMark`).
- Footer hints today: `SUCCESSOR_PICKER_FOOTER_HINTS` / `..._VERDICT_HINTS` in
  `206-successor-picker-modal.js`; retarget hint appended only when the
  destination picker exists.

**Mac Capture — in-panel Pull-In / successor card.**

- Card copy/rows: `Sources/CaptureCore/CaptureSuccessorPresentation.swift`,
  `CaptureSuccessorOfferRows.swift`, `CapturePullInChoiceView.swift`.
- Key router: `Sources/BobMacCapture/CaptureKeyCommandRouter.swift`
  `pullInChoiceCommand(...)` — `Space` toggle, `Tab`/`Shift-Tab` toggle-and-move,
  `Cmd+A` mark all, `Ctrl+X` stage Done, `Ctrl+Shift+X` begin Cancel,
  `Return` confirm, `Shift-Return` verdicts-only (skip pull-ins),
  `Ctrl-Return` confirm-and-open, `Esc` cancel, `Ctrl+N/P` + arrows move.
- Spec: `docs/keyboard.md` § "Successor choices" and § "Inbox routing";
  `docs/capture-panel.md`, `docs/task-pickers.md`.
- Decision: Mac Capture is a thin client of bob
  (`decisions:mac-capture-is-a-thin-client`): it renders spans/candidates bob
  returns and submits one `bob capture` call. Successor choice is an in-panel
  step; bob remains the write authority.

**bob-cli (unchanged by this proposal).**

- Offer planning: `src/native/task_complete/successors.rs`
  (`SuccessorInput`, `SuccessorPlan`, `OfferReport`), close eligibility
  `src/native/task_complete/offer_close.rs` (`OfferCloseDescriptor`,
  `OfferCloseAction`), capture successor authoring
  `src/native/capture_complete/successor.rs`.
- Key point: offers are computed at gesture time and never stored; picks link +
  raise to Next + stamp fresh; unpicked rows recover without a link. There is no
  "jump" concept in the planner today, and there does not need to be.

## 2. Critique of the plan as stated

**It is a good idea.** The two motivating uses are real and distinct from
pull-in: (a) "I want this next but I don't want it in today's plan yet — take
me to it so I can prioritize/edit it in place"; (b) "I pulled it in but it
needs edits before it's actionable — land me on it." Both are currently
multi-gesture (close → remember → navigate → find line). A one-key "land me
there after the dust settles" closes that loop at the moment intent is
freshest. It composes rather than competes with the existing offer machinery.

**Adjustments I recommend (all tighten, none remove intent):**

1. **Jump must never imply pick, close, freshness, or lane change.**
   The request already says the jump row "may have any other state" — make that
   a hard invariant: setting jump changes zero plan semantics. This is required
   by `decisions:unblocked-tasks-are-offered` (only picked rows link). A jump
   mark on a row that is otherwise untouched leaves it to recover normally; a
   jump mark on a pulled-in row links it (because it was picked, not because it
   was jumped-to); a jump mark on a Done/Cancel verdict row still closes it.
   Say this in the copy ("jump is where you land, not what happens") or users
   will reasonably fear `Ctrl+J` does something to the task.

2. **Single slot, last-write-wins, `Ctrl+J` toggles.** The request says single
   — keep it, and define the toggle precisely: `Ctrl+J` on the highlighted
   offer sets jump to that row; pressing again on the same row clears it;
   pressing on a different row moves it. Never two jump marks. This falls out
   of "jump to the appropriate file" (singular) and keeps the footer/status
   trivially renderable.

3. **Jump survives verdict/pick changes but dies with the row's eligibility.**
   Because jump is orthogonal, toggling pick/verdict on the jump row must not
   clear jump (unlike the verdict↔mark exclusivity). But if the row becomes
   ineligible/disappears on re-render (filter, refresh, identity change), clear
   jump rather than carry a stale key. Stale jumps that land on the wrong line
   are the #1 reliability hazard; fail closed (no jump) over best-effort.

4. **Escape discards the jump with everything else.** The Mac card already uses
   two-stage Esc for verdicts; Obsidian arms Esc then discards. Jump is staged
   state like verdicts — first Esc arms (and should announce "jump discarded"
   only if one was set? no — keep it silent, it discards with the rest),
   second Esc drops it. Do not make jump "sticky across cancel": a canceled
   panel must never teleport the user on a later unrelated write.

5. **"Override `<Cmd+Enter>`" means replace, and only the open, never the
   write.** In the capture panel `Ctrl+Return`/`Cmd+Return` both mean
   "capture and open Bob's reported notes" (`docs/keyboard.md` editor table).
   When a jump is set, the jump replaces `open_notes` — it does not add a
   second window hop, and it never changes what was captured. If the jump
   target happens to be inside `open_notes`, dedupe to one landing. If the jump
   resolution fails post-write, fall back to the original open intent (or
   nothing, if the submit was plain `Return`) and say so in the status line —
   never strand the user with neither.

6. **Don't add a bob wire-format field in v1.** Tempting: `jump_key` next to
   `picks`/`closes` so bob returns the resolved line. Resist it. Both hosts can
   resolve the landing themselves after their own write pass (Obsidian has the
   final note text; Mac has bob's response + `open_notes` machinery and the
   existing `obsidian://bob-goto-task` URL). A protocol field buys a three-repo
   flag day (bob-cli + both clients + capability fallback) for zero planning
   value, because jump needs no planner input. Keep v1 pure client state; revisit
   only if CLI `bob capture` users need the same feature non-interactively
   (they don't — there is no panel there).

7. **Scope the key to the panel, not the editor.** `Ctrl+J` in the Mac editor
   today inserts an indentation-aware `- ` row (or newline in template drafts;
   `docs/keyboard.md` editor table). That binding stays. `Ctrl+J` as jump lives
   only while the successor/pull-in card is open (card owns the key while
   open, including when its filter is focused — see §4). Same in Obsidian: the
   modal owns it; it is not a global hotkey and needs no Command-ID.

## 3. Why `Ctrl+J` is the right key (and the conflicts that aren't)

- **Free in both panels.** Obsidian successor modal handles `Enter` (with
  `Ctrl`/`Meta` explicitly swallowed), `Tab`, `Space`, `Ctrl+A`, `Ctrl+X` /
  `Ctrl+Shift+X`, `Ctrl+Shift+Enter`, `Ctrl+N/P`, `Ctrl+[`, `Esc` — `Ctrl+J`
  hits none of those branches and currently falls to the base picker (which
  ignores it). Mac `pullInChoiceCommand` switches on `return / escape / [ /
  arrows / n / p / space / tab / a / x / t / backslash` — there is no `case
  .j`; adding `case KeyCode.j: modifiers == .control → toggleJump` collides
  with nothing (note `t` is `Ctrl+T → .consumeKey`; `j` is untouched).
- **Mnemonic + family.** J = jump; sits beside the existing `Ctrl+N/P`
  navigation family and the vim-adjacent `j` motion. `Cmd+J` (join calendar
  event) is a different modifier and unaffected; the request is explicitly
  control, not command.
- **No clipboard / IME hazard.** Unlike `Ctrl+X` (which needed a Linux-cut
  exception, `successorVerdictIsLinuxCut`), `Ctrl+J` has no platform kill/yank
  meaning in these panels and no text to cut while the filter is empty-or-not
  (it must `preventDefault` + `stopPropagation` + ignore `repeat`/`isComposing`,
  mirroring `handleVerdictKey`'s guards).
- **Repeat + held-key safety.** Ignore `event.repeat` (Mac: `isRepeat →
  .consumeKey`). Single toggle per press; no auto-repeat walk.
- **Alternatives considered.** `J` alone would steal filter typing; `Alt+J`
  conflicts with Mac word-motion chords nearby (`Ctrl+Shift+H/L` word jumps)
  and is undiscoverable; `Ctrl+G`-style chords are taken (`Ctrl+G,U` case
  toggle); `Cmd+J` is taken (join event). `Ctrl+J` is the only free,
  mnemonic, single-press option in both panels.

## 4. Interaction design (make it intuitive and beautiful)

**Mark affordance.** One jump glyph per row, shown only on the jump row:
suggest `⇢ jump` pill (or `⤵ jump`; avoid `★`/`☑` which already mean mark,
avoid `🍅`/`⛓️` domain glyphs). Row template: existing `☑/□` mark box stays
left; jump pill floats right alongside the existing `→ NAME` destination
override and verdict chips (`206d-successor-picker-verdict-render`). In the Mac
card, same right-aligned pill in the offer row; selected-row highlight unchanged.

**Footer + status.** Append one hint to both footers:
Obsidian `SUCCESSOR_PICKER_FOOTER_HINTS` → `{ keys: ["Ctrl+J"], label: "jump to" }`
(and the verdict variant); Mac successor footer → "Control-J marks the jump
target". On set: status line `Will jump to ‹task text› after close`
(truncate like other consequence lines); on move: update; on clear: restore the
highlight default. Keep the existing `Tab`/`Enter`/`Ctrl+X` hints untouched —
jump is additive, last in the list.

**Toggle rules (both hosts).**

- `Ctrl+J` on highlighted offer, row selectable → set/move jump; same row →
  clear. Render all (Obsidian) / announce (Mac).
- Works regardless of the row's mark/verdict state; does not alter them.
- Filter text preserved; caret stays in filter (Obsidian) — jump never steals
  focus. In the Mac card with `pullInReasonFocused`, `Ctrl+J` is inert (like
  all card keys while the cancel-reason field owns input).
- `Esc` (both stages), successful apply, or panel cancel clears the slot.
- Non-selectable rows (folded counts, ineligible closes, already-parked
  caveats): refuse with the row's existing refusal copy + shake (Obsidian
  `successorShakeRow` pattern), no jump set.

**What "focus the task" means.** Open the note (existing tab when open —
  never duplicate), place the caret at the task line's first non-bullet
  content (or line start when the line shape is unknown), scroll into view
  (centered `zz`-style when the host supports it, cf. `170-open-task-jump.js`
  `focusTaskAnchor` / `EditorView.scrollIntoView`), ensure editing focus. If
  the note is already active, just move the caret. Never change vim mode,
  never start a Pomodoro, never link anything.

## 5. Reliability: identity, ordering, and the capture override

**Resolve after writes, never before.** The jump key is the offer `key`
(`path#^blockID` or `path@digest~n` — the same key used for picks/closes).
Between staging and landing, the line may move: pull-in inserts Task Links,
verdict closes rewrite the row, freshness stamps edit it, block IDs get minted
(`plan.link_unblocked` missing-ID path). So:

1. Apply picks/verdicts exactly as today (Obsidian: vault writes with
   preimage checks in `089i`; Mac: `bob capture` submit).
2. Re-read the target note's **post-write** text.
3. Refind the task: prefer block ID (`^id` — stable across stamp/link edits),
   else digest + fuzzy line match, else clamp-to-nearest with a "landed near
   line N" notice. Obsidian already implements this shape in
   `675-plugin-goto-task-uri.js` (`refindGoToTaskLine`, `found.source ===
   "clamped"` notice + `focusTaskAnchor`); Mac has the same via
   `ObsidianOpenURL.taskGotoURL(path:line:ref:block:)` +
   `RefsPanelModel` fallback. Reuse those paths verbatim — do not invent a new
   resolver.
4. If resolution fails (note deleted/renamed mid-flight, ID ambiguous,
   `overlayValid === false`): **do not jump**. Mac: fall back to the pre-jump
   open intent; Obsidian: stay where the user was + plain notice. Log the key.

**Ordering with the close.** "After the user completes the task close that
triggered the successor panel" = after the pick/verdict write pass commits
(Obsidian `successorOfferCloseApply` / Mac capture success). The predecessor's
own close already happened to produce the offers; the jump must wait for the
successor writes, because the jump target may be one of the rows just written.

**Capture override semantics (as requested).** Submit flavor is known at
submit time (`submit` vs `submitAndOpen`). If jump set: Mac suppresses the
`open_notes` open and instead dispatches one `obsidian://bob-goto-task` for the
jump target. Announce in status: "Jumped to ‹task› instead of opening N
notes" (keeps the override legible). Telemetry/open-logging should record
`jump_suppressed_open_notes: true` where open outcomes are logged
(`CaptureTodayPomodoroGoto` / `NotificationService` paths), so a "where did my
notes go" report is answerable.

**New-task edge.** Offers never include the draft's own new tasks as jumpable
rows in v1 (jump targets are existing offer rows). If a future iteration offers
jump on a just-created task, resolve via the creation receipt (path + minted
block ID), not the draft line number.

## 6. What not to build (rejected alternatives)

- **Jump-as-pick (auto-pull-in the jump target).** Violates the offered-never-
  linked rule and destroys use-case (a) (prioritize without pulling in).
- **Multi-jump / jump queue.** No coherent "after" — the panel settles once;
  a queue is a tray, and trays were rejected for offers (`decisions:
  unblocked-tasks-are-offered`).
- **Bob-side `jump_key` field.** Three-repo flag day, no planner value (§2.6).
  Client state + existing goto URLs cover it.
- **Jump before writes settle (optimistic jump).** Races the write pass; lands
  on preimage lines that the pass then moves. The 350 ms enter guard
  (`SUCCESSOR_PICKER_ENTER_GUARD_MS`) already exists because gesture timing is
  delicate — don't add a second race.
- **Global `Ctrl+J` hotkey.** Unneeded surface; panel-scoped is discoverable
  (footer hint at point of use) and conflict-free.

## 7. Implementation sketch (pointers, no code)

**Obsidian (`bob-plugins`).**

- `206-successor-picker-modal.js`: add `this.jumpKey = null`; handle
  `Ctrl+J` (no `Meta`/`Alt`/`Shift`, ignore repeat/composing, `preventDefault`
  + `stopPropagation`) before the `Enter` branch; toggle + `renderAll`.
- `206c-successor-picker-verdicts.js`: jump setter enforces single-slot and
  row-selectability; `successorConvertVerdictToMark` / `successorSetVerdict`
  leave `jumpKey` alone; `handleEscapeKey` + `close()` clear it.
- `206d-successor-picker-verdict-render.js`: jump pill + status-line copy.
- Settle path (`collectPicks`/apply caller, `137a` integration): after the
  apply promise resolves, if `jumpKey`, refind post-write line and call the
  existing `focusTaskAnchor`-family helper (same helper `handleGoToTaskUri`
  uses). Clear slot in `finally`.
- Docs: `docs/task-status-cycler.md` successor § + `docs/bob-navigation-
  hotkeys.md` key table; footer hint arrays are the spec.

**Mac Capture (`bob-mac-capture`).**

- `CaptureKeyCommandRouter.swift`: `case toggleJumpTarget` (or
  `markJumpOfferAt`); in `pullInChoiceCommand`, `case KeyCode.j: modifiers ==
  .control && !isRepeat → .toggleJumpTarget` (return `.consumeKey` on repeat;
  `nil` when `reasonFocused`). Mirror `Ctrl+[`→ cancel conventions for Esc.
- `CapturePullInChoiceView.swift` + `CaptureSuccessorPresentation.swift`:
  single `jumpOfferID` slot, pill UI, footer hint, status text; confirm paths
  (`confirmPullInChoice` / `confirmPullInChoiceAndOpen`) carry the slot to the
  post-submit step, which replaces `open_notes` dispatch with one
  `ObsidianOpenURL.taskGotoURL` on success.
- `docs/keyboard.md` successor table + `docs/task-pickers.md` pull-in card:
  one row for `Control-J`.

**bob-cli.** No change in v1. If a later CLI-surface need appears, the honest
extension is a client-ignored `jump_key` echo in `OfferReport` — not planning
input — and it is not needed for this feature.

## 8. Test plan (both hosts)

- Toggle: set → pill appears + status; same-row `Ctrl+J` clears; other-row
  moves; only one pill ever.
- Orthogonality: jump + pull-in mark co-exist; jump + Done verdict co-exist;
  apply links/closes exactly as without jump (existing verdict/pick suites
  stay green unmodified).
- Esc: armed-Esc keeps jump visible; second Esc clears jump with verdicts and
  no navigation happens.
- Landing: pulled-in target (line moved by link insert), verdict-closed
  target (row rewritten), untouched target (recover-only) — all land on the
  right line post-write via block-ID refind; simulated concurrent edit →
  no-jump + notice, writes untouched.
- Capture: `Return`+jump → jump, no notes opened; `Ctrl/Cmd+Return`+jump →
  jump replaces `open_notes` + status names the suppression; jump-resolution
  failure → falls back to original open intent.
- A11y/keyboard: footer hint visible, `Ctrl+J` announced, repeat swallowed,
  IME composing ignored, filter caret unmoved, Linux `Ctrl+X`-cut behavior
  unchanged.

## 9. Open questions for Bryan (non-blocking)

1. Pill glyph: `⇢ jump` vs `⤵ jump` — I recommend `⇢` (reads as "go there",
   distinct from `→ NAME` destination arrows by carrying the word "jump").
2. Should `Shift-Return` (verdicts-only) + jump still jump? I say yes — jump
   is orthogonal to pull-ins, and verdicts-only + jump ("close these, take me
   to that") is a coherent gesture. If you disagree, the one-line rule is
   "jump requires no skip flag."
3. Confirm no global `Ctrl+J` meaning you rely on in Obsidian vim mode while a
   modal is open — research found none, but your hands are the authority.

## 10. Recommended solution (v1)

Ship a **client-only, single-slot, toggle `Ctrl+J`** in both successor
surfaces, resolving the landing post-write through the existing goto-task
machinery and replacing (not merging with) the capture open intent when set.
No bob-cli change, no protocol version bump, no new global hotkey. It is
intuitive (`J` = jump, footer-hinted at point of use), reliable (post-write
block-ID refind, fail-closed), and beautiful (one pill, one status line, zero
changes to existing rows/hints). The only contract the two clients share is
the sentence: *jump is where you land, never what happens.*
