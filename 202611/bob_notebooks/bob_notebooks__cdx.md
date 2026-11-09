# Notebooks for durable context: capture compatibility, discovery, and a first vault migration

Researcher: **cdx** · 2026-11-09 · Independent design research

## Recommendation in brief

**Add notebooks.** The vault already contains many notebook-shaped collections; naming the concept would let Bob discover, capture into, and display them without pretending they are projects. The strongest benefit is making existing knowledge usable, not creating another organizational taxonomy.

Make a notebook a **task-free collection of authored note bullets**, with a required, single `parent` and a short, authored `summary`. Keep the file and its block IDs stable. Render one compact, attractive notebook catalog in its existing Bob root parent, with ancestry shown for nested collections. Notebooks have no `^prj`, task status, freshness, Pomodoro membership, or separate lifecycle.

The main engineering risk is capture compatibility. **`@@foo` already means a draft-wide task destination; `%n` already means a Pomodoro note.** The requested grammar cannot safely be implemented as a few aliases or by reusing the project writer with a different template. I recommend a shared, typed destination-resolution phase: existing non-notebook `@@` behavior stays intact; a known notebook claims `@@notebook` as an item-local note destination, and the sealed creation marker plus `%n` creates a notebook. This introduces a deliberate dependency on note type, so all parsing, completion, rewrite, preview, and commit paths must share the same resolved intent.

Start with four existing files that need little restructuring, plus one genuinely parentless historical SASE note. Add the broader idea collections after triage. Do not begin by bulk-converting every parentless file.

This is a research report, not an implementation or live-vault migration. No vault contents or product code were changed. No other swarm researcher's report, findings, or transcript was consulted.

## 1. Evidence and scope

### Sources inspected

| Source | Revision / method | What it establishes |
|---|---|---|
| bob-cli | `4c09fac4479f855d04c7a381ff4505c25557bc35` | Capture contracts, parsing, alias rewrites, destination enumeration, block IDs, transaction machinery, root resolution |
| bob-plugins | `a2045cc9c1c4f4206b425df6985fca91a81928cb` | Parent-change machinery, project-specific writers, existing reading/editor rendering hooks |
| bob-mac-capture | `b81302b2610d31bbc9caa4c9c245097b16b0b884` | Block-ID picker, mode-specific presentations, grammar compatibility gate |
| Live Bob vault | Read-only native `bob query`, 2026-11-09 | Types, parents, links, bullet contents, block IDs, sections, candidate sizes |
| Installed `bob` | `bob 0.5.0`; isolated synthetic-vault dry runs | Current observable behavior of the proposed spellings |
| SASE memory | Audited reads | Existing Area Note, Project Note, Root Parent and Capture definitions; grammar/client decisions; documentation and release rules |

The metadata inventory returned **6,714 notes**, including **3,891 without a recognized `type` value**, 18 areas and 99 projects. This is the native query engine's indexed scope, not a count of every file or attachment on disk. There were **20 parentless files at the vault root**, many empty, system-oriented, or otherwise poor notebook candidates. Conversely, **174 root-level, untyped files have at least ten list items and no indexed checkbox tasks**. That latter group is the more useful search space.

Counts of list items include descendants, not just independent top-level notes. A zero checkbox-task count does not mean a collection contains no commitments: old `tick::`, `recur::`, `@READ`, and imperative prose occur in the idea collections. Native query also reported ambiguous link targets, including `foo`, `dad`, and several research-like stems. Candidate decisions use exact file paths; backlink counts are discovery signals, not proof of complete link resolution.

I inspected parsed bullets, frontmatter, block IDs and heading memberships for selected notes. I did not audit every raw paragraph, code fence, attachment or inbound Markdown link in every candidate. A migration must perform that final byte-level audit before applying the proposed transforms.

### High-value code anchors

Paths below are relative to the named repository; revisions above pin the observations.

| Repository and path | Relevant seam |
|---|---|
| bob-cli `docs/capture.md:481` | `@@route` is global metadata, anywhere in a draft; duplicate globals fail; local routes override it |
| bob-cli `src/native/capture_language/draft.rs:2516` | Global parser explicitly rejects `+`, `#`, `^`, and `:` suffixes |
| bob-cli `src/native/capture_language/model.rs` | Parse options already carry immutable route policy for configured record destinations; a precedent for notebook route policy |
| bob-cli `src/native/capture_language/mod.rs:51` | Inspected source declares capture grammar revision **22** |
| bob-cli `src/native/capture_language/tests/rewrite.rs:714`, `:1494` | Cursor-sensitive aliases; current negative cases explicitly include `@@r.` and `@@cash/` |
| bob-cli `src/native/capture/plan.rs`, `capture/sub_bullet.rs` | Existing `+id` writer resolves a **task**, rejects a non-task block, and participates in task effects |
| bob-cli `src/native/capture_project_note.rs`, `capture/project_note.rs` | Project creation supplies `^prj`, task rows, schedules, offers, links and blocking; notebook creation needs a separate planner |
| bob-cli `src/native/capture_targets.rs:231`, `parent_notes.rs` | Target kinds are Inbox, Area, Project, Record; the shared parent resolver serves more than capture |
| bob-cli `src/native/capture_sections.rs`, `capture/sections.rs` | Current heading catalog supports H1–H6; legacy section matching can fall back to the pre-heading region |
| bob-cli `src/native/capture_block_ids.rs` | Bob supplies allowed characters, used IDs, suggestions, intent and splice ranges |
| bob-cli `src/native/pomodoro_homes/resolve.rs:470` | Existing root-parent walk traverses other note types, selects nearest area/project, and respects project `root: true` |
| bob-cli `src/native/capture/commit.rs` | Staging, preimage guards, exclusive creation and rollback; explicitly **not** fully serialized cross-process transactions |
| bob-plugins `plugins/bob-navigation-hotkeys/src/208-parent-note-picker-model.js`, `211-parent-frontmatter-plan.js`, `682-plugin-parent-change.js` | Parent selection, cycle handling, and surgical YAML-span edits |
| bob-plugins `plugins/bob-ledger-tools/src/170-plugin-lifecycle.js:413` | Existing code-block and Markdown rendering integration points |
| bob-mac-capture `Sources/CaptureCore/BlockIDRules.swift`, `CapturePickerPresentation.swift`, `CaptureModels.swift` | Existing block-ID field, suggestions, intent-dependent labels and typed JSON decoding |
| bob-mac-capture `Sources/CaptureCore/CaptureGrammarGate.swift` | Compatibility is a minimum grammar revision check, not proof every later feature is understood |

