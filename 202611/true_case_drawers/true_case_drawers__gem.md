# Removing the ALL-CAPS Requirement from Task Drawers: Syntax, Rendering, Capture, and Lossless Project-Note Design

**Date:** 2026-11-22  
**Scope:** `bob-cli`, `bob-plugins`, `bob-mac-capture`, and the Bob vault (`~/bob`)  
**Related Work:** WIP epic `bob-cli-on` (*Task requirements (reqs)*), `bob.md` roadmap (`^no-all-caps-for-drawers`, `^micro-tasks`, `^tasks-parent-projects`, `^task-to-project`)

---

## Executive Summary

**Verdict: Yes — removing the ALL-CAPS requirement for task drawers is the right design decision, and the window immediately after `bob-cli-on` closes is the single cheapest moment in Bob's history to make the switch.**

An empirical read-only census of the entire vault (`~/bob`) found only **7 ALL-CAPS task drawers** in existence (4 on open tasks, 1 on an active closed task, 2 archived in `done/`). Once `bob-cli-on` finishes rolling out automatic `NOTES` drawer filing across requirements-owning tasks, ALL-CAPS drawers will multiply rapidly. Doing a clean cutover immediately after `bob-cli-on` lands prevents that proliferation, eliminates lossy casing round-trips (`API DESIGN` → `Api Design`), and establishes exact title isomorphism between task drawers and project-note `## H2` headings.

### Recommended Solution at a Glance

| Dimension | Recommendation | Key Rationale |
|---|---|---|
| **On-disk syntax** | **Whole-line bold:** `- **Title**` (direct non-checkbox child of a `#task`, entire trimmed body wrapped in a single `**...**` span, no trailing `:`, not reserved) | Zero-noise standard CommonMark; 0.066% prose collision in vault census (1 of 1,504 direct `#task` note children); matches Bryan's instinct in `bob.md`; native Live Preview reveal of `**` on caret adjacency. |
| **Why not `#foo` tags** | **Confirmed ruled out.** | Any `#tag` on a child bullet pollutes Obsidian's note-level `metadataCache.tags`, Tag Pane, Graph View, `tag:` search, and Dataview `file.tags`/`L.tags`, collides with capture `#` sigils, and renders as a clickable search pill. |
| **Cutover policy** | **Clean cutover** (no permanent ALL-CAPS fallback) + previewed one-shot vault migration for the 7 existing drawers | Eliminates acronym false positives (`TODO`, `WIP`, `FYI`), keeps parser/JS-twin surface half as big, and touches only 7 lines across 6 files. |
| **Visual rendering** | **Attribute-only architectural section-tab pill** in `bob-ledger-tools` (`Decoration.line` + Reading View post-processor) | Crisp `14×14` SVG drawer/tray CSS mask, `font-family: var(--font-interface)`, **strictly preserved case** (never `uppercase`/`small-caps`), quiet tabular child-count whisper (`::after`), dashed border when empty, muted when owner is closed, native `**Title**` reveal when editing. |
| **Capture syntax** | **Selective reuse of `capture_language/notebook.rs`:** share the glued `#selector` / `#"..."` parser, exact→slug→ambiguity resolver, and smart-casing creator; keep `- **Title**` as the canonical first-level capture bullet (with `- #selector` shorthand) | Preserves `decisions:capture-bullets-mirror-the-task-block`, avoids noisy quotes for multi-word drawers (`- **API Design**`), honors vault catalog spelling on all-lowercase slugs (`#api-design` → `API Design`), and preserves explicit mixed case (`#macOS-setup` → `macOS Setup`). |
| **Editor ergonomics** | **Refined typing kit** instead of bare `- *` → `- **<cursor>**` | Bare `- *` breaks `*italic*` bullets (8 in vault) and fights Obsidian's default `autoPairMarkdown: true` (where `**` already yields `**<cursor>**`). Replace with: native `**` auto-pair + **Smart `Enter` inside `- **Title|**`** (exits `**` and opens indented child `- |`) + atomic `Backspace` on `- **|**` + optional `- *` + `Space` trigger + Toggle Drawer command. |
| **`bob-cli-on` coordination** | **Zero semantic conflict; sequence right after `.12` & `.17` close.** | Requirements are non-`#task` checkboxes (`- [ ]`); drawers are non-checkbox children. Coordinate to also fix a live `bob-cli-on` bug where req-owning `^prj` tasks append duplicate `## NOTES` at EOF instead of routing into `## Notes`. |

---

## 1. Critique of the Plan & Justified Requirement Adjustments

### Is This a Good Idea?

**Yes — unequivocally.** The ALL-CAPS rule was a clever zero-punctuation heuristic when drawers were first introduced, but it now works against three core Bob goals:

1. **Semantic fidelity:** Real section names carry meaningful case and punctuation (`API Design`, `iOS App`, `macOS Setup`, `Q&A`, `C++ Notes`, `Phase 1: Auth`). Today, `formatProjectSectionTitle` (`bob-navigation-hotkeys/src/100-yank-and-paths.js:850-858`) explicitly documents the loss:
   > `// Acronyms are not special-cased: "API DESIGN" becomes "Api Design".`
   A drawer called `API DESIGN` promoted to a project note becomes `## Api Design`; demoting it back turns it into `API DESIGN`. True capitalization cannot survive a single round-trip.
2. **Visual confusion and false positives:** ALL-CAPS is overloaded with shouting, acronyms (`TODO`, `WIP`, `FYI`, `URL`), and Pomodoro names (`BOB+SASE`, `C++`), forcing awkward character-set bans (`+` forbidden in drawers, `:`/`?` forbidden in Pomodoro names — `src/native/capture_drawers.rs:1596-1673`) and forcing Google Calendar import (`src/native/gcal/description/bullets.rs:140`) to escape ALL-CAPS lines by wrapping them in `**...**`.
3. **Timing leverage:** Only **7 ALL-CAPS task drawers** exist in the entire vault right now. Waiting until `bob-cli-on` automatically files notes under `NOTES` across dozens of active tasks would turn a 7-line migration into a broad vault rewrite.

### Four Justified Adjustments to the Requirements

Before committing to implementation, four aspects of the initial direction merit explicit refinement:

#### Adjustment 1: Refine the `*` Auto-Expand Ergonomics (Critique of `bob.md`'s Note)
In `~/bob/bob.md:117-118`, the task `^no-all-caps-for-drawers` sketches:
> *"Use `**Title Text**` for this! The `*` character should expand to `**<cursor>**` when typed at the start of a sub-bullet!"*

Triggering expansion on a **bare single `*`** at bullet start has two concrete pitfalls:
1. **Breaks `*italic*` child notes:** The vault audit found **8 direct `#task` children beginning with `*italic*`** (including un-headered date log entries like `*2026-11-07* — ...` and Google Calendar summary lines). Auto-expanding bare `*` makes typing an italic note frustrating.
2. **Fights Obsidian's built-in Markdown auto-pairing:** Inspection of `/home/bryan/bob/.obsidian/app.json` confirms `autoPairMarkdown` is unset (Obsidian's default: **enabled**). With auto-pair on, typing `*` produces `*<cursor>*` and typing a second `*` immediately produces `**<cursor>**` in two native keystrokes. Intercepting the first `*` causes double-pair conflicts if Obsidian's native pairing also fires.

