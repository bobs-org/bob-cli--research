# Audit of Recent Task Beads: 48-Hour Impact Analysis

**Author:** Researcher gem (`research.0e.gem`)  
**Date:** 2026-10-07  
**Audit Window:** 2026-10-05T16:24:34Z to 2026-10-07T16:24:34Z (48 hours)  
**Target Repository:** `bob-cli` (including linked `bob-plugins`, `bob-mac-capture`, and SASE infrastructure)

---

## 1. Executive Summary & Scope

This research report provides a comprehensive, independent audit of all task beads within the project that were either **created** in the past 48 hours or received one or more **+1 corroborations** in the past 48 hours. The goal of this audit is to identify, categorize, and rank the most impactful work across the project.

Within the 48-hour observation window (anchored at `2026-10-07T16:24:34Z`):
- **Total task beads audited:** **31 unique beads**
- **Newly created task beads:** **25 beads**
- **Task beads receiving +1 corroborations:** **9 beads**
- **Overlap (created and +1ed in window):** **3 beads** (`bob-cli-4j`, `bob-cli-4o`, `bob-cli-4u`)
- **Status distribution:** 28 `ready` (awaiting triage/work), 3 `closed` (resolved during recent epic phases)

The audited beads span five distinct operational domains:
1. **Platform & Vault Data Safety:** Protection of live user vault state and SASE platform metadata.
2. **Core User Value & Feature Roadmaps:** Reference library scale, reading record migrations, and search.
3. **Runtime Bugs & Functional CLI Deficiencies:** Crashes, timeouts, and malformed outputs affecting daily use.
4. **Swarm Velocity & CI / Build Infrastructure:** Deterministic test failures, concurrency races, and broken build entry points stalling autonomous agent landings.
5. **Durable Memory & Policy Governance:** Synchronization of accepted decisions and glossary strands.

---

## 2. Methodology & Impact Evaluation Criteria

Data was audited directly from the authoritative bead store (`sase/repos/beads/events/streams/*.jsonl` and `issues.jsonl`), cross-referenced with recent epic landing logs (`bob-cli-4w.land`, `bob-cli-52.land`, `bob-cli-56.land`, `bob-cli-4q.land`, `bob-cli-4s.land`, `bob-cli-55.land`).

Impact is evaluated along four objective dimensions:
- **Blast Radius & Data Integrity:** Does the defect cause data loss, silent regression, or corruption of user notes, vault configurations, or durable audit trails?
- **Agent Swarm Velocity & Land Friction:** Does the issue deterministically break CI or landing gates, forcing multiple concurrent autonomous agents to stall, rerun suites, or formulate manual bypasses?
- **User Knowledge Base Scale & Longevity:** Does the work govern large quantities of user data (e.g., hundreds of historical reading records) or fundamental retrieval workflows?
- **Root Cause Leverage:** Does resolving the bead eliminate recurring cascades of secondary defects and flaky test reports across the codebase?

---

## 3. Comprehensive Inventory of the 31 Audited Task Beads

The following table itemizes all 31 task beads meeting the 48-hour criteria, sorted by bead ID:

