# Impact Audit of bob-cli Task Beads Created or +1ed in the Last 48 Hours

- **Researcher:** research.0e.cld (Claude, independent swarm member)
- **Date:** 2026-10-07
- **Window:** 2026-10-05T16:24:51Z → 2026-10-07T16:24:51Z (48 hours before the audit ran)
- **Data source:** `sase bead list --type task --status all` and `sase bead read` (audited) on the bob-cli
  bead store at beads-repo commit `e408f6b`, which was in sync with `origin/main`. Code checks ran on
  bob-cli master `65501f6`. The only change since `2d568fa`, where most of the latest reproductions ran,
  is a 10-line `docs/date-marks.md` edit, so those reproductions still describe current master.

## 1. Bottom Line

The 31 beads in the window fall into four groups. The most impactful group is also the cheapest to fix:
**master is red, and every agent landing pays for it.** Three defects keep `just all` / `cargo test`
failing on master:

- a race on a process-global env var in the Rust lib tests (`bob-cli-2e`, plus its duplicate `bob-cli-40`
  and the related `bob-cli-5c`);
- a missing completion-kind decision for `ref create --audio` (`bob-cli-4j`);
- a test that pins Pandoc's ampersand escaping (`bob-cli-4u`).

On top of those, a fourth defect (`bob-cli-3c`, no `just check` recipe) means the gate that landing
prompts ask for does not exist.

Within the window, every epic landing after `bob-cli-4j` was filed that ran the Rust suite hit it: 4i.7,
4q, 4s, 4w, 52, and 55. The only exception was the plugins-only bob-cli-4l landing. Epics bob-cli-4w
and bob-cli-52 each had 8–9 phases re-diagnose it and file it as a PROPOSED FOLLOW-UP. All four beads
are size S. Together, the green-master work (the bob-cli-2e race fix plus
bob-cli-4j, bob-cli-4u, and bob-cli-3c) is the highest-leverage work in the set.

Ranked next:

- **bob-cli-21:** the artifact-link event store has been corrupt for four weeks. Within the window, six
  new beads had to fall back to free-text "RELATED:" notes because of it.
- **bob-cli-33:** the main user-facing reliability bug. The 2 s Tasks sandbox deadline intermittently
  breaks `bob plan`, `bob freshness`, and the hooks.
- **bob-cli-59:** a bare `bob plugins sync` silently reverts plugins that the vault has already deployed.

The rest of the set is mostly design-gated feature follow-ups from the bob-cli-4w and bob-cli-52 epics,
plus a backlog of eight memory beads. Those are worth doing but are lower impact for now.

## 2. Method

**Selection.** A task bead is in scope if `created_at` falls in the window **or** at least one entry in
its `plus_one_evidence` has a timestamp in the window. That gives **31 beads**:

- 25 were created in the window.
- 6 older beads are in scope only through new +1s: 21, 2e, 33, 3c, 3w, 40.
- Three of the new beads (4j, 4o, 4u) also picked up +1s.
- The window holds 23 +1s in total.
- 28 of the 31 are `ready` and 3 are `closed` (4m, 4r, 4v).
- By type: 9 bug, 3 ci, 4 flake, 7 feature, 8 memory.

**Impact criteria.** I weighed five things together rather than with a formula:

1. **Reach:** who hits it and how often (Bryan's daily tools, every agent landing, or one rare path).
2. **Severity:** silent wrong results or data loss outweigh a loud failure, which outweighs a cosmetic
   issue.
3. **Evidence strength:** how many independent reproductions there are and how recent they are. A +1 is
   evidence, not a vote, but distinct landings that hit the same defect measure its reach directly.
4. **Leverage per unit of effort:** bead size against payoff, and whether fixing it unblocks other work.
5. **Decision readiness:** whether it can be launched now, or needs Bryan's design call first.

**Verification I did myself** (read-only):

- Confirmed `just --list` has no `check` recipe.
- Confirmed `src/native/completion/kinds.rs` has no `audio` entry.
- Confirmed the only env locks are module-private: `capture_complete/tests/mod.rs:24`,
  `highlights_ref/listen.rs:673`, and `ref_jobs/kick.rs:110`.
- Confirmed `EXPRESSION_TIMEOUT` is still 2 s, and that `JsSandbox::new` is still built eagerly at four
  call sites in `dataview/tasks/mod.rs`.
- Confirmed `src/native/plugins/` has no `current_dir` guard.
- Ran `bob freshness list -f json -l 1` four times on apollo (16 cores, load ~3.7). All four succeeded,
  but each took **5.6–6.0 s**.
- Ran `bob ref doctor` on apollo. It reports `~424 zorg-era reading records … not indexed` and
  `annotations: ok (no leaked marker mirrors)`. The second line confirms the bob-cli-4r fix is live.

## 3. Inventory of All 31 Beads

Tier key: **A** = top-10 impact, **B** = solid but secondary, **C** = low or design-gated,
**✓** = already closed.

| Bead | Type | Size | Status | +1 (window/total) | Tier | One-line assessment |
| --- | --- | --- | --- | --- | --- | --- |
| bob-cli-2e | bug | S | ready | 1 / 14 | **A** | Root cause of the most frequent red `cargo test`: `BOB_DAY_FILE` set without a shared lock |
| bob-cli-40 | flake | L | ready | 5 / 8 | A (merge) | Same test and root cause as 2e. Fold into 2e's fix, then close as duplicate |
| bob-cli-5c | flake | L | ready | 0 / 0 | A (merge) | Same class (`BOB_NOW` race), predicted in 2e's +1s. Fix with the same process-wide env guard |
| bob-cli-4j | ci | S | ready | 6 / 6 | **A** | Deterministic red master: `ref create --audio` has no completion-kind decision |
| bob-cli-4u | ci | S | ready | 3 / 3 | **A** | Deterministic red master on Pandoc 3.1.11.1: test pins `\&` escaping inside `\href` |
| bob-cli-21 | bug | L | ready | 2 / 5 | **A** | Artifact-link store corrupt since ~09-07. All link writes fail, and `sase plan propose` with `links:` half-completes |
| bob-cli-33 | bug | M | ready | 1 / 1 | **A** | 2 s deadline on eager whole-vault sandbox init. `bob plan`/`freshness`/hooks fail intermittently with "interrupted" |
| bob-cli-59 | bug | S | ready | 0 / 0 | **A** | Bare `bob plugins sync` from a worktree deploys the canonical checkout, silently rolling back vault plugins |
| bob-cli-3c | bug | S | ready | 3 / 8 | **A** | Landing prompts require `just check`, which does not exist |
| bob-cli-3w | flake | S | ready | 1 / 5 | **A** | bob-plugins `npm test` turns red under load because of a single cold 16 ms timing assertion |
| bob-cli-58 | bug | M | ready | 0 / 0 | **A** | 239/291 research PDFs repeat the H1 and number sections 1.x; 147/291 double-number |
| bob-cli-4x | feature | XL | ready | 0 / 0 | **A** | ~424 zorg-era reading records are invisible to `bob ref find/list` and the bob_ref skill |
| bob-cli-5d | memory | S | ready | 0 / 0 | B | Missing decision record for the just-shipped "bare link = reading intent" contract, which spans 3 repos |
| bob-cli-5g | feature | S | ready | 0 / 0 | B | Cheap safety net: a scheduled drain for ref jobs that a failed kick or a reboot leaves behind |
| bob-cli-5b | ci | S | ready | 0 / 0 | B | `just check-web-clip-adapter` always fails under SASE agents (AF_UNIX path > 108 bytes) |
| bob-cli-51 | memory | S | ready | 0 / 0 | B | Decision record for the derived reading state. It should land before 50 and 4z, which push against it |
| bob-cli-4t | memory | S | ready | 0 / 0 | B | Decision record for the shipped inbox answer-routing contract |
| bob-cli-5a | memory | S | ready | 0 / 0 | B | Decision record for rendered In Progress marks, plus a Work Log trigger |
| bob-cli-5f | feature | L | ready | 0 / 0 | B | Ref-job retries with backoff, so transient failures stop producing ⚠️ fallback tasks |
| bob-cli-4y | feature | L | ready | 0 / 0 | B | Library-wide annotation search ("where did I comment on X?") |
| bob-cli-5e | memory | S | ready | 0 / 0 | C | Ref Job glossary term. Pair it with 5d |
| bob-cli-5h | feature | L | ready | 0 / 0 | C | JSON output for `ref create`. Blocked on bob-cli-4a's flag-naming policy |
| bob-cli-50 | feature | L | ready | 0 / 0 | C | Durable "ever finished" history. Needs a new stored field, against the current decision |
| bob-cli-4k | flake | L | ready | 0 / 0 | C | Mac StartPending test timeout. One CI observation so far |
| bob-cli-4z | feature | S | ready | 0 / 0 | C | Bare `bob ref` shows the queue. Reverses an explicit epic decision; UX nicety |
| bob-cli-4o | memory | S | ready | 1 / 1 | C | Stale mac pom flash cadence in a glossary strand. Do it together with 57 |
| bob-cli-57 | memory | S | ready | 0 / 0 | C | Same strand: stale "polls every 15 seconds" |
| bob-cli-4n | memory | S | ready | 0 / 0 | C | One phrase in the Reference Note strand contradicts the area-note containment rule |
| bob-cli-4r | bug | L | closed | 0 / 0 | ✓ | Fixed: fake marker-mirror "annotations" in 113/115 annotated ref notes |
| bob-cli-4m | bug | M | closed | 0 / 0 | ✓ | Fixed: the review walk silently skipped due rows after line-shifting edits |
| bob-cli-4v | bug | S | closed | 0 / 0 | ✓ | Fixed: IPv4-mapped IPv6 literals bypassed the private-host URL rule |

## 4. Cross-Bead Findings

### 4.1 "Master is red" is the dominant cost in this window

Within the window, each of these landings recorded independent reproductions of the same pre-existing
failures: bob-cli-4i, 4i.7, 4l, 4q, 4s, 4w, 52, and 55. Each failure also comes back as a fresh PROPOSED
FOLLOW-UP from most phases:

- bob-cli-4w.land cites 9 phases proposing bob-cli-4j and 8 proposing bob-cli-4u.
- bob-cli-52.land cites 8 phases proposing each of them.

Re-diagnosing every time is pure overhead. The bigger risk is that a permanently red baseline trains
agents to wave away failures, so a real regression can hide behind "the known three". bob-cli-3f.land
also notes that the failing lib binary stops cargo before the CLI integration tests run unless
`--no-fail-fast` is used. In other words, the 2e race actively hides the CLI suite.

The four green-master beads are all size S. bob-cli-40 and bob-cli-5c are labelled L, but they collapse
into 2e's fix. I recommend shipping them together as one small tale or epic:

1. Add one process-wide env guard, or better, stop the tests from mutating env at all by passing the
   day-file path and the time in directly. That fixes 2e, 40, and 5c. The `BOB_NOW` path in 5c is the
   one 2e's own +1 from bob-cli-3n.12.9.land predicted. bob-cli-5c's note lists 12+ modules that call
   `set_var`, so a crate-wide guard is better than another module-private one.
2. Give `--audio` a `ValueHint::FilePath` or a kinds-table entry (4j).
3. Make the listen-card assertion check that the URI is preserved, rather than which escaping Pandoc
   happens to emit (4u). Note that apollo runs Pandoc 3.1.3 and athena runs 3.1.11.1, so the test has to
   accept both.
4. Add `just check` as the documented gate (3c). It is only useful once 1–3 make it green.

### 4.2 Broken tooling is leaking into data quality

bob-cli-21 shows up in this window not only through its two new +1s. Six beads created in the window
(4t, 4u, 58, 5c, 5g, 5h) each carry a note saying the typed artifact link they wanted was rejected and
the relation was kept as free text instead. Every day this stays broken, the bead graph loses structure
that `/sase_new_task` duplicate checks and future audits like this one rely on.

The bob-cli-0wk.f0 +1 also documents a worse failure. `sase plan propose` with a `links:` inlet archives
the plan and then crashes before the approval gate, leaving the proposal half-done. The colliding events
were located in two plans-sidecar files, so a data repair looks tractable from this project. The
hardening (one bad historical pair should not block every future write) belongs in sase.

### 4.3 The new reference library produced a burst of follow-ups that need Bryan's input

Epic bob-cli-4w (the `bob ref` library) filed 4x, 4y, 4z, 50, and 51. Epic bob-cli-52 (URL→ref-job
routing) filed 5b, 5c, 5d, 5e, 5f, 5g, and 5h. These are mostly *design-gated*:

- 4x needs a migration design.
- 4z reverses design decision 1.
- 50 conflicts with design decision 3.
- 5h waits on bob-cli-4a.

Two sequencing points matter:

- **Record the decisions before reopening them.** bob-cli-51 records "reading state is derived, verbs
  are read-only". 4z and 50 both push against that record, so landing 51 first gives Bryan a stable
  baseline to accept or supersede.
- **5g is the cheapest robustness fix for the just-shipped capture path.** Without a scheduled drain,
  a stranded pending job waits for the next capture's kick or a manual run (`docs/ref-jobs.md` says
  "A pending job older than an hour usually means the kick never ran"). bob-cli-30's crontab drift
  touches the same file.

