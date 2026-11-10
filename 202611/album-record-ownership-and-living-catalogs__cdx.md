# Albums as the home of record notes

Independent design research by **cdx**, 2026-11-10.

An album should be the place where a collection becomes useful: its schema, its records, and its relationship to a responsibility all meet in one note. I recommend this feature, with a narrow model: **record → album → area/project**, one canonical parent at each step, and the existing Root Parent calculation above that. Keep record kinds such as `restaurant` and `podcast`; introduce `album` for the collection note. Reuse the records engine and notebook catalog infrastructure, and preserve the existing Bases as interactive browsers.

Two findings materially change the requested migration. **`podcasts.md` already exists; `podcast.md` is the type-definition note and must remain.** Also, all 152 records inspected already point to their collection notes. The missing connection is primarily between collections and the responsibility tree, not between individual records and collections.

This report is research, not an implementation or a vault edit. No peer report, peer chat, or peer findings were consulted. Observations below come from source, a separately opened vault checkout, a read-only records check, and official Obsidian documentation. Suggested behavior is explicitly distinguished from current behavior.

## 1. What exists today

### Observed repository snapshots

| Repository | Inspected revision | Evidence used |
| --- | --- | --- |
| `bobs-org/bob-cli` | `9cd4ec3e590d187ecdad70e685c198bd45095b6c` | Records, capture, notebook catalogs, root resolution, contracts |
| `bobs-org/bob` vault | `36213b799fab08927fdaf583d63a20eb9108a62a` | Collection notes, record metadata, Bases, `job.md` history |
| linked `chezmoi` | `c6ae11ba186b82ad046eb4852e23cb26c4fcc09d` | `home/dot_config/bob/config.yml`, including all four record definitions |
| `bobs-org/bob-plugins` | `12e6e728f37367d666e771b2292d99d3c3076f13` | Notebook catalog rendering, data refresh, styling |

These are checkout observations, not a claim that every running host has identical state. Implementation must repeat preflight against the then-current vault and installed versions.

### The requested rename is already done

The vault has separate notes with separate responsibilities:

- `podcast.md` has `parent: "[[type]]"` and explains the `[[podcast]]` record type.
- `podcasts.md` is the collection, currently under `[[mind]]`. It embeds `podcasts.base`, retains a hand-authored subscription index with old anchors, and contains a few useful general notes.
- Every file in `podcasts/` has `type: "[[podcast]]"` and `parent: "[[podcasts]]"`.

Promote **`podcasts.md`**, changing its parent to `[[dev]]` as requested. Do not rename the singular note or rewrite record type links to `[[podcasts]]`. A singular type and plural collection are useful distinctions here, not obsolete clutter. [V1]

### Collection and record inventory

The following counts were independently read from immediate Markdown files and their YAML frontmatter in the vault snapshot:

| Proposed album | Record kind | Records | Existing record parents | Current collection parent | Existing statuses |
| --- | --- | ---: | --- | --- | --- |
| `eat.md` | `restaurant` | 104 | All `[[eat]]` | `[[h2_role]]` | 86 liked, 11 to try, 7 not liked |
| `podcasts.md` | `podcast` | 15 | All `[[podcasts]]` | `[[mind]]` | 9 subscribed, 6 unsubscribed |
| `tv.md` | `show` | 23 | All `[[tv]]` | `[[fun.md\|fun]]` | 23 to watch |
| `movies.md` | `movie` | 10 | All `[[movies]]` | `[[fun]]` | 9 to watch, 1 watched |

None of these collection notes currently declares `type: "[[album]]"`. `eat.md` still contains Zorg conversion metadata, large text tables, LID syntax, and a footnote section. `tv.md` is a short note with one legacy bullet for The Studio, although the record and Base already exist. `movies.md` is already a clean scaffold. These need different migrations, not a blanket rewrite. [V1]

The active schema source has four definitions under `records:`: restaurant/eat, podcast/podcasts, show/tv, movie/movies. The Rust schema already validates field kinds, ordered choices, defaults, required values, safe unique folders, and cross-type property storage compatibility. The catalog reads only the requested folder's immediate Markdown frontmatter and is lazy per invocation. Capture and CLI creation share a planner; updates preserve untouched YAML spans and body bytes. This is a strong foundation to retain. [C1–C3]

Current ownership is weak: a configured explicit record parent is written literally; otherwise creation uses `[[<dir>]]` only if `<dir>.md` exists. No album type or mandatory ownership contract is enforced there. The current records checker validates type and fields, but does not establish the proposed record → album → owner invariant. [C2]

### A real migration baseline, not an assumed clean vault

