# SASE blog drafting in record notes: album-per-blog appraisal

Researcher: mus (independent swarm report, suffix `__mus`).
Question: should each SASE-blog section/topic become a record note under a new
`~/bob/sase_blog_zettel.md` album, so the blog is later "mostly re-arranging"
finished records?

Short answer: the mechanism works, but it is the wrong tool for this job.
Do not create a `sase_blog_zettel` record album. Keep
`~/bob/sase_blog_contents.md` as the outline/manuscript spine with the existing
`sase_blog` project tasks for status, and add one **notebook**
`~/bob/sase_blog_zettel.md` (parent `[[sase_blog]]`) as the capture inbox for
per-topic material. Promote finished prose into per-topic plain draft notes only
if the outline stabilizes enough to need them, and assemble with Obsidian
embeds (`![[...]]`) in narrative order.

## Sources inspected (this session)

- Vault: `~/bob/sase_blog_contents.md` (outline, `parent: "[[sase_blog]]"`,
  `type: "[[article]]"`), `~/bob/sase_blog.md` (project note, `root: true`,
  Wave/zero-draft task tree, `## Requirements`), `~/bob/sase_blog_blockers.md`,
  `~/bob/sase_blog_0_legacy_notes.md`, `~/bob/sase.md` (area/project chain),
  `~/bob/eat.md` + `~/bob/eat/1_walnut.md` (canonical album + record),
  `~/bob/tv.md` (second album example).
- Beads (audited reads): `bob-cli-k3` (album notes epic, IN_PROGRESS; children
  k3.1–k3.11, album cards/catalogs/indexes), `bob-cli-ir` (record notes epic,
  CLOSED; capture grammar, `bob records`, Mac Record Card).
- Contracts: `docs/records.md` (albums, schema, planner, capture, `bob records`,
  `bob albums`), `docs/reference/cli/records.md`, `docs/reference/vault-format.md`
  (album/record rows, folder ownership), `docs/notebooks.md` + `docs/capture.md`
  (notebook routes), `sase/repos/research/202611/record_notes_capture_ux.md`.
- Memory (via `sase memory read`): `obsidian.md`, `docs.md`,
  `glossary:area-note`, `glossary:project-note`, `glossary:notebook`.
  `glossary:album-note` / `glossary:record-note` do not resolve yet (k3.11
  authorized them but they are not in this checkout), so the contract source is
  `docs/records.md`, not memory.
- SASE repo (opened via `sase repo open gh:sase-org/sase`): `docs/blog/posts/*.md`
  frontmatter (`title`, `date`, `draft`, `description`, `categories`, `slug`,
  `links`) and body shape.

## How the proposed mechanism actually works

An **album** is a vault-root note with `type: "[[album]]"` whose stem owns one
folder and one capture route (`eat.md` owns `eat/` and `@eat/`). It holds the
record schema in frontmatter under `record:` (`noun`, `label`, `plural`,
`fields`, plus `index_by`/`index_facets`/`summary`/`emoji`). Its `parent` must
be exactly one quoted `"[[stem]]"` resolving to an area or project, with the
chain reaching a Root Parent and no cycles. Each owner area/project then carries
a bob-owned `## Albums` catalog (`[!albums]` callout, stable rows
`> - <emoji> **[[stem|Title]]** — <summary>`); each album carries a bob-owned
`[!records]` index (tally title, rows `[[<album>/<stem>|<title>]]`, grouped by
`status` choices when present, otherwise first choices field). `bob albums
create PARENT STEM -n NOUN -s SUMMARY` writes album + starter `<stem>.base` +
owner catalog rows in one guarded write and one scoped commit; `bob albums sync`
repairs indexes/catalogs from one snapshot; `bob albums update STEM -i
envelope.json` applies ordered ops against the `expect` fingerprint with inverse
ops for undo. A broken album fails only its own route.

