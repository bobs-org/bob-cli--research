# Architectural Research: Periodic Note Hierarchy, Generalized Stats Strips, and Autonomous Agent Enrichment

**Author**: Researcher `gem` (5-Researcher Swarm)  
**Date**: November 3, 2026  
**Status**: Completed Research & Proposed Specification  
**Target Repository**: `bob-cli` / `bob-plugins` / Bob Vault (`~/bob/`)  

---

## 1. Executive Summary

Bryan's personal knowledge and task management vault (`~/bob/`) currently anchors daily notes (`YYYY/YYYYMMDD.md`) to a bare monthly file (`YYYY/YYYYMM.md`) that employs no template or visual summaries. The existing daily review workflow benefits from a sophisticated, compact, read-only UI component known as the **Day Strip** (rendered inside the `bob-plan` code block), which summarizes daily metrics, comparative baselines, and working-time distributions across Root Parents and Task Types. However, no corresponding visual or structural apparatus exists for weekly, quarterly, yearly, or all-time review cadences.

This research formulates an end-to-end architecture to:
1. **Restructure Periodic Note Genealogy**: Transition daily notes to link to **Weekly Notes** (`YYYY/YYYY-Www.md`), which link to **Quarterly Notes** (`YYYY/YYYY-Qq.md`), which link to **Yearly Notes** (`YYYY.md`), which link to a new **All-Time Note** (`all_time.md`), which finally terminates at the master structure note (`org.md`).
2. **Generalize the Day Strip into a Universal "Stats Strip"**: Elevate the design pattern of the Day Strip into a polymorphic visual component (`bob-stats-strip`) applicable to any periodic note, featuring:
   - A standardized **Headline Fact Grid** (Worked time, Pomodoro sessions, Tasks done, Tasks created, Net flow, and Habit/Review compliance).
   - Proportional **Working Time Distribution Bars** (Root Parent and Task Type lanes).
   - A dedicated **Sub-Unit Composition Breakdown** (e.g., daily breakdown for weeks, weekly breakdown for quarters, quarterly breakdown for years) with interactive links directly to constituent notes.
3. **Embed Pre-Configured Agent Enrichment Instructions**: Implement a zero-clutter prompting architecture using collapsed Obsidian callouts (`> [!info|instructions]- Agent Enrichment Instructions`) pre-baked into periodic templates. This enables autonomous LLM agents to execute comprehensive retrospectives, task portfolio audits, and next-horizon intention drafting with zero external prompting overhead.
4. **Synchronize GTD Review Chore Workflows**: Upgrade the weekly review chore in `~/bob/gtd_daily.md` and introduce quarterly and annual review recurring tasks to establish an unbroken rhythm across all GTD Horizons of Focus.
5. **Establish Formal SASE Glossary Canon**: Add the new glossary strand `stats-strip.md`, rigorously defining its interface contract and relations to `day-strip`, `stats-dash`, `root-parent`, and `task-type`.

---

## 2. Critical Evaluation & Plan Critique

### 2.1 The Omitted Month: Is Skipping Monthly Notes a Good Idea?

The proposed hierarchy intentionally omits monthly notes:
$$\text{Daily} \longrightarrow \text{Weekly} \longrightarrow \text{Quarterly} \longrightarrow \text{Yearly} \longrightarrow \text{All-Time} \longrightarrow \text{Org}$$

#### The Mathematical & Structural Superiority
In traditional calendar systems, weeks and months are fundamentally misaligned:
- A week is strictly $7$ days. A month varies between $28$ and $31$ days ($\approx 4.28$ to $4.43$ weeks).
- Almost every month begins or ends mid-week. If daily notes link to weeks, and weeks link to months, **Week 44 (Oct 26 – Nov 1)** straddles October and November. Which month does Week 44 link to? If it links to October, November 1st has an ancestor chain claiming it is part of October. If weeks are split into fractional sub-weeks, weekly rhythm and Pomodoro momentum tracking are severed.
- **In contrast, ISO 8601 weeks nest cleanly into 13-week Quarters**:
  $$\text{Q1} = \text{W01} \dots \text{W13} \quad (13\text{ weeks})$$
  $$\text{Q2} = \text{W14} \dots \text{W26} \quad (13\text{ weeks})$$
  $$\text{Q3} = \text{W27} \dots \text{W39} \quad (13\text{ weeks})$$
  $$\text{Q4} = \text{W40} \dots \text{W52} \quad (13\text{ weeks, } 14\text{ in 53-week years})$$
  Under this model:
  $$\text{Quarter}(\text{week}) = \left\lceil \frac{\text{week}}{13} \right\rceil$$
  Every single day belongs to exactly one ISO week, every ISO week belongs to exactly one ISO quarter, and every ISO quarter belongs to exactly one ISO year. **The note graph forms a strict, unambiguous, cycle-free tree.**

