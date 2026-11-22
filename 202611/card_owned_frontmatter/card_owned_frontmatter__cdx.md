# Property cards as the frontmatter interface

Independent research by **cdx**, 22 November 2026. Prepared for the property-card design decision. No other researcher's report, transcript, findings, or summary was consulted. This is research, not an implementation or a live-vault migration.

## Assessment

**This is a good direction, provided “taking over” means owning the interface while preserving the file format and existing write rules.** A note should have one coherent header. Bob already gives selected frontmatter a richer presentation, so leaving the rest in a separate native Properties block splits attention and makes the card feel incomplete.

The collapsed inspector is a particularly good compromise: the card stays readable, but every authored property remains discoverable. A dedicated editor can improve the experience through immediate field search, predictable keyboard navigation, contextual validation, and reversible changes. The danger is treating this as a CSS cleanup. Replacing the native editor creates obligations around value types, metadata type declarations, unknown YAML, concurrent writers, and recovery.

I recommend a **shared All properties drawer and shared Properties editor in Bob Ledger Tools**, retaining the specialized card editor behind `==`. The generic editor must route domain-owned fields through their existing writers. It must not become a second, less constrained way to change album schemas, bank configuration, record membership, or summary provenance.

## What the current implementation makes possible

Code was inspected at bob-cli commit `b7945e75d038506675de04f06bac826990db3d27`, bob-plugins commit `9b4bc2ca3b2c72c30538739b029dca705ee9f131`, and public Obsidian API commit `737629a51f6b4d30f8336fa3d38f3df006e322d4`.

| Existing behavior | Consequence |
| --- | --- |
| Shared property ownership marks selected native rows within the exact Reading/Live Preview container. Generation-bound handles prevent stale releases from clearing newer owners. | Extend this to whole-container ownership; do not hide every `.metadata-container` globally. [C1] |
| Album ownership currently names `record`; bank ownership names `bank`. Record cards hide schema fields under capability/health gates. | Taking over all frontmatter is a contract change, not simply adding `parent` and `created` to a list. [C1], [C3] |
| Day/period cards hide seven intention/provenance keys only while relevant content exists. Identity-only cards retain native Properties. | The shared drawer must also work on empty day/period cards; its ownership cannot depend on authored intentions. [C4] |
| Record cards already have an “other properties” fold and an `added …` footer. Identity/schema keys are excluded from the fold. Fully collapsed record bodies return before rendering the created footer. | Replace the fold with a complete shared drawer. Lift created presentation into shared chrome so it survives both kinds of collapse. [C3], [C9] |
| `==` intercepts the second key after Vim enters the `indentAuto` operator; it is not a simple vimrc mapping. | Extend this dispatcher for `-` and `+`, preserving its count, register, mode, composition, and duplicate-event guards. [C2] |
| Existing editors use guarded update sessions with pane saves, stale-generation handling, lock waits, and inverse-operation Undo. | Reuse these services and domain writers. A generic arbitrary-property writer is still new work. [C5], [C10] |
| Rust has shared YAML span primitives and a verified intention writer. | There is a preservation foundation, but no universal YAML editor to simply expose. [C6], [C11] |

The public API exposes `FileManager.processFrontMatter`, `Vault.process`, and metadata-cache access. The inspected declarations do **not** expose a supported native Properties-widget constructor or general metadata-type manager. This is a finding about those declarations, not proof that Obsidian lacks internal implementations. Transplanting its native editor or depending on undocumented type mutation therefore carries compatibility risk. [O3]

I ran the existing equals-dispatch tests (**29 passed**) and property-ownership tests (**13 passed**). They confirm the baseline mechanisms and their negative cases, not the proposed UI. I did not run a new Obsidian end-to-end session, audit live-vault properties, or test a mobile prototype.

## Adjustments to the requirements

