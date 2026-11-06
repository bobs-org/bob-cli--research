# `just install-all`: live progress, an honest ETA, and a "What's new" digest

*Researcher: cld · 2026-11-06 · bob-cli @ `b6a96243`, bob-plugins @ `5fbe82a`,
bob-mac-capture @ `a2aab30`*

## Question

`just install-all` can sit for several minutes on the bob-cli and bob-mac-capture
steps. During that time the screen shows a frozen Cargo bar
(`Building [=====> ] 253/258: bob-obsidian`) and nothing else, as in
`~/tmp/screenshots/20261106_123927.png`. Bryan asked for three things:

1. Progress indication, plus an ETA when the command has run on this machine
   before.
2. A much better summary of newly pulled commits in all three repositories. Show
   full commit messages when they all fit on one screen.
3. A design that is intuitive, reliable, and beautiful.

He also asked for a critique of the plan, with any requirement changes called out
explicitly.

## TL;DR

- **Yes, build it, but make the ETA time-based, not count-based.** Cargo's counter
  is the wrong signal. When pulled commits change source, one 667k-line crate
  (`bob-obsidian`) accounts for nearly all of the wait. Cargo shows 253/258 (98%)
  while that crate starts its 3½ minutes. On a given host its rebuild time is
  stable (209–235 s across four real-commit rebuilds here), so a **median of
  per-host history** gives a good ETA. Without history there is no honest ETA,
  which matches Bryan's instinct: show elapsed time, the current activity, and
  "first timed build here".
- **Hide the build output and show one live line.** Raw compiler output is why the
  screen looks frozen. It would also push any commit summary off the screen. Build
  output goes to a log file. On failure the run prints the error excerpt and the log
  path. `-v/--verbose` restores today's raw stream.
- **Pull all three repos first, then show "What's new" before the long builds.**
  The commit digest then fills the dead time with something worth reading, and the
  whole-run estimate ("about 4m 40s · done around 12:44") is known up front.
- **The full-messages idea needs a budget.** bob-cli lands about 40 commits/day
  (median of 24-hour windows over the last 21 days). A daily run pulls about 65
  commits across the three repos, so full messages fit only for frequent runs. I
  propose four layout levels (full → first paragraph → subjects → grouped). The
  richest level that fits the screen wins. Breaking changes always show their
  `BREAKING CHANGE:` text. SASE trailers are always stripped. Change types use the
  same groups as `release-plz.toml`.
- **Range fix:** "new commits" should mean *since the last successful install on
  this machine*, not *since this pull*. Today a manual `git pull` before the
  install shows "up to date" even though the install ships new code.
- **Ring the bell when a long run finishes.** Bryan's tmux has `monitor-bell on`
  and kitty has `enable_audio_bell yes`, so this one byte covers the "I walked away"
  case.
- **Implementation:** keep `scripts/install_all` (bash) as the orchestrator. Add one
  stdlib-only Python 3.9 helper, `scripts/lib/install_all_ui.py`, for the live line,
  the ETA history, and the digest, with unit tests in `just check-scripts`.
- **Speedups:** the profile tweaks I measured buy little (`opt-level=1` saved 12%).
  The one cheap structural win is to overlap the Swift build with the Rust build on
  macOS. I defer it to a measured phase 3.

## What happens today

`just install-all` runs `scripts/install_all` (827 lines of bash). The sequence:

1. Header and an optional clone offer (`offer_missing_clones`,
   `scripts/install_all:316`).
2. **bob-cli:** `pull_repo` (`:219`) runs `git pull --ff-only` and prints
   `1 new commit · e0960045 → ec39e1a0`. When bob-cli updated, the script re-execs
   itself (`:774`) so the freshly pulled script runs the rest. It then runs
   `just install` (`:778`), which prints its own nested `📦 INSTALL` banner (the
   duplicate banner in the screenshot) and streams `cargo install` raw
   (`justfile:144`).
3. **bob-plugins:** pull, `bob plugins sync --dry-run --format json`, sync, verify
   (`plugin_step`, `:355`). This step only copies files: built `main.js` files are
   committed in bob-plugins, so it takes seconds.
4. **bob-mac-capture:** pull, then `just install ~/Applications`
   (`mac_capture_step`, `:484`, `:525`). That runs a SwiftPM **release** build of
   the app plus an install-helper product, codesigns, verifies, swaps the bundle,
   and restarts the app.
5. **Obsidian:** restart when plugins changed (`obsidian_step`, `:580`).
6. **Summary:** one row per step with a duration (`print_summary`, `:206`).

