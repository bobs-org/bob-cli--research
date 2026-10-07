# 48-hour task-bead impact audit (bob-cli)

Researcher: `grk` (independent swarm member).
Project: `bob-cli` (`gh_bobs-org__bob-cli`).
Query time: 2026-10-07 16:25:58 UTC.
Window: 2026-10-05 16:25:58 UTC through 2026-10-07 16:25:58 UTC (48 hours).

## Question

Which bob-cli **task beads** created in the last 48 hours, or independently corroborated (`sase bead +1`) in that window, are associated with the most impactful work?

## Method

1. Listed every task bead with `sase bead list --type task --status all --format json -n 0` (109 beads).
2. Took the union of:
   - beads with `created_at >=` window start (equivalent to `--since 48h`; 25 beads), and
   - beads whose `plus_one_evidence[].timestamp` falls inside the window (9 beads, of which 6 were created earlier).
3. Read full JSON fields (title, size, task type, description, creation reason, notes, +1 evidence, close resolution) for the 31-bead union.
4. Audited compact reads of the ten ranked beads with `sase bead read`.
5. Used recent epic titles (`sase bead list --type plan --tier epic`) only as context for which product surfaces a task belongs to. Plan and phase beads are out of scope.

Impact is the leverage of the **work the bead describes** (or already shipped, if closed): daily GTD/capture/review/reading correctness, vault-wide data integrity, and the agent/CI throughput that currently lands almost all bob-cli work. Corroboration count is a recurrence and landing-tax signal, not a vote.

## Corpus

| Slice | Count |
|---|---|
| Task beads created in-window | 25 |
| Task beads +1ed in-window | 9 |
| Union (this audit) | **31** |
| Created earlier, +1ed in-window | 6 |
| Created in-window with a new +1 | 3 |
| Created in-window, no +1 | 22 |

Status: 28 ready, 3 closed (`done`). None in progress, snoozed, or claimed.

Types: 9 bug, 8 memory, 7 feature, 4 flake, 3 ci.

Sizes: 1 xlarge, 9 large, 3 medium, 18 small.

Closed in-window: `bob-cli-4m`, `bob-cli-4r`, `bob-cli-4v`. Closed work stays in the ranking when the shipped fix was high-leverage.

## Clusters

The 31 beads collapse into seven product clusters. Ranking inside a cluster is easier than ranking 31 isolates; the top ten below pick the highest-leverage bead from the clusters that matter.

### 1. Reference library (`bob-cli-4w` follow-ups)

Epic `bob-cli-4w` (`bob ref: a reference library for agents and Bryan`) closed ~16 hours before this audit. Its landing and verify phases produced the largest single cluster:

| ID | Type | Size | Status | Why it is in the cluster |
|---|---|---|---|---|
| `bob-cli-4x` | feature | xlarge | ready | Migrate ~424 zorg-era `status::` records still outside `ref/` |
| `bob-cli-4y` | feature | large | ready | Library-wide annotation search |
| `bob-cli-50` | feature | large | ready | Durable "ever finished" reading history |
| `bob-cli-4z` | feature | small | ready | Bare `bob ref` prints the queue |
| `bob-cli-51` | memory | small | ready | Record "reading state is derived; library verbs are read-only" |
| `bob-cli-4r` | bug | large | **closed** | 113/115 annotated notes leaked the page-1 Highlights marker as a fake annotation |
| `bob-cli-58` | bug | medium | ready | `bob ref create` Markdown PDFs repeat the H1 and double-number headings |

This is the highest-leverage product theme in the window: agents and Bryan now have a read surface for the library, and these beads decide whether that surface covers historical reading, search, honest "already read" state, and readable PDFs.

### 2. Capture URL routing (`bob-cli-52`, in progress)

Epic `bob-cli-52` (`Links go to the reading queue`) is still in progress. Its land/verify phases filed:

| ID | Type | Size | Status | Why it is in the cluster |
|---|---|---|---|---|
| `bob-cli-5d` | memory | small | ready | Decision: a bare public link is reading intent via ref jobs |
| `bob-cli-5e` | memory | small | ready | Glossary term **Ref Job** |
| `bob-cli-5f` | feature | large | ready | Retry retryable clips with backoff before inbox fallback |
| `bob-cli-5g` | feature | small | ready | Drain `bob ref jobs run -q` from the Mac 15-minute crontab |
| `bob-cli-5h` | feature | large | ready | JSON output for `bob ref create` (blocked on `bob-cli-4a` flag spelling) |
| `bob-cli-5b` | ci | small | ready | Web-clip self-test aborts Chrome under SASE's long `$TMPDIR` |
| `bob-cli-4v` | bug | small | **closed** | IPv4-mapped IPv6 literals bypassed the private-host gate (fixed in `bob-cli-52.2`) |

v1 already ships one-shot jobs. The remaining work that decides whether the pipeline survives real networks is retries (`5f`) plus a scheduled drain (`5g`).

### 3. Deterministic red lib tests

| ID | +1 in 48h / total | Failure |
|---|---|---|
| `bob-cli-4j` | 6 / 6 | `every_value_arg_has_a_decision` — `ref create:audio` has no completion-kinds entry |
| `bob-cli-4u` | 3 / 3 | Listen-card Pandoc test pins incidental `\&` escaping in an href URI |

Both fail serially on current master. Every landing since 2026-10-05 has independently reproduced `4j`; `4u` joined on 2026-10-06. Small code changes, large landing tax.

### 4. Parallel-test isolation (same failure class)

| ID | Type | Size | +1 in 48h / total | Failure |
|---|---|---|---|---|
| `bob-cli-2e` | bug | small | 1 / **14** | Unlocked `BOB_DAY_FILE` mutation in `capture_pomodoros::tests::with_env` |
| `bob-cli-40` | flake | large | **5** / 8 | Same test (`missing_note_and_missing_section_are_warning_successes`) flakes under parallel `cargo test` |
| `bob-cli-5c` | flake | large | 0 / 0 | `note_ready::scan_excludes_r3_and_r7_paths` flakes under parallel load; notes name `2e`/`40` as the same class |

`2e` is the causal write (share a process-wide lock, or stop mutating the environment). `40` is the flake tracker for the same assertion. Ranking both would double-count one fix.

### 5. Daily GTD walk and lane UI

| ID | Status | Work |
|---|---|---|
| `bob-cli-4m` | **closed** | `reviewAnsweredKeys` `path:line` keys silently skipped due rows after line-shifting edits; fixed as review-walk text identity |
| `bob-cli-4t` | ready | Record the inbox answer-routing contract (`Ctrl+Shift+P` / `Ctrl+Shift+Enter` route-then-move) |
| `bob-cli-5a` | ready | Record rendered In Progress marks and the Alt+[ / Alt+] Work Log trigger |

`4m` is the user-visible correctness bug. `4t` and `5a` freeze just-landed gesture contracts into decisions memory so later agents stop reinventing them.

### 6. SASE / harness friction

| ID | Size | +1 in 48h / total | Work |
|---|---|---|---|
| `bob-cli-21` | large | 2 / 5 | Artifact-link event store rejects every new link (`operation_id` reused). Also crashes `sase plan propose` when a plan has a `links:` inlet |
| `bob-cli-3c` | small | 3 / 8 | `just check` does not exist; every landing is told to run it and exits 1 immediately |
| `bob-cli-59` | small | 0 / 0 | Bare `bob plugins sync` from a SASE worktree deploys the canonical checkout and can roll a sibling plugin backward in the vault |

`21` bricks a whole SASE subsystem for this project. `3c` and `59` are small, high-frequency taxes on the same agent swarm.

### 7. Memory hygiene and narrower flakes

Mac-pom glossary drift (`bob-cli-4o` +1ed by a human, `bob-cli-57`), Reference Note containment wording (`bob-cli-4n`), Mac StartPending CI flake (`bob-cli-4k`, large, one fail/pass pair, no +1), and bob-plugins stage-ranker 16 ms flake (`bob-cli-3w`, +1=5 total, 1 in-window). Real, lower leverage than the clusters above.

## Ranking framework

A bead ranks high when several of these hold:

1. **Daily path.** Capture, review walk, freshness/plan, or the reading queue.
2. **Vault-wide integrity.** Agents or Bryan would misread notes, skip due rows, or lose reading history.
3. **Unblocks a just-landed product.** `bob ref` and URL-routing jobs only pay off if search, coverage, retries, and honest PDFs exist.
4. **Agent/CI throughput.** Deterministic red tests and a bricked artifact-link store tax every subsequent epic.
5. **Scope.** Size `xlarge`/`large` plus a counted blast radius (424 records, 113 notes, 239/291 PDFs, every `sase artifact link add`).
6. **Recurrence.** Independent +1s inside the window, especially from land agents on unchanged trees.

Memory beads that only restate a shipped epic rank below the feature/bug that the epic still needs. Closed beads rank when the shipped fix was itself high-leverage.

## Ranked 10

### 1. `bob-cli-4x` — Migrate zorg-era reading records into the reference library

- **Type / size / status:** feature / xlarge / ready
- **Created:** 2026-10-07 by `bob-cli-4w.land`
- **+1 (48h / all):** 0 / 0

`bob ref doctor` currently counts about **424 unindexed `status::` records** outside `ref/` (athena, ~2026-10-06), led by `work_ref.md` (75) and `nvim_ref.md` (69). Until those move, `bob ref find` / `list` cannot see that history, and every JSON envelope has to advertise the coverage hole. Epic `bob-cli-4w` shipped a read-only library on purpose and listed this migration as a separate Bryan-reviewed epic (bulk vault writes, legacy_status mapping, dedupe against the 282 records already in `ref/ai/`). This is the only xlarge in the set, and it is the coverage gap that decides whether `bob ref` is the library or a slice of it.

### 2. `bob-cli-21` — Artifact-link event store rejects every new link

- **Type / size / status:** bug / large / ready
- **Created:** 2026-09-10 (older; **+1ed twice in-window**)
- **+1 (48h / all):** 2 / 5

Every `sase artifact link add` in bob-cli fails with a reused `operation_id` (`de29d2e25c1cfb4381f223c44d576f8c`). Land agents in this window (`research.3s.cld`, `bob-cli-4q.land`) hit it while linking follow-ups; several new beads in the corpus literally record "typed artifact links were rejected" in notes. A 2026-10-04 +1 already showed `sase plan propose` crashing in `publish_plan_artifact_link_inlet` on the same store. Related-link flows in `/sase_new_task`, plan inlets, and bead-to-evidence graphs are all blocked until the store is repaired or the validator tolerates the historical duplicate. This is a project-wide SASE workflow outage, open for 26 days.

### 3. `bob-cli-4r` — Fake Highlights marker rendered as an annotation (shipped)

- **Type / size / status:** bug / large / **closed done** (2026-10-07, phase `bob-cli-4w.8`)
- **Created:** 2026-10-06 while researching a `bob ref` annotation-read surface
- **+1 (48h / all):** 0 / 0

**113 of 115** annotated reference notes rendered the page-1 sidecar marker (`status` / `parent` / `url`) as a `> [!note]` annotation with a `^h-…` block id. `highlights_count` was inflated by one on each, and any agent using `bob ref show -c` (or a future export) would treat Highlights metadata as Bryan's own note, often stale (`status: wip` on notes that are `read`). Root cause: a one-shot marker skip consumed by the setext title preamble. The fix is content-based mirror detection, silent drop without tombstones, and close-date stamping. Highest-leverage **completed** data-integrity work in the window, and it is what makes the new library safe to read.

### 4. `bob-cli-33` — Tasks JS sandbox 2s deadline fails freshness and plan

- **Type / size / status:** bug / medium / ready
- **Created:** 2026-10-01; **+1ed 2026-10-07** by `bob-cli-55.land`
- **+1 (48h / all):** 1 / 1

Every native Tasks query (`bob freshness list`, `bob plan` lanes/budgets, `bob query`) eagerly builds a `JsSandbox` that JSON-parses and hydrates the whole vault through Moment inside `EXPRESSION_TIMEOUT = 2s`. Queries with no `by function` still pay that bill. On 2026-10-07, `bob freshness list -f json` on master `092e098` exited 1 with `JavaScript error while initializing the Tasks JavaScript sandbox: Error: interrupted`. Fixture tests stay green; the real vault under load does not. This is the read path for Ready/NEW/ROTTEN and for today's plan, so a busy host makes the daily GTD CLI lie.

### 5. `bob-cli-4m` — Review walk skipped due rows after line-shifting edits (shipped)