| Bead ID | Title | Type | Size | Status | Created | 48h +1s | Total +1s | Category |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `bob-cli-21` | artifact-link event store rejects every new link: operation_id reused | bug | L | ready | 2026-09-10 | 2 | 5 | Platform / SASE Infra |
| `bob-cli-2e` | Serialize the capture_pomodoros BOB_DAY_FILE test mutation | bug | S | ready | 2026-09-28 | 1 | 14 | CI / Concurrency Race |
| `bob-cli-33` | Tasks JS sandbox init hits the 2s expression deadline on busy hosts | bug | M | ready | 2026-10-01 | 1 | 1 | CLI / Functional Bug |
| `bob-cli-3c` | Add the canonical just check file-change verification entry point | bug | S | ready | 2026-10-01 | 3 | 8 | Build / Agent Workflow |
| `bob-cli-3w` | Stage ranker 16 ms perf assertion flakes under parallel npm test load | flake | S | ready | 2026-10-03 | 1 | 5 | Plugins / Test Flake |
| `bob-cli-40` | capture_pomodoros warning test flakes under parallel cargo test | flake | L | ready | 2026-10-03 | 5 | 11 | CI / Test Flake |
| `bob-cli-4j` | highlights create --audio lacks completion kinds decision | ci | S | ready | 2026-10-05 | 6 | 6 | CI / Deterministic Failure |
| `bob-cli-4k` | Mac StartPending preview test times out, then passes on unchanged CI | flake | L | ready | 2026-10-05 | 0 | 0 | Mac Capture / UI Flake |
| `bob-cli-4m` | Day-long reviewAnsweredKeys path:line keys can name a different row | bug | M | closed | 2026-10-06 | 0 | 0 | Navigation / Review Walk |
| `bob-cli-4n` | Reword Reference Note follow-up-work phrase for area containment | memory | S | ready | 2026-10-06 | 0 | 0 | Memory / Glossary |
| `bob-cli-4o` | Mac pom glossary strand describes a stale NO POMODORO flash schedule | memory | S | ready | 2026-10-06 | 1 | 1 | Memory / Glossary |
| `bob-cli-4r` | Highlights sync renders page-1 marker mirror as annotation | bug | L | closed | 2026-10-06 | 0 | 0 | Vault / Data Hygiene |
| `bob-cli-4t` | Record the accepted inbox answer-routing contract | memory | S | ready | 2026-10-06 | 0 | 0 | Memory / Decisions |
| `bob-cli-4u` | Listen-card Pandoc test pins ampersand escaping in href URI | ci | S | ready | 2026-10-06 | 3 | 3 | CI / Deterministic Failure |
| `bob-cli-4v` | Highlights URL validation accepts IPv4-mapped IPv6 literals | bug | S | closed | 2026-10-06 | 0 | 0 | Security / URL Validation |
| `bob-cli-4x` | Migrate zorg-era reading records outside ref/ into reference library | feature | XL | ready | 2026-10-07 | 0 | 0 | User Data / Migration |
| `bob-cli-4y` | bob ref search: library-wide annotation search across ref notes | feature | L | ready | 2026-10-07 | 0 | 0 | Feature / Knowledge Search |
| `bob-cli-4z` | Bare bob ref shows the reading queue instead of help | feature | S | ready | 2026-10-07 | 0 | 0 | CLI UX / Ergonomics |
| `bob-cli-50` | Durable ever-finished reading history for reference notes | feature | L | ready | 2026-10-07 | 0 | 0 | Feature / Reading History |
| `bob-cli-51` | Record decision: reference reading state derived, verbs read-only | memory | S | ready | 2026-10-07 | 0 | 0 | Memory / Decisions |
| `bob-cli-57` | Mac pom glossary strand still says polls every 15 seconds | memory | S | ready | 2026-10-07 | 0 | 0 | Memory / Glossary |
| `bob-cli-58` | bob ref create Markdown PDFs repeat H1 and double-number headings | bug | M | ready | 2026-10-07 | 0 | 0 | Document / PDF Render |
| `bob-cli-59` | Bare bob plugins sync from SASE worktree deploys canonical checkout | bug | S | ready | 2026-10-07 | 0 | 0 | Vault Safety / Deployment |
| `bob-cli-5a` | Record rendered In Progress marks and Task Link Work Log trigger | memory | S | ready | 2026-10-07 | 0 | 0 | Memory / Decisions |
| `bob-cli-5b` | check-web-clip-adapter self-test aborts Chrome under long TMPDIR | ci | S | ready | 2026-10-07 | 0 | 0 | CI / Test Isolation |
| `bob-cli-5c` | note_ready scan_excludes_r3_and_r7_paths flakes under parallel test | flake | L | ready | 2026-10-07 | 0 | 0 | CI / Test Flake |
| `bob-cli-5d` | Record decision: bare public link is reading intent routed via jobs | memory | S | ready | 2026-10-07 | 0 | 0 | Memory / Decisions |
| `bob-cli-5e` | Add a Ref Job glossary term | memory | S | ready | 2026-10-07 | 0 | 0 | Memory / Glossary |
| `bob-cli-5f` | Retry retryable ref-job clips with backoff before falling back | feature | L | ready | 2026-10-07 | 0 | 0 | Pipeline / Resilience |
| `bob-cli-5g` | Run bob ref jobs run -q from the Mac 15-minute schedule | feature | S | ready | 2026-10-07 | 0 | 0 | Automation / Background Job |
| `bob-cli-5h` | JSON output for bob ref create reporting typed ingest outcome | feature | L | ready | 2026-10-07 | 0 | 0 | API / Tooling Contract |

---

## 4. Ranked Top 10 Most Impactful Task Beads

