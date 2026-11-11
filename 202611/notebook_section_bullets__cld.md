# Notebook Section Bullets: targeting notebook `##` sections from capture

*Researcher `cld` · 2026-11-11 · bob-cli at `01c8e822` (grammar 25), installed `bob` built
2026-11-11, Bob Mac Capture at `origin/master`*

## TL;DR

- **About half of the request already exists.** `@<notebook>#` already completes the
  notebook's real `##` sections, offers a `New section “…”` row, and creates a missing
  section when you commit. An `@nb#section` header line followed by bullets already files
  each bullet into that section. When a new notebook is created with
  `@parent^id@ %n`, ALL-CAPS bullets that have nested bullets already become `##`
  sections. **What's missing is the bullet-start `#` in notebook drafts.** Today that
  `#` opens no menu, has no `/` alias, and gets no highlight. It is also written to the
  file as a literal Obsidian tag, without any warning.
- **Verdict: build it, framed as the notebook twin of drawer bullets, not as new
  syntax.** One rule then covers tasks, project notes, and notebooks: *a first-level
  ALL-CAPS bullet with nested notes is a container. Under a task the container is a
  drawer; in a project note or notebook body it is a `##` section. A `#` at the start of
  such a bullet is the typing shortcut that completes the container's name.* This also
  fixes a real inconsistency today. The same draft bullet becomes a section when it
  creates a notebook, but a note with a child when it targets an existing notebook.
- **First, fix four bugs found while testing (§2.3).** The drawer menu wrongly opens on
  notebook note bullets. `%n` creation writes a later plain bullet into the section
  bullet before it. Section-start `#` is written to the file as a literal tag. Notebook
  list output says "tasks".
- **Upgrade the existing `@nb#` menu instead of duplicating it.** Give it the drawer
  menu's quality: groups, counts and age, consequence lines, refused rows, and no
  `New section “Tr”` row while you are still typing toward `Troubleshooting`.
- **Requirement changes I'm making**, each called out in §4: section bullets only where
  bullets land directly in the notebook body; no empty sections; tag-leading notes in
  notebook lists need `\#`; a notebook-only section catalog gated by recent use; and the
  `/` alias decided without vault access.

---

## 1. Reading the request

| Request bullet | My reading |
| --- | --- |
| "`#` (or `/`) at the start of a bullet completes known notebook sections" | A first-level `- #` (or `- /`) in a draft whose bullets land in a notebook body opens a section menu. |
| "good support when using the project capture syntax" | Creating a notebook with the project-capture seal: `@parent^id@ %n` plus bullets. The notebook does not exist yet, so its "known sections" come from the draft and from other notebooks. |
| "capturing new notes to an existing project by targeting it with the `@<notebook>` syntax" | I read "project" as a slip for **notebook**: an `@nb` header line followed by bullets. |
| "completion for existing sections and creation of new ones using `@<notebook>#`" | **Already shipped** (see §2.1). The real gap there is quality, not existence. |
| "intuitive, reliable, beautiful" | Intuitive: one rule shared with drawers. Reliable: menu, parse, preview, and commit use one resolver, and errors are loud instead of silent. Beautiful: rich rows, a clear preview, and draft text that reads like the result. |

---

## 2. What exists today (verified)

I verified everything below by running the installed `bob` against a scratch vault: an
area `dev`, a notebook `dev_tools` with `## Git`, `## Shell Shortcuts`, and
`## Troubleshooting`, and a notebook `linux`. I used `capture-complete`,
`capture-parse`, `capture-rewrite`, and `capture --dry-run`. I also read the code paths.

### 2.1 Already shipped

| Draft | Behavior today | Code |
| --- | --- | --- |
| `@dev_tools#` | `context: "section"` lists the real H2s in document order (`Git`, `shell-shortcuts`, `Troubleshooting`). The replacement is the bare title when it resolves back to that heading, else the slug, else a quoted title. | `capture_complete/candidates.rs::notebook_section_candidates` |
| `@dev_tools#perf` | Adds a `notebook_section_create` row, `New section “Perf”`, with replacement `perf`. | same |
| `@dev_tools#tr` | `Troubleshooting` plus `New section “Tr”` with replacement `"Tr"` (quoted, because a bare `tr` would be refused as a near miss). | same |
| `@dev_tools#tr` + `- note` (commit) | Refused: `no section 'tr' … did you mean '#troubleshooting'? Write '#"Tr"' to create it`. | `capture_language/notebook.rs::resolve_notebook_section` |
| `@dev_tools#troubleshooting` + bullets | List mode: each bullet becomes a stamped note in that section, and each note can keep **nested detail**. | `capture/notebook_note.rs` |
| `Neovim notes @dev^nvim@ %n` + `- TROUBLESHOOTING` / `  - check :checkhealth` | Creates `## Troubleshooting` with that note. | `capture/notebook_create.rs::seed_body` |
| `@dev_tools/` | The `/` alias types `#` (`Typed # for /`). | `capture_language/rewrite.rs::expand_hash_alias` |

