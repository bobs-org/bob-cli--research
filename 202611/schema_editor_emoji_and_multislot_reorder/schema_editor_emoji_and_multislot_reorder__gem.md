---
title: "Album & Bank Schema Editor UX: Emoji Completion, Multi-Slot Reordering, and Fast Apply"
date: 2026-11-16
author: gem
status: research
tags:
  - bob-cli
  - bob-plugins
  - albums
  - bank
  - bob-emoji
  - ux-design
---

# Album & Bank Schema Editor UX: Emoji Completion, Multi-Slot Reordering, and Fast Apply

## Executive Summary

An audit of `~/tmp/screenshots/20261116_134836.png`, the Obsidian schema editors in `bob-plugins`, and the guarded writers in `bob-cli` shows that **the underlying CLI protocols are already far more capable than the UIs sitting on top of them**. Both `bob albums update` and `bob bank config update` already support **arbitrary destination positions** (`position`, `before`/`after`) and **atomic multi-operation batches** (`ops: [...]`) with automatic reversed `inverse_ops` for single-step Undo.

The current pain stems from four mismatches in the client/server UX pipeline:

1. **Emoji inputs are bare `<input type="text">` boxes**, even though `bob-plugins` already ships a 1,500+ entry `gemoji` index and recents tracker in `bob-emoji` (`EditorSuggest` only—not exposed to modal `<input>`s). Meanwhile, Bank categories combine emoji and label into one string (`"☕ Coffee"`), Album-level `emoji:` isn't editable via `album.set` at all, and Bank modals have a key-handling bug where typing `q` inside any stage `<input>` cancels the entire stage.
2. **Reordering is forced into 1-slot-at-a-time `Apply` loops**: `AlbumSchemaCardModal` (`Alt+J`/`K`) and `BankSetupCardModal` (`Alt+J`/`K`) hardcode `±1` moves, replace the draft instead of coalescing or accumulating edits, show no live visual reorder in the chip/tile grid (Bank doesn't even paint the dry-run `categories[]` and hotkey shifts that `bob bank config update -d` already returns), and require a full multi-second `Apply` cycle per slot.
3. **`Apply` pays a multi-second network + scan tax on every edit**: `host_catalog::run_locked` executes two blocking remote Git checks (`pre-sync` `ls-remote` + `post-sync` `ls-remote` & `push`), `bob albums update` runs `VaultSnapshot::load` repeatedly across preflight, replan, overlay, and post-install verification, and both plugins then block modal responsiveness waiting for a second full-report subprocess (`bob albums list` / `bob bank config`) before returning control to the user.
4. **Modal DOM & visual friction**: Both modals nuke their entire DOM (`content.empty()`) on every keystroke; the Album Schema Card duplicates the `"2 zettels · dated notes"` line, paints an empty purple-bordered `.bob-album-schema-consequence` strip when idle, and shows a 12-button wall with disabled browse actions while a stage form is open.

**Recommended Direction:**
Move from *"1-slot stage → blocking sync/push → full reload"* to **Instant Optimistic Workspace + Coalesced Batch Preview + Local-Commit & Background Sync**:
- **Emoji UX:** Expose a versioned `bob-emoji` v1 API (upgraded with multi-token search, category metadata, and schema-friendly defaults), and build a shared, keyboard-first **Emoji Picker Popover + Label-Smart Combobox** for Album choices, Album `emoji`, and Bank category labels (fixing the `q`-in-input bug).
- **Multi-Slot Reordering UX:** Add **instant 0ms in-place visual reordering** via (a) Grab/Move mode (`m`) with Vim counts (`5j`), `Home`/`End`, and type-to-target placement, (b) sticky coalescing `Alt+J`/`K`/`H`/`L`, and (c) desktop drag-and-drop—paired with **multi-op draft accumulation** and live visual delta/ghost/hotkey-shift previews, coalesced into minimal `bob` ops applied in **one** atomic transaction.
- **Fast Performance:** Return the updated `album` / `config` report slice directly from `update` commands (eliminating the redundant post-apply `list`/`config` fetch), target-scope album snapshot reads, decouple `post-sync` (via `--offline` local commit + sync-on-open + debounced background `bob vault-sync`), and switch modal updates from `content.empty()` to targeted DOM patching.

---

## 1. Current State Audit (Codebase & Screenshot Evidence)

### 1.1 Visual Audit of `~/tmp/screenshots/20261116_134836.png`

The screenshot captures `AlbumSchemaCardModal` (`bob-ledger-tools`) open on `sase_blog_zettel` with `+ Add choice` staged under `Section`:

- **Redundant header/body stats row:** `<p class="bob-album-schema-dialog-stats">` (`241y-plugin-album-schema-card-dom.js:99`) and `<button data-target-key="stats">` (`241y-dom:126`) render identical `"2 zettels · dated notes"` lines stacked vertically.
- **Wrapped choice chips without move affordances:** `Section` has 14 choice chips wrapping across four rows (`🪝 Intro 0` … `🏁 Conclusion 0`). None indicate index order, drag handles, or an obvious multi-slot move workflow.
- **Bare `Add choice` form:** `Choice label` and `Choice emoji` are full-width stacked inputs (`242c-plugin-album-schema-edit.js:170-171`) with `Choice label` first, `Choice emoji` second (visually inverted relative to the resulting `✍️ Draft` chip), no live chip preview, and no emoji completion or picker trigger.
- **Empty purple consequence box:** `.bob-album-schema-consequence` (`styles.css:8849`) renders unconditionally (`241y-dom:210`) with `min-height: 1.4em`, `padding`, and a 2px purple left border even when `state.preview`, `state.busy`, and `state.refusal` are all null/false.
- **12-button toolbar wall:** Two rows of buttons (`Edit`, `Add field`, `Add choice`, `Toggle required`, `Toggle suggest`, `Move up`, `Move down`, `Remove`, `YAML`, `Undo`, `Cancel stage`, `Close`) remain mounted during an active stage, with 8 of them greyed out.

### 1.2 Inventory of All Schema Editor & Emoji Surfaces

| Surface | Implementation (`bob-plugins`) | Backend (`bob-cli`) | Current Emoji Input | Current Move Capability |
| --- | --- | --- | --- | --- |
| **Album Schema Card** | `241w`, `241x`, `241y`, `241y-dom`, `242a`–`242c` | `src/native/albums/update/*` | Separate plain `<input>` on `choice`, `choice-add`, `field-add` initial choices. **No emoji editing on `album` (`album.set`).** | `Alt+J`/`K` or buttons move **1 slot** (`index ± 1`), immediately overwrite `draftOps`, require full `Apply` per slot. |
| **Bank Setup Card** | `248i`, `248j`, `248k`, `248d`, `248e` | `src/native/bank/config_update/*` | Single `Label` `<input>` (`"e.g. ☕ Coffee"`). No separate emoji input or completion. **Typing `q` in input cancels stage!** | `Alt+J`/`K` only (no buttons) for same-group categories, groups, rules; opens `"Confirm Move"` modal for **1 slot**; ignores `report.categories` / `hotkeys.shifted` in visual grid during preview. |
| **Bank Category Card (`+ New category`)** | `248f`, `248g`, `247` | `src/native/bank/config_update/*` | Single `Label` `<input>` (`"e.g. 🍔 Fast food"`). Also catches `q` before `inInput` (`248g:145`). | N/A (add-only quick stage during `]b` walk). |
| **Note Editor Emoji** | `plugins/bob-emoji/` (`010`–`060`, `vendor/gemoji-emoji.json`) | N/A | `EditorSuggest` triggered only on `:<query>` at BOL or after whitespace in Markdown notes. **No modal `<input>` support or public `this.api`.** | N/A |

### 1.3 Why Reordering and `Apply` Feel So Slow (Exact Root Causes)

#### Protocol vs. UI Mismatch
Both Rust writers **already support full multi-slot moves and multi-op batches**:
- `bob albums update`: `field.move` and `choice.move` take any zero-based `position` (`src/native/albums/update/ops.rs:1097, 1617`); `ops` is an ordered `Vec<Op>` executed atomically (`ops.rs:162`) with reverse-ordered `inverse_ops`.
- `bob bank config update`: `category.move` and `group.move` accept `before` / `after` targeting **any** declared anchor (`src/native/bank/config_update/ops.rs:1157, 1398`), `rule.move` takes any zero-based `position` (`ops.rs:2278`), and `apply_ops` executes an ordered batch atomically (`ops.rs:231`).

Yet the Obsidian modals choke this down to 1-slot steps:
- `AlbumSchemaCardModal.schemaMoveSelected(direction)` (`241y:541-557`) computes `next = index + direction` (`±1`) and calls `schemaQueueOp(...)` -> `this.session.setDraft([op])` (`241y:512`), **overwriting** any prior staged op. Because `this.schemaModel` hasn't moved yet, pressing `Alt+J` twice produces the exact same 1-slot op.
- `BankSetupCardModal.beginSelectedGesture("move", direction)` (`248k:330-341`) calls `bankSetupCardCategoryMoveOp` / `GroupMoveOp` / `RuleMoveOp` (`248i:178-193, 346-354`), locking you into a `confirm` sub-stage with only `Apply` / `Cancel` for a 1-slot move.

#### Latency Anatomy of a Single `Apply`
Tracing one `Apply` click end-to-end reveals four stacked delays:

```text
[Click Apply]
  ├─ 1. Obsidian saveEditors([ownPath])
  ├─ 2. Spawn `bob <albums|bank> update -f json -i -`
  │     ├─ Preflight: full vault/bank scan + overlay + plan
  │     └─ host_catalog::run_locked (`src/native/host_catalog/txn.rs:945`):
  │           ├─ Acquire bob_sync.lock
  │           ├─ PRE-SYNC (`vault_sync.rs:309`): git status + `git ls-remote origin master` (network!)
  │           ├─ Re-plan inside lock: ANOTHER full vault/bank scan + overlay (`albums/update/run.rs:550`)
  │           ├─ Install + verify_installed (`albums/update/run.rs:457`: ANOTHER VaultSnapshot::load!)
  │           ├─ Scoped `git commit` (`txn.rs:884`)
  │           └─ POST-SYNC (`vault_sync.rs:309`): `git ls-remote` + `git push origin master` (network!)
  ├─ 3. Post-apply UI-blocking revalidation in `bob-ledger-tools`:
  │     ├─ Albums (`242a:120`): spawns `bob albums list -f json` (ANOTHER VaultSnapshot::load across whole vault!)
  │     └─ Bank (`248e:144`): spawns `bob bank config -f json` + `bankRevalidateMounts()` (`list`/`report`)
  └─ 4. Modal finally unlocks (`busy = false`)
```

Moving a choice 8 slots today triggers **8 separate `Apply` cycles** = **16 remote GitHub round-trips**, **~32–40 full vault scans** (for albums), **8 separate Git commits**, and **~20–35 seconds** of waiting!

#### Keystroke Jank in Modals
Both `AlbumSchemaCardModal.paintSchemaCard()` (`241y:149`) and `BankSetupCardModal.paint()` (`248j:437`) tear down the entire modal DOM (`content.empty()`) and re-focus by querySelector on **every single `input` event** (`241y:344` / `248k:361`). Typing inside an interactive emoji filter popover under full-modal tear-down will cause scroll jumps, flicker, and IME/focus loss.

---

## 2. Critique of the Initial Plan & Adjusted Requirements

The user's goal—making the bank and album schema editors convenient, emoji-friendly, fast for multi-slot moves, and genuinely pleasant to use—is spot-on. However, a literal implementation ("add autocomplete to the screenshot's emoji box + add multi-step move buttons + speed up `Apply`") leaves major UX traps intact. Below is a direct critique and the recommended adjustments to the requirements.

### Critique & Adjustments Summary

| # | Original Assumption | Critique | Adjusted Requirement |
| --- | --- | --- | --- |
| **1** | "Make it easier to move fields/choices up/down multiple spots … and faster Apply" | Even a 500ms `Apply` is painful if reordering by 8 slots requires 8 `Apply` cycles and 8 Git commits. The backend *already* supports target positions and atomic multi-op batches. | **Separate visual editing/reordering from committing.** Move items instantaneously (0ms) in an in-memory working draft with coalesced ops and multi-op batching, previewed once, applied in **one** transaction. |
| **2** | Emoji completion only mentioned for "prompting for emojis (as shown in the screenshot)" | Bank Category forms (`Edit` / `New category`) have *no* separate emoji field (only combined `"☕ Coffee"`), Album `album.set` cannot edit the album's own `emoji:`, and Bank modals drop any `q` keystroke inside inputs! | **Unify Emoji Completion across both editors & all emoji-bearing items**: Album choices (`choice`, `choice-add`, `field-add`), Album identity (`album.set` + `emoji`/`summary`), and Bank categories (`BankSetupCardModal` + `BankCategoryCardModal`'s `+ New category`), while fixing the `q`-in-input bug (`248k:601`, `248g:145`). |
| **3** | Build emoji completion ad hoc in schema modal | `bob-plugins/plugins/bob-emoji` already embeds 1,500+ gemoji entries and tracks recents, but doesn't expose an API or support multi-word queries (`"fast food"`, `"green check"`). Duplicating the catalog fragments recents. | **Upgrade `bob-emoji` to expose a versioned `api` (v1)** with multi-token + category search and shared recents; build a shared modal combobox/grid popover in `bob-ledger-tools` consuming it (with graceful fallback if disabled). |
| **4** | Bank category moves are 1-slot same-group moves | Bank categories in YAML can live in different `group`s, `category.move` only accepts `before`/`after` declared keys, and `BankSetupCardModal` currently throws away `bob -d`'s post-image `categories[]` & hotkey shifts! | **Render `bob`'s dry-run `categories[]` and hotkey shifts live on the tile grid**, and support **cross-group category moves** by emitting `[category.set(group), category.move]` atomically in one batch. |
| **5** | Speeding up `Apply` = optimizing Rust code | Rust YAML patching takes milliseconds; the seconds come from **two synchronous remote GitHub checks/pushes** in `run_locked` plus **redundant full-vault reads** in `update` and post-apply `list`/`config` revalidation. | **Three-part performance fix**: (a) return updated `album`/`config` state directly from `update`, (b) scope snapshot reads in `albums update` to root albums + `<stem>/`, and (c) decouple remote `git push` from blocking the modal via local-commit (`--offline`) + sync-on-open + debounced background `bob vault-sync` (with clear safety controls). |
| **6** | Visual polish only where broken | Screenshot reveals structural clutter: duplicated stats row, empty purple consequence box at rest, 12-button toolbar wall with disabled items during stages, inverted `[Label] [Emoji]` order, and full `content.empty()` DOM wipes per keystroke. | **Targeted UI & DOM cleanup**: deduplicate stats, collapse empty consequence box, render contextual stage vs. browse toolbars, pair `[Emoji] [Label]` with a live chip preview, and switch to targeted DOM region patching. |

