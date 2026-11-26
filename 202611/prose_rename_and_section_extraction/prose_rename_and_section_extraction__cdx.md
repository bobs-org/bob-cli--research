# From article notes to prose: naming, section extraction, and reversible projects

Independent research by **cdx**, 2026-11-26. This report uses the supplied request, local source, audited project memory, and primary external documentation. No other report or researcher findings from this swarm were consulted. Research only: no product code, vault notes, or configuration was changed.

**Recommendation in brief:** rename the user-facing content type to **prose**, separate that type from automatic formatting, and build a conservative section-to-note extraction operation with a tested inverse. Preserve complex project content in linked prose companion notes when reducing a project to a task. Do not make flattening every child file into a task a prerequisite for reversibility.

**What exists today, and why a rename alone is insufficient.** The inspected versions were bob-cli `4dd787bceaa2c0f16e25336ec6b3ff65d6a731f5` and bob-plugins `7d8a7d4ac876740b45ee596e556f9d9519f489e1`. Source references below identify those snapshots; paths are repository-relative.

| Observed behavior | Evidence | Consequence |
| --- | --- | --- |
| Article is recognized through `type: "[[article]]"`. Formatting rejects mixed types, `^prj`/`^ref`, and actual `#task` checkbox lines. | bob-cli `src/native/articles/marker.rs`: `skip_reason`, `adopt_decision`, `body_refusals`; `docs/articles.md` | This is a specialized content role, not a label for every file containing sentences. |
| Articles default to numbered sections. Formatting also adjusts heading levels, whitespace, Setext headings, and heading references. | `src/native/articles/sections.rs`, `marker.rs`; `docs/articles.md` | A rename carries publication-like behavior into ordinary notes unless deliberately separated. |
| Even `section_numbers: false` removes number-shaped prefixes considered Bob-owned. | `src/native/articles/marker.rs:236`; `docs/articles.md`, N6/N9 | Numbering off does not mean preserving heading text. Literal `1.5 million users` is a counterexample. |
| Capture uses article-specific de-numbered heading identity. | `src/native/capture/sections.rs:241` onward; `src/native/projects/scan.rs:364` | Migration must cover capture and discovery, not just the plugin. |
| Promotion already turns bold drawers into project H2 sections; reversal restores drawers. | bob-cli `docs/projects.md:470`; bob-plugins `210-rename-and-line-context.js`, `111-project-seed-reqs.js` under `plugins/bob-navigation-hotkeys/src/` | Extend the existing representation boundary instead of inventing competing drawers. |
| Reversal rejects stray paragraphs, nested headings, and fenced blocks in section bodies. | bob-plugins `plugins/bob-navigation-hotkeys/src/210-rename-and-line-context.js:640`; `scripts/test-navigation-hotkeys-project-reversal.cjs:696` | Free-form project prose is an obstacle independent of child files. |
| Reversal refuses **any** child note. Child discovery follows `parent` frontmatter. | bob-plugins `plugins/bob-navigation-hotkeys/src/665-plugin-project-conversion.js:63`; `640-plugin-notes-and-task-move.js:3` | Article children are one instance of a broader ownership problem. |
| Article formatting writes the article and then inbound repairs; a drifted linker may be skipped after the article succeeds. | bob-cli `src/native/articles/inbound.rs:139`; `docs/articles.md` | Useful formatter infrastructure, but insufficient as the transaction contract for content moves. |

The existing article and project-reversal suites passed together with:

```text
node --test --test-reporter=dot scripts/test-navigation-hotkeys-project-reversal.cjs scripts/test-bob-articles.cjs
```

This verifies the inspected baseline tests, not the proposed feature. I did not inventory the live vault, exercise an Obsidian UI, or test a prototype. There is therefore no measured migration count, performance estimate, or claim that a particular hotkey is free.

**Naming: I tried to improve on “prose,” but would keep it.** The relevant test is which word distinguishes this content from projects, references, records, and notebooks, while remaining natural for both sections and files.

