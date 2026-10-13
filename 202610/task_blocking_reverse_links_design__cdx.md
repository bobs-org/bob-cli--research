# Reverse dependency links: a compact, trustworthy “Blocks” row

Researcher: **cdx**  
Date: **2026-10-13**  
Scope: independent design research; no feature implementation or live-vault mutation.

## Recommendation at a glance

Build the feature. Add one generated direct-child row, `⛓️ **BLOCKS:**`, to an unfinished task when at least one unfinished task explicitly depends on it. Put all those dependents on that one row as ordinary block links. Render the row with the existing dependency-chip visual language.

Keep `Depends On` as the only dependency-authoring surface. The reverse row is disposable derived data: deleting or editing it never changes dependencies, and reconciliation restores its correct contents. Prefer navigation-only reverse chips in the first release.

The substantial work is reliable maintenance across notes, undo, completion, moves, and tasks without block IDs. The graph inversion itself is small. Do not turn this into a second dependency system.

## 1. What I investigated and what the existing design requires

I inspected bob-cli's dependency contract, R1–R10 reconciliation, promotion graph, guarded-write machinery, successor ID allocator, and dependency tests. I independently opened bob-plugins and examined its dependency editor, hand-edit mirror, cross-note preparation, and chip renderer. I reviewed official Tasks, Linear, and Asana documentation. I did not consult any other report or researcher from this swarm.

Source revisions inspected:

- **bob-cli:** `92515f1bb8565fa7d6116e4581911b9f45e880bb`.
- **bob-plugins:** `4f0cc94231556c5058030187da02b827a9ba8b93`.

These are source-inspection findings, not measurements of Bryan's live dependency graph. I did not benchmark a prototype or run feature tests; the acceptance cases below specify what an implementation should prove.

### Existing facts that constrain the design

| Finding | Consequence |
| --- | --- |
| A single managed `⛓️ **DEPENDS ON:**` row is authoritative; `[dependsOn::]` and prerequisite `[id::]` fields are projections. | Generate reverse rows from the accepted forward edges. Never derive forward edges from reverse rows. |
| Closed prerequisites remain on forward rows as history. Done and Cancelled stop blocking. | An inverse relationship is not necessarily a current blocker. Define the lifetime of `Blocks` explicitly. |
| R1–R10 processes open dependents, skips the protected previous daily note, and preserves malformed forward rows with warnings. | A naive second pass cannot assume every input was reconciled or writable. |
| A dependent can have a forward row without its own `^block-id`. | Reverse links require a new identity-allocation rule for that dependent. |
| The promotion graph uses block-addressable sources and adds implicit project/resident edges. | Simply inverting that graph loses unanchored dependents and invents reverse links for inherited project effects. |
| Cross-note target preparation precedes the dependent's one-editor-transaction commit. | Target identity can be prepared early; a reverse row asserting a new dependency should be written after the dependency commits. |
| Reconcile stages files, checks preimages, waits for structural quiet, and replaces files individually with recovery records. | Extend this mechanism; do not promise a vault-wide atomic transaction. |
| `^prj` dependencies can block a project's residents and descendants without copied dependency edges. | Persist the explicit project dependency once, rather than listing every inherited resident as a direct dependent. |

Evidence: bob-cli `docs/task-dependencies.md` §§2–7, 12–13; `src/native/task_status_hooks/reconcile.rs:283`, `:880`, `:1647`; `src/native/task_status_hooks/references.rs:313`; `src/native/task_status_hooks/sync.rs:430`; `src/native/task_status_hooks_write/preflight.rs` and `apply.rs`. Plugin evidence: `plugins/bob-navigation-hotkeys/src/080-dependency-identity.js:790`, `580-plugin-properties-and-dependency-edit.js:334`, `590-plugin-dependency-stage.js:143`, and `600-plugin-dependency-mirror.js`.

The accepted decision `decisions:task-deps-are-depends-on-links`, read through audited SASE memory, explicitly rejected two competing editable representations and one bullet per prerequisite. The proposed reverse row preserves that decision: it is a generated view, and still only one child per direction.

## 2. Is this a good idea?

