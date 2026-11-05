# Task and Pomodoro type agreement: repair the writers, then reconcile conservatively

Independent research by **cdx**, 2026-11-05. This report was prepared without consulting the other swarm researchers or their reports. It evaluates implementation choices; it does not change application code or the live vault.

**Recommendation:** strengthen the existing agreement invariant, fix specific gesture bugs, and add a conservative name-repair pass to `bob task reconcile`. Let task types drive automatic repairs. Add missing components to ordinary open Pomodoros; remove a component only when an observed edit proves its last relevant link left. Do not reconstruct every Pomodoro name from its current task links.

The idea is good, but “always” needs a precise boundary. Closed sessions record history, names can include intentional plans without links, custom containers hold mixed work, and some tasks deliberately have no effective type. Those distinctions materially change what safe reconciliation means.

## Evidence and scope

I inspected these local checkouts:

- `bob-cli` at `01cb7b5c3eb75d7353ef4a57014cc5ada1178bf6`.
- `bob-plugins` at `cfb331ea7f4d9f7413dece935e738a0eaa77e16e`.

I read the task-type, Pomodoro, merged-Pomodoro, and Task Link glossary entries through audited SASE memory reads, plus the component-identity, type-preference-journal, and sticky-lane decisions. I inspected the implementation, its documented contracts, and existing tests. I ran three focused plugin test files and two small in-memory probes. No live-vault measurement or interactive Obsidian testing was performed; the frequency of these failures in Bryan’s actual workflow is therefore unknown. I did not inspect the Mac frontend: this report identifies the bob-side companion command it needs to inherit fixes from.

Source references below link to the inspected commits. They were researched through local checkouts, not by fetching repository files over the web.

## What the system already promises

Bob already has most of the necessary model. An open task’s effective type comes from its explicit `[type:: X]` field (legacy `[theme:: X]` also reads), then the reading-task rule, then the nearest area/project default on its residence/root walk, then the global default. A field is an exception to inheritance; choosing the inherited value clears it. The result can legitimately be absent, including through `off`. Closed tasks have no current type suggestion. Duplicate or malformed fields are repair states, with inheritance used as the fallback. [C1, C2]

Pomodoro names split into normalized `+` components. With a configured vocabulary, matching components are types and the rest are labels. Without one, all components except inventory labels are types. A name with no type components is a **container**, including an unnamed entry. Agreement currently accepts containers and untyped tasks; otherwise the effective task key must match a component of the name. Comparison is by normalized key, not substring, spelling, or slug. [C1, C3]

Existing gestures are intentionally asymmetric:

| User action | Existing intended consequence |
| --- | --- |
| Link or move a task into another typed Pomodoro, ordinary Enter | Keep the task’s type; append missing type components to the destination. |
| Explicit Alt+Enter in a landing picker | Retype the task to the selected destination type, using Set/Clear relative to inheritance. |
| Change a task’s type, or move it to a note with a different inherited type | Relocate the live link; a running session absorbs the new type instead of moving the task out. |
| Name or rename a linked Pomodoro | Retype disagreeing open linked tasks to its chosen type. |
| Move links out of a merged Pomodoro | Shed types that had links before and have none after, with the existing base fallback. |
| Close a merged session | Narrow the closed name to worked types and shed the continuation using before/after link information. |

These rules are implemented by Rust’s `routing.rs` and `merged.rs`, mirrored in Ledger Tools JS with shared vectors. Reusing them is preferable to creating a new type system. Naming should remain an explicit action that can change task types; automatic cleanup should not impersonate that action. [C1, C3, C4, P1]

The current contract specifically says drift from hand edits, defaults/configuration changes, and sync is **flagged and never silently repaired**. `bob plan` adds a `type_mismatch` lint; Obsidian has a corresponding mark. Your proposed fallback is a deliberate change to that policy, not merely a missing call to existing reconciliation. The documentation also contains historical phase language contradicted by later completed sections; implementation and conformance tests should determine what actually ships. [C1, C5]

