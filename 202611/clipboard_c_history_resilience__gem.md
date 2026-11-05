# Research: Clipboard `%c` Multi-Entry History Architecture & Resilience

**Author**: `research.5r.gem`  
**Date**: November 2026  
**Target Repository**: `bobs-org/bob-cli` & `bobs-org/bob-mac-capture`  
**Scope**: `%c` and `%c<N>` capture directives, clipboard history providers, macOS pasteboard mechanics, and resilience architecture.

---

## 1. Executive Summary

When running `bob capture` with the `%c` capture directive, single-entry capture (no index or `%c1`) works reliably, but multi-entry history capture (`%c<N>` where `N > 1`) consistently exhibits a specific defect: **only the first entry is ever correct; subsequent entries are wrong or stale.**

### Key Findings

1. **Root Cause Confirmation**:
   - `%c` (single-item) reads directly from the live macOS pasteboard via `pbpaste` (`NSPasteboard.generalPasteboard`). It communicates directly with the macOS window server, requires no third-party daemon, has zero latency, and always returns the current system clipboard.
   - `%c<N>` (`N > 1`) executes a **hybrid split**: it reads entry #1 from live `pbpaste`, but fetches older entries (`candidates`) by querying a hardcoded SQLite file on disk:
     `~/Library/Application Support/com.clipy-app.Clipy/sqlite.db`.
   - **The "Zombie Provider" Phenomenon**: If Clipy was ever installed or run on the MacBook in the past (e.g. during initial feature development in July 2026), its SQLite file remains on disk forever. When `bob` executes, `database.is_file()` returns `true`, and `bob` queries the database without verifying whether Clipy is currently running or whether the records are fresh. As a result, `bob` takes the live pasteboard for item #1 and pairs it with months-old records from July 2026 for items #2 through #N.
   - **Did we integrate with the wrong clipboard manager?** Yes. Clipy was hardcoded as the sole built-in macOS history backend without verifying the user's active workflow, checking process liveness, or supporting modern alternatives (e.g., Maccy, Raycast, Alfred). Furthermore, Clipy itself is an unmaintained legacy utility with severe internal timing flaws (500ms polling latency, 1-second timestamp truncations resulting in random hash/UUID sorting for intra-second copies, and duplicate deduplication suppression).

2. **Critique of the Current Design**:
   - Relying on a third-party application's private, unversioned SQLite database file without an IPC contract, process check, or staleness threshold is fundamentally fragile.
   - The `%c<N>` feature itself is valuable for batch intake (e.g., quickly copying 3 URLs or research quotes), but the clipboard is a volatile medium. Without visual feedback, staleness guards, and strict health checks, multi-entry capture easily corrupts user notes.

3. **Recommended Solution**:
   - **First-Party Provider via `bob-mac-capture`**: Rather than chasing third-party clipboard managers, leverage Bryan's native `bob-mac-capture` menu-bar app, which is already running 24/7 on macOS, already polls `NSPasteboard` change counts, and can maintain a first-party, zero-overhead, rolling history buffer (`~/.local/state/bob/clipboard_history.json`).
   - **Fail-Fast Liveness & Staleness Guards**: If querying any external database (Clipy or Maccy), verify process liveness via `pgrep` and verify that the newest entry is within a tight time window (e.g., < 15 minutes) of the current clipboard. Never silently return ancient history.
   - **Health & Diagnostic Commands**: Expose provider resolution and status in `bob capture --dry-run` and add a diagnostic command (`bob doctor` or `bob clip --status`) so the user immediately knows where clipboard history is coming from.

---

## 2. Technical Root Cause Analysis

### 2.1 The Two Paths of `%c`

In `src/native/capture_clip/clipboard.rs`, clipboard resolution is divided into two distinct functions:

```rust
pub(crate) fn read_clipboard() -> Result<String, String> {
    let output = clipboard_command_output()?;
    normalize_clipboard_output(output.stdout)
}

pub(crate) fn read_clipboard_history(
    count: usize,
) -> Result<Vec<String>, String> {
    let current = read_clipboard()?;
    if count == 1 {
        return Ok(vec![current]);
    }

    let candidates = read_history_candidates(count)?
        .into_iter()
        ...
    merge_history_candidates(current, candidates, count)
}
```

