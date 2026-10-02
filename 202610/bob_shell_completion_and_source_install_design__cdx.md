# Bob shell completion and source installation: a design recommendation

Researcher: **cdx**. Date: **2026-10-02**. Scope: independent research and design; no production implementation or user installation was performed. No other report, transcript, summary, or finding from this research swarm was consulted.

## Assessment

This is a good idea. Bob has 27 visible top-level commands, nested command families, many flags, and a capture language whose routes and task identifiers are difficult to remember. Completion can make that interface discoverable and reduce mistakes. A source-install recipe that also maintains completion closes the common gap between “the binary installed” and “the command is pleasant to use.”

The work is larger than adding `clap_complete::generate()` to `main.rs`. Bob's top-level parser forwards opaque arguments to separate parsers, several commands still parse arguments by hand, and capture has trailing-text semantics that a generic completion engine does not fully respect. The best design starts by exposing Bob's real command definitions, then builds a small installation layer and read-only value providers around them.

**My preferred architecture is pinned Clap dynamic completion, with portable, self-correcting shell loaders and static exports as a fallback.** Rust's process cost makes this more attractive for Bob than it would be for a Python CLI. Keep SASE's useful installation affordances; do not reproduce its entire completion subsystem.

## Evidence and method

I inspected the current Bob source, the live `sase completion` help for every subcommand, and SASE's completion documentation and implementation. Other repositories were opened through audited `sase repo open` calls. I read the required CLI/artifact memory and the accepted thin-client decision through `sase memory read`.

Source revisions examined:

| Repository | Revision |
| --- | --- |
| bob-cli | `f11a9f81256a10ee812e47c3a203797262e9c381` |
| sase | `b255e14adc8b7c08174008220060de14a3650c60` |
| clap | `4be56132cf7a5ef6e237409a13225a5829cb24e4` |
| bash-completion | `00c34614e3a683421a4d1b10f3e72ddf4530af49` |

I also compiled an isolated release-mode Rust probe using **clap 4.6.6** and **clap_complete 4.6.11**, generated Bash/fish/zsh scripts, and tested Bash/zsh registration, candidate output, and zsh function-file loading. The probe used a small representative command tree and in-memory values, not Bob's actual vault. Fish was not installed on this research host, so its generated script was inspected but not executed. The proposed `just install` recipe was parsed with `just 1.50.0 --dry-run`; no install was run.

These observations establish feasibility and reveal integration issues. They are not an end-to-end validation of the proposed Bob implementation, macOS behavior, or production vault latency.

## What SASE offers, and what to borrow

The live command defaults to `list` and exposes this interface:

| SASE subcommand | Public options of interest | Purpose |
| --- | --- | --- |
| `bash`, `fish`, `zsh` | `-o/--output FILE` | Export native completion grammar. |
| `candidates KIND [PREFIX]` | `-l/--limit N`, `-p/--project NAME` | Return live values with descriptions. |
| `deploy-chezmoi` | `-a/--no-apply`, `-c/--no-commit`, `-d/--dry-run`, `-n/--no-push`, `-s/--source DIR` | Publish portable loaders through dotfiles. |
| `ensure SHELL` | `-f/--force`, `-p/--loader-path FILE`, `-O/--owner`, `-t/--target DIR` | Resolve or regenerate runtime-cached grammar. |
| `install [SHELL]` | `-d/--dry-run`, `-f/--force`, `-t/--target DIR` | Choose a usable location, install atomically, verify and stamp. |
| `list` | `-j/--json` | Show supported shells, ownership, locations, and health. |
| `loader SHELL` | `-O/--owner`, `-o/--output FILE` | Export a portable bootstrap loader. |
| `refresh [SHELL]` | `-d/--dry-run`, `-j/--json` | Refresh recorded installs without changing their locations. |
| `spec` | `-d/--descriptions`, `-j/--json`, `-o/--output FILE` | Expose structural grammar for integrations and snapshot checks. |

