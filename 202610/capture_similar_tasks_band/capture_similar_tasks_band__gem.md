# Research Report: Real-Time Related & Duplicate Task Preview in Bob Mac Capture

**Researcher:** `research.27.gem`  
**Date:** 2026-10-20  
**Status:** Complete  
**Scope:** Architecture, UX design, performance caching, query algorithms, and keyboard interaction models for detecting and displaying likely related tasks and duplicate tasks in the `bob-mac-capture` preview panel during new task capture.

---

## 1. Executive Summary & Assessment

### 1.1 The Proposal
The user proposes adding real-time task intelligence to the native macOS menu-bar application (`bob-mac-capture`). Specifically:
1. When a user enters a capture draft that will result in **one or more new tasks being created**, the app's live preview panel should surface **likely related tasks** and **potential duplicate tasks** from across the Obsidian vault.
2. The core benefits are providing an immediate heads-up about duplicate tasks (preventing clutter and fragmented tracking) and surfacing existing tasks that the user might want to relate, block, or link to today's Pomodoro.
3. The design must satisfy two strict engineering and UX constraints:
   - **Performance:** `bob-mac-capture` must remain blazing fast (instant typing feel, sub-millisecond response, zero keystroke lag).
   - **Panel Geometry & Screen Real Estate:** The panel must not feel cramped or force frequent scrolling, respecting the existing fixed eye line and height constraints.
   - **Quality of Craft:** Intuitive, reliable, keyboard-first, and visually beautiful.

### 1.2 The Verdict: Is This a Good Idea?
**Yes, but only if designed as an ambient, non-blocking superpower rather than a noisy, mandatory triage step.**

In personal knowledge management (PKM) and Getting Things Done (GTD) workflows, duplicate task creation is a notorious chronic friction:
- A user captures *"Buy replacement water filter @errands"* without remembering they already captured *"Order fridge water filter ^c49a"* two weeks ago in `home.md`.
- A user captures *"Fix API gateway timeout @work"* unaware that a sibling task *"Investigate 504 gateway timeout on ingress ^e81f"* is already scheduled or sitting in the Next lane.
- In both cases, the vault accumulates duplicates, rotting backlog items, and fragmented context that must later be laboriously reconciled during morning GTD reviews.

However, a naive implementation represents an existential threat to `bob-mac-capture`'s core value proposition. If every keystroke triggers a full-vault scan or pops up an intrusive, shifting list of suggestions, the app will degrade from a **low-friction capture tool** into a **sluggish, distracting modal dialog**.

### 1.3 Summary of Key Pitfalls in a Naive Approach
1. **The Keystroke Latency Hazard (Subprocess & Disk Thrashing):**  
   `bob capture --dry-run` currently completes in **~5 ms** because it only reads the single note targeted for insertion (e.g. `mac_inbox.md`). If every keystroke debounced at 50ms triggered a vault-wide disk walk across hundreds of Markdown files, latency would surge to **50–300 ms**, destroying keystroke fluidness, pinning CPU cores, and draining MacBook battery.
2. **The "Capture Mindset" Disruption:**  
   The primary reason `bob-mac-capture` exists is to let Bryan press a global hotkey, dump a raw thought in 2 seconds, and return to deep work. If the preview panel becomes visually chaotic with false-positive task cards, it introduces cognitive friction, forcing the user to evaluate backlog items when they simply wanted to record a quick thought.
3. **The Window Height & Layout Jitter Crisis:**  
   The preview pane adheres to a strict "steady-height policy" (`CapturePreviewPaneHeightPolicy`) to prevent the input caret from jumping. Unconditionally injecting 2–4 task cards (each 40–50pt high) would double the panel height, breach the 720pt screen cap, force the auxiliary `ScrollView` to engage, and violently bounce the window up and down as queries match and unmatch while typing.
4. **The False-Positive Trap:**  
   Short or generic drafts (e.g., *"Call Kelly"*, *"Fix bug"*, *"Update docs"*) match dozens of unrelated vault tasks if tokenization, stopword filtering, and query length thresholds are not strictly applied.
5. **Passive Notification vs. Actionable Superpower:**  
   Merely showing a task title is of low utility if the user still has to manually re-type `&projects/auth:b82e` or `:b82e`. The feature becomes truly transformative when it offers **single-keystroke splicing gestures** (converting a duplicate directly into a Pomodoro link or wiring up dependency links with a single accelerator).

