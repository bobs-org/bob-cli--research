# Subprojects deserve a section, not a second task system

Independent design research by **cdx** · 2026-11-13

## Judgment

**Yes: move the subproject collection into one `## Sub-projects` section.** Give it the same durable Markdown foundation and restrained visual treatment as notebook and album catalogs. Keep each child as a compact linked row. Do **not** create an H2 or H3 for every child, embed every child's task block, or introduce another editable project-status surface.

This is a worthwhile improvement because a project's component outcomes deserve to be visible independently of its completion checkbox. The present one-line child list has little room for meaningful titles or context, and it sits among dependency links and task logs. A section provides a stable destination for navigation and enough space to distinguish open work from retained history.

The implementation is more than a cosmetic move. The current line is also a local input to project-finished behavior. Removing it without upgrading its readers can make a parent look empty while it still has open children. The safest design is a narrowly owned catalog, a shared child-state model, and a reader-first migration across bob-cli and bob-plugins.

## Research basis and limits

I independently inspected bob-cli at `c994cfbd1d0d0a8271b5b27c3db5b6d6d73b0795` and the linked bob-plugins checkout at `2ee64e603c3b1dc5eab0d15c6b8ec4aebc7b8c4a`. I read the project, notebook, and record contracts; relevant Rust planners and region writers; plugin catalog/rendering code; lifecycle readers; and existing test cases. I also inspected the repository's album Reading-view screenshot and consulted official Obsidian and W3C documentation. Source locators appear below as C/P references.

I did not inspect the live vault, run Obsidian, benchmark a prototype, execute the existing test suites, or consult another swarm researcher's report or findings. Counts, project names, and the visual specimen below are illustrative. The proposal is a design recommendation, not an implemented or usability-tested feature.

## What the existing designs teach us

### Projects already have a precise lifecycle

A project remains its own Markdown file. Its `parent:` determines hierarchy; its exact `^prj` task carries the completion criterion, schedule, and dependency input. `root: true` affects reporting ancestry, not whether the note is a direct child of another project. Bob's term “leaf project” is a reporting role and can include a project that itself has children; the new UI must not use that term to mean “has no descendants.” These distinctions should survive unchanged.

Today, `bob projects sync` writes this generated direct child beneath an open `^prj`:

```markdown
- [ ] #task #prj Launch the new service #hide ^prj
  - 🧩 **Sub-projects:** [[service_api]] • 🗓️ [[service_launch]] • ~~[[service_spike]]~~ ✅
```

It derives open membership from child project notes. Open children are always listed. Closed children remain only when already represented in the generated line; deleting a closed entry deliberately prunes it, and old closed children are not rediscovered into the list. Done and canceled are distinct. A future schedule receives a calendar mark. Terminal parent projects normally receive no lifecycle-block edits until reopened. [C1, C2]

This curated-history behavior is easy to overlook and valuable to preserve. An apparently simpler “show every project whose parent matches” query would resurrect old history and change the meaning of deleting a closed entry.

### Notebooks supply the right ownership boundary

Notebook catalogs use a real `## Notebooks` heading followed by a `[!notebooks]` callout. Bob owns the callout; the author owns its position, heading, and surrounding prose. Stable titles, links, and summaries are written to Markdown. Counts, age, and colors belong to rendering. The shared region engine recognizes real source regions, ignores frontmatter and fenced examples, and preserves surrounding bytes and line endings. [C3, C5]

The scope is not identical to the proposed project catalog: notebook catalogs can roll up through descendant owners until a root boundary. For subprojects, I recommend direct children only. Borrow the presentation and ownership machinery, not the notebook membership rule.

### Albums supply useful visual behavior, not a new schema to copy

There are two relevant album surfaces: an owner's `## Albums` catalog and an album's `## Records` index. The owner catalog is the closer structural analogy. The record index demonstrates grouping, deliberate folding, and responsive chips. Its `index_by` subgroups are conditional, while smaller groups stay flat. That is a good reminder not to add structural chrome before it helps. [C4, P1]