1. **Hide native in-document Properties only while its replacement is healthy.** In supported desktop Reading/Live Preview views, the complete block—including heading and Add property—disappears. Source mode, failed mounts, unsupported contexts, and plugin disable retain/restore native access. This deliberately qualifies “completely”: recovery is part of reliability.
2. **The drawer contains all authored frontmatter, including fields summarized above.** Call it **All properties**, not Other properties. Duplication inside an intentionally opened inspector is useful: users should not have to infer where a key went.
3. **All properties are visible, but edit mechanisms differ.** Ordinary keys receive typed editing. Domain fields use specialized editors or shared domain stages. Generated metadata has explanations and repair/source routes. This narrows a literal “everything is freely editable here” interpretation to preserve Bob's invariants.
4. **Keep `==` for the existing card editor.** `=+` opens Properties; it does not mean Add property. Give both actions explicit visible labels so improving the inspector does not displace a familiar domain workflow.
5. **Created reflects the stored property only.** Never manufacture it from filesystem creation time, the date a daily note represents, or Git history. Missing values can show a quiet `Created —`; malformed values show `Created ?` with an explanation. Display never writes a timestamp.
6. **Initially cover existing supported card hosts.** Do not silently expand this into cards for all areas, projects, references, notebooks, embeds, bank fences, and mobile views. A card rendered inside an embed must never suppress the host note's properties.
7. **Define parity as a checklist.** A release delegating global property-type management to native tools must say so. Better everyday ergonomics does not mean the entire vault-wide property system has been replaced.

The first, third, and seventh are material compromises. I would accept them for an interface that remains trustworthy on an unusual note.

## Card design

Keep the species tile, title, accent, principal content, and navigation rail as the visual hierarchy. Append a quiet metadata footer **after the existing rail**, placing the requested section literally at the card's bottom. It belongs inside the same border, not in another floating panel.

Conceptual layout, not a pixel-accurate prototype:

```text
┌─────────────────────────────────────────────────────────┐
│ [species] RECORD · Eat                                   │
│ Pho House                                    Edit fields │
│ … curated record content …                              │
│ ‹ Previous                    Eat · 3/104          Next ›│
├─────────────────────────────────────────────────────────┤
│ Created Nov 20, 2026   ▸ All properties · 8    Edit   =+  │
└─────────────────────────────────────────────────────────┘
```

Expanded:

```text
│ Created Nov 20, 2026   ▾ All properties · 8    Edit   =+  │
│ type         [[record]]                                  │
│ parent       [[eat]]                                     │
│ title        Pho House                                   │
│ created      2026-11-20T10:34:00-05:00                     │
│ status       To try                                      │
│ tags         restaurant · nearby                         │
│ rating       0                                           │
│ notes        Empty text                                  │
```

Use existing card spacing and typography tokens. A thin separator and restrained background change suffice. Avoid a pill for every primitive or a competing colored box around each row. Keys must be exact and readable; values deserve more width. On narrow cards, stack key over value and wrap the footer. Keep species words and readable state labels; color alone conveys no essential meaning.

The drawer contract:

- Start collapsed in a new pane/file view. Retain state across repaint and mode changes for that pane's current file; reset on navigation to a different file. Store state in memory, not frontmatter.
- Remain independent of the main card-body collapse. A compact record card retains the footer; `=-` opens properties without expanding its curated content.
- Preserve authored top-level order. Filtering changes the displayed subset, never the source. Count actual top-level entries, excluding absent schema suggestions and nested descendants.
- Distinguish absent, null, empty string, empty list, `false`, and `0`. They must not disappear through truthiness checks or become indistinguishable dashes.
- Render links with normal navigation, tags with search, booleans as read-only state, and long text with expand/copy. An inert boolean must not look like an enabled write control.
- Render objects and complex lists as read-only trees with compact summaries and a verbatim YAML option. Never show `[object Object]`, drop them, or evaluate expressions.
- Include generated and legacy keys. “Managed by Bob” explains a field but does not remove it from the inventory.
- With no properties, show `All properties · 0` and Edit. Invalid/unclosed frontmatter shows a diagnostic and source route, never a misleading empty inventory.

Use a semantic definition list and a real disclosure button with visible focus, `aria-expanded`, an associated content region, and Enter/Space behavior. Collapsed content leaves the focus order; collapsing while focus is inside returns it to the disclosure. These match the [W3C disclosure pattern][O4]. `=-` retains the editing cursor and scroll position; if the footer is offscreen, reveal it with only the necessary scroll.

### Created presentation

Use **Created Nov 20, 2026**, shortened to **Created Nov 20** in the current year, with the complete stored value available on focus/click and in the drawer. `Created today · 10:34` is reasonable for recent timestamps. Prefer Created over the record-specific “added” when sharing the component across species.

Date-only values are calendar dates: do not parse them as UTC instants and shift their day. Offset timestamps may display locally, but details retain the stored offset/value. Floating timestamps have no known zone; do not invent one. A calendar note's creation date differs from the date it represents. Invalid/future values remain inspectable instead of silently normalized. Refresh relative labels at the local date boundary without writing or launching bob.

