# Near-infinite tokens for 48 hours: loopable high-value work

Researcher: `mus` (independent swarm report; peer reports not consulted).
Date: 2026-09-30. Scope: what Bryan should run in a loop
(e.g. repeated `/sase_handoff` with the same or similar prompt) during a
48-hour window in which token cost is effectively zero.

## Ground facts (observed this session)

- `bob-cli` is a Rust CLI (`cargo fmt --check`, `cargo clippy
  --all-targets --all-features`, `cargo test` via `justfile`) managing the
  `~/bob` Obsidian vault. Installed commands include `capture`,
  `capture-complete`, `capture-parse`, `freshness`, `gkeep`, `query`,
  `randomize`, `highlights`, `task-status-hooks`, `plan`, `nightly`,
  `plugins sync`, `vault-sync`, and others (enumerated from `justfile`
  `install-smoke`).
- The vault is large: 5,758 `*.md` files, ~4.3 GB on disk (includes
  PDFs/attachments), 629 top-level `.md` files with year/month notes back to
  2023. This is the single biggest token-absorbing asset Bryan owns.
- Open work ledger: 24 beads listed, 17 still open (`◇`), including live
  epics `bob-cli-31` (task freshness / rolling review lease), `bob-cli-32`
  (Work Log bullets under `=x`), `bob-cli-28` (solo `@route:id` linking),
  plus defect beads (capture_pomodoros mutation, completed-reference
  duplication, day-boundary TZ bug, clippy-warnings bead `bob-cli-v`).
- Prior research swarms exist per topic directory under
  `sase/repos/research/202609/` (only directory/file names listed, no peer
  contents consulted). Inference: the research-swarm + artifact-registration
  pattern in this prompt is itself well-supported tooling.
- SASE gives loop primitives for free: `/sase_handoff` chaining, `sase bead`
  cursors, `sase artifact create` snapshots, `bob freshness list/seed`,
  `bob gkeep pull`, dry-run capture verbs. Anything recommended below should
  be expressed as (shard cursor, idempotent unit of work, machine-checkable
  verify step, stop condition) or it will diverge when looped blind.

## What makes work worth the window

Infinite tokens do not buy judgment; they buy exhaustive passes over large
surfaces with per-unit verification. The ranking below prefers work that is:

1. Shardable (per file, per month, per command, per bead) so each handoff
   takes one shard and checkpoints a cursor.
2. Idempotent and dry-runnable first, because 48 unsupervised hours against
   a live 4.3 GB vault can do real damage.
3. Verified by a command, not by vibes (`just check`, `bob freshness
   list`, golden-file diffs, artifact snapshots).
4. Durable after the window ends (backfills, corpora, closed beads), not
   metered consumption (open-ended chat).

## Ranked recommendations

### 1. Sharded Ready-task freshness review sweep (vault backfill)

Run the freshness review over the whole vault in month-shards: for each
shard, `bob freshness list`, read each Ready task's context, and either
refresh, reword, link, schedule, or close it, recording the decision. This
directly advances epic `bob-cli-31` (rolling review lease) and converts the
token window into the scarcest resource in a PKM system: every open loop
looked at once by something with full context. Loop unit: one month-note or
one `freshness list` page. Verify: `freshness list` shrinks monotonically;
each handoff appends decisions to a per-shard log. Guard: seed/stamp only
through `bob` subcommands so the lease fields stay consistent; never
hand-edit freshness fields. Stop: all shards reviewed once, then convert to
a weekly single-shard maintenance loop.

### 2. GKeep inbox drain loop

`bob gkeep pull` in shards, triage each note into capture / task / reference
/ trash, file it via `bob capture` verbs. The vault already has a gkeep
adapter with self-test (`scripts/gkeep_adapter.py --self-test`) and CLI
coverage, so the machinery exists and only the queue is unbounded — exactly
what infinite tokens fix. Loop unit: N oldest pulled notes. Verify: pull
queue length decreases; filed items are greppable in the vault. Guard:
dedupe against existing vault content before filing (search first, file
second). Stop: inbox empty, then park as a daily cron instead of a loop.

### 3. Capture-grammar adversarial eval corpus + golden tests

Generate, parse, and lock in Adversarial capture inputs (odd punctuation,
nested task links, pomodoro names, timezone edges like the 8pm-EDT bug
`bob-cli-2q`, unicode, multi-line pastes) through `bob capture-parse` /
`capture-complete`, and promote each behavior to a golden test in `tests/`.
This hardens the `bob` contract that Bob Mac Capture (thin client) depends
on, and a corpus is valuable permanently. Loop unit: one grammar feature or
one open capture-adjacent defect bead per iteration. Verify: `cargo test`
passes and the corpus grows; each new case asserts before/after behavior.
Guard: corpus additions must fail on the old code first (red-green), or the
loop will "discover" only tautologies. Stop: coverage of every capture verb
plus regression cases for all open capture beads.

### 4. Clippy/test hardening sweep, one module per handoff

