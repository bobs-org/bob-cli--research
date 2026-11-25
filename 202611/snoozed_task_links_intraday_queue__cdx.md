# Snoozed Task Links: a reliable intraday holding area
Independent research by **cdx** · 2026-11-25  
Task: `bob.md#^snoozed-tasks`  
Scope: research and recommendation; no product or vault changes.

## Assessment

**This is a good feature if it postpones a planned link's availability without changing the underlying task's meaning.** Keep the proposed daily `## Snoozed` section and make `bob tick` the background wake owner. Implement an explicit, same-day hold on a Task Link, with a visible wake time, durable storage, and a safe release into the agenda.

The two lines in the task are not yet a sufficient implementation specification. The hard parts are preserving today's commitment, waking despite delayed background work, preserving notes, and handling a task whose circumstances change while asleep. A simple “move links out, then move them back when the clock passes” implementation would introduce silent loss and surprising task mutations.

I would avoid a new checkbox status, avoid extending `scheduled` to timestamps, and avoid automatically snoozing Calendar Event Tasks in the first release. Those alternatives change much more than this problem requires.

## What the task actually asks for

I read the task and its nested notes through the read-only `bob query` interface, selecting `file.path = "bob.md"` and `blockId = "snoozed-tasks"`. Its title is “Add support for ‘snoozed’ task links!” Its explicit requirements are:

- Use a new H2 `Snoozed` section in daily files.
- Make `bob tick` responsible for waking tasks.
- Support work already intended for today that cannot be done until a particular time.

The supplied examples are an email after an interview ending around 3:30 p.m., and tasks to do at home around 7 p.m. Event Tasks are described as the canonical example, but the text does **not** explicitly require migrating their existing calendar machinery into this feature. The task specifies neither syntax, precision, destination selection, notifications, nor next-day handling.

The distinction is useful: “email after the interview” may be a real prerequisite, whereas “home around 7” is an estimated context change. A clock can remind Bryan to reconsider either task; it cannot prove that the interview finished or that he arrived home. Snooze should be an explicit planning decision, not an assertion that a real-world prerequisite has been satisfied.

## Evidence from the current system

The following are observations from source and accepted decisions, not proposed behavior.

| Finding | Implementation consequence | Evidence |
| --- | --- | --- |
| Today is currently the set of open tasks reached by dedicated Task Links under today's open Pomodoros. It is deduplicated by resolved note path and block ID. | Moving links under an unrelated H2 removes them from Today unless readers deliberately learn a second kind of planned association. | `bob-cli:src/native/plan_budget/today.rs:1–150`; `decisions:today-is-read-from-the-ledger`. |
| A dedicated link bullet must contain exactly a plain or embedded block link after recognized Pomodoro markers. | Appending an arbitrary wake field to an ordinary queued link can make existing lineup and Today readers stop recognizing it. A new row grammar needs its own parser. | `plan_budget/today.rs:60–101`; `capture_task_toggle/links.rs`; plugin `060-today.js`. |
| Next and WIP are sticky outside the daily-note exception, while future scheduled dates and dependencies derive Blocked. Blocked can lose the previous lane. | A timestamp implemented as task blocking would damage the intended “still committed for today” semantics. Daily-note tasks also need coverage: unlinking can clear Next there. | `task_status_hooks/sync.rs:1340–1400`; `decisions:task-lanes-are-sticky`. |
| Freshness is a confirmation date. Its input includes Today membership; review tiers and lane pressure are separate concepts. | Snoozing should not manufacture a new freshness state or erase lane pressure. Planned-but-asleep membership needs deliberate review treatment. | `freshness/state.rs`; `docs/freshness.md`; audited freshness and decay memory. |
| Capture linking a task blocked only by its own prerequisites can delete those prerequisites before linking. Some link operations can also retire a future schedule. | A background wake must not invoke the ordinary high-level capture gesture as a shortcut. Share safe parsing and placement primitives, not the gesture's full mutation policy. | `decisions:capture-link-drops-blocking-deps`; `capture/pomodoro_link.rs`; `capture_task_toggle/task_update.rs`. |
| Tick is a sequential pipeline: gcal, gmail, gkeep, refs, projects, tasks. Task reconciliation defaults to 15 minutes. Individual steps have 10–30 minute ceilings. | Adding wake after reconciliation does not provide timely intraday resurfacing. | `docs/tick.md`; `tick/catalog.rs:115–169`. |
| A noninteractive tick returns immediately when another tick owns its run lock. | Even putting wake first in the existing catalog does not solve an earlier tick stuck in a long child. | `tick/lock.rs:32–65`; `tick/run.rs:87–105`. |
| Agenda JSON already carries calendar boundaries; the Mac schedules a boundary refresh while visible. | Reuse the boundary-refresh pattern for snooze presentation; keep semantic evaluation in bob. | `capture_pomodoros_agenda.rs:279–290,1010–1035`; Mac `CapturePanelModel.swift:1714–1759`. |
| Calendar links already have phase-based MEET placement, buffering, refiling ownership, and clock-aware closing. | Moving those links into a generic snooze section would create competing owners and could interfere with meeting handling. | Audited `synced-meetings-link-by-phase`, `event-buffers-widen-the-span`; `docs/gcal.md`. |
| Reading Board already calls its blocked reference lane “Snoozed.” | User-facing copy should distinguish “Snoozed until 15:30 today” from reference blocking; do not merge their storage or status rules merely because the labels match. | `docs/ref.md:416–454`. |

