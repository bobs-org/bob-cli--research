# Six themes, clearer commitments: an independent review of Bryan's Pomodoro taxonomy

Independent researcher: **cdx**. Research date: **2026-10-27**. Evidence: the supplied theme list, read-only Bob commands against the live vault, the bob-cli implementation and contracts, and independently consulted external sources. No other report, transcript, or findings from this research swarm were consulted.

Your six visible themes are a reasonable working vocabulary. I would keep that small set initially and change the rules governing it: narrow and time-budget GTD; give HOME a real execution commitment; clarify when career-oriented work belongs to JOB; and distinguish producing, repairing, and understanding without turning every session into several overlapping labels. The strongest evidence for change concerns what the labels permit and reveal, rather than their spelling.

The most consequential findings are that review accounts for about **31% of recorded time** in the last four complete weeks, HOME has **one completed session alongside repeated placeholders**, and JOB sometimes contains the same reading work that appears under READ. None establishes procrastination, waste, or neglected responsibilities. Together they identify where a clearer contract could make the system more useful.

## What I examined, and what the numbers mean

The live `bob themes list -f json` matched the supplied snapshot: 76 known themes, 70 hidden, six visible, five present today. The visible themes were GTD, BUILD, JOB, HOME, FIX, and READ. The installed executable reported `bob 0.3.1`; implementation references below use bob-cli commit `4cc0ef7dc131fb43570275716517de6cd9407a9b`.

I also examined completed-session statistics for **September 29 through October 26, 2026**, an inclusive 28-day window ending before the incomplete current day. I used Bob's own statistics and ledger interfaces, rather than independently parsing the vault. Selected historical task queries covered October 17, 22, and 25; I inspected ledger links and notes, not the research documents those links point to.

Several distinctions are essential:

- **Catalog presence is not execution.** `days_used` counts dates with a theme in canonical daily notes, including open plans. `entries` includes open and closed entries. A label can recur without any completed work.
- **“Last 90 days” filters which catalog rows appear.** The implementation retains cumulative usage counts through today; it does not turn the displayed counts into a 90-day time allocation. In this particular six-theme sample, all first-use dates happen to fall inside 90 days anyway.
- **“Five today” is not five active work themes.** At the first live inspection GTD was completed; JOB, BUILD, FIX, and HOME were open. `bob plan` reported **4/5 themes** and **6/15 links**. Your configured theme cap is five; the documented default of three is not your live setting.
- **Hidden means omitted from Recent suggestions.** Hidden themes remain in history and Stats and can still be typed. Seventy hidden names therefore do not mean seventy daily decisions or seventy abandoned projects.
- **Recorded time is not all waking time.** Unlogged care, leisure, exercise, errands, work, and brief tasks are outside this measurement. A theme's absence cannot establish an absence from your life.

