# Merge Highlights Underlines Into Parent Highlights as Emphasis

Research report — bob-cli ref notes + bob-mac-capture ref panel preview.
Researcher: mus.

## TL;DR and recommended solution

**Yes, this is a good idea — with the scope tightened.** Bryan's gesture
(highlight the passage, underline the phrase inside it that matters) is
natural, and today's output betrays it: each underline becomes its own
`[!quote]` block, so a single thought reads as two or three disconnected
"highlights" and the emphasis information (that the underlined words live
*inside* the larger quote) is lost.

**Recommended solution: merge bare underlines into their parent highlight
at `bob ref` render time, by bolding the underlined span inside the
parent's `> [!quote]` block and absorbing the underline's block.** No
bob-mac-capture change, no Obsidian CSS, no new gesture, no new config
flag in v1. Both surfaces already render `**bold**` inside quotes
beautifully — Obsidian natively, and the Mac preview pane through its
existing `RefsQuoteEmphasis` strong-run renderer — so the merged note
looks right everywhere with zero client work. Anything that cannot be
merged safely stays exactly as it is today ("when possible" is a
correctness gate, not an aspiration).

Concretely, for a sidecar pair like:

```md
> The quick brown fox jumps over the lazy dog.

---

> **brown fox**
```

render one block in the ref note:

```md
> [!quote] The quick **brown fox** jumps over the lazy dog.

^h-<head-id-unchanged>
```

and absorb the underline's block (redirect stub only if that block was
already published, mirroring the continuation-merge pattern). The Mac
preview pane picks this up automatically because it reads the same
`bob ref show -f json` quote strings.

**Adjustments to the request I am making (all called out in §7):**

1. Merge is **automatic and always-on**, not a gesture, toggle, or
   per-note opt-in. Rationale: the underline gesture already happened in
   Highlights; asking Bryan to re-mark intent in bob would punish the
   exact workflow this feature exists to honor.
2. Merge **only bare, uniquely-matching, nearby underlines**. An
   underline with a comment, task, or image-note never merges (it keeps
   its own block). An underline matching zero or several places never
   merges. This is stricter than "merge somehow when possible."
3. **No mac-app or plugin work in v1.** The thin-client contract holds:
   fix the renderer once, both surfaces heal.
4. **No new emphasis style.** Merged emphasis is always `**bold**`
   inside the existing `[!quote]` callout — not `==mark==`, not `<u>`,
   not a new callout type. Both renderers already support exactly this.

**Phase 0 is mandatory and small:** capture 2–3 golden sidecars from the
real Highlights app (one canonical case, one multi-underline case, one
adversarial case) and confirm the "underlines export as bold blockquotes"
assumption before writing merge logic. Everything below is designed so
that if Phase 0 surprises us, only the classifier changes.

---

## 1. Problem restatement

Bryan's Highlights workflow:

1. Highlight a passage (the unit of thought).
2. Underline a phrase inside it (extra emphasis on the words that matter).

Desired: the ref note (and the Mac ref panel preview) should show **one**
quote with the key phrase emphasized.

Actual: the ref note shows **N** quote blocks — the big highlight plus
each underline as a separate, bold-looking highlight — and the Mac preview
pane shows the same split. The reader must mentally re-attach the
emphasis to its context, which defeats the purpose of underlining.

The split is structural, not cosmetic: each annotation is its own
`[!quote]` callout with its own `^h-…` block ID. No CSS tweak can re-join
them. The fix must happen where blocks are created.

---

## 2. What I verified in the code (source of truth)

All paths below are in the bob-cli checkout unless noted.

### 2.1 Highlights enter bob only through the sidecar

- `src/native/highlights_ref/sidecar.rs` — `parse_sidecar_markdown`
  splits the sidecar on page headings and horizontal rules; each chunk
  becomes one `SidecarAnnotation`. A chunk whose quote region starts
  with `>` is `SidecarAnnotationKind::Highlight`; a Markdown image line
  is `Image`; anything else is `StandaloneNote`. There are exactly three
  kinds (`src/native/highlights_ref/model.rs`): **there is no Underline
  kind today.**
