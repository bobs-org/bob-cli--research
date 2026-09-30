# Task Freshness: Review Every Inbox Task Without Re-Reviewing Everything

Research report — researcher `mus` (independent swarm contribution).
Date: 2026-09-30. Context: `bob-cli-2y` epic (sticky Next/Pending lanes,
ledger-derived Today).

## 1. TL;DR verdict

The plan is a good idea and worth building, with adjustments. The core
insight is sound: Bryan's old habit (re-read the whole READY section every
morning, keep each project ≤5) guaranteed the inbox glance but scaled with
the size of READY instead of with the rate of change. A per-task
last-reviewed date with a default 7-day interval converts the morning review
from "re-read everything" to "read what changed or aged out," which is the
right complexity class for this problem.

I would build it, but I would change five things about the proposal as
stated:

1. **Field name and shape:** use inline Dataview field `[fresh:: YYYY-MM-DD]`
   (date only, task-line scoped), not a bare `fresh` free-text property.
   Reserve `fresh` as the one canonical key; do not accept synonyms.
2. **Interval precedence:** task field `[refresh:: Nd]` (integer days) >
   project-note frontmatter `refresh-interval` (integer days) > default 7.
   Both overrides are optional; malformed values mean "fall back," never
   "never expires."
3. **Scope stays Ready-only for v1**, explicitly excluding Blocked,
   scheduled-future, done/cancelled, `#hide`, `_templates`, and
   `_conflicts` — mirroring the existing lane-query defaults — but the
   staleness predicate must be shared in exactly one place per runtime
   (Rust + JS), not copy-pasted per query.
4. **Writers bump `fresh`, the hooks do not.** Every supported Obsidian
   keymap/capture path upserts `[fresh:: today]` as part of its existing
   line rewrite. `bob task-status-hooks` only lints (missing/malformed
   `fresh`), never auto-stamps — auto-stamping from a cron would silently
   mark tasks "reviewed" that no human saw.
5. **Ship the N-per-day cap on day one**, not as a later fallback. Without
   it, the first morning after rollout is a flood (every task without
   `fresh` is stale by definition), and the flood is what will kill the
   habit.

Recommended solution is in §8. Critique and rationale follow.

## 2. Problem restatement

- The motivating failure is concrete and high-stakes: a same-day commitment
  ("pick up our daughter in the morning") captured via Google Keep →
  `bob gkeep pull` → vault, then never glanced at, fails silently.
- The old process (read all of READY in `~/bob/dash.md` each morning)
  caught this, but cost O(READY) attention daily. Most of that attention
  was wasted on tasks already triaged days ago.
- The new epic (`bob-cli-2y`) makes this worse in one specific way and
  better in another. Worse: sticky lanes mean Next/Pending only grow (~2–3
  tasks/day noted in the `task-lanes-are-sticky` decision record), so
  "just read READY" is now a larger set with no automatic forgetting.
  Better: TODAY/PENDING/NEXT/READY sections are now mutually exclusive and
  lane counts come from `bob-ledger-tools` (`nextBudget`/`pendingBudget`
  with caps), so there is already a proven pattern for "chip counts +
  section query + keymap gesture" to copy for freshness.
- The proposal: stamp each Ready task with the last date a human confirmed
  it ("still needs doing, still looks right"), default interval 7 days,
  per-task and per-project overrides, auto-bump on keymap edits, and a new
  freshness review (stale count, refreshed-today count, next/prev stale
  navigation, one-key refresh).

## 3. What I verified in the tree

- **Inline-field convention exists and is shared.** `src/native/task_fields.rs`
  is the shared `[key:: value]` / `(key:: value)` scanner used by the
  toggle, `bob projects sync`, and the picker. `capture_task_toggle.rs`
  already consumes it for `scheduled`. A new `fresh` key fits this
  machinery cleanly.
