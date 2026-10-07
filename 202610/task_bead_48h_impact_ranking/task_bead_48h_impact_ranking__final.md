# Which recent bob-cli task beads carry the most impactful work

Consolidated report from the lead researcher. It merges the five independent swarm reports (`__cdx`,
`__cld`, `__grk`, `__mus`, `__gem`) with the lead's own verification on 2026-10-07.

- **Window:** task beads created, or given a `sase bead +1`, between 2026-10-05 16:24:36 and
  2026-10-07 16:24:36 UTC. That is the 48 hours before the swarm was dispatched.
- **Code checked:** bob-cli master `65501f6`. No newer commits existed on `origin/master` at 16:47 UTC.
- **Host:** apollo (16 cores, load around 2.5, Pandoc 3.1.3).

## 1. Bottom line

The window contains **31 task beads**. The most impactful work among them is making master's test
gate honest again, and that work is also the cheapest.

- **One one-line defect turns off most of the test suite.** `bob-cli-4j` fails the Rust lib suite on
  every run. Plain `cargo test`, which is what `just all` / `just test` run, then stops before **14 of
  its 15 test binaries** execute, so **1,306 integration tests (1,154 of them in `tests/cli`) never
  run**.
- **That has already let a real regression land.** The lead ran `cargo test --no-fail-fast` and found
  a deterministic CLI failure with no bead. It came from today's commit `84a8a31` (the `bob ref` help
  snapshot still lists `clip`), and nobody saw it. It is now filed as `bob-cli-5i`.

After the gate come three defects of different kinds:

- **`bob-cli-21`:** the broken artifact-link store, which `sase artifact doctor` still reports as
  unhealthy today.
- **`bob-cli-33`:** the 2 s Tasks-sandbox deadline on Bryan's daily `bob plan` / `bob freshness`
  read path.
- **`bob-cli-59`:** a plugin-sync hazard that can silently roll back the live vault.

The strongest product bet is `bob-cli-4x`, which would bring about 424 legacy reading records into the
reference library. Two closed beads in the window, `bob-cli-4m` and `bob-cli-4r`, delivered important
correctness fixes and rank on the work they shipped.

## 2. Scope and method

**Population.** "Task bead" means `issue_type: task`. The bead policy (`sase memory read
sase_beads.md`) defines `task` as a separate type from `plan` (epics) and `phase`. The lead pulled
`sase bead list --status all --type task --limit 0 --format json` (109 task beads) and took the union
of two sets:

- beads whose `created_at` falls in the window;
- beads with any `plus_one_evidence[].timestamp` in the window.

The result matches cdx, cld, grk, and gem exactly:

| Measure | Count |
|---|---|
| Task beads in scope | **31** |
| Created in the window | 25 |
| +1ed in the window | 9 (3 of these were also created in the window) |
| Older beads in scope only through new +1s | 6: `21`, `2e`, `33`, `3c`, `3w`, `40` |
| +1 events in the window | 23 |
| Status | 28 ready, 3 closed (`4m`, `4r`, `4v`) |
| Type | 9 bug, 8 memory, 7 feature, 4 flake, 3 ci |

The set was the same at 16:47 UTC. The lead filed `bob-cli-5i` (16:57) after the cutoff, so it is
outside the audited set by construction.

**Scope conflict resolved.** mus counted 102 beads by including 12 plans and 59 phases, and its top 10
is mostly epics (`52`, `4w`, `4i`, `4s`, `4l`, `4q`, `56`). Those are not task beads, so they are
excluded from the ranking. mus's view is still useful context: the task beads with the most product
leverage are follow-ups that the `bob-cli-4w` (reference library) and `bob-cli-52` (links go to the
reading queue) landings filed.

**Impact criteria.** These are weighed together, not scored:

- **Reach:** Bryan's daily tools, then every agent landing, then a rare path.
- **Severity:** silent wrong results outrank loud failures, which outrank cosmetic issues.
- **Evidence strength:** independent reproductions, mechanisms checked against current source, and
  quantified scope.
- **Leverage per unit of effort.**

