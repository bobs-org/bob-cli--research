# Article notes: a typed long-form document with a Bob-owned outline

Researcher: `grk`. Independent design research for marking vault Markdown files as articles / design docs / other sectioned prose, then auto-formatting and auto-numbering their sections. Peer swarm reports were not consulted.

## Verdict

Do it. Introduce a first-class note type `type: "[[article]]"`, the same ontology already used for `[[project]]`, `[[area]]`, `[[ref]]`, `[[day]]`, `[[restaurant]]`, `[[podcast]]`, and `[[done]]`. Keep GTD work on the parent project note. Give articles their own formatter, their own CSS class, and their own CLI group. The motivating file `sase_blog_contents.md` is already the right shape: a child of `[[sase_blog]]` that holds prose, with tasks and the outline living on the project.

The request is right about the split (long-form sectioned files deserve different treatment from task notes) and right about the first use-case (format + numbered outline). It is underspecified about the marker, and it is slightly too eager about "auto" if that means global Linter rules or a community heading-numbering plugin. Bob already has the classification, parsing, and on-save hooks this needs.

## Bottom line

1. **The marker is `type: "[[article]]"`.** Add `article.md` with `parent: "[[type]]"`. Metadata Menu's type picker already lists children of `type.md`, so the type note is the whole "how do I specify this" UX. Derive `cssclasses: [bob-article]` so Obsidian can style the note; do not make `cssclasses` the source of truth.
2. **The engine is `bob articles` in bob-cli.** Native, tested, line-oriented, fence-aware, idempotent. A thin Obsidian plugin (`bob-articles`) styles the note, formats on save, and shells out to bob. Same thin-client rule as Mac Capture.
3. **Number headings in the source, outline-style, starting at 1.** Write `1. Title`, `1.1. Title`, `1.1.1. Title` (always a trailing dot on the last component, then a space). Display-only CSS counters are a poor fit for Obsidian's flat preview DOM. Community plugins that number every file, or that stash settings in extra frontmatter keys, fight Bob's type system.
4. **Format structure, leave voice alone.** Repair heading increments, heading spacing, trailing whitespace, consecutive blanks, and EOF newline. Do not reflow paragraphs, title-case headings, move footnotes, or host `#task` lines in articles.

---

## 1. Is this a good idea?

Yes. The vault already distinguishes *kind of note* from *parent*. Restaurant notes, podcast notes, daily notes, and project notes all share `parent` plus a `type` wikilink. `sase_blog_contents.md` is the missing kind: a long-form document that belongs to a project and should look and behave like a document.

Three facts make the feature cheap and the alternative expensive:

- **The type registry is already a product.** `type.md` is the index. Its children today are `area`, `day`, `done`, `podcast`, `project`, `ref`, and `restaurant`. Metadata Menu's `type` field queries `dv.pages()` whose `parent` is `type.md`. Adding `article.md` makes `[[article]]` pickable in the Properties UI with no new plugin surface.
- **The motivating composition already exists.** `sase_blog.md` is `type: "[[project]]"` with a `^prj` task, `## Tasks`, `## Contents` (`Draft: [[sase_blog_contents]]`), and `## Outline`. `sase_blog_contents.md` is an untyped child (`parent: "[[sase_blog]]"`) of 40 lines of lede + headings + TODOs. The project holds work; the child holds the post. Marking the child as an article completes a pattern Bryan is already using.
- **A global formatter would harm GTD notes.** Project notes pack `## Tasks` against chip lines and status groups with no blank line. Daily notes, `## Pomodoros`, and generated BLOCKS/WORK LOG lines are similarly tight. Obsidian Linter is already `lintOnSave: true`, and the only enabled rule is `add-blank-line-after-yaml`. Enabling `heading-blank-lines`, `header-increment`, or `trailing-spaces` vault-wide would churn thousands of task notes. Article-scoped formatting is the feature; global markdown lint is the footgun.

The feature earns its keep if opening `sase_blog_contents.md` feels like opening a paper (numbered outline, calm type, predictable spacing) while `sase_blog.md` still feels like a project. It fails if articles grow `#task` lists, if numbering silently breaks `[[Note#Heading]]` links, or if format-on-save reflows Bryan's sentences.

---

## 2. Critique of the original plan

The request asks for: a way to specify that a particular Markdown file should always be treated as an article / design doc / sectioned content; different treatment (including formatting) from other vault notes; `~/bob/sase_blog_contents.md` as the first example; auto-format plus auto-number sections starting at 1 with subsection support; a design that is intuitive, reliable, and beautiful.

### What to keep