### 4.4 Memory backlog: eight small beads, three natural pairs

- **4o + 57:** same strand (`glossary/mac-menu-bar-pomodoro-indicator.md`). Do them in one edit, and
  only after the Fibonacci-reminder tale named in 4o's +1 lands or is rejected.
- **5d + 5e:** 5e should link the decision record that 5d creates.
- **4t + 4n:** both touch the area-note/inbox glossary family. 4t's note #2 already flags an inbox-file
  coordination question for Bryan.
- **51 and 5a** stand alone.

All of them need `/sase_memory_write` approval. The three decision records (5d, 4t, 5a) carry the most
weight. Decision records are what agents consult before changing behavior, so each missing one is a
standing invitation for a future agent to undo a deliberate design.

## 5. Ranked Top 10 Most Impactful Task Beads

The ranking covers open beads only, because they are where effort can still go. Closed beads are
covered in §6.

**1. bob-cli-2e: Serialize the capture_pomodoros `BOB_DAY_FILE` test mutation** (bug, S; fix
together with bob-cli-40 and bob-cli-5c)

- **Evidence.** This is the most-corroborated defect in the project: 14 +1s on 2e plus 8 on its
  duplicate 40. Reported failure rates range from about 1 in 3 to 5 of 5 full parallel
  `cargo test --lib` runs.
