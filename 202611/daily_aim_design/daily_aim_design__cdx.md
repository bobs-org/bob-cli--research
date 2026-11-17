# Daily Focus: preserve the day's choice without creating another backlog

Independent research by **cdx** · 2026-11-17

## Decision in brief

**Add a small, human-owned `## Focus` section to daily notes. Normally choose one concrete result or protected activity; allow an intentional day off. Keep execution in the existing Pomodoro ledger. Update the existing morning-review instruction rather than adding another daily task.**

This is worthwhile if it preserves the answer to “What did I choose to make room for today, and why?” It is not worthwhile if it merely duplicates Today, introduces another checkbox lifecycle, or makes every day a miniature quarterly performance review.

The strongest local finding is that this is partly an existing practice: the live `gtd_daily.md` Morning review already says “highlight chosen (≤3 themes, highlight first).” However, current Bob no longer caps themes, and its computed **highlight** is the first open, non-exempt Pomodoro. That pointer changes as sessions close. What is missing is a durable statement of the original daily choice, its intended finish line, and any deliberate change of course.

## Scope and method

I independently inspected bob-cli documentation and selected Rust implementation at commit `3236ceefaa690c2c9aa8d935db0de7b1a2c11ce1`, audited the relevant SASE memories, queried the current `gtd_daily` checklist through read-only `bob query`, and consulted primary research and the original authors' methods. I did not consult the other swarm researchers' reports, conversations, or findings. No vault notes, product code, configuration, or memory were changed.

The live query inspected checklist text, not a longitudinal sample of Bryan's days. Consequently, this report makes no claim that Bryan currently overcommits, misses priorities, or needs a particular daily time budget. The suggested limits are design defaults to evaluate, not measurements of his behavior. Plugin and Mac application source were not inspected; cross-client work below is conditional scope, not a verified implementation estimate.

## 1. What Bob already does

| Existing mechanism | Verified behavior | Design consequence |
| --- | --- | --- |
| Period planning | Weekly Intentions, quarterly Outcomes, yearly Theme and Outcomes are Bryan-owned prose. Period notes have no task rows. | Daily planning can preserve the same authorship without inheriting a full period-review workflow. |
| Period review | Agents draft Review through `bob periods draft`; human Reflection stays human-owned. A week has no unreviewed-days requirement. | Do not make daily completion or reflection a prerequisite for weekly review. |
| Today | Resolved open tasks with dedicated links under today's open Pomodoros. | A link in a Focus section must not confer Today membership. |
| Ledger highlight | First open, non-exempt entry in ledger order. | This is a changing execution pointer, not a stable account of the morning's intention. |
| Budget | Default budget is 10 distinct on-clock links; off-clock links are uncapped. Types are listed but never capped. | A Focus policy must not revive the retired theme cap or pretend a task count measures available time. |
| Morning review | PRE → NEW → PROJECTS → PENDING → NEXT → RECURRING → TICKLER → ROTTEN → POST; POST is morning closeout. | POST is an appropriate place to finalize today's choice, not an evening review hook. |
| Task homes | Ordinary tasks live in areas/projects; daily exceptions include `^gtd` and Event Tasks. | A daily focus should be prose referencing canonical tasks, not another ordinary `#task` in the day file. |