Based on the evaluation criteria, here is the ranked analysis of the **10 most impactful task beads** from the audited set:

---

### Rank 1: `bob-cli-59` — Bare bob plugins sync from a SASE worktree deploys the canonical checkout
- **Bead Metadata:** Type: `bug` | Size: `small` | Status: `ready` | Created: 2026-10-07T15:09:51Z by `bob-cli-56.land`
- **Why It Is Ranked #1:**
  This defect presents an active risk of **silent data and software regression in the user’s live Obsidian vault** (`~/bob`). When autonomous agents work on plugin features inside a SASE linked worktree and run `bob plugins sync`, the sync mechanism resolves `BOB_PLUGINS_DIR` to the canonical checkout (`~/projects/github/bobs-org/bob-plugins`) and runs `git pull` there, entirely ignoring the agent's active worktree.
  
  **Concrete Evidence:** During the landing of `bob-cli-56` on 2026-10-07, a bare sync command silently rolled back `ledger-tools` from version `1.34.0` to `1.33.0` inside Bryan's live vault, undoing deployed features. The proposed fix adds an immediate guard: when the invoking directory is inside a `bob-plugins` worktree that differs from the canonical repository, `bob plugins sync` aborts with an explicit error directing the caller to supply `--repo` and `-p`. This is the highest-severity operational hazard in the audit.

---

### Rank 2: `bob-cli-21` — artifact-link event store rejects every new link: operation_id reused for different events
- **Bead Metadata:** Type: `bug` | Size: `large` | Status: `ready` | Created: 2026-09-10T19:54:03Z | 48h Corroborations: **2** (`research.3s.cld`, `bob-cli-4q.land`) | All-time Corroborations: **5**
- **Why It Is Ranked #2:**
  This issue represents a **systemic platform-level failure across the entire SASE agent infrastructure**. The artifact-link event store is corrupted by a duplicated `operation_id` (`de29d2e25c1cfb4381f223c44d576f8c`). Consequently, **every invocation of `sase artifact link add` fails across the entire project**.
  
  **Concrete Evidence:** In the last 48 hours, research agents (`research.3s.cld`) and epic landing agents (`bob-cli-4q.land`, `bob-cli-4w.land`, `bob-cli-52.land`) across multiple separate workspaces have repeatedly noted that they cannot record typed artifact relationships between beads, research reports, and design files. Agents are forced to store fallback relationship text in unstructured bead notes. Restoring the integrity of this store unblocks the formal audit and provenance graph for all agents.

---

### Rank 3: `bob-cli-4x` — Migrate zorg-era reading records outside ref/ into the reference library
- **Bead Metadata:** Type: `feature` | Size: `xlarge` | Status: `ready` | Created: 2026-10-07T04:29:39Z by `bob-cli-4w.land`
- **Why It Is Ranked #3:**
  This bead represents the **largest user-data migration on the active roadmap**. During the verification of the newly shipped `bob ref` reference library (epic `bob-cli-4w`), `bob ref doctor` revealed approximately **424 unindexed legacy reading records** from Bryan’s pre-existing "zorg" era residing outside the managed `ref/` directory.
  
  Completing this XL migration will bring Bryan's entire historical corpus of literature notes, reading progress, and paper highlights into the unified reference library schema, enabling comprehensive library indexing, search, and reading queue integration.

---

### Rank 4: `bob-cli-2e` — Serialize the capture_pomodoros BOB_DAY_FILE test mutation
- **Bead Metadata:** Type: `bug` | Size: `small` | Status: `ready` | Created: 2026-09-28T18:08:13Z | 48h Corroborations: **1** (`bob-cli-4w.land`) | All-time Corroborations: **14**
- **Why It Is Ranked #4:**
  `bob-cli-2e` is the **foundational root-cause fix for the most pervasive test failure in the project history**. Inside `src/native/capture_pomodoros.rs`, `tests::with_env` mutates the process-global environment variable `BOB_DAY_FILE` without synchronization, while unit tests like `missing_note_and_missing_section_are_warning_successes` execute concurrently in Rust’s multithreaded test runner.
  
  This race condition directly causes `bob-cli-40` (which logged 5 failures in the last 48 hours alone). Fixing this race condition with proper mutex locking (analogous to `DAY_FILE_LOCK` in `capture_complete.rs`) stabilizes the core test suite across all agent workspaces.

---