---

## 2. Critique & Required Adjustments to Requirements

To reconcile the user's vision with the non-negotiable performance and UX constraints, the requirements must be adjusted and clarified in five critical ways:

### 2.1 Adjustment 1: Strict Task-Creation Classification
* **Requirement Refinement:** The system must only evaluate related tasks when the parsed capture draft *definitely results in one or more new tasks being created*.
* **Implementation Authority:** `bob-cli`'s capture grammar parser (`capture_language`) categorizes every draft item into a `CaptureKind`. The related-tasks evaluation must **only** trigger if the batch contains at least one item of:
  - `CaptureKind::Task` (plain new task)
  - `CaptureKind::TaskWithBlockId` (new task with explicit user block ID)
  - `CaptureKind::Pomodoro` with a non-empty task description (new Pomodoro-linked task)
  - `CaptureKind::ProjectNote` (creating project tasks)
* **Explicit Exclusions:** It must **never** run for:
  - Session operators: `=` (start), `x` (close), `+5`/`-5` (adjust), `++3`/`--3` (shift)
  - Reference link captures: bare URLs routed to reading queue (`CaptureKind::Ref`)
  - Headings / ordinary bullets: `@route#Section` (`CaptureKind::Bullet`)
  - Sub-bullets under existing tasks: `@route+block-id` (`CaptureKind::SubBullet`)
  - Pomodoro notes: trailing `#` (`CaptureKind::PomodoroNote`)
  - Existing task gestures: `^route:id`, `@route:id` (linking existing tasks), `@route+id!` (task toggle), `!route:id` (task completion)

### 2.2 Adjustment 2: Minimum Content Length & Significance Gate
* **Requirement Refinement:** Never query on trivial or transitional text.
* **Rule:** The task description (after stripping route tokens `@...`, schedule markers `s:...`, priority markers `$...`, and block IDs) must satisfy:
  1. Character count $\ge 4$ (excluding leading/trailing whitespace).
  2. At least one significant, non-stopword token (filtering out words like *the, a, an, to, for, and, with, of, in, on, at, do, make, get, fix, check, update* when standalone).
* **Rationale:** Typing *"Fix "* should not trigger a match against 80 tasks. The engine stays dormant until meaningful semantic tokens exist.

### 2.3 Adjustment 3: Two Distinct Match Classes ("Duplicate" vs. "Related")
* **Requirement Refinement:** Treat duplicate detection and related task discovery as two different UX tiers with different visual treatments:
  - **Tier A — High-Confidence Duplicate (Score $\ge 0.85$):**  
    The user is almost certainly typing an existing task (e.g., exact stem match, $\ge 80\%$ token overlap).  
    *Visual Treatment:* Prominent amber notice pill: `⚠️ Duplicate found in errands.md ^a1b2: "Buy cat food"`.  
    *Primary Action:* Single keystroke (`⌥:`) converts the draft to link the existing task into today's Pomodoro instead of minting a duplicate.
  - **Tier B — Contextually Related Tasks (Score $0.45 – 0.84$):**  
    The user is typing a new task that shares significant entities, systems, or projects with existing tasks (e.g., *"Deploy auth service"* vs. *"Fix auth token expiry"*).  
    *Visual Treatment:* Discreet, calm single-line accessory chip: `[ 🔗 2 related tasks ]`. Does not auto-expand. Never shifts the eye line.
  - **Below $0.45$:** Suppressed completely (zero UI footprint).

### 2.4 Adjustment 4: In-Memory Architecture to Preserve the 5ms Guarantee
* **Requirement Refinement:** The related-task search must **never** perform disk I/O on the keystroke path.
* **Architecture:** `bob-mac-capture` already runs a resident menu-bar process with an active `VaultTargetWatcher` (FSEvents). Bob Mac Capture must maintain an in-memory `CaptureTaskIndex` populated by `bob-cli`. Filtering and scoring happen in Swift memory using `FuzzyField` and token inverted indices in **$< 0.5\text{ ms}$**.

### 2.5 Adjustment 5: Fixed Height Budget & Folding Ladder
* **Requirement Refinement:** Related tasks must obey a strict 24pt–48pt height budget in the steady-state preview card.
* **Layout Rule:** In the normal preview, related tasks occupy at most **one accessory row** (height: 24pt). Expanding into the full comparison shelf (height: 96pt, max 3 items) is an explicit, intentional gesture (`⌥R` or clicking the chip) or keyboard-focused via Tab.