Running `bob records check -b <opened-vault> -f json` was read-only and exited **1**. It reported:

| Kind | Errors | Warnings | Cause |
| --- | ---: | ---: | --- |
| restaurant | 110 | 3 | 104 undeclared `companions` fields; 6 empty required categories; equivalent location spellings |
| podcast | 0 | 0 | Clean against current schema |
| show | 23 | 0 | Undeclared `companions` |
| movie | 10 | 0 | Undeclared `companions` |

All 137 restaurant/show/movie records carry `companions`; the configured definitions do not declare it. Preserve that real information and add an optional link-list field to those album schemas. **Do not add a default companion merely because current examples often name Kelly.** This is a small, justified schema repair beyond a byte-for-byte relocation.

The six missing restaurant categories belong to `1_walnut`, `bagel_supreme`, `clark_bagels`, `pardon_my_cheesesteak`, `rustic_mill_diner`, and `urban_burger`. Migration should retain those records and explicitly report the existing findings. Do not invent categories, delete records, or downgrade every schema rule to obtain a green check. This is part of the migration baseline, not a separate unrelated feature.

### What the `job.md` cleanup teaches

The vault's `fbab517019e2026b27342691f39840d85e5348d2` commit, “vault: de-zorg area notes and move legacy notes into notebooks,” removed Zorg generator/source metadata and obsolete identity decoration from `job.md`, and replaced legacy `theme` with `task_type`. The current note is a clear area/task front door; `legacy_job.md` is a notebook under `[[job]]`, with a summary stating that the historical material moved there on October 12. [V2]

The transferable principle is **clean the working front door while retaining history in an appropriate, linked home**. It is not “remove everything old.” The album cleanup must preserve record identity, meaningful notes, and old link targets.

## 2. Critique and explicit requirement adjustments

The idea is good. Collections currently carry useful information but sit outside the well-defined note hierarchy. Albums give them a visible owner, put schema changes beside their consequences, and make the whole collection portable with the vault. A restaurant's `parent: [[eat]]` becomes meaningful beyond navigation.

There are limits worth making explicit:

1. **Responsibility ownership is one dimension, not the whole meaning of a record.** A podcast can concern development, comedy, and relationships. One canonical album owner keeps routing predictable; ordinary links, categories, and references express other relationships. Do not introduce multiple `parent` values or duplicate records to reflect every interest.
2. **A record is not automatically a task.** “To try” and “to watch” express possibilities. They must not become Ready lanes, review obligations, decay candidates, or Pomodoro commitments. An actual commitment is a task in an area/project, linking to the record.
3. **An album is not a Root Parent.** In Bob, Root Parent has established reporting semantics. Albums and records should pass through to the existing resolver; no new stored `root_parent` field, and no `root: true` on albums. An album under a non-root subproject belongs directly to that project while its computed root may be a higher project. An ancestor area remains the life-responsibility context. [M1, C4]
4. **“Everything I track” should not mean “every note becomes a record.”** Keep notebooks for unstructured observations, references for external material, projects for outcomes, and records for schema-backed durable things. One restaurant note is not a meal-event database. Visit histories, listening sessions, and quantitative time series would need a separately designed event model.
5. **Moving schemas into notes has an editing cost.** Obsidian's standard Properties UI does not support nested properties; it recommends Source mode for them. The move still makes sense, but it needs readable schema inspection and precise file/field diagnostics. It will not automatically yield a friendly schema editor. [O1]

**Adjustments I recommend:**

| Requested direction | Recommended adjustment | Why |
| --- | --- | --- |
| Rename `podcast.md` to `podcasts.md` | Keep both; promote the already-existing plural collection | Prevent overwriting an album or destroying the type distinction |
| Give records a root parent | Require record → album → area/project; derive root using existing rules | Avoid conflicting ownership fields and changed Stats semantics |
| Move configured definitions into albums | One album owns one existing record kind and one folder in v1 | Matches the current engine; avoids a premature reusable-schema system |
| Beautiful album summaries | Compact deterministic snapshot plus the existing native Base | Good orientation without recreating filtering and table editing |
| New area/project H2 | `## Albums`, containing an index of albums, not copies of their records | Keeps the owner note focused and avoids very large duplicated tables |
| De-zorg collections | Preserve and map history and anchors before removing legacy layouts | Existing links and provenance are real data |
| Migrate definitions unchanged | Also declare observed `companions` as an optional link list | Prevents 137 legitimate fields becoming permanent schema errors |
| Everything should be linked to a responsibility | Require album owner chains to reach an area, but allow cross-links freely | Ownership need not constrain discovery or meaning |

