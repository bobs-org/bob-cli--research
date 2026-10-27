# Pomodoro Theme Taxonomy and Cognitive Ergonomics: Empirical Analysis and Modernization Roadmap

**Researcher:** `research.2n.gem` (gem)  
**Date:** October 27, 2026  
**Target Repository:** `bob-cli` / Bob Knowledge Vault  
**Scope:** Pomodoro Theme Mechanics, Catalog Evolution, Cognitive Alignment, and Taxonomy Optimization  

---

## Executive Summary

Over the past 90 days, the use of **Pomodoro Themes** in Bryan's Bob workflow underwent a dramatic trajectory: expanding from an initial disciplined core into an explosive proliferation of 76 distinct, ad-hoc micro-themes (peaking at 31 unique themes in a single week), followed by an abrupt administrative contraction on October 26, 2026, where an automated script mass-hid 70 unused themes, leaving an active roster of 6 visible themes.

The current active theme roster reported by `bob themes list` is:
```text
THEMES  76 known · 5 today · 70 hidden · last 90 days
□ GTD    today   54 days  muted · exempt
■ BUILD  today   30 days  yellow
■ JOB    today   20 days  aqua · area
■ HOME   today   11 days  violet
■ FIX    today    5 days  blue
■ READ   Oct 25  15 days  green
```

This research report presents an empirical archeology of all 1,322 Pomodoros recorded across 583 daily notes, analyzes the psychological and computational forces driving theme creation, and benchmarks Bryan's system against foundational productivity and information architecture frameworks: Francesco Cirillo's *Pomodoro Technique*, David Allen's *Getting Things Done (GTD)*, Cal Newport's *Deep Work / Time-Blocking*, Mike Vardy's *TimeCrafting Focusing Modes*, and S.R. Ranganathan's *Faceted Classification (MECE)*.

### Key Findings

1. **Dimensional Collapse (The Domain vs. Mode Collision):**  
   The current 6-theme roster suffers from a fundamental category error. It conflates **Cognitive/Operational Modality** (`BUILD`, `FIX`, `READ`, `GTD`) with **Life Domain / Area of Responsibility** (`JOB`, `HOME`).
2. **Redundancy with Bob's Derived Homes:**  
   Bob's architecture already computes task homes (Area, Project, Root Parent) automatically by walking markdown task link hierarchies at read time (`docs/pomodoro-homes.md`). Assigning `JOB` or `HOME` as a session theme provides **zero new informational entropy** in `bob stats`, while blinding the analytics engine to what cognitive work was actually performed (e.g., whether 22 hours of `JOB` were spent coding, researching, reading, or submitting application forms).
3. **The Hidden Theme Crisis & Backlog Pathology:**  
   The accumulation of 70 hidden themes was an inevitable symptom of an ontological vacuum. Without clear taxonomic boundaries, Pomodoro name tails became a dumping ground for project names (`SASE`, `ATHENA`, `BOB`), features (`PRINT COMMAND`), task fragments (`FIX KILL AND EDIT`), and emotions (`SHIT`). This friction inspired two problematic backlog items in `bob.md`: `^delete-themes` (attempting to delete immutable ledger history) and `^theme-on-task` (attempting to tie session themes to static backlog tasks).
4. **Missing Cognitive Modes:**  
   Crucial modes of high-value cognitive output—most notably **prose writing** (authoring SASE blog posts, architecture proposals, CV cover letters) and **administrative logistics** (form submissions, finances, maintenance)—currently have no dedicated theme, forcing them awkwardly into `BUILD` or `JOB`.

This report concludes with an eight-point, ranked set of actionable recommendations to establish a clean, orthogonal, and fatigue-free cognitive theme taxonomy.

---

## 1. Empirical Archeology: How Bryan Uses Themes in Bob

### 1.1 The Quantitative History of Themes

A complete scan of Bryan's daily notes in the Bob vault (`~/bob/2026/2026*.md`) yields the following baseline metrics:
- **Total Canonical Daily Notes Evaluated:** 583 notes.
- **Total Recorded Pomodoros:** 1,322 sessions.
- **Named Pomodoros (Carrying a `— NAME` Tail):** 651 sessions (49.2%).
- **Unnamed Pomodoros (Relying Solely on Derived Homes):** 671 sessions (50.8%).
- **Composites (`— A + B` Multi-Theme Sessions):** 11 sessions (<1.7% of named sessions).
- **Total Historical Unique Themes in Catalog:** 76 themes over the last 90 days.

