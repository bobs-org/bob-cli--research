# Similar-tasks calibration

Status: **calibrated from reviewed agent labels; Mac gate passes.** On
2026-10-21 Bryan delegated pair labeling to the agent (question gate
`bb385582-380e-4885-b381-3cb6422909db`). He asked `opus@xhigh` to double-check
the first pass and finish the work. Every label below is an agent judgment
made under that delegation. None is Bryan-authored or human ground truth. The
plan decision `calibration = labels` is satisfied in that delegated form.

## Result

| Bar or rule | Starting value | Calibrated value |
| --- | --- | --- |
| `POSSIBLE_DUPLICATE` | 0.70 | 0.70 (unchanged) |
| `SIMILAR` | 0.55 | **0.48** |
| `CLOSED_DUPLICATE` | 0.70 | 0.70 (unchanged; still the duplicate bar) |
| `HOLD_MARGIN`, `SHORT_QUERY_BOOST` | 0.10, 0.10 | unchanged |
| `SHORT_QUERY_TERMS`, `MIN_TERMS` | 3, 2 | unchanged |
| Stopwords | 29 words | + closed-class function words (pronouns, auxiliary and modal verbs, wh-words, `about`/`but`/`if`/`than`/`then`/`there`/`while`) |
| Numbers | single digits dropped | single digits kept as terms |
| Number guard | none | titles whose number sets differ are never `possible_duplicate` or `closed_duplicate` |

The table below uses the 496-query leave-one-out census at the labeled vault
state and the reviewed labels.

| Target | Starting bars | Calibrated | Met? |
| --- | --- | --- | --- |
| `possible_duplicate` precision ≥ 80% | 6/10 = 60.0% | **6/6 = 100%** (Wilson 95% 61–100%; 3 unordered relationships) | Point estimate yes; too few rows to establish |
| `similar` usefulness (D+U) ≥ 60% | 15/21 = 71.4% | **39/54 = 72.2%** (Wilson 59–82%; rank-one 33/45 = 73.3%) | Yes |
| Firing about 1 capture in 8 to 10 | 33/496 = 6.7% | **55/496 = 11.1%** (1 in 9.0); capture-like queries 44/442 = 10.0% | Yes, as a census proxy |
| Mac release p95 ≤ 50 ms | 46.881 ms | **43.494 ms** (calibrated build) | Yes |

Precision, usefulness and firing are in-sample measurements on the set used to
choose the bars. They are not a held-out evaluation or a measured
new-capture rate.

## Labels

- **First pass** (`file:explicit:b27592e2a9e2fdfe6a2165a2`): 80 directed pairs,
  10 D / 46 U / 24 N, authored from the score-free review before any scores
  were seen.
- **Review** (`calibration_labels_reviewed.md`/`.csv`/`.json`): I labeled all
  80 pairs from the score- and band-free review
  (`file:explicit:bd9fe71a265c714e4f41578a`) before opening the first pass or
  any score.
  - Agreement was 79/80. Pair 51 was revised N → U; both judgments are low
    confidence.
  - Pairs 42/72 were reconsidered as possible duplicates and kept U.
  - Confidence was lowered on 9/22 (high → medium) and 37/47 (medium → low).
  - Reviewed totals: **10 D / 47 U / 23 N**, or 6 D / 28 U / 14 N across 48
    unordered relationships.
- **Newly exposed pairs.** The tokenizer and Similar-bar changes exposed nine
  pairs below the old observation floor that became visible in at least one
  evaluated variant (N1–N9; six are visible at the final bars). They were
  labeled with the same rubric: 7 U / 2 N. An experiment printout had already shown
  their scores, so these nine are not score-blind. Every visible row at the
  final bars is labeled.
- **Rubric rules.**
  - Parent/subtask, reading/implementation and implementation/test pairs are U.
  - Same subsystem with a different instance (sibling provider adapters,
    sibling artifact entity types) is U.
  - A shared template with different subjects (different movies, readiness
    boilerplate, "Improve sase X") is N.
  - Literal identical titles in different products are U.
- No live-vault note bodies or referenced documents were read. Both passes
  come from one model family and are not independent raters. Reverse
  directions of one relationship are dependent observations.

The first-pass files (`calibration_labels_astra.*`,
`calibration_label_analysis_astra.*`) and the original blank
`calibration_worksheet.csv` / `calibration_review.md` are preserved
unchanged.

## Method

1. **Census.** `scripts/dev/capture_related_calibrate` runs every open task
   title through `bob capture-related --query … --days 30 --limit 100
   --exclude NOTE:LINE` with `BOB_NOW` pinned, keeps every response, and
   reports firing per band. The labeled census ran at vault commit `6af37e5e`
   with `BOB_NOW=2026-10-21 11:50:47`: 496 queries, 53 routes, 0 errors.
   Every returned candidate (80 directed / 48 unordered pairs) was labeled.
