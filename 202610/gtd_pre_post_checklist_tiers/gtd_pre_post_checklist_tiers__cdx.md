# PRE and POST in the GTD morning review: ordering, completion, and bounded upkeep

Researcher: **cdx**  
Date: **2026-10-04**  
Scope: independent implementation research and critique; no application code or vault tasks changed.

## Assessment

**This is a useful improvement if PRE and POST are treated as executable routine steps surrounding the existing review, with POST as a deliberate completion marker.** It puts preparation, intake, commitment review, and sign-off behind one familiar navigation sequence. The two important corrections are that recurring tasks need completion rather than freshness confirmation, and POST must remain reachable when ROTTEN upkeep is intentionally unfinished.

The recommended canonical order is:

```text
PRE → NEW → PROJECTS → PENDING → NEXT → RETURNED → REFERENCES → ROTTEN → POST
```

Keep ROTTEN optional within the morning time budget. Complete “Morning review” explicitly after required preparation and commitment reviews, choosing the day's highlight and resolving CROWDED, and either completing or intentionally stopping upkeep. That completion means the morning process was carried out, not that every old task disappeared.

I independently inspected bob-cli, the linked bob-plugins source, project decision memory, read-only vault queries, and official GTD/Tasks documentation. I did not read another researcher’s report, transcript, or findings.

## What exists today

### The walk already has seven groups

The current source contract is **NEW → PROJECTS → PENDING → NEXT → RETURNED → REFERENCES → ROTTEN**, not the shorter order still embedded in the daily “Morning review” description. The first six tiers are commitments; ROTTEN is upkeep. Both Rust and JavaScript evaluate this order. The navigation plugin consumes the shared queue, rather than independently collecting tasks. State/bucket classification and review tiers are deliberately separate dimensions. [S1–S4]

Freshness review currently excludes all recurring tasks, canonical daily-note tasks, and tasks linked under today's open Pomodoros. Recurring tasks also refuse `[fresh::]` stamping: the next recurrence would copy that stamp. Therefore adding tags and sorting existing queue entries will **not** admit these daily tasks. The implementation needs a narrow routine admission branch that precedes the ordinary freshness exclusions. [S1–S3]

“Ready” should mean the existing visible TODO lane: not closed, not dependency-blocked, not hidden, not in templates/conflicts, and not scheduled after the local day. It should not mean only tasks currently classified FRESH, and it should not mean every unfinished status. Next and Pending are separate lanes. The existing Ready predicate does not impose an additional due-date or start-date gate; this change should not introduce one. [S5]

The name `gtd_daily.md` does not make it a canonical daily note. Those have the `YYYY/YYYYMMDD.md` path shape. The present reason its tasks are absent is their recurrence. [S1, S3]

### The actual daily checklist

Read-only Dataview and Tasks queries of `gtd_daily.md` found **eight active daily TODO tasks**, each recurring `every day when done`. None currently has `#gtd`, `#pre`, or `#post`. The seven PRE candidates, in source order, are:

| Active task | Proposed task-line tags |
| --- | --- |
| Check weather | `#gtd #pre` |
| Brush teeth | `#gtd #pre` |
| Take fish oil pills + Take L-tyrosine pills | `#gtd #pre` |
| Review Calendar for today and tomorrow + Create @EVENT notes | `#gtd #pre` |
| Read Email | `#gtd #pre` |
| Import inbox tasks from Google Keep | `#gtd #pre` |
| Do morning stretches! | `#gtd #pre` |
| Morning review | `#gtd #post` |

The file also contains a **cancelled** daily “Pick today” task referencing the retired NOW workflow, a cancelled weekly review, and an ON_HOLD weekly prune. Do not retag or reactivate those as part of this migration. The weekly tasks do not meet the daily recurrence requirement. The cancelled daily row is an explicit exception to the literal “all tasks that recur daily” wording. [S6]