**Recommended ergonomic replacement:**
- **Keep native `**`** as the direct path (2 taps → `**<cursor>**`).
- **Add Smart `Enter` inside a drawer title (`- **Title|**`):** The real friction with `**Title**` is *leaving* the closing `**` to type the first note inside the drawer (normally `Right, Right, Enter, Tab, -, Space`). When pressing `Enter` with the cursor immediately before the closing `**` of a non-empty drawer header, automatically hop past `**`, insert a newline, indent one level deeper, and emit `- |`!
- **Add atomic `Backspace` on `- **|**`:** Pressing `Backspace` inside an empty bold pair at bullet start deletes all four asterisks cleanly back to `- |`.
- **Optional 2-key trigger — `- *` + `Space` → `- **<cursor>**`:** If you still want a single-asterisk shortcut (mirroring how `- [` + `Space` works in checklists), trigger on `*` followed by **`Space`** at bullet start. CommonMark forbids whitespace immediately after an opening italic `*`, so `- * ` has **zero conflict** with `*italic*` text!
- **Add a Toggle Drawer command/hotkey** (e.g., `Ctrl+Shift+D`, mirroring `Ctrl+]` for requirements) to wrap or unwrap an existing direct child bullet between `- Plain note` and `- **Plain note**`.

#### Adjustment 2: Choose a Clean Cutover Over Permanent Dual ALL-CAPS + Bold Recognition
It is tempting to recognize *both* `- NOTES` and `- **Notes**` permanently for backward compatibility. **Don't.** Dual recognition would:
- Keep every acronym false positive (`- TODO`, `- WIP`, `- FYI`) alive forever.
- Force `bob-cli`, all 3 twin JS bundles in `bob-plugins`, `gcal/description/bullets.rs`, and `bob-mac-capture` to carry two parsers and two escaping rules.
- Leave `NOTES` vs `**Notes**` visually inconsistent in the vault.

Because the entire vault holds only **7 ALL-CAPS task drawers**, a previewed one-shot migration (plus bumping `DRAWER_CATALOG_VERSION` from 2 → 3) is strictly cleaner, safer, and simpler.

#### Adjustment 3: Share the Notebook H2 Resolution Engine Selectively, Not Wholesale Bullet Syntax
The prompt asks whether to reuse notebook generic H2 section targeting in capture. **Reuse the selector parser and resolver, but do NOT force notebook `- #Section` syntax as the only first-level task-drawer capture syntax:**
- **Reuse directly** from `src/native/capture_language/notebook.rs`: glued `#selector` + verbatim quoted `#"..."` tokenization, the exact → whole-slug → ambiguity → near-miss resolution cascade, and `format_notebook_section_create_title` (which smartly preserves intentional mixed casing like `#API-design` → `API Design` and Title Cases all-lowercase words like `#future-work` → `Future Work`).
- **Keep distinct for task drawers:**
  1. First-level capture bullets should mirror on-disk Markdown (`decisions:capture-bullets-mirror-the-task-block`): `- **API Design**` with child bullets needs **no quotes** for multi-word or punctuated titles (`- **What's Next?**`, `- **C++ Notes**`), whereas `- #"API Design"` feels awkward in multi-line capture drafts. Keep `- #api-design` / `- #"API Design"` as a supported shorthand alongside canonical `- **API Design**`.
  2. Vault drawer catalog spelling should win when a user types an all-lowercase slug (`#api-design` matches catalog `API Design` rather than generating `Api Design`), while explicit uppercase letters in user input (`#macOS-v2`) always win verbatim.
  3. Task drawers must continue refusing reserved managed/structural names (`Tasks`, `Projects`, `Notebooks`, `Schedule Log`, `Work Log`, `Rotten Log`, `Cancel Log`, `Depends On`, `Blocks`, `Links`, etc.) and emitting `near_catalog_warning` on likely typos.

#### Adjustment 4: Be Honest About Goal #2 (Lossless Project-Note ↔ Task Conversion)
Removing ALL-CAPS solves **section header fidelity** — an essential prerequisite for lossless project-note ↔ task conversion — but an audit of all **102 active project notes** in `~/bob` shows **five other structural blockers** that still prevent lossless round-tripping today (most notably generated `### Done & Canceled` / `### Blocked` headings inside `## Tasks` on **62 of 102** projects, which currently make `splitProjectNoteForReversal` refuse reversal). Section 5 maps all five gaps so this task stays cleanly scoped while remaining 100% forward-compatible with `^task-to-project`.

---

## 2. On-Disk Representation & Empirical Vault Census

### Why `#foo` Tags Are Ruled Out (Answering Bryan's Question)

You suspected marking drawer bullets with a `#tag` (e.g., `- #drawer Title` or `- Title #drawer`) is ruled out. **Your instinct is right, with one subtle clarification worth recording:**

1. **Obsidian indexes every `#tag` on every line at the note level.** A `#drawer` tag on a task's sub-bullet enters `app.metadataCache.getFileCache(file).tags` for the entire file, floods the Tag Pane, creates a giant hub node in Graph View linking every note that contains any drawer, and matches `tag:#drawer` searches across the whole vault.
2. **Dataview indexes it into both `file.tags` and `L.tags`.** Every `LIST` or `TABLE` query over note tags or list items would need boilerplate filters excluding the drawer tag.
3. **Capture sigil collision (`decisions:capture-sigils-say-where-what-how`).** In Bob capture, glued `#` already names a section/drawer (`@file^id#drawer`) and free `#` names a task type or clock tag (`#work`, `#off`). Adding an on-disk `#tag` for drawers collides directly with capture's `#` grammar.
4. **Native rendering friction.** Obsidian turns `#tag` into a clickable pill that opens a global Search query on click, requiring brittle CSS hacks to hide or disarm it.
5. **Technical nuance on `#task` inheritance:** Obsidian's Tasks plugin parses tags **per-line**, so a `#drawer` tag on a child bullet would *not* actually get attached to the parent `- [ ] ... #task` object's own `task.tags`. Even so, the note-level Obsidian/Dataview/Graph/Search/capture pollution decisively rules out `#tag` markers.

### Empirical Vault Census (`~/bob`)

A read-only audit across all Markdown files in `/home/bryan/bob` (active notes, daily notes, project notes, notebooks, and `done/`) grounds the syntax choice in real vault data rather than guesses.

#### 1. Existing ALL-CAPS Task Drawers Across the Entire Vault: **7 Total**

| File | Line | Current Header | Owner State | Children |
|---|---:|---|---|---:|
| `needs_attn_tasks.md` | 28 | `- NOTES:` | Open | >0 |
| `sase_agent_recovery.md` | 57 | `- DONE` | Open | >0 |
| `sase_art_links.md` | 65 | `- NOTES` | Open | >0 |
| `sase_projects.md` | 24 | `- MOTIVATION` | Open | >0 |
| `sase_better_llm_disable.md` | 24 | `- OPTIONS:` | Closed (active dir) | >0 |
| `done/bob_done.md` | 378 | `- NOTES` | Archived (`done/`) | >0 |
| `done/sase_done.md` | 616 | `- NOTES` | Archived (`done/`) | >0 |

#### 2. Collision Audit Over All **1,504** Direct Note Children of `#task` Lines (43 With Sub-Children)