SASE separates static grammar from live values, caches candidate reads, records ownership and content identities, and handles zsh's `fpath` ordering and shadowing. Its documentation reports a 300–640 ms full Python startup, which motivates its grammar-cache layer. Those numbers describe SASE's documented environment; they are not Bob measurements. See the inspected [SASE completion documentation](https://github.com/sase-org/sase/blob/b255e14adc8b7c08174008220060de14a3650c60/docs/completion.md).

Borrow these principles:

- `completion` alone displays useful status; it neither installs nor dumps shell code unexpectedly.
- Explicit shell selection, dry-run, output files, and an honest distinction between a written file and active completion.
- Atomic installation, recorded destinations, content hashes, and refusal to overwrite foreign or edited files implicitly.
- Existing installations across several shells are refreshed after upgrades.
- Startup files stay user-owned. If setup is necessary, print the precise snippet.
- Descriptions accompany values wherever the shell can display them.

Do not start with `deploy-chezmoi`, a public structural `spec`, a grammar daemon, Python-style source fingerprinting, or zsh bytecode management. None is required for Bob's first release. An external dotfiles manager can install a portable loader produced by Bob. That is enough integration without turning a completion command into a dotfiles deployment tool.

## Bob-specific findings

### The full command tree does not currently exist at the runner boundary

`src/runner.rs::build_cli()` installs each command through `delegate_subcommand()`. A delegate disables its help flag and accepts a variadic `args` positional with `trailing_var_arg(true)` and `allow_hyphen_values(true)`. Execution forwards those arguments to `native::run()`. The actual flags and nested commands are defined inside native modules. See [the runner](https://github.com/bobs-org/bob-cli/blob/f11a9f81256a10ee812e47c3a203797262e9c381/src/runner.rs) and [native dispatch](https://github.com/bobs-org/bob-cli/blob/f11a9f81256a10ee812e47c3a203797262e9c381/src/native.rs).

The controlled probe reproduced this: generation from a delegate-only `query` command omitted both `--engine` and its `native`/`obsidian` choices in all three shells; generation from the real command definition included them. Merely attaching a generator to the current root would be visibly incomplete.

Expose pure command-builder functions through a native command-definition registry, normalize leaf names from strings such as `bob query` to `query` when composing them, and assemble a complete `bob` tree for completion. Reuse the same argument builders that execution already uses. The current top-level forwarding path can remain initially; this feature does not require rewriting every handler around one `ArgMatches` object.

The registry should connect command identity, description, implementation, and definition so newly added commands cannot silently omit completion. An exhaustive `NativeCommand` match or definition function in the existing command table can enforce this. Keep definitions free of vault reads, configuration validation, and external commands.

There are also hand-written parsers for `move-done-tasks`, `nightly`, `notify`, `pomodoro`, and the tmux surface. Give them accurate metadata in their own modules and compatibility checks, or migrate their parsing to shared Clap definitions only where current behavior can be preserved. Do not silently alter legacy shims, error messages, duration parsing, or accepted flag spellings merely to simplify completion.

One less obvious mismatch is `freshness`: its bare form reparses trailing arguments as `list`, while its displayed root builder contains only some of those flags. The composed completion definition must model the accepted bare form too. Reusing builders is necessary, but does not automatically capture every dispatch convention.

### Paths need explicit semantics

Many Bob arguments currently use `OsStringValueParser` and labels such as `PATH` or `DIR`, without `ValueHint`. Add hints at the actual definitions: `DirPath` for vault/repository/output directories; `FilePath` for actual query/input/output files; `Other` for text, identifiers, numeric values, and query expressions that should not suggest arbitrary files. Keep finite choices in Clap value parsers.

A vault-relative note selector, a route, and a filesystem path are different value domains. For example, a vault-relative query origin must not blindly complete files in the current working directory. Its provider should resolve under the selected vault and return the spelling Bob accepts. A new output file should still permit arbitrary typed names even if completion lists existing files. See [Clap's hint semantics and shell support table](https://docs.rs/clap/latest/clap/enum.ValueHint.html).

### Capture already owns the difficult semantics

`capture-complete` supplies a versioned result with UTF-8 byte replacement ranges, context, descriptions, and domain candidates. Existing scanners cover routes, tasks, sections, links, and named work sessions. `capture/cli.rs::text_arg()` joins multiple trailing arguments into a draft. `capture_complete.rs::build_result()` is currently private, making a small internal read-only service extraction a natural implementation step. See [capture CLI definitions](https://github.com/bobs-org/bob-cli/blob/f11a9f81256a10ee812e47c3a203797262e9c381/src/native/capture/cli.rs) and [the completion service](https://github.com/bobs-org/bob-cli/blob/f11a9f81256a10ee812e47c3a203797262e9c381/src/native/capture_complete.rs).

Shell completion should use this service in-process. It should not spawn a second Bob process or independently recognize the capture language. This follows the accepted thin-client decision: Bob remains the authority for capture grammar and candidate data.

Some picker rows require assigning an ID or a name. They carry `requires_block_id` or `requires_name`, sometimes with an empty or placeholder replacement. A shell completer must omit those action rows. It must never call `capture-task-id`, `capture-pomodoro-name`, a write handler, or a dry-run execution handler to obtain ordinary suggestions. A fully specified selector for a future capture action can be offered if its existing replacement is safe; creating the actual object remains the later capture command's job.

Do not call general command handlers for candidates. For instance, `bob plugins list` may perform a `git pull` unless instructed otherwise. Use the narrow manifest reader directly. Completion is a read-only operation with no network, clipboard, Git synchronization, or vault mutation.

## Implementation approaches compared

| Approach | Strength | Main cost or limitation | Verdict |
| --- | --- | --- | --- |
| Stable Clap static scripts only | Straightforward, no Bob process for ordinary Tab requests, straightforward packaging. | Live values require extra shell-specific machinery; positional support is uneven. | Keep as fallback/export, not the whole “excellent” experience. |
| Clap dynamic engine plus a small Bob integration | One Rust grammar and provider layer; described live values; argument-sensitive completion across shells. | Unstable API/protocol, one process per request, and a few Bob-specific transport/context corrections. | Preferred for the interactive experience. |
| Static grammar plus custom dynamic shell adapters | Static paths remain very cheap and can preserve rich native zsh grouping. | Maintaining context detection, positional overrides, caching, quoting, and three adapters becomes substantial custom completion work. | Credible second choice if profiling invalidates dynamic completion. |
| Hand-written grammar, separate DSL, or ported SASE emitters | Maximum control. | Duplicates Bob's command definitions and expands the maintenance surface. | Avoid. |

As inspected, `clap_complete` provides stable prebuilt generation under `aot` and environment-activated runtime completion behind `unstable-dynamic`. Static fish generation explicitly lacks positional argument support; static Bash handling of unconstrained positionals can fall back to filename completion even where that is inappropriate. These limitations matter for Bob's text and domain selectors. See [the crate API](https://docs.rs/clap_complete/4.6.11/clap_complete/) and the locally inspected `clap_complete/src/aot/shells/{bash,fish,zsh}.rs` at the revision above.

Dynamic completion is not a promise to perfectly reproduce Clap validation. It still needs acceptance tests for trailing text, omitted default subcommands, option values resembling subcommand names, and conflicting or already-used flags. Correct useful candidates are more valuable than an exhaustive but misleading list.

### Controlled probe results

| Check | Observation |
| --- | --- |
| Static delegate-only grammar | Missed `--engine` and enum values for all three shells. |
| Static composed grammar | Included nested commands, flags, and enum values. Bash and zsh syntax checks passed. |
| Dynamic enum completion | `bob query --engine <Tab>` returned `native` and `obsidian`. |
| Dynamic route completion | A prefix `g` returned `groceries` with a description. |
| Dynamic marker completion | `@d` returned marker values; a colon-containing value was escaped in zsh transport. Plain body text returned no candidates in the probe. |
| Bash/zsh registration by sourcing | Both registered a callback for `bob` successfully. |
| Dynamic zsh script placed directly on `fpath` as `_bob` | Its first function-file invocation registered the callback but did not invoke it. |
| Trailing capture text | `bob capture milk --r` suggested `--route`; `bob capture -- milk --r` did not. The first result disagrees with Bob's trailing-text execution semantics. |
| Process timing, 80 warm launches per case | Registration median 1.902 ms / p95 2.004 ms; enum median 1.906 ms / p95 2.004 ms; marker median 1.843 ms / p95 2.004 ms. |

Timings include Python's subprocess launch on this Linux host and exclude vault scans. The probe is small; these are feasibility evidence, not a production latency claim. Full Bob grammar and representative vault measurements remain required.

The two observed semantic failures are release gates:

1. The zsh installed loader must explicitly dispatch the requested completion on its first autoload invocation. Upstream environment registration output is intended to be sourced; it is not interchangeable with a zsh autoload function file. Use a small tested bootstrap wrapper or a narrow `EnvCompleter` adapter, not string replacement of generated grammar or an assumed internal callback name.
2. At the request boundary, detect when Bob's trailing `TEXT` has started. From that point, route completion to the capture service and suppress option/subcommand suggestions, even without an explicit `--`. Use the real argument definitions and semantics for this boundary, rather than a second shell grammar for capture text.

`ArgValueCompleter` receives the current value and a value index, not an entire parsed Bob invocation. Build an explicit per-request context for the selected vault, route, task, decoded trailing text, and cursor. Providers for `--section`, for example, must honor the preceding `--route`; providers must also honor `--bob-dir`, `BOB_DIR`, and the relevant existing configuration. Never invoke normal business-command dispatch to recover that context. See [custom completers](https://github.com/clap-rs/clap/blob/4be56132cf7a5ef6e237409a13225a5829cb24e4/clap_complete/src/engine/custom.rs) and [the shell adapter trait](https://docs.rs/clap_complete/latest/clap_complete/env/trait.EnvCompleter.html).

## Proposed public experience

Retain the familiar SASE spelling, but use fewer commands:

```text
bob completion                            # status, same as list
bob completion bash [-o FILE] [-s]
bob completion fish [-o FILE] [-s]
bob completion zsh  [-o FILE] [-s]
bob completion install [SHELL] [-d] [-f] [-t DIR]
bob completion list [-j] [-v]
bob completion refresh [SHELL] [-d] [-j]
```

- `bash`, `fish`, and `zsh` emit **portable dynamic loaders** by default. `-s/--static` emits a static grammar snapshot for packaging or a fallback. `-o/--output FILE` writes instead of printing. This default deliberately differs from SASE's raw grammar exports; describe it prominently in help.
- `install` selects a shell and destination, checks ownership, installs atomically, and prints activation instructions. `-d/--dry-run` performs no writes. `-f/--force` explicitly permits replacing a foreign or modified completion, preferably retaining a backup. `-t/--target DIR` overrides the destination.
- `list` distinguishes file health and activation evidence. `-j/--json` emits a versioned structured object. `-v/--verify` performs bounded fresh-shell verification; ordinary status need not launch startup files.
- `refresh` refreshes all recorded Bob-owned installs by default, or one named shell, preserving their destinations. It does not create an installation where none was recorded. `-d/--dry-run` touches no files or caches; `-j/--json` reports per-shell outcomes and an aggregate exit status.

Alphabetize commands and listed options; give every public long option its short alias, as required by this project's CLI rules. Candidate and script stdout contains no ANSI sequences or status prose. Human tables and successful-install output can use existing `Styler` behavior, respecting `NO_COLOR` and redirected output.

### Beauty as a practical property

Descriptions should be concise and distinguish similar commands and values. Insert only valid machine values; show note titles, task text, or concise destination information alongside them. Preserve useful ranking from Bob's capture service rather than alphabetizing every live list. Sanitize control characters and collapse multiline descriptions before serialization.

Example status presentation:

```text
Shell  File       Activation      Location
bash   absent     not checked     —
fish   absent     not checked     —
zsh    current    setup required  ~/.zfunc/_bob

Add the displayed fpath line before compinit, then open a new shell.
```

An example successful install should name the chosen shell and its detection source, show the destination, and end with one actionable activation sentence. Do not print a success checkmark for active completion based only on file existence.

Native zsh/fish can display descriptions; Bash generally inserts a plain value list. Do not promise identical visual features across shells. Upstream dynamic zsh currently groups results as generic values, and candidate tags are not automatically exposed as rich native groups. Attractive descriptions and menu behavior are achievable now; separate semantic groups would need a small explicit adapter enhancement. Optional styles should be scoped to `bob`, for example `zstyle ':completion:*:*:bob:*' menu select`, rather than globally changing every command's completion preferences. See [zsh's completion configuration](https://zsh.sourceforge.io/Doc/Release/Completion-System.html) and [fish's completion API](https://fishshell.com/docs/current/completions.html).

## Runtime and installation design

### A self-correcting dynamic loader

Pin the reviewed dynamic dependency version and lockfile. Put the environment completion check before parsing, logging, configuration loading, fallback script extraction, or business dispatch. Use a command-specific variable such as `BOB_COMPLETE` via `CompleteEnv::var()` to avoid accidentally inheriting another application's generic `COMPLETE` setting.

Install a small shell-native bootstrap that resolves the active `bob` from `PATH` and obtains registration code from that same executable when loaded. Execute the emitted shell code as code only at this trusted bootstrap boundary; candidate values are always transported as data. Avoid baking a checkout path or a source workspace binary into a portable loader. Ensure registration names `bob` even if installation invoked an absolute binary path.

On a fresh shell, the loader gets registration appropriate to the currently installed binary. Subsequent requests use the Rust engine and providers. Bash/fish load their drop-ins on demand; zsh needs the first-invocation dispatch correction above. If `bob` is absent, the loader quietly supplies no completion.

Upstream explicitly warns that persisted dynamic registration can become incompatible with a new binary and recommends regenerating it when a shell starts. A portable bootstrap follows that advice without requiring automatic rc edits. An existing open shell can still have an old callback after an upgrade: print a reload/new-shell instruction, and include a way to fail an incompatible completion request quietly. Do not claim an installer can mutate its parent shell. See [the dynamic integration warning](https://docs.rs/clap_complete/latest/clap_complete/env/index.html).

This is a justified departure from copying SASE's “avoid running the CLI at startup” performance policy. The measured small Rust probe costs about 2 ms; SASE's documented Python startup is far larger. Set a budget and measure actual Bob before adding a runtime grammar cache. If later measurements violate it, retain the same public surface and introduce caching internally.

The current Bob lockfile contains Clap **4.6.1** even though the manifest says `4.5`. The inspected `clap_complete 4.6.11` requires Clap **4.6.6** or newer. Adding it therefore needs a deliberate compatible lockfile update and regression checks, not an expectation that `--locked` will resolve it automatically. These versions describe the sources inspected for this report; recheck before implementation.

### Shell choice and destinations

An explicit shell argument wins; otherwise use `$SHELL` as a documented default. Do not infer the interactive shell from the immediate parent: this repository's Just recipes run under Bash even when the user uses zsh or fish. If `$SHELL` is unsupported or absent, explain the explicit-shell remedy rather than guessing. The installed binary can exist even if completion setup cannot finish.

| Shell | Default user location | Activation requirement |
| --- | --- | --- |
| zsh | Existing recorded destination or a known user completion directory; conventional fallback `~/.zfunc/_bob` | Directory on `fpath` before `compinit`, with no earlier conflicting `_bob`. |
| fish | `$XDG_CONFIG_HOME/fish/completions/bob.fish`, falling back to `~/.config/fish/completions/bob.fish` | Fish's completion search path includes that user directory. |
| Bash | A configured `BASH_COMPLETION_USER_DIR` entry's `completions/bob`, else `$XDG_DATA_HOME/bash-completion/completions/bob`, falling back under `~/.local/share` | bash-completion is loaded, or the user explicitly sources this drop-in. |

An explicit target always wins. Preserve a known stamped target before seeking a new one. For zsh, a recognized framework's intended user drop-in can be preferred where its load order is known; do not write into arbitrary plugin or cache directories merely because they are writable. Avoid system locations and elevated permissions for the default workflow.

Support `ZDOTDIR` when printing or checking zsh startup instructions. Verification must check both registration and the effective autoload file, because an earlier `_bob` can shadow the newly written file. Do not automatically remove unrelated completion files, all `.zcompdump` files, or shell security checks. Zsh's official documentation explains search ordering, `#compdef`, and cache behavior. Bash's per-user search directories and lazy loading are documented in the inspected [bash-completion README](https://github.com/scop/bash-completion/blob/00c34614e3a683421a4d1b10f3e72ddf4530af49/README.md).

Bound verification subprocesses by timeout and report unavailable or timed-out verification as such. Keep verification opt-in because loading real startup files can be slow and can execute user-defined initialization. Verify hermetic registration and real Tab behavior in automated tests separately.

### Ownership, atomicity, and honest failure states

Use a small versioned manifest under `$XDG_STATE_HOME/bob-cli/completion/`, falling back to `~/.local/state/bob-cli/completion/`. Record each shell's absolute installed path, representation, generated content hash, loader format revision, and relevant schema identity. Package version alone cannot identify a current source installation: Bob currently stays at `0.1.0` across changes. Static snapshots need a grammar/content identity; a current dynamic loader need not be called stale merely because the live grammar changed.

Write same-directory temporary files with safe permissions, flush and atomically rename, then update the manifest atomically. Refuse symlink or foreign targets by default. An edited file whose hash no longer matches the recorded bytes is not safe to overwrite just because a stamp names it. Refresh reports the conflict without discarding the edit. Dry-run must not create directories, manifests, bytecode, or caches.

An externally managed loader that already exactly equals Bob's current generated loader needs no write and can be reported as current without taking ownership. If it differs, print a precise manual regeneration instruction for the manager's source. Do not write through a symlink into that source or automatically run chezmoi. Track only Bob-owned installations for automatic refresh.

If an explicit target migration is supported, remove an earlier file only after the replacement succeeds and only if its recorded digest still matches. Treat cleanup failure separately from successful publication. Do not silently delete shadowing files that Bob does not own.

Use exit 2 for invalid CLI usage, exit 1 for a failed requested install/refresh, and exit 0 for successful work or an explicit no-op. A partially successful source installation should say “binary installed; completion needs setup/repair,” with the precise remedy. A conventional fallback directory requiring a first-time rc snippet is a truthful `setup required` outcome, not a false registration success.

## `just install`: concrete proposal

The recipe should install all current package binaries, then invoke **that newly installed Bob executable**, never an unrelated `bob` earlier on `PATH` or an assumed `target/release/bob`. A recipe's Bash interpreter must not determine the completion shell.

A tested Just syntax sketch:

```just
[positional-arguments]
install shell="auto" root="":
    #!/usr/bin/env bash
    set -euo pipefail
    bob_completion_shell="$1"
    bob_install_root="${2:-${CARGO_INSTALL_ROOT:-${CARGO_HOME:-$HOME/.cargo}}}"
    cargo install --path . --locked --force --root "$bob_install_root"
    bob_executable="$bob_install_root/bin/bob"
    if [[ "$bob_completion_shell" == "none" ]]; then
        exit 0
    fi
    "$bob_executable" completion refresh
    if [[ "$bob_completion_shell" == "auto" ]]; then
        "$bob_executable" completion install
    else
        "$bob_executable" completion install "$bob_completion_shell"
    fi
```

Usage:

```sh
just install                         # update source binaries and completion
just install zsh                     # explicit interactive shell
just install fish /custom/cargo-root  # explicit binary destination
just install none /tmp/bob-install    # deliberately isolated binary-only install
```

This is a design sketch, not production-ready installation reporting. Validate the shell argument before compiling; print the resolved binary path and partial-success outcomes; report if `PATH` resolves a different `bob`; and document that the portable loader follows the active executable. A post-install completion failure must return nonzero while stating that the binary step already succeeded. `none` is an explicit escape hatch for packaging/CI, not an implicit skip when detection fails.

The sketch intentionally resolves one root and passes it with `--root`. That makes the binary to invoke unambiguous but **overrides Cargo's configured `install.root`**. This is a requirement adjustment to document; users with that setting pass the same directory as the second recipe argument. Native Cargo remains available for full configuration semantics. Avoid silently claiming this abbreviated resolution implements Cargo's whole precedence chain. Cargo installs executables under the chosen root's `bin`, and `--locked` enforces dependency resolution. See [Cargo installation semantics](https://doc.rust-lang.org/cargo/commands/cargo-install.html).

`--force` follows the existing Bob source-install documentation and accommodates replacement across source checkouts; it is distinct from permission to overwrite completion files. Do not forward it to `completion install`. The recipe deliberately uses quoted shell positional arguments instead of interpolation, so spaces and metacharacters in paths remain data. See [Just's recipe parameter guidance](https://just.systems/man/en/recipe-parameters.html).

Leave `install-smoke` isolated: it should verify generation and temporary-target installation under temporary home/XDG paths without changing the research host's real completion. Direct `cargo install --path .` cannot promise to refresh shell configuration; document the subsequent `bob completion install` command. Do not put home-directory installation side effects into `build.rs`.

## Completion scope, latency, and acceptance criteria

The first release should include the full command/option/finite-choice tree, accurate path hints, routes for relevant option values, task/section values where preceding context resolves them, and capture-marker suggestions at the end of the active token. Start with safe existing replacement candidates, including a quoted draft such as `bob capture 'Fix deployment @de…'`. Suppress arbitrary file candidates in prose and query-language slots.

The capture bridge reconstructs the decoded draft from trailing arguments, computes its UTF-8 byte cursor, calls Bob's service, and maps each returned replacement range back into the active argument. A quoted multiword argument must retain all text around the replacement. Preserve marker sigils and suffixes rather than returning the service's bare fragment as the entire word. Shells own shell quoting; Bob owns capture parsing. Never use `eval` on user text to reconstruct arguments.

**Arbitrary cursor-middle edits, multiline drafts, and richer picker actions are not first-release requirements.** If the request cannot be safely mapped into the current token, supply no capture candidate. This is an explicit scope adjustment; the shell transport lacks the editor's full cursor/range contract, and “excellent” must not mean corrupting text in unusual positions. Promote these cases only with transport-specific tests. Keep the Mac capture JSON contract unchanged.

Prefer no persistent value cache until representative scans show it is needed. Rust startup is cheap; recursive vault scans may not be. Proposed acceptance budgets are warm p95 below 20 ms for structure-only completion and below 75 ms for common live candidates on a representative local vault. These are design targets, not measured Bob results. Measure cold and warm cases separately and include a large-vault case.

If necessary, use a bounded, short-lived read-only candidate cache scoped by canonical vault root, provider, route/task context, config identity, and relevant source freshness. Do not share results between vaults, key every cache only by package version, or key every scan solely by the typed prefix. Prefer serving one bounded candidate set across keystrokes. A TTL alone creates a staleness window; expose that tradeoff and invalidate cheaply when inputs change. Cap candidate count and scan work, return empty/stale-safe suggestions on unavailable data, and keep errors off the interactive display. No daemon is warranted by the present evidence.

Required verification for implementation:

1. **Definition coverage:** every visible command has a definition; default bare-command forms, nested commands, hidden aliases, shorts, choices, and help paths are represented. Full tree construction passes `debug_assert()`.
2. **Execution parity:** changing definition visibility/composition does not change capture `--`, trailing hyphen text, fallback scripts, helper JSON, legacy shims, or hand-written parser behavior.
3. **Real shell behavior:** Bash completion callback, fish `complete -C`, and zsh PTY/Tab tests. Include the first zsh Tab after autoload, reloads, aliases, `--flag=value`, short values, spaces, Unicode, colons, brackets, quotes, option values resembling commands, and cursor-suffix preservation/refusal. Pin supported shell versions; do not infer fish or macOS success from Linux zsh tests.
4. **Read-only providers:** fixture vault content remains byte-identical; fake Git/network/clipboard tools are never called; action rows are omitted; context overrides select the correct vault; descriptions cannot inject control sequences or shell code.
5. **Installation:** repeated installs are harmless; recorded targets refresh across shells; foreign, edited, and symlink files are preserved without explicit force; dry-run writes nothing; interrupted publication leaves recoverable state; status identifies missing/shadowed/setup-required/unverified states.
6. **Source workflow:** temporary-root installation invokes the new binary even when an older Bob is earlier on `PATH`; `$SHELL=zsh` survives the Bash recipe; a root containing spaces works; binary failure leaves completion untouched; completion failure reports partial success.
7. **Performance and distribution:** measure actual full Bob/candidate latency; check package contents; keep static snapshots producible from the installed binary. Update README installation/completion instructions and the existing installation smoke test. Run the repository's normal checks for the eventual code change.

## Explicit adjustments to the requested requirements

- Keep completion maintenance automatic in `just install`, but require a first-time startup snippet when the user's shell has no suitable configured loader path. No silent rc edits and no claim to update an already-running parent shell.
- Refresh every recorded Bob-owned shell installation, not only whichever shell happens to launch Just.
- Support Bash, fish, and zsh first. Static library support for additional shells does not imply an equally reliable installer or interactive experience; defer those claims.
- Choose dynamic completion despite its unstable feature flag, with pinned dependencies, fresh-loader generation, and regression gates. Keep a stable static export escape hatch.
- Reuse Bob's capture service, but initially restrict shell capture replacement to contexts that safely map into the active token. Defer arbitrary editor-like cursor manipulation and write-requiring picker actions.
- Resolve and explicitly pass the source-install root so the post-install command cannot accidentally run an old Bob. Document the departure from Cargo's configured `install.root` precedence and allow an explicit override.
- Provide an explicit `just install none` for isolated installs. An unknown shell must not silently select this mode.
- Defer dotfiles deployment, a public structural spec, grammar caching, automatic bytecode compilation, and a resident service unless a measured or concrete integration need justifies them.

## Recommended solution

Implement a complete, pure Clap command-definition tree reused from Bob's existing native builders; retain current handler dispatch initially and cover the few manual/default-form exceptions explicitly. Add a compact `bob completion` family with status, three shell exports, install, and refresh. Use a reviewed, pinned `clap_complete` dynamic engine for the interactive path, safe portable loaders that regenerate registration from the active Bob, and `--static` exports for packaging and fallback.

Supply live values through narrow in-process readers and Bob's existing capture-completion service. Make first-call zsh autoload dispatch and trailing capture-text handling mandatory correctness work. Treat arbitrary cursor mapping conservatively. Install atomically into user locations, preserve ownership, and display activation evidence honestly.

Add `just install` using `cargo install --path . --locked --force --root …`, invoke the exact installed binary to refresh all recorded completion installs and configure the requested/default shell, and print one clear next action if first-time shell setup is needed. This delivers a discoverable and attractive command without duplicating Bob's grammar or importing the complexity that SASE's Python runtime requires.
