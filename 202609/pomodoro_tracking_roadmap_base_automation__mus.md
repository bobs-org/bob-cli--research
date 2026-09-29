# Pomodoro tracking: simplify the day with a property-backed roadmap base and guard-railed automation

- Researcher: mus (`__mus`)
- Date: 2026-09-29
- Question: should Bryan change how he tracks pomodoros / work / time / the day's roadmap in `## Pomodoros`, and if so, how, keeping it simple?
- Prior work reviewed: `~/bob/lib/chat/pomodoro_ledger_and_daily_roadmap.pdf` (16 pp., extracted via `mutool draw -F txt`; highlights sidecar `lib/chat/pomodoro_ledger_and_daily_roadmap.md` + `ref/chat/pomodoro_ledger_and_daily_roadmap.md` confirm the recommended solution), today's daily note `~/bob/2026/20260929.md`, `~/bob/dash.md`, `~/bob/_templates/daily.md`, `~/bob/gtd_daily.md`, `docs/capture.md`, `docs/task-status-hooks.md`, `bob capture --help`, `bob task-status-hooks --help`, `bob capture-pomodoros --format json`, `bob task-status-hooks --dry-run --format json`, Obsidian hotkeys + `block-id-prompt` / `bob-navigation-hotkeys` sources.

## 1. What I verified independently

