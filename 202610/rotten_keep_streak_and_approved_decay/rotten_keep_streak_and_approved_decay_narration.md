---
narration: 1
title: Counting Alt+F keeps and asking, once, what to do about them
source: research:202610/rotten_keep_streak_and_approved_decay/rotten_keep_streak_and_approved_decay.md
source_blob: 4f0891c7c9ebb16719f16468f106cee248524c69
date: 2026-10-03
kind: research
edition: full
producer: agent
cover: rotten_keep_streak_and_approved_decay_infographic.png
---

## The question and the recommendation

Should Bob count explicit task refreshes, display that history, and eventually propose decay for tasks repeatedly kept alive?

Yes, build it. But change what the number means, and decide where decay leads, before writing code.

The recommendation is a keep streak, followed by a user-approved decision card that feeds the existing priority ladder. Count consecutive due reviews answered only with Alt plus F. Clear the streak when another deliberate decision stamps the task.

Show quiet dots inside the existing freshness mark. At the decision point, replace the refresh glyph with a leaf. After 3 counted keeps, the next due refresh opens the card. Nothing changes until you choose.

The recommended choice is Not now. It defers the task through the priority system. Less often, Reword, Drop, and Keep remain available. Escape writes nothing. Enter never closes a task.

This proposal changes the original request in several ways. It tracks a streak instead of a lifetime total. It counts only due Ready tasks. It suggests the property name keeps, and combines the display with the existing freshness mark.

## Why this is a good idea

The decisive finding is the meaning of a task with no priority field. Bob defines that task as implicit priority 0: the highest priority, do it now, with no rolled date.

The live census found 176 of 177 open, visible Ready tasks had no priority field. Existing priority decay therefore reaches only about 0.6% of Ready. Repeatedly confirming a task without starting it contradicts its stored urgency.

Keeps supply the missing top rung. Priority rolls already step tasks down from priority 1 through priority 4 and eventually cancel. Repeated keeps can bring implicit priority 0 tasks into that existing ladder.

The request also addresses a known review weakness. Refreshing is the cheapest answer, and currently remembers nothing about repetition. A stored event count provides information the freshness date cannot retain. Creation dates measure existence, not neglect.

But counting every refresh mixes different events. The same shortcut handles first triage, daily lane review, early confirmation, and overdue Ready review. Daily lane keeps would dominate a lifetime total. A Next task could reach a threshold in 3 days, conflicting with sticky lanes.

A lifetime total also never forgets. Rewriting, working, or reprioritizing a task should prevent old refreshes from triggering the wrong decision.

The strongest objection is fairness. A count may measure conscientious reviewing rather than neglect. Someone who ignores review accumulates nothing.

The design answers that objection by counting only requested reviews. Ignored tasks remain rotten and outside the freshness-gated Ready pool. The consequence is a question, and the default choice is reversible.

Still, the count says something about urgency, not value. The card should say kept 3 reviews in a row. It should never claim no progress.

## What counts and what resets

A keep streak means consecutive reviews where Bob asked whether a Ready task was still right, and you only refreshed it.

Alt plus F, or Alt plus Shift plus F, counts when the pre-write queue identifies the exact target. The row must be Ready and belong to the Rotten or Returned review tier. The count and date change together in the same line write.

A missing property means 0. There is no migration or backfill. Seeded ages are not human keeps.

First confirmation of a New task does not count. Neither does an early refresh, a Pending or Next lane keep, or an out-of-scope refresh. Those presses still stamp freshness and preserve any existing count.

Same-day repeats do not count. Once refreshed, the task is no longer due. Automation, hooks, randomization, and seeding leave the count alone.

Every other gesture that stamps freshness clears the streak. That includes committing to Next, changing priority or the review interval, routing, rolling, reopening, and the relevant capture gestures. Closing or cancelling does not stamp, so the count remains on the closed line as history.

Implement resets inside the shared stamping helpers. That covers existing callers without maintaining a separate reset list at each call site. A dedicated keep helper becomes the only incrementing writer.

The suggested property name is keeps. Refresh already means the review interval, so refresh count could suggest counting interval changes. The name is a soft recommendation. The design works under either name.

## The decision card

At the default limit of 3 keeps, the next due refresh opens a small card instead of stamping. Reuse the priority picker's modal, styles, safeguards, and undo behavior.

Enter selects Not now. For an implicit priority 0 task, the default destination is priority 2. The card previews both the new priority and the rolled return date.

Choose the first configured priority level whose shortest deferral exceeds the review interval. With the default 7-day interval, priority 1 spans 2 to 7 days. Priority 2 spans 8 to 30 days, so priority 2 is the appropriate entry.

A task reviewed every 30 days instead enters at priority 3. A fixed priority 1 override remains possible. The reason is simple: the deferral should outlast the review it replaces.

Already prioritized tasks use their normal ladder recommendation. If that recommendation would cancel, Enter offers a same-level roll instead. Cancellation belongs only to the explicit Drop choice.

Press L for Less often. It selects the next larger review preset: 14, 30, or 90 days. The streak clears.

Press E for Reword. It stamps, clears the streak, and places the cursor at the task text for editing.

Press D for Drop. It uses the existing cancellation writer and records the keep count in the Cancel Log.

Press Alt plus F for Keep. This increments the count, from 3 to 4 at the first card. The card returns at the next due review. Keeping does not reset the streak because a bare repeat is still a bare repeat.

Escape writes nothing and leaves the review anchor in place. The numbered priority choices remain available. Alt plus Shift plus F advances after resolving the card.

Why recommend Not now instead of Less often? Repeated keeps challenge the claim do it now. Deferral corrects that claim and removes the task from Ready and the note's crowding count until it returns.