Section resolution rules (`resolve_notebook_section`):

- A selector matches an exact title (case-insensitive) or a whole slug.
- An **unquoted** selector that is a slug prefix of a heading, or within edit distance
  **2** of one, is refused as a near miss.
- A quoted selector creates its exact title.
- Any other missing selector creates a Title Case `##` at the end of the file.

For comparison, the drawer resolver refuses at **edit distance 1**, and it creates new
drawers using the catalog's most common spelling.

### 2.2 Today's gaps for the request

| Draft (cursor at end) | Today |
| --- | --- |
| `@dev_tools` / `- #` | `context: null`: no menu. |
| `@dev_tools` / `- /` | Alias does **not** fire (`changed: false`). |
| `Neovim notes @dev^nvim@ %n` / `- #` | `context: null`. |
| `@dev_tools` / `- #troubleshooting` / `- plain note` (commit) | Writes a **top-level note whose text is literally `#troubleshooting`**, i.e. an Obsidian tag, without any warning. |
| `capture-parse` of the above | Only a `route` span. No span marks the `#troubleshooting`, and there is no diagnostic. |
| `@dev_tools` / `- TROUBLESHOOTING` / `  - check dmesg` | A note "TROUBLESHOOTING" with a child. The same bullet under `%n` becomes a **section**. |

### 2.3 Bugs found along the way (fix regardless of this feature)

1. **The drawer menu opens on notebook bullets.** `Some note @dev_tools` / `- #fut`
   returns `context: "drawer"` with the row `FUT … new`, offering to create a *drawer* in
   a notebook. `@@dev_tools` / `A note` / `- #` and `@dev_tools+x` / `- #` also return
   `context: "drawer"`. The commit then writes the literal child `- #future-work`. So
   the menu and the commit disagree, which breaks the "one resolver serves the menu,
   parse, preview, and commit" rule (`decisions:capture-bullets-mirror-the-task-block`).
   - **Cause:** `drawer_bullet::classify_target` decides from the lexical editor mode
     (`Task`). The completion engine never asks the notebook route policy before serving
     `bullet_drawer_candidates`.
   - **Knock-on effect:** the lexical `/` alias also fires there, so `- /` becomes `- #`.
2. **`%n` creation moves later plain bullets into the section before them.**
   `@dev^nvim@ %n` with `- TROUBLESHOOTING` / `  - check` / `- plain top note` writes
   `plain top note` *under* `## Troubleshooting`. In the draft, `- plain top note` is a
   sibling of the section bullet, so it belongs in the top region (before the first
   `##`). **Cause:** `seed_body` writes bullets strictly in draft order.
3. **`- #section` in notebook drafts is written as a literal tag** (rows in §2.2), both
   in `@nb` lists and in `%n` creation (`- #keymaps` → note `#keymaps`).
4. **Wrong noun:** `@dev_tools` + two bullets prints `list  dev_tools.md · 2 tasks`.
   `print_list_summary` uses `ListKind::Tasks` for a notebook list with no section.

Bug 1 is the strongest evidence that this feature is wanted. The drawer machinery
already "thinks" notebook bullets are an under-task position. It just picks the wrong
container kind.

### 2.4 How Bryan's vault uses sections (read-only `bob notebooks list -f json`)

- 37 notebooks across 13 roots. **Most have no sections at all**, including the
  high-traffic ones: `dev_ideas` (68 notes), `sase_ideas` (61), `gtd_ideas` (39),
  `nvim_plugins` (38), `vim` (35), `dev_tools` (30).
- Existing headings are mostly leftovers from migration: `Legacy Notes` (5 notebooks),
  `@FOOTNOTE` (4), `Migrated Zorg Inbox`, dated meeting headings with inline fields and
  block IDs, `[[nj#^…|Union County]]`, `#work [[goog]]`.
