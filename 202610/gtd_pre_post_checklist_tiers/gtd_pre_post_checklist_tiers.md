# PRE and POST checklist tiers around the `]s` morning walk

> **Research query:** What is the best way to add two review groups to the GTD morning review
> that `]s` triggers in Obsidian: PRE, reviewed before every other group and holding ready tasks
> tagged `#gtd` and `#pre` (every daily-recurring task in `~/bob/gtd_daily.md` except "Morning
> review"), and POST, reviewed after every other group and holding ready tasks tagged `#gtd` and
> `#post` ("Morning review"), so each recurring GTD task is closed as the walk reaches it and
> checking "Morning review" last certifies the whole review? Is this plan a good idea, would a
> different approach be better, and what requirement adjustments and recommended solution are
> justified?

![Infographic of the recommended morning walk: PRE checklist chores tagged #gtd #pre, then the NEW, PROJECTS, PENDING, NEXT, RETURNED, and REFERENCES commitments, then optional ROTTEN upkeep with a one-key jump to POST, and finally the POST Morning review closeout tagged #gtd #post, with which tasks qualify, the keys on PRE and POST rows, and the rollout](gtd_pre_post_checklist_tiers_infographic.png)

## Bottom line

1. **Build it. The idea is good.** It fixes a measured failure: since 09-01 the
   `gtd_daily.md` chores were closed on only 8–12 of 34 days, in late batches. "Morning
   review" has never been closed since it was created on 09-30. Six chores are still
   `scheduled:: 2026-09-29` (cld). Nothing in `]s` lands on them today. The order is also
   functionally right, not just tidy. Keep import, email, and calendar produce captures, so
   they must run before NEW, and PRE puts them there.
2. **Build PRE and POST as *[checklist tiers](#contract)* in the shared evaluator (Rust +
   JS).** They are resolved by **completing** the task, never by a freshness stamp. Fence them
   off from every freshness quantity: state, bucket, chips, keeps, decay cards, upkeep, and the
   budget. All four reports agree on this.
3. **Keep POST last, after ROTTEN, as you asked.** The reports
   [split 2–2 on this](#disagreements-and-how-i-resolved-them). The deciding evidence is the
   Morning review task's own text: it already lists *"then ROTTEN upkeep until 0 or budget,
   fine to stop partway"* as part of the review it certifies. `]S` (jump to last) already lands
   on POST in one key, so the walk only has to advertise it.
4. **Seven requirement adjustments, plus optional ones** ([R1–R8](#requirement-adjustments)). The
   most important:
   - Widen "ready" to *open and actionable today*. The 15-minute hooks leave each morning's
     chores `[?]` until they run.
   - Make Alt+Shift+F complete-and-advance on PRE/POST rows.
   - Match tags exactly.
   - Rewrite the Morning review text.
5. **The real engineering risk is nav identity after a recurrence insert.** It does not need a
   new key scheme (one report's proposal). The fix is a small *text-first cursor match* in
   `planReviewJump` ([F9](#what-exists-today)). None of the four reports found this gap.
6. **Timing.** `docs/freshness.md` §13 says "Don't change the ritual mid-trial", and the code
   won't land before Monday anyway. Tag the vault now; the tags are inert until the code ships.
   [Ship the code when it's ready and log the date](#rollout-and-the-trial) (my lean), or hold
   it until 10-19.

## What exists today

Load-bearing facts, re-checked today (verified). Facts marked *(new)* were not in any
researcher's report.

| # | Fact | Evidence |
| --- | --- | --- |
| F1 | **Walk order and the commitment boundary.** The order is NEW → PROJECTS → PENDING → NEXT → RETURNED → REFERENCES → ROTTEN. The first six are commitments; ROTTEN is upkeep. "Commitments done — N ROTTEN left" fires only on a forward step from a commitment tier into ROTTEN. | `reviewIsCommitmentTier`, `buildReviewBoundaryNotice` (nav); `FRESHNESS_FOOTER_COMMITMENT_TIERS` (ledger `src/120-freshness-footer.js`) |
| F2 | **Recurring tasks never enter the walk today.** `walk_scope` requires `lane ∧ lane_visible ∧ ¬recurring ∧ ¬daily note ∧ ¬Today`. Walk rows come only from the READY / PENDING / NEXT snapshots, so `[?]` rows exist only in the OPEN (seed) snapshot. Stamps refuse recurring lines; nav shows `recurring · not reviewed`. | `src/native/freshness/state.rs:308`, `scan.rs:159–168`; nav notice text |
| F3 | **`gtd_daily.md` contents.** It has 7 open daily chores: weather, teeth, pills, calendar, email, Keep import, and stretches. All are `#task` only and `[repeat:: every day when done]`; six are scheduled 09-29 and stretches 10-04. "Morning review" is daily, scheduled 09-30. "Weekly prune" is `[?]`, weekly, scheduled 10-05. "Pick today" and "Weekly review" are cancelled leftovers. No line has a block ID. | `bob query --format markdown --tasks 'path includes gtd_daily.md'` |
| F4 | **The Morning review text** reads: "`bob gkeep pull`, then ]s / Alt+Shift+F through NEW → PENDING → NEXT → RETURNED until Commitments done …; start highlight; clear CROWDED to 0 …; **then ROTTEN upkeep until 0 or budget, fine to stop partway**; ≤3 themes, highlight first". The tier list is stale (it lacks PROJECTS and REFERENCES), and it duplicates the Keep-import chore. | same query |
| F5 | **Live walk and installed binary.** The live walk is 128 = 4 NEW + 36 NEXT + 1 RETURNED + 10 REFERENCES + 77 ROTTEN, with `rotten_daily_budget` null. The installed `bob` emits schema 7 (source: 8) and still reports a decay `active_from` of 2026-10-19 that the source dropped, so the installed binary lags the tree. | `bob freshness list -f json`; `cli.rs:54` |
| F6 | **The hooks leave chores `[?]` overnight.** `bob task-status-hooks` runs only from the Mac's cron, every 15 min at :10/:25/:40/:55. It turns any `[ ]`, `[*]`, or `[/]` with a future `scheduled` date into `[?]`, and restores it on the first run after the date arrives. A completed chore's next occurrence therefore sits as `[?]` until the first cron run after the Mac wakes. cld observed "Do morning stretches!" still `[?]` at 05:30, after the daily note was created at 05:16. | `docs/task-status-hooks.md` (transition table); `docs/vault-git-sync.md` "Mac scheduled maintenance" |
| F7 | **Ctrl+Enter can't close a `[?]` task** *(new)*. The cycler's open/done toggle accepts only ` `, `*`, `/`, `x` (`OPEN_DONE_TASK_SYMBOLS`) and does nothing on `[?]`. Its write goes through the Tasks command `obsidian-tasks-plugin:set-status-symbol-to-x`, which fires recurrence, then runs `finalizeClosedTasks`. The cycler's cross-plugin API is `{ version: 1, recoverBlockedDependents }`, with no completion entry. | task-status-cycler `src/010-core.js`, `030-task-toggles.js`, `180-plugin-editor-edits.js`, `110-plugin-lifecycle.js` |
| F8 | **Completing a chore shifts every later line by one.** Tasks has `recurrenceOnNextLine: false`, so the new occurrence is inserted *above* the completed line. Done lines are archived only by the batch `bob move-done-tasks`, so the +1 shift persists all morning. | cld (Tasks `data.json`); README migration notes |
| F9 | **Line-number cursor match can skip a chore** *(new)*. Queue keys are `path:line`. `resolveReviewQueueLine` already relocates a *landing* to a unique exact-text match when the line moved, so cld's new key scheme isn't needed for landings. But `planReviewJump` identifies the *cursor's* entry by line number first and uses text only as a fallback. Under a stale Tasks cache right after an insert, the cursor on "Brush teeth" (now line 11) matches the stale entry for "Pills" (line 11), so `]s` skips Pills. | nav `planReviewJump` (cursor block), `resolveReviewQueueLine` |
| F10 | `]S` / `[S` call `planReviewJump` with `endpoint: "last"` / `"first"`: the last or first queue entry, ignoring the anchor. | nav `planReviewJump` |
| F11 | **Tags are inert today.** `#pre` and `#post` are unused, and no open task carries `#gtd`. The plan-cap GTD exemption keys on the Pomodoro entry *name* "GTD", not the tag, so tagging changes nothing until the code reads the tags. Near-matches exist (`#pressed_juice`, `#prestige_auto_gold`), and the JS `#hide` test is a case-insensitive **substring** match, so don't copy that helper. | cld/grk vault census; ledger `src/050-plan-budget.js` `exempt: ["GTD"]`, `src/070-ready-and-review.js:46` |
| F12 | **ledger-tools now builds from fragments** *(new)*. It was split into `src/` fragments today (`5680659`, v1.28.1), after the `6f8aca0` snapshot the researchers cited. Edit the fragments (`100-freshness-evaluate.js`, `110-freshness-queue.js`, `120-freshness-footer.js`, `170-plugin-lifecycle.js`) and rebuild; never edit the generated `main.js`. Nav is still a single `main.js`. | bob-plugins `git show --stat 5680659` |
| F13 | **The current decision forbids this.** Decision `review-walk-is-tiered` says "recurring, daily-note, hidden, dependency-blocked, future-scheduled, and Today-linked tasks are in no tier" and rejects a nav-only walk. Accepted records are immutable, so this change needs a successor record. | `sase memory read decisions:review-walk-is-tiered` |
| F14 | **The trial forbids mid-trial ritual changes.** §13 trial runs 2026-10-05 → 10-18: "Don't change the ritual mid-trial." The tally includes "minutes to Commitments done". The keep rule uses red-chip mornings, confirmed FRESH, and lost-needed-task. | `docs/freshness.md` §13 |
| F15 | **Size of the last tier addition.** REFERENCES took bob-cli `54712fe` (17 files, +860/−767) and bob-plugins `79d5975` (+408/−502), plus later fixes. | cld |

## Critique of the plan

Is this a good idea? **Yes, with fences.** I would not take a fundamentally different approach.

### What is right

- **It fixes the measured failure.** The chores are invisible at the moment they're due, then
  get batch-closed days later.
- **It follows GTD's own order:** get clear (inbox, email, calendar) before you get current
  (action lists). That is how the GTD Weekly Review checklist runs (cdx).
- **It gives the review a finish line.** Today the review has no exit gate.
- **Tags generalize for free.** A one-off or weekly item can join PRE or POST with no code
  change.

### What to watch

1. **Two kinds of work share one queue.** Walk rows ask "is this still right?" and are
   answered by a stamp. Checklist rows ask "did I do it?" and are answered by completion. If
   that line blurs, a recurring task could get stamped (and Tasks would copy `[fresh::]` onto
   tomorrow's occurrence), counted as upkeep, or turned into a decay card. Fence it in the
   contract and the tests ([R5](#requirement-adjustments)).
2. **It reverses an accepted invariant ([F13](#what-exists-today)).** Write a successor
   decision record; don't add a quiet exception.
3. **Habits re-enter the trusted list.** Earlier research (`gtd_morning_review_pomodoro_cutover`,
   Finding 7) suggested moving teeth, pills, and stretches out of `#task`. This request goes
   the other way, making them impossible to miss. That's legitimate, but it costs about 7
   completions before NEW. Consider merging the body chores into one line.
4. **"Read Email" can swallow the review.** Time-box it (for example "≤5 min: 2-minute replies,
   else capture").
5. **"≈10 min" is no longer true.** The walk is now PRE + 51 commitments + optional ROTTEN.
   Drop the duration, or scope it to the commitment walk.
6. **POST is an assertion, not proof.** Show the remaining PRE, commitment, and ROTTEN counts
   when the walk lands on POST. Never block it and never auto-complete it.
7. **A skipped chore keeps PRE non-empty**, so "Commitments done" won't fire. That is
   truthful. If a chore routinely happens later in the day (stretches?), remove its `#pre`.
8. **Cost (F15):** roughly a REFERENCES-sized epic, plus a new nav gesture and a cycler API
   entry.

### Alternatives rejected

| Alternative | Why not |
| --- | --- |
| Second keymap, or opening `gtd_daily.md` first | Status quo; PRE is exactly what gets skipped. |
| Membership by file path or note frontmatter | Ties membership to one file and still needs a Morning review exception. |
| Lift the recurring exclusion for all tasks | Bank and medication chores would land in NEW, then ROTTEN. Recurring tasks can't be stamped, so Alt+Shift+F would stall on them. |
| Drop `repeat` so the chores become ordinary Ready tasks | They'd blow the area note's ready cap (8 > 5), enter NEW then ROTTEN on a 7-day lease, and stop being daily checkboxes. |
| Daily-note template checkboxes (not `#task`) | `]s` can't reach them, and weekly cadences become impossible. |
| Configurable tag lists | Adds Rust/JS parity work. Hard-coded tags, like `#hide`, are enough. |

## How the four reports compared

### Where the reports agreed

- The idea is good. Keep `]s` as the only morning chord: no `]g`, no gtd-only walk, no
  dash section.
- Identity comes from **tags**, not a file path, `^pre`/`^post` block IDs (one per line, so
  seven chores can't share one), an inline field (trailing-field parse risk, per the `#now`
  record), or a nested `#gtd/pre`.
- Put the tiers **in both evaluators** with a schema bump and parity vectors, following the
  PROJECTS/REFERENCES precedent. A nav-only walk is rejected by F13.
- **Complete through Tasks; never stamp.** Recurring members keep null `state`/`bucket`. Never
  lift the recurring exclusion globally: the other open recurring tasks (3 in `recur.md`, 1
  in `cash.md`, per grk) would land in NEW, then ROTTEN.
- **Today membership does not hide a tagged row.**
- Sort PRE and POST by `path ↑, line ↑`, so the file order in `gtd_daily.md` is the checklist
  order.
- Tag only the 8 active dailies. Rewrite Morning review. Write a new decision record.

### Disagreements and how I resolved them

| Question | Positions | Resolution | Deciding evidence |
| --- | --- | --- | --- |
| **Where POST sits** | cdx, cld: after ROTTEN, reached with `]S`. grk, gem: between REFERENCES and ROTTEN, because 77 ROTTEN rows make POST "unreachable". | **After ROTTEN, as you asked**, plus a `]S` hint at the boundary. | F4: the checkbox's own definition includes ROTTEN upkeep, so moving POST before ROTTEN would redefine what the checkbox certifies. F10: `]S` reaches POST in one key, so reachability is solved. gem's "72 presses" assumes `]S` doesn't exist. **Reopen** if the tally shows `]S` pressed at the boundary with zero ROTTEN done on most mornings; then move POST before ROTTEN (a one-rank change). |
| **What "ready" means** | grk, gem: strict `[ ]`. cdx: the Ready lane. cld: any open status that is actionable today. | **cld's version.** | F6: chores sit at `[?]` until the hooks run. F7: Ctrl+Enter can't even close them then. A strict `[ ]` rule hides the chores at exactly the moment they're due. |
| **The key on a PRE/POST row** | grk, cld, gem: Alt+Shift+F = complete → next. cdx: keep Alt+F as a review gesture; Ctrl+Enter, then `]s`. | **Complete → next.** | Ctrl+Enter fails on `[?]` (F7). Manual Ctrl+Enter → `]s` is the path that hits F9. A gesture can pick its target *before* writing. |
| **Line-shift identity** | cld: a new text-stable key for checklist rows. cdx: test it and apply the narrowest fix. grk: the handled key is enough. gem: not addressed. | **No new key scheme. Use a text-first cursor match.** | Landings already relocate by text (F9). The gap is only the cursor lookup. Handled `path:line` keys are safe: after an above-insert they name the new future occurrence, which is never in the queue. |
| **Commitment set** | grk, gem: PRE and POST. cld: PRE only; POST is a closing tier. cdx: neither (a separate "preparation" count). | **PRE counts as a commitment; POST is a closing tier.** | With POST last, adding it to commitments would make "Commitments done" impossible before ROTTEN. PRE is required ("includes all of the items before it"). |
| **State of a tagged *one-off* task** | grk: null for all members. cdx, cld: keep its ordinary state and bucket; only the tier changes. | **Keep the ordinary state** (the REFERENCES precedent). | A tag shouldn't silently drop a task from NEW, ROTTEN, or the ready cap. Recurring members are null anyway. |
| **Canonical daily-note exclusion** | grk: keep it. cdx, cld: ignore it for tagged rows. | **Ignore it.** | The tags are explicit intent, and no daily note carries `#pre`. |
| **gem's "Morning Ritual" launcher that auto-completes Morning review** | Only gem proposed it; the other three reject it. | **Reject.** | Auto-completion turns POST into a claim nobody made: the checkbox is an *assertion, not proof* (cdx). A nav-only walk is also rejected by F13. |
| **The trial** | cld raised it; the others were silent. | Tag now; ship when ready and log the date. Or hold until 10-19 (your call). | F14 |

## Requirement adjustments

Each change to what you asked for, called out explicitly:

| # | You asked for | Recommended instead | Why |
| --- | --- | --- | --- |
| **R1** | PRE/POST hold **ready** tasks | Hold **open, actionable-today** tagged tasks: status ` `, `*`, `/`, or `?`; no open dependency; `scheduled` empty or ≤ today; no `#hide`; not under `_templates/` or `_conflicts/`. For these rows **only**, ignore the recurring, canonical-daily-note, and Today exclusions. | F6 and F7. Linking a chore under the GTD Pomodoro, or the hooks promoting it, shouldn't hide it either. |
| **R2** | Tag the tasks that "recur daily" | **Membership is tags only.** Daily recurrence is just the rule for this one-time vault migration. | One-off and weekly tasks then work with no code change. |
| **R3** | "has the `#gtd` and `#pre` tags" | **Exact, whole-token, case-insensitive** tags on the task line. `#gtd` + `#pre` + `#post` → PRE, with lint `checklist_tag_conflict`. `#pre` or `#post` without `#gtd` → not a member, with lint `checklist_tag_incomplete`. Optional lint: a recurring member whose rule lacks `when done`. | F11. Without `when done`, a missed day queues a backlog of past occurrences. |
| **R4** | PRE first, POST last | **Order kept:** PRE → NEW → PROJECTS → PENDING → NEXT → RETURNED → REFERENCES → ROTTEN → POST. *Addition:* PRE counts as a commitment; POST is a closing tier. When POST is non-empty, the ROTTEN boundary notice adds `· ]S closes the review`. | [Resolution table above](#disagreements-and-how-i-resolved-them). |
| **R5** | "close out each … as we get to them" | **Completion is the only way to resolve a row.** **Alt+Shift+F** = complete → next. **Alt+F** = complete in place. **`]s`** = skip. The row stays due; `when done` means no backlog builds up. Counted and Task Link Alt+F batches skip these rows, with a count. These rows never stamp and never touch keeps, decay, `upkeep_today`, the budget, or state counts. | One key carries you through the whole walk. A raw `[x]` write would skip recurrence, so it is forbidden. |
| **R6** | Tag every daily-recurring task except Morning review | Tag only the **8 active** lines: 7 × `#gtd #pre` and Morning review `#gtd #post`. Leave Weekly prune and the two cancelled leftovers untagged, and consider deleting the cancelled two. | Keeps POST to one task, so `]S` = Morning review. |
| **R7** | Tag Morning review | Also **rewrite its text** when the code ships, as a closeout checklist. Remove the inner `]s` recipe, `bob gkeep pull` (now a PRE chore), and "≈10 min". | Otherwise the last row tells you to start the walk you're finishing (F4). |
| **R8** | (implicit) | A **new decision record** that partly supersedes `review-walk-is-tiered`: its tier list, and "recurring / daily-note / Today in no tier" for tagged rows. | F13 |
| *opt.* | (not asked) | Move the Keep import to the **last** PRE line. Merge teeth, pills, and stretches. Time-box email. | Keep import then hands straight off to NEW, and the morning has fewer completions. |

## Recommended solution

### Contract

The contract goes in `docs/freshness.md` §4, §6, and §7, with JSON schema 9.

```text
checklist(t)       = pre   if tags ∋ #gtd ∧ tags ∋ #pre            (exact, case-insensitive)
                   | post  if tags ∋ #gtd ∧ tags ∋ #post ∧ tags ∌ #pre
                   | none
checklist_scope(t) = checklist(t) ≠ none
                     ∧ status ∈ { ' ', '*', '/', '?' }
                     ∧ ¬open dependency ∧ ¬(scheduled > today) ∧ ¬#hide
                     ∧ ¬_templates ∧ ¬_conflicts
                     (recurring, canonical daily note, Today: NOT exclusions here)
tier(t)            = checklist(t) if checklist_scope(t), else the existing rules
order              = pre 0 · new · projects · pending · next · returned · references · rotten · post 8
within pre/post    = path ↑, line ↑
due                = always while in scope; due_on / days_overdue null
state, bucket      = existing evaluation (recurring → null; one-off keeps its own)
counts             = by_tier += pre, post; pre_due, post_due; walk = Σ by_tier;
                     due, new, rotten, fresh, upkeep_today, budget_met unchanged
```

**Trap (cdx):** both evaluators return early when `state` is null. The checklist branch must
assign its tier independently of that early return, or every recurring member silently loses
its tier.

### Code surfaces

**bob-cli**

- `state.rs`: `Tier::Pre`/`Post`, `checklist: Option<ChecklistKind>` on `FreshnessRow`, the
  evaluate branch, the comparator, `ByTier`.
- `scan.rs`: build `checklist` from `RichTask.tags`, and admit checklist candidates from the
  **OPEN** snapshot so `[?]` rows are seen.
- `cli.rs`: `SCHEMA_VERSION` 9, human `PRE n` / `POST n` sections and header counts.
- Lints; Rust state and CLI tests; vectors in the doc.

**bob-plugins / ledger-tools** (fragments, [F12](#what-exists-today))

- `src/100-freshness-evaluate.js`: `FRESHNESS_TIER_ORDER` and the evaluate mirror.
- Row extraction: tags via `planTaskTags`, exact match.
- `src/110-freshness-queue.js`: admit lane-null checklist rows.
- `src/120-freshness-footer.js`: footer tiers; commitment set + `pre`.
- `reviewEntryView`: labels and the hint `Alt+Shift+F done → next · ]s skip`.
- `src/170-plugin-lifecycle.js`: bump the namespace version and add a `checklistTiers: true`
  capability, as `referenceReview` was gated.
- Rebuild via the fragment build.

**bob-plugins / task-status-cycler**

- API **v2** gains `completeTaskAtCursor(editor)`. It runs the same `set-status-symbol-to-x`
  Tasks path plus `finalizeClosedTasks`, and works from ` `, `*`, `/`, and `?`. It returns
  `{ ok, lineDelta }`. If the Tasks command is missing, it refuses with a notice and never
  writes `[x]` raw.

**bob-plugins / navigation-hotkeys**

- Tier recognition and notices.
- The complete → next gesture, gated on the `checklistTiers` capability.
- **Text-first cursor identity** in `planReviewJump`: match the cursor line's exact text
  against `originalMarkdown` first, and fall back to the line number only when no text
  matches. This also makes manual Ctrl+Enter → `]s` safe.
- Counted-batch skip, the boundary `]S` clause, and the POST landing summary.

**Complete → next, step by step:**

1. Identify the current row by the editor line's text, falling back to the line number.
2. Compute the target (the next live entry) **before** writing anything.
3. Call cycler `completeTaskAtCursor`.
4. Add the completed key to the anchor's handled keys.
5. Land through `resolveReviewQueueLine`, which already re-finds a shifted line by its text.
6. Show the notice.

**On POST,** complete and *stay*: show `Review closed — N ROTTEN left for later` instead of
wrapping into a ROTTEN row.

**Notices:**

| Moment | Notice |
| --- | --- |
| Landing on PRE | `PRE 2/7 · Brush teeth · Alt+Shift+F done → next · ]s skip` |
| Commitments → ROTTEN, none left | `Commitments done — 77 ROTTEN left · ]S closes the review` |
| Commitments → ROTTEN, some left | `ROTTEN next — 2 commitments still due` (the count includes PRE) |
| Landing on POST | `POST 1/1 · Morning review · 0 commitments due · 70 ROTTEN left` |

### Vault

**Now (inert until the code ships, F11):** in `~/bob/gtd_daily.md`, put the tags right after
`#task`, matching the 2026-05 archive's `#task #gtd …` style. Fields are unchanged and shown
here as `…`:

```markdown
- [ ] #task #gtd #pre Check weather …
- [ ] #task #gtd #pre Brush teeth …
- [ ] #task #gtd #pre Take fish oil pills + Take L-tyrosine pills …
- [ ] #task #gtd #pre Review Calendar for today and tomorrow + Create @EVENT notes …
- [ ] #task #gtd #pre Read Email …
- [ ] #task #gtd #pre Import inbox tasks from Google Keep …
- [ ] #task #gtd #pre Do morning stretches! …
- [ ] #task #gtd #post Morning review … 
```

**At deploy:** rewrite the POST line as a closeout, for example:

```markdown
- [ ] #task #gtd #post Morning review: PRE done or knowingly skipped · walked to Commitments done · [[crowded|CROWDED]] at 0 · highlight chosen (≤3 themes) · [[rotten|ROTTEN]] until 0, budget, or you stop — then ]S and close this [repeat:: every day when done] …
```

Tasks copies tags forward into each new occurrence, so tagging is a one-time edit.

### Docs and memory

- Update `docs/freshness.md`:
  - §4: the contract and the C-vectors.
  - §6: `[S` starts at PRE; Keep import happens in the walk; ROTTEN is optional; `]S` closes.
  - §7: the JSON schema.
  - §13: a rollout note.
- Update `docs/getting-started.md` and the nav README keymap notes.
- Update the glossary `task-freshness` strand and add the new decision record (for example
  `walk-is-framed-by-checklists`). Make both changes through the `/sase_memory_write`
  workflow.
- The decision record's reopen condition: if PRE rows are skipped with `]s` on most mornings,
  checklist-in-walk isn't working, and the habits should leave `#task`.

### Tests

**Parity vectors (Rust and JS):**

| Vector | Case |
| --- | --- |
| C1 | Recurring `[ ]` `#gtd #pre`, scheduled in the past → `pre`, state null |
| C2 | The same row as `[?]`, with an arrived schedule and no dependency → `pre` |
| C3 | Dependency-blocked, future-scheduled, `#hide`, or `_templates` → none |
| C4 | Today-linked, or in a canonical daily note → still `pre` |
| C5 | `#pre` without `#gtd`, `#pressed_juice` + `#gtd`, or `#gtd/pre` → none, with lints where applicable |
| C6 | Both `#pre` and `#post` → `pre`, plus the conflict lint |
| C7 | One-off `#gtd #post` NEW task → tier `post`, state `new` |
| C8 | Nine-tier order; `walk = Σ by_tier`; `due` unchanged |
| C9 | Stamp refused; keeps and `upkeep_today` unchanged |
| C10 | Tomorrow's generated occurrence is excluded |

**Nav integration tests:**

- Complete all 7 PRE rows in one file, with `recurrenceOnNextLine` both false and true, from
  a stale cache and from a refreshed cache. Cover both Alt+Shift+F and manual Ctrl+Enter →
  `]s`.
- `]S` reaches POST with 77 ROTTEN rows and a null budget.
- A stale previous-day anchor at day rollover does not skip PRE.

**Live check:** one live Obsidian run of the Tasks recurrence and cache timing. Mocks can't
prove that integration.

### Rollout and the trial

1. **Today:**
   - Apply the tags. They are inert.
   - Until the code ships, run the ritual by hand: open `gtd_daily.md` first, then `[S`, and
     close Morning review last.
2. **The epic (phases in order; don't parallelize phases 1 and 2, per grk):**
   1. Contract, Rust, and the decision record.
   2. ledger-tools.
   3. The cycler API and nav.
   4. Rollout: the Morning review rewrite, docs, `bob plugins sync`, and reinstalling `bob`
      (the installed binary lags, [F5](#what-exists-today)).
3. **The trial (F14):**
   - **Default:** ship when ready and record the date in §13. Measure "minutes to Commitments
     done" from the first NEW landing so it stays comparable. The keep rule's quantities (red
     chip, confirmed FRESH, lost-needed-task) are untouched.
   - **Strict alternative:** hold the deploy until 10-19.
   - Either way, don't tune intervals or the budget in the same week.

## Open questions for Bryan

1. **POST last + `]S` (recommended), or POST before ROTTEN?** The second option makes the
   checkbox mean "commitments done, ROTTEN is for later". Changing it is a one-rank change
   plus rewording.
2. **Strict or pragmatic deploy relative to [the trial](#rollout-and-the-trial)?**
3. **Merge the body chores, time-box email, move Keep import last?** All optional.
4. **What does the daily-note `^gtd` wrapper mean now?** My suggestion (cld): it is only the
   GTD Pomodoro's time-logging anchor, and POST is the "review done" signal. Stop cancelling
   the wrapper by hand.

## About this report

The lead researcher's paraphrase of the request:

> **Research request (paraphrased):** Add two review groups to the GTD morning walk that `]s`
> drives in Obsidian. **PRE** is reviewed before every other group and holds any ready task
> tagged `#gtd` and `#pre`; tag every daily-recurring task in `~/bob/gtd_daily.md` this way
> except "Morning review". **POST** is reviewed after every other group and holds any ready task
> tagged `#gtd` and `#post`; tag "Morning review" this way. Each recurring GTD task is closed as
> the walk reaches it. "Morning review" comes last, so checking it certifies everything before
> it, except ROTTEN tasks that can't be reached that day. Research the implementation, critique
> the plan, call out any requirement changes, and recommend a solution.

Consolidated by the lead researcher on 2026-10-04 (Sunday, the day before the 10-05 → 10-18
freshness trial starts). It merges four independent reports (`cdx`, `cld`, `grk`, `gem`, all in
this directory) and my own verification against bob-cli `660c171`, bob-plugins `5680659`, the
live vault (via `bob query`), and live `bob freshness list`.

## Sources and limits

- **Researcher reports** (this directory): `__cdx` (`file:explicit:155f60a8a548179fccebafd7`),
  `__cld` (`file:explicit:0ce43bf4422b72eed11afbc0`), `__grk`
  (`file:explicit:44eed554e548c63e4da61eb2`), `__gem`
  (`file:explicit:539f7246829426583c0bfeff`).
- **bob-cli `660c171`:**
  - `docs/freshness.md` §§4, 6, 13;
  - `docs/task-status-hooks.md`;
  - `docs/vault-git-sync.md`;
  - `src/native/freshness/{state,scan,cli}.rs`;
  - `src/native/dataview/tasks/mod.rs`;
  - README migration notes.
- **bob-plugins `5680659`:**
  - nav `planReviewJump`, `resolveReviewQueueLine`, `buildReviewBoundaryNotice`, and
    `reviewIsCommitmentTier`;
  - ledger `src/050`, `070`, `100`, `120`, `170`;
  - cycler `src/010`, `030`, `110`, `160`, `180`, and `190`.
- **Live data:** `bob query --tasks 'path includes gtd_daily.md'` and
  `bob freshness list -f json` (2026-10-04).
- **Memory and prior research:** `decisions:review-walk-is-tiered`;
  `research:202610/gtd_morning_review_pomodoro_cutover` (Finding 7).
- **External** (cited by cdx, not re-fetched): the GTD Weekly Review checklist, and the
  Obsidian Tasks "Recurring Tasks and Custom Statuses" page.
- **Not verified:**
  - Where Tasks leaves the cursor after a recurrence insert. This decides whether manual
    Ctrl+Enter → `]s` mis-lands *today*; the text-first fix covers both outcomes.
  - Whether cancelling a recurring task spawns its next occurrence. Don't rely on it; skip
    with `]s`.
  - Live Obsidian UI behavior.
- Nothing in the vault, bob-cli, or bob-plugins was modified by this research.
