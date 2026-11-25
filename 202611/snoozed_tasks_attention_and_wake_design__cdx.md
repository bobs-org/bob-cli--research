# Snoozed tasks: a quiet later-today queue with a trustworthy wake signal

Independent research by **cdx**, 2026-11-25. This report evaluates the user-designated [earlier consolidated proposal](snoozed_task_links/snoozed_task_links.md) against the current request and source code. It is research, not an implemented feature or an approved implementation plan. I did not consult the other reports or researchers in the current swarm. The earlier report's historical adjudications are shared input, not conclusions adopted by vote.

**Recommendation:** build a separate `## Snoozed` section after `## Pomodoros`. Exclude snoozed-only tasks from the active link budget; show a clock and wake time at their definitions; move eligible tasks into untimed Pomodoros when they wake. Preserve a small wake receipt so the resulting Task Link says **Ready since 14:31**. Announce successful wakes with brief grouped notifications and retain that visual evidence afterward. Exclude Event Tasks everywhere. Strengthen the original proposal's timing and notification design before implementation.

The useful promise is: **“Keep this on my plan for today, out of my active queue until this time, then make its return hard to miss.”** This concerns attention and placement, not another task status, deadline, or appointment.

## Evidence and scope

I inspected these local source snapshots through the required repository workflow:

| Repository | Revision | Evidence |
| --- | --- | --- |
| bob-cli | `8f88a52c1cfc59236d6ddc4bd36ee6f11de95afd` | `docs/plan.md`, `docs/today-marks.md`, `docs/capture.md`; `src/native/plan_budget/{mod,today}.rs`; `capture_pomodoro_start.rs`; `capture_pomodoro_close/links.rs`; `capture_pomodoros_agenda.rs`; `capture_language/markers.rs`; `capture_drawers.rs`; `tick/{catalog,lock}.rs`; `env.rs`; `desktop_notify.rs` |
| bob-plugins | `7c3431499200db62cd062ecab0e2587010a426f6` | `plugins/bob-ledger-tools/src/{143-today-marks,275-plugin-today-marks}.js`; `plugins/bob-navigation-hotkeys/src/160-pomodoro-reorder.js`; command sources and plugin documentation |
| bob-mac-capture | `3931c308b376904d063208e13f793691396e58cc` | `Sources/BobMacCapture/NotificationService.swift`, `WalkAttentionStore.swift`; `Sources/CaptureCore/CaptureAgendaBoundaryRefresh.swift` |

Audited memory reads covered Task Link, Event Task, Pomodoro, Task Freshness, sticky lanes, ledger-derived Today, note/time preservation, open-session naming, project blocking, successor offers, the review attention mark, dismissal keys, and CLI rules. No vault mutation, implementation test, plugin deployment, or live notification experiment was performed. Installed user keybindings, OS notification permissions, and actual tick runtimes were not measured. The older report's operational observations are not a new measurement here.

Important verified facts:

- Today is derived from dedicated links under open Pomodoros. The budget accepts a broader set of link occurrences, including some prose links. The two are not interchangeable.
- The start lineup requires a bare dedicated link after supported tomato stripping. Adding a clock or arbitrary text directly to that line can break recognition.
- Definition tomatoes are display-only decorations with exact source mapping, not task fields. Existing daily-note rendering suppresses them.
- The plugin's shared `planDeferredPomodoroLinkCleanup` currently searches open Pomodoro ranges only. A new external queue requires cleanup parity.
- Plain session close can classify ordinary links as worked/in progress. Automatically appending a newly woken task to a running session risks false work attribution.
- The Mac already has native notifications, authorization status, actions, boundary refresh, and lifecycle refresh patterns. Bob's general desktop notification helper is best-effort, uses AppleScript on macOS, and swallows failures.
- `s:<digits>` is a day offset. It must not be reused as a clock-time token.
- Bob has a configured timezone, with host-local fallback. Cross-host interpretation must be deliberate.

## Is this a good idea?

Yes. Day-level scheduling is too coarse for “call after lunch”; leaving the task among active links makes it distracting all morning; a reminder alone does not remove that distraction. A visible later-today queue fills the gap without changing task lanes.

The proposed separate section is a sound foundation. Existing execution readers cannot accidentally start its tasks. Human-readable Markdown is easier to trust than a hidden timer database. Wake is a concrete move into the existing active ledger, rather than a new interpretation silently imposed on every existing reader.

