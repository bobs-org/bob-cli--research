# Nested underline emphasis in ref notes

- **Researcher:** grk
- **Date:** 2026-10-19
- **Question:** Underlines in the Highlights app are extra emphasis on part of a larger highlight, but ref notes and the Bob Mac Capture ref-panel preview render them as separate, bold highlights. How should we merge them when possible so the result is intuitive, reliable, and beautiful?
- **Verdict:** Yes, merge them — automatically, at render time, in `bob ref`. Detect Highlights' underline export (`**…**`-wrapped quotes), nest each one into the unique same-page highlight that already contains its text, and draw a single `**span**` inside one `[!quote]`. Do not wait for Highlights, do not ask for a `<` marker, and do not put this logic in the Mac app.

---

## 1. In one breath

Highlights stores an underline as its own PDF annotation. Its documented markdown mapping is:

| PDF markup | Sidecar quote |
| --- | --- |
| Highlight | plain `> quote` |
| Underline | `> **quote**` (bold) |
| Strikethrough | `> ~~quote~~` |

`bob ref` already treats every sidecar quote as a separate `[!quote]` callout. The Mac inspector already paints balanced `**…**` as strong emphasis (`RefsQuoteEmphasis`). So an underline of a phrase inside a highlight becomes a second, fully-bold card sitting next to the real highlight.

That is the wrong reading of Bryan's gesture. The underline is not a second thought. It is extra weight on a span the highlight already captured.

The karpathy wiki note is the whole product:

```md
> [!quote] index.md is content-oriented. … When answering a query, the LLM reads the index first to find relevant pagesthen drills into them. This works surprisingly well at moderate scale (~100 sources, ~hundreds of pages) and avoids the need for embeddingbased RAG infrastructure

^h-1746e66b6f4f

> [!quote] **This works surprisingly well at moderate scale (~100 sources,** **~hundreds of pages) and avoids the need for embeddingbased RAG** **infrastructure**

^h-b4022493a6a2
```

The reading note should be one thought, with one span leaning forward:

```md
> [!quote]
> index.md is content-oriented. It's a catalog of everything in the wiki — each page listed with a link, a one-line summary, and optionally metadata like date or source count. Organized by category (entitiesconcepts, sources, etc.). The LLM updates it on every ingest. When answering a query, the LLM reads the index first to find relevant pagesthen drills into them. **This works surprisingly well at moderate scale (~100 sources, ~hundreds of pages) and avoids the need for embeddingbased RAG infrastructure**

^h-1746e66b6f4f
```

That is a good idea. The work is a containment pass next to the existing `<` continuation pass, plus one visual correction so the nested span can actually be seen in Obsidian.

---

## 2. What is actually happening

### 2.1 Highlights' contract, not a bob bug