This also fixes a current presentation gap: the record-created footer sits inside the expanded body. Shared created chrome belongs outside it. [C9]

## Properties editor

`=+` opens a compact labelled modal in the existing Bob editor visual language. Its header names the note. Begin in a focused browse list, with a visible filter and Add property button. Do not autofocus a value field and turn the next navigation key into an edit. Reopen on the last selected key when it still exists.

```text
┌ Properties · Pho House ──────────────────────────────────┐
│ Find property… /                            Add property │
│                                                         │
│ › rating       0                  Number                │
│   status       To try             Album field           │
│   parent       [[eat]]             Record membership     │
│   created      Nov 20, 2026        Date & time           │
│                                                         │
│ ↑↓ / j k move   Enter edit   / find   … actions   Esc close│
└─────────────────────────────────────────────────────────┘
```

Opening a field creates a stage within that modal. Keep name, type, and validation visible. Link/tag/choice controls offer filtered completion; text stays text unless the user explicitly converts it. Ordinary values should not require raw YAML.

Use **one field edit as one transaction** initially. Enter commits a single-line value; multiline text uses Mod+Enter. A list stage commits the complete list once, preserving item order. Opening, filtering, blur, changing control focus, and closing do not write. After success, return to the selected row, show Saved and Undo, and keep the modal open. This fits the record-editor model and avoids pretending that sequential calls to multiple domain writers are an atomic Save all. [C5], [C10]

