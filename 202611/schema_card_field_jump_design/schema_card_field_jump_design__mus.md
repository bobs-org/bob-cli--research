# Schema-card field jumps: `J`/`K` field motion, `1`–`9` direct jumps, index badges, breathing room

Research by `mus` · 2026-11-17 · in response to Bryan's schema-editing-cards keymap proposal.
Scope: the schema editing cards opened from album notes, record notes, and `~/bob/bank.md`
in Obsidian. All code below is the `bob-plugins` linked checkout
(`plugins/bob-ledger-tools/src/`, `scripts/`).

## Verdict up front

Yes — do it. It is a good idea, and the request is smaller than it looks: **one card
implementation covers both album notes and record notes**, because they already share
`AlbumSchemaCardModal`. The `bank.md` card is a *different* card with a *different*
selection model, so it should be explicitly out of scope for v1 (details in §6).

Concretely, I recommend shipping this, with four adjustments to the proposal:

1. **Redefine bare `J`/`K` (either case) as field-only motion**, keeping arrows as the
   fine-grained move-everything keys. Today bare `j`/`k` step through *every*
   selectable row (fields, every choice chip, `+ choice`, `+ field`, issues). On a field
   like `Section` with ~15 choices that is a ~17-stop walk to reach the next field —
   the exact pain in the screenshot. Fields are the units; choices are values.
2. **Fix the dead uppercase keys as part of this change.** Today the bare handler only
   matches lowercase `event.key === "j"` / `"k"` — with Shift held (`J`/`K`, the exact
   keys in the request) *nothing happens*. Whatever semantics we choose, both cases must
   work (plus an `event.code` fallback for non-Latin layouts, mirroring the existing
   Alt+J/K handler).
3. **Number the first nine fields in visible order; fields 10+ get no badge and no
   digit.** The proposal says "indexing each field selection (starting at 1)" without
   saying what happens at field 10. `1`–`9` can only ever address nine fields — say so
   in the UI by only badging those nine.
4. **Scope v1 to the album/record card; defer `bank.md`.** The bank card
   (`BankSetupCard`) has no fields — it has sectioned category/account/rule lists — and
   its categories section already binds bare `0`–`9`/`a`–`z` as per-category hotkey
   jumps. Positional `1`–`9` there would collide with an existing, shipped behavior.

The rest of this note documents what I verified in the code, critiques each part of the
plan, and ends with the recommended implementation (§8).

## 1. What the screenshot shows

`20261117_110414.png` (2858×1728): the `sase_blog_zettel` album note with the schema
card open. The card shows, top to bottom: title crumb, `4 zettels · dated notes`,
the **Status** field row (selected, purple ring) with its choice cloud
(Seed/Draft/Ready/Placed/Later/Cut, `+ choice`), then the **Claim** field row, then
the **Section** field row with a large multi-row choice cloud, then `+ choice`,
`+ field`, and the hint footer:

> `⏎ edit · a add field · c add choice · ! required · s suggest · ⌥J/K move · ⌃D
> remove · y YAML · esc close · …`

Two observations that motivate the request: (a) the footer documents **Alt**+J/K
(reorder the selection) but the bare `j`/`k` motion that already exists is
*undiscoverable* — it appears nowhere in the hints; (b) the Status choice cloud runs
directly into the Claim row with almost no separation, so it is genuinely hard to tell
which choices belong to which field — the "vertical space" ask is real, not cosmetic.

## 2. What I verified in the code

### 2.1 One card serves album notes AND record notes

- `242d-plugin-album-entrypoints.js` (`openAlbumSchemaEntry`): record notes resolve
  their parent album through frontmatter `parent` and open **the same**
  `AlbumSchemaCardModal` on the parent album's schema. Album surfaces and record
  surfaces converge here, so one implementation covers both — no per-surface work.
  (Glossary-confirmed vocabulary: an *album note* owns one record-note schema;
  a *record note* links to its album via `parent` — `sase memory read
  glossary:album-note glossary:record-note`.)
- `bank.md` opens a different modal, `BankSetupCard`
  (`248k-plugin-bank-setup-card.js`, entry via `248l-…-entrypoints.js`). It is
  sectioned (`categories` / `accounts` / `rules` / `checks`,
  `BANK_SETUP_CARD_SECTION_ORDER`) with per-section selection objects
  (`{type, key, id}`), not `field:`/`choice:` targets. Nothing about "fields" or
  "field selections" transfers directly.

### 2.2 The selection model the jumps must build on

