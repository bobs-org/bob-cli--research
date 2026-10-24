# Pomodoro themes: catalog, suggestions, hide, rename, and color

Researcher: cld · 2026-10-24 · scope: bob-cli, bob-plugins, bob-mac-capture, chezmoi
(mac pom / tmux), Bob vault data

## TL;DR

The idea is good, and it is overdue: the vault already treats Pomodoro names as
semi-structured data (the plan budget counts their `+` components as **themes**, Stats has a
`theme` dimension). But nothing treats a theme as a durable entity with history. In the real
vault, 81 distinct themes appeared in the ~two months since named Pomodoros began
(2026-08-26). 40 of them were used on only one day, and the list has obvious near-duplicates:
FIX/FIXES, TOOL/TOOLS, SCREENSHOT/SCREENSHOTS, SASE V18/SASE V19. Suggesting past themes and
being able to rename them would improve consistency and Stats quality directly.

I recommend building it, with six requirement adjustments (§3):

1. **A theme is one `+` component, not a whole name.** `BOB + DECKS` has two themes.
   Suggest, rename, hide, and color components. This is the definition `docs/plan.md`
   already uses.
2. **Disable → "Hide from suggestions."** A hidden theme leaves *history* suggestions only.
   It never affects today's real entries, history, Stats, colors, or your ability to type it.
   An exact-match query still shows it, dimmed, with ⌃D to unhide.
3. **Colors are stable per name, but they are not distinct.** On Bryan's real data, a pure
   name hash puts two same-day themes in the same color on **49–62 % of days**, whether the
   palette has 8, 12, 16 slots, or is a continuous hue wheel. So color must never carry
   meaning on its own. It always sits next to the name text. A per-theme **pin** fixes the
   collisions that recur: two pins remove both collisions that recur among the top themes.
   Exempt themes (GTD) render muted.
4. **Reuse the validated 8-slot area palette, but give themes a different *form*.** Themes get
   a tinted rounded pill with ink-colored text; areas keep the ● dot. Never paint theme text in
   the hue: three of the eight slots fall below 3:1 contrast on light surfaces.
5. **Hide/pin state lives in a union-merged vault journal** (`.bob/themes/<host>.jsonl`). It
   does not go in `~/.config/bob/config.yml`, which is chezmoi-managed and per host. The
   precedent is the Stats review journal.
6. **Global rename is a bob-owned vault transaction** modeled on `bob ref rename`: lock,
   pre-sync, snapshot, atomic writes, verify, one revertable scoped commit, post-sync. Obsidian
   and the Mac only preview it and invoke it.

The recommended solution, with a phased rollout, is in §8.

---

## 1. What exists today

### 1.1 Vocabulary already in the code

- **Pomodoro name** is the text after ` — ` on a column-0 `## Pomodoros` entry
  (`glossary:pomodoro`). It is canonical ALL-CAPS. `canonicalize_pomodoro_name`
  (`src/native/capture_pomodoros.rs:492`) collapses whitespace and ASCII-uppercases. The
  charset is letters, digits, spaces, and `& ' ( ) + , . / -`
  (`src/native/capture_pomodoro_name.rs` `name_arg`).
- **Theme**, per `docs/plan.md` §Names/§Themes, is one `+` component of a name
  (`split_components`, `src/native/plan_budget/mod.rs:514`). Components compare by
  `normalize_component`: collapsed whitespace, lowercased (`:245`). `plan.max_themes` counts
  distinct non-exempt components across open entries. `plan.exempt` (default `[GTD]`) and
  `plan.inventory_labels` (LATER, MISC, NEW FEATURES) qualify them. The budget also counts a
  pseudo-theme `(unnamed)` (`UNNAMED_THEME`).
- **Selector slug** is `selector_slug` (`src/native/capture_language/line.rs:346`): lowercase
  words joined by `-`. This is what `=deep-work` matches.
- **Glossary inconsistency:** `glossary:mac-menu-bar-pomodoro-indicator` says "THEME is the
  Pomodoro's ` — NAME`", which uses *theme* for the whole name. The new glossary term should
  settle this (§4.1).

### 1.2 Completion menus that show Pomodoro names (all today-only)

| Surface | Where | Source of candidates |
| --- | --- | --- |
| `=NAME` start (`pomodoro_start_name`) | `src/native/capture_complete/pomodoros.rs` `pomodoro_start_name_candidates_from_scan_with_hint` | today's note only: open placeholders, create row, "again" (completed today), name-it, running |
| `@r:id#NAME`, `@r^id+#NAME`, `@r+id#NAME` (`pomodoro_name`) | same file, `pomodoro_name_candidates_from_scan_with_hint` | today's open entries + create row |
| zsh `bob capture` completion | `capture_complete/shell.rs` | same engine |
| Bob Mac Capture inline list | `CapturePanelView.swift` `CompletionList`/`CompletionRow` (2325–2563); rows from `CompletionRowContent.swift:382–509` | bob's order verbatim, re-queried per keystroke |
| Mac "Name it" prompt | `submitPomodoroNamePrompt` (`CapturePanelModel.swift:6371`) → `bob capture-pomodoro-name` | free text, no suggestions |
| Obsidian Link-to-today picker (Ctrl+Shift+Enter) | `block-id-prompt` `085-pomodoro-link-picker-modal.js`, model `075-pomodoro-link-targets.js` | JS parse of today's note |
| Obsidian move-bullets / move-merge-rename pickers (`N<C-S-m>`) | nav `200-filtered-picker-modals.js:626,701`, rows `160-pomodoro-reorder.js:260–389` | JS parse of today's note |
| Successor picker (`→ NAME`) | nav `206-successor-picker-modal.js` | today's entries |

