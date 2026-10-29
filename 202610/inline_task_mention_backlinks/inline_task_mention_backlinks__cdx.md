# Inline task backlinks: make the reason visible, keep the source authoritative

Independent research and design recommendation by **cdx**, 2026-10-29.

## Recommendation in brief

**Build this feature. Treat an inline task reference as evidence for an incoming backlink, not as an automatically authored relation.** Reuse the target's existing `🪢 LINKED FROM` row. Give each inferred entry a persistent **in task text** badge, an exact source excerpt, and navigation to that occurrence. Do not create a `LINKS` row on the source, infer a semantic label, or give an inline-only entry the existing unlink control.

Use the live index for immediate display and Bob's existing reconciliation machinery for a readable, generated Markdown projection. Keep provenance separate from relation labels in both the data model and the generated grammar. Start with links in the source task's description line; expand to task-body prose only after measuring the usefulness and noise of that smaller scope.

This is a recommendation, not an implemented feature. I independently inspected bob-cli and bob-plugins, consulted primary Obsidian and accessibility documentation, and exercised the current plugin parser and existing tests. I did not inspect another swarm researcher's report, chat, or conclusions. I did not inspect Bryan's live vault or run a live-vault benchmark. Confidence is high in the architectural fit and identified integration points; the visual treatment and scope still need evaluation in the actual Obsidian UI.

## 1. Is this a good idea?

Yes: the source already records a useful fact, but the target currently loses the context of who is referring to it. Making that context visible at the task itself reduces navigation and duplicate relation entry. For example, while reviewing **Design the retry policy**, seeing that **Update the deployment checklist** references it can explain why the design matters without requiring a second manually maintained edge.

The risk is overstating that fact. A link can mean “compare with,” “use as an example,” “this supersedes,” or simply “see.” None of those meanings can safely be inferred from the presence of a link. A backlink should therefore say **this task is mentioned here**, not “this blocks,” “this follows up,” or “this is related in a specific way.” The excerpt supplies the meaning the author actually wrote.

There are four product traps:

1. **Unexpected mutations.** Typing prose should not visibly rearrange the source task or add a redundant outgoing row. Automatic ID creation, if needed for a durable backlink, must be narrowly bounded and documented.
2. **Unclear removal.** A generated entry that reappears after deletion feels broken. Its controls should lead to the source text, and its explanation should say why editing the target row does not remove the reference.
3. **Noise.** Scanning every child bullet, work log, dependency row, and daily ledger would mix several existing concepts and can create reciprocal backlink loops.
4. **False semantic equivalence.** A manually authored relation and a textual reference can connect the same tasks, but have different ownership, editing, and label behavior.

The feature earns its space if it answers two questions at a glance: **Which task mentions this one? Why am I seeing it?** A short source chip plus a visible origin badge answers the first layer; an exact excerpt answers the second.

Obsidian's core Backlinks feature provides note-level linked mentions, expandable context, and an optional in-document display. Bob's opportunity is to place a filtered, task-specific version next to the exact task, not duplicate the entire note backlinks panel. [Obsidian Backlinks][W2]

## 2. What the current implementation already provides

I inspected these repository snapshots:

- bob-cli: `48253b7f225620f2cde10c856f458c31cd6f58d3`.
- bob-plugins: `68db3fbefa30e13767f58fcf18c9c0b3fccd4b53`.

The following are observed behavior or contract requirements, not proposed additions.

| Existing mechanism | Consequence for this feature |
| --- | --- |
| An authored `LINKS` child is the authority; `LINKED FROM` is generated and never read back as an edge source. | Add another authoritative input class, the source description, rather than converting mentions to `LINKS`. |
| Identity is resolved note path plus block ID; self-relations are refused. | Deduplicate by task identity, never alias text, task title, or block ID alone. |
| Reconcile maintains mirrors on writable targets, including closed targets. Archives and the previous daily note are read-only in this pass. | Preserve those write boundaries. A complete UI still needs a live-only fallback for read-only targets. |
| Missing source IDs can already be minted for mirrors, with quiet-file and write checks. | Reuse that guarded mechanism, not a new writer on every keystroke. |
| Relations are inert except for explicit commits of configured cancel/complete labels. | Inline discovery must never enter those commit-time effect paths. |
| Chips use live data, include source status, support navigation, and distinguish stale stored entries. | Reuse the existing visual family and readiness behavior. |
| Incoming chips currently expose a remove action that calls `removeLink(S,T)` against the source's `LINKS` line. | Inline evidence must have different actions, and mixed evidence must identify which part an action removes. |

These points are documented in the [relation contract][C1], implemented by the [Rust reconcile pass][C2], and reflected in the [plugin chip model][P3] and [remove-action wiring][P6].

There are also concrete integration gaps:

