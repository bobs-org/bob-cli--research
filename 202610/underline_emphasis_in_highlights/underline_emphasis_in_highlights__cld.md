# Underlines inside highlights: render them as the highlight's own emphasis

- **Researcher:** cld (one of five independent reports)
- **Date:** 2026-10-19
- **Baselines:** bob-cli `1b158e66`, bob-mac-capture `5fd928b`, Obsidian 1.14.4 (`/snap/obsidian/69`)
- **Question:** You use Highlights underlines almost only to add extra emphasis to part of
  a larger highlight. In ref notes and in the Bob Refs preview pane, each underline
  instead shows up as its own separate, bold highlight. How should Bob merge them so the
  result is intuitive, reliable, and beautiful? Is the idea sound, and what would I
  change?

## Recommendation in brief

**Build it, in bob-cli, as an automatic render-time fold.** No marker is needed. An
underline whose text sits wholly inside one highlight on the same page becomes a `**bold**`
run inside that highlight's quote. The underline's comment, tasks, and screenshots join the
highlight's block. Nothing is written to the PDF or the sidecar, and removing the
highlight or the underline in Highlights undoes the fold on the next scan.

Five design decisions carry most of the weight:

1. **Containment is the trigger, and the vault confirms it.** All 19 underlines in your
   library sit wholly inside a highlight on the same page. None is standalone,
   ambiguous, or only partly covered (§2). An underline that does not match exactly one
   highlight stays its own block, rendered as one clean bold run.
2. **Match on text with whitespace ignored, then snap to whole words.** Sidecar order
   cannot be trusted: 16 underlines come after their highlight and 3 come before it. The
   PDF's own timestamps show you often draw the underline first. So the host is found by
   content, never by position, and `what didn’` is widened to `what didn’t`.
3. **Keep `**bold**` as the stored syntax and add one CSS rule in the vault.** Obsidian
   renders every highlight as the quote callout's grey, semibold *title*, so bold inside
   it only moves from weight 600 to 800. That change is nearly invisible today, especially
   in dark mode. A 3-line vault snippet draws the emphasized words in full ink against
   the grey quote (Figure 1). The Mac preview already renders `**` runs as strong emphasis.
4. **Identity is preserved, and only anchors with a task get a redirect stub.** The host's
   `^h-` ID never changes. An absorbed underline's ID is neither tombstoned nor, in the
   common case, stubbed. Only a previously published underline that carries a `#task`
   keeps a redirect stub, because a 🔖 link points at it. In the vault today that rule
   yields exactly one stub, not nineteen.
5. **Fix the latent `<` interaction.** Absorbed underlines must be invisible to the
   continuation marker's "previous highlight" search. Otherwise a `<` on the next page
   joins the underline instead of the highlight that contains it. The current code
   already has this bug in waiting.

One gap is not closed by bob-cli: the Mac inspector cuts quotes off at 3–4 lines. For 7 of
the 19 merged highlights, the bold run starts more than 150 characters in, so a small
follow-up in the Mac app should show the excerpt around the emphasis (§6.7).