- **The native Tasks engine only strips known keys.**
  `src/native/dataview/tasks/task.rs:572-618` (`try_take_dataview_field`)
  recognizes `priority/start/created/scheduled/due/completion/cancelled/
  repeat/onCompletion/id/dependsOn` and leaves anything else (including a
  future `[fresh:: …]`) inside `description`. Consequence: Rust-side
  freshness matching must parse `fresh` out of the line/description with
  `task_fields`, not expect a first-class `TaskDate`. Obsidian-side, the
  same applies: freshness filtering should use `filter by function` with a
  small JS predicate that regex-parses the raw line, exactly as
  `dash.md` already does for Today
  (`ledgerApi.isToday(task)`), rather than assuming `task.fresh` exists on
  the Tasks `Task` object.
- **Lane-query defaults are the scope template.**
  `src/native/dataview/tasks/mod.rs` (`NEXT_QUERY`/`PENDING_QUERY`) and
  `~/bob/dash.md` agree on: not done, not dependency-blocked, no `#hide`,
  no `_templates`, no `_conflicts`, no scheduled date after today. The
  freshness query must reuse these defaults plus `status.type is TODO`
  (Ready) and `isToday !== true`, or READY and FRESHNESS will disagree
  about membership.
- **Today is read-time, and freshness must be too.** Per
  `today-is-read-from-the-ledger`, Today is dedicated Task Links under
  today's open Pomodoros computed at render. Freshness staleness is the
  same kind of derived predicate (`stale = no valid fresh, or
  fresh + interval < today`) and must be computed at render/query time,
  never stored as a second tag that a cron rewrites (the rejected `#today`
  tag pattern).
- **Keymap inventory has room.** `bob-navigation-hotkeys` owns
  `toggle-task-lane` (Alt+N), `jump-to-next/prev-open-task`,
  `jump-to-next/prev-section-header`, `open-dash-tasks` (Ctrl+0);
  `block-id-prompt` owns `link-task-to-pomodoro` (Ctrl+Shift+Enter);
  `task-status-cycler` owns status cycling. A `refresh-current-task` plus
  `jump-to-next/prev-stale-task` fits naturally in navigation-hotkeys,
  reusing the existing jump machinery with a different predicate.
- **Counts pattern exists.** `dash.md` renders TODAY/PENDING/NEXT/READY/
  BLOCKED/PLAN chips in dataviewjs, preferring `ledgerApi.nextBudget()`,
  `pendingBudget()`, `planBudget()` with inline fallbacks. A
  `staleBudget()`/`freshBudget()` (or one `freshnessBudget()`) API on
  `bob-ledger-tools` plus inline fallback is the consistent extension.
- **New Keep tasks arrive without `fresh`.** `src/native/gkeep/render.rs`
  renders one Keep note as `- [ ] #task … [created::…]` plus children.
  Nothing stamps `fresh`, which is exactly what the proposal wants
  (inbox = stale by default). Do not "fix" this by stamping pull time.

## 4. Critique: what's strong

- **Correct default (missing = stale).** The inbox guarantee falls out of
  the data model with no special case: never-reviewed means review-needed.
  This is the proposal's best decision.
- **Interval overrides at two levels are justified.** A 7-day default with
  per-task and per-project overrides matches how Bryan already works:
  most tasks want the default, a few areas (e.g. slow-burn projects) want
  longer, a few hot tasks want shorter. Project-frontmatter override
  parallels the existing per-project `scheduled` frontmatter in
  `src/native/projects/scan.rs`, so the concept is precedented.
- **Bump-on-keymap-edit is the right trigger set.** "Any supported keymap
  edit refreshes" captures revealed attention: if Bryan touched the line
  through a first-class gesture (retarget, reprioritize, link/unlink,
  commit/release, capture rewrite), he looked at it. Explicit-refresh
  covers "looked, changed nothing."
- **Counts + next/prev + one-key refresh is the minimal viable review.**
  It mirrors the existing lane workflow (chips → section → Alt+N) and
  keeps hands on keyboard, which is where this habit lives or dies.

## 5. Critique: risks and gaps in the plan as stated