#### The GTD & Human Rhythm Alignment
From a productivity methodology standpoint (David Allen's *Getting Things Done* and Brian Moran's *The 12-Week Year*):
- **The Week** is the fundamental operational execution sprint. It is short enough to hold tactical commitments and long enough to see tangible progress.
- **The Quarter (12–13 Weeks)** is the optimal strategic execution horizon for OKRs, major product versions, and habit transformations.
- **The Month** is historically an administrative artifact (billing cycles, salary, rent). As a review horizon, a month is too long for tactical course correction and too short for major strategic shifts.

#### Caveats & Recommended Adjustment
While the primary structural tree should follow `Daily -> Weekly -> Quarterly`, calendar months still govern personal finances (mortgages, credit card statements, pay stubs).  
**Recommendation**: 
- Accept the user's plan as the primary structural and review hierarchy.
- Do not actively delete existing monthly files (`202611.md`). Treat monthly notes as *ancillary financial/logistical indices* queryable via Dataview (`type: [[month]]`), but decouple them entirely from the task and Pomodoro review tree.

---

### 2.2 The `all_time.md` -> `org.md` Integration

#### Current State in `~/bob/`
In the existing vault:
- `org.md` is the root structure note (`# G = [[log]]`).
- `log.md` links to `journal.md`.
- `journal.md` links to `2024.md`, `2025.md`, `2026.md`.
- `journal.md` declares: `All daily log files / journals are decedents [sic] of this file.`

#### Critique & Recommendation
Introducing `all_time.md` as the direct parent of yearly notes (`2024`, `2025`, `2026`) and pointing `all_time.md` to `org.md` cleanly modernizes the legacy Zorg converter hierarchy:
- `all_time.md` serves as the lifetime horizon dashboard: summarizing total years of tracked Pomodoros, aggregate lifetime hours, overarching life chapters/eras, and multi-year trajectory.
- To maintain pristine vault link integrity, `org.md` should be updated to link `# G = [[all_time]] | Lifetime log files and multi-year history`, gracefully deprecating `log.md` and `journal.md` without breaking older notes.

---

### 2.3 Visual Component Architecture: Live Code Fence vs Pre-Generated Static Text

The user requests:
> Each of these weekly/quarterly/yearly files should contain a "stats strip" that breaks down the working time for the given time period... We should try to automatically summarize the units/parts that make up the whole...

There are two primary paradigms for implementing this in Obsidian:

| Aspect | Paradigm A: Pure Live Code Fence (`bob-stats-strip`) | Paradigm B: Pure Pre-Generated Static Text | Paradigm C: Recommended Hybrid |
| :--- | :--- | :--- | :--- |
| **Mechanics** | Obsidian plugin renders dynamic HTML/Canvas on the fly from `bob stats` JSON. | A script or CLI command stamps markdown tables/figures into the file. | A dynamic `bob-stats-strip` code block at the top + structured Markdown sections below. |
| **Freshness** | **100% Real-time**: Never goes stale if older Pomodoros are edited or reconciled. | **Static**: Freezes immediately; retroactively edited Pomodoros cause permanent drift. | **Best of both**: Visual strip is always live; agent-written analysis captures reflective consensus. |
| **Obsidian UI** | **Gorgeous**: Interactive hover tooltips, smooth bar transitions, click-to-pin navigation. | **Basic**: Standard Markdown tables or static Mermaid diagrams. | **World-Class**: Live interactive visual strip paired with deep narrative prose. |
| **LLM Agent Visibility** | **Opaque**: LLMs reading raw `.md` files cannot see inside custom JS-rendered blocks without running CLI commands. | **Transparent**: LLM reads exact numbers directly from the file markdown. | **Transparent**: Pre-generated agent instructions explicitly tell the agent to run `bob stats show -r <period> -a -f json`. |
| **Portability** | Requires `bob-ledger-tools` plugin on desktop. | Renders in any Markdown reader, mobile, and GitHub. | Graceful fallback note if plugin is absent; full prose and daily links render everywhere. |

**Recommendation**: Adopt **Paradigm C (The Hybrid Architecture)**.
1. The periodic note header contains an interactive, zero-argument ````bob-stats-strip```` code block.
2. The `bob-ledger-tools` Obsidian plugin inspects the current note's frontmatter (`date` or `id`) and renders the full, responsive, beautiful Stats Strip automatically.
3. Below the visual strip, the note template supplies pre-generated markdown headings and agent prompt callouts for reflective narrative enrichment.

---

## 3. Universal "Stats Strip" Design Specification

### 3.1 Visual Anatomy of a Stats Strip