### Rank 5: `bob-cli-4j` — highlights create --audio lacks a shell-completion kinds decision, failing every_value_arg_has_a_decision
- **Bead Metadata:** Type: `ci` | Size: `small` | Status: `ready` | Created: 2026-10-05T22:06:41Z by `bob-cli-4i.land` | 48h Corroborations: **6** (`bob-cli-4i.7.land`, `bob-cli-4q.land`, `bob-cli-4s.land`, `bob-cli-4w.land`, `bob-cli-55.land`, `bob-cli-52.land`) | All-time Corroborations: **6**
- **Why It Is Ranked #5:**
  `bob-cli-4j` has been the **single most frequently hit test failure across the entire project over the last 48 hours**. It is a deterministic failure: `cargo test --lib` exits with code 101 on master because `highlights create --audio` (recently renamed to `ref create:audio`) takes a value argument but lacks an entry in the shell completion kinds decision table (`native::completion::kinds::tests::every_value_arg_has_a_decision`).
  
  Six consecutive landing agents over the past two days have been forced to triage, document, and bypass this deterministic failure. Because it is a small, isolated fix, closing it provides immediate, massive friction relief to every working agent.

---

### Rank 6: `bob-cli-33` — Tasks JS sandbox init hits the 2s expression deadline on busy hosts, failing queries with no by-function
- **Bead Metadata:** Type: `bug` | Size: `medium` | Status: `ready` | Created: 2026-10-01T03:48:26Z | 48h Corroborations: **1** (`bob-cli-55.land`) | All-time Corroborations: **1**
- **Why It Is Ranked #6:**
  This is a **critical CLI availability defect**. In `src/native/dataview/tasks/js.rs`, the JavaScript sandbox initialization is executed eagerly for the entire vault and is bound by a strict 2-second `EXPRESSION_TIMEOUT`.
  
  **Concrete Evidence:** When executing `bob freshness list -f json` on busy hosts or production-scale vaults, the command fails with:
  `JavaScript error while initializing the Tasks JavaScript sandbox: Error: interrupted, including __bobMoment/TasksDate/__bobHydrateTask`.
  Even simple queries that do not require custom JS functions are completely aborted. Deferring sandbox construction until custom functions are evaluated or extending the initialization deadline restores reliable task list generation.

---

### Rank 7: `bob-cli-4u` — Listen-card Pandoc test pins ampersand escaping in href URI
- **Bead Metadata:** Type: `ci` | Size: `small` | Status: `ready` | Created: 2026-10-06T19:54:15Z by `bob-cli-4q.land` | 48h Corroborations: **3** (`bob-cli-4s.land`, `bob-cli-4w.land`, `bob-cli-52.land`) | All-time Corroborations: **3**
- **Why It Is Ranked #7:**
  Alongside `bob-cli-4j`, this is the second **deterministic CI failure currently broken on the master branch**. The unit test `native::highlights_ref::create::tests::listen_filter_renders_card_and_encoded_play_link` asserts that generated LaTeX/pandoc output contains an escaped `\&` in href links. However, Pandoc 3.1.11.1 emits an unescaped bare `&`.
  
  Every full unit test run (`just all` or `cargo test --lib`) on master fails at `src/native/highlights_ref/create.rs:2386`. Correcting the test assertion to accommodate Pandoc's output is essential for returning the master branch to a clean, passing state.

---

### Rank 8: `bob-cli-3c` — Add the canonical just check file-change verification entry point
- **Bead Metadata:** Type: `bug` | Size: `small` | Status: `ready` | Created: 2026-10-01T18:41:02Z | 48h Corroborations: **3** (`bob-cli-4i.7.land`, `bob-cli-4q.land`, `bob-cli-55.land`) | All-time Corroborations: **8**
- **Why It Is Ranked #8:**
  This bead addresses a persistent **workflow disconnect in agent automated verification**. Standard SASE landing prompts instruct agents to run `just check` to verify repository health before landing. However, the root `Justfile` does not contain a `check` recipe (`error: justfile does not contain recipe check`).
  
  Landing agents are repeatedly interrupted by this failure, having to construct bespoke verification command chains (combining `cargo fmt`, `cargo test`, `npm test`) and record boilerplate explanations. Adding the canonical `just check` recipe standardizes and unblocks agent pre-landing verification across the project.

---