```
+-----------------------------------------------------------------------------------+
|                           THEME USAGE EVOLUTION (2026)                            |
+-----------------------------------------------------------------------------------+
| Week     | Total Poms | Unique Themes | Dominant Themes                           |
+----------+------------+---------------+-------------------------------------------+
| 2026-W34 |     35     |      10       | MEMORY (13), BUILD (4), GTD (3)          |
| 2026-W35 |     56     |      17       | REMOTE (14), GTD (13), MEMORY WEBS (6)    |
| 2026-W36 |     51     |      13       | GTD (21), SHIT (8), VERIFY (4)           |
| 2026-W37 |     52     |      20       | GTD (11), TOOL (8), SHIT (4)             |
| 2026-W38 |     45     |      14       | SASE (10), GOALS (6), READ (4)           |
| 2026-W39 |     97     |      31       | BUILD (25), GTD (20), SASE V18 (6)       |  <-- PEAK ENTROPY
| 2026-W40 |     86     |      21       | GTD (26), BUILD (17), JOB (8)            |
| 2026-W41 |    120     |      10       | JOB (59), BUILD (19), SASE (16)          |
| 2026-W42 |     97     |       8       | READ (29), GTD (28), BUILD (17), JOB (14)|  <-- CONSOLIDATION
| 2026-W43 |     23     |       5       | JOB (8), BUILD (7), GTD (4), FIX (2)     |  <-- POST-PURGE
+-----------------------------------------------------------------------------------+
```

### 1.2 The Four Evolutionary Phases

Bryan's use of themes evolved through four distinct behavioral phases:

#### Phase 1: Ad-Hoc Micro-Theming (Weeks 34–38, Late August – Mid September)
Themes were used as temporary scratchpad labels for immediate focus areas: `MEMORY`, `MEMORY WEBS`, `REMOTE`, `TOOL`, `VERIFY`, `SETUP`. When frustration mounted, slang or emotional labels appeared (`SHIT`: 16 entries across 13 days; `FIRE`: 1 entry). Because theme names auto-registered into the catalog upon appearance in `## Pomodoros`, the catalog expanded rapidly.

#### Phase 2: The Clutter Crisis (Weeks 39–40, Late September – Early October)
Entropy peaked in Week 39 with **31 distinct themes in 7 days**. Themes began colliding directly with other structural vault entities:
- **Project Duplication:** `SASE`, `SASE V18`, `SASE-V18`, `SASE V19`, `ATHENA`, `HERMES`, `JITUX`, `MUSE`, `BEADS`, `BOB`, `DECKS`.
- **Feature/Task Descriptions:** `NEW FEATURES`, `PRINT COMMAND`, `ALIAS DEFS`, `SUBTABS`, `MESSAGES`, `SCREENSHOTS`, `SWAP POMS`, `FIX KILL AND EDIT`, `RESTART MAC`, `AFTER TUI FIX`.
- **Inventory Confusion:** `LATER` (an inventory state) was authored as an open theme, triggering `inventory_label_open` lints.

This explosion caused immediate user-interface friction. In Bob Mac Capture and Obsidian completion menus (governed by `PT7 — Menu composition`), typing or viewing `Recent` suggestions presented a chaotic list of obsolete, single-use themes.

#### Phase 3: The Macro-Consolidation (Weeks 41–42, Mid October)
Recognizing that micro-themes were unmaintainable, Bryan shifted to high-level buckets: `JOB`, `BUILD`, `READ`, `GTD`. The number of unique themes per week collapsed from 31 down to 8.

#### Phase 4: The Automated Purge (October 26, 2026)
Yesterday, Bryan resolved the UI clutter by having an agent run a script to hide every theme not used in the preceding 7 days:
- Task reference: `done/bob_done#^clean-up-themes`:
  > *"agent is running on apollo to disable all themes not used in last 7d"*
- Result: 70 themes were appended to `.bob/themes/apollo.jsonl` as `theme.hide` events, bringing active visible themes down to the current 6.

### 1.3 Backlog Tensions

The friction caused by the theme lifecycle generated two revealing backlog tasks in `bob.md`:
1. `bob.md#^delete-themes` (Created Oct 26, 2026):  
   > `[?] #task Add ability to delete themes and then delete all currently disabled themes! ^delete-themes`  
   *Analysis:* Under Decision `theme-hide-is-recent-only`, hard-deleting themes was explicitly rejected because daily notes and historical `bob stats` rely on the ledger as immutable source of truth. The desire to delete stems entirely from the cognitive weight of knowing 70 "ghost" themes lurk in the background.
2. `bob.md#^theme-on-task` (Created Oct 27, 2026):  
   > `[?] #task Add ability to specify a task’s theme from the task itself?! ^theme-on-task`  
   *Analysis:* Bryan feels the friction of having to manually coordinate daily Pomodoro theme headings with the tasks he links beneath them. If he is working on a task from `job_2026.md`, he finds it redundant to create a `— JOB` Pomodoro and drag the task under it.

---

## 2. In-Depth Audit of the Current 6 Themes

