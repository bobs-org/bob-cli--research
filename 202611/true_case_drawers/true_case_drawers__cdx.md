# Case-preserving task drawers: explicit sections, familiar capture, honest round trips

Independent research by **cdx**, 2026-11-22. Research only; no product code or live-vault changes.

**Recommendation:** adopt an explicit drawer prefix, `- § Title as authored`, with a small section glyph and semibold title in rendered views. Keep `#` as capture's place-selection shortcut, reuse notebook section parsing/resolution where its contracts match, and preserve titles through capture, rename, promotion, and reversal. Land this after the relevant `bob-cli-on` work. Treat universal, lossless project/task conversion as a separate design problem.

This is a good change. Capitalization is content, and currently Bob consumes it as structural markup. Removing that coupling fixes a real information-loss problem and makes section titles more readable. The important adjustment is to replace the inference with an explicit structural marker, rather than another typography heuristic.

## Evidence and limits

I independently inspected these checkouts, opened through `sase repo open`:

| Repository | Inspected commit |
| --- | --- |
| bob-cli | `513ec47889893245cd0aacf7f67895efcc253817` |
| bob-plugins | `1e3852184dc6c1b780d6e9729071c5ba448171e5` |
| bob-mac-capture | `bf4b55ed01746cd23a18fa065c45a47f6ee721e0` |

I read `bob-cli-on` with `sase bead read`, its approved `plan:202611/task_requirements.md` with `sase artifact read`, and relevant drawer/notebook decisions through audited memory reads. I did not locate or read another report in this swarm or solicit another researcher's findings. Epic notes contained references to earlier, unrelated research; I did not open those reports.

I ran isolated dry runs against temporary fixture vaults using installed **bob 0.6.0, capture grammar 29**, with isolated config/cache locations. That binary is corroborating runtime evidence, not proof it was built from the inspected checkout SHA. I also executed the existing JS title-formatting function extracted directly from the plugin source. No actual Obsidian or macOS UI was exercised, and no production-vault inventory was performed. The presentation below is a design specification, not a screenshot of working software.

## What happens today

Drawer identity currently depends on an ASCII-uppercase title grammar. It permits a limited punctuation set, rejects `C++`, and distinguishes drawer titles from Pomodoro names through related predicates. A quoted drawer literal is still uppercased. The catalog, selector key, title validation, insertion geometry, and project-H2 adapter all live in [capture_drawers.rs][drawers]. Drawer completion inserts a bare uppercase title plus the child-bullet continuation. [Drawer completion source][completion]

Titles also change during conversion. Rust's `format_project_section_title` and the plugin's `formatProjectSectionTitle` lower-case the input and capitalize word runs; the source explicitly says acronyms are not preserved. Reversal uppercases the heading and validates it against the drawer grammar. Thus `API DESIGN → Api Design → API DESIGN` cannot recover `API design`, and an existing `## iOS / OAuth 2.0` loses spelling on reversal. [Rust conversion][project-capture], [JS conversion helpers][conversion-helpers]

These are measured results:

| Probe | Observed result |
| --- | --- |
| Capture new task with `- #"API design"` and a nested note | Preview writes `- API DESIGN`. |
| Capture with `- API design` and a nested note | Text survives, but `capture-parse` reports no `drawer_bullet` span. It is an ordinary note branch. |
| Capture with `- § API design` or `- **API design**` today | Also ordinary branches; neither proposal is already implemented. |
| Notebook capture with `- #"API design"` | Resolves the existing `## API design`, preserving its spelling. |
| Notebook capture with `- #"iOS / OAuth 2.0"` | Reports creation with exactly that title. |
| Drawer capture with `- #"C++"` | Exit 2, `invalid_drawer`. |
| Requirement `[ ]` nested beneath `#notes` | Exit 2, `req_in_drawer`. |
| Requirement directly under task, followed by `#notes` | Preview has a requirement followed by `NOTES` and its note. |
| `rename-drawer 'API DESIGN' 'API design'` | Exit 2, `same_drawer`. |
| Existing JS formatter: `iOS / OAuth 2.0` | `Ios / Oauth 2.0`. |
| Existing JS formatter: `eBPF & SQL` | `Ebpf & Sql`. |

