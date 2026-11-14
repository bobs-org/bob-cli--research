# Design & Critique: Generated `## Areas` Catalog Section (`> [!areas]`)

**Author:** Researcher `gem`
**Date:** 2026-11-14
**Scope:** Vault schema (`~/bob`), `bob-cli` (`host_catalog`, new `bob areas`, `capture`, `highlights_ref`, `nightly`), and `bob-plugins` (`bob-ledger-tools`, `bob-navigation-hotkeys`)

---

## Executive Summary

**Verdict:** Yes — adding a Bob-maintained `## Areas` section (`> [!areas]`) to area parents (including `~/bob/area.md`) is the **right move**. Areas are the last hierarchical note type in Bob without an owned parent catalog (`Notebooks`, `Albums`, and `Projects` already share `src/native/host_catalog`). Today, Bryan is either flying blind across sub-area hierarchies (`area.md`, `love.md`, `gtd.md` have no child links at all) or hand-maintaining prose link lists that drift (`cash.md`, `inbox.md`).

However, **implementing `## Areas` as a naive copy of `## Projects` would be a mistake.** Areas differ fundamentally from projects: they never close, they have no `^prj` completion criterion, all 19 areas in `~/bob` currently lack `summary:` frontmatter, only **5 files** in the entire vault host child areas, and `~/bob/area.md` itself is a `[[type]]` definition note (`parent: "[[type]]"`), not a `type: "[[area]]"` note.

**Recommended Solution in Brief:**
1. **Shared engine + dedicated `bob areas` domain:** Add `AREAS` (`heading: "Areas"`, `callout: "areas"`) to `src/native/host_catalog/region.rs` and introduce a dedicated `bob areas [list | check | sync]` command + `bob nightly` step rather than overloading `bob projects`.
2. **Render a nested indented subtree (`push_forest`-style) in Markdown, not a flat direct-children list (`A1`):** Because areas are small and bounded (19 total notes, max depth 3, max fanout 7), rendering nested children turns `~/bob/area.md` into a crisp 19-line Markdown atlas of the entire vault and only expands one area host (`gtd.md`: 2 → 5 lines).
3. **Fix inter-catalog first-write placement (`A4`):** Generalize `host_catalog::Placement` so `AREAS` (`BeforeFirstH2`) deterministically precedes `PROJECTS` (`AfterSectionThenFirstH2("Areas")`), giving every note canonical top-to-bottom structure: `Areas → Projects → Notebooks → Albums → Tasks`.
4. **Make Obsidian's `> [!areas]` card genuinely beautiful (`bob-ledger-tools`):** Match the hued card family of `[!projects]` / `[!notebooks]`, add **per-row area color rings/swatches** from each area's resolved R8 hue (turning monochrome `area.md` and `color: grey` `gtd.md` into an expressive color-coded atlas), surface right-aligned live rollups (`tasks`, `● today`, `prj`, `nb`, `alb`), non-default config pills (`PLAN`, `offclock`, `no cap`), interactive branch fold toggles (`▾`/`▸`), and subtle `↻ sync` / `check` recovery chrome.

---

## 1. Empirical Audit of `~/bob` and the Existing Catalog Stack

Inspecting every note matching `type: "[[area]]"` in `/home/bryan/bob/` alongside `~/bob/area.md` reveals the exact shape of the problem:

### 1.1 Live Vault Inventory (`~/bob`)
- **Total area notes:** **19** `type: "[[area]]"` files (100% live at vault root; 0 in subdirectories).
- **Synthetic root (`~/bob/area.md`):** Frontmatter is `parent: "[[type]]"` + `created:` — **it does NOT carry `type: "[[area]]"` and has no `color:` or headings**, only 2 short descriptive paragraphs.
- **Exact host set today (only 5 notes out of 20):**

| Host note | Kind | `color:` | Direct child areas | Depth beneath host | Already has manual links? | Other generated H2s |
| --- | --- | --- | --- | --- | --- | --- |
| `area.md` | type note (`parent: [[type]]`) | *(none)* | **7** (`body`, `cash`, `dev`, `gtd`, `job`, `love`, `meet`) | **3** (19 total areas) | None | None |
| `love.md` | area (`type: [[area]]`) | `yellow` | **5** (`abby`, `family`, `fun`, `kelly`, `vacation`) | 1 | None | `Notebooks`, `Tasks`, `Future Work` |
| `inbox.md` | sub-area (`parent: [[gtd]]`) | *(inherits `grey`)* | **3** (`gkeep_inbox`, `gmail_inbox`, `mac_inbox`) | 1 | Prose sentence (`[[mac_inbox]], [[gkeep_inbox]], and [[gmail_inbox]]`) | `Notebooks`, `Tasks` |
| `cash.md` | area (`type: [[area]]`) | `magenta` | **2** (`bank`, `recur`) | 1 | `Related: [[bank]] [[old_recur]] [[legacy_cash]]` (stale `[[old_recur]]`) | `Notebooks`, `Tasks`, `Notes` |
| `gtd.md` | area (`type: [[area]]`) | `grey` | **2** (`gtd_daily`, `inbox`) | **2** (5 descendant areas) | `Related:` does not list child areas | `Projects`, `Notebooks`, `Tasks` |

