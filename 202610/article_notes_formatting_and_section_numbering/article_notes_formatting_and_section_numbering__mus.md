# Article / Design-Doc Notes: Markup, Formatting & Section Numbering

Research report — researcher `mus`. Vault: `~/bob`, tool: `bob-cli` (Rust),
example note: `sase_blog_contents.md`.

## TL;DR

Yes, do it — but change two load-bearing parts of the ask:

1. **Mark the kind with a semantic frontmatter key, not a path/tag
   convention.** Recommended: `doctype: article`. Do not reuse `type:` (it
   already means `[[project]]` / `[[day]]` in this vault) and do not use a bare
   `#article` tag or a magic directory as the source of truth.
2. **Do not bake section numbers into the vault file by default.** Keep vault
   headings unnumbered; render numbers as a *view* (Obsidian CSS driven by the
   marker) and materialize them only at export/publish time. Offer a
   `--write` baked-number mode as an explicit opt-in, not the default.

Everything else in the request — a distinct article note kind with its own
formatting pass — is sound and composes well with how `bob-cli` already owns
vault grammar (cf. capture grammar living in `bob`, thin-client Mac app).

---

## 1. What was asked

- A per-file declaration: "this markdown file is an article / design doc /
  content-with-sections".
- Such files get different treatment from ordinary notes (tasks, journals,
  area/project notes).
- First use-case: auto-format these files (rules TBD — "think hard") and
  auto-number their sections starting at 1 with sub-section support.
- Design goals in order: intuitive, reliable, beautiful. Researcher leads the
  design.

## 2. Is this a good idea? (critique)

**Yes, with the adjustments in §7.** The vault already has implicit note kinds
(area, project, day, journal, ref) distinguished by frontmatter (`type:`,
`parent:`, `template:`) and by structure (task lines vs. prose). Articles are
the missing kind: long-lived prose with sections, few or no `#task` lines
(`sase_blog_contents.md` has zero task lines and four heading levels — it is
unambiguously this kind). Giving the kind a name unlocks formatting, numbering,
TOC, blog-export, and print CSS behind one predicate instead of N heuristics.

Risks that must shape the design:

1. **Formatting churn vs. `vault-sync` noise.** Any formatter that rewrites
   the whole vault on day one will flood git history. Scope the formatter to
   opted-in files first; make it idempotent; ship `--check` + diff preview
   before any `--write`.
2. **Baked numbers rot.** Inserting one section renumbers every later heading,
   producing large diffs and breaking Obsidian heading links
   (`[[note#2.3 Foo]]` dies when `2.3` becomes `2.4`). Humans also hand-edit
   baked numbers wrong, and then the tool and the human fight. This is the
   single biggest reliability risk in the request as stated.
3. **Heading links and Tasks are load-bearing.** `sase.md`-style notes carry
   block IDs (`^prj`), inline fields (`[priority:: high]`), and section links
   (`#Tasks#Next & In Progress`). The article formatter must provably never
   touch these — articles have fewer of them, but the code path will tempt
   reuse on ordinary notes later.
4. **Beauty is rendering, not source.** Numbered headings look best with
   tabular numerals, consistent gaps, and sub-number de-emphasis — all CSS
   properties. Baked `## 1.2 Foo` text cannot do any of that and looks
   progressively worse at depth (`#### 2.3.1.4 Foo`).

Verdict: introduce the *kind* now, ship *formatting* second, ship *numbering
as a view* third, and treat *baked numbers* as an export artifact, not vault
state.

---

## 3. How to mark a file as an article (options)

| Option | Mechanism | Verdict |
|---|---|---|
| **A. `doctype: article` frontmatter** | `doctype: article` (+ optional `number_sections: true`, `toc: false`) | **Recommended.** Explicit, greppable, Dataview-queryable, no rename, no move. |
| B. `#article` tag | inline tag anywhere | Reject as source of truth. Tags drift, get deleted in edits, and collide with content tags. Accept as a *fallback hint* at most. |
| C. Magic directory (`essays/`, `_articles/`) | location implies kind | Reject. Bryan's vault is flat (`~/bob/*.md`, ~670 files); moves break links and the `parent:` graph. |
| D. Filename suffix (`.article.md`) | name implies kind | Reject. Renames break `[[links]]` vault-wide; Obsidian rename-refactor would have to fire for every adoption. |
| E. `cssclasses:` only | presentational key | Reject as the semantic marker (fine as a *derived* rendering hook — see §6). `cssclasses` says how to look, not what the note is. |

