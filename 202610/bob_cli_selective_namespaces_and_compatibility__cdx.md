# Organizing bob around workflows, task operations, and a stable capture API

Researcher: cdx  
Research date: 2026-10-04  
Scope: independent research and a proposed command organization; no implementation changes.  
Source baseline: bob-cli commit `4e510cf50c3d11908e0b858520958e24a6d76abe`.

## Decision

**Yes, selectively grouping commands is a good idea. Add `bob task`, but address the capture helper commands first.** Keep `bob capture` and `bob plan` as direct daily actions. Put the ten capture frontend endpoints under a separate `bob capture-api` namespace, put backlog operations under `bob task`, consolidate timer reporting under `bob pomodoro`, and consolidate Git maintenance under `bob vault`. Preserve every existing valid invocation through compatibility routing.

The main issue is that the root mixes daily actions, task reports, integration families, scheduled maintenance, and frontend endpoints. A task group alone reduces the root from 28 commands to 24 and leaves the ten capture helpers occupying the first part of help. The complete proposal below has 12 advertised root commands, while preserving the same capabilities.

This is a recommendation about discovery and naming. It does not require new task CRUD operations, different task semantics, new JSON versions, or a rewritten capture language.

## What I examined, and the limits of the evidence

I inspected the command registry and dispatch in `src/runner.rs`, native command routing, the shell completion tree and presentation code, existing help tests, README command descriptions, and the capture, planning, freshness, randomization, status-hook, and sync contracts. I also ran installed `bob --help` and command-specific help. The 28 command names in the source registry all appeared in the installed root help; this verifies inventory agreement, not that the installed binary was built from this exact commit.

I opened the linked chezmoi and bob-plugins repositories through `sase repo open`. Chezmoi was at `3e2da60320db3acc932aa440347cdc56fdee051b`; bob-plugins was at `c2898cca19f427185e2ab8b007c210a3ded87f21`. I read project rules and relevant memory through audited `sase memory read` calls, including the thin-client architecture and sticky-lane decisions.

Opening bob-mac-capture failed because its configured primary checkout did not exist. Therefore Mac Capture's current source and every current subprocess call remain unaudited here. The accepted thin-client decision explicitly documents its use of capture parse/completion endpoints and `capture --dry-run`; that establishes a compatibility obligation, but does not substitute for a full implementation inventory.

External comparisons used primary documentation and the authors' own CLI design guide. I did not read or request another swarm researcher's report, transcript, or conclusions. I did not inspect unrelated prior research artifacts. The linked repositories were read-only, and dry-run capture probes used a temporary fixture inside this workspace, removed afterward.

There is no command-frequency telemetry or user study in this research. Statements about easier discovery are design judgments grounded in the current command surface. The inventory counts and compatibility examples below are observed facts.

## The actual source of complexity

### The root has 28 commands, including ten capture endpoints

