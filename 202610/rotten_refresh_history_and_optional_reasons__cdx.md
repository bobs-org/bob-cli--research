# Rotten Log: durable history for deliberate rotten-task keeps

Independent research by **cdx**, 2026-10-23. Research and design recommendation; no product code, live-vault behavior, or canonical glossary was changed.

The useful addition is a task-local record of **“I reviewed this expired task and kept it”**, with an optional explanation. It should preserve history after the current keep streak resets. I recommend building it, with a narrower and more explicit event definition than “every manual refresh.” The main requirement adjustment is essential: **the explanation may be optional; recording an eligible refresh must not be optional if the count is meant to be trustworthy.**

**Research basis and limits.** I independently inspected bob-cli at `f2c24531b5796878af1bff47d984bccababec6bf` and bob-plugins at `477af35548282f52cf6872d15e06668a4597767f`, read the relevant memory through audited commands, examined existing tests, and ran focused plugin tests. I did not consult any other report or findings from this research swarm. Product behavior below is grounded in those source snapshots, not a live Obsidian session or a census of Bryan's actual refresh frequency. External sources provide limited workflow and API context; they do not establish that this feature will improve productivity.

**What already exists.**

- Task Freshness is the most recent human confirmation date, `[fresh:: YYYY-MM-DD]`. Many meaningful human edits stamp it; automation generally does not. Consequently, a freshness date alone cannot say which gesture happened or why. [C1]
- `[keeps:: N]` is a consecutive due-Ready keep streak, not a lifetime count. Explicit keeps preserve or increment it; other human stamps clear it. The sole increment helper independently guards against NEW and same-day inflation and caps the streak at 999. Unblock ticklers preserve the streak. [C2]
- Freshness marks already display keep pips and a tooltip saying how many reviews in a row the task was kept. Adding another undifferentiated counter would make two different measures look interchangeable. [C3]
- Alt+F and Ctrl+Alt+F already prompt Pending tasks for an optional Work Log summary. Blank Enter refreshes without a Work Log entry; Escape cancels the operation. Counted and Task Link sessions share one summary among qualifying Pending targets. The normal source-note path plans the stamp and child-log insertion together, then applies one editor transaction. [C1, C4, C5]
- At the configured keep threshold, the next due qualifying keep opens the existing decay decision card. Its choices include Not now, Less often, Reword, Drop, and Keep. The Keep branch currently rewrites only the task line; it will need the new combined task-and-log writer. Counted and Task Link sessions skip targets needing this decision rather than opening a card for every target. [C4, C6]
- A review-answer journal already exists. Its event builder records day, tier, outcome, and row key; the sender adds plugin identity. Normal keep journaling is scoped through a review landing, and journal errors are handled separately from the successful task write. It is valuable for review statistics, but it is not an existing complete task-local history with explanations. [C7]

There is an explicit prior decision to revisit. `decisions:rotten-keeps-use-priority-decay` rejected both a lifetime counter and a new REVIEW LOG, because the original feature needed a streak to trigger an approved decision. Bryan's new request supplies a different purpose: durable explanations and recorded history. Preserve that decision's streak, consent, and freshness rules; supersede only its no-new-log choice if this design is accepted. Do not silently reinterpret `keeps` or derive historical events from old stamps.

Some memory descriptions still mention the older REFERENCES tier. The inspected current documentation and code instead include RECURRING and put references through ordinary task rules. Implement against the current evaluator and explicit eligibility, not an old hard-coded tier roster. [C1, C4]

**Is this a good idea?**

Yes, as an aid to the next decision. Seeing the last two explanations can reveal that a task has repeatedly survived for the same weak reason, that its wording is wrong, or that its review interval is inappropriate. The information remains useful when work, scheduling, or rewriting resets the keep streak. A log beside the task travels with its context and is readable without a statistics dashboard.