Bead `bob-cli-v` (eliminate clippy warnings) plus the known flaky/sandbox
failures (`replacement_inode_prevents_write`, `capture_pomodoros`
BOB_DAY_FILE mutation, gkeep stdin broken-pipe) are ideal loop fodder: one
warning class or one test file per iteration, each ending with `just check`
(or the scoped `cargo test <file>` + clippy). Loop unit: single lint class
or single test target. Verify: warning count strictly decreases per
handoff; no new warnings introduced. Guard: no behavior changes bundled
with lint fixes; keep diffs reviewable. Stop: zero warnings, all suite
green, then close the bead.

### 5. Vault link-integrity repair sweep (read-only propose, batched apply)

Walk all 5,758 markdown files in shards detecting dead Task Links, duplicated
Task Links in completed Pomodoros (cf. bead `bob-cli-2l`), orphaned block
IDs, and duplicate task text across daily notes. Each handoff emits a patch
proposal file (not direct edits); a second pass applies approved batches via
`bob` verbs or scripted edits under `vault-sync`/`vault-git-sync.md` rules.
Loop unit: one directory or letter-range shard. Verify: re-scan shows the
count of findings in applied shards at zero. Guard: proposals before edits,
vault git repo as the rollback net (note open bead `bob-cli-1g` about
untracked vault files — do not "fix" git tracking as a side effect; file it
as its own bead). Stop: full vault scanned once with findings at zero or
beaded.

### 6. Highlights/paper backfill through `bob highlights`

If Readwise/Kindle/PDF highlights predate the `highlights-ref-sync` flow,
shard by paper/book and backfill structured highlight notes with ref-sync
links. This is pure throughput work: each unit is independent, verifiable
(the note exists and links resolve), and never needs to happen again. Loop
unit: one paper or one highlights batch. Verify: `bob highlights` round-trip
and link resolution per unit. Guard: dedupe against existing highlight notes
first. Stop: backlog drained.

### 7. Docs-vs-CLI parity loop, one command per handoff

For each `bob` subcommand, diff `docs/*.md` against `--help` output and
actual behavior, and fix whichever side is wrong per `cli_rules` memory.
Boring, bounded, checkable, and it permanently reduces Bryan's support load
from his own tooling (and from the Mac Capture thin client, which depends on
documented `bob` behavior). Loop unit: one subcommand. Verify: doc claims
match `--help` and a smoke invocation. Stop: all commands in
`install-smoke` covered.

### 8. Plan/nightly output eval loop (qualityCompound)

Sample historical inputs, run `bob plan` / `bob nightly`, and score outputs
against a short rubric (Today-from-ledger correctness per decision
`today-is-read-from-the-ledger`, lane stickiness per `task-lanes-are-sticky`,
no invented `#now`). Keep passing outputs as golden fixtures; bead the
failures. This only ranks below the backfills because its value depends on
Bryan calibrating the rubric first — a 30-minute setup that should precede
the loop, not be discovered by it. Verify: fixture suite grows, failure
classes get beads. Stop: failure rate plateaus across two full passes.

### 9. Bead + memory hygiene curation (lowest token-leverage, still worth a loop)

Triage the 17 open beads (repro, dedupe, close stale), and refresh outdated
memory/skills beads (`task_types: memory`). Ranked last not because it lacks
value but because it needs Bryan's judgment at each step and consumes little
tokens — run it as a single assisted pass, not the 48-hour loop.

## Suggested 48-hour operating shape

- Hours 0–2: calibrate (freshness rubric, gkeep dedupe rule, eval rubric for
  #8), open one tracking bead per loop so cursors survive handoffs.
- Hours 2–40: run loops #1–#3 in parallel handoff chains (they touch
  disjoint surfaces: vault content, gkeep queue, test corpus). One shard per
  handoff; every handoff ends with its verify command and an artifact or
  commit-ready diff.
- Hours 40–48: verification passes only — re-run `just check`, re-scan fixed
  shards, close beads, write the one-page "what changed" note. No new
  shards in the last 4 hours; an unbounded loop must never own the deadline.

## What NOT to loop

- Vault migrations or bulk rewrites without a per-shard proposal/approve
  gate; a loop that edits 5,758 files will eventually misfire.
- `bob plugins sync` deploys or Mac Capture installs; deployment is a
  supervised act, not throughput work.
- Git history rewrites anywhere, or "fixing" vault git tracking
  (`bob-cli-1g`) / PDF policy (`bob-cli-1q`) inside another loop's diff.
- Open-ended "find insights in my vault" passes with no verify step; they
  burn the window's one advantage (exhaustiveness) on its weakest output
  (vibes). If wanted, constrain to loop #5's finding-proposal format.

## Method note

Formed independently from workspace inspection (`justfile`, `docs/`,
`src/`, `tests/`, bead ledger, vault stats). No swarm peer report or
transcript consulted; only filenames of prior research directories were
listed to avoid output collision. Rankings are the author's judgment about
durable value per unsupervised hour under a hard 48-hour deadline.