- **Type / size / status:** bug / medium / **closed done** (2026-10-06, agent `0x9.f0`)
- **Created:** 2026-10-06 during `ctrl_shift_m_never_advances_walk` work
- **+1 (48h / all):** 0 / 0

`reviewAnsweredKeys` stored day-long `path:line` keys. After a land-and-answer, inserting a due line (hand edit, or a recurring task writing the next occurrence) made a later due row inherit a handled key, and later advances treated that row as already reviewed for the rest of the day. Recovery existed (`[s`, `<C-o>`) and was silent. The walk is Bryan's daily GTD loop; a silent skip is worse than a loud failure. Fixed as review-walk **text identity**: position from this gesture's rows, handled keys verified by note+text, neighbours by text refs, with dedicated walk-identity tests. Highest-leverage **completed** daily-path fix in the window.

### 6. `bob-cli-5f` — Retry retryable ref-job clips before falling back

- **Type / size / status:** feature / large / ready
- **Created:** 2026-10-07 by `bob-cli-52.land` (verify follow-up)
- **+1 (48h / all):** 0 / 0

`bob-cli-52` routes a bare public URL through a durable ref job so capture stays off the network. v1 makes **one** attempt; any `IngestError` (timeout, 429, 5xx, browser, dependency) immediately writes the inbox-task fallback plus a warning. That is the design that will decide whether "links go to the reading queue" holds on a flaky hotel network or a briefly down clip adapter. v2 needs additive job-schema fields (`attempts`, `next_attempt_at`), doctor/UI for waiting retries, and a later kick (capture, Mac cron, or both). Pair with `bob-cli-5g` (scheduled `bob ref jobs run -q`) for drain-after-reboot; `5f` is the larger reliability design.

### 7. `bob-cli-4y` — Library-wide annotation search

- **Type / size / status:** feature / large / ready
- **Created:** 2026-10-07 by `bob-cli-4w.land`
- **+1 (48h / all):** 0 / 0

`bob ref show <REF> -c` already returns one note's highlights/comments. There is still no "where did I comment on X?" across the library. The parsers exist (`region.rs` quote/comment split, leaked-mirror exclusion) and a full vault scan is already ~35 ms for 594 notes. This is the agent-facing query that turns `bob ref` from a per-note lookup into a research tool, and it is the natural companion to `4x` (search is only as good as coverage). Explicitly out of scope for `4w` because matching, ranking, and output size need their own design.

### 8. `bob-cli-4j` — Missing `--audio` completion-kinds decision (lib tests red)

- **Type / size / status:** ci / small / ready
- **Created:** 2026-10-05
- **+1 (48h / all):** **6 / 6** (every independent landing in the window)

`cargo test --lib` fails **deterministically** on `native::completion::kinds::tests::every_value_arg_has_a_decision` because `ref create --audio` (formerly `highlights create --audio`) has no kinds-table entry or `ValueHint::FilePath`. Six land agents reproduced it on six SHAs (`fbc4f43` through `2d568fa`). Isolated `--exact` reruns fail the same way. The product fix is one completion decision; the operational impact is that every landing's full lib suite is red until it lands, which is why it outranks the larger-but-intermittent `capture_pomodoros` flake cluster.

### 9. `bob-cli-2e` — Serialize the `capture_pomodoros` `BOB_DAY_FILE` test mutation

- **Type / size / status:** bug / small / ready
- **Created:** 2026-09-28; **+1ed 2026-10-07** by `bob-cli-4w.land`
- **+1 (48h / all):** 1 / **14**

`capture_pomodoros::tests::with_env` sets process-global `BOB_DAY_FILE` with no lock, while `capture_complete` tests hold a **module-private** `DAY_FILE_LOCK`. Parallel `cargo test --lib` therefore points the missing-note assertion at another test's day file. This is the most-corroborated open task in the project (14 independent reports). In-window, `bob-cli-40` added five more observations of the **same test** failing under `just all` and passing isolated. Treat `40` (and likely `5c`) as the same isolation class; fixing `2e` with a process-wide lock is the work. Impact is landing reliability across nearly every epic since late September.

### 10. `bob-cli-58` — Markdown PDFs repeat the H1 and double-number headings