- **Reach.** bob-cli-40 alone gained +1s from five landings in the window (4i, 4q, 4s, 4w, 52), and
  bob-cli-52.land saw it fail in 2 of 2 runs today.
- **Hidden cost.** When the lib binary fails, cargo stops before the CLI integration tests run, so the
  CLI suite is silently skipped.
- **Leverage.** One crate-wide env discipline also fixes the newly filed note_ready `BOB_NOW` flake
  (5c).
- **Why it ranks first.** It costs the most agent time per day of anything in the set, it is the
  biggest masking risk, and it is a small fix.

**2. bob-cli-4j: `--audio` lacks a shell-completion kinds decision** (ci, S)

- **Evidence.** `cargo test --lib` fails deterministically on every run on master, and has since commit
  `2152202`.
- **Reach.** It has 6 +1s in under 48 hours, one from every Rust-running epic landing since it was
  filed, and 17 phase-level PROPOSED FOLLOW-UPs across bob-cli-4w and bob-cli-52 alone.
- **Effort.** It is a one-line `ValueHint` or kinds-table addition, the highest payoff-to-effort ratio
  in the set.
- **Why it matters.** Until it lands, no agent can ever see a green `cargo test`.

**3. bob-cli-4u: Listen-card Pandoc test pins ampersand escaping** (ci, S)

- **Evidence.** It is the third deterministic red test on master, with 3 +1s in the window (4s, 4w, and
  52 landings).
- **Effort.** Small, but it needs care. The bead asks to keep URI and percent-encoding coverage, not
  drop it. The fix has to tolerate the Pandoc versions actually installed: 3.1.11.1 on athena and 3.1.3
  on apollo.
- **Leverage.** Without it, #1 and #2 still leave master red, so its value is mostly in completing that
  set. bob-cli-58 touches the same `create.rs` Pandoc pipeline, so coordinate the two.

**4. bob-cli-21: Artifact-link event store rejects every new link** (bug, L)

