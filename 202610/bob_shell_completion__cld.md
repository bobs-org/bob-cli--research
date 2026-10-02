# Shell Completion For `bob` — Research, Critique, And Recommended Design

*Researcher: cld · 2026-10-02 · bob-cli `f11a9f8` · clap 4.6.1 / clap_complete 4.6.11 · zsh 5.9*

## TL;DR

- **Yes, build it.** `bob` has 27 visible subcommands. Ten of them are long-named
  `capture-*` endpoints. Across the full tree there are 123 value-taking long options
  (93 of them with no value completion at all today). The most valuable values (capture routes, task block IDs, Pomodoro refs,
  capture markers) live in the vault, where no static script can reach them.
- **Use runtime completion, not generated scripts.** `bob` starts in **4.4 ms**; a
  Python `sase` startup costs 300–640 ms. Almost all of `sase completion`'s machinery
  (loader, `ensure`, runtime grammar cache, `candidates` fast path, stamps, `refresh`)
  exists only to hide that startup cost. For `bob`, the binary itself can be the
  grammar. A small, stable shell adapter calls a hidden `bob __complete` on every
  `<TAB>`, so completion can never go stale relative to the installed binary.
- **Requirement adjustment (called out):** `just install` should **ensure** the
  adapter (`cargo install --path . --locked`, then `<installed bob> completion install`).
  It should not *regenerate a grammar*. Under this design, completion stays correct
  even when `bob` is installed some other way, such as `cargo install --git`, another
  workspace, or a teammate's machine.
- **Prerequisite (called out):** `bob` currently has *no single command tree*. The
  top-level parser treats every subcommand as an opaque trailing-args bag
  (`src/runner.rs:427-438`), 22 modules each build a private clap `Command`, and 5
  commands parse argv by hand. Completion needs one full tree. That needs a small
  refactor first, and it will also improve `--help` consistency.
- **Prototype validated.** I built a throwaway spike in `/tmp`, not in the repo. It
  composes the full tree, runs clap_complete's `unstable-dynamic` engine with bob
  value completers, and uses a ~50-line bob-owned zsh adapter. In a real zsh it
  rendered grouped, headed, described menus for subcommands, flags, routes (grouped
  inbox / areas / projects), `@dev:` task IDs with task text, and static choices.
  Static `<TAB>` took **~5 ms**, route completion **~15 ms**, and `@route:` task
  completion **~10 ms**. Wikilink completion took **~300 ms**, so it is deferred.

## 1. The Ask, Restated

1. Excellent `bob` shell completion, inspired by `sase completion`.
2. A new `just install` target that installs from source with `cargo install` and
   updates completion as part of the same step.
3. A design that is intuitive, reliable, and beautiful.
4. A critique, adjusted requirements (called out), and a recommendation.

## 2. Ground Truth: How `bob` Is Built Today

### 2.1 Two-level parsing means there is no full tree to complete from

- `run_bob()` parses argv with `build_cli()` (`src/runner.rs:403`). Every subcommand is a
  `delegate_subcommand()` with one trailing `args` value, `allow_hyphen_values`, and
  `disable_help_flag` (`src/runner.rs:427`). The top-level tree therefore knows
  subcommand *names* only.
- The real parsers are private `build_cli()` functions in 22 modules (for example
  `src/native/capture_sections.rs:52`). Each one reparses `Vec<OsString>` in its own
  `run()`.
- Five commands parse argv by hand, with no clap tree at all:
  `move-done-tasks` (`collect_done/mod.rs:248`), `nightly` (`nightly.rs:92`),
  `notify` (`notify.rs:78`), `pomodoro`, and `tmux-pomodoro` (`pomodoro.rs:198`). Their
  help output is also visibly different (`usage: bob_notify [-v] …`).
- Two hidden aliases exist (`mark-next-tasks`, `task-status-setter`).

What this means: feeding today's top-level `Command` into `clap_complete` would
complete subcommand names and nothing else. Any good design starts by composing the
full tree.

### 2.2 Value slots

I generated clap's static zsh script for the composed tree. It contains 123
value-taking long options: 93 with no value completion (`_default`) and 30 with static
possible values. It also contains 98 boolean long flags. Positional slots such as
capture `TEXT`, `MD_FILE`, and `PDF` come on top of those. The most repeated slots are `--bob-dir` ×31, `--format`
×24, `--lib-dir`/`--ref-dir`/`--xlib-dir` ×6 each, and `--route` ×5.

### 2.3 Where completion values would come from, and what they cost

All timings are warm runs on apollo against the real `~/bob` vault (5,781 notes),
measured end to end, including process start.