---

## 3. Architecture & Performance: Keeping Bob Mac Capture Blazing Fast

### 3.1 The Performance Contract: Subprocess vs. In-Memory
To keep the app blazing fast, we must analyze the two potential architectural paths:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ PATH A: On-Demand Subprocess Query (REJECTED)                              │
│                                                                             │
│ Keystroke ──> 50ms Debounce ──> Spawn `bob capture-related-tasks`            │
│                                  │                                          │
│                                  ├── Walk vault directories (15-40ms)       │
│                                  ├── Read 200+ markdown files (30-80ms)    │
│                                  ├── Parse Tasks & Block IDs (15-30ms)      │
│                                  ├── JSON serialization/IPC (5-10ms)        │
│                                  └── Swift decode & layout (5ms)            │
│                                                                             │
│ TOTAL LATENCY: 70ms – 165ms per keystroke (CPU heavy, battery drain)        │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ PATH B: Dual-Tier In-Memory Architecture (RECOMMENDED)                      │
│                                                                             │
│ 1. Background Indexing (Zero Keystroke Impact):                              │
│    Launch / FSEvents ──> `bob capture-dependency-tasks --format json`        │
│                         └── Decode into `CaptureTaskIndex` (in-memory)      │
│                                                                             │
│ 2. Keystroke Path (Blazing Fast):                                           │
│    Keystroke ──> 50ms Debounce ──> `processClient.captureLivePreview()` (5ms)│
│                                ──> `CaptureTaskIndex.search(query)` (0.3ms) │
│                                                                             │
│ TOTAL LATENCY: ~5.3ms (Feels completely instantaneous, zero disk I/O)       │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Conformance to Decision 6 (`mac-capture-is-a-thin-client`)
Decision 6 mandates:
> *"bob-cli is the only implementation of capture grammar, completion data, preview, and vault mutation. Bob Mac Capture owns presentation, process orchestration, the global hotkey, settings, launch at login, and packaging. It spawns bob directly... It may filter or rank what bob returned, but it never decides syntax itself... BlockIDRules.swift puts it as 'Bob is the only authority for the grammar'."*

Path B fully adheres to Decision 6:
1. **Bob owns the vault data and parsing:** `bob-cli` remains the sole authority that inspects the vault, parses tasks, identifies block IDs, extracts tags, and resolves note paths. It provides the structured task catalog via a CLI endpoint (`bob capture-dependency-tasks` or `bob capture-tasks --all`).
2. **The App owns caching, filtering, and presentation:** Just as `BlockIDPickerIndex.swift` precomputes search fields over a Bob-supplied snapshot to enable instant local filtering while picking block IDs, `CaptureTaskIndex` precomputes search tokens over Bob's task catalog to enable instant real-time scoring in memory.
3. **Bob owns all mutations and syntax splicing:** When the user decides to act on a related task (linking, blocking, or relating), the app splices Bob's authoritative syntax (`&`, `*`, `~`, `:`) into the draft and executes via `bob capture`.

### 3.3 The In-Memory Task Catalog & Memory Footprint
How heavy is an open-task catalog for an Obsidian vault?
- Typical user vault: 100 to 800 open tasks.
- Heavy power-user vault: 2,000 open tasks.
- Each indexed task in memory:
  ```swift
  struct IndexedTask: Sendable {
      let notePath: String           // "projects/bob-cli.md" (32 bytes)
      let locator: String            // "bob-cli" (16 bytes)
      let blockID: String?           // "task-123" (16 bytes)
      let statusSymbol: Character    // " " or "/" or "*" (8 bytes)
      let statusName: String         // "TODO" (8 bytes)
      let text: String               // "Fix timeout in auth client" (48 bytes)
      let section: String?           // "Tasks" (16 bytes)
      let tokens: Set<String>        // ["fix", "timeout", "auth", "client"] (64 bytes)
      let fuzzyField: FuzzyField     // precomputed boundary bonuses (~64 bytes)
  }
  ```
- **Total memory footprint for 1,000 tasks:** $\approx 250\text{ KB}$ of RAM.
- **Search time across 1,000 tasks:**
  - Token-set intersection across 1,000 items in Swift takes **$\approx 0.15\text{ ms}$**.
  - Top 5 candidates evaluated with `FuzzyMatcher` takes **$\approx 0.10\text{ ms}$**.
  - Total search time: **$< 0.3\text{ ms}$**.

