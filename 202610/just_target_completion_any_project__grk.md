# Just Target Completion, Any Project

> **Question.** How should Bryan get excellent command-line completion for `just` recipes on every project — the same class of experience he already has for `bob` — without tying the solution to bob-cli?

**Recommendation in one line:** keep `just` 1.58's live binary as the grammar, install a *bob-style static zsh adapter* into `~/.zfunc/_just` (chezmoi-owned, next to `_bob` and `_sase`), and drive it from `just --json` plus a flag-only `JUST_COMPLETE` call. Do not wait on upstream, do not put this in bob-cli, and do not treat `just --completions zsh` as the finished UX.

---

## 1. What "like bob" actually means

`bob` completion is documented in `docs/completion.md` and already live on this machine:

| Property | `bob` today |
|---|---|
| Engine | Hidden `bob __complete` against the binary on `PATH` |
| Adapter | Small static file, protocol 1, **never `eval`s generated code** |
| Install | `bob completion install` → `~/.zfunc/_bob` (status: `current`, registered as `_bob`) |
| First `<TAB>` | Commands only, grouped (`daily workflow`, `tasks and projects`, …) |
| Descriptions | Yes, with group headers `── <group> ──` scoped to `bob` |
| Files | Only when the slot is a path (`!dirs` / `!files` / `!files-in`) |
| Flags | After `-` / `--`, not mixed into the command list |
| Filter | Shell filters; bob returns the full slot |
| Latency | Structural p50 ~11 ms (debug); never writes |

The user's zsh already prefers this layout: `fpath` leads with `~/.zfunc`, `compinit` runs, `zstyle ':completion:*' menu select` is on, fzf is sourced for history (not fzf-tab). Chezmoi already owns `.zfunc` and `.zfunc/_sase`. `_bob` is tool-owned via `bob completion install`. There is **no** `_just` in `~/.zfunc`, site-functions, or vendor-completions.

That last fact is the largest single gap. `just` was installed with `cargo install` (`~/.cargo/bin/just`, 1.58.0, 6 Aug). Cargo does not drop completion scripts. Until an adapter is on `fpath`, TAB for `just` is default filename completion, which is why it feels nothing like `bob`.

---

## 2. What just 1.58 already has

casey/just 1.58.0 (the installed binary, matching the opened `gh:casey/just` tree) switched to clap's **dynamic** completion engine in 1.48.0 (`#3167`). The on-disk `completions/just.zsh` is five lines:

```zsh
#compdef just
source <(JUST_COMPLETE=zsh just)
if [ "$funcstack[1]" = "_just" ]; then
  _clap_dynamic_completer_just "$@"
fi
```

Each TAB then runs:

```text
JUST_COMPLETE=zsh _CLAP_COMPLETE_INDEX=$n just -- "${words[@]}"
```

The engine is `src/completer.rs`. It already:

- Walks up from cwd to find a justfile (and honors `--justfile` / `-g` / `--working-directory` by re-parsing the command line).
- Completes public recipes with `recipe.doc` as help (fish: `name\tdoc`; zsh: `name:doc`).
- Completes `module::recipe` paths (`tests/completions.rs` `module_recipes`).
- Completes `--set` variables, `--group` groups, `--show` / `--list` / `--usage` recipe-or-module slots.
- Hides private recipes (`_banner` in bob-cli's justfile does not appear).
- Completes aliases only with `--complete-aliases` or `JUST_COMPLETE_ALIASES=true` (off by default).
- Prefix-filters inside the binary.

Measured against bob-cli's justfile, empty-prefix `JUST_COMPLETE=zsh` is **3–6 ms** (10 samples, 0.003–0.006 s). `just --json`, `just --summary`, and `just --list` are the same order of magnitude (~4 ms). This is faster than bob's structural complete and well under bob's 20 ms / 75 ms budgets. Latency is not the problem.

### Live transcript (bob-cli justfile)

```text
$ JUST_COMPLETE=zsh _CLAP_COMPLETE_INDEX=1 just -- just ""
all
check-adapter:Not part of `all`: the first run fetches the pinned Python deps.
…
install:completion. Pass shells to choose explicitly: `just install zsh bash`.
…
test
rule=
.
AGENTS.md
CLAUDE.md
Cargo.lock
docs/
justfile
src/
--alias-style:Set list command alias display style
--allow-missing:Ignore missing recipe and module errors
…every long flag…
--help:Print help
```

That dump is the whole quality gap.

---

## 3. Why stock just completion will never feel like bob

### 3.1 One ungrouped "values" list

The generated zsh function splits candidates only into "ends with `/`" vs other, then:

```zsh
_describe -V 'values' dirs -S '/' -r '/'
_describe -V 'values' other
```

clap_complete *does* have `CompletionCandidate::tag()` ("Group candidates by tag. Future: these may become user-visible"). just's completer never sets tags, and the zsh adapter would ignore them anyway. Recipes, cwd files, `name=` assignments, and every `--flag` share one menu titled `values`. bob's adapter walks `value\tdesc\tgroup\tspace|nospace` and `_describe`s each group with a header.

### 3.2 Files are mixed in on purpose

1.50.0 changelog: "Complete files and directories when completing arguments (`#3299`)". `Completer::complete_argument` does:

1. public recipes
2. public assignments as `name=`
3. `PathCompleter::any()` for the cwd

On a rust repo the first TAB is recipes plus `Cargo.toml`, `src/`, `tests/`, `.`, `rule=`, and fifty flags. bob never does this: filename completion is a directive for path slots only, and bash is registered *without* `-o default`.

### 3.3 Flags on the empty prefix

`arguments` is `trailing_var_arg`. clap therefore offers flags together with values when the cursor is on ARGUMENTS. bob's first TAB is commands; flags appear after `-`.

### 3.4 No recipe-parameter slot

`just --json` already knows `install` has a star parameter `shells`, `filter` has `PATTERN`, `watch` has `+args`. The dynamic completer does not. After `just install <TAB>` it offers the same mixed dump again. `[arg(ARG, help=…)]`, `[arg(ARG, long=…)]`, `[arg(ARG, value=…)]` (just ≥ 1.46) are invisible to TAB.

just *can* run several recipes in one invocation (`just fmt lint test`), so after a zero-arg recipe the next word should still be recipes. After a recipe with required parameters, the next word should be that parameter (with a `_message` hint when values are free text). Stock cannot express that.

### 3.5 Docs are last-comment-line only

bob-cli's justfile:

```just
# Install bob and its shims from this checkout, then install or refresh shell
# completion. Pass shells to choose explicitly: `just install zsh bash`.
install *shells:
```

`--list`, JSON `doc`, and completion help all show only the last line (`completion. Pass shells…`). Multi-line docs need `[doc("…")]` or a single last-line comment. This is authoring, not completer logic, but it is why several bob-cli recipes look truncated.

### 3.6 The adapter evals generated code

`source <(JUST_COMPLETE=zsh just)` at autoload time. bob's install ethics (and the earlier `bob_shell_completion_and_just_install` research) are explicit: write a static file, never eval generated code, never edit rc. The clap function is small and the per-TAB path is live, so the risk is low — but it is the wrong shape to copy.

### 3.7 Upstream is not a delivery path

casey/just is **not accepting pull requests** (README note, `#3289` / `#3227`). Improving `completer.rs` (`.tag("recipes")`, `.hide(true)` on PathCompleter unless the prefix looks like a path, recipe-arg completer) cannot ship through a PR. A local fork of just is worse than a 100-line adapter.

---

## 4. Machine APIs for a custom adapter

Three live queries, all ~4 ms on bob-cli's justfile:

| API | Payload | Strength | Weakness |
|---|---|---|---|
| `JUST_COMPLETE=<shell> just -- words` | mixed recipes+files+flags, prefix-filtered, `--justfile`/`-g` aware | already slot-aware for `--set` / `--show` / path flags | presentation is ungrouped; files+flags pollute ARGUMENTS; no params |
| `just --json` (= `--dump --dump-format json`) | structured: recipes, `doc`, `private`, `parameters[]` (`name`, `kind` singular/star/plus, `help`, `long`, `short`, `flag`), `attributes` including `{group: …}`, nested `modules`, `aliases`, `assignments` | the grammar bob would have built | does not list CLI flags; must forward `-f`/`-g`/`-d` yourself |
| `just --list --list-submodules --unsorted` | human grouped-by-`[group:]` text with docs | matches `just --list` UX | text parsing; docs can contain `#` |

casey/just's own justfile is the better grouping demo: `--list --list-submodules` prints `[check]`, `[demo]`, `[dev]`, `[doc]`, `[misc]`, `[release]`, `[test]`. JSON stores those on `recipes.*.attributes` as `{group: "check"}` (the top-level `groups` array was empty in this dump; `just --groups` still lists them). bob-cli's justfile has no `[group:]` yet, so a completer should fall back to a single `recipes` group.

`--summary` is names only (space-separated, includes `mod::recipe`). Fine for a cheap name list, useless for descriptions and groups.

JSON size on bob-cli: ~10.6 KiB including recipe bodies. Fine for TAB. A hostile justfile with huge bodies would still parse in well under bob's vault deadline; if that ever mattered, `--list` is the fallback.

---

## 5. Alternatives

### A. Install stock `just --completions zsh` into `~/.zfunc/_just`

```zsh
just --completions zsh > ~/.zfunc/_just
rm -f "${ZDOTDIR:-$HOME}"/.zcompdump*
```

No rc edit (`~/.zfunc` is already first on `fpath`). After a new shell, TAB is live, described, module-aware, `--justfile`-aware, ~4 ms.

**Do this as a 30-second smoke test**, not as the destination. The mixed files+flags menu will still feel unlike bob, especially with `menu select`.

### B. Stock + zsh cosmetics

`zstyle` cannot split clap's single `values` group into recipes vs files vs flags. fzf-tab is not installed; adding it for one command is a framework change. `JUST_COMPLETE_ALIASES=true` is a one-line env win once an adapter exists. Cosmetics cannot fix 3.1–3.4.

### C. Carapace / fig / generic completion frameworks

carapace is a multi-shell completion library plus `carapace-bin` specs. It is a new always-on stack for one command the user already has a pattern for (`_bob`, `_sase`). Reject unless Bryan wants carapace for many tools.

### D. `just --choose` (fzf)

Already implemented; default chooser is `fzf`, and `~/.fzf.zsh` is sourced. Complementary for "pick one recipe interactively", not a replacement for `just fmt<TAB>` or `just install <TAB>`. Keep using it; do not build completion around it.

### E. Per-project completion snippets / a `justfile` recipe that installs completion

The request is any project. A recipe in bob-cli's justfile does not help a random checkout. A global justfile does not exist (`~/.justfile`, `~/.config/just/justfile` absent). Wrong layer.

### F. A `just` completer inside bob-cli

bob-cli is not a shell-completion product for other tools. Shipping `_just` from `bob completion install` would couple just UX to bob releases and surprise anyone who only wanted bob. Wrong repository.

### G. Patch casey/just

Correct engine fix (tag recipes, hide PathCompleter unless prefix contains `/`, complete parameters from the JSON-equivalent in-process AST). PRs are closed. Local fork of a 6.3 MB cargo binary to change TAB menus is disproportionate.

### H. Bob-style static adapter over live `just` queries (recommended)

Mirror bob's split:

```text
zsh ──TAB──▶ ~/.zfunc/_just   (static, chezmoi-owned, never eval)
                 │  just --json  [-f …] [-g] [-d …]
                 │  JUST_COMPLETE=zsh just -- …     (only when PREFIX is -*)
                 ▼
            grouped _describe, bob-colored headers scoped to just
```

This is the only option that hits the bob quality bar without forking just or adding a framework.

---

## 6. Recommended design

### 6.1 Ownership and install

| File | Owner | Why |
|---|---|---|
| `~/.zfunc/_bob` | `bob completion install` | tool-owned, protocol-versioned |
| `~/.zfunc/_sase` | chezmoi (`sase completion ensure … --owner chezmoi`) | loader |
| `~/.zfunc/_just` | **chezmoi** | just has no `completion install`; `.zfunc` is already chezmoi-managed |

Write the adapter as a chezmoi source file. Print the `fpath=(~/.zfunc $fpath)` line if it is ever missing (it is not, today). Never edit `.zshrc`. After first drop: `rm -f ~/.zcompdump* && exec zsh`.

Optional: `compdef _just just` is implied by `#compdef just`. If Bryan later aliases `j=just`, add `compdef _just j` — oh-my-zsh's fasd/juju plugins already claim `j`, so do not steal that alias.

Bash: bob bash completion is not installed; skip until bash is a real host.

### 6.2 Adapter behavior (zsh, protocol informal)

**Cursor word does not start with `-`**

1. Collect `-f/--justfile`, `-g/--global-justfile`, `-d/--working-directory` from `$words` and pass them through.
2. `just --json` (stderr discarded). Parse failure → empty (same as stock).
3. Emit groups, display order = first appearance:
   - each `[group:]` name, recipes in that group
   - `recipes` for ungrouped public recipes
   - `modules` as `name::` with **nospace** (so the next TAB is `mod::recipe`); also offer full `mod::recipe` paths
   - `variables` as `name=` with **nospace**
   - aliases only if `JUST_COMPLETE_ALIASES` is truthy
4. Skip `private` recipes (leading `_` and `private: true`).
5. Description = `doc` (just's last-comment-line / `[doc]`).
6. After a recipe that still has unsatisfied required parameters: `_message` with `name` + `help` (from `[arg(…, help=)]` when present); if the parameter looks like a path (`name` contains `path`/`file`/`dir`, or `pattern` is set), also `_files`. Still offer further recipes when the last recipe is fully bound, because just accepts multiple recipes.
7. Files: **only** if `PREFIX` contains `/` or `.` as a path prefix, or the current option is a known path flag. Never dump the cwd on a bare `just <TAB>`.

**Cursor word starts with `-`**

Call `JUST_COMPLETE=zsh just -- "${words[@]}"` and keep only lines that start with `-`. That reuses just's own flag help strings and stays in sync when just grows flags. Path-valued flags (`--justfile`, `--working-directory`, `--ceiling`, `--dotenv-path`, `--chooser`, `--cygpath`, `--tempdir`) delegate to `_files`. `--set` / `--show` / `--group` / `--list` / `--usage` delegate to the JSON recipe/variable/group lists (stock already has dedicated completers for these; the adapter should preserve that).

**Presentation** (copy bob's scoped defaults):

```zsh
zstyle ':completion:*:*:just:*:descriptions' format '%B%F{green}── %d ──%f%b'
zstyle ':completion:*:*:just:*' group-name ''
```

Only apply when the user has not set their own format, same as `_bob`.

**Filter policy:** return the full group and let zsh filter (bob rule). Do not prefix-filter in the adapter. `just --json` is not prefix-filtered, which is what we want. Avoid feeding `JUST_COMPLETE` for the recipe slot; it prefix-filters and mixes files.

**Failure:** empty output, exit 0 from the helper's point of view. A broken justfile must not print errors into the menu (stock already `2>/dev/null`).

**Debug:** `JUST_COMPLETE_DEBUG=/tmp/just-complete.log` analog is optional; `just --json` on the same line is enough to debug.

### 6.3 What the adapter should not do

- Cache JSON across TABs. 4 ms is cheaper than invalidation bugs when the justfile changes.
- Eval `just --completions`.
- Complete inside recipe bodies or `{{interpolation}}`.
- Talk to the network, git, or the vault.
- Live in bob-cli.

### 6.4 justfile hygiene (any project, including bob-cli)

These make *whatever* completer looks good, and they are cheap:

1. Put a **single last-line** doc comment, or `[doc("…")]`, so TAB descriptions are the sentence you want. bob-cli's `install` / `check-adapter` / `check-web-clip-adapter` currently show leftover second sentences.
2. Add `[group('check')]`, `[group('install')]`, … so the menu matches `just --list` on projects that already group (casey/just itself is the demo).
3. For useful parameters, `[arg("shells", help="zsh, bash, …")]` so the adapter can `_message` instead of guessing.

Do not block shipping the adapter on rewriting every justfile.

### 6.5 Implementation sketch (size)

A zsh function on the order of `_bob` (60 lines) plus a JSON parse. zsh's `jq`/`python3` are both present on this host; prefer `just --json | python3 -c '…'` only if the zsh JSON parse is painful — a 20-line python helper in `~/.local/lib/just-complete.py` (chezmoi-managed) is acceptable if it stays read-only and silent. Do not add a rust helper; just *is* the rust helper.

If a helper is used, its stdout protocol can copy bob protocol 1 (`value\tdesc\tgroup\tspace|nospace` plus `!files` / `!message`) so `_just` is a near-clone of `_bob`. That is the cleanest long-term shape: one presentation adapter, one tiny JSON-to-protocol filter. Version skew is irrelevant because chezmoi ships both files together.

---

## 7. Decision table

| Approach | Time to first TAB | Feels like bob | Any-project | Drift vs just | Maintain |
|---|---|---|---|---|---|
| Do nothing | — | no (`_just` missing) | — | — | — |
| A. Stock `just --completions zsh` | minutes | no (files+flags soup) | yes | none (live binary) | none |
| B. Stock + zstyle/fzf-tab | hours | no | yes | none | framework |
| C. carapace | days | maybe | yes | spec drift | new stack |
| D. `--choose` only | already there | no | yes | none | none |
| E. per-project / bob-cli | hours | local only | **no** | — | wrong layer |
| G. fork just | weeks | only after engine+adapter work | yes | fork | PRs closed |
| **H. chezmoi `_just` + `--json`** | half day | **yes** | **yes** | flags via `JUST_COMPLETE`; recipes via `--json` | one static file |

---

## 8. Recommended solution

**Ship H, with A as the five-minute preview.**

1. **Tonight, verify the engine:** `just --completions zsh > ~/.zfunc/_just`, new shell, TAB in bob-cli and in `gh:casey/just`. Confirm live recipes+docs. Expect the noisy files+flags list. Delete that file before chezmoi overwrites it, or replace it immediately with the real adapter.
2. **The real artifact:** a chezmoi-managed `~/.zfunc/_just` that is a static bob-style presenter. Recipe/module/variable/group data from `just --json` (forwarding `-f`/`-g`/`-d`). Flags from `JUST_COMPLETE` only when the prefix is `-`. Files only for path slots or a path-like prefix. Group headers copied from `_bob`. No rc edits, no eval, no bob-cli change, no just fork.
3. **Optionally** a 20-line python filter that prints bob protocol 1, so `_just` can share presentation code with `_bob` almost verbatim.
4. **Hygiene, not blocking:** `[group:]` / `[doc]` / `[arg(help=)]` on justfiles you care about, starting with bob-cli's `install` comment.
5. **Keep** `just --choose` for the fzf picker. **Skip** carapace, bash, upstream PRs, and any `just install` recipe that only helps one repo.

Success looks like: in any directory with a justfile, `just <TAB>` shows grouped recipe names with docs, private recipes hidden, no `Cargo.lock` in the menu, `just --<TAB>` shows flags, `just -f other.just <TAB>` uses that file, `just mod::<TAB>` lists that module, and the adapter in `~/.zfunc/_just` is the same kind of file as `_bob`.