I would not merge albums with notebooks. A notebook's contents are note bullets; an album's members are independent files governed by a schema. That difference affects validation, capture syntax, counts, and presentation enough to justify a note type.

## 3. Proposed data contract

### Identity and ancestry

For v1:

- An **album** is a vault-root note with `type: "[[album]]"`, one `parent` resolving unambiguously to an area or project, and one schema declaration. Its full parent chain must be acyclic and reach an area. A completed project may retain its albums; completion does not delete records or automatically reparent them.
- A **record** retains its domain type, such as `type: "[[restaurant]]"`, and has one `parent` pointing to its album. Its physical folder must agree with that album's declared folder. Folder membership alone does not silently repair a conflicting parent.
- An album's immediate owner is its area/project parent; its root is computed with the existing resolver. Neither album nor record is a task residence, a project, or a root boundary.
- One record kind ID and one folder belong to exactly one album. IDs and folders are globally unique using the existing normalization/collision rules. Reserve `album` as a record kind ID.
- Keep album filename, record kind ID, and folder as explicit distinct identities. They commonly align, but `eat`/`restaurant` and `tv`/`show` demonstrate why inferring all three from a filename would be wrong.
- Ordinary reparenting changes placement only. Renaming an album does not implicitly move its folder or rename its kind. A dedicated migration updates inbound links and member parents when a filename changes.
- Do not allow nested albums or albums under notebooks in v1. There is no demonstrated need, and the notebook contract presently forbids record children. Historical notebooks created during migration should therefore sit under the album's area/project owner, with a normal link back to the album. [M1, C5]

### Frontmatter shape

Use top-level metadata for the album itself, and a single nested `record:` declaration for the record schema. The following is a **proposed** schema, not syntax supported by today's binary:

```yaml
---
parent: "[[body]]"
type: "[[album]]"
summary: Restaurants to try, return to, or remember avoiding.
record:
  schema_version: 1
  id: restaurant
  dir: eat
  label: Restaurant
  emoji: 🍽️
  dated_notes: true
  fields:
    status:
      required: true
      values:
        to_try: 🔖 To try
        liked: 💚 Liked
        not_liked: 🚫 Not liked
    category: {required: true, suggest: true}
    location: {required: true, suggest: true}
    companions: {values: link, list: true}
    visited: {values: date}
    url: {values: url}
  legacy: [lid, source_*]
---
```

This relocates the established language rather than inventing a new form system. `schema_version` describes the declaration format, not each edit to its fields. Preserve ordered fields/choices, typed defaults, validation rules, and storage-shape checks. A structured error should name `eat.md`, the relevant line when available, and `record.fields.location`, instead of pointing to host configuration. [C1, O1]

The old schema-level `parent` option disappears for album-managed kinds: the containing album is always the record parent. A legacy explicit parent that differs from the prospective album must appear as a migration conflict, never be silently discarded.

An `album.md` type-definition note should sit under `[[type]]`, just as the existing `podcast.md`, `restaurant.md`, `show.md`, and `movie.md` explain their kinds. Keep those kind notes lightweight and link to their owning albums. They must not become a second source of schema definitions.

### Authority and failure behavior

The canonical state is the album declaration, member note bytes, and existing area/project graph. Generated summaries, catalogs, and caches are derived.

- Build one vault-aware registry used by CLI, capture parse, preview, completion, target discovery, related-record suggestions, checker, and notebook record classification. Eliminate host-global schema reads from these consumers.
- Load declarations from root notes; lazily read member folders only as needed. Ordinary task capture must retain its existing no-record-work fast path. Do not make each keystroke recursively scan the vault. [C3]
- Guard declaration bytes, owner ancestry, and membership-discovery inputs as transaction read dependencies. Schema edits or newly appearing records between planning and commit invalidate a planned summary; checking only files being overwritten is insufficient.
- A malformed album remains visible as a broken album. A route known to be a record route must fail with a useful diagnostic, never silently turn into task capture.
- Isolate a local schema error to its album when discovery proves it is local. Duplicate IDs/folders and conflicting property storage types affect every involved declaration. Incomplete discovery prevents writes based on an assumed complete registry.
- Required-field problems on an existing record do not remove it from the browser. Keep the current policy of validating changed fields on update while reporting untouched problems. Creation still requires a valid complete record.
- Records in the wrong folder, with the wrong parent, or with conflicting type declarations appear in diagnostics. Do not silently adopt, move, drop, or double-count them.

At the reporting layer, distinguish **members**, **members needing metadata repair**, and **misplaced/conflicting candidates**. A member whose category is missing still counts as a member; a file whose parent disagrees is a conflict, not an invisible record. Status distributions include an explicit unknown/invalid bucket so their totals reconcile with member counts.