A **record** is one durable thing: `type: "[[record]]"`,
`parent: "[[<album>]]"`, `record.noun` naming the kind, `title`, schema fields
in order, `created`, then `# Title` + `## Notes`. Example (`eat/1_walnut.md`):
`status: not_liked`, `category`, `location` (wikilink), plus `lid`,
`source_*` legacy keys. Filename stem is derived from the title (NFKD, `&` to
`and`, apostrophes dropped, other runs to `_`, lowercased); collisions are
**refused, never suffixed**. `bob records new TYPE TITLE` and capture
(`Title @eat/` + `key:: value` bullets + free note bullets; `@eat/<stem>` to
append; `@eat/^stem` for explicit stem) run through the same planner: all or
nothing, required fields enforced, duplicates refused, album index rebuilt in
the same transaction. `dated_notes: true` stamps each first-level note bullet;
an ALL-CAPS first-level bullet with children becomes a `## Section`.
`bob records check` lints membership, types, legacy keys, checkboxes, and
off-folder filing.

Concretely the proposal means: `bob albums create sase_blog sase_blog_zettel
-n <noun> -s '<one line>'`, pick a noun (e.g. `zettel`, `section`, `topic`),
declare fields (e.g. `status` choices, `outline_ref`, `claim`, `proof`, `lesson`
or similar), then `bob records new <noun> '<Section title>' ...` or
`Title @sase_blog_zettel/` per outline node, one file each under
`sase_blog_zettel/`, with the album index grouping them by the choice field.

## Critique: why records fight this draft

1. **Collections are flat and grouped; the blog is ordered and hierarchical.**
   The outline is `1 → 2 → 2.1 → 2.2 → 2.3 …` narrative order with nesting.
   The `## Records` index groups by `status`/first-choices field with peeks,
   not narrative order, and bob owns those bytes. There is no supported
   "arrange records into blog order" view; re-arranging still happens by hand
   in an editor, except now the source is N files plus a generated index that
   cannot express the order. Obsidian embeds in `sase_blog_contents.md` express
   order directly; the album index never will.
2. **Identity is stable; the outline is explicitly unstable.** The prompt says
   the outline will change. Records assume one durable entity per note with a
   filename derived from its title and collision refusal. Section renames,
   splits (`2.3 → 2.3.1 + 2.3.2`), merges, and re-parenting are the expected
   operations of an unstable outline, and each is friction under records
   (new file vs rename, stem collisions, `record_parent_mismatch`/
   `record_outside_album` lint while mid-move, index churn). Plain notes and
   notebook bullets absorb this with zero schema cost.
3. **Schema buys almost nothing for single-use prose.** Typed fields
   (`status`, `category`, `location` on restaurants) pay off across hundreds of
   comparable entities queried in Bases (`eat.base` formulas over `status`,
   `category`, `location`, `visited`). Blog sections are ~10 nodes, written once
   each, shipped once to `docs/blog/posts/`. The plausible fields
   (`status`, `outline_ref`, `word_count`, `proof_asset`) are either already
   tracked better elsewhere (status lives on the `sase_blog` zero-draft tasks
   with `fresh`/`dependsOn`/stamps) or are free text that lint cannot validate
   (claims, lessons, quotes). The strongest record features — choice
   validation, `suggest`, Bases formulas, `Similar records` dedup — have no
   meaningful blog-section workload: duplicate-section detection across ~10
   hand-curated headings is not a capture problem.
4. **The export gap is total.** The ship target is SASE `docs/blog/posts/*.md`
   frontmatter (`title/date/draft/description/categories/slug/links`) plus
   long-form Markdown with `<!-- more -->`, cross-links, and images. Record
   frontmatter (`parent/type/title/<schema fields>/created`) shares only
   `title`. No exporter exists; the "simplified to re-arranging" step is
   actually copy-paste plus frontmatter rewrite per record, identical to
   copying from plain draft notes but with YAML noise (`status:`, `created:`)
   to strip. Notebook bullets and plain notes have the same copy step with
   less to strip.
5. **Two statuses, two outlines, one confusion.** `sase_blog.md` already runs
   the draft as tasks (`s0-spike`, `zd-cli`, `zd-gates`, `zd-macros`,
   `w1-review`, `v1-draft`, each with INPUT/EXIT/STOP and CARD lines) and
   `sase_blog_contents.md` already holds the headings. A parallel record
   `status` field (or record-per-task mirror) creates a second status to keep
   in sync with `[?] / [/] / [x]` + `fresh::` + `dependsOn`, with no reconciler
   between them. The task lane is the right tracker (dependencies, scheduling,
   Ready caps, decay); records add a shadow tracker.
