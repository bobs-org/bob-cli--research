# bob CLI Subcommand Reorganization and Domain Grouping

- **Research date:** 2026-10-04
- **Researcher:** `research.06.gem`
- **Question:** How should the `bob` command organize its sub-commands more effectively to make them intuitive, cohesive, and easy to understand? Specifically, does grouping under a new `bob task` sub-command make sense, what sub-commands belong together, and what architecture best balances daily terminal ergonomics against machine-to-machine plumbing?
- **Evidence:** `bob-cli` codebase (`src/runner.rs`, `src/native.rs`, `src/native/completion/`, `src/native/task_status_hooks/`, `src/native/note_ready/`, `src/native/plan_budget/`, `src/native/pomodoro.rs`), `docs/capture.md`, `docs/README.md`, `README.md`, `cli_rules.md`, linked repositories (`bob-plugins`, `chezmoi`), external callers (Bob Mac Capture, Hammerspoon, tmux, background daemons, SASE agent skills), and established CLI design patterns (Git, Docker, Cargo, GitHub CLI).

---

## In One Breath

> **Do not move core daily verbs under `bob task`. Instead, introduce a focused `bob task` namespace for lifecycle maintenance, consolidate Pomodoro utilities under `bob pomodoro`, and isolate the 10 `capture-*` plumbing endpoints from the top-level porcelain help.**
>
> 1. **Critique of the `bob task` idea:** In Bob, *tasks are the primary domain currency*. Grouping high-frequency daily commands (`plan`, `ready`, `freshness`, `randomize`, `capture`) under `bob task` creates the **"Domain Currency Fallacy"**—it forces an unnecessary typing tax (`bob task plan`) on the commands run multiple times an hour, blurs the Pomodoro-budget nature of `bob plan`, and creates deeply awkward triple-nesting like `bob task freshness list`.
> 2. **Where `bob task` DOES work:** Creating a targeted `bob task` sub-command for task maintenance and reconciliation (`bob task sync` replacing `task-status-hooks`, and `bob task archive` replacing `move-done-tasks`) eliminates clunky, ad-hoc hyphenated names and gives task lifecycle actions a coherent home.
> 3. **The Elephant in the Room (The 10 Capture Endpoints):** Out of Bob's 28 sub-commands, **11 start with `capture`** (39% of the CLI). Ten of these (`capture-parse`, `capture-complete`, `capture-targets`, `capture-tasks`, etc.) are *pure machine plumbing* for the Bob Mac Capture menu-bar frontend. They clutter top-level `--help` and dwarf user commands.
> 4. **The Pomodoro Consolidation:** Top-level `tmux-pomodoro` and `notify` naturally belong as sub-commands of `bob pomodoro` (`bob pomodoro tmux` and `bob pomodoro notify`), uniting timer status and display under a single entity.
> 5. **Zero-Breakage Guarantee:** Every renamed or restructured command MUST retain a top-level compatibility alias (following Bob's existing precedent with `mark-next-tasks` and `task-status-setter`). External consumers—Bob Mac Capture Swift IPC, tmux status bars, Hammerspoon keybindings, and cron jobs—must experience zero disruption.

---

## 1. Full Inventory of Current Subcommands (The 28 Commands)

The `bob` binary currently exports **28 sub-commands** (27 declared in `SUBCOMMANDS` plus `help`, alongside 2 hidden compatibility aliases `mark-next-tasks` and `task-status-setter`).

Below is an exhaustive classification of every sub-command by purpose, caller persona, and design tier:

| Subcommand | Primary Role | Target Audience / Caller | Tier | Architectural Pain Point |
| :--- | :--- | :--- | :--- | :--- |
| `capture` | Capture text, tasks, bullets, or Pomodoro operators | Human CLI, Bob Mac Capture | **Porcelain** | Core entry point; must accept free-form prose. |
| `capture-complete` | Complete markers/wikilinks at cursor | Bob Mac Capture Swift frontend | **Plumbing** | Machine RPC; clutters human help. |
| `capture-parse` | Preview semantics and AST of in-progress capture | Bob Mac Capture Swift frontend | **Plumbing** | Machine RPC; clutters human help. |
| `capture-pomodoro-name`| Name an unnamed Pomodoro in daily note | Bob Mac Capture Swift frontend | **Plumbing** | Machine RPC; clutters human help. |
| `capture-pomodoros` | List today's Pomodoro ledger picker entries | Bob Mac Capture Swift frontend | **Plumbing** | Machine RPC; clutters human help. |
| `capture-rewrite` | Apply draft rewrites (bare `@@` absorption) | Bob Mac Capture Swift frontend | **Plumbing** | Machine RPC; clutters human help. |
| `capture-sections` | List non-Tasks headings for route | Bob Mac Capture Swift frontend | **Plumbing** | Machine RPC; clutters human help. |
| `capture-targets` | List routable note targets | Bob Mac Capture Swift frontend | **Plumbing** | Machine RPC; clutters human help. |
| `capture-task-id` | Assign block ID to open capture task | Bob Mac Capture Swift frontend | **Plumbing** | Machine RPC; clutters human help. |
| `capture-task-sections`| List ALL-CAPS child sections of parent task | Bob Mac Capture Swift frontend | **Plumbing** | Machine RPC; clutters human help. |
| `capture-tasks` | List open tasks in routed note | Bob Mac Capture Swift frontend | **Plumbing** | Machine RPC; clutters human help. |
| `completion` | Install/inspect shell completion | Human CLI, `just install` | **Porcelain** | Already has subcommands (`install`, `status`). |
| `freshness` | Walk tiered freshness review queue; seed cutover | Human CLI (morning review) | **Porcelain** | Already has subcommands (`list`, `seed`). |
| `gkeep` | Drain Google Keep inbox into Obsidian | Human CLI, automated sync | **Porcelain** | Already structured (`doctor`, `list`, `login`, `pull`). |
| `highlights` | Sync Highlights PDF annotations to reference notes | Human CLI, SASE agent, daemon | **Porcelain** | Already structured (`clip`, `create`, `scan`, `sync`). |
| `move-done-tasks` | Archive completed/canceled tasks to `done/` | `bob nightly`, background cron | **Maintenance** | Awkward hyphenated verb; no domain noun. |
| `nightly` | Run full vault maintenance & git sync sequence | Cron / systemd scheduler | **Maintenance** | Top-level macro runner; orchestrates 3 steps. |
| `notify` | Notify when current Pomodoro completes | Pomodoro scripts / timers | **Plumbing/Utility**| Disconnected from `pomodoro`. |
| `plan` | Show daily Pomodoro budget & active task lanes | Human CLI (hourly planning) | **Porcelain** | High-frequency daily command; multi-domain. |
| `plugins` | Manage & deploy custom Bob Obsidian plugins | Human CLI, agents, deploy | **Porcelain** | Already structured (`list`, `sync`). |
| `pomodoro` | Print current Pomodoro status | Human CLI, Hammerspoon | **Porcelain** | Core timer inspection; disconnected from `tmux`. |
| `projects` | Inspect & sync project note `^prj` tasks | Human CLI, agents | **Porcelain** | Already structured (`list`, `sync`). |
| `query` | Run Dataview / Tasks queries headless | Human CLI, agent skills | **Porcelain** | High-level read-only query engine. |
| `randomize` | Re-roll due prioritized tasks within windows | Human CLI (review) | **Porcelain** | Single-purpose review action. |
| `ready` | Show area/project notes against per-note cap | Human CLI (daily review) | **Porcelain** | High-frequency daily command. |
| `task-status-hooks` | Reconcile Pomodoro links, statuses, Blocked | Git hooks, `bob nightly`, CLI | **Maintenance** | Clunky hyphenated name; historical artifact. |
| `tmux-pomodoro` | Formatted Pomodoro status for tmux bar | `tmux.conf` status line daemon | **Plumbing/Utility**| Hyphenated sibling of `pomodoro`. |
| `vault-sync` | Reconcile Bob vault through Git | Daemon, `bob nightly`, CLI | **Maintenance** | Hyphenated; standalone git wrapper. |

---

## 2. Critique of the Four Existing CLI Anachronisms

Looking across the 28 sub-commands reveals four distinct structural anomalies:

### 2.1 Anomaly 1: The Capture Protocol Explosion (39% of the CLI)
When `bob --help` is executed today, the first 11 lines are all capture commands:
```text
Commands:
  capture                Capture a task or bullet into the Bob vault
  capture-complete       Complete the capture marker at the cursor
  capture-parse          Explain what in-progress capture text currently means
  capture-pomodoro-name  Assign a name to an open unnamed Pomodoro
  capture-pomodoros      List today's Pomodoro ledger entries
  capture-rewrite        Apply the capture grammar's automatic draft rewrites
  capture-sections       List the non-Tasks sections of a capture note
  capture-targets        List capture routes for inbox, area, and active project notes
  capture-task-id        Assign a block ID to an open capture task
  capture-task-sections  List the ALL-CAPS child sections of a capture task
  capture-tasks          List the open tasks of a capture note
```
A human user looking for how to capture a thought sees 11 commands, 10 of which require specialized JSON payloads, cursor offsets, and format flags meant exclusively for Bob Mac Capture (e.g. `bob capture-complete --cursor 1 --format json -- '@'`). 

Interestingly, the codebase **already recognizes this duality**! In `src/runner.rs`, lines 36–40:
```rust
pub(crate) enum CompletionTier {
    Porcelain,
    Plumbing,
}
```
And in `src/native/completion/present.rs`, line 395:
```rust
// Rule 4: SUBCOMMANDS order; rule 6: porcelain first under
// `commands`, the ten frontend endpoints under
// `capture protocol` last.
for tier in [CompletionTier::Porcelain, CompletionTier::Plumbing] {
    let group = if tier == CompletionTier::Porcelain {
        "commands"
    } else {
        "capture protocol"
    };
```
The completion engine already isolates these 10 commands into a separate completion group called `"capture protocol"`! However, because `SUBCOMMANDS` was passed directly into `clap`, `bob --help` renders them flat and alphabetical, obscuring the actual user commands.

### 2.2 Anomaly 2: Noun-Verb Asymmetry
Bob already has several beautifully designed noun-verb commands:
- `bob projects list`, `bob projects sync`
- `bob plugins list`, `bob plugins sync`
- `bob gkeep list`, `bob gkeep pull`, `bob gkeep doctor`, `bob gkeep login`
- `bob highlights scan`, `bob highlights sync`, `bob highlights create`, `bob highlights clip`
- `bob freshness list`, `bob freshness seed`

Yet, sitting alongside these clean nouns are archaic, hyphenated command strings:
- `bob task-status-hooks` (instead of `bob task sync` or `bob task hooks`)
- `bob move-done-tasks` (instead of `bob task archive` or `bob vault archive`)
- `bob tmux-pomodoro` (instead of `bob pomodoro tmux`)
- `bob vault-sync` (instead of `bob vault sync`)

### 2.3 Anomaly 3: The Pomodoro Triad Disconnect
Tracking the Pomodoro ledger is one of Bob's primary jobs. But Pomodoro features are scattered across three top-level names:
- `bob pomodoro`: Human-readable status (e.g. `🍅 12/25m [Task]`).
- `bob tmux-pomodoro`: Formatted snippet for tmux with plan-budget integration.
- `bob notify`: Desktop notification triggered on Pomodoro completion.

There is no conceptual reason for `tmux-pomodoro` and `notify` to be detached top-level siblings when they are specialized output modes of the Pomodoro subsystem.

### 2.4 Anomaly 4: Inconsistent Maintenance Command Placement
`bob nightly` orchestrates `vault-sync` -> `move-done-tasks` -> `vault-sync`.
Meanwhile, `task-status-hooks` is triggered by git hooks or manual reconciliation.
These commands form a clear "Vault & Task Maintenance" cluster, but currently wander as isolated top-level commands.

---

## 3. In-Depth Critique of the `bob task` Proposal

The user asks:
> *"For example, maybe we should consider grouping some of bob's current sub-commands under a new `bob task` sub-command? Is this a good idea? Would you take a different approach?"*

Let us evaluate this idea with rigor.

### 3.1 The "Domain Currency Fallacy" (Why Maximalist Grouping Fails)
If we were to pursue an aggressive grouping strategy where "everything touching a task" moves under `bob task`, what would that look like?
- `bob task plan` (instead of `bob plan`)
- `bob task ready` (instead of `bob ready`)
- `bob task freshness` (instead of `bob freshness`)
- `bob task randomize` (instead of `bob randomize`)
- `bob task capture` (instead of `bob capture`)
- `bob task sync` (instead of `bob task-status-hooks`)
- `bob task archive` (instead of `bob move-done-tasks`)

#### Why this is a major architectural mistake:
1. **The Domain Currency Problem:**
   In a specialized tool for GTD vault management, *Tasks* are not a secondary feature or optional plugin; they are the fundamental domain currency of the entire application. Grouping them under `task` is the equivalent of:
   - Git requiring `git git commit` or `git repo commit`.
   - Cargo requiring `cargo crate build` or `cargo package build`.
   - Kubectl requiring `kubectl resource get pods`.
   When an entity represents the primary object of the system, operations on that entity should be **top-level verbs**.
2. **Daily Terminal Ergonomics:**
   Bryan uses `bob plan`, `bob ready`, and `bob freshness` multiple times throughout the workday.
   Typing `bob task plan` instead of `bob plan` adds 5 keystrokes and a space to the highest-frequency commands. In CLI design, the length of a command should be inversely proportional to its invocation frequency.
3. **Conceptual Misrepresentation (`bob plan`):**
   `bob plan` is NOT just a task list. It evaluates the **Pomodoro Ledger Budget** (the 16-session daily ceiling, theme caps), calculates remaining capacity, and projects Today's open Pomodoro links against NEXT and PENDING lanes. Subordinating it to `bob task plan` misrepresents its role as the vault's daily budget engine.
4. **The Triple-Nesting Trap (`bob freshness`):**
   `bob freshness` is already a noun with sub-commands (`bob freshness list`, `bob freshness seed`). Nesting it under `bob task` results in `bob task freshness list`—a triple-level command hierarchy (`prog noun subnoun verb`). Deep hierarchies are notoriously frustrating in terminal environments.
5. **Capture Ambiguity:**
   `bob capture` captures more than tasks. It captures ordinary Markdown bullets into non-Tasks sections (`@route#Notes`), sets Pomodoro timers (`=`, `=3`), adjusts running sessions (`+5`, `-`), and closes sessions with work logs (`=x`). Subordinating capture to `bob task capture` breaks the mental model of capture as a universal vault intake.

### 3.2 The Viable Scope for `bob task`
Does this mean `bob task` should be rejected completely? **No.**

A **targeted, lifecycle-focused `bob task` namespace** is highly beneficial if scoped properly to task *reconciliation and maintenance*:
- `bob task sync` (or `bob task hooks`): Replaces `task-status-hooks`. It reconciles active task statuses, propagates dependency ranks from Depends-On lines, and derives Blocked states.
- `bob task archive` (or `bob task move-done`): Replaces `move-done-tasks`. It archives completed/canceled task blocks to `done/` notes and updates block references.

#### Adding Discoverability Aliases:
To satisfy the user expectation that typing `bob task --help` should provide a comprehensive view of task operations, `bob task` can provide aliases or pointers to read-only task views:
- `bob task ready` -> delegates to `bob ready`
- `bob task freshness` -> delegates to `bob freshness`
- `bob task randomize` -> delegates to `bob randomize`

Under this design:
- Interactive, high-speed morning reviews still use `bob plan`, `bob ready`, and `bob freshness`.
- Users or agents exploring the `bob task` command tree see a cohesive suite:
  ```text
  bob task archive    Archive completed and canceled tasks to done/
  bob task sync       Reconcile active task dependencies and Pomodoro statuses
  bob task freshness  Alias for 'bob freshness': inspect review queue
  bob task ready      Alias for 'bob ready': show per-note Ready lanes
  ```

---

## 4. The Real Problem: The Capture Protocol (Plumbing vs. Porcelain)

If `bob task` only absorbs two maintenance commands, how do we clean up the rest of the 28 sub-commands?
The core issue making `bob` feel cluttered is the **10 `capture-*` commands**.

### 4.1 Why Can't We Just Make Them Subcommands of `bob capture`?
A common proposal is: *"Why not make them `bob capture complete`, `bob capture parse`, `bob capture targets`, etc.?"*

#### The Free-Text Parsing Hazard:
`bob capture` has a fundamental grammatical property: **it accepts free-form text as positional trailing arguments**:
```bash
bob capture Buy milk @groceries
bob capture Finish report and call bank
```
In `clap`, if `bob capture` is given sub-commands named `complete`, `targets`, `tasks`, or `parse`, clap matches tokens before positional arguments. If a user types:
```bash
bob capture complete the Q3 audit report
```
`clap` will match the sub-command `complete`, fail to parse `"the Q3 audit report"` as the sub-command's flags (e.g. `--cursor`), and crash with a confusing error!

Requiring users to always type `--` before capture text (`bob capture -- complete the report`) would be a catastrophic regression in human usability. Therefore: **`bob capture` must remain an argument-taking command without conflicting sub-command names.**

### 4.2 How to Handle the Capture Protocol
There are three architectural options for the 10 capture endpoints:

#### Option 1: Physical Namespace Migration (`bob protocol capture <cmd>` or `bob capture-protocol <cmd>`)
Move all 10 endpoints under a dedicated machine namespace:
- `bob capture-protocol parse`
- `bob capture-protocol complete`
- `bob capture-protocol targets`
- `bob capture-protocol tasks`
- ...

*Trade-off:* Cleanest command tree, but requires changing the subprocess invocation contract in Bob Mac Capture (`~/projects/github/bobs-org/bob-mac-capture`). While `bob-cli` can keep hidden compatibility aliases, moving them physically requires dual maintenance across both repos.

#### Option 2: Clap Presentation Grouping via `help_heading` (Recommended for immediate rollout)
Keep the command names `capture-parse`, `capture-complete`, etc., but use modern Clap features to group them in `--help` output:
- Use `.subcommand_help_heading("Plumbing / Capture Protocol")` on all 10 endpoints.
- Or use Clap's `.hide(true)` on the 10 endpoints in standard `--help`, and provide `bob --help-all` or `bob --full-help` (exactly like `sase --full-help`) to inspect plumbing.

*Trade-off:* 100% backward-compatible with Bob Mac Capture, zero risk of breakage, and instantly reduces the default `bob --help` command list from 28 commands down to 18 clean commands!

---

## 5. Other Logical Domain Clusters

Beyond `bob task` and `bob capture`, what other sub-commands belong together?

### 5.1 The Pomodoro Subsystem (`bob pomodoro`)
Today:
- `bob pomodoro`: Prints status (e.g. `🍅 25m [Task]`).
- `bob tmux-pomodoro`: Prints formatted status + plan meter for tmux.
- `bob notify`: Triggers completion notification.

**Recommended Structure:**
Make `bob pomodoro` a command that defaults to status if run bare, but accepts sub-commands:
- `bob pomodoro` (or `bob pomodoro status`): Print current Pomodoro status.
- `bob pomodoro tmux`: Print status formatted for tmux status line.
- `bob pomodoro notify`: Trigger completion notification.

*Compatibility:* Keep `bob tmux-pomodoro` and `bob notify` as hidden aliases delegating directly to `bob pomodoro tmux` and `bob pomodoro notify`.

### 5.2 Vault Synchronization (`bob vault`)
Today:
- `bob vault-sync`: Reconciles vault via Git.
- `bob nightly`: Orchestrates `vault-sync` -> `move-done-tasks` -> `vault-sync`.

**Recommended Structure:**
Introduce `bob vault`:
- `bob vault sync`: Reconciles vault via Git (replaces `vault-sync`).
- `bob vault nightly`: Alias/home for nightly maintenance (while keeping `bob nightly` as top-level porcelain).
- `bob vault doctor`: General vault health checks (future extension).

*Compatibility:* Keep `bob vault-sync` as an alias.

---

## 6. Recommended Re-Organization Plan

### 6.1 The Reorganized Hierarchy

Here is the proposed architectural organization for `bob`:

```text
bob
├── Daily Workflow (Porcelain - High Frequency)
│   ├── capture                 Capture tasks, bullets, or Pomodoro sessions
│   ├── plan                    Show daily Pomodoro budget & active task lanes
│   ├── ready                   Show per-note Ready lanes against cap
│   ├── freshness               Walk tiered freshness review queue (list, seed)
│   └── randomize               Re-roll due prioritized tasks within windows
│
├── Domain Entity Commands (Noun -> Verbs)
│   ├── pomodoro                Pomodoro timer inspection and integrations
│   │   ├── [status]            (default) Show current Pomodoro status
│   │   ├── tmux                Format Pomodoro status and plan meter for tmux
│   │   └── notify              Send desktop notification on session completion
│   ├── task                    Task lifecycle, maintenance, and reconciliation
│   │   ├── sync                Reconcile active task dependencies and statuses
│   │   ├── archive             Archive completed and canceled tasks to done/
│   │   ├── ready               (alias -> bob ready)
│   │   └── freshness           (alias -> bob freshness)
│   ├── vault                   Obsidian vault Git synchronization and health
│   │   ├── sync                Pull, commit, and push vault Git changes
│   │   └── nightly             (alias -> bob nightly) Run nightly maintenance
│   ├── projects                Inspect and sync project notes (^prj) (list, sync)
│   ├── plugins                 Manage Bob Obsidian plugins (list, sync)
│   ├── highlights              PDF annotation sync and intake (clip, create, scan, sync)
│   └── gkeep                   Google Keep inbox drain (list, pull, doctor, login)
│
├── System & Inspection
│   ├── query                   Run read-only Dataview / Tasks queries
│   ├── nightly                 Run full nightly sync and maintenance workflow
│   └── completion              Install and inspect shell completion (install, status)
│
└── Capture Protocol (Plumbing - Hidden or Grouped)
    ├── capture-complete        RPC: Complete marker/wikilink at cursor
    ├── capture-parse           RPC: Explain in-progress capture text
    ├── capture-pomodoro-name   RPC: Name an open unnamed Pomodoro
    ├── capture-pomodoros       RPC: List today's Pomodoro ledger entries
    ├── capture-rewrite         RPC: Apply automatic draft rewrites
    ├── capture-sections        RPC: List non-Tasks sections in note
    ├── capture-targets         RPC: List capture routes
    ├── capture-task-id         RPC: Assign block ID to open task
    ├── capture-task-sections   RPC: List child sections of task
    └── capture-tasks           RPC: List open tasks in note
```

---

## 7. Before-and-After Comparison

| Command Category | Current Command | Proposed Primary Command | Compatibility Alias Retained? |
| :--- | :--- | :--- | :--- |
| **Task Reconciliation** | `bob task-status-hooks` | `bob task sync` (or `bob task hooks`) | Yes (`bob task-status-hooks`) |
| **Task Archiving** | `bob move-done-tasks` | `bob task archive` | Yes (`bob move-done-tasks`) |
| **Pomodoro Status** | `bob pomodoro` | `bob pomodoro` | Yes |
| **Pomodoro Tmux** | `bob tmux-pomodoro` | `bob pomodoro tmux` | Yes (`bob tmux-pomodoro`) |
| **Pomodoro Notify** | `bob notify` | `bob pomodoro notify` | Yes (`bob notify`) |
| **Vault Git Sync** | `bob vault-sync` | `bob vault sync` | Yes (`bob vault-sync`) |
| **Nightly Run** | `bob nightly` | `bob nightly` (also `bob vault nightly`) | Yes |
| **Planning & Review** | `bob plan` | `bob plan` (unchanged) | N/A |
| **Ready Cap** | `bob ready` | `bob ready` (also `bob task ready`) | N/A |
| **Freshness Queue** | `bob freshness` | `bob freshness` (also `bob task freshness`) | N/A |
| **Backlog Randomize**| `bob randomize` | `bob randomize` (also `bob task randomize`) | N/A |
| **Capture Intake** | `bob capture` | `bob capture` (unchanged) | N/A |
| **Capture Protocol** | `bob capture-*` (10 cmds) | Grouped under `Capture Protocol` in help | Yes (Unchanged for Bob Mac Capture) |
| **Projects** | `bob projects` | `bob projects` (unchanged) | N/A |
| **Plugins** | `bob plugins` | `bob plugins` (unchanged) | N/A |
| **Highlights** | `bob highlights` | `bob highlights` (unchanged) | N/A |
| **Google Keep** | `bob gkeep` | `bob gkeep` (unchanged) | N/A |
| **Dataview Query** | `bob query` | `bob query` (unchanged) | N/A |
| **Shell Completion** | `bob completion` | `bob completion` (unchanged) | N/A |

---

## 8. Mockup: Proposed `bob --help` Output

In accordance with `sase/memory/cli_rules.md`:
- *- Make `-h|--help` output excellent: clear, complete, consistent, and easy to scan.*
- *Keep listed subcommands and options sorted alphabetically.*
- *Prefer beautiful, colored output over black-and-white output when color improves readability.*

Here is how `bob --help` would render under the recommended design (alphabetical within logical help groups):

```text
Bob — command-line tools for the Bob Obsidian vault and Pomodoro workflow.

Bob tracks a daily Pomodoro ledger inside an Obsidian vault and keeps that vault
synced through Git. Run a command with `bob <command>`; pass `--help` to a
command for its own options.

Usage: bob <COMMAND>

Daily Workflow:
  capture                Capture a task, bullet, or Pomodoro session into the vault
  freshness              Walk the tiered freshness review queue and seed cutover
  plan                   Show today's plan budget, Today's tasks, and active lanes
  randomize              Re-roll due prioritized tasks within their priority windows
  ready                  Show ready tasks per area/project note against note cap

Domain Management:
  gkeep                  Drain Google Keep inbox notes into Obsidian tasks
  highlights             Sync Highlights PDF annotations into reference notes
  plugins                Manage and deploy Bob custom Obsidian plugins
  pomodoro               Inspect Pomodoro timer status and configure integrations
  projects               Manage project notes via their ^prj tasks
  task                   Reconcile active task dependencies and archive completed tasks
  vault                  Synchronize and maintain the Bob Obsidian Git vault

Inspection & System:
  completion             Install and inspect shell completion for bob
  nightly                Run the nightly Obsidian sync and maintenance steps
  query                  Run headless Dataview and Tasks queries against the vault

Options:
  -h, --help             Print help (see a summary with '-h')
  -V, --version          Print version
      --full-help        Show all commands, including frontend capture protocol

Run 'bob <command> --help' for more information on a command.
```

Notice the dramatic improvement:
1. Instead of a 28-item wall of text where 11 items start with `capture`, the user is greeted with **14 clean, categorized commands**.
2. High-frequency daily commands (`capture`, `plan`, `ready`, `freshness`) remain immediate top-level verbs.
3. Domain nouns (`pomodoro`, `task`, `vault`, `projects`, `plugins`, `highlights`, `gkeep`) follow a consistent noun-verb interaction pattern.
4. The 10 machine-oriented `capture-*` endpoints are safely tucked into `--full-help`, remaining 100% callable by Bob Mac Capture without cluttering human interaction.

---

## 9. Ecosystem Compatibility & Implementation Architecture

### 9.1 Compatibility Matrix with External Callers

| Caller Component | Repository / Location | Invocations Used | Migration Impact & Strategy |
| :--- | :--- | :--- | :--- |
| **Bob Mac Capture** | `bob-mac-capture` | `capture`, `capture-parse`, `capture-complete`, `capture-targets`, `capture-tasks`, `capture-sections`, `capture-pomodoros`, `capture-task-id`, etc. | **Zero breakage.** Commands remain registered in `runner.rs` dispatch and `completion/tree.rs`. Bob Mac Capture continues calling `bob capture-*` without changes. |
| **Tmux Status Bar** | `chezmoi` (`~/.config/tmux/tmux.conf`) | `bob tmux-pomodoro` | **Zero breakage.** `bob tmux-pomodoro` remains as a compatibility alias delegating to `bob pomodoro tmux`. |
| **Hammerspoon** | `chezmoi` (`~/.hammerspoon/init.lua`) | `bob pomodoro` | **Zero breakage.** `bob pomodoro` continues to output standard human status. |
| **Desktop Notify** | `chezmoi` (`~/bin/executable_bob_notify`) | `bob notify` | **Zero breakage.** `bob notify` remains as an alias for `bob pomodoro notify`. |
| **Vault Watcher** | `chezmoi` (`~/bin/executable_bob_vault_sync_watch`) | `bob vault-sync -q` | **Zero breakage.** `bob vault-sync` remains as an alias for `bob vault sync`. |
| **Highlights Sync**| `chezmoi` (`sase.yml`, wrapper scripts) | `bob highlights create` | **Zero breakage.** Unchanged. |
| **Obsidian Plugins**| `bob-plugins` | `bob plugins sync`, docs refer to `task-status-hooks` | **Zero breakage.** `task-status-hooks` remains as an alias for `bob task sync`. |
| **Cron / Nightly** | System crontab / systemd | `bob nightly` | **Zero breakage.** Unchanged. |

### 9.2 Rust Implementation Details

In `bob-cli`:
1. **`src/runner.rs`**:
   - Update `delegate_subcommand` and `build_cli` to support grouped sub-commands.
   - Expand `HIDDEN_SUBCOMMAND_ALIASES` to include:
     - `task-status-hooks` -> delegates to `NativeCommand::Task(TaskSubcommand::Sync)`
     - `move-done-tasks` -> delegates to `NativeCommand::Task(TaskSubcommand::Archive)`
     - `tmux-pomodoro` -> delegates to `NativeCommand::Pomodoro(PomodoroSubcommand::Tmux)`
     - `notify` -> delegates to `NativeCommand::Pomodoro(PomodoroSubcommand::Notify)`
     - `vault-sync` -> delegates to `NativeCommand::Vault(VaultSubcommand::Sync)`
2. **`src/native/completion/tree.rs`**:
   - Mount `task` (`sync`, `archive`), `pomodoro` (`tmux`, `notify`), and `vault` (`sync`) in the completion tree.
   - The tree already supports multi-level commands (e.g. `gkeep`, `highlights`, `plugins`); adding `task` and `pomodoro` subcommands follows the exact same pattern.
3. **`src/native/completion/present.rs`**:
   - The completion presenter already sorts porcelain under `"commands"` and plumbing under `"capture protocol"`. This structure is retained and enhanced.

---

## 10. Conclusion and Actionable Recommendations

### 10.1 Summary of Answers to User Questions

1. **Is grouping sub-commands under a new `bob task` sub-command a good idea?**
   - **Partially yes, but strictly for lifecycle maintenance.**
   - Do **NOT** move `bob plan`, `bob ready`, `bob freshness`, or `bob capture` under `bob task`. Doing so commits the Domain Currency Fallacy and degrades daily terminal ergonomics.
   - **DO** create `bob task` to absorb `task-status-hooks` (as `bob task sync`) and `move-done-tasks` (as `bob task archive`).

2. **Which other sub-commands deserve to be grouped together?**
   - **Pomodoro Cluster:** Group `tmux-pomodoro` and `notify` under `bob pomodoro` (`bob pomodoro tmux`, `bob pomodoro notify`).
   - **Vault Cluster:** Group `vault-sync` under `bob vault sync`.
   - **Capture Protocol:** Group the 10 machine-oriented `capture-*` commands under a designated Plumbing tier in help, removing them from the default user-facing `--help` view.

3. **What is the recommended implementation sequence?**
   - **Phase 1 (Clap Grouping & Help Facelift):** Add help categories to `build_cli()` in `runner.rs` and hide or separate `capture-*` endpoints into a `Capture Protocol` heading. This delivers 80% of the cognitive benefit immediately with zero risk of breaking any callers.
   - **Phase 2 (`bob task` & `bob pomodoro`):** Implement the `bob task` (`sync`, `archive`) and `bob pomodoro` (`tmux`, `notify`) sub-commands in `src/native/`, re-pointing legacy commands as aliases.
   - **Phase 3 (Documentation & Scripts Update):** Update `docs/` and internal script references (e.g. in `chezmoi` and `bob nightly`) to use the new canonical names while retaining aliases indefinitely.