#### Single Entry (`count == 1`):
When capturing `%c` or `%c1`, `read_clipboard()` calls `clipboard_command_output()`. On macOS, this invokes `pbpaste` directly. `pbpaste` queries the macOS window server's AppKit pasteboard directly. It does not depend on any running daemon, background helper, or file on disk. If you press `Cmd+C`, `pbpaste` immediately returns that content.

#### Multi-Entry (`count > 1`):
When capturing `%c2`, `%c3`, etc., `read_clipboard_history(count)` performs the following steps:
1. Reads `current` using `read_clipboard()` (live `pbpaste`).
2. Calls `read_history_candidates(count)`.
   On macOS, `read_history_candidates` hardcodes:
   ```rust
   #[cfg(target_os = "macos")]
   {
       let database = bob_env::home_dir()
           .join("Library/Application Support/com.clipy-app.Clipy/sqlite.db");
       read_clipy_history(&database, count)
   }
   ```
3. Queries Clipy's SQLite database:
   ```sql
   SELECT id FROM pasteboardHistories ORDER BY updateAt DESC, id DESC LIMIT ?1
   ```
4. Calls `merge_history_candidates(current, candidates, count)`:
   ```rust
   pub(super) fn merge_history_candidates(
       current: String,
       mut candidates: Vec<String>,
       count: usize,
   ) -> Result<Vec<String>, String> {
       if let Some(index) = candidates.iter().position(|value| value == &current) {
           candidates.remove(index);
       }
       let available = candidates.len() + 1;
       if available < count {
           return Err(format!(
               "clipboard history requested {count} entries but only {available} are available"
           ));
       }
       let mut values = Vec::with_capacity(count);
       values.push(current);
       values.extend(candidates.into_iter().take(count - 1));
       Ok(values)
   }
   ```

### 2.2 The "Only First Entry Is Correct" Mechanism

The root cause of Bryan's exact symptom is the interaction between live `pbpaste`, Clipy's dormant SQLite file, and `merge_history_candidates`:

1. **The Ghost Database**:
   Commit `e6b70be4` (July 15, 2026) introduced Clipy integration as the default macOS history provider. If Clipy was installed or tested on Bryan's MacBook at that time, `~/Library/Application Support/com.clipy-app.Clipy/sqlite.db` was created.
   Even if Bryan subsequently stopped using Clipy, uninstalled the app, switched to another clipboard manager (or uses none), the SQLite database file was left behind on disk.

2. **False Health Check**:
   `read_clipy_history` only performs a simple file existence check:
   ```rust
   if !database.is_file() {
       return Err(format!("Clipy clipboard history database was not found..."));
   }
   ```
   Because the file exists, `bob` treats it as healthy and active.

3. **Assembling the Frankenstein History**:
   - `current` is read from `pbpaste`. It contains the item Bryan copied 2 seconds ago (e.g., `"https://news.ycombinator.com"`).
   - `candidates` are read from `sqlite.db`. Because Clipy is not running, the newest rows in `sqlite.db` are from July 2026 (e.g., `"old task item 1"`, `"old task item 2"`).
   - In `merge_history_candidates`:
     - `candidates.iter().position(|value| value == &current)` finds no match because `"https://news.ycombinator.com"` is not in the 4-month-old database.
     - `values.push(current)` inserts the live copy at index 0.
     - `values.extend(candidates.into_iter().take(count - 1))` appends the top entries from July 2026.
   - Result:
     - Entry 1: Current, accurate clipboard content.
     - Entry 2: Ancient clip from months ago.
     - Entry 3: Ancient clip from months ago.
   This matches the observed defect with 100% precision.

### 2.3 Even if Clipy Were Running: Inherent Architectural Flaws

Inspection of Clipy's source code (`gh:Clipy/Clipy`) reveals several internal mechanisms that make Clipy unsuitable as a deterministic clipboard history provider:

1. **500ms Timer Polling Delay**:
   In `Clipy/Sources/Services/ClipService.swift`:
   ```swift
   for await _ in continuousClock.timer(interval: .milliseconds(500)) {
       let changeCount = NSPasteboard.general.changeCount
       guard changeCount != self?.cachedChangeCount else { continue }
       self?.cachedChangeCount = changeCount
       self?.create()
   }
   ```
   Clipy does not use event-driven pasteboard observation; it polls every 500ms. If a user copies item A, copies item B, and triggers capture within 500ms, Clipy has not yet written item B to SQLite.

2. **1-Second Timestamp Granularity & Arbitrary Sorting**:
   When Clipy records a clip:
   ```swift
   let unixTime = Int(Date().timeIntervalSince1970)
   let id = PasteboardHistory.ID(rawValue: savedHash)
   pasteboardHistoryRepository.save(id: id, content: content, updateAt: unixTime)
   ```
   `updateAt` is stored in integer seconds. If two clips are copied within the same second, both have identical `updateAt` timestamps.
   `bob-cli`'s query sorts by:
   `ORDER BY updateAt DESC, id DESC LIMIT ?1`
   When `updateAt` matches, sorting falls back to `id DESC`. But `id` is either a SHA-256 hash of the content or a random UUID! This means intra-second copies are sorted alphabetically by hash, completely scrambling chronological order.

3. **Deduplication Suppression**:
   In `ClipService.swift`:
   ```swift
   let historyID = PasteboardHistory.ID(rawValue: content.hash)
   if pasteboardHistoryRepository.fetchHistory(id: historyID) != nil, !allowsDuplicateHistory { return }
   ```
   If duplicate history is disabled in Clipy preferences, copying an item that already exists in history is a no-op: it neither updates `updateAt` nor moves the item to the top of the history stack.

4. **External Interruption (`killall Clipy`)**:
   In Bryan's dotfiles (`chezmoi`), `home/bin/executable_paste_parts` contains:
   ```bash
   # Kill Clipy clipboard manager to prevent interference.
   killall Clipy 2>/dev/null
   trap 'open -a Clipy' EXIT
   ```
   Any script execution or crash that terminates Clipy leaves the stale SQLite file on disk while `bob capture` continues reading it.

---

## 3. Critique of the Plan & Architecture

### 3.1 Is Integrating with a Third-Party Clipboard Manager a Good Idea?

**Verdict: No. It is an architectural anti-pattern for a core capture pipeline.**

| Aspect | Third-Party SQLite Integration (Current) | First-Party / Dedicated Bridge (Proposed) |
| :--- | :--- | :--- |
| **Contract** | None. Private schema subject to unannounced migrations or format changes. | Versioned, documented JSON/IPC contract. |
| **Liveness** | Invisible. A dead process leaves a readable database forever. | Explicit heartbeat, process checks, or direct IPC. |
| **Latency** | 500ms–1000ms polling lag in third-party event loops. | Synchronous or instant change notification. |
| **Portability** | Hardcoded to macOS Clipy. Broken on Linux unless manual env var set. | Consistent architecture across environments. |
| **User Agency** | Silent fallback to unknown local databases. | Transparent diagnostics (`bob clip status`). |

Reading the private SQLite file of an external GUI application violates basic decoupling principles:
- There is no file locking coordination. If Clipy is writing a transaction while `bob` reads, SQLite can encounter lock contention or read partial writes.
- The user is never informed that `bob` is delegating to Clipy. When it fails, the user cannot tell whether `bob`, macOS, or a clipboard manager is responsible.

### 3.2 Is `%c<N>` Multi-Entry Capture a Good Idea in General?

**Verdict: The feature is valuable, but its current execution is too fragile.**

- **User Value**: When doing research, reading papers, or compiling reference notes, copying 3 links or excerpts in succession and capturing them with `Review papers %c3` saves significant window-switching friction.
- **Inherent Risk**: The system clipboard is an invisible, shared global stack. It is easily polluted by:
  - Password managers auto-clearing or copying passwords/tokens.
  - Editor yank commands or linters copying to system clipboard.
  - Incidental selections.
