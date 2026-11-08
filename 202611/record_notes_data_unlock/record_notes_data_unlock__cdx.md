# Record notes: the personal details worth keeping, and how they could pay off

Independent research by **cdx** · 2026-11-08  
Project context: `bead:bob-cli-ir` and `plan:202611/record_notes.md`

**Your intuition is plausible. The strongest opportunity is to make small, reusable observations cheap enough to preserve: what worked, for whom, under which circumstances, what to avoid, and why you made a choice.** Much of this information is unavailable on the public web and disappears when an experience ends or an associated task is completed. A few useful sentences about a restaurant, show, device, or recurring process can pay back before you have enough records for any meaningful analysis.

There is research supporting the premise that useful personal information falls between the categories and interaction costs imposed by existing tools. There is no evidence establishing that Bob's record notes will be a “huge unlock” for you specifically. That depends on capture effort, whether you encounter the notes when they matter, and whether maintaining them remains pleasant. My recommendation is to try the four collections already in the epic, emphasizing **observations that change a future choice**, before adding many new record types.

## What Bob is actually enabling

The approved plan describes one Markdown note per thing, a configurable schema, guided capture, updates to existing notes, optional dated observations, and collection views. It starts with restaurants, podcasts, TV shows, and movies. It explicitly keeps actions such as watching something with Kelly separate from the record holding the recommendation and eventual verdict. The plan reports 92 existing restaurant notes, 15 podcast notes, and roughly 25 open watch-list tasks; these are the planner's counts, not an independently repeated vault census. Source: `plan:202611/record_notes.md`, “Why” and “Design calls.”

This is partly an improvement to something you already do. The interesting change is that the same capture habit can create or update many kinds of small personal collections, with consistent fields and a predictable home. You no longer have to invent a separate filing ritual for every collection. Whether that changes what you notice and retain is the hypothesis to test.

The epic was **in progress when inspected**. Throughout this report, “planned support” means the approved contract, not a verified installed capability. I did not change the implementation, configuration, or vault, and I did not read another member of this swarm's report or findings.

| Layer | Example | Appropriate role |
|---|---|---|
| Thing | A particular restaurant | The record's identity and stable home |
| Current assessment | `status: liked` | Fast selection and filtering |
| Experience | “Friday evening: food good, conversation difficult” | A dated note preserving context |
| Action | “Book a table for Saturday” | A separate task |
| External source | A review, article, or podcast episode | The existing reference workflow, linked when useful |

The last two boundaries matter. The plan keeps books and podcast episodes in `ref/`, and does not introduce people records. Additional record types below are possibilities for later experimentation, not additions to the current epic. The audited Capture and Reference Note glossary entries also support preserving the distinction between taking action and retaining source material.

## What the evidence supports

These are adjacent studies, not evaluations of Bob. Their value is in identifying mechanisms and failure modes.

