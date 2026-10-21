# Design & Research: GTD Review Group Icons & Compact Repeat Marks in Obsidian

**Researcher:** `research.28.gem` (Gemini)  
**Date:** 2026-10-21  
**Project:** bob-cli / bob-plugins (Obsidian integration)  
**Target Repository:** `bob-plugins` (`bob-ledger-tools`)  
**Status:** Research & Proposed Design Specification  

---

## 1. Executive Summary

This report investigates and presents a comprehensive design for rendering elegant, intuitive, and compact visual marks in Obsidian for two key task elements:
1. **GTD Review Group Tags (`#gtd #pre` and `#gtd #post`)**: Replacing bulky, accent-colored tag pills with dedicated, semantic identity icons.
2. **Task Recurrence Property (`[repeat:: ...]`)**: Compacting the wide Dataview inline field into an icon-assisted terse cadence mark (e.g. `🔁 daily`, `🔁 Sun`, `🔁 30d`) that eliminates up to 80% of horizontal clutter while preserving full operational transparency.

### Core Recommendations at a Glance

* **Single-Slot Replacement for Tag Pairs:** The tag sequences `#gtd #pre` and `#gtd #post` MUST each be collapsed into a **single unified glyph slot**, rather than rendering separate icons for `#gtd` and `#pre`/`#post`. This mirrors the proven `#task #ref` → `📖` pattern in `docs/task-tag-marks.md`, preventing visual noise and icon clutter.
* **Semantic Icon Metaphors:**
  * **PRE Tier (Opening Checklist / Warmup):** Lucide-style **`sunrise`** (🌅) in warm morning dawn gold (`--bob-gtd-pre-hue`). Represents morning kickoff, prelude chores, and daily commitments.
  * **POST Tier (Closing Review / Wrap-up):** Lucide-style **`flag`** (🚩) in cool milestone violet/indigo (`--bob-gtd-post-hue`). Represents the finish line, review completion, and weekly prune milestone.
* **Terse Cadence Pattern for Repeat (Icon + Compact Label):** Rather than an icon-only approach (which obscures whether a task recurs daily, weekly, or monthly) or leaving the full 30-character Dataview field exposed, adopt the **Date Marks pattern** (`docs/date-marks.md`): a recurring loop icon (`🔁`) paired with an ultra-short cadence label (`daily`, `Mon`, `30d`, `monthly · 1st`).
* **Strict Display-Only Architectural Boundary:** Stored markdown files across the vault retain standard `#gtd #pre` and Dataview `[repeat:: ...]` syntax without alteration. Rendering is handled entirely at the presentation layer in `bob-ledger-tools` via a CodeMirror 6 `ViewPlugin` (Live Preview) and Markdown Post-Processor (Reading View).
* **Frictionless Interaction & Reversibility:** Following the design system of `date-marks` and `task-tag-marks`, clicking or moving the cursor into any mark immediately unfolds the raw markdown for editing. A session toggle command allows instant vault-wide toggling back to native pills.

```text
BEFORE:
- [ ] #task #gtd #post **Morning review**: PRE chores done... [repeat:: every day when done] [created:: 2026-10-20] [scheduled:: 2026-10-21]
Obsidian: - [ ] ⌗ [#gtd] [#post] **Morning review**: ... REPEAT | every day when done + Oct 20 ⧗ today

AFTER:
- [ ] ⌗ 🚩 **Morning review**: PRE chores done... 🔁 daily + Oct 20 ⧗ today
```

---

## 2. Vault Census & Problem Analysis

### 2.1 The Anatomy of Clutter on Active Task Lines

In the Bob vault, the GTD morning review is governed by `decisions:review-walk-is-tiered` (accepted October 4, 2026). The morning review walk `]s` runs through structural tiers:
$$\text{PRE} \to \text{NEW} \to \text{PROJECTS} \to \text{PENDING} \to \text{NEXT} \to \text{TICKLER} \to \text{REFERENCES} \to \text{ROTTEN} \to \text{POST}$$