The existing visual language is good and worth keeping. Each section gets an emoji
banner with a 48-character colored rule. Commands are echoed dim as `$ …`. Rows use
`✓ ⚠ ✗ – ↻` glyphs. bob already has a progress convention in
`src/native/spinner.rs`: Braille frames `⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏` at 80 ms. Without a TTY,
`BOB_PROGRESS=1` prints one `label…` line and never uses `\r`. The installer should
reuse both.

## Measurements

### Where the time goes (bob-cli)

I took all measurements on **apollo** (Linux, 16 cores). Four peer researchers
were running at the same time, so load average was **13–30** throughout. Absolute
numbers are therefore inflated, and the Mac will differ. The *shape* of the results
is what matters. Each build used `cargo build --profile local-install --locked
--timings` with `RUSTC_WRAPPER=` (as `just install` does). Commit deltas are real
checkouts of master's history.

**Caveat found along the way:** SASE agent shells export `CARGO_INCREMENTAL=0`.
That overrides the profile's `incremental = true`, so my first round measured
non-incremental builds. The table below uses the second round, with the variable
unset as in Bryan's interactive shell.

| Scenario (incremental on) | Wall | `bob-obsidian` lib | frontend / codegen |
| --- | ---: | ---: | --- |
| First build into the incremental cache | 234.8 s | 233.0 s | 109 / 124 s |
| No-op rebuild | 0.5 s | — | — |
| Real 1-commit delta (`ec39e1a0 → b6a96243`, +2.7k lines) | 210.2 s | 208.9 s | 89 / 120 s |
| Real 1-commit delta, reverse direction | 218.0 s | 216.8 s | 92 / 125 s |
| 6-commit delta with a `Cargo.lock` change (new incremental dir) | 228.9 s | 227.5 s | 109 / 118 s |
| One comment line added to a leaf file | 30.0 s | 28.6 s | 20 / 9 s |
| Return to a tree the cache already compiled | 31.0 s | 29.6 s | 21 / 9 s |
| `cargo install` no-op (includes the crates.io index update) | 2.4–2.7 s | — | — |
| Cold build, non-incremental (all 235 units) | 333.9 s | 247.2 s | 117 / 131 s |
| Real 1-commit delta at `opt-level=1` | 184.2 s | 182.6 s | 85 / 98 s |

Findings:

- **On a warm rebuild, one crate is almost the entire wait.** The dependencies
  finish 86 s into a cold build. After that, `bob-obsidian` (667k lines of Rust in
  `src/`) compiles alone, and the four binaries link in under 1 s. Cargo's `253/258`
  therefore reads 98% done at the moment the real work starts. **Unit counts cannot
  drive the bar.**
- **Rebuild time is bimodal, and the slow mode is stable.** A real feature commit
  costs about the same as rebuilding the crate from scratch: 209–235 s, a spread of
  about ±6% under heavy, varying load. Incremental compilation only helps for tiny
  edits (about 30 s) or exact revisits. So "median of recent real rebuilds on this
  host" is a good predictor, and a fast build is a pleasant early finish rather than
  a broken ETA.
- **`Cargo.lock` or toolchain changes are a third mode.** Dependencies recompile,
  and a new `-C metadata` hash means a fresh incremental directory, so the result is
  a full build. Predict this from the diff of the pulled range.
- **Making it faster with profile tweaks is not worth it.** `opt-level=1` saved 12%
  (210 → 184 s) and produces slower binaries. The frontend (about 90–110 s, largely
  serial on stable rustc) is the floor until the crate is split.
- The Swift step could not be measured here (it needs macOS). The design learns its
  duration the same way.

### How many commits a run pulls

These figures simulate running `install-all` every *W* hours over the last 21 days
of first-parent history. Each cell is the median and p90 over windows that had at
least one commit.

| Repo (commits / 21 days) | every 1 h | every 4 h | every 12 h | every 24 h |
| --- | --- | --- | --- | --- |
| bob-cli (829) | 2 / 4 | 7 / 15 | 19 / 39 | 39 / 58 (max 77) |
| bob-plugins (330) | 1 / 3 | 3 / 8 | 8 / 18 | 15 / 25 (max 43) |
| bob-mac-capture (242) | 1 / 2 | 3 / 6 | 6 / 12 | 11 / 19 (max 21) |

### What the commit messages look like

Last 300 commits per repo, after stripping SASE trailers (`SASE_BEAD=`,
`SASE_TYPE=`, `SASE_AGENT=`, `SASE_MODEL=`) and `[n]: https://…` link
references:

| Repo | has a body | body lines p50 / p90 / max | subject chars p50 / p90 / max | breaking `!` |
| --- | ---: | --- | --- | ---: |
| bob-cli | 43% | 3 / 10 / 26 | 61 / 78 / 95 | 30 (10%) |
| bob-plugins | 40% | 3 / 9 / 20 | 64 / 82 / 111 | 6 |
| bob-mac-capture | 47% | 3 / 8 / 21 | 60 / 78 / 110 | 7 |