1. **Manual edits bypass the bump.** The proposal scopes auto-bump to
   "Obsidian keymaps we support" and explicitly declines to monitor manual
   edits. That means hand-editing a line (fix a typo, reword) leaves a
   fresh `fresh` date on a task the human did look at — actually fine —
   but worse, hand-*reviewing* (reading without touching) never stamps.
   The explicit-refresh keymap covers this, but only if it is as cheap as
   the review itself (one key, no modal, no focus theft). If refresh costs
   more than ~1s, reviewers will read-but-not-stamp and the data rots.
2. **A date-user-visible field will get hand-edited.** `[fresh:: 2026-09-20]`
   invites "I'll just fix the date" instead of using the keymap, plus
   malformed values (`tomorrow`, `9/30`, `2026-9-3`). The parser must be
   strict (`YYYY-MM-DD` only, via the existing
   `parse_strict_calendar_date`) and treat garbage as missing (stale), with
   a lint, not an error that breaks the query.
3. **The flood on day one is guaranteed.** Every existing Ready task lacks
   `fresh`, so all of them are stale on rollout. If Bryan has ~100+ Ready
   tasks (plausible given the 48 `[/]` + 25 `[*]` cutover figure), the
   first freshness review is demoralizing. The proposal defers the N/day
   cap to "if it becomes too much work" — it will be too much work on day
   one. Ship capped review from the start (§8).
4. **"Any change bumps" needs a carve-out list.** Some line rewrites are
   not human review: automated `scheduled` pull-forward on link
   (`plan_task_link` retires future `scheduled`), hooks-driven Blocked
   flips, `bob projects sync` normalization, Keep re-pulls. If those bump
   `fresh`, automation launders stale tasks as reviewed. Rule: only
   gestures initiated by Bryan (keymap, picker, capture submit, explicit
   refresh) bump; background reconciliations never do.
5. **Per-project frontmatter needs exact semantics.** Questions the proposal
   leaves open: does the project override apply by task residence (task
   lives in that project note) or by `parent` chain? What about tasks in
   daily notes or the inbox with no project? What wins on conflict
   (task vs. project)? Recommended answers in §6.
6. **Ready-only scope is right for v1 but must be explicit about Blocked
   return.** Per the epic, a blocked/deferred task "comes back as Ready
   (re-triage)." On return it should be stale-immediately (force a glance),
   not inherit its pre-block `fresh` date silently. Either clear `fresh`
   on the Blocked→Ready transition or treat "became Ready since X" as
   stale; simplest is: hooks clearing Blocked does not stamp `fresh`,
   so an old date (or none) naturally reads stale. Document this.
7. **Due/scheduled tasks need a non-duplication rule.** A task due today
   will surface in Today/urgency sorting anyway; showing it again in
   FRESHNESS is noise. v1 should not exclude them (simpler, and the
   morning inbox scan must catch "due today but wrong description"),
   but sort stale with due/overdue last? No — sort stale with due first
   is also defensible. I recommend: no exclusion, sort missing-`fresh`
   first, then oldest `fresh` first, with due/overdue as tiebreak high.
   The lead synthesizer should pick one; either is fine if documented.

## 6. Adjustments I recommend (numbered, as requested)

- **A1 — Key name: `fresh`, value: `YYYY-MM-DD`, one spelling only.**
  Alternatives (`reviewed`, `checked`, `lastSeen`, `freshness`) are all
  reasonable English, but `fresh` is shortest on the line and matches the
  proposal's own language ("task freshness"). Accept only `[fresh:: …]`
  (bracket or paren form per the shared scanner); never migrate synonyms.
  Datetime or relative values (`+7d`, `today`) are rejected as malformed.
- **A2 — Interval keys: `[refresh:: N]` on the task, `refresh-interval: N`
  in project frontmatter, `N` = integer days, 1–365.** I prefer `refresh`
  over `freshInterval`/`refreshEvery` because it reads naturally on the
  line (`[refresh:: 14]`) and in YAML (`refresh-interval: 14`). Task >
  project > 7. Out-of-range/malformed/zero/negative → ignore that level
  and fall through; if all levels invalid, 7. Never allow 0 or "never" in
  v1 (an immortal task is a `#hide` or a done task; a "never refresh"
  escape hatch guarantees rot).
