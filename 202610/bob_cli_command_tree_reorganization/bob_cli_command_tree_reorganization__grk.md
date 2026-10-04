# Should `bob` nest its subcommands (and should `bob task` exist)?

- **Researcher:** grk
- **Date:** 2026-10-04
- **Question:** Which of `bob`'s current subcommands, if any, deserve to be grouped under a parent (the example being a new `bob task`)? Is regrouping a good idea at all?
- **Verdict:** Do **not** add a `bob task` grab-bag. The real problem is that `bob --help` dumps 28 peers in one alphabetical list, ten of which are capture-protocol plumbing already split out in Tab completion. Fix help (git / `sase -h` style), keep daily verbs at the top level, keep the hyphenated `capture-*` protocol, and spend any rename budget on `task-status-hooks` and `move-done-tasks`. Nesting is already the rule when one noun has several verbs (`plugins`, `gkeep`, `highlights`, …). Extending that rule to “everything about tasks” would hide the commands Bryan types every day behind a noun that names the whole product.

---

## 1. In one breath

`bob` is a personal workflow CLI, closer to `git` than to `kubectl` or `gh`. Daily work is a handful of verbs (`capture`, `plan`, `ready`, `freshness`, `query`, `nightly`). Those should stay one token from `$`. Grouping is already used, and used well, wherever a **noun has several verbs**: `bob plugins list|sync`, `bob gkeep list|pull|doctor|login`, `bob highlights clip|create|scan|…`, `bob freshness list|seed`, `bob projects list|sync`, `bob vault-sync run|status`, `bob completion install|status|…`.

The ten `capture-*` commands look like the obvious nest (`bob capture parse`, …). They must **not** nest under `capture`. `bob capture` takes free-text `TEXT`, so a reserved word like `parse` would steal drafts. Bob Mac Capture hard-codes the hyphenated argv as a versioned JSON protocol. Hyphenation is the correct spelling for siblings of a free-text parent; Tab completion already files them under `capture protocol`.

A new `bob task` parent is the wrong cut. “Task” is the data type almost every command touches, not a user job. `bob task plan` / `bob task ready` / `bob task freshness` adds a token without partitioning intent. The two commands whose *names* are the problem (`task-status-hooks`, `move-done-tasks`) want **renames**, not a folder.

---

## 2. Critique of the plan

The plan as stated: make `bob`'s subcommands easier to understand by grouping some of them, with `bob task` as the working example.

### What is right

- Top-level `bob --help` is hard to scan. Live output on this host lists **28** subcommands plus `help`, alphabetically, so the first screen is almost entirely `capture` and `capture-*`. That is a real discoverability failure. `cli_rules.md` asks for help that is “clear, complete, consistent, and easy to scan”; the current listing is complete and alphabetical, and it is not easy to scan.
- Some commands already *feel* like they belong to a family: the ten `capture-*` endpoints, the three Pomodoro status tools (`pomodoro`, `tmux-pomodoro`, `notify`), and the vault-maintenance trio (`vault-sync`, `nightly`, `move-done-tasks`).
- Nested groups that already exist (`gkeep`, `highlights`, `plugins`, `projects`, `freshness`, `completion`, `vault-sync`) are the right shape: one noun, several verbs, default subcommand where a bare invocation is common (`bob gkeep` → `list`, `bob freshness` → `list`, `bob vault-sync` → `run`).
- Shell completion has already made the porcelain / plumbing cut that help has not: `CompletionTier::Porcelain` renders under `commands`; the ten frontend endpoints render last under `capture protocol` (`src/runner.rs`, `src/native/completion/present.rs`). The product already knows these are not peers. Help has not caught up.

### What is wrong

