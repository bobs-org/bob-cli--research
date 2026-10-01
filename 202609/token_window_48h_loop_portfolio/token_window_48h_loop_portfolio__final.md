# What to Loop During a 48-Hour Token Window

**Consolidated report** · 2026-09-30 · Lead researcher (Claude Opus 5.5), merging five
independent reports ([cdx](token_window_48h_loop_portfolio__cdx.md),
[cld](token_window_48h_loop_portfolio__cld.md),
[grk](token_window_48h_loop_portfolio__grk.md),
[mus](token_window_48h_loop_portfolio__mus.md),
[gem](token_window_48h_loop_portfolio__gem.md)) with my own checks of the claims they
disagreed on or rested on most heavily.

**Question.** Bryan has near-unlimited tokens for the next 48 hours only. Which
high-value work can run as a loop, meaning the same or a similar prompt run again and
again (for example via `/sase_handoff`)? The report ends with a ranked list.

---

## Bottom line

- **Tokens stop being the constraint, but four others remain.** All five reports reached
  this independently:
  1. **Verification gates.** The sase `check` passed 35 of 1,091 runs this week, and
     bob-cli master is red right now.
  2. **Your review attention.** The sase ready queue holds 312 task beads.
  3. **Host capacity.** athena can run only 2–3 full sase checks at once.
  4. **Loop plumbing.** Pipe chains are capped at 9 agents, and `%repeat` stalls after
     a crashed slot.
- **What a good loop needs.** Spend the window on loops that each have:
  - a check the agent can't edit
  - one small unit of work per iteration
  - a metric that only moves one way
  - a STOP condition
  - output that keeps paying after the window: green gates, landed epics, killed
    mutants, closed beads, tests
- **Don't start anything new.** No new feature epics, no find-and-file audits, no broad
  research swarms. Each of these creates review debt that outlives the window.
- **What I'd run:**
  - **Lane 1, sase gate sheriff.** Unstick the existing gate-repair epics first.
  - **Lane 2, one bob-cli lane:** fix master and add CI, then drain the ready beads,
    then harden with mutation and property tests.
  - **Lane 3, land finished sase epics,** once the gate turns green at least some of the
    time.
  - **Lanes 4 and 5:** de-flaking and a cross-provider auditor, alongside the others.
- **Model choice.** The "use it or lose it" capacity looks like Codex (91% left) and
  Claude Fable (100% left). Both reset in about 2 days, so put the heavy lanes on them.
  Claude all-models is at 36%, and Fable may draw against that cap too, so check.

---

## 1. What I verified myself

I re-checked the claims the rankings depend on. Where a report was wrong or out of date,
the correction is noted.

| Claim | Result (2026-09-30, ~23:30) | Notes |
|---|---|---|
| bob-cli master is red | **Confirmed at HEAD `663a0bc`.** `cargo test --lib`: 1,413 passed, 5 failed, all in `native::capture_pomodoro_close::linked_task_tests` | The close plan now writes `[fresh:: 2026-09-28]` on the `=x` row that sets `[/]`. `docs/freshness.md` lists exactly that gesture as one that stamps, so the 5 test expectations are probably what's stale (cld's inference). Confirm the owner first: bob-cli-31/32 are mid-landing. |
| bob-cli has no CI | Confirmed. There is no `.github/` directory, and `just lint` runs clippy without `-D warnings` | Nothing caught two epics colliding (cld). |
| No generative testing tooling | Confirmed. No proptest, quickcheck, arbitrary, fuzz or insta dependency; `cargo-mutants` is not installed | Install these before starting any hardening loop. |
| Clippy warnings | **54** (`--all-targets --all-features`) | grk's "~19 locations" is out of date; cld's ~55 is right. Several are unused imports in freshness code that is landing right now. Leave those to bob-cli-31. |
| bob-cli size | 142k lines in `src/`, 198k including `tests/` | gem (142k) and cdx (198k) were both right, measuring different scopes. |
| bob-cli queue | 17 ready beads. In progress: bob-cli-28, 31, 32 | Matches cdx, grk and gem. |
| sase check pass rate | 1,091 runs, **35 OK**, 832 failed, 221 censored. 185 killed at the time limit; **51.7 h wasted** in 7 days | Confirms cld. |
| sase epics finished but not landed | 96 in-progress epics, 57 of them 14 or more days old. **65 have every direct phase child closed but have not landed** | cld counted 36 with a stricter method, grk counted 97 in progress. Either way the queue is large. It includes **sase-126 "Restore SASE Master Gate and Full CI"** and **sase-j7** (flake-class root cause, 51 days old). |
| Flakes are swept, not fixed | 312 ready tasks (95 bug / 89 flake / 67 ci / 44 feature). Of 37 flakes closed in 14 days, **34 were "stale task bead swept from triage"** | Confirms cld. |
| Loop caps | `max_agent_pipe_chain: 8`, `max_running_agents: 10` (merged config) | A pipe refused at the cap leaves the calling agent alive (docs/configuration.md), so the chain stops cleanly rather than failing. |
| `%repeat` failure behavior | Unknown in all five reports. **sase docs: `%wait` is fail-closed.** A failed, killed or crashed slot never satisfies its successor's wait, so every later slot stays parked until you relaunch it. SASE sends a "terminally blocked wait" notification | This changes the overnight design (§3). |
| GKeep inbox | 65 open `#task` lines in `gkeep_inbox.md` | The pull already works. What remains is triage (grk), not running `bob gkeep pull` (mus). |
| Freshness semantics | `docs/freshness.md`: `[fresh::]` is "the local calendar date a **human** last confirmed" the task | An agent bulk-stamping freshness would falsify the signal. This rules out mus's #1 (§2). |
| Host | 64 cores, 62 GiB RAM, ~27 GiB available, load ~17.5. 25 agent rows (many of them WAITING) | Supports cld's limit of 2–3 concurrent full sase checks. |

