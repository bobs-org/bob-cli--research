# Bob periodic sync: design research (`bob sync` orchestrator)

**Researcher:** mus · **Date:** 2026-11-18 · **Swarm suffix:** `__mus`
**Input material:** `research:202611/bob_sync_task_review.md` (read via
`sase artifact read`, reason: sync-command design context), live
`home/.chezmoidata.yaml` cron data, `bob-cli` source at workspace
(`src/native/nightly.rs`, `src/native/vault_sync.rs`, `src/runner.rs`,
`src/native/gcal/sync.rs`, `src/native/gmail/`, `src/native/projects/mod.rs`,
`src/native/highlights_ref/cli.rs`, `src/native/gkeep/`), `docs/` contracts,
`sase memory read cli_rules.md docs.md crontab.md`.
**Peer reports:** not consulted (per swarm instructions).

## TL;DR and recommended solution

**Do it, as a small in-process orchestrator modelled on `bob nightly`, not as
a change to `bob task reconcile`.** Ship one new top-level command with the
canonical name **`bob sync`**, a fixed step order, per-step minimum intervals
in `~/.config/bob/config.yml`, `ok / waiting / failed` per-step receipts, and
a single 15-minute cron line on the Mac that replaces four existing jobs.
Enforce the "gcal at most hourly" requirement **inside the command** (a
per-step `gcal` minimum interval, default 60m, persisted in host-local state),
not by trusting the cron schedule alone — the schedule then cannot violate
the bound even if someone re-times the tick or runs the command by hand.

Concretely:

- **Name:** `bob sync` (canonical). Keep the name short as requested. Add
  `tick` as a permanent hidden alias for cron/scripts that want an
  unambiguous spelling (`sync` reads better for the daily hand-run; `tick`
  reads better in a crontab). Help text carries one line: "for git, use
  `bob vault-sync`."
- **Steps, fixed order:** `ref-scan → projects → gmail → gcal → reconcile`,
  with `gkeep` available as a **manual-only** step (`bob sync --all` / explicit
  step args), never on the timer.
- **Cadence:** one cron tick every 15 minutes; per-step minimum intervals in
  config default to `gmail: 60m`, `gcal: 60m`, everything else due every tick;
  any step also accepts `off` (never runs, even when named explicitly the
  command explains why) and `manual` (only runs when named or via `--all`).
- **Reliability core:** no lock held across steps (each step takes the shared
  vault lock itself, as today); one lightweight `sync` run-lock so two ticks
  never overlap; per-step time budgets so a slow refs scan cannot starve
  reconcile; later steps always run after a failure; the tick exits 1 iff any
  step that actually ran failed, else 0 (`waiting` never fails the tick).
- **Chezmoi/cron:** one commit replaces `bob-highlights-sync`,
  `bob-projects-sync`, `bob-task-reconcile`, `bob-gmail-sync` with one
  `bob-sync` job (`5,20,35,50 * * * *` is fine, or `*/15`; keep the :05 offset
  so the tick does not fire exactly on the vault-sync LaunchAgent's 15-second
  boundaries more than necessary). Validate with `cronctl check`,
  `cronctl diff mac`, converge with `cronctl apply mac`, watch with
  `cronctl status --all` and `~/.local/state/cron/bob-sync.log`.
- **Docs/contract:** new `docs/` page + generated CLI reference via
  `just docs-gen`, `just docs-check`; one decision record ("Mac background
  work is one ordered `bob sync` tick"); release-train note (agents never bump
  `Cargo.toml`/CHANGELOG; mark JSON breaks with `!`).

The rest of this report justifies each clause, critiques the plan, and gives
the exact config/cron shapes I would build.

## 1. What the request asks for (and the context it inherits)

The task-review input (`bob_sync_task_review.md`, 2026-11-18, evidence: live
`cronctl` state + ~1,700 Mac cron runs over nine days + source at `f0857be8`)
frames the work as: **one `bob sync` that wraps refs scan, Gmail sync, gcal
sync, and task reconcile so the Mac needs one cron line instead of four**
(projects sync is the fifth job today and belongs in the set too). Its verdict
is "proceed, narrow scope": a `bob nightly`-style orchestrator calling
existing entry points in-process, in a fixed order, with per-step intervals.

Live state I corroborated independently in this session:

- `home/.chezmoidata.yaml` today holds exactly four Mac periodic jobs:
  `bob-highlights-sync` (`0,15,30,45`, `maybe_bob_highlights_sync -w`),
  `bob-projects-sync` (`5,20,35,50`, `bob projects sync`),
  `bob-task-reconcile` (`10,25,40,55`, `bob task reconcile --retry-timeout 120`),
  `bob-gmail-sync` (`7 * * * *`, `bob gmail sync -q`). No `gcal` job exists —
  gcal syncs once at daily-note creation plus the manual morning chore
  (`gcal sync -n 2` + `gkeep pull` + `gmail sync` in `gtd_daily.md`).
- `~/.config/bob/config.yml` (chezmoi-managed) currently pins `gcal.writer`
  commented out (unset: any host may write) and `gmail.writer` commented out,
  with `gmail.sync` carrying `route_prefixes`, `reply_wait_days: 3`,
  `archive: on`. The `freshness.pre_stages` already contain a `sync` stage.
- CLI surface: there is **no top-level `sync`** in `src/runner.rs`
  (`SUBCOMMANDS` has `vault-sync` plus per-noun `sync` subcommands under
  `albums`/`areas`/`notebooks`/`projects`, and `ref scan|sync`, `gcal sync`,
  `gmail sync` as leaf subcommands). So a top-level `bob sync` is free, but
  the word is heavily loaded — §3 resolves this.
- The `nightly` precedent (`src/native/nightly.rs`, 402 lines) is exactly the
  shape to copy: a `Step { name, blurb, run: fn(&ChildEnv) -> i32 }` table,
  box-drawing section headers via a tiny `Styler` (color only on TTY, structure
  from glyphs + ✓/✗, never color alone), per-step footers, a summary, and
  "first nonzero exit wins" aggregation. `vault_sync::run_cycle_with_existing_lock`
  shows how a wrapped step reuses the existing lock holder.
- Locking reality: `src/native/ob.rs` exposes `acquire_lock`,
  `acquire_lock_quiet_if_held`, `try_acquire_lock`, and `acquire_lock_waiting`
  (bounded wait with jittered backoff); the shared lock path is
  `$BOB_VAULT_SYNC_LOCK_FILE` (`$XDG_RUNTIME_DIR/bob_sync.lock`, else
  `/tmp/bob_sync.lock`). `bob nightly` holds that lock for its whole run;
  copying that for a 15-minute tick is the main hazard the review identifies,
  and I agree: **do not hold the outer lock**.
- Per-step entry points already exist in-process: `nightly_step` helpers for
  `areas`/`projects`/`notebooks`/`albums`, `vault_sync::run_cycle_*`,
  `collect_done`, gcal `run(&SyncArgs)` (`src/native/gcal/sync.rs`), gmail
  sync CLI, `task reconcile` (`src/native/task_status_hooks/`), `ref scan`
  (`src/native/highlights_ref/`). The orchestrator is glue, not new sync
  logic — this is why the change is small-to-medium, not large.

## 2. Critique: is this a good idea?

**Yes — with the narrow scope, and with two requirement adjustments (§9).**
The three wins from the review hold up against the code I read:

1. **gcal gets a real periodic sync for the first time.** `docs/gcal.md`
   admits "no periodic sync"; the writer pin (`gcal.writer`) and the
   missing-note `waiting` path (`sync.rs` returns exit 0 with a reason + hint
   while the note is missing, has no `## Pomodoros`, or still has Templater
   tags) already encode the safe shape. A 15-minute tick with a 60-minute
   per-step gate is strictly more current than "once at note creation," and the
   `-n 2` (yesterday + today) default the review proposes costs one extra day
   of Google fetches per run — negligible against the "one pass per span of
   consecutive days" fetch structure.
2. **Order becomes real instead of minute-offset folklore.** The chezmoidata
   comment says gmail runs at :07 "so reconcile tidies the same rows minutes
   later" — but offsets are not ordering under sleep/wake pile-ups (the review
   cites a 21:27:39Z double-start). In-process sequencing (`gmail → gcal →
   reconcile` last) guarantees what the offsets only hope for.
3. **Noise drops.** The failure census (50× missing-daily-note reconcile
   failures, ~10 lock-contention failures out of 78) maps exactly onto code I
   verified: reconcile fails hard when the current daily note is missing or
   lock-busy, while gcal already treats the same situation as `waiting`/exit 0.
   Extending the `waiting` treatment to reconcile-inside-sync plus removing
   inter-job contention eliminates ~77% of mailed failures without hiding any
   real error — provided `waiting` stays exit 0 and stays out of the mailed
   tail (cronrun mails only failures; see below).