## Concrete gaps found

### 1. Pomodoro rename uses the wrong landing mode

**Reproduced in the plugin harness.** In `650-plugin-move-commit.js`, entry rename calls:

```javascript
pomodoroBulletMoveTypePlanRows(renameTypeApi, freshPreview, plan.name, {})
```

The helper sets `retype` only when `options.typeMode === "retype"`. Consequently rename requests merge mode. The task-write collector consumes only Set/Clear outcomes, so it ignores the resulting Merge outcome while the headline is renamed anyway. The rename preview makes the same mode mistake and can say all tasks agree when they do not. [P2, P3, P4]

My probe used the existing picker harness plus the production JS routing fragment, with simple normalization shims for the uppercase names in this example. A task inheriting BUILD was linked under BUILD. Renaming the entry to READ produced:

```text
ok: true
landing request: retype = false
landing result: merge, name = "READ + BUILD"
actual daily headline: — READ
task: unchanged, still inherits BUILD
notice: "Renamed Pomodoro #1 to READ · keeps BUILD"
```

This is a deterministic integration bug, not just a race. Pass explicit retype mode for both rename preview and commit, and use the actual routing implementation in the regression test. An existing preview test stubs `planLanding` to return Set/Clear regardless of mode, so it cannot catch this mistake. Preserve the distinction between rename and ordinary link landing.

### 2. “Live link” lookup includes historical links and ignores note identity

**Reproduced at the exported helper seam.** `taskCardTypeLedgerEntries` includes closed entries. `taskCardTypeFindLiveLink(details, blockId)` searches their links without filtering `open`, and matches only the block ID. `planTaskCardTypeLedgerMoves` silently skips when this returns multiple matches. [P5]

Four probe cases gave these results:

| Daily contents for a type edit of `work.md#^x` | Current lookup/planning result |
| --- | --- |
| One closed BUILD entry and one open BUILD entry, both linking `work#^x` | Two matches; relocation planner never called. |
| Open links to `other#^x` and `work#^x` | Two matches; relocation planner never called. |
| Only an open link to `other#^x` | Accepted as the link for the edit of `work#^x`; relocation planner called. |
| Only an open link to `work#^x` | One match; relocation planner called, as expected. |

The probe used a recording relocation stub; it demonstrates selection and suppression, not a complete wrong-note mutation. The downstream risk follows directly: one branch can leave the edited task mismatched, and another can act on an unrelated task’s entry. Repeated note-local IDs are valid, particularly reading-task IDs such as `^ref`.

Task Card field writes continue when there are no planned ledger moves. Note-move/inbox-route relocation uses the same lookup, so this is shared infrastructure to repair, not a one-keymap special case. [P6, P7]

Use `(resolved vault-relative note path, block ID)` identity, today’s open entries, and the canonical dedicated-link grammar. Distinguish “no live occurrence” from “ambiguous target,” “unavailable resolver,” and “multiple live occurrences.” Multiple occurrences of one resolved task should all be checked; ambiguity about which task a link resolves to should be diagnosed.

**Rust also needs the identity correction.** `relocation_apply::find_live_link` correctly filters open Pomodoros but still accepts only `block_id`; a second matching occurrence makes it return `None`. It also excludes embedded links, whereas the Today scanner accepts dedicated plain or embedded links. A new reconciler should not inherit these limitations. [C6, C7]

### 3. Partial writes are an explicit path to drift

**Confirmed by code inspection; no failure injection performed.** Task Card type commits write the task first, then re-read/replan and write the daily note. Failure of the ledger write reports a partial result. Multi-note type edits can also partially succeed. Bullet moves with retyping and Pomodoro renames write the daily editor first, then task-note groups; a failed group reports an incomplete type update. These paths make the fallback useful even after the deterministic bugs are fixed. [P3, P6]

