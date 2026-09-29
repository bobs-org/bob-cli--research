# A generated task roadmap and a closed Pomodoro day: automation without a second backlog

- **Researcher:** `cdx`
- **Date:** 2026-09-29
- **Decision:** Change the planning layer, not the retrospective time ledger.
- **Recommended architecture:** task-local roadmap horizons rendered in a generated Markdown view; a capped daily Pomodoro commitment list; capture, keymap, and hook support around one shared contract.

## Executive conclusion

Yes, the current approach should change, but less of it needs changing than the size of today's daily note suggests.

Keep the completed Pomodoro ledger. It is a useful, unusually honest record of time: variable-length sessions, task links, names, notes, and explicit duration. Do not force 25-minute blocks, add a second timer, rename `## Pomodoros`, or replace the vault with a separate planner.

Change the open half of the ledger. On the example day, it contains **22 open Pomodoro entries and 75 task references**, while the completed portion contains **6 sessions totaling 210 minutes**. A live `bob task-status-hooks --dry-run --format json` also reports **25 tasks kept Next and 52 kept In Progress**. There are even two open `SASE` buckets. This is not a day plan; it is an inventory, status engine, capture inbox, and plan collapsed into one surface.

My recommendation is:

1. Preserve the existing `## Pomodoros` completed log and its tools.
2. Treat open Pomodoros as a **closed commitment list for today**: one highlight represented in one of at most three non-GTD themes, no more than about ten task links, and only one timed session open.
3. Add exactly one orthogonal task field, `[roadmap:: now|next|later]`, as the canonical planning horizon. Absence means "not curated onto the roadmap," not Later.
4. Render those task fields in a query-only `roadmap.md`, not a hand-maintained list and not `roadmap.base`.
5. Stop copying unfinished Pomodoros into the next day. An explicit morning rollover marks yesterday's still-open Pomodoro parents cancelled while retaining their children as evidence; it does not move or copy tasks.
6. Make capture outside today use `@route^id` plus a new terminal `r:now`, `r:next`, or `r:later` marker. Keep `@route:id` as the explicit "commit this to today" form and make it imply roadmap Now.
7. Reuse `Ctrl+Shift+P` for horizon changes, but first make its writer place the custom field safely. Merely adding the property to `~/.config/bob/config.yml` is unsafe with the current task metadata parser.
8. Let `task-status-hooks` report policy violations with stable warning codes but not enforce subjective caps or silently rewrite yesterday. Show the same counts as red/amber badges at the top of `dash.md`, where they are visible in Obsidian.

This adds one field and one generated view, while deleting the daily carry-forward loop. The automation makes the intended behavior cheaper than the accidental behavior.

## What I inspected

I independently inspected:

- the required prior synthesis, `pomodoro_ledger_and_daily_roadmap.md`;
- `~/bob/2026/20260929.md`, `dash.md`, `_templates/daily.md`, `gtd_daily.md`, the Obsidian hotkeys, and the current bullet-property configuration;
- the live read-only output of `bob task-status-hooks` against the vault;
- `bob-cli` capture grammar, Pomodoro parsing, task-status reconciliation, JSON interfaces, tests, and sync behavior;
- the source-of-truth `bob-plugins` implementations of the ledger tools, block-ID prompt, task cycler, and navigation/property picker;
- the `bob-mac-capture` contract and its use of `capture-parse`, `capture-complete`, and dry-run capture JSON;
- official Obsidian Bases and hotkey documentation, Dataview's task-level field/query documentation, and the earlier report's behavioral sources.

I did not inspect any other researcher's report from this swarm.

## 1. The important distinction: four states, not one

The redesign succeeds only if it stops treating four different questions as one checkbox/status:

| Question | Canonical representation | Meaning |
|---|---|---|
| What state is the task in? | Tasks checkbox (`[ ]`, `[*]`, `[/]`, `[?]`, terminal states) | Ready, Next, In Progress, Blocked, done/cancelled |
| When is it a plausible focus? | `[roadmap:: now|next|later]` | Planning horizon, independent of execution status |
| Did I commit to it today? | Task Link under an open `## Pomodoros` entry | Today's closed list |
| What did I actually work on? | Completed timed Pomodoro plus 🍅 link/work notes | Historical record |

