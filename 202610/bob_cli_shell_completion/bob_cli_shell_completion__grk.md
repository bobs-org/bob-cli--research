# Shell completion for `bob`

- **Researcher:** grk
- **Date:** 2026-10-02
- **Question:** How should `bob` grow excellent command-line completion, using `sase completion` as inspiration, and how should a new `just install` target install the crate from source and keep that completion current?
- **Verdict:** Build it. Mirror the *user-facing* `sase completion` command (list / emit / install / refresh / candidates) and hook it from `just install`. Do **not** port sase's Python-era runtime grammar cache, `ensure`/`loader` split, structural spec snapshot, doctor checks, or `deploy-chezmoi` in v1. The implementation must compose bob's real nested clap trees first; generating completions from today's top-level delegate parser would complete subcommand *names* and then fall through to filenames.

---

## 1. In one breath

`sase completion` is the right product to copy and the wrong engine to copy.

The product: a first-class `completion` command that writes a script where the shell already looks, never edits `~/.zshrc`, verifies zsh actually registered the function, stamps what it wrote, and offers live values with descriptions. `just install` is `cargo install --path . --locked --force` followed by that same install/refresh so a source rebuild cannot leave Tab completing yesterday's flags.

The engine: sase generates native shell grammar from a huge argparse tree and caches it because `sase` takes ~570 ms to start. `bob --help` takes **3 ms**. Vault route listing takes **15 ms**. The cache/loader/`ensure` machinery exists to hide Python startup, not because shells require it. Porting it into a 3 ms Rust binary would add failure modes without adding speed.

The trap: `src/runner.rs` builds a clap tree whose every workflow subcommand is a `trailing_var_arg` bucket. Nested flags live in each module's own `build_cli()`. `clap_complete` pointed at `runner::build_cli()` today would make `bob <TAB>` list commands and `bob gkeep <TAB>` offer files. Excellent completion starts by composing those existing `build_cli()` functions into one tree used for generation (and, later, maybe for parsing).

---

## 2. Critique of the plan

The plan as stated: give `bob` excellent completion in the spirit of `sase completion`, and add `just install` that `cargo install`s from source and updates completion.

### What is right

- A dedicated `bob completion` command is the correct surface. Users already know `sase completion install`. Teaching a second ritual (`COMPLETE=zsh bob` in `~/.zshrc`, a Makefile `completions/` directory, a one-off `just completions`) would be a downgrade.
- `just install` is overdue on its own. README still tells people to type `cargo install --path . --locked --force`. The justfile only has `install-smoke`, which installs into a temp `--root` and must stay that way. The `bob` currently on `PATH` (`~/.cargo/bin/bob`) does not even recognize `ready`; the workspace tree does. Source install and completion refresh belong on the same happy path because cargo has no post-install hook.
- Never `eval "$(bob completion zsh)"` on every shell start, even though bob is fast enough that it would *work*. sase's docs spent real blood on this: write a file, `zcompile` it, open a new shell. Keep that muscle memory.
- Never edit rc files. If zsh registration fails, print the exact `fpath=(~/.zfunc $fpath)` line that must appear before `compinit`.
- Live values (routes, plugin ids) are what make completion *excellent* rather than a flag encyclopedia. Static subcommands and `value_parser(["human", "json"])` enums are the floor.

### What is wrong or incomplete

