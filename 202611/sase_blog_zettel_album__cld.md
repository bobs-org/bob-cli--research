# Writing the SASE post from record notes: should `sase_blog_zettel` be an album?

_Researcher: cld · 2026-11-12 · bob 0.5.0 on apollo · bob-cli master `4ed4fdab`_

## Bottom line

**Yes, build the album, but change three things about the plan.** Records are a good
place to draft blog material, and everything needed already ships: I created the
proposed album, captured into it, and appended to it in a sandbox vault, and nothing
needed new bob or plugin code. The album will not make the post write itself, though.
The plan needs these changes:

1. **One record per *topic* (one claim), not one per outline section.** Your outline
   will change; topics mostly won't. A section can hold several topics, and some
   topics will never ship.
2. **Keep `sase_blog_contents.md` (the article) as the spine and the final draft.**
   The album is the workbench where pieces get built. The article holds order and
   transitions, and it is where the finished post comes together. Record the order
   in one place only: the spine.
3. **"Re-arranging" is not the last step; rewriting is.** Budget a real pass for
   transitions and voice when the pieces come together, and keep the `^v1-draft`
   task as a writing task, not a paste job.

Do the setup inside the S0 spike and keep it to **one Pomodoro or less**. It should
*replace* part of S0's work ("one claim sentence under every heading"), not come
before it. The project has existed since 2026-06-11, and the article has had all 15
section headings since 2026-10-15, but there are still 0 words under any of them.
The bottleneck is writing, not storage.