Body lines are unwrapped paragraphs; the median longest line is 106 characters.
After wrapping, a body is typically 5–7 terminal rows. Without trailer stripping,
**every** commit gains 7 lines of agent metadata, which would make full messages
unreadable. First paragraphs say *what* changed. Later paragraphs are often
verification notes ("The full Rust check passes; docs-check has only…"). Breaking
commits carry a `BREAKING CHANGE:` footer that states the migration. That footer is
the most important text a person installing the update can read.

Types are overwhelmingly `feat` and `fix`. bob-cli also has many `docs` commits
(60/300). `release-plz.toml` already defines the canonical grouping for changelogs:
Breaking → Added (`feat`) → Fixed (`fix`) → Performance (`perf`) → Reverted
(`revert`), and it skips `chore/docs/test/refactor/style`.

## Critique: is this a good idea?

**Yes.** Bryan runs this command often: the screenshot pulled exactly one commit,
which suggests runs every hour or so. Each run blocks for minutes on a frozen
screen. Four things make a wait acceptable, and the plan should be judged against
them rather than against "has a progress bar":

1. **Proof of life.** The screen moves, and it says what is running right now.
2. **A credible "how long"** that never lies. A bar that sits at 98% for three
   minutes is worse than no bar.
3. **Something worth reading while waiting.** The commit digest does this.
4. **A signal when it is done,** for the walk-away case.

The original wording has three traps:

- "Progress indication" naturally points at Cargo's unit counter or a percentage of
  steps. The data shows that both are misleading for this workload.
- "Full commit messages if they fit" is right in spirit. At this repo's commit rate,
  though, it is the exception, and raw messages are mostly SASE trailers. Without a
  layout plan the feature will either overflow the screen or fall back to the
  current one-liner.
- Bolting more output onto today's raw streaming fails on both counts. Cargo and
  SwiftPM output scrolls any summary out of view, and a long bash script grows
  another layer of `printf` state.

### Requirement adjustments (called out explicitly)

| # | Change | Why |
| --- | --- | --- |
| R1 | **The ETA comes from per-host, per-change-kind wall-time history, never from tool counters.** First run on a host: no ETA, but show elapsed time, the current activity, and "first timed build here". | Measured: the unit counter reads 98% when 0% of the time has passed, while warm rebuild time is stable per host. |
| R2 | **Hide the build output** behind one live status line and a log file. Show an error excerpt and the log path on failure. Add `-v/--verbose` for today's raw stream. | Raw output is what looks frozen, and it would scroll the digest away. |
| R3 | **"New commits" means since the last successful install of that repo on this host,** recorded in state. Fall back to the pull range when there is no record. | A manual pull, a failed earlier install, or an agent's push from the same checkout all hide new code from today's pull-range count. |
| R4 | **"Full messages if they fit" becomes a four-level budgeted digest.** Breaking footers always show; SASE trailers are always stripped; types use the `release-plz.toml` groups. | About 40 bob-cli commits per day. Full messages fit only at hourly to four-hourly cadences. |
| R5 | **Pull all three repos before building anything.** Print "What's new" and the whole-run estimate before the first long build. | Reading time overlaps the waiting time, and the estimate covers the whole run. |
| R6 | **Ring the terminal bell when a run took over 30 s.** The summary says how the run compared with usual. | Bryan's tmux and kitty are already set up to surface bells. |
| R7 | **Plain `just install` gets the same live line and feeds the same history.** | Its cargo call is the same long step; shared history builds ETA data faster. |
| R8 | **Speedups are a separate, measured phase.** | Profile tweaks buy little (−12%); overlapping Swift with Rust on macOS may buy more but needs Mac data. |

## Design

### 1. Run structure

```text
pull bob-cli ─► (re-exec if the script changed) ─► pull bob-plugins ─► pull bob-mac-capture
      │
      ├─► WHAT'S NEW digest   (since the last successful install of each repo)
      ├─► plan line           (about 4m 40s · done around 12:44)  ← needs history
      │
      ├─► bob-cli install     (one live line; cargo output to a log)
      ├─► bob-plugins sync    (seconds; names the plugins it updates)
      ├─► mac-capture install (TTY signing preflight, then one live line)
      ├─► Obsidian restart
      └─► SUMMARY + "vs usual" + bell
```

The self re-exec keeps working: bob-cli is still pulled first. The two sibling pulls
move ahead of the bob-cli build. That is safe because the plugin sync uses the
installed `bob` binary only after the build.

### 2. Screens