The capture probes used `bob capture -b <fixture-vault> -f json --dry-run --no-clip -- <draft>`. Parsing used `bob capture-parse -f json -- <draft>`. For `@work+owner` followed by `- #api`, completion's existing-drawer replacement was `API DESIGN\n  - `.

The rename command is particularly relevant: its request validation rejects equal normalized keys before reading notes, and it deliberately writes uppercase drawer titles and title-cased project sections. Merely accepting lowercase in the scanner would leave both conversion and editing broken. [Rename implementation][rename]

There is an additional asymmetry: the vault drawer scanner recognizes an empty uppercase header, whereas capture authoring and promotion require nested content in important paths. The scanner documents this explicitly. The new contract should distinguish **recognition of existing structure** from **permission to create an empty drawer**. [capture_drawers.rs, `parse_drawer_title`][drawers]

## Compatibility with `bob-cli-on`

The epic explicitly names `^no-all-caps-for-drawers` as an intended follow-up. It is compatible in direction. It is not safe to implement as an isolated regex change while the epic is landing.

At the time of the audited read, phases 1–10, 13–14, and 16 were closed; **11 (Obsidian close card), 12 (promotion), 15 (Mac close card), and 17 (memory)** remained in progress. This is a snapshot; reread the bead before implementation. [Epic][epic]

The approved plan's constraints remain authoritative:

- Requirements are checkbox children without `#task`, structurally parented by a task or another requirement. A drawer breaks that ancestry chain.
- Drawers contain notes. They must not become containers for requirements or an alternate task status.
- A requirement-owning task files ordinary direct notes into its special notes drawer. That drawer is born with the **first note**, not automatically with the first requirement.
- Keep the established block zones: Cancel Log, managed links, requirements, authored children, drawers, logs. Notes is first among drawers where the requirement layout rule applies.
- The migration retires `REQUIREMENTS` in favor of `NOTES`/`## Notes`. This proposal must not revive the old name as a requirements container or infer requirements from old drawer content.
- Promotion moves only the outer requirement boundary to tasks. Nested requirements remain requirements of the resulting tasks. Loose notes and the notes drawer become `## Notes`; carried stubs remain notes.
- Rust owns semantics; JS twins share Rust-owned vectors; the Mac renders Bob's decisions.

The epic leaves other drawers' title-casing unchanged and leaves reversal unchanged. Those are precisely the portions this follow-up would intentionally replace. Its statement that a new marker is “one change in one place” is useful architectural intent, but understates the observed work: there are JS predicates/twins, rename rules, catalog caching, two conversion directions, completion replacements, preview models, and outside-text writers to coordinate. [Approved plan][epic-plan], [requirements contract][req-contract]

Two recorded epic issues intersect this proposal directly. Notes #2/#4 describe incorrect `^prj` notes-home handling: repeated `## NOTES` headings and task-style indentation beneath H2. Note #7 describes previews that show authored loose notes instead of their planned placement under NOTES. I did not reproduce those issues here; they are documented epic findings, not new independent discoveries. Revalidate them against the eventual landed epic. Do not copy either behavior into the shared drawer/section implementation.

**Sequencing recommendation:** depend on the epic's landing, at minimum its promotion, notes-home, rename/layout, and client contracts. Preserve its behavior through regression vectors. Keep its requirement glyphs and close-card semantics out of this feature. There is no reason to modify or reopen its migration as part of this research.

## Choosing an on-disk marker

The main criterion is that a reader can distinguish a section from prose without inspecting capitalization, and that software can do so without changing the owning task's classification.

