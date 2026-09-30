# Task freshness: a rolling review that guarantees yesterday's captures get a glance (cld)

## Bottom line

1. **Yes, build it. It is the right shape for your problem.**
   - The old morning Ready walk cost about **186 glances a day**, one per Ready task.
   - A 7-day freshness stamp cuts that to about **27 a day plus new arrivals**, and it still guarantees that every new
     capture is seen.
   - The key property is that "never reviewed" is a **state** (no stamp), not a time window like "created since
     yesterday". A state survives a skipped morning, a late `bob gkeep pull`, and captures that skip the inbox.
     `created` can't do this: `bob gkeep pull` writes the **Keep note's** creation date, not the pull date.
2. **The stamp must go *before* the Tasks fields on the line. This is a correctness requirement, not style.**
   - Obsidian Tasks 8.4.0, bob-cli's native Tasks engine and `bob task-status-hooks` all read fields from the **end**
     of the line and stop at the first field they don't recognize.
   - So a `[fresh:: …]` appended at the end, which is how every current writer appends fields, would hide `created`,
     `priority` and `scheduled`. The hooks would then stop deriving Blocked.
   - There is precedent for the safe placement: `bob highlights` already writes `[h:: …]` before `[created::]`.
3. **Automation must never stamp.** A stamp claims that a human looked at the task.
   - When a task leaves Blocked *by a human gesture*, it gets stamped, as you asked.
   - When it leaves Blocked *by itself*, it becomes **due** at read time instead. That covers a deferral date arriving
     or the hooks unblocking it. This is a tickler rule; no write is needed.
4. **Adjustment: keep two queues, and never cap the first.**
   - **New** means never stamped. You must clear all of it every morning; this is your hard requirement.
   - **Stale** means stamped, but past its interval or resurfaced since.
   - Your "only review N a day" fallback may cap *only* the stale queue. If it capped new tasks too, it would quietly
     break the requirement this design exists for.
5. **Adjustment: cover Next and Pending too, not just Ready.**
   - Sticky lanes (epic `bob-cli-2y`) removed automatic forgetting.
   - Their decision record makes a weekly prune mandatory, and you don't do weekly reviews.
   - With freshness, the gestures that work a task keep stamping it, so only *neglected* lane tasks come up. That is
     exactly the weekly prune, done in daily slices.
6. **Review in the source notes, not on the dash.**
   - `]s` / `[s` jump to the next or previous due task anywhere in the vault.
   - **Alt+F** stamps the task under the cursor (it also takes a count and works on Task Link lines, like Alt+N).
   - **Alt+Shift+F** stamps it and makes it come back less often.
   - A **status bar item** shows `⟳ 23 due · 3 new · ✓ 12 today` in whatever note you are in.
   - Every existing edit key already works in the source note. Most of them (Ctrl+Shift+P, Alt+N, Ctrl+Shift+M,
     Ctrl+Shift+Enter) will also stamp.
7. **The real risk is load, not mechanics.**
   - Daily load ≈ **(in-scope pool ÷ interval) + new captures + resurfaced deferrals**.
   - With about 250 in-scope tasks, that is roughly 35–50 a day in the first weeks.
   - The levers, in order:
     1. shrink the pool with P-level deferral during review;
     2. "see less often" (Alt+Shift+F, or `task_refresh` on big notes);
     3. only then a cap on stale tasks.
8. **Cutover needs seeding.**
   - On day one about 250 tasks have no stamp, which would make everything "new" at once.
   - Seed stamps spread over 7 days, grouped by note, so each morning's stale queue is a few whole projects.
   - This is honest: you have walked Ready every morning until now.

## Question and inputs

- **Date:** 2026-09-30, while epic `bob-cli-2y` (sticky Next/Pending lanes, a Today derived from the ledger) is
  rolling out.
- **Question:** Should every Ready task carry a `fresh` date? It would be refreshed automatically by keymap gestures,
  with a 7-day default interval and per-task and per-project overrides, and a daily "freshness review" of out-of-date
  tasks, with counts and next/previous/refresh keys. Critique the plan, adjust the requirements, and recommend an
  implementation.
- **Inputs:**
  - the `bob-cli-2y` epic bead and its plan (`plan:202609/retire_now_sticky_lanes.md`);
  - its research report (`research:202609/retire_now_sticky_lanes_ledger_today/…`);
  - the `decisions` web (`task-lanes-are-sticky`, `today-is-read-from-the-ledger`, `task-status-is-derived`,
    `mac-capture-is-a-thin-client`) and the glossary web;
  - bob-cli source and docs;
  - bob-plugins source (all six plugins);
  - the installed Tasks 8.4.0 bundle;
  - the live vault (read-only: `dash.md`, `gtd_daily.md`, the inbox notes, project notes, `hotkeys.json`,
    `obsidian_vimrc.md`);
  - `bob query` counts on 2026-09-30.

## What I verified

