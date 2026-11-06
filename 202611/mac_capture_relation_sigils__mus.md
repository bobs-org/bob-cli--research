# Mac Capture task-relation sigils (`~` / `=` / `-`): research and recommendation

Researcher: mus (`__mus`). Date: 2026-11-06. Scope: the four requested
relation-sigil changes in Bob Mac Capture, against the current `bob-cli`
capture grammar and the Mac app's editor / picker / label-card code.

Related vocabulary: `sase memory read glossary:task-relation` (directed,
optionally labelled edge authored on the source task's `LINKS:` line, mirrored
on the target's generated `LINKED FROM:` line; never blocks, never counts as a
Pomodoro Task Link), `glossary:capture` (the app submits the whole draft as one
`bob capture` call; live preview is `bob capture --dry-run`), and
`decisions:relation-card-tab-accepts-ctrl-d-hides`,
`decisions:capture-sigils-say-where-what-how`,
`decisions:relation-label-hide-is-suggestions-only`,
`decisions:relation-label-rename-rewrites-history`.
Governing thin-client rule: `decisions:mac-capture-is-a-thin-client` — the app
renders spans/candidates/previews `bob` returns and never invents grammar.

## TL;DR recommendation

Do all four changes, with three adjustments (below). In one sentence: retire the
bare `-` → `~` alias and replace it with a bare `=` → `~` alias; add a
post-token direction flip (`~` / `=` after a complete `~note:id` / `~~note:id`
token flips the sigil in place, both directions); give `=` a fast `==` escape
everywhere it aliases; and add `~` / `=` direction flip to the relation-label
card with a guard so `=` only flips when the label field cannot legally
contain it.

The rest of this note justifies that sentence, lists the exact code touch
points, and gives acceptance criteria.

## Current state (what exists today)

### bob-cli grammar: `~` / `~~` are the only stored syntax

- `docs/task-relations.md` §§LP/LD: `~note:block-id[|label]` links out,
  `~~note:block-id[|label]` links back. `scan_line_relations` in
  `src/native/capture_language/relations.rs` classifies `Complete`,
  `PartialTarget` (bare `~` / `~~`, `~query`, `~note:`), `PartialLabel`
  (`~note:id|`), `Invalid`, and `Escaped` (`\~`). Token-start rule
  (`is_token_start` — whitespace before), wikilink/backtick guards
  (`protected_ranges`), strike guards (`~~old~~`, `~~~x:y`, `~/path`, `~5m`
  stay literal), `token_end_at` (token runs to whitespace).
- `src/native/capture_language/completion.rs` (`relation_completion_field_at`,
  `relation_label_completion_field_at`): a cursor inside a complete or partial
  relation target yields `CompletionContext::RelationTo` / `RelationFrom` with
  `replacement: (start, end)`; a cursor after `|` yields `RelationLabel`.