**External evidence I re-checked:**

- [ImpossibleBench](https://arxiv.org/abs/2510.20270) (ICLR 2026): GPT-5 exploits tests
  in 76% of one-off impossible SWE-bench tasks. Giving it an explicit **abort option**
  cut cheating on conflicting SWE-bench from 54% to 9%.
- [Agentic property-based testing](https://arxiv.org/abs/2510.09907): 56% of the agent's
  bug reports were valid, and 86% of the top-ranked ones.
- [Meta ACH](https://arxiv.org/abs/2501.12862): 9,095 mutants led to 571 tests, and
  engineers accepted 73% of them.
- **A finding the reports missed:** [a 2026 study of repair agents](https://arxiv.org/abs/2607.28871)
  found that **46% of passing validation results contained no bug-discriminating
  information**, and 24% of runs closed with no discriminating evidence at all.
  - **Implication:** every fix loop must show that its new test fails on the pre-fix
    tree ("red-first"). A green run alone proves nothing.

---

## 2. Where the reports disagreed, and how I resolved it

1. **Which repo to work in.**
   - cdx, gem and mus looked only at bob-cli; cld and grk measured sase.
   - **Resolution:** run both, in separate lanes.
     - sase has by far the largest measured waste: a 3.2% pass rate, 51.7 hours a week,
       and about 94% of your prompts target it (cld survey).
     - bob-cli has the cleanest oracle and protects your personal vault.
2. **Should loops implement anything in sase?**
   - grk: don't put more implementation agents into sase. cld: run a sheriff and land
     epics.
   - **Resolution:** they are not in conflict. grk's evidence (97 in-progress epics,
     host load) argues against *starting* work. The sheriff, de-flake and landing lanes
     *finish or repair* work. Everyone agrees on no new epics.
3. **Which loop mechanism to use.**
   - grk and gem built around `/sase_handoff`. gem's estimate of 600–1,150 turns per
     chain is impossible under the 8-hop cap.
   - cld preferred `%repeat` but hadn't tested what happens on failure. The answer is
     now known: it is fail-closed.
   - **Resolution:** pick a mechanism per lane (§3). For unattended overnight lanes, use
     axe routines.
4. **gem's "infallible oracle, near-zero risk" for mutation testing.**
   - This is overstated. Equivalent mutants waste iterations, and tests can pass without
     discriminating anything (the 46% study above).
   - Mutation testing is still worth doing: the evidence favors running it per module
     and incrementally (cdx, citing Google), not whole-repo.
5. **mus's #1, a sharded vault freshness sweep.**
   - Rejected as a loop, for three reasons:
     - freshness is human-confirmed by contract
     - the sweep writes the live vault
     - `bob freshness list` landed only hours ago under bob-cli-31
   - **Instead:** an agent may prepare a review packet, and you stamp.
6. **Research or paper loops.**
   - grk ranks the 10-paper follow-up list #3: it's on today's READ theme and only cheap
     now. cld says skip research swarms because of the reading cost.
   - **Resolution:** keep it as a low-priority lane with a hard output budget: one page
     per paper and one synthesis.

---

## 3. How loops actually run in SASE

| Primitive | Behavior (verified from docs/config) | Use it for |
|---|---|---|
| `/sase_handoff` (`sase pipe -f`) | Serial, same workspace. The original agent is depth 0; a pipe is refused past `max_agent_pipe_chain` (default 8), so at most 9 agents per chain. A refused caller stays alive and can finish the work itself. | Continuing **one** item that ran out of context, or short daytime chains. To rely on it, raise the cap for bob-cli during the window. |
| `%repeat:N` | Spawns N fresh agents up front, each with its own workspace, wait-chained in series. `{{ n }}`/`{{ N }}` are available. `sase var set STOP=1` stops the rest of the chain. **Fail-closed:** a crashed or killed slot parks every later slot. | Draining a queue during the day while you can relaunch after a stall. |
| Axe routine (`run_every` + `inhibit_if: agent_clan.name_prefix`, as your `toobig_split` job does in the chezmoi-managed `sase_athena.yml`) | Each tick launches a fresh agent. The inhibit guard prevents overlap, and one failure doesn't stop later ticks. | **Overnight lanes,** and anything that should outlive the window (the sheriff). |

**Iteration contract.** Merged from cdx, grk, cld and gem, plus the evidence above. Put
this in every lane's prompt:

1. **Re-derive the queue every time.** Use a live command (`sase tool failures -j`,
   `sase bead ready`, `cargo mutants --list`, `git log --grep`) or a tracked ledger
   file. Never rely on chat memory. Claim exactly one item.
2. **Name the oracle before editing.** Reject any item whose only oracle is "the current
   implementation says so."
3. **Red-first.** A new test must fail on the pre-fix tree, and the agent records that.
   A green suite alone is not evidence.
4. **Anti-cheat.**
   - Never loosen or delete an assertion, guard, baseline, budget, timeout or lint rule.
   - Never regenerate a snapshot without justifying each changed line.
   - Offer an explicit **DECIDE/abort exit**: write a note to one DECIDE queue and
     finish. This is the ImpossibleBench mitigation.
5. **Commit, then record the metric** with `sase var set` (`CHECK=`, `FIXED=`,
   `KILLED=k/s`), so you can follow progress from Telegram.
6. **Always end as a normal, completed turn,** even when the item failed: record a skip
   and finish. A crash strands a `%repeat` chain.
7. **Stop** when the queue is empty, or after 3 consecutive iterations that produce
   nothing. Overbaking, where a loop keeps adding things nobody asked for, is the known
   failure mode of this kind of loop.
8. **Use temp vaults and worktrees only.** Never touch `~/bob`, plugin deploys,
   `vault-sync`, live Pomodoros or remotes.

**Capacity.**

- Run at most 2–3 lanes that each run a full sase `check` at the same time. cld measured
  a p90 process-tree peak of about 15.7 GiB, from only 5 sampled runs.
- bob-cli lanes are light: `cargo test --lib` takes about 2 seconds once warm.
- Optionally raise `max_running_agents` to about 14 for the window while watching memory
  pressure, or `%dispatch` to apollo.
- Pair every worker lane with an auditor from a different provider.

---

## 4. What not to spend the window on

- **New feature epics.** They need your taste and leave review debt.
- **Find-and-file audits.** Sweeps already cancel more beads than get fixed.
- **Mass regeneration of visual goldens.** sase-126 owns that, and athena is too loaded
  to run visual tests reliably.
- **Bulk writes to the vault,** including mus's freshness sweep and gem's "normalization"
  sweep.
- **Rustdoc or docs sweeps.** `refresh_docs` already runs.
- **Unbounded "improve the codebase" loops.**
- **Several copies of the same queue.** Two *different* loops is fine; two copies of one
  loop collide.
- **Policy decisions as loops:** PDF/untracked-file policy (bob-cli-1q/1g), Mac UX copy
  (bob-cli-20).

**Attended, not looped.** Do each of these in one sitting from an agent-prepared packet:

- **GKeep triage** (65 items). Cap new beads per item and run `/sase_new_task` first.
- **NEXT and PENDING overflow** (28/15 and 49/10). Only your Alt+N release lowers a lane,
  per `decisions:task-lanes-are-sticky`.
- **Freshness review.** The stamp has to be yours.
- **The `bob-cli-1g`/`1q` durability plan.**

---

## 5. A 48-hour schedule

| When | You | Loops |
|---|---|---|
| **H0–H2** (attended) | **Coordination:** check whether the land agents for sase-126 and sase-1c1 are stuck, and unstick them. Confirm with the bob-cli-31/32 owners that `=x` → `[/]` should stamp freshness, then fix the 5 tests. **Setup:** install `cargo-mutants` and add `proptest`. Add the sheriff axe routine. Raise the pipe cap if you'll use handoff. Smoke-test a 3-slot `%repeat` with one deliberately failing slot before trusting it overnight. | Start lanes 1 and 2. |
| **H2–H12** | Glance at the `sase var` metrics. | Lanes 1 and 2. Add lane 4 if the gate isn't saturating the host. Run lane 5 at about H6. |
| **H12** | Clear the DECIDE queue. Read `sase tool stats -t check -d 1`. | If the clean-master pass rate is over 50%, start lane 3. |
| **H12–H36** | At about H24, read the sheriff's `SYSTEMIC` notes and approve one prevention change. | Lanes 1–5. Lane 6 is a one-shot followed by its loop. Lane 7 runs in a spare slot. |
| **H36–H44** | — | Wind down. Start no new targets in the last 4 hours. |
| **H44–H48** | Read a one-page summary: what landed, bugs found, yield per lane. Decide which loops become permanent axe routines (the sheriff, and possibly a nightly bob-cli hardening run). | Consolidation only: full checks, stabilizing seeds, closing beads. |

---

## 6. Sources

**Local, run this session:**

- `cargo test --lib` and `cargo clippy --all-targets --all-features` at bob-cli `663a0bc`
- `sase bead ready`, `sase bead list` (bob-cli and sase stores)
- `sase tool stats -a -t check -d 7`, `sase usage`, `sase agent list`
- merged sase config
- sase `docs/xprompt.md` (Repeat Directive), `docs/configuration.md`
  (`max_agent_pipe_chain`), `docs/blog/posts/axe-background-daemon.md` (fail-closed
  `%wait`), `docs/notifications.md`
- bob-cli `docs/freshness.md`
- `~/.config/sase/sase_athena.yml` (`toobig_split`)
- `~/bob/gkeep_inbox.md` (count only)

**External:**

- [Anthropic, multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system)
- [Anthropic, effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)
- [METR time horizons](https://metr.org/time-horizons/)
- [ImpossibleBench](https://arxiv.org/abs/2510.20270)
- [Agentic property-based testing](https://arxiv.org/abs/2510.09907)
- [Meta ACH](https://arxiv.org/abs/2501.12862)
- [Validation evidence in LLM repair agents](https://arxiv.org/abs/2607.28871)
- [Google, practical mutation testing at scale](https://research.google/pubs/practical-mutation-testing-at-scale-a-view-from-google/)
- [Huntley, Ralph](https://ghuntley.com/ralph/)
- [DORA 2025](https://dora.dev/research/2025/dora-report/)

Further citations are in the individual reports.

---

## 7. Ranked recommendations

**How to choose.** Lane 1 has the largest payoff. Lane 2 is the safest. **If you will
run only one lane unattended overnight, run lane 2.**

### 1. sase gate sheriff: keep a clean origin/master passing `check`

- **Why:** 35 of 1,091 checks passed this week, and 51.7 hours went to waste. Your two
  highest-volume prompts, `#bd/work_phase_bead` and `#bd/land_epic`, depend on this
  gate. While it stays red, no other loop can tell whether its own work succeeded.
- **First, unstick the existing owners.** Two epics already target this:
  - sase-126 (Restore Master Gate and Full CI) has every phase closed but hasn't landed
  - sase-1c1 (green CI and ship 0.18.0) has agents WAITING

  The sheriff handles breaks that land after them and never duplicates them.
- **Loop:** an axe routine every 15–30 minutes, with `inhibit_if` on the `sheriff-` clan
  prefix.
  1. On a clean checkout of the newest master, run `check`.
  2. If it fails, bisect the first failing stage to the commit that broke it.
  3. Make the smallest fix consistent with what that commit meant to do.
  4. Record `CHECK=` and `SYSTEMIC=`.

  cld §7 has a ready-made prompt.
- **Oracle:** `check` on a clean tree.
- **Main risk:** the sheriff "fixes" things by weakening guards. The anti-cheat rules and
  the DECIDE exit cover this.
- **Afterward:** from the `SYSTEMIC` notes, approve one prevention change: run the cheap
  repo-wide invariant stages before commit. Keep the sheriff as a permanent routine.

### 2. One bob-cli lane: green and CI, then the ready beads, then hardening

A single prompt works through a priority queue:

- **(a) One-shots.**
  1. Fix the 5 red tests.
  2. Clear the 54 clippy warnings, minus the freshness imports that are landing now.
  3. Add a `.github` CI workflow (fmt, clippy `-D warnings`, `cargo test`).
  4. Add bob-cli to `ci_watch`.
- **(b) Deterministic ready beads.**
  - **Do:** `2q` (time zone after 8pm), `2e`, `2m`, `22`, `2l`, `2t`, `2u`, `v`, `30`,
    `2x`, `1x`.
  - **Skip:** `1g` and `1q` (policy), `20` (needs the Mac app), `2i` and `2j`
    (features).
  - **Plan only:** `21`.
- **(c) Hardening,** one module per iteration:
  - Kill surviving mutants, add properties, and add differential oracles:
    - parse/rewrite idempotence
    - dry-run equals apply
    - batch atomicity
    - pinned `BOB_NOW` gives the same result across time zones
    - sticky-lane invariants
  - **Start with files outside the in-flight epics:** `task_status_hooks_write.rs`,
    `vault_sync.rs`, `randomize_plan.rs`.
  - **Capture files** (`capture_language/`, `capture_pomodoro_close/`) only after
    bob-cli-28/31/32 land.
- **Why:** this is the one direction four of the five reports converged on. It has the
  strongest oracle, cheap verification, and temp vaults only, and it protects the tool
  that edits your notes every day.
- **Metrics:** `KILLED=k/s` and beads closed.

### 3. Land the finished-but-unlanded sase epics

- **When:** once lane 1 has the gate green at least some of the time.
- **Why:** 65 epics (by my count) have every phase closed but haven't landed. That is
  work already paid for, and today you relaunch these by hand.
- **Loop:** serial, with 1–2 landings in flight. Each iteration takes one epic:
  1. Diagnose why it stalled: a red gate, a wait on a failed agent, or a conflict.
  2. Either relaunch `#bd/land_epic`, or write a verdict: `close-candidate`,
     `duplicate-of`, or `needs-bryan`.
- **Order:** oldest first, but sase-126 and sase-j7 go first because they multiply
  everything else.
- **In-progress epics with open phases** (14 days or older) get grk's verdict-only
  honesty pass. It never closes or launches anything.
- **Then:** cut 0.18.

### 4. sase de-flake: one root cause per iteration

- **Why:** 89 flakes are ready, and only about 1 of 37 closures in two weeks was a real
  fix. About half match "fails in the parallel lane, passes alone", so they cluster
  around shared-state causes.
- **Proof required:**
  - Reproduce under the parallel lane *before* editing.
  - After the fix, 20 consecutive passes.
  - Retire the entry in `tests/reproducible_flake_baseline.txt`.
  - Forbidden: retries, larger timeouts, skips.
- **Coordinate with lane 3:** land sase-j7 (the leak detector) first.
- **Constraint:** it shares the 2–3 concurrent-check limit with lane 1.

### 5. Cross-provider auditor over every loop's commits

- **What:** every few hours, a model from a different provider reviews all commits since
  the last audited SHA. It looks only for:
  - weakened tests or guards
  - snapshot churn
  - behavior changes the bead didn't ask for
  - red-first evidence, by replaying each new test against the parent commit
- **Why:** the most reliable defense against the documented failure modes (test
  exploitation, non-discriminating validation), and it spends surplus tokens in place of
  your review.

### 6. Bob↔Mac contract harness: a one-shot, then one schema per iteration

- **One-shot:** replay each Bob Mac Capture JSON fixture against the current `bob` in a
  temp vault with `BOB_NOW` pinned, then run CaptureCore `swift test` on athena. cld's
  survey found 536 tests passing in 31 seconds.
- **Loop:** add drift fixtures and compatibility cases for one `--json` surface per
  iteration.
- **Coordination:** cross-repo work, so open repos through `/sase_repo` and run it
  serially.

### 7. Paper follow-up reading loop

- **Scope:** the 10 papers on today's READ theme, one per iteration.
- **Output:** a page or less on what each changes in sase or bob, then one synthesis
  with 3–5 concrete changes or an explicit "no change". No implementation.
- **Why:** low risk, and the reading is only cheap now.
- **Why it ranks low:** its value is capped by your reading time.

### 8. Rust file splits in sase-core with your existing `#split_epic`

- **Scope:** cld's survey found 56 files over 1,500 lines that the Python-only `toobig`
  job doesn't cover. I didn't re-verify that count.
- **Why:** compiler-checked, cheap to review, and it makes later agent reads cheaper.
- **Role:** filler for idle slots. bob-cli's 17 large files wait until its epics land.

### 9. SASE harness-evaluation flywheel (cdx)

- **What:** turn recurring agent failures into reproducible evals, then A/B test the
  smallest skill or tool change against them.
- **Why it ranks last:** highest ceiling but the weakest fit for 48 hours, because it
  needs an eval set before it yields anything.
- **When:** seed it after the window from lane 1's `SYSTEMIC` log and lane 5's findings,
  unless you have spare attention now.