| Source | Command / function | Latency | Usable per keystroke? |
| --- | --- | --- | --- |
| Process start | `bob --version` | 4.4 ms | yes |
| Static tree completion (prototype) | `bob __complete` | ~5 ms | yes |
| Capture routes | `scan_capture_targets` (`capture_targets.rs:220`) | ~15 ms (103 ms cold FS) | yes |
| Open Pomodoros | `capture-pomodoros` scan | ~6–9 ms | yes |
| Capture markers `@route`, `@route:` | `capture_complete::build_result` | ~10–16 ms | yes |
| Wikilinks `[[…` | same engine, wikilink context | **~300 ms** | **no** |
| Plugins | `bob plugins list` (`git pull` refresh) | **~700 ms** | **no**; read `<repo>/plugins/*/` instead |
| Projects | `bob projects list` | **~640 ms** | **no** |
| Plan | `bob plan -f json` | **3.2 s** | **no** |
| Plain vault walk | `find ~/bob -name '*.md'` | 30 ms | borderline |

Per-keystroke cost matters on your machine specifically, because `~/.zshrc` sets
`ZSH_AUTOSUGGEST_STRATEGY=(history completion)`. zsh-autosuggestions' completion
strategy runs the completer while you type, not only on `<TAB>`. Completers therefore
need a latency budget and must be side-effect free.

### 2.4 The capture engine is already a completion service

`bob capture-complete` (`capture_complete.rs:86`) already returns cursor-aware
candidates with replacement ranges for 14 contexts: routes, sections, Pomodoro block
IDs, task block IDs, Pomodoro names, task sections, active tasks, task links, and
wikilinks. Bob Mac Capture uses it today. The decision record
`decisions:mac-capture-is-a-thin-client` anticipates exactly this case: "JSON
endpoints also serve any later client (a Raycast extension, an iOS Shortcut, **zsh
completion**) for free." Shell completion should be the next thin client of that one
grammar implementation, never a second one.

### 2.5 Install drift is real

`~/.cargo/bin/bob` was built 2026-10-01 from a different workspace (`bob-cli_10`).
It already rejects `bob ready` (added in `812c1b1` the same day) and
`bob highlights clip`. A statically generated completion script would drift the same
way. A runtime design is immune to it.

### 2.6 Your zsh environment

- zsh 5.9 with oh-my-zsh. `~/.zfunc` is put first on `fpath` and re-asserted after
  oh-my-zsh loads (`~/.zshrc:19,47`). The managed `~/.zfunc/_sase` lives there, so
  `~/.zfunc/_bob` is the natural target. No `_bob` exists anywhere on `fpath`, and
  there is no bash-completion `bob` either.
- Styles in effect: `menu select`, a case-insensitive plus substring `matcher-list`,
  and `use-cache yes`. There is **no** `descriptions format` and **no** `group-name`,
  so today no completion shows group headers unless the completer supplies defaults
  (see §6.6).
- fish is not installed on apollo. bash 5.2 is.

## 3. What `sase completion` Teaches

| `sase completion …` | Why sase needs it | Does bob need it? |
| --- | --- | --- |
| `zsh` / `bash` / `fish` (print a script) | manual installs, snapshots | **Keep**: print the *adapter* |
| `install` (detect shell, pick a scanned dir, atomic write, zcompile, verify `_comps`, stamp) | first-time setup | **Keep**: this is the core of `just install` |
| `list` (default) | install status | **Keep, renamed `status`**, matching `bob vault-sync status`, and made the default |
| `refresh` | regenerate stale grammars after updates | **Drop**: the adapter never goes stale; `install` is idempotent |
| `loader` / `ensure` + runtime grammar cache | hide 300–640 ms startup | **Drop**: bob starts in 4 ms |
| `candidates KIND [PREFIX]` (pre-argparse fast path) | values without importing the CLI | **Drop**: the binary *is* the fast path; `bob __complete` covers debugging |
| `spec` (JSON snapshot gate) | snapshot tests, Command Line integration | **Drop as a command**; keep the *coverage test* idea in-process |
| `deploy-chezmoi` | chezmoi-managed loaders | **Drop**: the adapter is per-host and tied to the binary that `just install` places |

Lessons worth keeping, all learned the hard way in sase (`docs/completion.md` in the
sase repo):

1. Never `eval "$(… completion zsh)"` from an rc file. Write a file, and never edit rc
   files.
2. A file on disk proves nothing. zsh needs the directory on `fpath` *before*
   `compinit`, and an earlier `_bob` on `fpath` can shadow yours. Verify in a real
   shell.
3. Prefer directories the shell already scans. Framework *plugin* directories and
   caches are off-limits.
4. Path slots are completed by the shell natively, not by the program.
5. Pass the full candidate set and let the shell filter, so one fetch serves the
   whole word.
6. Ship the recommended `zstyle`s, because compsys grouping is opt-in.
7. Real-shell smoke tests catch bugs unit tests cannot (see the two zsh bugs in §5).

