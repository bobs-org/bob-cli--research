# Article Notes: Designating Prose Notes, Auto-Formatting Them, and Numbering Their Sections

_Researcher: cld · 2026-10-16 · Scope: bob-cli, bob-plugins, and the Bob vault (`~/bob`)_

> **Recommendation in one paragraph.** Add an **`article`** note type (`type: "[[article]]"`),
> alongside `area`, `project`, and `ref`. Give **bob** one Rust **article formatter**: a pure,
> line-based function that only changes layout. It never changes your words. It writes
> **section numbers into the heading text** as `1.`, `1.1.`, and `1.1.1.`. The numbers are
> derived from document order and owned by bob, so every run strips and rewrites them. Run it
> from four places: a thin Obsidian plugin (on save, when you leave the note, or from a
> command; it applies edits through the editor and never writes the open file from outside),
> `bob article fmt` for agents and scripts, and the nightly job. Keep in-note heading links
> pointing at the right section when numbers change. Show the numbers in a muted style in
> Obsidian. Leave out general Markdown "style" rules: emphasis style, typography, wrapping,
> and table alignment. They add churn and risk without adding structure.

Sections in this report are numbered with the proposed style.

---

## 1. What I examined

**The example note.** `~/bob/sase_blog_contents.md` has 40 lines and 253 body words. It holds
`parent` and `created` frontmatter and an unnumbered preamble of two paragraphs plus four
hand-written pseudo-footnotes (`[1]: TODO …`, `[a]: TODO …`). After that come 10 headings:
one `#`, seven `##`, and two `####`. Nine of the ten sections are `TODO` stubs. Some details
that matter for the design:

- The heading levels skip a level: `## Agent CLIs` is followed directly by `#### Skills, …`.
- One heading has a trailing space: `## VCS and workspace operations `.
- The spacing is inconsistent. There are two blank lines before the only `#` heading, and no
  blank line between a heading and its body.
- The top-level sections use `#` with no title heading, which is normal in this vault because
  the file name is the title.

**The vault's type system.** Notes declare `type: "[[X]]"`, and the link points at a type note
whose `parent` is `[[type]]` (`area.md`, `project.md`, `ref.md`, and so on). Current counts:
`day` 1196, `ref` 1053, `restaurant` 92, `project` 90, `done` 29, `podcast` 15, `area` 14.
`type.md` lists Bases such as `projects.base` and `refs.base`. Bob's Rust reader
`frontmatter_has_type` (`src/native/projects/scan.rs`) already accepts scalar and flow-list
types.

**Existing formatting in the vault.** Obsidian Linter 1.33.0 is installed with
`lintOnSave: true`, but only one rule is on: `add-blank-line-after-yaml`. Linter rules apply
to the whole vault. Files can only opt out, through `disabled rules`, so Linter cannot run a
rule set for one note type.

**Reusable bob-cli pieces:**

- `src/native/markdown.rs`: fence, ATX, setext, and HTML-comment helpers.
- `note_snapshot/classify.rs`: a `NoteKind` enum (`Ordinary | Area | Project | TerminalProject`)
  read from frontmatter.
- `highlights_ref/rename/links.rs`: a vault-wide inbound-link rewrite planner that returns
  `LineEdit` and `FileRewrite` plans.
- `bob ref create`: its plain-Markdown route passes pandoc `--number-sections --toc`. The
  vault-note snapshot route deliberately does not, and a test asserts that.

**Reusable bob-plugins patterns:**

- `bob-project-tasks` listens for `metadataCache "changed"`, waits 250 ms, then calls
  `processFrontMatter`.
- `bob-ledger-tools` runs `bob stats` with `execFile`, sets `BOB_DIR` and `NO_COLOR`, and only
  does so on desktop.
- `bob-navigation-hotkeys` maintains BLOCKS mirrors this way: same-note edits share the
  gesture's undo transaction, and cross-note updates run after the commit with a preimage
  check.

**Prior art.** I read the source of the Number Headings plugin (onlyafly) and read about
Section Numbering, Auto Headings, Header Enhancer, Heading Autolink, the Obsidian forum
threads on CSS heading counters and heading-link breakage, Obsidian's behaviour when a file
changes on disk, ISO 2145, Sphinx section numbering, and the RFC heading style.

**Experiments.** All of these ran on copies; nothing in the vault was touched.

1. A ~100-line Python prototype of the proposed formatter. Output on the real note is in §6.
   It was idempotent on the note and on an edge-case file.
2. Prettier 3.6.2 on Obsidian-flavored samples.
3. pandoc on the pseudo-footnote lines.

---

## 2. Is this a good idea?

**Yes, as long as two things hold:** the formatter stays narrow (layout and numbering only),
and the numbers are treated as derived data that bob owns, not as text you type.

Reasons it is worth doing:

1. **It gives you and your agents a shared way to point at sections.** Your blog workflow runs
   research swarms that "act on notes and polish". With numbers, "tighten §1.3, merge §1.4
   into §1.2" means the same thing to you in Obsidian, to an agent reading raw Markdown, to
   `git diff`, and in a printed PDF. This is the strongest argument for putting the numbers in
   the source rather than only drawing them on screen.
2. **Explicit opt-in fits the vault.** A one-line `type` matches how areas, projects, and refs
   already work. Your existing decisions consistently prefer explicit user-owned markers over
   inference.
