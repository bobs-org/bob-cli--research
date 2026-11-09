# Architectural Design and Vault Archaeology: The "Notebook" Note Type (`__gem`)

**Researcher:** `research.3x.gem`  
**Date:** November 9, 2026  
**Target Repository:** `bob-cli` (with linked `bob-plugins` and `bob-mac-capture`)  
**Artifact Classification:** Research Report & Design Specification  

---

## 1. Executive Summary & Core Verdict

The proposal to introduce a new **`notebook`** note type (`type: "[[notebook]]"`) into the Bob ecosystem is an outstanding and necessary evolution of Bryan's personal knowledge management architecture.

### Why This Is Needed
Across Bryan's Obsidian vault (`~/bob/`), notes currently fall into a few rigid categories:
1. **Area Notes (`[[area]]`)**: Ongoing spheres of responsibility (e.g. `cash.md`, `dev.md`, `job.md`). These are GTD operational centers hosting active task backlogs under `## Tasks`.
2. **Project Notes (`[[project]]`)**: Finite outcomes defined by a `^prj` completion task, a lifecycle status (`wip`, `done`, `canceled`), and project-specific tasks.
3. **Reference Notes (`[[ref]]`)**: Externally sourced reading materials (articles, books, papers, podcasts) linked to PDFs, media, and source digests.
4. **Daily Notes (`[[day]]`)**: Ephemeral daily logs, Pomodoro ledgers, and GTD review footers.
5. **Records (`[[restaurant]]`, `[[show]]`, etc.)**: Structured YAML entity databases.

Notice what is missing: **first-class containers for structured, hierarchical, non-task knowledge**. 

Our vault archaeology reveals that over **488 markdown files** in `~/bob/` lack a `type:` frontmatter field entirely. Among those, **393 files are pure note bullet collections** (0 tasks, hundreds of bullets) containing brainstorming ideas (`dev_ideas.md`, `work_ideas.md`, `sase_ideas.md`), meeting notes (`fscarpel_meet_2024Q3.md`, `team_meet_2024Q3.md`), playbooks (`before_mail_playbook.md`), and domain knowledge (`math.md`, `tin.md`, `legacy_dad.md`). Furthermore, existing Area notes like `cash.md` and `dev.md` have become heavily bloated with non-task sections (`## Area Notes`, `## Legacy Notes`, `## Future Work`) comprising over 70% of their content.

Introducing a dedicated `notebook` note type solves both problems:
- It gives untyped knowledge files a formal, typed, and indexed identity in Bob.
- It enables factoring large H2 note sections out of Area and Project notes into cohesive, clean child files.
- It provides a symmetric, intuitive capture syntax (`@@foo`, `@@foo#bar`, `@@foo+baz`, `@@foo^id`) that mirrors Bob's existing task capture grammar without polluting the task ledger.

### High-Level Critique Summary
The plan is fundamentally sound, but requires four critical architectural refinements:
1. **Resolving the `@@` Grammar Overload**: `@@route` currently denotes a draft-wide *global task destination*. We must formally define how `@@route` coexists between global task routing and notebook note capture.
2. **Strict Invariant on Task Exclusion**: Notebooks must strictly forbid `#task` checkboxes to maintain the operational separation between GTD review workflows and reference knowledge.
3. **Block ID Prompt Prefill Contract**: The existing `block-id-prompt` plugin in `bob-plugins` explicitly requires a checkbox line (`\[[^\]\n]\]`) before extracting headline text for slug prefill. It must be updated to accept checkbox-less note bullets.
4. **Materialized vs. Dynamic Root-Parent Rendering**: In accordance with Bob's design principles, root-parent notebook listings must be **materialized Markdown bullets** maintained by a CLI sync command (`bob notebook sync`), rather than relying on runtime Dataview queries.

---

## 2. Concept & Architecture of Notebook Notes

### 2.1 The Notebook Invariant Rules
A notebook is defined by three strict invariants:
1. **Pure Note Bullets Only**: Notebooks contain only hierarchical note bullets (`- Note` or `* Note`), optionally segmented into `## H2` sections. They **never** contain `#task` checkbox items. Any task generated from a notebook note must be captured into an Area/Project note or referenced via wikilinks.
2. **Strict Hierarchical Lineage (`parent` frontmatter)**: Every notebook MUST point to a valid parent via `parent: "[[<parent-route>]]"`. The parent must be an Area Note, a Project Note, or another Notebook. Rootless or orphaned notebooks are forbidden.
3. **Inherited Attribution & Root-Parent Membership**: While notebooks do not hold tasks or Pomodoros directly, any task elsewhere that references or transcludes a notebook bullet inherits the notebook's root parent for reporting and context.

