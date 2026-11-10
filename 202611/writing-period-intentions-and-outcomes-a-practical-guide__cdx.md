# What to write in Bob’s Intentions and Outcomes

Independent research by **cdx** · 2026-11-10

**Yes: Bob deliberately leaves these sections for you. Start with one sentence about what you want to be different by the end of this week, followed by how you will recognize it.** You do not need an elaborate annual plan before you can write a useful weekly intention.

A workable first entry is:

> By Sunday, I want to have decided which of the two approaches to my current problem to pursue. Enough evidence: a short comparison and a recorded decision, including what would change my mind.

That is an illustration, not a claim about your current projects. Replace the problem with something you actually care about. You can stop after those two sentences. A starting cue is useful if beginning the work is likely to be difficult.

My recommendation is to treat period planning as a small decision aid: **choose a change, identify evidence, make room for the work, and compare the result with the original choice.** The suggestions below are deliberately lightweight. The exact counts and time limits are proposed defaults, not Bob requirements or scientifically established optimums.

**What Bob actually expects.** I inspected the current bob-cli documentation and implementation at commit `8e2b93c7d0ed6bee06cb5b19b5ce95bc8f09115e`, then used read-only `bob periods brief` queries against the installed `bob 0.5.0`. The distinction between the sections is explicit:

| Section | What belongs there | Who writes it |
| --- | --- | --- |
| Weekly `## Intentions` | What you choose to advance, protect, resolve, or learn this week | You |
| Quarterly `## Outcomes` | The changes you want to be true by the quarter’s end | You |
| Yearly `## Theme` | A direction that helps you choose between competing opportunities | You |
| Yearly `## Outcomes` | A few desired changes at the year’s scale | You |
| `## Review` | Evidence about what the period produced, what remains open, and progress against your plans | An agent, through `bob periods draft` |
| `## Reflection` | Your interpretation: what mattered, what you learned, and what you will change | You |