The active “Morning review” description is currently a long script containing `bob gkeep pull`, the older tier list, lane gestures, starting the highlight, CROWDED cleanup, and optional ROTTEN upkeep. Making this entire script the final navigated task would ask the user to mentally replay a walk they have just completed. It should become a short sign-off with a link to the fuller procedure. PROJECTS and REFERENCES should appear in that procedure. [S1, S6]

### Live queue and verification

On 2026-10-04, the installed `bob freshness --format json` reported:

| Walk tier | Count |
| --- | ---: |
| NEW | 4 |
| PROJECTS | 0 |
| PENDING | 0 |
| NEXT | 36 |
| RETURNED | 1 |
| REFERENCES | 10 |
| ROTTEN | 77 |
| Total walk | 128 |

It reported **no configured upkeep budget**, seven upkeep stamps today, and no `gtd_daily.md` queue rows. The 77 ROTTEN entries make “just navigate through everything before POST” a poor default. The counts are a point-in-time observation, not an argument to automatically change intervals, release tasks, or enable a particular budget. [S7]

The deployed command emitted JSON schema **7**, while this workspace's source declares schema **8**. Source design and deployed behavior therefore need separate validation; testing the system-installed executable alone would not verify a new implementation. The inspected ledger freshness namespace is version 6, with explicit tracker capabilities. [S2, S3, S7]

I ran the four existing plugin suites for ledger freshness, its footer, review navigation, and task-status cycling: **313 tests passed, zero failed**. They establish a healthy baseline and cover recurrence refusal, navigation anchors, tier counts, and completion-related insertion safeguards. They do not validate PRE/POST or an end-to-end live Obsidian session. [S8]

## Critique of the proposal

### Why it is a good fit

Preparation before review is useful: calendar checks and importing inbox tasks can affect what the commitment walk needs to consider. Sign-off afterward gives one truthful place to record the completed ritual. Keeping the tasks in their existing note and using explicit user-owned tags makes the setup inspectable and easy to change.

Official GTD material treats capture, clarification, organization, reflection, and engagement as related but distinct activities. Its weekly checklist begins with clearing inputs before updating commitments, and its setup guidance distinguishes frequent daily list review from broader weekly review. That supports the shape of this routine; it does not prescribe PRE/POST labels or require a full weekly review every morning. This is a local workflow recommendation, not a claim of GTD certification. [S9, S10]

A separate checklist could also work, but it would leave the user alternating between that checklist and `]s`. Because the stated goal is one morning walk with independently completable steps, adding two structural tiers to the existing shared queue is preferable.

### Risks worth addressing

**Personal routines can delay commitment review.** Brushing teeth, supplements, and stretches are legitimate checklist steps, but they are different activities from checking the calendar and triaging commitments. I would initially include the seven requested active steps, then measure whether they delay the review. If so, the product already has an escape hatch: remove `#pre` from the distracting step while leaving the recurring task in place. There is no need to create another task framework.

**“Read Email” can absorb the whole morning.** Give it a behavioral boundary: identify actionable or urgent items and capture next actions, then stop. A long reply or unrelated task should become work after review. Similarly, the advertised approximately ten minutes should describe the central review, not imply that all personal routines, email, and 128 queue entries fit in ten minutes. This recommendation follows from the observed workload; it is not a measured duration estimate.

**An endlessly replenishing PRE group can prevent progress.** All current daily tasks use `when done` and have scheduled dates. Preserve that combination. Completing today's instance should generate a future-scheduled instance excluded until tomorrow. Do not remove the scheduled dates or convert recurrence to an interval anchored on an old overdue date during this change. A malformed or dateless recurring task that immediately regenerates as eligible must be diagnosed, not worked around by silently stamping it. [S6, S11]

**POST is an assertion, not proof.** Jumping past a task is not completing it, and completing “Morning review” does not establish that every previous item was done. The system should show remaining PRE and commitment counts when landing on POST, but should not auto-complete prior tasks or impose a hard completion interlock. The explicit checkbox records the user's judgment. Excluding intentional leftover ROTTEN is sound; silently excusing unprocessed intake or commitments is not.

