# Bank/Album Schema Editors: Emoji Completion, Multi-Spot Reorder, Fast Preview

> Research: make the bank/album schema editors easier, more convenient, more
> beautiful — emoji completion/filtering, moving fields/choices up/down multiple
> spots with preview, and fast Apply. Screenshot:
> `~/tmp/screenshots/20261116_134836.png` (SASE Blog Zettel album Schema Card,
> Add-choice stage with empty "Choice emoji" input focused).

## Bottom line

Yes — do this, but narrow it. The request names three pains that share one root
cause: the Schema Card collects intent one keystroke at a time but validates
through a full `bob` subprocess round trip per gesture. The fix is not three
features; it is one interaction rule:

**Stage locally and instantly; validate once through `bob`; apply the preview
you already approved.**

Concretely, ship in this order:

1. **Inline emoji completion** in every schema emoji input (album choice emoji;
   bank category emoji) by reusing the existing `bob-emoji` catalog + search —
   no new dependency, no floating picker window.
2. **Multi-spot reorder as a single staged intent**: keep the existing
   `field.move` / `choice.move` absolute-position ops, but let the user move one
   item N spots (keyboard repeat, jump-to-top/bottom, drag) with an optimistic
   local reorder and one preview / one apply.
3. **Perceived Apply speed** via optimistic paint + preview reuse, not by
   weakening the guarded-update safety net. Real wall-clock Apply stays
   ~spawn + revalidate; the UI stops feeling like "a few seconds" because the
   result is already on screen and Enter never re-previews.

Do not build a generic emoji browser, bulk multi-select reorder, or a
"fast path" apply that skips validation. Those are the justified scope cuts
(see adjustments).

## What the screenshot shows

Verified by viewing `~/tmp/screenshots/20261116_134836.png`:

- Modal titled `Zettel · dev > SASE = … > sase_blog > SASE Blog Zettel`,
  `2 zettels · dated notes`.
- `Status · *` field with 6 choice chips (`🌱 Seed 1`, `✍️ Draft 1`,
  `✅ Ready 0`, …), `+ Add choice`.
- `Claim · * · text`, `Section` field with ~15 choice chips
  (`🪝 Intro 0`, `🍫 What is SASE? 1`, `📜 Prompt language (macros) 1`, …),
  `+ Add choice`, `+ Add field`.
- Open `Add choice` stage: `Choice label` (empty), `Choice emoji` (empty,
  focused), `Preview this edit` / `Cancel stage`.
- Bottom action bar: `Edit Add field Add choice Toggle required Toggle suggest
  Move up Move down Remove YAML Undo Cancel stage Close`, with hint line
  `⏎ edit / apply a add field c add choice ! required s suggest ⌥J/… move …
  remove y YAML u undo esc cancel / close`.

So the user is adding a choice to a 15-choice field and must type an emoji
blind, then reorder with single-step moves.

## Current architecture (verified)

### Where the editors live

- Editors are Obsidian plugin UI in the linked `bob-plugins` monorepo,
  `plugins/bob-ledger-tools/src/` (fragment build, `main.js` generated).
  `bob-cli` owns storage/validation; the plugin never parses or writes YAML.
- Album Schema Card: `241y-plugin-album-schema-card.js` (modal, 883 lines),
  `242c-plugin-album-schema-edit.js` (stage builders, targets, identity notes),
  `241y-plugin-album-schema-card-dom.js` (buttons incl. `Move up`/`Move down`),
  `242b-plugin-album-update-session.js` + `242aa-plugin-guarded-update-session.js`
  (preview/apply state machine), `242a-plugin-album-update-service.js`
  (spawns `bob albums update`), `241z-plugin-album-update.js`
  (`ALBUM_UPDATE_PREVIEW_DEBOUNCE_MS = 250`, timeout = `BOB_SPAWN_TIMEOUT_MS`).
- Bank setup/category cards: `248k-plugin-bank-setup-card.js` (sections
  accounts/rules/categories, `Alt+J/K move`), `248g-plugin-bank-category-new-stage.js`,
  `248d-plugin-bank-config-update.js` + `248e-plugin-bank-config-update-service.js`
  (same guarded-session pattern, `bob bank config update`).
