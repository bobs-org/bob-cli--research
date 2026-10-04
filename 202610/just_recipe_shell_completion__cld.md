# Excellent Shell Completion For `just` Recipes, On Any Project

> **Research question:** Bryan wants `just` recipe completion that is as good as the
> completion `bob` now has, and that works in every project, not only bob-cli. What is
> the best way to build it? The report ends with a recommendation.
>
> **Researcher:** cld · 2026-10-04 · measured on athena (zsh 5.9, just 1.58.0, jq 1.7),
> and checked on apollo (just 1.50.0) and mac (just 1.56.0).

## Bottom line

**Recommendation: write a small zsh adapter, `~/.zfunc/_just`, and manage it with
chezmoi.** It reads just's own data and never invents a grammar:

- **Recipes, groups, docs, parameters, and modules** come from
  `just --dump --dump-format json`. That is just's documented, stabilized metadata
  interface. Reading it never runs justfile code.
- **just's own options and their values** (`-f`, `--set`, `--show`, `--group`, …) are
  handed to just's built-in completer (`JUST_COMPLETE=zsh`). They therefore track
  whichever `just` is installed.
- **A ~40-line binder** copies just's `InvocationParser`, so Tab knows whether the next
  word is a recipe, a parameter, or a recipe option.
- **The menus look like bob's.** The adapter uses the same grouped `_describe -V`
  rendering and the same scoped `── group ──` header defaults as `~/.zfunc/_bob`.

