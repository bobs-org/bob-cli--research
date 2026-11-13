# Sub-projects as an H2 Section Instead of `^prj` Sub-bullets

Researcher: mus (`__mus`) — independent swarm report. No peer report was opened or consulted.

Question: should sub-projects move out of the machine-owned `🧩 **Sub-projects:**`
sub-bullet under `^prj` into their own H2 section (with possible H3 sub-sections),
following the record-note / notebook precedent, in a way that is intuitive, reliable,
and beautiful?

Short answer: **yes, but as a generated `## Sub-projects` catalog section, not as
tasks living under H2/H3.** Keep the `^prj` task as the single source of project state
(Depends-On, BLOCKS, schedule, `#hide`, close/promote/restore semantics); move only the
*presentation* of the child list into a bob-owned callout region that reuses the exact
notebooks/albums host-catalog engine. Ship v1 with a **flat H2, no H3 sub-sections**;
add H3 grouping later only if a real density problem appears. Details and rationale below.

## 1. What exists today

### 1.1 The `^prj` task and its one machine-owned child

Each active project note carries one lifecycle task ([docs/projects.md](/home/bryan/.local/state/sase/workspaces/bobs-org/bob-cli/bob-cli_22/docs/projects.md)):

```markdown
- [ ] #task #prj Ship the project outcome! #hide ^prj
```

`bob projects sync` owns exactly one sub-bullet of that task (see
`src/native/projects/edits.rs`, `src/native/projects/sync.rs`,
`src/native/projects/mod.rs`):

```markdown
- 🧩 **Sub-projects:** [[alpha_child]] • [[beta_child]]
```

Placement is precise: nested under `^prj` after the whole Depends-On subtree and a
following BLOCKS subtree (or after a Cancel Log first slot), canonical tab indent,
canonical `•` separators. Only a direct child starting with the Depends-On or BLOCKS
marker counts; everything else under `^prj` is user-owned, including bare
`[[scratch_note]]` links. `sync` never uses those to suppress the generated line.

Decorations on that one line:

- Future-scheduled child (valid future `[scheduled::]` on the child's `^prj`, or
  leftover frontmatter about to be hoisted): `🗓️` prefix per child.
- Closed children already on the line are retained as a ledger: `~~[[child]]~~ ✅`
  (done) / `~~[[child]]~~ ❌` (canceled). Deleting a closed entry prunes it permanently
  unless reopened. New closed children are not resurrected.
- The line is deleted only when there are no open sub-projects and no tracked closed
  ones left. Duplicate marker lines are removed; an out-of-position marker is moved
  after Depends-On/BLOCKS or rewritten in place.

An open sub-project is defined structurally: another project note whose `parent`
frontmatter wikilink resolves to this note's stem and whose own `^prj` is open
(terminal frontmatter + open `^prj` counts as open because the run reopens it).
Sorting: open children first, then already-listed closed children, each group
case-insensitive by stem, original casing preserved.

### 1.2 Why the line lives where it lives

The position is load-bearing, not cosmetic:

- **Surfacing:** active projects with no non-hidden open tasks *and* no open
  sub-projects lose `#hide` on `^prj`; projects with either get `#hide` back.
  `surface.rs` counts `open_subprojects` from the marker line
  (`subproject_displays_in_marker_line`), with strikethrough forms explicitly
  excluded.
- **Blocking:** `projects-block-from-prj-line` + `subprojects-inherit-project-blocking`
  make the `^prj` Depends-On line and inline `[scheduled::]` the single source of
  project reason; residence/tag cascade (`#prj_is_blocked`, reconcile as authority)
  keys off the project tree, and close trigger (c) pulls a parent `^prj` to Next when
  its last open child closes. The marker line is the cheap reader for "does this
  project have open children" without walking the tree on every gesture.
- **Lifecycle moves:** promotion (`<ctrl+shift+option+n`, capture `@route:id@`),
  restore-to-task, schedule/work-log moves, Task Card gestures on `^prj`, and the
  close successor-offer paths all operate on the `^prj` *task block*. The generated
  Sub-projects child is explicitly omitted on reverse conversion and skipped as a
  move/copy source; user bullets move, the marker does not.
- **Obsidian reality:** the `^prj` block (including children) is one addressable task
  block (`#^prj`). Task-board views, block embeds, and the close/settle writers locate
  rows by identity within that block.

So "move sub-projects to H2" cannot mean "move the source of truth out of the task
block" without re-implementing all of the above.

### 1.3 The inspiration: records and notebooks