### 2.2 Notebook Frontmatter Schema
A canonical notebook frontmatter block requires:

```yaml
---
type: "[[notebook]]"
parent: "[[dev]]"
summary: "Ideas, architectural proposals, and tool experiments for developer tooling"
created: 2026-11-09T15:30:00-0500
---
```

#### Fields Breakdown:
- `type`: Must be `"[[notebook]]"` (scalar or quoted wikilink, resolved via `frontmatter_has_type(fm, "[[notebook]]")`).
- `parent`: The wikilink to the parent note (`"[[area_or_project_or_notebook]]"`).
- `summary`: A concise 1-line description (recommended 20–100 characters). This summary is surfaced in the root-parent visual index. (If omitted, tooling falls back to the H1 title or first note bullet).
- `created`: Standard ISO-8601 timestamp with timezone offset (`YYYY-MM-DDTHH:mm:ss±ZZZZ`), populated automatically by capture and templates.
- `project_name_aliases`: Optional array of short route aliases (e.g. `["ideas"]` for `dev_ideas.md`).

---

## 3. Capture Syntax & Grammar Integration

Bob's capture language (detailed in `docs/reference/capture-syntax.md`) is one of the most sophisticated DSLs in personal computing. The proposed notebook capture syntax integrates smoothly with this language by creating a direct structural parallel between task operations (`@`) and notebook operations (`@@`).

### 3.1 Creation Grammar: `@parent^slug@` with `%n`
To create a new notebook:

```bash
bob capture '@dev^ideas@' 'Developer Tooling Ideas' %n
```

#### How it Works:
1. **Lexical Recognition**: The parser recognizes the sealed note marker `@dev^ideas@` (parent = `dev`, slug = `ideas`).
2. **Directive Overload**: In standard Bob capture, `%n` is the *Pomodoro note* directive, which normally conflicts with `@route` (generating a `pomodoro_note_conflict` diagnostic). When paired with a sealed marker `@route^slug@`, the grammar instead classifies the item as `CaptureMode::NewNotebookNote`.
3. **Execution**:
   - Constructs target path `~/bob/dev_ideas.md` (or `ideas.md` if an explicit alias/route override is provided).
   - Generates frontmatter with `type: "[[notebook]]"`, `parent: "[[dev]]"`, and `summary: "Developer Tooling Ideas"`.
   - Initializes the body with `# Developer Tooling Ideas`.
   - Omits the `^prj` task, `template: "[[new_project]]"`, and `## Tasks` section that standard project notes receive.
   - Automatically executes the root-parent index sync on `dev.md`.

### 3.2 Note Appending Grammar: `@@route` and `@@route#Section`
Capturing into an existing notebook uses the double-at `@@` sigil:

#### Top-Level Note Capture:
```bash
bob capture 'Review AST visitor performance @@dev_ideas'
# or leading:
bob capture '@@dev_ideas Review AST visitor performance'
```
- Plans an edit to `dev_ideas.md`.
- Appends `- Review AST visitor performance` at the top level.
- If `dev_ideas.md` contains H2 sections, top-level notes are inserted before the first H2 section.

#### H2 Section Note Capture:
```bash
bob capture 'Explore tree-sitter incremental parsing @@dev_ideas#Parser'
# or leading:
bob capture '@@dev_ideas#Parser Explore tree-sitter incremental parsing'
```
- Locates `## Parser` in `dev_ideas.md` using case-insensitive whitespace-collapsed matching (`normalize_project_section_title`).
- If the section exists, appends `- Explore tree-sitter incremental parsing` as the last bullet of that section.
- If the section does not exist, appends `\n\n## Parser\n\n- Explore tree-sitter incremental parsing`.

### 3.3 Sub-Bullets and Block ID Targeting: `@@route+baz`
To add a sub-bullet under an existing note bullet that carries block ID `^baz`:

```bash
bob capture 'Benchmark against syn 2.0 @@dev_ideas+parser-ast'
```
- Scans `dev_ideas.md` for a note bullet ending in `^parser-ast`.
- Appends an indented sub-bullet: `\t- Benchmark against syn 2.0`.
- Mirrors the exact semantics of `@route+id` from task capture, preserving nesting and existing child notes.

### 3.4 Assigning Block IDs to Captured Notes: `@@route^some-id`
To capture a note bullet and explicitly assign it a block ID:

```bash
bob capture 'Compare jemalloc vs mimalloc @@dev_ideas^alloc-bench'
```
- Appends `- Compare jemalloc vs mimalloc ^alloc-bench`.

#### Interactive Prefill Prompt Contract:
When a user types `@@dev_ideas^` in Bob Mac Capture or an interactive CLI prompt:
1. Capture enters completion context `CompletionContext::NotebookBlockId`.
2. Bob extracts the draft's headline prose using `promptBlockIdCleanHeadline`.
3. Stopwords are stripped via `PROMPT_BLOCK_ID_STOPWORD_SET`, and remaining words are slugified into kebab-case up to 32 characters (`alloc-bench`).
4. Target notebook `dev_ideas.md` is scanned to ensure the ID is unique among `UsedBlockId` records.
5. The picker opens with the suggested slug pre-filled in the text field. Pressing `Return` accepts the suggestion; typing overrides it.

### 3.5 Single-Character Capture Aliases
Bob's real-time editor assistant (`bob capture-rewrite`, `src/native/capture_language/rewrite.rs`) enables seamless single-character shortcuts. The new notebook grammar integrates with these rules as follows:

| Alias Trigger | Context / Preceding Text | Rewritten Result | Purpose |
| :--- | :--- | :--- | :--- |
| `.` | Right after `@` (e.g. `Note @.`) | `Note @@` | Quick conversion from route to notebook route |
| `.` | Right after `@@route` (e.g. `@@ideas.`) | `@@ideas^` | Opens Block ID picker |
| `/` or `\` | Right after `@@route` (e.g. `@@ideas/`) | `@@ideas#` | Opens Section picker |
| `,` | Right after `@@route` (e.g. `@@ideas,`) | `@@ideas+` | Opens Parent Bullet picker |
| Spaced `.` | After prose (e.g. `Note .`) | `Note @` | Standard route alias (unchanged) |

---

## 4. Architectural Critique & Recommended Adjustments

While the overall vision is compelling, a rigorous analysis uncovers several technical nuances that must be addressed during design.

### 4.1 Critique 1: The `@@route` Global Destination Collision
**The Problem:**
In current Bob capture grammar (see `docs/reference/capture-syntax.md` §32 and `src/native/capture_parse.rs`), `@@route` designates a **draft-wide global task destination**:
```text
@@work
First task
Second task
```
Here, `@@work` causes all unrouted items to land in `work.md` under `## Tasks` as `- [ ] #task ...`.
If `@@foo` is also used to target notebooks for note bullets, does a syntactic clash occur?

**Resolution:**
The two semantics can coexist cleanly by evaluating the target note's `type:` frontmatter:
1. **Target Note Dispatching**:
   - When `route` resolves to an **Area Note** or **Project Note**, `@@route` behaves as a **Global Task Destination**.
   - When `route` resolves to a **Notebook Note** (`type: "[[notebook]]"`), `@@route` behaves as a **Notebook Note Destination**. Because notebooks forbid `#task` checkboxes, items captured under `@@notebook` are *always* emitted as pure note bullets (`- ...`), never tasks.
2. **Sub-Operator Immunity**:
   - `@@route#Section`, `@@route+id`, and `@@route^id` are **invalid syntax for global task destinations**. Therefore, any presence of `#`, `+`, or `^` attached to `@@` is 100% unambiguous and exclusively targets a notebook.
3. **Multi-Item Notebook Drafting**:
   A multi-line draft starting with `@@ideas`:
   ```text
   @@dev_ideas
   First brainstorming thought
   Second brainstorming thought
   ```
   correctly routes both items as top-level note bullets into `dev_ideas.md`.

### 4.2 Critique 2: Notebook Filename Scoping
**The Problem:**
When capturing a project note with `@work^intake-flow@`, Bob creates `<route>_<block_id>.md` (`work_intake_flow.md`).
For notebooks, should `@work^ideas@ %n` create `work_ideas.md` or `ideas.md`?

