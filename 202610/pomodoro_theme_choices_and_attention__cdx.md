---
title: "Pomodoro themes that guide attention: Bryan's usage and recommended changes"
date: 2026-10-27
researcher: cdx
status: independent-research
---

Your current theme menu is already reasonably small. The strongest opportunity is to make its labels better guides to what you will actually do: restore visibility to `JOB`, give `GTD` and `READ` clearer boundaries, turn `HOME` into a credible commitment, and distinguish `BUILD` from `FIX` by the result sought. I would preserve most names and historical records. A more elaborate taxonomy would add work without addressing the main patterns in your ledger.

This is an independent cdx report. I did not consult the other researchers, their reports, or their conversations. I used your supplied output, read-only Bob commands against your vault, Bob's local documentation and implementation, audited project memory, and external sources. No themes, preferences, tasks, or vault files were changed.

The observations below distinguish three things: **recorded facts**, **interpretations of those facts**, and **proposed experiments**. Established research can support attention management and concrete planning; it cannot tell us that Bryan should have exactly five themes, spend a prescribed percentage on reading, or rename a category to a particular word.

The catalog snapshot reproduced your supplied counts: 76 known, 71 hidden, and five present today. Bob reported its local date as October 26, while this research ran on October 27 UTC. For retrospective comparisons I excluded October 26 and used October 12–25, fourteen complete calendar days. A longer check covered August 26–October 25: 532 completed sessions and 16,650 recorded minutes, or 277h 30m. These are logged Pomodoro minutes, not all your waking time or an independent measurement of productive work.

Several details change how your original output should be interpreted.

- **Five visible names and five themes today are different sets.** `READ` is visible but last appeared October 25. `JOB` is hidden but appears October 26. On that date, `GTD` and `FIX` were closed; `JOB`, `BUILD`, and `HOME` still had open entries.
- **A catalog day is an appearance, not evidence of completed work.** Open placeholders contribute to `days_used` and `entries`. The “last 90 days” heading filters which visible records appear; it does not turn these fields into completed-session statistics.
- **Hiding affects suggestions.** A hidden name can still be used, retains its color, and remains in Stats. Reusing it does not unhide it. Therefore 71 hidden names do not establish 71 abandoned activities.
- **Your live limits differ from the documented defaults.** The current agenda reported three open counted themes against a cap of five, and seven links against a cap of fifteen. The documentation's defaults of three and ten are not your observed configuration. The catalog's “5 today” is not evidence that you exceeded a limit.
- **A `+` is allocation, not merely an extra tag.** A 50-minute `JOB + BUILD` session allocates approximately 25 minutes to each theme in Stats and consumes two distinct theme components while open. It does not independently record 50 minutes of career work and 50 minutes of building.

These interpretations follow Bob's [theme contract](https://github.com/bobs-org/bob-cli/blob/42abfa705a445647395fedea1691d885f53722b5/docs/pomodoro-themes.md), [plan-budget contract](https://github.com/bobs-org/bob-cli/blob/42abfa705a445647395fedea1691d885f53722b5/docs/plan.md), and [Stats contract](https://github.com/bobs-org/bob-cli/blob/42abfa705a445647395fedea1691d885f53722b5/docs/stats.md). The local source revision inspected was `42abfa705a445647395fedea1691d885f53722b5`; the installed CLI identified itself as `bob 0.3.1`. Current command output, rather than defaults, supplied the personal measurements.

Here is the most useful comparison between your remembered catalog and recent completed work. Catalog columns include appearances through October 26; completed columns cover only October 12–25. Theme minutes use Bob's component allocation.

| Theme | Visible in Recent? | Catalog days / entries | Completed sessions in 14 days | Days with completed sessions | Allocated minutes | Share of logged time |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| JOB | No | 19 / 88 | 56 | 9 | 1,070 | 30.1% |
| GTD | Yes | 53 / 139 | 39 | 14 | 1,020 | 28.7% |
| BUILD | Yes | 29 / 91 | 33 | 11 | 620 | 17.4% |
| READ | Yes | 15 / 45 | 25 | 7 | 495 | 13.9% |
| HOME | Yes | 10 / 10 | 1 | 1 | 25 | 0.7% |
| FIX | Yes | 4 / 7 | 1 | 1 | 25 | 0.7% |
| Other themes | Hidden | — | — | — | 305 | 8.6% |

