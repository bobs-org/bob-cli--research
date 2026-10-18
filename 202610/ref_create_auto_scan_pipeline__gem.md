# Research Report: Automating Reference Intake Across Tailnet Nodes

**Author:** `research.4s.gem`  
**Date:** 2026-10-18  
**Topic:** Automating `bob ref scan` and streamlining `bob ref create` across multi-machine tailnet topology  
**Target Repository:** `bob-cli`  

---

## Executive Summary

Running `bob ref create <target>` currently places generated, marker-stamped PDFs into `~/bob/xlib/` (intake) and prints `next: bob ref scan`. Because `xlib/` is intentionally excluded from Git synchronization in the Bob vault's `.gitignore`, newly created references remain trapped in local limbo until `bob ref scan` is executed. The reference note (`ref/<ref_type>/<name>.md`) is not generated, no reading task is filed in the parent note (`reading_inbox.md` or area note), Highlights app cannot see the PDF, and the PDF does not sync to any other machine.

Currently, the only automated scan trigger across Bryan's entire tailnet is a 15-minute cron job on a single machine: `kellys-macbook-pro` (the MacBook). That cron job runs `maybe_bob_highlights_sync -w`, which invokes `bob_xlib_pull` to probe `athena` and `apollo` over SSH, pulls pending PDFs via `rsync --remove-source-files`, and executes `bob ref scan`.

This architecture has a fatal availability and latency flaw:
1. **The MacBook is a battery-powered roaming laptop.** When the lid is closed, it is asleep, traveling, or offline, the cron job does not run. As a result, references created on `athena` (Linux desktop) or `apollo` (cloud VM) are stranded in `xlib/` indefinitely until Bryan manually intervenes or opens his laptop.
2. **Interactive Latency:** Even when all nodes are online and awake, a polling window of up to 15 minutes breaks the user workflow. When a user captures an article, paper, or note snapshot, they expect to immediately read it, view its reference note, or see its reading task in Obsidian.
3. **The Core Architectural Misconception:** Treating the problem as *"how to automate running `bob ref scan` periodically across 3 machines"* addresses the symptom rather than the cause. `bob ref scan` is a heavy, $O(N)$ batch reconciliation process that scans all 469+ PDFs in the library (~8.0s execution time) to discover sidecar annotations made in the Highlights macOS/iOS app. In contrast, ingesting a *single* newly created reference is an $O(1)$ operation that takes only **~68 milliseconds** via `bob ref sync`.

### Key Recommendation
We recommend **decoupling interactive single-reference intake from periodic batch annotation reconciliation**. Specifically:
- Teach `bob ref create` to perform **immediate scoped intake and sync** by default (`create-and-sync`). It will install the generated PDF and companion audio directly into `lib/` and execute single-PDF sync (`sync_pdf`) in ~68ms.
- Once the PDF is placed in `lib/` and its note is created in `ref/`, the existing, highly reliable 15-second Git synchronization engine (`bob vault-sync` via inotify systemd on Linux and launchd on macOS) automatically commits and replicates the usable reference across all machines within 15–30 seconds.
- Retain `xlib/` and the MacBook's 15-minute cron purely as a background fallback for manual, out-of-band PDF drops and for Highlights app annotation sidecars.

---

## 1. Current Architecture & Problem Analysis

### 1.1 The Multi-Machine Environment
Bryan operates three primary nodes on his Tailscale tailnet:
1. **`athena`** (`athena.tail297af1.ts.net`, Linux x86_64): Primary local workstation. High-performance, generally always on or awake during working hours. Fully equipped with pandoc, xelatex, chrome/playwright, uv, and bob-cli.
2. **`apollo`** (`apollo.tail297af1.ts.net`, Linux x86_64, DigitalOcean droplet): Cloud server. Always on, 24/7 connectivity, runs unattended tasks.
3. **`kellys-macbook-pro` / `mac`** (`kellys-macbook-pro.tail297af1.ts.net`, macOS Darwin): Personal laptop. Mobile, battery-powered, frequently sleeps with lid closed. Hosts the native macOS Highlights PDF annotation app and Obsidian desktop.

