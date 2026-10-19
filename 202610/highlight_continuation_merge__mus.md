# Merging split Highlights annotations with a `<` continuation marker

**Researcher:** mus · **Date:** 2026-10-19 · **Swarm:** 5-researcher (mus/cdx/cld/grk/gem, independent)
**Request:** Bryan wants `bob ref` to automatically merge a Highlights highlight
(and its notes) with the previous one in the generated ref note when the
highlight's note starts with `<` (optionally followed by a space and note text),
because the Highlights app cannot make one highlight/note span pages or
non-contiguous points in a paragraph.

**Verdict up front:** yes, do it — but implement it as a **render-stage,
comment-gated, adjacent-highlight-only merge** with three adjustments to the
proposal: (1) the `<` signal is recognized **only in a highlight's comment**,
never in standalone notes; (2) the merged block **keeps the first annotation's
block ID** so existing `^h-…` links don't churn; (3) a dangling `<` (nothing
mergeable before it) **warns instead of merging** and renders literally. Details
and rationale below, ending with a concrete recommended spec.

---

## 1. What the screenshot shows

`~/tmp/screenshots/20261019_063505.png` (Highlights app, `gas_town_emergency_user_manual.pdf`,
page 11 of 15) demonstrates the exact pain:

- One sentence is split by a page break / figure caption into **two yellow
  highlights**: `"One last Crew tip: … On every"` (top of p.11, ending
  mid-sentence) and `"session startup, … merging and cleanup."` (bottom of
  p.11, starting mid-sentence with a lowercase continuation).
- The right sidebar shows them as **two separate entries** (`Page 11` quote
  ending in "On every", then a `Page 12`-style second entry for the
  continuation) — the app gives Bryan no way to join them.
- The continuation highlight carries the note **`< PR Merge Master?!`**.
  Under the proposal, that leading `<` ("pointing back" at the previous
  highlight) would cause `bob ref scan`/`sync` to render the two fragments as
  **one quote** in the ref note, with the remainder (`PR Merge Master?!`) kept
  as (part of) the merged comment.

This is a real, recurring limitation (any sentence crossing a page boundary or
interrupted by a figure), and the example is well-chosen: the break point is
mid-clause, lowercase-to-lowercase, so a naive concatenation with a space
produces correct prose.

---

## 2. How the current pipeline works (what the merge must fit into)

All paths below are in this repo (`bob-cli_13` checkout); I read the source,
not just the docs.

### 2.1 Sidecar → annotations

- Bob never talks to the Highlights app live. It reads the **sidecar** beside
  the PDF (`foo.md`, or `foo.textbundle/text.md`) via
  `discover_sidecar_path` / `read_sidecar_for_pdf`
  ([sidecar.rs](/home/bryan/.local/state/sase/workspaces/bobs-org/bob-cli/bob-cli_13/src/native/highlights_ref/sidecar.rs)).
- `parse_sidecar_markdown` splits on page headings (`## Page N`, also linked
  `#### [Page N](highlights://…)` shape) and horizontal rules; each chunk
  becomes one `SidecarAnnotation` (`Highlight` | `Image` | `StandaloneNote`)
  with `page_label`, `text` (quote), `comment` (note text after the quote, with
  a `Comment:`/`Note:` label stripped), `task_source`, `order` (global), and
  `ordinal_on_page` ([model.rs](/home/bryan/.local/state/sase/workspaces/bobs-org/bob-cli/bob-cli_13/src/native/highlights_ref/model.rs),
  [sidecar.rs](/home/bryan/.local/state/sase/workspaces/bobs-org/bob-cli/bob-cli_13/src/native/highlights_ref/sidecar.rs)).
- Key consequence: **by the time Bob sees the data, the two fragments are two
  fully independent annotations** in sidecar order, possibly under different
  page headings. Any merge is therefore a Bob-side synthesis, invisible to
  Highlights (good: one-way sync preserved, per the generated-body contract in
  [highlights-ref-sync.md](/home/bryan/.local/state/sase/workspaces/bobs-org/bob-cli/bob-cli_13/docs/highlights-ref-sync.md)).

