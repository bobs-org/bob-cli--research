# Prose and notebook cards: useful context without overwhelming the writing

Independent research by **cdx**, 2026-11-26. Scope: design and implementation recommendation, including interaction with `bob-cli-qi` and `bob-cli-qj`. This is research, not an approved implementation plan. No other report from this swarm, peer transcript, or peer findings were consulted. No live-vault notes or product code were changed.

## Recommendation

**Build both cards as compact members of the existing Property Card family in bob-ledger-tools.** Give them one title, one Properties foot, the existing keyboard behavior, and conditional native-Properties takeover. Let the Prose Card orient the writer within a document; let the Notebook Card orient the reader within a collection. Prefer a few meaningful facts and destinations over a dashboard.

Implement in parallel with `qi` and `qj`, but coordinate three narrow boundaries: shared card ownership, the prose plugin's report API, and final deployment. There is no reason to block all work on either entire epic. Conversely, “no coordination needed” would repeat precisely the multiple-owner problem that `qi` is fixing.

The strongest adjustments to the request are:

1. **“Hide Properties” means successful, reversible takeover in supported views.** Source mode, unsupported contexts, invalid YAML, failed mounts, and missing editor capability retain native access.
2. **“Rich” means useful derived context, not more frontmatter.** Do not add stored counts, last-edited timestamps, completion percentages, publishing status, or new task policies to make the cards look substantial.
3. **Replace the notebook's existing header within the card's supported surface.** Do not stack two independently mounted headers.
4. **Preserve prose semantics and wire compatibility.** `[[article]]` remains a permanent spelling; `bob-articles` remains the plugin id; prose still reports generic `note` in `props`. An area or project with prose in its body does not get a Prose Card.
5. **Do not headline the current prose word or stub counts.** Experiments found that heading numbering changes `outline.words`, and an organizational heading with populated subsections can be a stub. Ship structure and navigation first; a stable word count is a separate, additive enhancement.
6. **The requested glossary terms should describe shipped behavior.** Include the draft definitions below in implementation work, then publish them with the feature. Do not install speculative memory during research.

## Evidence and confidence

The source snapshots were bob-cli `478d5233100d45ba27d1bf29530eb790a36a8837` and bob-plugins `86f5f3409ff5594fe9da2830c69096a3e86531bb`. These are independently opened checkouts; they are not a claim about every host's installed version. The primary checkout still has article-named source, while the approved `qj` plan describes its successor. Active work can change these anchors before implementation.

