# Daily intentions: do we need them, what to call them, and how to add them

Research report — daily planning layer (the proposed counterpart to weekly
Intentions / quarterly Outcomes / yearly Theme). Independent swarm contribution.

## TL;DR

- This is a **good idea with a real gap behind it**, but about 70% of the
  proposed machinery **already exists** under other names. What is genuinely
  missing is a small, Bryan-authored, slow-moving statement of the day's bets
  that survives intraday ledger churn and can be scored the next morning.
- **Do not call it "commitments."** The word is taken — twice. Recommend
  **`## Intentions`** in the daily note (parallel with the week), capped at
  **≤3**, or `## Focus` if Bryan wants a distinct word.
- **Do not put date-specific content in `gtd_daily.md`.** That file holds
  recurring chores, not dated content. The habit ("set today's intentions")
  belongs there as one PRE row; the content belongs in the daily note.
- **Do not build a new limit.** Four commitment-limit mechanisms already run
  (plan link budget, lane caps, highlight ≤3, per-note Ready cap). A fifth
  would duplicate them and violate the ownership rule that planning sections
  belong to Bryan, not to tools.
- Recommended v1 is deliberately small: one Bryan-owned daily-note section, one
  PRE chore row, one morning-review sentence, no new automation. Details in
  §6.

## 1. What already exists at each scale

The current stack, verified against the tree on 2026-11-17:

| Scale | Planning artifact (Bryan-owned) | Review (agent-drafted) | Cap / limit already enforced |
| --- | --- | --- | --- |
| Day | *none* — this proposal | none | plan link budget (here 13; `PLAN 10/13` live), PENDING 8 / NEXT 13 lane caps with lints, highlight ≤3 themes, per-note Ready cap 5 |
| Week | `## Intentions` (e.g. W47 lists 3, each ending `!`) | `## Review` ≤250 words, scores each Intention ✓/◐/✗ | Carried-forward ≤3 items (callout rule) |
| Quarter | `## Outcomes` ≤3 (Q4 currently has exactly 3) | `## Review` ≤400 words, scores each Outcome | ≤3 by convention |
| Year | `## Theme` + `## Outcomes` | `## Review` ≤600 words | ≤3 Outcomes by convention |

Ownership is load-bearing (`docs/periods.md`, "Note anatomy and ownership"):
frontmatter/nav/fences/callout belong to bob; strips and parts tables belong
to bob-ledger-tools; **`## Review` belongs to an agent via `bob periods
draft`; `## Intentions` / `## Outcomes` / `## Theme` / `## Reflection` belong
to Bryan — no tool or agent writes them.** Any daily design must preserve this:
a tool must never author, edit, or "enforce" the new section's content.

The daily layer is not empty today. Three mechanisms already do daily-commitment
work:

1. **Today + the Pomodoro ledger** (`docs/concepts/today-and-the-pomodoro-ledger.md`,
   `docs/plan.md`). Today is the open tasks with a dedicated Task Link under
   today's open Pomodoros, computed at read time — never a tag, field, or
   folder. Linking is commitment: a Ready task linked into today is promoted
   to Next (sticky), and unlinking never releases it.
2. **The morning `]s` walk** (`docs/freshness.md` §§4/7). The walk visits
   PRE → NEW → PROJECTS → PENDING → NEXT → RECURRING → TICKLER, then ROTTEN as
   upkeep and POST as closeout. The notice literally says **"Commitments
   done"** at the TICKLER boundary; then Bryan clears CROWDED to 0 and picks a
   **highlight of ≤3 themes, highlight first**. The live morning-review row in
   `gtd_daily.md` confirms this is current practice.
3. **Budgets and caps** (`docs/plan.md` lints; live `bob plan` output on
   2026-11-17 shows `PLAN 10/13 links · TODAY 11 · PENDING 11/8 · NEXT 9/13`
   with a `pending_cap_exceeded` warning). The link budget, the two lane caps,
   the highlight rule, and the per-note Ready cap (`plan.max_ready_per_note`,
   default 5) are four independent commitment limiters.

So the honest framing is not "daily files have nothing" but "daily files have
selection machinery (Today), pacing machinery (caps, highlight), and review
machinery (the walk) — but no authored statement of intent."

## 2. The actual gap