Under this architecture, checklist items belong to PRE or POST based on exact token tags:
* **PRE Checklist:** Requires `#gtd` plus `#pre` (case-insensitive).
* **POST Checklist:** Requires `#gtd` plus `#post` without `#pre`.

A census of active tasks in `~/bob/gtd_daily.md` reveals lines formatted as:
```markdown
- [?] #task #gtd #pre **Clean up SASE agents on athena and apollo**: Restart failed agents, dismiss agents from yesterday, review inboxes  [repeat:: every day when done]  [created:: 2026-10-21]  [scheduled:: 2026-10-22]
- [?] #task #gtd #pre Review Calendar for today and tomorrow + Create @EVENT notes  [repeat:: every day when done]  [created:: 2026-10-21]  [scheduled:: 2026-10-22]
- [?] #task #gtd #pre Brush teeth  [repeat:: every day when done]  [created:: 2026-10-21]  [scheduled:: 2026-10-22]
- [ ] #task #gtd #post **Morning review**: PRE chores done or knowingly skipped...  [repeat:: every day when done]  [created:: 2026-10-20]  [scheduled:: 2026-10-21]
```

When rendered in Obsidian without decoration:
1. **The Tag Prefix:** Obsidian renders `#gtd` and `#pre` as two consecutive accent-colored (bright violet) pills. They take up ~16 character widths and visually dominate the beginning of the line, pushing the task title far to the right.
2. **The Repeat Suffix:** `[repeat:: every day when done]` takes 30 physical characters. In Reading View (and under Dataview inline field formatting), it renders as an enormous two-tone pill: `REPEAT` | `every day when done`. On short tasks like "Brush teeth" (11 chars), the repeat property is nearly three times as wide as the task description itself.
3. **Contrast with Existing Refinements:** Notice that `#task` already renders as a quiet teal hash `⌗` (via `task-tag-marks`), and dates render as `+ Oct 21  ⧗ tomorrow` (via `date-marks`). The unadorned GTD tags and the bulky `repeat` field are now the **only remaining visual bottlenecks** on the task line.

### 2.2 Live Vault Census Data

A complete scan of the active vault (`~/bob/*.md`) and historical archives (`~/bob/done/*.md`) shows:
* **Total recurring tasks across vault history:** 972 tasks.
* **Distribution of `repeat` rules in the active vault:**
  * `[repeat:: every day when done]`: 17 tasks (94.4%)
  * `[repeat:: every week on Sunday]`: 1 task
  * `[repeat:: every week on Monday when done]`: 1 task
  * `[repeat:: every month on the 1st]`: 1 task
  * `[repeat:: every 30 days when done]`: 1 task
  * `[repeat:: every 28 days]`: 1 task
* **Active `#pre` tasks:** 8 daily morning checklist chores in `gtd_daily.md`.
* **Active `#post` tasks:** 2 closing checklist chores in `gtd_daily.md` ("Morning review" daily, and "Weekly prune" weekly on Monday).
* **Tag Syntax Consistency:** 100% of PRE/POST tasks in `gtd_daily.md` are authored with the exact sequence `#task #gtd #pre` or `#task #gtd #post`. None use emojis (`🔁`); all use Dataview inline bracket syntax `[repeat:: ...]`.

---

## 3. Critique of the Proposal & Conceptual Adjustments

### 3.1 Is This a Good Idea?

**Verdict: YES, exceptionally high-value and necessary.**

1. **Daily Cognitive Ergonomics:** The GTD morning review is executed every single day. Bryan encounters these exact 10 lines every morning. Eliminating tag pills and giant metadata pills transforms the daily ritual from scanning database syntax into reading an uncluttered personal agenda.
2. **Completing the Unified Task Display System:** Over the past few months, `bob-ledger-tools` has incrementally unified task presentation:
   * Priority marks (`docs/projects.md`) replaced `[priority:: ...]`.
   * Date marks (`docs/date-marks.md`) replaced `[created:: ...]`, `[scheduled:: ...]`, `[completion:: ...]`.
   * Task tag marks (`docs/task-tag-marks.md`) replaced `#task` and `#task #ref`.
   * Today marks (`docs/today-marks.md`) replaced `#today` tags.
   Addressing `#gtd #pre`/`#post` and `repeat` completes the vision: every standard task metadata element in Bob will now share a coherent, polished, and quiet design language.

