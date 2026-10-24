# Pomodoro themes: identity, completion, rename, and color

Researcher: `grk`. Independent report. Do not treat this as the swarm synthesis.

- **Question:** How should Bob grow first-class support for *pomodoro themes* (aka pomodoro names, themes): a glossary term, historical name completion with today's names ranked first, global rename, disable/hide from menus, and a deterministic per-name color used everywhere themes appear (including Obsidian and Bob Mac Capture)? Lead the design. Critique the request. Adjust requirements where justified. Recommend a solution.
- **Evidence:** bob-cli `src/native/capture_complete/{pomodoros,engine,model,cli,render,support}.rs`; `src/native/capture_pomodoros.rs`; `src/native/capture_pomodoro_name.rs`; `src/native/capture_task_sections.rs` (`is_pomodoro_name`); `src/native/plan_budget/mod.rs` (`split_components`, `normalize_component`); `src/native/pomodoro_homes/palette.rs` (FNV-1a 8-slot area hues); `src/native/stats/{index,metrics,render}.rs`; `src/native/nightly.rs`; `src/runner.rs` (`bob pomodoro` group); `docs/plan.md`; `docs/pomodoro-homes.md` R7–R8; `docs/capture.md` plan-budget / named-start; `docs/concepts/today-and-the-pomodoro-ledger.md`; glossary `Pomodoro`; CLI rules; decisions `mac-capture-is-a-thin-client`, `idle-capture-shows-ledger-agenda`. bob-mac-capture `CaptureKeyCommandRouter.swift`, `docs/keyboard.md`, `docs/task-pickers.md` (Naming a Pomodoro / Starting a named session), `CaptureEditorPalette.swift` (`pomodoro_name` → section purple), `PomodoroHomeColor.swift`, `CompletionRowContent.swift`. bob-plugins `block-id-prompt` pomodoro-link picker (`085-pomodoro-link-picker-modal.js`); `bob-ledger-tools` plan theme line, home-chip CSS (`data-home-hue`), Live Preview today-marks. Config `plan.exempt` / `plan.inventory_labels`.
- **Date of evidence:** bob-cli, bob-plugins, and bob-mac-capture trees as of 2026-10-24.

## Bottom line

Yes: give the ALL-CAPS ` — NAME` suffix a durable identity, a glossary term, historical completion, a vault-wide rename, a hide overlay, and a color of its own. No: do not treat a theme as a second object with a UUID, do not reuse the eight area-home hue slots, and do not bind `<ctrl+d>` as an unconditional "disable" key in a typing field.

**Recommended solution:** keep the canonical ALL-CAPS name as the identity. Derive the catalog from daily-note ledger suffixes. Overlay hide-state in config. Color each *component* with a new 12-slot palette hashed by the same FNV-1a already used for area homes, encoded as **colored small-caps text** so it never collides with the filled/hollow home dots on the same row. Bob owns ranking, hide, rename, and the hue slot; Mac Capture and the plugins only render.

The work is a good idea. The request as written over-indexes on a completion-menu key and under-specifies identity, composites, ranking relative to today's create/again rows, and the existing home-color system.

## Is this a good idea?

### What is right in the request

- **Names are already a product, and the product is incomplete.** Capture, plan, stats, the idle agenda, Hammerspoon, tmux, and the Obsidian link picker all speak ALL-CAPS ` — NAME`. Completion only sees *today's* daily note (`pomodoro_name_candidates` / `pomodoro_start_name_candidates` read `pomodoro::day_file_for`). Yesterday's `SASE` is gone until you retype it. That is the actual daily friction.
- **A glossary term is overdue.** Docs and code already say "theme" for two different things: the plan-budget *count* of distinct open non-exempt components (`docs/plan.md` "Themes"), and the *string* on the ledger line. Agents and humans collide those constantly. A glossary strand named **Pomodoro Theme** with aliases `pomodoro name`, `theme`, `named Pomodoro` (the last already in `glossary:Pomodoro`) is the cheapest correctness win in this whole brief.
- **Ranking today's names above history is the correct default.** `insert_pomodoro_creation_candidate` already inserts a create row after prefix-matching open names. History must sit *below* those open matches, and must never outrank a live ledger row the query still matches.
- **Global rename is a real vault verb.** The identity *is* the string. `BOB` in 200 daily files is 200 copies of the same name. A dedicated rewrite, under the maintenance lock, is the honest way to change it. `bob capture-pomodoro-name` only writes a name onto one *unnamed* open entry in today; it is the wrong tool.
- **Hide is the right escape hatch for typos and retired labels.** One-shot `BGUS` (the start-named tests even use that misspelling) will otherwise haunt completion forever once history is indexed.
- **Color is how a scannable ledger becomes beautiful.** Today every name is the same purple section-family ink in Mac Capture (`CaptureSemanticCategory.section` maps `pomodoro_name`), and the bob-plan theme line is muted uncolored text (`.bob-plan-themes { color: var(--text-muted) }`). Homes already proved that a documented, dual-implemented, deterministic hash can travel from Rust to JS to Swift without a global catalog.