A caution for implementers: the top comment in `capture_project_note.rs` still describes the retired `+` seal, while the current documentation and parser use `@`. Follow current executable behavior and tests rather than copying the stale example.

### Isolated behavioral probes

I created a disposable synthetic vault with an area `dev.md` and a `book.md` containing `type: "[[notebook]]"`, a normal bullet `^anchor`, and `## Bar`. Every invocation was `bob capture --dry-run --no-clip --no-ref --format json --bob-dir …`.

| Draft | Observed behavior |
|---|---|
| `A note @@book` | Success, **kind `task`**, planned `- [ ] #task A note …`; global destination `book` |
| `A note @@book#bar` | Rejected: `@@` takes only a route |
| `A child @@book+anchor` | Same global-declaration rejection |
| `A named note @@book^some-id` | Same global-declaration rejection |
| `A collection @dev^book@ %n` | Rejected: `%n` cannot be combined with an `@route` marker |
| `A child @book+anchor` | Rejected: `^anchor … is not a task` |
| `A note @book#does-not-exist` | Success, ordinary bullet inserted in the **pre-heading region**, despite the missing section |

These probes are enough to rule out a template-only implementation. They also show why installing a new `type` value before upgrading all capture writers is unsafe: an older Bob happily proposes checkbox tasks in it.

## 2. Critique: a useful concept if it stays small

Area and project notes answer ownership and action questions. A notebook answers **“Where do I keep what I know about this subject?”** A set of shell tips, design alternatives, interview observations, or writing fragments should not need a project completion criterion or an artificial area of responsibility.

The concept earns a distinct type because it changes allowed capture behavior, validation, and discovery. A tag would identify a collection but would not establish those boundaries. A generic record type is also a poor fit: records are field-oriented entities, whereas notebooks are growing outlines with individually addressable bullets.

The risks are organizational inflation, hiding real tasks inside notes, deep nesting, and another stale overview to maintain. Mitigate those with a narrow contract:

- Create a notebook when the collection deserves a name and is useful to open independently. Leave a small coherent H2 section where it is.
- Prefer one or two notebook levels, but do not impose an arbitrary shallow hard limit. Bound traversal for safety and diagnose cycles.
- Keep one structural parent. Use ordinary links for cross-cutting relationships rather than multiple parents.
- Preserve source documents and reference bundles as references. A notebook may contain observations about several references without replacing their source-of-truth files.
- Never automatically turn imperative prose into tasks, or silently convert an existing task into a bullet.
- A catalog should be derived from notebook metadata. Do not maintain a second hand-authored list of notebook identities.

I would **not** make recursive notebooks into a general-purpose outliner, add AI-generated summaries on every edit, create notebook statuses, or impose a mandatory organization wizard. Those additions would erase the feature's advantage over projects.

## 3. Proposed notebook contract

### Canonical file shape

```yaml
---
type: "[[notebook]]"
parent: "[[dev]]"
title: Shell notes
summary: Commands, failure modes, and small lessons from daily shell work.
created: 2026-11-09T10:00:00+0000
---
```

```markdown
- Open a long command in the editor with Ctrl+X, Ctrl+E. ^edit-command
  - Useful before changing a command copied from documentation.

## Troubleshooting

- Check which process owns a port before restarting services. ^port-owner
```

Write the quoted wikilink form used by Bob's area/project notes. Normalize supported legacy type spellings through the common frontmatter classifier rather than scattering string comparisons. Obsidian supports quoted internal links in text properties; a plain one-line `summary` fits its property model. [Obsidian Properties](https://obsidian.md/help/properties)

Required fields are `type`, exactly one `parent`, and a nonblank `summary`. `title` is a display label, optional on manually authored/migrated files and populated by creation; the filename remains the identity. `created` follows the existing creation convention. Do not store `root_parent`, descendant counts, last-rendered timestamps, project status, or task counts.

