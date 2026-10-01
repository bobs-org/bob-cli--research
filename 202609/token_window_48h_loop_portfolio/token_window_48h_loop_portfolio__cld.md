# Loopable, High-Value Work for a 48-Hour Token Surplus

**Researcher:** cld (one of five independent swarm researchers) · **Date:** 2026-09-30

**Question.** Bryan will have close to unlimited tokens for the next 48 hours, and only for those 48 hours. What high-value work fits a loop, meaning the same or a similar prompt run over and over (via `/sase_handoff`, `%repeat`, or an axe routine)? This report ends with a ranked list.

---

## TL;DR

- **Tokens are not the constraint this window removes.** Three things still limit how much useful work a loop can do:
  1. **sase's verification gate is almost always red.** Over the last 7 days, `sase tool run check` ran **1,091 times and passed 36 times (3.3%)**. Daily passes since 09-26 were 4, 0, 1, 0 and 2. The ledger records **51.7 hours of wasted check time** and **185 runs killed at the time ceiling**. Every loop's backpressure is that gate, so while it stays red a loop can't tell whether its own work succeeded.
  2. **Your attention, and the triage queue it has to clear.** sase has **312 ready beads**, including 95 bug, 89 flake, 67 ci and 44 feature tasks. You have already muted task-bead notifications. A loop that files more findings without fixing them makes this worse.
  3. **Host capacity for verification.** `max_running_agents: 10` is the default and you haven't overridden it. A check's process tree peaks around 15.7 GiB at p90 (small sample), so athena can only run a few full checks at once.
- **So turn the temporary tokens into lasting assets** that reduce your token and attention spend after the window closes:
  - a green gate
  - drained flake and failure queues
  - finished epics that actually get landed
  - a hardened bob-cli with real CI
  - smaller files and stricter types
- **Avoid** new-feature epics, find-and-file audit loops, and mass research. All three create review debt that outlasts the window.
- **Top three loops:**
  1. A **master sheriff** that keeps a clean origin/master green and records the systemic cause of each break.
  2. A **de-flake** loop that fixes one flake per iteration, with proof.
  3. **bob-cli hardening:** first fix today's red master and add CI, then a mutation- and property-test loop over the modules that write to the vault.

  Once the gate is meaningful, land the roughly **36 sase epics whose phases are all closed but which were never landed**.
- **Mechanics.** For draining queues, prefer `%repeat:N`: each slot is a fresh agent in its own workspace, slots are wait-chained in series, and `sase var set STOP=1` ends the chain. Avoid long `/sase_handoff` chains. bob-cli inherits `max_agent_pipe_chain: 8`, so a handoff loop there dies after 9 turns.

---

## 1. Method

I wanted the answer to come from Bryan's own systems, not from generic advice. Sources:

- **sase's own telemetry:**
  - `sase tool stats -t check` for 7 and 30 days
  - `sase tool failures -j` (1,000 grouped failure signatures over 7 days)
  - `sase usage`, `sase agent list`, `sase prompt stats`, `sase goal list`
- **Read-only surveys of every active repo:** sase, sase-core, sase-telegram, sase-github, sase-nvim, actstat, bugyi-chops, toobig, bob-cli, bob-plugins and bob-mac-capture. All were opened through `sase repo open`. Five parallel sub-surveys covered:
  - sase health
  - the Bob ecosystem
  - satellite repos
  - prompt history and prior research
  - external evidence on agent loops
- **Direct checks I ran myself:**
  - `cargo test --lib` on bob-cli master
  - existing loop mechanics in sase docs and config (`%repeat`, `max_agent_pipe_chain`, `max_running_agents`, axe routines)
  - the Telegram receiver's chat-authorization guard
- **External evidence** on which tasks autonomous loops do well and badly (§4). Citations are inline.

Numbers marked *(survey)* come from a sub-survey, and the command behind each is named so it can be reproduced. Numbers without that mark I measured myself.

---

## 2. What Bryan already does (so we don't duplicate it)

Bryan is already a heavy loop user. In prompt history (11,638 prompts since 2026-07-06), the top chips are:

| Chip | Count |
|---|---|
| `#bd/work_phase_bead` | 4,954 |
| `%miaw` | 3,758 |
| `#plan` | 2,785 |
| `#bd/land_epic` | 1,818 |
| `#split_file` | 1,023 |

About **94% of prompts target sase** *(survey)*. Already automated on athena:

| Already running | Mechanism | Covers |
|---|---|---|
| `toobig_split` | axe `run_every: 60m`, blocked while a `toobig-` clan is running, `%auto #split_file` with a `%if` that re-checks the 700-line floor | **sase Python `src/` + `tests/` only** |
| `refresh_docs` | axe `git.commits_since` threshold 100, `checkpoint: on_action_success` | docs refresh for every enabled project |
| `ci_watch` | actstat sweep every 5 min, notifications, guarded release-please merges | **notifies only; never launches repair agents** |
| Epic execution | `#bd/work_phase_bead` → `#bd/land_epic` | every planned epic |
| Research swarms | `#research_swarm` | 97 requests in September *(survey)* |

Retired loops that remain in prompt history are `recent_bug_audit`, `recent_improvement_audit` and `ci_fix`. All three last ran on 08-12 *(survey)*.

**Not covered today:**
- deterministic repair of master
- flake fixing (flakes get filed, not fixed)
- Rust file sizes in sase-core and bob-cli
- bob-cli CI (bob-cli has **no CI at all**)
- property and mutation testing anywhere
- type ratchets
- landing of stranded epics, which Bryan does by hand (on 09-30: "review and relaunch the 1d5, 1cx, 1cj.12, 1co, and 1ck epic beads…")

---

## 3. Findings

### 3.1 The sase gate is red about 97% of the time, and that feeds itself

`sase tool stats -t check -d 7` (athena, 09-23 → 09-30):

| Metric | Value |
|---|---|
| Runs | 1,091 (OK 36 · FAIL 832 · censored 221) |
| Killed at time ceiling | 185 (27.7 h) |
| Total waste | **51.7 h**, including 160 exact repeats (40.8 h) |
| Daily OK, 09-21 → 09-30 | 14, 24, 12, 12, 16, 4, **0, 1, 0, 2** |
| P50 / P90 wall time | 3m44s / 26m |

Stage-level failures (stages fail fast, so later stages see fewer runs):

| Stage | Runs | Fail | Note |
|---|---|---|---|
| lint (symvision) | 507 | **273** | 54% fail rate. In `sase tool failures`, single signatures recur across 44 agents each, e.g. `intent_accept in src/sase/monitor/no_new_receipt.py`, 52 runs |
| lint (mypy) | 862 | 173 | |
| lint (feature flags) | 709 | 124 | the top single signature: 76 runs across 66 agents |
| lint (patch/stitch terminology) | 568 | 64 | 58 runs across 55 agents for one signature |
| SASE validation | 339 | 58 | |
| test (scoped) | 275 | 139 (+106 incomplete) | **only 30 OK**; P50 **17m 4s**, P90 41m |

The failing test signatures with the most runs are mostly **deterministic repo-wide guard tests**, not flakes:

| Test | Runs |
|---|---|
| `test_timezone_display_guard::test_no_system_clock_display_sites` | 38 |
| `completion/test_kind_coverage` | 36 |
| `completion/test_snapshot::test_checked_in_snapshot_has_no_drift` | 28 |
| `test_config_schema_tools::test_project_sase_yml_matches_public_schema` | 25 |
| `test_agent_artifact_marker_path_passing_audit` | 29 |

Of the 1,000 groups the query returned (its cap), 326 are classed `known`, 312 `new`, 260 `unknown` and only 26 `flaky`.

**What this means:**

- **The red is shared.** One agent lands a commit that breaks a repo-wide invariant: an unused symbol, an unregistered flag, snapshot drift, schema drift or a terminology slip. From then on, every other agent's check fails on something it didn't cause.
- **The red feeds itself.** When the gate is always red, agents can't tell their own breakage from someone else's. They proceed or stall, which lets the next break land, which keeps the gate red.
- **This is the gate that `#bd/work_phase_bead` and `#bd/land_epic` rely on.** Those are your two highest-volume prompts.
- **Green checks will be slow.** The headline "check ≈ 2m30s" is mostly fail-fast. When lint passes, the scoped test stage alone has a **P50 of 17 minutes**, so a green gate costs roughly 20 minutes per run. That limits how many verifying loop iterations fit in 48 hours.
- **You've noticed it too:** "master is always red" (09-28 prompt), along with no PyPI release since v0.17.1 on 08-29 *(survey)*.

### 3.2 Failure queues are filled faster than they are drained *(survey: `sase bead list -T flake|bug|ci`)*

- **Flakes:**
  - 144 flake beads all-time, 79 of them in the last 14 days.
  - Of 37 closed in those 14 days, 34 were "stale task bead swept from triage" and **about 1 was actually fixed**.
  - 48 of the 91 active flakes match "fails under the full parallel lane, passes in isolation". That pattern points to a small number of shared-state root causes, so fixing one cluster should close several beads.