One anti-lesson: at a narrow terminal width, `sase completion list` printed its
PATH and DETAIL columns one character per line, so a single table filled several
screens. bob's `status` should use stacked per-shell blocks, not a wide table.

## 4. Options Considered

| | A. AOT static scripts (`clap_complete::aot`) | B. clap `CompleteEnv` as shipped | **C. clap engine + bob-owned protocol and adapters** | D. Hand-written `_arguments` emitter (sase-style) |
| --- | --- | --- | --- | --- |
| How | `bob completion zsh > _bob`, regenerated on install | `COMPLETE=zsh bob` registration; shell calls bob per TAB | adapter calls hidden `bob __complete`; bob post-processes clap's engine output | generate a rich compsys script from the tree |
| Vault values (routes, tasks, Pomodoros, capture markers) | no (all `_default`) | yes | **yes** | only by shelling back into bob |
| Staleness | stale after every CLI change until regenerated | adapter can mismatch the binary; upstream recommends re-sourcing on every shell start | **adapter is protocol-versioned; grammar always live** | stale like A |
| zsh beauty | good (`_arguments`, exclusion lists) | flat: a single `_describe -V values` group; tags dropped (`env/shells.rs:453`) | **grouped headers from tags, ranked order, native files** | best possible, at high cost |
| Code to own | ~0 (50 KB generated zsh, 68 KB bash) | ~0 | ~150 lines of shell + ~600 lines of Rust | 1,000s of lines (sase has ~30 modules) |
| Stability | stable API | `unstable-dynamic` | `unstable-dynamic` (pin exact) | stable |
| Fits "just install updates completion" | literally | weakly | **trivially (idempotent ensure)** | literally |

Also considered and rejected: (E) external spec tools such as carapace or `usage`,
which add a runtime dependency on every host and a second grammar description to keep
in sync. (F) an rc-file `source <(COMPLETE=zsh bob)` line, which is cheap for a 4 ms
binary but edits your chezmoi-managed `.zshrc` and makes `just install` irrelevant.

**Why C beats B:** B is C minus presentation. clap's engine already tags candidates
("Commands", "Options", per-argument tags, and custom tags) and orders them by tag
(`engine/complete.rs:230-241`), but the shipped zsh adapter throws the tags away.
Owning a ~50-line adapter buys group headers, native file completion, scoped default
styles, "no space after `/`", and a stale-adapter message. Those are precisely the
"beautiful" and "reliable" requirements.

**Why C beats A:** A cannot complete vault values, and vault values are the point.
A's one real advantage, zsh `_arguments` exclusion lists, can be reproduced in C with
a post-filter (§6.5).

## 5. Prototype (Evidence, Not Product Code)

I built the spike in a scratch copy (`/tmp/bob-proto-cld`, from `git archive HEAD`).
The workspace checkout was never modified. The spike consisted of:

- `clap_complete = { version = "=4.6.11", features = ["unstable-dynamic"] }`.
- `pub(crate)` on the 22 module `build_cli()` functions. A `completion::tree()` mounts
  each one under its subcommand name. Spec commands stand in for the 5 hand-parsed
  commands.
- An `annotate()` pass that attaches value kinds by argument ID, plus value completers
  for `route`, `pomodoro-ref`, and capture `text`. The `text` completer calls
  `capture_complete::build_result` in-process and splices its replacement range into
  the current word.
- A hidden `bob __complete zsh -- <words…>` that prints `value\tdescription\tgroup\tsuffix`
  lines, or `!dirs` / `!files <glob>` directives.
- zsh and bash adapters. The release rebuild took about 45 s incrementally and 1m47s
  clean.

Real zsh 5.9 output, driven through a pty (`zsh -i`, menu select, your matcher-list):

```text
% bob <TAB>
── commands ──
capture                -- Capture a task or bullet into the Bob vault
capture-complete       -- Complete capture or wikilink syntax at the cursor
capture-parse          -- Explain what in-progress capture text currently means
…
vault-sync             -- Reconcile the Bob vault through Git

% bob capture-sections --route <TAB>
── inbox ──
mac_inbox  -- inbox · default capture target
── areas ──
gkeep_inbox  gtd_daily  cash   body  gtd  fun  dev
vacation     recur      inbox  love  job            -- area
── projects ──
bob_git                 bob
gkeep_gdocs_inbox_dump  bob_gtd                     -- project · wip
…

% bob capture fix it @dev:<TAB>
── pomodoro block id ──
@dev:remote-power   -- Enable remote power on for Athena!
@dev:mac-navy       -- Create new mac app that allows single-key navigation to configured apps!
@dev:menu-bar-ping  -- Render tmux_ping in menu bar!

% bob highlights create --status <TAB>
── status ──
ready      next       wip        read       abandoned  legacy
```