Counter-arguments I weighed and where they land:

- **"Not urgent; everything succeeds >90%."** True, and a reason to keep the
  diff small — not a reason to keep four jobs. The cost of *not* doing it is
  permanent: every future periodic step (gkeep? bank? new integrations) either
  becomes job N+1 with its own offset superstition or gets hand-run forever.
  One orchestrator with a registration-one-line step table (`nightly.rs`
  `STEPS` is the template) pays for itself on the second addition.
- **"You lose per-job off switches."** Only if intervals are global. Per-step
  `off`/`manual`/duration values preserve — and improve — today's
  `cronctl`-level toggles, because they travel with the vault config instead
  of living in four cron lines.
- **"One exit code hides which step broke."** Only for a naive aggregator. The
  nightly-style per-step lines plus a `-f json` receipt (one object per step:
  `ok|waiting|failed + reason + duration_ms`) is strictly more diagnosable
  than four interleaved log files. Keep the aggregation rule dumb and
  documented: **exit 1 iff a step that ran returned nonzero.**
- **The genuine risks** are the three the review names (outer lock, slow-step
  starvation, merged exit codes), plus one I add: **config complexity creep.**
  A "highly configurable" sync can easily become a second cron language
  (arbitrary step lists, user ordering, per-step flags). The design in §4
  deliberately refuses that: fixed order, a closed step set, intervals only.
  Flexibility lives in *when/how often*, never in *what order* — ordering is
  the correctness property.

**What I would not do:** grow `bob task reconcile` into the syncer (the
superseded Keep idea). CLI rules reserve `bob task <verb>` for vault-wide
task-line rewrites; read-only reports stay top-level, and reconcile's
`--retry-timeout` budget (default 120s, bounded jittered backoff in
`task_status_hooks/retry.rs`) is tuned for lock/data races, not network
calls. Mixing Gmail/Google failures into that budget corrupts both meanings.

## 3. Naming: is `bob sync` right?

Short answer: **yes, keep `bob sync` as the canonical name** — but register
`tick` alongside it as a hidden alias, and disambiguate from `vault-sync` in
help. Reasoning, with the alternatives scored honestly:

### Constraints from the repo

- `cli_rules.md`: `-h/--help` excellent; options alphabetical with short
  aliases; subcommands alphabetical within help sections; sections follow the
  daily workflow; never hard-rename (old spellings become permanent hidden
  aliases); never add under `bob capture`; bare-group defaults only for
  flag-only read-only members (`vault-sync` bare=`run` is the grandfathered
  exception and must stay labelled).
- Namespace today: top-level nouns include `nightly` (Vault section),
  `vault-sync` (Vault), `ref` (Vault), `projects` (TasksAndProjects), `gcal` /
  `gmail` / `gkeep` (Integrations). No top-level `sync`. Subcommand `sync`
  exists under five nouns — so `bob sync gmail`-style step selectors collide
  *textually* with `bob gmail sync`, which argues for keeping the orchestrator
  flat (`bob sync gmail gcal`, like `nightly`'s flat design, not `bob sync run
  gmail`).
- The morning chore, the task name (`^bob-sync`), and `pre_stages: [sync]`
  already say "sync". Discoverability for the daily hand-run matters more than
  novelty: Bryan will type this name every morning.

### Candidates

| Name | Len | Discoverable | Collision-free | Says "periodic" | Says "ordered pass" | Verdict |
| --- | --- | --- | --- | --- | --- | --- |
| `sync` | 4 | yes (task, chore, stages) | weak (`vault-sync`, 5× subcommand `sync`) | no | no | **canonical** — wins on typing + history; fix collision in help, not by renaming |
| `tick` | 4 | medium | yes (unused) | **yes** (one tick per 15 min) | no | **hidden alias** — perfect cron spelling: `bob tick` in the crontab reads exactly like what it does |
| `sweep` | 5 | medium | yes | no | **yes** | runner-up; beautiful but implies cleaning more than fetching; keep as rejected alternative in the decision record |
| `pulse` | 5 | medium | yes | yes | no | implies health-check; `doctor` owns that word |
| `cycle` | 5 | weak | weak (`run_cycle`, `run_cycle_inner` are internals) | yes | no | confusable with vault-sync internals |
| `refresh` | 7 | medium | yes | no | no | long, and overlaps `notebooks`/`areas` "repair catalogs" language |
| `upkeep` | 6 | medium | yes | no | weak | closest to `nightly`'s "maintenance" framing; acceptable but 50% longer than `sync` for a daily-typed command |
| `routine` | 7 | weak | yes | yes | no | too long, clinical |
| `catchup` | 7 | medium | yes | no | no | describes backfill (`-n 7`), not the steady state |
| `maintain` | 8 | weak | yes | no | no | too long; `nightly` owns "maintenance" |

Length matters because this is a daily-typed command: `sync`/`tick` (4) beat
everything else by at least a keystroke, and the prompt explicitly asks for
short.

### Why not make `tick` canonical?

I considered it — `tick` is the more *precise* name (the cron line is
literally one tick; per-step due-gates are evaluated per tick; the review
itself says "one cron tick"). Two reasons to keep `sync` canonical anyway:
(1) every existing pointer (task `^bob-sync`, `#sync` chore, `pre_stages`
`sync`, "Mac scheduled maintenance" docs language) already resolves to
`sync`, and renaming burns that recognition to buy precision only engineers
notice; (2) CLI rules make renames permanent — picking `tick` now and
regretting it later costs a forever-alias either way, so spend the alias
budget once: canonical `sync`, hidden `tick`, both byte-identical. Cron lines
and scripts can use whichever reads better in context (`bob tick` in the
crontab, `bob sync -a` in the morning).

