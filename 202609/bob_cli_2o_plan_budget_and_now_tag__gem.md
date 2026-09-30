# Retrospective: Epic `bob-cli-2o` — Plan Budget, `#now`, and Ledger Guardrails

> **Executive Summary:**  
> The `bob-cli-2o` epic tackled a systemic pathology in Bryan's daily planning: runaway daily Pomodoro ledgers that routinely ballooned to 20+ open themes and 70+ task links, sustained by an exhausting morning routine of carrying unfinished work forward. The epic codified an authoritative rule across three repositories and the Obsidian vault: **"Today is a closed list (GTD + ≤3 themes, ≤10 links); This week is `#now` (≤15 bets); Everything else is READY or deferred."** The system replaces willpower and morning migration chores with automated, ubiquitous budget guardrails across the CLI, tmux, capture flows, and Obsidian.

---

## 1. The Why: Pathology of the Unbounded Ledger

Before `bob-cli-2o`, Bryan's daily Pomodoro ledger suffered from chronic planning inflation:

* **The Runaway Queue:** Daily notes regularly accumulated ~110 lines of backlog. Peak open themes reached **21** (against an average completion rate of ~3 per day), and peak open Task Links reached **74–75**. Only ~13% of planned themes were completed each day.
* **The Migration Trap:** Three separate morning GTD chores (*Migrate unfinished Pomodoro tasks*, *Review READY tasks*, and *Review WIP + NEXT*) mandated manually carrying leftover tasks forward. This created high friction, planning fallacy overhead, and zombie tasks.
* **Status Sprawl:** Incomplete tasks carried forward automatically entered in-progress (`[/]`) or next (`[*]`) states across the vault (accumulating ~75 active items), destroying the distinction between active focus and future intention.
* **Intake vs. Closure Imbalance:** New tasks were captured at roughly twice the rate of closure (2:1 ratio). Uncapped ledger insertions and default carry-forward on session close (`=x`) continuously fed the inflation.

```
[ Traditional Anti-Pattern ]
Capture/Carry-Forward ──> Uncapped Daily Note (20+ themes, 75+ links) ──> Overwhelm (~13% completed)
        ▲                                                                           │
        └──────────────── Morning Migration Chore ("Carry forward") ────────────────┘

[ The bob-cli-2o Guarded Model ]
Capture ──> Budget-Guarded Ledger (≤3 themes, ≤10 links) ──> High Focus (~70%+ hit rate)
                 │
                 ├── Dropped from today (~K) ──> Kept in view via #now (≤15 weekly bets)
                 └── Deferrals (P2/P3)       ──> Safely moved to future / backlog
```

---

## 2. The Rule: A Three-Tier Horizon Model

The epic establishes a crisp three-tier planning taxonomy:

| Horizon | Tool Anchor | Constraints / Budget | Behavioral Role |
| :--- | :--- | :--- | :--- |
| **Today** | Daily Note (`## Pomodoros`) | **≤ 3 themes**, **≤ 10 Task Links** (GTD exempt) | **Closed list.** Highlight is 1st non-exempt theme. Unfinished tasks are never copied forward by default. |
| **This Week** | `#now` tag | **≤ 15 tasks** across the vault | **Tactical bets.** Visible on dashboard; unlinking or dropping from today never loses them. Not a status change. |
| **Later** | READY / P-levels | Unbounded backlog, scoped by priority | Backlog tasks resurface via scheduled reviews or priority horizons. |

---

## 3. What Was Implemented: System Architecture & Phases

The epic delivered 13 distinct phases across `bob-cli`, `bob-plugins`, `bob-mac-capture`, and the vault:

```
                                  ┌───────────────────────────────┐
                                  │   ~/.config/bob/config.yml    │
                                  │  max_themes: 3, max_links: 10 │
                                  │   max_now: 15, strict: false  │
                                  └──────────────┬────────────────┘
                                                 │
                   ┌─────────────────────────────┴─────────────────────────────┐
                   ▼                                                           ▼
       ┌───────────────────────┐                                   ┌───────────────────────┐
       │   bob-cli (Rust)      │                                   │ bob-plugins (JS API)  │
       │  src/native/plan_budget│                                  │   bob-ledger-tools    │
       └───────────┬───────────┘                                   └───────────┬───────────┘
                   │                                                           │
     ┌─────────────┼─────────────┬─────────────┐                 ┌─────────────┼─────────────┐
     ▼             ▼             ▼             ▼                 ▼             ▼             ▼
 `bob plan`    tmux bar     `bob capture` task-status      `bob-plan` code   Ctrl+Shift+P   Alt+N toggle
 (CLI/JSON)   meter & rev   warnings/guards   hooks          block in daily   link-edit mode  (#now token)
                   │
                   ▼
       ┌───────────────────────┐
       │   Bob Mac Capture     │
       │ Destination & Meters  │
       └───────────────────────┘
```