- **A3 — Project membership = residence, not ancestry.** The project
  interval applies to tasks whose *note file* is that project note. Tasks
  in daily notes, inbox, or non-project notes use task-or-default only.
  Rationale: resolvable at query time from `task.path` with no graph walk,
  no `parent`-chain ambiguity, and matches how `scheduled` frontmatter
  already behaves (note-scoped). Ancestry-aware inheritance can be a later
  extension if Bryan asks.
- **A4 — Hooks lint, keymaps stamp.** Add `fresh_missing` /
  `fresh_malformed` info-level lints to `bob task-status-hooks` output
  (count + sample lines), but no auto-write. All `fresh` writes happen in:
  navigation-hotkeys line edits, block-id-prompt link/unlink,
  task-status-cycler transitions, `bob capture` task writes, and the new
  explicit-refresh command. `projects sync`, hooks Blocked flips, and
  Keep re-pulls never write `fresh`.
- **A5 — Ship the daily cap now: default 10 stale/day, weekly sweep.**
  Morning review shows "STALE 23 (showing 10)" with a deterministic order
  (missing first, then oldest `fresh`, due-tiebreak). A `freshness-weekly`
  chore (or just the uncapped FRESHNESS section scrolled past the cap)
  covers the remainder. This is the proposal's own fallback, moved to v1.
- **A6 — Refresh is idempotent and dateless-input.** The refresh keymap
  sets `[fresh:: <today-vault-date>]`, inserting the field if absent,
  replacing in place if present (reuse the `task_fields` span rewrite, not
  string append, to avoid duplicates). Pressing it twice same-day is a
  no-op. It never touches status, priority, scheduled, links, or children.
- **A7 — Glossary term: "Task Freshness (freshness)".** Draft in §7. Keep
  it short: definition, the `fresh`/`refresh` fields, the default, the
  staleness rule, and pointers to dash + keymaps. Do not restate lane or
  Today semantics; link the two superseding decision records instead.

## 7. Draft glossary entry (for the memory web)

> **Task Freshness (freshness).** The last calendar date (vault-local) a
> human confirmed a Ready task still needs doing and still looks right
> (priority, description, project unchanged or deliberately changed),
> stored as inline field `[fresh:: YYYY-MM-DD]` on the task line. Missing
> or malformed `fresh` means stale. A task is stale when it has no valid
> `fresh`, or when `fresh + interval < today`, where interval is the
> task's `[refresh:: N]` days, else its project note's `refresh-interval:
> N` frontmatter (by file residence), else 7 days. Only Ready tasks
> participate (Blocked, done/cancelled, scheduled-future, `#hide`,
> `_templates`, `_conflicts`, and Today-linked tasks are out of scope).
> Supported keymap/capture edits and the explicit-refresh key bump `fresh`
> to today; background reconciliations never do. Surfaced in `dash.md`'s
> FRESHNESS section with stale/refreshed-today chips and next/prev-stale
> navigation.

## 8. Recommended solution (phased)

**Phase 0 — Contract (half day, no code).** Lock A1–A7 with Bryan, write
the glossary strand above, and add the staleness predicate to `docs/plan.md`
next to the Today definition, including 5–10 conformance vectors
(missing → stale; fresh 8 days ago default → stale; fresh 6 days ago →
fresh; `[refresh:: 14]` extends; project frontmatter extends; malformed →
stale; Blocked/scheduled-future excluded; Today-linked excluded).

**Phase 1 — Writers (one slice per surface).** Add an `upsert_fresh(line,
today)` helper next to `task_fields` (Rust) and its JS twin in
navigation-hotkeys' line-edit module; call it from every human-initiated
task-line writer (keymaps, picker, cycler, capture plan/toggle paths).
New tasks from `bob capture` and `gkeep pull` intentionally omit `fresh`.
Cover with unit tests on the helper (insert/replace/idempotent-same-day/
malformed-replaced/duplicate-collapsed) plus one integration test per
caller proving "edit bumps, background sync does not."

