# Custom note capture: schemas, guided entry, and a restrained first release

Independent research by **cdx**, 2026-11-08.

## Decision in brief

**Build this, as a small schema-backed note-creation feature inside Bob capture.** The vault already contains two established collections that justify it: **92 restaurant notes** in `eat/` and **15 podcast-show notes** in `podcasts/`. Begin with restaurants, use podcasts to prove the design is genuinely configurable, and defer movie and TV-show collections until their value is clearer.

The principal interaction should be **New note → Restaurant → a compact field card**, available from the existing capture panel. The textual equivalent should be explicit, proposed here as `%note:restaurant Lantern Café`. Bob supplies the fields, suggestions, validation, destination, and finished Markdown. The Mac app presents them. Required fields are enforced at commit; useful defaults and optional fields keep capture fast.

The feature should create ordinary Markdown notes. It should not introduce a database, a second capture engine, automatic task creation, or a universal replacement for Bob's specialized project and reference workflows.

All syntax, schema keys, and protocol additions below are **proposals**, not existing functionality.

## 1. Evidence and limits

I independently inspected the current capture implementation, the Mac client's models and card patterns, read-only Dataview results from the live vault, and selected source notes from an audited vault checkout. I did not read or request other swarm researchers' reports or findings. No product code, configuration, or vault notes were changed.

Repository snapshots examined:

| Repository | Revision | Relevant evidence |
| --- | --- | --- |
| `bob-cli` | `572ce974c9d933e8bb0547418fd421d22e2957b3` | Capture grammar, planner, writer, CLI configuration and documentation |
| `bobs-org/bob` | `3a8d74268373a51320c2cff3adf8487f5db22a80` | Restaurant and podcast notes, Bases, collection/type notes, TV context, Git inclusion rules |
| `bob-mac-capture` | `0583f37aef3241ffc872e11325f8afaec1c5cbcc` | Capture models, process client, inbox-route choice card |

Live-vault counts came from `bob query`, including the following reproducible queries. The broad type inventory includes templates and generated material for other types; restaurant and podcast counts were also checked directly in their respective folders.

```dataview
TABLE WITHOUT ID type AS Type, length(rows) AS Count, unique(rows.file.folder) AS Folders
WHERE type
GROUP BY type
SORT length(rows) DESC
```

```dataview
TABLE WITHOUT ID status AS Status, length(rows) AS Count
FROM "eat"
GROUP BY status
```

The query engine emitted warnings about ambiguous links elsewhere in the vault. Its restaurant and podcast results were successful, and selected records were corroborated in source. This is not an exhaustive audit of every untyped note, unsynced attachment, or external media service. In particular, `fun.md` links to `text/tv.txt`, but that file was unavailable in the opened checkout. Conclusions about TV and movies are therefore about the evidence available, not proof that no other lists exist.

External references below are primary product/specification documentation. Their described behavior was reviewed, not installed or benchmarked in this research.

## 2. What the vault actually needs

### Restaurants: an existing collection, with migration baggage

The current shape is already suitable for a generic schema:

```yaml
parent: "[[eat]]"
type: "[[restaurant]]"
title: "Ahrres"
status: liked
category: "Coffee"
location: "Westfield"
companions:
  - "[[kelly]]"
```

The source note also contains `lid`, `source_group`, `source_note`, `source_anchors`, `source_dates`, and `source_lines`. Those are largely historical identifiers and import provenance. They must **not** become questions on every new restaurant capture. The record `eat/1_walnut.md` has `category: null`, demonstrating why “a field occurs in old files” is insufficient evidence that a user must supply it. [V1]

The current statuses are **85 liked** and **7 not_liked**. `maybe_eat.md` separately holds restaurants to try. A creation workflow should support an honest **To try** state rather than silently call a new restaurant liked. A **Try again** state also matches the prose description in `eat.md`, although it was not present as a structured status in the queried collection. These are proposed additions, not existing stored values.

Categories are free text: examples include `Coffee`, `Breakfast`, `Burgers + Dogs`, several cheesesteak spellings, and mixed categories. Locations include both plain strings and quoted wikilinks with block targets and aliases. Preserve that flexibility. Suggestions can make spelling more consistent without turning every cuisine or town into a controlled vocabulary.

