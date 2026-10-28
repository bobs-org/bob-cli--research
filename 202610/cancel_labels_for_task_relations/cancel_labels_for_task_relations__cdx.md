# Relation-driven cancellation: an explicit “Link & cancel” action

Independent research by **cdx**, 2026-10-28. Scope: design and implementation research; no product, vault, or chezmoi settings were changed. No other swarm research reports, findings, or transcripts were consulted.

**Recommendation:** implement this, with a narrow meaning: committing a newly added or materially relabelled, configured relation performs a visible **Link & cancel** action on its actual source. Do not make the presence of a relation an ongoing cancellation rule. Start with `duplicate of` and `superseded by` in Bryan’s chezmoi configuration, leaving the application default empty.

The idea is useful: one decision records why a task is obsolete and retires its planned work. The main danger is that cancellation has more consequences than changing a checkbox. In particular, it can release dependent tasks without transferring their dependencies to the replacement. The feature should expose that consequence and preserve the existing cancellation lifecycle.

## What the current system establishes

The findings below come from local source and contracts at the revisions listed under Evidence. They are observations, distinct from the proposals that follow.

1. **Relations are explicitly inert today.** `docs/task-relations.md` §§1–2 says a relation never changes status, freshness, scheduling, priority, or review position. The same claim appears in the glossary, plugin consequence copy, comments, and regression tests. This feature changes a published behavioral promise; it is not merely adding two strings to configuration. [E1, E6]

2. **Direction is structural.** The source owns the authored `🪢 **LINKS:**` entry. `🪢 **LINKED FROM:**` is a generated mirror. Forward `~` and Obsidian Links to write the current task’s outgoing edge; reverse `~~` and Linked from write another task’s outgoing edge. The inverse display phrases are presentation only. In particular, `supersedes` displayed on the target is not a second trigger label. [E1, E3]

3. **There is an established label identity.** `relation_label_key` collapses whitespace, strips one trailing colon, and applies Unicode lowercase. Writers separately validate the label grammar and 40-character limit. Use these rules; introducing substring matching, a regex engine, or a second case-folding scheme would cause inconsistent destructive behavior. [E2]

4. **Configuration currently exposes only relation mirrors.** Rust’s `RelationsConfig` contains `linked_from_lines`. Navigation reads that setting directly from Bob’s YAML, with a metadata-based cache. Bryan’s actual source file is `chezmoi:home/dot_config/bob/config.yml`; it currently has no `relations` block. It sets `timezone: America/New_York`, which matters for cancellation dates and “today.” [E2, E10]

5. **Normal cancellation is a lifecycle operation.** Navigation’s `planTaskCancelBatch` checks selected task preimages, skips already closed tasks, refuses recurring tasks, writes `[-]` and `[cancelled:: YYYY-MM-DD]`, and can insert a first-child `❌ **CANCEL LOG**`. Its orchestration prunes today’s open Pomodoro links and calls the cycler’s `recoverBlockedDependents`. Cancellation does not produce the Done-only successor offers. [E4, E8]

6. **Today’s cleanup has two existing implementations with different details.** The immediate plugin uses `planDeferredPomodoroLinkCleanup`: dedicated link bullets are removed with their subtrees; mixed prose loses the matching live link token; struck links are skipped; emptied open entries can disappear. Rust reconcile’s cancellation rule removes the entire containing list-item subtree, including mixed prose and struck links. Both scope deletion to open Pomodoros, preserve closed Pomodoros and other dates, and resolve task identity rather than matching a block-id substring. The hooks documentation contains these distinctions, although some surrounding wording suggests stronger parity than the implementations provide. [E4, E7]

7. **Existing write guarantees are not interchangeable.** Capture composes relation changes in `CaptureBatchPlanner`, verifies disk preimages, stages temporary files/backups, and rolls back ordinary write failures. Navigation’s relation writer commits source notes and then performs best-effort mirror follow-ups. Normal navigation cancellation can commit the task and then report a failed separate daily-note prune. None of these facts establishes a universal cross-file undo or crash-atomic transaction. [E3–E5]