### Rank 9: `bob-cli-5f` — Retry retryable ref-job clips with backoff before falling back
- **Bead Metadata:** Type: `feature` | Size: `large` | Status: `ready` | Created: 2026-10-07T16:15:45Z by `bob-cli-52.land`
- **Why It Is Ranked #9:**
  This feature provides **essential resilience to the new background reference capture architecture**. With the landing of `bob-cli-52`, URLs captured in macOS Bob Capture or the CLI are asynchronously ingested as background `ref jobs`.
  
  Currently, any transient HTTP network hiccup or temporary rate limit causes the job to immediately degrade into a fallback error task in `mac_inbox.md`. Implementing an intelligent retry mechanism with exponential backoff prevents transient failures from polluting the user's GTD inbox with false alarms.

---

### Rank 10: `bob-cli-58` — bob ref create Markdown PDFs repeat the H1 as section 1 and double-number manually numbered headings
- **Bead Metadata:** Type: `bug` | Size: `medium` | Status: `ready` | Created: 2026-10-07T15:05:16Z by `research.3x.cld`
- **Why It Is Ranked #10:**
  This defect causes **visible document corruption in generated PDF reference notes**. When Markdown files are converted into archival PDFs via `bob ref create <report>.md -o r.pdf -n`, Pandoc passes the top-level H1 heading both as the document title metadata and as section 1.
  
  Furthermore, documents with pre-numbered headings (standard for research reports and RFCs) suffer from double numbering (e.g., table of contents renders `1.1 1. Summary` and `1.2 2. Details`). Fixing the Pandoc heading level shift and section numbering flags directly restores the visual and archival quality of all generated reference PDFs.

---

## 5. Analysis of Notable Runners-Up & Closed Beads

### 5.1 The Root Cause vs. Symptom Coupling: `bob-cli-2e` and `bob-cli-40`
`bob-cli-40` (*capture_pomodoros warning test flakes under parallel cargo test*) recorded **5 +1 corroborations** in the last 48 hours (and 11 all-time). While superficially looking like one of the most critical beads by raw event count, it is the symptom manifestation of `bob-cli-2e`. Multiple landing notes confirm that `bob-cli-40` is directly triggered by the unlocked `BOB_DAY_FILE` mutation in `bob-cli-2e`. Prioritizing `bob-cli-2e` (Rank 4) directly resolves `bob-cli-40`.

### 5.2 High-Value Downstream Feature Expansions
Several beads created by `bob-cli-4w.land` and `bob-cli-52.land` represent substantial product capabilities that narrowly missed the top 10 due to the urgent necessity of fixing active regressions and CI blockers:
- **`bob-cli-4y` (bob ref search):** Full-text annotation search across reference notes. A major knowledge retrieval feature (Size: Large).
- **`bob-cli-50` (Durable ever-finished reading history):** Persistent reading history tracking for reference notes (Size: Large).
- **`bob-cli-5g` (Mac 15-minute cron for ref jobs):** Hands-free background execution of queued web clips on macOS (Size: Small).

### 5.3 Recently Closed High-Impact Beads
Three task beads were closed within the 48-hour audit window after being successfully diagnosed and resolved by recent epic phases:
- **`bob-cli-4m` (Resolved 2026-10-06):** Fixed review walk line-shifting errors by migrating `reviewAnsweredKeys` from naive `path:line` keys to content/text identity in navigation plugin v2.7.1.
- **`bob-cli-4r` (Resolved 2026-10-07):** Eliminated Highlights sidecar setext title preamble leaks in `bob-cli-4w.8`.
- **`bob-cli-4v` (Resolved 2026-10-07):** Closed an SSRF validation vulnerability where URL validation accepted IPv4-mapped IPv6 literals in `bob-cli-52.2`.

---

## 6. Strategic Recommendations

1. **Immediate CI & Tree Health Triage:**
   Assign small-task workers immediately to **`bob-cli-4j`** and **`bob-cli-4u`**, followed by **`bob-cli-2e`** and **`bob-cli-3c`**. All four are Small-sized beads that will immediately eliminate the 4 primary sources of test failure and landing friction across the autonomous swarm.
2. **Deploy Vault Sync Guard:**
   Prioritize **`bob-cli-59`** before launching further parallel agent runs on plugins to prevent silent rollbacks of live Obsidian vault configurations.
3. **Repair SASE Event Store:**
   Address **`bob-cli-21`** to restore the project-wide artifact linking capability, allowing agents to accurately record evidence graphs.
4. **Schedule the Zorg Migration Epic:**
   Plan **`bob-cli-4x`** as a dedicated, human-reviewed migration epic to transition legacy reading notes into the reference library.