- `src/native/highlights_ref/marker.rs` — PDF reading exists but only
  for the page-1 `/Text` marker note (`read_pdf_marker`). I found no
  `/Highlight` vs `/Underline` subtype reads, no `QuadPoints` geometry
  reads, anywhere under `src/native/highlights_ref/`. (The only
  "underline" hits in Rust are Setext-heading underlines and one Lua
  tree-walk comment.)
- Conclusion: **today, whatever distinction Highlights draws between a
  highlight and an underline must survive — if at all — as Markdown
  inside the sidecar.** If the sidecar encodes underlines
  indistinguishably from highlights, bob cannot classify them without
  new PDF-annotation reads.

### 2.2 Each highlight renders as its own callout block

- `src/native/highlights_ref/sidecar_render.rs` —
  `render_sidecar_highlights` renders each `Highlight` as
  `> [!quote] <beautified text>` plus an optional nested
  `> > [!note] Comment …`, followed by a stable `^h-…` block ID
  (`annotation_block_id`: SHA-256 over PDF path, kind, page label,
  page ordinal, and whitespace-normalized text).
- Continuation groups (`<` marker) are the one existing case where
  several sidecar annotations become one block, via
  `src/native/highlights_ref/continuation.rs` (`ContinuationPlan`:
  `head_of` / `followers` / seam logic) and
  `assemble_group_quote` + `render_highlight_group_block`. Absorbed
  followers that were already published leave a
  `> [!info] Merged highlight / Now part of [[#^h-…|…]]` redirect stub
  under `### Removed highlights`; never-published followers vanish
  silently. Head IDs are unchanged with or without followers.