The current write infrastructure has maintenance locks, input revalidation, staged replacements, and recovery manifests. It also explicitly supports reporting **partial** multi-file application. Reusing it is valuable, but calling a multi-file wake “atomic” without qualification would be wrong. A same-day wake that changes only the daily note is substantially easier to make reliable. See `task_status_hooks_write/apply.rs:30–170`.

A read-only `bob tick --status --format json` on Apollo returned no previous step runs for that host. That is not evidence that tick is absent on the actual writer. I did not inspect crontabs, change scheduler configuration, or establish a real production wake-latency bound.

## What comparable systems clarify

OmniFocus distinguishes a defer date, which constrains availability, from a planned date, which expresses intended work without imposing that constraint. That separation supports keeping Bob's durable task conditions distinct from this day's agenda placement. It does not imply Bob should adopt all of OmniFocus's date fields. [OmniFocus 4: The Outline](https://support.omnigroup.com/documentation/omnifocus/universal/4.10.1/en/outline/)

Things includes “This Evening” within Today and separates scheduling from reminders and deadlines. This is a useful precedent for a quiet, still-visible same-day shelf: “later today” should not disappear from the day's commitments. [Things: Scheduling To-Dos](https://culturedcode.com/things/support/articles/2803579/)

Things also treats reminder snoozing as notification behavior. Bryan's request is stronger: remove premature work from the active agenda and restore it later. A notification alone does not solve that. Notifications can be a later, optional layer rather than the core persistence mechanism. [Things: Setting a Reminder](https://culturedcode.com/things/support/articles/2803585/)

These are product precedents, not empirical evidence that snoozing improves productivity. The justification here is the concrete repeated interruption described in the task.

## Alternatives

| Approach | Benefit | Main cost | Judgment |
| --- | --- | --- | --- |
| A handwritten “Later today” list or existing future Pomodoro | Almost no implementation; good way to validate the interaction | No automatic clock transition or trusted missed-wake recovery | Useful fallback, insufficient for the stated request |
| Reminder notification only | Small visible feature | Does not remove premature links from the active lineup; notification can be dismissed or missed | Supplement only |
| Task-level timestamp, new status, or timed `scheduled` | Uniform global availability model | Broad parser/status/dependency/freshness changes; lane loss; unnecessary permanent task state | Reject for this task |
| Keep links in place and filter them by wake metadata | Preserves physical destination, reduces move operations | Every lineup, start, close, Today, and client reader must understand the filter; an older reader can act early | Plausible alternative if destination preservation becomes the dominant need |
| Dedicated daily Snoozed link records, then materialize ordinary links | Matches the task; readable vault source; dormant links are outside existing execution lineups | Requires planned-today membership, wake placement, and recovery rules | **Recommended** |

