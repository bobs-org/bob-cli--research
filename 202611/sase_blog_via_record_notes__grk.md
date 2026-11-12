---
title: Record notes are the wrong primitive for the SASE blog
description: Independent research (grk) on using album-backed record notes as section zettels for the SASE blog.
date: 2026-11-12
researcher: grk
query: Should each SASE blog topic live in its own record note under a new sase_blog_zettel album?
---

# Record notes are the wrong primitive for the SASE blog

> **Research query:** Bryan is writing a SASE blog post and wants each section or topic in its own record note, parented to a new `~/bob/sase_blog_zettel.md` album, so assembling the post is mostly rearrangement. Is that a good idea, what should change, and what should he actually implement?

## Bottom line

**Do not create `sase_blog_zettel.md`, and do not file one record per outline heading.** That plan uses Bob's schema-backed *thing* type as a stand-in for a manuscript. Records are restaurants, podcasts, shows, and movies. A blog section is prose in an argument. The vault already has the type, the file, and the writing method for this post.

- Keep **`~/bob/sase_blog_contents.md`** as the single manuscript (`type: "[[article]]"`).
- Keep **`~/bob/sase_blog.md`** as the kitchen (cards, requirements, screenshots, later-post list).
- Finish Spike S0 in the article: promise sentence, four Wave 1 cards, one claim sentence under every heading.
- Zero-draft by dictating *into the article headings*, with capture `@sase_blog_contents#agent` when a route helps.
- If an album is worth creating at all, create it later as **one record per SASE *post***, after this essay ships. That matches the four live albums. One record per *section* does not.

The attractive part of the idea — finish a chunk, then rearrange — is already how the article, the cards, and Wave 1 are designed. Splitting the manuscript into 15 record files makes rearrangement *harder*, because album indexes group by status, filenames freeze titles, and `bob articles` numbering, stubs, and word counts all operate on one note.

## Verdict

**The impulse is right. The type is wrong.**

Writing one claim, then one card, then 150 words under a heading, then rearranging, is a good way to finish this post. Mapping those chunks onto `type: "[[record]]"` children of a new album is a category error against the k3 record model, against the article type Bob already ships, and against how zettelkasten and snowflake writing actually compose a manuscript.

I would not take the proposed approach. I would take the writing system already on `sase_blog` and stop inventing a fifth album until there is more than one post to catalog.

## What a record note is for

bob-cli-k3 (*Album notes — every record collection hangs under the area it serves*) is still in progress at wrap-up (`bob-cli-k3.11`). The accepted design, the live vault, and `docs/records.md` already agree on the type.

A **record note** is one durable *thing*: a restaurant, a podcast, a show, a movie. Canonical records use `type: "[[record]]"` and `parent: "[[<album>]]"`. They live in the album's folder (`eat/`, `podcasts/`, `tv/`, `movies/`). Capture creates them with `@eat/` and first-level `key:: value` bullets. Bob always writes a `## Notes` section. Updates append more note bullets. Checkboxes are errors: the checker says **"records hold facts, never tasks."** Albums hold no tasks either (`album_holds_no_tasks`).

An **album** is a vault-root note with `type: "[[album]]"`. Its stem *is* the folder and the capture route. Its parent must be an area or a project. Schema lives in a nested `record:` mapping. Bob owns a grouped `[!records]` index rebuilt on every record write. Groups follow the `status` choices (actionable group first), then optional `index_by` subgroups once a group exceeds 12 rows. That index is a catalog of things, not a document outline.

The k3 research that the epic implements is explicit:

> "Everything I track" does not mean "everything becomes a record." Notebooks hold free-form observations, references hold external material, and projects hold outcomes. **Records are for schema-backed durable *things*.**

It also rejected "albums as notebooks" because notebook members are bullets and album members are schema-validated files. The same split applies here: article members are numbered sections of long-form prose.

Live albums today, from `bob albums list` on 2026-11-12:

| Album | Owner | Noun | Records | Grouping |
| --- | --- | --- | ---: | --- |
| `eat.md` | `body` | restaurant | 104 | to try / liked / not liked, then location |
| `podcasts.md` | `dev` | podcast | 15 | subscribed / unsubscribed |
| `tv.md` | `fun` | show | 23 | to watch |
| `movies.md` | `fun` | movie | 10 | to watch / watched |