Two precedents matter, and they are *different* patterns:

**A. Record notes turn ALL-CAPS bullets into H2 sections.**
`bob` writes `parent/type/title/schema-fields/created` frontmatter, then always-present
`## Notes`, and a first-level ALL-CAPS bullet with nested bullets becomes a Title-Cased
`##` section on create/update (`Ramen Nagi @eat/` planner; `capture_project_note.rs`
does the same for new project notes: an ALL-CAPS bullet with children becomes a
`## Title` section, reusing a matching header or appending at EOF, descendants copied
verbatim as reference notes, never tasks). Sections are *authored content*, not a
generated catalog.

**B. Notebooks and albums use a bob-owned callout inside an author-owned H2.**
Every area/project with notebooks beneath it carries ([docs/notebooks.md](/home/bryan/.local/state/sase/workspaces/bobs-org/bob-cli/bob-cli_22/docs/notebooks.md)):

```markdown
## Notebooks

> [!notebooks]
>
> - **[[dev_tools|Developer tools]]** — summary line.
>   - **[[git|Git]]** — nested notebook.
```

Albums are identical in shape (`## Albums` + `> [!albums]`, direct albums then
`> - 🧩 [[project]]` descendant groups). The contract, shared through
`src/native/host_catalog/region.rs`, is:

- Bob owns the **callout bytes**; Bryan owns the heading, its position, and everything
  else.
- First write goes before the first real `## Tasks` (notebooks) / before first H2 or at
  EOF (records index) / at end of `## Notebooks` else before `## Tasks` else EOF
  (albums); later writes patch only the callout wherever it was moved.
- Empty subtree deletes the callout (and the heading only if its section is then blank).
- Duplicates self-heal to the first region; malformed legacy markers are *damage* that
  refuses the host and never guesses a repair.
- `## Notebooks` is section-protected: `@dev#notebooks` refuses with
  `notebooks_section_generated` instead of writing into the catalog. Same for
  `## Albums`.
- `list`/`check` report `missing/stale/current/damaged` per host without writing;
  `sync` repairs under the shared maintenance lock with one scoped commit, dry-run
  diffs, JSON envelope v1, CRLF/BOM preservation, fence-aware scanning.

That pattern — **generated callout, author-owned heading and position** — is the one to
copy for sub-projects. It is proven, audited, and already handles the hard parts
(positioning, moves, duplicates, damage, dry-run, JSON, locks).

## 2. Is this a good idea?

**Yes, with the catalog interpretation. No, as a task-tree relocation.**

What an H2 gains:

- **Visibility.** A single `•`-joined line compresses badly past ~4–6 children and is
  nearly unreadable on mobile. One row per child with status/schedule affordances
  scales to real portfolios (Bryan already has multi-level project trees).
- **Consistency.** Areas and projects already explain themselves with `## Notebooks`
  and `## Albums` catalogs. A third catalog, `## Sub-projects`, completes the mental
  model: *tasks are work in this note; sub-projects are projects beneath this note;
  notebooks/albums are knowledge beneath this note.* Three generated catalogs, one
  engine, one set of rules.
- **Beauty.** Catalog rows (`**[[stem|Title]]** — summary`) render as Obsidian cards
  with existing hue/count/age clients, exactly like notebook/album rows. The current
  `🧩`-line cannot show summaries, counts, or group structure.

What breaks if the H2 *replaces* the task-block source:

1. `surface.rs` open-subproject counting, `edits.rs` anchor logic, close trigger (c),
   promotion/restore omission rules, Task Card `^prj` gestures, and reconcile's
   marker-line reads all assume the marker child. Every reader/writer would need a
   second parser, with a migration window where both exist and can disagree.
2. An H2 list of *task* lines (`- [ ] [[child]]`) creates residence ambiguity: every
   `#task` belongs by residence to exactly one area/project note (see glossary
   area-note). A mirrored task row in the parent would either double-count or need a
   new "mirror, not residence" task kind — a large contract change for zero task
   value, since the child's real tasks already live in the child note.
3. H3 sub-sections ("one H3 per sub-project with its tasks"?) would duplicate child
   `## Tasks` content into the parent, breaking the single-residence invariant,
   archive pairing (`done/`), Ready-cap counting (which counts the lane by residence),
   freshness walks, and Stats roots. Transclusion already solves "see child work from
   parent" without copying bytes.

So the critique of the plan as stated: **do not render sub-project *tasks* in the
parent's H2/H3.** Render the sub-project *catalog* in the parent's H2. The child's
tasks stay in the child. H3s are not needed for that.