The bob-side `capture-pomodoro-name` companion command likewise writes the headline first, then task retypes; a stale task preimage can be skipped and a later error can leave earlier writes applied. It is worth including in the writer audit even though it is not an Obsidian keymap. [C8]

Do not treat a missing type service or failed plan as a successful no-op when the gesture can change agreement. Preflight all relevant task, ledger, inheritance, and configuration inputs. Compose same-note edits into one editor transaction. For separate notes, use checked writes and guarded rollback/recovery where available; never blindly restore over newer edits. Report any unresolved partial write precisely.

Moving every gesture into a CLI subprocess is not the smallest solution: the plugin can have unsaved editor content and supports mobile. Keep the shared pure model and make its editor-aware adapters reliable. Obsidian’s official Vault documentation recommends `Vault.process` for content-dependent background changes and checking the preimage after asynchronous planning. That protects an individual file; it does not establish a transaction across task notes and a daily editor. [External: Obsidian Vault](https://docs.obsidian.md/Plugins/Vault)

### 4. The existing lint result is insufficient as a repair input

**Confirmed by code inspection.** `today_links` enumerates dedicated link occurrences. `today_tasks` then deduplicates by task identity, keeping the first occurrence. The mismatch lint iterates this deduplicated task list. If a task is linked under matching BUILD first and mismatching READ later, that later mismatch is not independently inspected by this lint path. [C5, C7]

Reconciliation must inspect **each eligible occurrence**, caching task resolution and effective types by identity. It must not use the deduplicated Today display list as its worklist. The current hooks’ broader reference scan is also not a substitute: it collects references from more bullet shapes for status purposes. Reuse the dedicated Task Link parser used by Today/close, excluding prose mentions, deeper descendants, fenced code, dependency/relation lines, struck links, and closed target tasks. Preserve the parser’s treatment of valid markers and embeds. [C7, C9]

## Requirements I would adjust explicitly

1. **Scope agreement to today’s live plan.** Apply to resolved open tasks referenced by dedicated live Task Links under today’s open Pomodoros. Check every occurrence. Do not require backlog tasks to acquire a link, and do not revisit historical sessions when a task’s current type changes. The previous daily note remains read-only for this repair.
2. **Separate type coverage from exact name equality.** Every eligible linked type must be represented, but every existing type component need not currently have a link. That is a coverage invariant, not an exact projection of task links.
3. **Keep the existing custom-container exception.** A label-only or unnamed container remains mixed work. A mixed name such as `BOB + BUILD` is still typed: retain BOB and enforce coverage on the entry. Do not add a new ad-hoc-name flag, syntax, or registry.
4. **Do not invent types for untyped tasks during background repair.** Report missing effective types separately. Existing `off` settings and absent defaults make strict universal typing a distinct product change. If you want every ordinary task typed, configure an ordinary global `plan.default_type` and decide the `off` exception policy separately. Do not guess a type from whichever Pomodoro happens to contain a link.
5. **Preserve exact MEET ownership.** Existing routing protects a whole name that normalizes to MEET. Background repair must not turn it into `MEET + BUILD`, nor silently retype a task to MEET. A mismatch there remains a specific unresolved diagnostic, fixed by an explicit landing/retype action. This is an additional justified exception to your proposed “always.”
6. **Define “always” as a successful-write postcondition plus eventual repair.** Supported managed gestures should preserve agreement on success. Hand edits, sync, unresolvable targets, invalid fields, unsaved buffers, and failed writes can temporarily violate it. The next successful reconcile repairs safe cases and reports remaining exceptions. A warning-free success must not disguise ambiguity or partial completion.

Unconfigured effective types deserve care: the current agreement function accepts a matching name component even if the configured vocabulary classifies that component as a label. Keep this compatibility behavior for repair, while retaining the unconfigured-type warning. Do not silently expand the configured vocabulary. A stricter “only configured types count” rule would be another behavior change. [C3]

## Why unconditional type removal is the wrong default

Consider these two entries:

```markdown
- [ ] () — BUILD + READ
  - [[work#^build-task]]
```

In one history, READ was intentionally planned before a reading task was selected. In another, the user deleted the last READ link by hand. The current bytes are identical. A stateless reconciler cannot distinguish them.

Deleting READ everywhere would erase intentional plans. Keeping it everywhere would retain some stale names. Neither a cache nor an inferred “base” solves that ambiguity reliably. A durable provenance journal or new pinned/derived component metadata could solve it, but that introduces a second authority for names, synchronization rules, and migrations. That cost is disproportionate to this request.

The existing `shed` rule already captures the appropriate compromise: drop a type when it had a link before the operation and has none afterward; preserve labels and types that never had links, and keep a base if all types would otherwise disappear. It applies only to merged names and preserves MEET and single-type entries. [C4]

**Recommended removal rule:** use that before/after evidence in managed gestures and in reconciliation operations that actually consume links in the same run. For pre-existing drift with no trustworthy before-image, add missing types but do not guess which old components to delete. Strict name compaction can be a later explicitly requested action if this conservative behavior proves insufficient.

This is the most significant adjustment to the initial request. Removing unused components is useful tidying; it is not required to satisfy task-to-Pomodoro agreement.

## Implementation design

### One pure repair policy, two adapters

Add a small pure planner next to `routing.rs` and `merged.rs`, with the same JS conformance vectors. Its input should include:

- The entry’s existing name, state, and classified components.
- Ordered eligible link occurrences and resolved effective type facts.
- Resolution/type-health diagnostics, so “unknown” is not mistaken for “none.”
- Optional trustworthy before/after facts for an operation that removed or retyped links.

Its result should be structured: unchanged, renamed with added/removed components and reasons, or unresolved/skipped with a reason. Keep rendering and file writes outside it. Prefer a named intent enum or dedicated rename API over another loosely propagated boolean; the existing rename bug demonstrates the risk of mode defaults.

For an ordinary typed entry:

```text
candidate = original name
if a known operation changed its links:
    candidate = existing conservative shed(candidate, before_types, after_types)
for resolved eligible links in ledger order:
    append its effective type if the normalized key is absent
return candidate and the actual additions/removals
```

Classify exceptions from the original entry. Preserve labels, retained spelling, component order, checkbox, timespan, clock fields, block identity, and all children. Append each new normalized key once, in first-link order. Already agreeing entries must remain byte-identical. Preserve valid unknown-type matching behavior. Respect existing name validity/length limits; diagnose an unrepresentable repair rather than truncate names.

Use `agrees`, type-component classification, normalization, and merge/shed primitives. **Do not call `land` indiscriminately from reconcile:** its MEET path can return task-field Set/Clear, which violates the proposed fallback’s ledger-only responsibility. Likewise, do not invoke a user-facing naming command to apply a derived headline edit: naming is an explicit retyping gesture.

If a task field is malformed or duplicated, conservative reconciliation should report it rather than silently grow a name from an uncertain inherited fallback. For mixed resolved/unresolved input, safe additions for independently resolved tasks can proceed, but suppress destructive shedding for the affected entry. Report these distinctions.

### Integrate into the existing reconciliation transaction

Use `bob task reconcile` itself, with existing dry-run and output modes; no new always-running watcher or command family is needed.

Run the name pass on the **final staged ledger**, after completed/cancelled/blocked-link consumption and empty-entry cleanup. `sync.rs` already has a second link-consumption pass after status composition; the repair belongs after that pass and before guarded application. A scan of the original ledger would add types for tasks removed later in the same run or target shifted lines. Resolve tasks against staged post-images where this run changed them. [C10]

Extend the guarded read-set to every new dependency: effective-type configuration, configured vocabulary/inventory, task content, and all notes visited by default/root inheritance. Reuse loaded snapshots and a resolver cache; avoid one full vault scan per link. Type classification should not depend on journal recency or suggestion visibility. Use existing authoritative display-name rules for newly added components.

Mark headline rewrites as structural so they obey the writer’s quiet-period and stale-input protection. Keep maintenance locking, recovery records, bounded retries, and partial-apply reporting. Existing reconciliation is guarded but is not a true multi-file database transaction; it explicitly cannot see unsaved editor buffers and does not automatically roll back an already partial apply. Do not promise stronger guarantees for this addition. [C11]

Add report rows such as `pomodoro_type_repairs` with entry location, old/new name, added/removed types, and cause. Add explicit unresolved reasons for untyped tasks, ambiguous targets, bad fields, MEET, and limits. Use the same plan for dry-run and apply, clearly distinguishing planned edits from successfully applied ones. Refresh mismatch diagnostics from the repaired post-image; retain diagnostics for skipped cases. The current plan-budget calculation receives original daily content, so report construction needs a deliberate review when adding repair output. [C10]

### Fix the actual gesture paths first

| Surface | Work needed |
| --- | --- |
| Ctrl+Shift+M on a Pomodoro headline: rename | Fix preview and commit to request retyping; cover differing inherited and explicit types. |
| Ctrl+Shift+P → Type, Use default, Ctrl+D | Fix live identity/occurrence discovery; avoid silent no-op on ambiguity or unavailable planning; compose ledger and task edits safely. |
| Ctrl+Shift+M task note move and inbox routing | Use the same corrected resolver, recompute inheritance at destination, and retain the existing checked move transaction. |
| Ctrl+Shift+Enter linking; bullet moves; successor picks | Preserve merge-on-Enter and retype-on-Alt+Enter; check every landing type, source shedding, multi-selection, unresolved targets, and partial writes. |
| Release/unlink, Done/cancel/block, merge/split, close/carry | Apply shedding only with trustworthy before/after evidence; validate the final post-image, not an intermediate one. |
| Capture named links, explicit type markers, task moves, ref-today | Reuse the Rust policy and correct path-qualified identities; exercise the existing staged capture planner. |
| `capture-pomodoro-name` and its clients | Preserve intentional naming/retyping; bring its separate writes under a checked plan and surface stale/partial outcomes. |
| Hand edits, note defaults, parent/root changes, configuration, sync | Fall back to reconcile; no need to intercept every editor keystroke. Managed operations that change inheritance should use the same postcondition. |

Only the first two bug mechanisms above were reproduced; the other rows are an implementation coverage audit, not a claim that every listed keymap is currently broken. Preserve existing task lanes, freshness, review-walk behavior, successor consent, and time accounting.

## Critique and alternatives

| Approach | Assessment |
| --- | --- |
| Keep warning-only behavior | Protects authored names but leaves avoidable manual work and the reproduced bugs. Useful for unsafe exceptions, insufficient as the main solution. |
| Automatically retype tasks to match the ledger | Makes a partial or stale headline edit authoritative over task intent and inherited defaults. Contradicts the requested fallback direction; reject. |
| Automatically relocate all mismatching links | Reorders the plan and can move work out of the context the user chose. Keep it for explicit type edits, not background cleanup. |
| Rebuild each name from its current links | Simple and deterministic but destroys planned empty types and can alter session attribution. Reject as the default. |
| Add provenance/pinned components | Can support exact pruning, but creates persistent synchronization and migration costs. Defer until demonstrated need. |
| Shared writer postconditions plus conservative headline repair | Best fit: addresses real bugs, preserves explicit intent, and adds a bounded fallback without new state. |

An additive fallback can grow running-session names and thereby affect type-based reporting or planned-type counts. That is the consequence of existing merge semantics, not a free cleanup. Preserve clock spans and closed historical names, show the actual change in reconciliation output, and measure repair frequency. If reconciliation repeatedly adds types after supported keymaps, treat that as evidence of a remaining writer defect rather than acceptable steady-state behavior.

Automatic repair should not run as a broad disk-writing subprocess after each keymap. That can race the editor and mask the originating bug. Make each managed operation correct using its own snapshots; let the normal reconciliation path handle external drift.

## Validation and acceptance criteria

The following existing plugin checks passed, exit 0, with 79 reported tests:

```sh
node --test --test-reporter=dot \
  scripts/test-navigation-task-card-theme-edit.cjs \
  scripts/test-ledger-tools-pomodoro-themes.cjs \
  scripts/test-navigation-hotkeys-pomodoro-move-pickers.cjs
```

The independent probes still demonstrated the lookup and rename failures described above. Passing existing tests is therefore evidence of the current baseline, not evidence that agreement already holds. No Rust build or full application suite was run for this research-only task.

The implementation should add meaningful regression and conformance cases:

- Rename BUILD → READ with a BUILD task: preview and commit agree, the task becomes READ, and no discarded Merge outcome is possible.
- One historical and one live link to the same task; identical block IDs in different notes; path aliases, same-note links, marked links, and embeds.
- Duplicate live occurrences: one matching and one mismatching entry must both be checked, regardless of order.
- Explicit, inherited, reading, root-based, and global defaults; clearing overrides; intentionally absent types; malformed fields and configuration changes during planning.
- Typed composites with labels, label-only containers, unnamed entries, no configured vocabulary, unconfigured effective types, hidden/exempt types, and exact MEET.
- Source removal with another same-type task remaining; last-link removal; components that never had links; base fallback; unresolved sibling links preventing unsafe removal.
- Completion/cancellation/blocking in the same reconcile pass, including line shifts and empty-entry deletion.
- Running versus planned entries, closed-session byte preservation, CRLF/no-final-newline, component spelling/order, length limits, and unchanged clock fields.
- Changed task/default/config preimages, unsaved editor contents, quiet-period deferral, failed second-file writes, and accurate partial-result notices.
- `repair(repair(snapshot)) == repair(snapshot)`; dry-run/apply plan equivalence; a corrected managed gesture followed by reconcile yields **zero type repairs**.

Use production routing helpers in integration tests rather than mocks that always return the desired action. Share the policy vectors between Rust and JS, and test the adapters separately; the reproduced defects are in the seams between correct pure rules and their callers.

## Source index

**bob-cli** — pinned to `01cb7b5c3eb75d7353ef4a57014cc5ada1178bf6`:

- [C1 — task-type contract, inheritance, routing, merged names](https://github.com/bobs-org/bob-cli/blob/01cb7b5c3eb75d7353ef4a57014cc5ada1178bf6/docs/task-types.md#pt13--task-type-suggestions).
- [C2 — effective type suggestions](https://github.com/bobs-org/bob-cli/blob/01cb7b5c3eb75d7353ef4a57014cc5ada1178bf6/src/native/pomodoro_themes/suggest.rs#L81).
- [C3 — classification, agreement, landing and relocation](https://github.com/bobs-org/bob-cli/blob/01cb7b5c3eb75d7353ef4a57014cc5ada1178bf6/src/native/pomodoro_themes/routing.rs#L35).
- [C4 — merge, narrow and before/after shedding](https://github.com/bobs-org/bob-cli/blob/01cb7b5c3eb75d7353ef4a57014cc5ada1178bf6/src/native/pomodoro_themes/merged.rs#L41).
- [C5 — mismatch lint](https://github.com/bobs-org/bob-cli/blob/01cb7b5c3eb75d7353ef4a57014cc5ada1178bf6/src/native/plan_budget/mod.rs#L332).
- [C6 — Rust relocation adapter and live-link lookup](https://github.com/bobs-org/bob-cli/blob/01cb7b5c3eb75d7353ef4a57014cc5ada1178bf6/src/native/pomodoro_themes/relocation_apply.rs#L236).
- [C7 — Today occurrence scanner and deduplicated task resolver](https://github.com/bobs-org/bob-cli/blob/01cb7b5c3eb75d7353ef4a57014cc5ada1178bf6/src/native/plan_budget/today.rs#L59).
- [C8 — companion naming command write sequence](https://github.com/bobs-org/bob-cli/blob/01cb7b5c3eb75d7353ef4a57014cc5ada1178bf6/src/native/capture_pomodoro_name.rs#L300).
- [C9 — broader hooks reference scanner](https://github.com/bobs-org/bob-cli/blob/01cb7b5c3eb75d7353ef4a57014cc5ada1178bf6/src/native/task_status_hooks/pomodoro.rs#L15).
- [C10 — reconciliation composition, final consumption and apply](https://github.com/bobs-org/bob-cli/blob/01cb7b5c3eb75d7353ef4a57014cc5ada1178bf6/src/native/task_status_hooks/sync.rs#L988).
- [C11 — guarded writes, recovery, quiet period and retry contract](https://github.com/bobs-org/bob-cli/blob/01cb7b5c3eb75d7353ef4a57014cc5ada1178bf6/docs/task-status-hooks.md#retries); preceding paragraphs document write safety and its limits.

**bob-plugins** — pinned to `cfb331ea7f4d9f7413dece935e738a0eaa77e16e`:

- [P1 — JS pure routing mirror](https://github.com/bobs-org/bob-plugins/blob/cfb331ea7f4d9f7413dece935e738a0eaa77e16e/plugins/bob-ledger-tools/src/279-plugin-task-type-routing.js#L142).
- [P2 — rename passes empty options](https://github.com/bobs-org/bob-plugins/blob/cfb331ea7f4d9f7413dece935e738a0eaa77e16e/plugins/bob-navigation-hotkeys/src/650-plugin-move-commit.js#L125).
- [P3 — landing-mode helper and split write application](https://github.com/bobs-org/bob-plugins/blob/cfb331ea7f4d9f7413dece935e738a0eaa77e16e/plugins/bob-navigation-hotkeys/src/651-pomodoro-bullet-type-move-commit.js#L42).
- [P4 — rename preview uses the same empty options](https://github.com/bobs-org/bob-plugins/blob/cfb331ea7f4d9f7413dece935e738a0eaa77e16e/plugins/bob-navigation-hotkeys/src/200a-pomodoro-bullet-type-move.js#L410).
- [P5 — Task Card entry enumeration, lookup and relocation planner](https://github.com/bobs-org/bob-plugins/blob/cfb331ea7f4d9f7413dece935e738a0eaa77e16e/plugins/bob-navigation-hotkeys/src/316-task-card-type-relocation.js#L33).
- [P6 — Task Card field-first/ledger-second commit](https://github.com/bobs-org/bob-plugins/blob/cfb331ea7f4d9f7413dece935e738a0eaa77e16e/plugins/bob-navigation-hotkeys/src/352-picker-task-card-theme-stage.js#L460).
- [P7 — note move uses the shared live-link lookup](https://github.com/bobs-org/bob-plugins/blob/cfb331ea7f4d9f7413dece935e738a0eaa77e16e/plugins/bob-navigation-hotkeys/src/655-plugin-inbox-route.js#L26).

## Recommended solution

Implement **agreement-preserving gestures plus conservative reconciliation of today’s open Pomodoro names**. First fix rename mode and path-qualified live-link discovery, including historical/duplicate occurrence handling. Keep explicit rename/retype and type-driven relocation behavior, but make failures and unavailable planning visible. Add shared postcondition checks to the affected writer paths.

Then add one final staged-ledger pass to `bob task reconcile`: preserve task types, link placement, labels, custom containers, MEET ownership, clock fields, and closed history; add missing components for safe resolved links; shed only where this operation has reliable before/after evidence. Report remaining untyped, ambiguous, invalid, or protected cases rather than guessing. Reuse dry-run, guarded writes, recovery, and shared Rust/JS vectors. Success means routine supported gestures need no subsequent type repair, while external drift converges safely on the next successful reconcile.

I would approve this adjusted design. I would not approve unconditional name reconstruction or silent background retyping: both make the rule appear stronger by discarding information the user still owns.