- The generated-body contract, including callout shapes, tombstones,
  and the `<!-- highlights:begin/end -->` ownership region, is
  specified in `docs/highlights-ref-sync.md` ("Generated Body
  Contract", "Continuation highlights (`<`)").

### 2.3 The Mac preview pane needs no change

- bob-mac-capture is a thin client of bob by decision
  (`decisions:mac-capture-is-a-thin-client`): it runs bob, renders what
  bob returns, and submits drafts as `bob capture` calls. The ref
  inspector hydrates from the `bob ref show -f json` envelope
  (`Sources/RefsCore/RefsInspector.swift`: `RefsShowResponse` /
  `RefsShowAnnotation` with `quote` / `comment` / `block_id` split —
  quote and comment stay in separate fields per `docs/ref.md`
  §"`bob ref show`").
- `RefsQuoteEmphasis` (same file) already splits quote strings on
  paired `**` delimiters into plain/strong runs; the inspector view
  (`Sources/BobMacCapture/Refs/RefsInspectorView.swift`, `quoteText`)
  renders strong runs with `.stronglyEmphasized` inside the yellow-rule
  quote styling. Unpaired markers stay literal; single `*`, `_`, `__`,
  and backticks are never emphasis.
- Consequence: **any `**span**` bob puts inside a quote string renders
  emphasized in the preview pane today, with no app release.** The
  Obsidian side needs nothing either: `**bold**` inside a `> [!quote]`
  callout is plain CommonMark/GitHub-flavored Markdown and renders
  bold in Obsidian preview and reading view. This was inferred from the
  renderers' code and the Markdown standard, not from a screenshot —
  see §8 for the visual check to run.

### 2.4 What I did not verify (honest gaps)

- I did **not** run the Highlights macOS app and did **not** find a
  checked-in golden sidecar containing an underline. The repo's
  fixtures (`tests/fixtures/highlights_ref/linked_sidecar.md`) and the
  sidecar tests cover highlights, image selections, standalone notes,
  marker mirrors, and continuations — not underlines.
- So the claim "Highlights exports an underline as a fully- or
  partially-`**bold**` blockquote chunk" rests on (a) Bryan's own
  observation in the prompt ("show up as separate, bold highlights" —
  the bold must come from somewhere, and the sidecar is the only
  channel), and (b) the Mac renderer's pre-existing `**` emphasis
  support, which strongly suggests the pipeline has always carried bold
  spans. That is a good hypothesis, not a confirmed fact. **Phase 0
  exists to turn it into a fact.**

---

## 3. How underlines arrive today (working model, pending Phase 0)

Working model of the sidecar for "highlight + inner underline":

```md
#### [Page 4](highlights://book#page=4)

> The quick brown fox jumps over the lazy dog.

---

#### [Page 4](highlights://book#page=4)

> **brown fox**
```

Why separate blocks: the parser (correctly, given what it knows) treats
each `---`-delimited chunk as an independent annotation, and the
renderer gives each its own callout + block ID. The bold survives
because `normalize_annotation_text` / `beautify_annotation_text`
(`src/native/highlights_ref/text.rs`, `sidecar_render.rs`) preserve
inline Markdown while reflowing words — so the underline's `**` lands
verbatim inside its own `> [!quote] **brown fox**`.

Why this hurts:

- **Reader cost.** A 200-word quote followed by three two-word "quotes"
  reads as four thoughts, not one thought with three stressed phrases.
- **Copy cost.** The Copy card's quote picker (`RefsCopy.swift`) offers
  each fragment as its own quotable unit.
- **Link cost.** Each fragment mints a `^h-…` anchor others may link;
  merging later without stubs would break those links (hence §5.4).

---

## 4. Critique: is this a good idea? What would I do differently?

**Yes — auto-merge at render time is the right call — but the naive
version ("always glue nearby bold things together") would be a
reliability liability.** Specific judgments:

1. **The instinct to merge is right; the layer matters.** The split is
   created in `render_sidecar_highlights`, consumed identically by
   Obsidian notes, `bob ref show` (human/JSON/Markdown), annotation
   tasks (`annotation_tasks.rs` keys tasks to block IDs), and the Mac
   preview. Merging at the renderer fixes all consumers at once and
   keeps the thin-client contract intact. Merging anywhere else is
   strictly worse:
   - *Obsidian CSS or a bob-plugin post-processor* hides the split
     visually while leaving block IDs, copy payloads, and the Mac
     preview split — two truths, guaranteed drift.
   - *A Mac-app-only merge* fixes the preview while the vault stays
     split — same two-truth problem in reverse, plus a cross-repo
     contract change for what is really a content bug.
   - *A new manual marker* (e.g. "type `=` on the underline to merge
     it," mirroring `<` continuations) is reliable but asks Bryan to
     annotate his annotations. The intent is already fully expressed
     by the underline gesture; a second gesture taxes every future
     underline to pay for a classifier we can write once.
2. **Do not distinguish by color.** Highlights color categories do not
   survive into the sidecar Markdown (no color field in
   `SidecarAnnotation`, no color in the generated-body contract), so a
   "make emphasis a color" workflow would require PDF-geometry reads to
   recover the color on every scan. Bold-substring matching uses data
   already in hand.
3. **Do not reach for PDF geometry in v1.** Reading `/Underline`
   `QuadPoints` via lopdf would classify underlines exactly, even when
   the Markdown is ambiguous. But it adds per-scan PDF parsing on every
   host, fails on scanned/image PDFs, duplicates the sidecar as a truth
   source, and complicates the Mac/athena/apollo scan parity story.
   Keep it as the documented fallback if Phase 0 shows the Markdown
   signal is ambiguous (criteria in §5.1).
4. **The real risk is misattribution, not missed merges.** A missed
   merge leaves today's (merely ugly) output. A wrong merge puts bold
   on words Bryan never stressed, and — worse — deletes the underline's
   block, orphaning any links or tasks pointing at it. So the design
   below is deliberately conservative: bare-only, unique-match-only,
   nearby-only, fail-open, stub-preserving. "When possible" must mean
   "when unambiguous," and the default for doubt is today's behavior.
5. **Beauty is a constraint, not a garnish.** The merged quote must
   read as normal prose with quiet stress. That rules out `==mark==`
   (Obsidian yellow-on-yellow against the quote's own accent, noisy at
   three stresses per quote), `<u>…</u>` (raw tags in the Mac preview,
   which only understands `**`; inconsistent in RSS/export/print
   paths), and nested callouts per stress (each stress would become a
   visual "card," heavier than the thought it decorates). `**bold**`
   inside the existing callout is the only option both renderers
   already make beautiful. No new visual language to learn, no theme
   to update.

---

## 5. Recommended design

### 5.1 Step zero: confirm the Markdown signal (Phase 0, half a day)

Before merge logic, Bryan (or whoever sits at the Mac) produces golden
fixtures from the real app:

- **A.** One highlight + one inner underline, same page.
- **B.** One highlight + two/three inner underlines (including one at
  the very start and one at the very end of the parent).
- **C.** Adversarial: underline with its own comment; underline whose
  words also appear elsewhere in the parent; underline on a different
  page than any highlight; lone underline with no surrounding
  highlight; highlight the user manually bolded in Highlights' note
  editor (if the app even allows that — needed to bound false
  positives).

Export/checkout the sidecar `.md` for each and check them in as
`tests/fixtures/highlights_ref/underline_*.md`. The classifier in §5.2
is written against these files, not against my working model. **Go /
no-go rule:** if underlines are fully-`**bold**` blockquote chunks
(model holds), proceed with the Markdown-only classifier. If underline
chunks are Markdown-indistinguishable from highlights, stop: the choice
is (i) PDF-geometry classification, or (ii) a manual marker. Do not
build the heuristic matcher on an unconfirmed signal.

### 5.2 Classifier: what counts as an "underline annotation"

A `SidecarAnnotation` is an *underline candidate* iff all hold:

- `kind == Highlight` (never `Image` captions, never `StandaloneNote`
  sticky notes — same exclusion the `<` continuation grammar uses);
- not a marker mirror (`is_sidecar_marker_mirror`);
- its beautified text is **fully wrapped in exactly one `**…**` pair**
  with non-empty, non-whitespace inner text (after `beautify`, so
  reflow/hyphen healing has already run — match what the reader sees);
- stripping that one outer pair leaves text with **no remaining `**`**
  (no partial-bold, no multi-span chunks — those stay separate; they
  are either user-authored Markdown or a signal Phase 0 didn't cover);
- it carries **no comment, no task source, no image-note refs**
  (`comment`/`task_source` empty, `split_image_note_lines` yields
  nothing). Anything the user said *about* the underline is content,
  not emphasis — it keeps its block.

Rationale for "fully bold only": it is the narrowest rule consistent
with the observed symptom, it has an obvious inverse (a partially-bold
highlight is a highlight that *contains* emphasis, not an underline),
and it fails closed on every ambiguous shape.

### 5.3 Matcher: which parent, and when to decline

For each underline candidate in sidecar order, consider parent
candidates: the nearest non-candidate `Highlight` annotations within a
small window (recommendation: **±2 annotation positions**, same-page
preferred — see below), plus the head of any already-formed
continuation group in that window (merge into the group quote, not a
single member). Normalize both sides identically before comparing:
`beautify` → collapse all whitespace runs → normalize smart quotes /
dashes to ASCII equivalents (the same normalization the renderer
already applies, so matching sees what rendering shows). Matching is
**case-sensitive** (case-insensitive bolding would claim "Fox" for an
underline of "fox") and **substring** on the normalized forms.

Merge iff **all** hold, else leave the underline as its own block:

1. Exactly one parent candidate contains the underline's inner text as
   a substring (zero → dangling, keep; two or more → ambiguous, keep).
2. Within that parent, the match occurs **exactly once** (two
   occurrences of "brown fox" in one quote → keep separate; we cannot
   know which occurrence was underlined).
3. The parent is on the **same page** (`page_index` equal when known;
   else identical `page_label`) or an **adjacent page**
   (`page_index` ±1, or the merged `Pages 11–12` / `pp.` group form).
   Anything farther → keep. Underlines are emphasis *within* a nearby
   thought, not cross-chapter links.
4. The underline is not longer than the parent (a longer "underline"
   containing the highlight is either a duplicate annotation or a
   different gesture — keep both).
5. Neither side is participating in a conflicting merge (an underline
   merges into at most one parent; a parent span is bolded at most
   once — overlapping underline candidates resolve in sidecar order,
   first wins, the loser stays separate).

Precedence when several parents contain the text (before rule 1
rejects): nearest preceding candidate wins over following (the natural
creation order is highlight-then-underline), then smallest page
distance, then smallest position distance. But note rule 1 still
requires global uniqueness inside the window — precedence only orders
the search, it never breaks a tie silently.

Deliberately no fuzzy matching in v1: no stemming, no punctuation
folding beyond the whitespace/smart-quote normalization above, no
cross-hyphenation guessing beyond what `beautify` already heals. Every
fuzz knob is a misattribution knob. Revisit only with failing fixtures
in hand.

### 5.4 Rendering, identity, and the after-state

- **Parent rewrite.** Wrap the matched span in the parent's quote in a
  single `**…**` pair, at every layer that carries the quote: the
  `> [!quote]` callout line(s) in the managed region and the
  `quote` field of the `bob ref show` JSON (same string, so the Mac
  preview and copy payloads agree). If the parent span is already bold
  (already contains `**`), do not double-wrap — treat as ambiguous and
  keep separate.
- **Underline absorption.** The underline's block disappears from the
  managed region. Identity follows the continuation precedent exactly:
  the head (parent) `^h-…` ID is byte-identical with or without merges
  (it hashes only the parent's raw sidecar text, so bolding the render
  does not re-key it); the absorbed underline's ID is computed
  unchanged (so un-merging restores the identical block); a
  previously-published underline leaves a
  `> [!info] Merged emphasis / Now part of [[#^h-<parent>|…]]`
  redirect stub under `### Removed highlights` — never a `[!warning]
  Removed highlight` tombstone, which would claim deletion. A
  never-published underline leaves no stub.
- **Tasks and comments are never absorbed.** By §5.2 the merger only
  ever sees bare underlines, but defense in depth: the plan builder
  re-checks `comment`/`task_source`/image-notes at merge time, and any
  underline that gained an annotation task since classification is
  skipped (its `🔖`/`[h::]` bindings in `annotation_tasks.rs` keep
  pointing at a live block).
- **Counts and JSON.** Mirror the continuation observability:
  `bob ref sync --dry-run` gains an `emphasis:` line (merged count)
  plus per-dangling `emphasis_dangling:` lines only when nonzero;
  concise `scan` prints `N emphasis` after continuation details;
  scan JSON gains `notes[].emphases` / `notes[].emphases_dangling`
  only when nonzero, `schema_version` stays `1`,
  `highlights_count` counts a merged group once (the absorbed
  underline is not a highlight anymore). No existing field changes
  shape — the Mac app parses nothing new.
- **Reversibility.** Deleting the underline in Highlights (or
  un-bolding it, if the app permits) restores the parent's plain render
  and either restores the underline's block (if it still exists as an
  annotation) or drops its redirect stub on the next scan. There is no
  bob-side state: the fold is stateless and deterministic like `<`
  continuations, recomputed from the sidecar on every sync. Nothing is
  written to the PDF or sidecar.

### 5.5 Beauty details (why this looks good, not just correct)

- One thought, one card. The merged `> [!quote] The quick **brown
  fox** jumps…` keeps Obsidian's quote typography (secondary color,
  comfortable line length) with the stressed words in the theme's bold
  weight — emphasis you notice while reading, not a second card
  competing for attention.
- The Mac preview's existing quote style (`.callout`, primary for
  highlights / secondary-italic for notes, yellow left rule,
  `lineSpacing(2)`, `RefsQuoteEmphasis` strong runs) was clearly built
  for exactly this string shape; merged quotes exercise a path the app
  already styles, rather than a new shape needing a new style.