1. The completed ledger is worth keeping. The heading Dataview formula sums `t` over completed tasks whose `meta(task.section).subpath` starts with `Pomodoros`; variable block lengths (median ~30–40 min, majority ≥50 min per prior measurement) are fine. `bob pomodoro`, `tmux-pomodoro`, `capture`, `block-id-prompt`, and `task-status-hooks` all key off the literal `## Pomodoros` heading (`is_pomodoros_heading` in `src/native/pomodoro.rs`, `/^##\s+Pomodoros(?:\s.*)?$/` in the plugin). Do not rename the heading.
2. The open queue is the problem, and it is still the problem today. `bob capture-pomodoros --format json` on today's file reports **22 open entries, 75 references** (`count:22`), including two separate open `SASE` buckets and a `LATER` bucket with 23 child links sitting inside the daily "plan". The prior report's "78 links / 23 entries" figure reproduces.
3. The mechanism diagnosis reproduces: capture defaults into today (`@route:id` → Next `[*]` + ledger link; `#name` creates `- [ ] () — NAME` future buckets), `task-status-hooks` promotes ledger-linked tasks to Next / keeps In Progress, and the "migrate unfinished" ritual copies leftovers forward while the "review WIP+NEXT and plan" ritual lapsed (last done 2026-09-09 per prior git-history work; today's `gtd_daily.md` still shows that planning task open/scheduled 2026-09-10). `task-status-hooks --dry-run` today scans 4577 files, keeps 25 Next + 52 In Progress alive from ledger reachability — status inflation is real.
4. The closed ledger hides the queue. End-of-day files look clean because migration cuts leftovers; only git history or a mid-day `capture-pomodoros` count shows the 20× growth. Any new process must make the **mid-day open count** visible, not the end-of-day file.

I agree with the prior report's core: keep the log, cap the open plan to ~1 highlight + ≤2 themes + GTD (~10 links, ~200 planned minutes), move the rest out of the daily note, fix the capture default, prune weekly, trial two weeks.

## 2. Where the prior research falls short (and what I add)

1. **No automation proposal.** The prior §7.7 lists "optional tooling, only after the habit holds" but specifies no keymaps, no capture grammar change, no hooks change. Habit-only fixes for a 70-item daily review are exactly what lapsed. Automation must ship with the process, not after.
2. **No `roadmap.base` / badge / properties design.** Prior proposes `roadmap.md` (Now/Next/Later markdown buckets in ledger shape). That duplicates the ledger's NAME + link-children shape in a second file, requires daily cut/paste, and re-creates the same manual-inventory failure mode. It never evaluates Obsidian Bases (`roadmap.base`), a badge/count on `dash.md`, or Dataview properties (`horizon::` / `roadmap::`) on the tasks themselves.
3. **No capture / mac-app / hooks automation analysis.** Prior names the `@route^id` habit but does not design the grammar default, the mac-app UX, or what `task-status-hooks` should enforce vs. warn.
4. **Other gaps I address below:** (a) `roadmap.md`-as-pile risk has no enforcement; (b) manual morning-pick cost is unmeasured and unscripted; (c) highlight hit-rate / plan-load metrics are hand-counted; (d) sub-section proposals (`## Roadmap`, `### Log`) break the heading total and were correctly rejected but the reason needs to become a lint rule; (e) research/`#ref` inflow (172 unread) and intake/closure ratio (0.47 in Sep) need a budget, not just a prune; (f) multi-open-timed-entry failure is a hard error today rather than a guided fix.

## 3. `roadmap.base` + properties instead of `roadmap.md`

### 3.1 Recommendation: tasks keep living in their home notes; the roadmap is a view, not a second copy

Prior `roadmap.md` asks Bryan to cut NAME + link-children buckets into Now/Next/Later headings. That preserves the valuable theme grouping (DECKS, QUEUE, SUDO, LATER) but creates two copies of every intention: one in the project note (the task), one in the roadmap (the link). Every cut/paste can drift, and there is no queryable owner for "what is Now?".

Prefer:

- A single Dataview/Tasks property on the task itself, e.g. `[horizon:: Now]` (alternatives: `[roadmap:: Now]`; pick one, document it, never both). Values: `Now` / `Next` / `Later` (+ blank = un-triaged inbox). This is the same inline-field mechanism already used for `[t::]`, `[created::]`, `[scheduled::]`, `[repeat::]`, `highlight::`.
- `roadmap.base` (Obsidian Bases) as the visual board: three views filtered by `horizon` (Now = this week's bets ≤5 themes; Next = queued; Later = parked), grouped by project/file. Bases gives drag-between-columns behavior that markdown buckets cannot, with no link-copying.
- `dash.md` gets a small roadmap badge row at the top reusing the existing `task-count-widget` pattern (WIP/NEXT/READY/BLOCKED chips are already computed in dataviewjs): add `NOW / NEXT / LATER / UNTRIAGED` counts from the same `plugin.getTasks()` scan or a Tasks query on the `horizon` field. Badge = early warning when `roadmap.base` becomes the next pile (e.g. Later > 50, Now themes > 5, untriaged growing).

Why this beats `roadmap.md`:

- One source of truth per task; no daily cut/paste of links; weekly review re-tags properties instead of moving lines.
- Counts are queryable for badges and trial metrics; markdown-bucket link counts require parsing headings.
- Capture can set the property atomically (`@route^id` + default `horizon:: Next`), so "captured but not for today" lands triaged instead of unowned.
- The daily note stays a **closed list of links**, while the base stays the **inventory** — Cirillo's To-Do-Today / Activity-Inventory split without two link-copies.

Migration cost is the objection: today's 70+ queued links have no `horizon` value. Answer: one-time script (`bob` one-shot or a Bases bulk-edit) that maps today's buckets to initial values — `LATER` bucket → `Later`, `QUEUE`/`NEW FEATURES` → `Next`, the ≤3 picked themes → `Now`, everything else → `Next` then prune in the first weekly review. Do not hand-edit 70 lines.

Fallback if Bases proves annoying: `roadmap.md` with the same three headings is an acceptable rendering of the same property (a manual view). But keep the property authoritative so the badge still works.

### 3.2 What the badge should show (top of `dash.md`)

Extend the existing chip bar, do not build a second dashboard:

- `NOW 5 · NEXT 18 · LATER 42 · INBOX 6` (example), each chip linking to the corresponding `roadmap.base` view.
- Second line (small, text-only): `today: 3/4 open · 8/10 links · highlight: touched 🍅` — plan-load signal (see §4.3).

Implementation is ~20 lines of dataviewjs beside the current WIP/NEXT/READY/BLOCKED computation. If `plugin.getTasks()` does not expose custom inline fields, use a `dv.pages().file.tasks`-style query on the `horizon` field instead; prototype both before committing to the property name.

## 4. Automations to implement (ship with the process, not after)

### 4.1 Obsidian keymaps (add, do not overload)

Keep `Ctrl+Shift+P` (schedule/priority + SCHEDULE LOG) and `Ctrl+Shift+Enter` (link into today's open entry / WORK LOG) unchanged. Add three small commands in `bob-navigation-hotkeys` (or block-id-prompt where the Pomodoro target logic lives):

1. **Pick from Now** (`Ctrl+Shift+Y` or free binding): picker over `roadmap.base#Now` themes; inserts `- [ ] () — THEME` + chosen links as one open entry, capped (refuses 5th entry / 11th link with a notice naming the cap). Replaces manual copy from roadmap.
2. **Send back to roadmap** (`Ctrl+Shift+U`): moves current open entry's links to their `horizon` home (sets property, removes ledger link via the same path `task-status-hooks` understands). This is the " cut yesterday's open entries" step as one keystroke.
3. **Cap check / highlight jump** (`Ctrl+Shift+H`): jumps to / creates the `highlight::` line above `## Pomodoros`; shows `open entries (n/4) · links (n/10) · highlight touched?` in the notice. Makes violations visible at the moment of planning.

All three must reuse `selectPomodoroInsertionTarget` semantics (single-open-timed guard) so they never create the multi-open-timed failure state.

### 4.2 `bob capture` grammar + `bob-mac-capture` app

Do not add a large new grammar. Make the safe path the default:

- Today the default mental model is "`:` = today". Keep `:`, but add a **cap guard**: when the day already has ≥4 open entries or ≥10 open links, `@route:id` (implicit or `#name` creation) warns/confirms (`--yes` to force; `--dry-run` previews). The prior "capture guard or config" idea is correct; make it a confirm-by-default, not a silent append. Config: `capture.today_cap_warn = true`, `capture.today_cap_entries = 4`, `capture.today_cap_links = 10`.
- Promote `^` (`@route^block-id`: ordinary Ready task, no ledger link) to the documented "not for today" path and let it also write the default horizon (`[horizon:: Next]` unless `s:`/`p:` says otherwise). Then the morning pick and weekly review only re-tag, never relocate.
- Optional tiny addition only if user testing shows confusion: `@route!block-id` as explicit "to Now" (creates Next + ledger link + `horizon:: Now`). I would **not** add this on day one; `:` + picker covers it. If added, `!` must share the cap guard.
- `bob-mac-capture`: add a `For today?` toggle (default OFF) + live preview line `today 3/4 · 8/10 · highlight touched`. When OFF, emit `^`; when ON, emit `:` (+ optional `#THEME` picker filtered to today's ≤3 themes). Show the cap warning inline before commit. This single checkbox fixes the measured 91%-captured-straight-into-today inflow without retraining muscle memory.

### 4.3 `bob task-status-hooks` as enforcer + scoreboard

`task-status-hooks` already owns dedupe, canceled-reference removal, childless-entry deletion, completed-reference retirement, and the multi-open-timed hard fail. Extend it minimally:

1. **Cap report (warn, don't fail):** every run (including `--dry-run`) prints `plan_load: {open_entries, open_links, highlight_present, highlight_touched}` and warns when over cap (`plan-over-cap: 22 open entries (cap 4), 75 links (cap 10)`). This is the violation-visibility the prompt asks for; it also feeds the dash second line and `bob pomodoro` output (`🍅 · 3/4 · 8/10`).
2. **Keep the multi-open-timed fail, but add a fix hint:** name the two entries + suggest the keymap ("run Send-back or close one with `=x`"). Today's hard error is correct; its message is not actionable enough.
3. **Lint the forbidden shapes:** warn on `###` sub-headings inside `## Pomodoros` (breaks the heading-total `subpath` test), on inventory labels (`SASE/MISC/LATER/NEW FEATURES`) as open daily themes, and on duplicate open names (two `SASE` buckets today). These are the exact failure shapes observed.
4. **Do NOT let `roadmap#Now`/base become a Next source by default.** Keep Next = today (open ledger) + recent-activity, as prior recommends. Only if the weekly signal is missed after the trial, add an opt-in `roadmap_now_is_next = true`. Otherwise statuses re-inflate and the badge loses meaning.
5. **One-shot migration/prune helpers, not daily magic:** `bob task-status-hooks --migrate-to-horizon` (one-time property seeding) and weekly `--prune-horizon --older-than 21d --no-tomato` (lists/cancels stale Later items). Daily runs stay idempotent and fast.

## 5. Trial, metrics, and risks

Run the prior two-week trial (2026-09-30 → 2026-10-13) with its signals (open entries ≤4, links ≤10, pick ≥10/14 days, highlight hit ≥80%, `[/]+[*]` ≤15, closed/created → 1), plus:

- Morning-pick duration (target 5–10 min; if lapsing, shrink `gtd_daily` to just the highlight line).
- Cap-warning override rate (if `:` is forced daily, the cap is wrong or intake needs the research budget).
- `Later > 50` → hard prune; `untriaged` count → capture-default check.

Risks: (1) `roadmap.base` becomes the next pile — defenses are the badge + weekly prune + research/reading budget (cap new swarms until `#ref` backlog drops); the intake ratio (0.47) cannot be fixed by planning alone. (2) Property-name churn — freeze `horizon::` (or chosen name) before migration; support exactly one spelling. (3) Over-automation — ship cap-warn + badge + two keymaps first; defer `!` syntax, calendar overlay, strict 25/5, day-themes, embedded daily queries (agree with prior §7.7).

## 6. Recommended solution (do this)

1. **Keep** `## Pomodoros`, the ledger format, `se`/`+N`/`-N`/`=X`/`=x`, variable blocks, `🍅`, WORK/SCHEDULE LOGs.
2. **Cap the day:** `highlight::` outcome line above the heading + ≤3 open entries besides GTD (highlight theme + ≤2) + ~10 links + ~200 planned min. Unplanned urgent work gets its own honestly-named block; no pre-staged buckets.
3. **Inventory as properties + base, not a second link-copy:** `[horizon:: Now|Next|Later]` on home-note tasks; `roadmap.base` (Now/Next/Later views); `dash.md` badge row (NOW/NEXT/LATER/INBOX) + `today n/4 · n/10 · highlight?` line. One-time seeded migration, then weekly re-tag.
4. **Automate the boundary:** cap-guard on `bob capture :` (+ `^` writes `horizon:: Next`); mac-app `For today?` toggle (default off) with live plan-load; keymaps pick-from-Now / send-back / highlight-jump; `task-status-hooks` cap report + better multi-open-timed hint + forbidden-shape lints; Next stays = today.
5. **Rituals:** 5-min morning pick (replaces migrate + daily READY/WIP reviews; READY moves weekly) with standing if-blocked rule; 25–50 min weekly review (re-rank Now ≤5, prune ≥3-week stale, review READY, set research budget, check hours / highlight-hit / created-vs-closed). Evening-before highlight optional.
6. **Trial two weeks** against the signals above; if the base adds friction, drop the base and keep capped ledger + properties + badge (the minimal variant). If intake still outruns closure, the lever is the capture default + research budget, not more planning structure.

This is simpler day-to-day than today (20 ledger lines, not 110; one pick, not three chores), and the only new structure is one property, one base view, one badge row, and guard-rails on tools Bryan already uses.