Every one of those is a catalog of durable objects with a verdict field. None is a manuscript.

k3.9 (vault cutover) is closed. `bob albums create` already works. Creating a fifth album is *possible*. Possibility is not fitness.

## What already exists for this blog

The proposed album would sit beside a writing stack that is already more specific than records.

### The manuscript is an article

`~/bob/sase_blog_contents.md` is the only vault note with `type: "[[article]]"`. Parent is `[[sase_blog]]`. `bob articles list` on 2026-11-12:

- 15 sections
- 301 words
- 15 TODO stubs
- 4 findings, all `pseudo-footnote` on the `[1]` / `[2]` / `[a]` / `[b]` TODO markers
- state: needs format

The lede is 190 words and is the only real prose. It is already in Bryan's voice: pride in being a software engineer, SASE as an attempt to take back control, "prototype gone wild." Every heading under that lede is still `TODO`.

Article notes are Bob's long-form type. `bob articles` owns numbering (N1–N9), layout (F1–F11), heading-identity links, stub detection, and word counts. Formatting never changes prose. Capture to an article matches **heading identity** with the number stripped, so `@sase_blog_contents#agent` still lands on `## 2.3 Agent CLIs` after a renumber. `--section "Agent CLIs"` and a stale `--section "1.4 Agent CLIs"` both work. That is section-addressed writing, already shipped.

Record notes get none of that. `bob records` validates fields, appends `## Notes` bullets, and rebuilds a status catalog. `bob articles outline` will not see them.

### The kitchen is the project

`~/bob/sase_blog.md` is a root project (`type: "[[project]]"`, parent `[[sase]]`, theme WRITE). The `^prj` outcome is: *My SASE post, in my own voice, is live on https://sase.sh!*

The open writing method is already snowflake-plus-cards, not zettel-per-section:

1. **Spike S0** (the only Next task): promise sentence, fill four Wave 1 cards, one claim sentence under every heading in `sase_blog_contents`, 2 🍅 hard stop.
2. **Four zero-drafts**, each "dictate ≥150 words under its heading, no editing": Agent CLIs, Agent presentation / "Why a TUI?", Gates → Plans → Epics, Xprompts / control flow.
3. Each zero-draft already carries a **CARD**: 😈 current pain · 😇 SASE move · PROOF · LESSON.
4. **Wave 1 review** then decides full section / series-map paragraph / *cut* for five other headings.
5. Intro is written last.

`## Requirements` on the same note is already the fleeting-note inbox: quotes, screenshots, GasTown comparisons, "optimal experience not optimal performance," stick-figure art, AI-slop categories. A 2026-09-01 bullet even quotes the r/Zettelkasten thread on hub notes versus structure notes — Bryan already knows that a hub/index and a structure/outline are different from main notes.

The S0 work log from today is `apollo research on creating new sase_blog_zettel album!`. This research is currently standing in for the promise sentence.

### The public blog already has a launch post and a series

The SASE repo already publishes a launch post and holds nine drafted follow-ups.

| File under `docs/blog/posts/` | Status | Role |
| --- | --- | --- |
| `structured-agentic-software-engineering.md` | **live** on https://sase.sh/blog/ (~2882 words) | Technical front door: wraps CLIs, Macros, Agents tab, install |
| `why-coding-agents-need-orchestration.md` | draft `[00]` | Series opener |
| `macros-in-depth.md` | draft `[02]` | |
| `axe-background-daemon.md` | draft `[03]` | |
| `beads-and-sdd.md` | draft `[04]` | Matches `sase_blog` "Later Posts → Beads and SDD" |
| `commit-workflows-plugins.md` | draft `[05]` | |
| `changespecs-in-practice.md` | draft `[06]` | Matches "ChangeSpec" |
| `telegram-mobile-agents.md` | draft `[07]` | Matches "Mobile" |
| `prompt-widget-and-nvim.md` | draft `[08]` | |
| `whats-next-memory-mobile-web.md` | draft `[09]` | Matches "Memory" / "Mobile (and Web?)" |

