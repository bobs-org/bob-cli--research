# Close the day, tag the week

What epic **bob-cli-2o** implemented, and why.

| | |
| --- | --- |
| **Bead** | [`bob-cli-2o`](https://github.com/bobs-org/bob-cli--beads/blob/main/pages/bob-cli-2o/README.md) · closed 2026-09-30 03:28 UTC |
| **Plan** | [`plan:202609/pomodoro_plan_budget_now_tag.md`](https://github.com/bobs-org/bob-cli--plans/blob/main/202609/pomodoro_plan_budget_now_tag.md) |
| **Closeout** | [`plan:202609/plan_budget_land_closeout.md`](https://github.com/bobs-org/bob-cli--plans/blob/main/202609/plan_budget_land_closeout.md) |
| **Title** | Close the day, tag the week: plan budget, `#now`, and ledger guardrails |
| **Span** | 13 phases, ~11 hours, four surfaces (bob-cli, bob-plugins, Bob Mac Capture, vault) |
| **Researcher** | grk · 2026-09-30 |

---

## The rule, on one card

> **Today is closed:** GTD plus at most 3 themes. The first open non-exempt Pomodoro is the highlight. Yesterday is history; nothing is copied forward by default.
>
> **This week is `#now`:** at most 15 tasks, tagged by hand. Drop a Task Link from today and the tag still keeps the task on the dash.
>
> **Everything else is READY (next) or a P-level (later).**

The tools make that rule **visible** at every place Bryan already looks, and **cheap to follow** with a few new gestures. They never rewrite the plan: no cron prunes, defers, or migrates, and yesterday's note stays read-only.

`docs/plan.md` is the authoritative definition. One Rust engine implements it (`src/native/plan_budget/`). bob-ledger-tools mirrors it in JavaScript. Every other surface calls one of those two.

---

## Why this epic existed

The prior research (`research:202609/pomodoro_closed_day_now_tag_automation` and `research:202609/now_tag_vs_in_progress_status.md`) measured a ledger that had become four jobs at once: capture inbox, backlog, status source, and today's plan.

| Measurement (2026-09-29) | What it meant |
| --- | --- |
| Median **3** planned themes actually worked per day, whether 12, 15, or 22 were open | The cap matches throughput |
| ~**50** In Progress `[/]` and ~**25** Next `[*]` | Status inflation from linking everything |
| 46 of 80 queued links idle ≥ 7 days | The open list was a hoard |
| Daily "Migrate unfinished…" copied the pile forward | End-of-day files looked clean; the queue survived as status |
| Unlinking a task demoted it, with nothing else remembering it | The *status-lock trap*: dropping work felt like losing it |

`[/]` is a **footprint** the tools derive from the ledger ("I worked on this recently"). `#now` is a **promise** only Bryan sets ("I have bet on this for the week"). The epic adds the promise so the footprint can decay honestly.

The two-week trial of the closed-day rule started **2026-09-30**. Phase 2 of the research (staleness lint, stats, a "close day" command) waits on that trial.

Rollout's own end-to-end check, against `20260929.md`, still showed the old pile live: **PLAN 19/3 themes · 73/10 links**, NOW 0/15, tmux reverse-video. The budget is already telling the truth.

---

## What shipped, by surface

```
                    ┌──────────── docs/plan.md ────────────┐
                    │  Rust engine     JS mirror (API v1)  │
                    └──────┬──────────────────────┬────────┘
           bob plan · capture · hooks · tmux     dash · bob-plan · Notices
                           │
              Bob Mac Capture (tolerant decode)
```

### bob-cli — one definition, three new contracts

| Command / path | What Bryan sees |
| --- | --- |
| `bob plan` / `bob plan -f json` | Full report: PLAN and NOW meters, ★ highlight, ▶ running, lints with stable codes. Read-only. Missing daily note still prints NOW and exits 0. |
| `bob task-status-hooks` | A `plan_budget` JSON object and one human meter line. Never writes, never changes the exit code. The meter is the ledger *before* sync cleanup. |
| `bob tmux-pomodoro` | Suffix `plan T/Tc · L/Lc`, reverse video when over. Script fallback stays budget-less. |
| `bob capture` | Before→after budget when today's Pomodoros section changes; cap warnings only when a count *grows* past a cap; destination `role` (`current` / `next_up` / `named` / `created`). |
| `plan.strict: true` | Atomic refusal of a **new named theme past the cap** that is *not* a session start. Starts (`=`, `#NAME=`, link starts) always go through. Failure code `plan_theme_cap_exceeded`. |
| `=x[<N>][!<M>][~<K>]` | New **drop** outcome: the link leaves the closed session, is not carried, is not started. `#now` keeps it in view. |
| Trailing `#now` | First-class tag on new task text. `now_tag` span and completion. The `^` picker lists Ready `#now` tasks after Next. |

Default caps, from `~/.config/bob/config.yml` (optional `plan:` block):

```yaml
plan:
  max_themes: 3
  max_links: 10
  max_now: 15
  strict: false
  exempt: [GTD]
  inventory_labels: [LATER, MISC, NEW FEATURES, SASE]
```

A missing file or block is those defaults. An invalid block: `bob plan` exits 2; every other surface falls back to the defaults and says so once. Capture, hooks, tmux, and keymaps keep working.

### Obsidian plugins — live chips, ledger gestures

| Plugin | Version | Gesture |
| --- | --- | --- |
| **bob-ledger-tools** | 1.5.0 | ```` ```bob-plan ```` block (PLAN + NOW chips, ★ themes, lints). Public `api` `{version:1, caps, planBudget, nowBudget}` for the dash and the other plugins. |
| **bob-navigation-hotkeys** | 1.38.0 → 1.39.0 | **Ctrl+Shift+P** on a dedicated Task Link bullet edits the *linked* task (counted `N<…>` covers sibling links). **Alt+N** and a pinned `#now` picker row toggle the tag on task lines and Task Links. |
| **block-id-prompt** | bumped | Ctrl+Shift+Enter Notices append ` · plan T/Tc · L/Lc`, with 🔴 when over. Warns only. |

Link-picker is the enabler for triaging *from* the daily note: future `scheduled` still marks the task Blocked and prunes its links from today's open Pomodoros.

### Bob Mac Capture — the same JSON, decoded tolerantly

- Destination row (`→ GOALS · next up`, `→ running GOALS 0945–1015`, `→ new Pomodoro BOB`).
- Themes / Links capsules with `+1 BOB` delta chips and orange warning captions.
- Red `4/3` badge on create-Pomodoro completion rows; strict-refusal hint on `plan_theme_cap_exceeded`.
- Dropped close rows (struck, dimmed, "stays in NOW"); mint `#now` span; NOW badges on active-task and close rows.

An older `bob` without the new fields still renders. macOS CI green on `b020df7`.

### Vault and config — the trial could start the same evening

- `dash.md`: purple **NOW** chip first in the bar, cyan **PLAN** chip after it (API, with inline 15 / hard-coded fallback), `### NOW Tasks` above WIP.
- `_templates/daily.md` and `20260929.md`: empty ```` ```bob-plan ```` block above `## Pomodoros`.
- `gtd_daily.md`: the three migrate/review chores cancelled; two new chores — **Pick today** (daily) and **Weekly review** (Mondays).
- chezmoi `plan:` block deployed to `~/.config/bob/config.yml`.
- `bob` reinstalled on apollo; plugins synced.

---

## Close outcomes, side by side

The drop outcome is the gesture the old close grammar was missing. A session close can now shrink the day.

| Outcome | 🍅 in the closed entry | Carried forward | Task effect |
| --- | --- | --- | --- |
| in progress (`N`, or the ledger default) | yes | yes | started `[/]` |
| deferred | removed | yes | none |
| complete (`!M`) | embedded | no | closed |
| **dropped (`~K`)** | **removed** | **no** | **none** — next hooks run demotes Next → Ready; `#now` keeps it in view |

Human close output lists dropped rows (`dropped 4 [[sase#^x]] · stays in NOW`) and a `Dropped 4, 5` summary.

---

## Phases (all closed)

```
.1 plan-core ──────────────────────────────────────────────┐
.2 vault-now ──────────────────────────────────────────────┤
.3 hooks-tmux          ← .1                                │
.4 capture-budget      ← .1 ─┐                             │
.5 close-drop          ← .1 .4                             │
.6 now-token           ← .5                                │
.7 ledger-plan-view    ← .1 ─┐                             │
.8 link-picker ──────────────┤                             │
.9 now-toggle          ← .8 .7                             │
.10 link-notice-budget ← .7                                │
.11 mac-budget         ← .4                                │
.12 mac-close-now      ← .11 .5 .6                         │
.13 rollout            ← .1 .2 .3 .6 .7 .9 .10 .12 ────────┘
```

| Id | Size | What landed |
| --- | --- | --- |
| `.1` | M | `plan:` config, pure engine, NOW counter, `bob plan`, `docs/plan.md` |
| `.2` | S | Vault NOW chip/section; chore swap (trial start, no code wait) |
| `.3` | S | Hooks JSON + human meter; tmux suffix |
| `.4` | M | Capture budget, strict mode, destination `role` |
| `.5` | M | `~<K>` drop |
| `.6` | M | First-class `#now` in capture + Ready `#now` in `^` |
| `.7` | M | JS mirror, `bob-plan` block, public API |
| `.8` | M | Ctrl+Shift+P through a Task Link |
| `.9` | M | Alt+N / picker `#now` toggle |
| `.10` | S | Plan suffix on Ctrl+Shift+Enter Notices |
| `.11` | M | Mac meter, destination row, cap badge |
| `.12` | M | Mac drop + `#now` + NOW badges |
| `.13` | S | Dash PLAN chip, template, config, install, e2e |

bob-cli commits (workspace `main`): `db89ee8` (engine), `f481c7a` (hooks/tmux), `35b96b3` (capture budget), `754d1f3` (drop), `d28f8cd` (`#now`), `25c1b2f` (closeout). Landed by `bob-cli-2o.land` after a dedicated tale that isolated a mistyped `plan:` block from other commands, made NOW-over leave `status` as `ok` (status is themes and links only), treated `[[#^id]]` / daily-path / basename as one link, and attached capture budget only when the Pomodoros section actually changed.

---

## Held for later, on purpose

From the research, plus design calls in the epic plan:

- **Phase 2 of the research** (after the 2026-09-30 → 2026-10-13 trial): `stale_link`, `bob pomodoro stats`, move-with-link-repair, a `#next` tag, pull-a-theme, a "close day" command.
- **Rejected storage:** `[roadmap::]` / `[horizon::]` fields (a trailing custom field erases Tasks `priority` and `created`); a hand-kept `roadmap.md`; `roadmap.base` (Bases rows are files); a DataviewJS view file (`.js` outside `.obsidian/` does not sync).
- **Invariant:** `#now` is never a Next source and never changes checkbox status.

Follow-ups already filed from landing:

| Bead | What |
| --- | --- |
| **bob-cli-2q** | apollo's system TZ is `Etc/UTC`, so after 20:00 EDT every "today" picker (`bob plan`, capture, tmux, hooks) aims at tomorrow's note. Medium bug. |
| **bob-cli-28** | Pre-existing clippy deny at `tests/cli/capture/pomodoro_name.rs:808` (`overly_complex_bool_expr`). Closeout recorded it as corroboration on that epic. |
| **bob-cli-v** | Clippy warning noise; land +1'd with the current count. |

---

## What Bryan still does by hand

The tools hold the line. The trial is the habit:

1. Tag at most **15** tasks `#now` for the week (type it, Alt+N, or the Ctrl+Shift+P `#now` row). Put the tag before trailing fields.
2. From 2026-09-30, carry at most **3** open entries by hand. Leave the rest in yesterday.
3. Put **GTD + ≤3 themes** in the daily note, highlight first.
4. On the MacBook and athena: reinstall `bob`, rebuild Bob Mac Capture, `bob plugins sync`.
5. After a week of red PLAN chips, consider `plan.strict: true`.
6. Confirm the two new `gtd_daily.md` chores (they were flipped to `[?]` by a MacBook sync after creation).

Monday review: re-tag NOW to ≤15, promote from READY, defer with P-levels. Untag anything with no 🍅 in seven days that is no longer a weekly bet.

---

## Sources

- Epic bead `bob-cli-2o` and phases `.1`–`.13` (close notes, land audit, e2e paste).
- `plan:202609/pomodoro_plan_budget_now_tag.md` and `plan:202609/plan_budget_land_closeout.md`.
- Shipped definition: `docs/plan.md`; capture grammar: `docs/capture.md`; hooks: `docs/task-status-hooks.md`; README "Plan budget".
- Implementation: `src/native/plan_budget/`, `src/native/config/plan.rs`, `src/native/capture/budget.rs`, `src/native/capture_pomodoro_close/selection.rs`.
- Motivating research: `research:202609/pomodoro_closed_day_now_tag_automation/pomodoro_closed_day_now_tag_automation.md`, `research:202609/now_tag_vs_in_progress_status.md`.