The dedicated section has a useful failure direction: an older parser generally ignores dormant rows instead of accidentally working them. That is only a migration advantage, not permission to deploy partially compatible clients indefinitely—old views can still undercount today's commitments.

## Proposed behavior

### 1. A snooze belongs to a daily plan association

Define three concepts explicitly:

- **Live links:** today's existing eligible links under open Pomodoros.
- **Dormant links:** valid unresolved snooze commitments for the owning daily plan.
- **Planned today:** the identity-deduplicated union of live and dormant links.

“Snooze until 15:30” means “keep this task in today's commitments, but withhold its link from normal start/close lineups until this instant.” It does not mean “lower its importance,” “complete it,” or “satisfy its dependencies.”

Keep Next/WIP unchanged for an already-linked task. If the user invokes snooze on an otherwise unplanned Ready task, the *human operation* can commit it to Next while creating the dormant association, exactly as an explicit planning gesture would. Explain that result in the preview. Automatic wake never stamps freshness, clears keeps, lowers lanes, drops dependencies, or removes a scheduled hold. Reconcile retains authority over real blockers.

A future snoozed task remains in lane-cap pressure: it still consumes today's attention budget. Suppress the same review prompts that a comparable live planned link suppresses, without changing the persisted confirmation. Once the original plan day expires, that suppression ends. This prevents an old unresolved snooze from hiding a task forever.

Keep execution-oriented APIs separate from the new planned set. Do not change `today_links()` to emit fake Pomodoro entries with missing entry lines. Add a companion commitment result or tagged association type; migrate presentation and freshness consumers intentionally.

This is a **deliberate amendment** to the existing open-Pomodoro-only definition of user-visible Today. It retains the accepted principle that Today comes from the ledger and is never written as a task tag or field. It is not a decision already authorized by existing memory.

### 2. Store one human-readable record under the requested H2

An illustrative grammar—not existing Bob syntax:

```markdown
## Snoozed

- [wake:: 2026-11-25T15:30:00-05:00] ^snooze-a81f
  - [[work#^email-followup]]
    - Send the interview update.
```

The non-checkbox parent is the snooze record; its single direct child is a plain Task Link with its note subtree. The stable snooze ID supports editing, diagnostics, retry tracking, and cross-day recovery. The task remains at its canonical source. Avoid copying its description or checkbox into the daily file.

One active snooze per resolved task identity per plan day is enough. Snoozing again edits that record; it does not append another timer. Selection should operate on resolved identity, not alias text or line number. If the selected task has multiple live planned occurrences, the gesture must deal with all of them consistently; v1 can refuse a complicated mixed-history case with a precise explanation rather than silently leaving an active duplicate.

