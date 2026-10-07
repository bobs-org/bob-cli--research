# Task-bead impact audit: created or +1ed in the last 48h

Researcher: mus (`__mus`). Independent swarm report; no peer reports consulted.

- Window: 2026-10-05 ~16:24 UTC → 2026-10-07 ~16:24 UTC (48h ending at audit time).
- Method: `sase bead list --since 2d --status all` (96 beads) plus a full-store
  scan of `plus_one_evidence` timestamps for older beads with +1s inside the window
  (23 +1 events on 9 distinct beads, 6 of them created before the window).
- In-scope set: **102 distinct beads** = 96 created in-window + 6 older beads
  pulled in via in-window +1s (`bob-cli-40`, `bob-cli-3c`, `bob-cli-3w`,
  `bob-cli-21`, `bob-cli-2e`, `bob-cli-33`).
- Composition of the 96 created: 12 plans (epics), 59 phases, 25 tasks;
  73 closed, 22 ready, 1 in progress (`bob-cli-52`).
- Impact model: breadth of who benefits (Bryan's daily workflow > agents >
  infra), depth (new capability > correctness/security fix > CI-signal fix >
  polish/docs), corroboration (+1 count), and leverage (small fix unblocking many).
- Top-10 candidates were re-verified with an audited `sase bead read`.

## Ranked top 10

### 1. `bob-cli-52` — Links go to the reading queue (in_progress epic)
URL routing for `bob capture`, Bob Mac Capture, and `bob gkeep pull`. A bare
public link becomes a reading-queue reference through a durable background ref
job instead of an inbox task; capture stays instant, offline-safe, and never
loses a link, with an inbox-task fallback plus retry command on clip failure.
Spans three intake surfaces, a new spool/worker subsystem (`bob ref jobs`), and
Mac presentation. It is the only in-progress epic in the window — the largest
live architectural change and the highest leverage/risk item: landing quality
here decides whether Bryan's read-it-later pipeline is trustworthy.

### 2. `bob-cli-4w` — `bob ref`: a reference library for agents and Bryan (closed epic)
Canonical `find`/`list`/`show` over the reference library with honest coverage,
unchanged Highlights verbs under aliases, marker-mirror cleanup, and a deployed
`bob_ref` skill making "check the library first" the default agent step. This is
the foundation `bob-cli-52` and all six ref follow-ups (`4x`–`51`) build on;
without it there is no library to route links into or search.

### 3. `bob-cli-4i` + `bob-cli-4i.7` — Complete any open task from capture (closed epics)
Whole-item `!note:block-id` marks open tasks Done with atomic subtask close,
ledger retirement, and dependent unblocking, plus a Mac Complete picker with
Today-first ordering and completion previews. Closes the capture→completion loop
the way `=x` closes the Pomodoro loop — a new daily-driver grammar, delivered
across two epics and eleven phases.

### 4. `bob-cli-21` — Artifact-link store rejects every new link (ready, +5)
One reused `operation_id` bricks **all** `sase artifact link` writes and now
crashes `sase plan propose` *after* it consumes the scratch file — a
whole-store validation failure with a data-loss-adjacent proposal path.
Reproduced three times inside the window. Oldest bead on this list (26d) and the
most infrastructurally urgent: a single bad historical pair blocks every future
link and every tale proposal with a links inlet.

### 5. `bob-cli-4s` — `bob highlights create --listen` and every sase-listen target (closed epic)
Every `sase-listen` document target (Markdown, local/remote PDFs, arXiv, web
articles) becomes a marker-stamped intake PDF, with `--listen` binding a
companion audio episode and `scan` writing a ref note with a player. A new
listen-to-learn intake modality: everything Bryan listens to ends up tracked in
`ref/`.

### 6. `bob-cli-4l` — Review-walk auto-advance (closed epic)
Every gesture that answers the row `]s` landed on advances to the next review
item in the same keystroke with one toast; Alt+F stays the explicit "stay".
Touches the highest-frequency daily ritual (morning GTD review) across
Ctrl+Enter, Alt+N, Task Card, link, and move gestures — small per-gesture
savings multiplied by every review, every day.

