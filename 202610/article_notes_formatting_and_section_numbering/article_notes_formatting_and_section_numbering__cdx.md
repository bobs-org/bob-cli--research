---
title: "Document mode for Bob: beautiful formatting without fragile headings"
researcher: cdx
date: 2026-10-16
status: independent-research
---

# Document mode for Bob: beautiful formatting without fragile headings

The idea is good: some vault files are sustained pieces of writing, and should receive a more deliberate treatment than working notes. The strongest design is an explicit **document mode**, with conservative source formatting and section numbers computed for display. I would avoid continuously rewriting numbers into the vault's heading text.

This report evaluates the request independently. I did not read the other swarm researchers' reports, transcripts, or conclusions. This is design research, not an implementation or a change to the vault.

## What the existing system tells us

I inspected the current bob-cli and bob-plugins checkouts, queried the example note read-only, studied an existing numbering plugin locally, and consulted primary documentation. Local source references below are pinned to the inspected commits.

The example is more interesting than a conventional article template. `bob query` reports `sase_blog_contents.md` with `created` and a `parent` pointing to `sase_blog.md`, with no document-mode property in the returned frontmatter. `bob capture-sections -r sase_blog_contents -f json` returns ten non-Tasks ATX headings, including:

```markdown
# The Abstractions
## Gates -> Plans -> Epics
## Beads -> Sidecar repos
## Agent CLIs
#### Skills, **memory**, provider interface, NOT hooks
#### Agent presentation / organization (tribes, clans, families, hoods, metadata/files/tools panel)
## VCS and workspace operations
## Xprompts / Agent control flow (forks/waits/queues)
## Project Management (hoods, agents sidecar, artifacts)
## Routines and Jobs
```

This is an observed outline, not a reproduction or review of the note body. The section command omits Tasks headings and is not a general Markdown parser. I have not verified the note's complete prose, embeds, existing heading links, or rendered appearance. In particular, the H1 could be a first section or an article title; its spelling alone cannot settle that.

Three repository findings materially affect the design:

- **`type` already carries Bob semantics.** Area and project detection recognizes `[[area]]` and `[[project]]` in `type`. Replacing it with `type: article` could change unrelated behavior. Document mode should be an independent property. [Project detection source](https://github.com/bobs-org/bob-cli/blob/31528a11bc3162e80f4e40011af4de4cad64c995/src/native/projects/scan.rs#L332)
- **Literal heading names already have consumers.** The task section picker compares titles to the exact string `Tasks`; a Reading-view heading chip also looks for Tasks at the start of heading text. Persisting `## 4 Tasks` would require a compatibility audit. These are source-level findings; I did not exercise those interactions in Obsidian. [Task routing source](https://github.com/bobs-org/bob-plugins/blob/86cebc9c4dcf83a238b387127b5eedf8c68f9725/plugins/task-status-cycler/src/040-sections.js#L370), [heading rendering source](https://github.com/bobs-org/bob-plugins/blob/86cebc9c4dcf83a238b387127b5eedf8c68f9725/plugins/bob-ledger-tools/src/220-plugin-heading-and-review.js#L154)
- **Rendering hooks already have a local precedent.** Ledger Tools registers both a Markdown postprocessor and an editor extension for heading adornments. This makes a focused document plugin a reasonable fit, without adding document concerns to the task plugin itself. [Lifecycle source](https://github.com/bobs-org/bob-plugins/blob/86cebc9c4dcf83a238b387127b5eedf8c68f9725/plugins/bob-ledger-tools/src/170-plugin-lifecycle.js#L402)

## Critique and justified requirement changes

The valuable requirement is persistent author intent: “this file is a document.” Formatting and numbering are consequences of that intent, rather than the definition of the document. Articles, design docs, and outlines can share a treatment without becoming one bibliographic type or moving into one folder.

Numbering helps readers discuss a design, find a subsection, and understand a long outline. It can also make a short article look bureaucratic. The feature should allow document styling and cleanup with numbering turned off. Do not infer eligibility from length, heading count, filename, parent, or the presence of an H1.

I recommend these explicit adjustments to the original request:

| Adjustment | Reason and consequence |
| --- | --- |
| Treat “always” as a durable per-file designation, not a promise that every application renders it identically. | The property survives moves, sync, and plugin disablement. Automatic behavior requires the responsible tool to be running. |
| Generate numbers in Obsidian; materialize them only in an explicit exported copy. | Inserting a section changes presentation without changing vault heading destinations or creating a large source diff. Raw Markdown viewed elsewhere remains unnumbered by default. |
| Separate safe formatting from editorial rewriting. | Cleanup may change whitespace at verified block boundaries. It must not rewrite prose, capitalization, hierarchy, task structure, or meaningful typography. |
| Number actual section ancestry when heading levels are skipped, and report the gap. | The example's H2-to-H4 jump can remain intact and display a sensible subsection number. Never silently promote/demote headings or invent zero-valued sections. |
| Make a short adoption preview part of enabling the feature on an existing note. | The author chooses whether an H1 is a title or section. Existing numeric prefixes are never guessed away. |

These adjustments favor the writing and link graph over rigid source uniformity. If numbers must be visible in raw Markdown in every editor, that is a different requirement and changes the recommendation; the explicit source-numbering alternative is evaluated below.

## A small, durable opt-in contract

Use one boolean frontmatter property:

```yaml
bob_document: true
```

Obsidian presents booleans as checkboxes. Keep optional controls flat so they remain editable in the Properties UI; nested properties are not supported there. [Obsidian Properties](https://help.obsidian.md/properties)

The complete initial contract should stay small:

| Property | Meaning | Default |
| --- | --- | --- |
| `bob_document` | Explicitly enables document treatment. Only YAML boolean `true` enables it. | Disabled when absent or false. |
| `bob_number_sections` | Shows computed section numbers. | True for enabled documents. |
| `bob_section_level` | Shallowest heading level treated as a section, integer 1–6. | 2, fitting a conventional unnumbered H1 title. |

An absent override inherits the documented default; an invalid value produces a useful diagnostic and disables the affected behavior. Duplicate control keys or malformed YAML disable automatic mutation rather than choosing whichever value a parser happens to return. Do not turn string `"false"` into a truthy opt-in.

`type`, `tags`, `parent`, `created`, and other existing metadata retain their meanings. The marker is not a publishing instruction and does not add this note to task capture or other Bob workflows. Disabling document mode stops future treatment; undo or history restores previous whitespace if desired.

Why this instead of alternatives?

- A tag is excellent for browsing, but a hashtag pasted into content should not authorize automatic writes.
- A folder rule couples behavior to location and excludes documents scattered among project notes.
- `cssclasses` is a useful presentation hook, but makes a stylesheet name responsible for write policy. Derive a runtime document class from the semantic property instead. Explicit `cssclasses: [bob-document]` can be offered as an optional CSS-only interoperability aid, never as a second authoritative switch. Obsidian already supports per-note CSS classes. [CSS snippets](https://help.obsidian.md/snippets)
- A filename registry breaks the direct relationship between a note and its treatment when notes move or are copied.

For the example, offer these two previews before applying the designation:

| Outline text | Base 1: H1 is a section | Base 2: H1 is a title |
| --- | --- | --- |
| The Abstractions | 1 The Abstractions | The Abstractions |
| Gates -> Plans -> Epics | 1.1 Gates -> Plans -> Epics | 1 Gates -> Plans -> Epics |
| Agent CLIs | 1.3 Agent CLIs | 3 Agent CLIs |
| Skills, **memory**, … | 1.3.1 Skills, **memory**, … | 3.1 Skills, **memory**, … |

For `sase_blog_contents.md`, I would tentatively choose base 1 because its first heading reads like a subject section; the author should confirm that interpretation in the preview. The H4 gaps generate a warning in either interpretation. No hierarchy correction is required to adopt the feature.

## Numbering that readers can trust

### Define the section tree, then count it

Numbers should derive from the whole document's parsed heading structure, independently of which headings happen to be visible on screen.

1. Only document-level headings participate. Exclude headings inside code, comments, quoted material, callouts, list items, HTML blocks, math blocks, and embedded documents. Support actual ATX and Setext headings; do not interpret every line beginning with `#` as a section.
2. Headings shallower than `bob_section_level` are unnumbered dividers or titles. They clear the current parent stack, but do not reset the document's root counter.
3. For each eligible heading, pop ancestors at the same or deeper raw heading level. Its parent is the nearest preceding eligible shallower heading, if one remains; otherwise it is a root section.
4. Increment that parent's child counter, starting at 1. Join the actual ancestor ordinals with periods: `1`, `1.1`, `1.1.1`, `1.2`, `2`. Reset only descendant counters when moving to a new sibling.
5. A skipped level is a structural diagnostic, not a missing invisible parent. H2 followed by H4 becomes a direct parent/child in the numbering tree, without changing the saved H4.

This policy is a deliberate design choice, not an assertion that raw H4 and H3 are interchangeable. The warning lets the writer decide whether a gap is intentional. A “Fix heading hierarchy” action, if ever added, must show its own diff.

Keep these edge cases explicit:

- Empty headings receive no number; withhold numbering for their unfinished subtree until the boundary is clear, and show a diagnostic without editing the draft.
- Duplicate titles have separate positions and ordinals. Preserve existing link resolution behavior and warn about ambiguous targets; numbering does not create identity.
- A title such as `2026 outlook`, `3.14 reasons`, or `10 lessons` is authored text. Prefix it visually if it is a section; never strip its digits.
- All eligible headings through H6 participate. Do not impose a hidden three-level limit; suggest shallower organization if the result becomes unwieldy.
- One counter space belongs to each source document. A section transclusion keeps its source-document numbers; it must not consume the host document's counters. If its source position cannot be resolved confidently, omit the adornment rather than guess.
- A small optional directive, on its own line immediately before a heading, can exclude a whole section subtree: `<!-- bob:unnumbered -->`. It consumes no ordinal. It is separate from formatting suppression and never appended to the heading text. Do not build appendix alphabets, restart schemes, or dozens of numbering styles in version one.

### Keep heading identity separate from the number

Obsidian documents heading links using heading text, including nested heading paths. Consequently, changing the heading text can change the target address; source rewriting cannot assume every inbound link will be repaired. [Internal links](https://help.obsidian.md/links)

For example, leave this saved source unchanged:

```markdown
## Tradeoffs

See [[design#Tradeoffs]].
```

Render a separate number span/widget before the heading's authored text. Keep the existing DOM anchor, source heading text, and link target. Reordering a preceding section can change the visual number from 3 to 4 with no heading-link rewrite.

This protects links against **renumbering**; it does not make links survive an actual heading rename. Existing explicit block IDs stay untouched. Do not add block IDs to every heading just to compensate for a numbering mechanism that mutates titles.

The default clipboard continues to copy authored Markdown. Provide a clearly named “Copy numbered Markdown” operation for sharing. It creates a derived copy and rewrites validated same-document heading references in that copy as needed; it never renumbers the original vault file. HTML/PDF export should keep stable unnumbered anchor IDs with visible number spans. Pandoc's output-time section numbering is a useful precedent, but its dialect and export path still need an Obsidian compatibility pass. [Pandoc numbering options](https://pandoc.org/MANUAL.html#options-affecting-specific-writers)

## Formatting rules worth automating

A good formatter makes the text quieter and the changes smaller. Beauty should come mainly from typesetting, not continuous source churn.

### Default source changes

Use parser-confirmed, document-level boundaries and minimal edits:

| Rule | Scope and guard |
| --- | --- |
| One blank line between frontmatter and the first body block. | Preserve frontmatter bytes, key order, quoting, comments, and unrelated properties. |
| One blank line around a document-level heading. | Never insert a leading blank line at file start; never split a block or edit a protected boundary. |
| Collapse runs of excess blank lines between ordinary top-level blocks to one. | Preserve blank lines inside lists, quotes, code, math, HTML, tables, and explicit formatting-off ranges. |
| One final newline in ordinary text files. | Preserve the file's existing LF/CRLF convention; decline this edit when EOF belongs to an incomplete/protected construct. |

These rules are intentionally narrower than a full Markdown pretty-printer. Even blank lines are not globally cosmetic: list spacing can affect whether a list is tight or loose. Identify syntactic context before touching whitespace. CommonMark's heading, container, and block rules provide the baseline; Obsidian extensions require additional handling. [CommonMark specification](https://spec.commonmark.org/0.31.2/)

### Preserve by default

Preserve paragraph wrapping and all authored line breaks; never globally trim trailing spaces, which may encode hard breaks. Retain indentation, ordered-list start values, checkbox characters, tasks' inline metadata and block IDs, reference definitions, footnotes, table contents, and link spelling. Keep wiki links, embeds, image sizing, `%%` comments, callouts, and Dataview/Tasks/Mermaid code opaque to source formatting. Do not format fenced code merely because its language is recognized. [Obsidian syntax](https://help.obsidian.md/syntax), [advanced syntax](https://help.obsidian.md/advanced-syntax)

Do not auto-capitalize headings, remove their punctuation, replace ASCII punctuation with smart characters, convert a paragraph into bullets, sort sections, rewrite Setext headings, or convert multiple H1 sections into a title. Those are editorial decisions. Suggest sentence-case headings in a template; do not enforce them by rewriting user text.

Defer table alignment, list normalization, reflow, and emphasis-marker normalization to separate explicit actions. They can be added after real examples demonstrate a benefit. Prettier's documented `proseWrap: preserve` and `embeddedLanguageFormatting: off` illustrate useful restraint, but those settings alone do not establish safety for the whole Obsidian dialect. [Prettier options](https://prettier.io/docs/options#prose-wrap)

Support `<!-- bob:format off -->` / `<!-- bob:format on -->` as standalone range directives for deliberate layouts. Preserve the enclosed source exactly. An unmatched off marker extends to EOF and produces a diagnostic. This suppresses source edits, not visual section counting; numbering exclusions use the separate directive above.

### Visual treatment

Scope the document style to the opted-in note's own content container. Prefer a single restrained reading measure around 70 characters, generous responsive side padding, and a line height around 1.6. Respect user font choices and Obsidian's theme variables. Use a clear title and H2/H3 scale, with more space before a section than after it, rather than decorative rules everywhere.

Numbers should sit beside the heading, slightly quieter and smaller, with tabular numerals and a consistent gap. Keep them readable in both light and dark themes. On narrow screens they stay inline; avoid a fixed gutter that clips deep numbers or steals writing space. Wrapped heading text should align cleanly, and the collapse control must remain clickable.

Use real accessible text for numbers in Reading view, announced once with the heading. In the editor, adornments must not capture the caret or create unexpected tab stops. Verify the actual accessibility tree and reading order; CSS-generated content alone is not an acceptance test. Preserve heading semantics, keyboard navigation, focus outlines, and zoom behavior. Do not add a new loud badge to every heading.

A compact optional document outline is more useful than a permanently inserted Markdown table of contents. It should use the same numbering model. Leave Obsidian's built-in outline unchanged initially; document that limitation rather than patching private outline internals.

## Automation without fighting the writer

“On save” needs a precise meaning in an app that already saves during typing. Default to formatting the departing document on a deliberate note switch or close, plus an explicit “Format document” command. A manual-save gesture may call the same command. Linter already documents save and file-switch workflows, so this interaction has an established precedent. [Linter running rules](https://platers.github.io/obsidian-linter/usage/running-rules/)

Do not run a full source rewrite on every edit or a fixed timer. Live numbers can update immediately because they are decorations. Source cleanup can wait for a clear editing boundary. An idle-format option can come later if testing shows it helps; it must defer during IME composition, preserve selections and scroll position, and skip active/incomplete blocks.

The writer safety contract should be concrete:

- Transform active content from its live editor buffer, never a stale disk read. Apply the minimal changes as one undoable editor transaction, mapped through selections. Two open panes for one note must not receive independent conflicting writes.
- When a departing editor is no longer available, write only after its current buffer is safely persisted. For genuinely closed notes use `Vault.process()`, and verify the exact preimage inside its callback before applying previously calculated edits. Obsidian documents `process()` as guarding the read/modify interval within its API. It is not a cross-process or cross-device lock. [Vault API guide](https://docs.obsidian.md/Plugins/Vault)
- Mark self-generated changes, coalesce duplicate work, and write nothing when output is identical. Undo must not immediately trigger the same auto-format again; suppress automatic reapplication until a fresh authored edit or explicit command.
- A missing or malformed control property, uncertain parse, stale source map, conflict file, or changed preimage means skip with a specific diagnostic. Preserve the original bytes. Do not “recover” by running a regex rewrite.
- Formatting is local editor maintenance. Do not add a second background vault watcher or a formatter inside Git sync/nightly by default. Multiple machines already write and sync this vault; the smaller the automatic write surface, the better.

This means an external agent's edit is formatted when the document next passes through the editor workflow, rather than guaranteeing immediate mutation while Obsidian is closed. If continuous headless formatting is important, add a single explicit headless consumer of the same formatter after the first release. Make that limitation visible in the product documentation.

## Existing options and their tradeoffs

| Option | What it buys | Why I would or would not choose it |
| --- | --- | --- |
| CSS snippet with counters | Fast visual prototype; native per-note styling hook. | Useful to explore typography. Insufficient as the numbering authority: the editor renders only a viewport, so offscreen headings cannot reliably contribute DOM counters. Embeds and partial rendering complicate Reading view too. |
| Number Headings plugin | Existing per-file settings, nested numbering, and source edits in editor transactions. | Credible low-cost alternative when persisted numbers are an explicit requirement. Its inspected implementation polls every ten seconds and uses prefix recognition that can consume meaningful leading digits. It does not establish the desired link-stability contract. |
| Obsidian Linter | Many formatting rules and existing save/switch triggers. | A good independent tool if the vault already wants those rules. Its documented per-note mechanism disables rules; it is not a ready-made affirmative Bob document profile. “Header increment” fixes heading levels, not decimal section numbering, and documented heading handling is ATX-only. |
| Prettier or dprint on complete files | Mature general-purpose formatting engines and headless operation. | More source normalization than this first use case needs; Obsidian-specific syntax and link destinations need demonstrated preservation. Neither removes the need for an explicit opt-in and a numbering model. |
| Pandoc on export | Numbered published artifacts with clean authoring source. | Appropriate downstream; an exporter does not supply live editor numbering or safe vault cleanup by itself. |
| Focused Bob document plugin | Exact marker, typography, live numbers, and conservative formatting under Bob's control. | Recommended, provided the source formatter remains intentionally small and parser-aware. Costs include a rendering/source-mapping layer and an acceptance corpus. |

The CSS concern follows from Obsidian's documented viewport behavior: only nearby editor content is rendered. Compute ordinals from a complete heading index, and render widgets only where needed. [Obsidian viewport guide](https://docs.obsidian.md/Plugins/Editor/Viewport), [decoration guide](https://docs.obsidian.md/Plugins/Editor/Decorations)

I inspected Number Headings at commit `4cd3fac7a2394648e8f8ef7193622ecb3d6eb02f` (manifest version 1.16.0). Its code batches source numbering in `editor.transaction`, but triggers automatic work on a ten-second interval. A small Node experiment using its numeric prefix regex recognized `## 2026 `, `## 3.14 `, and `## 10 ` as replaceable prefixes in the headings `2026 outlook`, `3.14 reasons`, and `10 lessons`. This tests the prefix recognition in isolation; I did not run the entire plugin or claim that every possible configuration exhibits it. [Timer source](https://github.com/onlyafly/number-headings-obsidian/blob/4cd3fac7a2394648e8f8ef7193622ecb3d6eb02f/src/main.ts#L319), [prefix recognition](https://github.com/onlyafly/number-headings-obsidian/blob/4cd3fac7a2394648e8f8ef7193622ecb3d6eb02f/src/textProcessing.ts#L17), [source transactions](https://github.com/onlyafly/number-headings-obsidian/blob/4cd3fac7a2394648e8f8ef7193622ecb3d6eb02f/src/numbering.ts#L155)

This is not just a theoretical reason to be careful: an upstream user also reports IME composition interruption from automatic numbering. Treat that as a bug report supporting the need for interaction tests, not as a reproduced defect in the current Bob environment. [Upstream issue 85](https://github.com/onlyafly/number-headings-obsidian/issues/85)

Linter explicitly describes header increment as changing level jumps, and notes that its heading rules do not support Setext. Its disabling mechanism is useful context, but should not be mistaken for a complete implementation of the requested opt-in. [Linter heading rules](https://platers.github.io/obsidian-linter/settings/heading-rules/), [per-file disabling](https://platers.github.io/obsidian-linter/usage/disabling-rules/)

Dprint also documents range-ignore comments and formatter delegation for fenced code. Those are useful features to evaluate if broad source normalization later becomes desirable; they do not prove Obsidian compatibility. [Dprint Markdown documentation](https://dprint.dev/plugins/markdown/)

If persistent source numbering wins despite the tradeoffs, require a previewed migration, parser-based heading recognition, transactional updates of all resolvable inbound heading links and embeds, refusal on ambiguous targets, preservation of semantic leading numbers, and an audit of literal heading consumers. External links and unavailable consumers still cannot all be repaired. I would ship that as an explicit operation on selected files, not the automatic default. A global “strip numbers, then add them back” regex is not acceptable.

## Implementation shape and acceptance criteria

Build a separate `bob-document-tools` plugin in the bob-plugins source repository. Keep the responsibility narrow rather than extending the already broad task/navigation plugins. Deployment should follow the existing `bob plugins sync --repo <opened-checkout>` workflow; installed files under the vault are not the source of truth. [Plugin management documentation](https://github.com/bobs-org/bob-cli/blob/31528a11bc3162e80f4e40011af4de4cad64c995/docs/plugins.md)

Structure it around pure, testable operations:

```text
frontmatter + source
        |
        v
eligibility + parsed blocks/headings + diagnostics
        |                                  |
        v                                  v
section tree + ordinals             minimal whitespace edits
        |                                  |
        v                                  v
editor / Reading view / export     guarded editor or vault writer
```

The parser must expose ranges and containment. Use the editor's current syntax information for active documents and a tested source parser for closed ones. Metadata-cache heading locations are useful only when their source version matches. Protect Obsidian-specific constructs that the source parser cannot interpret. A complete heading inventory is required before numbers are published; if parsing is partial, omit affected adornments temporarily rather than assign numbers from the visible subset.

Bob's existing Rust Markdown helpers cover ATX headings, fences, Setext underlines, and some exclusions, but are not a complete lossless Obsidian parser. They are a useful test seed rather than a sufficient formatter by themselves. [Markdown helpers](https://github.com/bobs-org/bob-cli/blob/31528a11bc3162e80f4e40011af4de4cad64c995/src/native/markdown.rs)

Keep the first formatter core platform-neutral JavaScript with no direct filesystem or desktop subprocess dependency, so the plugin can run on desktop and mobile. A later CLI should reuse the exact engine, not introduce a second formatter with subtly different rules. Bob already embeds QuickJS for query execution, so embedding a compatible generated JS core is a plausible route; it requires a dependency/bundling spike before promising it. Do not add a Node installation requirement or a Rust-to-Wasm build merely to ship the first editor use case. [Existing QuickJS usage](https://github.com/bobs-org/bob-cli/blob/31528a11bc3162e80f4e40011af4de4cad64c995/src/native/dataview/tasks/js.rs#L253)

A future CLI could be a top-level `bob format-document PATH` with preview by default and mutually exclusive `-c/--check` and `-w/--write`. It must enforce the same opt-in, use vault-relative paths safely, reject symlink escapes, and document that atomic replacement alone cannot resolve a simultaneous external writer. New public long options need short aliases and sorted help per project conventions. This is a future interface sketch, not an existing command or a prerequisite for the recommended first release.

The acceptance gate should test actual invariants:

1. **Eligibility:** ordinary notes are byte-identical; moves preserve intent; invalid/duplicate control metadata never enables mutation; parent/type/tags remain unchanged.
2. **Semantics:** for supported valid inputs, `format(format(text)) == format(text)`; parsed prose, headings, links, list structure, and protected spans are preserved. Run a fixed real-world fixture corpus and generated block combinations.
3. **Numbering:** cover H1 title versus H1 sections, starting at 1, all depths, level gaps, upward jumps, duplicate/empty headings, semantic numeric titles, Setext, excluded subtrees, and counter resets.
4. **Obsidian dialect:** include fenced and indented code, unclosed fences, inline code, quotes/callouts, `%%` comments, YAML, HTML, math, Tasks/Dataview/Mermaid, wiki heading/block links, embeds, and CRLF.
5. **Editor behavior:** caret and multi-selection stability, one-step undo, no immediate reformat after undo, IME composition, folds, two panes, large files, stale caches, tab close/switch, and plugin unload/reload.
6. **Rendered behavior:** scroll from the middle, collapse earlier sections, render an embed before its source has been opened, and edit an early heading. Numbers must agree across Live Preview, Reading view, optional outline, and export without changing saved headings.
7. **Presentation:** manual snapshots on light/dark themes, narrow and wide panes, 200% zoom, long wrapping headings, deep numbers, keyboard collapse/navigation, screen-reader announcements, and print. No horizontal clipping or unreadable low-contrast numerals.

I would first prove eligibility, numbering, and source mapping on a synthetic copy of the example outline. Then validate the conservative formatter on representative documents; only after that enable it on `sase_blog_contents.md` through the adoption preview. Do not silently run a vault-wide migration or enable a second source formatter on the same files.

The remaining product choices are small: whether the example H1 is a title, how important numbering outside Obsidian is, and whether formatting while Obsidian is closed is genuinely required. They do not block an editor-first design. Rendering, export, and mobile behavior described here are proposed acceptance targets, not completed compatibility testing.

## Recommended solution

**Implement explicit document mode with `bob_document: true` in a focused Bob plugin.** Keep article/reference/project classification independent. Default to an unnumbered H1 title and H2 sections, and let an adoption preview set `bob_section_level: 1` for outlines such as the supplied example when its H1 is a real section.

Show decimal section numbers derived from actual heading ancestry in Live Preview and Reading view, beginning at 1 and supporting every Markdown heading depth. Warn about skipped levels while preserving source hierarchy. Keep heading text and link destinations stable; provide numbering in exported copies when needed.

Automatically apply only proven whitespace rules at deliberate editing boundaries, with one undoable transaction and strict source guards. Make typography do most of the beautification. This delivers the desired distinction, readable numbered sections, and a calmer writing surface while keeping the vault's content and existing Bob behavior dependable.