`242c-plugin-album-schema-edit.js`, `albumSchemaTargets(model)` — the full selectable
list, in order: `stats` → per field `field:<key>` → per choice
`choice:<field>:<value>` → (`add-choice:<field>` for `choices`-kind fields) → …
→ `add-field` → issues. Declaration order throughout. The modal keeps
`selectedKey`/`selectedIndex` (`241y-…-card.js` `schemaSelect`, `schemaMove` with
wrap-around, `schemaRepairSelection`).

### 2.3 Current key handling (the exact lines to change)

`241y-plugin-album-schema-card.js`, `schemaOnKeyDown` (~lines 820–879):

- Inputs/stage short-circuit first: in an input only close-keys and Enter (apply)
  fire; with a stage open, browsing keys never fire. **Digits typed into stage inputs
  are therefore already safe** — any `1`–`9` handler placed alongside the other
  browsing keys inherits this for free.
- Browsing today: `Enter` edit · `Alt+J/K` reorder selection (`schemaMoveSelected`)
  · bare `j`/`ArrowDown`/`ArrowRight` → `schemaMove(1)`, bare `k`/`ArrowUp`/`ArrowLeft`
  → `schemaMove(-1)` · `a` add field · `c` add choice · `!` required · `s` suggest ·
  `y` YAML jump · `u` undo · `Ctrl+D` remove · `q`/`Ctrl+[`/Esc close (via
  `onEscapeKey` override + `241xc-plugin-card-close-keys.js`, per
  `decisions:q-and-ctrl-bracket-mirror-esc`).
- Gaps I confirmed: (a) bare handler matches **only lowercase** `j`/`k` — `J`/`K`
  are dead keys today; (b) no `1`–`9` handling anywhere in the card; (c) IME guard
  (`isComposing`/`keyCode 229`) and `defaultPrevented`/`__schemaEscapeHandled` guards
  already exist — new handlers must sit behind the same guards.
- Close-key interplay: close handling runs *before* the browsing keys, and `q` in a
  text control types instead of closing (`bobCardTypesText`). New bare keys must keep
  this ordering: never fire from inputs, never preempt close keys.

### 2.4 How the body paints (where badges and spacing go)

- `241yc-…-regions.js` `albumSchemaCardPaintBody` (~281–423): per field, paints the
  field row (`albumSchemaCardPaintFieldRow`, ~148–182: label + pills
  required/kind/index + `filledText`), then that field's choice cloud, then an
  optional `+ choice` row. Selection is `data-target-key` + `.is-selected` +
  `aria-current`; focus follows selection (`schemaFocusAfterPaint` in
  `241yd-…-paint.js`). A field jump is therefore just `schemaSelect("field:<key>")`
  — focus, ring, and `aria-current` come along with no extra work, provided the jump
  handler also ensures the row is scrolled into view.
- `albumSchemaCardHintItems` (~707–787) builds the footer strip; editable-mode hints
  currently show `⌥J/K move` but **no `j`/`k` entry at all** — the existing motion is
  invisible, which lowers the risk of changing it (few users can depend on what they
  cannot discover) and raises the obligation to document the new motion *in the strip*.
- Arrange mode (`241yb-…-arrange.js`, `241xb-…-dom.js`): gap-pick badges come from
  `schemaArrangeGapBadges` → `arrangeGapHintLabels` (letter badges; a shell test
  asserts no gap badge is `q`). Digits do not currently collide with gap badges, but
  hint mode suspends normal selection semantics, so digits should stay inert while it
  is active (see §8).
- Read-only card (`241x-…-dom.js` summary + the non-editable branch of `PaintBody`):
  rows are plain divs without `data-target-key` buttons; targets still exist in the
  model so modal-level jumps would function, but no badges paint there. Fine for v1.

### 2.5 Current CSS density (the spacing ask)

`styles.css` (~8773–8878): `.bob-album-schema-choice-cloud`
`{ display:flex; flex-wrap:wrap; gap:0.2em; margin:0.15em 0 0.35em; }`; field rows
have **no top margin** — a cloud's 0.35em bottom margin is the only thing separating
one field's choices from the next field's label. The fix is a sibling rule that
groups each field with *its own* cloud (see §8).

### 2.6 Bank card keymap (why bank is out of scope)

`248k-…-card.js` `onKeyDown` (~667–797): arrows move selection; `Alt+J/K` begins a
*move* (reorder) gesture; `Ctrl+N/P` also move; `Ctrl+D` remove; `+` add;
`Tab` switches sections; **bare `j`/`k` do nothing**; and in the categories section
any single `[a-z0-9]` press jumps to the category whose hotkey matches
(`bankSetupCardSelectionByHotkey`, ~793–796). So: no field concept, digits already
claimed, and even `J`/`K`-as-motion would need a per-section definition. A separate,
smaller design — not this change.