1. **Grouping by the word “task” does not match how Bryan uses `bob`.** The daily loop in the README is capture → `plan` / `freshness` / `ready` → link and run a Pomodoro → `task-status-hooks` → `nightly`. Those are jobs, not CRUD on a Task resource. `kubectl get pod` is resource-oriented because the API is. Bob’s API is a vault and a ledger.
2. **Nesting the daily reports would make the common path longer.** `bob plan`, `bob ready`, and `bob freshness` are the dashboard. CLIG.dev’s help rule is to lead with the most common commands (and `git` does exactly that: clone / add / commit stay at the top, not under `git object`). Putting them under `bob task` is the opposite of that rule.
3. **`bob capture` cannot grow nested protocol subcommands.** Capture’s payload is arbitrary `TEXT`. `bob capture parse` is either a protocol call or a task whose first word is “parse”. Clap `args_conflicts_with_subcommands` would reserve every protocol verb forever. Mac Capture’s `BobProcessClient` spawns `capture-parse`, `capture-rewrite`, `capture-complete`, `capture-task-id`, `capture-pomodoro-name`, `capture-targets`, and `capture` by those exact tokens, with `schema_version` checks. Moving them under `capture` is a coordinated breaking change for a thin client whose whole point is “bob is the only grammar.”
4. **The painful names are misnamed, not ungrouped.** `task-status-hooks` is a vault-wide reconcile of sticky lanes, derived Blocked, and ledger cleanup. `move-done-tasks` is an archive pass. Neither becomes clearer as `bob task hooks` / `bob task move-done`. They become clearer as verbs: `reconcile`, `archive`.
5. **`sase` is a caution, not a template.** `sase -h` shows a curated “Common commands” list and hides the long tail behind `--full-help`. That *help* pattern is worth stealing. The *tree* pattern (dozens of noun topics, including a `task` that is an alias of `proc`) is a platform CLI. Bob is not a platform. Copying `sase task` into bob would collide with two different meanings of “task” in the same house.
6. **A big argv move is expensive relative to the UX win.** Callers include Bob Mac Capture, `just install-smoke`, tmux `#(bob tmux-pomodoro)`, the `bob_notify` / `bob_pomodoro` / `tmux_bob_pomodoro` shims, cron/`bob nightly`, agent skills (`bob query`), and a large CLI test suite. Help headings and hidden plumbing change none of that. A `bob task` cut changes all of it.

The plan’s *goal* (make the surface easier to understand) is good. The working example (`bob task` as a folder for current commands) is a bad cut. Treat this as a **help-and-naming** problem with a small, optional nesting follow-up, not as a tree rewrite.

---

## 3. Justified requirement adjustments

These change the user’s wording. They are deliberate.

| Original implication | Adjustment | Why |
| --- | --- | --- |
| Group some current commands under a new `bob task` | Do not introduce `bob task` as a parent of existing commands. If a `bob task` ever appears, it should be a **new** single-resource command (show / id / toggle one task by ref), not a folder. | “Task” names the product’s data type. Folders should name jobs or bounded nouns (`gkeep`, `highlights`, `plugins`). |
| Reorganization means changing argv | Phase 1 changes **help and completion presentation only**. Argv stays. Nested aliases and renames are Phase 2 and need compatibility aliases. | Mac Capture, shims, tmux, and tests bind to names. Help can improve this week without a dual-dispatch window. |
| Nest the `capture-*` family under `bob capture` | Keep hyphenated top-level names. Hide them from default help. Keep them in Tab under `capture protocol`. Optionally show them on `bob --full-help`. | Free-text parent + versioned subprocess protocol. See §6. |
| Nest `plan` / `ready` / `freshness` / `randomize` with the task commands | Keep them top-level porcelain verbs. | They are the daily dashboard; extra tokens do not disambiguate. |
| Apply grouping uniformly | Nest only when (a) one noun has two or more verbs, (b) the parent is not a free-text command, and (c) a bare invocation can default to the common verb. That is already the house rule. | Matches `gkeep`, `plugins`, `freshness`, `vault-sync`. |
| Listed subcommands stay a single alphabetical list (`cli_rules.md`) | Keep **alphabetical order inside a heading**. Allow workflow-ordered **headings** (or a compact-vs-full help split). Amend `cli_rules.md` when help headings land. | Scanability beats a 28-row A–Z dump. Alphabet inside a group preserves guessability. |
| One regrouping PR | Split: (1) help/hide plumbing, (2) optional `pomodoro` nesting with aliases, (3) optional verb renames with aliases. | Each slice is independently shippable and reversible. |