### 3.4 Invalidation & Revalidation Lifecycle
Following the precedent established in Decision 4 (`idle-capture-shows-ledger-agenda`) and `CaptureTargetsCache`:
1. **Cold Launch:** App launches $\rightarrow$ triggers `bob capture-dependency-tasks --open-only --format json` in background $\rightarrow$ populates `CaptureTaskIndex`.
2. **Vault Changes (`FSEvents`):** `VaultTargetWatcher` observes `.md` note modifications. When changes settle (debounced at 1.5 seconds), revalidate the task catalog in the background.
3. **Post-Capture Mutation:** Whenever `bob capture` successfully writes a draft, invalidate and refresh the index in background.
4. **Stale-While-Revalidate:** If an FSEvent fired while the capture panel is active, the current query continues using the existing in-memory snapshot; the refreshed snapshot swaps in atomically on completion.

---

## 4. Query Analysis & Relevance Scoring Algorithm

To avoid false-positive spam, the matcher must combine fast lexical filtering with semantic relevance:

```
               ┌────────────────────────────────────────────────────────┐
               │                  User Capture Draft                    │
               │        "Fix timeout when renewing auth token"          │
               └───────────────────────────┬────────────────────────────┘
                                           │
                                           ▼
               ┌────────────────────────────────────────────────────────┐
               │           Extraction & Stopword Stripping              │
               │   Filtered tokens: ["timeout", "renewing", "auth"]     │
               └───────────────────────────┬────────────────────────────┘
                                           │
                    ┌──────────────────────┴──────────────────────┐
                    ▼                                             ▼
       ┌────────────────────────┐                    ┌────────────────────────┐
       │ Inverted Index Lookup  │                    │ Token Overlap (Jaccard)│
       │ Matches containing     │                    │ Intersection / Union   │
       │ $\ge 1$ content tokens │                    │ Weight by token length │
       └────────────┬───────────┘                    └────────────┬───────────┘
                    └──────────────────────┬──────────────────────┘
                                           │
                                           ▼
               ┌────────────────────────────────────────────────────────┐
               │                   Scoring & Bonuses                    │
               │  • Exact Substring Boost (+0.30)                       │
               │  • Same Note / Route Boost (+0.15)                     │
               │  • Status Weight: Next/In-Progress (+0.10)             │
               │  • Token Length Weight: long words count more          │
               └───────────────────────────┬────────────────────────────┘
                                           │
                    ┌──────────────────────┴──────────────────────┐
                    ▼                                             ▼
       ┌────────────────────────┐                    ┌────────────────────────┐
       │     Score $\ge 0.85$   │                    │  Score $0.45 – 0.84$   │
       │   "Definite Duplicate" │                    │   "Related Context"    │
       │   -> Show Warning Pill │                    │   -> Show Muted Chip   │
       └────────────────────────┘                    └────────────────────────┘
```

### 4.1 Token Scoring Formula
For a draft query $Q$ and candidate task $T$:
1. **Stopword Stripping:** Common English words (*the, is, at, which, on, a, an, and, or, but, if, then, so, for, to, of, with, by*) and common generic task verbs when unaccompanied (*do, make, get, check, update, fix, test, review*) are stripped.
2. **Weighted Jaccard Index ($S_{\text{Jaccard}}$):**
   $$S_{\text{Jaccard}}(Q, T) = \frac{\sum_{w \in Q \cap T} \text{len}(w)}{\sum_{w \in Q \cup T} \text{len}(w)}$$
   Weighting by word length ensures that matching a 7-letter domain word like `"timeout"` contributes far more than matching a 3-letter word like `"new"`.
3. **Substring Exactness Bonus ($B_{\text{sub}}$):**
   If the lowercased task text contains the entire query phrase verbatim (or vice versa), add $+0.35$.
4. **Locality Bonus ($B_{\text{route}}$):**
   If the candidate task resides in the destination note targeted by the draft (e.g. both are in `errands.md` or `@work`), add $+0.15$.
5. **Activity Tier Bonus ($B_{\text{status}}$):**
   - In-Progress (`[-]`) or Next (`[*]`) tasks receive $+0.10$ (high active relevance).
   - Normal open tasks (`[ ]`) receive $+0.05$.
   - Completed/Done tasks (`[x]`) are penalized $-0.20$ (unless query has exact match, in which case they surface with a "Recently Completed" badge).