---

## 3. Feature Design: Emoji Completion & Filtering

### 3.1 Shared Engine: Upgrading `bob-emoji` (v1 API)

Rather than duplicating `vendor/gemoji-emoji.json` inside `bob-ledger-tools`, `plugins/bob-emoji` should become the single source of truth for emoji lookup and recents across Obsidian:

1. **Preserve `category` in `scripts/gen-emoji-catalog.mjs`:**
   `vendor/gemoji-emoji.json` already contains a `"category"` field (`"Objects"`, `"Symbols"`, `"Food & Drink"`, `"Travel & Places"`, `"Activities"`, `"Animals & Nature"`, `"Smileys & Emotion"`, `"People & Body"`, `"Flags"`). Encode this compactly (e.g., 1-byte category index `c: 0..8` against `BOB_EMOJI_CATEGORIES`) so empty-query browsing can offer category filter pills with negligible size overhead.
2. **Upgrade `emojiSearch` (`030-emoji-model.js`) for natural multi-word filtering:**
   - **Colon-insensitive & trim-normalized:** Strip optional leading/trailing `:` so both `fire` and `:fire:` match identically (preserving existing `:shortcode` behavior for `EditorSuggest` via `emojiFindTrigger`).
   - **Multi-token AND matching:** Split query on whitespace/underscores/hyphens (`"green check"` → `["green", "check"]`). An entry matches if **every** token matches at least one alias token, tag, or description word.
   - **Word-boundary prefix boosting:** Rank exact alias (`tier 0`) > alias starts-with (`tier 1`) > alias/description word-prefix (`tier 2`, so `"car"` ranks `🚗 :car:` and `💳 :credit_card:` well ahead of `🧣 :scarf:`) > substring (`tier 3`) > tag (`tier 4`) > description (`tier 5`), with `recents` boosting within tiers.
   - **Schema-friendly `BOB_EMOJI_SCHEMA_POPULAR` preset:** Keep `BOB_EMOJI_POPULAR` for chat/notes, and add a `preset: "schema"` popular list tuned for statuses, categories, and topics (`✅`, `🌱`, `✍️`, `📌`, `🚫`, `🔁`, `⏳`, `🛒`, `🍽️`, `☕`, `🏠`, `🚗`, `💻`, `📚`, `🎬`, `🧠`, `⚙️`, `🗺️`, `🏷️`, `🔥`, `⚡`, `🎯`, `🔮`, `🏁`).
   - **Label-derived contextual hints (`suggestForLabel(labelText)`):** Extract meaningful words from the user's `Choice label` / `Category label` (e.g., `"Automation (service)"` → `["automation", "service"]` → `⚙️`, `🤖`, `🛠️`) so when an emoji box is focused *empty*, relevant icons appear in a tiny **"Suggested for '<Label>'"** strip immediately!