- **Rust discovery is `LINKS`-gated.** Both archive retention for relation sources and `collect_file_edges` use `contents.contains("LINKS")`. A source containing only a task-description block link is currently missed. [Rust relation pass][C2]
- **The JavaScript parser collects only accepted `LINKS` children.** The current startup lifecycle prefilters on metadata block links and calls that parser. The contract also describes an additional managed-row text prefilter, but that is not present in the inspected lifecycle path. Implementation should audit both code paths instead of assuming that changing one prefilter is sufficient. [Parser][P1], [lifecycle][P2], [contract §11][C1]
- **Rendering requires a row to decorate today.** Live Preview searches managed row text; Reading view looks for an existing matching list item. Merely putting an inline edge into the index will not show a first backlink on a task that has no stored `LINKED FROM` row yet. [Editor integration][P6], [Reading view integration][P5]
- **Current records do not carry origin or occurrence context.** `RelationEntry` contains target, block ID, label, and syntax decorations. The new representation needs explicit provenance and location evidence. [Rust model][C3], [JavaScript parser][P1]

### Checks performed

I ran the existing plugin tests for the relation index, relation chips, and Linked-from stage together. The command exited successfully:

```text
node --test --test-reporter=dot \
  scripts/test-ledger-tools-relation-index.cjs \
  scripts/test-ledger-tools-relation-chips.cjs \
  scripts/test-relation-index-linked-from-stage.cjs
```

A separate, in-memory probe through the repository's exported parser helpers produced:

| Input | Current outgoing edge count |
| --- | ---: |
| `- [ ] #task Review [[design#^target|the design]] ^source` | 0 |
| A task with `🪢 **LINKS:** [[design#^target]]` | 1 |
| A task with ordinary child prose `See [[design#^target]]` | 0 |
| A task with a generated `LINKED FROM` child | 0 |

A second probe confirmed that `(in task text)` is currently interpreted as an ordinary relation **label**, while `[in task text]` is rejected as malformed trailing material. This matters for the provenance and compatibility design below. These probes validate the current extension points; they do not validate a future implementation, actual Obsidian rendering, or performance.

## 3. The experience I would design

### The ordinary case

Source text, authored by Bryan:

```markdown
- [ ] #task Update the checklist after [[design#^retry-policy|the retry policy]] is settled ^update-checklist
```

Target after reconciliation:

```markdown
- [ ] #task Design the retry policy ^retry-policy
  - 🪢 **LINKED FROM:** [[release#^update-checklist]] [in task text]
```

The square-bracket suffix above is **proposed new mirror grammar**, not syntax the current release accepts.

Rendered concept, using the existing task chip family:

```text
☐ Design the retry policy
  🪢 LINKED FROM   [☐ Update the checklist…  ↗ release]  [in task text]
```

The source title is the primary object. The origin is a smaller, neutral text badge, always visible, visually distinct from the current small-caps semantic label treatment. Keep task status colors on the existing mini checkbox/chip. Do not introduce an “automatic link” color or use a dashed border for this normal state: dashed already communicates stale or broken data.

Activating **in task text** opens a small explanation anchored to that entry:

```text
Mentioned in task text

Update the checklist after [the retry policy] is settled
                            └ exact link highlighted

This task links here from its description.
Edit that link in the source task to change this entry.

Open mention ↗
```

The visual excerpt must be the actual source text, centered around the occurrence, with the linked phrase highlighted. It is not an AI-generated explanation and not a guessed relation label. Preserve the alias as the highlighted phrase; the source chip still names the actual source task.

Default behavior:

- Clicking the task chip follows normal task navigation and modifier-click conventions.
- Clicking or pressing Enter/Space on the origin badge opens the explanation; the explicit **Open mention** action goes to the occurrence, not merely the start of the file.
- Hover/focus can preview the same context, but clicking must provide a stable equivalent on touch devices and for keyboard users.
- Multiple occurrences in one description produce one source chip and `in task text · 2`; the explanation lists both occurrences.
- A source without a durable ID can still appear live using a checked location within its current file snapshot. It is not serialized as a block backlink until an ID exists.
- No transient notices appear for ordinary discovery or removal.

This makes the explanation available without turning every backlink into a permanent paragraph. When the panel contains an action, implement it as an accessible popover/disclosure rather than an interactive tooltip masquerading as plain tooltip text. Escape dismisses it and focus returns to the trigger. For hover/focus behavior, W3C calls for dismissible, hoverable, persistent content. [W3C hover/focus guidance][W3]

### Mixed authored and inline evidence

Suppose the same source also has an explicit `follow-up of` relation to this target. Show one source entry, retaining its existing inverse phrase, plus a badge **also in task text**:

```text
🪢 LINKED FROM
  followed up by [☐ Update the checklist… ↗ release] [also in task text]
```