**The present wording mixes reviewing with beginning deep work.** Choose the highlight during review; begin sustained work after the POST sign-off. That makes a clearer endpoint and avoids interrupting the first work session to return to CROWDED/upkeep.

**Source ordering is not a dependency graph.** Path/line sorting preserves the checklist's authored sequence in `gtd_daily.md`. Across different notes it provides deterministic order, not semantic prerequisites. Do not add task dependencies among these recurring tasks just to make PRE run first: the review tier already supplies that ordering, and completion/recurrence identities are a different problem.

## Adjusted requirements

These are explicit clarifications or changes I recommend before implementation:

| ID | Adjustment | Why |
| --- | --- | --- |
| A1 | Retag only the **eight active daily tasks**: seven PRE, one POST. Leave cancelled and weekly tasks alone. | Avoid modifying retired routines or broadening the request. |
| A2 | Ready means the existing visible TODO lane. PRE/POST admission does not require a freshness stamp or freshness due date. | Recurring tasks have no valid freshness-review lifecycle. |
| A3 | Wrap **all seven existing tiers**, retaining their internal order and comparators. | PROJECTS and REFERENCES already exist in the current source. |
| A4 | POST is structurally after ROTTEN, but explicitly reachable without exhausting ROTTEN or requiring `budget_met`. | The user allows unfinished upkeep; today's budget is unset. |
| A5 | Rewrite “Morning review” as a short completion checklist/sign-off, with details linked elsewhere. Choose the highlight before sign-off and start work after it. | Prevent a recursive instruction at the end of the walk. |
| A6 | Exact task tags `#gtd` plus exactly one of `#pre`/`#post` select a group. Both phase tags are an invalid configuration with a visible diagnostic. | A task cannot satisfy both “first” and “last” without duplication. |
| A7 | PRE/POST tasks are completed through the existing Tasks-aware completion path, then navigation advances. Alt+F retains its freshness-confirmation meaning. | Closing a recurrence and reviewing a backlog item are different actions. |
| A8 | Preserve relative `]s` navigation; `[S` explicitly starts at the first entry. Reset stale session anchors across local-day rollover. | Structural order does not imply restarting PRE on every navigation keypress. |

A2 also means explicitly tagged Ready tasks can participate outside `gtd_daily.md`, whether recurring or one-off. Restricting membership to that filename or requiring daily recurrence would contradict the requested tag-based groups. Daily recurrence selects the initial migration targets, not the group's universal eligibility rule.

## Proposed implementation contract

### Admission and ordering

Define a small, pure routine predicate over the same parsed Tasks rows used by the existing evaluator:

```text
routine_ready(t) = lane(t) = Ready AND existing lane-visible(t)
phase(t)         = PRE  if task tags contain #gtd and #pre but not #post
                 | POST if task tags contain #gtd and #post but not #pre
                 | none otherwise
routine_tier(t)  = phase(t) if routine_ready(t), else none
```

Use parsed **task-line tags**, compared as whole tokens with a documented consistent case policy; I recommend case-insensitive whole-token comparison. Do not select `#preview`, `#pre/other`, file-level tags, text inside a linked target, or arbitrary substring matches. Tasks' built-in `tags include` is a partial match, so it is not sufficient by itself for this contract. [S5, S12]

When a routine tier exists, it wins the walk tier before tracker/NEW/lane/returned/rotten tier assignment. Otherwise retain the existing evaluator. Admit tagged Ready routines despite the ordinary recurrence, canonical-daily-note, or Today-membership exclusions; these exclusions concern freshness review, whereas the tags deliberately request a morning action. Keep future-scheduled, hidden, blocked, closed, template, and conflict exclusions. In particular, Today-linked Ready routines remain in PRE/POST; if normal hooks promote a task to Next, it no longer satisfies Ready and is handled by that lane. Do not automatically demote it.