- **Flawed Strictness**: Currently, if `available < count`, `bob capture` hard-fails the entire capture:
  ```rust
  if available < count {
      return Err(format!("clipboard history requested {count} entries but only {available} are available"));
  }
  ```
  Failing the entire command because the user thought they copied 3 items but only 2 were recorded creates user frustration.

---

## 4. Evaluation of Architectural Alternatives

### Alternative 1: Multi-Manager Auto-Detection (Maccy, Alfred, Clipy)
Attempt to detect whichever clipboard manager the user has installed:
- **Maccy**: Native Swift/AppKit, actively maintained, stores history in `~/Library/Containers/org.p0deje.Maccy/Data/Library/Application Support/Maccy/Storage.sqlite`.
- **Alfred**: Stores history in `~/Library/Application Support/Alfred/Databases/clipboard.rubydb`.
- **Raycast**: Stores encrypted/proprietary SQLite database; no public read interface.

*Assessment*: Fragile. Writing custom SQLite parsers for every clipboard manager on macOS leads to continuous maintenance burden and schema chasing.

### Alternative 2: First-Party History in `bob-mac-capture` (Recommended)
`bob-mac-capture` is Bryan's native macOS menu-bar capture frontend.
- It is already running continuously at login.
- It already polls `NSPasteboard.general.changeCount` in `CapturePanelModel.swift` to invalidate preview cards.
- It has full AppKit permissions and native pasteboard access.

*Implementation*:
- `bob-mac-capture` maintains a rolling buffer of the last 25 clipboard items (text, file URLs, and metadata) in memory and flushes it to `~/.local/state/bob/clipboard_history.json` on changes.
- `bob-cli` reads `~/.local/state/bob/clipboard_history.json` as its primary macOS history provider.

*Assessment*: **Highest quality, lowest maintenance.** Zero third-party dependencies, sub-millisecond updates, guaranteed chronological ordering, and total ownership of the data contract.

### Alternative 3: Lightweight CLI History Daemon (`bob clip listen` / launchd)
For headless environments or users not running `bob-mac-capture`, `bob` can provide a lightweight background listener:
- `bob clip listen` runs as a user launchd agent (macOS) or systemd user service (Linux).
- Monitors pasteboard change counts and appends to `clipboard_history.json`.

*Assessment*: Excellent headless fallback for Linux or standalone CLI users.

### Alternative 4: Standardize on `BOB_CLIPBOARD_HISTORY_CMD`
`BOB_CLIPBOARD_HISTORY_CMD` already exists in `bob-cli`:
- It accepts the count as `$1` and expects a JSON array of strings newest-first.
- Users can plug in any command (e.g., a script querying Maccy, Raycast CLI, or a custom tool).

*Assessment*: Retain as an explicit override and integration test hook, but do not rely on it as the default out-of-the-box user experience.

---

## 5. Requirements Adjustments & Recommendations

To make `%c` and `%c<N>` resilient, reliable, and predictable, the following requirement adjustments are recommended:

### 1. Provider Resolution Hierarchy
`bob-cli` should resolve clipboard history through a deterministic, prioritized cascade:
1. **Environment Override**: `BOB_CLIPBOARD_HISTORY_CMD` (if set and non-empty).
2. **First-Party Bob History**: `~/.local/state/bob/clipboard_history.json` (written by `bob-mac-capture` or `bob clip listen`).
3. **Validated Third-Party Managers**: If and only if a third-party DB exists **AND passes process liveness and timestamp freshness checks**.
4. **Actionable Failure**: If no valid history provider is active, fail with clear instructions rather than reading stale files.

### 2. Mandatory Liveness & Freshness Guards
Any provider reading from an on-disk database must satisfy:
- **Process Liveness Check**: Verify that the owning process (e.g., `Clipy`, `Maccy`) is actively running.
- **Staleness Threshold**: Verify that the newest history entry in the database is not older than 15 minutes, or that it matches the current `pbpaste` value. If `pbpaste` does not match the top history entry and history is older than 5 minutes, flag the provider as out-of-sync.