- **Type / size / status:** bug / medium / ready
- **Created:** 2026-10-07 during PDF-backlinks research
- **+1 (48h / all):** 0 / 0

`bob ref create` runs pandoc with `--toc --number-sections` and also passes the first H1 as `--metadata title=`. Measured on 2026-10-07 over **291** PDFs in `~/bob/lib/chat`: **239/291** have `1.x` section numbers (title remains a level-1 section), and **147/291** double-number agent headings (`## 1. Evidence` becomes TOC `1.2 1. Evidence`). That is the default readability of almost every research/chat PDF Bryan and agents open from the library. The fix is small (shift heading level when the only H1 is the title; skip `--number-sections` when headings are already numbered) and coordinates with heading-id / backlink work. Vault-wide user-visible quality, sitting on the same `create.rs` pandoc path as `bob-cli-4u`.

## Honorable mentions (next 8)

These missed the cut because they duplicate a ranked bead, freeze already-shipped policy, or tax agents without touching Bryan's daily path as hard.

| Rank | ID | Why it is close |
|---|---|---|
| 11 | `bob-cli-3c` | Missing `just check`; 3 in-window +1s, 8 total. Every landing hits it. Small recipe, high swarm tax. |
| 12 | `bob-cli-40` | Same `capture_pomodoros` test as `2e`, 5 in-window +1s. Do this as part of `2e`. |
| 13 | `bob-cli-5d` | Decision record for bare-link → ref-job routing. Needed so later agents keep the contract; the runtime work is `5f`/`5g`. |
| 14 | `bob-cli-5g` | Mac 15-minute `bob ref jobs run -q`. Completes `5f` operationally (reboot / failed kick). Small, chezmoi crontab, related to `bob-cli-30`. |
| 15 | `bob-cli-50` | Durable ever-finished history. Product-complete `bob ref`, blocked on a stored-field vs derived-state decision (`51`). |
| 16 | `bob-cli-4t` | Inbox answer-routing decision. Documents `bob-cli-4q` so gesture semantics stay sticky. |
| 17 | `bob-cli-59` | Bare `bob plugins sync` clobbers a worktree deploy (ledger-tools 1.34.0 → 1.33.0 observed). Dangerous under concurrent epics. |
| 18 | `bob-cli-4u` | Second deterministic red lib test (Pandoc `\&`). Smaller blast radius than `4j`; same `create.rs` as `58`. |

Also in the union, lower leverage: `bob-cli-5a` (In Progress marks decision), `bob-cli-51` / `5e` (library/ref-job memory), `bob-cli-5h` (JSON create, waiting on `bob-cli-4a`), `bob-cli-4z` (bare `bob ref` default), `bob-cli-4v` (private-host IPv6, already closed), `bob-cli-5b` (clip self-test TMPDIR), `bob-cli-5c` (note_ready parallel flake), `bob-cli-4k` (Mac StartPending timeout, one CI pair), `bob-cli-3w` (16 ms ranker flake), `bob-cli-4n` / `4o` / `57` (glossary drift).

## Full inventory (31)

