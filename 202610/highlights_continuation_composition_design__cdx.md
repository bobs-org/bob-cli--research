# Composing Highlights fragments in Bob: a reversible continuation design

Researcher: **cdx**  
Date: **2026-10-19**  
Scope: independent design research; no implementation or vault mutation. No other swarm researcher's report, transcript, or findings were consulted.

**Recommendation:** implement the `<` gesture as a reversible grouping operation in Bob's sidecar-to-reference-note pipeline. Keep the original annotations and their identities; render one composite quotation with its comments. This is a useful feature, but a destructive string merge would break important existing contracts. Tighten the syntax, define “previous” precisely, preserve every source anchor and task identity, distinguish continuous quotation from omitted text, and reject ambiguous retargeting.

## 1. The actual reading problem

I inspected the supplied `~/tmp/screenshots/20261019_063505.png`. Page 11 ends a highlighted passage with “On every”; page 12 begins “session startup” and continues the same sentence. The page 12 highlight has the comment `< PR Merge Master?!`. The desired result is one passage about the PR Sheriff and one comment, **PR Merge Master?!**, applying to that whole passage.

This is a good interaction: the reader can mark the later fragment at the moment the discontinuity becomes apparent. `<` points backward, needs little typing, and remains visible in the annotation's comment in Highlights. It also fits Bob's existing convention of interpreting annotation comments for tasks and image notes.

The feature improves the **Bob reference note**. It does not make Highlights display a single cross-page PDF annotation. Be explicit about this distinction in the user documentation; otherwise the feature can appear broken while reading in Highlights.

There are two subtly different intentions in the request:

1. Reconstitute continuous source text interrupted by a page boundary.
2. Associate separated excerpts, potentially with omitted words between them, with one thought.

Both deserve support. Joining arbitrary excerpts with an ordinary space can fabricate a sentence the author never wrote. That is the main semantic weakness in the original proposal.

## 2. Evidence and limits

### Local implementation inspected

All code references below refer to **bob-cli commit `9217a475779fe0a7368f8ac99428fbca0bfbc100`**. Paths are relative to that repository, not to this report's repository.

| Evidence | What it establishes |
|---|---|
| `docs/highlights-ref-sync.md:1049–1109, 1198–1214, 1290–1383` | Managed region ownership, callout format, render-only text cleanup, task provenance, block identities, and tombstones. |
| `src/native/highlights_ref/model.rs:334–383` | `SidecarAnnotation` has kind, page label, text, comment, task source, image, export order, and per-page ordinal. It has no PDF annotation UUID, geometric bounds, or text offsets. |
| `src/native/highlights_ref/sidecar.rs:203–405` | Parser preserves sidecar sequence, computes original per-page ordinals, separates quotes/comments, and preserves task-oriented comment text. |
| `src/native/highlights_ref/sidecar_render.rs:4–187` | Rendering assigns source IDs and takes a set difference against prior IDs to create removal tombstones. |
| `src/native/highlights_ref/sidecar_render.rs:204–267, 369–389, 413–446, 541–579` | Callout construction, page-link destination loss, marker filtering, and comment/list normalization. |
| `src/native/highlights_ref/annotation_tasks.rs:4–66, 90–119, 213–241` | Text-highlight tasks recompute the original annotation ID; processed IDs include that source ID and task identity. |
| `src/native/highlights_ref/text.rs:73–163` | Existing prose reflow and line-end dehyphenation; these are display transformations. |
| `src/native/highlights_ref/region.rs:68–117, 279–285, 294–405` | Reader assumes a rendered block terminated by one standalone `^h-...` line; arbitrary aliases or extra metadata require parser changes. |
| `src/native/ref_library/show.rs:32–49, 209–275` | `bob ref show` reparses the generated region and reports separate quote/comment fields, one page label, and an annotation ID. |
| `src/native/highlights_ref/tests/sidecar.rs:399–428` and `tests/region.rs` | Existing whitespace/comment identity invariants and renderer/parser round-trip coverage. |
| `src/native/highlights_ref/sync.rs:372–405, 707–736`; `report.rs`; `scan_json.rs` | Both legacy and newer sync paths consume the renderer; reports and JSON need deliberate count/diagnostic behavior. |