- **History.** A whole SASE subsystem has been unusable in this project since about 2026-09-07. The bead
  was auto-swept as stale, then reopened by new evidence. It has 5 +1s, 2 of them in the window.
- **Breadth in the window.** Six new beads lost their typed relations because of it.
- **Severity.** The 0wk +1 shows `sase plan propose` with `links:` half-completing: the plan is
  archived, but there is no approval gate.
- **Path to a fix.** The exact two colliding link-event files are known, so the data repair is
  scoped. The guard against recurrence belongs in sase.
- **Why it ranks here.** It is degrading the bead knowledge graph every day it stays open.

**5. bob-cli-33: Tasks JS sandbox init hits the 2 s deadline** (bug, M)

- **Reach.** This is the most important bug in the set that Bryan hits directly. Every native Tasks
  query builds a JS sandbox that hydrates the whole vault through Moment, under a 2 s budget meant for
  one user expression. That includes `bob plan`, `bob freshness list/seed`, the task-status-hooks plan
  budgets, the tmux plan segment, and `bob query`.
- **Why it fails often.** Busy hosts are the norm here, because agents build and test constantly.
- **Misleading failure.** The error reads like a bad query ("interrupted"), not a timeout.
- **Evidence.** bob-cli-55.land reproduced it on master today. My runs on apollo succeeded but took
  5.6–6.0 s each, so there is little headroom.
- **Upside.** The proposed fix is to build the sandbox lazily, only when a `by function` clause needs
  it. That should also cut latency on Bryan's most-used planning commands, though I have not measured
  that.

**6. bob-cli-59: Bare `bob plugins sync` from a SASE worktree deploys the canonical checkout** (bug,
S)

- **Severity.** This silently corrupts the live environment. The vault copy is what Obsidian loads, and
  in bob-cli-56 a bare sync rolled ledger-tools back from 1.34.0 to 1.33.0, undoing a sibling phase's
  deployment.
- **Why now.** Concurrent epics that touch plugins are routine (three epics are in progress now). When
  this happens, Bryan runs stale plugin code and phases that verify in-vault behavior test the wrong
  code, with no signal either way.
- **Effort.** The fix is small and well-specified: abort when cwd is inside a different bob-plugins
  checkout, and update bob-plugins `AGENTS.md`. I confirmed `src/native/plugins/` has no `current_dir`
  guard today.

**7. bob-cli-3c: Add the canonical `just check` verification entry point** (bug, S)

- **Evidence.** It has 8 +1s, 3 of them in the window (4i.7, 4q, and 55 landings).
- **Impact.** Every landing prompt asks for `just check`, and every landing improvises its own
  fallback. Verification is therefore inconsistent across agents, and the landing record never names
  one gate as the bar that was met.
- **Effort.** Small.
- **Why it is not higher.** It pays off fully only once #1–#3 make the gate pass. Ship it in the same
  batch.

**8. bob-cli-3w: Stage-ranker 16 ms perf assertion flakes under parallel `npm test`** (flake, S)

- **Evidence.** It is the bob-plugins counterpart to #1: 5 +1s, the newest from the bob-cli-4l landing
  in the window. It was reproduced across epics 3v, 46, 47, 48, 4f, and 4l at 16–35 ms against a 16 ms
  budget, and always passes in isolation.
- **Impact.** Every plugin landing has to rerun it to prove nothing broke.
- **Effort.** The fix is mechanical: warm up and take a min or median, or move the budget behind an
  opt-in perf env var.

**9. bob-cli-58: `bob ref create` Markdown PDFs repeat the H1 and double-number headings** (bug, M)

- **Evidence.** It affects 239 of the 291 PDFs measured in `~/bob/lib/chat` (all sections numbered
  1.x), and 147 of them are double-numbered ("1.2 1. Evidence").
- **Impact.** This is the readability of every research and chat report Bryan reads in Highlights,
  including every future report from swarms like this one. It recurs indefinitely until fixed.
- **Effort.** Medium. It needs heading-id stability and coordination with the backlinks research and
  with 4u's `create.rs` changes.

**10. bob-cli-4x: Migrate zorg-era reading records into the reference library** (feature, XL)

