# Walker Footers in Obsidian: Architectural Analysis, UX Design, and Critique for Mode-Coupled Status Bar Cockpits

**Author:** Researcher gem (5-researcher swarm)  
**Date:** 2026-11-12  
**Target Repositories:** `bob-plugins` (`bob-ledger-tools`, `bob-navigation-hotkeys`), `bob-cli`  
**Relevant Prior Decisions:** `decisions:review-walk-is-tiered`, `decisions:task-lanes-are-sticky`, `decisions:today-is-read-from-the-ledger`, `decisions:alt-n-answers-from-due-rows`, `decisions:answering-advances-the-walk`

---

## 1. Executive Summary

This report provides an in-depth architectural analysis, usability critique, and design specification for evolving Obsidian's desktop status bar from a static, always-visible GTD review footer into a dynamic, mode-coupled **Walker Footer** system.

### The Proposal Under Evaluation
Currently, the Morning GTD Review Footer (`.bob-freshness`, hosted by `bob-ledger-tools`) is permanently mounted on desktop Obsidian as long as any task queue exists. The user proposal introduces two fundamental shifts:
1. **Mode-Gating the Review Footer:** Restrict the display of the GTD Review Footer to only when the `s` walk is active (i.e. `s` is selected in the Bracket Mode Indicator `[[ s w n ]]`, meaning `[[` and `]]` will trigger `[s` / `]s` review jumps).
2. **Introducing Symmetrical Walker Footers:** Add two new, dedicated status-bar footers that appear dynamically when their respective walk is active:
   - **The Lane Walker Footer (`w`):** Displays real-time metrics and cursor progress for the active plan lanes (PENDING / NEXT / READY tasks off today's plan).
   - **The Link Walker Footer (`n`):** Displays previous and next navigation link targets for the active document (daily note and periodic note sequence traversal).
3. **Glossary Formalization:** Add an authoritative "Walker Footer" glossary strand defining this generalized status-bar cockpit family.

### Core Verdict
The core concept is **ergonomically sound, conceptually unified, and highly desirable**:
- **Eliminates Status Bar Clutter:** During deep afternoon execution, displaying persistent review counts (e.g. `Review 28 due · 0 commitments · Upkeep budget met`) imposes unnecessary cognitive noise.
- **Completes the Mental Model:** Bob already exposes the `[[ s w n ]]` Bracket Mode Indicator, yet previously only `s` had a dedicated status bar cockpit, while `w` relied solely on transient screen toasts and `n` had zero ambient presence. Unifying all three walks under a polymorphic "Walker Footer" creates elegant symmetry.

### Critical Findings & Essential Refinements
However, a naive implementation would introduce four notable usability and architectural pitfalls:
1. **The "Transient Jump" Review Interruption:** In Bob, typing `]n` or `]w` immediately switches the bracket repeat mode to that family. If Bryan is in the middle of morning GTD review and uses `]n` to inspect a referenced note, the Review Footer would instantly disappear, hiding remaining commitment counts.  
   *Refinement:* Add a subtle "commitments pending" indicator (e.g. an amber notification dot or pip) on the `s` segment within `[[ s w n ]]`, ensuring Bryan is never blindsided by forgotten morning review commitments while in `w` or `n` mode.
2. **`Alt+P` Priority Preview Parity:** The existing review footer serves double duty: when on any open task with a priority, it displays the `Alt+P` Quick Roll recommendation (`Alt+P roll P2` or interactive answer chips). Tasks traversed during the `w` (Lane) walk are actively prioritized.  
   *Refinement:* The Lane Walker Footer (`w`) must fully inherit the `Alt+P` Quick Roll preview slot, ensuring parity during lane execution.
3. **Queue vs. Local Traversal Asymmetry:** While `s` and `w` are vault-wide queues with ordered integer ranks ($r/N$), `n` is a document-local relative navigation walk across body links.  
   *Refinement:* The Link Walker Footer (`n`) must not attempt to fake a global queue. Instead, it should act as an interactive directional control cockpit showing explicit relative targets (e.g. `‹ 20261111 · 20261113 ›`) with direct click-to-jump affordances.
4. **Inter-Plugin Architectural Boundary:** Multiple plugins creating independent `addStatusBarItem()` elements that fight for `margin-right: auto` causes layout jumping and DOM ordering races in Obsidian.  
   *Refinement:* Implement a **Single Walker Slot Architecture** hosted in `bob-ledger-tools` (which already owns the layout, responsive width-fitting engine, tier colors, and CSS), consuming a clean, decoupled `api.bracketMode` event stream and `api.linkWalk` data from `bob-navigation-hotkeys`.

---

## 2. Background: Current System Architecture & Topography

### 2.1 The Obsidian Status Bar Split Today
In Obsidian desktop, Bob's status bar is split into two primary zones:

```text
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│ [Left: Primary Flex Slot]                                            [Right: Pinned Indicators]  │
│ ⟳ Review 7 due · 4 commitments · ]s next   NEW 1 · PENDING 2 ...       [[ ⟨s⟩ w  n ]]  ... 13:45 │
│ (.bob-freshness, margin-right: auto)                                   (.bob-bracket-mode)       │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

1. **The Morning GTD Review Footer (`.bob-freshness`):** Owned by `bob-ledger-tools`. Positioned on the leading edge with `margin-right: auto` and `flex: 1 1 auto`. It absorbs all remaining horizontal width and uses a `ResizeObserver` to progressively drop components as the window narrows.
2. **The Bracket Mode Indicator (`.bob-bracket-mode`):** Owned by `bob-navigation-hotkeys`. Positioned in the trailing area with `flex: 0 0 auto`. It displays `[[ s w n ]]` with a sliding accent thumb over the active letter.

### 2.2 The Three Bracket Walk Families
Bob defines three first-class bracket walk families, mapped in the vault vimrc:

| Family | Walk Name | Primary Keymaps | Target Scope | Underlying Model / Source |
| :---: | :--- | :--- | :--- | :--- |
| **`s`** | **Review Walk** | `]s` / `[s`<br>`]S` / `[S` (groups) | Shared GTD Freshness Queue across vault | `freshnessEnsureMemo().queue`<br>Tiers: PRE $\to$ NEW $\to$ PROJECTS $\to$ PENDING $\to$ NEXT $\to$ RECURRING $\to$ TICKLER $\to$ ROTTEN $\to$ POST |
| **`w`** | **Lane Walk** | `]w` / `[w`<br>`]W` / `[W` (lanes) | Plan tasks off Today across vault | `api.laneWalk v2` (`laneWalkQueueFromTasks`)<br>Lanes: PENDING (WIP) $\to$ NEXT $\to$ READY |
| **`n`** | **Link Walk** | `]n` / `[n`<br>*(no uppercase)* | Body navigation links in current note | `findFirstRenderedLinkInLine`<br>Matches: `prev`/`next`, `‹ W44`/`W46 ›`, etc. |

The repeat keys `]]` (forward) and `[[` (backward) repeat whichever family was last used, or whichever letter Bryan explicitly clicked on the `[[ s w n ]]` indicator.

### 2.3 Current Presentation Lifecycle
- **Review Walk (`s`):** Has a comprehensive, persistent status-bar footer displaying remaining queue counts, commitment counts, tier groups, upkeep meter, and `Alt+P` previews. Clicking the footer executes `bob-navigation-hotkeys:jump-to-next-due-task`.
- **Lane Walk (`w`):** Has **no status bar presence**. When Bryan presses `]w`, it displays a temporary overlay toast (`renderLaneWalkNoticeFragment`) with an ASCII/CSS rail and lane color bars, which fades after several seconds.
- **Link Walk (`n`):** Has **no status bar presence and no toast**. Navigation occurs silently, displaying only an error notice (`No next link found`) if the target is absent.

```mermaid
flowchart TD
    subgraph Current Architecture
        A[User Action / Keypress] --> B{Key Pressed}
        B -->|]s or [s| C[Set Mode 's' in nav-hotkeys]
        B -->|]w or [w| D[Set Mode 'w' in nav-hotkeys]
        B -->|]n or [n| E[Set Mode 'n' in nav-hotkeys]
        
        C -.-> F[Review Footer: Always Shown in ledger-tools]
        D -.-> G[Lane Walk Toast: Transient]
        E -.-> H[Link Walk: Silent Jump]
        
        F --- I[Shows 's' queue metrics 24/7 regardless of mode]
    end
```

---

## 3. Critical Analysis & Critique of the User's Plan

### 3.1 Is Mode-Gating the Review Footer a Good Idea?
**Verdict: YES, with high confidence.**

#### The Benefits
1. **Reduces Ambient Cognitive Noise:** GTD review is a morning ritual. Once the commitment tiers (PRE, NEW, PROJECTS, PENDING, NEXT, RECURRING, TICKLER) are cleared, Bryan moves into deep execution. Having the review footer persist throughout the entire workday continuously reporting backlogged ROTTEN tasks is visual clutter that detracts from execution focus.
2. **Context-Sensitive HUD:** Converting the status bar into an active "heads-up display" (HUD) for the current tool creates a tighter feedback loop. When executing lanes (`w`), the user cares about `PENDING` and `NEXT` tasks. When browsing note chronologies (`n`), the user cares about relative navigation targets.
3. **Visual Alignment with `[[ s w n ]]`:** The Bracket Mode Indicator promises that `[[` and `]]` will act upon the lit mode. Having the status bar footer explain *what* that walk contains reinforces the user's mental model.

---

### 3.2 Critique & Essential Adjustments

While the user's premise is sound, a naive implementation creates four major usability risks that must be addressed in the final design.

#### Risk 1: The "Transient Jump" Interruption & Morning Review Amnesia
* **The Hazard:** In Bob, any press of `]s`, `]w`, or `]n` automatically calls `rememberBracketRepeatType()`. During morning GTD review, Bryan often encounters tasks with cross-references (e.g. reviewing an area note or checking yesterday's log via `]n`). The moment `]n` is pressed, the bracket mode shifts to `n`. Under a strict mode-gated system, the review footer would immediately vanish, replaced by the link footer. If Bryan has 2 unfinished commitments in his review walk, he may lose track of them because the review footer is no longer visible.
* **Adjustment 1: Commitment Notification Badge on `[[ s w n ]]`:**  
  When the `s` walk has unfinished commitment tiers (`read.commitments > 0`), the `s` letter in the `[[ s w n ]]` indicator should display a subtle accent badge (e.g. an amber pip or dot: `[[ s• ⟨w⟩ n ]]`). The tooltip for `s` should clearly state: `Review: 2 commitments still due — click to return to review`. This guarantees that morning review is never silently abandoned.

#### Risk 2: Loss of the `Alt+P` Quick Roll Preview during Execution
* **The Hazard:** The current review footer displays the `Alt+P` Quick Roll preview (e.g. `Alt+P roll P2 1/1`) when the cursor sits on any prioritized task, even off-walk. During execution, Bryan frequently navigates tasks via the `w` walk. If the review footer is hidden and the `w` footer does not implement the `Alt+P` slot, Bryan loses his live priority and roll previews.
* **Adjustment 2: Universal Priority / Answer Slot in the Lane Walker Footer:**  
  The Lane Walker Footer (`w`) must include a dedicated `Alt+P` preview slot that mirrors the review footer's implementation, rendering roll, decay, and assignment hints when resting on an open task.

#### Risk 3: The Cold Start / `none` Bracket Mode State
* **The Hazard:** On a new device or when local storage is cleared, `readBracketRepeatType()` returns `null` (rendered as `mode: "none"` with no thumb). What does the status bar display?
* **Adjustment 3: Intelligent Default / Minimal Prompt:**  
  If mode is `none`:
  - If GTD review commitments are due today: Default the active walker view to `s` (prompting the morning review).
  - If no commitments are due: Show a quiet placeholder `Walkers ready · Press ]s, ]w, or ]n to start` or collapse the walker slot until a walk command is invoked.

#### Risk 4: Asymmetry Between Queue Walks (`s`, `w`) and Traversal Walks (`n`)
* **The Hazard:** Designers often try to force uniform data models onto disparate systems. `s` and `w` are global lists indexed by integer positions ($r/N$). `n` has no global list; it only knows about `prev` and `next` links relative to the currently active markdown document.
* **Adjustment 4: Directional Traversal Cockpit for `n`:**  
  Rather than attempting to construct a synthetic queue of all links across the vault, the `n` footer should be designed explicitly as a **Directional Traversal Cockpit**. It displays the specific previous and next targets of the current note with interactive click targets.

---

## 4. Architectural Design: Inter-Plugin Coordination

### 4.1 Comparison of Architectural Approaches

Where should the Walker Footer live, and which plugin should own what?

```mermaid
flowchart LR
    subgraph Option A: Fragmented Footers
        LT1[bob-ledger-tools] -->|addStatusBarItem| F1[Review Footer]
        LT1 -->|addStatusBarItem| F2[Lane Footer]
        NH1[bob-navigation-hotkeys] -->|addStatusBarItem| F3[Link Footer]
    end
    
    subgraph Option B: Unified Host in ledger-tools (Recommended)
        NH2[bob-navigation-hotkeys] -->|api.bracketMode| LT2[bob-ledger-tools]
        NH2 -->|api.linkWalk| LT2
        LT2 -->|Single addStatusBarItem| WF[Unified Walker Footer Slot]
        WF --> View{Active Mode?}
        View -->|s| V1[Review Walker View]
        View -->|w| V2[Lane Walker View]
        View -->|n| V3[Link Walker View]
    end
