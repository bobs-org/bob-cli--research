# Renaming the `[[article]]` note type: name choice, critique, and implementation plan

Research report (swarm member `mus`). Question: rename the "article"
Obsidian note file type to something generic, since it will hold any prose;
tentative name "prose"; sections will implicitly use the type so a keymap can
promote a section to a full note; this is a stepping stone to lossless
task/project reversibility.

**Verdict up front: yes, do the rename; "prose" is the best name despite one
real grammatical wart; ship it as an alias-first rename (read both, write
canonical), not a flag day; do not build a stored section-type system; treat
the rename as necessary but not sufficient for reversibility.**

## 1. What `[[article]]` is today

An article is a long-form vault note marked `type: "[[article]]"`. bob owns its
section numbering (`1.` / `1.1` / `1.1.1`) and layout; formatting never changes
a word. The engine lives in `src/native/articles/` (`mod.rs`, `marker.rs`,
`scan.rs`, `sections.rs`, `layout.rs`, `links.rs`, `plan.rs`, `render.rs`,
`vault.rs`, `inbound.rs`, `cli.rs`, plus `tests/` and fixtures). The contract
is documented in `docs/articles.md` (rules N1–N9, F1–F11, findings catalog,
word invariant, idempotency gate, vault scanning, CLI table, ArticlePlan v1
JSON). Verified behaviors that constrain any rename:

- **Marker semantics** (`marker.rs`): `skip_reason` refuses notes whose type
  names anything besides `article` (`mixed-type`), that hold `^prj`/`^ref`
  anchors (`holds-anchor`), task lines (`holds-tasks`), or live under excluded
  dirs. `adopt` inserts `type: "[[article]]"` after `parent:` (or a fresh block)
  and no-ops on already-adopted notes. The refusal *codes* (`not-article`,
  `mixed-type`, `holds-tasks`, …) are user-visible and appear in JSON output.
- **Taxonomy position**: `frontmatter_is_article` (`src/native/projects/scan.rs:364`)
  is one peer among `project` / `area` / `notebook` / `album` / `record`; the
  plugin-side parent picker (`208-parent-note-picker-model.js`) lists
  `"article"` in `PARENT_RULE_NON_RECORD_TYPES` next to `mail`/`day`/`done`.
  The records schema reserves `"article"` as a record id
  (`src/native/records/schema.rs:15,19`).
- **Consumers of the type**: capture section targeting treats article notes
  specially (`destination_is_article`, identity-based heading match in
  `src/native/capture/sections.rs`); shell completion has an `ArticleNote`
  kind (`src/native/completion/`); URL routing maps `RouteHint::Article` to the
  display string `"article"` (`src/native/url_routing/intent.rs:30`);
  `bob-articles` Obsidian plugin shells out to
  `bob articles <action> --stdin <path> -f json`, parses `schema_version: 1`,
  checks `type: [[article]]` itself (`articleHasArticleType` in
  `020-article-core.js`), and styles with `.bob-article*` CSS classes.
- **Vault footprint is small**: today only 4 vault files carry `[[article]]`
  (`sase_blog_contents.md`, `_templates/new_article.md`, `AGENTS.md`, one
  ref-source). No file uses `[[prose]]`; no `prose.md` stem exists. Migration
  risk in the live vault is low — the risk is all in code, contracts, and
  muscle memory.

## 2. Critical scoping finding: "article" means four different things

A blind grep-rename of the string `article` would corrupt three unrelated
systems. The four meanings, each with its keeper:

1. **Note type** (`type: [[article]]`, `bob articles`, `ArticlePlan`,
   `frontmatter_is_article`, `.bob-article`). — **Rename this.**
2. **Web-capture source kind** (`"kind":"article"` in `bob ref` spool JSON,
   `route_hint: "article"`, `Self::Article` in `highlights_ref/ingest.rs`,
   `default_ref_type_for_kind("article", …)`). Means "the ingested URL is a
   web article". — **Do not touch.** It correctly describes web articles and
   feeds ref-type defaults and Mac Capture ref kinds.
3. **HTML `<article>` element** (`gmail/body/html.rs`, `podcast/notes.rs`,
   `clip_url.rs` path segments `"article"/"articles"`). Markup vocabulary. —
   **Do not touch.**
