# Explicit task refresh history and approved decay

Independent research by **cdx**, 2026-10-03. This report uses the request, current project memory, independently inspected source code, focused executable checks, and external primary sources. No other report or researcher findings from this swarm were consulted. This is design research; no application, plugin, configuration, or vault behavior was changed.

**My recommendation is to add `refresh_count`, while keeping the decay decision separate from that total.** A lifetime count can reveal repeated reconsideration. It cannot reliably tell whether a task should become less important. The useful intervention is an occasional, explicit decision about an unchanged Ready task that repeatedly becomes rotten: keep it, review it less often, lower its priority and defer it, rewrite it, or cancel it. Preserve Alt+F as an ordinary confirmation gesture; require a clearly labeled choice before it changes priority, schedule, or status.

For the first release, ship the count and its quiet visual treatment. Collect narrow decay evidence in an observation mode before enabling proposals. My preferred eventual trigger is the third attempted rotten keep in the same decision context, with daily lane review excluded. The threshold is a trial choice, not a research-established optimum. Implement automatic planning of a proposal, followed by approval at the moment of change.

**What the current system actually does.** I inspected bob-cli at `6b6423186314af3a8e7f70a3d61ee7fe0763f856` and bob-plugins at `ac5419c39ea0812a98c5b0e8e6d169ff26e72a70`. The inspected plugins are bob-ledger-tools 1.22.0 and bob-navigation-hotkeys 1.66.0; the freshness namespace is version 4. These revisions matter because the review walk and its lane semantics have recently evolved.