**Recommendation:**
- By default, Bob should generate `<parent>_<slug>.md` (e.g. `work_ideas.md`, `dev_ideas.md`). This prevents namespace collisions across different areas (e.g. `dev_ideas.md` vs. `job_ideas.md`).
- To allow users to refer to the notebook concisely as `@@ideas`, the creation pipeline should automatically write a frontmatter alias:
  ```yaml
  project_name_aliases: ["ideas"]
  ```
  `parent_notes.rs` and `capture_targets.rs` already resolve parent candidates via aliases; extending this to notebook resolution allows `@@ideas` to resolve directly to `dev_ideas.md` without polluting the global filesystem namespace.

### 4.3 Critique 3: Strict Validation Against Task Insertion
**The Problem:**
Users or external scripts might accidentally capture tasks into a notebook (`- [ ] #task ...`).

**Recommendation:**
1. **Linter & Hook Enforcement**: `bob notebook verify` (similar to `bob articles verify`) scans all files with `type: "[[notebook]]"`. If any line matches the task regex (`^[ \t]*[-*] \[[ xX?~-]\]`), it emits an error:
   ```text
   bob notebook: dev_ideas.md:14: notebook notes cannot contain tasks; found '- [ ] #task'
   ```
2. **Capture Rejection**: If capture item text contains `#task` or checkbox syntax while targeting `@@notebook`, the planner refuses the capture with diagnostic code `notebook_task_refused`.

### 4.4 Critique 4: Block ID Prefill in `block-id-prompt`
**The Problem:**
In `bob-plugins/plugins/block-id-prompt/src/015-prompt-block-id-naming.js`:
```javascript
function promptBlockIdExtractTaskBody(rawLine) {
  const line = String(rawLine || "");
  const match = line.match(
    /^[ \t]*(?:>[ \t]*)*(?:[-+*]|\d+[.)])[ \t]+\[[^\]\n]\](?:[ \t]+(.*))?$/,
  );
  if (!match) return null;
  return match[1] || "";
}
```
This regex strictly requires a checkbox `\[[^\]\n]\]`. If called on a notebook note bullet (`- Review AST visitor performance`), it returns `null`, causing the prompt to fail to pre-fill a suggested slug!

**Recommendation:**
Update `015-prompt-block-id-naming.js` to extract text from plain list items when no checkbox is present:
```javascript
function promptBlockIdExtractHeadline(rawLine) {
  const line = String(rawLine || "");
  // Checkbox task bullet
  const taskMatch = line.match(
    /^[ \t]*(?:>[ \t]*)*(?:[-+*]|\d+[.)])[ \t]+\[[^\]\n]\](?:[ \t]+(.*))?$/,
  );
  if (taskMatch) return taskMatch[1] || "";
  // Plain note bullet
  const noteMatch = line.match(
    /^[ \t]*(?:>[ \t]*)*(?:[-+*]|\d+[.)])[ \t]+(.*)$/,
  );
  if (noteMatch) return noteMatch[1] || "";
  return null;
}
```

---

## 5. Visual Root-Parent Rendering Specification

The user requested:
> "We should render an excellent, visually appealing section in the root parent of notebooks (for any root parent that has notebook children or has non-root children that do, recursively) that links to each notebook and includes a good summary of each notebook."

### 5.1 Root Parent Derivation Algorithm
In Bob's ontology, every notebook belongs to a root parent:
1. Walk the `parent` frontmatter chain upwards:
   - If `parent` is a Notebook, recurse to its parent.
   - If `parent` is a Project:
     - If the project has `root: true` or is a top-level project under an area, it is the root parent.
     - If the project is a sub-project without `root: true`, walk up to its parent project or area.
   - If `parent` is an Area, that Area is the root parent.
2. Group all notebooks in the vault by their derived root parent.

### 5.2 Visual Section Design
The section should be materialized into markdown under the heading `## Notebooks`.

#### Placement Rule:
- In an **Area Note**: Placed immediately above `## Tasks` (or above `## Future Work`).
- In a **Project Note**: Placed immediately beneath the `^prj` task block and its schedule logs, above `## Tasks`.