The inspected screenshot has a restrained accent, generous row spacing, readable links, and a compact folded history/group presentation. The implementation keeps fold state in the pane, retains last-good data during refresh, distinguishes failures from real zeroes, and avoids rewriting notes when painting. Those are the useful qualities to carry forward. A project catalog does not need album schemas, record facets, peeks, or a Schema Card. [P1–P3]

## Alternatives and critique

| Approach | Benefit | Cost or failure mode | Judgment |
| --- | --- | --- | --- |
| Keep the task sub-bullet and improve its CSS | Smallest change; preserves all readers | Hierarchy remains attached to one task; long lists still scan poorly | Reasonable fallback, weaker result |
| One H2 plus a plain linked list | Portable and easy to read | Heading alone does not define a safe rewrite boundary | Good baseline with an owned region |
| One H2 plus a generated callout and enhanced rows | Familiar catalogs; clear ownership; plain-source fallback | Requires lifecycle-reader migration and rendering work | **Recommended** |
| H3 per child, optionally with an embedded `^prj` | Rich context and native section navigation | Large notes, duplicated interaction surfaces, Outline clutter, unstable heading identities | Reserve for manually authored project briefs |
| H3s for Open / Blocked / Scheduled / Done | Explicit grouping | Several dimensions overlap; rows jump groups; tiny groups waste space | Avoid in v1 |
| Dataview/Bases-only dashboard | Flexible filtering and sorting | Changes durability and availability; does not preserve curated history by itself | Optional later view, not the canonical section |
| Full recursive project tree | Makes distant work visible | Repeats descendants across ancestors and expands scope considerably | Defer until direct-child navigation proves inadequate |

An H2 per individual subproject would place child navigation on the same outline level as Requirements, Notes, and Tasks. An H3 per child would still turn a directory into many mini-documents. Neither improves the ordinary “which component do I open?” interaction enough to justify its height.

Obsidian's Outline lists headings and lets users navigate or rearrange their sections. One real H2 therefore creates a useful section destination; generating headings for every row would deliberately enlarge that outline. This is a design inference from the documented behavior, not a measured usability result. [Obsidian Outline](https://obsidian.md/help/plugins/outline)

