# Typed off-clock inheritance and the MEET-only vault migration

Independent research by **cdx**, 2026-11-05. This report is based on source inspection, audited project memory, read-only vault queries, and Obsidian's documentation. No peer report, peer transcript, or peer findings were consulted. No application code or vault notes were changed.

**Recommendation:** add `offclock_types` as a narrowly scoped extension of the existing inherited clock policy. Match the task's **effective type**, and let the nearest area/project clock declaration replace the ancestor's policy. Preserve explicit clock tags, existing boolean semantics, the counted-links rule, and historical session stamps. Once all writers support it, replace `offclock: true` with `offclock_types: [MEET]` in the currently identified areas, `body.md` and `love.md`.

This is a good fit if the intended distinction is “meetings in these parts of my life should not count toward Worked, but deliberate non-meeting work should.” It is a behavioral change, not a syntax migration: an untagged non-MEET task previously inherited off-clock and will now usually be on-clock. If the intention is instead “all personal activity remains off-clock,” retain `offclock: true` and use occasional `#on` exceptions.

The findings below distinguish existing behavior from proposed requirements. Source paths refer to bob-cli commit `01cb7b5c3eb75d7353ef4a57014cc5ada1178bf6` and bob-plugins commit `cfb331ea7f4d9f7413dece935e738a0eaa77e16e`. These are the inspected revisions, not a claim about later deployment state.

