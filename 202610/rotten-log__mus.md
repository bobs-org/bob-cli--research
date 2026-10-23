# Rotten log: research and recommendation

Researcher: mus (swarm 55). Independent report; no peer reports consulted.

Request: add a "rotten log" (with a glossary entry) that works like the work
log, except the optional-entry prompt fires on a rotten-task refresh via
`<alt+f>` / `<ctrl+alt+f>` (e.g. in the GTD morning review). Goal: a visual
indication plus an audit trail showing how many times, when, and why a task
was manually refreshed.

Verdict up front: yes, with adjustments — build an optional, per-task
`🥀 **ROTTEN LOG**` as a third managed log kind that mirrors the work log's
shape and the Pending work-log prompt's Enter/Esc semantics, fired only on
Ready rotten/tickler keeps, skipped when the approved-decay card owns the
gesture. Do not add a lifetime counter field, do not reuse the work log, and
do not prompt on any other lane or tier.

## 1. How the work log works today (the template to copy)

### Marker, entries, placement

- Marker is a task-local direct child: `🛠️ **WORK LOG**`, newest-first
  dated entries shaped `*YYYY-MM-DD* — summary` underneath it.
- Glossary (`docs/reference/glossary.md`, `### Work Log`): "task-local
  history of work performed"; Ctrl+Shift+Enter unlink prepends the nonblank
  summary, blank leaves the log untouched; Alt+N release prompts for the
  same optional summary.
- Rust writer: `src/native/capture_work_log.rs` (`write_work_log_group`,
  `append_entry_node`, `WorkLogNode` / `WorkLogCursor` / `WorkLogWrite`).
  Entry text is `*{date}* — {body}`; descendants re-indented below.
- Rust recognition: `src/native/capture/sub_bullet.rs`
  (`parse_managed_task_log_marker`, `MANAGED_TASK_LOG_LABELS`,
  `SCHEDULE_LOG_EMOJI` / `WORK_LOG_EMOJI`, `ManagedTaskLogKind::Schedule |
  Work`). A present emoji must agree with the label, so
  `🗓️ **WORK LOG**` is not a marker. Assembly vectors pin this in
  `src/native/capture/tests/assembly.rs`.