6. **Composite Score:**
   $$\text{Score} = \min(1.0, S_{\text{Jaccard}} + B_{\text{sub}} + B_{\text{route}} + B_{\text{status}})$$

---

## 5. UI/UX Design: Intuitive, Reliable, and Beautiful

### 5.1 The Panel Geometry & Eye Line Challenge
The `bob-mac-capture` window layout is governed by:
- **Fixed Eye Line (`CapturePanelPlacement.swift`):** The window's input line is positioned at a constant vertical screen coordinate derived from AppKit `center()`. The panel grows **downward** from this eye line.
- **Maximum Panel Height:** 720pt (`panelMaximumContentHeight`).
- **Auxiliary Region:** Contains the preview card, completion picker, or error notices, wrapped in `auxiliaryScrollRegion` (`ScrollView`).
- **Steady-Height Policy:** The preview card has a minimum height floor (92pt) so small previews or loading spinners do not cause the window to collapse and bounce.

If related tasks were injected as large vertical cards inside the preview pane, typing would cause the panel to aggressively expand and contract on every word, creating visual turbulence.

### 5.2 The 3-Tier Visual Presentation Ladder

To solve this, we design a **calm, steady-height accessory ladder** directly integrated into `PreviewPane`:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ TIER 1: Ambient Accessory Chip (Default when Related Tasks Exist)           │
│                                                                             │
│  → mac_inbox · normal                                                       │
│  - [ ] #task Deploy telemetry worker to staging [created::2026-10-20] ^d81a │
│  ─────────────────────────────────────────────────────────────────────────  │
│  🔗 2 related tasks (⌥R to view) · top: staging ingress proxy (ops.md)      │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ TIER 2: High-Confidence Duplicate Warning Pill (Score >= 0.85)             │
│                                                                             │
│  → errands · normal                                                         │
│  - [ ] #task Buy replacement water filter [created::2026-10-20] ^f29b       │
│  ─────────────────────────────────────────────────────────────────────────  │
│  ⚠️  Likely duplicate in errands.md ^c49a: "Order fridge water filter"      │
│      [⌥: Link Existing Today]  [⌥/ Open]  [⏎ Create Anyway]                 │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ TIER 3: Expanded Comparison Shelf (Activated via ⌥R, Tab, or Click)         │
│                                                                             │
│  → mac_inbox · normal                                                       │
│  - [ ] #task Deploy telemetry worker to staging [created::2026-10-20] ^d81a │
│  ─────────────────────────────────────────────────────────────────────────  │
│  Related Tasks (2)                                           [⌥R to collapse]│
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ 1. [ ] #task Configure staging ingress proxy   ops.md ^e910 · 82%     │  │
│  │    Actions: [⌥& Prereq]  [⌥* Blocks]  [⌥~ Relate]  [⌥+ Parent]        │  │
│  ├───────────────────────────────────────────────────────────────────────┤  │
│  │ 2. [*] #task Telemetry worker unit tests      dev.md ^a124 · 64%     │  │
│  │    Actions: [⌥& Prereq]  [⌥* Blocks]  [⌥~ Relate]                     │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.3 Detailed Visual Styling
- **Material & Background:**
  The related task accessory sits inside the `PreviewPane`'s `.thinMaterial` card, separated from the verbatim block line by a hairline divider (`Divider().opacity(0.4)`).
- **Typography:**
  - Accessory chips: `.font(.caption)`, `.foregroundStyle(.secondary)`.
  - Duplicate alert: `.font(.callout.weight(.medium))`, tinted with `Color.orange`.
  - Task locators: `.font(.system(.caption, design: .monospaced))`, `.foregroundStyle(.tertiary)`.
- **Badge Accents:**
  - Status symbols (`[ ]`, `[*]`, `[-]`) use their native GTD palette colors (Next is cyan, In-Progress is amber, Ready is secondary).
  - Match percentage chip: subtle capsule (`.font(.system(size: 10, weight: .semibold, design: .monospaced))`, `.background(.quaternary, in: Capsule())`).
- **Screen Real Estate Footprint:**
  - Tier 1 (Chip): Exactly **22pt** height. It fits comfortably within the existing preview card without triggering auxiliary scrolling.
  - Tier 2 (Duplicate Banner): **36pt** height. Highly compact, self-contained action pills.
  - Tier 3 (Shelf): **80–110pt** height. Capped at a maximum of 3 items. If more exist, a trailing label reads `"+ 3 more in vault"`.