A **Stats Strip** is a compact, horizontal glance component designed to sit directly beneath the note's top title and navigation header. It adheres to a strict vertical budget ($\le 140\text{ px}$) to prevent pushing the note's body content below the fold.

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│  WORKED          SESSIONS        DONE            CREATED         NET             REVIEW / HABIT  │
│  32h 15m         78 poms         42 tasks        35 tasks        -7 tasks        6/7 days        │
│  ▲ 12% vs prior  11.1 / day      +8 vs prior     -4 vs prior     shrinking       85% met         │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│  Time by Root Parent · dev 18h 45m · gtd 6h 30m · job 4h 15m · body 2h 45m                      │
│  ████████████████████████████████████████░░░░░░░░░░░░░░░▒▒▒▒▒▒▒▒▒▒▓▓▓▓▓▓                         │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│  Time by Type · BUILD 14h 20m · PLAN 8h 10m · WRITE 5h 00m · READ 3h 15m · FIX 1h 30m           │
│  ███████████████████████████░░░░░░░░░░░░░░░░▒▒▒▒▒▒▒▒▒▒▓▓▓▓▓▓▓▓▓▓                                 │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│  Daily Breakdown (Sub-Unit Composition)                                                          │
│  Mon 4h 30m   Tue 6h 15m   Wed 5h 00m   Thu 6h 45m   Fri 5h 30m   Sat 2h 15m   Sun 2h 00m    │
│  [  ███    ]  [  █████  ]  [  ████   ]  [  ██████ ]  [  ████   ]  [  █      ]  [  █      ]    │
│  [[20261102]] [[20261103]] [[20261104]] [[20261105]] [[20261106]] [[20261107]] [[20261108]]   │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Visual Tier Breakdown

#### Tier 1: The Headline Fact Grid
A responsive horizontal grid of 5–6 core metric cards, separated by subtle hairline vertical rules (`--background-modifier-border`):
1. **WORKED**: Total on-clock Pomodoro duration (e.g. `32h 15m`). Quiet comparison baseline underneath displaying percentage delta vs. prior period (e.g. `▲ 12% vs prior week`).
2. **SESSIONS**: Total count of closed Pomodoros (e.g. `78`), with daily average underneath (e.g. `11.1 / day`).
3. **DONE**: Non-recurring completed tasks closed during the period (e.g. `42 tasks`).
4. **CREATED**: New tasks captured during the period (e.g. `35 tasks`).
5. **NET FLOW**: Net backlog change (`created - done - dropped`), displaying sign and directional color (green for negative/shrinking backlog, red for positive/expanding backlog).
6. **CADENCE / HABITS**:
   - For Weekly: Morning review completion ratio (e.g. `6/7 days met`).
   - For Quarterly: Weekly review completion ratio (e.g. `12/13 weeks`).
   - For Yearly: Quarterly review completion count (e.g. `4/4 quarters`).

#### Tier 2: Distribution Lanes (Where the Time Went)
Identical to the acclaimed Day Strip design system:
- **Root Parent Lane**: Proportional full-width stacked horizontal bar mapping minutes to top-level life areas (`dev`, `gtd`, `job`, `body`, `personal`). Each segment takes the canonical area/project hue.
- **Task Type Lane**: Proportional horizontal bar mapping minutes to task themes (`BUILD`, `PLAN`, `WRITE`, `READ`, `FIX`, `MEET`).
- **Interactive Legend**: Displays swatch/dot, uppercase category label, and formatted duration. Hovering dims non-matching segments; clicking reveals that slice in `dash_stats.md`.

#### Tier 3: Sub-Unit Composition Breakdown (Automatic Unit Summarization)
This directly fulfills the user's requirement:
> We should try to automatically summarize the units/parts that make up the whole of each of these files. For example, quarterly files should ideally show some kind of breakdown of each week.

The sub-unit breakdown provides an intuitive micro-visualization representing the child notes that constitute the current horizon:
- **Weekly Strip (7 Days)**:
  - 7 mini columns: Monday through Sunday.
  - Each column shows: Day of week, worked duration, a miniature proportional vertical bar (spark-bar), and a direct clickable Obsidian internal link `[[2026/20261103|Tue 11-03]]`.
  - Today is subtly highlighted; days with zero tracked time render a quiet dashed outline.
- **Quarterly Strip (13 Weeks)**:
  - 13 mini columns: `W01` through `W13`.
  - Each column displays the week number, worked hours, a spark-bar indicating relative weekly volume, and a direct link to that weekly note `[[2026/2026-W45|W45]]`.
  - Provides instant glanceability of sprint velocity consistency across the quarter.
- **Yearly Strip (4 Quarters / 12 Months)**:
  - 4 major quarter panels (or 12 monthly mini-bars), showing quarterly totals, percentage of annual output, and links to `[[2026/2026-Q1]]` through `[[2026/2026-Q4]]`.
- **All-Time Strip (Tracked Years)**:
  - Discrete annual blocks (e.g. `2023`, `2024`, `2025`, `2026`), depicting multi-year scaling and lifetime hours.

---

## 4. Note Templates & Prompt Engineering for Autonomous Agent Enrichment

### 4.1 The Prompt Delivery Mechanism: Collapsible Obsidian Callouts

A critical design challenge is ensuring that when an LLM agent is asked to enrich or review a periodic note, it has **complete, unambiguous instructions embedded right inside the file**, while ensuring that human reading experience in Obsidian remains completely clean.

