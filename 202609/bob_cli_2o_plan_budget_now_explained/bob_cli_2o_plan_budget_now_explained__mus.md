# bob-cli-2o: Close the Day, Tag the Week

> **Epic:** `bob-cli-2o` — *plan budget, #now, and ledger guardrails* · **Status:** CLOSED 2026-09-30 · **13/13 phases done**
> **Research date:** 2026-09-30 · **Bead:** `sase bead read bob-cli-2o -r '<why>'`

## The one-index-card version

> **Today is closed:** GTD plus at most 3 themes, ~10 Task Links. The first theme is the highlight.
> **This week is `#now`:** at most 15 tagged tasks. Dropping a link from today never loses the work,
> because `#now` keeps it in view. **Everything else is READY or deferred with a P-level.**

The tools make this rule **visible** everywhere Bryan already looks, and **cheap to follow** with a few
new gestures. They never rewrite the plan: nothing is pruned, deferred, or migrated behind his back.

## Why this epic exists

The prior research (`research:202609/pomodoro_closed_day_now_tag_automation/…`, plus the
`#now`-vs-`[/]` follow-up) diagnosed a **status-lock trap**: removing a Task Link from the daily ledger
demoted the task, and nothing else remembered it mattered — so everything stayed linked and statuses
inflated (≈50 `[/]`, ≈25 `[*]`, roughly a 15-day queue at ~5 closures/day). `[/]` had stopped telling
the truth about what was actually worked on.

The fix separates **memory** from **status**:

| | `#now` (new) | `[/]` In Progress (existing) |
|---|---|---|
| Kind | A tag **you** set and clear — "I've committed to this for the week" | A status the **tools** derive — "I worked on this in the last day or so" |
| Lifespan | ~a week, until the Monday review | ~a day of grace after its last ledger link, then hooks reset it |
| Tie to today | None by design — drop the link, keep the tag | Tight — it exists because of recent ledger links |
| Cap | ≤ 15 (`NOW n/15`, red over cap) | None (target: ≤ ~15 `[/]`+`[*]` combined) |

A falling WIP chip becomes a **success signal**, not lost work. Phase 2 of the report (conditional on a
two-week trial) stays out of scope; `stale_link` linting was deliberately deferred.

## What was built — four ideas, thirteen phases

### 1. One definition, many surfaces (the plan budget)

`docs/plan.md` is the authoritative spec; the Rust engine (`src/native/plan_budget/`) implements it and
`bob-ledger-tools` mirrors it in JavaScript — every other surface calls one of the two. Both test
against the same 7 conformance vectors.

The ledger is today's daily note from `## Pomodoros…` to the next `## ` heading (fences skipped).
Only **open** entries count; components in `plan.exempt` (default `[GTD]`) are never themes; links are
distinct `(target, block_id)` pairs, with struck/fenced links excluded. Caps default to **3 themes /
10 links / 15 NOW**, all configurable via an optional `plan:` block in `~/.config/bob/config.yml`
(invalid config never breaks a surface — `bob plan` exits 2, everything else falls back to defaults
with one warning).

| Surface | What Bryan sees |
|---|---|
| `bob plan` (new, read-only, human+JSON) | Full report: meters, themes (★ highlight, ▶ running), lints with hints |
| Daily note ` ```bob-plan ` block | Live `PLAN 3/3 · 7/10` + `NOW 12/15`, star, lints |
| `dash.md` | PLAN + NOW chips (red over cap), `### NOW Tasks` section |
| tmux status | `plan 3/3 · 7/10`, reverse video when over |
| `bob task-status-hooks` | `plan_budget` JSON block + one human meter line (pre-cleanup snapshot) |
| `bob capture` / Mac Capture | Before→after meter, cap warnings, destination row (`→ GOALS · next up`), optional strict refusal |
| Obsidian Notices | `· plan 3/3 · 11/10 🔴` on link changes; `#now added · NOW 13/15` on toggle |

