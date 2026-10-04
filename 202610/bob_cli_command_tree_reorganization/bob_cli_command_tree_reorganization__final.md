# Reorganizing `bob`'s command tree: sectioned help first, then a narrow `bob task` and `bob pomodoro`

*Consolidated report · 2026-10-04 · bob-cli @ `b1332af` (master) · merges researchers
cdx, cld, grk, gem plus lead verification*

## 1. Bottom line

**Yes, reorganize, but mostly not by nesting.** Most of what makes `bob --help` hard to
read has nothing to do with missing parent commands:

1. **Protocol clutter.** 10 of the 28 visible commands are `capture-*` JSON endpoints
   for Bob Mac Capture. They sort right after `capture`, so the first screen of help is
   almost entirely plumbing. 9 of the 29 help examples are protocol calls too.
2. **No structure.** One flat A–Z list hides the README's own daily loop: capture →
   review → link/run → reconcile → nightly.
3. **A few opaque names.** `task-status-hooks`, `move-done-tasks`, `randomize`, and a
   bare `notify` that is really about Pomodoros.

Problems 1 and 2 are fixed by **help sections**, with no argv change. Only problem 3
needs namespaces, and only two:

- A **narrow `bob task`** that holds just the bulk task-state writers: `archive`,
  `reconcile`, and `reroll`.
- **`bob pomodoro {notify,status,tmux}`**, where bare `bob pomodoro` still means
  `status`.

Every current spelling keeps working forever as a silent hidden alias. The default help
drops from 28 peers to **14 entries in 5 sections**, plus a final "Capture protocol"
section. No caller breaks: not Mac Capture, tmux, Hammerspoon, the launchd/systemd sync
watchers, the athena and Mac crontabs, or agent skills.

**A broad `bob task` umbrella is the wrong cut.** That means moving `plan`, `ready`,
`freshness`, `capture`, and so on under one noun. In Bob nearly every command touches
tasks, so a "task" folder has no predictable membership. It would also split the README's
review trio and make read-only reports read like mutations (`bob task ready`).

## 2. Where the four reports agreed, and where they split

| Question | cdx | cld | grk | gem | **Resolution** |
| --- | --- | --- | --- | --- | --- |
| Fix help before moving anything | yes | yes | yes | yes | **Yes: Phase 1** |
| Keep `plan` and `capture` top-level | yes | yes | yes | yes | **Yes** |
| Nest protocol under `bob capture` | no | no | no | no | **No** (grammar collision, §4.3) |
| Keep every old spelling working | yes | yes | yes | yes | **Yes, permanently, silently** |
| Fold `tmux-pomodoro`/`notify` into `pomodoro` | yes | yes | optional | yes | **Yes: Phase 2** |
| Add `bob task` at all | yes | yes (narrow) | **no** | yes (narrow) | **Yes, narrow** (§5.1) |
| `ready`/`freshness` under `task` | **yes** | no | no | alias only | **No** (§5.2) |
| `randomize` under `task` | yes | yes (`reroll`) | no | alias only | **Yes, as `reroll`** (§5.3) |
| Name for `task-status-hooks` | `reconcile` | `reconcile` | `reconcile` | `sync` | **`reconcile`** |
| Move the protocol to a new namespace | **`capture-api`** | no | no | no | **No; presentation only** (§5.4) |
| Help: sections or strict A–Z | **A–Z** | sections | sections | sections | **Sections, A–Z within each** (§5.5) |
| `bob vault {sync,nightly}` | **yes** | defer | no | yes | **Defer** (§5.6) |
| Deprecation hints | none | TTY-only | — | — | **None** (§6) |

### Corrections made while merging

These claims in the input reports were checked against the code and found wrong or
incomplete.

- **gem said Mac Capture spawns all 10 `capture-*` endpoints.** It spawns 7: `capture`,
  `capture-parse`, `capture-rewrite`, `capture-complete`, `capture-task-id`,
  `capture-pomodoro-name`, and `capture-targets` (bob-mac-capture `52b3360`, `Sources/`).
  `capture-tasks`, `-sections`, `-pomodoros`, and `-task-sections` have no subprocess
  caller. cld and grk had this right.