A +1 is append-only evidence, not a vote. +1 counts also favor defects that agents hit. Bugs only
Bryan hits (`33`, `58`, `59`) are under-represented, so their reach is judged by the surface they
touch.

**Closed beads stay in the ranking.** The question asks which beads are associated with the most
impactful work, and two of the three closes shipped high-value fixes. cdx and grk ranked closed beads;
cld and gem did not. §7 gives the open-only substitution.

## 3. What the lead verified directly

These checks target the places where the reports were thin or disagreed. All ran read-only, except
filing `bob-cli-5i` (with one note) and one +1 on `bob-cli-21`, both described below.

| Check | Result | Bearing |
|---|---|---|
| `cargo test --lib` on `65501f6`, run 5 times | All 5 runs failed (exit 101) on exactly one test, `every_value_arg_has_a_decision` (4j). 1874 passed. | 4j fails deterministically on every host. |
| Same 5 runs: the race tests `missing_note_and_missing_section_are_warning_successes` and `scan_excludes_r3_and_r7_paths` | Passed 5 of 5 on apollo at load around 2.5. | The 2e/40/5c race depends on load. It reproduced on 5 busy landing hosts in the window but did not reproduce here. |
| Same 5 runs: `listen_filter_renders_card_and_encoded_play_link` | Passed on apollo (Pandoc 3.1.3). | 4u fails only with Pandoc 3.1.11.1. Every reproduction was by an athena land agent, and athena is where landings run. |
| `cargo test` (the `just test` recipe) | Stops after the lib binary fails. Only 1 of 15 test binaries runs. | **New finding.** 4j hides the entire integration suite. |
| `cargo test --no-fail-fast` | 3177 passed, 4 failed (details below). | Turns cld's "masking risk" into an observed regression. |
| `sase artifact doctor` | Exit 1, `Status unhealthy`. Reports `Link event reduction errors: operation_id de29d2e2… was reused` and `Link event objects 977 durable / 10482 pending (delta +9505)`. A typed `link add` attempt at 16:58 UTC failed with the same error. | 21 is still live. The pending/durable gap suggests a large unreduced backlog; that reading is inferred, not confirmed. |
| `bob freshness list -f json -l 1`, run 3 times | All succeeded, at 5.50–5.52 s each. cld saw 5.6–6.0 s in 4 runs. | 33 fails intermittently under load; even successful runs are slow. |
| Vault plugin state (`bob plugins list --no-pull`) | `bob-ledger-tools` 1.34.0, `synced`. | The 59 rollback (1.34.0 → 1.33.0) was repaired. The hazard is now latent, not ongoing damage. |
| Source | Confirmed in current source: `EXPRESSION_TIMEOUT` = 2 s with eager `JsSandbox::new` at `dataview/tasks/mod.rs:167,195,240,277` (33). `plugins_dir()` falls back to the canonical checkout (`env.rs:18–24`, `plugins/cli.rs:229`) with no cwd guard (59). `Arg::new("audio")` has no value hint and no kinds entry (4j). `just --show check` exits 1 (3c). The only env locks are module-private (2e). | Each mechanism is still present on master. |
| +1 notes | 4j's in-window +1s cite about 24 phase-level PROPOSED FOLLOW-UPs across 5 epics; 4u's about 22; 40's about 13. `bob-cli-40` has **8** lifetime +1s (gem reported 11). | Puts a number on the re-diagnosis cost of a red master. |

**The four `--no-fail-fast` failures:**

1. `bob-cli-4j`: known.
2. **`help::ref_help_matches_grouped_snapshot`.** Deterministic: it failed 2 of 2 exact serial runs.
   Commit `84a8a31` (14:43 UTC today) removed `clip` from the `bob ref` group list, but
   `tests/fixtures/help/ref-short.txt:11` still lists it. No bead tracked it, and the `bob-cli-52`
   landing triage at 16:16 UTC does not mention it. **Filed as `bob-cli-5i`** (ci, small) after the
   `/sase_new_task` duplicate check.
3. `highlights::create::ingest_characterizes_url_failure_modes`: known. The `bob-cli-52` land agent
   owns it in its landing tale.