- **Impact.** About 424 reading records (I confirmed the count live with `bob ref doctor` on apollo) are
  invisible to `bob ref find/list`. They are also invisible to the bob_ref skill, which agents must
  consult before recommending reading. The library has 598 notes, so this is a large blind spot.
- **Why it is last.** It is large, and it needs Bryan's design review: landing location, status
  mapping, dedupe, and what happens to the source hubs.
- **Upside.** It is also the only feature bead here that turns an existing data asset into usable
  context for agents. It completes the bob-cli-4w library epic and lets every JSON envelope drop its
  `coverage.scope` caveat.

**Next in line (B tier):**

- **5d:** decision record for bare-link routing. Small, with high leverage against regressions in a
  contract that spans three repos.
- **5g:** cron drain for ref jobs. Small robustness fix.
- **5b:** web-clip adapter self-test under SASE. Agents cannot verify the adapter today.
- **51:** decision record for the derived reading state. Land it before deciding 50 or 4z.
- **4t / 5a:** decision records for features that already shipped.
- **5f:** retries with backoff for ref jobs.
- **4y:** library-wide annotation search.

## 6. Already-Delivered Work in the Window (closed beads)

These are out of the forward-looking ranking but were high-value work. If delivered work were counted,
bob-cli-4r would sit around #4.

- **bob-cli-4r** (closed by bob-cli-4w.8): 113 of 115 annotated ref notes rendered a fake, often stale
  "status/parent" marker mirror as one of Bryan's annotations. Any agent reading annotations would have
  treated it as Bryan's own note. The fix drops the leaked blocks silently, with no tombstone churn.
  `bob ref doctor` now reports `annotations: ok (no leaked marker mirrors)`.
- **bob-cli-4m** (closed same day): the ]s review walk silently skipped due rows for the rest of the day
  after a line-shifting edit. It was fixed by text-identity keys (nav 2.7.1).
- **bob-cli-4v** (closed by bob-cli-52.2): IPv4-mapped IPv6 literals bypassed the documented "no private
  hosts" URL contract, including on redirect hops. The same phase also closed the DNS-rebinding gap with
  per-hop resolved-address pinning.

## 7. Recommended Sequencing

1. **Green-master batch** (one small tale): 2e (closing 40, re-verifying 5c) → 4j → 4u → 3c. Success
   criterion: `just check` and `just all` pass twice in a row on master under default parallelism.
2. **bob-cli-21 data repair**, with a sase hardening bead filed in the sase project.
3. **bob-cli-33** (lazy sandbox) and **bob-cli-59** (sync guard) as independent small/medium tasks.
4. **bob-cli-3w** in bob-plugins.
5. **Memory batch** via `/sase_memory_write`: 51 → 5d + 5e → 4t (+4n) → 5a → 4o + 57.
6. **Ask Bryan** about the design-gated features: 4x (migration design), 4z and 50 (they reverse
   recorded decisions), and 5h (blocked on bob-cli-4a).

## 8. Incidental Observations and Caveats

- **Incidental finding (outside the audit set).** `bob ref doctor` on apollo ends `result: failed` on
  `lib/docs/gastown_readme.textbundle`. Its `text.markdown` is excluded by the vault's `.gitignore` (the
  `*` rule on line 3), so git-synced hosts get only `assets/`. This looks like another instance of
  bob-cli-1g (vault files that sync to Obsidian but are untracked in the vault Git repo). I did not +1
  or file anything: doing so would have changed the very bead set this swarm is auditing. The lead may
  want to add it as evidence on bob-cli-1g.
- **Merge candidates.** bob-cli-40 duplicates bob-cli-2e (same test, same root cause, and 40's own +1s
  cite 2e). The project would be cleaner with 40 closed as `superseded` once 2e's fix lands.
- **What the evidence shows.** +1 counts strongly favor defects that agent landings hit. Bugs that only
  Bryan hits (33, 58, 59) are under-represented in +1s, so I weighted their reach by the surface they
  touch rather than by +1 count.
- **Snapshot.** I did not run the full Rust or npm suites myself. The red-master claims rest on the
  reproductions recorded on `2d568fa` today, plus my source checks that the defects are unchanged at
  `65501f6`. Several beads were created minutes before the audit (5b–5h), so their evidence is still
  thin.