2. **Reproducible evaluation.**
   - The live vault had drifted 66 commits by review time. Every variant was
     therefore evaluated against a read-only text snapshot of the vault at
     `6af37e5e`, extracted outside the vault with census-time mtimes
     (`calibration_snapshot_provenance.json`).
   - The pre-calibration binary reproduced all 496 retained responses exactly
     on that snapshot (ignoring the absolute `target` path).
3. **Engine runs, not spreadsheet sweeps.**
   - Each variant reran all 496 queries through a real release build. A
     scratch-copy experiment build exposed environment toggles; the shipped
     source has none.
   - Bars were never re-derived from rounded scores, so short-query boosts,
     same-title rules, open-duplicate suppression of closed rows, hold, and
     limits all applied as shipped.
   - The final source was then built normally and reproduced the chosen
     variant on all 496 responses.
4. **Live cross-check.**
   - The sampler with the final binary on the live vault (read-only, status
     unchanged) gave 489 queries, 0 errors, and 55 fired (11.2%).
   - Joined to labels by note and title, the live visible rows carry the same
     label counts as the snapshot. Its six apparently new pairs are labeled
     pairs 27/34, 38/60 and 52/66, with `#prj_is_blocked` added to their
     titles since the census.

## What the labels exposed, and the fixes

At the starting bars, scalar thresholds could not reach the precision target.
The best `possible_duplicate` precision available from any single bar was
60%, because two false positives outscored every true duplicate.

| Finding (pairs) | Cause | Generic fix | Effect |
| --- | --- | --- | --- |
| Part 1 vs Part 2 readings scored 0.930/0.909 (13/25, U) | The single digit `2` was dropped as a 1-character token, so only `part` differed | Keep single-digit numbers; titles with different number sets cannot be possible or closed duplicates | Now `similar` (useful) |
| Readiness projects scored 0.767/0.774 (10/23, N) | Boilerplate function words (`are`, `about`) were terms and outweighed the different subjects | Closed-class function-word stopwords | Now `similar` (0.678/0.686) |
| Closed admin rename matched "Apply to 29 job openings" (18, N) | Shared identifier tokens; candidate also names `2026` | Number guard | No longer a closed duplicate |
| Closed "Gas Town vs. SASE" for "Gas City vs. SASE" (30, U) | Shared `where`/`what`/`should` | Stopwords | Below the closed bar |
| "Download Romantic Comedy movie" vs "Download "9" movie" (39, N) | Same digit-drop issue | Keep digits | Similar → hold |

Stopword choice. Lucene's classic stop set left the readiness pair at 75%
possible-duplicate precision. NLTK's English list also reached 6/6, but it
strips particles, quantifiers and negations that change what a task asks for
(`sign up`, `figure out`, `all`, `not`). The adopted list is the
closed-class subset only. Every comparison is in `calibration_final_analysis.json`
(`sweep`).

Bar choice.

- **`possible_duplicate`: 0.70 is the knee.**
  - 0.65 admits reading/implementation, sibling-provider and readiness pairs
    (6/14 = 42.9%).
  - 0.75 keeps 3/3 but halves duplicate recall.
- **`similar`: usefulness is flat from 0.45 to 0.55** (69.9–79.4%), so the
  firing target decided this bar.

  | Similar bar | Fired | Capture-like queries |
  | --- | --- | --- |
  | 0.50 | 9.5% | 8.6% |
  | **0.48** | **11.1%** | **10.0%** |
  | 0.46 | 12.7% | 11.3% |
  | 0.45 | 13.7% | 12.4% |

  0.48 is the value inside the 1-in-8-to-10 range on both populations.
- **Closed and hold bars are unchanged.**

## Final band composition (snapshot census, reviewed labels)

| Band | D / U / N | Notes |
| --- | --- | --- |
| `same_title` | 0 / 2 / 0 | Bob vs SASE docs-site task (14/26): literal same title, different work |
| `possible_duplicate` | 6 / 0 / 0 | Sell stocks (12/24), Cancel Obsidian (11/33), Statistics tab (9/22) |
| `similar` | 2 / 37 / 15 | Includes the CT appointment duplicates (6/48), previously only hold |
| `closed_duplicate` | 2 / 2 / 0 | UPS battery (3), dependency removal (4); glossary subtask (1), `%hold` implementation vs E2E test (2) |
| `hold` | 0 / 12 / 8, plus 79 unlabeled | Never causes a first display |

Rows changed from the starting bars:

- `possible_duplicate` → `similar`: 4 rows (13/25 U, 10/23 N).
- `closed_duplicate` → none: 2 rows (18 N, 30 U).
- `similar` → `hold`: 39 (N).
- `hold` → none: 67 (N).
- `hold` → `similar`: 24 rows (2 D / 16 U / 6 N).
- Newly visible `similar`: 6 rows (4 U / 2 N).