- Multi-stress quotes (`The **quick** brown **fox** jumps`) stay calm
  because bold is inline: three stresses add zero cards, zero rules,
  zero vertical rhythm breaks. The rejected alternatives all add
  chrome per stress.
- Accessibility comes free: `quoteText` builds a real `AttributedString`
  with `.stronglyEmphasized` runs (VoiceOver announces emphasis), and
  the combined accessibility labels already read quote-then-comment.
  No new label logic needed.

---

## 6. Options considered (and why they lose)

| Option | What changes | Verdict |
|---|---|---|
| **A. Render-time auto-merge (recommended)** | New `emphasis` plan step in `sidecar_render.rs`; classifier + matcher per §5.2–5.3; stubs/counts/JSON per §5.4 | Fixes vault, `ref show`, tasks, and Mac preview at once; deterministic; reversible; no client changes |
| B. Manual merge marker (underline-side `<`-style sigil) | New grammar + docs + user gesture per underline | Reliable but taxes every future underline; second gesture for already-expressed intent; worse intuitiveness |
| C. PDF-geometry classification (`/Underline` `QuadPoints`) | lopdf annotation reads on every sync/scan | Exact classification, but heavy, host-fragile, duplicate truth source; hold as fallback if Phase 0 fails |
| D. Obsidian CSS / plugin post-process | Stylesheet or plugin joins adjacent quote callouts | Cosmetic only; block IDs, copy, tasks, Mac preview stay split; two truths |
| E. Mac-app-only merge | Swift-side substring join on `quote` strings | Preview heals, vault stays split; violates thin-client decision; cross-repo contract for a content bug |
| F. `==mark==` or `<u>` instead of `**bold**` | Different inline markup in merged span | `==` clashes with quote accent and has no Mac-renderer support; `<u>` renders as literal tags in preview; both less portable than bold |
| G. Do nothing / retrain the gesture | Docs telling Bryan to stop underlining | Cheapest, and worth saying: if merge proves unreliable, dropping underlines loses little. But the gesture is good and the fix is small — try A first |