### 2.2 Block IDs and tombstones (the load-bearing constraint)

- Each highlight/standalone block gets a stable `^h-…` ID:
  `annotation_block_id` hashes `(source_pdf, kind, page_label, ordinal_on_page,
  normalized_identity_text(text))`
  ([sidecar_render.rs](/home/bryan/.local/state/sase/workspaces/bobs-org/bob-cli/bob-cli_13/src/native/highlights_ref/sidecar_render.rs)).
  Identity uses the **raw** sidecar text; prettification is render-only.
- Disappeared IDs **tombstone** under `### Removed highlights` instead of
  vanishing; mirror-shaped/preamble blocks are the only silent drops.
- Consequence: a merge that simply concatenates texts and re-hashes **changes
  both IDs**, so enabling the feature on an already-synced library would
  tombstone two good blocks and mint a third — churning history and breaking
  inbound `[[ref/x#^h-…]]` links (annotation follow-up tasks link to these
  blocks). The design must decide ID policy explicitly (see §6.4; my
  recommendation anchors the merged ID to the first fragment).

### 2.3 Rendering and text cleanup

- Highlights render as `> [!quote]` callouts with the comment nested as
  `> > [!note] Comment`, grouped under `### Page N` headings; standalone notes
  are `> [!note]` callouts
  ([sidecar_render.rs](/home/bryan/.local/state/sase/workspaces/bobs-org/bob-cli/bob-cli_13/src/native/highlights_ref/sidecar_render.rs)).
- Quote text is beautified render-only: line reflow, hyphen-healing at join
  points (lowercase continuation drops the `-`, uppercase/digit keeps it),
  ligature/space normalization ([text.rs](/home/bryan/.local/state/sase/workspaces/bobs-org/bob-cli/bob-cli_13/src/native/highlights_ref/text.rs)).
  A cross-highlight join should reuse exactly this hyphen logic at the new
  boundary (the screenshot's boundary needs only a space, but hyphenated
  page-break words are the common case in two-column PDFs).
- Highlight comments can mint Obsidian tasks: any bullet line whose item text
  contains a `#task` token is copied as a task while the ref status is open
  ([highlights-ref-sync.md](/home/bryan/.local/state/sase/workspaces/bobs-org/bob-cli/bob-cli_13/docs/highlights-ref-sync.md)).
  Merged comments must preserve task intake from **both** fragments.

---

## 3. Critique of the proposed plan

### 3.1 Is it a good idea? Yes — with the scope narrowed

**For:**

- The limitation is real and frequent (page breaks, figure interruptions,
  paragraph re-entry points). Highlights upstream is unlikely to add spanning
  selections; a Bob-side convention is the pragmatic layer to fix it in,
  consistent with the standing decision that Bob owns rendering while
  Highlights owns capture data (`mac-capture-is-a-thin-client` is the sibling
  expression of this philosophy; the Highlights equivalent is "Bob never
  creates or mutates sidecars, it only reads" in
  [highlights-ref-sync.md](/home/bryan/.local/state/sase/workspaces/bobs-org/bob-cli/bob-cli_13/docs/highlights-ref-sync.md)).
- A one-character in-band marker is the *only* channel available: Highlights
  notes are plain text with no metadata, and asking Bryan to hand-edit
  generated Obsidian regions fights the managed-region contract (hand edits
  inside `<!-- highlights:begin/end -->` may be overwritten).
- `<` reads naturally as "joins to the thing above," matching the sidebar's
  top-to-bottom order, and the "optionally followed by a space and note text"
  shape lets the continuation carry its own comment (the screenshot's
  `< PR Merge Master?!` is exactly this).

**Against / risks (all manageable, none fatal):**

- **In-band signaling collides with real text.** Comments can legitimately
  start with `<` (HTML like `<div>`, math like `< 5`, arrows like `<-`, the
  `<3` heart). The proposal's "optionally followed by a space" already
  excludes `<div`, but `< 5` or `<- fix` would false-positive. Mitigation: only
  treat `<` as a signal in a narrow, documented position (start of the
  *stripped* comment), provide an escape (`\<`), and warn on dangling merges
  so surprises surface in `scan --dry-run` instead of silently eating text.
