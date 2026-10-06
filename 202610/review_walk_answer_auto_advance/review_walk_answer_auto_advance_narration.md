---
narration: 1
title: Auto-advancing the morning review
source: research:202610/review_walk_answer_auto_advance/review_walk_answer_auto_advance__final.md
source_blob: 271ff82f8318f3dd3235317de5007706b89e62ca
date: 2026-10-06
kind: research
edition: brief
producer: agent
target_minutes: 4
---

## The short answer

Should answering an item automatically advance your Getting Things Done morning review? The recommendation is yes, with clear limits.

Today, you start and continue the walk with right bracket followed by S. Several answers already advance automatically. Others leave you on a task you have handled, requiring another navigation press.

The proposal completes that existing pattern. It also makes release, defer, and drop as convenient as keeping a task. Currently, the advancing keep gesture gives keeping a small structural advantage.

The deciding rule should describe outcomes, rather than keys. A gesture must start on the row where the review just landed. After its successful write removes that row from today's walk, advance exactly once.

This applies only to the current review landing. The same commands should retain their ordinary behavior during daytime use.

The volume makes release especially valuable. The live snapshot had 34 tasks in Next against a cap of 15. Getting below that cap takes about 19 releases. None of those releases advance today.

## Which answers should advance

Control Enter should advance after completing a task in every review tier. Reopening a task should stay put.

However, preserve the boundary between checklist chores and ordinary tasks. At the end of the opening checklist, Control Enter should stop. An explicit navigation press continues the review. This deliberately narrows the original request.

The reason is accidental completion. A habitual extra press could close a real commitment and immediately move you away from it.

Control Shift Enter should advance after successfully linking the task to Today. Unlinking should stay put. Linking an opening or closing checklist row also stays, because that row still needs completion.

Alt N should advance after a successful lane commit or release. A Pending release waits until its work-log prompt is confirmed. A counted batch should produce exactly one jump.

Control Shift P opens the Task Card. Advance after its final committed answer resolves the row, rather than when the menu opens.

For ordinary review tasks, committed card writes stamp the task as reviewed or close it. Checklist rows have stricter rules. Advance only after cancellation, a future schedule, or a new blocking prerequisite resolves the row.

Escape, cancelled prompts, refused writes, and changes that do nothing should stay. Reword and exploratory status cycling should also stay.

Keep Alt F as the explicit keep-and-stay answer. Control Alt F remains keep-and-advance.

Moving a task with Control Shift M is a later candidate. During review, advancing would replace the existing destination focus. That choice still needs Bryan's decision.

## The recommended solution

Put one shared helper in the navigation plugin. Capture the review origin before a writer changes anything. Continue only after the final successful write.

Keep the existing writers responsible for their own changes. In particular, retain the status cycler's normal completion path, which updates embedded task copies.

Determine resolution from the reported outcome and the changed line. A fresh queue membership check cannot reliably answer this immediately, because the task cache lags.

Reuse the existing anchor to find the next remaining item. Avoid passive file watchers: they cannot distinguish your answer from typing, synchronization, or automated updates.

The main shipping risk is a fast double press. These commands toggle. A second press could undo the answer or answer the next task before you see it.

Require an in-flight guard and a short settling window. Reject stale callbacks after another landing or navigation. Record the answered row in jump history so Control O can return to it.

Live Obsidian behavior and jump-history recovery remain unverified. Test them before shipping.

Start with completion, lane release, Today linking, and Task Card commits. Preserve the checklist boundary and the stay gesture. Add move integration later, if desired. Every completed decision should advance once; the review navigation key remains the skip gesture.