Sensitivity of `similar` usefulness at the final bars:

| Label variant | Similar usefulness |
| --- | --- |
| First-pass labels | 38/54 = 70.4% |
| Every low-confidence judgment flipped (all five in Similar go U → N) | 34/54 = 63.0% |
| Excluding `#gtd` checklist and reading-task queries | 26/40 = 65.0% (possible duplicate still 6/6) |
| Unordered relationships | 22/31 = 71.0% (possible duplicate 3/3) |

At most two rows shown per query: 51/65 = 78.5% useful.

The plan's research pairs still hold:

- "templated capture" vs "capture templates" reaches `possible_duplicate`;
- the CT appointment pair reaches at least `hold` (it is now `similar`);
- the `%d` vs `!<cmd>` code-span pair stays below `similar`.

## Limits and open questions

- **Small samples.** Possible-duplicate evidence is 6 directed rows, 3
  relationships. The 80% target is met as a point estimate, but the Wilson
  lower bound is 61%. Closed-duplicate evidence is 4 rows.
- **In-sample.** The bars and fixes were chosen against these labels. Three
  choices reduce overfitting:
  - the fixes are generic tokenizer and number rules, not per-task rules;
  - only one bar moved;
  - that bar was chosen from the firing target, not from usefulness.

  It remains calibration evidence, not validation.
- **Firing is a census proxy.** Queries are existing open task titles,
  including `#gtd` checklist rows and reading-task wikilinks that real
  captures do not create. References are captured as URLs, whose `ref` mode
  does not qualify. The capture-like subset fires at 10.0%.
- **Closed rows.** Duplicate precision is 2/4; the other two closed rows are
  useful related work, and no closed row is noise.
  - The plan sets no separate closed target, and closed rows show
    "Done/Canceled N d ago" with `open` as the default, not a
    "Possible duplicate" mark.
  - A closed bar above 0.82 would reach 2/2, but on the strength of one pair
    (2). It was not adopted; re-check when more closed pairs accumulate.
- **Same title is literal by contract.** The only observed same-title rows (one
  relationship) are cross-product, and both are U. The plan-selected
  `discard` default for `same_title` (`duplicate_default = split`) is a
  product decision that this data neither establishes nor overturns. It was
  not changed here.
- **Abbreviations.** The CT appointment duplicates rank only `similar`,
  because `appt` ≠ `appointment`. No abbreviation table was added; that would
  be vocabulary-specific.
- **Hold rows.** At the final bars, 79 hold rows are unlabeled. They render
  only to keep an already-visible row steady while the user types.

## Mac release timing

### Calibrated build (measured 2026-10-21 17:30 UTC)

Measured on Kellys-MBP (arm64, macOS 26.5, rustc 1.95.0).

- **Source.** A disposable rsync of the calibrated working tree on top of
  `5d212ef9`; hashes of the engine files are in the evidence and match the
  verified tree.
- **Build and method.** `cargo build --locked --release --bin bob`, then one
  warmup per draft and 30 alternating launches against `~/bob`, timed with
  `perf_counter_ns`.

| Draft | Runs | Median | p95 | Nearest-rank p95 | Maximum |
| --- | ---: | ---: | ---: | ---: | ---: |
| Qualifying: `Install new UPS battery @dev` | 30 | 41.436 ms | 43.494 ms | 43.844 ms | 44.030 ms |
| Non-creating: `Remember a thought @dev#Ideas` | 30 | 5.972 ms | 6.343 ms | 6.343 ms | 6.716 ms |

- **Gate.** The warmed qualifying p95 passes the 50 ms gate with 6.5 ms of
  headroom, so no index escalation is needed.
- **Cold first launch.** The first qualifying warmup was 1030.942 ms (968 ms
  for the previous fresh binary). Its cause was not isolated, and these
  numbers do not describe cold-start latency.
- **Safety checks.** The installed `~/.cargo/bin/bob` checksum
  (`c2c7fb22…`) was unchanged, vault status was unchanged, and the scratch
  directory was removed.
- **Evidence.** `calibration_mac_timing_final.json`.

### Starting bars (measured 2026-10-21 11:16 UTC)

Same Mac and method, at base revision `5d212ef9`:

| Draft | Median | p95 |
| --- | ---: | ---: |
| Qualifying | 40.700 ms | 46.881 ms (nearest-rank 47.642) |
| Non-creating | 6.461 ms | 7.547 ms |

The first warmup was 968.373 ms. Evidence is in `calibration_mac_timing.json`
and `file:explicit:416e5e7515b42bf9c399706f`.

## Apollo timing