These meanings come from the [theme contract](https://github.com/bobs-org/bob-cli/blob/4cc0ef7dc131fb43570275716517de6cd9407a9b/docs/pomodoro-themes.md), [catalog aggregation](https://github.com/bobs-org/bob-cli/blob/4cc0ef7dc131fb43570275716517de6cd9407a9b/src/native/pomodoro_themes/mod.rs), and [list filtering](https://github.com/bobs-org/bob-cli/blob/4cc0ef7dc131fb43570275716517de6cd9407a9b/src/native/pomodoro_themes/cli.rs), corroborated by the live commands.

| Theme | Catalog days / entries through Oct 27 | First recorded use | Completed theme minutes, Sep 29–Oct 26 | Share of all recorded minutes |
| --- | ---: | --- | ---: | ---: |
| GTD | 54 / 142 | Aug 28 | 2,310 — 38h 30m | 31.1% |
| BUILD | 30 / 92 | Aug 27 | 1,585 — 26h 25m | 21.3% |
| JOB | 20 / 89 | Oct 7 | 1,315 — 21h 55m | 17.7% |
| HOME | 11 / 11 | Oct 10 | 25m | 0.3% |
| FIX | 5 / 8 | Sep 6 | 150 — 2h 30m | 2.0% |
| READ | 15 / 45 | Sep 21 | 645 — 10h 45m | 8.7% |
| Other historical themes combined | Not comparable to the six-row snapshot | Various | 1,405 — 23h 25m | 18.9% |
| **All themes** | — | — | **7,435 — 123h 55m** | **100.0%** |

The time table uses the `worked` metric's `parts.theme`, summed across daily points. Its denominator includes review. Rounded shares need not sum exactly to 100. There were **294 completed sessions**, all with `quality: ok`, and 28 days with data. Bob's separate `review_time` total was **2,298 minutes**, or **38h 18m and 30.9%** of recorded time. Its median was **55 minutes per day**, versus a mean of about 82; several long days raise the mean. The 12-minute difference between review attribution and GTD-theme time is expected because the two classify sessions differently.

The 28-day history contains 24 distinct theme components, but that does not describe the present menu. In the final seven days, completed work used only **GTD, BUILD, JOB, READ, and FIX**; HOME was planned but had no completed minutes. This is consistent with an already simplified current vocabulary, although historical renames mean the ledger cannot prove when that simplification happened.

## How your themes actually function

**GTD is a control loop with a special software exemption.** Its regularity is unsurprising for a daily review practice. The recent sample nevertheless makes its scope worth examining: 38 hours of attributed review is a substantial allocation. October 24 alone contains eight completed GTD sessions totaling 150 minutes, interspersed with BUILD. That might represent useful recurring triage, a difficult backlog, recording conventions, or avoidable reopening of the system. The ledger does not distinguish those explanations. Most sampled GTD links point to the daily review row, which records purpose but not a detailed breakdown of what happened inside it.

A further measurement limitation matters here: a wholly exempt named session is attributed to the review bucket regardless of its task links. The review statistic is therefore partly a consequence of the label you chose. It is not an independent observation that every minute was spent reviewing. The appropriate response is a brief content audit, not a declaration that 31% is intrinsically too much.

**BUILD is mostly product/tool development, not everything constructive.** Of the 1,550 minutes in sessions named exactly BUILD, Bob attributed 1,425 to Bob and its `bob_gtd` subproject—about 92%. Another 35 theme minutes came from a composite session, explaining the 1,585-minute table total. This concentration makes BUILD more coherent in practice than the word alone suggests. Thirteen of its 65 exact-name sessions had multiple homes, however, so a single BUILD label does not guarantee a single working context.

**JOB expresses a purpose that crosses project boundaries.** The 1,315 minutes include application and CV projects, but also 389 minutes attributed to `sase_blog`, plus other software projects. That can be sensible if publishing and tooling support the current career effort. It should not be assumed to mean paid employment or an employer's project. On October 22, the same code-review reference task appeared in two completed READ sessions and in an open JOB session. On October 25, completed JOB sessions linked to a blog-planning reference. These examples show a real overlap between activity and purpose, without proving that either classification was wrong.

**HOME currently acts more like a holding place than a reliable record of personal execution.** Between its first recorded use on October 10 and October 27, I found 11 HOME entries: one completed session and ten untimed open placeholders. Nine placeholders are on past dates; one is today's plan. The completed October 17 session points to the `dev_plex_hack_patch` project. October 22 and 25 repeat the same three personal-maintenance task links, spanning hardware maintenance, administration, and backup work. Today's HOME also includes a care task. This is broader than housework or physical location.

That is evidence of repeated planning and limited session closure, not a 9% task-completion rate. The denominator is ledger entries, the tasks may repeat, some work may happen outside Pomodoros, and old open entries are not themselves a longitudinal record of every edit. The useful question is whether HOME is meant to book real capacity or merely keep reminders visible.

**FIX is small but potentially valuable.** Five exact-name completed sessions account for 150 minutes across three days, primarily attributed to SASE. The present open task concerns reliability. This supports an initial distinction between extending capability and restoring expected behavior. It does not establish that maintenance is only 2% of your work: repairs may also occur under BUILD, JOB, or older labels. A small category can still be useful if it protects capacity or exposes recurring operational problems.

**READ is strongly tied to ongoing engineering decisions.** All but 25 minutes of its recent attribution resolve to named projects or review; 355 of 645 minutes—55%—are attributed to `sase_pypi_releases`. Sampled task links concern code review, release reliability, merge queues, and delegation. This looks substantially like technical investigation and reading supporting current projects. It is not evidence of a broad leisure-reading habit, nor evidence that you lack one. It also means that “read more books” would be poorly targeted advice for this theme.

Home attribution in these observations is a derived allocation, not a stopwatch per project: Bob divides session time among linked tasks and uses the current note hierarchy. The report exposed 65 unlinked minutes, one unfiled link, and no unresolved or ambiguous home links. The separate historical Dataview queries emitted general link-ambiguity warnings; the examples above rely on explicit returned ledger links, not guessed resolutions. See the [Stats definitions](https://github.com/bobs-org/bob-cli/blob/4cc0ef7dc131fb43570275716517de6cd9407a9b/docs/stats.md) and [Pomodoro home rules](https://github.com/bobs-org/bob-cli/blob/4cc0ef7dc131fb43570275716517de6cd9407a9b/docs/pomodoro-homes.md).

## What established practices support—and what they do not

There is no research result establishing these six names, a particular color scheme, or a universally optimal number of personal themes. The useful comparison is between functions: clarifying commitments, protecting attention, choosing executable work, learning from completed work, and keeping maintenance costs proportionate.

| Established practice or evidence | Relevant principle | Application to your system | Strength and limit |
| --- | --- | --- | --- |
| GTD's Horizons of Focus | Ongoing responsibilities, finite projects, and next actions answer different questions. | JOB can represent a commitment; READ an activity; a linked task supplies the concrete action. Keep those distinctions explicit. | Primary methodology, not a controlled test of theme names. [David Allen Company](https://gettingthingsdone.com/2018/12/the-gtd-horizons-of-focus-for-determining-your-priorities/) |
| GTD's three kinds of work | Defining work, executing predefined work, and handling arriving work are all legitimate. | Keep GTD for clarification/review; give project execution and technical system-building their own honest labels. | Practitioner framework. It does not prescribe a universal review percentage. [Allen's original essay](https://gettingthingsdone.com/wp-content/uploads/2014/10/Threefold.pdf) |
| Original Pomodoro practice | Choose an activity, observe interruptions, compare estimates with experience, and include recovery. | A theme needs a bounded task or outcome underneath it. Counting labels or completed timers is insufficient. | Creator's account, not comparative efficacy evidence. [Francesco Cirillo](https://www.francescocirillo.com/blog/pomodoro-technique-was-never-just-a-timer/) |
| Time blocking | Assign work to available time and revise the plan when reality changes. | Replace recurring HOME placeholders with a feasible appointment when HOME matters that day. | Practitioner technique. Newport's productivity claims are not effect estimates applicable to you. [Cal Newport](https://calnewport.com/focus-week-take-control-of-your-time/) |
| Personal Kanban | Make commitments visible and limit work in progress. | Limit distinct outcomes competing for attention, not just the number of category names. | Three is an explicitly arbitrary starting heuristic, not a cognitive constant. [Jim Benson](https://personalkanban.com/pk/uncategorized-how-to-setting-your-personal-wip-limit/) |
| PARA | Separate active outcomes, continuing responsibilities, reference material, and inactive material. | Bob already supplies project/area structure and hidden historical themes. Avoid duplicating the entire hierarchy in the theme menu. | Information-organization method, not a scheduling prescription. [Tiago Forte](https://fortelabs.com/blog/para/) |
| Attention-residue experiments | Attention can remain with an unfinished task after switching and impair the next task. | Moving between two unrelated BUILD tasks can be a consequential switch despite an unchanged theme. | Leroy's 2009 paper reports two experiments; it does not establish a universal recovery time. [Original paper](https://www.sciencedirect.com/science/article/pii/S0749597809000399) |
| Ready-to-resume research | Briefly planning a return to interrupted work can help attention move to the intervening task. | Leave one concrete resumption note before switching projects or reacting to an agent result. | Four studies support a specific intervention; transfer to your workflow is an inference. [Leroy and Glomb, 2018](https://experts.umn.edu/en/publications/tasks-interrupted-how-anticipating-time-pressure-on-resumption-of/) |
| Progress-monitoring meta-analysis | Interventions increasing progress monitoring improved goal attainment on average. | Review what each theme accomplished, not only how often its name appeared. | 138 randomized studies, 19,951 participants; mean goal-attainment effect d = 0.40. This does not mean more tracking is always better. [Harkin et al., 2016](https://www.apa.org/pubs/journals/releases/bul-bul0000025.pdf) |
| Time-management meta-analysis | Time management is associated with performance and wellbeing; the latter is not merely incidental. | Evaluate clarity and personal obligations alongside output. | 158 studies with mixed designs and heterogeneous effects; no validation of a particular taxonomy. [Aeon, Faber, and Panaccio, 2021](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0245066) |
| Google SRE's toil distinction | Repetitive, automatable operations differ from engineering that makes lasting improvements. | Separate repeated repair from removing its cause, even if both initially appear under FIX. | Useful engineering analogy; Google's 50% operational-work policy is not a personal budget recommendation. [Vivek Rau](https://sre.google/sre-book/eliminating-toil/) |
| Learning-technique review | Retrieval practice and spaced practice generally have stronger support for durable learning than rereading. | When READ is for retention, add a brief recall or application step. | Educational evidence; decision-oriented document review and pleasure reading have different goals. [Dunlosky et al., 2013](https://journals.sagepub.com/doi/10.1177/1529100612453266) |

One particularly relevant qualification comes from GTD's own coaching: defining work is real work, but allowing it to displace all execution is a problem. The same source notes that some high-input workloads legitimately need substantial processing time. That supports examining what your GTD sessions contain before cutting them to an arbitrary 25-minute ceiling. [GTD: Getting to inbox zero](https://gettingthingsdone.com/2018/10/getting-to-inbox-zero/)

## Choosing a taxonomy that fits Bob

Your current system mixes **purpose** (JOB, HOME), **activity** (BUILD, FIX, READ), and **coordination** (GTD). A textbook taxonomy might insist on one dimension. For your scheduling use, that would be too strong a demand: a hybrid can be useful when its categories represent choices you actually make, and when a consistent precedence rule resolves overlap.

Three alternatives are worth comparing:

| Approach | Example vocabulary | Main benefit | Main cost for you |
| --- | --- | --- | --- |
| All domains or projects | JOB, BOB, SASE, HOME | Obvious beneficiaries; project concentration becomes visible in names. | Duplicates Bob's existing home/project attribution and hides the distinction between building, repairing, and reading. |
| All activities | BUILD, FIX, READ, ADMIN, REVIEW | Cleaner comparison of how work is performed. | Career and personal obligations lose a prominent claim on the day; demands more reliable project attribution and separate capacity planning. |
| Current hybrid, with explicit rules | GTD, BUILD, JOB, HOME, FIX, READ | Preserves familiar choices and protected commitments with low migration cost. | Theme totals cannot simultaneously be complete domain totals and complete activity totals. |

**I favor the third option for an initial experiment.** The mismatch is manageable, whereas a wholesale redesign would change both behavior and measurement at once. Use themes to answer “What kind of commitment am I choosing for this block?” Use task links and homes to answer “Which project or responsibility benefits?” Use the task's outcome to answer “What would count as progress?”

A workable precedence rule is:

1. Use **GTD** for running the review/clarification process itself.
2. Use **JOB** when the block was explicitly reserved for a concrete career outcome; use **HOME** when reserved for a concrete personal-maintenance outcome.
3. Otherwise use **BUILD**, **FIX**, or **READ** according to the primary outcome: new capability/artifact, restored or maintained function, or understanding/decision.

This is a proposed convention, not a claim that you already follow it. Decide it before starting a block. For example, researching an interview answer belongs to JOB when it is part of an interview-preparation commitment. A separate session studying release-system design belongs to READ. Reading documentation incidentally while delivering a feature remains BUILD. The verb on a momentary action should not force the session to change themes every few minutes.

The tradeoff is deliberate: under this convention, READ means “blocks primarily reserved for reading outside the protected JOB/HOME commitments,” not every minute your eyes encounter text. Similarly, BUILD is not a complete census of all construction across your life. If comprehensive activity reporting becomes the overriding need, adopt the activity-only alternative instead of pretending this hybrid supplies it.

### Why routine `JOB + READ` tagging would be misleading

Bob's `+` components are not independent facets. Every non-exempt component counts toward the plan cap, and Stats splits a session's theme minutes between components. A 50-minute `JOB + READ` session contributes approximately 25 minutes to JOB and 25 to READ; it does not report 50 minutes of career work and 50 minutes of reading.

The observed October 16 `GTD + BUILD` session illustrates this distinction: its 70 minutes become 35 minutes in each theme, while review attribution uses separate home rules. That is an allocation convention, not a measurement of what fraction of attention went where.

Prefer one primary theme and the existing task/home information. Use a composite when the session really contains a mixed allocation and equal splitting is an acceptable approximation. When the split matters, close one timed session and start another. A new faceted-reporting feature might someday be useful, but it is unnecessary for the present recommendations. These constraints are documented in [Stats](https://github.com/bobs-org/bob-cli/blob/4cc0ef7dc131fb43570275716517de6cd9407a9b/docs/stats.md) and [the plan budget](https://github.com/bobs-org/bob-cli/blob/4cc0ef7dc131fb43570275716517de6cd9407a9b/docs/plan.md).

### Proposed boundaries for the existing six

| Theme | Proposed inclusion rule | Boundary to enforce | Useful stopping condition |
| --- | --- | --- | --- |
| GTD | Capture clarification, review, triage, deciding commitments. | Implementing Bob/SASE features is BUILD or FIX even if the product improves GTD. | Review pass or chosen triage batch finished; next commitments clear. |
| JOB | A block explicitly serving a named career opportunity or milestone. | Portfolio/tool work needs a stated career connection, not merely possible future usefulness. | Application submitted, assessment advanced, interview prepared, or a bounded portfolio deliverable completed. |
| HOME | A scheduled personal-maintenance or care batch, including household technology and administration. | Neither “anything done at home” nor an indefinite miscellaneous queue. | One important obligation resolved, or a deliberately bounded batch finished. |
| BUILD | Produce or extend a chosen artifact, capability, or system outside a protected purpose block. | Several unrelated projects do not become one context because they all involve building. | A named increment reaches its planned acceptance point. |
| FIX | Restore expected behavior or complete a deliberately selected maintenance intervention. | A surprising task is not automatically a fix; recurring operations are not automatically valuable engineering. | Failure resolved, cause isolated with a next step, or maintenance check complete. |
| READ | Understand material to answer a question, make a decision, or learn something chosen. | Opening more references is not itself the stopping rule. | Decision made, useful explanation recalled, application tried, or intended reading completed. |

These are operating definitions, not new metadata fields. One short note on the task or session is enough. The aim is less classification hesitation, not a second administrative system.

## A small experiment before any global rename

Keep all six spellings and colors for **14 days**. Apply the boundaries above; focus the first week on GTD and HOME. At the second weekly review, decide whether any naming change would make the boundaries easier to remember. The trial length and thresholds below are proposed conveniences, not research-established optima.

For GTD, use one short session note identifying the dominant activity on unusually long review days: clearing incoming material, reviewing commitments, making higher-level decisions, or drifting into tool implementation. Test a planned stopping point around your observed ordinary-day median of 55 minutes, with explicit extensions when needed. Do not aim to reduce the number merely by relabeling the same work. Any implementation time moved to BUILD should remain visible in the total.

For HOME, choose a real slot when an obligation merits one, with one must-finish action first. If it is a tiny task done outside a timed block, complete the task normally; do not manufacture a Pomodoro to make the chart look better. A past open placeholder should trigger a fresh decision about today's capacity, not automatic evidence that the commitment has been honored.

For JOB, distinguish direct opportunity work and enabling portfolio work in the task outcome or a brief session note. Do not add two permanent themes yet. At review, ask whether the enabling work made an application, assessment, interview, or public deliverable concretely more ready. A bounded publication task may qualify; open-ended infrastructure improvement should not qualify by association alone.

For BUILD/FIX/READ, select a primary project and one next outcome before starting. When an agent finishes unrelated work, capture the follow-up and review it at a chosen boundary unless it is urgent or blocks the current task. Before a switch, leave a short resumption note: where you stopped and the next action. This applies the attention research to your agent-heavy workflow; no data here measures the number or cost of your agent interruptions directly.

Use a very small review table:

| Question | Evidence to inspect | What would justify a change? |
| --- | --- | --- |
| Is GTD buying useful clarity? | Minutes, the few long-session notes, unresolved commitments, perceived control. | Repeated tool-building inside GTD, or review overruns without clearer choices. |
| Does HOME turn intention into action? | Planned batches and actual task completions, including work outside Pomodoros. | The same intended batch rolls forward repeatedly without an explicit capacity decision. |
| Does JOB advance the current career goal? | Concrete deliverables, separating direct and enabling work. | Enabling work repeatedly replaces the next direct step without a named dependency. |
| Are BUILD, FIX, and READ easy to choose? | A quick mark only when classification is genuinely ambiguous. | Several consequential ambiguities per week, rather than occasional edge cases. |
| Is the day manageable? | Actual unfinished commitments, meaningful outcomes, and a simple end-of-day control/strain judgment. | Lower label counts coexist with more unfinished outcomes or worse control. |

No target ratio between BUILD and FIX follows from this report. Nor should HOME be forced to match JOB's hours. Allocation depends on current obligations and choices, while this ledger measures only a selected part of them.

## Safe interpretation and migration

**Keep the hidden catalog.** You already separated a small suggestion set from a long historical record. A historical label is not a debt requiring deletion. Only revive a hidden theme when a recurring decision would become easier—not merely because an old topic exists.

**Keep the current colors initially.** The five visible non-exempt themes have different hues, and GTD's muted state carries a distinct meaning. Live hints concerned BUILD/CLEANUP and HOME/MEMORY, not a collision among the six visible names. Color changes offer little apparent benefit now. JOB's aqua comes from an area match; renaming it can remove that automatic relationship. Do not infer meaning from the hash-derived colors of BUILD, FIX, HOME, or READ.

**Treat renaming as a historical rewrite.** `bob themes rename` rewrites canonical past, present, and future daily entries plus the daily template. It is appropriate for a spelling correction or a stable meaning-preserving rename. It is unsuitable for claiming that old undifferentiated READ sessions were all active study, or that old JOB sessions all meant a newly narrowed career definition. A semantic change can instead begin prospectively, with its start date recorded and the old name hidden when appropriate.

A HOME-to-`LIFE ADMIN` rename is plausible if you conclude that the entire historical category already meant personal upkeep. It is less attractive if HOME intentionally includes care and leisure that “admin” would obscure. Likewise, FIX-to-MAINTAIN is useful only if preventive maintenance really belongs in the category; it should not broaden the category merely to sound more polished. Keep JOB unless a different term solves an actual interpretation problem. Keep GTD exempt while auditing its content; renaming an exempt/config-referenced name needs coordinated configuration handling.

For a later meaning-preserving HOME rename, the **preview-only** command would be:

```sh
bob themes rename HOME 'LIFE ADMIN' -d -f json
```

Inspect the preview's history, state, and color changes. If the target already exists, do not merge it without checking whether its prior meaning matches. No theme, preference, plan limit, configuration, or vault content was changed during this research. The relevant safeguards are in the [global rename contract](https://github.com/bobs-org/bob-cli/blob/4cc0ef7dc131fb43570275716517de6cd9407a9b/docs/pomodoro-themes.md#pt10--global-rename).

## Reproducibility and remaining uncertainty

The principal read-only commands were:

```sh
bob --version
bob themes list -f json
bob plan -f json
bob stats metrics -f json
bob stats show worked review_time sessions \
  -r 2026-09-29..2026-10-26 -g day -f json
bob capture-pomodoros -a -t -f json
```

For HOME history I called `bob capture-pomodoros -a -f json` with `BOB_NOW` set to noon on each date from October 10 through October 27, and selected entries named HOME. For the three historical examples, I used `bob query -f json` with:

```text
TABLE file.tasks AS Tasks
FROM "2026"
WHERE file.name = "20261017"
   OR file.name = "20261022"
   OR file.name = "20261025"
```

The table's exact-name home breakdowns sum `sessions[].homes.parts[].minutes` after filtering `sessions[].name`; theme totals instead sum `metrics[worked].points[].parts.theme`. This distinction accounts for composite-session differences. Dates and line locations of the main examples are October 17 line 31; October 22 lines 29–41; and October 25 lines 54–71. Line positions may change with later edits.

Bob derives historical home allocations from the current note tree, and global theme renames can rewrite historical names. Re-running the commands later can therefore produce different attribution even for the same date range. First-use dates cannot establish when you first adopted a concept, or whether a previously different label was merged into it.

The unresolved questions are whether long GTD sessions contain work beyond review, whether HOME work is happening without session closure, and which portfolio activities you deliberately regard as JOB. Those questions affect the strength of the behavioral recommendations, but they do not prevent a useful first experiment. The evidence does not justify a diagnosis of avoidance, a prescribed personal-time quota, a universal daily theme count, or a claim that six categories are scientifically optimal.

## Ranked changes to consider

1. **Narrow GTD's boundary and give its time an explicit stopping decision.** Keep its exemption and muted color, but reserve it for clarification and review. Put tool implementation under BUILD or FIX. At 30.9% of recorded time, this is the highest-leverage category to audit. Start from your observed 55-minute median rather than an invented ideal, and permit deliberate extensions. **Confidence: high in the need to inspect; medium that time should decrease. Cost: low.**

2. **Make HOME a scheduled personal-maintenance commitment, rather than a recurring placeholder.** Choose one meaningful action and a feasible slot on days you intend to do it; count task completion outside Pomodoros too. The one completed session and ten placeholders make this the clearest intention-versus-recorded-execution discrepancy. Consider `LIFE ADMIN` only if that wording accurately covers the category's existing scope. **Confidence: high in the discrepancy; medium in the behavioral explanation. Cost: low.**

3. **Define JOB by a concrete career outcome and separate direct progress from enabling work during review.** Keep JOB prominent and aqua. Require portfolio, reading, or infrastructure work to name the career milestone it advances. The same reference appearing under READ and JOB shows why an explicit purpose rule matters. Prefer a short outcome note over new permanent subthemes. **Confidence: high that the boundary needs clarification; medium on whether allocation should change. Cost: low.**

4. **Keep BUILD and FIX separate, but anchor each block to one primary project and result.** BUILD advances capability; FIX restores or deliberately maintains it. Do not merge them merely because FIX is infrequent, and do not call all repairs “toil.” If preventive maintenance becomes a sustained part of FIX, consider MAINTAIN prospectively. **Confidence: medium-high. Cost: low.**

5. **Keep READ, but make its intended result explicit: decide, understand, retain, or enjoy.** Your current READ largely supports engineering projects. For decision reading, finish with a decision or next action; for retention, add recall or application; for pleasure, impose no productivity artifact. Rename to LEARN only if the actual scope expands to practice and learning beyond reading. **Confidence: high on defining purpose; low that renaming is needed. Cost: low.**

6. **Keep six available themes while selecting fewer major commitments for an ordinary day.** Trial two or three substantive commitments plus necessary review/personal upkeep when feasible; treat that as an experiment, not a law. Your current 4/5 meter is within your configured cap. Focus on unfinished outcomes and project switches before changing the cap, and avoid counting every JOB/READ or HOME/FIX facet as a second theme. **Confidence: medium. Cost: low; no configuration change required initially.**

7. **Preserve the 70 hidden themes and existing color scheme; make renames only when meaning is stable.** The current menu is already small and visually distinct. Historical cleanup is lower value than clearer use, and a global rename can conceal changes in meaning. Prefer a dated prospective convention when the category itself changes. **Confidence: high. Cost: negligible.**

8. **Add or split a theme only after the two-week trial reveals a recurring decision the six cannot express.** An extra theme should change what you schedule, what you stop doing, or what you can usefully review. Do not add HEALTH, SOCIAL, WRITE, LEARN, or ADMIN simply to make the palette look comprehensive. Your existing task and area structure can represent those responsibilities without requiring every part of life to become a timed category. **Confidence: high as a restraint on complexity. Cost: negligible.**