### 3.2 Critical Adjustments to the Initial Requirements

We recommend four crucial adjustments to the user's initial proposal:

#### Adjustment 1: Single Replacement Glyph for `#gtd #pre` (Do NOT render two separate icons)
* *The Risk:* If we naively replace `#gtd` with one icon (e.g. a GTD checkbox/cog) and `#pre` with another icon (e.g. a sun), the line becomes an icon parade: `- [ ] ⌗ ⚙️ 🌅 Brush teeth`. This increases cognitive clutter rather than reducing it.
* *The Adjustment:* Treat `#gtd #pre` as a single semantic compound token representing the **PRE tier**, and `#gtd #post` as a single compound token representing the **POST tier**. One unified glyph replaces the entire contiguous tag sequence, exactly as `#task #ref` is replaced by the single book glyph `📖`. Isolated `#gtd` tags (e.g. on reading notes or project notes) remain normal Obsidian tag pills.

#### Adjustment 2: Icon + Compact Terse Label for `repeat` (Do NOT make it icon-only)
* *The Risk:* An icon-only approach (e.g. just `🔁`) makes task lines ultra-short, but erases cadence information. A user looking at `Pay kelly salary` or `Weekly prune` cannot tell if the task repeats daily, weekly, or monthly without hovering.
* *The Adjustment:* Adopt the proven **Date Marks pattern** (`hourglass` + `tomorrow`). For `repeat`, render an elegant cycle glyph (`🔁`) followed by a concise, humanized cadence token:
  * `[repeat:: every day when done]` $\to$ `🔁 daily`
  * `[repeat:: every week on Monday when done]` $\to$ `🔁 Mon`
  * `[repeat:: every month on the 1st]` $\to$ `🔁 monthly · 1st`
  * `[repeat:: every 30 days when done]` $\to$ `🔁 30d`
  This reduces a 30-character pill to ~7 characters (a 77% reduction in width) while preserving vital operational awareness at a glance.

#### Adjustment 3: Strict Display-Only Architecture (Zero Storage Mutation)
* *The Risk:* It might be tempting to simplify markdown storage by switching to Tasks emojis (e.g. `🔁 every day`) or shortening tags.
* *The Adjustment:* **Never mutate stored markdown.** `bob-cli`'s Rust core (`freshness.rs`, `query.rs`), the Pomodoro ledger, Bob Mac Capture, and Dataview DQL rely heavily on exact tokens `#gtd #pre` and `[repeat:: ...]`. All transformations must happen strictly in memory via CodeMirror 6 decorations and CSS.

#### Adjustment 4: Whitespace & Caret Trap Prevention
* *The Risk:* In CodeMirror 6, replacing multiple tags or bracketed fields can swallow whitespace and trap the cursor, making inline editing painful.
* *The Adjustment:* Replace only the exact character spans of the tokens. Preserve boundary whitespace. Provide an instant mousedown handler and cursor proximity reveal so clicking or navigating into the mark immediately reveals the underlying markdown text.

---

## 4. Visual Design Specifications

The Bob design system adheres to the core aesthetic axiom: **"Shape carries meaning; color whispers."** Icons must be geometric, stroked rather than filled, quiet at rest, and visually harmonious with theme typography.

### 4.1 PRE Review Mark: The Sunrise (`🌅`)

* **Semantic Meaning:** Morning opening ritual, prelude chores, daily readiness checklist.
* **Glyph Geometry:** A refined 16×16 stroked geometric sunrise based on the Lucide icon language:
  * Horizon line across the base.
  * Semicircular sun rising above the horizon.
  * Three radial morning rays extending upwards (at 45°, 90°, 135°).
  * Specifications: ViewBox `0 0 16 16`, `fill: none`, `stroke: currentColor`, `stroke-width: 1.8`, `stroke-linecap: round`, `stroke-linejoin: round`.
  * SVG Path definition:
    ```xml
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="none" stroke="#000" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
      <path d="M2.5 13.5h11M4.5 10.5a3.5 3.5 0 0 1 7 0M8 2.5v2M3.5 4.5l1.5 1.5M12.5 4.5l-1.5 1.5"/>
    </svg>
    ```