- Real hand-made topical sections are rare: `coc.nvim`, `2024 taxes (2023 tax year)`,
  `Reference`, `Meetings`, `HABITS TO TRACK`, `RESTAURANTS LIKED`.
- `last_note` is `null` for **every** notebook, because the migrated notes carry no
  `[created::]` stamps.

What this means for the design:

- A naive "known sections across the vault" list would suggest junk (`Legacy Notes`,
  `@FOOTNOTE`). The cross-notebook group must be **gated by recent use** (a section that
  received a stamped note in the last 90 days). With today's data that group is empty
  and fills naturally with real use.
- Most of the value is **forward-looking**: sections are cheap to make only once this
  feature exists. That's fine, but it argues for a lean v1 (§6).

---

## 3. Critique: is this a good idea?

**Yes, with the scope tightened.** The case for it:

1. **It removes an inconsistency instead of adding a feature.** `- TROUBLESHOOTING` plus
   nested notes already means "section" in `%n` creation, "drawer" under a task, and
   "section" on a project note's `^prj`. Only an existing-notebook list reads it as a
   note with a child.
2. **The slot is free.** In a task list (`@dev` + bullets), a bullet-start `#` is
   refused today (`drawer_bullet_position`: "list bullets are tasks, so `#` cannot start
   one…"). Giving `- #` a meaning in notebook lists collides with nothing in the task
   grammar.
3. **Most of the machinery exists.** It's already built: the shortcut lexer
   (`drawer_bullet::scan_leading`), H2 resolution (`resolve_notebook_section`), the
   section writer (`notebook_note.rs`), the menu engine and its row contract
   (`capture_complete/drawers.rs`), the Mac's grouped drawer menu
   (`CaptureDrawerMenuView`), and the catalog cache (`capture_drawers.rs`, 60 s time to
   live (TTL), per-file mtime fingerprints).

What I'd push back on:

- **Don't rebuild `@nb#`.** It works. Spend that effort on making its rows as good as
  the drawer menu's.
- **A depth limit is part of the deal.** Authored drafts allow two bullet levels. Under a
  section bullet, the nested level *is* the note, so section-bullet notes are one line
  with no detail. That's the same limit drawer notes have. The `@nb#section` header
  form keeps note-plus-detail depth, so the guidance is: section bullets for quick
  multi-section dumps, `@nb#section` headers for rich notes. State this in the docs and
  show it in the preview. Revisit only if authored bullets gain a third level, which is
  already the reopen condition of `decisions:capture-bullets-mirror-the-task-block`.
- **ALL-CAPS loses case.** `- SQL` with children creates `## Sql`, and `MACOS TIPS`
  becomes `## Macos Tips`. That matters more in dev notebooks than in project notes. §5.3
  makes this lossless whenever the user expresses intent, without guessing.
- **Section sprawl versus child notebooks.** Notebooks already nest (`git` under
  `dev_tools`). Easy sections invite many tiny ones. Proposed guidance: a section groups
  notes *inside one topic*. A durable subtopic that deserves a summary and a catalog row
  should be a child notebook. The menu's counts and ages (§5.5) make sprawl visible.
- **Tag-leading notes.** In a notebook list, `- #idea try nixos` is a plausible
  Obsidian-tag note, and under this design it becomes a section-shortcut error.
  Drawers made the same trade in grammar 4. The refusal is loud and `\#idea` keeps the
  tag. I accept that, but it is a breaking change and is called out below.

**Would I take a different approach?** No to the overall shape. Yes to some framing
(§4). The alternatives I weighed and rejected are in §7.

---

## 4. Requirement changes (explicitly called out)

| # | Change | Why |
| --- | --- | --- |
| **R1** | Treat `@nb#` completion and creation as **done**. Change that requirement to "upgrade the `@nb#` menu to the drawer-menu contract", with the same rows as the bullet menu. | It already exists (§2.1). |
| **R2** | Section bullets apply **only where bullets land directly in a notebook body**: an `@nb` header list and `@parent^id@ %n` creation. Under a notebook note (`Text @nb` + bullets, `@@nb` items with bullets, `@nb+id`), bullets are opaque detail: a leading `#` stays literal, with no menu and no error. Under an `@nb#section` header, `- #x` is a position error, mirroring `@route+id#drawer`. | The drawer rule is "only bullets that land directly under a task name a drawer". The notebook mirror is "only bullets that land directly in the notebook body name a section". Note detail stays opaque, as `decisions:notebook-routes-write-notes` requires. |
| **R3** | The bullet form is the **ALL-CAPS title** with nested notes. `- #…` is a typing shortcut that the menu rewrites to the bare title. `- #slug` and `- #"Exact Title"` remain valid text to commit. | Same rule as drawers and project notes, and it is how `%n` creation already works. |
| **R4** | **No empty sections**: a section bullet with no nested notes is refused (`empty_section_bullet`). The menu always opens a nested `  - ` after the title. | Same as "capture never creates an empty drawer". Scaffolding sections into a new notebook can be added later if wanted (§8 Q3). |
| **R5** | Plain first-level bullets in a notebook body always go to the top region (before the first `##`), **whatever their draft order** relative to section bullets. | Fixes bug 2. A sibling of a section bullet in the draft is not inside that section. |
| **R6** | Breaking change, grammar **26**: ALL-CAPS bullets with nested notes in `@nb` lists become sections, and `- #tag text` at a notebook-body bullet start is refused (`section_bullet_text`). `\#tag` keeps a tag. | Unifies the meaning. The refusal is loud, never silent. |
| **R7** | "Known sections" means, in order: **this notebook's H2s**, then **sections typed earlier in this draft**, then **recent sections in other notebooks** (got a stamped note in the last 90 days), then **one create row**. Notebook sections get their own catalog *scope* and are never mixed into the drawer catalog. | §2.4: an ungated vault-wide list suggests junk. Drawer names (REQUIREMENTS, FUTURE WORK) are about structuring work. Notebook sections are topics, and mixing them makes both menus worse. |
| **R8** | The `/` alias at a list-header bullet start is decided **lexically**. It fires after any whole-line `@route` header or on a `%n` creation item. On an area list, the resulting `#` gets the existing "list bullets are tasks" refusal. | `capture-rewrite` is contractually lexical: "never opens the vault … takes no --bob-dir" (V4 in `research:202611/bob_notebooks/bob_notebooks.md`). The over-fire only happens where a bullet-start `#` is already invalid, and Undo, Space, or Esc reverses it. |
| **R9** | When creating a new section from a slug, **keep any uppercase letters the user typed**: `#API-keys` → `API Keys`, `#api-keys` → `Api Keys`. Apply this to both `@nb#…` and the bullet's new row. An ALL-CAPS literal keeps the current rule (catalog spelling, else Title Case). | A lossless rule with no heuristics: what you type is what you get, and all-lowercase means Title Case. |

---

## 5. Recommended design

### 5.1 One rule, five positions

| Draft shape | Where its first-level bullets land | `- #…` / ALL-CAPS-with-children means | Today | Proposed |
| --- | --- | --- | --- | --- |
| `New task @dev` + bullets; `@dev^x@` + bullets; `@dev+id` (no note) + bullets | directly under a task / `^prj` | **drawer** (H2 section on a project note) | ✅ | unchanged |
| `@dev` header + bullets (area/project list) | bullets *are* tasks | refused: "list bullets are tasks" | ✅ | unchanged |
| **`@nb` header + bullets** | **directly in the notebook body** | **section bullet** | literal tag / note with child | **section** |
| **`@parent^id@ %n` + bullets** | **directly in the new notebook body** | **section bullet** | ALL-CAPS ✅, `#` literal | **section, plus the `#` shortcut and menu** |
| `@nb#Sec` header + bullets | inside `## Sec` | refused: position | literal tag | `section_bullet_position` |
| `Text @nb` + bullets; `@@nb` item + bullets; `@nb+id` + bullets | under a note | literal (opaque detail) | drawer menu leaks | **no menu; literal** |

### 5.2 What the draft looks like, and what it writes

Existing notebook, menu-assisted:

```text
@dev_tools
- GIT
  - `git switch -` returns to the previous branch
- TROUBLESHOOTING
  - `lsof -i :8080` shows who owns the port
- Prefer `fd` over `find`
```

writes to `dev_tools.md`:

```markdown
# Developer tools

- Use fd instead of find [created::2026-11-09]
- Prefer `fd` over `find` [created::2026-11-11]        ← top region, despite draft order

## Git

- git switch - returns to previous branch [created::2026-11-09]
- `git switch -` returns to the previous branch [created::2026-11-11]

## Shell Shortcuts
…
## Troubleshooting

- lsof -i :8080 [created::2026-11-09]
- `lsof -i :8080` shows who owns the port [created::2026-11-11]
```

New notebook (the "project capture syntax" path):

```text
Neovim config notes @dev^nvim@ %n
- KEYMAPS
  - leader is space
- #"LSP Setup"                ← quoted because a bare ALL-CAPS title would give "Lsp Setup"
  - mason installs servers
- :checkhealth is the first stop
```

writes `dev_nvim.md` with the plain note in the top region, then `## Keymaps` and
`## LSP Setup` in draft order.

### 5.3 Resolution and writes (one resolver)

Extend `resolve_notebook_section` with a **literal** mode for ALL-CAPS bullet titles. The
menu, `capture-parse`, the dry-run, and the commit all call that one function, so they
cannot disagree.

1. **Existing heading:** a case-insensitive title match, or a whole-slug match for a
   `#slug`. The file's spelling always wins, so `COC.NVIM` lands in `## coc.nvim`.
2. **Near miss:**
   - For `#slug`: keep today's refusal (prefix or edit distance ≤ 2,
     `notebook_section_near_miss`).
   - For an ALL-CAPS literal: deliberate authored text, so give a **warning**, not a
     refusal. `capture-parse` warns and the preview reads `new section Troubleshoting ·
     did you mean Troubleshooting?`. This matches drawer bullets, where the literal is
     treated as exact.