- **An explicit, durable marker on the file itself.** Path conventions (`articles/`), filename suffixes (`_contents`), and "this file has many headings" heuristics will rot. The marker has to survive rename, move, and agent edits.
- **Different treatment than task notes.** The first consumer is formatting and numbering. Later consumers (publish, PDF snapshot, a calmer reading theme, a TOC block) ride the same marker.
- **Auto-numbering with subsections, starting at 1.** Hierarchical decimal numbering is the right default for design docs and for a technical blog.
- **Beauty as a requirement.** Bob already has a visual language in vault snippets (`dataview-properties.css`, `inline-code.css`, `task-statuses.css`): CSS variables, `color-mix`, small radii, muted chrome. Article styling should speak that dialect.

### What to change

These are explicit requirement adjustments.

**A1. The marker is `type: "[[article]]"`, one field. (classification)**

The request says "a way to specify" without naming the field. Tags (`#article`) collide with GTD tags and can be many. `cssclasses` is the right *styling projection* (Obsidian 1.9 requires it to be a list, and it is applied to both `.markdown-source-view` and `.markdown-preview-view`), but it is a theme/CSS concern. Folder location is not identity. A parallel `format:` / `kind:` key would be a second ontology next to `type`, which the vault does not have.

`type` is already the ontology. Restaurant and podcast notes prove it is not reserved for GTD. Rust already has `frontmatter_has_type` in `src/native/projects/scan.rs` (quoted, bare, flow-list, block-list). Plugins already branch on `frontmatter.type`. One new type note plus one new predicate is the whole classification story.

**A2. One type covers article, design doc, RFC, and "content with sections." (scope)**

Do not ship `[[article]]` vs `[[design-doc]]` vs `[[rfc]]` in v1. There is no behavioral split yet. If a design doc later needs denser type or a paper margin, add an extra cssclass (`bob-article-dense`) or an optional `article_kind:` field. The type stays `[[article]]`.

**A3. Article notes do not host `#task` lines. (GTD boundary)**

Glossary: every `#task` belongs in exactly one area or project note by residence. An article with `#task` would become a new class of stray task, and every scanner that currently ignores untyped prose would have to special-case it. Checklists without `#task` are ordinary Markdown and are fine. Work for the article lives on the parent project, which is already how `sase_blog` / `sase_blog_contents` are split. The formatter refuses (or `--force`-warns) when it sees `#task` or a `^prj` / `^ref` line.

**A4. Never auto-detect articles. (reliability)**

A "file with ≥N headings and 0 tasks" query is a discovery aid, not a classifier. `bob articles mark PATH` (or the Properties type picker) is the only writer of `type: "[[article]]"`. `bob articles format` is a no-op on any other file. That is the safety property that makes on-save formatting acceptable.

**A5. Write numbers into the heading source, with an idempotent parser. (numbering medium)**

Display-only numbering (CSS `::before` counters, CodeMirror widgets) keeps wiki-heading targets stable and diffs quiet. It also disappears in git, in `bob` output, in agent context, and in any publish path that is not Obsidian. The motivating file is a blog draft destined for sase.sh; agents and git are first-class readers. Source numbering is the format that survives those readers.

CSS counters in particular are a known poor fit for Obsidian Reading view: headings sit in sibling `.markdown-preview-section` nodes rather than a nested outline, so nested counters reset per section (Obsidian Forum, "Header counter", 2020, still structurally true). Widget-based community plugins solve the display problem and leave the source mute.

Mitigation for heading-link breakage is part of the formatter, not a reason to stay display-only. See §6 and §8.

**A6. Do not turn on Obsidian Linter heading rules globally, and do not install Number Headings. (tooling)**

Linter is already the on-save chime. Its heading rules (`header-increment`, `heading-blank-lines`, `capitalize-headings`, `file-name-heading`, `re-index-footnotes`) are all disabled, correctly. Number Headings (onlyafly, last feature release 1.16.0 on 2023-10-03) numbers by command or by its own frontmatter settings blob, has no Bob type awareness, and has historically looped on separators and eaten headings that start with digits. Auto Headings / Number Suite (2025–2026) are better display-only plugins and still add a third-party numbering authority next to Bob.

Use Linter as the on-save *trigger* (`lintCommands` → `bob-articles:format-if-article`). Keep its rule set as it is.

**A7. Do not reflow prose. (voice)**

"Auto-format" in the request is easy to read as prettier/mdformat. Reflowing Bryan's lede would produce noisy diffs, fight Vim line-wise editing, and change the writing. v1 formats structure around headings and whitespace. Sentence wrapping, smart-punctuation of body text, and `->` → `→` in paragraphs wait for an explicit later decision. Heading-only arrow normalization is listed below as optional polish, off by default.

**A8. Default document title is the filename / inline title. Number every heading. (outline origin)**

