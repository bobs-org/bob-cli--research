# Section annotations for Highlights ref notes (`# name` + `@name`)

> **Research query:** Add support for grouping one or more annotations under a "section
> annotation" when `bob ref` renders ref notes from Highlights PDF annotations. A
> section annotation has the form `# <name>`, with an optional description after a
> blank line. Any highlight note, underline note, or standalone note that contains
> `@<name>` renders under that section. The grouping must look good in Obsidian, in the
> Bob Mac Capture Refs panel, and anywhere else ref notes are viewed. Lead the design
> (intuitive, reliable, beautiful), critique the plan, call out justified requirement
> adjustments, and end with a recommended solution.
>
> Researcher: **cld** (one of five independent reports).

## Bottom line

**Build it.** Make it a third **render-time fold**, alongside underline emphasis and `<`
continuations.

- The PDF's Highlights annotations stay the only source of truth. The sidecar is
  re-read on every scan, and nothing is written to the PDF or the sidecar.
- Inside the managed region, each section becomes a real Obsidian **heading** with a
  small **section card** under it.
- Inside sections and in an "Other highlights" group, pages move down to `####`.
- Notes that declare no sections render **byte-for-byte as today**.
- `bob ref show --format json` gains an additive `sections` list and a per-annotation
  `section` key. The Mac Refs inspector draws section headers from that JSON and never
  parses Markdown itself.