## 3. Requirements adjustments

I recommend these explicit adjustments to the request before implementation:

1. **Keep the `^prj` marker line as the source during migration; add the H2 as the
   reader.** Either (a) dual-write both for one release then retire the marker child,
   or (b) keep the marker permanently as a hidden machine anchor. I recommend (a):
   dual-write with byte-identical semantics for one train, then a single follow-up
   that removes the marker child and repoints `surface.rs`/close/Task-Card readers to
   the catalog region. Never two long-lived sources.
2. **No H3 sub-sections in v1.** Flat rows + `🧩 [[project]]` descendant groups
   (exactly the albums pattern) handle nesting without inventing an H3 contract.
   Reserve H3 for a later density proposal (e.g. `### Open` / `### Closed ledger`, or
   per-group headings) only with evidence that flat + groups is insufficient.
3. **Rows are links, not tasks.** The H2 lists `[[child]]` catalog rows (non-checkbox),
   never `- [ ]` task rows. This preserves residence, Ready caps, freshness, and
   archive invariants by construction.
4. **Bob owns the callout; Bryan owns the heading and position.** Copy the
   notebooks/albums ownership split verbatim, including section protection
   (`@proj#sub-projects` refuses), duplicate self-heal, and damage refusal.
5. **Closed ledger stays opt-in by retention, not by resurrection.** Copy the current
   rule: retained `~~[[child]]~~ ✅/❌` rows persist; deleted ones stay deleted; sync
   never resurrects unlisted closed children. Cap the retained ledger (suggest 10,
   matching the archive window's order of magnitude) so a long-lived parent does not
   accumulate an unbounded closed list.
6. **Schedule decoration stays future-only `🗓️`.** Same `BOB_NOW` boundary, same
   today/past suppression, same invalid-date silence. Do not add new date chips in the
   file; chips/dates are client rendering (the child-picker already shows
   `calendar-clock` chips from the child's inline date).

## 4. Recommended solution

### 4.1 File shape

```markdown
## Sub-projects

> [!sub-projects]
>
> - **[[alpha_child|Alpha Child]]** — one-line summary. 🗓️ Jul 16
> - **[[beta_child|Beta Child]]** — one-line summary.
> - 🧩 [[gamma_group|Gamma Group]]
>   - **[[delta|Delta]]** — nested descendant summary.
>
> <!-- closed ledger -->
> - ~~[[old_child|Old Child]]~~ ✅
```

Concretely:

- Heading is exactly `## Sub-projects` (matching the existing marker spelling
  `Sub-projects`, not `Subprojects`, to avoid a rename cascade across docs, marker
  prefix constant, and vault content).
- Callout head is canonical `> [!sub-projects]` (lowercase, hyphenated, mirroring
  `[!notebooks]` / `[!albums]` / `[!records]`).
- Open children first (case-insensitive by display title, path tie-break — same as
  notebooks), then retained closed ledger (`✅`/`❌`), each struck through.
- Descendant-owner grouping copies albums: direct children flat, deeper descendants
  under `> - 🧩 [[project]]` group lines. Nesting depth mirrors the parent chain, not
  the full subtree indent of the task block.
- Summaries reuse the child's `summary:` frontmatter one-liner (escaped exactly like
  notebook/album rows: wikilink/emphasis/code/tag/block-ID/math/comment/highlight/inline-field
  openers backslash-escaped, whitespace folded). No colors, counts, recency, or dates
  are written; clients draw those.
- Terminal projects get no region. Reopening `^prj` recreates it under the same rules
  as today (active run applies surfacing + catalog rules from the reopened `wip`).

Placement reuses `host_catalog` placements: first write at the end of an existing
`## Notebooks` section (albums precedent: owner catalogs insert after Notebooks), else
before the first real `## Tasks`, else at EOF. Later writes patch only the callout.
`## Sub-projects` gets the same section protection as `## Notebooks`/`## Albums`:
capture `@proj#sub-projects` refuses with `sub_projects_section_generated`, and drawer
creation never targets it.

### 4.2 Sync semantics (reuse, don't reinvent)

- Port the *planner* (`desired_subprojects`, open-first/closed-retained sorting,
  future-marker and ledger decoration, idempotent canonical render) unchanged; swap the
  *emitter* from "one tab-indented task sub-bullet after Depends-On/BLOCKS" to
  "host-catalog callout region via `host_catalog::plan_host_region`".
- Keep every existing event/reason (`AddSubprojectLink`, `MarkSubproject`,
  `NormalizeSubprojects`, `🗓️` add/remove) so `list`/`check`/dry-run output and tests
  keep their vocabulary; only the byte span changes.
- Damage states copy notebooks: `missing / stale / current / damaged`. A damaged
  region (e.g. hand-edited callout head, torn group indent) is reported as
  `sub_projects_catalog_damaged` with path+line and left untouched; healthy hosts apply
  together; exit codes match (`check` 1 on error, `sync` 1 on damage/failure, 2 on
  usage).
- Guarded write path: preimage/revalidation, shared maintenance lock, one scoped commit
  (`projects: sync sub-project catalogs (N notes)` or folded into the existing
  projects-sync commit), post-sync only when the run changed bytes, unified diffs on
  `-d`, JSON envelope v1 (`catalogs[]`, `changes[]`, `findings[]`, `commit`, `sync`).
- `bob projects sync` remains the single CLI owner of derived sub-project state; `bob
  task reconcile` keeps owning derived `[?]` Blocked state. No new command in v1; the
  existing `list`/`check`/`sync -d` surface covers it. (A future `bob projects
  catalog` split is explicitly out of scope.)

### 4.3 Readers to repoint (the real work list)

- `surface.rs`: count open sub-projects from the catalog region instead of
  `subproject_displays_in_marker_line`. During dual-write, assert both agree (and warn
  on disagreement rather than guessing).
- Close trigger (c), promotion/restore omission, Task Card `^prj` gestures, capture
  `@route+id!` / `=x~K` consumption guards, and the `<ctrl+=>` child-picker
  `calendar-clock` chip: all keep reading the *planned* set, not the raw bytes, so
  they survive the emitter swap. Anything that today parses the marker line's raw
  text must move to the planner output.
- Plugin counterpart (`bob-navigation-hotkeys` project model, child picker, Depends-on
  stage on `^prj`): the `🧩`-line parser is the cross-repo reader most likely to be
  missed. Coordinate the contract change across both repos; the mac thin client needs
  no change (it renders what bob returns).
- Obsidian presentation: one card style for sub-project rows reusing the album-card /
  notebook-gesture CSS (status pill, future-date chip, struck ledger style). No new
  icons; `🧩` stays the group glyph for continuity.

### 4.4 Why not H3s

The request's parenthetical "(with possible H3 sub-sections?)" is the riskiest phrase.
H3s would mean one of:

- (i) H3 per sub-project with that sub-project's tasks underneath — rejected in §2
  (residence duplication).
- (ii) H3 grouping (`### Open`, `### Recently closed`) — unnecessary in v1; the flat
  open-then-ledger order plus `✅/❌` already encodes it, and every extra heading is a
  new placement/damage/migration case.
- (iii) H3 per descendant group — the albums `🧩 [[project]]` group-line pattern
  already expresses nesting with zero heading machinery and composes with duplicate
  self-heal.

Recommendation: **ship flat + group lines; revisit H3 only with vault evidence that a
parent with 20+ children is unreadable as a flat catalog.** That evidence does not exist
today; the longest marker lines are a handful of children.

### 4.5 Migration and compatibility

1. Release N: dual-write. `sync` writes both the legacy marker child *and* the new
   callout from the same `desired_subprojects` plan. Readers keep using the marker.
   `check` reports catalog `missing/stale` as warnings with the `bob projects sync`
   hint. Docs gain the new section; the marker is documented as legacy-but-authoritative.
2. Release N+1: flip readers to the catalog (with a one-run agreement assertion), stop
   writing the marker child, delete orphan marker lines. Closed-ledger entries migrate
   verbatim (struck + ✅/❌ + any `🗓️`).
3. Hand-authored `[[child]]` bullets under `^prj` stay user-owned throughout; section
   bullets that qualify as ALL-CAPS sections on project creation keep working
   (creation path already excludes `## Tasks`-matching sections from duplication).
4. Fenced examples, CRLF, BOM, and final-newline behavior inherit the host-catalog
   guarantees; add conformance vectors mirroring `notebooks/region.rs` (BOM+CRLF,
   duplicate regions, moved region, legacy marker pair if one is introduced).

### 4.6 What to verify before building

- Measure the widest current marker lines (children count, byte length) to size row
  layout and justify the ledger cap.
- Confirm no vault query, Dataview, or Bases view reads the literal
  `🧩 **Sub-projects:**` string outside Rust + the nav-hotkeys plugin (search both
  repos and `docs/`).
- Confirm the `<ctrl+=>` picker and task-dependency §12.10/13 prose changes needed for
  the catalog reader swap.
- Run the full `projects` + `notebooks` + `albums` + `capture_project_note` suites plus
  `just check`-equivalent gates; the emitter swap touches all three catalog emitters'
  shared region code paths.

## 5. Alternatives considered

| Option | Shape | Verdict |
|---|---|---|
| A. H2 catalog callout (recommended) | `## Sub-projects` + `> [!sub-projects]`, link rows, group lines | Intuitive (third catalog beside Notebooks/Albums), reliable (proven engine), beautiful (card rendering). |
| B. H2 task list | `## Sub-projects` with `- [ ] [[child]]` checkboxes | Rejected: breaks single-residence invariant, Ready caps, freshness, archive pairing. |
| C. H2/H3 embedded child tasks | H3 per sub-project with mirrored tasks | Rejected: strongest form of B's failure; transclusion already covers visibility. |
| D. Keep marker, render H2 only in clients | File keeps `🧩`-line; dash/pickers render sections | Viable fallback if the vault-file migration proves too costly; loses git/mobile/plain-Markdown readability, keeps two mental models. Do this only as a stopgap. |
| E. Dataview/Bases index, no bytes | `dataview` query lists children live | Rejected per the notebook decision's reasoning: invisible to git/agents/mobile, cannot roll up, no ledger. |

## 6. Risks and open questions

- **Cross-repo reader miss** is the top risk: the nav-hotkeys plugin parses the marker
  line for the child picker and Depends-on stage. Gate the flip on the exact-SHA mac
  run only insofar as it exercises that plugin; the Rust suites alone are insufficient.
- **Ledger growth** without a cap repeats the closed-line accumulation problem in a
  taller region. The proposed cap of 10 retained closed rows needs Bryan's.confirmation
  (or "unbounded, prune by hand" as today).
- **`root: true` and leaf reporting** (`leaf project may have sub-projects`) interact
  with group-line nesting: confirm group lines stop at the next root exactly like
  notebook catalogs ("stopping at another root").
- **Empty-subtree heading rule**: copy notebooks verbatim (delete callout; delete
  heading only when its section is then blank) so authored prose under `## Sub-projects`
  survives.
- **Decision record**: this change partially supersedes the "single Sub-projects line
  nested under `^prj`" paragraphs of `docs/projects.md` and the
  `subprojects-inherit-project-blocking` evidence chain. Per the decisions contract,
  write a new immutable record with `superseded_by` back-links rather than editing the
  old ones in place.

## 7. Sources consulted

- `docs/projects.md` (§§ Project Notes, Sync Rules, Sub-projects line, promotion/restore).
- `docs/notebooks.md` (catalog, owned region, placement, damage, section protection).
- `docs/records.md` (album catalogs, `## Notes`/section creation, shared region engine).
- `docs/reference/vault-format.md` (notebook/album/project/inbox/Tasks-region contracts).
- `src/native/projects/{mod,sync,edits,surface}.rs`,
  `src/native/host_catalog/region.rs`, `src/native/notebooks/{catalog,region}.rs`,
  `src/native/albums/{catalog,index}.rs`, `src/native/capture_project_note.rs`.
- Memory (via `sase memory read`, not direct file opens):
  `decisions:projects-block-from-prj-line`,
  `decisions:subprojects-inherit-project-blocking`,
  `decisions:task-lanes-are-sticky`, `decisions:notebook-routes-write-notes`,
  `decisions:today-is-read-from-the-ledger`,
  `glossary:project-note`, `glossary:notebook`, `glossary:leaf-project`.
- Deliberately not consulted: any peer `__cdx`/`__cld`/`__grk`/`__gem` swarm report,
  its transcript, or its summaries.

## 8. Recommended build order

1. Record the decision (new immutable `decisions:` record + this research link).
2. Extract the marker-line planner into a shared plan type consumed by both emitters.
3. Implement the `## Sub-projects` callout emitter on `host_catalog`, with
   `list`/`check` states and `-d` diffs, behind dual-write.
4. Repoint `surface.rs`/close/picker readers to the plan output; add agreement
   assertions.
5. Obsidian card CSS for sub-project rows (reuse album/notebook cards).
6. Docs (`projects.md`, `vault-format.md`, capture section-protection lists) + JSON
   output docs.
7. Flip + marker retirement release, with ledger migration verification on a scratch
   vault containing deep chains, future-scheduled children, retained closed ledgers,
   CRLF/BOM notes, and moved catalog regions.
