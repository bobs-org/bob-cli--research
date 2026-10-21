# Reviewed calibration labels (agent judgments)

**These are agent judgments, not Bryan-authored labels.** On 2026-10-21 Bryan delegated pair labeling through question gate `bb385582-380e-4885-b381-3cb6422909db` and asked `opus@xhigh` to double-check the first pass and complete calibration. This file is that review.

## Procedure

- Read the score- and band-free review (file:explicit:bd9fe71a265c714e4f41578a) and wrote independent judgments for all 80 pairs before opening the first-pass labels or any score.
- Compared with the first pass (file:explicit:b27592e2a9e2fdfe6a2165a2): 79/80 agreed. Pair 51 was revised N->U (both low confidence). Pairs 42/72 were reconsidered as possible D and kept U. Confidence was adjusted on 9/22 (high->medium) and 37/47 (medium->low).
- Nine pairs newly exposed by the tokenizer and similar-bar changes (N1-N9) were labeled with the same rubric. An experiment printout had already shown their bands and scores, so they are not score-blind.
- No live-vault note bodies or referenced documents were read for labeling; evidence is the title, note path and line, reference syntax, and closed metadata.

## Rubric

- **duplicate**: same intended work: capturing the query would re-record the candidate's work
- **useful heads-up**: different work worth seeing while capturing (shared subsystem or instance-level coordination, parent/subtask, reading vs implementation, explicit dependency)
- **noise**: not worth showing: a shared verb, template, or coincidental token only (different movies, readiness-project boilerplate, name puns)

- Parent/subtask, reading/implementation, and implementation/test pairs are U, never D.
- Same subsystem with a different instance (sibling provider adapters, sibling artifact entity types) is U; a shared template with different subjects (movies, readiness projects, 'Improve sase X') is N.
- Literal same title across different products (Bob vs SASE docs) is U: Same title is accurate, duplicate is not.
- Closed rows are judged as duplicates only when they record the same work.

## Outcome

- Original 80 directed pairs: first pass 10 D / 46 U / 24 N; reviewed **10 D / 47 U / 23 N** (48 unordered relationships: 6 D / 28 U / 14 N).
- Agreement: 79/80 directed pairs. Revised: pair 51 (N -> U, low confidence on both sides).
- Reconsidered and kept: 42/72 (considered D, kept U); 3, 11/33, 12/24 (ambiguous duplicates, kept D at medium); 17/36, 29/46 (cross-provider, kept U at medium); 37/47 (artifact entity types, kept U, lowered to low); 31/67 (kept N, low); 44/49 and 78 (kept U, low).
- Newly exposed pairs N1-N9: 7 U / 2 N (N1/N9 is a name pun: `sase-talk` vs `talked about`).

## Disagreements and changed judgments

| Pair | First pass | Reviewed | Note |
| --- | --- | --- | --- |
| 9 | D (high) | D (medium) | Concur on duplicate; confidence lowered from high. The `?!` proposal and the `Finish migrating` task name one outcome (Statistics tab on `sase stats`), but the first could be read as the open question that spawned the second. |
| 22 | D (high) | D (medium) | Concur; same reasoning and confidence change as pair 9. |
| 37 | U (medium) | U (low) | Concur, confidence lowered to low. Both promote a new entity type to first-class artifact status, which plausibly shares registration and lifecycle design, but the titles do not show a dependency. |
| 47 | U (medium) | U (low) | Concur, confidence lowered to low; reverse of pair 37. |
| 51 | N (low) | U (low) | REVISED N -> U (low). The candidate automates two of the routine's named steps (restart failed agents, dismiss agents), so seeing it is a 'you already wrote down the fix' heads-up. Both judgments are low confidence; sensitivity is reported both ways. The query is a #gtd checklist row that would not be captured as a new task. |

## All judgments