| # | Finding | Evidence |
|---|---|---|
| 1 | **Pool size.** Ready is 186 tasks in 27 notes: `gkeep_inbox.md` 65 (35%), `sase.md` 48, `sase_remote.md` 11, then a long tail. Next is 26 and Pending is 52. 10 Ready tasks are recurring chores. | `bob query --tasks 'status.type is TODO' --origin dash.md -f json` and the same for `IN_PROGRESS` and `Next` |
| 2 | **Ready is old, not fresh.** Median age since `created` is 17 days. 85 tasks are 14–30 days old, 27 are 30–90, and only 2 were created in the last 2 days. So the daily Ready walk mostly re-read unchanged tasks, as you suspected. | same query, `created` values |
| 3 | **Capture rate.** 411 non-recurring, non-daily-note tasks carry a September `created` date: 13.7 a day, weekly 103 / 127 / 87 / 77. | vault scan of `[created:: 2026-09-…]` on `#task` lines |
| 4 | **Deferral pool and resurfacing rate.** 290 open `[?]` tasks, 277 of them with a future `scheduled`. 120 return in the next 7 days (17 a day), 134 in days 8–30 (5.8 a day). `p:<N>` rolls `scheduled` inside the P-level windows (P1 2–7 days, P2 8–30, P3 31–90, P4 91–365). | vault scan; `docs/capture.md` |
| 5 | **The trailing-field trap.** Tasks 8.4.0 builds every Dataview-format field regex with a `$` anchor (`Sr(...)`) and parses fields and trailing tags in a loop from the end. bob-cli's native engine (`dataview/tasks/task.rs` `parse_details` / `try_take_dataview_field`) and the hooks (`task_status_hooks/parse.rs` `task_metadata`: `_ => false` → `break`) behave the same way. An unknown field **after** `[scheduled::]` hides `scheduled` from all three. | Tasks bundle, bob-cli source |
| 6 | **No shared field inserter, and current writers append at the end.** Capture appends `created → priority → scheduled → ^id` (`capture/plan.rs`, `append_*_property`). `bob projects sync` inserts before `^id`. bob-navigation-hotkeys `upsertBulletProperty` appends before `^id`, and its own comment warns that "Tasks-format parsers read trailing fields right to left". A `fresh` field written "the usual way" would land in the wrong place. | bob-cli and bob-plugins source |
| 7 | **Precedent for correct placement.** `bob highlights` writes `… [h:: <hash>] [created::D]` (`highlights_ref/annotation_tasks.rs`), and those lines parse correctly in Tasks. | vault `sase_memory.md`, `sase.md` |
| 8 | **Display surfaces mostly hide inline fields.** `note_tasks::clean_description` strips `[k:: v]` for capture pickers, `capture-complete`, the Pomodoro close/start rows, `bob plan` `today_tasks`, `gkeep list`, and so for Bob Mac Capture too. It would **show** in hooks change rows (`task_status_hooks/parse.rs` `task_description`) and in Tasks-rendered dash descriptions, exactly as `[h:: …]` does today. | bob-cli source |
| 9 | **`created` is the wrong signal for "captured yesterday".** `bob gkeep pull` writes `[created::]` = the Keep note's creation date, not the pull date. The default `bob capture` destination is `mac_inbox.md`, but routed captures (`@sase …`) go straight into project notes. So neither "created since yesterday" nor "lives in an inbox note" finds every new task. | `gkeep/render.rs`, `docs/gkeep.md`; `capture/mod.rs` `INBOX_FILE` |
| 10 | **Tasks exposes project frontmatter to queries; bob-cli's engine doesn't.** `task.file.property(key)` exists in Tasks 8.4.0. bob-cli's native engine defines it but `TaskFile` carries no properties, so it returns `null` headless. The headless predicate therefore has to be Rust code, not a Tasks query. | Tasks bundle; `dataview/tasks/js.rs`, `task.rs` |
| 11 | **Plugin infrastructure exists for most of the UI**, but nothing covers the whole vault. bob-ledger-tools api v2 already reads `config.yml` (`loadPlanCaps`), reads the Tasks cache (`getTasks`), runs a 60 s rollover interval, and fires `obsidian-tasks-plugin:reload-open-search-results`. nav has in-file open-task jumps (Ctrl+Shift+J/K), the counted `N<Alt+N>` capture listener, Task Link target discovery, and an open-note-then-jump helper (`focusTaskMoveDestination`). **No plugin** has a status bar item, editor decoration, or a vault-wide jump. | bob-plugins source |
| 12 | **Free keys.** Alt+F, Alt+Shift+F and Alt+J/K are unbound in `hotkeys.json` and in plugin defaults. The vimrc maps `[[`/`]]` and `[<Space>`/`]<Space>`, but not `]s`/`[s`. | `~/bob/.obsidian/hotkeys.json`, `~/bob/obsidian_vimrc.md` |
| 13 | **Only 29 of 186 Ready tasks have a block ID**, and the hooks move task blocks between status headings (`task_status_groups::transform`). A freshness store outside the line would have no stable key. | Ready query `blockId`; hooks source |
| 14 | **Stamping changes the line digest.** `note_tasks::line_digest` hashes the whole line, so a `line:digest` picker ref taken before a stamp goes stale. | bob-cli source |
| 15 | **The rituals are already daily.** `gtd_daily.md` has "Import inbox tasks from Google Keep" and the new "Morning review (≤5 min): PENDING → NEXT → READY". The weekly prune is a `[?]` chore scheduled for 2026-10-05. | vault |

## Critique of the plan

### What is right

- **Cost follows attention, not list size.**
  - The daily Ready walk costs O(list) every day.
  - A per-task stamp costs O(list ÷ interval) plus arrivals, and it focuses the time on what you haven't seen.
  - This is GTD's weekly review done in daily slices. That suits someone who doesn't do weekly reviews.
