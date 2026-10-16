# Article Notes: Typed Long-Form Notes With Bob-Owned Formatting and Section Numbers

_Lead-researcher consolidation · 2026-10-16 · Inputs: five independent reports (cdx, cld,
grk, mus, gem), plus my own checks this turn against the vault, bob-cli, and bob-plugins,
and a prototype run on copies. Nothing in `~/bob` was changed._

> **Recommendation.** Mark long-form notes with **`type: "[[article]]"`**, the same field
> that areas, projects, and refs already use. Give **bob** one Rust **article formatter**.
> It is a pure function that changes layout and never changes your words. It writes
> section numbers **into the heading text**, in the numbering style Bryan's docs already
> use: `1.` for top-level sections and `1.1` / `1.1.1` below them. bob owns those numbers:
> every run strips the old number and writes the correct one. A thin **`bob-articles`**
> Obsidian plugin calls bob when you save (`:w`), when you leave the note, or from a
> command, and applies the result as one undoable edit. It also gives articles their own
> look: a calm reading measure, quiet tabular section numbers, and a `§ 1.3.1` status
> item. Agents and scripts run `bob articles format`. In-note heading links follow the
> numbers; links from other notes follow in a later phase. Leave general Markdown style
> alone: wrapping, emphasis markers, title case, table alignment, and moving footnotes.

This report uses the numbering it proposes.

---

## 1. Where the five reports agreed, split, and where I landed

All five reports say **yes, build it**. All five scope it to an **explicit, per-file
opt-in** and reject inferring it from headings, folders, or file names. All five forbid
**prose reflow** and keep fenced code, math, comments, wikilinks, and block IDs out of the
formatter's reach. They split on six decisions:

| Decision | cdx | cld | grk | mus | gem | **Consolidated** |
| --- | --- | --- | --- | --- | --- | --- |
| Marker | `bob_document: true` | `type: "[[article]]"` | `type: "[[article]]"`, plus `cssclasses` written to YAML | `doctype: article` | `type: "[[article]]"`, plus `design-doc`/`essay`/`rfc` types | **`type: "[[article]]"`**; the plugin adds the CSS class at runtime |
| Where numbers live | Display-only editor widgets; numbered export copy | Source | Source | View (CSS counters) plus export | Contradictory: "virtual by default" (R1), but its worked example writes them into the source | **Source, owned by bob** |
| Number style | `1` / `1.1` | `1.` / `1.1.` / `1.1.1.` | `1.` / `1.1.` | `1` / `1.1` | `1` / `1.1` | **House style: `1.` / `1.1` / `1.1.1`** (§2.1) |
| Skipped levels (H2 → H4) | Number by ancestry, warn, never edit | Normalize, and promote the shallowest level to `#` | Pull up | Clamp, warn, `--fix-levels` | Normalize | **Close gaps by pulling headings up; keep the author's top level** |
| Title vs. first H1 | Adoption preview picks | The file name is the title | The file name is the title; `article_title: h1` option | H1 is an unnumbered title | Auto-detect | **The file name (or `title:`) is the title; every heading is a section** |
| Formatter scope | Whitespace only | Layout plus lints | Structure plus whitespace | Broad (lists, emphasis, rules) | 10 rules, including title case, table alignment, and moving footnotes | **Layout plus lints** (§5.3) |
| Engine | JavaScript core in a plugin; CLI later | Rust in bob plus a thin plugin | Rust plus a thin plugin | Rust CLI plus CSS | Rust plus a plugin | **Rust in bob plus a thin plugin** |

The two decisions that matter most are **source vs. display numbering** and **number
style**. My own research found evidence that none of the five reports used (§2.1). It
settles the style question and tips the source-vs-display question.

---

## 2. What I verified this turn

### 2.1 Bryan's writing already has a numbering house style, and it is not `1.1.`

I counted numbered headings in the documents Bryan and his agents already write:

| Corpus | Top-level `## 1.` | Top-level `## 1` | Sub-level `### 1.1` | Sub-level `### 1.1.` |
| --- | ---: | ---: | ---: | ---: |
| bob-cli `docs/` (e.g., `task-dependencies.md`, `freshness.md`) | 28 | 0 | 77 | 0 |
| research repo | 2,211 | 1 | 2,036 | 18 |
| plans repo | 1,150 | 0 | 92 | 0 |

The house style is plain: **`1.` at the top level and `1.1`, `1.1.1` below**. Two
consequences follow:

- **cld's and grk's trailing-dot style (`1.1.`) would make articles the odd one out.** It
  appears in 18 of about 2,200 sub-level headings.
- **The trailing dot does not deliver the safety it was chosen for.** cld and grk picked
  `1.1.` so bob could tell its numbers from the author's text. But agents, and Bryan,
  write `### 2.1 Foo` out of habit, as the 2,205 examples above show. Under a strict
  trailing-dot rule, an agent that adds `## 1.4 New section` gets `## 1.5. 1.4 New
  section`. grk noticed this and loosened its rule to also strip `1.1 `. That
  loosened rule also strips `1.5` from `1.5 million users`, which is exactly what the
  trailing dot was meant to protect. My prototype confirmed both failures (§7).
  Recognizing house-style numbers is therefore required, and once bob recognizes them it
  may as well write them.

### 2.2 Leading digits in real titles

The vault has headings like `## 2024 taxes` (`taxes.md`), `# 30 Burger`, `# 787 Coffee`,
and `# 1 Walnut` (`eat/`). A plugin that strips any leading `([0-9]+\.)*[0-9]+` would eat
them, and Number Headings does exactly that (cdx tested its prefix regex). Bob's rule must
**never** remove a bare number that has no dot (§5.2, N6).

### 2.3 `type` is safe to extend; cdx's and mus's concern does not hold