![Figure 1: today versus recommended, rendered with Obsidian 1.14.4's own app.css](underline_emphasis_merge__cld_before_after.png)

*Figure 1. Gas Town pp. 6, 7, and 10, rendered with Obsidian's real `app.css` in
headless Chrome using Inter. Left: today. Right: merged, with the recommended snippet.*

---

## 1. What happens today, verified

### 1.1 The Highlights export writes an underline as a bold blockquote

Your sidecars contain the underline as its own annotation. Each physical `>` line is
wrapped in `**…**` separately, and hard-wrapped lines sit inside the bold span
(`lib/blogs/gas_town_emergency_user_manual.md`, p. 5):

```md
> It’s OK not to swarm all the time. … For instance, you
> might be
getting ready to restart your entire town, for a
> version upgrade, …

***

> **For instance, you might be
getting ready to restart your entire**
> **town, for a version upgrade,
and you want to land everyone’s**
> **work first and clean all the
sandboxes. Or maybe you need to**
> **roll out a schema change before
everyone continues**
```

The PDF confirms what each item is (`mutool show …pdf 771 772 808 813 820 821`):

- The bold items are `/Subtype /Underline`, drawn in green (`/C [.5 1 .5]`).
- Their hosts are `/Subtype /Highlight`, drawn in yellow (`/C [1 1 .5]`).
- Every underline quad lies inside its host's quads.
- The `/M` timestamps show the underline was drawn *before* its highlight on p. 4 and
  p. 6, and after it on p. 7. You underline first and highlight second about as often as
  the reverse.

A web search found the Highlights developer's statement that highlighted, underlined, and
strikethrough text export as quotes with "normal, bold and strikethrough emphasis". The
`highlights.app` site itself now redirects to a domain-parking page, so the PDF evidence
above is the authority.

### 1.2 bob renders it as a second block

`parse_sidecar_chunk` keeps the `**` in `SidecarAnnotation.text`. The renderer reflows
each line on its own, so the note shows broken per-line bold runs as a separate block
(`ref/blogs/gas_town_emergency_user_manual.md`):

```md
> [!quote] It’s OK not to swarm all the time. … For instance, you might be getting ready to restart your entire town, … before everyone continues. It’s totally normal …

^h-fbbc682d3efb

> [!quote] **For instance, you might be getting ready to restart your entire** **town, for a version upgrade, and you want to land everyone’s** **work first and clean all the sandboxes. Or maybe you need to** **roll out a schema change before everyone continues**

^h-030d5bfd330e
```

This causes four separate problems:

1. **Duplicated text.** The underlined words appear twice.
2. **Lost context.** A comment on an underline, such as "This feels wrong!" on p. 7,
   attaches to a fragment and not to the passage around it.
3. **Inflated counts.** `highlights_count` reports 15 for Gas Town; the true count is 10.
4. **Broken runs.** The `** **` seams show as raw markers in `bob ref show`. They would
   also block hyphen healing at a `>`-line break (`sub-**` + `**goals`), because
   `beautify_annotation_text` never sees the hyphen at the end of the line.

### 1.3 In Obsidian the "bold" barely shows

`push_callout_block` (`sidecar_render.rs:554`) writes the quote's first paragraph on the
`> [!quote]` line. Obsidian treats that text as the callout **title**. In Obsidian
1.14.4's `app.css` (extracted from the snap's `obsidian.asar`):

- `--callout-quote: #9e9e9e` (line 2155). `.callout-title` takes that grey color.
- `.callout-title-inner { --font-weight: var(--callout-title-weight) }` (line 11753)
  makes every highlight semibold (400 + 200 = 600).
- `strong { font-weight: calc(var(--font-weight) + var(--bold-modifier)) }` (line 14534)
  therefore renders bold inside a title at 800. The color stays the same grey.

So in Obsidian an underline appears as a grey 800-weight run beside grey 600-weight text.
In a separate block it looks almost exactly like any other highlight (Figure 1, left).
Merged runs with default CSS have the same problem (Figure 2, column A).

### 1.4 The Mac preview reads the ref note, not the sidecar

The Bob Refs inspector loads `bob ref show <note> -f json`. That command parses the
managed region (`region.rs` `parse_managed_region`), so the inspector shows whatever
bob-cli rendered:

- `RefsQuoteEmphasis.runs` (`RefsInspector.swift:518`) already turns balanced `**` pairs
  into `.stronglyEmphasized`.
- Today each underline is its own entry. The 8 commented underlines appear under YOUR
  NOTES detached from their passages.
- **Once bob-cli merges, the Mac shows merged quotes with no code change.** This follows
  the thin-client decision (`decisions:mac-capture-is-a-thin-client`).

## 2. How you actually use underlines (vault survey)

I scanned every Highlights sidecar under `~/bob/lib`, both Markdown and TextBundle, with a
read-only Python prototype.

| Measure | Value |
| --- | --- |
| Sidecars / text highlights / underlines | 171 / 332 / 19 |
| Sidecars with any underline | 7 |
| Underlines wholly inside a **same-page** highlight | **19 of 19** |
| Standalone, partial-overlap, cross-page, multi-host, repeated-text | 0, 0, 0, 0, 0 |
| Host immediately adjacent in sidecar order | 19 of 19 (16 after the host, 3 before) |
| Underlines carrying their own comment | **8 of 19 (42%)** |
| Underlines carrying a `#task` | 1 (`gastown_readme` p. 2, routed into `sase.md`) |
| Hosts with their own comment as well | 1 (Gas Town p. 4; its underline has none) |
| Hosts containing two or more underlines | 0 |
| Underline ending mid-word | 1 (`… what didn’` in a host reading `… what didn’t.`) |
| Underline share of host length | 4%–72% (median about 25%) |
| Emphasis starting more than 150 characters into the host | 7 of 19 (3 of them commented) |
| Published underline `^h-` IDs linked from anywhere outside their own block | 1 of 19 (the routed task above) |