The optimal solution is Obsidian's **Collapsible Callout syntax with a folded default (`-`)**:
```markdown
> [!info|instructions]- 🤖 Agent Enrichment Instructions (Click to expand)
> When prompted to review or enrich this note:
> 1. Run `bob stats show -r <period> -a -f json`...
> 2. Inspect constituent child notes...
```

**Why this is world-class design**:
1. **Zero UI Noise for Bryan**: In Obsidian Reading View and Live Preview, a callout with `]-` renders as a sleek, single-line collapsed pill (`🤖 Agent Enrichment Instructions`). It consumes zero vertical space and hides all instruction boilerplate.
2. **100% Legibility for AI Agents**: LLMs interact with markdown files as raw text streams. When an agent reads the file via `read_file` or a CLI read, it sees the complete, un-truncated instruction text immediately.
3. **Zero Configuration**: Any agent launched via SASE, Antigravity, or terminal CLI can simply be told: `"Enrich 2026-W45.md"`. The agent opens the file, reads its self-contained marching orders, runs the audited tools, and fills out the templated sections.

---

### 4.2 Comprehensive Note Templates

#### 4.2.1 Daily Template Update (`~/bob/_templates/daily.md`)
Modify the existing `parent` frontmatter token so newly spawned daily notes point directly to their ISO weekly parent:

```markdown
---
parent: '[[<% moment(tp.file.title, "YYYYMMDD").format("YYYY/GGGG-[W]WW") %>]]'
template: "[[daily]]"
alt_file: "[[dash]]"
type: "[[day]]"
created: <% tp.file.creation_date("YYYY-MM-DD[T]HH:mm:ssZ") %>
date: <% moment(tp.file.title, "YYYYMMDD").format("YYYY-MM-DD") %>
aliases:
  - <% moment(tp.file.title, "YYYYMMDD").format("YYYY-MM-DD ddd") %>
tags:
  - daily
id: <% tp.file.title %>
---

# <% moment(tp.file.title, "YYYYMMDD").format("YYYY-MM-DD ddd") %>

[[<% tp.date.now("YYYY/YYYYMMDD", -1, tp.file.title, "YYYYMMDD") %>|prev]]  | [[<% tp.date.now("YYYY/YYYYMMDD", 1, tp.file.title, "YYYYMMDD") %>|next]]

- [*] #task [[gtd_daily]] [root:: gtd_daily] [created::<% tp.file.creation_date("YYYY-MM-DD") %>] ^gtd

```bob-plan

```

## Pomodoros

- [ ] () — PLAN
	- [[#^gtd]]
```

*(Note: `GGGG-[W]WW` is Moment.js ISO-week formatting. For `20261103`, it resolves to `2026/2026-W45`).*

---

#### 4.2.2 Weekly Template (`~/bob/_templates/weekly.md`)

```markdown
---
type: "[[week]]"
created: <% tp.file.creation_date("YYYY-MM-DD[T]HH:mm:ssZ") %>
date: <% tp.file.title %>
parent: "[[<% moment(tp.file.title, "GGGG-[W]WW").format("GGGG/GGGG-[Q]Q") %>]]"
template: "[[weekly]]"
aliases:
  - Week <% moment(tp.file.title, "GGGG-[W]WW").format("WW, GGGG") %>
tags:
  - weekly
id: <% tp.file.title %>
---

# Week <% moment(tp.file.title, "GGGG-[W]WW").format("WW · GGGG") %>
[[<% moment(tp.file.title, "GGGG-[W]WW").subtract(1, "week").format("GGGG/GGGG-[W]WW") %>|prev]] | [[<% moment(tp.file.title, "GGGG-[W]WW").add(1, "week").format("GGGG/GGGG-[W]WW") %>|next]]

```bob-stats-strip
```

> [!info|instructions]- 🤖 Agent Enrichment Instructions (Click to expand)
> You are an expert executive chief of staff and GTD mentor. When tasked with enriching or reviewing this weekly note:
> 1. **Data Discovery**:
>    - Execute `bob stats show -r <START_DATE>..<END_DATE> -a -f json` (spanning Monday through Sunday of this ISO week).
>    - Read the 7 constituent daily notes listed under `## Daily Notes` to extract closed `#task` rows, completed Pomodoros, and `🛠️ **WORK LOG**` entries.
> 2. **Accomplishments & Delivery**:
>    - Under `## Accomplished & Shipped`, synthesize all work delivered. Group items by Root Parent / Project. Highlight major PRs, documents authored, bugs eradicated, and tasks marked Done.
> 3. **Time & Energy Reflection**:
>    - Under `## Time & Energy Distribution`, analyze the stats strip data. Evaluate Theme allocation (e.g. was BUILD $\ge 50\%$? Was MEET kept bounded? Did FIX surge unexpectedly?). Note any notable off-clock hours.
> 4. **Friction, Stalls & Upkeep**:
>    - Identify tasks that underwent repeated keeps (high keep streaks or Rotten Log entries).
>    - Flag any blocked projects or unclosed open loops.
> 5. **Next Week Intentions**:
>    - Under `## Intentions & Focus Bets`, formulate 3 to 5 clear, high-leverage bets for the upcoming sprint, referencing current Next/Ready tasks.
> 6. **Preservation**:
>    - Never delete or overwrite manual notes authored by Bryan. Replace only the HTML placeholder comments inside each section.

