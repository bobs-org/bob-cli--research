# Project `scheduled` and `depends_on` back on the `^prj` task, `#prj_is_blocked`, and a review guarantee for unblocked tasks

> **Research query:** Move the project note's `scheduled` and `depends_on` frontmatter
> fields back onto the project's `^prj` task. Check that frontmatter is not needed and
> that nothing breaks. Add a `#prj_is_blocked` tag to every task that is Blocked only
> because its project is blocked. Make sure that **every** task that becomes unblocked,
> for any reason (a project's `scheduled` date arriving included), is reviewed in the
> next morning GTD review at the latest, unless it was pulled into today's ledger as a
> successor. Is this a good idea, what should change, and how should it be built?

Checked **Monday, October 12, 2026, about 09:30 EDT** against:

- bob-cli `75e323b` (master);
- bob-plugins `3208e8c` (origin/master, which landed at 09:15 today);
- the live `~/bob` vault (read-only);
- the state of epic `bob-cli-6s`.

Builds on `research:202610/unblocked_task_review_guarantee.md` and
`research:202610/project_dependency_blocking/project_dependency_blocking.md`.

## Bottom line

- **Yes: move both fields back onto `^prj`.** Frontmatter is not needed, and nothing
  that ships today depends on it:
  - no vault query reads project `scheduled` or `depends_on`;
  - no project note uses `depends_on`;
  - only 14 projects use `scheduled`, and only one of those dates is in the future.

  The `^prj` line model already works with zero code changes for:
  - reconcile's Blocked rule;
  - the R1–R10 dependency rules;
  - successor recovery;
  - the Depends on stage;
  - the ledger chips.

  `job_apply_to_databricks.md` is live proof. Frontmatter was the odd one out: the
  project design already says "the task line is the interaction point"
  (`docs/projects.md:19-21`).
- **Do it as a re-plan of `bob-cli-6s`, today, not as a follow-up.** The epic is
  running right now:
  - two phases are writing the YAML `depends_on` reader and splice writer;
  - one plugin phase has already landed code that reads frontmatter `scheduled`;
  - nine more phases are queued, and three of them (`.3`, `.9`, `.10`) are mostly YAML
    plumbing.

  Every hour they run produces code this change deletes.
- **Projects still block their tasks.** Only storage moves. The rule gets simpler: *a
  task in a project note is Blocked while that project's `^prj` task has its own reason
  to be Blocked* (an open prerequisite on its Depends-On line, or a future inline
  `scheduled`).
- **`#prj_is_blocked`: yes, with one adjustment.** Tag **every** open task in a blocked
  project, not only the tasks whose *only* reason is the project (ADJ-3). The tag then
  states a fact about the project:
  - it never flips when a task's own reasons change;
  - it touches far fewer writers;
  - a task with two reasons shows both.
- **The review guarantee is not true today, and it would not be true after
  `bob-cli-6s` as planned.** Under the plan, project members recover "recover-only,
  never linked", with their old `[fresh::]` stamp. They can sit FRESH, outside the
  walk, for up to 6 mornings.
- **Recommended fix: record the unblock and classify it at read time.** Every
  *automatic* Blocked → Ready recovery writes `[unblocked:: YYYY-MM-DD]`. The evaluators
  treat it like an arrived `scheduled` date, so the task becomes TICKLER (a commitment
  tier) the next morning. Any stamp removes the field.
  - The read-time-only alternative from the earlier report (`returned_on` from
    prerequisite completion dates) leaves exactly the gaps you care about: a project
    you unblock yourself by removing its prerequisite or its date from `^prj`.

## Do this first: the epic is in flight

| Phase | State at 09:30 | YAML-specific work this change deletes |
| --- | --- | --- |
| `.1` contract | ✅ landed (`75e323b`) | §13.2 storage, §13.7 R0 hoist and property R-rules, PDP/PDW vectors, most of PDR |
| `.2` cli-model | ⏳ running | the generalised frontmatter list reader and `splice_depends_on` |
| `.8` nav-model | ⏳ running (uncommitted 739-line `215-project-dependencies.js`) | `parseProjectDependsOn`, `planProjectDependsOnSplice`, harness YAML parsing |
| `.11` plugins-compat | ✅ landed (bob-plugins `3208e8c`) | Little: it already reads `^prj`'s **inline** `[dependsOn::]`. Its two frontmatter `scheduled` readers need a small follow-up |
| `.3` reconcile-deps | queued | most of it (R0 hoist, property R-rules, D3); the implicit resident edges survive |
| `.9` nav-stage | queued | the `project-dependencies` descriptor, the property splice, the audit of 11 fragments |
| `.10` nav-convert-move | queued | YAML on conversion (the line simply moves instead) |
| `.4`–`.7`, `.12`, `.13` | queued | Their non-storage halves (inheritance, consumption, guards, rollout, publish) all survive |

**Recommendation:** stop `bob-cli-6s.2` and `.8`, and keep the queued phases from
starting. Then amend `plan:202610/prj_task_dep_links.md` along the lines of
[Recommended solution](#recommended-solution) and relaunch. If you would rather let
`.2`/`.8` finish, their project recognition, openness, ADJ-11, and recovery-gate parts
are reusable. Only their YAML parts become dead code to remove.

The memory phase (`.13`) has not run. So the new decision record can state the inline
model from the start, and no record has to be superseded the day it is accepted.

## Verification: does dropping the frontmatter break anything?

### The vault

- **Project notes:** 85 active, 0 in `done/`.
- **Frontmatter `scheduled`:** 14 notes.
  - 10 are on wip projects: 1 future date (`sase_message_boards.md`, 2026-10-16, with 0
    open residents) and 9 past dates.
  - 4 are on terminal projects.
- **Frontmatter `depends_on`:** 0 notes.
- **`^prj` lines:**
  - 0 carry an inline `scheduled`;
  - 1 has a Depends-On child and a `[dependsOn::]` field (`job_apply_to_databricks.md`,
    already in the target shape);
  - all 34 wip `^prj` lines carry `#hide`.
- **Queries:** none read project-level `scheduled` or `depends_on`. That covers:
  - the 28 `tasks` blocks;
  - the 2 `dataviewjs` blocks;
  - the 5 `.base` files.

  `projects.base` uses `type`, `status`, `parent`, `priority`, `task_count`,
  `open_task_count`, and `title`, but never `scheduled`.
- **Templates:** `_templates/new_project.md` has no `scheduled:`.
  `.obsidian/types.json` declares `scheduled: date` generically, which is harmless.
- **Your own note** `bob.md:27-28` ("Migrate `depends_on` and `scheduled` back to
  project task!" / "start adding `#prj_is_blocked` tags to blocked child tasks!")
  confirms that "parent" means the project the task lives in (ADJ-2).

### What already works on the `^prj` line, with no code change

| Surface | Evidence |
| --- | --- |
| Reconcile's Blocked rule sees an inline future `scheduled` on `^prj`; there is no `^prj` exclusion | `task_status_hooks/sync.rs:525-529` and `task_transition` `:746-770` |
| R1–R10 reconcile a Depends-On line under `^prj` like any other task | `reconcile.rs` `plan_dependent` (437-494) has no block-id check, and the field writer is already tested on `^prj` shapes (`reconcile/fields.rs:174-185`). Live: Databricks `^prj` is `[?]` from its line |
| Successor recovery keeps a future-dated `^prj` Blocked | `task_complete/successors.rs` checks step 2 (scheduled) before step 4 (`project_task`); vector SL11 |
| The nav Depends on stage, the card's `b` key, and api v3 `openDependencyStageForRef` / `removeDependencyByRef` all accept `^prj` | no `^prj` refusal anywhere in `070`, `080`, `300`, `310`, `590`, or `600` |
| Ledger chips render on a `^prj` Depends-On line, and date marks render `[scheduled::]` | `140-*.js:183` `dependencyChipLineOwnedByTask` only needs a `#task` checkbox parent; `136-*.js` date marks have no `^prj` case |
| Tasks' `is blocked` sees `^prj` | the derived `[dependsOn::]` field, as today; the vault uses `taskFormat: dataview` |

The "nicer view" claim holds:
- `^prj` gets live chips and date marks for free;
- a chip that points at a project (`[[x#^prj]]`) gains the project's date in its tooltip
  (`140-*.js:763-776` reads the target's Tasks-cache `scheduled`);
- the earlier report's "v2 chips from YAML" follow-up becomes unnecessary.

### What must change

| # | Today | Change |
| --- | --- | --- |
| 1 | **`bob projects sync` deletes any inline `scheduled` on an open `^prj`** ("scheduled is no longer used"; `projects/sync.rs:681-685`, `edits.rs:14-16,47-55,136-139,400-433`) | Remove that path, and read the project date from `^prj`'s inline field (`parse_inline_schedule_date`, `tags.rs:166-170`). **This is the rollout hazard:** an old `sync` on the MacBook cron (`:05/:20/:35/:50`) would silently erase every newly written `^prj` date |
| 2 | Sync's propagation, `#hide` forcing, and Sub-projects `🗓️` marker read `Project.scheduled` from frontmatter (`scan.rs:200-251`, `sync.rs:462-465,514-573,582`) | Same logic, with the source switched to `^prj` inline. Schedule issues become per-line issues; re-key `issues_allow_subproject` (`sync.rs:373-379`) |
| 3 | Capture `+` writes frontmatter `scheduled` and a dateless `[?]` `^prj` (`capture_project_note.rs:282-288,389-391`) | Write `[scheduled:: P]` on `^prj`. This fixes the known flip-back where reconcile recovers that `[?]` |
| 4 | nav strips inline `scheduled` from `^prj` (`250:663`, `260:25`, `260:540-551`) and routes `scheduled` on `^prj` to `kind: "project-frontmatter"` (20 checks in 11 fragments) | Collapse into the ordinary inline Schedule path. Keep the two project side effects: propagation to residents and the `#hide` toggle. Drop the `^prj` recovery and prune exclusions (`580:126,130`, `610:21`). Stamps then follow the normal rule, so freshness.md's "project-frontmatter edits never stamp" goes away |
| 5 | The child-note picker's `calendar-clock` chip reads child frontmatter (`190:324,363,379`) | Read the child's `^prj` line (`cachedRead`, or the Tasks cache nav already uses for candidate badges) |
| 6 | Create-project-note-from-task copies the source `[scheduled::]` into frontmatter (`100:288,361`, `110:709-717`) and seeds a Depends-On child as a fake `## Tasks` row (`110:1`) | Keep both on `^prj`: the field stays on the line, and the Depends-On line becomes `^prj`'s first child, with same-note links rebased (`[[#^a]]` → `[[source#^a]]`). Reverse already prefers an inline date (`project-reversal.cjs:315-328`) and carries children (`210:846`); it only needs links re-formed relative to the destination, the Sub-projects line skipped, and `[?]` accepted (`210:791`) |
| 7 | bob-plugins `3208e8c`: `projectDependencyInfo` (cycler `080:170-191`) and `parseProjectFrontmatter` (block-id-prompt `030:384-420`) read frontmatter `scheduled` | Read `^prj`'s inline `scheduled`. Both helpers already read the `^prj` line for `[dependsOn::]` |
| 8 | Sync inserts the Sub-projects line as `^prj`'s **first** child (`edits.rs:483-496`), which displaces a Depends-On line | Insert it after the Depends-On line, and after a Cancel Log that holds the first slot. Optionally move a misplaced marker line (sync owns it) |
| 9 | Docs, help text, and tests | `docs/projects.md` (about 12 spots), `docs/task-dependencies.md` §2.1 and §13, `docs/task-status-hooks.md:384-437`, `docs/capture.md:1289,2777-2789,2822`, `docs/freshness.md:450-456,513`, `docs/randomize.md:75`, and `README.md:796-806`. Help text in `projects/mod.rs`, `task_status_hooks/mod.rs:107-108`, `capture/cli.rs:365-366`, and `projects/output.rs:153`. About 20 tests pin the frontmatter model (`tests/cli/projects/schedule.rs` all 6, `projects/tests/*`, `tests/cli/task_status_hooks/blocked.rs:131-152`, `tests/cli/freshness.rs:1189-1196`, and the capture project-note tests) |

### What is actually lost

- **Properties-pane and Bases queries on a project's date or prerequisites.** Nobody uses
  them today. If a "projects by start date" view is ever wanted, use one of:
  - a Tasks query on `#prj` with `scheduled`;
  - a `bob projects list` column;
  - a machine-written mirror (the way `status` and `task_count` are synced *from* the
    task today).

  None is needed now.
- **The cheap `metadataCache` frontmatter read** in nav's child picker. A `cachedRead`
  of about 85 small project notes is cheap.
- **A longer `^prj` line.** `[scheduled::]` and `[dependsOn::]` join `#hide`, `[id::]`,
  `[fresh::]`, and `[priority::]`. The vault CSS snippet already shrinks `[dependsOn::]`
  to a glyph and hides `[id::]`.

## Is this a good idea?

**Yes.** These are the arguments that originally justified frontmatter, and where each
one stands now:

| Original argument for frontmatter | Status now |
| --- | --- |
| Bryan asked for it | Withdrawn |
| It frees the `^prj` first-child slot from the Sub-projects line | A one-branch sync fix (change 8). Depends-On first, Sub-projects second |
| Clean conversion mapping | The line mapping is *simpler*: line ↔ line and field ↔ field, with no YAML on either side |
| Queryable in Properties and Bases | 0 users; Tasks and Dataview already query the inline fields |
| `scheduled` precedent | That precedent is what this change reverses. `status` and `task_count` are synced *from* the task, which is the stated design |

Benefits beyond consistency:

1. **One dependency model, unchanged.** `decisions:task-deps-are-depends-on-links` holds
   for `^prj` with no exception, and it rejected "fields only with a virtual line"
   precisely because hand edits need a surface. This removes the YAML reader and splice
   writer, R0, D3, the R2 exception, malformed-property handling, and the Properties-pane
   blind spot from five engines: Rust hooks, Rust capture, nav, the cycler, and
   block-id-prompt. The "five engines drift" risk shrinks to the inheritance rule alone.
2. **The blocking rule gets simpler and self-describing.** A project is blocked exactly
   when its `^prj` would be Blocked as an ordinary task. The JS shortcut ("this note's
   `^prj` is `[?]`") becomes nearly exact.
3. **Known bugs disappear for free:**
   - capture's `[?]` `^prj` stops being recovered by reconcile;
   - nav's dependency removal stops recovering a future-dated `^prj` (`140:1` reads only
     inline);
   - the old cycler stops recovering a future-dated `^prj` on close;
   - a `^prj` resurfaces into PROJECTS when its date arrives, where today it never does.
4. **The migration is tiny.** For dependencies there is nothing to migrate: the only
   `^prj` dependency already lives on a line. For schedules it is 10 active projects.

What I would do differently from the request (all called out in the table below):

- re-plan the epic now, not later;
- broader tag semantics;
- a recorded unblock event rather than "mark as needing refresh" on its own;
- keep schedule propagation onto residents for now.

## Requirement adjustments

| # | As requested | Adjusted to | Why |
| --- | --- | --- | --- |
| **ADJ-1** | Migrate the fields back (implicitly after `bob-cli-6s`) | **Re-plan `bob-cli-6s` now.** Pause `.2`/`.8` and the queued phases, then amend §13 and the plan. Keep the epic's inheritance, consumption, ADJ-11, guards, and visibility | The storage half is a large share of the epic's remaining work (most of `.3`, and parts of `.2`, `.8`, `.9`, and `.10`), and it is the half being written right now |
| **ADJ-2** | "Blocked because its **parent** is blocked" | "Parent" means the **project note the task lives in** (its `^prj`), as in §13.1 residence: nested and `#ref` tasks included. **No** cascade through the `parent:` frontmatter of sub-projects (Q2 stands) | Matches `bob.md:28` ("blocked child tasks"). A `parent:` cascade would freeze most of the `sase` tree (29 wip sub-projects under wip parents) |
| **ADJ-3** | Tag tasks blocked **only** because of the project | Tag **every** open resident of a blocked project, whether or not it also has its own reasons. `^prj` itself is never tagged (its reasons are its own, visible on its line) | "Exactly why" needs both reasons visible on a task that has two. The tag flips only when the project changes, not when a task's own date or prerequisite changes, so only project-level writers maintain it. Under "only", every schedule and dependency writer would have to recompute it, and a resident of a scheduled project (which carries a propagated date) would never get the tag |
| **ADJ-4** | Add the tag | The tag is **machine-owned derived state**, like `[?]` and `#hide`. Reconcile is the authority and adds or strips it on open lines. Every writer that sets residents `[?]` or recovers them also adds or strips it in the same write. Closed lines are never edited | Same model as Blocked itself (`decisions:task-status-is-derived`). ADJ-4 of the earlier report ("nothing copied onto residents") rejected *copied dependency fields* because they collide with R1/R2. A tag does not |
| **ADJ-5** | "Marked as needing a refresh somehow" | An automatic Blocked → Ready recovery writes `[unblocked:: D]`. It is an *input*, like `scheduled`. Read-time classification makes the task TICKLER, and any stamp clears the field | Covers every unblock reason, including gestures on `^prj` that read-time inference cannot see ([details](#4-the-unblocked-task-review-guarantee)) |
| **ADJ-6** | "Regardless of the reason" | The guarantee covers **automatic** recoveries to **Ready**. Three other cases are already covered: a gesture on the task itself stamps it, which counts as reviewing it; a recovery to Next or Pending (successor link, live link, recent activity) is covered by the daily lane walk; a task whose own `scheduled` arrived is already TICKLER | Avoids writing a mark that would be immediately redundant. The lane walk covers lane tasks only while `next_interval` / `pending_interval` are not `false` |
| **ADJ-7** | Make sure this happens when a project's `scheduled` arrives | Already true for residents through their **propagated** `[scheduled:: P]` copies (TICKLER). `^prj` gains it through its own inline date. Residents without a copy are covered by ADJ-5 | Verified against `projects/edits.rs:101-163` and freshness §4 |
| **ADJ-8** | (unstated) | **Keep** `bob projects sync`'s propagation of the project date onto residents. Its source becomes `^prj` inline | Retiring it would also change `blocked.md`'s date sections, dash, and TICKLER sourcing. It is a separate decision (open question 3) |
| **ADJ-9** | (unstated) | `bob projects sync` hoists frontmatter `scheduled` to `^prj` inline, then deletes the key. Frontmatter wins when both exist. Terminal projects are left alone | Sync already owns project schedules and runs on cron. "Frontmatter wins" also makes it a compatibility shim for any old nav that still writes YAML |
| **ADJ-10** | (unstated) | **Rollout: bob on the MacBook first, then plugins**, as ADJ-13 of the earlier report. Here an old sync *deletes* data rather than re-adopting it | `projects/sync.rs:681-685` |
| **ADJ-11** | (unstated) | `blocked.md` gains a PROJECT section **keyed on the tag**, and STRANDED excludes it | The earlier report's filter read `task.file.property('depends_on')`, which no longer exists. The tag makes the section exact instead of approximate |

## Design

### 1. Storage and the effective-blocking rule

```markdown
---
type: "[[project]]"
status: wip
---
- [?] #task #prj Apply to DataBricks NYC role(s)! [fresh:: 2026-10-12] [scheduled:: 2026-10-20] #hide [dependsOn:: job__update-linkedin] ^prj
	- ⛓️ **DEPENDS ON:** [[job#^update-linkedin]]
	- 🧩 **Sub-projects:** …
## Tasks
### Blocked
- [?] #task #ref [[…databricks_nyc_cv_and_role_pitches|…]] #prj_is_blocked ^ref-databricks-nyc-cv-and-role-pitches
```

```text
own_reasons(T)   = open prerequisites on T's Depends-On line          (local_dependency)
                 ∪ { T.scheduled > today }                            (local_schedule)
project(T)       = the note T lives in, when: type project, non-terminal status,
                   exactly one open ^prj, not a canonical daily note   (unchanged §13.1)
project_blocked  = own_reasons(^prj) ≠ ∅, with internal targets (residents of the
                   same note) excluded from ^prj's prerequisites
T is Blocked     = own_reasons(T) ≠ ∅
                OR (T is a resident of project P AND project_blocked(P))
                   → reported as project_dependency / project_schedule
edges(T)         = T's own dep links ∪ (T is a resident ? ^prj's dep links : ∅)
```

- `^prj` is an ordinary task for R1–R10. There is no R0, no D3, and no YAML. Keep from
  §13: the guards, the cycle rule with implicit resident → project edges, ADJ-11 (never
  raise a `^prj` target into a lane), consumption, and the gesture rule.
- **Internal targets.** A `^prj` Depends-On link to a task in its own note is a
  guaranteed deadlock. Pickers refuse it; reconcile keeps the link but does not project
  it into `[dependsOn::]`, and warns `project_internal_dependency` (§13.6, unchanged in
  spirit).
- **Derive from reasons, not from the `[?]` cache.** In reconcile, compute `^prj`'s own
  reasons first; residents follow from them. A hand-set `[?]` on `^prj` blocks nobody
  (D4 in the earlier report). JS immediate paths may still use `^prj`'s `[?]` as the
  shortcut.

### 2. Project schedule on `^prj`

- **Source of truth:** `^prj`'s inline `[scheduled:: YYYY-MM-DD]`, placed like any
  task's schedule.
  - It blocks `^prj` directly (`local_schedule`). That fixes Q5 and capture's `[?]` with
    no new rule.
  - `#hide` forcing for a future date stays in sync.
- **Propagation (ADJ-8):** sync and nav keep copying the date to residents (raise-only,
  as today).
  - **Fix while you are there:** when nav changes `^prj`'s date from P_old to P_new, also
    replace residents' copies that are *exactly* P_old.
  - Ctrl+D already matches copies by exact value. Today, moving a project date
    **earlier** leaves residents Blocked until the old date: `upsertProjectTaskScheduledField`
    (`250:514-545`) and Rust's `upsert_task_scheduled` both only raise dates.
- **Freshness side effects (improvements):**
  - a Task Card schedule edit on `^prj` stamps it like any task;
  - a visible `^prj` whose date arrives after its stamp becomes RESURFACED → PROJECTS;
  - a future-dated `^prj` is out of the walk (today a frontmatter-scheduled `^prj`
    without `#hide` still walks).
- **Gesture rule detail:** block-id-prompt's own-schedule pull-forward
  (`070:391-401`) would delete `^prj`'s date when you link `^prj` itself. Treat that
  pull-forward like a `^prj` reschedule to today, so residents' P_old copies move too.
  Alternatively, refuse to link `^prj` (it is `#hide` and already excluded from the
  picker).

### 3. `#prj_is_blocked`

- **Rule (ADJ-3):** an open resident of a blocked project carries exactly one
  `#prj_is_blocked`. No other open task carries it. Closed lines are left alone; the
  tag on a closed line is accurate history.
- **Writers:**
  - Reconcile is the authority. It adds the tag, and strips it from open tasks that are
    not residents of a blocked project: moved out, project unblocked, project terminal,
    or hand-copied.
  - The immediate writers that already flip residents in the epic maintain it in the same
    write:
    - nav: the Depends on stage on `^prj`, the Schedule/Ctrl+D row on `^prj`,
      Ctrl+Shift+M into or out of a project, and conversion;
    - the cycler: recovery of `^prj` and its residents (`3208e8c`);
    - capture: `&` on `^prj`, and new tasks into a blocked project.
  - A missed immediate write is repaired within 15 minutes, which is the same window as
    `[?]` today.
- **Placement:**
  - Insert it with sync's `#hide` helper (`task_metadata_insertion_offset`: after the
    fields, before `^id`).
  - Both Rust parsers and the freshness placement rule treat trailing tags as part of
    the Tasks suffix.
  - In reconcile, tag edits are line rewrites and count as structural (the quiet
    interval applies).
- **Matching hazards:**
  - Tasks/Dataview `tags include #prj` is a substring match, so it would match
    `#prj_is_blocked`. No vault query does this today; note it in `docs/projects.md`.
    bob-cli's own tag matching is token-bounded.
  - Add the tag to `projects/tags.rs:172-184`'s strip list as a precaution.
- **Optional polish (v2):** in bob-ledger-tools, render the tag as a small "blocked by
  project" pill, like the existing `#task` and `#ref` marks. The tooltip would name the
  project and its reasons, and clicking it would jump to `^prj`.
- **Rejected: a virtual, render-only reason chip with no write.** It would be
  invisible on mobile and in raw Markdown, greppable nowhere, and `blocked.md` could not
  filter on it without a plugin API call. The written tag is what you asked for, and it
  has precedent (`#hide`).

### 4. The unblocked-task review guarantee

**Why it is not true today, and is not true after the epic:**
- Freshness is read-time state from `fresh`, `scheduled`, and the interval
  (`state.rs:452-462` and `100-freshness-evaluate.js:399-426`; both use only
  `scheduled` for RESURFACED).
- Automation never stamps (freshness §5).
- Project-member recovery is "recover-only, never linked" (§12.2, PDC2).

So a resident whose stamp is under 7 days old recovers FRESH and is in **no tier**. With
an older stamp it is ROTTEN, which is optional upkeep after "Commitments done". That
means the guarantee does not hold either way.

**Options:**

| Option | How | Gaps | Cost |
| --- | --- | --- | --- |
| A. Read-time `returned_on` (earlier report) | RESURFACED when `fresh < max(scheduled, completion/cancel dates of own prerequisites and of ^prj's prerequisites) ≤ today` | Misses: removing a project's prerequisite from `^prj` (Ctrl+Shift+P or a hand edit); deleting or moving a project date via Ctrl+D or Task Card; deleted or unresolvable prerequisites; a raw `[x]` with no `[completion::]`; a project closed with Blocked residents. **The first two are the commonest ways you unblock a project yourself** | Cross-task lookups (id → completion date, archive paths) in both evaluators. No writes |
| **B. Record the event (recommended)** | Whoever performs an automatic Blocked → Ready recovery writes `[unblocked:: today]`. Evaluators: RESURFACED when `unblocked ≤ today` and the task has not been stamped since | Only a recovery path that forgets to write it. Mitigated by one helper per language and shared vectors | One small evaluator change on each side. A write helper in Rust and in bob-ledger-tools (`api.freshness`), called from about 6 recovery sites. A placement-rule extension |
| C. Clear `[fresh::]` on unblock (shows as NEW) | Automation deletes the stamp | None | Rejected: NEW means "never confirmed", it breaks "automation never stamps", and it loses keeps |
| D. Recover to Next | Rank override | None | Rejected: contradicts sticky lanes and the derived rank, and grows the lanes |
| E. Successor-link residents when a project unblocks | §12 linking | Only covers close gestures, and the 5-link breaker | Rejected in D8 of the earlier report (membership is not an authored edge). It still is |

**Recommended rule (B):**

```text
WRITE  — on every automatic transition of an open task from Blocked [?] to Ready [ ]:
           reconcile Unblock; capture/cycler close recovery (including project_member);
           nav/cycler project recovery of residents; nav schedule recovery of lines other
           than the gesture's own line
         skip if: scheduled(t) exists ∧ fresh(t) < scheduled(t) ≤ today   (already a tickler)
         skip if: the recovery lands in Next or Pending (lane walk covers it)
         else:    set [unblocked:: today]  (replace any older value)
CLEAR  — every stamp (stamp_fresh / stampLine / keepLine) removes [unblocked::], as
         generic stamps already remove keeps. Reconcile prunes [unblocked:: U] where
         fresh > U (a hand stamp).
READ   — returned_on(t) = latest of
           scheduled(t)  if fresh(t) < scheduled(t) ≤ today
           unblocked(t)  if unblocked(t) ≤ today ∧ (no fresh(t) ∨ fresh(t) ≤ unblocked(t))
         state  = NEW if no fresh; RESURFACED if returned_on exists; ROTTEN; FRESH (as today)
         tier   = TICKLER (commitment); due_on = returned_on
```

- **The tie rule.** Because stamps clear the field, `fresh ≤ unblocked` is safe.
  Consider a task stamped in the morning, for example when you add its prerequisite,
  and unblocked that afternoon. Its stamp and its unblock fall on the same day, but it
  still resurfaces. Under option A's strict `<`, it would be missed.
- **Placement.** Put `unblocked` in the freshness group:
  `[fresh::] [refresh::] [keeps::] [unblocked::]`, then the Tasks suffix.
  - Both suffix scanners must treat it as a non-Tasks key that extends the run, the way
    `keeps` works. Otherwise reconcile's `task_metadata` stops scanning at it and loses
    `scheduled`.
  - Extend `fresh_misplaced` to cover it.
  - Hide or mute it in `dataview-properties.css`, as `[fresh::]` is.
- **Keeps.** A keep on a TICKLER row that came from `unblocked` should **not**
  increment `[keeps::]`. Today `keepLine` counts any `rotten`/`tickler` row, and a newly
  unblocked task is not evidence of procrastination.
- **Notice copy.** The TICKLER row says why: `unblocked Oct 12 · project
  job_apply_to_databricks` rather than `scheduled Oct 12`. Reconcile JSON already
  carries the reason kinds.
- **When a whole project unblocks**, N residents land in TICKLER together. Sort ties
  within the same `due_on` by path then line (today the order is `created ↓`), so a
  project's tasks are contiguous and one counted Ctrl+Alt+F can sweep them.
- **Remaining precondition (from the earlier report).**
  - The walk only sees a task once its checkbox has left `[?]`. That happens through
    reconcile (MacBook cron, every 15 minutes, only while the Mac is awake) or through
    an immediate plugin path.
  - Consider a PRE-tier guard: a notice or chore when reconcile has not run since
    midnight. Reconcile records no last-run time today, so this is a small follow-up.

**Guarantee after the change:**

| Unblock path | Mechanism | Reviewed by the next morning? |
| --- | --- | --- |
| Own `scheduled` arrives | existing TICKLER | ✅ |
| Project `scheduled` arrives | residents' propagated copies; `^prj`'s own inline date | ✅ |
| Own prerequisite closes or is cancelled, any surface (gesture, phone, raw click) | cycler, capture, or reconcile writes `unblocked` | ✅ |
| …through a Bob close while planned today | successor link → Next → NEXT lane | ✅ |
| Project prerequisite closes | residents recovered with `unblocked` (cycler, capture, reconcile) | ✅ |
| **You remove a project prerequisite, or Ctrl+D the project date, on `^prj`** | nav writes `unblocked` on the residents; `^prj` itself is stamped by the gesture | ✅ (option A ❌) |
| Prerequisite deleted or unresolvable; project closed with Blocked residents; hand edits | reconcile Unblock writes `unblocked` | ✅ (option A ❌) |
| More than 5 successors (breaker) | recover → `unblocked` | ✅ |
| You unblock the task itself (Alt+], Task Card, `&`) | the gesture stamps it, which counts as reviewing it | ✅ |

Caveats: reconcile must have run since the unblock; lane walks must be enabled; and old
plugin versions do not write the field during the rollout window.

### 5. Visibility (`blocked.md`)

Add this before STRANDED, and add `NOT (tags include #prj_is_blocked)` to STRANDED:

````markdown
## PROJECT Tasks
_Waiting on their project: its `^prj` has an open prerequisite or a future date._
```tasks
is not blocked
status.name includes Blocked
tags include #prj_is_blocked
NOT (scheduled after today)
group by path
```
````

- Residents that carry a propagated future date stay in the date sections, which keeps
  the page's "exactly one section" rule. The tag then explains them inline.
- Also update the page's intro, and replace `bob task-status-hooks` with
  `bob task reconcile`.
- Optionally, add a Tasks query on `#prj` with `scheduled after today` to
  `dash_projects.md`, to recover a "projects by start date" view without frontmatter.

### 6. Migration and rollout

1. **bob-cli first, installed on the MacBook** (the only host that runs `projects sync`
   and `reconcile`), *before* any new plugin is synced there. An old sync deletes inline
   `^prj` dates.
2. **The first `projects sync` run hoists dates.**
   - For each active project with a valid frontmatter `scheduled`: write it inline on
     `^prj` (frontmatter wins), then delete the key.
   - Expected: 10 projects. `sase_message_boards` gains `[scheduled:: 2026-10-16]`, and
     the next reconcile makes its `^prj` `[?]`. The other 9 get past dates, which are
     inert: their `^prj`s are `#hide`.
   - Hoist verbatim, so propagation behaves identically.
   - An invalid value is left in place with a warning.
3. **The first reconcile.** The Databricks `#ref` residents become `[?]` +
   `#prj_is_blocked`, and their already-removed links need no ledger change. No
   dependency migration is needed.
4. **Then the plugins on the MacBook** (nav, cycler, block-id-prompt, ledger-tools
   evaluator).
5. **Then `blocked.md` and the memory records.**

## Recommended solution

Re-plan `bob-cli-6s` as **"project blocking from the `^prj` line"**, in this order:

| Phase | Repo | Content |
| --- | --- | --- |
| contract-v2 | bob-cli docs | Rewrite §13: storage is `^prj`'s own Depends-On line and inline `scheduled`; drop §13.2, the §13.7 property R-rules, PDP/PDW, and the YAML PDR rows. Add vectors for the tag (PDT) and for `unblocked` (UB, in freshness §10). Revert §2.1's "`^prj` never has a Depends-On line". Update `docs/projects.md` and freshness §2–5 |
| cli-model | bob-cli | Project recognition and reasons from the `^prj` line (no frontmatter list reader). Reuse `.2`'s non-YAML parts |
| cli-projects | bob-cli | Sync: the hoist (ADJ-9); stop stripping inline `^prj` dates; propagation, `#hide`, and the `🗓️` marker read from `^prj`; Sub-projects goes after Depends-On. Capture `+` writes inline |
| cli-reconcile | bob-cli | The effective-blocking rule; tag maintenance; consumption; ADJ-11; internal-target guard; writing `unblocked` on Unblock; reason kinds in the output; help text |
| cli-close-capture | bob-cli | Close and recovery paths (PDC, with tag and `unblocked`); `&` on `^prj` keeps writing the line and adds resident blocking and consumption; never link a Blocked task (as planned in `.7`) |
| freshness | bob-cli + ledger-tools | Both evaluators read `unblocked`; stamp helpers clear it; keep eligibility; placement rule and lint; schema and api version bump; shared UB vectors; TICKLER notice copy and tie order |
| nav | bob-plugins | Recovery gate reads `^prj`'s reasons; Schedule on `^prj` uses the inline path (the `project-frontmatter` kind retired for `scheduled`) with propagation and the move-earlier fix; the Depends on stage on `^prj` blocks residents with the tag, consumes links, and writes `unblocked` on removal; conversion line ↔ line; Ctrl+Shift+M; child-picker chip |
| compat | bob-plugins | Follow-up to `3208e8c`: the cycler and block-id-prompt read `^prj` inline `scheduled`, and maintain the tag and `unblocked` on resident recovery |
| rollout | MacBook, vault | Bob first, then the hoist and reconcile, then plugins; `blocked.md` PROJECT section |
| publish | memory | One new decision record, "Projects block their tasks from the `^prj` line" (inheritance, inline storage, tag, consumption). It partly supersedes `task-lanes-are-sticky` claim 1 (consumption) and `task-deps-are-depends-on-links` (consumption only; storage is unchanged). A second record, "Unblocked tasks resurface as ticklers", partly supersedes `ready-is-freshness-gated` ("stamps remain the only write") and extends `review-walk-is-tiered`'s TICKLER. Glossary: Project Task, Task Dependency Link, Task Freshness |

Why this order:

- The contract fixes the vectors before any engine moves.
- bob-cli lands and is installed before any plugin writes inline `^prj` dates.
- The freshness change lands with the recovery writers, so no engine is touched twice.

## Open questions for Bryan

1. **Pause the running phases now?** **Recommended: yes.** Stop `.2` and `.8`, hold the
   queue, amend the plan, and relaunch.
2. **Tag semantics: every resident of a blocked project (ADJ-3) or only the residents
   whose sole reason is the project?** **Recommended: every resident.**
3. **Keep propagating the project date onto residents (ADJ-8)?** **Recommended: keep it
   for now.** Retiring it would make the tag plus `project_schedule` the only signal, and
   would need `blocked.md` and TICKLER changes. It is worth its own decision later if
   the copies keep causing trouble, like the move-earlier quirk.
4. **The unblock mechanism: write `[unblocked::]` (B) or stay read-only (A)?**
   **Recommended: B.** A is principled but misses the project unblocks you perform
   yourself. If "stamps remain the only write" matters more to you, choose A and accept
   those gaps.
5. **Should a keep on an unblock-TICKLER row count toward the keep streak?**
   **Recommended: no.**

## Incidental findings

- **Moving a project's date earlier leaves its residents Blocked until the old date.**
  Both writers only ever raise a date: nav `upsertProjectTaskScheduledField`
  (`250:514-545`) and Rust `upsert_task_scheduled` (`projects/edits.rs:207-240`). Only
  Ctrl+D removes copies by exact value.
- **Reconcile's `task_metadata` stops at the first unrecognised field.** A `scheduled`
  left of `[fresh::]`, `[keeps::]`, or `[p::]` is invisible to the Blocked rule
  (`task_status_hooks/parse.rs:122-194`). Current writers avoid this. A new `unblocked`
  key must be registered with the same scanner.
- **`bob-project-tasks` rewrites frontmatter with `processFrontMatter`** 250 ms after
  metadata changes (`main.js:256,269`). It could reformat or race a YAML `depends_on`
  splice. The inline model removes that interop risk entirely.
- **`project.md` documents a stale model** ("`[scheduled::YYYY-MM-DD]` added to `^prj`"),
  and `blocked.md` still names `bob task-status-hooks`.
- **A `[?]` `^prj` cannot be reverse-converted** (nav `210:791`), and the forward
  conversion seeds a Depends-On child as a fake task (`110:1`). Both are already in the
  epic's scope, and both get simpler with the line model.

## Sources

- **bob-cli `75e323b`:**
  - docs: `docs/projects.md` (§Sync Rules, Task Card, Scheduling from `^prj`);
    `docs/task-dependencies.md` §§2, 4, 5, 12.2, 13; `docs/freshness.md` §§2–6;
    `docs/vault-git-sync.md:113-138` (the Mac crontab);
  - code: `src/native/projects/{scan,sync,edits,model,tags}.rs`;
    `task_status_hooks/{sync,parse,reconcile,references}.rs`;
    `task_complete/successors.rs`; `capture_project_note.rs`; `freshness/state.rs`.
- **bob-plugins `3208e8c`:**
  - bob-navigation-hotkeys fragments 010, 070, 080, 100, 110, 140, 190, 200, 210, 250,
    260, 300, 310, 550, 570, 580, 590, 610;
  - bob-ledger-tools 100, 136, 140, 160;
  - task-status-cycler 080, 085;
  - block-id-prompt 030, 070, 120;
  - `bob-project-tasks/main.js`;
  - the epic's in-progress nav-model work, read only to size it.
- **Vault (read-only):**
  - the project-note census;
  - `job_apply_to_databricks.md`, `sase.md`, `sase_message_boards.md`, `bob.md:27-28`;
  - `blocked.md`, `dash.md`, `projects.base`, `_templates/new_project.md`, `project.md`;
  - `.obsidian/plugins/obsidian-tasks-plugin/data.json`, `.obsidian/types.json`,
    `.obsidian/snippets/*.css`.
- **Research:** `research:202610/unblocked_task_review_guarantee.md`;
  `research:202610/project_dependency_blocking/project_dependency_blocking.md`.
- **Plan and bead:** `plan:202610/prj_task_dep_links.md`; epic `bob-cli-6s` and its
  phase states; `sase agent list` at about 09:30 EDT.
- **Memory (audited reads):** `decisions:task-deps-are-depends-on-links`,
  `decisions:review-walk-is-tiered`, `decisions:task-status-is-derived`,
  `decisions:ready-is-freshness-gated`, `decisions:task-lanes-are-sticky`,
  `glossary:project-task`, `glossary:task-dependency-link`, `glossary:task-freshness`.