Include the vault's type-definition page for `[[notebook]]` and a reusable manual-creation template in the implementation. The type-definition page is a system/taxonomy note under the existing type index, not a notebook instance with a self-referential type. Keep the template and CLI renderer on the same canonical field contract.

The summary describes **scope**, not every current detail: “Operational commands and setup notes for Linux machines” survives additions better than “Seven Linux tips.” Recommend one sentence, roughly 60–180 characters; do not reject a useful note merely for exceeding a presentation guideline. Missing summaries should be visible diagnostics, with a temporary display fallback, rather than making a hand-edited notebook disappear. Controlled creation and the migration must supply them.

### Content and lifecycle

- Author ordinary Markdown bullets and optional H2 sections. Nested bullets and Markdown continuations—links, code, images, quotations, tables—can belong to a note. “Only note bullets” should not mean “text can never span more than one line.”
- Do not generate `## Tasks`, `^prj`, checkboxes or `#task` metadata. Normal bullet creation can retain the established `[created::…]` convention.
- Reads preserve legacy content even if it violates the ideal shape; validation reports it. Writers must not flatten, erase, or reinterpret it automatically.
- Prevent Bob-managed task capture, project promotion, task moves, dependencies, and Pomodoro links from targeting a notebook. Audit every writer, not only the new `@@` handler.
- Hand-authored checkbox tasks are a validation error. Keep them visible for repair; do not silently delete them or globally hide them from existing task scans.
- Closing or blocking an ancestor project does not close, block, hide or prohibit notes in a notebook. Knowledge often remains useful after work ends. New notebooks can also be created under a closed project; this intentionally differs from project-child creation.

### Parent graph

The immediate parent must resolve uniquely to an existing area, project or notebook, and the notebook chain must reach an area/project. Refuse missing parents, ambiguous links, lists of parents, self-parenting and cycles. Do not allow a notebook as the structural parent of a new area/project in this release; that would change the work hierarchy rather than just organize notes.

Accept a notebook parent staged earlier in the same capture batch. Resolve against the batch snapshot, not only disk. A creation filename follows the familiar `<parent-route>_<slug>.md` rule; after creation, **reparenting does not rename it**. Existing migrations keep their filenames where possible. Filename prefixes are a convenience, never a second parent graph.

No new synthetic “notebook root” is necessary. Reuse Bob's root-parent calculation, treating notebook nodes as transparent. An area is its own root; a project marked `root: true` is a boundary; otherwise the existing outer-project rule applies. The current resolver already walks through `Other` nodes, so add validation and tests around that behavior rather than replacing it.

### Proposed glossary entry

> **Notebook**
>
> A Bob vault Markdown note with `type: "[[notebook]]"` that keeps a named collection of related observations, explanations, ideas, or working notes. Its content is ordinary note bullets, optionally grouped under H2 sections; bullets may have children and stable block IDs. A notebook has one `parent`, pointing to an Area Note, Project Note, or another Notebook, and a short `summary` explaining what belongs there. Its parent chain must reach an area or project.
>
> A notebook carries context without acquiring a project's completion task or an area's responsibility: it has no `^prj`, task lane, review schedule, or Pomodoro membership. Tasks stay in area/project notes and can link to notebook material. Closing a parent project leaves its notebooks readable and editable.
>
> Capture creates a notebook with `@parent^name@ %n`; `@@name` adds a note, `@@name#section` files it under an H2, `@@name+id` adds a child to a note bullet, and `@@name^id` names a new bullet. Bob derives its Root Parent and lists it there with its summary and ancestry. Reparenting changes that placement without changing the notebook's identity.

This entry belongs in `sase/memory/glossary/notebook.md` when implemented, linked to the existing Area Note, Project Note, Root Parent and Capture strands. The user explicitly requested this glossary addition. An eventual SASE implementation plan should carry the required per-note memory decision with the exact request: “We should add an excellent new \"notebook\" glossary term to describe this concept.” Existing capture/glossary definitions will also need narrowly scoped updates for changed behavior; accepted decision records require proper supersession, not silent rewrites. This report does not publish new durable memory.

## 4. Capture design and compatibility

### Three possible approaches

| Approach | Benefit | Cost | Judgment |
|---|---|---|---|
| Reassign all `@@` to local note capture | One simple syntax independent of type | Breaks existing inline and standalone global task routes, templates and habits; requires a replacement global spelling | Too disruptive for this feature |
| Add a different notebook sigil | Existing grammar stays simpler | Rejects the user's requested shorthand and adds another symbol to remember | Reasonable fallback if type-dependent parsing proves too costly |
| Let known notebooks claim local `@@`; preserve legacy globals elsewhere | Supports requested syntax and retains current valid area/project global drafts | Parsing must know the destination kind; converted files intentionally change meaning | **Recommended**, with shared route policy and explicit preview |

Do not distinguish these operations by whether `@@` appears at line start or after prose. Existing globals are legal anywhere, including authored child lines. A position-only rule would break valid drafts while appearing backward-compatible.

### Exact proposed semantics

For this table, `foo.md` exists and is a notebook; `dev.md` is an area.