| ID | Status | Type | Size | +1 48h/all | In set as | Title |
|---|---|---|---|---|---|---|
| bob-cli-21 | ready | bug | large | 2/5 | +1-only | artifact-link event store rejects every new link |
| bob-cli-2e | ready | bug | small | 1/14 | +1-only | Serialize the capture_pomodoros BOB_DAY_FILE test mutation |
| bob-cli-33 | ready | bug | medium | 1/1 | +1-only | Tasks JS sandbox init hits the 2s expression deadline |
| bob-cli-3c | ready | bug | small | 3/8 | +1-only | Add the canonical just check entry point |
| bob-cli-3w | ready | flake | small | 1/5 | +1-only | Stage ranker 16 ms perf assertion flakes |
| bob-cli-40 | ready | flake | large | 5/8 | +1-only | capture_pomodoros warning test flakes under parallel cargo test |
| bob-cli-4j | ready | ci | small | 6/6 | created+1 | highlights/ref create --audio missing completion kinds |
| bob-cli-4k | ready | flake | large | 0/0 | created | Mac StartPending preview test times out then passes |
| bob-cli-4m | closed | bug | medium | 0/0 | created | reviewAnsweredKeys path:line keys skip shifted due rows |
| bob-cli-4n | ready | memory | small | 0/0 | created | Reword Reference Note follow-up-work phrase |
| bob-cli-4o | ready | memory | small | 1/1 | created+1 | Mac pom glossary stale NO POMODORO flash schedule |
| bob-cli-4r | closed | bug | large | 0/0 | created | Highlights sync renders page-1 marker as an annotation |
| bob-cli-4t | ready | memory | small | 0/0 | created | Record the accepted inbox answer-routing contract |
| bob-cli-4u | ready | ci | small | 3/3 | created+1 | Listen-card Pandoc test pins ampersand escaping |
| bob-cli-4v | closed | bug | small | 0/0 | created | URL validation accepts IPv4-mapped IPv6 private hosts |
| bob-cli-4x | ready | feature | xlarge | 0/0 | created | Migrate zorg-era reading records into the library |
| bob-cli-4y | ready | feature | large | 0/0 | created | bob ref search across ref notes |
| bob-cli-4z | ready | feature | small | 0/0 | created | Bare bob ref shows the reading queue |
| bob-cli-50 | ready | feature | large | 0/0 | created | Durable ever-finished reading history |
| bob-cli-51 | ready | memory | small | 0/0 | created | Record derived reading state / read-only verbs |
| bob-cli-57 | ready | memory | small | 0/0 | created | Mac pom glossary still says polls every 15 seconds |
| bob-cli-58 | ready | bug | medium | 0/0 | created | Markdown PDFs repeat H1 and double-number headings |
| bob-cli-59 | ready | bug | small | 0/0 | created | Bare plugins sync from a worktree deploys canonical checkout |
| bob-cli-5a | ready | memory | small | 0/0 | created | Record rendered In Progress marks and Work Log trigger |
| bob-cli-5b | ready | ci | small | 0/0 | created | check-web-clip-adapter aborts Chrome under long TMPDIR |
| bob-cli-5c | ready | flake | large | 0/0 | created | note_ready r3/r7 scan flakes under parallel cargo test |
| bob-cli-5d | ready | memory | small | 0/0 | created | Record bare public link as reading intent via ref jobs |
| bob-cli-5e | ready | memory | small | 0/0 | created | Add a Ref Job glossary term |
| bob-cli-5f | ready | feature | large | 0/0 | created | Retry retryable ref-job clips with backoff |
| bob-cli-5g | ready | feature | small | 0/0 | created | Run bob ref jobs run -q from the Mac 15-minute schedule |
| bob-cli-5h | ready | feature | large | 0/0 | created | JSON output for bob ref create |

## Recommendation

If the lead is synthesizing a "what to do next" list from this swarm, the productive cut is:

1. **Unblock the swarm (hours):** `bob-cli-4j` then `bob-cli-4u` (make `cargo test --lib` green), `bob-cli-2e` (and close `40`/`5c` as the same isolation class), `bob-cli-3c` (`just check`), `bob-cli-21` (artifact-link store — large, but every subsequent landing keeps paying for it).
2. **Finish the library (the product bet of this week):** `bob-cli-4x` (coverage), `bob-cli-4y` (search), `bob-cli-58` (readable PDFs), `bob-cli-50`/`51` (honest finished-state).
3. **Make URL routing survive reality:** `bob-cli-5f` + `bob-cli-5g`, then freeze the contract with `bob-cli-5d`/`5e`.
4. **Leave memory-only restatements** (`4n`, `4o`, `57`, and most of `4t`/`5a`/`51`) until the feature/bug they document is already in Bryan's hands.

Shipped in this window and already high-impact: `bob-cli-4r` (library safe to read) and `bob-cli-4m` (review walk no longer silently skips due rows).

## Evidence commands

```bash
sase bead list --type task --since 48h --status all --format json -n 0
sase bead list --type task --status all --format json -n 0   # then filter plus_one_evidence timestamps
sase bead read bob-cli-4x bob-cli-21 bob-cli-4r bob-cli-33 bob-cli-4m \
  bob-cli-5f bob-cli-4y bob-cli-2e bob-cli-4j bob-cli-58 \
  --format compact -r "Need compact status of the ten highest-impact candidates before ranking"
```

No peer swarm reports were opened. Prior research filenames in `202610/` that belong to other topics were left unread.