The idea is sound. As written, though, the spec would break real notes in your vault.
I recommend nine adjustments ([details](#requirement-adjustments)). These five matter
most:

1. **`@name` is a tag, not a substring.** It counts only when the name matches a
   section declared in the same PDF, and only at the start or end of a line. Matching is
   forgiving: case, `-`, `_`, and spaces are ignored. Mid-sentence mentions such as
   your real `Keep @chat and @agent!` stay prose. A consumed tag disappears from the
   rendered comment. **If you still see an `@name`, it did not group**, the same rule
   the `<` marker uses.
2. **`@` already means "route" on `#task` lines.** `- #task … @sase` sends the task to
   `sase.md` today, and `~/bob/ideas.md` exists. On a `#task` line, a trailing `@name`
   stays a route when that root note exists. Otherwise it means section membership. Today
   that same line fails the whole PDF with `routed annotation task target does not
   exist`.
3. **A `# ` line declares a section only at the very start of a note.** Two real
   sidecars contain hard-wrapped highlighted code whose lines start with `# `. A naive
   grammar would declare sections named "Set default agent" and "should start with
   <?xml". Those same lines already show a separate parser bug, which I filed as
   **`bob-cli-ba`**.
4. **Sections render first, then "Other highlights".** Sections appear in declaration
   order, each with its own page sub-headings, followed by everything else by page. A
   section never renders "in place" in the page flow.
5. **Toggling membership never changes any `^h-` ID.** Highlight IDs already ignore
   comments. Standalone-note IDs must also ignore consumed tags, so adding `@methods`
   never tombstones a block or orphans a task.

## Contents

- [Bottom line](#bottom-line)
- [What exists today (verified)](#what-exists-today-verified)
- [Evidence from the vault](#evidence-from-the-vault)
- [Prior art](#prior-art)
- [Is this a good idea?](#is-this-a-good-idea)
- [Requirement adjustments](#requirement-adjustments)
- [Design](#design)
  - [Grammar: declaring a section](#grammar-declaring-a-section)
  - [Grammar: joining a section](#grammar-joining-a-section)
  - [Resolving membership across folds](#resolving-membership-across-folds)
  - [Persistence: where the grouping lives](#persistence-where-the-grouping-lives)
  - [Rendering in Obsidian](#rendering-in-obsidian)
  - [Rendering in the Mac Refs panel](#rendering-in-the-mac-refs-panel)
  - [Other viewers](#other-viewers)
  - [Identity, tasks, and tombstones](#identity-tasks-and-tombstones)
  - [Diagnostics](#diagnostics)
- [Alternatives considered](#alternatives-considered)
- [Risks and costs](#risks-and-costs)
- [Recommended solution](#recommended-solution)
- [Sources](#sources)

## What exists today (verified)

Everything below was read in this workspace (`bob-cli` at `30f10f15`) or in the linked
`bob-mac-capture` and `bob-plugins` checkouts, opened with `sase repo open`.

**Sidecar parsing.**

- `parse_sidecar_markdown` (`src/native/highlights_ref/sidecar.rs:203`) splits the
  Highlights Markdown or TextBundle sidecar into chunks at page headings and horizontal
  rules.
- `parse_sidecar_chunk` (`sidecar.rs:295`) **filters every Markdown heading line out**
  of highlight comments (`sidecar.rs:347`) and standalone notes (`sidecar.rs:370`). A
  chunk made only of headings is dropped entirely (`sidecar.rs:302`).
- So today a sticky note reading `# Methods` vanishes without a trace. `# Methods` plus
  a description renders as a plain note that keeps only the description.
- `sidecar_page_heading_details` (`sidecar_render.rs:2050`) treats any `#`-led line at
  any level as a page heading when its label starts with `page `, `page:`, `p. `, or
  `p `.
- As a result, a section titled `# P values` or `# Page layout` would currently be read
  as a page break.

**Rendering.**

- `render_sidecar_highlights` (`sidecar_render.rs:4`) walks annotations in sidecar
  order. It skips `<` followers and absorbed underlines, which render inside their head
  or host.
- `push_page_heading` (`sidecar_render.rs:714`) emits `### <page label>` whenever the
  label changes.
- Highlights become `[!quote]` callouts with nested `[!note] Comment` callouts.
  Standalone notes become `[!note]` callouts. Each block is followed by a `^h-…` ID
  line.
- `### Removed highlights` (`mod.rs:197`) collects tombstones and redirect stubs.
- Folds are planned in `plan_annotation_folds` (`underline.rs:176`): underlines first,
  then continuations (`continuation.rs:103`). A section planner slots in as the third
  stage.

**Identity.**

- Highlight block IDs hash PDF path, kind, page label, and normalized quote text. The
  doc states plainly: "Highlight comments are not part of the hash"
  (`docs/highlights-ref-sync.md`, Generated Body Contract).
- Standalone-note IDs hash the note's own text (`annotation_block_id`,
  `sidecar_render.rs:924`). This asymmetry matters for tags.

**Task routes.**

- `split_annotation_task_route_suffix` (`annotation_tasks.rs:198`) removes a strict
  trailing `@name` from a `#task` bullet and routes the task to `~/bob/name.md`.
- A missing note is a hard error (`annotation_tasks.rs:245`): "routed annotation task
  target does not exist … create a root-level note named name.md first".
- Across Bob, `@route` is the destination sigil (`docs/capture.md`, lines 77–154).

**Read-back.**

- `parse_managed_region` (`region.rs:81`) re-parses the rendered region. Every H3 other
  than "Removed highlights" is a page heading (`region.rs:281`). Only `^h-` IDs count as
  blocks (`region.rs:292`).
- It feeds `bob ref show` (`ref_library/show.rs:226`), library counts
  (`ref_library/mod.rs:585`), and rename planning (`rename/plan.rs:2043`).
- The rendered note is therefore the persisted form that every downstream reader
  consumes.

**Mac Refs inspector.**

- `RefsShowResponse` decodes `bob ref show <path> -f json` lossily
  (`RefsCore/RefsInspector.swift:12`).
- `RefsInspectorFeed` is **one flat HIGHLIGHTS stream** with a page-run label rule
  (`RefsInspector.swift:522`, `entries(visible:)` at `:806`). It pages entries through
  `RefsNotesPage`.
- The view draws a caption-weight `HIGHLIGHTS` header, quote cards with a 2 pt yellow
  rule, and pale-yellow note cards (`RefsInspectorView.swift:913`).
- The visual language is set out in `RefsVisualTokens.swift`: yellow means your
  highlights, gold means underline ink, orange means note glyphs.
- The thin-client decision (`decisions:mac-capture-is-a-thin-client`) requires bob to
  supply the structure and the app to present it.

**Obsidian.**

- No `bob-plugins` plugin renders ref-note bodies. Notes rely on native callouts plus
  the vault snippet `~/bob/.obsidian/snippets/ref-highlights.css`, which is enabled in
  `appearance.json`.
- That snippet styles underline emphasis and `<` group seams. The seams use
  `data-callout-metadata` for a small-caps page caption.
- The Reading Board in `bob-ledger-tools` only shows an annotation count.

## Evidence from the vault

All checks below were read-only scans of `~/bob/lib` (178 sidecar files) and `~/bob/ref`.

**Existing usage.**

| Check | Result | Consequence |
| --- | --- | --- |
| User notes whose first line is `# ` (H1 plus space) | **0** | Shipping declarations changes no existing note |
| Notes starting with a hashtag (`#a Yes…`, `#task …`) | several (`chat/tailnet_agent_fleet.md`) | Exported verbatim, so a `# ` line will probably be exported verbatim too (verify, see below) |
| `@word` in comments | `#task … @sase` (a route), `Keep @chat and @agent!` (prose) | `@` is already overloaded, so tags must be strict |
| Root notes in `~/bob/` | 653, including `ideas.md` and `inbox.md` | A section named "Ideas" would collide with a task route |
| Ref notes with annotations | 91 notes, about 467 blocks; 28 notes have 5 or more blocks, 12 have 10 or more | Real but modest demand today; the value grows with long papers and books |

**Quote-boundary patterns.**

| Line after a `>` quote line | Count | What it is |
| --- | --- | --- |
| Blank line | 332 | Normal end of a quote |
| Non-blank, non-`>` line | 787 | Hard-wrap continuation lines (linked style) |
| …of those, starting with `#` | **2** | Highlighted code, not user notes (see below) |
| …of those, a list item | 0 | No comment ever directly follows a quote line |
| User comments after a blank line | 161 | The blank line is the reliable comment boundary |

**The two `#` cases are an existing bug and a trap for this feature.**

- `~/bob/lib/docs/gastown_readme.textbundle/text.markdown:155` contains
  `# Set default agent` inside a hard-wrapped quote.
- `~/bob/ref/docs/gastown_readme.md:79–81` shows the result: the quote loses that line,
  and the rest renders as `Comment gt config default-agent > claude-glm`.
- `chat/sase_listen_antennapod_setup.md:63` contains `# should start with <?xml`, and
  its ref note shows `Comment > … <rss`.

Highlighted words disappear and quote text masquerades as your comment. A naive section
grammar would also turn both lines into section declarations. I filed this as task bead
**`bob-cli-ba`** (bug, medium, ready). The fix is to treat a `#`-led line that directly
follows a quote line as quote text, and to start the comment side only after a blank
line. The same rule protects section declarations.

**Unverified assumption: run this test first.** Nothing I found states how Highlights
exports a note whose first line is `# Methods`.

- The Highlights FAQ confirms per-annotation tags on macOS, written in comments as
  `#tag` (its examples: `#review`, `#important-citation`). The changelog confirms that
  exports use `####` category and annotation headers.
- `#a` survives the export verbatim, so `# ` very likely does too.
- The test takes two minutes on the Mac: add a sticky note `# Test section`, add a
  highlight comment `@test-section`, add a highlight comment `# Other\n\nA description`,
  then read the sidecar.
- Also check whether the export wraps notes in `- ` list items, whether smart
  punctuation touches anything, and whether the iPad and iPhone keyboards autocapitalize
  `@Test`.

## Prior art

- **Readwise heading action tags.** A highlight whose note is `.h1`, `.h2`, or `.h3`
  becomes a heading. A line break after the tag adds a description: "simply add a line
  break after the action tag… `.h1 ⏎ This section is about how Topic A relates to Topic
  X.`" The heading text is always the highlighted text: "The heading action tag will not
  work properly unless you highlight the text that is the section title."
- **Readwise membership is positional.** Readwise does not let you assign highlights to
  a heading by name. "You must add heading tags in order, as you read," for some
  sources.
- **Readwise inline tags.** You "start any note with a `.` and follow it with a single
  word," and can put several on one line (`.prob .puzzling`). The `.c1`/`.c2`
  concatenation tags were the prior art for `<`.
  ([action tags](https://docs.readwise.io/readwise/guides/action-tags),
  [Reader FAQ](https://docs.readwise.io/reader/docs/faqs/action-tags),
  [chapters blog](https://blog.readwise.io/add-chapters-to-highlights/),
  [tagging blog](https://blog.readwise.io/tag-your-highlights-while-you-read/))
- **Highlights itself.** It can name color categories and group its notes by color ("The
  annotations in your notes are now grouped by color"). It recognizes per-annotation
  `#tags` on macOS, and its exports use `####` category headers. It has no
  section/outline grouping in exports and no annotation-to-annotation links.
  ([color categories](https://highlightsapp.net/how-to/mac/sort-pdf-annotations-using-color-categories/),
  [FAQ](https://highlightsapp.net/faq/), [changelog](https://highlightsapp.net/changelog/))
- **Zotero Integration templates for Obsidian.** Community templates group annotations by
  color under custom headings, and change `groupby("color")` to group by tag instead. Users
  report heading duplication on re-import. Bob's regenerate-the-region model avoids that
  problem.
  ([forum thread](https://forum.obsidian.md/t/zotero-integration-import-templates/36310))

So your design is **membership by name**. It is more expressive than Readwise's
positional headings, because a section can gather highlights from anywhere in the
document. It is also more local than Highlights' global color categories. That is the
right call for thematic synthesis. It just needs tighter grammar than "contains".

## Is this a good idea?

**Yes, with a smaller, stricter v1 than the spec implies.**

**Why it is right:**

1. **Right layer.** `bob ref` already owns a deterministic projection: sidecar in,
   managed region out. Underline emphasis and `<` continuations proved that the pattern
   is stateless, reversible, and safe for identity. Sections are the same kind of
   fold.
2. **Right moment.** You decide "this belongs with Methods" while reading, inside
   Highlights, where the context is. No second pass in Obsidian is needed, and any edit
   in Obsidian would be overwritten anyway.
3. **It unlocks reuse.** A section as a heading can be embedded elsewhere:
   `![[ref/papers/foo#Open questions]]` inside a project note is a live view of your
   curated subset of a paper. That alone justifies headings over any container
   construct.
4. **It turns a page dump into a synthesis.** Long refs currently read as "Page 1, Page
   2, …". Sections let the note open with your structure.

**What would make it a bad idea:**

- **A loose trigger.** "Contains `@name`" would capture prose (`@chat`), task routes
  (`@sase`), and anything that merely looks like a mention.
- **Silent failures.** A typo in `@methds` leaves an annotation quietly in the wrong
  place.
- **Churn.** If adding a tag re-minted IDs or tombstoned blocks, every reorganization
  would break 🔖 task links.
- **A format break.** Changing how every existing note renders, or emitting Markdown
  that the region parser, `bob ref show`, rename, and library counts cannot read back.
- **Over-reach.** Shipping nesting, multi-membership, and positional scoping in v1 would
  triple the grammar before any real use.

**Honest cost.** Every fold adds grammar to learn. Today zero notes use declarations,
and only about 12 notes are long enough to clearly benefit. The design below keeps the
gesture small (one `#` line, one `@tag`) and makes non-use free, because output without
sections stays byte-identical.

## Requirement adjustments

Each adjustment changes or sharpens your spec. Each one is called out with the reason.

| # | Your spec | Adjusted | Why |
| --- | --- | --- | --- |
| A1 | `@<name>` matches the section | `@key`, where the key is the title folded to lowercase letters and digits (`@open-questions`, `@open_questions`, `@OpenQuestions` all match "Open questions"). A declaration may add short aliases on its heading line: `# Open questions @q` | Names contain spaces and `@` tokens cannot. Autocapitalization on iPad turns `@test` into `@Test`. Aliases make repeated tagging cheap and let you rename a title without retagging |
| A2 | Any note that **contains** `@name` | Only at a **tag position**: the run of `@tags` at the start of any line (after one list marker) or at the end of any line. Mid-sentence `@word` stays prose | Your real comments use `@chat`/`@agent` as prose. Tags sit where people type tags |
| A3 | (implicit) | Only names **declared in the same PDF** count. Unknown tags stay literal text, with a dry-run "did you mean" | Without declarations as an allowlist, every `@word` is a false positive |
| A4 | (silent) | On a `#task` bullet, a trailing `@name` **routes** when `~/bob/name.md` exists. Otherwise it joins the declared section. Dry run flags any route that shadows a section | Preserves every existing route, and turns today's hard "target does not exist" PDF failure into the intended meaning. Membership has an unambiguous alternative spelling (a tag on its own line); routing has none |
| A5 | One or more annotations per section | Each block has **one home**: the first matching tag wins. Extra tags stay visible and are reported | Each `^h-` block ID must stay unique, so a block can't be rendered twice. Embedding a block into a second section (`![[#^h-…]]`) is a clean v2 if you need it |
| A6 | `# <name>` is "a section annotation" | The note's **first non-empty line** must be `# Title` (one `#`, then a space). That holds for a sticky note or for a highlight's or image's note. In linked sidecars, the line must not directly continue a quote. Text on later lines (blank line optional) is the description | Two real quote lines start with `# `. A declaring highlight should still keep its quote, the way Readwise heading highlights do |
| A7 | (unspecified) | Sections render **first**, in declaration order, then `### Other highlights` by page. Pages become `####` only in notes that have sections | Curated structure leads. Notes without sections are byte-identical, so nothing churns |
| A8 | "Persist this grouping" | **Persist nothing new.** The annotations are the truth, and the rendered region encodes the grouping in a structure the region parser reads back. `bob ref show` JSON exposes it additively | This mirrors `<` and underline folds. Writing to the PDF would bring back every coordinated-write risk (`decisions:open-pdf-writes-are-coordinated`) |
| A9 | (unspecified) | Toggling membership never changes `^h-` IDs or re-creates tasks | Your reorganizations must never break 🔖 links, Task Links, or `[h::]` dedup |

Deferred on purpose, and not in v1:

- Nested sections (`##`).
- Multiple homes per block.
- Several declarations in one sticky note.
- Positional "chapter" scoping.
- Automatic grouping by the PDF outline.

## Design

### Grammar: declaring a section

A note declares a section when its first non-empty line, after an optional `Comment:` or
`Note:` label and at most one `- `/`* `/`+ ` list marker, is:

```text
# <Title> [@alias ...]
```

- **Title.** The text after `# `, trimmed. A title of `#` alone, or an empty title,
  declares nothing.
- **Aliases.** Trailing `@alias` tokens on the heading line, with the same token
  grammar as tags. They add match keys and are stripped from the title.
- **Description.** Every later line, blank lines trimmed at both ends. It is beautified
  like any note (reflowed, ligatures normalized), may hold `#task` bullets (imported
  normally), and may hold an image-note path (the image renders on the section card).
- **Where it can appear.**
  - A **sticky note**, which becomes the section card itself.
  - A **text highlight's note**: the highlight keeps its quote and joins the section
    as a member.
  - A **TextBundle image selection's caption**: the image joins as a member.
- **Never a declaration:**
  - A `<` continuation note.
  - A line that hard-wraps a quote (no blank line before it, in linked style).
  - Any `#` line that is not the note's first line.
  - `##`-level and deeper lines. In v1 these are kept as literal text, escaped as `\#`
    so they do not render as giant headings inside a Comment callout. Today they are
    silently deleted.
- **Keys.** Lowercase the title, keep Unicode letters and digits, and drop everything
  else (emoji, spaces, punctuation). `# 🧪 Open Questions!` therefore has key
  `openquestions`. The canonical key is the first alias if one exists, otherwise the
  title key. The section's block ID `^s-<slug>` comes from the canonical key: ASCII
  words joined with `-`, or `s-<hash8>` when the name is not ASCII.
- **Duplicate keys.** Two declarations that share a key merge into one section. The
  first declaration supplies the title and description, and a diagnostic reports the
  merge.
- **Reserved titles.** "Other highlights" and "Removed highlights" are reserved, and
  such a declaration is reported and ignored.
- **Order.** Sections appear in the order their declarations appear in the sidecar,
  which is Highlights' sidebar order. **Tip:** stack your declaring sticky notes on page
  1, top to bottom, to get a deliberate outline.
- **Page-heading fix.** Recognize page headings only at the heading level the sidecar
  uses for its first page heading (`####` in every linked export in the vault, `##` in
  the simple shape). An H1 inside a page is never a page break, so `# P values` works.

### Grammar: joining a section

Tags are scanned per line of the effective note: after the `Comment:`/`Note:` label is
stripped and after any `<` marker is removed. A `<`, if present, must come first.

- **Token.** `@` followed by a letter or digit, then letters, digits, `_`, or `-`. One
  trailing `.`, `,`, `;`, `:`, `!`, `?`, or `)` is tolerated and kept.
- **Tag positions.**
  - The leading run of tokens on a line (after one list marker). `@methods Nice point`
    and `- @methods #task Re-check` both qualify.
  - The trailing run on a line. `Nice point @methods` qualifies.
  - A line made only of tags. `@methods`, alone or several, qualifies.
- **Match.** A token joins a section only when its key equals a declared key or alias in
  **this** PDF.
- **Consumption.** A matched tag is removed from the rendered comment, whitespace is
  collapsed, and a line left empty is dropped. Unmatched tokens and mid-line tokens are
  left untouched.
- **Task lines.** A trailing token on a `#task` bullet is resolved by A4. A route wins
  if `~/bob/<name>.md` exists. Otherwise a declared section takes the token, and the
  task files to its default destination. Otherwise the existing route error applies.
  The task identity already excludes the suffix, so `[h::]` dedup is unchanged.
- **Kinds that can join:** text highlights, standalone underlines, absorbed underlines
  (by way of their host), image selections, and sticky notes.
- **Kinds that cannot join:** declarations do not join other sections. The page-1
  marker never joins.

Two rules to remember, mirroring the `<` docs:

- **A `# ` first line starts a section; whatever follows describes it.**
- **If you still see an `@name`, it did not join a section.**

| Note on an annotation | Result |
| --- | --- |
| `@methods` | Joins Methods; no comment rendered |
| `@Methods Compare with table 2` | Joins; comment `Compare with table 2` |
| `Compare with table 2 @methods` | Joins; same comment |
| `- #task Re-run this @methods` (no `methods.md`) | Joins; task imports as `#task Re-run this` |
| `- #task Send to Alice @ideas` (`ideas.md` exists) | Routes to `ideas.md`; does **not** join; dry run warns if "Ideas" is a section |
| `Keep @chat and @agent!` | Prose; nothing joins, even if `# Chat` exists |
| `@methds` | Literal; dry run: `did you mean @methods?` |
| `@methods @results` | Joins Methods; `@results` stays visible; conflict reported |
| `< @methods more` | Continuation follower; the group joins Methods |
| `\@methods` | Literal `@methods`, matching the `\<` escape convention |

### Resolving membership across folds

Sections are planned **after** `plan_annotation_folds`, over rendered blocks rather than
raw annotations:

1. For each rendered block, collect matched tags in member order. A block is a head with
   its followers and absorbed underlines, a sticky note, an image, or a standalone
   underline. Order within a block: the head's tags first, then followers in sidecar
   order, then absorbed underlines in run order.
2. The first match is the block's **home**. The tag that set the home is consumed. Every
   other matched tag stays visible and is reported as `section_conflict`.
3. A declaring highlight is a member of its own section, unless it also carries a
   different tag on a later line (that is a conflict, and its own section wins).
4. Within a section, blocks render in sidecar order, with `####` page headings at each
   page change. Group labels such as `Pages 11–12` are reused unchanged.
5. Blocks with no home render under `### Other highlights` in sidecar order. That
   heading is omitted when every block has a home.

The planner is pure and deterministic, and it never reads the existing region. That
keeps the property the `<` design depends on: deleting a tag or declaration and
rescanning restores the previous layout exactly.

### Persistence: where the grouping lives

| Option | Verdict |
| --- | --- |
| **Derive on every render from the sidecar; encode in the rendered region; expose via `ref show` JSON** | **Recommended.** One source of truth (your annotations), stateless and reversible, like `<` and underlines |
| Write sections into the PDF (outline bookmarks, `/Subj`, colors) | Rejected. Brings back the coordinated-write risk, causes Highlights reloads and undo resets, and goes beyond the single page-1 marker contract |
| Store membership in the ref note outside the managed region | Rejected. Creates two sources of truth that drift; the region is regenerated anyway |
| Separate sections file (`foo.sections.yml`) or Bob state dir | Rejected. Invisible from Highlights and the iPad, and not synced |
| Declare sections in the page-1 marker list | Rejected. The marker is two-way synced status metadata, and adding keys makes conflict logic harder |
| Derived frontmatter `highlights_sections: [...]`, written only when sections exist | **Optional.** Same class as `highlights_count`. Enables Dataview queries and Mac list search by section; deferred to polish |

Inside the region, the grouping must survive `parse_managed_region` without guessing.
A section is recognized by a **structural signature**, not by heading text:

```text
### <Title>                         ← H3
                                    ← blank
> [!summary|section] …              ← section card (callout metadata "section")
> <description lines>
                                    ← blank
^s-<slug>                           ← section ID (never ^h-)
```

The parser contract becomes:

- **Notes without a section card** parse exactly as today: H3 means page.
- **Notes with sections.**
  - An H3 followed by a section card opens a section.
  - The exact `### Other highlights` opens the unsectioned group.
  - `####` page headings inside either group set `page_label`.
  - `### Removed highlights` is unchanged.
- **Blocks.** Every block gets `section: Option<String>` (the canonical key).
  `RegionParse` gains `sections: Vec<RegionSection { key, title, description, block_id }>`.
- **What is not counted.** `^s-` cards are never counted as annotations, so
  `highlights_count`, the Reading Board's `✎ N`, and library counts keep their
  meaning.

A page-label-looking title such as "Page turners" is safe, because the card, not the
text, marks a section.

### Rendering in Obsidian

A real-shaped example, built from your goals paper. Sidecar fragment:

```md
#### [Page 1](highlights://goals#page=1)

##### 2026-10-24:

# Ideas for sase @idea

Things from this paper I want to build into sase goals.

***

##### 2026-10-24:

> We argue that goals should be encoded as first-class abstractions that drive human-AI collaborative workflows

@idea

***

#### [Page 2](highlights://goals#page=2)

##### 2026-10-24:

> Goals enable flexible coordination: shared goals let collaborators, human or AI, interpret and infer others’ behaviour …

- #task Planner agents should run the `sase goals list` command before planning?! @idea
```

Rendered managed region:

```md
## Highlights

<!-- highlights:begin -->

### Ideas for sase

> [!summary|section] `@idea` · 2 highlights · Pages 1–2
> Things from this paper I want to build into sase goals.

^s-idea

#### Page 1

> [!quote] We argue that goals should be encoded as first-class abstractions that drive human-AI collaborative workflows

^h-f0a3bdf3cd77

#### Page 2

> [!quote] Goals enable flexible coordination: shared goals let collaborators, human or AI, interpret and infer others’ behaviour …
>
> > [!note] Comment #task Planner agents should run the `sase goals list` command before planning?!

^h-a6ecafe42cb7


### Other highlights

#### Page 1

> [!quote] existing ecosystems support goal tracking but not goal articulation, alignment, or contextual use

^h-ec921544b3b2

<!-- highlights:end -->
```

The `^h-` IDs above are the **real current IDs** from
`ref/papers/2026_goals_as_first_class_abstractions_…md`. Comments are not hashed, so
tagging these highlights would leave them unchanged.

**Why this shape:**

- **Headings, not a wrapping callout.**
  - Obsidian folds headings natively.
  - Headings list sections in the Outline pane.
  - Heading links (`[[foo#Ideas for sase]]`) and heading embeds work out of the box.
  - Member markup is unchanged: `^h-` lines stay outside the callouts, as today. A
    wrapping `[!section]` callout would push `<` groups to four `>` levels and put
    block IDs inside blockquotes, which risks 🔖 link resolution.
- **A section card under the heading.**
  - Its title line, `` `@idea` · 2 highlights · Pages 1–2 ``, teaches you the tag to
    type and summarizes the section at a glance.
  - Its body is your description.
  - With no description, the card is a slim title bar.
  - An empty section shows `` `@related` · nothing tagged yet ``, which works as a to-do
    for your own outline.
  - `[!summary]` is a built-in type, so the card looks good without CSS.
  - The `|section` metadata lets CSS restyle the card without touching other `summary`
    callouts in the vault.
- **`####` pages inside groups** keep the "which page?" answer visible in plain
  Obsidian. Page counts reuse the existing range formatter (`Pages 3, 7, 12`).
- **Heading text is sanitized** for Obsidian link safety: `#`, `|`, `^`, `[[`, and `]]`
  are dropped or replaced. Emoji are kept.

**Optional CSS polish,** appended to `ref-highlights.css`. It extends the language the
snippet already speaks: faint small caps for page captions, and quiet rules rather than
boxes. Structure gets a cool purple accent, so your yellow quotes and orange notes stay
the loudest marks on the page:

```css
/* bob ref: a `# name` section opens with a card. Draw it as a quiet,
   purple-ruled header, not a boxed callout: small-caps meta line (the @tag,
   counts, pages), then your description in normal ink. Yellow quotes and
   orange notes stay the loudest things on the page. */
.callout[data-callout="summary"][data-callout-metadata="section"] {
  --callout-color: var(--color-purple-rgb);
  margin: -0.35em 0 1.1em;
  padding: 0.1em 0 0.1em 0.85em;
  border: 0;
  border-left: 3px solid rgba(var(--callout-color), 0.55);
  border-radius: 0;
  background: transparent;
}
.callout[data-callout-metadata="section"] > .callout-title {
  gap: 0;
  font-size: var(--font-smallest);
  font-variant: all-small-caps;
  letter-spacing: 0.06em;
  color: var(--text-faint);
}
.callout[data-callout-metadata="section"] > .callout-title .callout-icon {
  display: none;
}
.callout[data-callout-metadata="section"] > .callout-content {
  color: var(--text-muted);
}
```

To make the `####` page headings look like the existing faint small-caps captions,
Obsidian needs a note-level class. bob could add a managed `cssclasses: [bob-ref]` to
notes that have sections, which enables `.bob-ref h4 {…}` in both views. I'd defer
this: plain `####` already reads fine, and a new managed frontmatter key needs its own
merge rules for user-set classes.

### Rendering in the Mac Refs panel

The app stays a thin client. bob adds the following to each `ref show` row, additively
and with `schema_version` unchanged at 1 (the same precedent as `pieces` for `<`
groups):

```json
"sections": [
  {
    "key": "idea",
    "title": "Ideas for sase",
    "aliases": ["idea", "ideasforsase"],
    "description": "Things from this paper I want to build into sase goals.",
    "block_id": "s-idea",
    "link": "[[ref/papers/foo#^s-idea]]",
    "count": 2,
    "pages": "Pages 1–2"
  }
],
"annotations": [ { "...": "...", "section": "idea" } ]
```

`annotations` stay in note order, with sectioned blocks first. The app decodes both
fields with `decodeIfPresent`, so an older `bob` simply shows today's flat feed.

**`RefsInspectorFeed`.**

- Projects `Entry` values plus `SectionHeader` rows: header, then members, for each
  section; then an "Other highlights" header if any entries lack a section.
- Resets the page-run rule at every header, so the first member of a section always
  shows its page.
- Pagination still counts annotation entries only. A header appears only when its first
  member is visible, so a header is never orphaned.
- The disclosure text gains a clause, for example `Show 8 more · 2 sections`.

**Section header view.** Purple marks structure; yellow and orange keep their meaning:

```text
HIGHLIGHTS 22  ✎ 9
▍Ideas for sase                                  @idea · 2
▍Things from this paper I want to build into
▍sase goals.
   Page 1
   ┃ We argue that goals should be encoded as first-class…
   Page 2
   ┃ Goals enable flexible coordination: shared goals let…
   ╭──────────────────────────────────────────────────╮
   │ ✎ #task Planner agents should run sase goals…    │
   ╰──────────────────────────────────────────────────╯
OTHER HIGHLIGHTS 20
   Page 1
   ┃ existing ecosystems support goal tracking but not…
```

- **Header row.** A 3 pt rounded purple bar (`Color.purple`, about 0.6 opacity; full
  opacity under Increase Contrast). The title in `.subheadline.weight(.semibold)`. On
  the right, `@idea · 2` in `.caption2.monospacedDigit()` tertiary.
- **Description.** `.callout` in secondary color, three lines in compact layout and five
  in wide, under the same bar.
- **Spacing.** A new `inspectorSectionGap` token, about 14 pt, sits above each header.
  Members keep today's exact quote and note-card views.
- **"Other highlights" header.** Reuses the existing caption-weight `sectionLabel`
  style, so the hierarchy reads HIGHLIGHTS → section → page.
- **VoiceOver.** A header is `.isHeader`, with the label "Section Ideas for sase, 2
  highlights. Things from this paper…".
- **Copy card.** "A" (all notes) emits `### <Title>` groups in the same order. The H
  picker shows section names as group labels. A later `G` key could copy one section's
  Markdown or its `[[…#^s-…]]` link; `G` is free in `RefsCopyKey`.

### Other viewers

| Surface | Change |
| --- | --- |
| `bob ref show` (human) | A bold section title, a dim description, and the `@key` and count on the same line; members indented under it; then `Other highlights` |
| `bob ref show -f markdown` (agent digests, the `bob_ref` skill) | `### Annotations` → `#### <Title>` with the description as a blockquote, then page labels → `#### Other highlights`. Agents see your synthesis directly |
| `bob ref show -f json` | `sections` plus `annotations[].section`, as above |
| Library index and counts (`ref list`, Reading Board `✎ N`, `doctor`) | Unchanged meaning; section cards are not annotations |
| `bob ref rename` | Rewrites `[[old#^s-…]]` and `[[old#Title]]` links like any other link to the note; test that `^s-` IDs survive |
| Snapshotting a ref note into a PDF (`bob ref create` on a vault note) | Headings become PDF outline bookmarks for free |
| qmd and agent vault search | Headings improve chunking and retrieval with no extra work |
| Highlights sidebar | Unchanged. The grouping exists only in bob views. You still see `# Title` and `@tag` text in Highlights, which is fine because they are what you typed |

### Identity, tasks, and tombstones

- **Highlights, underlines, groups, and images.** No change: comments and captions are
  outside the hash.
- **Sticky notes.** Their ID hashes their text, so consumed tags must be removed from
  the identity text. The ID planner (`plan_block_ids`) also gets one reuse rule: an
  existing live ID equal to the raw-text ID maps to the new block. Tagging or untagging a
  sticky note then never re-mints or tombstones it.
- **Declaring sticky notes** produce a section card, not an annotation block.
  - Their `#task` bullets keep a per-annotation `[h::]` processed ID, computed from the
    would-be `^h-` ID exactly as continuation followers do.
  - New tasks link 🔖 to `#^s-<slug>`.
  - Converting an existing sticky note into a declaration: the vault has zero such notes
    today. In general, a previously published ID gets a redirect stub, on the same rule
    as `Merged emphasis`. A stub is written only when that ID was already listed as
    removed or is linked from vault Markdown.
- **Removed or renamed sections.**
  - Members fall back to "Other highlights" with their `@tags` visible again
    (self-diagnosing), and the dry run lists them.
  - A vanished `^s-` ID gets a `[!info] Removed section` stub only when vault Markdown
    links to it. That avoids a noisy tombstone for every experiment.
  - To rename a title without retagging, keep the old key as an alias:
    `# Methodology @methods`.
- **Task routing** follows A4. Existing routed tasks are never re-created, because the
  task identity has always excluded the suffix.

### Diagnostics

The naming follows the existing `continuation_dangling` and `underline_standalone`
style.

- **`bob ref sync <pdf> --dry-run`** prints the following:
  - `sections: 2 (idea 2, open-questions 0)`
  - `section_tag_unknown: Page 4 @methds (did you mean @methods?)`, for tag-position
    tokens within edit distance 2 of a key, or any unknown tag in a PDF that declares
    sections.
  - `section_conflict: Page 7 tagged @methods, @results (kept @methods)`
  - `section_tag_is_route: Page 3 @ideas routes the task to ideas.md; put @ideas on its own line to join "Ideas"`
  - `section_duplicate: "Open Questions" (Page 9) merged into "Open questions" (Page 2)`
  - `section_reserved_title: "Other highlights" (Page 1) ignored`
- **Concise `bob ref scan`** adds `2 sections` and `1 unknown section tag` after the
  continuation details.
- **Scan JSON** adds `notes[].sections`, `notes[].sectioned`, and
  `notes[].section_tags_unknown`, each only when non-zero. `schema_version` stays 1.

## Alternatives considered

| Alternative | Verdict |
| --- | --- |
| **Positional "chapters"** (Readwise `.h1`: everything after a heading until the next one belongs to it) | Rejected for v1. It is cheap to type, but it can't build thematic, cross-page groups. Membership shifts when you add an annotation in between, and it depends on sidecar order, which a color sort breaks. Fine as a later, separate gesture if you want document structure |
| **Automatic grouping by the PDF outline** (bob-created PDFs already carry pandoc outline bookmarks) | Worth a separate feature ("group by chapter"). It needs no typing, but it answers a different question, document structure rather than your synthesis |
| **Highlights color categories as sections** | Rejected. Colors are global, not per document, and capped at a handful. Colors are not reliably in the sidecar, color-sorted exports break `<`, and categories leave no room for descriptions |
| **Highlights `#hashtags` instead of `@`** | Rejected. `#task` and `#a` already carry meaning in bob. `#methods` beside `# Methods` invites mistakes. Native tag filtering needs Split files and is not confirmed for the sidebar |
| **A different sigil (`§`, `.`, `^`)** | Rejected. `§` is hard to type on iPad. `.tag` is Readwise's convention but reads like a typo in prose. `@` already means "where this goes" across Bob, which is the same mental model as "put this highlight in that section"; A4 resolves the one real overlap |
| **A wrapping `[!section]` callout** (collapsible) | Rejected. Nesting depth, block IDs inside blockquotes, no heading links or embeds, and no Outline entry |
| **Sections "in place"** at the declaration's position in the page flow | Rejected. Thematic members come from anywhere, so page-9 highlights would sit inside the page-3 flow under confusing headings |
| **Prefix matching for tags** (`@meth` → `methods`) | Rejected. Adding a section later could silently re-home annotations. Aliases are explicit and stable |

## Risks and costs

- **Region-format skew.**
  - An older `bob` reading a sectioned note sees H3 titles as page labels. Its card and
    `####` lines fall into `unparsed`, so `ref show` reports `annotations_status:
    unparsed`.
  - This degrades but does not corrupt, and the daily release train keeps hosts within
    a day of each other.
  - Only notes that declare sections are affected.
- **Grammar surface.** Two more rules in a contract that already has continuations,
  underlines, image notes, and routes. The two rules of thumb and the "visible tag"
  convention keep it learnable.
- **Highlights export assumption.** Unverified until the two-minute Mac test passes.
- **Bug coupling.** `bob-cli-ba` should land first, or with phase 1. Its fix changes
  the quote text of two highlights and re-mints their IDs once. That is a separate,
  explicitly accepted cost.
- **Mac work is gated by macOS CI.** Per `bob-mac-capture/AGENTS.md`, agent hosts
  without Swift must compile on the Mac or athena.
- **Decision record.** On landing, record a `decisions:` strand covering name-keyed
  membership, tag positions, route precedence, and "persist nothing new", written through
  `/sase_memory_write`.

## Recommended solution

Ship **name-keyed section folds**, rendered as headings, in three phases.

**Phase 0: verify and fix (small).**

- Run the two-minute Highlights export test on the Mac. Repeat on iPad if you annotate
  there.
- Land `bob-cli-ba`: a `#`-led line that directly follows a quote line continues the
  quote, and the comment side starts after a blank line.
- Make page-heading detection level-aware, so an H1 is never a page break.

**Phase 1: bob-cli (medium to large; one epic phase or two).**

1. **Parser** (`sidecar.rs`): keep a first-line `# ` in notes as content, flagged as a
   candidate declaration. Keep `##`+ lines as escaped text instead of deleting them.
2. **Planner** (new `sections.rs`, beside `continuation.rs`):
   - `scan_section_declaration`, `scan_section_tags`, and
     `plan_sections(annotations, &folds) -> SectionPlan` (sections, `home_of`,
     consumed tokens, diagnostics), run after `plan_annotation_folds`.
3. **Renderer** (`sidecar_render.rs`):
   - With no sections, run the current path unchanged.
   - With sections: H3 section, `[!summary|section]` card, `^s-<slug>`, `####` pages,
     then `### Other highlights`, then `### Removed highlights`. Consumed tags are
     stripped from the rendered comments.
4. **Identity**: strip consumed tags from sticky-note identity, add the raw-text reuse
   rule, and keep processed `[h::]` IDs for declaration tasks.
5. **Tasks** (`annotation_tasks.rs`): A4 precedence. A route wins only when the root
   note exists.
6. **Region parser** (`region.rs`):
   - Detect sections by structural signature.
   - Add `RegionBlock.section` and `RegionParse.sections`.
   - Do not count `^s-` cards.
7. **`bob ref show`**:
   - JSON `sections` and `annotations[].section`.
   - Grouped human and Markdown output.
8. **Reports**: dry-run, concise, and JSON diagnostics as listed above.
9. **Docs**: a new "Sections (`#` and `@`)" subsection in
   `docs/highlights-ref-sync.md`, with the two rules of thumb, the behavior table, and
   the CSS. Update the vault snippet `ref-highlights.css`.
10. **Tests**:
    - Fixtures for linked and simple sidecars.
    - Regressions for the gastown and antennapod quotes, `# P values`, and
      `#task … @ideas` with `ideas.md` present.
    - Identity stability: toggling tags yields the same IDs and no tombstones.
    - The whole current fixture corpus stays byte-identical.
    - Region round-trip and JSON shape.
    - A vault-wide `bob ref scan --dry-run` that shows zero note changes before any
      declaration exists.

**Phase 2: Bob Mac Capture (medium).**

- Decode `sections` and `section`.
- Add sectioned `RefsInspectorFeed` projection and a header view: purple bar, title,
  `@key · N`, description.
- Reset the page-run rule per section, and add the pagination clause and VoiceOver
  labels.
- Group the Copy card's "A" output by section, and label sections in the H picker.

**Phase 3: optional polish, only after real use.**

- A `G` section picker in the Copy card.
- Section jump chips at the top of HIGHLIGHTS.
- Derived `highlights_sections` frontmatter for Dataview and list search.
- `cssclasses` for small-caps `####` page captions.
- Multiple homes via same-note block embeds.
- Several declarations in one outline sticky note.
- A separate "chapters from PDF outline" view.

That keeps your gesture exactly as you imagined it: `# Name` on a note, `@name` on the
things that belong there. Beyond that it adds only what keeps it reliable: declared names,
tag positions, one home per block, and route precedence. It adds nothing that makes
non-use cost anything.

## Sources

- bob-cli (this workspace, `30f10f15`): `docs/highlights-ref-sync.md` (Generated Body
  Contract, Continuation highlights, Underline emphasis, Tasks);
  `src/native/highlights_ref/{sidecar.rs, sidecar_render.rs, continuation.rs,
  underline.rs, region.rs, annotation_tasks.rs, mod.rs}`;
  `src/native/ref_library/{show.rs, mod.rs}`; `docs/capture.md`.
- bob-mac-capture (linked checkout): `Sources/RefsCore/RefsInspector.swift`,
  `Sources/BobMacCapture/Refs/RefsInspectorView.swift`,
  `Sources/BobMacCapture/Refs/RefsVisualTokens.swift`, `Sources/RefsCore/RefsCopy.swift`,
  `AGENTS.md`.
- bob-plugins (linked checkout): `docs/highlights.md`,
  `plugins/bob-ledger-tools/src/243-plugin-reading-board-render.js`.
- Vault (read-only): `~/bob/lib/**` sidecars, `~/bob/ref/**` notes,
  `~/bob/.obsidian/snippets/ref-highlights.css`, `~/bob/.obsidian/appearance.json`.
- Memory: `decisions:mac-capture-is-a-thin-client`,
  `decisions:open-pdf-writes-are-coordinated`, `glossary:reference-note`, `obsidian.md`.
- Prior research (unrelated swarm):
  `research:202610/highlight_continuation_marker/highlight_continuation_marker.md`.
- Filed during this research: task bead `bob-cli-ba` (bug).
- Web: [Readwise action tags](https://docs.readwise.io/readwise/guides/action-tags) ·
  [Readwise Reader action-tag FAQ](https://docs.readwise.io/reader/docs/faqs/action-tags) ·
  [Readwise: add chapters to highlights](https://blog.readwise.io/add-chapters-to-highlights/) ·
  [Readwise: tag your highlights while you read](https://blog.readwise.io/tag-your-highlights-while-you-read/) ·
  [Highlights FAQ](https://highlightsapp.net/faq/) ·
  [Highlights color categories](https://highlightsapp.net/how-to/mac/sort-pdf-annotations-using-color-categories/) ·
  [Highlights changelog](https://highlightsapp.net/changelog/) ·
  [Highlights features](https://highlightsapp.net/features) ·
  [Obsidian forum: Zotero Integration templates](https://forum.obsidian.md/t/zotero-integration-import-templates/36310).