---

## 4. What `bob` actually is today

### 4.1 Top-level dispatch

`src/runner.rs` is a sorted table of 28 public names plus two hidden aliases. Every public entry is a `trailing_var_arg` delegate; nested flags live in each module’s own clap tree. Help renders in declaration order; `subcommands_are_sorted_alphabetically` guards the invariant.

**Porcelain (18)** — Tab group `commands`:

| Command | Role | Nested verbs already? |
| --- | --- | --- |
| `capture` | Write tasks/bullets; free-text `TEXT` | no (must stay that way) |
| `completion` | Install/inspect shell completion | `install`, `status`, `uninstall`, `bash`, `zsh` (bare → status) |
| `freshness` | Tiered review queue | `list`, `seed` (bare → list) |
| `gkeep` | Keep → vault drain | `list`, `pull`, `doctor`, `login` (bare → list) |
| `highlights` | PDF annotations ↔ ref notes | `clip`, `create`, `doctor`, `marker`, `scan`, `sync` (required) |
| `move-done-tasks` | Archive done/canceled blocks | no |
| `nightly` | Cron entry: vault-sync → archive → vault-sync | no (it *is* a sequence) |
| `notify` | Watch the current Pomodoro and notify | no |
| `plan` | Today’s budget, Today’s tasks, NEXT/PENDING | no |
| `plugins` | List/deploy custom Obsidian plugins | `list`, `sync` (bare → list) |
| `pomodoro` | Print current Pomodoro status | no |
| `projects` | `^prj` lifecycle | `list`, `sync` (required) |
| `query` | Dataview / Tasks queries | flags, not verbs |
| `randomize` | Re-roll due prioritized tasks | no |
| `ready` | Per-note Ready lane vs cap | no |
| `task-status-hooks` | Reconcile lanes, deps, ledger | no |
| `tmux-pomodoro` | Status-line format of `pomodoro` | no |
| `vault-sync` | Git reconcile of the vault | `run`, `status` (bare → run) |

**Plumbing (10)** — Tab group `capture protocol`:

`capture-complete`, `capture-parse`, `capture-pomodoro-name`, `capture-pomodoros`, `capture-rewrite`, `capture-sections`, `capture-targets`, `capture-task-id`, `capture-task-sections`, `capture-tasks`.

**Hidden aliases:** `mark-next-tasks`, `task-status-setter` → `task-status-hooks`.

Live `bob --help` also injects clap’s `help` subcommand. The `AFTER_HELP` example block currently leads with **nine** protocol examples before `completion` / `query` / `freshness`. Even a user who skips the command table still sees plumbing first.

### 4.2 The grouping that already exists

Bob is not a flat bag of 28 unrelated tools. It is already grouped three ways:

1. **Nested clap trees** for nouns with several verbs (table above).
2. **Completion tiers** (porcelain vs capture protocol) that help does not mirror.
3. **Docs** (`docs/README.md`, getting-started “What commands change”) already cluster by job: capture, plan/ready/freshness, vault git, archive, randomize, plugins, gkeep, highlights, completion.

The missing piece is that (1)–(3) never appear in `bob --help`. A new parent command is not required to surface them.

### 4.3 Who is bound to the current names

**Bob Mac Capture** (`sase repo open gh:bobs-org/bob-mac-capture`, `Sources/CaptureCore/BobProcessClient.swift`) spawns, with `schema_version` 1:

- `capture-parse --format json -- <draft>`
- `capture-rewrite --cursor N --format json -- <draft>`
- `capture-complete --all-tasks --cursor N --format json -- <draft>`
- `capture-task-id --route … --task-ref … --block-id … --format json`
- `capture-pomodoro-name --pomodoro-ref … --name … --format json`
- `capture-targets --format json`
- `capture [--dry-run] [--no-clip] --format json -- <draft>`

The remaining protocol commands (`capture-tasks`, `capture-sections`, `capture-pomodoros`, `capture-task-sections`) are not spawned by the app; they are the same family for shell completion and any later client. The thin-client decision (`decisions:mac-capture-is-a-thin-client`) says the JSON contract grows additively and command names are the transport.

**Shims (Cargo `[[bin]]` + README compatibility table):** `bob_notify` → `bob notify`; `bob_pomodoro` → `bob pomodoro`; `tmux_bob_pomodoro` → `bob tmux-pomodoro`. Tmux status lines call `#(bob tmux-pomodoro)` (README).

**Install smoke** (`justfile`) asserts `--help` on every `capture-*` name.

**Agents** call `bob query` by that exact verb (skills `bob_query` / `bob_dataview`).

Any argv regrouping has to keep these spellings as aliases for a long time. Help regrouping does not.

---

## 5. How comparable CLIs cut this problem

### 5.1 Porcelain vs plumbing (git)

Git keeps ~30 human commands visible and hides the low-level toolkit (`hash-object`, `update-index`, …) from default `git` help. Plumbing stays callable and is documented for scripts. The interface of plumbing is the stable one; porcelain may change to improve humans (`git(1)`, Pro Git ch. 10).

Bob already named this split (`CompletionTier::{Porcelain,Plumbing}`) and then listed plumbing in default help anyway. The git move is: **stop listing plumbing by default**, do not rename it.

Git also leads help with *common* commands grouped by situation (start a working area / work on the current change / …), not with a single A–Z dump. That is the CLIG.dev rule “display the most common flags and commands at the start of the help text.”

### 5.2 Compact vs full help (sase)

`sase -h` prints a short “Common commands” list. `sase --full-help` prints every topic (50+). `sase` *does* nest by noun (`repo`, `artifact`, `bead`, …) because it is a platform with many resources. It also has a `task` topic that is an alias of `proc` — evidence that “task” is already overloaded in this house and a bad folder name for bob.

Steal the **compact/full help** idea. Do not steal the 50-topic noun tree.

### 5.3 Resource vs verb (gh, kubectl, heroku)

- **gh / heroku:** noun then verb (`gh pr list`, `heroku apps:create`). Fits an HTTP API of many resource types with the same CRUD verbs.
- **kubectl:** verb then noun (`kubectl get pod`) because one verb applies across types.
- **git / bob:** verb at the top (`commit`, `capture`, `plan`) because the user is doing a job, not picking a resource type.

Medium’s “Structuring a CLI” note is the same cut: pick resource-oriented when the product is an API of many nouns; pick command-oriented when the product is a workflow. Bob is a workflow.

Heroku’s style guide adds a useful constraint: a topic should be a **plural noun with verbs under it**, and the bare topic lists those nouns. `bob gkeep` / `bob plugins` already match. `bob task` would only match if its job were “list/show/edit tasks.” That command does not exist; `bob query`, `bob plan`, and `bob ready` are different reports over the same rows.

### 5.4 CLIG.dev (clig.dev)

Relevant rules, applied:

- **Human-first, ease of discovery.** Default help is the GUI of a CLI. 28 alphabetized peers with plumbing first fails this.
- **Lead with examples of common complex uses.** Current `AFTER_HELP` leads with protocol invocations a human almost never types (`capture-complete --cursor 1 --format json`). Move those to each protocol command’s own `--help`.
- **Consistency.** Bob already has a nest-when-the-noun-has-verbs rule. A one-off `bob task` folder that mixes reports, reconcile, and archive would be the inconsistency.
- **Do not make users remember two spellings without an alias.** Any Phase 2 rename keeps the old name hidden, the same way `task-status-setter` already works.

---