The period contains 170 completed sessions and 3,560 minutes, or 59h 20m. A session can contain multiple themes, so component session counts are not generally additive. All 170 sessions had Bob's `ok` quality flag; that flag establishes acceptable recorded inputs, not accurate recollection or desirable allocation.

The adjacent weeks show why a single average is insufficient:

| Recorded theme minutes | October 12–18 | October 19–25 |
| --- | ---: | ---: |
| JOB | 915 | 155 |
| GTD | 355 | 665 |
| BUILD | 370 | 250 |
| READ | 25 | 470 |
| HOME | 25 | 0 |
| FIX | 25 | 0 |
| Other | 305 | 0 |
| Total | 2,020 | 1,540 |

In the second week, `GTD` and `READ` together accounted for 1,135 minutes: 73.7% of recorded time. `GTD` alone was 43.2%, and `READ` 30.5%. This is a review prompt, not a diagnosis of procrastination. A release investigation, unusually large review backlog, or deliberate learning week could justify it. It is nevertheless more consequential than the color collisions shown in the original command.

The sampled ledger gives the categories some concrete meaning. On October 26, `JOB` included work on the SASE blog; it was not limited to tasks residing in a job note. `BUILD` included Bob work and SASE feature work. `HOME` held personal infrastructure, backup, and financial tasks; its sole completed session was on October 17. On October 23, `READ` linked references about code review, agentic CI, merge queues, and the software-development lifecycle. This is at least partly project-related technical reading. The sample does not justify describing it as passive entertainment, nor does it tell us how much understanding or decision value each session produced.

There is a practical strength in your current approach: the theme can record **why you are choosing a session**, while the task links and derived homes record **which project receives it**. A blog session under `JOB` can mean career-facing work even when the project lives under development. Flattening all themes into project names would lose that distinction. Conversely, `BUILD` can keep a stable identity across several projects. The weakness is overlapping decision rules: the same blog or infrastructure task could plausibly be `JOB`, `BUILD`, `READ`, `HOME`, or `FIX` unless you choose the session's purpose first.

GTD provides a useful comparison. Its official guidance separates context, available time, available resources or energy, and priority; it also distinguishes actions, projects, and areas of responsibility. It explicitly recognizes defining work as real work alongside doing planned work and handling new work. Applied here, `GTD` deserves a legitimate place, while `HOME` is only a physical context when location actually constrains the action. `BUILD` and `READ` describe activity modes, not priorities. The missing information can live in the selected task and session outcome; it need not become another theme. This is a methodological comparison, not experimental evidence that GTD's complete system is superior. [David Allen Company, “Choosing what to do”](https://gettingthingsdone.com/2023/01/choosing-what-to-do/).