**What exists today.** A task's own `#on` wins, followed by `#off` and its deprecated aliases, then the nearest area/project `offclock` value, then on-clock. An invalid nearer boolean stops inheritance and resolves on-clock. Blank or absent values inherit. The walk follows the task's valid `[root:: NOTE]` when present, otherwise its residence, then note `parent` links, with cycle protection and a 16-note bound. This is graph inheritance, not a filesystem subtree search. Daily tasks can inherit through `[root::]`; an ordinary daily note contributes no default. Other note kinds can carry the walk but do not declare clock policy. This is implemented in [`pomodoro_homes/clock.rs`](https://github.com/bobs-org/bob-cli/blob/01cb7b5c3eb75d7353ef4a57014cc5ada1178bf6/src/native/pomodoro_homes/clock.rs), [`resolve.rs`](https://github.com/bobs-org/bob-cli/blob/01cb7b5c3eb75d7353ef4a57014cc5ada1178bf6/src/native/pomodoro_homes/resolve.rs), and documented in the [vault format](https://github.com/bobs-org/bob-cli/blob/01cb7b5c3eb75d7353ef4a57014cc5ada1178bf6/docs/reference/vault-format.md#task-clock-tags-and-note-defaults).

A task has one effective type, even though a Pomodoro name can have several `+` components. For open tasks, type resolution is: explicit `[type::]` or legacy `[theme::]`; reading-task rule; nearest eligible `task_type:` or legacy `theme:` default; global `plan.default_type`; otherwise none. A field can be omitted precisely because it matches inheritance. Therefore matching only literal `[type:: MEET]` would miss valid MEET tasks. Dataview's raw task fields are not an effective-type API. See [`suggest.rs`](https://github.com/bobs-org/bob-cli/blob/01cb7b5c3eb75d7353ef4a57014cc5ada1178bf6/src/native/pomodoro_themes/suggest.rs) and the [task-type contract](https://github.com/bobs-org/bob-cli/blob/01cb7b5c3eb75d7353ef4a57014cc5ada1178bf6/docs/task-types.md).

Clock choice is operational. Starts and closes stamp `[t:: Nm]` or `[off:: Nm]`; calendar sync creates stamped sessions; ended off-clock Event Tasks can settle automatically. A session remains wholly Worked if any counted link is on-clock or unresolved, or if it has no counted links. Closed ledger stamps remain history, while later changes can produce drift diagnostics. The proposal must retain these rules rather than becoming a Stats-only filter. I reviewed the audited decisions `decisions:off-clock-follows-tag-then-note-default` and `decisions:off-clock-pomodoros-count-apart`, along with the related glossary definitions.

**The actual migration surface.** This read-only query returned exactly two notes with non-null `offclock` or `offclock_types`:

```dataview
TABLE WITHOUT ID file.path AS Path, type AS Kind, parent AS Parent,
  offclock AS Offclock, task_type AS TaskType, offclock_types AS OffclockTypes
WHERE offclock != null OR offclock_types != null
SORT file.path ASC
```

| Note | Kind | Parent | Current clock property | New property present |
| --- | --- | --- | --- | --- |
| `body.md` | area | `area` | `offclock: true` | no |
| `love.md` | area | `area` | `offclock: true` | no |

Neither returned a `task_type` default. A second query for immediate children showed that the policy reaches beyond these two files, including subareas such as `abby.md`, `family.md`, `fun.md`, `kelly.md`, and `vacation.md` under love, plus other child notes and archived notes. That query is not a complete recursive impact analysis. Parent relationships on non-area notes can still matter because the walk traverses them, and daily Event Tasks can reach these areas through task roots.

Both queries completed successfully, with unrelated ambiguous-link warnings from the vault index. The inventory is an observation of the default vault on this host; it is not an assertion that every host has synced or that there are no blank properties. I did not measure the exact number of affected effective task types or forecast a change in Worked minutes. Those require the proposed resolver and an impact preview, not counts of raw `[type::]` strings.

**Proposed contract, with the requirement adjustments made explicit.** The request leaves inheritance, mixed declarations, and type identity underspecified. I recommend the following choices:

| Case | Recommended behavior |
| --- | --- |
| `offclock_types: [MEET, READ]` | Off-clock iff the task's effective type equals a listed canonical type key. |
| Multiline YAML list | Identical to a flow list. |
| Missing, blank, or YAML null `offclock_types` | No local declaration; inherit. |
| `offclock_types: []` | Explicit local policy matching no types; stop ancestor inheritance. |
| A nonmatching or untyped task at a valid list | On-clock; do not resume searching ancestors. |
| Nearer list versus ancestor list or boolean | Nearer declaration replaces the whole inherited clock policy. Do not union lists. |
| Nearer `offclock: false` or `true` | Existing all-on/all-off behavior wins over ancestor declarations. |
| Own `#on` or `#off` | Existing tag precedence wins over every note policy. |
| Both nonblank properties on one note | Diagnose a conflicting declaration; retain the existing boolean's precedence, including its existing invalid-value behavior. Writers/migration should never create this state. |
| Malformed list, invalid item, scalar shorthand, map, or composite item | Diagnose; treat the declaration as on-clock and stop inheritance. Do not partially accept the list. |
| Property on a non-area/project note | Ignore with a diagnostic; continue the normal parent walk. |
| Syntactically valid but unconfigured type | Allow matching; catalog membership, hiding, and color do not define semantic identity. |

The coexistence rule is a compatibility choice: adding a second field should not silently weaken an existing `offclock: false` exception or narrow an existing `true`. It makes removing the boolean an essential part of migration. A strict refusal at the writer boundary is appropriate, but ordinary read/clock resolution needs a deterministic fallback. A future design could instead make coexistence invalid and resolve everything on-clock; I prefer preserving the existing explicit boolean.

The most consequential adjustment is **replacement inheritance**. Suppose an ancestor says `offclock: true` and a project beneath it says `offclock_types: [MEET]`. The project's BUILD tasks should be on-clock. Continuing to the ancestor after a list miss would leave them off-clock and defeat the apparent narrowing. Conversely, a child list `[READ]` beneath an ancestor `[MEET]` means only READ in that child; include both names when both are wanted. `[]` provides an explicit reset, while deleting the property restores inheritance. These rules make a list an inherited predicate over types, consistent with the existing nearest boolean default.

This is preferable to accumulating every matching ancestor: cumulative rules make narrowing difficult and create surprising interactions with `offclock: false`. It is also preferable to requiring `offclock: true` alongside a list: that couples two inherited properties, raises cross-level filtering questions, and contradicts the requested migration to a standalone `offclock_types` property.

Use the existing single-component type canonicalization and `normalize_component` identity; trim, normalize case/whitespace consistently, and deduplicate equivalent list entries. Do not introduce substring, prefix, wildcard, regex, tag, or Pomodoro-component matching. `MEET` is a task type here, not the note's `type: "[[area]]"`, a calendar provider flag, or the name of a linked session. A manually written Event Task without an effective MEET type should not acquire MEET merely because its description contains a time span. Likewise, an ordinary area task whose effective type is MEET should match even if it is not a calendar event.

A list fits Obsidian's property editor: Obsidian supports list properties and assigns a property type consistently by property name across the vault. Keep the field flat rather than introducing a nested rule language; nested properties are not supported by its ordinary property editor. A canonical writer should emit the familiar block-list form. [Obsidian Properties documentation](https://obsidian.md/help/properties).

```yaml
offclock_types:
  - MEET
```

**Where the implementation needs care.** The central Rust resolver already gives this feature a natural home. Extend `NoteFacts` with an explicit representation that distinguishes absence, a valid set (including the empty set), and invalid input. Consider a unified parsed `NoteClockPolicy` with variants for all, none, selected types, and invalid; preserve enough raw information to diagnose both properties. Keep the selection policy in one place rather than adding `offclock || matches_type` independently to callers. The current parsing lives in [`facts.rs`](https://github.com/bobs-org/bob-cli/blob/01cb7b5c3eb75d7353ef4a57014cc5ada1178bf6/src/native/pomodoro_homes/facts.rs).

The existing `frontmatter_scalar` deliberately rejects sequences; it cannot parse the new field. Add a strict list reader that handles flow lists, indented and unindented block lists, quoted strings, comments, blank/null values, duplicate keys, and empty lists. Validate original YAML element types before converting names; a mixed list containing a boolean or mapping must not be silently coerced or flattened. Reuse the existing YAML dependency for the isolated property's value if practical, while preserving the line-based reader's handling of other Bob frontmatter. Replacing every frontmatter parser is unnecessary scope. Rust's raw-text interpretation and Obsidian's parsed metadata must share fixtures, especially for `[]`, null, numbers, nested lists, and unquoted wikilinks. See [`projects/scan.rs`](https://github.com/bobs-org/bob-cli/blob/01cb7b5c3eb75d7353ef4a57014cc5ada1178bf6/src/native/projects/scan.rs) and [`ref_library/frontmatter.rs`](https://github.com/bobs-org/bob-cli/blob/01cb7b5c3eb75d7353ef4a57014cc5ada1178bf6/src/native/ref_library/frontmatter.rs).

Type resolution introduces a dependency the current clock resolver lacks: `effective_clock` currently takes a home resolver, residence, and task line, with no `PlanConfig`. Extract or expose a lightweight effective-type result—canonical key, origin, repair/warnings—from the existing semantic resolution rather than invoking a catalog scan or CLI for each clock lookup. The richer suggestion API can build its UI metadata from that result. Pass the same immutable configuration snapshot used by the operation; cache note facts and walk results within it. Resolve types lazily only when a selected-types policy needs them. A boolean policy or explicit clock tag should remain cheap.

Do not simply call today's `suggest_for_task` everywhere: it intentionally returns no suggestion for completed/cancelled tasks. Closes and Google sync can examine already-transformed rows, and Stats evaluates current linked-task facts for drift. A typed clock must not suddenly become on-clock because a checkbox changed to `[x]`. Define a lower-level resolution path that can evaluate the line's explicit type and applicable current inheritance independently of suggestion eligibility. Use it only to choose a new stamp or compute current drift; never rewrite an existing closed session stamp. Existing malformed/duplicate task-type fields should retain their current repair-and-inherit semantics, rather than acquiring a different clock-specific parser. This closed-task boundary is visible in [`suggest_for_task`](https://github.com/bobs-org/bob-cli/blob/01cb7b5c3eb75d7353ef4a57014cc5ada1178bf6/src/native/pomodoro_themes/suggest.rs#L81) and [`stats/homes.rs`](https://github.com/bobs-org/bob-cli/blob/01cb7b5c3eb75d7353ef4a57014cc5ada1178bf6/src/native/stats/homes.rs).

The integration surface is broader than the new frontmatter parser:

| Consumer | Work needed |
| --- | --- |
| `capture_pomodoro_start.rs` and `capture_pomodoro_close/linked_tasks.rs` | Supply type/config context; resolve from the final candidate task state and counted links. Keep previews and committed stamps identical. |
| `event_task::enrich_event_clocks` and `task_status_hooks/settle.rs` | Use the same resolver so inherited MEET events settle correctly and nonmatching events remain on-clock. |
| `gcal/clock.rs`, `snapshot.rs`, and `plan.rs` | Make predicted creation and retained-row clock resolution type-aware; preserve explicit tags and user edits. |
| `stats/homes.rs` | Update current-clock drift calculation, leaving historical time totals based on stored ledger keys. |
| Obsidian ledger tools | Mirror policy/type semantics for starts, link chips, event marks, and the public clock API. |
| Obsidian task-status-cycler | Verify closes using the ledger-tools clock API; retain documented tag-only fallback when that API is unavailable. |
| Capture agenda/preview consumers | Confirm returned clock booleans/provenance stay consistent with the eventual write. |
| Type rename/split coverage | Include or explicitly report references inside the new lists so type operations cannot leave stale policies. |

There is a concrete Google Calendar trap: [`gcal/clock.rs::probe_line`](https://github.com/bobs-org/bob-cli/blob/01cb7b5c3eb75d7353ef4a57014cc5ada1178bf6/src/native/gcal/clock.rs#L43) currently constructs `- [ ] #task Event ... [root:: X]` without a type. Newly created synced tasks are made effectively MEET, and `[type:: MEET]` is omitted when inheritance already supplies it. A type-aware resolver applied to the old synthetic probe can therefore disagree with the task sync will create. For creation previews, pass the intended effective MEET type or construct the same candidate task semantics as the writer. For existing tasks, resolve the retained/post-update vault line so an explicit retype or edited root continues to matter. Context-only calendar rows should keep their existing tag-only behavior. The write side is in [`gcal/sync.rs`](https://github.com/bobs-org/bob-cli/blob/01cb7b5c3eb75d7353ef4a57014cc5ada1178bf6/src/native/gcal/sync.rs) and [`gcal/plan.rs`](https://github.com/bobs-org/bob-cli/blob/01cb7b5c3eb75d7353ef4a57014cc5ada1178bf6/src/native/gcal/plan.rs).

Obsidian is a second implementation, not merely a renderer. [`036-pomodoro-clock.js`](https://github.com/bobs-org/bob-plugins/blob/cfb331ea7f4d9f7413dece935e738a0eaa77e16e/plugins/bob-ledger-tools/src/036-pomodoro-clock.js) walks metadata and resolves boolean defaults itself. Its public adapter in `273-plugin-pomodoro-home-chips.js` currently supplies metadata and the vault, without plan type defaults. The type suggestion mirror already lives in `279-plugin-task-theme-suggest.js`; its UI wrapper also suppresses suggestions for closed tasks. Supply shared semantic type/config context without introducing subprocess calls into rendering. Test the public API used by [`task-status-cycler`](https://github.com/bobs-org/bob-plugins/blob/cfb331ea7f4d9f7413dece935e738a0eaa77e16e/plugins/task-status-cycler/src/062-pomodoro-clock.js), not just the pure ledger-tools helper.

Clock displays will now depend on more inputs: type fields, reading/global type configuration, ancestor type defaults, the new list, roots, and parents. Existing metadata listeners already refresh link chips for note changes, but configuration changes need explicit verification too. Use unsaved/current editor text where the operation already does so; don't resolve a retyped task against stale disk content. Resolve after retype/root edits and before stamping, with a coherent snapshot. Keep existing `clock_source: note` and note provenance if possible; optional policy/type explanation fields can say “off-clock via love: MEET matches offclock_types.” Avoid a new required enum value solely for this feature. The Mac capture client should continue to render Bob's returned results; this proposal does not justify moving clock policy into Swift.

A less obvious requirement is type rename integrity. Today [`pomodoro_themes/coverage.rs`](https://github.com/bobs-org/bob-cli/blob/01cb7b5c3eb75d7353ef4a57014cc5ada1178bf6/src/native/pomodoro_themes/coverage.rs) knows about note defaults and task fields, while [`rename.rs`](https://github.com/bobs-org/bob-cli/blob/01cb7b5c3eb75d7353ef4a57014cc5ada1178bf6/src/native/pomodoro_themes/rename.rs) promises to rename types everywhere. A new list is another semantic type reference. Rename should rewrite matching entries in its existing previewed transaction, deduplicate on merges, and preserve unrelated bytes. Split cannot infer which new types should remain off-clock; preserve the list and surface an explicit remaining-reference warning, consistent with its treatment of defaults. This is part of safely supporting arbitrary type names, not an unrelated cleanup.

**Critique and alternatives.** The feature removes repetitive tags and expresses a useful intersection: area ownership plus kind of work. The flat list is easy to understand and retains boolean defaults for truly all-off areas. It avoids making all MEET tasks everywhere off-clock, which would incorrectly include work meetings. A global `offclock_types` configuration would therefore be the wrong scope for this use case.

The cost is that type becomes an accounting input. Changing a task from MEET to PLAN, changing an inherited type, or moving its root can change its current clock without changing any clock property. The implementation must make that explanation visible and keep historical session stamps stable. If types are used casually as labels rather than stable kinds of work, explicit `#off` is more predictable.

MEET is also not synonymous with “personal time,” “calendar event,” or “attended meeting.” An untitled or untyped hand-written Event Task may cease inheriting off-clock after migration. A personal task retyped to MEET can gain it. Ended matching events can still settle automatically even if nobody attended; this feature narrows eligibility but does not change attendance semantics. Those are consequences to accept deliberately, not implementation bugs to paper over with implicit MEET inference.

The mixed-session rule remains a limitation: a session with one off-clock MEET link and one on-clock task is entirely Worked. Do not promise per-link minute filtering, or add it to this change. Similarly, changing area properties should not recalculate old Worked totals. More drift diagnostics after migration are expected evidence of a policy change.

If the real goal is specifically “calendar-derived personal meetings,” an explicit rule at calendar routing or tags in Google titles is a viable narrower alternative. It would omit manual MEET tasks and add another source-specific policy, so I would choose it only if that narrower distinction is intentional. A general conditional clock rules engine is excessive for a two-note, one-type use case. Keep `offclock_types`; do not introduce arbitrary conditions, a second type taxonomy, or a polymorphic `offclock` boolean/list property.

**Migration and verification.** Treat the change as two deliverables: deploy compatible behavior, then make a small reviewed vault edit. Do not migrate the vault first: older CLI/plugin versions ignore the new list and would treat even untagged personal MEET tasks as on-clock. Keep the old properties until every active writer is ready, including calendar sync and reconciliation on other hosts and Obsidian on the Mac. Use the normal bob-cli release train; plugin work belongs in the source repository and is deployed with `bob plugins sync`.

Before applying the edit, re-run the inventory and compute a read-only before/after report with the real resolver over affected open tasks and current/future Event Tasks, including `[root::]` routes. Group changes by effective type and show `#on`/`#off` overrides. This can be an implementation-time migration helper; it does not require a permanent new CLI command. Finish or explicitly inspect affected running sessions before the switch, because close-time resolution may legitimately differ from start-time resolution. Obtain a clean sync baseline and perform a narrow, conflict-checked edit under the vault's existing maintenance/sync coordination.

The intended source change in each confirmed area is only:

```diff
-offclock: true
+offclock_types:
+  - MEET
```

Do not replace `offclock: false`, invalid values, unrelated projects, task tags, or archived content. Do not stamp inherited `#off` onto tasks. Preserve the rest of each note, and verify the exact current content before applying. Re-running the migration should produce no diff. If the inventory has changed, reassess it rather than expanding a blanket replacement. Existing explicit `#off` tags on non-MEET tasks continue to win; any cleanup of those is a separate policy decision. Rollback restores the two properties; it does not retroactively rewrite sessions recorded while the new policy was active.

The implementation should be accepted against shared Rust/JavaScript contract vectors and a focused set of integration tests:

- Flow/block lists; case and whitespace normalization; duplicates; empty versus absent/null; malformed scalars, mixed/nested lists, comments, and conflicting keys.
- A full nearest-policy matrix: parent true/false/list crossed with nearer true/false/list/empty/absent, plus tags, nonmatching types, and unknown-but-valid type names.
- Effective type from task field, legacy alias, reading rule, note default, global default, no type, and repair state. Include `task_type: off` with a configured global default, preserving today's type semantics.
- Root-routed daily tasks, invalid/ambiguous roots, non-area intermediary notes, cycles, and depth limits. Existing boolean-only fixtures must remain unchanged.
- CLI preview/write parity and Obsidian start/close parity; closed checkbox rows must not lose MEET merely because the suggestion UI excludes them.
- Google list versus sync for new MEET tasks, MEET inherited without an explicit task field, edited retained task types/roots, context-only rows, and past events born closed.
- Ended-event settling, agenda clocks, link/event display refresh after type/default/config edits, and mixed/unresolved/empty counted-link sessions.
- Type rename and merge through lists, split warnings, and a migration repeated twice with the second run producing no changes.
- Closed ledger bytes and historical totals unchanged after the policy edit; current-clock drift can change and must be explained.

I inspected the existing resolver and integration tests, including `pomodoro_homes/tests.rs`, `tests/cli/capture/pomodoro_clock.rs`, `tests/cli/task_status_hooks/settle.rs`, `tests/cli/stats_clock.rs`, and the plugin clock tests. I did not implement a prototype or run a new test suite in this research turn. The remaining uncertainties are deployment readiness across hosts, the exact affected-task inventory at migration time, and performance after adding effective-type context. They do not block selecting the design, but they must be checked before the vault cutover.

**Recommended solution:** implement a standalone, strict `offclock_types` list as the nearest inherited clock predicate, evaluated against the existing effective task type. Preserve explicit tag overrides, boolean compatibility, all-or-nothing session accounting, and frozen historical stamps. Deliver Rust and Obsidian parity—including calendar prediction, closed-task resolution, and type-reference maintenance—before replacing the two observed `offclock: true` declarations in `body.md` and `love.md` with `offclock_types: [MEET]`. This is a sound, bounded improvement when the intended policy is specifically to exclude MEET work in those areas while counting their other work.
