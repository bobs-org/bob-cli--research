# Continuation Highlights: Merging Split Highlights Annotations in `bob ref`

Researcher: `cld` (one of five independent reports) · 2026-10-19

## TL;DR

**Build it, with five refinements.** A note that begins with `<` should fold that
highlight into the one before it in the ref note. This is the right gesture at the
right layer:

- PDF annotations are per-page by spec, so no PDF tool can produce this merge itself.
- Readwise already ships this pattern as a sync-time "concatenation" note tag.
- `bob ref` already owns a one-way, regenerate-every-scan projection from the
  sidecar into the ref note.

The merge is a pure render-time fold. It is deterministic and reversible (delete the
`<` and the next scan splits the pieces again), and it never touches the PDF or the
sidecar.

The refinements, each called out in [§7](#7-requirement-adjustments-called-out):

1. **Sigil grammar:** `<` counts only when it is followed by whitespace or the end of
   the note. It must sit on the first line, after Highlights' list marker or
   `Comment:` label. `<https://…>`, `<br>`, `<-`, and `<3` stay ordinary text.
2. **"Previous" means the previous text highlight** in Highlights' sidebar order. The
   marker, sticky notes, and image selections are skipped. Chains work: several `<`
   pieces build one passage.
3. **An honest seam.** Pieces join seamlessly only when the next piece picks up
   mid-sentence on the next page; that is a page turn, and hyphens heal. Any other
   seam renders as ` … `. When in doubt, show the seam.
4. **Identity rules:**
   - The merged block keeps the head's `^h-` ID.
   - A follower's own ID is never tombstoned.
   - Annotation-task `[h::]` IDs stay keyed to the piece they came from, so toggling
     `<` never duplicates a task. The `🔖` link points at the merged block.
5. **Failure stays visible.** A `<` with nothing to join renders verbatim (the `<`
   survives) and the scan report counts it. The sigil is consumed if and only if the
   merge happened.

No new CLI flags or config, no change to the ref-note region format, and no
bob-plugins change. Your first real case is already in the vault (pages 11–12 of
the Gas Town manual). The first scan after shipping will exercise the trickiest
path: a follower that has already been rendered on its own.

---

## 1. The ask and the first real case

Your screenshot (`~/tmp/screenshots/20261019_063505.png`) shows a highlight ending at
the bottom of p. 11 ("…PR Sheriff Standing Orders. On every"). The sentence continues
at the top of p. 12 ("session startup, the sheriff checks open PRs…"), and the p. 12
highlight's note is `< PR Merge Master?!`.

The Highlights sidecar (`lib/blogs/gas_town_emergency_user_manual.md`) records it
verbatim:

```md
#### [Page 11](highlights://gas_town_emergency_user_manual#page=11)
##### 2026-10-19:
> One last Crew tip: I have a new ad-hoc role that I’ve been using
> …PR Sheriff Standing Orders. On every
***
#### [Page 12](highlights://gas_town_emergency_user_manual#page=12)
##### 2026-10-19:
> session startup, the sheriff checks open PRs and divides them
> …other crew for merging and cleanup

< PR Merge Master?!
```

The Mac scan at 06:45 (vault commit `69d1050c`) already rendered this as **two**
blocks. The comment landed on the second half, with a literal `<` in it:

```md
### Page 11

> [!quote] One last Crew tip: … PR Sheriff Standing Orders. On every

^h-06d27eae3c84


### Page 12

> [!quote] session startup, the sheriff checks open PRs and divides them into easy wins …
>
> > [!note] Comment < PR Merge Master?!

^h-434a5e5a2bc4
```

That is the problem in one picture: half-sentences under different headings, and a
thought that belongs to the whole passage stranded on one half.

## 2. How `bob ref` works today (what matters for this feature)

- **One-way projection.** The Mac's scheduled `bob ref scan` reads the sidecar
  Highlights writes next to each PDF. It regenerates the region between
  `<!-- highlights:begin -->` and `<!-- highlights:end -->` on every run. Bob never
  writes the sidecar or the annotations (`docs/highlights-ref-sync.md`, "Generated
  Body Contract"). A render-time fold fits this model exactly.
- **Order.** `parse_sidecar_markdown` (`src/native/highlights_ref/sidecar.rs`) emits
  annotations in sidecar order. Highlights groups that order by page and sorts by
  position on the page, not by date. Evidence: on p. 9 of the Gas Town sidecar, a
  2026-10-19 annotation precedes 10-16 and 10-18 ones, and Highlights' docs say notes
  are placed "by their location on the page". Your screenshot's sidebar shows the
  same order. So "previous" can be defined as "the item above it in Highlights'
  sidebar", which you can see while reading.
- **Only three consumers** read the parsed annotations:
  - `render_sidecar_highlights` (`sidecar_render.rs`)
  - `annotation_task_candidates` (`annotation_tasks.rs`)
  - `resolve_sidecar_image_assets` (`sidecar.rs`)

  The fold lands at one clean seam.
- **Block IDs.** `annotation_block_id` hashes PDF, kind, page label,
  `ordinal_on_page`, and the raw quote text. Comments are excluded, so editing a
  comment never churns an ID.
- **Tombstones.** Any previously rendered ID that is missing now is tombstoned under
  `### Removed highlights`. The exception is IDs in `silently_dropped_block_ids`, the
  leaked marker-mirror and preamble blocks.
- **Annotation tasks.** `#task` bullets in comments become tasks.
  `annotation_task_processed_id` hashes the note path, the **source block ID**, and the
  task identity into `[h:: …]`. The same `source_block_id` also builds the `🔖`
  backlink. A merge forces these two roles apart (§6.6).
- **Readers of the rendered region.** `bob ref show` and the reference index parse the
  rendered region (`region.rs`), not the sidecar. Whatever the renderer emits is what
  agents see. The merged block simply reads as one highlight with one comment, and the
  region grammar needs no change.
- **bob-plugins** never parse highlight blocks; they only carry `🔖` task backlinks.
  I grepped the linked repo for `^h-`, `[!quote]`, and `highlights:begin`. The change
  is bob-cli-only.

## 3. Evidence from your vault

I ran a read-only scan over every Highlights sidecar in `~/bob/lib`.

| Fact | Value |
| --- | --- |
| Sidecars with annotations | 77 |
| Annotations | 338 |
| Heuristic cross-page split candidates (last highlight on p. N ends mid-sentence, first on p. N+1 starts lowercase) | 7 |
| Of those, true page-turn continuations by inspection | 3–4 (Gas Town p11→12, `agent_catalog_pane` p15→16, `lumberjack_chop_config_improvements` p11→12, likely `sase_AGENTS` p2→3) |
| False positives among the 7 | ≥3 (Gas Town p9→10, a pair of shell commands, a goals-paper clause) |
| Existing comments that start with `< ` (apart from the new one) | **0** |
| Lines starting with `<` at all | 1 other, a hard-wrapped quote line `<reason>"` inside a highlight (not a comment, and no space after `<`) |

What this says:

- **Real but modest need.** About 1% of annotations. It is not a daily pain, but it is
  ugly when it happens.
- **You already improvised the gesture once.** In `agent_catalog_pane` the p. 15 half
  carries "After step 2 (i.e. in step 3)!" and the p. 16 half carries
  **"…see above note"**. That is a manual back-reference: exactly what `<` formalizes.
- **Auto-detection would be wrong about half the time.** The heuristic's precision is
  roughly 50%. This is the strongest argument for an explicit sigil over "smart"
  merging (§8).
- **Zero-churn rollout.** No existing note changes when the feature ships except the
  Gas Town one you want changed.
- **You habitually start notes with "…".** Examples: "…so the crew are just my
  large/xlarge model aliases…" and "…see above note". Any ellipsis-based sigil, in
  the Readwise or scholarly style, would collide with how you already write. `<`
  does not.

## 4. Prior art

- **The PDF model forbids it natively.** Every annotation belongs to one page. Zotero's
  lead developer: "I don't think it's possible for a PDF annotation to span multiple
  pages… if you exported to an external program, you'd necessarily end up with
  multiple annotations." Zotero has had open requests for cross-page merge and
  grouping since 2021, still unresolved in Sept 2026. DEVONthink users and staff
  reached the same conclusion. Skim can merge only same-page highlights. Apple
  Preview and PDFPen let a continuous-scroll selection cross a page, but headers and
  footers leak into the text.
- **Readwise ships the same idea at sync time.** You tag the first highlight's note
  `.c1` and the next `.c2` (continuing with `.c3`…), and "upon importing into Readwise,
  these two highlights will be combined", rendered "with an ellipse (…) between the two
  pieces". `.c1` always starts a new chain. Readwise needs numbered tags on *both*
  pieces. `<` needs one character on the follower only, because bob can rely on
  sidecar order.
- **Community workarounds point the same way.** Zotero users hand-edit page ranges
  ("9-10", exported as "pp. 9-10"). Several Zotero commenters propose Readwise-style
  continuation markers or an automatic "[…]" for gaps. A DEVONthink staffer objects
  that "guessing whether one annotation and the next belongs together isn't something
  DEVONthink should do", which argues for an explicit gesture.
- **Highlights itself** documents no merge or link feature. Its only note syntax is
  `#tag` (macOS, split-files mode). A "Smart Merge Annotations" row appears on its
  features page without explanation. It most likely refers to overlapping highlights
  on one page and cannot change the per-page constraint.

## 5. Critique: is this a good idea?

**Yes. The plan is sound in its three load-bearing choices:**

1. **The layer.** Merging belongs in bob's projection, not in Highlights or the PDF. It
   is reversible, needs no state, and agents see it through `bob ref show` for free.
2. **The gesture.** A note on the *follower* is typed at the moment you make the second
   highlight, with no navigating back to the first. In Highlights' own sidebar,
   `< PR Merge Master?!` reads naturally as "← continues; my thought".
3. **The character.** `<` points backward. It survives Markdown export unescaped (your
   sidecar proves it), and unlike `>` it does not collide with blockquote syntax. It
   needs no counter, unlike Readwise's `.c1`/`.c2`.

**Where the plan as stated would bite (and how §6 fixes each):**

| Risk | Unrefined behavior | Fix |
| --- | --- | --- |
| Misquoting | Joining "different points in a paragraph" seamlessly presents non-contiguous text as one sentence | Conservative seam rule (§6.4) |
| Task duplication | A follower's tasks re-hash under the head's block ID when `<` is added or removed, so tasks get re-created (text dedup only saves *unedited* tasks) | Processed IDs keyed per piece (§6.6) |
| Tombstone noise | The follower's old block is tombstoned as "no longer present", which is false. This happens on the very first run for Gas Town, and again whenever a scan lands between creating a highlight and typing `<` | Followers never tombstone (§6.6) |
| Sigil false positives | `<https://…>`, `<br>`, `<-`, `<3` would trigger merges | Whitespace-or-end rule (§6.2) |
| Silent non-merge | A `<` with nothing above it disappears, or quietly fails | Verbatim fallback plus report count (§6.8) |
| "Previous" surprises | A sticky note or figure between the pieces captures the merge | Skip non-text annotations (§6.3) |

**Would I take a different approach?** No. The alternatives (§8) are all worse:
auto-detection, colors, numbered tags, write-back, and PDF re-extraction. The one
direction worth keeping in mind for later is re-extracting quote text from the PDF's
own text layer using the highlight quads. That would also fix the "B eads" damage
(bob-cli-85) and enable geometric contiguity checks. It is a much bigger investment,
and this feature should not wait for it.

## 6. Design

### 6.1 Layer: a pure fold over parsed annotations

```text
sidecar ──parse──▶ [annotations] ──resolve_continuations──▶ [annotations + head/seam] ──render/tasks/assets
```

- `parse_sidecar_chunk` detects and strips the sigil on highlight comments, recording
  `continuation_requested: true`.
- `resolve_continuations` is a pure, separately tested function. It walks the
  annotations in order and assigns each requesting highlight a `head_order` and a
  `seam` (PageTurn | Elision), or marks it an orphan.
- Ordinals and per-piece IDs are computed **before** folding, so they are identical
  with or without `<`.
- Nothing is persisted. Every scan recomputes from the sidecar, so the result is
  idempotent and reversible.

### 6.2 Grammar

A text highlight is a **continuation** when the first non-blank line of its note,
after Highlights' list marker (`- `) and an optional `Comment:` or `Note:` label, matches
`^<(\s|$)`.

- Strip exactly that `<` and its following whitespace. If the line is then empty, drop
  it. Whatever remains is ordinary note text: comment prose, `#task` bullets, image
  paths.
- Strip the sigil from **both** `comment` and `task_source`. Otherwise `- < #task …`
  creates a task whose text starts with `<`.
- `<` followed by anything other than whitespace is *not* a sigil. This protects
  `<https://…>` autolinks, `<br>`, arrows like `<-` and `<=`, `<3`, and the
  angle-bracket-wrapped image paths image notes already accept
  (`<~/tmp/screenshots/x.png>`).
- `< ~/tmp/screenshots/x.png` works: it continues, and the screenshot becomes an image
  note on the merged block.
- Optional: a leading `\<` renders a literal `<` and does not merge. This is cheap and
  rarely needed.

Sigils considered and rejected:

| Sigil | Verdict |
| --- | --- |
| `>` on the head | Collides with blockquote export, and forces you back to the earlier highlight |
| `^` | Collides with Obsidian block-ID syntax, and reads as chat's "agree with above" |
| `+` | Already an unordered-list marker bob strips |
| `…` or `...` | Collides with your habit of opening notes with "…" (§3) |
| `.c1`/`.c2` | More typing, a counter, and edits on both pieces |
| A highlight color | Colors only reach Markdown as optional HTML, carry semantics you may want elsewhere, and leave no room for a comment |

### 6.3 What "previous" means

> **The head is the nearest earlier *text highlight* in sidecar order** (which is
> Highlights' sidebar order). The page-1 marker mirror, sticky notes, and image or area
> selections are skipped and keep their own blocks and positions.

- **Chains.** If the previous highlight is itself a follower, join *its* head. So A,
  `<`B, `<`C renders one passage, A+B+C.
- **No distance limit.** "The highlight above it in the sidebar" is the whole rule.
  A hidden page cap would be one more thing to remember.
- **Skipped items keep their place.** A sticky note sitting between two pieces renders
  right after the merged block. In document terms it is still "after A".
- **Self-healing.** If you delete and redo the head, `<` temporarily attaches to the
  highlight before it, then re-attaches on the next scan once the new head exists.
  Head IDs are unaffected (§6.6), so this costs one transient render, never a
  tombstone.
- **Followers are text highlights only (v1).** A sticky note or image selection whose
  note starts with `< ` is rendered verbatim and counted as an ignored continuation
  (§6.8). "Sticky note `<` adds a comment to the highlight above" is a reasonable v2.

### 6.4 The seam: honest by default

```text
seam(prev_piece, next_piece) =
  PageTurn  if page(next) == page(prev) + 1
            and (ends_mid_sentence(prev.text) or starts_lowercase(next.text))
  Elision   otherwise
```

- **PageTurn:** concatenate the raw texts with `\n`. The existing
  `beautify_annotation_text` reflows them into one paragraph and heals a word split
  across the page break (`imple-` + `mentation` → `implementation`). The result is
  seamless.
- **Elision:** join the beautified pieces with ` … ` (U+2026, spaced; Readwise's
  choice). Skip it if either side already ends or starts with an ellipsis, so you never
  get `… …`.
- `ends_mid_sentence`: the last character, after trailing whitespace, `*`/`_`
  emphasis, and closing quotes or brackets are stripped, is not one of `. ! ? …`.
  Colons, commas, dashes, and words all count as mid-sentence ("permanent hook:"
  continues).
- `starts_lowercase`: the first letter, after emphasis and opening quotes are
  stripped, is lowercase.
- `page()` parses the trailing integer of the page label ("Page 12", "p. 12"). A label
  that does not parse is never "consecutive", so it gets the elision.

Why conservative: a wrong seam has asymmetric cost.

- A seamless join over a real gap **misquotes the author**: the text reads as one
  sentence that does not exist.
- An ellipsis over contiguous text only claims an omission. The PDF is one click away.

Your two stated use cases land correctly:

- **Across pages** (the Gas Town case): "On every" ends mid-sentence, p11→12, seamless.
- **Different points in a paragraph** (same page): elision.

The rare miss is a mid-sentence clause on p. N joined to a lowercase clause at the top
of p. N+1 that is *not* its continuation. If that ever matters, a v2 "force gap" form
can be added; do not ship it now (§10).

### 6.5 Notes, tasks, and images in the merged block

- **Quote:** the head's text, then each piece in order, joined by its seam. Each piece
  keeps its own emphasis; underlines export as `**bold**`.
- **Comment:** one `[!note] Comment` callout.
  - Content: the head's note first, then each follower's remaining note text.
  - Each piece's text is its own paragraph (a `> >` blank line between).
  - Strip list markers per piece before joining: `strip_comment_list_markers` is
    all-or-nothing per text, so joining first could change how the head's comment
    renders.
  - The comment carries no "p. 12 said:" attribution. A merged highlight is one
    thought.
- **Image notes:** from any piece, embedded below the merged quote in piece order,
  exactly as today.
- **`#task` bullets:** from any piece, imported as usual. Identity rules are in §6.6.

### 6.6 Identity

| ID | Rule | Why |
| --- | --- | --- |
| Merged block `^h-` | The head's own `annotation_block_id`, unchanged | Adding, removing, or editing a continuation never churns the head, so existing `🔖` links to it stay live |
| Follower's own `^h-` | Computed (from raw ordinals) but never rendered; **added to the silent-drop set**, never tombstoned | Its content is visibly present in the head block. A "no longer present" tombstone would be false. |
| Task `[h:: …]` processed ID | Hashed from the **piece's own** block ID | Toggling `<` before or after a task exists never re-creates it |
| Task `🔖` backlink | Points at the **rendered** block (the head) | The link opens the quote the task came from |
| `block_ids_by_annotation_order` | A follower's order maps to the head's ID | Keeps image-task lookups consistent |

Implementation note: split `AnnotationTaskCandidate.source_block_id` into
`identity_block_id` and `link_block_id`.

The silent drop matters in practice:

- **The first real run.** On the first scan after this ships, the Gas Town note's
  `^h-434a5e5a2bc4` (the standalone p. 12 block) must vanish quietly. The result
  should be one block `^h-06d27eae3c84` under `### Page 11`, no `### Page 12`
  heading (nothing else is annotated on p. 12), and no new tombstone.
- **Everyday use.** Whenever the cron scan lands between "made the p. 12 highlight"
  and "typed `<`", the same thing happens.

One accepted gap: a task created from a follower's comment *while it stood alone*
keeps a `🔖` link to the follower's old ID, which no longer renders. Obsidian then
opens the note without jumping to the block. Optional hardening, if this ever shows
up: when a follower's note contains `#task` lines and its old ID was rendered before,
emit a one-line redirect stub under Removed highlights instead of dropping it
silently:

```md
> [!info] Merged highlight Now part of [[#^h-06d27eae3c84|the highlight on Page 11]].

^h-434a5e5a2bc4
```

### 6.7 Where the merged block lives

The merged block renders **under the head's page heading**, the way a citation starts
at "p. 11". Page headings are emitted only for pages that still have a rendered block.
The rendered region needs no page-range markup:

- `bob ref show` reports `page_label: "Page 11"`.
- `highlights_count` counts the merged block once.

**After** (the target rendering for your case):

```md
### Page 11

> [!quote] One last Crew tip: I have a new ad-hoc role that I’ve been using for the past week, called the “PR Sheriff.One of my B eads crew has a permanent hook: b d-4f43s: PR Sheriff Standing Orders. On every session startup, the sheriff checks open PRs and divides them into easy wins and those needing human review, then slings the easy wins to other crew for merging and cleanup
>
> > [!note] Comment PR Merge Master?!

^h-06d27eae3c84
```

"B eads" and "b d-4f43s" are not a merge artifact. Highlights' own text extraction
damages bob web-clip PDFs; `pdftotext` reads "Beads" and "bd-4f43s" cleanly. That is
tracked as bob-cli-85, and I added this instance as a +1.

**Your improvised case** (`agent_catalog_pane`), had the p. 16 note been just `<`:

```md
### Page 15

> [!quote] Enable relation:, artifact:, and linked: after the derivation report’s Phase 0 fix.
>
> > [!note] Comment After step 2 (i.e. in step 3)!

^h-…
```

**A same-page elision** (two points in one paragraph):

```md
> [!quote] Do this until every crew member is spinning, working on some task you gave them … hook it so they will continue working on it after a crash
```

### 6.8 Failure modes and reporting

| Situation | Rendering | Report |
| --- | --- | --- |
| `<` with no earlier text highlight in the PDF | Standalone block, note **verbatim** (the `<` stays) | `continuation_orphans` |
| `<` on a sticky note or image selection (v1) | Verbatim | `continuations_ignored` |
| Normal merge | One block, sigil consumed | `continuations: N` |

- **The rule you learn:** if you still see a `<` in the ref note, it did not merge.
- **Where the counts appear:** the verbose plan and scan JSON, mirroring the existing
  `image_notes` / `image_notes_unresolved` fields.
- **Optional:** a `doctor` library diagnostic `orphan_continuation`, found by spotting
  region comments that begin with `< `.

### 6.9 What does not change

- No new CLI subcommand, option, or config key. The feature is opt-in per annotation by
  construction, so there is no kill switch to design.
- No PDF or sidecar writes. Marker write-back is unaffected.
- No change to the region grammar, the `bob ref show` contract, bob-plugins, or Bob Mac
  Capture.

## 7. Requirement adjustments (called out)

| # | Your requirement | Adjusted to | Why |
| --- | --- | --- | --- |
| A1 | Note "starts with `<` (optionally followed by a space and note text)" | `<` followed by whitespace or end of note, on the first note line, after Highlights' list marker or `Comment:` label; `<x` is not a sigil | Removes false positives (`<https://…>`, `<br>`, `<-`, `<3`, wrapped image paths) without making real use any harder |
| A2 | Merge with "the previous one" | The previous **text highlight** in sidebar order (skip the marker, sticky notes, and image selections); chains allowed | Predictable from what you see in Highlights; one stray sticky note cannot hijack a merge |
| A3 | Merge highlight text (unspecified joint) | Seamless only on a mid-sentence page turn to the next page; otherwise ` … ` | Keeps quotes honest for your "different points in a paragraph" case |
| A4 | "and its notes" | Notes concatenate as paragraphs in one Comment callout; tasks and image notes keep working; task identity stays keyed per piece | Prevents duplicate tasks and stranded backlinks when `<` is toggled |
| A5 | (implicit) old block handling | The merged block keeps the head's `^h-`; a follower's old `^h-` is dropped silently, never tombstoned | Avoids false "Removed highlight" noise, including on the very first Gas Town run |
| A6 | (implicit) failure behavior | An unmergeable `<` renders verbatim and is counted in the scan report | The `<` disappears only when the merge happened |
| A7 | (scope) | v1: followers are text highlights only | Sticky-note and image followers need separate rendering rules; defer until wanted |

## 8. Alternatives considered

| Alternative | Verdict |
| --- | --- |
| **Auto-merge page-split highlights** (no sigil) | Rejected: about 50% precision on your own vault (§3), and wrong merges silently corrupt quotes. Even as a suggestion it is noise for ~1% of annotations. |
| **Readwise-style `.c1`/`.c2`** | Rejected: needs edits on both pieces plus a counter; `<` gets the same result from sidecar order. |
| **A dedicated "continuation" color** | Rejected: colors are not reliably in the Markdown sidecar, overload a visual channel, and leave no room for a comment. |
| **Forward sigil `>` on the head** | Rejected: collides with blockquote export, and requires going back. |
| **Write the merge back** into Highlights or the PDF | Impossible across pages (per-page annotations) and violates bob's read-only stance toward annotations. |
| **Edit the ref note by hand** | The managed region is regenerated every scan. |
| **Re-extract quote text from the PDF with highlight QuadPoints**, for exact contiguity and clean text | The best long-term direction (it also fixes bob-cli-85-style damage), but a large project. It should not block this feature. |

## 9. Implementation sketch

All in `src/native/highlights_ref/`:

1. **`model.rs`:** `SidecarAnnotation` gains `continuation: Continuation` with variants
   `None | Requested | Resolved { head_order, seam } | Orphan | Ignored`, plus
   `enum Seam { PageTurn, Elision }`.
2. **`sidecar.rs`:**
   - `strip_continuation_sigil` runs in `parse_sidecar_chunk`, highlights only, on
     both `comment` and `task_source`.
   - `resolve_continuations(&mut [SidecarAnnotation])` runs once in
     `read_sidecar_for_pdf` after parsing. It is pure, owns the "previous text
     highlight" walk and the seam rule, and restores the verbatim sigil for orphans.
3. **`sidecar_render.rs`:**
   - Skip followers in `render_sidecar_highlights`.
   - Build each head's merged quote (seam join, return-link stripping per piece) and
     merged remaining-note text (per-piece label and list stripping, then join).
   - Map follower orders to the head ID in `block_ids_by_annotation_order`.
   - Extend the silent-drop set with followers' own IDs.
   - Record `continuations` and orphan counts on `RenderedHighlights`.
4. **`annotation_tasks.rs`:** split `source_block_id` into `identity_block_id` (the
   piece's own ID, for `[h::]`) and `link_block_id` (the rendered head, for `🔖`).
5. **`report.rs` / `scan_json.rs`:** `continuations`, `continuation_orphans`, and
   `continuations_ignored`, mirroring the `image_notes` fields.
6. **Docs:**
   - `docs/highlights-ref-sync.md`: a new `### Continuation notes` section after
     `### Image notes`, plus a line in "Generated Body Contract".
   - After acceptance, record a `decisions` strand ("Continuation notes merge at render
     time") and add a `glossary` term ("Continuation Note"), both via
     `/sase_memory_write`.
7. **Tests:**
   - Sigil table (positive and negative).
   - Grouping: chains; skipping marker, notes, and images; orphan; ignored kinds.
   - Seam rule: mid-sentence page turn → seamless with hyphen heal; sentence boundary
     → elision; same page → elision; non-numeric label → elision; no doubled `…`.
   - ID stability: the head ID is unchanged with or without a follower; a follower's
     old ID is not tombstoned.
   - Task dedup across a `<` toggle.
   - A golden fixture from the real Gas Town p. 11–12 sidecar text.

Size: bounded and single-module, with no CLI surface. One `medium` tale-sized task,
or `large` if the planner wants the optional redirect stub and doctor diagnostic
included.

**MacBook validation** (real Highlights files):

- `<` survives in TextBundle `text.md` as it does in `.md`.
- A comment that Highlights exports as a list item (`- < …`) merges.
- In a **two-column paper**, the sidebar or export order follows reading order. If
  Highlights sorts purely by y-coordinate across columns, "previous" can surprise
  there. The rule stays the same; document it.

## 10. Open questions for Bryan

1. **Seam honesty versus beauty.** Do you want the conservative seam (§6.4)? Or would
   you rather always join seamlessly, which is prettier and occasionally dishonest?
   I recommend conservative.
2. **Force-gap override.** If cross-page mid-sentence joins of *non*-contiguous text
   turn out to happen, would you accept a v2 form such as `<…`/`<...` (no space)? Your
   "…" habit makes any ellipsis form slightly risky, so I would only add it on demand.
3. **Sticky-note followers.** Do you want a sticky note starting with `< ` to attach
   as an extra comment to the highlight above? (v1 says no.)

## 11. Side findings (filed)

- **`bob-cli-9o` (new bug, large):** highlight block IDs hash `ordinal_on_page`.
  Adding one highlight *above* others on a page re-mints and tombstones every later
  ID on that page.
  - Proof from vault history: commit `69d1050c` added the p. 9 caption highlight and
    tombstoned three unchanged p. 9 highlights (`ab3f80f326b4`, `4462b6562b19`,
    `028f34fba39e`).
  - That accounts for 3 of the Gas Town note's 5 tombstones, and it breaks `🔖` task
    backlinks.
  - The continuation design above deliberately computes IDs from raw, pre-fold
    ordinals, so it adds no new churn. It inherits this existing fragility until
    bob-cli-9o is fixed.
- **`bob-cli-85` (+1):** Highlights' extraction of bob web-clip PDFs drops and splits
  characters ("B eads", "b d-4f43s", "jusone", "nowatching", "Sheriff.One"), while
  `pdftotext` reads the same pages cleanly. Merged passages make this damage more
  visible, but they do not cause it.

## 12. Recommended solution

Ship a **render-time continuation fold** in `bob ref`, as specified in §6.

1. **Trigger.** A text highlight whose note begins with `<` plus whitespace or the end
   of the note (after any list marker or `Comment:` label) continues the nearest earlier
   text highlight in Highlights' sidebar order. Chains are allowed. The marker, sticky
   notes, and image selections are skipped.
2. **Rendering.** The pieces render as one `[!quote]` block under the head's page
   heading.
   - A mid-sentence turn onto the next page joins seamlessly and heals hyphens.
   - Every other seam shows ` … `.
   - Notes merge, in order, into one Comment callout, with tasks and image notes
     intact.
3. **Identity.** The merged block keeps the head's `^h-` ID, and follower IDs drop
   without tombstones. Task `[h::]` IDs stay keyed to the piece they came from, while
   `🔖` links target the merged block.
4. **Failure.** A `<` that cannot merge renders verbatim and is counted in the scan
   report.
5. **Scope.** No new flags, no config, no PDF or sidecar writes, no format change for
   `bob ref show` or the plugins. Document it in `docs/highlights-ref-sync.md`, and
   record the decision once you accept it.

On the next Mac scan, your Gas Town p. 11–12 passage becomes one quote with "PR Merge
Master?!" beneath it, `^h-06d27eae3c84` stays put, and no tombstone appears.

---

## Sources

- Bob code: `src/native/highlights_ref/{sidecar.rs, sidecar_render.rs, annotation_tasks.rs, region.rs, text.rs, image_notes.rs, sync.rs}`, `src/native/ref_library/show.rs`; `docs/highlights-ref-sync.md`
- Vault evidence (read-only): `~/bob/lib/**` sidecars; `~/bob/ref/blogs/gas_town_emergency_user_manual.md` and its git history (`94b786eb`, `69d1050c`); `pdftotext` on `lib/blogs/gas_town_emergency_user_manual.pdf`
- Screenshot: `~/tmp/screenshots/20261019_063505.png`
- [Readwise — Action tags guide](https://docs.readwise.io/readwise/guides/action-tags)
- [Readwise Reader — Action tags FAQ](https://docs.readwise.io/reader/docs/faqs/action-tags)
- [Readwise blog — Combine highlights on the fly (2018)](https://blog.readwise.io/combine-highlights-on-the-fly/)
- [Zotero forums — Feature Suggestion: Merge annotations](https://forums.zotero.org/discussion/89572/)
- [Zotero forums — PDF Reader: Highlighting across page breaks](https://forums.zotero.org/discussion/comment/385205/)
- [DEVONthink forum — Highlighted propositions broken between two pages](https://discourse.devontechnologies.com/t/highlighted-propositions-broken-between-two-pages/67496)
- [Highlights app — features, FAQ, sidecar files, export how-tos](https://highlightsapp.net/)
- Beads: `bob-cli-9o` (filed), `bob-cli-85` (+1)