---

## 7. Adjustments to the requirements (explicit)

1. **Automatic, not manual.** The prompt asks to "merge these in a
   visually appealing way somehow when possible" and invites design
   leadership. I am resolving the "somehow" as *no new user action*:
   the underline already is the instruction. A marker/gesture variant
   is the fallback, not the default.
2. **"When possible" = the five gates in §5.3, nothing looser.**
   Anything failing a gate keeps today's separate block. In
   particular: annotated underlines (comment/task/image) never merge,
   and multi-occurrence matches never merge. I would rather Bryan
   report "this one didn't merge" (actionable, visible in dry-run)
   than "this merged onto the wrong words" (silent corruption).
3. **No Mac-app or plugin changes in v1.** The prompt names both
   surfaces as broken; the fix still ships in one repo because the
   second surface reads the first repo's output. If the Mac preview's
   bold styling ever needs tuning (weight, color), that is a separate,
   purely-cosmetic follow-up with no contract impact.
4. **No configuration knob in v1.** No
   `highlights.merge_underline_emphasis`, no per-note frontmatter
   opt-out. A flag would let a bad merge hide instead of being fixed,
   and the fail-open gates already bound the blast radius to
   "today's behavior." Add an opt-out only on evidence (a class of
   false merges the gates cannot express), not preemptively.