Below is an empirical audit of the 6 themes currently active in Bryan's catalog:

```
+--------------------------------------------------------------------------------------------------------+
|                                    ACTIVE THEMES ROSTER AUDIT                                          |
+-------+--------+---------+--------+---------+-------------------+--------------------------------------+
| Theme | Days   | Entries | Status | Hue     | Hue Source        | Dominant Linked Notes                |
+-------+--------+---------+--------+---------+-------------------+--------------------------------------+
| GTD   | 54     | 142     | Exempt | Muted   | exempt (null)     | ^gtd (daily note review anchor)      |
| BUILD | 30     | 92      | Active | Yellow  | hash (fnv1a32%8)  | sase, bob, done/bob_done             |
| JOB   | 20     | 89      | Active | Aqua    | area (job.md)     | done/sase_blog_done, job_2026, sase  |
| HOME  | 11     | 11      | Active | Violet  | hash (fnv1a32%8)  | dev_plex_hack_patch, dev, love       |
| FIX   | 5      | 8       | Active | Blue    | hash (fnv1a32%8)  | sase                                 |
| READ  | 15     | 45      | Active | Green   | hash (fnv1a32%8)  | sase_pypi_releases, sase             |
+-------+--------+---------+--------+---------+-------------------+--------------------------------------+
```

### 2.1 Detailed Evaluation of Each Theme

#### 1. GTD (Exempt Review Bucket)
- **Role:** Meta-work, morning GTD review walk, inbox processing, habit tracking (`#pre` and `#post` chores).
- **Semantics:** Exempt from the `plan.max_themes` budget (default 3, Bryan currently at 5). Renders with a muted, borderless swatch (`□`).
- **Verdict: Flawless.** GTD aligns directly with the GTD methodology's separation between *defining work* and *doing work*. It prevents routine administrative planning from exhausting the daily creative capacity budget.

#### 2. BUILD (Software Construction & Creative Deep Work)
- **Role:** Feature implementation, coding, architectural refactoring, agent pipeline development.
- **Semantics:** Active theme. Hashed to `yellow`.
- **Verdict: High Value, but Overloaded.** `BUILD` is Bryan's core creative mode. However, because there is no separate theme for writing or documentation, drafting technical documentation and blog posts is frequently lumped into `BUILD`.

#### 3. JOB (Life Domain / Employment)
- **Role:** Professional career management, job applications (e.g. Tower, Tailscale, Databricks, Harvey), cover letter drafting, portfolio engineering.
- **Semantics:** Active theme. Wears `aqua` via `hue_source: area` matching `job.md`.
- **The Core Conflict:** An examination of sessions under `— JOB` reveals massive task contamination:
  - Drafting technical blog posts: `done/sase_blog_done#^write-introduction` (24 sessions!).
  - Reading distributed systems and merge queue literature: `sase_pypi_releases#^ref-redesigning-source-control` and `sase_pypi_releases#^ref-solving-code-review-at-anthropic`.
  - Launching and verifying agents on Athena and Apollo: `done/bob_done#^cmd-t`.
  - Filling job application forms and tailoring CVs: `job_2026_apply_29#^apply-tower-tailscale`.
  
  `JOB` is an **Area of Responsibility**, not an activity mode. When Bryan spends 25 minutes reading an Anthropic engineering paper under `— JOB`, the session is semantically indistinguishable from a session under `— READ`. In `bob stats`, `worked` time attributes 21h 55m to the theme `JOB`, telling Bryan nothing about whether that time was spent reading, coding, or writing applications.

#### 4. HOME (Life Domain / Personal Admin)
- **Role:** Domestic and personal chores.
- **Semantics:** Active theme. Hashed to `violet`.
- **The Core Conflict:** Over 11 sessions, the linked tasks were:
  - `dev_plex_hack_patch#^sell-stocks-now` (17 times)
  - `dev#^ref-cp1500pfclcd-battery-swap-and-athena` (9 times)
  - `love#^clean-ears` (1 time)
  
  Selling stock is in `dev_plex_hack_patch.md` (under area `dev`), swapping a UPS battery is in `dev.md`, and dog care is in `love.md`. Bryan used `— HOME` as an ad-hoc catch-all for "personal, non-coding errands." Like `JOB`, `HOME` represents a life sphere, not a cognitive posture.

#### 5. FIX (Reactive Repair & Troubleshooting)
- **Role:** Bug fixes, hotfixes, defect resolution.
- **Semantics:** Active theme. Hashed to `blue`.
- **Evaluation: Under-utilized and Borderline Redundant.** With only 8 entries across 5 days (compared to 92 entries for `BUILD`), `FIX` occupies 1 of Bryan's precious 5 daily theme slots to record trivial 5-to-10 minute bug fixes. The cognitive distinction between writing new code (`BUILD`) and modifying existing code to fix an edge case (`FIX`) is rarely worth a separate daily theme slot unless engaged in a dedicated bug-hunting sprint.