The context panel shows two reasons: the explicit relation and the source-description occurrence. A labelled relation is still editable, but “Remove relation” removes only the `LINKS` evidence. The inline badge and backlink remain while the source text still links here. Report that outcome plainly: **Relation removed; the reference in task text remains.**

Do not suppress a deliberately authored `LINKS` entry merely because the same pair also has a textual reference. The user's requirement should prohibit **automatically adding** that redundant outgoing bullet; it should not erase previously authored meaning.

### Controls, counts, and visual density

| Entry kind | Main action | Editing affordance |
| --- | --- | --- |
| Explicit relation only | Open source task | Existing remove/relabel controls |
| Inline reference only | Open source task / exact mention | Open source text; no × and no relabel |
| Both | Open source task / inspect both reasons | Explicit “Remove relation” and “Open mention”; avoid an ambiguous × |
| Unverified stored entry | Open last-known source if it still resolves | Navigation only; say verification is pending |

The Linked-from Task Card should count **unique source tasks**, not evidence records. Keep its current explicit-edit interaction for authored relations, and visibly distinguish an inline-only CURRENT row: Enter opens its occurrence; it cannot silently toggle a relation. The footer/action hints must follow the selected row. A later command can deliberately add an explicit labelled relation, but “convert” must not imply deleting source prose.

Reuse existing closed-source collapsing, dimming, and `#hide` treatment. If the row has many open sources, show the first three in stable order and a text button **+N more**; the expanded list can live in the existing Linked-from surface. This is a proposed density cap, not a change to stored membership or counts. Test the cap against real examples before hardening it. Never hide provenance merely to fit a chip, and never make “in task text” a hover-only icon.

Use the existing `--text-muted`, font scale, spacing, and focus styling, with wrapping between entries and a full title in the expanded context. Muted text still needs readable contrast in light and dark themes. Text communicates the origin; color is supplementary and remains dedicated to task status. [Existing relation CSS][P7], [W3C use-of-color guidance][W4]

## 4. Explicit adjustments to the requested requirements

These are design choices I recommend, not assumptions about an already agreed contract.

| Requested or implied scope | Recommended adjustment | Reason |
| --- | --- | --- |
| Auto-add “linked from” bullets | Maintain one generated `LINKED FROM` child containing all unique incoming sources; display it live before persistence when necessary. | Fits the existing model and avoids one child bullet per source. |
| Links anywhere inside another task | **V1: the task's own description line only**, including visually wrapped text on that line. Nested task descriptions qualify independently. Ordinary child bullets, physical continuation lines, logs, and all managed children do not. | Clear ownership, bounded work, and no accidental history/ledger/dependency inference. This is a deliberate scope reduction. |
| Obsidian links | V1 guarantees the requested wikilinks: same-note, note-relative resolution, explicit paths, optional `.md`, and display aliases. Ordinary Markdown-link syntax is a separately tested follow-up. | The shared Bob scanner currently handles wikilinks. Do not advertise all Obsidian link syntax prematurely. |
| Every backlink has a persisted row immediately | Live display is immediate after a settled parse; disk projection follows safe reconciliation. Archives stay read-only. | A live editing session must not cause speculative cross-file writes. |
| The source is untouched | No extra outgoing row. A missing source block ID may be appended only by a successful, guarded persistence pass when a durable mirror needs it. | Otherwise a stable reverse block link cannot be written. This is the one source-side bookkeeping mutation. |
| Remove the backlink from its target | Inline-only entries lead to source editing; they cannot erase prose from the target surface. | Removal belongs where the fact is authored. |
| Infer “relation” semantics | Infer only **mentions this task**. No label, dependency, status, lane, freshness, schedule, or closing effect. | Presence of a reference does not determine intent. |

If links in handwritten task-body notes are common, the next expansion should include those with an explicit **nearest task owner** rule and managed-subtree exclusions. It should not be an unbounded descendant scan. Do not include a nested task's prose in its parent's outgoing evidence.

Obsidian documents wikilinks and Markdown links as distinct supported formats; block links use `#^id`, and a pipe changes display text. That supports separating resolution identity from alias presentation. The narrower initial support above is a Bob delivery choice, not a limitation claimed about Obsidian. [Internal links][W1]

## 5. A data model that preserves the distinction

Let `E(S,T)` be an authored LINKS relation, with an optional label. Let `I(S,T)` be the nonempty set of eligible inline occurrences in S that resolve to task T.

```text
incoming(T) = unique source tasks S for which E(S,T) exists or I(S,T) is nonempty
```

Group the two reasons for display, but retain them independently:

```typescript
type IncomingConnection = {
  source: TaskIdentity | CheckedTransientTaskLocation;
  target: TaskIdentity;
  explicitRelation?: { label: string | null };
  inlineOccurrences: Array<{
    sourceRevision: string;
    line: number;
    start: number;
    end: number;
    rawLink: string;
    displayText: string;
  }>;
  verification: "current" | "pending" | "unavailable";
};
```