Official extraction rules ([How to Extract PDF Annotations](https://highlightsapp.net/how-to/iphone/extract-pdf-annotations/)):

- Highlighted text → quote
- Underlined text → **bold quote**
- Strikethrough text → strikethrough quote

MacUpdater's app description says the same: "Highlighted, underlined and strikethrough text become quotes with normal, bold and strikethrough emphasis."

CommonMark has no underline. Highlights chose `**` as the portable stand-in. That choice is why the Mac inspector already has a `**`-only emphasis parser, and why Bryan sees "bold highlights" rather than underlined ones.

Each markup is still a separate PDF annotation (`/Highlight` vs `/Underline` vs `/StrikeOut`). The sidecar is 1:1 with those annotations. bob's parser never sees annotation subtype, color, or quads — only the markdown Highlights wrote.

### 2.2 Hard-wrap makes the bold look worse

Highlights wraps **each wrapped line** of an underline independently. From `lib/blogs/karpathy_llm_wiki.md`:

```md
> **This works surprisingly well at moderate scale
(~100 sources,**
> **~hundreds of pages) and avoids the need for embedding-
based RAG**
> **infrastructure**
```

`beautify_annotation_text` then reflows those lines, so the generated callout is three adjacent strong runs, not one:

```md
> [!quote] **This works surprisingly well at moderate scale (~100 sources,** **~hundreds of pages) and avoids the need for embeddingbased RAG** **infrastructure**
```

The Mac inspector paints every run as strong, so the whole card is bold. Obsidian paints the whole string as the callout *title* (already semibold) **and** as `**strong**`. Double weight, no contrast, a second card. Ugly on both surfaces, for different reasons.

### 2.3 The vault already proves containment

A pass over `~/bob/ref` on 2026-10-19:

| | Count |
| --- | ---: |
| Live `[!quote]` blocks | 351 |
| Fully-`**`-wrapped quotes (underline exports) | 19 |
| Same-page parent highlight that contains the inner text | **19 / 19** |
| Those underlines that carry a comment | 8 |
| Parent appears *after* the underline in sidecar order | majority |
| Parent appears *before* the underline | the rest |
| Unmergeable leftovers | **0** |

Every current underline is extra emphasis inside a larger same-page highlight. Comments live on the underline more often than on the parent (`aligned with what a team is actually doing`, `who changed them, when, and why`, gastown wisps `#task`, Gas Town page 7 and 10). Sidecar order is not "underline follows parent": Highlights often emits the underline first.

So:

- Auto-merge is safe on today's library.
- "Previous highlight" (the `<` continuation rule) is the wrong lookup.
- Comments must travel with the span onto the parent card.

### 2.4 The two surfaces already disagree in a useful way

| Surface | How a quote is drawn | How `**` reads |
| --- | --- | --- |
| Obsidian ref note | Entire quote is the `[!quote]` **title** (semibold) | Nested strong is almost invisible |
| Mac inspector HIGHLIGHTS | Regular-weight callout + yellow rule (`highlightView`) | Nested strong pops |
| Mac inspector YOUR NOTES | Italic secondary quote + yellow rule (`noteView`) | Nested strong still pops, quieter |

The Mac panel will show the nested span as soon as `bob ref show` returns one quote with an inner `**span**`. Obsidian will not, unless the quote moves out of the callout title and into the body.

---

## 3. Is this a good idea?

**Yes.** Three properties make it the right layer:

1. **The gesture already happened in the PDF.** Bryan underlined a span he had also highlighted. Asking him to type `<` on the underline, or to stop underlining, fights the tool he is already using. Continuation merge needs `<` because two plain highlights are ambiguous. A fully-`**`-wrapped quote is not ambiguous — Highlights has labeled its type.
2. **bob already owns the reading surface.** Sidecar parse → continuation grouping → callout render → `^h-` identity → `bob ref show` JSON → Mac inspector. Comments are not in the block-id hash. The Mac app is a thin client of that JSON (`decisions:mac-capture-is-a-thin-client` for capture; the inspector already only *paints* `**`, it does not decide meaning).
3. **Containment is checkable.** 19/19 current underlines are unique substrings of a same-page unwrapped highlight, after stripping `**` and allowing a truncated last token (`didn'` vs `didn't.`). That is a boring, testable rule.

What would make it a bad idea:

- silently joining every adjacent pair of highlights (continuation research already rejected this; nested short-plus-long highlights on Gas Town pages 4–7 are the counterexample);
- rewriting the sidecar or the PDF (Highlights owns both; bob's contract is "never create or mutate sidecars");
- merging only in Swift (Obsidian stays ugly; an older bob would disagree with the panel);
- tombstoning absorbed underlines as `[!warning] Removed highlight` (the first scan after ship would fill `### Removed highlights` with eighteen false deaths);
- nesting `**` into callout titles and calling it done (Obsidian still shows two weights of the same bold).

---

## 4. Critique of the plan as stated

The plan: *underlines are extra emphasis on part of a larger highlight; merge them in a visually appealing way when possible; lead the design so it is intuitive, reliable, and beautiful.*

### What is right

- **Merge when possible, keep a leftover when not.** That is the right fallback. Today's leftover set is empty; the rule still needs one.
- **Both surfaces.** The inspector reads `bob ref show`. If bob merges, both surfaces move together. If only the Mac merges, the vault lies.
- **Beauty is a requirement, not polish.** A second fully-bold card is not "good enough until CSS."

### What is incomplete or unsafe

1. **"Merge" is underspecified.** Concatenating two callouts, nesting a second `[!quote]`, or emitting `<u>` would all "merge." Only one of those is beautiful.
2. **"When possible" needs a predicate.** Possible = unique same-page containment of a fully-strong quote inside a not-fully-strong quote. Not: previous annotation, overlapping geometry, or a `<` marker.
3. **Sidecar order will fool a "previous" rule.** Most underlines currently *precede* their parent. Continuation's previous-highlight walk would miss them or glue them to the wrong neighbor.
4. **Comments sit on the underline.** Absorbing the span and dropping the comment would lose the thought. `gastown_readme`'s `#task` and the goals-paper notes are on the bold card today.
5. **Obsidian title-vs-body is unnamed.** Today's renderer puts the quote on the `[!quote]` title line (`push_callout_block`). Nested `**` there cannot read as extra emphasis. The inspector does not have this problem.
6. **Identity is unstated.** Block ids hash `(pdf, kind, page, ordinal, quote text)`. Comments are excluded. Absorbing the underline makes its `^h-` disappear; today's renderer tombstones every disappearance that is not a leaked marker/preamble. First merge of the karpathy note would put `^h-b4022493a6a2` under `### Removed highlights`.
7. **Fragmented `**a** **b** **c**` is unnamed.** Even a perfect nest still looks broken if we keep Highlights' per-line wrappers. Heal to one span.
8. **Highlights will not save us.** "Smart Merge Annotations" is a free-tier bullet with no public spec. It does not nest an `/Underline` into a `/Highlight` in today's sidecars — those 19 pairs exist. "Underline Power Tools" are citation lookup and file tags by color, which is a different gesture. Note Format → "Text and Border" would paint highlight color into the export; Bryan's sidecars are the default (plain highlight, bold underline).
9. **The Mac app must not grow a second merger.** It already splits `**` for paint. Give it one quote with one span.

---

## 5. Alternatives considered

| Approach | Why it loses |
| --- | --- |
| Ask Highlights to nest types in the sidecar | Closed app, not scriptable ([FAQ](https://highlightsapp.net/faq/)). Even a perfect export would still be two PDF annotations. |
| Smart Merge in Highlights | Adjacent same-type glue, not type nesting. Today's library still has 19 separate underline quotes. |
| Type `<` on every underline | Wrong gesture. Continuation `<` is for overflow the PDF cannot store. This span *is* stored. |
| Merge only in Bob Mac Capture | Vault and Obsidian stay wrong. Violates "bob is the compiler." |
| PDF quad geometry | Accurate, expensive, and unused: bob does not parse highlight quads today, and 19/19 pairs already match on text. Reopen if text match starts failing. |
| Nested `<u>` / `<ins>` | Looks like a link. Capture does not parse HTML. Markdown's authors omitted underline for this reason. |
| Nested `==mark==` | A second highlighter wash inside a quote callout. Capture does not parse it. |
| Nested italic | Weaker, and YOUR NOTES quotes are already italic. |
| Custom callout type (`[!emphasis]`) | Extra chrome. The outer quote *is* the highlight; the inner span should stay typographic. |
| CSS snippet only | Cannot collapse two callouts into one. Optional later for painting `strong` inside `[!quote]` with a hairline underline. |

The winner is the same shape as continuation merge: a **stateless render-time grouping pass** in `bob ref scan` / `sync`. Continuation is opt-in (`<`) because the inputs are two plain highlights. Emphasis merge is automatic because the input is already typed.

---

## 6. Justified requirement adjustments

These change the user's wording. They are deliberate.

| # | Original implication | Adjustment | Why |
| --- | --- | --- | --- |
| A1 | Merge "somehow" in notes and the preview | Merge only while **rendering** the managed region. Never write the sidecar or the PDF. | Same contract as continuation. Unmerge is "delete the underline in Highlights and scan." |
| A2 | "When possible" | Possible = the quote is *fully strong* (every non-whitespace character sits inside `**` runs) **and** its inner text is a unique containment in one same-page, not-fully-strong highlight. | `**` is Highlights' underline label. Unique containment is the reliability gate. |
| A3 | Implied "previous" / adjacent card | Search **the whole page**, both directions. Prefer the shortest containing parent; if still tied, the sidecar-nearest. If still tied, do not merge. | Underlines often render *before* the parent. |
| A4 | Keep `**foo** **bar** **baz**` | Heal a fully-strong quote to **one** `**inner**` span before matching and before drawing. | Highlights' per-line wrap is an export artifact, not emphasis structure. |
| A5 | Nested emphasis as true underline | Draw nested emphasis as `**strong**`, not `<u>`. | Portable, already painted in the inspector, already rendered in Obsidian, not link-shaped. |
| A6 | Leave `[!quote]` title layout alone | Put highlight quote text on the **callout body**, with an empty title: `> [!quote]\n> …`. | Titles are already semibold; nested strong cannot pop there. Image callouts keep the `Image` title. |
| A7 | Unspecified comments | Comments, image-notes, and `#task` lines on the underline attach to the parent callout. Parent comment first, then absorbed comments in sidecar order, as paragraphs of one `[!note] Comment`. | 8/19 underlines carry the thought. |
| A8 | Unspecified identity | Survivor `^h-` is the **parent's** current id. Absorbed underline ids follow the continuation rule: never `[!warning]` tombstones; previously published ids get `[!info] Merged highlight` redirect stubs. | First scan must not look like data loss. |
| A9 | Unspecified tasks | `[h::]` keeps hashing against each annotation's **own** original `^h-`. The 🔖 link jumps to the **parent**. | Same as continuation. Follow-ups do not duplicate. |
| A10 | Mac preview as a second implementation | No Swift merge. Inspector and Copy card consume the merged `bob ref show` quote. Optional later: also underline strong runs in `quoteText` — not required for v1. | Thin client. `RefsQuoteEmphasis` already does the paint. |
| A11 | Underlines only | The same pass may nest fully-`~~`-wrapped quotes as `~~span~~` (strikethrough). | Identical machinery. Bryan did not ask; ship it if the detector is shared, or leave a hook. Call it follow-up if it grows tests. |
| A12 | Implied new command | No new subcommand, flag, or config key. Document next to continuation under the generated-body contract. Dry-run prints `emphasis_nested: N`. | CLI rules: this is render behavior of `scan`/`sync`. |
| A13 | Always merge a bold quote | If no unique parent exists, keep a **single** `**inner**` callout (healed, not fragmented). Do not fail the PDF. | Honest leftover. Today's N is 0. |
| A14 | Equal-length highlight+underline of the same span | Treat as containment (`inner` length ≤ parent). Drop the duplicate card and wrap the whole parent. | "I marked it twice" still wants one card. |
| A15 | Unspecified order vs `<` | Run **after** continuation grouping. An underline may nest into a group quote when its page is one of the group's pages. Fully-strong quotes are not continuation heads. | Page-break sentence first, then inner emphasis. |
| A16 | Unspecified counts | `highlights_count` is rendered blocks after both grouping passes. | Karpathy goes 2 → 1. |

A6 is the largest visual change. It affects every highlight, not only merged ones. It is still justified: without it, the feature is beautiful in the inspector and muddy in Obsidian, which is where Bryan reads the notes. Body quotes also make ordinary highlights quieter, so the nested span is the only heavy type on the card.

---

## 7. Recommended solution

### 7.1 Layer

A second grouping plan beside `plan_continuations` in `src/native/highlights_ref/`:

1. Parse sidecar (unchanged).
2. `plan_continuations` (unchanged).
3. **`plan_emphasis_nests`** (new): walk remaining text highlights plus assembled continuation groups.
4. Render groups; skip absorbed underline orders the same way continuation skips followers.
5. `block_ids_by_annotation_order` maps underline orders to the parent id, so 🔖 and `ref show` agree.

Stateless. Deleting the underline in Highlights and scanning restores two cards under the original ids.

### 7.2 Detector

A text highlight is an **emphasis child** when, after `beautify_annotation_text` (and return-link stripping when that flag is on):

1. `RefsQuoteEmphasis`-style pairing of `**` finds at least one run.
2. Every non-whitespace character of the quote sits inside those runs.
3. The inner text (runs joined with the whitespace that sat between them, `**` discarded) is non-empty.

Do not treat partial `**` inside a longer plain quote as a child — that is already nested emphasis, or literal stars. Do not treat `==…==` or HTML color spans as underlines (Note Format → Text and Border, which Bryan is not using).

### 7.3 Parent match

Normalize for matching only (do not write the normalized form):

- Unicode NFC, collapse whitespace, keep curly quotes.
- Strip hyphens inside tokens for a second attempt (`sub-goals` / `subgoals`, `embedding-based` / `embeddingbased`).

A candidate parent is a same-page text highlight that is **not** an emphasis child (a continuation group's assembled quote counts as one parent, visible to children whose `page_label` is in the group).

Containment:

1. Exact substring of normalized inner in normalized parent.
2. Else: inner with its last token dropped, if at least two tokens remain.
3. Else: last token of inner is a prefix of the corresponding parent token (the `didn'` / `didn't.` case).

If several parents match, keep the shortest. If still tied, keep the sidecar-nearest. If still tied, leave the child standalone.

Do **not** nest a child into another child. Do **not** nest a plain highlight into a fully-strong quote (Bryan's stated usage is underline-inside-highlight, not the inverse). Do **not** cross pages except via a continuation group that already owns both.

### 7.4 Draw

On the parent quote, wrap the matched span in a single `**…**`. If the parent already has `**` on that span, do not double-wrap.

Callout shape for every text highlight, merged or not:

```md
### Page 4

> [!quote]
> prefix **emphasized span** suffix
>
> > [!note] Comment
> > The thought that used to live on the underline.

^h-parent
```

Empty title, body at regular weight, one strong span, one nested comment. The `### Page N` heading above the card already names the page; the callout does not need a title.

Healed leftover (no parent):

```md
> [!quote]
> **standalone underlined phrase**

^h-child
```

Redirect stub for a previously published child id, reused from continuation:

```md
> [!info] Merged highlight
> Now part of [[#^h-parent|the Page 4 highlight]].

^h-child
```

### 7.5 Beauty rules (the actual look)

- **One card.** The outer quote wash *is* the highlighter. Do not add a second callout, a nested `[!quote]`, a label, or a color chip.
- **One span.** Inner `**` is extra weight, not extra chrome. Heal Highlights' per-line wrappers.
- **Quiet context.** Body text at regular weight so the span can be heavier than its surroundings. This is why A6 exists.
- **Comment under the whole quote.** Markdown cannot pin a note to a span without HTML. The inspector already shows YOUR NOTES first; after merge, a commented underline *promotes* the parent into YOUR NOTES, so the thought arrives with its sentence. That is the correct promotion.
- **Yellow rule stays one.** The inspector's 3 pt yellow bar already means "this is a highlight." Nested strong is enough. Do not add a second bar under the span in v1.
- **Optional later CSS** (vault snippet, not bob): `strong` inside `.callout[data-callout="quote"]` may add a 1 px underline in the callout color, if Bryan still misses the PDF's line. Do not block v1 on it.

Worked example, goals paper page 4:

Before: six cards, three of them fully bold, two comments stranded on the short ones.

After:

```md
> [!quote]
> AI should play a substantive collaborative role: interrogating whether a goal is coherent, feasible, and **aligned with what a team is actually doing**, not just polishing phrasing
>
> > [!note] Comment
> > This is the point of having every agent which has no preset goal run `sase goal list` before `sase goal set`!

^h-10017bc967f8
```

That is the PDF gesture, in a note.

### 7.6 Inspector and Copy

No Mac code required for v1.

- `bob ref show` returns one annotation: longer `quote`, comment present if either member had one, parent's `block_id` and `link`.
- `RefsQuoteEmphasis` already paints the inner span.
- YOUR NOTES vs HIGHLIGHTS follows the existing comment rule, so a comment-on-underline parent lands in YOUR NOTES with context. That is an upgrade.
- Copy / H picker lose the short standalone underline row. Acceptable: the copied quote is the sentence the underline was about. A later "Copy emphasized span" alternate is follow-up, not v1.
- Hover tooltip already shows the full quote (` .help(quote)`).

### 7.7 Tests to pin

Minimum set, next to `tests/cli/highlights/continuations.rs`:

- Karpathy suffix span, underline *after* parent in sidecar, fragmented per-line `**`.
- Gas Town page 4: underline *before* parent, prefix span.
- `**beads epics**` short interior span.
- Comment and `#task` on the child, none on the parent.
- Comments on both: parent paragraph then child paragraph.
- Truncation `didn'` ⊂ `didn't.`
- Unique-occurrence miss: same inner on two parents → no merge.
- Continuation group on pages 11–12, underline on page 12 nested into the assembled quote.
- First merge of a previously published child id → info stub, not warning tombstone.
- Unmerge (child removed from sidecar) restores the parent without `**` and does not resurrect the stub.
- `highlights_count` drops by the number of absorbed children.
- Region parser still reads empty-title `[!quote]` body as `quote`.
- `bob ref show -f json` quote contains a single `**span**`.

### 7.8 What not to do in v1

- New CLI, config, or frontmatter field.
- PDF annotation-subtype parsing (`/Underline`).
- Color-aware Power Tool tag exclusion (reopen if Bryan starts underlining tags with a dedicated color; those would look like short `**word**` quotes and could false-merge).
- Inverse nest (plain highlight inside a fully-strong underline).
- Mac-side merge, `<u>`, `==mark==`, or CSS as the merge mechanism.

---

## 8. Risks

| Risk | Mitigation |
| --- | --- |
| A6 restyles every highlight in Obsidian | Intended. Snapshot tests will move. Inspector is unchanged. |
| Short inner text matches the wrong parent | Unique containment + shortest parent. 2-word `beads epics` is unique on its page today. |
| Underline Power Tool tags | Not in current library. Reopen with a color/subtype detector if they appear. |
| Note Format "Text and Border" wraps highlights too | Detector requires *fully* strong, so a mixed highlight stays a parent. |
| First scan stub noise | Info stubs only for ids that already existed in the note, same as continuation. |
| Copy picker loses the short row | Document as a cost; the remaining row is the better copy. |

---

## 9. Recommended decision

Ship **automatic, render-time emphasis nesting in `bob ref`**, after continuation grouping:

1. Fully-`**`-wrapped quotes are underline children.
2. Nest each into the unique same-page parent that contains them.
3. Draw one `[!quote]` **body** with one healed `**span**`.
4. Move comments with the span.
5. Keep parent identity; redirect absorbed ids; leave the sidecar and PDF untouched.
6. Leave the Mac app as a painter of `**`.

Do this instead of a Highlights feature request, a `<` gesture, a Swift-only merge, or a true underline in Markdown.

It is the same philosophy as continuation merge, with the opposite trigger: continuation is opt-in because the inputs are indistinguishable; emphasis merge is automatic because Highlights has already labeled the child.