## Daily Notes
- [[<% moment(tp.file.title, "GGGG-[W]WW").isoWeekday(1).format("YYYY/YYYYMMDD|ddd YYYY-MM-DD") %>]]
- [[<% moment(tp.file.title, "GGGG-[W]WW").isoWeekday(2).format("YYYY/YYYYMMDD|ddd YYYY-MM-DD") %>]]
- [[<% moment(tp.file.title, "GGGG-[W]WW").isoWeekday(3).format("YYYY/YYYYMMDD|ddd YYYY-MM-DD") %>]]
- [[<% moment(tp.file.title, "GGGG-[W]WW").isoWeekday(4).format("YYYY/YYYYMMDD|ddd YYYY-MM-DD") %>]]
- [[<% moment(tp.file.title, "GGGG-[W]WW").isoWeekday(5).format("YYYY/YYYYMMDD|ddd YYYY-MM-DD") %>]]
- [[<% moment(tp.file.title, "GGGG-[W]WW").isoWeekday(6).format("YYYY/YYYYMMDD|ddd YYYY-MM-DD") %>]]
- [[<% moment(tp.file.title, "GGGG-[W]WW").isoWeekday(7).format("YYYY/YYYYMMDD|ddd YYYY-MM-DD") %>]]

## Executive Summary
<!-- AGENT: 2-3 paragraph synthesis of the week's operational momentum, primary theme, and overall output. -->

## Accomplished & Shipped
<!-- AGENT: Grouped bulleted list by Area/Project detailing closed tasks, shipped features, and milestones. -->

## Time & Energy Distribution
<!-- AGENT: Narrative commentary on the stats strip: hours worked, theme mix, unexpected drift, and focus quality. -->

## Friction, Blockers & Rotten Upkeep
<!-- AGENT: Analysis of tasks kept repeatedly, postponed chores, stalled epics, or recurring friction. -->

## Intentions & Focus Bets for Next Week
<!-- AGENT: 3-5 high-leverage focus bets proposed for next week's sprint. -->
```

---

#### 4.2.3 Quarterly Template (`~/bob/_templates/quarterly.md`)

```markdown
---
type: "[[quarter]]"
created: <% tp.file.creation_date("YYYY-MM-DD[T]HH:mm:ssZ") %>
date: <% tp.file.title %>
parent: "[[<% tp.file.title.slice(0, 4) %>]]"
template: "[[quarterly]]"
aliases:
  - <% tp.file.title %>
tags:
  - quarterly
id: <% tp.file.title %>
---

# <% tp.file.title %> · Quarterly Horizon
[[<% tp.file.title.slice(0,4) + "-Q" + (parseInt(tp.file.title.slice(6,7)) > 1 ? parseInt(tp.file.title.slice(6,7)) - 1 : 4) %>|prev]] | [[<% tp.file.title.slice(0,4) + "-Q" + (parseInt(tp.file.title.slice(6,7)) < 4 ? parseInt(tp.file.title.slice(6,7)) + 1 : 1) %>|next]]

```bob-stats-strip
```

> [!info|instructions]- 🤖 Agent Enrichment Instructions (Click to expand)
> You are an executive strategist and Horizons of Focus coach. When asked to enrich this quarterly note:
> 1. **Data Discovery**:
>    - Run `bob stats show -r <QUARTER_START>..<QUARTER_END> -g week -a -f json` to retrieve the 13-week progression.
>    - Review the 13 weekly notes under `## Weeks in Quarter`.
>    - Audit `~/bob/projects.md` and active project notes under `prj/`.
> 2. **Quarterly Milestone Synthesis**:
>    - Under `## Shipped Milestones & Major Outcomes`, detail completed multi-week projects, architectural breakthroughs, and significant publications.
> 3. **Macro Allocation Analysis**:
>    - Under `## Macro Time & Velocity Trends`, evaluate the quarter-long trends: velocity stability across the 13 weeks, work/life balance, and area investment proportions.
> 4. **Portfolio & Someday/Maybe Audit**:
>    - Review stalled or zombie projects. Recommend archiving completed initiatives and evaluate `maybe.md` candidates for activation.
> 5. **Next Quarter Horizon Bets**:
>    - Under `## Strategic Horizon Bets for Next Quarter`, define 3 to 5 quarterly objectives (OKRs / 12-Week Year bets).
> 6. Preserve manual human notes; update only comment placeholders.

## Weeks in Quarter
<!-- Auto-templated list of the 13 constituent ISO weekly notes -->

## Strategic Retrospective
<!-- AGENT: High-level narrative of the quarter's overarching narrative, triumphs, and pivots. -->

