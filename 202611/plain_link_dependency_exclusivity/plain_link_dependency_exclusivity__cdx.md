# Dependencies and plain links: one deliberate relationship choice

Independent research by **cdx**, 2026-11-25. Developed from Bob's code, contracts, audited project memory, and primary external documentation. No other researcher's report or findings were consulted. This is design research, not an implementation or an inspection of the live vault.

**Recommendation in brief.** Adopt the exclusion rule for **unlabelled task relations and explicit direct dependencies**. A successful managed operation should leave a task pair with dependencies or plain relations, never both. Preserve each edge's direction and preserve labelled relations. Add `Ctrl+B` to Links and Linked from, and `Ctrl+L` to Depends on and Blocks. Present each shortcut as an explicit action with a visible consequence, not as a hidden mode switch. Implement the common relationship transition before adding the shortcuts: today's independent writers cannot safely provide the full guarantee by being called one after the other.

**Is this a good idea?** Yes. If A cannot proceed until B is finished, the dependency already communicates that they are connected. An additional unlabelled relation contributes little information while creating another thing to maintain. Converting the connection in one gesture fits how understanding changes: something first collected as related work can become a prerequisite, and a supposed prerequisite can later prove optional.

The cost is that creating a plain link now has scheduling consequences when it replaces a dependency. Bob currently describes ordinary relations as inert. That remains true of the resulting relation, but no longer describes the conversion operation. A beautiful interface must make this distinction legible before the write. “Linked” alone is insufficient feedback when another task has just become unblocked.

I would not extend the exclusion to labelled relations. A task can both depend on another and be “inspired by” it; removing the label discards information. Some labels also drive completion, cancellation, merge, or successor behavior. Nor would I redefine all plain relations as undirected: Bob already has separate Links to and Linked from workflows, and A → B and B → A are independent stored edges. Pair-wide exclusivity does not require discarding those directions.

**What the implementation establishes.** I examined bob-cli at `68dee6e1f280f235971d55ee915ce46e82902b29` and bob-plugins at `bdb85e34dca948c36e547937d45df3caabb5d50a`. Findings are grounded in the local checkouts; these links pin the inspected versions.