The section names and ownership are Bob’s contract; the plain-language prompts in the middle column are my operational interpretation. **Outcomes is a planning section. Actual outcomes are reported in Review and interpreted in Reflection.** The review instructions explicitly compare the period with your previously stated Intentions or Outcomes. Period notes contain no task rows: actionable work stays in the task system, with ordinary links from the planning prose where useful. [Bob note anatomy and ownership](https://github.com/bobs-org/bob-cli/blob/8e2b93c7d0ed6bee06cb5b19b5ce95bc8f09115e/docs/periods.md#note-anatomy-and-ownership), [review instructions](https://github.com/bobs-org/bob-cli/blob/8e2b93c7d0ed6bee06cb5b19b5ce95bc8f09115e/docs/periods.md#agent-instruction-callouts-v2).

The live query for `2026-W46` returned empty Intentions and an empty previous-week Reflection. Its parent, `2026-Q4`, had empty Outcomes. A separate Q4 brief confirmed empty parent-year Theme and Outcomes. This is a narrow snapshot, not a history-wide audit. It corroborates your report of not having filled these sections; it cannot establish why. Your own explanation—uncertainty about what to write—is the strongest evidence about that.

The scaffolding code inserts bare headings without instructional prompts or examples. My inference is that the interface leaves a substantial translation job to you: it provides a place for intentions without teaching what a useful entry looks like. That suggests trying concrete sentence patterns before adding reminders, new automation, or more review obligations. [Scaffold implementation](https://github.com/bobs-org/bob-cli/blob/8e2b93c7d0ed6bee06cb5b19b5ce95bc8f09115e/src/native/periods/scaffold.rs#L156).

**Write a recognizable change, at the right scale.** An intention can concern producing something, making a decision, learning something, sustaining a practice, or protecting something valuable. “Outcome” does not require a number. It does require enough clarity that future you can discuss what happened without inventing a new definition of success.

| Vague entry | More useful entry | What makes it reviewable |
| --- | --- | --- |
| Work on capture | Resolve the most disruptive capture failure; the original reproduction works and I have used the repaired path in ordinary work | A named problem and evidence of use |
| Read more | Decide whether this paper changes my approach; write the claim, its strongest limitation, and my decision | A learning result rather than pages consumed |
| Improve planning | Try one weekly intention and one end-of-week reflection; decide whether it helped me choose work | A bounded experiment |
| Get the proposal accepted | Submit a proposal that addresses the stated requirements and request a decision; acceptance remains uncertain | My contribution is separate from someone else’s response |
| Be more present | Keep one agreed evening free of work and spend it with someone I care about | A concrete protected experience |
| Keep things running | Maintain the essential recurring commitments during a crowded week; defer optional changes | Maintenance can be the chosen result |
| Fix the whole architecture | Compare two approaches against the troublesome case and choose a next experiment | A plausible learning result for uncertain work |

These are invented examples. They are not inferred deficiencies in your work, relationships, or habits. Choose language you would naturally say aloud; there is no benefit in making a small intention sound like a corporate objective.

**A weekly entry can be two sentences.** Put the following content under the existing `## Intentions` heading. This is a writing prompt, not text to paste unchanged:

```markdown
- By the end of this week, I want [specific change, decision, or experience].
  Enough evidence: [something I can observe, show, or honestly describe].
```

If useful, add one sentence about why this matters *now*. Link the actual project or task already in your vault. Do not create a checkbox in the period note or duplicate the task’s execution plan there.

Start with **one** intention. After two weeks, allow up to three if the additional choices make the week clearer. Three is a ceiling to experiment with, not a quota. Normal work, maintenance, interruptions, and obligations continue outside this shortlist. You do not need an intention for every project or area.

A useful final check is: “If this succeeds, what becomes different?” If the answer is only “I will have spent time,” decide whether time itself is the point. A restorative afternoon or protected practice session can legitimately be the point. For a software project, a resolved uncertainty, usable capability, or completed decision will usually explain the value better than a Pomodoro count.

For work that is hard to start, add an optional cue:

```markdown
When I finish my first morning review on Tuesday, I will open the
comparison note and spend the first work session on the unresolved case.
If I start broadening the project, I will record the idea and return
to that case.
```

This is a bridge from the intention to action. Record the actual next action in its normal task location. Use a calendar entry when you have made a real time commitment. An intention by itself does not reserve capacity or change a task’s Bob status.

**Quarterly Outcomes describe changes that weekly work can support.** A useful sentence pattern is:

```markdown
- By this quarter’s end, [capability, condition, decision, or relationship
  I want to have established]. I will judge this by [credible evidence].
  This matters because [reason I endorse].
```

Begin with one outcome; two or three may become useful later. A quarter offers more time for a sustained change than a week, but uncertainty also increases. Write evidence you can actually collect. A number is helpful when it represents the desired change and has a meaningful basis; it is unnecessary decoration when it does not.

For example, a hypothetical outcome for this very practice could be:

> For the remainder of this quarter, weekly planning helps me choose what deserves attention. I can point to four consecutive weeks with an intention written before the work and a brief reflection afterward, plus at least two concrete choices those intentions helped me make. I will keep each planning pass under ten minutes and simplify the format if it becomes burdensome.

The consecutive weeks show that you tried the practice; the decisions provide evidence that it served a purpose. Filling four notes alone would not establish that the practice helped. The counts and time limit here are experimental choices, not validated targets.

For a product project, an outcome might instead be: “The everyday capture workflow is dependable enough for normal use; the previously identified failure cases pass and the remaining limitations are explicit.” Its weekly intention could be “Resolve the highest-impact remaining failure.” The related tasks describe how to do that. This is a meaningful connection across scales without copying every task into every period.

**A yearly Theme helps with tradeoffs.** A phrase such as “Make everyday tools dependable” becomes more useful when followed by an implication: “Give reliability and simplification first consideration when choosing between them and additional features.” Treat this as an illustration, not a proposed value for you. A theme that never affects a choice may need a more concrete interpretation.

Yearly Outcomes name the few changes that would make the year meaningfully different. Quarterly outcomes can be milestones, experiments, or evidence toward them. Maintenance, personal commitments, and unexpected opportunities need not be forced into a parent outcome. The hierarchy is context, not a requirement to justify every action through four levels of goals.

Bob’s calendar matters: its weeks are ISO Monday–Sunday weeks, and quarters group whole ISO weeks. The current Q4 runs **September 28, 2026–January 3, 2027**, including W53. There is no monthly-note level in this period system. For a plan started now, write “chosen November 10; for the rest of the quarter” rather than implying you set it in September. You can leave annual planning until it would help you; it is not a prerequisite to starting this week. [Bob calendar contract](https://github.com/bobs-org/bob-cli/blob/8e2b93c7d0ed6bee06cb5b19b5ce95bc8f09115e/docs/periods.md#calendar-and-identity).

**What the research supports—and what it does not.** This was a focused research review, not an exhaustive systematic review. I selected original research, research syntheses, and an original practitioner checklist relevant to choosing goals, initiating action, and reviewing progress.

| Evidence | Finding relevant here | Practical implication and limit |
| --- | --- | --- |
| Locke & Latham (2002), review of goal-setting research | Specific, challenging goals often improve performance relative to vague exhortations; commitment, feedback, ability, and task complexity matter. For unfamiliar complex tasks, learning goals can be more useful than demanding a performance result too early. | State what you want to accomplish or learn. This does not mean choosing the hardest imaginable goal or converting every personal value into a metric. [Paper](https://med.stanford.edu/content/dam/sm/s-spire/documents/PD.locke-and-latham-retrospective_Paper.pdf) |
| Gollwitzer & Sheeran, National Cancer Institute research overview | Implementation intentions link a recognizable situation with a particular action to help enact an already chosen goal. | Add an if–then or when–then cue where initiation or distraction is a problem. A weekly heading called Intentions is not automatically an implementation intention in the technical sense. [Overview](https://dccps.nci.nih.gov/BRP/constructs/implementation_intentions/goal_intent_attain.pdf) |
| Harkin et al. (2016), experimental meta-analysis | Across 138 studies and 19,951 participants, interventions promoting progress monitoring improved goal attainment on average: standardized effect d = 0.40, 95% CI 0.32–0.48. Recording progress was associated with larger effects in moderator analyses. | Return to the original intention and record what happened. This does not establish an ideal weekly cadence, a benefit from elaborate dashboards, or a 40% increase in success. [Paper](https://www.apa.org/pubs/journals/releases/bul-bul0000025.pdf) |
| Wang, Wang & Gai (2021), meta-analysis of mental contrasting plus implementation intentions | Across 21 studies, 24 effect sizes, and 15,907 participants, the pooled effect was g = 0.336. Publication-bias concerns temper that result; a trim-and-fill adjustment gave g = 0.242. | Consider a plausible obstacle and your response, particularly for an intention that repeatedly slips. This supports an optional technique, not a requirement to complete a lengthy worksheet. [Paper](https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2021.565202/full) |
| Sheldon & Elliot (1999), self-concordance research | Their longitudinal model connects goals consistent with one’s interests and values to sustained effort and benefits from attainment. | Ask whether you endorse the outcome and why it matters now. Longitudinal associations do not prove that adding a “why” sentence will cause success. [Paper](https://selfdeterminationtheory.org/SDT/documents/1999_SheldonElliot.pdf) |
| David Allen Company, GTD Weekly Review checklist | The checklist connects review of projects and larger outcomes with current next actions, calendar commitments, and waiting items. | Reuse your existing task and calendar context when choosing an intention. This is practitioner guidance, not experimental evidence for Bob’s particular structure. [Checklist](https://gettingthingsdone.com/wp-content/uploads/2016/04/GTD-WeeklyReview.pdf) |

The evidence supports ingredients: meaningful choice, specificity, useful action cues, and feedback. **None of these sources validates the exact Bob hierarchy or the particular template I propose.** Much of the experimental literature concerns discrete behaviors, health, education, or bounded work tasks. Applying it to broad personal planning requires judgment. The recommendation to begin with one intention is chiefly a response to your stated friction and the cost of maintaining another practice.

**Choose what to write with a short pass through existing context.** Try this sequence at the beginning of a week, or today for the remainder of this one:

1. Read the previous Review and your Reflection if they exist. Notice one unfinished thread or one decision you want the coming week to reflect. If those sections are empty, continue.
2. Look at actual calendar commitments and the work already underway. Consider what can fit after those obligations.
3. Ask: “What would I be glad was different by Sunday?” Select one answer. It can concern completing, deciding, learning, maintaining, or protecting.
4. Write the two-sentence intention and locate its first action in the existing task system. Add a starting cue only if that would help.
5. Name one tempting addition that can wait, if choosing this intention requires a tradeoff. Keep that sentence adjacent to the intention; it needs no separate tracking system.

Aim for five minutes initially, with ten as a stopping point. These are suggested limits. If writing the intention requires substantial project investigation, the intention can be to resolve that uncertainty. You do not have to solve the entire project during the planning pass.

The current weekly note is `2026/2026-W46.md`. Read-only terminal context is available through `bob periods show`, `bob periods brief`, and `bob periods brief last-week`; the latter two expose the planning context used by an agent. A brief is source material, not a generated Review. These commands are optional aids, not additional weekly obligations. [Period commands](https://github.com/bobs-org/bob-cli/blob/8e2b93c7d0ed6bee06cb5b19b5ce95bc8f09115e/docs/periods.md#cli-so-far).

**Close the loop with evidence, then your interpretation.** At the end of the period, compare what happened with the original wording. Bob’s agent instructions distinguish done, partial, not done, and no evidence. The last category matters: absent recorded time does not establish absent work, and hours logged do not establish that the intended change occurred. A link to a completed project, a decision note, an artifact, or a brief factual account can be more informative than time totals. [Review evidence rules](https://github.com/bobs-org/bob-cli/blob/8e2b93c7d0ed6bee06cb5b19b5ce95bc8f09115e/docs/periods.md#agent-instruction-callouts-v2).

If you want an agent-drafted Review, get it first, then write your Reflection. One or two sentences can be enough:

> The comparison was useful, but I stopped short of choosing because I was waiting for information I had not requested. Next week I will request it first, and decide with the available evidence by Friday.

That invented example separates observation, your explanation, and the next choice. You can also record satisfaction, disappointment, a valuable surprise, or a deliberate change of priority. A Reflection need not be a productivity diagnosis.

**Keep Reflection genuinely empty until you intend to reflect.** In Bob, any text there marks the note `reflected`, even an unfinished placeholder such as “write this later.” A normal agent draft then refuses that note unless you explicitly request a redo. Bob also refuses ordinary drafts for an open period unless you request a “so far” review. These are workflow details that matter when adopting a template. [Review-state rules](https://github.com/bobs-org/bob-cli/blob/8e2b93c7d0ed6bee06cb5b19b5ce95bc8f09115e/docs/periods.md#review-state-and-headline), [draft guards](https://github.com/bobs-org/bob-cli/blob/8e2b93c7d0ed6bee06cb5b19b5ce95bc8f09115e/src/native/periods/draft.rs#L246).

If priorities change midweek, preserve the original intent and add a dated amendment explaining the choice. Do not silently rewrite the beginning of the week to match its ending. If you miss a week, start at the current date. Retrospective learning belongs in Reflection; invented retrospective intentions would make the record less useful.

When an intention misses repeatedly, reconsider its size, importance, missing prerequisite, or wording. Choose explicitly among trying again, narrowing it, changing the approach, deferring it, or dropping it. These are planning decisions; carry out any resulting task changes separately through the normal task workflow. A miss alone is not evidence about your character.

**A two-week trial is enough to learn whether this format helps.** For the rest of W46, write one intention with observable evidence. Glance at it once during the week when choosing work. After the week ends, read or obtain the Review and add a short Reflection. Do the same in W47. You can start this trial with the quarterly and yearly sections still empty.

At the end of those two weeks, ask whether the notes helped you make a concrete choice, recognize a useful result, or notice an unrealistic expectation—and whether the writing cost was acceptable. If they did, add a provisional quarterly Outcome and consider a second weekly intention. If they did not, change the sentence pattern or reduce its burden. The number of filled sections is not the purpose of the experiment.

A complete minimal example, for you to adapt rather than adopt automatically:

```markdown
## Intentions

- Chosen November 10, for the rest of this week: decide which approach
  to the current problem to pursue. Enough evidence: a short comparison,
  a chosen approach, and the next action recorded in the project note.
```

Use the body under your existing heading; there is no need to add a duplicate heading. Leave Review and Reflection untouched until their respective moments. This report offers wording and a practice to try; it does not author your intentions or change your vault.

**Research scope and provenance.** I worked independently and did not locate, read, or consult any other report or researcher’s findings from this swarm. Local evidence consists of the pinned bob-cli files linked above, the audited `glossary:period-note` memory, and read-only filtered brief outputs on November 10. Only planning fields, period headers, and the prior Reflection field were surfaced; I did not inspect the full task ledger or infer personal goals from it. The weekly and quarterly notes were open and their Review states were `empty` at inspection. Their planning blanks are observations, not an explanation of motivation.

All six external sources in the evidence table were checked together through `bob ref find` using DOI or exact URL. All returned `not_found`. That means absent from the indexed `ref/` library under those identifiers, not that you have never read them; intake was not checked. You do not need to read any of them before trying the practice. If you want the rationale for one ingredient, the implementation-intentions overview explains starting cues, and the Harkin paper provides the broadest experimental evidence here for returning to a written goal.

Library check: 0 of 6 candidates already in your library (0 finished).