- Closed registry: `docs/reference/vault-format.md` ("Other machine-owned
  direct children (closed registry)") and `docs/task-dependencies.md §2.4`
  ("Managed child lines"): CANCEL LOG first-direct-child; DEPENDS ON /
  BLOCKS / Sub-projects / LINKS slots; SCHEDULE LOG and WORK LOG "after
  the managed-dependency lines (and Sub-projects on `^prj`)". Every row
  lists the recognisers that must reject every other row; a new log kind
  must extend all of them plus §11.8 MC vectors.
- Scanners ignore log lines: Task Link and Pomodoro scanners, section
  titles, Depends-On / BLOCKS / Sub-projects / Schedule / Work / Cancel
  parsers, tree-close and strike/restore, R8 legacy-child. Capture grammar
  likewise never claims log bullets (cf. `bare_close_suppresses_…`,
  `work_log_bullet_lines_request_no_marker_completion`,
  `plus_parent_picker_does_not_claim_operators_or_work_log_text` tests).
- Projection: `src/native/highlights_ref/note_snapshot/transclusion.rs`
  (counts schedule/work logs, condenses full logs), `visibility.rs`
  (`LogKind::Schedule | Work`, cancel-log hiding, `log_rows`), `view.rs`
  (`summary.work_logs`), `create.rs` (`logs: {} schedule logs · {}
  work logs`, snapshot PDFs condense logs unless `-C`).

### The Pending keep prompt (the exact interaction to mirror)

- Contract (`docs/freshness.md §5`, "Before Alt+F …"): before Alt+F or
  Ctrl+Alt+F stamps a validated Pending (`[/]`) target, ask once for an
  optional Work Log summary. In a counted or Task Link batch only the
  Pending targets share the summary; every other accepted target still
  refreshes. Enter on empty still keeps with no entry; Escape cancels the
  refresh (task stays due, Ctrl+Alt+F does not advance).
- Plugin implementation (linked repo `bob-plugins`, read via `sase repo
  open bob-plugins`): `planFreshStampBatchWithWorkLogs` in
  `plugins/bob-navigation-hotkeys/src/480-review-jump-and-nav-api.js`
  (stamp first, then prepend one entry per stamped pre-write Pending
  task via `insertLaneWorkLogEntry`, marker ownership / indentation /
  line-ending preserving); prompt/modals in `190-summary-modals.js`,
  `370-picker-schedule-work-log.js`, `525-plugin-task-link-lane.js`;
  leaf formatting in `030-bullet-blocks-and-logs.js`
  (`formatScheduleLogParentBullet`, `formatScheduleLogEntryText`,
  `parseManagedTaskLogParentBullet`, `findScheduleLogParent`,
  `planScheduleLogEntry`, cancel-log analogues).
- Sibling prompts with the same shape: Move-to-Next (`docs/plan.md`, "The
  Move to Next prompt", `*YYYY-MM-DD* — summary`, `No work-log entry will
  be added.`, newest-first, `· logged` notice chip) and the
  recommendation-batch schedule/work-log prompt (`docs/projects.md`,
  "Only explicit targets qualify", shared summary to qualifying
  Pending/Next targets, `::` warns as inline field).
- Schedule-log entry shape for contrast: `*<from> → <to>* — <reason>`
  (`src/native/capture_schedule_log.rs`, `MARKER_TEXT =
  "🗓️ **SCHEDULE LOG**"`, `entry_text`, `plan`, `plan_entry_insertion`;
  JS `formatScheduleLogEntryText`). Cancel-log shape:
  `*YYYY-MM-DD* — reason` under `❌ **CANCEL LOG**` (JS
  `formatCancelLogEntryText`; Rust `is_cancel_log_line`,
  `reconcile/fields.rs`, `task_dependencies/blocks.rs`).

## 2. Where rotten refreshes live (what the prompt must hook)

- `docs/freshness.md` is the contract both sides cite. Rust:
  `src/native/freshness/` (`placement.rs`, `state.rs`, `cli.rs`,
  `scan.rs`, `seed.rs`) plus `src/native/config/freshness.rs`. JS mirror:
  `api.freshness` in bob-ledger-tools (top-level api v3, freshness
  namespace v12 with `recurringTier` and `markUnblockedLine`).
- Keymaps: Alt+F confirms and stays (the one stay answer); Ctrl+Alt+F
  confirms and advances exactly once (`docs/develop/decisions.md`,
  `docs/freshness.md §6`, `docs/concepts/freshness-and-the-review-walk.md`).
  Both stamp through `api.freshness.keepLine` (sole increment helper,
  namespace v5+); nav/freshness call sites are pinned in the §5
  surface table.
- Eligibility for counting is narrow (§2a): exact due-Ready
  ROTTEN/TICKLER row (pre-write queue holds exactly one row with
  `path/line/originalMarkdown/lane==='ready'/tier∈{rotten,tickler}`);
  everything else (NEW, FRESH/early, Pending, Next, Blocked,
  Today-linked, PROJECTS, excluded, unresolved cache) stamps uncounted
  and preserves the streak. Same-day repeat preserves; every other human
  stamp clears; close/cancel preserves on the closed line; automation,
  hooks, randomize, seed neither increment nor reset; recurring and
  closed refused; PROJECTS trackers never decide; dependency capture
  (`&`) is a generic clearing stamp; unblock-tickler keeps
  (`returned_by: unblocked`) stamp `[fresh:: today]`, clear
  `[unblocked::]`, leave `[keeps::]` unchanged, never open the card.
- `[keeps:: N]` is a streak, not a lifetime counter (§2a, decision
  `rotten-keeps-use-priority-decay`): 1–999, absence = 0, writers omit
  zero, saturates at 999, first-valid read, canonical placement after
  `fresh`/`refresh`. Do not introduce a second lifetime counter or
  alias — the record explicitly rejects it, with no backfill (seeded /
  captured / old `fresh` stamps are not evidence of keeps). Sync may lose
  an increment; caches under-count; hand edits stay unobserved.
- At the configured limit (`freshness.decay.keeps`, default 3; `false`
  counts/shows but never asks) a single Alt+F / Ctrl+Alt+F on an exact
  due at-limit target opens the explicit consent card (Not now, Less
  often, Reword, Drop, Keep) and writes nothing; counted and Task Link
  sessions skip those targets (`N needs a decision`) without changing
  fresh/count. Card outcomes reuse existing writers with `· kept N×`
  tails (priority/schedule/cancel/work logs; Keep just counts again).
  Available immediately on compatible plugins (namespace v6, card
  capability v2); mixed-version sessions keep counting with
  counting-only wording. `docs/projects.md` ("Approved-decay decision
  planner") owns the planner; `keepLine` failing / pre-v5 falls back to
  the uncounted stamper.
- Review ritual (§6): tiers PRE → NEW → PROJECTS → PENDING → NEXT →
  RECURRING → TICKLER → ROTTEN → POST; only due tasks walk; Alt+F stays,
  answers advance; `]s` skips; `<C-o>` returns. ROTTEN is optional
  upkeep to 0, the budget, or quitting.

## 3. Proposed shape: `🥀 **ROTTEN LOG**`

- Marker: `🥀 **ROTTEN LOG**` (wilted flower; visually distinct from
  🛠️ / 🗓️ / ❌; label uppercase with legacy `Rotten log` alias,
  mirroring the existing bilingual `SCHEDULE LOG` / `Schedule log` and
  `WORK LOG` / `Work log` pairs). Alternatives: 🪦 (funereal, reads as
  dead not kept), 📜 (collides with reference/reading metaphors), 🕰️
  (reads as scheduled). If Bryan dislikes 🥀, any emoji the plugin and
  Rust agree on works — the two sides must add the same emoji+label
  pair, since an emoji that disagrees with the label is not a marker.
- Entries: work-log shape, `*YYYY-MM-DD* — reason`, newest-first
  prepend under the task's direct ROTTEN LOG child. Rationale: a keep
  reason is free text ("still waiting on X", "revisit after launch"),
  not a date transition, so the schedule-log `*from → to*` shape does
  not fit; the work-log shape keeps one entry grammar for both
  reviewers and parsers. Whitespace normalized, Markdown preserved,
  `::` warns as a possible inline field (same rule as the other log
  prompts).
- Blank means "keep without logging" (stamp still written); Escape
  means "cancel the whole gesture" (nothing written, task stays due,
  Ctrl+Alt+F does not advance). This is exactly the Pending work-log
  contract and must not be renegotiated per log kind.
- Slot: direct child of the task, created after the managed-dependency
  lines (and Sub-projects on `^prj`), alongside SCHEDULE/WORK LOG. Pin
  the relative order explicitly (recommendation: SCHEDULE, then WORK,
  then ROTTEN last — a new marker always appends as the last direct
  child; existing markers are reused in place). Never disturb the
  first-child CANCEL LOG or the Depends-On slot
  (first, or second after Cancel Log).
- No new task-line field. The count question is already answered by
  `[keeps::]` pips plus log length; a `[refreshes::]` / lifetime field
  would contradict the "no second lifetime counter" rule and needs a
  new decision record to reopen. The log is the audit; keeps stays the
  streak.

## 4. Touch list (both repos, plus docs)

Rust (`bob-cli`, this checkout):

- `src/native/capture/sub_bullet.rs`: new emoji constant, new
  `("ROTTEN LOG", Rotten)` + `("Rotten log", Rotten)` label pair,
  `ManagedTaskLogKind::Rotten`, emoji-agreement arm in
  `parse_managed_task_log_marker`. Extend `assembly.rs` vectors.
- Every closed-registry recogniser must reject the new marker: Task
  Link / Pomodoro scanners, section titles, Depends-On, BLOCKS,
  Sub-projects, LINKS / LINKED FROM, Schedule / Work / Cancel parsers,
  tree-close / strike-restore, R8 legacy-child; `first_direct_managed_
  log_start` and `nearest_shallower_list_item_parent` behavior follows
  the existing kinds. Capture grammar tests need rotten-log analogues
  of the work-log "never claims log text" cases.
- `highlights_ref/note_snapshot/`: `transclusion.rs` (count + condense),
  `visibility.rs` (`LogKind::Rotten`, `log_rows`, open-task hiding
  rules), `view.rs` (summary count), `create.rs` (condense wording,
  `logs:` line). Decide whether snapshots say `N rotten logs` and
  whether `-C` restores them, mirroring work logs.
- `freshness/` needs no new writer: Rust reads/clears/reports keeps and
  must keep never incrementing; the seed preserve-mode exception stays
  the only Rust path that stamps while keeping a streak. Optional:
  expose a rotten-log count in `bob freshness` JSON — nice, not
  required. Per `cli_rules.md`, do not add a subcommand under
  `bob capture`, and no new subcommand is needed at all.

Plugins (`bob-plugins`, linked repo):

- `010-requires-and-config.js`: `ROTTEN_LOG_EMOJI / LABEL /
  MARKER_TEXT / PARENT_RE / ENTRY_RE`, `MANAGED_TASK_LOG_KIND_ROTTEN`;
  extend `parseManagedTaskLogParentBullet` (emoji-agreement parity).
- `030-bullet-blocks-and-logs.js`: `formatRottenLogParentBullet`,
  `formatRottenLogEntryText/Bullet`, `parseRottenLogParentBullet`,
  `findRottenLogParent`, `getRottenLogEntryIndent`,
  `planRottenLogEntry` (prepend-or-create, same guards:
  task-out-of-range, not-list-item, empty-reason), `insertRottenLogEntry`.
- Refresh path: a `planFreshStampBatchWithRottenLogs` analogue of
  `planFreshStampBatchWithWorkLogs` (`480-…`), wired into the
  Alt+F / Ctrl+Alt+F flow (`530-…`, `470-…`, `536-…`) and the counted /
  Task Link batch paths (`360-…`, `525-…`). Prompt copy mirrors the
  Move-to-Next modal (`190-…`, `196-…`): task or `N tasks`, optional
  `Refresh reason (optional)`, live preview (`🥀 **ROTTEN LOG**` /
  `*YYYY-MM-DD* — reason` vs `No rotten-log entry will be added.`).
- Mac client: nothing to change (thin client — `decisions:
  mac-capture-is-a-thin-client`). It renders what bob returns and
  submits one `bob capture` call; the new marker must simply survive
  its preview as inert text.

Docs and memory (per `docs.md` routing: behavior change → contract /
  reference + only the guide steps made incorrect; hotkey → plugin
  reference; decision → decision record):

- New glossary entry (see §6 draft) in `docs/reference/glossary.md`;
  closed-registry rows in `docs/reference/vault-format.md` and
  `docs/task-dependencies.md §2.4` + recogniser columns + §11.8 MC
  vectors; `docs/freshness.md §§5–6` (prompt rule, batch rule,
  card-exclusion, ritual answer list); plugin hotkey reference for
  Alt+F / Ctrl+Alt+F; `docs/projects.md` decay-planner note that card
  outcomes do not also write rotten entries. Run `just docs-check`
  (and `just docs-gen` if any CLI help changes — none expected).
- Plan shape follows the repo's plan conventions, and per the release
  decision (`bob-cli-releases-ride-a-daily-train`) agents never edit
  `Cargo.toml` or `CHANGELOG.md`.

## 5. Critique: is this a good idea?

Good core, real costs. The goal is legitimate: `[keeps::]` answers "how
many consecutive keeps" but deliberately cannot answer "when and why" —
it clears on any non-keep stamp, ignores unblock-tickler keeps, and is
documented as unobserved under hand edits and sync conflicts. A
task-local dated reason log fills exactly that gap, and the work /
schedule / cancel logs prove the pattern scales through scanners,
projections, and the review walk.

Costs and risks, honestly:

1. Cross-repo surface. A "small log" touches the closed registry in two
   languages plus vectors, snapshots, and four doc pages. That is the
   dominant cost — not the prompt itself. Skipping any recogniser
   reintroduces the exact bug class the registry exists to prevent
   (a log line parsed as a Task Link, section, or dependency).
2. Prompt fatigue. ROTTEN upkeep already competes with the ~25 lane
   decisions; a modal on every rotten keep taxes the fastest ritual.
   The blank-Enter escape hatch is load-bearing: the stamp must never
   wait on prose. Reviewer habit will be "Enter, Enter" on most keeps,
   which yields date-only entries — fine, but be honest that many
   entries will carry no "why".
3. Two counts that can disagree. `[keeps::]` (streak, clears, saturates,
   unobserved writes) vs log length (lifetime, append-only, blank-skips
   leave gaps). Users will ask which is "the" refresh count. The docs
   must say: keeps = consecutive keeps; log = dated audit, blanks
   omitted, no backfill. Never sum them.
4. Clutter. A task kept 10× gains 10 entries under a third marker
   alongside schedule/work history. Newest-first + snapshot condensing
   contain it, but long-lived backlog tasks will grow tall. No cap is
   the right default (work logs are uncapped too), but call it out.
5. No backfill. Old keeps are not evidence of keeps (same rule as the
   streak). The log starts empty on day one; `keeps:: 3` with zero
   entries is expected, not a bug.
6. Mixed-version rendering. Older plugins / mobile see an unknown
   marker as a plain bullet. Safe (no parse, no write), slightly ugly
   until upgrades land.

Adjustments I would make to the request as stated:

- (a) Fire only on Ready rotten/tickler keeps — never on Pending
  (already work-log-prompted), Next, NEW, PROJECTS, recurring, closed,
  or uncounted stamps. A Pending rotten-adjacent task keeps its Work
  Log prompt; do not stack two prompts on one keystroke.
- (b) Blank Enter keeps without an entry; Esc cancels the gesture.
  Non-negotiable; mirrors the Pending contract byte for byte.
- (c) One shared prompt per batch (counted / Task Link multi-select):
  the same reason is prepended to every stamped rotten target, exactly
  like the shared Pending summary. Per-task reasons in a batch are
  out of scope.
- (d) Never prompt when the decision card owns the gesture. At-limit
  Alt+F writes nothing and asks the card question; card outcomes log
  through their own writers (Less often → SCHEDULE LOG, Drop → CANCEL
  LOG, Reword → generic stamp). A rotten entry there would double-log
  the same decision.
- (e) No config knob at launch. `freshness.decay: false` already
  suppresses the card; the log prompt needs no interval, limit, or
  budget — it rides the existing due computation. Add
  `freshness.rotten_log: false` only if the ritual proves too chatty;
  fewer knobs until then. (If a kill-switch is wanted on day one,
  default it on.)
- (f) Keep the entry date-only-friendly: prefill nothing, accept empty,
  still write `*today* — reason` only when nonblank. Do not mint
  `*today* — kept` filler — filler destroys the "why" signal the log
  exists for.
- (g) Visual indication comes free: marker presence + entry count +
  existing keeps pips + a `· logged` notice chip on write (mirror the
  Move-to-Next notice). Do not add color, tags, fields, or dashboard
  chips — freshness never changes lanes/Today/schedule/priority, and
  tags/fields would violate the no-review-state-in-tags rule.

Alternatives considered and rejected:

- Reuse `🛠️ **WORK LOG**` for keep reasons. Cheapest, but pollutes
  "work performed" semantics, corrupts work-log counts in snapshots
  and `· logged` notices, and mixes "did X" with "still true because
  Y" in one timeline. Reject.
- Lifetime `[refreshes:: N]` / `[refresh_count::]` field. Directly
  contradicts the accepted "no second lifetime counter" rule; needs a
  new decision record with backfill, saturation, and sync-loss answers
  the log sidesteps by being append-only prose. Reject.
- Auto-log date-only entries with no prompt. Removes fatigue but also
  removes the "why" — the one thing keeps cannot supply — while adding
  all the registry cost. If fatigue wins, prefer blank-Enter habit
  over silent writes. Reject as default; acceptable as a per-task
  opt-out the blank already provides.
- Journal-in-daily-note instead of per-task log. Loses task-locality;
  the morning review asks "why is this still true", answered best on
  the task. Reject.
- Do nothing; rely on keeps pips. Zero cost and possibly sufficient if
  Bryan only wants "how many times". But it concedes "when and why"
  permanently. Viable fallback, not the recommendation.

## 6. Draft glossary entry (proposed)

```markdown
### Rotten Log {#rotten-log}

A task-local history of manual refreshes, stored as a `🥀 **ROTTEN LOG**`
direct child with newest-first `*YYYY-MM-DD* — reason` sub-bullets. When
Alt+F / Ctrl+Alt+F stamps a due Ready rotten or tickler task, Bob asks once
for an optional refresh reason; a blank summary still keeps the task with no
entry, while Escape cancels the refresh. Unblock-tickler keeps, Pending
Work Log prompts, and approved-decay card gestures never write one.
```

## 7. Recommended solution

1. Accept the feature with the adjustments in §5(a)–(g): new marker
   `🥀 **ROTTEN LOG**`, work-log entry shape, prompt only on Ready
   rotten/tickler keeps, blank-Enter keeps, Esc cancels, one shared batch
   prompt, card gestures excluded, no new field or config.
2. Land in this order: (i) glossary + decision-record amendment noting
   the log complements but does not replace `[keeps::]`; (ii)
   closed-registry recognition in Rust + JS with scanner-rejection
   vectors; (iii) prompt + prepend-or-create writer on the Alt+F /
   Ctrl+Alt+F path with batch + Esc semantics; (iv) snapshot
   count/condense + `· logged` notice; (v) docs (`freshness.md §§5–6`,
   `vault-format.md`, `task-dependencies.md §2.4 + §11.8`, plugin
   reference) with `just docs-check` green.
3. Explicit non-goals: no backfill, no cap, no per-task opt-out marker
   beyond blank-Enter, no dashboard chips, no Mac-client changes, no
   `bob freshness` subcommand, no `Cargo.toml` / `CHANGELOG.md` edits.
4. Success looks like: a rotten keep with a reason leaves
   `[fresh:: today]`, an incremented (or card-deferred) `[keeps::]`,
   and one prepended `*today* — reason` entry; a blank keep leaves only
   the stamp; Esc leaves the task due; the walk, Today, lanes,
   schedule, and priority are unchanged; old checkouts render the new
   marker as inert text.