The live post already uses 😈/😇 bullets, `tmux_ai_window`, and a "What's Next" that points at later posts. The vault article is a *second* front door: personal voice, "why I use / what is / why you should not." That is a rewrite or companion, not a blank page.

`sase_blog.md` "Later Posts" already lists Beads and SDD, Memory, Mobile, ChangeSpec, Architecture. Those are posts, not sections. If any album belongs in this neighborhood, it catalogs **those**, not heading 2.3.1 of the current outline.

## Critique of the proposed plan

### 1. One record per section is not a zettelkasten

Andy Matuschak: evergreen notes should be **concept-oriented**, not organized by book, project, or topic. Notes titled after outline headings ("2.3 Agent CLIs") do not accrete. The next time "optimal experience not optimal performance" comes up, it is buried inside a section file instead of being a reusable claim.

Sönke Ahrens (*How to Take Smart Notes*): permanent notes are one idea each, written in full sentences. When it is time to publish, you pull related notes, rearrange them, and **write a rough draft**. The notes help develop the argument; they are not themselves the argument. Concatenating section files skips the draft step the method still requires.

Bryan's own Requirements quote from r/Zettelkasten: a hub note stays a thin index; turning it into a structure note fills it with commentary that does not belong in the main notes. `sase_blog_zettel.md` as an album of section files is a structure note wearing an album header.

The Wave 1 cards are the actual zettels:

- "one CLI at a time" → "every provider behind one harness"
- "tmux_ai_window" → "one screen for every agent"
- "Plan mode is the canonical example of some deeper primitive" → "gates → plans → epics"
- `%wait` / `#fork` → "loop vs graph engineering"

Those are concept-sized. "§2.3 Agent CLIs" is outline-sized.

### 2. Rearrangement gets harder, not easier

The pitch is that the blog becomes "mostly just re-arranging content already written." For this post, the opposite happens.

| Mechanism | Article manuscript | Record-per-section |
| --- | --- | --- |
| Reorder | Cut/paste a heading; `bob articles format` renumbers | Rename files, rewrite parents, rebuild index; order is not a first-class field |
| Rename a heading | Edit the heading; heading-identity capture still matches | Filename stem is computed from title at create; collisions refuse a suffix |
| Cut a section | Wave 1 already plans this for five headings | Orphan record, or a `cut` status that still occupies the catalog |
| Connective tissue | Written between headings in one voice | Has to be invented at compile time; collage voice |
| Progress | `bob articles outline` stubs and word counts | Album index grouped by status, not reading order |
| Capture | `@sase_blog_contents#agent` | `@sase_blog_zettel/` plus field bullets |

Album indexes group by `status` (and `index_by` only inside groups larger than 12). A 15-section album would read "4 drafts · 11 ideas," not "1, 2, 2.1, 2.2." Document order is exactly what `bob articles outline` already prints.

### 3. The outline is still moving, and the numbers already drifted

The user said the outline is not finalized. The vault proves it.

Wave 1 tasks were numbered as §1.1, §1.3, §1.3.2, §1.5 when "What is SASE?" was section 1. The article now has **1. Why I use SASE** and **2. What is SASE?**, so those same headings are 2.1, 2.3, 2.3.2, 2.5. Capture to the article still works because it matches identity, not the number. Records keyed to "1.3 Agent CLIs" would already be stale.

Wave 1 review will cut or shrink §1.2 / §1.3.1 / §1.4 / §1.6 / §1.7 (old numbers). Pre-creating 15 records from today's outline invests in headings the current plan expects to drop.

### 4. Record bodies are note bullets, not essay prose

Bob's record writer always emits:

```markdown
# Title

## Notes

- first bullet
```

Capture treats first-level `key:: value` as fields and other first-level bullets as notes. Updates append under `## Notes`. ALL-CAPS bullets can become extra H2s, still filled with bullets. Long-form paragraphs are not the supported path. `record_checkbox` errors because "records hold facts, never tasks."