- `tests/reproducible_flake_baseline.txt` has **86 live entries**. Its own header says "Entries are debt to remove, not suppressions to grow."
- **Bugs:** 57 were swept as canceled and 26 were done in 14 days.
- **Lesson:** the bottleneck is fixing, not finding. A loop that only finds things adds to triage you have already given up on.

### 3.3 Work that is finished but never landed *(survey)*

- 97 sase epics are in progress, and **36 have every phase closed but were never landed**. The oldest is sase-lh, at about 47 days.
- 61 in-progress phase beads haven't been touched in over 7 days.
- Land agents for sase-1c1 (the CI-repair epic), sase-1bc and sase-1ab.10 have been WAITING since 09-27/28. I saw them in `sase agent list`.
- `#bd/land_epic` already says that a check failure which reproduces on the clean base tree should not block landing. So this queue is not only a symptom of §3.1: something in launching or waiting stalls too, and it needs diagnosing per epic.

### 3.4 bob-cli: master is red, there is no CI, and the grammar has no property tests

- **Master is red right now.** At `779cc0c`, `cargo test --lib` gives **1,413 passed, 5 failed**, all in `native::capture_pomodoro_close::linked_task_tests`.
  - Cause *(survey)*: commit 3cd4d44 (freshness epic bob-cli-31) began stamping `[fresh:: …]` on rewritten tasks.
  - The close tests from 15c6341 (Work Log epic bob-cli-32) assume there is no stamp.
  - Two epics that landed in parallel collided, and **nothing caught it, because bob-cli has no `.github` CI**. `just all` runs clippy without `-D warnings`.
- **Clippy:** about 55 warnings *(survey)*. Bead bob-cli-v recorded 3–5, so the count has grown.
- **Flaky tests:** two known flakes, bob-cli-2e (`BOB_DAY_FILE` env race, seen live by the survey) and bob-cli-2m (EPIPE).
- **Capture grammar:** `src/native/capture_language/` is about 19.8k lines, and `docs/capture.md` is 3,501 lines with about 200 table rows.
  - There is **no proptest, quickcheck, insta snapshot, cargo-fuzz or cargo-mutants** anywhere.
  - The JSON contract with Bob Mac Capture (`schema_version: 1`) is checked only by inline assertions and by Mac fixtures captured once by hand.
  - Nothing detects drift between bob's output and those fixtures.
- **Churn:** 134 commits in 30 days, 88 of them on Sep 28–30. Agents write to this code very fast, and it is the code that edits your personal vault.
- **Large files:** 17 files in `src/` are over 1,500 lines. The largest is `capture_complete.rs` at 4,261.
- **bob-plugins:** 927 `node:test` cases with 1 failing (`test-ledger-tools-freshness.cjs:768`). No types, lint or CI. `bob-navigation-hotkeys/main.js` is 31.6k lines *(survey)*.
- **bob-mac-capture:** the CaptureCore half (536 tests) **runs on Linux** and passes in 31 seconds *(survey)*. A contract harness between the two repos is therefore feasible on athena.

### 3.5 Satellite repos *(survey)*

- **sase-core (Rust, about 499k lines):**
  - **56 files over 1,500 lines**, which the hourly toobig job doesn't cover.
  - About 4.3k non-test `.unwrap()` calls.
  - No coverage, proptest or fuzzing.
  - 8 of the last 40 master CI runs failed.
  - Releases go out automatically through release-plz, so any loop there must not change behavior.
- **sase-telegram** (684 tests, green), **sase-github** (215 tests, green) and **actstat** (141 tests, green, in production every 5 minutes): safe places for test-only loops, but low leverage compared with sase itself.
- **bugyi-chops** is red at HEAD; that is a one-shot fix, not a loop. toobig is dormant. sase-nvim has no runner or CI yet, so a loop there has nothing to check against.
- **Security:** I checked one obvious risk. The Telegram receiver can launch agents, but it **does reject unauthorized chats** (`inbound_handlers/dispatch.py:73`). A security sweep is still reasonable as a single swarm. It is not urgent enough to loop for 48 hours.

### 3.6 Capacity and mechanics constraints