zsh's `list-grouped` collapses candidates that share a description into compact
columns, so grouping areas under one header reads well. That rewards descriptions
that add information (project status) rather than repeat the value.

The spike also surfaced bugs that a production design must avoid:

1. **`emulate -L zsh` inside the completion function breaks `_describe`.** It turns off
   `extendedglob`, so `_describe` passed `compadd` empty match strings. The menu
   rendered, but nothing could be inserted, and `-`-prefixed words got no matches.
   Completion functions must inherit compsys's `_comp_options`.
2. **Tab is an IFS-whitespace character.** `IFS=$'\t' read` collapses empty fields, so
   a missing description shifted every later field. Split with `"${(@ps:\t:)line}"`.
3. **The clap engine re-offers options already used** (`--route` after `--route cash`)
   and options that conflict (`--task` after `--section`). bob needs a post-filter.
4. **A lone `-` yields only short flags.** Add the long forms so zsh shows
   `-b  --bob-dir  -- Bob vault root` on one row.
5. **On an empty word the engine offers every option**, mixed in with subcommands and
   positional values. `_arguments` convention is options only after `-`.
6. **Value completers get no context.** The engine passes only the current word, so
   `--section` cannot see `--route`. The spike scanned the words by hand; production
   should use clap itself (§6.4).
7. **bash splits `@dev:remote-power` at `:`** (`COMP_WORDBREAKS`). The bash adapter must
   reassemble the word from `COMP_LINE`/`COMP_POINT`, as bash-completion's
   `_get_comp_words_by_ref -n :` does.

## 6. Recommended Design

### 6.1 Shape

```text
 zsh/bash  ──TAB──▶  _bob adapter (~50 lines, protocol 1, written by `bob completion install`)
                        │  command bob __complete zsh --protocol 1 -- ${words[1,CURRENT]}
                        ▼
 bob __complete ──▶ completion::tree()            one full clap tree (exhaustive over NativeCommand)
                 ──▶ partial parse (ignore_errors) context: bob-dir, route, task, repo …
                 ──▶ clap_complete::engine::complete  subcommands / flags / values (pinned =4.6.11)
                 ──▶ bob value kinds                 routes, tasks, Pomodoros, capture markers …
                 ──▶ bob post-filter + presenter     rules in §6.5, groups, descriptions
                 ──▶ protocol lines / directives     value\tdesc\tgroup\tsuffix | !dirs | !files … | !message …
```

Principles:

- **One grammar.** Shell adapters never parse bob syntax. `bob` alone decides what a
  word means, the same way Bob Mac Capture works.
- **Binary as grammar.** The adapter is stable. All behavior ships with the binary.
- **The user's style always wins.** Bob sets defaults only where you have set nothing.
- **Never noisy, never slow.** No stderr reaches the prompt, every request has a
  deadline, and completion never writes anything.

### 6.2 Command-line interface

```text
bob completion [COMMAND]

Install shell completion for bob and check that it works. Completion is computed
by the installed bob binary on every <TAB>, so it always matches the bob on your
PATH; the installed shell file is a small adapter that rarely changes.

Commands:
  bash       Print the bash completion adapter
  install    Install or update the completion adapter for your shells
  status     Show installed adapters, their freshness, and the bob they call (default)
  uninstall  Remove completion adapters that bob installed
  zsh        Print the zsh completion adapter

Examples:
  bob completion                    Same as `bob completion status`
  bob completion install            Install for your login shell; refresh any others
  bob completion install zsh -d     Show the zsh install plan without writing
  bob completion status -p          Also probe a real shell for registration
  bob completion zsh > ~/.zfunc/_bob
```

`bob completion install [SHELL]...` (SHELL: `bash`, `zsh`). With no SHELL argument it
targets your login shell (`$SHELL`) plus every shell that already has a bob-written
adapter. The first run installs your shell, and later runs keep every adapter current.

```text
  -d, --dry-run       Print the plan without writing anything
  -f, --force         Overwrite a completion file that bob did not write
  -n, --no-verify     Skip the real-shell registration check
  -q, --quiet         Print only changes and problems
  -t, --target <DIR>  Install into DIR instead of the detected directory
```

`bob completion status [-j|--json] [-p|--probe]` and
`bob completion uninstall [SHELL]... [-d|--dry-run]`. Options are sorted, and every
public long option has a short alias, per `cli_rules`.

The internal endpoint, hidden from help and completion, is
`bob __complete <SHELL> --protocol <N> -- <WORDS>...`. Internal subprocess arguments
are exempt from the short-alias rule.

### 6.3 Protocol 1

- Input is the words up to and including the cursor word. Text after the cursor is
  ignored, which matches zsh's `words[1,CURRENT]`.