### Disambiguation (the real cost of `sync`)

- Help: `bob sync --help` opens with "Run due background steps in order."
  and carries one explicit line: "For git pull/push of the vault, use
  `bob vault-sync`." `bob --help` lists `sync` in the Vault section near
  `nightly`/`vault-sync` with distinct `about` strings ("Run due background
  steps in order" vs "Reconcile the vault through Git").
- Delete the stale `~/bin/bob_sync` wrapper on apollo (it runs `exec bob sync`
  against the pre-`vault-sync` meaning) in the same change series — the review
  flags this, and leaving it redefines `sync` on one host.
- Never accept `bob sync sync` or `bob capture … sync` spellings; the step
  selector grammar is flat step names only (§4).

## 4. Configurability: which steps, how often (without building a cron language)

### Closed step set, fixed order

| # | Step | Runs | Default cadence | Manual? | Notes |
| --- | --- | --- | --- | --- | --- |
| 1 | `refs` (`bob ref scan`) | full scan (intake + annotation pass) | every tick | — | longest pole (p50 79s, p90 133s); needs the time budget most |
| 2 | `projects` (`bob projects sync`) | lifecycle + catalogs | every tick | — | fast (p50 5s); keep before gmail/gcal so catalog state is fresh |
| 3 | `gmail` (`bob gmail sync -q`) | file + watch; archive rules unchanged | **60m** | — | preserves today's hourly cadence + 2-hour staleness rule (`sync/health.rs`: quiet busy-skip fails only after 2h without success — the orchestrator must surface, not reset, that clock) |
| 4 | `gcal` (`bob gcal sync`, yesterday + today) | Events + MEET for last 2 days | **60m** | — | the new periodic win; `-n 2` equivalent baked in, overridable per-run |
| 5 | `reconcile` (`bob task reconcile`) | vault-only tidy, last | every tick | — | always runs, even after a prior step failed; missing-note becomes `waiting` (see below) |
| — | `gkeep` (`bob gkeep pull`) | drain Keep inbox | `manual` | **yes** | clips web pages, can prompt, Google-throttles; `bob sync --all` or explicit `bob sync gkeep` only |

Order is load-bearing (fetch → file → tidy) and therefore **not user
configurable**. Config controls *whether/when*, never *in what sequence*.
Adding a future step is one line in the step table plus one config key — the
`nightly.rs` `STEPS` pattern verbatim.

### Config schema (new `sync:` block, `~/.config/bob/config.yml`)

Follow the `freshness.*` and `gcal.*`/`gmail.*` conventions (typed values,
documented defaults, invalid = config error exit 2 for the command):

```yaml
sync:
  # Per-step minimum interval between successful-or-attempted runs.
  # Value: <N>m | <N>h | off | manual. Default per step below.
  refs: 15m        # every tick
  projects: 15m   # every tick
  gmail: 60m      # preserves today's hourly cadence
  gcal: 60m       # HARD CEILING: never more often than hourly (see §5)
  reconcile: 15m  # every tick; missing daily note => waiting, not failure
  gkeep: manual   # never on the timer; `bob sync --all` or `bob sync gkeep`
  writer: kellys-macbook-pro  # default: gcal.writer when set; else this host may run
  # timeout_secs: 600  # optional per-tick ceiling; a step exceeding its budget
  #   records waiting (reason: timed_out) and the tick continues to reconcile.
```

Semantics:

- `15m`/`60m`: step runs when `now - last_attempt_at(step) >= interval`.
  State lives host-local under `$XDG_STATE_HOME/bob-cli/sync/` (one JSON per
  step: `last_attempt_at`, `last_success_at`, `last_status`, `last_reason`) —
  the same pattern as `vault-sync.json`, `gcal` journal, and `gmail` link
  state. Host-local (not vault-committed) because due-ness is about *this
  machine's* executions, and the Mac sleeps (time-of-day jobs skip; intervals
  measured in wall-clock elapsed time do the right thing on wake: one catch-up
  run, not a burst).