- **Baseline vs final A/B.** Interleaved release builds ran on the snapshot
  while apollo carried a load average of about 5–7 from concurrent agents.
  With 60 runs the qualifying medians were 87.252 ms vs 87.518 ms, a 0.3%
  difference within noise. The p95 values were 96.0 ms vs 98.2 ms. The
  non-creating median fell from 4.45 ms to 4.04 ms.
- **Stopword lookup.** It uses a binary search over the sorted list, so the
  longer list adds no linear scan cost.
- **Sampler timings with the final build:**
  - qualifying: median 85.6 ms, p95 90.2 ms;
  - non-creating: median 3.4 ms, p95 4.4 ms.
- **Pre-calibration census (11:51 UTC):**
  - qualifying: median 86.406 ms, p95 90.935 ms;
  - non-creating: median 3.361 ms, p95 4.412 ms.
- Apollo is not the acceptance host.

## Recovery and sampling history

- **Recovery.** The previous phase left the sampler in a stash and the report
  and worksheet only in artifacts. They were recovered on 2026-10-21.
- **Legacy worksheet.** It held 100 rows but only 54 directed matches; 46 rows
  had no candidate, and all labels were empty.
- **Self-match fix.** The original sampler dropped self-matches after ranking,
  so an open self-match could suppress closed duplicates. The query-only
  `--exclude NOTE:LINE` option now removes the source task before scoring,
  band suppression and limits, and it is rejected in draft mode.
- **Legacy census** (502 queries, before the fix): visible firing 28/502
  (5.6%), with a closed count biased by self-suppression.

## Verification

All gates ran on the final source tree on apollo, 2026-10-21 17:35–17:39 UTC:

- `just docs-gen`, which produced no new changes;
- `just check`: fmt, clippy (project gate), and 5268 tests with 0 failures;
- `just check-scripts`, including `capture-related-calibrate-test: PASS`;
- `just docs-check`: 447 passed and 1 skipped (optional font dependency);
- `git diff --check`.

After those gates, the `docs/capture.md` paragraph was re-wrapped (line breaks
only). `just docs-check` (447 passed, 1 skipped) and `git diff --check` were
rerun on that final text and passed.

New unit tests cover:

- the number guard: `Part 2` vs `Part 3` or unnumbered stays `similar`, an
  unchanged control stays `possible_duplicate`, and a closed `2025` vs `2026`
  is suppressed;
- the stopword and digit tokenizer cases;
- the sorted stopword list.

The draft-mode CLI goldens needed no regeneration and pass.

## Evidence artifacts

All refs are immutable snapshots. Read them with
`sase artifact read <ref> "<reason>"`.

| Evidence | Artifact ref |
| --- | --- |
| Reviewed labels and disagreements | `file:explicit:c7de83cce58aab48e84b27a1` |
| Reviewed labels CSV (80 + 9) | `file:explicit:773fbd5a6f26c5e990c6244a` |
| Reviewed labels provenance, rubric and rows | `file:explicit:cae01b758b77d83f13c2447f` |
| Final metrics, sensitivity, sweep and source hashes | `file:explicit:c36bed37d6fb0b0a1ed456ef` |
| Final-bar census responses (snapshot) | `file:explicit:4ebbd4fa39c14343fda9e074` |
| Final-bar census summary (snapshot and live) | `file:explicit:c3194fcc4b012e5042c08bb7` |
| Mac timing, calibrated build | `file:explicit:b665608a7bbb39d1288d4bba` |
| Apollo baseline-vs-final timing | `file:explicit:af6e954e2f62720ca77cbde4` |
| Evaluation snapshot provenance | `file:explicit:589a2593eaf30db51eef6070` |
| First-pass judgments | `file:explicit:b27592e2a9e2fdfe6a2165a2` |
| First-pass CSV | `file:explicit:ef1d9faf9c1efce6c084ba23` |
| First-pass provenance | `file:explicit:3909e4a260d0f8aea117a8bc` |
| First-pass analysis | `file:explicit:78fd69bc548396bd7b4bd609` |
| Score-free numbered review | `file:explicit:bd9fe71a265c714e4f41578a` |
| Blank 80-pair worksheet | `file:explicit:965954f61a5d725b7827ed11` |
| Starting-bar census | `file:explicit:c9ad49e5fc63d54df5ba9edd` |
| Starting-bar responses (496) | `file:explicit:12ffdbf73c4f258517bdb94e` |
| Starting-bar source/vault provenance | `file:explicit:c3dc974fd1d48bc1e11616d6` |
| Apollo samples (starting bars) | `file:explicit:fa6366e2980b3ab54566205d` |
| 496-task catalog | `file:explicit:0d0e7d862e34b52c1cc6a527` |
| Mac timing (starting bars) | `file:explicit:416e5e7515b42bf9c399706f` |
