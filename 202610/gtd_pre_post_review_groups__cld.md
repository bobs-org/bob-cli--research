# PRE and POST checklist groups around the `]s` morning walk

> **Research query (paraphrased):** Add two review groups to the `]s` GTD morning walk. **PRE** comes
> before every other group and holds any ready task tagged `#gtd` and `#pre`. Tag every daily-recurring
> task in `~/bob/gtd_daily.md` this way except "Morning review". **POST** comes after every other group
> and holds any ready task tagged `#gtd` and `#post`. Tag "Morning review" this way. Each recurring GTD
> task is closed as the walk reaches it. "Morning review" comes last, so checking it off means the whole
> morning review is done, except ROTTEN tasks that can't be reached that day. Research the best
> implementation, critique the plan, make (and call out) any justified changes to the requirements, and
> end with a recommended solution.

Researcher: `cld`, one of four independent researchers. Date: 2026-10-04 (Sunday, the day before the
2026-10-05 → 10-18 trial starts).

## Bottom line

1. **Build it. The idea is good and the order is right.** The data shows a real failure that PRE and
   POST address directly:
   - Since 09-01 (34 days), the daily chores in `gtd_daily.md` were closed on only **8–12 days**.
   - When they are closed, it happens in batches days late. For example, "Brush teeth" was scheduled
     09-21 and completed 09-25.
   - "Morning review" has not been closed once since it was created on 09-30.
   - The daily-note `^gtd` wrapper was cancelled on 09-30, 10-01, 10-02 and 10-03.

   Putting the checklist inside the one key path you already use each morning (`]s`) is the
   cheapest way to make it happen on the day. The order also fits how the vault works:
   - "Import inbox tasks from Google Keep", "Read Email", and "Review Calendar" all produce captures.
     They must come **before** NEW, and PRE puts them there.
   - Closing "Morning review" last is a natural exit gate.
2. **Treat PRE/POST as *checklist tiers*, not freshness tiers.**
   - Every current tier answers "is this task still right?" and is resolved by a `[fresh::]` stamp.
   - A checklist row answers "did I do it?" and is resolved by **completing** it.
   - Recurring tasks are explicitly out of every tier today, and Alt+F refuses them with
     `recurring · not reviewed`.

   So these rows must carry no freshness state, bucket, chip, keep streak, decay card, or upkeep
   budget effect. The design below keeps all of those exactly as they are.