- `off`: step never runs, even when named explicitly — the command prints
  `step off (sync.<step>: off)` and continues. (Cron-level `enabled: false`
  moves into config where it is versioned with the vault setup.)
- `manual`: step runs only when named (`bob sync gkeep`) or via `--all`.
  This is the gkeep answer and the escape hatch for any future
  prompt-capable step.
- Unknown `sync.*` keys: warn-and-ignore (config-blocks convention elsewhere:
  builds ignore unknown `capture` keys) — never hard-fail on forward-compat
  keys.
- `writer`: one host label allowed to run the timer set; anywhere else
  `bob sync` behaves like `-d` (prints the plan + "not the writer" reasons,
  exit 0). Default to `gcal.writer` when set so there is one pin, not two;
  `doctor` compares against the vault-sync hostname slug exactly as
  `gcal`/`gmail` doctors do today.

### CLI shape (flat, like `nightly`; every long flag gets its short alias)

```text
bob sync                 # run every due step (what cron runs)
bob sync -a, --all       # run every step now, gkeep included (replaces the morning chore)
bob sync gmail gcal      # run only these steps, now (due-gates bypassed, writer still enforced)
bob sync -d, --dry-run   # show each step's plan + why it would wait; write nothing
bob sync -f json         # machine-readable receipt (also always saved to state dir)
bob sync -q, --quiet     # print only waiting reasons and failures
```