Today, a link under an open Pomodoro answers all four questions at once. `task-status-hooks` promotes it; capture puts newly created work there; migration preserves it; the daily note displays it. That coupling is the mechanism behind the growth.

The roadmap field must therefore **not** be inferred from task status:

- A Ready task can be Roadmap Now without being committed today.
- A Blocked task can remain Roadmap Now while waiting on a dependency.
- A Next or In Progress task should normally be linked in today's ledger, but its status remains an execution concern owned by the existing hooks.
- A task with no roadmap field remains in the ordinary READY/inbox universe.

This orthogonality is more important than whether the UI says "Now" or uses a particular color.

## 2. Why `roadmap.base` is the wrong primary view today

The idea is attractive: a compact `.base` file, a badge/count on `dash.md`, and no large manually edited `roadmap.md`. The obstacle is the current Obsidian data model, not taste.

Obsidian's official Bases documentation says each row is a **file**, and Base properties are note frontmatter, file properties, or formulas. A Base can filter, group, and render notes in table/list/card/Kanban views, but it does not make each Markdown task line a first-class row. The vault's existing `projects.base` works precisely because each project is a note. The roadmap candidates, by contrast, are many individual task lines inside route/area/project notes; a single `sase.md` can contain tasks in more than one horizon.

Consequences:

- A task-level `[roadmap:: now]` field is not a note frontmatter property and cannot make that task an independent Base row.
- `file.tasks` could be displayed as a compound value on a file row, but that is not an interactive Now/Next/Later task board.
- A custom Bases view plugin could flatten tasks, but it would add another rendering/editing integration before the process is validated.
- Moving every task into its own note would make Bases fit, but would be a much larger and unrelated workflow migration.

Dataview already has the correct granularity. Its `TASK` query operates on `file.tasks`, recognizes list/task inline fields such as `[roadmap:: now]`, and can update the original checkbox when a rendered task is checked. Therefore:

> Use `roadmap.md` as a generated **view**, not as a second hand-maintained source of truth.

The file would contain frontmatter (`parent: "[[gtd]]"`) and three Dataview task queries. It would contain no copied task links to reconcile manually:

````markdown
## Now

```dataview
TASK
WHERE !completed AND roadmap = "now" AND contains(tags, "#task")
SORT priority ASC, file.name ASC, line ASC
```

## Next

```dataview
TASK
WHERE !completed AND roadmap = "next" AND contains(tags, "#task")
SORT priority ASC, file.name ASC, line ASC
```

## Later

```dataview
TASK
WHERE !completed AND roadmap = "later" AND contains(tags, "#task")
SORT file.name ASC, line ASC
```
````

The exact query syntax should be tested against the installed Dataview build, but the documented task-level model supports this design.

A `roadmap.base` may become useful later for a **project-level** roadmap, where each project note gets frontmatter such as `roadmap: now`. It is not the right primary artifact for today's task-line workflow.

## 3. The subtle blocker: task metadata ordering

The current Obsidian property picker almost makes the roadmap field free. `Ctrl+Shift+P` invokes `bob-navigation-hotkeys:set-bullet-property`, and `~/.config/bob/config.yml` already accepts properties with a fixed list of scalar values. It would be tempting to add:

```yaml
- name: roadmap
  values: [now, next, later]
```

Do not ship only that change.

The current generic writer appends a new field immediately before a trailing block ID. Local source comments document an important compatibility rule: Tasks-format parsers read trailing inline metadata from right to left and stop at the first property they do not recognize. An invented custom value or field placed at the far right can hide standard `[scheduled::]`, `[priority::]`, `[created::]`, `[id::]`, and `[dependsOn::]` metadata to its left from Obsidian Tasks, `bob query`, and dashboard queries.

The canonical safe shape is instead:

```markdown
- [ ] #task Investigate the flaky launch [roadmap:: now] [created:: 2026-09-29] [priority:: high] ^flaky-launch
```

The custom field must appear **before the trailing run of Tasks-recognized metadata**, so the Tasks parser consumes its known fields before stopping at `roadmap`.

This needs one shared placement rule across:

- `bob capture` rendering;
- `Ctrl+Shift+P` single and counted edits;
- any future CLI setter or migration;
- repair/validation in `task-status-hooks`.