Three risks need attention:

1. **A second backlog:** retain same-day scope, visible counts, and no automatic next-day carry. Avoid arbitrary future reminders, recurrence scheduling, event anchors, and dependency rules in the first release.
2. **Hidden overcommitment:** honor the requested `max_links` exemption, but show waiting work separately. An active-work cap and a summary of later work answer different questions.
3. **False readiness:** a clock may pass while the task is blocked or the vault cannot be safely written. Distinguish “due to wake” from “ready.”

A time also approximates “after I get home” or “after the interview ends.” Use snooze when that approximation is useful. Actual completion dependencies and successor offers remain separate; waking must never silently clear prerequisites.

Product precedent supports this distinction: Things separates start planning, deadlines, time-specific reminders, and a This Evening subdivision of Today. That is useful evidence for separating later attention from active work, not a specification Bob must copy. [Things scheduling](https://culturedcode.com/things/support/articles/2803579/), [Things Today and This Evening](https://culturedcode.com/things/support/articles/4001304/).

## Explicit adjustments

| Topic | Recommendation | Change or clarification |
| --- | --- | --- |
| Event Tasks | Resolve identity/type and refuse snooze at every authoring/wake route. Invalid hand-written event rows are non-executable and diagnosed. | Stronger than the old proposal's allowance for manual event snoozing; directly follows the current request. |
| Budget | Snoozed-only tasks contribute zero to `plan.max_links`. Eligible woken on-clock links count normally. | **Reverses the earlier recommendation. The current requirement wins.** |
| Definitions | Clock plus `until 14:30` while sleeping; tomato after wake, with a compact ready-since cue. | Makes active and sleeping plans distinguishable without another status. |
| Woken links | Main label `Ready since 14:31` uses actual successful placement; detail says `Snoozed until 14:30`. | Chooses actual wake time, not the time Snooze was initially pressed; exposes lateness honestly. |
| Timing | Running clients trigger the same guarded Bob writer at boundaries; tick provides recovery. | **Strengthens tick-only scheduling.** Five-minute polling alone does not deliver an intuitive minute-specific experience. |
| Notification | Native banner and one short sound by default, foreground ribbon, durable link provenance; group simultaneous wakes. | Treats delivery as a feature, not a single best-effort command side effect. Sound is separately switchable. |
| Running links | Close-first flow through existing session outcomes before moving the link away. | **Additional safety constraint:** do not silently erase recorded context or stop the timer. |
| Midnight | No automatic carry; expired rows become history and normal review resumes. | Retains narrow scope; add a discoverable missed-snooze summary. |
| Freshness | Reuse human-commit rules; background wake never stamps review or increments keeps. Recurring tasks retain no-stamp behavior. | Narrows the old broad “promote and stamp” wording. |
| Glossary | Draft below, published with the implemented contract. | Designs the requested term without claiming the feature already exists. |

## Core semantics

Keep technical Today unchanged: open tasks behind dedicated links under today's open Pomodoros. Snoozed rows enter it only after successful placement. In user-facing copy, both belong to **Today's plan**, with **Active** and **Snoozed** subdivisions. Do not tell a user their deliberately planned later-today task is “not today.”

Expose separate sets:

- `active_today`: existing Today membership.
- `snoozed_today`: valid, open, eligible ordinary tasks waiting in today's queue.
- `planned_today`: the union, used deliberately for presentation and review exclusion.

Do not replace all Today consumers with the union. Start lineups, close outcomes, attribution, and the tomato require active membership. Share identity resolution/classification and let each consumer choose its documented set.

Snooze does not set `[scheduled::]`, derive Blocked, write `#snoozed` onto definitions, or introduce a checkbox status. A Ready task can be committed to Next through the normal human gesture; Next and Pending stay in their lanes. Removing a snooze does not lower the lane. Explicit release follows its existing lane rule and also removes the pending snooze.

Exclude valid sleeping and due-to-wake rows from today's routine review walk. Otherwise hand-written or already-stale tasks can immediately demand review after being set aside. Preserve the daily-note-resident exception carefully: an eligible ordinary task in that note is still deliberately committed while snoozed. This must not admit Event Tasks. Invalid, unresolved, or blocked rows must not suppress legitimate review indefinitely.

Keep `max_next`, `max_pending`, and Ready policies independent. The requested exemption concerns active links, not all sticky-lane commitments. If a dashboard adds a Snoozed group, make displayed rows exclusive without silently changing the lane meters.

| State | Definition mark | Daily presentation | Active budget | Announcement |
| --- | --- | --- | --- | --- |
| Active, never snoozed | Existing tomato | Ordinary link | Existing rules | None |
| Sleeping | Clock `until 14:30` | Snoozed row `14:30` | Zero | None |
| Time passed, write pending | Clock `wake due 14:30` | `Wake due · 14:30` | Zero | No ready claim |
| Successfully woken and active | Tomato + `since 14:31` | `Ready since 14:31` | Existing rules | Once per wake event |
| Blocked/missing/invalid | No false ready mark | Specific diagnostic | No executable snooze | Failure explanation if a promised wake could not happen |
| Finished/released/removed | Normal existing state | Preserved notes/history as appropriate | Existing rules | Cancel pending notice |

An active link plus a snoozed row for the same resolved task is a conflict, not two commitments. Active wins for mark and budget; lint the redundant snooze. Supported snooze removes all eligible planned active occurrences atomically. Never hide an active occurrence because another spelling also appears in Snoozed.

## The interaction and appearance

### Snooze from a Task Link

Add **Snooze until…** as a named command, Task Link context action, and Task Card action. Recommended default shortcut: **Ctrl+Shift+S**, subject to installed-binding conflict checks. I found no matching literal registration in the inspected Bob sources, but that does not prove Bryan's OS, Obsidian, or other plugins leave it free. Never overwrite an existing binding; keep the named/context action available. Avoid undo/Vim meanings such as Ctrl+Z or bare `z`.

One small anchored card is sufficient:

```text
Snooze “Email Dan”
Keep it on today's plan. Bring it back at:

[ 14:30                              ]
  In 15 min     In 30 min     In 1 hour

Today · 14:30 · America/New_York
Active links 8 → 7     Snoozed 2 → 3

                         Snooze ↵
```

Select the time field initially. Accept `1430`, `14:30`, `+15m`, `+1h`; preview the exact date/time. Enter applies once. Escape/Ctrl+[ cancel; `q` uses Bob's existing text-control exception. No second confirmation for an ordinary planned link. After success, focus the new Snoozed row and provide normal checked Undo.

The same action on a sleeping row edits its time and offers **Wake now** and **Remove from today's plan**. On a woken link it starts a new snooze cycle. Do not silently repeat a snooze.

A running-session link needs **Close session, then snooze** through the existing close selection UI. Preserve elapsed time and work notes; do not implicitly mark every session task worked. Cancelling that flow does neither operation. A planned-link-only fast path is preferable to quiet time-attribution damage. Batch snooze can follow later; if included, preview one time and a count, validate all targets, and write atomically.

### Definition marks

Extend the existing identity-slot decoration. Sleeping tasks replace the tomato with an outline clock and `until 14:30`. Use a subdued blue/violet tint with readable text, not disabled grey. Woken active tasks restore the warm tomato and add smaller `since 14:31` text. Preserve the existing unmarked-row spacing.

```text
⌗  ◷ until 14:30   Email Dan with interview updates
⌗  🍅 since 14:31  Email Dan with interview updates
⌗  🍅              Fix parser crash
```

These are wireframes, not literal CSS/glyph requirements. Use the established icon family, tabular digits, baseline alignment, and bounded width. Plain click retains cursor behavior; modifier-click or the keyboard jump opens the active/Snoozed row. Revalidate the target rather than trusting a cached line number.

Tooltip examples: “Snoozed in today's plan until 14:30” and “Woke at 14:31; set for 14:30; queued in WRITE.” Communicate through text and shape, not color alone. Preserve reduced motion, forced colors, and truthful-or-neutral source mapping. Existing daily-note and query rendering exclusions should only change when deliberately covered by the new display contract.

### Daily rows and Mac agenda

Sleeping rows show clock, scheduled time, title, and child notes; sort by time, stable for ties. A passed target is amber **Wake due**, not an indefinite spinning “waking” indicator. Known contention can say `Waiting for sync`; invalid rows name the repair.

After successful wake, show **Ready since 14:31** beside the normal rendered Task Link. Keep it after the notification disappears, app restarts, and ordinary same-day link moves. Show scheduled time in details. The time the user initially pressed Snooze is much less useful for choosing work now.

The Mac idle agenda gets a separately named Snoozed group, never a fake executable Pomodoro. Its collapsed form retains `3 snoozed · next 14:30`. Woken tasks appear in their ordinary upcoming entries with the same badge. The Mac renders state, times, copy, and refresh deadlines returned by Bob; it does not parse the vault or independently compute eligibility.

### Budget honesty

Example: **TODAY 7/10 · 3 snoozed**. Seven is counted active on-clock work; three is separate waiting work. Off-clock keeps its existing treatment. Expanded copy can explain the distinct planned-today total after deduplication.

If two on-clock tasks wake at 10/10, the meter becomes 12/10. Wake succeeds and the ordinary over-cap warning appears: `2 tasks ready · active links now 12/10`. Do not hold the tasks for capacity, evict other links, or reinterpret exemption as a reservation. This is the cost of the chosen preference, made visible rather than overridden.

Preserve the existing distinction between budget link occurrences and dedicated Today links. A snoozed-only row outside Pomodoros is exempt; an independent active occurrence inside Pomodoros can still count. Do not change all link-budget semantics as collateral work.

## Notifications: a brief interruption with lasting context

Do not implement the central promise solely through `desktop_notify::send_notification`: its best-effort AppleScript path and shared vault-sync opt-out provide insufficient control. Extend the signed Mac app's native `UNUserNotificationCenter` service and open-note actions.

Recommended delivery:

1. **Desktop:** one native banner per batch, one short sound by default with a separate mute preference. Title `Ready for today`; body `Email Dan · woke 14:31`. For several: `3 planned tasks are ready`, at most two names plus a remainder count. Main action opens the actual daily rows. **Snooze again…** opens the card rather than choosing a time automatically.
2. **Foreground Bob surface:** a compact top-edge ribbon for **12 seconds**, `◷ Email Dan is ready · since 14:31`, with **Show** and **Snooze…**. Pause dismissal while hovered or keyboard-focused. Never steal focus, open a modal, scroll the editor, alter a capture draft, or start a timer.
3. **After dismissal:** the daily badge and a small **Woken today** agenda filter/summary retain equivalent information and actions. Notification expiry must not remove the only way to act.

A native banner and an in-context ribbon are deliberate layered feedback. Only the designated desktop notifier emits system banners/sound; Obsidian does not send a second macOS system alert. Multiple Obsidian windows share delivery state and use the foreground window. Without the Mac app, the foreground Obsidian ribbon still works; background delivery should have an explicit configured owner, not every CLI/server process in the tailnet.

Group tasks woken in the same transaction; coalesce closely spaced events over roughly two seconds. On launch/unlock, produce one catch-up summary for relevant unannounced wakes from today. Do not replay yesterday, already-completed work, or every unchanged row at each poll. Snooze again or release invalidates stale actions and pending notices.

Each committed wake has a stable event ID. Keep local per-host/per-consumer delivery receipts. Fetching an event is not proof it was presented. Track submission/presentation where available; retry known submission failures with backoff and reuse a stable OS request identifier. A crash between submission and receipt recording can still duplicate a notice: promise idempotent placement and best-effort deduplicated delivery, not exactly-once human notification. Notification failure never rolls back a successful wake.

Use one configured notification-owning Mac initially. Other hosts may publish committed wake receipts without all ringing. No distributed leader-election service is needed. A local filesystem lock does not coordinate independent synced checkouts; document that boundary.

Use normal notification priority initially. Apple distinguishes normal Active delivery from Time Sensitive delivery that can bypass Focus, and advises matching interruption level to real urgency. Consider an explicit future opt-in for snooze reminders through Focus where supported; never use Critical alarms here. [Apple notification guidance](https://developer.apple.com/design/human-interface-guidelines/managing-notifications?changes=la&language=objc).

**Honest limit:** a denied permission, Focus, a stopped app, or a sleeping computer can prevent immediate visibility. Native banner duration follows OS/user settings; only the app-owned ribbon promises its own 12-second lifetime. Show notification health in settings and in the first snooze preview when unavailable, without blocking the queue action. Do not pre-schedule a “ready” banner solely from target time: eligibility and successful placement must come first.

Durable context also makes auto-dismissal accessible. W3C's timing guidance explicitly discusses transient toasts with equivalent information/actions available elsewhere. Announce foreground batches through a polite status live region, without focus theft or continuously re-announcing elapsed time. [W3C Timing Adjustable](https://www.w3.org/WAI/WCAG22/Understanding/timing-adjustable.html), [W3C Status Messages](https://www.w3.org/WAI/WCAG22/Understanding/status-messages.html).

## Storage and reliable transition

### Preserve the simple queue and canonical active link

Keep the earlier proposal's hand-writable form:

```markdown
## Pomodoros

- [ ] () — WRITE
    - [[job#^other-task]]

## Snoozed

- **1430** [[job#^email-dan]]
    - Mention the new interview timeline.
```

Only direct top-level timed rows in Snoozed qualify. Require one plain unstruck block link, a valid same-day time, and a resolved eligible non-Event task. Accept hand-written `HH:MM`, normalize on supported write. Authored children travel as a subtree; they are not additional snooze targets. Fences, malformed times, prose, extra links, and nested examples never execute. Diagnose duplicate/malformed sections rather than guessing a destructive merge.

Register Snoozed as a structural H2 so it is not offered as a drawer route. Keep it after Pomodoros: the existing ledger ends at the next H2, and Events placement remains unchanged.

After successful wake at 14:31:

```markdown
## Pomodoros

- [ ] () — WRITE
    - [[job#^other-task]]
    - [[job#^email-dan]]
        - ⏰ Woke **1431** · set for **1430** <!-- bob-snooze:v1 id=EXAMPLE -->
        - Mention the new interview timeline.

## Snoozed
```

**Keep the active link line canonical.** Do not prefix it with a time or append arbitrary prose: `list_queued_links`, Today, close selection, and other readers rely on dedicated-link recognition. A pretty raw prefix can make one surface lose the task while another still counts it.

The reserved child receipt is a **proposed new contract**, not existing syntax. The example abbreviates metadata. Specify a versioned grammar with event ID, requested wake instant, actual committed wake instant, and automatic/manual cause. Absolute instants in the receipt support ordering and deduplication; readable local HHMM stays in prose. The hand-written queue itself needs neither a UUID nor full timestamp. Generate the receipt within the wake transaction.

Supported views render this child as the parent's ready-since badge without duplicating prose. Plain Markdown retains a useful explanation. Keep it on the daily link subtree, not the task definition or a separate authoritative task-state database. Closed/history rendering says `Woke 14:31`, not “ready.” Same-day active moves preserve it; a new snooze cycle replaces the live-cycle presentation on its next wake. Preserve authored children.

Classify the reserved child explicitly so it is not treated as a Work Log, task requirement, drawer, extra Task Link, or user note in summaries/previews. This focused integration is safer than widening every dedicated-link parser.

### One guarded writer

A wake attempt should:

1. Compute Bob's date/time once and read today's note. Return cheaply when no row is due.
2. Acquire the existing mutation guard only when needed; re-read/snapshot the daily and relevant task/blocker inputs. Revalidate the day immediately before commit.
3. Resolve canonical `(vault-relative path, block ID)` identities. Refuse ambiguity and Event Tasks; check effective blockers, terminal/hidden eligibility under existing link policy, and active duplicates.
4. Choose an **untimed** exact-type entry, then an untimed containing-type entry, then a new typed placeholder. Preserve naming agreement. Never append automatically to the running session.
5. Move the authored subtree, add canonical link and receipt, and remove the source in one daily-note write. If a hand-written Ready row needs Ensure Next, use the existing checked multi-file transaction for that task-line change.
6. Commit before exposing the wake event. A read-only projection can say `due`; only committed placement can say `ready` and notify.

Supported release/close/blocking writers should already remove pending snoozes. If a hand edit leaves a blocked/closed contradiction, retire the queued instruction with a visible explanation and preserve notes. Missing/ambiguous targets remain repair rows. Temporary I/O or edit/sync contention leaves the due row intact for retry. An already-active duplicate gets no fresh ready event; preserve/merge its notes safely and report the redundancy.

Do not call a capture path that drops prerequisites or pulls a future schedule forward merely because it can create a link. Automatic wake fulfills an earlier choice; it is not a new human override. It never stamps `[fresh::]`, increments/clears keeps as a review action, writes `[unblocked::]` because a clock expired, or creates successor offers. Normal Ensure Next behavior for explicitly planned hand-written work is separate from freshness confirmation.

### Timing and recovery

Use Bob's existing configured timezone/date policy. Resolve relative input in the commit preview, require a future target, and reject cross-midnight times with a clear schedule-another-day alternative. All wake-capable hosts must agree on Bob's zone; host-local fallback needs particular care.

Reject nonexistent daylight-saving times rather than normalizing silently. For ambiguous repeated times, require a disambiguated UI choice or diagnose a hand-written row. Same-day scope does not eliminate these cases. Backwards clock movement cannot undo a completed wake because its source row is gone. Forward movement makes rows due; report actual placement. Inject one clock in tests.

Keep a cheap tick step for unattended recovery. Running clients also schedule refresh/wake at Bob's `next_due_at`, and retry transient deferrals on a short bounded cadence, e.g. 15–30 seconds with backoff. Revalidate on launch, resume, unlock, focus, timezone/clock changes, and relevant vault events. Reuse Mac boundary/lifecycle patterns; clients invoke Bob and do not write vault files themselves.

The normal target is placement within seconds while a client is awake and the vault writable. Measure it; do not claim a hard guarantee. Tick-only latency includes polling, contention, and suspension. `tick/lock.rs` skips overlapping noninteractive runs and step ceilings can be much longer than one minute. Old observations of short typical runs do not establish a universal ten-minute upper bound.

A direct client wake can operate outside whole-tick orchestration while still respecting shared vault mutation and maintenance locks. Never bypass those safety locks for speed. Prove the concurrency behavior with tests.

### Cleanup and midnight

Extend both Rust and plugin cleanup by resolved identity to include Snoozed. Otherwise release, complete, cancel, future schedule, dependency changes, and relevant decay/roll actions can leave a timer instruction that resurrects the task. This parity must ship with authoring, not later.

Preserve existing rules: retain child notes, remove only entries actually emptied by the operation, and retain closed recorded sessions. Task moves/renames need queue/receipt coverage even where whole-note link rewrites help. A merge or split must not accidentally replicate one wake instruction across several tasks. Never use line numbers as durable identity.

At midnight, yesterday's rows cease to execute or suppress review. Do not auto-carry or create today's plan. A quiet “Yesterday: 2 snoozes did not wake” summary may offer explicit re-plan actions. A transaction racing midnight either commits under the old day's still-valid conditions or defers without manufacturing a new-day promise.

## Implementation boundaries and acceptance

`bob snooze` remains a reasonable daily-queue command family. Bare/list is read-only; verbs cover add/change, wake, and remove, with due-batch versus explicit early-wake semantics documented. Follow existing dry-run, JSON, help, and public short-option conventions. Do not add subcommands under `bob capture`.

If capture authoring ships, keep `z:<when>`, e.g. `@job:email-dan z:1430`; `s:1430` means a day offset today. Bob produces the same preview/guards as the card. A bare link to a sleeping task may mean explicit early wake only when preview makes that clear and no duplicate timer remains.

Additive JSON should carry canonical identity, queue state, scheduled time, next refresh, committed wake receipt, outcome/reason, and budget breakdown. Unsupported capability differs from an empty queue. The Mac must remain a renderer/client of Bob's semantics.

Implement in coherent slices, with no half-integrated authoring release:

1. Contract/core: parsing, state, checked move, receipts, cleanup parity, budget/review rules, failure/time vectors.
2. Interaction: marks, badge, command/card, agenda, capability fallback.
3. Delivery/recovery: native categories/actions, foreground ribbon, local delivery receipts, boundary triggers, tick fallback, sleep/restart validation.

Reader support and cleanup parity precede enabling authoring. Coordinate CLI/plugin/Mac versions through the existing release train. Plugin implementation requires normal build/validation and `bob plugins sync`; native changes require actual macOS compilation and exact-SHA CI, not portable Swift checks alone.

These are future acceptance tests, not checks claimed to have run:

| Area | Required behavior |
| --- | --- |
| Exact boundary | Sleeping before target, due at target, ready only after successful move. |
| Definition display | Clock before wake, tomato afterward; stale cache/duplicate IDs do not lie. |
| Budget | Snoozed-only zero; active wake counts; off-clock exemption preserved; active duplicate wins. |
| Capacity | Wake over cap succeeds and surfaces overage without hidden waiting. |
| Events | Synced and hand-written Event Tasks are refused through all target spellings/routes. |
| Running session | No automatic insertion; later plain close cannot falsely claim newly woken work. |
| Snooze action | All planned occurrences handled atomically; running/history context and notes preserved. |
| Cleanup | Release/close/cancel/schedule/dependency/decay cannot leave a reviving timer. |
| Blocker race | Changed prerequisites prevent wake; automation never removes them. |
| Parser | Fences, malformed times, extra links, duplicate sections, and nested examples never execute. |
| Identity | Alias/path deduplication, rename/move, stale line references, ambiguous IDs handled safely. |
| Crash | Failure before/after write boundaries cannot lose/duplicate placement; committed receipt recovers missed notice. |
| Concurrency | Tick/native/plugin race gives one placement and no overwritten edits; locks cause bounded retries. |
| Notification | One OS sound/banner per batch; ribbon expires; equivalent information/actions remain. |
| Permissions | Denied notifications, Focus, hidden/stopped clients have honest degraded behavior. |
| Restart | Same-day unannounced wakes summarized once; completed/re-snoozed work not announced stale. |
| Time | Midnight, sleep past target, clock jumps, zone mismatch, DST gap/fold; no auto-carry. |
| Provenance | Moves preserve receipt; history says Woke; metadata never masquerades as work/requirements. |
| Accessibility | One polite batch announcement, no focus theft, keyboard alternatives, reduced motion/high contrast. |
| Compatibility | Old clients report unsupported; supported mixed versions cannot work sleeping tasks early. |

Measure wake lateness and placement-to-notice delay while sync/scans are active. Also verify quietness: no repeated notice for an unchanged ready-since badge. The usability question is “can Bryan immediately tell why this task is here and when it returned?”, not merely “did the timer callback fire?”

## Proposed glossary term

**Snoozed Task**  
*Aliases: snoozed task link, later-today task*

> An open, non-Event Task deliberately kept on today's plan but set aside until a chosen time later today. Its Task Link waits in the daily note's `## Snoozed` section, with a wake time and any attached notes. While there, it shows a clock instead of the active Today tomato, is omitted from today's routine review walk, and does not count against `plan.max_links`.
>
> When the time arrives, Bob checks the task again and, if eligible, moves its link and notes into an untimed open Pomodoro. It then becomes active Today, counts under the normal link-budget rules, and shows when it actually woke. A brief notification announces the return; waking never starts work or confirms freshness. A passed wake time awaiting a safe write is **wake due**, not yet active.
>
> Snoozing does not make a task Blocked or create a new lane. It differs from a future scheduled date, a reminder with no effect on today's queue, a successor offer, a hidden task, and an Event Task. An unwoken snooze does not carry itself into tomorrow.

Publish as `glossary:snoozed-task` with links to Task Link, Event Task, Pomodoro, Task Freshness, and successor terminology when the implemented contract is settled. Point to one feature guide for syntax. Do not accidentally redefine other existing reference-library/project uses of “snooze.”

## Recommended solution

**Implement the separate same-day queue, active-only budget, and durable wake provenance.** Keep the original proposal's simple timed Markdown rows, after-Pomodoros position, guarded subtree move, sticky lanes, and no-auto-carry rule. Make Event Task exclusion a hard invariant. Add a fast Snooze until card for planned links, an explicit close-first path for running links, and clock/time definition marks.

Show **until 14:30** while sleeping and **Ready since 14:31** only after successful placement; keep intended time in details. Preserve canonical active-link syntax and place the small versioned receipt beneath it. Use native grouped notifications with one optional sound, reinforce them with a 12-second foreground ribbon, and retain discoverable wake information after dismissal. Boundary-triggered attempts provide promptness; tick provides recovery; all routes share Bob's guarded writer.

This feature is worthwhile when it reduces work visible now without weakening trust in work planned for later. Prioritize correct cleanup, truthful timing, preserved notes/time, and a visible return before adding more syntax or smarter scheduling.