Prototype check: matching ignores whitespace and snaps to whole words (§6.3). It merges
all 19 cleanly, including the `didn’t` case and the hyphen-split `sub-wisps`. Your
stated habit holds in practice: in this vault an underline means "emphasis inside a
highlight", every time.

## 3. Is this a good idea?

**Yes, clearly.** It is a better fit than the `<` continuation marker was. That feature
needed an explicit gesture because automatic page-split merging was only about 50%
precise. Here the signal is structural: one annotation's text is *contained in* another
on the same page. That is not a coincidence a reader could misinterpret, and the survey
shows 100% precision and 100% recall.

Why it belongs in bob-cli, at render time:

- **One fix, every surface.** Obsidian, `bob ref show`, the Mac inspector, the Mac copy
  card, and agents all read the managed region. Changing the region changes everything
  downstream, which matches how continuations shipped.
- **Stateless and reversible.** The region is regenerated from the sidecar on every scan.
  Delete the highlight and the underline renders on its own again. Delete the underline
  and the bold run disappears.
- **No new gesture.** You keep using Highlights exactly as you do now, and existing notes
  improve on the next scan.

What would make it a **bad** idea:

- **Fuzzy or positional matching.** Merging into "the previous highlight" would be wrong
  3 times in 19, because those underlines sort *before* their host.
- **Silent loss.** Dropping the underline's comment or task, or an underline vanishing
  without merging.
- **Identity churn.** Re-hashing the host, or tombstoning the absorbed underline as
  "Removed".
- **Stub clutter.** Adding a "Merged highlight" stub to seven notes for anchors that
  nothing links to.
- **The wrong syntax for the surfaces.** `==mark==` or `<u>` would show as raw markup in
  the Mac app, in `bob ref show`, and in copied text.

The design below avoids each of these.

## 4. Alternatives considered

| Alternative | Verdict |
| --- | --- |
| **Automatic, containment-based, render-time fold** | **Recommended.** Matches your usage exactly and is reversible. |
| An explicit marker on the underline's note (as with `<`) | Rejected. Containment is already unambiguous, and a marker adds friction you would forget. Escalate to a marker only if false merges ever appear (§8). |
| Merge the underline into the "previous" or "next" annotation | Rejected. Sidecar order puts 3 of 19 underlines before their host. Highlights sorts by position, and an underline that starts on an earlier line sorts first. |
| Geometry: match the PDF `/QuadPoints` of `/Underline` against `/Highlight` | Not for v1. It finds the host but not *where in the text* to bold, and the sidecar has no annotation IDs to join on. Keep it as a v2 tie-breaker for repeated text; `marker.rs` already walks `/Annots` with lopdf. |
| Render the underline as a nested sub-callout under its host | Rejected. It duplicates text, the region parser accepts only one depth-2 Comment group (`region.rs:449`), and it looks busier. |
| Use a second highlight color in Highlights instead of underlines | Rejected. Colors are not in the Markdown export, and overlapping highlights are messy in the PDF. |
| Store the emphasis as `==mark==` | Rejected. It is Obsidian-only, shows as raw `==` in the Mac app, `ref show`, and pasted LLM context, and means "highlight inside a highlight". |
| Store the emphasis as `<u>…</u>` | Rejected. It is HTML in Markdown, raw in the Mac app, and underlines on screen read as links (Obsidian sets `--link-decoration: underline`). |
| Store the emphasis as `*italic*` (the scholarly "emphasis added") | Rejected. It is weaker than what you mean by "extra emphasis" and would be invisible in themes that italicize quotes. |
| Rewrite the sidecar or the PDF | Rejected. Highlights owns both and overwrites the sidecar on autosave. |

## 5. Requirement adjustments (called out explicitly)