| Pair | Query | Candidate | Label | Confidence | Review |
| --- | --- | --- | --- | --- | --- |
| 1 | #prj Improve sase's Glossary! #hide (`sase_better_glossary.md:11`) | Review and improve sase's glossary terms! (`sase_better_glossary.md:78`) | U | medium | Concur. A closed subtask of the open project is useful context; it does not duplicate the project. |
| 2 | E2E test new `%hold` directive! (`sase.md:40`) | Add support for new `%hold` directive! (`done/sase_done.md:1205`) | U | high | Concur. Implementation versus its E2E test: separate deliverables, so not a closed duplicate. |
| 3 | Install new UPS battery! (`cash.md:52`) | Install UPS battery! (`dev.md:125`) | D | medium | Concur. The canceled dev.md row and the open cash.md row name the same install; nothing indicates a second UPS. A recently canceled twin is exactly what the closed band exists to surface. |
| 4 | Remove `branch_or_workspace_name` dependency! #prj_is_blocked (`sase_pre_blog.md:34`) | Remove `branch_or_workspace_name` dependency! #prj_is_blocked (`sase_pre_blog.md:53`) | D | high | Concur. |
| 5 | #prj Add "Goals" support to sase! #hide (`sase_goals.md:11`) | Plan epic roadmap for goals! #prj_is_blocked (`sase_post_blog.md:18`) | U | high | Concur. |
| 6 | Make appointment for CT scan! (`body.md:31`) | Make appt w/ Rahway Hospital for CT scan! (`body.md:39`) | D | high | Concur. |
| 7 | #gtd #pre Read Email (`gtd_daily.md:18`) | EMAIL: Update your MyPay access log-in to a personal email! (`cash.md:24`) | N | high | Concur. The query is a #gtd checklist row, a census artifact rather than a realistic capture. |
| 8 | Download "9" movie [💡](https://keep.google.com/u/0/#NOTE/1a11ae0c629.baf610f2fa3b51d2 "Open in Google Keep") (`love.md:45`) | Download Romantic Comedy movie! (`love.md:79`) | N | high | Concur. |
| 9 | The "Statistics” tab should be powered by `sase stats` command?! #prj_is_blocked (`sase_projects.md:17`) | Finish migrating "Statistics" tab backends to `sase stats` sub-commands! #prj_is_blocked (`sase_post_blog.md:24`) | D | medium | Concur on duplicate; confidence lowered from high. The `?!` proposal and the `Finish migrating` task name one outcome (Statistics tab on `sase stats`), but the first could be read as the open question that spawned the second. |
| 10 | #prj Installs/updates are ready to be talked about! #hide (`sase_better_installs.md:10`) | #prj Sase projects are ready to be talked about! #hide #prj_is_blocked (`sase_projects.md:10`) | N | high | Concur. |
| 11 | Cancel Obsidian! (`cash.md:117`) | Cancel Obsidian Sync! (`bob_git.md:24`) | D | medium | Concur. Obsidian's cancellable paid service, named in the git-sync project, is Sync; the cash.md row most plausibly tracks the same subscription. |
| 12 | Sell stocks now! (`dev_plex_hack_patch.md:22`) | Sell stocks! (`cash.md:61`) | D | medium | Concur. Same action; `now` adds urgency, not a second transaction. Why a stock sale sits in dev_plex_hack_patch.md is unexplained, which keeps confidence at medium. |
| 13 | [[ref/blogs/minions_stripes_one_shot_end_to_end_coding_agents\|Minions: Stripe’s one-shot, end-to-end coding agents]] (`sase.md:71`) | Minions: Stripe’s one-shot, end-to-end coding agents—Part 2 (`sase.md:233`) | U | high | Concur. Part 1 and Part 2 are separate readings with distinct ref notes; seeing one when capturing the other is useful, but it is not a duplicate. |
| 14 | Make docs site just as nice as https://zensical.org site! #prj_is_blocked (`sase_pre_blog.md:26`) | Make docs site just as nice as https://zensical.org site! (`bob.md:61`) | U | high | Concur. Literal same title, different products (SASE docs vs Bob docs): Same title is accurate, duplicate is not. |
| 15 | #prj Improved memory enough that it's ready to be talked about! #hide (`sase_memory.md:11`) | #prj Sase projects are ready to be talked about! #hide #prj_is_blocked (`sase_projects.md:10`) | N | high | Concur. |
| 16 | Watch the "Messenger” movie with Kelly! (`love.md:67`) | Watch "F1” the movie with Kelly! (`love.md:89`) | N | high | Concur. |
| 17 | [[ref/chat/hermes_agent_sase_provider\|Hermes Agent as a Fully Supported SASE Provider]] #prj_is_blocked (`sase_pre_blog.md:31`) | Adding pi as a fully supported SASE provider #prj_is_blocked (`sase_pre_blog.md:28`) | U | medium | Concur after challenge. Sibling provider designs share one adapter contract, so a relation is plausible. Rule applied: same subsystem with a different instance is U; a shared template with different subjects (movies, readiness projects) is N. |
| 18 | #prj Apply to 29 job openings! #hide (`job_2026_apply_29.md:11`) | Rename the project to "job_2026_apply_29"! (`done/job_2026_apply_29_done.md:10`) | N | medium | Concur. An administrative rename shares only identifier tokens with the query. |
| 19 | Review and close all memory beads! (`sase_memory.md:132`) | Apply for close! (`job_2026_apply_29.md:21`) | N | high | Concur. |
| 20 | Allow projects to configure local sidecar repos again! #prj_is_blocked (`sase_post_blog.md:28`) | Allow sidecar plugin repos to configure what AGENTS.md is used for the new repo! (`sase_art.md:142`) | U | medium | Concur. |
| 21 | #gtd #pre Read Email (`gtd_daily.md:18`) | Email #person/jenika for new meds! (`recur.md:15`) | N | high | Concur; #gtd checklist query. |
| 22 | Finish migrating "Statistics" tab backends to `sase stats` sub-commands! #prj_is_blocked (`sase_post_blog.md:24`) | The "Statistics” tab should be powered by `sase stats` command?! #prj_is_blocked (`sase_projects.md:17`) | D | medium | Concur; same reasoning and confidence change as pair 9. |
| 23 | #prj Sase projects are ready to be talked about! #hide #prj_is_blocked (`sase_projects.md:10`) | #prj Installs/updates are ready to be talked about! #hide (`sase_better_installs.md:10`) | N | high | Concur. |
| 24 | Sell stocks! (`cash.md:61`) | Sell stocks now! (`dev_plex_hack_patch.md:22`) | D | medium | Concur; reverse of pair 12. |
| 25 | [[ref/blogs/minions_stripes_one_shot_end_to_end_coding_agents_part_2\|Minions: Stripe’s one-shot, end-to-end coding agents—Part 2]] (`sase.md:233`) | Minions: Stripe’s one-shot, end-to-end coding agents (`sase.md:71`) | U | high | Concur; reverse of pair 13. |
| 26 | Make docs site just as nice as https://zensical.org site! (`bob.md:61`) | Make docs site just as nice as https://zensical.org site! #prj_is_blocked (`sase_pre_blog.md:26`) | U | high | Concur; reverse of pair 14. |
| 27 | Fix remote machines! #prj_is_blocked (`sase_post_blog.md:36`) | Add support for updating sase and agent CLIs on remote machines! (`sase_remote.md:46`) | U | medium | Concur. |
| 28 | Watch "F1” the movie with Kelly! (`love.md:89`) | Watch the "Messenger” movie with Kelly! (`love.md:67`) | N | high | Concur. |
| 29 | Add support for hermes LLM provider! #prj_is_blocked (`sase_pre_blog.md:45`) | Add support for pi LLM provider! #prj_is_blocked (`sase_pre_blog.md:42`) | U | medium | Concur after challenge. Two adapters built against one provider interface; the shared surface makes the heads-up actionable. The weakest U class in the set; see sensitivity. |
| 30 | [[ref/chat/gascity_advantages_over_sase_and_what_to_borrow\|Gas City vs. SASE: where Gas City is ahead, and what SASE should borrow]] (`sase.md:135`) | Gas Town vs. SASE: where Gas Town is ahead, and what SASE should borrow (`done/sase_done.md:1431`) | U | medium | Concur. Comparisons of different systems (Gas City vs Gas Town) against SASE: useful baseline, not the same report. |
| 31 | Artifact annotations should be auto-read when agents read the artifacts! #prj_is_blocked (`sase_post_blog.md:47`) | Memory should be artifacts! (`sase_memory_plan.md:26`) | N | low | Concur. They share only the artifact category; no overlap or dependency is visible. |
| 32 | Start prompting for next task when "next" task is promoted to a project! (`bob.md:144`) | Start prompting for next task in same project when closing task if any exist! (`bob.md:93`) | U | high | Concur. |
| 33 | Cancel Obsidian Sync! (`bob_git.md:24`) | Cancel Obsidian! (`cash.md:117`) | D | medium | Concur; reverse of pair 11. |
| 34 | Add support for updating sase and agent CLIs on remote machines! (`sase_remote.md:46`) | Fix remote machines! #prj_is_blocked (`sase_post_blog.md:36`) | U | medium | Concur. |
| 35 | #prj Sase projects are ready to be talked about! #hide #prj_is_blocked (`sase_projects.md:10`) | #prj Improved memory enough that it's ready to be talked about! #hide (`sase_memory.md:11`) | N | high | Concur. |
| 36 | [[ref/chat/pi_sase_provider_design\|Adding pi as a fully supported SASE provider]] #prj_is_blocked (`sase_pre_blog.md:28`) | Hermes Agent as a Fully Supported SASE Provider #prj_is_blocked (`sase_pre_blog.md:31`) | U | medium | Concur after challenge; reverse of pair 17. |
| 37 | Make prompts first-class artifact files with their own artifact repo! (`sase_art.md:126`) | Proc shells should have first-class support as sase artifacts! (`sase_polish_proc_lanes.md:19`) | U | low | Concur, confidence lowered to low. Both promote a new entity type to first-class artifact status, which plausibly shares registration and lifecycle design, but the titles do not show a dependency. |
| 38 | Stop duplicating notifications from remote machines! (`sase_remote.md:21`) | Fix remote machines! #prj_is_blocked (`sase_post_blog.md:36`) | U | medium | Concur. |
| 39 | Download Romantic Comedy movie! (`love.md:79`) | Download "9" movie [💡](https://keep.google.com/u/0/#NOTE/1a11ae0c629.baf610f2fa3b51d2 "Open in Google Keep") (`love.md:45`) | N | high | Concur. |
| 40 | Add support for hermes LLM provider! #prj_is_blocked (`sase_pre_blog.md:45`) | Hermes Agent as a Fully Supported SASE Provider #prj_is_blocked (`sase_pre_blog.md:31`) | U | high | Concur. |
| 41 | #prj Implement `/sase_skills` skill search skill! #hide (`sase_skill_bundles.md:10`) | Read research on `/sase_skills`! (`sase_skill_bundles.md:44`) | U | high | Concur. |
| 42 | Tell Kelly to get this stupid Trump account. [💡](https://keep.google.com/u/0/#NOTE/1a155504e27.804d139e0b1c3f52 "Open in Google Keep") (`love.md:26`) | Sign up for Trump account?! (`cash.md:39`) | U | medium | Concur after considering D. Both aim at the household getting a Trump account, so a recapture reading is possible. U is kept because delegating to Kelly and signing up yourself are different actions, and the beneficiary is unstated. |
| 43 | Integrate `symvision` script into sase-core repo?! (`sase_toobig_symvision.md:28`) | Merge functionality of `pyscripts` script into `symvision`! (`sase_toobig_symvision.md:20`) | U | medium | Concur. |
| 44 | [[ref/blogs/structured_agentic_software_engineering\|SASE: Structured Agentic Software Engineering¶]] (`sase_blog.md:16`) | The best recent reading on agentic software engineering (`sase.md:20`) | U | low | Concur, low. The reading list on agentic SE is plausible companion context for the SASE article within the blog project. |
| 45 | [[ref/chat/hermes_agent_sase_provider\|Hermes Agent as a Fully Supported SASE Provider]] #prj_is_blocked (`sase_pre_blog.md:31`) | Add support for hermes LLM provider! #prj_is_blocked (`sase_pre_blog.md:45`) | U | high | Concur. |
| 46 | Add support for pi LLM provider! #prj_is_blocked (`sase_pre_blog.md:42`) | Add support for hermes LLM provider! #prj_is_blocked (`sase_pre_blog.md:45`) | U | medium | Concur after challenge; reverse of pair 29. |
| 47 | Proc shells should have first-class support as sase artifacts! (`sase_polish_proc_lanes.md:19`) | Make prompts first-class artifact files with their own artifact repo! (`sase_art.md:126`) | U | low | Concur, confidence lowered to low; reverse of pair 37. |
| 48 | Make appt w/ Rahway Hospital for CT scan! (`body.md:39`) | Make appointment for CT scan! (`body.md:31`) | D | high | Concur. |
| 49 | [[ref/chat/agentic_software_engineering_reading_list\|The best recent reading on agentic software engineering]] (`sase.md:20`) | SASE: Structured Agentic Software Engineering¶ (`sase_blog.md:16`) | U | low | Concur, low; reverse of pair 44. |
| 50 | Read research on `/sase_skills`! (`sase_skill_bundles.md:44`) | #prj Implement `/sase_skills` skill search skill! #hide (`sase_skill_bundles.md:10`) | U | high | Concur. |
| 51 | #gtd #pre **Clean up SASE agents on athena and apollo**: Restart failed agents, dismiss agents from yesterday, review inboxes (`gtd_daily.md:16`) | Always prompt to restart failed agents when dismissing! [💡](https://keep.google.com/u/0/#NOTE/1a0be86d3a8.ab95b262553bc452 "Open in Google Keep") (`sase_agent_recovery.md:25`) | U | low | REVISED N -> U (low). The candidate automates two of the routine's named steps (restart failed agents, dismiss agents), so seeing it is a 'you already wrote down the fix' heads-up. Both judgments are low confidence; sensitivity is reported both ways. The query is a #gtd checklist row that would not be captured as a new task. |
| 52 | #prj Improve sase plans and epics! #hide (`sase_better_plans.md:10`) | #prj Improve sase's Glossary! #hide (`sase_better_glossary.md:11`) | N | high | Concur. |
| 53 | Add support for pi LLM provider! #prj_is_blocked (`sase_pre_blog.md:42`) | Adding pi as a fully supported SASE provider #prj_is_blocked (`sase_pre_blog.md:28`) | U | high | Concur. |
| 54 | #gtd #pre Brush teeth (`gtd_daily.md:21`) | Start brushing Leonard's teeth once a week! (`love.md:38`) | N | high | Concur; #gtd checklist query. |
| 55 | #prj Finish `toobig` / `symvision` migration! #hide (`sase_toobig_symvision.md:10`) | Integrate `symvision` script into sase-core repo?! (`sase_toobig_symvision.md:28`) | U | high | Concur. |
| 56 | Allow sidecar plugin repos to configure what AGENTS.md is used for the new repo! (`sase_art.md:142`) | Allow projects to configure local sidecar repos again! #prj_is_blocked (`sase_post_blog.md:28`) | U | medium | Concur. |
| 57 | [[ref/chat/pi_sase_provider_design\|Adding pi as a fully supported SASE provider]] #prj_is_blocked (`sase_pre_blog.md:28`) | Add support for pi LLM provider! #prj_is_blocked (`sase_pre_blog.md:42`) | U | high | Concur. |
| 58 | Enable remote power on for Athena! (`dev.md:73`) | Athena: outage recovery and remote power-on (consolidated report) (`dev.md:88`) | U | high | Concur. |
| 59 | #gtd #pre Import inbox tasks from Google Keep (`gtd_daily.md:19`) | #prj Empty this Google Keep inbox dump - every task triaged or done! #hide (`gkeep_gdocs_inbox_dump.md:11`) | U | medium | Concur; #gtd checklist query, so it is a census artifact. |
| 60 | Fix remote machines! #prj_is_blocked (`sase_post_blog.md:36`) | Stop duplicating notifications from remote machines! (`sase_remote.md:21`) | U | medium | Concur. |
| 61 | Merge functionality of `pyscripts` script into `symvision`! (`sase_toobig_symvision.md:20`) | Integrate `symvision` script into sase-core repo?! (`sase_toobig_symvision.md:28`) | U | medium | Concur. |
| 62 | Start prompting for next task in same project when closing task if any exist! (`bob.md:93`) | Start prompting for next task when "next" task is promoted to a project! (`bob.md:144`) | U | high | Concur. |
| 63 | [[ref/papers/agentic_software_engineering\|Agentic Software Engineering: Foundational Pillars and a Research Roadmap]] (`sase_blog.md:17`) | SASE: Structured Agentic Software Engineering¶ (`sase_blog.md:16`) | U | medium | Concur. |
| 64 | #prj Installs/updates are ready to be talked about! #hide (`sase_better_installs.md:10`) | #prj Improved memory enough that it's ready to be talked about! #hide (`sase_memory.md:11`) | N | high | Concur. |
| 65 | Improve `sase artifact create` command! (`sase_art_links.md:33`) | Add `commit_hooks.artifacts` to allow users to configure which files have `sase artifact create` run on them! (`sase_art_links.md:19`) | U | medium | Concur. |
| 66 | #prj Improve sase's Glossary! #hide (`sase_better_glossary.md:11`) | #prj Improve sase plans and epics! #hide (`sase_better_plans.md:10`) | N | high | Concur. |
| 67 | Memory should be artifacts! (`sase_memory_plan.md:26`) | Artifact annotations should be auto-read when agents read the artifacts! #prj_is_blocked (`sase_post_blog.md:47`) | N | low | Concur; reverse of pair 31. |
| 68 | #prj Improved memory enough that it's ready to be talked about! #hide (`sase_memory.md:11`) | #prj Installs/updates are ready to be talked about! #hide (`sase_better_installs.md:10`) | N | high | Concur. |
| 69 | Plan epic roadmap for goals! #prj_is_blocked (`sase_post_blog.md:18`) | #prj Add "Goals" support to sase! #hide (`sase_goals.md:11`) | U | high | Concur. |
| 70 | Give `just check-full` good output again! (`sase_monitor.md:31`) | Start making `just check-full` always run test suite! (`sase_pypi_releases.md:16`) | U | medium | Concur. |
| 71 | E2E test new agent history! #prj_is_blocked (`sase_pre_blog.md:19`) | E2E test new `%hold` directive! (`sase.md:40`) | N | high | Concur. |
| 72 | Sign up for Trump account?! (`cash.md:39`) | Tell Kelly to get this stupid Trump account. [💡](https://keep.google.com/u/0/#NOTE/1a155504e27.804d139e0b1c3f52 "Open in Google Keep") (`love.md:26`) | U | medium | Concur after considering D; reverse of pair 42. |
| 73 | [[ref/chat/athena_outage_recovery_and_remote_power\|Athena: outage recovery and remote power-on (consolidated report)]] (`dev.md:88`) | Enable remote power on for Athena! (`dev.md:73`) | U | high | Concur. |
| 74 | Add support for project-local xprompt skills! (`sase_skill_bundles.md:34`) | Migrate sase/skills/ directory to sase/memory/ once I figured out how project local skills work! (`sase_memory.md:104`) | U | high | Concur. |
| 75 | [[ref/blogs/structured_agentic_software_engineering\|SASE: Structured Agentic Software Engineering¶]] (`sase_blog.md:16`) | Agentic Software Engineering: Foundational Pillars and a Research Roadmap (`sase_blog.md:17`) | U | medium | Concur. |
| 76 | E2E test new `%hold` directive! (`sase.md:40`) | E2E test new agent history! #prj_is_blocked (`sase_pre_blog.md:19`) | N | high | Concur. |
| 77 | #prj Improve sase plans and epics! #hide (`sase_better_plans.md:10`) | Plan epic roadmap for goals! #prj_is_blocked (`sase_post_blog.md:18`) | N | medium | Concur. |
| 78 | [[ref/chat/agentic_software_engineering_reading_list\|The best recent reading on agentic software engineering]] (`sase.md:20`) | Agentic Software Engineering: Foundational Pillars and a Research Roadmap (`sase_blog.md:17`) | U | low | Concur, low. Same reasoning as pair 44, with the research-roadmap paper. |
| 79 | Plan epic roadmap for goals! #prj_is_blocked (`sase_post_blog.md:18`) | #prj Improve sase plans and epics! #hide (`sase_better_plans.md:10`) | N | medium | Concur. |
| 80 | Integrate `symvision` script into sase-core repo?! (`sase_toobig_symvision.md:28`) | #prj Finish `toobig` / `symvision` migration! #hide (`sase_toobig_symvision.md:10`) | U | high | Concur. |
| N1 | Rename sase-listen to sase-talk! (`sase.md:170`) | #prj Sase projects are ready to be talked about! #hide #prj_is_blocked (`sase_projects.md:10`) | N | high | Shared `talk` comes from the sase-talk name and the boilerplate `talked about`; renaming a CLI is unrelated to a readiness project. |
| N2 | [[ref/chat/artifacts_files_subtab_explained\|What are the entries on the Artifacts → Files sub-tab?]] (`sase_art.md:57`) | The files sub-tab of the artifacts tab should have files sorted by project and directory. (`sase_art.md:172`) | U | high | The explanatory reading on the Files sub-tab is direct background for changing that sub-tab's sort order; reading and implementation are separate work. |
| N3 | The files sub-tab of the artifacts tab should have files sorted by project and directory. (`sase_art.md:172`) | What are the entries on the Artifacts → Files sub-tab? (`sase_art.md:57`) | U | high | Reverse of N2: the existing explanation of the same sub-tab is useful context for the change. |
| N4 | Add `commit_hooks.artifacts` to allow users to configure which files have `sase artifact create` run on them! (`sase_art_links.md:19`) | Improve `sase artifact create` command! (`sase_art_links.md:33`) | U | medium | Reverse of pair 65: the hook configures which files run the command being improved, so the two inform each other without being the same work. |
| N5 | Start creating a PR for every epic! (`sase_better_plans.md:71`) | Create new PR for every necessary sidecar repo when PR exists for main project! (`sase_completion.md:32`) | U | medium | Both automate PR creation in the finalization flow (per epic vs per sidecar repo); different triggers worth coordinating, like pairs 32/62. |
| N6 | Create new PR for every necessary sidecar repo when PR exists for main project! (`sase_completion.md:32`) | Start creating a PR for every epic! (`sase_better_plans.md:71`) | U | medium | Reverse of N5. |
| N7 | #prj Implement memory webs/strands! #hide (`sase_memory_webs.md:11`) | Webs should be able to specify if/how/when an agent can/should modify its strands! (`sase_memory_webs.md:29`) | U | high | Project versus one of its own subtasks (agent permissions for strands): direct scope context, not the same deliverable. |
| N8 | Webs should be able to specify if/how/when an agent can/should modify its strands! (`sase_memory_webs.md:29`) | #prj Implement memory webs/strands! #hide (`sase_memory_webs.md:11`) | U | high | Reverse of N7: the parent project is direct context for the subtask. |
| N9 | #prj Sase projects are ready to be talked about! #hide #prj_is_blocked (`sase_projects.md:10`) | Rename sase-listen to sase-talk! (`sase.md:170`) | N | high | Reverse of N1: the shared token is a coincidence of names. |

## Limitations

- Single-annotator agent judgments by models from one family; the first pass and this review are not statistically independent raters.
- Reverse directions of one relationship are dependent observations.
- This is a calibration set from one vault census, not a held-out evaluation.