Recurring routine rows retain **null freshness state and bucket**, and never acquire `[fresh::]`, `[refresh::]`, keep streaks, or decay decisions just for being walked. For tagged one-off tasks, preserve whatever ordinary state/bucket evaluation would produce; only their walk tier changes. This avoids silently changing dashboard freshness semantics when adding a tag. Each task appears once in the walk. The explicit routine action remains completion, even if a one-off task also has normal freshness metadata.

PRE and POST sort by **path ascending, line ascending**. Thus the initial PRE group follows the authored order of the source note. Keep the existing per-tier comparators for the middle seven groups. There is no configuration block, new priority, status, or generic ordering system to introduce.

The exception must be explicit in the result path: simply assigning `tier = pre` and then entering the existing `state == null` early return would discard every recurring routine's new tier. Both current evaluators have that early-return pattern. [S2, S3]

### Actions and recurrence safety

For PRE/POST notices and footer context, show a short hint such as **“Complete with Ctrl+Enter, then ]s”**. Route completion through the current task-status-cycler/Obsidian Tasks behavior; do not implement recurrence generation inside freshness code or directly change `[ ]` to `[x]` without the existing completion adapter. The cycler delegates recognized tasks to Tasks commands and accounts for insertion/deletion. Public Tasks documentation likewise ties recurrence generation to transition into a DONE status. [S4, S11]

Keep Alt+F and Alt+Shift+F as review gestures. A recurring routine should still refuse stamping. Give a routine-specific explanation pointing to completion; do not make the same key silently complete a routine and merely confirm the next backlog task. A future “complete and advance” command could reuse the existing completion path, but it is not necessary for the first version.

The important integration test is not just that the next tier is correct: **complete the first PRE task, allow Tasks to insert tomorrow's occurrence, then press ]s immediately and again after the task cache updates**. Verify that neither the inserted future occurrence nor a different shifted source line becomes the selected task. Repeat with successive completions, duplicate descriptions, completion deletion, and note edits.

Navigation currently anchors queue entries with keys that fall back to path plus line and resolves landings against original Markdown. Those are valuable safeguards, but recurrence can change both line positions and cache timing. Prefer the narrowest fix established by integration tests: reconcile surviving targets using original-line identity/current source and existing anchors, or notify and re-read when identity is ambiguous. Do not add persistent block IDs or a new recurrence identity database merely to implement these tiers. I have identified a risk to test, not demonstrated a current recurrence-navigation bug. [S4]

### Finishing without clearing ROTTEN

Retain the canonical queue, including all due ROTTEN entries. Do not remove or silently mark them reviewed when a budget is reached.

For the requested initial setup there is one POST task, so the existing **`]S` jump-to-last** provides a direct finish route. After required PRE/commitment work and CROWDED cleanup, do as much ROTTEN upkeep as time allows; press `]S`, assess the sign-off checklist, and complete “Morning review.” This needs no additional hotkey and works even when the numeric budget is absent or not met. `[S` starts at PRE; lowercase `]s`/`[s` keep their normal relative and counted navigation. [S1, S4]

If multiple POST tasks become common, add a small **“Jump to POST”** navigation command targeting the first POST entry. Jump-to-last would otherwise bypass earlier POST steps. This is an optional extension, not a prerequisite for the one-marker migration. Multiple POST tasks can still be walked normally in the canonical order.

Separate the summary into **preparation**, **commitment review**, **upkeep**, and **sign-off** counts. PRE remains required preparation. POST must not be added to the existing “commitments remaining” calculation used before ROTTEN: that would make “Commitments done” impossible until a task after ROTTEN was completed. Instead show **“Commitment reviews done · 77 ROTTEN optional · POST remaining”** at that boundary. On POST, show remaining required preparation/commitment counts rather than proclaiming completion solely because the cursor reached the end.

