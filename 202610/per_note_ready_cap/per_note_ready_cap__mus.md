# Ready-task budget per area/project note (cap N, default 5)

**Researcher:** mus · **Date:** 2026-10-01 · **Vault/bead context:** `bob_gtd.md#^prj-task-count-warn`
("Show warnings when projects contain >5 ready tasks!")

## TL;DR

This is a good idea and it fills a genuine gap: the vault already caps the
**global** READY backlog (`plan.max_ready: 100`) and the **daily** plan
(`max_themes`/`max_links`/NEXT/PENDING caps), but there is no **per-note**
WIP limit, so one bloated project note can silently hold 30 "ready" tasks
while every global meter stays green. Implement it as a **soft limit**
(not a blocker), consistent with every existing cap in this system:

- New `ready:` config block, `max_per_note: 5` default, optional per-note
  `task_budget:` frontmatter override.
- New read-only CLI (`bob ready`) + a capture-time warning; reuse the
  plan/freshness output idioms (TTY color, JSON `schema_version: 2`).
- Obsidian side (bob-plugins): a non-modal Notice on the move/write
  gestures that actually push a destination note over budget, plus a
  `dash.md` over-budget section and a per-note `READY n/5` badge rendered
  by bob-ledger-tools. No modals, no refused writes.
- Count **dashboard-READY per file** as the definition of "ready" (TODO,
  visible, unblocked, due, not-Today, freshness-confirmed-or-exempt);
  ship a same-day v1 on the already-native SHOWN predicate if the full
  predicate proves expensive, clearly labeled.

## 1. What I inspected (method)

- `docs/plan.md` (plan budget, Today, NEXT/PENDING/READY lane definitions),
  `docs/freshness.md` (freshness-gated READY, `bob freshness` contract,
  native-fallback behavior), `docs/projects.md` (`^prj` sync, SHOWN column,
  `Ctrl+Shift+P`/`Ctrl+D` project-schedule behavior), `docs/plugins.md`.
- Live vault: `~/bob/dash.md` (chips + TODAY/NEW/PENDING/NEXT/READY
  sections), `~/.config/bob/config.yml` (`plan:` block), `bob_gtd.md`
  (the pre-existing `^prj-task-count-warn` task — this request restates it).
- Live commands: `bob capture-targets -f json` (54 routable notes, kinds
  `inbox`/`area`/`project`), `bob projects list` (OPEN vs SHOWN columns),
  `bob freshness list`, `bob query --tasks`, `bob plan`.
- Rust sources: `src/native/capture_targets.rs`, `src/native/projects/scan.rs`
  (`frontmatter_is_area` = `type: [[area]]`, project = `type: [[project]]`),
  `src/native/projects/output.rs`, `src/native/note_tasks.rs`.
- I did **not** open the `bob-plugins` repo (Obsidian keymap/plugin
  internals below are inferred from `docs/projects.md` + `dash.md` and are
  flagged where they need plugin-side confirmation). I did not seek out any
  peer swarm report.

## 2. Key facts the design must respect

1. **"Ready" already has a precise meaning.** `dash.md#READY Tasks` is:
   `status.type is TODO`, not in `_templates`/`_conflicts`, no `#hide`,
   not a Today task, and freshness `bucket === null` (confirmed, not
   NEW/ROTTEN). The dashboard additionally excludes `dash.md` itself,
   dependency-blocked tasks, and future-scheduled tasks (`docs/plan.md`
   §READY). Any per-note "ready count" that disagrees with this predicate
   will confuse the morning review — the count in the note must add up to
   the count on the dash.
2. **SHOWN vs OPEN vs READY.** `bob projects list` already computes two
   per-project counts: OPEN (open non-hidden tasks) and SHOWN
   (dashboard-visible: open, non-`^prj`, non-hidden `#task`, not `[?]`, not
   future-scheduled). SHOWN is close to per-note READY but **includes**
   NEW/ROTTEN (unconfirmed) tasks and **excludes** Today handling. It is
   fully native (no Obsidian API needed) — the pragmatic v1 counter.
3. **Native fallback rule.** Per `docs/freshness.md` §7, when the Obsidian
   freshness/Today API is missing, dash shows `–`, never a silent zero.
   A CLI/Obsidian per-note counter must do the same: `–` when Today or
   bucket state is unprovable, not `0`.
4. **Routable scope already exists.** `capture-targets` = top-level
   `*.md` with `type: [[area]]` + non-terminal `type: [[project]]` notes
   (+ pinned `mac_inbox`). That is exactly the "area/project note file"
   population the user means — reuse it, don't invent a second roster.
   Live vault: 12 areas + ~40 active projects.
5. **Cap philosophy is settled: soft limits.** `max_ready` over-cap is a
   red badge + lint line, never a refused write (`docs/plan.md`); only
   `plan.strict` refuses, and only new themes. A per-note cap that
   **blocks** moves would be the first hard WIP limit in the system and
   would break the "capture first, triage later" inbox flow.