5. **Redirect stubs say "Merged emphasis," not "Merged highlight."**
   Small wording point with real UX value: the `### Removed
   highlights` section will now contain two kinds of entries
   (continuation merges + emphasis absorptions). Distinct titles keep
   the archaeology readable and keep `doctor`/diagnostic grep counts
   meaningful.

---

## 8. Verification plan (what "done" looks like)

- **Phase 0 fixtures.** `tests/fixtures/highlights_ref/underline_*.md`
  (A/B/C per §5.1) checked in from real app output; classifier unit
  tests assert candidate/non-candidate on each chunk.
- **Golden render tests.** Before/after generated-region assertions:
  canonical merge (one parent + one underline → one bolded block, head
  ID stable, no stub on first publish); multi-stress (one parent +
  two underlines → two bold spans); annotated underline (keeps block);
  ambiguous underline (keeps block + `emphasis_dangling` line);
  un-merge (remove underline from sidecar → parent plain again,
  stub dropped or retained per published-state).
- **ID/task stability.** Head `^h-…` IDs byte-identical with and
  without merges; absorbed IDs restorable; `annotation_tasks.rs`
  bindings for merged-away blocks resolve via stubs; no task rewrite
  on retroactive merge (same guarantee continuations already give).
- **Observability.** `--dry-run` shows `emphasis:` /
  `emphasis_dangling:`; `scan` counts; JSON fields present-only-when-
  nonzero; `schema_version` unchanged; full `just check` green.
