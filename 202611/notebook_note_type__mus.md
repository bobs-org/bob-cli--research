# Notebook notes (`type: [[notebook]]`) — research report

*Researcher: mus · 2026-11-09 · single-turn swarm research, written independently.*

## Question

Should bob-cli gain a new Obsidian note file type `type: [[notebook]]` — a
task-free note holding only note bullets (optionally under H2 sections),
parented under an area, project, or another notebook — plus capture syntax to
create notebooks and append to them, a root-parent "Notebooks" render, and a
migration of orphaned vault notes into the first notebooks?

## Short answer

Yes, with adjustments. The vault has a real orphan problem this fixes (~304
untyped bullet-only notes with `parent:` links that resolve to nothing in the
typed tree), and the design has clean precedent inside the codebase (record
notes for config-declared types, ref notes for task-free notes, the
machine-owned Sub-projects line for managed children renders, the Add block ID
flow for ID prompts). But three parts of the proposal as written collide with
live grammar and need to change: bare `@@foo` cannot mean "append to notebook"
without breaking the global-declaration contract; `%n` should not gain a second
job; and the "required summary frontmatter" needs a precise shape and a writer
so it does not rot. Details and a recommended solution below.

## What exists today (verified in tree)

### Note types and the typed tree

- `src/native/projects/scan.rs` recognizes exactly two tree types:
  `frontmatter_is_area` (`type: [[area]]`) and `frontmatter_is_project`
  (`type: [[project]]`), plus `frontmatter_is_article` (`type: [[article]]`,
  used for section-selector identity matching). Ref notes are
  `type: [[ref]]`; record notes use config-declared ids (`docs/records.md`);
  reserved record ids are `project, area, ref, day, done, mail, article,
  type` — `notebook` is free.
- `walk_typed_notes` (`src/native/projects/scan.rs`) walks the vault and keeps
  only area/project notes (skipping `done/`, daily paths, `dash.md`). Every
  other consumer of "the tree" — `bob projects list/sync`, capture targets,
  ready caps, parent candidates — builds on this shape. A notebook type is
  therefore *ignored everywhere by default*, which is the safe starting point:
  the work is opting notebooks into exactly the walkers they need
  (parent-chain traversal, children listing) while keeping them out of the
  ones they must avoid (capture task routes, ready caps, review walk, stats
  homes, `projects sync` schedule propagation).
- Parentage is a `parent: "[[stem]]"` wikilink (`wikilink_target` in
  `scan.rs`). Root-parent derivation (`docs/pomodoro-homes.md`, R2) walks that
  chain; `root: true` on a project makes it its own root. A notebook parent
  chain (`notebook → project → area`) already works *if* chain walkers do not
  stop at "not area/project". That is the main traversal change: every
  `frontmatter_is_area || frontmatter_is_project` gate on a *chain walk*
  needs a third arm for notebook, while gates on *task residence* must keep
  excluding notebooks (see § Residence).
- `parent_notes.rs` / `capture_targets.rs` define the capture-target set
  (inbox, area, project, record). Notebooks must NOT become capture task
  routes — that is the whole point (task-free notes) — so they stay out of
  `scan_capture_targets`.

### Capture grammar touchpoints (all verified in `docs/capture.md`)

| Proposed syntax | Current meaning of that shape | Verdict |
| --- | --- | --- |
| `@foo^bar@` + `%n` (create notebook) | `@route^id@` creates a project note today | Reuse is natural, but `%n` is the wrong switch (see below) |
| `@@foo` (append note to notebook top) | Bare `@@route` is the draft-wide **global task destination declaration**; `@@foo#…`, `@@foo^id`, `@@foo:id`, `@@foo+id` are explicit errors teaching the `@@` spelling (`docs/capture.md` § on global declarations) | **Collision.** Bare `@@foo` cannot be both. The suffixed forms (`#`, `^`, `+`) live in currently-error space and are safe to claim |
| `@@foo#bar` (append under H2) | Currently an error (`Unsupported forms such as @@foo#Ideas … are errors`) | Safe to claim |
| `@@foo+baz` (sub-note under `^baz`) | `@route+id` is sub-bullet/Ensure-Next today; `@@…+…` is an error | Safe to claim as a notebook addressing form, but grammar must disambiguate from target-run spellings |
| `@@foo^some-id` (note with block ID) | Error space today | Safe; `capture-task-id` Add-block-ID flow exists for the prompt |
| `.` → `@`/`^`, `/` → `#` aliases | `capture-rewrite` sigil aliases (typed `.` after `@route` becomes `^`; `/` becomes `#` where the completion grammar opens a `#` menu) | Compose for free *if* the new grammar hooks into the same completion contexts (`task_parent`, section, block-ID pickers) |