6. **Keymap ownership is split.** `Ctrl+Shift+P` (property/priority/schedule
   rolls + Blocked reconciliation), `Ctrl+Shift+M` (move to project),
   `Ctrl+Shift+Enter` (link Next), `Alt+N` (release), `Ctrl+D` (clear
   property) live in `bob-navigation-hotkeys` / ledger-tools, with
   `bob capture`, `bob projects sync`, `bob task-status-hooks` as CLI
   counterparts. Any toast/badge work is a **two-repo change**
   (bob-cli counter + bob-plugins UI) joined by a versioned
   ledger-tools API, exactly like the freshness rollout (`api.freshness` v3).
7. **The `^prj` lifecycle task must never count.** It is machine surfacing
   (`#hide` toggled by `projects sync`), not pullable work. SHOWN already
   excludes it; any new counter must too.

## 3. Critique: is this a good idea?

**Yes — with three caveats.** The strengths:

- It closes the loop between capture convenience (one keypress to file a
  task anywhere) and GTD's project-support horizon (a project with 15
  next-actions isn't a project, it's a backlog wearing a trench coat).
  Bryan already intuited this: `^prj-task-count-warn` predates this request.
- N = 5 is a defensible default: small enough to force the
  split-or-deprioritize decision, large enough that ordinary projects
  (`bob`: SHOWN 11 — already over, correctly! — vs `sase_decks`: 0) don't
  all scream at once. Spot-checking live SHOWN values, a cap of 5 flags
  roughly the notes a human would also flag.
- All four requested surfaces (keymap toast, dash diagnostics, per-note
  badge, CLI) mirror proven surfaces (plan meters, READY badge, freshness
  marks), so the design language already exists.

The caveats (each becomes an adjustment in §4):

1. **Notification fatigue is the #1 killer.** A toast on *every*
   `Ctrl+Shift+P` press that leaves a note over budget will train Bryan to
   dismiss it within a week — especially since legitimate states (weekly
   review in progress, pre-split project) sit over budget for days.
   Toast only on transitions that *increase* the destination count past N,
   dedupe per note per day, and never modal.
2. **The metric will be gamed, including by existing automation.**
   `projects sync` itself adds/removes `#hide`; a user (or a future agent)
   silencing the badge with `#hide` is one keystroke away. Treat the number
   as a *triage hint*, and consider counting `#hide` tasks in a dimmed
   "hidden N" suffix so hiding doesn't look like progress.
3. **Areas and projects need different defaults in practice.** An area
   (`job`, `cash`) legitimately aggregates; a project should stay tight.
   One global N will either nag on areas or sleep on projects. Per-kind
   defaults (or the per-note override) are not gold-plating, they're the
   difference between trusted and muted.

**Alternatives considered:** (a) *Weekly-review query only, no toasts* —
cheaper, arguably 80% of the value, and my recommended phase 1 if budget
is tight; (b) *lower the global `max_ready`* — wrong layer, punishes all
notes for one bloated note; (c) *auto-split projects* — too clever,
destroys the human judgment this ritual is for; (d) *hard block over-cap
moves* — rejected, violates the soft-limit philosophy and the inbox flow.

## 4. Adjustments to the requirements (explicit)

1. **Define "ready" as dashboard-READY-per-file** (§2.1), not "all open
   `[ ]` lines." Raw open counts punish un-triaged NEW tasks and duplicate
   the existing OPEN column. If the full predicate (Today + freshness
   bucket) is too costly natively, v1 may count the SHOWN predicate and
   must label itself `SHOWN-based (incl. unreviewed)` until v2.
2. **Split N by kind:** `max_per_area_note` (default 8) and
   `max_per_project_note` (default 5), plus per-note `task_budget: N`
   frontmatter override. The request's single N becomes the project
   default; areas get headroom.
3. **Toast only on crossing the threshold upward**, only for gestures that
   *add* ready work to a note (`Ctrl+Shift+M` move, capture routing,
   unschedule/unblock via `Ctrl+Shift+P`, `Ctrl+D` on priority/schedule):
   "now N+1 over." Pure edits inside an already-over note stay silent.
   One notice per note per day; always with the two action hints
   (split-project via `Ctrl+Shift+Opt+N`, de-prioritize via
   `Ctrl+Shift+P`).
4. **Soft everywhere.** No gesture is refused, no status is auto-changed,
   no `#hide` is auto-added. Unknown/unavailable counts render `–`.
5. **Scope = routable set minus inboxes/dailies** (`capture-targets`
   roster, excluding `mac_inbox`, `inbox`, `gkeep_inbox`, daily notes,
   `done/`, templates, conflicts). Recurring tasks excluded (they're not
   READY-eligible scope per `docs/freshness.md` §4).

## 5. Recommended solution

### 5.1 Config (`~/.config/bob/config.yml`)

```yaml
ready:
  max_per_project_note: 5  # over-budget project notes get badge + lint
  max_per_area_note: 8     # areas aggregate; headroom per §4.2
  # per-note override lives in that note's frontmatter:
  # task_budget: 3
```

Validation mirrors `plan:` — integers ≥ 1; `bob ready` exits 2 on invalid,
all other surfaces fall back to defaults with a one-time warning
(established pattern, `docs/plan.md` §Config).