Today churns. Sessions open and close, links are added and consumed, reconcile
rewrites the ledger, and by evening Today says what is *currently* linked, not
what the morning decided mattered. Session history (closed entries) records what
was planned, but it mixes plan with log and buries the signal: eleven Today
tasks across six roots (as in today's live plan) is a schedule, not a thesis.

What weekly Intentions give the week — a short, stable, authorial "these three
things are the bet," written before the work and scoreable after it — has no
daily counterpart. That is the whole gap, and it is narrow: persistence plus
authorship plus next-morning scoreability. Everything else (selection, limits,
review ritual) exists.

## 3. Naming: why "commitments" is the wrong word

Three candidate names were weighed against the vault's existing vocabulary:

- **"Daily commitments" (proposed). Recommend against.** "Commitment" already
  has two precise, load-bearing meanings: (a) the walk's commitment tiers and
  the "Commitments done" boundary notice in `docs/freshness.md` ("The
  commitment tiers are PRE, NEW, PROJECTS, PENDING, NEXT, RECURRING, and
  TICKLER. They sit before the Commitments done boundary"), and (b) lane
  commitment via Alt+N / linking ("Linking a Ready task under today's open
  Pomodoros, or Alt+N commit"). A third meaning — an authored list of daily
  bets — would collide with both in exactly the documents and keymaps where
  precision matters most. Every future sentence like "commit your commitments"
  is a bug report waiting to happen.
- **"Intentions" (recommended).** Parallel with `## Intentions` on the week
  note: same word, same ≤3 shape, same scoring grammar (✓/◐/✗), one smaller
  scope. Lowest learning cost; the weekly agent callout already teaches Bryan
  the genre. The only cost is mild ambiguity between "week intentions" and
  "day intentions," resolved everywhere by the note that holds them.
- **"Focus" (acceptable alternative).** Distinct word, no collisions, matches
  the highlight concept ("highlight chosen (≤3 themes, highlight first)").
  Costs a second vocabulary item for the same genre at two scales.

Recommendation: `## Intentions` on the daily note. If Bryan dislikes reusing
the word, `## Focus` — not "commitments."

## 4. Constraints and policies: what is needed, what already exists

**A commitment limit.** Not needed as new machinery. Four limiters already
bind the day (see §1 table), and they operate at the right layers: the plan
budget limits *selection breadth*, lane caps limit *sticky commitment stock*,
the highlight limits *thematic breadth* (≤3), and the Ready cap limits
*per-note backlog*. A fifth cap on the intentions list itself should be
**convention (≤3, matching the week), not code**: the section is Bryan-owned
prose, and a lint that nags Bryan about his own planning section inverts the
ownership rule. If a number is wanted anywhere, the cheapest honest one is
display-only — e.g. `bob plan` echoing an intentions count — and even that is
v2, not v1 (plan reads the ledger, not note sections; wiring section reads
into it crosses a clean architectural line for little benefit).

**A daily task in `gtd_daily.md`.** Half right, half wrong — split it:

- *Wrong as content home.* `gtd_daily.md` is a recurring-chore file
  (`repeat:: every day when done`, `every week on Monday…`). A row written
  there recurs forever; date-specific intentions would either repeat daily
  (wrong) or need one-off rows (clutter in a file whose morning walk walks
  every row). The existing morning-review row already walks the reviewer to
  "Commitments done," proving the file is a *ritual checklist*, not a journal.
- *Right as habit home.* The habit needs exactly one PRE row: "Set today's ≤3
  intentions in today's note." That is the correct shape for this file, and it
  makes the practice part of the walked ritual instead of a second system to
  remember. Likewise, extend the morning-review row's "highlight chosen (≤3
  themes…)" clause to reference the intentions, or let the new PRE row carry
  it — one place, not two.

**A scoring/reading policy.** This is the proposal's weakest point as stated:
weekly Intentions work because the weekly Review callout *reads* them (the
agent must score each one). Daily intentions would have **no reader**: there is
no daily Review, no `brief` for days, and the weekly callout's fixed part-list
(Headline / Intentions / Shipped / Where-the-time-went / Carried-forward /
Questions) has no slot for them. An unread section is write-only, and
write-only sections die. The policy must name the reader before the section
ships (§6 names two: tomorrow-morning Bryan, then optionally the weekly agent).

## 5. Critique: is this a good idea?

**Yes, with the scope cut in §4.** The GTD analogue is solid — "3 MITs"
(Zen to Done) and the "daily big three" are among the few productivity
practices with durable cross-system consensus, and Bryan's stack is unusually
well prepared for it: the week/quarter/year layers prove the genre works for
him (W47's three `!`-marked intentions; Q4's three outcomes), and the highlight
rule shows ≤3 is already his number. The gap in §2 is genuine.

Adjustments and warnings:

1. **Burden is the top risk.** The morning ritual is already long (PRE chores,
   `]s` walk to Commitments done, CROWDED to 0, highlight, ROTTEN upkeep).
   Every added PRE row taxes a ritual whose completion rate is the system's
   load-bearing metric. Keep the addition to *one row, one section, zero new
   tools* — and say explicitly that an empty intentions section on a
   reactive day (travel, outage, sick) is legitimate, not a failure. Consider
   seeding the section from the highlight rather than writing from blank.
2. **Do not conflate intentions with Today.** The most likely failure mode is
   treating "3 intentions" as "3 Today links." They are different dimensions
   (cf. `docs/concepts/tasks-and-lanes.md`: "Lane, Today, freshness state, and
   review tier are different dimensions"). An intention can name an outcome
   with no task yet, span several tasks, or deliberately exclude an urgent
   task that still earns Today links. If intentions must link tasks, they link
   — they never move, copy, or restate them.
3. **No automation in v1.** Auto-seeding from yesterday's unfinished Today,
   auto-carry-forward, or a cap lint would each violate Bryan-ownership,
   duplicate the decay ladder's consented-keep logic, or both. The decay
   ladder (`decisions:task-decay-is-one-ladder`) already handles "kept but
   unfinished" with consent; do not build a parallel forgetting machine.
4. **Template mechanics need care.** Daily notes are canonical (`YYYY/…md`,
   parented to the week) and Templater-adjacent; adding a scaffold section
   means changing the daily template plus a decision about backfill (recommend:
   no backfill — absent section means "predates the practice," and any reader
   must treat absence as neutral, never as failure).
5. **Weekly Review consumption is a later, gated change.** Teaching the weekly
   callout to read seven days of intentions changes the agent bundle, the word
   cap (250 is already tight), and the brief. Do not bundle it with v1; run
   the practice manually for a few weeks, then decide if the agent needs it.

## 6. Recommended solution

**v1 — practice first, no new code:**

1. **Section.** Add a Bryan-owned `## Intentions` section to the daily-note
   template (position: after the day's frontmatter/nav, before `## Events` —
   intent precedes schedule), with convention **≤3 bullets**, each one line,
   plain language first with optional `[[task#^block]]` links after it. Never
   task rows. Absent section = predates practice or a reactive day; both are
   fine and no tool may flag them.
2. **Habit.** Add one PRE row to `gtd_daily.md`: "Set today's ≤3 intentions in
   today's note (reactive day? leave empty)." Append "intentions set" to the
   morning-review row's checklist sentence so the existing walk enforces it.
3. **Reader.** Next morning, Bryan scores yesterday's intentions informally
   (✓/◐/✗) while the walk is in TICKLER — no written record required. After
   3–4 weeks, decide whether to (a) keep it manual, (b) add a weekly-callout
   line letting the agent cite daily intentions as context (not scored parts),
   or (c) drop the practice.
4. **Explicit non-goals for v1:** no `bob` command changes, no new lint or
   cap, no `periods brief/draft` for days, no backfill, no callout changes.

**Deliberate deviations from the request, called out:** (i) name is
Intentions, not commitments (§3); (ii) no numeric commitment-limit mechanism —
convention ≤3 only, existing caps already bind (§4); (iii) `gtd_daily.md` gets
the habit row, never the content (§4); (iv) no daily Review/draft flow — the
reader is tomorrow-morning Bryan, not an agent (§4–§5.5).

**Open questions for Bryan:** (a) Intentions or Focus? (b) Should an intention
be allowed to be purely thematic ("a writing day") with no task links, or must
each name at least one task? (Recommend: allowed — outcomes often have no task
yet.) (c) After the trial, is weekly-agent visibility worth the callout cost?

## Sources checked

- Live vault state 2026-11-17: `2026-W46`/`2026-W47` Intentions, `2026-Q4`
  Outcomes (3), `2026` Theme/Outcomes, `2026/20261115.md` ledger anatomy,
  `gtd_daily.md` morning-review text, `crowded.md`, `rotten.md`, `gtd.md`.
- Live `bob plan` output (`PLAN 10/13 · TODAY 11 · PENDING 11/8 ·
  NEXT 9/13` + `pending_cap_exceeded`).
- `docs/periods.md` (ownership, caps, callouts), `docs/plan.md` (budget,
  Today, lanes), `docs/concepts/today-and-the-pomodoro-ledger.md`,
  `docs/concepts/tasks-and-lanes.md`, `docs/freshness.md` §§4/7 (walk,
  "Commitments done," highlight ≤3).
- Memory: `decisions:task-lanes-are-sticky`, `decisions:today-is-read-from-the-ledger`,
  `decisions:ready-is-freshness-gated`, `decisions:review-walk-is-tiered`;
  glossary `period-note`, `pomodoro`, `task-freshness`, `task-link`.
- Prior research directories listed for orientation only; no peer report from
  this swarm was opened or read.