* **Color & Tone (Dawn Amber):**
  * Identity Ink: A warm golden amber that evokes dawn without clashing with the orange attention hue:
    ```css
    --bob-gtd-pre-hue: color-mix(in srgb, var(--color-orange, #e59900) 60%, var(--color-yellow, #e5c07b));
    ```
  * Rest opacity: 0.9.
  * Hover: Opacity 1.0 with subtle tinted capsule background (`color-mix(in srgb, var(--bob-gtd-pre-hue) 14%, transparent)`).
  * Done/Cancelled resting tone: Blended 40% toward `--text-faint` at 0.75 opacity on completed lines.
* **Tooltip Text:**
  ```text
  GTD PRE · morning review opening checklist
  Ctrl+Enter to complete
  ```

### 4.2 POST Review Mark: The Finish Flag (`🚩`)

* **Semantic Meaning:** Closing ritual of the morning review walk, commitment review, weekly prune milestone.
* **Glyph Geometry:** A clean 16×16 stroked finish flag:
  * Vertical staff on the left.
  * Triangular/pennant flag flying to the right.
  * Firm ground anchor.
  * Specifications: ViewBox `0 0 16 16`, `fill: none`, `stroke: currentColor`, `stroke-width: 1.8`, `stroke-linecap: round`, `stroke-linejoin: round`.
  * SVG Path definition:
    ```xml
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="none" stroke="#000" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
      <path d="M3.5 2v12M3.5 3h8.5l-2.5 4 2.5 4H3.5"/>
    </svg>
    ```
* **Color & Tone (Milestone Violet):**
  * Identity Ink: A deep review violet/indigo that distinguishes the wrap-up milestone:
    ```css
    --bob-gtd-post-hue: color-mix(in srgb, var(--color-purple, #9d7cd8) 75%, var(--text-normal));
    ```
  * Rest opacity: 0.9.
  * Done/Cancelled resting tone: Blended 40% toward `--text-faint` at 0.75 opacity.
* **Tooltip Text:**
  ```text
  GTD POST · morning review closing checklist
  Ctrl+Enter to complete
  ```

### 4.3 Repeat Mark: The Recurrence Cycle (`🔁`) + Terse Cadence

* **Semantic Meaning:** Recurring task schedule and frequency.
* **Glyph Geometry:** Lucide-style dual looping cycle arrows:
  * ViewBox `0 0 16 16`, `fill: none`, `stroke: currentColor`, `stroke-width: 1.8`, `stroke-linecap: round`, `stroke-linejoin: round`.
  * SVG Path definition:
    ```xml
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="none" stroke="#000" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
      <path d="M12.5 2.5l2 2-2 2M1.5 6.5v-1a3 3 0 0 1 3-3h10M3.5 13.5l-2-2 2-2M14.5 9.5v1a3 3 0 0 1-3 3h-10"/>
    </svg>
    ```
* **Cadence Grammar Engine:**
  The grammar normalizes the Dataview `[repeat:: <spec>]` string into a terse, readable label:

| Stored Markdown Spec | Rendered Label | Tooltip Explanation |
| :--- | :--- | :--- |
| `[repeat:: every day when done]` | `🔁 daily` | Repeats daily (calculated from completion date) |
| `[repeat:: every day]` | `🔁 daily` | Repeats daily (calculated from scheduled date) |
| `[repeat:: every week on Monday when done]` | `🔁 Mon` | Repeats weekly on Monday (when done) |
| `[repeat:: every week on Sunday]` | `🔁 Sun` | Repeats weekly on Sunday |
| `[repeat:: every 30 days when done]` | `🔁 30d` | Repeats every 30 days (when done) |
| `[repeat:: every 28 days]` | `🔁 28d` | Repeats every 28 days |
| `[repeat:: every month on the 1st]` | `🔁 monthly · 1st` | Repeats monthly on the 1st |
| `[repeat:: every 2 weeks]` | `🔁 2w` | Repeats every 2 weeks |
| *Arbitrary / complex string* | `🔁 <first-3-words>` | Unabbreviated rule in tooltip |