```

| Criterion | Option A: Multiple Separate Status Bar Items | Option B: Unified Host in `bob-ledger-tools` (Recommended) | Option C: Unified Host in `bob-navigation-hotkeys` |
| :--- | :--- | :--- | :--- |
| **DOM Stability** | **Poor:** Toggling `display: none` across 3 different status bar items causes layout jitter and flex reflows in Obsidian. | **Excellent:** Single DOM node container mounted once; inner contents update idempotently. | **Excellent:** Single DOM node container mounted once. |
| **Status Bar Positioning** | **Unstable:** Obsidian status bar items cannot be dynamically reordered. If plugins load in different orders, item positions drift. | **Rock Solid:** Reuses the existing `.bob-freshness` slot at the extreme left (`margin-right: auto`). | **Complex:** Must transfer `margin-right: auto` ownership from ledger-tools to nav-hotkeys. |
| **Code Reuse** | **Low:** Duplicates `ResizeObserver` width-fitting, tooltip handlers, and styling across plugins. | **Maximum:** Reuses 100% of ledger-tools' existing width-fitting engine, CSS classes, tier colors, and chip renderers. | **Low:** Requires porting extensive CSS and responsive truncation logic into nav-hotkeys. |
| **Data Locality** | Mixed. | **High:** `s` and `w` queues are already computed in ledger-tools (`freshnessEnsureMemo` and `api.laneWalk`). Only `n` links are passed in. | **Moderate:** Must query ledger-tools for both `s` and `w` queues across the plugin boundary on every turn. |

### 4.2 The Recommended Solution: Single Walker Slot in `bob-ledger-tools`

We recommend **Option B**:
1. `bob-navigation-hotkeys` publishes an additive API namespace: `api.bracketMode v1`:
   - `getMode()`: returns `"s" | "w" | "n" | null`
   - `onModeChange(listener)`: event emitter triggered whenever `rememberBracketRepeatType()` changes the active mode.
   - `api.linkWalk v1`: exposes `getNoteNavLinks(content)` returning `{ prev: LinkTarget | null, next: LinkTarget | null, series: string | null }`.
2. `bob-ledger-tools` renames its status bar host internally to `this.walkerStatusEl` (retaining `.bob-freshness` and `.bob-walker-footer` classes for styling continuity).
3. `bob-ledger-tools` listens to `api.bracketMode.onModeChange`. When the mode switches, it updates its view model:
   - If mode is `"s"`: Evaluates `freshnessFooterView(...)` (GTD Review Walker).
   - If mode is `"w"`: Evaluates `laneWalkFooterView(...)` (Lane Walker).
   - If mode is `"n"`: Evaluates `linkWalkFooterView(...)` (Link Walker).
4. Clicking the main button on the walker footer executes the active walk:
   - `"s"` $\to$ `bob-navigation-hotkeys:jump-to-next-due-task`
   - `"w"` $\to$ `bob-navigation-hotkeys:jump-to-next-lane-task`
   - `"n"` $\to$ `bob-navigation-hotkeys:open-next-link`

---

## 5. Detailed Design Specifications for the Walker Footers

### 5.1 Design 1: The GTD Review Walker Footer (`s`)

The Review Walker Footer represents the existing morning review engine, refined to participate seamlessly in the walker family.

#### Visual Hierarchy & States

```text
Wide Display (Off-row overview):
⟳ Review 7 due · 4 commitments   NEW 1 · PENDING 2 · RETURNED 1 · ROTTEN 3   ✓ 0/15 today · ]s next