### 5.2 CLI: `bob ready` (new, read-only)

Human table reuses the `projects list` + plan-meter idioms (sorted by
kind then name; red over-cap rows only on TTY):

```text
bob ready · Thu 2026-10-01 · 12 areas · 41 projects · cap P5/A8

  NOTE                KIND     READY  CAP  STATUS
  bob                 project   11     5   🔴 over by 6
  sase                project  124*    5   🔴 over by 119 (SHOWN-based)
  job                 area       6     8   ok
```

(`*` marks SHOWN-based fallback rows while v1 lacks native Today/bucket
state; JSON carries `"basis": "ready" | "shown" | "unavailable"` per row
so scripts never mistake a fallback for a measurement.)

- `bob ready -f json` → `{ok, date, caps, notes: [{path, kind, ready,
  cap, over_by, basis}], over: [...], warnings, schema_version: 2}`.
- `bob capture … @route` gains one warning line when the routed note
  would cross its cap (`→ bob (READY 12/5 — consider splitting)`),
  never a refusal. `bob task-status-hooks` summary gains the same
  one-line over-budget list (it already prints the plan meter).

### 5.3 Obsidian: toasts, dash, per-note badge (bob-plugins side)

- **Toast:** in the guarded editor transaction *after* a move/write that
  raises the destination note from ≤N to >N, one
  `Notice("📥 bob: 7 ready (cap 5) — split (Ctrl+Shift+Opt+N) or de-prioritize (Ctrl+Shift+P)")`.
  Needs a ledger-tools `api.ready.budgetByNote()` (+ `basis`) so the
  hotkey code never re-implements the predicate (placement rule precedent:
  `docs/freshness.md` §5 — one helper per language, call sites stay thin).
- **dash.md:** a compact `### Over budget` dataviewjs/Tasks group under the
  chips listing `note — READY n/cap`, reusing `.task-count-chip` +
  `.task-count-over` styling; empty state renders nothing (not `0`).
- **Per-note:** a `bob-ready` code block (same renderer family as
  `bob-plan`) showing `READY n/cap`, red when over, `–` when unavailable;
  click-through to `dash#READY Tasks` filtered to that note.

### 5.4 Beauty notes (this request asks for beautiful)

- One glyph language everywhere: `✓`/green within cap, `🔴`/red + "over
  by N" past it, `–` for unknown — the exact plan-meter semantics, so no
  new visual vocabulary to learn.
- Counts are right-aligned tabular numerals; note names link to the note;
  tooltips carry the composition (`READY 12/5 · lane …`) like the READY
  badge's whole-lane tooltip.
- Morning-review framing: the dash section is titled as a question
  ("Split or shelve?") with the two keypress hints inline, so the toast
  teaches the ritual instead of just nagging.

### 5.5 Rollout (phased, each shippable alone)

1. **CLI + config** (`bob ready`, `ready:` block, capture warning) — all
   in this repo; proves the predicate and gives Bryan the morning view
   immediately.
2. **ledger-tools `api.ready`** + dash over-budget section (needs the
   freshness `bucket` + `isToday` composition per file — the only genuinely
   new computation).
3. **Keymap toasts + per-note badge** (thin call sites on the v2 API).
4. Revisit defaults after 2 weeks of live over-budget lists (my priors:
   P5/A8 will need per-note `task_budget` on ~5 notes like `sase`/`bob`).

### 5.6 Edge cases & falsifiability

- `^prj` task, `#hide`, `[?]`-blocked, future-scheduled, Today-linked,
  recurring, done/canceled: never counted (SHOWN already handles most;
  full READY handles all).
- Multi-`scheduled` malformed lines: counted as-is, surfaced via existing
  `projects sync` warnings — the counter never "fixes" lines.
- Missing/stale Today or bucket state → `–` + `unavailable`, never `0`.
- Success criterion: after phase 1, `bob ready -f json | jq .over` names
  the same notes the morning review would have flagged by hand; after
  phase 3, zero dismissed-notice complaints for a fortnight (ask Bryan).

## 6. Open questions for the lead / Bryan

1. Is SHOWN-based v1 (includes NEW/ROTTEN) acceptable labeled, or must v1
   wait for native Today+bucket per file? (Needs plugin-side confirmation
   of `api.ready` cost.)
2. Should areas be in scope at all, or projects-only with areas as
   silent? I recommend in-scope with A8; Bryan's morning flow decides.
3. Toast copy + dedupe window (per-note per-day?) — taste call, needs
   Bryan's noise tolerance.

## Sources

`docs/plan.md` (READY/plan-budget), `docs/freshness.md` (§4 scope, §7
fallback, §8 surfaces), `docs/projects.md` (SHOWN def, `^prj`/`#hide`
surfacing, `Ctrl+Shift+P`/`Ctrl+D`), `dash.md` chips + READY/NEW/ROTTEN
sections, `~/.config/bob/config.yml` (`plan:`), `bob capture-targets -f
json`, `bob projects list`, `bob freshness list`, `bob query --tasks`,
`src/native/capture_targets.rs`, `src/native/projects/{scan,output}.rs`.