- Step args are validated against the closed set; unknown step = exit 2 with
  the valid list (mirrors `bob ref`'s `subcommand_required` discipline).
- `-a` implies "all configured steps including `manual`", never "all
  including `off`".
- Explicit step args bypass *due-gates* (the user asked now) but never bypass
  *writer* or *readiness* gates (missing daily note is still `waiting`).
- `-f json` prints the same receipt that is always saved to
  `$XDG_STATE_HOME/bob-cli/sync/receipt-<ts>.json` (cap retained count, e.g.
  keep last 50) — the hook Bob Mac Capture will eventually read instead of
  scraping logs.

## 5. The hourly gcal bound (two layers; the schedule is the weaker one)

Requirement: "`bob gcal sync` is not run more than hourly on my mac."

**Layer 1 — the command enforces it (binding).** `sync.gcal: 60m` (default;
configurable upward, and downward only with an explicit `gcal_min_interval`
floor discussion — I would hard-floor at `30m` in code and document why:
Calendar API quota + the Templater-render race on the daily note). The
due-gate consults the host-local stamp *before* spawning anything, so neither
a tightened cron line nor an enthusiastic `bob sync gcal gcal` double-run can
violate the bound within one host. Manual `bob gcal sync` stays unthrottled
(the user asked now; the bound is on the *background* path), which preserves
the morning-chore escape hatch.

**Layer 2 — chezmoi cron expresses it (declarative).** With one 15-minute
tick and a 60-minute per-step gate, gcal *cannot* run more than hourly no
matter the tick phase — the cron line carries no gcal-specific schedule at
all. The chezmoi change is therefore a deletion (four jobs → one), not a
schedule puzzle, and there is no second place where the bound can drift. The
per-machine-machines invariant ("different behaviour means two jobs") is
satisfied trivially: mac gets the tick; athena keeps `bob-nightly` + its
hourly jobs; apollo is untouched.

Concrete `home/.chezmoidata.yaml` delta (in the linked `chezmoi` repo, via
`sase repo open chezmoi`, validated with `cronctl check --source`, previewed
with `cronctl diff mac`, converged with `cronctl apply mac`):

```yaml
jobs:
  # ... athena jobs unchanged ...
  - name: bob-sync
    machines: [mac]
    schedule: "5,20,35,50 * * * *"
    description: Run due Bob background steps in order (refs, projects, gmail, gcal, reconcile)
    command: bob sync -q
```

(Remove `bob-highlights-sync`, `bob-projects-sync`, `bob-task-reconcile`,
`bob-gmail-sync` in the same commit so the swap is atomic; rollback is
`git revert` + `cronctl apply mac`. Keep the `:05` phase rather than `:00` so
the tick does not pile onto whatever else fires on the quarter hour.)

Why not also gate by cron schedule (e.g. gcal only on `:05`)? Because two
independent enforcements of the same bound *disagree* eventually: someone
re-times the tick, runs `bob sync` by hand twice, or the Mac wakes from sleep
and cron fires a burst — and the "schedule" layer silently stops meaning
anything while looking authoritative. One enforcement point (the due-gate),
one expression point (the tick). The schedule stays dumb on purpose.

## 6. Mac crontab update (mechanics, not `crontab -e`)

Per `crontab.md` (read this turn): the `cron:` key is the only source of
truth; each machine renders a `# BEGIN chezmoi-cron … # END` block via
`~/.config/cron/managed.crontab`; `cronrun` derives PATH, guards overlaps
(`<job>.lock`), logs to `~/.local/state/cron/<job>.log`, and mails only
failures. So:

1. Edit `home/.chezmoidata.yaml` (chezmoi repo), not any live crontab.
2. `cronctl check --source <checkout>` (validates names `^[a-z0-9][a-z0-9-]*$`,
   schedules, `machines` values).
3. `cronctl diff mac --source <checkout>` — expect: four deletions, one
   addition. Read it; it is the actual blast radius.
4. Push, then `cronctl apply mac` (or `chezmoi update -a` on the Mac, which
   syncs when the block changes). `pending` means unreachable/not-yet-applied.
5. Verify live, never from memory: `cronctl status --all`,
   `cronrun --dry-run bob-sync 'bob sync -q'`,
   `tail ~/.local/state/cron/bob-sync.log`, and one forced
   `cronrun bob-sync 'bob sync -q'` (real side effects — it syncs) or
   `bob sync -d` (no side effects) first.
6. Rollback: revert the one commit, re-apply. Leave the individual commands
   (`bob ref scan`, `bob projects sync`, …) installed and working — the swap
   changes scheduling, not capability.

No secrets in job definitions (public repo); `bob sync` needs no new env
beyond `BOB_DIR`/`BOB_CONFIG_FILE` defaults, and GUI-PATH concerns
(`BOB_GCAL_GOG`, login-shell PATH) are already handled per-command.

## 7. Intuitive, reliable, beautiful — the three design pressures

**Intuitive.** One name for one job; flat step args (no `bob sync run gmail`
nesting — CLI rules punish needless nesting, and `nightly` proves flat
works); `-d` previews *reasons* ("gmail: waiting (ran 22m ago; due in 38m)"),
not just actions; `waiting` is a first-class outcome with a human sentence and
a hint (`run on kellys-macbook-pro, or set sync.writer`), exactly as gcal's
waiting path does today. Bare `bob sync` is the read-mostly safe default
(due steps only); `-a` is the explicit "do everything" gesture for the
morning.

**Reliable.** The full gate chain per step, in order: (1) `off`? → waiting.
(2) `manual` and not requested? → waiting. (3) interval unreached? → waiting
(record `last_attempt_at`? No — waiting on interval must *not* advance the
stamp, or a 15-minute tick would never let a 60-minute step become due; stamp
only on attempt). (4) wrong host? → waiting. (5) inputs not ready (no daily
note / no `## Pomodoros` / Templater tags unrendered / lock held)? → waiting
or bounded retry per the step's own policy (reconcile keeps its
`--retry-timeout` semantics *inside* its step; gmail keeps its 2-hour
busy-skip clock — the orchestrator passes through, never resets, these
clocks). (6) run with that step's own lock acquisition; on error record
`failed` with the step's stderr tail, continue to the next step, reconcile
always last. Exit 1 iff any attempted step failed. Overlap: a `sync.lock`
(run-lock, distinct from the vault lock) makes a concurrent tick exit 0 with
"already running" — cron bursts on wake become one run plus cheap no-ops.
Budgets: a per-step timeout (default generous, e.g. refs 15 min — its p99 is
~18 min including sleep tails, so measure warm p99 before fixing the number)
records `waiting (timed_out)` and moves on; reconcile still runs.