| # | You asked for | Adjusted to | Why |
| --- | --- | --- | --- |
| R1 | Merge "when possible". | Merge when the underline's text, with whitespace ignored, occurs **exactly once** inside **one** text highlight on the **same page**. If several hosts qualify, the nearest in sidecar order wins. Repeated text inside one host, or no host at all, leaves the underline standalone and reports it. | Precise and predictable. A wrong bold run is a silent misquote, while a standalone block is visibly "not merged". |
| R2 | (Unstated) underline comments | An underline's comment, `#task` lines, and screenshot image notes join the host's single Comment callout as their own paragraphs. A short bold excerpt anchors a paragraph only when the reader could otherwise not tell which emphasis it is about (§6.4). | 42% of your underlines carry a comment. Dropping them, or leaving them to dangle, would make the feature a regression. |
| R3 | "Visually appealing" | Keep `**…**` as the stored syntax. Add a vault CSS snippet (`ref-highlights.css`) that brings bold runs in quote callouts to full ink. Optionally mirror that focus in the Mac inspector. | Every surface already understands `**`. The snippet fixes the real Obsidian problem (§1.3) without changing any format. |
| R4 | (Unstated) identity | The host `^h-` never changes. Absorbed underline IDs are never tombstoned. A redirect stub appears **only** for an underline that was already published **and** carries a task. | Continuations stub every published follower, but underlines are often published *before* their host exists (you draw them first), so that rule would add 19 stubs, 18 protecting nothing. |
| R5 | (Scope) the Mac preview pane | bob-cli is phase 1 and fixes the pane by itself. Phase 2 is a small presentation change in Bob Refs that windows a clipped quote around its first bold run. | Note quotes clip at 3 lines and highlights at 4 (`RefsVisualTokens.swift:56–57`). 7 of 19 runs start late. |
| R6 | (Scope) other markup | Underlines only. Build the classifier so strikethrough (`~~…~~`) is a later, small addition. | You have 0 strikethroughs. YAGNI, but do not paint it into a corner. |
| R7 | (Scope) negatives | No marker, config flag, CLI flag, sidecar or PDF write, region-parser change, or `ref show` schema change. | The implementer should not invent any of these. |
| R8 | (Scope) existing notes | It applies retroactively on the next scan: 7 notes and 19 underlines, expecting 1 stub. Preview with `bob ref scan --dry-run` first. | It is a render-time fold, and the dry run shows every change before it is written. |
| R9 | (Bug found) `<` interplay | Absorbed underlines are excluded from the `<` "previous text highlight" search. | `plan_continuations` treats every `Highlight` kind as text (`continuation.rs:110`, `208`). An underline sorted after its host would capture a `<` from the next page. |

## 6. The design

### 6.1 Recognizing an underline

An annotation is an **underline** when:

- its kind is `Highlight` and it is not a marker mirror, and
- every logical quote line is wrapped in `**…**`. A logical line is a `>` line plus its
  hard-wrapped continuation lines, which the parser pushes separately
  (`sidecar.rs:333`), so wrapping must be checked over the run of lines between bold
  delimiters, and
- no `**` appears anywhere else.

Detect this while parsing, where `>` lines are still distinguishable. Record it as a
derived field, for example `markup: Option<Markup::Underline { inner }>`:

- **Leave `text` byte-identical.** `annotation_block_id` hashes `text` and
  `ordinal_on_page` (`sidecar_render.rs:433`), so every existing underline ID stays
  stable.
- **Build `inner`** by removing the delimiters line by line *before* reflow. This lets
  the existing hyphen healing see `sub-` + `goals`.

### 6.2 Finding the host

Run this before continuation planning, over all annotations:

```text
for each underline U (in sidecar order):
  key(U) = whitespace-free projection of beautify(inner(U))
  hosts  = text highlights H (not underlines, not marker mirrors) with
           page(H) == page(U)                      # same page label/index
           and key(U) occurs in key(beautify(H.text))
  pick   = the host nearest to U in sidecar order; ties go to the earlier one
  if no host                        -> standalone   (reason: no_host)
  elif key(U) occurs twice in pick  -> standalone   (reason: ambiguous)
  else                              -> absorbed into pick
```

Notes on the matching:

- **Whitespace-free matching** absorbs every spacing artifact: reflow differences,
  hard-wrap points, and the `m ulti`-style fragmentation from web-clip PDFs
  (`bob-cli-85`). Both annotations come from the same glyphs, so only spacing can
  differ.
- **Apply the same cleanup to both sides.** That means NFKC/ligatures, soft hyphens,
  zero-width characters, and return-link glyph stripping when `return_links: true`.
- **"Same page"** means the same `page_index` when both are known, otherwise the same
  `page_label`. An underline cannot cross a page: PDF annotations are per page.
- **Hosts inside continuation groups.** A host may be a member of a `<` group. The run is
  placed inside that member's part of the group quote (§6.6).

### 6.3 Placing the bold run

Do this on the host block's *final* beautified quote, the string that will be written:

1. **Locate.** Map the matched span from the whitespace-free projection back to character
   offsets `[a, b)` in the quote.