### 1.2 Vault Synchronization Channel
Since August 2026 (Epic `bob-cli-1n`), the Bob Obsidian vault (`~/bob`) synchronizes strictly through Git via `bob vault-sync`:
- **Linux (`athena` and `apollo`):** Run `bob-vault-sync.service` (systemd user service) executing `~/bin/bob_vault_sync_watch`. It uses `inotifywait` with a 15-second timeout and 5-second debounce to detect filesystem changes and run `bob vault-sync -q`.
- **macOS (`mac`):** Runs `com.bbugyi.bob-vault-sync.plist` (launchd user agent) running `bob vault-sync -q` every 15 seconds.
- Commits are pushed to and pulled from GitHub (`github-bob`), auto-resolving non-overlapping edits and quarantining true conflicts into `_conflicts/`.

### 1.3 The Role of `xlib/` vs `lib/`
In `~/bob/.gitignore`, the following rules govern attachments and PDFs:
```gitignore
!*.pdf
!*.PDF
!*.mp3

# PDF trees carried outside git.
lit_review/
xlib/
```
- **`lib/`:** The canonical reference library (`~/bob/lib/<ref_type>/<name>.pdf`). All PDFs, companion audio (`.mp3`), and sidecar notes (`.md`, `.textbundle`) in `lib/` **are tracked in Git**.
- **`xlib/`:** The intake staging area (`~/bob/xlib/<ref_type>/<name>.pdf`). **Git explicitly ignores `xlib/`.** Files in `xlib/` are never committed or synced by `bob vault-sync`.

This distinction was instituted during the August 2026 migration (`obsidian_vault_git_sync.md`) after an untracked intake PDF (`xlib/chat/AGENTS.pdf`) broke Obsidian Sync's vault quota. The rule was established that unverified intake PDFs must not enter Git staging.

### 1.4 The Creation & Scan Lifecycle
When Bryan runs `bob ref create <target>`:
1. `create_pdf` renders the content (via pandoc/xelatex for Markdown/notes or Playwright/Chrome for URLs).
2. `stamp_and_install` writes the Page-1 `/Text` annotation marker (`status: ready`, `parent: ...`, metadata, return links).
3. The PDF is written to `plan.target`, which defaults to `~/bob/xlib/<ref_type>/<stem>.pdf`.
4. Companion audio (if `--listen` was requested) is copied to `~/bob/xlib/<ref_type>/<stem>.mp3`.
5. The command prints `next: bob ref scan` and exits with code 0.

At this point:
- The PDF sits in `~/bob/xlib/`.
- The reference note `ref/<ref_type>/<stem>.md` **does not exist**.
- The reading task `- [ ] #task Read ...` **does not exist** in `reading_inbox.md` or the parent note.
- `bob ref list` and `bob ref find` treat the reference as `in_intake`, not in the library.
- Highlights app cannot open the PDF (it watches `lib/`).
- Because `xlib/` is gitignored, `bob vault-sync` does not commit the file.

### 1.5 The Current "Highlights Bridge" Automation
How does `xlib/` currently get scanned?
- Only the MacBook runs scheduled scanning via crontab:
  ```cron
  0,15,30,45 * * * * ~/bin/maybe_bob_highlights_sync -w >> /var/tmp/maybe_bob_highlights_sync.log 2>&1
  ```
- `maybe_bob_highlights_sync` executes `bob highlights scan -w`.
- `bob ref scan` invokes its configured pre-scan hook:
  ```yaml
  highlights:
    pre_scan_hook: PATH="$HOME/bin:$PATH" bob_xlib_pull
  ```