Escape from an edited stage backs out and retains the draft for the modal session; show Draft and an explicit Discard action. Closing with an unsaved draft asks Save/Discard/Keep editing. Escape, `q`, and Ctrl+[ share the same layered dispatch, with `q` typing normally in text controls. This follows the project decision read via `sase memory read decisions:q-and-ctrl-bracket-mirror-esc`; do not invent another close convention.

| Context | Keys | Proposed behavior |
| --- | --- | --- |
| Browse | Up/Down, j/k, Ctrl+P/N | Move selection; letter commands apply only outside text controls. |
| Browse | `/` | Focus filter; Escape clears/exits filter before closing. |
| Browse | Enter or `e` | Open value stage or its labelled specialized editor. |
| Browse | `a` | Add property: name completion, explicit type, then value. |
| Browse | `r` | Rename ordinary local key, checking collisions. |
| Browse | actions menu | Remove, convert, reorder, copy, open YAML, specialized editor; all keyboard reachable. |
| Value stage | Enter / Mod+Enter | Save single-line / multiline value. |
| Any layer | Escape / Ctrl+[; `q` outside text | Back out one layer through one handler. |
| Browse | `u`, Mod+Z | Undo last committed operation when no text input owns undo. |
| Text control | Mod+Z / Mod+Shift+Z | Normal text undo/redo, without changing committed file history. |

Offer committed-operation Redo too, guarded by the post-Undo snapshot. Existing inverse-operation Undo is a foundation; multi-step history and Redo are additional work, not existing shared-session guarantees. Label the affected key. External edits invalidate conflicting history instead of being overwritten.

Prefer ordinary semantic controls to inventing a spreadsheet. The modal needs contained tab order, visible close, an accessible name, and focus restoration to its invoking control/pane. Test keyboard and screen-reader behavior. [O5]

### A measurable replacement standard

Obsidian supports text, list, number, checkbox, date, date-time, and tags. Types attach to property names across the vault, not individual note widgets. Its native editor already supports keyboard navigation, name/value focus, deletion, undo/redo, and Vim actions. Nested values and bulk editing are outside documented native support. [O1]

This table describes proposed Bob acceptance criteria, not completed functionality:

| Capability | Required behavior |
| --- | --- |
| Primitive values | Controls for every native type; no silent scalar coercion. Preserve precision; numbers beyond safe structured representation use exact source editing. |
| Names | Add, local rename, remove, completion, collision rejection. Renaming to a managed key enters its domain policy. |
| Lists/tags | Keyboard add/remove/reorder and completion; explicit duplicate handling. Empty list differs from removing the key. |
| Links | File/alias completion, navigation, correct quoting, preserved aliases/subpaths. |
| Dates | Typed entry and accessible picker; date/timestamp distinction and no offset loss. |
| Undo/Redo | Text history inside controls and guarded committed-operation history outside them. Never blind whole-file rollback. |
| Key order | Explicit local move-up/down preserving attached comments; refuse unsupported shapes. Routine editing never reorders. |
| Global property types | One native authority, accessed through a tested compatibility adapter; native management for mutation unless a supported API is verified. Label vault-wide effects. |
| Complex YAML | Complete read-only view, copy, source recovery at launch; structured nested editing can follow. Do not flatten into dotted keys. |
| Bob semantics | Domain validation, stale-write refusal, and safe recovery rather than another weaker writer. |

Native All properties also supports global rename and property search. Keep this sidebar available; do not disguise a local rename as the same operation. [O2]

**Parity limitation:** delegating global type changes is an intentional compromise. If every native operation must occur inside `=+`, type-registry integration is a release-blocking spike. Inferred YAML scalar types do not reproduce native Text/List/Date registrations. Do not invent a second Bob-wide schema to cover missing API access.

## Read, ownership, and write architecture

### Shared property model

Use one snapshot/model for drawer and editor: exact authored key, presence, typed value, source span/order, native type when known, diagnostics, and responsible editor/writer. Keep display metadata separate from persisted fields.

Metadata cache supports fast paint; confirmed source bytes establish exact membership/order and malformed YAML. Do not assume every cache-object entry came from the file. The record model filters a `position`-shaped cache artifact; a universal inspector should identify authored keys from source instead of banning a legitimate user property with that name. [C3]

Painting and folding stay local and read-only: no per-card subprocess, vault scan, normalization write, or report request. Refresh on relevant file/metadata events, deduplicate work across panes, and preserve scroll/focus during DOM updates. Lazily build huge nested trees while preserving complete access.

### Whole-container ownership

Add a whole-container mode to the shared kit. Acquire ownership after the complete inspector is usable and an editor or explicit recovery route exists. Hide the exact native note-local container, not merely current rows; otherwise native heading/Add property survives and new keys leak into a second interface.

Keep generation-bound release handles and restoration on mode/file change, mount loss, unload, and exceptions. Title ownership remains separate. Routine repaint should not flash native Properties. Bound observers to known native scopes and avoid responding recursively to Bob's own DOM changes. [C1]

Invariant: **when Bob suppresses the native block, a complete working route to that file's properties exists.** Invalid-YAML diagnostics with source recovery are useful; a stale or partial inventory presented as complete is not. Temporary duplication is preferable to inaccessible metadata during uncertain mounting.

### Domain-aware write routing

Determine ownership from current note context and actual domain policy, not key names alone:

| Class | Route |
| --- | --- |
| Ordinary user keys, aliases, tags, cssclasses, valid created corrections | New generic preserving writer. |
| Record schema values | Existing records writer with album validation. |
| Album schema/configuration | Existing album editor/writer. |
| Bank configuration | Existing bank editor/writer, without arbitrary nested replacement bypass. |
| Intentions, summary, reflection | Periods writer, preserving provenance and Undo semantics. |
| Digests/generated stamps | Visible and explained; normal mode read-only; repair/source route. |
| Structural type/parent changes | Domain action where available, otherwise deliberate source route. Changing record parent alone does not necessarily move its file into another album. |

A generic bob-cli writer is the most coherent default. Obsidian normally recommends its atomic frontmatter API; `Vault.process` also provides safe synchronous read-modify-write. These are valid conventional-plugin alternatives. [O3], [O6], [O7] Bob already coordinates independent CLI writers and schema rules, and its parent editor explicitly avoids whole-frontmatter reserialization. [C7] Neither native API automatically supplies Bob's cross-process protocol or domain guarantees.

Use validated operations over fresh source and the shared YAML span foundation. A versioned request needs file identity, expected snapshot, and ordered operations. Results need typed errors, confirmed after-state, and inverse operations. Exact command names remain implementation choices; do not broaden `records update` into an unrelated arbitrary-note writer just because it exists.

Required writer behavior:

- Confirm/save every open pane for the target and relevant schema dependencies, following existing sessions. Refuse if editor state cannot be reconciled.
- Under established vault write coordination, reread and validate expectations. Frontmatter/schema changes invalidate stale requests. Preserve the freshest body rather than writing an old whole-document snapshot.
- Preserve untouched bytes: comments, line endings, BOM, quoting, order, multiline blocks, body. No-op means no write. Reparse the full result and verify intended semantics before committing.
- Detect duplicate keys before conversion loses ambiguity. Refuse unsupported anchors, aliases, tags, merge keys, complex mapping keys, or uncertain spans instead of silently rewriting. Keep source recovery available.
- Preserve null/removal and quoted/typed scalar distinctions. JSON alone cannot represent all YAML or arbitrary-precision numbers; use explicit representations or opaque source routes.
- Return conflicts while preserving the draft. No automatic last-write-wins. Disjoint three-way merge can be future work; start with explicit refresh/review.
- On timeout/lost response, reread before retrying. Separate saved-but-sync-pending from not-saved. Undo uses expectations, never blind full-file restoration.

The record fingerprint preserves scalar types, includes album schema, and excludes body bytes. It also maps YAML to canonical JSON, omitting non-string mapping keys and unwrapping tags. It is a useful precedent, **not** a universal fingerprint to copy unchanged. Generic edits need an explicitly supported YAML subset or raw-frontmatter digest plus suitable semantic guards. [C8]

## Equals-key integration

Extend the existing dispatcher's second-key vocabulary from `=` to `=`, `-`, and `+` after the same pending operator. Cancel that operator before dispatch, and consume each physical event once even when both window/document listeners see it. Match `event.key === '+'`, not one unshifted physical key: layouts produce plus differently. [C2]

Recommended scope:

- `==` retains specialized editing; `=-` toggles the active pane's drawer; `=+` opens its Properties editor regardless of drawer state.
- Live Preview only: Vim normal mode, uncounted/unregistered pending equals, eligible mounted card.
- Preserve behavior in insert/visual/replace modes, Source, other notes, IME composition, held-key repeats, and unrelated operator sequences. Native `=+`/`=-` can be operator-plus-motion inputs; these are intentional local overrides.
- Reading/non-Vim users get buttons and named palette commands with configurable shortcuts. Avoid a global timed equals detector.
- Modal text, capture, relations, and command chips retain their keys. `=+` appears in capture fixtures, reinforcing why this must be context-scoped.

Passing existing tests does not settle actual CodeMirror/Vim event behavior or non-US keyboard layouts. Run an Obsidian spike. A vimrc-only implementation is insufficient given how the current dispatcher handles the equals operator. [C2]

## Alternatives and delivery gates

| Approach | Strength | Problem | Decision |
| --- | --- | --- | --- |
| Globally hide Properties; rely on Source/sidebar | Small change | No complete replacement; affects unsupported notes | Reject. |
| Move native Properties widget into card | Potential quick native parity | No public mount API found; lifecycle/focus risk; inherently editable unlike requested drawer | Bounded experiment only. |
| Adopt metadata plugin as editor | Rich controls | Another schema/write authority without demonstrated Bob guarantees | Borrow ideas, not foundation. |
| Custom UI using processFrontMatter for everything | Supported and simple | Does not by itself preserve source or enforce Bob semantics/coordination | Weak fit here. |
| Shared Bob UI, generic guarded writer, domain delegation | Extends architecture; coherent behavior | Larger scope and type compatibility work | Recommend. |

Metadata Menu demonstrates compact field modals, contextual schemas, and nested object controls. Its documented field definitions/file classes would overlap with Bob's album schemas if made authoritative. Borrow interaction ideas without assuming tested interoperability or transaction safety. [O8], [O9]

Deliver through three acceptance stages:

1. **Prove the seams:** disposable Obsidian fixtures for full-block ownership/restoration, equals keys, and native type discovery/change routing. Decide whether global type editing is supported or explicitly delegated.
2. **Complete display and editing before takeover:** shared drawer, created footer, native primitive controls, add/rename/remove/reorder, guarded writes, domain dispatch, conflicts, Undo/Redo. Keep native Properties during development; suppress it only after parity/recovery checks. Do not hide it while promising editing later.
3. **Harden and broaden deliberately:** full species/view matrix, large values, real themes and keyboards. Arbitrary nested editing, mobile, bulk changes, and new note species can follow independently; recovery remains available.

The acceptance matrix should include:

- Every existing species, identity-only day/period cards, no frontmatter, unknown/legacy keys, missing/invalid created.
- Multiple panes, file switches, Source/Live Preview/Reading, unload, failed title-slot mounting, native container replacement, narrow and light/dark layouts.
- False/zero/null/empty values, typed-looking strings, lists/links/multiline text, BOM/CRLF, comments, duplicate keys, anchors/aliases, large nested values.
- Concurrent changes to frontmatter/schema/body, rename/delete while open, timeout after success, local success with sync failure, conflicting Undo/Redo.
- Keyboard-only add/edit/rename/remove/reorder, completion, filter focus, close aliases, text undo, tab containment, focus restoration, screen-reader announcements.
- Zero writes and zero bob launches from paint, folding, relative-created refresh, or read-only browsing.

Concentrate code ownership: shared model/display/ownership/dispatch in the property-card kit, reusable typed stages, domain policy supplied by each adapter, and guarded writers in bob-cli. Do not implement a bespoke metadata fold per species or reproduce schema validation in JavaScript.

## Evidence and limits

Primary web sources were checked. Repository contents were read from SASE-opened local checkouts; links below pin inspected commits. A historical screenshot in bob-cli's evidence directory was inspected but not treated as proof of today's layout. No peer research was used.

[C1]: https://github.com/bobs-org/bob-plugins/blob/9b4bc2ca3b2c72c30538739b029dca705ee9f131/plugins/bob-ledger-tools/src/240b-plugin-property-card-ownership.js
[C2]: https://github.com/bobs-org/bob-plugins/blob/9b4bc2ca3b2c72c30538739b029dca705ee9f131/plugins/bob-ledger-tools/src/248m-plugin-schema-double-equals.js
[C3]: https://github.com/bobs-org/bob-plugins/blob/9b4bc2ca3b2c72c30538739b029dca705ee9f131/plugins/bob-ledger-tools/src/242i-plugin-record-sheet-model.js
[C4]: https://github.com/bobs-org/bob-plugins/blob/9b4bc2ca3b2c72c30538739b029dca705ee9f131/plugins/bob-ledger-tools/src/296d-plugin-intention-card-title-slot.js
[C5]: https://github.com/bobs-org/bob-plugins/blob/9b4bc2ca3b2c72c30538739b029dca705ee9f131/plugins/bob-ledger-tools/src/242aa-plugin-guarded-update-session.js
[C6]: https://github.com/bobs-org/bob-cli/blob/b7945e75d038506675de04f06bac826990db3d27/src/native/yaml_spans.rs
[C7]: https://github.com/bobs-org/bob-plugins/blob/9b4bc2ca3b2c72c30538739b029dca705ee9f131/plugins/bob-navigation-hotkeys/src/211-parent-frontmatter-plan.js
[C8]: https://github.com/bobs-org/bob-cli/blob/b7945e75d038506675de04f06bac826990db3d27/src/native/records/fingerprint.rs
[C9]: https://github.com/bobs-org/bob-plugins/blob/9b4bc2ca3b2c72c30538739b029dca705ee9f131/plugins/bob-ledger-tools/src/242j-plugin-record-sheet-dom.js#L417
[C10]: https://github.com/bobs-org/bob-plugins/blob/9b4bc2ca3b2c72c30538739b029dca705ee9f131/plugins/bob-ledger-tools/src/242m-plugin-record-update-session.js
[C11]: https://github.com/bobs-org/bob-cli/blob/b7945e75d038506675de04f06bac826990db3d27/src/native/intentions/write.rs
[O1]: https://obsidian.md/help/properties
[O2]: https://obsidian.md/help/plugins/properties
[O3]: https://github.com/obsidianmd/obsidian-api/blob/737629a51f6b4d30f8336fa3d38f3df006e322d4/obsidian.d.ts
[O4]: https://www.w3.org/WAI/ARIA/apg/patterns/disclosure/
[O5]: https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/
[O6]: https://docs.obsidian.md/Plugins/Vault
[O7]: https://docs.obsidian.md/oo/plugin
[O8]: https://mdelobelle.github.io/metadatamenu/controls/
[O9]: https://mdelobelle.github.io/metadatamenu/fields/

Unresolved questions are bounded: native type-registry compatibility in the installed Obsidian build, actual prevalence of complex/invalid YAML, non-US-keyboard behavior, and future mobile coverage. Existing primitives do not mean the generic editor or whole-container ownership already exists. The tests run were `node scripts/test-ledger-tools-schema-double-equals.cjs` and `node scripts/test-ledger-tools-property-card-ownership.cjs`; no implementation changes were made.

## Recommended solution

**Proceed with a shared Bob frontmatter interface: `=-` toggles a collapsed-by-default All properties drawer, `=+` opens a keyboard-first Properties editor, and `==` keeps the specialized card editor.** Put a compact created value in persistent card chrome and show every authored key in the drawer. Hide the complete native in-document block only while that replacement is healthy, with automatic restoration and Source recovery.

Build around explicit field transactions, guarded Undo/Redo, and existing domain writers. Add a generic byte-preserving writer for ordinary properties; prevent bypasses of schemas, structural constraints, and generated provenance. Treat native type-registry integration and actual Obsidian keyboard/lifecycle testing as release gates. This achieves the requested visual coherence while retaining the trustworthy parts of the current architecture.
