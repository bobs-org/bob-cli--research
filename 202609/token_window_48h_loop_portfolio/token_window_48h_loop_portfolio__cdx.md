# Spending a 48-hour abundance of agent tokens well

**Independent research report (`cdx`) — 2026-09-30**

## Executive conclusion

The best use of a temporary, nearly unlimited token budget is not a single 48-hour
assignment. It is a sequence of short, independently verifiable searches that leave
behind durable tests, minimized counterexamples, evaluation cases, or resolved tasks.
The scarce resources are reliable oracles, clean handoffs, wall-clock time, and Bryan's
review attention—not model output.

My strongest recommendation is to build and run a **semantic counterexample factory for
Bob**: agents repeatedly choose one invariant in the capture/vault state machine,
generate adversarial cases, minimize any counterexample, and leave either a regression
test plus fix or a demonstrably stronger test harness. Bob is unusually well suited to
this because it has a large combinatorial language, many interacting state transitions,
existing differential/parity fixtures, and a mature conventional test suite, but no
property-testing or fuzzing dependency today.

My second recommendation is more leveraged but harder to bootstrap: a **SASE
harness-evaluation flywheel** that mines recurring agent failures, turns one failure at
a time into a reproducible evaluation, makes the smallest prompt/skill/tool-interface
change, and A/B tests it over independent runs. If it works, it improves every later
agent hour rather than only one repository.

I would not run all the ideas below. I would choose one primary loop, keep a second as a
reserve when the primary is blocked, and reserve the final six hours for consolidation.

## What makes a good abundance-window loop

The useful unit is not “keep an agent busy.” It is a bounded attempt with a state
transition that a successor can verify. I used these criteria:

1. **Verifier strength.** Can a machine distinguish progress from plausible prose?
2. **Token elasticity.** Do more independent hypotheses or critiques improve the odds,
   rather than merely making the output longer?
3. **Durability.** Does each pass leave tests, fixtures, an eval case, a fix, or a
   decision-ready artifact that retains value after the cheap-token window?
4. **Handoffability.** Can a fresh agent make progress from a small frontier record
   without inheriting the whole transcript?
5. **Low human bottleneck.** Can most iterations settle without asking Bryan a policy or
   taste question?
6. **Safety and reversibility.** Can the loop stay in temporary vaults/worktrees and
   avoid mutating live data or external systems?
7. **A real stop rule.** Can the loop recognize saturation, duplication, or declining
   marginal value?

This selection rule is supported by several independent findings:

- Anthropic reports that its multi-agent research system beat a single-agent setup by
  90.2% on an internal breadth-first research evaluation, that token use alone explained
  80% of BrowseComp performance variance, and that its multi-agent system used about 15
  times the tokens of ordinary chats. The same report warns that coding tasks with many
  dependencies are less parallelizable. The implication here is to spend abundance on
  independent searches and trials, not on many agents concurrently editing the same
  state. [Anthropic, “How we built our multi-agent research system”](https://www.anthropic.com/engineering/multi-agent-research-system)
- METR defines agent time horizon on self-contained tasks with clear, automatically
  evaluated success criteria and explicitly distinguishes a thousand independent
  one-hour tasks from one thousand-hour task. It also reports worse performance on
  messier work and warns against generalizing clean benchmark performance to ordinary
  jobs. The relevant inference is to slice the 48 hours into short, clean episodes.
  [METR, “Task-Completion Time Horizons of Frontier AI Models”](https://metr.org/time-horizons/)
- AlphaEvolve's useful general pattern is proposals plus objective evaluators plus a
  database of prior candidates. DeepMind says the system is most applicable where
  solutions can be systematically scored. That is a better model for token abundance
  than unconstrained self-reflection. [Google DeepMind, “AlphaEvolve”](https://deepmind.google/blog/alphaevolve-a-gemini-powered-coding-agent-for-designing-advanced-algorithms/)
- A 2025 property-based refinement paper reports 23.1%–37.3% relative pass@1 gains over
  its TDD baselines and emphasizes independent properties plus structurally minimal
  counterexamples. The exact numbers should not be assumed to transfer to Bob, but the
  mechanism directly addresses the risk that an agent writes tests sharing the same
  misconception as its implementation. [He et al., “Use Property-Based Testing to Bridge LLM Code Generation and Validation”](https://arxiv.org/abs/2506.18315)
- Fuzzing is a proven durable search loop: OSS-Fuzz reports more than 10,000
  vulnerabilities and 36,000 bugs across 1,000 projects, including memory-safe
  languages such as Rust. [OSS-Fuzz documentation](https://google.github.io/oss-fuzz/)
- Mutation testing supplies a stronger adequacy signal than coverage alone. Google's
  large-scale work recommends incremental, filtered mutants rather than mutating an
  entire codebase, and its longitudinal study found that mutation-guided developers
  wrote better tests and that surviving mutants were coupled with real faults.
  [Practical Mutation Testing at Scale](https://research.google/pubs/practical-mutation-testing-at-scale-a-view-from-google/),
  [Long Term Effects of Mutation Testing](https://research.google/pubs/long-term-effects-of-mutation-testing/)
- DORA's 2025 conclusion is a useful caution: AI is an amplifier of the surrounding
  system's strengths and weaknesses. An unverified loop scales defects and clutter as
  readily as value. [DORA, State of AI-assisted Software Development 2025](https://dora.dev/research/2025/dora-report/)

The reported percentages above come from vendor/internal evaluations or research
benchmarks, not from this repository. I use them as evidence for loop design, not as
promised Bob productivity gains.

## Local opportunity: why Bob is a particularly good target

I inspected the current `bob-cli` checkout and its live work graph, without consulting
any peer report from this swarm.

- The checkout contains about **197,932 lines of Rust across `src/` and `tests/`**, 221
  Rust source files, 77 Rust integration-test files, and approximately 2,243 Rust
  `#[test]`/`#[tokio::test]` attributes. It is mature enough that generated cases can be
  anchored in real contracts rather than guessed behavior.
- The capture contract is highly combinatorial: routing, task IDs, Pomodoro selection,
  link outcomes, session starts/closes/shifts, batch atomicity, work logs, schedules,
  priorities, completion, JSON previews, and cross-client presentation interact.
- There are already differential and parity footholds: native Dataview versus Obsidian,
  native Tasks versus Obsidian Tasks, plugin parity cases, round trips, and many explicit
  idempotence checks.
- `Cargo.toml` currently has no `proptest`, `quickcheck`, `arbitrary`, `libfuzzer`,
  `cargo-fuzz`, or equivalent testing dependency. That is not a defect, but it means the
  existing suite has not yet exploited a systematic generative search layer.
- The active SASE graph contained **17 ready tasks and 7 in-progress nodes** at the time
  of inspection. The ready queue includes data-durability, artifact-event integrity,
  timezone, concurrent environment mutation, broken-pipe, link-duplication, and stale
  line-index defects. This is direct evidence that the system still has high-value edge
  conditions despite its large example-based suite.
- Three feature epics were already in progress. A new broad feature swarm would compete
  with moving contracts; a test/search loop can instead work on stable slices and make
  those contracts safer.

This combination—dense state space, strong existing examples, and missing generative
search—is the clearest high-return opportunity I found.

## Recommendation 1: a Bob semantic counterexample factory

### Goal

Create a repeatable loop in which each agent adds one independently justified property,
generator, differential oracle, or minimized regression case around Bob's semantics.
Fix an exposed defect only after the counterexample is captured. The output is a growing
executable specification, not a pile of speculative bug reports.

### Best initial surfaces

1. **Capture parser and rewrite algebra**
   - rewriting is idempotent;
   - parse/rewrite preserves semantic intent;
   - insignificant whitespace or line-ending transformations do not alter actions;
   - completion acceptance produces a draft the parser classifies as promised;
   - unsupported combinations fail deterministically and without mutation.
2. **Planner/apply equivalence and atomicity**
   - dry-run plans predict live application on a temporary vault;
   - any failing item in a batch leaves all files byte-for-byte unchanged;
   - rerunning idempotent commands produces no diff;
   - stale-file and lock failures never partially apply a plan.
3. **Task/Pomodoro state transitions**
   - link cardinality never exceeds one where uniqueness is required;
   - sticky Next/Pending lanes never fall without the explicit release gesture;
   - Blocked is a function of future schedule and dependencies;
   - close/start chains equal the corresponding sequential operations when the contract
     says they should;
   - task numbering and typed Work Log targeting remain stable under unrelated children.
4. **Time and environment metamorphisms**
   - an explicit `BOB_NOW` produces the same result under different host time zones;
   - boundary dates, DST transitions, midnight, and the post-8pm case do not select a
     different daily note unexpectedly;
   - test-global environment changes are serialized.
5. **Existing external oracles**
   - expand native/Obsidian Dataview and Tasks differential corpora;
   - compare plugin-originated and CLI-originated equivalent edits;
   - compare JSON previews with the exact mutation later applied.

### Iteration contract

Each pass should take roughly 45–120 minutes and do exactly one of the following:

- land one meaningful property/generator that kills at least one relevant mutant;
- produce one minimized, deterministic counterexample and a regression test, then fix
  it if the scope is bounded;
- prove that a suspected discrepancy is intended, record the contract evidence, and
  remove it from the frontier.

An iteration is not successful merely because it adds random inputs or line coverage.
The test oracle must be independent of the implementation under test. Prefer algebraic
properties, an existing external implementation, pre/post-state invariants, or a tiny
reference model. Every random failure must print and persist its seed and shrink to a
small fixture.

The loop must use only temporary fixture vaults. It should never fuzz `~/bob`, invoke a
live sync, deploy plugins, close a real Pomodoro, or change remote state.

### Durable frontier

Use an ordinary tracked test-frontier document—not SASE memory—with rows such as:

| Surface | Property/oracle | Generator status | Mutant killed? | Counterexample/fix | Next edge |
| --- | --- | --- | --- | --- | --- |

The successor should receive that file, the test command, the last deterministic seed,
and at most three best next targets. This avoids handing an ever-growing transcript to
the next context.

### Stop rule

Stop a surface after three consecutive well-targeted iterations add neither a killed
mutant nor a new behavior distinction, or when the only remaining oracle is “the current
implementation says so.” Switch surfaces rather than manufacturing low-value tests.

## Recommendation 2: a SASE harness-evaluation flywheel

### Why it could compound more than repository work

SASE mediates future agents, tools, skills, finalization, plans, artifacts, and repo
access. A recurring mistake eliminated in the harness pays back on every later task.
Anthropic reports that a tool-testing agent which repeatedly exercised a flawed tool and
rewrote its description reduced later task completion time by 40% in its environment.
That number is not portable, but the intervention is unusually compatible with a
temporary abundance of independent model trials.

### Loop

1. Choose one recurring, objectively observable failure class from historical runs:
   wrong tool choice, repeated invalid command, missed handoff wait, stale final
   manifest, forgotten repo open, unnecessary clarification, duplicate task filing, or
   bloated context.
2. Build a small redacted evaluation set with success/failure criteria. Exclude this
   current five-researcher swarm so the experiment cannot leak peer findings.
3. Run the existing harness several times with fresh contexts and record baseline pass
   rate, tool calls, wall time, and tokens.
4. Make the smallest plausible change: a tool description, skill instruction, example,
   validator, or deterministic guard. Avoid bundling changes.
5. A/B test on held-out cases and one adversarial variant. Revert changes that merely
   overfit the training transcript.
6. Commit the eval, measured result, and change; update a compact experiment ledger;
   hand off the next highest-frequency failure.

### Guardrails

- Never improve a prompt on anecdotes alone.
- Separate the agent proposing a harness change from the evaluator or use blind labels.
- Require repeated independent runs for nondeterministic outcomes.
- Prefer deterministic product constraints over more prompt prose when both solve the
  failure.
- Track regressions in completion quality, not only token or latency reduction.
- Do not silently promote conclusions into SASE memory; memory changes require their
  normal authorization path.

### Stop rule

Stop when the next candidate failure is rare, lacks a stable oracle, or the confidence
interval is too broad to distinguish the proposed change within the remaining window.
Do not spend the last hours tuning prompts to noise.

## Recommendation 3: a proof-carrying ready-backlog train

The current queue already contains many high-value, well-evidenced tasks. A serial loop
can select the highest-impact safe task, reproduce it, add a failing test, implement the
smallest fix, run focused and full checks, close it through the normal bead workflow,
and hand off the next task.

Good autonomous candidates are deterministic code defects such as timezone selection,
Task Link duplication, stale `entry_line`, environment-variable test races, broken-pipe
handling, clippy cleanup, and inode-reuse assumptions. Poor autonomous candidates are
live-vault durability policy, Mac Terminal steps, broad PDF policy, memory changes, or
anything requiring Bryan's preference or a destructive migration.

This is lower in the ranking because it does not uniquely exploit a huge token budget;
normal agent capacity can already do it. It is nevertheless the best fallback when a
testing harness bootstrap stalls, because every completion has an existing definition
of value and evidence.

## Recommendation 4: a cross-repository contract ratchet

Bob Mac Capture is intentionally a thin client of `bob`, while plugins reproduce some
editing semantics. This makes interface drift both costly and mechanically testable.
Run one iteration per externally consumed contract:

- inventory one JSON response or preview schema and every consumer;
- capture a canonical fixture plus an explicit compatibility policy;
- generate adversarial optional/missing/unknown-field cases;
- verify old clients tolerate additive changes and new clients decode old fixtures;
- add CI that exercises the producer against the consumer fixture;
- update both repositories in one bounded, reviewed unit when necessary.

Start with high-churn capture parse/preview/close structures, especially Work Log
details, Pomodoro blocks, completion spans, and task-link candidates. The oracle is
strong—schema decode plus golden presentation—and each contract is independently
handoffable. The cost is cross-repo coordination and slower CI, so serial work is safer
than several concurrent editors.

## Recommendation 5: destructive-workflow fault injection

This is a specialized reliability loop for `vault-sync`, `move-done-tasks`, project
sync, Highlights, GKeep, nightly maintenance, plugin deployment, and any multi-file
capture. Each iteration chooses one interruption point (lock contention, stale mtime,
rename failure, malformed Git state, broken pipe, process kill, duplicate ID), injects
it in a disposable clone or temporary vault, and verifies:

- no content loss;
- no half-applied transaction;
- actionable diagnostics;
- safe retry or idempotent recovery;
- preservation of unrelated bytes and authored structure.

This may find fewer bugs than grammar fuzzing but the impact per bug is higher. It must
never run against the live vault or real remotes. Treat fault injection as an extension
after a reusable temporary-vault harness exists, not as an improvised shell chaos loop.

## Recommendation 6: incremental mutation-guided test hardening

Run mutation testing one changed or high-risk module at a time. Give the agent a small
set of surviving mutants and require it to classify each as equivalent, irrelevant, or
evidence of a missing behavioral test. Land only tests that express a contract a human
would care about.

This is highly measurable and useful for judging tests produced by Recommendations 1,
3, and 5. It ranks below them as a standalone activity because mutation score can become
a game, full-repository mutation is wall-clock expensive, and equivalent mutants waste
attention. Google's evidence specifically favors incremental filtering over brute-force
whole-codebase mutation.

## Recommendation 7: decision-targeted research packets

If coding becomes blocked, use the remaining breadth on specific decisions rather than
generic “research the project” prompts. One loop iteration should take one real pending
decision—backup/PDF policy, task ergonomics, agent eval design, sync architecture—and
produce:

- primary-source evidence;
- current local constraints;
- mutually exclusive options;
- a falsifiable recommendation;
- unresolved questions requiring Bryan;
- an explicit expiration date for time-sensitive claims.

Research is very token-elastic and parallelizable, but its verifier is weaker and Bryan
becomes the decision bottleneck. Reports without an owner or imminent decision tend to
become a document graveyard. This should therefore be a reserve loop, not the main 48
hours.

## A reusable handoff contract

The following skeleton fits the first six recommendations:

```text
You are the next iteration of <named loop>. Read the repository instructions and the
tracked LOOP_STATE/frontier file. Work on exactly one highest-value unclaimed item that
can be completed and verified in this turn.

Before changing anything, state the independent oracle and the stop condition. Do not
touch live user data or external systems. Do not duplicate active work. If the oracle
depends only on the implementation under test, reject the item and choose another.

A successful iteration must leave one of: (a) a minimized failing case plus regression
test and bounded fix, (b) a property/fixture/eval that catches a seeded fault or relevant
mutant, or (c) evidence that closes and removes a false lead. Run focused verification
and the proportionate repository checks.

Update the durable frontier with the hypothesis, evidence, commands, deterministic
seed, result, artifact/commit/bead reference, remaining risks, and at most three next
items. If no meaningful progress is possible, record why and switch once; do not pad the
turn with prose. Hand off to a fresh successor unless the loop stop rule has fired.
```

For `/sase_handoff`, the successor prompt should point to durable state rather than
retelling the work. Fresh context is a feature: it limits anchoring and forces the
result to be reproducible from repository evidence.

## Suggested 48-hour allocation

- **Hours 0–3:** establish the primary loop's frontier, metrics, safety boundary, and
  first tiny vertical slice. If this infrastructure is not usable by hour three, switch
  to the ready-backlog train rather than polishing it indefinitely.
- **Hours 3–30:** run bounded iterations. Prefer serial handoffs within one code surface;
  use parallel agents only for independent oracle design, source research, or blind
  critique—not overlapping edits.
- **Hours 30–40:** exploit the strongest harness on higher-impact cases, or switch to the
  reserve loop if marginal yield has fallen.
- **Hours 40–46:** consolidate: minimize corpora, eliminate flaky seeds, run full checks,
  classify remaining findings, deduplicate tasks, and make the frontier understandable
  to a normal-budget successor.
- **Hours 46–48:** produce a short human review packet: what changed, bugs prevented,
  measured yield per iteration, risks, and the few decisions that actually need Bryan.
  Start no new broad investigation.

## Work I would avoid during this window

- One agent attempting a vaguely specified two-day refactor.
- Many agents editing the same modules or contracts concurrently.
- Broad code review that can file claims without a failing test or reproduction.
- Mass generation of example tests whose expected values come from the same model that
  wrote the implementation.
- Whole-codebase mutation or fuzzing before a small target proves useful.
- Prose-only documentation sweeps, speculative feature ideation, or memory expansion.
- Live-vault chaos testing, unattended deployment, policy decisions, or external writes.
- Optimizing for tokens consumed, number of reports, test count, or coverage rather than
  faults exposed and durable contracts established.

## Ranked recommendations

1. **Build and run the Bob semantic counterexample factory.** Best combination of a
   strong oracle, unexplored combinatorial state space, safe repeatability, and durable
   value; begin with capture rewrite/parse algebra and planner/apply atomicity.
2. **Build a SASE harness-evaluation flywheel.** Potentially the highest compounding
   payoff, but only after creating reproducible evals and held-out A/B trials; avoid
   anecdotal prompt edits.
3. **Run a proof-carrying ready-backlog train.** Highest-confidence immediate value and
   excellent fallback; select safe deterministic defects and skip policy/live-system
   tasks.
4. **Ratchet cross-repository Bob contracts.** Add producer/consumer fixtures and
   compatibility tests around the CLI, Mac client, and plugins, one schema at a time.
5. **Fault-inject destructive workflows in disposable vaults.** Lower discovery volume
   but very high consequence; pursue after the reusable sandbox harness exists.
6. **Use incremental mutation testing to harden important tests.** A strong secondary
   evaluator and saturation detector, not a whole-codebase score chase.
7. **Produce decision-targeted research packets.** Valuable reserve work when code is
   blocked, provided every packet answers a live decision and has a human owner.