| Draft | Meaning |
|---|---|
| `Shell commands and lessons @dev^shell@ %n` | Create `dev_shell.md`, parent `dev`, title derived from `shell`, summary from the item text |
| `Useful observation @@foo` | Add a top-level note to `foo.md` |
| `Useful observation @@foo#bar` | Add it to the H2 whose exact normalized title/slug is `bar` |
| `Useful observation @@foo#"API Design"` | Exact named H2; quoting preserves intended spelling |
| `A detail @@foo+baz` | Add a child to the existing ordinary note bullet `^baz` |
| `Useful observation @@foo^some-id` | Add a top-level note with block ID `some-id` |
| `Useful observation @@foo#bar^some-id` | Add a named note to that H2; a useful compositional extension |
| `@@foo` followed by authored bullet lines | A notebook list: each first-level bullet becomes a separate note |
| Bare `@@foo`, no body or children | Incomplete; do not create an empty bullet or reinterpret it as global task metadata |
| `Do work @@dev` | Existing global task destination behavior remains |
| `Remember the timeout %n` | Existing Pomodoro-note behavior remains |
| `Outcome @dev^ship@` | Existing project-note creation remains |

Notebook `@@` markers are **item-local**, so a draft can independently write one note to `@@foo`, another to `@@bar`, and an ordinary task to `@dev`. An existing `@@dev` global affects only otherwise-unrouted task items, not explicit notebook items.

An unresolved `@@name` should produce a useful destination error and suggestions rather than create a new task file. This is a **deliberate compatibility tightening**: existing ordinary routed task capture can create missing files today. Existing non-notebook destinations retain their global behavior, including legacy existing notes; notebook suffixes on such destinations fail with a notebook-specific explanation. Preview must say **“Shared task destination”** or **“Note → Notebook / Section”**, not just show the same route chip for both.

### Notebook creation

A sealed `@parent^slug@` plus item-edge `%n` selects **NotebookCreate** before the ordinary `%n` conflict check. The main item text becomes the required scope summary, so creation needs no mandatory second dialog. Children seed the notes:

```text
Commands and lessons for everyday shell work @dev^shell@ %n
- Open a long command in an editor before changing it.
- TROUBLESHOOTING
  - Check the process owning a port before restarting services.
```

Reuse the existing ALL-CAPS-with-children section convention to produce `## Troubleshooting`; remaining children are note bullets, never tasks. The creation preview must explicitly show filename, parent, title, summary and outline. Allow a user to refine the title without inventing another compulsory syntax token.

The `^slug` in a sealed creation marker names a **file**, not a parent bullet and not a notebook `^prj`. Reuse slug validation and filename collision checks, but give its picker a notebook-name intent and label.

Do not accept the project offer form `@parent:slug@ %n`, Pomodoro suffixes after the seal, task scheduling/priority, or task move bullets for notebook creation. They have no clear notebook meaning. Refuse those combinations with specific explanations. Ordinary `%n` still owns Pomodoro notes; combining it with an existing notebook note route should be refused as redundant/conflicting rather than silently moving the note to today's ledger.

### Insertion must be predictable

**Top-level:** insert after the last full top-level note block in the pre-H2 region, before the first H2. If there are no such notes, insert after frontmatter and any permitted title/preamble. Never append a nominally top-level note below the last H2: Markdown would put it in that section.

**Section:** only H2s participate in notebook section completion. Match normalized title or whole slug exactly; completion can offer fuzzy suggestions, but the committed selector must be exact. `#bar` reaches `## Bar`; it must not silently reach `## Barriers`. Duplicate normalized matches are an error. If absent, show an explicit **Create “Bar” section** choice; the canonical completed selector then creates that section at EOF, with creation stated in preview. A fully typed missing selector may also create its literal section, consistently with that preview. Never reuse the current unmatched-section-to-preamble fallback.

**Child:** find exactly one ordinary list-item block with that ID, including nested bullets, and insert after its full existing child subtree using the file's indentation. Reject missing, duplicated, task, heading, fenced-code and non-list targets. No task status or ledger reads/writes occur. Generalize structural block location, not the task-effect pipeline.

