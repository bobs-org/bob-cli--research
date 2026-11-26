# Renaming `article` to `prose`: section extraction and the road to reversible projects

_Consolidated report, 2026-11-26. Merges five independent researcher reports (`cdx`,
`cld`, `grk`, `mus`, `gem` — siblings in this directory) plus the lead researcher's own
verification of every disputed claim against bob-cli (`4dd787bc`), bob-plugins
(current `master`), the live vault (`~/bob`), and the SASE decisions roster._

## TL;DR

**Rename the type to `prose`, and do it now.** All five researchers independently
evaluated 20–25 candidate names and all five arrived at `prose`; the lead review did not
find a better one either. The vault has exactly **one** live `type: "[[article]]"` note
(`sase_blog_contents.md`) plus one template and the type note, no `bob-articles` hotkeys
and no plugin `data.json`, so the rename will never be cheaper. "Article" also actively
collides with the web-article sense used by `bob ref` ingestion, `~/bob/articles.md`,
and Bob Mac Capture's Refs kinds.

**The product is not the rename — it is the capability.** "Sections implicitly use this
type" must mean *derived eligibility for extraction* (and heading identity), never
in-place formatting of project/area notes and never a stored section type. Ship
extraction **with its inverse** (`bob prose extract` / `bob prose inline`) as a
Rust-owned, preimage-guarded, link-repairing planner in bob-cli, with the Obsidian
plugin as a thin keymap client.

**The rename is necessary but far from sufficient for reversible projects.** Verified in
code and the live vault: project → task reversal today refuses for reasons prose cannot
fix — `###` status-group headings inside `## Tasks` (written by task reconcile and
present in real project notes), generated `[!notebooks]`/`[!albums]` catalogs (only
`[!projects]` is skipped), any child note of any kind, and req/subtask asymmetry. Prose
extraction unblocks exactly the prose-child and prose-section class; the other blockers
are separate fixes. Plan and promise accordingly.

---

## 1. Current state (verified)

Facts below were reported by two or more researchers and re-verified by the lead where
disputed or load-bearing. Paths are repo-relative; bob-cli at `4dd787bc`.

### 1.1 The `article` type

- Marker: `type: "[[article]]"`; `frontmatter_is_article` (`src/native/projects/scan.rs:364`);
  engine in `src/native/articles/` (~14 files). Contract in `docs/articles.md`:
  numbering rules N1–N9, layout F1–F11, heading-link and inbound-link repair, word-token
  invariant, preimage-checked atomic writes.
- Refusals already define the type by **ownership**: `mixed-type`, `holds-anchor`
  ("articles cannot be projects or refs"), `holds-tasks`, `conflict-markers`. A body the
  author owns, where bob formats but never adds structure.
- `section_numbers` defaults to **`true`** (`marker.rs:250`; `docs/articles.md:16`).
  N6 claims one leading `\d{1,3}\.`-shaped token as bob-owned; the documented known risk
  is that an unescaped `## 1.5 million users` is rewritten (N7 escape exists). N9:
  numbering-off removes owned tokens and is idempotent.
- JSON: `ArticlePlan` `schema_version: 1`; **"The contract only grows; clients must
  reject an unknown `schema_version`"** (`docs/articles.md:229`). `summary.articles` is
  a wire key (`plan.rs:171`). The only client is the `bob-articles` plugin, which
  hard-checks the version and never parses article grammar.
- Other consumers: capture section targeting uses de-numbered heading identity
  (`src/native/capture/sections.rs`), completion kind `ArticleNote`, catalog slots
  (`article-note`, `articles-list`/`articles-outline`), nightly `format -a -c`,
  reserved record id `article` (`src/native/records/schema.rs`),
  `PARENT_RULE_NON_RECORD_TYPES` in the nav plugin's parent picker.
- Gaps: `docs/reference/vault-format.md` omits the article type entirely (verified: zero
  hits); there is no glossary term for it.

### 1.2 Vault footprint and the name collision

- `[[article]]` appears in exactly: `sase_blog_contents.md` (the one live note, child of
  project `sase_blog`), `_templates/new_article.md`, `AGENTS.md:15`, and write-once
  `.bob/ref-sources` history (leave those alone). Type note `article.md`,
  `articles.base`, `type.md` embed complete the set. No hotkeys bind `bob-articles:*`
  commands; the plugin has no `data.json`.