The risk is making review into documentation work. An optional text box still adds an interruption and a confirmation keystroke. For illustration, 15 qualifying tasks at an assumed additional 4 seconds each add a minute; neither number is a measurement of Bryan's workflow. A mandatory reason would encourage boilerplate and make omission feel like an error. A large lifetime count can also be misleading: a seven-day review interval naturally creates more events than a thirty-day interval, and a task may have been substantially reworded while retaining its history.

The official GTD review guidance emphasizes checking action lists, identifying follow-ups, and ensuring projects have current actions. It does not prescribe a reason ledger for every retained item. My inference is that this log earns its place only if it helps choose the next action without consuming the review. Keep the input short and optional, expose recent history, and retain the existing options to defer, reduce review frequency, reword, or drop. [Guided GTD Weekly Review](https://gettingthingsdone.com/2015/07/podcast-07-guided-gtd-weekly-review/)

Use neutral input copy such as **“What makes this worth keeping? (optional)”** or **“Why keep this task? (optional)”**. Avoid “Why haven't you done this?” The prompt should invite decision context, not an account of personal failure. An explanation is also not proof that work was performed, so it must not enter Work Log statistics.

**Requirement adjustments I recommend.**

| Adjustment | Reason |
| --- | --- |
| Always record a successful qualifying keep; make only its reason optional. | Blank submissions must not make the count understate recorded refreshes. This intentionally differs from Work Log blank-input semantics. |
| Define “rotten” as the current evaluator's expired Ready ROTTEN task, with ordinary `rotten` review tier. | The dashboard's rotten bucket also contains ticklers. Project-review rows can have an underlying expired state without being ordinary rotten upkeep. Neither should be included accidentally. |
| Record deliberate keeps from Alt+F/Ctrl+Alt+F and equivalent command routes, including the decay card's Keep choice. | Do not conflate work, rescheduling, task creation, automatic recovery, and confirmation. The UI should say “recorded rotten keeps,” not “all refreshes.” |
| Keep the current stay/advance rules and perform all writes before advancing. | The log is an extension of the answer, not a second answer or a navigation event. |
| Derive the displayed count from retained log events; add no authoritative counter field. | Prevent drift between a number and its explanation history. Keep the independent streak unchanged. |
| Start recording at rollout; never backfill from `fresh`, `keeps`, Git guesses, or the review journal. | The available data does not prove when, why, or by which gesture all past refreshes occurred. |
| Treat this as an editable history, not a tamper-proof audit system. | The vault owner can edit or delete Markdown, undo an action, and resolve sync conflicts. The count describes retained recorded events. |

The strict ROTTEN scope is a recommendation, not an assumption that Bryan meant to exclude ticklers. If the actual desired scope is all deliberate review confirmations, choose a broader **Refresh Log** or **Review Log** vocabulary and explicitly include those event classes. Do not ship a “Rotten Log” that silently counts every due lane review or every freshness stamp.

**Proposed event and interaction contract.**

A qualifying event requires all of the following: a user invokes the explicit refresh/keep route; the exact source task is currently eligible as an expired Ready task in ordinary ROTTEN review; the user confirms; and the combined write changes its confirmation to the current local day successfully. Eligibility is evaluated **before** stamping. After stamping, the task is no longer rotten.

Use the shared evaluator and source identity, not `bucket === "rotten"`, a file named `rotten.md`, stale rendered text, or the mere presence of `[keeps::]`. The existing exact queue matcher is a useful first guard. If the queue and source disagree, re-resolve against current inputs or refuse with a retry notice; do not confidently report that an unverified eligible keep was logged. Pending, Next, trackers, recurring tasks, checklist rows, and unblock ticklers have other semantics. [C1, C2, C4]

| Situation | Prompt / Rotten Log result |
| --- | --- |
| Exact ordinary Ready ROTTEN task; Alt+F | Optional reason; one event plus refresh; remain on task. |
| Same task; Ctrl+Alt+F | Same commit; then existing refresh-and-advance behavior, exactly once. |
| Same qualifying task outside the morning review | Same logging. Time of day and being a walk landing are not eligibility requirements. |
| Empty or whitespace-only reason, then Enter | Refresh and record a dated event explicitly saying no reason was provided. |
| Escape, close, or Cancel | No stamp, event, streak change, answer-journal event, or advance. |
| Repeated key event, double submit, or a task already fresh today | No second Rotten Log event. A same-day keep is not a second expiry cycle. |
| NEW or an ordinary still-fresh task | Existing refresh semantics; no Rotten Log prompt/event. |
| Scheduled or unblock TICKLER | Existing tickler semantics; no Rotten Log prompt/event under this proposal. |
| Pending (`[/]`) | Existing optional Work Log prompt and blank behavior; no Rotten Log. |
| Next, PROJECTS, PRE/POST, or RECURRING | Existing respective behavior; no Rotten Log. An ordinary reference task may qualify if it actually evaluates into ROTTEN. |
| At-limit ROTTEN task opens decay card | No event merely for opening the card. Keep commits one event; other choices retain their own existing logs. |
| Counted or Task Link refresh | One prompt for the accepted rotten subset; one event per unique qualifying source task; no event for skipped targets. |
| Capture edits, reschedule, completion, recovery, seed, sync | No Rotten Log event. A generic freshness stamp is insufficient. |

The log count must **not** depend on whether `keeps` numerically increased: the streak saturates at 999, while an accepted future rotten keep is still a real event. Conversely, a keep increment for a scheduled tickler must not create a Rotten Log event under the narrow definition.

Below the decay threshold, reuse the existing refresh modal's structure, with task text, optional reason, a preview of the exact dated row, and Enter/Escape behavior. Display the current recorded count and latest reason so the new decision can benefit from history. Do not prefill the old reason: that would encourage accidental reuse as if it were a new explanation.

At the threshold, preserve the existing decision card first. Add the optional reason input to its Keep action/stage so the user sees one coherent decision flow. It must write nothing until Keep is approved. Do not put a generic Rotten Log prompt before a card that may then defer or drop the task. Reword, Less often, and Not now may stamp, but are substantive changes rather than bare keeps and remain outside this log's count. If collecting a reason requires a Keep-specific stage, that stage should use the same modal shell, not a second unrelated popup.

For mixed batches, show separate optional fields for **Work summary** on Pending targets and **Keep reason** on qualifying rotten targets, with each target count visible. A Work summary must never be copied into a Rotten Log, or vice versa. One shared keep reason may apply to all listed rotten targets after explicit confirmation; users wanting distinct reasons review them individually. Preserve existing decision-required skips and deduplicate multiple links to one source task before planning. [C4, C5]

**Storage and visual design.**

Use one task-owned direct-child marker, with newest-first dated child events, mirroring the Work Log's ownership and indentation conventions. Proposed canonical representation:

```markdown
- [ ] #task Review the backup restore procedure [fresh:: 2026-10-23] [keeps:: 2] ^restore-review
    - ♻️ **ROTTEN LOG**
        - *2026-10-23* — Kept — Still the next useful step; check during the next maintenance window.
        - *2026-10-16* — Kept — No reason provided.
```

The icon is a proposed visual choice; the bold label and a documented grammar should carry identity. Explicit “Kept” gives a fixed event action separate from arbitrary reason text. Store the actual local review date, not the previous fresh date. Date precision is sufficient because freshness and eligibility operate on calendar days; introduce a timestamp with timezone only if there is a real requirement for multiple distinguishable events per day. No task-ID minting is necessary solely to attach a direct child to an existing task.

Count valid dated direct-child events of the managed marker. Nested explanation bullets, arbitrary prose, task children belonging to another task, and text mentioning the words ROTTEN LOG do not count. Reuse established handling for list markers, tabs/spaces, CRLF, optional matching emoji, and strict parent ownership. Define duplicate/malformed marker handling: do not silently merge or delete history; a writer should refuse ambiguous ownership with a useful notice, while a reader should avoid claiming an exact count from ambiguous content.

Keep the marker text stable. Do **not** persist `ROTTEN LOG (3)` in Markdown: existing managed-marker grammars reject trailing text, and the duplicated total would need repair. [C8]

The visual minimum should be more than a buried expanded list:

- Render a compact, neutral count near the task's existing freshness mark, for example `↻ 2`, with accessible text **“2 recorded rotten keeps.”** Keep pips retain their existing consecutive-streak meaning. Do not add red severity based on the historical total.
- Its tooltip gives the last date and reason, with separate labels for recorded keeps and current streak. Activating the history affordance reveals the task's log; do not change the existing freshness mark's raw-field-editing action.
- In the source note, the log is an ordinary foldable child block. The rendered header may show a derived count without writing it into the source. Retain history when the task becomes fresh, Next, Pending, completed, moved, or archived with its child block.

Compute a small per-task summary from the source note and cache it per file revision/editor revision. Do not rescan the whole vault for every mark or keystroke. Rendered Tasks rows and transclusions should use existing source-resolution guards; if the source is unresolved, omit the count or show unavailable instead of inventing zero. The count is the number of retained valid events since this feature started, not a proven lifetime total. Editing or removing a log row changes that count; undo restores both line and history.

A first implementation can keep richer history display in Obsidian while preserving it as ordinary Markdown elsewhere. Do not accidentally label these entries as work, counted work sessions, or schedule changes in CLI snapshots or Mac previews.

**Implementation seams and engineering risks.**

The primary implementation belongs in **bob-plugins**, not in a new CLI command and not in the live vault's copied plugin files. The change is larger than adding a modal because log ownership, alternate refresh routes, and reader behavior all matter.

| Area | Concrete work |
| --- | --- |
| Refresh orchestration | Extend `520-plugin-lane-links-and-review.js` and the Task Link route in `530-plugin-freshness-refresh-and-decay.js` with a distinct pre-write rotten-event eligibility result. Do not reuse `counted` as the new predicate. |
| Pure planner | Evolve `planFreshStampBatchWithWorkLogs` in `480-review-jump-and-nav-api.js` into a planner accepting typed Work Log and Rotten Log inputs. Stamp first in the planned document, insert log rows bottom-up, and return source preimages plus log-write counts. |
| Log parser/writer | Add an explicit Rotten kind around `030-bullet-blocks-and-logs.js` and the existing `220-property-targets.js` insertion conventions. Reuse structural parsing without giving Rotten Log Work Log blank-input semantics. |
| Modal | Generalize `FreshnessRefreshSummaryModal` in `190-summary-modals.js` to explicit field kinds and previews. Extend the decay Keep stage without changing default card actions. |
| Decay Keep and fallback | Replace the line-only write in `540-plugin-decay-picker-and-cancel.js::applyFreshnessDecayCardKeep` with the combined planner. Cover the card-unavailable fallback in the source refresh route too; it currently bypasses the Work Log planner. |
| Read models and marks | Add source-derived count/latest-entry metadata and a distinct history affordance alongside existing freshness marks. Audit Live Preview, reading view, and resolved task-query/transclusion surfaces. |
| bob-cli readers | Review `ManagedTaskLogKind` and its consumers before adding a new marker kind. Capture insertion anchors, task-section suggestions, agenda display, and highlight/note snapshot log folding all currently know Schedule/Work explicitly. [C8, C9] |
| Documentation and memory | Update freshness and plugin behavior documentation; add the requested glossary entry when behavior is implemented. A new accepted decision should narrowly supersede the old no-review-log rejection if approved; do not rewrite accepted policy silently. |

For a source note, capture its preimage, task identity, local day, and eligibility inputs before the prompt. Revalidate them, including the task's child block, after the asynchronous prompt. A tab switch, midnight rollover, changed note configuration, stale task cache, task deletion, or concurrent edit must not attach a reason to a different target. Plan `[fresh]`, the existing keep semantics, and the new log as one postimage and commit one editor transaction/undo step. If logging cannot be planned or committed, refuse the eligible keep rather than silently produce an incomplete audit.

For linked files, reuse the existing grouped commit machinery and keep each task's stamp plus log in the same file write. Its source shows preimage validation and best-effort rollback; do not advertise a global crash-safe transaction across several notes. A mid-batch failure needs honest partial-write handling, and successful notes must not gain duplicate events on retry. [C10]

Obsidian's documented `Vault.process()` reads and writes a file under a single guarded operation and supports checking the preimage after asynchronous work. That is appropriate for unloaded source notes through the existing writer abstraction; active editors need their existing editor transaction path. It is not a promise of atomicity across an entire vault or several devices. [Obsidian Vault API](https://docs.obsidian.md/Plugins/Vault)

Do not put child-log writes inside `freshness.keepLine`. That helper is intentionally a pure single-line transformation shared with existing counting semantics. Keep event planning above it, where note content and user consent are available.

Adding a Rust managed-log enum variant exposes exhaustive consumers. Decide each one deliberately: for v1, recognize/protect Rotten Log as managed history, preserve its plain Markdown where shown, and keep it out of work/schedule totals and capture section suggestions. A dedicated `rotten` agenda JSON category or Mac-specific history widget would be a separate coordinated contract change; inspect the linked Mac client through `sase_repo` if that scope is selected. It is unnecessary for the requested keymap workflow. Do not add new wire values casually just because an internal enum gained a variant.

**Alternatives considered.**

| Approach | Assessment |
| --- | --- |
| Keep existing streak and pips only | Lowest cost, but loses explanations and cannot retain counts across streak resets. Does not meet the request. |
| Optional nonblank Rotten Log entries, exactly like Work Log | Useful notes but an incomplete event history. Acceptable only if the UI explicitly counts notes, not refreshes. |
| A lifetime `[refresh_count:: N]` field | Cheap to render, but provides no dates/reasons and duplicates information once a log exists. Avoid. |
| Put review reasons in Work Log | Reuses UI and storage, but conflates confirmation with actual work and may affect work-related displays or metrics. Avoid. |
| Use the central review journal as the only history | It already serves statistics, but the observed event model has no reasons and normal refresh journaling depends on the landing flow. Expanding it creates identity, retention, projection, and consistency work for a task-local request. Avoid as v1's source of truth. |
| Log every human freshness stamp | A broader activity history could be useful, but requires reason/event taxonomy across many writers and no longer answers only “how often did I keep this rotten task?” Defer. |
| Prompt only at the keep threshold | Good fallback if frequent prompting becomes burdensome, especially because a decision card already exists. It does not satisfy the initial requested per-rotten-refresh prompt, so do not silently substitute it. |

If review becomes noticeably slower, keep automatic dated events but reduce when the reason field interrupts—for example, only on threshold decisions, with an explicit way to add a reason otherwise. Evaluate this after real use rather than adding a configuration matrix immediately. The test of success is whether the history helps alter decisions, not how much text it accumulates.

**Proposed glossary entry, ready to publish with the feature.**

Target: `sase/memory/glossary/rotten-log.md`; title **Rotten Log**; optional alias **rotten keep history**. The requested glossary addition is supported by the current research prompt. Its text should describe implemented behavior, so this report supplies the draft rather than prematurely publishing it as current behavior.

> A task-local history of explicit keeps of an expired Ready task in the ROTTEN review tier, stored as a `♻️ **ROTTEN LOG**` direct child with newest-first dated entries. Alt+F refreshes in place and Ctrl+Alt+F uses the same commit before continuing the review; both offer an optional keep reason, including the decay card's Keep choice. Blank Enter still records the keep; Escape changes nothing. Each successful qualifying keep records once, while same-day repeats, ticklers, other lane reviews, substantive edits, and automation do not. Its displayed count comes from retained log entries and survives resets of the [[keep-streak]]. It records confirmation, not work performed in a [[work-log]], and does not itself change the task's lane, schedule, priority, or [[task-freshness]] rules.

If scope is broadened to ticklers, update both the name/definition and the eligibility matrix before implementation; the definition must not hide that product choice.

**Validation performed and acceptance evidence needed.**

I ran these existing suites in bob-plugins on the inspected, unchanged tree:

```text
node --test --test-reporter=tap \
  scripts/test-navigation-refresh-modal.cjs \
  scripts/test-navigation-freshness.cjs \
  scripts/test-navigation-keep-counting.cjs \
  scripts/test-navigation-decision-card-handlers.cjs \
  scripts/test-navigation-review-advance.cjs \
  scripts/test-navigation-review-journal.cjs \
  scripts/test-ledger-tools-freshness-keeps.cjs
```

Result: **239 tests, 238 pass, 1 fail**. The failure, `Keep counts once and saturates at 999 without reset`, reproduces in isolation on the unchanged tree. Its stamp and keep-count assertions pass; its last-notice assertion instead sees the subsequent missing-review-statistics-API notice. This is already tracked by `bead:bob-cli-6w`; I added independent corroboration, with durable reproduction evidence `file:explicit:4ad894f8d3cfa300fad12869`. No new implementation was tested, and no claim of full baseline green is made.

For implementation, prioritize tests that distinguish product semantics:

1. Successful ROTTEN keep with a reason; blank reason still records; Escape leaves the entire document and walk untouched; same-day repeat and double submit do not duplicate.
2. Strict ROTTEN versus scheduled/unblock ticklers, NEW, Pending, Next, project review, recurring/checklist rows, and ordinary reference tasks. Include a saturated keep streak to prove log eligibility is independent of a numeric increment.
3. At-limit Keep records once; opening/cancelling the card does not; other outcomes use existing logs; compatibility fallback cannot bypass the audit writer.
4. Mixed Pending/ROTTEN batches use the correct fields; duplicate Task Links deduplicate; decision-required rows remain due and unlogged; grouped-write failure and retries preserve per-task consistency.
5. Parent ownership, nested tasks/log-like text, indentation, CRLF, missing final newline, malformed/duplicate markers, Markdown reasons, and ordinary captured notes placed around logs.
6. Active document/child block/configuration/day changes during the prompt cause no stale commit; insertion line shifts preserve the correct walk successor; Undo restores the line, streak, and log together.
7. History remains after a generic human stamp clears `keeps`; it survives task moves; reading surfaces omit unavailable counts honestly and never contribute to Work Log totals.
8. Live Obsidian checks cover keyboard focus, IME composition, Escape and Enter, one undo step, fold behavior, accessible count labels, and Ctrl+Alt+F navigation after inserted lines. Existing Node stubs cannot establish those UI guarantees.

Build generated plugin entrypoints from source fragments, run the repository's build/validation and relevant tests, then use `bob plugins sync` when implementing. The research made no plugin changes and did not deploy anything.

**Source map.** Links pin locally inspected source, not peer reports. Memory decisions and glossary strands were read through `sase memory read`.

- [C1 — bob-cli freshness contract, including Pending Work Log prompt and current review tiers](https://github.com/bobs-org/bob-cli/blob/f2c24531b5796878af1bff47d984bccababec6bf/docs/freshness.md).
- [C2 — sole keep helper and same-day/unblocked guards](https://github.com/bobs-org/bob-plugins/blob/477af35548282f52cf6872d15e06668a4597767f/plugins/bob-ledger-tools/src/080-freshness-placement.js#L677).
- [C3 — freshness mark model, streak tooltip, and pips](https://github.com/bobs-org/bob-plugins/blob/477af35548282f52cf6872d15e06668a4597767f/plugins/bob-ledger-tools/src/130-freshness-marks.js#L559).
- [C4 — refresh orchestration, prompt, decision interception, and fallback](https://github.com/bobs-org/bob-plugins/blob/477af35548282f52cf6872d15e06668a4597767f/plugins/bob-navigation-hotkeys/src/520-plugin-lane-links-and-review.js#L293); [Task Link path](https://github.com/bobs-org/bob-plugins/blob/477af35548282f52cf6872d15e06668a4597767f/plugins/bob-navigation-hotkeys/src/530-plugin-freshness-refresh-and-decay.js#L3).
- [C5 — combined freshness and Work Log planner](https://github.com/bobs-org/bob-plugins/blob/477af35548282f52cf6872d15e06668a4597767f/plugins/bob-navigation-hotkeys/src/480-review-jump-and-nav-api.js#L600); [existing refresh summary modal](https://github.com/bobs-org/bob-plugins/blob/477af35548282f52cf6872d15e06668a4597767f/plugins/bob-navigation-hotkeys/src/190-summary-modals.js#L662).
- [C6 — decay Keep's current single-line writer](https://github.com/bobs-org/bob-plugins/blob/477af35548282f52cf6872d15e06668a4597767f/plugins/bob-navigation-hotkeys/src/540-plugin-decay-picker-and-cancel.js#L202); [card revalidation and action dispatch](https://github.com/bobs-org/bob-plugins/blob/477af35548282f52cf6872d15e06668a4597767f/plugins/bob-navigation-hotkeys/src/530-plugin-freshness-refresh-and-decay.js#L512).
- [C7 — review-answer journal event model and failure handling](https://github.com/bobs-org/bob-plugins/blob/477af35548282f52cf6872d15e06668a4597767f/plugins/bob-navigation-hotkeys/src/545-plugin-review-journal.js); [normal keep journal trigger](https://github.com/bobs-org/bob-plugins/blob/477af35548282f52cf6872d15e06668a4597767f/plugins/bob-navigation-hotkeys/src/530-plugin-freshness-refresh-and-decay.js#L225).
- [C8 — Rust managed-log marker grammar and insertion anchors](https://github.com/bobs-org/bob-cli/blob/f2c24531b5796878af1bff47d984bccababec6bf/src/native/capture/sub_bullet.rs#L274); [plugin managed-log grammar](https://github.com/bobs-org/bob-plugins/blob/477af35548282f52cf6872d15e06668a4597767f/plugins/bob-navigation-hotkeys/src/030-bullet-blocks-and-logs.js#L118).
- [C9 — capture section exclusions](https://github.com/bobs-org/bob-cli/blob/f2c24531b5796878af1bff47d984bccababec6bf/src/native/capture_task_sections.rs#L55); [agenda Work/Schedule enum](https://github.com/bobs-org/bob-cli/blob/f2c24531b5796878af1bff47d984bccababec6bf/src/native/capture_pomodoros_agenda.rs#L68); [snapshot log counters](https://github.com/bobs-org/bob-cli/blob/f2c24531b5796878af1bff47d984bccababec6bf/src/native/highlights_ref/note_snapshot/transclusion.rs#L1805).
- [C10 — grouped writes and best-effort rollback](https://github.com/bobs-org/bob-plugins/blob/477af35548282f52cf6872d15e06668a4597767f/plugins/bob-navigation-hotkeys/src/510-plugin-link-commit-and-lane.js#L1).
- Audited policy: `glossary:work-log`, `glossary:task-freshness`, `glossary:keep-streak`, `glossary:schedule-log`, `glossary:morning-gtd-review-footer`; `decisions:rotten-keeps-use-priority-decay`, `decisions:decay-decisions-are-available-immediately`, `decisions:review-walk-is-tiered`, `decisions:answering-advances-the-walk`, and `decisions:unblocked-tasks-resurface-as-ticklers`.

**Recommended solution.**

Implement **Rotten Log as a task-local history of explicit ordinary ROTTEN keeps**, using the existing refresh prompt/planner infrastructure. Offer an optional reason on Alt+F and Ctrl+Alt+F, but always write one dated event when the qualifying keep succeeds—even when the reason is blank. Include the decay card's Keep path, preserve existing batch skips, and commit the stamp, streak effect, and event together before any advance.

Show a compact count and latest reason derived from the log, keep `[keeps::]` as the existing independent streak, and publish the glossary draft with the implementation. Start with strict ROTTEN scope, no backfill, no extra authoritative counter, and no new global review mode. This delivers the requested visible history while keeping the decision itself quick and preserving the current review system's meaning.