PARA likewise distinguishes finite projects, continuing responsibilities, reference resources, and inactive archives. That distinction supports keeping project structure and current session choice separate. It also supports retaining inactive material without putting it in the everyday selection menu. Your 71 hidden names are therefore not inherently a cleanup problem. Thirty-eight of the 76 catalog themes appeared on only one day, and all 38 are hidden. That is consistent with a historical vocabulary being kept out of current suggestions, although the catalog cannot establish when or why you hid them. [Tiago Forte's original PARA explanation](https://fortelabs.com/blog/para/).

The original Pomodoro workflow separates an activity inventory from the tasks selected for today, and provides space for interruptions. This distinction maps well to Bob's project/task inventory and daily ledger. A theme that returns as an open placeholder without obtaining a real opportunity to run risks becoming another inventory container. That is the concern with `HOME`: its ten appearances and one completed session suggest a planning-to-execution gap. They do not prove that home responsibilities were ignored; some may have been completed outside Pomodoro tracking. [Pomodoro Activity Inventory](https://www.pomodorotechnique.com/solutions/pomodoro-activity-inventory-esheet/), [Pomodoro To-Do Today](https://www.pomodorotechnique.com/solutions/pomodoro-to-do-today-esheet/).

Time blocking offers a complementary rule: allocate specific work to a feasible interval and revise the plan when reality changes. Your theme can name the block, but the linked task should name what that block is for. This is more informative than selecting `BUILD` and deciding among unrelated projects throughout the session. A simple example is “BUILD: finish this task's acceptance check during the next two sessions,” including ordinary breaks. Newport's presentation is practitioner guidance; its strong productivity claims are not a quantified estimate for your situation. [Cal Newport, “Focus Week: Take Control of Your Time”](https://calnewport.com/focus-week-take-control-of-your-time/).

Attention research supplies a narrower empirical reason for that practice. Leroy's experiments found that difficulty disengaging from unfinished work can impair performance on subsequent tasks. Leroy and Glomb later tested a brief plan for returning to interrupted work; across four studies it reduced attention residue and protected performance on the interrupting task. This supports writing a short return note before moving between important work streams. It does not show that changing a label removes the cost of switching, or that every Pomodoro break is harmful. [Leroy, 2009](https://www.sciencedirect.com/science/article/pii/S0749597809000399), [Leroy and Glomb, 2018](https://pubsonline.informs.org/doi/10.1287/orsc.2017.1184).

For your workflow, the useful unit of continuity is often the actual deliverable. Staying in `BUILD` while jumping between several projects can still require repeated mental reconstruction. Moving from reading a design to implementing that same design may preserve more context even though the label changes. This is an inference from the research and your workflow, not something theme counts measure. Delegated agents introduce a further distinction: parallel machine work need not imply parallel human attention. The controllable bottleneck may be how many results you are actively reviewing and deciding on.

Kanban makes the measurement problem explicit: work in progress concerns work items between defined start and finish points, with an explicit policy for controlling their number. Bob's count of distinct themes in open ledger entries is a useful attention prompt, but it is not a project WIP measure. One `BUILD` theme can conceal many started deliverables; closing today's session does not necessarily finish its task. I would therefore avoid treating a green theme meter as proof that your workload is small. Keep one primary deliverable in the current focus block, and let the actual task lanes expose unfinished work. No universal limit of three themes follows from the Kanban guide. [The Kanban Guide, May 2025](https://kanbanguides.org/the-kanban-guide/2025.5/).

For `HOME`, evidence on implementation intentions suggests a small experiment: attach the intended action to a specific feasible cue. “After lunch on Tuesday, start the backup task for one session” is a more executable commitment than an indefinitely open `HOME` entry. Gollwitzer and Sheeran's review found benefits from specifying when and how to act; their author-written overview also emphasizes that an underlying commitment matters. The evidence spans many settings and does not establish the effect size for your ledger. [Gollwitzer and Sheeran, implementation-intentions overview](https://cancercontrol.cancer.gov/brp/research/constructs/implementation-intentions).

For `READ`, the improvement depends on purpose. Learning research gives strong support to retrieval practice and distributed practice, while repeated rereading alone has weaker general utility. When you want retention, finish by recalling the key point without looking and revisit it later. When you are evaluating a technical proposal, a useful exit is a decision, objection, or next experiment; that is an adaptation to your work, not the same claim as an educational retention result. Reading for enjoyment need not produce an artifact. Your sampled technical references make these distinctions more useful than blindly renaming `READ` to `LEARN`. [Dunlosky and colleagues, 2013](https://www.psychologicalscience.org/journals/pspi/1529100612453266/), [full review](https://journals.sagepub.com/stoken/rbtfl/Z10jaVH/60XQM/full).

A broader meta-analysis of 158 studies linked time management to performance and wellbeing, with particularly meaningful associations for life satisfaction. The included evidence is heterogeneous and includes nonexperimental work. This argues for evaluating your theme system by whether important commitments move and your days feel manageable, alongside time allocation. It does not support maximizing logged minutes or squeezing all non-work life into categories. [Aeon, Faber, and Panaccio, 2021](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0245066).

I considered three plausible designs. A pure activity scheme—such as create, maintain, learn, administer—would be tidier, but could hide the career and household commitments that `JOB` and `HOME` help protect. A pure project/domain scheme—such as Bob, SASE, job, home—would make ownership clearer but duplicate task homes and lose some activity distinctions. A large two-axis scheme using `JOB + BUILD` would appear expressive while producing misleading half-and-half theme totals. **The best fit is a small, deliberately mixed menu with explicit selection rules.** This is a design judgment based on your existing behavior; there is no research consensus that all personal categories must use a single axis.

Here is the proposed meaning of each frequently relevant label. This is a dictionary for choosing future sessions, not a request to rewrite history.

| Label | Choose it when… | Finish the session with… | Important boundary |
| --- | --- | --- | --- |
| GTD | You are clarifying inputs, reviewing commitments, or deciding what to engage with | A clarified or reviewed set and a selected next action | Building Bob/SASE features belongs in BUILD or FIX even when those features support GTD |
| JOB | The session advances a chosen career outcome | A concrete application, outreach, portfolio, or publication increment | A career connection should be explicit; it should not make every software task JOB |
| BUILD | You are deliberately creating or extending a capability or artifact | A named increment or a clear next step on one deliverable | Pure inspection of new material can be READ; restoring broken behavior can be FIX |
| FIX | You are restoring expected behavior or resolving a specific defect | A verified repair or a narrowed diagnosis | Optional redesign and open-ended cleanup do not automatically qualify |
| READ | Your immediate job is to understand or evaluate selected material | A recalled idea, answered question, or decision when useful | Reading undertaken inside a deliverable's session need not always receive a separate label |
| HOME | You are protecting a bounded personal or household responsibility | One concrete action on that responsibility | HOME does not mean every activity performed in your house |

For overlaps, choose the commitment the session is meant to protect. If a household outcome is the reason to do a repair now, `HOME` is defensible; if the session is a general debugging batch, `FIX` may fit. If a portfolio milestone is the reason for a blog session, `JOB` is defensible even if the activity is writing. Record the concrete task once and use its project home for the other dimension. This sacrifices a perfectly pure theme breakdown in exchange for useful everyday choices; the tradeoff should be conscious.

Only ten of the 532 completed sessions in the longer window had composite names. You already mostly use one name per session. Preserve that habit. Use a composite when you intend a genuinely shared allocation, not as a substitute for independent metadata. If the time split matters and is not roughly equal, separate recorded sessions communicate it more honestly.

The color suggestions are reasonable local collision repairs, but low priority. Your visible colored names already have distinct hues: yellow, violet, blue, and green. An unhidden `JOB` would add aqua. `CLEANUP` last appeared September 30 and `MEMORY` October 19; their collisions do not establish confusion in current work. Recolor them if they interfere with a chart you actually use. Labels should continue to carry meaning alongside color, consistent with W3C guidance against making color the sole information channel. There is no defensible basis here for assigning a psychological productivity effect to blue versus orange. [W3C, Use of Color](https://www.w3.org/WAI/WCAG22/Understanding/use-of-color.html).

Historical cleanup should also be selective. Bob's rename rewrites matching components across canonical daily notes and the daily template; it changes historical theme aggregation. It is not merely a prospective display alias. True spelling equivalents such as `FIXES` and `FIX` might merit a preview after checking their meaning. `MEMORY`, `CLEANUP`, `RESEARCH`, and `BUILD` are not proven synonyms and should not be bulk-merged just to reduce the known count. A broader future definition such as `LEARN` would not justify retroactively relabeling every reading session. [Bob rename contract](https://github.com/bobs-org/bob-cli/blob/42abfa705a445647395fedea1691d885f53722b5/docs/reference/cli/themes.md).

The analysis can be reproduced with these read-only commands:

```sh
bob themes list -a -F -f json
bob stats show worked -r 2026-08-26..2026-10-26 -g day -f json
bob capture-pomodoros -a -t -f json
```

For the table, filter `metrics[0].points` and `sessions` explicitly to `2026-10-12 <= date <= 2026-10-25`; sum `parts.theme` for minutes. Do not silently include the live day's point: the returned report included October 26 entries even though its retrospective summary ended October 25. Completed-session theme counts split `name` on `+`. The catalog values are a separate snapshot and should not be used as a completed-session denominator. I also used bounded Dataview queries for October 23 task children and read the current agenda's resolved tasks. Home attribution follows task links and today's note tree, so it is approximate project allocation, not evidence of what happened minute by minute. No causal claim about your productivity can be made from these observations alone.

A lightweight fourteen-day trial would retain the names, use the dictionary above, and choose one concrete result for the first focus block each day. During the existing review, check whether that result moved, whether a planned `HOME` opportunity actually happened, and whether extra `GTD` or `READ` time served a named need. Use existing session notes rather than creating a new tracking system. At the end, keep changes that made selection easier or improved follow-through. Smaller time totals are not automatically success, and the recent reading-heavy week is not automatically the baseline you should return to.

My recommendations, ranked by likely benefit relative to effort and uncertainty, are:

1. **Make `JOB` available in Recent, and define its career outcome.** It was your largest category in the fourteen-day window while hidden. Consider `bob themes unhide JOB`; the change restores suggestions and preserves history. Include portfolio/blog work when its career purpose is explicit. If hiding it was intentional because it already lives in your daily template, keeping it hidden is reasonable—the finding establishes use, not your reason for hiding. **High confidence in the usage finding; medium confidence in the preference change.**

2. **Keep `GTD` exempt and muted, but give it a deliberate scope and time allowance.** Reserve it for running the review/clarification process. Put software improvements in BUILD or FIX. Your fourteen-day median was 50 GTD minutes per day, with large spikes; use your usual review duration as a starting checkpoint, and name the reason for an extension. This preserves necessary review while exposing its opportunity cost. It is not a recommendation for a universal 50-minute cap. **High confidence that the distinction matters; medium confidence about the size of any time reduction.**

3. **Make `HOME` a scheduled, bounded commitment instead of a recurring open container.** Keep the name, select one real action, and give it a feasible cue or slot. If there is no capacity today, defer that selection explicitly while preserving the underlying task. Ten appearances with one completed session is the clearest planning/work mismatch in the current menu. Do not hide HOME merely to improve appearances. **High confidence in the recorded mismatch; medium confidence about unlogged home activity.**

4. **Keep `READ`, but specify the question or learning purpose before starting.** For project research, stop when the relevant question is answered or the planned reading block ends; record the decision or next test. For learning, use brief recall and a later revisit. The 470 reading minutes in the last complete week justify inspecting value, not automatically cutting reading. Consider a new `LEARN` or `DECIDE` name only if a recurring distinction changes your choices; do not globally rename READ now. **Medium-high confidence.**

5. **Give `BUILD` and `FIX` distinct result definitions and keep one primary deliverable in focus.** BUILD creates or extends; FIX restores expected behavior. Select the task before entering the block, continue with that deliverable across adjacent sessions when useful, and leave a return note before switching away. Keep both names initially; if you repeatedly cannot make the distinction or it never changes a decision, simplify prospectively after the trial. **Medium-high confidence in clearer boundaries; medium confidence that two categories remain necessary.**

6. **Keep a small menu of roughly these six names without trying to use all six every day.** Retain the other names as hidden history. Avoid adding project names with `+` just to express ownership, and do not treat the current five-theme cap as a target to fill. Judge overload by real unfinished commitments as well as the theme meter. Six is a practical description of your current recurring vocabulary, not a research-derived optimum. **High confidence in avoiding needless expansion.**

7. **Defer color work and historical merges until they solve an observed problem.** If the old collisions impede a chart you use, the existing suggestions—`bob themes color CLEANUP blue` and `bob themes color MEMORY orange`—are reasonable. For a verified synonym, start with a preview such as `bob themes rename FIXES FIX --merge --dry-run`. Preserve meaningful distinctions and historical comparability. Neither recoloring nor reducing the catalog below 76 is likely to improve your attention as much as the changes above. **High confidence in this lower priority.**
