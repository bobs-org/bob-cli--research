# Six months of work, seven activity themes

**Independent researcher:** cdx  
**Audit date:** 2026-10-27  
**Requested window:** 2026-04-27 through 2026-10-26, inclusive; today is excluded.  
**Recommendation:** **PLAN · READ · BUILD · FIX · VERIFY · WRITE · CHORE**

Your proposed change makes sense. Themes can describe the activity you are doing, while linked tasks and their project/area homes describe what that activity is for. I recommend accepting **GTD → PLAN** and **HOME → CHORE** as forward-looking vocabulary changes, retaining **READ, BUILD, FIX**, retiring **JOB** from new sessions, and adding **VERIFY** and **WRITE**.

The most consequential addition is **VERIFY**. Your history repeatedly distinguishes requesting or making a change from personally testing, reviewing, or accepting its result. That distinction matters in your agent-assisted workflow. **WRITE** also has direct support, although less than software development: blog drafts, requirements, and application materials deserve a mode that distinguishes producing prose from reading about it.

This is a recommendation about future labeling, not a claim that every historical minute can be accurately reassigned. It also does not imply seven themes should be open every day.

## Evidence, coverage, and limits

I read the user-specified [earlier six-theme review](pomodoro_six_theme_review/pomodoro_six_theme_review.md) as shared context, then independently queried Bob's current ledger, completed tasks, and theme catalog. I did not consult any other report or researcher from this swarm.

The earlier review recommended keeping a hybrid purpose/activity vocabulary. Your new preference changes that premise. Its argument for preserving JOB as a cross-project career category does not require keeping JOB in the activity slot. The tradeoff remains real: a career-wide total that includes both job applications and SASE promotion may need an explicit project grouping; the existing `job` area alone does not necessarily capture it.

### What the available records cover

Bob reports **1,178 closed Pomodoro rows and 40,755 recorded minutes (679h 15m)**. There are **152 days with ledger data**, including one zero-session day, August 4, and **151 days with closed sessions**. The first timed record in this window is May 28. The preceding **31 days, April 27–May 27, lack usable timed ledger data**. Earlier daily notes contain navigation and some routine checklist material, but those are not evidence of completed timed work.

| Period | Closed session rows | Recorded time | Nonrecurring dated completion rows |
|---|---:|---:|---:|
| Apr 27–May 27 | No usable timed records | Unknown | None returned |
| May 28–31 | 21 | 14h 45m | 40 |
| June | 223 | 128h 25m | 296 |
| July | 188 | 118h 25m | 250 |
| August | 250 | 159h 00m | 343 |
| September | 222 | 146h 40m | 150 |
| October 1–26 | 274 | 112h 00m | 607 |
| **Total available** | **1,178** | **679h 15m** | **1,686** |

The completion total independently reconciles between `bob stats` and the Tasks query after excluding recurring tasks and the daily `^gtd` row. The full dated query returned 2,764 rows: 996 recurring completions, 82 daily review rows, and these 1,686 other completions. These are **task rows, not unique deliverables**; parent tasks, subtasks, reference records, and repeated versions can all count separately.

Several limitations constrain interpretation:

- **Historical names are weak evidence.** There are 645 unnamed sessions, containing 24,225 minutes, or **59.4% of recorded time**. The first named closed session in this window is August 26. The earlier review also documents October's retroactive theme renames.
- **Recorded time has small visible defects.** May 28 repeats both its 1105–1245 and 1345–1410 migration entries verbatim. Removing one copy of each would reduce the raw total by 125 minutes to **677h 10m**, with 1,176 rows remaining. I retain Bob's raw total for reproducibility, not as an exact stopwatch total. June 4 also has one closed untimed placeholder; it contributes a row but no minutes. Fifteen sessions use time-range fallback rather than a recorded duration.
- **Links are not a stopwatch.** Many sessions contain several tasks, sometimes in several modes. A link establishes association, not the time spent on each activity. I do not split every mixed session equally into invented activity totals.
- **Review attribution is especially broad.** Bob attributes 10,862 minutes to its review bucket, but naming/exemption and review-link rules can send an entire mixed session there. This is not a measurement of pure planning time.
- **Personal life is under-recorded.** Timed records are dominated by development and review. Purchases, payments, communications, and other upkeep also appear in completed tasks, even when not separately timed. Absence of logged time does not establish absence of that work.
- **Completion counts are sensitive to conventions.** There are 255 reference-tagged/reference-ID completion rows; 223 of the 300 broader reading-signal rows occur in October. Changed recording conventions and multiple reference representations mean this is not evidence that reading suddenly increased by that ratio.