| Evidence | What it establishes |
| --- | --- |
| Audited `sase bead read bob-cli-qi bob-cli-qj` and `sase artifact read plan:202611/bank_hub_demotion.md`, `plan:202611/prose_note_type.md` | Epic scope, selected decisions, compatibility promises, ownership and deployment overlaps |
| Audited decisions roster and `decisions:notebook-routes-write-notes`; glossary reads for Property Card and Notebook | Notebooks remain task-free bullet collections; parent/owner/root have distinct meanings; cards are read-only projections with guarded takeover |
| [Notebook contract](https://github.com/bobs-org/bob-cli/blob/478d5233100d45ba27d1bf29530eb790a36a8837/docs/notebooks.md), [report model](https://github.com/bobs-org/bob-cli/blob/478d5233100d45ba27d1bf29530eb790a36a8837/src/native/notebooks/model.rs), [scanner](https://github.com/bobs-org/bob-cli/blob/478d5233100d45ba27d1bf29530eb790a36a8837/src/native/notebooks/scan.rs) | Titles, counts, recency, hierarchy, diagnostics, and current JSON limitations |
| [Article/prose contract](https://github.com/bobs-org/bob-cli/blob/478d5233100d45ba27d1bf29530eb790a36a8837/docs/articles.md), [outline implementation](https://github.com/bobs-org/bob-cli/blob/478d5233100d45ba27d1bf29530eb790a36a8837/src/native/articles/outline.rs) | Title and numbering precedence; source/output line distinction; word and stub semantics |
| [Props classification](https://github.com/bobs-org/bob-cli/blob/478d5233100d45ba27d1bf29530eb790a36a8837/src/native/props/roles.rs), [settings registry](https://github.com/bobs-org/bob-cli/blob/478d5233100d45ba27d1bf29530eb790a36a8837/src/native/props/contract/settings.rs) | Notebook is a known kind; prose is generic note; typed settings currently belong to area/project |
| [Card host](https://github.com/bobs-org/bob-plugins/blob/86f5f3409ff5594fe9da2830c69096a3e86531bb/plugins/bob-ledger-tools/src/240c-plugin-property-card-host.js), [species](https://github.com/bobs-org/bob-plugins/blob/86f5f3409ff5594fe9da2830c69096a3e86531bb/plugins/bob-ledger-tools/src/240f-plugin-property-card-species.js), [takeover](https://github.com/bobs-org/bob-plugins/blob/86f5f3409ff5594fe9da2830c69096a3e86531bb/plugins/bob-ledger-tools/src/240q-plugin-property-card-frontmatter-ownership.js) | Existing lifecycle and chrome; species allowlists and path attributes need explicit extension |
| [Notebook service](https://github.com/bobs-org/bob-plugins/blob/86f5f3409ff5594fe9da2830c69096a3e86531bb/plugins/bob-ledger-tools/src/241a-plugin-notebook-data.js), [header model](https://github.com/bobs-org/bob-plugins/blob/86f5f3409ff5594fe9da2830c69096a3e86531bb/plugins/bob-ledger-tools/src/241e-plugin-notebook-header-model.js), [header mounts](https://github.com/bobs-org/bob-plugins/blob/86f5f3409ff5594fe9da2830c69096a3e86531bb/plugins/bob-ledger-tools/src/241f-plugin-notebook-header.js) | Shared list/cache/sync machinery and ancestry UI already exist |
| [Prose outline lifecycle](https://github.com/bobs-org/bob-plugins/blob/86f5f3409ff5594fe9da2830c69096a3e86531bb/plugins/bob-articles/src/035-plugin-look.js), [plugin lifecycle](https://github.com/bobs-org/bob-plugins/blob/86f5f3409ff5594fe9da2830c69096a3e86531bb/plugins/bob-articles/src/030-plugin.js) | Private outline cache exists, but a supported versioned subscriber API is new work |

Confidence is high in the architectural fit and compatibility constraints, and moderate in the proposed visual hierarchy until real Obsidian review. No real-app screenshots were produced in this research. Existing docs can lag active work: for example, the opened Area/Project card doc says native Properties remain visible, while the code already has a capability-gated takeover and `qi` explicitly includes the documentation sweep. Use source plus approved acceptance requirements, not that sentence as a precedent.

### Small experiments that materially changed the recommendation

Used the installed `bob 0.6.0`, binary SHA-256 `63262ba9a2160c84a1e0d684063a87e79be9a2eb1261549d82637845bae569da`, against disposable vaults inside this workspace. The binary's commit is not known; the observations agree with the inspected source. Temporary files were removed.

**Notebook fixture:** three column-zero notes, a nested detail stamped later than its parent, two `## Ideas` headings, and a fenced example with an even later date. `bob notebooks list -f json -b FIXTURE` returned:

- `notes: 3`; nested detail and the fenced example did not increase the count.
- `last_note: 2026-11-25`, taken from the nested detail, not the fenced 2026-11-26 example.
- Two separate `{title: "Ideas", notes: 1}` entries, with no section line or stable id and no issue for duplication.

Consequences: call the date **Latest dated note**, not **Last edited** or **Last captured**. Do not turn section labels into naive `#Ideas` links; those cannot distinguish the two sections.

**Prose fixture:** a title in frontmatter followed by:

```markdown
# Umbrella

## Child

Actual body words.

## Later

TODO
```

`bob articles outline essay -b FIXTURE -f json` reported 3 sections, 10 words, and `stub: true` for both Umbrella and Later. Formatting only added heading numbers; a second outline reported 13 words. Thus `words` currently includes heading syntax/number tokens, and `stub` means an empty or TODO-like *immediate body*, not unfinished subtree or incomplete document. A “67% unfinished” indicator would be wrong.

`bob props show … -f json` confirmed the prose fixture is `note_kind: note` with `props_v1`; the notebook has its own kind. `title`, `parent`, and notebook `summary` are loose properties, not species settings. The initial read-only probes left all fixture bytes unchanged; the formatting comparison intentionally changed only its disposable prose fixture.

Three existing plugin suites passed at the pinned plugin revision:

- `node scripts/test-ledger-tools-property-card-frontmatter-ownership.cjs`: 27 tests.
- `node scripts/test-ledger-tools-notebook-header.cjs`: 21 tests.
- `node scripts/test-bob-articles.cjs`: 23 tests.

These validate the reused foundations, not the proposed cards or their actual Obsidian rendering.

## Is this a good idea?

Yes, provided the card earns the space it occupies. Raw YAML is a poor default opening for authored writing: internal type/template metadata dominates, while document structure and notebook navigation are elsewhere. A compact card can answer “what is this?”, “where does it belong?”, and “where can I go next?” in one stable place.

The main danger is copying the Area/Project card's *contents* instead of its interaction contract. Prose and notebooks are not task homes. Ready caps, freshness warnings, productivity scores, WIP badges, clock defaults, and activity pressure would misrepresent them. A notebook that has not changed in months may be an excellent reference collection. A prose note without TODOs is not necessarily finished or published.

Nor should “rich data” require authors to maintain extra fields. Notebook summary already expresses collection scope; prose already supports a publication/display title and section-numbering option. Parent and created metadata exist too. Their meaning matters more than the number of keys.

Alternatives considered:

| Approach | Assessment |
| --- | --- |
| Keep native Properties and add a small navigation strip | Cheapest, but duplicates the existing card language and does not meet the requested presentation |
| Add separate prose/notebook plugins with independent card frameworks | Creates extra lifecycle, ownership, keyboard, and deployment surfaces; little benefit |
| Render a large outline, backlinks, statistics, and action toolbar by default | Gives useful features too much visual priority and pushes writing down; favors collapsed detail instead |
| Persist derived metrics into YAML | Adds writers, sync churn, and misleading freshness; rejected |
| Extend the existing family with species adapters and shared reports | Best balance of consistency, reliability, useful context, and implementation cost |

Obsidian itself treats properties as small structured values and provides separate document visibility modes and a File Properties sidebar. That supports keeping arbitrary YAML reachable while using the card as the normal view. It does not justify changing the user's global Properties setting. [Obsidian Properties](https://obsidian.md/help/properties), [Properties view](https://obsidian.md/help/plugins/properties).

## Proposed experience

### Shared visual language

Use the existing card spacing, title block, foot, fold affordance, and theme variables. Species is communicated by **form, icon, and the word**; inherited home hue communicates location. Do not invent a blue Prose category and a green Notebook category that disagree with the rest of Bob.

Suggested identities: Prose uses a restrained page/pen tile and `PROSE`; Notebook uses a bound-outline tile and `NOTEBOOK`. Confirm the icons against existing Record and Album tiles in grayscale: a second generic file icon alone is insufficient distinction. Reuse shared tile geometry where possible; the kicker must always disambiguate.

Default view has a compact identity block, an optional summary, and one quiet fact/navigation row. The Properties foot stays in its usual position. Use at most two summary lines in the compact view, with the full value available through expansion or the editor. Long titles wrap; they are never clipped into indistinguishable fragments. Keep the body reading font and line-number/section-number layout controlled by Bob Prose, independently of card typography.

Conceptual layouts, with illustrative values rather than actual vault data:

```text
[page/pen]  PROSE  ·  Development › SASE
            Why I built SASE
            A short account of the ideas behind the tool.
            8 sections ↗                 Numbering on
            Created Nov 12       Properties · 5   −  +

[notebook]  NOTEBOOK  ·  Development
            Linux
            Machine setup, shell shortcuts, and troubleshooting.
            34 notes · 6 sections ↗ · Latest dated note Nov 25
            2 child notebooks ↗
            Created Nov 9        Properties · 5   −  +
```

The collapsed `_` state retains species, title, location, and foot. Optional summary, readouts, and child previews fold together; it does not collapse the note body. Expanded detail is bounded and does not automatically turn into a full-page table of contents. At narrow pane widths, keep title and immediate parent, collapse middle ancestry into an accessible chooser, and wrap the single readout row. Avoid horizontal scrolling or a row of unlabeled icons. Use text labels and focus indicators, not color alone; control names should describe their action and expanded state.

### Prose Card: orientation for authored writing

| Element | Authority and exact behavior |
| --- | --- |
| Title | Existing prose precedence: nonblank `title`, otherwise file stem. Do not silently switch to first H1: prose H1s can be numbered content sections. |
| Location | Resolve the authored parent to a real path with existing navigation helpers. Show available ancestry compactly; unresolved parents remain understandable, without an invented owner or hue. Do not impose notebook parent rules on prose. |
| Summary | Optional plain scalar `summary`, when authored. It describes the document's point or scope. Do not scrape the lede or generate a summary. Absence is normal. |
| Structure | `outline.sections.length`, labeled “sections” with an outline action. Show a bounded outline with depth and existing numbering; use source-bound anchors. |
| Numbering | Show On/Off, with the implicit default distinguishable in the editor. An explicit toggle invokes `bob-articles:toggle-section-numbers`, the command owned by `qj`; it must not merely set a YAML boolean. |
| Findings | One quiet foot indicator for actual diagnostic findings, opening the affected source line or a small list. A formatter refusal is not a successful zero-section report. |
| Created and arbitrary properties | Shared foot and full Property Editor; no duplicate created label in the metric row. |

Do not hide a prose heading just because it is the first H1 or matches the title after de-numbering. Under the current engine it can be a real section with inbound links. **V1 should own the inline title, while leaving all prose body headings visible.** This is a deliberate species-specific exception to title-range hiding, not a new title-writing rule. Later redundant-title suppression would need explicit agreement with the formatter/outline semantics.

Do not expose `stub` as a score or warning about unfinished work. It can be an optional outline annotation with its literal meaning, but is not necessary for launch. Do not show `outline.words` as a stable writing metric. If a word count is prioritized later, add an authoritative, formatting-invariant field such as `content_words`, with tested treatment of headings, links, inline/fenced code, comments, math, and Unicode. Keep the old wire field for compatibility; do not substitute a new JS whitespace counter. Defer reading-time estimates with it.

### Notebook Card: orientation for a collection

| Element | Authority and exact behavior |
| --- | --- |
| Title | Existing notebook precedence: eligible opening H1, first alias, humanized stem. This differs legitimately from prose. |
| Breadcrumb | Reuse notebookHeader's path-aware ancestry. Parent is immediate container; owner is the nearest area/project; root is the reporting root. Avoid presenting all three as redundant badges. |
| Summary | Existing scope statement. When missing, a discreet “Add summary” action focuses a preseeded editor field; no alert banner. |
| Notes | Existing direct column-zero note count; nested detail and child notebooks are excluded. Tooltip states the scope. |
| Sections | Count H2 entries; action reveals a compact section list with each direct count. Keep top-region notes distinguishable from named sections. |
| Recency | `last_note`, labeled “Latest dated note.” Null omits the date. It is not mtime, last edit, capture history, or the newest top-level note necessarily. |
| Children | Direct child notebooks, initially a count or at most three title links plus “N more”; no recursive subtree wall. Use the existing resolved child paths. |
| Findings | Existing per-notebook issues in the common foot, opening source/repair context. Do not paste owner-catalog warnings onto unrelated notebook cards. |

The old notebook header already provides much of the ancestry/children presentation. Refactor its model into the card adapter and disable that old mount *only in a scope the new card has successfully taken over*. On failure restore it; do not remove existing embed behavior as an incidental cleanup. Preserve the current “Notebook chips” preference: counts, recency, and child chips should respect it, while essential identity and ancestry remain. Update its description to cover cards.

An empty notebook should say `0 notes` only from a valid current report, and offer the existing capture route through an explicit action if that integration is reliable. It should not look broken or create sample content. Unknown data is never zero.

### Editing and navigation

Use the established keys in their existing supported modes:

- `-`: show/hide the complete Properties drawer.
- `_`: fold this card's details, independently of that drawer.
- `+`: open the full shared Property Editor.
- `==`: a species-focused entry into the same editor, initially focused on `summary` for a notebook and `title` for prose. If missing, use a preseeded Add flow; do not invent a second modal framework.

Clicks and ordinary keyboard activation must provide equivalent access outside Vim normal mode. Breadcrumbs navigate. Notebook title edits continue through the H1/aliases source convention; do not add a competing `title` field solely for the card. Parent clicks should not silently reparent. If a reparent action is included, route it through the existing validated Change parent workflow, not a new card-local writer.

A concrete implementation trap: `notebookFocusSummaryProperty` currently routes an owned scope through `setting: "summary"`, intended for area settings. Notebooks have no settings contract. It must select the loose property by key (or open Add with `summary` prefilled), otherwise takeover can strand the existing “add summary” affordance. The same distinction applies to `==`.

## Architecture and reliability

### Two adapters, one owner per pane

Keep both card adapters in bob-ledger-tools. Reuse `createPropertyCardHost`, identity/title utilities, `propertyCardFootAdapter`, drawer inventory, actual-ownership routing, and the central key registry. Add species entries, source-path attributes, and eligibility branches explicitly; the current frontmatter coordinator hardcodes supported kinds and mount attributes. Merely rendering `.bob-property-card` will not hide Properties safely.

For prose, the UI kind can be `prose` while `props.note_kind` remains `note`. Match the typed note through the shared prose/legacy predicate, not through the generic wire kind. Both spellings on one note count as one species. A mixed prose+notebook or prose+project type must not mount competing cards. Preserve path-canonical bank exclusion and existing registry precedence.

Native takeover requires all the existing evidence: supported desktop Live Preview/Reading scope, connected card and foot for this path, closed duplicate-free frontmatter, source/cache agreement, confirmed current-binary `props_v1`, and working editor routing. Since these cards initially use generic loose-property editing, **do not demand or manufacture area/project `props_contract_v1` settings**. Release ownership when identity, path, mode, capability, or mount evidence becomes invalid. Keep native File Properties sidebar behavior.

Separate validity of the card shell from freshness of body-derived numbers. An out-of-date section count should disappear or show a quiet updating state; it should not repeatedly unmount the title and flash native Properties while someone types.

### Read services and freshness

**Notebook:** subscribe to the existing shared notebook service. Do not start one `notebooks list` or `sync` per card. Current service invalidates on Markdown events and separately decides catalog sync from relevant metadata; preserve that separation. Rendering, resize, fold, drawer, and cursor movement never schedule writes or scans.

For reliable section navigation and exact source matching, recommend a small additive notebook report extension: optional per-entry `source_sha256` and optional per-section 1-based `line`. The scanner already knows section lines but drops them from JSON. Keep schema v1 growth-only and preserve old fields. Old hosts can still paint identity and summary; they should omit exact section jumps when evidence is unavailable. In dirty editors, hide disk-derived counts until a saved current snapshot matches, rather than maintaining a second notebook parser in JS.

**Prose:** the existing `articleOutlines` Map is private, path-keyed, and is not a ready-made cross-plugin contract. Add a small versioned read interface to the retained `bob-articles` plugin: synchronous snapshot lookup plus subscription/unsubscription, returning a source identity/generation, outline, findings, and freshness. Names such as `api.proseCards` are proposed, not existing APIs. The provider retains responsibility for lifecycle-triggered read-only plan requests, bounds/coalesces requests, rejects late responses, and handles both editor and Reading-only opens. Ledger painting only reads the latest snapshot.

Use the plan's input SHA where available. After applied formatting, source/output line mapping and the accepted buffer generation must refer to the *new* buffer; do not keep asserting that the pre-format SHA matches it. Multiple views of a path with different revisions must not receive each other's source targets. Unsubscribe on unload and drop/rename entries on the corresponding vault events. Obsidian's official event guidance explicitly recommends registered handlers so unload detaches them. [Plugin Events](https://docs.obsidian.md/Plugins/Events).

The numbering button delegates to `qj`'s existing one-transaction formatter action, preserving its preimage checks and undo guard. Opening or folding the card must never call that action. If the provider or new action is absent, keep a local identity/summary card where safe and omit unavailable controls; if property editing itself is unavailable, restore native Properties.

### Keep writes narrow

No frontmatter counts, metric timestamps, auto-summaries, or heading rewrites on paint. User-requested property changes use the shared property update service, which saves relevant panes and uses bob's fingerprinted transaction. Arbitrary keys and invalid values remain recoverable in the drawer/editor/source. Card text should render as text or through existing safe link rendering, never raw HTML from a title or summary.

This design does not require a new CLI command, a new props note kind, a vault migration, a third graph index, or a generic card framework rewrite.

## Parallel delivery with qi and qj

At the audited read, `qi.1`–`.3` were closed and `qi.4`–`.6` active. `qj.1`–`.5` were active. Treat that as a snapshot, not a permanent schedule.

| Existing work | Overlap and ownership | Proposed boundary |
| --- | --- | --- |
| `qi.3`, already closed | Removed Bank/Area arbitration; retained shared card kit | Base on landed single-owner code; never reintroduce arbitration for the new species |
| `qi.4` takeover acceptance | Shared coordinator, native entrypoints, key routing, screenshots | Keep fixes owned by qi; new-card integrator ports/extends tests after rebasing and reruns family acceptance on the combined revision |
| `qi.6` passive proof/docs/deploy | `240*` kit, manifests, generated bundles, docs, Property Card glossary | One integrator changes shared registration; preserve qi's family additions, append new species after rebasing; serialize final clean deploy |
| `qj.1`–`.2` engine rename and aliases | `articles/` → `prose/`, predicates, frozen wire names, generic props kind | Do not edit moving engine paths for card-only work; use legacy-compatible test fixtures and retain `note_kind: note` |
| `qj.3` prose plugin | `030-plugin.js`, `035-plugin-look.js`, manifest, tests, new toggle | Agree a small snapshot API; implement card consumer against fixtures now, land the provider hook after/on top of qj's plugin changes |
| `qj.4` host gate/cutover | Canonical argv and vault rename | Card work does not switch argv or retype notes; permanent legacy support makes the card independent of the migration |
| `qj.5` extract/inline planning | Future document moves | No dependency; cards respond to ordinary rename/modify events and never own body content |

**Recommended work split:** notebook adapter/report additions; prose adapter/read API; and one integration/acceptance owner. The first two can work in parallel in new source fragments and focused tests. The integrator owns shared species/coordinator/key registrations, fragment manifests, generated entrypoints, combined docs, and family visual review. This avoids two feature workers simultaneously rewriting the same shared file.

The useful dependency edges are small: prose provider integration follows the relevant `qj.3` changes; shared takeover integration follows whatever `qi` fixes touch that coordinator; final deploy follows the combined acceptance run. Notebook modeling, visual fixtures, data tests, and most prose rendering can begin immediately. There is no need for a blanket dependency on `qi`'s vault cleanup, `qj`'s host availability, or section-extraction planning.

Coordination should be a short contract and ownership agreement recorded by the implementation lead, not a new coordinator service. Recheck the current epic state before landing. Do not ask the active epic owners to absorb this feature into their scope. Do not send messages or launch agents as part of this independent research.

Build from fragment sources, never hand-edit generated `main.js`. After plugin changes, use the repo's build/test and `bob plugins sync` workflow, respecting its no-force overwrite rules. Multiple prototype branches must not race to replace the live plugin bundle. CLI additions ship through the existing release policy; optional JSON additions and plugin feature detection allow version skew without hiding access. Final UI acceptance must name both the CLI/binary and plugin revisions, not merely “master.”

## Acceptance that would make this reliable and beautiful

| Area | Required checks |
| --- | --- |
| Classification | Canonical prose, legacy article, both spellings, notebook, mixed types, ordinary prose-containing projects, type-note files, templates, conflicts, archived paths, and the path-canonical bank hub |
| Single ownership | One card, one title owner, one foot per supported pane; old notebook header suppressed only after success; split panes, close/reopen, plugin enable order, rename/retype, and unload restore correctly |
| Native access | `+`, `==`, `-`, `_`, Add file property, notebook add-summary, full unknown properties, YAML recovery; Source and sidebar remain usable; opener failure restores native access |
| Read correctness | Zero vs unavailable; direct vs descendant counts; null recency; nested stamps; fenced examples; duplicate H2s; title precedence; source vs formatted line offsets; out-of-order responses |
| Prose preservation | First numbered H1 remains visible; section-link navigation still works; toggle is one undoable plan; undo does not trigger formatting from a subsequent card refresh |
| Passive behavior | Hash protected fixture files before/after repeated paint/fold/resize/drawer/cursor actions; assert no writes and no new paint-triggered bob processes; normal service refreshes measured separately |
| Version skew | Old bob, missing prose API, missing toggle, unknown schema, missing optional notebook anchors, disabled plugins; no false metrics or inaccessible properties |
| Visual review | Real Obsidian, isolated fixture vault, light/dark × narrow/wide × Live Preview/Reading; long titles, two-line summaries, no summary, empty notebook, deep ancestry, many children, loading, invalid YAML, and source recovery |
| Accessibility | Keyboard-equivalent actions, visible focus, named buttons, no hidden focusable Properties controls, meaningful grayscale identity, no essential tooltip-only information |

Reuse the existing takeover e2e harness and capture representative images beside Album, Record, Area, Project, and Bank cards. Review visual evidence, not only DOM assertions. Check that the notebook card replaces rather than increases header clutter and that the prose lede remains visually dominant. Do not run automated UI acceptance against the live vault.

## Proposed glossary entries

These are drafts for the feature implementation, not statements that the cards already exist. Use `/sase_memory_write` when publishing. The user's explicit request covers the two new terms; a formal implementation plan should name those changes precisely. Rebase any Property Card family update on qi's pending additions rather than replacing its roster. `qj` owns Prose Note and its permanent legacy-name decision.

### Prose Card

> The note-top member of the [[property-card]] family for a [[prose-note]], including the permanent legacy `[[article]]` spelling. It gives authored writing a title, its available parent context, an optional summary, and source-checked section navigation and numbering state. It is a view over the note and Bob Prose's report, not another document or a stored outline. Body headings remain the author's sections.
>
> In supported desktop Live Preview and Reading views, its title and shared Properties foot replace the native presentation only while source, capability, mount, and editor evidence are valid; otherwise native access returns. `==` opens its focused property editor, `+` the full Property Editor, `-` the Properties drawer, and `_` the card's details. Numbering changes use Bob Prose's explicit formatter action. Painting never writes or formats the note. Not a card for every note containing prose, a publishing status, a completion score, or a [[reference-note]] card.

### Notebook Card

> The note-top member of the [[property-card]] family for a [[notebook]]. It brings the collection's title, scope summary, ancestry, direct note and section counts, latest dated note, and child-notebook navigation into one compact panel. It replaces the notebook's separate header where it mounts successfully. Counts come from Bob's notebook report: nested detail and descendant notebooks do not become direct notes, and the latest note date is an authored date rather than file modification time.
>
> The shared Properties foot keeps every frontmatter field reachable. `==` opens summary editing, `+` the full Property Editor, `-` the Properties drawer, and `_` the card's details. Native Properties returns whenever takeover is unsafe or unsupported. Painting writes nothing and creates no tasks. Not an [[album-card]], the generated `## Notebooks` catalog on an owner, a task home, or a review queue.

Keep command matrices, field inventories, and screenshot guidance in feature docs; the glossary should retain identity, distinctions, authority, and interaction semantics without duplicating the implementation manual.

## Recommended solution

Proceed with **two small card adapters on the existing kit**, using the notebook report service and a supported prose snapshot API. Lead with identity, summary, location, and navigation. Notebook counts and authored recency add useful context; prose section navigation and the existing numbering action do the same. Keep misleading word/stub-derived progress out of the initial card.

The new cards should preserve the existing note formats and generic property writer, conditionally take over native Properties, and restore it reliably. Fold the old notebook header into its card, leave prose body headings alone, and publish the two glossary definitions with the verified behavior. Start adapter work in parallel now; coordinate the small shared-code seams and land only after one combined real-Obsidian acceptance and clean deployment. That meets the request without turning either kind of writing into another task dashboard.
