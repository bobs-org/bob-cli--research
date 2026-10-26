# Research Report: 7-Day Rolling Average Comparison Indicators for the Day Strip

**Author:** researcher gem (`research.5d.gem`)  
**Date:** 2026-10-26  
**Topic:** Visual Comparison of Daily Note Day Strip Numeric Metrics to Their Previous 7-Day Rolling Averages  
**Target Repository:** `bob-plugins` (`bob-ledger-tools`) & `bob-cli`  
**Status:** Complete Design, Critique, and Architecture Proposal  

---

## Executive Summary

This research investigates the design, user experience, statistical validity, and technical implementation of adding visual indicators to the daily note **Day Strip** in Obsidian, showing how each numeric metric on day $D$ compares to the average of the previous 7 days ($D-7 \dots D-1$).

The Day Strip currently renders five facts at the top of the `bob-plan` code block in canonical daily notes (`YYYY/YYYYMMDD.md`):
1. `worked` (focus duration in minutes, e.g., `3h 45m`)
2. `reviewed` (count of review answers committed, e.g., `42`)
3. `done` (count of tasks completed, e.g., `18`)
4. `created` (count of new tasks captured, e.g., `7`)
5. `review_closed` (boolean daily closeout status: check mark, ✕, or half-ring)

### Verdict & Core Critique

The proposal to contextualize daily numbers against a recent baseline is **conceptually sound and high-value**, but **implementing it naively (e.g., standard red/green stock-ticker deltas) will degrade the user experience and violate core design principles**:

1. **The "Provisional Today" Anxiety Trap:** At 9:00 AM on today's note, Bryan has worked 25 minutes. Showing a harsh red downward delta (`▼ −4h 05m / −91%`) treats an early morning start as a catastrophic failure. Daily GTD tools must motivate and orient, not inflict artificial gamified stress.
2. **The Normative Valence Trap (Red vs. Green):** Productivity metrics do not have monotonic "more is better" semantics. High `created` task counts often indicate runaway capture or scope creep; low task creation during deep execution weeks is positive. Coloring up-arrows green and down-arrows red injects false moral judgments.
3. **The Outlier Distortion Trap (Mean vs. Median):** The arithmetic mean of $N=7$ days is fragile to single-day anomalies (e.g., a sick day with 0 minutes or a weekend marathon of 10 hours). Robust guardrails, minimum data thresholds, and clear definitions are essential.
4. **The Visual Clutter Risk:** The Day Strip is celebrated for its clean, airy, hairline-delimited typography. Crowding the fact cards with noisy percentage badges or multi-line text will ruin its aesthetic elegance.

### Key Recommended Adjustments