3. **Expose `plugin.api` on `BobEmojiPlugin` (`050-plugin.js`):**
   ```js
   this.api = Object.freeze({
     version: 1,
     categories: BOB_EMOJI_CATEGORIES,
     search: (query, options) => emojiSearch(this.emojiIndex, query, this.emojiRecents, options?.limit, options?.popular, options),
     suggestForLabel: (label, limit = 6) => emojiSuggestForLabel(this.emojiIndex, label, this.emojiRecents, limit),
     lookup: (emoji) => this.emojiByGlyph.get(emoji) || null,
     recents: () => this.emojiRecents.slice(),
     recordRecent: (suggestion) => this.emojiRememberRecent(suggestion),
   });
   ```
   - **Fallback when `bob-emoji` is disabled:** `bob-ledger-tools` checks `app.plugins.plugins["bob-emoji"]?.api`. If absent, the emoji swatch/input stays editable as plain text (plus a compact picker of recently used emojis from the current album/bank config itself!) with a quiet hint `"Enable Bob Emoji for full search"`.

### 3.2 Shared UI Component: The Emoji Chip & Anchored Hybrid Popover

Let's design the interaction so it works identically whether editing an **Album Choice**, **Album Icon**, or **Bank Category**, using both mouse and pure keyboard.

#### A. Layout: Paired `[Emoji] [Label]` + Live Chip Preview
Replace stacked `[Choice label]` / `[Choice emoji]` with a clean, compact horizontal unit and live preview:

```text
┌─ Add choice · Section ───────────────────────────────────────────────────┐
│  Preview:  [ 🗺️ Future Work ]                                            │
│                                                                          │
│  Emoji & Label                                                           │
│  ┌──────────────┐  ┌───────────────────────────────────────────────────┐ │
│  │ 🗺️   ▾  [×]  │  │ Future Work                                       │ │
│  └──────────────┘  └───────────────────────────────────────────────────┘ │
│         ▲ (Alt+E or click opens / focuses Emoji Picker Popover)          │
└──────────────────────────────────────────────────────────────────────────┘
```

And in **Bank Category Edit / New Category**:
- **Same `[Emoji] [Label]` visual pairing!** When opening Edit on `"☕ Coffee"`, `splitIcon` separates `☕` into the Emoji control and `Coffee` into the `Label` input (saving joins them back as `"☕ Coffee"` for `category.add`/`category.set`—or if a user pastes `"🍔 Fast food"` directly into `Label`, auto-split it cleanly!).
- **During `]b` bank triage (`BankCategoryCardModal` `+ New category`)**: Keep `Label` focused first so muscle-memory typing works instantly, and support **both** inline `:shortcode` trigger right inside `Label` (e.g., typing `:burger ` → `🍔 `) **and** `Alt+E` / clicking the leading `[ ☺ ]` chip to open the full Emoji Picker Popover!

#### B. Anchored Hybrid Popover (Grid when Browsing → Ranked List when Filtering)
When the Emoji control is clicked, receives `Alt+E`, or (in `Choice emoji`) is focused/typed into:

```text
  ┌─ Pick emoji ───────────────────────────────────────────────────────────┐
  │ 🔍 [ green check_                                         ]  [All ▾]   │
  ├────────────────────────────────────────────────────────────────────────┤
  │  Suggested for "Ready"                                                 │
  │   ✅  🟢  ☑️  ✔️  🚀  🏁                                               │
  │                                                                        │
  │  Matches (ranked)                                                      │
  │  ▸ ✅  :white_check_mark:    check · mark · green · done               │
  │    🟩  :green_square:        green · square                            │
  │    💚  :green_heart:         heart · love · green                      │
  │    ☑️  :ballot_box_with_check:  check · box                            │
  │    🥗  :green_salad:         food · green                              │
  ├────────────────────────────────────────────────────────────────────────┤
  │  ✅ :white_check_mark: — check mark button      ↑↓ move · ↵ pick · esc │
  └────────────────────────────────────────────────────────────────────────┘
```

And when the filter input is **empty** (browse mode):

```text
  ┌─ Pick emoji ───────────────────────────────────────────────────────────┐
  │ 🔍 [ Search emoji by name, tag, or :shortcode…            ]  [All ▾]   │
  ├────────────────────────────────────────────────────────────────────────┤
  │  [All] [Recent] [Symbols] [Objects] [Food] [Places] [Nature] [Smileys] │
  │  Recent & Suggested                                                    │
  │   ✍️  🧠  🗺️  ⚙️  🎬  🔮  🏁  🌱                                       │
  │  Popular for schemas                                                   │
  │   ✅  📌  ⏭️  ✂️  🚫  🔁  ⏳  🏷️                                       │
  │   🛒  🍽️  ☕  🏠  🚗  💻  📚  ⚡                                       │
  ├────────────────────────────────────────────────────────────────────────┤
  │  🎯 :dart: — bullseye  ·  ● used in sibling     ←↑↓→ move · ↵ pick     │
  └────────────────────────────────────────────────────────────────────────┘
```

**Why this hybrid design works so well:**
1. **Never mixes existing glyph with new filter text:** The selected emoji lives in the chip/button (`[ ✍️ × ]`) while the popover search box holds *only* the filter query. You never accidentally search `"✍️brain"`.
2. **Smart sibling deduplication cue:** A tiny muted corner dot (`●`) marks emojis already used by another choice in the same field (or another category in Bank), helping prevent accidental visual duplicates without forbidding reuse.
3. **Strict Keyboard Priority (Zero Conflicts):**
   - Popover open:
     - `↑` / `↓` / `Ctrl+N` / `Ctrl+P` (plus `←`/`→` in empty-query 8-col grid): move highlight.
     - `Tab` / `Shift+Tab` (when empty) or `Ctrl+]`/`[`: cycle category filter pill; when filtering, `Tab` or `Enter`: accept highlighted emoji, record in `bob-emoji` recents, close popover, trigger stage preview, and return focus cleanly!
     - `Esc`: dismiss popover **without** closing the edit stage (`stopPropagation()`).
     - Typing `q` inside any input: **fix `248k:601` and `248g:145`** so `q` ONLY closes/cancels when `!inInput`!
     - Raw emoji paste or macOS `Cmd+Ctrl+Space`: detected via non-ASCII pictographic regex (`albumSchemaChoiceParts` / `\p{Extended_Pictographic}`) and accepted directly into the emoji slot!