## Shipped Milestones & Major Outcomes
<!-- AGENT: Detailed summary of shipped epics, released software versions, and life accomplishments. -->

## Macro Time & Velocity Trends
<!-- AGENT: Trend commentary across the 13 weeks: consistency, peak weeks, recovery weeks, theme distribution. -->

## Project Portfolio Health & Someday/Maybe Audit
<!-- AGENT: Audit of projects completed, projects retired, and candidates pulled from Someday/Maybe. -->

## Strategic Horizon Bets for Next Quarter
<!-- AGENT: 3-5 macro objectives and thematic focus areas for the upcoming quarter. -->
```

---

#### 4.2.4 Yearly Template (`~/bob/_templates/yearly.md`)

```markdown
---
type: "[[year]]"
created: <% tp.file.creation_date("YYYY-MM-DD[T]HH:mm:ssZ") %>
date: <% tp.file.title %>
parent: "[[all_time]]"
template: "[[yearly]]"
aliases:
  - Year <% tp.file.title %>
tags:
  - yearly
id: <% tp.file.title %>
---

# <% tp.file.title %> · Annual Ledger & Retrospective
[[<% parseInt(tp.file.title) - 1 %>|prev]] | [[<% parseInt(tp.file.title) + 1 %>|next]]

```bob-stats-strip
```

> [!info|instructions]- 🤖 Agent Enrichment Instructions (Click to expand)
> You are a life historian and executive biographer. When asked to enrich this yearly note:
> 1. **Data Discovery**:
>    - Execute `bob stats show -r <YEAR>-01-01..<YEAR>-12-31 -g month -a -f json`.
>    - Inspect the 4 quarterly notes (`<YEAR>-Q1` through `<YEAR>-Q4`).
>    - Review reference reading history via `bob ref` and git log milestones.
> 2. **Annual Retrospective**:
>    - Synthesize the overarching character, challenges, and defining moments of the year.
> 3. **Life Horizons Audit**:
>    - Evaluate progress against David Allen's Horizons of Focus (Level 2: Areas of Focus & Responsibility, Level 3: 1-2 Year Goals, Level 4: 3-5 Year Vision).
> 4. **Annual Knowledge & Craft Growth**:
>    - Summarize key books/papers digested in `bob ref`, software capabilities built, and skills mastered.
> 5. **Next Year's Guiding Theme & Horizons**:
>    - Synthesize a singular annual theme (e.g. "Consolidation", "Scale", "Mastery") and top-tier intentions.

## Constituent Quarters
- [[<% tp.file.title %>/2026-Q1|Q1 · Winter]]
- [[<% tp.file.title %>/2026-Q2|Q2 · Spring]]
- [[<% tp.file.title %>/2026-Q3|Q3 · Summer]]
- [[<% tp.file.title %>/2026-Q4|Q4 · Autumn]]

## Annual Retrospective & Defining Themes
<!-- AGENT: Deep, reflective narrative synthesizing the narrative arc of the entire year. -->

## Landmark Achievements by Life Area
<!-- AGENT: Detailed triumphs across dev, career, cash, health, personal, and relationships. -->

## Annual Working Time & Energy Analysis
<!-- AGENT: Analysis of 12-month trends, total hours worked, seasonality, and work/rest rhythms. -->

## Knowledge & Reference Library Ingestion
<!-- AGENT: Reading highlights, digested literature, and major technical insights acquired. -->

## Guiding Theme & Horizon Intentions for <% parseInt(tp.file.title) + 1 %>
<!-- AGENT: Proposed annual motto, guiding principles, and primary horizon goals for next year. -->
```

---

#### 4.2.5 The Lifetime Root Note (`~/bob/all_time.md`)

```markdown
---
type: "[[all_time]]"
created: 2026-11-03T09:00:00-05:00
parent: "[[org]]"
template: "[[all_time]]"
aliases:
  - All Time
  - Master History
tags:
  - all_time
id: all_time
---

# All-Time Ledger & Master History
Parent: [[org]]

```bob-stats-strip
```

> [!info|instructions]- 🤖 Agent Enrichment Instructions (Click to expand)
> When updating this master history note:
> 1. Run `bob stats show -r all -g year -a -f json`.
> 2. Audit the index of all tracked years to ensure every yearly note in the vault is linked.
> 3. Chronicle the overarching multi-year eras, career epochs, and cumulative life statistics.

## Tracked Years
- [[2023]]
- [[2024]]
- [[2025]]
- [[2026]]

## Multi-Year Eras & Career Epochs
<!-- Narrative timeline documenting major life chapters, career transitions, and foundational eras. -->

