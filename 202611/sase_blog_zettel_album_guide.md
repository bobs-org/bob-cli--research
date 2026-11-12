# Draft the SASE blog in claim-sized zettels

_Your album is set up and validated as of 12 November 2026. It is intentionally empty: the approved setup created no seed records._

## 1. What this album is (and is not)

Treat the SASE Blog Zettel album as a workbench for claim-sized drafts. The article, <code>sase_blog_contents.md</code>, remains the manuscript, the spine, and the only authority for order and transitions. The album is an inventory of material; it is never a second outline.

Make one record per topic or claim, not one per article section. Several records may feed one section, and some records may never ship. The outline is still candidate coverage, so combine, split, add, or drop topics as the argument takes shape.

“Mostly rearranging” is an illusion. Plan for a real rewrite pass in the spine to find your voice, add transitions, and remove repetition. The <code>^v1-draft</code> task remains a writing task.

## 2. The schema, field by field

The root note <code>sase_blog_zettel.md</code> owns the record schema. Its top-level <code>index_facets: [part, claim]</code> key displays those facets; neither controls article order.

| Field | How to use it |
| --- | --- |
| <code>status</code> | 🌱 Seed → ✍️ Draft → ✅ Ready → 📌 Placed. Use ⏭️ Later for a future post and ✂️ Cut for material you are dropping but keeping. |
| <code>claim</code> | Required. State the record’s point in one sentence. If you cannot state it, it is not a topic yet; add the idea to an existing record’s Notes. |
| <code>part</code> | Display facet only: <code>hook</code>, <code>why</code>, <code>what</code>, <code>why_not</code>, or <code>close</code>. It is a rough reader-facing grouping, never an ordering field. |

There are no <code>order</code>, <code>section</code>, <code>wave</code>, or <code>target_words</code> fields. The article spine owns order, and the outline stays provisional.

Use these exit criteria:

- **🌱 Seed:** a title and a real one-sentence claim.
- **✍️ Draft:** at least 150 unedited words in <code>## Draft</code>. Get the thought down before polishing.
- **✅ Ready:** revise the draft, check names and facts against the current <code>sase</code> HEAD (Macros, not Xprompts; Patches, not ChangeSpec), and resolve its links and images. Ready means usable material, not a promise to include it.
- **📌 Placed:** paste the material into the spine. From then on, edit only the article; this is a one-way fork with no back-sync.
- **⏭️ Later:** keep it for a future post.
- **✂️ Cut:** drop it from this post but retain the record.

The album uses dated Notes. <code>bob capture</code> supplies the date when it appends a note. There is no default status, so provide one when creating a record.

## 3. Record body convention

Bob creates the title and <code>## Notes</code> section. Add <code>## Draft</code> yourself; only that section ever ships.

    # One CLI behind every provider

    ## Draft

    Write the claim out in your own voice. This is the only section to paste into the article.

    ## Notes

    - 2026-11-12: 😈 pain · 😇 SASE move
    - 2026-11-12: PROOF screenshot path or source

Keep quotes, ideas, screenshots, proof, and CARD material in <code>## Notes</code>. Capture appends dated bullets there. Never add a checkbox to a record: actions belong as tasks in <code>sase_blog.md</code>, linked to the record.

## 4. Capture cheatsheet

For a new zettel, route the title to the album and supply its required fields. Use a lowercase hyphenated filename stem after <code>^</code>; replace the claim prompt with your actual sentence before writing.

    bob capture --dry-run --no-clip <<'EOF'
    What is SASE? @sase_blog_zettel/^what-is-sase
    - status:: seed
    - claim:: <one-sentence claim>
    - part:: what
    EOF

To append an idea to that record’s Notes after it exists:

    bob capture --dry-run --no-clip 'Add one supporting idea @sase_blog_zettel/what-is-sase'

The append preview was exercised as a second item after a staged record creation in one dry-run. <code>status::</code> and <code>part::</code> take the field keys shown above. For an existing zettel, the same append can be previewed on its own.

The command-line equivalents are useful when you prefer explicit record operations:

    bob records new zettel 'What is SASE?' --stem what-is-sase --set status=seed --set claim='one-sentence claim' --set part=what --dry-run
    bob records update zettel what-is-sase --note 'Add one supporting idea' --dry-run

Remove <code>--dry-run</code> only when you are ready to write. <code>update</code> takes an existing filename stem; it can append Notes or change only the fields you supply.

### Candidate-coverage batch template

