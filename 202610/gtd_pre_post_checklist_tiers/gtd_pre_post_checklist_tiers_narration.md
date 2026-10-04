---
narration: 1
title: PRE and POST for the Morning Review
source: research:202610/gtd_pre_post_checklist_tiers/gtd_pre_post_checklist_tiers__final.md
source_blob: d5e10ef2bc8f085880af3e7cfbec4f40c1f0cfcd
date: 2026-10-04
kind: research
edition: brief
producer: agent
target_minutes: 4
---

## The short answer

Should the Getting Things Done morning review gain PRE and POST groups? The report recommends building both into the existing review walk.

PRE contains the opening chores. POST contains the Morning review task, which you complete to close the ritual. Membership comes from exact task tags: the GTD tag together with PRE or POST.

This solves a measured problem. The daily chores were closed on only 8–12 of 34 days, often in late batches. Morning review has never been closed. The current walk never lands on these recurring tasks.

The proposed order also makes sense. Importing inbox tasks, checking email, and reviewing the calendar can produce new captures. Those chores should happen before reviewing NEW tasks.

Keep POST last, after ROTTEN. The researchers split on that placement. The deciding evidence is the Morning review task itself. Its text already includes optional ROTTEN upkeep before completion.

You do not have to traverse every ROTTEN task to reach POST. The existing jump-to-last command reaches it directly. Advertise that shortcut when the walk enters ROTTEN.

## The deciding safeguards

The crucial distinction is between reviewing a task and doing a chore. Ordinary review rows ask whether a commitment is still right. PRE and POST rows ask whether you did the work.

Completing the task must resolve a checklist row. A freshness stamp must never resolve it. Checklist actions must not affect keep streaks, decay, upkeep counts, or the ROTTEN budget.

For recurring chores, freshness state remains empty. Tagged one-off tasks retain their ordinary freshness state and bucket. The tags change their position in the walk.

The most important requirement adjustment widens ready to open and actionable today. The status hooks run every 15 minutes. Until they run after waking, due chores can still display as Blocked.

A strict Ready-only rule would hide chores exactly when you need them. Include open tasks with an arrived schedule and no open dependency. Keep hidden tasks and future tasks excluded.

Completion also needs a deliberate gesture. On PRE and POST, Alt Shift F should complete and advance. Alt F should complete in place. The normal next-task key skips the chore, leaving it due.

Use the existing Tasks completion command so recurrence happens correctly. Do not write a completed checkbox directly. Completing a recurring chore inserts its next occurrence and shifts later lines.

That exposes a navigation risk. A stale line-number match can skip the next chore. Match the cursor by task text first. Verify recurrence and cursor behavior in a live Obsidian run.

Match tags exactly. Similar words must not qualify. Warn about missing GTD tags or conflicting phase tags.

## What to do

Tag only the 8 active daily tasks: 7 chores enter PRE, and Morning review enters POST. Leave Weekly prune and cancelled leftovers alone.

Rewrite Morning review as a closing checklist when the code ships. Remove instructions that restart the walk and duplicate the inbox import.

PRE counts toward commitments. POST is a closing group. Show remaining work when you reach POST, but never block completion or complete it automatically. Its checkbox is your assertion.

Consider merging the body chores and limiting email time. A regularly skipped PRE chore may belong elsewhere in the day.

Implement the groups in both shared evaluators, with matching tests. Update the decision record because recurring tasks are currently excluded from every tier.

The freshness trial says to avoid changing the ritual mid-trial. The report leans toward shipping when ready and logging the date. Holding deployment until after the trial is the stricter alternative.

The recommendation is to build PRE and POST, keep POST last, and make checklist completion explicit and separate from freshness review.