## Cumulative Lifetime Metrics & Macro Allocation
<!-- Multi-year time tracking trends, aggregate pomodoro volumes, and long-term discipline trends. -->
```

---

## 5. GTD Review Chore Choreography in `~/bob/gtd_daily.md`

`~/bob/gtd_daily.md` manages daily recurring GTD checklist chores. To support the new periodic rhythm, we upgrade the existing weekly task and introduce dedicated quarterly and annual review recurring tasks.

### 5.1 Updated Weekly Review Task
Currently in `gtd_daily.md`:
```markdown
- [?] #task #gtd #post **Weekly prune**: release [[dash#NEXT Tasks|NEXT]] to ≤15 and [[dash#PENDING Tasks|PENDING]] to ≤10 with Alt+N, promote from [[dash#READY Tasks|READY]], defer with P-levels, check [[dash_stats|Stats]] (hours, created vs closed, keep rate); clear leftover [[rotten|ROTTEN]] or lengthen that note's task_refresh.  [repeat:: every week on Monday when done]  [created:: 2026-11-02]  [scheduled:: 2026-11-09]
```

**Upgraded Definition**:
```markdown
- [?] #task #gtd #post **Weekly review**: Open current week note [[<% moment().format("YYYY/[20]GG-[W]WW") %>]] · review weekly stats strip & daily unit breakdown · release [[dash#NEXT Tasks|NEXT]] to ≤15 and [[dash#PENDING Tasks|PENDING]] to ≤10 with Alt+N · promote from [[dash#READY Tasks|READY]] · defer with P-levels · run or review LLM enrichment on weekly note · clear leftover [[rotten|ROTTEN]] or lengthen task_refresh · set 3–5 focus bets for upcoming week.  [repeat:: every week on Monday when done]  [created:: 2026-11-03]  [scheduled:: 2026-11-09]
```

### 5.2 New Quarterly Review Task
To be scheduled for the first Monday of each quarter (Jan, Apr, Jul, Oct):
```markdown
- [?] #task #gtd #post **Quarterly review**: Open current quarter note [[<% moment().format("YYYY/[20]GG-[Q]Q") %>]] · review quarterly stats strip & 13-week progression · audit active & stalled projects in [[projects]] · review [[maybe|Someday/Maybe]] list · enrich quarterly note with agent · define strategic horizon bets for next quarter.  [repeat:: every 3 months on 1st Monday when done]  [created:: 2026-11-03]  [scheduled:: 2027-01-04]
```

### 5.3 New Annual Review Task
To be scheduled every January 2:
```markdown
- [?] #task #gtd #post **Annual review**: Open [[<% moment().format("YYYY") %>]] · review annual stats strip & quarterly distribution · complete annual retrospective & life horizon audit across [[horizon]] · update [[all_time]] and [[org]] · enrich yearly note with agent · define annual vision and guiding theme for new year.  [repeat:: every year on January 2 when done]  [created:: 2026-11-03]  [scheduled:: 2027-01-02]
```

---

## 6. SASE Glossary Definition: `stats-strip`

In accordance with SASE memory strand rules (`sase/memory/glossary/`), we specify the formal glossary strand defining `stats-strip` and establishing its exact taxonomy alongside existing terms (`day-strip`, `stats-dash`, `root-parent`, and `task-type`).

```markdown
# Stats Strip

*Requested · project*

aka periodic stats strip, time strip, stats banner

The read-only, compact working-time and activity summary embedded at the
head of periodic notes (daily, weekly, quarterly, yearly, or all-time),
rendered by the `bob-stats-strip` code block (or `bob-plan` / `bob-day-stats`
for daily files). Its contents:

1. **Headline Fact Grid**: A horizontal row of key performance metrics
   (`worked`, `sessions`, `done`, `created`, `net`, and review/habit
   ratios), displaying large tabular values over quiet comparative reference
   lines (percentage delta vs. prior period or typical baseline).
2. **Distribution Lanes**: Proportional horizontal stacked bars showing
   working time by [[root-parent]] and by [[task-type]], featuring
   interactive legends and full palette hue attribution.
3. **Sub-Unit Composition Breakdown**: For multi-day periodic notes, an
   integrated micro-breakdown showing the constituent temporal units that
   make up the whole (daily breakdown for weeks, weekly breakdown for
   quarters, quarterly breakdown for years) with clickable links navigating
   directly to child notes.

bob-cli owns every derived value; the strip never mutates vault notes.
Clicking any fact or bar segment opens the [[stats-dash]] pinned to that
discrete time window.

### Taxonomy & Relations
- **[[day-strip]]**: The canonical daily specialization of the stats strip
  family, embedded directly inside the `bob-plan` block of daily notes.
- **[[stats-dash]]** (`dash_stats.md`): The expansive, full-page analytical
  workspace featuring mutable range pickers, time-series charts, and filter
  panels. In contrast, a stats strip is an inline, context-anchored glance
  strip bound immutably to the note's enclosing period.
- **Agent Enrichment**: Higher-order stats strips anchor periodic GTD
  reviews and provide structured numeric grounding for autonomous LLM
  enrichment workflows.