### `%n` today

`%n` is the Pomodoro-note directive (`directive.rs`: `DirectiveKind::Note`),
rendered as `- <text>` with no stamp, no `#task`, no block ID — and it is
*refused* alongside any `@route` token, `s:<N>`, `$<N>`, `--route/--section/
--task` (`docs/capture.md`, "Pomodoro notes"). Giving `%n` "two related
purposes — notes and notebooks" overloads one glyph with context-sensitive
meaning across exactly the boundary (`@`-routed vs unrouted) that today is a
hard error. That error exists to keep "where" and "how" orthogonal (`@` says
where, `#` names a place, `%` says how). I recommend against the overload
(see Recommended solution).

### Managed-render precedent

`bob projects sync` owns one machine-written line nested under `^prj`:
`- 🧩 **Sub-projects:** [[a]] • [[b]]`, with open-first sorting, closed-child
ledger (`~~[[x]]~~ ✅/❌`), `🗓️` future markers, and in-place rewriting that
leaves user bullets alone (`docs/projects.md`, "Sync Rules"). This is the
exact precedent for a managed Notebooks render: one machine-owned line, fully
rewritten, user content untouched. Note the placement constraint the precedent
reveals: the Sub-projects line lives under `^prj`, which areas do not have —
so a Notebooks render for area root parents needs its own anchor (see below).

### Block-ID prompting precedent

`bob capture-task-id --route … --task-ref …` assigns IDs with suggestions and
stale-safe Add-block-ID flows; the capture grammar already routes incomplete
`+query`/`#section`/`:id` states through picker needs
(`task_parent`, `block_id`, `section`, `drawer`). A `@@foo^` (empty ID) state
that pre-fills a slug derived from the note text follows the same path as the
existing "mint ID for `<` merge targets" behavior.

## The vault: orphan candidates (direct reads + `bob query`)

Method note: `TABLE`-shaped DQL over frontmatter returned empty in this
environment even for known-good notes (e.g. `WHERE file.name = "cash"`), while
`TASK FROM "cash.md"` works fine — so the counts below come from bounded
direct reads of specific files, corroborated by `bob query` TASK output, not
from Dataview aggregation. Treat them as ±a few, not exact.

- ~664 Markdown files at the vault root (plus `ref/`, dated subtrees).
- **~304 untyped files** (no `type:` at all) containing 3+ bullets and zero
  `#task` lines, almost all carrying a `parent: [[…]]` link from the old Zorg
  conversion (`generated_from_zorg: true`). Only **1** lacks `parent`
  entirely (`old_arms_2.md`). The request's "live in a file without a parent"
  is better stated as **"whose parent is not in the typed tree"**: the top
  parent values are `[[tick_day]]`, `[[work]]`, `[[org]]`, `[[tick_month]]`,
  `[[ks]]`, `[[zorg_ref_man]]`, `[[gam]]`, `[[dev]]`, `[[prj_work]]` — most of
  these name notes that are themselves untyped or non-existent as
  area/project notes, so these files are invisible to every tree consumer
  (capture routing, ready caps, review walk, stats) while still rendering as
  ordinary wiki pages.
- Character of the orphans: overwhelmingly **reference/reading notes**
  (`clean_arch.md`, `balance_coupling.md`, `ad_tech_book.md` — book notes with
  `[[parts]]`/`[[chapters]]` bullets; `agent_ref.md`, `claude_code_ref.md`,
  `dev_tools.md` — tool/AI link collections), **idea lists** (`dev_ideas.md`,
  131 bullets), and **log-style notes** (`build_pages.md`, 68 bullets under 29
  date H2s; `breuch_meet.md`, 45 bullets under 10 H2s). Zero `#task` lines in
  the samples — they are already notebook-shaped in content; they only lack
  the type and a valid parent.