The field is still the best data model, but safe writing is an implementation prerequisite. A tag such as `#roadmap/now` would avoid this parser boundary, yet it is noisier in prose, harder to clear through the existing property UI, and conflates organization tags with one-valued state. I prefer the field plus an explicit safe writer.

## 4. Recommended process

### 4.1 Horizon semantics

Use only these values:

- `now`: eligible to pull within the next day or two; a deliberately small replenishment pool;
- `next`: intentionally retained, but not eligible for the current daily pick without promotion;
- `later`: parked and hidden from routine daily choice;
- absent: inbox/untriaged/not deliberately roadmapped.

Keep the vocabulary deliberately vague about dates. Scheduling remains `[scheduled:: YYYY-MM-DD]`; priority remains `[priority:: ...]`. The roadmap says when to consider a task, not when it is due.

Suggested starting limits, exposed as config rather than hard-coded truths:

- Roadmap Now: warn above 12 open tasks or five source/project notes;
- today's daily note: warn above four open named entries including GTD, or above ten unique task links;
- only one non-empty open timed Pomodoro remains a structural hard error, as it is today.

The Now limit is a two-day buffer, not a target to fill. The daily cap is grounded in the measured throughput summarized by the prior research. Recalibrate both after the trial.

### 4.2 The daily note

Keep the existing heading and duration formula. Add one optional line immediately above it:

```markdown
highlight:: Decide the goals phase order and file its beads
```

The open portion should contain:

- `GTD`;
- the highlight's theme;
- at most two other themes;
- at most about ten unique task links total.

The highlight is an outcome, not another task store. It answers "what would make today count?" and can link to the main task if useful.

Unplanned urgent work gets a truthful block when it occurs (`OPS`, `RELAUNCH`, `FIXES`). It is not pre-staged as a permanent open bucket. Variable session lengths remain valid.

### 4.3 Morning rollover: cancel, do not carry

Replace "Migrate unfinished Pomodoro tasks" and the two large daily review chores with one five-minute action:

1. Mark yesterday's still-open Pomodoro parent lines `[-]`, retaining their child links and notes in place.
2. Do not copy any task or bucket into today.
3. Review only Roadmap Now.
4. Write the highlight and link today's small selection into named open Pomodoros.

Cancelling only the parent line has useful semantics with the existing parsers: `[-]` is neither open nor completed, so it stops driving current status and does not enter duration totals, while the children preserve evidence of what was planned but not done. This creates better calibration data than cutting the entries out of history.

The rollover should be an explicit, previewable CLI/plugin action, not a midnight cron mutation. An automatic midnight rewrite is unsafe when work crosses midnight or another machine has unsynced edits. A good contract would support dry-run and JSON, refuse a genuinely live timed session without explicit confirmation, and use the same guarded-write/recovery discipline as the existing mutators.

`task-status-hooks` currently treats the latest earlier daily note as read-only recent-activity context. Keep that invariant. The new rollover owns the deliberate historical mutation; the frequent reconciliation cron should not silently rewrite yesterday.

### 4.4 Weekly replenishment

Once per week:

- shrink Now back under its cap;
- promote a small set from Next;
- prune or retain Later intentionally;
- review READY tasks that have no roadmap field;
- compare created versus closed work and the age of Now tasks.

This is the only time the whole candidate inventory should be reviewed. The daily process should never require reading every READY, Next, or Later task.

## 5. Automation design

### 5.1 `bob capture`: make destination intent explicit

The current grammar already distinguishes the two crucial cases:

- `@route:block-id` creates/ensures a Next task and links it into today's Pomodoro ledger;
- `@route^block-id` creates an ordinary Ready task with an ID and does not touch today's ledger.

Preserve that distinction and add one terminal roadmap token family:

```text
r:now
r:next
r:later
```

Examples:

```text
Investigate parser ordering @bob^parser-order r:now
Try a task-level Bases view @bob^bases-task-view r:later
Fix the broken deploy @bob:fix-deploy#ops
```

Rules:

- `r:<horizon>` composes with route, `s:<N>`, `p:<N>`, clipboard, and batch capture using the same terminal-token discipline already used by capture.
- `@route:id` means today and therefore implies `roadmap:: now`; explicit `r:next` or `r:later` with a today marker is rejected as contradictory.
- `@route^id r:...` is the normal path for captured work that should be visible on the roadmap but not committed today.
- An ordinary capture without `r:` remains uncurated inbox work. Do not make Later the default; a silent infinite Later bucket would recreate the original problem.
- Rendering places `[roadmap:: ...]` before the trailing Tasks-recognized metadata run.
- Dry-run JSON returns the horizon and any capacity warnings as structured additive fields.