| Candidate Pattern | Vault Matches (of 1,504) | Breakdown / Collision Verdict |
|---|---:|---|
| Whole-line `**Bold**` | **3** (0.20%) | `done/sase_done.md:393` `**ROADMAP**` (3 children — **already an intended drawer!**); `2026/20261113.md:31` `**Note:**` (0 children — synced from Google Calendar HTML, trailing `:`); `done/sase_done.md:1420` `**Or just use task dependencies for this?!**` (0 children — **1 emphasized prose note out of 1,504 = 0.066%**). |
| Leading `**Bold**` + trailing text | **7** | e.g., `**PHONE NUMBER:** (732) 381-4200`, `**RELATED:** ...` — **0 collisions** with whole-line bold. |
| Trailing colon (`Title:`) with children | **11** | e.g., `Example blogs to subscribe to:`, `For example, we should support:` — **Disqualifies trailing colon.** |
| Whole-line `` `code` `` | **80** | Command/path notes — **Disqualifies inline code.** |
| Leading `*italic*` | **8** | Un-headered log dates (`*2026-11-07* — ...`) + Google Calendar lines — **Rules out bare `*` auto-expand.** |
| Whole-line `__Under__`, `- ## Heading`, `==Highlight==`, `[Bracket]`, `📂`/`🗂`/`§`/`▸`, leading `#tag` | **0** | Zero existing collisions, but evaluated on ergonomics, Markdown safety, and rendering below. |

#### 3. Active Project-Note H2s (102 Notes: 42 `wip`, 51 `done`, 8 `canceled`, 1 unset) & Notebook H2s

- **12 unique project-note H2 titles:** `Tasks` (101), `Notes` (51), `Future Work` (50), `Projects` (16), `Project Notes` (2), `Motivation` (2), `Cover Letter` (1), `Notebooks` (1), `Albums` (1), `Screenshots` (1), `Contents` (1), `Later Posts` (1). **Zero end with a colon.**
- **29 notebook H2 headings (22 unique):** **10 fail the current ALL-CAPS drawer charset** (e.g., `@FOOTNOTE`, `[[nj#^z-250118-1j|Union County]]`, `2024-06-25.Tue | ...`, `#work [[goog]]`, `coc.nvim`).

### On-Disk Candidate Evaluation Matrix

| Candidate | Raw Markdown Readability | Typing Speed (Vim / Mobile / CLI) | Prose Collision | Ecosystem / CommonMark Safety | `bob-cli-on` Compatible? | Verdict |
|---|---|---|---|---|---|---|
| **`- **Title**`** | Excellent — looks like a section header even with plugins off | Fast (2 taps `**` auto-pair; great on mobile & Vim) | **0.066%** (1/1,504; 0% with children) | 100% pure CommonMark; zero plugin/Obsidian/Linter issues (`strong-style` disabled in `obsidian-linter/data.json`) | **Yes** | **WINNER** |
| `- 📂 **Title**` / `- 🗂️ **Title**` | Good, matches emoji+bold managed logs (`📅 **Schedule Log**`) | Poor — non-ASCII emoji requires snippet/picker on Linux, Vim, mobile, CLI | **0%** | Safe, but adds visual emoji clutter and risks blurring *user-owned* drawers with *Bob-managed* logs | Yes | **Strongest runner-up** (reject: typing friction + blurs managed vs. user-owned) |
| `- § Title` / `- § **Title**` | Clean typographic feel; mirrors `bob notebooks list` | Poor — `§` is awkward on US keyboards, Linux Vim, and iOS | **0%** | Safe CommonMark | Yes | Runner-up (reject: non-ASCII typing friction) |
| `- ## Title` | Looks analogous to `## H2` on paper | Fast (`## `) | **0%** | **BROKEN in practice:** CM6 `ATXHeading2` folding/font-size bugs inside lists, Reading View loose-list `<p>` side effects, GitHub giant underlined `<h2>`, Pandoc/LaTeX `\subsection` pollution, and visual clash with `⌗⌗` req symbols | Yes (syntactically) | **Disqualified** |
| `- __Title__` | Identical rendered HTML to `**Title**` | Fast | **0%** | **Brittle:** CommonMark compiles `__` and `**` identically to `<strong>`; formatters, agents, and editors normalize `__` → `**`; intraword `_` pitfalls | Yes | **Rejected** |
| `- [d] Title` | Compact | Fast | **0%** | **CONFLICTS with `bob-cli-on`** (requirements own non-`#task` checkboxes); custom checkbox glyphs break outside Obsidian | **NO** | **Disqualified** |
| `- Title:` | Natural English | Fast | **High (11 real prose collisions)** | Ambiguous with ordinary lead-in bullets | Yes | **Disqualified** |
| `- ==Title==` | Non-standard | Moderate | **0%** | Non-CommonMark (fails on GitHub/Pandoc); renders as garish yellow highlighter with plugins off | Yes | **Rejected** |
| `- [drawer:: Title]` | Noisy | Slow | **0%** | Pollutes Dataview inline fields; ugly raw Markdown | Yes | **Rejected** |
| `- **Title** %%drawer%%` | Cluttered source | Slow / tedious | **0%** | Breaks manual authoring ergonomics; Obsidian comments still show while editing | Yes | **Rejected** |

