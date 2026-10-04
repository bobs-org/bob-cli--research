# Reorganizing `bob`'s subcommands: help sections first, a narrow `bob task`, and no broken callers

*Researcher: cld · 2026-10-04 · bob-cli @ `4e510cf` (master)*

## 1. Summary

**Verdict on the idea.** Grouping is worth doing, but a broad `bob task` umbrella is
the wrong tool for most of the problem. Most of what makes `bob --help` hard to read
has nothing to do with missing namespaces:

1. 10 of the 28 visible top-level commands, and 11 of the 29 help examples, are
   `capture-*` JSON endpoints. Bob Mac Capture calls them. People don't type them.
2. The help is one flat alphabetical list, so the daily loop, maintenance commands,
   integrations, and setup commands are mixed together.
3. A few names don't say what they do: `task-status-hooks`, `move-done-tasks`,
   `randomize`, and a bare `notify` that is really about Pomodoros.

Problem 2 is solved by **help sections**, not nesting. Problem 1 is solved by
**collapsing the capture protocol** in the short help. Nesting is only the right
fix for problem 3. Even there it works only because a noun is needed to disambiguate
the clearer verbs (`archive` what? `reroll` what?).

**Recommended solution, in three phases:**

- **Phase 1 (no breakage, most of the value).** Render `bob -h` / `bob --help` as
  workflow sections (Daily workflow · Tasks and projects · Vault · Integrations ·
  Setup). Collapse the 10 `capture-*` endpoints into a one-line "Capture protocol"
  pointer in `-h`, with the full list in `--help`. Trim the examples to porcelain
  commands, and make the shell-completion groups match the help sections.
- **Phase 2 (renames, every old spelling kept as a hidden alias).**
  - Add a **narrow `bob task`** for the three bulk task-state writers:
    `bob task reconcile` (was `task-status-hooks`), `bob task archive` (was
    `move-done-tasks`), `bob task reroll` (was `randomize`).
  - Fold `tmux-pomodoro` and `notify` into **`bob pomodoro {status,tmux,notify}`**,
    with bare `bob pomodoro` still meaning `status`.
- **Phase 3 (consistency polish).** Accept `-f/--format json` everywhere, with
  `--json` kept as an alias. Give the five hand-parsed commands clap-styled help.
  Mark default subcommands as "(default)" in help. Hide the one-time
  `freshness seed` once the cutover is done.

The visible top level shrinks from **28 entries to 14** plus a one-line protocol
pointer. Not one existing invocation breaks: not in the Mac app, tmux, Hammerspoon,
cron, launchd/systemd, the Obsidian plugins, or agent skills.

## 2. Requirement adjustments (called out explicitly)

These change the request as I read it. Each one is justified later in the report.

| # | Adjustment | Why |
| --- | --- | --- |
| R1 | **Reframe the goal** from "group sub-commands" to "make `bob --help` and command names self-explanatory." Treat grouping as one means among several. | §5: the largest readability costs are the protocol clutter and flat listing, not missing namespaces. |
| R2 | **Add a hard requirement: zero breakage.** Every current spelling, including the existing hidden aliases, keeps working indefinitely as a hidden alias. Don't print deprecation text to stderr when it isn't a TTY. | Program callers dominate (§4). The last hard renames left stale callers that are still broken today (§12.1). |
| R3 | **Treat the `capture-*` endpoints as a frozen protocol** and keep them out of the reorganization. Only their *presentation* changes. | The thin-client decision requires the Mac JSON contract to grow additively, and `bob` and the app are installed independently (§4.1). |
| R4 | **Scope `bob task` narrowly** to vault-wide task-state writers. Don't make it an umbrella for everything that touches tasks. | In Bob nearly every command touches tasks, so a broad `task` namespace has no predictable membership (§7). |
| R5 | **Amend the CLI rule** "keep listed subcommands sorted alphabetically" to "sorted alphabetically *within each help section*; sections in workflow order." | Sections and a single global alphabetical order can't both hold. This is a `sase/memory/cli_rules.md` change and must go through `/sase_memory_write`. |