- Output is one line per candidate: `value<TAB>description<TAB>group<TAB>suffix`, where
  `suffix` ∈ {`space`, `nospace`}. Order is the display order, which the adapter keeps
  (`_describe -V`).
- Directives are whole lines:
  - `!dirs`
  - `!files <glob>`
  - `!files-in <root> <glob>` (vault-relative paths via `_files -W`)
  - `!message <text>` (free-text slots; for example `TEXT — task text; @route, ^task, #pomodoro`)
- **Version skew is designed in from day one.** If the binary does not support an
  adapter's `--protocol`, it emits
  `!message bob completion is out of date — run: bob completion install`, and the
  adapter shows it with zsh's `_message`. Binaries support the current and previous
  protocol.
- Failures are silent. The adapter discards stderr, and an empty response returns 1, so
  zsh falls through normally. `BOB_COMPLETE_DEBUG=<file>` appends the request, the
  response, and the timing for diagnosis.

### 6.4 One tree, value kinds, and context

- **Tree.** Add `NativeCommand::command(self) -> clap::Command` as an *exhaustive
  `match`*, so a new subcommand cannot compile without a tree. The top-level
  completion tree mounts each one under its `SUBCOMMANDS` name and `about` text, and
  disables clap's auto `help` subcommands. Runtime dispatch stays exactly as it is,
  which keeps the risk low. Migrate the five hand-parsed commands to clap, with parity
  tests on accepted and rejected argv.
- **Kinds.** Keep one table in `native/completion/kinds.rs` keyed by
  `(command path pattern, arg id)`, most specific entry first. A path-qualified key is
  required because one arg ID can mean different things. `--block-id` is a *new* ID in
  `capture-task-id` (free text) but an *existing* parent task in
  `capture-task-sections` (completable).
- **Context.** Before running the engine, partially parse the words before the cursor
  on the resolved subcommand with `Command::ignore_errors(true)`. Completers then
  receive `bob_dir`, `route`, `task`, `repo`, and so on from clap's own matches, so
  short clusters (`-rcash`), `--route=cash`, and aliases all behave exactly like a
  real parse.
- **Two coverage tests make this reliable:**
  1. Every value-taking argument in the tree has a decision: possible values, a
     `ValueHint`, a kind, or explicit free text (`ValueHint::Other`). Adding an option
     without deciding its completion fails CI.
  2. Every table entry matches a real argument, so renames cannot silently drop
     completion.

v1 kind catalog:

| Kind | Slots | Source | Notes |
| --- | --- | --- | --- |
| static choices | `--format`, `--engine`, `--status`, `--prefer`, gkeep `--source` | clap possible values | add `PossibleValue::help` where useful |
| directories | `--bob-dir`, `--repo`, `--backup-dir`, `--lib-dir`, `--ref-dir`, `--xlib-dir` | `!dirs` → `_files -/` | native colors and quoting |
| files | `--query-file`, `--tasks-file` (and `-`), `highlights create MD_FILE` (`*.md`), `sync`/`marker PDF` and `--output` (`*.pdf`) | `!files` | |
| vault notes | `query --tasks-note`, `--origin` | `!files-in $BOB_DIR *.md` | vault-relative, no scan |
| route | `--route` on capture, capture-sections, capture-tasks, capture-task-id, capture-task-sections | `scan_capture_targets` | groups inbox / areas / projects; ~15 ms |
| section | `capture --section` (← route) | capture-sections scan | |
| task | `capture --task`, `capture-task-sections --block-id`, `--task-ref` (← route) | capture-tasks scan | description = task text |
| task section | `capture --task-section` (← route, task) | capture-task-sections scan | |
| Pomodoro ref | `capture-pomodoro-name --pomodoro-ref` | capture-pomodoros scan | description = `0700-0725 GTD` |
| capture marker | TEXT words starting `@ ^ : =` on capture / capture-parse / capture-rewrite | `capture_complete::build_result` | wikilinks deferred (300 ms) |
| plugin | `plugins sync --plugin` (← `--repo`) | list `<repo>/plugins/*/` | **never** `git pull` |
| level | `randomize --level` | `randomize.levels[].label` in config | |
| free text | `--message`, `--name`, `--title`, `--seed`, `--cursor`, gkeep `--id`/`--email`, `--query`, `--tasks` … | `!message <help>` | |

### 6.5 Behavior rules (intuitive)

1. On an empty word, offer subcommands and positional values. Offer options only when
   nothing else applies (`bob capture-sections <TAB>`) or after `-`, following the
   `_arguments` convention.
2. A lone `-` pairs each short and long form on one row.
3. Drop options already given, unless they are `Append`/`Count`. Drop options that
   conflict with given ones (`get_arg_conflicts_with`). Drop `--help` once other
   arguments are present.