- In Rust, `frontmatter_has_type()` (`src/native/projects/scan.rs`) is only ever called
  with `"[[project]]"` or `"[[area]]"`.
- The plugins check `isProjectType` / `isAreaType` (in `bob-project-tasks`,
  `bob-navigation-hotkeys`, and `bob-ledger-tools`).
- Nothing treats "has any `type`" as special. `sase_blog_contents.md` has no `type`
  today, so `[[article]]` is purely additive.
- Existing types already include non-GTD kinds: `[[restaurant]]`, `[[podcast]]`, and
  `[[day]]`.

One implementation note: `flow_list_contains` hard-codes the bare wikilink forms for
project and area. Generalize it when adding article.

### 2.4 Heading links

- **Vault-wide:** 2,381 wikilinks point at a heading. **None** point into
  `sase_blog_contents.md`.
- **Into this note:** the only links are plain links from `sase_blog.md` ("Draft:") and
  `why_sase.md` ("Superseded by").
- **Obsidian's link updating:** `alwaysUpdateLinks: true` updates links when a file is
  renamed, not when a heading changes. Obsidian keeps heading links intact only when you
  use its right-click **Rename heading** command. Editing a heading by hand or by script
  breaks them. ([forum](https://forum.obsidian.md/t/update-links-to-section-headings-after-automatic-rename/24016),
  [forum](https://forum.obsidian.md/t/internal-links-to-headers-are-not-automatically-updated-with-header-changes/18423))

### 2.5 Vault configuration relevant to triggers and style

- `vimMode: true`, so "save" means `:w`.
- Strict line breaks are at the default (off), so a single newline already renders as a
  line break.
- Default theme, three CSS snippets, and no `cssclasses` used anywhere.
- **Obsidian Linter** is enabled with `lintOnSave: true`, but only one rule is on:
  `add-blank-line-after-yaml`. gem's claim that Linter is "intentionally disabled
  vault-wide" is wrong.
- The documented sync topology is git across athena, apollo, and the MacBook, with no
  mobile client. Desktop-only plugin features are therefore acceptable (cdx assumed mobile
  mattered).

### 2.6 Spawning bob is cheap enough to call on every save

On apollo, `bob capture-sections -r sase_blog_contents -f json` took under 10 ms of wall
time (`/usr/bin/time` printed `0.00 s` in three runs). The accepted
`mac-capture-is-a-thin-client` decision measured about 5 ms for a capture dry run. A
plugin that calls bob on save, or on a debounced pause in typing, is well within budget.
That lets bob stay the only implementation, the same rule the Mac capture app follows.

### 2.7 CSS counters do not work as the source of the numbers

- **Reading view:** headings and their bodies sit at the same, flat level of HTML, and the
  view renders lazily. Counter resets therefore misbehave across sections and embeds
  ([forum](https://forum.obsidian.md/t/header-counter/3525/10),
  [forum](https://forum.obsidian.md/t/indent-sections-by-heading-using-css-partial-solution/74060)).
- **Live Preview:** the editor renders only the visible region
  ([Obsidian viewport docs](https://docs.obsidian.md/Plugins/Editor/Viewport)).

A counter computed from the rendered page is wrong whenever earlier headings are off
screen. mus's default (CSS counters) fails on exactly the long documents this feature is
for.

### 2.8 The example note's pseudo-footnotes are fragile, as cld said

I checked with pandoc (CommonMark):

- A standalone `[c]: TBD` at the start of a block becomes a **hidden link definition**,
  and `X[c]` elsewhere silently renders as a link to `TBD`.
- The current `[1]: TODO: Add a note …` lines render as text only because the words
  after the colon make the definition invalid. Once one line fails to parse as a
  definition, the lines after it are absorbed into the same paragraph.

This deserves a **lint**. gem's auto-rewrite to `[^1]`, which also moves the definitions
to a References section, changes the text and is rejected.

### 2.9 What exists to reuse

- `src/native/markdown.rs`: `fenced_lines`, `atx_heading`, `setext_underline`, and
  `strictly_closed_frontmatter_end`.
- `src/native/highlights_ref/rename/links.rs`: `plan_vault_links`, `LineEdit`, and
  `FileRewrite`, a vault-wide link-rewrite planner.
- `src/native/vault_links.rs`.
- bob-plugins: the `execFile` pattern for calling bob (`bob-ledger-tools`
  `236-plugin-stats-data.js`), plus existing `registerEditorExtension` and
  `registerMarkdownPostProcessor` adornments.

---

## 3. Is this a good idea?

**Yes.** Three conditions make it reliable:

- the formatter stays **layout-only**;
- section numbers are **derived data that bob owns**, not text you maintain by hand;
- it **never runs while you type**.

Why it is worth doing:

1. **It fills a gap in the vault's note types.** `sase_blog.md` is a project: `^prj`,
   `## Tasks`, `## Outline`, and a "Draft:" link. `sase_blog_contents.md` is its
   untyped child holding the actual prose. The vault already separates the work (project)
   from the product (article); this names the product.
2. **A shared way to point at sections.** Bryan's blog workflow runs agent swarms over
   notes. With numbers in the source, "tighten §1.3, fold §1.4 into §1.2" means the same
   thing in Obsidian, in raw Markdown, in `git diff`, in an agent prompt, and in a PDF.
3. **Scoping is what makes automatic formatting safe.** Project and daily notes depend on
   tight layouts: `## Tasks` chip lines, status groups, Pomodoros, BLOCKS rows. A
   vault-wide formatter would damage thousands of them. Limiting it to one explicitly
   typed kind is the safety property.
4. **It is cheap.** The parser helpers, the type matcher, the link planner, and the
   plugin-calls-bob pattern all exist.

What could go wrong, and how this design handles it:

| Risk | How the design handles it |
| --- | --- |
| Heading links break when numbers change | In-note links are refreshed in the same edit. Links from other notes are reported until phase 3 rewrites them. There are none today (§2.4) |
| Diff churn and merge conflicts | Only heading lines change, and the output is deterministic. On a conflict, keep either side and run `format` again |
| Edits fight the cursor or undo | Formatting runs at save or note boundaries, as one transaction and one undo step, with a preimage check |
| Your words get deleted | A narrow ownership rule, an escape (`1\.5`), an adoption preview, and a runtime check that no words changed |
| Scope creep into a general Markdown formatter | Explicit "never" rules (§5.3); style opinions are rejected, not deferred indefinitely |
| A note is classified as an article by accident | Only an explicit `type` turns it on. `format` refuses notes holding `#task`, `^prj`, or `^ref` |
| A blog post looks like an academic paper | Numbers are muted on screen and can be stripped at export (phase 3). bob can always recognize its own numbers |

---

## 4. Changes to the requirements

| # | Original ask | Adjustment | Why |
| --- | --- | --- | --- |
| **A1** | "A way to specify" | The marker is `type: "[[article]]"`. Add an `article.md` type note, a template, and `bob articles adopt` | It follows the area, project, and ref convention. Metadata Menu's type picker lists children of `type.md`, so adoption needs no new UI |
| **A2** | "article / design doc / content with sections" | **One** type covers all of them | There is no behavioral difference yet. Split it only when one appears |
| **A3** | *(new)* | Articles do not hold `#task` lines. Work stays in the parent project; the formatter flags stray tasks | Every `#task` belongs in an area or project note. That split is already in use |
| **A4** | "Auto-format (think hard)" | Narrowed to **layout only**: words, inline markup, wrapping, and typography never change | That restraint is what makes it safe to run on every save |
| **A5** | "Auto-number" (mechanism open) | Numbers are **source text owned by bob**. Any leading number token on an article heading belongs to bob; escape it to keep it as text | Agents, git, and the Outline pane see them, and typed or stale numbers fix themselves |
| **A6** | "Starting at 1 with sub-sections" | House style `1.` / `1.1` / `1.1.1`, numbered at every depth | It matches about 3,400 existing numbered headings (§2.1) |
| **A7** | *(new)* | Skipped heading levels are closed by pulling headings up (`####` under `##` becomes `###`). Headings are never pushed down, and the top level is never changed | Otherwise numbering would be built on a gap |
| **A8** | *(implied)* | The file name, or a `title:` property, is the title. **Every heading is a section**, and there is no H1-title heuristic | gem's heuristic would treat the example's single H1, "The Abstractions", as the title, which is wrong |
| **A9** | *(new)* | Heading links follow the numbers: in-note links in v1, other notes' links in phase 3 | Otherwise every renumber silently breaks links |
| **A10** | *(implied: automatic)* | Formatting runs on `:w`, on leaving the note, on a command, from the CLI, or by an agent. **Never while typing.** Nightly starts as a check only | Numbers changing under the cursor are disorienting; writes at 3 a.m. need trust first |
| **A11** | — | **Deferred:** generated table of contents, footnote renumbering, appendix lettering, per-heading opt-out, smart typography, stripping numbers at export | Each is reasonable later; none is needed for the first use case |

---

## 5. Design

### 5.1 Marker and adoption

```yaml
---
parent: "[[sase_blog]]"
type: "[[article]]"
created: 2026-10-15T15:10:41-04:00
# Both keys are optional:
# title: "Why I built SASE"   # publication title; otherwise the file name
# section_numbers: false      # keep formatting, remove bob's numbers (reversible)
---
```

That is the whole contract. There are no depth knobs, separators, or start-at values.

- **Type note `~/bob/article.md`** (`parent: "[[type]]"`) states the contract in a few
  lines. Add an Articles block to `type.md`, next to Projects and Reading List.
- **Three ways to adopt.** All of them write the same single line:
  - **Properties:** pick `[[article]]` in the `type` picker. It appears once `article.md`
    exists.
  - **Command "Bob: Convert note to article":** shows the first format as a diff in a
    preview modal before applying it. This is cdx's adoption preview. It is where any
    leading numbers that would be stripped become visible.
  - **`bob articles adopt NOTE`:** a dry run unless `-w/--write`, like
    `bob ref migrate-tasks`.
- **Template** `_templates/new_article.md`: `parent` comes from the active note; it also
  sets `type` and `created`.
- **The CSS class is injected at runtime** by the plugin, based on the note's `type`. It
  is not written to YAML (grk's `cssclasses` projection), because that would add YAML noise
  and a second source of truth.
- **Exclusive with project, area, and ref.** `format` refuses a note that holds `^prj`,
  `^ref`, or `#task` lines.

Why not a separate key (`bob_document`, `doctype`)? Both proposals were meant to protect
existing `type` consumers. §2.3 shows those consumers match exact values, so
`[[article]]` cannot trigger them. A second key would also create a second classification
system next to the one the vault, Dataview, Bases, Metadata Menu, and bob already share.

### 5.2 Section numbering

**Rules:**

- **N1. What counts as a section.** A heading at the top level of the note body: ATX
  (`#` … `######`) or Setext. Headings inside frontmatter, code fences, `$$` math, `%%`
  comments, HTML blocks, blockquotes or callouts, and list items do not count.
- **N2. Preamble.** Text before the first heading is the unnumbered lede.
- **N3. Levels.** The base is the shallowest heading level in the note; the author's
  choice is kept. Each heading's new level is one more than the new level of the nearest
  earlier heading that was shallower in the original, or the base if there is none. This
  only ever pulls headings up. Each repair is reported.
- **N4. Counting.** A heading's depth is its level minus the base, plus 1. Each depth has
  a counter; deeper counters reset when a shallower heading appears. All depths are
  numbered, starting at 1. A lint suggests flattening below depth 4.
- **N5. Format.** Depth 1 is written `1.`; deeper levels are `1.1`, `1.1.1`. Then one
  space and the title. Inline markup in the title is kept byte-for-byte.
- **N6. Ownership.** Before writing, bob removes **exactly one** leading token that
  matches `^(\d{1,3}\.|\d{1,3}(\.\d{1,3})+\.?)[ \t]+`, then writes the correct number.
  A bare number with no dot is never removed.
- **N7. Escape.** Write `1\.5 million users`. It renders as `1.5 million users`, and bob
  never touches it.
- **N8. Links.** Links inside the note (`[[#…]]`, and links to the note's own name with a
  `#heading`) are refreshed in the same edit. A link matches a heading when the two are
  equal after removing the number token from both. Ambiguous matches are reported, not
  rewritten.
  - **Other notes:** v1 reports inbound heading links that this renumber would break.
    Phase 3 rewrites them with `plan_vault_links`.
  - **Block links:** `[[note#^id]]` links are never affected.
- **N9. Turning numbering off.** `section_numbers: false` removes bob's tokens, and
  setting it back restores them. Both states are idempotent.

How N6 and N7 treat real headings. Each example is a `##` heading under a `#` section, so
it gets a two-part number:

| Heading as typed | Result | Why |
| --- | --- | --- |
| `## 2024 taxes`, `## 30 Burger` | `## 1.1 2024 taxes` | A bare number with no dot is your text |
| `## 1.4 New section` (typed by an agent) | `## 1.5 New section` | House-style number, treated as stale and replaced |
| `## 3. Reasons I quit` | `## 1.2 Reasons I quit` | Matches the token. In an article, a typed number is assumed to be a section number |
| `## 1.5 million users` | ⚠ becomes `## 2.1 million users` | **Remaining risk.** Use `1\.5`; the adoption preview and change notice show it |
| `## 1\.5 million users` | `## 2.1 1\.5 million users` | Escaped, so it is kept |

The `1.5 million users` row is the cost of matching the house style. It is rare: no vault
heading outside `_generated/` starts with a decimal (§2.2). It is also visible and
recoverable: the adoption preview shows it, the edit is a single `u` to undo, and git
history has the original. The trailing-dot alternative avoids this case but fails on the
common case, numbers that agents type by habit (§2.1).

**Why numbers in the source rather than display-only** (this is where I disagree with cdx
and mus):

1. **Agents and git are first-class readers.** The first article is a blog draft that
   agent swarms edit. A "§1.3" in a prompt, in `git diff`, and on Bryan's screen must be
   the same string.
2. **Obsidian surfaces pick them up for free:** the Outline pane, `[[note#`
   autocomplete, heading search, `bob capture-sections`, and PDF snapshots. Display-only
   numbers reach none of them. cdx itself notes the built-in Outline would stay
   unnumbered.
3. **Display-only still needs the ownership rule.** Agents type numbers by habit, so a
   display layer would show `1.2 1.2 Foo` unless a formatter strips typed numbers. That is
   the N6 grammar anyway. On top of it you would need a second numbering engine in
   JavaScript for both editor widgets and Reading view. That goes against the
   one-implementation rule bob already follows for capture.
4. **The costs are bounded.** Diffs touch only heading lines and are deterministic. There
   are no inbound heading links today, and refresh handles in-note links.

**When cdx's display-only design would be right:** if Bryan wants raw Markdown and git to
stay unnumbered, and agents never cite sections by number. That is open question 1 (§10).

### 5.3 Formatting rules

Principles:

- **Layout, never language.** The sequence of words is unchanged apart from bob's number
  tokens. A runtime check enforces this.
- **Line-level edits, never a whole-file reprint.** Untouched lines stay byte-identical.
- **Idempotent and deterministic.**
- **When unsure, report instead of fixing.**
- **Silent when there is nothing to do.**

**Fix automatically:**

| ID | Rule | Notes |
| --- | --- | --- |
| F1 | Exactly one blank line between the frontmatter and the body. Frontmatter bytes are otherwise untouched | Same as Linter's only enabled rule, so the two can run in either order |
| F2 | Heading lines take the form `#…# NUMBER TITLE`. Closing `#`s and trailing whitespace are removed | Fixes `## VCS and workspace operations␠` |
| F3 | Skipped levels are closed by pulling up (N3) | `####` under `##` becomes `###` |
| F4 | Section numbers (N4–N6) | The first use case |
| F5 | One blank line before and after every heading, except at the start of the body | Visual chapter breaks come from CSS margins, not extra source lines |
| F6 | Runs of blank lines between top-level blocks collapse to one. Never inside lists, quotes or callouts, code, math, HTML, comments, or tables | Does not change whether a list is tight or loose |
| F7 | Trailing whitespace is removed outside code, math, and HTML | Strict line breaks are off in this vault, so two trailing spaces add nothing in Obsidian. A `\` hard break still works |
| F8 | No leading blank lines; exactly one final newline; the file's LF or CRLF is kept | Clean diffs |
| F9 | In-note heading links are refreshed (N8) | Renumbering never breaks a link inside the note |
| F10 | Setext headings are converted to ATX, and the conversion is reported | They are real headings and need numbers; one heading syntax keeps things simple |

**Report, never fix.** Lints appear in the save notice, in `bob articles list`, and in
JSON output:

| ID | Finding | Suggested action |
| --- | --- | --- |
| L1 | A `#task`, `^prj`, or `^ref` line in an article | Move it to the parent note with Ctrl+Shift+M |
| L2 | A fragile pseudo-footnote: a `[x]: …` line that is, or could become, a hidden link definition (§2.8) | Use `[^x]` footnotes |
| L3 | An in-note heading link with no target, or with more than one possible target | Fix the link or rename the heading |
| L4 | A link from another note to a heading that this renumber changes (until phase 3) | Re-point it, or use a `^id` block link |
| L5 | A heading-level repair was made (F3), or a heading sits deeper than depth 4 | Informational |
| L6 | A code fence that is never closed | The formatter changes nothing after it |
| L7 | The first heading repeats the file name or `title:` | Delete it; Obsidian already shows the inline title |

`bob articles outline` also reports progress, which is useful while drafting: words per
section and TODO stubs ("9 of 10 sections are TODO").

**Never do (rejected, not just deferred):**

- **Reflowing paragraphs or adding semantic line breaks.** Soft wrap already works, and
  reflow ruins diffs and vim's line-wise editing.
- **Title-casing headings** (gem). It changes words. Bryan writes headings like "NOT
  hooks" and `**memory**` on purpose.
- **Smart typography** (`->` → `→`, curly quotes). It changes words. Do it at publish time
  if at all (pandoc `+smart`).
- **Aligning table pipes** (gem). Editing one cell would rewrite the whole table, and
  Live Preview renders tables anyway.
- **Normalizing emphasis or list markers** (mus). Cosmetic only. Changing markers can
  merge two adjacent lists into one, and inline parsing is where Obsidian syntax breaks.
- **Moving or renumbering footnotes** (gem). It moves content and rewrites references.
- **Adding block IDs to every heading** (gem). It clutters headings to work around a
  problem that link refresh already solves.
- **A generated table of contents in the source.** It churns on every edit, and the
  Outline pane already shows the numbered tree.
- **Reordering sections, or editing frontmatter keys other than F1.**

### 5.4 Architecture: bob decides, the plugin applies

```text
                     ┌──────── bob-cli (Rust): the only implementation ────────┐
 bob-articles  ────▶ │ articles::format(text, ctx) -> FormatPlan               │ ◀── bob articles format
 (Obsidian plugin;   │  1 scan blocks: frontmatter, fences, $$, %%, HTML, >    │     (you, agents)
  sends the buffer   │  2 heading tree: close level gaps                       │ ◀── bob nightly
  on stdin, gets     │  3 numbering: strip one owned token, renumber           │     (phase 3)
  JSON back)         │  4 layout: blank lines, whitespace, end of file         │
                     │  5 in-note link refresh, inbound-link scan              │
                     │  6 verify: idempotent, words unchanged                  │
                     └─────────────────────────────────────────────────────────┘
 FormatPlan = { schema_version, changed, edits[line range → text], lints[],
                outline[{number, level, title, line, words}], inbound_links[] }
```

- **The core is pure:** text in, plan out, no I/O. The CLI wraps it with an atomic write
  that checks a content hash first. The plugin wraps it with one editor transaction.
- **The JSON contract only grows.** Fields are added with a `schema_version`, as in the
  capture protocol.
- **Why not a plugin-only engine (cdx)?** Agents edit `~/bob` without Obsidian running,
  and the nightly check needs the same rules. With bob as the only engine, the editor and
  the CLI can never disagree.

### 5.5 Triggers and write safety

- **In Obsidian:**
  - On `:w` or Ctrl+S. The plugin wraps the `editor:save-file` command the way Linter's
    lint-on-save does.
  - When you leave the note (leaf change or file close). The plugin waits until the buffer
    has been saved, then writes through `vault.process`, checking first that the file is
    unchanged since bob read it.
  - From the command "Bob: Format article".
  - **Never** on a timer or per keystroke. Number Headings polls every 10 seconds, and
    users have reported it interrupting IME composition
    ([issue 85](https://github.com/onlyafly/number-headings-obsidian/issues/85)).
- **One transaction.** Edits are computed from the live buffer and applied only if the
  buffer still matches what was sent to bob. They land as one CodeMirror transaction, so
  one `u` undoes them, with selections mapped through. Undoing a format does not trigger
  another format until you make a fresh edit (cdx).
- **Agents and scripts.** Add one line to the vault's `AGENTS.md`: *after editing a note
  whose `type` is `[[article]]`, run `bob articles format <path>`.* The CLI writes
  atomically with a preimage check. It skips `_conflicts/`, `_templates/`, files with
  conflict markers, and files whose frontmatter does not parse, and it gives a reason for
  each skip.
- **Nightly (phase 3).** Start with `bob articles format --check --all`, which reports
  only. Once trusted, run `--all` between the two `vault-sync` runs. Nightly already
  rewrites notes (`task archive`), and the output is deterministic, so each machine
  produces the same bytes.
- **Runtime check that no words changed.** Before any write, compare the sequence of
  non-whitespace tokens, ignoring heading `#`s and each heading's single leading number
  token. If they differ, write nothing and report an internal error.

### 5.6 Beauty

The goal is calm. Task notes look like tools; articles should look like a well-set paper.
Every rule is scoped under `.bob-article`, which the plugin adds to Markdown views of
article notes.

- **Measure and rhythm.** About 40rem (~70 characters) via `--file-line-width`, body line
  height about 1.65, and more space above H1 and H2 than below them. Section breaks come
  from margins, not from rules, borders, or badges. gem's boxed number badges are rejected
  as too loud.
- **Body typeface.** A serif text stack for article prose only (`ui-serif, "Iowan Old
  Style", Charter, Georgia, serif`), with the theme's heading face kept for contrast. This
  is the single strongest cue that "this is a document". A plugin setting returns to the
  theme font.
- **Numbers.** `--text-muted` colour (not `--text-faint`, which is too low-contrast in
  dark themes), normal weight, `font-variant-numeric: tabular-nums`, and a fixed 0.5em gap
  before the title. They are real text, so screen readers and copy-paste get them.
- **Hanging numbers in Reading view.** On wide panes, numbers sit in the left margin so
  every title starts on the same edge. Narrow panes fall back to inline numbers. Live
  Preview keeps numbers inline, because the cursor line shows raw source anyway.
- **Stale-number signal.** In Live Preview the plugin runs bob's dry run on the buffer
  (`--stdin`, debounced about 400 ms after typing stops, desktop only). Any heading whose
  number no longer matches gets a dotted accent underline until the next save. A number
  on screen is therefore either correct or visibly stale.
- **Status bar:** `§ 1.3.1` shows the section under the cursor, in article notes only.
- **Notice only when something changed:** `Article formatted · 4 sections renumbered ·
  1 link refreshed`, with lints on a second line.
- **Terminal:** `bob articles outline` prints a coloured tree: numbers dim, titles
  bright, word counts right-aligned, TODO stubs highlighted.

```css
.bob-article {
  --file-line-width: 40rem;
  --line-height-normal: 1.65;
  --font-text: ui-serif, "Iowan Old Style", Charter, Georgia, serif;
}
.bob-article .bob-secno {
  color: var(--text-muted);
  font-weight: var(--font-normal);
  font-variant-numeric: tabular-nums;
  margin-inline-end: 0.5em;
}
.bob-article .bob-secno.is-stale { text-decoration: underline dotted var(--text-accent); }
@container (min-width: 46rem) {          /* Reading view, wide pane: hang the number */
  .bob-article .markdown-rendered :is(h1,h2,h3,h4) .bob-secno {
    position: absolute; transform: translateX(calc(-100% - 0.75em));
  }
}
```

This sketch shows the direction only. Container queries and the exact selectors need a
test pass on light and dark themes, at narrow widths, at 200% zoom, and in print.

### 5.7 CLI surface

The new group goes in the Vault section, with the membership rule "commands that inspect
or rewrite notes whose type is `[[article]]`". It is plural to mirror `bob projects`, and,
like `bob projects`, it requires a subcommand.

```text
$ bob articles --help
Format and inspect article notes (frontmatter type: "[[article]]")

Commands:
  adopt    Mark a note as an article; dry run unless --write
  format   Normalize layout and renumber sections in article notes
  list     List article notes with section, TODO, and lint counts
  outline  Print an article's numbered section outline

$ bob articles format --help
Usage: bob articles format [OPTIONS] [PATH]...
  -a, --all            Format every article note in the vault
  -b, --bob-dir DIR    Vault root (default: $BOB_DIR, then ~/bob)
  -c, --check          Exit 1 if any note would change; write nothing
  -d, --dry-run        Print the unified diff; write nothing
  -f, --format FMT     human (default) | json
  -s, --stdin          Read one note's text from stdin (PATH names it); print the plan
```

```text
$ bob articles outline sase_blog_contents
sase_blog_contents · article · 253 words · 10 sections · 9 TODO
  ¶       Preamble                                                  186 w
  1.      The Abstractions                                            0 w
  1.1     Gates -> Plans -> Epics                                  TODO
  1.2     Beads -> Sidecar repos                                   TODO
  1.3     Agent CLIs                                               TODO
  1.3.1   Skills, **memory**, provider interface, NOT hooks        TODO
  1.3.2   Agent presentation / organization (tribes, clans, …)     TODO
  1.4     VCS and workspace operations                             TODO
  …
```

`outline -f json` lets an agent act on "rewrite §1.3" precisely, using that section's
line range.

---

## 6. Alternatives considered

| Option | Verdict | Reason |
| --- | --- | --- |
| **CSS counters** through `cssclasses` (mus) | Rejected | Wrong numbers in lazily rendered or virtualized views (§2.7). Invisible to agents, git, and the Outline pane |
| **Display-only editor widgets** with numbers baked into exports (cdx) | Runner-up | Correct on screen, with no churn and no link risk. But it still needs the ownership grammar, needs a second engine in JavaScript, and agents, git, and the Outline pane never see the numbers (§5.2) |
| **Trailing-dot numbers `1.1.`** (cld, grk) | Rejected | Foreign to the house style, and it fails on numbers agents type by habit (§2.1) |
| **Number Headings plugin** | Rejected | Polls every 10 s; strips leading years and decimals; no link maintenance; plugin-only; last release 2023 |
| **Obsidian Linter rules** | Rejected as the engine | Rules can't be limited to one note type (files can only opt out) and there is no numbering rule. Keep its one rule, which F1 matches |
| **Prettier / mdformat / dprint** | Rejected | Reprints the whole file with its own style opinions, can't be limited to a note type, can't number sections, and would add Node to bob's headless path |
| **gem's 10-rule profile** (title case, table alignment, moving footnotes, injecting block IDs) | Rejected | Changes words and meaning, and causes churn. Its title-detection heuristic gets the example note wrong |
| **A separate `bob_document` / `doctype` key** | Rejected | Built to avoid a conflict that does not exist (§2.3), at the cost of a second classification system |
| **Folder, filename, or tag marker** | Rejected | Breaks when the note moves or is renamed; tags in this vault are GTD-heavy |
| **A generic `bob fmt` with a profile per note type** | Deferred | Reasonable later. With one profile, a `bob articles` group is clearer, and the core can move later at no cost |
| **Recommended:** a bob-owned, layout-only formatter writing house-style numbers into the source, plus a thin plugin | ✅ | §5 |

---

## 7. Worked example: `sase_blog_contents.md`

My throwaway prototype (about 100 lines of Python implementing F1–F9 and N3–N8) ran on a
copy of the note. Only heading lines and blank lines change. The preamble and the
pseudo-footnote lines stay byte-identical, and a second run changes nothing:

```markdown
[b]: TODO: Update commit/line counts!

# 1. The Abstractions

## 1.1 Gates -> Plans -> Epics

TODO

## 1.2 Beads -> Sidecar repos

TODO

## 1.3 Agent CLIs

TODO

### 1.3.1 Skills, **memory**, provider interface, NOT hooks

TODO

### 1.3.2 Agent presentation / organization (tribes, clans, families, hoods, metadata/files/tools panel)

TODO

## 1.4 VCS and workspace operations

TODO
…
## 1.7 Routines and Jobs

TODO
```

Notice: `Article formatted · 10 sections numbered · 2 headings promoted (#### → ###)`.

Every section sits under `1.` because the draft has one top-level section. That is
accurate. It spreads out as Bryan adds sibling top-level sections ("Why I built it",
"What I learned"). Promoting the H2s to `#` instead is an outline decision for the author,
not for the formatter.

I also ran the prototype on an edge-case fixture. Each result matches the N6 table:

- `2024 taxes` and `30 Burger` were kept.
- An agent-typed `1.4` and a typed `3.` were replaced.
- `1.5 million users` and `1.16.0 changelog` lost their leading token: the known
  remaining risk.
- `1\.5` was kept.
- `#` lines inside a fenced block were untouched.
- `[[#Beads]]` became `[[#7. Beads]]`.
- `[[sase_blog_contents#2024 taxes|alias]]` became
  `[[sase_blog_contents#1. 2024 taxes|alias]]`.

The prototype is evidence for the rules, not an implementation. The real engine reuses
bob's `markdown.rs` and adds callout, math, comment, and HTML handling.

---

## 8. Phased plan

| Phase | Repo | Scope | Size |
| --- | --- | --- | --- |
| **0. Vault** | `~/bob` | Type note `article.md` and an Articles block in `type.md`; `_templates/new_article.md`; one line in the vault's `AGENTS.md` | S |
| **1. Engine and CLI** | bob-cli | `src/native/articles/`: block scan (reusing `markdown.rs`), heading tree, numbering, layout, in-note link refresh, inbound-link scan, both invariants. `bob articles {adopt, format, list, outline}` with `--check`, `--dry-run`, `--stdin`, `--format json`. Also `docs/articles.md`, and `frontmatter_is_article` with the generalized flow-list matcher. Tests: golden fixtures (this note plus §7's edge cases, Setext, callouts, math, `%%`, CRLF, block IDs, a non-article that must come out byte-identical); property tests (idempotency, words unchanged); a fuzz-style `--check` over every vault note treated as an article, run on a temp copy; help snapshots. Then adopt `sase_blog_contents.md` with `bob articles adopt -w` | M |
| **2. Plugin** | bob-plugins | A new `bob-articles` plugin: runtime class plus CSS; format on `:w`, on leaving the note, and on command, applied as one transaction; adoption preview modal; muted, stale-aware number decoration; hanging numbers in Reading view; `§` status item. Deploy with `bob plugins sync` | M |
| **3. Hardening** | both | Rewrite inbound heading links across the vault with `plan_vault_links`; nightly `--check`, then `--all`; a `NoteKind::Article` snapshot profile; `export --strip-numbers` if posts should be unnumbered; a per-heading `<!-- bob:unnumbered -->` opt-out; a footnote tool | M |

Phases 0–2 deliver the full experience for `sase_blog_contents.md`. Phase 1 is useful on
its own, because agents can run `bob articles format` right away.

**Memory follow-ups, once Bryan accepts the design** (through `/sase_memory_write`; not
done here):

- a glossary term **Article Note**;
- a decision record: "Article section numbers are bob-owned source text in house style
  (`1.` / `1.1`)", recording display-only and `1.1.` as rejected alternatives.

---

## 9. Corrections to the input reports

- **gem**
  - Says Linter is "intentionally disabled vault-wide". In fact it runs on save with one
    rule.
  - Its "virtual by default" adjustment (R1) contradicts its own worked example, which
    writes numbers into the source.
  - Its title heuristic ("a single H1 means a title") would misread this note.
  - Title case, moving footnotes, and the `[1]` → `[^1]` rewrite all change Bryan's text.
- **mus**
  - CSS counters are unreliable in Obsidian (§2.7).
  - Its "H1 is the title" default would number "The Abstractions" sub-sections as
    top-level 1–7.
  - Its strip regex `^(\d+[.\)]\s?)+` reduces `1.5 million` to `5 million`.
- **grk:** its loosened strip grammar removes `1.5` from `1.5 million users`, which
  contradicts its own safety claim (§2.1).
- **cld**
  - The trailing-dot style is not the house style, and it fails on agent-typed numbers.
  - Promoting the shallowest level to `#` changes heading sizes needlessly.
  - Two blank lines before `#` sections are not needed; CSS gives the same visual break.
- **cdx**
  - Its separate-key rationale does not hold (§2.3).
  - The mobile constraint does not apply to this vault's sync topology (§2.5).
  - Its strongest contributions are kept in this design: the write-safety contract,
    the adoption preview, accessibility, and the acceptance matrix.

---

## 10. Open questions for Bryan

1. **Source numbers vs. display-only.** I recommend source numbers. Display-only is right
   only if you want raw Markdown and git unnumbered, and agents never cite sections by
   number.
2. **Numbers in the published post?** If not, phase 3 adds
   `bob articles export --strip-numbers`. This is easy, because bob recognizes its own
   tokens.
3. **Serif body text for articles by default?** I recommend yes; it is one setting to
   revert.
4. **Nightly:** should it eventually write, or only ever check?
5. **Name:** `article` covers blog posts, design docs, and essays. Say so if you would
   rather use `doc`.

---

## 11. Recommended solution

**Add an `article` note type with a layout-only formatter that bob owns. It writes
house-style section numbers into the source, and a thin Obsidian plugin makes articles
look like documents.**

1. **Marker:** `type: "[[article]]"`, with an `article.md` type note, a template, and
   adoption through the Properties picker, a previewing command, or
   `bob articles adopt`. It is never inferred. Optional keys: `title:` and
   `section_numbers: false`.
2. **Engine:** one pure Rust function in bob-cli. It closes heading-level gaps, numbers
   every section as `1.` / `1.1` / `1.1.1`, applies layout rules F1–F10, refreshes in-note
   heading links, reports lints L1–L7, and checks idempotency and that no words changed
   before every write. It is exposed as `bob articles {adopt, format, list, outline}`
   with `--check`, `--dry-run`, `--stdin`, and `--format json`.
3. **Ownership:** each run strips one leading `N.` or `N.N…` token per heading and writes
   the correct number. A bare number stays, and `1\.5` escapes a literal.
4. **Triggers:** the plugin applies bob's plan as one undoable transaction on `:w`, when
   you leave the note, or on command. Agents run `bob articles format <path>`. Nightly
   starts as a check. Nothing runs while you type.
5. **Beauty:** a calm reading measure, serif prose, muted tabular numbers that hang in the
   margin in Reading view, stale numbers marked, a `§ 1.3.1` status item, and a coloured
   `bob articles outline`.
6. **Not included:** reflow, title case, smart typography, table alignment, moving
   footnotes, a generated table of contents, and block-ID injection. Rewriting links from
   other notes, stripping numbers at export, and per-heading opt-outs come in phase 3.

The result: numbered, consistently laid out articles where Bryan and every agent can say
"§1.3" and mean the same thing. The design costs one frontmatter line per note, never
deletes a word without showing it, and never fights the cursor.

---

## Sources

**Local evidence (verified this turn):**

- Vault: `~/bob/sase_blog_contents.md`, `sase_blog.md`, and `why_sase.md` (read-only);
  `.obsidian/app.json`, `appearance.json`, `types.json`, `community-plugins.json`, and the
  Linter `data.json`; the vault's `AGENTS.md`; ripgrep counts of numbered headings and
  heading links.
- bob-cli: `src/native/projects/scan.rs` (`frontmatter_has_type`, `flow_list_contains`);
  `src/native/markdown.rs`; `src/native/highlights_ref/rename/links.rs`;
  `src/native/vault_links.rs`; `src/native/highlights_ref/note_snapshot/classify.rs`;
  numbered-heading counts in `docs/`; `bob --help`, `bob projects --help`,
  `bob ref --help`.
- bob-plugins at `e90c260`: type checks in `bob-project-tasks`, `bob-navigation-hotkeys`,
  and `bob-ledger-tools`; the `execFile` and editor-extension patterns.
- The research and plans repos: house-style numbering counts.
- Memory: `obsidian.md`, `cli_rules.md`, `decisions:mac-capture-is-a-thin-client`, and
  glossary Area Note and Project Note.
- Experiments on copies under `/tmp`: the prototype formatter (example note plus edge
  fixture), pandoc CommonMark checks of pseudo-footnotes, and `bob capture-sections`
  timing on apollo.

**External:**

- Obsidian forum on CSS heading counters:
  [Header counter](https://forum.obsidian.md/t/header-counter/3525),
  [page 3](https://forum.obsidian.md/t/header-counter/3525?page=3),
  [post 10](https://forum.obsidian.md/t/header-counter/3525/10),
  [CSS for numbered headers in Live Preview](https://forum.obsidian.md/t/css-for-numbered-headers-in-live-preview/40347),
  [Indent sections by heading (flat HTML)](https://forum.obsidian.md/t/indent-sections-by-heading-using-css-partial-solution/74060).
- Obsidian docs: [Editor viewport](https://docs.obsidian.md/Plugins/Editor/Viewport),
  [Decorations](https://docs.obsidian.md/Plugins/Editor/Decorations),
  [Vault API / process()](https://docs.obsidian.md/Plugins/Vault),
  [Internal links](https://help.obsidian.md/links),
  [Properties](https://help.obsidian.md/properties),
  [CSS snippets / cssclasses](https://help.obsidian.md/snippets).
- Heading links not following heading edits:
  [Update links after automatic rename](https://forum.obsidian.md/t/update-links-to-section-headings-after-automatic-rename/24016),
  [Internal links to headers not updated](https://forum.obsidian.md/t/internal-links-to-headers-are-not-automatically-updated-with-header-changes/18423),
  [Automatic inline update of heading links](https://forum.obsidian.md/t/automatic-inline-update-of-links-to-headers-and-blocks-when-they-are-modified-no-extra-dialog-window/25412?page=3),
  [Heading Keeper](https://community.obsidian.md/plugins/heading-keeper),
  [Heading Autolink](https://community.obsidian.md/plugins/heading-autolink).
- Numbering plugins:
  [Number Headings source at 4cd3fac](https://github.com/onlyafly/number-headings-obsidian/blob/4cd3fac7a2394648e8f8ef7193622ecb3d6eb02f/src/textProcessing.ts#L17),
  [10 s timer](https://github.com/onlyafly/number-headings-obsidian/blob/4cd3fac7a2394648e8f8ef7193622ecb3d6eb02f/src/main.ts#L319),
  [issue 85 (IME)](https://github.com/onlyafly/number-headings-obsidian/issues/85),
  [Section Numbering](https://community.obsidian.md/plugins/section-numbering),
  [Auto Heading](https://www.obsidianstats.com/plugins/auto-heading).
- Formatting references:
  [Obsidian Linter running rules](https://platers.github.io/obsidian-linter/usage/running-rules/),
  [Linter heading rules](https://platers.github.io/obsidian-linter/settings/heading-rules/),
  [CommonMark 0.31.2](https://spec.commonmark.org/0.31.2/),
  [Prettier options](https://prettier.io/docs/options#prose-wrap),
  [Pandoc numbering options](https://pandoc.org/MANUAL.html#options-affecting-specific-writers),
  [ISO 2145](https://en.wikipedia.org/wiki/ISO_2145).
- Input reports, in this directory: `__cdx.md`, `__cld.md`, `__grk.md`, `__mus.md`,
  `__gem.md`.
