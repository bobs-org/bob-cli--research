# Research Report: In-Obsidian Bob Command-Mode & the `:` Keymap

- **Author**: Researcher `gem` (5-Researcher Swarm)
- **Date**: 2026-10-26
- **Status**: Complete & Ready for Synthesis
- **Target Repository**: `bob-plugins` (Obsidian plugin monorepo) & `bob-cli`
- **Output Target**: `research:202610/obsidian_colon_bob_command_mode__gem.md`

---

## 1. Executive Summary & Core Verdict

The proposal to introduce a fast, in-Obsidian `bob` command launcher triggered by a single keypress is **an outstanding ergonomic enhancement**, but **binding raw `:` in Vim Normal Mode carries severe technical and usability risks that must be carefully architected**.

Today, Bryan frequently leaves Obsidian to run essential terminal operations: syncing the vault with Git (`bob vault-sync`), running the end-of-day maintenance suite (`bob nightly`), reconciling task statuses (`bob task reconcile`), pulling Google Keep notes (`bob gkeep pull`), and deploying plugin changes (`bob plugins sync`). Moving these operations inside Obsidian preserves flow, eliminates window-switching latency, and unifies Bryan's daily workflow under a single interface.

However, treating this feature as a simple "map `:` to a command palette" will break standard Vim workflows unless key conflicts are addressed. Specifically:
1. **The Vim Ex-Mode Conflict**: In Vim (and Obsidian's CodeMirror Vim adapter), `:` is the canonical leader for Ex commands (`:w`, `:q`, `:s/.../.../g`, etc.). While Obsidian autosaves (making `:w` technically redundant), remapping `:` unconditionally in Normal Mode will destroy regex substitution (`:s`) and any muscle-memory Ex commands.
2. **The Output Problem**: Running CLI commands asynchronously cannot rely solely on Obsidian's transient `new Notice()` toasts. A 4-second toast is incapable of displaying multi-step logs, Git diff stats, or terminal error backtraces when operations fail.
3. **The Vault Concurrency Problem**: Commands such as `bob task reconcile`, `bob task archive`, and `bob vault-sync` modify Markdown files directly on disk. If triggered while Obsidian holds unsaved in-memory editor buffers, file clobbering or race conditions can occur.

### Recommended Solution Summary
We recommend building a dedicated Obsidian plugin, **`bob-command-mode`** (or a clean modular fragment within `bob-navigation-hotkeys`), designed around four pillars:
- **Smart Keymap Dispatch**: Map `:` in Vim Normal Mode (`nmap : :bob_command_mode<CR>` in `obsidian_vimrc.md`) to open a polished, fuzzy-searchable **Bob Command Palette Modal** (built on the vault's proven `FilteredPickerModal` design system). If Bryan types a traditional Ex command (such as `:s/foo/bar/g` or `:w`), the palette automatically detects the Ex syntax and passes it through to CodeMirror Vim's Ex engine. Additionally, register a global Obsidian command (`Cmd+Shift+B` or `<leader>b`) for contexts where CodeMirror is not focused (e.g. Reading View, Canvas, or Reading Board).
- **Curated Command Taxonomy**: Instead of dumping raw CLI flags into a flat list, implement a tiered registry of 12 core commands across three distinct operational modes: **Vault & Git Operations** (`vault-sync`, `nightly`, `plugins sync`), **Task Maintenance** (`task reconcile`, `task archive`, `task reroll`), and **Ingestion/Sync** (`gkeep pull`, `projects sync`, `ref sync`, `ref scan`). Support instant Dry-Run vs. Write toggling via `Shift+Enter` or `Tab`.
- **Two-Tiered Notification & Output Architecture**: When a command runs, a non-blocking status bar spinner appears. On completion, a subtle Notice toast reports runtime and status (`✓ bob vault-sync completed in 1.4s`) with an embedded `[View Output]` button. Clicking the button—or pressing `Ctrl+O` / running the `bob:show-last-output` command—opens a gorgeous, dark-mode **Command Output Inspector Modal** featuring ANSI color rendering, scrollable stdout/stderr logs, execution metrics, and a one-click `[Re-run]` button.
- **Buffer Safety & Lock Coordination**: The runner automatically flushes active editor changes to disk before spawning mutating commands, checks the shared maintenance lock (`/tmp/bob_sync.lock`), and debounces external file-watcher events upon completion.

---

## 2. Motivation & Workflow Context

### 2.1 The Terminal Context-Switch Tax
In Bryan's environment, Obsidian (`~/bob/`) serves as the single source of truth for daily planning, task execution, reading notes, and reference ingestion. However, the system's heavy machinery resides in the `bob` CLI:
- Git vault synchronization (`bob vault-sync`) connects machines (athena, apollo, MacBook).
- Task state reconciliation (`bob task reconcile`) validates dependencies, project blocking (`^prj`), and Pomodoro linkages.
- Ingestion pipelines (`bob gkeep pull`, `bob ref scan`) bridge external tools into Obsidian.
- Maintenance routines (`bob nightly`, `bob task archive`) archive finished work into `done/`.

Currently, whenever Bryan wants to run one of these tools outside of background timers (systemd user services and LaunchAgents), he must:
1. `Alt+Tab` or switch desktop spaces from Obsidian to a terminal / tmux window.
2. Recall the exact CLI flags (e.g. `bob task reconcile --dry-run` vs write mode).
3. Wait for execution, inspect stdout, and switch back to Obsidian.
4. Wait for Obsidian's file watcher to pick up changes.

Bringing command execution directly into Obsidian eliminates this friction, keeping Bryan in active flow.

### 2.2 System Topology & Existing Integration Patterns
Inspection of the `bob-plugins` codebase reveals that several plugins already communicate with `bob` via Node's `child_process`:
- `bob-articles`: Runs `bob articles format` via `articleSpawnBob` using `child_process.spawn`.
- `bob-project-tasks`: Runs `bob projects list --json` via `snapshotSpawnBob` using `child_process.execFile`.
- `bob-ledger-tools`: Runs `bob stats` via `bobSpawnJson`.

These integrations share established patterns:
- Setting `BOB_DIR` to `this.app.vault.adapter.basePath`.
- Setting `NO_COLOR = "1"` for machine-decoded JSON outputs.
- Resolving the binary across standard candidate paths (`~/.cargo/bin/bob`, `~/.local/bin/bob`, `/opt/homebrew/bin/bob`, `/usr/local/bin/bob`, or PATH).

However, each of these existing integrations is an internal data-fetch plumbing mechanism tied to a specific view (e.g. rendering charts or syncing article section headers). None provides a **general-purpose, user-facing command launcher** with streaming execution feedback and output visualization.

---

## 3. Critical Critique of the Proposed Plan

### 3.1 Is This a Good Idea?
**Yes, with crucial architectural refinements.**
The concept of an in-editor command launcher is proven across modern development environments (e.g. Sublime Text's Command Palette, VS Code's `Ctrl+Shift+P`, Neovim's `:Telescope`, IntelliJ's Search Everywhere). For a power user managing a Git-backed Obsidian vault with a companion CLI, having instant access to CLI commands from the keyboard is a massive productivity multiplier.

However, the specific plan outlined in the prompt contains four significant hazards that must be addressed:

---

### 3.2 Hazard 1: Overriding `:` in Vim Normal Mode
The prompt specifies: *"I would like to add a new `:` keymap to Obsidian that triggers a new bob command-mode."*

#### The Problem:
1. **Destruction of Vim Ex Command-Line Mode**:
   Bryan uses Vim mode in Obsidian (`obsidian-vimrc-support` paired with CodeMirror Vim). In Vim, `:` is not an arbitrary hotkey; it enters **Command-line (Ex) mode**.
   While Obsidian auto-saves notes (eliminating the strict necessity of `:w`) and Bryan has mapped `\\`, `\<`, and `\>` to tab management commands in `obsidian_vimrc.md`, Vim users frequently rely on:
   - Search and replace: `:s/target/replacement/g` or `:%s/.../.../`
   - Line jumps and ranges: `:120` or `:'<,'>sort`
   - Splitting/closing windows: `:sp`, `:vsp`, `:q`
   If `:` in Normal Mode unconditionally triggers an Obsidian modal, **native Ex command capability is completely blocked**.
2. **Insert Mode Hazard**:
   If the keymap is registered carelessly at the Obsidian level rather than strictly within Vim Normal Mode, typing `:` in regular Markdown text (URLs like `https://`, time stamps like `14:30`, YAML headers `key: value`, or task tags) will intercept text input and open the modal.
3. **Non-Editor Contexts**:
   Vim keymaps only function when a Markdown editor leaf has active focus. If Bryan is viewing the Reading Board, navigating the file tree, viewing a canvas, or in Reading View, pressing `:` does nothing.

#### The Critique & Solution:
Do not implement `:` as a raw, dumb modal trigger that destroys Vim Ex mode. Instead, implement a **Smart Ex Pass-Through & Dual Trigger Strategy**:
1. In `obsidian_vimrc.md`, map `:` in Normal Mode to open the Bob Command Palette:
   ```vim
   exmap bob_command_mode obcommand bob-command-mode:open
   nmap : :bob_command_mode<CR>
   ```
2. In the Command Palette modal, provide **Automatic Ex-Command Pass-Through**:
   If the user starts typing an Ex command (e.g. `s/`, `%s/`, `w`, `q`, `sort`, or any string starting with `:` or `/`), the modal detects this input, closes itself immediately, and dispatches the raw command to CodeMirror Vim's `vim.handleEx(cm, text)`.
3. Provide an explicit fallback keymap in Vim (`nmap g: :` or `nmap <leader>: :`) so that raw Ex mode is always accessible with zero ambiguity.
4. Register a global Obsidian command (`bob-command-mode:open`) and assign a global hotkey (e.g. `Cmd+Shift+B` or `<leader>b`) that functions anywhere in the vault, even when an editor is not focused.

---

### 3.3 Hazard 2: "Support Any Bob Command That Might Be Useful" (The Kitchen-Sink Trap)
The prompt notes: *"This command-mode should support any bob command that might be useful to run from Obsidian. Think hard about which commands to add support for."*

#### The Problem:
`bob` has dozens of subcommands and flags. Dumping all commands indiscriminately into a modal results in a cluttered, unnavigable mess. Furthermore, many `bob` commands fall into categories that are **fundamentally unsuitable** for a generic picker:
- **Protocol & Internal IPC**: Subcommands like `capture-parse`, `capture-rewrite`, `capture-complete`, and `capture-task-id` are low-level JSON contracts designed for Bob Mac Capture, not humans.
- **In-Vault Redundancy**: Running `bob capture "buy milk"` from inside Obsidian makes little sense when the user is already inside Obsidian with instant note editing and hotkeys.
- **Destructive Unparameterized Actions**: Commands like `bob ref rename` require source/destination parameters; executing them blindly from a single click could corrupt links or fail abruptly.

#### The Critique & Solution:
A command launcher is only as good as its curation. Commands must be strictly classified into **Actionable Categories** with first-class handling of **Parameters and Dry-Run Modes**:
- **Immediate Execution Commands**: Commands that require no arguments and should run immediately (e.g. `bob vault-sync`, `bob nightly`, `bob gkeep pull`, `bob plugins sync`).
- **Parameterized Sub-Items**: Commands that have critical execution variants (e.g. `bob task reconcile --dry-run` vs `bob task reconcile`, `bob task archive`, `bob vault-sync status`).
- **Interactive Prompts**: Commands that need a target (e.g. `bob task move`, `bob ref today`) should open a secondary picker stage rather than failing on missing CLI arguments.

---

### 3.4 Hazard 3: Notification & Output Truncation
The prompt specifies: *"When the user runs a command from this command-mode, they should be notified of its completion (on success or failure) with support for showing the full command output of the command that was run somehow."*

#### The Problem:
Obsidian's built-in `new Notice("...")` API is designed for brief, single-line alerts (e.g. "Note saved", "5 tasks archived").
- If `bob vault-sync` succeeds, the output may include fast-forward commits, branch statuses, or sync conflict warnings across multiple machines.
- If `bob nightly` runs, it executes a 4-step pipeline that produces 20-50 lines of logs.
- If a command fails (e.g. Git lock contention, merge conflict, network timeout during Google Keep auth), the failure reason is buried in `stderr`. A toast notice auto-dismisses after a few seconds, leaving the user with no record of what went wrong.

#### The Critique & Solution:
We need a **Two-Tiered Notification & Inspection System**:
1. **Tier 1 (Glance / Status Notice)**:
   - A non-intrusive toast notification appears during execution with an animated indicator: `$(spinner) Running bob vault-sync...`.
   - On completion, the toast updates:
     - On Success: `✓ bob vault-sync finished (1.4s)` with an embedded button: `[View Output]`.
     - On Failure: `✗ bob vault-sync failed (exit code 1)` with `[View Output]` (and an extended timeout of 10s or manual dismissal).
2. **Tier 2 (The Command Output Inspector Modal)**:
   - Clicking `[View Output]`, or pressing `Ctrl+O` immediately after completion, or triggering `bob:show-last-output` opens an Obsidian modal formatted like a sleek terminal output viewer.
   - It displays stdout/stderr with ANSI color rendering, execution metadata (command string, exit code, execution time, timestamp), a `[Copy to Clipboard]` button, and a `[Re-run]` button.

---

### 3.5 Hazard 4: Vault Concurrency & File Buffer Clashing
When `bob vault-sync`, `bob task reconcile`, or `bob nightly` runs, it executes outside Obsidian and rewrites Markdown files directly on the filesystem.

#### The Problem:
1. **Dirty Editor Overwrites**: If Bryan has note `projects/alpha.md` open in an active Obsidian editor with unsaved keystrokes in CodeMirror, and `bob task reconcile` modifies `projects/alpha.md` on disk, a file-system race condition occurs. Obsidian might overwrite the CLI changes on the next autosave tick, or pop an intrusive external-change conflict dialog.
2. **Lock Collisions**: `bob vault-sync` and `bob nightly` acquire the shared lock file (`BOB_VAULT_SYNC_LOCK_FILE`, `/tmp/bob_sync.lock`). If a background cron/systemd service (`bob-vault-sync.service`) is currently running, spawning a new sync from Obsidian will fail with lock contention unless handled gracefully.

#### The Critique & Solution:
1. **Pre-Execution Flush**: Before launching any mutating command, the plugin must explicitly flush active editor buffers:
   ```javascript
   const activeView = this.app.workspace.getActiveViewOfType(MarkdownView);
   if (activeView?.editor) {
     await activeView.save();
   }
   ```
2. **Lock Awareness**: The plugin should check if `/tmp/bob_sync.lock` is held. If so, it displays a polite notice (`"Vault sync already in progress by background service; waiting..."`) rather than abruptly crashing.
3. **Post-Execution File Watcher Debounce**: After CLI execution completes, give Obsidian's internal filesystem cache a 100ms window to settle before clearing any pending UI indicators.

---

## 4. Comprehensive Bob Command Catalog & Taxonomy

Below is the definitive catalog of `bob` commands, analyzed and classified for inclusion in the in-Obsidian command mode.

```
                    ┌──────────────────────────────────────────────┐
                    │          Bob In-Obsidian Command Mode         │
                    └──────────────────────┬───────────────────────┘
                                           │
         ┌─────────────────────────────────┼─────────────────────────────────┐
         │                                 │                                 │
         ▼                                 ▼                                 ▼
┌──────────────────┐             ┌──────────────────┐             ┌──────────────────┐
│  Tier 1: Core Ops│             │  Tier 2: Ingest  │             │ Tier 3: Inspect  │
│  (Vault & Git)   │             │   & Sync Tools   │             │   & Dashboards   │
├──────────────────┤             ├──────────────────┤             ├──────────────────┤
│ vault-sync (run) │             │ gkeep pull       │             │ stats (glance)   │
│ vault-sync status│             │ gkeep list       │             │ plan (budget)    │
│ nightly (full)   │             │ plugins sync     │             │ ready (caps)     │
│ task reconcile   │             │ plugins list     │             │ freshness (walk) │
│ task archive     │             │ projects sync    │             │ ref list         │
│ task reroll      │             │ ref sync / scan  │             │ projects list    │
└──────────────────┘             └──────────────────┘             └──────────────────┘
```

### 4.1 Tier 1: Core Vault & Git Operations (The Essential Daily Drivers)
These are commands Bryan runs multiple times a day or at session end. They must be prominently featured at the top of the palette.

| Command ID | Display Label | CLI Invocation | Safety / Mutating | Description & Behavior |
| :--- | :--- | :--- | :--- | :--- |
| `vault-sync` | **Vault: Git Sync** | `bob vault-sync` | Mutating (Git/Vault) | Runs lock-protected Git reconcile cycle (pull, commit, push, fast-forward). |
| `vault-sync-status` | **Vault: Git Sync Status** | `bob vault-sync status` | Read-Only | Checks whether local vault is dirty or ahead/behind remote without writing. |
| `nightly` | **Vault: Nightly Maintenance** | `bob nightly` | Heavy Mutating | Full 4-step pipeline: `vault-sync` → `task archive` → `articles` check → `vault-sync`. |
| `task-reconcile-dry`| **Tasks: Reconcile (Dry Run)** | `bob task reconcile --dry-run` | Read-Only | Previews task status changes based on Pomodoro ledger and dependencies. |
| `task-reconcile` | **Tasks: Reconcile Statuses**| `bob task reconcile` | Mutating (Tasks) | Reconciles task checkboxes across the vault to Next, In Progress, or Blocked. |
| `task-archive` | **Tasks: Archive Done/Canceled**| `bob task archive` | Mutating (Tasks) | Moves completed and canceled tasks into `done/` archives and updates links. |
| `task-reroll` | **Tasks: Reroll Due Priorities**| `bob task reroll` | Mutating (Tasks) | Re-rolls due prioritized tasks within their priority windows. |

### 4.2 Tier 2: Vault Ingestion & Plugin Deployment
Commands that sync external services into the vault or manage custom plugin code.

| Command ID | Display Label | CLI Invocation | Safety / Mutating | Description & Behavior |
| :--- | :--- | :--- | :--- | :--- |
| `gkeep-pull` | **Google Keep: Drain Inbox** | `bob gkeep pull` | Mutating (Keep/Vault)| Imports Keep notes into `gkeep_inbox.md` and archives them in Google Keep. |
| `gkeep-pull-dry` | **Google Keep: Preview Drain** | `bob gkeep pull -d` | Read-Only | Previews Markdown that would be imported without modifying Keep or vault. |
| `plugins-sync` | **Plugins: Deploy From Repo** | `bob plugins sync` | Mutating (Plugins)| Deploys compiled plugin files from `bob-plugins` into `~/bob/.obsidian/plugins/`. |
| `plugins-list` | **Plugins: Check Sync Status**| `bob plugins list` | Read-Only | Compares plugin repo versions against installed vault copies. |
| `projects-sync` | **Projects: Sync Schedules** | `bob projects sync` | Mutating (Projects)| Syncs project status, task schedules, and subprojects from `^prj` tasks. |
| `ref-scan` | **References: Scan Highlights**| `bob ref scan` | Mutating (Refs) | Scans Highlights library and syncs PDF markers into reference notes. |

### 4.3 Tier 3: Inspection, Dashboards & Queries (Read-Only Views)
Commands that generate formatted reports or summaries. These output directly into the Output Inspector Modal.

| Command ID | Display Label | CLI Invocation | Safety / Mutating | Description & Behavior |
| :--- | :--- | :--- | :--- | :--- |
| `stats-glance` | **Stats: Daily Metrics Glance**| `bob stats` | Read-Only | Prints today's Pomodoro counts, task completions, and streak metrics. |
| `plan-budget` | **Plan: Today's Budget & Lanes**| `bob plan` | Read-Only | Displays today's planned budget, active tasks, and NEXT/PENDING lanes. |
| `ready-caps` | **Ready: Note Caps & Lanes** | `bob ready` | Read-Only | Shows Ready lane counts against per-note caps across all active notes. |
| `freshness-queue` | **Freshness: Review Queue** | `bob freshness` | Read-Only | Lists tasks currently due for review across the tiered review walk. |
| `ref-list-queue` | **References: Reading Queue** | `bob ref list` | Read-Only | Displays active references by reading state (queued, reading, finished). |

### 4.4 Explicitly Excluded Commands & Technical Rationale

| Excluded Command | CLI Invocation | Rationale for Exclusion from Obsidian Command Mode |
| :--- | :--- | :--- |
| `capture` | `bob capture ...` | Redundant. Inside Obsidian, users can type directly or use native hotkeys; outside, Bob Mac Capture is already bound to global system hotkeys. |
| `pomodoro` | `bob pomodoro ...` | Handled natively by `bob-ledger-tools` and daily notes. The CLI command is primarily for tmux status bars. |
| `articles format` | `bob articles ...` | Already implemented natively inside Obsidian via the `bob-articles` plugin (`bob-articles:format-article-numbers`). |
| `completion` | `bob completion` | Pure shell setup utility; zero utility inside an Obsidian editor. |
| Capture Protocol | `bob capture-parse`, etc. | Low-level JSON endpoints powering Bob Mac Capture. Human execution makes no sense. |
| `ref rename` | `bob ref rename <ref> <name>`| Requires multiple string arguments. Best executed from terminal or dedicated renaming modal, not a single-click command palette. |

---

## 5. Keymap & Trigger Architecture

### 5.1 Evaluating Keymap Mechanisms

We evaluated four possible mechanisms for wiring `:` into Obsidian:

| Approach | Description | Ergonomics | Vim Safety | Implementation Complexity | Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Option 1: Raw Global Hotkey `:`** | Register `:` in Obsidian Hotkeys settings | Poor | Broken (Breaks typing colons in notes) | Trivial | **Rejected**: Catastrophic failure for text editing. |
| **Option 2: Direct Ex Command `:bob`** | Define `:bob <cmd>` via `obsidian-vimrc-support` | Moderate | 100% Safe (Native Ex syntax) | Low | **Viable secondary**: Great for terminal purists, but lacks fuzzy modal UI. |
| **Option 3: Leader Key (`<Space>b`)** | Map `<Space>b` or `<leader>b` in Normal Mode | High | 100% Safe (Zero Ex conflict) | Low | **Solid Alternative**: Very clean, but deviates from user's explicit `:` request. |
| **Option 4: Normal Mode `nmap :` with Ex Pass-Through** | Map `:` in Normal Mode to modal, with auto-fallback to Ex engine | **Exceptional** | **High** (Preserves Ex commands via smart sniffing) | Moderate | **RECOMMENDED**: Fully satisfies user's `:` desire while protecting Ex mode. |

### 5.2 The Recommended Trigger Specification: Smart Ex Pass-Through

#### 1. Normal Mode Mapping (`obsidian_vimrc.md`)
In `~/bob/obsidian_vimrc.md`, register the Ex mapping:
```vim
" Bob Command Mode: Launch the Bob Command Palette
exmap bob_command_mode obcommand bob-command-mode:open
nmap : :bob_command_mode<CR>

" Escape hatch: g: always opens native Vim Ex mode
nmap g: :
```

#### 2. The Smart Ex-Sniffing Logic
Inside the Command Palette's input handler:
```typescript
class BobCommandPaletteModal extends FilteredPickerModal {
  // When the user presses Enter on the input:
  handleKeydown(event: KeyboardEvent) {
    const rawQuery = this.getRawQuery();

    // Check if input begins with Vim Ex commands (e.g. :s/old/new/, :w, :q, :%s)
    if (this.isVimExCommand(rawQuery)) {
      event.preventDefault();
      event.stopPropagation();
      this.close();
      this.dispatchToVimEx(rawQuery);
      return;
    }

    super.handleKeydown(event);
  }

  isVimExCommand(query: string): boolean {
    const trimmed = query.startsWith(":") ? query.slice(1).trim() : query.trim();
    // Regex matching standard Ex commands: substitution (s/...), save (w), quit (q), etc.
    return /^([%0-9,.'<>]*)s[\/#]|^(w|q|wq|x|sort|vimgrep)\b/.test(trimmed);
  }

  dispatchToVimEx(query: string) {
    const activeView = this.app.workspace.getActiveViewOfType(MarkdownView);
    const cm = this.plugin.resolveVimCodeMirror(activeView?.editor);
    const vim = this.plugin.getVimAdapter();
    if (cm && vim && typeof vim.handleEx === "function") {
      const exCommand = query.startsWith(":") ? query.slice(1) : query;
      vim.handleEx(cm, exCommand);
    }
  }
}
```

#### 3. Global Hotkey for Non-Editor Views
Register `bob-command-mode:open` in Obsidian's command registry. Users can assign an Obsidian hotkey (e.g. `Cmd+Shift+B` or `Ctrl+Alt+B`) so the command palette can be opened even when CodeMirror is not focused.

---

## 6. UI / UX Design: Intuitive, Reliable, and Beautiful

To match the exceptional visual standards of Bryan's vault (seen in `bob-navigation-hotkeys` and `bob-ledger-tools`), the interface is built strictly on **Obsidian CSS variables** and reuses the established `bob-cnp-*` modal architecture.

### 6.1 Component 1: The Bob Command Palette Modal
Subclassed from `FilteredPickerModal`, this modal offers instant fuzzy filtering, category badges, execution safety chips, and keyboard shortcuts.

#### Visual Layout (ASCII Mockup)
```
┌─────────────────────────────────────────────────────────────────────────────┐
│ ⚡ Bob Commands                                                 [12 commands]│
│ Type to search · <Tab> toggle Dry-Run · <Shift+Enter> preview · <Esc> exit │
├─────────────────────────────────────────────────────────────────────────────┤
│ 🔍 sync                                                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│  [Sync]      Vault: Git Sync                       ⚡ Mutating         ↵ Run│
│              bob vault-sync · Reconcile vault with Git remote               │
│                                                                             │
│  [Sync]      Vault: Git Sync Status                🛡️ Read-Only         ↵ Run│
│              bob vault-sync status · Check local vs remote status           │
│                                                                             │
│  [Plugins]   Plugins: Deploy From Repo             ⚡ Mutating         ↵ Run│
│              bob plugins sync · Deploy compiled plugins to vault            │
│                                                                             │
│  [Projects]  Projects: Sync Schedules              ⚡ Mutating         ↵ Run│
│              bob projects sync · Propagate dates and subprojects            │
├─────────────────────────────────────────────────────────────────────────────┤
│ <Enter> Run   <Shift+Enter> Dry-Run   <Ctrl+N/P> Navigate   <Esc> Cancel    │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Visual Details & Styling
- **Header Icon**: Lucide `terminal` or `zap` icon with accent hue.
- **Search Bar**: Centered input with clear placeholder (`"Search bob commands (e.g. sync, task, gkeep)..."`).
- **Row Anatomy**:
  - **Category Badge**: Pill tag with subtle background (`[Sync]`, `[Tasks]`, `[Ingest]`, `[Inspect]`).
  - **Command Title**: Bold primary label (`Vault: Git Sync`).
  - **Safety Chip**: Color-coded badge (`🛡️ Read-Only` in muted blue; `⚡ Mutating` in warm amber; `🔥 Destructive` in red).
  - **Subtitle**: Monospace CLI invocation + short explanation (`bob vault-sync · Reconcile vault with Git remote`).
  - **Action Hint**: Lucide `corner-down-left` icon on the active row.

---

### 6.2 Component 2: Execution Status & Notice Toasts

Execution is completely non-blocking. When a command is selected:
1. **Modal Closes Instantly**: The UI never hangs or freezes.
2. **Active Status Notice**:
   ```
   ┌────────────────────────────────────────────────────────────┐
   │ ⏳ Running `bob vault-sync`...                             │
   └────────────────────────────────────────────────────────────┘
   ```
3. **Completion Notice with Action Button**:
   - **On Success**:
     ```
     ┌────────────────────────────────────────────────────────────┐
     │ ✓ `bob vault-sync` completed (1.4s)        [ View Output ] │
     └────────────────────────────────────────────────────────────┘
     ```
     *(Duration: 4000ms. Clicking `[ View Output ]` opens the Inspector.)*
   - **On Failure**:
     ```
     ┌────────────────────────────────────────────────────────────┐
     │ ✗ `bob vault-sync` failed (exit code 1)    [ View Output ] │
     └────────────────────────────────────────────────────────────┘
     ```
     *(Duration: 12000ms. Highlighted in error red. Clicking opens error logs.)*

---

### 6.3 Component 3: The Command Output Inspector Modal (`BobOutputModal`)

When a user clicks `[ View Output ]`, presses `Ctrl+O`, or runs `bob:show-last-output`, this modal opens:

#### Visual Layout (ASCII Mockup)
```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 💻 Bob Output: bob vault-sync                                               │
│ Status: ✓ Success (0)  ·  Duration: 1.42s  ·  Executed: Today at 08:35:12   │
├─────────────────────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ [vault-sync] Acquiring shared lock: /tmp/bob_sync.lock                  │ │
│ │ [vault-sync] Checking remote origin/master...                           │ │
│ │ [vault-sync] Fast-forwarding 2 commits from origin/master               │ │
│ │              Updating 4a12fbc..9b88c12                                  │ │
│ │              Fast-forward                                               │ │
│ │              daily/2026-10-26.md | 4 +++-                               │ │
│ │              projects/bob-cli.md | 2 +-                                 │ │
│ │ [vault-sync] Git working tree clean; sync completed successfully.       │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────────────────┤
│ [ 📋 Copy Output ]     [ 🔄 Re-run Command ]                    [ Close ] │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Inspector Features:
- **Terminal Styling**: Monospace typography (`var(--font-monospace)`), dark theme background (`var(--background-secondary)`), subtle rounded border.
- **ANSI Color Support**: Clean styling using standard ANSI escape sequence translation into CSS classes (e.g. green for additions, red for deletions/errors).
- **Action Controls**:
  - `[ 📋 Copy Output ]`: Copies raw stdout/stderr to clipboard with feedback Notice.
  - `[ 🔄 Re-run Command ]`: Re-executes the exact command immediately.
  - `[ Close ]` / `Esc`: Dismisses modal.

---

## 7. Technical Implementation & Architecture

### 7.1 Plugin Location: Standalone vs Existing Monorepo Plugin
We analyzed two potential homes for this code within `bob-plugins`:

| Option | Pros | Cons | Recommendation |
| :--- | :--- | :--- | :--- |
| **Integrate into `bob-navigation-hotkeys`** | • Direct access to `FilteredPickerModal`<br>• Direct access to Vim adapter and CM6 hooks<br>• Zero new plugin installation overhead | • Plugin is already very large (83k lines)<br>• Dilutes navigation/task-card scope | **Viable secondary choice** |
| **New Standalone Plugin: `bob-command-mode`** | • Clean modular boundaries<br>• Isolated test suite and build fragments<br>• Dedicated settings & output state<br>• Can export an API | • Minor boilerplate for new plugin manifest | **STRONGLY RECOMMENDED** |

**Recommendation**: Create a new plugin in `bob-plugins/plugins/bob-command-mode/`. Reuse the shared `FilteredPickerModal` and `bobSpawn` patterns from `bob-navigation-hotkeys` and `bob-ledger-tools`.

---

### 7.2 The Process Spawning Engine (`bobRunner.ts`)

```typescript
import { ChildProcess, execFile, spawn } from "node:child_process";
import * as path from "node:path";
import * as fs from "node:fs";

export interface BobRunResult {
  ok: boolean;
  command: string;
  args: string[];
  code: number | null;
  stdout: string;
  stderr: string;
  durationMs: number;
  timestamp: Date;
  error?: string;
}

export class BobRunner {
  private activeProcess: ChildProcess | null = null;
  private lastResult: BobRunResult | null = null;

  resolveBobBinary(): string {
    const home = process.env.HOME || "";
    const candidates = [
      `${home}/.cargo/bin/bob`,
      `${home}/.local/bin/bob`,
      "/opt/homebrew/bin/bob",
      "/usr/local/bin/bob",
    ];
    for (const cand of candidates) {
      if (fs.existsSync(cand)) return cand;
    }
    return "bob";
  }

  async run(args: string[], vaultPath: string): Promise<BobRunResult> {
    if (this.activeProcess) {
      throw new Error("Another bob command is currently running.");
    }

    const binary = this.resolveBobBinary();
    const startTime = Date.now();
    const env = {
      ...process.env,
      BOB_DIR: vaultPath,
      NO_COLOR: "1", // Or omit if ANSI viewer is enabled
    };

    return new Promise((resolve) => {
      let stdout = "";
      let stderr = "";

      const child = spawn(binary, args, {
        env,
        stdio: ["ignore", "pipe", "pipe"],
      });
      this.activeProcess = child;

      child.stdout.on("data", (chunk) => { stdout += chunk.toString(); });
      child.stderr.on("data", (chunk) => { stderr += chunk.toString(); });

      child.on("close", (code) => {
        const durationMs = Date.now() - startTime;
        this.activeProcess = null;
        const result: BobRunResult = {
          ok: code === 0,
          command: `bob ${args.join(" ")}`,
          args,
          code,
          stdout,
          stderr,
          durationMs,
          timestamp: new Date(),
        };
        this.lastResult = result;
        resolve(result);
      });

      child.on("error", (err) => {
        this.activeProcess = null;
        const durationMs = Date.now() - startTime;
        const result: BobRunResult = {
          ok: false,
          command: `bob ${args.join(" ")}`,
          args,
          code: null,
          stdout,
          stderr,
          durationMs,
          timestamp: new Date(),
          error: err.message,
        };
        this.lastResult = result;
        resolve(result);
      });
    });
  }

  getLastResult(): BobRunResult | null {
    return this.lastResult;
  }

  isRunning(): boolean {
    return this.activeProcess !== null;
  }
}
```

---

### 7.3 Vault Coordination & State Management
Before launching mutating commands, coordinate with Obsidian:
1. **Save Buffers**: Call `await this.app.workspace.getActiveViewOfType(MarkdownView)?.save()`.
2. **Lock Collision Detection**: Read `/tmp/bob_sync.lock`. If locked, notify user immediately:
   `"Notice: Shared lock is currently held by background sync. Command may wait or fail."`
3. **History Ring Buffer**: Maintain an in-memory history of the last 10 executed commands (`BobCommandHistory`) so Bryan can review prior runs or compare timing.

---

## 8. Implementation Roadmap

### Phase 1: Core Engine & Test Harness (`bob-command-mode`)
1. Create plugin directory `plugins/bob-command-mode/` in `bob-plugins`.
2. Create `src/fragments.json` with modular fragment architecture.
3. Implement `BobRunner` with unit test suite in `scripts/test-command-mode-runner.cjs` mocking `child_process`.
4. Implement buffer flush and lock detection.

### Phase 2: Command Registry & Palette UI
1. Define the curated `BOB_COMMAND_REGISTRY` with categories, safety chips, and CLI arguments.
2. Port and adapt `FilteredPickerModal` into `BobCommandPaletteModal`.
3. Implement fuzzy filtering across labels, descriptions, and categories (`sync:`, `tasks:`).
4. Add keyboard shortcuts (`Shift+Enter` for dry-run toggle).

### Phase 3: Notification & Output Inspector
1. Implement interactive `Notice` handler with embedded `[View Output]` button.
2. Build `BobOutputModal` with ANSI formatting, copy button, and re-run trigger.
3. Register Obsidian command `bob-command-mode:show-last-output` (hotkey: `Ctrl+O`).

### Phase 4: Keymap Integration & VimRC
1. Expose `bob-command-mode:open` in Obsidian's command palette.
2. Update `obsidian_vimrc.md`:
   ```vim
   exmap bob_command_mode obcommand bob-command-mode:open
   nmap : :bob_command_mode<CR>
   nmap g: :
   ```
3. Test Smart Ex pass-through with `:w`, `:q`, and `:s/foo/bar/g`.

### Phase 5: Vault Deployment & Sync
1. Run `npm run build` and `npm run validate` in `bob-plugins`.
2. Run `bob plugins sync` to deploy `bob-command-mode` to `~/bob/.obsidian/plugins/`.
3. Enable `bob-command-mode` in `~/bob/.obsidian/community-plugins.json`.

---

## 9. Adjustments to Requirements & Open Decisions for Bryan

### Recommended Requirement Adjustments
1. **Preserve Vim Ex Mode with Smart Pass-Through**: Do not unconditionally blind-map `:`. Implement input sniffing so standard Ex commands (`:s/...`, `:w`, etc.) route directly to Vim.
2. **Curated Taxonomy Over Raw Kitchen Sink**: Exclude low-level protocol commands (`capture-parse`) and redundant in-editor commands (`capture`); emphasize high-value operations (`vault-sync`, `nightly`, `task reconcile`, `gkeep pull`).
3. **Two-Tiered Output Model**: Replace simple Notice alerts with an interactive toast + dedicated terminal Output Inspector Modal.
4. **Pre-Execution Buffer Save**: Guarantee that active Obsidian buffers are flushed to disk before any mutating CLI command is executed.

### Open Decisions for Bryan
1. **Plugin Packaging**: Standalone plugin (`bob-command-mode`) vs. module inside `bob-navigation-hotkeys`? *(Researcher recommendation: Standalone plugin for clean boundaries and fast iteration).*
2. **Keymap Preference**: Are you comfortable with `nmap :` using the smart Ex pass-through (with `g:` as fallback), or would you prefer a dedicated leader key like `<Space><Space>` or `<leader>b` to leave native `:` 100% untouched?
3. **ANSI Styling**: Do you prefer colored ANSI terminal output inside the Output Inspector, or strict plain-text stripping (`NO_COLOR=1`)? *(Researcher recommendation: Colored ANSI rendering via lightweight CSS classes).*

---
*End of Report by Researcher `gem`.*
