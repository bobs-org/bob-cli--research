# SASE blog records: a source album, a flexible manuscript, and an early assembly test

Independent research by **cdx**, 2026-11-12.

**Recommendation:** use `sase_blog_zettel.md` as a project-specific album of writing pieces, owned by `[[sase_blog]]`. Keep `sase_blog_contents.md` as the Article Note that owns the argument, inclusion, sequence, and eventual publication prose. Begin with the four pieces already selected in the blog project, assemble an incomplete draft early, and revise across the seams. This is a good way to reduce the blank-page problem. It will not reduce the final writing task to rearrangement alone.

This report is research, not an implementation: no live vault notes, schemas, tasks, or product code were changed. I did not read any other report, chat, or findings from this research swarm.

## What I checked

I read the audited `bob-cli-k3` epic and its accepted plan, `plan:202611/album_and_record_notes.md`; the current Bob record, album, capture, and article contracts and implementation; the blog outline and its parent project; current SASE documentation; and primary sources on linked notes, composition, and Obsidian. I also exercised the proposed schema and relevant CLI paths in disposable local fixtures.

Repository snapshots:

- bob-cli: `4ed4fdabf33d065d516dcdfb8fe4785503f35726`.
- Bob vault: `1e89bf261a77798349340d718a5fd9c75053eaaa`.
- sase-org/sase: `1087ccd7f15f09f9cd2267a4cef598a1219432ca`.
- Installed CLI used for the fixture probes: `bob 0.5.0`; this version string alone does not prove it is the same build as the inspected source checkout.

The vault inputs were read from a fresh, SASE-opened repository checkout. That gives a reproducible synced snapshot of `~/bob/sase_blog_contents.md` and `~/bob/sase_blog.md`, but does not establish that there are no newer unsynced local edits. The epic was still in progress: phases 1–10 were closed, while wrap-up phase 11 remained in progress. The recommendations rely on observed capabilities, not an assumption that every epic promise has shipped everywhere. [Album epic][epic]

## The existing setup is closer than the proposal suggests

The outline is already `type: "[[article]]"`, with `parent: "[[sase_blog]]"`. It contains a personal introduction followed by Why I use SASE; What is SASE, with seven feature-oriented subsections; Why you should probably not use SASE; and Conclusion. Its opening voice and existing paragraphs are valuable authored material, not scaffolding to discard. [Outline snapshot][outline]

The parent `sase_blog.md` is already a project under `sase`, marked `root: true`. Its completion criterion explicitly calls for a post in Bryan's own voice. More significantly, it already selects a first wave: Agent CLIs, the TUI, Gates/Plans/Epics, and Xprompts/control flow. Those tasks include concrete incidents, screenshots, contrasts, and lessons. There is already a review step deciding which remaining topics deserve sections, short mentions, or removal. Some task descriptions still use earlier section numbers; links to record identities would be more durable than those numbers. [Blog project snapshot][project]

Therefore, a new album should be a storage and writing aid for the existing project, not another project with another outline and another task backlog. Its correct owner is `[[sase_blog]]`, not the article, not another album, and not necessarily the broader `[[sase]]` project.

The SASE repository already contains a substantial front-door blog article and additional draft posts. Treat these as existing source material and editorial overlap to review, not as proof that the requested personal essay is already finished or that their prose is Bryan's desired voice. The source article explicitly records the xprompt-to-macro terminology change. There is little value in reproducing a feature manual when the distinctive contribution can be Bryan's experience, decisions, failures, and tradeoffs. [Existing article][existing-post]

## Is writing in records a good idea?

Yes, with a narrower promise: **develop reusable explanations independently, then compose a reader's journey from selected material**.

A record is a reasonable representation of one durable explanation, incident, example, or argument. Writing the complete thought forces more progress than collecting bookmarks. A schema can make unfinished work visible, and discarding a section from this post need not discard the useful explanation. This fits an outline that is still changing.

