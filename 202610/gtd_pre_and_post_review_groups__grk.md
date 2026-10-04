# PRE and POST groups on the `]s` morning review walk

Researcher: `grk`. Independent report. Do not treat this as the swarm synthesis.

> **Research query:** Add two new review groups to the GTD morning review triggered by `]s` in Obsidian: PRE (before every other group) and POST (after every other group). PRE holds ready tasks tagged `#gtd` and `#pre`; POST holds ready tasks tagged `#gtd` and `#post`. Tag the daily recurring tasks in `~/bob/gtd_daily.md` with `#gtd #pre`, except the "Morning review" task, which gets `#gtd #post`. Close each recurring GTD task as it is reached; Morning review is last so it can be checked after everything before it, except ROTTEN left undone that day. Is this a good idea? Would a different approach be better? Adjust requirements if justified. Recommend a solution.

## Bottom line

1. **Do it as two new walk tiers on the existing `]s` queue, with three required adjustments.** Putting the daily GTD checklist on the same finger-memory as NEW / PROJECTS / PENDING / NEXT / RETURNED / REFERENCES / ROTTEN is the right idea. Those habits are already overdue and invisible to the walk. Tags are the right membership. Closing them (Tasks "when done") is the right outcome. A second keymap, a dash section, or a freshness stamp on a recurring line would all miss the point.

2. **POST must sit at the commitment closeout, before ROTTEN, not after it.** **ADJ-1.** The request's "after any other review group" fights its own parenthetical: Morning review is meant to cover everything *except* ROTTEN you skip. Today's "Commitments done" notice is already that boundary. Putting POST after 77 ROTTEN rows makes the checkbox unreachable without walking or jumping the upkeep pile.

3. **Alt+Shift+F on PRE/POST must complete through the Tasks plugin, then advance. It must not stamp.** **ADJ-2.** Recurring lines are refused by `stampLine` / `keepLine` so the next occurrence does not inherit a fake `[fresh::]`. The walk's keep gesture is the wrong verb for a habit checkbox. One-at-a-time only; counted `N` Alt+Shift+F must not batch-complete real-world actions.

4. **Do not lift the recurring exclusion globally, and do not feed PRE/POST into buckets or chips.** **ADJ-3.** Membership is tag AND ready (`[ ]`) AND scheduled empty-or-due. Recurring stays out of every other tier. `state` / `bucket` stay null, like lane rows. Dash NEW / READY / `rotten.md` / note-ready caps stay unchanged.

