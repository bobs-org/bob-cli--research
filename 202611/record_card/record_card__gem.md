# Record Note Fields Card — Architecture, Critique & Design Recommendation

- **Researcher:** `gem` (independent analysis)
- **Date:** 2026-11-17
- **Scope:** Replacing native Obsidian Properties on record notes with an H1-anchored, schema-aware card and full interactive editing parity (`bob-cli` + `bob-plugins`, plus coordination with `plans/202611/double_equals_schema_keymap.md`)

---

## 1. Executive Summary

Hiding Obsidian's native YAML Properties panel on record notes and rendering a schema-aware card right under the `# Title` (`H1`) and above `## Notes` (`H2`) is **fundamentally the right direction**, and aligns naturally with how album notes and `~/bob/bank.md` already present structured metadata.

Looking closely at the live vault (`6` albums, `186` records across `eat`, `movies`, `podcasts`, `sase_blog_zettel`, `subscriptions`, and `tv`), the current screenshot (`~/tmp/screenshots/20261117_101208.png` showing `sase_blog_zettel/bead_lifecycle.md`), and the existing `bob-cli` / `bob-plugins` architecture reveals **five places where the initial requirements need sharpening or adjustment** before implementation:

1. **Name & Mental Model:** On a record note, the card displays and edits **record instance values** conforming to the parent album's schema — not the schema definition itself. Naming it **Record Card** / **Record Fields Card** (`⊞ Edit`, with a secondary `⊞ Schema` / `S` jump to the parent album's Schema Card) avoids colliding with `Edit album schema` (`242d-plugin-album-entrypoints.js`), which already resolves record notes to their *parent album*.
2. **Dual-Surface Parity (Inline View + Modal Editor), Not Inline CM6 Inputs:** Neither album headers nor `~/bob/bank.md` embed interactive `<input>`/`<select>` widgets inside CodeMirror `Decoration.widget`s. Both pair an **inline display/action card under H1** (`241v`/`241x` and `248a`/`248b`/`248c`) with a **keyboard-first Modal editor** (`AlbumSchemaCardModal` `241y*`, `BankSetupCardModal` `248k*`, and `Task Card` `320/330`) backed by `createGuardedUpdateSession` (`242aa`). Adopting that exact two-surface architecture is essential for Vim keybindings, CM6 focus stability, dry-run previews, and Reading/Live Preview parity.
3. **Conditional, Non-Source-Mode Frontmatter Suppression:** Blindly hiding `.metadata-container` breaks **Source mode** (`y` YAML excursion), hides **broken/orphan records** (`missing-parent`, `cyclic-parent`), and masks **`legacy`** (`lid`, `source_*`, `recur_id`) or **`unknown`** keys. Suppression must be scoped to verified `.bob-record-card-surface` views in Live Preview & Reading view, hide boilerplate + schema-owned + declared `legacy` keys, and surface any unexpected/unknown/invalid state loudly in the card.
4. **`subscriptions/*.md` Dual-Widget Coordination:** `bob-ledger-tools` (`241hg-plugin-bank-subscription-header.js`) *already* mounts `.bob-subscription-header` immediately after `# Title` (`H1`) in Live Preview and Reading view. The new Record Fields Card must explicitly establish widget precedence (`record` above `subscription`, Reading priority `49` ahead of `51` and ordered CM6 placement) and harmonious styling so `subscriptions/*.md` shows one cohesive header stack rather than two colliding cards.
5. **Close Backend Parity Gaps First:** `bob records update` currently takes positional CLI flags (`-s KEY=VALUE`), lacks `host_catalog::run_locked` (vault lock, pre-sync, scoped commit, post-sync), has no `expect` concurrency fingerprints, returns no `inverse_ops` for `u` undo, and cannot safely edit multi-value lists containing commas or titles. Likewise, `bob records show TYPE` caps `suggest` values at `top_values` (5 items) and does not inspect a single note's parsed fields, line numbers, legacy keys, or per-note findings. Closing these in `bob-cli` (`bob records inspect` + guarded `-i -` JSON envelope on `bob records update`) makes the frontend clean, atomic, and race-free.

**Recommended Solution:** Build a **Record Fields Card** in three clean slices — **(1)** `bob records inspect` + guarded JSON `bob records update -i -` using `host_catalog::run_locked`, **(2)** a fast, conditional inline card under `# Title` (rendered immediately from Obsidian `metadataCache` + cached `bob albums list` schemas and quietly verified/enriched via `bob records inspect`), and **(3)** a keyboard-first `RecordCardModal` wired to `createGuardedUpdateSession`, `==` (`248m-plugin-schema-double-equals.js`), `y` YAML excursion, `u` undo, and `S` parent-schema jump.

---

## 2. Current State Observed in Vault & Codebase

### 2.1 What Record Notes Look Like Today (`~/tmp/screenshots/20261117_101208.png`)

Inspecting `sase_blog_zettel/bead_lifecycle.md` in Obsidian Live Preview (screenshot `20261117_101208.png`) highlights the exact friction Bryan is reacting to:

1. Below the Obsidian inline title (`bead_lifecycle`), the native Properties widget renders **8 vertical rows** before any prose appears:
   - `parent: sase_blog_zettel`
   - `type: [[record]]`
   - `title: Bead Lifecycle`
   - `status: draft`
   - `claim: Bead triage/lifecycle needs to be thoroughly designed in v2.`
   - `section: future`
   - `created: 2026-11-17T07:55:39-0500`
   - `+ Add property`
