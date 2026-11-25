# Bank card as a proper property card: collapsing schema + `_` keymap

Research report (`__mus`), 2026-11-25. Independent research for the bank-card
property-card proposal: make the `bank.md` bank card a full property card
(collapse its schema section by default, hide native Obsidian Properties),
and add a `_` keymap that toggles the schema section in the bank card and in
album cards (expanded by default). Goal: help decide the best implementation,
critique the plan, and recommend a solution.

Primary sources inspected (all in-repo, no peer reports consulted):

- `plugins/bob-ledger-tools/src/248a-plugin-bank-setup-model.js` — Setup state,
  `BANK_SETUP_DEFAULT_EXPANDED = true`, invalid-forces-open, collapsed line.
- `plugins/bob-ledger-tools/src/248b-plugin-bank-setup-dom.js` — Setup header
  painter, `▾ Setup` disclosure, collapsed line, foot-free fences.
- `plugins/bob-ledger-tools/src/248c-plugin-bank-setup-hosts.js` — bank host:
  per-note session expand map, focus-preserving repaint, **no**
  `titleOwnership` (album host has `titleOwnership: true`).
- `plugins/bob-ledger-tools/src/241v-plugin-album-header.js` — album host with
  title ownership, `albumHeaderExpanded` session map, `toggleSchema` handler.
- `plugins/bob-ledger-tools/src/241w-plugin-album-schema-model.js`,
  `241x-plugin-album-schema-dom.js` — schema starts expanded, session-only
  collapse flag, healthy fold line, `aria-expanded` + `data-schema-fold`.
- `plugins/bob-ledger-tools/src/248m-plugin-schema-double-equals.js` — the
  `==` / `-` / `+` key dispatch, Vim-snapshot gates, species registry
  (bank → album → record), `toggle-card-properties` command.
- `plugins/bob-ledger-tools/src/240p-plugin-property-card-foot-state.js`,
  `240q-plugin-property-card-frontmatter-ownership.js` — per-note foot session
  state, whole-frontmatter ownership coordinator (hide native, restore on
  uncertainty).
- `docs/bob-ledger-tools.md` — bank card + Properties drawer documentation.
- Prior (unrelated, public) research finals in `202611/`: `bank_config_read_write_ux__final.md`,
  `album_record_schema_ux__final.md` — nested mappings can't render natively;
  hide the row, render a replacement, edit through bob.

## What exists today

**Bank card.** The `bank.md` hub renders a Setup header under `# 🏦 Bank` from
`bob bank config`: `🏦 BANK` badge + `▾ Setup` disclosure (expanded by default,
per-session collapse), collapsed line `<accounts> · <categories> · <rules>`,
`⊞ Edit`, `↗ YAML`, then the shared properties **foot outside the collapse**.
`==` on `bank.md` opens the bank editor; `-` toggles the foot drawer; `+`
opens the Property Editor. It already hides the single `bank` frontmatter row
(the native widget renders nested mappings as an inert JSON string), but it
**keeps the rest of the native Properties block** and **does not own the
title** — the two things that make album/record/day/period cards "proper"
property cards.

**Album schema section.** The album header renders a schema summary button
(`▾ Schema · N fields · …`, `aria-expanded`, `aria-controls` on the chip list)
that toggles a session-only per-note flag (`albumHeaderExpanded`, default
expanded). Click-only today: no keymap. Collapse is paint-only, never writes
the vault.

**Keymap family.** `==` opens the species editor (bank → album → record via
registry), `-` toggles the foot drawer, `+` opens the Property Editor. All
three fire only in desktop Live Preview, Vim normal mode, empty key buffer, no
count/register/operator, unmodified (ctrl/alt/meta free; shift ignored so `+`
works). `-`/`+` additionally require the event to be in note content
(`inContent`), `==` requires it in the editor. Vim motions are already
overridden by precedent: `-`/`+` steal Vim's line motions in exactly this
context.

## Critique of the plan

**The direction is right.** The bank hub is the worst of both worlds today: the
most setup-heavy note in the vault shows both a rendered Setup body *and* a
native Properties block that renders its most important value (`bank:`) as an
unreadable JSON string. Full property-card treatment (own the title, hide all
native Properties, foot drawer as the only Properties surface) is the proven
album pattern, and the kit already supports every piece: title-slot mount,
whole-frontmatter coordinator with automatic native restore on stale
source/cache, per-note session foot state, `-`/`+` arms. This is assembly, not
invention — low risk.

**Collapsed-by-default for the bank schema is correct.** Bank Setup is
reference material 99% of the time (categories change rarely; the queue/month
cards below are the daily surface). The collapsed line already summarizes what
matters (account/category/rule counts). Keep the existing escape hatch:
`invalid` state forces expanded so findings can't hide.

**One shared `_` toggle for bank + album is the right call.** Both sections
already share a visual language (▾/▸ disclosure, `aria-expanded`, one-line
fold grammar, click toggles, session-only state). One key for "fold/unfold the
schema I'm looking at" is easier to learn than two, and the species gate means
it never fires where there's no schema to fold.

**Adjustments I would make (called out explicitly):**

1. **Don't persist the collapse in the vault.** Keep it session-only
   (`Map` keyed by normalized path, like both existing maps). Persisting
   fold state in frontmatter or `localStorage` adds sync/conflict surface for
   zero benefit — refresh/collapse/revisit survival is already the behavior,
   and reload reset is harmless.