### Where the request is underspecified or too sharp

- **"Theme" is already a loaded word.** Light/dark Obsidian themes, MkDocs `theme:`, CSS theme hooks (`--bob-task-tag-color`), and the plan-budget meter all use it. The glossary must pin *Pomodoro Theme* as the ledger-name identity and keep plan-budget "themes" as the *count of those identities currently open*.
- **Identity is the name.** There is no block id, no stem, no file. A parallel UUID catalog would desync from the daily notes, which are the only source of truth. Rename rewrites strings. Color hashes strings. Hide keys strings.
- **Completion already has a richer ranking than "today vs history".** `pomodoro_start_name` order is: planned placeholders (`next_up` first) → create → today's completed *again* → name-it → running. History is a generalization of *again* across days. It has to interleave with that order, not flatten it.
- **`<ctrl+d>` is a hostile default on a typing surface.** In Mac Capture, Control-D is emacs forward-delete in text fields, page-down in the Refs inspector, and unused in inline completion only because it currently falls through to native field editing. On the Task Card, Ctrl+D already deletes the selected property. The pomodoro-link picker search box is also a text field. Binding disable to Ctrl+D while the query is nonempty steals a character-editing chord on the exact surface where you type names.
- **Color cannot reuse the area-home palette.** Home chips already sit on the same Pomodoro row (`data-home-hue` filled/hollow dots, R7–R8, `PomodoroHomeChipView`). Hashing `SASE` into the same eight slots as `dev`/`gtd`/`job` would put two orange dots of different meanings on one line. Themes need a second palette and a second encoding.
- **"Anywhere themes are shown" is a large surface list.** Doing every surface in one epic will stall the completion win. Color and history have a natural phased order.

### Would I take a different approach?

I would still ship the glossary term, historical completion, hide, rename, and color. I would change three things:

1. **Catalog shape.** Derived from daily files, plus a hide overlay in `~/.config/bob/config.yml`. No first-class theme note, no UUID, no vault YAML of every name.
2. **Disable gesture.** CLI is the authority. The completion/picker chord is empty-query, two-step hide on a *history* row only. Native forward-delete stays while you are typing.
3. **Color language.** A 12-slot theme palette, FNV-1a on the canonical component, rendered as ink + a hairline underline. Home dots keep the existing 8-slot area palette.

I would skip: auto-disabling unused names; rewriting history on hide; blocking capture of a hidden name; a GUI theme manager; per-theme color overrides in v1; coloring the tomato or the time range.

## Requirement adjustments

Call-outs the lead should adopt or explicitly reject.