The mockups use real subjects from today's history. Durations are illustrative.

**A. Typical run (four-hourly cadence) during the bob-cli build**

```text
🚀  INSTALL ALL
────────────────────────────────────────────────
  from     ~/projects/github/bobs-org
  then     restart Obsidian if the plugin sync changes the vault
  $ git pull --ff-only --no-rebase   (in each checkout)
  ⇣ bob-cli          ✓ 3 new commits · e0960045 → b6a96243
  ⇣ bob-plugins      ✓ 2 new commits · 62e6113 → 5fbe82a
  ⇣ bob-mac-capture  ✓ up to date · a2aab30

📰  WHAT'S NEW
────────────────────────────────────────────────
  bob-cli · 3 commits since your last install 2h ago
    feat  gmail       add safe draft create and update flow                b6a96243
    feat  gmail       pull label mail and import attachments               ec39e1a0
    feat  gmail       link captured Gmail URLs without blocking capture    e0960045
                      Add grammar 16 Gmail spans and offline previews, reuse
                      saved-thread links within capture batches, and queue
                      unresolved URLs for a detached single-flight linker after
                      commit. Gate automatic linking through local login
                      receipts, writer selection, and BOB_GMAIL_KICK.

  bob-plugins · 2 commits · will update bob-mail, navigation
    feat  navigation  handle Gmail attachment origins                      5fbe82a
    feat  bob-mail    add Gmail picker and paste integration               f909c04

  ⏱  about 4m 40s · done around 12:44

🦀  BOB-CLI  1/3
────────────────────────────────────────────────
  $ just --justfile ~/projects/github/bobs-org/bob-cli/justfile install
  ⠼ compiling bob-obsidian  ━━━━━━━━━━━━━━━━━━━╸─────────────  1:52 of ~3:40
```

Details:

- The bar's filled part (`━`) uses the step's banner color: 35 for bob-cli, 34 for
  plugins, 32 for mac-capture. The unfilled part (`─`) is dim, echoing the banner
  rules. `╸` gives half-cell resolution.
- The live line contains no emoji. Braille and box-drawing characters are one cell
  wide in kitty and tmux, so redraws and truncation stay correct.
- Durations are `m:ss` while running and `3m 32s` in finished rows, matching
  `format_duration`. Estimates of a minute or more round to 10 s; shorter ones round
  to 5 s.
- The "done around" clock time is printed once and appears again only if it moves
  by a minute or more. It answers "can I go make coffee?" better than a ticking
  countdown.

**B. Live-line states**

```text
  ⠼ updating crates.io index · 0:02
  ⠼ compiling dependencies 87/235  ━━━━━╸───────────────────────  0:41 of ~5:30
  ⠼ compiling bob-obsidian  ━━━━━━━━━━━━━━━━━━━╸─────────────  1:52 of ~3:40
  ⠼ compiling bob-obsidian  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  4:05 · 25s longer than usual
  ⠼ compiling bob-obsidian · 1:52 · first timed build on this machine; next run shows an ETA
  ⠼ waiting for another cargo build to release the build directory · 0:14
  ⠼ building Bob Mac Capture (release)  ━━━━━━━━━━━━╸──────────  0:21 of ~0:45
```

**C. Finished**

```text
🦀  BOB-CLI  1/3
────────────────────────────────────────────────
  $ just --justfile ~/projects/github/bobs-org/bob-cli/justfile install
  ✓ 3 new commits · installed @ b6a96243 · 3m 32s
…
✨  SUMMARY
────────────────────────────────────────────────
  ✓  bob-cli           3 new commits · installed @ b6a96243            3m 32s
  ✓  bob-plugins       2 new commits · bob-mail, navigation updated       4s
  ✓  bob-mac-capture   up to date · installed ~/Applications/…          41s
  ↻  obsidian          restarted · plugins changed                        9s

  ✓  ALL INSTALLED · 4m 31s · about as long as usual (4m 40s)
```

The run ends with a `\a` bell when it took more than 30 s.

**D. Failure.** The run prints the excerpt from the first `error` line to the end,
capped at about 40 lines:

```text
  ✗ build failed after 1:12 · cargo exit 101
      error[E0308]: mismatched types
        --> src/native/gmail/draft.rs:212:17
      …
      error: could not compile `bob-obsidian` (lib) due to 1 previous error
      full log  ~/.local/state/bob-cli/install-all/logs/20261106-123927-bob-cli.log
```

**E. Daily cadence: the digest falls back to the grouped level**