- **24 H2-heavy typed notes** (3+ H2s, 10+ bullets) are factor-out candidates:
  area notes `body`, `cash` (191 bullets), `dev` (154), `meet` (7 H2s), `gtd`;
  project notes `sase_art` (244 bullets), `sase_blog` (173, 6 H2s),
  `sase_better_plans` (81), `sase_monitor` (68), `sase_parallel_fams`,
  `sase_research`, `sase_skill_bundles`, etc. `build_pages.md`-style date-H2
  logs and `sase_blog`'s 6 sections are the clearest "factor this H2 out into
  a child notebook" examples.
- First-notebook migration set (concrete, from the scan): group the AI/agent
  orphans (`agent_ref.md`, `claude_code_ref.md`, plus `ai.md`, `aip.md`,
  `dev_tools.md`) under a notebook parented at the area/project that owns AI
  work; group the book-notes orphans (`clean_arch.md`, `balance_coupling.md`,
  `ad_tech_book.md`) under a reading-notes notebook; promote `dev_ideas.md`
  (131 idea bullets, parent `[[dev]]` — already a valid area!) almost as-is.
  `dev_ideas.md` is the single easiest pilot: valid parent, no tasks, one
  topic.

## Critique of the plan as written

1. **The core idea is good.** Task-free typed notes with valid parents close
   the exact gap the vault scan shows: hundreds of content notes that are
   neither tasks (area/project), nor external readings with embed contracts
   (ref), nor config-schema things (records), nor dated (day). Factoring large
   H2 sections out of area/project notes is the same operation as the
   already-accepted sub-project split, one level lighter (no `^prj`
   lifecycle). The "root parent renders its notebook tree" requirement is what
   keeps notebooks *linked into the system* instead of becoming a second,
   quieter orphan pool — keep it, and make it machine-owned so it cannot rot.
