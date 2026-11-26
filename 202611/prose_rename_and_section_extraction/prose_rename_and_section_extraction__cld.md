# Renaming the `article` note type: the name, the scope, and a path to reversible projects

*Researcher: cld · 2026-11-26 · repos read: bob-cli, bob-plugins, the Bob vault (`~/bob`), Obsidian Help*

## TL;DR

- **Rename it, and do it now.** The vault has exactly **one** real article note
  (`sase_blog_contents.md`), plus one template, one `.base`, and one type note. No
  hotkeys are bound to `bob-articles`. The rename will never be cheaper. "Article" also
  already collides with web articles: `bob ref create` "Web article capture", the
  zorg-converted `articles.md` ref collection in the vault root, and ~200 "article" hits
  in `highlights_ref`.
- **Use `prose`.** Of about 20 candidates it is the only one that works both as a note
  type (`type: "[[prose]]"`, `bob prose`) and as the adjective your section idea needs
  ("prose section"). It is also the natural opposite of `notebook`, which holds only
  bullets. The runner-up is `doc`. It is a countable noun but reads badly as "doc
  section", and the vault already has a `docs.md`. Rules for using "prose" are in §3.4.
- **Change the definition, not just the name.** A prose note should not mean "any file
  that contains prose". Area, project, and ref notes all contain prose. A prose note is
  **a note whose body belongs to the author, where bob owns only the formatting and
  never adds structure**. The current refusals already enforce this: no `#task` lines,
  no `^prj`/`^ref` anchors, no mixed types.
- **A prose section should be a derived, extractable unit, not a region that gets
  formatted in place.** Formatting stays scoped to whole notes, as it is today. A
  "prose section" is any authored `##` section, worked out from its content and never
  marked in the file. One gesture extracts it into a prose note and leaves
  `## Title` + `![[note]]` behind. The opposite gesture inlines it back. Round-tripping
  must be byte-exact.
- **The type rename does not unblock reversibility.** The reversal code refuses for
  three separate reasons: child notes, non-list section content, and content outside
  sections. I recommend a **placement model**: prose never moves into a task block.
  Tasks and projects *place* prose notes with an embed, and conversion moves the
  placement and re-points `parent:`. Converting task → project → task then loses
  nothing, and the prose bytes are never rewritten.

---

## 1. What exists today

### 1.1 The `article` type

| Surface | Where | Notes |
| --- | --- | --- |
| Marker | `type: "[[article]]"`; `frontmatter_is_article` in `src/native/projects/scan.rs:364`; `TYPE_LINE` in `src/native/articles/marker.rs:116` | Type values are wikilinks to a type note (`~/bob/article.md`, parent `[[type]]`). |
| Engine | `src/native/articles/` (14 files, ~5.7k lines, ~494 "article" hits) | Numbering rules N1–N9, layout F1–F11, heading-link and inbound-link repair, word-token invariant, preimage-checked atomic writes. |
| CLI | `bob articles [list\|adopt\|format\|outline]` (`src/runner.rs:1284`) | Nightly runs `format -a -c` (`src/native/nightly.rs:42`). |
| Other bob-cli touch points | `capture/sections.rs` (capture `@note#Heading` matches article heading identity), `completion/kinds.rs` (`ArticleNote`), `props/roles.rs:352` (built-in type list) | About 60 hits outside the module. |
| Refusals | `not-article`, `mixed-type`, `holds-anchor` ("articles cannot be projects or refs"), `holds-tasks`, `conflict-markers`, `excluded-directory`, `frontmatter-unclosed` | These refusals already define the type: a body the author owns, with no machine structure. |
| JSON | ArticlePlan v1. "The contract only grows." | The only client is the plugin. |
| Plugin | `bob-plugins/plugins/bob-articles` (id `bob-articles`, "Bob Articles" v0.2.1). Commands `format-article` and `convert-to-article`, `.bob-article` class, `articleTypeface` setting. Detection in `articleHasArticleType` (`020-article-core.js:69`). | It is a thin client: it never parses article grammar. |
| Vault | `sase_blog_contents.md` (the only real note), `_templates/new_article.md`, `article.md` (type note), `articles.base` (`note.type == link("article")`), `type.md` (embeds `articles.base`), `AGENTS.md:15` | No `bob-articles:*` entries in `.obsidian/hotkeys.json`, and no plugin `data.json`. |