Why not reuse `type:`? Because `type: "[[project]]"` / `type: "[[day]]"` is
already a type system with Dataview and plugin consumers. Overloading it with
`type: article` (unlinked string vs. `[[link]]`) creates a silent schema fork.
A fresh `doctype:` key leaves every existing query untouched and generalizes:
`doctype: article | design-doc | memo | essay` later, with per-doctype
formatting profiles.

Proposed schema (minimal, extensible):

```yaml
---
parent: "[[sase_blog]]"
created: 2026-10-15T15:10:41-04:00
doctype: article        # the kind marker; absence = ordinary note
number_sections: true  # default true when doctype is article; explicit opt-out
toc: false             # optional; default false until the TOC design lands
---
```

Rules: `doctype` is a plain scalar (never a `[[link]]`); unknown `doctype`
values warn, never error; `number_sections` without `doctype: article` warns
("did you mean to set doctype?"). Keep the key lowercase with underscore to
match `number_sections` style already implicit in vault YAML (`zorg_source_*`,
`generated_from_zorg`).

Intuition check: adopting = adding one frontmatter line. Unadopting = deleting
one line. Discovering = `grep -l '^doctype: article' *.md` or one Dataview
query. That is the right weight for the gesture.

---

## 4. Formatting rules (thought hard about)

Design principles: **idempotent** (second run is a no-op), **surgical**
(never reflows meaning), **Obsidian-faithful** (wikilinks, embeds, block IDs,
callouts, math, and task lines are opaque tokens), **diff-minimal** (smallest
edit that achieves the rule).

### 4.1 Apply (article profile, v1)

1. **Frontmatter hygiene.** Ensure `---`-delimited block; normalize keys
   already present (no reordering in v1 — reorder diffs are large and
   opinionated); ensure exactly one blank line after closing `---`.
2. **Trailing whitespace.** Strip trailing spaces/tabs on all lines, with one
   exception: preserve the two-space hard-break *only* if the file already
   uses it consistently (>50% of non-blank lines end in two spaces — almost
   never true; default strips). Rationale: trailing whitespace is invisible
   diff noise; hard-breaks via `\` are explicit.
3. **End of file.** Exactly one trailing newline; no trailing blank lines.
4. **Blank-line discipline.** At most one consecutive blank line in prose;
   exactly one blank line before and after: ATX headings, fenced code blocks,
   blockquotes, lists (as blocks), thematic breaks, tables, footnotes
   definitions. Collapse 3+ blank lines → 1. (Beauty comes mostly from this
   one rule.)
5. **Heading style.** Normalize to ATX (`#`–`######`), no closing hashes
   (`## Foo ##` → `## Foo`); require exactly one space after the run of
   `#`s; enforce heading hierarchy on write — no skipped levels (H2→H4 is
   either promoted to H3 or warns; pick warn-first, fix with `--fix-levels`).
   H1: at most one, must be first heading if present; articles *may* omit H1
   (title lives in frontmatter/filename) — formatter never inserts one.
6. **List markers.** Unordered → `-` (matches vault convention); normalize
   indentation to 2 spaces per level; one space after marker; checkbox
   `- [ ]` / `- [x]` spacing canonicalized. **Ordered content lists are never
   renumbered** (`1.` `1.` `1.` "all-ones" style is valid Markdown and
   renumbering fights section numbers visually).