The useful unit is not necessarily a final section. A section can draw on several records, and a record can supply one paragraph, an example, or nothing to the final version. Conversely, an inseparable explanation should remain one record rather than being fragmented into a dozen sentences. Andy Matuschak's own account of atomic notes describes this balance between independent reuse and excessive fragmentation. His concept-oriented approach favors ideas over project/topic containers; the proposed album borrows that useful property without pretending that a single-post collection is a lifelong Zettelkasten. [Atomic notes][atomic] [Concept-oriented notes][concept]

The weakest part of the original plan is “finish one record for each topic,” then mostly rearrange. That can postpone the most important discovery: which ideas actually belong in this essay. Independently polished pieces also tend to repeat introductions, assume different background knowledge, change terminology, and disagree about the central promise. Selection, transitions, explanatory order, cuts, and rewriting remain substantial work.

Harvard's writing guidance recommends deriving an argument from a thesis and using a reverse outline of the draft to expose gaps, duplication, and misplaced points. This supports testing the whole piece while its parts are still provisional. It is practical guidance, not experimental proof that this specific album workflow will make Bryan faster. [Organizing an essay][harvard]

Scrivener provides a useful design comparison: a card corresponds to a document, and arranging cards updates the manuscript hierarchy. The lesson to borrow is the explicit relationship between pieces and composition. Bob's generated album inventory does not supply that relationship. There is no need to adopt another application to get the benefit here. [Scrivener corkboard][scrivener]

| Approach | What it gives you | Main cost | Fit here |
| --- | --- | --- | --- |
| Continue directly in the existing Article Note | Immediate sense of flow; almost no setup | Independent material is harder to browse and reuse | Best fallback if separate files slow drafting |
| Project album plus the existing article | Named pieces, status, capture, flexible reuse, a coherent final draft | Requires explicit assembly and one authority for each stage | Recommended |
| General evergreen-note system first | Reuse across many future projects | Taxonomy, migration, and linking work before this essay progresses | Defer until reuse becomes an observed need |
| A writing suite or custom compilation system | Strong ordering/export facilities | Migration or engineering effort | Unnecessary for the first pilot |

## Requirements I would change

These are proposed adjustments, not assumptions about previously accepted requirements.

| Original or implied requirement | Proposed adjustment | Reason |
| --- | --- | --- |
| One record for each section/topic | One record for each useful writing piece; allow many-to-one and partial use | The final outline should follow the argument rather than the file inventory |
| Finish all records before writing the post | Assemble after the first small wave, while some sections are still missing | Detect structural problems before polishing discarded material |
| Finish a record once | Use reversible `seed`, `draft`, and `ready` maturity states | Readiness means useful for assembly, not immutable or published |
| Album as the organizing parent | Keep that parent, and give the album `parent: "[[sase_blog]]"` | Uses the existing project and satisfies album ownership |
| Rearrangement is most of the remaining work | Budget an explicit synthesis pass | The final product needs one voice, shared context, and transitions |
| Every outlined feature deserves coverage | Treat the outline as candidate coverage; record deliberate cuts | A product catalogue is not automatically a compelling personal essay |
| New writing infrastructure may be needed | Start with existing records, article formatting, and optional embeds | Current capabilities cover the pilot; tooling should follow observed friction |

## A concrete design using current Bob behavior

### Separate collection, work, and publication

The relationships would be:

```text
sase_blog.md                         existing project: purpose and writing tasks
├── sase_blog_zettel.md              new album: schema and generated inventory
│   └── sase_blog_zettel/*.md        records: explanations, examples, evidence
└── sase_blog_contents.md            existing article: argument and final prose
```

A record has one parent; appearing in another article does not require changing that parent. Use links for reuse. Keep every record directly in `sase_blog_zettel/`, rather than nesting folders by proposed section. The record collection is scoped structurally by the album folder. Album nouns are unique across the vault, which is why the example below uses `sase_blog_idea` rather than assuming a generic noun such as `idea` is available. [Bob record contract][bob-records]