- **Silent text destruction is the worst failure mode.** If `<` misfires, a
  comment's first two characters vanish into machinery. The design must make
  the non-merge path byte-preserving (render the `<` literally) and the merge
  path previewable.
- **Link-stability churn** (§2.2) if IDs are re-hashed naively. Fix with ID
  anchoring (§6.4).
- **Scope creep into notes.** "Merge a highlight (and its notes)" is ambiguous
  about standalone notes. Standalone notes have no quote to join; letting them
  merge (or be merged into) complicates the model for no demonstrated use case.
  Narrow to highlight comments only.

### 3.2 Would I take a different approach? Considered and rejected

| Alternative | Why not |
|---|---|
| Suffix marker on the *first* fragment (e.g. trailing `>`) | Marks intent at the break, but you often don't know a break needs marking until you've made the second highlight; editing the first note retroactively is more taps in Highlights than prefixing the new one. Also collides with blockquote/arrow text. |
| Trailing `…` / leading `…` auto-join (no marker) | Magical: every sentence-fragment highlight would glue itself to its neighbor, including intentional fragments. Explicit beats inferred. |
| Merge in the PDF via lopdf annotation rewrite | Fights the "Bob never mutates Highlights-owned data" rule; risks corrupting signed/byte-sensitive PDFs; invisible in the app anyway. |
| Hand-edit the generated Obsidian region | Violates the managed-region contract; next scan overwrites it. |
| Multi-select join in Highlights | Doesn't exist upstream; waiting on it is not a plan. |
| A second marker direction (`>` = merge with next) | Forward references break streaming render and idempotency reasoning; backward-only (`<`) keeps a single left-to-right pass. Don't add it. |

The `<`-prefix-on-continuation is the right call. Keep it backward-only and
highlight-comment-only.

---

## 4. Design details that must be nailed down

### 4.1 Where the marker lives and what exactly matches

- Recognize the signal **after** the existing comment normalization (list-marker
  strip, `Comment:`/`Note:` label strip) so `- < foo`, `* < foo`, and
  `Comment: < foo` all work — Bryan will type all three in the app.
- Grammar: `^<(\s+(.*)|\s*)$` on the stripped comment — i.e. `<` followed by
  end-of-text (bare join) or whitespace + remainder. `<div`, `<-x`, `<3` never
  match because there is no space. This is exactly the proposal's "optionally
  followed by a space and note text," tightened into a testable rule.
- Escape: a comment starting with `\<` renders as literal `<…` and never
  merges. Document it once; implement it in the same strip function.
- The `<` line may be the whole comment or the first line of a multi-line
  comment — only the first line carries the signal; the rest is ordinary
  remainder text. (Highlights notes in the linked-page export shape arrive as
  list items; the strip pipeline in
  [sidecar_render.rs](/home/bryan/.local/state/sase/workspaces/bobs-org/bob-cli/bob-cli_13/src/native/highlights_ref/sidecar_render.rs)
  already flattens those.)

### 4.2 What may merge with what

- **Both sides must be `Highlight` kind**, adjacent in sidecar `order` after
  skipping marker mirrors (a mirrored marker between two fragments must not
  block the merge — mirrors are excluded from rendering anyway per
  `is_sidecar_marker_mirror`). Everything else blocks: image selections,
  standalone notes, preamble, page structure never blocks (cross-page is the
  point).
- **Chains work**: `H1, H2(<…), H3(<…)` renders one block. Implement as a fold:
  when annotation *i* carries the signal and the current run's last emitted
  unit is a mergeable highlight, append; else start a dangling-`<` warning.
- **Only the immediately previous rendered unit** qualifies — never "search
  backward past a standalone note for a highlight." Predictability beats
  cleverness; the sidebar order is the mental model.