- **athena:** 64 cores and 62 GiB RAM. At 23:14 about 28 GiB was available and the load average was about 17.
- **Check memory:** `tree RSS peak p90 15.7 GiB` (from only 5 sampled runs). The check stats also show 185 runs killed at the time ceiling.
- **Practical limit:** about 2–3 concurrent full sase checks before the gate itself becomes the flake source. That is consistent with the import-budget test being classed flaky (29 runs).
- **Agent cap:** `max_running_agents: 10` host-wide (default in sase's `default_config.yml`; not overridden in `~/.config/sase`). The five-researcher swarm and the in-flight epics already hold many of those slots.
- **Pipe-chain cap:** `max_agent_pipe_chain` defaults to **8**. The sase project temporarily sets 40, but **bob-cli inherits 8**.
- **`%repeat:N`** (docs/xprompt.md, "Repeat Directive"):
  - spawns N agents up front, each with its own workspace and fresh context
  - wait-chains them serially
  - exposes `{{ n }}`/`{{ N }}`
  - lets any slot stop the rest with `sase var set STOP=1`

  This is the right primitive for working through a queue.
- **Axe routines** (`run_every` + `inhibit_if` on a clan prefix) are the right primitive for something time-driven that should outlive the window. Your `toobig_split` job is the model.
- **No goals are set:** `sase goal list` shows no active goals for either sase or bob-cli.

**Usage snapshot** (`sase usage`, about 23:00):

| Provider | Weekly remaining | Resets in |
|---|---|---|
| Claude (all models) | 37% | about 2 d |
| Fable | 100% | about 2 d |
| Codex | 91% | about 2 d |
| Grok | 57% | about 34 h |
| Muse | 48% | about 3 d |

---

## 4. What makes a good 48-hour loop

External evidence, summarized:

- **An objective check the agent can't edit is the deciding factor.**
  - Anthropic's long-running-agent harness (initializer, then one feature per worker, then a progress file) and its C-compiler case study both say the verifier must be "nearly perfect", or the agent solves the wrong problem ([Anthropic, 2025-11-26](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents); [Carlini, 2026-02-05](https://www.anthropic.com/engineering/building-c-compiler)).
  - Agents game weak checks. On impossible tasks GPT-5 cheated 76% of the time, mostly by editing tests, but an explicit "STOP if the tests are flawed" instruction cut cheating sharply ([ImpossibleBench, 2025-10](https://arxiv.org/abs/2510.20270)).
- **Ralph-style loops** do one item per iteration, keep state on disk and reset hard on failure. They suit greenfield or spec-driven work. Huntley himself warns against using them on an existing codebase without strong backpressure. The known failure mode, "overbaking", is a loop that keeps running after its queue is empty and starts adding things nobody asked for ([Huntley, 2025-07-14](https://ghuntley.com/ralph/); [Horthy, 2026-01-06](https://www.humanlayer.dev/blog/brief-history-of-ralph)).
- **Loop work with measured payoff:**
  - mutation-guided test generation (Meta's ACH turned 9,095 mutants into 571 tests; engineers accepted 73% of them — [2501.12862](https://arxiv.org/abs/2501.12862))
  - property-based bug hunting (56% of bug reports valid, 86% with a ranking rubric — [Anthropic, 2026-01-14](https://www.anthropic.com/research/property-based-testing))
  - large mechanical migrations, where retrying failed items beat perfecting the prompt ([Airbnb, 2025-03](https://medium.com/airbnb-engineering/accelerating-large-scale-test-migration-with-llms-9565c208023b))
  - flaky-test repair (FlakyGuard fixed 47.6% of reproducible flakes — [2025](https://www.researchgate.net/publication/397740228_FlakyGuard_Automatically_Fixing_Flaky_Tests_at_Industry_Scale))
- **Where loops do poorly:**
  - ambiguous product or design work
  - work where "tests pass" is mistaken for "mergeable" ([METR, 2025-08-12](https://metr.org/blog/2025-08-12-research-update-towards-reconciling-slowdown-with-time-horizons/))
  - output that piles up review load: one study saw review time rise 91% under heavy AI use ([Faros, 2025-07](https://www.faros.ai/blog/ai-software-engineering))
- **Duplication accumulates** under AI authorship (8× rise in duplicated blocks, [GitClear, 2025-02](https://www.gitclear.com/ai_assistant_code_quality_2025_research)). "Agents amplify what they see", so cleanup compounds.

**Selection criteria used below.** A good loop for this window:

- **(a)** has a check the agent can't edit
- **(b)** draws from a queue of small, independent items that can be generated live
- **(c)** has a metric that only moves one way, so done can be detected mechanically
- **(d)** has small, mechanical diffs, so review is cheap
- **(e)** keeps paying back after the window ends
- **(f)** doesn't fight the ~90 commits a day landing on sase master, or the active bob-cli epics

---

## 5. Candidate loops, evaluated

| # | Candidate | Value | Check the agent can't edit | Review cost | Main risk | Verdict |
|---|---|---|---|---|---|---|
| A | **sase master sheriff:** keep clean origin/master passing `check` | Very high: unblocks every agent and every other loop; recovers part of the 51.7 h/week waste | `check` on a clean tree: binary, and the agent can't edit it as long as guards are off-limits | Low: small fixes, each tied to a breaking commit | Sheriff "fixes" by weakening a guard, or deletes a symbol a pending phase needs | **Do first** |
| B | **sase de-flake**, one cluster per iteration | High: 91 active flakes, 86 baseline entries, about 1 real fix in 14 days | Reproduce-before / 20 passes after under the parallel lane; `selection-health --fail-on-new-flake` | Low–medium | Timeouts or retries passed off as fixes; CPU contention invalidating the evidence | **Do** |
| C | **bob-cli: green + CI, then mutation/property hardening** | High per token: it's your daily tool and writes your vault; red master today; no CI | `cargo test`/clippy `-D warnings`; mutants killed; proptest invariants | Low (mostly tests) | Collides with in-flight epics bob-cli-28/31/32 in the same files; needs proptest and cargo-mutants installed | **Do** |
| D | **Land the 36 stranded sase epics** | High: finished work you've already paid for becomes shipped | `#bd/land_epic`'s own verify, integrate and close steps | Medium (integration diffs) | Pointless while the gate is red; collisions between concurrent landings | **Do once A has the gate green at least intermittently** |
| E | **Cross-provider auditor** of all loop commits | Medium–high: insurance against the test-cheating failure mode, using tokens in place of your review | LLM judgment, aimed narrowly at weakened tests and guards and at unintended behavior changes | Low (exceptions only) | False alarms; over-engineering fixes | **Run alongside A–D** |
| F | **TUI performance ratchet: counters, not clocks** | High subjective value (flicker, lag, startup and unread latency are your most repeated complaints) | Deterministic counters such as imports, queries, file reads and renders per keystroke. Wall-clock time is too noisy on a loaded host: the import-budget test is already flaky | Medium | TUI is the defect hotspot (74 of 219 recent fixes); visual goldens are already drifting (sase-x5) | **Do, after one planning step builds the harness** |
| G | **Rust file splits** (sase-core 56, bob-cli 17 over 1,500 lines) via your existing `#split_epic` | Medium: smaller files mean cheaper, more accurate agent reads, which your 1,930 split prompts suggest you value | Compiler + clippy + tests + line counts | Low | Conflicts with hot bob files under active epics; sase-core CI is already intermittently red | **Do in sase-core now; in bob-cli after its epics land** |
| H | **sase TUI type ratchet** (4,009 `[attr-defined]` ignores from the mixin pattern) plus a one-shot ruff F401/F821 cleanup (843 unused imports, 22 undefined names in tests, 1,202 no-op `noqa: BLE001`) | Medium: types would catch real attribute bugs in the hotspot | mypy; the ignore count only goes down | Low | Touches hundreds of TUI files at once, risking merge conflicts with epics in flight | **Optional filler; do F401/F821 once** |
| I | **Satellite test hardening** (sase-telegram coverage, actstat wiremock edge cases, sase-core proptests) | Low–medium | Tests plus coverage that only goes up | Very low | Low leverage | **Filler lane for idle capacity** |
| J | Duplicate-function consolidation (537 groups, about 6.1k lines) | Medium | Tests | Medium | Subtle behavior differences between the copies; churn | Later, not this window |
| K | Feature-flag retirement | Low now | — | — | No flag is due before 2026-11-17; the removal criteria need soak time | Skip |
| L | Find-and-file audit loops (`recent_bug_audit`) | Negative while triage is saturated | — | High (triage) | Adds to the queue sweeps already empty | **Skip** unless rewritten as find-*and-fix* |
| M | New feature epics, mass research swarms | Taste-heavy; review debt outlasts the window | — | High | — | **Skip** |

---

## 6. Running loops in SASE: the recommended operating model

1. **Use the right primitive:**
   - **Queue-draining lanes** (B, C, D, G, H, I): `%repeat:N` with `sase var set STOP=1` when the queue is empty.
     - Each slot gets a fresh context and its own workspace, so state lives in git and in live queries, not in the chat.
     - Make each iteration **re-derive its queue from a live command**: `sase tool failures -j`, `sase bead list -T flake`, `cargo mutants --list`, `git log --grep`. A slot that dies then costs only its own item.
   - **The time-driven sheriff** (A): an axe routine shaped like `toobig_split`, with `run_every` of about 15m and `inhibit_if: agent_clan.name_prefix: sheriff-`. It can stay installed after the window. For the window alone, a long `%repeat` chain also works, because each iteration's check (about 4–20 minutes) paces it.
   - **`/sase_handoff`** (`sase pipe`): only for continuing a single item that ran out of context.
     - Use `-f` for a fresh context.
     - Raise `max_agent_pipe_chain` for the window if you rely on it. bob-cli is capped at 8.
   - **Before an overnight run,** test what a *failed* `%repeat` slot does to its successors on a 3-slot toy chain.
2. **One item per iteration, proven, committed, then a recorded metric.** Every lane's prompt ends with `sase var set` of its metric:
   - the sheriff's `CHECK=green|fixed`
   - de-flake's `FIXED=<node>`
   - bob hardening's `KILLED=k/s`

   That way you can check progress from Telegram without reading diffs.
3. **Anti-cheat rules in every prompt** (from ImpossibleBench): never delete or loosen an assertion, guard, baseline, budget, timeout or lint rule. Never regenerate a snapshot without explaining each changed line. If that seems to be the only option, stop and write a **DECIDE** note instead.
4. **Funnel ambiguity into one DECIDE queue** that you review twice a day. Use a bead note prefix or a single tracking bead; your choice. Never let a loop guess at intended behavior.
5. **Spend the surplus tokens on verification, not volume.**
   - Pair lanes across providers: Muse/Codex do the work, while a Claude/Fable auditor (lane E) reviews each batch of commits since its last audited SHA, and vice versa.
   - For the hardest chronic bugs (TUI flicker, which you've noted "we've tried to fix several times"), run best-of-3 across providers and judge with your `#prs/compare` xprompt.
6. **Capacity plan:**
   - At most **2–3 lanes that run a full sase `check` at the same time**: A, B and D in sequence or alternating.
   - Run bob-cli lanes alongside them; warm `cargo test` takes about 18 s and is light.
   - Satellite lanes fill whatever is left.
   - Consider raising `max_running_agents` from 10 to about 14 for the window, provided you watch memory pressure. `%dispatch` to apollo adds capacity that doesn't compete for athena's memory.
7. **Optionally, set `sase goal new` for each lane** with a measurable outcome, for example "clean-master check pass rate ≥ 80% over 24 h". Agents can read goals, and you get one place to see progress.

---

## 7. Starter prompts for the top lanes

These are sketches written in your directive vocabulary. Check directive spelling and model aliases against your config before launching. Fenced so that `#`/`%` aren't expanded while you read this file.

### Lane A: sase master sheriff

```text
%repeat:100
%id:sheriff
#m_opus
You are iteration {{ n }}/{{ N }} of the sase MASTER SHERIFF loop. Your only job: a
clean checkout of the newest origin/master must pass `sase tool run check`, and every
guard must stay exactly as strict as it was.

1. Sync to the newest origin/master with no local edits; run `sase tool run check`
   (via /sase_monitor). If it passes: `sase var set CHECK=green SHA=<sha>` and finish.
2. If it fails, take the first failing stage. Use `sase tool failures -t check` to see
   how many agents the signature has hit. Find the master commit that introduced it
   (bisect recent master commits running only that stage).
3. Fix it with the smallest change consistent with what that commit meant to do: the
   registry, snapshot, or schema entry it forgot; a half-landed rename; an epic-symbol
   whitelist entry when the "unused" symbol belongs to an open epic phase.
4. Forbidden: loosening or deleting any assertion, guard, baseline, budget, timeout, or
   lint rule; regenerating a snapshot without justifying each changed line; deleting a
   symbol an open epic phase still plans to use. If one of those looks like the only
   fix, leave a DECIDE note on the responsible bead instead and finish.
5. Commit, rerun the stage, then `sase var set CHECK=fixed STAGE=<stage>
   CAUSE=<sha> SYSTEMIC="<which cheaper, earlier gate would have stopped this commit>"`.
```

**Systemic follow-up.** After about 24 hours, read the `SYSTEMIC` vars and plan *one* prevention change: run the cheap repo-wide-invariant stages before commit or push. Terminology (6 s), keep-sorted, ruff and fmt each take seconds, and flags and symvision take about a minute each, against roughly 17 minutes for scoped tests. This is a design decision for you to approve; don't let a loop make it.

### Lane B: sase de-flake

```text
%repeat:40
%id:deflake
#m_codex
You are iteration {{ n }}/{{ N }} of the sase DE-FLAKE loop. Fix exactly ONE flaky test
(or one cluster with a shared root cause), for real.

1. Pick: the highest-run signature classed `flaky` in `sase tool failures -t check -j`,
   else the open `flake` bead with the most +1s. Skip items noted by another deflake
   iteration in the last 24h.
2. Reproduce BEFORE editing, under the same parallel lane that fails (not in isolation).
   No reproduction within 30 minutes: note what you tried on the bead, +1 it, and move
   to the next item (at most 2 items per iteration).
3. Fix the shared-state cause: env vars, HOME/XDG, cwd, tmp paths, module-level caches,
   ports, wall clock, import-time side effects, ordering. Forbidden: retries, bigger
   timeouts, skip/xfail, new baseline entries, deleted assertions.
4. Prove: 20 consecutive passes under the parallel lane plus the scoped check. Retire
   the node in tests/reproducible_flake_baseline.txt with `# fixed-at:` per its header;
   close the bead with the evidence; `sase var set FIXED=<node>`.
5. Nothing flaky left: `sase var set STOP=1`.
```

### Lane C: bob-cli. Do the one-shots first, then loop.

**One-shots, about an hour of agent time, plus one decision from you:**

1. Decide whether `=x` closes should stamp `[fresh:: …]`. The bob-cli-31 spec suggests yes, in which case the 5 tests are what's stale.
2. Fix the 5 red tests.
3. Add `.github/workflows/ci.yml` running fmt, `clippy --all-targets -D warnings` and `cargo test`.
4. Add `bobs-org/bob-cli` to `ci_watch`'s repo list.
5. Close bob-cli-v (clippy), 2e and 2m (flakes).
6. Fix the failing bob-plugins test.
7. Install `cargo-mutants` and add `proptest` as a dev-dependency.

Then the loop:

```text
%repeat:20
%id:bobharden
You are iteration {{ n }}/{{ N }} of the bob-cli HARDENING loop. Harden exactly one
vault-writing module.

1. Target = first entry with no `test(harden): <entry>` commit yet
   (`git log --oneline --grep 'test(harden)'`): src/native/task_status_hooks_write.rs,
   capture_task_toggle.rs, capture_pomodoro_close/, capture_task_sections.rs,
   capture_links.rs, capture_clip.rs, randomize_plan.rs, vault_sync.rs, then one
   capture_language/ submodule per iteration.
2. `cargo mutants --file <target> --timeout 120`; list survivors.
3. Add tests (only #[cfg(test)] modules or tests/) that kill survivors and assert
   properties: no panic on arbitrary input; --dry-run never writes; applying the same
   capture / hooks run twice == once; CRLF and unicode round-trip; nothing outside the
   target note changes. Use temp vaults only — never ~/bob.
4. A survivor or property that exposes a real bug: failing test first, smallest fix,
   say so in the commit body. Unsure whether behavior is intended: #[ignore = "DECIDE: …"]
   plus a DECIDE note. Never guess.
5. Gate: fmt, clippy -D warnings, `cargo test` twice. Commit
   `test(harden): <target> — killed K/S`; `sase var set KILLED=K/S`.
6. List exhausted: `sase var set STOP=1`.
```

Wait until bob-cli-28, bob-cli-31 and bob-cli-32 have landed before targeting the capture files those epics are touching. Start with `task_status_hooks_write.rs`, `vault_sync.rs` and `randomize_plan.rs`.

**One-shot worth adding to lane C:** a Linux contract harness. It replays each Bob Mac Capture JSON fixture's scenario against the current `bob` in a temp vault with `BOB_NOW` pinned, diffs the output, then runs CaptureCore `swift test`, which passes on athena. After that, drift in the capture contract fails a test instead of reaching your Mac.

### Lane D: land stranded epics (start once lane A has the gate green at least intermittently)

Have one agent list the in-progress epics whose phases are all closed and that have no live land agent, oldest first, each with a one-line reason it stalled. Then launch one `#bd/land_epic:<id>` per epic as a serial `%wait` chain, the mechanism you already use, at most one or two landings in flight. When master is green, cut the 0.18 release.

---

## 8. A 48-hour schedule

| When | You | Loops |
|---|---|---|
| **H0–H1** (you're awake) | Make the bob-cli freshness decision. Create goals. Optionally raise `max_running_agents` to about 14. Kick off the lanes. | Start **A** (sheriff) and **B** (de-flake). Start the **bob-cli one-shots**. Start **G** on sase-core (`#split_epic`, Rust, 1,500 lines). |
| **H1–H12** | Glance at the `sase var` metrics via Telegram. | A, B, C one-shots, then the C loop, plus G. Run **E** (auditor) every few hours over all loop commits. |
| **H12** (first review) | Clear the DECIDE queue. Read the check pass-rate trend in `sase tool stats -t check -d 1`. | If clean-master check is passing more often than not, start **D** (landings). |
| **H12–H36** | Second review around H24: read the `SYSTEMIC` vars and approve the one prevention change. | A, B, C, D, E. Build the **F** harness (one planning agent) and start the F loop. **I** fills idle slots. |
| **H36–H48** | Final review. Decide which loops become permanent axe routines. The sheriff is the obvious one. | Wind down D and F. Cut the sase release once the gate is green. |

---

## 9. What I would not spend the window on

- **New feature epics.** You lead design closely (558 `#beau` prompts). Features need your taste and leave review and maintenance debt that outlasts 48 hours.
- **Find-and-file loops.** Bug sweeps already cancel more beads than they close (57 swept vs 26 done in 14 days). New findings only help if the same iteration fixes them.
- **More research swarms.** Their output costs reading time, which is the scarce resource.
- **Python file splitting and docs refresh.** Both are already automated.
- **Feature-flag retirement.** Nothing is due before mid-November, and the criteria need soak time.
- **Unbounded "improve the codebase" loops.** These overbake. Give every lane a queue, a metric and a STOP condition.

---

## 10. Caveats

- The check ledger only starts on 2026-09-20. Its OK/FAIL numbers include runs on agents' own dirty trees, so some failures were self-inflicted. The cross-agent counts per signature (44–66 agents for one symvision or flag signature) are what show the shared, master-level breakage.
- I don't know which provider is the "near infinite" one. Put lanes A, B and E on the strongest reasoner you have in surplus, the mechanical lanes (G, H, I) on your Muse/Codex workhorses, and pair each lane with a reviewer from a different provider.
- The figures for stranded epics and flake/bug bead counts come from a sub-survey that read the sase bead store. Re-derive them live at H0. The loops are designed to query their queues live anyway.
- I have not tested `%repeat` failure semantics (what a failed slot does to the chain) or the exact argument syntax for `#split_epic`. Smoke-test both before leaving anything overnight.

---

## 11. Ranked recommendations

1. **Run a sase master sheriff (lane A), starting now and probably keeping it afterwards.**
   - *Why:* check passed 36 of 1,091 runs this week, with 51.7 hours of waste and 0–2 passes a day since 09-27. Every other loop and all of your epic work depends on this gate.
   - *Shape:* an iteration only fixes clean master, never by weakening a guard, and records the systemic cause of each break.
   - *Afterwards:* approve one prevention change (cheap invariant stages before commit or push) based on what the sheriff recorded.
2. **Run a sase de-flake loop (lane B), one root cause per iteration, with reproduce-before and 20-passes-after proof.**
   - *Why:* 91 active flakes and 86 baseline entries, with about one real fix in 14 days. Half the flakes share an "isolated pass / parallel fail" signature, so fixes come in clusters.
   - *Payoff:* every closed root cause permanently cuts wasted check runs.
3. **Harden bob-cli (lane C).**
   - *First, today:* fix the 5 red tests, add CI with `clippy -D warnings`, and add bob-cli to `ci_watch`.
   - *Then:* a mutation- and property-test loop over the vault-writing modules, plus a Linux Bob↔Mac contract harness.
   - *Why:* it's the tool that edits your personal notes every day. Master is red right now because two epics collided, and there's no CI, no property tests, and no drift detection against the Mac fixtures.
4. **Land the stranded sase epics (lane D) once the gate is meaningful, then cut 0.18.**
   - *Why:* about 36 epics have every phase closed but were never landed. That's finished work you've already paid for, it's blocked, and you currently relaunch these by hand. Your existing `#bd/land_epic` prompt does the work.
5. **Run a cross-provider auditor (lane E) over every loop's commits.**
   - *Why:* surplus tokens are best spent on verification. A different model, scoped narrowly to weakened tests and guards and unintended behavior changes, is cheap insurance against the documented failure mode where agents edit the check to pass it.
6. **Run a TUI performance ratchet built on deterministic counters (lane F).**
   - *Why:* flicker, typing lag, startup time and unread latency are your most repeated complaints.
   - *Shape:* one planning agent builds a headless scenario harness that counts imports, queries, file reads and renders per action. The loop then lowers one budget per iteration. Counters avoid the wall-clock noise that already makes the import-budget test flaky.
7. **Split the oversized Rust files with your existing `#split_epic` (lane G).**
   - *Scope:* sase-core first (56 files over 1,500 lines, not covered by toobig); bob-cli's 17 after its active epics land.
   - *Why:* low risk because the compiler checks each step, low review cost, and it lowers the cost of every future agent read.
8. **Ratchet types in the sase TUI (lane H), plus a one-shot ruff F401/F821 cleanup.**
   - *Why:* replacing the 4,009 `[attr-defined]` ignores with typed mixin protocols lets mypy catch real bugs in your defect hotspot. Run it only in idle capacity, because the churn will collide with TUI epics.
9. **Use satellite test hardening as filler (lane I)** whenever slots are idle: sase-telegram coverage, actstat GitHub edge cases, sase-core proptests.
   - *Why:* safe and green, but low leverage. Use it so no capacity sits idle, not as a priority.
