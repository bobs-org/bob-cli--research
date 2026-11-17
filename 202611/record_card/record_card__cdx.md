# Record-note details cards: schema-aware presentation with guarded editing

Independent research by **cdx**, 2026-11-17. No other report, transcript, summary, or findings from this research swarm were consulted.

## Decision in brief

**Build this feature.** Replace the record note’s routine in-document Properties display with an album-driven **Record details** card immediately below its authored H1. Display actual record values using the album’s field order, labels, choice labels, and types. Use the existing album/bank visual language and guarded editing machinery. Keep YAML as the only stored representation.

The most important adjustment is semantic: **a record card edits this record’s values; an album Schema Card edits the collection’s definition.** They should feel like members of one family, but they should not expose the same destructive or structural actions. On a record, `==` should open **Edit record details**. An explicitly named **Edit album schema…** action should remain available separately.

This is more than a rendering task. The existing record writer is a strong foundation, but the complete feature needs a reliable single-record read contract, an edit-session concurrency token, guarded Undo, coordination with open editor buffers, and safe fallback when a card cannot replace Properties.

## Evidence and confidence

I inspected the supplied screenshot, the bob-cli records contract and implementation, the linked bob-plugins implementation and tests, existing album UI screenshots, the requested `==` plan through an audited artifact read, and official Obsidian/accessibility documentation. I also used the supported read-only `bob query`, `bob records show`, and `bob bank config` interfaces against the default vault. No vault or plugin code was changed.

Source snapshots:

- bob-cli: `f6924787fa43424d6fb217261adf264debbf2272`.
- bob-plugins: `1b74ad52ce63e129524f40a221b0f59bc55f23de`.
- Shared input: `plan:202611/double_equals_schema_keymap.md`, read with `sase artifact read`.
- Screenshot: `~/tmp/screenshots/20261117_101208.png`.

The screenshot shows `bead_lifecycle`, seven Properties, then the authored **Bead Lifecycle** H1 and **Notes** H2. It also shows Obsidian’s separate filename-derived inline title above Properties. Hiding Properties alone will not remove that duplicate title. Treat inline-title suppression as a separate, optional, per-view polish decision; do not change the vault-wide setting as part of this feature.

The read-only live queries confirm that `sase_blog_zettel/bead_lifecycle.md` belongs to `sase_blog_zettel.md`, with `status=draft`, the Claim text shown in the screenshot, and `section=future`. The authoritative `bob records show sase_blog_zettel -f json` orders its fields **Status, Claim, Section**, marks the first two required, and supplies **✍️ Draft** and **🔮 Future Work** as choice labels. The album has four records at inspection time.

`bob bank config -f json` identifies `bank.md` as valid and reports 25 categories, one account, and ten rules. I examined its rendering and editing implementation rather than claiming a live visual walkthrough of that note. The vault was queried through Bob’s read-only interfaces, not opened as an unmanaged repository checkout.

Confidence is high in the data model and integration points, moderate in the final interaction details until exercised in real Obsidian. This research did not implement or run the proposed UI. Existing screenshots are evidence of the established components, not screenshots of the proposed feature.

## Why it is a good idea, and where it can go wrong

The current presentation gives storage mechanics prominence over the record’s meaning. `parent`, `type`, and `created` are useful metadata, but the user’s immediate questions are “what is this?”, “what are its facts?”, and “what have I noted about it?”. An album-aware card can answer those questions compactly and offer valid choices without asking the user to remember stored keys.

