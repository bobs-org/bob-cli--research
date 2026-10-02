# Excellent shell completion for `bob` (+ `just install`): research & recommendation

Researcher: mus · 2026-10-02 · bob-cli swarm
Scope: design shell completion for the Rust `bob` CLI inspired by `sase completion`,
plus a new `just install` target (`cargo install` from source + completion refresh).

All claims below were verified against this checkout (`src/runner.rs`,
`src/native/*.rs`, `justfile`, `Cargo.toml`/`Cargo.lock`) and the live `sase`
CLI on this machine (`sase completion --help` and subcommand helps). Peer
swarm reports were not consulted. Bryan's shell here is zsh (`$SHELL=/bin/zsh`,
`~/.zfunc` on `fpath`, `compinit` in `~/.zshrc`, `_sase` already managed there).

## 1. What `sase completion` actually is (interface inventory)

`sase completion` with no subcommand defaults to `list`. Subcommands:

| Subcommand | Purpose (from `--help`) |
|---|---|
| `bash` / `fish` / `zsh` | Emit a native static script for that shell; `-o FILE` writes instead of stdout. Scripts are static files, never `eval`'d on shell start (sase startup is too slow to pay per-shell). |
| `install [shell]` | Detect shell, pick a directory the shell actually scans, write atomically, `zcompile` (zsh), verify registration, stamp the install. **Never edits `~/.zshrc`**; prints the exact `fpath=(...)` line if registration fails. Flags: `-d/--dry-run`, `-f/--force`, `-t DIR/--target`. |
| `refresh [shell]` | Regenerate stamped installs from the running CLI (`-d` plan, `-j` JSON). Chezmoi-owned targets refresh in place. |
| `list` | Shells × generator/status/path/zwc/stamp/owner/grammar table. |
| `spec` | Structural completion spec as JSON (snapshot artifact). |
| `candidates KIND [PREFIX]` | **Live dynamic values** (`value<TAB>description`, e.g. `project`, `bead`), with `-l/--limit`, `-p/--project`. Served via a pre-argparse fast path. |
| `loader <shell>` | Small shell-native loader resolving the active executable at runtime + asking `ensure` for the cached grammar. |
| `ensure <shell>` | Guarantee a runtime-cached grammar file exists; print its path. Cache hits avoid building the argparse tree. |
| `deploy-chezmoi` | Render portable loaders into a chezmoi source tree (dotfile-manager deployment). |

Architecture in one sentence: **static scripts generated from the live argparse
tree + a live `candidates` hook for dynamic values + install/refresh/stamp
lifecycle + chezmoi-aware deployment.** That layering is the thing worth copying,
not any single flag.

## 2. What `bob` looks like today (the load-bearing facts)

1. **The top-level clap tree is a thin dispatcher, not a real CLI model.**
   `build_cli()` (`src/runner.rs:403`) creates `Command::new("bob")` with
   `subcommand_required(true)` and registers ~25 subcommands via
   `delegate_subcommand()` (`runner.rs:427`), which sets
   `.disable_help_flag(true)` and a single trailing `args: OsString` catch-all
   (`trailing_var_arg(true)`, `allow_hyphen_values(true)`). Every subcommand's
   real flags are parsed *after* dispatch, inside each native module or script.
2. **Subcommand arg parsing is split-brain.** 24 of ~36 `src/native/` modules
   build their own internal clap `Command` (e.g. `capture_complete.rs`,
   `capture_parse.rs`, `freshness/cli.rs`, `gkeep/cli.rs`, `plan_budget/cli.rs`);
   the rest hand-roll parsing (e.g. `pomodoro.rs:198` `parse_args` loops over
   `OsString`s). There is **no single `Command` value that knows every flag**.
3. **`clap_complete` is NOT currently a dependency** (`Cargo.toml` has only
   `clap 4.5`; lockfile has `clap 4.6.1`/`clap_builder 4.6.0`, no
   `clap_complete`). It is readily available upstream (`clap_complete 4.6.x`,
   generators for bash/elvish/fish/powershell/zsh).
4. **Name-collision caution:** "completion" already means something in bob-land:
   `capture-complete`, `capture-parse`, and the `*-completion` *contexts* in
   `docs/capture.md` are about completing capture markers for the macOS picker,
   not shell completion. A `bob completion` subcommand does not collide
   lexically (distinct subcommand names), but docs/help must disambiguate.
5. **`just install` does not exist; `install-smoke` does.** The justfile's
   `install-smoke` recipe runs `cargo install --path . --locked --root <tmp>`
   and smoke-checks `--help` for every subcommand — an excellent template for
   the real target. `cargo install` never installs shell completions on its
   own, so the "also update completion" step must be explicit scripting.