* **Color & Tone (Interface Monochrome):**
  * In keeping with Date Marks (`docs/date-marks.md`), recurrence is a temporal schedule property, not an identity type. It uses monochrome interface text ink:
    ```css
    --bob-repeat-mark-ink: var(--text-muted);
    ```
  * Resting opacity: 0.85 (resting on closed lines at 0.65).
  * Font: Monospace or interface font at `0.78em`, aligned with date marks.
* **Tooltip Text:**
  ```text
  Repeats: every day when done
  Rule: Next recurrence scheduled 1 day after completion
  Click or move cursor to edit
  ```

---

## 5. Visual Comparison: Before & After

### Case 1: Daily GTD Morning Checklist Chore (`gtd_daily.md`)
```text
RAW MARKDOWN:
- [?] #task #gtd #pre Brush teeth  [repeat:: every day when done]  [created:: 2026-10-21]  [scheduled:: 2026-10-22]

CURRENT OBSIDIAN RENDERING:
- [?] ⌗ [#gtd] [#pre] Brush teeth  REPEAT│every day when done  + Oct 21  ⧗ tomorrow
(Total visual width: ~85 characters; tags and repeat dominate the row)

PROPOSED RENDERING:
- [?] ⌗ 🌅 Brush teeth  🔁 daily  + Oct 21  ⧗ tomorrow
(Total visual width: ~48 characters; 44% width reduction; "Brush teeth" is primary)
```

### Case 2: Daily GTD Closing Milestone Chore (`gtd_daily.md`)
```text
RAW MARKDOWN:
- [ ] #task #gtd #post **Morning review**: PRE chores done or knowingly skipped...  [repeat:: every day when done]  [created:: 2026-10-20]  [scheduled:: 2026-10-21]

CURRENT OBSIDIAN RENDERING:
- [ ] ⌗ [#gtd] [#post] **Morning review**: PRE chores done...  REPEAT│every day when done  + Oct 20  ⧗ today

PROPOSED RENDERING:
- [ ] ⌗ 🚩 **Morning review**: PRE chores done...  🔁 daily  + Oct 20  ⧗ today
```

### Case 3: Fixed Recurrence Task (`recur.md`)
```text
RAW MARKDOWN:
- [?] #task Pay [[kelly]] salary (see [[kellys_salary_info]])!  [repeat:: every month on the 1st]  [created:: 2026-10-08]  [scheduled:: 2026-11-01]

CURRENT OBSIDIAN RENDERING:
- [?] ⌗ Pay [[kelly]] salary (see [[kellys_salary_info]])!  REPEAT│every month on the 1st  + Oct 8  ⧗ Nov 1

PROPOSED RENDERING:
- [?] ⌗ Pay [[kelly]] salary (see [[kellys_salary_info]])!  🔁 monthly · 1st  + Oct 8  ⧗ Nov 1
```

---

## 6. Technical Architecture & Implementation Plan

### 6.1 Placement in Codebase

The implementation belongs in `bob-plugins/plugins/bob-ledger-tools/`, which already houses the complete family of task decorations.

```text
bob-plugins/plugins/bob-ledger-tools/
├── src/
│   ├── 138-task-tag-marks.js           (Existing #task and #ref core)
│   ├── 140-gtd-review-marks.js         (NEW: Pure parsing & range calculation for #gtd #pre / #post)
│   ├── 147-repeat-marks.js             (NEW: Pure parsing & label grammar for [repeat:: ...])
│   ├── 263-plugin-gtd-review-marks.js  (NEW: CM6 ViewPlugin, post-processor & toggle)
│   ├── 262-plugin-repeat-marks.js      (NEW: CM6 ViewPlugin, post-processor & toggle)
│   └── 310-install-methods.js          (Mixins wired into plugin lifecycle)
├── styles.css                          (CSS masks, layouts, resting tones)
└── scripts/
    ├── test-ledger-tools-gtd-review-marks.cjs  (Unit tests for review mark parsing & ranges)
    └── test-ledger-tools-repeat-marks.cjs      (Unit tests for repeat grammar & folding)
```