The generated `[!records]` callout is Bob-owned. It groups by a choices-based `status` field and sorts titles within the relevant groups; `index_by` can introduce subgroups for larger groups, not arbitrary essay order. Do not manually rearrange that callout, prefix filenames with section numbers, or maintain a competing `position` property. The authored order of sections and references in the article is the single source of narrative order. [Grouping implementation][grouping]

Put a short brief and links to the article and Base outside the generated callout. Keep the album small enough that opening it answers “what material do I have?” rather than becoming another manuscript.

### Minimal schema

This is a proposed final album configuration, not a file created by this research:

```yaml
---
parent: "[[sase_blog]]"
type: "[[album]]"
summary: Claims, examples, and evidence for my SASE post.
emoji: ✍️
index_facets: [topic]
record:
  noun: sase_blog_idea
  label: Blog idea
  plural: blog ideas
  dated_notes: false
  fields:
    status:
      required: true
      values:
        seed: 🌱 Seed
        draft: ✍️ Draft
        ready: ✅ Ready to assemble
    topic:
      suggest: true
---
```

Only status is required. Topic is optional free text for finding related material; it is not a frozen outline category. Do not start with fields for section number, word budget, importance, publication order, citation objects, or half a dozen quality scores. Keep the claim and evidence in readable prose.

Bob explicitly disallows a default for `status`; capture must supply it. Record field storage shapes must agree across albums, so check the actual vault before deploying even this small schema. `status` here is record metadata; it is not a task checkbox or a task lane. [Schema rules][bob-records]

Use these meanings:

- `seed`: a thought, question, or incident worth developing.
- `draft`: explanatory prose exists but still has a material gap.
- `ready`: the piece makes a clear point, has an example or appropriate evidence, and names its important limitation; it can be tried in an assembly.

Inclusion is separate from maturity. A ready record can be left out. Its omission from the article is enough; no `included` flag or compulsory `published` transition is needed.

### Record content and creation

Create through Bob, then write paragraphs in Obsidian. The current writer creates an H1 and `## Notes`; its note arguments append bullets, not an automatically templated essay. A body-only Obsidian template or a small manual paste can add the other headings once, without duplicating the existing `## Notes`. Core Templates supports inserting snippets into the active note. [Record rendering][bob-records] [Obsidian Templates][templates]

Suggested record shape:

```markdown
---
parent: "[[sase_blog_zettel]]"
type: "[[record]]"
title: "Switch providers without reconstructing the work"
status: draft
topic: "providers"
created: 2026-11-12
---

# Switch providers without reconstructing the work

## Claim

One sentence stating the point this piece is trying to establish.

## Prose

The explanation in my own words, with enough context to stand alone.
Use paragraphs; include a concrete incident and its limitation.

## Evidence

- Source or screenshot, what it establishes, and when it was checked.
- Separate observed behavior, documented behavior, and personal judgment.

## Notes

- Questions, objections, related records, and scraps that are not publication prose.
```

This is a writing convention, not a new Bob schema extension. Source inspection and a CLI fixture show that a status update preserves authored prose and extra headings, and that a record with these sections passes `records check`. There is no need to mark the record as both `record` and `article`: the article formatter refuses mixed note kinds. Keep the record identity and format the assembled Article Note instead. [Article contract][articles]

Records and albums may not contain task checkboxes. Actions such as finding a screenshot or checking a claim belong in `sase_blog.md`, linked to the relevant record. In a record, unanswered questions can be plain bullets. The current checker explicitly diagnoses real checkbox rows outside fenced examples. [Record checker][record-check]

A capture draft can be:

```text
Switch providers without reconstructing the work @sase_blog_zettel/
- status:: draft
- topic:: providers
- A concrete incident goes here.
```