```text
  bob-cli · 41 commits since your last install yesterday
    ⚠ BREAKING  capture  settle close names and retype tasks landing in created entries
                BREAKING CHANGE: a capture #NAME/=name that creates its destination
                entry now retypes the landing task instead of merging the entry name.
    feat  gmail          add safe draft create and update flow
    feat  gmail          pull label mail and import attachments
    feat  stats          add typical day to daily points
    fix   gmail          close transactional save gaps
    fix   task-complete  repair successor verdict contracts and receipts
    + 29 more: feat 21 (gmail 9 · ref 5 · capture 4 · 3 other scopes) · fix 7 · docs 7 · refactor 1
      git -C ~/projects/github/bobs-org/bob-cli log --oneline <from>..b6a96243
```

**F. Not a TTY** (piped, CI, or an agent): no `\r` and no colors under `NO_COLOR`.
Progress lines appear only with `BOB_PROGRESS=1`, matching bob's convention:

```text
bob-cli: compiling bob-obsidian (usually 3m 40s)…
bob-cli: built in 3m 32s
```

### 3. The ETA model

**Steps and phases recorded:**

| Step | Phases (boundary signal) |
| --- | --- |
| bob-cli | `index` (`Updating crates.io index`) → `deps` (other `Compiling` lines) → `crate` (`Compiling bob-obsidian`) → `install` (`Finished` → exit, including `bob completion install`) |
| bob-plugins | one phase (`sync`) |
| bob-mac-capture | `build` (SwiftPM output until the last `Build complete!`) → `install` (sign, verify, swap, restart) |
| obsidian | `restart` (quit → relaunch confirmed) |

**Predicted change kind, decided before the step from local git state only:**

| Kind | bob-cli rule | mac-capture rule |
| --- | --- | --- |
| `noop` | HEAD equals the last installed SHA, the tree is clean, and the binary exists | HEAD equals the last installed SHA |
| `cold` | No `target/local-install` yet, or `rust-toolchain.toml` changed in the range | No `.build/release` yet |
| `deps` | `Cargo.lock` changed in the range | `Package.swift` changed in the range (no `Package.resolved` is tracked) |
| `rebuild` | anything else | anything else |

**Estimator.** Use the median of the last 5 successful samples with the same host,
step, phase, and kind, plus the same `incremental` flag. The flag matters because
agent shells set `CARGO_INCREMENTAL=0`. After a run, a `crate` phase shorter than a
third of the current rebuild estimate is recorded as kind `quick` and excluded from
future rebuild estimates. So the estimate always tracks the slow, common mode, and
fast builds simply finish early. With no samples, there is no estimate.

**Display rules.**

- Step fill = elapsed ÷ (elapsed in finished phases + estimates of remaining
  phases), re-anchored at each phase boundary.
- Fill never goes backwards: if re-anchoring would lower it, it holds until elapsed
  time catches up.
- Fill is clamped to 99% until the step exits.
- Once a step runs past 110% of its estimate, the bar stops filling. The label
  switches to "25s longer than usual", and the "done around" time moves forward.
- Time spent waiting on a Cargo or SwiftPM lock is excluded from phase durations
  and shown as waiting.

**Storage.** Everything lives under the existing state directory,
`${XDG_STATE_HOME:-~/.local/state}/bob-cli/install-all/`, which is per host and
not vault-synced:

- `timings.jsonl`: one line per measured phase:
  `{"v":1,"ts":…,"host":"…","step":"bob-cli","phase":"crate","kind":"rebuild","secs":212.4,"ok":true,"incremental":true}`.
  Lines are appended with a single `O_APPEND` write, malformed lines are ignored,
  and the file is trimmed to the last 500 lines by temp-file-and-rename.
- `installed.json`: per repo, the SHA, time, and dirty flag of the last successful
  install (or sync, for plugins). This drives R3 and the change kind.
- `logs/<stamp>-<step>.log`: the captured output, keeping the last 10 runs.
- `obsidian-restart-pending`: unchanged.

### 4. The "What's new" digest

**Input.** For each repo, the range runs from `installed.json`'s SHA (falling back
to the pre-pull HEAD) to the post-pull HEAD. The digest uses `git log
--first-parent --format=%H%x1f%s%x1f%b` over that range. `git rev-list A..B` copes
with a non-ancestor A after a rewrite. If A no longer exists, the digest falls back
to the pull range and says so. A dirty working tree adds a line: "installing with
uncommitted changes in 3 files".

**Parsing.**

- Subjects match the Conventional Commits pattern `type(scope)!: subject`;
  non-conventional subjects form an "other" group.
- Bodies drop trailers: `SASE_*=`, `[n]: http…`, `Co-Authored-By:`,
  `Signed-off-by:`.
- A `BREAKING CHANGE:` footer is extracted separately.
- Groups and their order mirror `release-plz.toml`: Breaking, Added, Fixed,
  Performance, Reverted, then the rest as one dim count line.