Sources: [period anatomy and ownership](https://github.com/bobs-org/bob-cli/blob/3236ceefaa690c2c9aa8d935db0de7b1a2c11ce1/docs/periods.md#note-anatomy-and-ownership), [plan contract](https://github.com/bobs-org/bob-cli/blob/3236ceefaa690c2c9aa8d935db0de7b1a2c11ce1/docs/plan.md), [highlight implementation](https://github.com/bobs-org/bob-cli/blob/3236ceefaa690c2c9aa8d935db0de7b1a2c11ce1/src/native/plan_budget/mod.rs), [review guide](https://github.com/bobs-org/bob-cli/blob/3236ceefaa690c2c9aa8d935db0de7b1a2c11ce1/docs/guides/run-morning-review.md), and [task residence](https://github.com/bobs-org/bob-cli/blob/3236ceefaa690c2c9aa8d935db0de7b1a2c11ce1/docs/reference/glossary.md#area-note).

The live checklist query also found existing weekly and quarterly instructions to select at most three Intentions/Outcomes. **That does not imply three daily focus items.** Those horizons have different capacities and purposes. The checklist's separate “≤3 themes” phrase conflicts with the current plan contract, which explicitly ignores retired `max_themes` and `strict` keys. Correct that wording when implementing this feature; do not treat it as a current software constraint. This report does not change it.

## 2. What the research supports—and what it does not

### Specific action plans are more useful than another list of wishes

Gollwitzer and Sheeran distinguish wanting an outcome from specifying a situational cue and a response. Their author-written [implementation-intentions overview](https://cancercontrol.cancer.gov/brp/research/constructs/implementation-intentions) explains why if–then plans can help translate goals into action. This supports adding a brief start cue when starting is difficult, such as “After morning review, use the first work block to reproduce the failure.” It does not establish that every daily note needs mandatory fields, that three goals is optimal, or that writing prose guarantees completion. The underlying [2006 meta-analysis](https://doi.org/10.1016/S0065-2601(06)38002-1) was identified; the publisher full text was inaccessible in this session, so I do not base a numerical effect-size claim on it.

### Plan for interruptions, not just the ideal day

Parke et al.'s [daily-planning study](https://www.anderson.ucla.edu/documents/sites/faculty/review%20publications/research/DeVoe-et-al_timemgmt_2017.pdf) followed 187 employees over two workweeks, with 1,465 daily observations. Task/schedule planning's positive association with engagement and performance weakened with interruptions; contingent planning remained useful across interruption levels. This was an experience-sampling study with self-reported measures, not a randomized trial establishing causality. It supports a modest design inference: optionally record a fallback or a condition for changing the plan. It does not justify rigid enforcement or a predicted productivity gain for Bryan.

### Capacity needs historical reality, not just confidence

Buehler, Griffin, and Ross's [planning-fallacy experiments](https://web.mit.edu/curhan/www/docs/Articles/biases/67_J_Personality_and_Social_Psychology_366,_1994.pdf) found optimistic estimates for participants' own work. In one study, explicitly connecting relevant past experience to the forecast eliminated the optimistic bias. The practical inference is to size today's focus against comparable work and the day's actual obligations. Bob's ledger can inform that judgment, but apportioned task minutes are not precise effort estimates, and total Worked time is not the same as discretionary focus capacity. Neither this study nor the other sources establishes a universal “reserve 40%” rule.

### Specific plans can reduce mental interference; that is not proof of more output

Masicampo and Baumeister's [2011 paper abstract](https://pubmed.ncbi.nlm.nih.gov/21688924/) reports that making specific plans reduced several cognitive interference effects of unfinished goals in experiments. The [author's publication page](https://roybaumeister.com/2011/10/16/consider-it-done-plan-making-can-eliminate-the-cognitive-effects-of-unfulfilled-goals/) confirms the citation. I used the abstract-level findings; full text was not available through the publisher here. This supports a plausible benefit of recording a trusted choice, not a claim that unfinished tasks universally cause distress or that a daily commitment list is clinically beneficial.

### A single highlight is a useful method, not a scientific optimum

John Zeratsky's original [Make Time explanation](https://maketime.blog/article/choose-a-highlight-to-make-time-every-day/) proposes one daily highlight chosen for urgency, satisfaction, or joy. It explicitly allows other work to happen and offers 60–90 minutes as a rule of thumb. This is a good product precedent for selecting something meaningful without turning the entire day into a promise. The duration and single-item default are practitioner guidance, not validated thresholds for Bob. A 20-minute personal activity or a focused investigation can also be a valid daily choice.

### Preserve the distinction between priorities and actual obligations

The David Allen Company's [GTD setup guide](https://store.gettingthingsdone.com/wp-content/uploads/2023/12/GTD_Todoist_SAMPLE_LTR.pdf), especially the calendar section, distinguishes day/time-specific obligations from flexible next actions and warns against overcomplicating the system. A daily focus can complement GTD as a conscious preference. It should not create artificial due dates, replace real deadlines, or require copying every next action into another list.

**Evidence assessment:** there is reasonable support for specific planning, contingency thinking, and realistic sizing. There is no source here validating this exact Obsidian feature, an optimal commitment count, punitive misses, automatic rollover, or a success percentage. Naming, one-item defaults, and storage design remain engineering and workflow judgments.

## 3. Is another daily planning layer a good idea?

The idea has two concrete benefits. First, the existing ledger records selected work and time but cannot necessarily explain what would have made the day worthwhile. Second, a preserved choice lets weekly review compare intentions with evidence without inventing the day's priorities after the fact.

The costs are equally concrete:

- **Duplicate planning.** If the new section merely enumerates Today tasks, it adds editing and reconciliation without answering a new question.
- **Promise inflation.** Calling preferences “commitments” can turn sensible reprioritization into a daily sense of failure and obscure actual promises to others.
- **Hierarchy theater.** Requiring every daily action to link to a weekly intention, quarterly outcome, and yearly theme creates administrative work and excludes maintenance, emergencies, relationships, and rest.
- **Short-horizon bias.** A completion score favors small finishable work over exploration, learning, and uncertain research. A worthwhile day can yield a narrower question rather than a shipped feature.
- **Ritual growth.** Bryan already has a substantial review checklist. Another recurring task and dashboard could become more work to maintain than the choice itself.
- **False history.** Current task status and the last open session cannot reliably reconstruct what was chosen or accomplished on an earlier day.

I would proceed only with a feature that stays useful as a few lines of Markdown. If its usefulness depends on enforcing quotas, generating daily agent reports, or synchronizing multiple task states, the scope is too large.

## 4. Naming and alternatives

| Name/design | Strength | Main problem | Judgment |
| --- | --- | --- | --- |
| Daily commitments | Signals seriousness | Overlaps review “commitments,” sticky Next, and real obligations; implies a stronger promise than intended | Do not use as the primary label |
| Daily intentions | Familiar parallel with weekly notes | Blurs the weekly/daily distinction and can remain vague | Acceptable, but less clear |
| Daily outcomes | Encourages specificity | Conflicts with quarterly Outcomes; can imply an achieved result before the day happens | Avoid |
| Daily wins / Big Three / MITs | Easy to remember | Encourages scoring or checklist quotas; “three” is arbitrary | Avoid as the data model |
| Daily Highlight | Familiar from the current ritual | Already names a moving ledger entry; also easily confused with annotation highlights | Keep as conversational language only |
| **Daily Focus (`## Focus`)** | Describes a human priority without a new status; accommodates meaningful activities | Needs a concrete sentence to avoid vagueness | **Recommended** |
| No new section; use only the ledger | Zero new ceremony | Loses the durable rationale and intended finish line | Best fallback if the section is not useful |

The conceptual progression is **yearly direction → quarterly changes sought → weekly intentions → today's chosen contribution → ledger execution**. This is a way to think, not a required foreign-key chain. A daily focus can advance one weekly intention, several, or an explicit exception. Do not enforce one item per life area or per weekly intention each day.

## 5. Proposed policy

### Selection and scope

Use **zero or one primary focus per day** as the default. One is a scope constraint for the practice, not a parser rejection or a scientific claim. Avoid a built-in list of two “optional” items that will quietly become three daily obligations. If a day genuinely needs several aims, name one primary focus and leave the other work in the ledger. A freeform note may explain the exception; no modal approval or justification field is needed.

A focus states a concrete result, learning target, or activity under Bryan's control. “Have the feature approved” depends on somebody else; “send the reviewable implementation and open questions” is controllable. “Work on Bob” is too vague; “reproduce the sync failure and record the smallest failing case” is useful. “Read for 30 minutes without checking messages” is a legitimate activity focus even without a completed reading task.

Choosing none is valid for rest, illness, travel, or a day already consumed by obligations. An optional “No focus planned—travel” distinguishes this from missing data. Missing or empty text means **not recorded**, never failed. A focus may be off-clock; on-clock plan-budget exemptions must not be mistaken for unlimited personal capacity.

### Capacity

Before choosing, inspect the day's meetings and buffers, hard deadlines, review/admin load, and energy. Select a scope that fits a realistic available block with breathing room. If it cannot fit, reduce the slice or choose no additional discretionary focus. No universal minute target or utilization percentage is proposed.

When a focus spans several sessions, keep one intended result and execute through those sessions. When several tasks support it, link their canonical rows in the ledger; do not manufacture a parent focus task just to count it. When exploration is uncertain, prefer a bounded investigation and an evidence artifact to a promised answer.

### Plan changes and history

The Focus section is a record of the selected aim, not a live projection of whichever session is currently first. Closing or reordering Pomodoros must not rewrite it. Linking a task there must not start it, promote its lane, stamp freshness, alter priority, or create a dependency.

Allow deliberate replacement during the day. After meaningful work has begun, preserve the original sentence and add a short `Changed:` line stating the new aim and reason; do not silently rewrite history. Cosmetic wording corrections do not need an event log. Do not repeatedly add completed aims to the list to inflate a score.

At day's end, optionally append one `Result:` sentence: achieved, partial, replaced, or not attempted, with the concrete evidence or recorded reason. These are human words, not a new task status enum. If nothing was recorded, weekly review leaves it unknown. No daily success badges, streaks, or automatic grades.

### Carryover

No automatic carryover. An unfinished canonical task remains in its current task system, where normal review and lane policies already apply. The next day starts with a fresh choice; Bryan may intentionally choose the same work again. Repeated selection is a prompt to reconsider scope, dependencies, or priority during ordinary review, not a new decay mechanism or a forced cancellation rule.

## 6. Minimal daily-note shape

Place the section near the top of the daily note, outside `## Pomodoros`, after existing navigation/stats and before the execution sections where the actual template allows. A simple example, with illustrative link targets:

```markdown
## Focus

Produce a minimal reproduction for the sync failure.
Supports [[2026/2026-W47#Intentions|this week's reliability intention]].
Start after morning review with [[bob#^sync-repro|the existing task]].
If a production incident takes the morning, stop after the failing case is recorded.

Result: Reproduced the failure; isolation remains. Evidence is in the task's work log.
```

Only the first sentence is essential. The weekly link, start cue, fallback, and result are optional; most days should take fewer lines. Do not seed empty mandatory labels that suggest a form must be completed. A shorter example is sufficient:

```markdown
## Focus

Read for 30 minutes after lunch, away from messages.
```

Use ordinary prose and inline links: no `#task`, checkbox copies, task-level `focus`/`today` fields, new tags, or dependency syntax. Existing task ownership and execution remain intact. The daily note's date scopes the choice; no separate `focus_date` is needed. A real deadline remains on the canonical task/calendar regardless of whether it is selected as Focus.

## 7. Fit into the existing review instead of adding another chore

**Revise the existing Morning review item's highlight clause.** Suggested replacement, preserving the rest of its instructions:

> Today's Focus chosen, or deliberately none: check the calendar and this week's Intentions; write one concrete aim in today's Focus section; arrange the next executable work in the ledger.

Remove its obsolete “≤3 themes” language. Do not require the stable Focus sentence to match the first open session throughout the day. Morning setup may put the relevant work first, but urgent events and completed sessions naturally change that pointer.

Place this decision at morning closeout, after enough review to understand obligations. Do not wait for ROTTEN to reach zero: optional upkeep must not consume the whole day before it can be planned. On weekly-review days, read or revise this week's Intentions first where practical; this does not require a new review tier.

Do **not** add an evening `#post` task: POST already means the end of the morning walk. Initially, record the optional result when closing the last work session, or glance at the previous day's Focus before selecting the next one. If that proves too much ceremony, review the week's Focus sentences during weekly review instead. A missing result must never block completing Morning review.

This change also avoids conflating “review closed” with “focus achieved.” The existing review closeout metric should continue measuring the review ritual, not daily goal attainment.

## 8. Implementation direction and boundaries

### First useful version: convention and template

Implement the empty `## Focus` heading in the actual daily-note template/creation path and update the existing checklist clause. Verify how `_templates/daily.md` is instantiated before editing; period scaffolding itself does not currently create daily notes. Apply to new days and optionally today's note, preserving all authored content. Do not mass-backfill historical notes or reconstruct choices from time logs.

Bryan owns the section's contents, just as he owns weekly Intentions. Agents may suggest wording when asked but should not select, populate, or retrospectively score Focus. Creating an empty scaffold is distinct from authoring the person's intention.

No new CLI, parser, database, task state, plugin panel, notification, or mobile contract is required for this version. It can be used immediately; an evaluation period below is not a calendar gate that withholds functionality.

### First valuable automation, only if wanted: weekly context

The best later integration is letting the weekly agent brief include each day's recorded Focus and optional result as attributed human context. Today, [`periods/report.rs::build_child`](https://github.com/bobs-org/bob-cli/blob/3236ceefaa690c2c9aa8d935db0de7b1a2c11ce1/src/native/periods/report.rs) gives daily children `review: null`, and [the brief contract](https://github.com/bobs-org/bob-cli/blob/3236ceefaa690c2c9aa8d935db0de7b1a2c11ce1/docs/periods.md#agent-briefs-brief-v2) intentionally omits daily review-state/Headline fields. Keep that distinction.

If this integration is built:

- Read the exact Focus section as human-authored data, with day identity and source link. Keep it separate from agent instructions and numerical facts.
- Add an explicitly named bounded context field rather than overloading daily Headline, Review, closeout, or Done. Decide and document schema compatibility before changing a versioned output.
- Preserve missing, empty, and explicit “none” distinctions when available. Mark truncation instead of silently dropping caveats; preserve some context for each recorded day.
- Do not infer success from current task status, minutes, or the current highlight. A task completed Tuesday does not prove Monday's focus was achieved Monday. A bounded research focus may be met while its canonical project task remains open.
- Carry the daily-note evidence into weekly interpretation; do not roll up a “focus success rate.” Separate planned focus, the human result statement, and independent execution evidence.
- Keep unrecorded days compatible with weekly and quarterly reviews. No daily review digests or force/redo lifecycle are needed.

### Surfaces and tests, if automation is implemented

A dedicated UI is not the first priority. If a persistent display later proves helpful, label it **Daily focus** and show it separately from the live Now/Next/Later agenda. Bob owns any new data endpoint; Bob Mac Capture remains a thin client and does not parse vault Markdown. Preserve existing agenda positioning and folding rather than squeezing a new form into the capture flow.

Meaningful acceptance cases for future automation are:

| Case | Required behavior |
| --- | --- |
| Inline task link in Focus | Does not alter Today, task lanes, link counts, or freshness |
| First Pomodoro closes or ledger order changes | Focus text remains unchanged |
| Rest day / absent section / explicit none | Distinguishable where possible; no failure or overdue state |
| Focus changes during the day | Original aim and change note remain visible as authored |
| Canonical task moves or archives | Standard link-rewrite behavior is respected; no new copy of the task |
| Task completes on a later day | No retrospective automatic success for the earlier focus |
| Missing result or missing daily note | Weekly review still works and states uncertainty |
| Year boundary or timezone boundary | Use Bob's established daily date/path semantics and ISO-week parent, not the research host's UTC date |
| Hand-edited section / concurrent vault update | Preserve human text; use existing guarded write rules for any eventual writer |
| Duplicate headings or fenced example headings | Diagnose ambiguity; do not invent a merged authoritative choice |

This report proposes those boundaries; it does not implement or test the feature. Detailed CLI/help changes would require the project's normal contract and documentation review when that work is actually scoped.

## 9. Evaluate the practice without creating another tracking project

Use it for roughly ten working days, including an interrupted day if one naturally occurs. At the next weekly review, ask:

1. Did recording the focus change a real choice about what to do or decline?
2. Could I set it in roughly a minute or two, and was the result sentence easy to omit when unnecessary?
3. Did it add context that the ledger and weekly Intentions did not already provide?
4. When the plan changed, did the record explain the change without guilt or clerical cleanup?

These are practical acceptance questions, not experimental proof or mandatory telemetry. Do not make an 80% completion threshold the objective. Keep the feature if it improves decisions or review at low cost. Simplify it to one sentence if optional fields become chores. Remove the section and retain the existing ledger-highlight practice if it adds no information. Build weekly-brief integration only after there is useful content to consume.

## 10. Explicit adjustments to the requested concept

1. **Rename “daily commitments” to “Daily Focus.”** This avoids existing terminology and distinguishes a chosen aim from an external promise.
2. **Use one primary aim as the default, not a three-item daily quota.** The weekly/quarterly cap does not supply a daily capacity estimate; zero is valid.
3. **Update an existing daily checklist item instead of adding one.** The current Morning review already includes highlight selection.
4. **Retire stale checklist wording, not reintroduce a theme limit.** Code and current contract have no type/theme cap.
5. **Keep stable daily intent distinct from the advancing ledger highlight.** Execution order can change without rewriting the day's original choice.
6. **Use prose with optional task references, not new daily tasks or statuses.** This respects canonical task homes and ledger-derived Today.
7. **Add optional evidence and deliberate reselection, with no rollover or grading.** This supports weekly learning without manufacturing a second backlog.
8. **Start with a usable note convention; add read-only weekly context before specialized UI.** Do not reproduce the complete week/quarter review machinery at daily scale.

## Sources and audit notes

Repository citations above are pinned to the inspected bob-cli commit. Local reference reads covered artifact/vault conventions, Period Note/Pomodoro/Task Link vocabulary, ledger-derived Today, sticky lanes, current review tiers, and the idle-capture agenda contract. The live checklist was queried on 2026-11-17 using:

```sh
bob query --format markdown --query 'TABLE WITHOUT ID t.text AS "Checklist item", t.status AS "State" FROM "gtd_daily" FLATTEN file.tasks AS t WHERE !t.completed'
```

The query returned rows successfully, with unrelated ambiguous-link warnings; it does not establish the recurrence schedule or due state of every returned row. Only the relevant Morning/weekly/quarterly wording informed the recommendations.

External evidence used: Parke et al. (2018), DOI `10.1037/apl0000278`; Gollwitzer and Sheeran's author-written NCI overview and identified 2006 meta-analysis, DOI `10.1016/S0065-2601(06)38002-1`; Buehler et al. (1994), DOI `10.1037/0022-3514.67.3.366`; Masicampo and Baumeister (2011), DOI `10.1037/a0024192` (abstract-level use); John Zeratsky's Make Time article; and the David Allen Company guide. The first three research lines inform mechanisms and constraints; the latter two methods are workflow precedents, not controlled evidence for this implementation.

A batched `bob ref find` checked the six main article/DOI/guide candidates. All returned `not_found` in indexed `ref/`; intake was not checked. This does not mean Bryan has never read them, and a different capture URL or unindexed record may exist. No readings were added to the vault. Library check: 0 of 6 candidates already in your library (0 finished).

## Recommended solution

**Ship a human-owned `## Focus` section with one concrete daily aim, allow deliberate none, and revise the existing Morning review clause to prompt that choice.** Keep start cues, weekly links, fallback plans, and result notes optional. Preserve canonical tasks and the Pomodoro ledger as the execution system; keep the current moving highlight separate. Remove the stale theme-limit wording, add no new task status or automatic carryover, and do not grade days.

Use the section immediately as plain Markdown. If it proves useful, expose its recorded text to weekly review with clear provenance and uncertainty. If it duplicates the ledger, keep the simpler existing practice. The purpose is a better daily choice and a more truthful weekly memory, not another obligation to manage.