- **Metadata & content gaps across all 19 areas:**
  - `summary:` frontmatter: **0 / 19** have a `summary:` key. Most use a 1–2 line body paragraph (e.g., `love.md`: *"Projects related to the all-powerful force of LOVE should link to this note as their `parent`."*).
  - H1 heading (`# ...`): only **4 / 19** have one (`bank` → `# 🏦 Bank`, `gmail_inbox` → `# Gmail inbox`, `inbox` → `# Inbox`, `mac_inbox` → `# Mac Inbox`).
  - Zero-H2 leaves exist (`bank.md` has `# 🏦 Bank` + `bank:` YAML + ````bob-bank```; `family.md` is a single body line).
  - Non-default configuration keys live in area frontmatter and cascade downward: `task_type` (`dev`: `BUILD`, `gtd`: `PLAN`, `gtd_daily`: `PLAN`, `job`: `WRITE`, `love`: `CHORE`, `meet`: `MEET`), `offclock: true` (`body`, `love`), `offclock_types: [MEET]` (`love`), and `ready_cap: off` (`inbox`, `gkeep_inbox`, `gmail_inbox`, `mac_inbox`).

### 1.2 Existing Codebase Foundations
1. **`bob-cli` shared engine (`src/native/host_catalog/region.rs`):** Already parameterizes `RegionSpec<'static>` (`NOTEBOOKS`, `ALBUMS`, `PROJECTS`) and exports `GENERATED_CATALOGS`. `insert_at` handles CRLF/LF, BOM, fenced-code exclusion, leading/trailing blank lines automatically, and `owned_regions` detects damaged callout openers cleanly when `strict_bare: true`.
2. **Capture guards (`src/native/capture_drawers.rs`, `src/native/capture/sections.rs`):** `is_structural_h2_key` and `is_generated_catalog_heading` already iterate over `GENERATED_CATALOGS`, whereas `reject_generated_catalog_selector` uses a hardcoded slice of specs + error codes and must add `AREAS` / `areas_section_generated`.
3. **Host scanning blind spot (`src/native/projects/scan.rs`):** `walk_typed_notes` explicitly skips any Markdown file that is neither `frontmatter_is_area` nor `frontmatter_is_project`, so `~/bob/area.md` is invisible to the `projects` pipeline. Meanwhile, existing `bob-cli` tests (`src/native/projects/catalog.rs`, `src/native/albums/registry.rs`, `tests/gmail_shell.rs`, `tests/cli/highlights/create.rs`, `tests/cli/capture/targets.rs`) frequently create a synthetic `"area.md"` test fixture **with** `type: [[area]]`.
4. **Colors (`src/native/pomodoro_homes/facts.rs`, `bob-ledger-tools/src/142-pomodoro-home-chips.js`, `142a-pomodoro-home-colors.js`, `styles.css`):** Eight `--bob-area-*` CSS variables (`blue`, `orange`, `aqua`, `yellow`, `magenta`, `green`, `violet`, `red`) exist with light/dark theme values. `color: grey` (`gtd.md`) intentionally resolves to `hue: null, hue_source: "muted"` so `[data-callout="projects"]` falls back to `--text-muted`.
5. **PDF Snapshots (`src/native/highlights_ref/note_snapshot/bob.rs`):** `apply_bob_task_rows` explicitly rewrites `[!projects]` callouts (`rewrite_projects_catalogs`), turning glyphs into chips and dropping `Closed` rows. Without equivalent handling, a raw `[!areas]` callout renders as a generic callout inside Reference/Note PDFs.

---

## 2. Critique of the Plan & Alternative Approaches

### 2.1 Is This Plan a Good Idea?
**Yes — with targeted adaptations.** Its strategic strengths outweigh its risks:

- **Completes the note-graph symmetry:** In Bob, `area`/`project` notes already materialize downward edges for every child kind (`## Projects`, `## Notebooks`, `## Albums`). Areas were the lone holdout. Giving `area -> area` and `area.md -> area` the same `host_catalog` contract eliminates an artificial seam.
- **Replaces brittle manual cross-links:** `cash.md` still links to non-child `[[old_recur]]` in `Related:`, `inbox.md` embeds child names in English prose, and `love.md`, `gtd.md`, and `area.md` omit child area links completely. Generated `## Areas` gives Bryan reliable, self-healing navigation.
- **Survives outside Obsidian:** Unlike Obsidian Bases or DataviewJS, a Markdown `> [!areas]` callout works in Neovim, `rg`, git diffs, Highlights PDF snapshots, and SASE AI agents reading `~/bob/area.md` or `~/bob/gtd.md` for vault structure.

### 2.2 Where a Naive Port of `## Projects` Fails
1. **Areas have no row body without intentional design:** A `## Projects` row has a natural two-part rhythm (`> - ⛓️ **[[sase]]** — sase has received >=1000 stars on GitHub!`). Areas have no `^prj` task, no `status`, no `Closed` group, and (today) zero `summary:` fields. A naive port produces `> - **[[abby]]**` — bare wikilinks with no textual value in raw Markdown.
2. **Direct-only visibility under-delivers on such a small graph:** Only **5** files even qualify for `## Areas`. If `area.md` lists only its 7 direct children flatly, a reader opening `area.md` in raw Markdown or PDF still cannot see where `bank`, `recur`, `gtd_daily`, `inbox`, `mac_inbox`, or `abby` live without hopping across multiple notes.
3. **Invariant gap on Area `parent:` and cycles:** `bob notebooks check` enforces `notebook_parent_kind` and `notebook_cycle`. Areas currently have no equivalent validator, so an accidentally inverted parent (`area -> project`) or cycle silently fails or confuses Pomodoro home walks.
4. **First-write heading race with `## Projects`:** Both `PROJECTS` (`Placement::BeforeFirstH2`) and a naive `AREAS` (`Placement::BeforeFirstH2`) target the same insertion anchor, meaning whichever sync runs second jumps ahead of the first.
5. **Visual flatness on `area.md` and `gtd.md`:** Both `area.md` (no `type: [[area]]`, no `color:`) and `gtd.md` (`color: grey`) resolve `notebookHostHueName` to `null`. Copying `[!projects]`'s single-hue `--bob-projects-hue` turns `area.md` — arguably the signature index card of the entire vault — into muted monochrome.

### 2.3 Comparison of Approaches

| Approach | Pros | Cons | Verdict |
| --- | --- | --- | --- |
| **A. Naive `## Projects` clone inside `bob projects sync`** | Minimal new CLI surface; reuses existing plugin file watcher immediately. | Conflates finite `^prj` project lifecycles with timeless areas; misses `area.md` in `walk_typed_notes`; direct-only leaves `area.md` blind to sub-areas; `BeforeFirstH2` ordering race. | **Reject** |
| **B. Obsidian-only (`areas.base` on `area.md` + virtual JS widget on area hosts)** | Zero Markdown edits to vault files; table columns/formulas trivially configurable in Obsidian. | Invisible in Neovim, git diffs, CLI, Highlights PDFs, and AI agent reads; misses the `[[area]]`-style Obsidian link graph (`inlinks`/`outlinks`); doesn't fit `love/cash/gtd/inbox` cleanly. | **Reject as primary** *(optional `areas.base` in `type.md` can complement if desired, though redundant with `area.md`'s card)* |
| **C. Dedicated `bob areas` + `host_catalog::AREAS` (nested tree) + Obsidian `[!areas]` card** | Clean CLI & JSON domain (`bob areas list/check/sync`); solves `area.md`, `Placement` ordering, and parent/cycle validation cleanly; full raw-Markdown atlas + rich hued Obsidian card. | Adds one small Rust module (`src/native/areas/`) and one card renderer family in `bob-ledger-tools` (highly pattern-identical to `projects`/`notebooks`). | **Recommended** |