### 2.7 In-repo precedents for digit keys

- Task Card (`plugins/bob-navigation-hotkeys/src/314-task-card-key-model.js`):
  bare `/^[1-9]$/` with no modifiers already jumps to numbered items — the exact
  idiom being proposed, so schema-card digits would *match* Bob card language.
- `266a-window-tab-model.js` `windowPrefixDigitFromKeydown`: accepts both
  `event.key` digits and `Digit`/`Numpad` codes — copy that dual check so numpad `1`
  works too.

## 3. Critique of the plan

**The core idea is sound.** Field-level motion matches the user's mental model
(fields are the units being designed; choices are values being picked), and the
screenshot proves the pain: reaching Claim from Status today costs ~8 `j` presses
through choice chips. Numbered direct jumps compose well with the existing `y`
(YAML-jump-to-field-line) escape hatch.

**Adjustment 1 — semantics of `J`/`K`: fields-only, both cases.** The request says
"`J` and `K` … jump … to the next/previous selection that represents a field". I read
that as: the *landing* selection is always a field. Keep arrows (and, via native Tab,
button focus) as the fine-grained path to individual choice chips. Do not preserve
bare-`j`/`k`-steps-through-choices: it is undiscoverable (absent from hints), it is
what makes long fields painful, and the uppercase keys it would conflict with are
currently dead. One crisp rule — "J/K move between fields, arrows move between
everything" — beats a two-tier shift-sensitive scheme.

**Adjustment 2 — anchor rule for non-field selections.** "Next field" needs a
definition when the current selection is a choice chip, `+ choice`, `stats`, or an
issue. Recommended: the anchor is the field containing the current selection (a
choice's own field, an `add-choice` row's field); `J` = next field after the anchor,
`K` = previous field before it, wrapping within the field list; from `stats` /
`add-field` / issues, `J` = first field, `K` = last field. Predictable from any
starting point, two sentences to document.

**Adjustment 3 — cap the numbering at nine, visibly.** With 10+ fields, digits can
only address the first nine. Badge only fields 1–9 (in *visible* order, so arrange
reorders renumber honestly); fields 10+ get no badge rather than a teasing number.
The hint entry reads `1–9`, never `1–N`.

**Adjustment 4 — bank.md deferred, stated plainly.** Reasons in §2.6. If parity is
wanted later, the bank analogue is per-section `J`/`K` movement aliases (bare `j`/`k`
are free there) — but *not* positional digits, which collide with category hotkeys.
That is a separate bead, not a stretch goal of this one.

**What I would not change:** `Alt+J/K` reorder, `Ctrl+D` remove, `y` YAML jump, the
`a`/`c`/`!`/`s`/`u` single-letter commands, and the `q`/`Ctrl+[`/Esc close contract
(`decisions:q-and-ctrl-bracket-mirror-esc`) all stay exactly as they are. The footer
already says `⌥J/K move` — the new entries must be worded to contrast (`J/K field`,
not `J/K move`).

## 4. Intuitive? Reliable? Beautiful? — pressure-testing the three goals

- *Intuitive.* J/K-as-field-motion plus visible `1`–`9` badges plus a footer that
  teaches both is about as discoverable as a keyboard UI gets. Residual risk: users
  who learned bare-`j` choice-stepping (undocumented, unlikely) lose it — mitigated by
  arrows. The `⌥J/K move` vs `J/K field` wording must be deliberately contrasted in
  the strip or the two will blur.
- *Reliable.* The risky surface is small and already guarded: inputs (early return),
  open stage (early return), applying state (early return), IME (guard exists). New
  risks to close: hint/arrange modes (gate digits and jumps off while active),
  empty-schema (no-op), stale-report refresh mid-jump (selection repair already
  exists via `schemaRepairSelection`), and focus loss if a painted row is missing
  (fallback: keep selection, focus card). All covered in §8.
- *Beautiful.* Two surgical changes, both in the card's existing visual language:
  a muted index badge that rhymes with the existing count pills
  (tabular numerals, no new color), and one sibling-margin rule that turns
  field+cloud into visual blocks. No layout restructure, no new hues, wraps safely at
  narrow widths (both rows already `flex-wrap`).

## 5. Edge cases the implementation must handle

1. Zero fields (empty schema): `J`/`K`/digits no-op; hide both new hint entries.
2. One field: `J`/`K` wrap to itself (harmless); digit `1` selects it.
3. 10+ fields: badges on first nine only; digits `1`–`9` address those nine.
4. Choice/`+ choice` selected: anchor to its field (§3, adjustment 2).
5. `stats`/`+ field`/issue selected: `J`→first field, `K`→last field.
6. Stage open, applying/preview-pending, arrange hint mode, arrange dirty-confirm:
   digits and jumps inert (Enter/Esc own those modes); hint strip already swaps in
   those modes, so the new entries vanish with it.