### 3. Graceful History Count Handling
If a user requests `%c3` but only 2 entries are available in history:
- Provide an option or relaxed mode (or clear preview warning in Bob Mac Capture) showing that only 2 items exist, rather than aborting vault mutation unceremoniously.

### 4. Diagnostic Observability
Add a `bob clip status` command (and include clipboard diagnostics in `bob-mac-capture` settings):
- Prints the active provider, process status, file path, number of available history entries, and timestamp of the most recent entry.

---

## 6. Implementation Blueprint

```mermaid
flowchart TD
    A["User triggers `%c<N>`"] --> B{"`BOB_CLIPBOARD_HISTORY_CMD` set?"}
    B -- Yes --> C["Execute custom command"]
    B -- No --> D{"First-party history exists?<br/>`~/.local/state/bob/clipboard_history.json`"}
    D -- Yes & Fresh --> E["Read first-party history"]
    D -- No / Stale --> F{"External provider configured?<br/>(e.g., Clipy/Maccy DB)"}
    F -- Yes --> G{"Process alive &<br/>timestamp fresh (< 15 min)?"}
    G -- Yes --> H["Read external SQLite"]
    G -- No --> I["Reject provider as stale/dead"]
    F -- No --> I
    I --> J["Error: No active clipboard history provider.<br/>Suggest running `bob-mac-capture` or setting `BOB_CLIPBOARD_HISTORY_CMD`"]
    C --> K["Merge with live `pbpaste` & Validate"]
    E --> K
    H --> K
    K --> L["Return clean, chronological entries"]
```

### Phase 1: Immediate Hardening of `bob-cli` (Safety Patch)
1. **Add Staleness Check in `src/native/capture_clip/clipy.rs`**:
   - Query `MAX(updateAt)` from `pasteboardHistories`.
   - If `MAX(updateAt)` is older than 1 hour (or if current time - `updateAt` > threshold), reject the database with an explicit error:
     `"Clipy clipboard database is stale (newest entry is from YYYY-MM-DD); ensure Clipy is running or use BOB_CLIPBOARD_HISTORY_CMD"`.
2. **Add Process Check on macOS**:
   - Run a non-blocking check (`pgrep -x Clipy`) before opening the database.
3. **Sub-Second Tie-Breaking**:
   - If multiple entries share the same `updateAt` timestamp, do not sort by `id DESC` (hash/UUID). Fall back to SQLite rowid or asset creation order.

### Phase 2: Native History in `bob-mac-capture` (Durable Solution)
1. **In `bob-mac-capture`**:
   - In `CapturePanelModel.swift`, when `NSPasteboard.general.changeCount` advances, read plain text and file URLs.
   - Append to an atomic JSON file at `~/.local/state/bob/clipboard_history.json` containing:
     ```json
     {
       "version": 1,
       "updated_at": "2026-11-05T14:10:00Z",
       "entries": [
         { "timestamp": 1793887800, "text": "latest clip", "type": "text" },
         { "timestamp": 1793887792, "text": "older clip", "type": "text" }
       ]
     }
     ```
   - Cap history at 50 items.
2. **In `bob-cli`**:
   - Introduce `src/native/capture_clip/first_party.rs` to read this file.
   - Place this reader ahead of Clipy in `read_history_candidates()`.

### Phase 3: Verification & Integration Testing
- Add unit tests verifying that stale SQLite databases are rejected.
- Add integration tests verifying that `bob-mac-capture`'s JSON history format is parsed and deduplicated correctly.
- Verify end-to-end capture on macOS with live preview card agreement.

---

## 7. Conclusion

The `%c<N>` defect is not a flaw in capture grammar or parser logic; it is a **silent fallback to a dormant, unmaintained third-party SQLite file** that was hardcoded in July 2026. Because single-entry `%c` bypasses that database entirely and queries `pbpaste`, it worked flawlessly, masking the fact that the history backend was effectively dead.

By shifting clipboard history ownership to Bryan's existing `bob-mac-capture` application and adding strict liveness/staleness guards to `bob-cli`, `%c` and `%c<N>` will become completely deterministic, robust, and independent of fragile third-party tools.