The tests were inspected, not executed or modified. I did not obtain the screenshot's real exported sidecar or run Highlights/Obsidian on macOS. Export escaping, actual Obsidian appearance, and native Smart Merge behavior remain implementation validation items, not verified results.

### External primary sources

- Highlights officially advertises **Smart Merge Annotations**. Its feature list does not establish whether that supports this cross-page/discontiguous use case. Therefore, “Highlights has no merging at all” is too broad; the narrower claim is the user's observed limitation, which this research did not reproduce. A short native-app check is sensible, but not a reason to disregard the screenshot. [Highlights features](https://highlightsapp.net/features/)
- Default extraction turns highlighted text into quotes and comments into text below them; sticky notes have their own position among annotations. This supports using comments as the command surface and treating intervening non-highlight content deliberately. [Extraction rules](https://highlightsapp.net/how-to/mac/extract-pdf-annotations/)
- Default sorting uses text/page position, while color sorting can change that sequence. Thus “previous” cannot safely mean creation time, most recently edited highlight, or an assumed globally spatial order regardless of export settings. [Color sorting](https://highlightsapp.net/how-to/mac/sort-pdf-annotations-using-color-categories/)
- Highlights writes Markdown/TextBundle sidecars on PDF save/autosave and overwrites external edits to those sidecars. The composition must live in Bob's generated output, not as an edit to the exported sidecar. [Sidecar files](https://highlightsapp.net/how-to/mac/sidecar-files/)
- Obsidian documents one block identifier for a structured block and explicitly does not support links to specific parts of quotations/callouts. Do not assume multiple consecutive IDs or nested fragment IDs alias the same composite callout. [Internal links](https://help.obsidian.md/links)
- Highlights' FAQ says it is not scriptable. A custom AppleScript integration is consequently not a documented alternative to the existing export pipeline. [Highlights FAQ](https://highlightsapp.net/faq/)

## 3. Is the proposed approach worthwhile?

**Yes, for this workflow.** It keeps authoring where the reader already is, requires no new app, and uses Bob's existing synchronization machinery. The source PDF remains portable, and the ordinary marker comment survives outside Bob.

The cost is a small language embedded in prose. A bare `starts_with('<')` rule is deceptively broad: it also catches HTML, angle-bracket links, comparisons, and examples of the operator itself. A feature that silently chooses the wrong passage is worse than leaving two highlights separate.

I would not start by replacing Highlights, developing an Obsidian plugin, or rebuilding extraction directly from PDF geometry. Those are much larger changes than this need warrants. Nor would I edit the generated reference-note region by hand: Bob explicitly owns it and can overwrite such edits.

A modest composition model is justified; a general graph of named annotation groups is not yet justified. Keep the gesture local and backward-only.

## 4. Proposed user contract and explicit requirement adjustments

These are proposals, not descriptions of existing behavior.

### A. Keep `<`, but make it an operator token

Recognize the first token of a text highlight's **logical comment**, after the existing export-label/wrapper normalization. Accept `<` followed by end-of-comment or whitespace. Remove the operator and its separator from the interpreted comment; preserve the remaining paragraphs, lists, task bullets, and image-path lines.

| Comment | Proposed meaning |
|---|---|
| `<` | Continue the previous highlight; add no comment. |
| `< PR Merge Master?!` | Continue the previous highlight; append this comment. |
| `<` followed by a newline and several paragraphs | Continue and preserve the full multiline comment. |
| `< - #task Investigate this` | Continue; process the remaining task bullet normally. |
| `<... Compare the two claims` | Group separated excerpts with an explicit omission boundary. |
| `\< 5 ms is the target` | Literal comment beginning with `<`; no composition. |
| `<div>`, `<https://example.org>`, `<word`, `<= 5` | Ordinary comment; no composition. |
| `A comment mentioning < later` | Ordinary comment; no composition. |

**Adjustment 1:** a token boundary replaces the original unrestricted first-character test. `<word` would no longer be a command. This reduces accidental merges and makes the syntax explainable. `< 5 ms` is still ambiguous and must be escaped; tokenization cannot eliminate that inherent collision.

Use the logical-comment view to handle formats already accepted by Bob, including `Comment: < text` and export-style bullet wrappers. Do not search arbitrary later bullets or code blocks for `<`, and do not globally unescape HTML/entities before command detection. Retain a mapping to the task-preserving source so stripping the operator does not erase list markers.

### B. Distinguish continuation from omission

**Adjustment 2:** reserve `<...` as a second, small operator. `<` asserts direct continuation; `<...` inserts an editorial ` […] ` between excerpts. Both point to the same predecessor and group comments the same way. The screenshot keeps its exact `< PR Merge Master?!` gesture.

For `<`, join boundary prose with one space, preserving internal paragraph/list structure. Do not run a new heuristic that removes a hard hyphen merely because the following fragment starts lowercase. Existing cleanup may continue within each source fragment; cross-fragment cleanup should be conservative. A clearly recorded soft hyphen may be handled, but ambiguous hard hyphens should survive.

For `<...`, preserve each fragment and insert the omission marker at the boundary. If a boundary involves a list, code, or multiple paragraphs, preserve separate blocks within the one callout instead of flattening them into prose. Do not use AI or punctuation heuristics to infer what was omitted.

This tiny extension makes the two requested uses honest. The alternative is always showing separate fragment paragraphs in one card; that avoids extra syntax but reads poorly for “On every / session startup.” I prefer explicit join intent.

### C. Define “previous” as a source-order relationship

**Adjustment 3:** “previous” means the immediately preceding substantive annotation in the same PDF's supported sidecar sequence, after skipping the known marker mirror and document preamble. It must be a text highlight. Page headings and export date headings do not interrupt the relationship. An image or standalone note does interrupt it: do not silently skip meaningful content looking for a suitable target.

The first marked highlight cannot merge. A marker on an image or standalone note remains literal. A chain `A, B(<), C(<)` becomes one group `[A, B, C]`; C attaches to B's group, not to whichever block was last emitted by the renderer. A later unmarked highlight starts another group. No cross-PDF grouping.

Use the source order that Bob already parses. Do not sort string page labels, renumber annotations after filtering, or infer order from timestamps. Document that continuation authoring expects Highlights' normal page-position sort. Detect known category-grouped exports or backwards/ambiguous page traversal and decline composition where order cannot be trusted. Numeric monotonicity alone cannot detect same-page color rearrangement; disclose that residual limitation. Supporting arbitrary export ordering would require richer source location data.

### D. Preserve all comments, not just the marked comment

Group comments in source order. Keep separate comments as separate paragraphs inside one nested Comment callout. Do not deduplicate identical prose, choose the newest note, or concatenate separate thoughts into one sentence. Marker-only members add no blank note. Image notes from any member remain supported.

If a marker cannot be honored, keep its original text visible. An unfulfilled control must not silently erase the user's words.

### E. Undo is a normal source edit

Removing `<` from B splits before B at the next successful sync. In `A, B(<), C(<)`, removing B's operator yields `[A]` and `[B, C]`; removing C's yields `[A, B]` and `[C]`. Deleting a source fragment removes that fragment under the existing removal policy. Do not write controls or processed state back to the PDF/sidecar.

## 5. Presentation: one readable quote, truthful provenance

For the screenshot, put the group at its first member's position. Use a short title such as **Pages 11–12** and place the quotation in the callout body. This avoids turning an entire long passage into a bold callout title. Keep a single nested Comment callout. Do not repeat the source quote under Page 12 or emit an empty Page 12 heading just for a consumed member.

Illustrative Markdown, with abbreviated source text and illustrative IDs:

```md
### Page 11

> [!quote] Pages 11–12
> One last Crew tip: … On every session startup, the sheriff checks open PRs
> and divides them into easy wins and those needing human review, then slings
> the easy wins to other crew for merging and cleanup.
>
> > [!note] Comment
> > PR Merge Master?!

^h-root

[Page 12](highlights://example.pdf#page=12) · [[#^h-root|Full highlight]] ^h-child
```

The ellipsis inside this mockup abbreviates the example only; it is not an instruction to summarize the imported quotation. Production rendering keeps the complete extracted text. Page links must use real preserved source destinations, not the illustrative URL above.

The final small paragraph preserves the later member's old source anchor and gives that link a useful destination with a one-click jump to the full quotation. It is an intentional, visible compatibility affordance. Avoid unsupported invisible aliases, custom CSS, or links to nested pieces of the quote. When a group has several later members, render one compact source paragraph per member. Same-page members need distinguishable labels such as “Page 7 · fragment 2.”

Use a concise ordered list of actual page labels; `11, 14` must not become `11–14`. Only compress a range when the labels/locations establish consecutive pages. Preserve source page URLs in the parser: it currently retains the label and a boolean, discarding the destination. Printed labels are not necessarily physical PDF page indices. If no trustworthy target exists, show the label without inventing a link.

This presentation requires explicit reader support: today a custom title is interpreted as quote content, and an inline paragraph ID is not recognized by the managed-region parser. Add a structured distinction between the display title, quote text, and continuation source paragraphs. The clean appearance is the output of a defined format, not an incidental Markdown trick.

## 6. Implementation shape: keep source records, derive groups

Do not modify `SidecarAnnotation.text` to contain combined text before computing IDs, and do not delete continuation annotations from `SidecarInput`.

A useful model is:

```text
SourceAnnotation
  existing source ID, original order/ordinal, kind, page label/link
  original quote, original comment/task source
  parsed control and effective comment/task source

AnnotationGroup
  root source ID
  ordered source members
  boundary mode for each continuation
  ordered comment/image contributions

CompositionPlan
  groups, forwarding anchors, relation metadata, diagnostics
```

The processing order should be:

1. Parse the sidecar as today, retaining original positions and ordinals.
2. Identify marker mirrors without reindexing real annotations.
3. Compute each original source ID with the current algorithm.
4. Interpret comment controls into separate effective views.
5. Build and validate groups; compare previous successful relationships where available.
6. Extract tasks and image-note references per source member from the effective text.
7. Render groups, forwarding paragraphs, structured metadata, and genuine tombstones.
8. Let the existing sync planner and write guards handle persistence.

The grouping pass is linear in annotation count. PDF geometry extraction, native annotation UUID migration, a separate database, and a new CLI command are unnecessary for the initial feature.

### Identity and task intake are release-critical

`annotation_block_id` hashes the PDF path, kind, page label, original ordinal-on-page, and normalized quote text. Comments are excluded. Consequently, adding `<` to an unchanged annotation can preserve its existing ID—but computing an ID from a concatenated quote cannot.

Keep the root ID on the composite callout. Keep every member ID alive as either that root or a forwarding paragraph. Include all live source IDs when calculating removals. A member incorporated into a group is **not removed** and must not receive a false removal warning.

For tasks, keep the member's original source ID in both processed-ID calculation and provenance link. Do not make every member's task use the group root. The current task hash includes the source annotation ID, so retargeting it would make an already processed task look new. The existing `block_ids_by_annotation_order` map does not solve this alone: the highlight branch of `annotation_task_candidates` recomputes source IDs itself; only the image branch consults that map.

Strip the operator before task/image parsing. This is needed for `< - #task ...` and `< ~/tmp/screenshots/example.png`, while ordinary later task bullets must remain intact. Identical task text in two different source annotations retains existing per-source semantics; grouping is not an authorization to deduplicate tasks across sources. Imported tasks that were completed, edited, routed, or archived must stay processed after merge, comment edit, and split.

### Reader and reporting changes belong in the same release

Update `region.rs`, the generated-ID collector in `note.rs`, `ref_library/show.rs`, and annotation counting alongside the renderer. Otherwise valid forwarding paragraphs become `unparsed` content or duplicate apparent annotations.

`bob ref show` should expose one logical annotation per group, with the whole quote/comment plus member provenance. Add structured `source_block_ids`, page labels, and segment/boundary information where the JSON contract permits; keep the root block ID as the primary link. Preserve the schema's existing compatibility/versioning rules rather than silently changing a scalar field's type.

Separate source counts from displayed group counts. Preserve the existing sync `highlights_count` source-count meaning for compatibility; report displayed groups and continuation count separately. `ref show`/library annotation counts should describe logical displayed annotations and should not count forwarding records as annotations. Explain this distinction and test it; `current_ids.len()` is no longer a visual-card count.

A useful dry-run summary is `2 source annotations → 1 highlight · pages 11–12`, accompanied by short previews of both boundary fragments. Existing dry-run/scan output is sufficient; no new flag is necessary.

## 7. Reliability: the hard case is editing after a successful merge

A stateless “merge with whatever comes immediately before B today” implementation is deterministic, but determinism is not intention preservation. If A is deleted or X is inserted between A and B, the same `<` on B can silently bind to a different passage.

**Adjustment 4:** retain a small, versioned record of successful continuation relationships in the managed reference-note region, and use it as an ambiguity guard. This is generated synchronization metadata, not a new user-authored source of truth. Record each member's source ID, predecessor, page/kind/normalized-quote signature, and join mode. Keep it portable with the note rather than in host-local state.

On unchanged input or comment-only changes, reuse the relationship. If an operator is removed, honor the explicit split. If the relationship changes unexpectedly, stop planning writes for that PDF with a specific diagnostic and preserve the last good note. Other PDFs can continue under the existing scan contract. A first-run orphan/blocked merge can remain separate with its marker visible and a warning; it must never disappear.

The current ordinal-based identity makes this nuanced:

- Adding an earlier same-page annotation can change IDs even when quote text is unchanged.
- A unique exact page/kind/quote match can establish that a previous member still exists for relationship checking. This need not change the legacy source-ID algorithm.
- Duplicate identical quotes or edited member text can make that matching ambiguous. Do not fuzzy-match or silently decide which one is intended.
- Conservative refusal has a real cost: unusual edits can require removing the operator, syncing, then reapplying it. That two-sync reset explicitly establishes a new relationship without another command. Document the recovery hint.

Do not promise global annotation-ID stability as part of this feature. The existing identity limitation remains for insertion, quote edits, and some other source changes. Preserve current tombstone behavior for genuine vanished legacy IDs; grouping itself must add no extra churn. A future PDF-native identity project is separate.

If this relationship guard is considered too costly for a first release, choose stateless semantics explicitly and document automatic retargeting after source edits. I would not call that version reliable enough for unattended merging in the normal Mac scan.

New metadata must have an understood version and validated shape. An unknown or malformed grouping record should yield a diagnostic and preserve the affected note, not be silently dropped. Coordinate reader and writer rollout across Bob hosts. Old binaries can otherwise misread or overwrite the new generated format; version metadata alone cannot make an old writer safe.

## 8. Alternatives considered

| Approach | Benefit | Why I would or would not use it |
|---|---|---|
| Use native Highlights Smart Merge | Potentially no Bob work | Worth a short hands-on check. Official marketing does not verify the required cross-page/discontiguous behavior or export semantics. |
| Concatenate during parsing and delete the later annotation | Smallest patch | Reject: changes hash inputs, loses source IDs/pages, disrupts task provenance, and can generate false tombstones. |
| Group only at rendering with retained source records | Fits current architecture | Recommended, with identity-preserving anchors and shared reader support. |
| Always keep fragments as separate paragraphs inside one callout | No extra join operator; cautious quotation | Viable fallback, but less polished for a continuous sentence split by pagination. |
| Persistent named groups or explicit target IDs in comments | Can target non-adjacent annotations robustly | Too much typing and state for this use case. Revisit only if arbitrary long-distance linking is common. |
| Automatic same-color/proximity or AI merging | No typing | Reject: guesses intent and can fabricate connections. |
| Rewrite PDF annotations or sidecars | May seem more universal | Wrong ownership boundary; sidecars are overwritten and the source annotations should remain reversible. |
| Merge manually in Obsidian | Immediate workaround | Only durable outside the generated region; duplicates work and loses automatic source updates. |

## 9. Verification and delivery gates

This deserves focused behavior tests because the risk is provenance/task corruption, not merely a cosmetic change.

| Case | Required result |
|---|---|
| Screenshot fixture: pages 11/12, `< PR Merge Master?!` | One uninterrupted passage, exact comment, both page origins, both source anchors. |
| Same-page disjoint excerpts with `<...` | One group with explicit omission; no invented contiguous quotation. |
| Three-member chains; mixed direct/omission boundaries | Stable member order and the chosen separator at every boundary. |
| Bare marker, multiline comments, export labels/bullets, CRLF | Correct command detection; no empty comment card or lost list structure. |
| Literal HTML/URLs/comparisons, escaped marker, later occurrence | No accidental composition. |
| Marker mirror, first highlight, intervening image/sticky note | Known metadata skipped; meaningful boundaries respected; invalid intent retained visibly. |
| `< - #task ...`, existing routed/archived/completed tasks | Exactly the existing per-source task behavior; no duplicates after grouping or splitting. |
| Image paths in root/child comments, unresolved paths | Existing image-note behavior preserved after control stripping. |
| Two identical source excerpts | Unique identities maintained; ambiguous historical matching declines writes. |
| Merge → identical sync → comment edit → unmerge → identical sync | Stable generated output when input is unchanged; no false removals or extra tasks. |
| Delete root/insert predecessor/reorder exports | No silent retargeting of an established relationship. |
| Page labels differing from physical numbers | Accurate labels; source destinations retained; no guessed links. |
| `parse_managed_region` and `ref show` round trip | Quote excludes title/forwarding prose, comments remain distinct, source anchors are recoverable, no spurious unparsed content. |
| No sidecar, empty sidecar, preexisting removed IDs, manual text outside region | Existing behavior retained; outside text preserved. |
| Dry run and malformed/unknown group metadata | No writes; useful preview or precise recovery diagnostic. |

Start with a real Mac-exported fixture for the supplied example, including how literal `<`, an escaped `<`, and `<...` are exported. Do not infer exact bytes from the screenshot. Then implement the pure composition pass and identity/task invariants, followed by writer/reader changes in one coherent release. Validate in a temporary vault: both member block links, hover previews, source-page links, and composite layout in Obsidian Reading view and Live Preview. Plain Markdown screenshots alone cannot prove Obsidian block behavior.

Use the existing focused sidecar/region/task CLI tests and repository-required checks during implementation. This research added no executable code and did not run the full test suite.

## 10. Recommended solution

Proceed with **source-preserving annotation composition in `bob ref`**. Keep the screenshot's `< PR Merge Master?!` gesture; interpret it as direct continuation, strip only the control from Bob's display, and render one short-titled quotation with all comments. Add `<...` for excerpts separated by omitted text, require a token boundary, and offer a literal escape.

Define the predecessor from the supported export sequence, preserve every original source ID and task identity, and give consumed members compact forwarding anchors instead of tombstones. Update rendering, parsing, `ref show`, counts, and diagnostics together. Retain prior relationships to prevent silent rebinding after source edits, while acknowledging the limits of today's ordinal-based IDs.

The feature is a good idea when it makes a multi-part reading thought feel like one note **without discarding the evidence that it came from several annotations**. That is the version I recommend implementing.