Today's ranking is `support::rank`: prefix matches, then substring matches, each in source
order. The create row is inserted after the prefix matches and before the substring matches
(`insert_pomodoro_creation_candidate`). `named_creation_name`
(`capture_pomodoros.rs:771`) already refuses to offer creation when an open exact or
**prefix** match would win. That matters for history rows (§5.2).

### 1.3 Other places a name is shown (candidates for color)

- **Obsidian:** Pomodoro entry lines (Live Preview and Reading view). The home chip
  `● bob · dev` sits at the line end (`142-pomodoro-home-chips.js`,
  `273-plugin-pomodoro-home-chips.js`). Also: the `bob-plan` block theme line `★ A · B`
  (`340-dashboard-views-and-plan-block.js:952`), the Today-mark tooltip, picker rows, the
  successor rows, notices, and the Stats **Themes** panel, which currently paints every bar in
  the metric hue (`239-plugin-stats-panel-render.js:185–220`).
- **Mac:**
  - The idle agenda: headers, Later strip, and one-row summary.
  - The Themes/Links capsules and the `+1 BOB` delta chip.
  - Destination rows `→ GOALS · next up`.
  - The block headline, close, adjust, shift, and start cards.
  - Picker badges `Now · NAME`, and the Refs Today card.
  - Editor span highlighting: `pomodoro_name` spans map to `.section` purple
    (`CompletionRowContent.swift:56`). `CaptureSpan` already has an additive `field` slot that
    a per-span hue could copy.
- **CLI:** `bob plan`, `bob pomodoro` (status and `tmux`), `bob capture` destination lines,
  and the `bob stats` theme dimension. Only `note` and `theme` fold to top-N plus other
  (`docs/stats.md:367`).
- **Hammerspoon mac pom:** `THEME (50m) · 🍅 12:34`
  (`chezmoi home/dot_hammerspoon/pomodoro_countdown.lua`).

### 1.4 Color machinery already validated

- **Area hues (`docs/pomodoro-homes.md` R8):** 8 fixed slots blue, orange, aqua, yellow,
  magenta, green, violet, red. Each has light and dark hex values and an xterm-256 code.
  - The fallback is `palette[fnv1a32(lowercase stem) % 8]`, and a top-level area's `color:`
    overrides it.
  - The `area_hue_collision` lint suggests a pin when two areas share a slot.
  - Twins exist in Rust (`src/native/pomodoro_homes/palette.rs`), JS (`142-pomodoro-home-chips.js`
    with `--bob-area-*` CSS variables), and Swift (`PomodoroHomes.swift:250–338`,
    `PomodoroHomeColor.swift`). Conformance vectors live in
    `tests/fixtures/pomodoro_homes/vectors.json`.
- **Validator result:** I ran the dataviz validator on these 8 hexes. In light mode they pass
  the lightness band, the chroma floor, adjacent-pair CVD separation (worst ΔE 9.1), and the
  normal-vision floor (worst ΔE 19.6). The contrast check WARNs: aqua 2.74:1, yellow 2.11:1,
  and magenta 2.62:1 against the light surface. So these hues are fine as **fills and marks**
  but not as **text color**.

### 1.5 Where state could live

- **`~/.config/bob/config.yml` is chezmoi-managed** (`chezmoi home/dot_config/bob/config.yml`)
  and per host. If the Mac app wrote a hide there, chezmoi would report drift and the hide
  would not propagate.
- **The vault already carries synced machine-written state:**
  - `.bob/stats/review/YYYY-MM.<host>.jsonl` is append-only per host. It is re-included by
    `!/.bob/stats/**/*.jsonl` and union-merged by `.gitattributes`
    (`docs/vault-git-sync.md` §Stats review journal).
  - The JS plugins already write it, so it is a proven two-runtime, multi-host pattern.

### 1.6 Vault-wide rewrite precedent

`bob ref rename` (`docs/ref.md:581`) is the template for a rename:

- It is live by default, with `-d` for a dry run.
- It takes `bob_sync.lock`, runs a pre-sync, and replans.
- It snapshots before-images, writes atomically, verifies, and restores on failure.
- It makes one scoped commit with the subject `bob ref rename: <old> → <new>`, then runs a
  post-sync.
- Refusals are typed codes. Rollback is `git revert` of that one commit.

Nothing renames Pomodoro names across days today. Nav's `planPomodoroEntryRename` renames one
entry in place.

## 2. Evidence from the vault

A read-only scan of `~/bob/YYYY/YYYYMMDD.md` (1 169 daily notes, 384 with a `## Pomodoros`
section) found:

| Metric | Value |
| --- | --- |
| Pomodoro entries / named | 1 266 / 597 (named Pomodoros start 2026-08-26) |
| Composite (`A + B`) names | 10 (rare) |
| Distinct themes (component keys) | 81 |
| Themes used on exactly one day | 40 (49 %) |
| Themes last used since 2026-09-01 | 76 |
| Days with ≥ 2 themes | 60; themes/day mostly 2–7 (one day with 21) |
| Non-ALL-CAPS spellings in the vault | 0 (canonicalization works) |

Top themes, with the number of days used: GTD 51, BOB 26, BLOG 14, SASE 14, SHIT 13, READ 9,
MEMORY 8, JOB 7, REMOTE 6, GOALS 6, SASE V18 6, HACK 6, PYPI 6.

Near-duplicate clusters that suggestions and rename would have prevented or fixed:
FIX/FIXES, TOOL/TOOLS, SCREENSHOT/SCREENSHOTS, SASE V18/SASE V19, and MEMORY / MEMORY WEBS /
PLAN MEMORY / AUDIT MEMORY / MEMORY BEADS.

**Color collisions, measured.** I counted the days on which two of that day's non-GTD themes
land in the same color:

| Assignment | Days with a collision |
| --- | --- |
| FNV-1a % 8 (the existing area hash) | 27/55 (49 %); 60 % with GTD included |
| % 10 / % 12 / % 16 slots | 27 % / 45 % / 33 % (noise; no fix) |
| Continuous hash hue, min gap < 20° / < 30° | 47 % / 62 % |
| 8 slots, top 8 / top 16 themes pinned by greedy co-occurrence | 33 % / 27 % |