### 3.1 Shared Plan Budget Engine (`bob-cli`)
* **Core Calculator (`src/native/plan_budget/`):** Pure functional parser implementing rules 1–9 from `docs/plan.md`. Parses column-0 checkbox entries (`- [ ] () — THEME`), splits compound names (`BOB + DECKS`), excludes exempt entries (`GTD`), deduplicates links (`[[target#^id]]`), ignores struck-out (`~~...~~`) or fenced links, and identifies the highlight and running entries.
* **Unified Config (`config/plan.rs`):** Configured in `~/.config/bob/config.yml` with safe defaults (`max_themes: 3`, `max_links: 10`, `max_now: 15`, `strict: false`, `exempt: [GTD]`). Invalid configuration falls back gracefully without breaking capture or tmux.
* **Read-Only `bob plan` CLI:** Provides immediate feedback in both ANSI color human output (`PLAN 3/3 themes · 7/10 links   NOW 12/15`) and machine-readable JSON (`schema_version: 1`).
* **Authoritative Lints:** Standardized lint engine with stable codes:
  * `plan_theme_cap_exceeded` & `plan_link_cap_exceeded`
  * `duplicate_open_pomodoro_name`
  * `inventory_label_open` (warns against storage labels like `LATER` or `MISC`)
  * `subheading_in_pomodoros` (flags subheadings that break time tracking)
  * `now_cap_exceeded`

### 3.2 Ubiquitous Budget Visibility
Every surface Bryan touches exposes the exact same budget numbers:
1. **tmux Status Line (`bob tmux-pomodoro`):** Appends `plan T/Tc · L/Lc | ` to the current Pomodoro segment; switches to reverse video (`#[reverse]`) when over budget.
2. **Periodic Reconciliation (`bob task-status-hooks`):** Injects the full `plan_budget` object into JSON output and prints a concise human summary. Also flags multiple open timed Pomodoro entries with corrective guidance.
3. **Daily Note Header:** Embedded ` ```bob-plan ` code block rendered by `bob-ledger-tools` directly above `## Pomodoros`. Renders interactive PLAN and NOW chips with active theme lists and lints.
4. **Obsidian Dashboard (`dash.md`):** Features `NOW 12/15` and `PLAN 3/3 · 7/10` chips alongside a dedicated `### NOW Tasks` dataview section.
5. **Obsidian Notices:** Appends `· plan T/Tc · L/Lc 🔴` to link feedback notifications on `Ctrl+Shift+Enter`.

### 3.3 Capture Guardrails & Strict Mode
* **Before/After Diffing:** `bob capture` diffs the daily note before and after batch operations, warning on stderr if a capture causes themes or links to exceed their caps.
* **Strict Mode (`plan.strict: true`):** When enabled, atomically rejects any capture batch that introduces an unstarted named theme when already at or over `max_themes` (session starts with `=` are always permitted).
* **Implicit Destination Transparency:** Output reports destination `role` (`current`, `next_up`, `named`, `created`) so Bryan immediately sees where captured links land (e.g., `→ under GOALS (next up)`).
* **Bob Mac Capture Frontend:** Displays live theme/link meter capsules, destination banners (`→ GOALS · next up`), and mint-colored `#now` highlighting.

### 3.4 New Gestures: Dropping and Tagging from the Ledger
* **Drop Outcome for `=x` Closes (`~<K>`):**
  * Grammar extended: `=x[<N>][!<M>][~<K>]` (e.g. `=x~2,3` or `=x1!2~3`).
  * Dropped tasks (`~K`) are cleanly excised from today's entry: they do **not** carry forward to a new placeholder stub and do **not** mark the task as started (`[/]`).
  * If the task has `#now`, it safely remains in the weekly pool.
* **First-Class `#now` Capture:**
  * Syntax: `<text> @route^id #now` automatically resolves `#now` before trailing dataview fields (`[created::...] ^id`).
  * Completion context (`now_tag`) suggests `#now` ("This week's bet").
* **Link-Mode Task Editing in Obsidian (`bob-navigation-hotkeys`):**
  * `Ctrl+Shift+P` on a dedicated Task Link bullet directly targets the resolved task file and line.
  * Counted prefix `N<Ctrl+Shift+P>` operates across sibling link bullets.
  * `Alt+N` (and counted `N<Alt+N>`) toggles `#now` on both `#task` lines and tasks behind Task Links in a single chord.

### 3.5 GTD Chore Modernization (`gtd_daily.md`)
The daily manual chore overhead was replaced by two focused rituals:
* **Retired Chores:** Cancelled "Migrate unfinished Pomodoro tasks...", "Review READY tasks", and "Review WIP + NEXT...".
* **New Chores:**
  1. **Daily Pick (≤ 5 min):** `Pick today: ≤3 themes from yesterday + NOW (highlight first)`
  2. **Weekly Review (Monday):** `Weekly review: re-tag NOW to ≤15, promote from READY, defer with P-levels...`

---

## 4. Key Behavioral Takeaways

1. **Closed List vs. Running Queue:** By treating today's note as a closed container and stopping automatic carryover, unfinished items naturally drop back to the weekly pool or backlog rather than polluting tomorrow's focus.
2. **Defensive Defaults:** Instead of asking the user to manually track caps, tooling across all environments (terminal, editor, Mac menu bar) surfaces identical meter states in real-time.
3. **Frictionless Dropping:** The `=x~K` drop gesture eliminates the guilt of leaving tasks incomplete; work can be dropped from today's plan without being lost or cluttering the next session.