2. **Snap to whole words.** If `a` falls inside a word, move it back to the word's start;
   if `b` does, move it forward to the word's end. Word characters are Unicode letters and
   digits plus `’` and `'`. This turns `what didn’` into `what didn’t`, which is
   exactly how you read it.
3. **Trim** whitespace at the ends.
4. **Guarantee CommonMark flanking.**
   - An opening `**` must be left-flanking: not followed by whitespace, and if followed by
     punctuation, preceded by whitespace or punctuation.
   - A closing `**` must be right-flanking, the mirror rule.
   - If either side fails, widen that side to the nearest whitespace boundary, which
     always succeeds.
   - On the real data no case needed widening: `**“Landed” … finished”.**`,
     `fully-spec’ed **beads epics**.` and `what didn’t**.` are all valid.
5. **Never cross a paragraph break.** If `[a, b)` spans a blank line, emit one run per
   paragraph. Emphasis cannot span Markdown blocks, and the first paragraph is the
   callout title.
6. **Union runs.** Overlapping runs, or runs separated only by whitespace, become one run.
   This prevents `**a** **b**`.
7. **Insert** `**` at the final offsets.

**Standalone underlines** render once, as `**<beautified inner>**`. That is one clean run
with no `** **` seams, so a standalone underline still reads as "this whole passage was
emphasized".

### 6.4 Comments, tasks, and image notes

The host block's Comment callout gathers paragraphs in this order:

1. The host's own comment (or each continuation member's, in order).
2. Each absorbed underline's comment, in the order its run appears in the quote.

Within that:

- Labels and list markers are stripped **per piece before joining**, exactly as in
  continuations.
- **Anchor rule.** Prefix an underline's comment with `**<first ≤ 6 words of its run>…** — `
  only when the block shows two or more comment sources, or two or more bold runs.
  Otherwise the single bold run and the single comment explain each other, so the anchor
  would be clutter. In the vault today this never triggers. It exists so that a future
  "host comment + underline comment" pair stays readable:

  ```md
  > > [!note] Comment Should sase run like claude code …?
  > >
  > > **You technically only need…** — Isn’t this the tutorial path?
  ```