This is the birthday problem. Pins only help frequent pairs, because half of all themes are
one-offs. Out of the box, the two recurring collisions are **BOB/JOB (both magenta, together
on 6 days)** and **SASE/BLOG (both orange, 6 days)**. Pinning **JOB → aqua** (which also
matches the `job` area's pinned hue) and **BLOG → red** removes both. After those two pins, no
pair collides on more than two days.

## 3. Critique and requirement adjustments

> **Verdict:** a good idea. Names are already the backbone of the plan budget and the Stats
> `theme` dimension, and the data shows real drift. The risk is not the feature itself. The
> risks are the three hidden traps below: name vs. theme, "disable" semantics, and the
> promise that colors are distinct. Each adjustment is labeled **ADJ-n**.

- **ADJ-1: a theme is a name component.** Rename, hide, color, and suggestions operate on
  `+` components (the `normalize_component` key), not on whole names. Renaming FIXES → FIX
  turns `BOB + FIXES` into `BOB + FIX`. This keeps one meaning with `plan.max_themes` and Stats.
  Whole composite names are not catalog entries.

- **ADJ-2: "disable" becomes "hide from suggestions."** Hiding never:
  - removes or affects today's ledger rows (a real open entry must stay targetable);
  - rewrites history, Stats, or colors;
  - blocks typing the name. `=fixes` still works.

  An exact-match query for a hidden theme shows one dimmed row, `FIXES · hidden`, with
  `⌃D unhide`. Using a hidden theme does **not** silently unhide it, which matches the vault's
  "nothing changes state behind your back" decisions. This is the browser-history mental
  model (Chrome's Shift+Delete removes one history suggestion), with one difference: here the
  hide survives sync, because it lives in the vault journal.

- **ADJ-3: colors are stable and learnable, not guaranteed distinct.** The requirement
  "distinct" and "deterministic from the name" conflict on about half of real days (§2).
  - Keep the name hash as the default.
  - Add an explicit per-theme **pin**.
  - Mute exempt themes (GTD), matching "exempt rows are dimmed" in `bob plan`.
  - Ship a collision report that suggests pins.
  - Never let color be the only carrier: the name text is always beside it.

- **ADJ-4: colors follow form rules.**
  - Reuse the validated 8 slots; no new palette to validate in three runtimes.
  - Draw a theme as a **tinted rounded pill with ink text** (or an ■ rounded-square swatch in
    dense rows). An area stays a **● dot**.
  - Never color the theme text itself.
  - While you type an unknown name, keep the neutral span color. Otherwise every keystroke
    re-hashes to a new hue and the text flickers through colors.

- **ADJ-5: hide and pin state live in a vault journal** that syncs to every host. Not in
  config.yml.

- **ADJ-6: the create row moves below history prefix matches**, and today's rows rank above
  everything. One existing behavior changes: today's *substring* matches now rank above the
  create row (§5.2). The rule "known names before new names" is what label pickers in Linear
  and GitHub do, and it extends bob's existing create-placement rule.

- **Added requirement (small): a near-duplicate heads-up.**
  - What it does: a create row whose name is within edit distance 2 of a visible catalog
    theme, or is its plural/singular, gets a `like FIX` badge.
  - Why it is in scope: the vault data shows this is where the drift comes from.
  - Precedent: `select_named` already computes a Levenshtein suggestion over open entries.

- **Out of scope for v1:**
  - theme descriptions or notes;
  - per-theme Obsidian notes;
  - completing the next component after `+` (`=bob+de|`). That is a nice v2.

## 4. Vocabulary and memory

### 4.1 Proposed glossary strand (`glossary:pomodoro-theme`)

> **Pomodoro Theme** — aka theme
>
> One `+`-separated component of a [[pomodoro]]'s name. `— BOB + DECKS` has the themes BOB
> and DECKS; `— GTD` has one.
>
> - **Comparison and display.** Themes compare case-insensitively after collapsing
>   whitespace, which is the plan budget's component key. They display ALL-CAPS.
> - **One meaning everywhere.** A theme is what `plan.max_themes` counts (except `plan.exempt`
>   names such as GTD, which are review themes), what the Stats `theme` dimension reports, and
>   what `bob theme` lists, renames, hides, and colors.
> - **The theme catalog** is every theme on any daily note's `## Pomodoros` entry, open or
>   closed, plus the hide and color state in `.bob/themes/*.jsonl`.
> - **Hiding** a theme only removes it from history suggestions. Today's entries, history,
>   Stats, and typing the name are unaffected.
> - **Color.** A theme's color is one of the eight Pomodoro-home hue slots: a pin, else muted
>   for exempt themes, else `fnv1a32(key) % 8`. It is drawn as a tinted pill, never as text
>   color.
> - **What it is not.** It is not a Pomodoro home (derived from Task Links and drawn as a ●
>   dot) and not an Obsidian appearance theme. The budget's `(unnamed)` is a placeholder, not
>   a catalog theme.

Also update `glossary:pomodoro`, which should link [[pomodoro-theme]], and the mac-pom strand,
which should say "NAME" where it says "THEME". Both edits go through `/sase_memory_write`.

### 4.2 Proposed decision records

Draft these for Bryan to accept:

1. `pomodoro-themes-are-name-components`
2. `hidden-themes-leave-suggestions-only`
3. `theme-colors-are-hashed-slots-with-pins`
4. `theme-state-is-a-union-merged-vault-journal`

Each record's "rejected alternatives" can come straight from §7.

Naming hazard: in CSS and code, *theme* collides with `.theme-dark` and Obsidian themes. Use
`pomodoro_theme` in Rust/JSON and `bob-pomo-theme*` classes and variables in CSS.

## 5. Design

### 5.1 The theme catalog (bob-cli owns it)

**Module.** A new `src/native/pomodoro_themes/` module with a contract page
`docs/pomodoro-themes.md` (rules T1…Tn), shaped like `docs/pomodoro-homes.md`. It ships
conformance vectors in `tests/fixtures/pomodoro_themes/vectors.json`, which the JS mirror
runs too.

**Scan.**
- Read every canonical daily note `YYYY/YYYYMMDD.md` and its `## Pomodoros` entries, all
  states. Fenced code is skipped, as in the ledger rules.
- Per theme key, record:
  - the display name (from the most recent spelling);
  - `first_day`, `last_day`, `days_used`, `entries`;
  - optionally `minutes` (from timespans).
- Exclude `_templates/`, `done/`, and `_conflicts/`.

**Cache.**
- Location: `bob_cli_cache_dir()/themes/catalog-v1.json`, keyed per daily path by
  `(mtime_ns, size)`.
- Today's note is always re-read.
- Measured on apollo: `stat` of all daily notes takes ~17 ms and a full read takes ~88 ms (in
  Python). A warm Rust pass is dominated by `readdir` + `stat`, so a per-keystroke
  `capture-complete` stays cheap.
- Re-measure on the Mac before shipping. The thin-client decision reopens if spawn latency
  breaks the live preview.

**State fold.**
- Union every `.bob/themes/*.jsonl` (§5.3), sort by `(ts, host, line)`, and apply events
  last-writer-wins per key.
- Result per theme: `hidden: bool`, `pin: Option<Hue>`.

**Hue resolution (T-hue).**
1. A pin wins.
2. Otherwise, a key in `plan.exempt` renders **muted** (`hue: null`, `hue_source: "exempt"`).
3. Otherwise, `Hue::ALL[fnv1a32(key) % 8]`, reusing `palette::fallback_hue`.

Inventory labels keep their hash hue. Optionally they could render as an outlined pill in v2.

**Shared JSON object** (additive; no schema-version bumps):

```json
"themes": [
  { "key": "bob", "name": "BOB", "hue": "magenta", "hue_source": "hash", "hidden": false }
]
```

It is emitted on:
- `capture-pomodoros` entries and the agenda;
- `bob plan` entries (next to `components`);
- completion candidates;
- `capture-parse` `pomodoro_name` spans, with component offsets, only when the name resolves
  to a *known* theme;
- `bob pomodoro` JSON, if or when one exists;
- Stats theme parts (`parts_hue.theme`).

Swift and Lua consume `hue` from bob. Only the JS mirror computes it itself.

### 5.2 Suggestions in completion menus

**Order** for `pomodoro_start_name` and `pomodoro_name`, top to bottom:

1. **Today**: every matching row of today's ledger, in today's existing internal order (start
   or open, again, name-it, running). The user's rule: existing names always come first.
2. **Recent themes, prefix matches**: ranked by `last_day` descending, then `days_used`
   descending, then name. "Most recently used first" is explainable on the row
   (`yesterday · 26 days`).
3. **Create row**: shown only if the query is non-empty, creatable (`named_creation_name`), and
   no today row or history row matches it *exactly*. An exact history match *is* the create
   row: it carries `creates_pomodoro`, `plan_themes_after`, and `plan_themes_cap`, like
   today's "again" rows.
4. **Recent themes, substring matches.**

**Caps.** At most 5 history rows on an empty query. With a query, at most 20. No dormancy
rule: recency ordering already buries old one-offs.

**Correctness guards** (this is where "reliable" is won or lost):

- **Prefix shadowing.** `=bob` selects an open `BOBCAT` by prefix, so a history row `BOB`
  would lie if it said "new session". Resolve every history row through the same
  `select_named` / `named_creation_name` logic as capture. Drop the row if the selection would
  hit an existing entry.
- **No duplicate themes.** Suppress history rows for any key already present in today's
  ledger, *including components of composites*. If `BOB + DECKS` is open, offering a history
  row `DECKS` would create a duplicate open theme and raise `duplicate_open_pomodoro_name`.
  Today's row still surfaces through its substring match.
- **Spelling.** A replacement uses the selector slug (`deep-work`) plus the existing
  bare-spelling `#` rule (`apply_bare_start_name_replacements`).
- **Hidden themes** appear only on an exact query match, as a dimmed row with
  `hidden: true`.

**Candidate fields** (additive, `decodeIfPresent` on the Mac):

| Field | Meaning |
| --- | --- |
| `origin: "today" \| "history"` | absent means today |
| `themes` | the shared object from §5.1 |
| `last_used`, `days_used` | history rows only |
| `similar_to: ["FIX"]` | on create rows (near-duplicate heads-up) |
| `hidden` | on the exact-match hidden row |

**Mac rendering.** Group headers "Today" / "Recent themes". Today, grouping exists only for
the `task` context. Each row gets an 8 pt rounded-square swatch.

Mockup (`▪` is a tinted swatch):

```
 =bo▏
 ┌────────────────────────────────────────────────────┐
 │ TODAY                                              │
 │ ▪ BOB          Planned · 2 links            Next   │
 │ RECENT THEMES                                      │
 │ ▪ BOOKS        Oct 21 · 3 days         +1 · 4/5    │
 │ ▪ BOT          Sep 29 · 1 day          +1 · 4/5    │
 │ + New Pomodoro BO                           New    │
 │                     ⇥ accept   ⌃D hide theme       │
 └────────────────────────────────────────────────────┘
```

**Other surfaces:**
- **zsh completion** inherits history rows for free.
- **Obsidian pickers** (link picker, nav move and rename pickers) get the same rows through
  `bob-ledger-tools` `api.themes.suggest(query, {ledger})`. This mirrors the Rust ranking and
  is gated by the shared vectors. The existing relation-label suggestion stage
  (`426-picker-relation-stage.js`, "used N×") is the in-repo UX precedent.
- **Mac "Name it" prompt** gets suggestions from `bob theme list --query Q -f json` (§5.5).
  The thin-client rule allows the app to filter what bob returned.

### 5.3 Hide (née disable)

**Gesture: ⌃D on a history row.** It is a toggle and applies only to `origin: history` rows.

1. The row stays in place as a ghost, `BOOKS hidden · ⌃D undo`, until the next keystroke
   re-queries. This is in-place undo with no global undo stack.
2. On a today row, ⌃D shows the hint "BOB is on today's ledger; hide it from Themes". It
   changes nothing.

Why ⌃D:

- It is Bryan's own proposal, and it is already the "delete property" key on the Obsidian
  Task Card.
- It is one-handed on every host.

Alternatives I rejected:

- **Shift+Delete** (the browser convention) needs Fn on a MacBook.
- **⌘⌫** is delete-to-line-start in the capture editor.
- **Ctrl+X** is already merge in nav.

The cost: Cocoa binds ⌃D to forward-delete in NSTextView. Claim it only while the popup is
visible *and* a history row is selected; otherwise pass it through. Document it in the Mac
`docs/keyboard.md`, and in the plugin references and footer hints.

**Writes:**
- Mac: `bob theme hide NAME -f json` in its own process lane (`"theme"`). The `"completion"`
  lane would cancel it. On failure, restore the row and put the error in the status line,
  following the `capture-templates delete` pattern.
- Obsidian: ledger-tools appends to the journal directly, as the review journal does, so it
  also works on mobile.

**Journal: `.bob/themes/<host>.jsonl`**, one file per host, append-only.

```json
{"v":1,"ts":"2026-10-24T09:41:07-04:00","host":"apollo","kind":"theme.hide","key":"fixes","name":"FIXES","via":"bob-mac-capture@…"}
{"v":1,"ts":"…","host":"mac","kind":"theme.unhide","key":"fixes"}
{"v":1,"ts":"…","host":"apollo","kind":"theme.color","key":"job","hue":"aqua"}
{"v":1,"ts":"…","host":"apollo","kind":"theme.rename","from":"fixes","to":"fix"}
```

- `hue: null` unpins.
- A `rename` event moves `from`'s state to `to` unless `to` already has explicit state, in
  which case `to`'s state wins.
- **Rollout:** add `!/.bob/themes/*.jsonl` to the vault `.gitignore`, and add the matching
  `merge=union` line to `.gitattributes`. This is a one-time vault edit that propagates
  through vault-sync, documented in `docs/vault-git-sync.md` as for the Stats journal.

**Management.**
- `bob theme hide|unhide NAME…` and `bob theme list --hidden`.
- The Obsidian Themes manager (§5.5).
- The exact-match recovery row in every menu.

### 5.4 Global rename

```
bob theme rename OLD NEW [-d/--dry-run] [-f/--format human|json] [-m/--merge] [-o/--offline]
```

**Scope:**
- The name tails of `## Pomodoros` entries in every canonical daily note. Component-wise:
  separators keep the ` + ` spelling, and a resulting duplicate (`FIX + FIXES` → `FIX`)
  collapses.
- Plus the `_templates/daily.md` Pomodoros lines. The template contains `- [ ] () — GTD`, so
  renaming GTD must update it.
- **Reported, not written:**
  - `config.yml` mentions (`plan.exempt`, `plan.inventory_labels`, Stats metric
    `themes`/`exclude_themes`). config.yml is chezmoi-managed, so bob prints the exact YAML
    path to edit.
  - Saved capture templates in the host-local shelf whose text contains the slug.
  - Prose mentions in notes are never touched.

**Flow:** copy `bob ref rename` exactly.
1. Take `bob_sync.lock` and run a pre-sync (unless `-o`), then replan.
2. Snapshot each file with a compare-and-swap check: a note that changed since planning
   aborts the run, as in capture.
3. Write atomically per file. Append the `theme.rename` journal event.
4. Verify: rescan, OLD is absent, entry counts are unchanged, and only name tails changed.
5. Restore the before-images on any failure.
6. Commit once with subject `bob theme rename: FIXES → FIX`, then run a post-sync.
7. Rollback is `git revert`, documented as a runbook.

**Refusals:**

| Code | When |
| --- | --- |
| `unknown_theme` | OLD is not in the catalog |
| `invalid_name` | NEW fails the name charset |
| `theme_exists` | NEW already exists; needs `--merge`, since a typo like BLOG → BOB is a plausible accident |
| `unchanged` | OLD and NEW are the same theme |
| `lock_busy` | the sync lock is held |
| `dirty_paths` | offline, and a touched path is dirty |
| `not_a_worktree` | the vault is not a Git worktree |
| `stale_note` | a note changed since planning |
| `sync_failed` | the pre- or post-sync failed |
| `verify_failed` | post-write verification failed |

Human dry-run mock:

```
RENAME  FIXES → FIX   merge: FIX already used on 3 days
  2026/20260903.md   2 entries   — FIXES          → — FIX
  2026/20261016.md   1 entry     — BOB + FIXES    → — BOB + FIX
  state              FIXES hidden → FIX keeps its own (visible)
  not changed        config.yml stats.metrics.fix_time.themes names FIXES (chezmoi; edit by hand)
dry run · nothing written · rerun with --merge to apply
```

**UIs** preview with `-d -f json` and execute through bob. In Obsidian this is a spawn via
the shared `api.stats.bobPath()`, desktop-only. Single-entry rename (nav's move/merge/rename
picker) stays as is. The global rename lives in the Themes manager and the CLI, so "rename
this Pomodoro" and "rename this theme everywhere" never share a gesture.

### 5.5 `bob theme` command group

This follows `cli_rules.md`: sorted options, a short alias for each, colored output.

- **Membership rule:** "read or change the Pomodoro theme catalog."
- **Why a new top-level group:** it is a new noun. `bob task` is reserved for rewriting task
  lines. `bob pomodoro` is runtime status.
- **Bare `bob theme`** = `bob theme list`. This is allowed because `list` is a flag-only,
  read-only default.

| Command | Purpose |
| --- | --- |
| `bob theme list [-a/--all] [-H/--hidden] [-q/--query Q] [-f]` | catalog, ranked as in §5.2 when `-q` is given |
| `bob theme hide NAME…` / `bob theme unhide NAME…` | journal writes |
| `bob theme color NAME HUE\|auto` | pin or unpin |
| `bob theme rename OLD NEW …` | §5.4 |

`bob theme list` mock. The ■ swatches use xterm-256 colors from `Hue::xterm()`, and names stay
in the default foreground:

```
THEMES  81 known · 4 today · 2 hidden · last 90 days
  ■ BOB        today    26d  ▂▅▇▆▇█▅▆   magenta
  ■ BLOG       Oct 23   14d  ▁▁▁▂▅█▇▅   orange
  ■ JOB        Oct 16    7d  ▁▁▁▁▁▇█▁   magenta
  □ GTD        today    51d  ████████   muted · exempt
  …
  hint  BOB and JOB share magenta and met on 6 days → bob theme color JOB aqua
  hint  SASE and BLOG share orange and met on 6 days → bob theme color BLOG red
```

The collision hint (`theme_hue_collision`) mirrors `area_hue_collision`:
- It covers unpinned pairs that co-occurred on ≥ 2 of the last 30 days.
- It suggests the slot least used among that theme's co-occurring set.
- It is advisory only. Nothing pins automatically.

### 5.6 Color on every surface

**Shared tokens.** Introduce `--bob-hue-<slot>` and alias the existing `--bob-area-<slot>` to
it. A pill is
`background: color-mix(in srgb, var(--bob-hue-X) 16%, transparent); color: var(--text-normal); border-radius: 4px`.
A muted pill uses `--background-modifier-hover` with `--text-muted`. This keeps the
stylesheet's "no hex outside data-viz tokens" rule.

| Surface | Treatment |
| --- | --- |
| Obsidian entry lines (Live Preview) | `Decoration.mark` over each component of the ` — NAME` tail (text stays editable). It reuses the home-chip extension's line scan and its `StateEffect` refresh. The `+` stays neutral. |
| Obsidian Reading view | post-processor wraps the components in pill spans |
| `bob-plan` theme line | `★ A · B` becomes pills |
| Obsidian pickers | ■ swatch before the name; hidden rows dimmed |
| Stats Themes panel | bars in the theme hue. "Color follows the entity, never its rank." The folded "other" row is gray, and labeled rows mean color is never alone. |
| Mac completion rows | rounded-square swatch (the area dot stays a circle) |
| Mac editor spans | background tint (alpha ≈ 0.18) behind a *known* theme name, ink text, per component. Unknown or new names keep the `.section` color, so there is no flicker while typing. |
| Mac agenda / cards / `+1 BOB` chip / destinations | tinted pill or swatch |
| CLI (`plan`, `pomodoro`, `capture` output, `theme list`) | xterm-256 ■ swatch plus a default-fg name |
| tmux | `#[fg=colourN]■#[default] BOB 12:34` |
| Hammerspoon mac pom (optional) | `hs.styledtext` swatch before the name. Never tint the title text: the menu bar already reserves red and green for overdue and worked status. |

Obsidian line mockup (⟦ ⟧ = tinted pill):

```
- [x] (**0920-0950** [t:: 30m]) — ⟦BOB⟧ + ⟦DECKS⟧        ● bob · dev
- [ ] () — ⟦GTD⟧ (muted)
```

### 5.7 The Themes manager (Obsidian)

The command **Bob: Pomodoro themes** opens a `FilteredPickerModal` (nav). Each row shows a
pill, `last used · N days`, a 12-week sparkline, and `today` / `hidden` / `pinned` badges.

**Keys:**
- ⌃D toggles hidden, consistent with the menus.
- Enter opens an action stage with mnemonic keys: `r` rename (live `bob theme rename -d`
  preview, then confirm), `c` color (1–8 pick a slot, 0 auto), `h` hide/unhide.

**Optional extras:**
- A `bob-themes` code block on a `dash_themes.md` page, reachable from the Stats Themes panel.
- A Mac Themes pane in v2. In v1 the Mac only needs ⌃D.

## 6. Risks and open questions

**Risks:**

1. **Per-keystroke cost on the Mac.** The catalog cache must be warm. Measure
   `capture-complete` latency on the Mac before and after.
2. **Rename touching today's open note.** The compare-and-swap snapshot plus Obsidian's
   reload on external change bound the risk. Capture already writes today's note under the
   same conditions.
3. **JS/Rust drift.** Shared vectors cover key normalization, hue precedence, ranking,
   hidden filtering, and the journal fold.
4. **A journal written before the `.gitignore` allowance reaches a host stays local.** The
   hide still works on that host; document it.

**Questions for Bryan:**

1. Is "hide" the right word, or do you prefer "retire" (stronger end-of-life intent)?
2. Should GTD be muted (my recommendation) or colored?
3. Accept the create-row move (ADJ-6)? A short new name that prefixes an old theme now needs
   ↓ before Enter.
4. Seed the pins JOB → aqua and BLOG → red?
5. Keep `--merge` as a required guard for renames into an existing theme?
6. Do you use Obsidian mobile? Hide would work there; rename would be desktop-only.

## 7. Alternatives considered and rejected

- **Store hide/pin state in `config.yml`.** It is chezmoi-managed and per host. A Mac write
  drifts and never reaches apollo or athena.
- **A single vault YAML/Markdown registry note.** It is human-editable, but concurrent edits
  from two hosts conflict. vault-sync keeps the remote copy and parks the local one under
  `_conflicts/`, so a hide is silently lost. The union-merged journal cannot conflict.
- **One note per theme.** That would be 81 notes for two months of use. It adds a note type
  (`parent:` and all) for no requested capability.
- **Theme color = its dominant area's hue.** This is semantically elegant, because it unifies
  "color = area". But most of Bryan's themes are dev work, so nearly every pill would be blue.
  It also drifts with history and is not name-based.
- **Per-day collision-free assignment** (shift a colliding theme to its next free slot). It
  guarantees distinct colors within a day, but BOB would change color on some days. That
  breaks learnability and the "deterministic from name" requirement.
- **A bigger or continuous palette** (12, 16, or hash hue in OKLCH/HSLuv, as XMPP's XEP-0392
  does for nicknames). It does not reduce collisions on real data (§2), and it exceeds the
  ~8 categorical hues a reader can distinguish. The validated 8 already work in Rust, JS, and
  Swift.
- **Auto-pin at first sighting.** It is stateful and multi-writer: capture, three plugins,
  and the Mac all create names. Pins would also race across hosts.
- **Auto-unhide on use.** It is a silent state change. The exact-match ghost row makes
  unhiding a one-key decision instead.
- **Plugins spawning bob for suggestions.** It adds latency to pickers and fails on mobile.
  The ledger-tools mirror plus vectors is the established pattern ("bob-ledger-tools mirrors
  it in JavaScript, and every other surface calls one of those two").

## 8. Recommended solution

**Rust owns the model.** Build a **theme catalog in bob-cli**:

- **Definition:** themes are `+` components keyed by `normalize_component`.
- **Data:** scanned from every daily note and cached by mtime.
- **State:** folded with a union-merged `.bob/themes/<host>.jsonl` hide/pin journal.
- **Contract:** `docs/pomodoro-themes.md` plus shared vectors.
- **Interfaces:** a new `bob theme list|hide|unhide|color|rename` group, and additive
  `themes` / `origin` / `last_used` / `days_used` / `similar_to` / `hidden` JSON fields.

**Suggestions everywhere.**
- Today's rows first, then recent themes ranked most-recent-first: prefix matches, then the
  create row, then substring matches.
- Guard against prefix shadowing and duplicate components.
- ⌃D on a history row hides it, as an in-place toggle.
- Hidden themes return only on an exact match, as a dimmed row with ⌃D to unhide.

**Rename** is one revertable bob transaction modeled on `bob ref rename`, with `--merge` as
the guard. UIs preview and invoke it; they never re-implement it.

**Color.**
- Stable FNV-1a slot from the existing validated 8-hue palette, a pin override, exempt themes
  muted.
- Drawn as tinted pills or rounded-square swatches with ink text, distinct from the area ●
  dot.
- Colored only once a name is known, so typing never flickers.
- A collision hint suggests pins. Seed JOB → aqua and BLOG → red.

**Phased rollout:**

| Phase | Repo | Deliverable |
| --- | --- | --- |
| 1 | bob-cli | `pomodoro_themes` module (catalog, cache, hue, journal fold), `docs/pomodoro-themes.md`, vectors, `bob theme list/hide/unhide/color`, vault `.gitignore`/`.gitattributes` runbook |
| 2 | bob-cli | history rows in `pomodoro_start_name` / `pomodoro_name`, ranking and guards, `themes` JSON on completion, parse spans, `capture-pomodoros`/agenda, `plan`, Stats; CLI and tmux swatches; `docs/capture.md` + `just docs-gen` |
| 3 | bob-cli | `bob theme rename` transaction, refusal codes, rollback runbook |
| 4 | bob-plugins | ledger-tools `themes` API namespace (mirror + vectors, plus consolidating today's four name normalizers), pills in Live Preview, Reading view, and the `bob-plan` block, history rows + ⌃D in the link, move, and rename pickers, Themes manager, Stats Themes hues |
| 5 | bob-mac-capture | decode the new fields, Today/Recent groups, swatches, ⌃D hide/unhide (`theme` lane), span tints, agenda pills, Name-it suggestions; `docs/protocol.md` compatibility rows, `docs/keyboard.md` |
| 6 | chezmoi (optional) | mac pom swatch from bob JSON |
| — | memory | `glossary:pomodoro-theme` strand + the four decision records, via `/sase_memory_write` |

Phases 1–3 are independently shippable. Phase 2 alone delivers the most-requested capability
(suggestions) in the Mac app and the CLI. Phases 4–5 follow the thin-client and mirror rules
already in force.

## Sources

- In-repo: `docs/plan.md` (Names, Themes, Exempt), `docs/pomodoro-homes.md` (R7 chips, R8
  hues), `docs/capture.md` (named starts, `pomodoro_name` / `pomodoro_start_name`),
  `docs/ref.md` (`bob ref rename` live flow), `docs/vault-git-sync.md` and `docs/stats.md`
  (review journal), `src/native/capture_complete/{pomodoros,support,model}.rs`,
  `src/native/capture_pomodoros.rs`, `src/native/plan_budget/mod.rs`,
  `src/native/pomodoro_homes/palette.rs`.
- Linked repos (opened with `sase repo open`): bob-plugins (block-id-prompt, nav,
  bob-ledger-tools, task-status-cycler files cited above), bob-mac-capture (files cited
  above), chezmoi (`home/dot_config/bob/config.yml`,
  `home/dot_hammerspoon/pomodoro_countdown.lua`).
- Memory: `glossary:pomodoro`, `glossary:mac-menu-bar-pomodoro-indicator`,
  `decisions:mac-capture-is-a-thin-client`, `decisions:idle-capture-shows-ledger-agenda`,
  `obsidian.md`, `cli_rules.md`, `docs.md`.
- Vault data: a read-only scan of `~/bob/YYYY/YYYYMMDD.md` on 2026-10-24. The numbers are in
  §2.
- Palette validation: the dataviz skill's `validate_palette.js` on the 8 area hexes (light
  mode).
- External:
  - [XEP-0392: Consistent Color Generation](https://xmpp.org/extensions/xep-0392.html):
    name-hash → hue precedent.
  - [9to5Google: delete Chrome autocomplete suggestions](https://9to5google.com/2020/05/05/google-chrome-delete-autocomplete-suggestions/)
    and [Make Tech Easier: delete a URL from Chrome's omnibox](https://maketecheasier.com/delete-url-from-chrome-omnibox/):
    the Shift+Delete history-suggestion removal precedent, including the Mac Fn requirement
    and the sync-resurrection caveat.