It also makes the album schema pay off in everyday use. Today, the schema knows that Section is a choice and Claim is required; the generic Properties surface does not embody that complete Bob contract. The native Properties UI already has keyboard navigation, however, so a replacement must earn its complexity through schema-specific behavior and safe writes, not simply through rounded corners. Obsidian documents both Properties navigation and its vault-wide property-type semantics. [Obsidian Properties](https://obsidian.md/help/properties)

The main risks are hiding information, creating a second source of truth, allowing a stale card to overwrite another pane’s work, and turning a small record into a large configuration dashboard. Those are avoidable with the boundaries below.

| Approach | Advantages | Costs | Judgment |
| --- | --- | --- | --- |
| Restyle or reposition native Properties | Low initial effort; retains native editing | Does not naturally express Bob choice sets, required fields, album order, or atomic index updates; DOM relocation is fragile | Keep native Properties as fallback, not the primary design |
| Generated Markdown table/callout in every record | Portable rendered output | Duplicates stored values, adds maintenance writes, introduces stale representations and migration work | Reject |
| Permanently editable inputs embedded in Live Preview | Direct mouse editing | Focus/caret survival, CodeMirror selection, widget re-creation, and write timing become much harder | Defer; not needed for a strong first release |
| Read-oriented details card plus existing modal editing idiom | Familiar, compact, easy to reach by key or click; clean separation of display and mutations | Requires a new record adapter and writer contract | **Recommend** |
| Separate inspector/sidebar only | Avoids editor integration | Misses the requested reading flow and loses context when switching notes | Useful fallback, not sufficient alone |

## Explicit requirement adjustments

1. **Call the visible surface “Details” or “Zettel details”, not “Schema”.** The schema is the definition on the album; the record contains an instance. Reserve “Edit album schema…” for a deliberate collection-wide action.
2. **Hide the rendered Properties surface, never delete or relocate frontmatter bytes.** Source mode and the native Properties sidebar remain available. Do not alter global Obsidian Properties settings.
3. **Make hiding conditional on a usable replacement.** During initial loading, unavailable/broken identity, unsupported data, or a rendering failure, keep native Properties available. A stale but complete last-good card may remain visible with a stale notice and edits disabled until revalidated.
4. **Parity means common interaction and safety, not every schema operation.** Do not offer field-definition removal, required/suggest toggles, choice creation, field reordering, or schema-label editing as record-value actions.
5. **Do not silently hide properties that the album does not declare.** Provide a visibly labelled **Other properties (N)** disclosure and a native Properties/Source action. Preserve every key, including plugin and user metadata.
6. **Keep record identity out of the initial writer scope.** `parent`, `type`, `title`, and `created` are reserved, not schema fields. Show parent as navigation and the others in Metadata. Title/H1 divergence should be visible, not silently reconciled; title editing, moving albums, and renaming files need their own contract.
7. **Make record `==` open record values.** This intentionally resolves the in-flight plan’s record ambiguity differently from its `records_too` alternative, which opens the parent’s schema editor.
8. **Use desktop editing first, with honest mobile degradation.** If a mobile device lacks a usable report and Bob writer, preserve native Properties and Source. Do not hide the only functioning editor behind an unavailable CLI.

These changes preserve the requested placement, visual family, field editing, and keyboard quality while narrowing the dangerous ambiguities.

## Proposed appearance

Use the existing album/bank shell: a restrained root-area accent, a thin leading border, subtle tinted background, rounded corners, and readable theme-aware text. The current styles already share approximately 8 px corners, a 2 px leading accent, and similar padding. Reuse those tokens rather than inventing a third style system. Keep title-sized typography outside the card.

A schematic for the actual example:

```text
Bead Lifecycle                                      ← authored H1

┌─ 📇 SASE Blog Zettel                     Edit ==  ⋯ ─┐
│                                                     │
│  Status    ✍️ Draft                                  │
│  Claim     Bead triage/lifecycle needs to be          │
│            thoroughly designed in v2.               │
│  Section   🔮 Future Work                            │
│                                                     │
│  Metadata ▸                                         │
└─────────────────────────────────────────────────────┘

Notes                                               ← authored H2
```

This is an interaction sketch, not a pixel-accurate mockup. Actual values and choice labels above come from the inspected record and album.

Design details:

- Render fields in declared schema order. Use stable stored keys as identity, never labels or row offsets.
- Use a two-column label/value layout at normal widths. At a narrow pane, stack the value beneath its label. Text wraps; long links and claims must not cause horizontal scrolling.
- Do not make every value a pill. Choices can use compact labelled chips; prose remains prose; numbers remain readable numbers. Show a small edit affordance on row hover/focus without making ordinary links stop navigating.
- Render declared optional fields even when absent, with **Not set** and an edit affordance. Missing required fields say **Required · missing**. A missing field is not an inherited default.
- Display configured choice labels while retaining the stored key in accessible details or a tooltip. An unknown choice displays its actual raw value and a warning; it must never appear as an empty field or silently map to the nearest choice.
- Preserve textual content as text. Render recognized link fields with Obsidian navigation/hover semantics and URL fields as links; do not render arbitrary stored text as executable HTML.
- Metadata contains the immutable creation timestamp, actual type, stored title, and path as useful secondary information. Use an exact timestamp on demand rather than letting a relative date become misleading.
- Other properties is a separate disclosure when needed, with names and actual values or an explicit unsupported-value marker. Never hide extra data merely because it cannot be formatted attractively.
- Put **Edit album schema…**, **Show Properties**, and **Open Source** in the overflow menu. The album link remains visible. No record count, filled-count badge, schema usage chart, or dashed “add field” target is needed on this card.
- Default to expanded details. For genuinely large schemas, a whole-card collapse may remember view-local state; do not silently omit the last fields or prioritize by filled status. Keep one-column reading order consistent across widths.
- Use textual states as well as color, clear focus rings, reduced-motion support, and generous pointer targets. Keep short action hints visible; place the complete keyboard reference under Help/All actions.

The inline surface should use ordinary section/description-list/link/button semantics. It is not a modal or an ARIA grid. The editor can reuse the existing modal shell with native labelled inputs, explicit Save/Cancel buttons, focus containment, and focus restoration. Those focus rules follow the W3C dialog pattern. [WAI-ARIA modal dialog pattern](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/)

## Editing and keyboard contract

### One record editor, reached in several ways

The header’s **Edit**, a field’s edit button, **Edit record details** in the command palette, and `==` must all call one entry point, conceptually `openRecordDetailsEntry({ filePath, fieldKey?, leaf? })`.

A field click opens that field’s editor directly. The header and `==` open browsing at the last selected field for that pane, otherwise the first declared field. Enter edits it. Keep the modal open after a successful save, return to the saved row, and offer Undo. A persistent title names the record, so users can distinguish the current note from its parent album.

Recommended key behavior:

| Context | Key | Result |
| --- | --- | --- |
| Live Preview, Vim normal mode, eligible record | `==` | Open this record’s details editor |
| Record editor browsing | `j/k` or Up/Down | Move selected field |
| Browsing | Enter | Edit selected value |
| Browsing | `y` | Open this record’s Source at the selected field |
| Browsing | `u` | Preview guarded Undo of the last successful save |
| Any interactive surface | Tab / Shift+Tab | Ordinary accessible focus movement |
| Text/number/date input | Ordinary letters and arrows | Edit the input; never trigger browsing shortcuts |
| Single-line value stage | Enter / Save | Save after its matching successful validation preview |
| Choice search with an active suggestion | Enter | Accept the suggestion into the draft; a later Enter/Save commits |
| List editor | Enter on item input | Accept an item into the draft; explicit Save commits the field |
| Nested choice popup | Esc | Close popup first |
| Unsaved field stage | Esc / Cancel | Discard that staged value and return to browsing |
| Browsing | Esc / Close | Close and restore the invoking pane, cursor, and focus |

Use a visible **Clear value** action for optional fields. If retaining the familiar `Ctrl+D` gesture, expose it only in browsing, label it **Clear value**, and route it through the same staged save. It must never mean delete this field from the album. Do not hijack normal text-input editing keys.

Keep writes explicit. Blur, Tab, closing a popup, opening the card, and following a link never save. Normal valid field changes should need one explicit Save after editing, not a second ceremonial confirmation. Preview happens automatically and shows normalization, errors, and relevant consequences. If Enter arrives during preview, reuse the existing exact-revision latch; changing the draft clears it. An IME composition event never applies.

### Integrate `==`; do not add a competing listener

The supplied plan correctly identifies why a simple `nnoremap ==` cannot win against the built-in `=` operator. It proposes a capture-phase bridge that intercepts only the second unmodified `=` when Vim has precisely a lone pending `indentAuto`, then clears it with `<Esc>` before opening the card.

Retain that bridge and its negative cases: insert/visual/replace modes, Source mode, counted `N==`, register-prefixed forms, other pending operators, composition, repeat events, missing Vim APIs, and noneligible notes must retain native behavior. Reading view has no Vim `==`; its buttons and palette command are the equivalent access paths.

Extend the shared target resolver to a distinct `record` target and dispatch to the record entry point. Preserve album → album schema and `bank.md` → Bank setup. Use the record’s own path, not the parent path. An invalid record should receive a helpful record diagnostic, never fall through to editing its parent’s schema accidentally.

At the inspected bob-plugins SHA, the planned `248m-plugin-schema-double-equals.js` was not present. The plan itself contains both `album_only` and `records_too` decision alternatives. This report does not assume either has shipped. Coordinate with the final implementation of that bridge before changing it. The plan also explicitly excludes popout-window coverage; do not claim keyboard parity there without adding owner-document listeners and acceptance tests.

Preserve the existing **Edit album schema** command’s behavior from a record. It is an explicitly named route to the parent definition and remains useful. There is no need to broaden Ctrl+Shift+P or disturb Task Card precedence in this feature.

## Field semantics: render and edit what Bob actually supports

The current record kinds are text, choices, date, link, URL, and number, each optionally a list. This is not a general YAML form builder. There is no boolean record-field kind today; text such as `false` remains text. [Bob records contract, source snapshot](https://github.com/bobs-org/bob-cli/blob/f6924787fa43424d6fb217261adf264debbf2272/docs/records.md)

| Kind | Presentation and editor | Important constraint |
| --- | --- | --- |
| Text | Wrapping text; single logical value input that may visually grow | Literal content stays literal; never reinterpret numeric-looking strings or Markdown |
| Choices | Configured label/emoji; searchable picker in declared order | Store exact choice key; display label changes never change identity |
| Date | Unambiguous date with optional relative hint; date entry and calendar affordance | Bob resolves `today`/`yesterday`; preview shows the resolved ISO value |
| Link | Native internal-link behavior; note picker plus editable target | Preserve path, alias, and permitted fragment semantics; do not identify notes by display label |
| URL | Readable linked URL; URL input | Validate with Bob’s HTTP(S) rules, not a divergent JS validator |
| Number | Plain numeric value; input with bounds hint | Keep zero, finite decimals, and inclusive bounds; never use truthiness for presence |
| List variant | Ordered values/chips with add/remove controls | Save the ordered list as one field; do not flatten values into a comma-joined string |

Suggestions for `suggest: true` are optional assistance from the album’s existing value catalog, not a closed vocabulary. Preserve required/optional semantics. Defaults belong to creation: existing updates must not silently fill absent fields or reinsert a default after an explicit clear.

Preserve malformed and historical values in the read model. `null`, an absent key, an empty string, an empty list, the wrong scalar type, and an unsupported mapping are distinct states. The existing update planner’s `yaml_to_current` is intentionally permissive and can fall back to strings or no value; it is not a sufficient lossless inspection format for replacing Properties.

An unrelated existing defect should remain a warning while a valid field is repaired. The current record update contract already validates changed fields rather than refusing every edit until the whole old record is perfect. Preserve that useful behavior.

## Implementation architecture

### 1. Reuse the existing ownership boundaries

**bob-cli** owns album resolution, membership checks, field types, normalization, validation, record YAML edits, generated album indexes, concurrency checks, and inverse operations.

**bob-ledger-tools** owns rendering, focus, keyboard routing, temporary drafts, and presentation of Bob’s reports. It should not write frontmatter with `processFrontMatter`, invent its own YAML serializer, or implement the record validator in JavaScript.

Reuse the album data service for ordered schema metadata and invalidation. Add one record-details service keyed by canonical vault-relative record path, with shared in-flight requests and last-good results. Fetch details for mounted/open records; avoid rescanning the entire vault per row, repaint, or keystroke. Filter events to the record, parent schema, and required ancestors, and invalidate suggestions when their album changes.

### 2. Add a real single-record read contract

`bob records show TYPE` currently reports a **schema and common values**, not a particular record. Do not change that meaning or pretend it already supplies record state.

A proposed additive command is `bob records inspect PATH -f json` (exact name can be settled during implementation). It should return:

- Canonical record and album identities, structural membership, stored title/type/parent/created, and source location information.
- Ordered field definitions together with actual raw values, typed/display values where valid, explicit presence and validity states, and diagnostics.
- Extra frontmatter keys, with a safe representation of unsupported values.
- Schema fingerprint, record revision, and one opaque composite edit token.
- Capability information for editing and recoverable versus blocking failures.

It should return an informative diagnostic model for an invalid record or parent when possible, not disguise it as an empty record. Enforce path confinement and symlink safety and verify both the actual parent and immediate-folder membership. Do not infer the album from a folder prefix alone or classify every unfamiliar note type as an eligible record. The existing album-schema entry resolver has a broad legacy-type fallback; a record-value editor needs authoritative membership confirmation.

The read path must not write, repair indexes, create commits, or trigger sync. Preserve `show` unchanged; any public new options require short aliases and the repository’s CLI/help conventions.

### 3. Extend the record writer additively for guarded UI edits

The existing `records update` planner and span editor are reusable. They edit supplied YAML spans, preserve unrelated content, rebuild the album index, and guard disk preimages during installation. What they do **not** currently expose is a token representing the state the user originally inspected, or a server-produced Undo envelope. A dry run and a later independent update command can therefore each be internally safe while still overwriting a value changed between those commands.

Add a structured-envelope mode to the existing command, for example `bob records update ALBUM STEM -i - -f json`, without removing the existing `-s` and `-n` forms. The envelope should use a version, opaque `expect` token, and explicit set/clear operations. This is a proposed contract, not an existing CLI example:

```json
{
  "schema_version": 1,
  "expect": "opaque-record-and-schema-revision",
  "ops": [
    { "op": "field.set", "key": "status", "value": "ready" }
  ]
}
```

Pass the request through stdin and spawn an argv array. Do not construct shell commands from values. Represent ordered list members structurally so a comma in a member does not become accidental capture grammar. Keep explicit clearing distinct from a typed string or absent operation.

For the initial implementation, use a conservative composite token covering **canonical record/album identity, full record bytes, and semantic album-schema fingerprint**. The server should independently verify it before planning the apply and again through guarded installation. This allows the existing string-based guarded session to remain useful. Include the album’s current index and other read dependencies in the transaction’s preimage checks, even though unrelated index-only changes need not invalidate the user’s schema token.

This intentionally refuses an edit if someone appended Notes while the modal was open. That is a usability cost, but an understandable first-release safety rule: preserve the draft, show that the note changed, reload, and require a new Save. A later touched-field comparison strategy can accept unrelated body edits if real use demonstrates too many conflicts. Do not silently rebase initially.

Reuse the established album update transaction pattern for the UI path: maintenance lock, fresh planning after any pre-sync, guarded record-plus-index install, scoped commit, post-sync reporting, and safe rollback. The inspected record CLI calls the staged-file installer directly; that fact alone is not evidence that it already has the album schema writer’s complete commit/sync/result envelope. Add and test the missing transaction/result behavior rather than assuming parity from similar command names.

The result should expose before/after tokens, changed fields, typed errors, warnings, index changes, commit/sync state, and server-produced inverse operations. A post-sync failure after a successful local commit is **Saved locally; sync failed**, with Retry sync only. Never replay the mutation to retry publication.

Do not invoke the writer when opening, collapsing, or closing an unchanged card. Existing `records update` deliberately repairs a stale index even for a no-op record update; preserve that CLI behavior, but avoid turning a UI visit into an implicit repair.

### 4. Reuse the guarded session, with a record adapter

The plugin already has `createGuardedUpdateSession` in `242aa-plugin-guarded-update-session.js`; `createAlbumUpdateSession` is a thin wrapper. It tracks draft revision, expected fingerprint, vault generation, matching preview, editor-save barrier, lock retries, inverse Undo, and sync-only recovery. Reuse it rather than cloning the entire album modal or implementing a new save state machine.

The record adapter must supply both the record path and album path to the editor-save barrier. The generic controller currently calls `saveEditors([ownPath])`; the adapter can expand that set. Save/verify open buffers before inspection and again before apply. Detect divergent unsaved buffers instead of blindly making the last pane saved the winner. If a buffer save changes the input, retain the draft but invalidate its preview.

A successful Undo must reverse the changed values and the resulting index through Bob, using the last successful after-token. It must not restore an old whole note or overwrite newer Notes. Restore original absence and YAML representation where feasible through guarded server-generated span inverses, borrowing the album writer’s approach. Explicitly test repair-then-Undo of a historically invalid value: either safely support restoring that captured state with a visible warning, or clearly refuse that Undo. Never claim Undo worked while normalizing or dropping the prior value.

Keep modal drafts outside widget DOM and key them by field key and pane/session. A refresh may update status but must not recreate a focused input, move the caret, or erase a draft. Ignore superseded async responses. Closing or navigating during an already-started apply must not cause another apply or reopen a stale modal; the plugin-owned operation settles and reports its outcome.

### 5. Own placement and property suppression as one lifecycle

Existing album headers use Reading-view postprocessors and Live Preview decorations; both anchor after the first H1 and fall back after frontmatter. The new record surface should follow that model, with syntax-aware detection of the first real authored H1 outside fenced code and nested embeds. It must not require a new fence, marker, H2, or rewrite of existing records.

Canonical order is **H1 → Record details → optional subscription summary → authored content/Notes**. `241hg-plugin-bank-subscription-header.js` already inserts a subscription strip after the H1. Two independent after-H1 inserters would make order depend on render timing. Introduce an explicit record-header host/slot ordering or make the subscription host attach after the details surface. Give both Reading view and Live Preview the same rule. Preserve existing subscription timeline and financial calculations rather than duplicating them as generic fields.

For malformed notes without H1, fall back to the first body position after frontmatter, ahead of Notes when present, without creating a heading. Source mode remains unmodified. Embeds/hover previews must be scoped to their own source, with no leakage into the containing note; an initially read-only embed is acceptable.

Use a view-local marker applied only after successful mounting. Hide only that view’s in-document Properties, not every `.metadata-container` globally and not the sidebar. Remove the marker on mode switch, file switch, mount failure, unload, or loss of a usable model. Unknown data requires either a complete Other properties disclosure or a visible native fallback before suppression is allowed.

For a new multiline CodeMirror widget, use decorations supplied directly by a StateField if it changes vertical layout. Obsidian explicitly distinguishes state fields for layout-affecting decorations from viewport-based view plugins. Existing headers use ViewPlugin-provided inline widgets; reuse their lifecycle lessons, but do not blindly copy that implementation for an expanding interactive card. [Obsidian decoration guidance](https://docs.obsidian.md/Plugins/Editor/Decorations)

## Delivery boundaries and verification

The useful first release includes the complete read surface, all existing scalar/list kinds, typed editing, `==` integration, guarded save/Undo, native fallback, and subscription ordering. It does not need drag-and-drop schema arrangement, per-record layout configuration, arbitrary YAML editing, title/file renaming, album migration, or mobile writes.

Validate a vertical slice with the actual Zettel example first, then complete the remaining supported kinds before enabling Properties suppression generally. Reuse existing album/bank test infrastructure and scratch-vault writer tests; never use the live vault as a destructive test fixture.

Release acceptance should demonstrate:

1. **Presentation:** exactly one card after the real H1 and before Notes in Reading and Live Preview; sensible missing-H1 handling; no card in Source; no duplicate surface in splits or embeds; correct subscription ordering.
2. **Data fidelity:** schema order and labels; optional missing versus null/invalid; zero; literal `false` text; unknown choices; ordered lists; unusual quoted values; extra properties; no default insertion on viewing or updating another field.
3. **Keyboard:** actual Vim `==` opens once without reindent or an undo entry; negative cases preserve Vim; IME is safe; inputs keep normal text editing; Esc unwinds stages correctly; focus returns to the exact invoking pane.
4. **Typed writes:** each supported kind, list replacement, optional clear, required refusal, and unrelated pre-existing warnings behave like Bob’s record contract. A successful edit updates the album index atomically and leaves unrelated body/YAML bytes intact.
5. **Concurrency:** two panes, external CLI writes, dirty Source buffers, parent schema edits, record rename/delete, late preview responses, lock contention, and unload during apply cannot overwrite unseen work or duplicate saves.
6. **Undo and recovery:** original presence/quoting can return; stale Undo refuses; repair of invalid values has defined Undo behavior; local-save/post-sync failure retains the mutation and retries only sync.
7. **Failure accessibility:** absent executable, invalid schema, missing parent, first-load failure, stale cache, unsupported YAML, and plugin disable/unload leave a usable source/native route and never turn missing data into a blank successful card.
8. **Visual quality:** light/dark themes, about 375 px panes, long Claim text, long URLs, large choice lists, large schemas, zoomed text, and reduced motion. Use screenshots and a real Obsidian keyboard walkthrough; DOM stubs cannot prove Vim event precedence, focus survival, or widget placement.
9. **No presentation writes:** byte/hash comparisons show that rendering, navigating, refreshing, expanding, and canceling do not modify record or album files.
10. **Shared-component regression:** existing album Schema Card and Bank setup retain their keyboard, preview, Undo, Source excursion, and sync behavior after common adapters change.

For implementation, follow bob-plugins’ source-fragment build rules and deployment procedure. Add meaningful CLI and shared-session tests, run relevant existing checks, and deploy with `bob plugins sync` only when implementing the approved feature. This research has not deployed anything.

## Source map for implementers

These are directly inspected sources, not peer research. Paths are repository-relative so the report remains useful outside this workspace.

| Source | Relevant evidence |
| --- | --- |
| bob-cli `docs/records.md`, especially Schema, Updating notes, and bob records | Field kinds/order, reserved identity keys, creation-only defaults, partial validation, preserving untouched bytes, record/index writes |
| bob-cli `src/native/records/cli.rs`: `run_show`, `build_cli_update`, `execute_update`, `plan_album_write_for_record` | Schema-only `show`; existing update flags; disk snapshots; index planning and read guards; lack of session expectation input |
| bob-cli `src/native/records/plan.rs`: `PlanUpdateRequest`, `snapshot_currents`, `yaml_to_current`, `yaml_to_inputs` | Typed planning and limitations of using update projection as a lossless read model |
| bob-cli `src/native/records/render.rs`: `RecordUpdateRequest`, `apply_record_update` | Span-preserving mutation and typed refusals |
| bob-cli `src/native/capture/commit.rs`: `write_staged_files_guarded` | Preimage validation before staging and replacing; guarded multi-file installation |
| bob-cli `tests/cli/records.rs` | Existing create/update, capture equivalence, optional clearing, warnings, and preservation tests |
| bob-plugins `docs/albums.md`; `241u-plugin-album-header-model.js`; `241v-plugin-album-header.js`; `styles.css` | Album header, scoped property hiding, visual conventions, Reading/Live Preview lifecycle |
| bob-plugins `248a-plugin-bank-setup-model.js`; `248c-plugin-bank-setup-hosts.js`; `248l-plugin-bank-setup-card-entrypoints.js` | Bank Setup state handling, mounting, and common edit entry point |
| bob-plugins `242aa-plugin-guarded-update-session.js`; `242b-plugin-album-update-session.js`; `242a-plugin-album-update-service.js` | Reusable preview/apply/Undo state machine and mutation serialization |
| bob-plugins `241y-plugin-album-schema-card-dom.js`: `albumSchemaSaveOpenEditors`; `242e-plugin-album-yaml-excursion.js` | Editor-save barrier and pane-aware Source excursion |
| bob-plugins `242d-plugin-album-entrypoints.js` | Actual-parent album resolution; existing explicit parent-schema command; broad legacy-type classification to avoid blindly copying |
| bob-plugins `241hg-plugin-bank-subscription-header.js` | Existing record-level after-H1 surface that must compose with the new card |
| `plan:202611/double_equals_schema_keymap.md` | In-flight Vim bridge design, unresolved record alternatives, and popout limitation |
| Supplied screenshot; bob-cli `evidence/album-schema-finish-apply-final/shots/album-records-live.png` and `album-schema-375-dark.png` | Current record friction and established album visual/editor idiom |

## Recommended solution

**Implement an album-aware Record details card in bob-ledger-tools, backed by an additive bob-cli single-record inspection and guarded-update contract.** Place it after the authored H1, preserve the YAML and Notes, render values in schema order, and hide in-document Properties only while a complete, usable replacement is available. Reuse the existing modal, shared guarded session, Source escape, and visual tokens. Route record `==` to record values and expose parent-schema editing by an explicit separate action.

The feature is worth doing because it brings the album’s semantics to the place records are read and edited. Its success should be judged by how quickly the example record can be understood and safely changed—not by how many schema-editor controls can be copied onto it.