Completing a routine must not satisfy the freshness upkeep meter. Preserve current freshness-state totals, NEW/ROTTEN dashboard bucket semantics, and the existing stamp-based budget. Extend `by_tier`, `walk`, ranks, group labels, and CLI human output for PRE/POST; `walk` still equals the sum of the full tier histogram even with `--limit`. With all initial tasks eligible, eight additional queue entries are expected, without eight extra freshness-due states.

### Implementation surfaces and deployment

| Surface | Required work |
| --- | --- |
| bob-cli `src/native/freshness/state.rs` | PRE/POST tiers, routine admission, explicit null-state results, sorting and histogram. |
| bob-cli `src/native/freshness/scan.rs` | Pass parsed `RichTask.tags` or a derived phase into `FreshnessRow`; do not reparse the vault using ad hoc regexes. |
| bob-cli `src/native/freshness/cli.rs` | Tier serialization, summaries, human sections and boundary wording; bump the source's versioned JSON schema for the expanded tier contract. |
| bob-plugins ledger `plugins/bob-ledger-tools/main.js` | Mirror evaluation, collect tags in `freshnessRowFromTask`, counts, ranks, shared entry presentation, footer groups, and cache invalidation inputs. |
| bob-plugins navigation `plugins/bob-navigation-hotkeys/main.js` | Recognize tiers, completion hints, boundary logic, anchor/rollover behavior, and PRE/POST-compatible first/last/counted jumps. |
| Existing cycler | Reuse completion behavior; change it only if a tested integration gap requires a small adapter. |
| Vault `gtd_daily.md` | Idempotent migration of seven PRE and one POST tag pairs; preserve recurrence, schedule, creation fields and other task metadata. |
| Documentation | Update `docs/freshness.md`, relevant getting-started/plan references, and the morning procedure. Do not rerun freshness seed. |

Use an explicit freshness capability such as `routineReview: true` so a consumer can distinguish support; decide the precise namespace/schema increment against the actual source version at implementation time. Add mixed-version tests so older/missing providers do not produce false zero routine counts or misleading action hints. Deploy compatible plugin changes together, reload them, then migrate task tags. The linked repo is the plugin source of truth; deploy with `bob plugins sync`. Respect source fragments/build checks if changes touch a plugin with `src/fragments.json`; do not edit its generated entrypoint. [S2–S4, S13]

The implementation changes the accepted rule that recurring tasks occupy no review tier. That exception should be documented explicitly. If the decision record is updated after approval, follow the memory-write workflow and write a successor/partial supersession rather than editing an accepted immutable record in place. This research does not change memory.

## Acceptance checks and trial

| Case | Expected result |
| --- | --- |
| Seven active daily PRE tasks plus Morning review | PRE follows source order; all current tiers follow; POST is last. |
| Cancelled daily row and weekly rows | No migration changes and no accidental reactivation. |
| Recurring Ready routine scheduled today or earlier | Included; no freshness stamp required. |
| Tomorrow's generated occurrence | Excluded today; eligible at local-day rollover. |
| Closed, blocked, hidden, future-scheduled, template/conflict routine | Excluded using the existing visibility rules. |
| Nonrecurring tagged Ready task in another note | Included without requiring that filename or daily recurrence; ordinary state/bucket preserved. |
| Tagged task in Next/Pending | No PRE/POST override; ordinary lane rules continue. |
| Missing #gtd, prefix/subtag lookalikes, or inherited note tags | No routine membership. |
| Both #pre and #post | Visible configuration diagnostic; no duplicate routine entries. |
| Ready routine in canonical daily note or linked Today | Explicit routine exception applies; ordinary freshness exclusions are unchanged elsewhere. |
| Freshness confirmation on recurring routine | Refused with completion guidance; neither done nor fresh changes. |
| Complete PRE and navigate during cache lag/line insertion | Lands on the correct surviving successor; future instance never becomes a morning item. |
| Partial ROTTEN review with no budget configured | Explicit ]S reaches the sole POST task without writing any skipped ROTTEN row. |
| ROTTEN entry requiring a decay decision | Existing card/skip behavior preserved; POST remains reachable. |
| POST with PRE or commitment reviews still due | Shows truthful remaining counts; no automatic completion or hard block. |
| Empty middle tiers, only PRE/POST, no POST, multiple POST | Deterministic navigation, truthful footer and empty messages; no invented sign-off task. |
| Counted/reverse/first/last navigation and day rollover | Existing key meanings preserved with the expanded order; stale previous-day anchor does not skip new preparation. |
| CLI and plugin parity, --limit, old provider | Matching tier vectors/full counts, limited rows only, explicit compatibility behavior. |

