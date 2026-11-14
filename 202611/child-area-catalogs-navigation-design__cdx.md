# Child-area catalogs: a quiet, dependable navigation layer

Independent research by **cdx**, 2026-11-14.

## Decision in brief

**Yes: add `## Areas`, but treat it as a directory of responsibilities rather than a second project dashboard.** Store a small `[!areas]` callout listing direct child areas, use the established catalog writer and transaction protections, and give it the same restrained styling as Projects. Show a bold note link and, when supplied, a short `summary:`. Keep task counts, progress, lifecycle controls, recursive trees, and a new area-creation gesture out of the first release.

The difficult work is not generating the bullets. It is making the exact `area.md` root eligible, preserving authored text, handling invalid parent links, coordinating section placement with Projects, and keeping automatic maintenance from repeatedly rewriting notes.

This report distinguishes existing behavior from proposed behavior. It is based on independent inspection of bob-cli at `9574e6185026b56744f75f60b1ec9e6e6c2a9b22`, bob-plugins at `d4b2bb2bf4ed255383fdf257706d62e979f713c4`, audited project memories, and official Obsidian/W3C documentation. No peer report, peer transcript, or peer findings were consulted. No live vault contents were inspected, no product code was changed, and no runtime UI validation was performed.

## 1. Is this a good idea?

The existing parent property provides upward navigation. A generated child directory completes the other direction: opening an area reveals the responsibilities it contains. This is especially useful at `area.md`, where it makes the top of the hierarchy browsable without remembering filenames or searching backlinks.

The benefit is coherence, not a new hierarchy. A child has one authored parent; the parent automatically offers the reverse link. That is a useful invariant users can learn once.

Three risks deserve restraint:

- **Too much furniture.** Areas, Projects, Notebooks, Albums, and Tasks can turn an otherwise useful note into a stack of panels. Add Areas only where there are children, keep it compact, and respect the author's chosen placement.
- **False progress signals.** An area has no finite outcome. A completion percentage, green check, or “empty” warning would suggest that ongoing responsibilities should finish. An area with no tasks can still be a perfectly useful place.
- **A second source of truth.** Manually editing catalog membership, deriving it from folders, or independently calculating it in JavaScript would make the hierarchy unreliable. Membership must remain a projection of the child's existing parent link.

I would choose a different approach only if the real goal were a global overview of every area and project. That would justify a dedicated dashboard or an optional tree view, not recursively expanding every note. The request as written is better served by a local directory.

## 2. What the current implementation already gives us

### Projects is a useful model, but its lifecycle is not