| Representation | Strength | Cost or failure mode | Judgment |
| --- | --- | --- | --- |
| `- § API design` | Explicit section marker; keeps an ordinary list item; no tag or heading namespace; visible with plugins off; title unconstrained by case | Unicode symbol is inconvenient to type manually; needs custom styling for the desired finish | **Preferred**, paired with existing `#` capture completion |
| `- **API design**` | Familiar and attractive in ordinary Markdown | Gives ordinary emphasis structural meaning; bold note branches can silently become drawers; arbitrary Markdown in titles becomes harder to delimit | Strong visual alternative, weaker semantic boundary |
| `- ## API design` | Explicit, familiar heading syntax and obvious H2 relationship | Creates a real nested Markdown heading; heading-aware tooling, navigation and styling need an audit; risks confusion with requirement hash glyphs | Technically viable, but an unnecessarily broad behavioral change |
| `- #drawer API design` or `- API design #drawer` | Easy to query and type | Structural metadata enters note-wide tag/search semantics; requires every consumer to distinguish it from topical tags | Reject as the canonical form |
| `- API design %%drawer%%` or HTML comment | Explicit metadata without visible title restriction | In supporting views the only structural evidence disappears unless Bob decorates it; extra hidden state to preserve while editing | Possible escape hatch, poor default for a visible section |
| `- [drawer:: API design]` | Explicit field syntax | More bytes and metadata coupling; presentation depends on field rendering; conceptually a field instead of a section header | Unnecessary machinery |
| Nested callout | Native visual identity and folding | Changes the subtree into quoted content; prefixes every body line; current scanners deliberately exclude quotes | Too invasive for this change |
| `- API design:` | Very easy to type | Common prose and existing label syntax; repeats inference rather than establishing a reliable type boundary | Reject |

CommonMark permits block content inside list items, including headings. Therefore `- ## Title` is not just a decorative string: it can introduce heading semantics. Obsidian also documents headings as part of its Outline model. The precise effect on Bob's nested headings needs an Obsidian integration probe; I am not claiming to have tested that UI. [CommonMark list items](https://spec.commonmark.org/0.31.2/#list-items), [Obsidian formatting](https://help.obsidian.md/syntax)