The outline is not final. This ready-to-fill template covers its current candidate topics; it does not set your final record count or article order. Replace every <code>TODO</code> with a real claim before running it. Do not capture placeholder claims.

    bob capture --dry-run --no-clip <<'EOF'
    {0} @sase_blog_zettel/^candidate-{1} %t
    - status:: seed
    - claim:: {2}
    - part:: {3}

    "Hook" hook "TODO — fill with one claim" hook
    "Why I use SASE" why-i-use "TODO — fill with one claim" why
    "What is SASE?" what-is-sase "TODO — fill with one claim" what
    "Gates → Plans → Epics" gates-plans-epics "TODO — fill with one claim" what
    "Beads → Sidecar repos" beads-sidecars "TODO — fill with one claim" what
    "Agent CLIs" agent-clis "TODO — fill with one claim" what
    "Skills, memory, provider interface" skills-memory-provider-interface "TODO — fill with one claim" what
    "Agent presentation / organization" agent-presentation "TODO — fill with one claim" what
    "VCS and workspace operations" vcs-workspaces "TODO — fill with one claim" what
    "Macros / agent control flow" macros-control-flow "TODO — fill with one claim" what
    "Project management" project-management "TODO — fill with one claim" what
    "Routines and jobs" routines-jobs "TODO — fill with one claim" what
    "My definition of AI slop" ai-slop-definition "TODO — fill with one claim" why_not
    "Future work" future-work "TODO — fill with one claim" why_not
    "Conclusion" conclusion "TODO — fill with one claim" close
    EOF

The batch uses Bob’s <code>%t</code> template: each row supplies title, filename stem, claim, and display facet. Keep or discard candidates based on the article you are writing. This command is a preview; after replacing every TODO and checking the diff, remove <code>--dry-run</code> to create the chosen records.

## 5. One home per kind of material

| Material | Home |
| --- | --- |
| Idea, quote, screenshot path, or proof for a topic | That record’s <code>## Notes</code> |
| Prose in your voice | That record’s <code>## Draft</code> |
| Order, headings, transitions, intro, and promise | <code>sase_blog_contents.md</code> |
| Post-wide style and production rules | <code>sase_blog.md</code> → <code>## Requirements</code> |
| Work items | Tasks in <code>sase_blog.md</code>, linked to the records |

Triage the roughly 44 existing Requirements bullets lazily, one topic at a time. When drafting a topic, move only its relevant bullets into that record’s Notes. Do not migrate the Requirements list up front.

## 6. Revised S0 checklist

Timebox S0 to **one 🍅 total, then stop**.

1. The album and schema are ready; setup is done.
2. Create one zettel per topic you choose, with a real claim, using one batch capture. Start from the candidate template above, but remove candidates that do not earn a place.
3. Move the four Wave 1 CARD bullets into their records’ <code>## Notes</code>. Point each <code>zd-*</code> task at its record. Keep the task exit criteria, now aimed at <code>## Draft</code>.
4. Add the record links under the relevant article headings in the spine.
5. Write the promise sentence. Decide whether this post replaces or accompanies the July launch post; that choice determines what belongs in ⏭️ Later or ✂️ Cut.

Then stop. Dictating the four zero-drafts is the next writing work.

## 7. Assemble and publish from the spine

Under each relevant article heading, add the records that feed it:

    → [[sase_blog_zettel/<stem>|Title]]

Reorder the article by moving headings and their link lines in <code>sase_blog_contents.md</code>; <code>bob articles</code> renumbers and repairs heading links. Write transitions directly in the spine. It owns the argument and the final wording.

Assemble early, after Wave 1, rather than waiting for every record to reach Ready. Paste the useful Draft sections into the spine, read the incomplete whole, and look for gaps, repetition, and terminology drift while cuts are cheap. Mark pasted records 📌 Placed. After that one-way fork, edit only the article.

Budget the rewrite pass even after pasting: make the voice consistent, join the pieces, and remove duplicate explanations. Before publishing, check facts and names against current <code>sase</code> HEAD again.

Publish by copying the finished article into <code>docs/blog/posts/&lt;slug&gt;.md</code> in <code>sase-org/sase</code>. Convert Obsidian wikilinks, callouts, embeds, and footnotes, then run <code>mkdocs build --strict</code>. Do not build an exporter now; revisit one only after two posts have shipped this way.

## 8. Fallback triggers

Article-only writing is a fully successful outcome. Fall back if setup ever costs more than one 🍅, or if after Wave 1 most pieces feel inseparable and switching files hurts more than it helps. Continue in the article and keep records only for examples or claims that you expect to reuse.

## 9. Open questions for you

- Does this post replace or accompany the July launch post? Decide in the promise sentence.
- Keep <code>claim</code> required, or relax it if it blocks capture flow?
- Does “zettel” over-promise for topic drafts? Keep the name or rename the album.

## 10. Research and known issue

For the rationale and alternatives, see the [consolidated research report](sase_blog_drafting_in_records/sase_blog_drafting_in_records.md).

The cosmetic <code>1 zettels</code> tally bug is known and tracked on <code>bob-cli-k3</code>; expect that wording once the first record is created. It does not affect the schema or record checks.
