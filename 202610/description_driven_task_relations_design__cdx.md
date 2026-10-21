# Description-driven task relations: a symmetric default without ambiguous writes

Independent research by **cdx**, 2026-10-21.

## Decision in brief

**Adopt undirected relations as the default when no description is present.** Keep described relations directed, provided the interface teaches that the description is a phrase read from a particular source to a particular target. This fits Bob's fast capture workflow and removes an arbitrary distinction from ordinary “these tasks belong together” links.

This changes the graph model, editing operations, and compatibility contract—not just two headings. Separate three things:

1. **Meaning:** an undescribed pair, or a described source-to-target edge.
2. **Storage provenance:** which task's authored Markdown contains the record.
3. **Presentation:** what the current task sees, regardless of where the record lives.

Recommend one authored record for a new undirected relation, symmetric lookup and editing, a single neutral **Links** group at either endpoint, and **Links to / Links from** only for described edges. Require a description to submit `~~`. Preserve current inertness, archive rules, and the authored-versus-generated distinction.

The principal adjustments to the request are explicit below: descriptions are a Bob convention rather than a universal test of direction; omitting a description during repeat capture must not erase one; the feature remains task-to-task; and raw Markdown needs a distinct generated-backlink marker even when the rendered group says Links.

## Evidence and scope

I independently inspected the current CLI contract and Rust implementation, the Obsidian plugins' index/render/edit paths, and the Mac client's presentation and capability checks. I did not consult another report or researcher in this swarm. I did not inspect the live vault, run a migration, alter product code, or change canonical memory. The glossary text below is proposed wording for implementation.

Inspected revisions:

| Repository | Revision |
| --- | --- |
| bob-cli | `bcc201feebc262f2b4f16569e959bd03cedecce4` |
| bob-plugins | `ee16031f6944628f3099571f5fbd51d01de95f6d` |
| bob-mac-capture | `bf30f9edead0cf47afa8923949a276dee29159bd` |

Recommendations are grounded in source inspection and existing conformance vectors, not a claim that a prototype has been tested. The number and shape of existing undescribed, reciprocal, aliased, or archived relations remain unknown until a read-only vault inventory.

## 1. What exists today