We recommend adopting the feature with **five specific design adjustments**:
1. **Dual-Mode Presentation (Pace vs. Delta):** For **provisional today**, display the 7-day average as a quiet, aspirational benchmark target (`7d: 4h 30m`) rather than a negative deficit. For **past settled days** (or once today's review is closed), display the settled directional delta (`▲ +45m` or `▼ −15m`).
2. **Numeric Scope Only:** Restrict comparison strictly to the four numeric metrics (`worked`, `reviewed`, `done`, `created`). Omit `review_closed`, which is a boolean state mark.
3. **Valence-Neutral Tonal Styling:** Avoid aggressive saturated traffic lights (neon red/green). Use subtle, muted typographic glyphs (`▲`, `▼`, `≈`) set in Obsidian's neutral theme inks (`var(--text-muted)` and subtle tonal tinting).
4. **Robust Baseline Data Quality ($k \ge 4$):** Compute the average strictly over the completed window $[D-7, D-1]$, excluding $D$. Require at least 4 valid, tracked days; otherwise display a neutral `–` (insufficient baseline).
5. **Sub-Value Microline Layout:** Place a delicate, third-tier microline (`font-size: 0.72em`) directly below each large tabular numeral. This preserves horizontal alignment, avoids line clipping, and discloses full statistical nuance (both mean and median) on hover via rich accessible tooltips.

---

## 1. Context & Architectural Foundation

### 1.1 The Shipped Day Strip Architecture

The Day Strip was established in epic `bob-cli-bp` and refined in subsequent iterations (`bob-cli-bz` and `bob-cli-an`). It lives as a virtual mount inside desktop Obsidian daily notes, rendered as the first child of the `bob-plan` codeblock processor:

```text
^gtd
┌──────────────────────────────────────────────────────────────────────────────────┐
│  WORKED        REVIEWED       DONE           CREATED        REVIEW CLOSED        │  <-- Line 1: Facts
│  5h 25m        64             30             40             ✔                    │
│                                                                                  │
│  ● sase 2h 45m   ● bob 1h 55m   ● dev 45m                        so far · 14:50  │  <-- Line 2: Legend & Meta
│  █████████████████████████████████░░░░░░░░░░░░░░░░░░░▒▒▒▒▒▒▒▒▒▒                  │  <-- Line 3: Root-Parent Bar
└──────────────────────────────────────────────────────────────────────────────────┘
 [TODAY 3/3 · 7/10]  [PENDING 4/10]  [NEXT 15/15]  [READY 61/100]   ★ GTD · BOB    <-- Plan Badges

## Pomodoros
- [x] (**0720-0745** [t:: 25m]) — GTD
	- 🍅 [[#^gtd]]
```

Each fact card in Line 1 is an interactive target (`<span role="link" class="bob-day-strip-fact">`) that opens the Stats dashboard (`dash_stats.md`) with day $D$ pinned and that metric focused.

### 1.2 Data Pipeline & Cache Discovery

A vital discovery from our codebase inspection is that **all necessary 7-day data is ALREADY in memory**:

1. In `plugins/bob-ledger-tools/src/236-plugin-stats-data.js`, the plugin fetches stats using:
   ```javascript
   const args = ["stats", "show", "-a", "-f", "json"];
   ```
   By default, this loads a `4w` (28-day) window of daily series points.
2. In `plugins/bob-ledger-tools/src/239-plugin-day-strip-hosts.js`, `dayStripDefaultReportCovers(report, day, localToday)` explicitly enforces that a cached report is only usable for day $D$ if:
   ```javascript
   // its daily series contains every date D-7..D
   for (let back = 7; back >= 0; back -= 1) {
     wanted.push(dayStripShiftDay(day, -back));
   }
   ```
   This check was originally designed for the 8-point history marks ($D-7 \dots D$).
3. **Consequence:** For every rendered Day Strip, the points for $D-7, D-6, D-5, D-4, D-3, D-2, D-1$ are already present in the active report object. Implementing 7-day comparison requires **zero additional CLI subprocess spawns, zero disk I/O, and zero network calls**.

### 1.3 The Architectural Principle: "Bob Owns Every Value"

According to SASE memory and `docs/stats.md`:
> *"bob-cli owns the metric meanings; the terminal and Obsidian views consume the same JSON model... Bob owns every value: labels, values, part displays, and definitions all come from the report. No definition or metric value is reconstructed by the renderer."*

If the Obsidian plugin computes averages directly in JavaScript without a backend contract, it creates technical debt and risks divergent logic between the terminal `bob stats` glance and Obsidian. 

Therefore, our proposal designs the visual presentation first, defines the formal mathematical specification, and maps out both an **Engine-Authoritative path** (Rust backend emitting comparison fields on `SeriesPoint`) and an **Adaptive Client Fallback** (plugin computing the compliant contract locally when running against existing CLI binaries).

---

## 2. Critique of the 7-Day Average Concept

### 2.1 Strengths: Why 7 Days Works

- **Neutralizing Weekly Seasonality:** Human work schedules are inherently cyclical on a 7-day cadence. Bryan typically works focused deep-work hours Monday through Friday and lighter or maintenance hours on weekends. A 7-day window $[D-7 \dots D-1]$ always contains exactly 5 weekdays and 2 weekend days. It eliminates the distortion where a Monday is compared only to Sunday, or Friday is compared only to Thursday.
- **Adaptive Recency:** A 30-day average is too sluggish to reflect life phases (vacations, conferences, intense sprint cycles). A 3-day average is too volatile. A 7-day rolling window provides the optimal "Goldilocks" blend of statistical stability and temporal relevance.
- **Cognitive Grounding:** A number like `14` tasks done has no emotional anchor. `14 (avg 8)` immediately signals a productive flow day.

### 2.2 Critical Vulnerabilities: Where the Plan Can Fail

#### Trap 1: The "Provisional Today" / Morning Anxiety Problem
When Bryan opens his daily note at 8:30 AM, `worked` is `0m` or `25m`.
- If the system shows:
  ```text
  WORKED
  25m  ▼ −4h 05m (−91%)
  ```
  It projects failure before the workday has even begun.
- A morning snapshot is *incomplete*, not *deficient*. Comparing an open accumulator against a closed 24-hour baseline violates basic measurement hygiene.

#### Trap 2: The Normative Valence Problem (The Red/Green Fallacy)
In financial interfaces, Green = Up and Red = Down. Applying this blindly to personal task management causes psychological friction:
- **`created` (New tasks captured):** If Bryan's 7-day average is 5 new tasks, and today he captures 35 tasks, an indicator reading `▲ +30` in bright green congratulates him for massively inflating his backlog! In reality, excessive capture can indicate lack of focus or overwhelming incoming requests. Conversely, a day with `0` created tasks (while grinding down existing work) would be penalized in red.
- **`worked`:** Working 9 hours when average is 5 hours might represent unsustainable overwork or late-night crunch, not necessarily a positive event to be cheered with neon badges.
- **Verdict:** GTD tools must remain **objective instruments of reality**, not judgmental coaches. Indicators must be informative, neutral, and quiet.

#### Trap 3: Mean vs. Median (Outlier Distortion)
In small sample sizes ($N=7$), the arithmetic mean $\mu = \frac{1}{7}\sum x_i$ is fragile:
- Suppose daily worked minutes over the last 7 days were: `[4h, 4h, 4h, 0m (sick), 4h, 4h, 4h]`.
  - Sum = 24h. Mean = $24 / 7 = 3\text{h } 25\text{m}$.
  - The single sick day drags down the baseline by 35 minutes!
- Conversely, a single 9-hour marathon pulls the baseline upward, making normal 4-hour days look substandard.
- In `src/native/stats/series.rs`, `bob-cli` already uses **median** for its rolling metric series (`rolling_median`) precisely because median ignores single-day outliers.
- However, for small integer counts (`done`, `created`), medians can be coarse (e.g., median of `[1, 1, 2, 2, 2, 3, 3]` is `2`, masking a rising trend).

#### Trap 4: Visual Density and Box-Model Constraints
In epic `bob-cli-bz`, history marks were removed after a severe CSS bug occurred where Obsidian's default `button { height: 30px }` rule clipped elements and forced overflow onto adjacent lines. 
The current Day Strip is horizontally compact:
- Desktop view: 5 columns across ~700px reading width ($\approx 120\text{px} - 140\text{px}$ per column).
- Responsive wrap (< 34em): 3 columns on row 1, 2 columns on row 2 ($\approx 150\text{px} - 170\text{px}$ per column).
- Squeezing large percentage chips, full sentences, or multiple numbers into each card will cause text wrapping, uneven vertical stretching, or horizontal overflow.

---

## 3. Recommended Design Specification

To resolve all critiques while delivering an intuitive, reliable, and beautiful feature, we propose the **Sub-Value Microline Pattern with Dual-Mode Temporal Semantics**.

### 3.1 The Dual-Mode Temporal Semantics

The indicator adapts its meaning and presentation depending on whether the day being viewed is **Provisional (In Progress)** or **Settled (Completed)**:

```
┌───────────────────────────────────────────────────────────────────────────────┐
│ TEMPORAL STATE   │ PRIMARY PRESENTATION        │ SEMANTIC MEANING             │
├──────────────────┼─────────────────────────────┼──────────────────────────────┤
│ Today (Active)   │ 7d: 4h 30m                  │ Benchmark Target (Pace)      │
│ Today (Exceeded) │ ▲ +25m                      │ Milestone Cleared            │
│ Past Day (Above) │ ▲ +45m                      │ Settled Surplus vs Baseline  │
│ Past Day (Below) │ ▼ −30m                      │ Settled Deficit vs Baseline  │
│ Past Day (At Par)│ ≈ par                       │ Balanced with Baseline (±5%) │
│ Insufficient Data│ –                           │ Baseline Not Established     │
└───────────────────────────────────────────────────────────────────────────────┘
```

#### Mode A: Today in Progress (`provisional == true`)
- **Before clearing average:** The microline quietly displays the target baseline:
  ```text
  WORKED
  1h 45m
  7d: 4h 30m
  ```
  This answers: *"What is my typical rhythm?"* without labeling the current state as a failure.
- **After clearing average:** Once today's value surpasses the 7-day average, the microline flips to celebrate the milestone:
  ```text
  WORKED
  4h 55m
  ▲ +25m
  ```

#### Mode B: Past Settled Days (`day < localToday` or `review_closed == met`)
- Displays the final directional delta relative to the 7 days preceding that date:
  ```text
  WORKED            REVIEWED          DONE              CREATED
  5h 15m            58                24                6
  ▲ +45m            ▲ +12             ▼ −4              ≈ par
  ```

### 3.2 Typography & Visual Hierarchy

Each fact card maintains a disciplined, 3-tier vertical hierarchy:

```
+------------------------------------------+
|  WORKED                                  |  <-- Tier 1: Label (0.75em, uppercase, muted)
|  5h 25m                                  |  <-- Tier 2: Primary Value (1.35em, bold tabular)
|  ▲ +45m                                  |  <-- Tier 3: Comparison Microline (0.72em, tabular)
+------------------------------------------+
```

#### Visual Styling Principles:
1. **Font Scale:** The microline is set at `0.72em` with `font-variant-numeric: tabular-nums`. It is visually subordinate to the primary value so it never competes for dominance.
2. **Directional Glyphs:** Clean geometric unicode triangles `▲` (U+25B2) and `▼` (U+25BC), sized slightly smaller than adjacent numbers (`0.85em`), or a subtle approximation glyph `≈` (U+2248) when within $\pm 5\%$.
3. **Restrained Tonal Inks (No Neon Traffic Lights):**
   - **Upward Delta (`▲`):** Styled with subtle, calming ink:
     `color: color-mix(in srgb, var(--color-green, #48c774) 65%, var(--text-muted));`
   - **Downward Delta (`▼`):** Styled with soft, non-punitive stone/amber ink:
     `color: color-mix(in srgb, var(--color-orange, #e67e22) 65%, var(--text-muted));`
   - **Neutral / Par (`≈`) / Pace Target (`7d:`):** Styled with standard faint secondary ink:
     `color: var(--text-faint);`
   - **`CREATED` Metric Exception:** For the `created` metric, deltas are ALWAYS rendered in neutral `var(--text-muted)` ink regardless of direction, explicitly preventing false value judgments about task capture volume.

### 3.3 ASCII Layout Mockups

#### Desktop View: Full 5-Column Grid (Normal Reading Width ~700px)

```text
^gtd
┌────────────────────────────────────────────────────────────────────────────────────────┐
│  WORKED          REVIEWED        DONE            CREATED         REVIEW CLOSED         │
│  5h 25m          64              30              12              ✔                     │
│  ▲ +45m          ▲ +14           ▲ +8            ▼ −3            met                   │
│                                                                                        │
│  ● sase 2h 45m   ● bob 1h 55m   ● dev 45m                            so far · 16:30    │
│  █████████████████████████████████░░░░░░░░░░░░░░░░░░░▒▒▒▒▒▒▒▒▒▒                        │
└────────────────────────────────────────────────────────────────────────────────────────┘
 [TODAY 3/3 · 7/10]  [PENDING 4/10]  [NEXT 15/15]  [READY 61/100]   ★ GTD · BOB
```

#### Morning View: Provisional Today (8:45 AM, Workday Just Beginning)

```text
^gtd
┌────────────────────────────────────────────────────────────────────────────────────────┐
│  WORKED          REVIEWED        DONE            CREATED         REVIEW CLOSED         │
│  25m             12              2               4               ◐                     │
│  7d: 4h 30m      7d: 48          7d: 18          7d: 8           in progress           │
│                                                                                        │
│  ● gtd 25m                                                           so far · 08:45    │
│  ████████████                                                                          │
└────────────────────────────────────────────────────────────────────────────────────────┘
```
*(Notice: No negative red arrows. Clear, calming target benchmarks.)*

#### Responsive View: Split Pane / Mobile (< 34em ~540px)
The existing Day Strip container wraps to a 3-column + 2-column grid. The microline flows naturally without overflowing:

```text
┌────────────────────────────────────────────────────────┐
│  WORKED               REVIEWED          DONE           │
│  5h 25m               64                30             │
│  ▲ +45m               ▲ +14             ▲ +8           │
│  ───────────────────────────────────────────────────── │
│  CREATED              REVIEW CLOSED                    │
│  12                   ✔                                │
│  ▼ −3                 met                              │
│                                                        │
│  ● sase 2h 45m   ● bob 1h 55m   +1       so far · 16:30│
│  ████████████████████░░░░░░░░░░▒▒▒▒▒▒                  │
└────────────────────────────────────────────────────────┘
```

---

## 4. Statistical Specification & Edge Case Handling

### 4.1 Window Definition

For any target day $D$, the comparison window $W(D)$ is defined strictly as the **seven preceding calendar days**:
$$W(D) = \{D - 7, D - 6, D - 5, D - 4, D - 3, D - 2, D - 1\}$$

- **Strict Exclusion of $D$:** Day $D$ is never included in its own baseline.
- **Chronological Completeness:** All 7 calendar dates in $W(D)$ are evaluated.

### 4.2 Data Quality & Inclusion Rules

Each day $d \in W(D)$ has an observed value $v(d)$ and a data quality status $q(d) \in \{\text{ok}, \text{provisional}, \text{missing}, \text{not\_tracked}, \text{warning}\}$.

1. **Eligible Days:** A day $d$ is eligible if $q(d) \in \{\text{ok}, \text{warning}\}$ and $v(d)$ is finite.
2. **Real Zeros vs. Missing Days:**
   - If Bryan logged no pomodoros on Sunday, $v(\text{Sunday}) = 0$ with $q = \text{ok}$. This **MUST** be included in the average as $0$. Excluding real zeros would falsely inflate the average.
   - If the vault was closed or unindexed, $q = \text{missing}$. Missing days are excluded from both numerator and denominator.
3. **Minimum Baseline Threshold ($k \ge 4$):**
   - Let $k$ be the count of eligible days in $W(D)$.
   - If $k < 4$ (fewer than 4 valid days out of 7, e.g., tracking just started 2 days ago):
     - The comparison state is set to `insufficient`.
     - Primary display: `–`
     - Tooltip: `Previous 7 days: Insufficient data (N/7 days tracked).`
4. **Outlier Mitigation: Both Mean & Median:**
   - **Primary Indicator Metric:** Arithmetic Mean $\mu_{7d} = \frac{1}{k}\sum_{i=1}^k v(d_i)$.
   - **Secondary Tooltip Verification:** Rolling Median $M_{7d} = \text{median}(\{v(d_1), \dots, v(d_k)\})$.
   - Both values are computed and displayed in the tooltip to give complete transparency whenever mean and median diverge due to an outlier.

### 4.3 Delta and Formatting Math

#### 1. Focus Time (`worked`)
- Unit: Minutes ($m$).
- Value formatting: If $| \Delta | \ge 60$, format as hours and minutes (e.g., `+1h 15m`, `−45m`).
- Par threshold: If $|\Delta| \le 10\text{m}$, mark as `≈ par`.
- Today target format: `7d: Xh Ym` (e.g., `7d: 4h 30m`).

#### 2. Count Metrics (`reviewed`, `done`, `created`)
- Unit: Discrete integer counts.
- Average formatting: Rounded to one decimal place in tooltips (e.g., `avg 18.4`), rounded to nearest integer for target lines (`7d: 18`).
- Delta formatting: Signed integer (e.g., `+5`, `−2`).
- Par threshold: If $|\Delta| = 0$, mark as `≈ par`.

---

## 5. Tooltip & Accessibility Specification

### 5.1 Rich Accessible Tooltips

Hovering or focusing any fact card reveals a structured, multi-line disclosure providing complete context without cluttering the primary surface:

#### Example: `WORKED` on a Settled Day
```text
Worked: 5h 25m
Previous 7-day average: 4h 40m (+45m / +16%)
Previous 7-day median: 5h 00m
Window: Oct 17 – Oct 23 (7 of 7 days tracked)
Click to open Stats focused on Worked.
```

#### Example: `WORKED` on Today (Provisional Morning)
```text
Worked: 25m (so far)
Previous 7-day average: 4h 30m (benchmark pace)
Previous 7-day median: 4h 15m
Window: Oct 19 – Oct 25 (7 of 7 days tracked)
Click to open Stats focused on Worked.
```

#### Example: `DONE` with an Outlier
```text
Done: 30 tasks
Previous 7-day average: 21.4 tasks (+8 / +37%)
Previous 7-day median: 19 tasks
Window: Oct 17 – Oct 23 (7 of 7 days tracked)
Click to open Stats focused on Done.
```

### 5.2 Screen Reader Accessibility (`aria-label`)

The root Day Strip container maintains an accurate, accessible plain-language narrative.
- Current format:
  `Day stats for Friday, October 24: Worked 5h 25m, Reviewed 64, Done 30, Created 12, Review closed met.`
- Enhanced format:
  `Day stats for Friday, October 24: Worked 5h 25m, up 45 minutes versus 7-day average of 4h 40m; Reviewed 64, up 14 versus 7-day average; Done 30, up 8 versus 7-day average; Created 12, down 3 versus 7-day average; Review closed met.`

---

## 6. Implementation Architecture

### 6.1 DOM & CSS Architecture (`bob-ledger-tools`)

#### Proposed DOM Modification (`239-plugin-day-strip-render.js`):
Inside `dayStripRenderFact(doc, fact, model, handlers, arrive)`, append a third child element `.bob-day-strip-comp` below `.bob-day-strip-value`:

```javascript
// Build the comparison microline element
if (fact.comp && fact.comp.state !== "none" && !skeleton) {
  const compNode = statsEl(doc, "span", {
    class: "bob-day-strip-comp bob-day-strip-comp-" + fact.comp.state,
    "aria-hidden": "true",
  });
  
  if (fact.comp.glyph) {
    dayStripAppend(compNode, statsEl(doc, "span", {
      class: "bob-day-strip-comp-glyph",
    }, fact.comp.glyph));
  }
  
  dayStripAppend(compNode, statsEl(doc, "span", {
    class: "bob-day-strip-comp-text",
  }, fact.comp.text));
  
  dayStripAppend(node, compNode);
}
```

#### Proposed CSS Rules (`plugins/bob-ledger-tools/styles.css`):
```css
/* Fact Card Container - ensure clean vertical stacking */
.bob-day-strip-fact {
  position: relative;
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
  min-width: 0;
  gap: 0.1em;
  padding: 0.25em 0.7em 0.35em;
  border-radius: var(--radius-s);
  cursor: pointer;
}

/* Primary tabular value */
.bob-day-strip-value {
  display: block;
  width: fit-content;
  max-width: 100%;
  overflow: hidden;
  color: var(--text-normal);
  font-size: 1.3em; /* slight adjustment from 1.35em preserves 48px baseline */
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  letter-spacing: -0.02em;
  line-height: 1.1;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Comparison Microline */
.bob-day-strip-comp {
  display: flex;
  align-items: center;
  gap: 0.25em;
  font-size: 0.72em;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  line-height: 1.2;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Tonal Inks */
.bob-day-strip-comp-up {
  color: color-mix(in srgb, var(--color-green, #48c774) 75%, var(--text-muted));
}

.bob-day-strip-comp-down {
  color: color-mix(in srgb, var(--color-orange, #e67e22) 75%, var(--text-muted));
}

.bob-day-strip-comp-par,
.bob-day-strip-comp-target,
.bob-day-strip-comp-neutral {
  color: var(--text-faint);
}

/* Metric exception: CREATED is always neutral */
.bob-day-strip-fact[data-day-strip-metric="created"] .bob-day-strip-comp {
  color: var(--text-muted) !important;
}

.bob-day-strip-comp-glyph {
  font-size: 0.85em;
  line-height: 1;
}

/* Skeleton Placeholder */
.bob-day-strip-comp-skeleton {
  visibility: hidden;
}
```

### 6.2 Pure Model Calculation (`239-plugin-day-strip-model.js`)

In `dayStripBuildFact`, extract the previous 7 days from `report` and calculate the comparison object:

```javascript
function dayStripCalculate7dComparison(metric, report, targetDay, isProvisional) {
  if (!metric || metric.unit === "bool") return { state: "none" };
  
  const points = dayStripMetricPoints(metric, report);
  if (!Array.isArray(points) || points.length === 0) return { state: "none" };

  // Collect previous 7 calendar days D-7..D-1
  const baselineDays = [];
  for (let offset = 7; offset >= 1; offset -= 1) {
    baselineDays.push(dayStripShiftDay(targetDay, -offset));
  }

  const validValues = [];
  for (const date of baselineDays) {
    const pt = points.find((p) => p && p.date === date);
    if (pt && typeof pt.value === "number" && (pt.quality === "ok" || pt.quality === "warning")) {
      validValues.push(pt.value);
    }
  }

  // Minimum 4 valid days required
  if (validValues.length < 4) {
    return {
      state: "insufficient",
      glyph: "",
      text: "–",
      avg: null,
      median: null,
      daysTracked: validValues.length,
    };
  }

  // Calculate Mean and Median
  const sum = validValues.reduce((acc, val) => acc + val, 0);
  const mean = sum / validValues.length;
  const sorted = validValues.slice().sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  const median = sorted.length % 2 !== 0 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2;

  const currentPoint = points.find((p) => p && p.date === targetDay);
  const currentValue = currentPoint && typeof currentPoint.value === "number" ? currentPoint.value : 0;

  // Format benchmark display strings
  const isWorked = metric.id === "worked";
  const formatVal = (val) => isWorked ? dayStripFormatMinutes(Math.round(val)) : String(Math.round(val));

  // Mode A: Provisional Today
  if (isProvisional && currentValue < mean) {
    return {
      state: "target",
      glyph: "",
      text: "7d: " + formatVal(mean),
      avg: mean,
      median,
      delta: currentValue - mean,
      daysTracked: validValues.length,
    };
  }

  // Mode B: Settled Day or Exceeded Today
  const delta = currentValue - mean;
  const parThreshold = isWorked ? 10 : 0.5;

  if (Math.abs(delta) <= parThreshold) {
    return {
      state: "par",
      glyph: "≈",
      text: "par",
      avg: mean,
      median,
      delta: 0,
      daysTracked: validValues.length,
    };
  }

  const isUp = delta > 0;
  const deltaText = (isUp ? "+" : "−") + (isWorked ? dayStripFormatMinutes(Math.abs(Math.round(delta))) : String(Math.abs(Math.round(delta))));

  return {
    state: isUp ? "up" : "down",
    glyph: isUp ? "▲" : "▼",
    text: deltaText,
    avg: mean,
    median,
    delta,
    daysTracked: validValues.length,
  };
}
```

---

## 7. Comparison of Alternatives

During this research, we evaluated four distinct presentation archetypes:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ ARCHETYPE               │ PROS                        │ CONS                           │
├─────────────────────────┼─────────────────────────────┼────────────────────────────────┤
│ 1. Sub-Value Microline  │ Cleanest hierarchy; fits all│ Adds ~0.8em vertical height    │
│    (Recommended)        │ columns; tabular stability. │ to the overall strip.          │
│                         │                             │                                │
│ 2. Value-Adjacent Pill  │ Keeps 2-line height;        │ Causes severe horizontal       │
│    (e.g., "5h 25m [+18%]")│ compact.                  │ overflow in narrow columns.    │
│                         │                             │                                │
│ 3. Header Right-Aligned │ Uses empty space beside     │ Fails on longer labels;        │
│    (e.g., "WORKED ▲+45m") label; no height increase.  │ separates delta from value.    │
│                         │                             │                                │
│ 4. Embedded Bullet Bar  │ Extremely visual; Tuftean   │ Unintuitive for counts; hard   │
│    (Mini horizontal bar)│ micro-gauge.                │ to calibrate scale dynamically.│
└────────────────────────────────────────────────────────────────────────────────────────┘
```

**Why Option 1 (Sub-Value Microline) Won:**
Option 1 provides the highest data clarity, flawless responsive behavior across all viewports, and an uncluttered visual rhythm that integrates naturally into the existing Day Strip design language.

---

## 8. Implementation Roadmap

### Phase 1: Pure Logic & Fixtures (`bob-ledger-tools`)
- Implement `dayStripCalculate7dComparison` in `239-plugin-day-strip-model.js`.
- Add test fixtures in `day-strip-fixtures.cjs` covering:
  - Normal above-average and below-average days.
  - Provisional today with target pace display.
  - Real zeros on weekends.
  - Missing and untracked days with insufficient data fallbacks.
- Update unit tests in `scripts/test-ledger-tools-day-strip.cjs`.

### Phase 2: Painter & Stylesheet (`bob-ledger-tools`)
- Update `dayStripRenderFact` in `239-plugin-day-strip-render.js` to render `.bob-day-strip-comp`.
- Add tonal CSS rules and responsive container query adjustments to `styles.css`.
- Verify in headless browser matrix via `scripts/preview-day-strip.cjs`.

### Phase 3: `bob-cli` Engine Alignment (Future Schema Enhancement)
- Extend `SeriesPoint` in `src/native/stats/report.rs`:
  ```rust
  #[serde(skip_serializing_if = "Option::is_none")]
  pub(crate) rolling_avg_7d: Option<i64>,
  #[serde(skip_serializing_if = "Option::is_none")]
  pub(crate) delta_7d: Option<i64>,
  ```
- Calculate authoritative deltas in `src/native/stats/series.rs`, formalizing backend ownership.

---

## 9. Recommended Next Steps

1. **Review and Approve Design:** Confirm agreement with the proposed **Dual-Mode Temporal Semantics** (Target pace for today, directional delta for past days) and **Sub-Value Microline Layout**.
2. **Implement in `bob-plugins`:** Execute Phases 1 and 2 in `plugins/bob-ledger-tools/`.
3. **Deploy via `bob plugins sync`:** Verify the live visual presentation in Obsidian across actual vault daily notes.
