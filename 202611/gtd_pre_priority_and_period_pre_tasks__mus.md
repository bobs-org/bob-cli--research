# Prioritizing pre-GTD chores and adding period-prep reminders

**Researcher:** mus · **Date:** 2026-11-05 · **Vault observed:** `~/bob/gtd_daily.md` (45 lines, 12 open rows) · **Codebase:** bob-cli checkout (`src/native/freshness/`, `docs/freshness.md`, `docs/guides/run-morning-review.md`, `docs/periods.md`)

## 0. Bottom line

The request is two coupled changes and both are worth doing, but not in the
form first sketched. Add the period-prep reminders as ordinary `#gtd #pre`
checklist rows that mirror their `#gtd #post` period reviews, and order the
PRE tier by explicit bands rather than by an arbitrary per-task number.

Concretely: do the vault change now with no code (reorder `gtd_daily.md`,
fix two tags, add three rows). If an explicit code guarantee is wanted
later, add one optional numeric key that both evaluators sort on
(`order` first, then `path, line`), applied symmetrically to PRE and POST.
Do not reuse `[priority:: P-levels]` for walk order, do not split PRE into
sub-tiers, and do not build a config-ordered list.

The rest of this note shows why: how the walk actually orders PRE/POST
today, the two live bugs the new rows would inherit, the design space with
costs, and the exact recommended rows and comparator.

## 1. How PRE/POST actually work today

### 1.1 The queue and its comparator

The morning walk is one shared queue in tier order `PRE -> NEW ->
PROJECTS -> PENDING -> NEXT -> RECURRING -> TICKLER -> ROTTEN -> POST`
(`docs/freshness.md` section 4; `src/native/freshness/state.rs`
`enum Tier` with `#[derive(Ord)]` in that exact order; `queue()` sorts by
`tier` first). The guide `docs/guides/run-morning-review.md` prints the same
order and shows a typical `PRE 1 / POST 1` split from `gtd_daily.md`.

Within each tier the comparator is fixed (`docs/freshness.md` section 4
table; `state.rs::queue()` match arms):

- `pre | post | new`: `path ASC, line ASC`. No dates, no `created`, no
  priority participate. Every PRE row in the same file walks in file order.
- `recurring`: `due_on ASC, path ASC, line ASC`.
- `projects | pending | next`: null-`due_on` first, then `due_on`,
  `created`, `path`, `line`.
- `tickler`: `due_on, path, line` (`created` deliberately excluded, UB14).
- `rotten`: `interval, due_on, created DESC, path, line`.

`RichTask` (`src/native/dataview/tasks/mod.rs`) currently carries
`path, line, status_symbol, status_type, original_markdown, text,
created/scheduled/due/start, is_recurring, is_blocked, tags, block_id` --
notably **no priority**. So any priority-based PRE ordering needs new
plumbing through `RowCtx::freshness_row()` (`src/native/freshness/scan.rs`)
into `FreshnessRow`, `QueueEntry`, and the `Tier::Pre | Tier::Post` arm,
plus the JavaScript mirror (`api.freshness` in bob-ledger-tools, freshness
namespace v12 per `docs/freshness.md`), plus vectors and docs. Tag-based
ordering needs no new plumbing (tags already flow), but still needs both
comparators, vectors, footer/nav checks, and docs.

### 1.2 What admits a row to PRE/POST

Membership is exact whole-token tags (`state.rs::checklist_from_tags`):
`#gtd + #pre` is PRE, `#gtd + #post` (without `#pre`) is POST. Scope
(`checklist_in_scope`, `checklist_candidate_visible` in `state.rs` /
`scan.rs`) additionally requires: open status symbol in
`{space, *, /, ?}`, not dependency-blocked, not `#hide`, not under
`_templates` / `_conflicts`, and `scheduled <= today`. Recurring,
canonical-daily-note, and Today-linked rows are explicitly admitted here
(unlike every other tier). Checklist rows resolve only by completion
(Ctrl+Enter); they are never stamped, never `decide`, and `due_on` is
always `None`.

The `[?]` symbol matters: the vault's Tasks settings map `[?]` to
`Blocked / ON_HOLD` (observed in
`~/bob/.obsidian/plugins/obsidian-tasks-plugin/data.json`), so
`is_todo` is false and `lane_for_row('?', false)` returns `None`
(`state.rs`). That is fine for checklists -- `queue()` keeps
`lane == None` rows exactly when `tier.is_checklist()` -- but it means a
`[?]` row with no `#pre/#post` is in **no tier at all** (see section 2.2).