| ID | Adjustment | Why it is justified |
| --- | --- | --- |
| **ADJ-1** | Canonical term: **Pomodoro Theme**. Aliases: `pomodoro name`, `theme`, `named Pomodoro`. Glossary body distinguishes the *identity* from the plan-budget *count*. Update `glossary:Pomodoro` to link it. | Docs already use "theme" both ways (`docs/plan.md` vs capture `#name`). One strand prevents the next agent from inventing a third. |
| **ADJ-2** | Identity is the canonical ALL-CAPS name after `canonicalize_pomodoro_name` (trim, uppercase, `is_pomodoro_name` grammar). Composites split on `+` (`plan_budget::split_components`). Color, hide, and rename key the *component*. | Matches every writer and the plan engine. A UUID would be a second source of truth. |
| **ADJ-3** | History is a generalization of today's *again* / completed-only create rows, indexed from canonical `YYYY/YYYYMMDD.md` ledgers. Empty query keeps today's start list and adds at most **five** recent-not-today names under a `Recent` origin. Nonempty query adds matching history below today's open prefix matches, the create row, and today's again rows. | Empty `=#` is already a careful start picker. Dumping years of names on an empty query ruins it. Typing one letter is when history earns its keep. |
| **ADJ-4** | Rank, after the existing prefix-then-substring `rank()`: (1) today's open selectable names the query still matches, (2) create row when the current rule would insert one, (3) today's again rows, (4) historical rows, (5) name-it rows, (6) running last in `pomodoro_start_name`. Dedupe by canonical component: an open or again row suppresses the same name from history. | This is the request's "existing names on top" rule, made precise against the start-name list that already exists. |
| **ADJ-5** | Hide is a completion filter, never a capture ban. Typing a hidden name still creates. Open-today rows always remain visible. Hide keys components: a candidate drops when **any** of its components is hidden. | Disable is for menus. Banning a string you can still write on the daily note by hand is a trap. Composites would leak a hidden component if only the exact full string were filtered. |
| **ADJ-6** | **Do not bind Ctrl+D while the query is nonempty.** Optional chord: empty filter/query, history (or Recent) row selected, first press arms `Hide NAME?`, second confirms, Esc disarms. Footer `⌃D hide`. CLI remains the primary verb. | Same two-step pattern as the template shelf's Backspace-twice. Empty-filter Backspace already has special meaning in pickers. Forward-delete stays in the name field. |
| **ADJ-7** | Rename is `bob pomodoro theme rename OLD NEW` under the maintenance lock, with `--dry-run` and `--merge`. Default refuse when NEW already exists as a distinct component. Rewrites the ` — NAME` suffix on column-0 Pomodoro entries only, including composite components, across every canonical daily note. | `bob task` is reserved for task-line rewrites. `capture-pomodoro-name` names one unnamed entry. Merge is a deliberate history-combine, not an accident. |
| **ADJ-8** | Color uses a **new 12-slot theme palette**, FNV-1a 32 of the lowercase canonical component, modulo 12. Encoding is colored ALL-CAPS ink plus a 2px underline. Homes keep R8 dots. Unnamed stays muted. Composites color each component; ` + ` stays muted. | Two palettes, two encodings, one row. Reusing eight area slots fails the moment a home chip and a theme name share a line. |
| **ADJ-9** | Bob emits an additive `theme_hue` (slot name) plus `origin` on each pomodoro-name candidate. `schema_version` stays 1. Mac Capture remains a thin client: it paints the slot, it does not hash, it does not scan dailies. Plugins that color a daily note without a bob round-trip dual-implement the documented hash, the same way `bob-ledger-tools` already dual-implements plan budget and home hues. | `decisions:mac-capture-is-a-thin-client`. Homes already shipped this exact split (`hue: "orange"` on the wire, hex in Swift/CSS). |
| **ADJ-10** | Do not scan the vault on every keystroke. Keep a mtime-aware index at `.bob/pomodoro-themes-index.json` (machine cache, gitignored like other `.bob/` working files). Rebuild on miss, after rename, and as a cheap `bob nightly` step. Completion reads the cache plus today's live scan. | `bob stats` already walks every daily note; doing that inside `capture-complete` would hitch the panel. |
| **ADJ-11** | Hide overlay lives in config, sibling to plan, not inside `plan.exempt`: `themes.hidden: [BGUS, OLD NAME]`. Chezmoi already syncs `~/.config/bob/config.yml`. Exempt remains a budget rule. | Hiding a typo must not also drop it from the plan meter. Inventory labels (`SASE`, `MISC`) stay suggestable. |
| **ADJ-12** | One-shot names stay reachable by a unique prefix but do not occupy empty-query Recent unless used on **two or more days** or within the last **30 days**. | History without a gate resurfaces every typo. Disable is the manual override; the gate is the default hygiene. |
| **ADJ-13** | Phase the work. P0: glossary + hue algorithm + JSON `theme_hue`/`origin` + paint today's names (completion, start list, Name Pomodoro prompt, plan theme line, daily-note Live Preview). P1: historical index + ranking. P2: hide overlay + empty-query chord + CLI list/hide/unhide. P3: global rename. | Completion-without-history is still prettier. Rename-without-index is a grep. Shipping all four as one epic blocks the daily win. |
| **ADJ-14** | Color is redundant encoding. Names stay unique ALL-CAPS text. Increased-contrast and `NO_COLOR` still show origin badges (`today`, `again`, `recent`, `new`, `name it`). | Mac Capture pickers already require "color is never the only signal". |
| **ADJ-15** | Do not add per-theme color overrides, a themes note in the vault, or a settings GUI in v1. Rename *does* change color, because color is a hash of the new name; that is the visual confirmation the rewrite happened. | Overrides imply a catalog of objects. The point of this design is that the string is the object. |