Wide Display (Cursor landed on queue row):
⟳ Review 2/7 · PENDING 1/2 · confirmed yesterday   NEW 1 · NEXT 2 · ROTTEN 3   ✓ 0/15 today   [Alt+P roll P2]

Narrow Display (Progressively collapsed):
⟳ Review 2/7 · PENDING 1/2   [Alt+P roll P2]
```

#### Visual Spec
- **Icon:** `⟳` (`refresh-cw` Lucide icon or theme glyph).
- **Prefix:** `Review` (or `⟳ Review`).
- **Counters:** Active rank / total (`r/N`) when on a queue task; remaining due (`N due`) when off-queue.
- **Commitment Indicator:** Explicit count (`K commitments`), `Commitments done`, or `Upkeep budget met`.
- **Tier Group Chips:** Styled with canonical GTD tier colors (`data-review-tier="pre|new|pending|next|..."`).
- **Upkeep Meter:** `✓ upkeep/budget today`.
- **Answer / Hint Slot:** Tier-aware `Alt+P` Quick Roll preview or dynamic tinted answer chip on TICKLER rows.

---

### 5.2 Design 2: The Lane Walker Footer (`w`)

The Lane Walker Footer provides real-time situational awareness over the active task backlog (tasks off today's plan).

#### Core Data Source
Driven by `bob-ledger-tools` `api.laneWalk v2` (`laneWalkQueueFromTasks`), which scans all tasks in the vault against today's plan:
- **`pending` (WIP):** Tasks in progress (`dashboardLaneSectionVisible(task, ..., "pending")`).
- **`next`:** Tasks marked Next (`dashboardLaneSectionVisible(task, ..., "next")`).
- **`ready`:** Confirmed, fresh tasks eligible for work (`readyLaneScanFromTasks(...)`).
- Tasks already linked under today's open Pomodoros are counted separately (`todayPending`, `todayNext`).

#### Visual Hierarchy & States

```text
State A: Off-walk Overview (Wide Desktop)
⤹ Lanes 14 active   2 WIP · 4 Next · 8 Ready   [───▪▪▪▪────────]   ]w next