**Beautiful.** Copy `nightly`'s proven aesthetic instead of inventing one:
single rule-width (68 cols), `╭─ step 2/5 · projects ─…` headers,
`└─ ✓ projects ok` / `└─ ✗ gmail failed (exit 1)` footers, a `Summary` with
per-step rows and one closing line. Color via the existing `Styler`
(TTY-gated, `NO_COLOR`/`CLICOLOR_FORCE`-aware); structure never color-only so
cron logs read clean. One line per step in `-q` mode; full sections otherwise.
JSON receipt schema (versioned, `schema_version: 1` per
`docs/reference/json-outputs.md` conventions):

```json
{"schema_version": 1, "command": "sync", "at": "2026-11-18T09:05:01-05:00",
 "host": "kellys-macbook-pro", "tick_ms": 41230, "exit": 0,
 "steps": [{"name": "refs", "status": "ok", "duration_ms": 1204, "reason": null},
           {"name": "gmail", "status": "waiting", "duration_ms": 3, "reason": "ran 22m ago; due in 38m"},
           {"name": "reconcile", "status": "ok", "duration_ms": 8123, "reason": null}]}
```

Save every receipt; print it on `-f json`. This is the artifact Mac Capture
will consume later — one log, one receipt, one health signal, as the review
asks.

## 8. Alternatives considered (and why they lose)

- **Four cron lines + a fifth gcal line.** Preserves lock collisions, mail
  noise, and offset-folklore ordering; adds the exact failure mode (wake
  bursts) the evidence already shows. Rejected.
- **A shell-script wrapper (`~/bin/bob_sync`).** Zero config surface, zero
  receipt, zero JSON, untestable gating in bash 3.2, and apollo already has a
  stale `bob_sync` wrapper with the *old* meaning — reusing the path invites
  the worst confusion. The review's "reuse the name, delete the wrapper" only
  works if the name means the new Rust command everywhere. Rejected.
- **LaunchAgent instead of cron.** The gcal plan once offered a 5-minute
  LaunchAgent; it was never installed, and the Mac already runs
  `com.bbugyi.bob-vault-sync.plist` every 15s. Two schedulers (cron +
  launchd) for one vault doubles the "who runs what" surface and the sleep
  semantics differ (cron skips time-of-day jobs on sleep; per the memory,
  `mac` skips them — the tick design *relies* on elapsed-time due-gates to
  behave on wake). Keep cron; keep `cronrun`'s overlap guard, rotation, and
  mail-on-failure. Rejected.
- **Daemon / scheduler thread inside `bob`.** A long-lived process on a
  sleeping laptop is the wrong shape; cron already wakes it. Rejected.
- **Per-step flags passthrough (`bob sync --gmail-limit 5`).** Tempting,
  unneeded: steps keep their own CLIs for hand-tuning; the orchestrator passes
  fixed, reviewed args (`gmail sync -q`, `gcal sync` for yesterday+today,
  `reconcile` with its default retry budget). If a step later needs a knob on
  the tick, add one config key with a default — not a CLI passthrough matrix.
  Deferred, not rejected.

## 9. Adjustments to the requirements (explicit)

1. **Five steps, not four.** The prompt says "frequent `bob` commands" and the
   task text names four, but projects sync is the fifth periodic Mac job and
   belongs in the tick (its failures include real lock-contention wins). Added.
2. **gkeep is manual-only.** The prompt asks for configurable commands; I fix
   gkeep to `manual` rather than offering it on the timer: it clips web pages
   and can prompt, and unattended web-clip traffic is a throttle risk
   (`docs/gkeep.md`). `--all` covers the morning chore.
3. **gcal window is yesterday + today**, not just today — late-arriving
   changes to yesterday's meetings still land, for ~zero marginal fetch cost.
4. **Reconcile's missing-note case becomes `waiting` inside the tick**
   (exit 0). This is the 50-run fix; standalone `bob task reconcile` keeps its
   current behavior (CLI stability rule: never change an existing command's
   contract silently — the waiting treatment is the orchestrator's
   interpretation, plus optionally a later reconcile-side flag).
5. **No user-ordered steps.** "Highly configurable" is honored as
   which-steps + how-often + off/manual, not arbitrary DAGs. Ordering is the
   correctness property; exposing it trades reliability for a knob nobody
   asked to turn.
