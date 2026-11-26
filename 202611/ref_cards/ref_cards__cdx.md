# Ref Cards: identity, trustworthy metadata, and parallel delivery

Independent research by **cdx**, 2026-11-26.

Ref Cards are a good addition if they make a reference easier to recognize, open, and navigate. I recommend a compact, folded-by-default member of the existing Property Card family, backed by Bob's existing reference index. Give it `==`, but make that open reference-aware metadata editing in the existing Property Editor—not an album-style schema designer. Keep reading-state changes attached to the reading task and lifecycle changes attached to their existing commands.

The biggest implementation risk is not CSS. It is presenting imported, projected, and identity-sensitive fields as ordinary editable properties. The biggest concurrency risk is sharing a temporary activation switch with an epic that intends to delete it.

## Scope and evidence

This is research and a proposed design, not an approved implementation plan. No product, vault, or canonical memory files were changed. I did not read any other researcher's report, transcript, or findings. The notebook/prose epic is shared input explicitly requested by the user.

Source inspection used bob-cli **`cf414ce15c5489203abf81d308d9359d30214510`** and the opened bob-plugins checkout **`6bd399f301f200b9b692f367af1baf0bdfb2732c`**. The audited bead read reported `bob-cli-qm` and its seven phases in progress. Its approved plan is **`plan:202611/prose_and_notebook_cards.md`**, accessed through `sase artifact read`. That plan was written against older plugin code; its future seams must not be mistaken for already landed APIs.

I inspected existing card hosting, species, title recognition, ownership, keyboard routing, report services, property roles/writes, reference rows, annotation counting, and sync projections. I also consulted the official Obsidian, Zotero, and W3C sources cited below. The recommendations are my design judgments; the observed behaviors and measurements are identified separately.

### What the library actually contains

I queried only metadata through `bob ref list`, aggregating the results without printing reference titles, bodies, or annotations. The final queries used `-o external` and `-o agent-report`, each with `-R all -n 5000 -f json`; both returned `truncated: false`. These are this host's indexed library at observation time, not a claim about unfiled intake or other hosts. Superseded rows are hidden by the existing command: two external rows were excluded.

| Metadata observation | Modern external | Legacy external | Modern agent reports | Legacy agent reports |
|---|---:|---:|---:|---:|
| Returned references | 64 | 590 | 711 | 12 |
| Author present | 33 | 0 | 0 | 0 |
| Published present | 28 | 0 | 0 | 0 |
| Parent present | 64 | 590 | 711 | 12 |
| Reading-task pointer present | 64 | 0 | 711 | 0 |
| PDF pointer present | 64 | 0 | 711 | 0 |
| Audio pointer present | 13 | 0 | 16 | 0 |
| Saved Markdown pointer present | 7 | 0 | 486 | 0 |
| Nonzero annotation count | 26 | 0 | 72 | 0 |
| Nonzero comment count | 24 | 0 | 34 | 0 |

That is **1,377 returned references**, including **602 legacy references**. A paper-centric design with compulsory author, publication date, PDF, or task rows would look broken on much of this library. Only one modern report had `research_ref`; it cannot be the primary affordance for report access. A stored pointer does not establish that its target exists or is readable on this host.

The two complete metadata queries took approximately **1.39 s** and **1.30 s** on this run. This is a small observation, not a performance benchmark, but enough to reject a subprocess per render or per open pane. The first capped samples were heavily biased toward legacy external refs; the table uses the later complete results.

## 1. What to reuse—and what differs from other cards

The existing kit already provides the essential product behavior:

- Shared `.bob-property-card` chrome and a species registry, with root hue carrying ownership and a tile plus word carrying species.
- A host for Reading and Live Preview; generation-bound ownership handles for split panes and late callbacks.
- Separate title, individual-property, and whole-frontmatter ownership.
- Native Properties replacement only after a valid card and foot mount, confirmed source/cache agreement, compatible `props_v1`, and working editor routing. Source, embeds, hover, canvas, print, mobile, invalid YAML, and failed mounts retain or recover native access.
- A full Properties drawer and the `==`, `+`, `-`, `_` family. `==` uses a registry and a capture-phase pending-equals gate; a naive Vim mapping does not work reliably.
- Span-preserving property updates with semantic fingerprints and typed stale refusals.