## 6. Candidate groups, scored

Scoring: **Do** / **Maybe** / **Don’t**. “Do” means change help or (for Maybe) add nested *aliases*. None of the “Do” rows require breaking argv.

### 6.1 Capture protocol — Don’t nest; Do hide

| Keep as | Why |
| --- | --- |
| Top-level hyphenated names | `bob capture` consumes `TEXT`. Nested verbs would reserve words in drafts. |
| Hidden from default `bob --help` | They are a frontend protocol, not daily verbs. Completion already treats them that way. |
| Visible on `bob --full-help` and each command’s `--help` | Scripts and Mac Capture still need to find them. |
| Unchanged argv | `BobProcessClient` + `schema_version` + `just install-smoke`. |

A third parent (`bob proto parse`, `bob cap parse`) is worse than hyphenation: extra token, new jargon, still a Mac Capture break.

### 6.2 `bob task {plan,ready,freshness,…}` — Don’t

Commands one might dump here: `plan`, `ready`, `freshness`, `randomize`, `task-status-hooks`, `move-done-tasks`, `projects`, maybe `query`.

They do not share a user question:

| Command | Question it answers |
| --- | --- |
| `plan` | What is today (themes, links, caps)? |
| `ready` | Which notes are over the Ready cap? |
| `freshness` | What is due for review, in walk order? |
| `randomize` | Re-roll stale priority windows. |
| `task-status-hooks` | Make the ledger and derived Blocked true. |
| `move-done-tasks` | Archive closed blocks. |
| `projects` | How are `^prj` trackers? |
| `query` | Run an arbitrary Dataview/Tasks expression. |

A folder named `task` says “these are all about tasks,” which is true and useless — `capture` and `gkeep` are also about tasks. The cost is a mandatory extra token on the three commands in the morning loop.

### 6.3 Pomodoro status tools — Maybe (nested aliases only)

`pomodoro`, `tmux-pomodoro`, and `notify` are one domain: **read the ledger, don’t start sessions** (session operators live in `capture`). README already documents them as a unit.

Recommended shape, all additive:

```text
bob pomodoro              # unchanged: human status
bob pomodoro tmux         # same as bob tmux-pomodoro
bob pomodoro notify …     # same as bob notify
```

Keep `bob tmux-pomodoro` and `bob notify` as public aliases so tmux configs and shims do not move. Do not put `capture-pomodoros` / `capture-pomodoro-name` here; those are protocol writes/lists for the capture panel.

This is optional polish, not the main fix. Three porcelain names dropping to one visible noun is nice; tmux and notify are already discoverable from README.

### 6.4 Vault maintenance — Don’t nest `nightly`

`nightly` *calls* `vault-sync` then `move-done-tasks` then `vault-sync`. That is composition, not a missing parent. Cron wants a verb (`bob nightly`). `bob vault nightly` is longer and no clearer. `vault-sync` already has `run` / `status`. Leave this family as three top-level porcelain commands; they can share a **help heading** named Vault.

### 6.5 Verb renames — Maybe, independently of grouping

| Today | Better verb | Keep as hidden alias |
| --- | --- | --- |
| `task-status-hooks` | `reconcile` | `task-status-hooks`, `task-status-setter`, `mark-next-tasks` |
| `move-done-tasks` | `archive` | `move-done-tasks` |

These are the two names that make the porcelain list look like an internal toolkit. Renaming is a better response than wrapping them in `bob task`. Do this in a dedicated PR after help, because every docs page and agent memory line currently says `task-status-hooks`.

`tmux-pomodoro` is awkward but is also a copy-paste token in tmux configs; leave the public name unless the nested `bob pomodoro tmux` alias is enough.

---

## 7. Recommended solution

**Primary move: regroup help, not argv.**

Implement a compact default help that a human can scan, and a full inventory for protocol/script users. Keep every current command name working. Optionally, later, add nested Pomodoro aliases and verb-rename the two worst porcelain names.

