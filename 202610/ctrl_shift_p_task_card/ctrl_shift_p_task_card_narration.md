---
narration: 1
title: Ctrl Shift P Task Card
source: research:202610/ctrl_shift_p_task_card/ctrl_shift_p_task_card.md
source_blob: d6df9070ea8360749998974f5456044530b2dd7a
date: 2026-10-03
kind: research
edition: brief
producer: agent
target_minutes: 4
cover: ctrl_shift_p_task_card_infographic.png
---

## The question and short answer

Should Bob replace the panel opened by Control Shift P in Obsidian? Yes, redesign its first screen. Keep the existing stages and writers behind it.

The recommended replacement is a compact Task Card, styled like Bob's existing decay card. All 4 independent researchers agreed that the front door is the right place to change.

The current panel asks which property to edit before asking what you want to accomplish. Its rows move with task state. Its search box takes focus, making direct letter shortcuts difficult.

The Task Card instead opens focused and names the task you are changing. Its actions stay in fixed positions. Unavailable actions dim and explain why.

Priority keys 1 through 4 set the level and the exact date shown beforehand. Key 0 clears priority. Control Enter keeps taking the existing recommendation. Enter opens scheduling without writing. The letter b opens dependencies, f opens review frequency, and x opens cancellation. Alt N commits or releases the lane.

Any other printable key enters the existing search list. Escape closes without writing. Backspace on an empty input returns to the card.

## The deciding evidence

The speed gain comes from eliminating navigation, not replacing the write engine. That engine already contains about 5,900 lines of tested behavior.

It handles dates, reasons, work summaries, dependencies, cancellation, freshness, project propagation, and different targeting contexts. Rebuilding those rules creates risk without making the first choice faster.

Picking a priority level drops from about 6 gestures to 2. Opening dependencies drops from 5 to 2. Cancellation drops from 6 to 3. Taking the recommendation stays at 2.

These estimates count a keyboard chord as one gesture. Fewer visual searches matter too: the priority digits never move.

The reports disagreed about making scheduling reasons optional by default. The consolidated recommendation keeps the prompt. The vault contains 79–216 typed reasons, depending on classification. Reasons are an established habit, not merely overhead.

Make them cheaper instead. Allow a reason beside the typed date. Shift Enter skips it. Combine the reason and any qualifying work summary into one review screen, while preserving their distinct meanings.

The priority buttons also need honest labels. Pressing 2 on a priority 2 task deliberately re-picks the level and resets its roll streak. Control Enter takes the recommendation and can count toward that streak. Similar dates do not mean identical behavior.

Beauty here means restraint: compact dimensions, theme colors, visible keycaps, readable dates, and the same visual family as the decay card.

## What to do next

Fix the refresh-stage crash before the freshness trial begins on October 5. Verification found it also breaks the decay card's less-often picker for intervals of 90 days or more.

Open the card immediately, even when a linked task requires an asynchronous note read. Otherwise fast keystrokes can reach the Vim editor, where x deletes a character.

While targets resolve, swallow keys and ignore writing shortcuts. Never queue a write whose preview the user has not seen. Ignore held-key repeats and text composition. Freeze displayed dates until an explicit re-roll. Preserve stale-change refusal and existing rollback behavior.

Build behind a setting that is off by default during the October 5–18 trial. Activate on or after October 19. Pilot the card and tally 20–30 real uses.

The adjusted requirements are explicit: preserve every capability and stored behavior, while allowing key sequences to change. Optimize frequent outcomes with visible previews. Keep the classic search permanently reachable.

The recommended solution is a new Task Card front door on the existing engine: faster common actions, stable geometry, and the same trusted writers.