3. **It is cheap given what bob already has.** The frontmatter, fence, heading, and link
   machinery already exists, and so does the plugin-calls-bob pattern.

What can go wrong, and how the design below handles each risk:

| Risk | Why it is real | Mitigation in this design |
| --- | --- | --- |
| Scope creep into a general Markdown formatter | Style rules invite endless debate and change text you care about | A "layout only, never words" rule, enforced by a runtime check (§4.7) |
| Numbers inside heading text break `[[note#heading]]` links | Obsidian matches the whole heading text. Editing a heading by hand does not update links; only the right-click "Rename heading" does ([forum](https://forum.obsidian.md/t/internal-links-to-headers-are-not-automatically-updated-with-header-changes/18423), [forum](https://forum.obsidian.md/t/automatic-inline-update-of-links-to-headers-and-blocks-when-they-are-modified-no-extra-dialog-window/25412?page=3)) | Number-insensitive link refresh. In-note links in v1, vault-wide links in phase 3 (§4.3, N7) |
| Writing the open note from outside Obsidian | Obsidian silently merges outside changes into unsaved edits, and there are reports of lost data ([changelog v0.11.6](https://obsidian.md/changelog/2021-03-09-desktop-v0.11.6/), [forum](https://forum.obsidian.md/t/obsidian-doesnt-reload-the-current-file-when-it-is-changed-outside-of-obsidian/114185)) | When the note is open, the plugin applies bob's edits through the editor API. The CLI writes atomically with a preimage check |
| Changing "which notes are articles" automatically | My scan found dozens of heading-heavy untyped prose notes (meeting notes, `prompts/sase_xpl.md`, `lit/*`). Renumbering a prompt note would change prompt text | Only an explicit `type` turns it on. Nothing infers article status |
| Numbered sections make a personal essay read like an academic paper | Blog posts rarely number their sections | Keep the numbers for drafting and collaboration. Because bob can always recognize its own numbers, an export can drop them (§7) |

**Would I take a different approach?** Same direction, with four changes from the obvious
version:

1. **bob owns the formatter.** Not an Obsidian plugin, Linter, or Prettier. Agents and the
   nightly job need it to run without Obsidian.
2. **The number format makes bob's own numbers unambiguous**, so bob never deletes a number
   you typed (`1.5 million users`, `2026 roadmap`).
3. **Formatting is layout only**, and every write is checked at runtime to prove no words
   changed.
4. **It never formats while you type.** It formats on save, when you leave the note, on a
   command, from the CLI, and nightly. Number Headings re-numbers the active note every 10
   seconds while you edit (`registerInterval(..., 10 * 1000)` in its `main.ts`). That is the
   behaviour to avoid.

---

## 3. Changes to your requirements (called out explicitly)

| # | Your requirement | Adjustment | Why |
| --- | --- | --- | --- |
| **A1** | "A way to specify that a file is an article" | Mark it with `type: "[[article]]"`, plus an `article.md` type note, `articles.base`, and a `_templates/new_article.md` template | Same idiom as area, project, and ref. The marker moves with the file, shows in the Properties UI, and Dataview, Bases, bob, plugins, and agents can all query it. A tag, folder, CSS class, or config list would add a second source of truth |
| **A2** | "Auto-format these files" | Narrowed to **layout only**. Words, inline markup, links (except heading-link refresh), line wrapping, and typography never change | This keeps the formatter trustworthy enough to run automatically. Style choices such as emphasis markers and smart quotes belong in publishing (pandoc `+smart`), not in your source |
| **A3** | (not requested) | **Normalize heading levels**: the shallowest heading becomes `#`, and skipped levels close up (your `##` → `####` becomes `##` → `###`) | Numbering needs a clean tree. It also gives a simple rule you can read off the page: the number of `#` marks equals the number of parts in the section number (`###` ⇔ `1.3.1.`) |
| **A4** | "Auto-number starting at 1 with sub-sections" | Style is **`1.` / `1.1.` / `1.1.1.`** with a trailing dot at every level (Sphinx, Python docs, RFC style). Depth defaults to 3 | The trailing dot is what lets bob recognize its own numbers safely (§4.3, N5). Below depth 3, numbers like `1.2.3.4.` get unreadable |
| **A5** | (not requested) | **Heading links follow the numbers.** In-note links are refreshed in v1. Links from other notes are refreshed in phase 3 | Without this, every renumber silently breaks links |
| **A6** | (not requested) | A separate **lint channel**: things that need judgment are reported, never auto-fixed (§4.4) | Examples: `#task` lines in an article, duplicate titles, and fragile pseudo-footnotes |
| **A7** | (implied: automatic) | Triggers are save, leaving the note, a command, the CLI, and nightly. **Never while typing** | Numbers that change under the cursor are disorienting. Numbers that might be stale need a visible signal (§4.6) |
| **A8** | — | **Deferred:** generated table of contents, footnote renumbering, lettered appendices, opting out single headings, typography | Each is reasonable later. None is needed for the first use case |

---

## 4. Design

### 4.1. Marking an article

```yaml
---
parent: "[[sase_blog]]"
type: "[[article]]"
created: 2026-10-15T15:10:41-04:00
# optional; default 3. `false` turns numbering off (and removes bob's numbers)
section_numbers: 3
---
```

- **Type note `~/bob/article.md`** (`parent: "[[type]]"`). It documents the contract in a few
  lines: "Articles hold authored prose with sections. bob formats their layout and numbers
  their sections. Tasks about an article live in its parent project or area note." Add an
  `## Articles ([[articles.base]])` block to `type.md`, matching the existing Projects and
  Reading List blocks.
- **Ways to create one.** All of them end at the same single marker:
  - the Templater template `_templates/new_article.md`;
  - a plugin command, **"Bob: Convert note to article"**, which sets `type` and formats once;
  - editing the property by hand.
- **Articles should not also be projects.** Bob's parser accepts `type: ["[[project]]",
  "[[article]]"]`, but the clean pattern is the one you already use: a project note holds the
  `^prj` task and `## Tasks` (`sase_blog`), and an article note holds the prose and links to
  it through `parent` (`sase_blog_contents`). The glossary already requires every `#task` to
  live in an area or project note, so the formatter flags `#task` lines in an article instead
  of tolerating them.
- **Name.** `article` is concrete and covers blog posts and design docs. It also pairs
  naturally with `ref`: refs are things you read, articles are things you write. I rejected
  `doc`, which is too generic (every note is a doc) and collides with "docs".

### 4.2. Architecture: bob decides, the plugin applies

```
                        ┌──────────── bob (Rust) — single source of truth ───────────┐
 Obsidian plugin ──────▶│ article::format(text, ctx) -> FormatPlan                   │◀── bob article fmt (agents, you)
 (stdin + --format json)│   1 scan blocks   (frontmatter, fences, $$, %%, HTML, >)   │◀── bob nightly (athena)
                        │   2 heading tree  (normalize levels)                       │
                        │   3 numbering     (strip owned tokens, renumber)           │
                        │   4 layout        (blank lines, whitespace, EOF)           │
                        │   5 link refresh  (in-note heading links)                  │
                        │   6 verify        (idempotent + word-preservation)         │
                        └────────────────────────────────────────────────────────────┘
 FormatPlan = { changed, edits: [line ranges → text], text, summary, lints[], inbound_rewrites[] }
```

- **The core is a pure function.** Text goes in and a plan comes out, with no I/O, so it is
  trivial to test and safe to call from anywhere. The CLI wraps it with atomic, preimage-checked
  writes. The plugin wraps it with an editor transaction.
- **The plugin is a thin client.** It sends the buffer on stdin, receives `edits`, checks that
  the buffer has not changed since it sent it, and applies everything as **one CodeMirror
  transaction**. That gives one vim `u` to undo, keeps the cursor and folds in place, and
  never writes the file behind the editor's back. Cross-note link rewrites (phase 3) follow
  the BLOCKS-mirror pattern: they run after the same-note commit, using `vault.process` with a
  preimage check. This is the same arrangement as the
  `mac-capture-is-a-thin-client` decision: bob owns the rules, and the clients render and
  apply. A JavaScript reimplementation would drift from the Rust one.
- **Why not plugin-only:** agents edit `~/bob` without Obsidian running. The nightly job and
  `--check` also need the same rules.

### 4.3. Section-numbering rules

**N1. What counts as a section.** An ATX heading (`#` to `######`) at the top level of the
body. It must not be inside frontmatter, code fences, `$$` math, `%% %%` comments, HTML
blocks, blockquotes or callouts, or list items. A setext heading (`Title` over `===` or
`---`) is a real heading by the CommonMark spec and in Obsidian, so it is converted to ATX
form and numbered like any other.

**N2. Preamble.** Text before the first heading is the unnumbered lede. Your intro stays as
it is.

**N3. Level normalization.** Keep a stack of (original level, new level). For each heading,
pop entries whose original level is at least the heading's level. The new level is the
top entry's new level plus one, or 1 if the stack is empty. Result: the shallowest heading
becomes `#`, skipped levels close up, and the tree shape is preserved. Heading links do not
contain `#` counts, so this never breaks a link.

**N4. Numbers.** Each depth up to D (default 3) gets a counter, and deeper counters reset
when a shallower heading appears. Numbers render as `1.`, `1.2.`, `1.2.3.`. Headings deeper
than D are written without numbers.

**N5. Which numbers belong to bob.** On every heading, at every depth, a leading token that
matches `^(?:\d{1,3}\.)+[ \t]+` (one or more groups of digits, each followed by a dot, then
whitespace) is bob's. Bob strips it and writes the correct number, or nothing beyond depth D.
The prototype shows what this means in practice:

| You type | Result (`##` heading, depth 2) | Why |
| --- | --- | --- |
| `## 2026 Roadmap` | `## 1.1. 2026 Roadmap` | No trailing dot, so this is your text |
| `## 1.5 million users` | `## 1.1. 1.5 million users` | Last group has no trailing dot, so this is your text |
| `## 3. Reasons I quit` | `## 1.1. Reasons I quit` | Matches the token. A typed number in a numbered article is treated as stale |
| `## 3\. Reasons I quit` | `## 1.1. 3\. Reasons I quit` | Backslash escape, standard CommonMark, renders as `3.` |
| `## 2.1. Moved section` (moved) | `## 1.4. Moved section` | Stale number replaced |

**Why `1.1.` and not ISO 2145 `1.1`.** ISO 2145 puts no full stop after the last number
([ISO 2145](https://en.wikipedia.org/wiki/ISO_2145)), and it is the more classical
typography. The problem is ownership. Without a trailing dot, `1.5 million users` and
`2026 Roadmap` look exactly like section numbers, so an automatic formatter would delete your
words. That is precisely the known flaw in Number Headings, which strips any leading
`([0-9]+\.)*([0-9]+)?` (its `textProcessing.ts`). The Section Numbering plugin had to add a
separator option to protect years
([obsidianstats](https://www.obsidianstats.com/plugins/section-numbering)). The trailing-dot
style has strong precedent: Sphinx's default `html_secnumber_suffix` is `". "`, which gives
the Python docs headings like "2.1.1. Argument Passing"; RFCs use `1.1.` too; and a 2003 note says Word
added a final full stop by default
([W3C note](https://lists.w3.org/Archives/Public/www-html-editor/2005JulSep/0003.html)). The
extra dot costs very little visually, especially once the numbers are styled faintly (§4.6).
In exchange, bob can never mistake your words for its numbers.

**N6. Heading text.** The text becomes the number, one space, and your title. Bob removes
trailing whitespace and closing `#` marks and changes nothing else in the title (it does not
turn `->` into `→`).

**N7. Link refresh.** A link fragment matches a heading if the two are equal after removing
bob's number token from both (Obsidian's own punctuation-stripping comparison also applies
[(forum)](https://forum.obsidian.md/t/headings-with-special-characters-have-broken-links-and-renaming/40707)).

- Bob rewrites in-note links (`[[#1.2. Beads -> Sidecar repos]]`) and self-links
  (`[[sase_blog_contents#…]]`) so they carry the current number. Nested chains such as
  `[[#1. The Abstractions#1.3. Agent CLIs]]` are refreshed part by part.
- Ambiguous matches are reported, not rewritten.
- Because matching ignores numbers, links survive any renumbering. Numbering also makes
  heading titles unique within the note, which fixes Obsidian's first-match ambiguity for
  repeated titles.
- Phase 3 extends the same rule to inbound links from other notes by reusing the planner in
  `highlights_ref/rename/links.rs`. The vault has about 2.4k heading links overall (many from
  the zorg era) and none pointing into this article yet, so in-note refresh is enough for v1.

**N8. Turning numbering off.** `section_numbers: false` removes bob's tokens. Toggling is
therefore reversible, and both states are idempotent. To make bob leave a note alone
entirely, remove the `article` type.

### 4.4. Formatting rules

**Principles.**

- **P1. Layout, never language.** The sequence of words is unchanged apart from bob's number
  tokens, and this is checked at runtime (§4.7).
- **P2. Line-based surgery, never re-printing the whole file.** Untouched lines stay
  byte-identical. Obsidian syntax (`[[…]]`, `![[…]]`, `%%…%%`, `==…==`, `[key:: v]`, `^id`,
  callouts, `$$`) is never re-serialized.
- **P3. Idempotent and deterministic.** Formatting twice equals formatting once, and every
  machine produces the same bytes, so concurrent formatting on athena, apollo, and the Mac
  merges cleanly in git.
- **P4. Derived content is overwritten; authored content is preserved.** Section numbers are
  derived; everything else is authored.
- **P5. When unsure, report instead of fixing.**
- **P6. Silent when there is nothing to do.** A notice appears only when something changed.

**Fixes (applied automatically):**

| ID | Rule | Example | Why |
| --- | --- | --- | --- |
| F1 | Exactly one blank line between frontmatter and body. Frontmatter itself is untouched | — | Agrees with your Linter rule, so the two never fight. Obsidian's Properties UI owns the YAML |
| F2 | Headings in ATX form: `#…# ␠Title`; closing `#`s and trailing whitespace removed; setext converted | `## VCS and workspace operations␠` → `## 1.4. VCS and workspace operations` | One heading syntax makes the source predictable for you and agents |
| F3 | Heading levels normalized (N3) | `####` under `##` → `###` | Gives a clean tree. A3 |
| F4 | Section numbers (N4–N8) | `## Beads` → `## 1.2. Beads` | Your first use case |
| F5 | **Vertical rhythm.** Two blank lines before every `#` section (unless it opens the body), one before deeper headings, one after every heading | see §6 | Matches the instinct already visible in your draft (two blank lines before `# The Abstractions`) and PEP 8's spacing between top-level definitions. In Live Preview, top-level sections then read as chapters. Reading view collapses it, so rendering does not change |
| F6 | Runs of blank lines elsewhere shrink to one (never inside fences, math, comments, or HTML) | — | Removes accidental gaps. Does not change whether a list is tight or loose |
| F7 | Trailing whitespace removed outside fences | — | Your vault keeps Obsidian's default of strict line breaks off, so two trailing spaces mean nothing there. You write one paragraph per line, so the published CommonMark rendering is unaffected too |
| F8 | No leading blank lines; exactly one `\n` at the end of the file | — | Clean diffs |
| F9 | In-note heading-link refresh (N7) | `[[#Beads -> Sidecar repos]]` → `[[#1.2. Beads -> Sidecar repos]]` | Numbers never break links |

**Lints (reported, never fixed):**

| ID | Finding | Suggested action |
| --- | --- | --- |
| L1 | A `#task` checkbox inside an article | Move it to the parent project with Ctrl+Shift+M |
| L2 | **Fragile pseudo-footnote.** A line like `[c]: TBD` on its own becomes a *hidden* link definition, which turns `X[c]` into a link to "TBD". I confirmed this with pandoc. Your `[1]: TODO: Add …` lines render only because the trailing words make the definition invalid | Use Obsidian footnotes `[^1]`, which render properly (phase 3 can number them) |
| L3 | Heading or footnote reference with no target in this note | Fix or remove it |
| L4 | Empty or `TODO` sections (count and list) | A progress signal: "9 of 10 sections are stubs" |
| L5 | Headings deeper than `section_numbers` | Informational |
| L6 | Fence never closed (everything after it is code) | Usually a typo; the formatter changes nothing after it |

**Rules rejected, and why:**

| Rule | Verdict |
| --- | --- |
| Paragraph rewrapping or semantic line breaks | **No.** Obsidian renders single newlines as breaks, wrapping makes diffs noisy, and soft wrap already works |
| Emphasis or strong style (`*x*` vs `_x_`) | **No.** Inline parsing is where Obsidian syntax breaks, and the value is cosmetic. Prettier 3.6.2 rewrote `*emphasis*` → `_emphasis_` and `__strong__` → `**strong**` on my sample |
| Smart typography (`->` → `→`, quotes, dashes) | **No in source.** It changes words. Do it when publishing (pandoc `smart`) |
| Table column alignment | **Later at most.** Live Preview renders tables anyway. Prettier pads every cell, so editing one cell rewrites the whole table |
| List marker normalization (`*`/`+` → `-`) | **Later at most.** Low value. Changing markers can merge two adjacent lists into one; Prettier alternated markers to avoid exactly that |
| Generated table of contents in the source | **No.** It churns on every edit. Obsidian's Outline pane already shows the numbered tree for free, because the numbers are in the source |

### 4.5. Triggers and UX

**In Obsidian (new plugin `bob-articles` in bob-plugins, active only for article notes):**

- **On save.** Ctrl+S or vim `:w`. The plugin wraps the `editor:save-file` command the way
  Linter's lint-on-save does. The two run in either order and reach the same result (F1).
- **On leaving the note** (`active-leaf-change`). The editor is gone by then, so the plugin
  applies the plan with `vault.process`.
- **Commands:**
  - "Bob: Format article";
  - "Bob: Convert note to article";
  - "Bob: Copy section reference" (copies `§1.3 Agent CLIs` or a `[[note#1.3. …]]` link,
    which is handy when talking to agents).
- **Notice, only when something changed:** `Article formatted · renumbered 4 sections · 2
  links refreshed`. Lints appear as a second line, such as `L2: fragile footnote [c] (line
  12)`.
- **Mobile:** does nothing, because Obsidian mobile cannot start a subprocess. The next
  desktop save or the nightly run catches up.

**CLI (follows `cli_rules`: sorted options, a short alias for each, colored output, bare group
runs a read-only member):**

```text
$ bob article --help
Format and inspect article notes (frontmatter type: "[[article]]")

Usage: bob article [COMMAND]

Commands:
  fmt      Normalize layout and renumber sections in article notes
  list     List article notes (default)
  outline  Print an article's numbered section outline

$ bob article fmt --help
Usage: bob article fmt [OPTIONS] [PATH]...

Options:
  -a, --all            Format every article note in the vault
  -b, --bob-dir DIR    Vault root (default: $BOB_DIR, then ~/bob)
  -c, --check          Exit 1 if any note would change; write nothing
  -d, --dry-run        Print the unified diff; write nothing
  -f, --format FMT     human (default) | json
  -s, --stdin          Read one note's text from stdin; PATH names it; print the plan
```

```text
$ bob article outline sase_blog_contents
sase_blog_contents · article · 253 words · 10 sections · 9 TODO

  ¶       Preamble                                                    186 w
  1.      The Abstractions                                              0 w
  1.1.    Gates -> Plans -> Epics                                    TODO
  1.2.    Beads -> Sidecar repos                                     TODO
  1.3.    Agent CLIs                                                 TODO
  1.3.1.  Skills, **memory**, provider interface, NOT hooks          TODO
  1.3.2.  Agent presentation / organization (tribes, clans, …)       TODO
  1.4.    VCS and workspace operations                               TODO
  …
```

`outline --format json` gives each section's number, title, line range, and word count. That
lets an agent act on "rewrite §1.3" precisely, and `bob article fmt <path>` afterwards keeps
the numbering correct.

**Agents and automation.**

- Add one line to the vault's `AGENTS.md`: "After editing a note whose `type` is
  `[[article]]`, run `bob article fmt <path>`."
- `bob nightly` on athena runs `bob article fmt --all` between its two `vault-sync` runs.
  Formatting is deterministic, so other machines' copies merge cleanly.

### 4.6. Making it look good

- **In the source:** the vertical rhythm of F5, numbers that line up with heading depth, and
  one space before the title.
- **Live Preview:** a small CodeMirror decoration wraps bob's number token in
  `span.bob-secno`:

  ```css
  .bob-article .bob-secno {
    color: var(--text-faint);
    font-weight: var(--font-normal);
    font-variant-numeric: tabular-nums;
    margin-inline-end: 0.15em;
  }
  .bob-article .bob-secno.is-stale {
    color: var(--text-accent);
    text-decoration: underline dotted;
  }
  ```

  The titles stay prominent and the numbers sit in the background. **Stale numbers are
  visible:** if you move a section and have not saved yet, the decoration compares each
  heading's number with the number it should have and marks any mismatch, so a number on
  screen is either correct or visibly stale.
- **Reading view:** numbers **hang in the left margin**, so all titles line up on one edge,
  the way good typography handles numbered sections. A post-processor wraps the token, and
  CSS positions it to the right of the margin edge. Narrow panes fall back to inline numbers.
  The plugin adds the `bob-article` class to the view based on `type`, so you never need a
  separate `cssclasses` entry.
- **Status bar:** shows `§ 1.3.1` for the section under the cursor, in article notes only.
- **Why not CSS counters only?** That approach is broken in Obsidian's preview, which wraps
  and lazily renders sections, so numbers reset as you scroll. A staff member said a working
  CSS heading counter is not currently possible
  ([forum](https://forum.obsidian.md/t/header-counter/3525?page=2)). Decorations computed from
  the whole document avoid that problem, but numbers that exist only on screen are invisible
  to agents, git, PDF export, and the Outline pane. Use decorations for **styling**, not as
  the source of the numbers.

### 4.7. Reliability guarantees

1. **Idempotent:** `fmt(fmt(x)) == fmt(x)`. This is a property test over a corpus, and the
   prototype already met it on both inputs.
2. **Word preservation, checked at runtime.** Before writing, compare the sequence of
   non-whitespace tokens, ignoring heading `#`s and bob's number tokens. If they differ, write
   nothing and report an internal error. This is what turns "never changes your words" from a
   claim into a guarantee.
3. **Regions bob never edits:** frontmatter, fenced code, `$$` math, `%%` comments, HTML
   blocks, blockquote and callout bodies, tables, and list items, apart from whole-line
   blank-line handling *between* blocks.
4. **Preimage checks.** The plugin applies edits only if the buffer still matches what it
   sent. The CLI uses atomic writes with a content-hash preimage, the same discipline as
   `bob capture`'s all-or-nothing planner.
5. **Skipped:** `_conflicts/`, `_templates/`, files with git conflict markers, and files whose
   frontmatter will not parse. Each skip comes with a reason.
6. **Tests:**
   - golden fixtures, including the current `sase_blog_contents.md`;
   - an Obsidian syntax corpus covering wikilinks, embeds, callouts, comments, math, inline
     fields, block IDs, and tags;
   - a fuzz-style run that formats **every** vault note as if it were an article in
     `--check` mode, asserting idempotency, word preservation, and no edits inside opaque
     regions;
   - help-output snapshot tests, following bob's existing conventions.

---

## 5. Alternatives considered

| Option | Verdict | Reason |
| --- | --- | --- |
| **CSS counters** (via `cssclasses`) | Rejected | Wrong numbers in Obsidian's preview modes ([forum](https://forum.obsidian.md/t/header-counter/3525)). Invisible to agents, git, export, and the Outline pane |
| **Numbers drawn only by plugin decorations** | Runner-up, partly adopted for styling | Correct and causes no churn, but numbers that exist only on screen defeat the main purpose: agents and you referring to the same "§1.3" |
| **Number Headings plugin** | Rejected | Polls every 10 s and rewrites the active note while you type. Its strip pattern eats leading years and decimals. No link maintenance. Last change 2023-10-03. Plugin-only, so no headless runs. Its frontmatter switch (`number headings: auto, …`) is the one good idea, and `type` plus `section_numbers` covers it |
| **Auto Headings / Header Enhancer** | Rejected | They do maintain backlinks (per their listings), but they are plugin-only, hold their own rule sets, and are unproven in this vault ([Auto Headings](https://www.obsidianstats.com/plugins/auto-headings), [Header Enhancer](https://community.obsidian.md/plugins/header-enhancer)) |
| **Obsidian Linter rules** | Rejected | Rules cannot be scoped to a note type, there is no numbering rule, and it is plugin-only. Keep it for its one vault-wide rule |
| **Prettier, mdformat, or dprint over the whole file** | Rejected | Prettier 3.6.2 handled wikilinks, callouts, `%%`, and math well with `--prose-wrap preserve`, which is better than I expected. It is still the wrong tool: it cannot be scoped to a type, cannot number, re-prints the whole file with fixed style opinions, and would add Node to bob's headless path |
| **A general `bob fmt` that picks a profile per note type** | Deferred | It might be the right shape eventually. With one profile today, a `bob article` group is clearer, and moving the core into a shared `fmt` module later costs nothing |
| **Writing outside Obsidian** (Quarto, Typst, LaTeX) | Rejected | Leaves the vault, links, tasks, and capture behind |
| **Recommended: bob-owned layout-only formatter with derived in-source numbers, plus a thin plugin** | ✅ | §4 |

---

## 6. Worked example: `sase_blog_contents.md` (prototype output, from a copy)

Running the throwaway prototype (F2–F8, N3–N5) on a copy of the note changes only heading
lines and blank lines. The preamble and pseudo-footnotes are byte-identical, and a second run
changes nothing:

```diff
 [b]: TODO: Update commit/line counts!
 
 
-# The Abstractions
-## Gates -> Plans -> Epics
+# 1. The Abstractions
+
+## 1.1. Gates -> Plans -> Epics
+
 TODO
 
-## Beads -> Sidecar repos
+## 1.2. Beads -> Sidecar repos
+
 TODO
 
-## Agent CLIs
+## 1.3. Agent CLIs
+
 TODO
-#### Skills, **memory**, provider interface, NOT hooks
+
+### 1.3.1. Skills, **memory**, provider interface, NOT hooks
+
 TODO
-#### Agent presentation / organization (tribes, clans, families, hoods, metadata/files/tools panel)
+
+### 1.3.2. Agent presentation / organization (tribes, clans, families, hoods, metadata/files/tools panel)
+
 TODO
 
-## VCS and workspace operations 
+## 1.4. VCS and workspace operations
+
 TODO
 …
-## Routines and Jobs
+## 1.7. Routines and Jobs
+
 TODO
```

What this example shows:

- **Every section currently sits under `1.`** because the draft has a single top-level
  section. That is accurate, and it will spread out as you add top-level sections such as
  "Why I built it" or "What I learned". If you would rather "The Abstractions" sections were
  top-level (`1.`–`7.`), that is an outline decision: promote them to `#` and the numbers
  follow.
- **L2 would flag nothing yet,** because every pseudo-footnote line has trailing words.
  Adding a standalone `[c]: TBD` would trigger it.
- The real formatter would also add `type: "[[article]]"` (A1) when you run "Convert note to
  article".

---

## 7. Integration notes and side effects

- **`bob ref create` on articles.** The plain-Markdown route passes `--number-sections`, so an
  article *outside the vault* would print with double numbers (`1 1. The Abstractions`). Vault
  notes take the snapshot route, which correctly skips numbering. Fix: if the source's `type`
  is article, never pass `--number-sections`. Also add `NoteKind::Article` to
  `note_snapshot/classify.rs` so the print profile can render articles nicely, for example
  with a contents page.
- **Publishing.** Because bob can always recognize its own numbers, `bob article export
  --strip-numbers` (or a pandoc Lua filter) can drop them for the published post if you
  prefer an unnumbered blog. The same applies to narration (`--listen`), where "one point
  three point one" adds nothing.
- **Capture.** Articles are not capture targets because they are neither areas nor projects.
  A later, optional addition: `@sase_blog_contents#1.3` appends an idea bullet into a
  section.
- **Linter.** The two agree on the blank line after frontmatter, so they never undo each
  other.
- **Git merges.** Inserting a section renumbers every later heading line. That churn is
  inherent and deterministic. If two edits conflict on heading lines, keep either side and
  run `bob article fmt` again.
- **Memory (after you accept).** Add a glossary term **Article Note** and a decision record
  such as "Article section numbers are derived and bob-owned (`1.1.` style)", through
  `/sase_memory_write`. I have not changed any memory.

---

## 8. Phased plan

| Phase | Repo | Scope | Size |
| --- | --- | --- | --- |
| **0. Vault** | `~/bob` | `article.md` type note, `articles.base`, `_templates/new_article.md`, `type: "[[article]]"` on `sase_blog_contents.md`, one line in the vault's `AGENTS.md` | S |
| **1. Core and CLI** | bob-cli | `src/native/article/` (block scanner reusing `markdown.rs`, heading tree, numbering, layout, in-note link refresh, both invariants), `bob article {list, outline, fmt}` with `--check`, `--dry-run`, `--stdin`, `--format json`, `docs/article.md`, and the fixture, corpus, and fuzz tests | M |
| **2. Plugin** | bob-plugins | `bob-articles`: format on save and on leaving the note through the bob JSON plan, applied as one transaction; muted, stale-aware number decoration; hanging numbers in reading view; `§` status item; the three commands; then `bob plugins sync` | M |
| **3. Hardening and extensions** | both | Inbound heading-link rewrites across the vault (reusing `rename/links.rs`), nightly `--all`, `NoteKind::Article` and the `ref create` flag fix, numeric footnote renumbering (`[^n]` by first use, definitions moved to the end), optional `export --strip-numbers` | M |

Phases 0–2 deliver the full experience for `sase_blog_contents.md`. Phase 1 is useful on its
own, because agents can run `bob article fmt` right away.

---

## 9. Open questions for you

1. **Trailing-dot style (`1.1.`)?** It is my recommendation because it makes bob's numbers
   unambiguous. If you strongly prefer ISO `1.1`, the cost is a guarded rule (numbers
   without a final dot count as bob's only when they have two or more parts) plus one
   documented escape for titles that start with a decimal, like `1\.5 million`.
2. **Depth 3 by default?** Your draft goes three levels deep (`1.3.1.`), which fits.
3. **Two blank lines before top-level sections (F5)?** I inferred this from your draft. One
   blank line everywhere is the conservative alternative.
4. **Keep the numbers in the published post?** This decides whether `export
   --strip-numbers` needs to be built.

---

## 10. Recommended solution

**Build an `article` note type with a layout-only formatter that bob owns and that writes
derived section numbers, plus a thin Obsidian plugin.**

1. **Marker:** `type: "[[article]]"`, with an `article.md` type note, `articles.base`, and a
   template. It is opt-in only and never inferred.
2. **Engine:** a pure Rust function in bob-cli that scans blocks, normalizes heading levels,
   numbers sections, applies layout rules F1–F9, refreshes in-note heading links, and checks
   idempotency and word preservation before every write. It is exposed as
   `bob article {list, outline, fmt}` with `--check`, `--dry-run`, `--stdin`, and
   `--format json`.
3. **Numbers:** `1.` / `1.1.` / `1.1.1.`, three levels deep by default, rewritten on every
   run. A leading `(\d+\.)+` token is bob's; any other leading number is yours. Override per
   note with `section_numbers: N | false`.
4. **Triggers:** the Obsidian plugin applies bob's plan as one undoable transaction on save,
   when you leave the note, or on a command. Agents run `bob article fmt <path>`, and the
   nightly job runs it on every article. Nothing changes while you type.
5. **Beauty:** chapter-like spacing in the source, faint tabular numbers in Live Preview with
   stale numbers marked, hanging numbers in reading view, a `§ 1.3.1` status item, and a
   colored `bob article outline`.
6. **Not included:** paragraph wrapping, emphasis or typography rewrites, table alignment,
   and a generated table of contents. Footnote renumbering and links from other notes come
   later.

This gives you numbered, consistently laid-out articles in which you and every agent can
say "§1.3" and mean the same thing. It cannot delete a word, it never fights your cursor,
and it costs one frontmatter line per note.

---

## Sources

- Obsidian forum, CSS heading counters do not work reliably in preview: [Header counter](https://forum.obsidian.md/t/header-counter/3525), [page 2](https://forum.obsidian.md/t/header-counter/3525?page=2), [CSS for numbered headers in live preview](https://forum.obsidian.md/t/css-for-numbered-headers-in-live-preview/40347)
- Obsidian forum, heading links break unless headings are renamed through the dedicated command: [Internal links to headers are not updated](https://forum.obsidian.md/t/internal-links-to-headers-are-not-automatically-updated-with-header-changes/18423), [Automatic update of links to headers (p.3)](https://forum.obsidian.md/t/automatic-inline-update-of-links-to-headers-and-blocks-when-they-are-modified-no-extra-dialog-window/25412?page=3), [Update links after automatic rename](https://forum.obsidian.md/t/update-links-to-section-headings-after-automatic-rename/24016), [Mini plugin: update links when renaming headings](https://forum.obsidian.md/t/mini-plugin-update-internal-links-when-renaming-headings/86850)
- Obsidian forum, punctuation stripped when matching heading links: [Headings with special characters](https://forum.obsidian.md/t/headings-with-special-characters-have-broken-links-and-renaming/40707), [Support special characters in headings](https://forum.obsidian.md/t/support-special-characters-in-headings-for-linking/40724); [Obsidian Help: Internal links](https://obsidian.md/help/links)
- Obsidian, external modifications merged into unsaved edits: [Desktop v0.11.6 changelog](https://obsidian.md/changelog/2021-03-09-desktop-v0.11.6/), [Toggle to disable automatic merging](https://forum.obsidian.md/t/editor-add-a-toggle-to-disable-automatic-merging-of-changes-non-obsidian-sync/14874/), [File not reloaded after external change](https://forum.obsidian.md/t/obsidian-doesnt-reload-the-current-file-when-it-is-changed-outside-of-obsidian/114185), [Modified externally, merging changes](https://forum.obsidian.md/t/has-been-modified-externally-merging-changes-automatically/111594)
- Heading-numbering plugins: [Number Headings (community)](https://community.obsidian.md/plugins/number-headings-obsidian), [Number Headings (obsidianstats)](https://www.obsidianstats.com/plugins/number-headings-obsidian), [Section Numbering](https://www.obsidianstats.com/plugins/section-numbering), [Auto Headings](https://www.obsidianstats.com/plugins/auto-headings), [Header Enhancer](https://community.obsidian.md/plugins/header-enhancer), [Heading Autolink](https://community.obsidian.md/plugins/heading-autolink), [HeadNumatic](https://community.obsidian.md/plugins/headnumatic), [Auto Numbered Headings](https://community.obsidian.md/plugins/auto-numbered-headings)
- Number Headings source (opened read-only as an external repo with `sase repo open gh:onlyafly/number-headings-obsidian`): `src/textProcessing.ts` (strip pattern), `src/main.ts` (10 s auto interval), `src/frontMatter.ts` (`number headings:` key); last commit 4cd3fac, 2023-10-03
- Numbering conventions: [ISO 2145 (Wikipedia)](https://en.wikipedia.org/wiki/ISO_2145), [W3C note on full stops after section numbers](https://lists.w3.org/Archives/Public/www-html-editor/2005JulSep/0003.html), [Sphinx `html_secnumber_suffix` (config dump showing `'. '`)](https://connect-to-another-repo.readthedocs.io/en/latest/sphinx-context.html)
- Linting references: [Obsidian Linter](https://community.obsidian.md/plugins/obsidian-linter), [markdownlint rules (MD001 header-increment, MD012, MD022)](https://github.com/DavidAnson/markdownlint/blob/v0.4.1/doc/Rules.md)
- Local evidence: the bob-cli source files named in §1; bob-plugins (`bob-project-tasks/main.js`, `bob-ledger-tools/src/236-plugin-stats-data.js`, README BLOCKS-mirror section); vault `.obsidian/plugins/obsidian-linter/data.json`, `.obsidian/app.json`, `type.md`, `project.md`, `area.md`; experiments with Prettier 3.6.2, pandoc (CommonMark), and the prototype, all run on copies under `/tmp`