## 4. Presentation: two levels, two reader questions

### The album answers “What is here, and what do I want next?”

Use a clear H1, a one-sentence scope, an unobtrusive owner link/breadcrumb, a compact generated overview, and one interactive Base. Keep authored general notes and history links below. No generic wall of properties, enormous generated duplicate table, cover-art fetching, or new JavaScript query language is needed.

An illustrative `eat.md` body, using observed counts:

```markdown
# Restaurants

Restaurants to try, return to, or remember avoiding. · [[body|Body]]

## Records

> [!album] 🍽️ Restaurants
> **104 restaurants** · 🔖 11 to try · 💚 86 liked · 🚫 7 not liked

[[eat.base#🔖 To Try|Choose somewhere new]] · [[eat.base#💚 Favorites|Return to a favorite]] · [[eat.base#🗺️ By Town|Browse by town]]

![[eat.base#🔖 To Try]]

## Notes

Related: [[drink]] · [[legacy_eat|Historical restaurant notes]]
```

The overview count/status line is a generated snapshot of record fields. Its action labels and choice of Base view are authored presentation, not guessed from arbitrary status strings. Treat the generated region and authored Base/navigation region separately. Render status counts in declared choice order when the schema defines a scalar choice field named `status`; otherwise show the total without inventing a lifecycle. Invalid/missing statuses get a clearly labelled bucket. Empty albums show “No records yet” with a route-specific capture example, and still appear in their owner's catalog.

A precise ownership choice is: **Bob owns only the `[!album]` callout containing the title and count/status line; Bryan owns adjacent navigation links, the Base embed, headings, and notes.** The example renders without a special Bob plugin; Bob's plugin enhances typography and actions, not basic readability. Native Bases still requires Obsidian's Bases core plugin; outside Obsidian, the snapshot and ordinary links remain readable.

The native Base provides filtering, grouping, sorting, and editing; its data remains ordinary note properties. Bases can embed a named view via `![[File.base#View]]`. These are existing platform capabilities, so reuse them instead of building a parallel browser. [O2, O3]

Suggested default experiences:

| Album | Overview | Main browser | Secondary useful views |
| --- | --- | --- | --- |
| Restaurants | Total and each verdict/status count | To try; restaurant, cuisine, location | Liked, by town, all, not liked |
| Podcasts | Total; subscribed, to try, unsubscribed | Subscribed; title, category, listen link | To try, all, unsubscribed |
| TV | Total; watching, to watch, watched, dropped | Watching when useful; otherwise explicitly choose To watch | All, watched with verdict |
| Movies | Total; to watch, watched | To watch; title, year, service | Watched with verdict, all |

The default view is authored and stable; do not switch it underneath someone when counts change. Empty views should say what is empty and link to the full collection, not imply data loss. Keep roughly three or four useful visible columns on narrow screens; additional metadata belongs in the record or optional views. Use text labels with icons so color is never the only signal.

**Do not infer activity from file modification times or migration dates.** Only 2 of 104 restaurant records currently have `visited`; only 13 have `created`; podcast records have no `created`. `eat.base` currently derives “Last Tried” from `source_dates` when `visited` is absent. Those source codes are provenance, not proven visit events. Preserve the underlying dates, but remove that behavioral claim or relabel it clearly as a source date. Offer “Visited” only where an actual visit date exists; show unknown rather than guessing. Avoid “Recently active,” stale badges, streaks, and trend charts until meaningful event data exists. [V3]

Also avoid treating `liked` as a ranked favorite or an instruction to recommend a particular restaurant. The existing Favorites view can remain, but its semantics are a filter over liked records. The system has no evidence for popularity, frequency, or relative preference.

### The owner answers “What collections belong to this responsibility?”

Add **`## Albums`**, adjacent to `## Notebooks` and before `## Tasks` on first insertion. Later, preserve its position. A portable source form:

```markdown
## Albums

> [!albums]
>
> - 🍽️ **[[eat|Restaurants]]** — Restaurants to try, return to, or remember avoiding.
```

Under `dev.md`:

```markdown
## Albums

> [!albums]
>
> - 🎙️ **[[podcasts|Podcasts]]** — Shows I follow, sample, or have stopped listening to.
```

The enhanced Obsidian view can decorate those rows using Bob's report:

```text
Restaurants                                      104 records
Restaurants to try, return to, or remember avoiding.
11 to try · 86 liked · 7 not liked                     Open →
```

Use the existing area's color as a restrained border/accent, readable linked titles, muted one-line summaries, and compact aligned counts. On mobile, stack counts below the summary. A keyboard user should be able to follow every action; reduced motion and plugin-disabled rendering should remain useful. Extend the notebook catalog's existing rendering patterns and stale/error handling. [P1]