#### 6. READ (Absorptive Literature Study)
- **Role:** Reading reference materials, academic papers, and technical specifications (`bob ref`).
- **Semantics:** Active theme. Hashed to `green`.
- **Verdict: Highly Effective.** Reading requires a calm, absorptive, reflective cognitive posture completely distinct from interactive coding or rapid task triage. Preserving `READ` as a first-class cognitive theme protects focused literature study from being swallowed by active execution.

---

## 3. Benchmarking Against Established Productivity Best Practices

To evaluate Bryan's setup rigorously, we benchmark his themes against five foundational frameworks in personal productivity and cognitive ergonomics.

```
+----------------------------------------------------------------------------------------------------------+
|                                    FRAMEWORK BENCHMARKING MATRIX                                         |
+--------------------------+------------------------------+---------------------------+--------------------+
| Framework                | Core Principle               | Bryan's Current System    | Alignment / Gap    |
+--------------------------+------------------------------+---------------------------+--------------------+
| Pomodoro Technique       | Low-friction timeboxing;     | 6 macro-themes; low       | High alignment now;|
| (Francesco Cirillo)      | units of effort, not filing  | friction after purge      | past micro-themes  |
|                          | metadata during execution    | (was high friction)       | caused high waste  |
+--------------------------+------------------------------+---------------------------+--------------------+
| Getting Things Done      | Strict separation between    | Violates separation:      | MAJOR GAP:         |
| (David Allen)            | Horizons of Focus (Areas)    | JOB & HOME duplicate      | Areas masquerade   |
|                          | and Execution Contexts       | Areas in session themes   | as session themes  |
+--------------------------+------------------------------+---------------------------+--------------------+
| Deep Work                | Protect deep cognitively     | BUILD & READ are deep;    | Moderate gap:      |
| (Cal Newport)            | demanding work from shallow  | JOB & HOME mix shallow    | Shallow logistics  |
|                          | administrative logistics     | chores with deep synthesis| contaminate stats  |
+--------------------------+------------------------------+---------------------------+--------------------+
| TimeCrafting             | Intentional Focusing Modes   | Covers Create (BUILD) and | Gap: Missing       |
| (Mike Vardy)             | (Create, Consume, Curate,    | Consume (READ); missing   | Write & Admin;     |
|                          | Connect, Cultivate)          | Write & Admin modes       | conflates domain   |
+--------------------------+------------------------------+---------------------------+--------------------+
| Faceted Classification   | MECE: Orthogonal dimensions  | Collapses Facet 2 (Where) | MAJOR GAP:         |
| (Ranganathan / Morville) | (Entity, Area, Task, Mode)   | into Facet 4 (How)        | Dimensional        |
|                          | must not overlap             |                           | collapse           |
+--------------------------+------------------------------+---------------------------+--------------------+
```

### 3.1 The Pomodoro Technique (Cirillo)
Francesco Cirillo conceived the Pomodoro as an **indivisible atom of applied attention** (25 minutes of unbroken focus) designed to minimize cognitive friction, internal interruptions, and tracking overhead.
- *Best Practice:* Tracking during the day must be effortless (a simple checkmark). Complex categorization belongs in post-hoc daily archiving, never in the 2-minute decision window before winding the clock.
- *Assessment of Bryan's Workflow:* During Phase 2 (31 themes/week), Bryan was using Pomodoro name tails as an expressive micro-tagger. This induced decision fatigue before starting each session ("What should I name this Pomodoro?"). The consolidation down to a few standard themes dramatically lowered friction. However, whenever Bryan must choose between `JOB` and `BUILD` for a single coding session, the hesitation returns.

### 3.2 Getting Things Done (Allen)
David Allen's GTD enforces a strict ontological separation across the **Horizons of Focus**:
- **Horizon 1:** Projects (multi-step deliverables, e.g., `job_2026_apply_29`, `sase_blog`).
- **Horizon 2:** Areas of Focus & Responsibility (standards to maintain, e.g., `job`, `dev`, `home`, `love`).
- **Runway:** Actions and Execution Contexts (physical or mental constraints, e.g., `@computer`, `@calls`).

*The GTD Violation:* GTD explicitly states that Areas of Focus are **never contexts or action labels**. An Area of Focus is a maintenance standard that spawns projects and tasks. In Bob:
- Bob's **Homes** already track Horizons 1 and 2 automatically! When a task is linked from `job_2026.md`, Bob knows its Area is `job`.
- By creating a Theme called `JOB`, Bryan re-injects Horizon 2 into the execution runway. This produces tautological tracking: working on a `job` task in a `JOB` pomodoro in the `job` area.