**Method:** I extracted all 1,178 closed-session facts, joined every one to its daily-note list row, and inspected a reproducible sample of 96 sessions: 16 selected independently within each represented month, May–October, using Python `random.Random(20261027)` on the chronological session lists. I supplemented that sample with targeted inspection of verification, writing, upkeep, and application records. I screened all 1,686 completion descriptions for recurring activities. This is a full-record extraction with sampled and targeted semantic review, not exhaustive human coding of every session.

## What your work actually contains

### 1. Choosing and organizing work is a durable activity: PLAN

Daily review is present long before named themes. June 6 and June 15 have short sessions linked only to `gtd_daily`; September and October repeatedly have GTD sessions linked to the daily review row. Your recurring completion history includes 120 calendar-review rows, 116 Keep-inbox imports, and multiple generations of backlog and daily-planning checklists.

There is project planning too. On **August 11**, four successive sessions totaling **130 minutes** link only to `done/sase_done#^plan-art-and-cars`, whose task is to clean up and plan the artifact roadmap. A fifth session mixes that roadmap with implementation work. On **October 26**, JOB sessions at lines 49 and 54 contain the blog's task-review item, not prose drafting.

**Implication:** PLAN is a better name than GTD for the activity. Define it as clarifying commitments, choosing priorities, scoping work, sequencing tasks, and reviewing what needs doing. It should not absorb every action triggered by the morning checklist.

**Evidence:** `2026/20260606.md:38`; `2026/20260615.md:24`; `2026/20260811.md:34`; `2026/20261026.md:49`; `done/sase_done.md#^plan-art-and-cars`; `done/sase_blog_done.md#^review-tasks`; recurring completion query.

### 2. Reading spans every project: READ

Reading predates the current READ label. May 29 explicitly records finishing the Obsidian workflow roadmap and reading capture research. June 7 includes a session on a SASE popularity-strategy reference. July includes beads and agent-workflow research; August includes monitor research; September includes goals research; October includes application recommendations, software articles, and blog materials.

A conservative text screen finds **300 completed rows** that either carry `#ref`/the `ref` block ID or begin with “Read.” This is a count of reading signals in task records, not 300 distinct documents and not a time estimate.

**Implication:** READ should apply regardless of whether the beneficiary is SASE, Bob, your blog, or your job search. It can include listening to a reference and taking ordinary comprehension notes. Reading a report does not become BUILD because an agent wrote it or because you plan to implement its recommendations later.

**Evidence:** `2026/20260529.md:50`; `2026/20260607.md:41`; `2026/20260727.md:34`; `2026/20260813.md:36`; `2026/20260926.md:34`; `2026/20261012.md:49`; `2026/20261023.md:37`.

### 3. Creating capabilities remains the main technical mode: BUILD

Feature creation occurs throughout the usable window: capture keymaps in May, prompt and task features in June, configuration and agent-family features in July, artifact and memory systems in August, remote-agent and capture features in September, and Bob refinements in October.

**397 completed rows begin with Add, Create, Implement, or Integrate.** That is a reproducible creation-language signal, not 397 cleanly classified BUILD tasks: creating a project note, for example, can be PLAN. The dated examples establish the stronger point without relying on that count alone.

Your own contribution often involves writing a prompt, launching an agent, refining requirements, or guiding implementation. These belong with the change they are intended to produce. A dedicated AGENT theme would mostly record the tool or executor rather than the kind of work.

**Implication:** BUILD includes producing or substantially improving functioning systems, configurations, workflows, and prototypes. It includes implementation design and engineering prompts when they are part of making that change. Count your engaged work, not the agent's unattended elapsed runtime.

**Evidence:** `2026/20260616.md:31`; `2026/20260710.md:36`; `2026/20260820.md:42`; `2026/20260926.md:25`; `2026/20261024.md:46`; `2026/20261026.md:31`.