Lints (`duplicate_open_pomodoro_name`, `inventory_label_open`, `subheading_in_pomodoros`,
`plan_theme/link_cap_exceeded`, `now_cap_exceeded`) carry stable codes and 1-based lines.
Phases: `.1` core + `bob plan`, `.3` hooks/tmux, `.4` capture warnings + strict + destination roles,
`.7` ledger-tools view + versioned API, `.10` link Notices, `.11` Mac meter/destination/cap badge,
`.13` rollout (chips, template, chezmoi config, reinstall, end-to-end check).

### 2. `#now`: this week's bets, everywhere

- **Vault first** (`.2`): NOW chip + `### NOW Tasks` section on `dash.md`; the three
  migrate/review chores in `gtd_daily.md` collapsed into one daily pick + one weekly review.
- **Capture** (`.6`): `#now` accepted after the route marker (`now_tag` span, `#n`/`#no` completion),
  and the `^` picker lists Ready `#now` tasks flagged `now`. `#now` is never a Next source.
- **Obsidian** (`.9`): counted `Toggle #now` (Alt+N) + a `#now` row in the Ctrl+Shift+P picker, working
  on task lines *and* Task Link lines, with a NOW-count Notice.
- **Mac** (`.12`): mint `now_tag` rendering, `#now` completion row, NOW badges on pickers and close rows.

### 3. Drop, don't drag: the `~<K>` close outcome

Close grammar grew to `=x[<N>][!<M>][~<K>]` (`.5`): dropped links are **removed** from the closed
session — not carried, never started, no Work Log — with `drop` JSON, `dropped` outcome/role, a `now`
flag on close rows, and a human `Dropped` summary. Paired with `.8` (Ctrl+Shift+P edits the task
*behind* a Task Link, counted across siblings) and `.4`'s destination roles
(`current / next_up / named / created`), the ledger itself becomes the editing surface:
drop, defer, and tag without leaving it. Strict mode (`plan.strict`) atomically refuses only *new
non-start themes* past the cap — starts are never refused. Mac renders all of it tolerantly (`.12`).

### 4. Guardrails, not automation

Warnings fire only when a batch **grows** past a cap; the multi-open-timed error now names entries and
suggests `=x`; links/unlinks warn but never refuse; yesterday's note is never written; no cron migrates
anything. Rollout's live check told the story: `PLAN 19/3 themes · 73/10 links` — the very first run
showed *how far over* the day was, which is the point.

## Verification snapshot

- `bob plan` is live and read-only (observed: `PLAN 0/3 themes · 0/10 links NOW 0/15`, exit 0, no daily
  note yet — headers degrade gracefully, NOW still reported).
- Phase notes record green suites at each landing (`cargo test` ~1267 lib + ~596 cli, `npm test`
  ~794 pass, `npm run validate` 6/6, macOS CI green on `.11`/`.12`, real-`bob` fixtures byte-identical).
- Closeout stitch `25c1b2f` (`plan_budget_land_closeout`) isolated config, fixed ledger parity and
  capture guards, aligned the three guides; follow-up docs commit `cd355e6`.

## Known loose ends (all triaged on the epic)

- **Clippy gate red on the clean base** (`pomodoro_name.rs:808` `|| true`, deny) — pre-existing, not
  this epic's; routed to active epic `bob-cli-28`.
- **System TZ `Etc/UTC` flips bob's day at 20:00 EDT** (`env.rs` uses `Local::now`) — new bug bead
  `bob-cli-2q`.
- One genuine new clippy warning from the epic (`capture_complete.rs:1372`) was fixed in the closeout;
  `capture_complete.rs` at ~3790 lines was noted but left alone beyond splitting what this epic pushed
  past ~1500 lines.

## Bottom line

Thirteen phases across four repos plus the vault, landed in about nine hours: a **shared, capped,
visible daily plan**; a **human-owned weekly `#now` tag** that frees `[/]` to tell the truth; and
**ledger-native gestures** (drop, destination, toggle) that make the disciplined thing the easy thing —
with nothing ever rewriting the plan behind Bryan's back.