- "Article" means **four different things** across the repos (mus): (1) the note type —
  rename this; (2) the web-capture/ref kind (`RouteHint::Article`, `kind: "article"`,
  ~200 hits in `highlights_ref`, all of Mac Capture's hits) — keep, it correctly
  describes web articles; (3) the HTML `<article>` element — keep; (4) the ordinary
  English word — touch only where it names the type. **The rename must be semantic,
  per-site; never `sed s/article/prose/`.** Mac Capture is verified unaffected.
- Scale context: roughly 100 projects, 200+ records, ~40 notebooks, ~1400 refs — and
  1 article. The type failed to spread under its current name while prose kept landing
  in untyped root files (`why_sase.md`) and inside project sections.

### 1.3 Project ⇄ task conversion today

- Forward (task → project) is lossless for drawers: `- **Title**` ↔ `## Title` byte for
  byte (`decisions:drawers-keep-their-names`, `docs/projects.md`).
- Reversal refuses in three coded situations (bob-plugins, `bob-navigation-hotkeys`):
  any child note (`665-plugin-project-conversion.js:63` — kind-blind, via `parent:`),
  non-list section content (`210-rename-and-line-context.js:698`), and content outside
  the `^prj` task and its sections (`210-...:744`).
- **Lead-verified pre-existing blockers beyond prose** (gem's finding, confirmed in
  code and vault):
  - `PROJECT_SECTION_BOUNDARY_HEADER_RE = /^ {0,3}#{1,2}(?:[ \t]|$)/`
    (`010-requires-and-config.js:124`): only H1/H2 end a section, so the `###` status
    groups bob writes under `## Tasks` (`### Next & In Progress`, `### Blocked`,
    `### Done & Canceled`, from `src/native/task_status_groups/`) hit the
    "not a list item" refusal. Real project notes carry them today
    (`sase_size_models.md`, `sase_model.md`, `sase_memory_plan.md`, …).
  - `skipGeneratedProjectsCatalog` matches **only** the `[!projects]` callout head
    (`212-project-conversion.js:63–77`); `[!notebooks]` / `[!albums]` catalogs (present
    on `sase_blog.md`) refuse reversal.
  - Reversal emits `## Tasks` rows as nested `#task` subtasks while forward promotion
    turns reqs into tasks — the round trip is asymmetric
    (`decisions:task-reqs-are-met-with-their-task` governs the boundary).
  - Project-only frontmatter (`task_type`, `offclock`, `ready_cap`, `root: true`,
    `done_tasks:`) has no task-line representation and would be silently dropped.

### 1.4 Governing decisions

Consulted via the decisions roster. Directly governing: `drawers-keep-their-names`,
`notebook-routes-write-notes` (notebooks are bullet collections — prose is explicitly
pushed out of them by `notebook_shape`), `task-reqs-are-met-with-their-task`,
`capture-bullets-mirror-the-task-block`, `unblocked-tasks-are-offered` (consent for
surprising cross-note effects), `bob-cli-releases-ride-a-daily-train` (`!` for contract
breaks, no manual versions/changelog), `mac-capture-is-a-thin-client`,
`task-deps-are-depends-on-links`, `projects-block-from-prj-line`,
`subprojects-inherit-project-blocking`. No existing decision governs the article type's
name; nothing in the roster contradicts the rename.

---

## 2. Naming: `prose` wins, 5/5

Every researcher tried hard to beat `prose` (collectively ~25 candidates checked against
vault filenames, CLI nouns, glossary terms, and `bob ref` kinds) and every one landed on
it. The decisive tests:

1. **It names the actual membership rule** — "a file whose body is prose" — and it is
   already Bob's word for exactly this ("never changes prose", "stray top-level
   paragraph; keep prose in the preamble", "Bob-owned prose field").
2. **It is the only candidate that works at every scale the plan needs**: prose field
   (exists), **prose section** (the extraction unit), **prose note** (the file). The
   section phrase is the requirement most candidates fail.
3. **It names the structural contrast that organizes task-free content**: notebook =
   bullets, record = schema fields, prose = continuous writing.
4. **Zero identifier collisions** in `src/` and no user-facing vault collisions; the
   existing "body text" sense of the word points the same direction.

The one real cost: it is a mass noun. Copy convention handles it — always "**prose
note**" / "**prose section**" / "3 prose notes", never "a prose". `bob prose <verb>`
reads fine (`bob ref` and `bob mail` set the mass-noun precedent).

Runner-ups, for the record: **`page`** (grk, gem) is the strongest countable fallback —
clean, but every note is a page, and it collides with PDF-page vocabulary in refs;
**`document`/`doc`** (cdx, cld) is semantically broadest but collides three ways in this
ecosystem (`~/bob/docs.md`, repo `docs/`, the published docs site); **`entry`** (mus) is
countable but smells of diaries and `DirEntry`. Rejected classes: genre words
(essay/memo/post/draft/writeup — same narrowness problem as article), overloaded words
(note/text/section/sheet/card/leaf/copy), and ornate ones (folio/manuscript/longform).
Keeping `article` was costed and rejected: it cements the wrong mental model exactly
where sections and reversibility need the right one.

**Definition to record** (merging cdx's content definition with cld's ownership
definition): a **prose note** is a note whose body is free-form authored Markdown that
the author owns — paragraphs, headings, lists, tables, quotes, code — where bob may
format layout and (opt-in) numbering but never adds structure; it holds no `#task`
lines, no `^prj`/`^ref` anchors, and no mixed types. The distinction is **primary
role**: a project containing prose sections stays a project. Do not define it as "any
file that contains prose" — every area, project, and ref contains prose.

Keep "article" for the web-clip/ref kind (it is correct there) and for the plugin's
serif "article typeface" look if desired (appearance, not type).

---

## 3. Critique: is the plan a good idea?

**Yes — the unifying instinct (one prose payload at file and section scale, with scale
changes as cheap, reversible operations) is architecturally sound, and the vault already
proves the need** (`job_2026.md`'s `## Why I left Google?` prose section blocks reversal
today; `sase_blog` can never reverse). But the plan as stated has five traps the
requirements should be adjusted around. Each adjustment is called out explicitly:

- **A1 — Define the type by ownership, not content** (§2 above). Otherwise
  `[[prose]]` on a project note looks reasonable and the engine rightly refuses it.
- **A2 — "Sections implicitly use this type" means extract-eligibility, not
  formatting.** The formatter stays whole-note and opt-in via `type:`. Running N-rules
  or F-rules inside a live project note would fight `## Tasks` status groups, chip
  lines, and generated catalogs; the 202610 article research's safety property
  (formatting is safe *because* it is scoped by explicit type) still holds. No stored
  per-section type, no section registry: eligibility is derived at the cursor, like
  Leaf Project.
- **A3 — Ship the inverse with the extract.** Org-roam users asked for
  `extract-subtree`-in-reverse within a year; Bob already has the pattern (Task
  Split/Merge, drawer ↔ H2). A one-way keymap traps writing in files that then block
  project reversal — the exact problem this work exists to solve.
- **A4 — The rename does not unblock reversibility, and prose alone does not
  either.** The child-note refusal is kind-blind; status groups, catalogs, req
  asymmetry, and project-only frontmatter are independent, verified blockers (§1.3).
  Scope the promise: this work unblocks the *prose class*; albums, refs, and
  subprojects need their own rules (subprojects should stay refused — flattening them
  destroys project boundaries).
- **A5 — Distinguish derived prose from root prose.** A note extracted from a section
  folds back losslessly. A document that happens to be a project child
  (`sase_blog_contents.md`) must **never** be poured into a task — byte-lossless would
  still be the wrong shape. Provenance recorded at extraction (origin parent + heading
  identity) is the discriminator; missing provenance ⇒ root prose.

Two more adjustments earned consensus and survive lead review: **A6 — define
"lossless" testably** (`inline(extract(S)) == S` byte-for-byte modulo bob-owned number
tokens and seam blank lines; the word-token invariant holds across every multi-file
plan; anything that would be dropped — unknown frontmatter keys, colliding block ids —
refuses or previews, never silently discards) and **A7 — alias-first, never flag-day**
(per `cli_rules`: `bob articles` becomes a permanent hidden alias; the matcher reads
`[[article]]` permanently — one predicate — while writers emit `[[prose]]`).

---

## 4. Disagreements between the reports, resolved

The swarm converged on the name, the Rust-planner architecture, derived (never stored)
section eligibility, and "prose is never poured into drawers / `parent:` never points at
task blocks". Four real disagreements remained; resolutions below with reasons.

### 4.1 What extraction leaves behind in the source note

Positions: keep `## Title` + plain wikilink (cdx, grk) · keep `## Title` + embed
`![[note]]` (cld's "placement model") · remove the section and rely on a generated
`## Prose` catalog (gem).

**Resolution: keep the heading, and make the stub a single list bullet —
`## Title` + `- [[stem|Title]]` (embed-bullet `- ![[stem]]` as an option).** Keeping the
heading preserves the structural slot, document order, and a landing for inbound links
(both cdx and cld independently argued this; gem's catalog-only approach loses authored
position and reading flow). The bullet form is a lead-researcher synthesis the swarm
missed: a list-only section already passes today's reversal split as a drawer with one
note line, so stub sections are reversal-compatible with **zero new reversal code**, and
a bullet link also satisfies the drawer contract ("entries are plain bullets") after
conversion. Embed-vs-link display is a taste call: embeds give reading continuity but
render the extracted note's promoted headings beneath the stub heading — test that
rendering (cdx's caveat) before making embeds the default. gem's `## Prose` host catalog
(same engine as `[!notebooks]`/`[!albums]`) is **complementary discovery, not a
replacement**, and is a justified optional extra for a later phase — note that adding it
also obligates the reversal catalog-skip fix (§1.3).

### 4.2 `section_numbers` default

Positions: keep `true` (cld) · flip to `false` (gem) · origin-dependent (grk) ·
separate preserve/managed formatting policy (cdx).

**Resolution: grk's origin rule.** Extraction always writes an explicit
`section_numbers: false` (a heading named `API Design` must not come back as
`## 1. API Design`); hand-created root prose keeps today's `true` default, preserving
the house style that lets agents say "tighten §1.3". This needs no default flip, no
contract change, and addresses the adoption-friction concern where it actually bites.
**Clearly flagged taste call for Bryan:** if quick generic prose notes (letters, meeting
notes) feel invaded by auto-numbering, flip the global default to `false` — migration
cost is one line on `sase_blog_contents.md` plus the template — and add a
`Toggle section numbers` command either way. cdx's separate preserve/managed formatting
property is deferred: it adds a second knob before any evidence demands it.

### 4.3 JSON contract: bump or keep?

Positions: keep `schema_version: 1` with stable wire keys (cld, grk) · bump to v2
renaming `summary.articles`/`not-article` (mus, gem).

**Resolution: keep v1; wire vocabulary is contract, not user language.** Verified: the
contract is growth-only and the plugin hard-rejects unknown versions; three hosts run
skewed bob versions while plugins deploy instantly via `bob plugins sync`, so a key
rename forces either dual-version plugin code or a coordinated cutover — for zero user
benefit, since `summary.articles` and refusal codes are machine-facing. Rename only
display strings ("Prose note formatted · …"). The extract/inline feature arrives as a
**new, separately versioned conversion contract** anyway (do not repurpose ArticlePlan
formatter fields for multi-file moves — cdx), so no `!` break is needed for the rename
at all. A v2 bump stays available if a real structural change ever justifies it.

### 4.4 Plugin identity

Positions: keep id `bob-articles`, rename display name (cdx, cld, grk) · rename dir/id
to `bob-prose` (mus, gem).

**Resolution: keep the id; rename the display name to "Bob Prose" and the command
titles.** An id rename is *feasible* right now (verified: no `data.json`, no bound
hotkeys) but costs a manual vault cutover (`config.yml` `plugins.sync`,
`community-plugins.json`, removing the old plugin dir — `bob plugins sync` does not
auto-prune) and buys nothing functional. Give the **new** extract/inline commands
prose-named ids from day one. If Bryan wants the repo directory renamed for aesthetics,
do it as its own coordinated chore, not inside this epic.

### 4.5 Reversal model for prose children

Positions mostly converge once vocabulary is aligned: cld's "re-point `parent:` to the
residence note" and grk/gem's "reparent to the grandparent" name the same note (the
restored task's residence). cdx alone proposes keeping a **prose companion at the
project's old path** (retype the project file to prose; children untouched).

**Resolution: reparent-and-carry as the default; companion as a named alternative.** On
project → task reversal: implicit prose sections are offered for extraction (preview,
one transaction) to new prose notes parented to the residence; existing prose children
reparent to the residence; each carried note gets a `- [[stem|Title]]` bullet under the
restored task's `- **Notes**` drawer. On task → project promotion: prose notes linked in
the task block whose current `parent` is the source note are offered in an explicit
consent picker (per `decisions:unblocked-tasks-are-offered` — the direct-sibling rule
prevents a mention in `dev.md` from stealing `sase_blog_contents` from `sase_blog`);
accepted ones reparent under the new project. Provenance recorded at extraction (A5)
chooses the inverse. cdx's companion model — retype the project note to prose in place
so children's `parent:` stays valid — is the better shape for *document-centric*
projects and avoids touching children at all; keep it as an explicit option rather than
the default, since it leaves a file where "reversal" promises removal. Two cdx points
stand regardless of model: distinguish **operation undo** (exact before-images while
postimages match) from **semantic re-inlining** (a new transformation of current
content), and define content/identity preservation separately from scheduling/review
equivalence — promotion consumes plans and offers successors by design, so exact
operational-state reversal is not on the table
(`decisions:projects-block-from-prj-line`, `decisions:task-lanes-are-sticky`).

---

## 5. Recommended solution

Three decoupled phases, each independently useful, ordered for the daily release train
(`decisions:bob-cli-releases-ride-a-daily-train`; plugins deploy instantly; three hosts
skew).

### Phase 1 — Rename (one train, small)

1. **bob-cli**: matcher accepts `[[article]]` and `[[prose]]` permanently; `adopt`
   writes `[[prose]]`; `bob prose` canonical with `bob articles` as a permanent hidden
   alias (`cli_rules`); rename display strings, help, nightly step label, completion
   kind, catalog slot labels; add `prose` to reserved record ids and built-in type
   lists (keep `article` reserved). **Keep wire keys, refusal codes, and
   `schema_version: 1`** (§4.3) — no `!` needed. Docs: `docs/articles.md` →
   `docs/prose-notes.md` with redirect (read the `docs.md` memory first), and add the
   type to `docs/reference/vault-format.md` (it is the only first-class type missing).
   Optional separate refactor commit: Rust module `articles` → `prose` so greps stop
   mixing it with `highlights_ref`'s web articles.
2. **bob-plugins** (same day fine): display name "Bob Prose", command titles renamed,
   detection accepts both types; plugin id and existing command ids stay (§4.4).
3. **Vault** (after all three hosts' `bob --version` includes step 1): retype
   `sase_blog_contents.md`; rename `article.md` → `prose.md` (reworded to the §2
   definition), `new_article.md` → `new_prose.md`, `articles.base` → `prose.base` with
   filter accepting both types; update `type.md` and `AGENTS.md`. Leave
   `.bob/ref-sources` history alone.
4. **Memory** (via `/sase_memory_write`): glossary entries **Prose Note** (alias:
   article, legacy) and **Prose Section**, each saying what it is *not* (not a notebook,
   record, ref, drawer, or Annotation Section — that name is already taken by managed
   Highlights groups); one decision record covering the name, the ownership definition,
   the permanent aliases, and implicit-type-as-eligibility.

### Phase 2 — Extract / inline (the feature)

`bob prose extract NOTE --section IDENTITY` and `bob prose inline NOTE` in Rust
(`src/native/prose/`), with dry-run previews, JSON plans under a **new** versioned
conversion contract, preimage-guarded all-or-nothing multi-file writes
(`vault_rewrite` as the base — add tested create/trash handling and crash-recovery
evidence; multiple atomic file replacements are not an atomic vault transaction), and
the word-token invariant across the whole plan.

- **Eligibility (derived, never stored)**: an authored, non-structural `##` section (or
  deeper subtree at the cursor) in an area, project, or prose note; not `## Tasks`, not
  generated catalogs or their status groups; no `#task` lines, `^prj`/`^ref` anchors, or
  conflict markers in the subtree; classified with the real Markdown classifier
  (fences, callouts, Setext, list continuations), not heading regexes. Bullet-only
  sections are also extractable (start in bullets, graduate to prose). Notebooks,
  records, refs, daily notes excluded in v1. Ineligible contexts refuse with a named
  reason; never fall back to converting the surrounding note.
- **Extract**: new note `<owner>_<slug>.md` (editable prompt, collision refusal) with
  `parent: "[[owner]]"`, `type: "[[prose]]"`, `created:`, `title:` holding the exact
  heading bytes, provenance fields (origin + heading identity), explicit
  `section_numbers: false` when extracted from work notes; headings promoted one level
  (refuse on depth overflow rather than emit invalid levels); stub left behind per
  §4.1. Link repair in every direction reusing the articles inbound machinery:
  source-local links into the subtree, subtree links back to the source, third-party
  `[[owner#Heading]]`/`[[owner#^id]]` links, aliases and embeds preserved; refuse
  ambiguous duplicate headings and cross-boundary footnote/reference-definition
  dependencies rather than silently re-targeting (CommonMark definitions are
  document-global — cdx).
- **Inline**: requires provenance or a stub match; demotes headings (refuse on
  overflow), strips bob-owned number tokens (N6/N9), absorbs only the known frontmatter
  keys and **refuses listing any other key** (A6); re-points inbound links; trashes the
  note only after all writes land. Refuses if the note has children, if the origin
  section still exists in full, or if block ids would collide. Property test:
  `inline(extract(S)) == S` for eligible sections without owned-number ambiguity.
- **Keymap**: one bidirectional command in the plugin (context-dispatched: heading ⇒
  extract preview; prose note ⇒ inline preview), mirroring the
  `Ctrl+Shift+Alt+N` task/project toggle ergonomics. `Ctrl+Shift+E` is verified unbound
  in `hotkeys.json` and the plugins; overloading the existing conversion gesture by
  cursor depth is the alternative — Bryan's call.
- **Zero-code stopgap meanwhile** (cld): Obsidian's core Note Composer with a
  `_templates/prose_extract.md` template (`parent: "[[{{fromTitle}}]]"`,
  `type: "[[prose]]"`) gives most of the extract gesture today — useful for feel, not
  authoritative (no heading-subtree semantics, no Bob link repair, no inverse).

### Phase 3 — Reversible projects (consumer of Phase 2)

1. **Fix the pre-existing blockers first** (§1.3): flatten/skip `## Tasks` status
   groups and the chip line on reversal; skip all generated catalogs
   (`[!notebooks]`, `[!albums]`, future `[!prose]`), not just `[!projects]`; define the
   req round-trip rule (plain rows without live task identity return to `- [ ]` reqs);
   preview-and-warn before dropping project-only frontmatter or orphaning
   `done_tasks:`. These fixes are valuable with or without prose.
2. **Integrate prose** per §4.5: offer extraction of implicit prose sections, reparent
   and carry prose children, consent-based re-adoption on promotion. Strongly consider
   moving the conversion planner itself into Rust (`bob projects promote/demote`) while
   touching it — the JS planner is ~1,500 lines of twin-parser logic and this epic
   rewrites its core anyway.
3. **Scope honestly**: albums, refs, subprojects, and untyped children still refuse,
   with notices that name the files. Design the carry rule so notebooks can adopt it
   later without a second mechanism.
4. **Memory**: a second decision record ("prose is placed, never poured") after Phase 3
   ships.

### Open questions for Bryan

1. Stub form: plain bullet link (recommended) vs. embed bullet — does reading-in-place
   matter enough to accept the double-heading rendering quirk?
2. Numbering: accept the origin rule (extracted ⇒ `false`, root ⇒ `true`), or flip the
   global default to `false`?
3. Keymap: new `Ctrl+Shift+E` chord, or overload the task/project conversion gesture by
   cursor context?
4. Intro prose above a project's first `##`: extract as a `## Overview` prose section,
   or keep refusing?
5. Is the generated `## Prose` host catalog wanted (discovery + honest conversion), or
   is `parent:`-based discovery via `Ctrl+=` enough?
6. Any ArticlePlan/`bob articles` consumers outside bob-cli, bob-plugins,
   bob-mac-capture, and the vault (scripts, cron, launchers)? The swarm audited those
   four; anything else needs one grep.

---

## Provenance

- `__cdx`: formatting/type separation, extraction contract rigor (link-repair table,
  footnote/definition hazards, undo-vs-reinline distinction), companion-file reversal
  alternative, acceptance-test matrix.
- `__cld`: vault census, placement model, byte-exact round-trip rules E1–E5/I1–I4,
  Note Composer stopgap, keep-wire-contract argument, rename sequencing for the train.
- `__grk`: three-scales framing (see its `*_scales.png` figure), derived-vs-root prose,
  origin-dependent numbering, reversal-scope figure (`*_reversal.png`), A1–A12
  adjustment list, vault-format/glossary gaps.
- `__mus`: four-meanings collision analysis (semantic rename, Mac Capture verified
  clean), alias-first mechanics, candidate matrix incl. `entry`, phase blueprint.
- `__gem`: live-vault evidence (`job_2026.md`, `sase_blog.md`), the five additional
  reversal blockers (lead-verified), `## Prose` catalog design, Rust extract/inline
  specs with depth-overflow and block-id-collision refusals, keymap verification.
- Lead verification this report: decisions roster; `docs/articles.md` (growth-only
  contract, N6/N7/N9, `section_numbers` default); `plan.rs` wire keys; reversal
  regexes and catalog skip in bob-plugins; status groups and catalogs in live project
  notes; vault `[[article]]` census; `vault-format.md` omission; free `Ctrl+Shift+E`;
  the bullet-stub synthesis in §4.1.
