# Research Report: Google Keep & Vault Inbox Footer Indicator in Obsidian

**Researcher ID:** `gem` (5-Researcher Swarm)  
**Target Repository:** `bob-plugins` / `bob-cli`  
**Date:** October 2026  
**Artifact Label:** `research:202610/gkeep_obsidian_footer_indicator__gem.md`

---

## 1. Executive Summary

The user proposes adding a status bar indicator (the "footer") to Obsidian that tracks two related but distinct quantities:
1. **Google Keep Inbound Notes**: How many notes currently reside in Google Keep that would be ingested if `bob gkeep pull` were executed.
2. **Vault Inbox Tasks**: How many non-closed tasks (any checkbox other than `[x]` or `[-]`) currently reside in `~/bob/gkeep_inbox.md`.

The user requested that this indicator:
- Appear **only** when Google Keep is properly authenticated (i.e. `bob gkeep pull` would succeed).
- Avoid frequent Google Keep syncs to protect the API from rate limits and conserve MacBook CPU and battery.
- Track the vault's `gkeep_inbox.md` count much more frequently (within seconds).
- Distinguish the two counts visually.
- Be intuitive, reliable, and beautiful.
- Provide a critical evaluation of whether this is a good idea, suggest necessary requirement adjustments, and recommend an implementation path.

### Key Verdict
**The proposal is fundamentally sound and fills a crucial gap in Bryan's capture pipeline, but a naive implementation would introduce severe failure modes.** Specifically, running `gkeepapi` network syncs directly from an Electron status bar item risks Google account rate-limiting, CAPTCHA lockouts, MacBook battery drain, and process hangs caused by unattended GPG/pinentry credential lookups. 

With **three critical requirement adjustments** (a 3-tier local auth gate, a decoupled event-driven sync cadence with local state caching, and 0ms reactive in-memory vault tracking), the feature can be implemented as an elegant, robust, dual-stage capture pipeline indicator (`[ 💡 N · 📥 M ]`) embedded directly within `bob-ledger-tools`.

---

## 2. Critique of the Plan

### 2.1 The Strengths: Why This Solves a Real Problem
1. **Closing the Mobile Capture Loop**: Bryan captures ideas, tasks, links, and audio on mobile via the native Google Keep app. Once back at his MacBook, those notes remain stranded in the cloud until an explicit terminal command (`bob gkeep pull`) is run. Without an indicator, the user must rely on memory or run exploratory CLI commands. An ambient status bar indicator provides immediate awareness of pending inbound notes.
2. **The Dual-Stage Inbox Mental Model**: In Getting Things Done (GTD) methodology, capture consists of two stages:
   - **Stage 1 (Raw Ingestion / Inbound Buffer)**: Captured raw in Google Keep.
   - **Stage 2 (Local Vault Triage / Inbox Processing)**: Ingested into `gkeep_inbox.md`, awaiting priority assignment, scheduling, project affiliation, or completion.
   Separating these counts in the UI provides clarity on whether the bottleneck is *cloud ingestion* (running `bob gkeep pull`) or *vault processing* (triaging `gkeep_inbox.md`).

### 2.2 Potential Pitfalls & Hidden Complexities

#### A. The Unofficial API Vulnerability (`gkeepapi`)
Google Keep provides **no official public REST API** for personal Google accounts. `bob gkeep` interfaces with Keep via `gkeepapi` (v0.17.1) and `gpsoauth` (v2.0.0), which emulate Google's internal Android client sync protocol over HTTPS (`android.clients.google.com/auth` and Google Reminders/Keep backend endpoints).
- **Rate-Limiting & Block Risk**: Google aggressively throttles and issues HTTP 429 or `BrowserLoginRequiredException` when clients poll too frequently or exhibit bot-like request cadences.
- **Account Disruption**: Exceeding undocumented rate thresholds can invalidate the master token (`aas_et/...`), forcing the user to regenerate cookies and re-authenticate via `bob gkeep login`.
- **Latency**: Even an incremental sync takes 2 to 6 seconds over Wi-Fi. An Obsidian UI thread must never block on or stutter from this operation.

#### B. MacBook Resource Constraints (Battery, Thermal, Wakes)
Spawning a Python process via `uv run` inside Node/Electron every few minutes wakes the CPU, prevents macOS App Nap / sleep states, and noticeably degrades battery life. The design must minimize process spawning and network activity when on battery or when the application is idle.

