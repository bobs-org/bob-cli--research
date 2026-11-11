# Notebook H2 capture: explicit section groups, shared resolution, and a truthful picker

Independent research by **cdx**, 2026-11-11. No report, transcript, summary, or findings from the other researchers in this swarm were consulted.

## Judgment

**This is a good feature, but it is primarily a missing composition and presentation layer—not a missing `@notebook#` feature.** Bob already completes notebook H2s, creates missing sections, and writes notes through `@notebook#section`. The unfinished experience is grouping several notes into sections while creating or updating a notebook, particularly with bullet-start completion.

I recommend keeping the explicit destination route, adding **section groups** to notebook outlines, and sharing one resolver across completion, parse, preview, and commit. Reuse the drawer menu's keyboard habits and restrained appearance, but do not copy its ALL-CAPS replacement semantics into notebooks. Arbitrary notebook titles must survive selection unchanged.

The essential interaction should be:

```text
@dev_tools
- #git
  - Use worktrees for independent investigations.
- #"API Design"
  - Preserve meaning across API versions.
```

The groups write notes under `## Git` and `## API Design`; the group labels themselves are never note bullets. Picking a section only edits the draft. Capture remains the one atomic write.

## Scope and evidence

I inspected bob-cli at `01c8e822508fb34ce70dab4f4eaf375128b5cab7` and the linked Bob Mac Capture checkout at `ee26941dedaeff5cbfae6640daee18000b668e84`. I also exercised the installed `bob 0.5.0`, reporting capture grammar **25**, against disposable synthetic vaults. Every capture probe used `--dry-run` and an explicit synthetic `--bob-dir`; no real vault was read or changed. The installed executable was not rebuilt from the inspected SHA, so runtime observations are evidence about that executable, corroborated where noted by source—not an exact-SHA test run. No macOS visual or compilation checks were performed for this research.

The phrase “project capture syntax” needs two distinctions:

- `Summary @parent^id@ %n` creates a **notebook** using the existing sealed capture shape. This is a primary target of the proposed feature.
- `Goal @parent^id@` creates a **project**, where first-level ALL-CAPS groups already become H2 sections. Preserve that behavior. `@project` still creates tasks; `@project+prj` provides the existing project-section-as-drawer path. A notebook owned by a project is still addressed using its own `@notebook` route.

I assume the request means notebook creation plus writing into an existing notebook, including one owned by a project. If it also means routing selected children of a new project draft into a different existing notebook, that is an additional cross-destination child grammar; I would design it separately rather than infer it from this request.

### What exists, and what the probes found

| Surface | Observed current behavior | Consequence for this feature |
| --- | --- | --- |
| `Note @notes#` completion | `context: section`; real H2s only, in document order; H3 excluded | Reuse this path; it is already implemented |
| `Note @notes#workflows` | A `notebook_section_create` row; dry-run creates `## Workflows` | No new section-creation command is needed |
| `Note @notes#gi`, with `## Git` present | Menu offers Git and explicit `New section “Gi”`; direct dry-run refuses with `notebook_section_near_miss` | Completion may assist prefixes; commit must never interpret a prefix as an existing destination |
| `@notes` followed by `- #` | No completion; dry-run captures a literal `#` note | Bullet-start section support requires parser and writer work, not just UI wiring |
| `@notes` followed by `- GIT` and nested `- One` | Captures a note named GIT with a child, not an H2 group | Reusing drawer acceptance that inserts ALL-CAPS would silently write the wrong shape |
| `Parent @notes` followed by `- #api` | Completion offers drawer `API`, consequence “Starts API on the new task” | Notebook-aware classification must precede the old drawer probe |
| Notebook-create draft with `- GIT` and nested notes | Seeds `## Git` | Preserve the existing creation shorthand |
| Notebook-create draft with `- #git` and nested notes | Seeds a literal `#git` note | The explicit group spelling is new behavior here too |
| Later `@dev_fresh#` after creating `dev_fresh` with a Git section earlier in the draft | Empty section candidates; full `#Git` succeeds at dry-run and `#gi` refuses as a near miss | Completion reads disk where execution already knows the staged notebook |
| `Note @notes/` through `capture-rewrite` | Rewrites to `Note @notes#` | The attached slash alias already works |
| `@notes\n- /` or notebook-create `… %n\n- /` through `capture-rewrite` | No rewrite | Bullet alias support remains missing |
| Two literal `## Git` headings | Only the first is offered; selector resolves to the first | Reliable selection needs an explicit ambiguity policy |
| `Note @notes#` execution | Dry-run succeeds as an unsectioned note | An incomplete section destination can silently lose its intended placement |