### 7. `bob-cli-4q` — Inbox routing for Ctrl+Shift+P and Ctrl+Shift+Enter (closed epic)
Commits on inbox-resident tasks prompt for a destination first, then apply the
action and land the task in its new home, advancing the walk — morning triage
no longer needs a separate Ctrl+Shift+M. Removes a whole step from the inbox
workflow rather than speeding one up.

### 8. `bob-cli-4j` — `--audio` completion-kinds CI failure (ready, +6 in window)
One missing shell-completion decision for `highlights create --audio` fails
`every_value_arg_has_a_decision` deterministically on master — the main Rust
unit gate is red for everyone until a one-line `ValueHint::FilePath`/kinds-table
fix lands. Hottest bead in the window (6 +1s, most of any in-scope bead) because
every epic landing trips over it. Maximum leverage per line of fix.

### 9. `bob-cli-2e` — `BOB_DAY_FILE` test-mutation race (ready, +14 total)
Root-cause bead behind the `capture_pomodoros` flake class (`bob-cli-40` is the
symptom report): `with_env` mutates a process-global without the
`DAY_FILE_LOCK` that `capture_complete` already uses, and the lock is
module-private so it cannot serialize across modules. Most-corroborated bead in
scope (14 +1s); fixing it the right way (shared lock or no env mutation)
silences a whole family of parallel-suite flakes, not one test.

### 10. `bob-cli-56` — In Progress marks and the Alt+[/Alt+] lane toggle (closed epic)
Pomodoro Task Links render an amber half-ring for In Progress tasks and toggle
Next↔In Progress from the keyboard with an optional Work Log entry — nothing
ever written into the daily note. Daily-visible status legibility plus the
cheapest possible lane change, shipped across ledger-tools, navigation-hotkeys,
and task-status-cycler with docs.

## Honorable mentions (did not make the 10)

- `bob-cli-33` — Tasks JS sandbox 2s init deadline fails `freshness list` on the
  real vault (pre-existing, newly exposed). Real-vault-only breakage of a new
  command; next fix in line.
- `bob-cli-3c` — Missing canonical `just check` gate (8 +1s). Every landing
  notes it; process leverage, but it asks for a new gate rather than fixing a
  red one.
- `bob-cli-59` — Bare `bob plugins sync` from a SASE worktree deploys the
  canonical checkout (observed ledger-tools 1.34.0→1.33.0 rollback). Real
  multi-agent deploy hazard; narrower blast radius than the top 10.
- `bob-cli-58` — Markdown-PDF H1 repeat + double numbering measured across
  239/291 and 147/291 library PDFs. Visible quality defect, cosmetic.
- `bob-cli-4x` — Migrate ~424 zorg-era reading records into the library.
  Largest known completeness gap, but needs Bryan's design review first.
- `bob-cli-5f`/`bob-cli-5g` — Ref-job retries with backoff; Mac cron drain for
  `bob ref jobs run -q`. Reliability v2 for the `bob-cli-52` pipeline; sequels,
  correctly filed as follow-ups.
- `bob-cli-4o`/`bob-cli-57` — Stale mac-pom glossary strands; `bob-cli-3w` stage-ranker
  perf flake; `bob-cli-5b`/`bob-cli-5c`/`bob-cli-4u` test-infra items — real but
  narrower or docs-level.

## Scope notes

- Phase beads (59 of 96 created) were treated as parts of their parent epics,
  not ranked individually; the epic carries the impact.
- In-window +1 leaders: `bob-cli-4j` (6), `bob-cli-40` (5), `bob-cli-3c` (3),
  `bob-cli-4u` (3); all-time corroboration leader in scope is `bob-cli-2e` (14).
- Closed-but-high-impact items (`4w`, `4i`, `4s`, `4l`, `4q`, `56`) rank on the
  work they delivered in-window, not on remaining effort.