2. Only *after* that entire property table does `# Bead Lifecycle` (`H1`) appear, followed by `## Notes` (`H2`).
3. **UX defects visible right in the screenshot:**
   - Raw slugs (`draft`, `future`) replace the album schema's rich labels (`✍️ Draft`, `🔮 Future Work`).
   - Boilerplate plumbing (`parent`, `type: [[record]]`, redundant `title`, full ISO `created` timestamp) eats over half the visible top fold.
   - Generic `+ Add property` and text inputs tempt edits that bypass `bob`'s schema validation, near-duplicate protection, and `[!records]` album-index synchronization.
   - Requiredness (`status`, `claim` are required; `section` is optional) and allowed choices/suggestions are invisible.

### 2.2 Live Record Schema Diversity Across the Vault

Checking `bob records list -f json`, `bob albums list -f json`, `bob records check -f json`, and representative vault files (`bead_lifecycle.md`, `eat/ninja_sushi.md`, `movies/f1.md`, `subscriptions/chatgpt.md`) shows the real shapes the card must handle seamlessly:

| Album (`stem`) | Count | Example Record | Declared + Merged Fields | Special Characteristics |
|---|---:|---|---|---|
| `eat` | 104 | `eat/ninja_sushi.md` | `status` (choices*), `category` (text+suggest*), `location` (text+suggest*), `visited` (date), `url` (url) | Wikilink `location` values (`[[nj_towns#^z-241117-0b\|cranford]]`), `legacy` keys (`lid`, `source_*`), `## Source` section after `## Notes` |
| `movies` | 12 | `movies/f1.md` | `status` (choices*), `year` (number `1888..2100`), `service` (text+suggest), `recommended_by` (text+suggest), `verdict` (choices), `watched_on` (date), `url` (url) | Sparse notes (`movies/f1.md` has *only* `status: to_watch` filled — 6 of 7 fields absent) |
| `podcasts` | 15 | — | `status` (choices*), `category` (text+suggest*), `url` (url) | `legacy` keys (`zorg_id`, `source_*`) |
| `sase_blog_zettel` | 4 | `bead_lifecycle.md` | `status` (choices*, 6 choices), `claim` (text*), `section` (choices, 15 choices) | Long prose `claim`, 15-option `section` catalog |
| `subscriptions` | 28 | `subscriptions/chatgpt.md` | `status`*, `amount`*, `cadence`*, `pricing` (`default: fixed`), `match` (`list: true`), `category` (suggest), `url`, `renews`, `ended` | Merges album-defined fields (`line != null`) with bank-synthesized fields (`line: null`), `list: true` array (`match`), `legacy` (`recur_id`), **and existing `.bob-subscription-header` widget** |
| `tv` | 23 | — | `status`*, `service` (suggest), `recommended_by` (suggest), `verdict` (choices), `watched_on` (date), `url` (url) | Sparse optional fields (`0/23` have `verdict`/`watched_on`/`url` filled) |

> **All 186 records currently pass `bob records check -f json` with `0` errors and `0` warnings**, meaning our clean-path property hiding will trigger across 100% of healthy records while still needing safe fallback behavior when a record becomes invalid or unlinked.

### 2.3 Existing Parity Patterns in `bob-plugins`

1. **Dual-View H1 Anchoring (`241v`, `241f`, `241g`, `241hg`, `248c`):**
   - **Reading View:** `registerMarkdownPostProcessor` finds the first `h1` outside code blocks (`root.querySelectorAll("h1")`) and inserts the header DOM via `anchor.parentNode.insertBefore(card, anchor.nextSibling || null)`.
   - **Live Preview:** CM6 `ViewPlugin.fromClass` checks `editorInfoField` + `editorLivePreviewField` (returning `Decoration.none` in Source mode!) and mounts a `Decoration.widget({ widget, side: 1 })` at `view.state.doc.line(anchor + 1).to` using `notebookHeaderLiveAnchor(docText)`.
   - **Property Hiding Pattern (`styles.css`):** Existing rules scope hiding strictly to annotated view containers:
     - `.bob-album-header-surface .metadata-property[data-property-key="record"] { display: none !important; }`
     - `.bob-bank-setup-surface .metadata-property[data-property-key="bank"] { display: none !important; }`
2. **Guarded Modal Editing (`241y*`, `242aa`, `242d`, `242e`, `248j/k/l`):**
   - `createGuardedUpdateSession` (`242aa-plugin-guarded-update-session.js`) standardizes revision-tracked `draftOps`, `250ms` debounced dry-run previews (`epoch`/`revision`/`identity`/`expect`/`generation` staleness guards), pre-apply dirty editor saving (`saveEditors`), `lock_busy` 10-minute retry loops (`lockWait`), and `inverseOps` undo.
   - `242e-plugin-album-yaml-excursion.js` switches the active pane cleanly into Source mode onto the target YAML line and attaches a floating `Done` pill to jump back to Live Preview.
3. **`==` Keymap & Target Dispatch (`plans/202611/double_equals_schema_keymap.md`):**
   - Planned `248m-plugin-schema-double-equals.js` (not yet present in `bob-plugins/plugins/bob-ledger-tools/src/`) intercepts exact Vim Normal `==` (`inputState.operator === "indentAuto"`, empty `keyBuffer`, no counts/registers) in capture phase, injects `<Esc>` via `CodeMirrorAdapter.Vim.handleKey`, and routes by `schemaDoubleEqualsTargetKind`.
   - Crucially, `double_equals_schema_keymap.md` previously chose `records: album_only` specifically because a user pressing `==` inside a record note did not want to edit the *album schema*. Now that record notes will have their own card, that decision should evolve cleanly.

---

## 3. Critique of the Plan & Justified Requirement Adjustments

Is this a good idea? **Yes — with high confidence.** Replacing Obsidian's raw YAML box on record notes solves real visual clutter, reveals schema semantics (`choices`, requiredness, `suggest`, clickable `url`/wikilinks), and stops ad-hoc frontmatter edits from bypassing `bob`.

However, implementing the requirements literally without adjustments would introduce subtle UX and reliability regressions. The table below explicitly calls out each recommended adjustment:

| # | Original Requirement | Critique / Risk If Taken Literally | Justified Adjustment |
|---|---|---|---|
| **1** | Render a **"schema card"** in record notes | On albums and `bank.md`, "Schema Card" means editing *field definitions/choices/rules*. A record note holds *field values* matching a schema, and `albumResolveSchemaTargetForFile` (`242d`) already maps record notes (`record-parent`) to `Edit album schema`. Using the same name conflates editing a record's data with changing every sibling record's schema. | Name the feature **Record Card** (or **Record Fields Card**, button `⊞ Edit`), keeping "Schema Card" (`⊞ Schema`) for album schemas — and provide an explicit **`S` / `⊞ Schema`** jump inside the Record Card to edit the parent album schema when needed (e.g., adding a new `section` or `status` choice). |
| **2** | **Full parity** with album & `bank.md` schema cards (inline editing under H1) | Placing `<input>`/`<select>`/`dropdown` form controls directly inside CM6 `Decoration.widget`s fights Obsidian editor focus, breaks Reading View vs Live Preview symmetry, breaks Vim `j`/`k`/`Esc`/`i`, and cannot easily render multi-column choice/suggest pickers + debounced diff banners. Notice neither album notes nor `bank.md` do inline CM6 editing! | Adopt **true architectural parity** with albums & `bank.md`: **(a) Inline Card under H1** for crisp scan, clickable links/pills, diagnostics, and one-click/targeted field launch; **(b) Interactive Modal Card** (`==` / `⊞ Edit` / clicking any field row) using `createGuardedUpdateSession`, `j`/`k`/`Enter`/`Ctrl+D`/`u`/`y` Source excursion. |
| **3** | **Hide frontmatter fields** in record notes | Blindly hiding `.metadata-container` breaks: (1) **Source mode** YAML editing (`y` excursion), (2) **broken/orphan records** (`missing-parent`, `cyclic-parent`) leaving zero UI to fix `parent`, (3) **`unknown` or extra custom fields**, and (4) leaving an awkward empty `Properties` header + `+ Add property` button if only individual `[data-property-key]` rows are hidden. Meanwhile, `legacy` keys (`lid`, `source_*`, `recur_id`) should be tucked out of everyday sight without deleting history. | Only apply `.bob-record-card-surface` in Live Preview & Reading view **after** confirming a valid parent album schema. Hide **managed keys** (`parent`, `type`, `title`, `created`, declared `fields[].key`, declared `legacy` keys). Collapse `.metadata-container` **only when zero unmanaged/unknown/broken properties remain visible**, surface `unknown`/diagnostic keys inside the card with `y` YAML jump, and expose `legacy` keys only via a muted modal footer / `↗ YAML`. |
| **4** | Place **underneath H1, above `## Notes`** | Works for standard record notes, *except* `subscriptions/*.md` (`241hg`) **already mounts `.bob-subscription-header` right after H1**. Uncoordinated mounting will interleave or clash two widgets in CM6 / Reading View. Also, some records have intro prose between H1 and `## Notes`, or `## Source` sections, or lack H1 if malformed. | Mount right after the **first H1 outside code** (matching `241g` `notebookHeaderLiveAnchor`), so any authored intro prose stays cleanly below the card and above `## Notes`. On `subscriptions/*.md`, enforce deterministic order (**Record Fields Card priority `49` above Subscription Header priority `51`** in Reading View, matching CM6 order) and shared visual spacing — or fold shared billing status badges cleanly. |
| **5** | Support the **`==` keymap** (`double_equals_schema_keymap.md`) | `double_equals_schema_keymap.md` currently sets `records = album_only`, leaving `==` on record notes as Vim reindent because editing the *album* schema on `==` inside a record felt wrong. | Extend `248m-plugin-schema-double-equals.js` (`schemaDoubleEqualsTargetKind`) cleanly: `bank` → `BankSetupCard`, `album` → `AlbumSchemaCard`, `record` → **`RecordCardModal`**, with **`S`** inside the modal opening the parent `AlbumSchemaCard`. Optionally allow `551-plugin-album-schema-fallback.js` (`Ctrl+Shift+P` when cursor is not on a task/link/dep) to fall back to `RecordCardModal` on records too. |

---

## 4. Detailed UX & Visual Design

### 4.1 What Each Frontmatter Property Becomes

Every piece of information visible in `screenshot 20261117_101208.png` is preserved in a cleaner, higher-signal hierarchy — nothing useful is lost:

| Frontmatter Key | Visual Treatment on Inline Card | Editable in Modal? | Rationale |
|---|---|---|---|
| `parent` (`"[[sase_blog_zettel]]"`) | **Header Breadcrumb:** `SASE Blog › 📇 SASE Blog Zettel` (clickable link to album note) | No (use `y` YAML or `bob` move if changing album) | Matches album header breadcrumbs; frees 1 vertical row |
| `type` (`"[[record]]"`) | **Noun Badge** in header (`Zettel`, `Restaurant`, `Movie`, `Subscription`) | No (invariant identity) | Eliminates `[[record]]` noise |
| `title` | Already shown in Obsidian Inline Title + `# H1` (card header stays compact without repeating H1!) | **Optional `[t] Title` action/row** (syncs YAML `title` + H1 + `[!records]` link safely if user renames) | Avoids visual redundancy unless title != H1 (shows subtle mismatch badge if drifted) |
| `created` | Quiet muted date token in header right (`Nov 17`, hover shows `2026-11-17T07:55:39-0500`) | Read-only in card (`y` YAML if backdating) | Preserves provenance in 10px without eating a row |
| **Required fields** (`required: true`) | Always rendered as labeled rows/chips in schema order. If unset/invalid: high-contrast warning chip (`! Claim required`) | Yes (primary rows, cannot clear optional-style) | Immediate visual accountability |
| **Filled optional fields** | Always rendered in schema order with formatted values | Yes (`Enter` edit, `Ctrl+D` clear) | High signal, zero clutter |
| **Unset optional fields** | **Compact `+ Optional` footer pills** on inline card (e.g., `+ Visited · Url`); full rows in Modal | Yes (click pill to jump straight to editing that field!) | Keeps sparse records like `movies/f1.md` (1/7 filled) clean & uncrowded |
| **`choices` fields** | Colored **emoji + label pills** (`✍️ Draft`, `🔮 Future Work`, `💚 Liked`) using album schema choices | Single-pick grid/filter list (+ `[` / `]` quick cycle!) | Instant scannability over raw slugs |
| **`suggest` fields** | Clean text or Obsidian-link chip (wikilink renders alias e.g. `cranford` + hover preview) | Combobox showing **all** folder values by frequency + near-duplicate warning | Prevents `Cafe` vs `Coffee` / typo drift |
| **`list: true` fields** (`match`) | Wrapped pill tokens (`CHATGPT *OPENAI`, `OPENAI *CHATGPT`) | Token editor: add chip, `Ctrl+D`/backspace remove, `Alt+J/K` reorder | Preserves multi-value bank patterns cleanly |
| **`url` fields** | Compact domain/label link (`↗ chatgpt.com` or schema label `↗ Manage`, full URL tooltip) | Validated URL input (`http://` / `https://`) | Prevents 90-char URLs wrapping awkwardly |
| **`date` fields** | Formatted `YYYY-MM-DD` with quiet relative hint (`2026-11-01 · 16d ago`) | Smart input (`today`/`t`, `yesterday`, `-2d`, `+1w`, ISO) | Matches Task Card date ergonomics |
| **`number` fields** | Tabular numeric chip (`$20`, `2025`) | Numeric input enforcing `min`/`max` bounds | Clear range feedback |
| **`legacy`** (`lid`, `source_*`, `recur_id`) | Hidden on inline card | Shown only in quiet collapsible `Legacy (1)` row or `↗ YAML` | Preserves migrated IDs without clutter |
| **Unknown / Diagnostic keys** | **Loud amber/red diagnostic row** inside card (`⚠ Unknown key: foo`) + `↗ YAML` jump | Highlighted diagnostic row + quick fix/clear/YAML jump | Never silently hides schema errors |

### 4.2 Inline Card Mockups (Reading View & Live Preview)

#### Example 1 — `sase_blog_zettel/bead_lifecycle.md` (Before vs After `screenshot 20261117_101208.png`)

When Properties are suppressed below Inline Title `bead_lifecycle`, `# Bead Lifecycle` sits cleanly at the top, followed immediately by the Record Fields Card and then `## Notes`:

```text
bead_lifecycle

# Bead Lifecycle
╭──────────────────────────────────────────────────────────────────────────────────────╮
│ ▾  📇 SASE Blog › SASE Blog Zettel · Nov 17          [⊞ Edit ==] [⊞ Schema] [↗ YAML] │
├──────────────────────────────────────────────────────────────────────────────────────┤
│ Status     [ ✍️ Draft ]                                                              │
│ Section    [ 🔮 Future Work ]                                                        │
│ Claim      Bead triage/lifecycle needs to be thoroughly designed in v2.              │
╰──────────────────────────────────────────────────────────────────────────────────────╯

## Notes
```

*(Design nuance for `sase_blog_zettel`: compact badge fields like `Status` + `Section` can sit cleanly in a responsive flex/2-col header grid or tight aligned table so 2-chip + 1-prose records take only ~3 lines vertically, while `## Notes` remains comfortably above the fold!)*

#### Example 2 — Sparse Optional Fields (`movies/f1.md`, 1 of 7 fields set)

```text
# F1
╭──────────────────────────────────────────────────────────────────────────────────────╮
│ ▾  🎬 Fun › Movies · 2025-11-xx                      [⊞ Edit ==] [⊞ Schema] [↗ YAML] │
├──────────────────────────────────────────────────────────────────────────────────────┤
│ Status     [ 🔖 To watch ]                                                           │
│ + Add      Year · Service · Recommended By · Verdict · Watched On · Url              │
╰──────────────────────────────────────────────────────────────────────────────────────╯

## Notes
```

Clicking `+ Year` (or any pill in `+ Add`) opens the `RecordCardModal` immediately focused on `year`'s number input!

#### Example 3 — Rich Mixed Types & `subscriptions/*.md` Composition (`subscriptions/chatgpt.md`)

On `subscriptions/*.md`, the Record Fields Card sits at priority `49` right after `# ChatGPT` (`H1`), with `.bob-subscription-header` (`241hg`, priority `51`) immediately beneath it using aligned card geometry and zero repeated title noise:

```text
# ChatGPT
╭──────────────────────────────────────────────────────────────────────────────────────╮
│ ▾  🔁 Bank › Subscriptions · 2026-04-xx              [⊞ Edit ==] [⊞ Schema] [↗ YAML] │
├──────────────────────────────────────────────────────────────────────────────────────┤
│ Status     [ 💚 Active ]       Pricing   [ 📌 Fixed ]       Cadence  [ 🗓️ Monthly ]  │
│ Charged    $20                 Category  Software                                    │
│ Shows up   [CHATGPT *OPENAI] [OPENAI *CHATGPT]                                       │
│ + Add      Manage · Renews · Ended                                                   │
╰──────────────────────────────────────────────────────────────────────────────────────╯
╭──────────────────────────────────────────────────────────────────────────────────────╮
│ Ledger · WF Checking · $20/mo · Last charge 2026-10-14 · [●●●●●●●●●●○○] 10/12 mos    │
╰──────────────────────────────────────────────────────────────────────────────────────╯

## Notes
```