This is illustrative, not a proposed public JSON contract. Internal ranges need a documented coordinate system: Rust byte offsets and JavaScript UTF-16 offsets are not interchangeable. Convert from a common source revision or pin cross-language vectors with emoji and non-ASCII text before exposing ranges across that boundary.

The task identity is canonical vault-relative note path plus block ID. Occurrence coordinates are locators within a versioned snapshot, not durable identities. Revalidate before navigation; after edits, relocate by task identity and link occurrence, or open the source task with an honest fallback. Never jump to an unchecked stale line or silently rebind by title.

Key invariants:

- One source task counts once even if it mentions the target repeatedly or also has a relation.
- Removing one occurrence preserves the connection while another remains.
- Removing the explicit relation preserves inline evidence; removing the final inline occurrence preserves an explicit relation.
- Aliases are display text. They never become relation labels or enter label suggestions, hide preferences, rename rewrites, or cancel/complete matching.
- The reverse projection is never an input to either E or I.
- Self-links create no backlink to the same task. True mutual references remain two independent directions.
- Closing, cancelling, reopening, and archiving do not erase a still-present reference. Inference itself has no lifecycle effects.
- A completed task is not the same as a struck-through link. Keep references from completed task descriptions; exclude an explicitly struck-through reference as withdrawn text in the new inline extractor.

The label isolation is particularly important because this project has persisted label preferences and rename transactions. A generated origin must not accidentally become user vocabulary. Those decisions were read through the audited memory interface: `decisions:relation-label-hide-is-suggestions-only`, `decisions:relation-label-prefs-live-in-per-host-journal`, and `decisions:relation-label-rename-rewrites-history`.

### API compatibility

Do not silently widen today's `api.relationIndex.incoming()` to return editable-looking inline edges to old consumers. Preserve legacy authored-relation queries and add a capability-advertised typed query, for example `incomingConnections()`, for the new UI. The exact method name is not essential; **explicit opt-in to evidence-aware semantics is**. Use one underlying index with separate views, not an independently maintained second graph.

Update the chip model, Linked-from count, picker CURRENT rows, cold-scan fallback, and actions together. An old client lacking the new capability should continue showing authored relations, rather than offering a remove action it cannot execute correctly. Review any CLI/JSON changes against the repository's contract and release rules if implementation introduces them.

## 6. Storage: readable projection with an unambiguous origin

My preferred generated notation is:

```markdown
- 🪢 **LINKED FROM:** [[work#^source]] [in task text]
- 🪢 **LINKED FROM:** [[work#^source]] (follow-up of) [also in task text]
- 🪢 **LINKED FROM:** [[work#^source]] [also in task text]
```

These are three separate examples, not three rows under one task. They respectively mean inline-only, labelled explicit plus inline, and unlabelled explicit plus inline. An explicit-only entry keeps today's format unchanged.

Extend the mirror parser with exactly two optional, fixed provenance suffixes, outside the label parentheses. They are mirror-only generated syntax. Parse the block link first, then any ordinary label, then the recognized origin suffix. Unknown suffixes remain malformed. Mixed-origin markers are not inferred from user labels that happen to contain similar words.

Why pay for a small grammar extension?

- `(inline)` or `(in task text)` currently occupies the user-label slot. Reusing it would blur origin, pollute label operations, and make a real user label of that name ambiguous.
- An unexplained icon is not sufficient in plain Markdown.
- Persisting the source excerpt would duplicate prose, increase sync churn, and create stale quoted text. Keep excerpts live.
- Hidden HTML comments can encode machine provenance, but make source mode harder to understand and introduce another hidden field readers must maintain.
- A separate `MENTIONED BY` row would separate semantics clearly, but creates a second incoming surface, complicates deduplication, and diverges from the requested Linked-from design. It is a credible alternative if a merged row later proves confusing.

This grammar is a concrete recommendation, not a statement that square brackets are mandatory. Its acceptance criteria are mandatory: readable without plugins, distinguishable from arbitrary user labels, lossless for the two origin bits, and safely rejected by older parsers.

### Existing safeguards and their limits

Current JavaScript probes reject the proposed square-bracket suffixes as malformed; the Rust mirror pass explicitly leaves malformed rows alone and warns. That is useful protection against silent reinterpretation, **not proof of complete downgrade compatibility**. Some older actions may refuse, display raw text, or fail label-rename validation. All relation readers, small recognizers, formatters, planners, and rename paths need compatibility vectors before generation is enabled. [Rust mirror planner integration][C2], [parser][P1]