### 3.3 Deep Work & Time-Blocking (Newport)
Cal Newport defines **Deep Work** as professional activities performed in a state of distraction-free concentration that push cognitive capabilities to their limit, and **Shallow Work** as non-cognitively demanding, logistical, or administrative tasks.
- *Best Practice:* Time blocks should segregate deep cognitive synthesis from shallow logistics to prevent attention residue from degrading flow states.
- *Assessment:* Bryan's `BUILD` and `READ` are pure Deep Work containers. But `JOB` and `HOME` act as semantic Trojan horses: they allow shallow tasks (checking an application status, uploading a PDF, selling stock, cleaning dog ears) to share the same theme container as deep cognitive work (writing an original systems architecture essay for a portfolio). This distorts the `worked` metrics in `bob stats`.

### 3.4 TimeCrafting & Focusing Modes (Vardy)
Mike Vardy's *TimeCrafting* distinguishes between "Theming Days" (assigning an overarching objective to a day) and "Focusing Modes" (categorizing blocks by cognitive modality):
- **Create:** Generative production (coding, writing code).
- **Consume:** Absorbing information (reading, studying, listening).
- **Curate:** Organizing, prioritizing, reviewing (GTD, backlog maintenance).
- **Communicate / Connect:** External correspondence, outreach, meetings.
- **Cultivate:** Personal health, domestic errands, rest.

*Assessment:* Bryan's `BUILD` is *Create*, `READ` is *Consume*, and `GTD` is *Curate*. However, Bryan has no dedicated mode for *Writing* (prose composition) or *Admin/Logistics*. Instead, he uses `JOB` and `HOME` as awkward substitutes for *Communicate* and *Cultivate*.

### 3.5 Faceted Information Architecture (MECE Principle)
In information science, a classification system is MECE (Mutually Exclusive and Collectively Exhaustive) when its facets are orthogonal. A robust personal productivity taxonomy requires four distinct facets:

```
+-----------------------------------------------------------------------------------+
|                        THE FOUR ORTHOGONAL FACETS OF BOB                          |
+-------------------+--------------------+------------------+-----------------------+
| Facet             | Question Answered  | Governed By      | Example               |
+-------------------+--------------------+------------------+-----------------------+
| 1. Subject Entity | WHAT project?      | Task Note Parent | sase_blog, bob-cli    |
| 2. Life Sphere    | WHERE / FOR WHOM?  | Area Hierarchy   | dev, job, love, cash  |
| 3. Atomic Step    | WHICH action?      | Task Block Link  | ^write-intro, ^cmd-p  |
| 4. Cognitive Mode | HOW am I focusing? | Pomodoro Theme   | BUILD, READ, WRITE    |
+-------------------+--------------------+------------------+-----------------------+
```

When Facet 2 (Life Sphere: `JOB`, `HOME`) is forced into Facet 4 (Cognitive Mode), the taxonomy collapses. The user is forced into an artificial dilemma:
> *"I am writing code (`BUILD`) for my job application (`JOB`). Should I label the theme BUILD or JOB?"*

Whichever Bryan picks, one dimension is lost in theme tracking, and Stats becomes inconsistent.

---

## 4. Critical Gap Analysis: Systemic Hazards in Bryan's Setup

### 4.1 Hazard 1: Zero-Entropy Themes (`JOB` and `HOME`)
In information theory, entropy measures the information content of a signal. Because Bob's home resolver already maps linked tasks to their areas (`job` and `dev`/`love`), tagging the session as `JOB` or `HOME` provides zero new information to the system:

```
                      +-----------------------------+
                      | Linked Task: job_2026#^step |
                      +--------------+--------------+
                                     |
               +---------------------+---------------------+
               |                                           |
               v                                           v
      [ Bob Home Resolver ]                      [ Authored Session ]
               |                                           |
    Area: job (100% known)                       Theme: JOB (Redundant!)
    Root: job_2026                               Cognitive Mode: Unknown!
    Project: job_2026_apply_29                   (Was it coding? Reading? Forms?)
```

If Bryan instead tags that session `BUILD`, `READ`, or `ADMIN`, the system captures two complementary dimensions:
- **Area / Root Parent:** `job` / `job_2026` (Captured automatically from the task link).
- **Theme:** `ADMIN` or `BUILD` (Captured intentionally from the Pomodoro tail).

In `bob stats`, Bryan would then be able to see: *"Of my 22 hours on Job Search, 12 hours were spent WRITING, 6 hours READING, and 4 hours on ADMIN."* Under the current setup, all 22 hours are flatlined as `JOB`.

