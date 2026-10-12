# Do epics `bob-cli-6t` (project pull-in) and `bob-cli-6u` (`^prj`-line project blocking) conflict?

> **Research query:** I think the bob-cli-6u and bob-cli-6t epic beads conflict a bit.
> Confirm or deny this, leave good notes on the relevant beads, and suggest next actions:
> should I stop or re-plan either epic, or can both run in parallel as they are now?

Checked **Monday, October 12, 2026, 10:30–10:50 EDT** against:

- bob-cli `ec7251e` (origin/master; 6t.1's contract is the newest commit);
- both epic plans (`plan:202610/project_task_pull_in.md`,
  `plan:202610/prj_line_project_blocking.md`), every phase bead of both epics, and the
  canceled epic `bob-cli-6s`;
- live agent state from `sase agent list` and the running agents' artifact logs:
  `live_reply.md` (draft) and `codex_thinking.jsonl` / `tool_calls.jsonl` (stable
  checkpoints);
- the deployed plugin manifests in `~/bob/.obsidian/plugins/` (read-only).

## Bottom line

- **Confirmed: they conflict, and running both unchanged is unsafe.** The conflict is
  not in what you asked for. Pulling an emptied project's `^prj` in as Next fits 6u's
  line model. The conflict is in **how 6t was planned to be built**: on top of
  `bob-cli-6s`, which you canceled at 09:46 EDT and replaced with 6u. 6t was planned at
  10:07 EDT against the still-listed 6s phases, and its plan never mentions 6u.
- **The sharpest problem: every 6s bead now reads `CLOSED` (resolution `canceled`).**
  6t's "wait until 6s.X is closed" gates therefore pass even though the code they wait
  for never landed and never will.
  - **6t.2 (running).** Its own reasoning log says "Step 3 will borrow the
    project-blocked verdict from 6s.2 because 6s.5 was canceled." It is writing
    pull-in code against the YAML model (`src/native/project_dependencies/`, frontmatter
    `depends_on` / `scheduled`), which 6u.2 deletes. It is also editing
    `projects/{scan,mod,edits}.rs`, which 6u.2 and 6u.4 rewrite.
  - **6t.4 (waiting).** Its gate, "MacBook only after 6s.12 closes", is already true.
    When it runs, it would install bob and sync all plugins on the MacBook in the middle
    of 6u. That breaks 6u's ADJ-10 rollout order: Mac bob first, then this host, then
    Mac plugins, all owned by 6u.16.
- **Recommendation:** keep **6u** running as is. **Stop 6t's phase agents now** (6t.2
  and 6t.3 have committed nothing yet) and **re-plan 6t on top of 6u**, starting after
  6u.7 and 6u.15. The re-plan is small, because 6t.1's contract (§12.10 / §12.11) is
  already on master and 6u.1 is porting it to the line model right now. If you'd rather
  not stop it, the minimum is to make 6t.4 wait for 6u.16 (see
  [Next actions](#next-actions)).

## The two epics

| Epic         | Goal                                                                                                                                                                                                                                                              | State at 10:46 EDT                                                                                                                                                       |
| ------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `bob-cli-6t` | A close that empties a project links its `^prj` as Next and drops `#hide`, in both bob capture and Obsidian (§12.10)                                                                                                                                              | 6t.1 contract **landed** (`ec7251e`). 6t.2 (Rust) and 6t.3 (plugins) **running about 18 min, uncommitted**. 6t.4 rollout and land are waiting                           |
| `bob-cli-6u` | Replaces canceled 6s: project prerequisites on `^prj`'s Depends-On line, the project date as inline `[scheduled::]`, `#prj_is_blocked` on residents, no Task Links to Blocked tasks, and `[unblocked::]` so every auto-unblocked task resurfaces as a TICKLER | 6u.1 contract **running**, docs only, now at `just all`. 6u.2–6u.17 and land are waiting on dependencies                                                                |

## Where they conflict

### 1. 6t's gates point at canceled 6s beads (high severity)

6t's plan (`Relationship to the in-progress epic bob-cli-6s`) sequences itself against
6s phases. 6s was canceled for this re-plan, and 6u says only 6s.1, 6s.2 and 6s.11
landed. All 6s phases nevertheless show `✓ CLOSED`.

| 6t gate in the plan                                               | What happens now                                                                                                                                               | 6u replacement |
| ----------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------- |
| 6t.2 step 0: wait for 6s.5's §12.2 step-3 project verdict to land | 6t.2 saw "closed as canceled" and skipped the wait. It reuses 6s.2's YAML model instead, which is exactly what 6u.2 deletes                                    | 6u.7           |
| 6t.3 reuses 6s.11's cycler project helpers                        | Those helpers read frontmatter `scheduled` and use `^prj`'s `[?]` as the resident signal. 6u.15 rewrites them                                                   | 6u.15          |
| 6t.4 step 3: MacBook only after 6s.12 closes                      | Already "satisfied". It would `git pull && just install` and `bob plugins sync` on the Mac mid-6u                                                              | 6u.16          |
| 6t.1 finish: keep §12.10 through 6s.13's docs sweep               | The note went to a canceled bead. 6u.17's plan doesn't know about §12.10                                                                                        | 6u.17          |

Evidence that 6t.2 took the wrong branch, from its stable reasoning checkpoint
(`codex_thinking.jsonl`):

> 6s.5 is closed and never landed, so the four-hour wait is unnecessary. … The agent will
> reuse 6s.2's shared project-dependency model for Rule step 3 instead of
> re-implementing 6s.5.
>
> … examining how `task_dependency_states` calculates open counts and how to detect
> completed tasks in YAML `depends_on` fields.

### 2. Both epics edit the same files (high severity for Rust, medium for plugins)

| File(s)                                                                         | 6t phase                                                                                   | 6u phase(s)                                                                                           |
| ------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------- |
| `src/native/projects/scan.rs`, `mod.rs`, `edits.rs`                             | 6t.2: `drain_state` (**already edited**), `normalize_task_hide_tag` made `pub(crate)`      | 6u.2 deletes `project_schedule_date` and the frontmatter reader and reverts `scan.rs` alias parsing; 6u.4 rewrites `edits.rs` paths |
| `src/native/project_dependencies/*`                                             | 6t.2 reads it for step 3                                                                   | 6u.2 deletes `parse.rs`, `format.rs`, `resolve_dependencies`                                          |
| `task_complete/successors.rs` (1488 lines), `capture/output.rs`                 | 6t.2: relaxed `[id::]` gate, pull-in verdicts, `trigger` / `hide_removed`, `surfaced` verb | 6u.7: `StillBlockedProject`, `project_member` recovery, `[unblocked::]`, `edit_line` changes          |
| `capture/pomodoro_close.rs`, `capture/task_complete.rs`                         | 6t.2: candidate detection in both close paths                                              | 6u.9 (`pomodoro_close.rs` link-then-close)                                                            |
| cycler `080`, `085` (about 24 lines of headroom), `135` / `136`, `fragments.json`, manifest | 6t.3: new `088` (**already written**), `085` (**already edited**), planned `137`, `136` | 6u.15: `080` helpers, `085` ~771 and ~858–886, a new fragment, manifest                               |
| nav `285-unblocked-notice.js`, nav manifest, nav deploy                         | 6t.3: bumps "from master" (2.19.0 → **2.20.0**) and deploys nav on this host               | 6u.11 must salvage the **uncommitted 2.20.0 bundle still deployed here** and release 2.21.0           |

Whichever epic lands second gets merge conflicts. The danger is a silent semantic
overwrite. One example: 6u.2's instruction to revert `scan.rs` helpers from
`54a54bf^` would delete 6t.2's `drain_state` if applied wholesale. Another: 6t.2's step
3 would call a deleted module, and 6u.2 would have to rewrite it outside its scope.

### 3. Rollout order (high severity if 6t.4 runs before 6u.16)

6u's Design §7 / ADJ-10 exists because an old `bob projects sync` on the MacBook cron
deletes inline `^prj` dates. 6t.4 would install master bob on the Mac mid-6u and then
run `bob plugins sync` there, pushing every plugin bundle. That would put a partial 6u
on the Mac's live 15-minute `projects sync` / `reconcile` cron against the vault, plus
6s.11's whole-vault-read cycler. 6u's own plan states that "Nothing reached the MacBook"
and depends on that.

### 4. Contract drift in §12.10 (low; already being repaired)

6t.1's landed §12.10 / §12.11 uses YAML-model terms:

- Rule step 3 ("N has project reasons", from 6s.5);
- PP7 (a future project `scheduled` gives `reason: project`);
- PP8 and the Gate (project `depends_on`);
- Trigger (b) ("derived field for a `depends_on` property").

Under 6u's Design §2, `^prj` "reports only its own reasons". So step 3 folds into steps
1–2, and PP7's reason becomes `scheduled`.

**6u.1 has already noticed this on its own.** Its reasoning log says it is correcting
PP7 to `still_blocked{reason: scheduled}`, dropping PP8's `depends_on` clause, removing
§12.10's YAML references, and keeping step 3 as a redundant safety net. Once 6u.1 lands,
6t.2's tests written from the old PP7 would contradict the contract.

There is one gap neither plan covers. §12.10 Writes says "Nothing else changes". But the
pull-in's **recover-rank** path (R `[?]` → `[ ]` when not linked: PP10, PP11, PP18) is
an automatic Blocked → Ready recovery. 6u's Design §4 requires every such recovery to
write `[unblocked::]`. The linked `?` → `*` path lands in Next and is correctly
skipped. I put this on 6u.1, 6u.7 and 6u.17.

### What does *not* conflict

- **Never linking a Blocked task.** A pulled-in `^prj` passes Rule steps 1–3 first, so
  it is never Blocked when linked. 6u's §5 consumption and "capture never links a
  Blocked task" hold.
- **`#prj_is_blocked` never goes on `^prj`**, so the pull-in's line write needs no tag
  handling. The only requirement is that 6t's display stripping of `#prj` / `#hide` is
  token-bounded.
- **Remaining work.** 6t's REMAINING counts `[?]` tasks as remaining work. Under 6u,
  residents of a blocked project are `[?]`, but then `^prj` itself is still blocked and
  the pull-in reports `still_blocked`. Both rules agree.
- **Sticky lanes and Alt+N release** (`decisions:task-lanes-are-sticky`), ADJ-11
  promotion, sync's `#hide` predicate, and the "no sub-project cascade" choice are the
  same in both plans.
- **Memory.** 6t edits no memory (`decision_record = no`). 6u.17 owns all decision and
  glossary edits.

## Options

| Option                                                         | Verdict                                                                                                                                                                                                                                                                                                         |
| -------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A. Run both in parallel as is                                  | **No.** 6t.2 lands code on a model that 6u.2 deletes, and 6t.4 can reach the Mac out of order. My bead notes reduce the risk, but a running agent may not re-read its bead before it finishes                                                                                                                  |
| B. **Stop 6t's phases and re-plan 6t after 6u** (recommended)  | About 20 minutes of uncommitted agent work is lost. The contract survives: 6u.1 is porting it. A re-plan can be small: cli after 6u.7 and 6u.9, plugins after 6u.15 and 6u.14, rollout riding along with 6u.16                                                                                                 |
| C. Keep the 6t epic but re-sequence it in place                | Cheaper than a re-plan, but the 6t plan text is full of 6s gates and an overlap table that agents follow literally. Cross-epic bead dependencies are not something I verified the runner honors for already-launched, waiting agents                                                                           |
| D. Stop or re-plan 6u                                          | **No.** 6u is the model you chose, much larger, and 6t depends on it, not the other way round                                                                                                                                                                                                                  |

## Next actions

1. **Now: stop 6t's agents.** 6t.2 and 6t.3 are mid-implementation and nothing of
   theirs is on master. Kill the waiting 6t.4 and the land agent too, so nothing
   reaches the Mac.

   ```bash
   sase agent kill -n bob-cli-6t.2
   sase agent kill -n bob-cli-6t.3
   sase agent kill -n bob-cli-6t.4
   sase agent kill -n bob-cli-6t.land
   ```

   Do not revert `ec7251e`. 6u.1 is rewriting §12.10 in place.

2. **Close out 6t the way you closed 6s:** resolution `canceled`, with a reason
   pointing here. The phase beads are still open, so the close needs `--force` with a
   non-`done` resolution:

   ```bash
   sase bead close bob-cli-6t --force -R canceled \
     --reason "Planned against canceled bob-cli-6s; re-plan on bob-cli-6u's ^prj-line model (research:202610/bob_cli_6t_6u_epic_conflict.md)"
   ```

3. **Leave 6u running.** Check 6u.1's commit when it lands: §12.10 should no longer
   mention `depends_on` or frontmatter `scheduled`, and PP7 should say `scheduled`. If
   the `[unblocked::]` gap isn't covered, it is already noted on 6u.7 and 6u.17.

4. **Re-plan the pull-in once 6u.7 and 6u.15 have landed.** You could start right away
   with explicit dependencies, but waiting avoids planning against moving code. Ask the
   planner to:
   - reuse §12.10 / §12.11 as ported by 6u.1, with no new contract phase unless 6u.1
     left gaps;
   - in Rust, build on 6u.7's verdicts in `successors.rs` / `recovery.rs`, read the
     `^prj` inline date and Depends-On line (never frontmatter), make the recover-rank
     path write `[unblocked::]`, fire 6u.7's `project_member` cascade even when a
     pull-in replaces the `project_task` row, and strip `#prj` / `#hide` token-bounded;
   - in the plugins, build on 6u.15's helpers and `api.freshness.markUnblockedLine`
     (v12), follow 6u.1's reason kinds in nav `285`, and bump nav from at least 2.21.0;
   - for rollout, ride along with 6u.16 if it hasn't run yet, otherwise install after
     it. Never touch the Mac before 6u.16 closes.

5. **If you decide to let 6t keep running anyway (option A/C),** do at least this:

   ```bash
   sase bead dep add bob-cli-6t.4 bob-cli-6u.16
   ```

   Then watch 6t.2's commit: it must not import `project_dependencies::*` or read
   frontmatter `scheduled`. My notes on 6t.2, 6t.3 and 6t.4 tell those agents the same
   thing, but they may not re-read their beads before finishing.

6. **Optional process fix.** "Wait until bead X is closed" gates in plans should check
   `resolution: done`, not just `closed`. That is how 6t.2 and 6t.4 got fooled. Worth a
   line in the epic-planning prompt or a sase feature request.

## Notes left on beads

I appended the notes below to 13 beads with `sase bead update <id> -n @<file>`, posted
at about 10:46 EDT. Each is reproduced verbatim.

### `bob-cli-6t` (epic)

```text
COORDINATION — CONFLICT WITH bob-cli-6u (checked 2026-10-12 10:45 EDT, agent 72). This epic was planned against bob-cli-6s. Bryan canceled 6s at 09:46 EDT and replaced it with bob-cli-6u (plan:202610/prj_line_project_blocking.md, the ^prj-line model). Every 6s bead now reads CLOSED (resolution: canceled), so this plan's "wait until 6s.X is closed" gates pass even though the code they wait for never landed.
1. 6t.2 (cli): 6s.5's §12.2 step-3 project verdict never landed. The running agent decided to "borrow the project-blocked verdict from 6s.2" (the YAML model in src/native/project_dependencies/ plus frontmatter depends_on/scheduled), which 6u.2 deletes. It is editing projects/scan.rs, mod.rs and edits.rs (6u.2 and 6u.4 rewrite these). It will edit successors.rs and capture/output.rs (6u.7 rewrites these) and pomodoro_close.rs (6u.9 rewrites it).
2. 6t.3 (plugins): reuses 6s.11's cycler helpers, which read frontmatter scheduled and treat ^prj's [?] as the resident signal; 6u.15 rewrites them. It shares 085's ~24 lines of headroom with 6u.15. Its nav bump "from master" (2.19.0 → 2.20.0) collides with the uncommitted 2.20.0 bundle still deployed on this host, which 6u.11 must salvage and must not reuse.
3. 6t.4 (rollout): "MacBook only after 6s.12 closes" is now vacuously true. It would run just install plus bob plugins sync on the MacBook in the middle of 6u, breaking 6u's ADJ-10 order (Mac bob → this host → Mac plugins, owned by 6u.16).
4. The landed §12.10/§12.11 contract (ec7251e) uses YAML-model terms. These are Rule step 3, PP7 (project scheduled → reason project), PP8 and the Gate (project depends_on), and Trigger (b) (a depends_on property). Under 6u, ^prj reports only its own reasons, so step 3 folds into steps 1–2 and PP7's reason becomes scheduled. The recover-rank path (R ? → space) is an automatic Blocked→Ready recovery, so under 6u Design §4 it must write [unblocked::]. §12.10 Writes says "Nothing else changes", which forbids that.
The pull-in requirement itself is compatible with 6u: a pulled-in ^prj is never Blocked, and ^prj never carries #prj_is_blocked. Only this plan's substrate, sequencing, and file ownership conflict. Recommendation: stop 6t.2/6t.3 and re-sequence 6t after 6u. Details: research:202610/bob_cli_6t_6u_epic_conflict.md.
```

### `bob-cli-6t.2` (cli, running)

```text
COORDINATION — DO NOT LAND AGAINST THE 6s.2 YAML MODEL (conflict with bob-cli-6u). bob-cli-6s.5 reads CLOSED only because Bryan canceled 6s. Its step-3 verdict never landed and never will. 6s's replacement, bob-cli-6u (plan:202610/prj_line_project_blocking.md), removes what this phase is borrowing:
- 6u.2 deletes project_dependencies/parse.rs and format.rs, resolve_dependencies/Openness, projects/scan.rs project_schedule_date, and the frontmatter list reader. It also reverts scan.rs alias parsing.
- 6u.4 makes ^prj's inline [scheduled::] the project date, hoists frontmatter scheduled, and rewrites parts of projects/edits.rs and scan.rs.
- 6u.7 owns the StillBlockedProject verdict, project_member recovery, and [unblocked::] writes in successors.rs, recovery.rs, and capture/output.rs.
Under 6u Design §2, ^prj "reports only its own reasons". §12.10 Rule step 3 is therefore vacuous for R, because steps 1–2 (R's own [dependsOn::] and R's inline [scheduled::]) already cover it. Do not read frontmatter depends_on/scheduled or call project_dependencies::* for step 3, the Gate, or DrainState's future date. The 6u plan is the newer, Bryan-chosen model, so prefer it wherever the two plans disagree on project storage or blocking.
Other 6u points that touch this phase:
(a) The recover-rank path (R ? → space, as in PP10/PP11 when R was [?]) must write [unblocked::] through 6u.3's mark_unblocked once that lands.
(b) Strip #prj/#hide from display text token-bounded, so #prj_is_blocked is never mangled.
(c) 6u.4 moves the Sub-projects marker after ^prj's Depends-On line, so do not assume it is the first child.
Safest course: stop here, record your diff and findings on this bead, and let Bryan re-sequence this phase after 6u.2/6u.4/6u.7. See research:202610/bob_cli_6t_6u_epic_conflict.md.
```

### `bob-cli-6t.3` (plugins, running)

```text
COORDINATION — conflict with bob-cli-6u (6s's replacement, the ^prj-line model). The 6s.11 cycler helpers this phase reuses for Rule step 3 (projectDependencyInfo and projectIsBlockedAfter in 080, still_blocked scheduled in 085 ~771) read frontmatter scheduled and treat ^prj's [?] as the resident signal. bob-cli-6u.15 (plugins-compat) rewrites them to read ^prj's inline [scheduled::] and each resident's #prj_is_blocked tag. It also edits 085 (~771, pushRecover ~858-886) and the 135 live/vault writers.
1. Do not add frontmatter depends_on/scheduled parsing. Under 6u, ^prj has only its own reasons (Rule steps 1–2).
2. 085's ~24 lines of headroom and the fragments.json/mixin registration are shared with 6u.15. Name your claimed fragment numbers (088, 137) in a note so 6u.15 avoids them.
3. Nav: master is 2.19.0, but the deployed nav bundle on this host is the uncommitted 6s.8 build 2.20.0. 6u.11 must salvage it and release 2.21.0. Do not use 2.20.0 for your bump. Do not run bob plugins sync -p bob-navigation-hotkeys on this host before 6u.11 has salvaged that bundle (a sync backs up to ~/.local/state/bob-cli/plugin-backups/, but that is a fallback).
4. 285's still_blocked reason "project" copy: 6u.1 is rewriting the reason kinds right now (local_dependency, local_schedule, project_dependency, project_schedule). Follow the contract that lands, not 6s's §12.5.
5. Recover-rank writes (? → space) must add [unblocked::] through api.freshness.markUnblockedLine (namespace v12, from 6u.10).
Safest course: stop before deploying or landing, and let Bryan re-sequence this phase after 6u.15 (and 6u.11 for nav). See research:202610/bob_cli_6t_6u_epic_conflict.md.
```

### `bob-cli-6t.4` (rollout, waiting)

```text
COORDINATION — DO NOT TOUCH THE MACBOOK UNTIL bob-cli-6u.16 CLOSES. The plan's gate "MacBook only after bob-cli-6s.12 is closed" is vacuously true: 6s.12 is CLOSED with resolution canceled, because Bryan replaced 6s with bob-cli-6u. 6u's ADJ-10 order is bob on the MacBook first, then verify the hoist and reconcile, then this host, then MacBook plugins, all owned by 6u.16. An old Mac projects sync deletes inline ^prj dates. A git pull + just install + bob plugins sync on the Mac mid-6u would put a partial 6u bob on the Mac's 15-minute cron, writing live to the vault, and push 6s.11/6u plugin bundles out of order. Read every "6s.12" in the plan as "6u.16". If 6u.16 is not closed, leave the Mac alone and append a note to bob-cli-6u.16 saying its install and sync also carry the project pull-in. On this host, 6u also puts just install after the Mac, so prefer to wait for 6u.16 step 2 or ask Bryan. Bryan may add the dep bob-cli-6t.4 → bob-cli-6u.16. See research:202610/bob_cli_6t_6u_epic_conflict.md.
```

### `bob-cli-6u` (epic)

```text
COORDINATION — concurrent epic bob-cli-6t (project pull-in, plan:202610/project_task_pull_in.md) was planned against canceled 6s and is running now (6t.2 and 6t.3 started 10:28 EDT). Impact on this epic:
1. ec7251e (6t.1, landed) added docs/task-dependencies.md §12.10 "Project pull-in" and §12.11 PP1–PP24. It also added a §13.4 sentence: ADJ-11 governs dependency promotion, and the §12.10 close-gesture pull-in is the one path that makes ^prj Next. Pointers went into docs/projects.md, plan.md, capture.md and README. 6t.1's "keep this through the sweep" note went to canceled 6s.13, so this plan never lists it. Keep §12.10, and port its YAML-model wording (Rule step 3, PP7, PP8, the Gate, Trigger (b), PP17) to the line model.
2. 6t.2 is adding drain_state/DrainState in projects/scan.rs, mod.rs and edits.rs (and making normalize_task_hide_tag pub(crate)). It will add task_complete/project_pull_in.rs and edit successors.rs, capture/output.rs, task_complete.rs and pomodoro_close.rs. It takes step 3 from the 6s.2 YAML model. If it lands before 6u.2/6u.4/6u.7, carry its callers over to the line model; do not revert them, and do not restore scan.rs wholesale from 54a54bf^.
3. 6t.3 is adding task-status-cycler 088 (and a planned 137 mixin), and editing 085, 136, nav 285 and the nav manifest. That overlaps 6u.15 and 6u.11.
4. 6t.4 would reach the MacBook early because 6s.12 reads closed. A note on 6t.4 redirects it to 6u.16.
I asked 6t.2/6t.3 not to land against the YAML model. Bryan decides whether to stop or re-sequence 6t. See research:202610/bob_cli_6t_6u_epic_conflict.md.
```

### `bob-cli-6u.1` (contract, running)

```text
COORDINATION — docs/task-dependencies.md §12.10 "Project pull-in" and §12.11 PP1–PP24 landed in ec7251e (bob-cli-6t.1) just before this phase started. This plan's §12/§13 repair tables do not list them. While rewriting §13, §12.5 and §12.2:
(a) Keep the §13.4 sentence naming §12.10 as the one close-gesture path that makes ^prj Next.
(b) Port §12.10's YAML-model wording:
- Rule step 3 "N has project reasons (§13.3)" is vacuous under Design §2, because ^prj reports only its own reasons. Fold it into steps 1–2.
- PP7: a future project date is now R's own inline [scheduled::], so the result is still_blocked{reason: scheduled}, not reason project.
- PP8: "or project depends_on" becomes R's own Depends-On line.
- Drop the Gate's "or N has a non-empty depends_on key".
- Drop Trigger (b)'s "including the derived field for a depends_on property".
- PP17's "legacy internal Depends-On line": internal ^prj targets are kept on the line but never projected, so R qualifies through trigger (a) only and there is no project_task row to beat.
(c) §12.10 Writes says "Nothing else changes". The recover-rank path (R ? → space; PP10/PP11/PP18 when R was [?]) is an automatic Blocked→Ready recovery, so it writes [unblocked::] per the new freshness §5. The linked ? → * path lands in Next and is skipped.
If this is out of scope, record a PROPOSED FOLLOW-UP so 6u.17 picks it up. See research:202610/bob_cli_6t_6u_epic_conflict.md.
```

### `bob-cli-6u.2` (cli-model)

```text
COORDINATION — bob-cli-6t.2 (project pull-in, running since 10:28 EDT) is editing src/native/projects/scan.rs, mod.rs and edits.rs. It adds a crate-visible drain_state/DrainState that wraps parse_project (open_unhidden_count, unstruck Sub-projects children, the project's future schedule) and makes edits::normalize_task_hide_tag pub(crate). Its reasoning log says it takes §12.10 Rule step 3 from 6s.2's YAML model (project_dependencies::*, frontmatter scheduled/depends_on), because 6s.5 never landed. Before starting, run git log origin/master -- src/native/projects src/native/task_complete. If 6t.2 has landed: revert only the alias helpers from 54a54bf^ (never restore scan.rs wholesale), keep drain_state, and re-point its schedule and project-reason inputs to the ^prj line rather than deleting its callers. See research:202610/bob_cli_6t_6u_epic_conflict.md.
```

### `bob-cli-6u.4` (cli-projects)

```text
COORDINATION — bob-cli-6t.2 (project pull-in, §12.10) relies on projects::edits::normalize_task_hide_tag (made pub(crate)) for byte-identical #hide removal (PP22). Its PP23 asserts that after a pull-in, bob projects sync --dry-run reports no change for the project. If it has landed, keep that helper's bytes and visibility. Point DrainState's future-schedule input at ^prj's inline date, and keep PP23 passing after the hoist and the Sub-projects reorder (marker after the Depends-On line). The pull-in's SUBOPEN check reads that marker line. See research:202610/bob_cli_6t_6u_epic_conflict.md.
```

### `bob-cli-6u.7` (cli-close)

```text
COORDINATION — bob-cli-6t.2 (project pull-in, §12.10, running) adds task_complete/project_pull_in.rs and wires it into plan_successors. The wiring relaxes the [id::] gate and lets a pull-in verdict replace Recover("project_task") for an emptied project's ^prj. It adds trigger/hide_removed to UnblockedRow and StillBlockedRow and a surfaced verb in capture/output.rs. It was planned to build on 6s.5's project verdict, which never landed; this phase now owns that verdict. Whichever lands second must merge, not overwrite:
(1) StillBlockedProject applies to residents only. ^prj has only its own reasons (Design §2), which §12.10 steps 1–2 already cover.
(2) The project_member cascade must fire whenever ^prj recovers, including when the pull-in verdict replaced the project_task row. An emptied N can still hold [?] residents tagged #hide, because §12.10's REMAINING skips #hide lines.
(3) The pull-in's recover-rank path (? → space) writes [unblocked::] through mark_unblocked like every other Ready recovery. The linked ? → * path skips it.
(4) successors.rs is 1488 lines and both plans say to put new logic in new modules.
See research:202610/bob_cli_6t_6u_epic_conflict.md.
```

### `bob-cli-6u.11` (nav-model)

```text
COORDINATION — bob-cli-6t.3 (project pull-in plugins phase, running) edits nav 285-unblocked-notice.js: project rows, a "Project empty" title, a project_member label, and "blocked by project" copy. Its plan bumps the nav manifest "from the latest master version" (2.19.0) and deploys nav on this host. A note on 6t.3 asks it to skip 2.20.0 and to leave the deploy until after your salvage. As of 10:45 EDT the deployed ~/bob/.obsidian/plugins/bob-navigation-hotkeys/manifest.json still says 2.20.0. Re-check before you start. If it was replaced, use the newest ~/.local/state/bob-cli/plugin-backups/<ts>/bob-navigation-hotkeys copy whose manifest says 2.20.0. If 6t.3's nav commit landed, rebase on it, merge 285 and the README/package.json rows, and bump from the higher version. See research:202610/bob_cli_6t_6u_epic_conflict.md.
```

### `bob-cli-6u.15` (plugins-compat)

```text
COORDINATION — bob-cli-6t.3 (running) adds task-status-cycler fragment 088-successor-project.js (projectDrainState, removeProjectHideTags, planProjectPullIns). It edits 085-successor-plan.js (relaxed gate, one row per R, breaker exemption, trigger/hide_removed) and plans a 137-plugin-successor-project.js mixin and 136 receipt changes. It reuses projectDependencyInfo/projectIsBlockedAfter (080) for its step 3. When you move those helpers to the inline ^prj date and the #prj_is_blocked signal, update 6t.3's callers too, and include its recover-rank writes (? → space) in your [unblocked::] rewrite. 085's headroom is shared, so avoid its fragment numbers. See research:202610/bob_cli_6t_6u_epic_conflict.md.
```

### `bob-cli-6u.16` (rollout)

```text
COORDINATION — bob-cli-6t.4 (project pull-in rollout) is gated on canceled 6s.12, which reads CLOSED, so it may reach the MacBook before you do. A note on 6t.4 redirects it to wait for this bead. Before step 1, read bob-cli-6t.4's notes. If it already ran just install or bob plugins sync on the Mac, record the Mac's bob commit and plugin versions, and check the vault for early hoists, tags and [unblocked::] writes. If 6t's code has landed, your install and sync carry the project pull-in: add one pilot (close a project's last task through its link, then check the ^prj link, [*], and that #hide is gone). See research:202610/bob_cli_6t_6u_epic_conflict.md.
```

### `bob-cli-6u.17` (publish)

```text
COORDINATION — In the docs sweep, keep docs/task-dependencies.md §12.10 "Project pull-in", §12.11 PP vectors (bob-cli-6t, ec7251e) and the §13.4 sentence naming §12.10. 6t.1's keep-request went to canceled 6s.13. If 6u.1 didn't port them, fix §12.10's YAML-model wording: project depends_on and frontmatter scheduled, Rule step 3 project reasons for ^prj, and PP7/PP8/PP17. Also make the recover-rank path write [unblocked::]. Add "depends_on key" and "derived field for a depends_on property" to the rg list. bob-cli-6t skipped its decision record (decision_record=no); if one is written later, it should link [[decisions/projects-block-from-prj-line]]. See research:202610/bob_cli_6t_6u_epic_conflict.md.
```