- **gem said to give the 10 endpoints a per-command `subcommand_help_heading`.** clap
  can't do that. `subcommand_help_heading` is a single setting on the parent, and
  vendored `clap_builder-4.6.7` has no per-subcommand heading. Sections must be rendered
  from bob's own table, as cld proposed.
- **gem said `task-status-hooks` is run by `bob nightly`.** It isn't. `nightly` runs
  exactly `vault-sync` → `move-done-tasks` → `vault-sync` (`src/native/nightly.rs` `STEPS`).
- **gem said the registry declares 27 commands plus `help`.** It declares 28 public
  commands plus 2 hidden aliases (`src/runner.rs` `SUBCOMMANDS`).
- **gem said Bryan runs `plan`/`ready`/`freshness` "multiple times an hour".** Nothing
  supports that. cld's athena shell-history counts show very little hand-typed `bob` use
  (the Mac wasn't sampled). This report therefore doesn't base any decision on saving
  keystrokes.
- **cld counted 11 of 29 examples as protocol calls.** The actual count is 9 protocol
  examples, plus 2 ordinary `capture` examples.
- **No report listed the Mac crontab.** The scheduled caller of `task-status-hooks` is a
  hand-installed Mac crontab, not managed by chezmoi. It runs
  `bob task-status-hooks --retry-timeout 120` and `bob projects sync` every 15 minutes
  (`docs/vault-git-sync.md:120-123`). Its stderr deliberately reaches cron mail. This
  settles two questions: the old name must stay callable forever, and aliases must never
  print to stderr.

## 3. Adjusted requirements (called out explicitly)

| # | Adjustment to the request | Why |
| --- | --- | --- |
| R1 | **Reframe the goal.** Change it from "group sub-commands" to "make `bob --help` and command names self-explanatory." Grouping is one tool among several. | The two largest readability costs (protocol clutter and the flat list) need no new parents (§1). |
| R2 | **Hard zero-breakage rule.** Every current spelling keeps working indefinitely as a hidden alias. That includes `task-status-setter`, `mark-next-tasks`, and the `bob_pomodoro`/`bob_notify`/`tmux_bob_pomodoro` binaries. No deprecation output. | Callers are mostly programs (§4.2). bob's past hard renames (`dataview`, `highlights-ref`, `collect-done`) left callers broken. Example: the installed `bob_dataview` agent skill still tells agents to run `bob dataview`, which fails with `unrecognized subcommand`. |
| R3 | **Freeze the `capture-*` protocol.** Change only how it's presented in help. | Under `decisions:mac-capture-is-a-thin-client`, bob and the app install independently, so the contract may only grow additively. |
| R4 | **Scope `bob task` narrowly** with a stated membership rule: "`bob task <verb>` rewrites task lines across the whole vault." | A broad "task" folder has no discriminating power in a tool where everything touches tasks (§5.2). |
| R5 | **Amend `cli_rules.md`.** Change "keep listed subcommands … sorted alphabetically" to "alphabetical *within each help section*; sections in workflow order." This must go through `/sase_memory_write`. | Sections and one global A–Z order can't both hold. Sorting within sections keeps commands easy to guess. |
| R6 | **Help and completion parity are requirements, not polish.** `bob help <cmd>` must show real help. Leaf help must print the canonical path. `bob <TAB>` groups must match the help sections. | `bob help plan` currently prints the delegate stub `Usage: bob plan [args]...` instead of the real help (verified; cdx). |
| R7 | **Don't invent new task operations** to make the tree look complete. No `task add/list/show` now. | No such contract exists. `query`, `plan`, and `ready` already cover the read side (cdx, grk). |
| R8 | **Out of scope; file separately:** unifying `-j/--json` with `-f/--format json`, singular/plural normalization, and restyling the hand-parsed help. | These are real inconsistencies (cld §5), but bundling them inflates the change and its risk. |

## 4. Evidence base

### 4.1 Current surface (verified)

`src/runner.rs` holds a sorted table of 28 delegate commands. Each forwards raw
`OsString` args to a native module that builds its own clap parser. Each entry is tagged
`CompletionTier::Porcelain` (18) or `Plumbing` (10).

Shell completion already renders the 10 plumbing endpoints last, under a
`capture protocol` group (`src/native/completion/present.rs` ~L392). Help doesn't: it
uses one `{all-args}` block and a 29-line `AFTER_HELP`. Two hidden aliases,
`mark-next-tasks` and `task-status-setter`, route to `task-status-hooks`.

Existing families already follow a "noun with several verbs" rule:

- `completion` {bash, install, status (default), uninstall, zsh}
- `freshness` {list (default), seed}
- `gkeep` {doctor, list (default), login, pull}
- `highlights` {clip, create, doctor, marker, scan, sync}
- `plugins` {list (default), sync}
- `projects` {list, sync}
- `vault-sync` {run (default), status}

### 4.2 Who calls which names (sets the cost of any move)

| Caller | Invocation | Source |
| --- | --- | --- |
| Bob Mac Capture | the 7 `capture*` names listed in §2 | bob-mac-capture `Sources/` @ `52b3360` |
| Mac crontab (hand-installed) | `bob task-status-hooks --retry-timeout 120`, `bob projects sync` every 15 min | `docs/vault-git-sync.md:120-123` |
| athena crontab | `bob nightly` at 03:30 | cld |
| macOS LaunchAgent / systemd watcher | `bob vault-sync -q` (every 15 s on Mac) | chezmoi (cdx, cld) |
| tmux status line | `#(bob tmux-pomodoro)` | chezmoi `tmux.conf` |
| Hammerspoon | `bob pomodoro --show-stale`, parsing stdout | chezmoi `init.lua:496` |
| Shims | `bob_pomodoro`, `bob_notify`, `tmux_bob_pomodoro` | Cargo `[[bin]]`, chezmoi `bin/` |
| Agents | `bob query` (`bob_query` skill) | skills |
| `just install-smoke` | `--help` on every `capture-*` name | `justfile:78+` |
| bob-plugins | one user-visible string: "deferred to bob task-status-hooks" | `bob-navigation-hotkeys/main.js:21232` |

The README's own "Migration notes" tell new integrations to use `bob pomodoro`,
`bob notify`, `bob vault-sync`, and `bob tmux-pomodoro`. These are published integration
names, which is another reason R2 makes old spellings permanent.

Churn if names changed by hard cut: `task-status-hooks` appears on ~47 lines of
docs/README and 225 test lines (verified). Permanent aliases plus a parametrized
old/new equivalence test make updating those mentions optional, not blocking.

### 4.3 The capture-grammar constraint (why `bob capture parse` is impossible)

`bob capture` takes free-text `TEXT…`. cdx ran
`bob capture --dry-run --format json <text>` against an isolated fixture. Each of
`parse`, `complete`, `tasks`, `parse invoices`, and `api design` came back as an ordinary
task, with exit 0.

Reserving any of those words as subcommands would silently change valid captures.
Quoting doesn't help: the shell strips the quotes before bob sees the word. Requiring
`--` would be a grammar break. The protocol therefore can't nest under `capture`, and
keeping the hyphenated sibling names is correct.

### 4.4 Tooling limits (verified)

- clap 4.6.7 has one `subcommand_help_heading` per parent; per-subcommand headings are
  still open upstream (clap #1553, #5828; PR #5819, per cld). bob's root is already a
  table of argument-less delegates with a custom `help_template`, so it can render
  sections itself without a clap fork.
- A clap `alias` names a sibling. It can't map a flat name onto a two-token nested path.
  Compatibility needs an argv-prefix rewrite table, resolved before clap parses (cdx,
  cld).

### 4.5 Comparable CLIs (from the input reports; not re-fetched)

- **git** keeps every command top-level. It hides plumbing from common help and groups
  the common commands by situation ("start a working area", …). This is the model for
  Phase 1.
- **gh** mixes object families (`issue`, `repo`) with direct actions (`browse`,
  `status`). That supports keeping `capture` and `plan` direct.
- **Docker 1.13** added `docker container …` while keeping every legacy top-level command
  working. This is the model for R2.
- **clig.dev:** lead help with common commands, avoid catch-all names, keep noun-verb
  consistent where it's used.

## 5. Resolving the disagreements

### 5.1 Should `bob task` exist? Yes, narrowly (against grk)

grk prefers top-level renames (`bob reconcile`, `bob archive`) with no new noun. The
noun earns its place because the bare verbs are ambiguous in this tool:

- `vault-sync`'s own description is "Reconcile the Bob vault through Git", and `nightly`
  "reconciles the vault through Git". So a top-level `bob reconcile` would compete with
  Git reconciliation.
- `bob archive` could mean `done/` archive notes, Highlights PDFs, or `old_lib/`.
- `bob reroll` doesn't say what gets re-rolled.

With `task` in front, all three are unambiguous. grk's other worry was that "task" is
overloaded because `sase task` aliases `proc`. That doesn't apply: they're different
binaries.

### 5.2 What belongs in `bob task`? Only the vault-wide task writers (against cdx and gem)

Membership rule: **`bob task <verb>` rewrites task lines across the whole vault.**

| Today | Canonical | Writes |
| --- | --- | --- |
| `task-status-hooks` (+ `task-status-setter`, `mark-next-tasks`) | `bob task reconcile` | Promotes linked work, derives Blocked, cleans the ledger |
| `move-done-tasks` | `bob task archive` | Moves done/canceled blocks to `done/`, repairs links, commits |
| `randomize` | `bob task reroll` | Re-rolls scheduled dates of due prioritized tasks, sync-sandwiched commit |

`ready` and `freshness` stay top-level, against cdx, for four reasons:

1. The README groups `plan`, `freshness`, and `ready` as the read-only review trio.
   cdx keeps `plan` top-level, so its tree splits the trio across two depths.
2. In noun-verb grammar, `bob task ready` reads as "make the task ready", but it's a
   read-only report.
3. `bob task freshness list|seed` creates a third level of nesting.
4. Adding read-only reports would blur the one rule that makes the namespace
   predictable.

gem's alias entries (`bob task ready` → `bob ready`) are rejected too. Two visible
spellings clutter completion and make the canonical path unclear. Instead,
`bob task --help` ends with a "See also: `bob plan`, `bob ready`, `bob freshness`,
`bob projects`, `bob query`" line.

Future room: if Bob ever gains single-task commands keyed by a stable ref, they can join
this namespace (e.g. grk's `bob task show <ref>`). Only add them with a real contract;
don't rename `capture-task-id` into `bob task id` (cdx).

### 5.3 `randomize` → `bob task reroll` (lowest-confidence call)

The case for moving it: it's a bulk writer that commits through Git, the same kind of
command as the other two. A top-level `randomize` leaves open what is randomized.

The case for `reroll` over `randomize`: the command's own about string says "Re-roll
due prioritized tasks". The docs say "re-roll". Capture's `p:<N>` "roll[s] a scheduled
date". And "randomize" wrongly suggests shuffling task order.

Counterweight: the README lists it under step 2 (review), and `bob randomize` is the
label on its Git commits. **`bob task randomize` is an acceptable fallback** if Bryan
prefers to keep the word. Either way, `bob randomize` stays as a hidden alias.

### 5.4 Capture protocol: presentation only, no `capture-api` (against cdx)

cdx's `bob capture-api {parse,…}` would make the root tree smallest. Sectioned help gets
the same visual result for free, though. A move would leave the 7 Mac-spawned names
needing permanent aliases, which permanently doubles a versioned protocol's surface and
its tests, for commands nobody types.

So: keep the names. Put them last in their own section, collapsed to one line in `-h`
and fully listed in `--help`. Mark the two writers (`capture-task-id`,
`capture-pomodoro-name`) as such in their descriptions (cdx).

The 4 endpoints with no subprocess caller stay too. They're the documented picker
protocol for future clients. Revisit them only with an inventory of all clients.

### 5.5 Sections vs strict A–Z (against cdx)

cdx keeps a single alphabetical list to honor `cli_rules.md` and avoid judgment calls on
grouping. The rule's first line, though, demands help that is "easy to scan", and a
28-row A–Z list with plumbing first fails that.

To limit judgment calls, take the sections from the README's existing daily-workflow
steps and keep commands A–Z within each section (R5). Use clap's existing `-h`/`--help`
split rather than inventing `--full-help`. A new public long option would also need a
short alias under `cli_rules.md`, and agents running `--help` still get the complete
inventory.

### 5.6 `bob vault`: defer (against cdx and gem)

- `vault-sync` already carries its noun.
- `nightly` is a cron verb.
- These are the most automation-bound names (15 s LaunchAgent, systemd, athena cron,
  README integration notes).
- `bob vault sync` would add another "sync" under yet another parent.

A "Vault" help section gives the grouping without the risk. Reopen if a third
vault-level command arrives (e.g. a conflicts or doctor view). gem's
`bob vault nightly` alongside a top-level `bob nightly` is rejected: it creates two
visible spellings.

## 6. Recommended solution

**Phase 1 — help and completion only (no argv change; most of the value).**

1. Add a `section` to each `Subcommand` row, replacing `CompletionTier`. Render the
   command listing from the table in the root help template. Sections in workflow order,
   A–Z within each.
2. In `-h`, collapse the 10 protocol endpoints to a one-line pointer. In `--help`, list
   them with descriptions in a final "Capture protocol" section.
3. Cut `AFTER_HELP` to about 8 porcelain examples. Move protocol examples into each
   endpoint's own `--help`.
4. Fix `bob help <cmd>` so it shows the leaf's real help, not the delegate stub.
5. Render `bob <TAB>` groups with the same section names, so help and completion teach
   one map.
6. Label bare defaults in help, e.g. `vault-sync` "(default: run)". cld found bare
   `bob vault-sync` is a writer, unlike every other group's bare form.
7. Hide `freshness seed` from help and completion; it stays callable with its guards.
   `docs/freshness.md` says the seed "was a one-time cutover and must not be re-run".
8. Amend `cli_rules.md` (R5) via `/sase_memory_write`.

**Phase 2 — two narrow namespaces, every old spelling a permanent silent alias.**

- `bob task {archive,reconcile,reroll}`. Bare `bob task` prints help and does nothing;
  there's no default because all three members are writers.
- `bob pomodoro {notify,status,tmux}`, with bare `bob pomodoro` = `status`. This is
  safe: `pomodoro` takes only flags (`-d`, `-s`, `-v`) and `notify` takes numeric
  positionals, so a first-token dispatch can't collide.
- Rule for groups: **a bare group may default only to a read-only view.** `vault-sync`
  is a grandfathered exception, labeled in help.
- **No deprecation output, TTY or not.** The Mac crontab routes stderr to cron mail, so
  any non-TTY notice would mail every 15 minutes. Hand-typing of these names is rare
  (cld's history data), so a TTY-only hint adds test surface for little benefit. Teach
  the new names through help, completion, the README, and a migration table.

**Phase 3 — optional cleanup, never a prerequisite.** Move chezmoi shims, `tmux.conf`,
the Mac crontab, the bob-plugins notice string, and docs/memory mentions to the
canonical names when convenient. Remove the stale `bob_dataview` skill. File R8's
consistency items as separate beads.

### 6.1 Implementation notes (merged from cdx and cld)

- **Table model.**
  `Subcommand { name, about, section, target: Leaf{native, script} | Group{members, default} }`,
  plus `ALIASES: &[(&[&str], &[&str])]` mapping an old argv prefix to a canonical path.
  Rewrite aliases before clap parses, so the clap tree has no hidden duplicates.
- **Argument handling.** Preserve non-UTF-8 `OsString` args and `--` boundaries, and
  never route through a shell string.
- **Script fallback.** Select the leaf *before* checking the script fallback, so
  `BOB_CLI_USE_SCRIPT=1` still sends `pomodoro tmux` to the `tmux_bob_pomodoro` asset.
- **No shared parent options.** In particular there's no `task --bob-dir`: `randomize`
  deliberately lacks `--bob-dir` because its Git sync is bound to `BOB_DIR`
  (`docs/randomize.md:41-43`).
- **Usage names.** Leaf parsers embed a flat `COMMAND_NAME`. Pass a display path so
  `bob task reroll --help` prints canonical usage. `notify` currently prints
  `usage: bob_notify`.
- **Completion.** `tree()` mounts the groups. `present.rs` switches from the tier pair to
  sections. Path-keyed value decisions in `kinds.rs` need the new paths. Hidden aliases
  stay out of candidates but keep option completion once typed.
- **Tests.**
  - Old/new byte-identical stdout, exit code, and fixture effects for every alias.
  - Every `NativeCommand` reachable through exactly one canonical path.
  - Sorted within section.
  - `-h`/`--help` snapshots.
  - Capture-text regressions for `parse`/`complete`/`tasks`/`api`.
  - Timer stdout parity, including `--show-stale`.
  - `install-smoke` keeps `capture-*` `--help`.
- **Size.** Phase 1 is one focused change (runner, completion presentation, tests,
  README Commands table, CLI-rule amendment). Phase 2 is two: groups plus aliases, then
  docs.

## 7. Recommended reorganization of `bob`

### 7.1 Target `bob -h`

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
  task        Bulk task maintenance: reconcile statuses, re-roll due tasks, archive done

Vault:
  nightly     Run nightly maintenance: vault-sync, task archive, vault-sync
  query       Run Dataview or Tasks queries against the vault
  vault-sync  Reconcile the vault through Git (default: run) or show status

Integrations:
  gkeep       Drain the Google Keep inbox into Obsidian tasks
  highlights  Sync Highlights PDF annotations into reference notes

Setup:
  completion  Install and inspect shell completion for bob
  plugins     List and deploy Bob's custom Obsidian plugins

Capture protocol (JSON endpoints for Bob Mac Capture; `bob --help` describes them):
  capture-complete  capture-parse  capture-pomodoro-name  capture-pomodoros
  capture-rewrite  capture-sections  capture-targets  capture-task-id
  capture-task-sections  capture-tasks

Examples:
  bob capture buy milk @groceries     Capture a task into groceries.md
  bob capture '='                     Start the queued Pomodoro
  bob plan                            Show today's plan budget and lanes
  bob freshness                       List the review queue
  bob ready                           Show Ready lanes against the per-note cap
  bob task reconcile --dry-run        Preview task status reconciliation
  bob query --source '#project'       Print matching note paths
  bob vault-sync status --json        Print the last vault Git sync status
```

### 7.2 Full tree and old → new map

```text
bob
├── capture [OPTIONS] [TEXT]...            unchanged; free-text grammar untouched
├── completion {bash, install, status*, uninstall, zsh}
├── freshness {list*, seed†}               † hidden from help after the one-time cutover
├── gkeep {doctor, list*, login, pull}
├── highlights {clip, create, doctor, marker, scan, sync}
├── nightly                                unchanged (cron verb)
├── plan                                   unchanged
├── plugins {list*, sync}
├── pomodoro                               bare = status
│   ├── notify                             ← notify
│   ├── status                             ← pomodoro
│   └── tmux                               ← tmux-pomodoro
├── projects {list, sync}
├── query                                  unchanged
├── ready                                  unchanged
├── task                                   bare = help; no default
│   ├── archive                            ← move-done-tasks
│   ├── reconcile                          ← task-status-hooks, task-status-setter, mark-next-tasks
│   └── reroll                             ← randomize
├── vault-sync {run*, status}              bare = run (grandfathered writer default)
└── capture-* (10)                         unchanged names; last help section
                                           (* = default subcommand)
```

| Old invocation | Canonical | Old spelling |
| --- | --- | --- |
| `bob task-status-hooks`, `task-status-setter`, `mark-next-tasks` | `bob task reconcile` | hidden alias, permanent |
| `bob move-done-tasks` | `bob task archive` | hidden alias, permanent |
| `bob randomize` | `bob task reroll` | hidden alias, permanent |
| `bob tmux-pomodoro` | `bob pomodoro tmux` | hidden alias, permanent |
| `bob notify` | `bob pomodoro notify` | hidden alias, permanent |
| `bob pomodoro [flags]` | `bob pomodoro [status] [flags]` | unchanged |
| `bob_pomodoro`, `bob_notify`, `tmux_bob_pomodoro` binaries | unchanged | unchanged |
| all 10 `capture-*`, and every other command | unchanged | n/a |

Result: 14 root entries in 5 sections instead of 28 flat peers. The README review trio
and the Pomodoro tools sit together on the first screen. The three opaque writers gain a
noun that predicts where they live. And not one existing invocation changes behavior.

## 8. Open questions for Bryan

1. `bob task reroll` or `bob task randomize`? This report recommends `reroll` (§5.3).
2. `reconcile` or keep the doc concept's word (`bob task hooks`)? This report recommends
   `reconcile`. The concept and `docs/task-status-hooks.md` can keep their name, and the
   immutable decision records that cite `bob task-status-hooks` stay accurate through the
   alias.
3. Hide `freshness seed` now (recommended), or keep it visible for a hypothetical second
   vault?
4. Do you hand-type `plan`/`ready`/`freshness` often on the Mac? The recommendation
   doesn't depend on it, but it would confirm the decision to keep them top-level.

## 9. Sources

- Input reports (this directory): `__cdx` (selective namespaces, capture-grammar probes,
  `bob help` stub, chezmoi caller inventory); `__cld` (help sections, narrow task rule,
  athena history, stale-rename callers, clap heading limits); `__grk` (git-style help,
  porcelain/plumbing, case against a `task` folder); `__gem` (Pomodoro triad,
  ecosystem matrix).
- Lead verification (2026-10-04):
  - bob-cli `src/runner.rs` (`SUBCOMMANDS`, `HIDDEN_SUBCOMMAND_ALIASES`, `AFTER_HELP`,
    `build_cli`)
  - `src/native/nightly.rs` (`STEPS`)
  - `src/native/completion/present.rs`
  - `docs/vault-git-sync.md:15-24,113-146`
  - `docs/freshness.md:737`
  - `README.md` (Daily workflow, Migration notes)
  - live `bob help plan`, `bob plan --help`, `bob pomodoro --help`, `bob notify --help`,
    `bob dataview`
  - `~/.cargo/registry/.../clap_builder-4.6.7/src/builder/command.rs`
  - bob-mac-capture `Sources/` @ `52b3360`
  - bob-plugins string grep
  - `sase/memory/cli_rules.md` (audited read)
- External: [clig.dev](https://clig.dev/);
  [git command categories](https://git-scm.com/docs/git#_git_commands);
  [GitHub CLI manual](https://cli.github.com/manual/gh);
  [Docker 1.13 management commands](https://www.couchbase.com/blog/docker-1-13-management-commands/);
  clap [#1553](https://github.com/clap-rs/clap/issues/1553),
  [#5828](https://github.com/clap-rs/clap/issues/5828),
  [PR #5819](https://github.com/clap-rs/clap/pull/5819).
  These were cited by the input reports; the lead didn't re-fetch them.