1. **sase is not a template to photocopy.** `src/sase/completion/` is 45 Python modules. It exists because argparse has no `clap_complete`, because sase startup is 300–640 ms (measured 567 ms for `sase version` on this host), because the tree has hundreds of parsers, and because Bryan's machines are chezmoi-managed. bob has none of those constraints except the last.
2. **`just install` cannot be the only way completion gets installed.** `cargo install --git …` and a plain `cargo install --path .` will keep existing. The primitive is `bob completion install`. `just install` *calls* it.
3. **Generating from the current top-level clap command is a false start.** See §5. Any design that adds `clap_complete` to `runner::build_cli()` without composing nested commands will ship "completion" that feels broken on the second Tab.
4. **Unifying clap parsing is a good cleanup and a bad blocker.** Help tests pin mixed templates (`usage: bob move-done-tasks` vs `Usage: bob task-status-hooks`), custom after-help, and `disable_help_flag(true)` on many commands. Completions can consume a composed tree while dispatch stays trailing-var-arg. Do not hold Tab hostage to a help-text refactor.
5. **Calling the full user commands for live values is too slow and too side-effecting.** `bob plugins list` took **497 ms** here and git-pulls the plugins repo unless `--no-pull`. A completer that shells out to the real command will hitch zsh-autosuggestions and mutate remotes. Live providers must be read-only scans with a latency budget.
6. **`deploy-chezmoi` is real in this house and still not v1.** `~/.zfunc/_sase` is chezmoi-owned (`home/dot_zfunc/_sase` in the chezmoi source). A local `_bob` next to it will survive `chezmoi apply` on typical configs (unmanaged files stay) and will **not** appear on the MacBook until that machine runs `just install`. That is acceptable for a cargo-built binary. A chezmoi deployer is a follow-up, not a prerequisite.
7. **CompleteEnv (`COMPLETE=zsh bob`) is the fashionable Rust answer and the wrong default UX.** clap_complete's own docs tell you to re-source the stub on every shell start because the protocol is unstable. jj documents both `jj util completion zsh` and `COMPLETE=zsh jj`, and calls the latter the "improved" dynamic mode. For bob, hide any `COMPLETE=` protocol behind `bob completion install`. Users should never put `COMPLETE=` in an rc file.

The plan is a good product idea. A literal sase port, or a literal `clap_complete::generate(&runner::build_cli())`, would be a bad implementation.

---

## 3. Justified requirement adjustments

These change the user's wording. They are deliberate.