4. **English word in docs/comments** ("never changes prose", "a bare `==`
   run followed by prose stays prose", "Papers, articles, and docs show…").
   — **Touch only where it names the type.**

Consequences: the rename must be a *semantic* rename done by hand per call
site, never `sed s/article/prose/`. Mac Capture is **unaffected** — every
`article` hit there (`RefsModel.article`, `.articles` scope, ranking keywords)
is meaning 2 (reference kind), confirmed by direct grep of `Sources/`. The
`bob-articles` plugin and `bob-cli` own essentially the whole blast radius.

A second collision to record: `prose` already means "body text" throughout
`src/` and `docs/` ("stays prose", "ordinary prose", "Imported prose", "prose
field" in the plugins repo: `test-prose-field-roles.cjs`,
`record-card-prose-field`, `intention-card-prose-field`). Adopting `[[prose]]`
overloads that word. I judge this benign — a prose note is a note whose body
*is* prose, so the two senses point the same direction — but the plan must
budget doc/comment disambiguation (see §6).

## 3. Name candidates

Requirements derived from the request and the codebase: (a) names the
membership rule "file whose body is prose"; (b) works as `type: [[X]]`, CLI
noun `bob X …`, plugin id, CSS class, JSON contract name; (c) countable or at
least comfortable in "convert this section into a full X"; (d) no collision
with existing type names (`project area ref day done mail notebook album
record type`), task tags, capture sigils, or high-frequency Rust identifiers;
(e) reads naturally for the section-promotion keymap ("X section").

| Candidate | Countable? | Collisions | CLI / copy reads | Verdict |
| --- | --- | --- | --- | --- |
| `prose` (proposed) | No — mass noun ("a prose" is ungrammatical) | **None as an identifier** (zero hits in `src/` outside comments); mild word-sense overlap with "body text" | `bob prose list` fine; "prose section" good; countable contexts use "prose note" (which the request already does) | **Recommend** |
| `note` | Perfect ("a note") | **Fatal**: every typed note is a note; collides with `resolve_note`, `NOTE` args, `is_markdown_file`, `parentRuleKindOf` vocabulary; `[[note]]` inside a note is self-referential mush | `bob notes` swallows the namespace | Reject |
| `document` / `doc` | Yes | Collides with `docs/` dir, docs tooling, "documentation" in every help text; `bob docs` ambiguity | Confusing | Reject |
| `page` | Yes | Obsidian renders every note as a page; collides with highlights `page_words`, ref page vocabulary | Misleading | Reject |
| `text` | Barely ("a text" is tech-jargon) | **Fatal in code**: `text` is the single most common parameter name (`text_is_article`, `format(text, …)`); rename churn enormous | Poor | Reject |
| `sheet` | Yes | Taken: command sheet, capture sheet, run sheet | Taken | Reject |
| `card` | Yes | Taken: card family (property/record/intention cards) | Taken | Reject |
| `entry` | Yes ("an entry") | Moderate: `DirEntry`/fs vocabulary; journal/diary flavor pulls toward day notes | `bob entries` OK | Runner-up |
| `piece` ("a piece of writing") | Yes | None found | "piece section" awkward; slightly literary | Second runner-up |
| `passage` | Yes | Mild: ref/highlights "passages" (excerpts) suggest *part*, not *whole* | Backwards connotation | Reject |
| `essay` / `memo` / `treatise` / `folio` / `scroll` / `longform` | Varies | None, but each narrows register (argumentative / workplace-short / archaic / cute / jargon) | The type must cover meeting notes and journals, not just essays | Reject |

Why `prose` wins despite the mass-noun wart: it is the only candidate that
simultaneously (i) names the actual membership rule the user stated ("any file
that needs to contain prose"), (ii) has zero identifier collisions so the
Rust rename is mechanical (`frontmatter_is_article` →
`frontmatter_is_prose`, `text_is_article` → `text_is_prose`, `ArticlePlan` →
`ProsePlan`, `ArticleStatus`, `adopt_notice`, completion `ArticleNote` →
`ProseNote`), and (iii) already appears attributively in the request itself
("prose sections", "a full-blown 'prose' note"). The wart is handled by a
copy convention: the type token is `[[prose]]`, but all countable
user-facing copy says **"prose note"** ("convert section to prose note",
"3 prose notes need formatting"). `bob prose <verb>` never needs a plural
because the subcommand carries the verb (`list`, `format`, `adopt`,
`outline`) — same shape as `bob ref`, which is also a mass noun and reads
fine.

`entry` is the honest runner-up and the right fallback if Bryan hates the
uncountable noun: `bob entries`, "an entry", no type-namespace collision. Its
costs are the fs-vocabulary noise and a diary flavor that will mislead on
meeting notes. `piece` stays in the pocket only if both fail.

Rejected alternative worth one line: keep `[[article]]` and just document it
as "our generic prose type". Zero cost, but it cements the wrong mental model
exactly where the new features (implicit section typing, reversibility) need
the right one, and "article section" will read as "published piece" forever.
Also rejected: a two-tier taxonomy (`prose` supertype + `article` subtype for
publishable pieces with `title:`). It buys nothing today — the engine treats
them identically — and doubles the marker/mixed-type logic. Revisit only when
a real publication feature (not just `title:`) exists.

## 4. Critique of the plan

**The rename is a good idea, and now is the cheapest time.** The vault
footprint is 4 files; the plugin contract is versioned (`schema_version: 1`,
`ARTICLE_PLAN_SCHEMA_VERSION = 1`), so a coordinated bump is tractable; and
doing it *before* building section-extraction and reversibility avoids baking
`article` into two more features' vocabulary. Delay raises the price roughly
linearly with each feature shipped on top.

**Adjustments I would make to the requirements:**

1. **Alias-first, not flag-day.** Per `cli_rules` (never hard-rename a
   command: old spelling becomes a permanent hidden alias, byte-identical)
   and the gotchas (CLI/JSON breaks marked `!`, no release PR, daily train):
   `bob articles …` must survive as a hidden alias; the frontmatter reader
   must accept `[[article]]` indefinitely (or for a stated sunset) while the
   writer emits `[[prose]]`. Vaults, templates, and muscle memory contain
   `[[article]]`; a flag day strands them. Read-both/write-canonical is the
   only safe shape, and it needs a stated end-of-life for the alias or it
   becomes permanent tech debt — I recommend *permanent read support* (cheap:
   one predicate) with the write path canonicalizing on next `format -w`.
2. **Bump, don't silently reshape, the JSON contract.** `ArticlePlanResponse`
   carries `schema_version: 1` and a `notes`/`articles` count field
   (`plan.rs:163-196`); the plugin hard-checks the version
   (`020-article-core.js:86`). Renaming JSON keys under version 1 would
   silently break older `bob-articles` installs. Ship the renamed shape as
   `schema_version: 2` (or keep key names stable under v1 and rename only in
   v2 — decision for the plan author, but it must be explicit and `!`-marked).
3. **Do not build stored section types.** "Sections implicitly use this type"
   should mean: *extraction targets prose semantics*, not *each section gets a
   persisted type tag*. Sections already have identity rules shared with
   capture (`heading_identity`). A persisted per-section type would need a
   storage format (HTML comments? block ids?), conflict with the word
   invariant, and duplicate the heading-identity machinery. The keymap feature
   wants one command — `bob prose extract NOTE#Section` (name TBD) — that
   reuses `adopt` + `format` + inbound-link repair. No schema change to
   sections at all.
4. **Rename ≠ reversibility.** The prose type gives task/project demotion a
   honest target, but lossless reversibility needs three more mechanisms that
   are independent of the name: (a) `^prj` anchor add/remove with catalog
   repair (today `holds-anchor` is a hard refusal — that refusal *is* the
   reversibility gap); (b) project children/catalog preservation across
   demotion (Sub-projects markers, parent links); (c) task-checkbox ↔ prose
   paragraph round-trip rules. Sequence the work: rename → extract → anchor
   add/remove → demotion/promotion. Do not promise reversibility in the rename
   release.
5. **The `mixed-type` rule gets more valuable, not less.** Genericizing the
   type will tempt `type: [[prose]]` + `[[project]]` combos ("a project with
   prose"). Keep the refusal: a note is either bob-numbered prose or it isn't.
   If project-child prose notes need project linkage, that travels in
   `parent:`, not `type:` — which is already the shape
   (`sase_blog_contents.md` carries both `parent:` and `type:`).

## 5. Implementation blueprint (for the plan author)

Phase 0 — audit (one pass, no behavior change): enumerate every meaning-1
call site: `src/native/articles/**`, `frontmatter_is_article`,
`destination_is_article`, completion kinds/providers/tree, `url_routing`
display string, `records/schema.rs` reserved ids, `docs/articles.md`,
`docs/reference/cli/articles.md`, `docs/_meta/contracts.yml`,
`docs/reference/json-outputs.md`, `docs/develop/contracts.md`, plugin
`bob-articles` (id, dir, manifest, `main.js` bundle, `.bob-article*` CSS,
subprocess argv `["articles", …]`, `ARTICLE_PLAN_SCHEMA_VERSION`,
`articleHasArticleType`, `docs/bob-articles.md`, `test-bob-articles.cjs`),
`PARENT_RULE_NON_RECORD_TYPES`, vault `_templates/new_article.md`, vault
`AGENTS.md` mention. Explicitly exclude meaning-2/3 sites (ref spool kinds,
HTML tag matchers, URL slugs) with a per-site comment so the next grepper
knows they were considered.

Phase 1 — engine alias (bob-cli, `!`-marked): predicate accepts
`article|prose`, canonical name `prose`; `TYPE_LINE` writes
`type: "[[prose]]"`; `adopt` on an `[[article]]` note normalizes the marker
(decide: Changed with marker-only edit, or silent — recommend Changed, it
is a write); `format -a` discovers both; refusal codes: keep wire codes
stable *or* rename with schema bump — no silent third option; `bob articles`
kept as hidden alias per `cli_rules`; JSON `schema_version: 2` for renamed
keys. Update `RESERVED_RECORD_IDS` (add `prose`; keep `article` reserved while
the alias reads it), `PARENT_RULE_NON_RECORD_TYPES` equivalent on the Rust
side if any, completion strings, help text (alphabetical per `cli_rules`).

Phase 2 — plugin + vault + docs: rename plugin dir/id to `bob-prose`
(coordinated with bob-cli 2; plugin must accept both schema versions during
rollout or pin minimum bob version), CSS classes (keep `.bob-article` as
compat shim or cut over — Obsidian caches styles, so a shim release is
safer), template `new_article.md` → `new_prose.md` (keep old template? vault
templates are user files — add new, leave old, note in changelog), vault
`AGENTS.md` + the 3 live `[[article]]` notes canonicalized, `docs/articles.md`
→ `docs/prose.md` with redirect note (mkdocs nav — check `mkdocs.yml` + read
`cli_rules`/`docs.md` memory first per repo rules), contract metadata updates.

Phase 3 — validation: full `just check` (or repo's configured gate) plus the
plugin's `test-bob-articles.cjs` suite; manual matrix: adopt/format/list on
`[[article]]` notes, `[[prose]]` notes, mixed, and alias-spelled CLI; old
plugin + new bob and new plugin + old bob (one must degrade gracefully —
state which in the release notes).

Phase 4 (separate release) — `extract`: `bob prose extract NOTE#Section`
reusing adopt/format/inbound repair; renumbering falls out of bob-owned
tokens (extracted `1.1.3 …` becomes `1 …`); inbound heading links to the moved
section repaired like a rename. Keymap binds to it. No section schema.

## 6. Recommended solution

1. **Name: `prose`.** Type token `type: "[[prose]]"`, CLI `bob prose …`
   (`bob articles …` permanent hidden alias), engine `ProsePlan`, plugin
   `bob-prose`, copy convention "prose note" everywhere countable.
   Fallback order if vetoed: `entry`, then `piece`.
2. **Shape: alias-first rename with JSON schema bump**, sequenced
   engine → plugin/vault/docs → extract, per §5. Mark the CLI/JSON break
   with `!`; never edit versions/changelog by hand (release train owns them).
3. **Explicitly out of scope for the rename:** ref-pipeline "article" kinds,
   HTML tag matchers, URL slugs, Mac Capture (verified unaffected), stored
   section types, and reversibility mechanics beyond naming the target.
4. **Reversibility follows as its own project** (extract → anchor add/remove
   → demotion/promotion), unblocked but not delivered by this rename.

## 7. Open questions for the plan author (not blockers for this report)

- Refusal-code stability: rename `not-article` → `not-prose` (clean, needs
  schema bump + plugin coordination) or keep wire codes forever (ugly,
  zero-risk)? I lean rename-with-bump since §5 already bumps.
- Does `adopt` on a legacy `[[article]]` note rewrite the marker to
  `[[prose]]` as a `Changed` plan, or treat it as already-canonical? (Lean:
  Changed — visible, auditable, one-time.)
- Sunset policy for `[[article]]` read support: permanent (my recommendation —
  one predicate, and old vault history/templates live forever) vs. dated.
- Who else consumes ArticlePlan JSON or `bob articles` argv? I audited
  bob-cli, bob-plugins, bob-mac-capture (clean), and the live vault. Anything
  outside those three repos plus the vault (scripts, cron, Raycast/Alfred
  shortcuts) needs one grep from Bryan's side.