## 3. What `bob` looks like today

`bob --help` lists 28 commands, plus `help` (91–96 lines with examples). The runner
is a flat table (`src/runner.rs` `SUBCOMMANDS`). Each entry delegates its raw args
to a native module that builds its own clap parser. Two hidden aliases
(`task-status-setter`, `mark-next-tasks`) map to `task-status-hooks`. Completion
already splits the table into two tiers: `Porcelain` and `Plumbing`, the latter
shown as "capture protocol" (`CompletionTier` in `runner.rs`, `present.rs`).

| Command | Kind | Own subcommands | Reads/writes | Main callers |
| --- | --- | --- | --- | --- |
| `capture` | porcelain | — (free-text `TEXT…`) | writes vault | Mac app, Bryan, agents |
| `capture-complete`, `-parse`, `-rewrite`, `-targets`, `-task-id`, `-pomodoro-name` | plumbing | — | read (task-id/pomodoro-name write) | **Bob Mac Capture** |
| `capture-pomodoros`, `-sections`, `-tasks`, `-task-sections` | plumbing | — | read | **no subprocess caller found** (completion uses the scanners in-process) |
| `completion` | setup | bash, install, status (default), uninstall, zsh | shell files | `just install` |
| `freshness` | report | list (default), seed | read / seed writes | Bryan |
| `gkeep` | integration | doctor, list (default), login, pull | Keep + vault | Bryan |
| `highlights` | integration | clip, create, doctor, marker, scan, sync (required) | PDFs, ref notes | chezmoi scripts, `sase.yml` |
| `move-done-tasks` | maintenance (hand-parsed) | — | writes + git | `nightly` |
| `nightly` | maintenance (hand-parsed) | — | git + writes | athena cron 03:30 |
| `notify` | pomodoro (hand-parsed) | — | read, notifies | `bob_notify` shim |
| `plan` | report | — | read | Bryan, agents |
| `plugins` | setup/dev | list (default), sync | plugin repo, vault | Bryan (32 uses on athena) |
| `pomodoro` | pomodoro (hand-parsed) | — | read | Hammerspoon menu bar (every 15 s) |
| `projects` | task model | list, sync (required) | read / writes | Bryan |
| `query` | inspect | — | read | agents (`bob_query` skill), `tg_cmd_tasks` |
| `randomize` | maintenance | — | writes + git | Bryan after time away |
| `ready` | report | — | read | Bryan, scripts (`--check`) |
| `task-status-hooks` | maintenance | — | writes | Bryan, after manual edits |
| `tmux-pomodoro` | pomodoro (hand-parsed) | — | read | `tmux.conf` status-right |
| `vault-sync` | maintenance | run (**default**), status | git | systemd watcher, macOS LaunchAgent |

## 4. Who actually calls `bob` (this sets the cost of any rename)

### 4.1 Program callers

- **Bob Mac Capture** (`Sources/CaptureCore/BobProcessClient.swift`) spawns
  `capture`, `capture-parse`, `capture-rewrite`, `capture-complete`,
  `capture-task-id`, `capture-pomodoro-name`, and `capture-targets`. The
  `mac-capture-is-a-thin-client` decision record says `bob` and the app "are installed
  independently, so the JSON contract must grow additively". A subcommand rename
  isn't additive. These names are effectively frozen.