7. Arrange-projected order: badges and jumps follow the *painted* order, not the
   model order, or numbers will lie after a drag.
8. Non-Latin layouts / Caps Lock: accept `event.code === "KeyJ"/"KeyK"` as fallback
   (same pattern as the Alt handler) and compare digits via both `key` and
   `Digit`/`Numpad` codes (same pattern as `windowPrefixDigitFromKeydown`).
9. Long field names + badges at narrow widths: badge is a fixed-width inline chip;
   rows already wrap — verify at ~320px card width.
10. Screen readers: badges `aria-hidden`; the field button's `aria-label` gains
    "field N of M" so the number is announced once, not twice.

## 6. Explicit scope decision: bank.md

Out of scope for v1. The bank setup card has sections, not fields; its digit keys are
taken (category hotkeys); its bare `j`/`k` are free but would need per-section motion
semantics (`moveSelection` aliases) — a different, smaller proposal. Ship the
album/record card first; file the bank analogue as follow-up only if Bryan misses it
there. Record notes need no extra work (shared modal, §2.1) — verify with one record
note in manual QA.

## 7. Verification plan (what "done" looks like)

- Shell tests in `scripts/test-ledger-tools-album-schema-card-shell.cjs` (FakeNode
  harness already drives `schemaOnKeyDown`): field-skip forward/back from field and
  from choice anchors; wrap at both ends; `stats`/`add-field` anchor rule; digits
  `1`–`9` incl. uppercase `J`/`K` and numpad codes; digits inert in stage inputs and
  while a stage/apply/hint-mode is active; >9-field badging (first nine only);
  `Alt+J/K` reorder and all existing single-letter keys unchanged (regression).
- `npm run build:check` (`build-plugins.mjs --check`) + the schema-card shell test
  file; the full `test:unit` line if time permits (it is long — the repo's known-long
  commands live behind `just check` per project convention).
- Manual Obsidian QA on the `sase_blog_zettel` album from the screenshot (Status →
  `J` → Claim; `1` → Status; `3` → Section) plus one record note and one 10+-field
  album; narrow-width check for badge wrap.
- Docs: the footer strip is self-documenting; update whichever plugin doc enumerates
  schema-card keys (check `plugins/bob-ledger-tools` docs + `docs/records.md`
  cross-links) so prose and strip agree.

## 8. Recommended solution

**Ship v1 on `AlbumSchemaCardModal` only (album notes + record notes, §2.1), with bank
explicitly deferred (§6).**

1. **Motion.** In `schemaOnKeyDown`'s browsing branch, replace the bare-`j`/`k` arms
   with field jumps: unmodified `j`/`J` (`key` case-insensitive or `code === "KeyJ"`)
   → next field; `k`/`K` → previous field, per the anchor rule in §3. Arrows keep
   `schemaMove` over all targets. Leave `Alt+J/K` (reorder) untouched.
2. **Direct jumps.** Unmodified `1`–`9` (`key` or `Digit`/`Numpad` code, no modifiers)
   → select the nth field in painted order; no-op beyond the field count. Inert in
   inputs, open stages, applying/preview states, and arrange hint mode (the existing
   early returns plus one hint-mode guard).
3. **Badges.** In `albumSchemaCardPaintFieldRow`, prepend a muted index chip
   (`aria-hidden`, count-pill-like styling, tabular numerals) for fields 1–9 in
   painted order; extend the field button's `aria-label` with "field N of M".
   No badge on fields 10+.
4. **Spacing.** One CSS rule — `.bob-album-schema-dialog
   .bob-album-schema-choice-cloud + .bob-album-schema-field { margin-top: ~0.55em; }`
   (tune 0.5–0.7em against the screenshot) — so each field row opens a visual block
   with its own cloud tucked beneath it. No other layout changes.
5. **Hints.** Add `J/K field` and `1–9 jump` entries to `albumSchemaCardHintItems`'
   browsing set (hidden with zero fields); keep `⌥J/K move` verbatim so the two
   motions read as distinct.
6. **Tests + docs** per §7; manual pass on the screenshot's album, a record note,
   and a 10+-field album.

This keeps every existing contract (close keys, reorder, YAML jump, single-letter
commands, arrange flows), fixes two dead keys, teaches itself in the footer, and
changes the card's look by one badge and one margin — intuitive, reliable, and
quietly beautiful.