Persist only stable catalog links/scope text in parent notes; counts are live client decorations. This follows the notebook precedent and prevents every restaurant update from rewriting `body.md`, creating needless cross-host merge traffic. The album itself can keep its small portable snapshot, refreshed together with its own record writes.

For v1, include **direct child albums only**. The request explicitly asks for the section in the specified parent, and direct membership is easy to explain. An album under a project appears in that project; the area already links its projects. A read-only `albums list` may group by computed root for a wider overview. Recursive parent catalogs can follow later if actual usage justifies them; if added, adopt the notebook root-boundary/grouping rule rather than inventing a different hierarchy. This intentional difference from notebook rollups should be documented.

Do not put all restaurant records, pending-watch queues, aggregate “life completion” percentages, or automatic recommendation prose into the owner section. Albums contribute context, not another work queue.

## 5. Generated-region and refresh design

Reuse the notebook transaction and region patterns, but use distinct `[!album]` and `[!albums]` regions with explicit owners. Recognize them only outside frontmatter and code fences and only on the appropriate note kinds. The heading's text alone must not grant write ownership. Escape titles, summaries, labels, and links before writing Markdown; schema content is data, never executable template code. [C5, P1]

Expected lifecycle:

1. Record create/update plans its final record bytes and the affected album summary from one overlaid snapshot. A mixed capture draft remains one all-or-nothing transaction, including several records in the same album.
2. Album create/reparent/summary changes update affected owner catalogs. Reparenting removes the old row and adds the new row in one transaction; record files need no edits.
3. Manual note edits and vault-sync trigger a debounced read refresh for displayed data. A guarded sync command repairs persisted snapshots/catalogs. Integrate the lock-free repair core into nightly under its existing lock.
4. Read-only list/check/preview commands never repair files. No-op sync writes and commits nothing. Do not stamp a changing “generated at” time into every summary.
5. Incomplete scans never delete catalog rows. A damaged affected region refuses the relevant transaction. Do not silently report record success while an intended atomic summary write failed. Unrelated damaged albums need not block healthy ones when dependency scope is known.
6. Preserve all bytes outside owned regions, including newline style and moved headings. When the last album leaves an owner, remove its owned callout; remove the H2 only if the section is otherwise blank.

A nightly refresh alone is insufficient for a feature used immediately after capture. Conversely, a background writer should not repeatedly rewrite an unsaved editor buffer. Reuse the existing guarded file writer and notebook client synchronization lifecycle, and test Obsidian save/sync races.

This is deliberately a small amount of materialization: one per-album count/status snapshot, stable owner indexes, and live Base rows. It avoids both extremes of a new custom database UI and hundreds of duplicated Markdown rows.

## 6. Implementation boundaries and compatibility

The code change is wider than swapping one config loader. These are concrete touchpoints observed in source:

| Surface | Current files | Required change |
| --- | --- | --- |
| Schema definitions/loading | `src/native/config/records.rs`, `src/native/records/schema.rs` | Vault-aware album registry; reuse field validation; source provenance; reserve `album` |
| Create/update/check/init | `src/native/records/{plan,check,init,cli,render,catalog}.rs` | Mandatory album parent, album bootstrap, integrity diagnostics, overview planning |
| Capture and live preview | `src/native/capture_record.rs`, `src/native/capture/record_note.rs`, `src/native/capture_parse.rs` | Same registry and staged overlay across parse/preview/commit; declaration read guards |
| Completion/routes | `src/native/capture_complete/{records,candidates,shell}.rs`, `src/native/capture_targets.rs` | Vault-scoped schemas and album context; preserve existing record route forms |
| Related records | `src/native/capture_related/records.rs` | Continue sharing record semantics and ownership data |
| Notebook classification | `src/native/notebooks/snapshot.rs` | Stop loading record IDs from host-global configuration; keep child-kind checks accurate |
| Root/owner resolution | `src/native/pomodoro_homes/{facts,resolve}.rs` | Reuse traversal; explicit album validation elsewhere; regression tests for transparent wrappers |
| Catalogs and transactions | `src/native/notebooks/{catalog,region,snapshot,txn,sync}.rs` | Extract only useful shared mechanisms; avoid a broad generic graph framework |
| Obsidian rendering | `bob-ledger-tools` notebook API/data/catalog fragments and styles | Album overview/catalog rendering and cache invalidation; task-only destination guards |
| Mac capture client | Existing versioned Bob subprocess interfaces | Verify rendering, schema errors, new context fields, and album-file invalidation; no Swift schema parser |