3. **Create** (the spelling is decided in this order):
   - a quoted literal: verbatim;
   - a `#slug` with typed capitals: those capitals are kept (R9);
   - otherwise the most common spelling of that key in the **notebook-section catalog**
     (so `COC.NVIM` in a new notebook creates `## coc.nvim` if any notebook already has
     one);
   - otherwise Title Case.
4. **Reserved:** `Notebooks` (the generated catalog heading) is refused, as
   `@dev#notebooks` already is with `notebooks_section_generated`.
5. **Unspellable headings** (`#work [[goog]]`, `@FOOTNOTE`, anything outside
   `is_project_section_title`'s character set) appear as **refused rows**. The copy
   reuses the existing project-section text: "uses characters an ALL-CAPS bullet cannot
   spell; capture into it with `@python#…`". The quoted `- #"…"` form is the
   alternative.

Write rules:

- **Grouping:** plain notes go to the top region, after the last top-region note. Section
  notes go after the last note of their section. Missing sections are created at end of
  file in first-mention draft order. Repeated section bullets with the same key merge.
- **Each nested line is one stamped note:** `[created::]` plus an optional trailing
  `^id`, which reuses the `@nb^id` block-ID rules.
- **Transaction:** the whole draft is one all-or-nothing guarded write, as now.

### 5.4 Grammar and parse contract

- **Lexer:** reuse `drawer_bullet::scan_leading`. Add a target variant
  `DrawerBulletTarget::NotebookBody { route, creating: bool }` (or a sibling
  `ContainerBulletTarget`). Set it in `notebook.rs` when the claim is a list or a create,
  so it is never inferred from editor mode (that inference is bug 1).
- **`capture-parse`:** add a span `kind: "notebook_section"` with `notebook: true`,
  `title`, `key`, and `section_action: existing|create`. Add diagnostics with these
  codes:
  - `section_bullet_text`
  - `empty_section_bullet`
  - `section_bullet_position`
  - `notebook_section_near_miss` (an error for a slug, a warning for a literal)
  - `notebooks_section_generated`
- **Grammar bump** 25 → 26; raise the Mac's minimum grammar accordingly.
- **Error copy** (Bob-authored, teaching the current grammar only):
  - `` `- #troubleshooting` names a section, so it takes no text: nest `lsof …` beneath it (`- TROUBLESHOOTING` / `  - lsof …`), or write `\#troubleshooting` to keep a tag ``
  - `` this list already files every bullet into ## Troubleshooting; drop `#troubleshooting` from `@dev_tools` to use section bullets ``
  - `` `- #ideas` has no notes beneath it; nest them as `  - …` (capture never creates an empty section) ``

### 5.5 The menu: drawer-grade rows for both `@nb#` and `- #`

Use one new completion context, **`notebook_section`**, for both the glued `@nb#…` form
and the bullet form. Rows reuse the drawer row schema (`DrawerCandidate`), so the Mac can
reuse `CaptureDrawerMenuView`:

| Field | Bullet form | Glued form |
| --- | --- | --- |
| `replacement` | `KEYMAPS\n  - ` (bare ALL-CAPS title plus an opened nested bullet), or `#"LSP Setup"\n  - ` when the bare title would not keep its spelling | `#keymaps` / `#"LSP Setup"`, as today |
| `group` | `notebook` · `draft` · `recent` · `new` | `notebook` · `recent` · `new` |
| `group_title` (new, Bob-authored) | `In Developer tools` · `Earlier in this draft` · `Other notebooks` | same |
| `detail` | `3 notes · 2 days ago` / `empty` / `used in 2 notebooks · last week` | same |
| `consequence` | `Adds after “lsof -i :8080” in Troubleshooting` / `Creates ## Perf at the end of Developer tools` / `Starts ## Keymaps in the new notebook` | same |
| `refused` | resolver's own reason (reserved, unspellable, mismatch) | same |
| `creates`, `cursor_after`, `note_count`, `last_note` | as drawers | as drawers |

The response `target` carries `{route, title, breadcrumb, creating}`, so the header
caption reads `📓 Developer tools · dev`, or `📓 New notebook · Nvim · dev` during
creation.

Ranking and noise rules:

- **Empty query:** this notebook's sections in document order, then draft sections, then
  up to 5 recent rows. **No create row.**
- **Typed query:** prefix matches first, then substring matches, within each group.
- **Create row:** only when no row claims the query **and the query is not a strict
  prefix of an existing section's title or slug**. This removes today's
  `New section “Tr”` while you type toward Troubleshooting. An edit-distance near miss
  still gets a create row, with detail `did you mean Troubleshooting?`.
- **Bob-authored group titles:** the Mac's drawer presentation hard-codes
  `On this task`, `Recent`, `＋ New drawer`. With `group_title` and a
  `new_row_prefix` (`＋ New section`) sent by Bob, the same view renders both menus.
  That keeps the client thin (`decisions:mac-capture-is-a-thin-client`).

Catalog:

- Add a `scope` (`task` | `project` | `notebook`) to each entry in the existing drawer
  catalog cache, plus a per-section `last_note`. Bump `DRAWER_CATALOG_VERSION`.
- The drawer menu reads `task` and `project` entries; the notebook menu reads `notebook`
  entries. There is no second vault scan, and the 60 s TTL and mtime fingerprints carry
  over.

### 5.6 Preview and highlighting (the "beautiful" part)

- **Highlighting:** the editor colors the section bullet title like a drawer bullet. The
  shortcut `#` is highlighted while incomplete.
- **Batch preview:** group rows by section instead of a flat `1/3, 2/3, 3/3`:

  ```text
  📓 3 notes → Developer tools
     › Git                     `git switch -` returns to the previous branch
     › Troubleshooting         `lsof -i :8080` shows who owns the port
     · top                     Prefer `fd` over `find`
  ```

  A created section gets the existing `New section · Perf` badge
  (`CaptureNotebookPresentation.newSectionBadge`).
- **CLI human output:** keep the shipped `📓 Note → Title › Section` and
  `› new section Name` forms, and fix the list summary noun (`· 3 notes`).

### 5.7 `/` alias

- The lexical `completion_field_at` gains a `SectionBullet` field for a first-level bullet
  start under a whole-line `@route` header or a `%n` creation item, so
  `expand_hash_alias` accepts it the same way it accepts `Drawer`.
- The vault-aware `capture-complete` then:
  - serves the menu for notebook routes;
  - returns an empty success for area or project lists, where the existing refusal
    explains.
- After bug 1 is fixed, `Text @nb` + `- /` still becomes `#` (a lexical over-fire that
  already happens today). It now opens no menu and commits literally, and the
  alias-escape rules still apply. This is a known, accepted cost under R8.

---

## 6. Implementation phases

| Phase | Repo | Scope | Size |
| --- | --- | --- | --- |
| **P0: fixes** | bob-cli | Bug 1: the engine consults the notebook policy before `bullet_drawer_candidates`. Bug 2: `seed_body` writes top-region notes first. Bug 4: list noun. Regression tests for every draft in §2.2/§2.3. | S |
| **P1: grammar 26** | bob-cli | `NotebookBody` target; literal mode in `resolve_notebook_section`; writer grouping (R5); parse spans and diagnostics; R9 typed capitals; capture docs. | M |
| **P2: menu** | bob-cli | `notebook_section` context for bullet and glued forms; catalog `scope` and `last_note`; prefix-suppressed create row; `SectionBullet` lexical field and alias; `capture-complete --help`. | M |
| **P3: Mac** | bob-mac-capture | Render `notebook_section` through the drawer menu view using Bob's `group_title`; highlight span; section-grouped preview; raise minimum grammar. Gate on the exact-SHA macOS CI run. | S–M |
| **P4: memory/docs** | bob-cli (+ vault memory) | New decision record (§9); glossary updates for **Notebook** and **Task Drawer** ("the notebook twin is a section bullet"); `docs/notebooks.md`, `docs/capture.md`, `docs/reference/capture-syntax.md`; Mac `docs/keyboard.md`. | S |

Test matrix (each run through parse, complete, dry-run, and commit, with assertions that
all four agree):

- `@nb` list containing existing, new, near-miss, quoted, unspellable, reserved, and
  repeated section bullets, mixed with plain notes in every order;
- `%n` creation with sections, `- #` shortcuts, and plain notes after sections;
- position errors under `@nb#Sec`;
- opacity under `Text @nb`, `@@nb`, and `@nb+id`;
- area list `- #` still refused;
- alias over-fire on an area list;
- CRLF/BOM notebooks;
- fenced `##` lines ignored;
- the `## Notebooks` catalog heading refused.

---

## 7. Alternatives considered and rejected

| Alternative | Why not |
| --- | --- |
| **Keep the `#selector` in the draft** (`- #git` stays `- #git`) | Reads like an Obsidian tag. It contradicts the drawer-bullet decision, which rejected a `- #drawer text` shorthand because it cannot survive the bare-title rewrite, and it gives notebooks a second section-bullet spelling. (Still accepted as text to commit, as with drawers.) |
| **Markdown heading inside a bullet**, `- ## Git` | Exact case and no clash with prose, which is the strongest alternative. But it is a second container spelling next to ALL-CAPS (drawers, project notes, `%n`), and it reads oddly in Obsidian. **Reopen** if acronym loss or ALL-CAPS-prose clashes bite in practice. |
| **Bare heading lines** in a list (`@dev_tools` / `## Git` / `- note`) | Mirrors the file most literally and allows note-plus-detail depth. But it is a new non-bullet line class in the authored grammar, the `/` alias can't fire at a line start (Go To owns that), and it doesn't match what was asked. |
| **`@@nb#section`** | Removed on purpose on 2026-10-31 and refused with `invalid_global_destination` (`decisions:notebook-routes-write-notes`). |
| **A vault-aware `capture-rewrite`**, or Mac-supplied `--notebook-route` hints | Breaks the lexical rewrite contract (V4) or spreads route knowledge into the Mac. The over-fire it would prevent is small and recoverable. |
| **Section bullets for area and project lists too** | `@area#Sec` + bullets already writes plain bullets into a section, while `@area` + bullets writes tasks. Making nesting switch the item kind would confuse things, and areas keep tasks in `## Tasks` for Ready-lane grouping. |
| **Merging notebook sections into the drawer catalog** | Topics and work structure would pollute each other's menus (§2.4). |
| **Allowing empty sections** | Inconsistent with drawers, and leaves clutter. Could return later as an explicit `%n` scaffold. |
| **Meaning that depends on the vault** (ALL-CAPS is a section only if the heading exists) | Already rejected in `plan:202611/capture_list_section_names.md`: "the meaning would also depend on vault contents." |

---

## 8. Open questions for Bryan

1. **ALL-CAPS versus `- ## Title`.** I recommend ALL-CAPS for parity with drawers and
   `%n`. Do you agree, given that acronyms need `#"SQL Tips"` when creating?
2. **The R6 break.** Hand-typed ALL-CAPS bullets with children in existing-notebook lists
   become sections, and `- #tag text` at a notebook-body bullet start errors (use
   `\#tag`). OK?
3. **Scaffolding.** Should `%n` creation allow empty section bullets as a skeleton, or
   keep "no empty sections" everywhere? I recommend no for v1.
4. **R9.** Keep typed capitals when creating from a slug (`#API-keys` → `API Keys`), for
   `@nb#` as well?
5. **Near-miss threshold.** Notebooks use edit distance ≤ 2 and drawers use ≤ 1. Align
   them? I lean toward keeping 2 for notebooks, because section names are fewer and
   longer.

---

## 9. Recommended solution

Ship **notebook section bullets** as the notebook twin of drawer bullets:

1. **P0 first.** Fix the drawer-menu leak on notebook note bullets, `%n` creation moving
   plain bullets into the preceding section, and the "tasks" noun. These are real bugs
   today and are independent of the feature.
2. **Grammar 26, one rule.** In a notebook body (an `@nb` header list or `%n`
   creation), a first-level ALL-CAPS bullet with nested notes files those notes into
   that `##` section. `- #` is its typing shortcut. Plain bullets go to the top region.
   An existing heading's spelling wins, then the notebook-section catalog's spelling,
   then Title Case. Quoted `#"…"` creates exactly. No empty sections. Position, text, and
   reserved-name refusals are loud and bob-authored.
3. **One menu for `@nb#` and `- #`:** the `notebook_section` context with drawer-grade
   rows. Groups are *In this notebook* → *Earlier in this draft* → *Other notebooks*
   (recent use only) → *＋ New section*, with Bob-authored group titles, counts, ages,
   and consequences. The create row is hidden while the query is a prefix of an existing
   section.
4. **A lexical `/` alias** at notebook-shaped bullet starts. The small over-fire on area
   lists is accepted and already refused there.
5. **Mac:** reuse `CaptureDrawerMenuView` with the Bob-sent labels, add the
   `notebook_section` highlight span, and group the batch preview by section.
6. **Record it.** Add a decision record, e.g. `notebook-section-bullets` ("In a notebook
   body, an ALL-CAPS bullet with notes is a `##` section; `- #` completes it"). It
   should extend `notebook-routes-write-notes` and `capture-bullets-mirror-the-task-block`
   and partly supersede the "ALL-CAPS childful notebook bullet is a note" reading. Also
   update the Notebook and Task Drawer glossary terms.

This keeps one mental model across Bob ("ALL-CAPS with notes is a container; `#` names
it"), adds no new sigils, uses the one free grammar slot, and turns a silent
literal-tag mistake into a guided, previewed, all-or-nothing write.

---

## Appendix A: incidental finding outside this feature

**The notebook `created:` frontmatter has the wrong UTC offset.** On a host whose clock
read 13:01 UTC, `bob notebooks create … -d` wrote
`created: 2026-11-11T08:01:12+0000`. That is New York wall-clock time labelled as UTC,
five hours off.

- `BOB_NOW=2026-11-11T10:00:00-05:00` was ignored, while `BOB_NOW="2026-11-11 10:00"`
  gave `10:00:00+0000`.
- The capture `%n` path shows the same `+0000` form.
- `docs/notebooks.md` shows the intended form, `2026-11-09T09:14:00-05:00`.
- Dataview and other parsers will read these instants five hours early, which can shift
  the date for captures made after 19:00 local time.

## Appendix B: evidence index

- Scratch vault probes: `capture-complete` / `capture-parse` / `capture-rewrite` /
  `capture --dry-run` on every draft quoted in §2.
- Code read in bob-cli:
  - `src/native/capture_language/drawer_bullet.rs` (`scan_leading`, `classify_target`,
    `finish_execution_drawer_bullets`)
  - `src/native/capture_language/notebook.rs` (`resolve_notebook_section`,
    `notebook_sub_bullets` sets `drawer: None`, `provisional_create_sections`)
  - `src/native/capture/notebook_create.rs::seed_body`
  - `src/native/capture_complete/{drawers.rs,candidates.rs,model.rs}`
  - `src/native/capture_drawers.rs` (catalog scope, TTL, `is_drawer_title`)
  - `src/native/capture_project_note.rs` (`is_project_section_title`,
    `format_project_section_title`)
  - `src/native/capture_language/rewrite.rs::expand_hash_alias`
  - `src/native/capture/output.rs::print_list_summary`
- Code read in Bob Mac Capture:
  - `Sources/CaptureCore/CaptureDrawerMenuPresentation.swift` (hard-coded
    `Drawer` / `On this task` / `Recent` / `＋ New drawer`)
  - `Sources/CaptureCore/CompletionRowContent.swift` (`section` rows render as a plain
    heading with an `H2` badge)
  - `Sources/CaptureCore/CaptureNotebookPresentation.swift` (`newSectionBadge`)
- Memory: `decisions:notebook-routes-write-notes`,
  `decisions:capture-bullets-mirror-the-task-block`,
  `decisions:capture-sigils-say-where-what-how`; glossary `notebook`, `task-drawer`,
  `capture-alias`, `project-note-capture`, `bulk-capture`.
- Prior artifacts: `research:202611/bob_notebooks/bob_notebooks.md` (V4: lexical
  rewrite), `plan:202611/capture_list_section_names.md` (one slug rule; the menu inserts
  what resolves back; vault-dependent meaning rejected).
- Vault survey: `bob notebooks list -f json` (read-only), §2.4.