`eat.base` already filters on folder plus `type`, renders friendly verdicts, groups categories, and reads locations. It derives “Last Tried” from legacy `source_dates`. `eat.md` still contains a long historical restaurant list. Creating a new file alone will therefore populate the Base but not that historical list; a new creation date also cannot honestly stand in for a visit date. [V2]

### Podcasts: the second real schema

The vault has **15 podcast-show notes**, with **9 subscribed** and **6 unsubscribed**. Existing fields are `parent: "[[podcasts]]"`, `type: "[[podcast]]"`, `title`, `status`, `category`, and `url`, followed by migration fields such as `zorg_id` and `source_*`. `podcasts.md` embeds `podcasts.base` and retains explicit subscription lists. [V3]

The type note explicitly distinguishes **shows** from **episode references** and **literature notes from episodes**. Keep that distinction. Capturing a podcast record must not ingest an episode into the reference pipeline or subscribe to a service. A proposed `interested` status permits saving a recommendation without claiming an actual subscription.

`podcasts.base` derives “Added” from migration dates. It needs a `created` fallback for new notes. Its All Podcasts view can include new statuses, but labels and dedicated views should be updated intentionally.

### TV, movies, and other possible types

| Candidate | Evidence | Recommendation |
| --- | --- | --- |
| Restaurant | 92 typed records, a dedicated folder and Base | First release |
| Podcast show | 15 typed records, folder, type note and Base | Second schema in the same delivery effort |
| TV show | `tv.md` has a plain show bullet; `fun.md` has TV context and a link to an unavailable text list | Leave the existing list usable; add a schema when tracking status, season, companions, or notes warrants individual records |
| Movie | No established movie type appeared in the type inventory; `chad_movie.md` is a recommendation prompt, not a movie record | Defer; a small watchlist does not need one file per title |
| Book/article/episode | Bob already has reference and article behavior | Do not duplicate their ingestion, reading-task, annotation, or rendering semantics |
| Person, recipe, game, place | Plausible future uses, without enough evidence here | Let the registry accommodate them; do not ship speculative defaults |

If films and shows later need records, use distinct `movie` and `tv_show` types and directories, sharing basic field primitives. A show has seasons and ongoing status; a film has a release year and a finite viewing event. Avoid a broad `media` schema with many conditional fields merely to reuse title and URL.

A useful admission rule is: **create a type when individual entities repeatedly need their own identity, several stable fields, and a useful collection view**. A list remains a good representation when it is sufficient. [V4]

## 3. Critique and explicit requirement adjustments

The idea is good because it removes a repeated, error-prone step: remembering frontmatter, choosing a filename and folder, and satisfying the same conventions each time. Its main risk is scope expansion into a database designer and form platform inside an already sophisticated capture grammar.

I would make these adjustments:

1. **Call these note types everywhere.** Bob already uses “task type” for work categories and Pomodoro names. `#restaurant` must not silently become a note-creation operator, and existing `bob types` must not become an unrelated schema registry.
2. **Required does not mean manually entered.** `type`, `parent`, and `created` are supplied by Bob; `title` is supplied once; defaults can satisfy other required fields. A field with an unknown value should usually be optional rather than pressure the user to invent data.
3. **Support optional fields in version one.** Without them, each schema either becomes an interrogation or discards useful details. Blank optional fields are omitted from new frontmatter, not filled with dummy values.
4. **Enforce schemas on new captures, not continuously across the vault.** Existing notes remain editable Markdown. Report legacy inconsistencies through a read-only check; do not rewrite or invalidate old notes during an unrelated capture.
5. **Treat each directory as the canonical creation destination.** Do not infer type solely from a folder or move old files automatically when a schema changes. Membership checks should inspect both type and expected residence, reporting mismatches.
6. **Include collection visibility in the feature.** A successful capture must be discoverable in the appropriate Base. Updating a historical manual list on every capture would create a second source of truth.
7. **Keep schemas declarative and local.** No JavaScript, shell hooks, AI-required field extraction, external metadata APIs, or network-dependent completion in the first release.
8. **Generalize ordinary record creation, not specialized workflows.** A restaurant record should not get `#task`, a project task, a reading task, or a Pomodoro link merely because capture is the entry point.

These are deliberate scope changes: optional fields and dashboard adoption expand the minimum implementation; deferring speculative types, migrations, automation, and general editing keeps the feature manageable.

## 4. What to borrow from existing tools