2. **`@@foo` bare form must not change meaning.** Today a physical line of
   only `@@foo` tokens is *metadata* (global declaration), and
   `note @work @@groceries` routes a task. Reassigning bare `@@foo` to
   "append a note to notebook foo" makes every existing draft containing a
   notebook-named route silently change from task capture to note capture —
   a data-loss-shaped breaking change (tasks never created, notes created
   instead). The suffixed forms have no such problem: they are errors today.
   **Adjustment: bare `@@foo` keeps its declaration meaning; if `foo` is a
   notebook, it errors with a teaching message** ("foo is a notebook; write
   @@foo#Section, @@foo+block-id, or @@foo^block-id"). Notebook appends always
   carry a suffix (`#`, `+id`, `^id`), with `@@foo#` (bare hash) meaning
   "first/any non-Tasks section", mirroring `@route#`.
3. **`%n` should keep one job.** `%n` = "this item is a plain note, not a
   task" is a clean, documented meaning. Notebook *creation* does not need
   `%n`: `@foo^bar@` already unambiguously creates a note-file (project
   create reuses exactly this seal; notebooks are the task-free sibling, so
   the seal reading "create a note-file of the type implied by context" is
   coherent). **Adjustment: creation is `@parent^stem@` where the new note's
   type comes from an explicit marker — and since `@a^id@` vs notebook-`@a^id@`
   would collide, require the notebook creation seal to differ.** The natural
   minimal split: `@parent^stem@` stays project creation; notebook creation is
   `@parent^stem@ %n`… but that reintroduces the `%n`+`@route` refusal. Cleaner:
   notebook creation reuses the *record-note* precedent (`Title @dir/` —
   type from the route position) — i.e. create notebooks from the parent side
   with a dedicated verb rather than overloading the project seal. See
   Recommended solution for the concrete grammar.
4. **"Required summary frontmatter" needs a shape, a writer, and a fallback.**
   A required field with no prompting writer will be empty within a month
   (every optional-field postmortem in `docs/records.md` says so: only
   `status` is required there, precisely because required fields need guided
   capture). **Adjustment: `summary:` — a plain 1–2-line string, max ~140
   chars, prompted at creation with the first H2/bullet text pre-filled;
   missing/empty renders the note's H1 + first-bullet excerpt as fallback, and
   `bob notebooks sync --dry-run` (or fold into `projects sync`) reports
   empty summaries as warnings, never errors.**
5. **"Children of area/project/another notebook" needs a depth and cycle
   rule.** Parent chains are walked recursively (stats, root derivation); a
   notebook cycle (`a → b → a`) would hang or misattribute those walkers.
   **Adjustment: max depth (e.g. error past 8, matching existing walker
   guards if any — verify against `task_root.rs`), cycle = scan error naming
   both files, same as duplicate-alias handling.** Also: a notebook's parent
   must itself be area/project/notebook — parenting under ref/article/day/inbox
   is refused at creation with the valid-target list (reuse `ParentError`
   shapes from `parent_notes.rs`).
6. **Residence rule must be explicit.** Area/project notes own tasks by
   residence; ref notes hold no open tasks. Notebooks must state the same
   invariant or `#task` lines will drift into them via move/edit: **no `#task`
   checkboxes in notebooks, period** (enforced by `projects sync`-equivalent
   warning + `bob task move` refusing notebook destinations for tasks +
   capture refusing `@notebook` task routes with a teaching error). Without
   this, notebooks silently become second-class project notes and inherit the
   entire scheduling/blocking contract.
7. **Root-parent render scope creep.** "For any root parent that has notebook
   children or has non-root children that do, recursively" is correct
   (render at the reporting root, transitive), but it needs an owner command
   and idempotence story or two writers will fight over the line. **Adjustment:
   one machine-owned line, one owner.** Either extend `bob projects sync`
   (renamed scope — no, keep `projects sync` pure per cli_rules: never
   repurpose a command) or add `bob notebooks sync`. Prefer the latter; it
   also owns summary warnings, cycle/depth errors, and empty-section pruning.
8. **Migration is the riskiest part, not the grammar.** 304 files with
   `generated_from_zorg` frontmatter and `^z-…` block IDs plus inbound links
   from across the vault. Renaming/typing breaks nothing (stems stay), but
   *reparenting* changes root walks → stats attribution shifts. Migration must
   be stem-preserving, link-safe (no renames in v1), and report attribution
   deltas. Do not migrate all 304 at once: pilot with `dev_ideas.md`-shaped
   easy wins (valid parent already), then reading-note clusters.

## Recommended solution

### Data model

- New type `type: "[[notebook]]"`. File layout mirrors project notes at the
  vault root (`<stem>.md`), no required sections. Frontmatter:
  `parent: "[[<area|project|notebook>]]"` (required, validated),
  `type: "[[notebook]]"`, `summary: "<≤140 chars>"` (required at creation,
  warned-when-empty after), optional `ready_cap` ignored, no `status`, no
  `^prj`, no `#task` lines.
- Note bullets are the existing section-bullet bytes (`- <text>
  [created::YYYY-MM-DD]`, optional `^block-id`), optionally grouped under H2s.
  Sub-notes under `^id` bullets reuse `@route+id` drawer mechanics with the
  drawer vocabulary replaced by "child bullets" (no ALL-CAPS-drawer
  requirement — notebook children nest directly).
- Chain walkers (`task_root.rs`, pomodoro-homes R1/R2, offclock inheritance)
  traverse notebook nodes transparently; task-residence, ready-cap,
  review-walk, stats-home, and capture-route enumerations keep excluding them.
  Cycle/depth violations are scan errors.

### Glossary term (draft, to be filed via `/sase_memory_write` + `decisions` as appropriate)

> **Notebook** — A Bob vault file with frontmatter `type: "[[notebook]]"` for
> a durable collection of plain note bullets with no open tasks, such as
> reading notes, idea lists, or factored-out sections of an area/project note.
> Its `parent` names the area, project, or notebook it belongs to. Notebooks
> hold no `#task` lines; capture appends bullets with `@@note` suffixed forms
> and creates notebooks from a parent with the notebook seal. Each reporting
> root renders its transitive notebook tree through one machine-owned
> Notebooks line. See `docs/notebooks.md`.

### Capture grammar (final)

- **Create:** `@parent^stem@ %notebook`… — no. Final: **`@parent/stem`
  is taken (record notes), `@parent^stem@` is taken (projects).** Claim the
  remaining free combination: **`@parent^^stem`** (double-caret create seal)
  creates `<stem>.md` with `parent: [[parent]]`, `type: [[notebook]]`,
  prompting `summary:` pre-filled from the item text. `capture-parse` reports
  mode `notebook_note`. Rationale: visually adjacent to project creation,
  zero collision with any documented form, toggleable in `capture-rewrite`
  (`^` after `@parent^stem` doubles it, mirroring the existing seal-toggle
  rule). First-level bullets become H2 sections per
  `capture-bullets-mirror-the-task-block` (ALL-CAPS bullet + notes → section);
  `- ^id`/`:id` move-in forms are refused for notebooks (nothing to move in —
  tasks are banned), which keeps the creation grammar small.
- **Append:** `@@note#Section` (H2, prefix-matched, created when missing),
  `@@note#` (first non-Tasks section), `@@note+block-id` (child of that note
  bullet), `@@note^block-id` (new top-level bullet with that ID; empty
  `@@note^` opens the Add-block-ID flow with a slug pre-fill). Bare `@@note`
  keeps declaration meaning and teaches when `note` is a notebook.
- **Aliases** compose automatically once the new forms register in the
  completion grammar (`.` after `@parent` still offers `^`; `/` still offers
  `#`; `,` still offers `+`), because `capture-rewrite` aliases are driven by
  the completion contexts, not by token spellings. This is a testable
  acceptance criterion, not a second implementation.
- **Refusals (all with teaching errors, mirroring existing codes):** notebook
  targets reject `s:<N>`, `$<N>`, `#type`, `%c` combos that imply tasks,
  `&`/`*`/`~` ownership forms, `!` completion, and whole-item `x`/`=` session
  operators — the same table as Pomodoro notes plus `@`-routing, extended with
  notebook addressing.

### Root-parent render

- One machine-owned line in the reporting root note (the R2 root parent),
  placed directly after the `Related notes:` block (areas) or after the
  Sub-projects line's note (projects):
  `- 📓 **Notebooks:** [[ideas]] — <summary> • [[reading]] — <summary>`.
  Transitive (recursive through non-root children), open-notebooks sorted
  case-insensitively, summaries truncated at 140 chars, missing summaries fall
  back to first-bullet excerpt with no error. Owned by new
  `bob notebooks sync` (`--dry-run` first, same contract as `projects sync`:
  per-file errors never stop the scan, exit 1 on any file error).
- Why a line and not a section: sections are user content and H2s are
  notebook payload; a managed line cannot collide with factored-out H2s.

### Migration (v1 scope)

1. `bob notebooks sync` ships first (validation + render, zero captures).
2. Pilot: type-only promotion of ~5 valid-parent orphans (`dev_ideas.md` et
   al.) + one factored H2 (a `sase_blog` section) as child notebook, with
   attribution-delta preview in `--dry-run`.
3. Reading-note clusters next (book notes under one notebook each); log-style
   date-H2 notes (`build_pages.md`) last — they may want `dated_notes`
   record semantics instead, which is an open question for the lead (see
   below), not a blocker.

### Open questions for the lead researcher

- Should date-log orphans (`build_pages.md`: 29 date H2s) become notebooks or
  a new `dated_notes`-style record type? They are append-only logs, not curated
  notes — notebooks fit poorly.
- Should `summary:` be a plain string or a wikilink-free excerpt contract
  shared with record `label:`? Defer to records precedent.
- `bob notebooks sync` vs folding into `projects sync`: separate command
  preferred (cli_rules: never repurpose), but confirm with Bryan.

## Files & commands touched (estimate for planning, not a plan)

`src/native/projects/scan.rs` (type gate + chain traversal),
`src/native/notebooks/` (new: scan/validate/sync/render),
`src/native/capture_language/*` (create seal, `@@` suffixed forms, refusals),
`src/native/capture_complete.rs` + providers (picker contexts so aliases
compose), `src/native/capture_rewrite` (seal toggle), `docs/notebooks.md` +
`docs/reference/capture-syntax.md` + `docs/capture.md` (behavior contracts),
`tests/` mirrors, `just docs-check` gate.

## Verification performed

- Read `docs/capture.md` grammar tables (directives, `@@` declarations,
  section/sub-bullet/task-toggle semantics), `docs/projects.md` sync rules,
  `docs/records.md` schema + reserved ids, `docs/pomodoro-homes.md` R1/R2.
- Read `sase/memory` strands via `sase memory read` (cli_rules, docs,
  glossary: area/project/reference/root-parent/capture/project-note-capture).
- Used `bob query` per the `bob_query` skill (logged use); `TASK FROM`
  works, `TABLE` over frontmatter returned empty in this environment, so vault
  counts come from bounded direct reads of named files.
- Inspected `scan.rs` (`frontmatter_is_*`, `walk_typed_notes`), `directive.rs`
  (`%n`), `capture_targets.rs`/`parent_notes.rs` (target set), `capture_task_id.rs`
  (ID flow), `capture_sections.rs` (section listing).
