---
narration: 1
title: Reorganizing Bob's Commands
source: research:202610/bob_cli_command_tree_reorganization/bob_cli_command_tree_reorganization__final.md
source_blob: 69b74d2dfe1118e8f5db8b25d0e5d2ba3ff09f6a
date: 2026-10-04
kind: research
edition: brief
producer: agent
target_minutes: 4
---

## The question and short answer

Could Bob's commands become easier to understand by grouping them under new parent commands? The report recommends reorganizing Bob, primarily through clearer help. Add only 2 narrow families: task maintenance and Pomodoro tools.

The current help lists 28 visible commands alphabetically. Of those, 10 are capture protocol endpoints for Bob Mac Capture. Their names place them near the start, filling the first screen with plumbing. The flat list also hides the daily workflow already explained in the documentation.

The proposed result is 14 entries in 5 help sections, followed by a separate capture protocol section. The sections cover daily workflow, tasks and projects, the vault, integrations, and setup. Sort commands alphabetically inside each section.

This reframes the goal. Make help and command names self-explanatory. Grouping is one tool for reaching that goal. Keep capture and the review commands directly accessible. Do not invent task operations merely to make a new command family look complete.

## The deciding reasons

A broad task umbrella sounds intuitive, but nearly everything in Bob touches tasks. It would offer little guidance about membership. It would also split the existing review trio: plan, ready, and freshness. A command called bob task ready sounds like a mutation, although ready displays a report.

A narrow task family earns its place because its verbs otherwise remain ambiguous. Archive could refer to completed tasks or documents. Reconcile could refer to tasks or Git synchronization. Putting task before those verbs identifies what changes.

The proposed membership rule is simple: these commands rewrite task lines across the whole vault. Reconcile updates task states and cleans the ledger. Archive moves completed or canceled task blocks. Reroll changes scheduled dates for due prioritized tasks.

Reroll is the least certain naming choice. The report prefers it because randomize can suggest shuffling task order. Task randomize remains an acceptable fallback.

Compatibility determines the rollout. Existing spellings must keep working indefinitely as hidden aliases, with no warning output. A Mac crontab runs task reconciliation every 15 minutes and sends errors to cron mail. Warning messages could therefore generate repeated mail.

The capture protocol names must stay unchanged. Bob Mac Capture installs separately and invokes exact command names. Nesting protocol operations under capture would also collide with valid free-text captures. Words such as parse and complete already work as task text.

A new vault family is deferred. A Vault help section provides the grouping, while existing synchronization and nightly names remain familiar to automation.

## What to implement

Start with help and completion. Show the workflow sections in both. Collapse capture endpoints to a pointer in short help, and list them fully in long help. Repair command-specific help so it shows the real options. Label default actions clearly. Hide the one-time freshness seed operation from help and completion, while retaining its guarded implementation.

Next, introduce bob task archive, bob task reconcile, and bob task reroll. Bare bob task should show help and do nothing, because every member writes data.

Introduce bob pomodoro notify, bob pomodoro status, and bob pomodoro tmux. Bare bob pomodoro should continue showing status. Every previous spelling remains a permanent silent alias.

Verify equivalent output, exit codes, and effects between old and new names. Preserve capture grammar, timer output, and existing integrations. Update documentation and scripts when convenient; those updates must never become prerequisites for compatibility.

The recommended solution is staged: improve discovery first, then add only the 2 families whose membership is predictable. Keep the familiar daily commands at the root and preserve every existing invocation.