- `bob-cli` writer: `src/native/albums/update/ops.rs` (~3800 lines),
  `plan.rs`, `src/native/records/schema.rs`. Move ops already take absolute
  `position` (`field.move`, `choice.move`) with `position_out_of_range` guards
  and inverse ops for Undo.

### Emoji today

- `plugins/bob-emoji/src/` has a complete offline solution: catalog shards
  (`020`–`023`), `030-emoji-model.js` (`emojiSearch`: tier 0 alias-prefix >
  tier 1 alias-substring > tier 2 tags > tier 3 description words; recents
  boost; popular fallback when query empty; limit 30), `040-emoji-suggest.js`
  (`BobEmojiSuggest`, `:shortcode:` trigger, glyph + `:alias:` + tags render),
  `050-plugin.js` (loads index + recents, registers `EditorSuggest`).
- Gap: `EditorSuggest` only fires in CodeMirror editors via `:` trigger. The
  Schema Card emoji inputs are native `<input data-schema-input="choiceEmoji">`
  built by `albumSchemaControl()`, so no completion fires. The user types a
  raw glyph (or pastes from elsewhere) with no filtering.
- Choice parsing already handles compound emoji:
  `albumSchemaChoiceParts()` splits leading `Extended_Pictographic` / flag /
  keycap runs from the label, so `🍫 What is SASE?` round-trips.

### Move + preview + apply today

- `schemaMoveSelected(direction)` only does `±1`: finds current index, computes
  `next = index ± 1`, queues `{ op: "field.move" | "choice.move", position: next }`.
  Buttons `move-up`/`move-down` and `Alt+J/K` call it; `Alt+J/K` repeats are N
  separate gestures.
- Every `schemaQueueOp()` clears stage, calls `session.setDraft([op])`, which
  schedules a preview after 250 ms debounce → spawns `bob albums update -d`
  (`BOB_SPAWN_TIMEOUT_MS = 20000`, 32 MB buffer) → paints consequence. Apply
  (`schemaApplyCurrentPreview`) refuses unless `preview-ready` + `canApply` +
  fresh generation, then spawns the real write, then `albumRevalidateAfterSync`
  (force fresh `apiAlbumReport`) before painting.
- Bank setup card has the same single-step `Alt+J/K move` idiom for
  rules/categories.
- Why Apply "takes a few seconds": at minimum one preview spawn + one apply
  spawn + one forced report fetch, each a Node→Rust process launch plus YAML
  load/validate/emit and index rebuild, serialized against sync flights. For a
  5-spot move done as five `±1` gestures that is ~5 previews + 5 applies +
  5 revalidates. Even when each leg is <500 ms, the chain feels broken.

## Emoji completion/filtering: design

Goal: typing in `Choice emoji` (and bank category emoji) feels like the
existing `:` completion in the editor, but inside a small modal input.

Recommended: **inline filtered dropdown attached to the emoji input**, reusing
`emojiSearch` + catalog, not a new picker library.

- Reuse, don't duplicate: import `emojiBuildIndex`, `emojiSearch`,
  `BOB_EMOJI_CATALOG`, recents helpers from `bob-emoji` fragments into the
  ledger-tools bundle (or a shared chunk). No `emoji-mart` / CDN / network.
- Trigger: filter on every input change (glyph fragment, alias without colon,
  tag, description word). Empty query shows recents + popular (same as
  `emojiSearch` with `""`) — this is the "browse" case the screenshot needs.
- Render (max ~8 visible, scroll): `glyph  :alias:  tag hints`, highlight
  matched alias substring (same as `renderSuggestion`). Show `isRecent`
  subtly. Footer hint: `↑↓ navigate · Tab/⏎ accept · Esc dismiss`.
- Accept writes only the glyph into the input (keep `:alias:` as search text,
  never committed). Selecting updates recents via `emojiRememberRecent`.
- Keys inside the emoji input: `↑/↓` + `Tab`/`⏎` navigate/accept the dropdown;
  `Esc` dismisses dropdown first (second `Esc` cancels stage — preserve the
  existing `schemaHandleEscape` staging order). `Alt+J/K` must not move the
  underlying row while the dropdown is open.
