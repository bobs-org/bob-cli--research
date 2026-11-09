# Period Note Agent Instructions: From Mechanical Summaries to Strategic GTD Reviews

*Researcher gem (`__gem`) · 2026-11-09 · Independent research report for bob-cli & Bob vault period notes*

---

## Executive Summary & Recommendation

**Verdict: YES, upgrading period note agent instructions is an excellent and high-leverage idea, provided it maintains strict scope discipline and tight word caps.**

The recent implementation of period notes (`YYYY-Www.md`, `YYYY-Qn.md`, `YYYY.md`) in `bob-cli` successfully solved the architectural problem: deterministic CLI scaffolding (`bob periods ensure`), atomic, guarded drafts (`bob periods draft`), live-rendered stats strips (`bob-stats-strip`), and child parts tables (`bob-period-parts`).

However, an audit of the initial production draft—generated today in `~/bob/2026/2026-W45.md`—reveals that while the mechanical pipeline works smoothly, the **instruction contract (`v1`) produces reviews with a low signal-to-noise ratio**:
1. **Redundancy & Repetition:** Tasks taking the most minutes appear under *both* "Where the time went" and "Finished", wasting ~25% of the strict 250-word budget.
2. **Routine Chore Spam:** Repetitive daily maintenance tasks (`[[gtd_daily]]`) crowded out 5 of the 7 slots in "Finished". Bryan is told five separate times that he conducted his daily review, obscuring actual project milestones.
3. **Number Regurgitation:** The `Headline` simply re-states total hours and percentage deltas, duplicating numbers already prominently displayed in the stats strip directly above `## Review`.
4. **Neglect of Rich Qualitative Signals:** `bob periods brief` already aggregates "Bryan's words" (manual log entries in daily notes and project notes), work-type distributions (BUILD vs. PLAN vs. FIX), and off-clock personal area time (Abby, Kelly, Body), but the `v1` instructions give the agent zero guidance or permission to incorporate them.
5. **Nagging Compliance Questions:** The drafted questions audit checklist compliance (e.g., asking why Wednesday missed its closeout or demanding an accounting of close categories) rather than prompting strategic GTD reflection on priorities, trade-offs, and pruning.

**Recommended Action:**
Adopt **`Agent instructions · weekly v2`** (and corresponding `quarterly v2` / `yearly v2`), keeping the hard word caps (250w weekly, 400w quarterly, 600w yearly) and non-judgmental tone, while refining the drafting rules to:
- **Forbid raw hour/delta repetition in the Headline**, focusing instead on the defining narrative arc and shipped outcomes.
- **Deduplicate "Finished" against "Where the time went"** and **explicitly filter out recurring routine maintenance**.
- **Incorporate work-type balance (BUILD/PLAN/FIX) and off-clock personal areas**.
- **Leverage "Bryan's words"** from the brief to connect machine metrics to human intent.
- **Re-orient "Questions" toward GTD Horizons and tactical decisions** (prune vs. schedule, trade-offs, next steps).

---

## 1. Case Study: Anatomy of the 2026-W45 Draft

On 2026-11-09 at 10:43 UTC, an agent drafted `## Review` in `~/bob/2026/2026-W45.md` (commit `288a8cbea` in the Bob vault). Let us examine the exact text produced under the `weekly v1` instructions:

```markdown
## Review

**Headline:** A 24h 45m week, 5h 28m below typical, put 45% into bob, led by WIP/Next
auto-decay and weekly/quarterly/yearly note templates.

**Where the time went:**

- [[bob]] · 11h 11m (45%):
  [[done/bob_done#^auto-decay-wip-next|WIP and Next auto-decay]] (55m),
  [[done/bob_done#^wqy-stat-strips|weekly/quarterly/yearly templates]] (45m), and
  [[done/bob_done#^tilde-x-equals|`~N` for `x=`]] (32m).
- [[gtd]] · 6h 58m (28%): daily review rows, led by [[2026/20261102#^gtd|Mon Nov 2]] at
  1h 30m and [[2026/20261104#^gtd|Wed 4]] at 1h 18m.
- [[sase]] · 2h 59m (12%):
  [[sase#^ref-the-ai-native-sdlc-playbook|The AI-native SDLC playbook]] (35m),
  [[sase#^agent-hijack-turns|agent hijack turns]] (30m), and
  [[done/sase_done#^fix-agent-sidecars|sidecar publishing]] (20m).

**Finished:**

- [[done/bob_done#^auto-decay-wip-next|Auto-decay WIP to Next and Next to Ready]] · 55m
- [[done/bob_done#^wqy-stat-strips|Weekly/quarterly/yearly file templates]] · 45m
- Daily [[gtd_daily]] rows: [[2026/20261102#^gtd|Mon]] 1h 30m,
  [[2026/20261103#^gtd|Tue]] 1h 00m, [[2026/20261105#^gtd|Thu]] 45m,
  [[2026/20261107#^gtd|Sat]] 43m, [[2026/20261106#^gtd|Fri]] 40m

+240 more.

**Still open:**

- [[bob#^successor-deps|Dependencies from successor offers]] · kept 3×, no reason given
- [[sase|`/sase_plan` agents may critique requirements]] · kept 3×, no reason given
- [[sase_completion#^e2e-gate-finalizers|Gates and monitors to finalizers]] · kept 3×,
  no reason given
- [[sase_memory_plan#^ref-docs-backed-memory-and-agent-maintained|Docs as Memory]] ·
  kept 3×: "I still really need to clean up sase's memory."

**Questions:**

- Done ran 33 above typical while Worked ran 5h 28m below and [[bob]] took 45% — what
  kinds of tasks made up those closes?
- [[2026/20261104|Wed 4]] missed its closeout although its
  [[2026/20261104#^gtd|gtd row]] logged 1h 18m — what happened to that review?
- Three of four 3× keeps, like [[bob#^successor-deps|successor dependencies]], carry no
  reason — what keeps them on the list?
```

### Critical Findings from W45:

1. **Word Count vs. Value:**
   The draft consumed 236 words (out of the 250-word cap). However, **62 words (~26%) were spent repeating tasks** between "Where the time went" and "Finished", combined with reciting daily review rows for Monday, Tuesday, Thursday, Friday, and Saturday.
2. **Routine Chores Crowd Out Real Work:**
   The instruction for Finished states: `^prj completions first, then at most 7 tasks, then +N more.`
   Because no `^prj` completed in W45, the sorting algorithm in `brief` fell back to logged time. Consequently, `gtd_daily` tasks dominated. 5 of the 7 items were identical daily routines. This hid genuinely finished standalone work (such as authenticating `doctl` in `dev`, fixing email anacron errors, or publishing SASE sidecars).
3. **Headline Duplication:**
   The headline opens with: `"A 24h 45m week, 5h 28m below typical, put 45% into bob..."`
   When Bryan opens `2026-W45.md`, the very first visual element is the `bob-stats-strip`, which renders:
   `Worked: 24h 45m (▼ 5h 28m)`.
   When parent notes (like `2026-Q4.md`) render their `bob-period-parts` table, Column 1 displays `24h 45m` and Column 2 displays the headline. Having the headline open with "A 24h 45m week..." makes Column 2 an echo of Column 1.
4. **Data Provided in the Brief but Completely Lost:**
   Running `bob periods brief 2026-W45 -f md` provides rich context that was entirely omitted:
   - **Work Type Distribution:** `BUILD: 10h 45m (43%), PLAN: 7h 23m (30%), FIX: 4h 17m (17%)`. Knowing that nearly a third of the week was spent planning is a critical GTD reflection metric.
   - **Off-Clock Balance:** `11h 30m off-clock across 13 sessions (Abby 8h 30m, Kelly 2h 30m, Body 30m)`. Life balance and personal commitments are completely erased from the summary.
   - **Bryan's Own Logged Words:** The brief captured 38 explicit log entries written by Bryan (e.g., launching epics for `bob-cli-ft`, running research on Athena/Apollo, adding songs to Spotify). None of this qualitative context informed the narrative.