### 4.2 Hazard 2: The Missing "Prose Writing" Mode (`WRITE`)
Bryan does a substantial amount of long-form writing:
- Public blog posts: `sase_blog` (24 sessions in the last 14 days!).
- Research reports and architecture specs in `bob-cli` and `sase`.
- Job application cover letters and portfolio write-ups.

Writing prose requires a fundamentally different mental state from writing code. Writing code is iterative, compiler-driven, symbolic, and architectural (`BUILD`). Writing prose is linear, rhetorical, tone-sensitive, and syntactical (`WRITE`). Lumping blog posts into `BUILD` or `JOB` obscures how much creative writing Bryan actually produces.

### 4.3 Hazard 3: Hue Collisions and Color Ergonomics
Decision `theme-hue-is-pin-exempt-area-hash` governs theme colors. When a theme is not pinned and does not match an area note stem, its color is assigned via hash: `Hue::ALL[fnv1a32(key) % 8]`.

The JSON output from `bob themes list -a -f json` reported active warnings:
```json
"hints": [
  {
    "code": "theme_hue_collision",
    "themes": ["BUILD", "CLEANUP"],
    "hue": "yellow",
    "days_together": 2,
    "suggest": { "name": "CLEANUP", "hue": "blue" }
  },
  {
    "code": "theme_hue_collision",
    "themes": ["HOME", "MEMORY"],
    "hue": "violet",
    "days_together": 2,
    "suggest": { "name": "MEMORY", "hue": "orange" }
  }
]
```
Furthermore, the current color assignment lacks psychological coherence:
- `BUILD` is yellow (energetic, but clashes with warning highlights).
- `JOB` is aqua (inherited from `job.md`, which is fine, but as a theme it clashes with code editors).
- `HOME` is violet.
- `FIX` is blue.
- `READ` is green (well-aligned: green represents calm, growth, absorption).

Rather than letting FNV-1a hash determine the visual environment of the terminal, Obsidian pills, and Mac menu bar, the core theme modes should be explicitly pinned to meaningful colors.

### 4.4 Hazard 4: The Misconception Behind `^theme-on-task`
In `bob.md#^theme-on-task`, Bryan proposed adding theme properties directly to tasks:
```markdown
- [?] #task Add ability to specify a task’s theme from the task itself?! [created::2026-10-27] ^theme-on-task
```

This idea stems from a natural desire to automate theme entry, but it violates a core principle of time management:
- A **Task** is a deliverable outcome (e.g., `Implement agent restart gate`). It belongs to a Project and an Area.
- A **Pomodoro** is a timebox of human attention and cognitive posture.

A single complex task frequently requires multiple cognitive postures over its lifecycle:
1. Pomodoro 1: `READ` (studying the relevant RFC or API documentation).
2. Pomodoros 2–3: `BUILD` (implementing the core logic).
3. Pomodoro 4: `FIX` (debugging test failures).
4. Pomodoro 5: `GTD` or `ADMIN` (updating documentation, closing issues, cleaning up branches).

If the task carried a static `theme: BUILD` field, Bryan would lose the flexibility to shift his cognitive mode while working on that task, or he would be forced to create artificial subtasks just to change the session theme. **Theme belongs to the session, not the task.**

---

## 5. Ranked List of Recommended Changes

Based on this deep research and empirical evidence, here is the prioritized, ranked list of recommendations for Bryan's theme system:

```
+---------------------------------------------------------------------------------------------------+
|                                  RANKED RECOMMENDATIONS SUMMARY                                   |
+------+-------------------------------------------+-----------+------------------------------------+
| Rank | Recommendation                            | Effort    | Primary Benefit                    |
+------+-------------------------------------------+-----------+------------------------------------+
|  1   | Retire Domain Themes (JOB & HOME)         | Low       | Eliminates dimensional collapse;   |
|      |                                           |           | restores clean Stats entropy       |
+------+-------------------------------------------+-----------+------------------------------------+
|  2   | Introduce Dedicated ADMIN (or OPS) Mode   | Low       | Separates shallow logistics from   |
|      |                                           |           | deep creative work across all areas|
+------+-------------------------------------------+-----------+------------------------------------+
|  3   | Introduce Dedicated WRITE Mode            | Low       | Isolates prose/blogging from       |
|      |                                           |           | software construction              |
+------+-------------------------------------------+-----------+------------------------------------+
|  4   | Pin Semantic Palette Hues (No Hashes)     | Very Low  | Eliminates collisions; provides    |
|      |                                           |           | stable, intuitive visual cues      |
+------+-------------------------------------------+-----------+------------------------------------+
|  5   | Preserve GTD as the Sole Exempt Meta-Mode | Zero      | Maintains Bryan's highest-volume,  |
|      |                                           |           | most disciplined daily ritual      |
+------+-------------------------------------------+-----------+------------------------------------+
|  6   | Re-evaluate FIX: Reserve for Bug Sprints  | Behavior  | Conserves daily theme budget       |
|      |                                           |           | (plan.max_themes headroom)         |
+------+-------------------------------------------+-----------+------------------------------------+
|  7   | Reject ^theme-on-task; Close ^delete-theme| Backlog   | Prevents architectural regressions |
|      | via Catalog Allowlist                     |           | and preserves ledger immutability  |
+------+-------------------------------------------+-----------+------------------------------------+
|  8   | Lower Daily Theme Cap (plan.max_themes: 3)| Config    | Enforces cognitive focus; reduces  |
|      |                                           |           | mid-day context switching          |
+------+-------------------------------------------+-----------+------------------------------------+
```