Use the containing daily note as the plan date, but store the release instant with an explicit numeric UTC offset. RFC 3339 supplies an unambiguous timestamp representation; an offset is not an IANA timezone or a recurring wall-clock rule. [RFC 3339, §§4–5](https://www.rfc-editor.org/rfc/rfc3339.html)

Interpret time-only input through Bob's configured timezone, already centralized in `src/native/env.rs:469–542`, not the agent's UTC clock or each client's host zone. The UI can display `15:30`; storage should not depend on which host wakes it. Reject nonexistent local DST times; ask for an explicit offset/occurrence for ambiguous ones rather than guessing. A time already passed today should offer “Wake now” or require another explicit time, never silently become tomorrow.

For the first release, accept same-day one-shot wake times. Cross-day scheduled work stays with the existing date scheduling flow. Relative durations are a convenience only if the preview resolves them to one concrete same-day instant.

### 3. Make the wake transition narrow and repeatable

Compute due as `wake_at <= now`. Do not require a tick to occur in a matching minute.

Under the existing vault write guard, re-read the record and resolve the target. Then:

| Condition | Result |
| --- | --- |
| Still before wake | No mutation |
| Due, task open, no real blockers, eligible destination available | Move its bare link and owned child notes into the ordinary queued destination; retire the source record in the same daily-note replacement |
| Task already live today | Do not duplicate it; preserve or merge owned notes explicitly before retiring the redundant record |
| Task completed or canceled | Retire the commitment without recreating an open link; preserve notes/history |
| Real dependency, project, or future-date blocker | Keep a visible “time arrived · blocked” item; retry after blocker changes |
| Missing/ambiguous note, duplicate block ID, malformed record | Keep visible with a specific repair action; no guessed target |
| Own plan day ended | Surface a missed-plan item for explicit re-planning; do not silently recommit it to today |

The original snooze was an explicit decision to link later, so waking that exact selected task does not need a second confirmation. It must not spread to newly unblocked dependents or project residents: those remain governed by the existing successor-offer policy.

Use lower-level link relocation/placement helpers with a **wake-specific mutation policy**. Never execute `bob capture @route:id` in the background. Its dependency-dropping and pull-forward behavior is appropriate only to its explicit human gesture.

Resolve the destination at wake using the task's current effective type and compatible queued Pomodoros; do not store a fragile source line number. A manually chosen destination can be an optional hint, revalidated at wake. If that hint became invalid, show the fallback chosen or retain the record for resolution.

I recommend that automatic wake **not append to a running Pomodoro**. A new link can enter the current session's default close selection, which is a stronger effect than merely becoming available. Reuse/create an eligible unstarted placeholder. If the only matching open entry is running and a duplicate name is forbidden, show “Ready · waiting for a queue destination” and retry after that session closes. An explicit user “Use now” action may join the running session. This exception must be visible, not a second invisible sleep.

For v1, snoozing an unworked queued link is the safe core operation. Moving already-worked or running-session history should be refused or handled through the existing close/park flow first. Preserve note subtrees and never delete a timed or history-bearing Pomodoro merely because its last planned link moved.

### 4. Tick owns background wake; the UI owns timely visibility

“Wake at 15:30” cannot honestly mean exact-second execution on a sleeping or offline writer. Separate:

1. **Availability time:** a pure comparison the read model can explain immediately.
2. **Placement time:** when the background writer safely materializes the active link.

The agenda should change a due row to “Ready · awaiting wake” even before placement succeeds. It should never claim the link is already in a Pomodoro when the write has not happened. This also makes missed scheduler runs observable.

Do not put wake at the tail of the existing tick pipeline. For a production implementation, I recommend a short local wake pass owned by `bob tick`, run before the long-pipeline single-flight early return. Give that pass its own short lock, use the same writer pin and shared vault lock, and bound lock waits. Thus an invocation can process a newly due item even if another tick is still waiting on Google. Existing intake/reconcile ordering remains intact.

This is a proposed scheduler change, not something the catalog currently supports. It needs its own status/receipt handling so an older long tick cannot overwrite the latest wake result. Read-only `--status` and `--dry-run` must remain read-only. No new daemon or per-task OS job is required.

The pass still cannot bypass a busy vault. Report `waiting` and retry; do not consume a long cadence after contention. Show last successful wake check, next wake, and pending failures. A reasonable initial *conditional target* is placement within one configured tick interval while the writer is awake and the vault writable. Verify that on the actual writer before promising a numerical bound.

If implementation scope must be smaller, a first catalog step is acceptable only with an explicitly best-effort latency contract and the due-but-unplaced UI. It does **not** solve the long-running prior-tick problem.

Extend the existing agenda boundary-refresh mechanism to the minimum of calendar and snooze boundaries. The Mac should request fresh bob data at the boundary, on show, on app/system resume, and after relevant vault events. Swift renders returned state; it does not parse vault records or independently decide mutation rules. Obsidian needs the equivalent read refresh and command adapter.

### 5. Do not lose commitments at midnight

A today-only scanner can strand a snooze if the writer slept from afternoon until the next morning. Scanning yesterday alone still loses it after a weekend away.

On day change/startup, discover unresolved records from older daily notes through a rebuildable index or a scan of canonical daily files. The Markdown records remain authoritative; a local cache is only acceleration. A cache deletion, changed old note, or machine switch must not erase discovery.

Show older items as “Missed from Monday” with Wake today, Reschedule, and Remove from plan actions. Preserve the original timestamp. Do not silently grant every old plan a new Today commitment, and do not suppress ordinary review because yesterday's record still exists. Deduplicate presentation if that task is already actively planned today.

This is intentionally less ambitious than automatic carry-forward. Explicit cross-day adoption needs safe two-file recovery; use the existing staged/recovery infrastructure and make the snooze ID part of idempotency checks. Write the destination before retiring the old source, retain recovery evidence on partial apply, and recognize a destination already installed on retry. Do not assert multi-file transactional guarantees that the current applier does not provide.

### 6. Keep the interface small

Use a named “Snooze until…” task/link action with presets and a clock input, plus Wake now, Change time, and Remove from today's plan. Preview the resolved time and placement consequences; removal cancels only the daily commitment, not the task.

A compact collapsed agenda section can read “Snoozed · 2 · next 15:30.” Expand to show times, target links, and any exceptional state. Due-but-unplaced or broken rows should not hide behind a calm count. Avoid adding a new global attention-letter family or making every wake interrupt the user.

Do not overload `s:`, `+`, `=`, or other capture operators without a separate grammar review. A public CLI shape, if needed, is better centered on the daily queue—for example `bob snooze` as a read-only list with explicit set/wake/remove verbs—than under `bob task`, whose documented membership is vault-wide task-line rewriting. That spelling is illustrative, not a request to add it unchanged. Any new public options need short aliases and the usual dry-run/JSON/help contract.

## Requirements I would change or add

These changes are recommendations, not claims that they already appear in the task.

| Adjustment | Reason |
| --- | --- |
| Clarify that this snoozes a daily Task Link, not a task status | Preserves commitment, existing schedule semantics, and durable task identity |
| Include dormant links in the visible day's commitments, with an explicit distinction from executable links | Otherwise the requested move defeats “I know I need to do it today” |
| Limit initial authoring to same-day one-shot times and safe unworked links | Covers the supplied examples while containing history and recurrence complexity |
| Keep Calendar Event Tasks on the existing calendar path | Avoids two writers moving the same MEET links; generic event-following automation needs a separate ownership design |
| Treat wake as availability/placement, never implicit start, completion, dependency removal, or human confirmation | A timer has no evidence for those actions |
| Add visible due, blocked, invalid, and missed states | Reliability requires recoverable failure, not just a happy-path timer |
| Add bounded wake processing outside tick's long-pipeline exclusion | Prevents unrelated intake latency from starving due work |
| Preserve all link-owned notes and historical time | Moving a planned association must not discard recorded information |
| Add explicit cross-day recovery without automatic recommitment | Survives sleep and multi-day absence without inventing today's plan |
| Make notifications optional later | The core problem is agenda availability; alert volume is a separate choice |

The largest policy change is the planned-today union. The largest engineering addition is reliable tick servicing. If Bryan wants neither, the honest smaller alternative is a manually reviewed “Later today” list—not a supposedly reliable timer that silently drops out of Today.

## Implementation boundaries and evidence to require

This is a component map, not an approved implementation plan or estimate.

| Area | Likely touchpoints | Evidence required |
| --- | --- | --- |
| Markdown model and pure reducer | New shared snooze module; `note_tasks`, `vault_links`, existing link subtree helpers | Parse/write round trips; canonical identity; future/due/invalid states |
| Safe mutation | `capture_task_toggle/{links,relocation}.rs`; `task_status_hooks_write/*` | Source and destination change together for same-day moves; retry convergence; no destructive capture policy leakage |
| Planned membership | `plan_budget/today.rs`, freshness scan, daily-note reconcile exception; plugin `060-today.js`, `290-plugin-today-and-location.js` | Rust/JS vectors for live/dormant union, counts, review suppression, and lane retention |
| Background servicing | `tick/{catalog,run,lock,state,receipt,gates}.rs` | Writer pin, long intake contention, restart, read-only modes, receipt consistency |
| Agenda protocol and client | `capture_pomodoros_agenda.rs`; Mac `CaptureAgendaModels.swift`, `CaptureAgendaPresentation.swift`, `CapturePanelModel.swift` | Additive/versioned payload; absent-field fallback; boundary refresh and resume behavior |
| Obsidian actions and marks | Navigation/task-link adapters and ledger-tools source fragments | Shared command semantics; visible dormant/due states; normal build and deployment checks |
| Compatibility and documentation | Capture/plan/tick contracts, JSON fixtures, daily section conventions | Reader compatibility before writers emit records; existing schedules and Event Task handling unchanged |

Do not make the existing `AgendaRole` enum unexpectedly grow a new value for a non-Pomodoro object without a decoder audit. A separate optional `snoozed` payload with its own state is a cleaner additive boundary. Treat any changed meaning of an established JSON field as a contract change, consistent with the daily release train.

Minimum acceptance cases:

1. A planned task snoozed until 15:30 is absent from default start/close selection at 15:29, remains counted as a daily commitment, and preserves its lane and notes.
2. At exactly 15:30 it becomes due; the first successful eligible wake moves it once. A second wake is a no-op.
3. A 15:40 catch-up processes a 15:30 record; no narrow clock-window test loses it.
4. A running destination, absent daily section, or busy vault produces a visible pending state without inventing a session or deleting the record.
5. A dependency or project blocker added while asleep prevents placement. Prerequisites and schedules remain byte-for-byte intact.
6. Completion, cancellation, explicit re-linking, note rename, task move, and duplicate block IDs are handled by resolved identity and explicit invalidation rules.
7. Existing task-link removal/completion/release gestures also retire or intentionally preserve dormant associations. “Remove from plan” must not be undone by a later timer.
8. Notes beneath the moved link survive; worked links and timed closed Pomodoros retain their history.
9. Repeated snooze edits update one record. Concurrent editor changes abort/replan instead of overwriting the edit.
10. Several due records have deterministic ordering, share valid destinations without duplicating links, and do not renumber a running session's close lineup.
11. Restart after midnight or a multi-day absence shows every unresolved missed commitment; deleting the cache does not lose it.
12. Different host timezones and DST boundaries resolve the same stored instant; backwards clock movement cannot resurrect an already-retired record.
13. A long network child in another tick does not prevent the proposed wake pass from attempting work; shared vault contention still respects the write guard.
14. The Mac at a visible time boundary, after sleep, and on reopening agrees with bob; old clients tolerate absent/new optional payloads.
15. Google retiming, buffer changes, future MEET links, scheduled-date ticklers, Gmail holds, and ordinary successor offers retain their existing behavior.

These tests should exercise behavior and failure recovery, not merely mirror parser implementation. Product code was not changed or compiled during this research. Future Swift work must follow the linked repository's compile/CI requirements; a Linux-only check cannot verify macOS targets.

## Limits and source provenance

This report was formed independently. I did not read another swarm researcher's report, chat, summary, or findings.

Source snapshots inspected:

- **bob-cli:** `5ab392a1ba087c6f87d8685035979498082079ed`.
- **bob-plugins:** `69047866eacd505e8a306440c99e71b481cfdf31`.
- **bob-mac-capture:** `3931c308b376904d063208e13f793691396e58cc`.

Repository paths above are relative to the named repository at those snapshots. The task was read from the live vault using `bob query`; accepted decisions and glossary terms were read through audited `sase memory read`. Relevant decisions include sticky lanes, ledger-derived Today, preservation of link notes/time, project blocking, unblocked ticklers, the decay ladder, capture dependency dropping, successor offers, meeting phase/buffer ownership, and the thin Mac client.

External sources were official product documentation and RFC 3339, accessed on 2026-11-25 and linked beside the claims they support. I did not measure user interaction frequency, end-to-end scheduler latency, or the current writer's sleep/availability. The proposed grammar, command shape, state names, and fast wake pass are design recommendations rather than implemented interfaces.

## Recommended solution

**Implement a small, durable daily Snoozed queue for ordinary planned Task Links.** Keep one visible record per task and plan day, store an explicit wake instant, preserve lane and notes, and include dormant work in today's commitments without putting it in executable lineups.

Let `bob tick` perform a guarded, idempotent wake using safe placement primitives, with a short wake pass that is not starved by the long intake pipeline. Make due-but-unplaced and missed-day work visible so the system remains trustworthy when timing or placement fails. Keep Calendar Event Tasks, task-level date scheduling, and real dependency conditions on their existing paths.

Ship this only with the planned-today contract and recovery behavior defined. The feature is worthwhile; a broader timed task-status system would solve a different problem at much greater cost.