The last observation has source support: `scan_route_marker` derives `section_range` from the parsed section flags; the strict refusal in `finish_notebook_claim` only runs if that range or an empty section survives. The feature should close this gap, not rely on a menu to prevent submission. [S1–S5]

There is also a presentation gap. The Mac's generic `.section` row uses `candidate.title` and the same heading accessibility hint for every row. It does not distinguish `kind: notebook_section_create` or show its `New section` label in that branch. The notebook **preview** does show new-section status, but that does not make the choice itself clear. This is source inspection, not a claim based on seeing the current app onscreen. [S8]

## The interaction contract I would ship

### Two forms, one meaning of “section”

Use the attached form for one destination:

```text
Use worktrees @dev_tools#git
Preserve API boundaries @dev_tools#"API Design"
A named observation @dev_tools#git^worktrees
```

Use a route-only header for several notes and destinations:

```text
@dev_tools
- An unsectioned observation.
- #git
  - Use worktrees.
  - Keep one worktree per investigation.
- #"API Design"
  - Preserve API boundaries.
```

Use the same explicit groups when creating a notebook:

```text
Tools and workflow observations @dev^tools@ %n
- #git
  - Use worktrees.
- #"API Design"
  - Preserve API boundaries.
```

A single-section batch needs no groups:

```text
@dev_tools#git
- Use worktrees.
- Keep one worktree per investigation.
```

These forms avoid a new sigil, command, or modal destination form. They also respect the existing distinction between a route-only list and an actual parent note.

### Exactly where `#` opens section completion

| Position | Proposed interpretation |
| --- | --- |
| Immediately after notebook `@nb#` | Notebook H2 picker, as today |
| First-level `- #` under route-only `@nb` | Notebook section-group picker |
| First-level `- #` in `@parent^id@ %n` creation | Section-group picker for the new notebook |
| First-level groups in ordinary sealed project creation | Keep existing project/drawer behavior; improve section wording where useful |
| Nested bullet inside a note or section group | Literal note content; do not reinterpret as another H2 |
| `Parent text @nb` followed by child bullets | Children belong to that note; no H2 group completion |
| `@nb+id` children | Children belong to the identified note; no H2 group completion |
| Children under `@nb#section` list header | All notes go to that section; no nested routing groups |
| Unrouted text, fenced code, inline code, escaped hash, or a wikilink | Preserve the existing grammar and completion precedence |

“First-level” must mean the structural outline level, not merely a physical line with `- `. The current list splitter turns a route-header list into per-bullet items, so a probe based on `line_index > 0` misses precisely the new use case. Resolve ownership using list/header metadata. [S3, S7]

A group owns **only its indented notes**. A following unindented sibling is not silently filed into the preceding section. Unsectioned siblings belong before the first H2 in the output; notes retain draft order within each destination, and existing section order stays unchanged. The preview should show this final placement explicitly.

For creation, collect unsectioned notes into the preamble, then render sections in first-appearance order. Repeated groups for one section merge in source order. This deliberately fixes a current asymmetry: `- GIT / nested note / - Outside` currently renders both notes under Git even though Outside is a sibling. Treat changing that behavior as a documented grammar change, with a regression example, rather than pretending the current writer already has indentation-bounded semantics.

### What selecting a section inserts

For notebook groups, retain a semantic selector:

```text
- #api
```

becomes, for example:

```text
- #"API Design"
  - |
```

Here `|` marks the caret, not inserted text. Bob chooses the shortest **round-tripping** spelling: a safe title/slug if it resolves uniquely and preserves identity, otherwise a quoted exact title. Quotes are not an instruction to rename an existing heading. Existing capitalization, punctuation, emoji, and acronyms survive.

