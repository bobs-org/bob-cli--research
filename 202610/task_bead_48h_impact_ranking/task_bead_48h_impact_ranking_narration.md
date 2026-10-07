---
narration: 1
title: Which Recent Task Beads Matter Most
source: research:202610/task_bead_48h_impact_ranking/task_bead_48h_impact_ranking__final.md
source_blob: 4512832b6ab0c78d56a6ef3e8faf5b3435b9040c
date: 2026-10-07
kind: research
edition: brief
producer: agent
target_minutes: 4
---

## The short answer

Which recent task beads represent the most impactful work? The audit covers 31 task beads created or corroborated within 48 hours. It combines 5 independent researchers with the lead's own verification.

The strongest opportunity is making the test gate reliable again. A missing completion decision causes a deterministic failure before most tests can run. Fixing it offers the highest payoff per line of change.

The ranking weighs daily reach, severity, evidence, and effort. Corroboration is evidence, not a vote. Agent-facing defects attract more reports than problems Bryan encounters directly.

Plans and phases are excluded because they are different bead types. Completed fixes remain eligible because the question concerns impactful work, including work already delivered.

## What decides the ranking

First comes the missing completion decision for audio input. The lead reproduced this failure in 5 of 5 runs. It prevents 14 of 15 test binaries from executing. That hides 1,306 integration tests. A separate help snapshot regression already landed unnoticed. The lead filed that regression after the audit cutoff, so it falls outside this ranking.

Second is shared environment isolation across Rust tests. Module-private locks let parallel tests overwrite each other's environment. This is the most corroborated defect. It did not reproduce in the lead's 5 runs on lightly loaded apollo. Busy landing hosts keep encountering it. The related clock-variable failure needs verification rather than an assumed common cause.

Third is the broken artifact-link store. It has been broken for about 4 weeks. New links fail, and linked plan proposals crash before approval. The lead reproduced the failure directly. Repair would restore relationships needed for duplicate checks and future audits.

Fourth is the Tasks query sandbox deadline. Whole-vault initialization consumes a 2 second budget intended for a user expression. Daily planning and freshness queries can fail under load. Successful runs still took about 5.5 seconds. Lazy initialization could help, but the speedup has not been measured.

Fifth is plugin synchronization from agent worktrees. A plain sync can silently deploy stale code from the canonical checkout. One incident rolled back the live vault. That rollback is repaired; the recurrence hazard remains. A small guard could prevent it.

Sixth is a completed review-walk correction. Line-shifting edits previously caused due rows to disappear silently from the daily review. Stable text identity fixed the skip. All 6 identity tests passed when a researcher reran them.

Seventh is migration of about 424 legacy reading records. Those records remain invisible to the reference library and agents consulting it. This is the largest completeness opportunity. Its benefit remains potential because status mapping, duplicate handling, and source-hub policy need Bryan's design review.

Eighth is another completed fix: removing exported metadata from personal annotations. It corrected 113 of 115 annotated reference notes. That makes the library trustworthy for agents reading Bryan's notes.

Ninth is the Pandoc escaping test. It fails on athena's Pandoc 3.1.11.1, but passes on apollo's 3.1.3. Athena runs landings, so this still matters after the leading test defects are repaired.

Tenth is the missing canonical verification gate. Each landing currently improvises a substitute. The gate should run every test binary, preventing an early failure from hiding later regressions.

## What to do next

Start with the test failures and the newly discovered help regression. Then establish the canonical gate. The report asks for all test binaries to pass twice on athena under default parallelism.

Next repair artifact links, then tackle query timeouts and the plugin-sync guard. Review the reading migration design before bulk writes.

For an open-work queue, remove the 2 completed fixes. Substitute the PDF heading defect and the plugin timing flake.

The ranking is judgment, not a numerical score. The broad workflow failures clearly outweigh polish; their exact ordering is less certain.
