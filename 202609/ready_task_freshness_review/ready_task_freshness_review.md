# Task freshness: a rolling review lease for Ready tasks

## Bottom line

1. **Build it. The idea is sound and has direct prior art** (see the
   [critique](#is-this-a-good-idea)).
   - Taskwarrior's `tasksh review` is almost exactly this design: a `reviewed` date on each task, a missing date
     means "never reviewed", a one-week interval, and `review N` to limit a session.
   - OmniFocus runs the same loop at project grain: a review interval per project (one week by default), a Review
     perspective listing what is due, and "Mark Reviewed", which stamps today and moves on to the next item.
   - What you are adding is the task grain plus automatic stamping from the gestures you already use.
2. **The failure you described is acknowledgement latency, not prioritization.**
   - A missing stamp is a durable **"never reviewed"** state. It survives a skipped morning or a late
     `bob gkeep pull`, and it also catches captures that skip the inbox.
   - Any definition based on `created` fails, because `bob gkeep pull` writes the **Keep note's** creation date,
     not the date of the pull.
3. **Correctness blocker: where the field goes on the line.**
   - Obsidian Tasks 8.4.0 and bob-cli's native Tasks engine both read fields from the end of the line and stop at
     the first key they don't recognize.
   - So a `[fresh:: …]` appended at the end hides `created`, `priority`, `scheduled`, `id` and `dependsOn`, and
     Blocked stops being derived for that task.
   - Today every Bob writer appends new fields at the end (`upsertBulletProperty` puts them just before `^id`).
   - `fresh` must go **immediately before the line's trailing run of Tasks fields, tags and `^id`**, and one
     [placement helper](#data-model-and-placement) per language must own that rule.
4. **Only a human gesture may stamp** (see [Who stamps](#who-stamps)).
   - An automatic Blocked → Ready return (a `scheduled` date arriving, or a dependency closing) must not claim
     that you looked at the task.
   - Instead it becomes **due for review** when you next [read the queue](#state-computed-at-read-time). No hooks
     write is needed.
5. **Two tiers, and the first can never be capped.**
   - **NEW** means never stamped. It is your hard requirement, so you clear it every morning, uncapped.
   - **STALE** means stamped but expired, or back from a deferral. This tier is maintenance: it can be budgeted
     and slowed down, and a weekly catch-up can finish it.
   - Your "N per day" fallback is right, but only for STALE, and it should be a **goal meter, not a filter**. A
     Tasks `limit N` block just slides the next N tasks into view and never finishes.
6. **Load is the real risk, not the mechanics** (see [The daily load](#the-daily-load)).
   - Today's 176 non-recurring Ready tasks at 7 days mean about **25 stale tasks a day**.
   - Add returning deferrals: about 17 a day this coming week, about 6 a day later.
   - Add NEW tasks: about 14 are created per day, but fewer survive to the next morning unstamped.
   - Expect **30–45 glances a morning** at first, about 5–8 minutes. That is well below the old 186-task walk,
     but it is not free.
   - The [levers](#keeping-the-load-down), in order: longer intervals on large, slow notes; deferring or
     cancelling during review; then the STALE budget.
7. **Review in the source notes, not on the dash** (see [The review experience](#the-review-experience)).
   - Vault-wide next/previous jumps (`]s` / `[s`, or Ctrl+Alt+J/K).
   - **Alt+F** to refresh; **Alt+Shift+F** to refresh and jump to the next due task.
   - A **status bar** counter visible in any note: `⟳ 23 due · 3 new · ✓ 12 today`.
   - The dash gets **one chip**, not a new section. The accepted decision `today-is-read-from-the-ledger` makes the
     TODAY / PENDING / NEXT / READY sections mutually exclusive.
8. **Cutover needs a written, staggered seed** (see [Cutover and trial](#cutover-and-trial)).
   - Without one, day one makes every existing task "new" and buries the one capture that matters.
   - Seed every open, non-recurring task. Spread Ready tasks over 7 days, grouped by note. Give Blocked, Next and
     Pending tasks the cutover date, so that returning deferrals arrive as STALE and not as NEW.
   - Land this after `bob-cli-2y.12` and the lane triage.

The [recommended solution](#recommended-solution) at the end states the whole design in one place.

![Infographic of task freshness: the capture, review NEW, review STALE, and plan loop; the 7-day stale timer that a human confirmation resets; the drop from a 186-task Ready walk to 30–45 daily glances; the fresh-field logic; and review in source notes, status bar counts, and seeding old tasks before launch](ready_task_freshness_review_infographic.png)

## Is this a good idea

### What is right

- **Cost follows attention, not list size.**
  - The old habit cost about 186 glances every day.
  - A per-task lease costs roughly pool ÷ interval, plus arrivals. It spends your attention on what you have not
    seen.
  - This is GTD's "get current" step done in daily slices, which suits someone who does not do a weekly review.
- **"Missing means never reviewed" is the right primitive** (all five reports agree).
  - It needs no knowledge of how a task was captured.
  - Nothing, not a skipped day or a late pull, can make it go away.
- **Stamping on existing gestures keeps active work out of the queue.**
  - Anything you move, commit, schedule, re-prioritize or release is fresh by construction.
  - The review then shows only what you have been ignoring.
- **The overrides match how the vault is organized.** Tasks live in project and area notes, and project
  frontmatter already carries machine-maintained `task_count` / `open_task_count`.
- **It complements sticky lanes.** Freshness is a forgetting *signal* without automatic demotion. That is a
  better answer to backlog rot than the "age-based Next decay" that the lanes decision held in reserve.

### What it does not solve

- **Refresh is not clarification.** Glancing at "Pick up our daughter" and pressing Refresh, without deciding
  whether it belongs to today, is a failed review, even though the metadata turns green.
  - Treat Refresh as "confirm", not "dismiss", in its wording, its Notice, and the glossary.
  - Keep the other outcomes one key away: link to today, commit, defer, move, cancel.
- **It is record validity, not project coverage.** A vault where every task is fresh can still contain a project
  with no next action, stale Waiting-For items, or unchecked calendar commitments. A tiny weekly check remains
  (see [Rituals](#rituals)), piggy-backed on the existing weekly prune chore rather than added as a new ritual.
- **7 days is a service level you choose, not a property of the task.** A volatile family errand and a low-value
  SASE idea do not decay at the same rate. The overrides are essential, not decoration.

### The daily load

The load, honestly:

| In-scope Ready pool | Stale per day at 7 d | at 14 d |
|---|---:|---:|
| 176 (today) | 25 | 13 |
| 176, with `sase.md` at 14 d and everything else at 7 d | 22 | — |
| 120 | 17 | 9 |
| 80 | 11 | 6 |

- **Add to that:** returning deferrals and NEW tasks.
  - Returning deferrals run about 17 a day this week, then about 6 a day. Deferrals longer than the interval
    would come back stale anyway, so the tickler rule (see
    [State computed at read time](#state-computed-at-read-time)) adds reviews only for short P1 deferrals.
  - NEW tasks: a handful each morning.
- **Time.** At about 5 s for "still fine" and about 25 s for the roughly 1 in 5 tasks that need an action, 35
  tasks take about 5–6 minutes.
- **Implication.** Re-baseline the "Morning review ≤5 min" chore to about 10 minutes for the combined ritual.
  Otherwise, shrink the pool or lengthen intervals before the trial starts.

## What was verified

Lead-verified on 2026-09-30 unless noted. Where a researcher's number differed, the verified value is shown. The
rest of this report cites these findings as V1–V12.

| # | Finding | Evidence |
|---|---|---|
| V1 | **Ready pool.** 186 dash-visible Ready tasks: 10 recurring, 176 non-recurring, in 25 notes. `gkeep_inbox.md` 65 (35%), `sase.md` 48, `sase_remote.md` 11. Median age since `created` is 17 days, so the old morning walk mostly re-read unchanged tasks. Next 26, Pending 52 (cld, grk). | `bob query --tasks 'status.type is TODO' --origin dash.md -f json` |
| V2 | **Capture rate.** 411 non-recurring tasks carry a September `created` date (13.7 a day, including ones already done). There are 290 open `[?]` tasks; 120 return within 7 days (cld). | vault scan |
| V3 | **The trailing-field trap is real in both engines.** Tasks 8.4.0 runs a `do … while (matched)` loop over end-anchored field regexes. bob-cli's `parse_details` / `try_take_dataview_field` hits `_ => false` and then `break`. An unknown key at the end stops all parsing to its left. `docs/projects.md` and `config.yml` already warn about this for invented priority values. | `obsidian-tasks-plugin/main.js`; `src/native/dataview/tasks/task.rs` |
| V4 | **The existing writer would put `fresh` in the wrong place.** `upsertBulletProperty` inserts at `getBulletPropertyAppendIndex`, which is the end of the line or just before a trailing `^id`. Capture appends `created → priority → scheduled`. There is precedent for the safe placement: `bob highlights` writes `[h:: …]` before `[created::]` (cld). | `bob-navigation-hotkeys/main.js`; `capture/plan.rs`; `highlights_ref/annotation_tasks.rs` |
| V5 | **`created` does not mean "arrived".** `gkeep/render.rs` sets `created` from the Keep note's creation time. The default capture destination is `mac_inbox.md`, but routed `@project` captures go straight to project notes. | `gkeep/render.rs:48,487`; `capture/mod.rs:45` |
| V6 | **No stable out-of-line key.** Only 29 of the 176 non-recurring Ready tasks have a block ID, and the hooks move task blocks between status headings. A side-car store could not key on anything. | Ready JSON `blockId` |
| V7 | **The dash sections are exclusive by accepted decision.** `today-is-read-from-the-ledger`: "The dash sections are exclusive (TODAY / PENDING / NEXT / READY)." A REVIEW overlay section would change governed behavior and would need a new decision record. | `decisions:today-is-read-from-the-ledger` |
| V8 | **Free keys.** Alt+F, Alt+Shift+F, Alt+Shift+J/K and Ctrl+Alt+J/K are unbound, both in `.obsidian/hotkeys.json` and in the plugins' default hotkeys. `]s` / `[s` are unmapped in `obsidian_vimrc.md`. Ctrl+Shift+J/K already mean "next/previous open task **in this note**", and Ctrl+Alt+] belongs to task-status-cycler. On macOS, Alt+N needs a raw keydown listener (`event.code === "KeyN"`), so Alt+F will need the same. | vault config; plugin source |
| V9 | **The inline field can be visually muted.** Dataview 0.5.68 renders inline fields with `data-dv-key`, and the vault already ships a `dataview-properties.css` snippet. A rule for `[data-dv-key="fresh"]` can shrink it to a small muted chip. | Dataview bundle; `.obsidian/snippets/` |
| V10 | **"Freshness" already means other things.** About 50 legacy notes carry Zorg `@FRESHNESS` blocks (file-level `last_refreshed_on` / `recur::7d` — the same idea one level up). `docs/dataview.md` says "vault freshness is owned by `bob vault-sync`". An August task used "freshness dates" for P-level windows (grk). | vault grep; bob-cli docs |
| V11 | **The existing rituals.** `gtd_daily.md` has the "Import inbox tasks from Google Keep" chore and "Morning review (≤5 min): PENDING → NEXT → READY". The weekly prune is a `[?]` chore scheduled for 2026-10-05. `gkeep_inbox.md` is `type: [[area]]` and holds unrouted mixed items, mostly SASE ideas plus a few errands. | vault |
| V12 | **Prior art.** tasksh `review [N]` walks tasks whose `reviewed` date is missing or older than about a week, lets you modify, skip, or mark reviewed, and resumes where you stopped. Its docs advise: "If you find yourself making no changes to the tasks, perhaps you should review less often." OmniFocus's Mark Reviewed stamps today, computes the next review date from "Review every", and presents the next item; the default is weekly. | [Taskwarrior review docs](https://taskwarrior.org/docs/review/), [tasksh(1)](https://www.mankier.com/1/tasksh), [OmniFocus 4 manual](https://support.omnigroup.com/documentation/omnifocus/universal/4.3.3/en/perspectives/) |

## Adjusted requirements

These are the changes to your plan. They are marked **ADJ**. Everything else is your requirement as stated.

| # | Requirement | Change |
|---|---|---|
| R1 | Ready tasks carry `[fresh:: YYYY-MM-DD]`: the last local date a human confirmed the task still needs doing and still looks right (text, priority, project, schedule, dependencies). | **ADJ:** the field is *optional*; absence is the NEW state. **ADJ:** it sits before the trailing Tasks fields, tags and `^id`, never after them. |
| R2 | Default interval 7 days. | **ADJ:** configurable as `freshness.interval: 7` in `config.yml` (chezmoi), not hard-coded in two languages. |
| R3 | Per-task override. | `[refresh:: N]`: integer days, 1–365, placed right after `fresh`. |
| R4 | Per-project override in frontmatter. | `task_refresh: N` in the note's frontmatter. **ADJ:** it applies by *residence* (the note that contains the task, whether a project, area or inbox note), not by walking `parent` links. |
| R5 | — | **ADJ:** resolution order is task `refresh`, then note `task_refresh`, then config, then 7. Invalid values are linted and fall through to the next level. |
| R6 | Supported keymap changes to a Ready task refresh it, including making it Ready. | **ADJ:** only *human* gestures stamp, including a human unblock (Alt+[ / Alt+], or clearing `scheduled` with Ctrl+Shift+P). Automatic returns from Blocked do **not** stamp; a returned deferral is due at read time. |
| R7 | Inbox tasks start out of date. | **ADJ, extended:** *creation never stamps, on any path*: gkeep, Mac capture, routed `@project` capture, Ctrl+Shift+] promotion, `bob highlights`, or typing by hand. That is what "glance at every task I captured" requires. |
| R8 | Out-of-date tasks show up in the freshness review. | **ADJ:** two tiers. **NEW** (no stamp) comes first and is uncapped. **STALE** (expired, or back from a deferral) follows, most overdue first. |
| R9 | See out-of-date and refreshed-today counts at a glance. | **ADJ, surfaces:** a status bar item in every note, a Notice after each refresh, and a dash chip. |
| R10 | Next/previous out-of-date keys, and a refresh key that makes no other change. | Vault-wide `]s` / `[s` and Ctrl+Alt+J/K; Alt+F. **ADJ, added:** Alt+Shift+F (refresh and advance), and a `refresh` row in Ctrl+Shift+P for changing the interval. |
| R11 | An optional N-per-day limit later. | **ADJ:** a STALE-only goal meter (`freshness.stale_daily_budget`), never a filter and never applied to NEW. |
| R12 | Replaces the daily inbox glance and minimizes the weekly review. | **ADJ:** keep a ≤5-minute weekly check inside the existing weekly-prune chore: clear any leftover STALE, and look for projects with no Next or Ready task. Freshness cannot see missing tasks. |
| R13 | Recurring tasks. | **ADJ:** excluded. Their recurrence already resurfaces them, and Tasks would copy `fresh` into the next occurrence. |
| R14 | Cutover. | **ADJ:** a dry-run-first, staggered written seed of every open non-recurring task (see [Cutover and trial](#cutover-and-trial)). |
| R15 | Glossary term. | **ADJ, added:** a decision record too, because this is a policy that every writer must follow. The glossary strand must disambiguate the other "freshness" senses (V10). |

## Recommended design

### Glossary definition

Draft of the glossary strand:

> **Task Freshness** (aka freshness, fresh, stale task). The local date a human last confirmed that an open Ready
> task still needs doing as written — wording, priority, project, schedule, and dependencies — stored as
> `[fresh:: YYYY-MM-DD]` on the task line before its Tasks fields. Human gestures stamp it (supported Bob keymaps,
> `bob capture` edits of existing tasks, and the Refresh key). Task creation and automation never do. A task is
> **due for review** when it has no stamp (**new**), when its `scheduled` date arrived after the stamp
> (**resurfaced**), or when the stamp is at least its refresh interval old (**stale**). The interval is the task's
> `[refresh:: N]`, else its note's `task_refresh: N` frontmatter, else `freshness.interval` (7 days). Freshness never
> changes a task's lane, Today membership, schedule, or priority. Not to be confused with Zorg `@FRESHNESS` note
> ticks, `bob vault-sync` freshness, or P-level scheduling windows.

Write it through `/sase_memory_write` when the feature ships, together with a decision record ("Freshness Is
Stamped Only By Human Gestures And Read At Review Time") that records the
[rejected alternatives](#rejected-alternatives).

### Data model and placement

```markdown
- [ ] #task Pick up our daughter [fresh:: 2026-09-30] [created::2026-09-29] ^pickup
- [ ] #task Rename queue input [fresh:: 2026-09-30] [refresh:: 14] [created::2026-09-10] [priority:: low] [scheduled:: 2026-09-12]
- [ ] #task Read X [[#^h-8bac|🔖]] [h:: e629…] [fresh:: 2026-09-30] [created::2026-08-28]
```

The placement rule is `task_fields::stamp_fresh` in Rust and `api.freshness.stampLine` in JavaScript. Both
follow the same rule and are pinned by shared test vectors.

1. **If a `[fresh:: …]` already sits before the trailing suffix,** replace its value in place and remove any
   duplicates.
2. **Otherwise, find the trailing Tasks-parsable suffix the same way the parsers do:**
   - strip a trailing `^id`;
   - then repeatedly strip a recognized field (`priority start created scheduled due completion cancelled repeat
     onCompletion id dependsOn`) or a trailing tag.
   - Insert ` [fresh:: D]` at the start of that suffix, or at the end of the line if there is no suffix.
3. **If `fresh` sits inside the suffix** (typed by hand in the wrong place), move it out and report the lint
   `fresh_misplaced`.
4. **`refresh` uses the same rule** and sits immediately after `fresh`.
5. **Stamping today on a task already stamped today is a no-op.** No churn, and capture's `line:digest` refs
   don't go stale for nothing.

**Why the bracket Dataview form.**

- It is your proposal.
- `note_tasks::clean_description` already strips `[k:: v]` from capture pickers, the Pomodoro rows and Bob Mac
  Capture.
- Dataview types it as a date, so `bob query` can run `TASK WHERE !fresh`.

It will show up in Tasks-rendered dash descriptions and in hooks change rows, the same way `[h::]` does today.
Mute it with a `[data-dv-key="fresh"]` rule in `dataview-properties.css`.

### State computed at read time

State is computed when the queue is read, never stored.

```text
interval(t) = t.refresh ?? note(t).task_refresh ?? config.freshness.interval ?? 7      # ints, 1..365
in_scope(t) = status is Ready "[ ]" ∧ dash-visible (¬#hide, ¬_templates, ¬_conflicts,
              ¬dependency-blocked, ¬scheduled > today) ∧ ¬Today(t) ∧ ¬recurring
              ∧ ¬in a canonical daily note
state(t)    = NEW         if no valid fresh              (malformed or future ⇒ NEW + lint)
            | RESURFACED  if fresh < scheduled ≤ today   (tickler: a deferral came back)
            | STALE       if today ≥ fresh + interval(t) (inclusive: stamped Mon ⇒ due next Mon)
            | FRESH       otherwise
due(t)      = in_scope(t) ∧ state(t) ≠ FRESH
refreshed_today = open tasks (any lane) with fresh == today   # does not drop when a reviewed task moves to NEXT
```

- **Queue order.** NEW first, newest `created` first. Then RESURFACED and STALE together, earliest due date
  first, then path, then line.
  - The seed stamps whole notes on the same day, so this order naturally groups each morning's stale work by
    project. That recreates the per-project sweep you liked.
- **Calendar.** Everything uses the vault's local calendar day; midnight rollover re-evaluates the queue.
- **Conformance vectors.** `docs/freshness.md` owns the rule and the vectors, following the Today pattern:
  - no stamp;
  - the day-7 boundary;
  - task, note and config precedence;
  - malformed, future and duplicate stamps;
  - resurfaced;
  - recurring, Blocked and Today excluded;
  - placement: no fields, `[h::]` present, trailing `#hide ^id`, a misplaced `fresh`.
- **Engines.**
  - In Obsidian, bob-ledger-tools computes the predicate from the Tasks cache plus `metadataCache` frontmatter.
  - Headless, the Rust side computes it directly. bob-cli's `TaskFile` carries no frontmatter, so a pure Tasks
    query cannot do it (cld).

### Who stamps

**Rule:** a supported human gesture that already rewrites a task's line stamps that task in the same write, if
the task is still open afterwards.

| Surface | Stamps | Does not stamp |
|---|---|---|
| bob-navigation-hotkeys | Alt+F / Alt+Shift+F (the only change they make). Alt+N commit and release. Ctrl+Shift+P priority, `scheduled` (defer or pull forward), `dependsOn`, delete property, lane row, and the new `refresh` row. Ctrl+Shift+M move: routing an inbox item *is* a review. | Ctrl+Shift+P cancel (the task leaves scope). Project-level bulk `scheduled`. |
| task-status-cycler | Alt+[ / Alt+] to an open status, including a hand unblock or a reopen. | Ctrl+Enter close. Ctrl+Shift+] bullet → `#task` (that is creation). |
| block-id-prompt | Ctrl+Shift+Enter when it writes the task line (Ready → Next on link). | Link or unlink of a Next or Pending task (no task-line write). Ctrl+6 block-ID rename. |
| bob capture / Bob Mac Capture | Edits to an *existing* task: the link toggle, Ensure Next, `=x` rows, and linking an existing `@r:id`. bob-cli stamps, so Mac Capture needs no change (thin-client rule). | Any new task, on any route. |
| Automation | — | **Never:** hooks, `projects sync`, `randomize`, `gkeep pull`, `highlights`, `move-done-tasks`, nightly, vault-sync. |
| Hand editing | — | Not monitored, as you asked. Edit, then press Alt+F. |

- **Where the JavaScript lives.** Plugins normally copy small pure helpers instead of importing each other. Here,
  call the risky placement helper through the ledger-tools api (`api?.freshness?.stampLine?.(line, today) ??
  line`).
- **Why that is safe.**
  - A *missing* stamp is safe: you just see the task once more.
  - A *misplaced* stamp is unsafe: it hides Tasks fields.
  - So centralize the unsafe part, and let the safe failure happen when ledger-tools is old or absent.
- **Precedent.** Nav and block-id-prompt already call `nextBudget` / `pendingBudget` at runtime. Record the
  exception in the decision record.

### The review experience

- **Status bar** (ledger-tools): `⟳ 23 due · 3 new · ✓ 12 today`.
  - The tooltip gives the tier breakdown and the oldest lateness.
  - When `stale_daily_budget` is set, the counter reads `✓ 12/15`, and it turns green once the budget is met
    **and** new is 0.
  - Clicking it runs "next due task".
  - It updates on Tasks `cache-update`, on relevant frontmatter changes, and at midnight rollover.
- **Jumps.** Nav commands `jump-to-next-due-task` / `jump-to-prev-due-task`, bound to `]s` / `[s` through vimrc
  `exmap` (like `[[` / `]]`) and to Ctrl+Alt+J/K.
  - They read `api.freshness.queue()` fresh on every call.
  - They open the source note, center the task line (reusing `focusTaskMoveDestination`), and wrap around with a
    Notice.
  - The Tasks cache lags a few hundred milliseconds after a write, so the jump skips the key it just stamped,
    the way Alt+N adjusts its lane counts.
  - A missing block ID never blocks navigation. On a stale preimage, rebuild the queue and refuse; never write to
    a guessed line.
- **Alt+F** stamps the cursor task, or the target of a Task Link, and the next N tasks when counted.
  - It changes nothing else, refuses done and cancelled tasks, and shows `Fresh · 22 due (3 new) · ✓ 13 today`.
- **Alt+Shift+F** stamps, then jumps to the next due task. This is the fast path through the review.
- **Review note.** A small `freshness.md` with a header of counts and one Tasks block, grouped by tier. (The name
  `review.md` is already taken by a legacy Zorg note.)

  ````markdown
  ```tasks
  filter by function globalThis.app?.plugins?.plugins?.["bob-ledger-tools"]?.api?.freshness?.isDue?.(task) === true
  sort by function globalThis.app?.plugins?.plugins?.["bob-ledger-tools"]?.api?.freshness?.rank?.(task) ?? 0
  group by function globalThis.app?.plugins?.plugins?.["bob-ledger-tools"]?.api?.freshness?.tier?.(task) ?? "?"
  ```
  ````

  Headless `bob query` sees this block as empty, the same way it sees TODAY. `bob freshness list` is the
  headless view.
- **Dash.** One chip, `REVIEW 23 · 3 new · ✓ 12`, highlighted while new > 0 and linking to the review note.
  TODAY / PENDING / NEXT / READY stay exclusive and unchanged.
- **Outcomes per task** — one key each; every row except "edit" stamps on its own:

  | Decision | Key |
  |---|---|
  | still right, keep | Alt+Shift+F (or Alt+F) |
  | keep, but see it less often | Ctrl+Shift+P → `refresh` → 14 / 30 / 90 |
  | not now | Ctrl+Shift+P priority (rolls a P-level `scheduled` date) |
  | do today / commit | Ctrl+Shift+Enter / Alt+N |
  | route to a project | Ctrl+Shift+M |
  | drop | Ctrl+Shift+P cancel |
  | wording is wrong | edit, then Alt+F |

### Rituals

**Morning** (this replaces the "Morning review" chore text in `gtd_daily.md`):

1. `bob gkeep pull` (the existing chore).
2. `]s` / Alt+Shift+F until the status bar shows **0 new**. This step is never skipped and never capped.
3. Continue through STALE until **0 due**, or until the budget meter goes green.
4. PENDING → NEXT: link today's work (≤3 themes) and release the rest. READY stays a pull list, not reading
   material.

**Weekly** (add one line to the existing weekly-prune chore, not a new ritual):

- clear any leftover STALE, or deliberately lengthen that note's interval;
- prune NEXT to ≤15 and PENDING to ≤10;
- glance for projects with no Next or Ready task.

### Keeping the load down

Apply these in order, and change one at a time.

1. **Lengthen intervals on large, slow notes.** For example, `task_refresh: 14` on `sase.md`. This is Taskwarrior's
   own advice: if review changes nothing, review less often.
2. **Shrink the pool during review.** A P3 or P4 deferral buys 1–12 months without a glance, and cancelling is
   allowed.
3. **Only then set `freshness.stale_daily_budget`** (start at 15). Leftover STALE rolls over and stays visible in
   the counts; the weekly line catches it up.
4. **Deferred ideas.**
   - Automatic back-off (each unchanged refresh doubles the interval) cuts load the most. But it needs
     machine-owned state beside your override. Revisit it if you keep choosing "see less often".
   - Random sampling cannot guarantee NEW, so at most it is a tie-breaker.

### Cutover and trial

1. **Land after `bob-cli-2y.12`** and the lane triage to NEXT ≤15 and PENDING ≤10. Seeding before the triage would
   stamp tasks you are about to release.
2. **Optional but recommended: one deliberate `gkeep_inbox.md` triage** before seeding. Most of its 65 items are
   SASE ideas that belong in `sase.md` (Ctrl+Shift+M stamps them as they move). Afterwards, set `task_refresh: 2`
   on `gkeep_inbox.md` and `mac_inbox.md`, so a glanced-but-unrouted capture comes back within two days, not
   seven.
   - If you would rather keep `gkeep_inbox.md` as a standing someday list, give it a long interval instead (cdx
     suggested 30).
3. **`bob freshness seed --dry-run`, then apply from one machine and run `bob vault-sync run`.** The seed:
   - bin-packs open non-recurring **Ready** tasks by note into 7 daily groups (splitting `sase.md` by line order)
     and stamps each group `today − 7 + k`;
   - stamps **Blocked, Next and Pending** tasks with the cutover date, so that returning deferrals and releases
     arrive as RESURFACED or STALE, never as NEW.

   This is a one-time diff of several hundred lines. The seeded dates are a scheduling device: every seeded Ready
   task gets a real review within the first interval.
4. **Two-week trial.** Keep the design if, on at least 10 of 14 mornings:
   - NEW reaches 0 before planning;
   - the whole ritual's median is ≤10 minutes;
   - STALE debt is flat or falling;
   - no new capture was missed;
   - no freshness write ever changed a lane, schedule, priority or Task Link.

   If the time bound fails, work through [Keeping the load down](#keeping-the-load-down) in order. Never cap NEW.

### Where the code lives

| Repo | Change |
|---|---|
| bob-cli | `docs/freshness.md` (definition and vectors). `task_fields::stamp_fresh` / `set_refresh`, the first shared field inserter. A `freshness` predicate module. A `freshness:` config block (`interval`, `stale_daily_budget`). `bob freshness list \| seed` — read `cli_rules.md` first: alphabetical options, short aliases, color only on a TTY. Stamping in the capture paths that edit existing tasks. Optionally, an additive `bob plan` meter. Hooks: no change, beyond a test that they preserve the field. |
| bob-plugins | **ledger-tools:** an additive `api.freshness` namespace (`state`, `isDue`, `tier`, `rank`, `queue`, `counts`, `intervalFor`, `stampLine`, `setRefresh`), the status bar, the config read beside `loadPlanCaps`, and a rollover reload. **nav:** the jumps, Alt+F, Alt+Shift+F (with a raw keydown listener like Alt+N's), the Ctrl+Shift+P `refresh` row, and stamping in Alt+N, Ctrl+Shift+P and Ctrl+Shift+M. Also stop using end-append `upsertBulletProperty` for `fresh` / `refresh`. **task-status-cycler, block-id-prompt:** best-effort stamping through the api. Deploy with `bob plugins sync`. |
| Vault | The review note, the dash chip, the vimrc maps, the CSS rule, the `gtd_daily.md` chore text, and `task_refresh` on the inbox notes and `sase.md`. |
| chezmoi | `freshness:` defaults in `config.yml`. |
| Memory | The glossary strand and the decision record, via `/sase_memory_write`. |
| Bob Mac Capture | None. |

## Where the researchers disagreed

Each row gives the researchers' positions, the resolution, and why. The tags cdx, cld, grk, mus and gem name the
five swarm reports (see [About this report](#about-this-report)); V1–V12 refer to the findings in
[What was verified](#what-was-verified).

| Topic | Positions | Resolution | Why |
|---|---|---|---|
| **Where the stamp lives** | End of line before `^id`, via the existing upsert (cdx, implicitly). Before the trailing Tasks fields (cld, gem). A managed `🌱 FRESH [on::]` child bullet (grk). Inline, with the stop-parsing effect missed (mus). | **Inline, before the trailing Tasks suffix**, through one helper per language. The child bullet is the documented fallback. | The end-of-line placement breaks parsing (V3, V4). A child bullet keeps the task line clean, but it adds a line to each of 176+ tasks, turns single-line guarded writes into multi-line block edits, and the evaluator could no longer read the stamp from the Tasks cache's `originalMarkdown`. The inline field is short, travels with the line, has the `[h::]` precedent, and can be muted with CSS (V9). |
| **Teach bob-cli's parser to recognize `fresh`** | gem: add `fresh` to `try_take_dataview_field`. | **Reject.** | `bob query` would then parse lines differently from Obsidian Tasks, which the dash uses. The native engine exists to mirror Tasks. |
| **Scope** | Ready only (cdx, grk, mus, gem). All actionable lanes: Ready, Next, Pending (cld). | **Ready only in v1**, with a lane-parametric predicate. | That is what you asked for. Next and Pending are already walked in the daily PENDING → NEXT step and pruned weekly under the sticky-lanes decision. Revisit if the weekly prune keeps getting skipped; it is then a one-line change. |
| **Inbox guarantee** | State-based: no stamp means NEW (cdx, cld, mus). Path-based: an INBOX section for `gkeep_inbox.md` / `mac_inbox.md` that Refresh cannot clear (grk, gem). | **State-based NEW**, plus a **short note interval** on inbox notes after a one-time triage. | Routed desk captures skip the inbox notes, so a path rule misses them. grk's worry (a tired Refresh snoozes an unrouted inbox item for a week) is handled by `task_refresh: 2` on inbox notes, with no path special case. |
| **Automated Blocked → Ready** | Hooks delete `fresh` on unblock (cdx). A read-time tickler makes it due (cld). "Just don't stamp" (grk, mus). gem stamps on unblock. | **Never stamp. A read-time tickler for `scheduled` arrivals. Dependency unblocks are deferred.** | This avoids adding text writes to the hooks, which today only swap checkbox bytes. Dependency unblocks usually come back stale anyway; add a rule for them only if you miss one. |
| **Daily cap** | Ship on day one as a query `limit 10` (mus, gem). Later, only as a fallback (cld, grk). Cap stale and legacy only (cdx). | **A STALE-only budget *meter*, default off; NEW is never capped.** | `limit N` never completes: refresh 10 and the next 10 appear. A meter (`✓ 12/15`) tells you when you may stop and hides nothing. The seed (see [Cutover and trial](#cutover-and-trial)) removes the day-one flood, which was the case for shipping a cap immediately. |
| **Default interval** | 7 days (4 reports). 14 days for projects, 7 for areas, 3 for inbox (gem). | **7 days, as you specified**, with note overrides such as 14 on `sase.md`. | Load is a per-note property. A global 14 would halve the review rate for volatile personal tasks too. |
| **Cutover** | No seed: LEGACY state, epoch in config (cdx). No seed, the cap absorbs the flood (mus). Staggered written seed (cld, grk, gem). | **A written, staggered seed of *every* open non-recurring task.** | A zero-write epoch cannot tell "existed at cutover" from "arrived after" (Keep's `created` predates the pull, V5). cld's seed stamped only in-scope Ready tasks, so about 120 deferrals returning this week would have arrived as **NEW** and flooded the uncapped tier. None of the reports caught this; seeding Blocked, Next and Pending closes it. |
| **Review surface** | A dedicated review note plus a dash chip (cdx). Source notes, a status bar, and a dash overlay section (cld). Dash INBOX and STALE sections (grk, mus, gem; gem even replaces READY). | **Source-note jumps, a status bar, a dedicated review note, and one dash chip.** | Keymaps act on editor lines. A dash section would violate the exclusivity decision (V7). |
| **Next/previous keys** | `]s` / `[s` (cld). Ctrl+Alt+J/K (grk, mus). Alt+Shift+J/K (cdx, gem, but gem's are in-note only). | **`]s` / `[s` in the vimrc, plus Ctrl+Alt+J/K** as the Obsidian hotkeys. | The jump must be vault-wide. J/K then forms a family: Ctrl = headers, Ctrl+Shift = open tasks in this note, Ctrl+Alt = due tasks across the vault. |
| **Refresh key** | Alt+F (cld, gem). Ctrl+Alt+R (grk). Alt+R and advance (cdx). | **Alt+F stamps and stays** (counted `N<Alt+F>`, works on Task Links). **Alt+Shift+F stamps and jumps to the next due task.** | "Refresh and advance" is how OmniFocus and tasksh behave (V12), and it makes the review loop one key per task. Alt+F sits next to Alt+N in the lane-gesture family. |
| **`never` interval** | Allowed (cld). Rejected (cdx, mus). | **Reject in v1**; the maximum is 365. | An immortal Ready task is exactly the rot this feature exists to prevent. `#hide`, deferral, or cancelling are the honest options. |
| **Hooks lints** | Lint a missing `fresh` (mus). | **Lint only malformed or misplaced `fresh`.** | A missing stamp is the normal NEW state, so linting it would be noise. |

## Rejected alternatives

| Alternative | Why not |
|---|---|
| Keep walking READY every morning | O(pool) every day; this is the cost you want to remove. |
| A "created since yesterday" view | Keep's `created` predates the pull, and a skipped morning drops a day. It does nothing for backlog rot. The NEW tier covers its good part. |
| Inbox-only review | Solves the pickup case but leaves filed tasks to rot, and routed captures bypass it. It survives as the short inbox-note interval. |
| Per-project review stamps only (OmniFocus, Zorg `@FRESHNESS`) | Re-reads unchanged tasks, and one file stamp lets 65 unrouted captures go unseen. It survives as note-level *interval defaults* and note-grouped seeding. |
| Rolling `scheduled` as the review date | A future `scheduled` means Blocked and hidden. It conflates "not now" with "look again". |
| Reusing Tasks' `start` date | It parses natively, but it has the wrong meaning, side effects on urgency, and collisions with recurrence. |
| A side-car store | No stable key ([V6](#what-was-verified)), and it breaks when tasks move. |
| Using mtime or git blame as "last touched" | It counts sync and hooks writes as attention, and mtime is note-wide. |
| Stamp on view | Seeing a task is not confirming it. |
| A "Needs Review" checkbox status | Status is for lanes. It would fight the hooks and Alt+N. |
| Auto-expiring stale tasks | It loses tasks silently, the opposite of the goal. |

## Risks

- **Rubber-stamping.** Word the key and Notice as "confirm". Measure how often a review leads to an action
  (defer, cancel, move), not just how many refreshes you press.
- **Placement regressions.** One helper per language, shared vectors, the `fresh_misplaced` lint, and a
  regression test that a stamped line still parses `created`, `scheduled`, `priority` and `dependsOn` in both
  engines.
- **Write churn.** About 20–40 single-line edits a morning, which vault-sync already handles. Same-day
  re-stamps are no-ops, and writes go through guarded `Vault.process()`.
- **Two implementations** (Rust and JavaScript). Mitigated the way Today is: the doc owns the rule, and both sides
  run its vectors.
- **Confounding the sticky-lanes trial.** Start freshness after that trial's baseline, or re-baseline its
  "≤5 min" metric to the combined ritual.
- **Term collision.** The glossary strand must name the other three meanings of "freshness" (V10).

## Open questions for Bryan

1. **`gkeep_inbox.md`:** do a one-time triage, then `task_refresh: 2` (recommended), or keep it as a someday list
   with a long interval?
2. **Desk captures:** keep "creation never stamps" for routed `@project` / Mac captures and hand-typed tasks
   (recommended; they are the cheapest glances), or stamp them at creation to save roughly 5–10 glances a day?
3. **Scope:** Ready-only in v1 (recommended), or include Next and Pending now and retire the weekly prune?
4. **Alt+Shift+F:** "refresh and advance" (recommended), or "refresh and see less often" (cld)?
5. **Names:** `fresh` / `refresh` / `task_refresh` / `freshness.md` / `]s`, or something like `reviewed` /
   `review_every`?

## Recommended solution

Adopt **Task Freshness as a review lease on visible, non-recurring Ready tasks**: a human-confirmed local date
that is never a status and never changes a task's lane.

1. **[The field](#data-model-and-placement).**
   - Store the stamp as an optional `[fresh:: YYYY-MM-DD]`, placed **before** the task's trailing Tasks fields by
     a single helper per language.
   - A missing stamp means NEW, and is due now.
   - The interval comes from `[refresh:: N]`, else the containing note's `task_refresh: N`, else
     `freshness.interval`, else 7 days.
2. **[Who stamps](#who-stamps).**
   - Only human gestures stamp: every supported keymap or capture edit that already rewrites the line, and the
     Refresh keys.
   - Creation and automation never stamp.
   - A returning deferral is due at read time, through the tickler rule.
3. **[The contract and code](#where-the-code-lives).**
   - Put the definition and conformance vectors in bob-cli's `docs/freshness.md`, with a Rust evaluator,
     `bob freshness list | seed`, and stamping in capture's edit paths.
   - Make bob-ledger-tools the Obsidian-side evaluator: an `api.freshness` namespace and the status bar.
   - Put the jumps and Refresh keys in bob-navigation-hotkeys: `]s` / `[s` and Ctrl+Alt+J/K; Alt+F; Alt+Shift+F.
4. **[The review surface](#the-review-experience).**
   - Review in the source notes.
   - Keep the dash exclusive and add one REVIEW chip that links to a small review note.
5. **[Every morning](#rituals).**
   - Pull Keep, then clear **NEW** (uncapped).
   - Then work **STALE** until it is empty or an optional budget meter is met.
   - Then plan from PENDING → NEXT.
6. **Every week.** Add one line to the existing prune chore: clear leftover STALE, and look for projects with no
   next action.
7. **[Rollout](#cutover-and-trial).**
   - Roll out after `bob-cli-2y.12`.
   - Do an optional one-time `gkeep_inbox` triage.
   - Run a dry-run-first, staggered seed of every open non-recurring task, so NEW means "arrived after cutover".
   - Tune intervals per note during a two-week trial.

Success means:

- yesterday's captures are always acknowledged before planning;
- the review debt is flat or falling;
- the whole ritual stays around 10 minutes;
- freshness never changes a task's execution state by itself.

## About this report

- **Date:** 2026-09-30
- **Lead researcher:** consolidation of five independent reports (`__cdx`, `__cld`, `__grk`, `__mus`,
  `__gem` in this directory) plus the lead's own verification against bob-cli, bob-plugins, the installed
  Obsidian plugins, the live vault, and outside prior art.
- **Context:** epic `bob-cli-2y` (sticky Next/Pending lanes, a Today read from the ledger), whose last phase
  (`bob-cli-2y.12`, install and end-to-end check) is still in progress.
- **Question:** Should every Ready task carry a human-confirmed `fresh` date (7-day default, per-task and
  per-project overrides, stamped automatically by supported keymaps), with a daily review of out-of-date tasks
  that shows counts and has next/previous/refresh keys? Critique the plan, adjust the requirements where that is
  justified, and recommend an implementation.

## Sources

- **Swarm reports** (this directory):
  - `ready_task_freshness_review__cdx.md`
  - `ready_task_freshness_review__cld.md`
  - `ready_task_freshness_review__grk.md`
  - `ready_task_freshness_review__mus.md`
  - `ready_task_freshness_review__gem.md`
- **Project:**
  - epic `bob-cli-2y` and `plan:202609/retire_now_sticky_lanes.md`;
  - `decisions:task-lanes-are-sticky` and `decisions:today-is-read-from-the-ledger`;
  - glossary: Pomodoro, Schedule Log, Task Link, Work Log.
- **bob-cli:**
  - `src/native/dataview/tasks/task.rs` (`parse_details`, `try_take_dataview_field`);
  - `src/native/gkeep/render.rs`;
  - `src/native/capture/mod.rs`;
  - `docs/projects.md`, `docs/dataview.md`.
- **bob-plugins:**
  - `bob-navigation-hotkeys/main.js` (`upsertBulletProperty`, `getBulletPropertyAppendIndex`, the raw Alt+N
    listener);
  - `bob-ledger-tools/main.js` (api v2);
  - the plugins' default hotkeys.
- **Installed plugins:** Obsidian Tasks 8.4.0 (the field-extraction loop, `hashTagsFromEnd`); Dataview 0.5.68
  (`data-dv-key`).
- **Vault (read-only):**
  - `dash.md`, `gtd_daily.md`, `gkeep_inbox.md`, `mac_inbox.md`;
  - `.obsidian/hotkeys.json`, `obsidian_vimrc.md`, `.obsidian/snippets/`;
  - `bob query` Ready JSON and a `created` scan, both taken on 2026-09-30.
- **External:**
  - [Taskwarrior: Tasksh Review](https://taskwarrior.org/docs/review/)
  - [tasksh(1) man page](https://www.mankier.com/1/tasksh)
  - [Random Geekery taskrc (`_reviewed` report)](https://randomgeekery.org/config/shell/taskwarrior/)
  - [OmniFocus 4 Reference Manual: Perspectives / Review](https://support.omnigroup.com/documentation/omnifocus/universal/4.3.3/en/perspectives/)
  - [OmniFocus at School: Reviews](https://www.omnigroup.com/blog/omnifocus-at-school-reviews)
  - [GTD Weekly Review checklist](https://gettingthingsdone.com/wp-content/uploads/2016/04/GTD-WeeklyReview.pdf)
  - [Tasks: filters and custom functions](https://publish.obsidian.md/tasks/Queries/Filters)
  - [Tasks: limiting](https://publish.obsidian.md/tasks/Queries/Limiting)
  - [Dataview: metadata on tasks](https://blacksmithgu.github.io/obsidian-dataview/annotation/metadata-tasks/)
  - [Obsidian Vault API (`process`)](https://docs.obsidian.md/Plugins/Vault)