The adjustments are marked **ADJ-n**. The design is in [Recommended solution](#recommended-solution).

## Is this a good idea

### What is right

- **The daily GTD checklist is currently invisible to the only morning keymap.** `gtd_daily.md` holds seven open daily habits plus the Morning review chore. Every one is `[repeat:: every day when done]`. The evaluator's `walk_scope` / `in_scope` both require `!recurring`, and stamp helpers refuse a `repeat` field so Tasks will not copy `[fresh::]` onto tomorrow's instance (`docs/freshness.md` §3 P13, §4 S13; `state.rs` `evaluate`; ledger-tools `freshnessEvaluate`). Live `bob freshness list` on 2026-10-04 has **zero** `gtd_daily.md` rows. The one GTD-named queue hit is `bob_gtd.md:21`, a Next-lane project task. The checklist lives in a file you have to remember to open. That is the failure mode `research:202610/gtd_morning_review_pomodoro_cutover` already named: life admin slides while the review machinery grows.
- **Those habits are already late.** Scheduled dates on the open daily lines are 2026-09-29 (weather, teeth, pills, calendar, email, Keep), 2026-10-04 (stretches), and 2026-09-30 (Morning review). Today is 2026-10-04. Five of the seven PRE candidates have been due for five days. Recurrence did not save them, because nothing in `]s` lands on them.
- **One keymap should own the morning order.** `]s` / `[s` / `[S` / `]S` in `~/bob/obsidian_vimrc.md` call `bob-navigation-hotkeys:jump-to-next-due-task` (and prev/first/last). `planReviewJump` walks `api.freshness.queue()` in source notes and does not sort. PROJECTS and REFERENCES already proved that new structural tiers, not a new chord, are how the walk grows. PRE before NEW is GTD "get current" (body, calendar, inbox) before commitments. POST as a closeout checkbox is the missing finish line for the ritual itself.
- **Tags are the right membership, and the namespace is free.** Historical morning lines already used `#gtd` (see `done/2026/20260528_day_done.md`: weather, teeth, pills, calendar). Live Tasks census: 12 tasks with `#gtd`, **0 open**; **0** tasks with `#pre`, `#post`, `#gtd/pre`, or `#gtd/post`. Requiring both `#gtd` and `#pre` (resp. `#post`) keeps a stray `#pre` out and keeps `#gtd` queryable the way the 2026-05 archive already was. Whole-token match, the same rule as `#hide` in the seed (`seed.rs`: `tag == "#hide"`).
- **Closing "when done" is the correct off-ramp.** `recur.md` shows the Tasks pattern: the done instance stays with a `[completion::]` date, and a new `[ ]` instance is inserted with the next `scheduled`. Tags copy forward. Tomorrow's line has a future `scheduled`, so READY_QUERY's "scheduled on or before today" keeps it out until the next morning. No freshness stamp is required or wanted.
- **The add is small against today's walk.** Live queue: 128 due (4 NEW, 36 NEXT, 1 RETURNED, 10 REFERENCES, 77 ROTTEN; pending and projects empty). Seven PRE + one POST is eight glances, in file order, before the existing 128. That is the cheap part of the morning. The expensive part is still NEXT and ROTTEN.

### What is wrong or incomplete in the request as written

- **"POST after any other review group" includes ROTTEN.** Live ROTTEN is 77. The Morning review text already says ROTTEN is "fine to stop partway." `docs/freshness.md` §6 and the footer treat NEW → PROJECTS → PENDING → NEXT → RETURNED → REFERENCES as **commitments**, ROTTEN as **upkeep**, with a "Commitments done — N ROTTEN left" boundary notice. If POST is last, reaching the checkbox means walking or `]S`-jumping the upkeep pile. Checking it then either lies (ROTTEN skipped) or forces finishing ROTTEN to make the checkbox honest. The parenthetical in the request is the real rule: POST means "I did the required morning, ROTTEN excepted." That is the commitment closeout, not a row after upkeep.
- **The walk's default action is stamp-and-advance. These tasks cannot be stamped.** Alt+Shift+F calls `api.freshness.keepLine`. Recurring is a hard refusal. If PRE/POST land in the queue and Alt+Shift+F no-ops, the keymap feels broken and the habits stay open. Completing must go through the Tasks plugin command (`task-status-cycler` already does this: `tryExecuteTasksCommand` so recurrence insertion fires). A local `[ ]` → `[x]` flip is not enough.
- **"Ready task" plus "recurring" is a contradiction in the current contract.** Ready in freshness means TODO, lane-visible, **non-recurring**, not daily-note, not Today. The request's PRE/POST members fail that predicate today. The exception has to be explicit and narrow: ritual tags bypass the recurring (and, see ADJ-4, Today) exclusions *only* for PRE/POST tier assignment, and they still do not acquire a Ready `state` / `bucket`.
- **The Morning review task cannot keep describing the walk once it is *in* the walk.** Line 18 of `gtd_daily.md` currently starts with "`bob gkeep pull`, then ]s / Alt+Shift+F through NEW → PENDING → NEXT → RETURNED…". It is already stale (no PROJECTS / REFERENCES). If that line is the POST target, completing it while standing on it is recursive, and it still tells you to run `]s` as a step of itself. Rewrite it as a closeout checkbox. Keep import is also duplicated: it is both a PRE candidate ("Import inbox tasks from Google Keep") and step 1 of the current chore / `docs/freshness.md` §6.
- **Counted sessions would complete several real-world actions in one key.** `N` Alt+Shift+F on NEW stamps N captures. On PRE it would mark weather, teeth, and pills done without doing them. Refuse counted / Task-Link batch complete on PRE/POST.
- **Two independent tags vs one nested tag.** `#gtd/pre` would look cleaner, but Tasks tags are stored as written (`['#gtd', '#context/home']` on the archive lines). A nested `#gtd/pre` is a single token and would **not** satisfy "has `#gtd` and `#pre`" unless the matcher expands parents. The Dataview engine's `tags include` also matches subtags (`#hide/x`); whole-token AND of two tags does not. Keep the two tags the request named.

### Would I take a different approach

I would still extend the shared `api.freshness.queue()` with two structural tiers and keep `]s` as the only morning chord. I would not:

- add `]g` / a gtd-only walk (two rituals; PRE is the thing that already gets skipped);
- walk `gtd_daily.md` as a file (nav jumps queue entries, not notes; Alt+Shift+F would still try to stamp);
- use trailing `^pre` / `^post` block IDs (the PROJECTS/REFERENCES identity). A task can have only one block ID, and these lines may want unique ids later. Tags compose. `#hide` is already the tag-shaped special case;
- put PRE/POST on `dash.md` or `rotten.md`;
- stamp recurring lines, or strip `repeat` so they become ordinary Ready;
- encode order as `[priority::]` or a stored rank.

The one alternative worth taking seriously: **POST last, skip ROTTEN with `]S`.** Faithful to "after any other group." Usable only because `]S` is already last-due. Worse: the closeout is hidden behind upkeep, `]S` becomes a secret handshake, and "Commitments done" fires before the checkbox that claims commitments are done. Reject it.

## Requirement adjustments

**ADJ-1. POST is a commitment-closeout tier: after REFERENCES, before ROTTEN.** Walk order becomes PRE → NEW → PROJECTS → PENDING → NEXT → RETURNED → REFERENCES → POST → ROTTEN. POST joins `FRESHNESS_FOOTER_COMMITMENT_TIERS`. "Commitments done" fires when PRE…POST are empty, including when ROTTEN remains. This is the request's parenthetical, made structural. Call it out in the ritual text so "last" means "last required," not "after upkeep."

**ADJ-2. PRE/POST default action is Tasks-complete then advance, never stamp.** Alt+Shift+F (and the matching counted-session path) on a PRE/POST cursor: run the same Tasks command the cycler uses to close a TODO so "when done" inserts tomorrow's instance, then `planReviewJump` with the just-closed key in `handled`. Alt+F without advance completes and stays. Escape / skip is plain `]s` (leave it due). Recurring stamp refusals stay. Counted `N` and Task-Link batches **refuse** on these tiers with a notice.

**ADJ-3. Exclusive ritual membership; null state/bucket; recurring exclusion otherwise unchanged.** A visible TODO with whole-token `#gtd` and `#pre` (resp. `#post`) walks only in that tier. It never also enters NEW / RETURNED / ROTTEN / PROJECTS / REFERENCES / lanes. `state` and `bucket` stay null. Dash chips, gated READY, `rotten.md`, and `note_ready` counted rows stay as they are. Recurring tasks without both tags stay out of the walk, as today. Non-recurring tasks that carry both tags *do* enter PRE/POST (the request said "any ready task," not "any recurring task") and completing them is still the action — do not put a freshness-review item in these tags.

**ADJ-4. Ritual tags bypass Today membership; they still honor future `scheduled`, `#hide`, blocked, closed, daily-note, templates, conflicts.** GTD is often the first Pomodoro. Linking a PRE habit under it would otherwise drop it out of the walk (`is_today`). Ritual checkboxes are not plan work. Future-scheduled (tomorrow's "when done" child) stays out. `#hide` stays out. Canonical `YYYY/YYYYMMDD.md` stays out. `gtd_daily.md` is an area note, not a daily note, so it is already eligible.

**ADJ-5. Within PRE and within POST, sort `(path, line)`.** That is NEW's comparator and it preserves the written order in `gtd_daily.md`: weather → teeth → pills → calendar → email → Keep → stretches. Do not sort by `due_on` or `created`; the September `scheduled` dates would scramble the ritual.

**ADJ-6. Do not tag cancelled or non-daily lines.** Open daily `[ ]` except Morning review → `#gtd #pre`. Morning review → `#gtd #post`. Leave the cancelled "Pick today" and "Weekly review" lines, and the blocked weekly prune `[?]`, untagged. Blocked is not ready and would not walk anyway.

**ADJ-7. Rewrite the Morning review line so it is a closeout, not a nested walk recipe.** Suggested body (vault edit, not evaluator): the checkbox means highlight started, CROWDED cleared, commitments walked; ROTTEN optional. Drop the inner "`]s` through NEW → …" and drop the duplicate `bob gkeep pull` (that is the PRE Keep item). Update `docs/freshness.md` §6 step 1–2: `]s` starts at PRE, Keep import happens *in* the walk, POST is the closeout, then ROTTEN.

**ADJ-8. JSON schema bump to 9.** `by_tier` gains `pre` and `post`; add `counts.pre_due` / `counts.post_due` equal to those keys; `walk = sum(by_tier)`. Additive fields with a version bump match how schema 5 added PROJECTS and schema 7 added REFERENCES. Workspace `SCHEMA_VERSION` is already 8 (live installed `bob freshness` still reported 7 on 2026-10-04 — the PATH binary lags this tree). Do not reuse `counts.due` (Ready-state due) for ritual rows.

**ADJ-9. No dash section, no chip, no config interval, no seed change.** Tiers never feed buckets (`decisions:review-walk-is-tiered`). There is no PRE interval: due means open, tagged, ready, scheduled empty-or-≤ today. `bob freshness seed` still skips recurring. Footer shows nonempty PRE / POST groups in walk order.

**ADJ-10. New decision record; do not silently edit `review-walk-is-tiered`.** That record claims "recurring, daily-note, hidden, dependency-blocked, future-scheduled, and Today-linked tasks are in no tier" and order NEW → PENDING → NEXT → RETURNED → ROTTEN (already partly superseded in docs by PROJECTS / REFERENCES). A new record extends the order and carves the ritual-tag exception. Mark the old recurring/Today sentence superseded in part. Classification stays read-time; tags here are *membership*, the way `#hide` is, not stored NEW/ROTTEN state (the alternative `ready-is-freshness-gated` rejected).

## What exists today

Verified 2026-10-04 against this workspace (`bob-cli_14`), the opened `bob-plugins` linked checkout, vault `~/bob`, and live `bob` on PATH.

| # | Fact | Evidence |
| --- | --- | --- |
| E1 | `]s` / `[s` / `[S` / `]S` → `jump-to-{next,prev,first,last}-due-task`. Same commands as Ctrl+Alt+J/K. Nav does not sort. | vault `obsidian_vimrc.md` 33–40; bob-navigation-hotkeys `planReviewJump` |
| E2 | Shared queue order is NEW → PROJECTS → PENDING → NEXT → RETURNED → REFERENCES → ROTTEN. Commitments are the first six; ROTTEN is upkeep. | `docs/freshness.md` §4 / §6; `state.rs` `Tier`; ledger-tools `FRESHNESS_TIER_ORDER`, `FRESHNESS_FOOTER_COMMITMENT_TIERS` |
| E3 | `walk_scope` / `in_scope` require `!recurring`. Stamp helpers refuse `repeat`. Recurring is S13 out of scope. | `state.rs` 308–351; `placement.rs` P13; JS `freshnessEvaluate` ~5144–5175; `docs/freshness.md` §3.5, §4 |
| E4 | `READY_QUERY` does **not** exclude recurring. Recurring TODOs with `scheduled` ≤ today are in `snapshot.ready` and then dropped by `evaluate`. | `dataview/tasks/mod.rs` `READY_QUERY`; `freshness/scan.rs` `ready`; `state.rs` `evaluate` |
| E5 | `FreshnessRow` has no `tags` field. `RichTask.tags` exists and is how `#hide` is tested (`tag == "#hide"`). | `state.rs` `FreshnessRow`; `dataview/tasks/mod.rs` `RichTask`; `seed.rs` 273 |
| E6 | `gtd_daily.md` open daily lines are all `[repeat:: every day when done]`, `#task` only, no `#gtd`/`#pre`/`#post`, no block ids. Two cancelled dailies, one blocked weekly prune. | vault `gtd_daily.md`; `bob query --tasks 'path includes gtd_daily.md'` → 11 tasks |
| E7 | Live walk 128 due: `by_tier` new 4, pending 0, projects 0, next 36, returned 1, references 10, rotten 77. No `gtd_daily.md` paths. | `bob freshness list -f json` 2026-10-04 |
| E8 | Open recurring vault-wide: **13** (9 `gtd_daily.md`, 3 `recur.md`, 1 `cash.md`). Lifting recurring globally would not flood the walk; lifting it without tags would still pull bank/meds habits into NEW. | `bob query --tasks 'is recurring'` |
| E9 | `#gtd` on 12 tasks, all done (May 2026 archive of these same habits plus a few others). `#pre` / `#post` / `#gtd/pre` / `#gtd/post`: 0. | `bob query --tasks 'tags include #…'` |
| E10 | Completing a filtered `#task` goes through the Tasks plugin command so recurrence can insert a line; cycler then stamps only if line count is unchanged (recurrence insert ⇒ no stamp). | task-status-cycler `setActiveCheckboxStatus` / `tryExecuteTasksCommand` |
| E11 | Dual evaluator: Rust `src/native/freshness/` and JS `api.freshness` in bob-ledger-tools, kept in sync under `docs/freshness.md` vectors. Footer, notices, `reviewEntryView` action hints are JS. | `docs/freshness.md` intro; ledger-tools `freshnessReviewEntryView` |
| E12 | Decision `review-walk-is-tiered` (accepted 2026-10-01): recurring in no tier; stamps stay; seed never re-runs; tiers never feed buckets/chips. Docs already added PROJECTS/REFERENCES after that record. | `sase memory read decisions:review-walk-is-tiered`; `docs/freshness.md` §4 |
| E13 | Recurring is excluded from the per-note Ready cap. `gtd_daily.md` is an `[[area]]` with 8 open dailies; if they lost `repeat` they would crowd the default cap of 5. | `is_counted_ready_row`; `note_ready`; `gtd_daily.md` frontmatter |
| E14 | Workspace freshness JSON `SCHEMA_VERSION` is 8. Live PATH `bob freshness` reported `schema_version` 7. Implement against the tree, not the older binary. | `freshness/cli.rs` 54; live list JSON |

### Live `gtd_daily.md` census (open)

| Line | Status | Repeat | Scheduled | Proposed tags |
| ---: | --- | --- | --- | --- |
| 9 | `[ ]` Check weather | every day when done | 2026-09-29 | `#gtd #pre` |
| 10 | `[ ]` Brush teeth | every day when done | 2026-09-29 | `#gtd #pre` |
| 11 | `[ ]` Take fish oil + L-tyrosine | every day when done | 2026-09-29 | `#gtd #pre` |
| 12 | `[ ]` Review Calendar + @EVENT notes | every day when done | 2026-09-29 | `#gtd #pre` |
| 13 | `[ ]` Read Email | every day when done | 2026-09-29 | `#gtd #pre` |
| 14 | `[ ]` Import inbox from Google Keep | every day when done | 2026-09-29 | `#gtd #pre` |
| 15 | `[ ]` Do morning stretches | every day when done | 2026-10-04 | `#gtd #pre` |
| 16 | `[-]` Pick today | every day when done | 2026-09-30 | none (cancelled) |
| 17 | `[-]` Weekly review | every week on Monday when done | 2026-10-05 | none |
| 18 | `[ ]` Morning review (≈10 min)… | every day when done | 2026-09-30 | `#gtd #post` |
| 19 | `[?]` Weekly prune | every week on Monday when done | 2026-10-05 | none (blocked) |

Tag placement: after `#task`, matching the 2026-05 archive (`- [ ] #task #gtd #pre Check weather …`). Trailing-suffix tags also work; body tags after `#task` are the house style.

## How the request was read

| You wrote | Read as | Why |
| --- | --- | --- |
| "two new review groups" | Walk tiers / footer groups, not `task-status-groups` (Active / Blocked / Closed) and not dash sections | The `]s` footer already calls NEW…ROTTEN "walk groups" |
| "before any other review group" | First tier, before NEW | Structural, like PROJECTS sitting before PENDING |
| "after any other review group" | Last *required* tier; ROTTEN remains optional upkeep (**ADJ-1**) | Otherwise the ROTTEN exception in the same sentence is unimplementable |
| "any ready task that has `#gtd` and `#pre`" | Whole-token AND, TODO `[ ]`, exclusive of other tiers; recurring allowed | Ready in the lane sense, not the current freshness `in_scope` sense |
| "add these tags to all of the tasks in `gtd_daily.md` that recur daily except Morning review" | The seven open daily `[ ]` lines only | Cancelled dailies and weekly lines are not that set |
| "close out each of these recurring GTD tasks as we get to them" | Tasks-complete (when-done recurrence), not Alt+F keep | Stamp is refused and would be the wrong verb |

## Implementation shape

Same dual-evaluator pattern as PROJECTS/REFERENCES. Nav still does not own membership or sort.

### Contract (`docs/freshness.md` §4 / §6 / JSON)

```text
ritual(t) = lane ready
          ∧ lane-visible (blocked / templates / conflicts / future scheduled / #hide out)
          ∧ ¬canonical daily note
          ∧ whole-token tags contain #gtd
          ∧ (whole-token #pre XOR whole-token #post)
          # Today membership is ignored (ADJ-4)
          # recurring is allowed

tier(t)   = pre   if ritual(t) ∧ #pre
          | post  if ritual(t) ∧ #post
          | (existing tracker / new / pending / next / returned / rotten,
             only when ¬ritual(t))

order     = pre → new → projects → pending → next → returned → references → post → rotten
pre/post sort = path ↑, line ↑
state/bucket for ritual rows = null
```

Both tags on one line: lint `ritual_tag_conflict`, `#pre` wins so it still surfaces. `#gtd` without `#pre`/`#post` is inert (today's archive shape).

Human list and footer: `PRE` / `POST` labels. `reviewEntryView` action hint: `Done? Alt+Shift+F complete · ]s skip`. Commitments remaining include PRE and POST.

### Code surfaces

| Surface | Change |
| --- | --- |
| `FreshnessRow` + JS row | Carry `tags: Vec<String>` (copy of `RichTask.tags`) |
| `Tier` enum / `FRESHNESS_TIER_ORDER` | `Pre` first, `Post` after `References` |
| `evaluate` / `freshnessEvaluate` | Ritual branch before trackers/NEW; recurring+Today bypass only here |
| `ByTier` / counts / CLI human | `pre`, `post`, `pre_due`, `post_due`; schema 9 |
| `queue` comparators | PRE/POST use path,line |
| ledger-tools footer, `reviewEntryView`, machine-tier allow-list | Two groups, hints, commitment set |
| nav `refreshTaskFreshness` | If cursor tier is pre/post: complete via Tasks command, then advance; refuse counted |
| nav notices / `buildReviewBoundaryNotice` | POST → ROTTEN is the "Commitments done" crossing |
| tests | New vectors in `docs/freshness.md`; Rust `state_tests`; JS `test-ledger-tools-freshness.cjs`, `test-navigation-freshness.cjs`, footer tests |
| vault `gtd_daily.md` | Tags (**ADJ-6**), rewrite Morning review (**ADJ-7**) |
| `docs/freshness.md` §6, `docs/getting-started.md`, glossary `task-freshness` | Ritual order |
| new `decisions:` record | **ADJ-10** |

`planReviewJump` algorithm unchanged. `obsidian_vimrc.md` unchanged. `dash.md` / `rotten.md` queries unchanged. `bob freshness seed` unchanged. Chezmoi config unchanged (no new interval keys).

### Phases

1. **contract-eval (bob-cli, medium).** Schema 9, tags on the row, ritual predicate, tier order, vectors (recurring+tags → PRE; recurring without tags → none; `#gtd` only → none; future scheduled → none; Today+tags → PRE; both tags → lint+PRE; POST before ROTTEN in queue).
2. **ledger-nav (bob-plugins, medium).** JS mirror, footer, complete-and-advance, counted refuse, tests. Deploy with `bob plugins sync`.
3. **vault-ritual (small).** Tags + Morning review wording + §6. Can land with phase 2; tags without evaluator are inert, evaluator without tags yields empty PRE/POST.

Do not parallelize 1 and 2. Empty PRE/POST in production for a day is fine; a JS/Rust split is not.

## Critique of alternatives

| Alternative | Why not |
| --- | --- |
| Second keymap `]g` | PRE is what already gets skipped. Two morning chords recreate the problem. |
| Open `gtd_daily.md` as a pinned first stop | Not a queue entry; Alt+Shift+F still stamps; easy to skip. Status quo. |
| File-path membership (`path is gtd_daily.md`) | Simpler, but the request wants tags so a one-off morning item in another note can join. Tags are already how `#hide` opts out. |
| `^pre` / `^post` tracker identity | One block ID per line; collides with unique ids; tags compose. |
| Nested `#gtd/pre` only | Does not satisfy two-token AND unless parent expansion is specified. Tasks stores tags as written. |
| Lift recurring exclusion for all Ready | 13 open recurring, but `recur.md` / `cash.md` would land in NEW and then ROTTEN every interval. Bank/meds are not morning review. |
| Stamp instead of complete | Refused; next occurrence would inherit `[fresh::]` if it were not. Completing *is* the confirmation. |
| POST last + `]S` skip | Secret handshake; "Commitments done" fires too early. |
| Dash PRE/POST sections | Tiers must not feed buckets; Alt+F does not stamp query rows. |
| Drop `repeat` so they become ordinary Ready | They would count toward the area ready cap (8 > 5), enter NEW then ROTTEN on a 7-day lease, and stop being daily checkboxes. |
| Store review state in tags beyond membership | `#new`/`#rotten` were rejected. `#pre`/`#post` are opt-in identity, evaluated at read time, same family as `#hide`. |

## Risks

- **Two evaluators.** Same mitigation as PROJECTS/REFERENCES: one contract, shared vectors, Rust + JS tests. Drift desyncs `]s` from `bob freshness list`.
- **Tasks cache lag after recurrence insert.** Nav already remembers handled keys after Alt+Shift+F because the Tasks cache lags stamps. Completing inserts a *new* line; the closed line must be the handled key, and tomorrow's child must stay out via future `scheduled`. Pin with a vector plus a nav test that a just-completed PRE does not reappear as NEW.
- **Completing without the Tasks command.** A raw checkbox flip skips recurrence. Always go through `obsidian-tasks-plugin`'s done command, the way the cycler does. If Tasks is missing, refuse with a notice; do not local-write.
- **Batch complete.** Mitigated by ADJ-2 refuse-counted.
- **Today-link surprise.** ADJ-4 is the mitigation. Document: do not depend on Today exclusion to hide a ritual task; untag or `#hide` it.
- **Tag leakage.** Anyone can add `#gtd #pre` to a real Ready task and the next Alt+Shift+F will *complete* it. Mitigation: exclusive tier + action hint "complete," and keep `#gtd` as the namespace guard. Do not auto-tag from agents.
- **Morning review wording drift.** If the vault line still says "then ]s through NEW…," standing on POST tells you to start the walk you are already in. ADJ-7 is load-bearing.
- **Schema 8 vs live 7.** Implement in this tree (schema 9 on top of 8). Do not assume the PATH `bob` already has REFERENCES in JSON.
- **Keep-import duplication.** Harmless if ADJ-7 drops `gkeep pull` from the POST text; harmful if both PRE Keep and POST text still say to pull.

## Recommended solution

Build **PRE and POST as structural walk tiers** on the existing `]s` / Alt+Shift+F machinery.

**Membership.** Ready `[ ]`, lane-visible, not `#hide`, not blocked, not canonical daily note, not future-scheduled, whole-token `#gtd` **and** `#pre` (PRE) or `#gtd` **and** `#post` (POST). Recurring allowed. Today-linked allowed. Exclusive of every other tier. `state`/`bucket` null.

**Order.** PRE → NEW → PROJECTS → PENDING → NEXT → RETURNED → REFERENCES → POST → ROTTEN. Within PRE/POST: path, line.

**Action.** On PRE/POST, Alt+Shift+F = Tasks-complete + advance. `]s` skips. Counted sessions refuse. Other tiers unchanged (stamp / keep / release / roll).

**Vault.** Tag the seven open daily `gtd_daily.md` lines `#gtd #pre`. Tag Morning review `#gtd #post` and rewrite it as a closeout. Leave cancelled and weekly lines alone.

**Unchanged.** Dash, chips, buckets, seed, vimrc maps, ready cap, recurring exclusion for untagged tasks, stamp refusals for recurring.

**Decision.** New accepted record that extends `review-walk-is-tiered` (order + ritual-tag exception) without rewriting that file in place.

This is a small, coherent extension of a walk that already grew PROJECTS and REFERENCES the same way. The request's instinct — put the life checklist on `]s`, close the items as you reach them, check Morning review when the required part is done — is right. The implementation has to honor the recurring/stamp contract and the commitment/upkeep split that the last two review designs already paid for.