markdownlint MD001 treats a YAML `title:` as an implicit H1 and then wants the first heading to be H2. Restaurant and podcast notes follow "H1 matches filename, then `## Notes`". The blog file does the opposite: no title H1, lede paragraphs, then `# The Abstractions` as the first *section*. Auto-treating a lone H1 as an unnumbered title would skip numbering the one heading that most needs it.

Default: `article_title: filename`. Every ATX heading participates in the outline; the shallowest heading in the file is outline level 1. Override with `article_title: h1` when the first heading really is the document title (unnumbered, and sections start at H2 as `1.`).

**A9. Repair skipped heading levels rather than numbering a hole. (MD001)**

The example jumps from `## Agent CLIs` to `#### Skills`. Numbering that as `1.3` then `1.3.1.1` (or `1.3.0.1`) is ugly and inaccessible (W3C heading guidance; markdownlint MD001). The formatter pulls a heading up so its outline depth is at most one deeper than the previous heading. It never pushes headings down. `#### Skills` under `## Agent CLIs` becomes `### 1.3.1. Skills`.

---

## 3. How Bob already classifies notes

Live vault frontmatter `type` values (gitignored trees skipped: `.obsidian`, `lit_review`, `xlib`, `done`):

| Count | `type` | Role |
| ---: | --- | --- |
| 1193 | `[[day]]` | Periodic notes |
| 1053 | `[[ref]]` | External reading |
| 92 | `[[restaurant]]` | One-note-per-place records under `[[eat]]` |
| 88 | `[[project]]` | Finite outcomes with `^prj` |
| 15 | `[[podcast]]` | One-note-per-show records under `[[podcasts]]` |
| 13 | `[[area]]` | Ongoing spheres with no end state |
| ~2727 | *(none)* | Includes `sase_blog_contents.md`, most zettels, playbooks |

Type notes themselves live at the vault root with `parent: "[[type]]"`. `article.md` does not exist yet. Restaurant and podcast notes also carry `title:`, a matching `# Title` H1, and a `## Notes` section — a content-note pattern, still unnumbered, and correctly so. Those types stay out of the article formatter because the formatter keys off `type`, not off "has headings."

`bob projects` already ignores every type other than `[[project]]`. Adding `[[article]]` does not disturb project scan, area Ready caps, ref sync, or daily-note machinery, as long as articles remain exclusive of those types (one `type` field).

Plugin type matching is currently stricter than Rust: `bob-project-tasks` compares `frontmatter.type` to the exact string `"[[project]]"`. Rust accepts quoted, bare `[[project]]`, flow lists, and block lists (`frontmatter_has_type`). New article detection on both sides should use the Rust-flexible matcher.

Obsidian community plugins already in the vault that touch this problem:

| Plugin | Relevance |
| --- | --- |
| **Obsidian Linter** | `lintOnSave: true`; only `add-blank-line-after-yaml` enabled; `lintCommands: []`; ignore lists empty |
| **Metadata Menu** | `type` is a File field whose Dataview query is "pages whose parent is `type.md`" |
| **Templater** | `_templates/new_note.md` writes `parent` + `created`, no type; `_templates/new_project.md` writes `type: "[[project]]"` |
| Number Headings / Auto Headings / Number Suite | **Not installed** |

Vault CSS snippets enabled: `task-statuses`, `dataview-properties`, `inline-code`. No `cssclasses` uses showed up in a vault-wide Markdown search. `cssclasses` is green field, and the class name should be prefixed `bob-` so it cannot collide with theme utility classes (`writing`, `paper`, `readable`, ITS Theme abbreviations, and so on).

---

## 4. The motivating file

`~/bob/sase_blog_contents.md` today:

```yaml
---
parent: "[[sase_blog]]"
created: 2026-10-15T15:10:41-04:00
---
```

Then two lede paragraphs, four footnote definitions (`[1]`, `[2]`, `[a]`, `[b]`), a blank run, and this outline:

```
# The Abstractions
## Gates -> Plans -> Epics
## Beads -> Sidecar repos
## Agent CLIs
#### Skills, **memory**, provider interface, NOT hooks
#### Agent presentation / organization (tribes, clans, families, hoods, metadata/files/tools panel)
## VCS and workspace operations␠
## Xprompts / Agent control flow (forks/waits/queues)
## Project Management (hoods, agents sidecar, artifacts)
## Routines and Jobs
```

Defects a formatter should repair without asking:

- Missing `type` / `cssclasses`
- Heading skip (`##` → `####`)
- Trailing space on "VCS and workspace operations"
- No blank line after `# The Abstractions`
- Extra blank lines between the footnote block and the first heading