---

## 6. Interaction Model: Single-Keystroke Superpowers

A heads-up is only valuable if acting on it is effortless. We design single-keystroke accelerators that splice Bob capture markers into the draft without requiring the user to touch the mouse or remember syntax:

### 6.1 Duplicate Resolution Shortcuts
When Tier 2 (Duplicate Alert) is active:
| Shortcut | Action | What Happens Under the Hood |
| :--- | :--- | :--- |
| `⌥:` | **Link Existing Today** | Replaces the draft text with `@note:block-id`, converting the new task capture into a Pomodoro link for the existing task. |
| `⌥/` | **Open in Obsidian** | Dispatches an Obsidian URL open (`obsidian://open?vault=...&file=...`) and dismisses the panel. |
| `⏎` (Return) | **Create Anyway** | Normal capture execution; creates the new task as typed. |
| `⎋` (Escape) | **Dismiss / Retain** | Closes capture panel, retaining draft in stash. |

### 6.2 Related Task Splicing Shortcuts
When Tier 3 (Expanded Shelf) is active, candidate #1 is selected by default (navigable with `↑`/`↓`):
| Shortcut | Action | Spliced Syntax Result | GTD Semantic Meaning |
| :--- | :--- | :--- | :--- |
| `⌥&` | **Make Prerequisite** | Appends `&note:block-id` | New task depends on candidate task. |
| `⌥*` | **Make Blocker** | Appends `*note:block-id` | Candidate task depends on new task. |
| `⌥~` | **Relate Tasks** | Appends `~note:block-id` | Symmetric relation link between tasks. |
| `⌥+` | **Make Child Task** | Appends `+note:block-id` | Files new task as child sub-bullet under candidate. |
| `⌥R` or `Tab` | **Toggle Drawer** | Toggles between Tier 1 chip and Tier 3 shelf. | Quick look without touching mouse. |

*Why this is beautiful:*  
A user typing `"Deploy auth v2"` sees `"Configure auth database schema ^db1"` in the shelf. They simply press `⌥&` followed by `⏎`. In two keystrokes, they have captured their new task **and** wired up the entire dependency graph in Obsidian!

---

## 7. Technical Specifications & Implementation Blueprint

### 7.1 Component Architecture Overview

```mermaid
flowchart TD
    subgraph BobCLI ["bob-cli (Rust Engine)"]
        CLICatalog["bob capture-tasks --all --format json"]
        CLIParent["note_tasks::scan() across vault"]
        CLICatalog --> CLIParent
    end

    subgraph BobMacCapture ["Bob Mac Capture (Swift Client)"]
        FSWatcher["VaultTargetWatcher (FSEvents)"]
        TaskStore["CaptureTaskIndex (In-Memory Actor)"]
        PanelModel["CapturePanelModel"]
        Matcher["FuzzyQuery & TokenMatcher"]
        PreviewView["PreviewPane & RelatedTasksAccessoryView"]

        FSWatcher -->|Vault Changed| TaskStore
        TaskStore -->|Refresh Catalog| CLICatalog
        PanelModel -->|1. Live Syntax Preview| BobCLI
        PanelModel -->|2. In-Memory Search (<0.5ms)| TaskStore
        TaskStore --> Matcher
        Matcher -->|Scored Matches| PanelModel
        PanelModel -->|Publish UI State| PreviewView
    end
```

### 7.2 Backend: `bob-cli` Enhancements
We extend `bob capture-tasks` to support vault-wide catalog export:

```rust
// In src/native/capture_tasks.rs
pub(crate) struct VaultTaskCatalog {
    pub(crate) schema_version: u32,
    pub(crate) tasks: Vec<CatalogTask>,
}

#[derive(Serialize, Deserialize)]
pub(crate) struct CatalogTask {
    pub(crate) note_path: String,       // "projects/dev.md"
    pub(crate) locator: String,         // "dev"
    pub(crate) block_id: Option<String>,// "auth-v2"
    pub(crate) status_symbol: char,     // ' '
    pub(crate) status_name: String,     // "TODO"
    pub(crate) status_type: String,     // "open"
    pub(crate) text: String,            // "Configure auth database schema"
    pub(crate) section: Option<String>, // "Tasks"
    pub(crate) line: usize,             // 42
    pub(crate) tags: Vec<String>,       // ["#auth", "#db"]
}
```
CLI invocation: `bob capture-tasks --all --format json`
- Filters out completed/archived tasks unless `--include-done` is passed.
- Reuses the blazing directory walker and note scanner from `capture_dependency_tasks.rs`.