#### Layout & Typography:
```markdown
## Notebooks

- 📓 **[[dev_ideas]]** — Ideas, tool suggestions, and refactoring proposals for developer tooling
- 📓 **[[cli_rules]]** — Guidelines and conventions for Bob CLI subcommands and options
  - 📓 **[[cli_help_standards]]** — Formatting rules for `--help` flags and doc generation
- 📓 **[[tin]]** — Technical notes, docs, and test target guidance for the Tin test runner
```

#### Why This Layout Wins:
1. **Semantic Iconography (`📓`)**: Parallels `🧩 **Sub-projects:**` and `🧱 **BLOCKS:**`, making notebook links visually recognizable across the vault.
2. **Bold Wikilinks (`**[[slug]]**`)**: Ensures clean Obsidian navigation and graph view connectivity.
3. **Em-Dash Summaries (`— <summary>`)**: Surfaces the notebook's purpose immediately without requiring the user to open the file.
4. **Recursive Indentation**: Sub-notebooks are indented directly beneath their parent notebook, rendering nested hierarchies naturally.
5. **Portability**: Pure GitHub Flavored Markdown renders flawlessly in terminal CLI tools (`cat`, `glow`), SASE agent memory, mobile Obsidian, and web viewports.

### 5.3 Maintenance Command: `bob notebook sync`
To ensure this section never becomes stale:
- A new command `bob notebook sync` scans all notes with `type: "[[notebook]]"`, builds the dependency forest, extracts `summary:` fields, and rewrites the `## Notebooks` section in every root parent note.
- `bob notebook sync` is hooked into `bob project sync` and `bob vault-sync`, ensuring that whenever git syncs or project structures update, notebook indexes update automatically.

---

## 6. SASE Memory Glossary Term

In accordance with SASE conventions, we define the new glossary strand for the `glossary` memory web.

### File: `sase/memory/glossary/notebook.md`

```markdown
---
keyword: Notebook
aliases:
  - "notebook note"
  - "notebook file"
---

# Notebook

*Requested · project*

A Bob vault Markdown file with frontmatter `type: "[[notebook]]"` that holds pure note
bullets (never `#task` items), optionally organized under `## H2` section headings. It
provides a lightweight, flexible container for grouping related reference knowledge,
brainstorming ideas, meeting notes, playbooks, and documentation without the overhead of
an [[area-note]] or the finite lifecycle and `^prj` criteria of a [[project-note]].

Every notebook must specify a parent via its frontmatter `parent:` field, linking it to
an area note, a project note, or another notebook. Notebooks cannot be rootless. A
notebook's root parent is derived by walking its parent chain upwards to the outermost
root project or area note. The root parent materializes an indexed `## Notebooks` section
linking to all child notebooks in its subtree along with their frontmatter summaries.