The root resolver already follows `Other` notes through `parent` until it finds an area/project. This makes transparent album ancestry feasible without introducing a new reporting root kind. It does **not** by itself validate album parents or prevent tasks from being captured into albums; those need explicit checks. [C4]

Preserve `@eat/`, `@eat/^stem`, `@eat/existing_stem`, and the corresponding podcast routes. A bare `@eat` should not create an orphan task in the album. Teach `@eat/` for a record and `@body` for a task. This intentionally tightens today's behavior, where a collection route can remain task capture with a warning; treat that as a contract change and cover forced routes and completion, not just ordinary text parsing. [C1]

Keep `bob records` as the record-facing command family. Add a small album-facing family with read-only `list`/`show`/`check`, explicit `sync`, and a bootstrap `create` operation. `records new/update/show/check` keep their type-ID arguments and become backed by albums. Preserve `records init TYPE` as an idempotent scaffolder for a known declaration, and provide an explicit migration path for legacy configured types. Do not hard-remove or gratuitously rename commands. Bare `albums` should mean read-only list; public flags need short aliases and alphabetical help per project conventions. Exact new options should be settled against the full CLI design, not frozen by this research sketch. [M2]

Proposed additive JSON data: album path/title, owner, root, breadcrumb, declaration source, member counts, status counts, findings, and catalog/overview state. Keep strings versus nullable values and version negotiation explicit. Existing `kind: record` routing need not change just because an album exists.

## 7. Migration: preserve meaning before cleaning appearance

### Schema and rollout migration

Migrate all four configured kinds, including the comparatively clean TV/movie collections. Set `eat → body` and `podcasts → dev` explicitly. Preserve `tv → fun` and `movies → fun` after normalizing and validating their links.

The migration tool should produce a preview and manifest containing input hashes, proposed paths, schema equivalence results, parent changes, existing findings, anchor/link mappings, and expected output inventory. Then apply through the existing lock/guard/rollback machinery. A second run must be a no-op.

Definitions must end up with **one authority in the vault**. Prefer no automatic runtime fallback: the migration operation explicitly reads legacy config, while upgraded record commands read albums only. Missing declarations produce an actionable migration diagnostic. This avoids a stale host config resurrecting a deleted or broken album.

For staggered installation, first prepare all four albums with semantically equivalent definitions while old clients can still use the existing config. Hold schema-changing record work during the cutover; verify that every writing host and capture client supports the album source. Then apply deliberate schema repairs such as `companions`, remove the definitions from the chezmoi source, and apply that change to hosts. If a compatibility reader proves necessary, require whole-registry equality during transition and an explicit cutover; never merge individual fields or silently choose one source. Verify capture from a host with no `records:` block. Preview equivalence separately from the intentional repairs so reviewers can distinguish relocation from changed semantics.

Do not claim vault and chezmoi updates are one atomic transaction: they are different repositories and deployment channels. Make their checkpoints explicit, keep a reversible migration manifest, and gate cutover on compatible clients. Follow the normal daily release train; do not hand-edit versions or bypass release CI.

### Content migration, album by album

**Restaurants require the most care.** There are already 104 record notes; do not re-import the old tables and create duplicates. Preserve unique record bodies and match historical table rows using multiple clues: source note, source anchors, LID, name, and existing file identity. Examine `maybe_eat.md` too, because to-try records may already represent its list.

Crucially, `eat.md` has two duplicated block IDs: `z-240410-7y` and `z-240410-7z`. Existing record provenance maps each to two different records (`garlic_rose`/`pancheros`, and `hop_hing`/`track_5`). **A global anchor-to-record replacement cannot be trusted.** Use unambiguous mappings where possible; preserve ambiguous targets and report them for inspection. Do not guess from the order files happen to be scanned. [V4]

A broad textual scan found 1,220 `[[eat...]]` link occurrences in 493 Markdown files. This includes metadata and generated/historical material, so it is not an exact count of links needing edits. It is sufficient evidence that deleting the old anchors without a link audit would be reckless.

Recommended cleanup:

- Move retained legacy prose, unresolved tables, and footnotes into a task-free `legacy_eat.md` notebook under `[[body]]`; normalize only what the notebook contract requires, preserving meaningful block identity and provenance.
- Give the working `eat.md` the album schema and new presentation. Remove its obsolete Zorg generator metadata and table-alignment instructions after the historical material is durably retained.
- Rewrite unambiguous active links to their record or preserved historical destination. Maintain a folded compatibility section with old target anchors where safe mapping is not possible; each ambiguous target should expose both candidate records rather than choose one. Check duplicate anchors explicitly.
- Preserve `source_*`, LID, and Zorg IDs on record notes until their consumers and all link/provenance uses have been audited. The visible front door can be clean while hidden historical metadata remains.
- Move any genuine open tasks encountered to the appropriate area/project through the task mover. Do not convert them to record statuses or silently delete checkboxes.

