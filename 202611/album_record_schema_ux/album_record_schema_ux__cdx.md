# Record settings that belong in the album: Obsidian rendering and editing

Independent research by **cdx**, 2026-11-12. This report uses the supplied screenshot, the `bob-cli-k3` epic and its approved plan, the local Bob source, and primary Obsidian/plugin documentation. No report, transcript, summary, or findings from the other researchers in this swarm were consulted.

**Recommendation:** Keep the nested `record:` mapping as the album's authoritative schema. Render it as a compact, expandable **Record settings** section in the existing album header, with a visible **Edit** action opening a focused form. Keep validation and writes in Bob. Make ordinary changes easy; treat changes to stored identifiers and existing data as explicit migrations. Extend the album work already underway instead of creating a generic nested-properties framework.

## What the evidence establishes

The screenshot shows `eat.md` with ordinary properties rendering normally and `record` displayed as an orange, truncated object beside a question-mark icon. That presentation is consistent with a nested mapping that Obsidian's native Properties UI does not support. It is not evidence that the stored YAML is malformed or that Bob wrote a JSON string. Changing the property to Text, quoting the object, or stringifying it would change its type and break Bob's schema reader. Obsidian's current help explicitly lists nested properties as unsupported and recommends Source mode for viewing them. It also assigns a property's type vault-wide by name. [Obsidian Properties](https://help.obsidian.md/properties)

An apparent counterexample deserves care: the Obsidian 1.10.3 announcement says the new **Bases List view** supports nested properties. That statement concerns a Base's presentation, not a schema editor in the note's Properties panel. It does not establish native editing support for this `record` object. [Obsidian 1.10.3 announcement](https://obsidian.md/changelog/2025-11-11-desktop-v1.10.3/)

The approved album plan deliberately chooses this structure. Album facts such as `summary`, `emoji`, and `index_by` remain ordinary properties; `record` contains the contract for the album's children. The schema and its records travel together through vault sync. The plan explicitly includes a **read-only schema card** and hiding `.metadata-property[data-property-key="record"]` on album notes. Thus part of the requested rendering fix is already planned. The new requirement is a usable authoring surface and its save semantics. Approved plan: `plan:202611/album_and_record_notes.md`, `plugins-albums` and album contract (audited read).

At the audited bead read, `bob-cli-k3.7`, “Obsidian album cards, live chips, and the album header,” was in progress. In the linked plugin checkout I inspected, the shared album report/sync service exists, but I found no album-header/schema-card implementation under the searched ledger-tools source and stylesheet. This describes that snapshot, not the current deployed Mac build or another worker's unlanded code. Coordinate with the phase owner before implementation; do not develop a competing header. [Epic](https://github.com/bobs-org/bob-cli--beads/blob/main/pages/bob-cli-k3/README.md)

Several implementation facts matter more than the visual defect:

- `record` is a mapping, with `noun`, `label`, `plural`, `dated_notes`, ordered `fields`, and `legacy`. Unknown schema keys produce errors. Fields and choices retain declaration order.
- A field supports text, choices, date, link, URL, or number; `list` is an independent dimension. It can also carry `label`, `required`, `suggest`, a typed `default`, and numeric bounds. `status` cannot have a default.
- Field keys and choice values are stored in child records. Labels are presentation. Editing one is materially different from editing the other.
- Storage shape for a shared property name must agree across record types. A change in one album can therefore affect another even if its own records validate.
- `bob albums list -f json` is a useful display projection, not a complete editing document. Its field payload omits defaults, suggestions, and numeric bounds. `bob records show -f json` is also lossy: defaults are display strings; it omits some schema options, explicit-versus-inherited state, and source formatting. Neither payload is safe to round-trip as the whole `record:` value.

These are verified in [schema parsing](https://github.com/bobs-org/bob-cli/blob/4835680dc5e8a09bc9ab3d4537160f0254670a65/src/native/records/schema.rs), [album reporting](https://github.com/bobs-org/bob-cli/blob/4835680dc5e8a09bc9ab3d4537160f0254670a65/src/native/albums/report.rs), [record schema reporting](https://github.com/bobs-org/bob-cli/blob/4835680dc5e8a09bc9ab3d4537160f0254670a65/src/native/records/cli.rs), and [the records contract](https://github.com/bobs-org/bob-cli/blob/4835680dc5e8a09bc9ab3d4537160f0254670a65/docs/records.md).

## Is the underlying idea good?

Yes. Keeping the record schema beside the collection it governs fixes a real ownership and sync problem. The epic documents earlier drift between configuration and record notes. Moving it back to host configuration to accommodate the Properties widget would sacrifice that benefit. Flattening every schema path into a property would create dozens of implementation-shaped rows and still leave dynamic field definitions, choice order, and typed defaults awkward to edit. A schema code block in the body would need new routing, parsing, and ownership rules without inherently providing a better form.

The weak point is the assumption that making configuration visible makes it usable. A large schema is useful when configuring an album, but rarely the reason to open `eat.md`. The primary activity is finding or adding a restaurant. The screenshot already devotes substantial vertical space to metadata before reaching the collection. A permanently expanded schema card could replace ugly clutter with attractive clutter.

The design should answer two different questions:

1. **Reading:** “What information does a restaurant record contain, and where do I change that?”
2. **Editing:** “How do I add a field or adjust a choice without damaging my restaurants?”

A small summary plus a deliberate form answers both. A generic YAML tree answers neither especially well.

This is worth building as a small album capability. It is not a good reason to build a universal form designer, a second schema registry, an alternative Bases implementation, or a migration engine for arbitrary vault references.

## The proposed experience

### On the album: one quiet, useful affordance

Use the album header being built by k3.7. Under the breadcrumb/title, show a single compact section:

```text
Body › Restaurants                                + Restaurant

▸ Record settings     Restaurant · 5 fields                Edit

Restaurants Kelly and I have tried, liked, or want to try.
...
Records
104 restaurants · 🔖 11 to try · 💚 86 liked · 🚫 7 not liked
```

“Record settings” describes the job better than the bare storage key `record`, and “Edit” is more discoverable than an icon or hover-only action. The disclosure expands an overview; it does not enter edit mode. The five fields and counts above come from the supplied example/approved plan and are illustrative, not newly measured live data.

Expanded, the overview is a restrained list:

| Field | What it accepts | Rule |
| --- | --- | --- |
| Status | 🔖 To try · 💚 Liked · 🚫 Not liked | Required |
| Category | Text | Required · Suggestions |
| Location | Text | Required · Suggestions |
| Visited | Date | Optional |
| URL | Web address | Optional |

Below it, “New notes include a date.” Use labels in the overview; reveal stored keys in details, not as the leading typography. Limit long choice lists to a few chips and “+N more,” with a keyboard-accessible expansion. “Required” should be understandable without knowing what an asterisk means. Keep overview collapse state local to the view/session; never write it into frontmatter.

On a new album with no fields, show **“No custom fields yet”** and **“Add a field”**. An empty `fields` mapping is valid. Do not imply that a restaurant schema or a status field is mandatory for every album.

The raw `record` property may be hidden only while a corresponding display or actionable error state is successfully mounted for that album. Do not globally hide every property named `record`, hide all Properties, or apply a vault-wide type override. Source mode always exposes the original YAML. When Properties are hidden by the user's preference, the header's settings action still exists.

### Entering the editor

Provide three entry points to the same dialog:

- **Edit** in Record settings.
- A command-palette action, **Bob: Edit album record settings**. Make it assignable; do not seize an existing hotkey.
- A note-menu action. From an individual record, offer **Edit this album's record settings…**, explicitly naming the owning album.

The dialog title is **Record settings · Restaurants**, with a sentence: **“These settings apply to every restaurant in this album.”** This prevents confusion with editing one restaurant's `status` or `visited` value. Editing individual record values is outside this feature.

Use one medium-width Obsidian modal, approximately 680–760 px on a wide window, constrained to the viewport. On narrow windows, use a single-column layout with a reachable footer. A modal is preferable to a tiny popover for an ordered schema and preferable to an always-open sidebar for an occasional bounded task. Use the existing plugin's native controls and styling rather than introduce a UI framework solely for this feature.

### Form organization

The initial view has a short general section followed by ordered, collapsible field rows. Expand only the field being edited; adding a field expands its new row immediately.

```text
Record settings · Restaurants
These settings apply to every restaurant in this album.

Display name       [Restaurant                          ]
Plural             [restaurants                         ]
Date new notes     [on]

Fields                                           + Add field
  Status       Choices · Required                            ›
  Category     Text · Required · Suggestions                 ›
  Location     Text · Required · Suggestions                 ›
  Visited      Date                                         ›
  URL          Web address                                  ›

Advanced ▸

                                      Cancel      Save changes
```

Suggested field controls:

| Control | Behavior |
| --- | --- |
| Name | Human label. Safe to edit without renaming stored properties. |
| Property key | Suggest once from a new field's name; show the final key before creation. Keep existing keys read-only in the ordinary form. |
| Accepts | Text, Choices, Date, Note link, Web address, Number. Do not offer schema types Bob does not support. |
| Multiple values | Maps to `list`. Separate from the value kind; changing it on an established field needs compatibility checks. |
| Required | Explain existing missing values if turning it on. Turning it off should be easy. |
| Suggest existing values | Clear language for `suggest`; preserve the current contract's supported behavior. |
| Default | A control matching the value kind, plus “No default.” Lists get ordered items. Hide/refuse it for `status`. |
| Minimum / Maximum | Shown for Number only; inclusive. |
| Choices | Ordered rows with a visible label and a smaller stored value. Add/reorder using accessible buttons; dragging may supplement them. |

For example, changing **“💚 Liked”** to **“💚 Would return”** changes the label; the stored value remains `liked`. The existing record files remain untouched. The form should make that consequence visible in its change summary. A new choice suggests a key, but does not keep changing that key as the label is subsequently edited.

Include the following details because they prevent subtle data changes:

- Show inherited label/plural defaults as placeholders or an explicit “Automatic” state. Opening and saving must not materialize every implicit default.
- Distinguish no default, an explicit empty value where allowed, `false` as text, zero as a number, and an empty list. Do not serialize every form input as a string.
- Explain that defaults affect subsequent writes where the field is absent; they do not backfill existing records. “Date new notes” also does not retroactively date old prose.
- Field order affects capture presentation and, without `status`, can change which choices field groups the index. Choice order changes group order. Preview that effect rather than describe ordering as cosmetic.
- Preserve `legacy` and advanced options even when the ordinary form does not edit them. Display them in Advanced with an explanation and access to source.
- Keep album `parent`, `emoji`, `summary`, `index_by`, and `index_facets` in their existing places. The settings dialog may explain grouping and flag a dangling field reference, but should not silently absorb every album property into a new editor.

### Save, cancel, validation, and failure

Use **explicit Save**, not autosave. Every intermediate form state remains a draft; incomplete typing must never publish an invalid schema to capture or sync. No changes means Save is disabled and no write occurs.

Validate quick local input immediately, but let Bob decide semantic validity. Show errors next to the affected control, with a short summary linking to the first error. Preserve the draft on errors. Avoid a succession of transient notices for each keystroke.

For ordinary edits, show a compact footer result such as **“1 choice label changed · existing values unchanged.”** Save remains one deliberate action, with no second confirmation for a simple label or optional-field addition. The actual save must revalidate; an earlier green preview is not a guarantee.

For constraints affecting existing records, show an impact result before saving:

```text
Visited would become required.
18 existing restaurants have no value. No changes saved.
View affected records                       Keep optional
```

That count is illustrative. The implementation must derive counts from a complete scan of the relevant records, never from the current visible rows or a partial report. Do not automatically fill defaults into those notes.

Cmd/Ctrl+Enter saves a valid draft; Escape cancels a clean dialog or asks to discard an actual dirty draft. Restore focus to the originating action after closing. All fields and reorder actions must work by keyboard; accessible names cannot depend on tooltip hover. A save-in-progress state must prevent duplicate submissions.

When the schema is broken, display **“Record settings need attention”**, the concrete error, and **Fix settings / Open YAML**. If Bob can represent the problem safely, open the form at that field. For malformed YAML or unsupported shapes, open Source mode at the diagnostic line and retain the form draft for copying. Never replace an unparseable schema with a blank template.

When the backend is unavailable or too old, keep the last successful overview visibly stale, make source available, and explain why guided saving is unavailable. Never present a stale card as a healthy current schema.

### Visual quality

Use the existing notebook/album typography, spacing, borders, and owner hue. A subtle accent and familiar choice icons are enough. Avoid a second oversized colored callout above the Records callout, a rainbow of field-kind badges, or repeated counters in both settings and the collection header.

Use Obsidian theme variables, readable secondary text, clear focus rings, and layouts that wrap at narrow widths. “Edit” stays visible; detail is progressively disclosed. Screen-reader status should announce “Saved” or a validation failure without moving focus unexpectedly. Avoid motion beyond a restrained disclosure transition and respect reduced motion. Obsidian's developer guidance recommends its theme variables for components that adapt across themes. [HTML elements and styling guidance](https://docs.obsidian.md/Plugins/User%20interface/HTML%20elements)

## Implementation architecture

### Build on the existing album service

`bob-ledger-tools` already has a shared, version-checked album report and sync service with subscriptions, request coalescing, invalidation generations, and a three-second sync debounce. Use it for the overview and refresh. Do not spawn a fresh vault scan for every rendered row or every view. Its notebook header has separate Reading and Live Preview implementations and leaves Source mode alone; that is the relevant rendering precedent. [Album service](https://github.com/bobs-org/bob-plugins/blob/564f3c1087e3bf1f4a03854a15e905e08c253301/plugins/bob-ledger-tools/src/241m-plugin-album-data-service.js), [notebook header](https://github.com/bobs-org/bob-plugins/blob/564f3c1087e3bf1f4a03854a15e905e08c253301/plugins/bob-ledger-tools/src/241f-plugin-notebook-header.js), [Live Preview implementation](https://github.com/bobs-org/bob-plugins/blob/564f3c1087e3bf1f4a03854a15e905e08c253301/plugins/bob-ledger-tools/src/241g-plugin-notebook-header-live.js)

The public Obsidian API declaration I inspected includes Markdown processors, editor extensions, modals, view actions, and frontmatter/file processing. I found no public custom Properties-type registration API there. That is a scoped source finding, not a claim that native-row customization is impossible. A private Properties registry integration would need compatibility maintenance and could compete with other plugins. [Inspected API declaration](https://github.com/obsidianmd/obsidian-api/blob/879c936660fcc45c90ee28ea6b4ef7068006477c/obsidian.d.ts)

Prefer supported rendering extension points for the actual card and modal. Isolate the small native-row hide/reveal adapter. It is still coupled to Obsidian DOM conventions and must be tested as such. If it cannot find or safely identify the row, leave the raw row visible; the command and header action continue working. Do not hide the row based solely on cached metadata when the active editor's current text no longer describes an album.

For the Properties sidebar, the first release can leave the native representation available alongside a note-menu action. If sidebar parity is required, add the same compact launcher only when the target file is unambiguous. A sidebar or pop-out associated with another file must never edit the active file by accident. This is a documented limitation, not permission to globally suppress the property.

### Add an editing contract, not another display projection

Bob should provide three logical operations: **inspect**, **preview**, and **apply**. These are proposed capabilities, not existing command names. A public `bob albums` extension is a reasonable home because the membership rule is albums; exact command/option design should follow the CLI rules. Do not add subcommands to `bob capture`.

| Operation | Required result |
| --- | --- |
| Inspect | Exact album identity, complete ordered schema, explicit/implicit values, raw/source preservation information, diagnostics, and a revision token. Works usefully for a broken schema. |
| Preview | Apply an ordered set of requested operations to the inspected revision in memory; return validation, existing-record impact, affected index grouping, and a diff. No mutation, Git, or sync. |
| Apply | Re-read and verify current inputs under the established write discipline, revalidate the draft, then save the schema and its derived index together. Return the resulting revision and precise write/sync outcome. |

Send structured requests through stdin or an equivalent framed subprocess interface, with a versioned JSON envelope and argv-based spawning. Never interpolate field labels or YAML into a shell command. Arrays should carry field and choice order explicitly. Preserve the original schema and apply changes to it; do not regenerate a complete schema from the current `albums list` or `records show` display objects.

Reuse `parse_album_record_schema`, the vault-aware registry, record checks, and the existing host-catalog/index planner. The UI may detect an empty label immediately, but should not implement a parallel Rust parser in JavaScript or duplicate cross-album compatibility rules.

### The writer is the critical part

For this repository, a controlled Bob writer is preferable to immediately assigning a JavaScript object through `processFrontMatter`. Obsidian exposes that method as an atomic frontmatter read/modify/save and generally recommends it to plugin authors. However, an object-based API does not promise to preserve comments or exact YAML spans. Bob already has a concrete precedent: the parent-property planner explicitly avoids whole-frontmatter serialization because it can rewrite other keys, including unquoted wikilinks. [Obsidian plugin checklist](https://docs.obsidian.md/oo/plugin), [Bob parent-span planner](https://github.com/bobs-org/bob-plugins/blob/564f3c1087e3bf1f4a03854a15e905e08c253301/plugins/bob-navigation-hotkeys/src/211-parent-frontmatter-plan.js)

The recommended write guarantee is:

1. Opening, viewing, expanding, previewing, and cancelling produce zero vault writes.
2. Ordinary edits preserve every byte outside the intended schema spans and Bob's already-owned index region. Preserve untouched schema entries and comments as well.
3. New fields use canonical block YAML. Existing flow-style schemas remain readable. If an operation requires normalizing a flow-style region, preview the precise affected region and require that normalization to be visible in the change summary; never silently normalize the whole frontmatter.
4. Ambiguous YAML, duplicate mapping keys, anchors/aliases, or tags that the span editor cannot preserve safely cause a typed refusal and source fallback. Do not guess at a substring boundary with a regex and overwrite it.
5. A no-op Save is byte-identical, produces no commit, and triggers no sync.

This requires extending the existing span-editing discipline to nested schema edits. It is new work, not something `records update` already provides for album configuration. A syntax-aware parser with locations or a deliberately bounded, well-tested span planner is preferable to hand-assembling YAML from UI strings.

Reuse the maintenance lock, input guards, and scoped commit/sync pattern. Schema changes affecting labels or grouping should regenerate the album's `[!records]` region in the same write set. They need not rewrite child records or owner notes. Never overwrite a damaged generated region to force success. If the index cannot be safely updated, refuse the dependent save and retain the draft with the concrete reason. [Album sync guards and transaction](https://github.com/bobs-org/bob-cli/blob/4835680dc5e8a09bc9ab3d4537160f0254670a65/src/native/albums/sync.rs)

There is an important concurrency boundary: a Bob lock does not lock Obsidian's unsaved editor buffer. Before backend Apply, flush the relevant open document using a supported save path, verify disk and editor revisions, and guard the full album preimage plus the member frontmatter and cross-album declarations on which validation depended. If an intervening edit occurs, refuse and retain the draft rather than overwrite. Ensure the post-save editor cannot subsequently flush an older snapshot back over the saved schema. Verify this behavior in actual Obsidian, with two panes and a delayed save; shell-only tests cannot prove it.

The public `Vault.process` API protects an Obsidian read/modify/write cycle, but does not by itself establish a transaction covering Bob's subprocess, record inventory, and Git sync. Do not confuse those guarantees. If the proposed backend/editor coordination cannot pass the race test, resolve that ownership design before enabling writes. [Obsidian Vault guidance](https://docs.obsidian.md/Plugins/Vault)

After success, invalidate the shared album/schema caches, coalesce the plugin's delayed sync, and prevent repeated save loops. If the local save succeeded but publishing/sync failed, report **“Saved locally; sync failed”** and offer a sync retry. Do not repeat the schema mutation. Provide a guarded “Revert this settings change” action backed by the before/after revision, or the existing scoped history path; do not promise that ordinary editor Undo necessarily reverses a subprocess write.

## Scope: easy changes versus migrations

The first release should be genuinely useful without taking responsibility for every possible schema transformation.

| Change | Recommended initial behavior |
| --- | --- |
| Change a label or plural; toggle date-new-notes | Normal Save; explain prospective effects. |
| Add an optional field or choice | Normal Save after validation and compatibility checks. |
| Reorder fields or choices | Save with grouping/order consequences shown. |
| Change default, suggestions, or numeric limits | Validate typed configuration; evaluate any existing-record impact. |
| Make an existing field required or narrow accepted values | Save only if complete validation proves no new invalid records; otherwise explain and retain draft. |
| Rename existing field keys or stored choice values; change noun | Keep out of ordinary editing; explain that identifiers require migration. Labels remain editable. |
| Remove a field/choice currently used; change scalar/list shape or stored kind incompatibly | Block the ordinary save. A future migration flow must show affected files and explicit remapping. |
| Remove an unused choice or field | Allow only after proving it is unused and not referenced by defaults, grouping/facets, or other known dependencies; otherwise defer to migration/source. |

Treat user-authored Bases, external queries, templates, and scripts as potential consumers of stored keys. Bob cannot credibly promise to discover every reference. This is another reason to protect established identifiers in the first release. Do not mass-rewrite `.base` files just because a display label changed.

Do not force Bryan to fix every unrelated warning before changing one harmless label. Compare before/after findings on readable existing records and block newly introduced failures, while always requiring the proposed schema itself to be valid. Incomplete discovery is not proof of safety. Broken-schema repair needs a separate initial state: parse the raw declaration, preserve unsupported parts, and clearly distinguish successful schema repair from remaining record-health findings.

## Alternatives considered

| Approach | Benefits | Why I would or would not choose it |
| --- | --- | --- |
| Source mode or a syntax-highlighted YAML modal | Minimal work; full expressive power; essential recovery tool | Good fallback or interim release. It still requires schema and YAML knowledge and gives poor guidance about existing data. |
| Generic nested-object Properties renderer | Keeps everything in the native row | A tree of `fields → status → values` exposes the storage model. Private APIs and native keyboard behavior increase maintenance cost. Unnecessary for one domain. |
| Flatten schema into top-level properties | More native controls | Major model change; many rows; awkward ordering and typing; conflicts with the accepted album contract. |
| Metadata Menu / FileClasses | Existing nested object and field-editing support | A credible generic solution, but Bob would need an adapter or a second field-definition system. It does not automatically inherit Bob's constraints, transactions, or migration rules. |
| Meta Bind controls | Can bind directly to nested property paths | Useful for a few fixed controls or a prototype. A variable ordered map of fields and choices plus validated Save still needs custom orchestration. |
| Bases | Good for browsing/editing record values | It solves the child-data surface, not authoring the album's schema. Retain the existing linked Base. |
| Album-specific summary and form | Matches the user's task, reuses existing header/service, keeps one schema | Recommended. Costs a real editing protocol and careful write coordination, but directly addresses the hard parts. |

Metadata Menu documents Object/ObjectList/YAML controls and fileClass-specific field definitions. Meta Bind documents nested dot/bracket bind targets; its bind targets are static unless additional JavaScript is used. These establish feasibility for generic controls, not Bob-specific correctness. I did not install or benchmark these plugins. The conclusion that an album-specific form is a better fit is design judgment. [Metadata Menu fields](https://mdelobelle.github.io/metadatamenu/fields/), [FileClasses](https://mdelobelle.github.io/metadatamenu/fileclasses/), [Meta Bind bind targets](https://www.moritzjung.dev/obsidian-meta-bind-plugin-docs/guides/bindtargets/)

## Changes I recommend to the requirements and existing plan

1. **Define “render properly” semantically.** The result should be a readable record-settings surface in Reading and Live Preview, not necessarily a custom native property type. Keep Properties/sidebar and Source fallbacks explicit.
2. **Change the read-only schema card into a compact overview with editing.** Default collapsed, visible Edit, expandable field summary. This preserves the album's focus on its records.
3. **Add a correctness contract for saving.** Preview, canonical validation, revision guards, no-op identity, preservation of untouched YAML, and recovery are part of this feature, not later polish.
4. **Bound ordinary editing.** Make safe changes easy; do not imply that changing a stored key is the same as renaming a label. Full migrations can be a separate feature with explicit scope.
5. **Replace the plan's serialization assumption.** The risk table says canonical block YAML makes Properties reserialization a no-op. Matching formatting style does not establish that. Preserve bytes with the chosen writer and verify native Properties edits separately; hiding a row does not change Obsidian's serializer.
6. **Require recovery before hiding.** Invalid data, missing Bob, unexpected DOM, plugin disable/unload, and unsupported newer schema must never leave a hidden, inaccessible contract.
7. **Scope platform support honestly.** Prioritize the desktop setup shown in the screenshot. The existing service launches `bob`; mobile guided writes require an explicit backend strategy. Source viewing and native fallback should remain possible there. Do not silently invent a second JavaScript writer for mobile.

These changes preserve the epic's storage and ownership decisions while adding a manageable authoring surface. They intentionally do not add per-record forms, automatic record migrations, new schema kinds, an album designer, or a new sync mechanism.

## How to validate the implementation

Start with a short compatibility spike against the actual installed Obsidian build: mount the compact header in Reading and Live Preview, hide/reveal only the intended row, open the modal from each entry point, and demonstrate editor/subprocess save coordination. This should precede most form polish because it addresses the greatest implementation uncertainty.

Then implement the complete edit document and guarded writer before wiring live Save. An intermediate renderer plus “Open YAML” is useful, but should not be declared fulfillment of the “very easy to modify” requirement.

Acceptance should include:

- **Usability:** without YAML or a terminal, change a choice's label, add an optional URL field, and reorder choices. The user sees which part is stored versus displayed and can cancel without effects.
- **Preservation:** label edits leave stored tokens, record files, unrelated frontmatter, prose, comments, and line endings intact. No-op and cancelled edits are byte-identical. Typed/list defaults and advanced options survive a full editor round trip.
- **Schema safety:** duplicate keys, reserved field names, invalid defaults, `status` defaults, numeric bounds, list/scalar conflicts, cross-album shape conflicts, malformed YAML, and dangling `index_by`/`index_facets` references receive precise outcomes.
- **Existing data:** adding a required field or removing an in-use choice does not silently invalidate children. Pre-existing unrelated issues are distinguished from new ones. Unreadable inventory refuses claims of compatibility.
- **Concurrency:** two dialogs, two panes, unsaved source edits, a background record capture, schema changes on disk during preview, file rename/deletion, and sync during save cannot clobber data. Retry never duplicates a saved mutation.
- **Derived state:** affected index bytes update with the schema; capture/completion see the new definition; no unrelated owner notes or authored Bases change; repeated synchronization becomes a no-op.
- **Presentation:** light/dark themes, a narrow pane, large text, keyboard-only use, screen-reader labels, Properties hidden/visible, source mode, Properties sidebar, and pop-out windows. Disabling the plugin restores the native row and removes listeners/widgets.
- **Failure:** timeout, missing/old Bob, invalid JSON version, disk failure, and sync failure retain a recoverable draft and accurately distinguish “not saved” from “saved locally.”

Use backend fixture/transaction tests for correctness and the plugin's existing model/DOM harnesses for rendering state. Perform real Obsidian interaction tests for Properties DOM, focus, mode transitions, and buffer races. Screenshots should verify the actual UI, not serve as evidence that transactional behavior works. No implementation or runtime Obsidian prototype was performed for this research report.

## Evidence and confidence

The input screenshot was inspected at `/home/bryan/tmp/screenshots/20261112_054646.png`. The epic was read through `sase bead read bob-cli-k3`; its plan was read through `sase artifact read plan:202611/album_and_record_notes.md`. Source inspection was pinned to bob-cli `4835680dc5e8a09bc9ab3d4537160f0254670a65`, bob-plugins `564f3c1087e3bf1f4a03854a15e905e08c253301`, and the public Obsidian API `879c936660fcc45c90ee28ea6b4ef7068006477c`. Linked/external repositories were opened through `sase repo open`. Official web documentation was checked during this investigation; the links above support the claims beside them.

Confidence is high that the current native property mismatch, existing plan overlap, and lossy display-payload risks are real. Confidence is high in retaining one album-owned schema. The exact rendering adapter, editor flush/reload behavior, and smallest safe nested-YAML writer require the proposed implementation spike. The screenshot does not reveal the installed Obsidian version, plugin deployment state, or underlying YAML bytes, so this report does not assert those details.

## Recommended solution

**Extend the existing Bob album header with a compact Record settings overview and one focused, keyboard-friendly editor. Keep `record:` as nested YAML. Let Bob validate and apply explicit changes through a complete, revisioned editing contract, preserving unrelated text and rebuilding the affected index. Make labels, choices, and additive fields easy; reserve incompatible identifier/data changes for a deliberate migration workflow.**

Ship the readable overview and useful editor together, with source recovery always reachable. This gives Bryan a calm album page for daily use and a trustworthy place to change the collection when needed, without paying the cost of a generic properties platform or abandoning the album model.
