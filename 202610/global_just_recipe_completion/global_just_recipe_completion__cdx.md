# Excellent `just` target completion across projects

Researcher: cdx  
Date: 2026-10-04  
Scope: independent research and recommendation; no completion configuration was deployed.

## Decision in brief

Use **`just`'s existing dynamic completion engine, installed globally through chezmoi**. The installed `just 1.58.0` already discovers recipes, reads descriptions, handles imports and qualified module paths, and answers completion requests live. On this machine, the immediate problem is that a fresh interactive zsh has **no `just` completion handler registered**.

For a robust zsh installation, I recommend a small loader around the native shell function, with shell-word normalization to fix a quoted-path defect reproduced below. This preserves upstream parsing and rendering and requires no project-specific files. Defer a separate JSON completion engine, Carapace adoption, and fuzzy-menu changes unless their additional features justify the maintenance.

Native completion does **not** yet provide all of Bob's polish: recipe-specific argument slots, clear semantic groups, and full shell-side matching are separate concerns. The recommendation is excellent live target discovery with a small integration footprint, with those limitations explicitly acknowledged.

## Method and source boundaries

I inspected Bob's completion documentation and adapter, the linked chezmoi checkout, the upstream `just` release source, Carapace's `just` completer, and fzf-tab's documentation. Repositories were opened through `sase repo open`; web browsing was limited to documentation and issue/PR discussions. I did not consult another swarm researcher's report, chat, or findings.

Behavioral experiments used the installed `just 1.58.0`, temporary fixture projects, and real interactive zsh sessions through a pseudoterminal. Fixtures covered private recipes, aliases, imports, modules, parameters, explicit justfiles, quoted paths, and side-effect sentinels. Temporary fixtures were removed afterward. Carapace and fzf-tab were assessed from source/documentation; neither was installed or benchmarked.

Source revisions:

| Source | Inspected revision |
| --- | --- |
| Installed `just` behavior | `just 1.58.0`, executable `~/.cargo/bin/just` |
| Release source used to explain that behavior | `7f4ef81bd6a93faa2b28430912c8e9ab0e3dd29a`, tag `1.58.0` |
| Upstream `just` checkout | `602ee328c9b21361121b498674334012175d4d81`, 21 commits beyond that tag |
| bob-cli | `260a1fe928c82eb61de67c35924e303ef9551ca4` |
| Linked chezmoi | `53960fc09b3aadf9da3c3932f269f140ceda9da8` |
| carapace-bin | `c9cac841afb9ac0265ef7b35b47194756b160d8f` |
| fzf-tab | `24105b15714bfec37989ed5c5b6e60f572253019` |

The newer upstream checkout contains additional module-related completion work. Its features should not be attributed to the installed release without testing.

## What Bryan has now