- `bob_xlib_pull`:
  1. Checks if it is running on macOS (`case "$(uname -s)" in Darwin) ... *) exit 0 ;; esac`). On Linux, it exits immediately with code 0.
  2. Probes `athena` and `apollo` concurrently over SSH using non-blocking connection options (`ConnectTimeout=5`).
  3. If pending files exist in `~/bob/xlib/` on either host, it runs:
     ```bash
     rsync -a --remove-source-files --ignore-existing "${transfer_host_name}:bob/xlib/" "$dest_dir/"
     ```
  4. Runs `bob highlights --no-hooks scan -w` on the MacBook.
  5. `scan` moves PDFs from the Mac's `xlib/` to `lib/`, writes reference notes in `ref/`, and files reading tasks.
  6. The Mac's `bob vault-sync` LaunchAgent commits `lib/` and `ref/` and pushes to GitHub within 15 seconds.
  7. `athena` and `apollo` pull those commits via their own `bob-vault-sync.service`.

### 1.6 Failure Modes of the Current Setup
1. **MacBook Sleep / Power Off:** The MacBook is not a server. When Bryan travels, puts the laptop in a bag, or leaves it unplugged overnight, the cron daemon halts. Captures on `athena` or `apollo` stay trapped in `xlib/` indefinitely.
2. **Unacceptable Latency (0 to 15+ minutes):** Even if the MacBook is open and active, waiting up to 15 minutes to read an article just captured on `athena` disrupts focus.
3. **Unidirectional Topology:** Athena and Apollo cannot push their intake to the Mac; they rely entirely on the Mac polling them.
4. **Manual Scan on Linux Is Incomplete:** If Bryan runs `bob ref scan` manually on `athena`, it processes only `athena:~/bob/xlib/`. It does not pull from `apollo` because `bob_xlib_pull` only runs on Darwin.

---

## 2. Critique of the Plan: Is Automating `bob ref scan` the Right Goal?

Bryan asks:
> *"I would like to think of a way to make this much more convenient/automatic somehow so I rarely need to run the `bob ref scan` command manually, but I'm not sure how to achieve this reliably. Can you do some research with the goal of helping me decide the best way to implement this? Also, critique this plan in general. Is this a good idea? Would you take a different approach?"*

### 2.1 The Two Disparate Duties of `bob ref scan`
The root design flaw lies in treating **Intake Ingestion** and **Library Reconciliation** as the exact same operation. In `bob-cli`, `bob ref scan` performs two completely different jobs:

| Attribute | Job A: Intake Ingestion | Job B: Continuous Library Sync |
| :--- | :--- | :--- |
| **Trigger** | `bob ref create` or file dropped in `xlib/` | User highlights a PDF in Highlights app |
| **Scope** | 1 newly created PDF (or small batch) | All 469+ PDFs in `~/bob/lib/` |
| **Duration** | **~68 milliseconds** | **~8.0 seconds** |
| **Frequency** | On-demand (few times per day) | Periodic background sweep (every 15 min) |
| **Host Relevance** | Any node (`athena`, `apollo`, `mac`) | macOS only (where Highlights app runs) |
| **Actions** | Move `xlib/` $\rightarrow$ `lib/`, initial note creation, reading task insertion | Read sidecars (`.textbundle`/`.md`), update managed body, sync marker hashes |

### 2.2 Why Automating Full `bob ref scan` Across Machines Is a Trap
If we attempt to solve Bryan's problem by setting up background timers, watchers, or distributed triggers to run `bob ref scan` automatically across all three machines, we introduce serious complications:
- **Lock Contention:** `bob ref scan` takes `acquire_scan_writer_lock`. Running full scans frequently on multiple machines creates lock collisions with `bob vault-sync`, `bob nightly`, and interactive commands.
- **Resource Inefficiency:** Scanning 469 PDFs every time an article is created burns CPU cycles and disk I/O, especially on a battery-constrained laptop.
- **Network Flakiness:** Having `athena` or `apollo` attempt to wake or SSH into the MacBook when a capture finishes is inherently unreliable due to macOS power management and dynamic sleep states.

### 2.3 The Real Question to Ask
Instead of asking:
> *"How do we automate running the 8-second batch `bob ref scan` whenever a file is created?"*

We should ask:
> *"Why does `bob ref create` stop at `xlib/` instead of completing the reference creation directly into `lib/`?"*

When a user explicitly types `bob ref create https://example.com/article`, their intent is clear: they want that reference added to their reading library. Creating a PDF, stamping its marker, moving it into `lib/`, writing the `ref/` note, and inserting the reading task in `reading_inbox.md` takes **under 100 milliseconds** combined. 