4. Keep bob's ranking. Routes come in capture-targets order, and tasks in
   `capture-complete` ranking. Never alphabetize what bob ranked.
5. Descriptions must add information: kind and status for routes, task text for task
   IDs, time range and name for Pomodoros. Never repeat the value.
6. Add no space after `/`, after `=`, or after a capture marker that expects a
   continuation (for example `@dev:` → `#name`).
7. Group names are human words: `commands`, `options`, `inbox`, `areas`, `projects`,
   `tasks in dev`, `open Pomodoros`. Never use internal IDs such as
   `pomodoro_block_id`.
8. **Porcelain before plumbing (adjustment, see §7):** subcommands carry a tier in
   `SUBCOMMANDS`. `bob <TAB>` shows `commands` first and the ten capture frontend
   endpoints under a final `capture protocol` group.

### 6.6 The zsh adapter (tested shape)

This exact function rendered the menus in §5, with the prototype's `--protocol` flag
added:

```zsh
#compdef bob
# Generated by `bob completion zsh` (protocol 1). Do not edit: run
# `bob completion install` instead. Each <TAB> asks the `bob` on PATH,
# so completions always match the installed binary.

_bob() {
  local -a lines fields groups
  local -A arrays
  local line value help group suffix array ret=1
  lines=("${(@f)$(command bob __complete zsh --protocol 1 -- "${(@)words[1,CURRENT]}" 2>/dev/null)}")
  (( ${#lines} )) || return 1

  # Bob-scoped presentation defaults. Any style the user set wins.
  zstyle -m ":completion:${curcontext}:descriptions" format '*' ||
    zstyle ':completion:*:*:bob:*:descriptions' format $'%{\e[1;32m%}── %d ──%{\e[0m%}'
  zstyle -m ":completion:${curcontext}:" group-name '*' ||
    zstyle ':completion:*:*:bob:*' group-name ''

  for line in $lines; do
    case $line in
      ('!dirs')       _files -/ && ret=0; continue ;;
      ('!files '*)    _files -g "${line#!files }" && ret=0; continue ;;
      ('!files-in '*) fields=(${(s: :)${line#!files-in }})
                      _files -W "$fields[1]" -g "$fields[2]" && ret=0; continue ;;
      ('!message '*)  _message -r "${line#!message }"; continue ;;
    esac
    fields=("${(@ps:\t:)line}")
    value=${fields[1]//:/\\:} help=$fields[2] group=${fields[3]:-values} suffix=$fields[4]
    array=$arrays[$group/$suffix]
    if [[ -z $array ]]; then
      array=_bob_group_${#groups}
      arrays[$group/$suffix]=$array
      groups+=("$group/$suffix")
      local -a $array
    fi
    set -A $array "${(@P)array}" "$value${help:+:$help}"
  done

  for group in $groups; do
    array=$arrays[$group]
    suffix=${group##*/} group=${group%/*}
    if [[ $suffix == nospace ]]; then
      _describe -V -t "${group// /-}" "$group" $array -S '' && ret=0
    else
      _describe -V -t "${group// /-}" "$group" $array && ret=0
    fi
  done
  return ret
}

if [[ $zsh_eval_context[-1] == loadautofunc ]]; then
  _bob "$@"
else
  compdef _bob bob
fi
```

The default styles are scoped to `bob` contexts and applied only when no matching user
style exists. The first `<TAB>` in a shell gets the green `── group ──` headers. If you
configure your own `format` or `group-name`, yours wins with no extra knob.
`list-colors`, `menu select`, and your `matcher-list` keep working because the adapter
goes through `_describe` and `_files`.

The bash adapter is ~40 lines. It reassembles the cursor word from
`COMP_LINE`/`COMP_POINT` (to handle `:` and `=` word breaks) and maps directives to
`compgen -d` / `compgen -f`. bash cannot show descriptions or groups, so it receives
values only.

### 6.7 `install`: target selection, safety, verification

1. **Target**, in order:
   - `-t/--target` or `BOB_COMPLETION_DIR`
   - the directory of an existing bob-written adapter (keeps its location stable)
   - zsh: the first user-owned, writable `fpath` entry under `$HOME` that is not a
     framework plugin or cache directory, read from `zsh -ic 'print -rl -- $fpath'`
     with a timeout. On your machines that is `~/.zfunc`.
   - zsh: `${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/completions` (created if missing)
   - zsh: `~/.zfunc`, printing the exact `fpath=(~/.zfunc $fpath)` line to add before
     `compinit`
   - bash: `${BASH_COMPLETION_USER_DIR:-${XDG_DATA_HOME:-~/.local/share}/bash-completion}/completions/bob`