Clicking `▾` toggles the Record Card to a 1-line collapsed summary strip matching `.bob-bank-setup` and `.bob-album-header`:

```text
▸  🔁 Subscriptions · 💚 Active · $20/mo · Software                  [⊞ Edit ==] [↗ YAML]
```

*(And if `bob` or parent-album resolution reports an error/missing required field, the card auto-expands a slim red/amber banner at the bottom of the card: `⚠ Claim is required — click to set` or `⚠ Unknown property 'foo' — open YAML`, and refuses to suppress `.metadata-container` if the parent album cannot be resolved!)*

### 4.3 Interactive Record Card Modal (`RecordCardModal`) — Full Parity Behavior

Opening the card via **`==`** (in Vim Normal mode anywhere in the note), **`⊞ Edit`**, Command Palette (`Edit record fields`), clicking any inline field/pill, or optional `Ctrl+Shift+P` fallback opens a centered **Record Card Modal** styled in the exact `--bob-*` / Task Card / Bank Setup Card idiom:

```text
╭──────────────────────────────────────────────────────────────────────────────────────╮
│ 📇 Bead Lifecycle   SASE Blog › SASE Blog Zettel · Clean              [S] Schema  [y] │
├──────────────────────────────────────────────────────────────────────────────────────┤
│  1 * Status     choices     ✍️ Draft                        →  ✍️ Draft              │
│▸ 2 * Claim      text        Bead triage/lifecycle needs...  →  ...designed in v2.    │
│  3   Section    choices     🔮 Future Work                  →  🔁 Agent turn   (MOD) │
├──────────────────────────────────────────────────────────────────────────────────────┤
│ Preview (1 file + album index update)                                                │
│  • sase_blog_zettel/bead_lifecycle.md: section future → turn                         │
│  • sase_blog_zettel.md [!records]: 🔮 Future Work → 🔁 Agent turn                    │
├──────────────────────────────────────────────────────────────────────────────────────┤
│ [↑↓/jk] Navigate   [Enter] Edit   [[]/[]] Cycle   [Ctrl+D] Clear   [y] YAML   [S] Schema│
│ [u] Undo (0)                                          [Esc] Cancel   [Ctrl+Enter] Save│
╰──────────────────────────────────────────────────────────────────────────────────────╯
```

#### Keyboard Grammar & Field-Type Editors

| Key / Gesture | Context | Action |
|---|---|---|
| `j` / `k` / `↑` / `↓` | Field list | Move active row cursor smoothly across schema fields (+ optional `[Title]` / `Legacy` diagnostic section). |
| `1`–`9` | Field list (not editing text) | Jump directly to field *N*. |
| `[` / `]` | On a `choices` row | Quick-cycle choice values left/right immediately without entering the sub-picker! |
| `Enter` / `Space` / `e` | Any editable field row | Enter the field's stage editor: **Choices** (searchable pill grid with album choice counts, instant filter, `Enter` select), **Suggest Text** (combobox showing *all* folder values sorted by count + wikilink alias matching + live `record_near_duplicate_value` warning badge), **Free Text** (auto-expanding input), **List** (pill chip add/remove/`Alt+J`/`Alt+K` reorder), **Date** (supports `today`/`t`, `yesterday`, `-3d`, `+1w`, `YYYY-MM-DD` with live weekday preview), **Number** (shows `min`/`max` bounds), **URL** (validates scheme). |
| `Ctrl+D` / `Backspace` | Focused field row | Unset optional field (plans removal of YAML key). On `required: true` field: displays gentle inline refusal (`Required by SASE Blog Zettel schema`). |
| `y` / `Ctrl+E` | Anywhere in modal | **YAML Excursion (`242e` style):** saves/switches note to Source mode, positions cursor on the active field's exact YAML line (or `created` insertion point), mounts floating `Done` button that verifies `bob records check` before returning to Live Preview. |
| `S` | Anywhere in modal | **Parent Schema Handoff:** if no unsaved edits (or after prompting/applying), opens `openAlbumSchemaEntry` on the parent album (`sase_blog_zettel.md`) so missing choices/fields can be added without losing context! |
| `Ctrl+Enter` | Anywhere in modal (when `draftOps` dirty) | Apply staged ops atomically through `createGuardedUpdateSession` (`host_catalog::run_locked` → vault commit + `[!records]` album index update), with `lockWait` progress if vault lock is busy. |
| `u` / `Ctrl+Z` | Clean modal after apply | Executes `inverse_ops` from the last commit through the same guarded transaction! |
| `Esc` | Sub-editor → Field list → Close | Steps out one level; if `draftOps` are staged at top level, asks/confirms discard (or discards cleanly if unmodified). |

> **Why Staged Draft + `Ctrl+Enter` (matching `AlbumSchemaCardModal` & `BankSetupCardModal`) beats auto-committing every keystroke:** Updating `status`, `verdict`, and `watched_on` on a movie in one modal session runs a fast `250ms`-debounced `bob records update -d` dry-run as you edit (showing exact `[!records]` index impact and typo warnings live), and then commits **all three fields in one vault lock acquisition and one atomic `records: update` git commit**, producing one clean `inverse_ops` entry for `u` undo! For quick single-field edits, `==` → `Enter` (or `[`/`]`) → `Ctrl+Enter` is still effortless muscle memory.

### 4.4 `==` Keymap Evolution (`plans/202611/double_equals_schema_keymap.md`)

In `plans/202611/double_equals_schema_keymap.md`, Section 2 currently specifies `records = album_only` ("Keep `==` on records as Vim reindent; do not open parent album"). With the Record Card introduced, extending `schemaDoubleEqualsTargetKind` creates one unified, memorable mental model across all three structured note classes in Bob:

| Note Class (`frontmatter.type`) | `==` Action (Normal mode, Live Preview, exact `==`, no count/register) | Secondary Access |
|---|---|---|
| `bank` (`~/bob/bank.md`) | Opens **Bank Setup Card** (`openBankSetupCard`) | `⊞ Edit` inline button |
| `album` (`eat.md`, `sase_blog_zettel.md`, ...) | Opens **Album Schema Card** (`openAlbumSchemaEntry`) | `⊞ Schema` inline button, `Ctrl+Shift+P` fallback (`551`) |
| `record` (`eat/*`, `sase_blog_zettel/*`, ...) | Opens **Record Card** (`openRecordCardEntry`) | `⊞ Edit` / field click, **`S` inside modal → Parent Album Schema Card**, optional `Ctrl+Shift+P` fallback when not on a task/link/dep |
| All other notes / Source mode | Native Vim `==` indentation untouched | — |

*(Note: Preserve `vim-indent` behavior cleanly whenever count/operator-pending/visual/Source mode is used, matching `248m`'s exact `operator === "indentAuto" && keyBuffer === ""` guard.)*

---

## 5. Backend (`bob-cli`) & Frontend (`bob-plugins`) Implementation Plan

### 5.1 Required `bob-cli` Upgrades (`src/native/records/`)

Why not let Obsidian call `app.fileManager.processFrontMatter`? Both `bob-plugins` conventions (`211-parent-frontmatter-plan.js` / prior research) and `bob` architecture prohibit it because `processFrontMatter` rewrites YAML formatting arbitrarily, does not validate against the parent album schema, and leaves the parent album's `> [!records]` callout stale.

Today's `bob records` already has strong planning/rendering code (`plan.rs`, `render.rs`, `check.rs`), and `bob albums update` + `bob bank config update` (`bank/config_update/run.rs`) show the exact guarded JSON pattern to copy:

1. **New Subcommand: `bob records inspect <TARGET> [-b DIR] [-f FORMAT] [-h]`** *(alphabetical under `bob records` per `sase/memory/cli_rules.md`)*
   - Reads **only** the target record note, its resolved album + owner ancestry, and sibling records in that **single album directory** via `RecordCatalog::folder` (fast `O(folder_size)`, avoiding full-vault scans on UI interactions!).
   - Returns `schema_version: 1` JSON containing:
     - `path`, `stem`, `title`, `type`, `album`: `{ stem, title, owner, breadcrumb, emoji, dated_notes, index_facets, schema_fingerprint }`
     - `record_fingerprint` (`"sha256:..."` of current file bytes)
     - `lines`: 1-based YAML line map per present key (including `parent`, `type`, `title`, `created`, fields, legacy, unknown) + `insert_line` for `y` YAML excursion!
     - `fields`: schema fields in declaration order merged with current value, display label, `state` (`set` | `absent` | `invalid`), `line`, full `suggestions` list (`[{ value, display, count }]` ranked by frequency — **not** truncated to 5 like `bob records show`!), and `choices` with counts.
     - `legacy_present`: `[{ key, value, line }]`
     - `unknown_keys`: `[{ key, value, line }]`
     - `findings`: per-note `records check` diagnostics (`record_missing_field`, `record_invalid_value`, `record_unknown_field`, `record_parent_mismatch`, `record_near_duplicate_value`, etc.).
   - Also exits cleanly with typed refusal JSON when `parent` is missing/broken so the plugin safely keeps native Properties visible instead of masking the error.

2. **Upgrade `bob records update` With Guarded JSON Envelope Mode (`-i, --input <FILE>`)** *(keeping `bob records update TYPE STEM [-s ...] [-n ...]` 100% backward-compatible per `cli_rules.md`!)*
   - Add `-i, --input <FILE>` (`-` reads stdin) following `bob albums update`:
     - Request JSON envelope:
       ```json
       {
         "schema_version": 1,
         "target": "sase_blog_zettel/bead_lifecycle.md",
         "expect": {
           "record_fingerprint": "sha256:...",
           "schema_fingerprint": "sha256:..."
         },
         "ops": [
           { "op": "field.set", "key": "section", "value": "turn" },
           { "op": "field.unset", "key": "url" },
           { "op": "list.set", "key": "match", "values": ["OPENAI *"] },
           { "op": "title.set", "value": "Bead Lifecycle" }
         ]
       }
       ```
     - **Dry-run (`-d`):** skips lock/sync, runs the planner, validates near-duplicates (`warnings`), computes `album_index` diff, unified file diffs, `after_fingerprint`, and **`inverse_ops`** (capturing exact prior `field.set` / `field.unset` / `list.set` / `title.set` state).
     - **Real apply:** wraps `host_catalog::run_locked(vault, &child_env, json_mode, "records", ...)` just like `bob bank config update` (`bank/config_update/run.rs:372`) and `bob albums update`:
       - Pre-syncs vault, reloads target + folder + album inside lock, verifies `expect.record_fingerprint` & `expect.schema_fingerprint` (returning typed `stale_record` / `stale_schema` errors on drift), applies `PlannedTxn` writing both the record note and rebuilt album `[!records]` index atomically, commits with scoped subject `records: update <path>`, post-syncs, and supports `lock_busy` retry cleanly for `createGuardedUpdateSession`.
     - **Structured Types:** JSON `ops` eliminate comma-splitting fragility on `list: true` arrays (`match`), safely support multiline/quoted values (`claim`, wikilinks with `|`), and resolve natural date shorthands (`today`, `yesterday`, `±Nd`) consistently. (Note: `title.set` should update `title` frontmatter + matching `# H1` if previously synchronized, plus rebuild `[!records]` index link labels.)

### 5.2 `bob-plugins` Frontend Architecture (`bob-ledger-tools` + `bob-navigation-hotkeys`)

#### Rendering Strategy: Instant First Paint + Authoritative Background Verify

- **Why not block H1 card render on spawning `bob` every time a tab opens?** Rapidly flipping tabs (`Ctrl+O` / `Ctrl+Tab`) should render in `<5ms` with zero layout jump after H1.
- **Two-tier read model:**
  1. **Instant Local Render:** Compose `app.metadataCache.getFileCache(file).frontmatter` with the already-cached `bob albums list -f json` service (`241m-plugin-album-data-service.js`) whenever `albumSchemaEntryKindOf(frontmatter) === "record"` and `albumResolveSchemaTargetForFile` succeeds.
  2. **Lazy Authoritative Inspect (`bob records inspect`):** Run on **Modal open (`==` / `⊞ Edit`)** immediately (for `record_fingerprint`, line numbers, full `suggest` frequency list, and near-duplicate checks), and optionally debounced (`~150ms`) on active record view if local heuristics detect potential issues/stale cache — updating the inline card in place cleanly.

#### Conditional CSS Frontmatter Suppression (`styles.css`)

To eliminate both the field list **and** Obsidian's empty `Properties` / `+ Add property` container cleanly without hiding unrecognized fields or Source mode:

1. Toggle `.bob-record-card-surface` on the view container (`.markdown-preview-view` in Reading view; `.markdown-source-view.is-live-preview` in Live Preview — **never** Source mode!) **only when** parent album resolution succeeds AND the inline card actually mounted.
2. Hide explicitly managed keys via `data-property-key` rules generated/stamped safely (for boilerplate `parent`, `type`, `title`, `created`, plus schema keys via DOM `data-bob-record-managed="true"` attribute synced on `.metadata-property` nodes or explicit selector list):
   - `.bob-record-card-surface .metadata-property[data-bob-record-managed="true"] { display: none !important; }`
3. Hide `.metadata-container` header & `+ Add property` **only when no unmanaged property rows remain visible** (using CSS `:not(:has(.metadata-property:not([data-bob-record-managed="true"])))` on `.bob-record-card-surface .metadata-container` — Electron/Chromium supports `:has()` natively, and falling back cleanly if an `unknown` property is present so Obsidian's native error/property row stays visible until removed!).
   - Alternatively, if unknown keys are rendered inside the Record Card's diagnostic strip too, mark whether `.bob-record-card-surface--clean` hides the container cleanly while `.bob-record-card-surface--has-unknown` leaves unknown rows exposed! Keeping unknown/non-managed rows visible in Properties **and** flagging them in the card makes data-loss impossible.

#### Proposed Module Breakdown in `bob-plugins`

1. **`bob-ledger-tools/src/`:**
   - **Record inspect & update service (`249a`):** Wraps `bob records inspect` (single-flight + mtime/modify invalidation) and `bob records update -i -` (dry-run + apply), exporting `createRecordUpdateSession` on top of `242aa` (`createGuardedUpdateSession`).
   - **Record card view model (`249b`):** Normalizes `inspect` / cached `(frontmatter, albumSchema)` into ordered display fields, missing required alerts, `+ Optional` footer items, clickable URL/wikilink descriptors, `created` relative badge, and diagnostic banner.
   - **Record card inline DOM (`249c`) & dual-view host (`249d`):**
     - Shared DOM builder for Reading View (`registerMarkdownPostProcessor` at priority `49` — strictly ahead of `51` `subscriptionSurfaces`!) and Live Preview (`CM6 ViewPlugin` anchored at `notebookHeaderLiveAnchor`, `side: 1` ordered before `subscriptionHeader` via `Prec.high`/explicit DOM order).
     - Passive event guards: never steal CM6 focus on render; click handlers bail cleanly when clicking `<a href>` / `.internal-link`; clicking a field pill dispatches `openRecordCardEntry(file, { focusField })`.
     - Collapse state persisted cleanly (e.g. `localStorage` global or per-album toggle).
   - **Record card modal (`249e` / `249f`):** `RecordCardModal` extending `Modal` with field list keyboard navigation, choice/suggest/list/date/number/url stage sub-editors, near-duplicate banner, diff/index consequence preview, `y` YAML excursion (reusing/generalizing `242e`), `S` parent schema jump (`openAlbumSchemaEntry`), `u` undo, and `Ctrl+Enter` guarded commit.
   - **Keymap & Entrypoints:** Extend planned `248m-plugin-schema-double-equals.js` (`schemaDoubleEqualsTargetKind` returns `"record"` → `openRecordCardEntry`) and register Obsidian command `Edit record fields`.
2. **`bob-navigation-hotkeys/src/551-plugin-album-schema-fallback.js`:**
   - Optionally route `Ctrl+Shift+P` fallback on `record` notes (when cursor is not on a task/link/dep line and no Task Card target exists) to `openRecordCardEntry`, giving complete parity between `Ctrl+Shift+P` and `==` across `bank`, `album`, and `record` notes.

---

## 6. Edge Cases, Risks & Mitigations

| Risk / Edge Case | What Goes Wrong Naively | Mitigation in This Design |
|---|---|---|
| **`subscriptions/*.md` widget clash** | `.bob-subscription-header` (`241hg`) mounts at the exact same post-H1 anchor in both views. | Reading priority `49` (Record Card) vs `51` (Subscription Header) + explicit CM6 ordering keeps Record Card consistently on top; harmonized border/gap styling prevents visual double-frames. |
| **Dirty `## Notes` buffer when applying modal edit** | Applying `bob records update` on disk while user has unsaved typing in `## Notes` overwrites or conflicts in Obsidian. | `createGuardedUpdateSession` calls `saveEditors` before locking, passes `record_fingerprint` into `host_catalog::run_locked`, and reloads updated file cleanly after scoped commit. |
| **Orphan / broken `parent` record** | Hiding `.metadata-container` leaves an unreadable blank header with no way to fix `parent: "[[...]]"`. | Card refuses `.bob-record-card-surface` hiding when `albumResolveSchemaTargetForFile` fails; renders compact warning card with `↗ Fix YAML (y)` instead. |
| **Stale `metadataCache` during rapid edits** | Modal closes after `bob records update` writes disk, but Obsidian's `metadataCache` lags 50–100ms, causing inline card flash. | Optimistically push the just-applied `inspect`/updated state into the inline card's per-path store until vault `'changed'` + `metadataCache`'s `'resolve'` event catches up. |
| **YAML comments, formatting, & wikilinks** | Frontmatter edits via Obsidian APIs corrupt unquoted/quoted YAML, strip comments, or break `[[file#^id\|alias]]`. | Zero JS YAML writing: **every write goes through `bob records update -i -`**, preserving untouched YAML spans cleanly (`plan.rs`/`render.rs`). |
| **Large `suggest` list UX (`eat` has 104 records)** | `bob records show` only returns top 5; users pick typos (`coffee` vs `Coffee` vs `Cafe`). | `bob records inspect` returns full sorted distinct folder values; Suggest Combobox filters on both raw target and `\|alias` and renders `bob`'s near-duplicate warning live before saving. |
| **Missing `# Title` H1 or stale `H1` vs `title`** | Anchor lookup misses H1, hiding card or mounting above title. | Fallback CM6 anchor right after frontmatter fence (`---`) if H1 is missing (matching `notebookHeaderLiveAnchor`), plus optional mismatch indicator if YAML `title` differs from H1 text. |

---

## 7. Verification Plan

Before marking the feature ship-ready across slices:

1. **Backend (`bob-cli`, `cargo test`):**
   - `bob records inspect` single-record JSON snapshots: healthy record (`bead_lifecycle`), sparse record (`f1`), list+legacy record (`chatgpt`), wikilink+legacy record (`ninja_sushi`), broken-parent refusal, and missing-required / near-duplicate findings.
   - `bob records update -i -` JSON envelope tests: `--dry-run` (`inverse_ops`, `album_index` diff, no vault lock), real apply (`host_catalog::run_locked`, scoped commit `records: update ...`, `[!records]` index update in same txn), `stale_record` and `stale_schema` refusal on `expect` mismatch, `list.set` arrays containing commas/quotes, and `u` inverse roundtrip restoring byte-for-byte original markdown.
   - CLI contract conformance against `sase/memory/cli_rules.md` (`bob records --help` alphabetical subcommands/options, short flags for every public long option, backward-identical positional `TYPE STEM -s ...` behavior).
2. **Frontend (`bob-plugins` unit tests & build):**
   - Conditional surface suppression unit tests (Live Preview clean record → collapsed container; Source mode → untouched; broken parent / unmanaged extra key → native row remains visible).
   - Anchor & multi-widget order tests (H1 present + intro prose + `## Notes`; `subscriptions/*.md` ordering; missing H1 fallback).
   - `248m` `==` router unit tests across `bank`, `album`, `record`, plain note, Visual/Operator/Source modes, and counts.
3. **End-to-End Obsidian Verification (CDP on scratch vault):**
   - Inspect live rendered pixels across `bead_lifecycle.md`, `f1.md`, `ninja_sushi.md`, `chatgpt.md` in **Live Preview**, **Reading View**, and **Source Mode**.
   - Exercise full keyboard workflow end-to-end: `==` open → `j`/`k` → `[`/`]` cycle `status` → `Enter` edit `claim` / `section` / `match` → check live diff & `[!records]` preview → `Ctrl+Enter` save → verify `u` undo → `S` open parent album schema → `y` YAML excursion + `Done` return → `Ctrl+Shift+P` fallback parity.

---

## 8. Recommended Solution & Phased Rollout

Build the **Record Card** in three incremental, independently testable slices:

1. **Slice 1 — `bob-cli` Record Protocol Parity (`bob records inspect` + Guarded `bob records update -i -`):**
   - Add `bob records inspect <TARGET> -f json` returning single-note parsed fields, line numbers, full ranked `suggest` lists, legacy/unknown keys, findings, and `record_fingerprint` + `schema_fingerprint`.
   - Add `-i, --input <FILE>` JSON envelope mode + `host_catalog::run_locked` + `expect` + `inverse_ops` + `list.set`/`title.set` to `bob records update`, leaving existing positional CLI usage untouched.
2. **Slice 2 — Read-Only Inline Record Card & Safe Property Hiding (`bob-ledger-tools`):**
   - Render `.bob-record-card` cleanly below H1 (above `## Notes`, ordered ahead of `.bob-subscription-header` on `subscriptions/*.md`) from cached album schema + `metadataCache` with silent `bob records inspect` reconciliation.
   - Enable conditional `.bob-record-card-surface` CSS suppression in Live Preview & Reading view only when parent resolution succeeds and `.metadata-container` holds no unmanaged keys.
   - Include collapse toggle (`▾`/`▸`), `+ Optional` click-to-edit footer pills, `⊞ Schema` parent link, and `↗ YAML` excursion button.
3. **Slice 3 — Keyboard-First `RecordCardModal` & `==` Integration (`bob-ledger-tools` + `248m` + `551`):**
   - Implement `RecordCardModal` on `createGuardedUpdateSession` (`242aa`) with choice picker + `[`/`]` cycling, full `suggest` combobox + near-duplicate warning, date shorthand parser, number range checks, list token editor, `y` YAML excursion, `S` parent schema jump, `u` undo, and live `[!records]` preview.
   - Flip planned `248m-plugin-schema-double-equals.js` from `records: album_only` to unified `bank` / `album` / `record` `==` routing (plus optional `Ctrl+Shift+P` fallback in `551`).
