# Continuation highlights: merge with `<` in `bob ref`

- **Researcher:** grk
- **Date:** 2026-10-19
- **Question:** When Highlights cannot span a highlight (or its note) across a page break or across two points in a paragraph, should `bob ref` merge the new highlight with the previous one whenever the highlight's note starts with `<`? How should that feel, stay reliable, and look in the ref note?
- **Verdict:** Yes. Keep Bryan's `<` gesture. Implement it as **render-time grouping** inside `bob ref scan` / `sync`. Do not mutate the sidecar or the PDF. Tighten the matcher, pin identity to the first highlight, and join the quotes with the beautify path that already heals wrapped PDF lines.

---

## 1. In one breath

Highlights cannot store a single highlight that crosses a page. PDF highlight annotations are page-scoped (quads live on one page). Bryan already works around that in the only place he can while reading: he highlights the overflow, then types a note that starts with `<`.

The 2026-10-19 screenshot (`~/tmp/screenshots/20261019_063505.png`) is the whole product:

- Page 11 quote ends mid-sentence: `… PR Sheriff Standing Orders. On every`
- Page 12 quote continues: `session startup, the sheriff checks open PRs…`
- Page 12 note: `< PR Merge Master?!`

The Mac scan has already written that into the vault as **two** callouts, and the `<` is still sitting in the comment:

```md
### Page 11

> [!quote] One last Crew tip: … On every

^h-06d27eae3c84

### Page 12

> [!quote] session startup, the sheriff checks open PRs …
>
> > [!note] Comment < PR Merge Master?!

^h-434a5e5a2bc4
```

The reading note should be one thought:

```md
### Page 11–12

> [!quote] One last Crew tip: I have a new ad-hoc role that I've been using for the past week, called the "PR Sheriff." One of my Beads crew has a permanent hook: bd-4f43s: PR Sheriff Standing Orders. On every session startup, the sheriff checks open PRs and divides them into easy wins and those needing human review, then slings the easy wins to other crew for merging and cleanup.
>
> > [!note] Comment PR Merge Master?!

^h-06d27eae3c84
```

That is a good idea. The raw rule ("starts with `<`") is almost the right rule. The work is to make the matcher boring, the identity stable, and the callout beautiful.

---

## 2. Is this a good idea?

**Yes.** Three properties make it the right layer:

1. **The PDF cannot hold the thought.** A `Highlight` annotation's `QuadPoints` are on one page. DEVONthink's forum states the same limit, and Highlights' own changelog never describes cross-page text selection. "Smart Merge Annotations" on [highlightsapp.net/features](https://highlightsapp.net/features/) is a free-tier product bullet; it is the wrong tool for this screenshot. Even if the app joins overlapping markups on one page, it still has to emit two PDF annotations for a page-break sentence, and bob's sidecar parser is 1:1 with those annotations.
2. **The gesture is already in Bryan's fingers.** He typed `< PR Merge Master?!` in Highlights while looking at page 12. That is both the merge directive *and* the real note. Zero extra UI, zero new command, zero trip into Obsidian. The same prefix works for the second stated use (two non-adjacent spans in one paragraph): highlight the pieces you want, mark every overflow with `<`.
3. **bob already owns the reading surface.** Sidecar parse → callout render → `^h-` identity → annotation tasks. Comments are not part of the block-id hash. Beautify already reflows wrapped PDF lines and heals `through-` + `put`. The feature is a grouping pass in that pipeline, not a new product.

What would make it a bad idea:

- silently joining every page-break pair (this same note has nested short-plus-long highlights on pages 4, 5, 6, and 7; auto-merge would wreck them);
- rewriting the sidecar (Highlights owns it; bob's contract is "never create or mutate sidecars");
- tombstoning the continuation under `### Removed highlights` (the gas-town note already has five of those from earlier edits; an intentional merge must not add a sixth);
- changing `[h::]` when the 🔖 target moves (that recreates follow-up tasks).

The design below closes those.

---

## 3. Critique of the plan as stated

The plan: *"`bob ref` automatically merge a highlight (and its notes) with the previous one in the corresponding ref note iff the highlight note starts with `<` (optionally followed by a space and note text)."*

### What is right

- **Opt-in per annotation, in the app where the reading happens.** The prefix lives in the highlight comment, survives every scan, and unmerges when deleted. That is the same philosophy as image notes (a screenshot path pasted into the comment) and `#task` bullets.
- **Merge quotes and notes together.** The screenshot's comment belongs to the combined thought, not to the page-12 fragment.
- **Previous in ref-note order.** Sidecar document order is already the render order. No timestamps, no geometry, no "closest highlight on the previous page."
- **No Highlights feature request as the path.** The app is closed. bob is the reading-note compiler.

### What is incomplete or unsafe

1. **"Starts with `<`" is too loose.** After label/list stripping, that would also match `< 0.05`, `<= 5`, `<<`, `<div>`, and the image-note wrapper `<~/tmp/screenshots/foo.png>` that `image_notes.rs` already unwraps. Bryan's library has only one comment that starts with `<` today (this one), so the collision is future-tense, but he does read papers with p-values.
2. **"The previous one" is underspecified.** Previous sidecar annotation? Previous *highlight*? Previous rendered block after skipping marker mirrors? If a standalone note or image sits between two quotes, joining across it is a surprise.
3. **Identity is unstated, and the current renderer will get it wrong.** Block ids hash `(pdf, kind, page, ordinal_on_page, quote text)`. Comments are excluded, so adding `<` does not change the continuation's id. Merging at render time makes that id disappear from the generated region, and today's code tombstones every disappearance that is not a leaked marker/preamble. First merge of this screenshot would put `^h-434a5e5a2bc4` under `### Removed highlights`. That is the opposite of beautiful.
4. **Join rules are unstated.** Page 11 ends `On every` and page 12 starts `session startup`. Concatenate-then-beautify already produces the right space. A hyphenated page-break (`every-` / `session`) should use the existing `append_reflow_fragment` heal. Two independent paragraphs glued with a blank line would be the wrong default for this feature's purpose.
5. **Page headings are unstated.** Leaving the merged quote under `### Page 11` hides that it includes page 12. Emitting both `### Page 11` and `### Page 12` around one callout is worse. The honest heading is `### Page 11–12`.
6. **Annotation tasks are unstated.** `[h::]` is `sha256(version, note path, source_block_id, identity)`. If merge retargets `source_block_id` to the survivor for both the hash and the 🔖, every continuation task is recreated on first merge and again on unmerge.
7. **Where it runs is unstated.** Parse-time fusion would mint a new quote string and therefore a new `^h-`. Render-time grouping keeps both hashes and only changes what is drawn.

---

## 4. Justified requirement adjustments

These change the user's wording. They are deliberate.

| # | Original implication | Adjustment | Why |
| --- | --- | --- | --- |
| A1 | `bob ref` merges | Merge only while **rendering** the managed region. Never write the sidecar, the PDF, or a second copy of the quote. | Sidecar is Highlights-owned (`docs/highlights-ref-sync.md`). Unmerge is "delete the `<` and scan." |
| A2 | Note "starts with `<`" | First line of the highlight comment, after `Comment:` / `Note:` / list-marker stripping, matches `^<\s*$` **or** `^<\s+\S` whose remainder does **not** start with a digit or `=<>`. | Keeps `< PR Merge Master?!` and bare `<`. Rejects `< 0.05`, `<=`, `<<`, `<~/tmp/foo.png>`. |
| A3 | "The previous one" | Immediately previous **rendered highlight** in sidecar order. Marker mirrors are skipped (they already are). Images and standalone notes are **not** skipped: if the previous visible block is one of those, the `<` does not fire and stays visible. | Predictable. No joining across a figure. |
| A4 | One previous | Chains. Each `<` extends the open group. Three page-break fragments need `<` on the second *and* the third. | Matches how you highlight overflow: mark every continuation, never the start. |
| A5 | "Merge a highlight and its notes" | Join member quotes through `beautify_annotation_text` (newline concat, then the existing reflow/hyphen heal). Join comments as paragraphs, with the continuation prefix stripped. Image-note lines on any member attach to the survivor callout. | One quote, one comment, one screenshot slot. |
| A6 | Unspecified identity | Survivor `^h-` is the **first** member's current id. Absorbed ids are silently dropped (same class as leaked marker/preamble), never tombstoned. Unmerge recreates the continuation block under its original id. | Comments are not in the hash, so the continuation id is stable across merge/unmerge. |
| A7 | Unspecified tasks | `[h::]` keeps hashing against each annotation's **own** original `^h-`. The 🔖 link jumps to the **survivor**. | Follow-ups do not duplicate. Clicking the bookmark lands on the visible quote. |
| A8 | Unspecified headings | If the group spans two or more labels that all match `Page N` / `p. N`, emit `### Page {first}–{last}` with an en-dash. Same-page groups keep `### Page N`. Non-numeric labels keep the first heading. | Honest, quiet, already accepted by `region_page_heading` (any `###` except `Removed highlights`). |
| A9 | Prefix remains in the vault | Strip `<` from the **rendered** comment. Leave it in Highlights. | The PDF sidebar still shows the join mark. The ref note shows `Comment PR Merge Master?!`. |
| A10 | Implied magic around page breaks | **No** auto-merge without `<`. | This note's nested short/long highlights would false-positive. |
| A11 | `bob ref` the command | No new subcommand, flag, or config key. Document under the generated-body contract. Dry-run prints `merged: N`. | CLI rules: nest under a noun with a membership rule; this is render behavior of `scan`/`sync`. |
| A12 | Always merge when prefix present | If there is no eligible previous highlight, **keep** the `<` in the rendered comment and do not fail the PDF. Optional doctor warning `continuation_without_target`. | A leading `<` on the first highlight of a note is a visible no-op, not data loss. |
| A13 | "Highlight note" | Trigger only on `SidecarAnnotationKind::Highlight` comments. Standalone notes and image-selection captions do not merge. | Sticky notes are not overflow quotes. |
| A14 | Unspecified counts | `highlights_count` is the number of **rendered** blocks after grouping. | Frontmatter already stores `rendered.count`. One merged thought is one highlight. |

---

## 5. Recommended solution

### 5.1 Gesture

In Highlights, on the **continuation** highlight (the overflow page, or the later span in the same paragraph):

| Typed in the highlight note | Meaning |
| --- | --- |
| `<` | Join this quote to the previous highlight. No extra comment. |
| `< PR Merge Master?!` | Join, and the merged comment is `PR Merge Master?!`. |
| `<` then a screenshot path on the next line | Join, and attach the image note to the survivor. |
| `<` then `- #task …` | Join, and import the task against the continuation's original id, 🔖 to the survivor. |

Authoring rhythm for a sentence that falls off page 11: highlight page 11 as usual; highlight the page 12 overflow; type `<` (and any thought) on the second note. Do not go back and mark the first highlight.

### 5.2 Matcher

Operate on the comment *after* the same stripping image notes already do (`Comment:` / `Note:`, one unordered-list marker), then look at the first non-empty line:

```text
bare       :=  ^<\s*$
with-note  :=  ^<\s+(\S.*)$   and remainder[0] ∉ {0-9, '=', '<', '>'}
```

Examples:

| Comment | Merge? | Remainder |
| --- | --- | --- |
| `< PR Merge Master?!` | yes | `PR Merge Master?!` |
| `<` | yes | (empty) |
| `- < keep going` | yes | `keep going` |
| `Comment: < keep going` | yes | `keep going` |
| `< 0.05` | no | — |
| `<= 5` | no | — |
| `<< back` | no | — |
| `<~/tmp/screenshots/x.png>` | no | — |
| `…so the crew are just` | no | — (already in this note) |

ASCII `<` (U+003C) only. `←`, `‹`, `＜` stay ordinary text.

### 5.3 Grouping

Walk `sidecar.annotations` in order, skipping `is_sidecar_marker_mirror` as today.

```text
open := none
for each rendered annotation A:
  if A is Highlight and continuation(A) and open is a Highlight group:
    append A to open
  else:
    flush open
    open := new group starting at A
flush open
```

A group of one renders exactly as today. A group of N>1 renders as one callout.

### 5.4 Quote join

For each member, optionally `strip_return_link_glyphs` (same `return_links:` flag as today), then join the raw texts with `\n` and run `beautify_annotation_text` **once** on the combined string.

That reuses the proven heal:

- `through-` + `put` → `throughput`
- `Marie-` + `Curie` → `Marie-Curie`
- `On every` + `session startup` → `On every session startup`

Do not insert a paragraph break at the member boundary. This feature's job is "this is one sentence / one paragraph I could not select in one gesture." If Bryan wanted two paragraphs he would leave them unmerged.

### 5.5 Comment join

Survivor comment = first member's comment (unchanged) plus each continuation remainder, separated by a blank line when both sides are non-empty. Then the existing image-note split and `[!note] Comment` callout.

The screenshot has no comment on page 11, so the merged comment is just `PR Merge Master?!`.

### 5.6 Identity and tombstones

- `annotation_block_id` is unchanged. First member keeps `^h-06d27eae3c84`. Continuation keeps hashing to `^h-434a5e5a2bc4` even while merged.
- Emit **one** `^h-` line: the survivor.
- Put absorbed ids in the silent-drop set (extend `silently_dropped_block_ids` / the `removed_ids` filter in `render_sidecar_highlights`). They must not appear under `### Removed highlights`.
- `block_ids_by_annotation_order` maps **every** member order to the survivor id, so image-task lookup and 🔖 retarget share one table.
- Unmerge (delete `<`, scan): continuation reappears with `^h-434a5e5a2bc4`. No tombstone, no new id.

Obsidian cannot alias two `^id` lines onto one callout cleanly. Do not emit a dummy paragraph for the absorbed id. The 🔖 retarget is the jump; inbound links to an absorbed id during the merged window are accepted as stale (they revive on unmerge). In practice the `<` is typed in the same breath as the continuation highlight, before anything has linked to it.

### 5.7 Annotation tasks

Today highlight tasks ignore the render map and hash + link against `annotation_block_id`. Split those two jobs:

| Field | Value |
| --- | --- |
| `[h::]` / `processed_id` | `sha256(version, note, **original** ^h-, identity)` — **do not bump** `HIGHLIGHT_TASK_ID_VERSION` |
| 🔖 `[[#^…]]` | survivor id from `block_ids_by_annotation_order` |

A `#task` on the page-12 comment keeps its processed id across merge/unmerge and always jumps to the visible quote.

Strip the merge prefix from `task_source` before parsing bullets, so `- < #task …` is still a task and does not keep `<` in the task text.

### 5.8 Page headings

| Members | Heading |
| --- | --- |
| all `Page 11` | `### Page 11` |
| `Page 11` then `Page 12` | `### Page 11–12` |
| `Page 11`, `Page 12`, `Page 13` | `### Page 11–13` |
| mixed / non-numeric | first member's label |

Use U+2013 (`–`), no spaces. After a `Page 11–12` group, a later unmerged page-12 highlight still opens `### Page 12`. Slightly redundant, honest.

`region.rs` already treats any `###` other than `Removed highlights` as a page label, so `bob ref show` and the annotation snapshot pick this up with no parser change.

### 5.9 Counts, dry-run, doctor

- `highlights_count` / `rendered.count` = groups, not raw sidecar rows. The gas-town note goes 16 → 15.
- Verbose / human scan report grows `merged: N` next to `images:` (`N` = absorbed members, so this screenshot prints `merged: 1`).
- `bob ref doctor`: warning-level `continuation_without_target` with the PDF path. Never a hard fail.

### 5.10 Where the code goes

All of this is `src/native/highlights_ref/`:

| Piece | Home |
| --- | --- |
| Matcher + grouping | new `continuation.rs` (small, unit-tested), called from `render_sidecar_highlights` |
| Silent-drop of absorbed ids | `sidecar_render.rs` next to `silently_dropped_block_ids` |
| 🔖 vs `[h::]` | `annotation_tasks.rs` (`AnnotationTaskCandidate` gains `link_block_id` or equivalent) |
| Docs | `docs/highlights-ref-sync.md` → Generated body contract, new **Continuation highlights** subsection |
| Tests | `src/native/highlights_ref/tests/sidecar.rs` plus one CLI scan fixture that is this sidecar fragment |

No bob-plugins work. No Mac Capture work. Annotation sync remains the Mac full scan; the `<` travels in the sidecar that scan already reads.

---

## 6. Worked example (the screenshot)

Sidecar, linked-page shape, already on disk at `~/bob/lib/blogs/gas_town_emergency_user_manual.md`:

```md
#### [Page 11](highlights://gas_town_emergency_user_manual#page=11)

##### 2026-10-19:

> One last Crew tip: I have a new ad-hoc role that I've been using
> for the past week, called the "PR Sheriff.One of my B
eads crew
> has a permanent hook: b
d-4f43s: PR Sheriff Standing Orders. On
> every

***

#### [Page 12](highlights://gas_town_emergency_user_manual#page=12)

##### 2026-10-19:

> session startup, the sheriff checks open PRs and divides them
> into easy wins and those needing human review, then slings the
> easy wins to other crew for merging and cleanup

< PR Merge Master?!
```

After this feature, the managed region for those two chunks is one callout under `### Page 11–12`, comment `PR Merge Master?!`, block id `^h-06d27eae3c84`. PDF extraction scars (`Sheriff.One`, `B eads`, `b d-4f43s`) stay; they are a Highlights/PDF-text problem, not a merge problem. Beautify still turns `On every` + `session startup` into one sentence.

---

## 7. Alternatives and why they lose

| Alternative | Why not |
| --- | --- |
| Auto-merge when the previous quote has no terminal punctuation and the next page starts lowercase | This note's nested highlights (page 4 short + long, page 7 short + long) would join. Opt-out would need another marker, which is the original feature with extra sadness. |
| `<<`, `^merge`, `+`, `…` | Bryan already wrote `<`. `…` is in use on page 9 (`…so the crew are just`). `>` is a blockquote in the sidecar. `+` is a list marker. |
| `<` on the *first* highlight meaning "the next one continues me" | You would have to remember before seeing the overflow. The natural moment is the second selection. |
| Mutate the sidecar into one blockquote | Fights Highlights autosave; next app write splits it again. Violates "Bob never creates or mutates sidecars." |
| Merge in Obsidian after the fact | Two-place workflow. The whole point is a one-character mark while the PDF is in front of you. |
| Ask Highlights for multi-page selection | PDF cannot represent it as one annotation. Even a perfect app UI would still export two quads. |
| Rely on Highlights "Smart Merge Annotations" | Same-page overlapping markups at best; cannot be one PDF annot across pages 11 and 12. The screenshot is already two notes. |
| Keep both `^h-` lines on the merged callout | Obsidian binds a block id to the preceding paragraph. A second `^h-` becomes its own tiny block, not an alias. |
| Parse-time fusion into one `SidecarAnnotation` | Combined text changes the hash; both old ids tombstone; tasks churn. |
| Color-coded "continuation" highlights | Eats a color category, invisible in the comment, worse in the Highlights sidebar than `<`. |

---

## 8. Edge cases the implementation must pin

1. **First highlight of the PDF carries `<`.** No merge. Prefix stays. Doctor warning.
2. **Previous visible block is an image or standalone note.** No merge. Prefix stays.
3. **Marker mirror between two highlights.** Mirrors are already skipped; the previous *rendered* highlight is still eligible.
4. **Chain of three.** `<` on #2 and #3. One group, survivor is #1, heading `Page 11–13` if labels are numeric.
5. **Same-page two-point paragraph.** Two highlights under `Page 9`, second starts with `<`. One callout, heading stays `### Page 9`. Omitted middle of the paragraph stays omitted.
6. **Unmerge.** Delete `<` in Highlights, next scan restores two callouts and the original continuation id. Any `[h::]` created while merged still matches.
7. **Edit the continuation quote while merged.** Its latent id changes (existing text-edit behavior). Still no tombstone while absorbed. After unmerge the new id appears; the old continuation id tombstones. Same as editing an unmerged highlight today.
8. **Edit the first quote while merged.** Survivor id changes (existing behavior); the old first id tombstones; continuation remains absorbed under the new survivor.
9. **Both members have comments.** Two paragraphs in one Comment callout.
10. **Continuation is only `<` plus an image-note path.** Survivor gains the image, no Comment callout unless other text remains.
11. **`#task` on both members.** Two tasks, two `[h::]`, both 🔖 to survivor.
12. **Return-link PDFs.** Strip glyphs per member, then join, then beautify. A trailing `↩ p. 12ᵈ` on the page-11 fragment must not glue onto `session`.

---

## 9. Tests that would prove it

Minimum set, all in `tests/sidecar.rs` / CLI highlights, using the linked-page sidecar shape (that is what Highlights actually writes for this library):

1. Screenshot fixture: pages 11–12, comment `< PR Merge Master?!` → one callout, heading `Page 11–12`, comment without `<`, id of page 11, no `Removed highlights`.
2. Bare `<`.
3. Same-page pair.
4. Three-member chain.
5. `<` on the first highlight: two blocks, prefix kept.
6. Image between two highlights, second has `<`: no merge.
7. `< 0.05` and `<~/tmp/x.png>`: no merge.
8. Hyphen across the join (`every-` / `session`).
9. Absorbed id was present in the previous generated region: still no tombstone.
10. Unmerge restores the continuation id.
11. Task on the continuation: 🔖 = survivor, `[h::]` unchanged if the same test runs merged then unmerged.
12. `merged: 1` on dry-run.

---

## 10. What this is not

- A fix for Highlights' PDF text extraction (`Sheriff.One`, `B eads`, `jusone`, `nowatching` on this same note). Merge will not heal those.
- A garbage collector for the five existing tombstones on this note.
- A new `bob ref merge` verb.
- Auto-join of adjacent quotes.

Those can be later beads. This feature is the `<` grouping pass.

---

## 11. Recommended solution (the one sentence)

Add a render-time continuation pass to `bob ref` highlight rendering: a highlight comment whose first token is `<` (bare, or `<` + whitespace + non-comparison text) is joined to the immediately previous rendered highlight; quotes reflow through the existing beautify healer; the first highlight keeps the `^h-`; absorbed ids never tombstone; the prefix is stripped in the vault and left alone in Highlights.

Implement that, with the table in §4 as the contract, and the screenshot's page 11–12 pair as the first golden fixture.