Inbound wiki links: `sase_blog.md` (`Draft: [[sase_blog_contents]]`) and `why_sase.md` (`Superseded by [[sase_blog_contents]]`). **No inbound heading links.** v1 numbering will not break any existing `#Heading` target for this file. `why_sase.md` is a superseded draft of the same post; leave it untyped.

The parent project already owns `## Contents` and `## Outline`. The article formatter should not inject a Contents section of its own.

---

## 5. How to mark a file as an article

Ranked options:

| Marker | Intuitive | Reliable | Beautiful | Verdict |
| --- | --- | --- | --- | --- |
| `type: "[[article]]"` | Matches every other kind of note; Properties picker comes free | Parsed by existing `frontmatter_has_type`; Dataview-queryable | Type note is a place to put the contract | **Choose** |
| `cssclasses: [bob-article]` only | Properties UI is fine | No Bob CLI meaning unless every command grows a second reader | The official styling hook | Derive it from type |
| `#article` tag | Fast to type | Tags are many, GTD-heavy, easy to apply by accident | Weak | Reject |
| Folder `articles/` | Familiar from static sites | Breaks on move; `sase_blog_contents` wants to sit next to `sase_blog` | Fine | Reject as primary |
| `format: article` extra key | Clear | Second ontology | Extra chrome | Reject |
| Number Headings frontmatter blob (`number-headings: …`) | Hidden | Plugin-specific, not a Bob type | Ugly YAML | Reject |
| Heuristic (heading count) | Zero ceremony | Will false-positive playbooks, type notes, dashboards | Invisible | Reject as a writer; optional as `bob articles candidates` later |

**Marking UX, in order of daily use:**

1. Properties → `type` → pick `[[article]]` (Metadata Menu, once `article.md` exists).
2. `bob articles mark sase_blog_contents.md` writes `type: "[[article]]"` and ensures `cssclasses` contains `bob-article`, preserving every other YAML key and quoting style.
3. `_templates/new_article.md`, sibling of `new_project.md`: `parent` from the active file, `type: "[[article]]"`, `cssclasses: [bob-article]`, `created`.

`bob articles mark` is the agent-friendly path. The template is the human-friendly path for new files. The type picker is the path for converting an existing untyped draft (the blog).

`cssclasses` is a derived field, in the same spirit as project `task_count`: machine-maintained, safe to restore, not a second source of truth. The plugin also injects the `bob-article` class on the leaf at runtime if the YAML projection is missing, so a half-marked note still *looks* like an article while `mark` / `format` repair the YAML.

---

## 6. Auto-numbering: source vs display

This is the design fork that decides whether the feature is a vault theme or a document format.

### Display-only (CSS widgets / `::before`)

- Heading wiki targets stay `[[sase_blog_contents#The Abstractions]]`.
- Git diffs stay quiet when a section is inserted above.
- Reading view and Live Preview can look numbered.
- Source mode, `cat`, `bob query`, agents, and any non-Obsidian publish path see an unnumbered file.
- Pure CSS counters do not nest correctly in Reading view (flat preview sections).
- Needs a plugin for Live Preview widgets and for the Outline pane.

### Source numbering (write `1.1. Title` into the heading line)

- Every reader sees the outline, including agents drafting the blog.
- The published Markdown carries the numbers.
- Idempotence is mandatory (re-run must not produce `1. 1. Title`).
- Inserting a section above rewrites later numbers (expected, and a real diff).
- `[[Note#Heading]]` targets change when numbers change.

**Recommendation: source numbering.** The first use-case is a blog post. The second reader after Bryan is an agent. Display-only would make the vault pretty and the git history mute, which is the wrong priority for a document that wants to leave the vault.

**Link-stability plan, so this stays reliable:**

- Strip and reapply with a strict prefix grammar (next section) so numbering is a projection of heading order, always.
- Same-file heading links (`[[#The Abstractions]]`, `[text](#the-abstractions)`) update in the same format transaction.
- Vault-wide heading-link repair is v1.1, using the existing `vault_links` note index. v1 may refuse to number (or may warn) when other notes already link at a heading that would change, once that scan exists; the blog file currently has zero such links, so v1 can ship without the vault-wide pass.
- Block IDs on headings (`## Title ^id`) stay on the line; numbers go in the title text; `[[Note#^id]]` links are unaffected. Prefer `^id` for any heading that other notes must cite.