The zero-draft instruction is "dictate ≥150 words under its heading, no editing." That is a paragraph dump into an article section. Dumping it into `## Notes` bullets either fights the record shape or produces a listicle that still has to be rewritten into the article.

Notebooks are worse for this job: they are task-free bullet collections, and `notebook_shape` warns on stray top-level paragraphs. Notebooks are for observations. Articles are for essays. Records are for things.

### 5. Three sources of truth are already too many

Today the same essay exists as:

1. The live sase.sh launch post in `docs/blog/posts/structured-agentic-software-engineering.md`
2. The vault article `sase_blog_contents.md`
3. The project kitchen `sase_blog.md` (cards, requirements, screenshots)

Adding `sase_blog_zettel/` with one file per heading is a fourth store. Transcluding records into the article (`![[sase_blog_zettel/agent_clis]]`) would hide the prose from `bob articles` outline, stub detection, and numbering, which all read one note's body. Compiling by hand re-creates the "just rearrange" step the plan claimed to delete.

### 6. Naming and parent rules fight the idea

- Album parent must be an **area or project**. `sase_blog.md` is a project, so it is the right parent if an album exists. A new album named `sase_blog_zettel` is not a parent of records in the colloquial sense until it itself hangs off `sase_blog` or `sase`.
- Album stem = folder = route. `@sase_blog_zettel/` is a clumsy capture route for dictation.
- `article` is a reserved record noun. The album cannot call its records "articles."
- Record parents are album-only (k3.7.1.5). They cannot parent to the article, the project, or a notebook.
- "Zettel" in the filename promises evergreen atomic notes. Outline-section files are the thing zettelkasten advice tells you not to create.

### 7. This is process-shopping on a stalled S0

S0 has been open since 2026-10-23. The article still has 15 stubs. The next action logged today is this research. A new album, a schema, 15 files, and a compile step are a larger machine than "write the promise sentence and four cards." The writing system on the project is blocked on starting, not on missing primitives.

## Writing methods, mapped onto Bob

| Method | Grain | Composition step | Bob home |
| --- | --- | --- | --- |
| Snowflake (Ingermanson) | Sentence → paragraph → outline → scenes | Expand in place; the one-sentence spine stays | S0 promise sentence + claim-per-heading in the article |
| Index cards / Wave 1 cards | One 😈/😇/PROOF/LESSON per section you will actually write | Dictate 150 words under the heading | Cards on `sase_blog` tasks; prose in the article |
| Zettelkasten / evergreen notes | One concept, reusable across essays | Pull notes, then write a new draft | Requirements bullets now; a real zettel would be a claim note, not a section file |
| Record album | One durable thing with a schema and a status | Catalog, filter, peek | `eat`, `podcasts`, `tv`, `movies` — and maybe later a *posts* album |

The current S0 + Wave 1 plan is already Snowflake plus cards, with the article as the scene list. That is the right method for a single personal essay with a deadline. A zettelkasten is the right method for a decade of claims that might feed many essays. A record album is the right method for a watch list.

Mixing them produces outline-shaped "zettels" stored as restaurant-shaped records.

## Requirement adjustments

These are deliberate changes to the request, not silent scope cuts.

1. **Drop "one record per section or topic."** Replace with "one claim sentence per heading in the article, and a CARD only for headings that survive Wave 1."
2. **Do not create `~/bob/sase_blog_zettel.md`.** If an album is created later, name it for *posts* (`sase_posts.md`, noun `post`), parent `sase_blog` or `sase`, never "zettel."
3. **Keep `sase_blog_contents.md` as the only manuscript.** Rearrangement happens inside that file. `bob articles format` owns numbering after moves.
4. **Treat the current outline as disposable.** Wave 1 already plans cuts. Do not materialize it as files.
5. **Treat `sase_blog.md` Requirements as the fleeting inbox.** Do not migrate those bullets into records in order to start writing.
6. **Do not wait on k3.11.** Album create already works; wrap-up is config retirement and glossary publish. Waiting on wrap-up is another stall. The glossary strands `album-note` and `record-note` are not published yet (authorized by k3, still assigned to `.11`).
7. **Do not compile the vault article by transclusion.** Publish by editing `docs/blog/posts/` in sase-org/sase when the vault draft is actually a draft, and decide then whether it replaces or sits beside the live launch post.
8. **Call the live sase.sh post what it is.** The `^prj` line asks for a post *in my own voice*. A technical launch post is already live. This vault essay is a rewrite or companion. That decision belongs in S0's promise sentence, not in an album schema.