4. `capture::r#ref::capture_url_with_markers_or_flags_stays_a_task`: an environment artifact of this
   session. A stale SSH-forwarded `DISPLAY` made `xclip` fail. It passes under `env -u DISPLAY`.

**Side effects.** The typed related links for `5i` were rejected by the `21` store, so they were
recorded as a `RELATED` note. The doctor evidence was added as a +1 on `bob-cli-21`. The first
bead-store pushes hit a transient GitHub `Internal Server Error`; a retry published everything
(`e408f6b..d12d250`).

## 4. Where the researchers disagreed, and how it was resolved

| Disagreement | Resolution |
|---|---|
| **Scope.** mus used 102 beads; the other four used 31. | 31. Plans and phases are not task beads (§2). |
| **Closed beads.** Ranked by cdx and grk, excluded by cld and gem. | Ranked on delivered impact and labeled closed. §7 gives the open-only list. |
| **Whether 2e is #1 (cld) or #9 (grk).** | **#2.** 2e is the most-corroborated defect, but it is intermittent: 0/5 on apollo. 4j is deterministic, and it is what currently hides the CLI suite. |
| **Whether 4u is a universal red test.** | No. It fails deterministically only with Pandoc 3.1.11.1 (athena, the landing host) and passes with 3.1.3 (apollo). The fix must accept both escapings. It ranks #9 because landings run on athena. |
| **Whether 4x is #1 (grk) or #10 (cld).** | **#7.** It is the largest completeness gap, but the benefit is potential: it is xlarge and needs Bryan's design review (mapping, dedupe, source-hub policy). |
| **Whether 59 is #1 (gem) or an honorable mention (grk, mus).** | **#5.** The failure is silent and the fix small, but it has one recorded incident, now repaired. |
| **Whether 3c is near the top (cld #7, gem #8) or outside the 10 (cdx, grk).** | **#10.** The lead's masking finding raises its value: the canonical gate should run every test binary, which prevents the `5i` class of miss. |
| **Whether 5f (grk #6, gem #9) or 5g (cdx #10) makes the list.** | Neither. 5g is the cheaper first step, and neither bead has measured failure-frequency data. |
| **Whether 58 makes the list (cld, grk, gem #9–10).** | #11. It is broad and visible to Bryan, but cosmetic. It loses its slot to 3c because of the masking evidence. |
| **bob-cli-40's +1 count.** | 8, not 11. |

## 5. Ledger of all 31 beads

The **+1** column shows in-window / lifetime counts. Ranks refer to §6.

| Bead | Type / size | Status | +1 | Assessment |
|---|---|---|---|---|
| `4j` | ci / S | ready | 6/6 | **#1.** Deterministic red lib suite; hides 1,306 integration tests. |
| `2e` | bug / S | ready | 1/14 | **#2.** Root cause of the parallel env-var race. |
| `40` | flake / L | ready | 5/8 | Same test and cause as 2e. Fold it into 2e's fix, then close it as superseded. |
| `5c` | flake / L | ready | 0/0 | `BOB_NOW` variant of the same class; the cause is not isolated. Include it in 2e's acceptance tests. |
| `21` | bug / L | ready | 2/5 (+1 from the lead after the cutoff) | **#3.** The artifact-link store has been broken for about 4 weeks. |
| `33` | bug / M | ready | 1/1 | **#4.** The 2 s sandbox deadline on the daily Tasks read path. |
| `59` | bug / S | ready | 0/0 | **#5.** A bare plugin sync can silently roll back the vault. |
| `4m` | bug / M | **closed** | 0/0 | **#6.** Delivered: the review walk no longer silently skips rows. |
| `4x` | feature / XL | ready | 0/0 | **#7.** About 424 legacy reading records are invisible to `bob ref`. |
| `4r` | bug / L | **closed** | 0/0 | **#8.** Delivered: fake annotations removed from 113 of 115 notes. |
| `4u` | ci / S | ready | 3/3 | **#9.** Red on athena's Pandoc 3.1.11.1. |
| `3c` | bug / S | ready | 3/8 | **#10.** No `just check` gate. |
| `58` | bug / M | ready | 0/0 | #11. 239 of 291 library PDFs repeat the H1 as section 1; 147 double-number headings. Shares `create.rs` with 4u. |
| `3w` | flake / S | ready | 1/5 | A cold 16 ms perf assertion fails bob-plugins `npm test` under load. A mechanical fix. |
| `5g` | feature / S | ready | 0/0 | A scheduled `ref jobs run -q` drain recovers jobs after a missed kick. Cheap robustness for the new `bob-cli-52` path. |
| `5f` | feature / L | ready | 0/0 | Ref-job retries with backoff. A larger design with no measured failure rate. |
| `4y` | feature / L | ready | 0/0 | Annotation search across the library. Valuable, but still a proposal. |
| `5d` | memory / S | ready | 0/0 | The most important missing decision record: a bare link means reading intent, a contract spanning 3 repos. |
| `51` | memory / S | ready | 0/0 | Decision record that reading state is derived. Land it before deciding 4z or 50, which push against it. |
| `4t` | memory / S | ready | 0/0 | Decision record for inbox answer routing, a shipped contract. |
| `5a` | memory / S | ready | 0/0 | Decision record for In Progress marks and the Work Log trigger. |
| `5b` | ci / S | ready | 0/0 | The web-clip self-test aborts Chrome under SASE's long `TMPDIR`. Production already has a fallback. |
| `5e` | memory / S | ready | 0/0 | Ref Job glossary term. Pair it with 5d. |
| `50` | feature / L | ready | 0/0 | Durable "ever finished" reading history. Conflicts with the recorded derived-state design. |
| `5h` | feature / L | ready | 0/0 | `ref create` JSON output. Waits on 4a's flag policy. |
| `4z` | feature / S | ready | 0/0 | Bare `bob ref` shows the queue. Reverses an explicit epic decision. |
| `4k` | flake / L | ready | 0/0 | Mac StartPending timeout. One fail/pass pair; cause unknown. |
| `4v` | bug / S | **closed** | 0/0 | Delivered: IPv4-mapped IPv6 private-host bypass fixed. Exposure was low because Bryan chooses the URLs. |
| `4o` | memory / S | ready | 1/1 | Stale mac-pom flash cadence in the glossary. Do it together with 57. |
| `57` | memory / S | ready | 0/0 | Same glossary strand: stale "polls every 15 seconds". |
| `4n` | memory / S | ready | 0/0 | One glossary phrase contradicts the containment rule. |

## 6. Ranked top 10

Each researcher's rank appears in brackets as cdx / cld / grk / gem / mus. "HM" means honorable
mention and "—" means unranked.

**1. `bob-cli-4j`: `ref create --audio` has no completion-kinds decision.** Ready, ci, small.
[6 / 2 / 8 / 5 / 8]

- **What fails.** One missing `ValueHint::FilePath` or kinds-table entry makes
  `every_value_arg_has_a_decision` fail on every run, on every host. The lead saw 5 of 5.
- **Evidence.** All six land agents that ran the Rust suite in the window reproduced it on six SHAs
  (4i.7, 4q, 4s, 4w, 55, 52), and their +1 notes cite about 24 phase-level re-diagnoses.
- **Hidden cost.** Because cargo stops on the failing lib binary, `just all` never runs the 1,306
  integration tests. A real CLI regression (`5i`) landed today and went unnoticed.
- **Why #1.** It has the highest payoff per line of fix in the set. Until it lands, no agent can see a
  green suite, and the red baseline trains everyone to wave failures through.

**2. `bob-cli-2e`: share process-wide env isolation across Rust tests.** Ready, bug, small. Absorbs
`40`; covers `5c`. [5 / 1 / 9 / 4 / 9]

- **What fails.** `capture_pomodoros::tests::with_env` mutates `BOB_DAY_FILE` with no lock, while
  `capture_complete` holds a module-private lock. Parallel runs therefore point the missing-note
  assertion at another test's day file.
- **Evidence.** It is the most-corroborated defect in the project: 14 +1s on 2e and 8 on 40. The six
  in-window +1s across the two came from five distinct landings (4i, 4q, 4s, 4w, 52). Historical
  failure rates range from 1 in 3 to 5 of 5 full runs.
- **Load dependence.** It did not fire in the lead's 5 runs on a lightly loaded apollo. That matches
  the load-dependent mechanism and explains why it bites landings on busy hosts.
- **Fix.** Use one crate-wide env guard, or better, stop the tests from mutating the environment at
  all. Treat `5c` (`BOB_NOW`) as part of the acceptance tests, not as proven to share the cause.
- **Why it matters.** Once 4j is fixed, this race becomes what keeps master intermittently red, and
  intermittently hides the integration suite.

**3. `bob-cli-21`: the artifact-link event store rejects every new link.** Ready, bug, large.
[3 / 4 / 2 / 2 / 4]

- **Duration.** It has been broken since about 2026-09-07, and `sase artifact doctor` still reports
  the store unhealthy today.
- **Effects.**
  - Every `sase artifact link add` fails. The lead's own attempt failed.
  - `sase plan propose` with a `links:` inlet archives the plan and then crashes before the approval
    gate.
  - Six beads created in the window (`4t`, `4u`, `58`, `5c`, `5g`, `5h`) had to keep their relations
    as free text.
- **Why it matters.** Every day it stays open, the bead graph loses the structure that duplicate checks
  and audits like this one depend on.
- **Fix.** The two colliding event files are known, so the data repair is scoped. Hardening, so one
  bad historical pair cannot block every future write, belongs in sase.

**4. `bob-cli-33`: Tasks JS sandbox initialization hits the 2 s deadline.** Ready, bug, medium.
[1 / 5 / 4 / 6 / HM]

- **Mechanism.** Every native Tasks query eagerly builds a sandbox that hydrates the whole vault inside
  a 2 s budget meant for one user expression. That includes `bob plan`, `bob freshness`, the
  plan-budget hooks, the tmux segment, and `bob query`. Queries with no `by function` clause pay the
  cost too.
- **Evidence.** It reproduced on master today in the `bob-cli-55` landing. The lead's runs on apollo
  succeeded, at 5.5 s each.
- **Why it matters.** This is the main defect in the set that Bryan hits directly. It is intermittent
  on busy hosts, and its "interrupted" error reads like a bad query rather than a timeout.
- **Upside.** Building the sandbox lazily should also cut latency on his most-used commands. That
  speedup has not been measured.

**5. `bob-cli-59`: a bare `bob plugins sync` from a SASE worktree deploys the canonical checkout.**
Ready, bug, small. [2 / 6 / HM / 1 / HM]

- **Mechanism.** The source falls back to the canonical repo, with no cwd guard.
- **Incident.** One recorded incident silently rolled `ledger-tools` back from 1.34.0 to 1.33.0 during
  a sibling landing. The vault is back at 1.34.0 now.
- **Why it matters.** With several plugin-touching epics running at once, a recurrence leaves Bryan on
  stale plugins and verification phases testing the wrong code, with no signal either way.
- **Fix.** Small and well specified: refuse to sync when the cwd is inside a different bob-plugins
  checkout.

**6. `bob-cli-4m`: preserve review-row identity after line-shifting edits.** Closed (done), bug,
medium. [4 / closed §6 / 5 / closed list / —]

- **What it fixed.** Day-long `path:line` keys made the `]s` walk silently treat a due row as already
  answered after an insertion or a recurring-task completion. A silent skip in Bryan's daily GTD loop
  is worse than a loud error.
- **How.** Shipped as text-identity keys in navigation 2.7.1. cdx reran the 6 walk-identity tests and
  all 6 passed. Keep it closed.

**7. `bob-cli-4x`: migrate the zorg-era reading records into the reference library.** Ready, feature,
xlarge. [7 / 10 / 1 / 3 / HM]

- **Gap.** About 424 records, led by `work_ref.md` (75) and `nvim_ref.md` (69), are invisible to
  `bob ref find/list` and to the `bob_ref` skill. Agents must consult that skill before recommending
  reading. cld confirmed the count live with `bob ref doctor`.
- **Why it matters.** It is the only bead in the set that turns an existing data asset into usable
  context. It also completes the `4w` library epic.
- **Why it is #7.** The benefit is still potential: it needs a reviewed design for the bulk vault
  write (status mapping, dedupe, source-hub policy).

**8. `bob-cli-4r`: keep exported metadata out of Bryan's annotations.** Closed (done), bug, large.
[8 / closed §6, "≈#4" / 3 / closed list / —]

- **What it fixed.** 113 of 115 annotated reference notes rendered a stale status/parent/URL marker
  mirror as one of Bryan's own annotations. Any agent reading them would have taken Highlights
  metadata for Bryan's notes.
- **How.** Content-based mirror detection now drops them silently. `bob ref doctor` reports
  `annotations: ok`.
- **Why it matters.** This fix is what makes the new library trustworthy to read.

**9. `bob-cli-4u`: the listen-card Pandoc test pins ampersand escaping.** Ready, ci, small.
[near miss / 3 / HM / 7 / HM]

- **What fails.** The test fails deterministically wherever Pandoc 3.1.11.1 emits a bare `&` inside
  `\href`. Every reproduction came from athena land agents (4s, 4w, 52), whose +1 notes cite about 22
  phase-level re-diagnoses. It passes on apollo's Pandoc 3.1.3.
- **Why it matters.** Without this fix, the landing host stays red even after #1 and #2.
- **Fix.** Assert that the URI is preserved under both escapings, keeping the percent-encoding
  coverage. Coordinate with 58, which touches the same `create.rs` Pandoc path.

**10. `bob-cli-3c`: add the canonical `just check` gate.** Ready, bug, small.
[near miss / 7 / HM / 8 / HM]

- **Evidence.** Every landing prompt asks for `just check`, the recipe does not exist, and each
  landing improvises its own substitute. It has 8 lifetime +1s, 3 in the window.
- **Why it matters.** The lead's finding sharpens its value. The gate should run every test binary,
  with `--no-fail-fast` or explicit `--lib` and `--test cli` steps, so one failing binary cannot hide
  the others again. It pays off fully once #1, #2, and #9 make the suite green.

## 7. Recommended sequencing

1. **Green-gate batch, one small tale:**
   - `4j`, then `5i`: one line each.
   - `2e`: close `40` as superseded, and re-verify `5c`.
   - `4u`.
   - `3c`, defining `just check` to run every test binary.

   Success criterion: `cargo test --no-fail-fast` passes twice in a row on athena under default
   parallelism.
2. **`21`:** data repair in this project, plus a hardening task in sase.
3. **`33` and `59`:** independent small and medium fixes.
4. **Memory batch,** each through `/sase_memory_write`: `51`, then `5d` + `5e`, then `4t` (+`4n`), then
   `5a`, then `4o` + `57`. Do `4o` + `57` only after the Fibonacci-reminder tale lands or is rejected.
5. **Questions for Bryan:**
   - `4x`: the migration design.
   - `4z` and `50`: both reverse recorded decisions.
   - `5h`: blocked on `bob-cli-4a`.
   - `5f` / `5g`: start with `5g`.

**Open-only view.** For a queue of work still to do, drop `4m` and `4r`. Promote `58` (Markdown PDF
headings) and then `3w` (the plugin perf flake), and shift ranks 7–10 up by one.

## 8. Caveats

- The ranking is ordinal judgment. Within the leading cluster, the boundary between broad workflow
  failures and narrow polish is more certain than the exact order.
- These figures are recorded measurements from bead evidence, not remeasured here: the 424 records,
  113/115 notes, 239/291 and 147/291 PDFs, and historical failure rates.
- The lead ran the Rust suites on apollo only. Athena behavior comes from land-agent evidence.
- The doctor's "pending vs durable" link-event gap is reported verbatim. Its operational meaning was
  not confirmed.
- **Incidental, unverified by the lead:** cld observed `bob ref doctor` failing on
  `lib/docs/gastown_readme.textbundle` because a vault `.gitignore` rule excludes its
  `text.markdown`. It may be another instance of `bob-cli-1g`.