| Candidate | Advantage | Weakness | Judgment |
| --- | --- | --- | --- |
| **Prose** | “Prose note” and “prose section” are natural; no implied publication, completion, or minimum length. | Literally excludes verse and can sound paragraph-only; “a prose” is awkward. | Best fit if explicitly defined to permit supporting Markdown blocks. Say “a prose note.” |
| **Document** | Best broader alternative; covers plans, explanations, tables, code, and mixed text. | Every project/reference/record file is also a document; “document section” says little about behavior. More file-oriented. | Runner-up. Prefer it if the intended scope becomes arbitrary standalone Markdown, including predominantly non-prose material. |
| **Text** | Short and size-neutral. | Already means strings, a property type, and text files. | Too broad for the type vocabulary. |
| **Note** | Familiar and size-neutral. | Already the umbrella term and the unit captured into notebooks; “note note” is awkward. | Avoid as the specific type. |
| **Writing** | Broad, purposeful, not necessarily published. | “Writing section” sounds like an activity; “a writing” is unnatural here. | Good UI prose, weak schema name. |
| **Page** | Familiar in wikis. | Implies a boundary precisely when sections should work before extraction; also PDF pages. | Weak fit. |
| **Essay / article / draft** | Communicates authored material. | Genre or lifecycle restrictions; short explanations and finished documentation do not fit. | Too narrow. |
| **Content / body / material** | Broad enough for everything. | Does not distinguish a useful entity or behavior. | Too abstract. |
| **Fragment / passage / snippet** | Good for embedded pieces. | Undersells full documents and becomes false as content grows. | Useful names for source spans, not the type. |
| **Notebook** | Already collects general observations and ideas. | Bob notebooks are collections of note bullets with their own capture contract. | Keep distinct. |

This is a product-language judgment, not an externally established naming result. My suggested definition:

> A prose note is a free-form Markdown document whose primary purpose is to hold written content. It may contain headings, lists, tables, images, quotations, equations, and code. It does not acquire task or project behavior merely because it contains those blocks.

The distinction is **primary role**, not whether prose occurs somewhere in the file. A project remains a project while containing prose sections. A reference remains a reference while containing authored commentary and managed Highlights. Do not add `[[prose]]` alongside `[[project]]` to enable extraction.

A notebook remains a collection of discrete note bullets. The useful question is “am I writing a document, or collecting entries?” Their shared lack of project status is insufficient reason to merge them. Audited `glossary:notebook` and `decisions:notebook-routes-write-notes` make the distinction operational: notebooks forbid checkboxes, have different capture behavior, and constrain their parents.