- **Visual check (the beauty gate).** After a real `bob ref sync` on a
  fixture-derived vault: screenshot the merged quote in Obsidian
  reading view *and* the Mac ref panel preview; confirm single card,
  correct bold spans, no orphan blocks, VoiceOver reads emphasis.
  This is the one check unit tests cannot replace — do not skip it.
- **Rollout.** Ship behind no flag but announce the dry-run lines in
  the release note; first real scan reviewed with `--dry-run` on
  Bryan's vault before writing.

---

## 9. Risks and open questions

- **Signal risk (the big one).** If Phase 0 shows underlines are not
  `**bold**` chunks — or not consistently so — the Markdown classifier
  is wrong and §5.2 must be rewritten (likely toward PDF geometry or a
  manual marker). Cap Phase 0 time-boxed; do not build the matcher
  first.
- **Order dependence.** The matcher assumes sidecar order is stable
  document order (the same assumption continuations document: sorted-
  by-color/date exports are unsupported). If Bryan ever sorts the
  Highlights sidebar differently, merges degrade to keeps — safe, but
  worth one line in the docs next to the continuation sort warning.
- **Quote-vs-note styling asymmetry.** Merged emphasis only applies to
  highlight quotes, never to standalone-note bodies or image captions
  (same exclusion as `<`). An underline of a sticky note's words stays
  separate — correct, but slightly surprising; document it.
- **Copy-menu interplay.** The Ctrl+Y copy menu (`refs_panel_ctrl_y_*`
  research track) offers per-highlight payloads; merged quotes copy
  with their `**` markers (as continuations already do). Whether the
  copy path should strip or keep emphasis markers for each paste
  target is out of scope here — flag it to that track, don't solve it
  here.

---

## 10. Bottom line

Build **A**: a small, conservative, render-time emphasis merge in
bob-cli (`sidecar_render` + a focused plan module reusing the
continuation stub/count/JSON patterns), gated by Phase-0 fixtures,
with no client changes. It is intuitive (zero new gestures — the
underline already said it), reliable (fail-open gates, stable IDs,
stubs, dry-run visibility, fully reversible), and beautiful (one calm
quote card with inline bold in both Obsidian and the Mac preview,
using render paths that already exist). If Phase 0 falsifies the bold
signal, fall back to **C** (geometry) or **B** (manual marker) in that
order — do not ship a heuristic matcher on an unconfirmed signal.