- `bob capture` / `bob capture-parse` keep literal text: the `-` / `=` assists
  are editor-only `capture-rewrite` rules, never grammar (see
  `docs/capture.md` "Sigil alias" and `docs/reference/cli/capture-rewrite.md").
- `=` already has many whole-item / suffix meanings that are all
  position-locked: whole-item `=` / `=<X>` start (`PomodoroStart`),
  `=*` merge, `=/` split, `x=` past, `@route:id=x…` / `^route:id=x…` link suffix,
  `=~<K>` / `x~<K>` drop lists, `~<K>` in `x[…]` closes. None of them is "after
  a space in the middle of prose", which is why the proposal's collision claim
  is nearly right (see §1 for the two real exceptions).

### `capture-rewrite expand_sigil_alias` (the alias authority)

`src/native/capture_language/rewrite.rs`:

- `expand_sigil_alias` dispatches on the byte before `--cursor`: `"-"` →
  `expand_past_segment_dash_alias` (`x=-` → `x=~`, `x=~-` → `x=~~`) else
  `expand_relation_dash_alias`; `"="` → `expand_relation_flip_alias`;
  `"\\"` / `"/"` → `expand_hash_alias`; `"."` / `";"` / `","` → block-ID /
  parent-task aliases.
- `expand_relation_dash_alias` (line ~308): `-` after a space/tab becomes `~`
  only where the swapped candidate opens an empty `RelationTo` at exactly
  `(start, cursor)`. Guards: `relation_dash_position_ok` (space/tab before; not
  at line/bullet-body start; not glued; not after another `-`; odd-backtick
  guard), plus `wikilink_claims` veto.
- `expand_relation_flip_alias` (line ~388): `=` right after a bare `~` that
  opens Links To turns the pair into `~~` (`Fix it ~=` → `Fix it ~~`), checked
  against an empty `RelationFrom` at `(start-1, cursor)`; `=` right after a `-`
  that would alias `~` turns the pair into `~~` via
  `finish_relation_flip_dash_alias` (`Fix it -=` → `Fix it ~~`). Everywhere else
  `=` stays literal, explicitly including after `~~` and inside wikilinks. The
  `~~` + `=` early return (`start >= 2 && bytes[start-2] == b'~'`) is the guard
  that proposal §2 must relax in a controlled way.
- Help text (`src/native/capture_rewrite.rs`, `docs/capture.md` "Sigil alias",
  `docs/reference/cli/capture-rewrite.md`): documents all of the above with the
  `Fix it -=` / `Fix it ~=` examples and the "without `--cursor` this rule is
  skipped" note.

### Mac app: three cooperating mechanisms

Editor (`Sources/BobMacCapture/CapturePanelModel.swift`,
`Sources/BobMacCapture/CapturePanelController.swift`,
`Sources/BobMacCapture/CaptureKeyCommandRouter.swift`):

- Key-down records a `pendingSeparatorToggleIntent`
  (`noteSeparatorToggleIntent`, `noteSeparatorToggleIntentIfEligible`) for
  `: ^ + | , . ; \ / - =`, with the `=` gate requiring the previous char to be
  `~` or `-` (`CapturePanelController.swift` ~1119-1140). The rewrite reply
  (`applyNativeRewrite`, ~15600+) arms one-shot state:
  `CaptureHashAliasArm` (`\` / `/` → `#`),
  `CaptureRelationDashArm` (`-` → `~`; struct at `CapturePanelModel.swift` ~45),
  `CaptureRelationFlipAliasOpen` (`~=` → `~~` or `-=` → `~~`; struct at ~57).
- Dash escape today: while `relationDashLiteralArm` is armed and the picker is
  still an empty `.linksTo` on the same draft, Space restores `"- "`, a second
  `-` restores `"--"`, Escape restores `"-"` (`restoreRelationDashLiteral`,
  `relationDashRestoreCommand`, `CaptureKeyCommandRouter.swift` ~1214+). Undo
  after a restore returns to the post-key `~` draft. Hash escape: fast second
  press replaces `#` with the literal key (`replaceHashAliasWithLiteralKey`);
  before Bob answers, `noteHashAliasBeforeReply` / `HashAliasProbe` re-asks
  about the first draft and deletes the extra key only when Bob says the first
  would have become `#`. There is currently no `=` escape; `=` handling is
  one-shot flip-only.
- Picker-open race: `relationDashLiteralArm` / `relationFlipAliasOpen` let the
  still-matching empty Links To / Linked From picker open even when a
  caret-selection analysis beats the edit-triggered request
  (`CapturePanelModel.swift` ~6940-6980).

Relation picker (`Sources/CaptureCore/CapturePickerPresentation.swift`,
`Sources/CaptureCore/CaptureRelationshipCopy.swift`,
`Sources/CaptureCore/DependencyPickerPresentation.swift`):

- `~` opens Links To (`relation_to`, scope `~`); `~~` opens Linked From
  (`relation_from`, scope `~~`). Headers, action line
  (`↩ link · ⇧↩ link with a relation · ~ or = flips direction`), footer
  (`~ Flip direction`), hints
  (`tilde or equals flips direction, Escape cancels`), and
  `docs/relationship-pickers.md` ("Typing `~` anywhere in the filter
  live-flips … Typing `=` anywhere in the filter flips exactly like `~`")
  all agree after commits `591e4ed` (dash aliases) and `3ba25d6` (flip with `=`
  anywhere in filter).
- `flipRelationDirection` (`CapturePanelModel.swift` ~8897) inserts/removes one
  `~` at the sigil, keeps the picker open with the filter untouched, never
  suppresses auto-open, and lets analysis live-flip `relation_to` ↔
  `relation_from`. `removePickerTrigger` on empty `~~` flips back by removing
  one tilde. `CaptureKeyCommandRouter.swift` ~1137 routes `~` / `=` in a
  relation filter to `.flipRelationDirection` (repeat → consume).

Relation-label card (`Sources/BobMacCapture/CapturePanelView.swift`
`RelationLabelPromptCard`, `Sources/BobMacCapture/RelationLabelField.swift`,
`CapturePanelModel.swift` `CaptureRelationLabelPromptState` at ~280):

- State: `draftSnapshot`, `tokenRange` (`~note:id` without `|label`),
  `labelRange`, `direction`, `ownerText` / `targetText`, `restoreCursor`,
  `returnPicker`, `authoredLabel`, `suggestions` / `catalog`, `selectedKey`,
  `showHidden`, `oneOff`, `hiddenRows`, `ghosts`, `rename`, `isSaving`, plus
  `relationCancel` / `relationComplete` / `relationSuccessor` verdicts.
- Sentence pill (`relationLabelSentenceSource` / `Target`) already renders
  direction; footer (`relationLabelFooterItems` ~11988) teaches `↩ ⌃D ⌃H esc`
  but has no direction key. Router (`relationLabelPromptCommand` ~918+) handles
  Tab / arrows / Ctrl+D / Ctrl+H / Backspace / rename keys, but `~` / `=`
  fall through to the AppKit field as label text. No flip exists here today.
- Critical label-charset fact (`src/native/task_relations/label.rs`):
  `FORBIDDEN_CHARS` includes `~` (plus `[ ] ( ) " \ | • *`), while `=` is
  allowed. So `~` can never be legal label content, but `=` can (e.g. a label
  like `a=b`). Any label-card flip must respect that asymmetry.

Docs: `docs/capture-panel.md`, `docs/keyboard.md` (notably the `; - = \ or /`
  table rows and the "Relation pickers … treat `~` or `=` anywhere in the
  filter as the live direction flip" paragraph), `docs/protocol.md`,
  `docs/relationship-pickers.md`, `docs/task-relations.md` (CLI-side contract).

## Proposal-by-proposal analysis

### 1. Make `=` the only alias for `~` (retire the `-` alias)

What the request means in code terms: today `-` (after space/tab) aliases `~`
(`expand_relation_dash_alias` + `CaptureRelationDashArm` + dash-restore keys),
while `=` only flips (`~=` → `~~`, `-=` → `~~`). The request is to add a bare
`=` → `~` alias in exactly the positions where `-` → `~` fires today, and then
remove the `-` path. Verdict: yes, with one guard adjustment.

Why `=` is safer than `-`:

- `-` after a space is ordinary prose. `Fix it - call mom`, em-dash-adjacent
  typing, `- 2` list-ish starts, and `--` shift/adjust prefixes all begin with
  exactly the keystroke the alias hijacks. The only thing saving users today is
  the completion-eligibility check plus the Space / `-` / Escape restore dance;
  every trailing-dash sentence still flashes a relation picker before the user
  can restore it.
- `=` after a space is almost never grammar. Whole-item operators (`=`, `=*`,
  `=/`, `x=`, `+N`/`-N`, `++`/`--`) are anchored to item starts or to block-ID
  suffixes (`@route:id=x…`, `=~<K>` drop lists); none fires for `word =` in the
  middle of prose. The two genuine collisions are both glued, not spaced, and
  both stay safe under the existing "space/tab before" precondition:
  `a=b` / `2+2=4` prose math (no surrounding space on at least one side in the
  common case, and even spaced `a = b` is far rarer than a prose dash), and the
  `x=~` / `=~` drop-tail family (cursor is inside a token, not after a space).
  Keep the space/tab-before precondition and the `RelationTo`-at-`(start,
  cursor)` eligibility check, and the false-positive rate drops by an order of
  magnitude versus `-`.
- Ergonomics agree: on a US keyboard `~` is Shift+backtick (a reach), `=` is an
  unshifted home-row-adjacent key, `-` is also unshifted but already overloaded
  as prose. `=` is the cheapest key with no prose meaning in exactly the
  hijacked position.

What must be kept from the `-` implementation when porting to `=`:

- The same three guards: space/tab before (reuse
  `relation_dash_position_ok`-style logic, renamed), `RelationTo` eligibility
  at the swapped candidate, `wikilink_claims` veto. Do not loosen any of them.
- A one-shot literal arm mirroring `CaptureRelationDashArm`, because `=` in
  prose (`a = b`) must stay typeable without a trip to Undo. The dash arm's
  Space / `-` / Escape restore table does not transfer verbatim (see §3).
- The picker-open race allowance (`openedByRelationDashAlias` pattern) needs an
  `=`-alias twin, or the new alias will intermittently fail to open its picker
  when a caret-selection analysis wins the race — the exact bug class the two
  recent commits fixed.
- Retire, don't orphan: delete `expand_relation_dash_alias` (or gate it behind
  a one-release fallback), remove `CaptureRelationDashArm` and its router
  branch once the `=` path ships, and update every doc row that teaches `-`
  (`docs/keyboard.md`, `docs/relationship-pickers.md`,
  `docs/reference/cli/capture-rewrite.md`, `docs/capture.md` "Sigil alias").
  Leaving both aliases live doubles the prose-hijack surface and keeps the
  `-=` → `~~` special case the request wants gone.

Adjustment A1: do not ship "only `=`" as "`=` anywhere". Ship "`=` after
whitespace where bare `~` would open Links To" — the same positional
precondition as `-` today. A bare `=` at a line start, glued to a word, after
another `=`, inside backticks/wikilinks, or inside an `x=` / `=~` / `@id=`
token must stay literal (mirror the `-` and `\`/`/` guards).

### 2. `~` / `=` after `~foo:bar` flips to `~~foo:bar` (and back)

Status today: `=` flips only a bare sigil (`~` + `=` → `~~`; `-` + `=` → `~~`).
`=` after `~~` is deliberately literal, and `~`/`=` after a complete token
(`~work:foo~`, `~work:foo=`, `~~work:foo~`, `~~work:foo=`) has no rewrite at
all. Verdict: yes — this is the highest-value item — with boundary rules.

Why it is worth doing: direction mistakes are currently expensive. The picker
flip exists, but once the token is committed (Return/Tab accepted, picker
closed, caret sitting after `~work:foo`), fixing `~` → `~~` means
arrowing back to the sigil and editing one character by hand, or deleting and
re-invoking the picker. The reporter's "realized the relation is pointing the
wrong way" moment happens after commit, not during filtering, so a
post-token flip pays off every week.

Design that fits the codebase:

- Prefer a `capture-rewrite` rule over a Mac-only edit. The flip is a grammar
  question ("is the caret directly after a complete relation token, and would
  the flipped sigil still scan as the same token in the opposite direction?"),
  and `bob` already owns that scan (`scan_line_relations`,
  `completion_field_at`). A Mac-local regex would drift from the CLI's strike /
  wikilink / `~~~` guards. Implement `expand_relation_post_token_flip` in
  `src/native/capture_language/rewrite.rs`, next to
  `expand_relation_flip_alias`: if the char before `--cursor` is `~`/`=` and
  the text before that char ends at a `Complete` relation's `end`, rewrite the
  sigil bytes (`~` ↔ `~~` at `entry.start`) and consume the typed char.
- Consume the typed char; do not append it. `~work:foo` + `~` → `~~work:foo`
  (caret after the token, not `~work:foo~`); `~~work:foo` + `~` → `~work:foo`.
  Same for `=`. This matches the existing `~=` → `~~` behavior (the `=` never
  appears in the output) and keeps the draft parseable after every keystroke.
- Scope to the token end only: caret must equal `entry.end` (or `entry.end`
  plus the `|label` span end when a label is present — decide once, document
  once; recommended: include the label, so `~a:b|next~` flips the whole edge
  and keeps its label). A `~`/`=` after a space (`~a:b ~`) is a new relation,
  not a flip — never touch it. A `~`/`=` in the middle of the token (block-ID
  query still open) keeps today's behavior (picker filter flip / completion).
- Keep every existing literal guard: `~~` + `=` after a bare sigil stays the
  flip today, but `~~old~~` strikes, `~/path`, `~5m`, `` `~` `` spans, and
  `[[~]]` must never flip. The rewrite must re-scan the flipped candidate and
  require a `Complete` relation at the same `(start, end±1)`; otherwise stay
  literal.
- Reverse must be symmetric: `~~work:foo` + `~`/`=` → `~work:foo`. The current
  `~~` + `=` early-return in `expand_relation_flip_alias` is exactly the branch
  this rule supersedes for the post-token position only; the bare-sigil
  `~~` + `=` (empty `~~` + `=` → literal) should stay literal to protect
  strike-adjacent typing.
- Mac side: route the rewrite through the same native-edit path as other
  single-edit rewrites (so Undo restores the pre-flip token), re-trigger
  analysis with `requestCompletion: true`, and suppress the empty-picker
  auto-open race the same way `relationFlipAliasOpen` does. The picker is
  closed at post-token time, so no picker state moves; only draft, caret, and
  parse change.

Open edge to close in implementation (not in this research): post-token `=`
when the token carries a `=~` drop tail or sits inside an `x=` / `@id=x`
suffix. Those suffixes own `=` already; the flip must refuse when the caret is
inside a `pomodoro_start_drop`, `pomodoro_close`, or `pomodoro_link` span.
State the refusal in the rule's doc comment so the next reader does not
"fix" it.

### 3. Escape `=` with a fast `==`

Status today: no `=` escape exists. Hash aliases escape by fast double-tap
(second `\`/`/` replaces `#` with the literal key); dash aliases escape by
Space / `-` / Escape restore while the arm is live. Verdict: yes, needed —
making `=` an alias without an escape would strand prose `=` — but define it
as two cases, not one.

- Case A — `=` before Bob answers (the `HashAliasProbe` window): the first `=`
  is still in flight as `pendingSeparatorToggleIntent` / `pendingHashAlias`
  equivalent. A second `=` arriving in that window must be treated like the
  hash double-tap: re-ask Bob about the first draft, and if Bob says the first
  would have become `~`, replace the `~` with a single literal `=` through the
  native edit (Undo returns to `~`). If Bob says the first would have stayed
  literal, leave both `==` alone. This is a small extension of
  `noteHashAliasBeforeReply` / `hashAliasReplyPending`, generalized from
  `\`/`/` to `=`.
- Case B — `=` after Bob already rewrote (`~` on screen, one-shot `=`-alias
  arm live, empty Links To picker open): a fast second `=` must do what the
  second `\` does per `docs/keyboard.md` ("leaves one literal and closes the
  menu"): replace `~` with `=` and close the picker without opening another.
  Do not stack a second alias (`~~`) — that is the current flip path and the
  opposite of an escape.
- "Fast enough" needs a number. Recommend: the arm window (same lifetime as
  `CaptureRelationDashArm` / hash arm — until the next non-escape key, draft
  change, picker filter entry, or submit), not a millisecond timer. Timer-based
  double-tap detection fights AppKit key repeat and accessibility key
  delays; arm-lifetime detection already handles both (`isARepeat` → consume).
  Document it as "press `=` again while the fresh `~` picker is still empty"
  rather than "within N ms".
- What `==` yields: one literal `=`, not two. The typed second key replaces the
  aliased sigil (same as `replaceHashAliasWithLiteralKey`: `#` → `\`). A user
  who wants literal `==` (`a == b`) types `=` `=` and gets `=`; a third `=`
  then inserts normally because no arm is live. Call this out in docs with an
  example, mirroring the `\#`-escape and `!!`-prose notes.
- Also keep Undo as the slow escape: after any alias rewrite, Cmd+Z restores
  the literal key. The fast path is for touch-typists; Undo is for "I noticed
  a second later".

Adjustment A3: the escape must cover both alias sites — the new bare-`=` alias
(§1) and the existing `~=` / `-=` flip alias. `~` + `=` + `=` fast should end
at literal `~=` (flip undone, first sigil kept), not at `~~` or `~=`. Spell
this as a test, because it is the case implementers will get wrong.

### 4. `~` / `=` flips direction inside the relation-label card

Status today: flip exists only in the task picker
(`CaptureKeyCommandRouter.swift` ~1137 → `.flipRelationDirection` →
`flipRelationDirection`). The label card has no such binding; both keys go to
the AppKit field as text. Verdict: yes for `~`, guarded yes for `=`.

- `~` is unconditionally safe to hijack in this field: `~` is in
  `FORBIDDEN_CHARS` (`src/native/task_relations/label.rs`), so it can never be
  committed as label content — today it only produces a `ForbiddenCharacter`
  refusal. Flipping on `~` converts a dead keystroke into the requested rescue
  path with zero label regressions.
- `=` is not safe unconditionally: it is a legal label character, and labels
  like `a=b` (or a typed `=` prefix) must keep working. Options, in preference
  order: (a) flip on `=` only when the field is empty (the common "wrong way,
  no label typed yet" moment the request describes; a non-empty field keeps `=`
  as text); (b) flip on `=` only when the field is empty or holds only `=`
  (treat a lone `=` as an explicit flip gesture, since no real label is a bare
  `=`); (c) never flip on `=` in the card and teach `~` as the card's flip key.
  Recommended: (a), with (b) as a one-line extension if user testing shows
  people type `=` first and then think better of it. Do not ship an
  unconditional `=` flip in the card.
- Mechanics: the card owns `draftSnapshot` + `tokenRange` + `labelRange` +
  `direction`, so a flip is a draft rewrite (insert/remove one `~` at
  `tokenRange.start`), then rebase `tokenRange` / `labelRange` /
  `draftSnapshot` / `direction` / `restoreCursor`, swap
  `ownerText`/`targetText` roles in the sentence pill, and keep `authoredLabel`,
  `selectedKey`, `showHidden`, `oneOff`, `ghosts`, and `rename` untouched.
  Cancel must still return to the pre-card draft/caret; submit must commit the
  flipped token + label. The picker-return path (`returnPicker`) needs the
  flipped direction too, or Escape will land back in the wrong picker.
- Keys: reuse `.flipRelationDirection` (or a sibling
  `.flipRelationLabelDirection`) in `relationLabelPromptCommand`, ignoring
  auto-repeat, and mirror the picker's footer/hint copy in the card footer
  (`~ flip direction`, plus `= flip direction` only when the empty-field guard
  holds, else omit it so the footer never lies). Update the card's
  accessibility label the same way `CapturePickerPresentation` does for the
  picker (`tilde or equals flips direction` → card equivalent, conditioned on
  the guard).
- Rename mode owns the field: when `rename != nil`, `~`/`=` stay text (rename
  text follows the same label charset, and hijacking rename input would corrupt
  a rename preview). Flip only in choose mode.

## Critique: is this the right plan?

Yes, with the adjustments above. The direction is right for three reasons:

1. It removes the worst alias (`-`) and keeps the cheapest safe one (`=`).
   Prose dashes are daily; spaced `=` prose is rare; the completion-eligibility
   gate makes `=` strictly fewer false positives.
2. It fixes mistakes where they are noticed (post-token, in the label card)
   instead of only where they are made (bare sigil, picker filter). The two
   existing flips are pre-commit; both requests are post-commit rescues, which
   is why they feel disproportionately valuable.
3. It closes the escape gap before widening the alias. Shipping a bare-`=`
   alias without `==` would trade dash-hijacks for equals-hijacks; shipping
   them together keeps every new hijack undoable at typing speed.

What I would not do:

- Do not keep `-` and `=` both live as bare aliases. Two prose-hijack keys,
  two literal arms, two restore tables, and the `-=` → `~~` special case that
  then needs its own escape matrix. Pick one (`=`), delete the other, and spend
  the saved complexity budget on the post-token flip tests.
- Do not implement the post-token flip as a Mac-local string edit. The
  strike/wikilink/backtick/`~~~` guards already live in
  `scan_line_relations` + `completion_field_at`; duplicating them in Swift
  guarantees drift (the `docs/task-relations.md` LP5/LP14 strike cases are the
  first victims). Put the rule in `capture-rewrite`, keep the Mac side to
  native-edit application + analysis retrigger.
- Do not give the label card an unconditional `=` flip. The charset fact
  (`~` forbidden, `=` allowed) decides this one without taste: hijacking `~`
  is free, hijacking `=` costs real labels. Gate `=` on the empty field.

## Recommended solution (build order)

1. bob-cli (`src/native/capture_language/rewrite.rs`,
   `src/native/capture_rewrite.rs` help, `docs/capture.md`,
   `docs/reference/cli/capture-rewrite.md`, unit tests in-module):
   - Add `expand_relation_equals_alias` (bare `=` after space/tab → `~`,
     same guards as the dash alias) and remove/retire
     `expand_relation_dash_alias` + `finish_relation_flip_dash_alias`'s `-=`
     branch. Keep `~=` → `~~`.
   - Add `expand_relation_post_token_flip` (post-token `~`/`=` flips
     `Complete` token sigil both directions, label-span-aware, suffix-span
     refusals, strike/wikilink re-scan). Keep bare `~~` + `=` literal.
   - `capture-rewrite` JSON stays shape-stable (`rule:
     expand_sigil_alias`, one covering edit, cursor past sigil/token end);
     only `summary` strings gain `=` variants.
2. Mac editor (`CapturePanelModel.swift`, `CapturePanelController.swift`,
   `CaptureKeyCommandRouter.swift`):
   - Replace the `-` alias arm with an `=`-alias arm (same one-shot shape as
     `CaptureRelationDashArm`); port the picker-race allowance, the native-edit
     application, and the Undo behavior; wire `==` Cases A + B (§3).
   - Route post-token `~`/`=` through `capture-rewrite` and apply as a native
     single-edit rewrite; retrigger analysis with completion on.
   - Update `noteSeparatorToggleIntentIfEligible` gates (drop `-`-as-relation,
     keep `-` for `noteSeparatorToggleIntent`'s other duties if any; add bare
     `=` intent with the space/tab precondition).
3. Relation picker: unchanged behavior (`~`/`=` anywhere flips), but update
   copy that still names `-` (`docs/relationship-pickers.md`,
   `docs/keyboard.md`, `CapturePickerPresentation` hints if they name `-`).
4. Label card (`CapturePanelModel.swift` prompt state +
   `CaptureKeyCommandRouter.relationLabelPromptCommand` +
   `CapturePanelView.RelationLabelPromptCard` footer/a11y):
   - `~` always flips; `=` flips only on empty field (extension: or lone
     `=`); never in rename mode. Rebase token/label ranges, direction,
     sentence pill, and `returnPicker`; keep query/selection/hidden/one-off.
5. Docs + tests:
   - `bob-cli`: rewrite unit tests for `=`-alias eligibility/refusals
     (line start, glued, `==`, backtick, wikilink, `x=`/`=~`/`@id=` refusals),
     post-token flip matrix (`~a:b`±`~`/`=`, `~~a:b`±`~`/`=`, with/without
     `|label`, strike/wikilink/prose refusals, `~=` + `=` → literal `~=`),
     `==` escape timing (before/after reply).
   - Mac: `CaptureRelationDashAliasTests` → `CaptureRelationEqualsAliasTests`
     (or rename), `CaptureRelationFlipAliasTests` + post-token cases,
     `CaptureSeparatorToggleTests` updates, label-card flip tests
     (empty/non-empty field × `~`/`=`, rename-mode refusal, Escape/submit after
     flip, ghost/hidden preservation).
   - Docs: `relationship-pickers.md`, `keyboard.md` (editor table + picker
     paragraph + relation-card keys), `capture-panel.md`, `protocol.md` if it
     names the `-` rule, `docs/task-relations.md` if CLI behavior changes.
6. Rollout: grammar stays additive (no stored-syntax change; `--dry-run` and
   `capture-parse` keep literal text), so no migration. Ship behind the normal
   release train; no vault rewrite, no mirror changes, no `LINKED FROM`
   backfill. Note the breaking-assist surface in the release notes the way the
   `-` alias introduction did (behavioral, not schematic).

## Acceptance criteria

- `Fix it =` (cursor end) rewrites to `Fix it ~` and opens Links To; `Fix it -`
  stays `Fix it -` (no picker); `a=b`, `a == b` (slow), `` `=` ``, `[[a=b]]`,
  `x=~2`, `@r:id=x1` never alias.
- `Fix it ~=` → `Fix it ~~` (Linked From); fast `~` `=` `=` → literal `~=`; fast
  `=` `=` after a bare alias → single literal `=` with the picker closed.
- `~work:foo` + `~`/`=` → `~~work:foo` (char consumed); `~~work:foo` + `~`/`=`
  → `~work:foo`; with `|label` the label survives; `~a:b ~` (spaced) starts a
  new relation instead of flipping; strikes/wikilinks never flip.
- In the label card with an empty field, `~` and `=` flip the sentence pill
  (`…links to…` ↔ `…will link to…`) and keep query/selection/hidden/one-off;
  with `follow` typed, `~` still flips (it is not label content) and `=` types
  text; in rename mode both type text.
- Undo after every new rewrite restores the literal keystrokes; footers, hints,
  and VoiceOver labels name exactly the keys that work (no `=` hint when the
  field is non-empty).