**Yes, for visibility and navigation.** A forward row answers “what am I waiting on?” A reverse row answers “what work is waiting on this?” That second question is useful when selecting a prerequisite, understanding why a small task matters, and checking the consequences of postponing it. It is especially valuable when the dependent lives in another note.

The terminology is familiar. Asana exposes separate incoming and outgoing dependency fields, and shows a predecessor the work waiting on it. Linear distinguishes “Blocked by” from “Blocks,” and moves resolved blocking relations out of the active blocking category. These are useful interface precedents, not evidence that their storage strategies should be copied. [Asana task dependencies](https://help.asana.com/s/article/task-dependencies), [Linear issue relations](https://linear.app/docs/issue-property#issue-relations).

There is an even closer precedent in the installed ecosystem: Tasks already has `is blocking`. Its documented definition requires a direct dependency and open status types at both ends; Done, Cancelled, and Non-task do not qualify. This supports active, direct semantics for the new row. [Tasks dependency filters](https://publish.obsidian.md/tasks/Queries/Filters).

### The costs are real

1. **Redundant Markdown creates maintenance work.** One dependency edit now affects another task's block, often in another note. Completion also changes incoming reverse rows. Sync can temporarily carry stale generated content.
2. **More children compete with the task headline.** A prolific prerequisite can accumulate many backlinks. One compact row and display-only overflow are essential.
3. **Counts can suggest the wrong priority.** A task blocking ten low-value tasks may matter less than a task blocking one critical outcome. This feature should not change priority, freshness, schedules, or lane policy.
4. **“Blocks” can be mistaken for “finishing this makes all those tasks Ready.”** A dependent may also have another prerequisite, a future schedule, or an inherited project reason.
5. **A rendered reverse row can become a confusing editing surface.** A hover `×` that silently edits a different task would add a second authoring workflow before its undo behavior is understood.

If the real need were just identifying bottlenecks in a task query, I would start with Tasks' existing `is blocking` filter. For the requested in-note explanation and direct navigation, the reverse row offers a meaningful improvement.

## 3. Requirement adjustments I recommend

These are proposed changes or clarifications, not descriptions of existing behavior.

| Adjustment | Why it is justified |
| --- | --- |
| **One child row per prerequisite, containing all direct dependents.** No bullet per dependent. | Fits the established compact dependency design and avoids unbounded child-list growth. |
| **Only active blocking belongs in `Blocks`: both endpoints must be open.** | A completed prerequisite no longer blocks anything, even though forward history remains. |
| **Only explicit direct dependencies are persisted.** | Transitive paths and inherited project effects would inflate counts and misrepresent authored relationships. |
| **Reverse rows are generated and navigation-only in v1.** | Keeps one source of truth and avoids surprising cross-note removals. |
| **Maintenance covers removal, completion, cancellation, reopening, moves, and undo—not only additions.** | An append-only implementation would become misleading almost immediately. |
| **Mint a block ID for an open dependent that needs a reverse backlink.** Do not add a Tasks `[id::]` solely for that purpose. | Ordinary block links need an anchor; Tasks dependency identity and Markdown block identity are different. |
| **Allow narrowly scoped removal of this generated row under closed tasks in writable active notes.** | Existing “closed dependents are never touched” behavior otherwise leaves stale `Blocks` rows on completion. Forward history and the closed task line still remain untouched. |
| **State consistency guarantees within existing writable scan boundaries, with explicit deferred/warning output.** | Protected previous-day snapshots, inaccessible notes, and excluded archives cannot honestly be covered by an unconditional “everything is consistent.” |

The closed-task exception is particularly important to call out. It should be documented and tested as “remove a known machine-owned reverse row,” not generalized permission to normalize historical task blocks.

## 4. Product contract

### 4.1 Meaning

Let `D → P` mean “dependent D has an accepted explicit dependency on prerequisite P.”

Then:

```text
Blocks(P) = { D | D → P is an accepted direct edge
                 and D is open
                 and P is open }
```

“Open” uses the configured Tasks status type: Todo, In Progress, or On Hold. A `[?]` task is still open. A prerequisite that is itself blocked can therefore block another task too.

The edge set comes from the successful forward reconciliation result: resolved, project-valid, projectable links, plus R8 field-covered legacy children during the supported migration window. It excludes self-links, non-task links, unresolved links, archive history, and links deliberately refused by the existing ID/project rules. A mere stale `[dependsOn::]` breadcrumb is insufficient evidence.

Do not exclude `#hide` tasks just because they are visually muted. Their open dependencies are still real. Use Bob's normal scan exclusions rather than adding a second eligibility policy.

For a cycle introduced by hand editing, preserve and expose its valid direct edges and the existing cycle warning. A reverse row must not invent cycle-breaking behavior or bypass the picker guard.

### 4.2 Direct project links, not an inherited expansion

If `Launch project ^prj` depends on `Obtain approval`, the approval task's reverse row links to that `^prj` task. It does not list every project resident and descendant.

A chip targeting `^prj` should use the existing cleaned task headline and project note context; its tooltip can explain that resident work inherits the project block. Do not add a stored resident count or claim that those residents authored individual dependencies.

Also do not use future schedules as reverse dependency edges: a date is a blocking reason, not another task.

### 4.3 Lifecycle

| Event | Expected result |
| --- | --- |
| Add `D → P`, both open | P lists D once. |
| Add another dependent of P | Append/rebuild the same row; no additional child row. |
| Remove `D → P` | Remove D from P's row; delete the row when empty. |
| Close or cancel D | D disappears from every prerequisite's reverse row. |
| Close or cancel P | Remove P's own reverse row. D's forward link to P remains historical. |
| Reopen D or P | Recompute the row; it reappears when both ends qualify. |
| D also depends on Q | P still lists D. Completing P alone does not promise to unblock D. |
| Move or rename a task/note | Heal/re-resolve forward relationships first, then regenerate reverse links at their current locations. |
| Hand-delete P's reverse row | Recreate it without changing any forward dependency. |
| Hand-add a fake reverse link | Remove it on successful reconciliation; never create a forward edge. |
| Undo a dependency gesture | Recompute from the restored forward state and repair other notes' generated rows. |
| Archive a completed task | Strip its generated reverse row as part of the archive write; preserve forward history. |

Full reconciliation remains the repair authority. Immediate maintenance should normally finish with the initiating action, but a safe refusal or interrupted cross-note write may leave generated rows pending repair.

## 5. A visual design that fits Bob

### 5.1 Markdown writer form

Use the existing chain icon, separator, plain-link policy, indentation, and line-ending conventions:

```markdown
- [*] #task Confirm venue [id:: events__venue] ^venue
  - ⛓️ **BLOCKS:** [[#^invitations]] • [[#^catering]]

- [?] #task Send invitations [dependsOn:: events__venue, events__guest-list] ^invitations
  - ⛓️ **DEPENDS ON:** [[#^venue]] • [[#^guest-list]]

- [?] #task Book catering [dependsOn:: events__venue] ^catering
  - ⛓️ **DEPENDS ON:** [[#^venue]]

- [ ] #task Finalize guest list [id:: events__guest-list] ^guest-list
  - ⛓️ **BLOCKS:** [[#^invitations]]
```

The label provides the direction. Reusing `⛓️` makes the pair look like one relationship family. Avoid a lock icon: a prerequisite can be Ready or Next while it blocks others, so a lock risks confusing outgoing relationships with its own status.

A task can own both rows. Keep the established `Depends On` first-child position. The new row follows the existing relation header group:

```text
CANCEL LOG, if present
DEPENDS ON, if present
Sub-projects, on ^prj if present
BLOCKS, if nonempty
other existing children
```

This preserves the current `^prj` sub-project ordering. Insert a new reverse row at that slot. Update an existing valid row in place rather than moving authored children around just to achieve visual tidiness; flag awkward duplicates/malformed cases through the rules below.

Writers emit no aliases, embeds, strikes, stored counters, or empty placeholders. Reuse the shortest unambiguous link form from the owning prerequisite to its dependent. No dependency-ID path encoding is required for the dependent solely to create this ordinary wikilink; a note name with spaces can still be linked.

Reserve the exact managed `BLOCKS` label under an owning `#task` as machine-maintained content. A recognizer may tolerate the missing emoji/VS16 as the forward parser already does, but it should not claim unrelated prose saying “blocks.”

### 5.2 Rendered form

```text
[*] Confirm venue
    ⛓ blocks  ( ? Send invitations )  ( ? Book catering )

[?] Send invitations
    ⛓ depends on  ( * Confirm venue )  ( ○ Finalize guest list )  ＋  waiting on 2
```

Use the existing `bob-dep-row` and `bob-dep-chip` family: quiet label, compact pills, miniature status symbol, cleaned title, and `↗ note` for cross-note context. Use existing theme/status tokens. Keep task text stronger than the relation label; do not add a competing bright “blocker” badge to every task headline.

Because dependents will often all be `[?]`, many chip accents will be the existing Blocked color. Keep the subtle border treatment rather than filling the whole row red.

Show at most three chips by default, then an accessible `+N more` disclosure. The disclosure reveals all remaining chips in a popover/list with keyboard navigation; it does not rewrite or truncate Markdown. Use ordinary line-height rhythm, wrap between chips at narrow widths, and avoid clipping the overflow control. With one or two chips, no extra count is necessary.

Counts mean **open direct dependents**, not exclusive blockers or guaranteed Ready recoveries. Useful tooltip copy: “These tasks have an unfinished dependency on this task. They may also have other blocking reasons.” A disclosure's accessible name should say “Show N more dependent tasks.”

### 5.3 Interaction

- Click or Enter opens the dependent; Mod-click follows the existing new-tab behavior.
- Hover provides the native page preview and the full title, note path, and status.
- Put the cursor on the row to reveal raw Markdown, matching current chips.
- In v1, omit the reverse row's `＋` and per-chip `×`. To change the relationship, follow the chip and edit the dependent's existing `Depends On` row.
- Ctrl+Shift+P on the reverse row should resolve to its **owning prerequisite**, consistent with task-child ownership. It must not silently treat the chip under the cursor as the dependency editor's owner.
- Source mode and a vault without these plugins retain ordinary readable block links.

The display parser/renderer needs an explicit relation direction. Reuse chip anatomy without blindly reusing incoming-row semantics, action callbacks, `waiting on` copy, or ARIA labels. Existing code hardcodes these in `140-dependency-model.js`, `150-dependency-element.js`, and both preview/reading render paths.

No runtime labels such as “projection” or “cache generation” belong in the ordinary product interface. A repair failure can say “Dependency saved; Blocks row update deferred.”

## 6. How I would implement it reliably

### 6.1 Expose explicit edge provenance

Extend the forward reconciliation result to expose accepted **explicit** edges independently of the promotion graph. An edge should retain its source task locator, resolved target locator, and enough information about resolution/writability to explain a skipped reverse update.

Initially, locate a source by note and task position while planning; convert it to a block identity when needed. This prevents silently dropping dependents that do not already have `^block-id`.

Do not invert `dependency_edges()` as-is. In `references.rs:313`, it skips sources without block IDs and adds implicit resident/ancestor edges at the end. The cycle graph in `reconcile.rs` also requires a source block ID and includes inherited edges. Both are useful existing graphs, but neither exactly matches the proposed product contract.

Do not independently infer edges by scanning every wikilink/backlink. R4 breadcrumbs, ordinary reading embeds, and project-invalid links would produce false relationships.

### 6.2 Anchor unaddressable dependents

For an open dependent with at least one accepted open prerequisite, reuse its valid existing `^block-id`; otherwise mint one with the existing automatic block-ID policy. Rust already has `capture_block_ids::mint_block_id` at line 619, used for successor dependents. Check all block IDs in the note, including non-task blocks and batch reservations.

Allocate once per dependent, not once per outgoing edge. Keep existing IDs stable, and do not add a Tasks `[id::]` field unless the task separately becomes a prerequisite under the normal rules.

In a gesture, include the source anchor in the dependent's existing editor transaction. In reconciliation, plan it deterministically and report it. Allocation is a narrowly documented structural edit; it must not stamp freshness. Escaping a picker, a dry-run, and an aborted gesture allocate nothing on disk.

This is an intentional usability choice: do not introduce an unexpected second ID prompt just to support a generated backlink. Preserve existing prerequisite-ID prompts.

### 6.3 Build and render one reverse map per snapshot

After forward adoption/healing/projection and source-anchor planning:

```text
for each accepted explicit D → P:
    if D and P are open:
        reverse[P].insert(D)

for each writable task P with expected or existing managed reverse content:
    expected = canonical Blocks links from reverse[P]
    insert, replace, deduplicate, or remove the managed row
```

Use note path plus block identity, not a naked block ID. Guard duplicate block definitions and ambiguous resolution; do not link to whichever task happens to appear first.

Make reverse order deterministic: same-note dependents in document order, then other notes by normalized vault-relative path and document order, with block ID as a tie-breaker. This differs deliberately from forward rows' append-preserving author order: reverse rows have no user-authored order to preserve. Avoid sorting by mutable status or task title, which would churn bytes during ordinary maintenance.

Index building is linear in scanned tasks and accepted edges; ordering adds the usual per-row sort cost. Maintain note-name ambiguity indexes rather than rescanning the vault for each backlink.

### 6.4 Fit reverse writes into reconciliation's existing guarded output

Plan both directions from one reconciled in-memory snapshot. Fold reverse line edits and new source IDs into the note-edit composition so later status changes/regrouping do not use obsolete line offsets. Apply edits against original coordinates in a coherent per-note edit plan, or reparse/rebase between passes.

Feed touched notes through the same structural quiet interval, preimage verification, recovery, and retry mechanism used today. Do not issue a second independent post-reconcile filesystem-writing loop.

A source dependency can exist after an interrupted write while its reverse row is missing or stale. That is repairable. Forward status derivation remains authoritative and does not read `Blocks`. Recovery reports must retain the existing applied/deferred file distinction.

The command still inherits current prerequisites: today’s daily note must exist, have a Pomodoros section, and pass the multiple-timed-entry guard. This research does **not** recommend broadening `bob task reconcile` into a separate dependency-only command to bypass those checks. Document that an invalid daily note can defer full repair; immediate plugin maintenance should not require running the whole reconciler. Evidence: bob-cli `README.md:624` and `src/native/task_status_hooks/sync.rs:225`.

### 6.5 Immediate plugin maintenance: authoritative write first

Use a shared reverse-row planner/maintainer across dependency entry points rather than adding custom append code only to Ctrl+Shift+P.

For a same-note edit, plan the forward change, source anchor, and affected reverse rows together and commit them in the existing single editor transaction. One Ctrl+Z restores that note coherently.

For cross-note edits:

1. Preserve the existing target identity/preparation behavior.
2. Commit the dependent's forward row, field, source anchor, and normal status effects.
3. Update affected prerequisites' reverse rows from the committed forward state, through open editors where available and preimage-checked `vault.process` otherwise.
4. If step 3 fails, keep the valid dependency, report the deferred generated update, and let reconciliation repair it.

Do not write a new reverse relationship during target preparation: if the dependent commit fails, that would leave a false assertion of a relationship.

Coalesce updates to the same note and use current task identities to find owners again after line insertions. Checking only the task headline is insufficient protection if the generated child or other task-block contents changed concurrently.

Cross-note operations do not have one global undo stack. Promise one undo for the dependent's editor transaction; repair generated rows in other notes when the forward state changes through undo/redo. Never blindly replay an old whole-note snapshot over unrelated later edits.

### 6.6 Cover other writers and avoid feedback loops

The reverse index must observe accepted dependency changes and endpoint status/location changes. Cover:

- Task Card edits, counted/batch gestures, API edits, and chip removals;
- the existing forward hand-edit mirror;
- task close/cancel/reopen through task-status-cycler and block-id-prompt;
- CLI capture/dependency writes, reconcile, moves/renames, and archival.

For Obsidian, use a coalesced change worker with open-buffer overrides and the existing warm-cache/fallback principles. Process graph changes off the keypress path; render visible ranges from memory. Do not read the vault on every search keystroke or every chip render.

Invalidate old and new prerequisite neighborhoods when a dependent changes; update an endpoint's incoming neighborhood when its status changes. A note rename must refresh canonical link spelling even when semantic edge membership is unchanged.

Ignore reverse-row-only changes as graph inputs and compare canonical output before writing. This is essential to avoid event loops and repeated undo entries.

For bob-cli mutations, integrate the pure reverse planner where the changed notes are already staged; run the normal reconciler as the whole-vault backstop. Merely implementing the plugin would leave headless capture and manual edits inconsistent.

### 6.7 Respect uncertain and historical inputs

Only delete/rebuild a row when its contributing input set is known. A cold/partial cache, a note read failure, or a malformed authoritative forward row is not proof that a dependency vanished.

For malformed forward owners, preserve prior reverse entries attributable to that uncertain owner and warn. If affected targets cannot be identified safely, defer destructive reverse pruning rather than replacing a whole-vault reverse map with an incomplete one. Valid, authoritative removals still take effect.

For malformed reverse content or a reserved-label row with prose/nested authored children, leave it untouched and report a specific warning. Never swallow those children when removing an empty generated row. Canonical duplicate rows containing only recognized managed content may be consolidated safely.

Never mint IDs or write rows in the protected previous daily note. Where an otherwise accepted relationship cannot receive an anchor or destination write, report that omission; do not use a note-level link or fabricated task anchor as a substitute.

Remove generated rows before supported archive operations move tasks out of the active scan. Do not expand normal reconciliation to rewrite every historical archive solely to maintain this live view. An externally moved stale archived row remains an explicit limitation; a renderer that recognizes a terminal owner should not present it as live blocking.

## 7. Reporting, conformance, and rollout

Extend the existing human/JSON reconcile report additively. A concrete proposal is `blocking_line_updates` with inserted/replaced/removed/consolidated actions, source/owner location, and resulting link count; `dependent_block_ids_created`; and structured reverse-maintenance warnings. Keep applied/deferred output semantics distinct from planned changes. Dry-run should preview newly minted anchors and generated rows without writing them.

No new CLI subcommand or flag is needed for the core feature.

Update the shared dependency contract with the new grammar, authority rule, lifetime, source-ID policy, insertion order, uncertainty behavior, and closed-task exception. Add shared conformance vectors before implementing Rust and JavaScript mirrors. In the plugin repo, edit source fragments, regenerate entrypoints, and deploy through `bob plugins sync`; never hand-edit generated `main.js` or vault plugin copies.

### Acceptance cases that matter

| Case | What must be proved |
| --- | --- |
| Two dependents share one prerequisite | Exactly one reverse row; exactly two unique links. |
| Dependent has two prerequisites | Both prerequisite rows list it; completing one need not unblock it. |
| Either endpoint closes/cancels | Corresponding active reverse entries disappear; forward history survives. |
| Reopen either endpoint | Correct entries return without duplicate IDs or rows. |
| Dependent lacks `^block-id` | One collision-safe source anchor is created and reused across all backlinks. |
| IDs collide with a prose block or batch reservation | Allocation avoids every occupied ID, not only task IDs. |
| Same block ID exists in different notes | Correct path-qualified identities and unambiguous links. |
| Duplicate block definitions in one note | Safe warning/refusal, never arbitrary owner selection. |
| Rename/move across notes | Old row membership and link spelling repair; forward healing runs first. |
| `^prj` dependency with nested projects | One direct project backlink; no fabricated resident/transitive entries. |
| Resolved, unresolved, non-task, self, unencodable, and cyclic inputs | Reverse membership matches the accepted forward semantics and warning policy. |
| False, deleted, empty, duplicate, or malformed reverse rows | Generated data repairs where safe; no forward edges are created and no prose is lost. |
| LF/CRLF, no final newline, tabs/spaces, cancellation and schedule logs | Byte conventions, ownership, log order, and unrelated children survive. |
| Fenced/quoted/nested `BLOCKS` text | Unowned examples and prose are untouched. |
| Same-note add/remove then Ctrl+Z | Forward row, source ID, and reverse row restore in one transaction. |
| Cross-note undo/redo or failure after forward commit | Authority remains correct; reverse repair is bounded, visible, and preserves unrelated edits. |
| Cold cache, stale editor, partial scan, or malformed forward owner | Missing information never causes destructive pruning. |
| Protected previous-day and archive paths | No unauthorized historical writes; omissions are reported. |
| Second reconcile on unchanged complete inputs | Zero additional row/ID edits, apart from persistent warnings. |
| Plugin source/preview/reading views, narrow widths, keyboard focus | Correct relation direction, complete accessible overflow, and no accidental dependency actions. |

An additional invariant is valuable: deleting all well-formed generated reverse rows should leave blocking, promotion, scheduling, successor behavior, and authored forward edges unchanged; one successful reconcile rebuilds the rows.

Ship the Rust reconciliation and plugin mutation support as one compatible feature, with both Live Preview and Reading View chips ready. A plain-link fallback makes CLI-first ordering technically safe, but exposing a raw field before its navigation and lifetime are understood would underserve the design goal.

Preview the first vault application with the existing `bob task reconcile --dry-run --format json`. Review changes involving minted source IDs, closed-task cleanup, protected-note omissions, and large fan-outs before the normal deployment. This is a rollout recommendation, not an additional approval gate requested by this research.

## 8. Alternatives considered

| Alternative | Merit | Reason to decline as the primary implementation |
| --- | --- | --- |
| Existing `is blocking` query only | No new redundant Markdown; quickly exposes blockers. | Does not provide the requested contextual dependent links beneath the prerequisite. |
| Virtual reverse chips with no stored row | Least filesystem churn; easiest completion/history handling. | Plain source mode and plugin-free reading lose the feature, and reconcile cannot ensure requested sub-bullets exist. Sensible fallback if write/undo costs prove unacceptable. |
| Stored `Required by` row including history | More semantically accurate for persistent relationships involving closed tasks. | Less focused on work currently waiting; introduces a second historical listing that duplicates the forward record. |
| Bidirectionally editable `Blocks` and `Depends On` | Convenient editing from either end. | More cross-note undo and error cases, and a greater chance of competing authority. Revisit only as an explicit UI feature that still writes forward authority. |
| A boolean `#blocks` tag or count on the task line | Compact scanning signal. | No navigation, another stale stored field, and added task-headline clutter. |
| One bullet per dependent or transcluded task | Rich text visible without custom chips. | Bloated task blocks; embeds risk reintroducing old close/promotion inference problems. |
| Full transitive downstream rollup | Shows broad potential impact. | Confuses direct authoring with reachability, expands project inheritance, and invites misleading priority/count claims. |

I favor stored active reverse rows because they satisfy the requested portable Markdown form while keeping the existing dependency system intact. If maintenance becomes expensive in practice, the fallback should be virtual navigation-only reverse chips—not a new editable reverse field.

## 9. Remaining uncertainty and confidence

Confidence is high on the single-authority design, active/direct semantics, source-anchor requirement, and the danger of inverting the existing promotion graph. These follow from inspected contracts and code.

Confidence is moderate on the initial three-chip overflow threshold and ordering preference. They are design choices that should be checked against Bryan's actual fan-out distribution and a narrow-window prototype. I did not collect live-vault counts.

The most important unresolved implementation detail is how to reuse a source block-ID policy consistently across Rust and the relevant plugin writers without adding an unwanted prompt or another subtly different allocator. That should be resolved through shared vectors, not assumed away.

The user-experience tradeoff is explicit: the active `Blocks` row disappears after completion, while dependency history remains on dependents' forward rows. If Bryan prefers a permanent reverse relationship ledger, choose `Required by` and design history deliberately; do not label historical links as live blockers.

## Recommended solution

Implement **one generated `⛓️ **BLOCKS:**` direct-child row listing open explicit dependents of an open prerequisite**, rendered with Bob's existing chips and navigation behavior. Keep `Depends On` authoritative; maintain the reverse row after committed dependency/status changes and rebuild it within `bob task reconcile`'s guarded write.

Treat missing dependent anchors, closed-task cleanup, cross-note undo, uncertain scans, and direct-versus-inherited project edges as first-class requirements. Preserve existing status, promotion, freshness, and scheduling policy. This gives Bryan a useful, compact view of why a task matters without creating a second dependency system.