The [relation contract](https://github.com/bobs-org/bob-cli/blob/bcc201feebc262f2b4f16569e959bd03cedecce4/docs/task-relations.md) defines a directed, optionally labelled edge. Its identity is `(source, target)`; reverse edges are independent. The source's `🪢 **LINKS:**` line is authoritative. The target's `🪢 **LINKED FROM:**` line is generated. Reconcile never reads the latter as input. A source currently holds at most one entry per target; re-adding a target with a different label relabels that entry.

Details directly relevant to this proposal:

- `LINKS TO` is already an alias of authored `LINKS`; `BACKLINKS` is already an alias of generated `LINKED FROM`. Assigning either alias a new storage role requires changing every reader, not merely the writer.
- Labels are normalized: trim, collapse whitespace, strip one trailing colon. Writers require a valid 1–40 character result; readers accept longer valid labels. A wikilink alias becomes its relation label when no preceding label exists. Classify using the **parsed semantic label**, not a search for visible prose before `[[`.
- Reconcile preserves uncertain data and does not rewrite authored LINKS during routine projection repair. It reads archived sources without writing them. Relations survive completion, cancellation, reopening, and archiving.
- The live plugin index reads authored records and publishes forward and reverse maps. Chips do not use the stored mirror as truth. This is the right foundation for symmetric display.
- The Task Card's outgoing summary reads the current task's own LINKS line; its incoming summary uses the live index. A neutral Links summary must replace that asymmetry or miss links authored elsewhere.
- Source block IDs are currently minted for mirrors. Disabling `relations.linked_from_lines` suppresses those mints. Stable identity for undirected edges therefore needs an explicit decision.
- Capture stages writes against snapshots. The plugin commits source changes and then performs best-effort mirror follow-ups. Those follow-ups are not an atomic transaction for changes to two authoritative records.

These facts are visible in the [Rust model and planner](https://github.com/bobs-org/bob-cli/tree/bcc201feebc262f2b4f16569e959bd03cedecce4/src/native/task_relations), [reconcile pass](https://github.com/bobs-org/bob-cli/blob/bcc201feebc262f2b4f16569e959bd03cedecce4/src/native/task_status_hooks/relations.rs), [Task Card summaries](https://github.com/bobs-org/bob-plugins/blob/ee16031f6944628f3099571f5fbd51d01de95f6d/plugins/bob-navigation-hotkeys/src/312-task-card-relations.js), and [plugin writer](https://github.com/bobs-org/bob-plugins/blob/ee16031f6944628f3099571f5fbd51d01de95f6d/plugins/bob-navigation-hotkeys/src/594-plugin-relation-edit.js).

A heading-only change would leave duplicate views, source-dependent deletion, incorrect counts, incoming links missing from the neutral picker, and surprising direction changes during relabeling.

## 2. Critique: a good default, with a deliberate limitation

### Unqualified association should be symmetric

If I connect “Investigate retry failures” with “Review timeout policy” without explaining a direction, remembering which task I started from offers little value. The task I happen to be viewing should not decide whether the connection is outgoing or incoming.

Zotero provides a useful product precedent: its Related Items relation appears from both ends and does not infer relations between indirectly connected items. Bob should adopt those two properties: **symmetric, not transitively inferred**. This is a precedent for interaction, not a recommendation to copy Zotero's storage. [Zotero Related Items](https://www.zotero.org/support/related)

W3C SKOS also distinguishes a symmetric associative relation from directional relations. That supports separating association from orientation. Bob need not import SKOS's ontology or restrictions on combining relation types. [SKOS semantic relations, §8](https://www.w3.org/TR/skos-reference/#semantic-relations)

### Text presence does not logically prove direction

“Same topic as,” “related to,” and sometimes “duplicate of” can be symmetric descriptions. Conversely, an undescribed hyperlink still has a direction of reference. Ordinary backlinks expose where a link was authored; that does not decide the semantics of the association. [Obsidian Backlinks](https://obsidian.md/help/plugins/backlinks)

Teach the rule as:

> In Bob, leaving the relation description empty creates a shared link. Adding a description creates a statement: **source — description → target**.

Do not promise automatic understanding of the words. Do not infer symmetric exceptions for particular phrases or use an LLM to reverse arbitrary descriptions. An inverse-phrase table can remain a display convenience; it never changes the stored phrase or edge.

This restriction is reasonable for a small personal workflow because it eliminates a separate “directed?” setting. If Bryan later needs descriptions on symmetric links, that is the clear reason to reopen the decision and separate **kind** from **description** in storage. Avoid adding that mode before a real use case.

### Alternatives

| Approach | Benefit | Cost / recommendation |
| --- | --- | --- |
| Keep everything directed; hide arrows for blank labels | Small presentation change | Does not deliver symmetric identity, counts, or editing. Reject. |
| Explicit direction toggle independent of description | Most expressive; supports labelled symmetric links | Extra state and syntax; permits confusing empty directed edges. Reconsider when actual examples demand it. |
| Fixed relation types with inverses and symmetry rules | Strong machine semantics | Taxonomy/configuration burden for lightweight capture. Premature. |
| Two authoritative reciprocal entries for each shared link | Each note looks self-contained | Delete-versus-repair ambiguity, double counts, duplicate conversions, harder sync conflicts. Reject. |
| Central relation database/file | Clean globally unique records | New source of truth outside task Markdown; harder offline edits and recovery. Disproportionate. |
| **Description-derived meaning over one authored record** | Fast default, readable Markdown, reuse of index/reconciliation | Requires precise identity and mutation semantics. **Recommended.** |

## 3. Adjustments to the requirements

| Adjustment | Rationale |
| --- | --- |
| Keep this **task-to-task**, including project tasks such as `^prj`; do not add arbitrary note relations | Existing relations address task block IDs. The prompt's “note” wording should not silently expand scope. |
| Treat Description as a **source-oriented phrase**, not a free-form annotation | A sentence preview makes direction understandable; arbitrary explanatory prose cannot reliably do so. |
| `~~` without a description is incomplete while editing and refused on execution | It specifies orientation without the required statement. Teach adding a description or using `~`; never silently discard a tilde. |
| Omitted description on repeat capture does **not** erase existing text | Relabeling now changes semantics. Clearing must be explicit. |
| Keep storage provenance separate from direction | One authored side is compatible with symmetry; it must not determine orientation when a description is later added. |
| Use **Links** in rendered views, but retain a distinct generated marker in raw Markdown | Calling both authoritative and generated entries LINKS would make recovery consume its own output. Prefer raw BACKLINKS for the projection. |
| Give both endpoints stable IDs on new explicit undirected writes, even with mirrors disabled | The mirror preference controls generated text, not semantic identity. This narrows the old “disabled means no source mint” guarantee. |
| Treat this as a coordinated contract change | Existing relation support does not mean support for symmetric semantics. |

“Directed” and “undirected” belong in the glossary and detailed editor help. Everyday controls should mainly say Links, Description, and Direction.

## 4. Recommended semantic model

### Identity

Use resolved task identities, not titles, basename guesses, or raw link spelling. Today persisted task identity is vault-relative path plus block ID, with supported moves/renames repairing links.

```text
Undirected: U({A, B})
Directed:   D(A, B, description)

U key = (undirected, min(A, B), max(A, B))
D key = (directed, A, B)
```

Min/max only represents an unordered key. **It does not choose where Markdown must be stored.** Choosing storage ownership by sorted path would turn renames into transfers and might select an archived, unwritable task.

Description is not part of directed identity, so changing it remains relabeling. Reverse directed edges are independent. Self-relations remain refused. Neither kind implies transitive relations, a reverse authored assertion, blocking, completion, or any lane/freshness/schedule/Pomodoro change.

Use an in-memory discriminated type, such as `Undirected { endpoints, origins }` and `Directed { source, target, description, origin }`. Derive kind once from normalized parsed text. Do not persist a second boolean that can disagree with the description.

### Physical records and duplicate origins

Author a new U once, normally on the writable task where the gesture began, and index it symmetrically. Retain an internal origin locator for the authored task/entry so the logical link can be edited from either endpoint.

Legacy or simultaneous edits may contain blank A→B and blank B→A records. Represent them as **one U with two origins**. Show one chip, count one relation, and retain both locators. Managed removal must remove every authoritative origin or the link will reappear.

Do not delete duplicate authored records during ordinary reconcile. That pass repairs generated data; keeping it non-destructive is valuable. Physical consolidation belongs in a previewed migration or an explicit edit touching the pair.

Preserve described reverse edges and mixed legacy states. A pair can contain U and one or both directed edges; never discard a description because a blank record exists elsewhere. These are distinct semantic records even if rarely useful together. Authored deduplication must therefore distinguish `(target, kind)` instead of collapsing every entry to the same target. Retain at most one described edge per ordered pair; this is not a general multi-predicate graph.

That is a real amendment to today's “one entry per target” contract. It needs shared parser/planner vectors and must not be activated with old writers still running.

### Missing identity

New explicit undirected writes mint missing endpoint IDs in the same transaction. Completion, preview, index reads, and Escape never mint.

Legacy sources can lack IDs when mirrors have been disabled. An index may use a provisional path/line locator for display, but not as a durable key. Before mutation, re-resolve against a current snapshot and mint if writable. Duplicate IDs or an unidentifiable archived source make the edit unavailable; do not guess. Inventory these cases separately.

## 5. Storage: one source of truth

Keep the authored LINKS grammar, including descriptions before links. Prefer the already-recognized neutral spelling BACKLINKS as the generated line's canonical form, while continuing to read LINKED FROM.

```markdown
- [ ] #task Investigate retry failures ^retry
  - 🪢 **LINKS:** [[policy#^timeout]] • follow-up of [[done/bugs#^old-retry]]

- [ ] #task Review timeout policy ^timeout
  - 🪢 **BACKLINKS:** [[bugs#^retry]]
```

The blank entry means U(retry, timeout); the described entry means D(retry, old-retry). BACKLINKS is generated evidence of an authored record, not a second U assertion. Described backlinks retain the existing `(description)` form.

This deliberately does **not** give raw Markdown the same three headings as the rendered view. Raw text must distinguish authority from projection. BACKLINKS explains provenance without imposing semantic direction. Reader tolerance already exists; formatter expectations, tests, docs, prefilters, and notices still need updating.

Do not redefine LINKS TO as a directed-only authored line: it already aliases LINKS. Do not introduce three attractive raw headings if doing so loses ownership information. Entry-level ownership markers could solve that, but add machinery and uglier Markdown for a cosmetic goal.

The mirror setting still controls materialization. Disabling it removes only generated text, not relations. Both endpoints must still show U in the live UI. Deleting generated lines and reconciling restores the projection without creating authored edges.

Keep archive policy: a new relation to an archived task is authored in the active task. Normal projection/conversion writes never touch `done/` or the previous daily note. A U whose sole authored origin has since been archived is visible but cannot be removed or described through a normal gesture that would write the archive. Explain that limitation rather than creating another record to conceal it. Semantic symmetry does not override permissions.

## 6. Capture and editing

### Syntax for a new pair

A is the captured/selected owner; `work:b` resolves to B.

| Fragment | Meaning | Preview |
| --- | --- | --- |
| `~work:b` | U({A,B}) | `A — B` under Links |
| `~work:b\|"follow-up of"` | D(A,B,follow-up of) | `A — follow-up of → B` |
| `~~work:b\|"follow-up of"` | D(B,A,follow-up of) | `B — follow-up of → A` |
| `~~work:b` | Target selected; description required | `Add a description for this direction, or use ~ for a shared link.` |
| `~work:b\|` or unfinished quote | Description being entered; incomplete | No committed change |
| Explicit whitespace-only or colon-only quoted description | Empty after normalization; invalid | Explain how to omit Description entirely |

Retain `~~` as an expert shortcut for an incoming described relation. After selecting a task, offer Description automatically. No-description submission fails before any task creation, ID mint, or write. Do not reject early enough to prevent target completion.

Use the same Rust validation for typed capture, completion, dry-run, and execution. Swift renders Bob's needs and semantic output; it does not implement separate grammar. Preserve tests for strikethrough, escaped tildes, quoted note paths, code spans, and Pomodoro `x~` / `=~`. [Current capture grammar](https://github.com/bobs-org/bob-cli/blob/bcc201feebc262f2b4f16569e959bd03cedecce4/docs/capture.md#linking-tasks)

### Repeat capture and explicit editing

These rules must be intentional, not accidental consequences of optional-label upsert:

| Existing state | Action | Result |
| --- | --- | --- |
| No relation | Bare `~B` | Add U |
| U, authored at either end | Bare `~B` | No-op; do not add reciprocal record |
| Only described edge(s) | Bare `~B` | No-op: `Already linked; description kept`; neither clear text nor add redundant U |
| U and no D in requested orientation | Described `~` or `~~` | Convert U into D in that orientation; preserve opposite D |
| D in requested orientation | Described capture | Relabel that D; identical normalized text is a no-op; preserve separate U/opposite D |
| Only D in opposite orientation | Described capture | Add independent D in requested orientation |
| Selected U in editor | Add description | Convert U using visible sentence orientation |
| Selected D in editor | Clear description | Convert selected D to U; preserve opposite D; merge with existing U |
| Selected U | Remove | Remove all blank authored origins; leave described edges |
| Selected D | Remove | Remove that directed edge only |

If a U conversion collides with a separate D in the selected orientation, do not overwrite D implicitly. Keep the proposed edit open, show the existing description, and offer explicit replacement/merge or cancellation. Contradictory descriptions for the same directed key in bulk capture fail the whole batch, following today's conflicting-label guard.

The asymmetry is deliberate: **supplying a description adds meaning; omission does not revoke meaning**. “Make undirected” is an explicit operation, available by clearing the selected relation's Description field. Preview: `Remove “follow-up of”; keep a shared link between A and B.` Save is enough for an ordinary reversible change; a second confirmation dialog is unnecessary.

Describing U from its other endpoint uses the visible sentence order, not its historical owner. The change may transfer the authoritative record. That is a semantic write, not a mirror follow-up.

## 7. Interaction and visual design

### One calm relation area

Reuse the neutral knot icon, task chips, status checkbox, note locator, and hover preview. Render only nonempty semantic groups:

```text
Investigate retry failures

  🪢 Links        [Review timeout policy  ↗ policy]

     Links to     follow-up of → [Original retry bug  ↗ bugs]

     Links from   [Reliability review  ↗ project] — includes → this task
```

At Review timeout policy, the same blank connection appears under Links pointing back to Investigate retry failures. No arrows, ownership badges, “from,” or duplicate chips appear for U. Prefer a plain connector in previews over ↔, which can suggest two directed edges.

For incoming D, use existing known inverse phrases where clear; otherwise show `Other task — phrase → this task`. Never mechanically append “by” or invent an inverse. Tooltips and accessible labels expose the full source–phrase–target sentence.

Text and geometry communicate direction; color continues to mean task status. This preserves Bob's current visual vocabulary and avoids color-only encoding. [W3C use-of-color guidance](https://www.w3.org/WAI/WCAG22/Understanding/use-of-color.html)

### Task Card and keyboard

- Primary `l` becomes **Links…**, opening one editor over incident relations, defaulting to the neutral link action.
- `⇧L` opens the incoming described flow, with direction preselected and Description required.
- Choose a task first. Blank Description creates a shared link. Valid text reveals the directed sentence and Swap direction action. Update the preview in place rather than jumping between layouts.
- Help text: `Leave blank for a shared link. Add a phrase to give it a direction.` Use source-oriented examples such as “follow-up of.”
- Escape before Save changes nothing. Clearing a field changes only draft preview until commit.
- Removal appears on focus as well as hover. Accessible labels distinguish `Remove link between A and B` from `Remove A — phrase → B`.
- Do not transfer outgoing-only Ctrl+D to the merged Links group. It would become a cross-note bulk delete. Prefer per-relation removal; any bulk action lists its affected relations and uses the same transaction planner.

### Aggregate per task, not per physical line

Build one per-task model from a single index generation:

```text
undirected neighbors
outgoing described edges
incoming described edges
```

Deduplicate U by unordered key and sort neighbors independently of storage ownership. Preserve authored order for outgoing D and canonical incoming order where practical. Counts and rows come from the same semantic snapshot.

Mount at a stable managed-child location and avoid rendering duplicates for LINKS plus BACKLINKS. Incoming-only tasks need a live anchor even if mirrors are disabled or the target is archived. Source mode still exposes Markdown. Distinguish broken targets, loading indexes, and read-only records; a loading index must not appear to contain zero links.

Beauty here comes from fewer arbitrary distinctions and consistent spacing, not a new palette or decorative graph. Review single-link rows, mixed directions, long descriptions, narrow windows, closed tasks, keyboard focus, and missing targets before finalizing the layout.

## 8. Reliability: where most work belongs

### Semantic planning above line formatting

The current line planner remains useful, but symmetric mutations need a higher-level planner:

1. Resolve identities against current text and gather every authoritative origin.
2. Derive the semantic change and check description/orientation collisions.
3. Check all authoritative files for writability and malformed relation lines.
4. Stage authoritative removals/additions/conversions and ID mints.
5. Validate preimages/read dependencies, commit the authoritative batch, and report the actual outcome.
6. Update generated mirrors as repairable projections, distinguishing their failures from authoritative failures.

Existing plugin mirror follow-ups are insufficient for ownership transfer, reciprocal-origin deletion, or conversion merges. The inspected writer loops over source writes and can return after a later failure. The new feature needs verified multi-file commit/rollback behavior, including unsaved editor buffers. Reuse existing transaction machinery where suitable; this report does not claim that a sufficient cross-editor transaction already exists.

A stale snapshot should refuse/replan while preserving the draft. Never report successful deletion if a read-only or changed origin survived. If a failure also prevents restoring preimages, report partial state honestly.

### Reconcile and concurrency

Use the same classification in reconcile and the live index. Never promote generated backlinks to origins. For malformed or duplicate-ID sources, retain conservative warning/preservation behavior; do not prune or guess identities.

Two devices may independently add the same U before syncing. Origin tracking produces one logical read result after merge. It does not provide distributed delete semantics: a later-arriving origin can restore a locally deleted U. Do not claim CRDT behavior or automatic lossless Git conflict resolution. Use the existing vault conflict workflow; promise convergence over a fixed resolved input. Tombstones or a replicated relation database would be a much larger feature.

Reverse lookup must be complete before deciding U is absent. Build/reuse a reverse index from the read set; avoid scanning the entire vault per picker row or bulk-capture item. Measure on a representative vault rather than promising unmeasured latency.

### Invariants

- Blank records produce the same U from both ends.
- Descriptions never reverse meaning because the viewer or owner changed.
- Generated lines alone never sustain a removed relation.
- Reciprocal blank origins produce one count.
- Removing U preserves D to the same task, and vice versa.
- Relation operations preserve statuses, lanes, task fields, dependencies, review position, and Pomodoro sections, except necessary block IDs.
- Dry-run and live execution plan the same action; preview/completion/cancel write nothing.
- Repeated unchanged capture/reconcile avoids writes and undo entries.

## 9. Compatibility and migration

### Explicit protocol meaning

Expose a discriminator such as `kind: "undirected" | "directed"` and view-relative orientation `none | outgoing | incoming`. Do not overload current `direction: "to" | "from"`: capture sigil orientation describes syntax, not necessarily semantic direction.

For U expose endpoints without pretending the physical owner is a semantic source. Mutation results should report before/after kind and conversions explicitly; old `relabeled` wording must not conceal a semantic change. Finalize exact fields with Rust/Swift fixtures.

The contract currently advertises `relation_grammar: 1`. Bump that capability, but **a bump alone does not protect older Mac clients**. The inspected [CapturePanelModel](https://github.com/bobs-org/bob-mac-capture/blob/bf30f9edead0cf47afa8923949a276dee29159bd/Sources/BobMacCapture/CapturePanelModel.swift) checks whether the field is absent, not whether its value is understood. [Presentation code](https://github.com/bobs-org/bob-mac-capture/blob/bf30f9edead0cf47afa8923949a276dee29159bd/Sources/CaptureCore/CaptureRelationshipPresentation.swift) still renders links to/from using the old direction field.

Default recommendation: a coordinated **capture schema v2 boundary for the affected capture command family**, with Mac dual-schema support prepared before Bob switches. Existing schema rejection then prevents old clients silently presenting new semantics as old direction. Negotiated request contracts could avoid the broader schema break, but must be implemented and tested first. Merely adding optional fields does not solve semantic incompatibility. Keep changes additive wherever possible within the explicit boundary.

Publish v2 index/navigation APIs for semantic neighbors and logical-identity mutation. New controls require both compatible index and writer versions. Rendering Links while calling v1 `removeLink(source,target)` cannot correctly remove a U with multiple origins.

The audited thin-client decision remains binding: Rust owns capture meaning; Swift presents it. Follow the audited daily release-train decision: mark CLI/JSON breaks with `!`, use the train, and do not manually edit versions or CHANGELOG.

### Rollout

1. **Read-only inventory.** Count blank, described, reciprocal-blank, mixed-kind, aliased-label, malformed, id-less, unresolved, and archived-origin cases. Preview normalization; do not infer real counts from this report.
2. **Prepare consumers.** Dual-version Mac decoding, v2 plugin APIs, shared vectors, and unsupported-version handling. Exercise old/new combinations.
3. **Coordinate every writer.** Upgrade hooks, plugins, and capture together. Old writers can relabel or deduplicate by target alone. New fields cannot force installed old code to cooperate; suspend incompatible writers during activation.
4. **Activate semantic reads.** Existing blank authored records become U; physical orientation remains provenance. Preserve every described orientation. No wholesale authored rewrite is required.
5. **Repair projections.** Preview then regenerate BACKLINKS and permitted stable IDs. Preserve/report archived or malformed cases. Audit alias-derived descriptions against real parser behavior.
6. **Optionally consolidate later.** Collapse reciprocal blank origins only when all authoritative records are writable and the preview lists each change. The feature works without physical cleanup.

Keep a recoverable snapshot of affected notes. Binary rollback after v2 writers create mixed-kind entries is unsafe: v1 deduplication can discard information. Retain v2 readers during rollback or restore a pre-activation snapshot with explicit treatment of subsequent user edits. Reinstalling an old executable alone is not a safe rollback story.

## 10. Implementation surface and verification

| Surface | Work |
| --- | --- |
| `bob-cli/src/native/task_relations/` | Kind/key helpers, kind-aware duplicates, conversion planning, neutral generated formatter, shared vectors |
| `capture_language/relations.rs`, parse/complete | Description-required reverse capture, semantic fields, partial states, symmetric already-linked lookup |
| `capture/relations.rs`, `relations_mirror.rs` | Pair-aware writes, transfers, IDs, semantic reports |
| `task_status_hooks/relations.rs` | Shared classification/projection rules; preserve uncertainty and authoritative data |
| Plugin grammar/index/Task Card/widgets/nav | Symmetric neighbors, one task-level view, merged counts, origin-aware mutations, v2 gates |
| task-status-cycler and block-id-prompt | Recognize every managed relation form as inert metadata |
| Mac CaptureCore and panel/model | Schema decoding, neutral copy, required descriptions, sentence previews, conversions, version checks |
| Docs and glossary | New definitions, gestures, provenance, transition rules, compatibility |

Update the shared contract and vectors with code. Do not port capture grammar to Swift. Rebuild plugin source fragments instead of editing generated main.js. Follow linked repository checks, including compiling changed Swift on an appropriate platform: Linux-only validation cannot verify the Mac UI.

Acceptance cases:

| Case | Required observation |
| --- | --- |
| Add blank A–B from A, repeat from B | One U; second operation no-op |
| Blank records already at both ends | One count; removal deletes both origins or refuses before writing |
| Describe U from non-owning endpoint, both orientations | Correct sentence; no leftover blank origin or accidental reversal |
| Clear D while opposite D or U exists | Only selected meaning changes; other description survives |
| Bare repeat capture against D | Existing description/orientation preserved |
| `~~` without label; empty normalized description | Incomplete/invalid as specified; zero writes/mints |
| Invalid item inside bulk capture | Entire batch refuses; no partial creation |
| Incoming-only U, mirrors disabled, archived target | Symmetric live row; no archive write |
| Archived authoritative origin | Display works; mutation unavailable with concrete reason |
| Aliases, tolerant headers, Unicode, alternate link spellings | Rust/JS classification and identity agree |
| Malformed line, unresolved target, duplicate IDs | Preserve evidence; no speculative identity or pruning |
| Concurrent edit / later-file write failure | No false success or unnoticed surviving origin |
| Move, rename, archive, close/cancel/reopen | Supported repairs preserve identity; relations stay inert |
| Delete generated lines; reconcile twice | Restore projection, then no-op; authored records unchanged |
| Old/new CLI, Mac, plugin combinations | Unsupported semantics gated explicitly |
| Narrow/dark/light/focus/high-count UI | Stable readable layout; accessible removal; no duplicate rows |

Do not import dependency cycle checks: relation cycles are legal. Add an endpoint-swap invariance property test for U and authoritative multi-file failure tests. These verify behavior that formatter or screenshot tests cannot.

## 11. Proposed glossary wording

These are proposed definitions, not memory edits made by this research. Use the SASE memory-writing workflow during implementation. The user explicitly requested the Task Relation update and directed/undirected terms.

**Task Relation** — An inert connection between two tasks. A relation without a description is an **Undirected Task Relation**; a relation with a description is a **Directed Task Relation**. Add or edit relations through Capture `~` / `~~` or the Task Card's Links controls. Authored records live on a task's LINKS line; BACKLINKS (formerly LINKED FROM) is a generated projection, never another authored relation. Relations never block tasks, count as Pomodoro Task Links, or change status, schedule, priority, freshness, or the review walk. They survive task completion and archiving.

**Undirected Task Relation** — A Task Relation without a description, connecting an unordered pair of distinct tasks. Either task shows the other under Links; creating the same link from the other end does not create another relation. One authored record normally stores it; its location is provenance, not direction. Managed edits act on that record from either endpoint, subject to write permissions. Undirected relations do not imply links between indirectly connected tasks.

**Directed Task Relation** — A Task Relation with a nonempty description, read as “source — description → target.” Capture `~target|description` uses the current task as source; `~~source|description` uses the selected other task as source. The source shows Links to and the target shows Links from. A reverse directed relation is independent. Generated backlinks and inverse display phrases do not create that reverse relation. Clearing Description through an explicit edit converts the selected relation to an undirected one.

Suggested aliases: **Directed Relation**, **Undirected Relation**, and **Relation Description** for the existing label concept. Retain wire/storage naming `label` where compatibility requires it; explain that UI Description and contract label mean the same field. Update Task Link's list of relation-line names so it continues to distinguish relations from Pomodoro Task Links. Avoid adding generic graph-theory guidance to core memory.

## 12. Confidence and remaining evidence

**High confidence:** the symmetric default is useful; headings alone are insufficient; one authored record plus derived views is safer than authoritative reciprocal mirrors; `~~` should require Description; sentence previews matter; old-client compatibility requires explicit handling.

**Moderate confidence:** retaining compact LINKS grammar and using BACKLINKS for raw provenance is the best first implementation. It minimizes storage disruption while delivering the requested UI. If Bryan wants semantic headings in raw Markdown too, design a separate ownership-preserving format rather than conflating generated and authored LINKS.

**Needs implementation evidence:** a multi-file transaction that handles unsaved editors; real vault counts and id-less/archive cases; pair-aware lookup performance; exact schema migration scope. This report does not establish those outcomes by measurement.

## Recommended solution

Ship **undescribed = undirected; described = directed** as an explicit Bob convention. Present one neutral **Links** group from either endpoint, with **Links to / Links from** for described relations. Show the complete source–description–target sentence and require Description for `~~`.

Keep **one authored record** as the normal storage form, a distinct generated **BACKLINKS** projection, and an index separating unordered meaning from ownership. Make deletion/conversion act on logical relations and all authoritative origins; never erase descriptions by omission or report partial authoritative edits as success. Preserve task-only scope, archive permissions, and inertness.

Implement the semantic planner and shared conformance vectors, then coordinate CLI, plugin, Mac, and glossary updates behind an enforced compatibility boundary. The simple user experience is worth building, but it depends on precise identity and editing rules.