The documented Projects catalog lists direct child projects under an area or project. It resolves parent links by exact vault-relative path, then unique case-insensitive basename; uses path-qualified links where necessary; sorts open rows alphabetically; and owns only its callout. Project rows also have completion criteria, scheduled/blocked states, and closed history. Those latter features belong to finite projects. [Projects contract](https://github.com/bobs-org/bob-cli/blob/9574e6185026b56744f75f60b1ec9e6e6c2a9b22/docs/projects.md#L279)

The audited `glossary:area-note` explicitly defines areas as ongoing responsibilities without `^prj` tasks or a done/canceled lifecycle. This is the key reason to reuse the catalog structure without cloning the project row model.

### The shared catalog engine is the right foundation

`host_catalog::RegionSpec` already identifies a catalog's heading, callout, insertion position, and strict damage behavior. The byte-span planner preserves surrounding content and line endings, ignores fenced/frontmatter examples, repairs duplicate well-formed managed callouts, and refuses malformed openers for strict catalog kinds. It can remove an emptied heading when the section contains nothing else. [Region engine](https://github.com/bobs-org/bob-cli/blob/9574e6185026b56744f75f60b1ec9e6e6c2a9b22/src/native/host_catalog/region.rs#L1)

The transaction layer already provides the vault lock, pre-sync, guarded staged writes, rollback protections, read dependencies, and scoped commits. This should be reused rather than implementing another file writer. [Transactions](https://github.com/bobs-org/bob-cli/blob/9574e6185026b56744f75f60b1ec9e6e6c2a9b22/src/native/host_catalog/txn.rs#L1)

### Existing snapshots need a small but important extension

The notebook/catalog `VaultSnapshot` already discovers paths, records note kinds and parent facts, and retains bodies for areas, projects, notebooks, and albums. However, an untyped note's body is not retained. **Reusing that snapshot unchanged would miss an untyped `area.md` host.** This is an implementation hazard, not a claim about the actual contents of Bryan's `area.md`, which I did not inspect. [Snapshot retention](https://github.com/bobs-org/bob-cli/blob/9574e6185026b56744f75f60b1ec9e6e6c2a9b22/src/native/notebooks/snapshot.rs#L224)

Likewise, a previously managed host that changes type can fall out of normal host enumeration. Retaining its reserved callout for cleanup must be deliberate.

### The plugin already has the relevant presentation and refresh machinery

Projects uses compact rows, muted descriptions, a lightly tinted border/background, wrapping controls, and focus styles. Its report service coalesces refreshes, tracks generations, fingerprints changes before scheduling sync, and retains prior successful data on failure. These patterns are better starting points than creating a separate plugin. [Projects CSS](https://github.com/bobs-org/bob-plugins/blob/d4b2bb2bf4ed255383fdf257706d62e979f713c4/plugins/bob-ledger-tools/styles.css#L9137), [report/sync service](https://github.com/bobs-org/bob-plugins/blob/d4b2bb2bf4ed255383fdf257706d62e979f713c4/plugins/bob-ledger-tools/src/241ab-plugin-projects-data-service.js#L1)

The existing card has substantial project-specific behavior: state glyphs, task chips, closed rows, child disclosures, and a project capture starter. Sharing its presentation primitives is sensible; importing all of that behavior into Areas is not.

## 3. Proposed product contract

### Membership and eligible hosts

Use these rules consistently in reports, stored Markdown, and plugin presentation:

| Case | Recommended behavior |
| --- | --- |
| Ordinary note recognized as an area by the existing type parser | Eligible host; eligible child when its parent edge is valid |
| Exact vault-relative `area.md` | Eligible host regardless of its own type/frontmatter; never a child row |
| Project, notebook, album, record, reference, or other ordinary note | Never receives a new Areas catalog |
| Area explicitly parented to another area | Listed once in that immediate parent's Areas catalog |
| Area explicitly parented to `area.md` | Listed once at the root |
| Grandchild | Listed in its own immediate parent, not duplicated in ancestors |
| Area with no tasks or projects | Still listed; navigation does not depend on activity |
| Missing or invalid parent | Report the problem; do not guess a parent |
| Folder placement, filename prefixes, backlinks, `root: true`, task `[root::]` | Do not determine child membership |

Here `area.md` means `<selected vault>/area.md`, not a hard-coded home-directory path, and not every note whose basename happens to be `area`. Honor the existing vault exclusions. Do not manufacture the root file if it is absent.

Keep the root exception local to this feature. Retaining its bytes for catalogs must not reclassify it globally as an ordinary area, a task home, or a time-reporting root.

### Parent resolution and invalid data

Reuse `NoteIndex` and the established path-preserving wikilink parsing semantics. The shared resolver first tries an exact path and then the unique basename; it can distinguish missing from ambiguous results. The existing project helper rejects self-parenting but returns only `Option`, so a diagnostic-rich Areas analyzer should use the detailed result and preserve the failure reason. [Link resolver](https://github.com/bobs-org/bob-cli/blob/9574e6185026b56744f75f60b1ec9e6e6c2a9b22/src/native/vault_links.rs#L150), [project parent helper](https://github.com/bobs-org/bob-cli/blob/9574e6185026b56744f75f60b1ec9e6e6c2a9b22/src/native/project_dependencies/tree.rs#L19)

Require one unambiguous parent declaration. Detect duplicate keys and actual list-valued parents instead of accepting whichever entry a convenience reader happens to encounter. Preserve compatibility with Bob's existing unquoted `[[parent]]` input convention where the current parser accepts it; recommend quoted text in documentation and templates. Obsidian itself documents quoted wikilinks for text properties. [Obsidian properties](https://obsidian.md/help/properties)

Diagnose missing targets, ambiguity, wrong parent kinds, self-links, and cycles. Do not render links that participate in a detected cycle as a valid hierarchy. Cycle detection should run over the resolved area graph, not depend on recursive rendering.

A bad ancestor should not erase unrelated useful navigation: if `child → parent` is a valid immediate area edge but `parent` lacks its own parent, `parent` can still show `child`. Report the parent's defect separately. Similarly, omit the edges inside a cycle while retaining valid incoming children outside that cycle. There is no need to make every local catalog contingent on the entire ancestry reaching the root.

`area.md` is a terminal sentinel for this catalog graph. Never follow its own parent to make it another child. A missing root or invalid top-level edge remains visible in diagnostics rather than silently turning an orphan into a top-level area.

### Row content

Canonical stored form:

```markdown
## Areas

> [!areas]
>
> - **[[dev]]** — Software, tools, and technical practice.
> - **[[health]]** — Movement, sleep, and care.
> - **[[home]]**
```

Each row contains exactly one ordinary note link and an optional inert text summary. Use the familiar filename stem for the label, matching Projects. If a short link would resolve to a different note, use `path-without-md|stem`. Where two rows have the same visible stem, show a small parent-folder qualifier so the distinction is available without hovering.

Use the child's optional `summary:` property for the description. Do not scrape its first paragraph or task list, invent a description, require a migration, or show “missing summary” nags. Decode a text value, collapse whitespace, and escape it using the existing inert-text machinery so it cannot create extra wikilinks, tags, task fields, or HTML. A missing or non-text summary does not hide the child; report malformed supplied values separately. [Existing inert-text helper](https://github.com/bobs-org/bob-cli/blob/9574e6185026b56744f75f60b1ec9e6e6c2a9b22/src/native/notebooks/catalog.rs#L285)

Prefer one concise sentence in authoring guidance, but do not truncate stored data or reject an otherwise valid area for description length. Omit an empty tail and a tail that merely repeats the label.

Sort by stem, case-insensitively, then by vault-relative path, using the same deterministic comparator as the Rust project planner. The plugin should preserve that order rather than independently applying locale-dependent sorting. No activity sorting, drag ordering, or manually persisted rank in v1.

### Empty, stale, and damaged catalogs

- A leaf gets no generated Areas section. Do not add “No areas yet” placeholders across the vault.
- Removing or reparenting the last child removes the managed callout. Remove its matching H2 only when the remaining section is whitespace; preserve any authored prose and heading that still contains it.
- A hand-deleted generated row returns on sync because the parent property remains authoritative.
- Reparenting updates the old and new host catalogs in the same planned transaction when both are healthy.
- Retyping a former area causes its old managed Areas callout to be removed, while its remaining content is preserved. This is cleanup, not permission to create catalogs in project notes. Detect existing real callouts on otherwise ineligible, non-excluded notes for that purpose.
- A malformed `[!areas` opener refuses edits to that host and identifies the physical source line. Healthy unrelated hosts may still update, but the result must clearly report partial completion.
- A filesystem discovery/read failure is different from a malformed document. Treat an incomplete snapshot as unsafe for removals and refuse writes rather than interpreting unreadable children as deleted.

Reusing the shared engine means duplicate well-formed `[!areas]` blocks are recognizable machine-owned duplicates: retain the first position and regenerate one catalog. Do not describe all duplicate regions as damage when existing catalogs deliberately self-heal this case.

## 4. Layout and appearance

### Default placement

On first insertion, the navigation order should be **Areas, then Projects**, followed by the note's existing sections. Do not move either catalog once Bryan has positioned it.

The existing Projects spec inserts before the first H2. Giving Areas that same placement independently is insufficient: the relative order would depend on which catalog appeared first. Add a focused placement rule rather than a vault-wide section sorter:

1. An existing valid managed callout stays exactly where it is.
2. When a single authored `## Areas` exists without a callout, insert into that section without replacing its prose or creating another H2. If several candidate headings make the target ambiguous, report it rather than guessing.
3. Otherwise, create Areas before an existing Projects section; if none exists, before the first real H2, or at EOF when there is none.
4. When Projects is first created in a note that already has Areas, insert it after the Areas section. Existing Projects placement remains unchanged.

Item 4 is a justified, narrowly scoped change to existing Projects behavior. Do not rely on nightly step order to solve it. Test both command orders and notes where one catalog arrives months after the other. The current `AfterSectionThenTasks` fallback is also not an exact fit: this rule needs a first-H2 fallback to preserve Projects' present behavior when Areas is absent. [Placement implementation](https://github.com/bobs-org/bob-cli/blob/9574e6185026b56744f75f60b1ec9e6e6c2a9b22/src/native/host_catalog/region.rs#L696)

### Visual direction

Use a small, single-column catalog, not individual tiles or a table. The bold link is the primary visual target; the summary is secondary. Use the existing catalog radius, typography, spacing, and restrained host hue. Let `area.md` use a neutral accent rather than inventing a new color identity. Avoid a state ring next to every area: Projects uses that shape to communicate lifecycle, which Areas does not have.

Illustrative rendered composition, not a screenshot:

```text
Areas                                      3 areas
┌────────────────────────────────────────────────┐
│ dev                                            │
│ Software, tools, and technical practice.        │
│                                                │
│ health                                         │
│ Movement, sleep, and care.                      │
│                                                │
│ home                                           │
└────────────────────────────────────────────────┘

Projects
[the existing Projects catalog]
```

At wider sizes the summary may sit on the same line after an em dash; at narrow sizes it wraps naturally. Missing descriptions simply produce shorter rows. Keep text selectable and preserve normal Obsidian link behavior, including modifier-click and link menus. Do not turn the whole row into a custom button.

The H2 should remain the document's primary section heading and navigation anchor. The enhancement can place a count beside it or in a subdued card header, but should avoid a second equally prominent “Areas” title. Without the custom plugin/styles, the callout's ordinary title is an acceptable fallback.

Obsidian supports Markdown and wikilinks inside callouts, custom callout types, and native foldable callouts. An unsupported type falls back to a normal note callout, which makes `[!areas]` a useful portable base. [Obsidian callouts](https://obsidian.md/help/callouts)

For v1, keep all direct children visible and rely on normal heading folding if a long section gets in the way. Do not add arbitrary “show five” truncation or a recursive explorer before observing actual catalog sizes. If a later design introduces a disclosure, use a real button, Enter/Space operation, and `aria-expanded`; keep the link as a separate target. [WAI disclosure pattern](https://www.w3.org/WAI/ARIA/apg/patterns/disclosure/)

Test wrapping at a 320 CSS-pixel content width and with enlarged text, without horizontal scrolling or hover-only access to summaries. This follows the reflow principle in WCAG's explanation; it is an acceptance target, not a claim of audited accessibility conformance. [W3C reflow guidance](https://www.w3.org/WAI/WCAG22/Understanding/reflow.html)

### What should stay out of the card

No completion checkboxes, percent done, “healthy” scores, closed group, due dates, Today badges, task totals, or red empty-area indicators. These would change the purpose from navigation to evaluation. The first useful count is simply the number of directly listed areas.

Do not copy the Projects “＋ project” button as “＋ area”: there is no demonstrated matching area-creation contract in the inspected command surface. Creating areas is a separate workflow decision.

## 5. Refresh, safety, and fallback behavior

### Give Bob one authoritative analyzer

Add an `areas` module with a pure analyzer/planner over a vault snapshot. Produce resolved edges, per-host ordered rows, catalog state, and findings from the same analysis. The stored catalog and JSON report must use those same results.

A minimal read report can contain a schema version, overall health, area entries, host catalogs with ordered child paths, and path/line/code diagnostics. Catalog states should match existing terminology: `current`, `missing`, `stale`, and `damaged`. Distinguish a partial scan from a complete scan with invalid documents.

Do not reuse `HomeResolver` as the membership engine. It answers time attribution and nearest-home questions, walks several note kinds, and has different stopping rules. Area membership is the direct resolved parent edge plus the explicit allowed-parent rule. Existing ancestry color helpers may still be reused for presentation without making them authoritative for membership.

### Proposed public surface

| Command | Purpose |
| --- | --- |
| `bob areas` / `bob areas list` | Read-only area inventory and catalog report; bare group defaults here |
| `bob areas list -f json` | Versioned report for the plugin |
| `bob areas check` | Read-only hierarchy and catalog diagnostics |
| `bob areas sync -d` | Preview the exact catalog changes |
| `bob areas sync` | Guarded catalog maintenance |

This is a proposal, not a claim these commands exist. Follow the project's CLI rules: alphabetized commands/options, short aliases for public long options, strong help, and a read-only bare default. Do not enlarge `bob projects sync` into an unrelated area writer or introduce a general `bob hierarchy` framework just to save one noun.

Document exits consistently with sibling catalog commands: success/no-op is zero; incomplete maintenance or check errors are nonzero; argument/validation refusals use the existing convention. A useful dry run must require neither a live Obsidian process nor a writable Git checkout.

### Transactions and automatic maintenance

Standalone sync should use the existing lock, pre-sync, snapshot, staged guarded install, verification, scoped commit, and post-sync machinery. Guard both destination preimages and read dependencies that determine membership: parent/type/summary facts and the note-path namespace used for resolution. A new same-named file arriving after planning can change whether a link is ambiguous even if no existing file changed.

No-op sync writes no bytes and makes no commit. A concurrent host edit or a changed dependency refuses/replans instead of overwriting it. Reparenting must never be implemented as two independent unguarded writes.

Add a lock-held Areas maintenance step to `bob nightly`, using the same pattern as Projects/Notebooks/Albums and no nested lock or extra sync cycle. This changes the maintenance program, not the machine's crontab. [Nightly sequence](https://github.com/bobs-org/bob-cli/blob/9574e6185026b56744f75f60b1ec9e6e6c2a9b22/src/native/nightly.rs#L25)

For immediate desktop feedback, extend `bob-ledger-tools` with a coalesced report/sync service patterned on the existing Projects service. Watch relevant create/delete/rename and semantic type/parent/summary changes. Track prior host identity so retyping still cleans old output. A path change to a non-area note can also alter basename ambiguity, so namespace invalidation must not be restricted solely to currently recognized areas.

Do not run one process per card, resync on every ordinary task edit, or treat the catalog's own rewrite as another membership change. Keep one in-flight maintenance operation, debounce bursts, and ensure an older report cannot replace a newer generation. Share scheduling primitives where practical; do not first undertake a general rewrite of all catalog services.

### The stored list remains useful throughout

Areas has no volatile metrics, so there is little benefit to replacing the whole stored list with a separate live-only tree. Style the stored links; use the authoritative report for host eligibility, health, and repair actions. While it is stale, preserve the list and show a restrained update affordance. Do not display a fresh count beside an older list whose membership differs.

| State | User experience |
| --- | --- |
| Current | Links and optional count; no success banner |
| Missing/stale | “Update catalog” invokes Bob's sync |
| Damaged opener | Explain the source problem and offer opening the affected line; sync cannot safely guess a repair |
| Report failure on desktop | Keep stored links/last good state; offer Retry without clearing content |
| Mobile or Bob unavailable by design | Ordinary readable callout; no permanent failure banner |

Never inject an anchor into arbitrary non-host notes just because a report is unavailable. The exact root and report-recognized hosts need deliberate eligibility handling.

## 6. Integration points that are easy to overlook

1. **Shared generated-heading registry.** Add Areas to `GENERATED_CATALOGS`, but also update the separate selector-error table. Merely hiding it from completion is insufficient: an unmatched `@host#areas` selector must not fall through and write somewhere else. Introduce an explicit `areas_section_generated` refusal and guidance to choose a child area or another section. [Capture protection](https://github.com/bobs-org/bob-cli/blob/9574e6185026b56744f75f60b1ec9e6e6c2a9b22/src/native/capture/sections.rs#L563)
2. **Task-container operations.** Generated headings are structural. Audit drawer completion, task move/merge/split, and section targeting so generated rows never become task or note destinations. The common registry already feeds part of this behavior. [Drawer exclusions](https://github.com/bobs-org/bob-cli/blob/9574e6185026b56744f75f60b1ec9e6e6c2a9b22/src/native/capture_drawers.rs#L533)
3. **Snapshot retention.** Preserve full bytes for the exact root and eligible cleanup targets without changing global note kinds. An `AREA.md`, a nested `area.md`, a project named `area`, and an untyped real root need separate fixtures.
4. **Exports.** Projects receives special PDF snapshot handling for its lifecycle rows. Areas should at least preserve its ordinary links and descriptions through generic callout export; verify that the custom marker is not leaked as visible junk or dropped. Do not copy the Projects closed-row filtering. [PDF snapshot handling](https://github.com/bobs-org/bob-cli/blob/9574e6185026b56744f75f60b1ec9e6e6c2a9b22/src/native/highlights_ref/note_snapshot/bob.rs#L332)
5. **Documentation and packaging.** Add the area catalog contract, CLI/help/completion coverage, nightly description, and plugin documentation. Plugin work belongs in the source-of-truth bob-plugins repository, with its generated build and deployment workflow. This research does not itself change those files.

## 7. Alternatives considered

| Approach | Benefit | Why I would or would not choose it |
| --- | --- | --- |
| Plain generated bullet list under H2 | Very small implementation | Ownership boundaries are less explicit; loses consistency with the existing managed-callout engine |
| Dataview/live query only | No stored catalog drift | Makes navigation depend on query/plugin availability and adds another implementation of parent semantics |
| Plugin-only navigation widget | Rich interaction, no Markdown writes | Absent from source/export and weaker without the plugin; unnecessary for a small stable directory |
| Full recursive Areas/Projects tree | Strong overview | Duplicates descendants, grows quickly, and obscures the local parent-child relationship |
| Combined “Children” section | Fewer headings | Hides the distinction between ongoing responsibilities and finite projects; changes an established Projects experience |
| `[!areas]` with direct links and optional summaries | Portable, consistent, maintainable | Adds stored derived text and another sync surface; existing infrastructure contains most of that cost |

The final option best satisfies the current request. A unified overview could be a later separate view if real usage shows a need; it should not be a prerequisite.

## 8. Explicit requirement adjustments

These are proposed additions or refinements, not assumptions hidden inside “similar to Projects”:

- **Clarify direct children only.** Each parent lists one level; no rollup and no recursive expansion in v1.
- **Treat `area.md` as an explicit root exception.** Its type must not accidentally gate the feature. Do not reinterpret the root in unrelated systems.
- **Add optional `summary:` support for areas.** This supplies context and visual rhythm without requiring new metadata on existing notes.
- **Keep area lifecycle and workload out.** Areas remain useful when they contain no active tasks; no project-style status markers or closed history.
- **Specify default Areas-before-Projects placement.** This requires a narrow first-insertion adjustment to Projects and reuse of a single existing Areas heading, while preserving moved content.
- **Specify invalid-data and cleanup behavior.** Do not silently infer root membership, turn read failures into deletions, or leave generated catalogs behind after a host changes type.
- **Include automatic upkeep and a static fallback.** Nightly and debounced desktop sync make the feature dependable; source Markdown stays sufficient to navigate.

I would not add configurable ordering, icons per area, required descriptions, a new creation grammar, or a new general hierarchy subsystem as part of this work.

## 9. Delivery sequence and acceptance criteria

### A. Establish the contract and pure planner

Implement the area inventory/edge diagnostics, root exception, summary rendering, cleanup eligibility, and `AREAS` region specification. Use existing snapshot, index, and transaction types. Extract only the small shared helpers that this second caller actually needs.

### B. Complete maintenance and safeguards

Add read/check/sync commands, dry-run diffs, generated-section protections, and the nightly step. Settle first-insertion behavior with Projects. Verify the data and stored representation before adding UI complexity.

### C. Add matching Obsidian presentation

Add the restrained styles and shared refresh/sync integration in bob-ledger-tools, covering both reading mode and Live Preview. Preserve links and the source fallback. Release the writer and its styling as one coherent feature after both are ready.

| Test family | Required evidence |
| --- | --- |
| Membership | Root with and without frontmatter; nested areas; only direct children; projects never gain new Areas catalogs; zero-task children stay listed |
| Identity | Exact-path precedence, duplicate stems, case differences, aliases/heading suffix parsing, renamed paths, nested `area.md` distinct from root |
| Invalid hierarchy | Missing/list/duplicate parent, wrong-kind parent, self-link, two-node and longer cycles; useful valid children remain visible despite an orphan ancestor |
| Ownership | Authored prose before/after callout, a single pre-existing H2, ambiguous duplicate headings, fenced examples, malformed openers, duplicate managed blocks, BOM/CRLF |
| Removal | Last child disappears; old/new parent update; host retyping; last child becomes a project; missing root never auto-created |
| Determinism | Repeat sync is byte-identical/no commit; Areas then Projects and Projects then Areas give the same default order; manually moved catalogs stay put |
| Concurrency | Host edited after planning, child parent/summary edited, new ambiguous filename introduced, partial scan, rollback preserves later user edits |
| Rendering | Long names/descriptions, absent summaries, escaped Markdown, duplicate visible labels, light/dark themes, narrow panes and enlarged text |
| Fallback | Plugin disabled, Bob unavailable/mobile, report failure, stale report, no phantom cards; links remain usable |
| System boundaries | Capture rejects generated targets; task/lifecycle/root metrics unchanged; export preserves area navigation; nightly reuses its lock |

BOM preservation by the region editor does not itself prove that the classifier recognizes BOM-prefixed frontmatter: test classification and rendering together. Likewise, an insertion helper passing its own unit tests does not prove it composes correctly with Projects.

This sequence is deliberately smaller than cloning the entire Projects feature: no project lifecycle calculation, task aggregates, closed sorting, child expansion, or new capture operation. The remaining cross-cutting work is still substantive and should not be estimated as “just another heading.”

### Remaining uncertainty

Source inspection establishes suitable extension points, not actual vault size, current area description coverage, the contents of the real root note, or visual fit in Bryan's theme. The design intentionally avoids depending on those unknowns. Before release, inspect a preview against representative notes and confirm it preserves authored content; use real sibling counts to decide whether folding needs more than the existing heading affordance. No benchmark or live UI result is claimed here.

## Recommended solution

Implement **a direct-child `## Areas` catalog backed by `[!areas]`, generated by Bob and lightly styled by bob-ledger-tools**. Eligible hosts are typed areas plus the exact vault-root `area.md`; membership comes only from valid explicit parent links. Use stable links, alphabetical order, optional escaped `summary:` text, and no workload or lifecycle badges. Default Areas above Projects on first creation, then respect the author's placement.

Reuse the existing catalog and transaction infrastructure, add a small diagnostic-rich Areas analyzer and `list/check/sync` surface, protect the generated section from capture, and connect nightly plus debounced desktop upkeep. Handle the root exception, old-host cleanup, and section-order interactions as first-class acceptance cases. This offers the navigation improvement Bryan wants while keeping the result readable, dependable, and visually calm.
