# `:` Command-Mode for bob in Obsidian — Research & Recommendation (`mus`)

- Date: 2026-10-26. Researcher: `mus` (independent swarm member; peer reports not consulted).
- Question: add a `:` keymap to Obsidian that opens a new bob command-mode
  (filterable command list, run from inside Obsidian, success/failure
  notification with full-output view). Lead the design; critique the plan;
  end with a recommended solution.
- Repos inspected (read-only): `bob-cli` workspace checkout (`src/runner.rs`
  command table, `src/native.rs`, `completion/protocol.rs`, `cli_rules.md`,
  `docs.md` memory); `bob-plugins` linked checkout (via `sase repo open`),
  especially `bob-navigation-hotkeys/src/200-filtered-picker-modals.js`
  (`FilteredPickerModal`), `490-plugin-lifecycle.js` (command registration),
  `610/620` vim-jump/vimrc bridge files, `bob-ledger-tools/src/236-plugin-stats-data.js`
  (`bobSpawnJson`); vault `~/bob/obsidian_vimrc.md` and
  `~/.obsidian/hotkeys.json` conventions.

## 1. What `bob` offers today (the candidate command surface)

The canonical inventory is the `SUBCOMMANDS` table in
`src/runner.rs` (single source for root help *and* shell completion), grouped
by workflow section. User-facing top-level commands:

- **Daily workflow:** `capture`, `freshness`, `plan`, `pomodoro`
  (`status` default, `notify`, `tmux`), `ready`, `stats` (`overview` default,
  `metrics`, `show`), `themes` (`list` default, `hide`, `unhide`, `color`, `rename`).
- **Tasks and projects:** `projects`, `relations` (`list` default, `hide`,
  `unhide`, `rename`), `task` (`archive`, `move`, `reconcile`, `reroll` — all
  vault-wide rewrites, no default member).
- **Vault:** `articles`, `nightly`, `query`, `ref`, `vault-sync`.
- **Integrations:** `gkeep`. **Setup:** `completion`, `plugins`.
- **Capture protocol (frozen siblings):** `capture-complete`,
  `capture-parse`, `capture-pomodoro-name`, `capture-pomodoros`,
  `capture-related`, `capture-rewrite`, `capture-sections`,
  `capture-targets`, `capture-task-id`, `capture-task-sections`,
  `capture-tasks`, `capture-templates` (`list` default + `save/show/delete/clear`).
- Hidden permanent aliases (`ALIASES` table, never shown in help):
  `highlights→ref`, `move-done-tasks→task archive`,
  `task-status-hooks→task reconcile`, `randomize→task reroll`, etc.

Two machine-readable sources already exist that a picker could consume instead
of a hand-maintained list: the `bob __complete <shell> --protocol N` completion
protocol (`src/native/completion/protocol.rs`, emits
`value<TAB>description<TAB>group<TAB>space|nospace` candidates) and the
`docs_catalog()` library function (help sections in `bob --help` order). Both
derive from the same `SUBCOMMANDS` table, so a generated catalog can never
drift from the CLI.

Many (not all) commands accept `-f/--format json` (`plan`, `stats show`,
`query`, `themes list`, `relations list`, capture-protocol readers, etc.).
JSON-capable commands can be rendered richly; the rest are text-only.

## 2. Hard constraints the design must respect

1. **A bare `:` hotkey is impossible in Obsidian proper.** Obsidian hotkeys
   require a modifier (`Ctrl/Cmd/Alt/Shift + key`); a bare printable character
   cannot be registered via `addCommand({hotkeys})`. The vault gets vim-style
   keys through `obsidian-vimrc-support`: `:` opens the vim ex-command line,
   and `exmap <name> obcommand <plugin>:<command-id>` + `nmap <keys>
   :<name><CR>` bindings live in `~/bob/obsidian_vimrc.md` (e.g.
   `nmap - :bob_daily<CR>`, `nmap Z :bob_zoom_image<CR>`). So the `:` trigger
   must be a **vim normal-mode mapping**, not an Obsidian hotkey — e.g.
   `exmap bob_command_mode obcommand <plugin>:open-command-mode`.
2. **Do not hijack vim's `:` ex line.** `:` in normal mode is load-bearing
   muscle memory (it powers every `:bob_*` mapping above). Remapping `:` to
   open the modal would break all of them. The modal should instead *look*
   like a vim command line (a `:`-prefixed input row) while being triggered
   by a different binding (recommended: a leader-style normal-mode key the
   vault leaves free, user-remappable in the vimrc, plus a palette command
   `Bob: Open command mode` so non-vim users get `Ctrl/Cmd+P` access).