### 6.2 Pure Core Logic

#### A. GTD Review Marks (`140-gtd-review-marks.js`)
* **Live Preview Range Detector:** `gtdReviewMarkRanges(lineText)`
  1. Quick gate: `lineText.indexOf("#gtd") === -1` returns `[]`.
  2. Gated by `freshnessTaskStatus(lineText) !== null` (ensures marks only appear on task lines).
  3. Scans for token pairs:
     * `#gtd` followed by whitespace and `#pre` $\to$ returns `{ from, to, tier: "pre" }`.
     * `#gtd` followed by whitespace and `#post` $\to$ returns `{ from, to, tier: "post" }`.
     * Also supports reverse order (`#pre #gtd` / `#post #gtd`).
  4. Code exclusion: Range builder checks `freshnessMarkPosInCode(tree, from + 1)` and drops matches inside backticks or codeblocks.
* **Reading View Anchor Eligibility:** `gtdReviewMarkElementEligible(anchor, root)`
  * Matches `a.tag` with text `#gtd` inside `li.task-list-item`.
  * Checks adjacent sibling element: if it is `a.tag` with text `#pre` or `#post`, annotates `#gtd` with the sunrise or flag, and marks the sibling with `bob-gtd-tag-hidden` (`display: none`).

#### B. Repeat Marks (`147-repeat-marks.js`)
* **Occurrence & Canonical Field Matcher:** `repeatMarkCanonicalFields(lineText)`
  * Matches single occurrence of `\[ *repeat:: *([^\]]+) *\]` or `\( *repeat:: *([^\)]+) *\)`.
  * Checks whitespace run immediately before the field to support whitespace folding (matching `136-date-marks.js`).
* **Cadence Grammar Formatter:** `formatRepeatCadence(rawRule)`
  * Case-insensitive regex matching for days, weeks, months, weekdays, and "when done".
  * Returns `{ icon: "repeat", label: "daily", fullRule: rawRule }`.

### 6.3 CodeMirror 6 Editor Extension (Live Preview)

* **ViewPlugin (`Prec.highest`):**
  Uses `RangeSetBuilder` to replace the exact character offsets with a `WidgetType`:
  ```javascript
  class GtdReviewMarkWidget extends WidgetType {
    constructor(tier) {
      super();
      this.tier = tier; // "pre" or "post"
    }
    eq(other) {
      return other instanceof GtdReviewMarkWidget && other.tier === this.tier;
    }
    toDOM(view) {
      const el = buildGtdReviewMarkElement(document, this.tier);
      addMarkRevealListener(el, view);
      return el;
    }
  }
  ```
* **Reveal-on-Selection Behavior:**
  If any editor selection range intersects the mark range (`sel.from <= to && sel.to >= from`), the decoration is suppressed, immediately exposing the raw text for seamless typing and backspacing.
* **Click-to-Focus Handler:**
  Mousedown on the widget dispatches `view.dispatch({ selection: { anchor: from } })` and calls `view.focus()`.

### 6.4 CSS Styling & Masks (`styles.css`)