**Phase 2 — Review surface.** (a) `dash.md`: new `## Freshness` block with
a `STALE` chip (`stale count/cap`) and `REFRESHED window`, an uncapped
`### STALE Tasks` Tasks query (`status.type is TODO` + shared defaults +
`filter by function isStale(task)`) sorted missing-first/oldest-first, and
a capped `showing N` variant for mornings. (b) `bob-ledger-tools` api v2
extension: `staleBudget()` / `refreshedToday()` (or one
`freshnessBudget()`), midnight-rollover-safe like the Today cache, with
the dataviewjs inline fallback so headless `bob query` still works.
(c) navigation-hotkeys: `refresh-current-task` (one key, no modal),
`jump-to-next/prev-stale-task` reusing the open-task jump with the stale
predicate. Pick unbound or `Ctrl+Alt+J/K`-family bindings to avoid
colliding with Alt+N / Ctrl+Shift+Enter; confirm against Bryan's current
hotkey map before locking.

**Phase 3 — Rollout with cap.** No backfill migration: day-one stale flood
is expected and is absorbed by the cap (default show 10, count shows the
true total). Optional one-time helper `bob freshness seed --before <date>`
for Bryan to stamp self-selected old-but-known-good tasks is allowed, but
no automatic mass-stamp. Add the weekly sweep to the GTD chores
(`dash-lanes` already owns that chore list) and the two hooks lints.
Trial it for the same two-week window as the sticky-lane trial, with the
keep rule: "stale count trends down or holds flat while READY grows; if
morning review exceeds ~10 min, lower the daily cap before touching the
interval."

## 9. Alternatives considered (and why not)

- **Reuse `scheduled` as the review driver.** Bumping `scheduled` to force
  resurfacing conflates "do date" with "looked date" and corrupts urgency
  sorting and the pull-forward logic. Freshness must be orthogonal to
  scheduling.
- **Inbox-only review (skip the interval system).** Simpler, and it solves
  the daughter-pickup case. But it abandons the second win: aging Ready
  tasks whose description/priority/project silently rots. The interval adds
  modest complexity for a real second payoff. If v1 must be cut, cut
  project-level override first, then per-task override — never the default
  interval itself.
- **Spaced repetition / random sampling.** Reviewing a random N/day gives
  probabilistic coverage but no guarantee the *inbox* item appears today.
  Missing-`fresh`-first ordering dominates randomness here.
- **File-mtime or `created`-age as implicit freshness.** Mtime changes on
  any rewrite (including automation) and `created` never advances on
  review; both mismeasure "human looked." Explicit stamp is the only
  honest signal.

## 10. Open questions for Bryan

1. Is Ready-only v1 acceptable, or must Next/Pending also age (the sticky
   lanes grow unbounded without some forgetting pressure)?
2. Cap default: 10/day reasonable, or start at 5 to match the old
   "≤5 per project" muscle?
3. Any project that should ship with a non-7 `refresh-interval` on day one?
4. Confirm the three new hotkeys don't collide with your current map.

## 11. Sources consulted (independent)

Workspace tree only: `sase/memory/{glossary,decisions}.md` descriptors +
`decisions:task-lanes-are-sticky` / `today-is-read-from-the-ledger` strands
via `sase memory read`; `bob-cli-2y` / `bob-cli-2y.10` beads via
`sase bead read`; `plan:202609/retire_now_sticky_lanes.md`;
`src/native/task_fields.rs`, `src/native/dataview/tasks/{mod,task}.rs`,
`src/native/task_status_hooks/`, `src/native/gkeep/{pull,render}.rs`,
`src/native/projects/{model,scan}.rs`, `src/native/capture_task_toggle.rs`;
linked `bob-plugins` (`sase repo open bob-plugins`) keymap inventory and
`bob-ledger-tools` Today/budget APIs; live `~/bob/dash.md`. No peer swarm
report was located, opened, or consulted.