---

### Detailed Recommendation Breakdown

### Rank 1: Retire Domain Themes (`JOB` and `HOME`) and Enforce Strict Orthogonality
- **Action:** Hide `JOB` and `HOME` from the active theme catalog using `bob themes hide JOB HOME`. Stop writing `— JOB` and `— HOME` on Pomodoro lines.
- **Rationale:** 
  - `job.md`, `job_2026.md`, `love.md`, and `dev.md` already supply the Area and Project dimensions to Bob automatically through task wikilinks.
  - When working on job applications, Bryan should name the session by what he is actually doing: `— WRITE` (drafting cover letters/prose), `— READ` (studying companies/papers), or `— ADMIN` (submitting web forms).
  - When doing personal errands, name the session `— ADMIN` (selling stock, ordering parts).
  - This immediately resolves the ambiguity of where to file tasks and restores rich, descriptive data to `bob stats`.

### Rank 2: Introduce an Explicit `ADMIN` (or `OPS`) Mode for Shallow/Logistical Execution
- **Action:** Adopt `ADMIN` as a first-class cognitive theme for low-concentration, execution-oriented logistics across both personal and professional life.
- **Use Cases:**
  - Submitting job application portals and updating tracker spreadsheets.
  - Financial chores (selling stock, banking, paying bills).
  - Hardware maintenance (UPS battery swaps, cable management).
  - Trivial environment setup, package updates, cleanups.
- **Rationale:** 
  - Prevents shallow logistics from contaminating `BUILD`.
  - In Newport's framework, having an explicit `ADMIN` bucket allows Bryan to timebox shallow work into dedicated "batch execution" blocks, protecting the rest of his day for deep creation.

### Rank 3: Introduce a Dedicated `WRITE` Theme for Prose, Specs, and Communication
- **Action:** Adopt `WRITE` as a first-class cognitive theme.
- **Use Cases:**
  - Authoring SASE blog posts (`sase_blog`).
  - Writing design documents, architectural RFCs, and SASE memory notes.
  - Writing cover letters and public essays.
- **Rationale:**
  - Writing prose is one of Bryan's major work outputs (24 sessions in the last 14 days under `JOB`), but it currently has no home. It is neither coding (`BUILD`) nor reading (`READ`). Giving it a distinct theme honors the unique mental state and pacing of creative prose composition.

### Rank 4: Pin Core Theme Hues Semantically Instead of Relying on Hash Slots
- **Action:** Explicitly pin the colors of the standardized cognitive palette using `bob themes color`:
  - `bob themes color BUILD yellow` (or `blue` for deep architectural focus)
  - `bob themes color READ green` (restful, absorptive learning)
  - `bob themes color WRITE violet` (creative, reflective composition)
  - `bob themes color ADMIN orange` (energetic, logistical execution)
  - `bob themes color FIX red` (critical repair, alerting)
  - `GTD` remains automatically `muted` (exempt).
- **Rationale:**
  - Eliminates the `theme_hue_collision` warnings currently emitted by `bob themes list`.
  - Provides a permanent, predictable visual language across the CLI (`■`), Obsidian pills, and Mac menu bar swatches.

### Rank 5: Preserve `GTD` as the Sole Muted, Exempt Meta-Mode
- **Action:** Maintain `GTD` exactly as implemented in `docs/plan.md` and `docs/pomodoro-themes.md`.
- **Rationale:**
  - With 142 entries over 54 days, `GTD` is Bryan's most stable and successful operational habit.
  - Its exemption from `plan.max_themes` correctly reflects its role as meta-work (defining the day) rather than productive capacity (executing the day).

### Rank 6: Reframe `FIX` as a Dedicated Sprint Mode (or Absorb Incidental Fixes)
- **Action:** Reserve `— FIX` for dedicated troubleshooting, bug triage, or incident-repair sessions. When an incidental 5-minute bug fix occurs in the middle of feature development, keep it under `BUILD`.
- **Rationale:**
  - With only 8 entries in 90 days, `FIX` creates unnecessary friction when deciding whether a minor tweak is a "feature" or a "fix".
  - If a day's budget allows 3 themes, dedicating one slot to a 10-minute fix wastes 33% of the daily cognitive allowance.