### 1.3 Recurrence and the `when done` anchor

All eight daily PRE rows in the vault use
`[repeat:: every day when done]` with a `scheduled` anchor. A weekly POST
row uses `[repeat:: every week on Monday when done]`. With `when done` the
next occurrence counts from the completion day; without it, from the
scheduled day. For calendar-anchored period reviews (must stay on Monday /
1st-Monday / 2nd-Monday) the anchored form is the correct one, and the
existing `when done` on the weekly row is already a drift risk worth
flagging (complete Wednesday, next occurrence drifts off Monday). Any new
period-pre row must use the **same repeat rule and the same scheduled
anchor** as its post sibling or the pair will separate after one late
completion.

### 1.4 The live vault (2026-11-05)

`~/bob/gtd_daily.md` holds 12 open `[?]` rows under one `### Blocked`
heading (the heading is a Tasks-grouping artifact, not freshness state):

- `#gtd #post` Morning review, daily, `scheduled 2026-11-06`.
- 8x `#gtd #pre` dailies: calendar (`Review next week in Google
  Calendar`), weather (`Check weather`), `Brush teeth`, `Read email`,
  `Clean up SASE agents`, `Run task reconcile + gcal sync + gkeep pull`,
  `Take fish oil pills + L-tyrosine`, `Do morning stretches`
  (`scheduled 2026-11-11`, the only non-daily of the eight).
- `#gtd #post` Weekly review, `every week on Monday when done`,
  `scheduled 2026-11-09`.
- `#gtd` (no pre/post) Quarterly review,
  `every 3 months on the 1st Monday`, `scheduled 2027-01-04`.
- `#gtd` (no pre/post) Yearly review,
  `every January on the 2nd Monday`, `scheduled 2027-01-11`.

All PRE rows share one path, so today PRE walks in line order (calendar
first, fish-oil last). The requested bands -- period-prep, then SASE
cleanup, then the three browser chores (weather, email, calendar), then
everything else -- are exactly a permutation of those lines. Section 2
covers the two bugs hiding in that list.

## 2. Two bugs the proposal must fix first

### 2.1 Quarterly and Yearly reviews never walk (missing `#post`)

Per section 1.2, a `[?]` (ON_HOLD, `lane == None`) row without
`#pre/#post` gets `tier == None` from `evaluate()` -> `overlay_checklist`
(no checklist) -> `overlay_recurring` (early-returns on `lane.is_none()`)
-> `evaluate_without_checklist` (needs `is_todo`, false). So the Quarterly
and Yearly rows, both `[?] #task #gtd` with no `#post`, are scanned
(`OPEN_QUERY` sees them) but never queued, never counted in `by_tier`,
never shown by `bob freshness`, never landed on by `]s`. The Weekly review
walks only because it carries `#post`.

Fix before adding anything: give both rows `#post` (they are closeouts:
prune, set Outcomes, write Reflection -- POST semantics per
`docs/concepts/freshness-and-the-review-walk.md`). Proposed exact lines in
section 5 keep their repeat rules and scheduled anchors and only add the
missing `#post` token. This is also the precondition for "trigger on the
same day as the corresponding post task": a pre row with the same repeat
and anchor becomes due on the same mornings the post row does, through the
same `scheduled <= today` gate.

### 2.2 `when done` vs anchored repeats for calendar periods

Making Quarterly/Yearly `#post` exposes a second issue: both repeats lack
`when done` (`every 3 months on the 1st Monday`, `every January on the 2nd
Monday`), so `checklist_repeat_not_when_done` will lint them
(`scan.rs::checklist_lints`: `has_gtd && (has_pre||has_post) &&
repeat_lacks_when_done`). That lint exists to catch daily chores that
should count from completion, but for quarter/year rows the anchored form
is arguably correct: a Q4 review completed a week late should still spawn
next quarter on schedule, not drift a week. The weekly row has the
opposite shape (`when done` present, no lint, but drift-prone).

Do not silently add `when done` to force the lint quiet. Decide per row:
daily and weekly preparation chores keep `when done` (they track "did I do
it", drift of a day is harmless and the next Monday re-anchors weekly
anyway if completed on time); quarterly and yearly stay anchored (no
`when done`) and the lint gains a documented period-row exception, or the
rows accept the lint as known-noise. Section 5 recommends keeping the
existing anchors verbatim for the mirror pairs and handling the two new
quarterly/yearly-post lints as accepted period-row noise until a
lint-exception ships, rather than changing recurrence semantics to please
a lint. Either way this must be an explicit decision, not an accident of
copy-paste.