### 3.3 Missing Piece: Album-Level Emoji Editing (`album.set`)
Currently `album.set` (`src/native/albums/update/ops.rs:295`) only edits `label`, `plural`, and `dated_notes`, even though albums render `emoji:` prominently in owner `## Albums` callouts, capture rows, and the Schema Card header (`🗃️ Zettel`).
- **Recommended adjustment:** Allow `emoji` (and `summary`) in `album.set` `set`/`unset`, guarded cleanly in `spans.rs` (since `emoji:` sits at top-level frontmatter rather than inside `record:`, `spans.rs` can patch root frontmatter `emoji:`/`summary:` with exact-byte inverse restoration just like `record:` keys!). That brings the exact same Emoji Picker to `Edit album details`.

---

## 4. Feature Design: Multi-Slot Reordering & Visual Preview

### 4.1 Interaction Model: "Instant Local Draft + Multi-Gesture Reorder"

Instead of firing `setDraft([move(±1)])` and waiting for `Apply` on every slot, both editors should maintain a **Live Draft Projection**:
- `draftOps`: an ordered list of normalized operations in the session (starting empty `[]`).
- `projectedModel`: pure deterministic function `projectDraftModel(baseModel, draftOps)` that applies moves/edits in-memory in **<1ms** so the UI always paints the exact post-edit state immediately.

#### Three Complementary Multi-Slot Move Gestures

1. **Grab / Reorder Mode (`m`) — Keyboard Power-User Hero:**
   - Focus any movable item (Album field, Album choice, Bank category, Bank group, Bank rule) and press `m` (or click a `Reorder` button / `⋮⋮` handle).
   - The item visually "lifts" (accent border, subtle shadow, position badge `[3 / 14]`):
     - **`j` / `k` / `↑` / `↓` / `h` / `l` / `←` / `→`**: move the grabbed item across slots at 60fps. (In wrapped chip rows like `Section`, `←`/`→`/`h`/`l` move 1 slot; `↑`/`↓`/`j`/`k` jump by visual row or 1 slot in vertical lists!)
     - **Vim numeric count prefix (`1`–`99`)**: e.g. `5j` or `5k` jumps 5 slots in one press!
     - **`0` / `Home`** jumps to first slot; **`$` / `End`** jumps to last slot!
     - **Type-to-target Jump (`/`)**: while grabbed, press `/` (or start typing letters in a `"Place before…"` mini-input) to filter sibling targets (`"conc"` → `🏁 Conclusion`), `Enter` places it right before/after that target!
     - **`Enter` or `m`**: drops the item in place into the staged draft (keeps the move staged—does *not* trigger slow Git sync yet!).
     - **`Esc`**: cancels the current grab and snaps the item back to where it started before `m`.