Obsidian properties supply the right storage model: ordinary YAML with text, lists, numbers, checkboxes, dates, and times. Property types are associated with property **names across the vault**, not independently per note schema. Consequently `status` can have different allowed strings for restaurants and podcasts, but it should not be text in one and a number in another. Obsidian also does not provide full nested-property editing in its normal property UI. Keep written frontmatter flat. [Obsidian properties](https://obsidian.md/help/properties)

QuickAdd demonstrates that known input requirements can be collected in one form, optional inputs can be skipped, and inputs already supplied need not be asked again. That is a strong interaction precedent for a compact Bob field card. [QuickAdd one-page inputs](https://quickadd.obsidian.guide/docs/Advanced/onePageInputs/)

QuickAdd also separates note creation from appending content and exposes explicit existing-file policies. Bob should make its create intent and collision behavior equally clear. [QuickAdd Template choices](https://quickadd.obsidian.guide/docs/Choices/TemplateChoice/)

These precedents do not justify a QuickAdd dependency. Bob's native capture panel, command-line operation, and shared Rust planner already provide the relevant integration boundary. A plugin-only implementation would be a reasonable cheap experiment if capture inside Obsidian were sufficient; it does not satisfy this request's broader Bob capture experience.

JSON Schema usefully separates property declarations from required-property declarations. Presence alone also does not guarantee a meaningful nonempty value. Its `default` annotation does not insert a value during validation; Bob must explicitly apply its own defaults before validating. Use these semantics, but do not expose the entire JSON Schema language as a prerequisite for defining a restaurant form. [JSON Schema objects](https://json-schema.org/understanding-json-schema/reference/object), [JSON Schema annotations](https://json-schema.org/understanding-json-schema/reference/annotations)

## 5. Schema design and ownership

### One authoritative registry

I recommend a **vault-owned `.bob/note-types.yml`**, versioned alongside the notes. Schemas define the meaning of shared records, so they should travel with those records. Bob's existing host configuration remains responsible for host preferences; avoid per-host overrides of a type's required fields or destination.

This is a justified addition to the existing configuration architecture, which currently reads `~/.config/bob/config.yml` with environment overrides. Reusing a `note_types` section there would be mechanically simpler and is the strongest alternative. I prefer vault ownership because a copied or synchronized vault should retain the rules for creating its records. Do not support both locations with merging precedence in the first release. [B4]

**Concrete rollout dependency:** the vault's `.gitignore` ignores everything by default and explicitly includes selected formats and `.bob` journals. It does **not** generally include YAML files. Add an exact inclusion for `/.bob/note-types.yml` during implementation and verify it survives `bob vault-sync`. Merely placing the file under `.bob` does not make it synchronized. [V5]

A single registry is sufficient for two or a handful of types. If it grows large, split it later with a documented include mechanism. Do not begin with schema inheritance or several independently merged registries.

### Illustrative definition

```yaml
schema_version: 1
note_types:
  restaurant:
    label: Restaurant
    icon: fork.knife
    directory: eat
    type_link: "[[restaurant]]"
    parent: "[[eat]]"
    body_heading: Notes
    fields:
      - key: title
        label: Name
        kind: text
        required: true
      - key: status
        label: Verdict
        kind: choice
        required: true
        default: to_try
        choices:
          - {value: to_try, label: To try}
          - {value: liked, label: Liked}
          - {value: not_liked, label: Not for us}
          - {value: try_again, label: Try again}
      - key: location
        label: Town or location
        kind: text
        suggestions: existing
        allow_wikilink: true
      - key: category
        label: Food or category
        kind: text
        suggestions: existing
      - key: companions
        label: With
        kind: links
      - key: url
        label: Website or map
        kind: url
      - key: last_visited
        label: Last visited
        kind: date
```

This is a proposed compact DSL, not a finalized configuration contract. Omitted `required` means false. Field order defines form order. `icon` is presentation metadata with a generic fallback, never a validation requirement.

`title` is declared in the field list because its label and constraints belong to the type, but it is a reserved system-mapped field: the draft header supplies it, and Bob writes both frontmatter title and H1. Every type must declare it once. Bob always writes `type`, `parent`, and `created`; schemas cannot redefine them as ordinary user fields. `file_stem`, discussed below, is a reserved draft control rather than frontmatter.

Required validation means **present and valid after defaults**. A required text value cannot be whitespace-only; a required collection cannot be empty; `false` and `0` remain legitimate boolean and numeric values. An explicitly emptied required field is an error, not an invitation to silently reinsert a default. Optional blank values disappear; unknown keys and duplicate keys are errors on new captures.

For the initial restaurant schema, only the name requires typing. Status has the visible `to_try` default. Location is prominently suggested but optional: a recommendation should be capturable before its address is known. Category, companions, URL, and visit date are optional. Do not copy `[[kelly]]` as a default merely because it occurs in imported records. A user-configured default would be a different, explicit choice.

For podcasts, use title, a required status defaulting to `interested`, optional category with suggestions, and optional show URL. Validate a supplied URL as a supported absolute web URL; it must not require fetching the website. New categories remain allowed. Status choices include the existing `subscribed` and `unsubscribed` values.

### Keep the type system modest

The useful primitive set is text, choice, text list, link/link list, URL, date, number, and boolean. Implement the primitives needed by the two initial schemas first; defer unused controls if delivery cost becomes material. Store them using Obsidian-compatible scalars and lists, with no nested per-note objects.

A text field that permits a wikilink remains a string in YAML. Validate link targets with Bob's existing resolver; preserve aliases and block fragments. Require the system parent and type links to resolve, with setup errors if they do not. Free text locations need no fabricated town note. Link-only fields such as companions should offer explicit selections and report unresolved or ambiguous links rather than guess.

The loader should validate identifiers, field kinds, choice uniqueness, defaults, reserved keys, duplicate type links, duplicate or overlapping destination directories, and conflicts in the primitive storage type used by shared property names. Do not change Obsidian's property settings silently. If the schema file has merge-conflict markers or malformed YAML, refuse typed-note creation with an actionable diagnostic; ordinary task capture should continue working.

Suggestion catalogs are scoped to the same type and field, exclude import-only fields, and return canonical values plus display labels. Sort configured choices predictably; keep existing-value suggestions stable and searchable. Suggestions are assistance, never validation rules unless the field explicitly is a choice.

## 6. Capture syntax: make creation explicit

### Alternatives considered

| Syntax/approach | Advantage | Problem | Decision |
| --- | --- | --- | --- |
| `#restaurant ...` | Short | `#` already selects task types or attached places | Reject |
| `@eat ...` | Familiar | Currently means an existing-note destination; would silently change a task into a file | Preserve its meaning |
| `@eat/new-name ...` | Looks like a path | Couples schema identity to storage and invites route/path ambiguity | Do not make it the main syntax |
| `%restaurant ...` | Compact | User-defined names compete with built-in directives | Reject the unrestricted namespace |
| `%t` saved templates only | Existing machinery | Current templates expand capture drafts; they do not define required frontmatter or guided field types | Allow later reuse, not schema authority |
| A separate note-creation command only | Easy to isolate | Misses the existing capture panel and mixed drafts | Possible scripting surface later |
| `%note:restaurant ...` plus a field card | Explicit, discoverable, namespaced | Longer to type; needs one new item grammar | Recommend |

`%` already introduces how a draft expands. A namespaced `%note:<type-id>` fits that family without taking over `@` or `#`. The current directive lexer treats unknown edge `%...` tokens as errors, so an older Bob should refuse this draft rather than accidentally capture it as a task. Verify that guarantee against supported versions. Current source exposes grammar revision **19**; use the actual revision/capability scheme at implementation time rather than assuming an old decision's revision number. [B1]

### Canonical text form

```text
%note:restaurant Lantern Café
  location: Westfield
  category: Coffee
  status: to_try
- Recommended by Sam; try the breakfast sandwich.
```

The picker inserts the canonical type ID. Incomplete `%note:` or `%note:rest` invokes completion; commit requires an exact registered ID. No guessing from fuzzy menu state.

Recommended grammar boundaries:

- The directive must begin the item's first line. The rest of that line is the title, treated as literal text; punctuation such as `@`, `#`, `=`, or `+` in a restaurant name must not become task operators.
- Consecutive two-space-indented `key: value` lines form the **field stanza**, only within a typed-note item and only before its body bullets. This is an explicit extension to today's rule that subsequent lines must be authored bullets.
- Values use a deliberately restricted YAML scalar/inline-list syntax. Ordinary text can be unquoted; the card emits quoted strings when necessary. Use `companions: ["[[kelly]]"]` for a list. Reject duplicate keys, nested maps, tags, anchors, aliases, and multiline scalar constructs in this stanza.
- Top-level `-` body bullets and their supported nested bullets become content under `## Notes`. They are literal note content in this item; `- status: liked` is a note, not a property assignment. Body text does not create tasks or invoke drawer semantics.
- Blank lines retain their current meaning: the next capture item starts. A draft can mix a restaurant note and an ordinary task in distinct items.
- Competing destination declarations, forced task-route options, task operators outside literal title/body spans, and other expansion directives are refused for a typed-note item in version one. Do not compose `%t`, `%c`, or reference ingestion until their behavior has been designed.
- An explicit literal escape for `%note:` must continue to permit prose about the syntax. Invalid schemas, missing fields, or unknown types never fall through to ordinary task capture.

The flat stanza is a readable serialization for a **form-backed interaction**, not a demand that the user learn YAML. Supporting arbitrary inline `key=value` assignments as well would add a second quoting grammar without clear benefit; defer it.

The existing two-level bullet grammar should remain unchanged for all other capture kinds. Introduce a `TypedNote` item early enough in draft parsing that the field stanza cannot be rejected by the old child-line parser or misread by global marker scans.

## 7. A beautiful, keyboard-first field card

Start through the existing `%` menu's **New note…** entry, then select **Restaurant**. The menu writes `%note:restaurant ` into the draft and focuses the name. Direct typing reaches exactly the same state.

A proposed compact presentation:

```text
┌──────────────────────────────────────────────────────┐
│  Restaurant                                New note  │
│  Lantern Café                                        │
│                                                      │
│  Verdict          To try                         ▾   │
│  Town or location Westfield                          │
│  Food or category Coffee                             │
│                                                      │
│  ▸ More details                                      │
│  Recommended by Sam; try the breakfast sandwich.      │
│                                                      │
│  eat/lantern_café.md                                  │
│  Tab next field · Esc back             Create note ↵ │
└──────────────────────────────────────────────────────┘
```

The exact filename is generated by Bob and shown before creation; the rendering above illustrates the intended Unicode-preserving slug policy, not a current output guarantee.

Interaction rules:

- Keep a stable header and layout while suggestions change. Show name, status, and the two most useful optional fields; keep secondary fields under More details. Any required field always stays visible, including fields newly required by a schema edit.
- Use persistent labels, generous focus indicators, normal text editing, and a restrained type icon. Required or invalid status must not rely on color alone. Support VoiceOver, dynamic text sizes, dark/light appearance, and reduced motion.
- Tab/Shift-Tab move between fields. In an open suggestion list, Return accepts the highlighted suggestion and does not submit the note. With no picker open, Return submits only when complete; otherwise it focuses the first required field. Multiline body entry retains newline behavior. The footer explains the current Return action.
- Do not auto-select the first person, town link, or enum choice unless the schema explicitly defines it as a default. A displayed suggestion is not an answer.
- A missing required field has a calm prompt before submit. After attempted submit, show a concrete inline explanation, such as “Choose a verdict,” while preserving every entered value.
- Escape closes the current popup first, then returns to the intact draft. It never drops the record or creates a partial file. Ordinary draft persistence should retain the canonical text, including field values.
- Show an optional “View Markdown” disclosure with the actual rendered frontmatter/body. Keep schema hashes, wire versions, and filesystem internals out of this view.

The field card and the textual editor are two views of the **same draft**. Bob returns canonical text edits for card changes. Swift must not independently quote YAML, normalize field values, derive filenames, or validate schema semantics.

Do not rebuild a form whenever the user types: preserve focus and caret by stable field key. Bind asynchronous results to a draft generation and schema digest, discarding old responses. Suggestions should use a local catalog cached by Bob; preview must remain offline. Measure this on the Mac rather than treating subprocess timing from another host as proof of responsiveness. [B3, M1]

## 8. Implementation shape and protocol

The existing division of responsibility is a good foundation:

| Layer | Proposed responsibility |
| --- | --- |
| Registry loader | Parse and validate the vault schema; expose immutable descriptors and a content digest |
| `capture_language` | Recognize typed-note items, title/field spans and incomplete states; keep legacy grammar stable |
| `capture-parse` | Add typed-note metadata, field states, precise diagnostics, and capability evidence |
| `capture-complete` | Supply type, field-name, choice, existing-value and link candidates, with Bob-owned replacement ranges |
| Pure draft-edit operation | Turn a card edit into canonical text edits without writing the vault |
| Capture planner | Resolve defaults and links, detect duplicates, allocate a safe path, render the note, stage it |
| Existing batch writer | Commit the validated new file with proper creation semantics and rollback integration |
| Mac Capture | Render controls, send edits, manage focus and subprocesses, display Bob's preview and result |

The draft-edit operation can live beside the existing lexical rewrite machinery, but **do not make today's `capture-rewrite` silently become a vault-reading schema service**: its documented contract is purely lexical. Settle the additive transport during implementation. There must still be only one semantic implementation in Rust. No new subcommands under `bob capture`: its positional text grammar makes that invalid under the CLI rules. [B1, B3, B4]

An illustrative additive parse/preview object:

```json
{
  "note_capture": {
    "version": 1,
    "schema_digest": "…",
    "item_key": "…",
    "type_id": "restaurant",
    "state": "needs_fields",
    "fields": [
      {"key": "title", "kind": "text", "required": true,
       "value": "", "state": "missing"},
      {"key": "status", "kind": "choice", "required": true,
       "value": "to_try", "source": "default", "state": "valid"}
    ]
  }
}
```

Once complete, Bob also returns the planned relative path, rendered content, duplicate candidates and relevant warnings. Names and exact envelope placement are illustrative. The existing capture result does not share the parse response's schema-version contract, so do not blindly add the same root envelope everywhere. Use the established optional-object conventions and explicit feature checks. [M1]

Card edits carry the draft generation, item key, field key and schema digest. Reordering or changing items invalidates stale bindings; item number alone is insufficient. Commit re-reads the schema and relevant inputs. If a required field, default, destination, or other semantic input changed, retain the draft and ask for a refreshed preview rather than committing different semantics from those reviewed.

Compatibility matrix:

| App / Bob | Expected behavior |
| --- | --- |
| New app / new Bob | Full guided entry |
| Old app / new Bob | Ordinary captures unchanged; fully specified typed text can work if supported by its preview path, otherwise an explicit unsupported-feature message |
| New app / old Bob | Hide the New note capability; pasted syntax gets a clear refusal, draft retained |
| Old app / old Bob | No changed behavior |

Test the actual combinations; additive JSON decoding alone does not prove grammar compatibility. Keep existing response versions stable unless their semantics truly break. Any necessary CLI/JSON break must follow the repository's release policy.

For scripts, the canonical multiline draft goes through ordinary `bob capture` stdin. Missing requirements produce a nonzero result with structured `needs_fields`, and **no writes**. Do not open interactive prompts for piped or JSON consumers. A terminal wizard can follow later if terminal usage warrants it.

A read-only schema catalog/check surface is useful for configuration diagnostics. It should report the current definitions and, on explicit request, audit only their collection directories. It should not become a second note writer.

## 9. Reliability and data integrity

### File identity, duplicates, and races

Generate the default filename from the title using one documented, deterministic slug policy consistent with the vault's underscores. Normalize Unicode consistently, retain meaningful non-Latin characters, replace unsafe separators, and detect case-folding collisions on every host so Linux cannot create names that collide on the Mac. Do not use a title as a relative path.

If the proposed file already exists, **stop and show it**. Offer Open existing or an explicitly different filename. Do not append, overwrite, or silently choose `_2`. A reserved optional `file_stem` draft control can persist a user-selected disambiguation, such as `lantern_cafe_westfield`; it allows a basename only and is never written as a frontmatter field.

Also show likely semantic duplicates, using normalized title plus location for restaurants and title/normalized show URL for podcasts. This is a hint, not an identity proof: chains have several branches, and URL normalization can discard meaningful information. Resolve aliases and compare same-batch planned notes as well as on-disk notes.

A retried submission must never produce another automatically suffixed record. If success is uncertain after a process/connection failure, retain the exact draft and target, then inspect/report the existing file. Do not call it a successful retry solely because a file exists; a receipt mechanism can be added if transparent retry becomes a requirement.

**Existing writer limitation:** `capture/commit.rs` explicitly describes its disk-preimage checks as optimistic guards, not cross-process locking or a fully serialized transaction. It rechecks and then calls `fs::rename`, leaving a race. Reusing that code does not establish a create-never-overwrites guarantee. [B2]

For new records, add a true no-replace install primitive, such as an appropriate platform helper or a same-filesystem temporary-file/link strategy that atomically fails on an existing target. Integrate its cleanup into the batch writer. A cooperative lock may help Bob processes, but cannot alone protect against every external editor or sync writer. If the destination appears, preserve it and refuse/replan.

### Paths, serialization, and defaults

- Restrict destinations to normalized, vault-relative directories. Reject absolute paths, `..`, reserved/system directories and unsafe symlink traversal. Reject shared or overlapping directory ownership in the initial registry.
- Start with existing, validated directories; setting up a type includes creating its folder and parent/type notes. Do not let a mistyped capture spontaneously construct a new directory hierarchy.
- Serialize frontmatter through a typed YAML serializer. Test quotes, colons, hashes, brackets, multiline-looking strings, `false`, numeric-looking names, Unicode and wikilinks. User text never becomes YAML code, path instructions, shell code, or template expressions.
- Apply defaults once to an absent field, then validate. Show their provenance in the preview. Generate timestamps once per planned operation using Bob's clock rules; do not let form refreshes continually alter displayed creation time.
- Reserve system fields and reject conflicting author values. Do not synthesize import IDs, migration source dates, or companion history.

### Batches and failures

Plan every item before writing anything. A missing restaurant field in a mixed restaurant/task draft must refuse the entire draft and retain both items. Dry run must have no file, directory, task, network, or journal side effects. Guard schema contents and parent/type resolution inputs as well as target files.

For ordinary runtime failures, integrate new files into the existing cleanup and rollback path. Do not market that as arbitrary multi-file crash atomicity: a process killed between filesystem operations is a separate problem. The first release should document the existing boundary, make each new file installation atomic, preserve accurate partial-failure diagnostics, and provide recovery tests. A durable multi-file transaction journal would be a separate infrastructure decision, not a hidden claim of this feature.

## 10. Adoption, delivery slices, and meaningful tests

These are implementation priorities for evaluating scope, not an already approved implementation plan.

**First: schema and writer contract.** Load the registry, implement ordinary typed-note parsing/validation/rendering, dry-run output and safe create-only file installation. Cover restaurants and a distinct synthetic schema before integrating UI. Keep all new behavior opt-in.

**Second: restaurant experience end to end.** Add the type menu, generic field card, completion, errors and preview. Ship the actual restaurant definition. Update `eat.base` with To try/Try again labels and useful views. Add or expose the Base from the main collection note without silently rewriting its historical material. For Last Tried, prefer `last_visited`, fall back to legacy source dates, and leave an unvisited new note blank; never substitute `created` for a visit.

**Third: prove reuse with podcasts.** Add the podcast definition through data, without new Swift controls or a podcast-specific capture parser. Update `podcasts.base` to show Interested and use `created` when legacy added dates are absent. Present the Base as the current collection; mark old manual lists as historical or otherwise make their role explicit, instead of maintaining both representations automatically.

**Fourth: observe before expanding.** Try real captures of a restaurant recommendation, a place with an unknown location, a disliked place, two branches of one chain, a subscribed podcast, and a show recommendation without its URL. Use the friction in those tasks to decide whether more field kinds, a terminal wizard, or TV/movie records earn their cost.

Minimum verification should test user-visible invariants:

| Area | Evidence required |
| --- | --- |
| Existing grammar | Regression suite for routes, task types, directives, project creation, references, templates and authored bullets |
| New grammar | Missing/unknown type, partial field input, escaping, field/body boundary, literal sigils, duplicate keys, Unicode byte ranges and mixed drafts |
| Schema | Missing/blank required values, meaningful `false`/`0`, defaults, invalid choices, optional omission, reserved keys, bad paths, conflicts and malformed configuration |
| Serialization | Parse rendered frontmatter back and compare typed values; preserve links, aliases, titles and content |
| Creation | Existing filename, case/Unicode collisions, two simultaneous creators, symlink/path escape attempts, and two colliding notes in one batch |
| Transaction behavior | Invalid later item causes zero writes; injected later write failure rolls back prior new files; stale schema/parent/target refuses without losing the draft |
| Mac UI | Keyboard completion versus submit, focus persistence, cancellation, stale responses, optional fields, accessibility and long labels |
| Compatibility | Capability absent, older server refusal, unknown optional fields, supported grammar combinations |
| Collection visibility | New restaurant/podcast appears in the intended Base with an honest status and date |
| Performance | Measure typing-to-suggestion and typing-to-preview on the Mac; verify catalogs do not rescan the entire vault per keystroke |

The Mac repository requires compiling Swift and macOS CI for the app-specific targets. A portable test pass alone is insufficient. This research did not run product tests because it made no implementation changes.

## 11. Source map

The following are the local source documents inspected, identified by the revisions in section 1. Repository paths refer to those repositories, not to another researcher's report.

- **B1 — Bob capture language:** `src/native/capture_language/mod.rs` (grammar revision), `model.rs` (capture kinds), `directive.rs` (directive namespace and unknown-token refusal); `docs/capture.md` and `docs/reference/capture-syntax.md` (item and child grammar).
- **B2 — Bob planning and writes:** `src/native/capture/plan.rs`, `batch.rs`, `commit.rs`, and `project_note.rs`; `src/native/capture_project_note.rs` supplies an existing note-rendering precedent. The optimistic-guard caveat is documented directly above `validate_disk_preimages` in `commit.rs`.
- **B3 — Existing editor integration:** `src/native/capture_parse.rs`, `capture_complete.rs`, `capture_rewrite.rs`, `capture/inbox_route.rs`; `docs/reference/mac-capture/capture-previews.md`; `docs/reference/cli/capture-templates.md`.
- **B4 — Configuration and CLI rules:** `docs/reference/configuration.md`, `src/native/config/mod.rs`, `src/native/config/capture.rs`; audited SASE memory `cli_rules.md`.
- **V1 — Restaurant records:** `restaurant.md`, `eat/ahrres.md`, `eat/1_walnut.md`; live `bob query` samples and status/type inventory.
- **V2 — Restaurant views/history:** `eat.base`, `eat.md`, `maybe_eat.md`.
- **V3 — Podcast records/views:** `podcast.md`, `podcasts.md`, `podcasts.base`, `podcasts/ai_daily_brief.md`; live folder and status queries.
- **V4 — Media evidence:** `tv.md`, `fun.md`, `chad_movie.md`, the type inventory and filename discovery. The linked `text/tv.txt` was unavailable in the checkout.
- **V5 — Vault synchronization scope:** `.gitignore`, especially its default deny rule and explicit format/journal inclusions.
- **M1 — Mac presentation/protocol:** `Sources/CaptureCore/CaptureModels.swift`, `BobProcessClient.swift`, `Sources/BobMacCapture/CaptureInboxRouteChoiceView.swift`, and the repository's `AGENTS.md` verification requirements.
- **Accepted architecture reviewed through audited memory:** `decisions:capture-sigils-say-where-what-how`, `decisions:capture-bullets-mirror-the-task-block`, `decisions:mac-capture-is-a-thin-client`; `glossary:capture`, `glossary:task-type`, `glossary:reference-note`, and `obsidian.md`.
- **External primary documentation:** [Obsidian properties](https://obsidian.md/help/properties), [QuickAdd one-page inputs](https://quickadd.obsidian.guide/docs/Advanced/onePageInputs/), [QuickAdd Template choices](https://quickadd.obsidian.guide/docs/Choices/TemplateChoice/), [JSON Schema objects](https://json-schema.org/understanding-json-schema/reference/object), [JSON Schema annotations](https://json-schema.org/understanding-json-schema/reference/annotations).

## 12. Recommended solution

Implement a **small vault-owned note-type registry and one generic guided creation card**, backed entirely by Bob's existing capture engine. Use explicit `%note:<type>` intent, keep schema-driven fields in a readable canonical draft, validate required values after visible defaults, and create ordinary Markdown with an unambiguous parent and type. Make creation collision-safe and keep preview, validation, completion, and commit under the same Rust authority.

Start with **Restaurant → `eat/`**, then **Podcast → `podcasts/`** as the proof that a second real type needs configuration rather than custom UI code. Include the Base adjustments and schema sync rule in the feature's completion criteria. Make location, category, URL and other enrichment optional unless a particular schema has a concrete reason to require them.

Defer movie/TV schemas, automatic metadata fetching, schema inheritance, automatic migrations, and generalized editing. The best result is a fast, pleasant way to create a well-formed record whenever the record is useful—not an obligation to turn every list into a collection of files.
