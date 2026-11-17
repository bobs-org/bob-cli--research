---
title: "Schema Editing Cards: J/K & 1–9 Field Navigation, Index Badges, and Vertical Spacing Design"
author: research.gem
date: 2026-11-17
status: recommendation
scope:
  - bob-plugins/plugins/bob-ledger-tools (`AlbumSchemaCardModal`, `BankSetupCardModal`)
  - bob-plugins/docs/albums.md
---

# Schema Editing Cards: `J`/`K` & `1–9` Field Navigation, Index Badges, and Vertical Spacing Design

## Executive Verdict

Adding `J`/`K` field-to-field jumping, `1`–`9` direct field jumps with inline field index badges, and explicit vertical spacing before fields is a **high-value ergonomic upgrade** for [`AlbumSchemaCardModal`](../../linked/bob-plugins/plugins/bob-ledger-tools/src/241y-plugin-album-schema-card.js) (opened from both **album notes** and **record notes**). In schemas with multi-row `.bob-album-schema-choice-cloud` blocks—such as `Zettel` in [`~/bob/sase_blog_zettel.md`](/home/bryan/bob/sase_blog_zettel.md) and [`~/tmp/screenshots/20261117_110414.png`](/home/bryan/tmp/screenshots/20261117_110414.png)—stepping one target at a time with `j`/`k`/arrows forces up to 16 sequential presses just to cross `Section` (15 choices + `+ choice`). Visually, flex-margin non-collapse inside `.bob-album-schema-choice-cloud` makes intra-field chip rows (`0.50em`) look as far apart as—or **3.3x farther apart than**—the boundary before the next field (`0.50em` after choices, `0.15em` between `Claim` and `Section`).

However, inspecting the full `bob-ledger-tools` codebase and live vault configs surfaces **three critical adjustments** to the initial proposal:

1. **Scope divergence on `~/bob/bank.md` (`BankSetupCardModal`)**: `~/bob/bank.md` does **not** use `AlbumSchemaCardModal`; it opens [`BankSetupCardModal`](../../linked/bob-plugins/plugins/bob-ledger-tools/src/248k-plugin-bank-setup-card.js), which has 4 tabs (`Categories`, `Accounts`, `Rules`, `Checks`), no fields/choices, existing `[a-z0-9]/i` direct-jump hotkeys on category tiles (Bryan's own [`~/bob/bank.md`](/home/bryan/bob/bank.md#L24-L32) binds `"1"`–`"8"` to `Bills` categories and `"k"` to `🚗 Car`), pre-numbered `1..N` rows on `Rules`, and `0.55em` group margins. **`1`–`9` should NOT be added to `BankSetupCardModal`**, and `J`/`K` requires either making category hotkeys lowercase-first (jumping between category **group headers**) or keeping `BankSetupCardModal` out of scope.
2. **Existing bare-digit collision on `AlbumSchemaCardModal` (`schemaArrangeCountBuffer`)**: Bare `[0-9]` keys are currently swallowed silently by [`241yb-plugin-album-schema-arrange.js`](../../linked/bob-plugins/plugins/bob-ledger-tools/src/241yb-plugin-album-schema-arrange.js#L884-L890) as an invisible Vim count prefix for `Alt+J`/`Alt+K` (e.g., `4Alt+K`). Because visual `m` (`Move to…` gap hints) and `Alt+Shift+J/K` already supersede blind count prefixes—and no tests or status UI expose the buffer—**retire bare-digit `schemaArrangeCountBuffer`** so `1`–`9` execute instantaneously.
3. **Scroll-into-view, dirty-arrangement parity, and parent-first `K`**: Right now [`schemaFocusAfterPaint`](../../linked/bob-plugins/plugins/bob-ledger-tools/src/241yd-plugin-album-schema-card-paint.js#L96) focuses targets with `{ preventScroll: true }` and nothing calls `scrollIntoView` in the modal, [`schemaTargets`](../../linked/bob-plugins/plugins/bob-ledger-tools/src/241y-plugin-album-schema-card.js#L34-L36) ignores pending `Alt+J`/`Alt+K` field reorders (`projected.fields`), and `~/bob/subscriptions.md` already reaches 9 fields. Addressing these alongside parent-first `K` semantics makes navigation completely reliable.

---

## 1. Surface Mapping: Album Notes, Record Notes, and `~/bob/bank.md`

Every surface named in the request maps onto `bob-ledger-tools` through [`248m-plugin-schema-double-equals.js`](../../linked/bob-plugins/plugins/bob-ledger-tools/src/248m-plugin-schema-double-equals.js#L79-L89) and [`242d-plugin-album-entrypoints.js`](../../linked/bob-plugins/plugins/bob-ledger-tools/src/242d-plugin-album-entrypoints.js#L160-L277):

| Vault Note Surface | How Schema Card Opens | Modal Class | Linear Target Structure | Real Vault Inventory |
| --- | --- | --- | --- | --- |
| **Album notes** (`type: "[[album]]"`) | `==` (`248m`), `Edit album schema` command, or inline summary button | `AlbumSchemaCardModal` | `stats` → `field:*` / `choice:*` / `add-choice:*` → `add-field` / `issue:*` | 6 albums: 3–9 fields (`sase_blog_zettel.md` 3, `podcasts.md` 3, `eat.md` 5, `tv.md` 6, `movies.md` 7, `subscriptions.md` 9) |
| **Record notes** (parent album via `albumResolveSchemaTargetForFile`) | `Edit album schema` command (`242d`; `==` intentionally skips records so Vim reindent still works) | `AlbumSchemaCardModal` (exact same modal instance) | Identical to parent album above | All records inherit parent album schema |
| **`~/bob/bank.md`** | `==` (`248m`), `Edit bank setup` command, or header Edit button (`248l`) | `BankSetupCardModal` | 4 tabs (`categories`, `accounts`, `rules`, `checks`): `group` + `category` tiles; flat `account` / `rule` / `finding` lists | [`~/bob/bank.md`](/home/bryan/bob/bank.md): 1 account, 21 declared categories (+ built-ins) across `Money moves` / `Everyday` / `Bills`, 10 rules |

Because album notes and record notes open the exact same `AlbumSchemaCardModal`, implementing the new keymaps, badges, and spacing on `AlbumSchemaCardModal` covers both automatically. By contrast, `~/bob/bank.md`'s `BankSetupCardModal` has fundamentally different structure and existing keybindings.

---

## 2. Critique of the Plan & Explicit Adjustments

### Adjustment 1 (Major): Treat `BankSetupCardModal` (`~/bob/bank.md`) Differently from `AlbumSchemaCardModal`

Applying the literal spec (`J`/`K` + `1`–`9` + extra field spacing) to `BankSetupCardModal` would break existing workflows:

1. **Direct `1`–`9` collision with Category Hotkeys**: On the `Categories` tab, [`248k-plugin-bank-setup-card.js`](../../linked/bob-plugins/plugins/bob-ledger-tools/src/248k-plugin-bank-setup-card.js#L793-L796) dispatches `/[a-z0-9]/i` directly to `bankSetupCardSelectionByHotkey(this.categories, key)`. In [`~/bob/bank.md`](/home/bryan/bob/bank.md#L25-L32), **all 8 `Bills` categories use numeric hotkeys `"1"`–`"8"`** (`home: "1"` through `fees: "8"`). Each tile already renders `<kbd class="bob-bank-category-keycap">` in [`248b-plugin-bank-setup-dom.js`](../../linked/bob-plugins/plugins/bob-ledger-tools/src/248b-plugin-bank-setup-dom.js#L135-L143). Rebinding `1`–`9` to groups or rows would break `"1"`–`"8"` category selection and visually compete with existing keycaps.
2. **Case-insensitive `"K"` collision**: Because `248k` L793 matches `/[a-z0-9]/i` and `bankSetupCardSelectionByHotkey` (`248i` L124) lowercases the key, pressing `Shift+K` (`K`) on `~/bob/bank.md` currently selects `🚗 Car` (`hotkey: k`), and `BankSetupCardModal` intentionally does **not** bind lowercase `j`/`k` so letters remain free for categories.
3. **Different visual hierarchy across tabs**: `Categories` already paints `<section class="bob-bank-setup-card-group">` with `margin: 0.55em 0;` ([`styles.css`](../../linked/bob-plugins/plugins/bob-ledger-tools/styles.css#L9836)), small-caps group headings, and `0.25rem` tile top spacing. `Rules` already renders explicit 1-based ordinal prefixes (`${position + 1} ...` in [`248j` L434](../../linked/bob-plugins/plugins/bob-ledger-tools/src/248j-plugin-bank-setup-card-dom.js#L434)), while `Accounts` and `Checks` are short flat lists navigated with `↑`/`↓`/`Ctrl+N`/`Ctrl+P`.

**Adjustment recommended for `~/bob/bank.md` (`BankSetupCardModal`)**:
- **Do NOT add `1`–`9` or numeric badges to `BankSetupCardModal`**: Preserve `1`–`9` exclusively for category hotkeys (`Categories` already gives single-key access to every tile; `Rules` already displays row numbers `1..N`).
- **Evaluate `J`/`K` on `Categories` tab (two clean options)**:
  - **Option B1 (Cross-card `J`/`K` symmetry)**: Restrict category hotkey matching in `248k` L793 to unshifted lowercase/digit keys (`/[a-z0-9]/` without `/i`—safe because bank hotkeys normalize to lowercase in [`248i` L164](../../linked/bob-plugins/plugins/bob-ledger-tools/src/248i-plugin-bank-setup-card-model.js#L164)), and bind `J`/`K` on the `Categories` tab to jump between `type: "group"` headers (`Money moves` ↔ `Everyday` ↔ `Bills` ↔ `HIDDEN`), which currently require arrowing through tiles to reach for `Enter` rename or `Alt+J/K` group reorder. Optionally bump `.bob-bank-setup-card-group:not(:first-child)` slightly from `0.55em` to `0.8em` if extra breathing room is desired.
  - **Option B2 (Album-only scope — simpler, zero hotkey surprise)**: Leave `BankSetupCardModal` untouched so `/i` still tolerates accidental CapsLock on category tiles, and scope `J`/`K`, `1`–`9`, index badges, and vertical spacing solely to `AlbumSchemaCardModal` where there are no tile hotkeys and wrapped chip clouds create real navigation friction.
  - **Recommendation**: **Adopt Option B2 initially** (or ship **Option B1** only if jumping directly to `Everyday`/`Bills` group headers without arrowing through tiles is a felt pain point). Either way, **never** override `1`–`9` on `BankSetupCardModal`.

---

### Adjustment 2 (Critical): Retire `schemaArrangeCountBuffer` (`4Alt+K`) So `1`–`9` Are Instant

Inspection of [`241yb-plugin-album-schema-arrange.js`](../../linked/bob-plugins/plugins/bob-ledger-tools/src/241yb-plugin-album-schema-arrange.js#L81-L87) reveals an existing bare-digit listener that directly blocks `1`–`9` navigation:

- Lines 884–890 intercept every unmodified `[0-9]` keydown when `!this.stage && !inInput` and append it to `this.schemaArrangeCountBuffer` (up to 3 digits, no timeout, no status-bar feedback, and only cleared by `schemaArrangeConsumeCount` when `Alt+J`/`K`/`Arrows` fires).
- [`docs/albums.md`](../../linked/bob-plugins/plugins/bob-ledger-tools/docs/albums.md#L136) currently mentions: *"a count prefix such as `4Alt+K` repeats the nudge"*.
- Neither `BankSetupCardModal` (`248ka`) nor any `test-ledger-tools-album*` keydown test exercises digit count buffering.

| Approach for `1`–`9` vs `schemaArrangeCountBuffer` | Pros | Cons | Verdict |
| --- | --- | --- | --- |
| **A. Retire bare-digit count buffer; assign `1`–`9` strictly to field jump** | Zero latency on `1`–`9`; matches prompt & Copy Card / Decision Card `1`–`9` ergonomics; eliminates silent invisible state bug where stray digits linger indefinitely; `m` gap hints + `Alt+Shift+J/K` already handle multi-slot moves better visually | Removes undocumented-in-UI `4Alt+K` chord (requires 1-line `docs/albums.md` update) | **Recommended** |
| **B. Prefix (`g1`–`g9`) or modifier (`Alt+1-9`, `Ctrl+1-9`)** | Preserves `4Alt+K` | Violates prompt (`1-9` directly); `Ctrl+1-9` collides with Obsidian window/tab jumping (`bob-navigation-hotkeys`); `Alt+1-9` types glyphs on macOS unless matched via `event.code` | Reject |
| **C. Disambiguate with timeout or pending-move state** | Attempts both | Waiting breaks instant snap; jumping to field `4` before `Alt+K` would move field `4` instead of current item | Reject |

**Adjusted Requirement**: Explicitly retire `schemaArrangeCountBuffer` / `schemaArrangeConsumeCount` in `241yb` and update `docs/albums.md` L136 to keep `m` (`Move to…`), `Alt+Shift+J/K`, and drag-and-drop as the multi-slot reorder mechanisms. Leave `0` unbound (do not hijack `0` for a 10th field, and don't add surprise behavior unless a dedicated "top/`stats`" key like `0` is explicitly wanted later).

---

### Adjustment 3 (Behavioral & Reliability): Exact `J`/`K`, `1`–`9`, Dirty-Arrange, and Scroll Rules

To make keyboard navigation rock-solid under every state in `AlbumSchemaCardModal`, refine the navigation state machine as follows:

1. **Parent-first `K` from inside choice clouds**:
   - **Rule for `J` (next field)**: From `stats`, jump to **Field 1**. From Field `i`, any `choice` of Field `i`, or `add-choice` of Field `i`, jump to **Field `i + 1`** (wrapping from Field `N` to **Field 1**). From `add-field` or `issue:*`, wrap to **Field 1**.
   - **Rule for `K` (previous field)**:
     - If currently on a **child target belonging to Field `i`** (`choice:<field>:<val>` or `add-choice:<field>`), jump **up to owning Field `i` itself** (not `i - 1`). *Why*: Visually in `Zettel`, when cursor is on the 4th chip row of `Section` (`🔮 Future Work` or `+ choice`), `Section` IS the field row directly above the cursor—reaching it in one `K` to hit `!`, `s`, `a`, `⏎`, or `⌥J/K` avoids overshooting up to `Claim` and arrowing back down through 15 chips. Pressing `K` a second time on `Section` then moves up to `Claim`.
     - If currently on Field `i`, jump to **Field `i - 1`** (wrapping from Field `1` to **Field `N`**).
     - If on `stats`, wrap to **Field `N`**. If on `add-field` or `issue:*` (below all fields), jump up to **Field `N`**.
   - *(Note: circular wrapping among fields matches `schemaMove(delta)` in [`241y` L70](../../linked/bob-plugins/plugins/bob-ledger-tools/src/241y-plugin-album-schema-card.js#L70). If hard stops at Field `1` and Field `N` are preferred over wrapping, that is a 1-line toggle in the helper.)*

2. **Empty, single-field, `> 9` fields, and out-of-range digits**:
   - **0 fields**: `J`/`K` and `1`–`9` are clean no-ops (leave selection untouched on `stats` or `add-field`).
   - **1 field**: From `stats`/`add-field`/`choice:*`/`add-choice:*`, `J`/`K` focus Field 1; when already on Field 1, `J`/`K` are quiet no-ops (avoid redundant DOM repaints).
   - **Fields `10+`**: [`~/bob/subscriptions.md`](/home/bryan/bob/subscriptions.md#L15-L38) already has **9 fields** (`status`, `amount`, `cadence`, `pricing`, `match`, `category`, `url`, `renews`, `ended`), so 10-field albums are realistic. Only fields `1`–`9` display a keycap badge (`1`–`9`). Never render a misleading `10` badge that cannot be typed with one key; fields `10+` remain navigable via `J`/`K`, `j`/`k`, arrows, and click.
   - **Out-of-range digit (e.g., pressing `4`–`9` on 3-field `Zettel`)**: Strict no-op (never clamp `9` down to Field 3, consistent with [`test-navigation-decision-card.cjs`](../../linked/bob-plugins/scripts/test-navigation-decision-card.cjs#L484) and [`docs/copy-card.md`](../../linked/bob-plugins/docs/copy-card.md)).

3. **Respect projected `Alt+J`/`Alt+K` field order before saving**:
   - Right now [`albumSchemaCardPaintBody`](../../linked/bob-plugins/plugins/bob-ledger-tools/src/241yc-plugin-album-schema-card-regions.js#L301-L303) renders fields in `projected.fields` order when `arrange?.dirty` is true, while [`schemaTargets()`](../../linked/bob-plugins/plugins/bob-ledger-tools/src/241y-plugin-album-schema-card.js#L34-L36) still reads raw `model.fields`.
   - If a user moves `Section` above `Claim` with `Alt+K` (pending save), visually `Section` is now `2` and `Claim` is `3`. **A single shared helper `albumSchemaOrderedFields(model, projected)` MUST drive badge numbering (`1`–`9`), `1`–`9` key jumps, and `J`/`K` stepping** (and ideally `schemaTargets()` too so `j`/`k`/arrows don't jump backward during pending moves!). And navigation (`1`–`9`, `J`/`K`) MUST stay active when `schemaArrangeDirty()` is true—never flash-block navigation!

4. **Modifier & modal-state guardrails**:
   - **Allow `1`–`9` and `J`/`K` ONLY when**: `!this.stage`, `!this.schemaHintMode`, `!inInput`, `this.sessionState?.status !== "applying"`, `!this.schemaMoreOpen` (if More actions popover is open—or close/respect it cleanly), and `!event.isComposing && event.keyCode !== 229`.
   - **Exact key matching**:
     - `J` / `K`: `!event.altKey && !event.ctrlKey && !event.metaKey && (event.key === "J" || event.key === "K")` (notice `event.shiftKey` IS `true` for uppercase `J`/`K`, while `Alt+J`/`K` and `Alt+Shift+J/K` remain handled earlier for item/edge moving!).
     - `1`–`9`: `!event.altKey && !event.ctrlKey && !event.metaKey && !event.shiftKey && /^[1-9]$/.test(event.key)` (checking `!event.shiftKey` + `event.key` guarantees `Shift+1` → `!` continues toggling `required` at `241y` L874!).

5. **Scroll-into-view fix for tall cards**:
   - Currently [`241yd` L96](../../linked/bob-plugins/plugins/bob-ledger-tools/src/241yd-plugin-album-schema-card-paint.js#L96) calls `selected?.focus?.({ preventScroll: true })`, and `rg -n scrollIntoView` confirmed **no code in `bob-ledger-tools` scrolls selected schema targets into view** inside the modal. On 6–9 field schemas (`TV`, `Movies`, `Subscriptions`) or multi-cloud schemas (`Zettel`), jumping straight to Field 7–9 will focus an off-screen button unless `paintSchemaCard("select")` scrolls it into view (`selected.scrollIntoView?.({ block: "nearest", inline: "nearest" })`, mirroring [`103-copy-card-modal.js`](../../linked/bob-plugins/plugins/bob-navigation-hotkeys/src/103-copy-card-modal.js#L327)). Scroll only on explicit selection movement (`reason === "select"`), never during `session` preview updates.

---

## 3. Visual & Spatial Design ("Intuitive, Reliable, Beautiful")

### Root Cause of Current Crowding (Verified in `styles.css`)

In [`plugins/bob-ledger-tools/styles.css`](../../linked/bob-plugins/plugins/bob-ledger-tools/styles.css#L8623) and [`L8773–L8804`](../../linked/bob-plugins/plugins/bob-ledger-tools/styles.css#L8773-L8804):

```text
Status (field row)            ── margin-bottom: 0.15em
  └─ +0.15em cloud margin-top + 0.15em flex child margin-top = 0.30em
🌱 Seed ... ⏭️ Later (row 1)
  └─ 0.15em chip bottom + 0.20em flex row-gap + 0.15em chip top = 0.50em  ◄── intra-field gap
✂️ Cut 0   [+ choice] (row 2)
  └─ 0.15em chip bottom + max(0.35em cloud bottom, 0.15em field top) = 0.50em ◄── inter-field gap == intra-field!
Claim (field row, no choices)
  └─ max(0.15em, 0.15em) block collapse = 0.15em                          ◄── choice-less inter-field is 3.3x TIGHTER!
Section (field row)
```

Because flexbox children (`.bob-album-schema-choice-button` and `.bob-album-schema-add-choice` with `margin: 0.15em 0.2em 0.15em 0;`) do **not** collapse their vertical margins with `.bob-album-schema-choice-cloud`'s `gap: 0.2em` or `.bob-album-schema-choice-cloud`'s outer margins, two wrapped lines of chips inside one field sit **0.50em** apart—the exact same vertical distance that separates `Status`'s last chip from `Claim`, while choice-less `Claim` collapses to just **0.15em** above `Section`. That directly explains the visual ambiguity visible in [`20261117_110414.png`](/home/bryan/tmp/screenshots/20261117_110414.png).

### Constraint 1: Keep Flat DOM & Dialog-Only CSS Scope

Two existing invariants prevent wrapping each field + choice cloud in a `<section>` wrapper:
1. [`albumSchemaCardInsertGhost`](../../linked/bob-plugins/plugins/bob-ledger-tools/src/241yc-plugin-album-schema-card-regions.js#L82-L102) scans `Array.from(host.children || [])` directly on `.bob-album-schema-dialog-body`, and [`albumSchemaCardPaintBody`](../../linked/bob-plugins/plugins/bob-ledger-tools/src/241yc-plugin-album-schema-card-regions.js#L317) inserts `m` (`move to…`) gap buttons as direct siblings in `host`.
2. [`schemaDragPaintCaret`](../../linked/bob-plugins/plugins/bob-ledger-tools/src/241xb-plugin-schema-arrange-dom.js#L482-L497) relies on `[data-drag-scope]` / `[data-arrange-id]` in the flat body tree.
3. [`241x-plugin-album-schema-dom.js`](../../linked/bob-plugins/plugins/bob-ledger-tools/src/241x-plugin-album-schema-dom.js#L21) reuses `.bob-album-schema-field` for the compact **inline note header** (`bob-album-schema-card`) visible behind the modal in the screenshot.

**Design consequence**: Achieve all vertical spacing strictly through **CSS scoped to `.bob-album-schema-dialog-body`**, keeping DOM flat and leaving the inline header untouched.

### Spacing Rhythm Design (~3.5:1 Gestalt Proximity Ratio)

Inside `.bob-album-schema-dialog-body` only:
- **Zero redundant chip margins inside the cloud**: Change `.bob-album-schema-dialog-body .bob-album-schema-choice-button` and `.bob-album-schema-add-choice` to `margin: 0;` and let `.bob-album-schema-choice-cloud` own spacing via `gap: 0.26em 0.28em; margin: 0.24em 0 0;`. Wrapped chip rows stay tight and cozy (`0.26em`), and the cloud hugs its own parent field (`0.24em`).
- **Clear separation *before* fields (2..N), `+ field`, and issues**:
  - Give `.bob-album-schema-dialog-body > .bob-album-schema-field` base `margin: 0;` (so Field 1 sits crisply right under the `0.55em` dialog-body top offset below `4 zettels · dated notes` without excessive top bloat).
  - Add generous top spacing before every subsequent field and `+ field`:
    ```css
    .bob-album-schema-dialog-body > .bob-album-schema-field:not(:first-child),
    .bob-album-schema-dialog-body > .bob-album-schema-add-field:not(:first-child) {
      margin-top: 0.9em;
    }
    /* Keep m (move to...) gap-hint before field 1 tight, and give gap hints modest breathing room */
    .bob-album-schema-dialog-body > .bob-album-schema-gap-hint + .bob-album-schema-field {
      margin-top: 0.35em;
    }
    ```
  - Notice why **pure whitespace (`0.9em` vs `0.24em` cloud attachment, a 3.75:1 ratio)** beats adding `border-top` hairlines on field buttons: `<button class="bob-album-schema-field">` already has rounded corners (`border-radius: 6px`), a light background pill, and a 2px `--interactive-accent` ring when `.is-selected`; a top border rule would clip at rounded corners or visually fight the selection ring. Even on 9-field `subscriptions.md`, adding ~`0.55em` net height per field adds only ~`4.4em` (~62px), keeping normal albums compact while eliminating every trace of Gestalt ambiguity.

### Index Keycap Badge Design (`1`–`9`)

Every field row inside `albumSchemaCardPaintFieldRow` (`241yc` L169–180) currently renders:

```text
[ ⠿ grip (opacity:0 until hover/focus) ] [ .bob-album-schema-field-main ] [ set on 4 of 4 ]
```

Observe in [`20261117_110414.png`](/home/bryan/tmp/screenshots/20261117_110414.png) that `.bob-album-schema-grip` holds a constant left-gutter width (`opacity: 0` at rest, `margin-right: 0.3em` in `styles.css` L9372–9387), so `Status`, `Claim`, and `Section` labels already align on the same vertical axis.

**Where to place the badge**: Insert `<kbd class="bob-album-schema-field-index" aria-hidden="true">1</kbd>` as the **first child of `.bob-album-schema-field-main`**, immediately before `.bob-album-schema-label` (for `1 <= fieldNumber <= 9`), and set `aria-keyshortcuts="{n}"` on the `<button>` row:

```text
  ╭─────────────────────────────────────────────────────────────────────╮
  │ ⠿  [1] Status  (required)                             set on 4 of 4 │  ◄── selected: purple ring + accent keycap
  ╰─────────────────────────────────────────────────────────────────────╯
       🌱 Seed 0   ✍️ Draft 4   ✅ Ready 0   📌 Placed 0   ⏭️ Later 0
       ✂️ Cut 0    + choice

       [2] Claim   (required) (text) (sub-groups index)   set on 4 of 4    ◄── clear 0.9em top gap!

       [3] Section (sub-groups index)                     set on 4 of 4
       🪝 Intro 0  🧱 What is SASE? 1  📜 Prompt language (macros) 1
       ...
       + choice

       + field
```

**Why this placement & visual styling works**:
- **Matches the Bob keycap family**: Mirrors `.bob-copy-card-key` (`bob-navigation-hotkeys/styles.css` L2236–2257), `.bob-bank-category-keycap` (`bob-ledger-tools/styles.css` L9587), and `.bob-album-schema-hint kbd` (`styles.css` L9287–9299):
  - Compact tabular monospace keycap (`min-width: 1.45em; height: 1.45em; padding: 0 0.28em; display: inline-flex; align-items: center; justify-content: center;`).
  - Subtle at rest (`border: 1px solid var(--background-modifier-border); border-radius: 4px; background: var(--background-secondary); color: var(--text-muted); font-family: var(--font-monospace, ui-monospace, monospace); font-size: 0.78em; font-weight: 600; font-variant-numeric: tabular-nums;`) so keycaps don't scream louder than the field labels or emoji choices.
  - Accent-highlighted when selected (`.bob-album-schema-field.is-selected .bob-album-schema-field-index { border-color: var(--interactive-accent); color: var(--interactive-accent); }`, directly matching `.bob-copy-card-row.is-selected .bob-copy-card-key`).
- **No horizontal jump with `⠿`**: Because `⠿` stays outermost on the left gutter (`opacity: 0` → `1`), hovering or focusing any field never collides with or shifts `[1]`..`[9]`.
- **No visual collision with `↑2`/`↓1` arrange badges**: Reorder delta pills (`.bob-album-schema-delta-badge`) append at the trailing edge of `.bob-album-schema-field`, well away from the leading keycap.
- **Unnumbered past 9**: Fields 10+ omit the keycap entirely, signaling honestly that only `1`–`9` have direct jump keys while keeping `.bob-album-schema-field-main` cleanly aligned at the grip gutter edge.

### Footer Hint Strip Fit

In [`styles.css` L9272–9279](../../linked/bob-plugins/plugins/bob-ledger-tools/styles.css#L9272-L9279), `.bob-album-schema-hint-strip` enforces `max-height: 3.1em; overflow: hidden;` (a hard **2-line cap**!). Currently, on a field target in `20261117_110414.png`, Line 1 holds 8 hints and Line 2 holds only `esc close` + `...` (~75% empty width).

- Adding **one compact hint** `{ keys: "1–9/J/K", label: "field" }` (or `{ keys: "J/K", label: "field" }` when the `1`–`9` badges on every row already self-teach digits—just like Copy Card and Bank Setup!) fits cleanly on Line 2 even when `u undo` and `⏎ apply` appear, without clipping `esc/q close` or `...`.
- In read-only modal mode (`!editable`, [`241yc` L717–723](../../linked/bob-plugins/plugins/bob-ledger-tools/src/241yc-plugin-album-schema-card-regions.js#L717-L723)), update `{ keys: "↑/↓", label: "navigate" }` to `{ keys: "↑/↓/J/K", label: "field" }` (and render keycaps + enable `1`–`9` / `J`/`K` on read-only fields too so navigation behaves identically!).

---

## 4. Recommended Implementation Blueprint (`bob-plugins`)

Per [`bob-plugins/AGENTS.md`](../../linked/bob-plugins/AGENTS.md), every hand-edited fragment under `src/` must stay **≤ 1000 lines**. Because [`241y-plugin-album-schema-card.js`](../../linked/bob-plugins/plugins/bob-ledger-tools/src/241y-plugin-album-schema-card.js) is already **953 lines** and [`241yb-plugin-album-schema-arrange.js`](../../linked/bob-plugins/plugins/bob-ledger-tools/src/241yb-plugin-album-schema-arrange.js) is **949 lines**, place shared pure helpers in [`242c-plugin-album-schema-edit.js`](../../linked/bob-plugins/plugins/bob-ledger-tools/src/242c-plugin-album-schema-edit.js) (currently **250 lines**) and paint helpers in [`241yc`](../../linked/bob-plugins/plugins/bob-ledger-tools/src/241yc-plugin-album-schema-card-regions.js) (**928 lines**) / [`241yd`](../../linked/bob-plugins/plugins/bob-ledger-tools/src/241yd-plugin-album-schema-card-paint.js) (**200 lines**).

### A. Shared Target & Field-Order Helpers (`242c-plugin-album-schema-edit.js`)

Add small pure functions in `242c`:

1. **`albumSchemaOrderedFields(model, projected)`**:
   - Returns `model.fields` reordered by `projected.fields` (when `projected?.fields` is present and valid), preserving every field object. Shared by **both** `albumSchemaCardPaintBody` (so badges `1`–`9` always match display order) and `schemaTargets()` (fixing `j`/`k`/arrow drift during dirty `Alt+J/K` arrangements too!).
2. **`albumSchemaFieldKeys(model, projected)`**:
   - Returns `albumSchemaOrderedFields(model, projected).map((f) => ` + `` `field:${f.key}` `` + `)`.
3. **`albumSchemaStepFieldKey(model, currentKey, delta, projected)`** and **`albumSchemaDigitFieldKey(model, digit, projected)`**:
   - `albumSchemaDigitFieldKey`: Parses `"1"`..`"9"` → 0-based `index = Number(digit) - 1`; returns `fieldKeys[index] || null` if `index < fieldKeys.length && index < 9`, else `null`.
   - `albumSchemaStepFieldKey`:
     - If `!fieldKeys.length`, return `null`.
     - Parse current target via `albumSchemaTargetByKey(model, currentKey)`:
       - **On `"field"`**: find `pos = fieldKeys.indexOf(currentKey)`; return `fieldKeys[(pos + delta + fieldKeys.length) % fieldKeys.length]`.
       - **On `"choice"` or `"add-choice"`** (belongs to `target.field.key`):
         - If `delta < 0` (`K`): return owning `` `field:${target.field.key}` `` (**parent-first**!).
         - If `delta > 0` (`J`): find `pos = fieldKeys.indexOf(` + `` `field:${target.field.key}` `` + `)`; return `fieldKeys[(pos + 1) % fieldKeys.length]`.
       - **On `"stats"`**: `delta > 0` (`J`) → `fieldKeys[0]`; `delta < 0` (`K`) → `fieldKeys[fieldKeys.length - 1]`.
       - **On `"add-field"` or `"issue"`**: `delta > 0` (`J`) → `fieldKeys[0]`; `delta < 0` (`K`) → `fieldKeys[fieldKeys.length - 1]`.

### B. Controller, Scroll, & Keydown Wiring (`241y`, `241yb`, `241yd`)

1. **`241y-plugin-album-schema-card.js`**:
   - Helper methods on `AlbumSchemaCardModal`:
     - `schemaMoveField(delta)` / `schemaJumpFieldNumber(digit)` using `this.schemaProjectedScopes()` (when `this.schemaArrangeDirty?.()`), calling `this.schemaSelect(nextKey)`.
     - Update `schemaTargets()` to pass projected field/choice order when `schemaArrangeDirty()` is true.
   - In `schemaOnKeyDown(event)` (after close keys and `Alt+J/K`, before `a`/`c`/`!`):
     - If `!event.altKey && !event.ctrlKey && !event.metaKey && !this.schemaMoreOpen`:
       - `if (event.key === "J") { event.preventDefault?.(); this.schemaMoveField(1); return; }`
       - `if (event.key === "K") { event.preventDefault?.(); this.schemaMoveField(-1); return; }`
       - `if (!event.shiftKey && /^[1-9]$/.test(event.key)) { event.preventDefault?.(); this.schemaJumpFieldNumber(event.key); return; }` (checking `!event.shiftKey` preserves `Shift+1` → `!` for `required`!).
2. **`241yb-plugin-album-schema-arrange.js`**:
   - Remove the `^[0-9]$` `schemaArrangeCountBuffer` capture at lines 884–890 and simplify `schemaArrangeConsumeCount` / `schemaArrangeNudge` to step by `1` (retiring `4Alt+K`).
   - Optionally expose `schemaProjectedScopes()` cleanly so `241y` stays comfortably below `1000` lines.
3. **`241yd-plugin-album-schema-card-paint.js`**:
   - In `paintSchemaCard("select")`: pass `{ scrollIntoView: true }` to `schemaFocusAfterPaint(false, { scrollIntoView: true })`, and after `selected?.focus?.({ preventScroll: true })` run:
     ```js
     if (scrollIntoView && selected && typeof selected.scrollIntoView === "function") {
       try { selected.scrollIntoView({ block: "nearest", inline: "nearest" }); } catch (_) {}
     }
     ```
   - Notice read-only modal parity: if `!this.session` (`editable === false`), keep `selectedIndex` synchronized with `field` index (or paint `data-target-key` / use `fieldIndex`) so `J`/`K`/`1-9` highlight read-only fields identically.

### C. DOM & Hint Strip (`241yc-plugin-album-schema-card-regions.js`)

1. **`albumSchemaCardPaintBody` & `albumSchemaCardPaintFieldRow`**:
   - Use `albumSchemaOrderedFields(model, projected)` and pass `{ ...itemOptions, fieldNumber: index + 1 }` (for both editable and read-only paint loops).
   - Inside `albumSchemaCardPaintFieldRow`: when `Number.isInteger(options?.fieldNumber) && options.fieldNumber >= 1 && options.fieldNumber <= 9`, prepend `<kbd class="bob-album-schema-field-index" aria-hidden="true">${options.fieldNumber}</kbd>` to `main` (before `label`) and set `row.setAttribute("aria-keyshortcuts", String(options.fieldNumber))` when editable.
2. **`albumSchemaCardHintItems`**:
   - Add `{ keys: "1–9/J/K", label: "field" }` when `(model?.fields || []).length > 0` (and in read-only mode, `{ keys: "↑/↓/J/K", label: "field" }` when non-empty).

### D. Styling (`plugins/bob-ledger-tools/styles.css`)

```css
/* Dialog-only field separation & cloud tightness (leaves inline 241x header compact) */
.bob-album-schema-dialog-body > .bob-album-schema-field {
  margin: 0;
}
.bob-album-schema-dialog-body > .bob-album-schema-field:not(:first-child),
.bob-album-schema-dialog-body > .bob-album-schema-add-field:not(:first-child) {
  margin-top: 0.9em;
}
.bob-album-schema-dialog-body > .bob-album-schema-gap-hint + .bob-album-schema-field {
  margin-top: 0.35em;
}
.bob-album-schema-dialog-body .bob-album-schema-choice-cloud {
  margin: 0.24em 0 0;
  gap: 0.26em 0.28em;
}
.bob-album-schema-dialog-body .bob-album-schema-choice-button,
.bob-album-schema-dialog-body .bob-album-schema-add-choice {
  margin: 0;
}

/* Field shortcut index keycap (matches bank-category-keycap / copy-card-key family) */
.bob-album-schema-field-index {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 auto;
  min-width: 1.45em;
  height: 1.45em;
  padding: 0 0.28em;
  border: 1px solid var(--background-modifier-border);
  border-radius: 4px;
  background: var(--background-secondary);
  color: var(--text-muted);
  font-family: var(--font-monospace, ui-monospace, monospace);
  font-size: 0.78em;
  font-weight: 600;
  line-height: 1.2;
  font-variant-numeric: tabular-nums;
}
.bob-album-schema-field.is-selected .bob-album-schema-field-index {
  border-color: var(--interactive-accent);
  color: var(--interactive-accent);
}
```

### E. Docs & Verification Plan

1. **Docs**: Update `plugins/bob-ledger-tools` documentation in [`docs/albums.md`](../../linked/bob-plugins/docs/albums.md#L133-L144) to add `J`/`K` (previous/next field) and `1`–`9` (direct field jump), replacing the `4Alt+K` count-prefix phrase with `m` / `Alt+Shift+J/K`.
2. **Unit & DOM Tests** (add to `scripts/test-ledger-tools-album-schema-card-shell.cjs` and `test-ledger-tools-album-schema-arrange-card.cjs`):
   - `J`/`K` from `stats`, between fields, parent-first `K` from `choice:*` / `add-choice:*`, wrapping from last field / `add-field` / `issue:*`, 0-field and 1-field no-ops.
   - `1`–`9` jumping directly to Field 1–9, ignoring `9` on a 3-field album, rendering keycaps ONLY on fields `1`–`9` (test 10+ fields), NOT breaking `Shift+1` (`!`) toggle-required, and staying ignored inside `this.stage`, `this.schemaHintMode`, `this.schemaMoreOpen`, and text inputs.
   - Dirty `Alt+J`/`Alt+K` reorder updates badge numbering `1`–`9` and `1`–`9`/`J`/`K` targets immediately before save.
   - `paintSchemaCard("select")` invokes `scrollIntoView({ block: "nearest", inline: "nearest" })`.
3. **Build & Sync Commands**:
   - `npm run build` → `npm test` → `npm run docs:check` → `bob plugins sync`.