### 7.3 Frontend: `CaptureTaskIndex` Actor in `CaptureCore`
A dedicated Swift actor managing the in-memory cache:

```swift
public actor CaptureTaskIndex {
    public static let shared = CaptureTaskIndex()

    private var tasks: [IndexedTask] = []
    private var tokenInvertedIndex: [String: Set<Int>] = [:]
    private var lastRefresh: Date?
    private var isRefreshing = false

    public func refresh(using client: BobProcessClient) async {
        guard !isRefreshing else { return }
        isRefreshing = true
        defer { isRefreshing = false }

        do {
            let response = try await client.captureTaskCatalog()
            var indexed: [IndexedTask] = []
            var inverted: [String: Set<Int>] = [:]

            for (index, item) in response.tasks.enumerated() {
                let tokens = Self.tokenize(item.text)
                for token in tokens {
                    inverted[token, default: []].insert(index)
                }
                indexed.append(IndexedTask(item: item, tokens: tokens))
            }

            self.tasks = indexed
            self.tokenInvertedIndex = inverted
            self.lastRefresh = Date()
        } catch {
            // Retain existing snapshot on error, mark stale
        }
    }

    public func search(query: String, destinationRoute: String?, limit: Int = 3) -> [RelatedTaskMatch] {
        let cleanQuery = query.trimmingCharacters(in: .whitespacesAndNewlines)
        let queryTokens = Self.tokenize(cleanQuery)
        guard queryTokens.count >= 1, cleanQuery.count >= 4 else { return [] }

        // 1. Candidate selection via inverted index union
        var candidateIndices = Set<Int>()
        for token in queryTokens {
            if let hits = tokenInvertedIndex[token] {
                candidateIndices.formUnion(hits)
            }
        }

        // 2. Score candidates
        var scored: [RelatedTaskMatch] = []
        for index in candidateIndices {
            let candidate = tasks[index]
            let score = Self.calculateScore(
                query: cleanQuery,
                queryTokens: queryTokens,
                candidate: candidate,
                destinationRoute: destinationRoute
            )
            if score >= 0.45 {
                scored.append(RelatedTaskMatch(task: candidate, score: score))
            }
        }

        scored.sort { $0.score > $1.score }
        return Array(scored.prefix(limit))
    }
}
```

### 7.4 Model Integration: `CapturePanelModel.swift`
In `CapturePanelModel.scheduleAnalysis()`:
1. `captureParse` runs as usual.
2. If `parse` contains any new task creation items:
   ```swift
   if let taskText = Self.extractNewTaskDescription(from: parse, draft: draft) {
       Task {
           let matches = await CaptureTaskIndex.shared.search(
               query: taskText,
               destinationRoute: parse.route
           )
           await MainActor.run {
               self.relatedTaskMatches = matches
           }
       }
   } else {
       self.relatedTaskMatches = []
   }
   ```
3. Because `CaptureTaskIndex.search` runs against memory in 0.3ms, this produces zero perceptible lag and never blocks the `captureLivePreview` pipeline.

### 7.5 View Integration: `PreviewPane` in `CapturePanelView.swift`
Inside `PreviewPane.previewContent()`:
```swift
if let duplicate = model.topDuplicateMatch {
    DuplicateNoticeBanner(
        duplicate: duplicate,
        onLinkExisting: { model.replaceDraftWithTaskLink(duplicate.task) },
        onOpenInObsidian: { model.openTaskInObsidian(duplicate.task) }
    )
} else if !model.relatedTaskMatches.isEmpty {
    RelatedTasksAccessoryView(
        matches: model.relatedTaskMatches,
        isExpanded: model.relatedShelfExpanded,
        onToggleExpand: { model.toggleRelatedShelf() },
        onSpliceAction: { action, task in model.spliceTaskRelation(action, task: task) }
    )
}
```

---

## 8. Alternative Approaches & Comparative Evaluation