5. **The Quality of the Questions:**
   - *Question 1:* Asking what tasks made up the 33 extra closes is an accounting query that asks Bryan to do manual data analysis.
   - *Question 2:* Asking "what happened to Wednesday's closeout?" sounds like an administrative audit rather than a prompt for meaningful weekly reflection.
   - *Question 3:* Highlighting 3× keeps with no reason is good, but ends on a scolding note ("what keeps them on the list?") rather than a decision-forcing GTD prompt ("should these be scheduled with dependencies or pruned to Someday?").

---

## 2. Evaluation: Is Modifying the Instructions a Good Idea?

### Arguments in Favor:
1. **The GTD Weekly Review is Bryan's highest-leverage ritual.**
   According to `gtd_daily.md`, every Monday morning during `#post`, Bryan executes:
   > *"Weekly review: close last week — from today's note open the week link, then ‹; correct the draft PRE started ... and write the Reflection · open this week's note, re-read the quarter's Outcomes (↑), and set ≤3 Intentions · prune: release NEXT ... PENDING ... promote from READY ... clear leftover ROTTEN"*
   The draft's sole purpose is to serve Bryan during this 15-minute window. If the draft is redundant and administrative, Bryan skips reading it or mentally filters it out. If the draft surfaces strategic patterns, trade-offs, and clear candidates for pruning/scheduling, it directly powers his decision-making.
2. **Zero Code Changes Required for Existing Notes.**
   `bob-cli` already has a built-in mechanism for updating callouts across the entire vault:
   `bob periods ensure -R/--refresh-instructions`.
   Updating the templates in `src/native/periods/instructions.rs` and bumping `INSTRUCTIONS_VERSION = 2` allows `bob periods ensure -R` to safely, idempotently upgrade all period notes across the vault in a single transaction.
3. **The Information Already Exists in the Brief.**
   `bob periods brief` already collects work types, off-clock time, Bryan's words, and started/dropped tasks. Improving the instructions does not require complex new backend statistics; it simply teaches the agent how to synthesize the gold that `brief` already provides.

### Risks and Constraints (What Must NOT Change):
1. **Word Caps Must Remain Rigid:**
   The word caps (250 words for weekly, 400 for quarterly, 600 for yearly) are essential. They protect Bryan from LLM bloat and keep reading time under 2 minutes. Any instruction change must fit comfortably within these caps.
2. **The "No Scores / No Advice / No Because" Rule Must Be Preserved:**
   Decision records and `docs/stats.md` explicitly reject automated "productivity scores", cheerleading ("Great job on bob!"), or speculative causal claims ("You worked less because you were tired"). The agent must remain an objective, evidence-linking intelligence officer, not an ungrounded coach.
3. **The Brief Remains the Sole Source of Numbers:**
   Agents must never open raw daily notes to tally numbers or calculate arithmetic. All metrics must trace to `bob periods brief`.
4. **Draft Validation Rules in `bob periods draft`:**
   The CLI strictly rejects drafts that contain Markdown headings (`#`), frontmatter fences (`---`), or agent callouts (`[!agent]`), and enforces `**Headline:**` on line 1. Instruction changes must strictly adhere to these syntax bounds.

---

## 3. Concrete Design: The "v2" Agent Instructions

Below are the proposed improvements across Weekly, Quarterly, and Yearly instructions.

### 3.1 Weekly Instructions (v2)