The capture action should not hard-fail merely because today's soft cap is exceeded. Emergencies are real, and a subprocess cannot conduct a nuanced confirmation dialogue. Return a warning; let the Mac preview and Obsidian UI show it prominently.

### 5.2 `bob-mac-capture`: remain a thin client

The Mac app already follows the right architecture:

- highlighting comes from `bob capture-parse` spans;
- completion comes from `bob capture-complete` contexts and replacement ranges;
- preview and submission use `bob capture` dry-run/live JSON;
- Swift presentation is intentionally not an independent grammar.

Extend that contract rather than parsing `r:` in Swift:

- add a `roadmap`/`roadmap_horizon` parse field and semantic span;
- add completion candidates for `now`, `next`, and `later` after `r:`;
- decode the field additively and show a small horizon chip in preview;
- render structured planning warnings (for example, `Today's plan is 11/10 links`) in amber;
- retain backward compatibility when an older `bob` omits the field.

The app should visually explain the existing punctuation as well: colon means **Today**, caret means **Backlog task with ID**. That is likely more valuable than inventing a separate roadmap UI.

### 5.3 Obsidian keymaps: reuse before adding

Do not allocate three new hotkeys.

After the safe-placement fix, add `roadmap: [now, next, later]` to the existing bullet-property configuration. `Ctrl+Shift+P` then changes or clears the field on one task, and the counted form can update several tasks. This preserves the current keyboard vocabulary.

Two existing commands should gain roadmap-aware behavior:

- `Ctrl+Shift+Enter` on a Ready task already links it into today's current/next Pomodoro and promotes it. If the task is `next` or `later`, the same transaction should set it to `now`; if absent, either leave it absent or offer a clear notice. I recommend setting it to Now because today is necessarily a subset of Now.
- Removing a task from today's ledger should **not** demote its roadmap horizon automatically. It remains a Now candidate until the weekly review moves it. This is what prevents removal from feeling like loss.

The property picker is desktop-only today because it reads host configuration. The raw Markdown remains portable, and mobile users can still edit the field manually. Do not make the process depend on a desktop-only modal to remain intelligible.

### 5.4 `task-status-hooks`: validate policy, mutate only facts

`task-status-hooks` already scans the vault, resolves task identities, applies guarded multi-file writes, cleans duplicate/cancelled/completed references, removes childless entries, derives statuses, and emits JSON. It is the right place to **detect** roadmap inconsistencies, but not to make subjective planning choices.

Add an additive `planning_warnings` array with stable codes and locations, for example:

- `daily_open_entry_cap_exceeded`;
- `daily_link_cap_exceeded`;
- `roadmap_now_cap_exceeded`;
- `daily_task_in_next_or_later`;
- `invalid_roadmap_value`;
- `unsafe_roadmap_field_order`;
- `duplicate_open_pomodoro_name`;
- `previous_daily_still_open`.

Policy warnings should exit zero and never block status reconciliation. Structural ambiguity, such as multiple open timed Pomodoros, remains a hard failure. Soft caps are feedback, not corruption.

Safe automatic mutations are limited to objective invariants:

- a task atomically added to today can be set Roadmap Now by the capture/link writer;
- malformed or ambiguous roadmap fields should be warned, not guessed;
- completed/cancelled tasks need no property cleanup because the generated view filters them out, and retaining the horizon supports later analysis;
- hooks must not auto-promote arbitrary Next tasks into today's ledger, auto-prune Later, or auto-cancel yesterday.

Because the hook normally runs from cron and writes stdout to a log, warnings there are not enough for the human loop. They need an Obsidian surface too.

### 5.5 `dash.md`: make violations visible where choices happen

Extend the existing DataviewJS chip bar with a second compact planning group:

```text
TODAY 22/4   LINKS 75/10   NOW 14/12   NEXT 27   LATER 41
```

- green under the cap;
- amber at the cap;
- red above it;
- every chip opens today's Pomodoros or the relevant `roadmap.md` heading.