### 4. Restoring broken behavior is recurrent, not an occasional exception: FIX

**143 completed rows begin with Fix, BUG, Debug, or Troubleshoot**, with matching rows in every represented month. The detailed ledger includes broken prompt keymaps, failed installs, UI behavior, filesystem capacity, crashes, and release or synchronization problems.

September 12 links both restarting agents and investigating a nearly full disk. September 23 mixes new features with UI and link defects. October 13 combines reading with a crash-fix epic. These are exactly the combinations a project name cannot disentangle.

**Implication:** Keep FIX, but define it by **repair intent**, not urgency. A scheduled defect repair is still FIX. An urgent new feature remains BUILD. Diagnose an observed failure under FIX; use CHORE for a known routine restart with no investigation.

**Evidence:** `2026/20260528.md:32`; `2026/20260608.md:38`; `2026/20260716.md:43`; `2026/20260820.md:59`; `2026/20260912.md:25`; `2026/20260923.md:23`; `2026/20261013.md:54`.

### 5. Testing and accepting results merits its own theme: VERIFY

This is the strongest addition beyond your examples.

**30 completed rows begin with E2E, Verify, Proofread, or Final proofread**, distributed across June–October. That narrow screen omits some checks with other wording and includes some compound/project-level tasks. It nevertheless establishes repeated, explicit verification work.

Thirty-four closed sessions over **19 distinct days** link to identifiable block IDs from that cohort. Those sessions contain 1,160 minutes in total, but **1,160 is associated-session time, not verification time**, because many also contain implementation or repair.

Clearer examples show why the distinction is useful:

| Date and ledger location | Recorded activity | Current historical name | Proposed activity |
|---|---|---|---|
| June 2, line 52 | End-to-end test SASE variables | Unnamed | VERIFY |
| July 6, lines 32 and 37 | Test agent-family waiting and launch behavior | Unnamed | VERIFY |
| August 27, lines 51 and 53 | End-to-end test and review Bob's Git work | BUILD | VERIFY |
| October 2, line 33 | End-to-end test `sase listen` | READ | VERIFY |
| October 12, lines 51 and 54 | Final CV proofread | JOB | VERIFY |

These dates refer to `2026/YYYYMMDD.md`; lines are one-based. On July 6 the logs record actual failures, so a later session spent correcting those failures would become FIX.

**Implication:** VERIFY means deciding whether an existing result meets its requirements: acceptance tests, reproductions, code/plan review, proofing, and checking agent output. READ means understanding material. WRITE means changing the prose. The distinction is the intended result of the session, not whether your eyes happen to be reading text.

I prefer **VERIFY** to REVIEW because “review” already names your daily planning ritual. VERIFY also has prior use in your theme history, although its historical sessions were not perfectly pure.

### 6. Producing prose exists and should become visible: WRITE

The evidence is smaller and more mixed than for BUILD, FIX, or READ, but it is real:

- A June 14 completed task calls for a dictated brain dump of the first blog post.
- The blog outline task completed July 7; generating a first draft with Fable completed July 8.
- July 5 logs work on an agent-family requirements section alongside development.
- August 3 links creation of the full blog-post note alongside other work.
- **October 14, line 61** explicitly logs writing a draft cover letter within a 50-minute JOB session that also included an application and waiting for feedback.

The 50-minute session does not establish 50 minutes of writing. Nor does reading a generated introduction prove authorship. These limits are reasons to start labeling the activity prospectively.

**Implication:** WRITE should cover drafting and substantively revising prose, including blog posts, requirements documents, CV bullets, substantive application answers, and cover letters. Producing a document with an agent still counts when your attention is on authorship and revision. A routine message or form submission belongs in CHORE; final acceptance of a finished document belongs in VERIFY.

**Evidence:** `done/sase_blog_done.md:75`; `done/sase_blog_done.md#^outline`; `done/sase_blog_done.md#^fable-draft`; `sase_dyn_agent_fam.md#^reqs`; `2026/20260705.md:44`; `2026/20260803.md:25`; `2026/20261014.md:61`.

### 7. Upkeep is broader than HOME: CHORE

Your dated completions include purchases, payments, routine calls and emails, application submissions, and administrative paperwork. August 5 contains a 25-minute session on an exit packet. October 15 contains several short application-submission sessions. The current daily checklist also mixes planning with personal routines and machine/agent upkeep.