Retain the existing canonical sort, single-child slot, CRLF/final-newline preservation, and no-op write behavior. Existing `relations.linked_from_lines=false` must continue to prevent persistent mirrors and mirror-driven ID minting; live inspection can still show evidence. If a separate rollout switch is introduced, define disabling semantics clearly and do not overload label hiding as backlink suppression.

## 7. Extraction and resolution rules

Use the existing task parser and shared block-link scanner as foundations, but do not assume either alone establishes Markdown context. The current Rust task walker parses physical lines, while the link scanner skips inline code and reports embed/strike decoration. The new extractor needs context filtering around them. [Task parser][C4], [shared scanner][C5]

| Case | V1 behavior |
| --- | --- |
| `[[foo#^bar]]` in a source task description | Include if it resolves to one eligible task. |
| `[[foo#^bar|read this]]` | Include; alias is occurrence display text only. |
| `[[#^bar]]` | Resolve within the source note. |
| `[[path/foo.md#^bar]]` | Resolve canonical path; preserve authored source syntax. |
| Same target mentioned twice | One connection, two occurrence records. |
| Link on a nested `#task` description | Owned by that nested task alone. |
| Ordinary child prose, work/schedule logs, ledger bullets | Exclude in V1. |
| LINKS, LINKED FROM, DEPENDS ON, BLOCKS, Sub-projects | Exclude as inline evidence, including malformed managed rows. |
| Inline code, fenced code, frontmatter, comments, escaped markup, blockquoted task examples | Exclude. Carry file-level fence/comment state across lines. |
| `![[foo#^bar]]` | Exclude in V1; it is a transclusion, not the requested plain inline reference. |
| `~~[[foo#^bar]]~~` | Exclude as withdrawn inline evidence. Existing explicit-relation reader tolerance remains unchanged. |
| Note link or heading link | Exclude; neither identifies a task. |
| Resolved block belongs to a paragraph rather than a task | Exclude. A block-cache hit alone is insufficient. |
| Same block ID in two different notes | Distinct identities; source-context resolution decides the note. |
| Duplicate block IDs in the resolved note | Ambiguous; do not choose the first task. Preserve last-known output as unverified when appropriate. |
| Missing/half-typed/unresolvable link | Do not invent a new target. Distinguish edit uncertainty from confirmed removal. |
| Source refers to itself | Exclude. |
| Source or target is closed | Include if the reference still exists; show status normally. |

For resolution, use the existing source-context-aware Obsidian resolver on the plugin side and Bob's canonical note index on the CLI side. Pin agreement with vectors for duplicate basenames, paths, extension handling, same-note links, and explicit `done/` references. If the two engines disagree, the CLI must not persist a guessed backlink. Preserve the authored link and surface a bounded diagnostic.

A missing metadata cache entry during startup is **unknown**, not proof of zero links. Add a bounded fallback/retry. Similarly, scan completion and target validation are different facts: do not publish an apparently final zero count while target reads are still pending.

## 8. Live rendering and safe persistence

The system should have two clocks:

1. **Display clock:** after a settled editor update or file event, update evidence and the visible backlink. This uses current editor text where available and makes no cross-file write.
2. **Persistence clock:** after saved text passes the existing quiet/preimage checks, reconcile projects current evidence to writable target rows.

This preserves responsive feedback while limiting source mutations and undo surprises. Start with the current index's debounce and generation guards; tune only after measurement. Invalid partial input can retain the previous verified evidence temporarily with **source being edited** or **checking reference** state. Do not present uncertain evidence as a fresh fact.

### A first backlink needs a row

For targets without stored mirrors, render a virtual `LINKED FROM` row at the same managed slot where reconcile will eventually insert it. For an existing stored row, merge into that row. On persistence, replace the virtual host with the stored host atomically in presentation so the user never sees both.

A virtual row that changes editor height is not just another inline replacement decoration. Obsidian's guidance directs such layout-affecting decorations through a state field; viewport-only view-plugin decoration is not sufficient for this case. Reading view also needs an insertion path when there is no list item to decorate. Respect source-mode editing, task folding, embeds, and the existing chip toggle. [Obsidian decorations][W5]

### Writable and read-only boundaries

| Situation | Live view | Persistent projection |
| --- | --- | --- |
| Writable source with ID, writable target | Show evidence | Reconcile adds/updates target row. |
| Writable source without ID | Checked transient source location | Mint one source ID only when a persistent mirror can be safely produced; then serialize. |
| Source in archive/previous daily, with ID | Show evidence | May update a writable target; never edit the source. |
| Read-only source without ID | Show checked source excerpt/location | Omit that source's block entry; do not invent a link or mint in the archive. |
| Read-only target | Show virtual/current incoming view | Never insert or repair its row during reconcile. |
| Source or target changed since planning | Preserve verified/pending UI state | Skip/replan under existing safeguards. |

The ID-less, read-only case is an honest limitation of durable block backlinks. Opening its evidence should revalidate the source text and fall back to opening the note if it cannot uniquely locate it. A stale line number must never masquerade as identity.