6. **Help text is already completion-feedstock.** `runner.rs` has custom
   `cli_styles` and curated `about` strings per subcommand; whatever generator
   we use will surface these as completion annotations, so they need an audit
   pass (some are long; zsh descriptions want one line).

## 3. Critique of the plan as stated

**Is this a good idea? Yes — with three adjustments (flagged ADJ-1..3).**

- Shell completion is high-leverage here: bob has 25+ multi-word hyphenated
  subcommands (`capture-task-sections`, `task-status-hooks`, …) that nobody can
  reliably type from memory. Completion turns discovery into a non-problem.
- `just install` from source via `cargo install` is the standard Rust-CLI
  distribution story and matches the existing `install-smoke` pattern.

**Critique 1 — `sase completion` is the wrong *size* of inspiration.**
sase's system (grammar cache, loaders, `ensure`, chezmoi deploy, stamps) exists
to serve a Python CLI with slow startup and a dotfiles manager. Porting all of
it to bob on day one would be gold-plating: `clap_complete`-generated static
scripts load in microseconds and have no startup-cost problem, so
loader/ensure/grammar-cache machinery buys nothing. **Take the layering
(static emit + install + refresh + dynamic candidates later), not the whole
apparatus.**

**Critique 2 — the dispatcher architecture caps what static generation can do.**
Running `clap_complete::generate` on today's `build_cli()` yields subcommand
*names* only — every subcommand looks flag-less to the shell because flags live
behind `trailing_var_arg`. Full flag completion requires promoting real arg
definitions into the top-level tree (see Option B). The plan should be explicit
that v1 completes names and v2 completes flags, or v1 will feel broken the
first time someone tabs after `bob capture-complete --`.

**Critique 3 — `just install` silently mutating shell state needs guardrails.**
"When `just install` is run, completion should also be updated" is fine as a
default, but it must be (a) per-shell correct (zsh → `~/.zfunc/_bob`; bash →
bash-completion dir; fish → `~/.config/fish/completions/`), (b) non-destructive
(atomic write, never touch `*rc` files — mirror sase's rule), (c) skippable
(env var / separate recipes), and (d) honest about staleness (static scripts
rot when the CLI changes; install must print a refresh path).

**ADJ-1 (name): use `bob completion`, mirroring sase, despite the
capture-completion homonym.** Consistency across Bryan's tools beats the
collision risk; disambiguate in help text ("shell completion", never bare
"completion" in descriptions).

**ADJ-2 (shell coverage): ship zsh + bash + fish generators, install for the
detected shell.** Bryan lives in zsh, but "excellent" means not zsh-only, and
`clap_complete` gives all three (+ elvish/powershell) nearly free.

**ADJ-3 (dynamic values are v2, but reserve the hook name now):**
bob's killer completion feature is vault-aware values (`--route` targets,
note names, pomodoro ids, task block ids — the `candidates` equivalent).
Building that in v1 doubles scope (vault I/O in a completion path has latency
and failure modes sase handles with dedicated fast paths). Reserve
`bob completion candidates KIND [PREFIX]` in the interface now; implement it
in v2 backed by the existing `capture-targets`/`capture-sections`-style JSON
listers.

## 4. Options considered

### Option A — `clap_complete` static scripts on the current tree (v1 floor)
Add `clap_complete` as a dependency; add `bob completion <shell>` that calls
`clap_complete::generate(shell, &mut build_cli(), "bob", &mut out)` for
bash/fish/zsh (+ elvish, powershell free). `just install` runs
`cargo install --locked --path .` then `bob completion <detected-shell> -o <dir>`.
- Pros: ~50 lines of Rust, zero architecture change, deterministic, testable
  (snapshot the generated scripts; the repo already snapshot-tests help text —
  see `subcommands_are_sorted_alphabetically`, runner.rs:638).
- Cons: completes subcommand names + `--help`-ish only; flags invisible (see
  Critique 2). Static scripts rot on CLI change with no stamp/refresh story
  unless we add one.

### Option B — promote real arg definitions into the top-level tree (v2 core)
Refactor so each subcommand's clap `Command` (the 24 modules that already have
one) is registered on the top-level `bob` command instead of behind
`delegate_subcommand`, with the dispatcher passing `ArgMatches` down rather
than raw `OsString`s; convert the hand-rolled parsers (pomodoro et al.) to
clap builders. Then `clap_complete` output covers every flag automatically,
and `--help` per subcommand comes from the same definition (today each module
prints its own help because the top level disables the help flag).
- Pros: one source of truth for parse + help + completion; full flag
  completion for free; kills the split-brain.