A later `bob articles format --display-only` or a plugin setting that conceals stored numbers in Live Preview (Number Suite's trick) can be a viewing preference. It is not v1, and it does not replace source numbers.

---

## 7. Formatting rules (v1)

Philosophy, copied from `bob projects sync`: mutate only the lines that must change. Reuse `src/native/markdown.rs` (`atx_heading`, fence tracking, strictly closed frontmatter). Do not parse the file into a CommonMark AST and pretty-print it; that is how wikilinks, Dataview fields, and block IDs get smashed.

Apply only when `frontmatter_has_type(..., "[[article]]")`. Otherwise print a one-line skip and leave the file untouched.

### Do

1. **Ensure YAML projection.** `type: "[[article]]"` already present (required). `cssclasses` is a YAML list containing `bob-article`. Do not reorder other keys. Do not add `title:` unless asked (`yaml-title` stays off, matching current Linter config).
2. **One blank line after the closing `---`.** Already Linter's only enabled rule; keep the formatter idempotent with it so order of on-save hooks does not matter.
3. **ATX headings only, hash-space form.** `##Title` becomes `## Title`. No Setext (`===` / `---`) conversion in v1; if a Setext heading appears, report it and leave it (rare in this vault).
4. **Trim trailing whitespace** on every non-code-fence line, including the trailing space on `## VCS and workspace operations `.
5. **Collapse consecutive blank lines to one.**
6. **Exactly one blank line before and after each heading**, including between a heading and a following heading. Exception: no extra blank line forced *inside* a YAML block.
7. **Repair heading increments** (A9): outline depth increases by at most one from the previous heading. Pull deeper headings up. Leave a jump *up* (H3 then H2) alone — that is a new sibling/parent, not a skip.
8. **Number headings** per §8.
9. **Single trailing newline at EOF.**
10. **Preserve:** YAML body other than the two derived keys, fenced code (`` ``` `` and `~~~`, using the existing fence matcher that respects 3-backtick rules and indentation ≤ 3), tables, wikilinks, Markdown links (except heading-target updates), footnotes in place, HTML comments, callouts, block IDs, emphasis in headings, tab indentation in lists, paragraph wrapping.

### Do not (v1)

- Reflow paragraphs or wrap to a column.
- Title-case headings (`capitalize-headings` stays off; Bryan's headings are as-written, with bold and commas).
- Move footnotes to the bottom or re-index `[1]` / `[a]`.
- Convert list markers, emphasis style, or quote style.
- Insert a Contents / TOC heading (the parent project already has one; a generated `## Contents` would itself get numbered as section 1).
- Touch `#task` lines, `^prj`, `^ref`, or any file whose type is not `[[article]]`.
- Rewrite `parent`.
- Smart-replace body punctuation. Optional later: heading-only `->` → `→` behind `--typography`.

### Idempotence

`format` twice is a no-op. `check` is format against an in-memory copy and exits 1 when a write would occur (CI / `--dry-run` twin). Cursor restoration is the plugin's job: map heading-line edits through the editor transaction, matching Number Headings 1.7.x's "don't pollute undo" lesson — one undo step per save, not per heading.

---

## 8. Numbering rules

**Grammar of a numbered heading:**

```
<ATX> <outline> "." <space> <title> [<space> "^" <block-id>]
```

Examples:

```markdown
# 1. The Abstractions
## 1.1. Gates -> Plans -> Epics
### 1.3.1. Skills, **memory**, provider interface, NOT hooks
```

Always a trailing dot on the last numeric component, then a space. That is the whole trick for not eating real titles that start with a year:

| Heading text | Strip as number? |
| --- | --- |
| `1. The Abstractions` | yes |
| `1.1. Gates` | yes |
| `1.1.1. Skills` | yes |
| `2026 Roadmap` | no (no trailing dot after the integer) |
| `1.1 Gates` (forgotten trailing dot) | no, then the next format pass numbers it as a *new* heading, producing `1.1. 1.1 Gates` unless we also accept a dotted multi-component without the final extra dot |

To close that last hole, the stripper accepts **either**:

- `\d+\.\s+` (single component with trailing dot and space), or
- `\d+(?:\.\d+)+\.?\s+` (two or more components, optional trailing dot, then space)

and nothing else. `2026 Roadmap` stays. `1. Title` strips. `1.1 Title` strips. After strip, the writer always emits the canonical trailing-dot form, so the forgotten-dot case converges in one pass.

**Outline construction:**

1. Collect unfenced ATX headings after frontmatter, each as `(level, title, block_id)`.
2. If `article_title: h1` and the first heading is H1, emit it unnumbered (after whitespace rules) and number the rest with H2 as outline depth 1.
3. Otherwise (`article_title: filename`, the default) every heading is numbered. Let `base = min(level)` over the file. Outline depth of a heading is `level - base + 1`, then compressed so depth increases by at most 1 relative to the previous *numbered* heading (the skip repair). When depth compresses, also rewrite the ATX hash count to match (H4 under H2 becomes H3).
4. Counters `c[1..=6]`. On depth `d`: `c[d] += 1`; `c[k>d] = 0`. Label is `c[1]..=c[d]` joined by `.`, plus a trailing `.`.
5. Start at 1. No roman numerals, no `A.B`, no `§`. No `start-at` in v1 (Number Headings has it; Bob does not need it until someone asks).

**Worked example — `sase_blog_contents.md` after format:**

```markdown
---
parent: "[[sase_blog]]"
created: 2026-10-15T15:10:41-04:00
type: "[[article]]"
cssclasses:
  - bob-article
---

I've always been proud to call myself a Software Engineer. …

SASE[1] (Structured Agentic Software Engineering) is …

[1]: TODO: Add a note about pronunciation, …
[2]: TODO: Link to Omnigent …
[a]: TODO: Add links!
[b]: TODO: Update commit/line counts!

# 1. The Abstractions

## 1.1. Gates -> Plans -> Epics

TODO

## 1.2. Beads -> Sidecar repos

TODO

## 1.3. Agent CLIs

TODO

### 1.3.1. Skills, **memory**, provider interface, NOT hooks

TODO

### 1.3.2. Agent presentation / organization (tribes, clans, families, hoods, metadata/files/tools panel)

TODO

## 1.4. VCS and workspace operations

TODO

## 1.5. Xprompts / Agent control flow (forks/waits/queues)

TODO

## 1.6. Project Management (hoods, agents sidecar, artifacts)

TODO

## 1.7. Routines and Jobs

TODO
```

Lede stays unnumbered. Footnotes stay where they are. H4s become H3s under Agent CLIs. Trailing space dies. The outline is readable in git, in Vim, and in an agent prompt.

---

## 9. Architecture

```
┌──────────────────────────────────────────────────────────────┐
│  article.md  parent: [[type]]     ← registry / picker        │
│  note YAML   type: [[article]]    ← source of truth          │
│              cssclasses: [bob-article]  ← styling projection │
└───────────────────────────┬──────────────────────────────────┘
                            │
          ┌─────────────────┴─────────────────┐
          ▼                                   ▼
┌─────────────────────┐             ┌─────────────────────┐
│ bob articles        │  JSON/text  │ bob-articles plugin │
│  list (default)     │◄────────────│  format-if-article  │
│  check              │  subprocess │  on Linter save     │
│  format             │             │  styles.css         │
│  mark               │             │  class injection    │
└─────────────────────┘             └─────────────────────┘
          │                                   │
          │ native: markdown.rs fences,       │ .bob-article
          │ atx_heading, frontmatter_has_type │ serif, numbers,
          │ line-oriented rewriter            │ spacing, paper
          ▼                                   ▼
     vault file                         reading / LP view
```

### CLI (`bob articles`, Vault section)

CLI rules: nest under a noun with a stated membership rule; a bare group may default only to a flag-only read-only member; every public long option gets a short alias; help is excellent; color when it helps; never hard-rename.

Membership rule: **commands that inspect or rewrite notes whose frontmatter type is `[[article]]`.**

| Command | Role |
| --- | --- |
| `bob articles` / `bob articles list` | Read-only catalog: path, parent, heading count, numbered? (yes/stale/no), `#task` warning |
| `bob articles check [PATH…]` | Dry-run format; exit 1 if any file would change |
| `bob articles format [PATH…]` | Write; default all article notes; `-d/--dry-run` aliases check for this member |
| `bob articles mark PATH` | Set type + cssclasses; create nothing else |

Alphabetical under Vault, `articles` sits above `nightly`, `query`, `ref`, `vault-sync`. Options (illustrative, keep sorted): `-b/--bob-dir`, `-d/--dry-run`, `-f/--format human|json`, `-n/--no-number` (format whitespace only, for debugging), `-q/--quiet`.

Reuse `frontmatter_has_type`; add `frontmatter_is_article`. Do not add a Markdown crate. Tests live next to the rewriter with fixtures that include fences, years-in-titles, skipped levels, block IDs, and a file that is *not* an article (must be a byte-identical no-op).

### Plugin (`bob-articles` in bob-plugins)

A seventh plugin, not another 2000 lines in navigation-hotkeys. Deploy with `bob plugins sync`.

- `styles.css`: the `.bob-article` theme (next section).
- Command `Format article if applicable` (`bob-articles:format-if-article`): if the active file's type is `[[article]]`, run `bob articles format --format json <path>`, apply the patch as one editor transaction, restore the cursor. If type is anything else, no-op (so it is safe as a Linter `lintCommand`).
- Workspace listener: add `bob-article` to the leaf's class list from `cache.frontmatter.type`, even before YAML projection exists.
- Palette command `Mark as article` → `bob articles mark`.
- Do not spawn bob on every keystroke. Save-only, matching current Linter behavior. Debounce is unnecessary if the trigger is save; if format ever moves to a metadata-change hook, debounce ≥500 ms and skip while the cursor is on a heading line that has no trailing newline yet.

Wire Linter: `lintCommands: ["bob-articles:format-if-article"]`. Linter still does the YAML blank line; the plugin does the rest; both are idempotent.

### What not to build in v1

- A `bob-article-toc` code block (tempting, and a good v2: rendered, never stored as headings).
- Publish pipeline into sase.sh.
- Vault-wide heading-link rewrite (v1.1).
- Display-only / conceal mode.
- New Dataview pages beyond "LIST WHERE type = [[article]]" which already works once the type exists.

---

## 10. Beauty

Task notes should keep looking like tools. Article notes should look like a short paper. The existing snippet quality bar is variables + `color-mix` + small chrome, not a new theme.

Sketch for `plugins/bob-articles/styles.css` (direction, not a paste-ready ship):

```css
.bob-article {
  --bob-article-measure: 42rem;
  --bob-article-number: color-mix(
    in srgb,
    var(--text-muted) 70%,
    var(--interactive-accent) 30%
  );
  --file-line-width: var(--bob-article-measure);
  --font-text: var(--font-text-theme, "Iowan Old Style", "Palatino Linotype", Palatino, Georgia, serif);
  --heading-spacing: 1.8em;
}

.bob-article .cm-header-1,
.bob-article .markdown-rendered h1 {
  letter-spacing: -0.015em;
}

.bob-article .cm-header,
.bob-article .markdown-rendered :is(h1, h2, h3, h4) {
  font-variant-numeric: tabular-nums;
}

/* The "1.1." prefix is source text; color only the leading outline. */
.bob-article .cm-header .cm-header-number,
.bob-article .markdown-rendered :is(h1, h2, h3, h4) .bob-article-number {
  color: var(--bob-article-number);
  font-weight: 550;
  margin-right: 0.15em;
}
```

The plugin may wrap the recognized outline prefix in a span so the number can be muted without a CSS parser for heading text. If that wrapping is too fiddly for v1, coloring the whole heading is acceptable; muted numbers are a v1.1 polish.

Other visual rules:

- Keep readable line length on articles even if the rest of the vault is wide (`.bob-article { --file-line-width: 42rem; }`).
- Slightly more space above H2 than H3.
- Do not watermark "DRAFT", do not center headings, do not drop-cap the lede. Calm > magazine.
- Properties in reading view can stay collapsed; the type wikilink is enough identity.
- Inline title (filename) remains the document title under the default `article_title: filename`. Do not hide it. Do not also insert a duplicate H1 of the filename.

This is the "treat differently" the request asked for: a serif measure and a numbered outline on article leaves, with GTD notes unchanged.

---

## 11. Alternatives rejected

**Community Number Headings as the formatter.** No type awareness, extra frontmatter settings, stale (2023), known loops on separators, eats digit-leading titles. Bob would still need a type marker and CSS. Two authorities.

**Auto Headings / Number Suite display-only, write-on-export.** Best-in-class for "pretty in Obsidian, clean in git." Wrong for a blog that agents edit and that wants numbers in the published Markdown. Adding them also puts heading policy outside bob-cli tests.

**Enable Linter `header-increment` + `heading-blank-lines` + custom regex numbering, scoped by folder.** Linter ignore lists are denylists, not allowlists. There is no "only these cssclasses" mode. Custom regex numbering will not be idempotent around fences and block IDs.

**`bob format` for every Markdown file.** Too tempting, too dangerous. The membership rule would be "all notes," which includes daily notes and projects.

**Make `sase_blog_contents` a project.** It would grow `^prj`, `## Tasks`, chips, Ready caps, and a walk slot. The post would stop being a post. The current parent/child split is the design.

**Put numbers in HTML comments or `{.n}` attributes.** Invisible in source readers; unsupported as first-class Obsidian heading syntax.

**Pandoc `--number-sections` at publish time only.** Fine as an *additional* publish step later. It does not help the vault, the agent, or the first use-case.

---

## 12. Risks

| Risk | Mitigation |
| --- | --- |
| Format-on-save fights Linter or jumps the Vim cursor | Idempotent rules that include Linter's YAML blank line; one editor transaction; save-only trigger |
| Numbering breaks `[[Note#Heading]]` | Strict prefix grammar; same-file link rewrite in v1; vault-wide rewrite in v1.1; prefer `^id` for durable cites |
| Year-leading titles get eaten | Trailing-dot grammar; fixture `## 2026 Roadmap` |
| Someone marks `sase_blog.md` as an article | `format` / `mark` refuse `#task`, `^prj`, `^ref`; project type stays exclusive |
| On-save spawn of `bob` is slow | Native command, one file, ~40–few-thousand lines; JSON in/out; skip spawn when type is not article (cheap frontmatter read in the plugin first) |
| Two types on one note | YAML `type` is a single field; do not allow `[[project]]` and `[[article]]` together |
| Agents invent a parallel `kind:` key | Type note + glossary strand at implementation time; `bob articles mark` is the blessed writer |
| Beauty CSS leaks into GTD notes | Every rule nested under `.bob-article`; class name prefixed |

---

## 13. Recommended solution

### Contract

A Bob **article note** is a vault Markdown file whose frontmatter has `type: "[[article]]"`. It has a `parent` like every other note. It does not carry `#task` / `^prj` / `^ref`. It may have checklists, footnotes, code fences, and a lede before the first heading. Its document title is the filename (optional override: first H1). Its sections are ATX headings, skip-repaired, numbered from 1 with dotted subsections, numbers stored in the heading text.

### v1 ship list

1. Vault: `article.md` (`parent: "[[type]]"`) describing the contract, plus `_templates/new_article.md`.
2. bob-cli: `frontmatter_is_article`, `bob articles {list,check,format,mark}`, line-oriented formatter with fixtures covering the blog file, fences, `2026 Roadmap`, skipped H4s, block IDs, and a project-note negative case.
3. bob-plugins: `bob-articles` plugin (styles + format-if-article + class injection + mark command).
4. Vault config: Linter `lintCommands` entry; enable the plugin via the usual `bob plugins sync` then Community plugins toggle.
5. Dogfood: `bob articles mark sase_blog_contents.md && bob articles format sase_blog_contents.md`.

### v1.1

- Vault-wide heading-link rewrite when numbers change.
- Muted outline-prefix span in Live Preview / Reading view.
- `bob articles candidates` (read-only: many headings, zero `#task`, untyped) as a discovery list, still not a writer.
- Optional `--typography` for heading `->` → `→`.
- Optional `bob-article-toc` fenced block that renders a TOC and is ignored by the heading scanner.

### v2

- Publish hook (numbers already in source, so this is mostly CSS/template).
- `article_kind` / extra cssclasses if design docs really want a denser face.
- Display-conceal as a view preference, numbers still in source.

### Implementation note for the next agent

The parser primitives already exist (`atx_heading`, fence tracking, `frontmatter_has_type`, `vault_links::NoteIndex`). The type picker already exists (Metadata Menu + `type.md` children). The on-save chime already exists (Linter). What does not exist is the type, the rewriter, the CSS class, and the refusal to run on GTD notes. That is a small feature if it stays inside those bounds, and a large mess if it becomes "prettier for the whole vault."

---

## Sources

Vault and code (primary):

- `~/bob/sase_blog_contents.md`, `~/bob/sase_blog.md`, `~/bob/why_sase.md`
- `~/bob/type.md` and type notes `area.md`, `project.md`, `ref.md`, `day.md`, `restaurant.md`, `podcast.md`, `done.md`
- `~/bob/_templates/new_note.md`, `new_project.md`
- `~/bob/.obsidian/plugins/obsidian-linter/data.json` (`lintOnSave: true`, heading rules off)
- `~/bob/.obsidian/plugins/metadata-menu/data.json` (type field query on `type.md` children)
- `~/bob/.obsidian/community-plugins.json`, `appearance.json`
- bob-cli `src/native/markdown.rs` (`atx_heading`, fences), `src/native/projects/scan.rs` (`frontmatter_has_type`), `src/runner.rs` (Vault section)
- bob-plugins `plugins/bob-project-tasks/main.js` (`isProjectType`)
- Glossary: Area Note, Project Note, Reference Note, Capture, Inbox File
- CLI rules memory; Obsidian vault conventions memory

External (not in Bryan's library; none of these need to be captured unless he wants them):

- Obsidian Help, Properties / `cssclasses` (list-valued as of 1.9; applied to source and preview views)
- Obsidian Forum, "Using cssclasses in snippets" (2025-05-11) and "Header counter" (2020–2022) on CSS counter limits in preview
- markdownlint MD001, heading-increment / W3C heading structure
- onlyafly/number-headings-obsidian README and changelog (1.16.0, 2023-10-03)
- AArlert/obsidian-auto-headings spec (display-only vs write-to-file, backlink sync)
- Number Suite plugin README (virtual numbers, concealment, write-on-demand)

Library check: 0 of 7 heading-numbering / Linter / cssclasses candidates already in the reference library (0 finished).