## What is already true

| # | Fact | Evidence |
| --- | --- | --- |
| E1 | A named Pomodoro is the ` — NAME` suffix after the placeholder or time range. Grammar: starts with A–Z or 0–9, at least one letter, rest A–Z / 0–9 / `& ' ( ) + , . / -`, `+` allowed only in non-leading position. Canonical form is ASCII-uppercased. | `glossary:Pomodoro`; `canonicalize_pomodoro_name`; `is_pomodoro_name`; `POMODORO_NAME_USAGE` |
| E2 | Plan-budget "themes" are the count of distinct non-exempt *components* of open entries. `BOB + DECKS` is two components. GTD is exempt by default. Unnamed counts as `(unnamed)` only when it holds a counted link. | `docs/plan.md` Names / Exempt / Themes; `split_components`; `normalize_component` |
| E3 | `pomodoro_name` completion lists today's *open* entries, collapses duplicate slugs, keeps name-it rows, and may prefix a `creates_pomodoro` row when the query is a valid missing name. | `pomodoro_name_candidates_from_scan_with_hint`; `capture_complete/cli.rs` long_about |
| E4 | `pomodoro_start_name` (`=<X>#name` / `=#`) lists planned placeholders, then create, then today's completed again (most recent first), then name-it, then running. New and again rows carry `plan_themes_after` / `plan_themes_cap`. | `pomodoro_start_name_candidates_from_scan_with_hint`; mac-capture `docs/task-pickers.md` |
| E5 | Both contexts read **only today's** daily note. A missing note or missing `## Pomodoros` is a warning plus an empty list. | `pomodoro_name_candidates_at`; `pomodoro_start_name_candidates_at` |
| E6 | Ranking is case-insensitive prefix then substring, preserving source order inside each group. Empty query keeps the whole discovery set. | `capture_complete/support.rs` `rank()` |
| E7 | Mac Capture paints `pomodoro_name` spans with the **section** purple, the same family as task-section titles. Completion rows share that palette. | `CompletionRowContent.swift`; `CaptureEditorPalette.swift` |
| E8 | Name Pomodoro prompt is free-text: prefill from the query, `Saves as DEEP WORK`, then `bob capture-pomodoro-name`. It does not complete historical names. | `docs/task-pickers.md` "Naming a Pomodoro"; `CapturePomodoroNamePromptState` |
| E9 | Obsidian Ctrl+Shift+Enter pomodoro-link picker filters **today's** entries or names a new one. Keys: ↑↓ / Ctrl-N/P, Enter, Shift-Enter create, Esc. No hide chord. | `085-pomodoro-link-picker-modal.js` |
| E10 | Area homes already have a documented 8-slot palette, FNV-1a on the lowercase stem, light/dark hex, xterm-256, JS CSS `data-home-hue`, Swift `PomodoroHomeColor`. Chips sit on Pomodoro rows. | `docs/pomodoro-homes.md` R7–R8; `palette.rs`; `bob-ledger-tools` styles; `PomodoroHomeChipView` |
| E11 | Stats already walks every canonical daily note into `StatsIndex.daily_notes` and splits session names into uppercase theme parts. Theme parts are currently uncolored keys; area/project parts take home hues. | `stats/index.rs`; `pomodoro_components` in `stats/metrics.rs`; `hue_dot` in `stats/render.rs` |
| E12 | Vault working state already uses `.bob/` (gkeep imports, stats review jsonl). Those paths are machine-local / often gitignored. Plan config lives in `~/.config/bob/config.yml`. | gkeep tests; `stats/index.rs`; `docs/plan.md` Config |
| E13 | `bob pomodoro` is an existing noun group: default `status`, plus `tmux`, `notify`. `bob task` is reserved for vault-wide task-line rewrites. Capture protocol names are frozen `capture-*` siblings. | CLI rules; `runner.rs` |
| E14 | `capture-complete` JSON is schema_version 1; new optional fields stay v1. Mac Capture ignores unknown fields. | `capture_complete/model.rs`; mac-capture `docs/protocol.md` |
| E15 | Ctrl+D meanings today: Task Card delete-property; Refs inspector page-down; macOS/emacs forward-delete in text fields; template shelf uses Backspace-twice to delete. Inline completion does not bind Ctrl+D. | `docs/reference/plugins/task-card.md`; `RefsInspectorScroll.swift`; `docs/keyboard.md` |
| E16 | Idle capture agenda already shows today's named ledger rows through `bob capture-pomodoros --tasks`. The app never reads the daily note. | `decisions:idle-capture-shows-ledger-agenda`; `capture_pomodoros` `--tasks` |