Type usage across the vault, for scale: `ref` 1390, `day` 1296, `record` 214, `project`
109, `done` 55, `notebook` 41, `mail` 32, `area` 24, `album` 11, **`article` 3**
(one note, one template, one historical chat source). The sibling types are short,
mostly countable nouns, and `done` shows that a non-noun type is already accepted.

### 1.2 The collision with "article" is real

- `~/bob/articles.md` is a zorg-converted **ref** collection ("[[ref]] notes for articles
  live here"). It sits in the vault root next to the `article.md` type note.
- `docs/highlights-clip.md` is titled "Web article capture (`bob ref create <URL>`)". The
  Reference Note glossary entry describes refs as "a book, article, or captured
  conversation".
- In bob-cli, `highlights_ref` has about 203 "article" hits, all meaning web articles.
  Anyone grepping for "article" gets two unrelated concepts.

### 1.3 Project ⇄ task conversion today

Promotion (task → project) is already lossless for drawers. "A bold drawer becomes a `##`
section that keeps its authored title byte for byte … Reversal of those sections writes
`- **Title**`" (`docs/projects.md`). Reversal (`^prj` → task) **refuses** in three
separate situations (bob-navigation-hotkeys):

1. `Project has N child notes; move them before converting`
   (`665-plugin-project-conversion.js:66`). This covers any note whose `parent:` is the
   project: article, notebook, album, or sub-project.
2. `Section "X" has content that is not a list item: "…"`
   (`210-rename-and-line-context.js:698`). This covers any paragraph, sub-heading,
   table, or fence inside a project `##` section.
3. `Project note has content outside the ^prj task and its sections`
   (`210-rename-and-line-context.js:744`). This covers intro prose.

`sase_blog` is a concrete example: it has `sase_blog_contents` (article),
`sase_blog_drafts` (sub-project), and `sase_blog_zettel` (album) as children, so today it
can never be reversed.

---

## 2. Is this a good idea? A critique

**The rename is a clear yes.** The user-visible concept will grow (sections, extraction,
reversal), and "article" is both too narrow (it suggests something published) and
ambiguous (web articles). The rename costs almost nothing today. Each new prose note you
write under the old name adds migration work later.

**The plan as written has four problems. I'd adjust the requirements as follows.**

> **Adjustment A1. Define the type by ownership, not by content.**
> *As written:* "use this type for any file that needs to contain prose."
> *Proposed:* "a note whose body the author owns: bob formats it but never adds
> structure, and it holds no tasks or anchors."
> *Why:* areas, projects, refs, records (the `sase_blog_zettel` records have prose
> claims), and notebooks all contain prose and must keep their types. The current
> refusals (`holds-tasks`, `holds-anchor`, `mixed-type`) already encode the ownership
> definition. Under the content definition, putting `[[prose]]` on a project note would
> look reasonable, and the engine would refuse it.

> **Adjustment A2. "Sections implicitly use this type" should mean *extractable*, not
> *formatted*.**
> Do not run numbering or layout inside a project's `## Design` section. The engine is
> deliberately whole-note ("it never formats only part of a note", `docs/articles.md`).
> Layout rules F5/F6/F8 are defined on whole files. Project notes also carry
> bob-managed content (`## Tasks` with generated `###` status groups, `[!projects]`,
> `[!albums]` catalogs) that capture and the nav plugin edit. A prose section should be
> a *derived classification*, like Leaf Project ("derived … never stored"). It makes
> the extract/inline gesture available and nothing more.

> **Adjustment A3. Reversibility needs a placement rule, not just a type.**
> Renaming `article` does not touch any of the three reversal refusals. The work that
> removes them is (a) extracting prose sections into prose notes and (b) a rule that
> lets a task *carry* its prose notes across conversion (§5). Prose bytes should never
> move into a task block: the drawer contract says entries are plain bullets.

> **Adjustment A4. The child-note blocker is wider than prose.**
> Refusal 1 also fires for notebooks, albums, and sub-projects. Ship prose first, but
> design the placement/carry rule so that notebooks can adopt it later without a
> second mechanism.

> **Adjustment A5. Old names are kept permanently.**
> Under `cli_rules`, `bob articles` becomes a *permanent* hidden alias of `bob prose`
> with byte-identical behavior. bob should also accept `type: "[[article]]"`
> permanently, the same way `[theme::]` and `theme:` are still read after the
> themes→types rename. Both are cheap and remove every version-skew risk (§6).

> **Adjustment A6. Define "lossless" so it can be tested.**
> *Lossless* means: `inline(extract(S))` reproduces section `S` byte for byte when the
> extracted note was not edited, apart from bob-owned section-number tokens and the
> blank line at each seam. The engine's existing word-token invariant (`verify.rs`)
> must hold across every multi-file plan. Anything that would be dropped (extra
> frontmatter keys) is refused or shown in the preview, never discarded silently.

---

## 3. Choosing the name

### 3.1 Criteria

1. **Generic.** It covers essays, blog posts, design docs, write-ups, letters, and
   extracted sections.
2. **Two grammatical roles.** It must work as a note type (`type: "[[X]]"`, `bob X`,
   "Bob X" plugin) *and* as a section adjective ("X section"). Your section idea
   depends on the second role.
3. **Contrast.** It should be distinct from `notebook` (bullets), `record` (fields),
   `ref` (external material), and `project`/`area` (tasks).
4. **No collisions** in bob's vocabulary, the vault root, or the Obsidian ecosystem.
5. **Short and typeable** in YAML and on the CLI.

### 3.2 Candidates

| Name | Generic | "X note" / "X section" | Collisions | Verdict |
| --- | --- | --- | --- | --- |
| **prose** | ✓✓ | ✓ / ✓✓ | Already a common noun in docs (~1000 uses, same meaning: free text). The nav plugin's internal `proseField` / "prose prompt" (free-text picker input). | **Recommended** |
| doc | ✓✓ | ✓ / ✗ ("doc section") | `~/bob/docs.md` exists (zorg); bob-cli `docs/`; "doc" = documentation everywhere | Runner-up |
| writing | ✓ | ✗ ("writing note") | — | Awkward |
| page | ✓✓ (too) | ✓ / ✗ | Every note is a page (Logseq/Notion sense) | Too generic |
| text | ✓✓ (too) | ✗ | Plain text, `.txt`, "text mention" | Too generic |
| essay / post / paper / memo | ✗ | ✓ | Genre-specific | Same problem as "article" |
| draft | ✗ | ✓ | Implies a lifecycle (unfinished) | Wrong meaning |
| longform | ~ | ✓ / ✗ | Popular Obsidian *Longform* plugin; implies length | Collides |
| writeup | ~ | ✗ | Suggests a report after an event | Narrow |
| section | — | — | Annotation Sections, notebook `#Section`, project `##` sections, capture `#Heading` | Badly overloaded |
| sheet / card | — | — | Record Sheet, Task/Property Card | Taken |
| chapter / passage / folio / piece / composition | ✗/~ | ~ | — | Obscure or genre-bound |
| (keep) article | ✗ | ✓ / ✗ | Web articles (§1.2) | Rejected |

### 3.3 Why `prose` wins

- **It is the only candidate that fills both roles.** "Prose note", "prose section",
  "Extract section to prose note", "Convert note to prose…", `bob prose format`, and
  "Bob Prose" all read naturally. The singular CLI noun matches `bob ref`.
- **It names the contrast that already structures the vault.** A notebook is "note
  bullets only" (`decisions:notebook-routes-write-notes`). A prose note is paragraphs
  and headings. The pair `notebook` / `prose` covers both shapes of an authored
  content note.
- **Its existing uses mean the same thing.** In current docs, "prose" means free,
  unstructured text ("Body prose is never scraped", "stays prose"). The type adds a
  precise meaning without changing the common one. The nav plugin's `proseField` also
  means "free-text input". Mild overlap, no contradiction.

The real costs of `prose` are that it is a mass noun ("a prose" is wrong) and that it is
hard to grep. §3.4 covers both.

### 3.4 Rules for using "prose"

- Always "**prose note**" or "**prose section**". Never "a prose" or "the prose" for
  the note. Plurals: "prose notes".
- Add a glossary entry **Prose Note** (alias: article (legacy)) and a separate entry
  **Prose Section**. Like the existing glossary entries, each should say what it is not:
  not a notebook, record, ref, drawer, or Annotation Section.
- In docs, use "free text" or "body text" for the generic meaning when the sentence is
  also about prose notes.
- Keep "article" available for the *look*: "article typeface" / serif reading view
  stays a plugin setting name, describing appearance, not type.

---

## 4. Prose sections: extract and inline

### 4.1 Definition (derived, never stored)

A **prose section** is an authored `##` section, meaning the H2 heading and every line
until the next H1/H2, that meets all of these:

- It is in an **area**, **project**, or **prose** note. Daily notes, refs, records,
  notebooks, albums, and mail are excluded in v1.
- It is **not bob-managed**: not `## Tasks` (whose `###` status groups are generated),
  and not the `## Projects` / `## Albums` / `## Notebooks` / `## Areas` catalogs.
- It holds **no `#task` checkbox lines and no `^prj`/`^ref` anchors**. This reuses
  `marker::body_refusals`. Requirement checkboxes and plain checklists are allowed.

A drawer-shaped section (only list items) is also a valid prose section. Extracting it
is allowed. It just isn't *required* for reversal.

### 4.2 Extract (section → prose note)

| Rule | Behavior |
| --- | --- |
| E1 New note | Stem `<owner>_<slug(title)>`, shown in an editable prompt. Refuse if the stem exists. Frontmatter: `parent: "[[owner]]"`, `type: "[[prose]]"`, `created:`, and **`title:` with the exact heading text, byte for byte** (the same rule drawers follow: `decisions:drawers-keep-their-names`). `title:` is already a supported article option. |
| E2 Body | The section body, with every heading **promoted one level** (`###` → `##`). The section's subsections become the note's top sections, matching the house style (`sase_blog_contents` uses `## 1.` at the top level). Then the normal format pass runs. |
| E3 What stays in the owner | `## <title>`, a blank line, and `![[<stem>]]`. The heading keeps its position and the embed renders the prose in place. Obsidian embeds don't show the note's title, so the heading doesn't appear twice. This "placed prose note" form is what makes the inverse operation and reversal (§5) work. |
| E4 Link repair | `[[owner#T]]` → `[[stem]]`. `[[owner#T#S]]` → `[[stem#S]]` (then renumbered by the existing link refresh). `[[owner#^id]]` where `^id` is inside the section → `[[stem#^id]]`. Embeds the same way. This reuses `links.rs` / `inbound.rs` identity matching and per-linker preimage checks. |
| E5 Safety | One plan across the owner, the new note, and the linkers. Writes are all-or-nothing. The word-token invariant holds across owner+note, and the result is idempotent. The existing `words-changed` / `not-idempotent` guards apply. |

### 4.3 Inline (prose note → section)

| Rule | Behavior |
| --- | --- |
| I1 Eligible | The cursor is on an owner section whose body is exactly one embed of a prose note whose `parent` is that owner, or the cursor is inside such a prose note. |
| I2 Body | Strip bob-owned number tokens (they belong to bob, rule N6), **demote** headings one level, and write `## <title:>` (or the stem). Refuse if the note has an H1 or any H6, since those cannot be demoted. |
| I3 Frontmatter | `parent`, `type`, `created`, `title`, `section_numbers`, and `template` are absorbed. Any **other key refuses** with the key listed, so nothing is silently dropped (A6). |
| I4 Links | `[[stem#S]]` → `[[owner#T#S]]`, `[[stem]]` → `[[owner#T]]`, block refs re-pointed. The note is then trashed, the same way reversal trashes the project note. |

**Property test (bob-cli):** for any eligible section `S` whose headings carry no
owned-number tokens, `inline(extract(S)) == S`. A section that *does* contain
`## 1.5 million users`-style tokens gets the same `number-replaced` preview that
`adopt` shows today.

### 4.4 Where it lives

Under the thin-client pattern that `bob-articles` already follows (the plugin "never
parses article grammar"; compare `decisions:mac-capture-is-a-thin-client`):

- **bob-cli** owns `bob prose extract NOTE --section TITLE` and `bob prose inline NOTE`.
  Each has a dry-run preview and `--stdin` JSON plans with multi-file edits, following
  the ArticlePlan pattern.
- The **Bob Prose plugin** provides two commands that send the buffer and apply the
  returned edits as one undoable transaction.
- **Keymap option** (needs your call): reuse the *conversion gesture's meaning* by
  cursor context. Today `Ctrl+Shift+Option+N` turns a task into a project and a `^prj`
  back into a task. The same idea one level down: on an authored `##` heading it would
  extract, and on a placed-prose embed it would inline. One "convert to its note form,
  or back" gesture across levels is easier to learn than three separate keys. If you'd
  rather not overload the nav key, give the prose plugin its own pair.

### 4.5 Prior art

- **Obsidian Note Composer** (core plugin, enabled in your vault). It offers "Extract
  current selection…" and "Merge current file with another file…". After extraction it
  leaves a link (default), an embed, or nothing. Its template supports `{{content}}`,
  `{{fromTitle}}`, `{{newTitle}}`, and `{{date:FORMAT}}`, and merging "updates all links
  to reference the merged note" (obsidian.md/help/plugins/note-composer). Gaps for Bob:
  it extracts a *selection*, not a heading subtree; it has no heading promotion or
  demotion; it does not repair links into the section; it has no Bob-aware inverse; and
  bob-cli or project reversal cannot call it. **Zero-code stopgap:** set its template
  to a `_templates/prose_extract.md` containing
  `parent: "[[{{fromTitle}}]]"` / `type: "[[prose]]"` and set it to embed after
  extraction. That gives you most of E1/E3 today.
- **Notion "Turn into → Page"** and **Logseq block ⇄ page** show the same idea: any
  block can become a page and keep its position. That position-keeping is what the
  embed in E3 provides.
- **Org-mode** refile/cut-paste of subtrees adjusts heading levels to the destination.
  That is the E2/I2 promote/demote rule.

---

## 5. Reversibility: the placement model

### 5.1 Principle

> **Prose is placed, never poured.** A task or project never contains prose bytes. It
> *places* a prose note with an embed (`![[x]]`), and the prose note's `parent:` names
> the note where the placement lives. Conversion moves the placement and re-points
> `parent:`. It never rewrites the prose.

There is already a precedent for this. A ref note's `parent` "is projected from where
that task lives" (Reference Note glossary), so a note's parent can follow a task's home.

### 5.2 Mapping

| Task block (in residence R) | Project note P | Status |
| --- | --- | --- |
| Drawer `- **T**` + bullets | `## T` + bullets | Exists |
| Drawer `- **T**` + `- ![[x]]` (x prose, parent R) | `## T` + `![[x]]` (x parent P) | **New**: promotion re-points x to P, reversal re-points x to R |
| — | `## T` + prose body | **Extract first** (§4.2), then the row above applies. Reversal can offer the extraction in its own preview instead of refusing. |
| Any prose note linked or embedded inside the task block, with parent R | A prose child of P | **Carry rule**: promotion re-points it to P. Reversal re-points it to R and keeps the link in the restored block. Unplaced prose children get a `- [[x]]` entry in the Notes drawer. |
| Intro prose above the first `##` | — | Extract it as a `## Overview` prose section first, or keep refusing. Your call. |

Under this model, task → project → task is byte-exact. Project → task → project loses
only *where* prose was written: an inline prose section comes back as a placed prose
note with identical bytes. That fits "minimal loss" and is the only normalization.

### 5.3 What I would not do

- **Put prose inside drawers** using indented continuation paragraphs or headings inside
  list items. That conflicts with the drawer contract ("its entries are plain bullets")
  and with every task-block parser in bob and the plugins. Its blast radius is far
  larger than anything else in this report.
- **Point `parent:` at a task block** (`parent: "[[R#^id]]"`). Parent walks resolve
  notes, not blocks. Every root/type/clock walk would need a new case.
- **Auto-format prose sections in place** (see A2).

---

## 6. Rename plan (ordered for the daily release train)

bob-cli ships at most once per New York day after full CI
(`decisions:bob-cli-releases-ride-a-daily-train`). Plugins deploy right away through
`bob plugins sync`, and three hosts (athena, apollo, mac) can run different bob
versions. So each step must be safe to run before the next one lands everywhere.

1. **bob-cli (one train).** Accept `[[prose]]` and `[[article]]` (permanent legacy
   alias). Make `bob prose` canonical and `bob articles` a permanent hidden alias
   (`cli_rules`). `adopt` writes `type: "[[prose]]"`. Add `prose` to the built-in type
   list in `props/roles.rs`. Rename the completion kind, the nightly step label, the
   help text, and the bob-owned display strings ("not a prose note; run
   `bob prose adopt`", "Prose note formatted · …"). Rename docs:
   `docs/articles.md` → `docs/prose-notes.md` and the CLI page, following the
   `pomodoro-themes.md` → `task-types.md` precedent (`d0603a5d`). **Keep machine
   vocabulary stable**: JSON keys (`summary.articles`), refusal *codes*
   (`not-article`), and `schema_version: 1`. They are contract, not user language, and
   "the contract only grows". Mark the commit `!` only if you choose to break JSON.
   Optional, separate refactor commit: rename the Rust module `articles` → `prose` so
   grep stops mixing it up with `highlights_ref`'s web articles.
2. **bob-plugins (same day is fine).** Change the display name to "Bob Prose", the
   commands to "Format prose note" / "Convert note to prose…", and detection to accept
   both types. **Keep the plugin id `bob-articles` and the existing command ids.** I
   found no retire/rename handling in `bob plugins sync`, and no hotkeys depend on the
   ids. The plugin can keep calling `bob articles`, which is a permanent alias, so
   version skew can't break it. Give *new* commands (extract/inline) prose-named ids
   from the start.
3. **Vault (after `bob --version` on all three hosts includes step 1).** Rewrite
   `sase_blog_contents.md`. Rename `article.md` → `prose.md` (Obsidian's rename updates
   links) and reword it to the A1 definition. Rename `new_article.md` → `new_prose.md`.
   Rename `articles.base` → `prose.base` with filter
   `note.type == link("prose") || note.type == link("article")`, and update the
   `type.md` heading. Update `AGENTS.md:15`. Leave the `.bob/ref-sources` chat sources
   alone (write-once history).
4. **Memory.** Add the Prose Note / Prose Section glossary entries. Write a decision
   record covering the rename, the A1 definition, and the permanent aliases. After §5
   ships, write a second one, "Prose is placed, never poured". Both go through
   `/sase_memory_write`.

Rough cost: step 1 is about 60 non-module touch points plus a mechanical module rename,
step 2 is a few dozen user-visible strings, step 3 is about six files. Prose sections
(§4) and the placement model (§5) are each a separate epic.

---

## 7. Risks and open questions

1. **Numbering default.** `section_numbers` defaults to `true`, the house style. That
   suits essays. For a short generic prose note with two headings it's a matter of
   taste. **Lean: keep `true`.** Inline strips the tokens, so it doesn't hurt round-trips.
   Revisit if most new prose notes end up opting out.
2. **Serif look on every prose note.** The plugin's `articleTypeface` setting already
   allows opting out. Leave it.
3. **Intro prose in project notes** (refusal 3). Extract it as `## Overview`, or keep
   refusing? It needs your decision. Each option has a cost.
4. **Notebooks/albums/sub-projects** still block reversal (A4). Placement generalizes to
   notebooks (embed a notebook). Sub-projects need their own design.
5. **Overloaded keymap** (§4.4). It's elegant, but it gives an existing hotkey new
   effects. Reject it if you'd rather keep gestures single-purpose.

---

## 8. Recommended solution

1. **Rename `article` → `prose` now**, with the ownership definition (A1). Keep
   `[[article]]` and `bob articles` as permanent aliases. Keep JSON keys, codes, and the
   plugin id stable. Change only user vocabulary. Ship in the order bob-cli → plugin →
   vault (§6).
2. **Treat "prose section" as a derived, extractable unit** (A2). Build
   `bob prose extract` / `bob prose inline` in bob-cli with byte-exact round-trip rules
   E1–E5 and I1–I4. Extraction leaves `## Title` + `![[note]]`. Expose them as two
   prose-plugin commands, or as a cursor-context extension of the existing conversion
   gesture. Meanwhile, a Note Composer template gives you most of extraction for free.
3. **Make task ⇄ project conversion placement-aware** (§5). Prose is placed with
   embeds, never poured into drawers. Promotion and reversal re-point `parent:` for
   carried prose notes, and reversal offers extraction for prose sections instead of
   refusing. Record this as a decision, and design it so notebooks can reuse it.

This keeps one engine owning prose formatting, adds no new stored state (prose sections
are derived and placements are ordinary embeds), and moves prose without changing its
bytes, which is what lossless reversal needs.
