# Close the day, tag the week

*What `bob-cli-2o` implemented, why it exists, and what it deliberately leaves to Bryan*

**Research date:** 2026-09-30  
**Epic:** `bob-cli-2o` — *Close the day, tag the week: plan budget, `#now`, and ledger guardrails*  
**Result:** all 13 phases closed; rollout completed across `bob-cli`, `bob-plugins`, Bob Mac Capture, the vault, and chezmoi-managed config.

> **In one sentence:** the epic turned the Pomodoro ledger back into a small, truthful plan for today, gave weekly commitments their own `#now` identity, and put the same guardrails everywhere work enters—without letting automation choose or erase work.

## Why this was built

The completed half of Bryan's `## Pomodoros` section was already useful: an honest record of time, themes, links, and notes. The open half was not. It had become four systems at once—today's plan, the backlog, the capture inbox, and the source of task status—and daily migration kept copying the whole pile forward.

The research behind the epic found three decisive facts:

- Bryan worked a median of **three planned themes per day** even as the median open list grew from 12 to 22 themes and its links grew toward 80. The cap therefore reflects observed throughput, not an aspirational quota.
- Removing a Task Link felt like losing the task because the link also drove Next/In Progress status. That encouraged hoarding. A separate weekly marker was needed so status could decay truthfully.
- Existing P1–P4 deferral already handled “Later,” and READY already handled “Next.” A second roadmap file, custom horizon fields, or task-level Obsidian Base would duplicate working machinery and add maintenance.

The resulting rule is intentionally small:

> **Today is closed:** GTD plus at most three themes and roughly ten Task Links. The first theme is the highlight.  
> **This week is `#now`:** at most fifteen visible tasks.  
> **Everything else is READY or deferred with a P-level.**

The distinction matters: **`[/]` is an automatically derived footprint of recent work; `#now` is a promise Bryan controls.** A task can lose its link and let its status decay while remaining visible as a weekly bet.

## What shipped

### 1. One budget definition, many views

`docs/plan.md` is now the authoritative contract. A new Rust engine computes a read-only report from today's open Pomodoro entries:

- distinct non-GTD themes, capped at 3;
- distinct Task Links, capped at 10;
- eligible `#now` tasks, capped at 15;
- the first open theme as ★ highlight and the timed entry as ▶ running;
- stable lints for exceeded caps, duplicate names, inventory labels used as themes, and subheadings inside the ledger.

It correctly ignores completed/cancelled entries, fenced code, struck links, duplicate links, and all-exempt entries. Configuration lives in an optional `plan:` block with shared defaults; invalid config is fatal only for `bob plan`, while operational surfaces fall back safely and warn.

The same information now appears where Bryan already looks:

| Surface | What changed |
|---|---|
| `bob plan` | New human/JSON command with full meters, entries, highlight/running state, NOW count, and lints. |
| `task-status-hooks` | Additive `plan_budget` JSON plus a human meter; status reconciliation remains separate. |
| tmux | Appends `plan T/3 · L/10`, reversed when over cap. |
| `bob capture` | Shows before→after budget, destination role, cap warnings, and optional strict refusal. |
| Daily note / `dash.md` | Live `bob-plan`, PLAN and NOW chips, and a generated NOW Tasks section. |
| Obsidian notices | Link changes show the resulting plan meter; NOW toggles show the weekly count. |
| Bob Mac Capture | Destination row, Themes/Links capsules, deltas, warnings, cap badges, and accessible summaries. |

Rust is the source implementation. `bob-ledger-tools` mirrors it in JavaScript because Obsidian must render locally, but both use the same documented conformance cases. Other plugins consume Ledger Tools' versioned API instead of inventing a third interpretation.

### 2. Guardrails at the point of capture

Capture now reports exactly where a Task Link will land—current, next-up, named, or newly created Pomodoro—and previews the resulting budget. Warnings fire when the operation grows an already over-cap dimension. With `plan.strict: true`, a named capture that creates a new over-cap theme is refused atomically; the default remains advisory.

`#now` became first-class capture grammar rather than an incidental tag:

- it works before or after the route marker and is written in the parser-safe position before trailing fields;
- `#n` / `#no` offer completion to `#now`;
- Ready `#now` tasks appear in the active-task picker with a NOW badge;
- new JSON fields are additive, and the Mac app decodes them tolerantly so older `bob` binaries still work.

### 3. The missing “not today” gestures

The close grammar now accepts `~<K>` in `=x[<N>][!<M>][~<K>]`. A dropped link is removed from today's closed session, not carried and not started; its task and any `#now` tag remain intact. The CLI and Mac close card both show the dropped outcome, with the Mac caption “stays in NOW” when appropriate.

Obsidian gained the complementary direct-manipulation tools:

- **Ctrl+Shift+P on a dedicated Task Link** edits the linked task in its source note; a count applies to sibling links, and future scheduling still prunes those links from today.
- **Alt+N** and a pinned `#now` property row toggle the weekly tag from either task lines or Task Links, including counted batches and guarded cross-note writes.
- **Ctrl+Shift+Enter** link/unlink notices include the post-write plan meter.

Together these remove the old psychological trap: pruning today no longer means forgetting the week.

### 4. The workflow—not just the code—was rolled out

The epic changed the vault immediately:

- added NOW first in the dashboard, then switched PLAN/NOW chips to the Ledger Tools API;
- added a live `bob-plan` block to the daily template and rollout day's note;
- cancelled three migrate/review chores and replaced them with one daily pick and one weekly `#now` review;
- installed the CLI, synced the plugins, applied the documented config defaults, synced the vault, and exercised the end-to-end contracts.

The rollout's live reading was **19/3 themes, 73/10 links, NOW 0/15**. That red result is not a failure of the feature; it reveals the inherited queue. The tools now hold up the ruler. They do not rewrite the ledger behind Bryan's back.

## The key design judgment

This epic is best understood as **automation of feedback and safe gestures, not automation of planning**.

It deliberately did **not** add a hand-maintained roadmap, `[roadmap::]` / `[horizon::]` fields, a highlight field, `#now` as a Next source, cron that rewrites old notes, or automatic pruning/migration. Those options either duplicated READY/P-levels, risked Tasks metadata parsing, inflated statuses again, or made a tool silently decide what mattered.

Also deferred until the two-week trial justifies them: multi-day stale-link analysis, Pomodoro statistics, move-with-link-repair, `#next`, pull-a-theme, and an explicit close-day command. The minimal system should get a chance to work before acquiring another layer.

## Confidence and loose ends

The phase records show broad verification: final Rust tests passed (**1,890 tests** across the recorded suites), formatting passed, plugin tests and validation passed, and Bob Mac Capture's macOS CI was green (including real-`bob` wire fixtures). The full Rust `just all` gate remained red on a pre-existing Clippy-denied tautology in `tests/cli/capture/pomodoro_name.rs`; closeout routed that evidence to the already-active `bob-cli-28` rather than misattributing it to this epic.

Two operational caveats remain:

- Apollo's system timezone is UTC while the vault day is Eastern; after 20:00 EDT, `Local::now()` can select tomorrow's note. This was filed as `bob-cli-2q`.
- The feature is deployed on Apollo, but the plan's manual checklist still calls for reinstalling `bob`, rebuilding Bob Mac Capture, and syncing plugins on the MacBook and Athena.

## Bottom line

`bob-cli-2o` did not build a more elaborate productivity system. It separated three meanings that had collapsed into one list:

1. **the ledger records what happened;**
2. **the capped open section says what is planned today;**
3. **`#now` remembers what matters this week.**

The most important implementation choice is that every surface agrees on those meanings while Bryan remains the only component allowed to choose the work.

---

## Evidence consulted

- `bead:bob-cli-2o` and all 13 audited child phase records
- `plan:202609/pomodoro_plan_budget_now_tag.md`
- `research:202609/pomodoro_closed_day_now_tag_automation/pomodoro_closed_day_now_tag_automation.md`
- `research:202609/now_tag_vs_in_progress_status.md`
- Landed source and history in `bob-cli`, `bob-plugins`, `bob-mac-capture`, and chezmoi, including closeout commits `25c1b2f`, `17fbc09`, Mac commits `1e025ce` / `b020df7`, and config commit `2d048c58`