6. **Generated-section ownership cuts against drafting.** Both the album's
   `[!records]` and the owner's `[!albums]` regions are bob-owned; hand edits
   there are overwritten by the next `sync`. Draft tooling that rewrites the
   album note (every `records new`) also rewrites the index in the same
   transaction, so the album note is a hot file under concurrent capture +
   Mac + nightly sync. Draft prose deserves cold, hand-owned files.
   Additionally the owner (`sase_blog` project, or `sase`) gains a bob-owned
   `## Albums` catalog section for exactly one album — pure overhead.
7. **Naming/placement constraints with no benefit.** The album must live at
   the vault root (`sase_blog_zettel.md` qualifies), stem lower-case route,
   noun `[a-z][a-z0-9_]*`, non-reserved (`album`, `record`, `article`, `day`,
   `done`, `ref`, `project`, `area`, `notebook`, `mail`, `type` excluded).
   `sase_blog_zettel` is a legal stem and `zettel`/`section`/`topic` are legal
   nouns, so the proposal is *buildable* — but compliance buys capture routing
   (`@sase_blog_zettel/`) and Bases that the draft does not need, while
   permanently reserving that route and folder.
8. **Long prose is second-class in both records and notebooks.**
   `## Notes` bullets with `dated_notes` stamping suit dated observations
   ("Spicy tuna was great"), not 150-word zero-drafts with headings, quotes,
   image embeds (`img/20260802_144938.png`), and `NEXT` lines. ALL-CAPS
   section seeding helps only for short titled sections. A 150+ word dictated
   section under a `## Notes` bullet is possible but ergonomically worse than a
   plain note body, and worse for the later paste into the SASE post.

None of this impugns records: restaurants/podcasts/TV/movies are the shape
records are for (many durable entities, stable nouns, comparable fields,
query/display in Bases, dedup at capture). Blog sections are the opposite
shape (few, unstable, hierarchical, ordered, prose-heavy, single shipment).

## Alternatives weighed

- **(A) Notebook inbox (part of recommendation).** One
  `sase_blog_zettel.md` with `type: "[[notebook]]"`, `parent: "[[sase_blog]]"`,
  one-line `summary`, H1, and `##` sections mirroring the current outline.
  Capture via `@sase_blog_zettel` / `@sase_blog_zettel#Section` /
  `@sase_blog_zettel^id` / draft-wide `@@sase_blog_zettel`; sections created on
  demand; notes append after the last note; `bob notebooks sync` maintains the
  `## Notebooks` catalog on `sase_blog`. No schema, no fingerprint envelopes,
  no index rebuilds, no filename derivation (note bullets carry `^id`s),
  outline renames are heading edits. Best capture ergonomics of any option;
  prose still lives in bullets, so promote to (B) when a section exceeds
  bullet scale.
- **(B) Plain draft children + embed spine (part of recommendation).**
  One vault-root note per matured section with `parent: "[[sase_blog]]"` (e.g.
  `sase_blog_gates.md`, or keep everything in `sase_blog_contents.md` until a
  section earns its own file), assembled in narrative order with
  `![[sase_blog_gates]]` embeds in `sase_blog_contents.md`. Re-ordering is
  re-ordering embed lines — the literal "mostly re-arranging" operation, with
  zero generated sections and zero export impedance beyond the unavoidable
  SASE-frontmatter rewrite. Renames/splits/merges are file ops.
- **(C) Status quo (viable fallback).** Keep drafting in
  `sase_blog_contents.md` headings + `sase_blog.md` Wave tasks only. The S0
  exit criteria (promise sentence, four Wave-1 cards, one claim sentence per
  heading, `bob ready sase_blog` ≤ 5) already define done without any new note
  kind. Add nothing until a concrete pain (e.g. contents note too large, or
  capture volume justifies an inbox) appears.