Operational upkeep recurs from July through October: restarting stopped work, restarting machines, clearing leftover agent records, dismissing yesterday's agents, and updating installations. Some such tasks are repairs or implementation in context, so I do not treat a “restart” keyword as a clean time category.

**Implication:** Rename the concept to CHORE and let it mean **routine execution and maintenance**, wherever it happens. It can include household errands, financial administration, submitting prepared applications, and routine computer or agent housekeeping. Its scope is not “anything outside development,” and it is not a judgment that the work is unimportant.

CHORE should exclude novel technical diagnosis (FIX), building an automation that removes recurring work (BUILD), thoughtful drafting (WRITE), and deciding which obligations to pursue (PLAN).

**Evidence:** `2026/20260805.md:44`; `done/cash_done.md#^goog-exit`; `done/sase_done.md#^relaunch-failed`; `done/sase_done.md#^restart-epics`; `done/sase_done.md#^clean-up-agents`; `2026/20261015.md:37`; `2026/20261015.md:39`; `gtd_daily.md`.

## A codebook you can use at the timer

Choose the theme by the **main intended result of this session**. Ordinary supporting steps stay inside it. Change the theme when you begin a distinct block with a different intended result; do not turn incidental reading, typing, or testing into constant timer changes.

| Theme | The result you are trying to produce | Use it for | Boundary |
|---|---|---|---|
| **PLAN** | A decision about what to do, when, or in what order | Daily/weekly review, prioritization, backlog clarification, project scoping | Engineering an implementation is BUILD; executing the checklist is not automatically PLAN |
| **READ** | Better understanding of existing material | Articles, reports, documentation, reference listening, comprehension notes | Checking whether a deliverable is acceptable is VERIFY |
| **BUILD** | A new or improved working capability | Features, automation, configuration, prototypes, implementation design and agent guidance | Restoring expected behavior is FIX |
| **FIX** | Broken behavior restored or a failure explained | Debugging, diagnosis, incident repair, correcting defects | Routine known maintenance is CHORE; acceptance testing alone is VERIFY |
| **VERIFY** | A judgment that something works or is ready | End-to-end tests, acceptance, code review, proofing, checking agent results | Understanding background is READ; substantive changes become BUILD/FIX/WRITE |
| **WRITE** | New or revised prose | Blog drafts, specs, requirements, CV and cover-letter content | Routine correspondence is CHORE; a final proof without revision is VERIFY |
| **CHORE** | An obligation discharged or routine state maintained | Errands, paperwork, submissions, inbox execution, machine/agent housekeeping | Planning obligations is PLAN; novel repair is FIX |

A practical tie-breaker is to finish this sentence: **“At the end of this block, I want ___.”** “A choice” points to PLAN; “understanding” to READ; “a working capability” to BUILD; “a repaired system” to FIX; “a verdict” to VERIFY; “a draft” to WRITE; “the routine obligation handled” to CHORE.

This is deliberately about the work mode, not the physical action. Reading code can be READ, FIX, or VERIFY. Typing can occur in all seven. The expected result provides the useful distinction.

### How a real project changes modes

Your application work illustrates the value:

| Activity within the same job-search project | Theme |
|---|---|
| Choose the next roles to pursue | PLAN |
| Read role descriptions or a research report | READ |
| Draft tailored CV bullets or a cover letter | WRITE |
| Proofread the finished application | VERIFY |
| Submit prepared materials and record the submission | CHORE |
| Repair an application helper that fails | FIX |
| Create a reusable application helper | BUILD |

All of these can retain the same task/project links. There is no need to turn JOB into seven new project names, and no reason to convert all old JOB sessions into WRITE.

Likewise, an agent is not a separate mode: request a new capability under BUILD, investigate its failure under FIX, test its output under VERIFY, read its research under READ, and clear routine failed-run clutter under CHORE. An unanswered technical question may justify a deliberate research session, discussed below.

## What I would not add yet