All persisted links must point to source IDs that will actually exist after the write. Reuse the current staged/reconciled edit framework, source quiet checks, preimages, recovery snapshots, and dependency-aware write ordering. A source ID should land before a dependent reverse reference; a partial failure may leave a harmless unused ID or missing mirror that the next run repairs, never a knowingly fictional backlink.

Do not add a second plugin-owned write loop for inline mentions in V1. Existing immediate writers can keep handling explicit relation gestures; the live display covers the delay for text-derived evidence. If later courtesy writes are justified, they must merge both origin classes and obey the same guards. In particular, removing an explicit relation must not delete a mirror entry still supported by inline text.

Obsidian recommends cached reads for display and `Vault.process()` for read/modify/write operations, with a preimage comparison when asynchronous work intervenes. That supports the separation above if any new plugin write path is eventually introduced. [Obsidian Vault API guidance][W6]

### Uncertainty, moves, and archives

Never prune on an incomplete scan, unreadable source, ambiguous identity, transient rename, or stale preimage. Preserve existing entries as **unverified** and disable destructive actions until evidence settles. A confirmed valid source snapshot with its final eligible occurrence removed is sufficient to remove only the inline reason; a verified deletion is also a real removal. Uncertainty must not preserve orphaned entries forever after the source is known to be gone.

A move or archive changes path identity. The existing supported move/archive flows rewrite inbound links; reuse them, then re-resolve and canonicalize. Do not attempt recovery by title similarity. The archive source prefilter must be broadened beyond `LINKS`, and explicit archive targets mentioned by inline sources must also be loaded. Scanning every file's text for relationships is not permission to write every file.

Multi-host convergence should come from source text plus deterministic projection. No new backlink journal is needed. Generated rows and generated source IDs can still create Git churn or conflicts; idempotence and conflict/retry tests are required. The live index's authority prevents a stale mirrored row from becoming an independent fact.

## 9. Alternatives and their costs

| Approach | Strength | Main cost | Judgment |
| --- | --- | --- | --- |
| Automatically author ordinary LINKS edges | Reuses nearly everything | Redundant source bullets, two authorities, ambiguous deletion and labels | Reject. |
| Reuse a magic relation label such as `inline` | Small parser change | Collides with user vocabulary and label lifecycle | Reject. |
| Separate generated MENTIONED BY row | Very clear category boundary | Two incoming surfaces and duplicate sources | Viable fallback if usability tests reject merging. |
| Purely virtual backlinks | No mirror churn or ID minting; easiest rollback | Absent in raw Markdown and plugin-free reading; diverges from existing durable rows | Strong lower-cost alternative, but not my preferred final experience here. |
| Persist only; wait for reconcile | Uses existing storage architecture | Slow first feedback; stale rows can appear authoritative | Insufficient alone. |
| Live evidence plus generated LINKED FROM projection | Responsive, durable, familiar, explainable | Provenance grammar, virtual row host, coordinated readers/writers | **Recommended.** |
| General backlink graph for all nested task content | Broad recall | Ownership ambiguity, logs, noise, larger scan and UI surface | Defer until narrower use is demonstrated. |

If implementation budget is constrained, the best reduction is **live-only inline entries in the existing Linked-from surface**, not implicit authoring of LINKS edges. That would be an explicit change to the persistent-bullet requirement and should be described as such.

## 10. Implementation scope, performance, and release sequence

This is a moderate cross-repository feature, not a regex addition. Most work is in semantics, projection compatibility, and interaction safety.

| Area | Main implementation locations |
| --- | --- |
| Contract and conformance vectors | bob-cli `docs/task-relations.md`; linked plugin documentation and relation vectors |
| Extraction, provenance model, formatting, planning | bob-cli `src/native/task_relations/`; shared scanner/context helpers |
| Reconcile, archive loading, source ID guards | bob-cli `src/native/task_status_hooks/relations.rs` and its existing sync integration |
| Immediate explicit writers | Capture mirror planners and navigation relation follow-ups; preserve inline evidence on explicit edits |
| Live parsing and lifecycle | bob-plugins ledger-tools `145-relation-index-model.js`, `171-relation-index-lifecycle.js` |
| Chip, explanation, and virtual row rendering | ledger-tools `146-relation-chip-model.js`, `153-relation-widget.js`, `278-plugin-relation-model.js`, `282-plugin-relation-render.js`, styles |
| Task Card and reverse picker | navigation `312-task-card-relations.js`, relation stage/view/plugin files, generation-guarded fallback scan |
| Small readers and label operations | Relation recognizers in task-status-cycler/block-id-prompt; label catalog/rename paths |