- **chezmoi** (Bryan's dotfiles):
  - `tmux.conf` calls `#(bob tmux-pomodoro)`.
  - Hammerspoon polls `bob pomodoro --show-stale`.
  - The LaunchAgent runs `bob vault-sync -q`.
  - `bin/bob_vault_sync_watch` (the systemd user service) runs `bob vault-sync -q`.
  - `bin/maybe_bob_highlights_sync` and `bin/bob_xlib_pull` run `bob highlights scan`.
  - `sase.yml` runs `bob highlights create --include-id`.
  - The `bin/bob_notify`, `bin/bob_pomodoro`, and `bin/tmux_bob_pomodoro` shims
    exec `bob notify|pomodoro|tmux-pomodoro`.
  - `tg_cmd_tasks` runs `bob query`.
- **athena crontab:** `30 3 * * * … bob nightly >> /var/tmp/bob_nightly.log`.
- **Obsidian plugins (bob-plugins)** never spawn `bob`. They mirror its rules in JS.
  User-visible strings still name commands, for example navigation-hotkeys'
  "deferred to bob task-status-hooks".
- **Agents** use the `bob_query` skill, which is synced across every provider's
  skills directory, plus whatever `bob --help` shows them.

### 4.2 People

Hand-typed `bob` in athena's shell history, all-time counts:

| Count | Command |
| --- | --- |
| 61 | `bob dataview` (now `query`) |
| 32 | `bob plugins` |
| 21 | `bob highlights-ref` (now `highlights`) |
| 17 | `bob highlights` |
| 5 | `bob capture` |
| 4 | `bob collect-done` (now `move-done-tasks`) |
| 3 | `bob pomodoro-runtimes` |
| 2 each | `bob projects`, `bob move-done-tasks`, `bob cronjob` (now `nightly`) |
| 1 each | `bob task-status-hooks`, `bob sync`, `bob ready` |

apollo's history has 3 `bob` lines. The Mac wasn't sampled.

**What follows from this:**

- The daily loop runs mostly through tools: the Mac panel, Obsidian, tmux, and
  Hammerspoon. People type `bob` for dev and admin work.
- So `bob --help` is read mostly by **Bryan rediscovering a command he rarely runs,
  and by agents**. That favors scannable, sectioned help and self-describing names
  over saving keystrokes.
- It also means renames carry little muscle-memory cost but real **automation** cost.
  That is why R2 makes hidden aliases mandatory.

## 5. What actually makes the CLI hard to understand (ranked)

1. **Protocol clutter.** The 10 `capture-*` endpoints take 36% of the command list
   and 11 of the 29 examples. They also sort between `capture` and `completion`, so
   they push everything else down.
2. **No grouping.** In a flat alphabetical list, `plan`, `ready`, and `freshness`
   (one review loop) are scattered, and so are `pomodoro`, `notify`, and
   `tmux-pomodoro` (one object). The README's "Daily workflow" (capture → review →
   run → reconcile → nightly) appears nowhere in the help.
3. **Opaque names.**
   - `task-status-hooks`: "hooks" is internal jargon; the docs' own verb is
     "reconcile".
   - `randomize`: randomize what?
   - `move-done-tasks`: verb-object-object.
   - `notify`: notify about what?
   - `tmux-pomodoro`: sorts away from `pomodoro`.
4. **Mixed naming grammars.** Verb-object (`move-done-tasks`), noun-verb
   (`vault-sync`), bare nouns (`plan`, `projects`), an adjective (`ready`), and
   product names (`gkeep`, `highlights`). Plurals are mixed too (`projects`,
   `plugins` vs `pomodoro`).
5. **Inconsistent group behavior.**
   - The bare form of a group does different things: `gkeep` → `list`,
     `completion` → `status`, `freshness` → `list`, `plugins` → `list`, but
     `vault-sync` → **`run`** (a git writer, see §12.3). `projects` and
     `highlights` require a subcommand.
   - JSON output is spelled `-j/--json` in `completion` and `vault-sync status`, but
     `-f/--format json` everywhere else.
   - The five hand-parsed commands print argparse-style help. `notify` even prints
     `usage: bob_notify`.
6. **"sync" means five things:** `vault-sync` (git), `plugins sync` (deploy),
   `projects sync` (derive project state), `highlights sync` (PDF → note), and the
   one-line description of `task-status-hooks` ("Sync active task dependencies…").

Only item 3, and part of item 4, actually need namespaces.

## 6. Design principles used to judge the options

- **Noun-verb two-level subcommands suit tools with many objects and operations, if
  the verbs stay consistent across nouns** ([clig.dev][clig], e.g.
  `docker container create`).