**Podcasts:** adopt existing `podcasts.md`, set its parent to `dev`, replace duplicate static subscription lists with the generated overview/Base, and preserve the 17 old anchors or rewrite their consumers using a verified map. Keep the Spotify note-taking instructions and useful links as authored notes. Keep `podcast_ref` and `lit/podcasts` distinct: a show record is not an episode reference or literature note.

**TV:** preserve `tv.md#^studio`, either on a small compatibility link to `tv/the_studio` or through verified link rewriting. Do not create The Studio again. Add the album schema and Base embed.

**Movies:** promote the clean scaffold with the schema and overview; retain authored Base customizations.

**Bases:** retain the current `.base` files, their named views, and customized formulas. Update only reviewed filters/columns/date labels as necessary. New scaffolding must never overwrite these files by default. Align the main membership filter with the album parent, type, and expected folder, and expose conflicts in the checker so strict filters cannot hide corruption without notice. Keep provenance-only properties out of default everyday views. [V1, V3]

### Acceptance criteria worth testing

These are implementation tests to add where they prove behavior; none were run against a nonexistent implementation:

- A record under `eat` resolves through `body`; an album under a non-root subproject inherits the correct existing Root Parent; closed-project ownership remains stable.
- Missing, multiple, ambiguous, cyclic, or wrong-kind parents are reported; duplicate IDs/folders and property-shape conflicts never choose an arbitrary winner.
- Create, update, parse, preview, completion, list, check, and notebook child classification all see the same album schema, including with `--bob-dir` selecting a different vault.
- Bare album routes and task-move destinations cannot create task residence in an album; ordinary task capture still works when an unrelated album is malformed.
- A mixed capture failure leaves no record or catalog behind; same-album multi-item drafts generate a final correct count; concurrent schema/parent/membership changes refuse stale writes.
- `sync --dry-run` is byte-preserving; repeated real sync is a no-op; incomplete scans never remove rows; authored text, headings, code fences, Unicode, CRLF, and unrelated regions survive.
- Existing record bodies and all 152 record identities survive migration. Known schema findings are visible. Distinguish new failures from the documented baseline.
- Podcast type identity stays singular; no existing plural collection is overwritten; unresolved legacy anchors have explicit preservation/reporting outcomes.
- Source-mode schema editing errors are understandable; plugin-disabled and narrow-screen album views remain useful; client refresh does not show stale cached schemas as current.
- Regression coverage checks old route syntax, JSON consumers, the normal documentation gate, plugin build/tests, and exact-SHA macOS CI if the Mac client changes.

## 8. Proposed glossary entries

These are proposed definitions for the requested future memory changes, not claims that the feature already exists. Publication should accompany the accepted implementation and use the SASE memory workflow.

### Album Note

A Bob vault Markdown file with frontmatter `type: "[[album]]"` that owns a named collection of [[record-note]] files and the schema used to capture and validate them. Its single `parent` names an [[area-note]] or [[project-note]], and that chain reaches an area. An album defines one record kind and one folder; the album note, record kind, and folder have distinct identities, as in `eat.md`, `restaurant`, and `eat/`.

The album is the collection's front door: it states its scope, shows a generated record summary, and offers views of its members. Its owner lists it under `## Albums`. It holds no tasks, has no project lifecycle, and is never a [[root-parent]]; ownership and root reporting pass through it to the area/project tree. Reparenting the album changes the collection's placement without moving its records. A notebook contains note bullets; an album contains a schema and an index of separate record files.

### Record Note

A Bob vault Markdown file for one durable thing tracked in an [[album-note]], such as one restaurant, podcast show, TV show, or movie. Its `type` names the album's declared record kind, such as `"[[restaurant]]"`; its single `parent` links to the album; and its metadata follows that album's schema. Its body holds notes about the thing, including dated observations where the schema enables them.

A record inherits its responsibility context through its album and the area/project parent chain. It is not a task, a Pomodoro, or a [[reference-note]] for source material. A record status such as `to_try` or `subscribed` describes the thing; it does not schedule work or enter task review. Commitments about a record live as tasks in an area/project and link to it. Capture uses the album's folder route: `@eat/` creates a restaurant record and `@eat/<stem>` updates one.

The Capture glossary's current “config-declared record type” wording must change alongside implementation, and the new terms should be linked from relevant existing entries. The Root Parent definition should preserve its current semantics; describe album transparency without redefining roots.

## 9. Evidence and limits