## Design

### 1. Glossary: Pomodoro Theme

Add a glossary strand **Pomodoro Theme** (`pomodoro-theme`), aliases `pomodoro name`, `theme`, `named Pomodoro`.

Suggested body:

> A Pomodoro Theme is the canonical ALL-CAPS identity of a named Pomodoro, written as the ` — NAME` suffix on a column-0 ledger entry under `## Pomodoros`. The name *is* the identity: there is no separate id. Composite names (`BOB + DECKS`) are one entry with two theme components, split on `+`. Distinct open non-exempt components count against the plan theme cap (see [[plan]] / `docs/plan.md`). Exempt names such as `GTD` are still themes; they simply do not consume the cap. An unnamed entry is not a theme. Completion, color, hide, and rename all key this identity.

Link it from `glossary:Pomodoro` ("an optional ` — NAME` suffix makes it a named Pomodoro, whose identity is a [[pomodoro-theme]]"). Implementation writes the strand through `/sase_memory_write` with an accepted memory decision; this research does not edit memory.

Keep saying "theme cap" in plan docs. That is the count. The glossary term is the thing being counted.

### 2. Catalog: derived names + hide overlay + machine index

Three layers:

**Source of truth.** Every ` — NAME` on a canonical daily-note Pomodoro entry. Scan with the existing `capture_pomodoros::scan`. Index both the full suffix (`BOB + DECKS`) and each component (`BOB`, `DECKS`). Accepting a component inserts that component's slug (`bob`). Accepting a full composite inserts the composite slug (`bob+decks`).

**Hide overlay.** `themes.hidden` in `~/.config/bob/config.yml`, a list of canonical names. Loaded next to `plan:` with the same file-discovery rules. Invalid entries warn and skip. Missing key means nothing hidden. This is a completion preference, so it belongs with the other bob config chezmoi already syncs, and it must not be folded into `plan.exempt`.

**Machine index.** `.bob/pomodoro-themes-index.json` inside the vault working tree, gitignored. Shape:

```json
{
  "schema_version": 1,
  "generated_at": "2026-10-24T12:00:00-04:00",
  "entries": [
    {
      "name": "SASE",
      "days": 41,
      "last_used": "2026-10-24",
      "first_used": "2026-03-02"
    }
  ]
}
```

Rebuild when any daily-note mtime is newer than the cache, after a successful rename, on cache miss, and from `bob nightly`. `capture-complete` reads the cache in the same process as today's live scan; it never walks years of files on a keystroke.

`bob stats` already pays the full walk when you ask for a report. The theme index is that walk with a smaller payload.

### 3. Completion ranking and origins

Add an additive `origin` on `PomodoroNameCandidate`:

| `origin` | Meaning | Typical badge |
| --- | --- | --- |
| `open` | Today's open selectable named entry | `current` / `next up` / `planned` (existing) |
| `create` | Query would create a new name | `create` / `new session` |
| `again` | Today's completed name, new session | `again · last HHMM–HHMM` |
| `recent` | Empty-query, not today, recency gate | `recent · Oct 12` |
| `history` | Nonempty-query historical match | `used Oct 12` or `41 days` |
| `nameable` | Unnamed / untypeable placeholder | `name it` |
| `running` | The timed open entry in start-name | `running HHMM–HHMM` |

Ranking for `pomodoro_name` (link / `#` after `@route:id`):

1. Open selectable names matching the query (prefix group, then substring group).
2. Create row, using the existing insertion rule (only when the query is a valid missing name that is not an open prefix match).
3. History matches (and today's completed-only names, which become create/again-equivalent `creates_pomodoro: true` rows as they do now).
4. Name-it rows last, still present even when the query is nonempty, matching today's contract.

Ranking for `pomodoro_start_name` (`=#`):

1. Planned placeholders (`next_up` first), ranked.
2. Create row when `NamedSelection::Missing`.
3. Today's again rows, most recent first, ranked.
4. Recent (empty query, max 5) or history (nonempty query).
5. Name-it.
6. Running, never the default.

Dedupe: once a canonical component appears as `open` or `again`, drop it from `recent`/`history`. A create row whose name equals an again row is already suppressed by `select_named` (`Missing` vs completed). Keep that.

Recency gate for `recent` / unfiltered history: `days >= 2` or `last_used` within 30 days. A unique prefix of a one-shot name still finds it under a nonempty query, so typos remain reachable and hide-able.

Name Pomodoro prompt and the Obsidian pomodoro-link picker consume the same candidate list. The prompt today is a dead-end text field; it should be the same completer, with name-it as the reason it opened.

Mac Capture stays thin: it already renders `creates_pomodoro`, `requires_name`, `next_up`, and cap badges from JSON. `origin` and `theme_hue` are two more fields. No Swift-side daily-note scan.

### 4. Hide / disable

**CLI (authority).** Nested under the existing `bob pomodoro` noun:

- `bob pomodoro theme list` (default member of the `theme` subgroup; read-only; human + JSON)
- `bob pomodoro theme hide NAME`
- `bob pomodoro theme unhide NAME`

`list` columns: name, days, last used, origin-today (open/again/—), hidden, hue slot. `--all` includes hidden. Hidden rows stay in the list so they can be unhidden.

Writes append/remove canonical names in `themes.hidden`. They do not rewrite daily notes. Help is alphabetical; every public long option gets a short alias (`-a/--all`, `-f/--format`, `-n/--name` as needed).

**Completion chord (optional, secondary).** Only when:

- the completion/picker query is empty,
- the selected row's `origin` is `recent` or `history`,
- the first Ctrl+D arms a one-line confirm (`Hide SASE from name lists?`),
- the second Ctrl+D calls the same hide path,
- Esc / any query keystroke disarms.

Today's `open` / `again` / `nameable` / `running` / `create` rows ignore the chord. A nonempty query leaves Ctrl+D as native forward-delete.

Obsidian picker's search box follows the same empty-query rule. Footer hint sits next to `↑↓ select`.

Re-enable from `bob pomodoro theme unhide` or by removing the config line. No "disabled" tombstone on the daily note.

### 5. Global rename

`bob pomodoro theme rename OLD NEW` (`-o/--old`, `-n/--new`, `-d/--dry-run`, `-m/--merge`, `-f/--format`).

Behavior:

- Canonicalize both arguments with `canonicalize_pomodoro_name`. Reject invalid names with the existing usage text.
- Acquire the vault maintenance lock (same family as `bob ref` rename / nightly).
- Walk canonical daily notes only (`YYYY/YYYYMMDD.md`). Skip fenced code. Touch only column-0 Pomodoro entry lines whose parsed name has OLD as a component.
- Replace that component, preserving sibling components and their order: ` — BOB + DECKS` + rename BOB→SASE becomes ` — SASE + DECKS`. Collapse `SASE + SASE` to `SASE`.
- Default: if NEW already exists as a component anywhere in the walk, refuse (`theme_rename_collision`) and print the first few paths. `--merge` allows the combine.
- Atomic: write all files or none (temp + rename per file, abort and restore on the first failure, report the partial set if restore fails).
- Human summary: `renamed BOB → SASE in 37 entries across 22 daily notes`. JSON: files, replacements, skipped, collision.
- `--dry-run` prints the same plan without writes.
- Refresh the theme index after success.
- If OLD was in `themes.hidden`, drop it; do not auto-hide NEW.

Out of scope for v1: rewriting prose mentions, task-section titles that happen to equal the name, Hammerspoon config, or stats caches other than the theme index. Stats will pick up the new strings on the next full index because the dailies changed. That is the point of a global rename.

### 6. Color

**Algorithm (pin in `docs/pomodoro-themes.md`, dual-implemented like R8).**

```
slot = THEME_HUE_ALL[ fnv1a32(lowercase_canonical_component) % 12 ]
```

Reuse `pomodoro_homes::palette::fnv1a32`. New table, twelve names that do not overlap R8 (`blue orange aqua yellow magenta green violet red`):

| Slot | Hue | Role |
| ---: | --- | --- |
| 1 | `coral` | warm red-orange |
| 2 | `teal` | cool green-blue |
| 3 | `gold` | yellow |
| 4 | `plum` | purple |
| 5 | `sage` | muted green |
| 6 | `indigo` | deep blue-violet |
| 7 | `rust` | brown-orange |
| 8 | `pink` | light magenta |
| 9 | `olive` | yellow-green |
| 10 | `sky` | light blue |
| 11 | `bronze` | tan |
| 12 | `lilac` | light violet |

Implementation pins light/dark hex and xterm-256 with the same contrast discipline as `docs/task-tag-marks.md` (WCAG 4.5:1 against `--background-primary` in both appearances). This research does not invent final hex; the implementer measures and pins vectors, including `fnv1a32(b"sase")` like the existing `job` → Magenta home test.

**Encoding, everywhere:**

- **Ink + 2px underline** on the ALL-CAPS letters. No filled dot. Home chips keep `●` / `○`.
- Composite: `BOB` in its slot, muted ` + `, `DECKS` in its slot.
- Unnamed, `(unnamed)`, and name-it rows: `--text-muted`, no underline.
- `NO_COLOR` / increased contrast: origin badge text remains.

**Wire format** (additive on each pomodoro-name candidate and on plan `theme_names` entries):

```json
"theme_hue": "teal"
```

For composites, either one candidate with `theme_hues: ["coral", "indigo"]` or pre-split display spans. Prefer `theme_hues` on the candidate plus a documented client join, so Mac Capture does not parse `+` itself. Bob already splits components; sending the list keeps the client thin.

**Where to paint (priority):**

P0, ships with the algorithm:

- Mac Capture completion rows and editor `pomodoro_name` spans (leave the `#` sigil in section purple; color only the name bytes).
- Name Pomodoro "Saves as NAME" hint.
- Idle agenda Pomodoro titles.
- Capture preview Pomodoro block headlines (`PomodoroBlockView`).
- Obsidian Live Preview + reading view on daily-note ` — NAME` (CodeMirror decoration + post-processor in `bob-ledger-tools`, same family as today-marks).
- bob-plan theme line (`★ GOALS · DECKS · BOB`), each token inked.
- `bob plan` / `bob capture-complete` human output via xterm-256.

P1:

- Stats theme dimension bars and the Stats plugin Themes view (today those parts are uncolored keys).
- Obsidian pomodoro-link picker titles.
- `bob pomodoro theme list`.

P2:

- Hammerspoon menu-bar `THEME (50m)` (chezmoi `pomodoro_countdown.lua`; coordinate with `bob pomodoro --show-stale --worked`).
- tmux status name.

Do not color: the tomato, the checkbox, the time range, Task Links, home chips, exempt-vs-not (GTD still hashes; exemption is a budget rule, not a color rule).

Obsidian source (raw markdown) can stay uncolored; Live Preview is the daily driver. iOS without the plugin degrades to uncolored names, which is acceptable under ADJ-14.

### 7. CLI shape

Under `bob pomodoro`, add a `theme` subgroup whose membership rule is: *commands that list or rewrite Pomodoro Theme identity across daily notes, or the hide overlay*.

```
bob pomodoro theme          → list (flag-only read-only default)
bob pomodoro theme list
bob pomodoro theme hide
bob pomodoro theme unhide
bob pomodoro theme rename
```

Bare `bob pomodoro` remains `status`. Do not put these under `bob task`. Do not invent `capture-theme-*`; capture protocol names are frozen.

JSON for `list` reuses index fields plus `hidden` and `theme_hue`. Human list is a colored table, hidden names dimmed with a `hidden` badge.

### 8. Docs, tests, decisions

- New contract page `docs/pomodoro-themes.md` (algorithm, ranking, hide, rename, JSON). Link from `docs/plan.md` Names, `docs/capture.md` named-start / completion, mac-capture `task-pickers.md` and `keyboard.md`, plugin pomodoro-link picker reference.
- Decision record: *Pomodoro Theme identity is the canonical name; color is a second palette; hide is a completion overlay.* Cite this research.
- Tests: FNV vectors per slot; ranking fixtures (open beats history; create still inserts before substring; hidden component suppresses composites; empty query recent cap); rename component-in-composite, collision refuse, `--merge`, fenced-code skip, dry-run; hide does not affect `bob capture =#HIDDEN`; completion JSON omits hidden history; schema_version stays 1.
- Cross-repo: bob-cli (engine, CLI, docs), bob-plugins (LP decorations, picker, plan line, stats themes view), bob-mac-capture (paint `theme_hue` / `origin`, empty-query hide chord, Name Pomodoro completer), chezmoi Hammerspoon in P2.

## Critique of the plan in general

The plan is the right product instinct: names are a vocabulary Bryan reuses every day, and the software currently has the memory of a goldfish past midnight.

The failure mode to avoid is **turning a suffix into a CMS**. A themes note, UUIDs, color pickers, and a disable that rewrites history would make the ledger heavier than the work it records. The ledger is supposed to stay a daily markdown list. Everything in this design either *reads* those lists, *rewrites the suffix in place*, or *filters a menu*.

The second failure mode is **color collision with homes**. That system just landed, it is documented, it is on the same row, and it is doing a different job (where the linked tasks live vs what you named the session). Mixing them would make both encodings lie.

The third is **a destructive chord on a text field**. Hide is rare. Typing is constant. The template shelf already taught the project that rare destructive acts want two steps and a footer hint.

## Recommended solution

Ship **Pomodoro Theme** as a named identity with four verbs — *complete, color, hide, rename* — and one rule: **the canonical ALL-CAPS component is the object**.

1. **Glossary** strand `pomodoro-theme`, linked from `Pomodoro`. Plan-budget "themes" remain the count of open non-exempt components of those identities.
2. **Bob-owned catalog.** Daily-note suffixes are the source of truth. `.bob/pomodoro-themes-index.json` is the per-machine cache. `themes.hidden` in config.yml is the hide overlay. No UUID, no vault theme note.
3. **Completion.** Same `capture-complete` contexts as today (`pomodoro_name`, `pomodoro_start_name`), plus the Name Pomodoro prompt and the Obsidian link picker. Additive `origin` and `theme_hue` / `theme_hues`. Today's open matches stay first. History generalizes *again*. Empty query gains at most five recent-not-today names. Mac Capture renders; it does not invent names.
4. **Hide.** `bob pomodoro theme hide/unhide/list`. Optional empty-query two-step Ctrl+D on a history/recent row. Capture of a hidden string still succeeds. Open-today rows always list.
5. **Rename.** `bob pomodoro theme rename OLD NEW` under the maintenance lock, component-aware, collision-refused unless `--merge`, `--dry-run` supported, daily Pomodoro suffixes only.
6. **Color.** New 12-slot palette, FNV-1a of the lowercase component, ink + underline, dual-implemented, documented. Homes keep R8 dots. Thin clients consume `theme_hue`. Live Preview paints the suffix in Obsidian. Unnamed stays muted.
7. **Phasing.** P0 glossary + color on today's surfaces. P1 historical index + ranking. P2 hide. P3 rename. Each phase is user-visible and shippable on the daily train.

This is intuitive (the name you type is the thing), reliable (one scanner, one hash, one overlay, one rewrite), and beautiful (quiet per-name ink beside the home dots, origin badges when color is off).