```

---

## 7. Engineering & Implementation Roadmap

To deliver this feature reliably, we break the implementation into four sequential, verifiable phases spanning `bob-cli`, `bob-plugins`, and vault configurations.

### Phase 1: `bob-cli` Range Parser Generalization
Currently, `bob stats show -r <RANGE>` only supports presets (`7d`, `4w`, `3m`, `1y`, `all`), offsets (`Nd`, `Nw`), or explicit dates (`YYYY-MM-DD..YYYY-MM-DD`). Passing `-r 2026-W44` fails with an invalid range error.

**Code Changes in `src/native/stats/`**:
- In `src/native/stats/cli.rs` and `src/native/stats/series.rs`:
  - Enhance `parse_range` to recognize ISO period keys:
    - `YYYY-Www` (e.g. `2026-W45`): Resolves to the Monday–Sunday date range for that ISO week.
    - `YYYY-Qq` (e.g. `2026-Q4`): Resolves to the start and end dates of that quarter.
    - `YYYY-MM` (e.g. `2026-11`): Resolves to the first and last day of that month.
    - `YYYY` (e.g. `2026`): Resolves to Jan 1 – Dec 31 of that year.
    - `all`: Resolves to first recorded date in vault through today.
  - This enables any CLI user, script, or Obsidian plugin to call `bob stats show -r 2026-W45 -a -f json` without manual calendar math.

### Phase 2: `bob-plugins` (`bob-ledger-tools`) Component Extension
Extend the Day Strip rendering engine in `bob-ledger-tools`:
- Register `bob-stats-strip` markdown code block processor in `src/238-plugin-stats-block.js` / `src/239-plugin-day-strip-registry.js`.
- **Auto-Detection Logic**: When `bob-stats-strip` has an empty body, inspect `ctx.sourcePath` and file metadata:
  - If title matches `^\d{8}$` -> Period is `day`.
  - If title matches `^\d{4}-W\d{2}$` -> Period is `week`.
  - If title matches `^\d{4}-Q[1-4]$` -> Period is `quarter`.
  - If title matches `^\d{4}$` -> Period is `year`.
  - If title matches `^all_time$` -> Period is `all`.
- **Render Sub-Unit Composition Row**:
  - For week: Render the 7-day mini-column strip with `[[YYYY/YYYYMMDD]]` links.
  - For quarter: Render the 13-week spark-bar row with `[[YYYY/YYYY-Www]]` links.
  - For year: Render the 4-quarter row with `[[YYYY/YYYY-Qq]]` links.

### Phase 3: Vault Configuration & Template Deployment
- Create `~/bob/_templates/weekly.md`, `quarterly.md`, `yearly.md`, `all_time.md`.
- Update `~/bob/_templates/daily.md` to set `parent: '[[<% moment(tp.file.title, "YYYYMMDD").format("YYYY/GGGG-[W]WW") %>]]'`.
- Initialize `~/bob/all_time.md` and link it under `~/bob/org.md`.
- Update `~/bob/gtd_daily.md` review tasks.

### Phase 4: SASE Memory & Decision Records
- Submit SASE Memory write for `sase/memory/glossary/stats-strip.md`.
- Formulate Decision Record `sase/memory/decisions/periodic-hierarchy-uses-iso-weeks.md`.

---

## 8. Summary of Adjustments to User Requirements

| Requirement | Proposed Adjustment | Rationale |
| :--- | :--- | :--- |
| **Drop Monthly Files** | **Endorsed for Primary Tree; Retain for Ancillary Finance** | ISO weeks nest cleanly into 13-week quarters without calendar boundary straddling. Monthly notes remain available for financial queries but exit the task/review tree. |
| **Stats Strip in Weekly/Quarterly/Yearly** | **Adopt Hybrid Architecture** | Dynamic code block provides real-time visual beauty in Obsidian; structured markdown callouts below ensure AI agents have full text access and instructions. |
| **Sub-unit Summarization** | **Multi-tier Composition Strip** | Weekly notes show 7 daily mini-bars with links; quarterly notes show 13 weekly velocity bars; yearly notes show 4 quarterly blocks. |
| **Agent Enrichment Instructions** | **Collapsible Callouts (`> [!info|instructions]-`)** | Keeps instructions 100% visible to LLMs in raw text while folding them into a zero-clutter 1-line pill in Obsidian Live Preview. |
| **Update `gtd_daily.md`** | **Add Quarterly and Annual Recurring Chores** | Extends GTD discipline cleanly across Horizons 1 (Daily), 2 (Weekly), 3 (Quarterly), and 4 (Annual). |

---

## 9. Conclusion & Next Actions

The proposed restructuring is a profound upgrade to the Bob personal productivity ecosystem. It replaces an awkward, un-templated monthly link with a mathematically rigorous, aesthetically beautiful ISO periodic hierarchy. The generalized **Stats Strip** transforms passive notes into active dashboards, while the collapsible agent instructions create a seamless, autonomous bridge between Bryan and his AI agent swarm.

**Recommended Immediate Next Step**:
Proceed to implement Phase 1 (`bob-cli` range parser extension for `YYYY-Www` and `YYYY-Qq`) and Phase 2 (`bob-stats-strip` renderer in `bob-ledger-tools`).
