# Bob-Grade Tab Completion For `just` Recipes, In Any Project

> **Question:** Bryan wants command-line completion for `just` targets that is as good as
> the completion he has for `bob`, and that works in every project, not only bob-cli. What
> is the best way to build it? This report ends with a recommendation.
>
> **Lead consolidation** · 2026-10-04 · It merges four independent reports
> ([cdx](global_just_recipe_completion__cdx.md), [cld](global_just_recipe_completion__cld.md),
> [grk](global_just_recipe_completion__grk.md), [gem](global_just_recipe_completion__gem.md))
> with the lead's own checks on athena: zsh 5.9, just 1.58.0, jq 1.7, and Bryan's
> interactive shell driven through tmux.

## Bottom line

**Ship a chezmoi-managed, bob-style zsh adapter at `~/.zfunc/_just`.** It reads recipe
data from `just --dump --dump-format json` through a small jq program. It hands only
just's own option names to just's built-in completer. It renders grouped menus the same
way `_bob` does.

- **Start from cld's tested prototype**
  ([Appendix A](global_just_recipe_completion__cld.md#appendix-a--prototype-_just-tested)),
  plus the three fixes listed under [changes to the prototype](#changes-to-the-prototype).
- **Phase 1 is roughly a half-day to a day of work.** It needs no new binary, no rc edits,
  no change to bob-cli, and no fork of `just`.
- **One `chezmoi apply` covers athena, apollo, and mac.**

Three of the four reports reached this design independently (cld, grk, gem). cdx
recommended installing just's stock completion behind a small shim instead. The lead's
side-by-side tests in a real shell settle that disagreement:

- The stock completer cannot meet the bob standard.
- gem's `--list`-parsing variant fails outright in compsys.
- cld's JSON adapter works, at about 11 ms per Tab on the largest justfile Bryan owns.

## 1. Where things stand

| Fact | Evidence |
|---|---|
| **No host completes `just` today.** A fresh `zsh -i` has `_comps[just]` unset, so Tab falls back to filenames. | lead, cdx, grk on athena; cld also checked apollo (just 1.50.0) and mac (1.56.0) |
| **The cause is installation, not capability.** just comes from `cargo install`, which ships no completion files. Oh-my-zsh has no `just` plugin. | all four reports |
| **`~/.zfunc` is first on `fpath`**, both before and after oh-my-zsh. chezmoi already ships `home/dot_zfunc/_sase` there, and `bob completion install` writes `_bob` there. | chezmoi `home/dot_zshrc` lines 19 and 47 |
| **Completion runs while Bryan types**, not only on Tab: the live strategy is `ZSH_AUTOSUGGEST_STRATEGY=(atuin history completion)`. Per-call latency therefore matters. | lead (`zsh -ic`); cld |
| **jq is on every host:** 1.7 on athena and apollo, 1.7.1-apple on mac. | cld (cross-host), lead (athena) |
| **`j` is already `alias j=jrnl`.** Do not claim `j` for just (gem's `#compdef just j` would). | lead |
| **Bryan's justfiles are plain.** sase has 97 public recipes, 50 of them with parameters. bob-cli has 12, and 7 have no doc comment. None use `[group]`, modules, aliases, or `[arg]`. | cld |

### The bar: what `bob <TAB>` does

bob's design is in `docs/completion.md`. Each Tab is answered live by the binary on
`PATH` through a ~60-line adapter that speaks "protocol 1":
`value⇥description⇥group⇥space|nospace`, plus directives such as `!files` and
`!message`. The adapter turns those lines into `_describe -V` groups with scoped
`── group ──` headers.

From that, the bar a `just` completer must meet:

1. **Grouped headers.** Candidates appear under labelled sections, not one flat list.
2. **Every row described.**
3. **No options until you type `-`.**
4. **No filenames where a command is expected.**
5. **Context-dependent values.** After a recipe, offer that recipe's parameter.
6. **Fast and read-only.** bob's structural `bob <TAB>` is about 11 ms p50, and it never
   writes anything.

## 2. just's built-in completion: what it does and does not do

Since 1.48 (#3167), `just --completions zsh` prints a four-line loader. The loader
sources `JUST_COMPLETE=zsh just`, which is clap_complete's dynamic engine wired to
just's own `src/completer.rs`.

### What it gets right

All four reports agree on these:

- **Finds the right justfile.** It searches upward from the current directory.
- **Recipes come with their doc text**, and `mod::recipe` paths complete.
- **Hides private recipes.** Aliases appear only with `JUST_COMPLETE_ALIASES=true`.
- **Completes option values:** `--set`, `--show`, `--group`, `--color`, and others.
- **Never runs justfile code.** cdx, cld, and the lead each checked this with a
  sentinel-file justfile.
- **Fast:** 3 to 8 ms.

### What it gets wrong

Each row below was measured by the researchers named; the lead reproduced the first
three in a real shell.

| Defect | Detail | Source |
|---|---|---|
| **A bare `just <TAB>` is mostly noise.** | bob-cli: 98 candidates, of which 68 are options, 17 are paths, and 12 are recipes. sase: 232 candidates. The 7 undocumented recipes in bob-cli land in the last rows, among the files. | cld (counts); cdx, grk, lead (shell) |
| **No parameter slots.** | After `just deploy `, it offers the same mixed list again instead of `deploy`'s `env` values. | cdx, cld, grk, lead |
| **`just mod <TAB>` lists the root recipes.** | Only the one-word form `mod::` works (casey/just#3729). | cdx, cld |
| **Quoted `-f` paths break completion.** | `just -f "my dir/x.just" al<TAB>` completes nothing, because the stock zsh function passes raw, still-quoted words to the engine. | cdx; lead |
| **One flat `values` group.** | Recipes, files, `VAR=` overrides, and flags share one menu. Even if just set clap's `CompletionCandidate::tag`, the zsh writer ignores it. | cld, grk, gem |
| **Filtering happens inside the binary.** | Candidates are pre-filtered with `starts_with`, so shell-side or fuzzy matching cannot recover what the backend dropped. | cdx |
| **Only the last comment line becomes the doc.** | This is just's own rule (`Parser::take_doc_comment`), not clap's as gem states. It affects `--list` too. | cld, grk |
| **Empty option values ignore `-f`.** | `JUST_COMPLETE … just -f "my dir/alt.just" --show ""` returns the recipes of the *current directory's* justfile. With prefix `a` it correctly returns `alpha alright`. `--set ""` behaves the same way. Cause: the empty value makes the command line invalid, so `Completer::config()` fails and falls back to the default search. | **lead (new)** |

**The upstream fix is not coming soon, and Bryan cannot contribute it.** The lead
re-checked the state of each item on 2026-10-04:

- **No pull requests.** The README says just "is not currently accepting pull requests"
  (#3289, 2026-04-11).
- **No new release.** 1.58.0 is still the latest. The 21 commits since then include
  #3716 (complete `--clean` and `--list`) and #3717 (tree order). Neither addresses the
  defects above.
- **The bare-Tab defect is unanswered.** #3729 was opened 2026-09-30 and has no reply.
- **#2406 is still open.** In it, casey calls position-aware completion "tough" and says
  he may *drop* doc comments from completions.
- **Grouping in zsh needs two upstream changes.** clap-rs/clap#6334, "group options by tag
  in zsh", is an open, unmerged PR; its last activity was 2026-08-31. just would then also
  have to tag its candidates.
- **Others are working around the same gap.** laurigates/dotfiles#252 keeps a
  hand-written JSON-based `_just` until upstream catches up.

cdx's suggestion to "pursue an upstream adapter fix" is therefore limited to issue
comments.

## 3. Options compared

| Option | Verdict | Deciding evidence |
|---|---|---|
| **A. Stock loader** (`just --completions zsh` saved to `~/.zfunc/_just`) | Use only as a quick preview and as the fallback when jq is missing | It fails bar items 1–5 (§2). |
| **A′. Stock loader plus cdx's shim** (shell-unquotes the words, re-registers `_just`) | A good fix *for the stock path*; its unquoting idea carries into the recommended adapter | It fixes quoted paths only. The menu is still the noisy flat list. |
| **B. Stock loader plus `zstyle` tuning or fzf-tab** | Rejected as the fix | Every candidate shares one tag, so `zstyle` has nothing to group by. `ignored-patterns` would also hide flags after `-`. fzf-tab changes all of Bryan's completion and still cannot add parameter slots. |
| **C. Custom zsh adapter: `--dump` JSON plus a jq binder, with just's engine for option names** (cld; grk's variant) | **Recommended** | It passed every lead test in Bryan's shell. It costs 10.6 ms on sase. It needs only jq, and it works with just 1.50, 1.56, and 1.58. |
| **D. Custom adapter parsing `just --list` text in pure zsh** (gem) | Rejected | Every Tab fails with `_just:126: bad pattern: #*` (details in §4). |
| **E. Adapter plus a Python filter** (grk's optional idea) | Rejected | Python startup costs 82 ms through the pyenv shim and 17.6 ms for `/usr/bin/python3`, against 2.9 ms for jq. That cost would land on every keystroke under autosuggest. |
| **F. A small Rust helper speaking bob protocol 1** | Runner-up; revisit only if the jq program grows past ~300 lines | It is more testable, but adds a crate, a repo, and `cargo install` on three hosts, plus version skew between helper and adapter. |
| **G. carapace's `just_completer`** | Rejected | It is not installed anywhere, and it would take over shell completion broadly. It also has a hand-maintained flag list. Its parameter lookup only checks root recipes (`jf.Recipes[c.Args[0]]`), so `mod::recipe` and aliases fail. It treats `+` variadics as single values. The earlier bob research rejected carapace for the same reasons. |
| **H. Fork just, or patch `completer.rs`** | Rejected | It would replace the machine-wide `just` on every host and need permanent rebasing, since PRs are closed. |
| **I. Put it in bob** (for example, `bob completion install just`) | Rejected | That couples a general developer tool to a vault CLI's release cycle. Copy bob's *rendering*, not where it lives. |
| **J. A per-project recipe or completion snippet** | Rejected | It does not help in "any project". |
| **K. `just --choose`** (fzf) | Keep alongside; it is not a replacement | It runs the recipe immediately. It skips recipes that need arguments, private recipes, and aliases. |

## 4. Disagreements between the reports, resolved

1. **Native shim (cdx) or custom adapter (cld, grk, gem)?** Use the custom adapter. cdx
   itself concedes that native completion "does not yet provide all of Bob's polish". The
   gap is structural (one tag, no position awareness), and upstream cannot accept a fix.
   Three of cdx's findings carry forward:
   - the quoted-word normalization with `${(@Q)…}`
   - the sentinel safety test
   - checking just's version on each host
2. **JSON (cld, grk) or `--list` text (gem)?** Use JSON. The lead tested gem's
   "production-ready" script in Bryan's shell, and every Tab failed with
   `_just:126: bad pattern: #*`. Three reasons:
   - **It breaks under compsys.** compsys always runs completion functions with
     `extendedglob`, so `${rest%%#*}` is an invalid pattern.
   - **The `--list` format is user-configurable.** `JUST_LIST_PREFIX`,
     `JUST_LIST_HEADING`, and `JUST_ALIAS_STYLE` reshape it.
   - **It drops information.** It shows `test [OPTIONS]` instead of the recipe's actual
     `[arg]` options.

   gem's script also hard-codes about 45 just options, which will drift as just adds
   new ones.
3. **Latency.** gem reported 12.4 ms for `JUST_COMPLETE` and 12–18 ms of jq overhead. The
   lead could not reproduce either number. On sase's 97-recipe justfile (104 KB of
   JSON), measured with `hyperfine`:

   | Path | Mean |
   |---|---|
   | `just --dump --dump-format json` | 6.4 ms |
   | `just --list --unsorted --list-submodules …` | 6.4 ms |
   | stock `JUST_COMPLETE=zsh`, empty word | 6.8 ms |
   | `--dump` piped into cld's jq binder (full program) | **10.6 ms** |
   | `jq -n 1` (jq startup alone) | 2.6–2.9 ms |
   | `bob <TAB>` structural (`docs/completion.md`), for reference | 10.9 ms p50 |

   The JSON approach costs about 4 ms more than the stock completer and matches bob's
   own speed. No cache is needed; all reports agree a cache would cause invalidation
   bugs.
4. **Which option values go to just's own engine?** cld sends every option value to it;
   grk serves recipe-, variable-, and group-valued options from the JSON. The lead's new
   `-f` finding (§2) favors grk: on an empty word, the engine reads the wrong justfile.
5. **Who owns the file?** chezmoi, unanimously. The `fpath` entry already exists, so no
   rc edit is needed. grk and gem note that the stock loader `source`s generated code
   when it is first loaded. That happens inside the completion function, not in rc, so
   it does not break bob's rule against `eval` in rc files. It is still another reason
   to prefer a static file.

## 5. Recommended design

```text
zsh ──TAB──▶ ~/.zfunc/_just     (chezmoi: home/dot_zfunc/_just[.tmpl], static, never sourced/eval'd)
              │ walk just's global options; keep only those that choose the justfile:
              │   -f/--justfile  -d/--working-directory  -g  --justfile-name  --ceiling
              ├─ word starts with `-` before any recipe ──▶ JUST_COMPLETE=zsh just -- ${(@Q)words}
              │     (option names only)                     rendered as ── just options ──
              ├─ value of a path option ──▶ _files / _files -/
              ├─ value of --show/--usage/--set/--group/-l ──▶ recipes/variables/groups from the JSON
              ├─ value of a fixed-choice option (--color, --dump-format, …) ──▶ JUST_COMPLETE
              └─ otherwise ──▶ just <search flags> --dump --dump-format json
                                 └─▶ jq binder ──▶ value⇥desc⇥group⇥space|nospace | !message | !files
                                       └─▶ grouped _describe -V, `── group ──` headers scoped to just
```

### Behavior

Rows were verified by cld's tmux captures and re-run by the lead where marked ✓.

| Cursor | Candidates |
|---|---|
| `just <TAB>` ✓ | `── recipes ──` (ungrouped), then one header per `[group]`, then `── modules ──` as `tools::` (no trailing space). **No options, files, or `VAR=` entries.** |
| `just p<TAB>` | As above, plus `── variable overrides ──` (`profile=`, no trailing space) |
| `just -…` before a recipe | just's own options, from the installed binary |
| `just deploy <TAB>` ✓ | That recipe's parameter: the choices from `[arg(pattern='staging\|prod')]`, or a hint (`target · build (default all)`) plus files |
| `just test --<TAB>` ✓ | That recipe's own `[arg(long/short)]` options under `── options · test ──` |
| Recipe's parameters all filled | The next recipe, since just runs several recipes per invocation (`just fmt lint test`) |
| `just tools <TAB>` ✓ / `just tools::<TAB>` | That module's recipes. This also covers #3729. |
| `just -f "my dir/x.just" al<TAB>` ✓ | Recipes from that file |
| Unknown recipe, or a broken or missing justfile | A one-line `_message` (for example `just: no justfile found`); never a stack of errors |

**How the binder places the cursor.** The binder copies `src/invocation_parser.rs` rule
for rule:

- **Positionals fill greedily.** A `*` or `+` parameter keeps consuming words.
- **Recipe options** may appear anywhere until `--`.
- **A recipe with no `[arg]` options** treats `--` as an ordinary value.
- **`NAME=VALUE` overrides** count only before the first recipe.

**Descriptions** show the signature first, then the doc:
`[target=all] [flags…] · Build everything`.

### Changes to the prototype

cld's Appendix A passed every lead test. Apply these changes before shipping:

1. **Unquote words before calling just's engine.** In `_just_clap`, pass
   `"${(@Q)words}"`, not `"${words[@]}"` (cdx's normalization).
2. **Serve recipe, variable, and group values from the JSON.** For `--show`, `--usage`,
   `--set`, `--group`, and `-l`, read the JSON with the forwarded search flags. Use
   `JUST_COMPLETE` only for option names and fixed choices. This avoids the engine's
   empty-word `-f` bug (§2).
3. **Fall back to the stock engine when jq is missing**, rather than going silent.

Defer cld's other P2 gaps to polish:

- show short and long forms on one row
- respect `$SUFFIX` when the cursor is mid-word
- de-duplicate variadic choices
- honor `JUST_COMPLETE_ALIASES` with an `aliases` group
- hide recipes restricted to another OS (`[linux]`, `[macos]`)
- mark `[confirm]` recipes and the default recipe
- add the parent justfile's recipes when `set fallback` is on

### Packaging and tests

- **File layout (in chezmoi).** cld proposes:
  - `home/dot_zfunc/_just.tmpl` for the adapter
  - `home/.chezmoitemplates/just_complete.jq` for the jq program, inlined with
    `{{ include }}` (not `template`). Tests can then run the program directly with
    `jq -f`.

  Neither directory exists yet. Keep `{{` out of the zsh text, or ship the `.jq` file
  as its own deployed file instead.
- **Rollout.**
  - Do not `zcompile` the adapter.
  - After the first `chezmoi apply`, run `rm -f ~/.zcompdump*` and start a new shell.
- **Tests.** Add `tests/zsh/` next to chezmoi's existing `tests/bash`, `tests/nvim`, and
  `tests/hammerspoon`:
  1. **jq golden tests** over fixture justfiles. Cover every row of the behavior table,
     plus `[group]`, modules, `[arg]` long/short/`value=`, `pattern` as a string
     (just 1.50) and as an array (1.55 and later), expression defaults, aliases, private
     recipes, and broken files.
  2. **A tmux real-shell smoke test.** This is how cld and the lead verified the
     behavior. Skip it when tmux is absent.
  3. **A drift test.** The adapter's list of value-taking global options must match the
     `<METAVAR>` options in `just --help`.
  4. **A safety test.** Completing against a sentinel justfile (backticks, `shell()`,
     parameter defaults) must create no files. Never call `--evaluate`, which does run
     backticks.

### Risks

| Risk | Mitigation |
|---|---|
| **The binder duplicates one just rule (argument binding).** If just changes it, the adapter gives a wrong hint. It never produces a wrong command. | Golden tests; re-check on each just release. |
| **A JSON field changes.** The dump has been stable since #1633, with additive changes only; `pattern` changing from a string to an array is already handled. | Golden tests run on all three just versions. |
| **jq treats recipe options as its own flags.** | Pass the words with `--args --` (already done in the prototype). |
| **Hosts run different just versions.** | `just --version` check in the smoke test. |

## 6. Justfile conventions that make completion excellent

These conventions improve *every* completer, including upstream's, and `just --list`. Do
not hold up the adapter for them.

| Convention | Effect | Where it pays off now |
|---|---|---|
| `[doc('One-line summary')]` on recipes with multi-line comments | A clean description instead of a fragment | sase: 40 of 94 recipes. bob-cli: `install`, `install-all`, `check-adapter`, `check-web-clip-adapter`. |
| A one-line comment on every public recipe | No blank rows in the menu | bob-cli: `all`, `fmt`, `lint`, `test`, … (7 of 12) |
| `[group('…')]` in large justfiles | Each group becomes a `── group ──` header | sase |
| `[arg('p', pattern='a\|b', help='…')]` | Validation, completion choices, and a hint from one annotation | bob-cli `install *shells`; bob-mac-capture `install` |

cld tested the bob-cli `install` annotation on a scratch copy. `just install <TAB>` then
offered `bash zsh` under `── shells · install — shells to install completion for ──`, and
`just -n install fish` was rejected by the pattern. The adapter should not guess groups
from name prefixes such as `bench-*`; those guesses would be wrong in other people's
projects.

## 7. Plan and retirement

| Phase | Size | Contents |
|---|---|---|
| **P1: ship** | S/M | Port the prototype into chezmoi with the three changes from §5 and the four test kinds. Run `chezmoi apply` on athena, apollo, and mac. |
| **P2: polish** | S | The deferred P2 items from §5. |
| **P3: hygiene** | S per repo | §6 conventions in sase, bob-cli, bob-mac-capture, chezmoi, … |
| **Ongoing** | XS | Comment on casey/just#2406 and #3729 with these measurements and the binder approach. Follow clap#6334. |

**Retire the adapter** once a just release does all four of the following. When
`just --completions zsh` stops being the four-line loader, that is the signal to check.

1. It hides options and files on an empty word before a recipe.
2. It renders `[group]`s as zsh groups.
3. It completes parameter slots after a recipe that has free slots.
4. It handles `just mod <TAB>`.

## 8. Open questions for Bryan

These come from cld's report; the defaults are what P1 should ship.

1. **Free-text parameter slots:** show the hint plus files (default, since parameters are
   often paths), or the hint alone?
2. **Signatures in descriptions:** keep them (default), or show docs only, as upstream is
   considering?
3. **fzf-tab:** worth trying later for 97-recipe menus? It is a shell-wide UX change and
   independent of this work.
4. **Bash:** skip it until bash is actually used on a host.

## Evidence

**Lead checks (2026-10-04, athena):**

- **Real-shell tests.** Fixture justfile with `[group]`s, a `tools` module, `[arg]`
  options, a `pattern` parameter, an alias, private recipes, a backtick sentinel, and a
  `my dir/alternate.just`. Each adapter was tested through tmux in Bryan's `zsh -i`, with
  `fpath` set per adapter:
  - **cld prototype:** passed all rows marked ✓ above.
  - **Stock loader:** a noisy flat list; offered recipes again after `deploy`; nothing
    for the quoted `-f` path.
  - **gem script:** `bad pattern: #*` on every Tab.
- **Engine probe.** `-f` is ignored on an empty `--show` or `--set` value and honored
  with a prefix. Traced to `Completer::config()`, which falls back to `Config::new()`.
- **Safety.** `just --dump --dump-format json` did not fire the backtick sentinel.
- **Benchmarks.** `hyperfine` (§4), plus Python startup (82.2 ms via pyenv, 17.6 ms for
  `/usr/bin/python3`).
- **Upstream state.** `gh:casey/just` fetched at `602ee328` (1.58.0 plus 21 commits);
  issue and PR status checked on the web for #3729, #2406, clap#6334, and
  laurigates/dotfiles#252.
- **Chezmoi checkout.** At `53960fc0`: `dot_zfunc/_sase`, the `fpath` and
  `ZSH_AUTOSUGGEST_STRATEGY` lines, and the `tests/` layout.

**Inherited, not re-run by the lead:** cld's cross-host checks on apollo and mac, its
bob-cli and sase candidate counts, and its annotation test; cdx's alias, nested
directory, and 1,000-recipe timings; and the Carapace source findings from cdx and cld.

**Sources:**

- [just shell completion docs](https://just.systems/man/en/shell-completion-scripts.html)
- [casey/just#2406](https://github.com/casey/just/issues/2406)
- [#3729](https://github.com/casey/just/issues/3729)
- [#3167 (dynamic engine)](https://github.com/casey/just/pull/3167)
- [clap-rs/clap#6334](https://github.com/clap-rs/clap/pull/6334)
- [laurigates/dotfiles#252](https://github.com/laurigates/dotfiles/issues/252)
- [fzf-tab](https://github.com/Aloxaf/fzf-tab)
- bob-cli `docs/completion.md`
- prior research `research:202610/bob_shell_completion_and_just_install/`

## Recommended solution

**Build `~/.zfunc/_just` as a static, chezmoi-managed zsh adapter in the same style as
`_bob`.**

- **Where the data comes from.**
  - Recipes, groups, docs, parameters, and modules come from
    `just --dump --dump-format json`, run through a small jq binder that copies just's
    argument-binding rules.
  - Only just's own option names and fixed option choices come from just's built-in
    completer.
  - Files are offered only in path slots.
- **What it delivers.**
  - `just <TAB>` in any project shows only grouped, described recipes and modules.
  - Typing `-` shows just's options.
  - After a recipe, you get that recipe's parameter: choices, a hint, or files.
  - `just mod <TAB>` and quoted `-f` paths work.
  - It costs about 11 ms per Tab on the largest justfile Bryan owns.
- **How to build it.**
  - Start from cld's tested prototype and apply the three changes from §5: unquote words
    before calling just's engine, serve recipe/variable/group option values from the
    JSON, and fall back to the stock engine when jq is missing.
  - Ship it with jq golden tests, a tmux smoke test, a drift test, and a sentinel
    safety test, then roll it out to all three hosts with `chezmoi apply`.
- **Alongside it.**
  - Add `[doc]`, `[group]`, and `[arg(pattern, help)]` to the justfiles you care about,
    starting with bob-cli's `install`.
  - Keep `just --choose` for interactive picking.
  - Skip carapace, Python, a Rust helper, a fork of just, and putting this in bob-cli.
  - Delete the adapter once an upstream just release meets the four retirement criteria
    in §7.