- **Image notes** (a screenshot path in the underline's note) embed under the host quote,
  as they already do for continuation members.
- **Tasks:** see §6.5.

This keeps the region's existing shape: one quote, optional image notes, and at most one
`[!note] Comment` group. So `region.rs`, `bob ref show` JSON, and the Mac decoder need no
change.

### 6.5 Identity, tombstones, stubs, and tasks

| Item | Rule |
| --- | --- |
| Host `^h-` | Unchanged. It is computed from the host's own raw text and ordinal, so adding or removing an underline never changes it. |
| Underline `^h-` | Computed exactly as today. When absorbed, it is not rendered, not counted, and **excluded from `removed_ids`** (extend `absorbed_ids`, `sidecar_render.rs:31` and `216`). |
| Redirect stub | Emitted under `### Removed highlights` only if the absorbed ID already appears in the existing region (published) **and** the underline yields at least one annotation-task candidate. Once emitted, it persists while the absorption holds, exactly like continuation stubs. Reuse `continuation_redirect_stubs`' format: `[!info] Merged highlight` and `Now part of [[#^h-host\|the Page N highlight]].` |
| Task `[h::]` | Keyed to the **underline's own** identity ID, so toggling the merge never duplicates a task. Do not bump `HIGHLIGHT_TASK_ID_VERSION`. |
| Task 🔖 | Links to the **host** block: map the underline's order to the host's ID in `block_ids_by_annotation_order`. `annotation_tasks.rs:28–37` already splits identity from link IDs, so this plugs in unchanged. |

Why the stub rule differs from continuations:

- A `<` is a deliberate, rare gesture, so a published follower is unusual.
- An underline is routinely drawn *before* its highlight. 2 of the 3 PDF pairs I checked
  were drawn in that order, seconds or a minute apart. Any scan in that gap publishes the
  underline as a standalone block, and the next scan absorbs it.
- Under "stub every published ID", that ordinary workflow would leave a permanent "Merged
  highlight" stub each time. On rollout alone it would add 19 stubs across 7 notes, 18 of
  which nothing links to (§2).
- The only links bob itself creates to an annotation are task 🔖 links, and those are
  exactly what the task-bearing condition protects. Today that means one stub:
  `gastown_readme` `^h-476bb727cc72`, which the routed task in `sase.md:1349` points at.
- The remaining risk is a block link you pasted by hand to an old underline block. Its
  scroll position degrades to the top of the note; the link itself still works. None
  exists today.
- If you would rather pay for complete safety, an alternative predicate is to stub when
  any vault note contains `#^<id>` outside this note's region. It is computed only on the
  first absorption, and a full-vault grep is cheap. I would not start there.

### 6.6 Interplay with `<` continuations

Order of operations:

1. `plan_underlines` runs first.
2. `plan_continuations` then runs over the annotations **minus absorbed underlines**.
   Standalone underlines remain ordinary text highlights and can be heads or followers.

This fixes the latent bug described in R9.

When the host belongs to a continuation group:

- Place the run inside the member it was matched against. Locate that member's beautified
  text inside the group quote first, then search within that window.
- A `<` typed on an underline that gets absorbed is satisfied silently, and its token is
  stripped from the comment. Two half-runs that meet across a join seam become one run
  through step 6 of §6.3.

### 6.7 Visual treatment on each surface

**Obsidian: add a vault snippet.** Create `.obsidian/snippets/ref-highlights.css` and add
`"ref-highlights"` to `enabledCssSnippets` in `appearance.json`. Both files are
git-tracked, so `bob vault-sync` carries them to the Mac, athena, and apollo.

```css
/* bob ref: an underline drawn inside a highlight renders as **bold** inside
   that highlight's [!quote] callout. Bring those words into full ink against
   the quote's muted text. Nested Comment callouts are not affected. */
.callout[data-callout="quote"] > .callout-title strong,
.callout[data-callout="quote"] > .callout-content > p strong {
  color: var(--text-normal);
}
```

I rendered four treatments with Obsidian's real `app.css`, in light and dark (Figure 2):

- **A, the default**, nearly loses the emphasis.
- **C, a thin green underline**, is faithful to the PDF gesture, but a long run reads as a
  row of links.
- **D, a soft green wash**, is lovely on "beads epics" and heavy on a 330-character run.
- **B, contrast only**, is calm and legible in both themes, and it carries a metaphor that
  fits: *the words you underlined come into focus.*

The `>` child combinators keep the rule off bold text inside the nested Comment callout.
It is theme-agnostic, because it uses only `--text-normal`.

![Figure 2: four emphasis treatments, light (top) and dark (bottom)](underline_emphasis_merge__cld_style_variants.png)

*Figure 2. A: Obsidian default. B: contrast only (recommended). C: contrast plus thin green
underline. D: contrast plus soft green wash.*

**Bob Refs (Mac), phase 2. These changes are presentation-only and follow the thin-client
decision:**

1. **Emphasis-aware excerpt.** In `highlightView` and `noteView`, if a quote contains a
   strong run that starts past roughly the first line's worth of characters, render
   `… <about 8 words of lead-in> **run** …`. Make it a pure `RefsCore` function so it is
   portable-testable; the tooltip and Copy keep the full quote. Without this, late runs
   are clipped by the 3-line and 4-line limits. Examples are the Gas Town p. 10 note
   `hook it so they will continue working on it after a crash` (starts at character 172)
   and `Add evals and the ledger post.` (starts at 274).
2. **Optional "focus" ink.** When a quote has strong runs, draw the plain runs in
   `.secondary` and the strong runs in `.primary`. This mirrors snippet B, so the two
   surfaces feel like one design.

**Terminal (`bob ref show`), small polish.** `quote_lines` (`show.rs:629`) prints `**`
raw. When styling is on, render the runs as ANSI bold; keep the `**` when plain.

### 6.8 Visibility and diagnostics

Model these on the continuation counters:

- **Dry run:** `bob ref sync <pdf> --dry-run` prints
  `underlines: N merged · M standalone`, then one line per standalone underline:
  `underline_standalone: Page 7 (no containing highlight | repeated in highlight)`.
- **Concise scan:** `bob ref scan` adds `N underlines merged` and, when non-zero,
  `M standalone underlines`.
- **Scan JSON:** `notes[].underlines_merged` and `notes[].underlines_standalone`, present
  only when non-zero. `schema_version` stays `1`.
- **Counts:** `highlights_count` counts rendered blocks, so it drops automatically (Gas
  Town 15 → 10).
- **The rule to learn:** a bold run *inside* a highlight is an underline that merged. A
  whole highlight in bold is an underline that found no highlight around it.

### 6.9 Worked examples (real data)

**Gas Town p. 7.** The underline sorts *before* its host and carries a comment. After:

```md
### Page 7

> [!quote] Don’t watch your agents work. Make sure they have their marching orders, and let them do their thing. **But. When you see that an agent is finished working, stop everything, ignore everyone else, and read what it has to say. Scroll back and make sure you understand what it did and what it’s saying. Then act on it. You can go in any order you like, but at some point you have to act on each agent’s response or risk losing work.** Spend your time reading agent responses and giving them direction — nowatching them work
>
> > [!note] Comment This feels wrong! You need to check on goals, not individual agents!

^h-09a36ba7f22f
```

`^h-e9a3ad5f4155` is absorbed, with no stub (no task) and no tombstone.

**Steve Kinney p. 7.** The underline ends mid-word, so the run is snapped:

```md
> [!quote] This is the missing piece in most agent frameworks— … practitioners. **Factual memory tells the agent what it knows. Experiential memory tells it how to do things better—how it solved problems in the past, what worked, what didn’t**.
```

**gastown_readme p. 2.** The underline carries a task, so its published anchor keeps one
stub:

```md
> [!quote] Molecules 🧬 Workflow templates … with tracked steps. **Two modes: root-only wisps (steps materialized at runtime, lightweight) and poured wisps (steps materialized as subwisps with checkpoint recovery).** See Molecules.
>
> > [!note] Comment #task Materialize steps in workflow to enable replay starting at certain xprompt workflow steps? @sase

^h-cdd7eb850000

…

### Removed highlights

> [!info] Merged highlight
> Now part of [[#^h-cdd7eb850000|the Page 2 highlight]].

^h-476bb727cc72
```

The existing routed task keeps its `[h::]` and its 🔖 link to `^h-476bb727cc72`; the stub
forwards to the host.

## 7. Implementation and rollout plan

**Phase 1, bob-cli only. This alone delivers the feature on every surface.**

1. Add an `underline.rs` module next to `continuation.rs`. It holds the classifier (§6.1),
   `plan_underlines` (host map, standalone list with reasons), and the span placer
   (§6.3).
2. In `render_sidecar_highlights`:
   - skip absorbed underlines;
   - give each host block its runs and comment, image-note, and task contributors;
   - extend `absorbed_ids`;
   - emit stubs under the task-bearing rule;
   - render standalone underlines as one clean run.
3. Run `plan_continuations` over the annotations minus absorbed underlines (R9).
4. Add the counters to the dry run, the concise scan, and scan JSON.
5. Write a docs section, "Underline emphasis", in `docs/highlights-ref-sync.md` under
   Generated Body Contract, in the style of the continuation section.

Tests:

- Matcher unit tests:
  - whitespace and fragmentation;
  - hyphen across a `>` line;
  - mid-word snapping at both ends;
  - each flanking rule;
  - curly quotes and punctuation;
  - paragraph split;
  - union of runs;
  - repeated text leading to a standalone block;
  - two hosts, nearest wins;
  - an underline before or after its host.
- Identity tests:
  - the host ID is unchanged;
  - the absorbed ID is neither tombstoned nor stubbed;
  - a published task-bearing ID gets a stub;
  - the stub persists and becomes a tombstone when the underline is deleted;
  - the task 🔖 link points at the host;
  - `[h::]` is stable across merge toggles.
- Continuation test: H on p. 11, U inside H sorted after it, `<`H′ on p. 12. H′ must join
  H.
- A round-trip test that `bob ref show` JSON keeps `**` in `quote`.
- Snapshot fixtures from the 7 real sidecars.

Rollout:

1. Run `bob ref scan --dry-run`. Expect 7 notes changed, 19 merged, 0 standalone, and 1
   stub.
2. Add and enable the snippet.
3. Scan, then review Gas Town and the goals paper in Obsidian, light and dark.

**Phase 2, bob-mac-capture.** Add the emphasis-aware excerpt and optionally the focus
ink. Compile on the Mac per its `AGENTS.md`; `RefsCore` tests run in CI.

**Afterwards.** Record a decision in the `decisions` web, for example "Underlines Inside A
Highlight Render As Its Emphasis", using `/sase_memory_write`. Record it after you accept
the design, not before.

## 8. Risks and open questions

- **False merge from coincidental text.** It requires the same page, whole containment,
  and a unique occurrence, so a false merge is very unlikely. Its blast radius is also
  small: some words show in bold and the comment moves into the neighboring block.
  Reopen with an opt-out marker on the underline's note if it ever happens.
- **Repeated phrase inside one host.** For example, underlining "the agent" in a quote
  that says it twice. Today this stays standalone with a diagnostic. In v2, disambiguate
  with the `/QuadPoints` line index against the host's hard-wrapped sidecar lines.
- **Ordinal churn (`bob-cli-9o`).** Drawing an underline that sorts *before* an
  already-published highlight shifts that highlight's `ordinal_on_page`, and therefore its
  ID. The same happens for every later ID on the page. This feature neither causes nor
  fixes that; it inherits it. Excluding underlines from ordinals would reduce it, at the
  cost of a one-time re-mint. That belongs to the `bob-cli-9o` fix, not here.
- **Literal `**` in source text** (for example `**kwargs`) would confuse emphasis pairing
  in every renderer. That is true today, and the feature does not make it worse. Escape it
  only if it ever appears.
- **Theme dependence.** Snippet B uses only `--text-normal`. It looks right in the
  default light and dark themes I rendered. A custom theme that restyles callout titles
  could weaken it.

## 9. Recommended solution

Ship an **automatic underline-into-highlight fold in bob-cli's renderer**:

- An underline (a sidecar quote whose every line is `**`-wrapped) whose text occurs exactly
  once, with whitespace ignored, inside one text highlight on the same page becomes a
  word-snapped, CommonMark-safe `**bold**` run inside that highlight's quote.
- Its comment, tasks, and screenshots join the host's single Comment callout. A bold
  excerpt anchors a comment only when two or more comment sources or runs make it
  ambiguous.
- The host keeps its `^h-` ID. The absorbed ID is never tombstoned. It keeps a redirect
  stub only if it was already published and carries a task.
- Absorbed underlines are hidden from the `<` continuation search.
- Underlines with no unique host stay as one clean bold block and are counted in the scan
  report.

Pair it with:

1. a 3-line Obsidian snippet, `ref-highlights.css`, that draws bold runs inside quote
   callouts in full ink (treatment B);
2. a phase-2 Bob Refs change that windows clipped quotes around their first bold run.

The result on your vault: 7 notes get shorter, 19 duplicate blocks disappear, 8 comments
move next to the passages they discuss, one task link stays valid through a stub, and the
emphasized words visibly come into focus in Obsidian and in the Mac preview.

---

### Evidence index

- Sidecars: `~/bob/lib/blogs/gas_town_emergency_user_manual.md`,
  `~/bob/lib/blogs/steve_kinney_agent_memory.md`,
  `~/bob/lib/docs/gastown_readme.textbundle/text.markdown`,
  `~/bob/lib/papers/2026_goals_as_first_class_abstractions_in_human_ai_collaboration_automationxp26.md`
- PDF objects: `mutool show ~/bob/lib/blogs/gas_town_emergency_user_manual.pdf 771 772 808 813 820 821`
- Rendered notes: `~/bob/ref/blogs/gas_town_emergency_user_manual.md`,
  `~/bob/ref/docs/gastown_readme.md`. Routed task: `~/bob/sase.md:1349`
- bob-cli:
  - `src/native/highlights_ref/sidecar.rs:295–404` (chunk parser)
  - `src/native/highlights_ref/sidecar_render.rs:4–285` (render), `:420–437` (block IDs),
    `:554` (callout title line)
  - `src/native/highlights_ref/continuation.rs:103–150` (previous-highlight walk)
  - `src/native/highlights_ref/region.rs:294–480` (region parser)
  - `src/native/highlights_ref/annotation_tasks.rs:28–43`
  - `src/native/ref_library/show.rs:629`
- bob-mac-capture:
  - `Sources/RefsCore/RefsInspector.swift:518–616`
  - `Sources/BobMacCapture/Refs/RefsInspectorView.swift:776–816`
  - `Sources/BobMacCapture/Refs/RefsVisualTokens.swift:56–57`
  - `README.md` §Inspector
- Obsidian 1.14.4 `app.css` lines 2155, 2459, 11706–11757, 14534–14538. Figures were
  rendered with that stylesheet in headless Chrome using Inter.
- Prior accepted design for render-time folding:
  `research:202610/highlight_continuation_marker/highlight_continuation_marker__final.md`
- Highlights export convention (corroborating only): developer description via
  [waerfa.com](https://www.waerfa.com/highlights-export-pdf-notes); App Store listing
  [Highlights – Export PDF Notes](https://apps.apple.com/us/app/highlights-extract-pdf-notes/id1498912833).