I built a working prototype and ran it in Bryan's real interactive zsh. It is in
[Appendix A](#appendix-a--prototype-_just-tested). It costs **~10 ms per Tab** on
sase's 97-recipe justfile, works unchanged with just 1.50, 1.56, and 1.58, and needs only
`jq`, which all three hosts already have.

Two cheap additions make it excellent rather than merely good:

1. **Justfile hygiene in Bryan's own repos.** Add `[doc('…')]` where a recipe's comment
   spans several lines (40 recipes in sase, 4 in bob-cli). Add `[group('…')]` to large
   justfiles. Add `[arg('x', pattern='a|b')]` where a parameter takes one of a few
   values. Completion turns these into descriptions, headers, and value choices for free.
2. **Upstream feedback, not upstream code.** `just` has not accepted pull requests since
   2026-04-11. Post the measurements on casey/just#2406 and #3729, watch clap#6334, and
   retire the adapter once upstream meets the [exit criteria](#retirement-criteria).

## 1. Where things stand today

| Host | just | Installed via | jq | `_just` on fpath? | `_bob` |
|---|---|---|---|---|---|
| athena | 1.58.0 | cargo | 1.7 | **no** | yes |
| apollo | 1.50.0 | cargo | 1.7 | **no** | yes |
| mac | 1.56.0 | cargo | 1.7.1-apple | **no** | no |

- **No host completes `just` at all today.** All three use cargo installs, which ship no
  completion files. zsh falls back to filenames, and oh-my-zsh (2026-09-22) has no
  `just` plugin.
- **`~/.zfunc` is the managed completion directory.** It is first on `fpath` (twice in
  `~/.zshrc`, before and after oh-my-zsh). chezmoi already ships `dot_zfunc/_sase`
  there, and `bob completion install` writes `_bob` there.
- **Completion runs while Bryan types.** `ZSH_AUTOSUGGEST_STRATEGY=(history completion)`
  makes zsh-autosuggestions call the completer as text is entered, not only on Tab, so
  the latency budget is real.
- **Bryan has many justfiles across projects:** sase, sase-core, sase-telegram,
  sase-github, bob-cli, bob-mac-capture, chezmoi, symvision, actstat, and others.
  - **sase:** 97 public recipes; 50 take parameters, 46 of them `*args`; 35 public
    variables.
  - **bob-cli:** 12 recipes, of which 7 have no doc comment.
  - **Attributes:** none of these use `[group]`, modules, aliases, or `[arg]`. The only
    attribute in use is `[positional-arguments]`.

### The bar: what `bob <TAB>` does

```text
❯ bob <TAB>
── daily workflow ──
capture    -- Capture tasks, bullets, and Pomodoro commands into the vault
freshness  -- Walk the tiered freshness review queue
plan       -- Show today's plan budget, Today's tasks, and NEXT/PENDING lanes
…
── setup ──
completion  -- Install and inspect shell completion for bob
plugins     -- List and deploy Bob's custom Obsidian plugins
── capture protocol ──
capture-complete       -- Complete the capture marker at the cursor
…
```

That menu sets six rules:

- grouped headers in a curated order
- every row described
- no options until you type `-`
- no filenames where a command is expected
- values that depend on context
- fast, and it never writes anything

The `just` adapter should meet the same bar.

## 2. Upstream `just --completions zsh` today

Since just 1.48 (2026-03-21, #3167), `just --completions zsh` prints a 4-line shim. The
shim sources `JUST_COMPLETE=zsh just`, which is clap_complete's *dynamic* engine. just
pins `clap_complete = "=4.6.8"` with `unstable-dynamic`, and attaches custom completers
for recipes, variables, groups, and modules (`src/completer.rs`).

### What it gets right

- **The justfile in use.** It searches upward like just does, and honors `-f`, `-d`,
  `--justfile-name`, and `-g`. It does this by parsing the command line with clap's
  `ignore_errors`.
- **Recipe names with docs, and `mod::recipe` paths.** Colons are escaped correctly for
  `_describe`.
- **Option values.** `--set` gets variable names, `--show` and `--usage` get recipes,
  `--group` gets groups, and `-l` gets modules.
- **Speed.** About 5 ms in bob-cli and 8 ms in sase, including a bash wrapper.
- **Safety.** It never evaluates anything. I confirmed this with a justfile whose
  backticks, `shell()` call, and parameter default each `touch` a sentinel file. None
  fired. A control run of `just --evaluate` did fire.

### What it gets wrong (measured)

**Bare `just <TAB>` is mostly noise.**

| Project | Candidates | Options | `VAR=` overrides | Paths | Recipes |
|---|---|---|---|---|---|
| bob-cli | 98 | 68 | 1 | 17 | 12 |
| sase | 232 | 68 | 35 | ~32 | ~97 |

**Undocumented recipes get buried.** This is real-shell output in bob-cli, captured
with tmux in Bryan's interactive zsh:

```text
❯ just <TAB>
check-adapter            -- Not part of `all`: the first run fetches the pinned Python deps.
check-web-clip-adapter   -- (otherwise they print "skipped: no browser" and still pass).
install                  -- completion. Pass shells to choose explicitly: `just install zsh bash`.
install-all              -- bob-mac-capture checkouts (missing siblings are skipped).
install-all-and-restart  -- install-all, then restart Obsidian (if it is running) so it loads the new plugins.
--alias-style            -- Set list command alias display style
--allow-missing          -- Ignore missing recipe and module errors
   … 66 more option rows …
docs           scripts        target         vault          check-scripts  install-smoke  package-list   rule=          AGENTS.md      Cargo.lock …
sase           src            tests          all            fmt            lint           test           .              CLAUDE.md      Cargo.toml …
```

`all`, `fmt`, `lint`, `test`, and three more recipes have no doc comment. They land in
the last two rows, mixed with directories and files, below 68 option rows. These are
bob-cli's most-used recipes.

Root causes:

1. **Options at an empty word.** clap_complete's engine adds every long option whenever
   the state is `ValueDone` and the word is empty (`engine/complete.rs`,
   `complete_option`). It also adds them after the first positional, because just's
   `ARGUMENTS` has `num_args = 1..`. Casey lists "Don't complete options after
   positional arguments (this is a clap bug)" in #2406. clap#6219 tracks the same
   problem in PowerShell.
2. **Files everywhere.** `Completer::complete_argument` always appends
   `PathCompleter::any()`, and has done since 1.50 (#3299).
3. **One flat group.** clap's zsh writer emits only `value:help`, and its shim renders a
   single `_describe -V 'values'`. Even if just set `CompletionCandidate::tag`, zsh would
   never show it. clap#6334, "group options by tag (in zsh)", is an open PR, last
   pushed 2026-08-31.
4. **No idea where the cursor is.** The completer does not know which positional it is
   completing. just binds arguments greedily: `just build test` runs `build` with
   `target=test`. Yet after `just build ` upstream offers recipes again. After
   `just test --` it offers *just's* global options, not the recipe's own
   `[arg(long)]` options. Casey's own note in #2406: "This may be tough. We don't know
   where exactly in the positional arguments we're completing."
5. **Space-separated module paths are not handled.** `just tools lint` is valid, but
   `just tools <TAB>` offers root recipes. This is casey/just#3729, opened 2026-09-30
   with no reply yet.
6. **Descriptions are the last comment line only.** This is just's own rule
   (`Parser::take_doc_comment`). In sase, 40 of 94 recipes have multi-line comments, so
   completion and `just --list` show fragments such as `bench-core # rows have been
   removed.` and `install # distribution instead.`.

### Upstream outlook

- **No PRs.** The README says "`just` is not currently accepting pull requests". That
  note landed 2026-04-11 (#3289).
- **Casey is actively working on completion.** Commits #3716 and #3717 (2026-09-25) are
  not yet released. His #2406 checklist names our exact gaps as unchecked:
  - intelligent position-aware completion
  - a recipe hint after Tab
  - no options after positionals
  - space-separated paths
  - `VAR=` without a trailing space
  - a way to print errors

  It also says "Reconsider including recipe doc comments in completions, it makes them
  take up much more space". Upstream may therefore move *away* from descriptions.
- **Grouping in zsh needs two upstream changes:** clap#6334 merged and released, and
  just adopting candidate tags. Someone else is waiting on the same thing:
  laurigates/dotfiles#252 keeps a hand-written `dot_zfunc/_just` built on
  `just --dump --dump-format json` until it lands.

**Conclusion:** upstream will improve, but on casey's schedule, and Bryan cannot
contribute code. Bryan should build something now, shaped so it can be thrown away
later.

## 3. Options considered

| Option | What it is | Verdict |
|---|---|---|
| **A. Upstream as-is** | `just --completions zsh > ~/.zfunc/_just` | Better than nothing, but fails the bar: 98 to 232-row menus, buried recipes, no parameter awareness. It is still the right engine for just's *own options*, so the recommendation delegates to it. |
| **B. Upstream plus zstyle tuning** | `ignored-patterns`, `group-order`, … | **Rejected.** Every candidate shares the one `values` tag, so zstyle has nothing to sort or group by. Hiding options with `ignored-patterns` also hides them after `-`. |
| **C. Custom zsh adapter plus jq** (chezmoi-managed) | JSON dump for recipes; just's engine for options; a jq binder | **Recommended.** One file, no new binary, deployed by `chezmoi apply`. Prototype proven in a real shell (§5). |
| **D. Tiny Rust helper** (`just-complete`) speaking bob's protocol 1 | serde, unit tests, reuses the `_bob` adapter verbatim | A credible runner-up. It is more testable, but adds a crate, a repo, and a `cargo install` on three hosts, plus version skew between helper and adapter, for ~150 lines of logic. Revisit if the jq program grows past ~300 lines. |
| **E. Python helper** in chezmoi `bin/` | Same logic in Python | **Rejected.** ~25–40 ms of interpreter start on every keystroke under autosuggest. jq plus zsh does it in ~10 ms. |
| **F. Fork just** with a better `Completer` | Reuse the real `InvocationParser`; add a zsh shell that emits tags | **Rejected.** It replaces the machine-wide `just` on every host and needs a permanent rebase (21 commits since 1.58.0 already), because the fork can never merge. |
| **G. carapace** (`carapace-bin` `just_completer`) | A Go completion framework with a just completer | **Rejected.** Not installed anywhere, and it takes over shell completion broadly. Its just completer lists flags by hand (drift), handles parameters only for *root* recipes (`jf.Recipes[c.Args[0]]`, so `tools::release` gives "unknown recipe"), treats `+` variadics as singular, and does not group. The previous bob research rejected carapace for the same "second grammar on every host" reason. |
| **H. fzf-tab / `just --choose`** | A fuzzy UI over whatever the completer returns | **Complementary, not a fix.** fzf-tab makes the 97-recipe sase menu easier to filter and renders `_describe` groups well, but changes *all* completion UX. Bryan's call, later. `just --choose` already exists for interactive picking. |
| **I. Put it in `bob`** (`bob completion install just`) | Reuse bob's `__complete`, manifest, and verification | **Rejected.** Scope creep: a vault CLI would own a general dev tool's completion, couple it to bob's release cycle, and require bob on every host. Copy bob's *rendering*, not its home. |

## 4. Recommended design

### Shape

```text
 zsh ──TAB──▶ ~/.zfunc/_just   (chezmoi: home/dot_zfunc/_just.tmpl, ~200 lines)
               │
               ├─ walk just's global options (only those that pick the justfile are kept)
               │    -f/--justfile  -d/--working-directory  -g  --justfile-name  --ceiling
               │
               ├─ cursor on `-…` before any recipe, on a global option's value,
               │  or after a subcommand flag (--show, --usage, -l, --set, …)
               │      └──▶ JUST_COMPLETE=zsh just -- $words   (just's own engine)
               │           rendered as `── just options ──`; path options use _files
               │
               └─ otherwise
                    just $search --dump --dump-format json     (stable, read-only, ~3–7 ms)
                      └──▶ jq binder + presenter                (~3 ms)
                             └──▶ value⇥description⇥group⇥suffix | !message | !files
                                    └──▶ bob-style grouped _describe -V rendering
```

**Principles:**

- **just is the grammar.** The adapter reads just's JSON and calls just's engine. The
  only logic it copies is argument binding, and it copies that rule for rule from
  `src/invocation_parser.rs`.
- **Read-only and side-effect free.** Use only `--dump` and `JUST_COMPLETE`. Verified:
  neither runs backticks, `shell()`, or defaults. Never call `--evaluate`, which does run
  backticks (verified), and do not add other subcommands without repeating the sentinel
  test.
- **Silent on failure, honest on error.** An empty result falls through. A justfile
  error becomes a one-line `_message` (for example `just: no justfile found`, or
  ``just: error: variable `nope` not defined``). Upstream shows nothing, and casey's
  #2406 still has "Figure out a way to print errors" unchecked.
- **The user's style wins.** Scoped default styles, identical to `_bob`, apply only where
  Bryan has set none.

### Behavior rules

| Cursor context | Candidates | Example (prototype output) |
|---|---|---|
| Empty word, before any recipe | Recipes: ungrouped first (`── recipes ──`), then one header per `[group]`, then `── modules ──` (`tools::`, no trailing space). **No options, files, or overrides.** | see §5 |
| Non-empty word, before any recipe | As above, plus `── variable overrides ──` (`profile=`, no trailing space) last | `just p<TAB>` |
| `-…` before any recipe | just's own options via its engine, under `── just options ──` | `just --j<TAB>` gives `--jobs --justfile --justfile-name --json` |
| Value of a global option | just's engine (`--set` names, `--show` recipes, …); `_files` for `-f`; `_files -/` for `-d`, `--ceiling`, `--tempdir` | `just --set <TAB>` gives `TOKEN profile` |
| After a recipe, in a positional slot | **The parameter, not recipes.** Literal `pattern` alternatives become choices. Otherwise a `!message` hint (name · recipe — help (default …)) plus files. | `just deploy <TAB>` gives `── env · deploy — target environment ──  staging prod` |
| After a recipe, `-…`, options not ended | That recipe's `[arg(long/short)]` options with help, `── options · test ──` | `just test --<TAB>` gives `--filter --verbose` |
| Value of a recipe option | That parameter's hint or choices | `just test -f <TAB>` gives `filter · test — only matching tests (default "")` |
| Recipe's slots all filled | The next recipe (just runs several recipes in one invocation) | `just deploy prod <TAB>` gives recipes |
| `mod::` path in one word | That module's recipes, fully qualified | `just tools::<TAB>` gives `tools::lint tools::release` |
| `mod` path with spaces | That module's recipes, bare | `just tools <TAB>` gives `lint release` (fixes #3729) |
| Unknown recipe word | `!message just: no recipe named …` | `just nope <TAB>` |

**Binding rules copied from `InvocationParser`.** Each was verified against real `just`
runs.

- **Module paths.** A word containing `:` is a `mod::path`. Otherwise the parser
  descends through module names word by word.
- **Options.** A recipe's `[arg]` options may appear anywhere among its arguments until
  `--`. `--x=v`, `--x v`, `-x v`, and combined shorts (`-abc`) all work. An option with
  `value=` takes no argument.
- **Positionals.** Positionals fill greedily, and a variadic `*`/`+` keeps consuming.
  The first word the recipe cannot take starts the next recipe. Examples:
  - `just build test` sets `target=test`.
  - `just test -f x build` runs `test`, then `build`.
  - `just test build --verbose` gives `build`'s `target` the value `--verbose`, because
    `build` has no options.
- **No options means no option parsing.** For a recipe with no `[arg]` options, `--` is
  an ordinary positional value.
- **Overrides.** `NAME=VALUE` overrides count only before the first recipe.

**Descriptions.** A recipe's description is its signature, then its doc:
`[target=all] [flags…] · Build everything`. Parameters with a default show it.
Expression defaults show `…`. A planner may decide to drop the signature on narrow
terminals (see [open questions](#open-questions-for-bryan)).

### Robustness and version tolerance

- **Old-just support.** It works with just 1.50 (apollo), 1.56 (mac), and 1.58
  (athena). The JSON dump was stabilized in #1633, and since then changes have been
  additive. One schema change matters: `pattern` was a string in 1.50 and became an
  array once const-expression patterns arrived (1.55). The jq accepts both.
- **jq quirk.** Pass words with `--args --`. Without the `--`, jq parses a recipe option
  such as `-f` or `--filter` as *its own* flag. This works on jq 1.7 and 1.7.1-apple.
- **zsh gotchas found during the spike** (all fixed in Appendix A):
  - `${${(f)var}[1]}` on a one-line string returns its first *character*. Split into an
    array first.
  - `_describe` needs `:` escaped in values (`mod::recipe`).
  - Style defaults must be set before any early return.
  - The first autoload must complete immediately, using the same
    `zsh_eval_context[-1] == loadautofunc` idiom as `_bob`.
- **Latency on sase (97 recipes, 1,300+ lines):**

  | Path | Time |
  |---|---|
  | `just --dump --dump-format json` alone | 6.7 ms |
  | `--dump` plus the jq binder (prototype) | 9.3–11.1 ms |
  | Upstream engine | 7.8 ms |
  | `bob __complete`, for reference | 3.3 ms |

  All are well inside a per-keystroke budget, so no cache is needed.

### Where it lives and how it ships

- **Location in chezmoi:** `home/dot_zfunc/_just.tmpl`. The jq program lives as its
  own file under `home/.chezmoitemplates/just_complete.jq` and is inlined with
  `{{ include … }}`. That way tests can run it directly with `jq -f`, and the shipped
  `_just` stays a single file.
  - Use `include`, not `template`, so jq text is never template-expanded.
  - chezmoi ignores dot-prefixed source paths, so the `.jq` file is never deployed on
    its own.
- **Rollout:** `chezmoi apply` on athena, apollo, and mac.
  - zsh picks up the new file on the next shell; compinit's dump notices the new
    `fpath` file.
  - Do not `zcompile` it.
  - Nothing to install, and no rc edits.
- **Tests (in chezmoi's `tests/`):**
  1. **jq golden tests** over fixture justfiles. Cover every row of the behavior table,
     plus modules, `[group]`, `[arg]` long/short/`value=`, pattern string/array,
     expression defaults, aliases, private recipes, and broken or missing justfiles.
  2. **Real-shell smoke test** with tmux, as used in this spike: type `just <TAB>` in a
     fixture and assert headers and rows. Skip when tmux or zsh is missing.
  3. **Drift test:** the adapter's hard-coded list of value-taking global options must
     equal the options with a `<METAVAR>` in `just --help`. This catches new just
     options that would shift the binder.
  4. **Safety test:** the sentinel-file justfile from §2 must stay untouched after a
     run of completions.

### Retirement criteria

Delete the custom binder and presenter, and keep only `just --completions zsh`, once an
upstream `just` release does all four of these:

1. hides options and files on an empty word before a recipe
2. renders `[group]`s as zsh groups (needs clap#6334 plus a just change)
3. completes parameter slots, not recipes, after a recipe that has free slots
4. handles `just mod <TAB>`

Re-check after each just release. `just --completions zsh` output changing from the
4-line shim is the signal to look.

## 5. Prototype results (real zsh, tmux-captured)

The fixture has `[group('dev')]` and `[group('ops')]` recipes, a `tools` module,
`[arg]` options, a pattern parameter, an alias, and private recipes:

```text
❯ just <TAB>
── recipes ──
fmt  -- files… · Format files
── dev ──
build  -- [target=all] [flags…] · Second line of the comment.
greet  -- [name=…] · Expression default
test   -- [--filter filter] [--verbose] · Run the test suite
── ops ──
deploy  -- env
── modules ──
tools::  -- module

❯ just deploy <TAB>
── env · deploy — target environment ──
staging  prod

❯ just build <TAB>
target · build (default all)
── file ──
./  ../  a.txt  b.md  justfile  sub/  tools.just

❯ just test --<TAB>
── options · test ──
--filter   -- only matching tests ‹filter›
--verbose  -- verbose

❯ just <TAB>        (in a directory with no justfile)
just: no justfile found
```

In bob-cli, all 12 recipes now show, with the 7 undocumented ones alongside the rest
and no options, files, or `rule=`. In sase, all 97 recipes show with no option, file, or
variable noise. The remaining wart is the fragment descriptions, which §6 fixes.

With bob-cli's `install` recipe annotated (tested on a scratch copy; the repo is
untouched):

```just
# Install bob and its shims from this checkout, then install or refresh shell
# completion. Pass shells to choose explicitly: `just install zsh bash`.
[doc('Install bob from this checkout and refresh its shell completion')]
[positional-arguments]
[arg('shells', pattern='bash|zsh', help='shells to install completion for')]
install *shells:
```

```text
❯ just --list | grep install
    install *shells         # Install bob from this checkout and refresh its shell completion
❯ just -n install fish
error: argument `fish` passed to recipe `install` parameter `shells` does not match pattern `bash|zsh`
❯ just install <TAB>
── shells · install — shells to install completion for ──
bash  zsh
```

One annotation gives validation, a clean `--list` line, and completion choices at once.

## 6. Justfile conventions that make completion excellent

These help with *any* completer, upstream's included, and they fix `just --list` too.

| Convention | Why | Where it pays off now |
|---|---|---|
| `[doc('One-line summary')]` above any recipe whose comment spans several lines; keep the long comment above it | just treats only the last comment line as the doc. `[doc]` overrides it, and #3275 preserves the comments above it. | sase: 40 of 94 recipes; bob-cli: 4 of 12 (`check-adapter`, `check-web-clip-adapter`, `install`, `install-all`) |
| A one-line comment on every public recipe | Undocumented recipes carry no information in the menu | bob-cli: 7 of 12 have none (`all`, `fmt`, `lint`, `test`, …) |
| `[group('…')]` in large justfiles | Becomes `── group ──` headers | sase's 97 recipes: e.g. `bench`, `fmt`, `test`, `docs`, `install` |
| `[arg('p', pattern='a\|b', help='…')]` for enumerable parameters | Validation plus completion choices plus hint text | bob-cli `install *shells`; bob-mac-capture `install target`/`identity` |
| Prefer `mod` over name prefixes for large sub-areas | Becomes `tools::` drill-down | none today; future-proofing |

I would **not** guess groups from name prefixes such as `bench-*` and `fmt-*` in the
adapter. Typing the prefix already filters, and guessed headers would be wrong in other
people's projects.

## 7. Phased plan

| Phase | Size | Contents |
|---|---|---|
| **P1: ship the adapter** | S/M | Port Appendix A into chezmoi (`_just.tmpl` plus `.chezmoitemplates/just_complete.jq`). Add the four test kinds. `chezmoi apply` on all hosts. |
| **P2: polish** | S | Show `--filter`/`-f` on one row. Drop variadic choices already given. Mark the default recipe (`first`) as `(default)`. Honor `JUST_COMPLETE_ALIASES` with an `aliases` group. Handle `$SUFFIX` when the cursor is mid-word. Hide recipes disabled on this OS (`[linux]`/`[macos]`/…). Mark `[confirm]` recipes. Optionally add parent-justfile recipes when `set fallback` is on. |
| **P3: justfile hygiene** | S per repo | §6 conventions in sase, bob-cli, bob-mac-capture, chezmoi, and others, each as an ordinary change in its own repo. |
| **Ongoing: upstream** | XS | Comment on casey/just#2406 and #3729 with §2's measurements and the binder approach (the `Completer` could run `InvocationParser` over the words before the cursor). Follow clap#6334. Apply the [retirement criteria](#retirement-criteria) on each just release. |

## 8. Risks and open questions

**Risks**

- **The binder is a second copy of one rule.** If just changes how arguments bind, the
  binder drifts. That has been stable, and the cost is low: a wrong hint, never a wrong
  command. The golden tests pin today's behavior.
- **The global-option list can drift.** A new value-taking just option, when used, would
  shift the binder by one word. The drift test catches it.
- **A JSON field could be renamed.** The dump is stabilized and changes have been
  additive. The jq already tolerates the one shape change seen (`pattern`).
- **jq missing on a future host.** The adapter should detect this and fall back to
  upstream's engine (`_just_clap 'recipes'`) rather than go silent.

### Open questions for Bryan

1. **Free-form parameter slots.** Show the hint *plus* files (recommended, since args
   are often paths), or the hint only?
2. **Module entries.** Offer `tools::` (one word, recommended) or `tools` followed by a
   space?
3. **Signatures in descriptions.** Keep them (recommended, because they tell you what the
   recipe will consume), or show docs only, as casey is considering upstream?
4. **fzf-tab.** Worth trying for big menus like sase's? It is a global UX change and
   independent of this work.

---

## Appendix A — prototype `_just` (tested)

This is the exact file used for every capture in §5. It was assembled from
`_just.head`, `just_complete.jq`, and `_just.tail`. Load it for a trial in any zsh:
`fpath=(/path/to/dir $fpath); autoload -Uz _just; compdef _just just`.

```zsh
#compdef just
# Prototype: grouped, parameter-aware completion for just recipes (research spike).
# Recipes, groups, docs, and parameters come from `just --dump --dump-format json`, just's
# stable metadata interface. just's own options and their values come from just's built-in
# completer (JUST_COMPLETE), so they track the installed just.

_just_clap() {
  local -a out
  case ${(Q)words[CURRENT-1]} in
    (-f|--justfile|-E|--dotenv-path|--chooser|--cygpath) _files; return ;;
    (-d|--working-directory|--ceiling|--tempdir) _files -/; return ;;
  esac
  out=("${(@f)$(_CLAP_IFS=$'\n' _CLAP_COMPLETE_INDEX=$((CURRENT - 1)) JUST_COMPLETE=zsh \
    command just -- "${words[@]}" 2>/dev/null)}")
  out=(${out:#})
  (( $#out )) || return 1
  _describe -V -t just-options "${1:-values}" out
}

_just() {
  local -a search rest lines fields groups
  local -A arrays
  local i=2 w json prog line value help group suffix array header ret=1

  # Presentation defaults, applied only where you have set no style (same look as `bob`).
  if ! zstyle -m ":completion:${curcontext}:descriptions" format '*'; then
    header='%B%F{green}── %d ──%f%b'
    (( ${+NO_COLOR} )) && header='── %d ──'
    zstyle ':completion:*:*:just:*:descriptions' format "$header"
  fi
  zstyle -m ":completion:${curcontext}:" group-name '*' ||
    zstyle ':completion:*:*:just:*' group-name ''

  # Walk just's own options up to the first recipe or override; keep the ones that choose
  # which justfile to read so the recipe list matches what `just` would run.
  while (( i < CURRENT )); do
    w=${(Q)words[i]}
    case $w in
      (-f|--justfile|-d|--working-directory|--justfile-name|--ceiling)
        search+=("$w" "${(Q)words[i+1]}"); (( i += 2 )) ;;
      (--justfile=*|--working-directory=*|--justfile-name=*|--ceiling=*|-g|--global-justfile)
        search+=("$w"); (( i++ )) ;;
      (--set) (( i += 3 )) ;;
      (--alias-style|--chooser|--color|--command-color|--cygpath|--dotenv-command|-F|--dotenv-filename|-E|--dotenv-path|--dump-format|--evaluate-format|--group|--indentation|--jobs|--list-heading|--list-prefix|--shell|--shell-arg|--tempdir|--timestamp-format)
        (( i += 2 )) ;;
      (-l|--list|-s|--show|--usage|--clean|-c|--command|--completions|--evaluate|--variables|--summary|--dump|--json|--groups|--fmt|--init|-e|--edit|--man|--changelog|--choose)
        _just_clap; return ;;  # a just subcommand owns the rest of the line
      (--) (( i++ )); break ;;
      (-*) (( i++ )) ;;
      (*) break ;;
    esac
  done
  (( i > CURRENT )) && { _just_clap; return; }           # value of one of just's options
  if (( i == CURRENT )) && [[ $PREFIX == -* ]]; then
    _just_clap 'just options'; return
  fi
  rest=("${(@Q)words[i,CURRENT-1]}")

  json=$(command just "${search[@]}" --dump --dump-format json 2>&1)
  if (( $? )); then
    fields=("${(@f)json}")
    _message -r "just: ${fields[1]#error: }"
    return 1
  fi
  read -r -d '' prog <<'JQ'
# Input: `just --dump --dump-format json`.  Args: $cur (word at cursor), $ARGS.positional
# (the words between just's global options and the cursor).  Output: protocol lines
# value<TAB>description<TAB>group<TAB>suffix, or directives (!message, !files).

def visible: to_entries | map(select(.value.private | not)) | map(.value);
def group_of: [.attributes[] | objects | .group // empty][0] // "recipes";
def default_text:
  if type == "string" then (if . == "" then "\"\"" else . end) else "…" end;
def is_opt: .long != null or .short != null;
def opt_name: if .long != null then "--" + .long else "-" + .short end;
def sig:
  [.parameters[]
   | if is_opt then "[" + opt_name + (if .value != null then "" else " " + .name end) + "]"
     elif .kind == "star" then "[" + .name + "…]"
     elif .kind == "plus" then .name + "…"
     elif .default != null then "[" + .name + "=" + (.default | default_text) + "]"
     else .name end]
  | join(" ");
def describe: ([sig, (.doc // "")] | map(select(. != "")) | join(" · "));
def line($v; $d; $g; $s): [$v, $d, $g, $s] | join("\t");

def module_at($path): reduce $path[] as $m (.; if . == null then null else .modules[$m] end);

# Resolve the recipe named at $w[$i]: "a::b" in one word, or "a b" as module words.
def resolve($w; $i):
  if ($w[$i] | contains("::")) then
    ($w[$i] | split("::")) as $p
    | (module_at($p[:-1]) | if . == null then null else .recipes[$p[-1]] end) as $r
    | if $r != null and ($r.private | not) then {recipe: $r, next: ($i + 1)} else {unknown: $w[$i]} end
  else
    def go($k; $path):
      if $k >= ($w | length) then {in_module: $path}
      elif .modules[$w[$k]] != null then (.modules[$w[$k]] | go($k + 1; $path + [$w[$k]]))
      elif .recipes[$w[$k]] != null and (.recipes[$w[$k]].private | not) then {recipe: .recipes[$w[$k]], next: ($k + 1)}
      elif .aliases[$w[$k]] != null then {recipe: .recipes[.aliases[$w[$k]].target], next: ($k + 1)}
      else {unknown: $w[$k]} end;
    go($i; [])
  end;

# Mirror just's InvocationParser: options interleave until `--`; positionals fill greedily,
# and a variadic parameter keeps consuming.  Stops at the first word the recipe cannot take.
def bind($r; $w; $i):
  ($r.parameters | map(select(is_opt | not))) as $pos
  | ($r.parameters | map(select(is_opt))) as $opts
  | {k: $i, pi: 0, n: 0, eoo: ($opts | length == 0), pending: null, stop: false}
  | until(.stop or .k >= ($w | length);
      $w[.k] as $a
      | if .pending != null then .pending = null | .k += 1
        elif (.eoo | not) and $a == "--" then .eoo = true | .k += 1
        elif (.eoo | not) and ($a | startswith("-")) and $a != "-" then
          ($a | ltrimstr("-") | ltrimstr("-") | split("=")) as $nv
          | (if ($a | startswith("--")) then [$opts[] | select(.long == $nv[0])]
             else [$opts[] | select(.short == ($nv[0] | .[-1:]))] end) as $hit
          | (if ($hit | length) > 0 and $hit[0].value == null and ($nv | length) == 1
             then .pending = $hit[0] else . end)
          | .k += 1
        elif .pi < ($pos | length) then
          (if ($pos[.pi].kind | IN("star", "plus")) then . else .pi += 1 end) | .n += 1 | .k += 1
        else .stop = true end)
  | . + {pos: $pos, opts: $opts};

def walk($w; $i):
  if $i >= ($w | length) then {mode: "recipe", module: [], first: ($i == 0)}
  else
    . as $jf | resolve($w; $i) as $res
    | if $res.unknown then {mode: "unknown", word: $res.unknown}
      elif $res.in_module then {mode: "recipe", module: $res.in_module, spaced: true}
      else bind($res.recipe; $w; $res.next) as $b
        | if $b.k >= ($w | length) then {mode: "arg", recipe: $res.recipe, b: $b}
          else $jf | walk($w; $b.k) end
      end
  end;

def recipe_lines($prefix):
  ([.recipes | visible[] | {g: group_of, l: line($prefix + .name; describe; group_of; "space")}]
   | sort_by(if .g == "recipes" then "" else .g end) | .[].l),
  ((.modules // {}) | to_entries[] | line($prefix + .key + "::"; (.value.doc // "module"); "modules"; "nospace"));

def param_lines($p; $r):
  ($p.name + " · " + $r.name + (if $p.help then " — " + $p.help else "" end)
   + (if $p.default != null then " (default " + ($p.default | default_text) + ")" else "" end)) as $label
  | ($p.pattern | if type == "string" then . elif type == "array" and length == 1 and (.[0] | type) == "string" then .[0] else null end) as $pat
  | if $pat != null and ($pat | test("^[A-Za-z0-9_.,/@+-]+(\\|[A-Za-z0-9_.,/@+-]+)*$"))
    then ($pat | split("|")[] | line(.; ""; $label; "space"))
    else "!message " + $label, "!files" end;

$ARGS.positional as $w0
| ([$w0 | to_entries[] | select(.value | test("^[A-Za-z_][A-Za-z0-9_-]*=") | not)][0].key // ($w0 | length)) as $skip
| $w0[$skip:] as $w
| walk($w; 0) as $st
| if $st.mode == "unknown" then "!message just: no recipe named `" + $st.word + "`"
  elif $st.mode == "recipe" then
    if ($st.module | length) == 0 and ($cur | contains("::")) then
      ($cur | split("::")[:-1]) as $mp
      | module_at($mp) | if . == null then empty else recipe_lines(($mp | join("::")) + "::") end
    else
      module_at($st.module) | recipe_lines(""),
      (if $st.first and ($cur | length) > 0 and ($skip == ($w0 | length)) then
         (.assignments | visible | .[] | line(.name + "="; "override variable"; "variable overrides"; "nospace"))
       else empty end)
    end
  else
    $st.b as $b | $st.recipe as $r
    | if $b.pending != null then param_lines($b.pending; $r)
      elif ($cur | startswith("-")) and ($b.eoo | not) then
        ($b.opts[] | line(opt_name; (.help // .name) + (if .value != null then "" else " ‹" + .name + "›" end); "options · " + $r.name; "space"))
      elif $b.pi < ($b.pos | length) then param_lines($b.pos[$b.pi]; $r)
      else recipe_lines("") end
  end
JQ
  lines=(${(f)"$(print -r -- "$json" | jq -r --arg cur "$PREFIX" "$prog" --args -- "${rest[@]}" 2>/dev/null)"})
  (( $#lines )) || return 1

  for line in $lines; do
    case $line in
      ('!files')     _files && ret=0; continue ;;
      ('!message '*) _message -r "${line#!message }"; continue ;;
      ('!'*)         continue ;;
    esac
    fields=("${(@ps:\t:)line}")
    value=${fields[1]//:/\\:} help=$fields[2] group=${fields[3]:-values} suffix=${fields[4]:-space}
    array=$arrays[$group/$suffix]
    if [[ -z $array ]]; then
      array=_just_group_$#groups
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
  _just "$@"
else
  compdef _just just
fi
```

**Known prototype gaps,** all P2:

- a short option is not shown on the same row as its long form
- variadic choices are not de-duplicated
- `$SUFFIX` (cursor mid-word) is ignored
- no fallback when jq is missing
- the counter `n` is unused

## Appendix B — how the evidence was gathered

- **Upstream candidates.** Collected with
  `_CLAP_IFS=$'\n' _CLAP_COMPLETE_INDEX=<i> JUST_COMPLETE=zsh just -- just <words…>`.
  This is the same call the shipped shim makes.
- **Real-shell captures.** A detached `tmux` session ran Bryan's interactive `zsh -i`,
  added a test `fpath` entry, typed the words, sent Tab, and captured the pane with
  `capture-pane`.
- **Latency.** `hyperfine -N --warmup 3 -r 20..30` on athena.
- **Cross-version checks.** The fixture plus the jq program ran over SSH in a temp
  directory on apollo (just 1.50.0) and mac (just 1.56.0). The temp directory was
  removed afterwards.
- **Source reading.** `casey/just` at `1.58.0-21-g602ee328`: `src/completer.rs`,
  `src/main.rs`, `src/arguments.rs`, `src/parser.rs` (`take_doc_comment`),
  `src/invocation_parser.rs`, `completions/just.zsh`, README, CHANGELOG. Also clap
  `clap_complete/src/engine/complete.rs` and `env/shells.rs`, and `carapace-bin`'s
  `just_completer` plus `pkg/actions/tools/just/recipe.go`. All were opened through
  `sase repo open`.
- **Related prior research.** `research:202610/bob_shell_completion_and_just_install/`,
  the source of bob's adapter design and protocol 1.

## Sources

- [casey/just#2406 — Improve dynamic completions](https://github.com/casey/just/issues/2406) (casey's checklist)
- [casey/just#3729 — zsh completion: prefer recipes over files, and complete module recipes after a space](https://github.com/casey/just/issues/3729)
- [clap-rs/clap#6334 — feat(complete): group options by tag (in zsh)](https://github.com/clap-rs/clap/issues/6334) (open PR)
- [clap-rs/clap#6320 — Zsh completion tagging / grouping](https://github.com/clap-rs/clap/issues/6320)
- [clap-rs/clap#6219 — Flags should only be completed when word starts with `-`](https://github.com/clap-rs/clap/issues/6219)
- [clap-rs/clap#5515 — Don't show flags in native completion that are already present](https://github.com/clap-rs/clap/issues/5515)
- [laurigates/dotfiles#252 — Track upstream grouped just recipe completion](https://github.com/laurigates/dotfiles/issues/252) (an independent `_just` built on the JSON dump)
- just README: "Shell Completion Scripts", "Documentation Comments", "Contributing" (the no-PRs note); CHANGELOG entries #1633, #3167, #3275, #3289, #3299