## Alternatives considered

| Alternative | Verdict |
| --- | --- |
| Proposed: album `sase_blog_zettel` + one record per outline heading | Reject. Wrong type, wrong grain, outline not frozen, compile step is the hard writing. |
| Notebook of section bullets under `sase_blog` | Reject for the manuscript. Notebooks refuse the essay shape (`notebook_shape`, no checkboxes, bullets only). Fine later for leftover fragments, not for the post. |
| One article per section (`type: "[[article]]"`) | Reject. `bob articles` is designed for one long note. Fifteen articles lose the outline, numbering, and stub report that already exist. |
| Transclude records or notes into `sase_blog_contents` | Reject. Outline/stubs/numbering will not see embedded bodies. Two-way edit becomes a trap. |
| Status-schema records as *cards*, manuscript still the article | Acceptable fallback if cards outgrow the project note. Create a record when a card is filled, never 15 empty files from the outline. See the constrained recipe below. |
| Album of *posts* for the series | Accept later. This matches eat/podcasts/tv/movies: one durable object, status, URL, date. Do it after the personal post exists, using the nine repo drafts plus this essay. |
| Keep writing in the article with S0 + Wave 1 | **Recommend.** Already specified, already instrumented, already compatible with capture and `bob articles`. |

## Recommended solution

### Now: write the essay in the article

1. Open `~/bob/sase_blog_contents.md`. This file stays the manuscript.
2. Spend S0's two tomatoes on the three S0 exits, in order:
   - One **promise sentence** that also decides: rewrite of the live launch post, or companion "why I use SASE / why you should not."
   - Four Wave 1 **cards** (they already exist as task children; fill any holes, do not invent a new card format).
   - One **claim sentence** under every heading, including headings Wave 1 might cut. A claim is enough to keep or kill a heading. Empty `TODO` is not.
3. Zero-draft the four Wave 1 headings *in the article*. Dictate 150+ words under the heading. Use `@sase_blog_contents#gates` / `#agent` / `#tui` / `#xprompt` when capture is more convenient than typing. Do not edit during the dump.
4. At Wave 1 review, cut in the article. `bob articles outline` will show which headings are still stubs. `bob articles format` will renumber what remains.
5. Write the intro last, as `^intro-v1` already says. The 190-word lede can stay; it only needs the promise sentence and the stats caveat.

No new note type. No new folder. No schema. The rearrangement step is ordinary editing in the one file `bob articles` already knows.

### Later: an album of posts, if the series needs a shelf

After this essay is a real draft (not 15 TODOs), and only if the series is hard to see from `docs/blog/posts/` plus `sase_blog.md` "Later Posts":

```sh
bob albums create sase_blog sase_posts \
  -n post \
  -s 'SASE essays: published, drafting, or cut.' \
  -e '✍️' \
  -t 'SASE posts'
```

Suggested `record.fields` (add after create, before the first record):

- `status` required, actionable first: `drafting` ✍️, `rewrite` 🔁, `published` ✅, `cut` ✂️
- `slug` text (the sase.sh slug)
- `url` url
- `published` date
- `wave` optional text (`launch`, `series`, `voice`)

Seed from objects that already exist: the live launch post, the nine drafted repo posts, and `sase_blog_contents` as the in-own-voice rewrite. Capture is `Title @sase_posts/` with `status:: drafting`. The album index then does what album indexes are for: **how many posts are live, how many are drafts, what to finish next.**

That album must not contain section files.

### Constrained fallback: cards as records

If the four cards plus Requirements become too large for `sase_blog.md` *after* S0, a cards album is still better than a sections album:

- Parent: `sase_blog`
- Stem: `sase_blog_cards` (not `zettel`)
- Noun: `card` (not `article`, not `zettel`, not `section`)
- Fields: `status` (`idea` / `card` / `zero` / `cut`), `wave` (`1` / `2` / `later`)
- Body: the CARD bullets only
- Create a record when a card is filled, never from the outline in bulk
- Prose still lands in `sase_blog_contents.md`

I would not build this until the project note is actually overcrowded. Today it is not.

## What success looks like

- `bob articles outline sase_blog_contents` shows a promise in the lede, a claim under every heading, and ≥150 words in the four Wave 1 sections.
- `bob ready sase_blog` is back under the S0 cap of 5.
- Zero new album appears in `bob albums list` until there is a second post to catalog.
- The live sase.sh launch post is cited, not ignored: the vault essay either replaces it or stands beside it on purpose.

## Sources

**Vault (read 2026-11-12):**

- `~/bob/sase_blog_contents.md` — article manuscript, 15 stub sections, 301 words
- `~/bob/sase_blog.md` — project, S0/Wave 1 tasks, Requirements, Later Posts
- `~/bob/sase.md` — parent project; `## Notebooks` already lists `sase_ideas`
- `~/bob/why_sase.md` — superseded precursor of the article
- `~/bob/sase_blog_0_legacy_notes.md` — earlier outline, already discarded
- `~/bob/eat.md`, `~/bob/podcasts.md`, `~/bob/eat/ani_ramen_house.md` — live album/record shape
- `~/bob/_templates/new_article.md`, `~/bob/article.md` — article type

**Bob commands (run 2026-11-12):**

- `bob articles list` / `outline sase_blog_contents` — 15 sections, 15 stubs, 4 pseudo-footnote findings
- `bob albums list` / `bob records list` — four albums, 152 records, all thing-catalogs

**bob-cli (this checkout):**

- `docs/records.md` — album/record contract, `## Notes` writer, `album_holds_no_tasks`, schema
- `docs/articles.md` — numbering, stubs, `bob articles outline`, capture heading identity
- `docs/notebooks.md` — notebooks are bullet collections, not essays
- `docs/capture.md` — `@sase_blog_contents#agent` heading-identity example
- `src/native/records/check.rs` — `record_checkbox`: "records hold facts, never tasks"

**Beads and plans (audited):**

- `bead:bob-cli-k3` — albums epic, in progress at `.11` wrap-up
- `plan:202611/album_and_record_notes.md` — accepted album/record design
- `research:202611/album_and_record_notes/album_and_record_notes.md` — records are schema-backed things; albums-as-notebooks rejected
- `bead:bob-cli-k3.7.1.5` — record parents = album only; album parents = area/project
- `bead:bob-cli-k3.9` — vault cutover closed; `bob albums create` is live
- `bead:bob-cli-k3.11` — glossary strands not published yet

**sase-org/sase (opened as `gh:sase-org/sase`):**

- `README.md` — public positioning; blog link
- `docs/blog/index.md` — blog home
- `docs/blog/posts/*.md` — one live launch post, nine drafts
- https://sase.sh/blog/ — launch post is public

**Writing methods (not in Bryan's `ref/` library; recommended only as method citations, not as new reading for S0):**

- Andy Matuschak, [Evergreen notes should be concept-oriented](https://notes.andymatuschak.org/z2hQEhqWkdRLL9JUwfawZZx)
- Sönke Ahrens, *How to Take Smart Notes* — notes develop the argument; the manuscript is a new draft (Forte Labs / Shortform summaries of the eight steps)
- Randy Ingermanson, [The Snowflake Method](https://www.advancedfictionwriting.com/articles/snowflake-method/) — sentence → paragraph → outline → scenes
- r/Zettelkasten, [Where do hub and structure notes go?](https://www.reddit.com/r/Zettelkasten/comments/1h443i2/where_do_hub_and_structure_notes_go_in_a/) — already quoted on `sase_blog` Requirements

Library check: 0 of 11 writing-method / sase.sh candidates are in `ref/` (0 finished). S0's own instruction is "No new reading." Do not queue these books to start the post.

## About this report

Independent researcher `grk` in the 2026-11-12 swarm on using record notes for the SASE blog. Did not read peer swarm reports. This is research, not a vault edit and not an implementation.