**The useful idea is changing content boundaries cheaply.** Keeping small explanations in their working context and extracting them when they grow avoids premature file creation. The inverse makes reorganization less consequential. Obsidian's core Note composer already extracts selections into new or existing notes and merges notes, with template support; Org's refile moves outline entries under another heading. These establish a useful interaction precedent, not Bob-specific ownership or reversibility guarantees. [Obsidian Note composer](https://obsidian.md/help/plugins/note-composer), [Org refile](https://orgmode.org/manual/Refile-and-Copy.html).

Native Note composer is worth trying on a disposable example to judge the interaction. I would not make it Bob's authoritative implementation: its documentation does not establish preservation of Bob task identity, parent relationships, inherited defaults, or the transaction guarantees needed here. A thin Bob command can provide the familiar interaction while Bob owns the semantic operation.

The strongest critique of the original proposal is its dependency claim. Section extraction is useful independently, but **project-to-task reversal does not require every prose child to become inline text**. It requires an unambiguous home for every authored fact and relationship after the project container changes. A task linking to a preserved document can satisfy that requirement more safely than converting arbitrary Markdown to deeply indented list content.

**Requirements I would adjust explicitly.**

| Adjustment | Proposed requirement | Reason |
| --- | --- | --- |
| A1 — Narrow the definition | Replace “any file that needs to contain prose” with “a file primarily serving as free-form written content.” | Otherwise virtually every note type qualifies. |
| A2 — Separate formatting | Being prose enables content operations; formatting and numbering are separate opt-ins for new notes. Preserve existing article behavior during migration. | A rename should not impose heading rewrites on new content. |
| A3 — Infer locally | Determine extraction eligibility for an authored section at the invoked location. Store no section-level `type:` or global registry of all prose sections. | The heading subtree already gives a boundary; inferred metadata would drift. |
| A4 — Require the inverse early | Ship extraction with safe re-inlining for the supported domain, plus separate operation undo. | Otherwise essential provenance may be absent when reversal is added. |
| A5 — Specify preservation | Preserve authored content, supported link targets, task identity, and ownership; list intentional representation changes. Refuse unsupported cases without writes. | “Minimal loss” otherwise permits subjective, silent omissions. |
| A6 — Permit companions | Reduction may retain prose files linked from the resulting task. Inline only when supported and useful. | Ownership and display location need not coincide. |
| A7 — Stage generality | Begin with heading subtrees in ordinary authored regions; defer arbitrary selections and generated/operational regions. | A small trustworthy domain is useful immediately. |

No new CLI syntax is finalized here. Implementation of commands or flags must first consult the project's CLI rules. Suggested command labels express behavior rather than an approved interface contract.

**An implicit prose section should be an eligible authored region, not a new note object under every heading.** Select the real heading at the cursor, or the nearest containing real heading, through the next heading of the same or shallower original level. Its nested headings belong to the move. Ineligible contexts should explain their refusal, never fall back to converting the surrounding project.

Use the Markdown classifier and source spans, not heading regexes alone. The article classifier already distinguishes fences, math, comments, HTML, quotes, lists, and Setext headings. Reuse that knowledge while separating generic discovery from numbering. A heading inside code, a callout, list continuation, or a managed region must not become an extraction boundary. Names alone are insufficient to determine authorship: inspect managed ownership and the actual subtree.

Initially refuse candidates intersecting a live `#task`, `^prj`/`^ref`, managed catalogs or Highlights, task-status groups, conflict markers, or unclosed structural blocks. Task-looking examples inside fenced code remain content. For real non-`#task` checkboxes, respect context: a task requirement remains a requirement, and notebooks still forbid checkboxes. Do not loosen those contracts accidentally.

Avoid “Annotation Section”: Bob already reserves it for managed Highlights groups. **Extract section to prose note** and **Inline prose note here** are clearer UI labels than “promote” and “demote,” which already carry workflow meanings. Keep distinct command IDs. Reusing the task/project key gesture can be considered after context dispatch is tested; choose an actual key only after checking the installed keymap.

**A concrete extraction contract.** Given this ordinary authored region:

```markdown
## Design rationale

Paragraphs, tables, code, and quotations stay ordinary Markdown.

### Alternatives

The alternatives and their tradeoffs.
```

Create a fresh prose file with required `parent`, a creation time, and the original subtree. Preserve original heading levels and text; normalization and renumbering are not side effects of extraction. A new note may initially begin with H2. That is preferable to silently changing anchors or requiring formatting. The heading supplies a suggested filename, with explicit sanitization, collision handling, and an editable title.

At the source, retain the root heading and replace its body with a plain link:

```markdown
## Design rationale

[[example_design_rationale|Open Design rationale]]
```

This preserves the old structural slot and provides a useful landing for external links that cannot be rewritten. Rewrite known references to moved content to its new target; the retained heading does not preserve every old nested anchor. A bare link replacing the entire H2 subtree can accidentally fall under the preceding H2, which is why I prefer retaining the heading.

Offer an embed when continuous reading matters. Obsidian supports whole-note, heading, and block embeds, but an embed remains a reference and is not an inverse conversion. Test rendering and duplicated headings before making embeds the default. [Obsidian embeds](https://obsidian.md/help/embeds).

The default parent can be the source note when the relationship is allowed and acyclic. Otherwise require a valid destination instead of inventing a task-fragment parent. Vault memory requires a parent on new notes. Do not copy complete source frontmatter: project status, reference source pointers, generated keys, and record schemas do not become prose metadata through extraction.

Record a durable operation identifier, source slot, created path, moved ranges, before/after hashes, added metadata, and relocation map. This is provenance, not a second editable content store. Associate the generated link stub with the operation using a supported anchor/comment convention selected during implementation. Matching an inverse by display title alone is unsafe under duplicates or renames.

**Link repair is the central correctness work.** Obsidian distinguishes file links, heading links, nested heading paths, and block links. Block IDs locate blocks within files; they are not universal identities for whole sections. A block anchor on a heading is not evidence that its block embed includes the heading subtree. [Obsidian internal links](https://obsidian.md/help/links).

| Reference case | Required treatment |
| --- | --- |
| Source-local link to moved heading/block | Qualify it with the new note path. |
| Moved text linking to content left behind | Qualify it with the original path. |
| Moved text linking within the subtree | Preserve its logical target; local syntax may stay local. |
| Another note linking into the subtree | Rewrite file and heading/block target; retain alias and link-versus-embed behavior. |
| Relative attachment or Markdown file link | Resolve at the old location, then serialize for the new one. Do not move binaries by default. |
| Nested/duplicate/numbered headings | Resolve against the old tree; use full ancestry where supported; refuse ambiguity. Never infer number ownership on unmanaged headings. |
| Frontmatter links and external bookmarks | Plan supported structured frontmatter links; report unsupported/unrewritable references. Do not claim universal repair. |
| Footnotes and reference-style definitions | Preserve each document's definition scope, not just selected text. |

A moved paragraph may reference a definition elsewhere, while a definition inside the subtree may serve text staying behind. CommonMark definitions affect the document globally, and the first matching definition takes precedence. Naive copying or merging can silently change destinations. Initially refuse cross-boundary definition dependencies unless explicitly retaining/copying/renaming the needed definitions and recording the transformation for the inverse. Apply similar care to Obsidian footnotes. [CommonMark reference definitions](https://spec.commonmark.org/0.31.2/#link-reference-definitions).

Use source-preserving edits around resolved spans. Re-rendering a whole AST can alter hard breaks, whitespace, tables, or code indentation. Bob's word-invariant check is valuable for formatting, but equality of non-whitespace tokens cannot prove equivalent rendering or link targets.

**Reversal has two meanings.** Operation undo restores exact before-images if all affected files still match the recorded after-images. Re-inlining after edits is a new transformation of the current prose, not a replay of the old payload. It must preserve those edits, adapt references to the current destination, and refuse conflicts.

For an extracted note, replace the recognized heading/link stub with the current subtree and retire the file only after all references are safe. New child notes, unknown metadata with nowhere to go, ambiguous headings, or duplicate destination block IDs should keep it linked or produce a precise refusal. No force-inline default. General inlining therefore has a narrower domain than “all prose notes.”

```text
undo(extract(vault)) = original vault bytes
    when the operation's postimages are unchanged

inline(extract(region)) ≈ original authored structure and references
    for supported regions, with documented metadata/layout differences
```

The second relation is semantic, not a promise to restore arbitrary editing history. Formatting can be a separate action; merely opening or saving the extracted file must not defeat preservation.

**Project reduction can preserve files rather than flatten them.** Suppose project `P` has parent area `A` and prose child `D` with `parent: "[[P]]"`. Today's reversal refuses. Deleting `P` would orphan `D`; folding `D` into a task risks its metadata, standalone references, and Markdown semantics.

For the first extension, keep a **prose companion at P's existing path** when the project has free-form context or prose children:

1. Restore the project-level task and supported resident tasks into `A` under the existing workflow rules.
2. Move task behavior out of `P`: relocate `^prj` identity, dependencies, task fields, and authored logs; rebuild derived projections. Prose must not retain a live project anchor or duplicate task.
3. Retype the remaining `P` as prose, retain written context and compatible metadata, and leave `D.parent = [[P]]` where valid. Link to the companion under the restored task.
4. Record an explicit task-to-companion association so later promotion can reuse the preserved file and children. A generic content link alone is insufficient provenance for choosing an inverse.
5. Rewrite known `P#^prj` links to the restored task. Whole-file links can continue pointing at surviving context; any different intended semantics need an explicit rewrite rule. Relocate other moved task/block references through the same map.

This is proposed behavior, not an existing capability. It deliberately retains a file. If the goal includes removing that file, provide explicit inline/move operations later; that is an additional requirement with additional cost.

Start with **prose-only child trees**. Do not assume this works for subprojects, notebooks, albums, or every type: notebooks constrain parent kinds, and project ancestry affects blocking and defaults. Compare effective root, clock/type defaults, blocking inputs, and child-parent validity before retyping. Materialize supported defaults or refuse silent semantic changes. Child projects need coordinated workflow conversion, not treatment as document attachments.

Simple projects whose content already fits drawers can keep today's direct reversal. Complex prose fits a preserved file better than a new multiline Markdown encoding inside drawers. A bold drawer can hold a companion link. This preserves authored drawer spelling under `decisions:drawers-keep-their-names`.

Do not collapse independent child tasks into requirements merely because the container becomes a task. Requirements derive state from their owner and lack independent lanes and schedules. Current reversal emits nested `#task` rows, while forward promotion makes outer requirements into tasks. Full round trips must preserve each kind's origin and semantics rather than assume those operations are inverses. `decisions:task-reqs-are-met-with-their-task` governs this boundary.

There are also deliberate workflow side effects: promotion consumes live source-task plans and offers successors, while preserving historical references differently. Exact operational-state reversal cannot be promised without changing those policies. Define content/identity preservation separately from scheduling/review equivalence. Governing audited constraints include `decisions:task-deps-are-depends-on-links`, `decisions:projects-block-from-prj-line` with `decisions:subprojects-inherit-project-blocking`, and `decisions:unblocked-tasks-are-offered`.

**Architecture and migration.** Put planning and mutation authority in bob-cli; let Obsidian supply cursor context, buffer coordination, preview, navigation, and receipts. The article plugin already consumes CLI plans; project conversion currently has substantial JavaScript logic. Move toward a shared planner without requiring a rewrite of every plugin first.

The conversion plan should enumerate preconditions, creates, edits, reference rewrites, metadata transformations, refusals, and destination cursor. Apply must revalidate it. A stale buffer is not permission to pick a different section. Save or supply current editor content and coordinate autosave around application: a CLI lock alone cannot prevent an uncoordinated editor from later overwriting a converted file.

Bob-cli `src/native/vault_rewrite/mod.rs` provides a useful base: creates/rewrites, preimage and target-absence checks, vault locking, rollback, verification, and one scoped commit. Its create/rewrite shape does not itself provide general trash/delete handling. This research did not establish crash recovery across interrupted multi-file writes. Add persistent recovery evidence and tested create/remove handling. Multiple atomic file replacements do not constitute an atomic vault transaction; never report success after half a move or half the required repairs.

Roll out reader-first and preserve existing behavior:

- Accept `article` and `prose` as aliases for one logical kind. A transient type list containing both should not look like unrelated mixed roles. Project/reference combinations should retain appropriate refusals.
- Add a distinct formatting policy, conceptually **preserve** versus **managed**, independent of numbering. New prose defaults to preserve; existing articles remain managed. Decide property spelling in the implementation contract. Preserve mode must neither strip numbers nor normalize levels nor format on save.
- During article migration explicitly retain effective formatting/numbering, including implicit numbering-on. Retype without reformatting bodies. New generic notes should not inherit serif styling merely because the old article template used it.
- Update discovery, adoption, capture heading identity, completions, property roles, nightly reporting, plugin labels/styles, templates, and queries. Keep `bob articles` compatibility while adding the prose surface. Avoid global text substitution: external-source ingestion also uses “article.”
- Initially retain plugin ID `bob-articles` and existing command IDs while changing display names. This preserves installed settings and hotkey bindings. Give extraction/inlining their own IDs.
- Preserve ArticlePlan v1 consumers where feasible. Use a separate versioned conversion contract rather than repurposing formatter fields for multi-file moves. Mark actual CLI/JSON breaks with `!`; follow the daily release train and do not manually edit versions/CHANGELOG.
- Migrate markers only after relevant hosts can read them. Dry-run templates/queries, retain rollback, and compare discovery counts. No live migration was performed here.

Deliver in this order: (1) compatible rename and formatting separation; (2) generic section discovery and precise eligibility; (3) extraction, inverse, repair, and recovery; (4) prose-companion support for project reversal; (5) richer child types and arbitrary selections. Earlier stages deliver independent value if project work takes longer.

**Acceptance examples.** Use a compact shared corpus for Rust and client integration rather than tests that merely repeat helper implementations.

| Area | Essential cases and evidence |
| --- | --- |
| Boundaries | Nested/skipped levels, ATX/Setext, literal numbered headings, empty sections, Unicode, CRLF, fake headings in fences. Exact span selected; neighbors unchanged. |
| Markdown semantics | Hard breaks, nested lists, tables, images, math, callouts, code indentation. Authored bytes retained except planned reference/metadata edits. |
| Links | Moved/staying links in every direction, aliases/embeds, relative attachments, nested headings, duplicate-title refusal, block IDs, definition/footnote boundaries. Equivalent targets. |
| Inverses | Exact immediate undo; edited prose uses current content; renamed/missing stub, child notes, unknown metadata, and ID collision produce safe refusal. |
| Concurrency | Dirty buffer, post-preview edits, destination collision, linker drift, failure after each write, process interruption, replay. No false success or loss; deterministic recovery. |
| Migration | Dual recognition, retained legacy formatting, preserved unmanaged literal numbers, working old IDs/settings. |
| Projects | Simple project, prose section, prose child and descendants, task/requirement distinctions, inbound `^prj`, logs, inherited defaults/blocking, unsupported notebook/subproject. Deliberate preserve-or-refuse behavior. |

This approach would need reconsideration if ordinary sections require pervasive annotations, companions cannot be associated reliably with tasks, or most requested conversions alter inherited workflow semantics. Those findings could justify task-owned documents with stable entity identifiers. That broader ownership model should follow concrete failures; it is unnecessary merely to rename articles or extract sections.

**Recommended solution:** adopt **prose** as the user-facing name and `[[prose]]` as the eventual canonical marker, retaining article compatibility during rollout. Define prose by primary content role, permit ordinary Markdown, and make formatting independent. Treat authored heading subtrees as implicitly eligible regions without another stored type. Implement extraction and safe re-inlining as source-preserving, reference-aware transactions. For project-to-task reversal, retain complex prose and prose children in an explicitly associated companion file by default, preserving the old path when possible. This gives the desired freedom to change scale while making preservation—not aggressive flattening—the central requirement.