State B: Cursor Landed on Lane Task (NEXT Lane)
⤹ Lanes 3/14 · NEXT 1/4 · ‹proj/bob-cli› Fix memory leak   2 WIP · 8 Ready   [Alt+P roll P2]

State C: Cursor Landed on WIP Task (PENDING Lane)
⤹ Lanes 1/14 · WIP 1/2 · ‹work/client› Draft release brief   4 Next · 8 Ready   [Alt+N release]

State D: Narrow Display (Responsive Truncation)
⤹ Lanes 3/14 · NEXT 1/4   [Alt+P roll P2]

State E: Lanes Clear
✓ Lanes clear · 0 WIP · 0 Next · 0 Ready   ]w scan
```

#### Element Breakdown & Styling
1. **Icon & Lead:** `⤹` (`arrow-down-right` or `corner-down-right`) with the title `Lanes`.
2. **Lane Count Badges:**
   - **`WIP` (PENDING):** Painted in warm amber (`--text-warning` / `#e5a50a` with `.is-pending`), reflecting in-progress commitments.
   - **`NEXT`:** Painted in vibrant cyan/blue (`--interactive-accent` / `#00b4d8` with `.is-next`), reflecting primed tasks.
   - **`READY`:** Painted in quiet purple/violet (`--text-accent` / `#a855f7` with `.is-ready`), reflecting the confirmed backlog.