#### C. Credential Retrieval & The Headless GPG Pinentry Trap
`bob gkeep` retrieves the master token by executing `token_command`, which defaults to `pass show gkeep/master_token`.
- As documented in prior Apollo incident research (`apollo-pass-pinentry-hang.md`), unattended invocations of `pass` without a controlling TTY can hang indefinitely waiting for `pinentry-curses` or fail to acquire GPG agent locks.
- If Obsidian spawns `bob gkeep` in the background when the GPG agent cache has expired and no GUI pinentry (`pinentry-mac`) is running, the background child process will hang and block future sync runs.
- **Rule**: Any background credential read must have an explicit timeout, fail fast, and never prompt for interactive passphrases without user initiation.

#### D. Semantic Mismatch: "Notes That Would Be Synced"
The user requested an indicator showing "how many notes I currently have in Google Keep that would be synced if the `bob gkeep pull` command were run."
In `bob-cli`'s classification logic (`src/native/gkeep/plan.rs`), not all Keep notes are actionable:
1. **Empty Notes**: Skipped (`NoteState::Empty`).
2. **Pinned Notes**: Skipped by default (`NoteState::Pinned`), unless `--include-pinned` is passed.
3. **Shared Notes**: Skipped by default (`NoteState::Shared`), unless `--include-shared` is passed.
4. **Already Archived Notes**: Skipped (`NoteState::Archived`).
5. **URL-Only Reference Notes**: Actionable (`PlanAction::CreateRef`), but they clip into PDF reference notes in `xlib/` / `lib/`, **not** task items in `gkeep_inbox.md`.
6. **New / Revised Notes**: Actionable (`PlanAction::Write` / `PlanAction::WriteRevision`), written as tasks to `gkeep_inbox.md` and archived.
7. **Pending Notes**: Actionable (`PlanAction::ArchiveOnly`), already present in the vault ledger, needing only cloud archiving.

**Crucial Distinction**: The indicator must display **actionable notes** (`new + pending + revised`), rather than total raw notes in Keep.

---

## 3. Recommended Adjustments to Requirements

To address these risks while fulfilling the user's vision, the following adjustments to the requirements are proposed:

| # | Original Requirement | Proposed Adjusted Requirement | Justification |
|---|----------------------|--------------------------------|---------------|
| **1** | Only show indicator if Google Keep is properly authenticated (i.e. `bob gkeep pull` would work). | **Three-Tier Auth Gate**: Validate configuration and cached credentials locally (0ms) without making live network calls on startup; fall back gracefully to a quiet warning state if auth expires. | Probing Google Keep over the network on Obsidian startup blocks startup, breaks offline use (airplane mode), and wastes API quotas. |
| **2** | Be careful not to sync with Google Keep too often. | **Decoupled Asynchronous Polling & State Caching**: Sync Google Keep on a coarse 30–60 minute interval while Obsidian is focused, revalidate on window focus (with a 15-minute cooldown), and revalidate immediately after any user-triggered pull. | Avoids Google rate-limiting, saves MacBook battery, and eliminates redundant background Python executions. |
| **3** | Count non-closed tasks in `gkeep_inbox.md` much more often (taking seconds at most). | **Sub-millisecond Reactive In-Memory Watcher**: Listen to Obsidian `vault.on("modify")` events for `gkeep_inbox.md`. Recount in memory using regex in < 1ms. | Direct file inspection inside Obsidian is instantaneous (0–1ms) and requires zero subprocess spawns or disk reads. |
| **4** | Simple visual distinction between counts. | **Unified Dual-Stage Status Pill (`[ 💡 N · 📥 M ]`)**: Display a cohesive segmented pill with branded iconography, distinct color tokens (Keep Amber vs. Vault Cyan/Muted), and an interactive click handler. | Treats the two numbers as connected stages of a single capture pipeline rather than two unrelated status widgets. |

---

## 4. Technical Feasibility & Deep Dive

### 4.1 How `bob-cli` Handles Google Keep Operations

`bob-cli` contains a robust `gkeep` subsystem with dedicated subcommands:
- `bob gkeep list`:
  - `bob gkeep list -s vault -f json`: **Fast, offline, 0 network**. Reads `~/bob/gkeep_inbox.md`, parses tasks, filters out closed tasks (`[x]` and `[-]`), and outputs JSON in ~12ms:
    ```json
    {
      "ok": true,
      "schema_version": 1,
      "vault": {
        "path": "gkeep_inbox.md",
        "tasks": [
          { "line": 22, "status": "[?]", "description": "...", "keep_id": "..." }
        ]
      }
    }
    ```
  - `bob gkeep list -f json`: Contacts Google Keep, downloads snapshot, classifies notes against vault import history, and outputs full JSON with `summary.new`, `summary.pending`, `summary.revised`, and `summary.skipped`. Actionable count is `new + pending + revised`.