Capture into notebooks uses the `@@` family of markers: `@@route` captures a top-level
note bullet, `@@route#Section` captures under an H2 section, `@@route+id` appends a
sub-bullet under an existing note bullet with block ID `^id`, and `@@route^id` mints a
new block ID on the captured bullet. Create a notebook using `@parent^slug@ <Title> %n`.
Notebooks are read-only to GTD review walks (`]s`), task status cyclers, and Pomodoro
task linkers.
```

---

## 7. Vault Archaeology & Candidate Migration Plan

A comprehensive scan of Bryan's Obsidian vault (`~/bob/`) was conducted. Here are the empirical findings:

### 7.1 Vault Census
- **Total Markdown Files in Vault**: 6,718
- **Files with Frontmatter**: 6,502
- **Files in Root Directory (`~/bob/*.md`)**: 664
  - Formally Typed (`type:` present): 161 (98 projects, 31 days, 18 areas, 13 refs, 1 article)
  - **Untyped Root Files (`parent:` present, but NO `type:`)**: **488**
  - Untyped Pure Note Bullet Files (0 tasks, >0 bullets): **393**

These 393 files are predominantly legacy notes converted from zorg (`generated_from_zorg: true`). They have valid parent pointers (`parent: [[...]]`), but because they lack `type: "[[notebook]]"`, Bob's CLI tools, capture completion targets, and navigation hotkeys treat them as unclassified files.

### 7.2 Selected High-Value Migration Candidates
We have analyzed and grouped the most valuable candidate files into five migration cohorts:

#### Cohort 1: Engineering & Developer Idea Notebooks
These files contain rich technical notes, tool ideas, and refactoring thoughts.
1. **`dev_ideas.md`** (Parent: `[[dev]]` | 223 bullets, 0 tasks)
   - *Summary*: "Brainstorming, tool ideas, and refactoring proposals for developer workflows"
   - *Target Type*: `type: "[[notebook]]"`, `parent: "[[dev]]"`
2. **`work_ideas.md`** (Parent: `[[job]]` | 209 bullets, 0 tasks)
   - *Summary*: "High-level initiatives, tooling concepts, and architecture ideas for work"
   - *Target Type*: `type: "[[notebook]]"`, `parent: "[[job]]"`
3. **`sase_ideas.md`** (Parent: `[[sase]]` | 167 bullets, 0 tasks)
   - *Summary*: "Ideas and enhancement proposals for SASE agent workflows and architecture"
   - *Target Type*: `type: "[[notebook]]"`, `parent: "[[sase]]"`
4. **`gtd_ideas.md`** (Parent: `[[gtd]]` | 131 bullets, 0 tasks)
   - *Summary*: "System design notes and continuous improvements for GTD and Bob"
   - *Target Type*: `type: "[[notebook]]"`, `parent: "[[gtd]]"`

#### Cohort 2: Recurring Meeting & 1:1 Series Notebooks
These files represent quarterly 1:1 meeting series, perfectly suited to H2 date sections.
1. **`fscarpel_meet_2024Q3.md`** (Parent: `[[job]]` | 210 bullets, 13 H2 sections)
   - *Summary*: "Quarterly 1:1 meeting agendas, discussion topics, and action notes for 2024 Q3"
   - *Target Type*: `type: "[[notebook]]"`, `parent: "[[job]]"`
2. **`fscarpel_meet_2024Q2.md`** (Parent: `[[job]]` | 184 bullets, 8 H2 sections)
   - *Summary*: "Quarterly 1:1 meeting notes for 2024 Q2"
3. **`team_meet_2024Q3.md`** (Parent: `[[job]]` | 119 bullets, 10 H2 sections)
   - *Summary*: "Team sync agendas, sprint discussions, and engineering updates for 2024 Q3"

#### Cohort 3: Playbooks & Technical References
Operational playbooks and guides that Bryan references regularly.
1. **`before_mail_playbook.md`** (Parent: `[[dev]]` | 17 bullets, 0 tasks)
   - *Summary*: "Pre-review CL checklist and verification playbook before requesting review"
   - *Target Type*: `type: "[[notebook]]"`, `parent: "[[dev]]"`
2. **`tin.md`** (Parent: `[[dev]]` | 66 bullets, 0 tasks)
   - *Summary*: "Internal test runner guide, command flags, and troubleshooting notes for Tin"
   - *Target Type*: `type: "[[notebook]]"`, `parent: "[[dev]]"`
3. **`build_pages.md`** (Parent: `[[dev]]` | 132 bullets, 29 H2 sections)
   - *Summary*: "Historical log of build breaks, page tracker alerts, and root cause notes"
   - *Target Type*: `type: "[[notebook]]"`, `parent: "[[dev]]"`

#### Cohort 4: Personal Knowledge Notebooks
1. **`legacy_dad.md`** (Parent: `[[abby]]` | 106 bullets, 0 tasks)
   - *Summary*: "Parenting notes, milestone reflections, and fatherhood principles"
   - *Target Type*: `type: "[[notebook]]"`, `parent: "[[abby]]"`
2. **`math.md`** (Parent: `[[dev]]` | 4 bullets, 0 tasks)
   - *Summary*: "Quick conversion heuristics and applied mathematics notes"
   - *Target Type*: `type: "[[notebook]]"`, `parent: "[[dev]]"`

#### Cohort 5: Factoring Out Bloated H2 Sections from Area/Project Notes
Our audit revealed massive H2 sections in Area notes that should be factored out into child notebooks:
1. **`cash.md`** → Extract `## Area Notes` and `## Legacy Notes` (166 note bullets!) into `cash_notes.md` (`parent: [[cash]]`, `summary: "Financial account notes, legacy instructions, and banking policies"`).
2. **`dev.md`** → Extract `## Legacy Notes` and `## Future Work` (128 note bullets!) into `dev_notes.md` (`parent: [[dev]]`, `summary: "Developer environment reference notes and tool experiments"`).
3. **`inbox.md`** → Extract `## Migrated Zorg Inbox` (179 note bullets!) into `inbox_archive.md` (`parent: [[inbox]]`, `summary: "Archived reference notes migrated from legacy Zorg inbox"`).
4. **`sase_blog.md`** (Project) → Extract `## Screenshots`, `## Contents`, `## Outline`, `## Later Posts` (159 note bullets!) into `sase_blog_notes.md` (`parent: [[sase_blog]]`, `summary: "Research material, outlines, and media plans for SASE blog posts"`).

---

## 8. Implementation Matrix & Architectural Roadmap

### 8.1 `bob-cli` Changes
1. **Frontmatter Detection (`src/native/projects/scan.rs`)**:
   - Implement `pub(crate) fn frontmatter_is_notebook(fm: &Frontmatter<'_>) -> bool`.
   - Update `frontmatter_type_names` and `RESERVED_RECORD_IDS` to include `"notebook"`.
2. **Capture Target Scanning (`src/native/capture_targets.rs`)**:
   - Add `CaptureTargetKind::Notebook` to `CaptureTargetKind`.
   - Update `scan_capture_targets_with_config` to index all `type: "[[notebook]]"` notes.
   - Display a distinct `Notebooks` group in `bob capture-targets`.
3. **Capture Grammar & Token Parser (`src/native/capture_parse.rs` & `capture_language/`)**:
   - Update lexer to recognize `@@route#Section`, `@@route+id`, `@@route^id`.
   - Add `CaptureMode::NotebookNote`.
   - Overload `@parent^slug@ %n` to trigger `CaptureMode::NewNotebookNote`.
4. **Rewrite & Sigil Aliases (`src/native/capture_language/rewrite.rs`)**:
   - Update `expand_dot_block_id_alias`: `@@notebook.` expands to `@@notebook^`.
   - Update `expand_hash_alias`: `@@notebook/` expands to `@@notebook#`.
   - Update `expand_parent_task_comma_alias`: `@@notebook,` expands to `@@notebook+`.
   - Add alias for `@.` expanding to `@@`.
5. **Execution Layer & Content Renderer (`src/native/capture/plan.rs`)**:
   - Implement pure note insertion at top-level or under target H2 section.
   - Handle sub-bullet placement under matching block ID.
   - Mint assigned block ID `^some-id`.
6. **Root Parent Sync Engine (`src/native/projects/sync.rs`)**:
   - Add `bob notebook sync` subcommand.
   - Implement recursive upward parent walk to root Area/Project.
   - Materialize the `## Notebooks` section with `📓 **[[slug]]** — <summary>`.

### 8.2 `bob-plugins` Changes
1. **`block-id-prompt`**:
   - Update `015-prompt-block-id-naming.js` (`promptBlockIdExtractHeadline`) to support checkbox-less note bullets.
2. **`bob-navigation-hotkeys`**:
   - Add a command "Factor H2 section into child notebook" (`Ctrl+Shift+Alt+N`).
   - Automatically create `<note>_<section>.md` with `parent: [[current]]`, cut the section contents, and insert `📓 **[[<note>_<section>]]**` into the parent's `## Notebooks` section.

### 8.3 `bob-mac-capture` Changes
- Update completion provider to recognize `notebook_route`, `notebook_section`, and `notebook_block_id` span types.
- Ensure the Block ID prompt displays suggested slugs for notebook captures.

---

## 9. Recommended Next Actions

1. **Adopt Design & Requirements**: Review this report's syntax coexistence model and root-parent layout.
2. **Implement Core Engine in `bob-cli`**:
   - Add `frontmatter_is_notebook` and `CaptureTargetKind::Notebook`.
   - Wire `@@` capture execution and `%n` creation overload.
   - Implement `bob notebook sync`.
3. **Update Plugins**: Patch `block-id-prompt` in `bob-plugins` for checkbox-less bullets.
4. **Execute Wave 1 Migration**:
   - Migrate Cohort 1 (`dev_ideas.md`, `work_ideas.md`, `sase_ideas.md`, `gtd_ideas.md`).
   - Migrate Cohort 3 (`before_mail_playbook.md`, `tin.md`).
   - Run `bob notebook sync` to generate the first visual `## Notebooks` sections in `dev.md` and `job.md`.