**Why `- **Title**` beats every alternative decisively:**
1. **Clean semantic separation from managed logs:** Managed task logs (`📅 **Schedule Log**`, `⏱️ **Work Log**`, `🥀 **Rotten Log**`, `❌ **Cancel Log**`) carry leading emoji + bold. User drawers carry **pure bold with no emoji** (`- **Notes**`, `- **API Design**`), letting CSS inject a calm monochrome drawer icon visually while keeping the raw Markdown crisp, portable, and effortless to type anywhere (Vim, iOS, Obsidian, raw CLI).
2. **Native Obsidian Live Preview magic for free:** Obsidian already hides `**` delimiters on non-active lines and reveals `**Title**` automatically when the cursor enters the line. Styling `.cm-strong` on drawer lines avoids every custom CM6 widget and caret-reveal bug (cf. `bob-cli-on` Note #6).
3. **Graceful degradation everywhere:** On GitHub, in terminal diff views, in Vim, in Obsidian Reading View with plugins disabled, and in exported PDFs, `- **API Design**` reads cleanly as a bold sub-heading above its notes.
4. **Zero `obsidian-linter` conflict:** Confirmed by inspecting `/home/bryan/bob/.obsidian/plugins/obsidian-linter/data.json` — only `add-blank-line-after-yaml` is enabled (`strong-style` is off).

### Exact On-Disk Specification for `- **Title**`

#### 1. Direct-Child Classification Precedence (Inside a `#task` Block)
Every direct child list line of a `#task` (not inside a fenced code block) is classified in strict order:

| Priority | Category | Matcher | Example |
|---:|---|---|---|
| 1 | **Managed link / log / dep** | Existing managed classifiers (`depends on`, `blocks`, `links`, `Schedule Log`, `Work Log`, `Rotten Log`, `Cancel Log`, etc.) | `- 📅 **Schedule Log**` |
| 2 | **Requirement (`bob-cli-on`)** | Non-`#task` task checkbox (`- [ ]`, `- [x]`, `- [-]`) | `- [ ] Handle empty input` |
| 3 | **Drawer** | Non-checkbox bullet whose trimmed body satisfies `parse_drawer_title(body) -> Some(title)` | `- **API Design**` |
| 4 | **Plain note** | Everything else (including `- **Label:** inline text`, `- **Note:**`, `- *italic*`, plain bullets) | `- **Note:** check timeout` |

#### 2. Exact `parse_drawer_title(body: &str) -> Option<&str>` Rule
Given a direct non-checkbox child bullet's trimmed body `s` (after stripping `- ` / `* ` / `+ ` list marker and leading/trailing whitespace):
1. **Outer bold delimiters:** `s.len() > 4 && s.starts_with("**") && s.ends_with("**")`.
2. **Inner slice:** `inner = &s[2..s.len() - 2]`.
3. **Tight delimiter binding (CommonMark strong validity):** `inner == inner.trim()` (no leading/trailing whitespace inside `**...**`).
4. **No triple-asterisk or split bold spans:**
   - `!inner.starts_with('*') && !inner.ends_with('*')` (rejects `***bold italic***` and `****`).
   - `!inner.contains("**")` (rejects `- **Step 1** then **Step 2**`).
5. **Valid title text (`is_valid_drawer_title_text(inner)`):**
   - Single-line (`!inner.contains('\n') && !inner.contains('\r')`).
   - Contains at least one Unicode alphanumeric character (`inner.chars().any(char::is_alphanumeric)`).
   - **No trailing colon** (`!inner.ends_with(':')`): keeps drawer titles identical to H2 section headings (0 of 12 project H2s end in `:`), eliminates the vault's Google Calendar `- **Note:**` false positive automatically, and lets users write bold lead-in labels like `- **TL;DR:**` without accidentally opening a drawer. Internal colons (e.g., `- **Phase 1: Auth**`) remain fully valid.
   - No embedded block-id anchor or task tag? *(Optional guard: disallow `#task` inside `inner` so a bolded task fragment is never misread.)*
6. **Not reserved:** `!is_reserved_drawer_key(&drawer_key(inner))`.

#### 3. Case-Insensitive Identity Key (`drawer_key`) & Reserved Keys
- **`drawer_key(title: &str) -> String`:** Collapse internal whitespace (`normalize_task_text`) and uppercase with Unicode-aware `.to_uppercase()` (upgrading from `.to_ascii_uppercase()`). Two drawers on the same task with keys matching `drawer_key` (e.g., `**API Design**` and `**api design**`) represent the same logical drawer.
- **Canonical default Notes drawer:**
  - `NOTES_TITLE = "Notes"` (rendered on disk as `- **Notes**` on a normal task, and `## Notes` on a project note).
  - `NOTES_KEY = "NOTES"` (used for case-insensitive matching against `drawer_key(title)`).
  - Updating `src/native/task_block_layout.rs:64` and `src/native/task_tidy/mod.rs:143` (and the JS twins `TASK_BLOCK_NOTES_TITLE` / `TASK_BLOCK_NOTES_KEY`) cleanly splits display spelling from comparison key!
- **Expand `reserved_drawer_keys()` (`src/native/capture_drawers.rs:95-117`):** Keep deriving managed log/dep/relation labels dynamically, keep `"TASKS"`, and also add Bob's structural project-note catalog H2 constants (`"PROJECTS"`, `"NOTEBOOKS"`, plus `"SUB-PROJECTS"` / `"SUB-PROJECT"` / `"DEPENDENCIES"` / `"BLOCKING"` if used as structural headings) so no user drawer can ever collide with a Bob-owned H2 during promotion.

#### 4. Three Critical Safety Fixes Uncovered in the Codebase
1. **Decouple `is_pomodoro_name` from `is_drawer_title` (`src/native/capture_drawers.rs:1596-1673`):** Pomodoro names (`BOB+SASE`, `C++`, `WORK`) MUST stay ALL-CAPS + `+`. Split `is_pomodoro_name` into its own standalone predicate in `capture_pomodoros.rs` (or keep it isolated in `capture_drawers.rs` without sharing `is_drawer_title_first`), freeing drawers to accept mixed case, `+`, Unicode, and punctuation (`- **C++ Notes**`, `- **Q&A**`, `- **Phase 1: Auth**`).
2. **Fix Google Calendar escaping — critical bug prevention! (`src/native/gcal/description/bullets.rs:140, 639, 787`):**
   Today, line 140 checks `else if capture_drawers::is_drawer_title(body_text.trim())` and wraps the line in `**...**` specifically to *prevent* an ALL-CAPS imported bullet from becoming a drawer! Under `- **Title**`, that exact line would **manufacture drawers** out of Google Calendar descriptions.
   - **Fix:** Replace that branch with `else if capture_drawers::parse_drawer_title(body_text.trim()).is_some()` and neutralize it with single-asterisk italicization `*...*` (stripping outer `**` and wrapping in `*...*`, matching line 139's existing italicization for managed lines). Also review `src/native/task_text_escape.rs` for any analogous wrapper.
3. **Escape hatch when a user truly wants a bold plain note:** A user who genuinely wants a non-drawer bold bullet has three effortless options: add punctuation/text outside `**...**` (`- **Important:** check X`, `- **Wait** — double check`), italicize (`- *Important*`), or escape (`- \*\*Important\*\*`). Given the 0.066% historical rate (1 line in 1,504), this virtually never occurs in daily use.

---

## 3. Visual Rendering & Interaction Design

> *"Regardless of what we store on disk, we should make sure to render these drawer sub-bullets in a distinct (and easily recognizable) way. Make sure you design this feature so it is intuitive, reliable, and (last but not least) beautiful!"*

### Design Philosophy: Calm Architectural Container vs. Actionable Requirement

A task block in Bob now contains four distinct child species. Each should have an unmistakable visual silhouette at a 200ms glance:

| Child Kind | On-Disk Form | Visual Role | Visual Silhouette |
|---|---|---|---|
| **Managed log / link** | `- 📅 **Schedule Log**` | System audit trail | Leading color emoji + muted label |
| **Requirement** (`bob-cli-on`) | `- [ ] Ship CLI flag` | **Actionable scope** (high urgency/focus) | Distinctive `⌗⌗` checkbox glyph + owner-type accent tint |
| **Drawer** (this design) | `- **API Design**` | **Structural container** (calm organizer) | Architectural **section-tab pill** with monochrome tray glyph, **true case**, subtle left accent edge, quiet tabular child count |
| **Plain note** | `- Check timeout value` | Freeform prose | Standard list bullet & body ink |

### Visual Mockup (Obsidian Live Preview & Reading View)

```text
- [ ] Redesign Bob task drawers #task #bob ^no-all-caps-for-drawers
    ⌗⌗  Support non-all-caps drawer titles
    ⌗⌗  Reuse notebook H2 selector resolution in capture
    ┌─ ▣ API Design  3 ───────────────────┐    ← Section-tab pill (true case, tray icon, tabular count)
    │ • Keep drawer_key case-insensitive       ← Subtle vertical guide rail tying children to the drawer
    │ • Reject trailing colons on titles
    │ • Neutralize gcal bold lines with *...*
    └─────────────────────────────────────┘
    ┌─ ▣ Open Questions  ┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┐    ← Empty drawer: subtle dashed outline, no count badge
    • Regular plain note bullet (unchanged)
```

When the cursor enters the drawer header line in Live Preview (`.cm-active`), Obsidian's native formatting reveal automatically exposes the raw Markdown delimiters and hides the count whisper so editing feels 100% honest and glitch-free:

```text
  - **API Design|**                            ← Caret active: native ** reveal, calm highlight, zero widget jump
```

### Architecture in `bob-ledger-tools` (Zero Extra DOM Nodes)

Follow the exact **attribute-only architecture** established by `bob-ledger-tools/src/264-plugin-task-reqs.js` and `bob-ledger-tools/styles.css`:

1. **Live Preview (CM6 `ViewPlugin`):**
   - Scan task blocks using the shared JS drawer classifier (from the unified task-reqs twin module — see bead `bob-cli-p9`).
   - Apply `Decoration.line({ attributes })` to every drawer header line:
     - `data-bob-drawer="true"`
     - `data-bob-drawer-state="populated"` or `"empty"`
     - `data-bob-drawer-count="<N>"` (direct child bullet count, `"0"` when empty)
     - `data-bob-drawer-owner-state="open"` | `"done"` | `"cancelled"`
     - `title="Drawer · “API Design” in “Redesign Bob task drawers” · 3 notes"` (matches the rich hover tooltip language of `264-plugin-task-reqs.js`)
   - Optionally apply `Decoration.line({ attributes: { "data-bob-drawer-child": "true" } })` to descendant lines inside a populated drawer so a whisper-thin `1px` vertical guide rail visually anchors the drawer's contents without shifting text alignment.
2. **Reading View (`registerMarkdownPostProcessor`):**
   - Walk `li` elements under `#task` items, match drawer `li` nodes whose first block contains solely a `<strong>` matching `parseDrawerTitle`, and stamp the exact same `data-bob-drawer*` attributes onto the `<li>`.
3. **Why Attribute-Only Beats CM6 `Decoration.replace` Widgets:**
   - **Native caret-adjacent `**` reveal works out of the box** — zero custom cursor math, zero IME/Vim `ci*` / `f*` / visual-selection bugs, zero scroll-height jitter.
   - **Zero DOM injection** — Obsidian's list folding triangle (`collapse-indicator`) continues working natively on the drawer bullet, letting Bryan fold/unfold any drawer cleanly!

### Concrete CSS Specification (Light & Dark Theme Native)

```css
/* === Bob Task Drawers (Live Preview + Reading View) === */

:root {
  --bob-drawer-ink: color-mix(in srgb, var(--text-normal) 86%, var(--interactive-accent) 14%);
  --bob-drawer-accent: color-mix(in srgb, var(--text-muted) 65%, var(--interactive-accent) 35%);
  --bob-drawer-bg: color-mix(in srgb, var(--bob-drawer-accent) 9%, transparent);
  --bob-drawer-border: color-mix(in srgb, var(--bob-drawer-accent) 26%, transparent);
  --bob-drawer-count-ink: var(--text-faint);
}

/* Section-tab pill applied directly to the bold span on non-active Live Preview lines
   and Reading View drawer headers — preserving exact capitalization! */
.cm-line.HyperMD-list-line[data-bob-drawer="true"]:not(.cm-active) .cm-strong,
.markdown-rendered li[data-bob-drawer="true"] > strong:first-of-type,
.markdown-rendered li[data-bob-drawer="true"] > p:first-child > strong:only-child {
  display: inline-flex;
  align-items: center;
  gap: 0.42em;
  padding: 0.08em 0.55em 0.08em 0.42em;
  border-radius: 3px 6px 6px 3px;              /* Subtle filing-tab asymmetry */
  border: 1px solid var(--bob-drawer-border);
  border-left: 2.5px solid var(--bob-drawer-accent);
  background: var(--bob-drawer-bg);
  color: var(--bob-drawer-ink);
  font-family: var(--font-interface);
  font-size: 0.89em;
  font-weight: 620;
  letter-spacing: 0.01em;
  line-height: 1.35;
  text-transform: none;                        /* CRITICAL: never alter real casing */
  font-variant-caps: normal;
  vertical-align: baseline;
}

/* Crisp 14x14 monochrome tray/drawer glyph via CSS mask (inherits theme color automatically) */
.cm-line.HyperMD-list-line[data-bob-drawer="true"]:not(.cm-active) .cm-strong::before,
.markdown-rendered li[data-bob-drawer="true"] > strong:first-of-type::before,
.markdown-rendered li[data-bob-drawer="true"] > p:first-child > strong:only-child::before {
  content: "";
  display: inline-block;
  width: 0.92em;
  height: 0.92em;
  flex-shrink: 0;
  background-color: var(--bob-drawer-accent);
  -webkit-mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16' fill='none' stroke='black' stroke-width='1.5' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect x='2' y='2.5' width='12' height='11' rx='2'/%3E%3Cpath d='M2 8.5h3.5l1 1.5h3l1-1.5H14'/%3E%3C/svg%3E");
  mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16' fill='none' stroke='black' stroke-width='1.5' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect x='2' y='2.5' width='12' height='11' rx='2'/%3E%3Cpath d='M2 8.5h3.5l1 1.5h3l1-1.5H14'/%3E%3C/svg%3E");
  -webkit-mask-size: contain;
  mask-size: contain;
  -webkit-mask-repeat: no-repeat;
  mask-repeat: no-repeat;
}

/* Quiet tabular child-count whisper when populated (hidden while editing) */
.cm-line.HyperMD-list-line[data-bob-drawer="true"][data-bob-drawer-state="populated"]:not(.cm-active) .cm-strong::after,
.markdown-rendered li[data-bob-drawer="true"][data-bob-drawer-state="populated"] > strong:first-of-type::after,
.markdown-rendered li[data-bob-drawer="true"][data-bob-drawer-state="populated"] > p:first-child > strong:only-child::after {
  content: attr(data-bob-drawer-count);        /* Or inherited via CSS var --bob-drawer-count */
  margin-left: 0.15em;
  padding: 0 0.35em;
  border-radius: 999px;
  background: color-mix(in srgb, var(--bob-drawer-accent) 13%, transparent);
  color: var(--bob-drawer-count-ink);
  font-size: 0.78em;
  font-weight: 500;
  font-variant-numeric: tabular-nums;
  line-height: 1.4;
}

/* Note: Because attr() reads the element's own attribute (the .cm-strong span, not .cm-line),
   pass count via inline style var `--bob-drawer-count: "3"` on Decoration.line so
   `content: var(--bob-drawer-count)` works cleanly across both CM6 and Reading View! */

/* Empty drawer: dashed border, gentler presence */
.cm-line.HyperMD-list-line[data-bob-drawer="true"][data-bob-drawer-state="empty"]:not(.cm-active) .cm-strong,
.markdown-rendered li[data-bob-drawer="true"][data-bob-drawer-state="empty"] > strong:first-of-type,
.markdown-rendered li[data-bob-drawer="true"][data-bob-drawer-state="empty"] > p:first-child > strong:only-child {
  border-style: dashed;
  border-left-style: solid;
  background: transparent;
  opacity: 0.78;
}

/* Active (editing) line: calm subtle tint, native ** visible */
.cm-line.HyperMD-list-line[data-bob-drawer="true"].cm-active .cm-strong {
  color: var(--bob-drawer-ink);
  font-family: var(--font-interface);
  font-weight: 620;
}

/* Closed / canceled owner task: desaturated, quiet */
.cm-line.HyperMD-list-line[data-bob-drawer="true"][data-bob-drawer-owner-state="done"]:not(.cm-active) .cm-strong,
.cm-line.HyperMD-list-line[data-bob-drawer="true"][data-bob-drawer-owner-state="cancelled"]:not(.cm-active) .cm-strong,
.markdown-rendered li[data-bob-drawer="true"][data-bob-drawer-owner-state="done"] > strong:first-of-type,
.markdown-rendered li[data-bob-drawer="true"][data-bob-drawer-owner-state="cancelled"] > strong:first-of-type {
  opacity: 0.55;
  filter: saturate(0.4);
}
```

> **Implementation detail:** In CSS, `content: attr(data-bob-drawer-count)` reads attributes from the `.cm-strong` span itself rather than its parent `.cm-line`. Setting `--bob-drawer-count: "3"` on the `Decoration.line` `style` attribute (and on Reading View's `<li>`) and reading `content: var(--bob-drawer-count)` on `.cm-strong::after` works identically in both CM6 and Reading View with zero extra decorations!

### Bob Mac Capture Styling (`bob-mac-capture`)

Per `decisions:mac-capture-is-a-thin-client`, Bob Mac Capture never parses grammar itself — it renders spans and previews returned by `bob capture-parse` / `bob capture-complete`.
- `Sources/CaptureCore/CompletionRowContent.swift:84` already styles `"drawer"` and `"drawer_bullet"` completions with the `.section` visual token, and `CaptureSubBulletPresentation.swift` already styles sub-bullet spans from `bob capture-parse`.
- **Two lightweight, high-polish Mac updates:**
  1. Emit `drawer_delimiter` (or flag the outer `**` offsets inside `drawer_bullet` spans) from `bob capture-parse` so the Mac composer renders `**` at subtle dimmed opacity while keeping the true-cased drawer title in crisp `.section` accent semibold.
  2. Render drawer headers inside the Mac live-preview card using a matching section-tab capsule with the SF Symbol `tray` (`11pt`, muted accent) and true capitalization — visually uniting Obsidian and Bob Mac Capture into one cohesive design language.

---

## 4. Capture Syntax & Notebook H2 Resolver Reuse

### Current Capture Surface Audit

Today, four places in `bob-cli` handle drawers or section bullets, with two separate implementations:
1. **Route drawer selector (`@file^id#drawer`):** `src/native/capture_language/tokens.rs` + `src/native/capture_drawers.rs` — requires ASCII-only lowercase slugs (`is_drawer_slug`) or ALL-CAPS/quoted literals (`normalize_drawer_literal` uppercases everything!).
2. **Task first-level sub-bullets (`- DRAWER` / `- #slug`):** `src/native/capture_language/drawer_bullet.rs` + `editor_parse.rs` + `capture_complete/drawers.rs` — detects ALL-CAPS headers via `is_all_caps_drawer_title`, and inserts `ALL CAPS\n  - ` on Tab completion.
3. **Notebook H2 targeting (`@nb#section`, `- #Section`, `@parent^id@ %n`):** `src/native/capture_language/notebook.rs` + `section_bullet.rs` — already supports arbitrary mixed-case unquoted selectors, verbatim quoted `#"..."` selectors, exact → whole-slug → ambiguity → near-miss resolution, and smart creation casing (`format_notebook_section_create_title`: keeps mixed-case words as typed, Title Cases all-lowercase hyphen/underscore words!).
4. **Project & Record section bullets (`@parent^id@ %p`, records):** `src/native/capture_project_note.rs:236` (`is_project_section_title` delegates to `is_drawer_title`), `src/native/capture_language/section_bullet.rs:440,626`, `src/native/capture_language/record.rs:851`, and `src/native/records/render.rs:239` — all currently rely on ALL-CAPS detection and then lossily re-case via `format_project_section_title`.

### Architecture: Extract Shared Section Selector Core, Keep Drawer Policy Layered On Top

Extract a shared module — e.g. `src/native/capture_language/section_selector.rs` — from `notebook.rs` and share it across **both** notebooks and task drawers:

| Layer | Shared (`section_selector.rs`) | Notebook-Specific (`notebook.rs`) | Drawer-Specific (`capture_drawers.rs` / `drawer_bullet.rs`) |
|---|---|---|---|
| **Glued `#selector` parsing** | Arbitrary non-whitespace unquoted (`#API-design`, `#C++`, `#notes`) + verbatim quoted (`#"Phase 1: Auth"`, `#"What's Next?"`) with `\"` / `\\` escapes | Used on `@nb#section` and `- #Section` | Used on `@file^id#drawer` and `- #drawer` shorthand |
| **Target resolution cascade** | 1. Exact case-insensitive match → 2. Whole-slug match → 3. Ambiguity error listing candidates → 4. Create new | Targets existing `## H2` headings in the notebook | Targets existing `- **Title**` drawers on the task (or `## H2` sections on a `^prj` project note) |
| **Create-title smart casing** | `format_section_create_title`: quoted `#"..."` = verbatim; unquoted = hyphen/underscore → space, preserve any word containing an uppercase letter (`API-design` → `API Design`, `macOS-setup` → `macOS Setup`, `iOS` → `iOS`), Title Case all-lowercase words (`future-work` → `Future Work`) | Direct output on new notebook H2 | **Layered rule:** If the selector was unquoted *and* all-lowercase (`#api-design`, `#qa`), check the **vault drawer catalog** first so `#api-design` adopts existing catalog spelling `API Design` (or `Q&A`) before falling back to `format_section_create_title`! If the user typed any uppercase letter or quotes (`#API-v2`, `#"C++ Notes"`), honor their exact casing verbatim. |
| **Validation & warnings** | Non-empty, single-line, contains alphanumeric | Disallows notebook-specific structural H2s if any | Refuses `reserved_drawer_keys()`, rejects trailing `:`, emits `near_catalog_warning` on close typos against vault catalog |

### First-Level Capture Bullet Syntax (`decisions:capture-bullets-mirror-the-task-block`)

Under any task (new or targeted), project capture (`%p`), notebook capture (`%n`), or record capture, **both** of these first-level forms work seamlessly:

#### 1. Canonical Authored Form (and Tab-Completion Insertion): `- **Title**`
```markdown
@bob^no-all-caps-for-drawers
- **API Design**
  - Reuse notebook selector resolver
  - Preserve explicit mixed case
- **Q&A**
  - Does trailing colon count as a drawer? No.
```
- Mirrors on-disk Markdown 1-to-1 (`decisions:capture-bullets-mirror-the-task-block`).
- Requires **zero quotes** for multi-word titles, punctuation, or symbols (`- **Phase 1: Auth**`, `- **What's Next?**`, `- **C++ Notes**`).
- **Tab completion (`capture_complete/drawers.rs`):** Typing `- #ap<Tab>` or `- **ap<Tab>` completes from the true-cased drawer catalog and inserts **`**API Design**\n  - `** (matching the task block directly, rather than noisy `#"API Design"`).
- **Childless `- **Title**` on a task capture:** Previously, `- ALLCAPS` without children was treated as a plain note *only* to avoid false positives on uppercase words like `- TODO` or `- WIP`. With explicit `**Title**`, a childless `- **Open Questions**` under a task can cleanly create an empty drawer (matching on-disk recognition!). *(If Bryan prefers requiring at least one child on capture to prevent accidental empty drawers, keep the existing child-required rule in capture and document that `- **Title**` creates a drawer only with children — both options are trivial to toggle, though allowing childless `- **Title**` under a task makes capture and on-disk 100% consistent.)*

#### 2. Shorthand Selector Form (Consistent With Notebooks): `- #selector` / `- #"Quoted Title"`
```markdown
@bob^no-all-caps-for-drawers
- #api-design
  - Reuse notebook selector resolver
- #"Phase 1: Auth"
  - Keep internal colons valid
```
- Resolves via the exact same shared selector engine + catalog spelling lookup.
- On disk, commits as `- **API Design**` and `- **Phase 1: Auth**` (on a task) or `## API Design` and `## Phase 1: Auth` (on a project note, notebook, or record).
- On a route (`@bob^no-all-caps-for-drawers#api-design` or `@bob^no-all-caps-for-drawers#"API Design"`), targets/creates the exact same drawer.

### Related CLI & Capture Touchpoints to Update Together
1. **`GRAMMAR_REVISION` (`src/native/capture_language/mod.rs:68`):** Bump **29 → 30** and document bold drawer bullets + shared `#selector` / `#"..."` syntax.
2. **`DRAWER_CATALOG_VERSION` (`src/native/capture_drawers.rs:161`):** Bump **2 → 3**. Crucially, **stop uppercasing project-note H2s when indexing the catalog**! Today `src/native/capture_drawers.rs` uppercases H2s into the catalog; storing their true spelling means the existing 102 project notes immediately seed the vault catalog with `Notes`, `Future Work`, `Motivation`, `Project Notes`, `Cover Letter`, etc. On catalog spelling conflict across files (e.g., `Api Design` in 1 note vs. `API Design` in 4 notes), prefer the most frequent spelling (breaking ties by most recently modified or lexicographically).
3. **`bob task rename-drawer` (`src/native/task_drawer_rename/mod.rs`):** Allow **case-only retitling** (e.g., `bob task rename-drawer "Api Design" "API Design"`), which currently errors because `old_key == new_key`! Also update `Lookalike::Bullet` (line 770) to check `parse_drawer_title` and write `- **<new_title>**`.
4. **`bob task tidy` (`src/native/task_tidy/mod.rs:143`) & `bob task merge` (`src/native/task_merge/containers.rs`):** Emit `- **Notes**` instead of `- NOTES` (and update `content_preserved` in `task_tidy/mod.rs:143` to expect `- **Notes**`).
5. **Project capture (`%p`), Notebook capture (`%n`), and Records (`capture_language/record.rs:851`, `records/render.rs:239`, `section_bullet.rs:440,626`):** Accept `- **Section Title**` (verbatim, bypassing lossy `format_project_section_title`) alongside `- #section`. For `%p` / records, `## API Design` is now written with its exact intended capitalization!

---

## 5. Stepping Stone Toward Lossless Project-Note ↔ Task Conversion

### What `- **Title**` Unlocks Immediately

With `- **Title**` drawers, section headers achieve **exact 1-to-1 lossless round-tripping** between a task block and a project note:

```markdown
<!-- Task representation -->
- [ ] Build export pipeline #task #bob ^export-pipe
	- [ ] Support CSV output
	- [ ] Add streaming tests
	- **Notes**
		- Benchmark on 10k rows
	- **API Design**
		- Version the JSON schema
	- **Future Work**
		- Add Parquet writer
```

↕ *(Promote ↔ Demote — zero casing or punctuation loss!)*

```markdown
## Tasks
- [ ] Support CSV output #task #bob
- [ ] Add streaming tests #task #bob

## Notes
- Benchmark on 10k rows

## API Design
- Version the JSON schema

## Future Work
- Add Parquet writer
```

- `formatProjectSectionTitle` (`bob-navigation-hotkeys/src/100-yank-and-paths.js:851-870`) no longer needs to destroy acronyms (`API DESIGN` → `Api Design`). `parseProjectSectionBulletTitle` simply unwraps `- **Title**` verbatim!
- `NOTES` ↔ `## Notes` is no longer a special-case casing hack — both sides are `Notes`.
- `## Q&A`, `## C++ Notes`, `## Phase 1: Auth`, `## macOS Setup` survive arbitrary promote/demote cycles untouched.

### Honest Map of the 5 Remaining Gaps (Audit of All 102 Active Project Notes)

Removing ALL-CAPS is necessary but **not sufficient** on its own for lossless project-note ↔ task conversion (`^task-to-project`). Auditing all 102 active project notes in `~/bob` reveals the exact remaining blockers so they are not surprises later:

| # | Remaining Gap | Vault Evidence (102 Active Project Notes) | Impact on `- **Title**` Design |
|---:|---|---|---|
| 1 | **Generated `###` status-group headings inside `## Tasks`** | `### Done & Canceled` (**62** notes), `### Blocked` (**39**), `### Next & In Progress` (**5**). Today `splitProjectNoteForReversal` (`210-rename-and-line-context.js:697`) rejects any non-list line in `## Tasks`, blocking reversal on **>60% of real projects**. | **None.** Reversal simply needs to treat Bob-generated status-group H3s as regenerable layout metadata rather than content. |
| 2 | **`## Tasks` ↔ Requirement checklists (`bob-cli-on`)** | Project tasks carry `#task`, `#now`, dates, deps, `^id`, and their own drawers/notes; requirements are simpler checkboxes. `bob-cli-on.12` handles promotion (`req → #task`), while demotion (`#task → req` or micro-task) belongs to `^micro-tasks` / `^task-to-project`. | **None.** Drawers are cleanly disjoint from requirements. |
| 3 | **Extra project-note YAML frontmatter** | Active project notes carry non-default keys: `theme` (2), `project_name_aliases` (1), `root` (1), `color` (1), `aliases` (1), `tags` (1), `source` (1), `id` (1). | **None.** Task-level inline fields or metadata drawers can be designed later without changing `- **Title**`. |
| 4 | **Non-list prose, code blocks, and custom `###` headings under H2s** | **2** project notes have non-status H3s (`### Future Work`, `### Option A`); **2** have prose paragraphs under custom H2s. | **Forward-compatible.** `- **Title**` cleanly hosts nested indented bullets; custom H3s inside an H2 could map cleanly to nested `- **Sub-Section**` drawers later if ever desired (currently drawers are direct-child only). |
| 5 | **Structural catalogs (`## Projects`, `## Notebooks`) & child notes** | **16** project notes have `## Projects`, **1** has `## Notebooks`. | **Protected.** Reserving `PROJECTS` and `NOTEBOOKS` in `reserved_drawer_keys()` ensures user drawers never collide with them, leaving them open for `^tasks-parent-projects`. |

---

## 6. Coordination & Non-Conflict With WIP `bob-cli-on`

### Current State of `bob-cli-on` (*Task requirements (reqs)*)

`bob-cli-on` is **13/17 phases closed**. Only four phases remain `IN_PROGRESS`:
- `bob-cli-on.11` — Obsidian successor card & carry-now (`bob-plugins`)
- `bob-cli-on.12` — Promotion maps requirements to tasks and notes to notes (`bob-plugins`: `100-yank-and-paths.js`, `110-project-seed.js`, `667-plugin-project-promotion.js`, `docs/projects.md`)
- `bob-cli-on.15` — Mac Pull-In card (`bob-mac-capture`)
- `bob-cli-on.17` — Memory records (`decisions:task-reqs-are-met-with-their-task`, `decisions:capture-bullets-mirror-the-task-block`, `glossary:task-drawer`, `glossary:task-requirement`)

### Why There Is Zero Semantic Conflict

1. **Disjoint syntax:** Requirements are non-`#task` checkboxes (`- [ ]`, `- [x]`, `- [-]`); drawers are non-checkbox bullets (`- **Title**`). Neither can ever be misclassified as the other.
2. **Case-folded `NOTES` matching is already in place:** `src/native/task_block_layout.rs:174` already checks `drawer_key(title) == NOTES_TITLE`, and `src/native/task_reqs.rs:283` delegates directly to `capture_drawers::is_drawer_title(title)`. Switching to `parse_drawer_title` and splitting `NOTES_TITLE = "Notes"` / `NOTES_KEY = "NOTES"` slots directly into the existing layout engine.

### Important Live Bug in `bob-cli-on` to Fix Alongside This Work

Inspection of `src/native/task_block_layout.rs` (and `bob-plugins` `696-task-block-layout-twin.js:437`) revealed an active bug on req-owning `^prj` tasks:
- `note_home` calls `capture_drawers::drawers` (which scans only indented bullet drawers, ignoring `project_h2_drawers`), so when a req-owning `^prj` task already has `## Notes`, `ensure_notes_drawer` fails to find it, appends a brand-new `## NOTES` (ALL-CAPS!) at EOF, and files tab-indented bullets under it — duplicating `## NOTES` on every capture.
- **Clean combined fix:** Route `^prj` `note_home` through `project_h2_drawers` + `h2_insert_position` with column-0 indentation, and emit `## Notes` (using `NOTES_TITLE = "Notes"` matched via `NOTES_KEY = "NOTES"`).

### Sequencing & Twin-Parity Checklist

1. **Wait for `bob-cli-on.12` and `.17` to close** before opening PRs that touch `110-project-seed.js`, `667-plugin-project-promotion.js`, and `glossary:task-drawer` (eliminates merge churn on hot files).
2. **Update all byte-identical JS twin copies together** (`bob-plugins` enforces identity via `scripts/test-task-reqs-twin-copies.cjs`):
   - `bob-navigation-hotkeys/src/{694,696,697,698}-task-*`
   - `task-status-cycler/src/{194,196,197,198}-task-*`
   - `block-id-prompt/src/165-task-reqs-lines-twin.js`
   - `bob-ledger-tools/src/139-task-reqs.js` (display-only copy; tracked for unification in `bob-cli-p9` — ideal to either unify or update in lockstep)
3. **Watch out for the `task-split` unwrapping trap:** `bob-navigation-hotkeys/src/257-task-split-apply.js:203-207` currently extracts `parentDrawer` via raw `parentBody.trim()` instead of unwrapping the drawer title! Without updating that line to call `parseDrawerTitle(parentBody)`, split picker headers would display `"Split **Notes** into tasks"` instead of `"Split Notes into tasks"`.
4. **Update cross-repo shared vector suites:** `tests/fixtures/task_reqs/{vectors,layout,writes}.json` (RQ/RL/RW) and `tests/fixtures/task_split/vectors.json` (SP32–SP50) so Rust and JS stay 100% locked together.

---

## 7. Recommended Solution & Phased Implementation Blueprint

### Final Recommendation Summary

Adopt **whole-line bold `- **Title**`** as the sole on-disk representation for task drawers, pair it with an **attribute-only architectural section-tab pill** in `bob-ledger-tools`, **share `notebook.rs`'s selector/resolver/smart-casing engine** in capture while keeping `- **Title**` as the canonical first-level capture bullet (with `- #selector` / `- #"..."` shorthand), refine editor ergonomics around **native `**` + Smart `Enter` exit + atomic `Backspace` + optional `- *` + `Space`**, and execute a **clean one-shot vault migration** of the 7 existing ALL-CAPS drawers right after `bob-cli-on` closes.

### Phased Implementation Plan

#### Phase 1 — Core Parser, Layout, & Safety Foundations (`bob-cli`)
1. Introduce `parse_drawer_title(body: &str) -> Option<&str>` and `is_valid_drawer_title_text(title: &str) -> bool` in `src/native/capture_drawers.rs`; decouple `is_pomodoro_name` completely.
2. Split `NOTES_TITLE = "Notes"` and `NOTES_KEY = "NOTES"` in `task_block_layout.rs`; fix the `^prj` `note_home` `## Notes` bug; update `task_tidy/mod.rs` and `task_merge/containers.rs` to emit `- **Notes**`.
3. Expand `reserved_drawer_keys()` to include Bob's structural project-note H2 constants (`PROJECTS`, `NOTEBOOKS`).
4. Fix `src/native/gcal/description/bullets.rs:140` (neutralize imported bold-only lines as `*...*` instead of wrapping ALL-CAPS in `**...**`).
5. Bump `DRAWER_CATALOG_VERSION` 2 → 3; preserve true casing from both `- **Title**` drawers and project-note `## H2` headings in the catalog.
6. Update `bob task rename-drawer` to support case-only retitling (`Api Design` → `API Design`) and emit `- **Title**`.

#### Phase 2 — Capture Language & Notebook Selector Reuse (`bob-cli`)
1. Extract `src/native/capture_language/section_selector.rs` from `notebook.rs` (glued `#selector` + quoted `#"..."`, shared exact→slug→ambiguity resolver, smart-casing creator).
2. Wire task drawer routes (`@file^id#drawer`), first-level drawer bullets (`- **Title**` canonical + `- #selector` / `- #"..."` shorthand), project capture (`%p`), notebook creation (`%n`), and record capture (`record.rs` / `records/render.rs`) onto the new rules, adding vault catalog spelling preference for all-lowercase drawer slugs.
3. Update `capture_complete/drawers.rs` to offer true-cased drawer names and insert `**Title**\n  - `.
4. Bump `GRAMMAR_REVISION` 29 → 30 and update `tests/fixtures/task_reqs/*` and `tests/fixtures/task_split/*`.

#### Phase 3 — Obsidian Twins, Promotion, Rendering, & Ergonomics (`bob-plugins`)
1. Update all shared JS twins (`694`/`696`/`697`/`698`, `194`/`196`/`197`/`198`, `165`, `139`), fix `257-task-split-apply.js:203-207` `parentDrawer` unwrapping, and simplify `parseProjectSectionBulletTitle` (`100-yank-and-paths.js:863`) to return verbatim unwrapped titles.
2. Implement the **attribute-only section-tab pill** renderer in `bob-ledger-tools` (CM6 `Decoration.line` + Reading View post-processor + CSS with SVG tray mask, preserved casing, tabular count whisper via `--bob-drawer-count`, dashed empty state, closed-owner fading, and subtle child guide rail).
3. Implement the **editor typing kit** (`task-status-cycler` or `bob-navigation-hotkeys`): Smart `Enter` inside `- **Title|**` → indented child `- |`, atomic `Backspace` on `- **|**`, optional `- *` + `Space` → `- **<cursor>**`, and Toggle Drawer command.
4. Run `scripts/test-task-reqs-twin-copies.cjs` and full plugin test suites, then deploy via `bob plugins sync`.

#### Phase 4 — Bob Mac Capture Polish (`bob-mac-capture`)
1. Consume `GRAMMAR_REVISION = 30` spans from `bob capture-parse`; dim `**` delimiters on unfocused `drawer_bullet` spans and render true-cased drawer capsules with the `tray` SF Symbol in live preview cards.
2. Gate via `scripts/dev/macos-ci-check` and watch exact-SHA macOS CI to green.

#### Phase 5 — Previewed One-Shot Vault Migration (`~/bob`)
Migrate the 7 existing ALL-CAPS drawers with a dry-run diff preview for Bryan's approval:
- `needs_attn_tasks.md:28`: `- NOTES:` → `- **Notes**`
- `sase_art_links.md:65`: `- NOTES` → `- **Notes**`
- `sase_projects.md:24`: `- MOTIVATION` → `- **Motivation**`
- `sase_agent_recovery.md:57`: `- DONE` → `- **Done**` *(confirm intent with Bryan)*
- `sase_better_llm_disable.md:24`: `- OPTIONS:` → `- **Options**`
- `done/bob_done.md:378`: `- NOTES` → `- **Notes**`
- `done/sase_done.md:616`: `- NOTES` → `- **Notes**`

#### Phase 6 — Docs & SASE Memory
1. Update `docs/reference/capture-syntax.md`, `docs/capture.md`, `docs/projects.md`, and `docs/task-requirements.md`.
2. Record a new accepted decision (e.g., `decisions:drawers-are-bold-bullets`), mark `decisions:capture-bullets-mirror-the-task-block` as partly superseded where it specifies ALL-CAPS drawers, and update `glossary:task-drawer`.