Embeds are supported and stay updated from their source, so embedding child blocks is technically possible. I would still reject it as the default: it exposes task controls in a navigation catalog, couples its height to task-child detail, and makes the parent feel like a second place to work on every child. Ordinary links and existing hover previews give a calmer first release. [Obsidian embeds](https://obsidian.md/help/embeds)

## Proposed experience

### One collection, immediately legible

Use `## Sub-projects` on project notes. Place a new catalog after the complete introductory/lifecycle region and before the first existing Notebooks, Albums, or Tasks section that follows it; otherwise append it. Never split the `^prj` task from its dependency or log subtree. Once positioned, preserve the author's placement. Do not reorder existing authored sections to enforce a universal template.

A typical new arrangement is:

```text
# Service launch

[Project completion criterion and its own dependencies/logs]
[Authored context]

## Sub-projects
[Child project catalog]

## Notebooks
[Existing notebook catalog]

## Albums
[Existing album catalog]

## Tasks
[The parent's own tasks]
```

Render the catalog as one quiet panel with a shared left accent, not a grid of individually boxed cards. Rows should feel like a readable directory:

```text
Sub-projects                              2 open · 1 closed

  API contract
  External clients can create and retrieve an order.

  Launch rehearsal                         Scheduled · Nov 20
  Complete the rehearsal and sign off the launch checklist.

  ▸ Closed (1)
```

At a narrow width, the schedule label moves beneath the title. At desktop widths it can sit at the trailing edge. The title remains the primary link; the outcome remains secondary. The H2 need not repeat a second large “Sub-projects” callout title. In a stock renderer, a modest default callout header is an acceptable fallback.

### Row content

Use the child's display title, resolved consistently with notebook titles: eligible first H1, then first alias, then humanized stem. Keep the real note path as identity. Equal titles remain separate; add a quiet disambiguator only when needed. Preserve ordinary Obsidian link behavior, modifier-click opening, and hover previews.

Show the cleaned completion criterion from the child's `^prj` as secondary text. Strip task syntax, machine tags, inline fields, the trailing block ID, and lifecycle decorations using existing parsers rather than broad text substitutions. Reduce embedded links to display text and escape active syntax before writing an inert summary. Do not introduce a required `summary:` field that competes with the existing definition of done. If the criterion is a placeholder or unavailable, omit it and surface the diagnostic rather than inventing a description. If it duplicates the title, omit the second line.

Keep source text complete. Prefer wrapping to mandatory truncation; for exceptionally long criteria, a render-only disclosure can show the full text accessibly. Never make a hover-only tooltip the sole way to read it.

Show an open child's hold information only when it matters: a scheduled date or a Blocked label with its actual reason. A future schedule is not itself the same concept as every kind of blocking. Preserve those distinctions in the model even if a compact row displays one primary reason and an accessible detail. Use Bob's existing reason authority; do not derive a separate blocked state in the renderer.

Do not display progress percentages in v1. Task counts do not measure outcome completion, and a parent whose work lives in child notes can have zero resident tasks while being very much unfinished. If counts are later added, explicitly distinguish resident tasks from child projects and total descendants.

### Grouping, history, and H3

Show all open children first, in stable case-insensitive display-title order with a path tie-breaker. Blocked and scheduled children remain in that set, with readable labels. They are still unfinished parts of the project.

When retained closed entries exist, render one **Closed** group after the open rows, collapsed by default in the enhanced view. Keep Done and Canceled distinguishable inside it. Preserve closed-row ordering deterministically; do not invent completion-date ordering when the historical data lacks those dates. With only closed entries, keep the closed group and its count visible. With no open or retained closed entries, remove the managed block and remove its heading only if the remaining section is blank.

Use a bold group label in Markdown, not a generated H3. This gives small notes minimal structure and avoids teaching the capture engine that status groups are writable sections. If a later need for durable outline navigation to Open and Closed is demonstrated, add real H3s as a separately specified format revision. Do not quietly alternate between H3 and flat formats based on row count.

A nested child project appears as one row. Opening it reveals its own direct children. A `root: true` child still appears in its parent's catalog: reporting boundaries must not erase parentage. Areas could later use the same machinery under `## Projects`, but that is an explicit scope extension, not necessary to replace the existing project-task line.

### Interaction and accessibility

The catalog is navigation. Clicking a title opens the child note; it does not close, schedule, or reparent it. No drag-to-reparent, checkboxes, or new row hotkeys are necessary for v1. Existing project gestures remain on the actual child note and its `^prj`.

The Closed disclosure must be a keyboard-operable button with visible focus, Enter/Space behavior, and `aria-expanded`. Keep its state per pane and host identity; a background refresh must not reset the user's fold or steal focus. Use text/icons as well as hue for status. These disclosure semantics follow the [W3C disclosure pattern](https://www.w3.org/WAI/ARIA/apg/patterns/disclosure/).

Use existing root-derived catalog color tokens and theme typography. Avoid a unique color for every child, oversized status pills, or a new dashboard visual language. Check light and dark themes, long titles, zoom, and approximately 375-pixel panes. Rows should wrap without horizontal scrolling.

## Durable Markdown and ownership

An illustrative canonical source shape is:

```markdown
## Sub-projects

> [!subprojects]
>
> - **[[service_api|API contract]]** — External clients can create and retrieve an order.
> - 🗓️ **[[service_launch|Launch rehearsal]]** — Complete the rehearsal and sign off the launch checklist.
> - **Closed**
>   - ~~[[service_spike|Feasibility spike]]~~ ✅
```

This is proposed syntax, not an existing supported callout. It deliberately retains the existing calendar and terminal marks so a source reader understands the basic lifecycle. Exact dates and current blocked reasons can be render-time data. Open rows are links, never duplicated checkboxes or `![[child#^prj]]` transclusions.

Obsidian supports custom callout identifiers, Markdown and links inside callouts, and a default rendering for unrecognized types. This makes the stored section readable before the custom renderer is installed. The new renderer should enhance the existing links rather than replace the only navigable content with an opaque widget. [Obsidian callouts](https://obsidian.md/help/callouts)

Define these ownership rules explicitly:

1. Bob owns recognized `[!subprojects]` quote lines only. A heading with the same name does not authorize deleting its entire section. Authored prose before or after the callout survives.
2. Recognition ignores frontmatter and fenced examples. Preserve BOM, CRLF/LF, trailing-newline state, and unrelated bytes, using `host_catalog::region` as the foundation.
3. Reuse a unique compatible existing Sub-projects heading for first insertion. If headings or malformed ownership boundaries make placement ambiguous, report it and leave the host unchanged.
4. Reserve the generated catalog from capture section selection and `@project+prj#...` drawer routing, including normalized spellings and generated descendants. A refusal should point to the child's route or a normal authored section.
5. Union previously tracked closed identities from all recognized old/new regions before deduplication; only then replace duplicates with one canonical block. The generic notebook duplicate cleanup is not sufficient by itself because project rows carry curated-history membership.
6. Hand deletion of a closed row remains pruning. An open row deleted from the catalog returns on sync because actual parentage still governs open membership. This asymmetry already exists and should be documented.
7. A malformed region, incomplete scan, unreadable child, or ambiguous parent must never be interpreted as a trustworthy empty child set. Preserve affected history and report the problem.

If a legacy marker has authored descendants or unusual mixed content, do not discard its subtree wholesale. Migrate only confidently owned bytes, preserve adjacent user bullets, and refuse an unsafe boundary with a useful diagnostic.

## The reliability work the design requires

### Decouple the child model from its old location

Introduce one internal representation for a host's catalog: resolved child identity/path, title, effective open/done/canceled state, schedule information, criterion, and findings. Keep retained closed membership as explicit input read from existing generated regions. Parent metadata and lifecycle tasks remain the authority for current relationships and state.

Two source readers—legacy `^prj` marker and new callout—should yield the same semantic entries. Rendering and lifecycle decisions should consume those entries, not search for a particular bullet beneath `^prj`.

For sync, use a coherent note graph. For immediate close gestures, preserve the existing fast local catalog read, now supporting both formats, with the staged just-closed child excluded by resolved identity. This avoids forcing a synchronous vault-wide scan into every gesture. If the representation is damaged, contradictory, or known stale, do not assert that the parent is empty: refresh/resolve the necessary children or withhold the parent-finished offer with a diagnostic. A complete, freshly read empty graph can still establish that a catalog-less project has no children.

This does not magically solve every pre-existing stale-cache case. A newly created or reparented child needs timely maintenance of the affected parent catalogs. Integrate the pure planner into Bob-owned create/reparent/reopen/close transactions where those writers exist; use a bounded shared refresh for other edits and nightly sync for repair. Do not implement a second independent Markdown writer in the presentation plugin. Generic file renames must invalidate both link identities and cached report data.

### Upgrade all behavioral readers before switching the writer

The highest-risk consumer is `projects::surface::project_surface_inner`: it currently reads the first marker under `prj_task.sub_block` to compute `open_subprojects`. The task-status-cycler mirror does the same in JavaScript. Both must recognize the new format before old marker removal. [C6, P4]

The parent-finished consequence is currently a **successor offer**, not automatic linking. Preserve that rule. Closing the last eligible child may surface the parent and offer it; the user must still select the link. Do not accidentally restore older auto-link behavior described in some historical comments. The audited accepted decision `decisions:unblocked-tasks-are-offered` governs this.

Also audit:

| Surface | Required work |
| --- | --- |
| Project sync and scan | Build the same effective lifecycle state, preserve tracked closed entries, plan region edits and lifecycle edits together |
| Rust and JS project-finished logic | Read both representations; use staged identities; no false empty result from missing/malformed data |
| Capture and section completion | Protect the catalog from ordinary note capture and project drawers; update affected parent presentation after project creation |
| Task/project promotion and reversal | Strip managed presentation deliberately; do not turn a whole catalog into task notes or lose authored prose |
| Relation/mention scanners and link marks | Keep navigation catalogs from becoming task dependency or mention edges; retain legacy recognizers |
| Note snapshots / Highlights PDF | Render the new section as a useful linked catalog with history; avoid duplicating the old task-card child row |
| Plugin data and rendering | Shared versioned report, cached refresh, Reading/Live Preview parity, Source-mode fidelity |

Relevant files and existing regression anchors are listed in C/P references. This is a cross-repository feature even though the visible change looks local.

### Reuse the safe writer, not just the pretty region

Notebook and album catalog sync use guarded planning, read-dependency validation, maintenance locking, and scoped commits. In contrast, the inspected `projects/sync.rs::apply_sync_plans` currently installs planned files with `fs::write`. Do not assume the older project writer already has the newer catalog transaction guarantees. [C2, C7]

Before a migration rewrites both task children and sections, route the resulting complete per-file plan through the shared guarded writer. Validate the host preimage and child inputs used for membership, lifecycle, title, and criterion; validate directory membership when newly created/deleted notes can affect results. Frontmatter-only guards are insufficient when the row reads `^prj` body text.

Compose catalog, status, schedule, and `#hide` edits against one planned text. Do not run separate writers that overwrite one another's result. Keep standalone and nightly lock ownership explicit so a nightly caller does not reacquire its own maintenance lock. Distinguish a committed-local/post-sync failure from a failed write, as the existing catalog infrastructure does.

A dry run should display the actual unified diff, including old-marker removal and new-section placement. Repeating sync with unchanged inputs should produce no diff. This is a prerequisite for reliable migration, not a proposal to rebuild every project command.

### Expose facts once for enhanced rendering

`bob projects list` currently has human output and no `-f json` option in the inspected CLI. Do not build UI by parsing that table or assuming an album-shaped endpoint already exists. [C8]

If rich row state is included in v1, add a versioned structured project report through `bob projects list -f json`, preserving existing human behavior and following the CLI rules. Include stable paths, effective lifecycle, safe display text, schedule/reason data where supported, catalog state, and findings. Keep “unknown/unavailable” distinct from zero. The plugin can then follow the existing album service's shared in-flight request, generation invalidation, last-good cache, and retry behavior. Report/paint must not write vault bytes.

A lean first slice can ship stable links/outcomes and Closed folding before richer state chips. Do not require a new configuration subsystem, schema language, or Mac capture grammar. Bob Mac Capture should benefit from corrected Bob semantics without client-specific parsing of the catalog.

## Migration and delivery sequence

1. **Lock the contract and fixtures.** Specify membership, current-state authority, source syntax, closed-history retention, ownership, empty/damaged behavior, and the reader union rules. Include the surprising cases below before polishing CSS.
2. **Ship compatible readers.** Update bob-cli and plugin lifecycle readers to accept both source layouts, plus capture/conversion/snapshot guards. Keep writing the legacy line in this compatibility stage. Verify current behavior on old notes.
3. **Implement the guarded new writer and preview.** Reuse the callout engine, add the child model and migration planner, and produce readable diffs. Preserve terminal parent notes by default; support mixed vaults indefinitely rather than bulk-rewriting closed history for visual uniformity.
4. **Deploy compatible clients before migrating active parents.** Check every host that writes/reads the vault; a newer CLI on one machine is insufficient if another host's old cycler still assumes the marker. Switch to writing one canonical callout only. Do not retain a permanent hidden second list under `^prj`.
5. **Finish the shared renderer.** Reading view and Live Preview use the same model and style; Source remains readable. Add rich state only through the structured report. Exercise real Obsidian, not only DOM mocks.
6. **Pilot and evaluate.** Preview representative notes, apply to a small controlled fixture/pilot set, confirm behavior, then migrate the remaining eligible active parents through the normal sync path. New clients can read reverted legacy Markdown; rolling clients back after vault migration requires restoring compatible source first.

The project's daily release-train policy applies to CLI changes. Coordinate the compatibility stages with that train; do not hand-edit release versions or publish an ad hoc release to rush migration.

## Acceptance cases that should decide whether this ships

| Area | Minimum evidence |
| --- | --- |
| Small layouts | Zero children has no empty panel; one child has no unnecessary group heading; all-closed retains a visible history disclosure |
| Large layouts | 20–50 direct children remain readable at narrow width; long titles/outcomes wrap; no descendant duplication or horizontal scrolling |
| Lifecycle parity | Open, future-scheduled, dependency-blocked, done, canceled, reopened, and terminal-parent cases retain current behavior |
| Parent-finished safety | One remaining open child suppresses a false finished offer; closing the last eligible child yields the same offer/recovery as before; no automatic successor link |
| Source compatibility | Legacy-only, new-only, and transitional mixed notes resolve consistently; conflicting/ambiguous data cannot imply empty |
| History | Already tracked closed rows survive migration; pruned ones stay absent; reopened ones return; reparented/deleted children do not remain under the wrong parent |
| Ownership | User prose and nonmanaged `^prj` bullets survive; examples in fences/frontmatter remain inert; moved sections stay moved; BOM/CRLF/EOF state survives |
| Identity | Aliases, duplicate display titles, exact path-qualified parents, ambiguous basenames, cycles, self-parent, and `root: true` have explicit tested outcomes |
| Capture/conversion | Catalog sections are not offered as writable drawers; project creation, task conversion, and reversal do not swallow or duplicate generated content |
| Transactions | Stale host, changed child criterion/state, new/deleted child during planning, incomplete scan, failure/rollback, and repeat no-op are tested |
| Rendering | Light/dark, Reading/Live Preview/Source, keyboard folds, focus retention, two panes with independent fold state, refresh failure, and cached/mobile fallback |
| Export | Snapshot/PDF remains legible and includes the intended closed history without duplicate lifecycle presentation |

Reuse and extend the existing project sync/surface, successor, notebook-region, and album UI test harnesses. Compare old and new fixture representations through the same lifecycle assertions. A successful Markdown snapshot alone does not establish behavioral parity.

## Explicit adjustments to the request

- **Interpret “their own H2 section” as one collection section**, not one section per child. Each child remains a separate note.
- **Defer H3s.** Use compact rows and one foldable Closed group. This is a deliberate design choice, not an omitted detail.
- **Keep hierarchy shallow in the parent view.** Show direct children; defer recursive trees and area-wide `## Projects` catalogs.
- **Reuse the completion criterion as context.** Do not require a new project summary property.
- **Retain curated closed history and current project semantics.** No automatic backlog/status changes, completion cascades, or implicit successor links arise from the visual redesign.
- **Include reader migration and guarded writes in the feature.** The code evidence makes them necessary for reliability.
- **Make rich statistics optional.** A tasteful navigational catalog is already useful without progress percentages, timers, or task-count rollups.

These choices keep the first release focused. The principal unresolved product question is whether routine navigation actually needs grandchildren visible at the parent. I would answer “no” initially and reopen it after using the direct-child catalog, rather than expand the data model and UI preemptively.

## Evidence locators

Paths below are relative to the named repositories at the revisions recorded above. Symbols are included to remain useful if line numbers move. These are inspected source and contract references, not unexecuted test results presented as passes.

| Ref | Repository and locator | What it supports |
| --- | --- | --- |
| C1 | bob-cli `docs/projects.md`, “Sync Rules,” especially generated Sub-projects and closed-history rules | Existing lifecycle, ordering, terminal behavior, and curation |
| C2 | bob-cli `src/native/projects/sync.rs:288`, `:396`, `:450`, `:791`; `scan.rs:129`, `:1121` | Graph aggregation, direct writes, desired entries, current stem-oriented matching |
| C3 | bob-cli `docs/notebooks.md:195`, “The catalog” | Author/machine ownership, notebook rollup scope, source protection |
| C4 | bob-cli `docs/records.md:26`, especially Records index and Owner catalogs | Album-vs-record distinction, stable catalog rows, conditional record subgrouping |
| C5 | bob-cli `src/native/host_catalog/region.rs:1`, `RegionSpec`, `plan_host`; `notebooks/catalog.rs::plan_catalogs` | Shared byte-span region engine and pure catalog planner |
| C6 | bob-cli `src/native/projects/surface.rs:1`, `project_surface_inner` | Local marker dependency in the EMPTY predicate |
| C7 | bob-cli `src/native/host_catalog/txn.rs:1`, `ReadDependencies`, `apply_and_commit`; `notebooks/sync.rs` | Guarded writer and standalone/nightly transaction composition |
| C8 | bob-cli `src/native/projects/mod.rs::build_cli`, `list_command`, `sync_command` | Current command surface; JSON extension is proposed, not existing |
| C9 | bob-cli `src/native/capture/sections.rs:539`, `:580`, `:617`; `capture/batch.rs` | Generated-section exclusion and explicit refusal pattern |
| C10 | bob-cli `src/native/task_children.rs:1`; `task_relations/parse.rs::is_subprojects_line`; `task_relations/mentions.rs` | Existing managed-child and relation/mention exclusions |
| C11 | bob-cli `src/native/highlights_ref/note_snapshot/bob.rs:529`, `is_subprojects_marker_line`, `subproject_items` | Current legacy task-card snapshot projection |
| C12 | bob-cli `tests/cli/projects/sync.rs`; `src/native/projects/tests/{surface,sync,edits}.rs`; `src/native/task_complete/tests/project_pull_in_tests.rs` | Regression anchors for history, source bytes, surface behavior, and parent-child close |
| C13 | bob-cli `src/native/capture/project_note.rs`; `capture_project_note.rs`; `tests/cli/capture/project_note.rs` | Project creation and staged capture integration points |
| P1 | bob-plugins `docs/albums.md`; bob-cli `evidence/album-schema-finish-escape/shots/album-records-reading.png` | Existing UI contract and inspected visual precedent |
| P2 | bob-plugins `plugins/bob-ledger-tools/src/241b-plugin-notebook-catalog-model.js`, `241c-plugin-notebook-catalog-dom.js`, `241d-plugin-notebook-catalog.js` | Nonwriting catalog models, DOM decoration, and lifecycle |
| P3 | bob-plugins `plugins/bob-ledger-tools/src/241m-plugin-album-data-service.js`; `241r/241s/241t` album-records fragments | Shared report/cache service and record grouping/folding surfaces |
| P4 | bob-plugins `plugins/task-status-cycler/src/089-successor-project.js:195`; `scripts/test-task-status-cycler-project-pull-in.cjs` | Legacy marker reader and mirrored lifecycle coverage |
| P5 | bob-plugins `plugins/bob-navigation-hotkeys/src/212-project-conversion.js:49`, `217-project-subprojects.js:1`, `665-plugin-project-conversion.js` | Managed-child stripping and path-aware hierarchy helpers |
| P6 | bob-plugins `plugins/bob-ledger-tools/src/145-relation-index-model.js:294`, `148-task-link-marks.js:676`, `285-plugin-task-link-marks-reading.js:18` | Additional old-marker recognition sites |
| P7 | bob-plugins `scripts/test-ledger-tools-notebook-catalog.cjs`, `test-ledger-tools-album-records.cjs`, `obsidian-notebook-ui-e2e.cjs`, `obsidian-album-ui-e2e.cjs` | Existing reusable UI verification harnesses |

Audited memory reads covered `sase_artifacts.md`, `cli_rules.md`, project/project-task/record/notebook/root-parent/leaf-project glossary entries, and decisions for notebook ownership, project blocking, inherited blocking, and explicit successor offers. The release-train rule was present in the supplied core decision roster. No memory or production source was changed for this research.

## Recommended solution

**Build one real `## Sub-projects` section containing a Bob-owned `[!subprojects]` catalog of direct children.** Render readable titles and completion criteria in compact rows, keep open children visible, fold retained closed history, and reuse the notebook/album visual language. Preserve plain Markdown and existing project authority in `parent:` and `^prj`.

**Ship dual-format readers and guarded migration before removing the old task-child marker.** Keep H3s, recursive trees, area catalogs, and progress dashboards out of the initial implementation. This delivers the requested clarity and beauty while concentrating engineering effort on the two things most likely to go wrong: preserving authored/history bytes and preserving project-finished behavior.
