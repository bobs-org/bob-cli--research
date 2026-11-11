# Notebook H2 Section Targeting in Capture: Architecture, Critique, and Design

**Author:** researcher `gem`  
**Date:** 2026-11-11  
**Scope:** `bob-cli`, `bob-mac-capture`, capture grammar, completion engine, rewrite rules, and notebook storage format.  
**Topic:** Extending drawer-style container targeting to notebook H2 sections via bullet shortcuts (`- #`, `- /`) and glued syntax (`@<notebook>#`).

---

## 1. Executive Summary

This research investigates the proposal to bring section-targeting capabilities—currently supported for task drawers and project note `##` headings—to Bob **notebooks**. Specifically, the feature request proposes:
1. Allowing the `#` key (or `/` capture alias) typed at the start of a first-level bullet (`- #` or `- /`) to trigger completion for known notebook H2 sections.
2. Providing robust support for this workflow both when capturing notes to an existing notebook via `@<notebook>` (or draft-wide `@@<notebook>`) and when using project capture syntax (e.g., creating a notebook via `@parent^id@ %n` or capturing notes to a project's notebook).
3. Ensuring seamless completion for existing sections and on-demand creation of new sections using the `@<notebook>#` syntax.

### Key Findings & High-Level Verdict

- **Core Verdict: Strongly Endorsed, with Critical Architectural Adjustments.** The proposal resolves a glaring asymmetry in Bob's capture ecosystem. Currently, capturing multi-note items into different sections of a notebook requires writing separate capture items or verbose glued `@nb#sec` selectors on every line. Adding bullet-level section targeting makes notebook capture substantially more expressive, fluid, and intuitive.
- **Critical Architectural Adjustment (Syntax & Visual Identity):** In task drawers, `RowStyle::Bullet` replaces `- #` with an ALL-CAPS title (`- REQUIREMENTS\n  - `) because a task drawer in Markdown is literally an ALL-CAPS child bullet. In contrast, notebook sections are Markdown `## Title Case` headings, and notebook notes are freeform bullets that may legitimately contain nested sub-bullets. Replacing `- #` with a bare bullet in a notebook would create severe syntactic ambiguity between section headers and ordinary notes with sub-bullets. **Therefore, notebook section bullets must preserve an explicit section sigil: `- #<slug>` or `- #"<Title>"` (e.g., `- #git\n  - ` or `- #"Merge Tools"\n  - `).**
- **Typing Alias Unification:** The `/` typing alias currently fails under notebook contexts because `classify_target` in `drawer_bullet.rs` returns `None` for notebook modes, causing `expand_hash_alias` to abort. Wiring notebook targets into `DrawerBulletTarget` automatically unlocks both `- /` -> `- #` on bullet lines and `@<notebook>/` -> `@<notebook>#` on route lines.
- **Recommended Solution:** Adopt the **Explicit Section Slug Model** (Model 2/3), where `- #` opens a dedicated `NotebookSection` completion menu showing existing H2s in document order, vault catalog recents, and a dynamic create row (`New section "..."`). Selection inserts `- #<slug>\n  - ` (with nested cursor placement). When committed, the capture planner files each nested note under its target `## Heading`, creating missing headings at EOF automatically while strictly preserving notebook integrity (no tasks, no checkboxes).

---

## 2. Baseline Architecture & Current State Analysis

To understand why this feature is needed and where the gaps lie, we must examine how Bob's capture pipeline currently handles notebooks versus task drawers.

### 2.1 The Notebook Data Model

According to `decisions:notebook-routes-write-notes`, `glossary:notebook`, and `docs/notebooks.md`:
- A notebook is a vault-root Markdown file with frontmatter `type: "[[notebook]]"`, a `parent:` link (reaching an area or project), and a one-line `summary:`.
- Its body consists exclusively of note bullets (`- ` outside code blocks), optionally partitioned by `## Heading` sections below a top-level H1 title.
- **Invariants:** A notebook holds **no tasks**, no checkboxes, no Pomodoro sessions, no Ready lanes, and no block links. It is transparent to clock and type walks.
- **Section Structure:** Sections are strictly level 2 headings (`## Title Case`). Bullets before the first `##` are top-level notes; bullets between `## Foo` and `## Bar` belong to section `Foo`.

### 2.2 Current Notebook Capture Forms

Currently, `bob capture` supports the following forms on a notebook route (`@nb`):

| Form | Meaning | Placement on Disk |
| :--- | :--- | :--- |
| `note text @nb` | Top-level note | Appended after the last note before the first `##` heading. |
| `note text @nb#section` | Section note | Appended after the last note under `## Section`. Missing sections are created at EOF. |
| `note text @nb^id` | Named note | Appended before first `##` with anchor `^id`. |
| `note text @nb#section^id` | Named section note | Appended under `## Section` with anchor `^id`. |
| `note text @nb+id` | Sub-note | Nested under note bullet `^id`. |
| `@@nb` | Draft-wide declaration | Unrouted items in the draft become notes in `@nb`. |
| `@parent^id@ %n <summary>` | Notebook creation | Writes `<parent>_<id>.md` and updates catalogs. |
| `@nb\n- note 1\n- note 2` | List header | Each bullet becomes a separate top-level note. |
| `@nb#section\n- note 1\n- note 2` | Section list header | Each bullet becomes a note under `## Section`. |

### 2.3 How Task Drawers & Project H2 Drawers Work Today

For tasks and project notes, Bob provides a rich, multi-tiered container targeting system:

```text
@project+task-id
- #requirements
  - note 1
  - note 2
- #future-work
  - note 3
```

1. **In the Lexer (`drawer_bullet.rs`):**
   `scan_leading` scans first-level authored bullets for `#`. If cursor is after `#`, `drawer_bullet_probe` queries `editor_item.drawer_bullet_target`.
2. **Target Classification (`classify_target`):**
   - `EditorMode::Task` -> `DrawerBulletTarget::NewTask`
   - `EditorMode::ProjectNote` -> `DrawerBulletTarget::NewProjectNote`
   - `EditorMode::SubBullet` / `TaskToggle` -> `DrawerBulletTarget::ExistingTask`
   - For an existing project note's `^prj` task, `lookup_target` calls `capture_drawers::project_h2_drawers(&contents)`, which scans the note's `##` ATX headings and presents them as drawers.
3. **Completion UI (`drawers.rs`):**
   The completion engine emits candidates divided into:
   - `task` (the target's existing drawers or H2 sections in document order)
   - `recent` (drawers from the vault-wide drawer catalog)
   - `new` (a create row for the typed query)
4. **Replacement & Continuation:**
   `append_continuation` appends `\n  - ` so the user immediately transitions from picking a container to typing its first note.
5. **Disk Commit:**
   On a task, notes are merged into the ALL-CAPS drawer bullet. On a project note (`^prj`), `resolve_h2_for_write` inserts the notes under the matching `## Title Case` heading, creating it if absent.

### 2.4 The Gap: Why Notebooks Fail Today

When a user tries to do the exact same thing under a notebook route:

```text
@dev_tools
- #git
  - note 1
```

1. **`classify_target` returns `None`:** In `src/native/capture_language/drawer_bullet.rs`, line 169:
   ```rust
   match entry_mode {
       EditorMode::Task | EditorMode::PomodoroTask => Some(DrawerBulletTarget::NewTask { .. }),
       EditorMode::ProjectNote | EditorMode::PomodoroProjectNote => Some(DrawerBulletTarget::NewProjectNote { .. }),
       EditorMode::SubBullet | EditorMode::TaskToggle => Some(DrawerBulletTarget::ExistingTask { .. }),
       _ => None, // <-- NotebookNote and NotebookCreate hit this!
   }
   ```
2. **`drawer_bullet_probe` aborts:** Returns `Some(None)`, treating `- #` as an empty success or invalid drawer position. No completion menu appears.
3. **Typing Alias Fails:** In `src/native/capture_language/rewrite.rs`, `expand_hash_alias` checks if candidate `- #` yields a valid completion field (`CompletionContext::Drawer` or `Section`). Because `drawer_bullet_probe` returns `None`, the candidate fails, and typing `- /` remains literal `- /`.
4. **Draft Execution Refuses:** If submitted, `capture` rejects `- #git` under `@dev_tools` with `drawer_bullet_position`: *"drawer shortcuts are for tasks; notebook notes are plain bullets"*.

---

## 3. Critical Appraisal & Plan Critique

### 3.1 Is this a good idea?

**Yes, unequivocally.** The benefits to user flow, cognitive ergonomics, and systemic consistency are significant:

1. **Eliminates High-Friction Workarounds:** Currently, capturing three notes into two different notebook sections requires either:
   - Writing 3 separate capture items with repetitive `@dev_tools#git` and `@dev_tools#troubleshooting` markers.
   - Writing multiple list-header items separated by blank lines.
   With bullet section targeting, it collapses into a single, elegant outline:
   ```text
   @dev_tools
   - #git
     - Use mergiraf for syntax-aware merge conflicts
     - Rebase with --autosquash
   - #troubleshooting
     - Check lsof -i :8080 before restarting service
   ```
2. **Completes the Mental Model Symmetry:** In Bob, container hierarchy is always traversed top-down:
   - Root / File (`@route`) -> Container (`#section` or `#drawer`) -> Item (`- note`).
   Users already expect `- #` to target containers. Having it work on project notes and tasks but silently fail on notebooks feels like an arbitrary and frustrating defect.
3. **Preserves Vault Speed & Offline Integrity:** Notebook H2 sections are purely local to the target Markdown file. Scanning and completing them requires reading only the single target note (or memory snapshot), avoiding heavyweight multi-file scans.

### 3.2 Critique of a Naive Implementation & Identified Pitfalls

A naive attempt to simply copy the task-drawer implementation would introduce severe design flaws. We must explicitly critique and resolve three major hazards:

#### Hazard 1: The ALL-CAPS Drawer Collision

In task drawers, `choose_bullet` replaces `- #` with an ALL-CAPS title:
`- #requirements` -> `- REQUIREMENTS\n  - `

If notebooks did the same:
`- #git` -> `- GIT\n  - `

Why this is unacceptable for notebooks:
- **Notebooks have no drawers:** Per `glossary:notebook` and `decisions:notebook-routes-write-notes`, notebooks strictly contain note bullets and `## Title Case` headings. Introducing ALL-CAPS bullets into notebook syntax blurs the distinction between GTD tasks and freeform knowledge notebooks.
- **Ambiguity with Authored Prose:** In a notebook, an authored note can legitimately be written in uppercase (e.g., `- IMPORTANT NOTE: backup encryption keys`). If ALL-CAPS bullets were treated as section headers, ordinary notes would accidentally create new H2 sections!
- **Ambiguity with Sub-Bullets:** In notebooks, notes can have nested detail:
  ```markdown
  - Architecture overview
    - Sub-bullet 1
    - Sub-bullet 2
  ```
  If a bare bullet with children were parsed as a section header, any multi-level note would be corrupted into an H2 section.

> [!IMPORTANT]
> **Resolution:** Section targets on notebook bullets **must preserve the `#` prefix**:
> `- #git\n  - ` or `- #"Merge Tools"\n  - `.
> The `#` is an unambiguous syntactic boundary: `- #` introduces a section container; `- ` introduces a note.

#### Hazard 2: "Project Capture Syntax" vs Notebook Capture Syntax

The user prompt notes:
> *"This functionality should have good support when using the project capture syntax or when capturing new notes to an existing project by targeting it with the `@<notebook>` syntax."*

We must clearly distinguish the two workflows referenced here:
1. **Capturing to an existing project's notebook (`@<notebook>`):**
   In Bob, notebooks are owned by an area or project (e.g., notebook `cash_tax.md` is owned by project `cash.md`). However, capture routing is always direct by stem (`@cash_tax`), not path-nested (`@cash/tax` is reserved for records). Thus, "targeting an existing project with the `@<notebook>` syntax" means targeting the project's dedicated notebook `@cash_tax` directly.
2. **Project Capture Syntax for Notebook Creation (`@parent^id@ %n`):**
   Notebooks are created using Bob's project seal syntax with the `%n` directive:
   `@project^notes@ %n Developer notes and architecture`
   Currently, `notebook_create.rs` parses ALL-CAPS first-level bullets into `## Title Case` sections at creation time (`is_project_section_title`). However, typing `- #` in that draft yields no completion. Extending completion to `EditorMode::NotebookCreate` allows users to pick catalog sections (e.g., `Architecture`, `Requirements`, `Troubleshooting`) and scaffold the notebook's initial H2 sections during creation.

#### Hazard 3: Near-Miss Section Collisions & Quoting Rules

In `notebook_note.rs`, `resolve_notebook_section` enforces strict near-miss protection:
- If a user types `@dev_tools#gi`, Bob refuses with `notebook_section_near_miss` because `gi` is close to existing section `Git`.
- To create a section named `Gi`, the user must explicitly quote it: `@dev_tools#"Gi"`.
- In bullet completion, the completion engine must adhere to this exact resolver contract:
  - If query matches an existing section (case-insensitively or via slug), select that section.
  - If query is unrelated, offer `New section "<Title>"`.
  - If query is a near-miss, offer `New section "\"<Title>\""` (quoted), preventing accidental typos from creating near-duplicate sections while keeping intentional creation explicit.

---

## 4. Proposed Design: The Beautiful & Intuitive UX

### 4.1 Visualizing the User Interaction

#### Workflow 1: Capturing into an Existing Notebook

Suppose the user has a notebook `dev_tools.md` with sections `## Git` and `## Troubleshooting`.

1. The user opens capture and types:
   ```text
   @dev_tools
   - /
   ```
2. **Instant Rewrite:** The typing alias immediately rewrites `/` to `#`:
   ```text
   @dev_tools
   - #
   ```
3. **Completion Palette Appears:**
   The completion palette pops up below the bullet with:
   ```text
   ╭─ Notebook Sections · dev_tools ──────────────────────────────────────────╮
   │  Git                 2 notes · Adds to ## Git                            │
   │  Troubleshooting     1 note  · Adds to ## Troubleshooting                │
   │  Recent: Config      Vault catalog · Creates ## Config                   │
   ╰──────────────────────────────────────────────────────────────────────────╯
   ```
4. **User Selects `Git` (or types `gi` and presses Enter):**
   The line expands to:
   ```text
   @dev_tools
   - #git
     - |
   ```
   The caret (`|`) lands indented two spaces, ready for immediate typing of the first note.
5. **User Types Notes & Adds Another Section:**
   ```text
   @dev_tools
   - #git
     - Use mergiraf for syntax-aware merge conflicts
     - Rebase with --autosquash
   - #tr
   ```
   Typing `#tr` filters completion to `Troubleshooting`. Pressing Tab/Enter expands to:
   ```text
   @dev_tools
   - #git
     - Use mergiraf for syntax-aware merge conflicts
     - Rebase with --autosquash
   - #troubleshooting
     - Check lsof -i :8080 before restarting
   ```
6. **Result on Disk (`dev_tools.md`):**
   ```markdown
   # Developer tools

   ## Git

   - Existing note [created::2026-11-08]
   - Use mergiraf for syntax-aware merge conflicts [created::2026-11-11]
   - Rebase with --autosquash [created::2026-11-11]

   ## Troubleshooting

   - Existing debug note [created::2026-11-09]
   - Check lsof -i :8080 before restarting [created::2026-11-11]
   ```

#### Workflow 2: Creating a New Section on the Fly

1. Draft:
   ```text
   @dev_tools
   - #docker
   ```
2. Completion Palette shows:
   ```text
   ╭─ Notebook Sections · dev_tools ──────────────────────────────────────────╮
   │  + New section "Docker"   Creates ## Docker at EOF                       │
   ╰──────────────────────────────────────────────────────────────────────────╯
   ```
3. On Enter, it expands to:
   ```text
   @dev_tools
   - #docker
     - Pin container base images by digest
   ```
4. On commit, Bob appends `## Docker\n\n- Pin container base images by digest [created::2026-11-11]` to `dev_tools.md`.

#### Workflow 3: Notebook Creation via Project Capture Syntax

1. Draft:
   ```text
   @dev^nvim@ %n Neovim configuration and plugins
   - /
   ```
2. Rewrites `/` to `#`. Completion offers common catalog sections (`Configuration`, `Keymaps`, `Plugins`, `Troubleshooting`).
3. User drafts:
   ```text
   @dev^nvim@ %n Neovim configuration and plugins
   - #plugins
     - mini.nvim for lightweight modules
     - oil.nvim for buffer-like file editing
   - #keymaps
     - Map <leader>ff to telescope find_files
   ```
4. On commit, Bob creates `dev_nvim.md`:
   ```markdown
   ---
   parent: "[[dev]]"
   template: "[[new_notebook]]"
   type: "[[notebook]]"
   summary: Neovim configuration and plugins
   created: 2026-11-11T13:00:00-05:00
   ---

   # Neovim

   ## Plugins

   - mini.nvim for lightweight modules [created::2026-11-11]
   - oil.nvim for buffer-like file editing [created::2026-11-11]

   ## Keymaps

   - Map <leader>ff to telescope find_files [created::2026-11-11]
   ```

#### Workflow 4: Glued `@<notebook>#` and Typing Alias `/`

1. The user types `@dev_tools/` on a parent line.
2. `expand_hash_alias` detects the complete notebook route and rewrites `@dev_tools/` to `@dev_tools#`.
3. Completion opens with `CompletionContext::Section`, listing `Git`, `Troubleshooting`, and `+ New section "..."`.
4. Picking `Git` produces:
   `Try mergiraf @dev_tools#Git` or `@dev_tools#Git\n- note 1\n- note 2`.

---

## 5. Architectural & Technical Implementation Specification

### 5.1 AST & Target Classification (`src/native/capture_language/`)

#### 1. Extend `DrawerBulletTarget` (`drawer_bullet.rs`)
Add explicit targets for existing and newly created notebooks:

```rust
#[derive(Debug, Clone, PartialEq, Eq)]
pub(crate) enum DrawerBulletTarget {
    ExistingTask { route: String, block_id: String },
    NewTask { route: Option<String>, text: String },
    NewProjectNote { route: String, block_id: String, text: String },
    /// Targeting an existing notebook: bullets file into notebook H2 sections.
    ExistingNotebook { route: String },
    /// Scaffolding sections while creating a notebook via `@parent^id@ %n`.
    NewNotebook { parent: String, notebook_id: String, summary: String },
}
```

#### 2. Update `classify_target` (`drawer_bullet.rs`)
Wire `EditorMode::NotebookNote`, `EditorMode::NotebookSubNote`, and `EditorMode::NotebookCreate`:

```rust
pub(crate) fn classify_target(
    entry_mode: EditorMode,
    route: Option<&str>,
    block_id: Option<&str>,
    parent_body: &str,
    glued_section: Option<&str>,
    has_first_level_line: bool,
    explicit_toggle: bool,
) -> Option<DrawerBulletTarget> {
    match entry_mode {
        EditorMode::Task | EditorMode::PomodoroTask => {
            Some(DrawerBulletTarget::NewTask {
                route: route.map(str::to_string),
                text: parent_body.trim().to_string(),
            })
        }
        EditorMode::ProjectNote | EditorMode::PomodoroProjectNote => {
            Some(DrawerBulletTarget::NewProjectNote {
                route: route?.to_string(),
                block_id: block_id?.to_string(),
                text: parent_body.trim().to_string(),
            })
        }
        EditorMode::NotebookNote | EditorMode::NotebookSubNote => {
            Some(DrawerBulletTarget::ExistingNotebook {
                route: route?.to_string(),
            })
        }
        EditorMode::NotebookCreate => {
            Some(DrawerBulletTarget::NewNotebook {
                parent: route?.to_string(),
                notebook_id: block_id?.to_string(),
                summary: parent_body.trim().to_string(),
            })
        }
        EditorMode::SubBullet | EditorMode::TaskToggle => {
            let glued = glued_section.is_some_and(|s| !s.is_empty());
            if !parent_body.trim().is_empty() || glued || explicit_toggle || !has_first_level_line {
                return None;
            }
            Some(DrawerBulletTarget::ExistingTask {
                route: route?.to_string(),
                block_id: block_id?.to_string(),
            })
        }
        _ => None,
    }
}
```

#### 3. Preserve Target under Draft-Wide `@@notebook` (`editor_parse.rs`)
In `apply_global_destination`:
When `global.mode == EditorMode::NotebookNote`, assign `DrawerBulletTarget::ExistingNotebook { route: global.route.clone() }` to child items.

### 5.2 Completion Engine (`src/native/capture_complete/`)

#### 1. Scope and Target Modeling (`drawers.rs`)
In `Target`:
- Add `DrawerScope::NotebookSection`.
- In `lookup_target`: If `route` resolves to a notebook (checked via `is_notebook_route_contents`), construct a `Target` with:
  - `scope: DrawerScope::NotebookSection`
  - `drawers`: Derived from `capture_language::notebook::notebook_sections(&contents)`. Each `NotebookSection` maps to a `Drawer`:
    - `key`: `drawer_key(&heading.title)`
    - `slug`: `selector_slug(&heading.title)`
    - `title`: `heading.title`
    - `line_index`: `heading.line_index`
- In `Target::fresh`: If bullet is `DrawerBulletTarget::NewNotebook`, construct a `Target` with `scope: DrawerScope::NotebookSection` and `new_note: true`.

#### 2. Formatting Menu Rows & Replacements
In `choose_bullet`:
For `DrawerScope::NotebookSection`:
- **Existing section:**
  - `replacement`: `format!("#{slug}")` (or bare slug if inside `#`).
  - `detail`: `format!("{N} notes")`.
  - `consequence`: `format!("Adds to ## {title}")`.
- **Catalog recent section:**
  - `replacement`: `format!("#{slug}")`.
  - `detail`: `"Catalog"`.
  - `consequence`: `format!("Creates ## {title}")`.
- **New section row (`new`):**
  - If bare query is a near-miss: `replacement = format!("\"{}\"", quoted_title)`.
  - Otherwise: `replacement = format!("#{slug}")`.
  - `consequence`: `format!("Creates ## {title}")`.

#### 3. Cursor Placement & Continuation
When completion is accepted at the end of the line:
`append_continuation` appends `\n  - `, positioning the caret directly on the first indented note bullet.

### 5.3 Typing Alias & Rewrite Rules (`src/native/capture_language/rewrite.rs`)

#### 1. Bullet-Start `/` Alias (`- /` -> `- #`)
Because `drawer_bullet_probe` now returns `Some(Some(DrawerBulletCompletion))` for `DrawerBulletTarget::ExistingNotebook` and `NewNotebook`, `expand_hash_alias` naturally validates that candidate `"- #"` yields a valid completion field (`CompletionContext::Drawer` / `Section`).
**Result:** Typing `- /` on a bullet line under a notebook route instantly expands to `- #` and pops up the section completion menu!

#### 2. Route-Glued `/` Alias (`@notebook/` -> `@notebook#`)
In `expand_hash_alias` (around line 1322):
When `raw_text` ends with `@route/`, if `route` is a notebook route, exempt it from the block-id check and swap `/` to `#`. This ensures `@dev_tools/` immediately expands to `@dev_tools#` and opens the section completion palette.

### 5.4 Capture Planning & Execution (`src/native/capture/`)

#### 1. Multi-Section Notebook Batch Planning (`notebook_note.rs`)
In `plan_notebook_note_item`:
When the capture item contains first-level authored bullets:
- Scan first-level bullets for leading `#`:
  - If a bullet starts with `- #<slug>`:
    - Resolve `<slug>` against the notebook's H2 sections using `resolve_notebook_section`.
    - If `Existing`: Target the existing `## Heading`.
    - If `Create`: Append `## <Title>\n\n` at EOF and target it.
    - If `NearMiss`: Return `CaptureError::usage_code(..., "notebook_section_near_miss")`.
    - Collect all nested sub-bullets under this section bullet and plan them as note rows under that section.
  - If a first-level bullet does **not** start with `#`:
    - Plan it as a top-level note bullet (inserted before the first `## Heading`).
- **Guarded Transaction:** All edits across all sections are planned into in-memory snapshots and committed atomically. If any section fails (e.g. near-miss conflict), the entire capture rolls back.

#### 2. Seeding Sections in Notebook Creation (`notebook_create.rs`)
In `seed_body`:
Support both:
- Existing ALL-CAPS section titles (`is_project_section_title`).
- New `- #<slug>` section bullets with nested notes.
Both cleanly translate to:
```markdown
## <Title Case Heading>

- note 1 [created::YYYY-MM-DD]
- note 2 [created::YYYY-MM-DD]
```

---

## 6. Comparison of Implementation Approaches

To assist in decision-making, the following table compares the three viable architectural models:

| Dimension | Model 1: Strict Drawer Analogy | Model 2: Explicit Section Slug (Recommended) | Model 3: Headings in Bullets |
| :--- | :--- | :--- | :--- |
| **Bullet Syntax** | `- GIT\n  - note` | `- #git\n  - note` | `- ## Git\n  - note` |
| **Completion Trigger** | `- #` or `- /` | `- #` or `- /` | `- #` or `- /` |
| **Completion Replacement** | `GIT\n  - ` | `#git\n  - ` | `## Git\n  - ` |
| **Glued Symmetry** | Collides with task drawers | Perfect agreement with `@nb#git` | Awkward / Non-standard |
| **Prose Note Collision Risk** | **High** (all-caps notes become sections) | **Zero** (explicit `#` sigil required) | **Low** (explicit `##` sigil required) |
| **Markdown Cleanliness** | Looks like a task drawer | Minimalist, clean, Bob-idiomatic | Looks like a nested markdown heading |
| **Near-Miss Safety** | Relies on drawer resolver | Shares exact notebook H2 resolver | Shares exact notebook H2 resolver |
| **Creation Support** | ALL-CAPS catalog recents | Slugs + Quoted `#"Title"` | Verbatim heading titles |
| **Implementation Complexity** | Medium (re-uses drawer engine) | Low-Medium (cleanly scoped extension) | Medium-High (special heading parser) |

### Why Model 2 (Explicit Section Slug) Wins
1. **Zero Semantic Pollution:** Notebooks remain clean knowledge repositories without task drawers.
2. **Syntactic Clarity:** Every user immediately understands that `- #` denotes an H2 section, directly mirroring `@notebook#section`.
3. **Typing Ergonomics:** With the `/` alias, typing `- /` expands to `- #`, opens completion, and pressing Enter inserts `#section\n  - `, placing the cursor right where note drafting begins.

---

## 7. Recommended Adjustments to the Requirements

Based on this research, we recommend three specific refinements to the user's original requirements:

1. **Retain `#` on Section Bullets (Do NOT strip `#` to bare ALL-CAPS):**
   *Adjustment:* When completion resolves a section in a notebook bullet, the replacement should be `- #<slug>\n  - ` (e.g., `- #git\n  - `), NOT bare `- GIT\n  - `.
   *Reason:* Notebook notes frequently contain sub-bullets and capitalized words. Retaining `#` avoids fatal ambiguity between section headers and prose notes with children.
2. **Preserve Exact Notebook Near-Miss Semantics in Bullet Completion:**
   *Adjustment:* When the user types an unquoted slug that is within Levenshtein distance 2 or a prefix of an existing section (e.g., `- #gi` when `## Git` exists), the completion menu must offer the quoted create row (`#"Gi"`), and bare unquoted near-miss creation must be refused at commit time.
   *Reason:* Preserves `resolve_notebook_section`'s contract and prevents accidental near-duplicate headings.
3. **Explicitly Support Draft-Wide `@@<notebook>`:**
   *Adjustment:* Ensure that bullet section targeting works seamlessly under a draft-wide `@@<notebook>` declaration, not just item-local `@<notebook>`.
   *Reason:* Draft-wide capture is the primary mode for bulk capture sessions; users should be able to declare `@@dev_tools` at the top and write multiple `- #section` bullet blocks below.

---

## 8. Verification & Implementation Roadmap

### Phase 1: AST & Lexer (`src/native/capture_language/`)
- Add `ExistingNotebook` and `NewNotebook` variants to `DrawerBulletTarget`.
- Update `classify_target` in `drawer_bullet.rs` to handle `EditorMode::NotebookNote`, `NotebookSubNote`, and `NotebookCreate`.
- Update `apply_global_destination` in `editor_parse.rs` to propagate notebook bullet targets from `@@notebook`.
- Update `expand_hash_alias` in `rewrite.rs` to support `@notebook/` -> `@notebook#` and `- /` -> `- #`.

### Phase 2: Completion Engine (`src/native/capture_complete/`)
- Add `DrawerScope::NotebookSection` to `Target` in `drawers.rs`.
- Populate target drawers from `capture_language::notebook::notebook_sections`.
- Implement `choose_bullet` for `NotebookSection` to generate `- #<slug>` and `- #"<Title>"` replacements.
- Wire `append_continuation` to append `\n  - ` and set `cursor_after`.

### Phase 3: Planner & Transaction Execution (`src/native/capture/`)
- Update `plan_notebook_note_item` in `notebook_note.rs` to parse first-level `- #<slug>` bullets as section boundaries.
- Group child sub-bullets under their resolved section and append them after the last note in that section.
- Update `notebook_create.rs` to recognize `- #<slug>` section bullets alongside existing ALL-CAPS bullets when seeding new notebooks.

### Phase 4: Verification Suite
- **Unit Tests (`src/native/capture_complete/tests/`):**
  - Verify `- #` completion on existing notebook lists existing H2s in document order.
  - Verify `- /` typing alias triggers section completion.
  - Verify `@notebook#` completion and `@notebook/` alias.
  - Verify near-miss queries offer quoted create rows.
  - Verify `- #` completion on `notebook_create` (`@parent^id@ %n`) offers catalog and create rows.
- **Integration Tests (`tests/cli/capture/`):**
  - Multi-section capture in a single draft (`@nb\n- #sec1\n  - n1\n- #sec2\n  - n2`).
  - Creation of new H2 sections at EOF.
  - Top-level notes mixed with section notes in a single draft.
  - Atomic rollback on near-miss refusal.