| Candidate | Evidence and cost | Recommendation |
|---|---|---|
| **RESEARCH / EXPLORE** | Investigation is present, but many “research” log entries mean launching a swarm or reading its report. Those do not establish a separate human research mode. | First candidate for an eighth theme if you repeatedly spend a block comparing sources, testing alternatives, or synthesizing an answer. Do not apply it to every swarm launch. |
| **OPS / ADMIN** | Real recurring work, but CHORE can cover routine digital and personal administration initially. | Split out OPS only if its growing time becomes a decision you want to track separately from life upkeep. |
| **DESIGN** | Requirements, architecture, and UX work recur, usually within building. | Keep implementation design in BUILD and prioritization in PLAN until that distinction is insufficient. |
| **TALK / MEET** | Calls and outreach appear; the available timed records do not establish a sustained separate meeting/interview mode. | Add when interviews, collaborative calls, or meetings become regular blocks. Do not infer that they never happen. |
| **PRACTICE / LEARN** | Reading is well evidenced; repeated deliberate exercises are not comparably established in this window. | Add PRACTICE if interview drills or skill exercises become regular. Avoid LEARN as a replacement for READ if it would blend consumption and practice. |
| **AGENT / MANAGE** | Delegation is ubiquitous and spans creation, repair, research, and checking. | Classify by the intended work result. A separate tool-based theme adds little. |
| **JOB / HOME / SASE / BOB** | These describe beneficiaries, locations, or projects. | Keep those meanings in task/project attribution rather than the activity vocabulary. |
| **MISC / DRIFT** | Some sessions have sparse or frustrated logs, but they do not justify a prospective work category. | Leave an honest session note when work derails; do not make a catch-all the normal planning destination. |

If seven feels cumbersome, a defensible six-theme version folds VERIFY into BUILD/FIX for technical checks and WRITE for editorial checks. I would prefer retaining VERIFY: your records show that accepting work is a recurring activity that the current scheme hides. Seven is a practical choice for this history, not a scientifically optimal number.

## Migration and a short trial

1. **Start with the seven-word codebook prospectively.** Use PLAN and CHORE for new sessions. Stop choosing JOB for new sessions; keep its historical meaning available. A mode change does not require rewriting six months of records.
2. **Treat global rename separately from a vocabulary decision.** Bob's theme rename rewrites canonical history and the daily template. Historical HOME included a renamed technical incident, and GTD included routine upkeep and implementation. A rename is not an accurate semantic recoding of those sessions. Preserve a transition date in your analysis of future statistics.
3. **Handle PLAN's exemption deliberately.** The current catalog marks GTD exempt. The CLI guards renames that leave config references inconsistent. More subtly, `pomodoro_homes/session.rs` treats a session whose components are all exempt as review and attributes the whole session to that bucket. If PLAN stays exempt and includes project roadmaps, those project-specific minutes can disappear from normal project attribution. Initially keeping PLAN narrowly for cross-project review avoids much of that ambiguity; counting all planning as PLAN may instead require reconsidering the exemption. Do not make CHORE exempt merely because it is routine.
4. **Keep one primary activity per normal session.** Bob splits composite theme attribution across components. `JOB + READ` is not a clean two-dimensional record, and `BUILD + VERIFY` does not measure the actual internal split. Use a short note for a small incidental activity or separate blocks when the work genuinely changes mode.
5. **Choose a daily subset.** Vocabulary size and simultaneous work are separate decisions. Your earlier review's cap discussion concerned project/purpose themes. With mode themes, visiting five modes within one project is not the same as juggling five projects. Do not copy a numerical cap without deciding what overload it is supposed to detect.
6. **Review after two weeks.** Ask whether you can choose quickly, whether verification remains visible, whether CHORE is swallowing too much digital upkeep, and whether dedicated research blocks repeatedly feel homeless. As a trial heuristic, add a category when the same distinct activity needs it on at least three separate days and you have a concrete review question for its total. This threshold is a usability suggestion, not a research finding.

No vault, theme journal, config, or historical ledger was changed for this report.

## External research: what supports the design

The activity set comes from your records. External sources provide useful design distinctions, not a validated seven-theme prescription.