| Finding | Consequence for this feature | Evidence |
| --- | --- | --- |
| Dependencies are authored on the dependent's DEPENDS ON line; `[dependsOn::]` and BLOCKS are derived. Reverse Blocks editing writes the other task's DEPENDS ON line. | Change the authored owner even when the panel is on the opposite endpoint. Removing generated mirror text is insufficient. | [Dependency reconciliation](https://github.com/bobs-org/bob-cli/blob/68dee6e1f280f235971d55ee915ce46e82902b29/docs/task-dependencies.md#4-reconciliation-the-hooks); [Blocks contract](https://github.com/bobs-org/bob-cli/blob/68dee6e1f280f235971d55ee915ce46e82902b29/docs/task-dependencies.md#15-the-blocks-stage-navigation-hotkeys) |
| Relations are authored on LINKS and projected into LINKED FROM. Identity is resolved note path plus block ID. Opposite directions are independent; each source has one relation entry per target. | Inspect both endpoints, resolve identities, preserve named edges, and handle conversion that would replace an existing label. | [Relation identity and projection](https://github.com/bobs-org/bob-cli/blob/68dee6e1f280f235971d55ee915ce46e82902b29/docs/task-relations.md#5-identity-and-minting) |
| Links RESULTS already have an informational `⛓ prerequisite` badge. Its helper reads the primary owner's forward dependencies; the tooltip says linking remains inert. | Extend an existing convention. The boolean is insufficient for reverse dependencies, incoming links, counted owners, and conversion effects. | [Identity helper](https://github.com/bobs-org/bob-plugins/blob/bdb85e34dca948c36e547937d45df3caabb5d50a/plugins/bob-navigation-hotkeys/src/304-relation-stage-view.js#L269); [badge rendering](https://github.com/bobs-org/bob-plugins/blob/bdb85e34dca948c36e547937d45df3caabb5d50a/plugins/bob-navigation-hotkeys/src/410-picker-filter-and-render.js#L467) |
| The relation stage already has a consequence strip, directional flipping, marked rows, a label substage, and contextual footer hints. | Extend these surfaces instead of adding another modal family. | [Relation picker](https://github.com/bobs-org/bob-plugins/blob/bdb85e34dca948c36e547937d45df3caabb5d50a/plugins/bob-navigation-hotkeys/src/426-picker-relation-stage.js); [copy helpers](https://github.com/bobs-org/bob-plugins/blob/bdb85e34dca948c36e547937d45df3caabb5d50a/plugins/bob-navigation-hotkeys/src/305-relation-stage-copy.js) |
| Relation writes keep cross-note mirrors as best-effort follow-ups. Reverse dependency writes can commit some target notes and fail others. Closed-note writes lack native editor undo. | Required authored removals cannot be optional mirror updates. Cross-note undo is part of the scope. | [Relation writers](https://github.com/bobs-org/bob-cli/blob/68dee6e1f280f235971d55ee915ce46e82902b29/docs/task-relations.md#8-immediate-writers); [Blocks writes and undo](https://github.com/bobs-org/bob-cli/blob/68dee6e1f280f235971d55ee915ce46e82902b29/docs/task-dependencies.md#156-one-gesture-writes-and-undo) |
| Capture stages dependencies before relations, not necessarily in textual modifier order. | A mixed `&B ~B` request must not become “plain link wins” merely because of implementation order. | [Dependency-only planner](https://github.com/bobs-org/bob-cli/blob/68dee6e1f280f235971d55ee915ce46e82902b29/src/native/capture/dependencies.rs#L3415); [relation planning order](https://github.com/bobs-org/bob-cli/blob/68dee6e1f280f235971d55ee915ce46e82902b29/src/native/capture/relations.rs#L151) |
| Missing DEPENDS ON plus a surviving field is interpreted as a legacy dependency to adopt. | Removing the last dependency line without clearing the corresponding field can resurrect the edge. | [R1–R10 rules](https://github.com/bobs-org/bob-cli/blob/68dee6e1f280f235971d55ee915ce46e82902b29/docs/task-dependencies.md#42-the-dependency-set) |
| Text mentions are a separate incoming kind. Dependencies suppress their projection; labelled relations survive alongside dependencies. | Never remove prose links as if they were plain relations; preserve mention precedence. | [Mention conformance test](https://github.com/bobs-org/bob-cli/blob/68dee6e1f280f235971d55ee915ce46e82902b29/tests/cli/task_status_hooks/relations.rs#L1220) |

**Adjustments to the requested requirements.** These are deliberate changes or clarifications, not claims that the original wording specifies every case.

1. **Apply exclusion to the unordered pair, while keeping edges directed.** “Remove from the current task” is too narrow. If B's LINKS points to A, adding A → B as a dependency must remove B's plain relation to A. Likewise, adding A's plain relation to B must remove B → A if that dependency exists. Name the task whose blocking state changes.
2. **Use “plain link” in the product.** Internally, this means a parsed LINKS entry with no normalized label. An aliased link that the parser interprets as labelled is not automatically plain.
3. **Preserve labelled relations, task-text mentions, and other link kinds.** This rule concerns neither Pomodoro Task Links nor arbitrary wikilinks. It does not remove inherited project blocking or transitive dependency paths: those are not the explicit A–B edge being edited.
4. **Define the achievable guarantee.** Supported writes must finish without the conflicting pair. Hand edits, external editors, sync, old clients, and protected historical notes can still introduce contradictory Markdown. Bob must detect it, present one effective relationship policy, and repair safely; arbitrary files cannot be made incapable of containing invalid text.
5. **Use dependency precedence only when intent is unknown.** A deliberate “Make plain link” operation wins over dependencies. Reconciliation of an ambiguous existing conflict retains the dependency and removes only a safely editable unlabelled redundancy. Never guess the latest intent from file modification times.
6. **Make shortcuts desired-state commands.** `Ctrl+B` means make a dependency; `Ctrl+L` means make a plain link. Repeating one must not flip the state back. Existing Enter toggles can remain familiar.
7. **Include cross-note conversion and undo in acceptance.** Merely adding key handlers leaves a correctness gap.

**The exact rule.** Let `D(A,B)` mean A explicitly depends on B, and `P(A,B)` mean A has an unlabelled LINKS entry to B. A nonempty labelled relation is independent of this exclusion.

```text
Forbidden pair:
    (D(A,B) OR D(B,A)) AND (P(A,B) OR P(B,A))

Allowed alongside either family:
    labelled relations, subject to the existing one-entry-per-direction rule
```

The rule is structural: a stored dependency to an already completed prerequisite is still a dependency, although it no longer blocks execution. Do not key exclusion on today's Blocked status. Conversely, Blocked status alone does not prove a direct dependency on the selected candidate.

| Requested operation | Required change | Retained behavior |
| --- | --- | --- |
| Ensure `D(A,B)` | Remove `P(A,B)` and `P(B,A)`; ensure `D(A,B)` | Keep labels and unrelated dependencies. Do not silently reverse `D(B,A)`; normal cycle guards still apply. |
| Ensure `P(A,B)` | Remove `D(A,B)` and `D(B,A)`; ensure `P(A,B)` | Keep the opposite plain relation and unrelated edges; handle the same-direction label collision below. |
| Add/relabel a nonempty label | Apply existing labelled-relation behavior | Dependencies remain; configured label effects keep their explicit-commit semantics. |
| Relabel to empty | Treat as ensure `P(A,B)`, including dependency removal | Preserve unrelated entries and prose. |
| Remove dependency | Remove that dependency only | Do not create a plain link automatically. |
| Unlink plain relation | Remove that directed relation only | Do not create a dependency automatically. |

The label collision deserves explicit handling. Bob cannot store both `A —inspired by→ B` and plain `A → B` on A's LINKS line. When `Ctrl+L` would replace that label, open the existing relation-label field with the proposed empty value and the consequence `Replace “inspired by” with a plain link · remove dependency`. Enter explicitly accepts that replacement; Escape preserves everything. This is an exceptional visible relabel, not silent deletion. Opposite-direction labels stay intact. When `Ctrl+B` is used on a labelled relation, add the dependency and show `Keeps “inspired by”`; this is addition, not replacement of the label.

If a corrupted pair has dependencies in both directions, making a plain link removes both and reports both removals. Adding a dependency does not repair an unrelated cycle by deleting some other edge.

**Panel interaction and direction.** Keep the four existing entry points. Here A is the task whose panel is open and B is the selected row. Make this table shared conformance data.

| Panel on A | Primary action on absent B | Alternate action | Alternate result |
| --- | --- | --- | --- |
| Links to | Enter: A links to B | `Ctrl+B`: Make prerequisite | `D(A,B)` |
| Linked from | Enter: B links to A | `Ctrl+B`: Make dependent | `D(B,A)` |
| Depends on | Enter: A depends on B | `Ctrl+L`: Make plain link | `P(A,B)` |
| Blocks | Enter: B depends on A | `Ctrl+L`: Make plain link here | `P(B,A)` |

These mappings preserve the authored arrow. A visible sentence should use names: `Prepare launch will depend on Security review` or `Release notes will depend on Prepare launch`. Do not rely on an unlabeled arrow or an ambiguous “blocks” badge.

On CURRENT, Enter keeps its removal behavior; the alternate action converts. On RESULTS, the alternate action creates its desired kind directly, without first creating the ordinary panel kind. An already-present desired dependency is an idempotent no-op, except that it still removes a conflicting plain link. A duplicate plain add must likewise normalize an invalid pair before reporting unchanged.

For Tab-marked batches, the alternate command means **set all marked pairs to this kind**, not “replay each ordinary toggle in another panel.” Before applying such a batch, change the previews to explicit desired actions and show aggregate consequences; Enter then applies the prepared batch. This extra review is specific to changing a marked batch's action kind. A single highlighted row remains a direct alternate action. Counted-owner sessions use the same desired-state plan for every pair and show counts such as `3 tasks will depend on Security review`. Do not infer the whole batch state from the primary owner. Conflicting requests within a batch refuse before any write.

Key handlers must be modal-scoped, work from the task filter, and consume handled events so `Ctrl+B` cannot bold the editor behind the panel. Require actual Control, not the platform “Mod” alias. Ignore repeats and composition events; prevent duplicate submission while writing. Do not intercept these chords inside unrelated editors, the block-ID prompt, or the relation-label field. Preserve `Ctrl+Enter`, direction flip, and Escape/q/Ctrl+[ behavior. Pointer buttons call the same commands.

Do not switch panel type merely because the chord was pressed. Successful single-row edits can close as existing Enter edits do. On validation failure, keep the query and target identity, explain the refusal, and refresh stale state without committing a different row.

**Visual design: calm rows, explicit consequences.** Reuse the current panel chrome, CURRENT/RESULTS groups, status colors, type scale, and consequence strip. Put the title first, note context second, and one quiet relationship badge at the right. The badge describes the pair relative to this panel's owner, independently of the candidate's own status.

| Pair fact | Suggested copy |
| --- | --- |
| A depends on B | `Prerequisite` |
| B depends on A | `Depends on this` |
| A has a plain link to B | `Linked to` |
| B has a plain link to A | `Links here` |
| Both plain directions exist | `Linked both ways` |
| Labelled relation | Existing label pill, with direction-aware wording |
| Incomplete relationship scan | `Checking connection…`, rather than falsely claiming no relationship |
| Existing invalid pair | `Dependency + plain link`, restrained warning treatment, clear repair action |

CURRENT should still mean what this panel owns; other-kind badges provide context in RESULTS. Annotate CURRENT too, so old conflicts and labelled-plus-dependency pairs remain understandable.

Illustrative layouts, not screenshots of the running product:

```text
Links to · Prepare launch

Filter tasks                                  security

RESULTS
  Security review                         Prerequisite
  platform · security-review

Enter replaces the dependency with a plain link.
Prepare launch will be Ready; it will not be added to Today.

[ Make plain link  ↵ ]  [ Keep prerequisite  Ctrl+B ]
Ctrl+Enter label · Tab mark · Esc back
```

```text
Depends on · Prepare launch

Filter tasks                                  security

RESULTS
  Security review                            Links here
  platform · security-review

Prepare launch will wait for Security review.
Removes the plain link from Security review to this task.

[ Make prerequisite  ↵ ]  [ Make plain link  Ctrl+L ]
Tab mark · Esc back
```

Status sentences must come from the planned result. If another prerequisite or project hold remains, say `Still blocked by …`; never promise Ready merely because one edge disappears. For a project dependency, summarize the actual affected-resident count. Include removal of live Pomodoro links when applicable. For a completed prerequisite, call the edge a dependency and explain that it is already satisfied instead of saying “will wait.”

Use neutral link/chain icons and existing status hues. Color must not be the sole distinction; reserve warning color for invalid state or an actual caveat. Truncate long titles visually but retain full accessible names. Keep the query and active row stable during refresh, avoiding animated resorting while choosing.

Put clickable actions in the footer, outside listbox options. WAI-ARIA's listbox pattern does not support interactive buttons nested inside an option; focus and selection are also distinct. An external action bar fits better than adding buttons inside every row. [W3C listbox pattern](https://www.w3.org/WAI/ARIA/apg/patterns/listbox/)

Expose shortcuts on controls, announce successful conversion through the polite live region, and keep the focused option visible. W3C's action-list example supports these practices while requiring real assistive-technology testing rather than treating example code as production-ready. [W3C action-list example](https://www.w3.org/WAI/ARIA/apg/patterns/listbox/examples/listbox-rearrangeable/)

**The implementation boundary.** Add a pure relationship-transition planner above the existing dependency and relation line planners. Inputs are resolved endpoints, desired kind and direction, both endpoint snapshots, and explicit operation intent. Outputs include authored edits, derived-field changes, dependency consequences, mirror updates, refusal reasons, and presentation data. Rust and JavaScript should share conformance vectors, following Bob's dual-engine pattern. Obsidian must continue using live editor buffers rather than invoking a CLI writer against potentially stale disk contents.

A representative plan has `ensure_dependency` or `ensure_plain_relation`, endpoint identities, exact removed edges, touched-note preimages, final-state validation, and a consequence summary. These are illustrative internal API names, not proposed public CLI subcommands.

1. Resolve both identities through existing link resolution. Prefer open buffers, including unsaved edits. Check ambiguity, duplicate block IDs, malformed managed lines, writability, and stable row identity. Completion and preview mint nothing.
2. Collect both authored DEPENDS ON sets and both authored LINKS sets. BLOCKS and LINKED FROM are projections, never deletion authority. Missing or disabled mirrors do not mean an edge is absent.
3. Compute the final relationship state. Remove only conflicting plain entries or direct dependencies. Preserve unrelated entries, labels, ordering, prose, line endings, and final newline. Fold ID minting into the plan.
4. Validate the final graph, including implicit project edges and all batch pairs. Dependency candidates must meet dependency eligibility even when selected from the broader Links pool. Closed/archive relation candidates must not bypass those rules.
5. Compose field updates, lane/status effects, promotion/recovery, freshness, and live Pomodoro cleanup through existing semantic helpers. A conversion that changes dependencies follows dependency-edit freshness rules; a pure relation edit remains unstamped. Do not synthesize Done, re-fire label effects, or automatically link an unblocked task into Today.
6. Commit through a conversion-aware coordinator, refresh projections, and return one result. The same planned final state drives preview and outcome copy.

Clear `[dependsOn::]` consistently when removing dependency links, especially the last one. Otherwise R2 can re-adopt the removed edge. Do not indiscriminately strip a target's `[id::]`; other dependents may use it.

Policy coverage includes Obsidian's forward/reverse dependency APIs, Links/Linked-from add and relabel, marked/count-based operations, and Rust capture's `&`, `*`, `~`, `~~`, and empty-label paths. Audit other writers that introduce, move, or relabel edges, including merge/reversal behavior, for a final-state check. Moves that merely rebase stable identities should preserve the invariant without becoming new edges. Hand-edit handlers and reconcile provide repair; hiding labels or disabling mirrors must not disable enforcement.

Reject a capture item simultaneously requesting a dependency and plain relation for the same resolved pair: `Choose a dependency (&) or a plain link (~) for Security review`. Permit both when the relation is labelled. Separate capture items retain sequential semantics: later explicit intent wins against earlier staged state, with preview/results reflecting the final state. This avoids an accidental winner based on internal planner ordering.

The [capture batch planner](https://github.com/bobs-org/bob-cli/blob/68dee6e1f280f235971d55ee915ce46e82902b29/src/native/capture/batch.rs) already supplies staged overlays and read guards. Reuse it rather than building a second Rust write pipeline. Extend read guards to every input used for pair and cycle assessment, not just files written.

**Cross-note commits, failure, and undo.** Obsidian documents `Vault.process()` as protection for one file's read/modify/write and requires preimage comparison after asynchronous work. It is not a documented transaction over several notes. Checking all notes followed by several `process()` calls does not provide global atomicity. [Obsidian Vault documentation](https://docs.obsidian.md/Plugins/Vault)

For one note, compose authored lines, fields, and applicable local effects into one annotated editor transaction. For multiple notes, use an operation record containing affected identities, preimages/postimages, and progress, with guarded compensation and recovery. Reuse suitable existing infrastructure after checking its guarantees; the current relation follow-up API is insufficient.

Required authored removals must complete before publishing the new relationship. If addition fails, restore removals only when current bytes match this operation's expected postimage. Never overwrite concurrent edits during rollback. Do not report success until the committed authored state satisfies the rule. A crash or compensation conflict needs an explicit recoverable operation state, not a success toast followed by invisible repair. Avoid painting an intermediate “no relationship” state as completed.

This is a recoverable multi-note operation, not a guarantee that every observer can never see intermediate bytes. Independent editors and sync remain outside a local transaction. Derived mirrors and existing downstream reconciliation work can remain recoverable follow-ups; required authored removal cannot. Include incomplete projection or cleanup honestly in results.

Provide a guarded operation-level Undo restoring all actual authored changes and associated recorded effects. For participating open editors, annotate transactions with the operation ID so native Undo/Redo can route the relationship change coherently; independently undoing one endpoint can recreate the forbidden state. Closed-note edits need the operation receipt despite having no editor history. If coherent native cross-note undo is not yet feasible, resolve that implementation gate rather than promising one-step undo that does not exist. A stale Undo preserves later edits and explains why full restoration is unsafe.

Not every link add needs a heavy transaction. Keep the cheap path when no conflicting authored relationship is removed; use the coordinator when conversion actually spans authored state. No-ops remain byte-identical with no history entry or freshness stamp.

**Existing data and hand edits.** Use a dependency-preserving repair rule rather than “last edited note wins.” Without explicit operation intent, two conflicting lines cannot reliably reveal the desired winner. Dropping a dependency could make unfinished work actionable.

Before rollout, inventory conflicts by resolved pair: writable unlabelled entries, protected history, malformed/ambiguous sources, and duplicates. Review a concrete dry-run diff; live-vault counts were not measured here. Normalize clear writable conflicts by keeping dependencies and removing only redundant plain relations. Never replay effects, stamp freshness, or change lanes merely for this cleanup. Repair mirrors afterward and verify a second pass is a no-op.

For ongoing hand edits/imports, use the same deterministic repair at the settled-edit/reconcile boundary, with quiet-period and preimage protection. The live projection can suppress redundant plain edges while exposing a conflict indicator, so panels do not advertise two valid kinds simultaneously. Do not silently hide unresolved conflicts without diagnostics.

This deliberately adds a narrow exception to today's rule that reconcile never edits authored LINKS. Restrict it to unambiguously resolved, unlabelled duplicate-pair entries; it must not become general rewriting of authored relations. [Current reconciliation ownership](https://github.com/bobs-org/bob-cli/blob/68dee6e1f280f235971d55ee915ce46e82902b29/docs/task-relations.md#7-reconciliation)

Protected `done/` and previous-daily sources are a current policy boundary. Do not broaden routine history writes for this feature. If an operation requires removing a protected authored edge, refuse before mutation and name its source. Existing protected conflicts remain diagnosed historical exceptions; a separate reviewed migration could handle them if vault-wide structural cleanup is desired. Unresolved or malformed text also must not be repaired by guessing. These limitations are why “impossible” needs the clarified scope.

**Where to implement and verify.** Work is moderate-to-large, concentrated in semantic composition, reverse writes, and undo; badges and chords are relatively small. The following is an implementation breakdown for decision-making, not a claim that production behavior has been changed.

| Area | Starting points | Completion evidence |
| --- | --- | --- |
| Pair model and vectors | `src/native/task_relations/{parse,plan,resolve}.rs`, `src/native/task_dependencies/`; JS `080-dependency-identity.js`, `086-relation-line-plan.js` | Equivalent desired-state cases in Rust/JS. |
| Capture | `src/native/capture/{dependencies,relations,blocked_tasks,batch}.rs`, completion/preview output | All sigils agree; contradictory items fail before writing; dry-run and apply agree. |
| Obsidian writes | `580-plugin-properties-and-dependency-edit.js`, `594-plugin-relation-edit.js`, reverse Blocks writers | Required authored edits coordinated; failure and Undo verified. |
| Pair-aware rows | `300-dependency-stage.js`, `304-relation-stage-view.js`, `427-relation-stage-plugin.js`, `410-picker-filter-and-render.js` | Both directions, CURRENT/RESULTS, fresh snapshots. |
| Interaction/copy | `426-picker-relation-stage.js`, `305-relation-stage-copy.js`, `450-picker-keydown.js`, dependency-stage equivalents | Direction mapping, marks, labels, disabled reasons, pointer/keyboard parity. |
| Repair/lifecycle | `src/native/task_status_hooks/{relations,sync}.rs`, dependency projection, hand-edit handlers | Deterministic repair, no label loss, no re-adoption or effect replay. |
| Documentation/rollout | Dependency/relation contracts and plugin docs | Conversion exception and historical limits explicit; compatible capabilities checked. |

If capture JSON gains conversion summaries, keep them additive where possible and check consumers. Bob Mac Capture should render Bob's computed preview, not implement its own rule. Its implementation was not inspected for this report; audit it if that contract changes. This feature does not require redesigning the Mac interface.

Tests should exercise meaning and failure, not just the key event:

- All four panel directions; plain edges in the same, reverse, and both directions.
- No edge, dependency, plain relation, labelled relation, labelled-plus-dependency, invalid state, repeated desired-state actions, and zero-byte no-ops.
- Same/cross-note endpoints, unsaved buffers, source/target above and below each other, shared-note batch pairs, CRLF and final newline.
- Direct, transitive, and project-induced cycle refusal without deleting the original plain link.
- Removing last versus one-of-several dependencies, future schedule/project holds, project residents, Pomodoro cleanup, and no automatic successor linking.
- Empty-label conversion, label collisions, opposite labels, prose mentions, mirrors disabled, and no replay of cancellation/completion/merge effects.
- Stale snapshots, incomplete indexes, duplicate IDs, broken links, cancelled ID prompts, protected history, failure after each authored step, crash recovery, stale Undo/Redo.
- Mixed capture modifiers and sequential items; both construction paths; reconcile idempotence and R2 re-adoption prevention.
- Eligibility: a closed/archive/Event Task in Links does not automatically become a legal dependency candidate. Existing closed prerequisites remain removable/convertible subject to writable-owner and identity rules.
- Tab/count batches, search generation changes, repeats, IME, Escape/q/Ctrl+[, and no Ctrl+B leakage into bold.
- Light/dark themes, long titles, narrow windows, keyboard-only use, visible focus, and actual assistive-technology testing.

No new implementation or live Obsidian usability test was run. Existing code/tests were inspected, not treated as proof of proposed semantics. In particular, the inspected mention test uses a **labelled** relation: it supports preserving labelled coexistence, not an assertion that an unlabelled conversion test already exists.

**Alternatives considered.** Hiding duplicate chips leaves contradictory authored data. Refusing every conflicting add makes a simple conversion a manual multi-step chore. Confirming every conversion unnecessarily interrupts routine use; consequence copy and coherent Undo serve the common case better. A single global Related/Dependency enum erases existing labelled and directional semantics and demands a larger migration. A universal relationship panel could eventually help, but this feature does not require one.

**Recommended solution.** Proceed with pair-wide exclusion between direct dependencies and unlabelled relations, preserving direction and independent labelled meaning. Add `Ctrl+B` for dependencies from relation panels and `Ctrl+L` for plain links from dependency panels, with name-based consequences, quiet reciprocal-state badges, and shared pointer actions. Build on one desired-state transition contract with final-graph validation, guarded multi-note conversion, and coherent Undo. Reject contradictory capture intent, normalize clear external conflicts in favor of dependencies, and diagnose protected or ambiguous history. This delivers the requested simplicity without silently losing labels, unblocking the wrong task, or promising stronger filesystem guarantees than Bob can enforce.