- Validation stays: single grapheme cluster (reuse the `albumSchemaChoiceParts`
  regex); reject multi-emoji/letter input with the existing refusal path, not
  a new error UI. Keep allowing paste of a raw glyph (power users).
- Same component for bank category emoji and album choice emoji. Bank hotkeys
  (`g`, `d`, …) are unrelated — do not conflate emoji search with hotkey
  assignment.

Why not a floating "emoji browser" button: it adds a second focus trap, breaks
the keyboard-first card idiom, and duplicates the catalog UI. Inline filtering
covers "I know roughly the food / the feeling" and "show me recents" with one
control. A browser can come later if telemetry says users browse aimlessly.

Beauty note: match the card's chip vocabulary — the accepted glyph previews
inline in the stage (`🍫 What is SASE?` live chip), so the user sees the exact
token that will appear in the index.

## Multi-spot moves with preview: design

Goal: move one field/choice from index `i` to `j` in one mental gesture, see
where it will land before committing, pay one preview + one apply.

Recommended interaction (both album card and bank setup card):

- Keep `Alt+J` / `Alt+K` (and `Move up`/`Move down` buttons) as-is for `±1`.
- Add: hold-to-repeat (key repeat already works — but stop queueing one op
  per repeat; coalesce), `Shift+Alt+J/K` = jump to top/bottom of the current
  field/choice list, and drag-and-drop on chips/rows as the mouse path.
- Optional but cheap: `Alt+1..9` or a "Move to position N" mini-stage for
  very long lists (the screenshot's 15-choice Section field is the motivating
  case). If in doubt, ship repeat + jump + drag first; numeric jump is the
  first follow-up.
- Optimistic local model: on each move intent, reorder the in-memory
  `schemaModel.fields` / `choices` array immediately and repaint the card
  (selection follows the moved row), then `setDraft` with **one** op carrying
  the final absolute `position`. Five `Alt+J` presses in <1 s produce one
  preview, not five. The backend needs no change — `position` is already
  absolute.
- Preview content for a pure reorder should be glanceable: `Section:
  "Intro" 3 → 1` plus a before/after strip (moved chip highlighted, neighbors
  dimmed). Server consequence stays the authority (impact counts for field
  moves: `index_by` / grouping changes; choice moves are presentational —
  say so explicitly so users stop fearing them).
- Selection stability: after preview resolves, keep focus on the moved row;
  `Undo (u)` already exists via inverse ops — advertise it in the move
  consequence (`Schema saved. Press u to preview Undo.` already does).
- Drag: HTML5 drag on chips with keyboard parity (drag is not the only path).
  Announce moves for screen readers via the existing card status region.

What not to build now: multi-select bulk reorder (lifts N rows at once).
It complicates selection + inverse ops for a rare case. Single-item multi-spot
covers the complaint.

## Preview + Apply performance

Do not "fix" this by removing the preview-before-apply guard. That guard
(`preview-ready` + `canApply` + generation match + `saveEditors` + one-flight
apply) is why the card survives concurrent vault edits and open Source panes.
Instead fix perceived latency:

1. **Coalesce previews.** Already partially there (250 ms debounce), but
   `schemaQueueOp` per `±1` defeats it during repeats. Coalesce rapid moves
   into one draft (final position only) before `setDraft`.
2. **Reuse the preview on Apply.** `schemaApplyCurrentPreview` already refuses
   stale previews; keep that, but never trigger a redundant `previewNow`
   from the Apply path when state is already `preview-ready` and fresh.
   The complaint's "Apply takes seconds" is partly preview→apply double work
   plus the forced post-write report.
3. **Paint optimistically, revalidate in background.** The local reorder +
   emoji chip preview can paint in <16 ms. Mark the card `preview-pending`
   subtly (existing `busy` state) rather than freezing it; let the server
   consequence fill in. Post-apply, keep the optimistic order on screen while
   `albumRevalidateAfterSync` runs; only roll back on refusal (with reason).