Repository locators below are pinned to the snapshot table above. Files were read from repositories opened through `sase repo`; no other researcher's output was used.

- **[C1]** bob-cli `docs/records.md`, `docs/reference/configuration.md`, `docs/reference/cli/records.md`: existing field language, route semantics, CLI, creation/update guarantees, scaffolding.
- **[C2]** bob-cli `src/native/records/plan.rs` (`resolve_parent`), `check.rs`, `schema.rs`, `init.rs`, `render.rs`: parent fallback, current lint limits, reserved identifiers, scaffold behavior.
- **[C3]** bob-cli `src/native/records/catalog.rs`, `capture_record.rs` (`record_policy_for_draft`), `capture_targets.rs`, and `capture_complete/{records,candidates,shell}.rs`: lazy reads and global config coupling. Existing suggestion code uses filesystem recency in some tie-breaking; that is not evidence of a real visit/listening date and should not be copied into overview semantics.
- **[C4]** bob-cli `src/native/pomodoro_homes/facts.rs` and `resolve.rs` (`resolve_note`): the Area/Project/Other distinction and ancestry/root computation.
- **[C5]** bob-cli `docs/notebooks.md`, `src/native/notebooks/{snapshot,catalog,region,txn,create,sync}.rs`: parent rules, owned callouts, partial-scan refusal, guarded inputs, and refresh design.
- **[V1]** vault `eat.md`, `podcast.md`, `podcasts.md`, `tv.md`, `movies.md`, the corresponding type notes, and the 152 records' frontmatter at revision `36213b799fab08927fdaf583d63a20eb9108a62a`; Python/YAML inventory and read-only `bob records check` summarized above.
- **[V2]** vault `job.md`, `legacy_job.md`, and the `job.md` diff in commit `fbab517019e2026b27342691f39840d85e5348d2`.
- **[V3]** vault `eat.base`, `podcasts.base`, `tv.base`, `movies.base`: existing named views, date formulas, customizations, and scalar metadata used for browsing.
- **[V4]** vault `eat.md`, `maybe_eat.md`, record `source_anchors`, and a broad read-only wikilink occurrence scan: duplicate anchors and cleanup scope. Regex occurrence counts are a risk estimate, not a semantic link resolver.
- **[P1]** bob-plugins `plugins/bob-ledger-tools/src/175-plugin-notebooks-api.js`, `241a-plugin-notebook-data.js`, `241b-plugin-notebook-catalog-model.js`, related catalog DOM/header fragments, and `styles.css` around the notebook catalog styles. These establish reusable patterns, not an already implemented album UI.
- **[M1]** Audited `sase memory read` of Obsidian conventions, Area Note, Project Note, Notebook, Reference Note, Root Parent, and `decisions:notebook-routes-write-notes`.
- **[M2]** Audited `cli_rules.md` and `docs.md`, plus the supplied core release-train and thin-client rules.
- **[O1]** [Obsidian Properties documentation](https://obsidian.md/help/properties): nested-property UI limitation and vault-wide property-name storage typing. Checked during this research.
- **[O2]** [Introduction to Bases](https://obsidian.md/help/bases): editable views over local Markdown properties.
- **[O3]** [Create a base](https://obsidian.md/help/bases/create-base) and [Views](https://obsidian.md/help/bases/views): embedding named views, grouping, sorting, filtering, and layouts.

The research did not verify the installed Obsidian version or render a visual prototype, inspect all Mac capture implementation paths, or prove every legacy prose fragment was already migrated. Those are bounded implementation-preflight tasks. Counts and observed defects are snapshot-specific. The feature's ownership, schema authority, and writer behavior can be settled now without pretending those checks are complete.

## Recommended solution

**Adopt albums as typed, schema-owning collection notes, with records parented to albums and albums parented directly to areas/projects.** Keep the existing domain record types and capture routes. Move all four configured schemas into album frontmatter; use the shared records engine and existing root resolver rather than create a parallel hierarchy.

Promote `eat.md → body`, `podcasts.md → dev`, and the TV/movie collections under `fun`. Preserve `podcast.md` as the type note. Give each album a compact, deterministic overview plus its existing native Base, and give each owner a restrained `## Albums` catalog. Keep daily task workflows separate from collections of possibilities.

Make migration conservative about identity and ambitious about the front door: retain legacy content and ambiguous anchors, declare the real `companions` field, stop presenting source dates as visits, and remove obsolete Zorg presentation only after preservation is verified. Ship the ownership and data contract first with the portable views; add client styling through the established notebook patterns. This makes the feature intuitive because there is one owner, reliable because there is one schema authority, and beautiful because each screen answers a small, useful question.