If the group already has children, replace only the selector and preserve those children. If there is no child, Bob supplies the newline, indentation, and final caret in its replacement. The unfinished empty child remains an editable placeholder; submitting an empty group refuses instead of creating an empty H2.

Do not introduce `- #git note text` as a third compact form. It makes group titles and note text compete for the same line and behaves differently after acceptance. Use an indented child, or the existing `note text @nb#git` form.

Keep ALL-CAPS group support in **notebook creation** for compatibility, but do not make arbitrary ALL-CAPS notes in existing notebooks structural. Existing notebook lists currently permit such content. Extending that heuristic would break more drafts than the explicit hash syntax requires.

A literal hashtag at the structural group position must have an explicit escape, e.g. `- \#git`; the writer emits the literal hash without the escape. Other note-body positions retain their opaque text behavior. Prefixing a group with `#` is a grammar change from today's literal notebook bullets and needs clear migration examples.

### Scope of suggestions

Existing notebook: show that notebook's real H2s, followed by sections introduced by valid earlier draft operations on that notebook. Exclude frontmatter and fenced examples; H1 and H3+ are not targets. A notebook H2 named Tasks or Notebooks is not automatically reserved merely because those names are managed in other note kinds; apply ownership restrictions according to destination kind.

New notebook: there are no existing destination sections. Show sections already introduced earlier in its draft and the explicit creation row for a nonempty query. On an empty query, show a calm “Type a section name” empty state.

Do **not** add vault-wide recent section names in the first release. A heading in another notebook is not a destination in this notebook, and treating it like one encourages duplicate structure. If later usage justifies suggestions, put them in a separate “Create from…” group, with provenance and an explicit creation consequence. They must never masquerade as existing sections. This is a requirement refinement: I interpret “known notebook sections” as destination-local sections, not a global vocabulary.

`@@nb` remains draft-wide routing, with no `#` suffix or new item-local meaning. To group a batch by section, use the local `@nb` header. Unrouted notes inheriting `@@nb` remain ordinary notes; do not invent an implicit outline owner. [M1]

## A compact, attractive section menu

Use the drawer menu's established dimensions, typography, key handling, and restrained borders. Introduce section semantics and copy, not another full-screen picker or a row of new controls. A small notebook icon and breadcrumb make the destination evident; a `＋` row makes creation evident. Titles should dominate; counts and hints should be secondary.

Illustrative existing-notebook menu, with query `gi`:

```text
Section                         Developer tools · dev

  §  Git                                      8 notes
  ───────────────────────────────────────────────────
  ＋ New section “Gi”

Use Git, or explicitly create Gi
↑↓ select     Tab / Return choose     Esc close
```

The count above is illustrative. Only show counts Bob supplies from its notebook scan; Swift must not infer them or read the vault. Show a route when titles collide, an exact title in a tooltip or accessible label when clipped, and a readable breadcrumb when the notebook has nested ownership.

For a new notebook, the caption says `New notebook · Developer tools`; existing draft sections carry `In this draft`. A preview after selecting a create row says **New section · Workflows**, with the intended notebook directly alongside it. Do not use a success checkmark before capture succeeds.

Interaction rules:

1. Bare `#` opens with **no selection**, matching the drawer picker. This changes the current notebook section menu's lack of an explicit no-selection contract.
2. Typing filters immediately. An exact or prefix match among existing rows can receive the normal completion selection; a **create row never becomes selected solely because it is the only result**. It requires deliberate navigation or click.
3. For an empty query, retain document order. For a query, rank exact, prefix, then substring matches, with document order as the stable tie-breaker. Creation stays last. This is a small proposed refinement to the current filtered document-order behavior.
4. Tab/Return on a selected row edits the draft; that same keystroke must not also submit capture. Escape dismisses without changing the authored selector. Returning to an unfinished `#` remains incomplete, not a fallback note.
5. Undo reverses acceptance as one edit. Alias Undo and a second slash preserve the existing literal-key escape behavior.
6. Disabled ambiguous rows explain the reason. If the target cannot be read, show a bounded error and no create option; absence of evidence is not evidence of an empty notebook.
7. Keep the active choice by candidate identity across refreshed results, not list index. Discard results whose draft, caret, route, or request generation no longer matches.
8. VoiceOver announces destination, title, existing/new status, and refusal where present. Color, dashed borders, and icons reinforce words rather than carry meaning alone.