3. **Desktop-only spawning.** The proven spawn path is
   `bob-ledger-tools/src/236-plugin-stats-data.js::bobSpawnJson`: optional
   `require("child_process").execFile` (argv array, **never a shell string**),
   `BOB_DIR=<vault path>` + `NO_COLOR=1` environment, explicit
   `timeout`/`maxBuffer`, a `tried`-path error model, and a graceful
   `bob-not-found` card when `child_process` is unavailable — i.e. on mobile.
   Command-mode inherits this: desktop-only execution, clean mobile
   degradation (explain, don't crash).
4. **`cli_rules.md` (reference memory, read for this report):** never
   hard-rename/remove commands (aliases are permanent); never add subcommands
   under `bob capture` (free TEXT swallows them); groups need membership
   rules. A command-mode catalog must therefore track canonical paths and
   resolve aliases, and must not invent new `capture` sub-spellings.
5. **Thin-client precedent** (`decisions:mac-capture-is-a-thin-client`, and
   the ledger-tools pattern generally): the plugin renders what `bob`
   returns; it never re-parses capture grammar or re-derives plan/freshness
   state. Command-mode is a launcher + output viewer, not a second
   implementation of any command.
6. **Concurrency with the vault.** `bob` rewrites note files while the user
   may have them open (task reconcile/move/archive, themes/relations
   rewrites, vault-sync). The editor must be refreshed/re-read after a
   write-command (Obsidian generally picks up disk changes, but the active
   pane should revalidate), writes should be single-flight (the stats-data
   module already serializes behind one running spawn — reuse that queue),
   and `nightly` stays cron-owned (see §4).

## 3. Which commands belong in command-mode (and which do not)

Recommended catalog shape: **curated allowlist generated at build time from
the `SUBCOMMANDS`/completion data, not a hand-typed list and not "every
string bob accepts."** Free-form argv typing stays available (power users),
but the default list is curated per the tiers below.

- **Tier 1 — include first (read-only, fast, high Obsidian value):**
  `plan`, `ready`, `freshness`, `stats` (+`show`/`metrics`), `query`,
  `projects`, `themes list`, `relations list`, `pomodoro status`,
  `capture-pomodoros`, `ref` (read paths), `articles` (read paths). These
  answer "what should I do now?" without leaving the editor — the core win.
- **Tier 2 — include with confirmation and/or `--dry-run` preview:**
  `task reconcile` (has `--dry-run`; show the preview, confirm to apply),
  `task archive`, `task move`, `task reroll`, `themes hide/unhide/color`,
  `relations hide/unhide`, `vault-sync` (long; progress + confirm),
  `gkeep` (imports into the vault; confirm), `ref rename` / `themes rename`
  / `relations rename` (each is one verified vault-wide commit; show the
  plan/preview first per their `--dry-run` where offered).
- **Tier 3 — exclude:** all `capture-*` protocol commands except none —
  they take internal cursor-context subprocess arguments and are meaningless
  standalone (calling them from command-mode can only confuse); `pomodoro
  notify` and `pomodoro tmux` (never-exit background loops — a modal spawn
  would hang until timeout); `completion install` (mutates shell dotfiles,
  not vault work); `plugins sync` (deploys to the vault; keep it in the
  palette/terminal, not one keystroke away); `nightly` (cron-owned sequence;
  running it by hand risks double-run against the lock — link to logs
  instead); bare `capture` (its free-text grammar deserves its own capture
  UX, not an argv text field; revisit only after the core mode lands).

Every entry stores: canonical path, one-line `about` (from the command
table), read-only vs write flag, JSON-capable flag, default args, and a
`confirm` policy. Alias inputs (`move-done-tasks`) resolve to canonical
paths silently in displayed results.

## 4. Critique of the plan as stated

- **"Any bob command" is too broad.** Tier 3 above shows commands that are
  useless or dangerous outside their harness. An unfiltered runner also
  becomes an arbitrary-argv footgun one keystroke from vault-wide rewrites.
  Adjustment: curated catalog + typed-args field, with the catalog generated
  so it cannot rot. (This is the one deliberate scope reduction; everything
  else below widens or refines the request.)
- **`:` as the trigger needs the vimrc caveat (§2.2).** Ship the
  vim-aesthetic input (`:` prefix, `Enter` runs, `Esc` closes) with a
  non-`:` trigger. Document the one-line vimrc addition.
- **"Notified on completion with full output" underspecifies two cases the
  design must cover:** (a) long commands (`vault-sync`, `gkeep`, `task`
  rewrites on a big vault) need *progress*, not just a completion toast —
  run async with a cancellable busy state; (b) failures need the *actionable*
  error model ledger-tools already built (`bob-not-found` → "set
  `stats.bob_path`…", `timeout` → retry, `schema-mismatch` → upgrade both
  sides), not a raw stack trace. Reuse `statsErrorModel`'s shape.
- **Output rendering should prefer JSON where the command offers it.**
  Raw-text-only display wastes the `-f json` contracts (§1). Rule: run with
  `--format json` when the catalog marks the command JSON-capable, render a
  small structured view (tables/lists reusing ledger-tools block styles),
  and always offer "view raw output."
- **Missing from the request: history and auditability.** A command runner
  without history is a black box. Keep last-N runs (command, args, exit,
  duration, timestamp) in plugin data, viewable from the modal; vault
  writes already land in git via existing commit paths, so history + git log
  = full audit.
- **Mobile and bob-missing paths must be designed, not discovered.** Per
  §2.3 the modal opens everywhere but execution degrades to the
  actionable-error card on mobile/no-bob.

## 5. Recommended solution

**A new small plugin, `bob-command-mode`** (not an addition to
`bob-navigation-hotkeys`, which is already a ~700-fragment monolith with a
1000-line-per-fragment budget and its own review-walk lifecycle; a focused
plugin keeps blast radius small and can depend on the two proven modules
below without entangling them).

1. **Trigger:** palette command `Bob: Open command mode` (works everywhere,
   hence non-vim users and mobile UI) + documented vimrc lines
   (`exmap bob_command_mode obcommand bob-command-mode:open-command-mode`,
   `nmap <leader-or-free-key> :bob_command_mode<CR>`). No Obsidian hotkey
   default; users bind one if wanted.
2. **Picker:** reuse the `FilteredPickerModal` pattern (`bob-cnp` styles,
   fuzzy filter, footer hints) — either factor it into a shared fragment or
   copy the ~200-line core with attribution. Input row renders with a `:`
   prefix and supports `> command args...` free-text after the curated
   rows; `Enter` runs, `Shift+Enter` (or a toggle) forces `--dry-run` when
   the command offers it, `Esc` closes without running.
3. **Catalog:** generated at plugin build time from `bob`'s own data
   (`docs_catalog()` or `bob __complete` dump checked into the plugin repo
   by a script), carrying the Tier 1/2 allowlist plus per-command
   `{about, readOnly, jsonCapable, needsConfirm, defaultArgs}`. Regenerate
   on each bob-cli release (daily train); a stale catalog degrades to
   "unknown command — run in terminal" rather than guessing.
4. **Execution:** reuse `bobSpawnJson` semantics (execFile argv, `BOB_DIR`,
   `NO_COLOR=1`, timeout, single-flight queue, `tried`-list errors).
   Confirm-step for every Tier 2 write (preview output first where
   `--dry-run` exists). Cancel button kills the child on timeout-track.
5. **Results:** `Notice` toast on completion (`✔ plan (0.4s)` /
  `✘ task archive failed — Show output`); full output in a read-only modal
   (structured view for JSON-capable commands, raw-text fallback, copy
   button); error card reuses the actionable error model with Retry;
   run history (last ~20) persisted in plugin data and browsable from the
   modal footer.
6. **Docs & rollout:** plugin reference page under `bob-plugins/docs/`
   (per `docs.md`: behavior contract + hotkey/vimrc lines, not README
   sprawl); `just docs-check`/`npm run validate` gates; ship Tier 1 first,
   Tier 2 behind the confirm flow in a follow-up; explicitly out of scope:
   Tier 3, background-loop commands, mobile execution.

**Why this shape:** it delivers the request's core value (no terminal
context-switch for the dozen commands Bryan runs all day) while honoring
every load-bearing constraint found in the repos — Obsidian's hotkey model,
the vim ex line, desktop-only spawning, thin-client rendering, and the CLI
rules that forbid alias/grammar drift. The build-time-generated catalog is
the detail that keeps the feature from rotting as `bob` gains commands on
the daily train.