The Mac capture client need not independently scan or interpret references. It already delegates capture behavior to Bob; only a changed shared response contract or user-facing count would require coordinated client work. Do not expand this task into an extra client-side graph.

### Performance discipline

Extract inline occurrences while already walking relevant task descriptions; maintain per-file source evidence and reverse lookup data. Keep startup chunked and cancellation/version guarded, coalesce events, and invalidate affected sources/targets on rename or deletion. Avoid rereading the entire vault on every editor event. Resolve cold-cache uncertainty with bounded work rather than treating it as emptiness.

The current lifecycle source records a historical startup incident involving vault-load event replay and excessive reads, plus a prior benchmark on a Markdown-only copy. I did not reproduce those measurements; they are a warning about the existing lifecycle constraints, not evidence that broader inline extraction is cheap. Preserve layout-ready registration and event coalescing, then rerun a controlled benchmark after changes. [Lifecycle comments and implementation][P2]

Measure cold startup, warm edits in a large note, first-reference discovery, archive loading, rename storms, target-read completion, and memory retained for excerpts. Use a generated fixture plus a separately authorized read-only representative vault copy. Report actual timings and memory rather than inventing a target from the old sample. The UI should stay responsive and avoid layout jumps; verify that in Obsidian, not solely Node mocks.

### Suggested delivery sequence

1. Specify the eligibility and provenance contract; add shared vectors and read-only extraction/indexing.
2. Ship readers and capability-aware UI paths, including origin actions and virtual-row behavior, before enabling new persisted syntax.
3. Extend every mirror planner and label operation; add guarded persistence and archive coverage. Dry-run output should expose affected notes and source-ID mints before first enablement.
4. Enable on a disposable fixture, then a preview of representative real data. Check accuracy and density, not just successful writes.
5. Ship compatible CLI/plugins together through the normal release/deployment process; no manual Cargo version or changelog edits. Test older-client behavior explicitly before multi-host enablement.

Do not leave “upgrade readers first” as a slogan: old CLI jobs on another host can still reconcile the vault. Inventory participating versions, define a minimum compatible set, and keep generation disabled until that condition is met. Rollback should stop new inline projection and remove only verified inline projection data with a compatible tool; it should preserve authored links, explicit relations, and already-minted IDs.

## 11. Acceptance criteria worth testing

A compact shared vector suite should verify the complete lifecycle, not merely that a regex finds `#^`.

| Scenario | Required result |
| --- | --- |
| First valid inline link; target has no children | One incoming row appears live and later persists; no source LINKS row. |
| Same-note and cross-note aliases | Correct task identity, unchanged source syntax, highlighted alias in explanation. |
| Two mentions of one target | One source chip, occurrence count two. |
| Remove one, then final occurrence | Count decreases, then inline evidence disappears; no unrelated changes. |
| Explicit plus inline; remove either reason | Other reason survives; origin and available actions change correctly. |
| A user label literally named `in task text` | Remains a label; cannot impersonate provenance. |
| Alias resembles a configured closing label | No cancel/complete/status/freshness side effects. |
| Code, comments, escaped links, frontmatter, malformed managed rows | No inline edges. |
| Child task and parent both mention target | Two correct source tasks; no ownership leakage. |
| Duplicate basenames/IDs; target is a non-task block | No guessed backlink or first-match ambiguity. |
| Broken/half-typed source, cold cache, read failure | Honest pending state; no destructive prune on uncertainty. |
| Source without ID | No mint during rendering or dry-run; guarded mint only when needed for persistent output. |
| Archive/previous daily source or target | Read coverage without forbidden writes; virtual fallbacks work. |
| Rename, move, archive, delete, undo/redo | Connection follows valid authored links; no phantom reverse edges. |
| Unicode text before the occurrence | Exact highlight/navigation despite byte versus UTF-16 offsets. |
| Reconcile twice with unchanged inputs | Second run changes zero bytes and mints zero IDs. |
| Concurrent source edit or failed write | Preserve authored content; no mirror to an ID that failed to land. |
| Stored plus virtual row transition | Exactly one visible row; stable selection, folding, and layout. |
| Inline-only CURRENT row or chip | No unlink/relabel route that edits arbitrary prose. |
| Light/dark, narrow layout, keyboard, touch, screen reader | Origin remains perceivable; context is operable and dismissible. |
| Old plugin/CLI reading new suffixes | Defined degradation; no relabeling or erasure of inline projection. |

For a short usability check, give Bryan three examples without explanation: inline-only, explicit-only, and mixed. Ask him to identify why each entry exists and remove just the explicit relation from the mixed case. If he expects the inline entry's × to remove prose, or cannot explain the badge without hovering, the design is not ready. This evaluation is proposed, not something performed during this research.

## 12. Sources and evidence boundaries

Repository links below are pinned to the inspected commits. The files were read from the approved local checkouts; the links provide durable locations for review. No peer report was consulted. Memory was read through `sase memory read`; no memory or application source was changed.