6. **Bound enforced in code, expressed in cron.** The prompt asks for the
   hourly gcal bound "by making the appropriate configuration changes to my
   chezmoi repo" — I do that (one tick line), but the *binding* enforcement
   must live in the command's due-gate, or hand-runs and re-timed ticks
   bypass it. Both changes ship; the config change alone is declared
   insufficient in the report and the decision record.

## 10. Recommended build (phased, small-to-medium)

1. **Command skeleton** (`src/native/sync.rs` + `NativeCommand::Sync` +
   `SUBCOMMANDS` entry in `Section::Vault`, alphabetical placement):
   step table, arg parsing (`-a/-d/-f/-q`, step positionals, `-h`), writer
   gate, dry-run planner, nightly-style output, JSON receipt + state stamps,
   run-lock. In-process calls into existing entry points (no subprocesses, no
   new network code).
2. **Per-step integration:** refs scan (full; intake-only is a separate
   concern), projects `nightly_step`, gmail sync (preserve `-q` + staleness
   clock), gcal sync (yesterday+today, waiting passthrough), reconcile
   (waiting on missing note *within sync*), gkeep manual wiring.
3. **Config:** `sync:` block parsing + validation (exit 2 on invalid, with
   the key path in the message, per `configuration.md` conventions), docs
   table rows, `just docs-gen`.
4. **Timeouts/budgets:** measure warm p50/p99 per step on the Mac first, then
   fix defaults; never ship a budget tuned on sleep-inflated tails.
5. **Chezmoi swap:** one commit (delete four, add one), `cronctl check`,
   `cronctl diff mac`, apply, observe one full hour (four ticks) + one forced
   `cronrun` before declaring done.
6. **Docs + decision record:** new behavior/contract page, CLI reference regen,
   `just docs-check`; record "Mac background work is one ordered `bob sync`
   tick" with the rejected alternatives (§8) and the reopen condition (a step
   that cannot tolerate fixed ordering).
7. **Gates:** `just check` (fmt + clippy + workspace tests incl. new
   orchestrator tests: due-gate math, off/manual, writer, waiting-vs-failed
   aggregation, receipt schema), `just check-scripts` untouched paths,
   release-train compliance (no version/CHANGELOG edits, `!` on JSON breaks).

## Sources (checkable)

- Task/history: `research:202611/bob_sync_task_review.md`; `~/bob/bob.md`
  `^bob-sync`; `done/bob_done.md` `^gmail-sync`; `gtd_daily.md` `#sync` chore.
- Live schedule/config: `home/.chezmoidata.yaml` (`cron.jobs`,
  `bob-highlights-sync`, `bob-projects-sync`, `bob-task-reconcile`,
  `bob-gmail-sync`); `home/dot_config/bob/config.yml` (`gcal`, `gmail.sync`,
  `freshness.pre_stages`); `~/bin/cronrun` (overlap guard, log/status paths,
  mail-on-failure).
- Code: `src/native/nightly.rs` (Step table, Styler, summary, exit fold);
  `src/native.rs` (module registry); `src/runner.rs` (`SUBCOMMANDS`,
  `ALIASES`, `Section::Vault`, `nightly` entry); `src/native/ob.rs`
  (lock API, `ChildEnv`); `src/native/vault_sync.rs`
  (`run_cycle_with_existing_lock`, `BOB_VAULT_SYNC_*` env);
  `src/native/gcal/sync.rs` (writer gate, waiting reasons, `-n`/`-D`/`-F`/`-d`/`-q`);
  `src/native/gmail/cli.rs` + `src/native/gmail/sync/health.rs`
  (2-hour stale busy-skip); `src/native/task_status_hooks/`
  (reconcile contract, retry); `src/native/projects/mod.rs` (sync help +
  one-commit semantics); `src/native/highlights_ref/cli.rs` (`scan`,
  `--intake-only`); `src/native/gkeep/` (`pull`, `status`, throttling).
- Docs/memory: `docs/gcal.md`, `docs/gmail.md`, `docs/gkeep.md`,
  `docs/reference/configuration.md`, `docs/reference/json-outputs.md`,
  `docs/reference/cli/nightly.md`, `docs/vault-git-sync.md` (Mac scheduled
  maintenance); memory `cli_rules.md`, `docs.md`, `crontab.md`
  (all read via `sase memory read` this turn).
- Decisions bearing on the design: `decisions:bob-gcal-is-read-only-and-proposes-once`,
  `decisions:gcal-force-resets-the-day`, `decisions:references-are-ingested-at-birth`
  (cited, not re-read; the new record should link them).