- `bob gkeep doctor -f json`: Executes checklist of 8 components (config, account, uv, token, adapter, keep reachability, target file, git).
- `bob gkeep pull`: Runs the complete atomic drain transaction.

### 4.2 State Caching in `gkeepapi` and `bob-cli`

When `gkeepapi` authenticates, it serializes its internal note database into a JSON state cache (`keep.dump()`), stored at:
```
~/.cache/bob-cli/gkeep/state.json
```
If a valid `state.json` exists on disk:
- Subsequent syncs are **incremental**: only note changes since the last sync timestamp are downloaded.
- However, `gkeep_adapter.py` currently invokes `keep.authenticate(..., sync=True)`, which always reaches out to Google.
- **Architectural Enhancement**: `bob-cli` can persist a lightweight metadata file:
  ```
  ~/.cache/bob-cli/gkeep/status.json
  ```
  containing:
  ```json
  {
    "account": "bryanbugyi34@gmail.com",
    "authenticated": true,
    "last_sync_utc": "2026-10-31T15:45:00Z",
    "actionable_count": 3,
    "breakdown": { "new": 2, "pending": 1, "revised": 0, "clips": 0 },
    "vault_inbox_count": 1,
    "error": null
  }
  ```
  This allows Obsidian to read the latest status instantly from disk or memory, while background sync updates `status.json`.

---

## 5. UI/UX Design Specification: Intuitive, Reliable, Beautiful

### 5.1 Placement in Obsidian

The Obsidian status bar (`this.addStatusBarItem()`) sits in the desktop footer. Existing custom items include:
- `bob-freshness`: Morning GTD review footer (`⟳ Review r/N · TIER i/M`).
- `bob-cmd-chip`: Command Mode chip (`:`).
- `bob-articles`: Look status.

The new indicator, named **`bob-gkeep-status`**, should sit immediately to the right of `bob-freshness` or on the right status shelf.

### 5.2 Visual Metaphor: The Dual-Stage Pipeline

```
┌────────────────────────────────────────────────────────┐
│  [ 💡 3  ·  📥 1 ]                                     │
└────────────────────────────────────────────────────────┘
     ▲         ▲
     │         └─ Local Vault Queue (gkeep_inbox.md open tasks)
     └─────────── Remote Cloud Buffer (Keep actionable notes)
```

- **Google Keep Segment**:
  - Icon: `💡` (Google Keep lightbulb symbol).
  - Accent Color: Google Keep Amber (`#fbbc04` in light mode, `#ffd54f` in dark mode).
  - Meaning: Notes currently held in Google Keep that need to be pulled into Obsidian.
- **Vault Inbox Segment**:
  - Icon: `📥` (Tray / Inbound inbox) or `📋`.
  - Accent Color: Standard interface text (`var(--text-normal)`), transitioning to subtle Cyan/Teal (`var(--interactive-accent)`) when tasks are pending.
  - Meaning: Tasks recorded in `~/bob/gkeep_inbox.md` that have not been triaged or closed.

### 5.3 State Progression Table

| System State | Visual Render in Status Bar | Meaning | Click Action |
|---|---|---|---|
| **Unauthenticated / Disabled** | *(Hidden / Display None)* | `gkeep` not configured or no token found. | None |
| **All Clear (Quiet)** | `💡 0 · 📥 0` *(dimmed text)* or `💡 ✓` | Keep is clear and inbox has no open tasks. | Opens `gkeep_inbox.md` |
| **Keep Notes Pending** | `💡 3 · 📥 0` *(Amber 💡 and count)* | 3 notes waiting in Keep to be pulled. | Runs `bob gkeep pull` |
| **Inbox Tasks Pending** | `💡 0 · 📥 2` *(Amber bulb dim, 📥 2 normal)* | Keep clear, but 2 open tasks in `gkeep_inbox.md`. | Opens `gkeep_inbox.md` |
| **Both Active** | `💡 4 · 📥 2` *(Both illuminated)* | 4 notes in Keep, 2 in vault inbox. | Runs `bob gkeep pull` |
| **Syncing in Progress** | `💡 ↻ · 📥 1` *(Animated spin on ↻)* | Background sync or pull is actively running. | Shows progress notice |
| **Auth / Sync Warning** | `⚠️ Keep Auth · 📥 1` *(Red/Orange warning)* | Token expired or connection failed. | Opens doctor report notice |

### 5.4 Rich Tooltip Layout

Hovering over the indicator reveals a clean, structured tooltip detailing both sides of the pipeline:

```
┌─────────────────────────────────────────────────────────────┐
│ Google Keep & Vault Inbox                                   │
│ ─────────────────────────────────────────────────────────── │
│ ☁️  Google Keep (bryanbugyi34@gmail.com)                     │
│    • 3 notes ready to pull (2 new, 1 revised, 0 clips)      │
│    • 1 pinned note staying in Keep                          │
│    • Last synced: 14 minutes ago                            │
│                                                             │
│ 📥  Vault Inbox (gkeep_inbox.md)                            │
│    • 1 open task awaiting triage                            │
│    • 0 in progress · 1 blocked                              │
│ ─────────────────────────────────────────────────────────── │
│ Left-click: Pull 3 notes into vault (bob gkeep pull)        │
│ Right-click: Open gkeep_inbox.md                            │
└─────────────────────────────────────────────────────────────┘
```

### 5.5 Interactive Click Behavior

- **Left-Click (Smart Default)**:
  - If **Keep Count > 0**: Spawns `bob gkeep pull` in the background with a subtle status notification (`"Syncing Google Keep..."`). Upon completion, plays a quiet completion toast (`"✓ Ingested 3 Keep notes into gkeep_inbox.md"`), recount happens reactively, and the indicator updates immediately.
  - If **Keep Count == 0** and **Vault Count > 0**: Jumps directly to `gkeep_inbox.md` in the active Obsidian leaf.
  - If **Both == 0**: Triggers an on-demand Keep sync check.
- **Alt / Right-Click (Context Menu)**:
  - `Pull Google Keep now (bob gkeep pull)`
  - `Preview pull in terminal (bob gkeep pull -d)`
  - `Open gkeep_inbox.md`
  - `Check Google Keep setup (bob gkeep doctor)`

---

## 6. Architecture & Implementation Options

### 6.1 Architectural Placement: Where Does the Code Live?

We evaluated two potential locations within the `bob-plugins` repository:

| Criteria | Option A: Inside `bob-ledger-tools` | Option B: Standalone Plugin `bob-gkeep` |
|---|---|---|
| **Architectural Cohesion** | High. `bob-ledger-tools` already owns status bar items (`bob-freshness`), integrates `bob gcal`, uses `bobSpawnJson`, and tracks GTD workflows. | Moderate. Keeps Google Keep isolated, but fragments Bryan's plugin ecosystem. |
| **Deployment Overhead** | Zero. `bob-ledger-tools` is already built, tested, and synced to `~/bob/.obsidian/plugins/`. | High. Requires adding a new plugin manifest, registering build scripts, and enabling in Obsidian's `community-plugins.json`. |
| **Vault Event Access** | Native. `bob-ledger-tools` already has active vault event bindings. | Requires duplicate boilerplate. |
| **Recommendation** | **STRONGLY RECOMMENDED** | Rejected as unnecessary overhead |

**Recommendation**: Implement this as a modular mixin within `bob-ledger-tools`:
- `src/242-plugin-gkeep-status.js`: Lifecycle, DOM setup, sync scheduler, click routing.
- `src/122-gkeep-footer-paint.js`: Pure DOM creation, CSS class management, tooltip formatting.
- `styles.css`: Scoped CSS styles under `.bob-gkeep-status`.

### 6.2 Data Flow Architecture

```
                  ┌──────────────────────────────────────────────┐
                  │            Obsidian UI (Desktop)             │
                  │   ┌──────────────────────────────────────┐   │
                  │   │ Status Bar Item: [ 💡 N  ·  📥 M ]    │   │
                  │   └───────────────────▲──────────────────┘   │
                  └───────────────────────┼──────────────────────┘
                                          │
                  ┌───────────────────────┴──────────────────────┐
                  │       bob-ledger-tools (Plugin Mixin)        │
                  ├───────────────────────┬──────────────────────┤
                  │ Local Vault Watcher   │ Keep Sync Controller │
                  └───────────▲───────────┴───────────▲──────────┘
                              │                       │
      vault.on("modify")      │                       │ 30-60m interval / Focus
      "gkeep_inbox.md"        │                       │ / Click trigger
                              │                       │
                  ┌───────────▼───────────┐   ┌───────▼──────────┐
                  │ Obsidian Vault API    │   │ bobSpawnJson     │
                  │ (in-memory regex, 0ms)│   │ ["gkeep", ...]   │
                  └───────────────────────┘   └───────▲──────────┘
                                                      │
                                              ┌───────▼──────────┐
                                              │ bob-cli (Rust)   │
                                              │ + gkeep_adapter  │
                                              └──────────────────┘
```

### 6.3 Detailed Component Responsibilities

