# Schema Editors: Instant Multi-Slot Reorder and a Real Emoji Picker (cld)

Research for making the album Schema Card and the Bank Setup card faster and easier to
use, prompted by `~/tmp/screenshots/20261116_134836.png` (album schema editor, "Add
choice" stage with an empty `Choice emoji` text box).

**Recommendation in one paragraph.** Separate composing an edit from committing it.
Reordering should happen locally and instantly on a *projected* model, so Alt+J/K, a
count, or a hint-letter jump moves the chip on screen with no bob call. One bob
transaction then saves the whole arrangement: one multi-op envelope, one preview, one
commit, one Undo. The save runs in the background while the card already shows the result.
"Add choice" should also place the new choice (a ghost chip you position before saving),
so add-then-move-four-times becomes one gesture and one commit. Emoji entry becomes a
shared **Emoji Slot**: a glyph button fused to the label, plus an inline grid palette.
It searches the existing `bob-emoji` catalog and recents through a new versioned
`bob-emoji` API. It suggests emoji from the label's words and from emoji already used in
your albums, warns about duplicates in the same field, and still accepts pasted or OS-picker
emoji. Enrich the catalog with Unicode CLDR keywords so filtering finds what people
actually type. Use the same two components in the Bank Setup card. The bob-cli changes
are optional performance trims, done after the UI work.

---

## 1. What I examined

- **Album card (bob-plugins `bob-ledger-tools`)**:
  - `src/241y-plugin-album-schema-card.js`: the controller.
  - `src/241y-plugin-album-schema-card-dom.js`: the card DOM.
  - `src/242c-plugin-album-schema-edit.js`: targets and stage controls.
  - `src/242aa-plugin-guarded-update-session.js`: the shared preview/apply session.
  - `src/242a-plugin-album-update-service.js` and `src/241z-plugin-album-update.js`: the
    writer service and wire.
- **Bank card**:
  - `src/248i-plugin-bank-setup-card-model.js`: the move ops.
  - `src/248k-plugin-bank-setup-card.js`: the gesture flow and the Alt+J/K move.
  - `src/248g-plugin-bank-category-new-stage.js`: the label input, placeholder
    `e.g. 🍔 Fast food`.
- **Emoji**: the `bob-emoji` plugin.
  - `src/030-emoji-model.js`: the index, ranking and recents.
  - `src/040-emoji-suggest.js`: the `:shortcode` EditorSuggest.
  - `vendor/gemoji-emoji.json`: 1,870 entries.
  - The plugin is enabled in the vault and its recents are persisted in `data.json`.
- **bob-cli writer**:
  - `src/native/albums/update/run.rs`: preflight, then `run_locked`, then verify.
  - `src/native/host_catalog/txn.rs`: `run_locked` with a pre-sync and a post-sync
    `sync_cycle`.
  - `src/native/albums/grouping.rs`: `group_field` is `status`, otherwise the first
    choices field.
  - `src/native/bank/config_update/protocol.rs`: `category.move`, `group.move` and
    `account.move` take a `before`/`after` anchor; `rule.move` takes a `position`.
- **Measurements on apollo** (vault of 7,293 notes, read-only commands only):
  - `bob albums update -d` dry-runs.
  - `bob albums list -f json`.
  - The vault-sync status record.
- **Vault git history** of `~/bob/sase_blog_zettel.md`.
- **Prior research**: `202611/album_record_schema_ux/album_record_schema_ux__final.md`.
  It established "one gesture = one scoped commit" and left commit granularity as an
  open question for Bryan.

## 2. Diagnosis

### 2.1 Why moves go one slot at a time (root cause, not just slowness)

`schemaMoveSelected(direction)` computes the target position from `this.schemaModel`,
which is the **server** model, and stages it with `setDraft([op])`. That *replaces* the
draft:

```js
const index = choices.findIndex((choice) => choice.value === target.choice.value);
const next = index + direction;            // always relative to the server order
this.schemaQueueOp({ op: "choice.move", …, position: next }, target.key);
```

The card also paints `this.schemaModel`, not the draft. So:

1. Pressing Alt+K twice before applying stages the *same* op (`position = server − 1`),
   so a second press is a no-op.
2. The chip row never shows the pending order. The only "preview" is a consequence
   sentence: `move choice "close" on "section" 14→13`.
3. Each slot therefore costs a full cycle: Alt+K, wait for the debounced preview, Enter,
   wait for apply and the report refresh, then re-select.

The Bank Setup card has the same shape: `beginGesture` opens a confirm stage per move
and refuses a second gesture while a stage is open.

**The wire already supports arbitrary moves and batches.** On the real album, I
measured three read-only dry-runs:

| Envelope | Wall time | Result |
|---|---|---|
| `choice.move close → 13` (one slot) | 1.09 s | ok, inverse `→14` |
| `choice.move close → 0` (14 slots) | 1.00 s | ok, inverse `→14` |
| 3 ops (two choice moves + a field move) | 1.15 s | ok, 3 inverse ops in reverse order, one consequence line |

A 14-slot move costs the same as a 1-slot move, and three ops cost the same as one.
Ops apply sequentially (op 2's `14→1` is relative to op 1's result), and `inverse_ops`
come back in undo order. **Phase 1 of this design needs no bob-cli change.**

### 2.2 Where the seconds go (per Apply, today)

| Step | Cost on apollo | Source |
|---|---|---|
| Debounced preview (`-d`): full vault snapshot, registry, plan | 0.25 s + ~1.0 s | measured (0.93–1.09 s) |
| Apply: preflight plan outside the lock | ~1.0 s | same planner as the dry run |
| Pre-sync `sync_cycle` (git, network) | ~0.8 s | last vault-sync cycle: `duration_ms: 796` |
| Fresh plan inside the lock | ~1.0 s | same planner |
| Write, commit, `verify_installed` (re-scans the whole vault) | ~0.6–1.0 s | `albums check` ≈ 0.55 s, same scan |
| Post-sync `sync_cycle` | ~0.8 s | same |
| Plugin forces `bob albums list -f json` before unlocking | ~0.65 s | measured warm (2.4 s cold) |
| **Machine time per one-slot move** | **≈ 5.5–6.5 s** | |

The vault history agrees. Right after the screenshot, "How I use SASE" was added at the
end of the Section field, then walked up one slot at a time, giving five commits in 85 s:

```
13:50:39  albums: update sase_blog_zettel.md (choice.add section/How I use SASE)
13:51:33  albums: update … (choice.move section/how_i_use_sase)   # past 🏁 Conclusion
13:51:45  albums: update … (choice.move section/how_i_use_sase)   # past 🔮 Future Work
13:51:54  albums: update … (choice.move section/how_i_use_sase)   # past 🛑 Not ready
13:52:04  albums: update … (choice.move section/how_i_use_sase)   # past 🎬 The Demos
```

Four of the six album-schema writes in the vault's history are one-slot moves. The
intent was a single thought: "put it before The Demos." That's the strongest evidence
for the move work.

### 2.3 Emoji today

- The `Choice emoji` field is a plain `<input type=text>`. You need macOS's
  Ctrl+Cmd+Space picker or a paste. Nothing filters, previews, or warns.
- For bank categories the emoji is typed inline in the label (`🍔 Fast food`), and bob
  splits it with `split_icon`. So the two editors already store emoji differently.
- A good engine already exists and goes unused here. `bob-emoji` has:
  - a 1,870-entry gemoji catalog with aliases, tags, descriptions and categories;
  - tiered ranking: alias prefix, then alias substring, then tag, then description word;
  - persisted recents (`👀`, `🔨` in the vault right now).
- **The gemoji keywords are thin.** 🧠 has only `brain`. 🧱 has `bricks` and no tags.
  🔍 is `mag` with tags `search, zoom`. 🪝 is `hook` with no tags. Typing "memory",
  "wall" or "find" finds nothing useful. Unicode CLDR annotations are the standard
  keyword set and are much richer.

### 2.4 Visual critique of the current card (from the screenshot)

- The stats text appears twice: once as the header subtitle and again as the first full-width
  row (`2 zettels · dated notes`).
- Field rows are flat gray full-width buttons. Required is a bare `*` (`Status · *`), and
  the useful facts ("set on 2 of 2 · sub-groups the index") sit in small gray text.
- Choice counts are glued to labels (`Ready 0`). Zero counts add noise across 15 chips.
- The empty status region renders as a tinted bar with nothing in it.
- The toolbar has 13 buttons. While a stage is open, almost all are disabled, and
  `Cancel stage` appears twice.
- `Preview this edit` is redundant, because preview already runs on input after 250 ms.
- Pressing Enter before that preview returns does nothing ("Enter is inert until a
  current preview succeeds"), which feels broken to a fast typist.
- The footer hint wraps to two lines and lists every key regardless of what's selected.

## 3. Is this a good idea? Critique and adjusted requirements

**Yes.** It's high value at moderate cost, the evidence is direct, and most of the work is
plugin-side. But the request as written aims slightly off-target in three places. I'm
adjusting the requirements below; each change is marked.

> **Adjusted requirement R1 — "move multiple spots" → "place anywhere in one gesture,
> one commit per arrangement."** Larger step sizes alone would still pay a full
> transaction per press. The fix is to make reordering local and batch the save:
> any number of nudges and jumps, across any number of items, saved as one envelope with
> one Undo.

> **Adjusted requirement R2 — "fast Apply" → "zero-latency preview, background save."**
> The bob round trip is bounded below by two git sync cycles plus full-vault scans,
> around 4–5 s. Trimming it is worthwhile (§5.7), but it won't make Apply feel instant.
> Perceived speed comes from (a) never waiting to *see* a result and (b) paying the save
> once per arrangement, off the critical path.

> **Adjusted requirement R3 (new) — "Add choice" must also place the choice.** Half the
> observed pain was adding at the end and then walking the choice up. Placement belongs
> in the add gesture, with a live ghost chip.

> **Adjusted requirement R4 — "emoji completion" → an Emoji Slot shared by both
> editors.** It should:
> - complete from search;
> - suggest from the label;
> - suggest from your own vault vocabulary;
> - flag duplicates within the field;
> - share recents with the editor's `:shortcode:` completion;
> - accept pasted or OS-picker glyphs.
>
> Bank categories get the same control, so the two editors stop diverging.

> **Adjusted requirement R5 (scope guard) — do not turn the whole card into a generic
> batched draft session.** Relabels, toggles, defaults and removals stay one gesture,
> one commit. Mixing them into one save makes refusal attribution, consequence text and
> Undo worse, and the history shows no bursts of those edits. Only reorders, plus the
> add-and-place gesture, batch. Revisit if relabel bursts show up in history.

What I would not do:

- **Drag-and-drop only.** You work keyboard-first (vim bindings, jump-to-link).
  Mouse dragging is a secondary path on the same model.
- **AbstractInputSuggest for emoji.** It's Obsidian's attached popover, available since
  1.4.10. It renders a vertical list with ↑/↓ only, floats outside the card, and adds a
  separate Escape scope to an already subtle Escape ladder. A grid inside the card is
  more legible for emoji, supports 2-D keys, and keeps key handling in one place.
- **Moving emoji search into bob-cli.** Obsidian is the only consumer, and a JS search
  over ~1.9k entries takes under a millisecond. A subprocess per keystroke adds latency
  for no gain.

## 4. Design principles

1. **Plugin composes, bob writes.** All vault bytes still come from `bob albums update`
   and `bob bank config update`. The plugin only predicts the order it shows and builds
   the envelope. This is unchanged from the existing contract.
2. **Every frame shows the truth or a clearly marked prediction.** Pending items are
   visibly pending. Saved items look normal.
3. **One intent, one commit, one Undo.** An arrangement is one intent, however many keys
   it took.
4. **No new failure modes.** The `expect` fingerprint, save-open-editors, preview-gated
   apply, stale refusal, sync-warning retry and inverse-op Undo all stay as they are,
   reused through the existing guarded session.
5. **Keyboard first, mouse equal, motion subtle.** Animations are 120–160 ms FLIP
   transitions and respect `prefers-reduced-motion`.

## 5. Design

### 5.1 Reorder: interaction model

There's no mode to enter. **Alt+J/K simply stops writing.** It moves the selected field or
choice one slot in the projected model, instantly, and keeps it selected. Everything
else builds on that:

| Key (item selected) | Effect (local, no bob call) |
|---|---|
| `⌥J` / `⌥K` | Nudge one slot later or earlier. Repeatable. |
| count + `⌥J`/`⌥K` (e.g. `4⌥K`) | Nudge N slots (vim count) |
| `⌥G` / `⌥⇧G` (or `⌥Home`/`⌥End`) | To the first or last slot |
| `m` | **Move to…** Every other chip or field in the same container gets a hint letter (`a s d f g h j k l …`). Type a letter to drop *before* that item; Shift+letter drops *after*. Same idea as the jump-to-link plugin you already use. |
| `j`/`k`, arrows | Select another item (pending moves stay) and nudge it too |
| `⏎` | **Save all pending moves** (one envelope; §5.3) |
| `esc` | Revert all pending moves (nothing was written). Existing Escape order: palette or stage, then pending draft, then close. |
| `u` | After a save, stage the inverse of the *whole* arrangement as one draft |

"Put How I use SASE before The Demos" then becomes `m`, `<hint on 🎬>`, `⏎`: three keys
and one commit, instead of 4 × (⌥K, wait, ⏎, wait).

**Mouse**: a drag handle appears on hover (`⋮⋮` at a chip's left edge, at a field
header's gutter). Pointer events (not HTML5 DnD) drive the drag, with a 2 px accent
insertion line between chips. Dropping feeds the same pending model, and the user still
presses `⏎` or clicks **Save order** to commit.

**Containers are respected.** Choices move within their field and fields move among
fields. A move past either end clamps with a soft shake. (Bank categories may cross
groups; see §5.6.)

### 5.2 Reorder: what you see (the preview)

```
╭───────────────────────────────────────────────────────────────────────────╮
│ 📇 Zettel                              dev › SASE › sase_blog              │
│ 2 zettels · dated notes                                                   │
│                                                                           │
│ Section                                 sub-groups the index · 2 of 2 set │
│  🪝 Intro   🧱 What is SASE? ·1   📜 Prompt language (macros) ·1           │
│  🔁 Agent turn   🚦 Gate   👪 Sessions, clans & tribes   🧠 Memory         │
│  🗺️ Plan & artifacts   📁 Project   ⚙️ Automation (service)                │
│  ┏━━━━━━━━━━━━━━━━━━━━┓                                                   │
│  ┃ 🔍 How I use SASE  ┃↑4   🎬 The Demos   🛑 Why SASE is still NOT ready  │
│  ┗━━━━━━━━━━━━━━━━━━━━┛                                                   │
│  🔮 Future Work   🏁 Conclusion   ＋                                        │
├───────────────────────────────────────────────────────────────────────────┤
│ ◆ 1 move pending — 🔍 How I use SASE  15 → 11          ⏎ save   esc revert │
│   ⌥J/K nudge · 4⌥K count · m move to… · ⌥G/⌥⇧G ends                       │
╰───────────────────────────────────────────────────────────────────────────╯
```

- **The projected model is what's rendered**: the server model plus pending moves. A
  moved chip gets an accent ring and a small delta badge (`↑4`). Neighbors slide over
  with a FLIP animation. Nothing else changes.
- **A pending bar replaces the toolbar** while moves are pending. It shows the count, a
  one-line summary per moved item (`15 → 11`), and the two decisions (`⏎ save`,
  `esc revert`). With several items moved it shows `3 moves pending` and lists them.
- **Accessibility**: a polite live region announces "How I use SASE, position 11 of 15"
  after each nudge (debounced about 100 ms) and "Saved order" or "Reverted" at the end.
  The containers carry `aria-roledescription="sortable"`.

### 5.3 Reorder: the save pipeline

```
nudge/jump ─▶ projected model repaints (<16 ms)
          └─▶ session.setDraft(envelopeOps)  ─▶ 250 ms pause ─▶ speculative dry-run (~1 s)
⏎ ─▶ "latched": apply as soon as this revision's preview is ok
    ├─ preview quiet  ─▶ apply (one commit) ─▶ repaint from post-write state ─▶ "Saved · u undo"
    └─ preview loud   ─▶ show consequence in amber, second ⏎ to apply
```

- **Envelope building.** Record intent per pickup as `(key, before|after anchor | start |
  end)`, coalescing repeated nudges of the same item. At build time, translate each
  intent into today's `field.move`/`choice.move {position}` against the order produced
  by the earlier ops. Sequential ops reproduce the user's order exactly, because bob
  applies them in order. Anchors make the intent survive a rebase: after a `stale_schema`
  refusal and refresh, rebuild positions from the anchors.
- **Enter latches.** Pressing ⏎ while the preview is in flight applies when that same
  revision's preview succeeds. Any further nudge cancels the latch. This fixes the
  "inert Enter" papercut for every stage, not only reorders.
- **Quiet means** all of these:
  - `report.ok`;
  - `group_before == group_after`;
  - no `newly_invalid > 0`;
  - no warnings.

  Choice moves are almost always quiet. A field move can change the grouping field when
  there's no `status` field (`group_field` picks the first choices field), and that is
  exactly when the preview should pause for a second ⏎.
- **Optimistic, but honest.** After ⏎ the projected order stays on screen with a faint
  "saving" shimmer on the moved chips. Navigation stays live. Structural gestures wait
  until the save returns, which is one in-flight save, as today. On refusal the chips
  FLIP back to the server order and the refusal shows inline.
- **Undo**: `inverse_ops` arrive in undo order (verified), so `u` reverts the whole
  arrangement in one transaction.
- **Invariant check**: after the post-write report lands, compare its order to the
  predicted order. A mismatch (it should never happen) shows a quiet warning rather than
  silently disagreeing.

### 5.4 Add-and-place (and the end of "add at the bottom")

`c` on any chip opens the add stage with a **ghost chip** inserted right after the
selection. Today `choice.add` already uses `position = selected + 1`, but you can't see
it. The ghost is a dashed outline that renders exactly what will be written
(`🔍 How I use SASE`) and updates as you type. While the stage is open, `⌥J/⌥K` and `m`
move the ghost. ⏎ sends one `choice.add {position}`: one commit, already in place. The
same applies to `a` (add field) with a ghost field block, and to the initial choice rows of
a new choices field.

### 5.5 The Emoji Slot

```
│ ＋ New choice · Section — after ⚙️ Automation (service)                    │
│  ┌────┬─────────────────────────────────────────┐                          │
│  │ 🔍 │ How I use SASE                          │   key  how_i_use_sase    │
│  └────┴─────────────────────────────────────────┘                          │
│  ⌕ use▏                                                    Smileys People… │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │ For this label   🔍  🧭  🛠️  🙋  📖  🧰  💡  🧪                        │  │
│  │ Your albums      ✍️  ✅  📌  🎬                                        │  │
│  │ Recent           👀  🔨                                                │  │
│  │ Matches "use"    …                                                    │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│  🔍  :mag:  magnifying glass tilted left — search · zoom · glass           │
│  Row: … ⚙️ Automation (service) ┆🔍 How I use SASE┆ 🎬 The Demos …          │
│  ⏎ add   tab next   ⌥J/K place   esc close picker                          │
```

**Control.** A square glyph button sits fused to the left of the label input, the way the
value is stored (`🔍 How I use SASE`).
- An empty slot shows a dotted `☺︎` placeholder.
- Tab from the label, a click, or `Ctrl+E` opens the palette with focus in its search box.
- Backspace on an empty search clears the glyph.
- Typing or pasting a literal emoji, including from the macOS picker, sets it directly.
- Validation is one emoji grapheme (the same regex as `albumSchemaChoiceParts`), shown
  inline before any bob call.

**Palette (inline, not floating).** It's a grid of 8 to 10 columns inside the stage,
using larger 1.4 em glyphs. With an empty query it shows these rows:

1. **For this label.** The label is tokenized and stop words removed (`how, i, the,
   is, of, &`). Each word is light-stemmed (`demos → demo`) and matched against aliases
   and keywords. Up to 8 results.
2. **Your albums.** Emoji already used for the same or a similar choice label elsewhere
   in the vault, read from the album report the plugin already holds. "Draft" offers
   ✍️ because another album uses it. This costs nothing to compute.
3. **Recent.** Shared with the editor `:shortcode:` completion, so both surfaces learn
   together.
4. **Category tabs** for browsing (Smileys, People, Animals & Nature, Food, Travel,
   Activities, Objects, Symbols, Flags), rendered one category at a time.

Typing filters live with no debounce, because the search runs in-process and is
sub-millisecond. The highlighted emoji's name, shortcode and top keywords show in the
caption line, with the matched letters accented, as `bob-emoji` already does. Arrow
keys or `Ctrl+N/P` move in 2-D, `⏎` picks and returns to the label, and `Tab` picks and
moves on. The first Esc closes the palette only.

**Ranking (an upgrade of `emojiSearch`).** Multi-word queries AND their tokens
("magnifying glass"). Tiers, best first:

1. exact alias or keyword;
2. alias prefix;
3. keyword word-start;
4. alias substring;
5. description word-start;
6. subsequence fuzzy, only when fewer than 8 results.

Within a tier, rank by recents, then vault-used, then shorter alias, then catalog order.

**Duplicate guard.** An emoji already used by a sibling choice shows dimmed with a small
badge (`used by ✍️ Draft`). It stays pickable, because duplicates are legal, just
usually a mistake.

**Data and API (owner: `bob-emoji`).** Add a versioned API, following the existing
cross-plugin `apiX` pattern (`app.plugins.getPlugin("bob-emoji")`):

```js
plugin.apiEmoji = {
  version: 1,
  search(query, { limit, exclude }),          // ranked, with match ranges
  suggestForLabel(label, { limit, exclude, vocabulary }),
  categories(), browse(categoryId),
  info(emoji),                                // name, aliases, keywords
  remember(emoji, alias),                     // shared recents
};
```

If `bob-emoji` is missing or older, the slot degrades to today's text input plus a hint.
In `scripts/gen-emoji-catalog.mjs`, merge English **CLDR annotations** (keywords and TTS
names) into each entry as `keywords`. Vendor them with the Unicode license notice, as
`vendor/` already does for gemoji. emojibase-data is the convenient MIT-packaged carrier
of CLDR data; check the license notice before vendoring.

### 5.6 Bank Setup card parity

- **Reorder.** Use the same projected-reorder engine for categories within and across
  groups, for groups, and for accounts.
  - Bank ops are already anchor-based (`category.move {before|after}`), which fits the
    intent model directly.
  - A category dropped into another group emits `category.set {group}` plus
    `category.move`, in one envelope.
  - **Rules are the exception**: their order is match precedence, so a rule reorder is
    always "loud". The preview shows which rows' categorization would change, and saving
    needs a second ⏎.
- **Emoji.** The `Label` field becomes the Emoji Slot plus a label. The plugin composes
  `${emoji} ${label}` into the op, and bob's `split_icon` keeps working unchanged.
  Label-aware suggestions work well for money categories (groceries → 🛒, gas → ⛽).

### 5.7 Performance budget

| | Today (per slot) | Proposed (per arrangement) |
|---|---|---|
| See the new order | after apply and refresh (~5–6 s) | **< 16 ms** per key |
| Preview | 0.25 s + ~1.0 s, per slot | ~1.0 s once, usually done before ⏎ |
| Save | ~4.5–5 s, blocking, per slot | ~4.5–5 s **once**, in the background |
| Commits / Undo steps | one per slot | **one** |
| "Before The Demos" from the observed session | 4 saves, ~31 s, 4 commits | 3 keys, 1 background save, 1 commit |
| Add + place | 5 saves, 85 s | 1 save |

**Optional bob-cli trims (Phase 5).** Measure first; each is a narrow change.

1. **Return the post-write album row in the apply report.** This is an additive
   `album` key, the same shape as `albums list`. The card repaints and unlocks without
   forcing `bob albums list` (about −0.65 s). The plugin still revalidates in the
   background.
2. **Scope `verify_installed`** to the edited album and its record folder instead of a
   full `VaultSnapshot` re-scan (about −0.5 s).
3. **Report index effects.** Add `facets_before/after`, or a single
   `index_changed: bool`, so "quiet" is decided by bob, never inferred in JS.
4. **Profile `VaultSnapshot::load`.** It's the ~1 s floor of every preview and plan, at
   7.3k notes and CPU-bound. Parallelizing it would speed up every bob writer, not just
   this card. That makes it a separate task, not part of this feature.

I'd *not* make the post-sync asynchronous for this writer alone. It's shared by every
guarded writer and protects multi-host convergence.

### 5.8 Visual refresh (folded into Phase 1)

- **Header**: one title line (`📇 Zettel`) with a dim breadcrumb on the right. Drop the
  duplicate stats row; the album-details target becomes a small `⚙` on the header.
- **Fields**: a label in medium weight, then `required` as a pill (not `*`), the kind as
  a dim mono tag, and "groups / sub-groups the index" as an accent pill. Right-align
  `2 of 2 set`.
- **Chips**: emoji, then label, then a count in a muted tabular-numeral pill (`·1`). A
  zero count shows faint. `＋` is a round ghost chip at the end of the row, not a full
  button.
- **Status**: hidden when empty. Otherwise one line with a colored left rule: neutral
  for preview, amber for loud, red for refusal, green for "Saved · u undo". Prefer that
  inline line over the floating `Notice`.
- **Actions**: replace the 13-button toolbar with a *contextual* hint strip that lists
  only the keys valid for the current selection. A `⋯` button reveals the full list for
  mouse users. Remove `Preview this edit`; preview is automatic and Enter latches.
- **Motion**: FLIP for reorders, 120 ms fades for ghost and pending states, and nothing
  else.

## 6. Reliability invariants (tests should assert these)

1. A nudge, jump, drag or Esc-revert performs **zero** bob calls and zero vault writes.
2. One ⏎ produces at most one `bob albums update` (non-dry) per arrangement and exactly
   one commit, and `u` restores the prior order in one commit.
3. The order rendered after the post-write report equals the predicted order (asserted
   in e2e).
4. A stale fingerprint during pending moves leads to a stale refusal. The session then
   rebases, the positions are rebuilt from anchors, and it previews again. Nothing is
   written against the wrong schema.
5. Escape follows a strict order: palette, then stage, then pending moves, then close.
   This means extending `onEscapeKey`, because Obsidian's Modal scope binds Escape before
   any contentEl listener; see the existing comment in `241y`.
6. IME composition never triggers palette navigation or Enter-latch.
7. If `bob-emoji` is absent, the editor still works (plain input).

## 7. Alternatives considered

| Option | Verdict | Why |
|---|---|---|
| Bigger step size (⌥⇧K = 5 slots), still one commit per press | Rejected | Still a full transaction per press, still no visual preview, still noisy history |
| Generic batched draft for *all* edits with a Save button | Rejected for v1 (R5) | Worse refusal attribution and Undo granularity; no evidence of non-move bursts |
| Write on drop with no preview for moves | Rejected | Field moves can change the grouping field; the speculative preview costs nothing perceived and keeps "bob previews every write" |
| Declarative `choice.order` / `field.order` op in bob | Deferred | Cleaner wire, but needs Rust work; anchored sequential `*.move` ops already reproduce the order exactly |
| `AbstractInputSuggest` popover for emoji | Rejected | List-only, ↑/↓ only, floats outside the card, extra Escape scope |
| Copy the emoji catalog into bob-ledger-tools | Rejected | Two catalogs and two recents lists drift; a cross-plugin API is the repo's existing pattern |
| `bob emoji search` subprocess | Rejected | Spawn cost per keystroke; Obsidian is the only consumer |
| Edit the YAML in vim (`y`, then `:m`) | Kept as an escape hatch | Fast for big restructures, but bypasses previews, counts and Undo; the card should be the easy path |

## 8. Implementation plan

New logic goes in new fragments, because `241y-plugin-album-schema-card.js` is already
883 lines against the 1,000-line fragment cap.

| Phase | Repo | Scope | Size |
|---|---|---|---|
| **P1 Projected reorder and add-and-place (album)** | bob-plugins | New `242f-plugin-schema-reorder-model.js`: pure model of intents, projection and envelope ops, with no DOM. New `242g-plugin-schema-reorder-dom.js`: FLIP, hint-jump, drag and the pending bar. Rewire `schemaMoveSelected`, the ghost chip, the Enter latch, and the visual refresh in §5.8. Unit tests for the model (permutations, anchors, coalescing, rebase). Extend `scripts/obsidian-album-schema-writer-e2e.cjs` with a batched-reorder apply and undo, plus the predicted-equals-actual check. | M–L |
| **P2 Emoji Slot** | bob-plugins | `bob-emoji`: `apiEmoji` v1 with shared recents, label suggestions, and CLDR `keywords` in `gen-emoji-catalog.mjs`. `bob-ledger-tools`: new `242h-plugin-emoji-slot.js` (palette DOM and keys), used in the choice, choice-add and field-add stages. Ranking and label-suggest unit tests. | M |
| **P3 Bank parity** | bob-plugins | Reuse P1 and P2 in `248k` and `248g`: categories, groups and accounts reorder, loud rule moves, and the Emoji Slot in the category label | M |
| **P4 Decision record** | memory | Once Bryan accepts: "a schema arrangement is one intent and one commit; non-reorder gestures stay one gesture, one commit". It answers the prior research's open commit-granularity question. | S |
| **P5 Optional bob-cli trims** | bob-cli | Post-write album row in the report, scoped verify, and index-effect fields (all additive JSON, one schema version). Profile the snapshot load separately. | S–M |

P1 and P2 are independent and can run in parallel; they touch different fragments.
Ship P1 first: the git history shows reordering is where the time actually goes. After
each bob-plugins change, run `npm run build`, `npm test` and `bob plugins sync`, as the
repo requires.

## 9. Open questions for Bryan

1. **Auto-apply quiet reorders on a single ⏎** (recommended), or always show the
   consequence and require a second ⏎?
2. **Hint-jump key**: `m` ("move to…") as proposed, or `f` to match your jump-to-link
   muscle memory? (`f` is free in the card today, but "f = find" may read oddly for
   moving.)
3. **CLDR keywords** add roughly 150–250 KB to `bob-emoji`. Is that fine? It's the
   biggest single improvement to filter quality.
4. **Bank**: should dropping a category into another group be allowed? It's one envelope
   with a `group` change, previewed as loud.

## 10. Recommended solution

Build **P1, a projected reorder with one batched save, plus add-and-place**, first.
- Alt+J/K, counts, `⌥G`/`⌥⇧G` and the `m` hint-jump move items instantly on a projected
  model.
- Pending moves show as accent rings with delta badges and a pending bar.
- ⏎ saves the whole arrangement as one anchored multi-op envelope through the existing
  guarded session. The preview is speculative, Enter latches, quiet saves auto-apply,
  and loud ones get a second ⏎.
- The result is one commit and one `u` Undo, and the card stays usable during the
  background save.
- New choices and fields are placed with a ghost before they're written.
- None of this needs a bob-cli change: the writer already accepts arbitrary positions
  and multi-op envelopes with correct inverses (verified by dry-run on the real album).

Then build **P2, the Emoji Slot**.
- A glyph fused to the label, with an inline grid palette.
- Rows for label-aware suggestions, your albums' existing emoji, and shared recents.
- Live filtering on a CLDR-enriched catalog, a duplicate guard, and a paste/OS-picker
  fallback.
- All of it is served by a new versioned `bob-emoji` API so both editors and the
  editor's `:shortcode:` completion share one engine.

Finish with **P3, bank parity**, using the same two components, and treat the **P5
bob-cli trims** as measured follow-ups. Together this turns the observed session (an add
followed by four one-slot moves, five commits in 85 s) into one gesture, one commit and
about three keystrokes, with the result visible before you let go of the key.

---

### Sources

- Code and data (local): bob-plugins `plugins/bob-ledger-tools/src/{241y,242a,242aa,242b,242c,241z,248g,248i,248k}*.js`;
  `plugins/bob-emoji/{src/030-emoji-model.js,src/040-emoji-suggest.js,vendor/gemoji-emoji.json}`;
  bob-cli `src/native/albums/update/run.rs`, `src/native/host_catalog/txn.rs`,
  `src/native/albums/grouping.rs`, `src/native/bank/config_update/protocol.rs`;
  `~/bob` git history of `sase_blog_zettel.md`; `~/.local/state/bob-cli/vault-sync.json`.
- Prior research: `202611/album_record_schema_ux/album_record_schema_ux__final.md`.
- [Obsidian API — AbstractInputSuggest (since 1.4.10)](https://docs.obsidian.md/Reference/TypeScript+API/AbstractInputSuggest)
- [obsidian.d.ts (AbstractInputSuggest @since 1.4.10)](https://raw.githubusercontent.com/obsidianmd/obsidian-api/master/obsidian.d.ts)
- [Forum: suggest input for plugins (AbstractInputSuggest)](https://forum.obsidian.md/t/provide-an-implementation-of-suggest-input-for-plugins-to-use/66561)
- [emojibase-data (MIT, localized CLDR-derived datasets)](https://www.jsdelivr.com/package/npm/emojibase-data?tab=files)
- [emojibase changelog (CLDR JSON packages)](https://unpkg.com/emojibase-data@16.0.3/CHANGELOG.md)
- [CLDR English emoji annotations (annotationsDerived/en.xml mirror)](https://android.googlesource.com/platform/external/cldr/+/fd14fac5e856cd3dbb44518370a3ef832a81bba7/common/annotationsDerived/en.xml)
- [dnd-kit accessibility guide (keyboard sensor, live-region announcements)](https://docs.dndkit.com/guides/accessibility)
- [Primer: accessible drag and drop pattern](https://primer.style/accessibility/patterns/drag-and-drop)
- [Smashing Magazine: Dragon Drop, accessible list reordering](https://www.smashingmagazine.com/2018/01/dragon-drop-accessible-list-reordering/)
- [Salesforce UX: 4 patterns for accessible drag and drop](https://medium.com/salesforce-ux/4-major-patterns-for-accessible-drag-and-drop-1d43f64ebf09)