| Original implication | Adjustment | Why |
| --- | --- | --- |
| Make bob completion "like sase" | Copy the **command interface and install ethics** (list/install/refresh/emit, no rc edits, zcompile, verify, stamp). Do not copy runtime grammar cache, `ensure`, portable loaders, `spec` snapshots, doctor groups, or `deploy-chezmoi` in v1. | Those exist to hide a 500 ms Python CLI and a 300-parser tree. bob is 3 ms and ~25 top-level commands. |
| `just install` installs the package and updates completion | `just install` = `cargo install --path . --locked --force` (same flags as README) then `bob completion install` then `bob completion refresh`. The public primitive remains `bob completion install`. | cargo has no post-install hook. Git-based `cargo install` users still need a command that works without just. |
| Excellent completion | v1 floor: every public subcommand, option, short alias, and static `value_parser` choice, plus live **route** and **plugin id** values. Capture-grammar completion inside `TEXT` (`@route`, `s:N`, `=x`) stays `bob capture-complete`'s job. | Shell Tab on free text is a different product. Mac Capture already owns that contract. |
| Support shells like sase | zsh, bash, and fish from day one. No nushell/powershell/elvish in v1. | sase's trio matches Bryan's machines. zsh is the daily driver (`~/.zfunc/_sase` is live). |
| Update completion on `just install` | Refresh **stamped** shells and install the detected current shell. Missing stamps for unused shells stay missing. | Installing fish completions on a zsh-only host is noise. Refresh keeps a previously stamped bash install from going stale. |
| Beautiful | Colored step output on install; a **readable** `list` table that does not wrap the path through a 1-character column (sase's current TTY table on this host is the anti-pattern); zsh descriptions; print the recommended `zstyle` snippet after a zsh install. | cli_rules.md: prefer colored output when it helps; help and completion are the same family of craft. |
| Reliable | Completers fail open (empty candidate list, never a traceback in Tab). Plugin candidates **must not** `git pull`. Route candidates reuse `scan_capture_targets` (15 ms). Hidden aliases (`mark-next-tasks`, `task-status-setter`) stay hidden. | A completer that errors is worse than no completer. `plugins list` at 497 ms with a network pull is a footgun. |

A Markdown-only "check completions/ into git and copy them in a Makefile" design is a **different product**. It drifts the moment someone adds a flag. sase moved *off* frozen snapshots for that reason.

---

## 4. How `sase completion` actually works

Measured and read from the sase checkout opened for this research (`sase repo open sase`), plus live `--help` on this host.

### Interface (copy this)

Bare `sase completion` defaults to `list`. Subcommands:

| Command | Role |
| --- | --- |
| `bash` / `fish` / `zsh` | Emit a native script (`-o/--output` to write a file) |
| `install [shell]` | Detect shell, pick a scanned directory, write atomically, `zcompile` (zsh), verify `_comps[sase]`, stamp |
| `list` | Shells, generator, install status, zwc freshness, stamp version, owner (`-j/--json`) |
| `refresh [shell]` | Rewrite stamped installs from the running binary |
| `candidates KIND [PREFIX]` | Live values as `value<TAB>description` |
| `loader` / `ensure` | Tiny shell stub + cached grammar path (Python-startup workaround) |
| `spec` | Structural JSON snapshot for CI |
| `deploy-chezmoi` | Write loaders into `~/.local/share/chezmoi/home` |

Hard rules worth stealing verbatim:

- Write a file. Do not eval generator output on every new shell.
- Never edit `~/.zshrc` / `~/.bashrc` / fish config.
- Prefer a directory the shell **already scans**. Framework drop-in (`~/.oh-my-zsh/custom/completions`) beats `~/.zfunc` when oh-my-zsh is in play, because frameworks guarantee `fpath` order before `compinit`. Never drop a script into a plugin's own directory.
- Detect shell from an explicit argument, then the parent process, then `$SHELL`. Never guess silently.
- Refuse to overwrite a file sase did not write unless `--force`.
- Stamp `~/.sase/completion/stamp/<shell>.json` so `list` can tell managed / stale / foreign / missing.
- Live values go through a narrow `candidates` wire format, not a full CLI parse.

### Why sase is that complicated (do not copy this)

From `docs/completion.md` and this host:

| Constraint | sase | bob |
| --- | --- | --- |
| Startup | 300–640 ms documented; **567 ms** for `sase version` here | **3 ms** for `bob --help`; **5 ms** for `bob capture --help` |
| Tree size | hundreds of parsers (docs cite 331 / 809 options as an old baseline) | ~25 top-level commands, a handful of nested trees |
| Parser | argparse, no clap_complete equivalent | clap 4.6 builder API, `clap_complete` is the native generator |
| Live values | beads, projects, xprompts, artifacts, … (20+ kinds, some needing a fast path around argparse) | routes, plugin ids, a few enums; capture grammar already has `capture-complete` |
| Multi-machine | chezmoi-owned loaders in `dot_zfunc/_sase` | cargo-installed per machine; chezmoi can wait |
| Upgrade hook | `sase update` auto-refreshes stamped installs | no equivalent except the `just install` we are adding |

The loader/`ensure` split exists so a 20-line chezmoi-managed stub can ask *whichever* `sase` is on `PATH` for a current cached grammar, avoiding a full import. bob does not need a grammar cache. Regenerating a zsh script is cheaper than sase's cache hit.

### Beauty notes from sase, good and bad

Steal: step-by-step install report; recommended `zstyle` block (`menu select`, group names, yellow description headers, `use-cache on`); candidate descriptions; `value<TAB>description` wire format.

Do not steal: the current `sase completion list` table on this terminal wrapped the path **vertically, one character per line**. A beautiful `bob completion list` should put the path on its own full-width row (or use `bob`'s existing `Styler` table helpers from `src/native/style.rs` / `plugins` list) so status is scannable at a glance.

---

## 5. How bob's CLI is shaped today (the real design constraint)

### Two clap trees, not one

`src/runner.rs` `build_cli()` registers every workflow command as:

```rust
ClapCommand::new(name)
    .disable_help_flag(true)
    .arg(Arg::new("args").num_args(0..).trailing_var_arg(true).allow_hyphen_values(true))
```

Dispatch then calls `native::run(NativeCommand, args)`, and **each module builds a second clap `Command`** named `"bob gkeep"`, `"bob capture"`, `"bob plugins"`, … with the real options and nested subcommands.

This is a migration leftover from script fallback (`BOB_CLI_USE_SCRIPT`, still wired for `notify` / `pomodoro` / `tmux-pomodoro`). It is why `bob gkeep --help` is excellent and why a generator pointed at the top-level command cannot see `--dry-run` on `gkeep pull`.

Every module already has a `fn build_cli() -> ClapCommand` (some `pub(crate)`, most private). Highlights, freshness, gkeep, plugins, projects, query, vault-sync already have nested subcommands. That is the raw material.

Composing them for completion:

```rust
gkeep::build_cli().name("gkeep")  // Command::new is "bob gkeep" for help bin_name
```

Do **not** change those names in the parse path in the same PR. Help tests are extensive (`tests/cli/help.rs`, `tests/cli/help_options.rs`) and pin wording, option order (cli_rules: alphabetical), and mixed usage templates.

### Static choices already in clap (free completions)

`value_parser([...])` is already used widely. clap_complete (and any walker) will pick these up for free:

| Values | Where |
| --- | --- |
| `human`, `json` | capture family, freshness, plan, ready, randomize, task-status-hooks, gkeep doctor, … |
| `table`, `json` | plugins, gkeep list |
| `both`, `keep`, `vault` | `bob gkeep --source` |
| `native`, `obsidian` | `bob query --engine` |
| `json`, `markdown`, `paths` | `bob query --format` |
| `marker`, `frontmatter` | highlights |
| clip/create ref-type enums | highlights clip/create |

`--bob-dir` / `--repo` / PDF inputs should grow `ValueHint::DirPath` / `FilePath` so the shell's native path completion kicks in. That is a small annotation pass, not a new subsystem.

### Live values that are worth a subprocess

| Kind | Source | Budget | Notes |
| --- | --- | --- | --- |
| `route` | `scan_capture_targets` (`CaptureTarget.route` + `label`/`kind`) | **15 ms** measured | Highest-leverage Tab: `bob capture --route <TAB>`, `bob capture-sections --route <TAB>` |
| `plugin` | directory names under `<plugins-repo>/plugins/` | must stay ≪ 100 ms | **Do not** call `bob plugins list` (git pull, 497 ms) |
| `section` | `capture-sections` for a known `--route` | later | Needs context (`--route`). v1.5 |
| `task` | `capture-tasks` for a known `--route` | later | Same |
| `pomodoro` | `capture-pomodoros` names | **6 ms** measured | Nice for `#name` / `-p`; v1.5 |
| gkeep note `--id` | Keep network | skip | Completing a network inbox on Tab is a bad default |

Candidate wire format: copy sase. One line per value, `value<TAB>description`, descriptions optional, prefix filter and `--limit` (default 200) applied in one place. zsh `_describe` consumes this directly.

Fail open: a vault that will not scan returns no candidates, exit 0, no stderr noise during Tab (diagnostics belong on `bob completion candidates` when run as a normal command, or behind a verbose flag).

### Hidden aliases

`mark-next-tasks` and `task-status-setter` are hidden compatibility spellings of `task-status-hooks`. They must not appear in Tab. The composed tree should skip `HIDDEN_SUBCOMMAND_ALIASES`.

---

## 6. Alternatives considered

### A. Check generated scripts into `completions/` and copy them from `just install`

Used by many Rust CLIs (older ripgrep/fd). Drifts. Requires a CI snapshot or a human to remember to regenerate. sase abandoned frozen snapshots for the same reason. **Reject** as the live mechanism. A *test* snapshot of the composed tree (command paths + option strings, descriptions digested) is still a good idea internally — that is sase `spec` without making it a user command.

### B. `clap_complete::generate` on today's `runner::build_cli()`

One afternoon of work. Completes top-level names only. Users will Tab into `bob highlights <TAB>` and get files. **Reject** as the shipped behavior. Fine as a stepping-stone in a WIP branch.

### C. `CompleteEnv` / `COMPLETE=zsh bob` (clap_complete `unstable-dynamic`)

The current clap-maintainer recommendation. Live `ArgValueCompleter`s, always in sync with the binary, ~3 ms per Tab. Downsides: the shell stub protocol is explicitly unstable; clap's docs tell you to re-source on every shell start; users would have to put `COMPLETE=` in an rc file unless we wrap it; still requires the composed tree. **Accept as an internal implementation option** only if it stays hidden behind `bob completion install`. Prefer a bob-owned `candidates` protocol so we are not coupled to clap's stub format across clap_complete upgrades.

### D. Full sase port (custom emitters + loader + ensure + cache + chezmoi + spec + doctor)

Maximum fidelity. Also ~45 modules of behavior bob does not need, including a cache whose hit path is slower than bob regenerating a script. **Reject for v1.** Revisit `deploy-chezmoi` when `_bob` should ride the same chezmoi apply as `_sase`.

### E. Compose the clap tree, generate native scripts, sase-like `bob completion` UX, live `candidates` for cheap kinds (recommended)

See §7.

### F. Unify clap parsing so the top-level command *is* the nested tree

Long-term cleanliness: one `Command`, one help path, one completion path, delete trailing-var-arg. Blast radius is every help test and every `ClapCommand::new("bob …")` name. **Follow-up**, not this feature.

---

## 7. Recommended solution

### 7.1 Product

Add `bob completion`, alphabetically between `capture-tasks` and `freshness`, with the same default-to-list behavior as sase.

```text
bob completion                         # list
bob completion list [-j]
bob completion bash|fish|zsh [-o FILE]
bob completion install [bash|fish|zsh] [-d] [-f] [-t DIR]
bob completion refresh [bash|fish|zsh] [-d] [-j]
bob completion candidates KIND [PREFIX] [-l N] [-b DIR]
```

cli_rules apply: `-h/--help` is excellent; subcommands and options alphabetical; every public long option has a short alias; color when it helps (`NO_COLOR` respected, matching `Styler::detect()`).

`KIND` on `candidates` completes to the kinds this build can answer. v1: `route`, `plugin`. Static enums do not need the candidates command.

Install ethics (copy sase, rename identifiers):

1. Detect shell: explicit arg → parent process comm → `$SHELL`. Fail with "pass bash, fish, or zsh" if none match.
2. Target directory, in order: `-t/--target`, `BOB_COMPLETION_DIR`, framework `completions` drop-in if present, first writable scanned directory, conventional fallback (`~/.zfunc`, `~/.local/share/bash-completion/completions/bob`, `~/.config/fish/completions/bob.fish`).
3. Write atomically. Filenames: zsh `_bob`, bash `bob`, fish `bob.fish`.
4. `zcompile` the zsh script. Verify `${_comps[bob]}` in a non-interactive zsh. On failure, print the `fpath` line; do not touch rc files.
5. Stamp `$XDG_STATE_HOME/bob-cli/completion/stamp/<shell>.json` (default `~/.local/state/bob-cli/completion/stamp/`). Fields: shell, bob version, script digest, target path, timestamp, owner=`local`. This matches how vault-sync already uses XDG state, not a new `~/.bob/` tree.
6. `--force` overwrites a foreign file. Without it, refuse.
7. After a successful zsh install, print the same family of `zstyle` lines sase prints (`menu select`, group-name, description format, `use-cache on`).

`list` shows, for each of bash/fish/zsh: generator yes, path, zwc freshness, stamp version vs running version (`installed` / `stale` / `missing` / `foreign`), owner. Path gets a full line. `-j` dumps the same as JSON.

`refresh` rewrites every stamped supported shell (or one named shell). No stamp → successful no-op, matching sase. Dry-run prints `already current` / `would refresh` with the digest reason.

### 7.2 Engine

New module `src/native/completion/` (not a script, not a Python port):

| File | Job |
| --- | --- |
| `tree.rs` | `full_cli() -> Command`: top-level `bob` + each module's `build_cli()` remapped to `.name("gkeep")` etc. + the `completion` command itself. Skip hidden aliases. |
| `walk.rs` | Walk that `Command` into a small spec: path, about, options (strings, takes_value, choices, value_hint, kind, hidden), positionals, subcommands. |
| `kinds.rs` | Map dest/metavar names onto `route` / `plugin` / `path` / `dir`. Unambiguous names only (`route`, `bob-dir`, `plugin`). Never guess `id` / `name`. |
| `emit_zsh.rs` / `emit_bash.rs` / `emit_fish.rs` | Native scripts. zsh: `#compdef bob`, `_arguments -C -s -S`, descriptions, kinded slots calling `__bob_candidates`. Do not eval. |
| `candidates.rs` | `route` via `scan_capture_targets`; `plugin` via a no-pull directory listing. Wire format `value<TAB>description`. |
| `install.rs` | detect / target / write / zcompile / verify / stamp / list / refresh. Port the *behavior* of sase's `install_flow.py` + `install_targets.py`, not the Python. |
| `cli.rs` | clap tree for `bob completion` itself. |

Generation walks **clap**, not argparse. That is the entire difference that lets this stay small.

Do **not** take a `clap_complete` dependency in v1 unless emit quality is lacking after a spike. clap_complete's aot zsh is serviceable; sase's `_arguments` scripts are what Bryan already likes. A walker + three emitters is less code than sase's 45 files and more control than `generate()`. If a spike shows clap_complete 4.6 aot output is already beautiful *and* we can splice candidate hooks into it, using it for the static skeleton is an implementation detail — the public command and the candidate protocol stay bob-owned.

`clap_complete` `unstable-dynamic` / `CompleteEnv` stays off the user-facing path.

### 7.3 `just install`

Replace the missing recipe (keep `install-smoke` unchanged aside from adding `bob completion --help` to the smoke list):

```just
install: (_banner "35" "📦" "INSTALL")
    cargo install --path . --locked --force
    bob completion install
    bob completion refresh
```

Order matters: cargo install first so `PATH`'s `bob` *is* the new binary; install writes/updates the current shell; refresh updates any other stamped shells from that same binary.

If `bob` is not on `PATH` after cargo install, fail with an explicit "put `~/.cargo/bin` on PATH" message rather than silently skipping completion.

`just install` is a **user** command. It replaces the live `~/.cargo/bin/bob`. Agents in numbered workspaces must not run it unless asked. `just install-smoke` remains the non-clobbering check (`--root` tempdir).

README Installation becomes:

```bash
just install          # cargo install --path . --locked --force, then completion
bob completion list   # confirm zsh/bash/fish status
```

The git-remote cargo line stays; add `bob completion install` immediately after it.

Release checklist: keep `just install-smoke`; mention `just install` as the human path, not the CI path.

### 7.4 What "excellent" Tab looks like after v1

```text
bob <TAB>                    capture, capture-complete, … completion, freshness, gkeep, …
bob g<TAB>                   gkeep
bob gkeep <TAB>              doctor, list, login, pull  (and flags)
bob gkeep pull --<TAB>       --all, --bob-dir, --dry-run, --format, --help, --id, --no-archive, …
bob gkeep pull -s <TAB>      both, keep, vault
bob capture --route <TAB>    mac_inbox, groceries, cash, …  (label as description)
bob plugins sync -p <TAB>    bob-project-tasks, …
bob query --format <TAB>     json, markdown, paths
bob completion <TAB>         bash, candidates, fish, install, list, refresh, zsh
```

`bob capture <TAB>` on the free-text operand does not invent `@groceries` in v1. That is capture-complete territory.

### 7.5 Tests

- `full_cli().debug_assert()` (runner already does this for the delegate tree).
- Composed tree contains every public `SUBCOMMANDS` name and does not contain hidden aliases.
- Generated zsh/bash/fish scripts contain representative nested paths (`gkeep pull`, `highlights scan`, `vault-sync status`, `completion install`) and `--dry-run`.
- `candidates route` against a fixture vault lists inbox + area routes as `value<TAB>description`.
- `candidates plugin` lists directory names without touching git.
- `install -t <tempdir> -d` prints a plan and writes nothing; without `-d` writes `_bob` (or bash/fish names), stamps, and is idempotent.
- Foreign file without `--force` refuses; with `--force` overwrites.
- Help: `bob completion --help` and each subcommand, options alphabetical, short aliases present, `assert_stdout_has_no_ansi` in tests (TTY color is for humans).
- `just install-smoke` invokes `bob completion --help` and `bob completion list --help`.

Do not spawn an interactive zsh registration probe in ordinary `cargo test`. That is sase's deep doctor check. Cover the probe in a dedicated test gated on `zsh` being present, or leave it to a later smoke.

---

## 8. `just install` and completion: is this a good idea?

Yes. Two separate goods that belong together.

**`just install` without completion** is already justified. The justfile is the project's task runner; README's cargo one-liner is the thing people forget flags on (`--locked --force`); the live binary on this host is already behind the tree (`ready` missing). A named target is how Bryan installs sase (`just install` in that repo, even though it means something else there: editable venv).

**Completion without `just install`** would bit-rot. The first time someone adds a subcommand and Tabs on the old script, they will not remember to regenerate. Binding refresh to the source-install command is the Rust equivalent of sase refreshing on `sase update`.

**The combination** is the daily loop: pull, `just install`, new shell, Tab is current.

Risks:

- Running `just install` from a dirty numbered workspace installs WIP onto `~/.cargo/bin`. That is also true of README's cargo command. Document it as a user-facing, machine-global install.
- Completion install can fail (undetectable shell, zsh fpath). Do not hide that failure inside a successful cargo install: non-zero exit, with the binary already updated and a printed recovery command (`bob completion install zsh -t ~/.zfunc`). Partial success (binary new, completion old) is recoverable; silent skip is not.
- Writing `_bob` into chezmoi-managed `~/.zfunc` is owner=`local`. A later `deploy-chezmoi` must refuse to clobber without `--force`, matching sase's local/chezmoi ownership guard.

---

## 9. Implementation sketch (for the planner, not a commit)

1. Export each module `build_cli` as `pub(crate)` (or add `pub(crate) fn completion_command() -> Command { build_cli().name("gkeep") }`).
2. Add `NativeCommand::Completion` and a `SUBCOMMANDS` row. Keep trailing-var-arg dispatch; `completion::cli::run` parses its own tree, same as gkeep.
3. Implement `full_cli()`, walker, emitters, candidates, install. No new runtime deps beyond the standard library plus clap (already there). Add `clap_complete` only if the spike says so.
4. Annotate directory/file args with `ValueHint`.
5. `just install` + README + `install-smoke` help coverage.
6. Tests in `tests/cli/completion.rs`.

Out of scope for the same PR: unifying parse trees, capture-grammar Tab, chezmoi deploy, a public `spec` command, doctor integration, CompleteEnv, nushell.

---

## 10. Follow-ups (not v1)

- **`bob completion deploy-chezmoi`**, writing `home/dot_zfunc/_bob` (and bash/fish siblings) next to `_sase`, with a `run_onchange_after_zcompile_bob_completion` hook. Do this when Tab on the MacBook should work without compiling bob there, or when chezmoi starts deleting unmanaged files in `~/.zfunc`.
- **Context-kind candidates:** `section` and `task` given `--route`, `pomodoro` names. Generated zsh can pass `opt_args[-r]`.
- **Unify clap parsing** so help, dispatch, and completion share one `Command`. Separate bead; help tests are the cost.
- **`bob capture <TAB>` offering `@route` prefixes** — only after capture-complete and shell completion share a kind, and only for a leading `@` token, never for prose.
- Internal tree digest in CI, if emitters prove jumpy. That is sase `spec` without the user command.

---

## 11. Recommended solution (short)

Ship a sase-*shaped* `bob completion` command implemented as a clap-tree walker plus native zsh/bash/fish emitters and a `candidates` fast path for routes and plugin ids. Hook it from a new `just install` that runs `cargo install --path . --locked --force` and then `bob completion install` + `refresh`. Do not port sase's cache/loader/ensure/spec/doctor/chezmoi stack. Do not generate from the current delegate parser. Do not put `COMPLETE=zsh bob` in an rc file. Do not complete capture grammar in v1.

That is intuitive (same verbs as sase), reliable (stamped, verified, fail-open, no git-pull on Tab, no rc edits), and beautiful (descriptions, zcompile, a list table that can actually be read, colored install steps, alphabetical help).