3. **Miniature Lane Rail:** A compact 40px inline horizontal bar showing the relative proportions of WIP / Next / Ready tasks with a bright cursor pip showing where the active task sits.
4. **Context & Note Breadcrumb:** When on a lane task, displays the parent note or area stem (`‹proj/bob-cli›`) followed by the truncated task description.
5. **Quick Roll / Action Hint:** Displays `Alt+P roll P2` if prioritized, or `Ctrl+Shift+Enter today` / `Alt+N release` to guide lane advancement.
6. **Click Action:** Executes `bob-navigation-hotkeys:jump-to-next-lane-task` (`]w`). `Shift+Click` executes `]W` (jump to next lane).

---

### 5.3 Design 3: The Link Walker Footer (`n`)

The Link Walker Footer acts as a directional navigation cockpit for chronological and sequential notes.

#### Core Data Source
Driven by `bob-navigation-hotkeys` `findFirstRenderedLinkInLine` scanning the active markdown document for navigation links:
- **Daily Notes:** Links aliased as `prev` and `next` (e.g. `[[20261111|prev]] · [[20261113|next]]`).
- **Periodic Notes (Weeks/Months/Years):** Links prefixed with `‹` / `<` or suffixed with `›` / `>` (e.g. `[[2026-W45|‹ W45]] · [[2026-W47|W47 ›]]`).
- **Sequential Project Notes:** Linked sequence chains using arrow navigation.