This is the same product instinct as `sase -h` / `sase --full-help` and as git’s “common commands” vs `git help -a`, applied to a 18+10 command workflow CLI.

### 7.1 Phase 1 — help (do this)

Default `bob --help` / `bob -h`:

1. Short about + usage (already good).
2. **Headings in workflow order**, commands alphabetical inside each heading. Porcelain only.
3. A one-line pointer: protocol endpoints are listed by `bob --full-help`; Tab already groups them as `capture protocol`.
4. **Examples of daily work only** (capture a task, plan, freshness, ready, query, nightly, gkeep pull --dry-run, completion install). Move protocol examples to those commands’ own `--help`.

Suggested headings and membership:

```text
Capture
  capture

Today
  plan
  pomodoro

Review
  freshness
  randomize
  ready

Vault
  move-done-tasks
  nightly
  projects
  task-status-hooks
  vault-sync

Integrations
  gkeep
  highlights
  plugins
  query

Sessions
  notify
  tmux-pomodoro

Shell
  completion
```

`bob --full-help` (new, analogous to `sase -H`) repeats the porcelain table and then lists the ten `capture-*` commands under **Capture protocol**, still alphabetical.

Plumbing stays fully dispatchable. Hidden aliases stay hidden.

Implementation sketch, staying inside today’s delegate runner:

- Mark the ten plumbing entries `.hide(true)` on the root clap command (same mechanism as `mark-next-tasks`).
- Replace the giant `AFTER_HELP` with porcelain examples + the `--full-help` pointer.
- Implement `--full-help` / `-H` on the root by rendering the hidden subcommands (custom help path, or a second clap command used only for that flag).
- If clap 4.6 cannot attach per-subcommand help headings cleanly, a custom `{all-args}` replacement in `HELP_TEMPLATE` is acceptable; scanability wins over using clap’s default table.
- Amend `cli_rules.md`: listed subcommands stay alphabetical **within a heading**; heading order is workflow order.
- Tab completion is already correct; do not hide plumbing from `__complete`.

Risk: low. Tests that snapshot full `bob --help` text will need updating (`tests/cli/help.rs`, `just install-smoke` already calls `bob --help` only for exit 0).

### 7.2 Phase 2 — optional nested aliases

Only if Phase 1 still leaves “why three Pomodoro commands?” as a live complaint:

```text
bob pomodoro            # status (unchanged)
bob pomodoro tmux       # alias of tmux-pomodoro
bob pomodoro notify     # alias of notify
```

Keep the old names public (not hidden) until tmux configs and shims are bored of them. Then hide, do not delete.

Do **not** nest `nightly` or `vault-sync`. Do **not** nest protocol under `capture`.

### 7.3 Phase 3 — optional verb renames

```text
bob reconcile    # alias-canonical for task-status-hooks
bob archive      # alias-canonical for move-done-tasks
```

Canonical help and README switch; old names remain forever as hidden aliases, matching the existing `task-status-setter` pattern. Coordinate agent memories and docs in the same PR. No Mac Capture impact.

### 7.4 Explicit non-goals

- No `bob task` parent for current commands.
- No `bob capture parse` (or `complete`, `targets`, …).
- No moving `plan` / `ready` / `freshness` / `query` / `randomize` under any noun.
- No breaking Mac Capture argv in the same release as a help-only change.
- No requirement that new grouping wait on unifying the delegate runner with the nested clap trees (completion already composes those trees separately).

---

## 8. Recommended command map (end state)

Public names a human should see in default help, after Phases 1–3. Italics are optional Phase 2/3.