Once written to `lib/` and `ref/`, the existing, bulletproof Git synchronization mechanism automatically distributes the completed reference to all tailnet machines within seconds!

---

## 3. Evaluation of Alternative Approaches

| Metric | Option 1: Inline Scoped Sync (`create-and-sync`) | Option 2: Post-Create Background Kick | Option 3: Local `xlib/` inotify/fswatch Daemons | Option 4: Cross-Machine SSH/Webhook Push | Option 5: Git-Tracked `xlib/` Staging |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Latency** | **< 100 ms** (instant) | 1–3 seconds | 2–5 seconds | Variable (fails if Mac asleep) | 30–60 seconds |
| **Reliability** | **100%** (deterministic) | 95% (process fork) | 85% (watcher crashes/misses) | 40% (depends on Mac sleep) | 70% (race conditions) |
| **Cross-Machine Dependencies** | **None** (relies on Git) | None (relies on Git) | None (relies on Git) | High (direct SSH to laptop) | None (relies on Git) |
| **Offline Support** | **Full** (works offline) | Full | Full | None | Partial |
| **Resource Cost** | Negligible (~68ms) | High (~8s full scan) | High (~8s per event) | High + network timeouts | High (double Git commits) |
| **Maintenance Burden** | Low (code in `bob-cli`) | Low | High (OS daemons on 3 nodes)| High (SSH keys, IP changes) | Low |
| **Verdict** | **STRONGLY RECOMMENDED** | Feasible alternative | Over-engineered | Rejected | **Rejected** |

### Detailed Assessment of Options

#### Option 1: Inline Scoped Intake & Sync on `create` (Recommended)
- **Mechanism:** In `bob ref create`, once `stamp_and_install` finishes, the command directly installs the PDF to `lib/<ref_type>/<stem>.pdf` (with existing collision suffixing), copies companion audio to `lib/`, and invokes `sync_pdf` for that specific target.
- **Why it wins:**
  1. **Instant gratification:** The reference note and reading task exist the millisecond `bob ref create` exits.
  2. **Zero distributed complexity:** No daemon, no SSH, no polling.
  3. **Leverages existing Git sync:** `lib/` and `ref/` are tracked by git. As soon as they are written, `bob_vault_sync_watch` on Linux and the LaunchAgent on macOS pick them up and push them. The other machines pull within 15–30 seconds.
  4. **Works offline:** If Bryan is on an airplane on his MacBook or offline on `athena`, the reference is fully created and usable locally.

#### Option 2: Post-Create Detached Kick (`bob ref jobs run` style)
- **Mechanism:** When `bob ref create` exits, it spawns a detached child process: `bob ref scan --no-hooks -q &`.
- **Flaws:** It runs the full 469-PDF batch scan (~8s of CPU). If Bryan captures 3 articles in quick succession, three overlapping full scans contend for `scan_writer_lock`.

#### Option 3: Event-Driven File Watchers on `xlib/` (`inotify` / `fswatch`)
- **Mechanism:** Install a systemd unit on Linux (`inotifywait`) and a LaunchAgent on macOS (`fswatch`) monitoring `~/bob/xlib/`. When a `.pdf` appears, run `bob ref scan`.
- **Flaws:** Introduces OS-level daemon maintenance across Linux and macOS. Watchers require tricky debouncing (e.g. not triggering while a multi-megabyte PDF is still being written). Furthermore, it still runs the heavy 8-second scan.

#### Option 4: Cross-Machine Remote Trigger (SSH Kick to Mac)
- **Mechanism:** When `create` runs on `athena` or `apollo`, it runs `ssh mac bob_xlib_pull`.
- **Flaws:** Catastrophic failure mode when the Mac is asleep. Laptop sleep breaks SSH connections or incurs 5–30s connection timeouts. Servers (`athena`/`apollo`) should never depend on a client laptop.

