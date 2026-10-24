# Section annotations: thematic grouping for ref notes

- **Researcher:** grk
- **Date:** 2026-10-24
- **Question:** Should `bob ref` group Highlights annotations under a "section annotation" of the form `# <name>` (optional description after a blank line), with membership via `@<name>` on highlight / underline / standalone notes? How should that grouping persist and render so it is intuitive in Highlights, reliable across sync, and beautiful in Obsidian and the Bob Mac Capture ref panel?
- **Verdict:** Yes — this is a good idea, and the vault is already asking for it. Implement it as a third **render-time grouping pass** next to `<` continuations and underline emphasis. Keep the source of truth in the PDF notes Bryan types while reading. Do **not** wrap members into one merged callout, do **not** tombstone them, and do **not** let the Mac app parse `#` / `@`. Fix two parser collisions first or the feature will silently no-op. Keep `# <name>` (space required) for the definition; keep `@<slug>` for membership, scanned in comments only.

Peer swarm reports were not consulted.

---

## 1. In one breath

Page order is the only axis ref notes have. A 16-page blog with 23 highlights, or a draft whose comments say "put this in the memory section" / "add this to intro", is already a thematic document trapped in spatial order.

Bryan's proposed gesture is the right *layer*: a sticky note that names a bucket, and a cheap tag on the members. It matches how `<` and image-note paths already work — typed in Highlights, interpreted by `bob ref`, projected into the managed region, never written back to the sidecar.

The raw spelling needs three corrections or it will fail in the current pipeline:

1. **`# Architecture` is an ATX heading.** The sidecar parser drops heading-only chunks and strips heading lines out of comments. A section sticky whose entire text is `# Architecture` can vanish before grouping ever runs.
2. **`#a` and `#task` already live in highlight comments.** The space after `#` is load-bearing: it is what keeps this grammar from eating Bryan's editorial prefix and the task importer.
3. **`@name` in a quoted PDF sentence is not membership.** Scan comments / standalone-note bodies / image captions. Leave the author's words alone.

Persist grouping the same way `<` does: as text in the PDF annotation, projected at scan time. Render it as **sibling cards under a section heading**, not as a fourth nested callout. Reordering distinct annotations is already a documented identity property (`docs/reference/vault-format.md`). Absorbing them is not.

---

## 2. Is this a good idea?

**Yes.** Four facts make it cheap, and one fact makes the alternative expensive.

### 2.1 The vault is already writing section membership in prose

`bob ref show -c` on recent, heavily annotated notes (2026-10-24):

| Note | Ann. | Comments | What the comments are doing |
| --- | ---: | ---: | --- |
| `ref/docs/sase_AGENTS_v2.md` | 14 | 14 | `#a` editorial notes and `#task` lines, already a classified comment vocabulary |
| `ref/notes/sase_blog_261019.md` | 17 | 17 | "reference this from the section where I talk about types of AI debt", "mention this when you mention memory", "include this in the memory section", "figure out where" |
| `ref/chat/sase_launch_post_outline.md` | 17 | 17 | "Add this to intro", "I like 'Why a TUI?' in this section", "Mention artifact sidecar repos…" |
| `ref/papers/2026_goals_as_first_class_abstractions_….md` | 13 | 13 | Tasks and reactions, mixed themes on adjacent pages |
| `ref/blogs/solving_code_review_at_anthropic.md` | 23 | 6 | Long page-order reading; one comment, several `<` groups, several images |

The blog/outline notes are the product. Bryan is classifying highlights by *destination section of a document he is writing*, which is not a PDF page and not a PDF outline bookmark. `@memory` is the structured form of a sentence he is already typing.

Most of the library does not need this. In a 200-row slice of finished refs, median annotation count is 0; only 7 notes have ≥10 annotations. That is an argument for **opt-in, zero churn**: notes with no section sticky keep today's `### Page N` body byte-for-byte.

### 2.2 Bob already owns this kind of feature

Three grouping passes already sit in `src/native/highlights_ref/`:

| Pass | Gesture | Effect on identity |
| --- | --- | --- |
| Continuation (`continuation.rs`) | note starts with `<` | Several highlights become **one** `^h-` card; published followers get a redirect stub |
| Underline emphasis (`underline.rs`) | fully-`**`-wrapped quote contained in a same-page highlight | Underline **nests** into the host; host `^h-` unchanged; stub only if linked |
| **Sections (proposed)** | sticky `# Name`, members `@slug` | Cards **move** under a heading; every `^h-` stays; **no stub** |