These are established contracts, not opportunities to make a smaller ref-only substitute. Relevant implementation anchors are [the host](https://github.com/bobs-org/bob-plugins/blob/6bd399f301f200b9b692f367af1baf0bdfb2732c/plugins/bob-ledger-tools/src/240c-plugin-property-card-host.js), [whole-frontmatter ownership](https://github.com/bobs-org/bob-plugins/blob/6bd399f301f200b9b692f367af1baf0bdfb2732c/plugins/bob-ledger-tools/src/240q-plugin-property-card-frontmatter-ownership.js), and [the key registry](https://github.com/bobs-org/bob-plugins/blob/6bd399f301f200b9b692f367af1baf0bdfb2732c/plugins/bob-ledger-tools/src/248m-plugin-schema-double-equals.js).

The approved `qm` plan is particularly useful for its separation of a local identity shell from asynchronously supplied readouts, omission of unavailable facts, reserved readout space, exact type eligibility, and reuse of the Property Editor. Its notebook-specific note counts, prose-specific word estimates, and numbered outline do not belong on a Ref Card simply because they exist.

A reference is also different from a record. It does not inherit an album's user-designed field schema. Its source bundle, reading task, and imported annotations each have an existing authority. The [reference-library concept](https://github.com/bobs-org/bob-cli/blob/cf414ce15c5489203abf81d308d9359d30214510/docs/concepts/reference-library.md) makes that separation explicit.

## 2. Product critique and requirement adjustments

The idea is sound: a reference note currently exposes a mixture of useful bibliography and operational frontmatter. A card can make the first screen intelligible without losing the underlying Markdown. It also gives the library a consistent visual language alongside notebooks and prose.

I would change these requirements explicitly:

1. **Replace “as much information as possible” with “answer the first four questions immediately.”** What is this? Where did it come from? Where am I with it? What useful material is here? Put less frequent inspection behind expansion or Properties. Available metadata is not automatically useful header content.
2. **Use a reference metadata editor, not a schema builder.** `==` should work, but refs do not need field-definition CRUD, validation-rule editing, or a new kind hierarchy.
3. **Do not promise all metadata is directly editable.** In the first release, support author, publication information, aliases, and topics through existing property machinery. Defer polished retitling, source replacement, retyping/refiling, and arbitrary ID changes until their domain transactions exist.
4. **Keep the managed reading-task embed visible initially.** A status badge is not an equivalent replacement for its task actions, child context, and navigation. Do not delete or hide it merely to produce a cleaner screenshot.
5. **Make the first implementation desktop-only under the family gate.** A narrow desktop pane must work; mobile should retain native rendering until separately accepted.
6. **No new PDF inspection or automatic metadata enrichment.** Page thumbnails, inferred reading duration, extracted summaries, and abstract previews are not required for the card. The Mac Ref Panel already has a richer inspector; the note itself already contains the annotations.

These changes reduce scope while making the result more reliable. They do not reduce the card to a decorative title banner: source access, reading context, saved-source access, annotations, lineage, and honest diagnostics remain useful functionality.

## 3. Recommended visual and interaction design

### A small reference identity card

Use a **bookmark-shaped tile**—a narrow ribbon with a notched lower edge—and a visible **REF** kicker. It should remain distinguishable from the album stack, record sheet, notebook spine, and prose folio in grayscale. A restrained root-area hue connects the card to its parent; do not create a separate rainbow by `ref_type`.

Use the family's typography, borders, spacing, and focus styles. Start with a quiet wash around the record/prose intensity, not a large saturated banner. A cover image is unnecessary and would make unavailable PDFs look like incomplete records.

**Default state: details folded, useful identity and actions visible.** An illustrative populated case:

```text
╭──────────────────────────────────────────────────────────────────╮
│ ▯  REF · Paper · ● Research › Machine learning           Finished │
│    Attention Is All You Need                                     │
│    Ashish Vaswani et al. · 2017 · arxiv.org                        │
│                                                                  │
│    Open PDF ↗       Reading task ↗       18 annotations           │
│                                          6 with notes            │
│ ──────────────────────────────────────────────────────────────── │
│    Added Oct 6, 2026                 Details ▸   Properties ▸  +  │
╰──────────────────────────────────────────────────────────────────╯
```

This is a layout sketch, not measured typography. In production the counts occupy one compact factual phrase, such as `18 annotations · 6 with notes`; they are not two competing status badges. The date and state are illustrative.

A sparse legacy reference should be equally intentional:

```text
│ ▯  REF · Book · ● Systems                         Finished · legacy │
│    Designing Data-Intensive Applications                           │
│    Open source ↗                                                   │
│    Details ▸                                      Properties ▸  + │
```

No ghost author, empty date row, missing-PDF error, “create reading task” prompt, or zero-highlight scoreboard. Absence is normal for this shape.

### Field and action hierarchy

| Element | Source and behavior |
|---|---|
| Kicker | `REF`, a human-readable `ref_type`, and a bounded parent breadcrumb. Agent reports read `Report`; an unknown type stays legible as text. The tile remains the same species. |
| Title | Match Bob's index precedence: nonblank frontmatter `title`, then the recognized H1, then humanized stem. Do not adopt prose's alias-first rule. Render source text safely as text. |
| Byline | Present author and publication value, then the source host. Drop missing components and separators. Show year-only values as years; do not invent January 1. |
| Reading state | Use Bob's `reading_state`, with blocked displayed as an additional condition, not a replacement state. Human copy may map `started` to `Reading`; it must not be described as page progress. Legacy state gets a quiet `legacy` qualifier. |
| Primary action | `Open PDF` when the target is usable on this host; otherwise an available web source. Neither changes status. The label says what will open. |
| Reading task | Link using the exact `(path, block_id)` Bob returns, including archived residences. Omit when absent. An ambiguous task yields a diagnostic instead of choosing one. |
| Annotation fact | `N annotations · M with notes`, only for verified parseable data and meaningful nonzero values. Counts come from Bob; they include supported annotation kinds, not just text highlights. |
| Foot | One useful acquisition date, clearly labelled `Added`, plus the standard Details/Properties controls. If using a Git-inferred date, mark it approximate. Do not duplicate added/captured/created dates in the default state. |
| Problem indicator | At most one concise indicator for an actionable current problem, such as `Reading task ambiguous`. Full codes/details live in expanded diagnostics. Historical import quirks are not permanent alarm badges. |

The title remains the dominant element. Limit default actions to a primary source action and reading-task navigation; put Audio, Saved Markdown, secondary URLs, and Copy in expanded details. With no task, the freed space may hold the annotation fact. With no usable source, preserve the title and metadata; a broken recorded path gets a specific diagnostic, while a legacy ref with no recorded PDF does not.

**Expanded Details** contains a few labelled groups, not another all-fields table:

- **Sources:** PDF, original URL(s), audio, and saved Markdown; exact identifiers and note link available through a compact Copy menu. Present preserved Markdown in a read-only viewer or copy flow, not an editor that invites changing the write-once source store.
- **Reading:** state provenance, task residence/lane, blocked reasons, and finished date where Bob reports one.
- **Annotations:** counts and “Snapshot from last Highlights scan” with its timestamp if known; jump to the actual Highlights section. Do not repeat annotation excerpts already below the card.
- **Related readings:** Earlier readings and replaced-capture history, with clear labels. `Reading 2` means lineage, not a version of the source document. Add Later only when an authoritative cached report supplies it; the list row has `earlier` and `reading`, while `later` belongs to `ref show`. Do not infer families from filenames.
- **Topics and diagnostics:** bounded topic chips, remaining source/provenance facts, and specific issues. The raw field inventory remains in Properties.

Omit empty groups. Use `_` to fold Details and `-` for Properties; they are different disclosures. Keep the reading state and primary source action visible when details fold. There should be no separate internal scroll area for a small expansion.

### Title and reading-task ownership

Reuse the title recognizer but make it strict: hide only a redundant opening H1 matching the displayed title. Leave a distinct H1, intervening prose, arbitrary embeds, annotations, and the managed reading-task embed intact. The existing [title-range scanner](https://github.com/bobs-org/bob-plugins/blob/6bd399f301f200b9b692f367af1baf0bdfb2732c/plugins/bob-ledger-tools/src/240h-plugin-property-card-title-range.js) stops at unrelated lines; the ref adapter should not broaden it to swallow every line after the title.

A duplicate equivalent H1 may disappear visually while its bytes remain. A cursor or selection touching that source range restores the Markdown, as in the family. A different H1 is content, even if it makes the page less visually tidy. This is one reason retitling is not a trivial `title:` text input.

### Narrow panes and accessibility

Below roughly 420 px, put reading state below the title/byline rather than squeezing it into a right column. Allow long titles and URLs to wrap; expanded details expose full values without relying on hover. Collapse middle breadcrumb segments before reducing legibility. Treat 320 px as an additional reflow check, not a mobile-launch commitment.

Use semantic headings, links, buttons, `aria-expanded`, visible keyboard focus, and words alongside color. Aim for controls of at least 24 × 24 CSS px or sufficient separation, preferably larger for primary actions. Keep light/dark, forced-colors, grayscale, and zoom screenshots in acceptance. These are grounded in [W3C's target-size guidance](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html) and [reflow guidance](https://www.w3.org/WAI/WCAG22/Understanding/reflow.html).

Zotero offers a useful precedent: its redesigned item pane keeps a title/author/date header visible while metadata sections collapse. The transferable idea is a stable identity header plus progressive disclosure, not copying Zotero's whole library interface into a note. [Zotero's redesign description](https://www.zotero.org/blog/zotero-7/).

## 4. `==`: yes, with a bounded reference metadata surface

`==` already means “open this card's editor” across the family. Omitting it from refs would create an unnecessary exception. Register a `ref` extension using the existing dispatcher. Preserve its Live Preview/Vim-normal-mode gates, counted/operator behavior, and Source-mode fallback. Provide a command and visible edit entry for users outside that key context.

The editor should be titled **Reference details** and reuse the Property Editor's stages, validation, focus, history, and close-key ladder. It is a mode or field grouping of the existing editor, not a second dialog engine. `+` still opens the complete Property Editor and `-` the complete inventory. `==` prioritizes the small set of supported reference metadata.

### First-release operations

| Field or action | Recommended first-release behavior |
|---|---|
| `author` | Add, correct, or clear a string; no new structured creator schema. |
| `published` | Add, correct, or clear the supported scalar representation. Preserve year-only and legacy values without inventing precision or silently coercing a global property type. |
| `aliases` | Add/remove/reorder values through existing list editing; preserve established serialization. |
| `topics` | Add/remove/reorder values using the currently supported string/list shape. Do not invent a tags↔topics migration. |
| `title` | Display and copy. Defer a polished Retitle operation until its semantics cover the generated H1 and source/task presentation. Raw YAML remains the deliberate recovery route. |
| `parent`, task lane, status, schedule | Show the effective values and offer **Open reading task**. Editing task residence or workflow uses the established task UI. Never set projected frontmatter to simulate a task move or completion. |
| `id`, filename | Inspect/copy; a future Rename affordance delegates to `bob ref rename`, including preview and all existing eligibility refusals. No freeform ID textbox. |
| `type`, `ref_type` | Inspect; do not offer directory refiling or a generic “change kind” picker. |
| Source URLs and bundle pointers | Open/copy. Do not silently replace the deduplication source, PDF, audio, or saved-source pointer through the friendly editor. |
| `earlier`, `superseded_by`, sync hashes, pipeline version, annotation counts/times | Managed inspection, grouped closed in Properties. No ordinary edits. |
| Extra custom properties | Remain available through `+` according to Bob's declared roles; unsupported YAML shapes retain the existing recovery path. |

Focus the first existing editable metadata row. If none exists, show deliberate Add choices for the supported fields; do not automatically create properties or prefill fabricated bibliography. `qm.1`'s focus-or-add helper can be reused after it lands.

This is a conservative first-release edit scope, and **a deliberate requirement adjustment**. Title correction is useful, but a product-quality Retitle operation has to define whether it changes only display metadata, the generated heading, a reading-task alias, and the PDF marker. The current index chooses `title` over H1, while the title ownership kit hides only matching headings. Changing `title:` alone can reveal a second, different H1. Silently treating any leading H1 as generated would be worse. Do not block useful card delivery on solving that transaction.

### Field policy must live in Bob

At the inspected revision, `props::roles` recognizes `NoteKind::Reference`, but its reference-specific protection chiefly covers `source_markdown`; many lifecycle-sensitive keys fall through as loose properties. That is not a sufficient authority model for the proposed friendly editor. See [property roles](https://github.com/bobs-org/bob-cli/blob/cf414ce15c5489203abf81d308d9359d30214510/src/native/props/roles.rs).

Extend the reference roles/contract in Bob before enabling the editor. Use the same protection for Set, Unset, Rename, YAML replacement, and restoration routes; a key rename or Undo must not bypass the policy. Preserve the explicit raw-YAML recovery route. Do not merely gray out fields in JavaScript while an alternative property entry point still edits them normally.

Expose a named capability for this policy, for example **`props_reference_v1`**; this is a proposed name, not an existing API. Require it before activating reference-specific editing or hiding native Properties for the new card. An older CLI may show a passive identity card with native access retained. This avoids treating the broad existing `props_v1` as evidence that the new restrictions are present. If the change makes formerly accepted generic property mutations refuse, account for the repository's CLI-contract breaking-change convention (`!`) instead of disguising that as a purely additive behavior change.

Use the existing fingerprinted `bob props` transaction for allowed metadata edits. Preserve YAML comments/unrelated fields and the body, validate current source under the write boundary, and refresh from the committed result. A stale edit remains open with the draft intact and a clear reload/review choice; never auto-reapply it over new data. The implementation basis is [the property planner](https://github.com/bobs-org/bob-cli/blob/cf414ce15c5489203abf81d308d9359d30214510/src/native/props/plan.rs).

### PDF synchronization is a separate consequence

Author, published, aliases, and topics are existing synced user fields. The [sync projection](https://github.com/bobs-org/bob-cli/blob/cf414ce15c5489203abf81d308d9359d30214510/src/native/highlights_ref/model.rs) and [field definitions](https://github.com/bobs-org/bob-cli/blob/cf414ce15c5489203abf81d308d9359d30214510/src/native/highlights_ref/mod.rs) establish this; they are not note-only decorations.

A metadata save should write the note through Bob and say that PDF metadata is synchronized by the existing reference sync workflow. It must not claim that the PDF already changed. Do not run a scan, rewrite a PDF, create a reading task, or move a bundle as a side effect of opening or saving the metadata editor. Existing scan conflict handling and coordinated PDF-write rules remain in charge. Esc, `q`, and Ctrl+`[` must back out through the existing layer, with the established text-entry exception for `q`.

Obsidian itself assigns property types by property name across the vault. A reference-specific editor must not casually convert the global `published` property into a stricter date shape just to get a date picker. [Official Properties documentation](https://obsidian.md/help/properties).

## 5. Data flow and reliability

### Reuse the reference index; do not parse a second library in JavaScript

The existing [RefRow](https://github.com/bobs-org/bob-cli/blob/cf414ce15c5489203abf81d308d9359d30214510/src/native/ref_library/row.rs) already supplies title, origin/type, state and its source, task pointer, parent, blocked reasons, URLs, author/publication/capture dates, source pointers, annotation/comment counts, snapshot time, lineage, identifiers, and diagnostics. This is enough for a useful first card.

Use one plugin-level reference report service, patterned after the album/notebook services but **without their mutation/sync lane**. A service can request the full metadata list with all reading states once, share it among mounted views, and index it by exact vault-relative note path. Do not use default `ref list`: it returns the reading queue and would omit finished/dropped references. If a capped response is used, `truncated` means incomplete coverage—not “this note does not exist.”

The local shell paints from confirmed frontmatter/source immediately. The service fetches off-paint on activation or a debounced relevant invalidation. Reflow, folding, drawer toggles, scrolling, and cursor movement perform no subprocess work. More than one view of a reference shares the same flight and result.

Use a bounded cache keyed by vault identity, Bob executable/capabilities, and report generation. Relevant events include reference note changes, reading-task residence/archive changes, parent metadata changes, and rename/delete. Changes outside `ref/` can alter a reference's state. Coalesce a burst into one refresh and discard obsolete replies; unloaded views must not remount themselves on completion. An absent or unsupported report should not generate a retry loop.

`ref show --no-annotations` exists, but it is not a cheap pure-header endpoint: `run_show` builds the index and `load_show_row` still returns own notes/tasks while clearing annotation arrays. The first card should use the list row and omit unavailable extended facts. Do not call `show` for every card mount or trigger it by folding Details. A later explicit inspection command can request it through the service. If profiling justifies a dedicated bounded metadata projection, add it in Bob; do not begin by maintaining a second card database. See [the show implementation](https://github.com/bobs-org/bob-cli/blob/cf414ce15c5489203abf81d308d9359d30214510/src/native/ref_library/show.rs).

### Distinguish three kinds of freshness

1. **Confirmed note source/cache:** controls whether the kit may safely own title/properties.
2. **Reference report freshness:** controls whether cross-note task state, lineage, and counts are current enough to present normally.
3. **Last Highlights snapshot:** tells when annotations were imported; it is not a freshness guarantee about the open PDF.

A stale report must not tear down a still-valid title shell. Keep its space stable; mark cached facts briefly as updating or omit the unavailable readout. A failed refresh may show “Reference details unavailable” with manual retry, not invented zeros. Current source/cache disagreement still follows the kit's native-restoration behavior.

Do not show an old `Finished` badge as confidently current after its reading task is reopened. Do not use `highlights_synced_at` as the sole invalidation key; it does not change on every task move or metadata edit. Invalid or partly parsed annotation regions should not produce a confident zero. Bob's `annotation_count` is based on managed-region parsing, excluding marker mirrors and preambles; `comment_count` also includes note/image-note cases. Therefore **“annotations / with notes”** is more accurate than **“highlights / comments.”** [Counting implementation](https://github.com/bobs-org/bob-cli/blob/cf414ce15c5489203abf81d308d9359d30214510/src/native/ref_library/mod.rs).

### Eligibility and actions

Prefer exact canonical `type: "[[ref]]"` (or its single-value list representation), with the family's denied paths/contexts. A file merely living under `ref/` is enough for the CLI index but should not automatically authorize full property takeover. Untyped or mixed-type indexed notes retain native access. Canonical legacy refs are eligible for the sparse card; lack of a task/PDF alone is not invalidity.

Fold the new predicate into the single species resolver as `qm.1` leaves it. Preserve existing precedence and assert that at most one card claims a note, especially mixed ref/prose, ref/notebook, and ref/record cases. Do not start another independent `type.includes('ref')` owner.

Open links through established APIs with explicit paths, modifiers, and jump history. The current [reference-PDF opener](https://github.com/bobs-org/bob-plugins/blob/6bd399f301f200b9b692f367af1baf0bdfb2732c/plugins/bob-navigation-hotkeys/src/677-plugin-ref-pdf-open.js) is a reuse seam, not permission to shell-interpolate frontmatter. Retain its path checks. Mac-specific Highlights actions require the Mac; other hosts need a supported viewer action or a precise unavailable state. A URI or saved Markdown pointer should never be treated as arbitrary executable text.

## 6. Parallel delivery with `bob-cli-qm`

**Proceed in parallel. Coordinate ownership and activation, not the whole product.** No ref research or implementation needs the notebook/prose readout algorithms, Bob Prose outline API, or their content models.

The approved `qm` plan assigns shared-kit work to `qm.1`, real-app acceptance to `qm.6`, and the shared docs/glossary/deploy sweep to `qm.7`. It also coordinates with `qi` and `qj`. Ref work should inherit only the seams it actually uses, not copy every transitive gate.

| Work | Can start independently? | Integration rule |
|---|---|---|
| Bob reference field policy/capability, mutation tests | Yes | New reference-scoped Rust work; no dependence on notebook/prose data. |
| Pure ref view model, fixtures, DOM design, report decoder/service | Yes | New `refCard*` files and tests; avoid modifying notebook/prose fragments. |
| Shared species, ownership, eligibility, key registration, focus-or-add | Implementation can be prepared | Apply after `qm.1` settles; adapt to its actual API and amend the shared exhaustive type test. One owner should integrate these small edits. |
| Real-Obsidian ref acceptance | Mostly | Add a sibling runner importing shared helpers. Do not edit shared harness internals during `qm.6`'s proof; if repairs are needed, serialize those repairs and rerun affected evidence. |
| Own ref documentation and glossary draft | Yes | Keep them independent until final integration. |
| Shared family glossary/docs and enabling live cards | Late seam | Rebase over `qm.7`'s final family text, or agree an explicit ordered merge preserving all species. Do not make overlapping replacement edits from old copies. |

### The activation-switch trap

`qm` adds `cardPreviewKinds: ["notebook", "prose"]`, then its go-live phase **deletes that gate, key, and tests**. Simply appending `ref` to this temporary list is unsafe: `qm.7` could unintentionally expose an unaccepted Ref Card or remove the mechanism ref development relies on.

Recommended default: **give ref a separate temporary activation gate**, local to the ref adapter and off by default. Gate its mount, `==` registration, and ref-specific UI together. Disposable acceptance vaults enable it. Remove it only when ref acceptance is GO and the compatible CLI capability is available. The runtime capability check remains after the temporary preview gate is removed.

This deliberately avoids asking the in-progress epic to change its activation design. If the implementation team explicitly agrees to a durable per-species registry, that is a reasonable alternative, but both epics must then stop deleting shared support prematurely. Do not rely on that agreement existing.

### Build, deployment, and integration hygiene

The plugin repository requires `bob plugins sync` after edits. Because any participating agent can deploy the shared plugin, an unfinished adapter must be inert even if its source has landed. A different checkout's protected deploy must not be force-overwritten.

Keep new fragments under the repository's 1,000-line limit and namespaced `refCard*` / `.bob-ref-card*`. Reserve the file names once, then keep model/service/DOM/editor work in distinct files. Shared edits belong in the integration slice, including fragment registration, package test scripts, CSS placement, and docs navigation.

On generated-bundle conflicts, rebase source fragments and rebuild `main.js`; do not hand-merge generated output. Resolve `fragments.json` by preserving both source registrations, not by discarding one side. Record the final CLI/plugin SHAs used for the joint smoke test. The daily CLI release train means source completion is not evidence that every host has the new capability.

No messages to other agents or bead dependencies were created during this research. The table recommends an implementation arrangement; it does not claim coordination has already occurred.

## 7. Governing decisions and proposed glossary entry

These consulted decisions bind the design:

- `decisions:reference-ids-follow-file-stems`: IDs follow stems with collision suffixes; reading-task block IDs remain stable. Do not describe the ref ID itself as permanently immutable.
- `decisions:reference-renames-keep-identity`, as partly superseded above: supported renames move the bundle and links; annotated full renames/refiling remain outside that contract.
- `decisions:reference-sources-are-preserved-write-once`: saved Markdown is preserved source, not a convenient editable copy or a live current document.
- `decisions:code-copy-reads-render-time-catalog`: if exact code copy is later added, use the recorded catalog through Bob; do not parse PDFs or Markdown again in the card.
- `decisions:references-are-ingested-at-birth`: library membership begins with a filed reference note; intake is not an empty card waiting for metadata.
- `decisions:open-pdf-writes-are-coordinated`: metadata editing must not introduce an uncoordinated PDF-write path.
- `decisions:q-and-ctrl-bracket-mirror-esc`: reference editor and expansions that dismiss through Esc reuse its close ladder.
- The always-loaded release rule applies: no manual version/CHANGELOG edits; identify CLI-contract breaks.

The following is a **proposed** glossary strand for the implemented feature. It should be adjusted to the shipped behavior and published at activation, not installed now as if the feature already existed:

> **Ref Card**  
> aka reference card, reference title card
>
> The note-top [[property-card]] for a [[reference-note]], shown by Bob Ledger Tools in desktop Live Preview and Reading view. A bookmark tile and `REF` label identify the card; the parent's hue locates it. Its title, available source attribution, reading state, and source/task links answer what the reference is and how to return to it.
>
> The card starts with details folded. `_` reveals available sources, annotation-snapshot facts, reading lineage, and diagnostics; `-` opens the complete Properties drawer. Missing facts are omitted, and annotation counts describe the last imported snapshot, never reading progress. The [[reference-task]] remains the authority for reading workflow and keeps its managed embed in the note.
>
> `==` opens reference metadata in the Property Editor; `+` opens the full editor. Supported bibliography and organization fields can be corrected there; task state, filing, source identity, and imported bookkeeping stay with their owning workflows. The card replaces native Properties only under the family gate, and passive painting neither writes the vault nor starts Bob.
>
> Not the [[ref-panel]] in Bob Mac Capture, a reading task, a PDF preview, or a schema definition. See the Ref Card user documentation.

The user explicitly requested this new term. The eventual implementation should also update `glossary:property-card` to include Ref Card without losing `qm`'s additions. Because that is a separate existing note, record its memory scope explicitly in the implementation plan. No accepted architecture decision needs rewriting merely to introduce a new renderer.

## 8. Acceptance, costs, and remaining uncertainty

A static mockup and unit tests alone are insufficient for ownership and keyboard behavior. Required acceptance should cover:

1. **Representative data:** modern paper, sparse report, legacy URL-only ref, absent PDF, audio, saved Markdown, missing task, archived task, blocked task, reread/history, malformed annotation region, and long/multilingual text. Synthetic fixtures should carry no private source text.
2. **Native recovery:** Reading/LP, Source, bad/duplicate YAML, stale cache, selection revealing the H1, failed card/foot mount, split panes, rename/delete, denied contexts, disabled plugin, missing/old CLI capability. No invisible native fields without a working replacement.
3. **Editing boundaries:** allowed metadata edits round-trip; managed fields refuse through every generic operation; changed preimages do not overwrite; close keys preserve the editor ladder. Confirm body and managed embed remain byte-identical for ordinary metadata edits. Test an explicitly opted-in synced field against the existing projection to establish the documented sync consequence.
4. **Passive proof:** repeated render, resize, fold, drawer, and cursor operations cause zero writes and zero paint-triggered spawns. Split panes share one report request. Task changes outside `ref/` invalidate the affected facts; old callbacks cannot resurrect stale states.
5. **Visual proof:** light/dark, 320/420/wide panes, folded/expanded, long title, sparse legacy, forced colors and keyboard focus; compare alongside an album, notebook, and prose card. Review images, not only DOM assertions.
6. **Joint delivery:** with both feature sets present, verify one owner per type, unchanged notebook/prose cards, stable `==` dispatch, native fallbacks, and no premature ref activation when `qm` removes its own preview gate.

The principal cost is a bounded cross-repository change: a plugin adapter/report service plus reference-aware property policy in Bob. A card-only JavaScript patch is cheaper but would leave misleading edit affordances. A full reference schema designer is much more expensive and has no demonstrated need.

Uncertainty remains around the exact `qm.1` API as it lands, the most natural tile at actual Obsidian sizes, and the performance of broad reference-report invalidation during real editing. These need implementation measurements, not guesses. No real-app visual prototype or write-path acceptance was run in this research. The inventory establishes field presence, not file availability, bibliographic correctness, or cross-host completeness.

## Recommended solution

Build a **folded, bookmark-identified Ref Card** on the existing Property Card kit. Lead with title, available attribution, source access, and Bob's reading context; put snapshots, lineage, secondary sources, and diagnostics behind Details, with every field still reachable through Properties. Keep the managed task embed and all source bytes intact.

Support **`==` through the existing Property Editor**, with a CLI-enforced reference field policy and a small initial edit scope: author, publication information, aliases, and topics. Keep retitling and other lifecycle operations out of the first friendly editor until their transactions are defined and tested. Do not add a schema language, progress estimate, thumbnail pipeline, or automatic enrichment.

Start the model, service, fixtures, and CLI policy now in parallel with `bob-cli-qm`. Integrate shared kit changes after `qm.1`, isolate ref's temporary activation gate from `qm`'s disposable switch, and serialize only shared acceptance repairs and the final family documentation/glossary merge. Ship after real-Obsidian and joint-feature acceptance, with the new glossary term published to match the behavior actually delivered.