#### Visual Hierarchy & States

```text
State A: Bidirectional Links (Daily Note `20261112`)
⇄ Links   ‹ 20261111   ·   20261113 ›   [n] / ]n

State B: Bidirectional Links (Weekly Note `2026-W46`)
⇄ Links   ‹ W45   ·   W47 ›   [n] / ]n

State C: Start of Series (Only Forward Link Exists)
⇄ Links   ‹ (start)   ·   2026-W02 ›   ]n next

State D: End of Series (Only Backward Link Exists)
⇄ Links   ‹ 2026-W51   ·   (end) ›   [n prev

State E: Active Note Has No Navigation Links
⇄ Links: none in note   [n] / ]n

State F: Active View Is Not a Markdown Note (e.g. Canvas, PDF, Image)
⇄ Links: no active note
```

#### Element Breakdown & Styling
1. **Icon & Lead:** `⇄` (`arrow-left-right`) with the title `Links`.
2. **Interactive Segmented Affordances:**
   - Left arrow segment (`‹ 20261111`): A clickable button region. Clicking it executes `[n` (`openLabeledBodyLink("prev")`).
   - Center separator: Subtle dot `·`.
   - Right arrow segment (`20261113 ›`): A clickable button region. Clicking it executes `]n` (`openLabeledBodyLink("next")`).
3. **Target Highlighting:** Hovering over an arrow segment highlights the destination note in Obsidian's accent color.
4. **Keybinding Hint:** Quiet trailing hint `[n / ]n`.

---

## 6. Authoritative Glossary Strand: "Walker Footer"

Below is the complete, canonical specification for the new glossary note to be published under `sase/memory/glossary/walker-footer.md`:

```markdown
---
keyword: Walker Footer
aliases:
  - "walker footers"
  - "walk footer"
---

The desktop Obsidian status-bar cockpit that visualizes the currently active bracket-walk family (`s` review, `w` lanes, or `n` links) as selected in the [[bracket-mode-indicator]] (`[[ s w n ]]`). A walker footer keeps the walk's queue progress, current cursor rank, and navigational targets in view without opening modal cards or reading vault files. Exactly one walker footer is active at a time, governed dynamically by `bob-navigation-hotkeys`'s remembered bracket-repeat type:

1. **[[morning-gtd-review-footer|Review Walker Footer]] (`s`):** The GTD review cockpit over the shared [[task-freshness]] queue (`]s` / `[s`), showing remaining due counts, commitment progress, tier breakdowns, and the `Alt+P` roll preview.
2. **Lane Walker Footer (`w`):** The daily plan execution cockpit over Today's PENDING, NEXT, and READY task lanes (`]w` / `[w`), showing active task counts by lane, on-walk queue position (`Lanes r/N · LANE i/M`), lane-tinted indicators, and the `Alt+P` roll preview.
3. **Link Walker Footer (`n`):** The document traversal cockpit over active-note body navigation links (`]n` / `[n`), showing previous and next relative targets (e.g. daily note dates `‹ 20261111 · 20261113 ›` or period weeks `‹ W44 · W46 ›`) with direct click-to-jump controls.

A walker footer is a read-only projection: clicking its main element triggers the forward jump of the active walk (`]s`, `]w`, or `]n`), while tooltips summarize full queue metrics and shortcut keymaps. When the bracket repeat mode is unset (`none`), the footer remains dormant or yields its space; when a walk's queue is clear, the footer presents an unobtrusive clear indicator or ambient priority preview rather than cluttering the status bar. When morning review commitments remain due in the `s` walk while `w` or `n` is active, the `s` segment in the [[bracket-mode-indicator]] wears an accent notification pip so review obligations remain visible throughout the day.
```

---

## 7. Implementation Roadmap & Technical Specifications

### 7.1 Phase 1: `bob-navigation-hotkeys` API Exposure
Add bracket mode event streaming and link extraction to `bob-navigation-hotkeys`:
1. **Extend `src/546-plugin-bracket-repeat.js`:**
   - In `rememberBracketRepeatType(type)`, dispatch an internal event `bob-bracket-mode-changed` carrying `{ mode: normalized, previous: old }`.