The registry labels ten `capture-*` commands as `CompletionTier::Plumbing`, while the other 18 are `Porcelain`. Shell completion already places the helpers last in a separate `capture protocol` group. Root help does not use that separation: its alphabetical command list starts with `capture` followed by ten helper commands. Installed root help had 96 lines, including nine capture-helper examples. This is an existing audience distinction that help currently obscures. [Command registry and root help construction](https://github.com/bobs-org/bob-cli/blob/4e510cf50c3d11908e0b858520958e24a6d76abe/src/runner.rs#L22), [completion presentation](https://github.com/bobs-org/bob-cli/blob/4e510cf50c3d11908e0b858520958e24a6d76abe/src/native/completion/present.rs#L392).

Those endpoints are useful to developers and can have human-readable output. Their placement should reflect their role, rather than imply that they are unsupported private internals. Two also write: `capture-task-id` assigns an ID using a stale-safe task reference, and `capture-pomodoro-name` names an open ledger entry. A new API group must label their mutation behavior accurately. [ID assignment contract](https://github.com/bobs-org/bob-cli/blob/4e510cf50c3d11908e0b858520958e24a6d76abe/src/native/capture_task_id.rs#L66), [Pomodoro naming implementation](https://github.com/bobs-org/bob-cli/blob/4e510cf50c3d11908e0b858520958e24a6d76abe/src/native/capture_pomodoro_name.rs#L1).

### bob already has sensible command families

`completion`, `gkeep`, `highlights`, `plugins`, and `projects` already group related operations. Their existing children should be retained. For example:

| Existing family | Existing substantive children |
| --- | --- |
| `completion` | `bash`, `install`, `status`, `uninstall`, `zsh` |
| `freshness` | `list`, `seed`; bare invocation defaults to list |
| `gkeep` | `doctor`, `list`, `login`, `pull` |
| `highlights` | `clip`, `create`, `doctor`, `marker`, `scan`, `sync` |
| `plugins` | `list`, `sync` |
| `projects` | `list`, `sync` |
| `vault-sync` | `run`, `status`; bare invocation defaults to run |

Observed through command help and the [README index](https://github.com/bobs-org/bob-cli/blob/4e510cf50c3d11908e0b858520958e24a6d76abe/README.md#L189). Generated `help` entries are omitted from these inventories.

This argues for extending the existing model, rather than reorganizing all features into new umbrellas such as `integrations`, `system`, `manage`, or `maintenance`.

### Similar-looking task commands have different jobs

| Command | Actual behavior relevant to grouping |
| --- | --- |
| `plan` | Read-only report combining today's Pomodoro themes/link budget, Today-linked tasks, and Next/Pending lane counts |
| `freshness list` | Read-only review queue; includes ordinary tasks and project/reference tracker rows |
| `freshness seed` | One-time cutover mutation, with explicit preview/force controls |
| `ready` | Read-only per-note Ready-lane cap report and optional note worklist |
| `randomize` | Bulk re-roll of due prioritized tasks' scheduled dates; normal runs coordinate Git sync and commit |
| `task-status-hooks` | Reconcile task promotion, dependencies, derived Blocked state, and ledger structure |
| `move-done-tasks` | Archive completed/canceled task blocks and repair links/identities; Git-backed runs also commit and push |

Sources: [plan and Ready contract](https://github.com/bobs-org/bob-cli/blob/4e510cf50c3d11908e0b858520958e24a6d76abe/docs/plan.md), [freshness CLI](https://github.com/bobs-org/bob-cli/blob/4e510cf50c3d11908e0b858520958e24a6d76abe/docs/freshness.md#L682), [randomize contract](https://github.com/bobs-org/bob-cli/blob/4e510cf50c3d11908e0b858520958e24a6d76abe/docs/randomize.md#L1), [status reconciliation](https://github.com/bobs-org/bob-cli/blob/4e510cf50c3d11908e0b858520958e24a6d76abe/docs/task-status-hooks.md#L1), [archival effects](https://github.com/bobs-org/bob-cli/blob/4e510cf50c3d11908e0b858520958e24a6d76abe/README.md#L808).

`task` is therefore a useful namespace for backlog inspection and operations. It should not promise a conventional task database with `add`, `delete`, `start`, and `complete` verbs. Bob's task and Pomodoro mutations already compose through capture grammar and editor gestures.

## Critique of the proposed direction

### Grouping is useful when the parent predicts the next command

A user who wants to reconcile task state can reasonably look under `task`. A user who wants timer notification can look under `pomodoro`. `notify` is currently vague at the root, despite being specifically a Pomodoro notifier. `vault-sync` and `nightly` both operate the vault's Git maintenance workflow.

In contrast, `plan` is a cross-cutting view of today's work. Keeping `bob plan` is justified by its meaning and current documented daily workflow, even without frequency measurements. `bob capture` likewise supports tasks, bullets, attachments, and session operators; placing it under `task` would narrow its apparent scope.

### A tidy hierarchy can make an interface worse

Extra parents increase typing and add opportunities to guess the wrong category. Most of Bob already concerns tasks in some way: projects have tracker tasks, Highlights yields reference tasks, Keep pulls tasks, and Pomodoros reference tasks. That is insufficient reason to put all of them under `task`.

A broad `task` group containing capture, query, projects, sessions, and synchronization would become another sprawling root. A generic `maintenance` group would split features by implementation timing and create ambiguous ownership: randomize and archival are maintenance, but are primarily task operations. Group by the user's object or goal.

The existing plural `projects` and `plugins` names need not become singular just because the new group is `task`. That additional churn has no demonstrated discovery benefit.

### The clean-looking capture nesting proposal has a real grammar collision

Avoid introducing `bob capture parse`, `bob capture tasks`, or even `bob capture api ...` while preserving default free-text capture. Today, the following words are valid capture text without an end-of-options marker:

| Text passed after capture options | Observed dry-run result |
| --- | --- |
| `parse` | `kind: task`, `text: parse` |
| `complete` | `kind: task`, `text: complete` |
| `tasks` | `kind: task`, `text: tasks` |
| `parse invoices` | `kind: task`, `text: parse invoices` |
| `api design` | `kind: task`, `text: api design` |

I ran `bob capture --dry-run --format json <text>` against an isolated fixture with an empty config, fixed `BOB_NOW`, and an inbox containing `## Tasks`. All five returned exit 0 and left the fixture inbox unchanged.

A parser that treats a leading known word as a helper subcommand changes these valid invocations. Quoting does not solve it: the shell removes the quotes before the program sees the word. Requiring `--` for newly reserved words would be a capture grammar breaking change.

`bob capture add TEXT` could make future nesting unambiguous, but it would require a much larger default-input migration. It is unjustified for this task. A separate `capture-api` group keeps the short free-text interface intact and unambiguously collects its protocol endpoints.

### Better help is a viable alternative and should precede migration

If Bryan mostly wants a less intimidating index, audience separation and fewer root examples may be enough. Matching root help to the existing completion tiers is lower risk than moving commands.

There is also an observed help defect relevant to discovery: `bob help plan` currently prints the root delegation stub, `Usage: bob plan [args]...`, without the native command's flags. `bob plan --help` prints the real help. A new hierarchy needs genuine help at every parent and leaf; nesting alone will not fix this. The reason is that runtime's root builds delegation nodes, while native commands parse their own arguments. [Root parsing](https://github.com/bobs-org/bob-cli/blob/4e510cf50c3d11908e0b858520958e24a6d76abe/src/runner.rs#L286), [delegation builders](https://github.com/bobs-org/bob-cli/blob/4e510cf50c3d11908e0b858520958e24a6d76abe/src/runner.rs#L465).

## What external examples suggest

The CLI Guidelines recommend consistent nested naming, often noun followed by operation, and describe additive interface evolution and explicit aliases. Their warning about catch-all inputs is directly relevant to free-text capture. These are design principles, not proof that Bob needs any particular namespace. [CLI Guidelines: subcommands](https://clig.dev/#subcommands), [future-proofing](https://clig.dev/#future-proofing).

GitHub CLI demonstrates a mixed interface: object families such as `issue` and `repo` coexist with direct actions such as `browse` and `status`, and the manual separates command audiences/categories. That supports keeping Bob's daily actions while adding domain families. [GitHub CLI manual](https://cli.github.com/manual/gh).

Git distinguishes user-facing porcelain from lower-level plumbing and exposes a common-command help view alongside an exhaustive list. This supports cleaning help without forcing every command into a hierarchy. [Git command categories](https://git-scm.com/docs/git#_git_commands), [git help](https://git-scm.com/docs/git-help).

Clap 4.6.6 supports hidden commands and hidden aliases. However, a command alias names a sibling command; it does not itself translate a flat command into a multi-token nested path. Bob needs compatibility routing backed by its command identifiers. [Clap Command API](https://docs.rs/clap/4.6.6/clap/struct.Command.html#method.alias), [hide](https://docs.rs/clap/4.6.6/clap/struct.Command.html#method.hide).

## Alternatives considered

These assessments are qualitative. Root counts follow directly from the current inventory and the explicit mappings in this report; they do not measure usability.

| Option | Advertised root commands | Benefit | Main cost / judgment |
| --- | ---: | --- | --- |
| Improve help only | 28 | Lowest compatibility risk; clarifies audiences | Leaves the flat command structure; good immediate first step |
| Add only task group | 24 | Makes backlog operations easier to find | Misses the dominant capture-helper clutter |
| Group only capture helpers | 19 | Largest single reduction; respects an existing code distinction | Leaves task and timer names dispersed |
| Capture API plus task group | 15 | Best initial structural milestone | Timer and vault maintenance remain split |
| Selective complete proposal | 12 | Coherent task, timer, vault, and frontend families; daily actions remain direct | Requires dispatch/help/completion migration; recommended destination |
| Uniform noun-first hierarchy for everything | Depends on design | Superficially regular | Adds low-value parents and risks changing capture input; reject |

## Explicit adjustments to the requirements

1. **Optimize discovery and correct command choice, rather than the smallest root count.** Retain direct daily actions and established integration families. The 12-command root is a consequence, not the primary success criterion.
2. **Include frontend endpoints in the scope.** `task` is useful, but the ten capture helpers are the strongest grouping opportunity.
3. **Make the migration additive.** New canonical paths can replace old names in help while old invocations keep working. No default removal deadline; independently installed clients and scheduled automation make permanent lightweight compatibility routing preferable.
4. **Preserve capture grammar, output contracts, and operational effects.** No task-status model, JSON schema, schedule policy, sync behavior, or global-flag changes are bundled into this reorganization.
5. **Include help and shell completion as implementation requirements.** Correct routing alone is insufficient if help is a stub or completion still advertises obsolete paths.
6. **Do not invent new task operations to make the tree look complete.** A generic `task review` might imply that the CLI marks tasks reviewed, but current freshness list is inspection; seed is cutover. Preserve that distinction.

These adjustments narrow implementation risk while expanding the discovery work to the place with the clearest evidence.

## Complete current-to-proposed mapping

All 28 existing advertised root commands are represented. `…` means retain the command's existing options, arguments, and any child commands.

| Existing command | Recommended canonical command | Reason / scope |
| --- | --- | --- |
| `capture …` | `capture …` | Keep free-text capture and session grammar unchanged |
| `capture-complete …` | `capture-api complete …` | Capture editor completion endpoint |
| `capture-parse …` | `capture-api parse …` | Semantic preview endpoint |
| `capture-pomodoro-name …` | `capture-api pomodoro-name …` | Stale-safe naming mutation used by capture clients |
| `capture-pomodoros …` | `capture-api pomodoros …` | Capture client's ledger picker |
| `capture-rewrite …` | `capture-api rewrite …` | Capture draft rewrite endpoint |
| `capture-sections …` | `capture-api sections …` | Routed-note picker |
| `capture-targets …` | `capture-api targets …` | Capture route picker |
| `capture-task-id …` | `capture-api task-id …` | Stale-safe ID assignment mutation |
| `capture-task-sections …` | `capture-api task-sections …` | Parent-task section picker |
| `capture-tasks …` | `capture-api tasks …` | Tasks in a capture route, not a general vault task list |
| `completion …` | `completion …` | Retain shell completion family |
| `freshness …` | `task freshness …` | Retain list/seed semantics and bare list default |
| `gkeep …` | `gkeep …` | Retain provider-specific workflow |
| `highlights …` | `highlights …` | Retain PDF/reference workflow |
| `move-done-tasks …` | `task archive …` | Name the user goal; retain archival and link/Git effects |
| `nightly …` | `vault nightly …` | Retain sync → archive → sync orchestration |
| `notify …` | `pomodoro notify …` | State which object notifications concern |
| `plan …` | `plan …` | Keep the cross-cutting daily report direct |
| `plugins …` | `plugins …` | Retain deployment family |
| `pomodoro …` | `pomodoro status …` | Explicit status operation; bare pomodoro remains status |
| `projects …` | `projects …` | Retain lifecycle owner for project notes |
| `query …` | `query …` | Retain general Dataview/Tasks query entry point |
| `randomize …` | `task randomize …` | Retain existing bulk scheduled-date re-roll, not priority shuffle |
| `ready …` | `task ready …` | Keep Ready-lane/cap terminology; this is a report |
| `task-status-hooks …` | `task reconcile …` | User-facing verb for reconciliation, not arbitrary status setting |
| `tmux-pomodoro …` | `pomodoro tmux …` | Timer's existing tmux presentation |
| `vault-sync …` | `vault sync …` | Retain run/status operations and implicit run |

Retain hidden `mark-next-tasks` and `task-status-setter` mappings to the same reconciliation handler. Retain installed `bob_pomodoro`, `bob_notify`, and `tmux_bob_pomodoro` binaries and their native/script fallback behavior. Leave hidden shell endpoint `bob __complete` in place.

Why not move `capture-api tasks` or `capture-api task-id` under task? Their route selectors, picker semantics, and stale-safe frontend references belong to one capture contract. A future general `task list` or `task id` would need its own user-facing contract; merely renaming these endpoints would overpromise their scope.

Why keep the word freshness? It is established project vocabulary and includes a real `seed` operation. Calling the family `review` is conceivable, but it obscures the stored freshness policy and increases rename scope. Use help text such as “Inspect tasks due for review; seed the freshness cutover.”

Why archive rather than collect or clean? “Archive completed and canceled task blocks; repair links” states the outcome. Its detailed help must also describe Git commit/push effects. Why reconcile rather than status-set? Blocked remains derived, Next/Pending remain sticky, and the handler also cleans ledger structure. The name must not imply a new arbitrary-status writer.

## Implementation and migration considerations

### Command routing

The runtime root currently parses only the first command and forwards `OsString` arguments to a native handler. Completion separately mounts each native command's clap builder or a descriptor for hand-parsed commands. This is a manageable refactor, but adding parent words to a string table alone will not work. [Runtime dispatch](https://github.com/bobs-org/bob-cli/blob/4e510cf50c3d11908e0b858520958e24a6d76abe/src/runner.rs#L286), [completion tree](https://github.com/bobs-org/bob-cli/blob/4e510cf50c3d11908e0b858520958e24a6d76abe/src/native/completion/tree.rs#L1).

Represent each canonical command path as components, linked to a stable internal command ID such as the existing `NativeCommand` variant. Keep a separate compatibility-path registry pointing to the same IDs. Derive namespace help and completion mounting from the same metadata. A two-level path adapter can invoke existing leaf handlers; a complete conversion of every native parser is not necessary.

Compatibility handling must preserve arbitrary non-UTF-8 arguments and `--` boundaries, and must never dispatch via a shell command assembled from strings. Use the same native handlers and existing script-fallback mapping. Select the leaf before checking fallback, so `pomodoro notify` and `pomodoro tmux` still reach their own shell assets when explicitly requested.

Do not silently create shared parent options. In particular, randomize intentionally has no `--bob-dir` because its Git-sync context is bound to `BOB_DIR`. A convenient `task --bob-dir` could otherwise send task edits and sync to different vaults. Preserve each leaf's existing flags and defaults. [Randomize flag constraint](https://github.com/bobs-org/bob-cli/blob/4e510cf50c3d11908e0b858520958e24a6d76abe/docs/randomize.md#L41).

### Help and completion

Keep public command and option lists alphabetical, in accordance with the audited CLI rules. Improve discovery through concise descriptions and workflow examples, rather than replacing alphabetic order with a guessed popularity ranking.

Keep about five root examples: capture a task, show today's plan, inspect review candidates, check timer status, and inspect vault sync status. Put capture API examples in `capture-api --help` and detailed client documentation.

Bare `task`, `vault`, and `capture-api` should print help and perform no operation. Preserve bare `pomodoro` as status, and support its existing flags alongside explicit `pomodoro status`. Preserve the existing default `task freshness` → list and `vault sync` → run.

Every `--help` path and `bob help <path>` should lead to real namespace or leaf help. Native builders currently embed flat `COMMAND_NAME` strings in help, errors, and examples. Supply a canonical display path or deliberately update those strings; otherwise the new route will still teach the old command. Protect actual machine output separately from help presentation.

Completion must be updated beyond the composed tree. `present.rs` recognizes capture text by the first path component; that condition needs to recognize the new parse/rewrite paths. `kinds.rs` keys some completion decisions by exact path, notably distinguishing a new authored block ID from an existing task ID. Update these selectors, context walking, and coverage tests. Keep hidden aliases absent from root suggestions, and retain option/value completion after an old spelling is explicitly typed. The shell adapter protocol can remain version 1; command candidates changing is the purpose of its live tree. [Capture text detection](https://github.com/bobs-org/bob-cli/blob/4e510cf50c3d11908e0b858520958e24a6d76abe/src/native/completion/present.rs#L178), [path-specific value decisions](https://github.com/bobs-org/bob-cli/blob/4e510cf50c3d11908e0b858520958e24a6d76abe/src/native/completion/kinds.rs#L1), [completion contract](https://github.com/bobs-org/bob-cli/blob/4e510cf50c3d11908e0b858520958e24a6d76abe/docs/completion.md).

### Real callers and compatibility

The chezmoi checkout contains concrete consumers:

| Consumer | Current invocation |
| --- | --- |
| `home/dot_hammerspoon/init.lua:496` | `bob pomodoro --show-stale` |
| `home/dot_config/tmux/tmux.conf:42` | `bob tmux-pomodoro` |
| `home/bin/executable_bob_vault_sync_watch:12` | `bob vault-sync -q` |
| `home/Library/LaunchAgents/com.bbugyi.bob-vault-sync.plist:12` | `vault-sync` and `-q` as process arguments |
| `home/bin/executable_bob_pomodoro` | Wrapper forwarding to `bob pomodoro` |
| `home/bin/executable_bob_notify` | Wrapper forwarding to `bob notify` |
| `home/bin/executable_tmux_bob_pomodoro` | Wrapper forwarding to `bob tmux-pomodoro` |

Paths refer to chezmoi commit `3e2da60320db3acc932aa440347cdc56fdee051b`. The Hammerspoon consumer parses timer output, so even nominally human-readable status is a real integration contract.

Keep these callers functioning before updating their configuration. Mac Capture and bob can be installed independently; legacy capture endpoints should continue working indefinitely unless a later inventory justifies removal. Do not emit recurring deprecation warnings from timers, pollers, or parse/completion endpoints. Document the preferred spelling once in migration notes.

Read-only searches in the plugin source did not establish direct subprocess consumers of the proposed moved names. This is a bounded negative finding, not proof that no plugin/runtime integration exists. The audit should cover all actual clients before any compatibility removal.

### Rollout order

1. First improve root help using the existing workflow/API distinction, trim frontend examples, and fix real leaf-help dispatch. This makes immediate progress without requiring clients to move.
2. Add the `capture-api` routes and `task` routes, backed by existing handlers and compatibility entries. Update completion and docs in the same release. The advertised root then has 15 commands.
3. Add the `pomodoro` children and `vault` namespace, preserving bare timer status and every old spelling. The destination has 12 advertised root commands.
4. Update known caller configurations and Mac Capture when convenient. This is cleanup, not a prerequisite for using the new CLI, and aliases need no automatic expiration.

The last consolidation can follow separately if Bryan wants a smaller initial change. It remains my recommended destination because `notify` and `nightly` currently require knowledge of their implicit domains.

### Verification that would justify shipping

The research itself did not implement or run the repository test suite. An implementation should exercise these substantive contracts:

- Table-driven old/new routing parity for every moved endpoint and retained compatibility binary: same options, result schemas, exits, and fixture changes.
- Capture regression fixtures for ordinary drafts beginning with `parse`, `complete`, `tasks`, and `api`, both with and without `--`; aggregate capture behavior must remain intact.
- Canonical help and help-command routing at parent and leaf depth; alphabetic order, accurate read/write descriptions, and no obsolete root examples.
- Nested zsh/bash completion for `capture-api parse` text, task references versus authored IDs, `task randomize --level`, and existing provider/default-subcommand behavior; completion remains read-only.
- Exact timer/tmux stdout parity, existing legacy shims, `--show-stale` handling, and `BOB_CLI_USE_SCRIPT=1` fallback.
- Preserve review-list versus seed behavior, Ready's crowded `--check` exit 3, task reconciliation invariants, and maintenance lock/sync/archival effects.

There is no reason to rerun long live-vault mutations just to test naming. Use the existing fixtures and parity suites. A short user walkthrough should compare finding a due-review list, inspecting a crowded note, reconciling state, obtaining timer status, and checking sync. Success means the appropriate parent and leaf are easier to find without losing the short capture/plan workflow; count reductions alone do not establish that.

## Recommended solution and final command organization

**Implement a backward-compatible, selective namespace reorganization.** Start with help plus capture API separation, add `task` for backlog operations, and complete the timer/vault consolidation. Keep capture grammar, JSON contracts, existing task semantics, integration families, and all old callable spellings.

The recommended advertised tree is below. Existing flags and default operations remain; generated `help` entries and hidden compatibility routes are omitted.

```text
bob
├── capture [OPTIONS] [TEXT]...
├── capture-api
│   ├── complete
│   ├── parse
│   ├── pomodoro-name
│   ├── pomodoros
│   ├── rewrite
│   ├── sections
│   ├── targets
│   ├── task-id
│   ├── task-sections
│   └── tasks
├── completion
│   ├── bash
│   ├── install
│   ├── status
│   ├── uninstall
│   └── zsh
├── gkeep
│   ├── doctor
│   ├── list
│   ├── login
│   └── pull
├── highlights
│   ├── clip
│   ├── create
│   ├── doctor
│   ├── marker
│   ├── scan
│   └── sync
├── plan
├── plugins
│   ├── list
│   └── sync
├── pomodoro                 # bare invocation remains status
│   ├── notify
│   ├── status
│   └── tmux
├── projects
│   ├── list
│   └── sync
├── query
├── task
│   ├── archive
│   ├── freshness            # bare invocation remains list
│   │   ├── list
│   │   └── seed
│   ├── randomize
│   ├── ready
│   └── reconcile
└── vault
    ├── nightly
    └── sync                 # bare invocation remains run
        ├── run
        └── status
```

This preserves the two concise daily entry points, gives task operations an obvious home, and removes ten frontend commands from the main workflow index without reserving any capture text.