Add these vectors to the existing Rust state/CLI tests and JavaScript evaluator/navigation/footer tests. Run existing plugin build checks and relevant suites, then exercise actual Obsidian recurrence completion and cache refresh; mocks alone cannot establish that integration.

Run a short personal trial after deployment. Track time to commitment review, missed preparation, mistaken double completion, whether sign-off is reached despite remaining ROTTEN, and whether PRE creates an inbox/personal-routine bottleneck. Keep the feature if the routine becomes easier to start and finish without false completion. If PRE delays useful review, narrow its membership; if NEXT reviews remain repetitive, tune the existing interval/cap policy separately rather than changing this feature's semantics.

## Evidence and sources

Repository links identify the exact revisions inspected locally; they were not fetched as a substitute for opening the repositories through SASE.

- **S1 — bob-cli contract:** [docs/freshness.md at 660c171](https://github.com/bobs-org/bob-cli/blob/660c171c6b281053d86907b3e908fce032f8f141/docs/freshness.md), especially sections 3, 4, 6 and 7. Audited reads also covered `decisions:review-walk-is-tiered`, `ready-is-freshness-gated`, `task-lanes-are-sticky`, `note-ready-cap-counts-the-lane`, and `rotten-keeps-use-priority-decay`.
- **S2 — native evaluator and API:** [state.rs](https://github.com/bobs-org/bob-cli/blob/660c171c6b281053d86907b3e908fce032f8f141/src/native/freshness/state.rs), [scan.rs](https://github.com/bobs-org/bob-cli/blob/660c171c6b281053d86907b3e908fce032f8f141/src/native/freshness/scan.rs), [cli.rs](https://github.com/bobs-org/bob-cli/blob/660c171c6b281053d86907b3e908fce032f8f141/src/native/freshness/cli.rs). `Tier` starts near line 73; ordinary scope near 314; `RowCtx::freshness_row` near scan line 53; CLI schema constant at line 54.
- **S3 — ledger mirror:** [bob-ledger-tools/main.js at 6f8aca0](https://github.com/bobs-org/bob-plugins/blob/6f8aca0beae21e66922ae61a6d865d642d056803/plugins/bob-ledger-tools/main.js): `freshnessEvaluate` near 5105, tier ordering 5441, queue 5534, counts 5654, footer tier constants 5930, shared presentation 6105, row extraction 9099, capability exposure 9601.
- **S4 — navigation and completion:** [bob-navigation-hotkeys/main.js](https://github.com/bobs-org/bob-plugins/blob/6f8aca0beae21e66922ae61a6d865d642d056803/plugins/bob-navigation-hotkeys/main.js): tier recognition near 33470, anchors 33958, remaining/boundary helpers 34009, queue-line resolution 34387, jumps 37534. [Cycler editor completion adapter](https://github.com/bobs-org/bob-plugins/blob/6f8aca0beae21e66922ae61a6d865d642d056803/plugins/task-status-cycler/src/180-plugin-editor-edits.js) and [completion mixin](https://github.com/bobs-org/bob-plugins/blob/6f8aca0beae21e66922ae61a6d865d642d056803/plugins/task-status-cycler/src/160-plugin-completion.js).
- **S5 — existing Ready predicate:** [native Tasks lane queries](https://github.com/bobs-org/bob-cli/blob/660c171c6b281053d86907b3e908fce032f8f141/src/native/dataview/tasks/mod.rs), `READY_QUERY` at line 94; S3 `planLaneVisible` at line 3015. `RichTask` already contains parsed tags.
- **S6 — vault observation:** read-only `bob query --format markdown --query-file -` with `FROM "gtd_daily.md"`, flattening task descriptions/tags/repeat/schedule; confirmed with `bob query --format markdown --tasks-file -`, exact file-path regex, grouping by `status.type`. DQL task line indexes are zero-based; repository/CLI queue lines are one-based. Queries succeeded; unrelated ambiguous-link diagnostics were emitted during the DQL scan. No vault file was opened or mutated directly.
- **S7 — deployed observation:** read-only `bob freshness --format json`, restricted in the presented output to date, schema, counts and `gtd_daily.md` queue rows. Observed 2026-10-04, schema 7, 128 walk entries, no GTD rows, budget null. Other private task descriptions were not copied into this report.
- **S8 — baseline test run:** in the opened bob-plugins checkout: `node --test scripts/test-ledger-tools-freshness.cjs scripts/test-ledger-tools-freshness-footer.cjs scripts/test-navigation-freshness.cjs scripts/test-task-status-cycler.cjs`. Exit 0; 313 passed, 0 failed. Both implementation checkouts remained clean afterward.
- **S9 — primary GTD guidance:** [David Allen Company Outlook for Web setup sample](https://gettingthingsdone.com/wp-content/uploads/2021/04/GTD_Outlook_Web_SAMPLE-LTR.pdf), particularly printed pages 1, 2 and 20 on system simplicity, workflow stages, and daily versus weekly list review.
- **S10 — primary GTD checklist:** [GTD Weekly Review checklist](https://gettingthingsdone.com/wp-content/uploads/2014/10/Weekly_Review_Checklist.pdf), on clearing inputs, updating action/project lists and reviewing checklists. It supports the critique's general sequencing, not this project's exact daily policy.
- **S11 — primary Tasks documentation:** [Recurring Tasks and Custom Statuses](https://publish.obsidian.md/tasks/Getting%20Started/Statuses/Recurring%20Tasks%20and%20Custom%20Statuses), on recurrence generation after a DONE transition and eligible statuses for the next occurrence. Local cycler source supplies the project-specific adapter evidence.
- **S12 — primary Tasks tag/status semantics:** [Tasks query filters](https://publish.obsidian.md/tasks/Queries/Filters), on TODO versus other open status types and partial tag matching. The proposed whole-token rule is a deliberate local tightening.
- **S13 — plugin source instructions:** opened bob-plugins `AGENTS.md`: linked-repo source of truth, build/fragments rules, and required `bob plugins sync` deployment after changes.

## Recommended solution

**Implement PRE and POST as two explicit routine tiers in the shared Rust/JavaScript review evaluator, surrounding the existing seven tiers.** Admit task-line `#gtd #pre` / `#gtd #post` Ready tasks independently of freshness due-ness, while retaining the normal visibility and scheduling gates. Use source order within these tiers, preserve existing state/bucket behavior, and leave recurrence generation to the current Tasks-aware completion path.

Migrate the seven active daily preparation tasks to `#gtd #pre` and the active “Morning review” task to `#gtd #post`; leave cancelled and weekly rows untouched. Shorten the POST task to a truthful sign-off, document `[S` to start and `]S` to finish the single-marker routine, and allow explicit completion after required reviews and intentionally bounded ROTTEN upkeep. Keep the queue and skipped ROTTEN tasks intact. This is a focused extension of the system the user already knows, with enough behavioral clarity to avoid copied stamps, never-ending recurrence loops, and an unreachable completion marker.