2. **Ownership.** The adapter's first comment line is the stamp (`Generated by
   bob completion (protocol N)`). Bob refuses to overwrite a file without it unless
   `--force` is given. It never touches rc files and never touches chezmoi sources.
3. **Write** is atomic (temp file + rename) and skipped when the bytes are unchanged
   (`unchanged`). Bob also removes a stale `_bob.zwc` next to the file. A ~50-line
   adapter gains nothing from `zcompile`.
4. **Verify** (zsh, skipped with `-n`). A real `zsh -ic` probe checks that
   `${_comps[bob]}` is `_bob`, and that `autoload +X _bob` resolves to *this* file
   (`$functions_source[_bob]`), which catches shadowing. Bob also warns when
   `command -v bob` is not the binary that is running, since PATH shadowing would make
   `<TAB>` ask a different bob.
5. **Report** in stacked blocks: color on a TTY, plain text otherwise, and `NO_COLOR`
   respected through the existing `style::Styler`.

```text
🐚  Shell completion
  ✓ zsh   ~/.zfunc/_bob  updated (protocol 1) · registered as _bob
  · bash  ~/.local/share/bash-completion/completions/bob  unchanged

  Open a new shell (or `exec zsh`) to pick up the new adapter.
```

### 6.8 `just install`

```just
# Install bob and its compatibility shims from this checkout, then install or
# refresh shell completion for your shell(s).
install: (_banner "35" "📦" "INSTALL")
    #!/usr/bin/env bash
    set -euo pipefail
    cargo install --path . --locked
    "${CARGO_INSTALL_ROOT:-${CARGO_HOME:-$HOME/.cargo}}/bin/bob" completion install