2. **Sticky Rapid Nudge (`Alt+J` / `Alt+K` / `Alt+H` / `Alt+L` & `Alt+Arrow`):**
   - Keeps Bryan's existing `Alt+J`/`K` muscle memory, **upgraded**:
     - Pressing `Alt+J` moves +1 slot *immediately* in `projectedModel` without requiring `Apply` or opening a blocking `"Confirm Move"` stage (removing `BankSetupCardModal`'s modal confirmation trap for moves!).
     - Pressing `Alt+J` again (and again) moves +2, +3, +4… **coalescing** into a single move op targeting the final slot (`position: finalIndex` or final `before`/`after` anchor)!
     - Returning an item to its original position **cancels out** its net move op (and `bob` automatically treats net no-ops as zero-cost!).

3. **Desktop Drag-and-Drop (`⋮⋮` Grip / Draggable Chips, Rows & Tiles):**
   - Field rows, choice chips, Bank category tiles (even **across groups!**), group sections, and rule rows become draggable on desktop (`draggable="true"` or Pointer Events for smooth horizontal/vertical insertion markers).
   - Hovering over a target slot shows a crisp **2px accent insertion line** (`border-inline-start` for wrapped chips/tiles, horizontal line between field/rule rows), and dropping emits the coalesced single move (or `[category.set(group), category.move]` if dragged into another Bank group).

### 4.2 What the Visual Preview Looks Like

A great preview shows **spatial layout**, **relative movement**, and **semantic side-effects** simultaneously:

```text
  Section  ·  set on 2 of 2 · sub-groups the index            [+ Add choice]
  ┌────────────────────────────────────────────────────────────────────────┐
  │ 🪝 Intro 0   🍫 What is SASE? 1   ⋮┆  [ 🏁 Conclusion 0  ↑11 ]         │
  │ 📜 Prompt language (macros) 1   🔄 Agent turn 0   🚦 Gate 0            │
  │ 🩻 Sessions, clans & tribes 0   🧠 Memory 0   🗺️ Plan & artifacts 0    │
  │ 🖥️ Project 0   ⚙️ Automation (service) 0   🎬 The Demos 0              │
  │ 🛑 Why SASE is still NOT ready 0   🔮 Future Work 0   + Add choice     │
  └────────────────────────────────────────────────────────────────────────┘
```

Visual cues in the live preview:
1. **In-place rearrangement:** The chip/row/tile literally renders at its new destination in the list/grid.
2. **Origin ghost & delta badge:** A faint vertical hairline (`⋮`) marks the original gap if helpful, while moved items carry a subtle accent border + delta chip (`↑11` or `14→3` in muted tabular numerals).
3. **Bank Setup Hotkey & Group Preview (fixing a current blind spot!):**
   - `bob bank config update -d` **already returns** `hotkeys.shifted` (`[{ key, from, to }]`) and the complete post-image `categories[]` (`bank/config_update/run.rs:131-141`).
   - Paint the dry-run `report.categories` directly into the Bank Setup tile grid! Any category whose derived hotkey shifts shows a dashed badge (`G→H`) right on its tile, and moving a category into another group moves its tile under that group heading immediately.
4. **Album Regrouping Warning:**
   - If moving a `choices` field before another `choices` field changes which field groups the `[!records]` index (`report.group_before !== report.group_after`), show a clear accent pill in the consequence strip: `Index regroups from Status → Section (2 records affected)`.

### 4.3 Multi-Op Coalescing & Keybinding Consistency

To let users move several items (or add emojis + reorder) and commit once cleanly:
- **Draft Coalescing Rules (client-side before sending `ops` to `bob`):**
  - Successive `field.move` / `choice.move` / `rule.move` on the same item collapse to **one** op with the final `position`.
  - Successive `category.move` / `group.move` collapse to **one** op with the final `before`/`after` declared anchor relative to the current draft order.
  - Re-editing a field/choice just staged or added merges cleanly (or appends in order when targeting newly created keys).
- **Clearer `Enter` vs. `Apply` Separation:**
  - Today in `AlbumSchemaCardModal` (`241y:527`), `Enter` means *"Edit"* when clean, *or "Apply"* if a move/toggle is staged—which makes multi-edit batching impossible because you can't press `Enter` to edit a second item without accidentally committing!
  - **Adjustment:**
    - **`Enter`** (when browsing, not grabbed): **always** opens Edit on the selected target.
    - **`m` / `Enter` while grabbed**: enters/exits Grab mode (leaves edit in the pending batch).
    - **`⌘↵` (`Ctrl+Enter`)** or clicking **`Apply (N)`**: commits the entire staged draft in **one** transaction from anywhere in the card! (When an Edit stage form is open and popover is closed, `Enter` still previews/applies that stage for quick single-edit flow, or stages it when in batch mode.)
    - **`u`**: while a draft is staged (`draftOps.length > 0`), `u` pops/undoes the last staged draft change; when clean (`draftOps.length === 0`), `u` previews Undo of the last committed `Apply`!
    - **`Esc`**: cancels Grab → closes Popover → cancels open Stage → asks/clears pending draft → closes Modal.

---

## 5. Fast Performance Architecture (`Preview` & `Apply`)

### 5.1 Separating the Three Latency Sources

| Stage | Current Bottleneck | Root Cause in Code | Target Latency |
| --- | --- | --- | --- |
| **During moves / typing** | 250ms wait + process spawn per slot | `schemaMoveSelected` only moves 1 slot & waits for `bob -d` | **0ms** visual update; **one** `bob -d` after 250ms settle |
| **`bob albums update -d` (dry run)** | Full vault Markdown read (twice!) | `VaultSnapshot::load` + `with_overlay` reads/parses every `.md` file (`albums/update/run.rs:349`, `plan.rs:265`) | **< 40–80ms** via targeted album/folder scan |
| **`Apply` execution & unlock** | 2–5+ seconds modal lock | Synchronous `pre-sync` + `post-sync` GitHub SSH round-trips (`host_catalog/txn.rs:945`) + 4× vault scans + blocking post-apply `bob albums list` / `bob bank config` (`242a:120`, `248e:144`) | **< 100–200ms** perceived (`Apply` unlocks immediately; remote push runs in background) |

### 5.2 Three Concrete Speedups (Ranked by Safety & Impact)

#### Optimization 1: Eliminate Redundant Post-Apply Subprocesses (Zero Risk)
- **What happens today:**
  - `apiAlbumUpdateApply` (`242a:120`) awaits `albumRevalidateAfterSync()` -> spawns `bob albums list -f json`, scanning the *entire* vault again before unlocking the modal.
  - `apiBankConfigUpdateApply` (`248e:144`) awaits `bankConfigRevalidateAfterApply()` -> spawns `bob bank config -f json` and triggers `bankRevalidateMounts()` before unlocking the modal.
- **Fix:**
  - Have `bob albums update -f json` embed `"album": <AlbumReportEntry>` (which `verify_installed` in `albums/update/run.rs:462-507` **already computes**!) and `bob bank config update -f json` embed `"config": <ConfigReport>` (which `plan.rs:186` **already builds**!).
  - On `Apply` success, the modal immediately patches its in-memory model/cache from `result.report.album` / `result.report.config` and unlocks. Mount/catalog background revalidation (`bankRevalidateMounts` / owner callouts) happens asynchronously without blocking the modal!

#### Optimization 2: Targeted Vault Loading in `bob albums update` (Zero Risk)
- **What happens today:** `VaultSnapshot::load(vault)` (`notebooks/snapshot.rs:82`) reads the text of **every `.md` file in the entire vault** (daily notes, archive `done/`, references, notebooks, other albums' records) just to validate one album, and `plan_update` then runs `snapshot.with_overlay(...)` + `AlbumRegistry::from_snapshot(...)` a second time.
- **Fix:** For `albums update` (`dry_run` and `apply`), construct a targeted scan:
  1. Walk paths/filenames (`discovered` `NoteIndex` needs path strings only—no reading bodies of daily/ref/done notes!).
  2. Read full contents **only** for: root `*.md` notes (album claim uniqueness + `other_fields` storage conflicts), `<stem>/*.md` (the target album's records), and the target album's ancestor `parent:` chain (for root/owner checks).
  3. On `overlay`, validate only the proposed `<stem>.md` declaration against that already-built `NoteIndex` and `other_fields` without re-walking or re-classifying thousands of unrelated files.
  4. On `run_standalone` (`albums/update/run.rs:513`), avoid running the full preflight scan *again* inside `run_locked` if the preflight didn't sync any changes (i.e., if `pre-sync` did not advance `HEAD` or touch working tree files, reuse or skip redundant scans!).

#### Optimization 3: Decouple Remote Git Sync from Interactive Modal `Apply` (Explicit Trade-off)
Right now, `host_catalog::run_locked` (`txn.rs:945-1034`) performs:
1. `pre-sync` (`git ls-remote origin master` + optional fetch/merge)
2. Local guarded write + verify + scoped `git commit`
3. `post-sync` (`git ls-remote origin master` + `git push origin master`)

Let's compare three options for sync latency:

| Sync Strategy | Perceived `Apply` Latency | Multi-Host Safety | Critique & Recommendation |
| --- | --- | --- | --- |
| **A. Status Quo (Sync Pre + Sync Post)** | **2–5s** per Apply | Highest (blocks until pushed) | Terrible interactive feel even with multi-op batching; two SSH round-trips block the UI even after the file is safely committed locally. |
| **B. Sync Pre + Async Post-Sync** | **~1–2s** per Apply | High (always pulls before edit; pushes async) | Cuts latency ~50% with zero pre-edit drift risk, **still** feels noticeably laggy (~1.5s) on every single tweak because `pre-sync` still calls `git ls-remote` synchronously. |
| **C. Sync-on-Open + Local Commit (`--offline`) + Debounced Background `bob vault-sync`** | **~50–150ms** per Apply | High for desktop interactive editing (uses existing `bob_sync.lock` + `vault-sync` auto-merge/quarantine) | **Best interactive UX.** Opening the modal triggers one non-blocking `bob vault-sync` in background while you read/edit (if stale, vault generation watcher updates `expect`!). Clicking `Apply` runs `bob ... update --offline` (local `bob_sync.lock` + fingerprint guard + write + verify + scoped Git commit), unlocks immediately, and schedules a 1.5s debounced background `bob vault-sync` with a live status pill (`Saved · syncing…` → `Synced ✓` or existing `Retry sync` banner on conflict/offline!). |

**Why Strategy C is justified and safe in Bob:**
- `bob task move`, `bob relations rename`, `bob ref rename`, and `bob themes split` **already implement `--offline`** (`skip both sync cycles while keeping the lock and scoped local commit`, `docs/vault-git-sync.md:42`).
- `createGuardedUpdateSession` (`242aa:427-440`) **already models** `"Saved locally; sync failed"` + `"Retry sync"` (`bob vault-sync`).
- Because `expect` (`sha256:...` fingerprint) is re-checked against disk under `bob_sync.lock`, a background sync-on-open landing before `Apply` can never silently clobber a remote edit—it safely triggers the stale-rebase flow instead.
- If Bryan ever wants strict synchronous sync (e.g., on slow/contested edits), a setting or Shift-modifier (`--offline` default in interactive cards, synchronous fallback if `Retry sync` is pending) preserves total flexibility.

---

## 6. Visual Polish & Modal Ergonomics

Grounded directly in `~/tmp/screenshots/20261116_134836.png`, `241y-dom`, `248j`, and `styles.css`:

1. **Clean Album Card Header & Stats (`241y-dom:95-130`):**
   - Remove the duplicate `"2 zettels · dated notes"` button in the body. Merge album metadata editing (`Edit details` icon button `✎` or clicking the header subtitle chip) into the header block so the body begins cleanly with the schema fields.
2. **Collapse Empty Consequence Strip (`241y-dom:210`, `styles.css:8849`):**
   - Only mount/show `.bob-album-schema-consequence` when there is active status (`busy`, `preview`, `refusal`, `syncWarning`, or `dirty` staged ops). Eliminate the dead purple bar seen below `Preview this edit` in the screenshot.
3. **Contextual Toolbar Instead of 12-Button Wall (`241y-dom:279-310`):**
   - **When a stage form is open:** Show only the stage's own actions (`Apply` / `Stage edit` + `Cancel`) plus `YAML` if helpful—hide the 8 disabled browse buttons (`Edit`, `Add field`, `Toggle required`, `Move up`, `Move down`, `Remove`, etc.).
   - **When browsing:** Keep primary browse actions crisp (`Edit`, `+ Field`, `+ Choice`, `Move`, `More…`/inline toggles) and show a high-contrast primary **`Apply (N)`** button + **`Discard`** pill *only* when `draftOps.length > 0`!
   - Add visible **Move / Reorder** buttons (or `m` grab mode + `⋮⋮` drag handles) to **Bank Setup Card** as well (currently Bank Setup Card relies solely on hidden `Alt+J`/`K` shortcuts!).
4. **Preserve Modal Scroll & Focus with Targeted DOM Patching:**
   - Refactor `AlbumSchemaCardModal.paintSchemaCard()` (`241y:140`) and `BankSetupCardModal.paint()` (`248j:424`) to keep persistent structural containers (`headerEl`, `bodyEl`, `stageEl`, `consequenceEl`, `toolbarEl`, `popoverEl`) and only re-render the dirty region. Typing in an emoji filter box or nudging a chip with `Alt+J` will never reset scrollTop or disrupt IME/popover focus.
5. **Fix the `q`-While-Typing Bug in Bank Modals (`248k:601`, `248g:145`):**
   - Move the `inInput` check **above** the `!mod && !altKey && lower === "q"` shortcut check so typing `"quiet"`, `"square"`, `"queen"`, `"Liquor"`, or `"Equipment"` in Bank Setup / Category stages doesn't silently abort your edit!

---

## 7. Recommended Solution & Architecture

### 7.1 Component Architecture

```text
┌────────────────────────────────────────────────────────────────────────────┐
│ bob-plugins                                                                │
│                                                                            │
│  ┌──────────────────────┐        app.plugins.plugins["bob-emoji"].api (v1) │
│  │ bob-emoji            │◄─────────────────────────────────────────────┐   │
│  │ • gemoji + category  │                                              │   │
│  │ • multi-token search │   ┌──────────────────────────────────────┐   │   │
│  │ • label hints        │   │ bob-ledger-tools                     │   │   │
│  │ • shared recents     │   │                                      │   │   │
│  └──────────────────────┘   │  Shared UI Modules:                  │   │   │
│                             │  • EmojiPickerControl + Popover      │   │   │
│                             │  • ReorderDraftController (m/Alt/DnD)│   │   │
│                             │  • Targeted DOM Region Patcher       │   │   │
│                             │  • GuardedSession (multi-op + async  │   │   │
│                             │    post-sync + background revalidate)│   │   │
│                             └──────┬─────────────────────┬─────────┘   │   │
│                                    │                     │             │   │
│                        AlbumSchemaCardModal   BankSetupCardModal       │   │
│                                                + BankCategoryCardModal │   │
└────────────────────────────────────┼─────────────────────┼─────────────┘   │
                                     │ JSON stdin/stdout   │                 │
┌────────────────────────────────────▼─────────────────────▼─────────────┐   │
│ bob-cli                                                                │   │
│  • `bob albums update`                                                 │   │
│     ├─ Add `emoji` & `summary` to `album.set`                          │   │
│     ├─ Targeted vault scan (root albums + `<stem>/` + ancestor chain)  │   │
│     ├─ Embed updated `album` entry in JSON output                      │   │
│     └─ Add `--offline` (local bob_sync.lock + scoped commit, no push)  │   │
│  • `bob bank config update`                                            │   │
│     ├─ Embed full `config` slice in JSON output                        │   │
│     └─ Add `--offline` (local bob_sync.lock + scoped commit, no push)  │   │
│  • `bob vault-sync` (debounced background sync after Apply)            │   │
└────────────────────────────────────────────────────────────────────────┘   │
```

### 7.2 Phased Implementation Roadmap

1. **Phase 1 — Foundation & Quick Fixes (`bob-plugins` only, immediate UX win)**
   - Fix the `q`-in-input bug in `248k-plugin-bank-setup-card.js:601` and `248g-plugin-bank-category-new-stage.js:145`.
   - Preserve `category` in `scripts/gen-emoji-catalog.mjs`, upgrade `emojiSearch` (`030-emoji-model.js`) with multi-token + word-prefix + colon-optional matching + schema popular list + label suggestion helper, and expose `BobEmojiPlugin.api` v1 (`050-plugin.js`).
   - Build the shared `EmojiPickerControl` + anchored hybrid grid/list popover (`bob-ledger-tools`), wire it into Album (`choice`, `choice-add`, `field-add`) and Bank (`BankSetupCardModal` category `edit`/`new`, `BankCategoryCardModal` `+ New category` with inline `:` trigger + `Alt+E` button).
   - Clean up the Album Schema Card screenshot pain points: deduplicate `stats`, collapse empty `.bob-album-schema-consequence`, contextualize stage toolbar, switch to targeted DOM patching, and render Bank Setup Card's dry-run `report.categories` + hotkey shifts on the tile grid.

2. **Phase 2 — Instant Multi-Slot Reordering & Multi-Op Batching (`bob-plugins` client-side over existing `bob` protocols)**
   - Implement `projectDraftModel` + op-coalescing in `AlbumSchemaCardModal` and `BankSetupCardModal` so repeated `Alt+J`/`K`/`H`/`L`, Grab/Move Mode (`m` + `↑↓←→`/`hjkl` + Vim counts + `0`/`$` + `/` type-to-target), and Desktop Drag-and-Drop update the card at 0ms and batch into minimal ops (`field.move`, `choice.move`, `category.move`, `category.set`+`category.move` across groups, `group.move`, `rule.move`).
   - Paint origin hairlines, move delta pills (`↑5`), predicted Bank hotkey shifts (`G→H`), and Album regrouping badges (`Status → Section`) directly in the card before committing.
   - Adopt consistent `Enter` (edit / drop grab) + `⌘↵` / `Apply (N)` (commit batch) + `u` (pop staged op or undo committed apply).

3. **Phase 3 — Fast `Apply` & Album Identity Completeness (`bob-cli` + `bob-ledger-tools`)**
   - Add `--offline` to `bob albums update` and `bob bank config update`; trigger non-blocking sync-on-open + 1.5s debounced background `bob vault-sync` on Apply with a live `"Saved · syncing…"` header status and existing `Retry sync` fallback.
   - Include updated `album` (`AlbumReportEntry`) in `bob albums update` JSON and full `config` slice in `bob bank config update` JSON so modals patch in-place and unlock without waiting for a second `list`/`config` subprocess.
   - Scope `bob albums update` snapshot reads to root albums + `<stem>/` + ancestor notes (eliminating whole-vault file reads during dry-run previews and apply).
   - Extend `album.set` in `bob albums update` to edit `emoji` and `summary` (wiring the Emoji Picker into `Edit album details`).
   - Add automated unit tests (op coalescing, multi-token emoji search, `q`-in-input regression, `--offline` commit & async sync state transitions) and CDP E2E coverage.

---

## 8. Key Risks & Verification Checklist

- **Risk 1 — Stale-draft conflicts when `vault-sync` runs on modal open:**
  *Mitigation:* Never silently discard user edits. If background sync updates `eat.md` or `bank.md` while `draftOps` is empty, silently rebase `expect`; if `draftOps` is non-empty, keep the draft, mark the preview stale, and offer one-click `Re-preview against updated schema` (reusing the existing `rebase-preview` flow in `241y:624` / `248k:125`).
- **Risk 2 — `Modal` keyboard/IME & Electron focus traps inside popovers:**
  *Mitigation:* Use `event.isComposing || event.keyCode === 229` guards, keep the emoji popover inside `modalEl` with `aria-activedescendant` (so focus stays cleanly in the filter `<input>` while `↑↓↵` navigate), and suppress `Enter` propagation when popover is open so `Enter` picks the emoji rather than submitting `Apply`.
- **Risk 3 — Cross-group category ordering in `bank.md`:**
  *Mitigation:* Because `bankCategorySections` groups visually by `group` even when YAML keys are interleaved, compute `category.move` anchors strictly against the filtered/projected visual group neighbors (and emit `category.set { group }` first when dragging across groups).
- **Risk 4 — Offline/online divergence if user closes Obsidian 100ms after `Apply`:**
  *Mitigation:* Local commit is already durable in Git (`albums: update ...` / `bank: config ...`). Flush any pending debounced `bob vault-sync` on `onClose` / `onunload` (fire-and-forget process or run sync immediately if the user prefers `Pre-sync` safety).