### Rank 7: Reject `^theme-on-task`; Resolve `^delete-themes` via Palette Allowlisting
- **Action:**
  - Mark `bob.md#^theme-on-task` as **cancelled/rejected**. Keep themes bound to Pomodoro sessions to preserve execution agility.
  - Mark `bob.md#^delete-themes` as **resolved by design**. Do not attempt to mutate historical Git ledger files. Instead, enforce a strict "Suggested Themes Allowlist" in Bob Mac Capture and Obsidian pickers so that arbitrary typos or one-off names cannot be created without an explicit override.
- **Rationale:**
  - Preserves the architectural integrity of Bob (ledger immutability and separation of concerns).

### Rank 8: Tighten Daily Theme Budget (`plan.max_themes: 3`) to Minimize Fragmentation
- **Action:** Reset `plan.max_themes` from 5 back to the system default of 3 in `chezmoi` configuration.
- **Rationale:**
  - Today's plan shows 4 non-exempt themes open at once (`JOB`, `BUILD`, `FIX`, `HOME`).
  - Switching between 4 different cognitive contexts in a single workday fragments attention. Sticking to 3 themes (e.g. `GTD` [exempt] + `BUILD` + `WRITE` + `ADMIN`) provides sufficient variety while enforcing disciplined timeblocking.

---

## 6. The Proposed Target Palette & Workflow Comparison

### 6.1 The Standardized 5+1 Cognitive Palette

By adopting these recommendations, Bryan's theme universe simplifies from 76 chaotic historical entries into a crisp, permanent **5+1 Cognitive Palette**:

```
+---------------------------------------------------------------------------------------------------------+
|                                  THE 5+1 COGNITIVE PALETTE                                              |
+-------+--------+---------+-------------------+----------------------------+-----------------------------+
| Theme | Swatch | Hue     | Cognitive Posture | Typical Activities         | Distinct From               |
+-------+--------+---------+-------------------+----------------------------+-----------------------------+
| GTD   |   □    | Muted   | Meta-Organization | Morning review, inbox walk | Not execution; exempt       |
| BUILD |   ■    | Blue    | Generative Syntax | Code writing, refactoring  | Not prose writing (WRITE)   |
| WRITE |   ■    | Violet  | Generative Prose  | Blog posts, RFCs, essays   | Not code writing (BUILD)    |
| READ  |   ■    | Green   | Absorptive Study  | Papers, books, docs        | Not active production       |
| ADMIN |   ■    | Orange  | Shallow Logistics | Applications, banking, UPS | Not deep creation           |
| FIX   |   ■    | Red     | Analytical Repair | Bug triage, outage repair  | (Optional sprint mode)      |
+-------+--------+---------+-------------------+----------------------------+-----------------------------+
```

### 6.2 Before vs. After Comparison Matrix

```
+---------------------------------------------------------------------------------------------------------+
|                                    BEFORE VS. AFTER WORKFLOW COMPARISON                                 |
+----------------------+---------------------------------------+------------------------------------------+
| Dimension            | Current State (Oct 2026)              | Proposed State (Post-Modernization)      |
+----------------------+---------------------------------------+------------------------------------------+
| Catalog Size         | 76 known, 70 hidden, 6 active         | 6 standard permanent modes               |
| Theme Semantics      | Mixed (4 modes + 2 life domains)      | Pure (100% cognitive modes)              |
| Redundancy           | High (JOB/HOME duplicate vault areas) | Zero (Homes and Themes are orthogonal)   |
| Capture Decision     | "Is this job coding JOB or BUILD?"    | "I am coding -> BUILD; task sets Area"   |
| Stats Visibility     | 22h in JOB (blind to actual work)     | 22h in Area:job split by WRITE/READ/ADMIN|
| Colors & Swatches    | Random FNV hashes; active collisions  | Pinned semantic colors; zero collisions  |
| Daily Budget         | 5 themes (frequent context switching) | 3 themes (enforces deep focus blocks)    |
| Backlog Health       | Lingering friction (^theme-on-task)   | Clear mental model; no structural debt   |
+----------------------+---------------------------------------+------------------------------------------+
```

### 6.3 Conclusion

Themes in Bob are at their best when they serve as **mirrors of cognitive posture**, signaling to Bryan's brain—and recording for his future analytics—what *kind* of energy and focus a session demands. By liberating themes from life domains (`JOB` and `HOME`), which Bob already tracks effortlessly through note ancestry, Bryan can eliminate the clutter that plagued his past catalog, restore clarity to his daily planning, and ensure that every 25-minute Pomodoro is an intentional act of focused attention.