## 3. Critique: is prioritizing PRE a good idea?

Yes for the three named bands, no for a general per-task priority dial.
Three structural facts push that way:

1. **PRE is already an ordered checklist, and its order is visible.**
   `path, line` means the file the human edits is the walk. Reordering
   eight lines in `gtd_daily.md` delivers the entire requested Monday
   experience with zero code, zero sync risk, and zero new syntax to
   learn. Any explicit key must beat "move the line up" on reliability,
   because it loses on beauty and intuitiveness by construction.
2. **A general numeric priority duplicates the P-level system.**
   `[priority:: highest/high/medium/low/lowest]` already exists with
   scheduling (`schedules`, roll windows P1 3-8d through P4 101-365d in
   `~/.config/bob/config.yml`), picker, and decay (`freshness.decay`,
   `decisions:task-decay-is-one-ladder`) semantics. Reusing it for
   "walks earlier in PRE" conflates "do this review step first" with
   "this work is important", invites `Alt+P` previews and roll prompts
   (`docs/freshness.md` sections 6-7, footer `Alt+P` hint) onto opening
   chores, and still needs the same plumbing as a new key (priority is
   parsed in `task.rs` but deliberately not carried on `RichTask`).
3. **PRE must stay short.** The walk opens with PRE every morning; the
   footer counts it as commitments (`glossary:morning-gtd-review-footer`),
   `]s` starts there, and `Morning review` POST explicitly gates on "PRE
   chores done or knowingly skipped". Growing PRE from 8 to 11 rows (3
   period-preps) is acceptable because at most one period-prep is due on
   most days (weekly on Mondays only; quarterly 4x/year; yearly 1x/year --
   section 4 shows the coincidence math). A free-form priority invites
   PRE bloat: every chore wants to be first. Fixed bands ("period-prep,
   then SASE, then browser batch, then rest") cap that pressure.

Alternative approaches considered and rejected (or deferred):

- **Split PRE into sub-tiers (e.g. PRE_HIGH / PRE).** Rejected. It
  changes `Tier` ordering, the nine-tier contract both evaluators cite,
  `by_tier` histogram keys and schema, the footer group list and colors,
  `]S`/`[S` group cycling, and every vector in `state_tests.rs`. Bands
  within one tier need none of that.
- **Config-ordered patterns** (`freshness.pre_order: [...]` substring or
  tag list). Rejected. Ordering leaves the vault (invisible while
  reviewing), needs config parsing + fallback + JS parity + docs, and
  breaks the "the file is the walk" mental model. Keep ordering where
  the chores live.
- **Heading-grouped PRE** (`### Period prep` sorts before `### Browser`
  regardless of lines). Rejected for now. `Task.heading` exists but is
  not plumbed to `RichTask`; heading renames would silently reorder the
  walk; and headings in `gtd_daily.md` currently serve Tasks grouping,
  not walk semantics.
- **One umbrella Monday pre-task** ("if Monday, check `bob periods list
  -p` and prep whatever is due") instead of three mirroring rows.
  Deferred as an option, not the recommendation. It halves Monday noise
  but reintroduces the logic the walk already implements: the three
  mirroring rows are each due exactly when their post sibling is due, so
  "which periods need review today" needs no human or agent reasoning.
  Revisit only if three rows prove noisy on quarter/year Mondays (at most
  5 Mondays a year carry two period-preps; only the 2nd Monday of
  January can carry three -- and only when it is also a quarter-start
  Monday).
- **Move period-prep out of PRE** (ordinary `#task` RECURRING rows, or
  Today-linked rows). Rejected. RECURRING requires a lane status
  (`overlay_recurring` needs `lane.is_some()`; `[?]` has none), refuses
  keeps, and resolves by completion-or-reschedule rather than by the
  checklist gesture the morning ritual expects. PRE is the right tier:
  these are opening chores resolved by completion.

Adjustment to the brief: the "browser" band should be an explicit closed
list (weather, email, calendar -- the three rows named), not a heuristic
("anything requiring my browser"). `Run task reconcile + gcal sync +
gkeep pull` also touches the network but is not a browser chore; a
heuristic would misfile it. Name the three rows; keep the band adjacent in
the file (and, if a code key ships, on the same band value) so the batch
stays atomic.

## 4. Design space for within-tier ordering

All options keep the nine tiers and the `path, line` tiebreak at the end.
The question is only what sorts before it inside PRE (and symmetrically
POST, since the request says "and/or" and symmetry is free).

| Option | Key | Plumbing | Intuitive? | Reliable? | Beautiful? |
| --- | --- | --- | --- | --- | --- |
| A. File order (status quo) | line number | none | yes -- WYSIWYG | medium -- drifts if Tasks recurrence ever re-appends lines; breaks across files | best -- zero syntax |
| B. Reuse `[priority::]` | `high..lowest` | `Task.priority` -> `RichTask` -> `FreshnessRow` -> `QueueEntry` + JS | no -- conflates review order with P-level urgency/scheduling/decay | high | poor -- adds P-level pills and roll affordances to chores |
| C. New `[order:: N]` (recommended if code ships) | integer, missing last | new non-Tasks run-extending key alongside `keeps`/`unblocked` (`placement.rs` suffix scan, `task.rs` details, `RichTask`, `FreshnessRow`, `QueueEntry`, JS mirror) | yes -- one number, one meaning, only read in PRE/POST | high -- stable across moves, files, recurrence | good -- one small field, hidden from description, documented in one place |
| D. Priority tags (`#ord-1` etc.) | tags | comparator only (tags already flow) | medium -- tag soup, pill noise, no natural "missing sorts last" story | medium -- renames reorder silently | poor -- every chore gains a pill |
| E. Band tags (`#period-pre`, `#browser`, ...) | closed tag set | comparator with fixed band order | medium -- readable but hard-codes today's three bands | low -- every new band needs a code + docs change | medium |

Notes on cost. Options B-E all touch `state.rs::queue()` (PRE/POST arm),
`state_tests.rs` vectors (CL/CL8 family), `docs/freshness.md` section 4
table, `docs/guides/run-morning-review.md`, the `api.freshness` JS mirror
and its conformance vectors, and the `bob-navigation-hotkeys` landing
(`]s` from outside starts at PRE's first row -- first row changes meaning)
and footer (group counts unchanged, but `TIER i/M` positions within PRE
shift). Option C additionally touches the Tasks suffix parsers on both
sides; it must be placed with `keeps`/`unblocked` as a run-extending
non-Tasks key so right-to-left Tasks parsing still finds `scheduled` /
`dependsOn` / `id` to its right (cf. the `P2`-hides-fields warning in the
managed `config.yml` comments). Option B additionally risks decay and
schedule-log interactions and is rejected on semantics, not just cost.

Recommendation on scope: bands, not a dial. Whether the key is line
position (A) or a number (C), constrain values to the four requested
bands (period-prep = 1, SASE = 2, browser batch = 3, rest = default) and
document them as bands. An unbounded 1-999 dial turns PRE into a second
READY queue and will be spent (see section 3.3). If C ships, validate
`1-9` (or `1-4`) and reject the rest with the existing lint path; do not
mirror the 1-999 `keeps` range.

Coincidence behavior (why bands are enough): weekly PRE/POST are due on
Mondays (`scheduled 2026-11-09` observed); quarterly on 1st-Mondays
(`2027-01-04`); yearly on 2nd-Monday January (`2027-01-11`). Daily PRE
rows are due every morning. So a Monday walk is: 1 period-prep (usually
weekly; quarterly/yearly only on their Mondays) + SASE + 3 browser + rest
(brush, reconcile, fish-oil, stretches when due). Quarter Mondays carry at
most weekly + quarterly; year Mondays at most weekly + yearly except the
rare triple Monday. Within-band order stays `path, line`, which keeps the
browser triple atomic as long as the three lines stay adjacent.

## 5. Recommended solution

### 5.1 Vault change (ship now, no release train)

1. Fix the two period-post tags: add `#post` to the Quarterly and Yearly
   rows, leaving repeat and anchor verbatim.
2. Add three period-prep rows at the top of the PRE block, each mirroring
   its post sibling's repeat and anchor verbatim (same due mornings by
   construction). Keep `[?]` and `#gtd #pre`. Wording names the agent
   action and the `periods` command so the row is completable without
   remembering anything:
3. Reorder the PRE block into the four bands (period-prep, SASE, browser
   triple adjacent, rest). POST order unchanged.

Proposed PRE block (anchors mirror the live posts; `created` set at write
time; `scheduled` equals the post sibling's anchor so pairs coincide from
day one):

```markdown
- [?] #task #gtd #pre **Prep weekly review**: run `bob periods list -p` and `bob periods brief 2026-W45 -f md`; launch the weekly agent when Review is empty  [repeat:: every week on Monday when done]  [created:: 2026-11-05]  [scheduled:: 2026-11-09]
- [?] #task #gtd #pre **Prep quarterly review**: run `bob periods list -p` and the quarter brief; launch the quarterly agent when Review is empty  [repeat:: every 3 months on the 1st Monday]  [created:: 2026-11-05]  [scheduled:: 2027-01-04]
- [?] #task #gtd #pre **Prep yearly review**: run `bob periods list -p` and the year brief; launch the yearly agent when Review is empty  [repeat:: every January on the 2nd Monday]  [created:: 2026-11-05]  [scheduled:: 2027-01-11]
- [?] #task #gtd #pre **Clean up SASE agents on athena and apollo**: Restart failed agents, dismiss agents from yesterday, review inboxes, update SASE on all machines!  [repeat:: every day when done]  [created:: 2026-11-05]  [scheduled:: 2026-11-06]
- [?] #task #gtd #pre Check [weather](https://google.com/search?q=weather)  [repeat:: every day when done]  [created:: 2026-11-05]  [scheduled:: 2026-11-06]
- [?] #task #gtd #pre Read email  [repeat:: every day when done]  [created:: 2026-11-05]  [scheduled:: 2026-11-06]
- [?] #task #gtd #pre Review next week in Google Calendar  [repeat:: every day when done]  [created:: 2026-11-05]  [scheduled:: 2026-11-06]
- [?] #task #gtd #pre Brush teeth  [repeat:: every day when done]  [created:: 2026-11-05]  [scheduled:: 2026-11-06]
- [?] #task #gtd #pre Run `task reconcile` + `gcal sync` + `gkeep pull`  [repeat:: every day when done]  [created:: 2026-11-05]  [scheduled:: 2026-11-06]
- [?] #task #gtd #pre Take fish oil pills + Take L-tyrosine pills  [repeat:: every day when done]  [created:: 2026-11-05]  [scheduled:: 2026-11-06]
- [?] #task #gtd #pre Do morning stretches [created::2026-07-06] [scheduled:: 2026-11-11]  [repeat:: every day when done]
```

Accept the two new `checklist_repeat_not_when_done` lints on the anchored
quarterly/yearly pairs (pre and post) as known period-row noise, or ship a
narrow lint exception for rows whose repeat names a 1st/2nd-Monday anchor;
do not add `when done` to silence them (section 2.2). Keep `Do morning
stretches` last (future-scheduled, out of scope until 2026-11-11 --
unchanged behavior, still walks last when due).

### 5.2 Code change (only if file order proves insufficient)

Ship option C narrowly, symmetrically for PRE and POST:

- New optional inline key `[order:: N]`, `N` in `1..=4` (band values:
  1 period-prep, 2 SASE, 3 browser, 4 explicit-rest; missing sorts after 4
  as today). Non-Tasks run-extending key in canonical position with
  `keeps`/`unblocked`; invalid/duplicate values lint and fall through to
  missing (same pattern as `read_freshness` note/task fallthrough).
- Comparator: `Tier::Pre | Tier::Post` sorts by
  `order ASC NULLS LAST, path ASC, line ASC`. All other tiers untouched.
  Missing stays exactly today's `path, line` behavior, so the vault
  change in 5.1 keeps working verbatim with or without the key, and the
  browser triple stays atomic (same band, adjacent lines).
- Parity: Rust (`placement.rs` read/canonicalize, `state.rs`
  `FreshnessRow.order` + `QueueEntry.order` + `queue()` arm,
  `scan.rs` plumbing, `state_tests.rs` CL-band vectors) and the JS
  `api.freshness` mirror under shared vectors; `docs/freshness.md`
  section 4 table + schema note, `run-morning-review.md` ("top walks
  first; `[order::]` breaks ties across files"), `task-tag-marks.md`
  only if the field renders a mark (prefer no mark: order is walk
  metadata, not task content). No `Tier`, `by_tier`, footer-group, or
  `]S` changes: bands live inside the tier, not as tiers.
- Gate: `bob freshness list` (human + `-f json` new `order` member, additive
  only) and `]s`/`[s`/`]S` walk-through on a fixture vault carrying the
  5.1 rows plus band keys; confirm quarterly/yearly POST rows appear on
  their anchor Mondays and period-pre rows coincide.

Explicit non-goals: no `[priority::]` reuse, no sub-tiers, no config list,
no heading-grouping, no POST reordering pass (apply the same key only if a
POST band need appears), no P-level, schedule, decay, Today, or bucket
changes (freshness never changes those -- `decisions:task-decay-is-one-ladder`,
`decisions:review-walk-is-tiered`).

## 6. Verification and risks

- Verified from the checkout and live vault in this session: PRE/POST
  comparator (`state.rs::queue()`), checklist admission
  (`checklist_from_tags`, `checklist_in_scope`,
  `checklist_candidate_visible`), `[?]`/ON_HOLD mapping (vault Tasks
  `data.json` + `lane_for_row`), `RichTask` field set (no priority),
  `by_tier` counting, `checklist_repeat_not_when_done`
  (`scan.rs::checklist_lints`), and the 12-row `gtd_daily.md` census with
  the two tag-missing period rows. Not run: `bob freshness` against
  `~/bob` (binary build exceeds this turn's budget) and the JS
  `api.freshness` sources (live in the linked `bob-plugins` repo, not
  opened per `/sase_repo` -- cited from `docs/freshness.md` parity notes
  only).
- Risks: (a) Tasks recurrence line placement -- confirm the next
  occurrence of a completed `when done` checklist row keeps its line
  (else file order degrades and option C becomes required, not
  optional); (b) quarter/year Mondays briefly lengthen PRE to ~11 rows
  -- acceptable at 4+1 days/year, but watch the morning-review closeout
  text ("PRE chores done or knowingly skipped" already permits skipping);
  (c) any `[order::]`-style key must land in the managed-config
  `priority`-values warning category: unknown placement hides
  `scheduled`/`dependsOn`/`id` from Tasks parsers, so placement and JS
  parity tests must cover it.

## 7. Evidence index

Code: `src/native/freshness/state.rs` (`Tier`, `checklist_from_tags`,
`checklist_in_scope`, `overlay_checklist`, `overlay_recurring`,
`lane_for_row`, `queue()`, `QueueEntry`, `by_tier`);
`src/native/freshness/scan.rs` (`RowCtx::freshness_row`,
`checklist_candidate_visible`, `checklist_lints`,
`repeat_lacks_when_done`); `src/native/freshness/placement.rs`
(suffix order `fresh, refresh, keeps, unblocked`); 
`src/native/dataview/tasks/mod.rs` (`NEXT/PENDING/READY/OPEN_QUERY`,
`RichTask`); `src/native/dataview/tasks/task.rs` (`Priority`,
`status_type`); `src/native/freshness/state_tests.rs` (CL/CL8, RC10-12)
and `placement_tests.rs`; `src/native/config/plan.rs` (lane caps,
unrelated to PRE order).

Docs/decisions: `docs/freshness.md` sections 2/2a/4/6/7/10-13;
`docs/guides/run-morning-review.md`; 
`docs/concepts/freshness-and-the-review-walk.md`;
`docs/periods.md` (week/quarter/year/all-time ids, `brief`/`draft`,
`list -p`, period-note holds no `#task` rows);
`docs/plan.md` (lane review paragraph);
`docs/task-tag-marks.md` (GTD checklist marks);
`decisions:review-walk-is-tiered`,
`decisions:recurring-occurrences-walk-when-due`,
`decisions:task-lanes-are-sticky`, `decisions:task-decay-is-one-ladder`,
`decisions:ready-is-freshness-gated`, `decisions:today-is-read-from-the-ledger`;
`glossary:task-freshness`, `glossary:morning-gtd-review-footer`;
`cli_rules.md` (consulted for the `[order::]` CLI-surface implications;
no CLI surface changes proposed).

Vault/config: `~/bob/gtd_daily.md`; `~/bob/2026/2026-W45.md` (weekly
callout shape the prep rows reference); `~/.config/bob/config.yml`
(`freshness`, `plan`, `properties.priority` P1-P4 windows);
`~/bob/.obsidian/plugins/obsidian-tasks-plugin/data.json`
(`[?]` = `Blocked/ON_HOLD`).