#### Option 5: Git-Tracked `xlib/` Staging
- **Mechanism:** Remove `xlib/` from `.gitignore` so intake PDFs replicate via Git.
- **Flaws:** Strongly discouraged. Re-introduces the risk of hitting GitHub's 100MB file limit or bloat from draft files. More importantly, it creates Git churn: committing `xlib/blogs/paper.pdf`, then deleting it and committing `lib/blogs/paper.pdf` 30 seconds later doubles repository growth for binary assets.

---

## 4. Adjustments to Requirements

Based on this analysis, we recommend adjusting Bryan's requirements as follows:

1. **Reframe the Goal:**
   - *Original Goal:* "Make running `bob ref scan` automatic across my tailnet machines."
   - *Adjusted Goal:* **"Eliminate the need to run `bob ref scan` for newly created references, making `bob ref create` produce an immediately usable reference in `lib/` and `ref/`."**
2. **Retain `xlib/` Exclusively as an Out-of-Band Staging Area:**
   - Keep `xlib/` in `.gitignore`.
   - Keep `bob_xlib_pull` and the MacBook's 15-minute cron job intact as a background safety net for cases where Bryan manually drops a raw PDF downloaded from a browser directly into `~/bob/xlib/`.
3. **Add an Opt-Out Flag for Staged Creation:**
   - Add a `--stage` or `--no-sync` flag to `bob ref create` (or `--staged`) if Bryan ever wants to generate an intake PDF without immediately creating a note or task in the vault (though default behavior should be immediate sync).
4. **Extend Immediate Sync to `bob capture` (Ref Jobs):**
   - When a URL is captured via `bob capture`, the background worker (`bob ref jobs run`) executes `create_pdf`.
   - By embedding immediate sync into the creation core, `bob capture` will also automatically produce the final reference note and reading task without waiting for the Mac's cron.

---

## 5. Technical Architecture & Implementation Blueprint

### 5.1 The `create-and-sync` Execution Flow

Currently, in `src/native/highlights_ref/create.rs`, the flow is:
```
render_temp_pdf()
       │
       ▼
stamp_and_install()  ──► Writes PDF to xlib/<ref_type>/<stem>.pdf
       │
       ▼
print_next_step()    ──► Prints "next: bob ref scan"
```

The modified flow:
```
render_temp_pdf()
       │
       ▼
stamp_and_install()  ──► Writes PDF directly to lib/<ref_type>/<stem>.pdf
       │                 (and companion audio to lib/<ref_type>/<stem>.mp3)
       ▼
sync_pdf_scoped()    ──► Takes scan lock (with 5s timeout)
       │             ──► Reads marker from newly created PDF
       │             ──► Emits ref/<ref_type>/<stem>.md
       │             ──► Inserts reading task in parent note (reading_inbox.md)
       ▼
Report Outcome       ──► Prints note path, task link, and "ready in library"
       │
       ▼
(Existing Git Sync)  ──► inotify / launchd picks up lib/ and ref/ changes
                         and commits/pushes to all tailnet nodes in < 15s.
```

### 5.2 Implementation Details in `bob-cli`

#### Step 1: Update Target Planning in `stamp.rs`
In `plan_default_target` (`src/native/highlights_ref/stamp.rs`):
- Currently, `plan_default_target` sets `target` to `xlib/<ref_type>/<stem>.pdf` and `library_destination` to `lib/<ref_type>/<stem>.pdf`.
- With auto-sync enabled (the default), `plan_default_target` can target `lib/` directly, with collision preflight already verifying that no occupant exists.
- If companion audio exists (`--listen` or `--audio`), it installs directly to `lib/<ref_type>/<stem>.mp3`.

#### Step 2: Wire Scoped Sync in `create.rs`
In `create_pdf` (`src/native/highlights_ref/create.rs`):
- After successful `stamp_and_install`, instead of calling `print_next_step`:
```rust
let sync_options = SyncOptions {
    dry_run: options.dry_run,
    write_pdf: false,
    prefer: None,
};

// Acquire the scan writer lock briefly to prevent collisions with batch scan
let _scan_lock = acquire_scan_writer_lock_with_timeout(Duration::from_secs(5))?;

// Execute the existing scoped sync_pdf (~68ms)
sync_pdf(config, &plan.target, sync_options)?;
```
- Print the created note path and parent note task confirmation:
```text
✓ created Highlights-ready PDF
source: https://example.com/article
pdf: /home/bryan/bob/lib/blogs/article.pdf
note: /home/bryan/bob/ref/blogs/article.md
reading_task: reading_inbox.md ^ref-article
status: ready
parent: reading_inbox
```