Dataview can count task-level inline fields directly. Counting open Pomodoro entries and their unique child Task Links may warrant a small shared helper or plugin function so its definition stays identical to `bob`; avoid a second approximate regex if the badge becomes an enforcement surface.

The roadmap note itself should show a warning callout above Now when the cap is exceeded and show age/created information where available. It should not hide excess items; visibility is the point.

## 6. Options considered

| Option | Strength | Failure mode | Verdict |
|---|---|---|---|
| Keep carrying the full ledger; restart daily review | No implementation | Review cost grows with backlog; selection already lapsed | Reject |
| Manual `roadmap.md` containing copied task links | Readable and reorderable | A second list must be moved, deduplicated, and reconciled | Accept only as a one-week prototype |
| `roadmap.base` over current task notes | Native UI and Kanban views | Rows are files, not task lines; mixed-horizon notes cannot be represented | Reject for the task roadmap |
| Use status as Now/Next/Later | No new field | Recreates the status/commitment coupling that caused the problem | Reject |
| Task-local horizon + generated `roadmap.md` | One source of truth, queryable, capture-friendly | Requires safe metadata placement and small writer changes | **Choose** |
| One note per roadmap item + Bases | Excellent Base fit | Large migration and too much ceremony for small tasks | Defer indefinitely |
| External task/time application | Rich automation | Duplicates vault tasks and loses current Task Links/log integration | Reject |

## 7. Rollout plan and decision gates

### Phase 0: behavior-only pilot (3–5 days)

- Stop adding new non-today work with `@route:id`; use `@route^id`.
- Cap today's open ledger at GTD plus three themes and about ten links.
- Do not migrate the old queue into a new day.
- Use a temporary manual Now/Next/Later note only to test whether the horizons help selection.

The point is to test the decision model before changing three repositories.

### Phase 1: canonical metadata and view

- Implement task-safe custom-field placement.
- Add `[roadmap:: ...]` support to the property picker.
- Create query-only `roadmap.md` and dash badges.
- Add read-only warning output to `task-status-hooks`.
- Migrate the small curated set, not every READY task. Unmarked tasks remain valid inbox items.

### Phase 2: capture contracts

- Add `r:` to `capture`, `capture-parse`, `capture-complete`, dry-run/live JSON, docs, and tests.
- Update `bob-mac-capture` as a thin additive client.
- Make today-link writers set Roadmap Now atomically.

### Phase 3: explicit rollover

- Add the previewable no-copy rollover command and an Obsidian command/key binding.
- Replace the existing migrate/review/plan daily tasks with one "Close yesterday; pick today" task.
- Keep rollover out of unattended nightly/cron automation until real use shows it is safe.

### Two-week success measures

Measure the system, not motivation:

- at least 10 of 14 days remain at or below four open daily entries and ten links;
- the morning pick usually takes five minutes or less;
- at least 80% of workdays give the highlight one completed Pomodoro;
- no task is reported lost after rollover (it remains at its source and, if curated, in the generated roadmap);
- Now returns under its cap at the weekly review;
- created-versus-closed work trends toward balance;
- the user opens the roadmap to choose work, rather than ignoring it as another dashboard.

If the roadmap view is routinely ignored, remove the field and keep only the capped daily ledger. If the view helps but the caps are wrong, change the config, not the architecture. If safe field placement proves too brittle across Tasks/Dataview versions, use `#roadmap/now|next|later` as the fallback representation while retaining the same semantics.

## 8. Risks and safeguards

### The roadmap becomes the next junk drawer

Mitigations: absence is allowed; Now is capped; Later is not shown during daily planning; the weekly review explicitly prunes. Do not auto-tag every Ready task Later.

### Automation makes surprising cross-file edits

Mitigations: dry-run/JSON first, guarded snapshots, exact task identity, one sync lock, recovery records, and no cron rollover. Capture/link operations that touch a task and daily note must be atomic, as they are today.

### The dashboard and CLI disagree

Mitigations: stable warning codes and one configured cap source. For nontrivial Pomodoro counts, expose a small authoritative status API or shared parser rather than copying regexes into DataviewJS.

### Metadata breaks Tasks parsing

Mitigations: canonical placement before trailing Tasks metadata, a hook warning/repair preview, fixtures covering every field ordering, and end-to-end parity tests against representative real-vault lines.

### More syntax increases capture friction

