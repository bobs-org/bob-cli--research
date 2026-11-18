# Design & Critique: Cyclic Alphabetical Navigation (`<` / `>`, `N of M`, `[n` / `]n`) for Album Record Notes

**Date:** 2026-11-18  
**Scope:** `bob-cli` (albums, records, capture, periods) & `bob-plugins` (`bob-ledger-tools`, `bob-navigation-hotkeys`)  
**Status:** Design research & architectural recommendation

---

## 1. Executive Summary & Verdict

You asked to automatically maintain `<` and `>` links across every record note in an album so that:
- `[n` and `]n` step cyclically and alphabetically between records in that album (with a 2-record album pointing each record's `<` and `>` at the other);
- `N of M` renders near those links showing the record's position in the walk out of the album total; and
- the whole experience is **intuitive, reliable, and genuinely beautiful**.

### The Short Verdict

- **Keep the user experience goal — it is a great fit for albums.** Albums are browseable collections (`eat`, `movies`, `subscriptions`, etc.), and flipping alphabetically through records with `[n` / `]n`, `[[` / `]]`, and a crisp `‹  N of M  ›` pager directly complements the new Record Sheet.
- **Reject writing `<` and `>` links into record note Markdown files.** Materializing neighbor pointers on disk creates a two-source-of-truth paradox with dynamically rendered `N of M`, collides directly with `bob-cli`'s recent cleanup making empty record notes frontmatter-only (`cfc3177c`, `2f80442b`), causes multi-file write churn and open-buffer races, pollutes Obsidian Backlinks/Graph/Delete Guard (`countDeleteGuardBacklinks`), and hits a subtle empty-label bug in the `n` Walker Footer if bare `"<"` / `">"` aliases are used.
- **Recommended Solution:** **Virtual (Computed) Album Record Navigation** driven by one shared plugin resolver (`bob-ledger-tools` `api.recordNav` v1 over Obsidian's live `vault` + `metadataCache`), rendered as a clean typographic pager (`‹  4 of 23  ›`) inside the **Record Sheet** (plus a read-only mobile fallback), wired directly into `[n` / `]n` / `[[` / `]]` in `bob-navigation-hotkeys`, and mirrored with neighbor names in the **`n` Walker Footer** (`⇄ Links · 4 of 23 · ‹ Prev · Next ›`). Zero bytes are ever written to record Markdown files.

### Summary of Recommended Adjustments to Requirements

| Requirement | Original Proposal | Recommended Adjustment | Why |
| --- | --- | --- | --- |
| **Storage of `<` / `>` links** | Automatically write `<` / `>` wikilinks into every record note's Markdown | **Compute dynamically** in `bob-plugins`; keep record Markdown pure data | Eliminates drift vs. `N of M`, write churn, buffer races, backlink pollution, and body clutter |
| **Link glyph & destination visibility** | Bare `<` and `>` links | Render typographic **`‹` and `›`** inside the sheet, with **neighbor titles** in tooltips, Obsidian hover previews, and the `n` Walker Footer | Matches Bob's period-note & breadcrumb typography (`‹ W44` / `W46 ›`), prevents blank arms in `linksWalkerFooterLabel`, and shows *where* a link goes |
| **Single-record edge case (`M = 1`)** | Naive modulo wrap would link `<` and `>` to `self` | Show `1 of 1` with **disabled/muted `‹` and `›`** (`prev = null, next = null`) | Self-navigation feels broken; cycling starts cleanly at `M >= 2` (matching your `M = 2` example) |
| **Definition of "alphabetical"** | Unspecified (title vs. filename stem, case/numeric/accent rules, grouped vs. flat) | **Flat album-wide walk sorted by display title** (fallback: humanized stem, then path) using case- & accent-insensitive natural collation | Matches visible titles, keeps `M` equal to the album tally even on grouped albums, and orders `"2"` before `"10"` and `"Éclair"` before `"Zebra"` |
| **Mobile Obsidian support** | Implicitly handled by raw Markdown links | Enable a lightweight **read-only Record Nav header on Mobile** using `vault` + `metadataCache` | `bob-ledger-tools` already sets `isDesktopOnly: false` and needs no `bob` subprocess for sibling discovery |

---

## 2. Codebase Ground Truth

Before critiquing or designing, here is how the relevant machinery in `bob-cli` and `bob-plugins` works today.

### 2.1 How `[n`, `]n`, `[[`, `]]`, and the `n` Walker Footer Work

1. **Keymaps & Repeat (`bob-navigation-hotkeys`)**:
   - `490-plugin-lifecycle.js` registers `open-next-link` (`]n`) and `open-prev-link` (`[n`). Both call `rememberBracketRepeatType("n")` and `openLabeledBodyLink("next" | "prev")`.
   - `546-plugin-bracket-repeat.js` remembers `"n"` in `localStorage` (`bob-navigation-hotkeys-bracket-repeat`), so `]]` and `[[` repeat `openLabeledBodyLink("next" | "prev")`. Uppercase `]}` / `[{` currently have `BRACKET_REPEAT_UPPERCASE_PLANS.n = null`.
   - `670-plugin-project-files.js` (`openLabeledBodyLink` → `findFirstRenderedLink`) scans the active note's text **skipping YAML frontmatter and fenced code blocks**, and opens the first wikilink or Markdown link whose rendered text matches `renderedLinkMatchesNavLabel`.
   - `680-plugin-link-parse.js` defines `renderedLinkMatchesNavLabel(renderedText, label)`:
     - `prev`: `text === "prev"` OR `/^[‹<]/.test(text)`
     - `next`: `text === "next"` OR `/^[›>]/.test(text)` OR `/[›>]$/.test(text)`
   - `openOrCreateLinkCandidate` (`640-plugin-notes-and-task-move.js`) calls `captureActiveFilePosition()` before `openResolvedLink`, so `<C-o>` jump history works automatically.
2. **The `n` Walker Footer (`bob-ledger-tools` + `bob-navigation-hotkeys`)**:
   - `482-walk-mode-nav-api.js` exposes `api.walkMode.links({ path, content })`, which calls `findFirstRenderedLink` + `toLineLinkCandidate` for `"prev"` and `"next"` and returns `{ ok: true, prev, next }`.
   - `124-links-walker-footer.js` paints the status bar when `n` is the active family:
     - `linksWalkerFooterLabel(link, direction)` formats `"prev"`/`"next"` via stem/daily-date formatting, and for anything else strips leading/trailing `[‹<>›]` (`text.replace(/^[‹<>›]\s*/, "").replace(/\s*[‹<>›]$/, "").trim()`).
     - `linksWalkerFooterArm` prepends `"‹ "` or appends `" ›"`.
     - Clicking either status-bar arm (`linksWalkerFooterActivate`) re-verifies `walkMode.links` and executes `bob-navigation-hotkeys:open-prev-link` or `open-next-link`.
   - **Important bug uncovered in `124-links-walker-footer.js` lines 7–12**: If a note actually contains `[[target|<]]` or `[[target|>]]`, `linksWalkerFooterLabel` strips `"<"` / `">"` down to `""` and returns `""` *without* falling back to `stem`! That causes the status bar to render blank buttons (`⇄ Links · ‹  ·  ›`).

### 2.2 How Period Notes vs. Album Record Notes Differ

- **Period Notes (`docs/periods.md`, `src/native/periods/scaffold.rs`, `src/native/periods/labels.rs`)**:
  - Period notes live on an **immutable calendar grid**. `2026-W45` is permanently between `2026-W44` and `2026-W46`. Once `bob periods ensure` writes `[[2026/2026-W44|‹ W44]] · [[2026/2026-Q4|↑ 2026-Q4]] · [[2026/2026-W46|W46 ›]]`, those links never need updating.
- **Record Notes (`docs/records.md`, `src/native/records/`, `src/native/albums/`)**:
  - Recent commits show a clear architectural trajectory:
    - `cfc3177c`: `feat(records): create records without empty Notes section and add tidy command`
    - `2f80442b`: `feat(records): write H1-less record notes and tidy redundant H1s` — explicitly establishing in `docs/records.md` that *"Record notes carry no H1: the frontmatter `title` is the title's one home (the record sheet renders it)... A note with no ordinary bullets and no sections ends right after the closing `---`."*
    - `bob-plugins` commits `60b5602`, `f8a8619`, `9ad471d`: `bob-ledger-tools` mounts the **Record Sheet** (`242i-k`) at the top of canonical `type: [[record]]` notes in Desktop Reading view and Live Preview, rendering the `title` in page-title styling, the `Root › Album › noun` breadcrumb, schema fields, ghosts, `created` footer, and other properties fold — while hiding Obsidian's native Properties and inline title (`.bob-record-sheet-hides-properties`).
  - Meanwhile, `bob albums sync` (`src/native/albums/sync.rs`, invoked with a 3-second debounce by `241m-plugin-album-data-service.js`) **only** writes the generated `[!records]` callout inside `<album>.md` and `[!albums]` catalogs in owner notes. It **never** touches record notes when new siblings appear or disappear.
  - Record sorting inside `src/native/albums/grouping.rs` (`title_order`, line 404) sorts by `title.to_lowercase()` then `path`, though `[!records]` itself groups by choice field (`status`) and optional `index_by` subgroup first.

---

## 3. Critique of the Original Plan (Materialized `<` / `>` Links in Record Notes)

Writing `<` and `>` wikilinks directly into every record note file works well for **Period Notes**, so it is natural to reach for the same pattern here. However, albums have fundamentally different invariants, and materializing neighbor links into every record note carries serious architectural costs:

### 3.1 The Two-Source-of-Truth Paradox (`N of M` Already Forces Runtime Album Knowledge)
Notice your own third bullet:
> *"we should also start rendering the `N of M` text (or something like that) somewhere close to these links"*

Nobody wants `N of M` stored inside every `.md` file — adding one `"Aardvark"` record would force rewriting every single file in `eat/` just to increment `N` and `M`. That means **something in `bob-plugins` (`bob-ledger-tools`) must already resolve the album's full sorted list of `M` records and compute index `N` at display time**.

Once `bob-plugins` has `[r_0, ..., r_{M-1}]` and index `i` in memory:
- `prev = r_{(i - 1 + M) % M}` and `next = r_{(i + 1) % M}` are trivial `O(1)` array reads.
- If `<` and `>` are *also* stored in Markdown on disk, you create **two independent sources of truth** that immediately disagree whenever you create, delete, rename, or retitle a record in Obsidian before `bob albums sync` finishes (or while offline on mobile, or while `bob_sync.lock` is held). Seeing `4 of 23` in the sheet while `]` jumps to the pre-sync neighbor is confusing and undermines trust.

### 3.2 Direct Reversal of the "Pure Record Note" Format (`2f80442b` / `cfc3177c`)
You literally just landed `bob records tidy` and H1-less record notes so that a record note without notes ends immediately after `---`, with zero boilerplate in the body (`docs/records.md`). Writing `[[eat/a|<]] · [[eat/c|>]]` at the top of every record body:
1. Forces every empty record note to carry machine-owned body Markdown again.
2. Collides visually with the Record Sheet in Live Preview and Reading view: `recordSheetAnchor` (`242k` line 716) places the Record Sheet right after `---` (or after an existing H1), so body line 1 renders **below** the Record Sheet as raw unstyled links unless `bob-ledger-tools` adds extra CodeMirror / DOM suppression decorations to hide the line it just wrote — at which point the Markdown line is pure overhead.
3. Requires updating `render_record_with_identity`, `apply_record_update`, `bob capture`, `bob records tidy`, and `bob records check` to preserve and lint a machine-owned nav region in every record note.

### 3.3 Write Amplification, Git Churn, and Open-Buffer Races
Unlike Period Notes, an album is a **mutable alphabetical ring**:
- Creating or deleting 1 record must lock, preimage-guard, modify, and commit **2 untouched neighbor files** (plus `<album>.md`).
- Editing a record's `title` across alphabetical neighbors must rewrite **up to 4 untouched neighbor files** (old prev, old next, new prev, new next).
- Every record addition pollutes the git blame/history of unrelated neighbor notes (`eat/yoshi.md` gets modified because `eat/yakiniku.md` was added).
- If `bob capture` (e.g., from Mac Capture) or the 3-second debounced `bob albums sync` rewrites `eat/prev.md` on disk while that file is open in an Obsidian tab, you risk editor reload flicker, cursor/undo disruption, or stale-file conflicts across synced devices (`vault-sync`).

### 3.4 Backlinks, Graph View, and Delete-Guard Pollution
Materializing `[[prev|<]] · [[next|>]]` in every record note body has unexpected side effects across Obsidian and Bob plugins:
- Every record note gains **2 spurious backlinks** from arbitrary alphabetical neighbors. Your Backlinks pane fills with unrelated items, and Obsidian's Graph View turns every album into an artificial closed loop.
- `bob-navigation-hotkeys`'s Delete Guard (`gatherDeleteCurrentFilePlanInput` in `670-plugin-project-files.js` + `countDeleteGuardBacklinks` in `671-delete-guard-model.js`) counts `metadataCache.resolvedLinks` toward a note's backlinks. Even if `<album>.md` already links to every record once synced, adding two more neighbor backlinks inflates incoming-link counts and makes unlinking/orphaning harder to reason about.

### 3.5 Bare `"<"` / `">"` Link Aliases Have UX & Footer Traps
- As noted in §2.1, `linksWalkerFooterLabel` (`124-links-walker-footer.js`) strips `[‹<>›]` from non-`prev`/non-`next` labels and returns `""`, so bare `[[eat/a|<]]` / `[[eat/c|>]]` would render blank footer arms (`‹  ·  ›`) until fixed.
- In raw Markdown (or when `M = 2`, where `<` and `>` point to the exact same note), bare `<` and `>` don't tell you *which* note you are about to open. Bob's Period Notes solved this gracefully with directional chevrons plus names (`‹ W44`, `W46 ›`).

### 3.6 What Materialized Links *Do* Have Going for Them (Honest Counter-Case)
To be fair, materialized Markdown links have two real advantages:
1. **Non-Obsidian environments**: Viewing a record file on GitHub web or editing in standalone Neovim shows clickable links (though `[n` / `]n` and rendered `N of M` do not exist outside Obsidian anyway, and `<album>.md`'s `[!records]` index already works on GitHub).
2. **Obsidian Mobile Reading View without new plugin rendering**: Today's `recordSheetGate` (`242i` line 111) skips mobile (`if (desktop !== true) return recordSheetFail("mobile")`). However, **this is straightforward to solve in `bob-ledger-tools` itself** (see §6.4), because `bob-ledger-tools` already runs on mobile (`isDesktopOnly: false`) and Obsidian's `vault` + `metadataCache` are completely local and synchronous on mobile.

---

## 4. Comparison of Architectural Options

| Dimension | Option A: Materialized Markdown (`bob-cli` writes `<`/`>` to every record; `bob-plugins` renders `N of M`) | Option B (Recommended): Virtual Computed Navigation (`bob-plugins` single source of truth; pure Markdown) | Option C: Hybrid (Virtual in Obsidian + Optional CLI Read/Check) |
| --- | --- | --- | --- |
| **Consistency between `<`/`>` and `N of M`** | Can drift whenever files change in Obsidian before sync | **Guaranteed 100% consistent** (computed from one sorted array) | **Guaranteed 100% consistent** in Obsidian |
| **Record note cleanliness (`2f80442b`)** | Broken — adds machine-owned line to every record body | **Preserved** — empty record notes stay frontmatter-only | **Preserved** |
| **Write amplification & git churn** | High — every create/delete/retitle rewrites 2–4 neighbor files | **Zero** — no record files written on neighbor changes | **Zero** |
| **Obsidian open-buffer race risk** | Real — background sync rewrites neighboring open tabs | **None** | **None** |
| **Backlinks / Graph / Delete Guard** | Polluted by 2 fake neighbor links per note | **Clean** — only real semantic links and `<album>.md` index | **Clean** |
| **`[n` / `]n`, `[[` / `]]`, `n` Walker Footer** | Works via existing body parser (after fixing blank `<`/`>` footer bug) | **Works seamlessly** across Reading, Live Preview, **and Source mode**; adds `N of M` in footer & enables `N]n` counts | Same as Option B |
| **Obsidian Mobile** | Raw Markdown links visible (no `N of M` unless plugin renders it) | **Works with lightweight read-only Record Nav header** via `metadataCache` (no `bob` binary needed) | Same as Option B |
| **GitHub web / standalone Vim** | Raw links clickable | No inline prev/next in raw `.md` (use `<album>.md` index) | Same as Option B; `bob records show` can print `N of M` & neighbors in terminal |
| **Implementation complexity** | High (8+ Rust modules + transaction guards + tidy + check + JS suppression + `N of M` JS) | **Low-to-medium** (contained in `bob-plugins` with clean unit/DOM tests) | Low-to-medium (+ tiny read-only `show.rs` enhancement) |

---

## 5. Justified Adjustments to Requirements

If we proceed with **Option B / C**, five small, well-justified refinements to the original specification make the result much cleaner:

1. **Compute `<` / `>` dynamically instead of materializing them into Markdown.**  
   You get the exact same `[n` / `]n` keyboard behavior, the exact same visual `<` / `>` links next to `N of M`, and zero stale-pointer bugs or multi-file write churn.
2. **Use `‹` and `›` visually (not raw `<` / `>`), and surface neighbor names on hover & in the `n` footer.**  
   Matches Bob's existing chevron idiom (`Body › Eat › restaurant`, `‹ W44`, `W46 ›`). Keep `N of M` compact inline (`‹  4 of 23  ›`) while showing `"Previous: <Title> ([n)"` / `"Next: <Title> (]n)"` in tooltips, Obsidian hover-preview popovers, and the `n` status-bar footer (`⇄ Links · 4 of 23 · ‹ Prev Title · Next Title ›`).
3. **Do not self-link when `M = 1`.**  
   When an album has only 1 record, render `1 of 1` with `‹` and `›` disabled/dimmed (`prev = null, next = null`), and show `"Only 1 record in <Album>"` on `[n` / `]n`. Start cycling cleanly at `M >= 2` (so an `M = 2` album points both `‹` and `›` at the other record, exactly as requested).
4. **Define "alphabetical" explicitly as flat, album-wide title order with natural case-/accent-insensitive collation.**  
   - **Scope:** All `M` direct `.md` members of `<album-stem>/` (not fragmented by `status` groups or `index_by` subgroups, so `M` matches `<album>.md`'s record count).
   - **Key:** Trimmed frontmatter `title` → first H1 → `humanizeStem(stem)`, tie-broken by exact `title`, then vault-relative `path`.
   - **Collation:** `Intl.Collator("en", { sensitivity: "base", numeric: true })` so `"Track 2"` precedes `"Track 10"` and `"Éclair"` sorts with `"E"` rather than after `"Z"` (note: `src/native/albums/grouping.rs::title_order` currently uses `.to_lowercase()`, which puts `"É"` after `"z"` and `"10"` before `"2"` — worth aligning in a small follow-up if exact index parity is desired).
5. **Render the controls on Mobile Obsidian via `metadataCache` (read-only), not just Desktop.**  
   Desktop keeps the full Record Sheet (with Properties hidden and `⊞ Edit`); Mobile keeps native Properties visible and mounts a minimal, read-only Record Nav strip using pure `vault` + `metadataCache`.

---

## 6. Recommended Design & Specification

### 6.1 Visual & Interaction Design (Intuitive, Reliable, Beautiful)

Where should `‹`, `N of M`, and `›` live inside the Record Sheet?

**Recommendation: Right-align a compact, accent-tinted segmented pager `[ ‹  4 of 23  › ]` on the Breadcrumb row (line 2 of the Record Sheet header).**

#### Why Line 2 (Breadcrumb Row) Beats Alternatives
- **Fixed vertical coordinate (zero mouse bounce):** Putting pagination below fields/ghosts/subscription strips makes the buttons jump up and down on every record depending on how many fields are filled. Anchoring `‹  4 of 23  ›` on line 2 keeps its Y-position identical across every record in the album so you can click `›` repeatedly without moving the cursor.
- **Survives sheet collapse:** When a record sheet is collapsed (`▸`), fields hide into the summary row, while line 2 stays visible — so pagination works in both expanded and collapsed states.
- **Preserves the Title hero row:** Line 1 (`.bob-record-sheet-title-row`) already holds the `1.8em` title plus `[⊞ Edit]` and `[▾]`. Adding pagination to line 1 would crush long titles on normal panes.
- **Clean visual restraint & `M = 2` grace:** Unlike spelling out `‹ Miso Ramen · 4 of 23 · Tsukemen ›` inline above the fields (which wraps poorly on 375px panes and awkwardly prints the same title twice when `M = 2`), a compact `‹  4 of 23  ›` pill handles `M = 1`, `M = 2`, long titles, and narrow splits effortlessly — while still exposing full neighbor titles via **Obsidian hover preview**, **tooltip**, and the **`n` Walker Footer**.

#### Layout Mockups

**Expanded Desktop Record Sheet:**
```text
┌─────────────────────────────────────────────────────────────────────────┐
│ Ramen Nagi                                                 [⊞ Edit] [▾] │
│ Body › Eat › restaurant                                 ‹  4 of 23  ›   │
├─────────────────────────────────────────────────────────────────────────┤
│ Status     💚 Liked                                                     │
│ Category   Ramen                                                        │
│ Location   Clark                                                        │
│                                                                         │
│ ＋ Notes   ＋ URL                                                       │
│                                                                         │
│ added Nov 8, 2026                                                       │
└─────────────────────────────────────────────────────────────────────────┘
```

**Collapsed Desktop Record Sheet:**
```text
┌─────────────────────────────────────────────────────────────────────────┐
│ Ramen Nagi                                                 [⊞ Edit] [▸] │
│ Body › Eat › restaurant · 💚 Liked · 3 fields           ‹  4 of 23  ›   │
└─────────────────────────────────────────────────────────────────────────┘
```

**Narrow Pane / Mobile (`≤ 375px`, Read-Only Mobile Strip or Wrapped Sheet):**
```text
┌────────────────────────────────────┐
│ Ramen Nagi                     [▸] │
│ Body › Eat › restaurant            │
│                      ‹  4 of 23  › │
└────────────────────────────────────┘
```
*(Or on Mobile without full Record Sheet, a sleek 1-line `.bob-record-nav-mobile` strip at the top of the body: `Body › Eat  ·  ‹  4 of 23  ›`.)*

**Single-Record Album (`M = 1`):**
```text
│ Body › Eat › restaurant                             ‹̶  1 of 1  ›̶       │
```
*(Muted `--text-faint` disabled arrows, tooltip: `"Only record in Eat"`.)*

**`n` Walker Footer in Status Bar (Desktop, when `n` family is active — including Source Mode!):**
```text
[[ s w n b ]]   ⇄ Links · 4 of 23 · ‹ Miso Ramen · Tsukemen ›
```
- The existing `.bob-freshness-context` slot (already part of `freshnessFooterEnsureDom` in `121-freshness-footer-paint.js`) holds `4 of 23`, shedding gracefully if the window narrows, while `.bob-freshness-link-prev` and `.bob-freshness-link-next` show the actual neighbor titles!

#### Visual Styling & Micro-Interactions (`styles.css` in `bob-ledger-tools`)
Follow the existing `.bob-record-sheet` token vocabulary (`--bob-record-accent`, `--text-muted`, `--background-modifier-hover`, `--radius-s`):
- **Container (`.bob-record-sheet-subrow`):** Flex row wrapping cleanly (`display: flex; flex-wrap: wrap; align-items: center; gap: 0.35em 0.75em;`) containing `.bob-record-sheet-nav` on the left and `.bob-record-sheet-pager` (`margin-inline-start: auto; flex: 0 0 auto;`) on the right.
- **Segmented Pager (`.bob-record-sheet-pager`):**
  - Subtle hairline pill (`border: 1px solid color-mix(in srgb, var(--bob-record-accent) 22%, var(--background-modifier-border)); border-radius: 999px; background: color-mix(in srgb, var(--background-primary) 75%, transparent); padding: 0.08em 0.25em;`).
  - **Arrows (`.bob-record-sheet-pager-btn`):** Real `<a class="internal-link bob-record-sheet-pager-btn">` elements (when enabled) with generous hit target (`min-width: 1.5em; text-align: center; text-decoration: none; border-radius: 999px;`), hover tint (`color-mix(in srgb, var(--bob-record-accent) 14%, transparent)`), `focus-visible` accent ring (`2px solid var(--interactive-accent)`), native Obsidian `hover-link` preview popover on hover (`recordSheetBindHover`), `Cmd/Ctrl+Click` for new tab, `Cmd/Ctrl+Shift+Click` for split, and `title` tooltip:
    - Prev: `"Previous: Miso Ramen ([n)"` (or `"Previous (wraps): Zebra ([n)"` when `N === 1`)
    - Next: `"Next: Tsukemen (]n)"` (or `"Next (wraps): Aardvark (]n)"` when `N === M`)
  - **Counter (`.bob-record-sheet-pager-pos`):**
    - Uses **`font-variant-numeric: tabular-nums`** so `4 of 23` → `10 of 23` never causes horizontal width jitter!
    - Color `var(--text-muted)`, `font-size: var(--font-ui-smaller, 0.85em)`, non-selectable (`user-select: none`), `aria-label="Record 4 of 23 in Eat"`.
    - Optional polish: making `4 of 23` a clickable jump to the parent album (`eat.md`) or keeping it quiet text (since `Eat` is already clickable right next to it in the breadcrumb — keeping `4 of 23` quiet text avoids redundant links and visual noise).
- **Respect `prefers-reduced-motion: reduce`:** No transform/bounce animations when reduced motion is enabled.

---

### 6.2 Shared Resolver & Data Architecture (`api.recordNav` v1)

To guarantee the Record Sheet, `[n` / `]n`, `[[` / `]]`, and the `n` Walker Footer **never disagree** (mirroring `api.bankWalk` and `api.laneWalk` in `bob-plugins/docs/develop/plugin-apis.md`), put **one pure, synchronous resolver** in `bob-ledger-tools` and expose it on `bob-ledger-tools.api.recordNav` (version `1`):

#### Resolution Algorithm (`resolveRecordNav(path, context)`)
1. **Structural gate on target `path`:**
   - Normalize `filePath = recordSheetPath(path)`. Must be `<albumStem>/<file>.md` (exactly one `/`, immediate Markdown child of a vault-root folder).
   - Look up `<albumStem>.md` in `vault.getAbstractFileByPath` and read its `metadataCache` frontmatter: `albumTypeNames(fm?.type).includes("album")` (and optionally confirm via cached `albumReport` when present on desktop).
   - Check the active file's own `metadataCache` frontmatter:
     - Does `type` match `"record"` OR the album's `record.noun` (supporting both canonical `[[record]]` and legacy noun-typed records for keyboard navigation, while Record Sheet mounting stays gated by `recordSheetGate`)?
     - Does `parent` resolve to `<albumStem>.md` (or fall back via `albumResolveSchemaTargetForFile`)?
     - If not a qualifying record note, return `{ ok: false, reason: "not-record" }` so non-record notes fall straight through to `findFirstRenderedLink`.
2. **Collect album members (`M`):**
   - Scan `vault.getMarkdownFiles()` for all direct children of `${albumStem}/` (i.e., `file.path.startsWith(albumStem + "/")` and `!file.path.slice(albumStem.length + 1).includes("/")`).
   - *(Note: Counting all immediate `.md` children of `<albumStem>/` matches `src/native/records/catalog.rs` and `src/native/albums/index.rs` so `M` always equals `eat.md`'s record count.)*
   - For each member, extract display title:
     1. Trimmed `frontmatter.title` (if non-empty string/scalar)
     2. Else first level-1 heading from `cache.headings`
     3. Else `humanizeStem(file.basename)` (`_` / `-` → spaces, title-cased — matching `GroupingRecord::from_indexed`)
3. **Deterministic alphabetical sort:**
   - Sort with a cached `Intl.Collator("en", { sensitivity: "base", numeric: true })`:
     1. `collator.compare(a.title, b.title)`
     2. Tie-break: `a.title < b.title ? -1 : a.title > b.title ? 1 : 0`
     3. Tie-break: `a.path < b.path ? -1 : a.path > b.path ? 1 : 0`
4. **Compute position & neighbors:**
   - Find `idx` matching `filePath`. `total = members.length`, `index = idx + 1` (`1`-based).
   - If `total <= 1`: `prev = null`, `next = null`.
   - If `total >= 2`:
     - `prev = members[(idx - 1 + total) % total]` (`wraps: idx === 0`)
     - `next = members[(idx + 1) % total]` (`wraps: idx === total - 1`)
   - Return frozen descriptor:
     ```js
     {
       ok: true,
       album: { path: albumPath, stem: albumStem, title: albumTitle },
       index, // 1-based N
       total, // M
       positionText: `${index} of ${total}`,
       prev: prev ? { path: prev.path, title: prev.title, wraps: idx === 0 } : null,
       next: next ? { path: next.path, title: next.title, wraps: idx === total - 1 } : null,
     }
     ```

#### Caching, Performance & Live Invalidation
- Keep a per-album memo (`Map<albumStem, { generation, items }>`) invalidated synchronously whenever:
  - `vault` emits `create`, `delete`, or `rename` where either `file.path` or `oldPath` is a direct child of an album folder or root `<album>.md`; or
  - `metadataCache` emits `changed` for any file inside an album folder or root `<album>.md`.
- **Crucial fix for `242k-plugin-record-sheet.js`:** Today `recordSheetOnMetadata(file)` refreshes sheets on `recordSheetOwnsPath(path)` (metadata changes), **but does not react to `vault` `delete` or `rename` events** except after the async `bob albums list` round-trip! Hook `vault` `create` / `delete` / `rename` + sibling `metadataCache` `changed` directly into `scheduleRecordSheetRefresh()` AND `linksWalkerFooterRequest()` so adding, deleting, or renaming a sibling updates `4 of 23` and `‹` / `›` in **one tick** with zero subprocess latency.
- **Crucial `WidgetType` cache key fix in `242i-plugin-record-sheet-model.js`:** Add `nav: model.nav` to `recordSheetSignature(model)` so CodeMirror 6 widgets repaint whenever `N`, `M`, `prev`, or `next` changes.

---

### 6.3 Integration with `[n` / `]n` and the `n` Walker Footer

1. **In `bob-navigation-hotkeys` (`670-plugin-project-files.js` & `482-walk-mode-nav-api.js`)**:
   - Extract a shared helper `resolveDirectionalNoteLink(plugin, path, content, direction, step = 1)`:
     - Query `app.plugins.plugins["bob-ledger-tools"]?.api?.recordNav` (version `>= 1`).
     - *(Optional resilience: include a tiny shared fallback using `metadataCache` + `vault` so `[n`/`]n` still works on record notes even if `bob-ledger-tools` is temporarily disabled.)*
     - If `nav.ok === true`:
       - On `total <= 1`: return `{ kind: "single-record", albumTitle: nav.album.title }` (so `openLabeledBodyLink` shows Notice `"Only 1 record in <Album>"` instead of `"No next link found"`, and `walkMode.links` reports `prev: null, next: null` with `position`).
       - Otherwise return the resolved target (`{ target: target.path, renderedText: direction === "prev" ? `‹ ${target.title}` : `${target.title} ›`, path: target.path, position: nav }`).
     - If not a record note (`nav.ok === false`): fall back unchanged to `findFirstRenderedLink(content, label)` (preserving daily notes, period notes, and general Markdown links!).
   - **Why record-walk precedence matters:** Checking `recordNav` *before* `findFirstRenderedLink` on canonical record notes guarantees that an authored link in `## Notes` whose alias happens to end in `>` (e.g., `[[other|A > B]]`) can never hijack `]n`.
   - **Bonus capability (`N]n` / `N[n` / `N]]` / `N[[`):** In `546-plugin-bracket-repeat.js` and `openLabeledBodyLink`, Vim counts (`3]n`, `3]]`) currently get ignored for `n`. When `nav.ok === true`, stepping `((idx + sign * count) % total + total) % total` lets `5]n` skip 5 records in `O(1)`.
   - **Jump history (`<C-o>`)**: `openLabeledBodyLink` → `openOrCreateLinkCandidate` already calls `captureActiveFilePosition()`. Also wire `recordSheetOpenPath` (`242k` line 346) to call `navApi.recordJump?.(...)` or `captureActiveFilePosition()` (matching how `241q` album-group jumps already record `<C-o>` history).

2. **In `bob-ledger-tools` (`124-links-walker-footer.js`)**:
   - Update `walkMode.links({ path, content })` (additive `version: 7` on `api.walkMode` or additive `position` property) to return:
     ```js
     {
       ok: true,
       prev: ...,
       next: ...,
       position: { index, total, text: `${index} of ${total}`, albumTitle }, // present on record notes
     }
     ```
   - In `linksWalkerFooterView(preview)`:
     - Populate `contextText: preview.position ? preview.position.text : ""` (so the bar shows `⇄ Links · 4 of 23 · ‹ Miso Ramen · Tsukemen ›`, or `⇄ Links · 1 of 1 · only record in Eat` when `M = 1`).
     - Include `view.contextText` in `linksWalkerFooterPaint`'s `paintKey` (line 253) so a change from `4 of 23` to `4 of 24` triggers a repaint!
     - **Fix the bare-chevron bug in `linksWalkerFooterLabel` (lines 7–12):**
       ```js
       if (text !== "prev" && text !== "next") {
         const stripped = text.replace(/^[‹<>›]\s*/, "").replace(/\s*[‹<>›]$/, "").trim();
         if (stripped) return stripped;
       }
       ```
       This ensures even hand-authored `[[note|<]]` / `[[note|>]]` links anywhere in the vault fall back cleanly to the target stem instead of rendering empty buttons.

---

### 6.4 Mobile Obsidian Strategy (`isDesktopOnly: false`)

Because `recordSheetGate` (`242i` line 111) currently exits on mobile (`if (desktop !== true) return recordSheetFail("mobile")`), Desktop-only rendering would leave Mobile Obsidian without `‹  N of M  ›`.

Recommended fix (zero `bob` subprocesses needed):
- Allow a lightweight **read-only Record Nav mode** on mobile (either mounting a compact `.bob-record-nav-mobile` card at the top of Reading view / Live Preview with breadcrumb + `‹  4 of 23  ›`, OR letting `recordSheetModel` mount a read-only header-only view on mobile with `hideEligible: false` and `editable: false` so native Properties stay intact).
- Both `vault.getMarkdownFiles()` and `metadataCache.getFileCache()` work identically on iOS/Android Obsidian, so mobile shows accurate live `‹  4 of 23  ›` navigation without touching `bob` CLI or note bytes.

---

### 6.5 Optional `bob-cli` Enhancements (Read-Only & Parity)

`bob-cli` requires **zero mandatory changes** for this feature to ship cleanly in `bob-plugins`. Two small optional enhancements are worth considering afterward:
1. **Terminal parity in `bob records show TYPE STEM` (`src/native/records/show.rs`):** Show `#4 of 23` (and optional `‹ Prev · Next ›` hint) in the human terminal card, computed read-only from `FolderIndex`.
2. **Collation parity in `src/native/albums/grouping.rs::title_order` (line 404):** Consider aligning Rust's `title_order` with accent-folded natural order (using `unicode_normalization` NFKD — already imported in `src/native/records/stem.rs`! — plus numeric run comparison) so `[!records]` index sorting and the album walk handle accents (`Éclair`) and numbers (`2` vs `10`) identically.

---

### 6.6 Appendix: If You Still Wanted On-Disk Materialization (Option A Blueprint)

If after weighing the critique you decide you **must** have literal wikilinks in `.md` files (e.g., for external GitHub/Vim browsing), here is the safest way to minimize breakage:
1. **Canonical line format:** First body line after `---`:  
   `[[<album>/<prev_stem>|‹ <Prev Title>]] · [[<album>/<next_stem>|<Next Title> ›]]`  
   *(Never bare `<` / `>`, and never store `N of M` in Markdown.)*
2. **Rust (`bob-cli`) changes required:**
   - Shared `album_neighbors` planner from `FolderIndex` (`src/native/albums/`).
   - `render_record_with_identity` & `apply_record_update` (`src/native/records/render.rs`) to emit/preserve line 1.
   - `bob capture` (`src/native/capture/record_note.rs`), `bob records new|update`, and `bob albums sync` (`src/native/albums/sync.rs`) to stage, preimage-guard, and rewrite 2–4 neighbor record files in the same transaction.
   - `src/native/records/notes_section.rs` & `bob records tidy` (`src/native/records/tidy.rs`) updated so tidy preserves/repairs the nav line rather than treating the body as non-empty or stripping around it.
   - `bob records check` (`src/native/records/check.rs`) to validate stale/missing nav lines.
3. **Plugin (`bob-plugins`) changes still required:**
   - Fix `linksWalkerFooterLabel` empty-strip bug (`124-links-walker-footer.js`).
   - Suppress/hide the raw body nav line in Live Preview and Reading view so it doesn't duplicate beneath the Record Sheet.
   - **Still compute the full sorted album list in JS** to render `N of M` inside the Record Sheet.

Seeing those two architectures side-by-side makes the conclusion sharp: Option A builds ~2× the machinery across both Rust and JS while fighting `bob`'s own pure-record-note direction — whereas **Option B delivers the complete, drift-free UX in one place**.

---

## 7. Implementation Roadmap & Verification Plan

### Phase 1 — Shared Resolver & `api.recordNav` v1 (`bob-ledger-tools`)
- Add `record-nav` model fragment (`resolveAlbumRecordNav`, natural `Intl.Collator("en", { sensitivity: "base", numeric: true })`, per-album cache invalidated on `vault` `create`/`delete`/`rename` and `metadataCache` `changed`).
- Expose `api.recordNav` (`version: 1`, `neighbors(path)`) on `bob-ledger-tools.api` and document it in `docs/develop/plugin-apis.md`.
- **Verify:** Unit tests covering `M = 0, 1, 2, 3+`, wrap boundaries (`1 of M` / `M of M`), accent/numeric collation, missing-title fallback, tie-breaking, non-record exclusion, and nested subfolder exclusion.

### Phase 2 — Record Sheet Pager + Mobile Read-Only Nav (`bob-ledger-tools`)
- Extend `recordSheetModel` (`242i`), `recordSheetBuildEl` (`242j`), `BobLedgerToolsRecordSheetMixin` (`242k`), and `styles.css` with `.bob-record-sheet-pager` (`‹  N of M  ›`), `tabular-nums`, hover previews, tooltips, `M = 1` disabled state, `recordSheetSignature` update, and sibling `vault` event listeners.
- Add read-only mobile fallback rendering the nav strip cleanly on iOS/Android without hiding Properties.
- **Verify:** Extend `scripts/test-ledger-tools-record-sheet.cjs` (expanded/collapsed/375px/M=1/M=2/hover/click/modifier-click/focus-preservation/DOM-cleanup) + `npm run build:check` + `npm test`.

### Phase 3 — `[n` / `]n`, `[[` / `]]`, and `n` Walker Footer (`bob-navigation-hotkeys` + `bob-ledger-tools`)
- Wire `openLabeledBodyLink` (`670`) and `walkMode.links` (`482`) to consult `recordNav` on record notes before `findFirstRenderedLink`.
- Update `124-links-walker-footer.js` to display `N of M` in `contextText` (included in `paintKey`), refresh on sibling changes, and fix the `linksWalkerFooterLabel` empty-strip bug.
- Optionally add `N]n` / `N[n` count stepping on record rings and `<C-o>` jump recording on sheet clicks.
- **Verify:** Extend `scripts/test-navigation-period-links.cjs`, `scripts/test-navigation-bracket-repeat.cjs`, and walker footer tests; run `npm run validate` and deploy via `bob plugins sync`.