**Layout levels.** The digest picks the richest level at which everything fits the
budget, and applies one level to the whole digest so it looks uniform:

| Level | Per commit | Typical fit |
| --- | --- | --- |
| L4 full | subject + whole body | hourly cadence (≤ ~5 commits) |
| L3 lead | subject + first body paragraph (≤ 4 wrapped lines) | ~4-hourly |
| L2 subjects | one line per commit, newest first within each group | ≤ ~30 commits |
| L1 grouped | breaking commits, then top subjects by group until the budget runs out, then a `+N more` line with counts by type and scope, plus the `git log` command | daily |

**Budget.** The goal is that the whole run, digest included, fits on one screen
when Bryan returns to the terminal.

- The budget is the terminal's rows minus the rows the rest of the run will need:
  roughly 6 for the header and pulls, 1 for the plan, 4 per step section, and
  6 + steps for the summary. That is about 30 rows on the Mac, about 22 on Linux
  (no Mac Capture step).
- The minimum budget is 8 rows.
- Breaking commits always render with their footer, even past the budget, because
  they are the reason to read the digest at all.
- Non-TTY output uses L2 capped at 60 lines.

**Formatting.**

- Each commit line reads `type` (colored: feat green, fix yellow, perf cyan,
  revert magenta, breaking bold red with `⚠ BREAKING`), then the scope (dim,
  aligned within the repo), then the subject (truncated with `…` at the width),
  then a dim short SHA at the right.
- The SHA is dropped first when the line is too narrow.
- Bodies are dim and aligned under the subject.
- For bob-plugins, the repo header names the plugins the dry-run will touch. The
  `--dry-run --format json` output already lists per-plugin `files[].action`.

### 5. Rendering mechanics (where reliability comes from)

- **One writer, one live line.** The helper runs the long command with stdout and
  stderr piped into it. It writes the log and owns exactly one terminal line,
  redrawn every 80 ms with `\r…\033[K`, truncated to `cols − 1` so it can never wrap.
  The cursor is hidden while drawing. A single-line region survives tmux zoom and
  resize: the worst case is one stale partial line. Multi-line live regions do
  not have that property.
- **No invisible prompts.** Captured children get `stdin=/dev/null`, so an
  unexpected prompt fails fast instead of hanging behind the spinner.
  - The one known interactive path is Mac Capture's keychain unlock. `install.sh`
    offers it only when `[[ -t 0 ]]` (lines 167 and 175). So `install_all` first
    runs bob-mac-capture's existing `just signing-check` attached to the TTY, which
    offers the unlock. Only then does it start the captured `just install`.
  - Exit codes 77 and 78 keep today's remedies.
  - Git pulls (SSH prompts) and clone offers stay outside any spinner, exactly as
    today.
  - `bob completion install` never reads stdin (checked in
    `src/native/completion/`).
- **Tool output signals.**
  - Cargo runs with `CARGO_TERM_COLOR=always`, so the log and failure excerpt keep
    colors, and with `CARGO_TERM_PROGRESS_WHEN=always` plus a fixed
    `CARGO_TERM_PROGRESS_WIDTH`. The `n/m` counter is then parseable for the deps
    phase. The helper treats the counter as decoration only, never as the ETA.
  - SwiftPM's `[n/m]` and `Build complete!` lines mark its phases.
- **Signals.** The helper ignores SIGINT itself and waits for the child, which
  receives SIGINT from the terminal's foreground process group. It then clears the
  line, shows the cursor, prints "interrupted after 1:12", and exits 130. Cleanup
  also runs on SIGTERM. SIGWINCH just forces a redraw at the new width.
- **Graceful fallback.** The helper is used only when stdout is a TTY, `python3` is
  on PATH, `TERM` is not `dumb`, and neither `--verbose` nor
  `BOB_INSTALL_VERBOSE=1` is set. Otherwise `install_all` behaves exactly as today.
  A helper crash must never fail an install: the shim falls back to running the
  command directly.
- **Python.** Use the standard library only and stay compatible with Python 3.9,
  which is what macOS Command Line Tools ships. CLT is already required on the Mac,
  because Cargo needs its linker and the Swift build needs Xcode tools. So `python3`
  is always present where this runs. Avoid `match` statements and `X | Y` type
  syntax.
- **Nesting.** The live line wraps the `cargo install` call *inside* the `install`
  recipe, so plain `just install` benefits too (R7). `install_all` passes
  `BOB_INSTALL_ALL=1` so the recipe skips its nested `📦 INSTALL` banner, and passes
  the estimate of the remaining steps so the nested helper can show "done around".

### 6. Alternatives considered