Lengthening the interval leaves the task in Ready, still occupying the note's capacity. It remains appropriate for standing or slow-burning tasks, so it stays one key away.

Batch refreshes count eligible below-limit targets and skip tasks needing a decision. They never open cards or bypass consent. Skipped tasks stay due, and the notice reports how many need a decision.

## A quiet and truthful display

Use the freshness mark already on the line. Add faint filled dots after its age and optional interval. A task with 2 keeps shows 2 dots.

Today's green check can remain green, but the dots never become achievement badges. Due tasks retain the existing orange capsule. At the decision point, a leaf replaces the refresh glyph. There is no red warning or extra border.

Dots cap at the configured limit, followed by an overflow count when needed. With decay disabled, dots cap at 3. A task kept beyond the limit can show 3 dots plus 1.

The tooltip adds the streak and threshold. At the limit, its shortcut hint changes from confirm to decide. Review notices announce that the next review will ask for a decision.

Raw properties remain available when editing. Malformed or misplaced fields stay visible with the existing repair treatment. Reading views and task results should fold the field consistently.

Do not add a dashboard chip, review tier, or separate rotten-task group. The leaf supplies the actionable signal without changing those settled systems.

The command-line freshness listing should expose the count and whether a decision is due. Its machine-readable schema moves from version 3 to version 4. Decision eligibility remains an annotation, never a new classification.

## Reliability and the alternatives

The important code defect is target matching. Today's refresh handler can associate a queue row with a task using only its line number. A lagging task cache could therefore credit the wrong task.

Counting must match the path, line number, and raw text exactly. An ambiguous or stale match should refresh without counting. The conservative failure is a missed keep, postponing the question by another review interval.

Store positive integers from 1 to 999. Omit 0. Invalid values read as 0 and receive a lint finding. Writers repair duplicates and placement.

The field belongs after freshness and the optional interval, before the Tasks suffix. Both language implementations must recognize it without hiding existing task properties.

Rust reads, validates, clears, and reports the field. JavaScript alone increments through the dedicated helper. Release Rust and the ledger-tools freshness namespace version 5 together. Older navigation code should fall back to an uncounted stamp.

Recurring tasks remain refused, preventing counts from carrying into another occurrence. Capture needs no grammar change, but its preview should render the property consistently.

Tests should cover counting, same-day repeats, uncounted keeps, resets, invalid data, placement repair, and unchanged task fields. They should also cover stale-cache matches, visual states, priority entry, and cancellation safeguards.

Synchronization can lose an increment. The scalar is therefore not an exact global event count. Hand edits are another limitation. Editing text and then refreshing a due task still counts as a keep. The Reword choice provides a correction; a false positive costs at most an early card.

4 of the 5 researchers favored a streak. The strongest alternative paired a lifetime count with a separate dated review log. That could detect rewording and improve auditing. It also adds multiline writes, another log grammar, and more rendering work. Decision-time log entries provide enough history for the initial design.

Interval graduation remains the Less often choice, rather than becoming a second decay ladder. The proposed split between prioritized and unprioritized tasks misread implicit priority 0.

Silently applying decay and offering undo does not satisfy approval at the moment of decay. Preselecting Keep would make the card another rubber stamp. Enter instead recommends reversible deferral and never cancels.

Lane decay remains outside scope. The feature must respect the existing sticky-lane rule.

## Rollout and the trial

Ship counting and display first, followed by the card. The freshness trial runs from October 5 through October 18, 2026. Do not change the review ritual during that trial.

Counting preserves the gesture. Dots are a display change that should be recorded in the trial log. For a pristine trial, count silently and show dots from October 19.

The report proposes the card after October 18 and before about October 24. Its arithmetic assumes counting starts October 6. 3 counted keeps, each a full lease apart, precede due review number 4. The first card therefore appears about October 27.

Expect an initial wave. The census found 11 recurring tasks and no per-task interval overrides among the 177 Ready tasks. All used the default 7-day interval. Roughly 166 divided by 7 means about 24 Ready reviews each day.

The review queue held 150 tasks: 4 New, 60 Pending, 33 Next, 1 Returned, and 52 Rotten. All 52 Rotten tasks were in the inbox. None had yet been kept by a human.

The seed staggered 15 to 26 stamps per day across a week. Tasks that are only kept can reach their first card in the same week, up to about 24 daily.

Deferred tasks return through the Returned commitment tier, spread across 8 to 30 days. Watch that queue for 2 weeks after the wave. If it crowds commitments, raise the entry level or keep limit.

Recalibrate after a month. If more than half of cards end in Keep, raise the limit to 4. If most end in Drop, lower it to 2.

The implementation also needs an accepted decision record and glossary updates. A separate inbox interval of 2 to 3 days is an adjacent vault choice, not a prerequisite.

## The recommended solution

Build the keep streak and the explicitly approved card. Use the existing priority ladder, existing writers, and existing freshness mark.

Count only exact-matched due Ready keeps. Clear the streak on other stamps. Default to 3 keeps before the next due review asks. Recommend deferral, keep Less often and Reword accessible, and reserve cancellation for Drop.

Show faint dots, then a leaf when a decision is due. Skip decision targets in batches. Introduce counting first, the card after the trial, and calibrate after a month.

Bryan still has choices to make. Choose keeps or refresh count. Confirm the limit of 3. Choose interval-aware priority entry or fixed priority 1. Decide whether Keep continues the streak or resets it. Choose dots during the trial or silent counting. Confirm that a lifetime total is unnecessary.

The report recommends keeps, the limit of 3, interval-aware entry, and continued counting after Keep. A streak plus decision-time logs replaces lifetime history.

The intended result is a familiar one-key keep until repetition merits a decision. The user approves the consequence, and the display remains quiet until that choice matters.