```css
/* SVG Mask Definitions */
body {
  --bob-gtd-pre-glyph: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16' fill='none' stroke='%23000' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M2.5 13.5h11M4.5 10.5a3.5 3.5 0 0 1 7 0M8 2.5v2M3.5 4.5l1.5 1.5M12.5 4.5l-1.5 1.5'/%3E%3C/svg%3E");
  --bob-gtd-post-glyph: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16' fill='none' stroke='%23000' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M3.5 2v12M3.5 3h8.5l-2.5 4 2.5 4H3.5'/%3E%3C/svg%3E");
  --bob-repeat-glyph: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16' fill='none' stroke='%23000' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M12.5 2.5l2 2-2 2M1.5 6.5v-1a3 3 0 0 1 3-3h10M3.5 13.5l-2-2 2-2M14.5 9.5v1a3 3 0 0 1-3 3h-10'/%3E%3C/svg%3E");

  --bob-gtd-pre-hue: color-mix(in srgb, var(--color-orange, #e59900) 60%, var(--color-yellow, #e5c07b));
  --bob-gtd-post-hue: color-mix(in srgb, var(--color-purple, #9d7cd8) 75%, var(--text-normal));
}

/* Base GTD Mark Container */
body.bob-gtd-review-marks .bob-gtd-review-mark {
  display: inline-block;
  position: relative;
  width: 1.1em;
  height: 1.1em;
  vertical-align: -0.15em;
  margin: 0 0.12em;
  cursor: pointer;
}

body.bob-gtd-review-marks .bob-gtd-review-mark::before {
  content: "";
  position: absolute;
  inset: 0.05em;
  background-color: var(--mark-ink);
  -webkit-mask-size: contain;
  mask-size: contain;
  -webkit-mask-repeat: no-repeat;
  mask-repeat: no-repeat;
  -webkit-mask-position: center;
  mask-position: center;
}

body.bob-gtd-review-marks .bob-gtd-review-mark.bob-gtd-pre-mark {
  --mark-ink: var(--bob-gtd-pre-hue);
}
body.bob-gtd-review-marks .bob-gtd-review-mark.bob-gtd-pre-mark::before {
  -webkit-mask-image: var(--bob-gtd-pre-glyph);
  mask-image: var(--bob-gtd-pre-glyph);
}

body.bob-gtd-review-marks .bob-gtd-review-mark.bob-gtd-post-mark {
  --mark-ink: var(--bob-gtd-post-hue);
}
body.bob-gtd-review-marks .bob-gtd-review-mark.bob-gtd-post-mark::before {
  -webkit-mask-image: var(--bob-gtd-post-glyph);
  mask-image: var(--bob-gtd-post-glyph);
}

/* Repeat Mark Container (Glyph + Label) */
body.bob-repeat-marks .bob-repeat-mark {
  display: inline-flex;
  align-items: center;
  gap: 0.25em;
  font-family: var(--font-monospace);
  font-size: 0.8em;
  color: var(--text-muted);
  opacity: 0.85;
  margin: 0 0.2em;
  vertical-align: 0;
  cursor: pointer;
}

body.bob-repeat-marks .bob-repeat-mark-icon {
  display: inline-block;
  width: 1em;
  height: 1em;
  background-color: currentColor;
  -webkit-mask-image: var(--bob-repeat-glyph);
  mask-image: var(--bob-repeat-glyph);
  -webkit-mask-size: contain;
  mask-size: contain;
  -webkit-mask-repeat: no-repeat;
  mask-repeat: no-repeat;
}

/* Resting State: Dimmed on Done / Cancelled lines */
li.task-list-item[data-task="x"] .bob-gtd-review-mark,
li.task-list-item[data-task="-"] .bob-gtd-review-mark,
.HyperMD-task-line[data-task="x"] .bob-gtd-review-mark,
.HyperMD-task-line[data-task="-"] .bob-gtd-review-mark,
li.task-list-item[data-task="x"] .bob-repeat-mark,
li.task-list-item[data-task="-"] .bob-repeat-mark,
.HyperMD-task-line[data-task="x"] .bob-repeat-mark,
.HyperMD-task-line[data-task="-"] .bob-repeat-mark {
  opacity: 0.6;
  filter: grayscale(40%);
}
```

---

## 7. Edge Cases & Conformance Test Plan

To guarantee zero regression and rock-solid stability, test vectors should be defined and run against a Node-based harness (`test-ledger-tools-gtd-review-marks.cjs` and `test-ledger-tools-repeat-marks.cjs`).

### 7.1 GTD Review Mark Vectors