| Dimension | Approach A: Synchronous Subprocess in `capture --dry-run` | Approach B: Dedicated Debounced CLI Subprocess | Approach C: In-Memory Client Cache + FSEvents (Recommended) | Approach D: Full Triage Modal Sheet |
| :--- | :--- | :--- | :--- | :--- |
| **Typing Latency** | 50–150ms (Severe stutter) | 30–80ms (Noticeable lag on pause) | **< 0.5ms** (Completely instantaneous) | N/A (Modal on submit) |
| **CPU / Battery Cost**| Extreme (Scans disk every 50ms) | Moderate (Spawns on typing pause) | **Negligible** (RAM search, FSEvents refresh) | Zero while typing |
| **Visual Stability** | High jitter (Cards pop in/out) | Delayed jitter (Pops in after pause) | **Rock solid** (Steady-height accessory chip)| High friction (Stops capture flow) |
| **Capture Flow** | Intrusive | Intrusive | **Ambient & Non-blocking** | Destroys low-friction GTD dumping |
| **Actionability** | Display only | Display only | **1-key splicing (`⌥:`, `⌥&`, `⌥*`)** | Dialog button clicks |
| **Thin Client Compliance** | Violates performance spirit | Complies | **Complies (Matches `BlockIDPickerIndex`)** | Complies |

**Why Approach C Wins Decisively:**  
It completely decouples disk I/O from keystrokes. It honors GTD purity by staying quiet when you don't need it, yet provides instantaneous keyboard superpowers the moment a duplicate or linkable task appears.

---

## 9. Implementation Phases & Verification Roadmap

### Phase 1: `bob-cli` Open Task Catalog
- Add `bob capture-tasks --all --format json` subcommand in `src/native/capture_tasks.rs`.
- Verify output schema with tests in `tests/test_capture_tasks.rs`.
- Benchmark execution: Ensure cold vault walk on 500 notes completes in $< 40\text{ ms}$.

### Phase 2: `bob-mac-capture` In-Memory Index & Token Matcher
- Implement `CaptureTaskIndex` actor and `IndexedTask` models in `CaptureCore`.
- Implement weighted token Jaccard and stopword filters in `FuzzyMatcher.swift`.
- Unit tests: Test scoring on exact matches, partial stems, stopword suppression, and route bonuses.
- Verify memory footprint ($< 500\text{ KB}$) and search latency ($< 0.5\text{ ms}$).

### Phase 3: FSEvents Invalidation & Model Wiring
- Wire `VaultTargetWatcher` batch notifications to `CaptureTaskIndex.refresh()`.
- Add task-creation detector in `CapturePanelModel.swift` to extract task descriptions.
- Wire search results into `@Published var relatedTaskMatches`.

### Phase 4: UI Presentation & Splicing Gestures
- Build `DuplicateNoticeBanner` and `RelatedTasksAccessoryView` in `BobMacCapture`.
- Implement keyboard shortcuts (`⌥:`, `⌥&`, `⌥*`, `⌥~`, `⌥+`, `⌥R`).
- Validate fixed eye line placement and verify that the steady-height policy is maintained.

### Phase 5: Verification & Accessibility
- VoiceOver testing: Ensure accessory chips announce concisely without repeating.
- End-to-end user testing: Confirm typing latency remains indistinguishable from the baseline app.

---

## 10. Recommended Solution & Synthesis

To build a feature that is **intuitive, reliable, blazing fast, and beautiful**:

1. **Do not run vault scans on keystrokes.** Implement the **Dual-Tier In-Memory Architecture**: `bob-cli` remains the authoritative catalog builder, while `bob-mac-capture` caches the task snapshot in memory and performs sub-millisecond lexical scoring in Swift.
2. **Do not clutter the preview by default.** Use the **3-Tier Visual Presentation Ladder**:
   - Definite duplicates trigger an **amber action pill** with single-keystroke resolution (`⌥:` to link existing).
   - Related tasks render as an **ambient, single-line chip** (`🔗 2 related`) that stays within the steady-height budget.
   - The comparison shelf only opens on intentional user command (`⌥R` or click).
3. **Turn passive alerts into active superpowers.** Implement single-keystroke splicing gestures (`⌥&` prereq, `⌥*` blocker, `⌥~` relate) so users can build their Obsidian task graph at the exact moment of capture with zero friction.
4. **Strictly gate execution.** Run matching only when the draft parses as creating a real new task and contains $\ge 4$ non-stopword characters.

This design transforms `bob-mac-capture` from a simple text-entry popup into an intelligent, ambient knowledge graph connector—without sacrificing a single millisecond of the blazing speed Bryan relies on.