| Finding | Consequence for this design | Primary evidence |
| --- | --- | --- |
| `fresh` means human confirmation that an open task still needs doing as written. Many human operations stamp it, including priority, schedule, dependency, lane, move, reopen, link, and selected capture operations. | Incrementing inside the generic stamper would count many actions other than an explicit refresh. | [Freshness contract, who stamps](https://github.com/bobs-org/bob-cli/blob/6b6423186314af3a8e7f70a3d61ee7fe0763f856/docs/freshness.md#5-who-stamps) |
| Alt+F and Alt+Shift+F share `refreshTaskFreshness`. They support ordinary tasks, counted targets, and dedicated Task Links. Alt+Shift+F advances after the write. | Both explicit refresh commands should count, including their batch and linked-task forms. Count the source task, never the link bullet. | [Navigation refresh implementation](https://github.com/bobs-org/bob-plugins/blob/ac5419c39ea0812a98c5b0e8e6d169ff26e72a70/plugins/bob-navigation-hotkeys/main.js#L32733) |
| A canonical stamp already dated today is currently a no-op. | “Every explicit refresh” and “every change of the stored date” are different requirements. We must choose deliberately. | [Placement and no-churn contract](https://github.com/bobs-org/bob-cli/blob/6b6423186314af3a8e7f70a3d61ee7fe0763f856/docs/freshness.md#3-placement-rule) |
| Pending and Next normally have daily review intervals. Their walk tiers are separate from freshness buckets. | A daily commitment check must not accumulate decay evidence merely because it is frequently confirmed. | [Tiered evaluation](https://github.com/bobs-org/bob-cli/blob/6b6423186314af3a8e7f70a3d61ee7fe0763f856/docs/freshness.md#4-evaluation) |
| NEW, RETURNED, and expired ROTTEN have different meanings. Future-scheduled, recurring, Today-linked, hidden, and other excluded tasks have special treatment. | A trigger must use the exact pre-write evaluator result, rather than “old date” or the dashboard’s combined rotten bucket. | Same evaluation contract |
| The freshness mark already uses a check for today, a draining ring for aging, and a clockwise refresh arrow for due review. | Reusing that due glyph for the historical count would overload its meaning. | [Freshness mark](https://github.com/bobs-org/bob-cli/blob/6b6423186314af3a8e7f70a3d61ee7fe0763f856/docs/freshness.md#11-display-the-freshness-mark) |
| Existing priority decay is a previewed, approved scheduling operation. Its same-level roll streak comes from the Schedule Log; automatic randomization is transparent to it. | Reuse its action planning and write machinery, while preserving a separate cause and evidence model for rotten keeps. | [Recommended roll and priority decay](https://github.com/bobs-org/bob-cli/blob/6b6423186314af3a8e7f70a3d61ee7fe0763f856/docs/projects.md#recommended-roll-and-priority-decay) |

I also read the accepted decisions for freshness-gated Ready, tiered review, and sticky lanes through audited memory reads. The proposed feature respects their current boundaries: refresh history does not create a new status, move a task, feed a bucket, reorder the review tiers, or release Next/Pending. Any approved scheduling action uses the existing scheduling rules. Any approved cancellation uses the existing cancellation path.

**The idea is useful, with a different interpretation of what the number proves.** The count can make an otherwise invisible pattern visible: “I keep confirming this task, yet it is still here.” That is a useful invitation to reconsider scope or opportunity cost. It can also help find tasks with excessive maintenance cost.

The count does not measure neglect, lack of progress, or low value. A task may remain important while an external dependency changes slowly. A demanding task may require several review cycles before there is enough uninterrupted time. Conversely, a neglected task might have a count of zero. A conscientious reviewer will often generate a higher count than a person who ignores review entirely. Automatically punishing the former would work against the behavior freshness was introduced to encourage.

This is my inference from the task semantics, not a claim that a particular count predicts procrastination. The official GTD Weekly Review includes reviewing action, waiting-for, and project lists; regular reconsideration is part of maintaining a trusted system. It supplies a useful counterexample to treating repeated review as inherently unhealthy. [David Allen Company’s Weekly Review](https://gettingthingsdone.com/2009/05/the-gtd-weekly-review/)

There are two different problems worth solving. **Review pressure** means a still-valid task returns for confirmation too often. Its natural remedy is a longer review interval. **Priority drift** means repeated decisions to leave a task in the backlog show that its current priority or commitment deserves reconsideration. Its remedy may be a lower priority and a future scheduled date, a smaller task, or an explicit cancellation. A priority decrease does not itself lengthen the freshness interval; the current system’s priority rolls also schedule tasks, which is what takes them out of the immediate Ready review pool.

I would therefore avoid a rule such as “refresh five times, reduce priority.” It mixes the two problems, treats different review cadences alike, and cannot distinguish actual execution from maintenance.

**Adjustments to the requirements I recommend.**

| Requested or implied requirement | Recommended clarification or adjustment | Reason |
| --- | --- | --- |
| Track explicit Alt+F refreshes. | Include Alt+Shift+F and command-palette invocations of the same operations, along with counted and Task Link targets. | They express the same user intent through existing supported surfaces. |
| Track every time. | Count each successful explicit refresh operation, including another deliberate confirmation on the same day. Ignore repeat key events, duplicate dispatch, duplicate targets, refused writes, and abandoned dialogs. | This tracks intent rather than whether a date string happened to change. It avoids losing a confirmation because a different operation stamped the task earlier today. |
| Use `refresh_count` to enable decay. | Keep `refresh_count` cumulative; use a separate, narrower evidence stream for decay. | Resetting the total destroys the requested history; using it directly produces false positives. |
| Auto-decay, approved at the time. | Automatically propose; commit only the action explicitly selected in the review decision UI. | Alt+F should never unexpectedly cancel or defer a task. |
| Render as an icon. | Render an icon **with the numeric count**, beside the existing freshness mark. | The count is the information; an icon alone cannot communicate it. |
| Beautiful. | Use the existing typography and spacing, with muted history and an actionable proposal only where relevant. | Visual intensity should follow the need to act, rather than the magnitude of a lifetime number. |
| Every task. | Preserve existing refusal rules for closed and recurring tasks; support all currently refreshable open lanes. | Recurrence copies task metadata into new occurrences, and closing is not an open-task confirmation. |
| Lifetime history. | Say “since tracking began,” without backfilling old `fresh` dates or seeded stamps. | Past counts cannot be inferred truthfully. |

The same-day choice deserves explicit attention. It changes the existing no-churn rule **only for explicit refresh commands**: `fresh` may remain today, but `refresh_count` changes. Generic stamping remains idempotent. If Bryan instead wants the narrow literal metric “number of times Alt+F changed the date,” keep today’s no-op and do not increment it. That alternative is smaller, but it systematically misses explicit confirmations after another same-day human action. I favor the operation-based definition because the stated goal is tracking explicit reconsideration.

**A concrete count contract.** Store `[refresh_count:: N]` on the task line. N is a non-negative integer; absence means no recorded count yet. Do not bulk-add zeros. The first successful explicit operation writes 1. Treat it as the cumulative count of committed explicit refreshes since instrumentation began, not all historical refreshes and not the total number of `fresh` writes.

The counter belongs to the task’s history. Ordinary moves, archive moves, lane changes, priority changes, completion, and reopening preserve it. A genuinely new task created from a template or copied through a supported creation operation begins without it; creation must not inherit freshness history or decay evidence. Manual copying remains ordinary text editing, so the source-mode contract should explain how to clear copied history. Never infer a reset from task age or a changed checkbox.

For a batch, resolve all targets first and deduplicate the actual source tasks by resolved file and task identity. Multiple Task Links to one task in the same invocation count once. Increment each successful distinct target by one, regardless of the numeric prefix. Preserve the existing meaning that a Vim count selects the cursor target plus N additional targets.

A refusal or stale preimage produces no stamp and no count change. A successful write groups the stamp and increment together. Undo restores both; redo restores the same postimage rather than executing another increment. Rendering, Dataview recomputation, note opening, midnight ticks, sync, hooks, randomize, and the one-time freshness seed never increment.

Choose one shared numeric range across Rust and JavaScript; `u32` is ample and exactly representable by JavaScript. Parse trimmed decimal digits, canonicalize valid integers, and refuse an increment at the maximum. A negative, fractional, malformed, or duplicate count is an integrity problem, not permission to guess zero or sum the fields. Expose a lint and leave the task untouched by the explicit refresh until the count is repaired. Ordinary stamping should preserve the bytes of an invalid counter rather than silently erase the history.

**Placement is the main implementation hazard.** The current native Tasks parser reads supported fields from the right and stops on an unknown key. Therefore this is the intended shape:

```markdown
- [ ] #task Investigate cache behavior [fresh:: 2026-10-08] [refresh:: 7] [refresh_count:: 4] [priority:: medium] [scheduled:: 2026-10-01] ^cache
```

All Bob freshness fields precede the trailing Tasks suffix. Do not append the counter after `scheduled`, `priority`, `dependsOn`, or the block ID. A custom field inserted inside that suffix can stop parsing and hide fields to its left. The exact canonical order should be documented and shared between languages; retaining `fresh` immediately followed by `refresh` preserves the existing adjacency convention, with the counter next.

The placement scanners must recognize `refresh_count` as a Bob field that extends the scanned run but is not a Tasks suffix element. Both generic stamping and interval editing must preserve and reposition it without incrementing. The explicit operation must update it through the same placement machinery, rather than append a second ad hoc field.

An executable probe against the current JavaScript helper confirmed that it preserves an unfamiliar counter in the body but moves the fresh/refresh pair to its right, with an extra space in one fixture. For example:

```text
Before: Test [fresh:: 2026-10-01] [refresh:: 7] [refresh_count:: 3] [priority:: medium] …
After:  Test  [refresh_count:: 3] [fresh:: 2026-10-08] [refresh:: 7] [priority:: medium] …
```

That is a compatibility finding for the proposed field, not an existing supported-feature defect. It means updating navigation alone is insufficient. Update the Rust writer, JavaScript writer, and renderer together. Make the display tolerate a valid standalone counter before the suffix, so an older writer’s reordering does not make the history disappear.

Keep `stampLine` as a generic stamp-only API. Add a distinctly named explicit-refresh reducer, such as `confirmLine`, that returns the new line plus a structured result. Navigation calls it only from the explicit refresh route. Existing status, link, dependency, priority, and capture callers retain their current stamper. The decay stage will need a task-block reducer because evidence lives under the task, not just on its line. Capability-check the new API; an old or missing ledger-tools plugin should refuse the new tracked operation with a useful notice, rather than silently refresh without recording the requested history.

**The visual design.** Keep the existing freshness mark as the primary signal and put a small history glyph and count immediately beside it. Use a clock-with-return-arrow glyph, visually related to freshness but distinct from the clockwise arrow that already means “review due.” Lucide’s historical `history` page now resolves to `rotate-ccw-clock`; verify the bundled Obsidian icon name or draw a tiny inline SVG in the existing widget rather than assuming the latest Lucide name is available. [Lucide history glyph](https://lucide.dev/icons/rotate-ccw-clock)

Conceptual text approximations, with the bracketed word representing the actual SVG:

```text
Investigate cache behavior       ✓ today · [history] 4
Investigate cache behavior       ◔ 3d/14d · [history] 4
Investigate cache behavior       ⟳ 7d · [history] 4
```

Use the existing mark’s 0.8em interface font, tabular numerals, baseline, and compact gap. The history count stays muted in every normal state, including very large totals. Give neither its capsule nor its text a permanent warning color. Hide absent/zero history by default; display every nonzero recorded count. Do not render “4d,” “4/3,” or four dots: those suggest age, a threshold gauge, or a score.

The combined tooltip should retain freshness’s date and next-review explanation, then add “4 explicit refreshes since tracking began.” If decay observation is enabled and the row is exactly resolved, add “2 unchanged rotten keeps in this decision cycle.” Keep those numbers separately labeled. A count of 20 could coexist with only one qualifying keep; that is expected.

Clicking or placing the cursor in the field reveals editable raw Markdown, as today’s freshness mark does. It never increments, accepts a recommendation, or cancels a task. Provide the corresponding palette operation for people who do not use the hotkey. Preserve source mode and the existing mark/pill toggle. Reading view, Tasks query output, Dataview output, and block transclusions should show the same numeric meaning. An unresolved rendered task may show its valid raw count, but it cannot claim to know its decay eligibility.

Keep colors theme-native and test contrast: muting must not make the digits unreadable. Use shape, text, and an accessible label as well as color. W3C’s guidance explicitly requires another visible means for information otherwise conveyed by color, and meaningful non-text graphics need sufficient contrast. [Use of Color](https://www.w3.org/WAI/WCAG22/Understanding/use-of-color.html), [Non-text Contrast](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html)

A quiet normal display with a secondary explanation fits progressive disclosure: reserve detailed choices for the occasional decision, while showing the history directly. Present concrete action labels and consequences there, rather than requiring the user to remember what an unexplained leaf or refresh icon does. [NN/G on progressive disclosure](https://www.nngroup.com/articles/progressive-disclosure/), [recognition and recall](https://www.nngroup.com/articles/recognition-and-recall/)

**Decay evidence should be sparse and auditable.** A lifetime total cannot reconstruct the states in which its events happened. The second stage should record qualifying review events in a managed child **REVIEW LOG** and derive the current run from that record. Do not put confirmations in the Schedule Log: confirming an unchanged task does not schedule it.

Log ordinary unchanged rotten keeps, approved review decisions, and boundaries that restart the decision context. Do not write a new child entry for every daily Pending/Next confirmation; those count in `refresh_count` but contribute no decay evidence. The counter and the sparse log have distinct meanings and are not duplicate projections of the same event stream.

A qualifying keep requires all of the following **before** the write:

- The exact shared evaluator identifies an eligible Ready task in the expired ROTTEN state/tier.
- The operation is an explicit confirmation, rather than an incidental stamp.
- The task has a valid prior confirmation; NEW contributes no evidence.
- It is neither RETURNED/resurfaced nor a walked Pending/Next task.
- It satisfies the existing visibility, dependency, schedule, recurrence, daily-note, and Today exclusions.
- Its actionable description and decision context still match the current evidence run.

The context should include normalized actionable wording, the current canonical priority value, and the effective review interval. Ignore formatting-only changes, `fresh`, the counter, block IDs, and derived dependency IDs when comparing wording. A rewrite changes the context. An interval change changes the context. An explicit priority decision changes the context. An approved “keep as is” decision in the proposal UI establishes a new context boundary even if the task text is unchanged.

Recorded work or an explicit commit/release/reopen decision should also end the old keep run. This feature must not label a task “without progress” unless it actually has trustworthy progress evidence; “unchanged rotten keeps” is the accurate UI phrase. For supported work and lane actions, record a review boundary through the shared task-block operation. For manually changed wording, context comparison can conservatively start a new run. Do not reset evidence for cosmetic edits or background normalization. Automated randomization should not manufacture a meaningful human decision.

The managed log needs a small, versioned grammar: typed event kind, local date, refresh ordinal where applicable, canonical priority and interval, and a context fingerprint. Human explanations can follow those fields, but the evaluator must not parse localized prose to infer an event kind. Read direct child entries only and ignore nested task logs. Give events stable IDs if they are to participate in conflict reconciliation. Newest-first entries follow the existing log idiom.

Malformed or missing evidence yields no automatic proposal. Never “recover” a rotten streak from the lifetime count. The lifetime count can ship before the log; in that case the later decay stage begins collecting its own evidence from zero. Historical counts do not retrospectively become eligibility.

This costs a new managed log and integration with meaningful-decision writers. It is justified when the decay feature is enabled, because the recommendation must explain why it exists. It is not necessary merely to render a count. Start the sparse log in observation mode if decay is intended soon; otherwise defer its schema rather than persisting speculative data indefinitely.

**The proposed policy and its exact timing.** Begin with an observation mode. Once the count and evidence contract are stable, trial `confirm` mode with K = 3 qualifying rotten keeps per decision context. Keep the policy disabled unless enabled intentionally. Do not borrow the existing default of one priority roll: a refresh confirms validity, while a roll explicitly postpones execution.

Let q be completed qualifying keeps since the last context boundary. On an eligible rotten confirmation, compute the candidate q + 1. If that is below K, commit the ordinary refresh and log the keep. If it reaches K, show a review decision **before any write**. Thus two keeps are already recorded when the third attempt opens the decision UI. Do not wait until the task was stamped and then discover that it has disappeared from the review queue.

| Example, 7-day Ready cadence | Total after action | Evidence after action |
| --- | --- | --- |
| Oct 1: confirm NEW | 1 | 0 |
| Oct 8: confirm unchanged ROTTEN | 2 | 1 |
| Oct 15: confirm unchanged ROTTEN | 3 | 2 |
| Oct 22: third rotten confirmation attempt | Unchanged while UI is open | Third candidate awaits a decision |
| Choose Keep as is | 4 | New boundary; 0 |
| Choose Lower priority and defer | 4 if the accepted Alt+F operation stamps the still-open target | New priority/context; 0 |
| Choose Cancel task | Remains 3; cancellation does not stamp a closed task | Terminal decision |
| Escape / Back | Remains 3 | Remains 2; nothing committed |

Repeated same-day explicit confirmations may increase the total, but cannot create another rotten cycle because the pre-write evaluator sees today’s stamp. Daily lane checks also increase the total while contributing zero evidence. With a 7-day cadence this trial intervenes after roughly three rotten review intervals; with another cadence the elapsed time differs. Do not add a second elapsed-time threshold until observation shows that it is needed.

The decision UI should use familiar task-property picker styling and identify the task. A concrete prototype:

```text
Investigate cache behavior
Still in Ready after repeated review

This is the third unchanged rotten keep at P2, every 7 days.
4 explicit refreshes if you confirm this review.

Keep as is                         Enter
Lower priority and defer           P2 → P3 · Dec 6 · in 45 days
Review less often                  Every 7 days → choose interval
Rewrite task                       Return to the source line
Cancel task                        Record an optional reason

Esc: back · no changes
```

The dates here illustrate a frozen preview, not a proposed default roll. Generate the actual date once from the configured destination window. The default selection is **Keep as is**. Approving lower priority requires selecting its labeled row; a habitual Enter cannot accidentally demote or cancel a task. This is approval of a concrete consequence, rather than a generic “Are you sure?” dialog.

Keep as is records a recommitment boundary and grants another K qualifying review cycles. An optional reason can document a real constraint; requiring prose on every keep would turn review into clerical work. Review less often opens the existing refresh interval control and stamps only if the user accepts a value. Rewrite returns to the task with no stamp/count yet, so editing and a later explicit refresh form the final confirmation. Escape writes nothing. Alt+Shift+F advances only after a committed resolution; dismissed or abandoned choices leave the task as the walk anchor.

For a configured priority level with a successor, offer the existing one-step lower-priority-and-schedule action, with its exact destination date and a recorded refresh-specific cause. For implicit P0/no priority or an unconfigured value, do not invent a ladder or silently assign P1; keep, interval change, rewrite, and cancel still work. At the last configured priority level, expose Cancel as a separate deliberate choice and keep the safe default. Do not silently inherit the existing roll ladder’s terminal cancellation as Alt+F behavior.

Use the current scheduling/cancellation machinery for consequences and logs. A future date may derive Blocked and invoke existing link cleanup. A keep leaves lane, priority, schedule, and dependencies untouched. Approved cancellation retains the task and its Cancel Log; it does not delete the task.

One decision should never decay two levels because both roll and refresh evidence happen to be eligible. Share the decay action planner, carry a reason/source, and make acceptance of any actual priority decay a boundary for refresh evidence. A refresh-triggered decay writes a Schedule Log transition that already breaks the roll streak. A roll-triggered decay must also establish the corresponding review boundary. A plain Keep decision need not alter the scheduling streak.

Explicit exits and an undo path preserve user control. Apply a same-note decision as one editor transaction; make cross-note undo or a visible guarded reversal available instead of claiming that the active editor’s undo can reverse background notes. [NN/G on user control and freedom](https://www.nngroup.com/articles/user-control-and-freedom/)

**Batch approval needs a separate design.** A counted refresh may include ordinary tasks and several decay candidates. Do not open a series of surprising single-task dialogs, and do not approve all demotions with a bare refresh keypress.

Plan the whole batch first. If no task needs a decision, retain today’s fast path. Otherwise show one review sheet listing each candidate’s evidence and proposed consequence, with Keep as is selected for every row. The sheet must disclose any lower-priority, scheduled, or cancellation outcomes before a final Apply. Cancel the sheet without writing any target. Deduplicate repeated links before displaying counts.

Revalidate every source task against the frozen preview at Apply, including its count, raw task/block, context, priority, log, and relevant date/config state. A changed note or a changed local day invalidates the old preview and asks for a fresh decision. Do not silently substitute a newly rolled date. For the first decay implementation, supporting single-target proposals before the batch sheet is reasonable; the interim batch behavior must be explicit and must not bypass eligible decisions.

**Reliability across editor, files, and devices.** Source writes should stay within the existing guarded navigation paths. Active-note updates use an editor transaction. Background note changes need a read/check/modify operation whose callback verifies the expected preimage; Obsidian recommends `Vault.process()` for this purpose and distinguishes it from a stale read followed by `modify()`. This provides protection within a note, not a multi-note transaction. [Obsidian Vault API guidance](https://docs.obsidian.md/Plugins/Vault)

The current link writer prechecks all notes, writes sequentially, and attempts rollback on a failed write. Its catch block suppresses rollback errors. Therefore “all-or-nothing” is a best-effort operational goal, not a crash-proof atomic guarantee. For new count/evidence writes, report which notes actually committed if rollback fails, avoid claiming no tasks changed, and do not blindly replay an increment. Preserve the existing successful fast path while testing these failure cases.

The vault synchronizes through Git across multiple machines. A scalar count is exact for serialized committed operations on one vault image; it is **not** a globally exact event counter during offline concurrent editing. Two devices can independently change 4 to 5, and identical line edits may collapse without a conflict. A process lock on one machine does not solve this.

For the first release, document this limitation and prefer syncing before switching the editing device. Do not sum conflicting scalar snapshots; both include the same prior history. Existing conflict preservation prevents losing the local file, but does not automatically reconcile its events.

If “every time” requires exact recovery across offline devices, change the storage requirement before coding: record every explicit refresh as an event with a stable ID, merge/deduplicate event sets, and derive/materialize `refresh_count` from that history after reconciliation. A sparse decay log alone cannot reconstruct all lane and same-day refreshes. Full event history is more durable but adds substantial daily log volume, conflict handling, and a counter-projection contract. I would not introduce that complexity without an actual need for concurrent offline editing.

**Alternatives and their costs.**

| Approach | Strength | Main weakness | Assessment |
| --- | --- | --- | --- |
| Lifetime count directly drives decay | Very small implementation | Daily review, task age, same-day actions, and actual progress distort the trigger | Reject |
| Reset `refresh_count` on work or decay | Small per-cycle metric | Stops being the requested cumulative history; resets are difficult to explain | Reject under the stated requirement |
| Lifetime count plus stored `rotten_refresh_streak` | Compact, no new log | Every meaningful writer must reset it correctly; its cause and repairs are hard to audit | Viable only if log cost is unacceptable |
| Lifetime count plus sparse review evidence | Explainable causes, healthy lane review excluded, aligns with existing log-derived streaks | New managed log and context/boundary integration | Preferred eventual decay design |
| Full refresh event history with derived count | Best foundation for reconciling offline events | Log volume and projection/merge complexity | Use only if exact cross-device history is required |
| Increasing review interval as the only intervention | Directly reduces upkeep while retaining the task | Does not address priority mismatch or overcommitment | Offer prominently, do not make it the sole outcome |
| New Someday status, hidden tag, or task relocation | Creates a place for low-pressure work | Conflicts with current lane/bucket choices and broadens the feature | Defer; unnecessary for this request |
| A numeric “task value” or decay score | Potentially flexible | Opaque meaning and misleading precision without validated inputs | Reject for the initial design |

**Implementation sequence and verification.** First define the count semantics, including the intentional same-day change, in `docs/freshness.md`. Add shared placement/count vectors and an explicit reducer in ledger-tools. Mirror counter reading, placement preservation, and linting in bob-cli. Update both navigation refresh variants, then the mark’s source detection, widget model, and rendered surfaces. Add count metadata to existing headless output only where useful; a new CLI subcommand is not needed for the initial feature.

Do not assume the Dataview task object already exposes this custom property in every surface; read the raw line through the shared helper where necessary. Rust’s existing clean-description path strips inline fields, so the new property should remain metadata rather than leaking into task titles. If JSON fields are added, follow the current schema-version contract.

Ship and deploy the coordinated plugin changes from bob-plugins through `bob plugins sync`, never by editing deployed vault copies. Capture remains an incidental stamper: it must preserve the field without incrementing it. A frontend that delegates capture to bob should gain the writer’s behavior rather than maintain another counter implementation.

Next add the sparse evidence reducer and read-only proposal model, with observation disabled unless intentionally enabled. Freeze its grammar, boundary rules, and preservation under moves/archive/project promotion before enabling approvals. Begin with single-target decisions; complete the batch sheet and partial-write reporting before enabling proposals for counted/linked batches.

The meaningful acceptance cases are:

- Alt+F and Alt+Shift+F each increment once on a successful source-task operation; same-day confirmations follow the chosen semantics.
- Physical key repeat, duplicate event dispatch, and multiple links to one task never double-increment one invocation.
- Ordinary stamping, interval edits outside the explicit refresh command, capture, seed, hooks, rendering, and randomize preserve the count without incrementing it.
- All supported suffix fields, tags, and block IDs parse identically before and after canonical placement; malformed/duplicate counts cannot be silently lost.
- Recurring, closed, stale, and failed targets write neither half of the stamp/count pair.
- Undo/redo, single-note batches, cross-note failure, and failed rollback produce truthful counts and notices.
- NEW, RETURNED, daily lane review, and Today/dependency exclusions produce zero decay evidence; pre-write expired Ready/ROTTEN qualifies.
- A rewrite, accepted recommitment, cadence change, actual priority decay, or supported work/lane boundary restarts the appropriate evidence run.
- The third eligible attempt shows the defined preview before writing; Keep, approved decay, cancel, rewrite, and Escape produce the specified outcomes.
- An old/missing API, unresolved renderer, invalid evidence, or changed preview does not invent eligibility.
- Light/dark themes, Source/Live Preview/Reading, query output, transclusions, and accessible labels preserve the same count meaning.

I ran the five existing focused JavaScript suites for navigation freshness, navigation roll decay, ledger freshness, freshness mark, and freshness mark surfaces; all exited successfully. I also ran the current-helper placement/same-day probes described above. These checks validate the observed baseline and integration points. They do not validate an unimplemented counter, policy, or visual design, and I did not conduct an interactive Obsidian usability trial or a vault census.

Observe review time, eligible proposals, chosen outcomes, accidental actions, and cases where a needed task became harder to find. Do not optimize for lower counts, more cancellations, or fewer visible tasks alone. The existing freshness trial runs 2026-10-05 through 2026-10-18; avoid changing its lane cadence or gating policy as a side effect of this work. The new count can be introduced independently, with decay observation/proposals evaluated afterward.

**Recommended solution.** Implement `refresh_count` as cumulative explicit-refresh history, including Alt+Shift+F, with a quiet history icon and numeral beside the existing freshness mark. Preserve generic stamping and existing task/lane semantics. Collect a separate sparse record of unchanged Ready/ROTTEN keeps if decay is going forward, and trial a proposal on the third qualifying attempt in the same decision context. Default to Keep as is; offer review-interval relief, a previewed one-level priority-and-schedule decay, rewrite, and explicit cancellation. Require approval before changing priority, schedule, or status. Ship the counter/display first and enable proposals only after the evidence and consent paths are verified. This makes the number useful without turning conscientious review into a penalty.