The recommended setup (detailed in [§7](#7-recommended-solution)):

- **Album:** `sase_blog_zettel.md`, parent `[[sase_blog]]`, noun `zettel`, emoji 📇.
- **Fields:** `status` (🌱 seed → ✍️ draft → ✅ ready → 📌 placed, plus ⏭️ later and
  ✂️ cut), a **required** one-sentence `claim`, and an optional `part`.
- **Index:** shows `part · claim` on every row, so the generated `[!records]` index
  reads as the post's argument and its tally works as a progress bar.
- **Record body:** `## Draft` (the only part that ships) above bob's `## Notes`
  (dated raw ideas that capture appends).

## 1. What I looked at

| Source | What it told me |
| --- | --- |
| Epic `bob-cli-k3` and `plan:202611/album_and_record_notes.md` | The album/record contract: owner = an area or project, stem = folder = capture route, records hold no tasks, the generated `[!records]` index, the `## Albums` catalog. |
| `docs/records.md`, `docs/articles.md`, `docs/notebooks.md`, `docs/capture.md` (bob-cli master) | What records, articles, and notebooks do with prose, and how capture routes into each. |
| `docs/reference/plugins/albums.md` | Album cards: live count, lead-group, and age chips on the owner's catalog row. |
| `~/bob/sase_blog.md`, `sase_blog_contents.md`, `sase_blog_0_legacy_notes.md`, `sase_blog_blockers.md`, `sase_pre_blog.md`, `sase_post_blog.md`, `movies.md` + `movies/` | Where the blog material lives today, and a live album for comparison. |
| `bob albums list`, `bob articles outline sase_blog_contents`, `bob albums create … -d` against the real vault (dry run, nothing written) | Current state, and exactly what creation would write. |
| A throwaway sandbox vault (`/tmp/cld_zettel_sandbox`) | End-to-end check of the proposed schema: check, create, capture-append, batch seeding, and index rendering. |
| `sase-org/sase` checkout (via `sase repo open sase`): `mkdocs.yml`, `docs/blog/` | The publishing target and the posts that already exist. |
| Web: Longform, Easy Bake, Ahrens' *How to Take Smart Notes* | Off-the-shelf "notes → manuscript" tools, and the standard warning about drafting from notes. |

## 2. Facts that shape the decision

### 2.1 What albums and records already give a writer

All of the following were verified on bob 0.5.0 (see §3 for the sandbox results):

- **An album can hang under `sase_blog`.** An album's parent may be "an area or
  project of any status". `sase_blog` is a `root: true` project, so the dry run
  touches exactly one catalog (`sase_blog.md`) and inserts `## Albums` right under
  the `^prj` block.
- **Record bodies are yours.** bob writes the frontmatter, an H1, and `## Notes`.
  After that, updates "preserve every untouched key, comment, body byte, and line
  ending". Prose, callouts, lists, links, and fenced code all pass
  `bob records check` with zero findings. Only checkbox rows outside fenced code
  are errors (`record_checkbox`).
- **Capture can route ideas to a topic.**
  - `idea text @sase_blog_zettel/<stem>` appends a dated bullet under that
    record's `## Notes` and leaves the rest of the body alone.
  - `Title @sase_blog_zettel/` plus `- key:: value` bullets creates a new record.
  - A `%t` template seeds many records in one atomic capture.
  - After `@sase_blog_zettel/`, `bob capture-complete` offers the existing record
    stems, each with its title and status (verified in the sandbox:
    `@sase_blog_zettel/agent_clis One CLI → Every CLI · 🌱 Seed`). Bob Mac Capture
    gets its album rows from bob too (epic phase k3.8).
- **The index works as a progress board.** The `[!records]` callout title is a
  tally, such as `14 zettels · 🌱 6 seed · ✍️ 4 draft · ✅ 2 ready · ✂️ 2 cut`.
  Groups follow the declared order of `status`, and up to three facets show on
  each row. In `sase_blog.md`, the Album card adds a live chip for the count, the
  first nonempty group, and the time since the last record was added.
- **Limits that matter here:**
  - Index rows sort **by title** within each status group. There is no
    narrative order.
  - The index never reads note bodies, so there are no per-record word counts.
  - A note cannot be both a record and an article (`bob articles` refuses
    `mixed-type`).
  - Albums and records hold no tasks.
  - The album must sit at the vault root, and its stem is the route you type.

### 2.2 The article tooling you already have

`sase_blog_contents.md` is already a `type: "[[article]]"` note.
`bob articles outline sase_blog_contents` reports the following today:

```text
sase_blog_contents · article · 301 words · 15 sections · 15 TODO
  ¶  Preamble  190 w
  1.     Why I use SASE  TODO
  2.     What is SASE?  TODO
  …
```

The article already provides:

- section numbering;
- per-section word counts and TODO-stub detection;
- automatic heading-link repair when sections move;
- capture into a section by its heading identity, so
  `@sase_blog_contents#agent` still finds `## 2.3 Agent CLIs` after renumbering
  (`docs/capture.md`, around line 7543).

So the single-article approach already handles capture routing and progress
tracking. The album has to earn its place on other grounds (§4).

### 2.3 Where blog material lives today

`sase_blog.md` holds:

- 44 top-level `## Requirements` bullets that mix topics, quotes, and style or
  production rules;
- 8 `## Outline` bullets;
- 6 `## Later Posts` bullets;
- 3 screenshots;
- four zero-draft tasks, each carrying a **CARD**: 😈 the old way · 😇 the SASE
  way · PROOF · LESSON.

There are also `sase_blog_contents.md` (the article), `sase_blog_0_legacy_notes.md`,
and the project's sub-projects. That is already four or five homes for blog
material, with no rule for which home a new idea goes to.

### 2.4 The publishing target: sase.sh

- **sase.sh is MkDocs Material**, using the `blog` plugin with
  `post_url_format: "posts/{slug}"` and `strict: true`. Posts are files in
  `docs/blog/posts/*.md` in the sase repo, so whatever you draft in Obsidian needs
  one syntax conversion pass at the end:
  - wikilinks → Markdown links;
  - `> [!note]` → `!!! note`;
  - `![[img/x.png|400]]` → a Markdown image with `{ width="400" }`;
  - `[1]:` pseudo-footnotes → `[^1]`.

  This is true for every option in §5.
- **A launch post is already live.** "SASE: Structured Agentic Software
  Engineering" (2,882 words) was published on 2026-07-08 through epic `sase-5k`. It
  covers agent CLIs, macros, the Agents tab, and installation. Nine more `draft: true`
  posts, `[00]`–`[09]`, total about 16.7K words. Your own-voice post overlaps heavily
  with that material.
- **SASE has renamed things since your outline was written.** The live post notes
  that "SASE xprompts have been renamed to macros", and the patches draft is titled
  "[06] Patches in Practice" (slug `changespecs-in-practice`). Your outline still
  says "Xprompts" (§2.5) and lists "ChangeSpec" under Later Posts. Drafts that sit
  for weeks will go stale on names and facts unless something checks them.

## 3. Sandbox evidence (dry runs and a scratch vault, nothing in `~/bob` touched)

1. **Creating the album against the real vault (dry run)** would write:
   - `sase_blog_zettel.md`, with canonical frontmatter, an intro line teaching
     `Name @sase_blog_zettel/`, and the empty index `> [!records] No zettels yet`;
   - a starter `sase_blog_zettel.base`, grouped by status;
   - one `## Albums` row in `sase_blog.md`.

   Without `-t`, the title comes out as "Sase blog zettel", so pass
   `-t 'SASE Blog Zettel'`.
2. **The proposed schema** (§7.1) passes `bob albums check` with 0 errors. A
   required `claim` works: capture without one refuses and prints a ready-to-copy
   draft:

   ```text
   bob capture: capture item 1 starting on line 1: a Zettel note needs 1 more required field
   Memory beats skills @sase_blog_zettel/
   - status:: seed
   - claim:: …
   ```

3. **Prose bodies** with `## Draft`, a callout, a list, and links: `bob records check
   zettel` reports `✓ 5 zettels — 0 errors, 0 warnings`.
4. **Appending by capture**
   (`Alternations enable "vibe evals" across rival labs @sase_blog_zettel/agent_clis`)
   adds `- 2026-11-12: …` as the last `## Notes` bullet. `## Draft` stays
   byte-identical, and the album index is re-planned in the same transaction.
5. **Batch seeding** with a `%t` template creates both records atomically:

   ```text
   {0} @sase_blog_zettel/ %t
   - status:: seed
   - part:: {1}
   - claim:: {2}

   "Why a TUI?" what "One screen for every agent beats a wall of terminals."
   "Memory over skills" what "If I started over, skills would just be procedural memory."
   ```

6. **The rendered index** is effectively the post's argument:

   ```markdown
   > [!records] 5 zettels · 🌱 2 seed · ✍️ 1 draft · ✅ 1 ready · ⏭️ 1 later
   >
   > - **🌱 Seed** · 2
   >   - [[sase_blog_zettel/ai_slop|My definition of AI slop]] — 🛑 Why not · AI slop is code nobody would defend in review: …
   >   - [[sase_blog_zettel/agent_clis|One CLI → Every CLI]] — 🧱 What it is · SASE promises the best experience across every provider, not the best performance.
   > - **✍️ Draft** · 1
   >   - [[sase_blog_zettel/gates_plans_epics|Gates → Plans → Epics]] — 🧱 What it is · Plan mode is one instance of a deeper primitive: the gate.
   > …
   ```

   The sandbox labelled the `why_not` choice `😈 Why not`. This report recommends
   `🛑 Why not` (§7.1), so the sample shows the recommended label.

## 4. Critique: is this a good idea?

### What the plan gets right

1. **It keeps raw ideas apart from prose, per topic.** Capturing into the article
   (`@sase_blog_contents#agent`) drops bullets straight into the draft. Capturing
   into a record puts dated notes under `## Notes`, away from `## Draft`. This is
   the biggest practical gain.
2. **Topic identity survives outline churn.** A record's filename is fixed when it
   is created. Renaming its `title:` or moving its topic to another section changes
   nothing about the record's identity or the links to it. Article capture
   selectors, by contrast, follow heading text.
3. **You get a progress board for free.** The tally, the status groups, and the
   owner-card chip in `sase_blog.md` answer "how far along is the post?" without a
   task per section.
4. **Small units fit how you already work.** The zero-draft tasks already say
   "dictate ≥150 words … no editing". One record is one Pomodoro-sized unit you can
   open on its own.
5. **Material carries over to later posts.** `⏭️ later` records keep material for
   the six "Later Posts" topics and the nine sase-repo drafts, instead of leaving it
   buried in `## Requirements`.
6. **It costs no code, and it tests albums on a non-media collection.** It is
   built entirely from shipped behavior (§3).

### What it gets wrong, or risks

1. **It can become productive procrastination.** The project was created on
   2026-06-11. The article got its headings on 2026-10-15 and was last edited on
   2026-10-26. The S0 spike was created on 2026-10-23 with a 2 🍅 hard stop, and
   today's work-log entry under S0 is "apollo research on creating new
   sase_blog_zettel album!". A new container only helps if writing the first claims
   *is* setting it up. Your own §3.1 list of AI-slop categories includes "Features
   that I no longer use or never used". Don't add tooling for a single post.
2. **"Mostly re-arranging" is optimistic.** The post has a through-line: pride →
   what SASE is → why you shouldn't use it. Sections written in isolation tend to
   re-introduce context and read like a listicle. Ahrens' standard advice on writing
   from notes is: "Don't simply copy your notes into a manuscript. Translate them
   into something coherent and embed them into the context of your argument." Expect
   arranging *plus* one rewrite pass.
3. **One record per section ties records to an outline you have said will change.**
   Sections and topics are not one-to-one:
   - §2.3.1 "Skills, **memory**, provider interface, NOT hooks" is three or four
     topics.
   - §3.2 "Future Work" overlaps "Later Posts".
   - The Requirements list holds topics that have no section yet (Gas Town
     comparison, "Why a TUI?", "vibe evals", loop vs. graph engineering).
4. **It adds a fifth home without a routing rule.** Unless each kind of material
   has one home (see the routing table in §7.2), the album will collect duplicates
   of Requirements bullets and task CARDs.
5. **Records were not designed for drafts.** They work because bob leaves body
   bytes alone, not because anything helps with prose. There is no per-record word
   count, and the index sorts by title. The article tooling (§2.2) is the better
   instrument once the prose comes together, so plan to switch back to it.
6. **"Zettel" promises more than these notes are.** Luhmann-style zettels are
   atomic, permanent, densely linked ideas. These records are topic drafts
   ("scenes", in Longform's vocabulary). The name is fine. The one Zettelkasten
   discipline worth keeping is **one claim per record**, enforced by a required
   `claim` field.
7. **Facts and names will drift.** Macros and Patches have already been renamed.
   The `ready` gate must include "names and claims checked against current sase".

**Verdict:** this is a good idea once adjusted. It costs about 15 minutes and fixes
three real problems: where captured ideas land, outline churn, and progress
visibility. It is a filing system, not a writing accelerator. Use it as the way to
do S0, not as a step before S0.

## 5. Alternatives considered

| Option | Strengths | Weaknesses | Verdict |
| --- | --- | --- | --- |
| **A. Single article only** (status quo: write under the headings in `sase_blog_contents.md`) | Shipped tooling: numbering, per-section words, TODO stubs, capture to `@sase_blog_contents#…`; prose flows from the start | Captured bullets land inside the prose; one large file; capture selectors follow headings that will change; no status per topic | Solid fallback. Choose it if you would rather just write. |
| **B. Notebook** (`sase_blog_notes` with `##` per topic) | Shipped; capture to `@nb#Section` | Notebooks are for bullets: `notebook_shape` warns on stray top-level paragraphs and on H3 or deeper headings; no status | Wrong shape for prose. |
| **C. Album, one record per outline section** (as asked) | Everything in §4 "what it gets right" | Ties records to the outline; fuzzy membership for multi-topic sections | Adjust to D. |
| **D. Album, one record per topic, with the article as spine** | C's strengths; the spine owns order and transitions; the article tooling returns for the final draft | One paste per topic when it is ready; two homes during placement (handled by `📌 placed`) | **Recommended.** |
| **E. Longform plugin** | Built for exactly this: scenes in a folder, drag to reorder, compile to a manuscript | New community plugin (not installed); it rewrites its index note's frontmatter, so it must not sit on the album note because it would fight the `record:` block; adds a second source of order | Not worth it for one post. Revisit if you write a series this way. |
| **F. Easy Bake plugin** | Bakes single-line embeds into one file | New plugin; behavior on heading embeds (`#Draft`) unverified | Optional at assembly only; ~15 manual pastes is about 15 minutes. |
| **G. New bob feature** (e.g. "assemble an article from an album") | Repeatable | Built for one post; scope creep | Premature. Revisit only after two posts have been assembled this way. |

## 6. Requirement adjustments (called out)

| # | Your requirement | Adjustment | Why |
| --- | --- | --- | --- |
| **R1** | Each section or topic gets its own record | **Changed:** one record per *topic* (one claim). A section holds one or more records; some records never ship. | Topics are stable while the outline changes; §2.3.1-style sections bundle several topics. |
| **R2** | Writing the blog becomes mostly re-arranging records | **Changed:** writing = arranging in the spine + one rewrite pass. `sase_blog_contents.md` stays the spine and the final draft. | Narrative glue and voice belong to the whole, not to the parts (§4, risk 2). |
| **R3** | Records are children of a new `~/bob/sase_blog_zettel.md` album | **Kept**, with the parent `[[sase_blog]]`, noun `zettel`, title "SASE Blog Zettel", and emoji **📇, not 🧩** | bob already uses 🧩 for "Sub-projects" lines and for project group rows in catalogs. 📇 (card index) suits a slip box. |
| **R4** | (none) | **Added:** a status pipeline with exit criteria, and a required `claim` | Turns the index into a progress board and enforces one claim per record. |
| **R5** | (none) | **Added:** body convention `## Draft` (ships) above `## Notes` (never ships) | A clear boundary for pasting; capture keeps appending to Notes. |
| **R6** | (none) | **Added:** a routing rule, one home per kind of material (§7.2) | Prevents a fifth pile of duplicates. |
| **R7** | (none) | **Added:** order lives only in the spine; no `order` field | A second source of order goes stale; the index cannot sort by it anyway. |
| **R8** | (none) | **Added:** setup inside S0, ≤ 1 🍅, no new bob or plugin code; triage the 44 Requirements bullets lazily | The bottleneck is words, not structure. |
| **R9** | (none) | **Added:** Draft prose uses portable Markdown and current SASE names; the `ready` gate includes a fact check | The target is MkDocs Material, and macros and Patches have been renamed. |

## 7. Recommended solution

### 7.1 Create the album (about 5 minutes)

```sh
cd ~/bob
bob albums create sase_blog sase_blog_zettel -n zettel -e 📇 -t 'SASE Blog Zettel' \
  -s 'Topic-sized pieces of my SASE posts, one claim per record, in my own voice.' -d
# Inspect the diff, then run the same command without -d.
```

Then make the album's frontmatter match the following. `create` writes the first
six keys; add `index_facets`, `dated_notes`, and `fields`. Run `bob albums check`
afterwards. The schema was validated in the sandbox.

```yaml
---
parent: "[[sase_blog]]"
type: "[[album]]"
summary: Topic-sized pieces of my SASE posts, one claim per record, in my own voice.
emoji: 📇
index_facets:
  - part
  - claim
created: … # written by create
record:
  noun: zettel
  label: Zettel
  dated_notes: true
  fields:
    status:
      required: true
      values:
        seed: 🌱 Seed
        draft: ✍️ Draft
        ready: ✅ Ready
        placed: 📌 Placed
        later: ⏭️ Later
        cut: ✂️ Cut
    claim:
      required: true
    part:
      values:
        hook: 🪝 Hook
        why: 🙋 Why I use it
        what: 🧱 What it is
        why_not: 🛑 Why not
        close: 🏁 Close
---
```

- **`status` stages and their exit criteria:**

  | Stage | Done when |
  | --- | --- |
  | 🌱 seed | It has a title and a claim. |
  | ✍️ draft | It has a zero-draft of at least 150 words in `## Draft`, dictated or typed, unedited. |
  | ✅ ready | It is revised, uses current SASE names, has its claims checked against sase HEAD, and has its links and images resolved. |
  | 📌 placed | It has been pasted into the spine. **From then on, edit only the article.** |
  | ⏭️ later | It belongs to a future post. |
  | ✂️ cut | It was dropped, but kept for the record. |

  Seed comes first because the index leads with the first declared group, so the
  next thing to write is always at the top.
- **`claim`** is required. If you cannot state the claim yet, the idea is not a
  topic: capture it as a note on an existing record, or into `## Requirements`.
- **`part`** is optional and coarse, because the top-level parts change less than
  the numbered sections. You can edit its choices later with `bob albums update`
  or in YAML. If the Seed group grows past 12 rows, add `index_by: part`.
- There is no `order` field (R7) and no word-count field. Obsidian's status bar
  shows the word count for the open record.

### 7.2 One home per kind of material

| Material | Home | Ships? |
| --- | --- | --- |
| A topic idea, quote, screenshot path, or proof for a topic | That topic's record, under `## Notes`, via capture or by hand | No; it is raw input |
| Prose in your voice | That record's `## Draft` | Yes, pasted when ✅ ready |
| Order, section headings, transitions, intro, promise sentence | `sase_blog_contents.md` (the spine) | Yes; it is the post |
| Post-wide style and production rules (devil/halo emojis, stick figures, citations, screenshots, `type:poll` issues, the podcast-transcription task) | `sase_blog.md` `## Requirements` (consider renaming it "Style & production") | Applied during the rewrite |
| Work: zero-drafts, reviews, release | Tasks in `sase_blog.md` that link to records (records hold no tasks) | n/a |

### 7.3 Record body convention

```markdown
# One CLI → Every CLI          ← bob writes this

## Draft                        ← you add it when you start drafting; only this ships

Portable Markdown: [text](https://…) links, [^1] footnotes, current SASE names.
Image embeds (![[img/….png|400]]) are fine; they get converted at publish time.

## Notes                        ← bob-managed; capture appends dated bullets here

- 2026-11-12: 😈 one CLI at a time · 😇 every provider behind one harness
- 2026-11-12: PROOF ~/tmp/screenshots/20260616_140429.png (retries through the Claude outage)
```

### 7.4 The spine (`sase_blog_contents.md`)

- Under each heading, link the records that feed it. For example, under
  `## Agent CLIs`: `→ [[sase_blog_zettel/agent_clis|One CLI → Every CLI]] · [[sase_blog_zettel/memory_over_skills|Memory over skills]]`.
- To reorder, move headings and link lines. `bob articles` renumbers the headings
  and repairs heading links.
- Write transitions directly in the spine, between the links. They belong to the
  whole, so they are the one kind of prose that does not live in a record.
- When a record reaches ✅ ready, paste its `## Draft` text in place of its link
  and set the record to `📌 placed`. From then on, `bob articles outline` word
  counts show the real per-section progress.
- Tradeoff: a section that contains only link lines no longer counts as a TODO
  stub, so until placement, the album tally is the progress signal.
- If you want a live read-through, `![[sase_blog_zettel/x#Draft]]` heading embeds
  also work in Obsidian. They render the "Draft" heading inside the article, so
  use plain links by default.

### 7.5 Capture recipes

- **New topic:**

  ```text
  Why a TUI? @sase_blog_zettel/
  - status:: seed
  - part:: what
  - claim:: One screen for every agent beats a wall of terminals.
  - Agents tab is the buggiest part of the TUI
  ```

- **Idea for an existing topic** (completion offers the stems):
  `Alternations enable vibe evals @sase_blog_zettel/macros`
- **Seeding many topics at once:** use the `%t` template from §3, item 5.
- **Promote a record:**
  `bob records update zettel agent_clis -s status=draft`, or edit the
  property in Obsidian.

### 7.6 First session: the revised S0 (one Pomodoro or less)

1. Create the album and paste the schema (7.1).
2. Seed one zettel per *topic* in the current outline, each with its claim. Use
   one `%t` capture of about 12–18 rows. This is S0's "one claim sentence under
   every heading", in a form the index can display. Use current names: write
   "Macros", not "Xprompts".
3. Move the four Wave 1 CARD bullets from `^zd-cli`, `^zd-tui`, `^zd-gates`, and
   `^zd-macros` into their records' `## Notes`, and point each task at its record.
   The tasks keep their "dictate ≥150 words" exit criterion, now aimed at `## Draft`.
4. Put the spine links under the article's headings, and write the promise
   sentence in the preamble.
5. **Stop.** Do not triage the 44 Requirements bullets up front. When you draft a
   topic, search Requirements for it and move the matching bullets into its
   `## Notes` at that point.

### 7.7 Assembly and publishing (later, once)

1. Place every ✅ ready record into the spine, then do the rewrite pass that
   `^v1-draft` covers: transitions, voice, and the through-line.
2. Copy the article to `docs/blog/posts/<slug>.md` in the sase repo. Add front
   matter shaped like the live launch post: `title`, `date`, `description`,
   `categories`, `slug`, `image`, `links`.
3. Convert Obsidian syntax (§2.4). Using a SASE agent for this is fine; ask it to
   change syntax only and to prove that the prose tokens are unchanged, the same
   word invariant `bob articles` enforces.
4. Run `mkdocs build --strict`.

## 8. Open questions for Bryan

1. **Does this post replace the July launch post or sit beside it?** The answer
   decides which topics become `⏭️ later` or `✂️ cut` instead of being re-explained.
2. **Should `later` records stay in this album?** I recommend yes, under
   `sase_blog`. If the later posts become their own project, reparent the album:
   edit the `parent` frontmatter, then run `bob albums sync`.
3. **Are you happy with a required `claim`?** It is the strongest guard against
   vague topics, but it costs a sentence on every capture of a new topic.

## 9. Minor findings for the lead (not filed, to avoid five duplicate beads)

- **The index tally ignores singular counts.** `tally_text` in
  `src/native/albums/index.rs` (around lines 338–350) always uses the plural and
  writes `⚠️ N need a status`. A new album with one record therefore reads
  `1 zettels`. This album will show it on its first capture.
- **`bob capture --help` is out of date.** It still says "Record types come from
  the `records:` config block" (`src/native/capture/cli.rs:30`). This probably
  belongs to k3.11's docs audit.

## Sources

- bob-cli: `docs/records.md`, `docs/articles.md`, `docs/notebooks.md`,
  `docs/capture.md`, `docs/reference/plugins/albums.md`,
  `src/native/albums/index.rs`, `src/native/capture/cli.rs` (master `4ed4fdab`)
- `plan:202611/album_and_record_notes.md`; bead `bob-cli-k3`
- sase repo: `mkdocs.yml`, `docs/blog/index.md`, `docs/blog/posts/*.md`
- [Longform plugin listing](https://community.obsidian.md/plugins/longform)
- [Easy Bake plugin listing](https://community.obsidian.md/plugins/easy-bake)
- [Excerpts from *How to Take Smart Notes* (Rufus Pollock)](https://rufuspollock.com/post/ahrens-how-to-take-smart-notes)
- Your saved quote from [r/Zettelkasten: where do hub and structure notes go](https://www.reddit.com/r/Zettelkasten/comments/1h443i2/where_do_hub_and_structure_notes_go_in_a/)
  fits this design: the album index is the hub note (generated, "a slice of topics
  shown at a glance"), and the article spine is the structure note.

Library check: 0 of 4 candidates already in your library (0 finished). Checked:
*How to Take Smart Notes*, Matuschak's Evergreen notes, the r/Zettelkasten thread,
and Longform. Nothing here is a reading assignment; they are cited for single claims.