7. **Emphasis/code canonicalization.** `__bold__` → `**bold**` (Obsidian
   renders both; `**` dominates the vault); inline code keeps single
   backticks; normalize fence character to backtick, length ≥3, info string
   trimmed (` ```rust ` stays, trailing spaces go).
8. **Thematic breaks.** `***`, `___`, `---` (outside frontmatter) → `---`
   with blank lines around. (Careful: `---` at file start is frontmatter —
   reuse the existing `strictly_closed_frontmatter_end` logic in
   `src/native/markdown.rs`.)
9. **Blockquotes.** `>foo` → `> foo`; nested `>>` → `> >`; blank-line
   discipline applies; never rewrap quote contents.
10. **Footnote definitions.** `[^a]:text` → `[^a]: text`, grouped at end of
    containing section (not moved across sections in v1 — moving is
    diff-large; only spacing normalized).
11. **Link hygiene (safe subset).** Trim whitespace inside wikilink targets
    (`[[ foo ]]` → `[[foo]]`); never rename targets; never touch display text
    `[[target|display]]` or embeds `![[...]]`; never touch URLs or bare-URL
    angle brackets.

### 4.2 Explicitly never do (v1)

- **Never rewrap prose.** No 80/100-col fill. Obsidian soft-wraps; hard wraps
  create whole-paragraph diffs on every edit and destroy `git blame`. This is
  the rule formatters most often get wrong for vaults.
- **Never touch inside fenced code blocks, math blocks (`$$`), or `<pre>`.**
  Reuse the existing `fenced_lines` scanner; extend to math.
- **Never touch task lines** (`- [ ]`, `- [x]`, `- [/]`, scheduled/dependsOn
  fields, block IDs `^id`) beyond trailing-whitespace stripping. Task lines
  belong to `task reconcile`/`task archive`, not the prose formatter.
- **Never align Markdown tables** (pipe padding). Alignment diffs are huge
  and Obsidian renders unaligned tables identically.
- **Never enforce sentence/prose style** (title case, Oxford comma, smart
  quotes, line-length nits). Style-lint is a separate tool with a separate
  off-switch.
- **Never reorder sections.** The formatter is order-preserving; moving
  content is an authoring act.

### 4.3 Why this rule set

Every rule above is (a) checkable by eye in a diff, (b) provably idempotent,
(c) invisible-or-beautifying in Obsidian reading view. Anything failing any of
the three (line wrapping, table alignment, quote reflow) is cut — that
discipline is what makes the formatter trustworthy enough to run on save or in
`nightly`.

---

## 5. Section numbering (the hard part)

### 5.1 The decision: view by default, bake only on export

| Approach | How | Pros | Cons |
|---|---|---|---|
| **V1. CSS counters (recommended default)** | `cssclasses: [numbered]` derived from `doctype` + a `numbered-sections.css` snippet; `body` resets, `h2::before { counter-increment …; content: counter(…) ". " }` | Zero vault diffs; instantly beautiful (styling, tabular nums, dimmed sub-numbers); heading links (`[[note#Foo]]`) never break; trivially toggled per-file | Numbers absent in raw source / non-Obsidian renderers / RSS |
| **V2. Export-time materialization** | `bob article export note.md` emits numbered copy to stdout/file for blog/PDF/RSS | Single code path (same counter algorithm); vault stays clean; publish pipeline gets exactly what it needs | Requires wiring the blog publish step to call it |
| V3. Baked into vault text (`## 2.1 Foo`) | `bob article number --write` rewrites headings | Numbers visible everywhere incl. git/raw | **Rot, diff noise, link breakage** (see §2); needs escape hatches; highest maintenance |

Recommendation: ship V1 + V2. Ship V3 only as an explicit `--write` behind a
flag, documented as "for snapshots sent outside Obsidian", never as the
steady state. If Bryan later insists every article file *contain* its numbers,
V3's algorithm below is specified and idempotent — but default matters, and
the default must be clean-source.

### 5.2 Numbering algorithm (shared by V1/V2/V3)

Same counter core in Rust (for export/baked) mirrored in CSS (for view); the
two must agree on one fixture file in `tests/`.

- **Scope:** ATX headings only (`src/native/markdown.rs::atx_heading`
  already parses these); Setext headings: convert to ATX first or ignore
  (recommend: convert `===`/`---` underlines to `#`/`##` during format, then
  number — one less heading dialect).
- **H1 is the title: unnumbered, excluded from counters.** Numbering starts at
  the first H2 as `1`. (`sase_blog_contents.md`: `# The Abstractions` stays
  bare; `## Gates -> Plans -> Epics` → `1`, `## Beads` → `2`, …;
  `#### Skills, memory, …` under `## Agent CLIs` → `3.1` — wait, it is H4
  under H2 with no H3 parent: see skipped-level rule.)
- **Depth mapping:** H2→depth 1, H3→depth 2, …, H6→depth 5. Counter vector of
  length 5; on visiting depth *d*: increment `c[d]`, zero all deeper, render
  `c[1..=d]` joined by `.`.
- **Skipped levels:** H2 followed directly by H4. Options: (a) treat at actual
  depth (`0.0.1`-style — ugly), (b) clamp to parent+1 (H4 behaves as H3 →
  `3.1`), (c) error. Recommend **(b) clamp + `--strict` warning** naming the
  line, matching the §4.1 hierarchy rule. The example file above has exactly
  this shape (`####` under `##`), so clamp-first is required for the flagship
  file to number sensibly.
- **Skipped content:** ignore headings inside fenced code blocks, math
  blocks, HTML comments, frontmatter, and blockquotes (`> # not a section`).
- **Opt-outs:** a heading ending with `<!-- no-number -->` (or carrying
  `{#no-number}`) is unnumbered and does not advance counters; its children
  attach to the nearest numbered ancestor. Also: `number_sections: false`
  disables the whole file; `<!-- numbers: restart -->` restarts at 1
  (appendix pattern); headings matching `Appendix` start `A, B, …` lettered
  counters (v2 — specify now, implement later).
- **Idempotency (V3 bake):** strip a leading `^(\d+[.\)]\s?)+` / `^([A-Z]\.)`
  pattern from every heading before recounting, then apply. Running twice =
  running once. Never strip numbers that are *part of the title* (`## 2001: A
  Space Odyssey` — guard: only strip when the numeric prefix is followed by a
  space and the remaining title is non-empty *and* the prefix matches the
  computed counter shape; otherwise leave and warn).
- **Beauty details:** render `1.` `1.1` `1.1.1` with `font-variant-numeric:
  tabular-nums`; sub-numbers (`1.1` portion) at reduced opacity in CSS;
  non-breaking space between number and title so wraps indent cleanly;
  numbers excluded from Obsidian heading-link slug generation (CSS `::before`
  content is — conveniently — already excluded from slugs, another argument
  for the view approach).

### 5.3 Worked example (`sase_blog_contents.md`)

Source (unchanged in vault):

```markdown
# The Abstractions
## Gates -> Plans -> Epics
## Beads -> Sidecar repos
## Agent CLIs
#### Skills, **memory**, provider interface, NOT hooks
#### Agent presentation / organization (…)
## VCS and workspace operations
```

Rendered / exported view:

```text
The Abstractions                      (unnumbered H1)
1  Gates -> Plans -> Epics
2  Beads -> Sidecar repos
3  Agent CLIs
3.1  Skills, memory, provider interface, NOT hooks     (clamped H4→H3-slot)
3.2  Agent presentation / organization (…)
4  VCS and workspace operations
```

Note the `**memory**` inside a heading: numbering must not disturb inline
formatting — strip/keep spans verbatim, count headings only.

---

## 6. Where it lives (implementation shape)

Follow the vault's existing authority split: **`bob-cli` owns grammar and
rewrites; the Obsidian plugin owns rendering.** (This mirrors the accepted
thin-client posture for capture: plugins never parse grammar.)

- **New command group `bob article`** (noun group with a stated membership
  rule per CLI rules: "commands that format, number, check, and export
  `doctype: article` notes"):
  - `bob article format [--write|--check|--diff] [PATH…]` — the §4
    formatter. Defaults: files with `doctype: article` (explicit paths
    override the filter with a warning). `--check` exits nonzero on
    would-change (for `nightly`/CI); `--diff` previews.
  - `bob article number [--write|--check] [PATH…]` — V3 baked numbering,
    explicit only; default action with no flag is to *print* the numbered
    outline (dry-run), never to mutate.
  - `bob article export [--to stdout|file] [--number] [--toc] NOTE` — V2
    publish artifact: frontmatter-aware, numbered, optional TOC prepended as
    Markdown list with anchor links.
  - `bob article adopt [--design-doc|--memo] NOTE` — adds the §3 frontmatter
    stanza (idempotent; refuses when `doctype` already set to a different
    value without `--force`).
- **Rendering (bob-plugins side, small):** one `numbered-sections.css`
  snippet + automatic `cssclasses: [numbered-sections]` injection *at render
  time by the plugin* (never written to the file — the file keeps only
  `doctype:`; presentation stays derived). Reading view + preview + print.
- **Automation:** add an `article format --check` step to `bob nightly`
  (warn-only for one release, then enforce); *do not* hook it into
  `task reconcile` (task engine must never reflow prose — separation of
  powers). Obsidian on-save formatting via existing plugin hooks comes after
  the CLI is trusted.
- **CLI-rules compliance:** short flags for all public longs (`-w/--write`,
  `-c/--check`, `-d/--diff`); alphabetical options; new group documented in
  `bob --help` Vault section; hidden-alias discipline for any renames (none
  expected — new surface).

Why not a standalone `prettier`/`mdformat` plugin? Three reasons: (1) generic
formatters rewrap prose and realign tables (§4.2 forbids both); (2) none
understands vault tokens (wikilinks, block IDs, inline fields, `[[link|alias]]`
display text) — a generic tool *will* mangle them eventually; (3) the repo
already has the Markdown primitives (`markdown.rs`: fences, ATX, Setext,
frontmatter) and the test harness (`cargo test`, golden files) — the marginal
cost of a vault-native formatter is low and the control is total.

---

## 7. Adjustments to the requirements (explicit)

| # | Original ask | Adjustment | Why |
|---|---|---|---|
| 1 | "specify a file is an article/design-doc" (mechanism open) | Pin to `doctype: article` frontmatter (§3); `design-doc`/`memo` become future enum values, not parallel mechanisms | One predicate, no link breakage, Dataview-ready |
| 2 | Auto-format (rules TBD) | Adopt the §4 allow/deny lists; **no prose rewrapping, no table alignment, no section moves** in v1 | Keeps diffs reviewable and `vault-sync` history clean |
| 3 | Auto-number sections "starting at 1 with sub-sections", implied baked | **Numbers are a view + export artifact by default; baking requires `--write`** (§5) | Prevents link rot and renumber churn; strictly more beautiful |
| 4 | (implied) H1 numbered too | H1 unnumbered title; numbering starts at first H2 | Matches publishing convention; the example file reads wrong otherwise |
| 5 | (implied) all files eventually | Scope v1 to `doctype: article` only; ordinary notes untouched | Blast-radius control; earns trust before any wider rollout |
| 6 | (new) TOC | Defer auto-TOC to v2 (`toc: true` reserved now); do not block v1 on it | TOC anchor generation has its own slug/escape design; ship numbering first |

---

## 8. Recommended solution (phased)

- **Phase 0 — marker + view (days).** `doctype:` schema doc; `bob article
  adopt`; CSS `numbered-sections` snippet + render-time class injection;
  `sase_blog_contents.md` adopts `doctype: article` as the pilot. Value from
  day one, zero rewrite risk.
- **Phase 1 — formatter (1–2 weeks).** `bob article format` implementing §4.1
  with `--check/--diff/--write`, golden-file tests incl. the pilot note,
  idempotency tests (format∘format = format), adversarial tests (tasks, block
  IDs, math, nested fences). Nightly `--check` warn-only.
- **Phase 2 — export (days, after Phase 0).** `bob article export --number
  [--toc]` with the §5.2 algorithm; wire the sase-blog publish step to it;
  CSS↔Rust counter parity fixture.
- **Phase 3 — baked `--write` (only on demonstrated need).** `bob article
  number --write` with idempotent strip-then-recount + opt-out comments;
  documented as snapshot/export tool, never as steady state.
- **Phase 4 — widen (only after trust).** Consider `doctype: design-doc |
  memo`, per-doctype profiles, on-save format, TOC, appendix lettering.

Success criteria: pilot file formatted + view-numbered with zero link
breakage; `format --check` green on second run always; `nightly` log shows
the article step; no `vault-sync` diff larger than the author's own edit.

## 9. Open questions for Bryan

1. Is view-numbering (clean source) acceptable, or must the raw `.md`
   contain literal numbers? (Determines whether Phase 3 is needed at all.)
2. Should `design-doc` differ from `article` in formatting, or is it just a
   label today? (Determines whether `doctype` needs profiles in v1.)
3. May `bob nightly` eventually *write* article formatting, or should it
   forever only *check* and report? (Writes at 3am need full trust first.)

---

*Method: independent research against the workspace checkout (`src/native/
markdown.rs`, `src/runner.rs`, CLI rules, vault frontmatter conventions) and
the live `~/bob` vault including the pilot note; no peer-report consultation.
No code changed; no verification commands run beyond read-only inspection
(formatter/numberer do not exist yet to test).*