| Heading | Command | Notes |
| --- | --- | --- |
| Capture | `capture` | Free-text write path. Protocol siblings stay hyphenated and hidden. |
| Today | `plan` | Read-only dashboard. |
| Today | `pomodoro` | Status. *Nested `tmux` / `notify` if Phase 2.* |
| Review | `freshness` | Bare = `list`; `seed` stays nested. |
| Review | `ready` | Per-note cap. |
| Review | `randomize` | Bulk re-roll. |
| Vault | *`reconcile`* | Today: `task-status-hooks`. |
| Vault | *`archive`* | Today: `move-done-tasks`. |
| Vault | `nightly` | Cron verb. |
| Vault | `vault-sync` | Bare = `run`; `status` nested. |
| Vault | `projects` | `list` / `sync`. |
| Integrations | `query` | Dataview/Tasks. |
| Integrations | `gkeep` | Bare = `list`. |
| Integrations | `highlights` | Subcommand required. |
| Integrations | `plugins` | Bare = `list`. |
| Sessions | `notify` | Keep until/unless Phase 2 hides it. |
| Sessions | `tmux-pomodoro` | Keep until/unless Phase 2 hides it. |
| Shell | `completion` | Bare = `status`. |

**Always callable, default-hidden, `--full-help` + Tab `capture protocol`:**

`capture-complete`, `capture-parse`, `capture-rewrite`, `capture-targets`, `capture-tasks`, `capture-sections`, `capture-task-sections`, `capture-task-id`, `capture-pomodoros`, `capture-pomodoro-name`.

**Forever aliases (hidden):** `mark-next-tasks`, `task-status-setter`, and after Phase 3 the old canonical names `task-status-hooks` and `move-done-tasks`.

Default help then shows **~16–18** commands instead of 28, in six named jobs, with the morning loop (`capture`, `plan`, `pomodoro`, `freshness`, `ready`) on the first screen instead of under a pile of `capture-*` plumbing.

---

## 9. If you still want a `bob task` someday

Build a **new** command that does one thing the CLI cannot do today: operate on a *single* task by stable ref (`route:block-id` or the capture `--task-ref` token).

```text
bob task show   <ref>     # one task: lane, freshness, deps, links
bob task id     <ref>     # wrap capture-task-id
bob task toggle <ref>     # wrap the capture toggle path
```

That is Heroku/gh-style (noun + verb on one resource). It does **not** absorb `plan`, `ready`, or `freshness`. Those reports stay verbs because they are not “a task.” Shipping this without Phase 1 would still leave `bob --help` unreadable; shipping Phase 1 without this is already a complete answer to the original question.

---

## 10. Sources

### This tree

- `src/runner.rs` — `SUBCOMMANDS`, `CompletionTier`, hidden aliases, `HELP_TEMPLATE` / `AFTER_HELP`
- `src/native.rs` — `NativeCommand` enum (28 variants)
- `src/native/completion/present.rs`, `docs/completion.md` — porcelain vs `capture protocol`
- Nested CLIs: `src/native/{gkeep,highlights_ref,plugins,projects,freshness,completion,vault_sync}/**`
- `docs/README.md`, `docs/getting-started.md`, `README.md` (daily workflow, compatibility shims)
- `sase/memory/cli_rules.md` via `sase memory read`
- `sase memory read decisions:mac-capture-is-a-thin-client`

### Mac Capture (external checkout)

- `Sources/CaptureCore/BobProcessClient.swift` — exact argv + `expectedSchema: 1`

### Live help

- `bob --help` (28 commands, plumbing first)
- `sase -h` vs `sase --full-help` (compact common list vs full inventory)

### External

- [Command Line Interface Guidelines](https://clig.dev/) — human-first help, lead with common commands/examples
- [Git Internals: Plumbing and Porcelain](https://git-scm.com/book/en/v2/Git-Internals-Plumbing-and-Porcelain)
- [Heroku CLI style guide](https://devcenter.heroku.com/articles/cli-style-guide) — topics as nouns, verbs underneath, bare topic lists
- [kubectl conventions](https://github.com/kubernetes/community/blob/main/contributors/devel/sig-cli/kubectl-conventions.md) — verb+noun for multi-type APIs
- [Structuring a CLI](https://medium.com/pon-tech-talk/structuring-a-cli-22e2492717de) — resource-oriented vs command-oriented