- **Grouping can live in the help instead of in nesting.** git keeps every command
  top-level. Its `command-list.txt` tags each one (`mainporcelain`,
  `plumbinginterrogators`, …), and `git help` prints the common ones grouped by
  theme ([git command-list][gitcl], [git help grouping patch][githelp]). gh prints
  "CORE COMMANDS / ADDITIONAL COMMANDS". Bob already has a porcelain/plumbing split
  in its completion tier.
- **Restructure without breaking.** Docker 1.13 added management commands
  (`docker container …`) but kept every legacy top-level command working, behind an
  opt-in `DOCKER_HIDE_LEGACY_COMMANDS` for the help listing
  ([Docker 1.13 blog][docker113], [Docker CLI reference][dockerref]).
- **Bob's own record.**
  - The `dataview → query`, `highlights-ref → highlights`, and `cronjob → nightly`
    renames were hard cuts, and they left callers that are still broken (§12.1).
  - The `task-status-setter → task-status-hooks` rename kept hidden aliases, cost
    one table row per alias, and nothing broke.
- **Avoid ambiguous and catch-all names** ([clig.dev][clig]). This argues against
  `bob task sync` (one more "sync") and against `task` as an umbrella for everything.
- **Tooling limit.** clap 4.6 supports a single `subcommand_help_heading` for all
  subcommands, not per-subcommand headings. Per-command headings are still an open
  request (clap [#1553][clap1553], [#5828][clap5828], unmerged PR [#5819][clap5819]),
  which I confirmed against the vendored `clap_builder-4.6.7`. Bob's top level is
  a table of argument-less delegate commands with a custom `help_template`, so it
  can render the sections itself. That needs no clap fork.

## 7. Critique of the `bob task` idea

**What's right about it:** three commands are clearly operations on the vault's set
of tasks, have opaque names, and get much clearer with a noun in front:

| Today | As `bob task …` | Why the noun helps |
| --- | --- | --- |
| `task-status-hooks` | `bob task reconcile` | Top-level `bob reconcile` could mean git (vault-sync's own description says "Reconcile the vault through Git"). |
| `move-done-tasks` | `bob task archive` | Top-level `bob archive` is ambiguous next to Highlights PDFs and `old_lib/`. |
| `randomize` | `bob task reroll` | `bob reroll` alone doesn't say *what* is re-rolled. |

These three also behave alike. They are vault-wide writers. Two of them take the
shared maintenance lock (`task-status-hooks` when not a dry run, and `randomize`),
and `move-done-tasks` runs inside `nightly`'s lock. Automation or a deliberate human
runs them to bring task state back into consistency. That gives a membership rule
that predicts where a command lives: **"`bob task <verb>` rewrites task state across
the whole vault."**

**What's wrong with a broad version** (`bob task` holding plan/ready/freshness/
projects/capture too):

- **No discriminating power.** In Bob everything is about tasks: capture creates
  them, plan and ready list them, freshness reviews them, projects are `^prj` tasks,
  gkeep pulls tasks. A namespace with no clear membership rule is the catch-all that
  clig.dev warns against. A user can't predict whether "Keep inbox" or "projects"
  lives under it.
- **The verbs read wrong in noun-verb grammar.** `bob task ready` reads as "make the
  task ready", but it's a read-only report. `bob task plan` reads as "schedule a
  task".
- **It lengthens the most-typed reports.** `plan`, `ready`, and `freshness` are the
  README's daily review trio, and nesting them buys nothing that a "Daily workflow"
  help section doesn't.
- **It can't include the capture protocol** (R3), so it would never fully absorb the
  task-related commands anyway.

**My position:** adopt `bob task`, but only with the narrow membership rule above.
`bob task --help` should end with a "See also: `bob plan`, `bob ready`,
`bob freshness`, `bob projects`" line, so someone who looks for task views under
`task` still finds them.

## 8. Options considered

| Option | Shape | Verdict |
| --- | --- | --- |
| **A. Sections only** | Flat names, sectioned help, protocol collapsed | **Adopt as Phase 1.** No breakage and most of the readability gain. On its own it leaves the opaque names. |
| **B. Narrow namespaces where a rename is needed anyway** | A + `bob task {archive,reconcile,reroll}` + `bob pomodoro {status,tmux,notify}`, hidden aliases for every old name | **Recommended (Phase 2).** Nest only where a rename is already justified and a crisp family exists. |
| C. Broad `bob task` umbrella | plan/ready/freshness/projects/capture/… under `task` | Reject (§7). |
| D. Full noun-verb rewrite (docker-style everywhere) | `bob vault sync`, `bob capture add`, `bob review plan`, … | Reject. `bob capture TEXT…` can't take verb subcommands without a grammar collision: `bob capture parse foo` is a valid capture today. The churn is huge: 14k doc lines, and `task-status-hooks` alone appears 56× in docs and 225× in tests. |
| E. Flat clearer renames (`bob archive`, `bob reconcile`, `bob reroll`) | No namespace | Reject. These are ambiguous at the top level of a tool that also does git, PDFs, and Keep (§7 table). |
| F. Namespace the capture protocol (`bob capture-api parse`, …) | Move the 10 endpoints | Reject. Not additive for the independently installed Mac app, nobody types them, and completion already groups them. Fix the presentation only. |
| G. `bob vault {sync,status,nightly}` | Fold `vault-sync` + `nightly` | **Defer.** Both names are already clear, and they are the most automation-bound commands (systemd, launchd, cron, memory notes). A "Vault" help section gets the grouping without the risk. Reopen if a third vault-level command arrives (e.g. a conflicts or doctor view). |
| H. `bob review {plan,ready,queue}` | Nest the review trio | Reject. These are the three most-read daily reports, each answering a different question, and a section already groups them. |
| I. Singular aliases (`project`, `plugin`) | Visible aliases | Skip. Two spellings would clutter completion. The plurals are fine as collection nouns. |

## 9. Recommended reorganization

### 9.1 Target top-level `bob -h`

```text
Bob — command-line tools for the Bob Obsidian vault and Pomodoro workflow

Usage: bob <COMMAND>

Daily workflow:
  capture     Capture tasks, bullets, and Pomodoro session commands into the vault
  freshness   Walk the tiered freshness review queue
  plan        Show today's plan budget, Today's tasks, and the NEXT/PENDING lanes
  pomodoro    Show Pomodoro status, print the tmux line, or notify on completion
  ready       Show each area/project note's Ready lane against the per-note cap

Tasks and projects:
  projects    List and sync project notes via their ^prj tasks
  task        Reconcile statuses, re-roll due tasks, and archive done tasks

Vault:
  nightly     Run nightly maintenance: sync, archive done tasks, sync
  query       Run Dataview or Tasks queries against the vault
  vault-sync  Reconcile the vault through Git (default: run) or show status

Integrations:
  gkeep       Drain the Google Keep inbox into Obsidian tasks
  highlights  Sync Highlights PDF annotations into reference notes

Setup:
  completion  Install and inspect shell completion for bob
  plugins     List and deploy Bob's custom Obsidian plugins

Capture protocol (JSON endpoints for Bob Mac Capture; `bob --help` lists them):
  capture-complete  capture-parse  capture-pomodoro-name  capture-pomodoros
  capture-rewrite   capture-sections  capture-targets  capture-task-id
  capture-task-sections  capture-tasks

Options:
  -h, --help     Print help (see more with '--help')
  -V, --version  Print version

Examples:
  bob capture buy milk @groceries     Capture a task into groceries.md
  bob capture '='                     Start the queued Pomodoro
  bob plan                            Show today's plan budget and lanes
  bob freshness list -f json          List the review queue
  bob task reconcile --dry-run        Preview task status reconciliation
  bob task reroll --dry-run           Preview re-rolling due prioritized tasks
  bob query --source '#project'       Print matching note paths
  bob vault-sync status --json        Print the last vault Git sync status
```

`bob --help` renders the same sections, plus one described line per protocol
endpoint and the long description. Sections are listed in workflow order, with
commands alphabetical within each (R5). Completion's group headers become these
same section names, so `bob <TAB>` and `bob -h` teach one map.

### 9.2 Old → new mapping (every old spelling stays as a hidden alias)

| Old invocation | Canonical invocation | Alias kept |
| --- | --- | --- |
| `bob task-status-hooks` | `bob task reconcile` | yes, plus the existing `task-status-setter` and `mark-next-tasks` |
| `bob move-done-tasks` | `bob task archive` | yes (`nightly` calls the new path internally) |
| `bob randomize` | `bob task reroll` | yes |
| `bob pomodoro` | `bob pomodoro` (= `bob pomodoro status`) | unchanged |
| `bob tmux-pomodoro` | `bob pomodoro tmux` | yes (`tmux.conf` keeps working) |
| `bob notify` | `bob pomodoro notify` | yes (`bob_notify` shim keeps working) |
| `bob capture-*` (10) | unchanged | n/a: frozen protocol |
| all others | unchanged | n/a |

The legacy binaries `bob_pomodoro`, `bob_notify`, and `tmux_bob_pomodoro` keep
working exactly as they do now.

### 9.3 `bob task -h` and `bob pomodoro -h`

```text
Usage: bob task <COMMAND>

Commands:
  archive    Move done and canceled tasks into archive notes and repair links
  reconcile  Apply the task status hooks: promote linked work, derive Blocked, clean the ledger
  reroll     Re-roll due prioritized tasks within their priority windows

See also: bob plan, bob ready, bob freshness, bob projects (read-only task views)
```

```text
Usage: bob pomodoro [COMMAND] [OPTIONS]

Commands:
  notify  Notify when the current Pomodoro is complete
  status  Show the current Pomodoro status (default)
  tmux    Print the Pomodoro status and plan-budget meter for tmux
```

`bob task` gets no default subcommand, because all three are writers. `bob pomodoro`
defaults to `status`, its read-only view. That follows the rule proposed in Phase 3:
**a group's bare form may only default to a read-only view.** `vault-sync` breaks
that rule today. Its bare form stays `run` for automation compatibility, but the
help should label it.

### 9.4 Why the names

- **`reconcile` over `sync` or `hooks`.**
  - The README and getting-started already describe the step as "reconcile
    statuses".
  - `sync` already has five meanings in Bob.
  - `hooks` reads as a noun ("list the hooks?").
  - The concept stays "task status hooks". The doc stays
    `docs/task-status-hooks.md`, and its usage line becomes "`bob task reconcile`
    applies the task status hooks". So the decision records that cite
    `bob task-status-hooks` stay accurate, through the alias, without being edited
    (they're immutable).
- **`reroll` over `randomize` or `reschedule`.** It matches the docs' "re-roll" and
  the capture-time `p:<N>` "priority roll", and it signals randomness within a
  window. `reschedule` sounds deterministic.
- **`archive` over `move-done`.** The vault layout already calls `done/` "archive
  notes".
- **`pomodoro tmux` / `pomodoro notify`.** They keep the old words, so muscle
  memory transfers.

## 10. Compatibility and migration policy

1. **Aliases are permanent and cheap.** One table row each, excluded from help and
   completion, covered by the same kind of tests that already guard
   `task-status-setter`/`mark-next-tasks` (`completion/tree.rs`
   `hidden_aliases_and_help_are_absent`).
2. **No stderr noise for programs.** At most, print a one-line hint when **stderr is
   a TTY** (`note: 'bob randomize' is now 'bob task reroll'`), so Bryan's habits move
   toward the canonical names. Never print it when stderr is a pipe: the Mac app and
   launchd/cron capture stderr into logs and error reports.
3. **Equivalence tests.** For every alias, the old and new spellings must give
   byte-identical stdout and exit codes on the existing fixtures. This replaces
   "update 225 test mentions" with a parametrized check, and the existing tests can
   migrate to canonical names gradually.
4. **Docs.**
   - Rewrite the README "Commands" table into the same sections.
   - Add an old → new table to "Migration notes".
   - Update usage lines in `task-status-hooks.md`, `randomize.md`,
     getting-started, and `capture.md` (its `task-status-hooks` mentions).
   - Leave `docs/` filenames alone.
5. **Cross-repo follow-ups.** None are urgent, because aliases cover them:
   - the navigation-hotkeys notice string in bob-plugins;
   - the chezmoi shims and `tmux.conf` (switch to `bob pomodoro tmux` whenever
     convenient);
   - the `obsidian.md` memory note's `move-done-tasks` mention.

## 11. Implementation sketch

**Runner model** (`src/runner.rs`): replace the tier with a section and allow groups.

```rust
enum Section { Daily, TasksProjects, Vault, Integrations, Setup, CaptureProtocol }

struct Subcommand {
    name: &'static str,
    about: &'static str,
    section: Section,
    target: Target,
}

enum Target {
    Leaf { native: NativeCommand, script: Option<&'static str> },
    Group { members: &'static [Subcommand], default: Option<&'static str> },
}

// Old spelling (argv prefix) -> canonical path; resolved before clap parses.
const ALIASES: &[(&[&str], &[&str])] = &[
    (&["task-status-hooks"], &["task", "reconcile"]),
    (&["task-status-setter"], &["task", "reconcile"]),
    (&["mark-next-tasks"], &["task", "reconcile"]),
    (&["move-done-tasks"], &["task", "archive"]),
    (&["randomize"], &["task", "reroll"]),
    (&["tmux-pomodoro"], &["pomodoro", "tmux"]),
    (&["notify"], &["pomodoro", "notify"]),
];
```

- **Help rendering.** Keep clap for parsing and errors, but take the subcommand
  listing out of `HELP_TEMPLATE`. Render the sections from the table into
  `before_help`/`before_long_help`. Put the compact protocol line in the short help
  and the described list in the long help. The table stays the single source, so
  help, completion, and dispatch can't drift (the property `CompletionTier` already
  guarantees).
- **Dispatch.** Rewriting the alias argv prefix first keeps clap's tree free of
  hidden duplicates. A group dispatches its first token to a member. If the token
  isn't a member name and the group has a `default`, the whole argv goes to the
  default member. That keeps `bob pomodoro --show-stale` and `bob pomodoro -s`
  working, and `BOB_CLI_USE_SCRIPT=1` still routes `pomodoro tmux` to the
  `tmux_bob_pomodoro` script asset.
- **Usage names.** Modules such as `randomize.rs` and `task_status_hooks/mod.rs`
  build their parser from a `COMMAND_NAME` constant. Pass in the display path
  (`bin_name("bob task")`, `name("reroll")`) so `bob task reroll --help` prints the
  canonical usage. About 26 in-source hint strings name old commands, and should move
  to canonical names.
- **Completion.** `tree()` mounts groups as nested clap commands; nested children
  already work for `projects`, `gkeep`, and others. `present.rs` swaps the hardcoded
  `commands`/`capture protocol` pair for the section names.
- **Tests to update or add:**
  - `subcommands_are_sorted_alphabetically` becomes "sorted within section".
  - `mounted_names_match_subcommands_in_order` gets updated.
  - New: alias equivalence, every `NativeCommand` reachable through exactly one
    canonical path, and help-snapshot tests for `bob -h` and `bob --help`.

**Size.** Phase 1 is one focused change (runner, completion presentation, tests,
README Commands table, CLI-rule memory amendment). Phase 2 is two to three focused
changes: groups and aliases, then docs and examples, then optional cross-repo string
updates. Phase 3 is independent small items that can be filed as separate beads.

## 12. Incidental findings

1. **Stale callers from past hard renames, still live:**
   - `~/.claude/skills/bob_dataview/SKILL.md` on apollo is an installed skill whose
     source no longer exists in chezmoi (only `bob_query` does). It tells agents to
     run `bob dataview`, which fails with `unrecognized subcommand 'dataview'`. It
     still shows up in agents' skill lists, including this session's.
   - chezmoi `bin/maybe_bob_highlights_sync` still reports failures as
     "bob highlights-ref scan failed".

   Both show what the "no aliases" policy costs, and why I recommend R2.
2. **Four protocol endpoints have no subprocess caller:** `capture-pomodoros`,
   `capture-sections`, `capture-tasks`, and `capture-task-sections`. The Mac source
   and its git history never call them; completion uses the same scanners in-process.
   They are documented as the picker protocol for future clients, so keep them. But
   the `--help`-only placement (§9.1) fits them, and they could be deprecated later
   if no frontend adopts them.
3. **Bare `bob vault-sync` is a writer.** It defaults to `run`, unlike every other
   group whose bare form is a read-only view, and the help only shows `bob vault-sync`
   as an example without saying so. I hit this while surveying defaults: a bare
   `bob vault-sync` probe ran one real reconcile cycle on apollo. It was a no-op
   (status: `files_committed: 0`, local = remote `7b592d99`, no push), the same cycle
   `bob-vault-sync.service` already runs continuously there. But it shows the
   surprise is real. Automation depends on `bob vault-sync -q`, so don't change the
   default; label it "(default)" in help (Phase 3).
4. **JSON flag inconsistency.** `completion` and `vault-sync status` use `-j/--json`,
   and everything else uses `-f/--format json`.
5. **Hand-parsed help.** `notify`'s usage says `bob_notify`, and the five hand-parsed
   commands use a different, lowercase, argparse-like help style from the clap
   commands. That conflicts with the CLI rule asking for excellent, consistent `-h`.

## 13. Open questions for Bryan

1. Does the Mac hand-typed history look like athena's (admin and dev use only)? If you
   type `plan`/`ready`/`freshness` often on the Mac, that further supports keeping
   them top-level.
2. Do you want the TTY-only migration hint (§10.2), or silent aliases?
3. `reconcile` vs keeping the `hooks` word (`bob task hooks`): which reads better to
   you? I recommend `reconcile` (§9.4). The concept name in the docs can stay either
   way.
4. Should `freshness seed` be hidden after the 2026-10-19 cutover, or kept visible for
   new vaults?

## Sources

- [Command Line Interface Guidelines (clig.dev)][clig]: subcommands, noun-verb
  consistency, ambiguous names, catch-alls.
- [git `command-list.txt`][gitcl] and the [`git help` group-common-commands-by-theme
  patch series][githelp]: help grouping without nesting.
- [Docker 1.13 Management Commands (Couchbase blog)][docker113] and the
  [Docker CLI reference][dockerref]: management commands plus legacy commands kept,
  `DOCKER_HIDE_LEGACY_COMMANDS`.
- clap issues [#1553 (multiple subcommand help headings)][clap1553],
  [#5828 (`next_help_heading` ignored for subcommands)][clap5828], and
  [PR #5819 (subcommand help headings)][clap5819]: current clap limits.
- Local evidence: bob-cli `src/runner.rs`, `src/native.rs`,
  `src/native/completion/{tree,present}.rs`, `README.md`,
  `docs/getting-started.md`, `docs/capture.md`, `docs/task-status-hooks.md`;
  Bob Mac Capture `Sources/CaptureCore/BobProcessClient.swift`; chezmoi
  `tmux.conf`, `dot_hammerspoon/init.lua`, LaunchAgent and systemd units, `bin/`
  shims; athena crontab and shell-history counts; the
  `decisions:mac-capture-is-a-thin-client` memory record; git history of the
  `dataview`, `highlights-ref`, `cronjob`, and `task-status-setter` renames
  (`f401add`, `292f530`, `20e9ecd`, `cf931a3`).

[clig]: https://clig.dev/
[gitcl]: https://github.com/git/git/blob/master/command-list.txt
[githelp]: https://ratatoskr.run/git/2016/06/7655659/t
[docker113]: https://www.couchbase.com/blog/docker-1-13-management-commands/
[dockerref]: https://docs.docker.com/reference/cli/docker/
[clap1553]: https://github.com/clap-rs/clap/issues/1553
[clap5828]: https://github.com/clap-rs/clap/issues/5828
[clap5819]: https://github.com/clap-rs/clap/pull/5819