- **(D) Record album (not recommended; specified only so it can be refused
  cleanly).** If built anyway: noun `section`, label `Section`, minimal fields
  (`status` choices `zero_draft/wave1_ready/v1/shipped`, optional `outline_ref`
  text, optional `proof` text, optional `lesson` text; no required fields
  beyond `status` so capture never blocks prose), `index_by: status`,
  `dated_notes: false` (dated bullets actively harm draft prose),
  `parent: "[[sase_blog]]"`. Expect to pay: fingerprint-envelope schema edits
  on every outline change, collision-refusal renames, shadow status sync with
  `sase_blog` tasks, hand-owned `## Records`-adjacent prose discipline, and a
  manual SASE-frontmatter export.

## Adjustments to the stated requirements

1. `sase_blog_zettel.md` should exist — but as a **notebook**, not an album.
   Drop `record:` schema, `noun`, `index_by`, `## Records` index, and `.base`
   expectations entirely.
2. Drop "one record per topic" as the unit of completion. The unit of
   completion stays what `sase_blog.md` already says: the zero-draft task per
   section (150 words, `NEXT` line) and the Wave gates. Records would
   duplicate that tracker.
3. Keep `sase_blog_contents.md` as the single outline spine (it already has
   `parent: "[[sase_blog]]"` and full heading structure). Do not fork the
   outline into N record titles; unstable outlines must live in one file until
   they stabilize.
4. If per-section files are wanted later, make them plain `parent:
   "[[sase_blog]]"` draft notes assembled by embeds, not records. Revisit
   records only if sections ever need queryable typed fields across dozens of
   comparable entities — which a one-shot blog post will not produce.

## Recommended solution

1. Create `~/bob/sase_blog_zettel.md` as a notebook (hand-owned prose, no
   schema):
   `parent: "[[sase_blog]]"`, `type: "[[notebook]]"`, one-line `summary:`
   (e.g. `Raw per-topic material for the SASE post, captured before drafting.`),
   H1 `# SASE blog zettel`, and one `##` section per current
   `sase_blog_contents.md` heading (Gates, Beads/Sidecars, Agent CLIs,
   presentation, VCS/workspaces, Xprompts, Project mgmt, Routines/Jobs, Why-not,
   Future work, Conclusion). Run `bob notebooks sync` so `sase_blog`'s
   `## Notebooks` catalog picks it up.
2. Capture raw material with notebook routes (`Topic @sase_blog_zettel#Gates`,
   draft-wide `@@sase_blog_zettel` for unrouted items). Keep bullets short;
   put quotes, links (`~/tmp/screenshots/*.png`, `img/20260802_*`), and QUOTE
   placeholders as nested detail under the bullet with `[created::]` stamps.
3. Draft in place where the outline lives: one claim sentence per heading in
   `sase_blog_contents.md` first (S0 exit), then zero-drafts per the existing
   `zd-*` tasks. Promote a section to its own `sase_blog_<slug>.md` draft note
   (`parent: "[[sase_blog]]"`) only when it outgrows the contents file; embed
   it back (`![[sase_blog_<slug>]]`) at the owning heading so the spine always
   reads in narrative order.
4. Track status only on `sase_blog.md` tasks (`fresh`, `dependsOn`, Wave
   gates). Do not mirror status into note frontmatter.
5. Ship by copying the stabilized spine sections into a new
   `docs/blog/posts/*.md` in the SASE checkout with the post frontmatter
   (`title/date/draft/description/categories/slug/links`), `<!-- more -->`,
   and SASE-side cross-links — one mechanical pass, no YAML surgery per
   record.
6. Explicit non-goals: no `bob albums create`, no `record:` schema, no
   `sase_blog_zettel/` folder, no `.base`, no `bob records` involvement, no
   `## Albums` catalog on `sase_blog`.

Why this wins: capture stays one keystroke (`@sase_blog_zettel#Section`),
order lives in hand-owned embed lines that directly support "re-arranging,"
renames/splits/merges cost a heading or file op, there is exactly one status
tracker (the existing tasks), and the export step is identical to the records
plan minus per-record YAML stripping. If Bryan still wants per-topic query
views later, the notebook sections promote cleanly into plain draft notes;
nothing about this path forecloses records — it just refuses to pay for them
before they earn their keep.