2. **Expose `api.bracketMode v1` in `src/480-review-jump-and-nav-api.js`:**
   ```javascript
   bracketMode: {
     version: 1,
     getMode: () => plugin.readBracketRepeatType(),
     setMode: (type) => plugin.rememberBracketRepeatType(type),
     onModeChange: (cb) => plugin.registerBracketModeListener(cb),
   }
   ```
3. **Expose `api.linkWalk v1` in `src/480-review-jump-and-nav-api.js`:**
   ```javascript
   linkWalk: {
     version: 1,
     scanCurrentNoteLinks: () => {
       const view = plugin.getActiveMarkdownView();
       if (!view || !view.editor || !view.file) return null;
       const content = view.editor.getValue() || "";
       const prev = plugin.findFirstRenderedLink(content, "prev");
       const next = plugin.findFirstRenderedLink(content, "next");
       return { prev, next, path: view.file.path };
     }
   }
   ```

### 7.2 Phase 2: Pure Walker Models in `bob-ledger-tools`
Create pure model evaluators that return immutable view objects:
1. **`laneWalkFooterView(laneMemo, options)`:**
   - Computes `{ dueText, contextText, detailText, hintText, groups, rail, action, tooltip, quickRoll }`.
   - Computes lane breakdown: `counts.pending`, `counts.next`, `counts.ready`.
   - Matches cursor against `laneMemo.entries` via `freshnessMatchQueueCursor`.
2. **`linkWalkFooterView(linkData, options)`:**
   - Computes `{ dueText: "Links", prevTarget, nextTarget, hasLinks, action: "open-next" }`.
3. **`walkerFooterView(activeMode, { freshnessMemo, laneMemo, linkData, cursor, quickRoll })`:**
   - Dispatches to `freshnessFooterView` if `mode === "s"`.
   - Dispatches to `laneWalkFooterView` if `mode === "w"`.
   - Dispatches to `linkWalkFooterView` if `mode === "n"`.

### 7.3 Phase 3: Pure DOM Painter & CSS in `bob-ledger-tools`
1. **Extend `freshnessFooterEnsureDom(el)`:**
   - Ensure DOM structure supports mode toggling via `data-walker-mode="s|w|n"`.
   - Add `.bob-walker-rail` container for the lane rail.
   - Add `.bob-walker-link-prev` and `.bob-walker-link-next` interactive segment spans.
2. **Styles in `plugins/bob-ledger-tools/styles.css`:**
   - Define `.bob-freshness[data-walker-mode="w"]` styles.
   - Define `.is-pending` (amber), `.is-next` (cyan), `.is-ready` (purple) badges.
   - Define `.bob-walker-rail` micro-progress bar.
   - Define `.bob-freshness[data-walker-mode="n"]` interactive link arrows.

### 7.4 Phase 4: Verification & Test Harness
1. **Unit Tests (`scripts/test-ledger-tools-walker-footer.cjs`):**
   - Test mode switching: verify that changing `activeMode` flips view model from `review` to `lane` to `link`.
   - Test `w` lane counts matching `laneWalkQueueFromTasks`.
   - Test `Alt+P` quick roll preview rendering inside `w` mode.
   - Test `n` link parsing on daily note fixture.
2. **Visual Preview (`scripts/preview-walker-footer.cjs`):**
   - Headless Chromium rendering of `s`, `w`, and `n` footers across light and dark themes, verifying responsive truncation.

---

## 8. Summary of Recommendations for Bryan

1. **Approve the Plan with Four Refinements:**
   - **Adopt** the core concept: tie the status bar footer visibility directly to the active walk mode in `[[ s w n ]]`.
   - **Add** the Commitment Notification Pip on `s` in `[[ s w n ]]` when morning GTD commitments remain unreviewed.
   - **Add** full `Alt+P` Quick Roll preview support to the Lane Walker Footer (`w`).
   - **Treat** the Link Walker Footer (`n`) as a local directional cockpit rather than a synthetic queue.
2. **Architecture:** Use the **Single Walker Slot Architecture** hosted in `bob-ledger-tools`. It completely avoids status-bar layout jumping, reuses existing width-fitting and tier color infrastructure, and keeps cross-plugin dependencies clean.
3. **Glossary:** Publish the drafted `walker-footer.md` strand into `sase/memory/glossary/walker-footer.md`.