Mitigations: `r:` is optional; full-word completions make it discoverable; existing colon/caret semantics remain; the Mac shows the resolved meaning. A capture with no horizon is still valid.

### Planning starts measuring vanity metrics

Mitigations: use counts as guardrails, not scores. The important outcome is that the next block is obvious and the day no longer begins already "behind."

## Recommended solution

Adopt a **generated task roadmap plus closed daily ledger**:

- Keep the completed Pomodoro ledger, variable session lengths, task links, 🍅 marks, and work notes unchanged.
- Add the task-local field `[roadmap:: now|next|later]`; keep status, horizon, daily commitment, and actual work as separate concepts.
- Render a query-only `roadmap.md` with Dataview. Do not use `roadmap.base` for task-level horizons because Bases currently renders files as rows.
- Put a compact capacity badge at the top of `dash.md`.
- Replace carry-forward with one explicit no-copy rollover that cancels yesterday's open parent entries and preserves their children.
- Keep today to a highlight, GTD, at most two other themes, and about ten links.
- Add `r:now|next|later` to the authoritative `bob capture` grammar; keep `@route:id` as explicit Today and `@route^id` as not-Today.
- Extend `bob-mac-capture` only through the CLI's parse/completion/preview JSON contracts.
- Reuse `Ctrl+Shift+P` for horizon changes after fixing custom-field placement; do not add a family of new key chords.
- Make `task-status-hooks` emit soft, typed policy diagnostics and preserve its existing factual cleanup/status duties. Do not let cron choose, prune, or migrate work.
- Trial the behavior first, then land metadata/view, capture, and rollover automation in that order.

This is simpler than the present system because the daily note stops carrying the inventory. The roadmap is generated rather than manually synchronized, and automation supports the boundary instead of adding another planning ritual.

## Sources

### Local and repository evidence

- Required prior synthesis: `research:202609/pomodoro_ledger_and_daily_roadmap/pomodoro_ledger_and_daily_roadmap.md`
- `~/bob/2026/20260929.md`
- `~/bob/dash.md`, `_templates/daily.md`, `gtd_daily.md`, `.obsidian/hotkeys.json`
- `~/.config/bob/config.yml`
- `bob-cli`: `docs/capture.md`, `docs/task-status-hooks.md`, `docs/vault-git-sync.md`, and the corresponding Rust source/tests
- `bob-plugins`: `bob-navigation-hotkeys`, `block-id-prompt`, `bob-ledger-tools`, and `task-status-cycler`
- `bob-mac-capture`: README, `CaptureCore`, app model, and contract tests
- Live read-only checks on 2026-09-29, including `bob task-status-hooks --dry-run --format json --retry-timeout 0`

### External documentation and evidence

1. Obsidian, **Introduction to Bases** — Base rows are files and views operate on file/note properties: <https://obsidian.md/help/bases>
2. Obsidian, **Bases syntax** — note properties are Markdown frontmatter; file and formula properties are the other native property kinds: <https://obsidian.md/help/bases/syntax>
3. Obsidian, **Views** — Base layouts, filtering, grouping, embedding, and per-view behavior: <https://obsidian.md/help/bases/views>
4. Obsidian, **Hotkeys** — commands can have customizable keyboard bindings: <https://obsidian.md/help/hotkeys>
5. Dataview, **Metadata on Tasks and Lists** — inline fields attach metadata to individual task/list rows: <https://blacksmithgu.github.io/obsidian-dataview/annotation/metadata-tasks/>
6. Dataview, **Query Types** — `TASK` queries operate at `file.tasks` granularity and can update the source checkbox: <https://blacksmithgu.github.io/obsidian-dataview/queries/query-types/>
7. E. J. Masicampo and R. F. Baumeister (2011), **Consider it done! Plan making can eliminate the cognitive effects of unfulfilled goals**, *Journal of Personality and Social Psychology* 101(4), 667–683: <https://pubmed.ncbi.nlm.nih.gov/21688924/>
8. Todd Little / Kanban University, **Exploring Little's Law** — WIP, throughput, and lead-time relationship and its stability assumptions: <https://kanban.university/wp-content/uploads/2022/09/Exploring-Littles-Law-KGS-2022.pdf>
9. Francesco Cirillo, **The Pomodoro Technique** — the useful separation between activity inventory, today's selection, and records: <https://www.pomodorotechnique.com/>