---

## 3. Justified Requirement Adjustments

The original prompt frames `## Areas` as *"something similar"* to `## Projects` and assumes *"area notes can only be children of other area notes or the ~/bob/area.md file"*. Based on the empirical evidence, six specific adjustments are justified:

### A1. Render an indented subtree (`push_forest`), NOT strictly direct children
- **Original assumption:** Mirror `## Projects`, which lists direct children only.
- **Adjustment:** Render the **full descendant subtree rooted under each host**, indented 2 spaces per level (`base_depth = 0`), sorting each sibling level A–Z case-insensitively by stem (`path` tie-breaker) — the same `push_forest` pattern already used by `## Notebooks`. Include no `**Closed**` group.
- **Why justified:** Projects grow into hundreds of files with terminal archives (`sase.md` alone has 22 open + 38 closed sub-projects), so flattening descendants in Markdown would bloat `dev.md`. Areas are permanent life pillars: the entire vault has **19 areas**, max depth **3**, and **0** closed rows. With nested Markdown:
  - `area.md` becomes a complete, 19-line single-screen map of every area in Bob.
  - Across the 4 `type: [[area]]` hosts (`love`, `inbox`, `cash`, `gtd`), subtree rendering differs from direct-only on literally **one** file (`gtd.md`: 2 lines → 5 lines to show `inbox`'s 3 inbox children).
  - In Obsidian, parent branches (`cash`, `gtd`, `inbox`, `love`) still gain interactive `▾` / `▸ N` fold buttons so Bryan can collapse subtrees in Reading/Live Preview without losing Markdown completeness.

### A2. Introduce a dedicated `bob areas` command (`list | check | sync`) instead of overloading `bob projects`
- **Original assumption:** Unspecified (implied `bob projects` or shared sync).
- **Adjustment:** Add `bob areas [list | check | sync]` (bare `bob areas` = read-only `list`) in the **Vault** section of `bob --help` alongside `bob notebooks` and `bob albums`, plus an `areas` step in `bob nightly` directly before `projects`. Keep `list` and `check` strictly read-only.
- **Why justified:** Follows `cli_rules.md` (*"Nest only under a noun with a stated membership rule"*). Area validation (`area_parent_kind`, `area_cycle`, `area_color_invalid`), area telemetry (subtree task/project/notebook rollups + config inheritance), and `area.md` scanning do not belong inside `projects`' `^prj` lifecycle report (`bob projects sync` commit messages and `projects.issues` semantics stay clean).

### A3. Formalize and enforce the "area parents only" invariant — safely handling `area.md` across vault and tests
- **Original assumption:** Area notes can *only* be children of other areas or `~/bob/area.md`.
- **Adjustment:**
  1. Treat that rule as an **enforced contract in `bob areas check`/`sync`** (currently nothing forbids an area from setting `parent: [[some_project]]` or forming a cycle!), flagging invalid parent kinds (`area_parent_kind`), missing/ambiguous parents (`area_parent_missing`, `area_parent_ambiguous`), and cycles (`area_cycle`).
  2. Define `is_areas_host` carefully: a note is an Areas host if `frontmatter_is_area(&fm)` **OR** it is the vault-root `area.md` file (when not classified as `project`, `notebook`, `album`, or excluded in `done/` / `_templates/`). Keep `area.md` out of `walk_typed_notes` (`bob projects`), `capture-targets`, and Pomodoro-home resolution (`area.md` is a host catalog container, not a routable task home!).
- **Why justified:** Real `~/bob/area.md` lacks `type: [[area]]`, while `bob-cli` test suites routinely write synthetic `"area.md"` files *with* `type: [[area]]`. Using the union predicate handles both seamlessly without breaking a single existing test.

### A4. Fix `Placement` ordering so `## Areas` always precedes `## Projects`
- **Original assumption:** Unspecified placement mechanics.
- **Adjustment:** Give `AREAS` `Placement::BeforeFirstH2` and upgrade `PROJECTS` in `src/native/host_catalog/region.rs` from `BeforeFirstH2` to `AfterSectionThenFirstH2("Areas")` (mirroring `ALBUMS`' `AfterSectionThenTasks("Notebooks")`).
- **Why justified:** Prevents a sync-order bug where running `bob projects sync` after `bob areas sync` on a note lacking both headings would insert `## Projects` *above* `## Areas`. Canonical first-write order becomes `## Areas` → `## Projects` → `## Notebooks` → `## Albums` → `## Tasks`. Author edits to heading order afterward remain untouched (standard `host_catalog` ownership).

### A5. Make `summary:` optional on Areas, use `**[[stem]]**` links, and never write counts into Markdown
- **Original assumption:** None specified for row text.
- **Adjustment:** Format each row as:
  `> {indent}- **[[{link}]]**` *(plus ` — {inert_text(summary)}` only when optional `summary:` frontmatter is non-blank)*.
  Do **not** require `summary:` as an error or warning yet (0/19 areas have it today), and **never** embed task counts, `H1` emojis, or `task_type` tags into Markdown bytes.
- **Why justified:** `**[[stem]]**` matches `## Projects` and Bryan's `@stem` capture vocabulary (`@bank`, `@mac_inbox`), keeps diffs quiet when tasks change daily, and avoids generating 19 warnings out of the gate. When Bryan gradually adds crisp 1-line `summary:` frontmatter (like Notebooks already have), raw Markdown and PDFs automatically enrich without changing the contract.

### A6. Explicitly wire ecosystem exclusions, PDF snapshot formatting, and live plugin auto-sync
- **Original assumption:** Sections and UI only.
- **Adjustment:** Include four small companion hooks in scope:
  1. Register `AREAS` in `GENERATED_CATALOGS` and `reject_generated_catalog_selector` (`areas_section_generated`) so `bob capture` never appends bullets into `## Areas`.
  2. Add `[!areas]` handling in `src/native/highlights_ref/note_snapshot/bob.rs` so PDF reference/note snapshots render `[!areas]` cleanly alongside `[!projects]`.
  3. Add an `areas` fingerprint watcher + Reading/Live Preview card decorator in `bob-ledger-tools`, watching `area.md` + `[[area]]` frontmatter (`parent`, `type`, `color`, `summary`, `task_type`, `offclock`, `offclock_types`, `ready_cap`) and `[[area]]` `H1` / task counts. *(Do NOT invent a `%a` area-creation capture sigil in v1 — Bryan adds new areas rarely enough that `<ctrl+=>` / templater + auto-sync handles creation cleanly.)*
  4. Exclude `[!areas]` callouts cleanly in any task-link/child-note scanner where needed (`bob-navigation-hotkeys`'s `<ctrl+=>` child picker already knows `"area"`!).

---

## 4. Recommended Solution Specification

### 4.1 Markdown Contract (`## Areas` + `> [!areas]`)

- **`RegionSpec` (`src/native/host_catalog/region.rs`):**
  - `callout`: `"areas"` (`> [!areas]`)
  - `heading`: `"Areas"` (`## Areas`)
  - `head_title`: `None`
  - `placement`: `Placement::BeforeFirstH2` (while updating `PROJECTS` to `Placement::AfterSectionThenFirstH2("Areas")`)
  - `legacy`: `None`
  - `strict_bare`: `true` (malformed `> [!areas...` triggers `areas_catalog_damaged` and preserves file bytes untouched)
- **Host eligibility & membership:**
  - Every `type: "[[area]]"` note (not inside `done/`, `_templates/`, `_conflicts/`, or `dash.md`) resolves its scalar `parent:` via `NoteIndex` (`exact path`, then `unique case-insensitive basename`, resolving `[[area]]` → `area.md`).
  - Only hosts with ≥ 1 valid descendant area receive `## Areas`. If reparenting leaves a previous host with 0 child areas, `host_catalog` deletes the generated callout and retires the `## Areas` heading if that section contains only whitespace (preserving any authored notes/prose!).
- **Row grammar & deterministic ordering:**
  - `> {indent}- **[[{link}]]**` (`{indent}` = `"  ".repeat(depth)`, `link` = `stem` if unique else `path_without_md|stem`)
  - If optional `summary:` frontmatter is single-line and non-empty (or collapsed whitespace if multi-line with soft lint warning `area_summary_multiline`), append ` — {inert_text(&summary)}`.
  - Siblings at each depth sort **A–Z case-insensitively by stem**, tie-breaking on relative path. Cycles are broken deterministically in traversal (and reported as hard `area_cycle` errors by `check`/`sync`).

#### Concrete Vault Previews (How Bryan's Actual Files Will Look)

**`~/bob/area.md`** *(entire 19-area vault atlas in 19 clean Markdown lines; optional `summary:` shown where illustrative)*:
```markdown
---
parent: "[[type]]"
created: 2026-06-11 17:04
---
Area notes link to this note as their `type`.
Use this type for ongoing spheres of responsibility with no end state, such as [[job]]. Area notes can contain ongoing
task lists directly. [[project]]s and sub-areas use their `parent` property to point at the area they belong to.

## Areas

> [!areas]
>
> - **[[body]]**
> - **[[cash]]**
>   - **[[bank]]**
>   - **[[recur]]**
> - **[[dev]]**
> - **[[gtd]]**
>   - **[[gtd_daily]]**
>   - **[[inbox]]**
>     - **[[gkeep_inbox]]**
>     - **[[gmail_inbox]]**
>     - **[[mac_inbox]]**
> - **[[job]]**
> - **[[love]]**
>   - **[[abby]]**
>   - **[[family]]**
>   - **[[fun]]**
>   - **[[kelly]]**
>   - **[[vacation]]**
> - **[[meet]]**
```

**`~/bob/gtd.md`** *(shows Areas landing cleanly above Projects → Notebooks → Tasks)*:
```markdown
## Areas

> [!areas]
>
> - **[[gtd_daily]]**
> - **[[inbox]]**
>   - **[[gkeep_inbox]]**
>   - **[[gmail_inbox]]**
>   - **[[mac_inbox]]**

## Projects

> [!projects]
>
> - **[[needs_attn_tasks]]** — Review all of the tasks in the needs_attn_tasks file!

## Notebooks
...
```

**`~/bob/cash.md`** *(leaves Bryan's `Related:` untouched while placing `## Areas` cleanly above `## Notebooks`; `[[old_recur]]` can later be tidied manually)*:
```markdown
Related: [[bank]] [[old_recur]] [[legacy_cash]]

## Areas

> [!areas]
>
> - **[[bank]]**
> - **[[recur]]**

## Notebooks
...
```

---

### 4.2 Obsidian Card Aesthetic & UX Design (`bob-ledger-tools`)

Raw Markdown keeps diffs noise-free; Obsidian (`bob-ledger-tools`) transforms `> [!areas]` into a live, scannable, color-coded architectural dashboard without modifying note bytes.

#### Visual Tokens & Solving Monochrome Hosts
- Follow the exact card shell established by `[data-callout="projects"]` / `[data-callout="notebooks"]` in `styles.css`:
  - **Callout icon:** `--callout-icon: lucide-layers` (distinct from `lucide-puzzle` for Projects, `lucide-notebook-tabs` for Notebooks, `lucide-album` for Albums, `lucide-list` for Records).
  - **Host surface:**
    ```css
    .callout[data-callout="areas"] {
      --callout-icon: lucide-layers;
      --bob-areas-hue: var(--text-muted);
      container-type: inline-size;
      container-name: bob-areas;
      background: color-mix(in srgb, var(--bob-areas-hue) 9%, var(--background-secondary));
      border: 1px solid color-mix(in srgb, var(--bob-areas-hue) 28%, var(--background-modifier-border));
      border-radius: var(--radius-l, 8px);
      padding: 0.55em 0.9em 0.7em;
    }
    ```
    When hosted in a chromatic area (`love` yellow, `cash` magenta, `inbox` fallback), `data-root-hue="<hue>"` tints the card border and nested tree guide rails identically to `[!projects]` and `[!notebooks]`.
  - **Per-Row Color Dots / Swatches (`data-area-hue="<hue|grey>"`):**
    Because `area.md` is neutral and `gtd.md` is `color: grey`, **every row carries its own circular 9px color dot/ring before the area link**, tinted by that child area's resolved R8 hue (`body` green, `cash` magenta, `dev` blue, `gtd` neutral muted border, `job` aqua, `love` yellow, `meet` violet; sub-areas inherit their parent pillar's hue, giving `bank`/`recur` magenta dots and `abby`/`fun`/`kelly`/`vacation` yellow dots). When hovering or focusing a nested `ul` under a parent row in `area.md`, its left tree guide rail softly picks up `--bob-area-row-hue`.

#### Row Anatomy & Progressive Disclosure
Each rendered `<li>` lays out cleanly using flexbox (matching `.callout[data-callout="projects"] .callout-content li`) and container queries:
1. **Left cluster:** Branch toggle (`▾` / `▸` if the area itself has child areas) + **8–9px resolved hue dot** (solid ring for top-level / colored areas; softer dot for inherited sub-areas) + bold internal link `[[stem]]` + optional H1 badge or tooltip (e.g., `🏦 Bank` hint on `[[bank]]` when the note's H1 adds meaning beyond `humanize(stem)`).
2. **Right-aligned tabular chip strip (`.bob-areas-chips`):** Only non-zero / non-default chips render — zero clutter on quiet rows:
   - **Today indicator:** `● today` (`var(--text-accent)`) if any task in this area *or its descendant area/project subtree* is in today's Pomodoro agenda / due today (`tasks.today > 0`, tooltip distinguishes direct vs subtree).
   - **Task count:** `{N} tasks` (if direct == subtree, e.g., `18 tasks`; if a parent has rolled-up subtree tasks, e.g., `17 tasks` + muted tooltip `"0 direct · 17 in gtd_daily & inboxes"`, or compact `{direct}/{subtree}` when both > 0 — keep pill copy short and scannable!).
   - **Child collection counts (only when > 0):** `{N} prj` (open projects), `{N} nb` (notebooks), `{N} alb` (albums).
   - **Behavior / config pills (muted subtle pill, only when explicitly configured on that area):** e.g., `BUILD`, `PLAN`, `CHORE`, `offclock`, `no cap` (`ready_cap: off`). Gives immediate system clarity (*"oh, `inbox` and its 3 children have `ready_cap: off`, while `love` defaults to `offclock`"*).
3. **Second wrapped line (`.bob-areas-summary`):** If `summary:` exists (rendered as ` — <text>` in Markdown), style cleanly as muted clamped sub-text (`text-overflow: ellipsis`, full text in `title` tooltip), just like `.bob-projects-criterion`. If no `summary:` exists and the note has an H1/short intro line? Keep Markdown/DOM honest: show explicit `summary:` in the row, and expose H1 / first-line preview in the link hover tooltip (`areasCardTooltip`), avoiding arbitrary prose scraping on screen.

#### Visual Mockup of Obsidian Card Rendering

**In `~/bob/area.md` (neutral card border, rainbow per-row dots):**
```text
┌────────────────────────────────────────────────────────────────────────────┐
│ ▤ Areas   7 areas · 12 sub-areas · 6 open projects · 102 tasks       [↻ sync] │
│ ────────────────────────────────────────────────────────────────────────── │
│ 🟢 body                                  offclock · 8 tasks · 2 nb · 1 alb │
│ ▾ 🟣 cash                                                30 tasks · 2 nb   │
│   │ 🟣 bank                                                                │
│   │ 🟣 recur                                                       3 tasks │
│ 🔵 dev                             BUILD · 18 tasks · 3 prj · 9 nb · 1 alb │
│ ▾ ⚫ gtd                                     PLAN · 18 tasks · 1 prj · 2 nb │
│   │ ⚫ gtd_daily                                            PLAN · 17 tasks │
│   │ ▾ ⚫ inbox                                    no cap · 1 prj · 1 nb    │
│   │   │ ⚫ gkeep_inbox                                         no cap · 1 nb│
│   │   │ ⚫ gmail_inbox                                                no cap│
│   │   │ ⚫ mac_inbox                                         no cap · 1 prj │
│ 🩵 job                                    WRITE · 1 task · 1 prj · 1 nb    │
│ ▾ 🟡 love                        CHORE · offclock · 27 tasks · 2 nb        │
│   │ 🟡 abby                                                   2 tasks · 1 nb│
│   │ 🟡 family                                                              │
│   │ 🟡 fun                                           1 task · 1 nb · 2 alb │
│   │ 🟡 kelly                                                          2 nb │
│   │ 🟡 vacation                                                            │
│ 🟣 meet                                                       MEET · 1 nb  │
└────────────────────────────────────────────────────────────────────────────┘
```
*(In Obsidian on desktop, chips align flush-right on a single line per row with tabular numerals; on narrow panes `< 440px`, `.bob-areas-chips` wraps neatly below the row title via `@container bob-areas (max-width: 440px)`.)*

**Chrome, Interactivity & Resilience:**
- **Keyed DOM updates (`albumReplaceChrome`):** Preserves button focus/hover during live revalidation; per-pane fold map (`WeakMap`) remembers expanded/collapsed child branches (`▾`/`▸`).
- **Missing-region standalone anchor:** Identical to `241ae-plugin-projects-catalog.js`, if a parent area (or `area.md`) acquires its first child area before `bob areas sync` has run, Obsidian paints a compact standalone anchor card with `↻ sync` so the user is never surprised why no callout exists yet — and removes all chrome cleanly if the host has zero child areas and a `current` catalog.
- **Health & Error Recovery:** Surfacing `missing catalog` / `stale catalog` / `damaged catalog` badges in the header + `Retry` when CLI fails + `↻ sync` only when repairable (`missing`/`stale`). Never auto-writes vault files when `damaged`.

---

### 4.3 `bob-cli` Architecture & Contracts

#### 1. `host_catalog` Generalization (`src/native/host_catalog/region.rs`)
- Add `Placement::AfterSectionThenFirstH2(&'a str)`: locates `end` of `## {section}` (falling back to `first_h2()`, else EOF), and update `PROJECTS` to `Placement::AfterSectionThenFirstH2("Areas")`.
- Add `pub(crate) const AREAS: RegionSpec<'static>` (`callout: "areas"`, `heading: "Areas"`, `placement: Placement::BeforeFirstH2`, `strict_bare: true`, `legacy: None`).
- Export `GENERATED_CATALOGS = &[AREAS, PROJECTS, NOTEBOOKS, ALBUMS]`.

#### 2. New `src/native/areas/` Module
Parallel to `src/native/notebooks/` and `src/native/projects/`:
- `scan.rs`: Scan vault notes excluding `.obsidian`/`.git`/`_templates`/`_conflicts`/`done/`/`dash.md` + daily paths. Include every `frontmatter_is_area` note plus vault-root `area.md` (when not another typed note). Extract `parent`, optional `summary`, H1 title, `color`, `task_type`/`theme`, `offclock`, `offclock_types`, `ready_cap`, direct task counts (open / `done` / `today` via today's Pomodoro agenda), direct project/notebook/album counts, and resolve each area's R8 hue + subtree rollups.
- `catalog.rs`: Pure `plan_catalogs` building nested `push_forest` rows for every host (`area.md` + any `type: [[area]]` note that has child areas or an existing `[!areas]` callout) and returning `CatalogState::{Current, Missing, Stale, Damaged}` + `FileEdit` diffs. Zero filesystem writes inside the planner.
- `check.rs` / validation codes:
  - **Hard errors (exit 1 on `bob areas check` and prevent unsafe sync writes):**
    - `area_parent_missing` (area lacks `parent:`, or resolves nowhere)
    - `area_parent_ambiguous` (list-form `parent:` or ambiguous stem match)
    - `area_parent_kind` (area `parent:` points to a project, notebook, album, record, or ordinary note rather than another area or `area.md`)
    - `area_cycle` (self-parent or cycle in area `parent:` chain)
    - `areas_catalog_damaged` (malformed `> [!areas` opener on host)
  - **Soft warnings (exit 0 on `check`):**
    - `area_color_invalid` (mirrors R8 invalid `color:` lint)
    - `area_summary_multiline` (multi-line `summary:` folded cleanly on render)
    - `area_summary_long` (> 140 chars)
    - `area_parent_unquoted` (unquoted YAML `[[x]]` form; match `notebooks` check style cleanly)
- `sync.rs`: Dry-run diffs (`--dry-run` / `-d`) and locked pre-synced transaction reusing `notebooks::txn::apply_and_commit` (`HostKind::Area` hosts + `ReadDependencies` over all area notes & `area.md`), committing cleanly with `areas: sync area catalogs (N notes)`.
- `output.rs` & `cli.rs` (`cli_rules.md`-compliant, alphabetical options with short flags):
  ```text
  bob areas [list] [-b DIR] [-f human|json] [-r ROOT]
  bob areas check [-b DIR] [-f human|json]
  bob areas sync [-b DIR] [-d] [-f human|json]
  ```
  - **JSON v1 contract (`bob areas list -f json`):**
    - Top-level: `schema_version: 1`, `command: "list"`, `ok`, `today`, `counts` (`areas`, `top_level`, `sub_areas`, `hosts`, `open_tasks`, `today_tasks`, `errors`, `warnings`), `areas[]`, `catalogs[]`, `findings[]`.
    - Per-area entry: `path`, `stem`, `title` (H1 or humanized stem), `summary`, `parent`, `root`, `depth`, `hue`, `hue_source` (`"color" | "muted" | "hash" | null`), `config` (`task_type`, `offclock`, `offclock_types`, `ready_cap`), `direct` (`open_tasks`, `today_tasks`, `open_projects`, `closed_projects`, `notebooks`, `albums`), `subtree` (`areas`, `open_tasks`, `today_tasks`, `open_projects`, `notebooks`, `albums`), `children[]`, `issues[]`.
    - Per-catalog entry: `host`, `path`, `kind` (`"area_root" | "area"`), `state` (`"current" | "missing" | "stale" | "damaged"`), `rows` (`direct`, `total`), `issues[]`.

#### 3. Integration Touchpoints
- **`bob nightly` (`src/native/nightly.rs`):** Insert `Step { name: "areas", blurb: "Validate areas and repair area catalogs", run: run_areas_step }` immediately before `"projects"`.
- **`bob capture` (`src/native/capture/sections.rs`, `capture_drawers.rs`):** Add `(&host_catalog::AREAS, "`## Areas` is the generated area catalog (written by `bob areas sync`) and is not a section target; pick another section, or capture into one of its areas", "areas_section_generated")` to `reject_generated_catalog_selector`. `capture_drawers::is_structural_h2_key` and `capture_complete::transfer_assist` pick up `AREAS` automatically via `GENERATED_CATALOGS`.
- **Highlights / PDF Note Snapshots (`src/native/highlights_ref/note_snapshot/bob.rs`):** Render `[!areas]` callouts as clean linked tree blocks (matching `[!projects]` visual cleanliness).
- **Obsidian Service (`bob-plugins` `bob-ledger-tools`):** Add `areas` service + `[data-callout="areas"]` ViewPlugin / PostProcessor sharing the `bobSpawnJson` / `projectsReportState` pattern (`areasFingerprint` checks changes to `area.md`, `type: [[area]]` frontmatter, H1s, and open/today task counts for live badge revalidation; structural changes trigger debounced `bob areas sync` just like `bob projects sync` and `bob notebooks sync`).

---

## 5. Phased Implementation Plan

1. **Phase 1 — `bob-cli` Core & Guards:**
   - Extend `host_catalog::Placement` with `AfterSectionThenFirstH2("Areas")` for `PROJECTS` and add `AREAS` to `GENERATED_CATALOGS`.
   - Implement `src/native/areas/*`, `bob areas [list | check | sync]`, `bob nightly` registration, `capture/sections.rs` refusal (`areas_section_generated`), and `note_snapshot/bob.rs` `[!areas]` projection.
   - Add unit + CLI tests covering `~/bob/area.md` (`parent: [[type]]`) vs synthetic `type: [[area]]` `area.md` test fixtures, multi-depth nesting, `Placement` ordering when creating `## Areas` + `## Projects`, cycle/parent-kind errors, and dry-run/sync round-trips.
2. **Phase 2 — `bob-plugins` (`bob-ledger-tools`) Card & Live Service:**
   - Build `bob-ledger-tools` `areas` data decoder/service (`bob areas list -f json`, `bob areas sync -f json`) + `fingerprint` invalidation/auto-sync on desktop.
   - Build Reading PostProcessor + Live Preview ViewPlugin & CSS `[data-callout="areas"]` with per-row `--bob-area-*` color swatches, `lucide-layers` icon, rolled-up telemetry & config chips, branch fold `WeakMap`, standalone missing-region anchor, and accessibility/container-query polish.
3. **Phase 3 — Vault Rollout & Tidying (`~/bob`):**
   - Run `bob areas check` and `bob areas sync --dry-run` on `~/bob` to verify exact diffs on the 5 host notes (`area.md`, `love.md`, `inbox.md`, `cash.md`, `gtd.md`).
   - Optionally clean up redundant manual links (`[[old_recur]]` / `[[bank]]` in `cash.md`, inline child list in `inbox.md`) and add concise `summary:` lines to area notes if Bryan wants descriptive subtitles alongside links in raw Markdown.