8. **A cancelled prerequisite stops blocking.** The dependency contract treats `CANCELLED` as nonblocking, and navigation cancellation invokes recovery. `A duplicate of B` does not redirect tasks depending on A to depend on B. This is the most consequential product tradeoff. [E8]

9. **Mac Capture should remain a thin client.** Bob supplies grammar, candidates, previews, and writes. The app already has relation-label cards, a live source/label/target sentence, and structured capture result presentation. The new behavior belongs in Bob’s planner; Swift should decode and display its consequences. [E9]

10. **Label preferences are not action policy.** Hide/unhide are suggestions-only; one-off `||` use still writes the same relation. Global label rename rewrites historical labels, including archives, in a previewed transaction. None should silently execute cancellation. [E2, E11]

## Is this a good idea?

Yes, provided the feature acts on a deliberate edit rather than interpreting the entire vault as a rule engine. “Duplicate of” conventionally means there should be one active representative. Linear’s explicit duplicate action similarly closes the duplicate as Canceled, although it also moves attachments; Bob should not inherit that merge behavior. [Linear’s triage documentation](https://linear.app/docs/triage).

“Superseded by” is a slightly looser assertion: a newer task may replace only part of the original work. Configuring it is reasonable for Bryan’s personal vocabulary, but it should remain an opt-in policy, with the exact effect shown before commit. Do not automatically add `merged into`, `related to`, inverse phrases, or fuzzy synonyms.

Three costs deserve explicit acceptance:

- **A label becomes partly operational.** A typo may create an inert relation, and a corrected label may now cancel the source. The UI must show the effective action for typed labels as well as suggestions.
- **Cancellation is not substitution.** If “Deploy” depends on old task A, cancelling A because it is superseded by unfinished B may make Deploy Ready. That is existing cancellation behavior, but it may contradict the user’s mental model of replacement.
- **Configuration lives per host.** The same label can have different effects until chezmoi has applied everywhere. This is manageable, but rollout and policy refresh cannot be omitted.

I would not build automatic dependency transfer in this feature. It introduces cycle checks, duplicate edge consolidation, project inheritance, and decisions about which work B actually replaces. Show affected dependents in the preview and provide a way to back out and edit them. Keep relation cancellation distinct from a future explicit “Replace task” or “Merge task” workflow.

| Approach | Strength | Main problem | Decision |
| --- | --- | --- | --- |
| Keep relations inert; manually cancel afterward | Smallest implementation | Two gestures can diverge; cancellation reason is easy to omit | Useful fallback, not the desired default |
| Periodically cancel every task carrying a configured relation | Catches manual Markdown edits | Retroactive cancellation, rename hazards, undo/reopen loops, cross-device surprises | Reject |
| Separate dedicated duplicate/supersede commands | Very explicit semantics | Creates a parallel workflow and bypasses the configurable relation chooser | Consider later as shortcuts into the same action |
| Configured, previewed action on relation commit | Fits existing vocabulary and records the reason | Requires coordinated planner, UI, and lifecycle changes | Recommend |
| General relation automation framework | Extensible | Far more surface than two cancellation labels need | Reject for this scope |

## Adjustments to the requirements

These are intentional changes or clarifications to the original request:

1. **“Automatically trigger” means at a managed commit boundary.** Selecting or hovering a suggestion, typing, dry-run, indexing, raw Markdown edits, configuration changes, and reconciliation do not cancel anything. A supported commit cancels after the user sees its consequence.
2. **“Source” always means the edge’s source.** In Linked from / `~~`, it can be a different task in another note. Copy must name it; “this task” is insufficient there.
3. **“Any task links in the current daily file” is narrowed to normal live planning cleanup.** Preserve completed/cancelled Pomodoro history, other dates, and links outside the planning scope. Reuse the ordinary immediate cancellation semantics, with explicit tests for the reconcile differences above.
4. **Add a cancellation log entry automatically.** The relation supplies the reason, so no mandatory free-text reason prompt is needed. The task remains readable as history.
5. **Use existing cancellation eligibility.** Refuse recurring sources with the existing instruction to use Obsidian Tasks. Exclude project lifecycle anchors (`^prj`) from the first release until cancellation is connected to the complete project lifecycle; retain ordinary inert relations for them. This is a proposed scope limit, not a claim that all existing project cancellation is unsupported.
6. **Do not convert Done to Cancelled or re-cancel a reopened task on a no-op save.** Removing a relation never reopens a task. Explicitly reopening is allowed even while the historical relation remains.
7. **Add a visible commit review for the destructive variant.** In Obsidian, accepting its label opens a small in-card consequence review before `Link & cancel`. Mac Capture already has a draft/submit boundary and should show the equivalent review there. This is one extra stage in the immediate Obsidian path, justified by incomplete cross-file undo today.
8. **Make source cancellation and required daily cleanup one checked operation.** Copying today’s best-effort cancellation orchestration would not fully satisfy the reliability requirement. A result must distinguish completed work, failed work, and derived mirror repair.
9. **Treat dependent release as part of the preview, without transferring or auto-linking dependencies.** Cancellation remains cancellation, not implicit migration of work.

## Proposed configuration and semantics

Add this to `chezmoi:home/dot_config/bob/config.yml` after all consumers support it:

```yaml
relations:
  # Applied by managed add/relabel commits; never scans existing relations.
  cancel_source_labels:
    - duplicate of
    - superseded by
```

Retain the independent `linked_from_lines` setting and its current default. `cancel_source_labels` defaults to `[]` in Bob. A small explicit list is preferable to `actions`, expressions, or a generic status map until another actual action is requested.

Validate the container and each label with the existing writer grammar; normalize with `relation_label_key` and deduplicate keys. For example, `Duplicate   Of:` matches `duplicate of`; `not duplicate of`, `duplicated by`, and `supersedes` do not. Reject malformed policy configuration on add/relabel writes rather than silently selecting a default destructive policy or claiming cancellation while doing nothing. Missing configuration is a valid empty policy; unreadable or malformed existing configuration is an error. Keep unlink and inspection available when possible.

Configured labels should be offered even when their corpus count is zero, respecting hidden state. Do not invent usage counts or promote them as the default selection. The catalog is otherwise usage-derived today, so this requires an explicit configured-label overlay. It should identify configured, zero-use rows without pretending they have appeared in a task.

A typed hidden label and a one-off `||` label still apply the policy. Hiding a label is not disabling cancellation. Disable the action by changing the policy, with an appropriate explanation near label management.

The trigger operates on the **semantic relation delta**:

| Event | Result |
| --- | --- |
| Add S → T with a configured label; S is eligible and open | Write edge, cancel S once, record reason, clean S’s live daily links |
| Relabel an existing edge to a different normalized configured label | Same action, after preview |
| Same edge and same normalized label, including case/spacing-only differences | No cancellation and no new log entry |
| Apply an ordinary label or remove an edge | Relation-only mutation |
| S is already Done or Cancelled | Keep status/date/history; allow ordinary relation editing where writable; show “Already closed” |
| T is Done, Cancelled, or archived but resolves as a task | Its status is shown; T is never changed merely because it is the relation target |
| S is recurring, an unsupported lifecycle anchor, read-only, ambiguous, or missing | Refuse the compound action before writing; explain why |
| S = T, or T cannot resolve as a task | Existing relation refusal; no cancellation |
| Change YAML, import notes, rebuild mirrors, run reconcile | No new cancellation |
| Global `relations rename`, including rename into a configured label | Text-only rename; no cancellation |
| Explicitly reopen S, then reconcile or save unchanged relation | S stays open unless another independent rule blocks it |
| Later explicitly add/relabel another configured edge on reopened S | A new visible cancellation action is possible |

If several new edges cancel the same source in one batch, cancel and clean it once, with one log entry listing the triggering relations in a deterministic order. Do not cascade to targets, traverse duplicate chains, merge task content, move children, or infer a canonical surviving task. Preserve ordinary non-destructive relation cycles. A compound draft should refuse contradictory requests to both complete/start/link and cancel the same task rather than letting item order decide its final status. Evaluate cancellation sets against the complete batch before producing the final preview.

A cancelled task could read:

```markdown
- [-] #task Repair the old importer [cancelled:: 2026-10-28] ^old-importer
  - ❌ **CANCEL LOG**
    - *2026-10-28* — Superseded by [[engineering#^new-importer]]
  - 🪢 **LINKS:** superseded by [[engineering#^new-importer]]
```

Use the existing log formatter and indentation/field ordering rather than treating this sketch as a new Markdown grammar. The structured edge remains authoritative relation history; the log explains the cancellation event. Ordinary removal or relabelling does not rewrite that event.

Label rename remains separate from the chezmoi policy: `duplicate of` → `duplicates` should warn that the old configured trigger will not follow the rename. Renaming into a configured key should warn about future commits, while preserving current task statuses. Do not rewrite a different repository or derive action aliases from the preferences journal behind the user’s back.

## Interaction design

The design should feel like the existing relation card gaining a clearly named consequence. Use the current typography, spacing, status icon, and subdued pill style. Keep the relation arrow neutral; use the established cancellation color only on the consequence badge and action. The badge must contain text as well as color. This follows the W3C requirement that meaningful information not rely on color alone. [W3C, Use of Color](https://www.w3.org/WAI/WCAG22/Understanding/use-of-color.html).

### Choosing the label

Both catalog and typed rows show a compact right-aligned `− Cancels source` badge for configured labels. Once actual task identities/statuses are known, the footer gives the real outcome: `Cancels “Repair the old importer”`, `Already closed · link only`, or a precise refusal. Never show a cancellation badge merely because the query approximately matches an enabled string.

Keep the current local navigation model: selected key, not row index; Ctrl+N/P move the highlight without editing the query; Tab accepts/completes; Ctrl+D hides what Return would use; Ctrl+H reveals hidden labels. No subprocess should run merely because the highlight moved. The loaded catalog can carry policy metadata; refresh the actual effect preview at commit preparation.

### Reviewing the effect

For an effectful Obsidian label, accepting the choice leads to a small review inside the same card. It can reuse the existing cancel-reason stage with a generated, editable optional note. The relationship itself provides the required reason. Normal inert labels retain their existing fast commit path.

Illustrative layout, using existing components rather than a new full-screen modal:

```text
🪢 Relation

Repair the old importer  — superseded by →  Build the new importer

− Cancel “Repair the old importer”
  Remove 2 live links from today’s Pomodoros
  1 dependent becomes Ready · dependencies are not transferred

[ Back ]                              [ Link & cancel ↵ ]
```

The sketch’s counts are illustrative; production values come from the plan. Show zero removals as “No live links today” when useful. If dependency impact cannot be assessed, say it is unavailable; do not render zero. The review must not silently truncate a batch to the first source: show the affected source count, expandable names, exclusions, and total removals. Refuse the operation if an ineligible member would make the announced batch inaccurate.

For reverse relations, the sentence remains **source → target**, and the named cancellation follows that same direction. The current task can stay open while a selected task is cancelled elsewhere. This should be obvious without understanding `~` versus `~~`.

Use `Back`, `Keep open`, and `Link & cancel`; avoid two different meanings of “Cancel” on adjacent buttons. Escape leaves the compound action unwritten. No timer, tooltip-only explanation, or animation should be required to understand the effect. Provide accessible names and announce changes in the consequence text without stealing keyboard focus.

Mac Capture accepts a label into its draft first. Bob’s dry-run should show source cancellation and ledger cleanup in the existing preview, and the final action should explicitly read `Capture & cancel 1 task` when applicable. Do not change label acceptance into an immediate vault write. A stale preview is refreshed before submission.

The preference for a clear preview and a real recovery path is consistent with GNOME’s guidance on destructive actions and specific action verbs. Cross-note Ctrl+Z is not currently a whole-action Undo, so the proposed in-card review supplies an explicit confirmation boundary without stacking a second modal. [GNOME dialog guidance](https://developer.gnome.org/hig/patterns/feedback/dialogs.html).

### After success and recovery

Show one composed result: `Linked & cancelled “Repair the old importer” · 2 live links removed`. Include actual dependent recoveries and any mirror repair warning. Do not show a generic relation-success toast followed by an unrelated cancellation toast.

Preserve a single source-note undo group for the relation, status, date, and log. Be honest that undoing that note does not restore a separate daily note. Do not label a “Reopen source” action as “Undo.” Reopening should use normal status handling and keep the historical relation; it must never immediately trigger cancellation again.

A complete, guarded cross-file Undo would be valuable later, but I would not make a new general undo framework a prerequisite. If one is added, it must restore ledger edits as well as source edits, check postimages before reversing, and re-evaluate derived dependency state. Replacing entire notes after intervening edits is not acceptable recovery.

A review-walk commit advances exactly once only if the actual cancelled source is the landed row and the existing walk policy allows it. Cancelling some other source from an incoming-relation card does not advance the current target. Mirror repair and raw text editing never advance the walk.

## Implementation architecture

### Separate policy, effect planning, and writing

Use three small layers:

1. **Policy:** normalized label → `none | cancel_source`, plus configuration validity/revision.
2. **Pure effect plan:** resolved semantic edge changes and current task snapshots → source transitions, log edits, daily cleanup, eligibility refusals, and impact summary.
3. **Existing writers:** apply the resulting per-note postimages with their editor/disk guards; then refresh derived views and dependency recovery.

Do not call the current relation writer, wait for it to succeed, then call the current cancel UI handler. Both assume ownership of notices, modal closure, undo, line positions, and follow-up writes. Compose pure plans before applying any changes.

Rust should own capture semantics and the structured Mac preview. A JavaScript planner twin is appropriate for Obsidian’s unsaved buffers, following the project’s existing Rust/JS contract-vector pattern. The plugin may read the same Bob config, as it already does for mirrors. It must not flush editors and call a disk-only CLI writer as a shortcut. Shared fixture vectors should prove equivalent normalized policy and effect decisions.

### Concrete seams

| Repository | Existing seam | Proposed responsibility |
| --- | --- | --- |
| bob-cli | `src/native/config/relations.rs` | Strict policy parsing; empty default; normalized key set |
| bob-cli | `src/native/relation_labels/`, `capture_complete/model.rs`, `capture_complete/candidates.rs` | Configured-label overlay and structured action metadata on typed/catalog rows |
| bob-cli | `src/native/capture/relations.rs`, `plan.rs`, `batch.rs`, `commit.rs` | Detect added/relabelled edges, compose cancellation with the staged batch, emit dry-run effects and checked results |
| bob-cli | `src/native/task_status_hooks/structure.rs` and normal cancellation contract | Reuse/extract scoped cleanup carefully; avoid running broad reconciliation as an action side effect |
| bob-plugins | nav `020-config-load-and-tasks.js`, `305-relation-stage-copy.js`, `426/428/429` relation-stage fragments | Policy cache, badge, typed-label effect, inline review, rename warning |
| bob-plugins | nav `594-plugin-relation-edit.js`, `240-cancel-and-lanes.js`, `160-pomodoro-reorder.js` | Compose relation + existing cancellation + daily cleanup against snapshots |
| bob-plugins | nav `510-plugin-link-commit-and-lane.js`, `540/550` cancellation orchestration | Reuse preimage/rollback mechanics with a required-cleanup mode; compose one result and existing recovery |
| bob-mac-capture | `CaptureModels.swift`, `CaptureRelationshipPresentation.swift`, relation card in `CapturePanelView.swift`, `CapturePanelModel.swift`, `BobProcessClient.swift` | Decode effects, render review, guard submission, report success accurately |
| chezmoi | `home/dot_config/bob/config.yml` | Enable only the two requested labels after compatible clients are deployed |

These are seams, not a proposal to grow already large fragments beyond their repository limits. Extract small modules where needed.

### Transaction and identity requirements

Resolve source and target first, using canonical note identity plus block id. Honor existing ambiguity/refusal rules. Do not use titles, cached line numbers alone, or basename-only string substitution. Re-locate after inserted IDs/logs shift lines. When source, target, and daily file are the same note, compose into one postimage and one editor transaction.

Treat the source LINKS edit, cancellation fields/log, and required live daily cleanup as critical. Preflight all critical note snapshots before the first write; use checked writes and conditional rollback on ordinary failures. Reuse the shared navigation commit machinery with an explicit required-daily mode rather than inheriting `pomodoroPruneFailed` as a successful finished operation. A changed daily note should lead to re-planning and review, not silently abandoning cleanup.

Derived LINKED FROM mirrors may remain best-effort where the current contract allows that, because the authoritative edge is durable and reconcile repairs its projection. Do not roll back a valid cancellation because an archived target intentionally has no stored mirror. `linked_from_lines: false` must not disable the action or its ledger cleanup.

A multi-file text operation is not crash-atomic merely because it has rollback code. Keep recovery snapshots, report rollback failures honestly, and test interrupted/partial states. If only some critical writes survive, return a typed partial outcome listing the affected notes; never say “no tasks were updated.” The recommended success contract is all required edits completed, with separate warnings only for derived follow-ups.

Resolve the effective daily date using Bob’s configured calendar, not this machine’s UTC date. A midnight rollover or policy change invalidates an effect preview if its consequences change. If today’s note is absent, report zero links without creating an empty daily note. An unreadable note is not equivalent to an absent note.

### Cleanup parity deserves explicit acceptance tests

For v1, match the **immediate normal Cancel gesture**: remove all matching live occurrences in open Pomodoros, remove dedicated bullets with their child subtrees, retain unrelated text on mixed lines, preserve closed-Pomodoro history, and remove newly empty planning entries using the established rules. Exclude managed relation/dependency lines and resolve ambiguous links conservatively.

Rust capture needs the equivalent scoped planner if an existing helper cannot produce precisely these semantics. Do not simply invoke full `bob task reconcile`: that would perform unrelated vault changes and could apply the broader cancelled-subtree rule described above.

Leave reconciliation’s existing behavior unchanged in this feature. Test and document that a struck cancelled link retained by the immediate gesture can subsequently be removed under an open Pomodoro by reconcile. Do not promise permanent preservation of all struck links, or claim identical cleanup algorithms. A future decision to unify those algorithms should cover ordinary cancellation too, rather than quietly changing only relation-driven cancellation.

### Protocol and compatibility

Suggested additive data includes a catalog `effect: "cancel_source"`, and an actual preview with canonical source/target identities, previous and proposed status, log reason, affected-note/ledger counts, eligibility/refusal reasons, dependency impact, and a policy/preview revision. Names are proposals, not existing fields. Separate static label capability from actual action: a configured label on an already closed source has no new cancellation.

New JSON fields alone are insufficient. An old Mac client could ignore a badge while a newer Bob still cancels. Require acknowledgement of the previewed effect for an effectful capture commit, tied to the effective policy and critical inputs. The UI supplies it after review. A direct CLI caller without it receives a typed “effect review required” response with a preview and a documented retry path; inert captures remain unchanged. This is additional CLI friction, but it prevents invisible destructive behavior for old clients and scripts.

Use positive capability detection before passing any new capture guard argument. The existing Mac client explicitly warns that an old Bob may treat unknown flags as task text; `BobProcessClient.swift` already gates newer pull-in/inbox flags on advertised support. Reuse that pattern, never fallback by removing the effect guard and retrying an effectful mutation. [E9]

Snapshot catalog metadata when opening a card so selection stays responsive, but revalidate policy/effects at commit. If configuration changed, show the changed consequence and require a fresh commit. Tolerant old-server decoding is useful for inert relations; it must not become permission to hide a new destructive action.

## Implementation order and verification

This is more than a plugin-only tweak. I would stage delivery as follows:

1. Specify the semantic delta, source direction, date, eligibility, log, cleanup, failure, and acknowledgement contracts. Keep the global policy default empty.
2. Implement Rust policy and pure effect planning; extend dry-run/completion JSON and capture commit guards. No broad reconciliation trigger.
3. Compose Obsidian source/daily plans and in-card review; preserve existing label keys and close/recovery behavior.
4. Implement Mac decoding, consequence presentation, and guarded submission, with executable-identity capability checks.
5. Add Bryan’s two labels to chezmoi and apply across supported hosts after verifying installed versions. Treat release sequencing as part of shipping the feature.

Update the owning relation/capture/plugin/Mac contracts and regenerate mounted docs through their normal tooling. Existing “relations never change status” assertions should be narrowed to inert relations and passive projection, not deleted wholesale. The audited glossary currently makes the same inert claim; an implementation plan should include the specific authorized memory correction through the memory-write workflow. This report itself changes no accepted memory or decision.

Validation should focus on outcomes, not duplicated implementation details:

- Shared Rust/JS vectors for normalized labels, invalid config, disabled mirrors, zero-use configured suggestions, hidden/one-off labels, typed rows, and rename boundaries.
- Forward and reverse commits, same-note source/target, external selected sources, counted forward sources, supported marked reverse sources, and deduplication of several cancelling edges for one source. Preserve existing refusals for unsupported counted reverse entry points.
- Ready/Next/Pending/Blocked sources, closed-source no-op, recurrence refusal, project-anchor refusal, archived targets, malformed LINKS, duplicate IDs, and task movement while the card is open.
- Cancellation fields and dated log; no freshness stamp, priority/schedule mutation, dependency transfer, child-task cancellation, target cancellation, or automatic successor linking.
- Daily note absent/unreadable; New York midnight; same-file composition; repeated links; mixed prose; dedicated bullet children; closed Pomodoros; struck links; ambiguous basename; fences; CRLF; EOF without newline; empty entry removal.
- An eligible dependent recovers, a dependent with another open prerequisite or future date stays blocked, and the preview does not call unknown impact zero.
- Configuration and target changes between preview and commit, repeated Return, no-op retries, rollback failures, partial write reports, and reconcile repair of intentionally skipped mirrors.
- User navigation changes no query text; Esc writes nothing; typed/configured row badges agree; reverse copy names the cancelled source; batch counts are accurate; normal labels keep their existing speed.
- A reopened source with unchanged historical relation stays open through save/reconcile; deleting a relation does not reopen; global rename never cancels.
- Old/new Bob × old/new Mac behavior, unsupported guards, and a backend refusal when an effectful write has no valid acknowledgement.
- Review walk advances once for the cancelled landing, stays for off-landing sources, and never advances after refusal or a passive mirror update.

Research validation performed: the following existing Node suites passed together against the checked-out plugin build: `test-navigation-hotkeys-cancel-task.cjs`, `test-navigation-hotkeys-cancel-log.cjs`, `test-navigation-relation-writer.cjs`, and `test-navigation-relation-links-stage.cjs`, using `node --test --test-reporter=dot`. This validates the inspected baseline, not the proposed feature. No new implementation, Rust build, Mac build, live-vault mutation, or visual usability test was performed.

Future implementation must run the appropriate Rust checks, plugin build/tests and `bob plugins sync`, and the Mac repository’s required portable/macOS compilation checks; do not mistake Linux-only checks for Swift UI verification. The existing daily release train and contract-break conventions still apply.

## Evidence and limits

Repository revisions inspected:

- **bob-cli:** `e7263d558aa3d9d1037f7f5c7e2831094d7f064b`
- **bob-plugins:** `8baf76398048612cc0ed1c7b7b03537c87056b3b`
- **bob-mac-capture:** `88757e97c4d761e4fbbf4829c1ed6badb7db36af`
- **chezmoi:** `2fc6b190e8feebf3c0d30183e7ad7be5385a999d`

| Ref | Source inspected | What it supports |
| --- | --- | --- |
| E1 | bob-cli `docs/task-relations.md` §§1–12, 16; audited `glossary:task-relation` and `glossary:task-link` | Inert contract, edge direction, mirrors, label rules, relation history, UI vocabulary |
| E2 | bob-cli `src/native/config/relations.rs`; `src/native/task_relations/label.rs`; `src/native/relation_labels/mod.rs`, `rename.rs`; `capture_complete/model.rs`, `candidates.rs` | Current policy surface, normalized keys, catalog and typed rows, inverse phrases |
| E3 | bob-cli `src/native/capture/relations.rs` (`plan_relation_writes`, `apply_linked_from`, unchanged-action guards); `batch.rs`, `commit.rs`; `tests/cli/capture/relations.rs` | Source identity, reverse direction, staged mutation, repeat/no-op behavior, rollback limits |
| E4 | bob-plugins nav `src/240-cancel-and-lanes.js`, `540-plugin-decay-picker-and-cancel.js`, `550-plugin-cancel-and-counted-property.js`, `160-pomodoro-reorder.js` | Normal cancel fields/log/recurrence, immediate pruning, recovery and notice |
| E5 | bob-plugins nav `src/594-plugin-relation-edit.js`, `510-plugin-link-commit-and-lane.js` | Editor-aware relation writes, best-effort mirrors, source batching and daily-prune failure semantics |
| E6 | bob-plugins nav `src/020-config-load-and-tasks.js`, `304-relation-stage-view.js`, `305-relation-stage-copy.js`, `428-picker-relation-label-vocabulary.js`, `429-relation-label-management.js`; relation writer tests | Config caching, current inert copy, label keyboard model, rename preview, undo boundaries |
| E7 | bob-cli `docs/task-status-hooks.md` “Canceled Task References”; `src/native/task_status_hooks/structure.rs` cancellation loop | Authoritative reconcile cleanup scope and subtree semantics |
| E8 | bob-cli `docs/task-status-hooks.md` dependency/recovery sections; `docs/task-dependencies.md` §12; audited `decisions:unblocked-tasks-are-offered` | Cancelled prerequisites do not block; recovery versus successor linking |
| E9 | Mac `Sources/CaptureCore/CaptureModels.swift`, `CaptureRelationshipPresentation.swift`, `BobProcessClient.swift` around the positive capability gates; `Sources/BobMacCapture/CapturePanelView.swift` relation card and `CapturePanelModel.swift`; audited thin-client decision | Existing UI/protocol seams and unknown-flag hazard |
| E10 | chezmoi `home/dot_config/bob/config.yml` | Actual source destination, absent relation policy, configured timezone |
| E11 | Audited `decisions:relation-card-tab-accepts-ctrl-d-hides`, `relation-label-hide-is-suggestions-only`, `relation-label-prefs-live-in-per-host-journal`, `relation-label-rename-rewrites-history`, `answering-advances-the-walk` | Constraints to preserve during implementation |

External sources were consulted independently on 2026-10-28: the linked Linear documentation supplies product precedent; GNOME supplies interaction guidance; W3C supplies the color-accessibility principle. They do not establish Bob’s implementation behavior. Local source and executable baseline tests are the evidence for that.

The report does not measure Bryan’s current number of duplicate/superseded relations or their dependency fan-out; no live vault census was required for this design. The extra review stage, lifecycle-anchor limit, strict critical-write completion, and capability acknowledgement are design judgments. A short usability pass on the actual card should validate the copy and keyboard rhythm before enabling the policy everywhere.

## Recommended solution

Ship **configured relation commit actions**, initially `duplicate of` and `superseded by`, with an empty application default and Bryan’s settings in chezmoi. Mark those labels with **Cancels source**, preview the actual source, live ledger removals, and dependent release, then commit through **Link & cancel**. Compose the relation, normal cancellation fields/log, and required daily cleanup before writing; keep the target and historical relations intact.

Do not make cancellation a reconciled property of relation text. Do not transfer dependencies, auto-link successors, silently close recurring/project-lifecycle tasks, or allow older clients to trigger an effect they cannot display. Preserve fast inert relations, make the destructive variant explicit in the existing card, and keep reopening independent of the historical edge. That is the most intuitive and reliable version of the request, with a restrained visual treatment that fits Bob rather than introducing a separate automation interface.