#### 1. Vault Inbox Counter (Instant, 0ms)
- On plugin load, register a vault file listener:
  ```javascript
  this.registerEvent(
    this.app.vault.on("modify", (file) => {
      if (file.path === "gkeep_inbox.md") {
        this.updateVaultInboxCount();
      }
    })
  );
  ```
- Fast in-memory counting function:
  ```javascript
  async function countOpenInboxTasks(vault) {
    const file = vault.getAbstractFileByPath("gkeep_inbox.md");
    if (!file) return 0;
    const content = await vault.read(file);
    const matches = content.match(/^[\t ]*-\s*\[([^xX\-])\]/gm);
    return matches ? matches.length : 0;
  }
  ```
- **Performance**: Executed in ~0.5ms. Completely decoupled from Python, `uv`, network, or disk subprocesses.

#### 2. Three-Tier Authentication Gate
Before showing the indicator:
1. **Tier 1 (Static Config Check)**: Check if `gkeep` is configured.
   Can be verified via `bob gkeep list -s vault -f json` (which succeeds if target exists) or checking if `gkeep.email` is set in config.
2. **Tier 2 (Token Availability)**: Check if a master token exists without prompting:
   Run token verification with a strict 1-second timeout (`env PASSWORD_STORE_GPG_OPTS='--batch --pinentry-mode error'`).
3. **Tier 3 (State / Health Memory)**: If previous attempts returned exit code 2 (unconfigured or missing token) or authentication failure (exit code 1 with auth error), keep the indicator hidden. Only display when authentication is established.

#### 3. Google Keep Sync Scheduler
- **Cadence**:
  - Initial check: 5 seconds after Obsidian layout is ready (`workspace.onLayoutReady`).
  - Periodic timer: Every 45 minutes while Obsidian window is active.
  - Focus trigger: On `visibilitychange` (tab/window active), if at least 15 minutes have elapsed since the last check.
  - Inactive suppression: If window is hidden / minimized, pause timer.
- **Execution**:
  - Uses `bobSpawnJson(["gkeep", "list", "-f", "json"], ...)` with a 30-second timeout.
  - Extracts `new + pending + revised` from `summary`.
  - On error, transitions indicator to warning state without crashing Obsidian.

---

## 7. Recommended Implementation Plan

### Phase 1: `bob-cli` Status & Cache Optimization
1. Verify `bob gkeep list -s vault -f json` returns quickly and safely across all vault states.
2. Ensure `bob gkeep list -f json` provides explicit error kinds on auth failures (`"kind": "auth"`).
3. (Optional) Provide a lightweight cached check flag: `bob gkeep list -f json --cached` that reads `state.json` without network sync when available.

### Phase 2: Status Bar Component in `bob-ledger-tools`
1. Create `src/122-gkeep-footer-paint.js` with pure DOM helpers:
   - `gkeepFooterEnsureDom(el)`
   - `gkeepFooterPaint(parts, state)`
   - Tooltip generation and formatting.
2. Add CSS rules to `plugins/bob-ledger-tools/styles.css`:
   - Flex layout, typography (`tabular-nums`), amber Keep badge, cyan/normal vault badge.
   - Smooth transition states (`opacity`, pulse on sync).
3. Create `src/242-plugin-gkeep-status.js`:
   - Mixin implementing `setupGkeepStatusBar()`, `updateVaultInboxCount()`, `scheduleKeepSync()`, and `handleGkeepClick()`.
   - Register vault modify listener for `gkeep_inbox.md`.

### Phase 3: Verification & Edge Cases
1. **Offline Test**: Disconnect Wi-Fi. Verify indicator displays cached count without hanging or error spam.
2. **Unauthenticated Test**: Remove token command. Verify indicator gracefully hides without errors.
3. **Reactive Modification Test**: Edit `gkeep_inbox.md` in Obsidian (e.g. check a task `[ ]` ➔ `[x]`). Verify count decrements instantaneously.
4. **Pull Ingestion Test**: Click indicator with pending Keep notes. Verify `bob gkeep pull` runs, notes land in `gkeep_inbox.md`, Keep count clears to 0, and vault count increments.

---

## 8. Conclusion

The user's plan to add a Google Keep and `gkeep_inbox.md` indicator to Obsidian's footer is an **outstanding functional enhancement** that bridges the mobile capture and desktop review gap. By treating Google Keep and `gkeep_inbox.md` as the two sequential stages of an inbound capture pipeline, and by decoupling the slow/fragile network sync from the lightning-fast reactive vault watcher, this feature can be delivered as an intuitive, rock-solid, and visually stunning addition to `bob-ledger-tools`.