**IDs:** validate against all real block IDs in the destination, including other bullet depths and staged additions. Scope uniqueness to a file, not the whole vault. Preserve the existing letters/digits/dashes rule. Obsidian supports IDs directly on individual list items and uses `[[file#^id]]` links. [Obsidian Internal links](https://obsidian.md/help/links)

### Block-ID prompt and aliases

Use the existing Bob-owned `block_id` completion payload. A bare trailing `@@foo^` opens a prompt with a suggested slug derived from the current note text, selected for easy replacement. Distinguish **New note ID**, **Existing note parent**, and **New notebook name**. An already complete explicit ID requires no extra modal. Suggestions are provisional: the commit rechecks collisions.

The current aliases are cursor-aware editor rewrites, not a blanket shell-text substitution. Extend that same machinery and keep canonical syntax as the CLI contract. Required cases include:

| Typed editor sequence/context | Canonical result |
|---|---|
| `.` at the established route-entry position | `@` |
| A second `.` while completing that prefix | `@@` and notebook completion |
| `@@foo.` | `@@foo^` and new-note-ID prompt |
| `@@foo/` | `@@foo#` and H2 completion |
| `@@foo,` in the parent-note picker position | `@@foo+` and ordinary-note parent completion |
| `@dev.` while creating a notebook | Existing `@dev^`; trailing seal and `%n` select notebook creation |

Audit the complete alias table, including `;`, backslash-to-`#`, literal escaping and alias idempotence; unsupported task-only aliases should refuse or remain literal according to a documented rule, never produce a task in a notebook. Preserve dots in prose/URLs, filesystem slashes, fenced/inline code, and slash task-open pickers. Test keystroke sequences, pasted canonical text, undo, selection replacement, Unicode offsets and mixed drafts. Tests currently asserting that `@@r.` and `@@cash/` remain literal will need precise notebook-aware counterparts, not broad deletion.

### Implementation shape

Add an immutable **NotebookRoutePolicy** (or general note destination catalog) to both strict/editor parse options, like the existing record policy. Classify notebook tokens **before** `take_global_declarations` strips all `@@` tokens. The model should represent NotebookCreate, NotebookNote and NotebookChild explicitly, or equally explicit typed destination plus operation variants.

The same semantic resolver must drive `capture-parse`, `capture-complete`, `capture-rewrite`, dry run and commit. A staged notebook created by an earlier item must be visible to later items. Guard the metadata read set, including ancestors: a note retyped or reparented after preview must not change the eventual write meaning unnoticed.

Do not simply add Notebook to the shared `capture-targets` enumeration and every current parent resolver. That resolver also feeds reference intake and other commands. Express capabilities—accepts tasks, accepts notes, accepts child notebooks—and filter each caller intentionally. Single-`@` task mode should refuse notebook targets and suggest the double-`@` spelling.

## 5. A root-parent notebook catalog that is useful and attractive

### Which root gets which notebook?

Define one owner function: `owner(N) = existing_root_parent(N.parent chain)`. A root displays every notebook whose owner is itself, including notebooks below non-root projects or other notebooks. Dedupe by canonical file path. Stop ownership at a different area/root project boundary.

Real vault example: `sase_blog.md` has **`root: true`** and parent `sase`. Therefore a notebook parented to `sase_blog` belongs in the **SASE Blog** catalog, not automatically in both `sase` and `dev`. A notebook under a non-root child of `sase` belongs in `sase`'s catalog. Show the breadcrumb so the filing location is still clear.

Offer lightweight child navigation inside a notebook as well, but the root catalog is the complete discovery surface. A nested notebook should never be reachable only through repeated drill-down.

### Visual treatment

Use an understated **Notebooks** heading with one notebook icon and an optional count. Each row has a strong linked title, a quiet one-sentence summary, and a smaller breadcrumb only when needed. Inherit the owning root's existing color as a restrained accent; do not invent a color taxonomy. Avoid large thumbnails, task chips, progress bars and timestamps.

Illustrative layout, not observed vault state:

```text
▤  Notebooks                                            4

Developer tools
Command-line tools, configuration techniques, and usage notes.

Linux operations
Machine setup, troubleshooting, and operational shortcuts.

Networking notes
Protocols, social networks, and practical networking tips.

Python experiments
Small language experiments and findings worth keeping.
Languages › Python
```

Use one column in normal note panes; a spacious pane may use two columns with the same reading order. Aim for roughly 12–16px row padding, a quiet divider or subtle surface, readable secondary text, and visible keyboard focus. Two summary lines may be shown compactly, but expanding/focusing must reveal the full text. Test both light/dark themes, mobile widths, zoom, Reading view and Live Preview. Let the ordinary link remain a real Obsidian link with keyboard navigation and native hover preview.

Place the catalog near the top, after the note's title/project overview and before `## Tasks`, outside the `^prj` child block. For a root with many notebooks, collapse the catalog behind its count and offer filtering in the enhanced view; do not permanently hide all but the first few. Preserve the disclosure preference locally, not as synced content. Sorting by title then canonical path is stable; avoid mtime sorting that reshuffles with automated edits.

### Rendering and ownership

Prefer **generated ordinary Markdown with progressive plugin styling**:

```markdown
<!-- bob:notebooks:start -->
## Notebooks

- [[dev_tools|Developer tools]] — Command-line tools and configuration notes.
- [[networking|Networking notes]] — Protocols and practical networking tips.
<!-- bob:notebooks:end -->
```

This survives disabled plugins, mobile, source mode, plain search, and export. A small Obsidian renderer can decorate the managed region as rows/cards without owning its membership logic. Raw summaries should be emitted safely as text, never executed as HTML or interpolated into DataviewJS.

Bob owns the projection. Recompute membership after notebook creation, summary/title/parent changes, deletion/rename, or ancestor `parent`/`root` changes. Ordinary bullet edits do **not** change catalog bytes. Empty roots lose only the managed region. A manual `## Notebooks` heading outside the markers is not permission to overwrite its text; diagnose/offer a placement choice. Malformed or manually modified managed regions require an explicit repair preview.

A proposed `bob notebooks` group could own list, check and sync operations over notebook files/catalogs; bare invocation would be read-only. Exact public command naming should follow the CLI rules. Do not nest this under `bob capture`, whose arguments are free text.

An Obsidian refresh hook can request a debounced Bob refresh after relevant changes, while a CLI sync repairs changes made elsewhere. Avoid one full-vault scan per visible root and on every keystroke: scan once, build canonical parent/reverse-child indexes, cache derived membership, and invalidate only affected roots. Two roots are affected by a cross-root reparent.

A purely virtual renderer would avoid projection writes but lose useful native Markdown links and make discoverability depend entirely on one plugin. A Dataview prototype is fine for trying row density; it should not become a second independent definition of root ownership.

## 6. Vault migration: what is actually worth moving

### First cohort

“Bullets” below means indexed list items including children. Parent values shown are normalized for readability; several current files use legacy unquoted YAML links. All four existing files below had zero indexed checkbox tasks and no capture-eligible headings, so they are useful simple pilots. Preserve their existing line structure and IDs; check non-bullet continuations before finalizing.

| Existing file | Evidence | Proposed notebook / parent | Suggested summary |
|---|---|---|---|
| `dev_tools.md` | 49 bullets, 116 inlinks; practical chezmoi, tmux, Pandoc, shell-history and CLI-tool notes; parent `dev` | Convert in place; parent `[[dev]]`; title **Developer tools** | Command-line tools, configuration techniques, and usage notes collected during development. |
| `linux.md` | 34 bullets, 74 inlinks; setup instructions and troubleshooting; parent `dev` | Convert in place; parent `[[dev]]`; title **Linux operations** | Machine setup, troubleshooting, and operational shortcuts for Linux environments. |
| `networking.md` | 18 bullets, 22 inlinks; protocol definitions, social networks and port diagnostics; parent `dev` | Convert in place; parent `[[dev]]`; title **Networking notes** | Protocols, social networks, and practical networking tips. |
| `sase_blog_0_legacy_notes.md` | 18 bullets, **0 inlinks**; writing fragments, architecture comparisons and future-topic ideas; valid parent `sase_blog` | Convert in place; parent `[[sase_blog]]`; title **SASE writing fragments** | Early arguments, examples, and topic ideas for the SASE blog. |

These files demonstrate the core problem: useful material can have a parent yet remain poorly exposed to the active Bob system. The writing fragments are particularly strong evidence: a valid parent alone has not supplied an inbound navigation link.

**Also migrate one real orphan in the first feature release:** `text/sase_notify.md` (4,505 bytes, 14 indexed bullets, 5 inlinks, no parent/type). Its content discusses notification triggers and actions—HITL choices, workspace errors and navigation—and its migration metadata identifies an older Zorg source. Convert it to **`sase_notification_history.md`**, parent `[[sase]]`, summary **“Historical notification requirements, trigger cases, and interaction ideas for SASE.”** Keep the entire document, including non-bullet prose, code and old terminology; organize it into bullets/H2s through an explicit preview, and rewrite inbound links. It is historical design context, not a claim about today's implementation. This candidate needs a raw-content audit before the transform is finalized; the research inspected its metadata and parsed bullet content, not every prose span.

A source-path change is justified here because capture's route model targets vault-root filenames. Check the proposed stem for collisions at execution time. Preserve `zorg_source`, source hashes and other provenance instead of replacing them with the new creation date.

### Second cohort: high value, needs semantic triage

| File(s) | Evidence and proposed treatment |
|---|---|
| `dev_ideas.md` | 235 bullets, 16 inlinks, parent `dev`. Strong notebook candidate, but `tick::` dates and “Start/Write/Install…” entries show a legacy action queue. Preserve IDs, separate current commitments from speculative ideas, then convert in place with an explicit “historical/uncommitted ideas” scope. |
| `gtd_ideas.md` | 150 bullets, 19 inlinks, parent `gtd`. Contains older workflow experiments, accepted entries and ticklers. Convert after triage; do not revive all old reminders or silently discard them. |
| `sase_ideas.md` | 173 bullets, 16 inlinks, parent **`work_ideas`**, itself under untyped `work`. Reparent directly to `[[sase]]`; preserve IDs and accepted/rejected/history notes. Stronger discoverability improvement than keeping the old chain. |
| `lang.md`, `python.md`, `rust.md` | `lang` is an 8-item language index under legacy `ks`; Python has 28 bullets/50 inlinks, Rust 39/31. A good **nested notebook pilot**: make `lang` a notebook under `dev`, and Python/Rust child notebooks under `lang`. Do not automatically convert every linked language file merely because it is mentioned. |
| `plans/sase_xprompt_jinja.md` | 4,474 bytes, 27 bullets, no parent, 0 inlinks. Historical Jinja/xprompt design with migration provenance. Candidate for a separate SASE design-history notebook; preserve the full source and label its age. |
| `chat/sase_fix_tests_prompt.md` | 6,679 bytes, 33 bullets, no parent, 0 inlinks. Historical test-repair workflow design with planning/editor/research “blackboard” concepts. Useful SASE history, but full transcript/prose preservation matters. |
| `word_of_day.md` | 28 bullets, 2 inlinks, parent `love`. A simple nontechnical notebook example; keep under `love` initially rather than inventing a new area. |
| `dev.md` → `## Legacy Notes` | 20 indexed bullets in that section; a useful future extraction exercise. Many are links to collections, so converting the destination collections first may reduce the need to extract the whole section. |

`gtd.md` has 31 bullets assigned to `Legacy Notes` and six in `HABITS TO TRACK`, but also legacy recurrence/tickler data. `sase.md`'s visible `Future Work` has only six indexed bullets, mostly imperative feature ideas; it is not a compelling first “large section” extraction. Do not choose a section merely because its heading sounds notebook-like.

### Exclusions and caution cases

- Most parentless entries are daily/generated/source material. `_generated/tag_pages/…`, `_meta/…`, templates, instructions, and empty `Untitled*.md` files are not migration targets.
- `agent_ref.md` is large (482 bullets) but starts with reference IDs, file pointers and reading state. `xprompt_ref.md` similarly catalogs sources. Size plus zero checkboxes is insufficient reason to turn either into a notebook. Audit source/reference ownership first.
- `lib/notes/sase_blog_261017.md` and `…261019.md` are parentless in query metadata but appear to contain source-document material. Do not bulk-move `lib/` inputs or bypass reference source preservation rules.
- `old_arms_2.md` is a genuine orphan (3,116 bytes, eight bullets, two inlinks), but historical work context and ownership are unclear; it is weaker than the SASE orphan candidates.
- `chad_movie.md` is a small orphan with a movie-related prompt. It is not a first-class notebook merely because it has no parent.
- `work.md`, `own.md`, `home.md`, and `h2_role.md` are legacy hierarchy nodes, not current areas. Do not propose them as valid notebook parents without first resolving their type/ownership deliberately.
- `text/habit_slide_show.md` is referenced as a Pandoc input from `dev_tools.md`; “helpfully” restructuring it could break that source workflow. Link to it from a notebook if useful, keep its source purpose.

### Migration invariants

1. Produce a manifest with original path, content digest, destination path, parent, title, summary, body transform, preserved IDs and all rewritten links. Review the concrete diff before applying.
2. For in-place conversion, edit only necessary frontmatter spans and justified formatting. Preserve provenance, line endings, authored ordering and IDs. Do not reserialize the whole frontmatter without need.
3. Before moves, enumerate wikilinks, embeds, relative Markdown links, property links and attachment paths. Use exact resolved identities, not a regex substitution on a basename. Aliases assist discovery but are not a substitute for rewriting actual destinations; Obsidian itself creates alias links with canonical destinations. [Obsidian Aliases](https://obsidian.md/help/aliases)
4. Compare hashes at apply time; refuse stale sources and newly occupied destinations. Apply source moves, backlink rewrites and affected root catalogs through one guarded operation with rollback. Preserve a recoverable before-state.
5. Verify that no original block ID disappeared or became duplicated, task counts/statuses and ledger bytes are unchanged, parent graphs are valid, and every migrated notebook appears in exactly its owner catalog.
6. Make the migration repeatable: already converted files are recognized, not duplicated. Run it first against a disposable snapshot. Use the established vault sync/maintenance coordination in production; the current capture writer's preimage checks alone are not distributed locking.

## 7. Section extraction should shape the design now, but ship later

An “Extract H2 to notebook” command is a natural sequel. It should show the source heading, new filename, title, required summary, parent and complete preview. Move the heading's full subtree, excluding the next same/higher heading, while preserving bullet IDs and nested Markdown. Set the notebook parent to the source area/project/notebook.

Rewrite `[[source#^id]]` to `[[new#^id]]`, including embeds, and rewrite section links to the destination. Local links inside the moved content also need rebasing: `[[#^id]]` might refer either to another moved block or to a block left behind. Relative Markdown attachment paths need the same care. Retain an intentional link under the original H2 when that preserves a useful old section entry point; do not duplicate the moved text.

Refuse extraction of tasks, `^prj`, generated status sections, managed catalogs and malformed/ambiguous headings. Whole-source read guards and a backlink audit are essential. This is more than cut-and-paste, so it should follow the small initial migration rather than delay the core notebook feature.

## 8. Delivery boundaries, failure cases and verification

### Work boundaries

1. **Domain and reader support:** canonical notebook metadata, validation, graph/root ownership and catalog model. Add explicit capabilities to destination catalogs without broadening reference/task parents accidentally.
2. **CLI grammar and writes:** notebook create/note/child operations, strict H2 targeting, ID completion, staged creation/use, alias parity and typed diagnostics. Reuse the common guarded batch writer and keep notebook-specific planning separate from task effects.
3. **Client and rendering:** Mac decoding, prompts, notebook-specific previews and completion; Obsidian catalog styling, parent-change validation and task-writer guards. Update source plugins and deploy with `bob plugins sync` when implemented.
4. **Documentation and glossary:** capture contract, syntax index, notebook contract, short guide, generated CLI help as needed, and the requested glossary strand. Follow the audited memory workflow and docs gates.
5. **Rollout and migration:** deploy compatible consumers/writers first, validate with a fixture vault, then migrate the small first cohort and inspect actual catalogs. Expand only after real usage.

Do not bump Cargo.toml or CHANGELOG.md by hand; the release train owns them. Capture meaning changes need the next grammar revision and appropriate breaking-change commit marking. The current minimum-only Mac grammar gate is insufficient evidence that an old client can present notebook modes. Add explicit feature negotiation/unsupported-mode refusal, test both upgrade directions, and coordinate installation before any note changes type. An old installed Bob cannot be retroactively taught that `@@notebook` is dangerous; rollout discipline is part of the solution.

There is a concrete unsafe fallback to address: `CaptureBlockIDIntent.init(wireValue:)` currently maps an unknown intent to **`.link`** (`CaptureModels.swift:10881`). Merely returning a new `notebook_note` intent from Bob would make that client present it as an existing-task link operation. Update this decoder and its presentation consumers explicitly; test unknown future intents as unsupported rather than letting them silently become task operations.

For Swift changes, portable checks alone do not verify AppKit/SwiftUI targets. Follow the Mac repository's compile/typecheck requirements and watch exact-SHA macOS CI to green after pushes. This research made no Swift changes and claims no such CI validation.

### Minimum acceptance matrix

| Area | Important assertions |
|---|---|
| Existing behavior | Area/project global `@@` at every currently supported position, local overrides, duplicate-global errors, ordinary `%n`, project create/offer and record syntax remain correct |
| Notebook creation | Correct type/parent/title/summary; no `^prj` or task rows; duplicate filenames and invalid parents refuse; child notebook creation works; no daily-note dependency |
| Mixed drafts | Several notebook destinations plus legacy global task routing; URL inside an explicit notebook stays a note rather than becoming a ref job; create-then-capture resolves staged files |
| Placement | Preamble with/without H2s, empty/existing sections, slug/exact matching, explicit new section, ambiguous headings, EOF, blank lines, CRLF, fenced pseudo-headings |
| Child notes | Parent at multiple depths, multiline content, sibling boundaries, indentation, missing/duplicate/non-list/task IDs; no incidental task/ledger writes |
| IDs and aliases | All IDs counted including staged notes; suggestions and exact collisions; cursor rewrite idempotence; literal syntax escapes; Unicode/UTF-16 client splice correctness |
| Hierarchy | Areas, non-root projects, `root: true`, nested notebooks, completed projects, bad parents, cycles, rename/delete/reparent and ancestor-root changes |
| Catalog | Exactly-once membership, stable order, no empty section, ordinary body edits yield no catalog diff, manual sections preserved, malformed managed regions diagnosed |
| Concurrency | Source or ancestor changes between preview/apply; target file appears during creation; partial install failure; repair/rollback verified; no false claim of distributed atomicity |
| Task boundary | Every task writer refuses notebook targets appropriately; manual stray tasks remain diagnosable; plan/freshness/project/ledger counts unchanged |
| UI | Full destination and summary visible; block-ID prompt prefilled; keyboard and hover links; source/Reading/Live Preview; narrow/mobile, light/dark and plugin-disabled fallback |
| Migration | Before/after block-ID and link-resolution inventories; preserved provenance; repeat-run idempotence; recovery on stale manifest |

Use golden fixtures for representative parent catalogs and capture outcomes, plus cross-language contract fixtures for the Mac payloads. Focus tests on these behavioral boundaries rather than mirroring implementation helpers.

## 9. Requirement adjustments I recommend

| Original request | Adjustment and reason |
|---|---|
| New `type` value | Yes: `type: "[[notebook]]"`, with a recognized normalized classifier. It is a content type, not a task type/theme. |
| Only note bullets, optional H2s | Keep that authoring model, but permit multiline Markdown within note bullets and preserve/lint historical content instead of flattening it. |
| Parent is area/project/notebook | Enforce exactly one valid parent and an acyclic path to an area/project; notebook parenthood does not also authorize projects beneath notebooks. |
| Summary “maybe” in frontmatter | Make a short authored `summary` required for controlled creation/migration, with readable fallback plus diagnostics for manual omissions. |
| Root section recursively links notebooks | Use the existing root-parent partition, not every ancestor. Respect `root: true`; include nested paths as breadcrumbs. |
| `%n` creates notebooks | Interpret it only with the sealed creation route; keep standalone `%n` as Pomodoro note. Use creation prose as summary. |
| `@@` notebook capture | Preserve existing globals on non-notebooks; known notebook routes are item-local. Explicitly accept type-aware resolution as a design cost. |
| Section selection | Tighten notebook matching; never inherit legacy silent preamble fallback. Creation must be explicit in completion/preview. |
| All one-character aliases | Implement contextual parity through Bob's rewrite contract, with negative cases; do not globally replace punctuation. |
| Migrate useful stray notes | Begin with four simple conversions and one genuine orphan; defer mixed idea queues, source libraries and legacy hierarchy repair. |
| Future H2 extraction | Design IDs/link rewriting for it now; ship the command after the basic feature and first migration are proven. |
| Notebook under finished project | Allow reading and writing independently of project lifecycle; deliberately avoid borrowing project-create's terminal-parent restriction. |

## Recommended solution

Implement notebooks as **small, task-free context collections owned by the existing area/project hierarchy**. Require one valid parent and one concise scope summary, preserve file and block identity, and expose all of a root's notebooks through a stable Markdown catalog with tasteful Obsidian styling.

Honor the requested capture forms through explicit notebook intents and a shared type-aware destination policy. Keep old area/project global `@@` and standalone `%n` working, refuse unknown notebook destinations and misplaced task operations, and make preview unambiguous. The parser, aliases, prompts, preview and writer must agree before any files are migrated.

Ship the first four in-place conversions—**Developer tools, Linux operations, Networking notes, and SASE writing fragments**—together with a carefully previewed rescue of **`text/sase_notify.md`** into a SASE history notebook. Then triage the idea collections and pilot nested language notebooks. This delivers discoverable, useful knowledge immediately while preserving the boundary between what Bryan knows and what Bryan has committed to do.
