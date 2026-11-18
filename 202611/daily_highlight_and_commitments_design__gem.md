# Daily Commitments and Highlights in Bob: Design Critique, Empirical Audit, and Recommended Solution

> **Context:** Independent research report (`__gem`) written **2026-11-17** (Tuesday of `2026-W47`). Grounded in a read-only audit of Bryan's Bob vault (`~/bob/2026/20261101.md`–`20261117.md`, `2026-W40.md`–`2026-W47.md`, `2026-Q4.md`, `2026.md`, `gtd_daily.md`, legacy `now_gtd.md`/`legacy_gtd.md`, `lit/*.md`, and prior research), `~/.config/bob/config.yml`, `bob-cli` source and docs (`src/native/periods/`, `src/native/plan_budget/`, `docs/{periods,plan,freshness}.md`), `bob-plugins`, `bob-mac-capture`, and behavioral literature. Nothing in the vault or codebases was modified.

---

## Executive Summary

**You are diagnosing a real failure in your daily execution loop, but copying weekly `## Intentions` into a prose `## Commitments` section on daily notes is the wrong mechanism.**

Across 17 days of November 2026 (`2026-11-01`–`2026-11-17`), your daily note already holds an execution plan (`## Pomodoros` / `TODAY`), yet empirical telemetry shows `TODAY` behaves like an **uncommitted rolling menu** rather than a daily bet:
- You averaged **`211.5m` (`3.52h`)** on-clock Worked time/day across **`19.2` closed Pomodoros/day**, but **`65.8%` (`196/298`)** of closed on-clock Pomodoros lasted **`≤10m`** (mean `12.1m`, median `10.0m`)—mostly reactive 5–10m SASE agent launches/researches across `mean 16.8` distinct tasks/day—while **`<1` task/day** received **`≥30m`** (`0` non-`gtd`/non-`MEET` tasks `≥30m` on `9` of `17` days, including `0` so far on `2026-11-17`).
- With `plan.max_links: 13` (raised above `docs/plan.md`'s default `10`) and `PENDING` currently over cap (`11/8`), closed days Nov 1–16 ended with **`mean 7.9` (median `8.0`, range `0–13`) unworked non-self open Task Links** (`127` open link-ends total). Only **`18.1%` (`23/127`)** were worked the very next day, **`49.6%` (`63/127`)** sat unworked open two consecutive days, and **`32.3%` (`41/127`)** vanished unworked.
- Even in `2026-W47`—where you set weekly `## Intentions` for the very first time yesterday (`2026-11-16`)—Intention #2 (`sase-1n6`) has zero presence in `20261117.md`, Intention #1 (`sase_blog_zettel`) sits at `0m` in `WRITE`/`READ`, and Intention #3 (`sase#^fix-decision-memory-web`) has sat **open and unworked in `FIX` for 6 consecutive days (`Nov 12–17`)**.

Meanwhile, adding a manual prose `## Commitments` heading to `YYYY/YYYYMMDD.md` would collide with Bob's reserved term **"Commitments done"** (`docs/freshness.md`), force dual-entry duplication against `TODAY` (`decisions:today-is-read-from-the-ledger`), add process weight onto a `gtd` (`PLAN`) footprint already consuming **`28.0%` (`59.1m/day`)** of Worked time in November (`31%` in W47 so far), and lack any daily `## Review` loop (`brief.rs`: *"Days have no Review"*). Furthermore, `~/bob/gtd_daily.md:13` *already* has a broken daily-commitment step—`highlight chosen (≤3 themes, highlight first)`—whose theme cap was retired in `bob-cli` and `bob-mac-capture` and whose `★` Highlight points at a shifting **Type group** rather than a concrete deliverable.

### Bottom-Line Recommendation
1. **Call it `Highlight`** (`1` mandatory daily win) optionally backed by up to **`2` supporting `Bets`** inside `TODAY` (**`≤3` key targets max**, never "Daily Commitments").
2. **Do not add a new daily prose section or build code right now.** Run a **zero-code Phase 1 trial (`2026-W47`–`W49`)** while weekly `## Intentions` stabilizes:
   - Lower `plan.max_links` in `~/.config/bob/config.yml` from **`13` → `8`** so `TODAY` stops acting as an overflow drawer.
   - Update **`Morning review`** (`~/bob/gtd_daily.md:13`) to replace the stale `(≤3 themes, highlight first)` text with a two-part morning gate: **(a) sweep yesterday's unworked `TODAY` carryover** (run, re-pick intentionally, or unlink) + **(b) check this week's `## Intentions` and crown `1` concrete `★ Highlight`** (top Pomodoro first, protected for `30–60m` before reactive `FIX` agent loops).
   - **Do NOT add an `#post` Evening review task** to `gtd_daily.md` (that would walk during the *morning* `]s` walk before `Morning review` and risk breaking `review_closed`). Put carryover reckoning in the **94%-reliable morning ritual** (`16/17` days closed in Nov).
3. **Only if Phase 1 holds through `2026-W49`**, implement minimal **Phase 2 ledger-first tooling** in `bob-cli` / `bob-plugins` / `bob-mac-capture`: a **task-pinned `★ Highlight`** (doesn't jump groups when the top entry closes), a **yesterday-carryover lint** (`bob plan` / `reconcile`), and an automatic **`★ [[task]] ✓/✗` token in weekly `bob periods brief`'s `## Parts` lines** so daily Highlights close cleanly inside the weekly Review you already run.

---

## 1. Critique of the Plan in General

Is adding something parallel to weekly `## Intentions` for daily files a good idea? **The instinct is right (your days lack a binding anchor linking Intention to execution), but the literal parallel—a manual prose section like `## Commitments` in `YYYY/YYYYMMDD.md`—is fragile and architecturally upside down for Bob.**

### 1.1 Timing Risk and Planning-Layer Overhead
1. **Weekly `## Intentions` is literally one day old.** As documented in your own `bob#^ref-what-to-write-in-period-notes` (`2026-11-10`), scanning all prior period notes found **0 of 47 weeks**, **0 of 5 quarters/years**, and **0 of 52 Reflections** filled (`W46` held `- NOT SET`). You filled `2026-Q4` Outcomes and `2026-W47` Intentions for the very first time **yesterday (`2026-11-16`)**. That report explicitly advised running the weekly loop for **2–4 weeks before building anything** because Bob's vault already contains a graveyard of abandoned hand-kept planning surfaces (`now_gtd.md`, `soon_gtd.md`, `now_*.zo` query pages, `sase_blog_blockers.md`, and the 73-task bulk `#now` tagging stripped the same day per `decisions:now-tag-is-user-owned`).
2. **Planning overhead (`PLAN`) already consumes nearly a third of your workday.** Across Nov 1–17, on-clock `PLAN` Pomodoros totaled **`mean 59.1m/day` (`28.0%` of all Worked time)**—peaking at **`41.9%`** (Nov 2) and **`47.4%`** (Nov 10), and standing at **`31%` (`2h 10m` of `7h 05m`, `gtd` as your #1 root parent)** in `2026-W47` (`bob periods brief 2026-W47`). Your own `lit/uptime.md:74` margin note from `2024-11-05` captures your threshold clearly: *"`@REJECTED`: I already write too much. I'm not keeping a 'productivity diary'."* Adding a daily prose writing + evening grading habit risks pushing maintenance time higher—or getting skipped whenever a week gets busy.

### 1.2 Architectural Asymmetry: Why Week/Quarter/Year Need Prose Sections and Days Do Not

Look closely at what each period note holds in `src/native/periods/` and `docs/periods.md`:

| Period Note | Execution Ledger? | Agent `## Review`? | How Planning Connects to Execution | Why Prose `## ...` Exists (or Collides) |
| :--- | :--- | :--- | :--- | :--- |
| **Year** (`YYYY.md`) | None (no `#task` rows allowed) | Yes (`brief.rs` reads Q4/Q1–Q4 + `h3_goal`/`h4_vision`) | Sets tie-break (`## Theme`) + annual milestones (`## Outcomes`) | No task list exists at year scale; prose is the *only* plan |
| **Quarter** (`YYYY-Q#.md`) | None (no `#task` rows allowed) | Yes (agent marks `## Outcomes` `✓ ◐ ✗ –`) | Feeds *Parent Outcomes* into every week brief | No quarter ledger exists; prose bridges Goals → Weeks |
| **Week** (`YYYY-W##.md`) | None (`NEXT` is a fluid lane, not a closed week list) | Yes (`brief.rs` copies `## Intentions` verbatim; Review marks `✓ ◐ ✗ –`) | Distinguishes **1–3 results** from up to 13 `NEXT` chores | Next Monday's agent reads and marks `## Intentions`, closing the loop |
| **Day** (`YYYYMMDD.md`) | **Yes: `## Pomodoros` (`TODAY`, `bob plan`, `★`)** | **No** (`report.rs` & `brief.rs`: *"Days have no Review"*) | `TODAY` is derived live from `## Pomodoros` Task Links | **A prose section here duplicates `TODAY` and has no automated Review reader** |

Three concrete codebase facts sharpen this contrast:
- **No reader exists for daily prose:** `src/native/periods/brief.rs` only inspects each day for `closeout` (`review_closed` from the `Morning review` chore), worked minutes, and `mostly` top root percentages (`Tue 17 · 3h 40m · mostly gtd 36% · bob 27% · job 20% · open`). Any free-form daily section in `YYYYMMDD.md` would sit **unread by `bob`, `bob plan`, Bob Mac Capture, and weekly `bob periods brief`**.
- **Single source of truth (`decisions:today-is-read-from-the-ledger`):** Bob deliberately retired daily `#now` state and made `## Pomodoros` the **one place** `bob plan`, Obsidian's Day Strip (`239-plugin-day-strip-plan-host.js`), and Bob Mac Capture's idle agenda (`CaptureAgendaPresentation.swift`) read today's plan from. Maintaining a separate prose `## Commitments` list alongside `## Pomodoros` requires writing commitments twice—once in prose, then again as Task Links in `## Pomodoros`—and guarantees drift whenever the day shifts.
- **Direct terminology collision (`Commitments`):** In Bob, **"Commitments"** is *already* an official UI and doc term for tiers 1–7 of the freshness walk (`PRE → NEW → PROJECTS → PENDING → NEXT → RECURRING → TICKLER` in `docs/freshness.md`). Both `~/bob/gtd_daily.md:13` (`walked to Commitments done`) and `bob-ledger-tools/src/120-freshness-footer.js:833` (`"Commitments done"`) display this word every morning. Naming daily targets `Daily Commitments` or `## Commitments` forces one word to mean both *"all GTD inbox/lane obligations walked before `ROTTEN`"* and *"today's 1–3 chosen deliverables."*

---

## 2. Empirical Diagnosis: What *Actually* Breaks Daily Follow-Through (Nov 1–17 Audit)

If a prose daily section isn't the right fix, why does it *feel* like your daily notes lack commitment? Auditing all **17 November daily files (`20261101.md`–`20261117.md`)**, live `bob plan`, and `bob periods brief 2026-W47 -f md` reveals **four specific, measurable breakdowns** inside the existing daily plan:

### 2.1 High-Burst Agent Work Masks Near-Zero Sustained Focus
| Metric (Nov 1–17, 2026 · N = 17 days) | Observed Value | Range / Distribution | What It Reveals |
| :--- | :--- | :--- | :--- |
| Closed Pomodoros / day | mean **19.2** (median **20**) | `10`–`25` | High session count every day |
| Closed on-clock Pomodoro duration (N = 298) | mean **12.1m** (median **10.0m**) | **`196/298` (`65.8%`) are `≤10m`** | Predominantly rapid SASE agent launches/checks |
| Total on-clock Worked / day | mean **211.5m** (**3.52h**) | `105m`–`340m` (median `205m`) | ~2.5h/day left after `PLAN` |
| `PLAN` (`gtd`) Worked / day | mean **59.1m** (**28.0%** of total) | `25m`–`90m` (`11.9%`–`47.4%`) | Morning GTD/admin is already heavy |
| Non-recurring, non-`#gtd`, non-`MEET` tasks completed / day | mean **25.5** (median **25**) | `8`–`42` | Lots of small `5m` fixes close smoothly |
| Distinct non-`#gtd`, non-`MEET` tasks worked in Pomodoros / day | mean **16.8** (median **18**) | `8`–`24` | Effort scatters across ~17 items/day |
| Non-`#gtd`/non-`MEET` tasks receiving **`≥30m`** in a day | mean **0.7/day** | **`0` on `9/17` days** (`0` on `Nov 17`) | Almost nothing gets a 60m Highlight block |
| Unworked open Task Links left at day end (Nov 1–16, N = 16) | mean **7.9/day** (median **8.0**) | `0`–`13` (`127` total link-ends) | **`TODAY` acts as a parking lot, not a bet** |

### 2.2 Chronic Unacknowledged Carryover (`18.1%` Next-Day Work Rate)
Tracking every non-self open Task Link left unworked at the end of Day $D$ into Day $D+1$ across Nov 1–16 (`N = 127` open link-ends):
- **Only `23 / 127` (`18.1%`)** received a closed Pomodoro the next day ($D+1$).
- **`63 / 127` (`49.6%`)** remained open and unworked **two consecutive days in a row**.
- **`41 / 127` (`32.3%`)** dropped out of $D+1$'s open ledger without a closed Pomodoro (completed off-ledger, deferred, or removed).

Right now in your live `20261117.md` (`bob plan` at `2026-11-17` afternoon: **`PLAN 11/13 links · 1 off-clock · TODAY 12 · PENDING 11/8 · NEXT 10/13`**):
- **`sase#^fix-decision-memory-web`**—literally **Intention #3** of `2026-W47`—was last worked on `2026-11-12` and has carried open and unworked across **five prior days (`Nov 12–16`) plus today (`Nov 17`)**.
- **`bob#^no-links-blocked-group`** has carried open and unworked across **four prior days (`Nov 13–16`) plus today (`Nov 17`)**.
- Meanwhile, **`PENDING` is over soft cap (`11/8`, triggering `pending_cap_exceeded`)**, because `TODAY` links keep raising tasks into sticky lanes without any daily pruning rule on carried links.

### 2.3 `★ Highlight` Is Broken by Construction (And `gtd_daily.md` Teaches a Retired Rule)
Look at what your system currently says vs. what it actually does:
1. **`~/bob/gtd_daily.md:13` (`Morning review`) says:**
   `highlight chosen (≤3 themes, highlight first)`
   - **Bug 1 (Stale rule):** The `≤3 themes` cap no longer exists! Both `docs/plan.md` (*"Types are listed, never budgeted: no type count, cap, warning, or refusal exists"*) and `CapturePlanBudgetPresentation.swift:15-19` (*"retiredTypeCapWarningCode = 'plan_theme_cap_exceeded' (all ignored)"*) removed it. Yet `gtd_daily.md` still reminds you of it every morning.
   - **Bug 2 (Group-level positional `★`, not a daily bet):** In `src/native/plan_budget/mod.rs:768-770`, `entries[first].highlight = true` simply marks **the first open non-exempt Pomodoro entry in ledger order**. Because your open Pomodoros are Type buckets (`WRITE`, `READ`, `CHORE`, `FIX`, `MEET`), today's `bob plan` shows `★ WRITE 1 link`—meaning the "Highlight" is a *task type category*, vanishes or slides onto `★ READ` the moment `WRITE` finishes, never targets a task inside a multi-link bucket (`FIX` holds `5` links), and is not surfaced as a pinned daily win in `CaptureAgendaPresentation.swift`.

### 2.4 Weekly Intentions Don't Feed Morning Selection
In `2026-W47.md`, Monday's checklist had you write 3 concrete Intentions (`sase_blog_zettel` album, `sase-1n6` release train, `sase#^fix-decision-memory-web`). But Tuesday–Sunday `Morning review` (`gtd_daily.md:13`) never prompts you to glance at `2026-W47` before picking `highlight`, so today produced `21` closed Pomodoros (`FIX`/`BUILD` quick hits + `80m` of `PLAN`) while Intention #2 stayed absent and Intention #3 stayed buried in `FIX`.

---

## 3. Justified Adjustments to the Requirements

Before choosing an implementation, five adjustments to the initial framing ("do something similar for daily files, called daily commitments, with a limit and a `gtd_daily.md` policy") are justified by the evidence above:

| # | Original Assumption / Framing | Recommended Adjustment | Justification from Vault, Code & Science |
| :--- | :--- | :--- | :--- |
| **1** | Call them **"Daily Commitments"** (matching `## Intentions` / `## Outcomes` / `## Theme`). | **Call the anchor `Highlight`** (`1` mandatory win), optionally paired with **`≤2` supporting `Daily Bets`** inside `TODAY`. | "Commitments" collides with `Commitments done` in `docs/freshness.md` & `gtd_daily.md`. `Highlight` already appears in `gtd_daily.md:13`, `plan_budget::highlight` (`★`), and `lit/make_time.md`. |
| **2** | Store them as a **new prose Markdown section** in `YYYY/YYYYMMDD.md`. | **Keep daily execution in `## Pomodoros` (`TODAY`) as the single source of truth**, anchoring `★ Highlight` at the top rather than creating a parallel daily list. | Daily files already have a ledger (`decisions:today-is-read-from-the-ledger`); prose headings duplicate `TODAY`, add unreviewed `PLAN` typing, and have no `## Review` reader (`brief.rs`). |
| **3** | Focus policy solely on **picking tomorrow/today's items** (`commitment limit`). | **Pair picking `1` Highlight with an explicit Morning Carryover Triage + tighter `plan.max_links` (`13 → 8`).** | Without clearing yesterday's `mean 7.9` zombie links (`49.6%` stuck 2+ days) and capping `TODAY`, a `1–3` commitment pick just sits on top of a `13`-item pile—magnifying attention residue (Leroy 2009) and burying Intentions. |
| **4** | Add a new **Evening review / Daily closeout `#gtd` task** in `gtd_daily.md` to mirror Weekly review. | **Do carryover & `Highlight` selection inside the existing `#post Morning review` row** (fix line 13); **do NOT add an `#gtd #post` Evening chore.** | Technically, `#gtd #post` rows walk *before* `Morning review` in the morning `]s` walk (`docs/freshness.md:42` / `105`), breaking closeout (`review_closed`). Behaviorally, `Morning review` already runs **`16/17` (`94%`)** days; an unguided evening task won't. |
| **5** | Build `bob-cli` / plugin / capture support immediately to match period notes. | **Run Phase 1 (zero code: `gtd_daily.md` + `config.yml`) through `2026-W49`** alongside the weekly Intentions trial; build **Phase 2** (`★` task-pin + `brief` `## Parts` flag) only if Phase 1 proves value. | Honors the 2–4 week validation gate from `bob#^ref-what-to-write-in-period-notes` (6 days ago), respects `gtd + bob = 58%` time load, and prevents yet another dead hand-kept layer. |

---

## 4. Detailed Design Analysis

### 4.1 What Should We Call Them?

| Candidate Term | Fit in Period Hierarchy (`Year → Quarter → Week → Day`) | Alignment with Bob Vault & Code | Psychological Clarity & Trap Avoidance | Verdict |
| :--- | :--- | :--- | :--- | :--- |
| **Daily Commitments** (`## Commitments`) | Looks parallel phonetically, implies binding daily promise | **Poor — direct collision** with `freshness` *Commitments* (`PRE..TICKLER`, `Commitments done`) | "3 commitments" blurs the 1 crucial win with routine chores; failure induces guilt/checkbox rewriting | **Reject** |
| **Daily Highlight** (`★ Highlight`) | Year **Theme** → Quarter **Outcomes** → Week **Intentions** → Day **Highlight** | **Best — already in `gtd_daily.md:13`**, `bob plan` (`★`), `plan_budget::highlight`, and `lit/make_time.md` | *Make Time* defines Highlight as **1** concrete, medium-sized (`60–90m`, or `30–60m` in your `3.5h` day) focal choice | **Primary Winner** |
| **Highlight + Bets** (`1` Highlight + `≤2` Bets) | Emphasizes uncertainty/allocation (like Shape Up "bets, not backlogs") | Harmonizes with `bob#^ref-what-to-write-in-period-notes` ("bets, not backlogs") | Captures days with `1` main win plus `1–2` non-negotiable supporting deliverables (`≤3` total) without turning `3` into a quota | **Recommended Pair** (when needing 2–3) |
| **Daily Intentions** | Same noun across Week and Day | **Confusing** with `## Intentions` in `YYYY-W##.md` | Weakens Week Intentions ("finished by Sunday") if daily chores use the same word | **Reject** |
| **Daily Focus / MITs / Targets** | Functional but generic | Zero hooks in `bob-cli`, `gtd_daily.md`, or `bob-mac-capture` | "Targets" risks Ordóñez et al. (2009) numeric target gaming; "MITs" is external jargon | **Fallback Only** |

**Terminology call:** Use **`Highlight`** for the singular daily bet (answer to *"What one finished outcome makes today a win—especially toward this week's Intentions?"*), and **`TODAY` (`max_links: 8`)** for the remaining bounded queue of tasks you plan to touch (or, if picking a secondary set, at most `2` **`Bets`** alongside `1` Highlight = `≤3` anchored items). Your own literature notes endorse both halves: `lit/make_time.md:13` (*"Medium sized 'highlights' are the best motivator"*), `lit/uptime.md:61-79` (*"absolute top priority"* protected during *"power hours"*), and `lit/productivity_project.md:42` (*Three Daily Tasks*).

### 4.2 Where Should It Live? Comparing Architectural Options

#### Option A: Parallel Prose Section (`## Highlight` / `## Commitments`) in `YYYY/YYYYMMDD.md`
Add a manual heading under `^gtd` (or inside `_templates/daily.md`) holding 1–3 plain Markdown bullets (`- Finish X -> [[note#^id]]`).
- **Pros:** Visually mirrors `## Intentions` in `YYYY-W##.md`; allows free-form non-task personal outcomes (`"Bed before 11pm"`).
- **Cons:**
  1. **Dual-entry tax:** Every work commitment must be written in `## Highlight` *and* linked inside `## Pomodoros` for `bob plan`, `CaptureAgenda`, and `task reconcile` to know about it.
  2. **Invisible to `bob`:** `docs/plan.md`, `bob-mac-capture`, `bob periods brief`, and `bob-ledger-tools` ignore arbitrary headings in daily notes. Without building a new Rust parser, validator, and brief extractor, Option A has zero enforcement and zero weekly summary feedback.
  3. **Known vault failure mode:** Unread daily text headings invite "empty-section fatigue" (`lit/uptime.md:74`, `W40–W45`).

#### Option B: Ledger-Native `★ Highlight` + Tightened `TODAY` (Zero-Code Phase 1 → Light Pinning Phase 2)
Keep `YYYY/YYYYMMDD.md` single-source-of-truth (`## Pomodoros`). Upgrade `highlight` from "whichever Type group happens to sit first" into **an explicit, bounded daily win inside `## Pomodoros`**.
- **Phase 1 (Zero code, starts tomorrow):** During `Morning review`, pick **1 concrete task** (first checking `2026-WNN` `## Intentions`) and place its single-task Pomodoro **at the very top of `## Pomodoros`** (right below closed morning `PLAN` entries), sized cleanly (`30–60m` or 1 finished agent-to-ship cycle) and lower `plan.max_links` to `8`. Yesterday's leftover open links are actively audited before linking anything new.
- **Phase 2 (Optional later):** Teach `bob-cli` that `★` pins to a **specific task link** (e.g., `★ [[sase#^fix-decision-memory-web]]` or explicit `[highlight]` / first pinned link at morning closeout), stays pinned as `★ ✓` if completed or `★` if unfinished rather than floating onto another Type group, gets surfaced as a dedicated pill in `bob-mac-capture`, and automatically prints in `bob periods brief`'s `## Parts` line (`Tue 17 · 3h 40m · ★ [[...]] ✓/✗ · mostly ... · met`).
- **Pros:** **Zero duplication**, **zero extra writing**, directly repairs the broken `★` already in `gtd_daily.md:13` and `bob plan`, respects `decisions:today-is-read-from-the-ledger`, gives Bob Mac Capture live visibility, and lets weekly `## Review` see daily follow-through **without requiring daily `## Review` or daily `## Reflection`**.
- **Cons:** Personal non-task daily commitments (`"no phone in bed"`) require either a daily-note task checkbox (`- [ ] ...` in `YYYYMMDD.md` or `gtd_daily.md`) or staying outside the ledger. (Note: `what_to_write_in_period_notes` already confirmed that daily-note tasks and Event Tasks appear in `Finished`!)

#### Option C: Hybrid — `1` Prose Highlight Line in Daily Note + Ledger Cap (No Full List)
Only write one line (`**Highlight:** ... [[link]]`) above `bob-plan` in `YYYYMMDD.md`, while capping `max_links` in `## Pomodoros`.
- **Critique:** Better than a 3-bullet prose `## Commitments` list, because 1 line is cheap and unambiguous—yet still suffers from manual duplication (`[[link]]` appears both in `**Highlight:**` and in `## Pomodoros`) and still requires `bob-cli` parser work if `bob` or Capture or `brief` is ever to read it. If Phase 1 shows you specifically want a non-ledger daily slogan or personal promise untouched by Pomodoro execution, a 1-line Highlight (NOT 3 bullets) is the only prose form worth considering—otherwise **Option B strictly dominates** because it fixes `bob plan`'s existing `★` rather than building beside it.

### 4.3 Constraints & Calibration to Your Real Workflow

1. **Highlight Cap: Strictly `1` Highlight (Ceiling `≤3` anchored bets total, starting with `1`):**
   - *Make Time* recommends **1** Highlight (~60–90m). Because your total non-`PLAN` Worked time averages **`~152m/day` (`211.5m - 59.1m`)** and tasks receiving `≥30m` happen **`0–2 times/day`**, committing to 3 big "daily commitments" every morning guarantees either **scope dilution** (3 tiny chores) or **daily failure** (18% next-day completion dynamics).
   - **Recommended constraint:** **`1` `★ Highlight` (30–60m concrete milestone toward a Weekly Intention or stalled project)** + up to **`2` optional supporting bets** inside your `TODAY` list—meaning at most **`3`** named must-touch items on a given day, while preserving the remaining `TODAY` slots for your signature **`5–10m` SASE agent bursts** and `MEET` buffers.
2. **Tighten `plan.max_links`: Drop `13` → `8` (evaluate `7` after two weeks):**
   - Currently `plan.max_links: 13` (higher than `docs/plan.md`'s default `10`) lets you end days with **`8–13` unworked links**, while `PENDING` (`11/8`) overflows silently.
   - Dropping `max_links` to **`8`** forces genuine trade-offs at morning planning time (`plan_link_cap_exceeded` actually fires before a `12`-item backlog accumulates!) while comfortably holding `1` Highlight + `2` supporting bets + `4–5` active SASE agent/read slots. (Off-clock links remain uncapped per `docs/plan.md`.)
3. **Rule of Order — Highlight *First* Before Reactive `FIX` Sweeps:**
   - Look at `20261117.md`: by mid-afternoon, you had logged **21 closed Pomodoros**—almost all `5–10m` `FIX` and `BUILD` agent turns plus `80m` of `PLAN`—while `WRITE` (`1` link), `READ` (`3` links), and `sase#^fix-decision-memory-web` (Intention #3) stayed untouched.
   - Behavioral and organizational evidence explains why this happens cleanly:
     - **Attention Residue (Leroy 2009):** Switching rapidly across fragmented tasks leaves residual cognitive load on prior unclosed loops, starving multi-step synthesis work.
     - **Specific Goal & Implementation Intention Effect (Locke & Latham 2002; Gollwitzer & Sheeran 2006, `d ≈ 0.65`; Sheeran, Listrom & Gollwitzer 2024):** Stating *when* you start ("first non-`PLAN` Pomodoro after `Morning review`") converts an intention into an automatic cue.
     - **Progress Principle / Small Wins (Amabile & Kramer 2011):** Across ~12,000 diary entries, forward progress on meaningful work was the #1 driver of daily inner work life—specifically when *meaningful* work moved forward, not mere reactive busywork.
     - **Cognitive Closure on Unfinished Loops (Masicampo & Baumeister 2011):** Leaving vague open links creates intrusive cognitive interference; **explicitly deciding** when/whether an unfinished link runs (next slot vs. release with `Alt+N`) shuts off the cognitive drag.
   - **Rule:** Never place generic multi-item Type groups like `FIX (5 links)` or `CHORE` above your `★ Highlight` group, and work **at least 1 Pomodoro (or 25–30m) on `★ Highlight` immediately after closing `Morning review`** before triaging ad-hoc `FIX` items.

### 4.4 Policy Design in `~/bob/gtd_daily.md` (What Changes, and Why No `#post` Evening Row)

Two policy options could support daily Highlights in `~/bob/gtd_daily.md`:

1. **Why NOT add an `#gtd #post` Evening Review task:**
   - First, a subtle codebase trap in `docs/freshness.md` (`POST` tier 9) and `docs/stats.md:198`: **all `#gtd #post` checklist items walk during the `]s` walk *before* the unstaged `Morning review` closeout**, and closing `Morning review` flips `review_closed = true` for day `D`. Putting an `#post` evening chore in `gtd_daily.md` either stalls morning closeout until night or trains you to check it off early in the morning (defeating its purpose) or leave it uncompleted.
   - Second, your behavioral record in November proves **Morning review is rock-solid (`16/17` = `94%` close rate)**, whereas evening shutdown rituals have zero automated walk trigger in Bob and historically go unlogged.
   - *(Optional lightweight alternative if you truly want evening hygiene:* make a 15-second mental/manual habit—close laptop only after deleting/releasing unfinished fluff from `TODAY`—outside `#gtd #post`, rather than adding a tracked checklist chore.)*
2. **Modify `Morning review` (`~/bob/gtd_daily.md:13`) directly—zero new chores, zero `review_closed` side effects:**
   - Note that `run task reconcile` (`#pre #init`, line 22) *already* runs before `Morning review` during `PRE`, cleaning up completed links and updating lanes.
   - Therefore, inside **`Morning review`** right after `[[crowded|CROWDED]] at 0`, we fix the stale `highlight chosen (≤3 themes, highlight first)` clause and insert two explicit, sub-90-second micro-steps:
     1. **Carryover Sweep:** Look at any leftover open links in `TODAY` carried from yesterday (`bob plan` or daily note). Don't leave zombie links untouched (`6`-day stale links like `fix-decision-memory-web` or `5`-day `no-links-blocked-group`): **either elevate one to today's `★ Highlight`, shrink/split it into an actually doable today step, or unlink/release (`Alt+N`)** to cut `PENDING` (`11/8`) and `TODAY` bloat.
     2. **Intention-Aligned `★ Highlight` Crown:** Open this week's `[[YYYY-WNN]]` (`W` nav link on daily note), read `## Intentions`, pick **`1` concrete `★ Highlight`** for today (a named single task/milestone—preferably moving a Weekly Intention—placed in its own **top `## Pomodoros` entry** above reactive `FIX`/`CHORE` pools), and keep `TODAY ≤ 8` links (`≤ 3` must-touch bets total).

---

## 5. Recommended Solution & Implementation Roadmap

Adopt **Option B (`★ Highlight` in the Pomodoro Ledger + Carryover Hygiene), phased in two gates**, starting immediately with zero code changes:

### Phase 1: Zero-Code Habit & Config Pilot (Run `2026-11-18` through end of `2026-W49`)

Make **only two small edits** (no Rust, JS, or Swift changes yet):

#### 1. Update `~/bob/gtd_daily.md` line 13 (`Morning review`)
Replace the stale `(≤3 themes, highlight first)` clause in `Morning review`:

- **Current text (`~/bob/gtd_daily.md:13`):**
  > `**Morning review**: PRE chores done or knowingly skipped · walked to Commitments done (...) · [[crowded|CROWDED]] at 0 (split, sequence, defer, drop) · highlight chosen (≤3 themes, highlight first) · [[rotten|ROTTEN]] upkeep until 0, budget, or you stop — then ]S and complete this.`

- **Proposed replacement:**
  > `**Morning review**: PRE chores done or knowingly skipped · walked to Commitments done (NEW never capped or skipped; lanes: keep Alt+Shift+F, today Ctrl+Shift+Enter, release Alt+N; tickler not-now is a priority roll, not Alt+F; recurring: Ctrl+Enter done, Ctrl+Shift+Enter today, or reschedule — never Alt+F) · [[crowded|CROWDED]] at 0 (split, sequence, defer, drop) · yesterday's leftover TODAY links triaged (keep deliberately or unlink; release stale PENDING with Alt+N) · peek [[W##]] Intentions & crown 1 ★ Highlight (own top Pomodoro, first non-PLAN block; TODAY ≤8, ≤3 core bets) · [[rotten|ROTTEN]] upkeep until 0, budget, or you stop — then ]S and complete this.`

#### 2. Tighten `plan.max_links` in `~/.config/bob/config.yml` (line 154)
```yaml
plan:
  max_links: 8    # down from 13 (docs default: 10); prevents TODAY from becoming a rolling wish-list
  max_pending: 8
  max_next: 13
  max_ready: 21
```
*(If `8` still regularly accumulates 6+ stale end-of-day carryovers after 1 week, drop once more to `7`; if `8` clips legitimate rapid-fire SASE runs because of `4–5` active `FIX`/`BUILD` links, use `9`, while keeping `≤3` core bets conceptually clear.)*

#### 3. Daily Operating Loop (90 Seconds Every Morning)
1. Finish `PRE` (`task reconcile` cleans closed/canceled links) and walk `Commitments` (`NEW` → `TICKLER`). Notice: don't dump tasks into `TODAY` with `Ctrl+Shift+Enter` during the walk unless they really beat `8`-slot scarcity.
2. Check **remaining open links in `TODAY`**: for anything left unworked from yesterday, **decide immediately**—*highlight it, split it into a startable 25m piece, or unlink it (`Alt+N` back to `READY` if it won't happen today)*.
3. Open this week's period note via today's `W47` breadcrumb, glance at **`## Intentions`**, and pick **`1` concrete `★ Highlight`** (aim for a single deliverable you can finish or meaningfully advance in **1 focused `30–60m` block**). Put that task in its **own named Pomodoro first** under `## Pomodoros` (so `bob plan` prints `★ <HIGHLIGHT NAME> · 1 link` at the top—never burying your Highlight inside a 5-link `FIX` bucket).
4. Start your **first non-`PLAN` Pomodoro** on `★ Highlight` *before* launching reactive `FIX` agent loops.

#### 4. Falsifiable Evaluation Gate (End of `2026-W49`, Sunday `2026-12-06`)
Evaluate Phase 1 after **2.5 weeks** alongside your `bob#^ref-what-to-write-in-period-notes` weekly-Intentions checkpoint:
- **Highlight fidelity:** Did `≥75%` of closed days start with a specific 1-task `★ Highlight` Pomodoro linked to a Weekly Intention or `^prj` milestone?
- **Carryover drop:** Did median day-end unworked open Task Links drop from **`8.0` → `≤3`** (and multi-day unworked consecutive zombies drop sharply from **`49.6%`**)?
- **Progress vs. busywork:** Did Weekly Review `**Intentions:**` progress from `0m` / `6`-day stalled items to concrete `✓` completions, without pushing `PLAN` share above `28%`?

*If Phase 1 stalls because `TODAY` still absorbs clutter or because `★` disappearing mid-day makes you forget what the day's bet was—AND weekly Intentions proved sticky—then and only then unlock Phase 2.*

---

### Phase 2: Minimal Code Support (Only After Phase 1 Proves Its Worth in `W49+`)

When justified, implement **three surgical, contract-consistent upgrades** across the Bob stack rather than adding a new daily prose parser:

1. **Task-Anchored Pinned `★ Highlight` in `bob-cli` (`plan_budget` + `capture_pomodoros`):**
   - Currently `src/native/plan_budget/mod.rs:768-770` marks `entries[first].highlight = true` on the first open Pomodoro group—so finishing that Pomodoro shifts `★` to `READ`/`FIX`, losing record of the day's actual Highlight.
   - **Upgrade:** Support an explicit task-level or entry-level Highlight pin (e.g., `★` marker / `=★` flag in capture or `[highlight]` on the chosen Task Link/Pomodoro entry), enforce **at most `1` pinned Highlight** per day (`duplicate_highlight` / `highlight_limit_exceeded` lint), preserve `★ ✓` once the pinned task closes (so `bob plan` and the daily record remember *what* the day's Highlight was and whether it shipped!), and fall back to current positional `entries[first]` when nothing is pinned.
2. **Carryover-Age / Unworked-Yesterday Lint (`bob plan` & `reconcile`):**
   - Cross-check open Task Links in `YYYYMMDD.md` against `yesterday.md`: emit an info/warning lint (`stale_carryover_link`, or surface a `day 3 open` badge next to carried links) whenever an open link carried unworked from yesterday (or `≥2` days unworked like `sase#^fix-decision-memory-web`). This adds **attention friction to zombie carryover** with zero manual writing overhead.
3. **Daily `★ Highlight` Visibility in `bob-mac-capture` & Weekly `bob periods brief`:**
   - **Mac Capture (`CaptureAgendaPresentation.swift`):** Render the pinned `★ Highlight` (task title + `open` / `✓ done` state) cleanly as a single subtle line or badge inside `planBudgetRow` / top of the idle agenda (`"★ <Task Title>"`), adhering strictly to `decisions:mac-capture-is-a-thin-client`.
   - **Weekly Brief (`src/native/periods/brief.rs`):** Expose each closed day's pinned `★ Highlight` outcome right inside weekly `## Parts` (e.g., `- Tue 17 · 3h 40m · ★ [[sase#^fix-decision-memory-web]] ✓ · mostly ... · met`). That gives Monday's weekly Review **full visibility into daily commitment follow-through without creating daily `## Review` or daily `## Reflection` sections**.

---

## 6. Open Questions to Confirm Before Editing `gtd_daily.md` / `config.yml`

1. **Scope of `★ Highlight`:** Should your daily `★ Highlight` stay focused on **work/vault deliverables** (matching Weekly `## Intentions` in `2026-W47` and linkable inside `## Pomodoros`), or do you frequently want an off-ledger **personal/habit Highlight** (`"lights out by 22:30"`) that has no task line? *(If personal non-task promises are half the point, a daily `#task` checkbox in `YYYYMMDD.md` / `Event Task`—or a single-line `**Highlight:**` convention—works cleanly; if `90%+` are project/Sase/Bob/Job/Read deliverables, ledger-native `★ Highlight` avoids all duplication.)*
2. **Target `max_links` tightness:** Are you comfortable testing **`max_links: 8`** right away (`PENDING` also pruned down toward `8`), or do your rapid multi-agent SASE sessions need **`9–10`** slots even with `1` protected `★ Highlight`?
3. **First-thing-after-`Morning review` rule:** Do you endorse protecting the **very first non-`PLAN` Pomodoro (`25–45m`)** strictly for `★ Highlight` before touching reactive `FIX` agent loops?

---

## Sources & Evidence Inspected

- **Vault files (read-only):** `~/bob/gtd_daily.md` (lines 1–53); `~/bob/_templates/daily.md`; `~/bob/2026/20261101.md`–`20261117.md`; `~/bob/2026/2026-W40.md`–`2026-W47.md`; `~/bob/2026/2026-Q3.md`, `2026-Q4.md`, `2026.md`; `~/bob/{gtd,bob_gtd,prj_gtd,now_gtd,soon_gtd,legacy_gtd,gtd_ideas,dash,h3_goal,h4_vision}.md`; `~/bob/lit/{make_time,one_thing,productivity_project,uptime}.md`; `~/bob/.bob/ref-sources/chat/what_to_write_in_period_notes--8f014de55f9c/source.md`.
- **Config & live CLI runs (`2026-11-17`):** `~/.config/bob/config.yml`; `bob plan`; `bob periods brief 2026-W47 -f md`; `bob periods show 2026-W47`; `bob ref find`.
- **Workspace code, docs, and memory (`bob-cli`, `bob-plugins`, `bob-mac-capture`):** `docs/{plan,periods,freshness,stats}.md`; `src/native/plan_budget/{mod,cli,today}.rs`; `src/native/periods/{scaffold,note,brief,draft,report,problems,ensure,instructions}.rs`; `src/native/capture_pomodoros_agenda.rs`; `bob-plugins/plugins/bob-ledger-tools/src/120-freshness-footer.js`; `bob-plugins/plugins/bob-navigation-hotkeys/src/535-plugin-review-checklist-walk.js`; `bob-mac-capture/Sources/CaptureCore/{CaptureAgendaPresentation,CapturePlanBudgetPresentation}.swift`; SASE memory `decisions:{review-walk-is-tiered,today-is-read-from-the-ledger,idle-capture-shows-ledger-agenda,task-lanes-are-sticky,mac-capture-is-a-thin-client,now-tag-is-user-owned}` and `glossary:{Period Note,Morning GTD Review Footer,Pomodoro,Task Link}`.
- **Empirical & behavioral literature:** Locke & Latham (2002), Gollwitzer & Sheeran (2006), Sheeran, Listrom & Gollwitzer (2024), Harkin et al. (2016), Wang, Wang & Gai (2021), Dai, Milkman & Riis (2014), Tannenbaum & Cerasoli (2013), Ordóñez et al. (2009), Masicampo & Baumeister (2011, *"Consider it done!"*), Leroy (2009, *"Why is it so hard to do my work?"*), Amabile & Kramer (2011, *The Progress Principle*).