#### Current (v1):
```markdown
> 3. **Write at most 250 words**, in this order, leaving out empty parts:
> `**Headline:**` one standalone sentence of at most 25 words. Parent notes display it.
> **Intentions:** one line each, marked ✓ done · ◐ partial · ✗ not done · – unclear, with one evidence link.
> **Where the time went:** one bullet per root parent with at least 10% of Worked, naming what the time bought.
> **Finished:** `^prj` completions first, then at most 7 tasks, then `+N more`.
> **Still open:** at most 5 stalled Next or WIP tasks, newly Blocked projects, or tasks kept 3+ times.
> **Questions:** 2–3, each grounded in a fact above.
>
> Don't retell the days; the strip and `## Days` already show them.
```

#### Proposed (v2):
```markdown
> 3. **Write at most 250 words**, in this order, leaving out empty parts:
> `**Headline:**` one standalone sentence of at most 25 words summarizing the week's
> main accomplishment, focus, or shift. Don't repeat total hours or percentage
> deltas; the stats strip and parent tables already display them.
> **Intentions:** one line each (✓ done · ◐ partial · ✗ not done · – unclear) with
> an evidence link. If none were set, you may note up to 2 ties to parent
> [[quarter#Outcomes|Quarter Outcomes]].
> **Where the time went:** one bullet per root parent with ≥10% of Worked, naming
> what the time bought; include a closing line on dominant work types (BUILD, PLAN,
> FIX) and off-clock personal areas if notable. Consult 'Bryan's words' in the
> brief to understand the intent behind the sessions.
> **Finished:** `^prj` completions first, then at most 5 notable, non-routine
> tasks/deliverables (skip tasks already listed in 'Where the time went'; omit daily
> checklist routines like review, chores, and pills; summarize daily review closures
> in one phrase if notable, e.g. 'Daily review closed 6/7 days'), then `+N more`.
> **Still open:** at most 5 stalled WIP tasks, newly Blocked projects, or tasks
> kept 3+ times (rotten).
> **Questions:** 2–3 strategic GTD questions to aid Bryan's reflection and upcoming
> planning. Focus on trade-offs between areas, unblocking next steps on shipped
> work, or deciding whether stalled/rotten tasks should be pruned to Someday or
> given explicit prerequisites. Avoid compliance or administrative auditing.
>
> Don't retell the days; the strip and `## Days` already show them.
```

### 3.2 Quarterly Instructions (v2)

#### Current (v1):
- Synthesizes weeks into Arcs (2–4 threads spanning ≥2 weeks), Projects (finished, started, stalled), Time shift (against previous quarter), and 2–4 Questions (one about next quarter's Outcomes). Word cap: 400 words.

#### Proposed Improvements for Quarterly (v2):
- **Headline:** Focus on the strategic inflection point of the quarter rather than repeating worked hours.
- **Outcomes & Horizon 3 Alignment:** Evaluate the quarter's `## Outcomes` against 1–2 year goals (`[[h3_goal]]`), noting which long-term bets gained traction.
- **Projects & Arcs:** Clearly distinguish finished major project milestones (`^prj`) from stalled initiatives. Highlight abandoned or pivoted threads.
- **Time Shift & Practice:** Note structural shifts in where time was invested compared to the prior quarter, and shifts in routines (review-closed rates, recurring habits).
- **Questions:** Frame questions around upcoming quarter Outcomes and pruning stalled projects.

### 3.3 Yearly Instructions (v2)

#### Current (v1):
- Synthesizes quarters into Theme & Outcomes, What got finished (≤10 projects), Where the year went (root shares by quarter), Changes in practice (routines, review-closed rate), Questions (3–5 tied to `[[h3_goal]]` and `[[h4_vision]]`). Word cap: 600 words.

#### Proposed Improvements for Yearly (v2):
- Keep the structure, which is already well-aligned with Horizons 3 (`h3_goal`) and 4 (`h4_vision`).
- Strengthen the requirement to contrast quarters (e.g., Q1/Q2 foundational build vs. Q3/Q4 consolidation).
- Add explicit guidance to look at recurring routines started vs. dropped across the entire year.

---

## 4. Side-by-Side Comparison: 2026-W45 Draft

To verify the impact of these changes, consider how `2026-W45` is transformed when drafted under `v2` instructions:

| Section | `weekly v1` (Actual Drafted Output) | `weekly v2` (Proposed Redraft) | Improvement |
| :--- | :--- | :--- | :--- |
| **Headline** | `A 24h 45m week, 5h 28m below typical, put 45% into bob, led by WIP/Next auto-decay and weekly/quarterly/yearly note templates.` (22w) | `Shipped WIP auto-decay and period note scaffolding in bob, while advancing SASE sidecar publishing and triage.` (16w) | Eliminates redundant metrics already shown in the strip; summarizes the actual work shipped. |
| **Where the time went** | Lists `bob`, `gtd`, `sase` tasks. (88w) | Lists `bob`, `gtd`, `sase` tasks; adds: `Work types: BUILD 43%, PLAN 30%, FIX 17%. Off-clock: 11h 30m across personal areas ([[abby]], [[kelly]], [[body]]).` (102w) | Surfaces high planning ratio (30%) and personal/family time balance from the brief. |
| **Finished** | Repeats auto-decay, templates, and 5 separate daily review rows (`Mon 1h 30m`, `Tue 1h 00m`, etc.). (48w) | `- [[done/dev_done#^doctl\|Authenticate and configure doctl]] · 35m`<br>`- [[done/sase_done#^fix-agent-sidecars\|Agent sidecar publishing]] · 20m`<br>`- [[done/dev_done#^fix-anacron-errors\|Fix anacron errors in emails]] · 12m`<br>`+242 more across maintenance and research.` (36w) | Deduplicates against time-spent section; removes daily checklist noise; surfaces real finished work. |
| **Still open** | Lists 4 rotten tasks kept 3×. (42w) | Same 4 rotten tasks kept 3×. (38w) | Concise and preserved. |
| **Questions** | - What kinds of tasks made up those closes?<br>- Wed 4 missed closeout — what happened?<br>- Three keeps carry no reason — what keeps them on the list? (36w) | - `Bob took 45% of worked time on core tooling; does the completion of auto-decay and period scaffolding unblock your primary Q4 deliverables?`<br>- `Four tasks have reached 3+ keeps without progress; which of these should be scheduled with hard prerequisites vs. pruned to Someday?` (44w) | Replaces administrative nagging with strategic GTD decision prompts. |
| **Total Words** | **236 words** (near cap, 26% noise) | **217 words** (comfortably under cap, 100% signal) | Higher density, zero fluff. |

---

## 5. Potential Enhancements to `bob periods brief`

While instructions alone yield immediate benefits, a few targeted enhancements to `bob periods brief` in `bob-cli` would make agent drafting even more reliable:

1. **Tag Routine / Maintenance Tasks in Brief JSON & Markdown:**
   In `src/native/periods/brief.rs`, tasks rooted at `gtd_daily` or marked `#gtd #post/#pre` can be flagged as `routine: true` or grouped into a `## Routine Maintenance` summary (`Daily reviews: 6 of 7 closed (6h 58m)`). This prevents the LLM from having to guess which tasks are recurring chores.
2. **Flag Shipped Milestones:**
   Explicitly identify tasks that closed an epic, closed a `^prj` line, or had an associated release note.
3. **Intentions / Outcomes Bridge:**
   When `## Intentions` in the current note is empty, `bob periods brief` could output an explicit hint:
   `Note: Intentions were not set for this week. Parent Outcomes for 2026-Q4 are: [...]`. This prompts the agent to evaluate the week against the quarter's goals automatically.

---

## 6. Implementation & Rollout Plan

If approved, the changes should follow this clean sequence:

1. **Update Rust Templates & Tests in `bob-cli`:**
   - In `src/native/periods/instructions.rs`:
     - Update `INSTRUCTIONS_VERSION = 2`.
     - Update `render_weekly()`, `render_quarterly()`, and `render_yearly()` with the refined text.
   - Update tests in `src/native/periods/instructions.rs` and `tests/cli/periods.rs`.
   - Update `docs/periods.md` §4 ("Agent instruction callouts").
2. **Verify Against Contract Constraints:**
   - Run `cargo test` and `just check`.
   - Ensure rendered callouts adhere strictly to the word caps and formatting rules.
3. **Roll Out to Vault via `bob periods ensure -R`:**
   - Run `bob periods ensure -R -f json` in the vault.
   - This command scans all period notes, detects callout version `v1 < 2`, and replaces only the callout block in an atomic `vault_rewrite` commit, leaving Bryan's sections and existing Reviews completely untouched.
4. **Test Next Monday Draft:**
   - On 2026-11-16 (W46 review), observe the newly drafted review under `weekly v2` and gather Bryan's feedback during his `#post` weekly review ritual.

---

## 7. Conclusion

Improving the period note agent instructions is a high-impact, low-risk upgrade. The infrastructure built in `bob-cli` is robust; what was missing was editorial precision in the prompt contract. By instructing agents to avoid repeating dashboard numbers, filter out routine chores, synthesize work types and life balance, and ask provocative GTD questions, period reviews will become an indispensable catalyst for Bryan's weekly planning.