These choices align with primary-source guidance without importing an unrelated widget wholesale. Obsidian already uses `#` to discover and address headings, making the notation familiar. [Obsidian internal links](https://obsidian.md/help/links)

Apple recommends clear search scope, responsive suggestions, and simplified relevant results; those principles support a small local menu. The specific scoped layout here is my recommendation, not an Apple requirement. [Apple Human Interface Guidelines: Search fields](https://developer.apple.com/design/human-interface-guidelines/search-fields)

The WAI combobox pattern distinguishes suggested arbitrary values from fixed choices, and supports exploring suggestions then escaping without changing input. That is useful interaction evidence for preserving text until acceptance; its web ARIA roles are not a prescription for this native Swift app. [WAI Combobox Pattern](https://www.w3.org/WAI/ARIA/apg/patterns/combobox/)

## Reliability: one resolver and one staged view

The invariant should be: **applying any enabled completion replacement and then planning the resulting draft reaches exactly the advertised section and action.** A menu selection is not a secret instruction needed by the writer; the resulting text is sufficient for CLI, paste, and later editing.

### Matching and creation

Reuse `resolve_notebook_section`, but strengthen its outcome model to distinguish `Existing`, `Create`, `NearMiss`, and `Ambiguous`. Share it everywhere that can name a notebook H2. [S1]

- Prefer an exact title match over a slug match; require uniqueness at the selected matching tier.
- If no exact title exists, a unique whole slug can name a section. Never use prefix/fuzzy matching to choose a write destination.
- Multiple exact matching headings are ambiguous. Refuse capture and identify their locations; do not silently pick the first. A quoted title can distinguish different titles sharing a slug, but cannot distinguish duplicate identical titles. The user must rename those outside capture for now.
- Keep the existing unquoted near-miss protection and explicit quoted creation escape. Do not silently align the notebook threshold with the drawer threshold: notebook source currently uses strict-prefix matching and bounded Levenshtein distance up to **2**, whereas the drawer contract describes **1**. Reusing UI does not justify changing either policy.
- The create row must be computed by the same resolver. For a near miss, selection emits the explicit quoted spelling; merely typing the near miss still refuses.
- A bare attached `@nb#` or structural `- #` is incomplete. A group without a nonempty note cannot execute. This prevents both accidental unsectioned capture and empty section clutter.
- Preserve quoted title bytes as far as the existing literal grammar permits. Test smart quotes, escaped quotes/backslashes, emoji, non-Latin headings, Unicode normalization collisions, and acronym casing. Do not inherit the drawer lexer's ASCII-letter-only opening rule for all notebook titles without deliberate validation.

### Draft overlay and transactions

The writer already has a guarded batch planner and notebook policy with prospective/staged creation. Use those foundations. The completion path currently builds a notebook policy but section candidates independently call `read_target`; fix this split. [S1, S2, S4, S5]

Build a read-only view of the selected notebook from disk plus **valid preceding operations in source order**. Include sections from earlier notebook-create items and earlier section groups. A later creation must not make an earlier route valid. Failed or incomplete earlier operations must not become selectable phantom sections.

The overlay must carry provenance: existing on disk, staged in this draft, or proposed new. Do not run a whole vault mutation planner on each keystroke or require every unrelated later item to parse successfully. Reuse pure planning/resolution functions and narrow target snapshots; completion must remain useful while typing an incomplete group.

On capture, lower groups into ordinary notebook-note operations with section selectors and source ranges, then use the existing transaction. The section header is created once; every child gets its own top-level `[created::]` note stamp. Preserve child note IDs and existing nested detail conventions; do not attach an ID to the group label. A later failure rolls back the notebook and any owner-catalog changes together.

Retain the writer's current read dependencies and preimage guards. Re-resolve against the staged current content at submission; a stale completion is not write authority. If a heading disappeared, retyped, or became ambiguous, refresh the preview before writing when a prior preview exists. For stronger rename protection, an optional snapshot/fingerprint expectation can refuse a changed target; do not use an old line number as persistent heading identity. Keep command-line text deterministic even when no editor snapshot exists.

An unresolved detail to prototype is richer children under a section-group note: the group adds an outline level, while capture already has depth constraints. Preserve all currently valid note detail. If a third authored level is necessary to represent it, extend the notebook-specific outline parser deliberately; do not flatten or discard it and do not relax task drawer depth rules incidentally.

## The slash alias requires an explicit backend design

There is a real architectural constraint here. `capture-rewrite` is deliberately **purely lexical**, takes no vault directory, and proves `/` aliases by testing whether `#` would open completion. It cannot know whether an arbitrary route-only `@name` header belongs to a notebook. The current drawer probe also uses an editor parse without notebook options. [S3, S6, M1, M2]

Do not solve this by letting Swift inspect frontmatter, match `%n` with a separate parser, or infer notebook grammar from cached labels. Do not enable slash-to-hash conversion in every list merely because the character is after `- `: ordinary task lists and literal paths still exist.

My preferred protocol addition is a **typing-only semantic assist on the existing `capture-complete` endpoint**, which already has notebook context. The app identifies the physical typed key and supplies an optional internal post-keystroke alias request (conceptually `typed_alias: "/"`; exact CLI spelling is an implementation detail). Bob validates the substituted `#` against the notebook-aware context and returns the existing `TextEdit`/`AliasStamp` style of result.

Apply that edit against the original request snapshot, then request ordinary completion for the rewritten draft. Using a second request avoids ambiguous replacement ranges belonging to two different draft versions. Do not run this assist for paste, stdin, or capture execution. For lexical shapes such as an explicit notebook-create seal, the old lexical rewrite can continue to handle what it can prove, but it must use the same structural context recognizer.

This keeps the old rewrite endpoint lexical, the Mac thin, and the grammar in Bob. It adds a small protocol round trip only where semantic context is required. Old Bob versions simply offer no new assist; the literal slash stays. The app must arbitrate the existing rewrite and the new assist so only one applies, gate on advertised support, and discard late replies. If the extra round trip proves perceptible in a Mac measurement, return completion alongside the edit with an explicit post-edit coordinate contract; do not preemptively duplicate the grammar.

This protocol detail is the main reason I would not describe the work as “just reuse drawer completion.” It also resolves the current misleading task drawer menu for `Parent @notebook` by giving semantic context precedence.

## Alternatives and requirement adjustments

| Approach | Assessment |
| --- | --- |
| Only improve `@nb#` and repeat one route per note | Lowest risk and a useful first slice, but leaves batch authoring unnecessarily repetitive and fails the bullet-start request |
| Copy the drawer menu and insert ALL-CAPS | Familiar but currently writes literal notebook notes; loses mixed-case heading intent and imports task terminology |
| Treat every ALL-CAPS notebook bullet as a section | Short syntax, but changes valid note content and extends a creation heuristic into existing notebooks |
| Persist `- #section` groups in capture drafts | Recommended: explicit intent, exact titles, common resolver, readable typed and pasted forms |
| Accept literal Markdown `## Heading` as the new capture grammar | Attractive long-term, but conflicts with current capture item splitting and does not directly meet the bullet-start interaction; larger authoring redesign |
| Add `@@nb#section`, a new sigil, or a modal notebook-section command | Reverses established routing semantics or adds needless concepts |
| Global AI-inferred filing or section suggestions | Makes placement harder to predict; not needed for this request |

The requirements I would explicitly adjust are:

1. **“At the start of a bullet” means eligible first-level notebook outline groups**, not every note or nested bullet.
2. **Keep `#` in notebook group replacements** rather than copying drawer ALL-CAPS acceptance. Existing notebook-create ALL-CAPS input remains supported.
3. **Known sections are local to the destination plus preceding draft edits**; no global history catalog initially.
4. **Section groups are indentation-scoped**, including a documented correction to creation's current sibling placement.
5. **No implicit create selection, empty section creation, silent first duplicate, or incomplete-selector fallback.** These are reliability requirements, not optional polish.
6. **Do not reinterpret project destinations as notebooks.** Ownership by a project does not change what route identifies the notebook.
7. **Keep alias eligibility in Bob.** Add a bounded semantic typing assist rather than weaken the lexical rewrite contract or implement grammar in Swift.

These are design recommendations for approval through the normal implementation process, not edits to the accepted decision records. If adopted, record the new explicit notebook group contract and any supersession of creation's legacy grouping behavior. The existing notebook/no-task and thin-client decisions remain intact.

## Implementation boundaries and acceptance evidence

The natural implementation seams are:

- **Context/outline recognition:** `capture_language/draft.rs`, `notebook.rs`, `completion.rs`, and the notebook-aware editor parse. Introduce a destination-aware structural group representation; preserve exact original UTF-8 spans. Avoid treating notebooks as `DrawerBulletTarget::NewTask`.
- **Resolution and staged discovery:** notebook section resolver/policy plus `capture_complete/candidates.rs` and `engine.rs`. Route both attached and group completion through one notebook section service. Keep ordinary project/drawer resolvers separate where their rules differ.
- **Planning:** `capture/notebook_create.rs` and `notebook_note.rs`. Reuse note writes and batch guards; render grouped sections once and preserve each child's identity and detail.
- **Protocol:** keep `context: section` for attached routes; add optional notebook target, placement, row identity, origin, create/refusal, replacement, and `cursor_after` metadata as needed. A group can use the same context with `placement: bullet_group`; it must never advertise `drawer` task semantics. Reuse `notebook_section_create` rather than invent a parallel create type.
- **Mac presentation:** generalize the existing compact drawer-style menu's reusable layout while keeping section copy and semantics distinct. Add explicit create-row rendering, destination breadcrumbs, and section-group spans. Preserve generic fallback behavior for older Bob.
- **Documentation/release:** update `docs/capture.md`, `docs/notebooks.md`, syntax/protocol reference, and the Mac capture docs. Generate CLI docs if an option is added. Bump the grammar revision for the changed interpretation of notebook `- #…`, incomplete `@nb#`, and grouping; mark the breaking behavior with a Conventional Commit `!`. Use the daily release train; do not edit Cargo version or CHANGELOG manually. [M3]

I would first land shared resolution and explicit-route reliability, then notebook outline semantics and staged completion, then the semantic alias and polished Mac menu. This is sequencing within one feature, not a recommendation to stop after the easy part.

The decisive acceptance checks are:

| Category | Required evidence |
| --- | --- |
| Context | New notebook, existing root/project-owned/nested notebook, route-only list, ordinary note with children, project creation, existing project's `^prj`, explicit section list, `@nb+id`, and `@@nb` do the documented thing |
| Round trip | For every enabled candidate, splice its replacement at Bob's byte range and run parse/dry-run; target title and existing/create action equal the advertised row |
| Text | Mixed case, acronyms, emoji, non-Latin names, quoted whitespace, punctuation, escaped literals, CRLF, UTF-8 caret offsets, `#section^id`, fenced headings, and wikilinks survive |
| Shape | Empty/incomplete groups refuse; repeated groups merge; unsectioned siblings do not inherit the prior section; child details and IDs survive |
| Scope | Only selected notebook sections appear; prior staged sections appear, future and invalid staged sections do not |
| Ambiguity | Duplicate headings and slug collisions cannot choose a different section from the selected row; exact quoted disambiguation works where possible |
| Transaction | Preview and commit produce the same planned bytes; missing/changed/retyped targets and late failures abort atomically; completion itself never writes |
| Alias | Direct `#` and typed `/` converge; pasted `/` stays literal; Undo, doubled slash, Escape, stale replies, record paths, URLs, and Go To retain existing behavior |
| UI | Existing and new rows are visibly and accessibly distinct; creation requires deliberate selection; selection edits once, never also submits; keyboard and VoiceOver flows work |
| Compatibility | Old/new client combinations decode safely and gate new behavior; shell completion never inserts UI-only placeholders |

Use the repository's meaningful parser/CLI tests and portable Swift presentation tests, then compile the changed macOS targets and run exact-SHA macOS CI as required by the linked repository. Run the applicable docs gate. This report has not run those implementation checks because it changes no product code.

## Source map

These are the independently inspected primary sources. Paths are repository-relative, with the source revisions pinned in the evidence section above.

- **S1 — bob-cli:** `src/native/capture_language/notebook.rs`: `NotebookRoutePolicy`, `notebook_sections`, `resolve_notebook_section` (around lines 174–271), `scan_route_marker` (around 470), and `finish_notebook_claim` (around 1348).
- **S2 — bob-cli:** `src/native/capture_complete/candidates.rs:167–383`: disk-backed section dispatch, notebook candidate matching, explicit create replacements, and heading replacement round trips. `capture_complete/engine.rs:98–120, 464–510, 1217`: notebook policy construction, legacy bullet probe, section dispatch, and initial selection.
- **S3 — bob-cli:** `src/native/capture_language/completion.rs:2117` and `:3686`: completion entry point and drawer-bullet probing. `capture_language/drawer_bullet.rs`: first-level shortcut lexer and task/project-only targets. `capture_complete/drawers.rs`: bare ALL-CAPS replacements and continuation.
- **S4 — bob-cli:** `src/native/capture/notebook_create.rs:174`: `seed_body`, section detection, and rendering. `capture_notebooks.rs`: notebook policy adaptation. `capture/notebook_note.rs:547`: shared resolver use and guarded region insertion.
- **S5 — bob-cli tests, inspected rather than executed:** `tests/cli/capture/notebook_notes.rs` (section matching, lists, global inheritance, transactional writes); `tests/cli/capture/notebook_create.rs` (seeding and later same-draft writes); `src/native/capture_complete/tests/routes_tasks.rs:451–583, 714` (H2 discovery, create rows, quoted titles, suffix preservation).
- **S6 — bob-cli:** `src/native/capture_rewrite.rs` documents the lexical/no-vault endpoint; `capture_language/rewrite.rs:1295` implements hash alias eligibility. Runtime alias probes omitted `--bob-dir`, which that endpoint does not accept.
- **S7 — bob-cli:** `src/native/capture_language/draft.rs:279–407`: route-header list grouping and per-bullet item fanout. `docs/notebooks.md` and `docs/capture.md`: current behavioral contracts.
- **S8 — Bob Mac Capture:** `Sources/CaptureCore/CompletionRowContent.swift:539–639` (generic section row); `CaptureDrawerMenuPresentation.swift` (grouped menu, consequences, accessibility); `CaptureNotebookPresentation.swift` (existing preview metadata); `Sources/BobMacCapture/CapturePanelModel.swift:14804` (drawer presentation dispatch); `CaptureDrawerMenuView.swift` and `CapturePanelView.swift` (compact menu layout).
- **M1 — audited SASE memory:** `decisions:notebook-routes-write-notes`, `decisions:capture-sigils-say-where-what-how`, `decisions:capture-bullets-mirror-the-task-block`; glossary Capture, Notebook, Project Note Capture, Capture Alias, and Task Drawer.
- **M2 — audited SASE memory:** `decisions:mac-capture-is-a-thin-client`.
- **M3 — audited SASE memory:** `cli_rules.md`, `docs.md`, and `decisions:bob-cli-releases-ride-a-daily-train`.

## Recommended solution

**Ship destination-aware notebook section groups, with `@nb#section` for single-section capture and persistent `- #section` groups for notebook creation and route-only batch drafts.** Keep titles exact, scope the menu to the selected notebook and preceding draft edits, preserve ordinary note children, and reuse the existing atomic notebook writer.

Make the menu beautiful through a clear breadcrumb, quiet existing rows, an unmistakable creation row, predictable keyboard behavior, and a preview that shows final placement. Make it reliable through one shared resolver, explicit ambiguity and incompleteness refusals, and a notebook-aware typing assist owned by Bob. That is a focused extension of the current capture language with enough semantic work underneath to make the polished surface trustworthy.