The trailing slash is significant: it creates a record. The bare album route is not a place to capture a task. After creation, use the actual generated stem to update that record. [Capture contract][capture]

For a later implementation, this command previews album creation:

```sh
bob albums create sase_blog sase_blog_zettel \
  -n sase_blog_idea -l 'Blog idea' \
  -s 'Claims, examples, and evidence for my SASE post.' \
  -t 'SASE blog ideas' -e '✍️' -d
```

Removing `-d` would create the album, starter Base, and affected owner-catalog rows. Creation does not install the custom fields above: add those separately through the supported schema editor/update path or carefully edited album YAML, then check the result. Preview existing-path and noun conflicts first. There is no reason to add a `records:` block to machine configuration. [Album creation contract][bob-records]

### Assembly and the source-of-truth transition

Keep the personal opening and the evolving headings in `sase_blog_contents.md`. Under a heading, either place a normal link with a one-line purpose statement or embed the record's prose section:

```markdown
## Agent CLIs

![[sase_blog_zettel/switch_providers_without_reconstructing_the_work#Prose]]

A transition explaining why supervision becomes the next problem.
```

Obsidian supports live note, heading, and block embeds. That is enough for an early read-through without copying text. It does not establish portable Markdown publication, and an embed preview may retain source-section framing that you will remove in the manuscript. [Obsidian embeds][embeds]

Use heading-targeted embeds, not whole-record embeds that mix prose with evidence notes and private drafting comments. Keep `## Prose` unique in each record. Do not rely on the article formatter to expand embeds or infer their word count; it owns numbering, layout, and links, not manuscript compilation. Native Bases can provide property-based views for browsing and editing maturity, but should not own publication order. [Article contract][articles] [Obsidian Bases][bases]

Once the first complete argument exists, materialize the selected prose into the article and make **that article the authority for this publication's wording**. Copying is an intentional fork at this boundary, not an ongoing two-way sync. Keep provenance links in the source material or a short assembly note; bring worthwhile later insights back to the records deliberately. Do not regenerate over the edited manuscript.

Before publishing, resolve embeds, convert vault-only links, copy and check images, reconcile citation/footnote identifiers, remove private notes and TODOs, and review one uninterrupted rendered article. The outline currently uses reference-style definitions such as `[1]: TODO ...`; Bob already has a `pseudo-footnote` diagnostic for this class of unfinished syntax. Actual public footnotes should use the target site's supported syntax. [Article findings][articles]

## Apply it to this outline, without freezing it

Use the existing four-card wave. Do not automatically create a record for every heading. These are candidate record questions, not replacement titles Bryan must adopt:

| Existing material | First writing question | What an assembly should test |
| --- | --- | --- |
| Agent CLIs; outage/retry example | What did switching runtimes let me keep doing? | Is the benefit understandable before listing providers? |
| Agent presentation; terminal history and TUI demo | What information do I need to supervise several agents? | Can the concrete screen explain the organization without an early taxonomy lecture? |
| Gates → Plans → Epics; related-plan example | Which decisions need to survive the current interaction? | Does this explain a real workflow, rather than imply every task follows one mandatory chain? |
| Xprompts/control flow; alternations and stashes | Which repeated instructions became reusable workflows? | Does one real example establish the point before syntax detail? |

These four topics and their evidence leads already exist in the project; the screenshot files themselves were not inspected in this research. Their dates are historical and their existence, legibility, and correspondence to current behavior still need checking. [Blog project snapshot][project]

A provisional reader journey might be: personal motivation → a concrete coordination problem → one end-to-end example → the few mechanisms needed to explain it → costs and limits → who should try SASE and what to try first. This is an editorial hypothesis to test, not a finalized outline.

Specific adjustments worth trying:

- Keep the personal introduction as the human entry point. Follow it with one clear reader promise, rather than asking repository size to establish usefulness.
- Combine overlapping explanations of hoods, agent organization, artifacts, and project management where they answer the same reader question. Introduce specialized names only when the example needs them.
- Put workspaces and durable records near the point where the reader asks what survives concurrent work or an ended process. Current SASE docs explicitly separate sessions, isolated workspaces, durable state, and host-owned landing. [Agents concept][agents] [Landing concept][landing]
- Connect limitations to the earlier claimed benefits. Bryan's existing “optimal experience” emphasis is more defensible as a personal design aim than an unmeasured claim of universally better model performance. Keep the AI-slop discussion concrete: one failure mode, its cost, and what changed.
- Treat routines/jobs and detailed feature taxonomies as candidates for later posts if they do not strengthen the first article's promise. The album retains that material without forcing it into this post.

Record factual claims close to their evidence. The outline's commit count, line count, provider list, and “high-quality software at scale” language have different evidentiary burdens. Counts need a date, repository scope, and counting method; they do not demonstrate quality or productivity. A provider list is time-sensitive. A screenshot establishes a particular example, not a reliability rate. Do not “refresh” these claims by guessing. The current README describes SASE as alpha software; older blog copy and older requirements need checking against the intended publication version. [SASE README][sase-readme]

## Pilot and criteria for keeping this workflow

Use the existing spike and Wave 1 review rather than creating parallel work tracking. Begin with four seeds, draft one or two, and attempt an assembly before completing the rest. Keep the initial passes rough; the project's existing short, bounded drafting sessions are appropriate. This changes the storage location and the timing of synthesis, not the project's purpose.

Keep the workflow if the pilot demonstrates that:

1. A record is easy to create, find, and continue writing.
2. Its schema helps choose the next writing action without demanding extra bookkeeping.
3. Reordering or cutting a section does not require renaming or reparenting records.
4. An early assembly reveals a real gap, duplication, or change of emphasis.
5. There is an unambiguous point at which the article becomes the publication master.

If most pieces end up inseparable, or opening several files interrupts writing more than it helps, continue directly in the article and retain records only for reusable examples and research. That is a successful experiment, not a failed implementation.

No new CLI command or plugin is needed for this pilot. Only after manual assembly repeatedly becomes a material burden would I consider a narrowly scoped exporter. Its input should be the author's explicit ordered selection, never “all ready records” or album sort order. It should read designated prose sections, report missing targets, preserve code and citations, handle image/link paths, and produce a new preview with provenance. It must not overwrite the edited Article Note or write back into source records. These are criteria for a future design, not proposed work to undertake now.

## Verification and limits

Disposable fixture checks with `bob 0.5.0` produced these results:

| Check | Observed result |
| --- | --- |
| Minimal album schema under a project, including the final three-status example | `albums check -f json` exited 0; zero schema errors; expected missing generated-index/catalog warnings |
| Record creation with status/topic | `records new ... -d -f json` exited 0 and planned canonical record parent/type, a note, and its index update |
| Omitted required status | Exit 2 with an incomplete draft naming `status` |
| Record containing Claim-style/prose/evidence/notes content | A prose/evidence/notes fixture passed `records check` with zero errors and warnings |
| Status update over authored body sections | `records update ... -d` returned the unchanged prose body; fixture source bytes remained unchanged |
| Record capture using the proposed album route and fields | Dry run exited 0 with `kind: record_note` and the correct album owner |
| Album creation and synchronization | Dry runs produced expected new-album or index/catalog plans; authored brief text was preserved |

The fixtures were removed afterward. I did not perform live writes, GUI testing, publication export, or a measured comparison of writing productivity. I did not verify every real-vault property collision or the availability of the example evidence assets. The external writing sources provide design guidance and product behavior, not a causal estimate of this workflow's benefit.

## Sources

The local repository links below are pinned to the inspected revisions; the epic and plan are moving project records. External pages were accessed on 2026-11-12.