| Evidence | What it contributes | Limit on the inference |
|---|---|---|
| Bernstein and colleagues examined 533 information scraps from 27 knowledge workers across five organizations. They found diverse content and needs for fast entry, flexible representation, and visibility. | There really is useful information that ordinary personal-information tools fail to accommodate. A configurable note with a free-text body could absorb some of it. | Observational study; it does not establish that imposing a schema improves capture. [Information Scraps, 2008](https://hci.stanford.edu/publications/2008/infoscraps/TOIS-final-with-refs.pdf) |
| Van Kleek and colleagues analyzed notes and interaction logs from 420 volunteer List-it users over a two-year study period. Users valued quick capture and arbitrary content; uses included reference, brainstorming, logging, and sentimental archiving. | A broadly reusable capture surface can support more than a single predefined use case. | Self-selected users, and the tool was largely unstructured. Not a controlled comparison with typed notes. [Finders/keepers, 2011](https://dspace.mit.edu/entities/publication/75796cd4-f2d4-4dba-844b-96bc832dc33b) |
| Epstein and colleagues studied tracking across physical activity, finances, and location, including 22 interviews. Their model includes instrumental uses, curiosity, lapses, and resumption. | You can keep records for practical recall or curiosity without committing to continuous self-improvement or daily logging. | These domains and tools differ from Bob's collections. [A Lived Informatics Model, 2015](https://depstein.net/assets/pubs/depstein_ubi15.pdf) |
| Moore and colleagues studied engagement with personal air-quality data. Participants found unexpected insights during exploration but were reluctant to adopt analysis tools themselves. | Interesting data does not automatically create a desire to maintain dashboards. Assistance and a concrete question can matter. | Small, domain-specific study involving researcher-supported exploration. [The Personal Informatics Analysis Gap, 2021](https://arxiv.org/html/2108.03761v1) |
| Bruce, Jones, and Dumais studied keeping and later re-finding web information, alongside a survey of 214 people. | Successful storage needs a route back to the information when a need arises. | Web re-finding is not identical to recalling personal experiences. [Keeping Found Things Found, 2004](https://files.eric.ed.gov/fulltext/EJ1082047.pdf) |
| Zhang and colleagues report four studies of rediscovering ordinary experiences; participants underestimated aspects of their future interest or enjoyment. | Some records can be worthwhile because rereading them is meaningful, even without a decision or productivity gain. | This does not justify exhaustive recording or establish the net benefit of a lifelong collection. [The Unexpected Value of Rediscovery, 2014](https://www.hbs.edu/ris/Publication%2520Files/Rediscovery_91a38887-12e7-4c5c-a60d-866c0e4a95c4.pdf) |

The evidence is strongest for **a real unmet need and a plausible mechanism**, weaker for the magnitude of personal benefit. Several papers come from overlapping research groups, and much of the work predates today's tools. None proves that more fields, more notes, or more analysis improves your life.

One tension is particularly relevant: information-scrap research favors flexible, inexpensive entry, while record notes introduce validation and required fields. Structure helps when it saves repeated interpretation later. It hurts when a fleeting observation becomes a form-filling exercise. The free-text body and quick updates are therefore central to the opportunity.

## The data that seems most worth capturing

A useful prompt is: **“What did I just learn that future me could not easily reconstruct?”**

Often the answer is neither a number nor a complete review. It is a qualification, a failed attempt, a precise detail, or the reason behind a preference. The examples below are invented illustrations, not claims about your habits or actual experiences.

### 1. Contextual preferences: “good for what?”

A restaurant's cuisine and address are relatively easy to recover. Your own reason for returning is harder:

> Excellent takeout, but the dining room was too loud for conversation. The smaller portion was enough. Order the broth separately for the drive home.

At the next choice, this can answer three questions: where to eat, whether to take out, and what to order. A generic `liked` verdict cannot answer all three. Likewise:

- A show might be excellent but require more concentration than you want tonight.
- A podcast might be useful for interviews but repetitive for weekly news.
- A film might be something you want to recommend to one friend but would not rewatch yourself.

**Planned fit:** Excellent. Existing status/verdict fields provide the short answer; ordinary notes carry the conditions. Do not add `noise`, `portion_size`, `attention_required`, and ten other fields immediately. Promote a recurring distinction into a field only when you actually want to filter on it.

**Payoff trigger:** Choosing dinner, entertainment, or something to listen to. Open the collection at the moment of choice.

### 2. Negative knowledge: “why did we rule this out?”

A surprisingly valuable record may preserve a reason not to repeat an investigation:

> Stopped this show after episode three because the humor did not work for us. The premise was promising; the problem was not lack of time.

Or, for a possible future software collection:

> Tried version 4.2 for offline search. It could search titles but not attachment text. Reconsider if that limitation changes.

The record makes a distinction that memory can blur: *not yet tried*, *tried and unsuitable*, and *previously unsuitable under a condition that might change*. This can prevent a fresh recommendation or attractive screenshot from restarting the same evaluation.

**Planned fit:** TV has `dropped`; restaurants have `not_liked`; podcasts have `unsubscribed`. Preserve the reason in the note. Software evaluations are outside the epic and may already belong in an existing project or decision document.

**Payoff trigger:** Reconsidering an option, encountering a familiar recommendation, or upgrading a tool. One avoided repeat investigation can justify a very small collection.

### 3. Recommendation context: “why was this suggested to me?”

A title and recommender are a start. The more useful observation is often:

> Recommended for its depiction of small-team collaboration; suggested that we try the first two episodes before deciding.

After viewing, add what actually matched. Months later you can distinguish recommendations that fit a particular interest from recommendations that happened to come from someone you trust generally. This also gives you something specific to say when thanking the person.

**Planned fit:** Shows and movies have `recommended_by` plus prose notes. Restaurants and podcasts can hold attribution in prose. There is no need to build a separate people database or assign “recommendation accuracy” scores to friends.

**Payoff trigger:** Selecting a new option or talking to the recommender again. With enough examples, a later review might reveal a useful taste pattern, but that is an optional second benefit.

### 4. Reproducible successes: “how do I get this result again?”

Preserve the detail that distinguishes a good result from an ordinary one:

> Ask for the side room; arrive before the main dinner rush; this particular dish travels well.

The same pattern extends beyond the current four collections:

- A recipe: the substitution, pan size, and timing that actually worked in your kitchen.
- A walking route: the entrance with easy parking and the segment that stays shaded.
- A device: the exact cable, port, firmware, and setting combination that solved a problem.
- A repeat trip: which arrival time or transfer arrangement made it easy.

**Payoff trigger:** Repeating the activity. This is especially promising when public descriptions cannot reproduce your specific setup or constraints.

### 5. Small observations that become questions later

You do not have to know every future query in advance. Suppose several notes happen to mention “too much setup,” “we could start immediately,” or “worked well when tired.” Later you may notice that your favorite leisure options share a low startup cost. That could become a useful question for the next choice.

This is an inference about how your collection might develop, not a demonstrated result. Preserve the original observations so a later interpretation can be checked against them. Do not require every note to support a prediction or metric at capture time.

A small amount of exploratory recording is reasonable when the observation is easy to capture and interesting in its own right. The safeguard is a bounded experiment and occasional reuse, rather than an obligation to keep collecting until a pattern appears.

## A wider menu of possibilities

The four existing collections are enough to test the idea. These additional examples are prompts for noticing unmet needs, **not a recommendation to create all these folders**. New record types would require later configuration and initialization; some ideas may work better as ordinary notes in an existing location.

| Candidate thing | Smallest useful observation | Question it could answer later | First place to try it |
|---|---|---|---|
| Restaurant | What to order, avoid, and choose it for | “Where would work for this particular evening?” | Planned restaurant record |
| Podcast | Why you kept or dropped it; useful episode formats | “What deserves a place in my listening rotation?” | Planned podcast record; individual episodes remain references |
| Show or movie | Who suggested it, why, stopping point, reaction | “Why is this on the list, and is it right for tonight?” | Planned media record |
| Clothing or shoes | Model, size, and how it fit after real use | “Which size actually worked last time?” | Optional later product collection |
| Device or accessory | Exact model and tested compatibility | “Will this work with the setup I own?” | Existing equipment note, or later product collection |
| Household appliance | Consumable part number and a dated repair observation | “Which replacement fits, and what fixed this before?” | Existing home notes, or later equipment collection |
| Service provider | Job performed, communication experience, result | “Who handled this kind of problem well?” | Existing notes, or later provider collection |
| Recipe you cook repeatedly | Change made and observed result | “Which version should I cook for these circumstances?” | Existing recipe/reference note; later recipe collection only if needed |
| Place or local outing | Entry point, real effort, weather caveat, who enjoyed it | “What is an easy option for this amount of time?” | Ordinary place note; later collection if comparisons recur |
| Repeated trip | What made transfers, packing, or arrival easier | “What would I do differently next visit?” | Existing travel/project notes |
| Software candidate | Tested version, decisive limitation, reconsideration condition | “Did I already test this, and what changed?” | Existing project/decision notes first |
| Recurring workflow | A concrete interruption and the workaround that helped | “Which source of friction keeps coming back?” | Existing project note before inventing a new record type |
| Hobby material or consumable | Exact variant, conditions of use, outcome | “Which one should I buy again for this purpose?” | Optional later collection tied to an actual hobby |
| Gift idea or past gift | The explicit preference it responds to; what was given when | “What would be thoughtful and not repetitive?” | Existing personal notes/tasks; no people-record migration |
| Ordinary shared memory | One detail you want to remember about an outing or film | “What did that period of our lives feel like?” | Dated body note on the relevant record |

My strongest candidates **beyond** the epic are exact product fit/compatibility and repeatable local experiences. They have identifiable objects, recurring questions, details that are easy to forget, and useful answers from only a handful of records. Recipes and software evaluations are plausible too, but should first be checked against places where you already preserve that information.

High-frequency mood, sleep, symptom, or productivity tracking is a different proposition. It requires attention to missing observations, measurement definitions, and time series. It is a poor initial test of whether one-note-per-thing capture helps you.

## Four examples using the approved syntax

These are fictional drafts illustrating the plan. They have not been run against the vault, and availability depends on the epic landing. Restaurant capture requires status, category, and location; the examples include those. The configured companion default is Kelly, so these drafts explicitly supply or clear it rather than silently treating a default as evidence of attendance.

**A recommendation with its reason, rather than just another title:**

```text
The Orchard House @tv/
- status:: to_watch
- recommended_by:: Sam
- companions:: [[kelly]]
- Sam recommended the small-team dynamics; try two episodes before deciding.
```

**A restaurant observation with several future uses:**

```text
The Quiet Table @eat/
- status:: liked
- category:: Mediterranean
- location:: Cranford
- companions:: [[kelly]]
- visited:: today
- Good for an unhurried conversation. Ask for the side room.
- The lentil dish was the repeat order; one starter was enough to share.
```

**A later visit that qualifies the first impression:**

```text
Friday was much louder; choose weekday lunch for conversation @eat/the_quiet_table
- visited:: today
- companions::
- Went alone this time. Food still good; the side room was closed.
```

In this example, the empty optional companions field explicitly clears the current field; the earlier visit's prose remains. A real record should name companions in a dated note when the historical distinction matters. The frontmatter is not an attendance history.

**A completed experience whose useful information survives:**

```text
Stopped after episode three; the humor did not work for us @tv/the_orchard_house
- status:: dropped
- verdict:: meh
- The collaboration theme was interesting, but we would not resume just because a new season appears.
```

A reminder to try the show, or a commitment to watch it with someone, is still a separate task. These drafts preserve the object and its history without making every saved possibility an obligation. Syntax and field behavior come from `plan:202611/record_notes.md`, “Schema” and “Capture grammar”; these fictional records do not exist in the vault.

## How the data becomes useful

There are three distinct levels of return. They need different amounts of data and different retrieval support.

| Return | Example | What is needed |
|---|---|---|
| Recall | “What was the dish we wanted to order again?” | One useful note and a way to find its restaurant |
| Selection | “Which of our options fits tonight?” | A small set of records; a few meaningful filters; reading the qualifying notes |
| Discovery | “What do the things we keep abandoning have in common?” | Several relevant observations, interpretation, and awareness of gaps |

**Start with recall and selection.** A record does not need to produce a chart to earn its keep. The collection's most important view may simply be “to try” or “liked,” followed by opening two or three notes.

Obsidian Bases supports views over files and their properties, including filtering, sorting, and grouping. That makes straightforward field-based selection feasible, but an observation in prose does not automatically become a typed filter. Start by reading it; add a field if the same selection need recurs. [Obsidian Bases documentation](https://obsidian.md/help/bases), [Bases syntax](https://obsidian.md/help/bases/syntax)

There is a significant contract boundary: **the planned `bob records list` lists record types, while `bob records show TYPE` describes the schema and common values. Neither is an arbitrary search over individual records.** The plan provides collection Bases, existing-record completion, and Similar records, but does not establish a natural-language recommendation engine. More advanced retrieval requires existing vault search/read tools or additional work. Source: `plan:202611/record_notes.md`, “CLI” and the capture-revisit phases.

An agent could nevertheless help interpret a deliberately selected set of notes. For example:

> From these restaurant notes, find up to three candidates for a quiet dinner. Give the dated evidence for each, identify missing information, and separate recorded facts from your suggestions.

Or:

> Read these dropped-show and unsubscribed-podcast notes. Suggest recurring reasons, link each proposed pattern to its examples, and include cases that do not fit. Do not update the records.

These are possible assisted workflows, not shipped commands. They have a concrete input and a checkable output. The agent cannot recover an unrecorded reason, infer what an absent verdict means, or make an old note about opening hours current. Public facts that affect an immediate choice still need rechecking.

## Keeping the collection useful without making it a chore

**Use fields for distinctions you repeatedly select by; use prose for explanation.** “Liked” is quick to scan. “Liked the food but would only return for takeout” explains the decision. A rating alone loses that distinction, and a large schema makes every observation more expensive.

**Prefer a sentence with a reason or condition over exhaustive metadata.** It often captures more value than filling every optional field. One usable record is a success; a partially populated collection is normal. The published work on tracking abandonment includes reasons beyond simple failure, including changing needs and satisfying curiosity. [Beyond Abandonment to Next Steps, 2016](https://pmc.ncbi.nlm.nih.gov/articles/PMC5428074/)

**Treat frontmatter as the current summary.** Updating `visited`, `status`, or `companions` does not by itself give you a clean event table. Put historically meaningful circumstances into dated notes. If you later need accurate counts or comparisons across visits, design an explicit event representation then. Do not pretend the current fields contain the past.

**A note's date is not always the event's date.** The plan dates note bullets when captured. When entering an older experience, state the actual or approximate event date in the text. Do not let “recorded today” become “happened today.”

**Missing is different from negative.** No verdict may mean not yet experienced, forgotten, or deliberately unrecorded. A companion default is a convenience, not proof. A provider used once without complaint is not a measured reliability score. Validation can check field shape; it cannot establish truth.

**Separate examples from rates.** Three recorded failures can suggest a recurring problem, but they do not establish a failure percentage without the total number of attempts. A collection of memorable experiences is a selected sample. Use it to generate questions and practical cautions; avoid treating it as a representative dataset or causal experiment.

**Preserve changing judgments.** Append the reason for a revised opinion rather than leaving only the latest verdict. Conversely, do not make an old negative note permanent law: include version, situation, or a condition for reconsidering it when those matter.

**Keep the best existing home.** Do not duplicate reading history, technical decisions, receipts, or maintenance logs merely to make them look uniform. A record can point to an authoritative source and add the personal context it lacks. This research does not call for migrating the existing reference library or project memory.

**Make retrieval situational.** Check restaurants when choosing where to eat; check media when deciding what to watch. A weekly obligation to inspect every record would consume much of the value. For sentimental use, an occasional voluntary browse is enough.

## A small experiment that can test the intuition

This is a suggested personal trial, not an implementation plan or a requirement to build more tooling.

1. **For two weeks, use at most two of the epic's collections.** Restaurants plus shows/movies are good candidates because the records can help at an ordinary decision point. If there are too few relevant experiences, extend the trial rather than creating entries just to reach a quota.
2. **Capture only an unusually useful detail or a real change.** Use the existing required fields. Add one short sentence about why, for whom, when to choose it, what to avoid, or what to repeat. An aspirational effort limit is roughly 20–30 seconds for a small update; this is a design target, not a measured Bob capability.
3. **Consult the collection before the next few relevant choices.** This is the crucial part. Without it, the experiment tests data entry alone.
4. **Keep one tiny payoff note.** Record occasions when a note saved a search, changed a choice, prevented repetition, made a recommendation more personal, or was enjoyable to revisit. Also note cases where entry felt annoying or retrieval failed. Do not instrument every interaction.
5. **At the end, choose to continue, simplify, or stop.** Retain fields that actually helped selection. Keep a collection that produced meaningful recall or enjoyment at little cost. Simplify one that has interesting notes but burdensome entry. Stop adding to one that feels like upkeep with no return. Existing notes can remain useful even if collection pauses.

A practical success signal would be **two clear moments of useful reuse without feeling obliged to log everything**. That is a proposed decision rule, not a research-established threshold. A rare but valuable lookup can also justify a low-maintenance collection; a short trial cannot evaluate every long-term payoff.

If the trial succeeds, choose one additional collection from an actual recurring question: “I keep forgetting which cable works,” “I keep repeating this evaluation,” or “I wish I could recreate that outing.” Start with a few real examples. Let those examples reveal the smallest shared schema.

My confidence is highest that record notes can improve **specific recall and reuse of personal experience**. I am moderately confident that guided entry and shared capture will broaden what you preserve. I am much less confident that large-scale tracking or automatic pattern discovery will be valuable without a concrete interest. The first two benefits are enough to justify a small trial.

## Research scope and source handling

I independently read `bob-cli-ir` through `sase bead read`, the approved `plan:202611/record_notes.md` through `sase artifact read`, and the relevant memory through audited SASE reads. I used primary research papers, author/university repositories, and official Obsidian documentation. Research links appear next to the claims they support. I did not consult peer reports, peer transcripts, or peer summaries, and did not perform a fresh census of personal vault contents.

The examples, candidate collections, confidence judgments, and trial criteria are my synthesis. They should be read as possibilities to test. No records, new record types, tasks, or product changes were created by this research.