Bob's model is a small shell adapter querying the installed binary on each Tab. Bob controls command grammar, value providers, grouping, descriptions, path directives, and space insertion. Its zsh adapter passes shell-unquoted words and cursor prefix/suffix separately. See [Bob's completion contract](https://github.com/bobs-org/bob-cli/blob/260a1fe928c82eb61de67c35924e303ef9551ca4/docs/completion.md) and [zsh adapter](https://github.com/bobs-org/bob-cli/blob/260a1fe928c82eb61de67c35924e303ef9551ca4/src/native/completion/adapters/_bob.zsh).

Local observations:

- `bob completion status -v` reports the zsh adapter current and registered as `_bob` at `~/.zfunc/_bob`.
- A fresh `zsh -ic` reports `${_comps[just]-none}` as `none`.
- Chezmoi's `home/dot_zshrc` already adds `~/.zfunc` to `fpath` before Oh My Zsh, restores its precedence afterward, runs `compinit`, and enables `menu select` globally. It also adds Homebrew's completion directory when Brew is available.
- No managed `_just` loader or explicit `just` completion registration appeared in the inspected chezmoi configuration.
- `fzf` is installed; `carapace` is not on PATH.

Therefore this machine's lack of recipe completion is first an installation/registration gap. This finding does not establish the configuration or installed `just` version on Bryan's other machines.

## What native completion already does

The upstream engine switched to dynamic completion in `1.48.0` on 2026-03-23. `1.48.1` fixed the first zsh autoload invocation; `1.49.0` added alias completion control; `1.50.0` added file/directory candidates for positional arguments. Use the installed `1.58.0` as the initial tested baseline rather than reproducing the behavior of old static completion scripts. Sources: [release changelog](https://github.com/casey/just/blob/7f4ef81bd6a93faa2b28430912c8e9ab0e3dd29a/CHANGELOG.md), [dynamic-engine PR](https://github.com/casey/just/pull/3167).

`just --completions zsh` currently emits this small autoloadable loader:

```zsh
#compdef just
source <(JUST_COMPLETE=zsh just)
if [ "$funcstack[1]" = "_just" ]; then
  _clap_dynamic_completer_just "$@"
fi
```

It obtains the shell function from the binary when loaded. That function then asks `just` for candidates on each request. Recipe discovery uses upstream's own search and compiler rather than parsing `--list` text. This architecture already provides the main benefit Bryan likes in Bob: live candidates from the installed command. Sources: [official installation instructions](https://just.systems/man/en/shell-completion-scripts.html), [release entry point](https://github.com/casey/just/blob/7f4ef81bd6a93faa2b28430912c8e9ab0e3dd29a/src/main.rs), [release completer](https://github.com/casey/just/blob/7f4ef81bd6a93faa2b28430912c8e9ab0e3dd29a/src/completer.rs).

Observed results from valid fixtures:

| Request or feature | Installed native behavior |
| --- | --- |
| `just bu<Tab>` | Completes `build`; includes its description |
| Request from a nested directory | Finds the ancestor justfile |
| `import 'imported.just'` | Imported public recipe appears |
| `_hidden` and `[private]` recipes | Excluded from candidates |
| Alias `b := build` | Excluded by default; included with `JUST_COMPLETE_ALIASES=true` |
| `just tools::ch<Tab>` | Completes `tools::check` with its description |
| `just --group <Tab>` | Offers the defined group `quality` |
| `just --set <Tab>` | Offers public variable names |
| `just --color <Tab>` | Offers `always`, `auto`, `never` |
| `-f PATH`, `--justfile=PATH`, `JUST_JUSTFILE=PATH` | Select the intended justfile when PATH is already shell-unquoted |
| Invalid or absent justfile | No recipe candidates, exit 0, stderr empty; CLI flags remain available |

A real interactive zsh test confirmed first-Tab autoload, ordinary target insertion, `::` module insertion, and `alias j=just` with `compdef j=just`. These are stronger evidence than inspecting a generated script alone.

No `RAN_RECIPE`, `RAN_BACKTICK`, or `RAN_DOTENV` sentinel was created by the completion requests. A separate `just --json` introspection request also left them absent. This is consistent with the completion path compiling the justfile without executing its recipes or evaluating runtime assignments. It is a fixture observation, not a blanket sandbox guarantee for every future `just` version.

### Performance

Thirty samples after one warmup, on this machine, with process startup included and output discarded:

| Request | Median | p95 |
| --- | ---: | ---: |
| Native target completion in bob-cli, prefix `in` | 2.63 ms | 3.21 ms |
| `just --json` in bob-cli | 3.08 ms | 3.68 ms |
| Native completion in a synthetic 1,000-recipe justfile | 7.19 ms | 10.16 ms |

These measurements cover backend requests, not a rendered menu or first-Tab `compinit` cost. They support starting without a persistent recipe cache. A cache would introduce invalidation problems across imports, modules, cwd, and explicit justfile selection.

## Gaps that matter when comparing with Bob

**The empty menu is noisy.** At `just <Tab>`, the native backend returned public recipes, public `NAME=` overrides, cwd paths, and 68 long CLI options in the tested release. Its zsh renderer labels candidates as values and treats trailing-slash directories specially; it does not give Bob's semantic recipe/variable/option groups or project-defined group headings. Styling can improve appearance but cannot create missing candidate categories.

**Recipe parameters are not interpreted as distinct completion slots.** After `just deploy `, where `deploy name` requires one argument, completion still offered recipes, variables, files, and flags. After `just tools `, it offered the root candidate set rather than only that module's members. Use the working `tools::check` form for now. The same root set after a zero-argument recipe can be useful because `just` supports multiple recipes in one invocation. A custom implementation must distinguish those situations. The upstream [completion improvement tracker](https://github.com/casey/just/issues/2406) discusses argument awareness, module syntax, hints, and related limitations; my tests establish the specific current behavior independently.

**Backend prefix filtering limits fuzzy matching.** Release `Completer::candidate_recipes` applies `starts_with` before candidates reach zsh. Shell `matcher-list` settings or fzf-tab cannot recover candidates the backend omitted. An empty-prefix menu can still be searched, but typing a non-prefix fragment and then pressing Tab is not full fuzzy target discovery.

**Descriptions depend on project documentation.** Existing recipe comments and `[doc]` attributes provide useful text. Undocumented recipes remain undocumented. The multiline-comment fixture exposed only its last comment line in the candidate description. Rich parameter signatures and recipe-body previews are additional work, not properties guaranteed by native completion.

**Quoted explicit justfile paths fail in the stock zsh adapter.** Both of these real interactive requests failed to extend `al`:

```zsh
just -f "my dir/alternate.just" al<Tab>
just -f my\ dir/alternate.just al<Tab>
```

The same request succeeded when the backend received an already-unquoted path. The generated function passes zsh's raw `words` array to the binary. A local normalization layer using `${(@Q)words}` fixed both forms while preserving the actual command buffer's quoting. This is a concrete integration defect, not a reason to reimplement justfile parsing.

## Alternatives and their tradeoffs

| Approach | What it adds | Costs and limits | Assessment |
| --- | --- | --- | --- |
| Native dynamic completion, global loader | Live recipes, descriptions, imports, native discovery, flags and values | Generic positional menu; stock zsh quoted-path defect | Best foundation |
| Small zsh integration shim around native function | Correct shell-word normalization; clean global ownership and lazy loading | Depends on an upstream shell function name; needs version compatibility checks | Recommended small addition |
| Custom engine reading `just --json` | Signatures, recipe groups, alias presentation, targeted hints, full candidate matching | Must model command-line state, parameters, imports/modules, visibility and platform rules; duplicate CLI grammar can drift | Appropriate only if exact Bob-like presentation is a firm requirement |
| Carapace's existing `just` completer | Tagged recipes, descriptions, parameter/recipe flag support, broad shell support | Adds a framework and parallel CLI model; source shows module/alias parameter lookup gaps | Consider for a broader completion initiative |
| fzf-tab over native candidates | Searchable selection menu and optional previews | Changes shell widget behavior; cannot repair missing candidates or infer argument semantics | Optional interface layer |
| `just --choose` | Built-in fuzzy recipe chooser using fzf by default | Runs selected recipes; skips recipes requiring arguments, private recipes and aliases | Useful separate command, incomplete substitute for Tab |
| Grep justfiles or scrape `--list` | Quick prototype | Fragile around imports, modules, comments, attributes, private recipes and customized list formatting | Avoid |

### Carapace findings

Carapace's recipe action reads `just --dump --dump-format json`, recursively lists modules, attaches descriptions, and tags its output `recipes`. Its argument action reads `just --json`, synthesizes a command from recipe parameters, provides file candidates for parameters, and handles flags represented in parameter metadata. These are useful capabilities absent from native generic positional completion.

However, that argument action looks up `jf.Recipes[c.Args[0]]` at the root. From source inspection, a qualified module recipe or an alias selected from the menu can fail the subsequent lookup. Parameter records also omit default information, and the variadic check only recognizes `star`. The root completer defines a separate CLI flag tree and passes an explicit justfile path to the recipe action; future flags and configuration inputs require independent maintenance. These are source-derived concerns, not reproduced Carapace runtime failures. Sources: [recipe actions](https://github.com/carapace-sh/carapace-bin/blob/c9cac841afb9ac0265ef7b35b47194756b160d8f/pkg/actions/tools/just/recipe.go), [root completer](https://github.com/carapace-sh/carapace-bin/blob/c9cac841afb9ac0265ef7b35b47194756b160d8f/completers/common/just_completer/cmd/root.go).

For a request focused on one installed Rust tool, native completion plus a small integration fix is a narrower maintenance commitment. If Bryan wants a uniform completion framework for many unrelated commands, Carapace deserves a separate evaluation.

### Fuzzy selection and previews

fzf-tab changes selection over existing zsh completions. It does not discover recipes itself. Its documentation requires careful loading relative to `compinit`, autosuggestions, syntax-highlighting plugins, and Tab widget bindings. Bryan already has those plugins plus a late `~/.fzf.zsh` source, so adopting it needs a deliberate integration test. Sources: [fzf-tab documentation](https://github.com/Aloxaf/fzf-tab/blob/24105b15714bfec37989ed5c5b6e60f572253019/README.md), [zsh completion system](https://zsh.sourceforge.io/Doc/Release/Completion-System.html).

A recipe preview should use introspection such as `just --show`, not `just --dry-run` or executing the selected recipe. Preserve explicit file-selection context and pass candidate names as arguments without constructing an unquoted shell command. No preview is needed for the initial solution.

`just --choose` is explicitly a selection-and-execution interface with fewer eligible recipes. It cannot replace editable command-line completion when a recipe needs parameters. See the [official chooser documentation](https://just.systems/man/en/selecting-recipes-to-run-with-an-interactive-chooser.html).

## Concrete implementation direction

Make the production change in the linked **chezmoi** repository, with `home/dot_zfunc/_just` as the global managed loader. The current zsh configuration already includes that directory in `fpath`; no per-project install command or justfile modification is needed.

The following research prototype passed real zsh tests for first-request quoted paths, subsequent ordinary requests, qualified modules, an alias, and backslash-escaped paths:

```zsh
#compdef just
_just() {
  local -a words=("${(@Q)words}")
  if (( ! ${+functions[_clap_dynamic_completer_just]} )); then
    source <(JUST_COMPLETE=zsh command just 2>/dev/null)
    (( ${+functions[_clap_dynamic_completer_just]} )) || return 1
    compdef _just just
  fi
  _clap_dynamic_completer_just "$@"
}
_just "$@"
```

This calls upstream's own generated renderer and engine. Rebinding `just` to `_just` after sourcing matters: the generated script otherwise registers the native function directly, bypassing normalization on later requests. The `words` variable is local, so this layer changes the completion request, not the user's input buffer.

Treat the prototype as a tested design seed, not a fully shipped compatibility layer. It depends on the internal function name `_clap_dynamic_completer_just`, verified with `1.58.0`. A production patch should document its supported version, verify the generated function at installation/testing time, and retire the workaround when upstream performs equivalent normalization. If upstream fixes the defect, use the generated stock loader directly.

Suggested acceptance criteria for that implementation:

1. A fresh normal interactive shell registers `just` to the managed loader, including when another `_just` exists later in `fpath`. Diagnose stale completion dump or `.zwc` files only if encountered.
2. First Tab works; no second-Tab workaround is needed. Switching cwd changes candidates without regeneration.
3. Parent discovery, imports, private recipes, alias policy, `::` modules, and quoted/escaped explicit justfile paths pass fixture tests.
4. Completion never executes recipe bodies, backticks, or dotenv commands in the sentinel fixtures; an invalid or missing justfile leaves the prompt usable.
5. Ordinary flags and enumerated values still complete. Document native argument-slot and space-separated-module limitations instead of claiming exact Bob parity.
6. On Bryan's other machines, verify `just --version`, the selected binary, and handler ownership. Do not assume this host's version or package completion installation is universal.

Use `JUST_COMPLETE_ALIASES=true` if Bryan wants recipe aliases in menus. A shell alias such as `j=just` is separate and can be registered with `compdef j=just`, which was tested. Retain the existing menu-selection behavior initially. Bash or Fish can use their generated adapters when those shells are actually in use; my runtime verification here was zsh-specific.

## Recommended solution

**Install native dynamic `just` completion globally through chezmoi, using the small zsh loader above to normalize shell words and preserve lazy loading.** It will discover targets in each project's actual justfile through the installed binary, with descriptions and qualified module paths, without any bob-cli changes or project opt-in. The installed backend is already fast enough to avoid caching.

Include the quoted-path regression in the initial implementation and pursue an upstream adapter fix so the local shim can shrink to the standard generated loader. Use `::` module paths while native space-separated completion remains limited. Add fzf-tab only if Bryan wants fuzzy menu selection across the shell; choose a JSON-based custom renderer only if separate recipe groups, signatures, and exact argument-slot behavior become explicit requirements. The evidence favors a small global integration change now, with upstream's engine retaining ownership of recipe parsing and discovery.