3. **Put the tiers in the shared evaluator (Rust + JavaScript), not in nav alone.** The accepted
   decision `review-walk-is-tiered` rejected a nav-only walk ("nav renders what the shared queue
   says"). PROJECTS and REFERENCES were added this way too: a schema bump, more `by_tier` keys,
   parity vectors.

   The walk becomes **PRE → NEW → PROJECTS → PENDING → NEXT → RETURNED → REFERENCES → ROTTEN → POST**.
   This needs a new decision record, because it partly supersedes the "recurring tasks are in no
   tier" rule.
4. **The riskiest part is in nav, not in the evaluator.**
   - Walk keys are `path:line` unless a task has a block ID, and these chores have none.
   - The vault's Tasks setting `recurrenceOnNextLine: false` inserts the new occurrence *above* the
     completed line. Every following PRE row then shifts down one line.
   - The Tasks cache also lags.

   Together these can make the walk land one line off right after you close a chore. The
   close-and-advance gesture must be built to survive this (see
   [Close-and-advance](#5-nav-close-and-advance-bob-navigation-hotkeys)).
5. **Requirement changes I recommend** (details in [Requirement adjustments](#requirement-adjustments)):
   - "Ready" should mean *open and actionable today*, not only `[ ]`. Otherwise the 15-minute hooks
     delay hides each morning's chores while they are still `[?]`.
   - Tag matching must be exact. The vault already has `#pressed_juice` and `#prestige_auto_gold`,
     and the existing `#hide` check is a substring match.
   - PRE counts toward "Commitments done". POST is a closing tier.
   - In PRE and POST, Alt+Shift+F means "done → next".
   - The "Morning review" text should shrink, since the walk now encodes the order.
   - Plan the deployment around the trial.
6. **Timing:** `docs/freshness.md` §13 says "Don't change the ritual mid-trial", and the trial starts
   tomorrow. Tag the vault now; the tags do nothing until the code ships. If the code lands
   mid-trial, write down the date. The tiers touch none of the trial's keep-rule quantities. They
   only affect the "minutes to Commitments done" tally column.

## What exists today

Everything here was checked on 2026-10-04 at bob-cli `660c171`, bob-plugins `6f8aca0`, and vault
`08fd35fd`. Installed plugins: nav 2.0.1, ledger-tools 1.27.0, Tasks 8.4.0. The repo is ahead of the
vault at nav 2.2.0 / ledger 1.28.0.

| # | Fact | Evidence |
| --- | --- | --- |
| E1 | `gtd_daily.md` lines 9–15 hold 7 open `[repeat:: every day when done]` chores: weather, teeth, pills, calendar, email, Keep import, stretches. Line 18 is "Morning review" (daily). Line 19 is "Weekly prune" (`[?]`, scheduled Mon 10-05). Lines 16–17 are two **cancelled** recurring leftovers ("Pick today", "Weekly review"). | `~/bob/gtd_daily.md` |
| E2 | Since 09-01 the chores were closed on: weather, teeth, and pills 12 days each; calendar and email 10; Keep import 8. Six chores are still `scheduled:: 2026-09-29`. Morning review is still `scheduled:: 2026-09-30`. Completions come in late batches (teeth: scheduled 09-21, done 09-25; scheduled 09-14, done 09-20). | `done/gtd_daily_done.md` tally |
| E3 | The daily-note wrapper `- [*] #task [[gtd_daily]] ^gtd` (from `_templates/daily.md`) was cancelled on 09-30, 10-01, 10-02 and 10-03; today's is `[/]`. Earlier research found it cancelled 21 days in a row before that. | `2026/2026093*.md`, `2026/202610*.md`; `research:202610/gtd_morning_review_pomodoro_cutover/…` Finding 7 |
| E4 | The walk order is NEW → PROJECTS → PENDING → NEXT → RETURNED → REFERENCES → ROTTEN. Both `in_scope` and `walk_scope` require `¬recurring ∧ ¬canonical daily note ∧ ¬Today(t)`. | `docs/freshness.md` §4; `freshnessEvaluate` in ledger-tools; `Tier` in `src/native/freshness/state.rs` |
| E5 | Alt+F / Alt+Shift+F refuse recurring lines (`recurring · not reviewed`). `stampLine` refuses them too. The nav cancel planner refuses recurring tasks ("Recurring tasks are cancelled with Obsidian Tasks so the next occurrence is handled"). | nav `classifyFreshStampTarget`, cancel planner; ledger `freshnessStampLine` |
| E6 | A queue key is `path#blockId` when the task has a block ID, otherwise `path:line`. The walk anchor stores handled keys plus the ordered `afterKeys` / `beforeKeys`. | ledger `freshnessRowKey`; nav `reviewQueueEntryKey`, `buildReviewAnchor`, `planReviewJump` |
| E7 | Tasks has `recurrenceOnNextLine: false`: completing a recurring task inserts the next occurrence **above** the completed line. Task-status-cycler's Ctrl+Enter goes through the Tasks command, and its own comments note that "a recurrence insert … changes the line count". | `.obsidian/plugins/obsidian-tasks-plugin/data.json`; task-status-cycler `toggleActiveCheckboxOpenDoneAndPropagate` |
| E8 | Once you complete a chore, its next occurrence is `[ ]` with tomorrow's `scheduled` date. The hooks make it `[?]`, then flip it back to `[ ]` on the morning it is due. Today "Do morning stretches!" stayed `[?]` until the 05:30 sync; the daily note was created at 05:16. | vault commit `f313f71a` diff |
| E9 | The lane-visibility predicate (`planLaneVisible`) checks done, Tasks dependency-blocking, `#hide` (as a **substring**: `tag.includes("#hide")`), template/conflict paths, and `scheduled > today`. It does **not** check the checkbox symbol. | ledger-tools `planLaneVisible` |
| E10 | Tags: `#gtd` appears 8,620 times (mostly zorg-era daily notes). **No** open `#task` line carries it today. The same chores were once tagged `#task #gtd #context/home …` (05-28 done file). `#pre` and `#post` appear nowhere. Near-matches exist: `#pressed_juice` (9), `#prestige_auto_gold` (2). | vault grep |
| E11 | Rust `RichTask` already carries `tags`, and JS rows come from Tasks objects that also carry `tags`. Neither side needs a new parser. | `src/native/dataview/tasks/mod.rs`; ledger `planTaskTags` |
| E12 | The live walk today: **128 = 4 NEW + 36 NEXT + 1 RETURNED + 10 REFERENCES + 77 ROTTEN**. `rotten_daily_budget` is off. `]S` / `[S` jump to the last / first queue entry. | `bob freshness list`; `obsidian_vimrc.md` lines 37–40; `~/.config/bob/config.yml` |
| E13 | Cost of the last tier addition (REFERENCES): bob-cli `54712fe`, 17 files, +860/−767; bob-plugins `79d5975`, +408/−502, plus later fixes. | `git show --stat` |
| E14 | §13: the trial runs 2026-10-05 → 10-18. "Don't change the ritual mid-trial." The tally records NEW, RETURNED, ROTTEN, confirmed FRESH, READY, lanes kept/released, **minutes to Commitments done**, and chip red. | `docs/freshness.md` §13 |

## How the request was read

| You wrote | Read as |
| --- | --- |
| "any ready task that has the `#gtd` and `#pre` tags" | Membership comes from the tags alone, wherever the task lives and whatever its cadence. "Ready" turned out to need widening (ADJ-1). |
| "all of the tasks … that recur daily except for the Morning review" | Tag the 7 open daily chores. Leave the 2 cancelled leftovers and the weekly "Weekly prune" untagged (but see ADJ-8). |
| "PRE … before any other review group; POST … after any other review group" | PRE is the first tier, ahead of NEW. POST is the last, after ROTTEN. |
| "close out each of these recurring GTD tasks as we get to them" | The resolution is **completion**, not a freshness stamp. |
| "unless there are some ROTTEN tasks I can't get to that day" | ROTTEN can be cut short; POST must stay reachable without clearing it. |

## Critique: is this a good idea?

### What's right about it

- **It fixes a measured failure (E2, E3).** The chores fail because nothing shows them at the right
  moment, so they get batch-checked days later. Earlier research flagged the same noise (Finding 7,
  "checked off in batches days later, which adds recurrence noise and no signal"). Inside `]s`, they
  show up at the start of the session you already run.
- **The order is functionally right, not just tidy.** Three PRE items produce inbox items: Keep import
  creates NEW tasks, and email and calendar spawn captures and @EVENT notes. NEW should only be walked
  after they run. Today the morning review text has to say "`bob gkeep pull`, then ]s" to get this.
  PRE makes it structural.
- **"Close Morning review last" gives the review the finish line it lacks.** Earlier research called
  for an exit gate. POST makes the gate a concrete task that you close when you leave the walk.
- **Tags are the right identity for this.** `#hide` set the precedent. The `#now` decision record
  showed that tags are parser-safe anywhere on a task line, while inline fields can corrupt trailing
  Tasks fields. Unlike `^prj` / `^ref` block IDs, tags can be shared by many tasks in one note.
- **It generalizes for free.** Because membership is tag-based, a weekly chore (Weekly prune on
  Monday) or a one-off task can join PRE or POST with one tag. No code change and no cadence rule are
  needed.

### Concerns

1. **It mixes two kinds of work in one queue.** Today the walk is a *review*: Alt+Shift+F means "still
   right, next". PRE/POST rows are *actions*: the honest outcome is "done". If the two get blurred, the
   freshness contract degrades: a recurring task could end up stamped, counted as upkeep, or turned
   into a ROTTEN decision card. The design must fence checklist rows off from every freshness quantity
   (ADJ-5).
2. **It reverses an accepted invariant.** `review-walk-is-tiered` says recurring, daily-note, and
   Today-linked tasks "are in no tier". PRE/POST deliberately include tagged recurring rows. That
   needs its own decision record, not a quiet exception.
3. **Line shifts and cache lag (E6, E7).** This is the main engineering risk; see
   [Close-and-advance](#5-nav-close-and-advance-bob-navigation-hotkeys).
4. **POST after 77 ROTTEN rows (E12).** With the budget off, you can't reach POST with `]s` without
   walking all of ROTTEN. `]S` already jumps to the last entry, so POST is always one key away. But the
   walk should *tell* you to press it.
5. **Habits now share the walk.** Earlier research recommended taking teeth, pills, weather, and
   stretches out of `#task` altogether. You are fixing the same symptom (late batch completion) the
   other way, by making them impossible to miss. That's a legitimate choice. Its cost is about 7
   completions every morning before NEW. Merging the trivial body habits into one line would cut
   that.
6. **There are still two GTD clocks (E3).** The daily-note `^gtd` wrapper stays as the GTD
   Pomodoro's link target. POST "Morning review" becomes the real "review done" signal. Don't couple
   them in code. Do decide what the wrapper means (see [Open questions](#open-questions-for-bryan)).
7. **Trial interference (E14).** This changes the ritual one day before a trial whose rules say not
   to.
8. **Cost (E13).** Expect roughly the size of the REFERENCES change, plus a new nav gesture: an epic
   with about 4 phases across both repos.

**Verdict:** a good idea, built as checklist tiers with the adjustments below. I would not take a
fundamentally different approach. The alternatives are each cheaper in one dimension and worse
overall (next section).

## Approaches considered

| Approach | Verdict | Why |
| --- | --- | --- |
| **A. Checklist tiers in the shared evaluator, identity by tags** (recommended) | **Adopt** | Fits the shared-queue contract and the decision records. Works in `bob freshness list` and on mobile (no config needed). Follows the PROJECTS/REFERENCES precedent. |
| B. Nav-only frame: nav queries tagged tasks itself and wraps them around `api.freshness.queue()` | Reject | Cheapest, but the decision record explicitly rejects a nav-only walk. The CLI and footer counts would drift from what `]s` does. |
| C. Drop the recurring exclusion and let these tasks into ordinary tiers | Reject | Recurring tasks can't be stamped (E5), so they would sit in NEW forever, and Alt+Shift+F could never advance past them. |
| D. Identity by note residence (frontmatter such as `walk: pre` on `gtd_daily.md`) | Reject | Ties membership to one file, and "Morning review" still needs a per-task exception. Tags are explicit and portable. |
| E. Identity by block IDs, like `^prj` / `^ref` | Reject | A block ID must be unique within a note, so seven chores can't share one. Tasks' recurrence handling of block IDs adds risk. |
| F. An inline field (`[walk:: pre]`) | Reject | Trailing-field parse risk, documented in the `#now` decision (a field erased `priority` / `created`). |
| G. Nested tags `#gtd/pre` / `#gtd/post` | Viable, not adopted | One token, so a task can't end up with only half the pair, and it groups under `#gtd` in the tag pane. I kept your two-tag form because these chores were historically tagged `#gtd` (E10), Dataview `contains(tags, "#gtd")` only matches the exact tag, and exact matching plus a lint removes the two-tag form's risks. Either works if the rule is written down. |
| H. Put the checklist in the daily-note template as plain checkboxes (not `#task`) | Reject | No recurrence noise and a per-day record. But `]s` can't reach it without a new non-Tasks source, weekly cadences are impossible, and template edits don't reach notes already created. |
| I. Place POST *between* the commitment tiers and ROTTEN | Considered, not adopted | It matches §6 (ROTTEN upkeep "then, or later") and lands exactly on the "Commitments done" boundary. But you said ROTTEN is part of the review the close certifies. The `]S` hint (ADJ-4) handles the reachability problem without reordering. |
| J. Configurable tag lists (`freshness.pre_tags`, `post_tags`) | Reject for now | Adds Rust/JS parity work, and mobile falls back to defaults when the config file can't be read. Hard-coded tags, like `#hide`, are enough. |

## Requirement adjustments

Each change to what you asked for, called out explicitly:

| # | You asked for | Recommended instead | Why |
| --- | --- | --- | --- |
| **ADJ-1** | PRE/POST hold **ready** tasks | Hold any **open, actionable-today** tagged task: status `[ ]`, `[*]`, `[/]`, or `[?]`, provided there is no open dependency, no `scheduled` date after today, no `#hide`, and no template/conflict path. For these rows only, **ignore** the recurring, canonical-daily-note, and Today exclusions. | The hooks re-derive `[?]` → `[ ]` only every 15 minutes, on the Mac (E8). A strict `[ ]` rule would hide each morning's chores until that sync. Linking a chore under the GTD Pomodoro (Today) shouldn't hide it either: a checklist row is due until it is closed. |
| **ADJ-2** | Tag tasks that "recur daily" | Membership is **tags only**. Daily recurrence is a rule for tagging the vault, not a code predicate. | Weekly chores, one-offs, and tasks in other notes then work with no code change. |
| **ADJ-3** | "has the `#gtd` and `#pre` tags" | Match **exact, whole, case-insensitive tags**, never substrings. `#gtd` + `#pre` + `#post` → PRE, with lint `checklist_tag_conflict`. `#pre` or `#post` without `#gtd` → not a member, with lint `checklist_tag_incomplete`. Optional lint: a recurring member whose rule lacks `when done`. | `#pressed_juice` and `#prestige_auto_gold` exist, and the `#hide` check it would be modeled on is a substring match (E9, E10). Without `when done`, a missed day queues a backlog of past occurrences. |
| **ADJ-4** | PRE first, POST last | Keep that order: **PRE → NEW → … → ROTTEN → POST**. PRE is a **commitment** tier, so "Commitments done" requires it. POST is a **closing** tier, neither commitment nor upkeep. When POST is non-empty, the ROTTEN boundary notice reads `Commitments done — 77 ROTTEN left · ]S closes the review`. | It keeps your semantics ("Morning review includes everything before it") and keeps POST one key away despite an unbounded ROTTEN tier. |
| **ADJ-5** | "close out each … as we get to them" | On a PRE/POST row, **Alt+Shift+F = complete → next** and **Alt+F = complete in place**. Both complete through the same Tasks path Ctrl+Enter uses, so recurrence, `completion::`, and close finalization all run. `]s` skips. To skip a chore for today, cancel it through Tasks or reschedule it to tomorrow. Checklist rows **never** stamp `fresh`, never count or reset `keeps`, never open a decay card, never count toward `upkeep_today` or the budget, and never feed `state` counts, buckets, or chips. Counted and Task Link Alt+F batches skip them. | One key carries you through the whole walk, and the freshness contract is untouched. Today those keys only show `recurring · not reviewed` on these rows, so nothing useful is lost. |
| **ADJ-6** | (implicit) | Checklist rows get a queue key that stays the same when lines move: path + normalized description (+ an occurrence index for duplicates), not `path:line`. The close-and-advance gesture adjusts its precomputed target for inserted lines. | Covers E6 and E7 (see [§5 below](#5-nav-close-and-advance-bob-navigation-hotkeys)). |
| **ADJ-7** | Tag "Morning review" `#post` | Also **rewrite its text**. The walk now encodes the order, `bob gkeep pull` is now a PRE chore, and the current text lists a stale order (no PROJECTS / REFERENCES). | The POST line should read as the exit gate, not a manual. |
| **ADJ-8** | (not asked) | Optional: tag **Weekly prune** `#gtd #post`, so on Mondays POST is Morning review, then Weekly prune (file order). Leave the two cancelled `[-]` leftovers untagged and consider deleting them. | It's the same "close when the walk ends" pattern, at a weekly cadence. |
| **ADJ-9** | (not asked) | Optional: move "Import inbox tasks from Google Keep" to the **last** PRE line. | It hands off straight into NEW, and email or calendar may add Keep captures first. |
| **ADJ-10** | (not asked) | Optional: merge "Brush teeth", the pills line, and "Do morning stretches!" into one body-routine chore. Time-box "Read Email" ("≤5 min: 2-minute replies, else capture"). | Fewer completions before NEW, and email can't swallow the review. |

## Recommended solution

### 1. Vault (now; inert until the code ships)

Put the tags right after `#task`, matching the historical `#task #gtd …` lines. Proposed `gtd_daily.md`
(fields unchanged and abbreviated as `…`):

```markdown
- [ ] #task #gtd #pre Check weather  [repeat:: every day when done] …
- [ ] #task #gtd #pre Brush teeth  [repeat:: every day when done] …
- [ ] #task #gtd #pre Take fish oil pills + Take L-tyrosine pills  [repeat:: every day when done] …
- [ ] #task #gtd #pre Review Calendar for today and tomorrow + Create @EVENT notes  [repeat:: every day when done] …
- [ ] #task #gtd #pre Read Email  [repeat:: every day when done] …
- [ ] #task #gtd #pre Do morning stretches! [created::2026-07-06] [scheduled:: 2026-10-04]  [repeat:: every day when done]
- [ ] #task #gtd #pre Import inbox tasks from Google Keep  [repeat:: every day when done] …   ← moved last (ADJ-9, optional)
- [ ] #task #gtd #post Morning review: [S/]s through PRE and the commitment tiers to Commitments done; clear [[crowded|CROWDED]]; [[rotten|ROTTEN]] upkeep until 0, budget, or you stop; ]S, close this, start the highlight (≤3 themes)  [repeat:: every day when done] …
- [?] #task #gtd #post Weekly prune: …   ← optional (ADJ-8)
```

Tasks copies the description, tags included, into each new occurrence, so this is a one-time edit.
Today it would yield **PRE 7, POST 1**. It is safe to land before the code because nothing reads
`#pre`, `#post`, or open `#gtd` tasks yet (E10).

### 2. Contract (`docs/freshness.md` §4, §6, §7)

Extend §4 with a checklist predicate that **wins before** every existing tier:

```text
checklist(t)       = pre   if tags ∋ #gtd ∧ tags ∋ #pre      (exact, case-insensitive)
                   | post  if tags ∋ #gtd ∧ tags ∋ #post ∧ tags ∌ #pre
                   | none  otherwise
checklist_scope(t) = checklist(t) ≠ none ∧ status type ∉ {DONE, CANCELLED, NON_TASK}
                     ∧ ¬dependency-blocked ∧ ¬(scheduled(t) > today) ∧ ¬#hide
                     ∧ ¬under _templates/_conflicts
                     (recurring, canonical daily note, and Today are NOT exclusions here)
tier(t)            = pre  if checklist(t) = pre  ∧ checklist_scope(t)
                   | post if checklist(t) = post ∧ checklist_scope(t)
                   | …existing rules unchanged (projects | references | new | pending | next | returned | rotten | none)
```

- **Order:** `pre` 0, then the existing seven tiers, then `post` 8. Inside PRE and POST, sort by
  `path ↑, line ↑`. You set the checklist order by line position.
- **Due:** always due while in scope. There is no stamp, interval, or `due_on`; `due_on` and
  `days_overdue` are null.
- **State/bucket:** evaluated exactly as today. A recurring member stays out of freshness scope, so
  its `state` and `bucket` stay null. A non-recurring member keeps its Ready `state` and `bucket`,
  and only its tier changes, which is the REFERENCES precedent. The partition
  `B = NEW ∪ RETURNED ∪ ROTTEN ∪ READY` and the dash chips don't change.
- **Counts:**
  - `by_tier` grows to nine keys, and `walk = sum(by_tier)` still holds.
  - New fields `pre_due` and `post_due`.
  - `due`, `new`, `resurfaced`, `rotten`, `fresh`, `refreshed_today`, `upkeep_today`, and
    `budget_met` are unchanged.
- **Commitment set:** add `pre`. POST is listed in neither the commitment set nor upkeep.
- **Schema:**
  - freshness JSON schema 9.
  - ledger-tools freshness namespace v7, with an explicit `checklistTiers` capability. Nav enables
    the checklist gestures only when it sees that capability, like the `referenceReview` gate.
- **§6 ritual:** PRE is walked first ("do it, Alt+Shift+F"). POST closes the walk via `]S`.

### 3. Rust (`src/native/freshness/`)

- `FreshnessRow` gains `checklist: Option<ChecklistKind>`, built in `scan.rs` from `RichTask.tags`
  with exact matching.
- Candidates come from the open-task universe (`snapshot.open`). Recurring rows are included for
  checklist members only.
- `evaluate` assigns `Tier::Pre` / `Tier::Post` before the tracker and lane rules. `queue` gets the
  new ordering and comparator.
- Lints: `checklist_tag_conflict`, `checklist_tag_incomplete`, and optionally
  `checklist_repeat_not_when_done`.
- Human output gets `PRE n` / `POST n` sections and header counts (`- 7 pre - … - 1 post`).

### 4. JavaScript (bob-ledger-tools)

Mirror the Rust changes:

- `freshnessRowFromTask` adds `checklist` from `planTaskTags` (exact match).
- `freshnessEvaluate` assigns the tier.
- `FRESHNESS_TIER_ORDER` gains `pre: 0 … post: 8`.
- `freshnessQueue` admits checklist rows even when `lane` is null, which covers the `[?]` hooks-lag
  rows. Today it skips lane-null entries.
- Update the footer and status tiers, the commitment set, and the status-bar mode (PRE > 0 counts as
  "due").
- The checklist row key from ADJ-6.
- Shared parity vectors (below).

### 5. Nav close-and-advance (bob-navigation-hotkeys)

**Close-and-advance (Alt+Shift+F on a PRE/POST row):**

1. Read the queue and the walk anchor. Compute the **target** (the next live entry after the current
   one) *before* writing anything.
2. Record the editor's line count, then complete the row through task-status-cycler's open/done path,
   or the Tasks done command. This triggers the Tasks recurrence and close finalization. Don't write
   `[x]` by hand, which would skip the next occurrence.
3. `delta = lineCount_after − lineCount_before` (usually +1).
4. If the target is in the same file below the completed line, shift its line by `delta`. Verify the
   target's text before landing; if it doesn't match, fall back to the stable key from ADJ-6.
5. Add the completed row's key to the anchor's handled keys. The Tasks cache lags, so the stale queue
   may still list the row.
6. Land and show the notice. The completed row's new occurrence is scheduled for tomorrow, so it is
   out of scope and won't reappear.

Because checklist keys are text-stable, a manual Ctrl+Enter followed by `]s` also resolves
correctly. Today `path:line` keys only land right by coincidence, because the shift is exactly +1.

**Notices:**

| Moment | Notice |
| --- | --- |
| Landing on PRE | `PRE 2/7 · Brush teeth · Alt+Shift+F done → next · ]s skip` |
| Stepping into ROTTEN with nothing left due | `Commitments done — 77 ROTTEN left · ]S closes the review` (the `]S` clause appears only when POST is non-empty) |
| Stepping into ROTTEN with PRE or commitments left | `ROTTEN next — 2 commitments still due` (existing wording; the count includes PRE) |
| Landing on POST | `POST 1/1 · Morning review · 0 commitments · 77 ROTTEN left` |
| Closing POST with commitments left | Close anyway and report `closed with 2 commitments still due`. No refusal, in line with the "nothing refuses" decisions. |
| Alt+F batches over checklist rows | Skip them with a count, as decision-due rows are skipped today. |

### 6. Decision record and docs

Write a new decisions-web record through `/sase_memory_write`, for example `walk-is-framed-by-checklists`,
"PRE And POST Checklists Frame The Review Walk". It should carry:

- the claim: the tag identity, the open-and-actionable scope, completion as the only resolution, and
  no freshness side effects;
- the rejected alternatives from the table above;
- the cost: one more tier pair kept in sync across both evaluators, and the nav line-shift handling;
- the reopen condition: say, if PRE rows are skipped with `]s` on more than half of mornings,
  checklist-in-walk isn't working and habits should leave `#task` as the earlier research suggested.

The new record partly supersedes `review-walk-is-tiered` (the tier list, and "recurring … in no
tier" for tagged rows only).

Docs to update:

- `docs/freshness.md` §§4, 6, 7, and 13 (the rollout note);
- the nav README keymap notes;
- the glossary `freshness` strand, which spells out the tier order.

### 7. Tests (parity vectors, both languages)

| Vector | Case |
| --- | --- |
| C1 | `#gtd #pre` recurring `[ ]`, scheduled in the past → `pre`, state null |
| C2 | Same row as `[?]` with an arrived schedule and no dependencies → `pre` (the hooks-lag case) |
| C3 | Dependency-blocked, future-scheduled, `#hide`, or under `_templates` → none |
| C4 | Today-linked or in a canonical daily note → still `pre` |
| C5 | `#pre` without `#gtd`; or `#pressed_juice` with `#gtd` → none (C5 also lints `checklist_tag_incomplete`) |
| C6 | Both `#pre` and `#post` → `pre`, plus the conflict lint |
| C7 | Non-recurring `#gtd #post` that is NEW → tier `post`, state `new`, bucket `new` |
| C8 | Nine-tier order with stable ties; `walk = sum(by_tier)`; `due` unchanged |
| C9 | Stamping a checklist row is refused; keeps unchanged; `upkeep_today` unchanged |

Nav also needs one test for close-and-advance over 7 PRE rows in one file, with
`recurrenceOnNextLine` both false and true, landing on PRE 2 from a stale and from a refreshed cache.

### 8. Rollout and the trial

1. **Today:** apply the vault edits from step 1. They are inert.
2. **Build:** one epic with phases contract+Rust, ledger-tools, nav, then rollout. Phase 1 writes the
   decision record.
3. **Deploy:** if it can't land before Monday's review, it's your call:
   - **Strict:** hold the deploy until 10-19.
   - **Pragmatic (my lean):** deploy when ready and record the date in §13 and the tally. The tiers
     don't touch the trial's measured quantities (buckets, chips, confirmations, lanes). The only
     column they move is "minutes to Commitments done", so note "incl. PRE" from that date.

   Either way, don't tune intervals or the budget in the same week, so the effects stay separable.

## Open questions for Bryan

1. **What does the `^gtd` daily-note wrapper mean now?** Suggestion: it stays the GTD Pomodoro's
   time-logging anchor only, and POST "Morning review" is the "review done" signal. Stop cancelling the
   wrapper by hand, or retire it in a later change.
2. **Two-tag `#gtd #pre` or nested `#gtd/pre`?** Either works with exact matching. This report assumes
   your two-tag form.
3. **Weekly prune in POST on Mondays (ADJ-8), and Keep import last in PRE (ADJ-9)?**
4. **Strict or pragmatic deploy relative to the trial?**
5. **Should ROTTEN have a daily budget during the trial?** With POST last, a budget (for example 15)
   would give `]S` a natural trigger. But §13 names the budget as the trial's tuning lever, so I
   haven't recommended changing it.

## About this report

- Sources read:
  - code: bob-cli `660c171` (`docs/freshness.md`, `src/native/freshness/{state,scan}.rs`,
    `src/native/dataview/tasks/mod.rs`, `docs/task-status-hooks.md`); bob-plugins `6f8aca0`
    (ledger-tools `freshnessEvaluate`, `freshnessQueue`, `freshnessRowFromTask`, `planLaneVisible`;
    nav `planReviewJump`, `buildReviewBoundaryNotice`, `classifyFreshStampTarget`, cancel planner;
    task-status-cycler toggle paths);
  - vault `08fd35fd` (`gtd_daily.md` and its git history, `done/gtd_daily_done.md`, daily notes
    09-30 → 10-04, `_templates/daily.md`, `obsidian_vimrc.md`, Tasks `data.json`);
  - `~/.config/bob/config.yml`; live `bob freshness list`;
  - decision records `review-walk-is-tiered`, `ready-is-freshness-gated`, `task-lanes-are-sticky`,
    `today-is-read-from-the-ledger`, `rotten-keeps-use-priority-decay`, `now-tag-is-user-owned`,
    `note-ready-cap-counts-the-lane`;
  - prior research `research:202610/tiered_morning_review_walk/…` and
    `research:202610/gtd_morning_review_pomodoro_cutover/…`.
- Not verified:
  - Obsidian UI behavior (headless session);
  - whether Tasks 8.4.0 creates the next occurrence when a recurring task is *cancelled*. Nav's
    refusal message says it does; confirm before documenting "cancel = skip today".
- Nothing in the vault or either repo was modified by this research.