- Cons: the biggest refactor here — must preserve exact current help output,
  exit codes (`run_bob`'s error paths), hidden aliases
  (`HIDDEN_SUBCOMMAND_ALIASES`), and the script-delegation fallback. Needs a
  per-subcommand parity test before/after. This is weeks-vs-days compared to A.

### Option C — sase-style dynamic completion system (v3 crown)
Static skeleton (from A or B) + `bob completion candidates KIND [PREFIX]`
backed by vault listers + `install`/`refresh`/`list` lifecycle + shell scripts
that call back into `bob` for kinded slots. This is what makes completion
*beautiful* (tab through `@routes`, note names, pomodoro ids with
descriptions), and sase proves the pattern — including the hard-won lessons:
never `eval` slow output on shell start, cache grammar, bound candidate counts
(`-l` default 200), stamp installs so `refresh` knows what to regenerate.
- Cons: vault I/O at tab-press latency; needs timeouts, failure-silence, and
  caching. Overkill before A+B exist.

### Option D — hand-written static scripts checked into the repo
A bespoke `_bob`/`bob.bash`/`bob.fish` maintained by hand.
Rejected: guaranteed rot, no help-text reuse, strictly worse than A on every axis.

## 5. Recommended solution (phased)

**Phase 1 — static + install plumbing (this change).**
1. Depend on `clap_complete` (pinned, `--locked`-compatible).
2. New `bob completion` subcommand with a sase-shaped subset:
   `bob completion {bash,fish,zsh} [-o FILE]` (emit) and
   `bob completion install [shell] [-d/--dry-run] [-f/--force] [-t DIR]`
   (detect via `$SHELL`, atomic write to the shell-scanned dir, `zcompile`
   when available, never edit rc files, print the `fpath` line on failure).
   Default with no args: print install *status* (sase's `list` behavior).
3. New `just install` target:
   `cargo install --locked --path .` (default root `~/.cargo`, overridable),
   then refresh completion for the detected shell, then print what changed +
   any manual step (e.g. "restart shell / run compinit"). Split into
   `just install-bin` and `just install-completions` so each half is
   independently runnable and skippable; `just install` runs both. Reuse the
   `install-smoke` per-subcommand `--help` checklist as the post-install
   verification gate.
4. Tests: snapshot generated scripts per shell; golden test that every
   `SUBCOMMANDS` name appears in each script; `just install` dry-run test.
5. Audit `about` strings to one-line completion-friendly descriptions.
6. Reserve (document, don't build): `candidates`, `refresh`, `spec`.

**Phase 2 — real flag completion (Option B).** Promote per-module clap
definitions to the top-level tree behind a parity harness; static scripts get
full flags with no interface change.

**Phase 3 — vault-aware dynamic values (Option C).**
`bob completion candidates {route,note,pomodoro,…}` + shell hooks calling back
with timeouts + `refresh`/stamp lifecycle.

**Why this phasing is beautiful, not just incremental:** each phase leaves the
interface a strict superset of the last (emit → install → full flags →
dynamic values), so users learn one `bob completion` mental model on day one
and it never breaks. Intuitive (mirrors `sase completion` verbs Bryan already
knows), reliable (static-first: completion never shells out to vault I/O in
v1, so tab can never hang), and beautiful (curated descriptions, styled help,
and eventually vault-aware candidates with human descriptions).

## 6. `just install` sketch

```just
install: install-bin install-completions
    @echo "installed $(bob --version) + completions"

install-bin:
    cargo install --locked --path .

install-completions:
    #!/usr/bin/env bash
    set -euo pipefail
    shell="$(basename "${SHELL:-zsh}")"
    case "$shell" in
      zsh) dest="${COMPLETION_DIR:-$HOME/.zfunc}/_bob" ;;
      bash) dest="${COMPLETION_DIR:-$HOME/.local/share/bash-completion/completions}/bob" ;;
      fish) dest="${COMPLETION_DIR:-$HOME/.config/fish/completions}/bob.fish" ;;
      *) echo "unsupported shell: $shell (COMPLETION_DIR override available)"; exit 0 ;;
    esac
    bob completion "$shell" -o "$dest"
```

`cargo install` details worth pinning down at implementation: `--locked` for
reproducibility (matches `install-smoke`); no `--force` by default (fail loud
on version conflicts rather than surprising); note `cargo install --path .`
ignores uncommitted filename changes only, content is always fresh — but same
version reinstalls need `--force`, so document it.