- [Album epic][epic]; audited plan identity: `plan:202611/album_and_record_notes.md`.
- [Blog outline][outline] and [blog project, tasks, and requirements][project].
- [Bob album/record contract][bob-records], [capture contract][capture], [group ordering][grouping], [record validation][record-check], and [article contract][articles].
- [SASE README][sase-readme], [agent/workspace concepts][agents], [landing concepts][landing], and [existing introductory article][existing-post].
- Andy Matuschak: [atomic notes][atomic] and [concept-oriented notes][concept].
- Harvard College Writing Center: [Tips for Organizing Your Essay][harvard].
- Literature & Latte: [Organize Your Scrivener Project with the Corkboard][scrivener].
- Obsidian Help: [embeds][embeds], [Bases][bases], [Templates][templates], and [Properties][properties]. Properties are small structured metadata, while nested schemas require Source mode or a suitable custom editing surface; this is another reason to keep long-form writing in the body.

[epic]: https://github.com/bobs-org/bob-cli--beads/blob/main/pages/bob-cli-k3/README.md
[outline]: https://github.com/bobs-org/bob/blob/1e89bf261a77798349340d718a5fd9c75053eaaa/sase_blog_contents.md
[project]: https://github.com/bobs-org/bob/blob/1e89bf261a77798349340d718a5fd9c75053eaaa/sase_blog.md
[bob-records]: https://github.com/bobs-org/bob-cli/blob/4ed4fdabf33d065d516dcdfb8fe4785503f35726/docs/records.md
[capture]: https://github.com/bobs-org/bob-cli/blob/4ed4fdabf33d065d516dcdfb8fe4785503f35726/docs/capture.md#record-notes
[grouping]: https://github.com/bobs-org/bob-cli/blob/4ed4fdabf33d065d516dcdfb8fe4785503f35726/src/native/albums/grouping.rs
[record-check]: https://github.com/bobs-org/bob-cli/blob/4ed4fdabf33d065d516dcdfb8fe4785503f35726/src/native/records/check.rs
[articles]: https://github.com/bobs-org/bob-cli/blob/4ed4fdabf33d065d516dcdfb8fe4785503f35726/docs/articles.md
[sase-readme]: https://github.com/sase-org/sase/blob/1087ccd7f15f09f9cd2267a4cef598a1219432ca/README.md
[agents]: https://github.com/sase-org/sase/blob/1087ccd7f15f09f9cd2267a4cef598a1219432ca/docs/concepts/agents.md
[landing]: https://github.com/sase-org/sase/blob/1087ccd7f15f09f9cd2267a4cef598a1219432ca/docs/concepts/landing.md
[existing-post]: https://github.com/sase-org/sase/blob/1087ccd7f15f09f9cd2267a4cef598a1219432ca/docs/blog/posts/structured-agentic-software-engineering.md
[atomic]: https://notes.andymatuschak.org/Evergreen_notes_should_be_atomic
[concept]: https://notes.andymatuschak.org/Evergreen_notes_should_be_concept-oriented
[harvard]: https://writingcenter.fas.harvard.edu/tips-organizing-your-essay
[scrivener]: https://www.literatureandlatte.com/blog/organize-your-scrivener-project-with-the-corkboard
[embeds]: https://help.obsidian.md/embeds
[bases]: https://help.obsidian.md/bases
[templates]: https://help.obsidian.md/plugins/templates
[properties]: https://help.obsidian.md/properties

## Recommended solution

Create the requested `sase_blog_zettel` album under the existing `sase_blog` project, with one record per useful writing piece and only maturity plus optional topic metadata. Use the four already-selected drafting cards as the pilot. Preserve `sase_blog_contents.md` as the Article Note and the sole authority for the evolving sequence; assemble early with explicit links or prose-section embeds, then materialize a complete draft and edit it as one essay. Keep tasks in the project and generated inventory under Bob's control. Invest in synthesis before export machinery: the goal is to make the ideas easier to develop and reuse while still producing a coherent post in Bryan's voice.