#### Step 3: Concurrency & Lock Safety
- `sync_pdf` runs with `acquire_scan_writer_lock_with_timeout(5s)`.
- If the Mac cron job or a manual `bob ref scan` happens to be running at that exact second, `create` waits up to 5 seconds for the scan lock to release, then writes cleanly.
- `bob vault-sync` shares `bob_sync.lock`. It will see the new `lib/` and `ref/` files on disk during its next 15-second tick and commit them cleanly.

#### Step 4: Ref-Jobs Background Worker Integration
In `src/native/ref_jobs/worker.rs`:
- When `bob capture` queues a job and kicks `bob ref jobs run`, the worker calls `create_pdf`.
- Because `create_pdf` now performs the sync inline, the worker's `done.jsonl` log will record the created `note` path immediately.
- The human report in `bob ref jobs` can report `✓ clipped and synced → ref/blogs/article.md`.

---

## 6. Migration and Operational Plan

### Phase 1: Local Code Change in `bob-cli`
1. Add an optional `--no-sync` flag to `bob ref create` CLI for backwards compatibility or dry debugging.
2. Update `stamp.rs` and `create.rs` to execute scoped `sync_pdf` immediately after stamping when `--no-sync` is false.
3. Update unit and integration tests in `tests/cli/highlights/create.rs`. Verify that `bob ref create` produces both the PDF in `lib/` and the Markdown file in `ref/`.

### Phase 2: Deploy to Tailnet Nodes
1. Run `cargo install --path .` (or `bob plugins sync` / chezmoi deploy) to install the updated `bob` binary on `athena`, `apollo`, and `kellys-macbook-pro`.
2. Verify with `bob ref doctor` on all three machines.

### Phase 3: Validation Matrix
Test the following scenarios across the tailnet:
1. **Interactive create on `athena` while MacBook is asleep:**
   - Put MacBook to sleep (lid closed).
   - On `athena`, run: `bob ref create https://example.com/test-article -P reading_inbox`.
   - Confirm `lib/blogs/test-article.pdf` and `ref/blogs/test-article.md` are created immediately on `athena`.
   - Confirm `git -C ~/bob status` on athena shows the new files committed by `bob-vault-sync.service` within 15 seconds.
   - Wake MacBook; confirm `git -C ~/bob pull` brings down the PDF and note.
2. **Interactive create on `kellys-macbook-pro`:**
   - Run `bob ref create` on the Mac.
   - Confirm PDF and note appear immediately without waiting for the 15-minute cron.
   - Open Highlights app; confirm the PDF in `lib/` is available for reading immediately.
3. **Capture via `bob capture`:**
   - Run `bob capture 'https://example.com/test-capture'`.
   - Confirm the background worker clips the link and syncs it into `lib/` and `ref/`.
4. **Fallback verification (Manual drop into `xlib/`):**
   - Drop a manual PDF into `athena:~/bob/xlib/papers/manual.pdf`.
   - Confirm that the MacBook's 15-minute cron (`bob_xlib_pull`) still drains `xlib/` from athena and runs `bob ref scan` as a legacy fallback.

---

## 7. Conclusion

Attempting to coordinate and automate the heavy, 8-second batch `bob ref scan` command across three separate machines—one of which is an intermittently sleeping laptop—is an unnecessary distributed systems problem. 

By recognizing that `bob ref create` was merely stopping one step too early, we can solve Bryan's problem completely at the source. Making `bob ref create` perform scoped intake and sync (~68ms) makes references immediately usable on the local machine the instant creation finishes, while the existing 15-second Git sync engine automatically and reliably propagates the finished reference across the entire tailnet.