- **"Unreviewed" as a missing stamp is the right primitive** ([row 9](#what-i-verified)).
  - It persists until you act on it.
  - It needs no knowledge of how the task was captured.
  - It catches a routed desk capture as surely as a Keep note.
- **Stamping on existing gestures keeps active work out of the review.** Anything you link, commit, work, schedule or
  re-prioritise is fresh by construction. The review only shows what you have been ignoring.
- **Overrides match how the vault is organised.**
  - Tasks live in project notes, and project frontmatter already carries machine-maintained `task_count` and
    `open_task_count`.
  - So a per-note interval is natural, and a per-task override covers the exceptions.
- **It completes the sticky-lanes design.** That design's main cost is "no automatic forgetting". Freshness gives a
  forgetting *signal* without automatic demotion. It is a much better answer to the stale-lane risk than the "age-based
  Next decay" the epic held in reserve.

### What needs changing

Each item below becomes an ADJ row in [Adjusted requirements](#adjusted-requirements).

1. **"Blocked → Ready refreshes" must be about gestures, not transitions.**
   - Most blocked → ready transitions are automatic: a `scheduled` date arrives, or the hooks' `Unblock` fires when a
     dependency closes. Nobody looked at those tasks, so a stamp would be a false claim.
   - Hooks writes are also deliberately one-byte checkbox swaps.
   - So:
     - human gestures that unblock stamp (clearing a schedule with Ctrl+Shift+P, cycling `?` away with Alt+[/],
       linking with Ctrl+Shift+Enter);
     - automatic unblocks make the task **due** at read time instead.
   - This is the GTD tickler: a deferral is a promise to look again on that date. It also matches R10 of the lanes
     epic ("returns as Ready = re-triage").
2. **Two tiers with different rules.**
   - Never-stamped tasks are the hard requirement: they must be cleared every morning and can never be capped.
   - Stale tasks are maintenance: they can be capped, batched or slowed.
   - A single "out-of-date" list hides that difference. Your N-per-day fallback would silently start dropping new
     captures on busy days.
3. **Scope: every actionable open lane.**
   - Ready alone leaves Next and Pending with no ageing signal, and those lanes are sticky now.
   - The gestures that work a lane task (link, `=x`, release, commit) stamp it, so only neglected ones surface. That
     costs at most (15 + 10) ÷ 7 ≈ 4 a day at the caps.
   - It replaces the weekly prune chore rather than adding work.
   - If you want Ready-only anyway, it is a one-line change to the scope predicate.
4. **Placement is mandatory** ([row 5](#what-i-verified)).
   - Put `fresh` immediately before the line's trailing run of Tasks fields, tags and `^id`.
   - Put the risky placement logic in **one** helper per language, pinned by shared vectors.
   - Don't copy it into four plugins.
5. **Creation never stamps, whatever the path.**
   - You said inbox tasks start out of date. I extend that to *every* new task: gkeep, the Mac inbox, a routed
     `@project` capture, Ctrl+Shift+] promotion, and `bob highlights`.
   - That is what "glance at every task I captured the previous day" literally requires.
   - Routed desk captures are the cheapest glances (you remember them), and one rule beats branching per capture
     path.
   - If the next-morning glance at desk captures proves pointless, revisit this rule alone.
6. **Seed at cutover** ([Cutover](#cutover-seeding)). About 250 tasks with no stamp would otherwise make day one a
   full review of everything, which is the cost this design exists to remove.
7. **Review in the source notes, with counts in the status bar.**
   - Keymaps act on editor lines, and every editing tool plus the task's context (siblings, notes, logs) is in the
     source note.
   - Rendered dash results support none of that.
   - The dash keeps an entry point (a REVIEW chip and section). The status bar answers "how many left / how many done
     today" wherever you are.
8. **Control load with deferral and "see less often" before a cap.**
   - A cap followed by a catch-up weekly review brings back the weekly review you don't do. It also builds hidden debt.
   - The honest levers:
     - make the carrying cost of a Ready task visible (one glance per interval);
     - make deferring (P-levels, which already exist) and slowing down cheaper than keeping.

### What it costs

| Cost | Severity | Mitigation |
|---|---|---|
| Daily review load about 35–50 in the first weeks ([Load](#load-and-how-to-keep-it-small)) | **High** | Defer during review, Alt+Shift+F, `task_refresh` on big notes, then a cap on stale tasks only |
| Another field on every task line: visual noise in Tasks-rendered results and the Tasks edit modal | Medium | Keep it short (`[fresh:: 2026-09-30]`). Optional CSS snippet to mute it. The pickers and Mac UI already strip it. |
| Many writers must stamp. A miss means an extra review, never a lost task. | Low | One JS helper (ledger-tools api) and one Rust helper, with a stamping row in each gesture's tests |
| Wrong placement would break Tasks and hooks parsing | **High if wrong** | One helper per language, shared vectors, and a lint for a misplaced `fresh` |
| Git churn: about 30–50 line edits a day; seeding writes about 250 lines at once | Low | vault-sync already commits. Seed from one machine while the others are idle. |
| `line:digest` picker refs go stale after a stamp ([row 14](#what-i-verified)) | Low | Capture already rejects a digest mismatch. Retry. |
| Another definition implemented twice (Rust and JS) | Medium | The Today pattern: `docs/freshness.md` owns the rule, and both sides run its vectors |
| It confounds the sticky-lanes trial ("morning review ≤ 5 min") | Low | Start after the `bob-cli-2y` rollout and re-baseline that metric to the combined ritual |

## Alternatives considered

| Alternative | Verdict | Why |
|---|---|---|
| **"Captured since yesterday" view on `created`** | Reject | It needs no new field, but gkeep's `created` is the Keep note's date ([row 9](#what-i-verified)), and a skipped morning drops a day. It also does nothing for the stale backlog. |
| **Inbox zero only** (route everything out of the inbox notes daily) | Complement, not a substitute | Routed captures bypass the inbox. It also doesn't age the backlog. Its good part is available as `task_refresh: 3d` on inbox notes ([Open questions](#open-questions-for-bryan)). |
| **Per-project review stamps** (`reviewed:` in project frontmatter; review whole projects in rotation) | Reject as primary | Cheap to write and good for context and the old "≤5 per project" judgement. But it re-reads unchanged tasks (the waste you want to cut) and can't point to a new task inside a 48-task note. Its good part is kept: [traversal is grouped by note](#the-review-loop) and seeding is grouped by project. |
| **Rolling `scheduled` as the review date** (review = defer to +7 days) | Reject | Future `scheduled` means Blocked and hidden. It merges "not now" with "look again", and you want reviewed Ready tasks to stay visible and pickable. |
| **Stamp on view** (seen on screen = fresh) | Reject | Passive viewing isn't confirmation. It would defeat the purpose. |
| **Last-touched from git blame or mtime** | Reject | It counts hooks and sync writes as "looked at", it is expensive, and lines move. |
| **Side-car store** (`_meta/freshness.json`) | Reject | No stable key: 157 of 186 Ready tasks have no block ID, and the hooks move blocks between headings ([row 13](#what-i-verified)). |
| **Reuse Tasks' `start::` as the stamp** | Reject | Clever, because Tasks would parse it natively, but it collides with Tasks semantics and filters and uses up a field you may want later. |
| **Automatic back-off** (each unchanged refresh doubles the interval) | Defer | It cuts load most. But it needs machine-owned state on the line next to your `refresh` override. The explicit Alt+Shift+F gets most of the benefit with no hidden state. Revisit if you find yourself pressing Alt+Shift+F on nearly everything. |
| **Auto-expire stale tasks** ("task bankruptcy") | Reject | It loses tasks silently, which is the opposite of the goal. |

## Adjusted requirements

My changes are marked ADJ.

| # | Requirement | Origin |
|---|---|---|
| F1 | Every in-scope task can carry `[fresh:: YYYY-MM-DD]`: the last date a human confirmed it still needs doing, as written. **ADJ:** the field sits immediately before the line's trailing Tasks fields, tags and `^id`, never after them. | yours, placement ADJ |
| F2 | The default refresh interval is 7 days. **ADJ:** it lives in `config.yml` as `freshness.interval: 7d`, not hard-coded in two languages. | yours |
| F3 | Per-task override `[refresh:: 14d]`. Values are `Nd`, `Nw`, or `never`. | yours (name ADJ) |
| F4 | Per-note override in frontmatter: `task_refresh: 14d`. It applies to every task in that note: projects, and also inbox and area notes. **ADJ:** no inheritance through `parent` in v1. | yours (name and scope ADJ) |
| F5 | Resolution order: task `refresh` → note `task_refresh` → `freshness.interval` → 7d. Invalid values are lints and fall through to the next level. | ADJ |
| F6 | **ADJ.** Only human gestures stamp: keymaps, `bob capture` edits of existing tasks, Alt+F. Automation never stamps: hooks, `bob projects sync`, `bob randomize`, `bob gkeep pull`, `bob highlights`, `move-done-tasks`, nightly. | yours, sharpened |
| F7 | A human gesture that makes a task Ready (or changes it in any other way) stamps it. **ADJ:** automatic resurfacing does not stamp. A task whose `scheduled` date falls after its stamp and on or before today is **due** (tickler rule), computed at read time. | yours, ADJ |
| F8 | **ADJ.** Creation never stamps, on any path. Every new task is reviewed once. | extends yours |
| F9 | **ADJ.** Scope: open, actionable, non-Today tasks in **any lane** (Ready, Next, Pending). Excluded: Blocked (a dependency or a future `scheduled`), recurring (`repeat::`), tasks in canonical daily notes, `#hide`, `_templates/`, `_conflicts/`, and `never`. | ADJ (yours was Ready only) |
| F10 | Due tasks appear in the freshness review. **ADJ:** two tiers, **new** (no stamp) before **stale** (stamp past its interval, or resurfaced). Within a tier, order by note path, then line. | yours, ADJ |
| F11 | See at a glance how many are due and how many were refreshed today. **ADJ:** an Obsidian status bar item, a Notice after each refresh, dash chips, and a `bob plan` meter. | yours, surfaces ADJ |
| F12 | Keys: next or previous due task, and refresh the current task without other changes. **ADJ:** `]s`/`[s` (vimrc), **Alt+F** (counted, and works on Task Link lines), plus **Alt+Shift+F** (refresh and see less often) and a Ctrl+Shift+P `refresh` row. | yours, extended |
| F13 | **ADJ.** Cutover seeds stamps spread over one interval, grouped by note, after a dry run you approve. | ADJ |
| F14 | A later N-per-day limit applies **only to the stale tier**: most overdue first, with the leftover shown ("+31 waiting"). Try deferral and slow-down first. | yours, constrained |
| F15 | **ADJ.** A headless mirror: a Rust predicate, `bob freshness`, and `bob plan` counts. `docs/freshness.md` owns the definition and the conformance vectors for Rust and JS. | ADJ |
| F16 | Add **Task Freshness** to the glossary web. **ADJ:** also add a decision record, because this sets a policy every writer must follow. | yours + ADJ |

## Design

### The field and where it sits

```markdown
- [ ] #task Fix it [fresh:: 2026-09-30] [created::2026-09-09] [priority:: high] [scheduled:: 2026-09-12] ^fix-it
- [ ] #task Read X [[#^h-8bac|🔖]] [h:: e629…] [fresh:: 2026-09-30] [created::2026-08-28]
- [ ] #task Blog idea [fresh:: 2026-09-30] [refresh:: 4w] [created::2026-09-10]
```

**The placement rule** (one helper per language: `task_fields::stamp_fresh` in Rust, `api.freshness.stampLine` in
ledger-tools):

1. If the line has a `[fresh:: …]` before the trailing suffix, replace its value in place and delete any duplicates.
2. Otherwise, find the **trailing Tasks-parsable suffix** exactly as the parsers do:
   - strip a trailing `^id`;
   - then repeatedly strip a trailing recognized Tasks field (`created`, `start`, `scheduled`, `due`, `completion`,
     `cancelled`, `priority`, `repeat`, `onCompletion`, `id`, `dependsOn`) or a trailing tag.
3. Insert ` [fresh:: D]` at the start of that suffix, or at the end of the line if there is no suffix.
4. If a `[fresh:: …]` sits *inside* the suffix (hand-typed in the wrong place), move it out. It is hiding fields, so
   also report the lint `fresh_misplaced`.
5. `refresh::` uses the same rule and sits right after `fresh`.
6. Stamping with today's date when the stamp is already today is a no-op. This avoids churn and digest changes.

**Why the bracket Dataview form:**

- It is your proposal.
- `clean_description` already strips it from every picker ([row 8](#what-i-verified)).
- Dataview types it as a date, so agents can write `TASK WHERE !completed AND !fresh` in `bob query`.
- The paren form `(fresh:: …)` is not stripped by `clean_description`.
- An `%%fresh%%` comment would be hidden in rendered views, but no query engine can read it.

### Interval and due state (the read-time predicate)

```text
interval(t) = t.refresh ?? note(t).task_refresh ?? config.freshness.interval ?? 7d     # "never" disables
in_scope(t) = status ∈ {Ready " ", Next "*", Pending "/"}
              ∧ ¬dependency-blocked ∧ ¬(scheduled > today) ∧ ¬Today(t) ∧ ¬repeat
              ∧ ¬in canonical daily note ∧ dash-visible (¬#hide, ¬_templates, ¬_conflicts)
              ∧ interval(t) ≠ never
state(t)    = NEW         if no valid fresh                     (malformed ⇒ NEW + lint fresh_invalid)
            | RESURFACED  if fresh < scheduled ≤ today          (tickler)
            | STALE       if today ≥ fresh + interval(t)
            | FRESH       otherwise
due(t)      = in_scope(t) ∧ state(t) ≠ FRESH
fresh_today = open tasks with fresh == today                   ("refreshed today")
```

- **Optional, and a later phase:** RESURFACED can also fire when a `dependsOn` target's completion date falls after
  the stamp. That catches dependency unblocks. It is computable from the Tasks cache, but skip it until you miss it.
- **Today is excluded** because you are handling it right now. Linking stamps anyway, and a hand-typed link is covered
  the next day.
- **In Obsidian**, ledger-tools computes the predicate from the Tasks cache plus `metadataCache` frontmatter.
- **Headless**, Rust computes it directly ([row 10](#what-i-verified)).
- Both sides run the vectors in `docs/freshness.md`:
  - FV1 no stamp → NEW;
  - FV2 the 7-day boundary;
  - FV3 task override;
  - FV4 note override;
  - FV5 config default;
  - FV6 `never`;
  - FV7 recurring excluded;
  - FV8 Blocked excluded;
  - FV9 Today excluded;
  - FV10 resurfaced;
  - FV11 malformed;
  - FV12–FV16 placement cases: no fields, `[h::]` present, trailing `#hide ^prj`, a misplaced `fresh`, duplicates.

### Who stamps

The rule: **a human gesture that writes a task's line or its logs stamps that task, if the task stays open.**

| Surface | Gesture | Stamps |
|---|---|---|
| bob-navigation-hotkeys | Alt+N commit / release | yes, each target |
| | Ctrl+Shift+P: priority, `scheduled` (defer or pull forward), `dependsOn`, delete property, lane row, new `refresh` row | yes |
| | Ctrl+Shift+P cancel | no (the task leaves scope) |
| | Ctrl+Shift+P project-level `scheduled` (bulk) | no. Resurfacing covers the return. |
| | Ctrl+Shift+M move task to note | yes, the moved tasks (routing an inbox item *is* a review) |
| | `!` add or remove a dependency | yes, the parent |
| | **Alt+F / Alt+Shift+F** (new) | yes, and nothing else changes |
| block-id-prompt | Ctrl+Shift+Enter link; `^^` picker link | yes. For a Next or Pending target this adds a write to the task's note, which today only writes the daily note. |
| | Ctrl+Shift+Enter unlink of `[/]` with a Work Log entry | yes (the log is written). A plain unlink doesn't. |
| | Ctrl+6 block-ID rename | no (bookkeeping) |
| task-status-cycler | Alt+] / Alt+[ to an open status; reopening | yes |
| | Ctrl+Enter close | no (leaves scope) |
| | Ctrl+Shift+] promote a bullet to `#task` | no (creation, F8) |
| bob capture (and so Bob Mac Capture) | link toggle (link direction), Ensure Next, `@r:id` / `^r:id` link existing, `=x` in-progress rows, sub-bullet `@r+id#section` | yes |
| | any new task, on any route | no (F8) |
| Automation | hooks, `projects sync`, `randomize`, `gkeep pull`, `highlights`, `move-done-tasks`, nightly | **never** |

**Where the JS stamp logic lives.** Plugins normally copy pure helpers rather than import each other. Here I'd call
the helper through the ledger-tools api instead (`api?.freshness?.stampLine?.(line, today) ?? line`).

- A missing stamp is **safe**: you review the task once more.
- A misplaced stamp is **unsafe**: it hides Tasks fields.
- So centralize the risky part and let the safe failure happen when ledger-tools is old or missing.
- Runtime api calls between plugins already exist: nav and block-id-prompt call `nextBudget` / `pendingBudget`.
- This departs from the copy convention, so record it in the decision record.

**No Bob Mac Capture changes are needed.** bob-cli does the stamping (thin-client rule), and `clean_description`
keeps the field out of the rows.

### The review loop

- **`]s` / `[s`**: nav commands `jump-to-next-due-task` / `jump-to-prev-due-task`, mapped in the vimrc with `exmap`,
  the same way as `[[`/`]]`.
  - Their mnemonic matches Vim's "next/previous misspelling".
  - They read `api.freshness.queue()`: tier, then note path, then line, recomputed on every jump.
  - They open the note and put the cursor on the task line, reusing `focusTaskMoveDestination`.
  - They step from the cursor's position in that order, and wrap with a Notice.
  - Because the Tasks cache lags a few hundred ms after a write, they skip the key just stamped, the same way Alt+N
    adjusts its lane counts.
- **Alt+F**: nav command `refresh-task`. It stamps the task on the cursor line.
  - Target discovery is Alt+N's: a task line plus the next N tasks, or a Task Link plus the next N sibling links.
  - It changes nothing else.
  - Notice: `Fresh · 22 due (3 new) · ✓ 13 today`, or `Already fresh today`.
  - It refuses done and cancelled tasks.
- **Alt+Shift+F**: "refresh, see less often". It stamps the task and sets `[refresh:: …]` to double the effective
  interval (7d → 2w → 4w → 8w, capped).
  - Notice: `Fresh · every 2w`.
  - The Ctrl+Shift+P `refresh` row sets any of 3d / 1w / 2w / 4w / 8w / never.
- **Status bar** (ledger-tools): `⟳ 23 due · 3 new · ✓ 13`.
  - The tooltip gives the tier breakdown.
  - Clicking it runs `]s`.
  - It updates on Tasks `cache-update` and at midnight rollover.
- **Dash**:
  - a `REVIEW` chip (`23 · 3 new`, highlighted while new > 0) and a `FRESH 13` chip;
  - a `### REVIEW Tasks` section above TODAY:
    `filter by function globalThis.app?.plugins?.plugins?.["bob-ledger-tools"]?.api?.freshness?.isDue?.(task) === true`,
    sorted by `api.freshness.rank(task)`.
  - REVIEW is an overlay, not a lane: it doesn't take part in the TODAY / PENDING / NEXT / READY exclusivity.
  - Headless `bob query` sees it as empty, like TODAY. Use `bob freshness` there.
- **Outcomes per task:**

  | Decision | Key |
  |---|---|
  | keep | Alt+F |
  | keep, but less often | Alt+Shift+F |
  | defer | Ctrl+Shift+P priority, which rolls a P-level date |
  | commit | Alt+N |
  | do today | Ctrl+Shift+Enter |
  | route (move to a project) | Ctrl+Shift+M |
  | cancel | Ctrl+Shift+P cancel |
  | edit the text | edit, then Alt+F |

  Every row except "edit the text" stamps on its own, so the loop is: read, one key, `]s`.

**Proposed morning ritual** (it replaces "PENDING → NEXT → READY" in `gtd_daily.md`):

1. `bob gkeep pull` (the existing chore).
2. `]s` until the status bar shows **0 new**, then continue until **0 due**, or until your stale budget runs out.
3. Plan today from PENDING → NEXT and link ≤ 3 themes.

The weekly prune chore can then go: stale lane tasks come up on their own.

### Load and how to keep it small

Daily load ≈ **pool ÷ interval + new tasks + resurfaced tasks**.

- The in-scope pool today is about 250: 176 non-recurring Ready + 26 Next + 52 Pending, before the lanes epic's triage
  to 15 + 10.
- New tasks: up to about 14 a day were created in September; fewer survive to the next morning unstamped.
- Resurfaced tasks: about 6 a day for returns 8–30 days out, but 17 a day over the coming week
  ([row 4](#what-i-verified)).

| In-scope pool | Stale per day at 7d | at 14d |
|---|---|---|
| 250 (today, before lane triage) | 36 | 18 |
| 200 (after lane triage) | 29 | 14 |
| 120 | 17 | 9 |
| 80 | 11 | 6 |

- **Time.** At about 5 s for "still fine" (Alt+F, `]s`) and about 25 s for the roughly 1 in 5 tasks that need an
  action, 30 due tasks take about 5 minutes.
  - That is a fifth of the old 186-task walk, and it never misses a capture.
- **The pool is the knob.** Freshness makes the carrying cost of a Ready task explicit: one glance per interval. In
  order:
  1. **Defer** during review. A P3 or P4 deferral buys 1–12 months without a glance.
  2. **Slow down** stable tasks with Alt+Shift+F, and set `task_refresh: 14d` on large, slow notes such as `sase.md`.
  3. Only then add **`freshness.stale_daily_limit`**: the stale tier only, most overdue first, with the leftover
     visible.

### Where the code lives

| Surface | Change |
|---|---|
| bob-cli | `docs/freshness.md` (definition and vectors, the single source of the rule); `task_fields::stamp_fresh` / `set_refresh` (the first shared inserter in the codebase); a `freshness` predicate module; `config/freshness.rs` (`freshness:` block); `bob freshness` (list and stamp); additive `bob plan` JSON (`freshness: {due, new, stale, resurfaced, fresh_today}`) and a human meter `REVIEW 23 (3 new) · FRESH 13`; stamping in the capture paths listed in [Who stamps](#who-stamps); README and docs |
| bob-ledger-tools | Api v3 adds `freshness`: `isDue(task)`, `state(task)`, `rank(task)`, `queue()`, `counts()`, `stampLine(line, date)`, `setRefresh(line, value)`, `intervalFor(task)`. Also a `freshness:` config read beside `loadPlanCaps`, the status bar item, and a reload trigger at rollover. |
| bob-navigation-hotkeys | `]s`/`[s` commands, Alt+F, Alt+Shift+F, the Ctrl+Shift+P `refresh` row, and stamping in Alt+N, Ctrl+Shift+P, Ctrl+Shift+M and `!`. Also fix `upsertBulletProperty`'s end-append for `refresh`. |
| block-id-prompt, task-status-cycler | Stamping through the ledger api (best effort) in the gestures listed above |
| Vault | The dash REVIEW chip and section; vimrc `exmap` / `nmap ]s`, `[s`; the `gtd_daily.md` chores; optionally, `task_refresh` on inbox notes and a CSS snippet to mute `fresh` |
| Memory | A `glossary` strand and a decision record ([Proposed memory text](#proposed-memory-text)) |
| Bob Mac Capture | none |

**CLI sketch.** Per `cli_rules.md`: options in alphabetical order, a short alias for every long option, and color only
on a TTY.

```text
bob freshness [list] [-a|--all] [-b|--bob-dir DIR] [-f|--format human|json] [-l|--limit N]
bob freshness stamp  [-b|--bob-dir DIR] [-d|--dry-run] [-f|--format human|json] [-n|--note PATH]...
                     [-s|--seed] [-S|--spread DAYS] [-t|--task PATH#BLOCK|PATH:LINE:DIGEST]...
```

`list` prints the queue in review order with its tier and age, plus the counts. `stamp` is for bulk and scripted
stamping. `--seed` stamps only unstamped in-scope tasks, spread as described below.

### Cutover (seeding)

1. **Land after the `bob-cli-2y` rollout,** once the lane triage has shrunk NEXT and PENDING. Seeding before the
   triage would stamp tasks you are about to release.
2. **Dry-run:** `bob freshness stamp --seed --spread 7 --dry-run`.
   - Bin-pack notes into 7 days by task count, splitting a large note like `sase.md` by line order.
   - Stamp each group with `today − 7 + day`.
   - Each morning of week one then brings a few whole projects due, which recreates the rotating per-project review
     you liked.
   - Because each batch is stamped together when you review it, the grouping mostly persists afterwards.
3. **Your call on `gkeep_inbox.md`:** seed it with the rest, or leave its 65 tasks unstamped for one deliberate inbox
   triage (route, defer, cancel).
4. Apply the seed from one machine, then run `bob vault-sync run`.
5. **Trial for two weeks.** Keep the design if, on at least 12 of 14 mornings:
   - **new** reaches 0 during the morning review;
   - the whole ritual takes ≤ 10 minutes (median);
   - the due count is flat or falling.

   If time fails, work through the levers in [Load](#load-and-how-to-keep-it-small) in order.

## Recommended solution

**Adopt task freshness, with the adjustments above.**

1. **Definition first (bob-cli).**
   - Write `docs/freshness.md`: the field, placement, resolution order, scope, the NEW / RESURFACED / STALE / FRESH
     states, and the vectors.
   - Add `task_fields::stamp_fresh`, the predicate, the `freshness:` config block, `bob freshness list|stamp`, and the
     `bob plan` meter.
2. **Review UX (bob-plugins).**
   - Ledger-tools api v3 with the predicate, `stampLine`, queue, counts and status bar.
   - nav `]s`/`[s`, Alt+F, Alt+Shift+F, and the Ctrl+Shift+P `refresh` row.
   - Dash REVIEW chip and section, and the vimrc maps.
   - After this phase the review works end to end. Gestures that don't stamp yet only cause extra reviews.
3. **Cutover.** Seed the stamps (dry-run first) and replace the morning-review chore. Retire the weekly prune chore
   once lane tasks show up on their own.
4. **Stamping everywhere.** Add it to the plugin gestures and bob capture paths in [Who stamps](#who-stamps), with a
   stamping assertion in each gesture's tests. No hooks or automation change except making sure they preserve the
   field.
5. **Memory.** Add the Task Freshness glossary strand and a decision record through `/sase_memory_write`.
6. **Trial for two weeks** with the keep rule above. Then consider:
   - RESURFACED for dependency unblocks;
   - `parent` inheritance of `task_refresh`;
   - a stale-only daily limit.

## Proposed memory text

**Glossary strand `task-freshness`** (aka freshness, fresh, stale task):

> The date a human last confirmed that an open task still needs doing as written. It is stored as `[fresh:: YYYY-MM-DD]`
> on the task line, before its Tasks fields. Human gestures stamp it: keymaps, `bob capture` edits, Alt+F. Automation
> and task creation never do. A task is **due for review** when it has no stamp (**new**), when its `scheduled` date
> has arrived since the stamp (**resurfaced**), or when the stamp is older than its refresh interval (**stale**). The
> interval is the task's `[refresh::]`, else its note's `task_refresh` frontmatter, else `freshness.interval` (7 days).
> Review with `]s`/`[s` and Alt+F. `docs/freshness.md` owns the rules.

**Decision record sketch: "Freshness Is Stamped Only By Human Gestures And Read At Review Time"**

- **Claim:** F1–F10 compressed.
- **Why:**
  - a missing stamp is a durable "unreviewed" state; `created` windows miss late pulls;
  - automation can't truthfully claim attention;
  - a read-time tickler avoids hooks text writes;
  - the placement is dictated by right-to-left field parsers.
- **Rejected:** a `created` window, per-project stamps, rolling `scheduled`, a side-car store, git-derived
  last-touched, automatic back-off (deferred), a cap on new tasks.
- **Cost:** field noise on every line, review load that scales with pool size, two implementations, and a
  stamp-through-api exception to the plugin copy convention.
- **Reopens when:**
  - new tasks can't be cleared daily for a week;
  - the trial's time bound fails after deferral and slow-down;
  - Tasks starts parsing unknown fields differently.

## Open questions for Bryan

1. **Scope.** Include Next and Pending (my recommendation), or Ready only as you wrote it?
2. **Desk captures.** Should routed `bob capture` / Mac captures be stamped at creation? That would save about 5–10
   glances a day but weaken "every task captured yesterday". I recommend not stamping them.
3. **Tickler.** Should resurfaced deferrals be due on the day they return (recommended)? That adds about 6–17 reviews a
   day at current deferral volumes.
4. **Inbox pressure.** Should `gkeep_inbox.md` and `mac_inbox.md` get `task_refresh: 3d`, so that items left unrouted
   come back sooner than project tasks?
5. **Names.** `fresh` / `refresh` / `task_refresh` / `]s` / Alt+F: keep them, or do you prefer `reviewed` / `review_every`?

## Sources

- **SASE beads, plans, research:**
  - `bob-cli-2y` (epic);
  - `plan:202609/retire_now_sticky_lanes.md`;
  - `research:202609/retire_now_sticky_lanes_ledger_today/retire_now_sticky_lanes_ledger_today.md`.
- **Memory:**
  - `decisions:task-lanes-are-sticky`, `decisions:today-is-read-from-the-ledger`, `decisions:task-status-is-derived`,
    `decisions:mac-capture-is-a-thin-client`;
  - glossary: Pomodoro, Schedule Log, Task Link, Work Log;
  - `cli_rules.md`, `obsidian.md`.
- **bob-cli:**
  - `src/native/task_fields.rs`;
  - `src/native/task_status_hooks/parse.rs` (`task_metadata`, `task_description`);
  - `src/native/dataview/tasks/{task.rs,js.rs}`;
  - `src/native/note_tasks.rs` (`clean_description`, `line_digest`);
  - `src/native/capture/plan.rs` (`format_task_line`, `append_*_property`), `src/native/capture/mod.rs` (`INBOX_FILE`);
  - `src/native/gkeep/render.rs`, `src/native/highlights_ref/annotation_tasks.rs`;
  - `src/native/config/{mod.rs,plan.rs}`, `src/native/plan_budget/`;
  - `docs/capture.md` (`p:<N>` windows), `docs/gkeep.md`.
- **bob-plugins** (via `sase repo open bob-plugins`):
  - bob-navigation-hotkeys (`toggleTaskLane`, `planTaskLaneBatch`, `upsertBulletProperty`, `reorderPropertyNames`,
    `registerCountedLaneToggleInputListeners`, `getOpenObsidianTaskJumpLine`, `focusTaskMoveDestination`);
  - block-id-prompt (`openPomodoroTaskLink`, `planTargetTaskUpdate`);
  - task-status-cycler (`setActiveCheckboxStatus`, `addCreatedFieldToObsidianTaskLine`);
  - bob-ledger-tools (`api` v2, `loadPlanCaps`, `rebuildTodayCache`, `planBlockTasks`);
  - bob-project-tasks (`task_count` frontmatter).
- **Obsidian Tasks 8.4.0 bundle:**
  - the `Sr()` Dataview field regex builder (`$`-anchored);
  - the end-of-line parse loop with `hashTagsFromEnd`;
  - `TasksFile.property` / `hasProperty`.
- **Vault (read-only):**
  - `dash.md`, `gtd_daily.md`, `gkeep_inbox.md`, `mac_inbox.md`, `sase.md`, `sase_remote.md`;
  - `.obsidian/hotkeys.json`, `obsidian_vimrc.md`;
  - `bob query` Ready / Next / Pending counts;
  - a scan of `created` and `scheduled` across the vault on 2026-09-30.