```

- Use `--path` and do not add `--force`. Cargo's documentation says "Installing with
  `--path` will always build and install", and `--path` reuses the workspace `target/`.
  On this host that measured ~45 s incremental and 1m47s clean (release).
- Call the *freshly installed* binary by path, not by PATH lookup. `bob completion
  install` then warns if PATH resolves a different `bob`.
- Extend `install-smoke`:
  - add `--help` checks for every new command
  - add `"${root}/bin/bob" __complete zsh --protocol 1 -- bob cap | grep -q '^capture'`
  - add `"${root}/bin/bob" completion install zsh -d -t "${root}/zfunc"`
- Update the README's Installation section to lead with `just install`, and add a new
  `docs/completion.md` linked from the README's "Detailed command contracts" table.

### 6.9 Reliability checklist

- Exact pin `clap_complete = "=4.6.11"` with `unstable-dynamic`, which is
  semver-exempt. Isolate all engine calls in one module. If upstream breaks the API,
  the fallback is a ~300-line in-house walker over clap's public `Command`
  introspection.
- **Deadline:** completers run on a worker thread, and the request returns after 150 ms
  regardless (`recv_timeout`) with whatever is ready. Target p50 is ≤10 ms for static
  slots and ≤30 ms for vault slots.
- **Read-only:** completers call only scanners. A test runs every completer against a
  `chmod -w` fixture vault and asserts no file changes. No locks, no `git`, no network.
- **Tests:**
  - tree ↔ `SUBCOMMANDS` parity (names and about text)
  - the two coverage tests from §6.4
  - golden protocol output against a fixture vault under `tests/cli/completion.rs`
  - real-shell smoke tests for zsh (pty or `zpty`) and bash (`COMP_LINE`), skipped
    when the shell is absent, as sase's `test_zsh_smoke.py` is
  - a warn-only latency check

## 7. Critique, And Adjusted Requirements (Called Out)

**Is this a good idea?** Yes. Completion turns recall into recognition for a CLI with
27 commands and 123 value-taking long options. It is also the cheapest way to make
vault state (routes, tasks, open Pomodoros) discoverable from a terminal. The one real
risk is building sase-scale machinery for a problem bob does not have. Avoid that.

| # | Adjustment | Why |
| --- | --- | --- |
| R1 | **`just install` ensures a stable adapter. It does not regenerate a grammar.** | A runtime grammar cannot drift; §2.5 shows drift already happens. |
| R2 | **Prerequisite: one full command tree, and the 5 hand-parsed commands migrated to clap.** | Without it, completion sees names only. It also unifies `--help`. |
| R3 | **zsh is first-class, bash is supported (values only), fish is deferred** until a test host has fish. The fish adapter is ~5 lines because fish natively reads `value\tdesc`. | Ship only what real-shell tests cover. fish is absent here. |
| R4 | **Vault-aware values are in scope for v1**: routes, tasks, Pomodoros, and capture markers. Wikilinks are deferred until an index cache exists. | That is where completion pays off. Wikilinks cost 300 ms. |
| R5 | **Porcelain before plumbing** in `bob <TAB>` (and later in `bob --help`). | 10 of 27 entries are capture-frontend endpoints that crowd out daily commands. |
| R6 | **No rc edits, no chezmoi deployment, no `eval` in rc.** `_bob` is host-local and owned by `bob completion install`. | It is tied to the binary `just install` places, and it follows sase's hard-won rules. |
| R7 | **Add `status` and `uninstall`.** | Something that writes into your dotfile directories must be inspectable and reversible. |

Risks I accept: an unstable upstream API (mitigated by pinning and isolation), about
150 lines of shell to own (mitigated by real-shell tests), and a new process per
keystroke under autosuggest (4–16 ms, plus a deadline).

## 8. Phased Plan

1. **P0 — One tree (S/M).** Add `NativeCommand::command()`, migrate the 5 hand
   parsers with parity tests, and add the tree ↔ `SUBCOMMANDS` test. No user-visible
   change except more consistent help.
2. **P1 — MVP completion (M).** Add the pinned dependency, `bob __complete`, protocol
   1, the zsh adapter, static kinds (choices, `!dirs`, `!files`, `!message`), the §6.5
   rules, the coverage tests, the zsh smoke test, `bob completion install|status|zsh`,
   `just install`, `install-smoke`, `docs/completion.md`, and the README.
3. **P2 — Vault kinds (M).** Add partial-parse context, then routes, sections, tasks,
   task sections, Pomodoro refs, capture markers (no wikilinks), plugins, and levels.
   Add the deadline and the read-only test.
4. **P3 — Breadth and polish (S).** Add the bash adapter with its smoke test,
   `uninstall`, porcelain/plumbing tiers, and `PossibleValue` help text.
5. **Later.** A wikilink index cache, the fish adapter, and offering tag-grouping in
   clap_complete's zsh adapter upstream.

## 9. Open Questions For Bryan

1. Should plumbing `capture-*` commands be grouped last (my recommendation) or hidden
   from `bob <TAB>` entirely?
2. Is bash worth P3 at all, or is zsh everywhere (apollo, athena, mac)?
3. Are you OK with `_bob` applying bob-scoped default group headers when you have set
   no style yourself?
4. Is the help-output change for `bob notify` / `pomodoro` / `move-done-tasks` (and the
   `bob_*` shims) acceptable when they move to clap?
5. Should the accepted design be recorded as a decision ("shell completion is a thin
   client of bob"), alongside `mac-capture-is-a-thin-client`?

## 10. Recommendation

Build **option C**: runtime completion computed by the `bob` binary.

- **Engine:** clap_complete's `unstable-dynamic` engine, pinned to `=4.6.11`, under a
  bob post-filter and presenter.
- **Shell side:** a protocol-versioned, ~50-line zsh adapter (and a bash one) that
  renders bob's tagged candidates as grouped, described, natively styled menus.
- **Prerequisite:** one exhaustive command tree, so every subcommand and option is
  completable, guarded by coverage tests.
- **Values:** vault-aware completers for routes, tasks, Pomodoros, and capture markers,
  reusing the existing scanners and `capture-complete`, under a 150 ms deadline and a
  read-only guarantee.
- **Install:** `bob completion install|status|uninstall|zsh|bash`, and a
  `just install` that runs `cargo install --path . --locked` and then the fresh binary's
  `completion install`. That keeps the adapter present and current without editing rc
  files.

This gives sase-grade polish at a fraction of sase's machinery. Completion is correct
by construction for whatever `bob` is on your PATH.

## Appendix: Sources

- bob-cli `f11a9f8`:
  - `src/runner.rs` (`SUBCOMMANDS`, `build_cli`, `delegate_subcommand`)
  - `src/native.rs`
  - `src/native/capture_complete.rs`, `capture_targets.rs`, `capture_pomodoros.rs`
  - the hand parsers listed in §2.1
  - `justfile`, `README.md` § Installation
- sase repo (opened via `sase repo open sase`): `docs/completion.md`,
  `src/sase/completion/`, `tests/completion/test_zsh_smoke.py`, plus the live
  `sase completion <cmd> --help` output.
- clap repo (opened via `sase repo open gh:clap-rs/clap`):
  - `clap_complete/src/engine/{complete,custom,candidate}.rs`
  - `clap_complete/src/env/{mod,shells}.rs`
  - `clap_complete/CHANGELOG.md` (4.6.11, 2026-09-15; `unstable-dynamic` still gated)
- `cargo help install` (cargo 1.95.0): `--path` semantics and `--target-dir` defaults.
- Memory: `decisions:mac-capture-is-a-thin-client`, `cli_rules`.
- Prototype: `/tmp/bob-proto-cld`. It is a scratch copy: 520-line
  `src/native/completion.rs`, visibility edits, and a pty harness that ran zsh 5.9
  through `pyte`. It is not committed anywhere.