2. **Don't redesign the folded lines.** Both already exist
   (`albumHeaderFoldText`, bank `collapsedLine`). The beauty work is
   alignment, not invention: same disclosure glyph rhythm, same muted
   summary style, `walks by <field>` pill parity if cheap.
3. **Scope `_` to bank + album only — not record/day/period.** Records expose
   schema rows through the Record Card's own drawer; day/period cards have no
   schema section. A generic "toggle first collapsible" key would be
   unpredictable. The gate should resolve the species registry and act only
   for `bank`/`album` mounts in the active view.
4. **Keep album expanded by default.** Agreed as specified. The album schema
   is the note's definition and is referenced while writing records; bank
   Setup is not. Asymmetric defaults with a symmetric toggle is the right
   shape.

## Design: intuitive, reliable, beautiful

**Intuitive.** `_` joins a discoverable family: `==` edits the card, `-`
toggles Properties, `+` edits properties, `_` folds the schema. Underscore
reads as "underline = the summary line", and Shift+- sits next to `-`/`+` on
the keyboard. Discoverability needs three cheap touches: a `_<` kbd hint in
the Setup/schema disclosure `title` (both already carry tooltips), a row in
`docs/bob-ledger-tools.md` next to the `-`/`+`/`==` documentation, and the
existing click target staying exactly where it is (mouse users unaffected).

**Reliable.** Reuse, don't invent:

- Collapse state: mirror the album pattern — `bankSetupExpanded` already
  exists; only flip `BANK_SETUP_DEFAULT_EXPANDED` to `false` and keep
  `invalid → always expanded`. Album side needs no state change (only the
  new key invoking the existing `toggleSchema` path).
- Native hide: route bank through the frontmatter ownership coordinator
  (`240q`) and title-slot adopter (`240k`) exactly as album does, with the
  same restore triggers (Source mode, file change, stale cache, failed
  mount, mobile, embeds/popovers/canvas/print, File Properties sidebar
  untouched). No new fallback logic.
- `_` dispatch: extend the `248m` keydown handler. Gate = the bare-key gate
  (`-`/`+` shape: Live Preview, Vim normal, empty buffer, no count/register,
  no operator, in-content) + `canAct` = a live bank/album card mount in the
  active view with a toggleable schema section (skip `loading`/`unsupported`/
  `mobile` bank states). Call the existing toggle entry points
  (`bankSetupToggleExpanded`, `albumHeaderSetExpanded`) so focus
  preservation and repaint batching come free. Never consume the key when the
  gate fails — Vim keeps its `_` motion everywhere else.
- Vim-conflict note: `_` in Vim is "first non-blank of current line". This
  is the same class of theft as `-`/`+` (line motions), already accepted in
  this exact context and only in this context. The gate's narrowness *is*
  the mitigation; document it in one line.

**Beautiful.** The folded states must look like siblings: `▸ Setup · 3
accounts · 12 categories · 2 rules` next to `▸ Schema · 5 fields · 142
records`. Checklist for the implementer: identical disclosure affordance
size/weight, identical muted-summary color, `aria-expanded` flip on both
(already present — verify), focus ring preserved after keyboard toggle (bank
repaint already restores `data-bank-setup-focus`; confirm the album repaint
restores `data-album-header-focus="summary"` on the same path), and no layout
shift in the queue/month cards below when Setup folds.

## Edge cases the implementer must cover

- `bank.md` in `invalid`/`missing`/`refresh-failed` states: invalid stays
  forced-open; missing keeps its starter-copy body behavior; `_` is a no-op
  (but never swallowed) where no toggle exists.
- Mobile, Reading-vs-Live-Preview, Source mode, embeds, popovers, canvas,
  print: unchanged fallbacks — native Properties return, `_` inert.
- Two panes on one note: per-path (not per-mount) state already shares
  correctly; toggling in one pane repaints both (same as `-` today).
- Vault `obsidian_vimrc` collisions: grep for existing `_`/`-`/`+` mappings
  before shipping; the capture-phase handler runs on `window`/`document`
  capture and must keep its `stopImmediatePropagation` discipline so a user
  `_` mapping doesn't double-fire.
- Tests: pure-model tests for default-collapsed + invalid-forces-open, gate
  tests for `_` (insert/visual/count/operator/Reading/untoggleable-state/
  modified keys all refuse without consuming), and a mount test that
  keyboard toggle produces the same signature as click toggle.

## Recommended solution

**Ship it in two slices, plugin-only, no bob CLI changes, no vault writes:**

1. **Slice A — bank becomes a proper property card, collapsed by default.**
   Enable title ownership + whole-frontmatter ownership for the bank host
   (album's `240k`/`240q` wiring, bank-scoped), flip
   `BANK_SETUP_DEFAULT_EXPANDED` to `false` (keep invalid-forces-open and the
   foot-outside-collapse), align the folded-line styling with the album
   schema summary, and document the new default. Gate everything on the
   kit's existing capability/source/cache evidence so any uncertainty
   restores today's rendering.
2. **Slice B — `_` toggles schema/Setup on bank + album.** Add the `_` arm
   to the `248m` dispatcher behind the bare-key gate plus a live-mount
   `canAct` (bank/album with a toggleable section only), calling the two
   existing toggle paths. Add the kbd hints, the docs row, and the gate
   tests. Explicitly out of scope: record/day/period cards, persisted fold
   state, any change to `==`/`-`/`+`.

This gives Bryan a quieter bank hub on every open, one memorable key for both
schema sections, and zero new fallback or sync machinery — the kit's proven
guarantees do the heavy lifting.
