# Similar Tasks in Bob Mac Capture's Preview — Design Research (cld)

> **Research query:** Show likely related tasks in Bob Mac Capture's preview panel when
> the draft will create one or more new tasks. The aim is to warn about duplicates and
> point out tasks worth linking. Constraints, in priority order: the app must stay
> blazing fast; the panel must not get cramped or need frequent scrolling; the feature
> must be intuitive, reliable, and beautiful. Critique the idea, call out any requirement
> changes, and end with a recommended solution.

![Mockup of the proposed Similar tasks band in four states: settled, focused row with action strip, after a relate action, and a bulk draft](capture_similar_tasks_preview__cld_mockup.png)

*The mockup is an approximate HTML render, not SwiftUI. Colours and glyphs follow
`CaptureEditorPalette`, and SF Symbols are drawn by hand.*

## Bottom line

- **Build it, but promise "similar", not "related".** I replayed 1,490 real captures
  (Jul 20 – Oct 20) against the vault as it stood when each was captured.
  - **Duplicates and near-duplicates are common and easy to catch.** At the recommended
    threshold, about **1 in 5 new-task captures** gets a suggestion, and about **88%** of
    the suggestions I hand-labelled were genuinely useful.
  - **Workflow relations are invisible to wording.** Across the vault's 95 real
    dependency links, the actual prerequisite ranked in the top 5 only **~20%** of the
    time. Prerequisites are usually worded nothing like their dependents.
  - So the feature can reliably say "you may already have this". It cannot reliably say
    "this depends on that".
    See [Evidence](#evidence).
- **Performance: no new per-keystroke subprocess.** The design rejects running bob per
  keystroke:
  - bob builds a small similarity index of about 1,400 tasks (open tasks plus tasks
    closed in the last 30 days). The app holds it in memory and refreshes it the same
    way it refreshes the idle agenda (stale-while-revalidate on filtered vault events).
  - The draft's query terms ride along on the `capture-parse` call the app already makes
    for every keystroke (about 6 ms today).
  - Ranking is a sparse dot product over about 1,400 short documents. It runs in tens of
    microseconds in the app, so similar tasks can render **before** the dry-run preview
    returns.
  - bob still owns every judgement of meaning: which tasks are eligible, tokenization,
    term weights, and thresholds. The app owns arithmetic, timing, and pixels.
    See [Architecture](#architecture--where-the-work-happens).
- **Bob's vocabulary matters more than the algorithm.**
  - About 20% of tasks contain code spans or keymaps, such as `` `@` `` or
    `<ctrl+shift+m>`. A generic tokenizer discards these and produces confident false
    duplicates, for example "Add support for new `@` syntax" ≈ "Add support for `:`
    syntax".
  - Treating code spans and keymaps as atomic terms raised ranking quality (AUC) from
    **0.71 to 0.82–0.84** on my labelled pairs.
  - Character trigrams added almost nothing (AUC 0.84). Semantic embeddings are not
    justified for v1.
- **Space: show nothing unless something clears the threshold.**
  - Matches appear as a one-line-per-task band at the foot of the new task's preview
    card, capped at 3 rows (1 per item in a bulk draft).
  - When the band fires it is 1 row about two-thirds of the time. A 3-row band costs
    about 90 pt; the common 1-row band costs about 42 pt.
  - On the ~79% of captures with no match, it costs zero pixels.
- **Calm: no flicker.**
  - Updating rows on every keystroke flickers. In a word-by-word typing simulation, 33–51%
    of captures briefly showed a suggestion that later vanished.
  - Rows therefore appear only when typing **settles** (about 400 ms idle). Hysteresis
    keeps a row on screen while you keep typing, and short queries need a higher score.
  - With these rules, transient suggestions drop to about 14%, and a real match still
    appears by about two-thirds of the way through typing the title.
- **Act with one keystroke, without reaching for the mouse, and nothing is written early.**
  - ⌘1–⌘3 focuses a row and opens an action strip whose keys are the capture sigils
    themselves: `~` relate, `&` needs it, `*` blocks it, `@` do it now, `!` mark it done,
    `/` open. `⌫` drops your item and keeps the existing task.
  - Every action is a **draft edit**, and bob's ordinary preview explains the result
    before Return writes anything.
  - The one write before Return is minting a block ID on a target that lacks one, which
    the `~`/`&` pickers already do.
  - Return never changes meaning and is never blocked by a match.

## Is this a good idea? (critique)

### What is right about it

1. **The duplicate problem is real and measurable.**
   - In the replay, 6% of new tasks had a near-identical open or recently closed task
     (score ≥ 0.75).
   - Many of these are exact restatements: "Install UPS battery!" was captured while the
     open task "Install new UPS battery!" already existed, and "Clear all open sase task
     beads!" duplicated "Close all open task beads!".
   - Others contradict an earlier decision: "Rename xprompts to macros!" followed an
     earlier "Rename "xprompts" to "hash-prompts"?".
   - The capture panel is the cheapest place to catch these, before a duplicate costs a
     triage decision in the NEW tier of the `]s` walk.
2. **It is the missing on-ramp for task relations.** `~` / `~~` relations just shipped
   (`bob-mac-capture` a85b1f8, bb7127a), and the vault has **zero** 🪢 LINKS lines today.
   A relation is easiest to make at capture time, while the related task is in front of
   you.
3. **It fits the architecture.** It mirrors a pattern that has already shipped and been
   accepted:
   - **The idle agenda:** bob-owned facts in an in-memory, stale-while-revalidate cache,
     with an app-owned fit (see `decisions:idle-capture-shows-ledger-agenda`).
   - **Successor offers:** suggestions are only *offered* and never acted on implicitly
     (see `decisions:unblocked-tasks-are-offered`).

### What is wrong or risky as stated

1. **"Likely related" over-promises.** On real dependency pairs, lexical similarity puts
   the true prerequisite in the top 5 only 19–22% of the time, under every tokenizer
   variant. Embeddings would not fix this (the qmd research below shows why).
   "Related" in the dependency sense mostly means "same note": 65% of prerequisites live
   in the dependent's own note. If the UI calls these rows "related", users will expect
   prerequisites and be disappointed. Call them **similar**, and add a separate
   **Likely duplicate** label for high-confidence matches.
2. **The naive implementation would hurt the thing Bryan cares most about.**
   - Matching inside bob per keystroke means walking the vault. The existing vault-wide
     task catalog (`capture-complete` for `&`) takes **353–363 ms** and returns 1.6 MB.
   - Today's per-keystroke `capture-parse` takes about 6 ms and `capture --dry-run` about
     12 ms.
   - A fourth spawn per keystroke, or a 30× slower preview, is unacceptable.
3. **A live list that changes on every keystroke is noise.** One-word prefixes match
   almost anything ("Launch …" matches "Launch epic!"). The typing simulation shows that
   without settling and hysteresis, half of all captures would flash a wrong suggestion.
4. **Low-precision suggestions train the user to ignore them.** A 0.35 threshold fires on
   about half of all captures at roughly 40% precision. That level of noise teaches the
   user to ignore the band, and the occasional true duplicate gets ignored with it.
5. **The panel is already dense.** `docs/capture-previews.md` describes close cards,
   start cards, budget meters, destination rows, relation rows, and successor offers. A
   new band must earn its pixels and must vanish when it has nothing to say.

### Would I take a different approach?

I would keep the push model (shown automatically while capturing), but with four
changes:

1. Rename the promise from "related" to "similar", with a separate duplicate tier.
2. Move matching out of the per-keystroke bob spawn and into an in-app ranker over a
   bob-built index.
3. Gate rows on settled typing.
4. Make every action a draft edit.

I considered three alternatives:

- **A pull gesture** (press a key to ask "anything similar?"): rejected as the primary
  mode, because people don't ask about duplicates they don't suspect.
- **Triage-time detection only** (a "Possible duplicate" chip in the NEW tier of the
  `]s` walk): a good *complement*. It catches drafts submitted before the band settled.
  But it acts after the duplicate already exists.
- **A post-capture notification:** too late, and too easy to swipe away.

## Requirement adjustments (explicitly called out)

| # | Original | Adjusted | Why |
|---|---|---|---|
| **R1** | "Likely related tasks" | **Similar tasks**, with a **Likely duplicate** label on high-confidence open matches | Wording finds duplicates and topic neighbours, not prerequisites (R@5 ≈ 0.20 on 95 real dependency pairs). |
| **R2** | (implicit) open tasks only | Also search tasks **closed in the last 30 days**. Show them dimmed ("done 8d ago"), never label them duplicates, and show at most one when open matches exist | Half of all matches are recently closed tasks: you did this already, or you cancelled it. |
| **R3** | Show related tasks whenever a new task is created | Show the band **only when a match clears bob's threshold**: no header, no placeholder, no "no matches" row | Keeps the README's "no dead space" principle. About 79% of captures show nothing. |
| **R4** | (implicit) live updates | **Settle on pause** (about 400 ms idle) with **hysteresis** and a stricter threshold for short queries | Updating on every keystroke flashes wrong suggestions in 33–51% of captures. |
| **R5** | "Blazing fast" | Hard rules: **no new subprocess per keystroke**; ranking ≤ 1 ms p99 on the main actor; the index refreshes in the background on its own lane; the preview and submit lanes never wait on it | Puts the speed requirement into numbers that can be enforced. |
| **R6** | (not specified) | Actions are **draft edits only**. Return is never blocked or re-confirmed by a match | Keeps capture frictionless and lets bob's normal preview explain consequences. A false-positive "are you sure?" would be intolerable. |
| **R7** | (not specified) | Skip `@@template:` drafts, items with fewer than 2 meaningful terms, and items that do not create a task. In bulk drafts, show at most **1 row per item** | Template rows repeat on purpose. Very short titles match noise. Bulk drafts must not balloon. |
| **R8** | (not specified) | A Settings toggle, on by default. Thresholds live in **bob's** output, never as app constants | Lets thresholds be retuned with a bob release, without an app release. |
| **R9** | (not specified) | A new `decisions` record that refines the thin-client split for ranking | The app will rank over a bob-built index. That is allowed ("may filter or rank what bob returned") but should be stated explicitly. |
| **R10** | (not specified) | Ship an **evaluation harness** (`bob capture-related --query`) plus a fresh labelled set before fixing thresholds | My precision numbers come from one labeller and 80 pairs. They are directional. |

## Evidence

All measurements were taken on apollo (16 vCPU Xeon, Linux) against the live vault at
HEAD `487f0509` (2026-10-20). **The Mac was offline**, so no macOS numbers exist. The
idle-agenda research already flagged that the Mac's spawn cost has never been measured.

### Facts from the code

| Fact | Source | Consequence |
|---|---|---|
| Every keystroke waits a 50 ms debounce, then runs `capture-parse` (lane `parse`), then `capture --dry-run --no-clip` (lane `preview`). Each lane kills its predecessor, and results are generation-checked. | `CapturePanelModel.swift:830` (`debounceNanoseconds = 50_000_000`), `scheduleAnalysis` ~8287–8462; `BobProcessClient.swift` lanes | The ranker can run on the parse result, which is the earliest per-keystroke data available. |
| `capture-parse` is vault-free and already reports each item's `mode` (`task`, `pomodoro_task`, `project_note`, …) and clean `body`. | `src/native/capture_parse.rs`, `docs/capture.md` ("Clean title") | Bob already knows which items create tasks and what their titles are, so the app needs no new grammar. |
| There is no vault-wide open-task index in the app. Pickers fetch candidates when they open and rank them in Swift (`FuzzyMatcher`, an fzf-style AND-subsequence matcher). | `DependencyPickerPresentation.swift:75–95`, `FuzzyMatcher.swift:78–95` | There is precedent for Swift ranking what bob returned. The picker matcher is the wrong tool for similarity, because it requires every term to match. |
| The idle agenda store is the model for caching: one lane, refreshed at launch, on filtered `.md` events, on show (stale-while-revalidate), after submit, on wake and unlock; byte-identical output publishes nothing. | `CaptureAgendaStore.swift:111–167`, `CaptureAgendaRefreshFilter.swift` | Reuse the same pattern, and the filter itself, for the similarity index. |
| The agenda shows only when the draft is blank, so it never competes with the preview. | `CaptureAgendaVisibility.swift` | The similar-tasks band lives only in the preview. |
| Preview rows are display-only today. The only actionable precedent is the successor-offer card (Space marks an offer, Return opens the card). ⌘-digits are not routed by `CaptureKeyCommandRouter`. | `CaptureKeyCommandRouter.swift:150–349` | ⌘1–⌘9 is free. Launchers such as Alfred use it for "act on result N". |
| bob-cli has no similarity code: no BM25, trigram, or embedding crates. Its matchers are prefix/substring tiers (`capture_link_tasks::match_score`) and a bounded Levenshtein used for "did you mean". | `Cargo.toml`, `src/native/capture_link_tasks.rs:289–381`, `note_tasks.rs:429` | New code is needed, but it is small: a tokenizer plus TF-IDF. |
| There is no duplicate-title detection anywhere. Capture dedupes only block IDs and reference URLs. | `capture/batch.rs:192`, `capture/plan.rs:220–260` | This would be the first duplicate check for tasks. |

### Latency measurements (apollo, three runs each)

| Command | Time | Output |
|---|---:|---|
| `bob capture-parse -f json -- 'Fix flaky gkeep test @sase'` | 6 ms | — |
| `bob capture --dry-run --no-clip -f json -- 'Fix flaky gkeep test'` | 12–13 ms | — |
| `bob capture-complete --all-tasks --cursor 1 -f json -- ':'` (root routable notes, open tasks) | 39–40 ms | 498 rows, 225 KB |
| `bob capture-complete --all-tasks --cursor 1 -f json -- '&'` (whole vault, open and closed) | 353–363 ms | 3,900 rows, 1.6 MB |

### Corpus census

- **3,900 `#task` lines** in total:
  - 2,852 done and 549 canceled;
  - **499 open**: 58 Todo, 8 Next, 11 In Progress and 422 Blocked (most of them blocked
    by their project's `^prj` line).
- **All 499 open tasks live in root-level notes.**
- **888 tasks were closed in the last 30 days.** 644 of them are archived in `done/`, 155
  are in root notes, 56 in `ref/` and 33 in daily notes.
- Open task titles have a median length of 51 characters (p90 81).
- **214 of the 499 open tasks (43%) have a block ID.** Actions on the other 57% must mint
  one, which the pickers already do through `capture-task-id`.
- Root notes total 1.9 MB and `done/` totals 0.5 MB. An index limited to routable notes
  plus `done/` files modified within the window therefore reads about 2.4 MB, not the
  whole 13.7 MB vault. I estimate it costs **about 40–70 ms**, with the 40 ms `:` catalog
  as the closest measured proxy.

### Experiment A — Can wording find prerequisites? (No)

**Method.** I took 95 dependency pairs from Depends-On lines (dependent → prerequisite).
For each one, I ranked the prerequisite among the tasks that existed when the dependent
was created, using the dependent's title as the query.

| Variant | R@1 | R@3 | R@5 | MRR |
|---|---:|---:|---:|---:|
| Words, no stemming | 0.04 | 0.16 | 0.19 | 0.12 |
| Words, light stemming | 0.07 | 0.17 | 0.20 | 0.14 |
| Character trigrams | 0.07 | 0.18 | 0.22 | 0.14 |
| Words + trigrams | 0.06 | 0.17 | 0.18 | 0.13 |

**Same note: 62/95 (65%) of prerequisites live in the dependent's own note.**

Typical pairs show why wording fails:

- "Get access to all of your money!" depends on "Did enrolling for unemployment work!".
- "Start releasing bob-cli to crates.io!" depends on "Switch to using diataxis method
  for bob docs!".

Dependencies are workflow knowledge. The UI must not imply that it finds them.

### Experiment B — Replay: how often would it fire?

**Method.**
- **Captures replayed:** every task created between Jul 20 and Oct 20, 1,490 in all. I
  excluded daily-note `^gtd` rows and `#ref` tasks.
- **Corpus:** tasks open at the time of capture (median 404) plus tasks closed in the
  previous 30 days (median 349).
- **Scoring:** TF-IDF cosine with sublinear term frequency, smoothed IDF, light stemming,
  and code spans and keymaps as atomic terms ("words+atoms").

| Threshold | Any match | Open match | Recently closed match |
|---:|---:|---:|---:|
| 0.40 | 35% | 22% | 20% |
| 0.45 | 27% | 16% | 15% |
| **0.50** | **21%** | **12%** | **12%** |
| 0.55 | 15% | 9% | 8% |
| 0.65 | 9% | 5% | 4% |
| 0.75 | 6% | 3% | 2% |

**Rows per firing capture at 0.50** (309 captures fired):

| Rows | Captures | Share |
|---:|---:|---:|
| 1 | 205 | 66% |
| 2 | 52 | 17% |
| 3 or more | 52 | 17% |

A cap of 3 rows plus an overflow chip covers every case.

### Experiment C — How good are the matches? (labelled sample)

**Method.**
- I drew 80 top-1 pairs, stratified across four score bands of the first scorer.
- I labelled each pair myself as *useful* (a duplicate, or related enough that I'd want
  the heads-up) or *noise*: 47 useful, 33 noise.

**Precision of the first scorer, by band:**

| Score band | Useful |
|---|---:|
| ≥ 0.70 | 15/20 |
| 0.55–0.70 | 14/20 |
| 0.45–0.55 | 10/20 |
| 0.35–0.45 | 8/20 |

**Most false positives at the top came from Bob's vocabulary.** Code spans and keymaps
had been stripped to nothing:

- "Add support for new `@` syntax" ≈ "Add support for `:` syntax" (0.86)
- "Make `,E` keymap a short-hand for `,UE`" ≈ "Make `@:` a short-hand for `:?`" (0.70)
- "Add `<ctrl+shift+b>` keymap" ≈ "Add `<ctrl+shift+p>` keymap task card" (0.70)

**Re-scoring the same 80 pairs:**

| Scorer | AUC | Useful at ≥ 0.45 | ≥ 0.50 | ≥ 0.55 | ≥ 0.65 |
|---|---:|---:|---:|---:|---:|
| First scorer: generic words + 35% trigram blend | 0.71 | 39/60 | — | 29/40 | 16/21 |
| **Words + atoms** (code spans and keymaps kept whole, double weight) | **0.82** | 31/38 | **29/33 (88%)** | 26/28 | **21/22 (95%)** |
| Words + atoms + 35% trigram blend | 0.84 | 33/40 | 29/32 | 28/29 | 15/16 |
| Trigrams only | 0.72 | 36/51 | 30/43 | 23/32 | 18/21 |

**Caveats.**
- There is one labeller, and only 80 pairs.
- The atoms fix was designed *after* seeing these false positives, so these numbers
  flatter it.
- The sample is stratified toward high scores.

Treat these as direction, not calibration: Bob's vocabulary must be tokenized as Bob
vocabulary, trigrams add little, and 0.50 / 0.70 are sensible starting thresholds. That
is why R10 asks for a fresh labelled set before shipping.

### Experiment D — Typing simulation: does a live list flicker?

**Method.**
- For each replayed capture, I re-ranked after every completed word, as if the user
  paused after each one. This is the worst case.
- A suggestion counts as *transient* if it appeared at some point but was not the final
  answer.
- These runs used the earlier blended scorer at 0.45. The shape of the results carries
  over to the recommended scorer, but the exact numbers may not.

| Policy | Captures with a transient suggestion | Top-row changes per capture | Final match first visible at |
|---|---:|---:|---:|
| Re-rank every word, no minimum | 51% | 1.13 | 67% of words |
| At least 2 terms | 33% | 1.00 | 77% |
| At least 3 terms | 18% | 0.59 | 83% |
| **At least 2 terms, +0.15 needed below 3 terms, keep a shown row while ≥ threshold − 0.10** | **14%** | **0.54** | **67%** |

Real typing does not pause after every word, so a 400 ms settle gate removes most
intermediate states on top of these numbers. The last row is the policy recommended
here.

### External precedent

- GitHub Issues (public preview, 2026-06-18) flags potential duplicates *while the issue
  form is being filled in*, inline, with **up to three suggestions**. It does not block
  creation: "review the suggested issues or continue creating your issue". (GitHub
  changelog, "Duplicate detection and issue fields MCP support for GitHub Issues".)
- A third-party Linear duplicate check (HackerOne's integration) matches on title
  keywords and links only above a confidence threshold (75% by default). That is a
  confidence-gated, non-blocking pattern like this one.
- Apple's on-device `NLEmbedding` has a mixed reputation for short-text retrieval. One
  practitioner write-up found that relevant and irrelevant scores clustered at 0.50–0.60,
  and a plain string match won. Combined with the prior qmd research, which found every
  method missed Bob jargon and lexical search matched hybrid on 9/10 questions, there is
  no case for embeddings in v1.

## Architecture — where the work happens

| Option | Per-keystroke cost | Who owns meaning | Verdict |
|---|---|---|---|
| **A. bob builds an index; the app holds it and ranks; query terms ride on `capture-parse`** | **~0 extra** (terms are microseconds inside an existing 6 ms spawn; ranking takes tens of µs) | bob: eligibility, tokens, weights, thresholds. App: dot product, timing, pixels | **Recommended** |
| B. bob coprocess (`--stdio`) holding the index and answering queries | ~1 ms of inter-process communication | bob, entirely | Escape hatch if A's ranking mirror ever drifts. It would be bob's first long-lived process, with its own lifecycle, versioning and invalidation. `decisions:mac-capture-is-a-thin-client` calls a daemon premature. |
| C. A new bob call per keystroke, backed by an on-disk index validated with `stat` | +15–40 ms and a fourth spawn | bob | Rejected. It creates a second derived cache to keep in sync (the qmd research flagged this) and makes every preview slower. |
| D. A new bob call per keystroke with a full walk | +350 ms | bob | Rejected. |
| E. Swift tokenizes `capture-complete &` output (no bob change) | ~0 | **Swift** | Prototype only. It is a 1.6 MB, 360 ms refresh, it duplicates tokenization, and it has no closed-date field. |
| F. Embeddings (Apple `NLContextualEmbedding`, or a local model behind bob) | ms per query plus model load | Swift or a model | Deferred. No evidence it helps on Bob's jargon. Revisit only as a re-ranker of a lexical shortlist if the harness shows recall gaps. |

Option A satisfies `decisions:mac-capture-is-a-thin-client`, which says the app "may
filter or rank what `bob` returned, but it never decides syntax itself". Bob decides
which tasks are candidates, what the terms are, how they are weighted, and what score
counts as a match. The app multiplies numbers bob gave it, and decides when and how to
draw. To keep the two rankers from drifting, bob's own `--query` path and the Swift
ranker must agree on shared fixtures.

## Recommended design

### 1. What gets a band

The band appears for an item only when all of these hold:

- The item's `capture-parse` mode creates a task: `task`, `pomodoro_task`, or the `^prj`
  title of `project_note` / `pomodoro_project_note`.
- The draft is not an `@@template:` draft.
- The item has at least `min_terms` (2) meaningful terms.
- At least one candidate clears the threshold.

Candidates already referenced by the draft (its `&`, `*`, `~`, `@route:id`, or
`+id` targets) are excluded. A row that was already visible instead switches to a
**linked** state, as in mockup panel ③.

### 2. Matching (owned by bob)

- **Eligibility.**
  - **Open:** every open `#task` in routable notes. This includes Blocked tasks, `#ref`
    reading tasks, and `^prj` lines, each marked with its kind.
  - **Recently closed:** completed or cancelled in the last `--days` days (default 30),
    from routable notes and from `done/` files modified within that window.
  - **Excluded:** daily-note `^gtd` rows, and closed instances of recurring tasks.
    Recurring chores such as "Pay kelly salary!" are duplicates by design.
- **Tokenizer.** Bob's vocabulary is a first-class concern:
  - lowercase, split camelCase and snake_case, light stemming (‑s, ‑es, ‑ies, ‑ed, ‑ing);
  - a stopword list; wikilinks reduced to their display alias;
  - inline fields, `#task`, `^id` and the 💡 Keep link removed;
  - **code spans and `<key+chords>` kept as atomic terms with double weight**;
  - context tags (`#dad`, `@BUY`, `%abby`) kept as weak terms.
- **Score.** Cosine similarity of TF-IDF vectors, using sublinear tf (1 + ln tf) and
  idf = ln((N + 1)/(df + 0.5)).
- **Policy, emitted by bob.** Starting values:
  - `similar` 0.50
  - `duplicate` 0.70, applied to open candidates only
  - `short_query_terms` 3 and `short_query_boost` 0.10: queries with fewer than 3 terms
    need 0.60
  - `hysteresis` 0.10
  - `max_rows` 3, `bulk_max_rows` 1, `max_closed_rows_with_open` 1
- **Tie-breaks.** Open before closed; then In Progress, Next, Todo, Blocked; then most
  recent.

### 3. bob contract (additive, `capture-*` protocol)

The CLI rules say `capture-*` names are frozen siblings that only grow, and that no
subcommand may be added under `bob capture`. The new sibling is **`bob capture-related`**,
listed alphabetically in **Capture protocol** between `capture-pomodoros` and
`capture-rewrite`:

```text
Usage: bob capture-related [OPTIONS]

List the open and recently closed tasks a new capture may duplicate or relate to,
with Bob-normalized terms so a capture client can rank drafts as they are typed.
Read-only; never writes the vault.

Options:
  -b, --bob-dir <DIR>     Bob vault root; defaults to BOB_DIR or ~/bob
  -d, --days <N>          Include tasks closed in the last N days [default: 30]
  -f, --format <FORMAT>   human or json [default: human]
  -h, --help              Show help
  -l, --limit <N>         With --query, how many matches to show [default: 5]
  -q, --query <TEXT>      Rank the index against TEXT (as capture would) and print matches
```

`--query` is the evaluation harness, the parity oracle, and a useful command for agents
and humans in its own right. Its human output should be coloured: score bars,
"Likely duplicate" tags, and matched terms in bold.

JSON sketch (`schema_version: 1`):

```json
{
  "ok": true,
  "schema_version": 1,
  "as_of": "2026-10-20",
  "policy": {
    "similar": 0.50, "duplicate": 0.70, "hysteresis": 0.10,
    "min_terms": 2, "short_query_terms": 3, "short_query_boost": 0.10,
    "max_rows": 3, "bulk_max_rows": 1, "max_closed_rows_with_open": 1
  },
  "vocab": ["instal", "ups", "battery", "athena", "code:@", "key:ctrl+shift+m"],
  "idf": [3.9, 5.8, 5.1, 3.2, 6.4, 6.0],
  "unknown_idf": 7.6,
  "tasks": [{
    "ref": "12:ab12cd34", "note_path": "dev.md", "locator": "dev",
    "block_id": "ups-battery", "requires_block_id": false,
    "text": "Install new UPS battery",
    "kind": "task",
    "status_symbol": "?", "status_name": "Blocked", "status_type": "ON_HOLD",
    "closed": null, "scheduled": "2026-12-08",
    "terms": [[0, 1.0], [1, 1.0], [2, 1.0]],
    "term_ranges": [[0, 7], [12, 15], [16, 23]]
  }]
}
```

`kind` is `task`, `ref`, or `prj`. `terms` are [vocab index, weight] pairs.
`term_ranges` are the UTF-8 ranges in `text` that the app emboldens.

- **Size.** About 1,400 tasks at roughly 200–250 bytes each, so about 300 KB. The app
  decodes it off the main thread in a few milliseconds, and only when the bytes change.
- **Determinism.** No clock-dependent fields except `as_of`. The same vault bytes produce
  the same output, which is what lets the app skip identical results.
- **`capture-parse`** gains an additive per-item field for task-creating items:
  `"similarity": {"terms": [["instal",1.0],["ups",1.0],["battery",1.0]]}`. The same Rust
  tokenizer produces the corpus terms and the query terms, so the query side costs
  microseconds and stays vault-free.
- **Docs and tests (bob-cli):**
  - a `docs/capture.md` section;
  - help-text examples;
  - fixture-vault goldens for `--format json` and `--query`;
  - a performance gate: p95 ≤ 100 ms on athena for a fixture of about 1,500 tasks;
  - a tokenizer table test covering code spans, keymaps, wikilink aliases, and tags.

### 4. App side (bob-mac-capture)

- **`SimilarTasksStore`** (BobMacCapture): a copy of `CaptureAgendaStore`'s discipline.
  - Lane `related`, one refresh in flight plus at most one follow-up, byte-identical
    output skipped, last good index kept when a refresh fails.
  - **Triggers:**
    - launch, after the agenda prefetch;
    - filtered vault events, using the agenda's `.md` filter with a 1 s trailing
      coalesce, because Obsidian autosaves in bursts;
    - panel show (stale-while-revalidate);
    - after submit;
    - wake, unlock, and day change (the closed-task window moves);
    - Recheck Bob or a change to the bob executable.
  - An older bob with no `capture-related`, or no `similarity` in parse output, hides the
    feature silently. Missing fields are read with `decodeIfPresent`.
- **`SimilarTaskRanker`** (CaptureCore, pure):
  - precomputes document norms and postings at decode time;
  - per query, builds the vector from bob's terms × idf and walks the postings;
  - applies policy, exclusions, and tie-breaks, and returns ranked rows with their
    matched-term ranges;
  - is covered by table tests, plus **parity fixtures generated by
    `bob capture-related --query`** and checked into the test fixtures.
- **`SimilarTasksSettlePolicy`** (CaptureCore, pure state machine, tested with a fake
  clock):
  - It ranks on every parse result but **publishes** rows only:
    - after 400 ms with no edits;
    - immediately on show with a retained draft;
    - on the explicit Preview button.
  - Between settles, rows already on screen stay while they score at least
    threshold − hysteresis, and keep their order. No new rows enter.
  - An item that stops creating a task, for example because you turned it into
    `@route:id`, drops its band immediately.
  - The 400 ms timing belongs to the app, because it is UI timing.
- **The ranker never awaits anything.** Ranking finishes in tens of µs on the main actor
  when the parse result arrives, so it cannot delay the preview or submit lanes.

### 5. Visual design

See the mockup at the top.

- **Placement.** The band is a **footer band inside the item's own preview card**,
  separated by a hairline:
  - it belongs to the task it describes;
  - it appears below content that is already settled, so nothing above it jumps;
  - the panel simply grows downward from the fixed eye line, under the existing
    unanimated resize rule.
  - For bulk drafts, each item card gets its own band of at most one row, plus a "+N"
    capsule when more matches exist.
- **Header.** A `square.on.square` symbol and "SIMILAR TASKS" in caption weight in
  secondary colour, with a trailing tertiary hint "⌘1–3 to act". The hint becomes
  "← → choose · ↩ apply · esc back" while a row is focused.
- **Row** (24 pt, callout, one line):
  - a key-cap column (`⌘1`, caption monospaced, hairline-bordered);
  - the status glyph from `CaptureEditorPalette` (`pause.circle` for Blocked,
    `circle.lefthalf.filled` orange for In Progress, `circle.inset.filled` blue for
    Next, `circle` for Todo, `checkmark.circle` green for Done, `xmark.circle` for
    Canceled);
  - the title, with **matched words semibold** so the reason for the match is visible at
    a glance;
  - capsules;
  - a trailing locator (`dev · Blocked`, or `done 8d ago` for closed rows).
- **Capsules:**
  - **Likely duplicate:** orange at 0.18, a scheme the app already uses for warnings and
    overrides;
  - **scheduled date:** the existing green calendar capsule;
  - **linked:** mint, the relation colour, shown after you act.
- **Closed rows.** Secondary-coloured title, never struck through. Strikethrough reads as
  "deleted" and would compete with the close card's meaning.
- **Truncation.** The title truncates at the tail. At narrow widths the locator
  truncates first, then the title, the same rule the close card uses. Badges never wrap
  or shrink.
- **Light and dark** come from semantic colours only. With Increase Contrast, the focus
  fill rises from 0.16 to 0.30, matching the picker rows.

### 6. Interaction

| Key | When | Effect |
|---|---|---|
| ⌘1–⌘9 | Similar rows visible (numbered down the preview stack) | Focus that row and open its action strip. Press the same key again to unfocus. |
| ← → / Tab | A row is focused | Move along the action strip |
| ↑ ↓ / Ctrl‑P Ctrl‑N | A row is focused | Move focus between rows |
| ↩ | A row is focused | Apply the highlighted action. The default is **⌫ drop mine** for a likely duplicate and **~ relate** otherwise. |
| `⌫` | A row is focused | **Drop mine:** remove this item from the draft and keep the existing task. Undo restores it. |
| `@` | A row is focused | **Do it now:** replace the item with `@route:id`, which links the existing task into today's Pomodoro. The footer verb becomes **Link**. |
| `!` | A row is focused | **Mark it done:** replace the item with `!note:id`. The footer verb becomes **Complete**. |
| `~` | A row is focused | **Relate:** append ` ~note:id` to the item's parent line (an inert 🪢 LINKS relation). |
| `&` | A row is focused | **Needs it:** append ` &note:id`, so the new task depends on the existing one. |
| `*` | A row is focused | **Blocks it:** append ` *note:id`, so the existing task depends on the new one. |
| `/` | A row is focused | **Open:** go to the existing task in Obsidian through the existing `/` go-to path. The panel hides and the draft is retained. |
| esc | A row is focused | Unfocus and return to typing (Escape still closes the panel when nothing is focused) |
| any other key | A row is focused | Unfocus and pass the key to the editor |
| click | — | Clicking a row focuses it. Clicking an action applies it. Hovering shows the full title and the note path. |

**Why the sigils are the keys.** The keys you press are the characters you would have
typed, so the strip teaches the grammar instead of adding vocabulary. Each action reuses
the matching picker's insertion path. For an ID-less target, bob's `capture-task-id`
returns ready-made replacements (`relation_to_replacement`, `dependency_replacement`,
`blocked_task_replacement`, `complete_replacement`), exactly as when a picker row is
accepted. Because the result is a draft edit:

1. bob's dry-run preview shows the real consequence (the relation row, the **Link** or
   **Complete** footer verb, the dependency rows);
2. bob validates it, so a stale row such as a task closed seconds ago fails safely in
   preview rather than on write;
3. ⌘Z undoes it.

**Return is never intercepted** when no row is focused. A likely duplicate never adds a
confirmation step.

### 7. Space policy (no cramping, no scroll)

- **No match, no pixels.** That holds for about 79% of task captures.
- **One line per row.** A 1-row band is about 42 pt (hairline, header and row) and a
  3-row band about 90 pt. A typical single-task preview is about 70–90 pt, so the whole
  auxiliary region stays under 200 pt, far below the below-eye-line budget (467 pt on a
  13" screen with the Dock shown).
- **Bulk drafts get 1 row per item**, with "+N" capsules, and at most 9 numbered rows in
  total.
- The action strip is the only expansion, adding 18 pt. You trigger it yourself, so the
  layout change is expected.
- **If the auxiliary region would scroll**, for example a long clip preview plus a band,
  the band keeps its place at the foot of its card. The existing scroll safety net
  applies; nothing is reordered. Long single-item previews are rare (clip and authored
  children), and a band you have to scroll to see is better than reshuffling the cards.

### 8. Accessibility, settings, and failure states

- **VoiceOver.** When a band settles, announce once: "2 similar tasks; likely duplicate:
  Install new UPS battery, dev, Blocked". Each row's label includes its status, locator,
  and closed date. Actions are exposed as accessibility custom actions.
- **Settings.** "Show similar tasks while capturing" is on by default. There is no
  threshold slider; bob's policy owns the thresholds.
- **Stale index.** A task closed seconds ago may still show as open until the next
  refresh, about 2 s after the vault event. Because actions are draft edits,
  bob's preview catches the mismatch. A failed refresh keeps the last good index without
  showing an error, because the band is advisory. Diagnostics records the failure.
- **Signposts.** Add `related.rank`, `related.refresh`, and `related.decode`. This is
  also how the first real Mac numbers get measured.

### 9. Performance budget (to enforce in tests and signposts)

| Path | Budget | Expected |
|---|---|---|
| Keystroke: extra subprocesses | **0** | 0 |
| Keystroke: `capture-parse` slowdown from emitting terms | ≤ 0.5 ms | microseconds |
| Keystroke: ranking on the main actor (2,000-task index) | ≤ 1 ms p99 | tens of µs. A naive Python version over about 750 tasks took 3.8 ms p50, so compiled Swift over arrays should be well under 0.1 ms. |
| Show path | no new work | 0 (rows come from the last settled state) |
| Background: `capture-related` build | ≤ 100 ms p95 on athena (fixture gate) | about 40–70 ms (estimate) |
| Background: decode and postings build | ≤ 15 ms, off main | a few ms for about 300 KB |
| Memory | ≤ 5 MB | about 1–2 MB |

## Rollout plan

1. **bob-cli, measurement first.**
   - Implement the tokenizer and ranker behind `bob capture-related --query`.
   - Add a small labelling script that samples top matches from the vault's own history
     (a replay like Experiment B).
   - Bryan labels about 100 fresh pairs. Tune the tokenizer and the 0.50 / 0.70 policy
     on that set, not on mine.
2. **bob-cli, contract.**
   - Add the `capture-related --format json` index and the `capture-parse`
     `similarity` field, plus docs, goldens, and the performance gate.
   - Export parity fixtures (fixture corpus, queries, and expected ranked IDs and scores)
     for the app.
3. **bob-mac-capture.**
   - Build the store, the ranker with parity tests, the settle policy with fake-clock
     tests, the band view, ⌘-digit focus and the sigil actions (reusing picker insertion
     and `capture-task-id`), VoiceOver, the Settings toggle, and signposts.
   - Update `capture-previews.md`, `keyboard.md`, and `settings.md`.
   - Compile on the Mac per `AGENTS.md`, and measure the signposts there.
4. **Decision record.** Write
   `decisions:similar-tasks-are-ranked-in-app-over-a-bob-index`:
   - bob owns eligibility, tokens, weights, and thresholds;
   - the app owns the dot product, settle timing, and pixels;
   - actions are draft edits;
   - Return is never gated.
   The record is written through the memory-write process; I have not created it.
5. **Follow-ups**, each optional and small:
   - **Picker seeding:** when `~`, `&`, or `*` opens with an empty filter on a
     new-task item, order its candidates by similarity. This gives better defaults at
     zero pixel cost.
   - **Route hint:** when most similar open tasks live in one project note, offer
     "→ @sase_memory" for an unrouted capture.
   - **Triage complement:** a "Possible duplicate" chip on NEW-tier rows in bob-plugins'
     `]s` walk, fed by the same index, for drafts submitted before the band settled.

## Open questions for Bryan

1. **Recently closed tasks.** Are 30 days and "at most one closed row when open matches
   exist" right? They were half of all matches in the replay.
2. **Default for a likely duplicate.** Should ↩ default to **drop mine** (keep the
   existing task) or **do it now** (`@route:id`, link it into today)? I chose drop mine,
   because linking commits you to today.
3. **⌘1–⌘9.** The router does not use these today, and launchers such as Alfred use them
   for "act on result N". Any personal conflicts?
4. **Settle delay.** 400 ms is a starting point. Tune it on the Mac with signposts, by
   feel.
5. **Project and reference matches.** Should `^prj` and `#ref` matches be shown
   distinctly ("project", "reading") or filtered out? I would show them with their kind
   glyph. A project match is also the seed of the route hint.

## Recommended solution

Ship a **Similar tasks** band, not a "related tasks" panel:

1. **bob** gains `bob capture-related` (an additive `capture-*` sibling).
   - It emits a deterministic index of open tasks plus tasks closed in the last 30 days,
     with Bob-aware terms (code spans and keymaps kept whole) and TF-IDF weights.
   - It also emits a policy block: similar 0.50, duplicate 0.70, a stricter threshold for
     short queries, and hysteresis.
   - Its `--query` mode doubles as the evaluation harness and the parity oracle.
   - `capture-parse` adds each task-creating item's query terms.
2. **The app** holds the index in memory, refreshed exactly like the idle agenda, and
   ranks on each parse result.
   - It needs **no new subprocess per keystroke**, and ranking takes tens of
     microseconds.
   - Rows **publish only when typing settles**, with hysteresis, so nothing flickers.
3. **The band** sits at the foot of the new task's preview card.
   - It renders nothing when there is no match. Otherwise it shows 1–3 one-line rows (1
     per item in bulk drafts) with status glyphs, the words that matched in bold, a
     **Likely duplicate** capsule on strong open matches, and dimmed "done Nd ago" rows
     for recent closures.
4. **⌘1–⌘3** focuses a row. The capture sigils act on it (`⌫ @ ! ~ & * /`) as **draft
   edits only**, so bob's own preview explains the result before Return writes anything.
   Return is never blocked.
5. **Calibrate first.** Build the harness and a fresh labelled set before fixing
   thresholds. Write the decision record that refines the thin-client split. Measure on
   the Mac with signposts.

**Expected outcome.**

- About 1 in 5 task captures gets a quiet, mostly correct heads-up.
- Exact duplicates get a clear warning.
- `~` relations get their first natural on-ramp.
- Typing speed, preview latency, and the panel's calm, compact look are unchanged.

---

### Appendix — Methodology notes

- **Corpus parser.** An ad hoc, read-only Python parse of `- [s] … #task …` lines across
  the vault. It skipped `.git`, `.obsidian`, `_conflicts`, `_generated`, `_templates`,
  `lib`, and other excluded directories, and it reproduced bob's 3,900-task count
  exactly.
- **Cleaning.** I stripped inline fields, `^id`, `#task`, the 💡 Keep links, and Markdown
  links, and reduced wikilinks to their alias or basename. Code spans and `<chord>`
  keymaps were captured as atoms before tag stripping.
- **Replay corpus.** For a capture made on day *c*: tasks created before *c* (or with no
  `created` stamp) that were open at *c* (still open, or closed on or after *c*), plus
  tasks closed in [*c* − 30 d, *c*). Daily-note tasks are excluded on both sides.
- **Labels.** The labels are mine. "Useful" means a duplicate, or a relation I would
  plausibly want to know about at capture time. Sample: seed 11, 20 pairs per band.
- No vault files were written. Scripts and intermediate JSON stayed in `/tmp`.

### Sources

- GitHub changelog, 2026-06-18: [Duplicate detection and issue fields MCP support for GitHub Issues](https://github.blog/changelog/2026-06-18-duplicate-detection-and-issue-fields-mcp-support-for-github-issues)
- HackerOne docs: [Hai Linear integration](https://docs.hackerone.com/en/articles/14840521-hai-linear-integration)
- Practitioner report on Apple NLEmbedding for retrieval: [Why a simple string match beat Apple's NLEmbedding for local RAG](https://dev.to/turgaysavaci/why-a-simple-string-match-beat-apples-nlembedding-for-local-rag-1l4)
- Callstack: [On-device text embeddings with Apple's NLP framework](https://callstack.com/blog/on-device-ai-introducing-apple-embeddings-in-react-native)
- Prior Bob research:
  - `research:202610/qmd_agent_vault_search/qmd_agent_vault_search.md`: lexical vs hybrid
    search on the vault, the jargon misses, and the warning that a derived index is a
    second thing to keep in sync.
  - `research:202610/idle_capture_pomodoro_agenda/idle_capture_pomodoro_agenda.md`: the
    in-memory stale-while-revalidate store, the fixed eye line, and the below-eye-line
    budget.
- Memory: `decisions:mac-capture-is-a-thin-client`,
  `decisions:idle-capture-shows-ledger-agenda`, `decisions:unblocked-tasks-are-offered`,
  `glossary:task-relation`, `glossary:bulk-capture`, `glossary:capture`.