Vault-format already says: "Reordering distinct exported annotations preserves those IDs." Section grouping is a reorder. It is not a merge. Treating it like `<` (one card, absorbed ids) would be the wrong reading of the gesture: Architecture is a *folder*, not a *sentence that spanned a page break*.

Mac Capture is a thin client of `bob` (`decisions:mac-capture-is-a-thin-client`). The inspector hydrates from `bob ref show <path> -f json` (`RefsShowResponse`, schema 1) and already ignores unknown keys. Grouping belongs in `bob ref`. The Mac app draws a header when a `sections` array is present.

### 2.3 Highlights will not grow this for us

Official extraction rules ([How to Extract PDF Annotations](https://highlightsapp.net/how-to/iphone/extract-pdf-annotations/)):

| PDF markup | Sidecar |
| --- | --- |
| Highlight | `> quote` |
| Underline | `> **quote**` |
| Strikethrough | `> ~~quote~~` |
| Comment | plain text under the quote |
| Sticky note | plain text, ordered by page position |
| Image selection | image + caption |

The app also has **color categories**, **`#hashtags` in comments** (changelog, iOS 2021.1.1), and optional annotation headers (page / category / color / date). None of those is a named, non-contiguous folder in the markdown bob sees. Color-sorting the sidecar is already documented as unsupported: it would break `<`'s "previous text highlight" walk. Waiting on Highlights folders would stall a gesture Bryan can type today.

### 2.4 What would make it a bad idea

- Shipping `# Architecture` without fixing the heading strip, so section stickies disappear.
- Treating `#a` / `#task` / `#hide` as section names.
- Scanning `@name` inside quoted PDF text (emails, Twitter handles, code).
- Wrapping every member in a foldable `[!section]` callout (fourth nesting level on a `<` group that already has a Comment card; existing `ref-highlights` nested-quote CSS would fight it; `^h-` lines get harder to reason about).
- Putting a markdown parser in Bob Mac Capture.
- Auto-grouping "everything after this sticky until the next" in v1 (a Related-Work paragraph sitting between two stickies becomes Architecture).
- Silently rewriting the sidecar or the PDF.

The design below closes those.

---

## 3. Critique of the plan as stated

The request: a section annotation of the form `# <name>`, optional description after a blank line; any highlight note / underline note / standalone note that contains `@<name>` renders under a visually appealing section; pleasant in Obsidian, the Mac ref panel, and anywhere else ref notes are viewed; lead the design; intuitive, reliable, beautiful.

### What to keep

- **Opt-in, typed in Highlights, while reading.** Same philosophy as `<`, `#task`, and pasted screenshot paths. Zero extra UI.
- **A named bucket plus cheap membership**, so grouping is non-contiguous. Page 3 and page 15 can both be Architecture.
- **Beauty as a requirement**, on both surfaces, not "Obsidian-only CSS" or "inspector-only chrome".
- **One feature across every reader of the generated note:** Obsidian, `bob ref show` human/markdown/JSON, the Mac inspector, Copy-card payloads, agent `-c -f markdown`.

### What to change

These are explicit requirement adjustments. They are justified below; the recommended grammar and render follow from them.

**A1. Membership is scanned in the user's words, never in the quote. (reliability)**

"Contains `@<name>`" as written would match a highlight of an email or a `@objc` snippet. The membership token lives in `task_source` / standalone-note text / image caption — the same fields `<` and `#task` already read.

**A2. A section definition is a standalone sticky, not a highlight comment. (identity)**

A highlight whose comment is `# Architecture` still has a quote that needs a card. Promoting that highlight to a banner would hide the quote. Only `SidecarAnnotationKind::StandaloneNote` whose first meaningful line matches the section header is a definition. A highlight comment `# Architecture` is ordinary text (and a dry-run hint if a section of that name exists, so Bryan can switch it to `@architecture`).

**A3. The space after `#` is required. `#a` and `#task` stay untouched. (collision)**

Live comments on `sase_AGENTS_v2` already use `#a …` (editorial) and `#task …` (imported). Highlights hashtags are `#tag` with no space. The section header is ATX-shaped: `#` + whitespace + name. That space is the whole discriminator. Do not accept `#architecture` as a definition.

**A4. The membership token is `@<slug>`, a single word. Multi-word titles slugify. (parseability)**

`# Error Handling` as a title is fine. `@Error Handling` in a sentence is not a token. Canonical id is the slug: Unicode NFC, casefold, whitespace → `-`, keep `[a-z0-9-]`. Membership is `@error-handling` (case-insensitive). Display title is the original `#` line, spaces and casing preserved.

**A5. Fix the sidecar parser so a non-page ATX heading in a sticky is content. (the feature exists)**

Today (`parse_sidecar_chunk` in `sidecar.rs`):

- a chunk whose every line is `is_markdown_heading` returns **no annotation**;
- heading lines are filtered out of both comments and standalone notes;
- `##### 2026-06-03:` date headings in the linked-page export rely on that filter.

So this sidecar sticky:

```md
#### [Page 4](highlights://paper#page=4)

##### 2026-06-03:

# Architecture

The locking and ownership story.
```

currently becomes a standalone note whose entire text is `The locking and ownership story.` The name is gone. A name-only sticky `# Architecture` becomes an empty chunk and is dropped.

Simple sidecars that prefix `Note: # Architecture` survive, because that line does not start with `#`. Linked-page export (the shape in `tests/fixtures/highlights_ref/linked_sidecar.md`) does not use that prefix. The parser fix is mandatory for reliability; relying on `Note:` is a coin flip.

Keep dropping: page headings, `##### YYYY-MM-DD:` date headings, document-title preamble. Keep a non-page `# Name` line as the standalone note's first line.

**A6. `parse_managed_region` must distinguish section H3s from page H3s. (round-trip)**

Today every level-3 heading other than `Removed highlights` is a `page_label`. If the generated body uses `### Architecture`, show/JSON would report page "Architecture" and the Mac inspector would print that as a page run. Reuse `is_sidecar_page_label`: `Page 12` / `Pages 11–12` / `p. 4` / `pp. 6–8` stay pages; any other H3 in the region is a section.

**A7. Grouping reorders. It does not merge, fold, or tombstone. (identity)**

Members keep their `^h-` ids, their Comment cards, their image notes, their `#task` imports, their `<` groups, their underline spans. The section sticky's id moves onto the section object (the banner), so a link to that sticky still resolves. No `### Removed highlights` stub — the cards are still published.

**A8. One level. First matching `@` wins. No duplicate cards. (v1 scope)**

An annotation tagged `@architecture @performance` sits in Architecture (first defined-section match in token order). Extra matching tokens are stripped from the displayed comment. Unmatched `@foo` stays visible, like a dangling `<`. Nested sections, "also in Performance" chips, and multi-section clones wait.

**A9. No implicit "everything until the next sticky" in v1. (footgun)**

Linear paper reading wants this. A sticky dropped between two unrelated highlights would steal them. Explicit `@` is more typing and much safer. Revisit implicit capture only after the explicit grammar has been used on real notes.

**A10. Notes with no section definition do not change. (churn)**

The rest of the library keeps `### Page N` and sidecar order. `### Other` appears only when a note has at least one valid section **and** at least one ungrouped member.

**A11. JSON stays schema 1, additive. Mac stays a thin client. (contract)**

Same pattern as `pieces` on continuation groups. `schema_version` remains 1. Old Mac ignores unknown keys and still sees a valid HIGHLIGHTS feed (in the new order, without headers). New Mac draws section headers from `sections`.

**A12. Include image annotations. (completeness)**

The request listed highlight / underline / standalone. Image selections with `@slug` in the caption belong in the same buckets. Underlines already merge into hosts; `@` on an underline comment applies to the host / continuation group.

---

## 4. How grouping and rendering work today

### 4.1 Pipeline

```
PDF + sidecar (Highlights owns these)
        ↓  parse_sidecar_markdown
SidecarAnnotation[]  (Highlight | Image | StandaloneNote)
        ↓  plan_continuations          (<)
        ↓  plan_emphasis_nests         (** underline **)
        ↓  sidecar_render              [!quote] / [!note] / ^h-…
        ↓  managed region in ref/*.md
        ↓  parse_managed_region
bob ref show  →  JSON / human / markdown
        ↓
Bob Mac Capture inspector  (thin client)
Obsidian  (callouts + ref-highlights.css)
```

Bob never creates or mutates sidecars (`docs/highlights-ref-sync.md`, Known TextBundle bug). Marker write-back is a separate opt-in. Section grouping must be a plan + render pass, like the two that already exist.

### 4.2 Generated body

Live blocks:

```md
### Page 12

> [!quote] Latency is not throughput.
>
> > [!note] Comment Compare this with SLO notes.

^h-2b91f0a4c7de

> [!note] Keep this standalone observation.

^h-8f42a61a90cc
```

Continuation groups already move the page into callout metadata and nest followers:

```md
### Pages 11–12

> [!quote|Page 11] PR Sheriff Standing Orders. On every
>
> > [!quote|Page 12] session startup, the sheriff checks open PRs
> >
> > > [!note] Comment PR Merge Master?!

^h-ba93bec527bb
```

`ref-highlights.css` draws nested quotes as one card with a dashed seam and a small-caps page caption from `data-callout-metadata`. Underline `**` runs become gold rules. That dialect is the one section chrome should speak: CSS variables, `color-mix`, small caps, hairline seams — not a new plugin, not a new callout type that restyles the whole vault.

### 4.3 Mac inspector

`RefsInspectorView.highlightsSection` is one HIGHLIGHTS feed in annotation order. Same-page entries share a caption (`showsPageLabel`); quotes get a 2 pt yellow leading rule; comments/images/stickies become a pale-yellow note card with `note.text`. Continuation groups stay one feed entry with dashed seams. Schema 1, `decodeIfPresent`, unknown keys ignored. The Copy card's H picker reads the same `annotations` array.

There is no section primitive. Adding one is a header row in this feed, not a second inspector pane.

### 4.4 Identity

Block ids are content-addressed from the PDF path and beautified quote (return-link glyphs and underline `**` stripped). Comments are not in the hash. Moving a card does not change its id. `#task` 🔖 links target the member id. Section grouping must not rewrite `[h::]` or recreate follow-up tasks — the same invariant `<` already documents for new tasks on grouped pieces.

---

## 5. The two collisions that would silently eat the feature

### 5.1 ATX headings vs section stickies

`is_markdown_heading` (`sidecar_render.rs`): 1–6 hashes followed by ASCII whitespace.

`parse_sidecar_chunk`: if every remaining line is a heading, return `[]`. Otherwise drop heading lines from comments and from standalone notes.

Linked-page export emits:

```md
# Document Title          ← preamble / ignored non-page heading
#### [Page 1](...)        ← page heading (kept as page_label)
##### 2026-06-03:         ← date heading (must keep ignoring)
> quote
comment
```

A sticky `# Architecture` in that export is indistinguishable from a heading. That is why A5 exists.

**Parser rule to add:** when flushing a standalone-note chunk, keep ATX lines that are neither page labels nor `##### YYYY-MM-DD:` date headings. Do this only for standalone notes, not for highlight comments (a comment that is literally `# See appendix` should stay a comment, and a heading-shaped comment line in linked export is usually the date heading).

Section *definitions* are standalone notes. Highlight comments use `@slug`, not `# Name`. So the keep-heading exception is scoped to the one kind that needs it.

### 5.2 `#` is already a comment vocabulary

From live notes, not from theory:

```
#a This description of memory webs should mention `sase memory read`…
#task Replace the contents of this line with …
```

`#a` is Bryan's editorial prefix (not a bob grammar). `#task` is a first-class importer. `#hide`, `#ref`, `#prj` are vault task tags. Capture uses `#name` for Pomodoros, on a different surface.

`# Architecture` (space) does not collide with any of those. `#architecture` (hashtag) would. The space is required.

`@` is quieter in this corpus: **zero** `@tokens` in the sampled comments. Capture's `@route` lives in the capture draft, not in PDF notes. Collision cost is low if we only scan comments and require a defined section before treating `@slug` as membership. Unknown `@objc` in a comment stays visible.

---

## 6. Alternatives considered

| Approach | Why it loses |
| --- | --- |
| **Highlights color categories** | Bob never sees color. Sorting the sidecar by color breaks `<`. Colors are few and unnamed unless Bryan also maintains a Highlights preference. |
| **PDF outline / bookmark auto-sections** | Free for some papers, useless for blogs and for "this quote belongs in my *memory* section". Themes are not document structure. |
| **Implicit range (everything until the next sticky)** | Fast while reading linearly; steals unrelated highlights. Footgun. v2 candidate, not v1. |
| **Obsidian-only headings edited in the managed region** | Next `scan` overwrites them. The managed region is not a notebook. |
| **Foldable `[!section]-` wrapping every member** | Fourth nesting level on continuation+comment; fights `ref-highlights` nested-quote CSS; block ids sit inside the fold; Mac would still need JSON to know the group. Beautiful in a screenshot, ugly in a real note. |
| **Dataview / plugin grouping of `[section::]` fields** | A new field on every card, a second ontology, invisible in `bob ref show` and in the Mac panel unless both grow parsers. |
| **Hashtag membership (`#architecture` on members)** | Collides with `#a` / `#task` / Highlights hashtags. `@slug` is the unused sigil in this corpus. |
| **`= Name` or `§ Name` instead of `# Name`** | Safer against ATX stripping, uglier in the Highlights notes pane, worse mnemonic. After A5, `# Name` is the heading it looks like. Keep it. |
| **Mac-side grouping of page-order JSON** | Violates the thin-client rule. Two apps would drift. `bob ref show -f markdown` and agents would still see page order. |

The winning shape is the one `<` proved: a small grammar in the PDF note, a plan in `bob ref`, a projection in the managed region, JSON for clients.

---

## 7. Recommended solution

### 7.1 Gesture

**Define** a section with a Highlights sticky note (standalone text annotation) whose first non-empty line is:

```text
# Architecture
```

Optional description after a blank line:

```text
# Architecture

How the pieces fit. Ownership, locking, and the public types.
```

Further lines may include `#task` bullets and image-note paths; those keep today's importers. The first line is consumed as the header. The description is the rest after the blank line, with membership tokens and the header line stripped.

**Join** a highlight, underline, image, or other sticky by putting `@architecture` anywhere in its note as a whole-word token. Combine freely with `<`, `#task`, and screenshot paths:

```text
@architecture
- #task Check the lock order on the daemon path
```

```text
< @architecture PR Merge Master?!
```

```text
locking belongs with the public types @architecture
```

**Leave** by deleting the `@` or the sticky. The next scan restores page-order cards. Stateless.

**Escape:** `\# Architecture` at the start of a sticky is a literal heading-shaped note. `\@architecture` is a literal at-token. Same boundary rule as `\<`.

### 7.2 Name rules

| Rule | Value |
| --- | --- |
| Header | `#` + ASCII whitespace + rest of line |
| Display title | trimmed rest of line, original casing |
| Id / membership | slug: NFC, casefold, whitespace → `-`, `[^a-z0-9-]` dropped |
| Token | `@` + slug, word boundary (no `@error handling`) |
| Empty / unslugable name | dangling; sticky renders as a normal `[!note]` |
| Duplicate slug | first definition wins; later `# Architecture` stickies dangle visibly |
| Reserved | names that match `is_sidecar_page_label`; `Removed highlights`; `Highlights`; `Tasks`; `Other` |
| Length | 1–40 characters of display title after trim |

`# Error Handling` → title `Error Handling`, id `error-handling`, members write `@error-handling`.

### 7.3 Planning pass

New module `src/native/highlights_ref/section.rs`, called from `plan_annotation_folds` **after** continuations and underline nests.

1. Walk remaining annotations (skip marker mirrors, skip underline children, treat a `<` group as one unit keyed by the head).
2. A standalone note whose first meaningful line matches the header grammar and is not escaped is a **definition**. Record title, slug, description, order, block id.
3. On every unit's effective `task_source` (and standalone text / image caption), find `@slug` tokens. Escape first. Unknown tokens stay. Known tokens: first match in token order assigns `section = slug`; all matching tokens are stripped from the displayed comment the same way `<` is stripped.
4. A `<` group's membership is the head's token, else the first follower that matches. An underline child's tokens join the host, same as its comments already do.
5. Dangling diagnostics: unknown `@slug`, duplicate definitions, reserved names, escaped-only, header with no slug.

Dry-run (`bob ref sync --dry-run`) prints `sections: N` and one `section_dangling:` line per problem, mirroring `continuations:` / `underlines_merged`. Concise scan adds `1 section` / `N sections` and dangling counts. JSON `notes[].sections` / `notes[].sections_dangling` only when nonzero. `schema_version` stays 1. `highlights_count` counts member cards, not banners.

### 7.4 Generated markdown (Obsidian)

When the plan is empty, render exactly as today.

When it is not, the managed region becomes section-primary:

```md
### Architecture

> How the pieces fit. Ownership, locking, and the public types.

> [!quote|Page 3] QuadPoints are page-scoped.
>
> > [!note] Comment The folder, not the sentence.

^h-aa11aa11aa11

> [!quote|Page 15] The daemon stores objects for the whole node.

^h-bb22bb22bb22

### Performance

> [!quote|Page 8] **No packfiles to accept.**

^h-cc33cc33cc33

### Other

### Page 1

> [!quote] We define goals broadly as desired outcomes at any altitude

^h-dd44dd44dd44
```

Design choices in that mockup:

- **`### Title` is a real heading**, so Obsidian's outline becomes Architecture / Performance / Other instead of a flat page list. That is the navigational payoff.
- **Description is a blockquote**, not a nested callout. Quiet, italic in many themes, no extra chrome, no fourth callout type in the default palette.
- **Members are siblings**, not children of a fold. Existing quote/comment/continuation CSS keeps working. `^h-` stays on the last line of each card.
- **Page moves to `[!quote|Page N]`** inside a section, the same metadata continuation groups already use. The `ref-highlights` rule that captions nested quotes from `data-callout-metadata` can grow a sibling rule for *top-level* quotes that carry metadata, so a single Architecture card still shows `Page 15` as a small-caps kicker.
- **`### Other` plus ordinary `### Page N`** only when ungrouped members exist. Pure section notes have no Other. Notes with no sections keep today's page headings and no Other.
- **Empty sections still emit** the heading (and description, if any), so Bryan can scaffold an outline and fill it.
- **Section order** is definition order (sidecar order of the stickies). **Member order** inside a section is sidecar order (roughly page order). Ungrouped members keep their relative sidecar order.

The section sticky's `^h-` is written immediately under the heading/description (a silent target), or as a block id on the heading line if we want it outline-visible. Prefer a dedicated line after the description, matching today's "id covers the card" pattern:

```md
### Architecture

> How the pieces fit.

^h-sec000000001
```

so `[[ref/paper#^h-sec000000001]]` still jumps. Do not reuse a member id.

### 7.5 CSS (`ref-highlights.css` only)

Do not add a plugin. Extend the snippet that already owns quote emphasis and continuation seams. Suggested dialect, matching the existing gold/yellow/small-caps language while giving sections a cooler accent so they do not compete with quote rules:

```css
/* bob ref: section annotations (# Name / @slug). Headings inside the
   managed region that are not page labels. */
.markdown-preview-view .el-h3 h3,
.markdown-source-view.mod-cm6 .cm-header-3 {
  /* scoped in practice via a .bob-ref-body class if we add one;
     otherwise accept that Page headings share some of this spacing. */
}

/* Prefer an explicit class on a wrapping callout-free container we
   cannot add without HTML. Practical v1: style H3s that do not
   match /^Page|^Pages|^p\.|^pp\./ via a tiny CodeMirror/plugin-free
   approach — a data attribute we cannot set on raw H3s.

   So v1 CSS targets a custom callout used ONLY when we need chrome
   the heading cannot carry: the description. Headings stay headings. */

.callout[data-callout="quote"][data-callout-metadata]:not(
    [data-callout-metadata=""]
  )::before {
  /* already used for nested continuation pieces; extend to top-level
     quotes so |Page 15 on a section member captions the same way */
}
```

Practical v1 that is actually beautiful without a plugin hook:

1. Give the section heading more `margin-top` by inserting a blank line (already there) and accepting that `### Page N` and `### Architecture` share heading size — they already do, and Architecture replacing Page in the outline *is* the visual change.
2. Keep the description as `>` so it is already muted.
3. Extend the existing `::before { content: attr(data-callout-metadata) }` rule so **top-level** `[!quote|Page N]` gets the same small-caps page kicker continuation followers already have. That is the polish that makes a reordered card still feel located.
4. Optional later: `cssclasses: [bob-ref]` on generated notes (frontmatter is already managed) and then `.bob-ref h3` can take a 3px left accent in `color-mix(in srgb, var(--color-blue) 40%, var(--text-muted))`, extra tracking, and a `SECTION` kicker via `::before` only when the heading text does not match the page-label regex. Frontmatter `cssclasses` is green field in this vault (article-notes research already proposed `bob-article`). Adding `bob-ref` on Highlights-generated notes is a small, justified projection.

I would take the optional `cssclasses: [bob-ref]` in the same PR as the renderer. One class, snippet already exists, outline + accent + page kicker = the look.

Do **not** invent `[!section]` as the primary chrome. Custom callouts are pretty and invisible to the outline. Headings are the outline. Description-as-blockquote is enough body.

### 7.6 `bob ref show` JSON (schema 1, additive)

On the show row, omit when empty:

```json
"sections": [
  {
    "id": "architecture",
    "title": "Architecture",
    "description": "How the pieces fit. Ownership, locking, and the public types.",
    "block_id": "h-sec000000001",
    "link": "[[ref/papers/scion#^h-sec000000001]]",
    "count": 2
  }
]
```

On each annotation, omit when null:

```json
"section": "architecture"
```

`annotations` order follows the generated region (section-primary when sections exist). That matches today's "show parses the managed region, not the sidecar" rule (`region.rs`). Human and markdown formatters print `### Architecture` then the members, with page labels on each card. `-c/--comments-only` keeps a section header when any kept member belongs to it.

`excluded` does not grow a `section_defs` counter; definitions are promoted, not excluded. Marker mirrors stay excluded.

### 7.7 Mac inspector

Thin client. `RefsShowAnnotation` gains `section: String?` (`decodeIfPresent`). `RefsShowRow` gains `sections: [RefsShowSection]` (default `[]`).

When `sections` is nonempty, `highlightsSection` inserts a header before each run:

- Small-caps title in the same caption semibold as `HIGHLIGHTS`, plus a tertiary count.
- Description under it in `callout` italic, 2-line limit, full text in a tooltip.
- Members keep today's quote rule, note card, image slot, and `<` seams.
- Page captions still appear on entries (`showsPageLabel` resets at each section run and whenever the page changes).
- `### Other` is a header titled `OTHER` for ungrouped members.
- VoiceOver: section headers `.isHeader`. Entries include the section title in the label (`Highlight, Architecture, Page 15: …`) so a flattened rotor still locates them.
- Paging (`Preview highlights per page`) stays index-based. A page boundary may fall inside a section; acceptable for v1. Revealed pages reset on selection change, as today.

Copy card H picker: keep a flat list in the new order; prefix the detail with the section title when present (`Architecture · p. 15`). Do not teach the picker to parse `@`.

Old app: unknown keys ignored; feed is still valid, just missing headers.

### 7.8 Interaction with the other two passes

Order:

1. Parse sidecar (after A5 heading fix).
2. `plan_continuations`.
3. `plan_emphasis_nests`.
4. **`plan_sections`** on the folded units.
5. Render: skip continuation followers and underline children as today; skip section-definition stickies (they become banners); emit banners then members.

`<` always wins structurally: a group is one member of at most one section. A leading `<` on an underline already forces that underline to stay standalone; if that standalone underline also has `@slug`, it sections as its own card.

`#task` on a member still imports against the member's identity id and 🔖-links the rendered card. `#task` on a section sticky imports against the section banner id.

Image notes on a section sticky: v1 may render them under the banner, below the description. Nice, not required; dropping them on the floor would be a bug, so copy them and emit them.

### 7.9 Dangling, dry-run, doctor

Visible leftover means "it did not take," the `<` rule.

| Typed | Result |
| --- | --- |
| `# Architecture` sticky, members `@architecture` | Section + grouped cards |
| `# Architecture` only | Empty section heading (scaffold) |
| `@architecture` with no definition | Token stays in the comment |
| Second `# Architecture` sticky | Renders as `[!note]`; dry-run `duplicate section architecture` |
| `# Page 12` sticky | Reserved; renders as `[!note]` |
| `\# Architecture` | Literal note |
| Highlight comment `# Architecture` | Literal comment; dry-run hint if that section exists ("did you mean @architecture?") |
| `@Error Handling` | Not a token; stays |

`bob ref doctor` does not need a new failing row. Optional later: a warn-level `section_dangling` under library diagnostics, like `unresolved_image_note`.

---

## 8. Beauty, specifically

The two surfaces already disagree in a useful way (underline research): Obsidian puts the quote in the callout **title** (semibold); the Mac paints it as body with a yellow rule. Sections should not add a third metaphor.

**Obsidian reading** should feel like a paper with an outline: named H3s, a short italic lede, then the same quote cards as today, each quietly captioned with its page. You jump from the outline. You do not open a fold to find a quote.

**Mac inspector** should feel like the same paper in a narrow column: the HIGHLIGHTS kicker stays; named runs appear as subkickers; yellow rules still mean "this was in the PDF"; pale-yellow cards still mean "this is yours." Section headers must be cooler and smaller than quote rules so the eye still hits the yellow first.

**Highlights itself** should keep looking like Highlights. `# Architecture` in the notes pane reads as a heading. `@architecture` on a highlight reads as a tag. If we picked `§` or `:::`, the pane would look like a markup error while reading.

That is why the grammar stays close to the request, and the *render* does the beauty work.

A concrete before/after from `sase_blog_261019` (17 comments, currently page-ordered). Today:

```
Page 2  "No, but point out that sase started at a lower level…"
Page 2  "Some form of this seems right."
Page 3  "Maybe reference this from the section where I talk about types of AI debt?"
Page 4  "Mention this when you mention memory of course."
Page 4  "Include this in the memory section as well."
Page 6  "All of these should be mentioned at some point in the blog post."
```

With two stickies `# Memory` and `# AI debt` and `@memory` / `@ai-debt` on those comments, the outline becomes the blog's outline, which is the document Bryan is actually trying to see.

---

## 9. Layering and rollout

### v1 (this feature)

- Parser fix A5.
- `section.rs` plan + render + region round-trip A6.
- Additive JSON, scan counts, dry-run dangling.
- `ref-highlights.css` page-kicker on top-level `|Page N` quotes.
- Optional `cssclasses: [bob-ref]` on generated notes.
- Mac inspector headers from `sections`.
- Docs: new subsection under Generated Body Contract, next to Continuation and Underline emphasis.
- Tests: sidecar heading-shaped stickies (simple + linked), slug/case, duplicate/reserved/escape, `<` + `@`, underline comment `@`, image caption `@`, empty section, Other tail, no-section notes byte-identical, region parse of mixed H3s, show JSON omit-empty, Mac decode of old envelopes.

No CLI flag. No Highlights preference. No plugin.

### Explicitly not v1

- Implicit sequential capture.
- Nested sections.
- Multi-section membership / duplicate cards.
- Foldable wrappers.
- Color-category import.
- PDF-outline auto buckets.
- Completing `@` inside Highlights (cannot).
- Editing grouping from Obsidian (overwritten).
- Schema 2.

### v2 candidates, only after real use

- Implicit capture between stickies, off by default or behind a second sticky spelling (`# Architecture.` vs `# Architecture>`).
- `bob-ref` CSS accent bar once `cssclasses` is in the wild.
- Inspector segment control "By page / By section" if anyone still wants page-primary on a sectioned note. JSON already has page labels, so this is a Mac-only view and does not require a second renderer.
- Doctor warn for dangling `@`.

---

## 10. Is the original plan good enough to ship as written?

No. The *idea* is right. The *spelling* is almost right. The *persistence model* ("think hard about the best way to persist") should not be a new file, a new frontmatter field, or a sidecar mutation — it should be the PDF note, like `<`. The *render* should not be "a nice visually appealing section of some sort" left to taste in each client: it should be one projection (H3 + sibling cards + `|Page N`) that Obsidian outlines, `ref show` prints, and the Mac headers.

Ship it with the twelve adjustments in §3. The feature then matches the bar the last two grouping passes already set: boring matcher, stable ids, leftover visible when it did not take, beautiful on both surfaces.

---

## 11. Recommended decision (for the lead)

**Do it.** Third grouping pass in `bob ref`.

- **Define:** standalone sticky, first line `# <Name>` (space required), optional description after a blank line.
- **Join:** `@<slug>` in the user's note text (comment / sticky / image caption), not in the quote.
- **Persist:** PDF annotation text only; generated region is a projection; no sidecar writes; no tombstones.
- **Render:** `### Name` + description blockquote + sibling `[!quote|Page N]` / `[!note]` cards; `### Other` only when needed; notes without definitions unchanged.
- **Clients:** additive `sections` / `section` on `bob ref show` JSON (schema 1); Mac draws headers; CSS extends `ref-highlights`.
- **Fix first:** sidecar heading strip (A5) and region H3 classification (A6).

That is the design I would implement.