The tag objection is directionally right, with an important qualification. Obsidian indexes tags as ways to find **notes**. Dataview separately exposes per-list-item tags and parent relationships; its documentation does **not** justify the blanket assertion that every child tag automatically becomes the parent task's own `tags` value. Nevertheless, using `#drawer` would introduce a structural tag into the note's tag namespace and require consumer-specific exceptions. We can avoid that entire ambiguity. [Obsidian tags](https://help.obsidian.md/tags), [Dataview task/list metadata](https://blacksmithgu.github.io/obsidian-dataview/annotation/metadata-tasks/)

This does **not** rule out capture's `#` shortcut. `@route+id#…` and a first-level `- #…` are instructions to the capture parser; the canonical writer need not store a tag. Keep the useful input gesture and choose independent storage syntax.

Comments have the opposite tradeoff: Obsidian's `%%…%%` is hidden in rendered views and is not portable Markdown comment syntax. Callouts carry native presentation but are explicitly blockquotes. Both are well-supported features, but neither matches the low-ceremony list structure wanted here. [Obsidian comments](https://help.obsidian.md/syntax), [Obsidian callouts](https://help.obsidian.md/callouts)

Why prefer `§` over inventing an ASCII delimiter such as `::`? It already visually denotes a section, takes one character, and avoids resemblance to Dataview fields. There should be one canonical spelling, not interchangeable `§`, `::`, and bold wrappers. Its typing cost is real; completion should eliminate that cost in the common flow. A small hands-on prototype should validate the glyph's feel before the storage decision is finalized.

## Proposed drawer contract

A normal task drawer is a **direct, non-checkbox list child of a real task** whose body begins with `§` followed by a space and a nonempty title. Managed logs/links keep their existing recognizers and precedence. Fence and quote exclusion, nearest-parent checks, and nested-task ownership remain mandatory.

```markdown
- [ ] #task Ship the API ^ship-api
    - [ ] Authentication works offline
    - § Notes
        - Agreed with Morgan on the rollout.
    - § API design
        - Preserve the OAuth response fields.
    - § iOS / OAuth 2.0
        - Keep the mobile fallback documented.
```

The example uses spaces for legibility; writers preserve the note's established indentation. `§` is structure, not part of the title. Headers remain list items, not task checkboxes or real Markdown headings.

Keep these separate in the model:

| Value | Purpose |
| --- | --- |
| Authored title text / raw source span | Display and serialization; never reconstructed from a key |
| Lookup key | Matching and existing Notes-role checks; no authority to change display text |
| Selector spelling | Input convenience, such as `api-design` or a quoted literal |
| Source kind and location | Explicit drawer, legacy drawer, or project H2; exact identity for a planned write |
| Header/body source ranges | Preserve title, descendants, indentation and untouched bytes |

A drawer called `API design` should promote to `## API design` and reverse to `- § API design`. Neither direction may run title case or uppercase formatting. Preserve existing spelling when a selector reaches an existing drawer. Choosing a common title from the catalog is explicit selection; its popularity must not silently override a freshly authored literal.

Support mixed case, Unicode and ordinary punctuation, including `C++`, using a nonempty single-line title rule instead of the current ASCII title alphabet. Keep structural reserved-name checks. Do not change Pomodoro-name grammar merely because it shares helpers with drawers today. Validate control characters and serialization boundaries, rather than inferring meaning from typography.

Do not normalize the stored title to achieve convenient lookup. Existing drawer keys collapse whitespace and ASCII-case-fold; notebook exact-title matching currently ignores ASCII case without the same whitespace step. Preserve those compatibility policies initially behind the shared resolver, and make any later unification an explicit contract change. No global Unicode-normalization policy needs to ride this feature. Unicode titles must at least round-trip verbatim and remain reachable by quoted selection.

For literal prose beginning with the marker, provide a clear escape. A source bullet such as ``- `§` refers to a section`` stays prose because its body starts with a code span, not the marker. Do not assume `\§` is a portable Markdown backslash escape. Imported external text must not acquire drawer semantics accidentally; the import path should preserve it as opaque text or escape the leading marker through an explicit, tested rule.

Retain the semantic notes role using the existing normalized `NOTES` key. Fresh system-created drawers can display `Notes`; existing `NOTES` titles remain exactly as authored until an explicit rename. Do not simultaneously add a general role-property system or allow arbitrary renaming of that special role without deciding where future ordinary notes go. Those would be separate behavioral changes.

**Empty headers:** recognize and preserve an explicit empty drawer structurally, so deleting its last note cannot turn it into a different kind of node. Keep the current capture rule that ordinary drawer creation needs content. For future conversion of empty project sections, decide explicitly whether to allow deliberate empty-drawer creation. Recognition and creation policy should be separate APIs.

## Capture: reuse notebook logic, preserve destination policy

The useful common concept is a **named place**. Its concrete output depends on the destination:

| Capture context | Selection | Writes |
| --- | --- | --- |
| Task | `@work+ship-api#"API design"` | A note in the task's `§ API design` drawer |
| Project's own `^prj` | `@project+prj#"API design"` | A note under `## API design` |
| Notebook | `@nb#"API design"` | A note under `## API design` |
| New task / note-less existing-task item | First-level `- #"API design"` plus nested notes | A marked drawer and its notes |
| Notebook body | First-level `- #"API design"` plus nested notes | An H2 section and its notes |

Keep the route shapes and the leading `#` picker. For tasks, accepting a completion should now produce:

```text
@work+ship-api
- § API design
  - |
```

Here `|` marks the caret. The marker remains in the draft, so the draft visibly expresses the structure it will write. Users may also type the canonical marker directly. Existing quoted shortcuts stay accepted until completion or commit resolves them. Notebook completion can retain its existing section-selector spelling; it need not adopt task storage syntax.

The [notebook resolver][notebook] already provides a useful pure operation: quoted literal resolution/creation, exact-title then whole-slug matching, ambiguity, near-miss refusal, and creation. It is shared between editor snapshots and staged writes. The [section-bullet lexer][section-bullet] already handles quoted names, escaped hashes, title-preferred replacement checks, and notebook-body routing. Reuse those building blocks rather than copying their behavior into a third parser.

There are real differences to retain or deliberately resolve:

- “Exact” currently means literal-selector mode, not byte-sensitive case matching: notebook `title_matches` uses `eq_ignore_ascii_case`.
- Notebook unquoted creation has its own capitalization formatter: it preserves uppercase-bearing words but title-cases other words and converts hyphens to spaces. It does **not** preserve every unquoted title verbatim.
- Drawer near-miss checking currently uses a different threshold from notebook sections: edit distance 1 versus up to 2. Reuse the mechanism with an explicit policy instead of silently widening drawer refusals.
- Task/project drawers have reserved managed names and project H2s have structural exclusions. Notebook sections have their own eligibility rules. Do not import task exclusions wholesale into notebooks.
- Notebook notes carry their existing note metadata rules; task drawer entries retain task-note rules. Shared selection must not unify these writers.
- A matching catalog row is a suggestion, not permission to skip commit-time resolution.

I recommend a small shared title-selector engine returning `Existing(identity, title)`, `Create(title)`, `Ambiguous(candidates)`, or `NearMiss(suggestion)`, with context adapters supplying candidates and policies. Keep mutation geometry in the destination writer. This directly avoids repeating the `^prj` notes-home mistake.

For unquoted new drawer names, retaining the notebook formatter is acceptable as an explicitly previewed convenience, but the creation row must show the exact title that will land. A quoted literal or directly authored `§ Title` is the guaranteed spelling path. This satisfies the capitalization goal without teaching users a wholly new targeting language.

Completion must preserve its strongest invariant: **apply any enabled replacement, parse it, preview it, and commit it; all four reach the same place with the same title**. Show the resolved write layout, including automatic Notes routing, rather than only the authored outline. Keep `#` incomplete while the picker is open; a cancelled or half-typed selector must not become accidental prose or a task type.

Case-only rename must become legal. For `API DESIGN → API design`, change the stored title and relevant heading links without treating equal keys as an error or merging distinct existing containers opportunistically. Preserve the existing explicit, previewed merge behavior for actual distinct-name renames. Duplicate source containers should be reported for review, not silently coalesced by this casing migration.

## Rendering: quiet section labels, clearly different from requirements

Drawers should be recognizable by shape and weight, not capitalization or color alone. Render the source example approximately as:

```text
⌗  Ship the API
   ⌗⌗ Authentication works offline
   §  Notes
      · Agreed with Morgan on the rollout.
   §  API design
      · Preserve the OAuth response fields.
   §  iOS / OAuth 2.0
      · Keep the mobile fallback documented.
```

This is a hierarchy sketch; the titles should be semibold in the real UI. Keep `§` as the visible section glyph so source and rendered modes share a recognizable cue. Use a neutral secondary ink for the glyph, normal foreground for the title, and restrained spacing before a drawer. A faint subtree guide is optional; do not add a heavy box around every drawer. Preserve the actual title case: no CSS uppercase or small-caps transformation.

Do not reuse the task/requirement `⌗` family or show a checkbox beside a drawer. Native list folding is enough initially. A disclosure control should appear only if it actually folds the subtree and exposes expanded/collapsed accessibility state. No permanent `Drawer` pill or item count is needed on every line; completion menus can show “Drawer · 3 notes” when it helps selection.

Use the same visual contract in Obsidian Live Preview, Reading view, capture editor spans, dry-run preview, and picker rows. In Source mode or with plugins disabled, `§` remains visible and the underlying list stays readable. Accessible names should identify “Drawer, API design” and folding state when relevant; the symbol alone should not be the spoken label.

The Mac already accepts Bob-authored drawer titles and creation flags through `CaptureSubBulletPresentation`; use those data, not local casing heuristics. Supply marker/title spans or explicit row kinds for drawer headers, and continue the existing thin-client approach. [Mac presentation model][mac-model]

Prefer decorating existing source ranges and actual text-layout coordinates. This marker is already visible, so there is no need to conceal invisible characters or build a detached glyph overlay. If a renderer replaces a marker, caret and selection must reveal and operate on the real bytes. Test wrapped titles, scrolling, folded parents, large font sizes, light/dark themes, copied text and accessibility. The raw source must not change just because a presentation layer is disabled.

## Why this is only one step toward lossless project conversion

The feature solves title identity and improves structural typing. It does not make every project representable as a task.

The inspected reversal implementation only accepts list-shaped section content, skips blank lines, drops empty sections in ordinary paths, and refuses non-list content or content outside recognized regions. The formatter can also refuse a heading that cannot become an uppercase drawer. These are concrete constraints, not hypothetical future edge cases. [Reversal splitter and builder][reversal]

The approved requirements promotion adds another distinction: a requirement becomes a task with task metadata, and loose notes merge into Notes. That is a useful semantic transformation, but by itself it is not an invertible serialization. It can erase the provenance needed to know whether a later row began as a requirement, a nested task, or a preexisting project task.

A future round-trip contract must address at least:

| Project information | Why a marked drawer alone is insufficient |
| --- | --- |
| Frontmatter, title, original path/stem, parent, note identity | A task headline does not encode the whole document envelope. |
| Duplicate H2s, empty H2s, heading order, H3+ structure | Name-based grouping or merging is not injective; hierarchy and boundaries matter. |
| Paragraphs, tables, fences, embeds, HTML, continuation lines | An outline of plain note bullets is not the whole Markdown document model. |
| Blank lines and whitespace | Required for byte-exact restoration; sometimes meaningful even for rendered semantics. |
| Relative links, heading links, block anchors | Relocation and title changes need identity-aware rewrites and collision handling. |
| Ordinary project tasks with lanes, dates, IDs and history | They cannot all become lightweight requirements without losing task semantics. |
| Generated catalogs and managed mirrors | Need explicit regenerate-versus-preserve ownership rules. |
| Notes merged from different source positions | A merged body cannot reveal the original split without provenance. |

Define “lossless” before claiming it. There are at least three different promises: preserve user-visible meaning; preserve all information needed to reconstruct the original document; reproduce original bytes except specified transforms. “Distinct representation for every project” implies an injective encoding, which is stronger than merely retaining most text.

For this feature, promise **title-preserving conversion for currently supported drawer/section bodies**, with refusal before writes if the title or body cannot be represented. Keep all current unsupported-content refusals. Add a pure drawer↔H2 round-trip test independent of the higher-level lifecycle transformation.

For the larger goal, a source-preserving document model with typed nodes and an explicit project envelope is more promising than adding special drawer names for every frontmatter field. Preserve raw spans and section boundaries; leave unknown content intact. Decide later whether the task representation must be self-contained or may reference preserved source. A hidden backup can prevent data loss but does not automatically satisfy the user's desire for a distinct, editable task representation.

One alternative to consider at that later stage is a task as a compact view/handle of a retained project document. It avoids serializing an arbitrary document into a list, but it is not equivalent to a self-contained task and should not be substituted without agreement. No need to resolve that architectural decision to fix casing now.

## Explicit adjustments to the request

1. **Make structure explicit, not merely case-insensitive.** Lowercase prose with children must remain prose. Bold and uppercase cease to be canonical structural signals after migration.
2. **Preserve title spelling end to end.** Include rename, both conversion directions, catalog choice, completion and previews; merely changing storage is insufficient.
3. **Separate narrow and broad losslessness.** This release preserves titles for supported structures; the universal project/task representation needs a separate spec and proof obligations.
4. **Broaden title characters along with capitalization.** Otherwise real section names such as `C++` and Unicode headings remain blocked, undermining the stated direction.
5. **Separate empty-header recognition from authoring policy.** Read explicit headers reliably even after their last child is removed; preserve the epic's first-note creation rule.
6. **Keep Notes semantics and requirement semantics unchanged.** Case preservation does not authorize a requirements redesign, a new notes role system, or resurrection of REQUIREMENTS.
7. **Do not guess historical capitalization.** A legacy `API DESIGN` cannot tell us whether the author intended `API design`, `API Design`, or `API DESIGN`. Migration should add a marker, not invent title case.

## Implementation boundaries and verification

This is an implementation recommendation, not an approved execution plan.

Start with a Rust-owned drawer-header model and conformance vectors. Include explicit and legacy encodings, display title, marker/title spans, and source identity. Route `capture_drawers`, `task_children`, `task_reqs`, block layout, tidy/writers, split and merge through it. Audit the helper relationship with Pomodoro names before changing any shared predicate. Existing [task child classification][children] and [block layout][layout] are the natural integration points.

Update capture tokenization and completion next, extracting the reusable notebook selector machinery with policy adapters. Preserve multi-item transactional writes, stale-snapshot checks, reserved-name refusals, and UTF-8 byte spans. Invalidate the drawer catalog cache format when its recognized representation changes.

Then coordinate the JS twins, navigation promotion/reversal, and Obsidian rendering. The inspected plugin has drawer predicates in task-split and requirement helpers, plus copies in cycler, navigation, ledger tools and block-ID handling; search by predicate use, not only by a file named “drawer.” Promotion changes must be based on the landed epic's requirement-aware implementation. The inspected plugin snapshot still contains older promotion behavior, which is consistent with phase 12 being active.

Update Mac rendering from authoritative spans/preview rows and its grammar compatibility checks. Treat this as a grammar/writer contract change, not a cosmetic update. Maintain the project's release discipline, run the relevant Rust/JS suites, and compile/type-check macOS targets through the repository's required macOS CI gate. Research-time dry runs do not replace those checks.

Only after compatible readers and writers are deployed across the participating clients should Bob emit or migrate the new canonical form in the real vault. Old readers can mistake `§ Notes` for a loose note and scoop it into a new NOTES drawer; backwards readability alone does not mean old writers are safe. Use a clear rollout compatibility boundary. Do not rely only on increasing a capture grammar number to protect independent vault-mutating plugins or older CLI hosts.

A migration should inventory old drawers and preexisting `§` lookalikes, retain raw title spelling, report reserved/ambiguous containers, and operate over a reviewed, preimage-checked snapshot. Cover closed and archived task blocks, templates and generated writers that can reintroduce uppercase headers. Keep the source title and descendants intact; never move requirements or convert checklist content. A second run should make no changes. Do not combine marker migration, title recasing, requirement conversion, and deduplication into one write.

A temporary dual reader can preserve legacy drawers. There must be an explicit end condition for uppercase inference; otherwise ordinary uppercase prose remains structurally ambiguous forever. Retire it only after the reviewed inventory and writer rollout justify doing so, with visible diagnostics for leftovers. Until then, keep the legacy parse provenance in the model so conversion can preserve the actual title without inventing missing capitalization.

Contract documentation needs to describe the new marker, quote semantics, Notes behavior and rollout. Future memory changes need their own authorized decisions; the epic's already approved memory choices do not automatically authorize this follow-up. I consulted the `sase_memory_write` workflow to identify that boundary and did not edit memory.

The most valuable acceptance cases are:

- `API design`, `iOS / OAuth 2.0`, `eBPF`, `C++`, punctuation and Unicode survive capture → drawer → H2 → drawer unchanged.
- Case-only rename works; same title/no change is idempotent; distinct-name merges remain explicit; duplicate identities do not silently collapse during migration.
- Plain mixed-case, uppercase and fully bold note branches behave according to the declared legacy/canonical mode, without surprise promotion.
- Notes and requirements preserve the epic's ancestry, derived state, ordering, first-note birth and promotion behavior. A drawer never becomes a requirement owner.
- Notebook/task/project targets share selector outcomes where policy agrees, and keep their deliberate differences where it does not.
- Every enabled completion replacement round-trips through parse, planned preview and commit; a stale target or duplicate match refuses without writes.
- External text, fenced examples, quotes and a literal `§` never accidentally become structural headers.
- Closed/archive blocks, CRLF, mixed indentation, existing anchors and heading links survive migration and renaming.
- Empty and unsupported project sections are preserved or refused explicitly; never silently discarded under a new “lossless” claim.
- Plugin-off source remains understandable, and all rendered surfaces distinguish drawers from notes and requirements at normal and enlarged text sizes.

## Source index

Repository links below are pinned to the code inspected locally; they were not used to fetch repository files over the web. The epic and plan were read through SASE's audited commands.

- [Task requirements epic][epic] and [approved epic plan][epic-plan].
- [Drawer scanner, selector and insertion implementation][drawers].
- [Drawer completion][completion], [notebook section resolution][notebook], [section-bullet lexer][section-bullet].
- [Rust project capture/title formatting][project-capture], [drawer rename][rename].
- [Task child classification][children], [task block layout][layout], [requirements contract][req-contract].
- [Plugin conversion helpers][conversion-helpers], [promotion seed][promotion], [project reversal][reversal].
- [Mac drawer preview presentation][mac-model].
- [CommonMark 0.31.2](https://spec.commonmark.org/0.31.2/), [Obsidian syntax](https://help.obsidian.md/syntax), [tags](https://help.obsidian.md/tags), [callouts](https://help.obsidian.md/callouts), and [Dataview task/list metadata](https://blacksmithgu.github.io/obsidian-dataview/annotation/metadata-tasks/).

[epic]: https://github.com/bobs-org/bob-cli--beads/blob/main/pages/bob-cli-on/README.md
[epic-plan]: https://github.com/bobs-org/bob-cli--plans/blob/main/202611/task_requirements.md
[drawers]: https://github.com/bobs-org/bob-cli/blob/513ec47889893245cd0aacf7f67895efcc253817/src/native/capture_drawers.rs
[completion]: https://github.com/bobs-org/bob-cli/blob/513ec47889893245cd0aacf7f67895efcc253817/src/native/capture_complete/drawers.rs
[notebook]: https://github.com/bobs-org/bob-cli/blob/513ec47889893245cd0aacf7f67895efcc253817/src/native/capture_language/notebook.rs
[section-bullet]: https://github.com/bobs-org/bob-cli/blob/513ec47889893245cd0aacf7f67895efcc253817/src/native/capture_language/section_bullet.rs
[project-capture]: https://github.com/bobs-org/bob-cli/blob/513ec47889893245cd0aacf7f67895efcc253817/src/native/capture_project_note.rs
[rename]: https://github.com/bobs-org/bob-cli/blob/513ec47889893245cd0aacf7f67895efcc253817/src/native/task_drawer_rename/mod.rs
[children]: https://github.com/bobs-org/bob-cli/blob/513ec47889893245cd0aacf7f67895efcc253817/src/native/task_children.rs
[layout]: https://github.com/bobs-org/bob-cli/blob/513ec47889893245cd0aacf7f67895efcc253817/src/native/task_block_layout.rs
[req-contract]: https://github.com/bobs-org/bob-cli/blob/513ec47889893245cd0aacf7f67895efcc253817/docs/task-requirements.md
[conversion-helpers]: https://github.com/bobs-org/bob-plugins/blob/1e3852184dc6c1b780d6e9729071c5ba448171e5/plugins/bob-navigation-hotkeys/src/100-yank-and-paths.js
[promotion]: https://github.com/bobs-org/bob-plugins/blob/1e3852184dc6c1b780d6e9729071c5ba448171e5/plugins/bob-navigation-hotkeys/src/110-project-seed.js
[reversal]: https://github.com/bobs-org/bob-plugins/blob/1e3852184dc6c1b780d6e9729071c5ba448171e5/plugins/bob-navigation-hotkeys/src/210-rename-and-line-context.js
[mac-model]: https://github.com/bobs-org/bob-mac-capture/blob/bf4b55ed01746cd23a18fa065c45a47f6ee721e0/Sources/CaptureCore/CaptureSubBulletPresentation.swift

## Recommended solution

Proceed with **explicit, case-preserving section drawers stored as `- § Title`**. Render a restrained section glyph and semibold, unchanged title; keep `#` completion as the easy authoring path. Reuse notebook selector parsing and resolution through destination-specific policies, while retaining separate writers for task children and H2 sections.

Build on the landed `bob-cli-on` requirements contract. Update capture, renaming, conversion in both directions, catalog handling and all clients together; permit case-only renames; migrate legacy headers without guessing their intended capitalization. Preserve unsupported content by refusing unsafe conversions.

This provides a coherent improvement now: titles become content again, sections become explicit, and task notes remain visually distinct from requirements. It also removes one real obstacle to future project/task round trips without pretending that a new drawer marker can encode an entire project document losslessly.