- [Bob relation contract][C1]: authored versus generated rows, identity, slots, projection, archive boundaries, gestures, chip conventions, label effects.
- [Rust relation reconcile implementation][C2], [relation model][C3], [task parser][C4], [shared block-link scanner][C5], [formatters][C6]: current extraction and persistence constraints.
- [Plugin parser][P1], [live index lifecycle][P2], [chip model][P3], [Task Card][P4], [Reading renderer][P5], [editor/actions][P6], [styles][P7]: actual client integration and behavior.
- [Obsidian internal links][W1] and [Backlinks][W2]: primary product semantics.
- [Obsidian decorations][W5] and [Vault API guide][W6]: primary implementation guidance.
- [W3C hover/focus][W3] and [use of color][W4]: reasons for persistent textual provenance and accessible context presentation.

External documents were consulted on 2026-10-29. They support platform and accessibility facts, not a claim that this particular design has been usability-tested. I attempted to access dedicated resolver API documentation, but those pages did not resolve through the browsing tool; resolver recommendations here are grounded in the inspected plugin implementation instead.

[C1]: https://github.com/bobs-org/bob-cli/blob/48253b7f225620f2cde10c856f458c31cd6f58d3/docs/task-relations.md
[C2]: https://github.com/bobs-org/bob-cli/blob/48253b7f225620f2cde10c856f458c31cd6f58d3/src/native/task_status_hooks/relations.rs
[C3]: https://github.com/bobs-org/bob-cli/blob/48253b7f225620f2cde10c856f458c31cd6f58d3/src/native/task_relations/mod.rs
[C4]: https://github.com/bobs-org/bob-cli/blob/48253b7f225620f2cde10c856f458c31cd6f58d3/src/native/task_status_hooks/parse.rs
[C5]: https://github.com/bobs-org/bob-cli/blob/48253b7f225620f2cde10c856f458c31cd6f58d3/src/native/task_dependencies/mod.rs
[C6]: https://github.com/bobs-org/bob-cli/blob/48253b7f225620f2cde10c856f458c31cd6f58d3/src/native/task_relations/format.rs
[P1]: https://github.com/bobs-org/bob-plugins/blob/68db3fbefa30e13767f58fcf18c9c0b3fccd4b53/plugins/bob-ledger-tools/src/145-relation-index-model.js
[P2]: https://github.com/bobs-org/bob-plugins/blob/68db3fbefa30e13767f58fcf18c9c0b3fccd4b53/plugins/bob-ledger-tools/src/171-relation-index-lifecycle.js
[P3]: https://github.com/bobs-org/bob-plugins/blob/68db3fbefa30e13767f58fcf18c9c0b3fccd4b53/plugins/bob-ledger-tools/src/146-relation-chip-model.js
[P4]: https://github.com/bobs-org/bob-plugins/blob/68db3fbefa30e13767f58fcf18c9c0b3fccd4b53/plugins/bob-navigation-hotkeys/src/312-task-card-relations.js
[P5]: https://github.com/bobs-org/bob-plugins/blob/68db3fbefa30e13767f58fcf18c9c0b3fccd4b53/plugins/bob-ledger-tools/src/282-plugin-relation-render.js
[P6]: https://github.com/bobs-org/bob-plugins/blob/68db3fbefa30e13767f58fcf18c9c0b3fccd4b53/plugins/bob-ledger-tools/src/278-plugin-relation-model.js
[P7]: https://github.com/bobs-org/bob-plugins/blob/68db3fbefa30e13767f58fcf18c9c0b3fccd4b53/plugins/bob-ledger-tools/styles.css
[W1]: https://obsidian.md/help/links
[W2]: https://obsidian.md/help/plugins/backlinks
[W3]: https://www.w3.org/WAI/WCAG22/Understanding/content-on-hover-or-focus.html
[W4]: https://www.w3.org/WAI/WCAG22/Understanding/use-of-color.html
[W5]: https://docs.obsidian.md/Plugins/Editor/Decorations
[W6]: https://docs.obsidian.md/Plugins/Vault

## Recommended solution

**Add provenance-aware inline backlinks to the existing LINKED FROM experience.** Discover plain task-block wikilinks in task descriptions, keep the original prose as the authority, and show one incoming source entry with an always-visible **in task text** badge and the exact source context. Do not auto-author outgoing LINKS rows, invent labels, or remove prose through a backlink control.

Back this with one live evidence index and the existing guarded Markdown projection, using explicit mirror-only provenance rather than a magic label. Preserve archive write boundaries, handle missing source IDs honestly, and distinguish uncertainty from removal. Start with description-line scope, ship compatible readers before writers, and judge success by whether Bryan can immediately understand and navigate each backlink without learning another relation vocabulary.