4. **Measure before optimizing the spawn.** `BOB_SPAWN_TIMEOUT_MS = 20000` is
   a ceiling, not a budget. Add timing to the preview/apply report path
   (envelope build → spawn → decode → revalidate) in the e2e harness
   (`scripts/test-obsidian-album-ui-e2e.cjs` family) and set a budget
   (e.g. p50 preview <600 ms on a 100-record album). Only if spawn dominates
   should you consider a persistent `bob` worker or a JS-side order-only fast
   path — both are real complexity with real staleness risk, not v1.

## Critique: is this a good idea?

Yes, with two adjustments and one warning.

**Worth doing.** Schema editing is the highest-leverage UI in the album
system: a typo'd choice key strands records, a field reorder reshapes the
index, and today both require YAML confidence. The card already proved the
pattern (keyboard-first, staged, dry-run consequence, one scoped commit).
Emoji + reorder polish turns it from "safe but tedious" into "fast and
pleasant" — exactly where Bryan spends time (15-choice Section fields).

**Adjustment 1 — treat bank and album as one interaction, two writers.**
The prompt says "bank/album schema editors". They are not the same code
(`albums update` vs `bank config update`), but the gestures should match:
same `Alt+J/K`, same jump modifiers, same inline emoji completion, same
preview-then-apply language. Implement the emoji input and the
reorder-coalescing once as shared fragments; wire each card's session
(`createAlbumUpdateSession` vs `createBankConfigUpdateSession`) as the only
difference.

**Adjustment 2 — cut scope to staged single-item moves + inline emoji.**
Defer: emoji browser modal, numeric position dialog (unless the 15-choice
case proves repeat+drag insufficient), bulk multi-select, offline/fast-path
apply. Each adds state (focus traps, selection sets, divergence from server
truth) for diminishing returns.

**Warning — beauty must not outrun reliability.** The card's ugliest moment
(an empty emoji box) is also its safest: nothing is staged until Preview
succeeds. Keep that invariant visible: the stage always shows
`Preview this edit` first, Apply stays inert until `canApply`, refusals name
the field/line (`refusal.line`, `key_path` already flow through). A
beautiful editor that lets Enter write an unpreviewed draft would be a
regression, not a polish.

## Recommended solution

**Phase A — shared inline emoji completion (both cards).**

- Extract `bob-emoji` search (index + `emojiSearch` + recents) for reuse from
  modal inputs; attach dropdown to `choiceEmoji` and bank category emoji.
- Empty-input shows recents + popular; typing filters by alias/tags/words;
  `↑↓/Tab/⏎` accept, `Esc` dismisses-then-cancels; accept writes glyph only.
- Acceptance: keyboard-only flow (open Add choice → type `choc` → see `🍫`
  top-ranked → `⏎` → chip previews `🍫 <label>` → Preview → Apply); mouse
  click also works; pasted glyph still accepted; invalid input refused with
  existing copy.

**Phase B — coalesced multi-spot reorder (both cards).**

- `Alt+J/K` repeat coalesces to one `move` op with final absolute position;
  `Shift+Alt+J/K` jumps to ends; drag-and-drop mirrors the keyboard move;
  selection follows the moved row; preview shows `i → j` + before/after strip
  + impact note (presentational vs index-changing).
- No `bob-cli` op changes needed; verify `position_out_of_range` + inverse-op
  Undo cover the coalesced op (existing tests in `ops.rs` already cover
  `field.move` / `choice.move`).
- Acceptance: move `Intro` from position 3 to 1 with 2 key gestures (or one
  drag), one preview, one apply; Undo restores; rapid repeats never queue N
  previews (assert via session test doubles).

**Phase C — perceived-speed hardening.**

- Optimistic reorder paint + preview reuse on Apply + background revalidate;
  add preview/apply timing to the album UI e2e harness; set and document a
  p50 budget.
- Acceptance: repeated-move Apply feels instant (paint <1 frame) with server
  confirmation <1 s on a large album; stale-vault and open-editor guards
  still refuse with the current copy.

Sequencing: A then B (both user-visible), C last (measurement-led). YAML
(`y` jump) stays for kind/key changes per the existing identity notes — the
card never models those, by design.