- **Separate project identity from additional categorization.** Toggl's official documentation describes tags as context beyond clients/projects and permits reporting on that context. Applying that distinction to Bob is my inference: task homes can retain purpose while themes describe activity. [Toggl, “Tags”](https://support.toggl.com/en-us/article/tags-2b1rse/).
- **Planning is work in its own right.** David Allen distinguishes predefined work, work encountered as it appears, and defining work. That supports making PLAN visible. His framework does not imply that maintenance, repair, or every action found during review should be labeled planning. [David Allen, “The Threefold Nature of Work”](https://gettingthingsdone.com/wp-content/uploads/2014/10/Threefold.pdf).
- **Routine operation and lasting engineering are different.** Google's SRE account distinguishes repetitive service upkeep from changes with enduring value, and separately notes administrative overhead. This helps define CHORE versus BUILD/FIX. Personal chores are not all SRE “toil,” and Google's organizational time targets are not recommendations for your day. [Google SRE, “Eliminating Toil”](https://sre.google/sre-book/eliminating-toil/).

These sources were checked on 2026-10-27. None establishes that renaming themes itself improves productivity or that seven is better than six for everyone.

## Reproducibility and source notes

The primary evidence is the current local Bob vault as queried on 2026-10-27. Daily-note citations above use one-based line numbers; Tasks/Dataview JSON uses zero-based list/task lines, while Stats session facts use one-based lines. Archived task IDs provide more stable anchors than line numbers. The current note tree and current archived task descriptions can differ from what was present when the work happened.

Read-only collection commands:

```sh
bob stats show worked review_time sessions done \
  -r 2026-04-27..2026-10-26 -g day -f json

bob themes list -f json

bob query --format json --tasks-file - <<'TASKS'
status.type is DONE
done after 2026-04-26
done before 2026-10-27
TASKS

bob query --format json --query-file - <<'DQL'
TABLE WITHOUT ID file.path AS path, L.line AS line,
  L.parent AS parent, L.section AS section, L.status AS status,
  L.text AS text, L.t AS duration, L.outlinks AS outlinks
FROM "2026"
WHERE regexmatch("^[0-9]{8}$", file.name)
  AND file.name >= "20260427" AND file.name <= "20261026"
FLATTEN file.lists AS L
DQL
```

For the completion count, flatten `result.groups[].tasks`, keep `isRecurring == false`, and exclude `blockId == "gtd"`. This produced exactly 1,686, matching Stats. The narrow description screens use `descriptionWithoutTags`, anchored at the beginning, case-insensitively. Reading additionally accepts the reference tag/block ID. These are screening counts; they neither partition the work nor measure time.

For historical task links, a supplementary DQL extraction collected task block IDs and descriptions outside daily notes, templates, and conflicts. I resolved explicit path-and-block links and recognizable archived equivalents. Missing or ambiguous bare links were not treated as proof of a particular activity. Dataview warned about unrelated ambiguous bare link targets; the completed Tasks query and Stats returned no warnings. Statistics were not inferred from the failed exploratory query variants used while settling the extraction syntax.

The 96-session sample was selected from the original chronological Stats lists, month by month, before adding archived-link matches. Exact duplicates in the original ledger remained eligible; no sample activity percentages are claimed. Focused verification examples and the writing examples were checked separately, rather than relying on keyword hits in article titles.

Relevant Bob implementation context: `docs/pomodoro-themes.md` for component identity, catalog scope, hiding, and global rename; `docs/stats.md` for attribution limits; `src/native/pomodoro_homes/session.rs:85` for exemption-driven review attribution. The audited SASE decision records were `pomodoro-theme-is-one-component`, `theme-hide-is-recent-only`, and `theme-prefs-live-in-per-host-journal`.

For identifying this audit's extraction, the Stats JSON SHA-256 was `cb1644f2409780aaf7d031c78224b1950871ee330ba59b46314456dcf836d668`; the completed-task JSON SHA-256 was `d3da9d2339f523c1740089f91bf7740f5865a76c2199e32b88cb52b0294de10c`. Raw query dumps were temporary working material, not separately published artifacts; the commands are the reproduction route, and later vault changes can change the results.

## Recommended set

**Use PLAN, READ, BUILD, FIX, VERIFY, WRITE, and CHORE.** Rename the future roles of GTD and HOME to PLAN and CHORE; retain READ/BUILD/FIX; retire JOB from new activity labels; add VERIFY and WRITE. Keep RESEARCH as the first possible extension if dedicated investigation sessions prove frequent enough to deserve their own category.