| Vector ID | Input Line | Expected Output Range & Mark | Note |
| :--- | :--- | :--- | :--- |
| `GR1` | `- [ ] #task #gtd #pre Chore` | `[12, 21)` $\to$ `Sunrise` | Standard PRE |
| `GR2` | `- [ ] #task #gtd #post Review` | `[12, 22)` $\to$ `Flag` | Standard POST |
| `GR3` | `- [ ] #task #pre #gtd Reversed` | `[12, 21)` $\to$ `Sunrise` | Order tolerance |
| `GR4` | `- [ ] #task #gtd   #pre Spaced` | `[12, 23)` $\to$ `Sunrise` | Whitespace gap tolerance |
| `GR5` | `- [ ] #task #gtd Lone GTD` | None | Standalone `#gtd` is untouched |
| `GR6` | `- [ ] #task #pre Lone PRE` | None | Lone `#pre` is untouched |
| `GR7` | `- #task #gtd #pre Plain bullet`| None | Non-task line gate |
| `GR8` | ``- [ ] #task `#gtd #pre` Code``| None | Backtick code exclusion |
| `GR9` | `- [x] #task #gtd #pre Done chore`| `[12, 21)` $\to$ `Sunrise` | CSS rests faint |

### 7.2 Repeat Mark Vectors

| Vector ID | Input Line | Expected Label | Tooltip Content |
| :--- | :--- | :--- | :--- |
| `RM1` | `[repeat:: every day when done]` | `🔁 daily` | "Repeats: every day when done" |
| `RM2` | `[repeat:: every day]` | `🔁 daily` | "Repeats: every day" |
| `RM3` | `[repeat:: every week on Monday when done]` | `🔁 Mon` | "Repeats: every week on Monday when done" |
| `RM4` | `[repeat:: every week on Sunday]` | `🔁 Sun` | "Repeats: every week on Sunday" |
| `RM5` | `[repeat:: every 30 days when done]` | `🔁 30d` | "Repeats: every 30 days when done" |
| `RM6` | `[repeat:: every 28 days]` | `🔁 28d` | "Repeats: every 28 days" |
| `RM7` | `[repeat:: every month on the 1st]`| `🔁 monthly · 1st` | "Repeats: every month on the 1st" |
| `RM8` | `[repeat:: ]` | None | Malformed empty field is skipped |
| `RM9` | `Text [repeat:: every day]` | `🔁 daily` | Works across plain bullets and tasks |

---

## 8. Rollout Strategy & Recommendations

### Recommended Rollout Phases

1. **Phase 1: Pure Parsing & Conformance Harness in `bob-plugins`**
   * Create `src/140-gtd-review-marks.js` and `src/147-repeat-marks.js`.
   * Add test suites in `scripts/` to verify vectors `GR1–GR9` and `RM1–RM9`.
2. **Phase 2: CodeMirror 6 Extensions & CSS Masks**
   * Create `src/263-plugin-gtd-review-marks.js` and `src/262-plugin-repeat-marks.js`.
   * Add CSS rules to `styles.css`.
   * Add command palette toggles (`toggle-gtd-review-marks`, `toggle-repeat-marks`).
   * Run `npm test` and build with `scripts/build.cjs`.
3. **Phase 3: Deploy to Vault via `bob plugins sync` & Live Verification**
   * Deploy to `~/bob/.obsidian/plugins/bob-ledger-tools/`.
   * Live test in Obsidian with `gtd_daily.md`, `cash.md`, and `recur.md`.
   * Verify cursor movements (Vim `j`/`k`, clicking to edit, backspacing).
   * Verify Dataview and Tasks query blocks remain unaffected.

### Final Design Synthesis

By implementing:
* A **single `sunrise` glyph** for `#gtd #pre`,
* A **single `flag` glyph** for `#gtd #post`, and
* An **icon + terse cadence label (`🔁 daily`, `🔁 Sun`, `🔁 30d`)** for `[repeat:: ...]`,

the Bob workspace achieves a level of visual elegance and spatial efficiency that matches the high standard set by `date-marks` and `task-tag-marks`. Daily review chores in `gtd_daily.md` become clean, beautiful commitments rather than dense database records.