- Standalone notes starting with `<` are **not signals** (adjustment #1).
  Rationale: nothing to join the quote to, and `<`-led standalone text (code,
  HTML, math) is far more common than a desire to glue a note onto a quote.
  If a future use case appears, it can be proposed separately.

### 4.3 Joining the quote text (the "beautiful" part)

- Join as `prev_text + boundary + next_text` where the boundary reuses the
  existing hyphen-healing rule from
  [text.rs](/home/bryan/.local/state/sase/workspaces/bobs-org/bob-cli/bob-cli_13/src/native/highlights_ref/text.rs):
  if `prev` ends with `-` (or `‐`) preceded by a letter and `next` starts
  lowercase → drop the hyphen (`encap-` + `sulation` → `encapsulation`); if
  `next` starts uppercase/digit → keep hyphen and join without space
  (`Marie-` + `Curie`); otherwise join with exactly one space, regardless of
  trailing/leading whitespace in the fragments. Then run the whole through the
  existing `beautify_annotation_text` so reflow/normalization stay uniform.
- Do **not** insert a visible seam (no `…`, no `//`, no pilcrow) by default:
  the entire point is that the sentence reads as the author wrote it. The
  page-range heading (§4.5) is where the join is disclosed, keeping the prose
  clean. (Optionally record the seam page in an HTML comment for debugging —
  invisible in reading view.)
- Hyphen edge: a prev-fragment ending in an em/en-dash or a next-fragment
  starting with punctuation (`,`, `.`, `;`, `)`, `'s`) joins with **no space**.
  Small rule, big beauty payoff for mid-sentence breaks before commas/quotes.

### 4.4 Merging the comments

- merged_comment = `prev.comment` + (remainder of continuation) with rules:
  - bare `<` (empty remainder) → keep `prev.comment` as-is;
  - both present → join with a space (both are already stripped/beautified
    fragments; a paragraph break between them overstates the seam — these were
    one reading moment);
  - only remainder → it becomes the comment (the screenshot case: prev has no
    comment, merged comment is `PR Merge Master?!`).
- Task intake must see the **concatenated task_source** of both fragments so
  `#task` lines on either side still mint tasks. Equally, image-note lines
  (`~/tmp/screenshots/….png` pasted in either fragment's note) must still
  resolve — concatenate before `split_image_note_lines`, not after.
- The `<` sigil itself never reaches the rendered comment.

### 4.5 Page headings (where cross-page beauty lives)

- Today each annotation renders under its own `### Page N`. A merged block
  spanning pages must not sit under a single misleading heading.
- Rule: if all fragments share a page → that heading (unchanged). If pages
  differ → `### Pages 11–12` (en-dash range, first-to-last in sidecar order;
  chains give `Pages 11–13`). Non-numeric labels (`p. 12`, linked-page labels)
  range the same way on their numeric parts; unparseable labels fall back to
  the first fragment's heading. This is the one visible trace of the merge,
  and it reads naturally in the ref note's table of contents.
- `bob ref show` (human/markdown/JSON): the merged entry carries the ranged
  label; JSON gains no new schema — `page_label` is already a string — but the
  value may now contain the range. Call this out in docs for the Refs-panel
  consumers.

### 4.6 Block IDs and the unmerge story (reliability core)

- **Anchor the merged block's ID to the first fragment**: compute it as if the
  first annotation's `(page_label, ordinal_on_page, kind)` were paired with
  the **merged** text? No — that still churns the first ID the moment a merge
  is added. Two candidate policies:
  - **(A) Keep-first-ID**: merged block reuses the first fragment's existing
    ID byte-for-byte (computed from the first fragment's text alone). Old
    `[[ref/x#^h-…]]` links to the first fragment keep working; the
    continuation's old ID (if it ever synced unmerged) retires **silently**
    (add to the silent-drop set alongside mirror/preamble IDs, with a dry-run
    note, not a `Removed highlight` tombstone — the content isn't removed,
    it's absorbed).
  - **(B) Re-hash merged text**: new ID, two tombstones. Link-breaking churn
    on every retroactive merge.
- **Recommend (A).** Cost: two different contents (unmerged-first vs. merged)
  share one ID during the transition — acceptable because the merged text is a
  strict extension the author explicitly declared as one thought, and the
  alternative (B) breaks links Bryan already pasted into tasks/notes. The
  continuation fragment must never have tasks pointing at its solo ID for long:
  in practice the `<` is typed at capture time, before the first scan, so the
  solo ID never escapes. Document the retroactive-merge caveat (old links to
  the second fragment go stale, shown once as a dry-run warning, no tombstone
  spam).
- **Unmerge** (Bryan deletes the `<` in Highlights, or deletes the
  continuation): the merged ID's text no longer matches; render the fragments
  separately again with their natural IDs and tombstone the merged block
  normally. Standard machinery, no special case — but only correct if the
  merge stays a pure render-stage fold (next point).

### 4.7 Pipeline stage: fold at render, not at parse

- Implement the merge as a **fold over parsed `SidecarAnnotation`s inside
  `render_sidecar_highlights`**, producing merged units before ID assignment
  and rendering. Do not mutate the parser: `parse_sidecar_markdown`,
  ordinals, marker-mirror detection, and task/image pipelines keep their
  current unit tests and semantics; the merge is one well-tested function
  `merge_continuations(annotations) -> (units, warnings)` plus renderer
  support for ranged headings.
- Why render-stage: parse-stage merging would shift `ordinal_on_page` for every
  later annotation on the page (ordinals feed IDs → mass churn); a render fold
  can preserve each survivor's addressing while consuming continuations
  silently.

### 4.8 Failure modes must be visible, never silent

- **Dangling `<`** (first annotation in the file, previous unit is an image /
  standalone note / mirror-only gap, or previous unit is on a removed path):
  render the comment **literally with the `<` intact**, emit a per-PDF warning
  surfaced in `sync --dry-run` / `scan --dry-run -v` and counted in the summary
  (new `continuations_dangling: N` counter, exit status unchanged — warnings,
  not failures, matching the image-note philosophy of self-healing states).
- `bob ref doctor`'s library-diagnostics roll-up is the natural home for a
  persistent "N dangling continuation markers" hint with example paths.
- Dry-run preview shows `continuations: 2 merged · 1 dangling` per PDF so Bryan
  can proof the joins before writing.

### 4.9 What stays out of scope (say no now)

- No forward (`>`) markers, no merge across different PDFs, no merging image
  selections (their IDs are content-addressed on image bytes; gluing quotes
  around them is incoherent), no merging into/inside `### Removed highlights`,
  no marker-write-back of anything merge-related to the PDF (one-way sync
  stays one-way; the `<` lives and dies in Highlights).
- No config flag for v1: ship the grammar fixed (`<` + space-or-end, `\<`
  escape). If false positives ever bite, add `highlights.continuation_marker`
  then — not before. (Per repo convention, new CLI surface needs
  `sase/memory/cli_rules.md` review; this design deliberately adds none.)

---

## 5. Beauty checklist (what "intuitive, reliable, beautiful" cashes out to)

- The merged quote reads as **one sentence** — no seam glyphs, correct
  hyphen/space/punctuation joins, single `> [!quote]` callout.
- The page-range heading (`### Pages 11–12`) tells the truth about provenance
  without cluttering prose.
- The continuation's note text survives as the (or part of the) merged
  comment — the screenshot's `PR Merge Master?!` must not be eaten by the
  machinery that joins the quotes.
- Idempotency: re-scanning with no sidecar change writes byte-identical notes
  (atomic-write skip path already handles this; the fold must be deterministic
  in the face of equal texts — dedupe identical adjacent fragments before
  merging so `H,H(<)` with identical text doesn't fork).
- The feature is discoverable: one docs section with three examples (basic
  join, bare `<`, chain + dangling warning), each showing Highlights-side text
  and ref-note output.

---

## 6. Recommended solution (spec for the implementing agent)

1. **Grammar** (comment pipeline, after `Comment:`/`Note:` label and list-marker
   stripping): `^<(\s+(?P<rest>[\s\S]*)|\s*)$`. On match → continuation with
   `rest` (possibly empty). `^\\<` → literal, strip one backslash. Everything
   else → ordinary comment (byte-preserving, `<` intact).
2. **Eligibility**: continuation merges iff the previous *emitted render unit*
   is a `Highlight` that was itself rendered (not a skipped mirror). Markers
   mirrors are skipped transparently; images, standalone notes, and file start
   make it dangling.
3. **Fold**: single left-to-right pass in `render_sidecar_highlights`;
   support chains; collect `(merged_units, dangling_warnings)`.
4. **Text join** (§4.3): hyphen-aware boundary + punctuation-aware spacing,
   then existing `beautify_annotation_text` over the whole.
5. **Comment join** (§4.4): `prev.comment ⊕ rest`; task/image-note splitting
   runs on the concatenated source so `#task` and screenshot paths from either
   fragment survive.
6. **Heading**: shared page → `### Page N`; spanning → `### Pages A–B`
   (en dash); unparseable → first fragment's label.
7. **IDs**: merged block keeps the **first fragment's block ID** (policy A);
   consumed continuation IDs retire silently (extend the silent-drop set for
   exactly the consumed orders); unmerge falls back to stock tombstone
   behavior. Task `h::` markers and `ht-` source links follow the merged unit.
8. **Visibility**: per-PDF `continuations: M merged · D dangling` in dry-run /
   verbose plans; dangling renders literally + warns; `doctor` rolls up
   dangling counts. No new CLI flags; no marker write-back.
9. **Tests** (repo convention: unit tests beside the module in
   `src/native/highlights_ref/tests/`): grammar table (bare `<`, `< rest`,
   `<div`, `<3`, `\<`, list-wrapped, `Comment:`-wrapped); join table
   (lowercase space-join, hyphen-drop, hyphen-keep, punctuation, chains);
   heading ranges; ID-anchoring (old link to first fragment resolves
   post-merge); dangling literalness; idempotency (double render byte-equal);
   unmerge tombstones; `#task`/image-note survival across the join; mirror
   between fragments doesn't block.
10. **Docs**: one new subsection in
    [highlights-ref-sync.md](/home/bryan/.local/state/sase/workspaces/bobs-org/bob-cli/bob-cli_13/docs/highlights-ref-sync.md)
    ("Continuation highlights (`<`)") with the grammar, the three adjustments
    called out, and before/after examples including the Gas Town PR-Sheriff
    sentence from the screenshot.

### Adjustments to the original requirements (explicit, as asked)

- **A1 — signal scope narrowed**: `<` merges only from a *highlight comment*.
  Standalone notes starting with `<` are literal text. (Proposal read as "the
  highlight note," which I take to mean the same thing — this makes it
  explicit and closes the standalone-note hole.)
- **A2 — ID anchoring added**: merged block keeps the first fragment's `^h-…`
  (proposal was silent; naive implementation churns links).
- **A3 — dangling behavior specified**: warn + render literally (proposal was
  silent; silent eating of `<` text would be the ugliest failure).
- **A4 — no forward markers, no config, no PDF write-back** (proposal didn't
  ask for these; stating the negative scope so the implementer doesn't invent
  it).

---

## 7. Sources consulted

- Screenshot `/home/bryan/tmp/screenshots/20261019_063505.png` (Gas Town
  Emergency User Manual, p.11 split highlight + `< PR Merge Master?!` note).
- [highlights-ref-sync.md](/home/bryan/.local/state/sase/workspaces/bobs-org/bob-cli/bob-cli_13/docs/highlights-ref-sync.md)
  (sidecar shapes, generated-body contract, image notes, task intake,
  tombstones, dry-run/doctor conventions).
- [ref.md](/home/bryan/.local/state/sase/workspaces/bobs-org/bob-cli/bob-cli_13/docs/ref.md)
  (`ref show` annotation model consumed by humans, markdown, JSON, and the
  Mac Refs panel).
- `src/native/highlights_ref/sidecar.rs`, `sidecar_render.rs`, `text.rs`,
  `model.rs` (parser, renderer, beautifier/identity split, block-ID hashing,
  marker-mirror and silent-drop sets).
- Prior swarm-adjacent research filenames in `sase/repos/research/202610/`
  avoided by stem choice; no peer report was opened (only filenames listed to
  avoid collision), per the independence rule.

*Independence note: this report was produced without reading any peer
`__cdx/__cld/__grk/__gem` report or transcript; conclusions are my own.*