| Option | Verdict | Reason |
| --- | --- | --- |
| Cargo's `n/m` counter as the progress source | Reject | Reads 98% when the one crate that is ~100% of warm-rebuild time starts. |
| A fixed guess with no history | Reject | Off by host speed and by change kind (2.5 s, 30 s, 210 s, 334 s modes). |
| Keep raw output and pin a footer with a DECSTBM scroll region (apt-style) | Reject | Two processes write the TTY; resize handling; a killed run leaves the terminal broken; still noisy. |
| PTY wrapper (`pty.spawn`-style passthrough) | Reject for now | Raw mode, SIGWINCH propagation, and signal forwarding cost a lot; the preflight plus `/dev/null` stdin solves prompts more simply. |
| Multi-line task-list live region (listr or Compose style) | Reject for v1 | Reflow glitches on tmux zoom and resize; the static plan line plus per-step live lines carry the same information. |
| OSC 9;4 native terminal progress | Reject | kitty support is unverified ([termpulse][termpulse], [test-r][test-r], [anstyle-progress][anstyle]). OSC 9 is a *notification* sequence on iTerm2-style terminals, so it risks notification spam; Cargo gates it on an allowlist ([cargo#16730][cargo16730]); tmux sits in between. |
| A tmux status-bar segment | Reject | Couples the installer to dotfiles; the bell already marks the window. |
| Rewrite `install_all` in Python or Rust | Reject | The 827 lines encode hard-won edge cases: keychain exits 72/77/78, the restart marker, the self re-exec, clone offers. |
| A hidden `bob` subcommand renders progress | Reject | Bootstrapping (no `bob` on first install, the binary replaced mid-run) and a hidden CLI contract that exists only for its own installer. |
| `opt-level=1` for `local-install` | Reject | −12% (210 → 184 s) for slower binaries. |
| Split the 667k-line crate | Out of scope | The only structural lever on the ~90–110 s serial frontend; a large refactor. |
| Download CI-built binaries for HEAD | Not now | CI builds release binaries only for the daily train. Per-SHA artifacts add CI cost, and installs often happen minutes after a push, before CI finishes. |
| Overlap a Swift prebuild with the Rust build on macOS | Phase 3 | While rustc's frontend runs largely serially, cores sit idle. A prebuild makes the later `just install` a SwiftPM no-op. It needs a `just prebuild` recipe owned by bob-mac-capture and Mac measurements, and concurrent runs get their own history kind. |

## Implementation plan

**Phase 1: core (bob-cli; bob-mac-capture is only wrapped, not changed)**

1. `scripts/lib/install_all_ui.py` (stdlib, Python 3.9) with three subcommands:
   - `run --step S --repo PATH --parser cargo|swiftpm --log … -- CMD…`: the live
     line, phase detection, a timings record, and the failure excerpt.
   - `estimate --step S --repo PATH …`: predicted kind and seconds per step, plus
     the plan line.
   - `digest --repo NAME=PATH:FROM:TO … [--rows N --cols M]`: the What's new
     section.
2. `scripts/lib/test_install_all_ui.py` (unittest), run from `just check-scripts`:
   - estimator: median, kinds, `quick` exclusion, no history, overtime;
   - cargo and SwiftPM parsers, using captured fixtures that include `\r` progress
     frames and lock waits;
   - trailer stripping, Conventional Commit parsing (`!`, `BREAKING CHANGE:`,
     non-conventional subjects);
   - golden layouts at 80 and 120 columns for each level;
   - the renderer with a fake clock and a fake terminal.
3. `justfile` `install`: route the cargo call through a tiny shim that uses the
   helper when eligible and records `installed.json` on success. Skip the nested
   banner under `BOB_INSTALL_ALL=1`.
4. `scripts/install_all`:
   - pull all three repos first, then the digest and the plan line;
   - run `just signing-check` attached to the TTY, then the wrapped mac-capture
     `just install`;
   - record plugin and Mac Capture installs in `installed.json`;
   - add "vs usual" to the summary and the bell;
   - add `-v/--verbose` (short alias per `cli_rules.md`), with `install-all
     *args` passing arguments through.
   - Extend the existing fake-binary test style (`scripts/test_install_migration`)
     into an end-to-end test that drives `install_all` under `script -q` with fake
     `git`, `cargo`, and `just`.
5. Docs:
   - Update `docs/guides/install-everything.md`, whose sample output is already
     stale, and the `just install` notes in `docs/start/install.md`.
   - Follow `sase/memory/docs.md`: behavior change goes to the guide steps it made
     incorrect.

**Phase 2: polish.** A spinner on the Obsidian quit/relaunch wait. Name the plugins
updated in the summary. Optionally `install-all --whats-new` to preview the digest
of `HEAD..@{upstream}` after a fetch, without installing.

**Phase 3: speed (measure on the Mac first).** Concurrent Swift prebuild via a new
bob-mac-capture `just prebuild` recipe. Skip the Mac Capture reinstall (and its
app restart) when its kind is `noop`.

**Manual acceptance on the Mac:**

- Run twice: the first run learns, the second shows an ETA.
- Press Ctrl-C mid-build.
- Toggle tmux zoom mid-build.
- Run with `NO_COLOR=1` and with `| cat`.
- Run with a locked login keychain (the preflight should prompt; the build should
  never hang).
- Run after a manual `git pull`: the digest should still list the new commits.

Estimated size: about 400–500 lines of Python plus about 300 lines of tests, and
about 150 changed lines of bash and just.

## Open questions for Bryan

1. **Cadence.** Do you usually run this hourly, or once or twice a day? This only
   tunes the default level and the budget reserve; the design handles both.
2. **Should `docs`, `test`, and `refactor` commits appear?** I propose one dim count
   line, matching the release notes, which skip them.
3. **Python helper.** Is a stdlib Python helper acceptable in `scripts/lib/`? The
   repo already uses Python for `tools/release` and `scripts/dev`.
4. **Bell.** Is a bell after runs over 30 s welcome, or would you prefer a macOS
   notification (like the existing Obsidian banners) for runs over 2 minutes?
5. **`$` lines.** Keep echoing `$ …` command lines in the default view? I kept them:
   they are dim, single-line, and copy-pasteable for a retry.

## Recommended solution

Keep `scripts/install_all` as the bash orchestrator and change three things:

1. **Pull first, then show a digest.** Pull all three repos before building. Print a
   **budgeted "What's new" digest** covering commits since the last successful
   install of each repo on this host:
   - layout levels: full → lead paragraph → subjects → grouped, picking the richest
     that fits the screen;
   - SASE trailers stripped; `release-plz.toml` change-type groups;
   - breaking changes always shown with their `BREAKING CHANGE:` text.

   Follow it with a one-line plan: "about 4m 40s · done around 12:44".
2. **Replace raw build output with one live line per long step.** The line shows a
   Braille spinner, the current activity, and a time-based bar against a
   **per-host, per-change-kind median of past runs**, with overtime handling. With
   no history it shows elapsed time and says the next run will have an ETA. Build
   output goes to a log, an error excerpt prints on failure, and `-v/--verbose`
   restores today's raw stream. The same line wraps plain `just install`.
3. **Finish with context and a signal.** Show "4m 31s · about as long as usual" in
   the summary and ring the bell.

Put the presentation logic in one tested, stdlib-only Python 3.9 helper
(`scripts/lib/install_all_ui.py`) behind a fallback shim, so the installer degrades
to today's behavior and never fails because of the UI.

- Prevent hidden prompts with a TTY `signing-check` preflight and `/dev/null` stdin
  for captured steps.
- Skip OSC 9;4, multi-line live regions, PTYs, and rewrites.
- Treat speed as a later, measured phase: a concurrent Swift prebuild on macOS
  first. Profile tweaks are not worth it, and crate splitting is the only
  structural lever.

## Appendix: method and raw data

- Timing builds: `cargo build --profile local-install --locked --timings` in a
  dedicated `CARGO_TARGET_DIR`. Lib sections (frontend and codegen) come from the
  `UNIT_DATA` JSON embedded in each `cargo-timing.html`. Deltas came from checking
  out `master~1` and `master~6` and returning to `master`; the workspace was
  restored clean to `master` afterwards.
- Load average during the runs ranged 12.6–29.6 on 16 cores (peer researchers were
  building at the same time). Expect lower absolute numbers on an idle machine.
- Commit-volume figures come from first-parent `git log --since="21 days ago"`,
  bucketed into fixed windows. Message-shape figures come from `git log -300` with
  trailers stripped by regex.
- Measurements not taken: Swift build times (Linux host), and Mac rustc times. The
  design learns both per host.
- Side observations for the lead:
  - `docs/guides/install-everything.md`'s sample output no longer matches the real
    rows.
  - SASE agent shells export `CARGO_INCREMENTAL=0`, which silently disables the
    `local-install` profile's incremental setting for agent-run installs and
    benchmarks.

[termpulse]: https://docs.rs/crate/termpulse/latest/source/src/detect.rs
[test-r]: https://docs.rs/crate/test-r-core/latest/source/src/output/term_progress.rs
[anstyle]: https://docs.rs/crate/anstyle-progress/latest/source/src/query.rs
[cargo16730]: https://github.com/rust-lang/cargo/pull/16730
