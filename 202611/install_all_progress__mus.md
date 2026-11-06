# `just install-all`: progress, ETA, and commit digest — research & recommended design

Researcher: mus. Date: 2026-11-06.
Scope: the "frozen screen for several minutes" experience in the
`~/tmp/screenshots/20261106_123927.png` screenshot, and Bryan's two asks:
(1) progress indication + ETA (only if a previous run exists on that machine),
(2) a better summary of newly-pulled commits, including the bob-plugins step,
with full messages when they fit on screen. Lead the design: intuitive,
reliable, beautiful.

## 1. What the screenshot actually shows (diagnosis)

The screenshot is mid-step-1/3 on a Mac (`tm sase`, `bob-cli on master`,
`just install-all`, ~2m elapsed per the shell prompt's `took 2m1s` from a
prior run):

- `INSTALL ALL` header, then `BOB-CLI 1/3`: one `git pull` line
  (`1 new commit · e0960045 → ec39e1a0`), then `just install`, then the
  nested `INSTALL` banner from the `just install` recipe.
- Cargo's own progress is visible and working:
  `Building [========================> ] 253/258: bob-obsidian`.
  The screen is not truly frozen — cargo rewrites that line in place.

So the pain is not missing output. It is missing **framing**:

1. No statement of the plan up front (3 steps + Obsidian restart, which of
   them will actually take minutes on this machine).
2. No position ("step 1 of 3") once the nested `INSTALL` banner scrolls the
   `1/3` title away — the visible banner just says `INSTALL`.
3. No time expectation: cargo's `253/258` is a *unit* counter, not a time
   counter, and the last 5 units (linking `bob-obsidian`, installing shims,
   building completions) can take longer than the first 253. A user cannot
   map it to wall-clock time.
4. The `git pull` line reports *one* new commit but says nothing about what
   it contains — and the bob-plugins step (step 2/3) reports even less: only
   `N new commits · sha → sha` in `pull_detail`, with no message text at all
   (`scripts/install_all`, `plugin_step`).

Conclusion: the fix is **framing around the existing output**, not replacing
cargo's output. Any design that swallows or interleaves with cargo's stderr
progress bar risks making things worse (garbled carriage-return lines,
lost compiler errors). Keep cargo's stream intact and add: a plan header, a
persistent position indicator, a history-based ETA, and a commit digest.

## 2. Current implementation (verified in tree)

All references are to `scripts/install_all` (~827 lines) unless noted.

- **Steps and order**: header → `offer_missing_clones` (interactive only) →
  `BOB-CLI 1/3` (self `pull_repo` + `just install` ≈ `cargo install --path .
  --profile local-install`) → `BOB-PLUGINS 2/3` (`pull_repo` + `bob plugins
  sync` twice: `--dry-run --format json` preview, then real sync, then
  `plugins list --format json` verify) → `BOB-MAC-CAPTURE 3/3` (macOS only;
  `pull_repo` + `just install` in that repo) → `OBSIDIAN` (restart iff
  `PLUGINS_CHANGED==1` or a restart-marker file exists) → `SUMMARY`
  (`print_summary`: per-step glyph + detail + duration, then total).
- **Timing today**: `SECONDS`-based per-step durations via
  `format_duration` (`%ss` / `%dm %02ds`), shown only in the final summary.
  No persistence: every run starts with no knowledge of past runs. The
  self-pull re-exec path (`PULL_STATE == updated` → re-exec with
  `BOB_INSTALL_ALL_*` env passthrough, including `BOB_INSTALL_ALL_ELAPSED`)
  exists so the just-rebuilt `install_all` script itself runs the install;
  any timing/history design must survive that exec (env passthrough or a
  state file written before exec).
- **State dir precedent**: restart marker lives at
  `${XDG_STATE_HOME:-$HOME/.local/state}/bob-cli/install-all/obsidian-restart-pending`.
  A history file in that same directory follows the existing convention and
  needs no new path plumbing.
- **Styling contract**: `banner` (icon + bold color title + 48-char rule,
  kept in sync with the justfile `_banner`), `command_line` (dim `$ ...`
  echo), `glyph_line` (✓ green / ⚠ yellow / ✗ red / ↻ cyan / – dim),
  `dim_diagnostics` for sub-command output, `NO_COLOR` + non-TTY fallback
  throughout. Any new UI must reuse these four helpers — that is what makes
  it look like it belongs.
- **Where the minutes go** (measured structure, not a benchmark): pulls are
  seconds; `bob plugins sync` is seconds; Obsidian restart is ~seconds plus
  user interruption. The minutes are `cargo install` in step 1 (compile
  `bob-obsidian` + deps; the `local-install` incremental profile helps
  repeat runs but a changed `bob_cli` crate still recompiles) and, on macOS,
  the `bob-mac-capture` `just install` (Swift build). So per-step history
  has a clean bimodal shape: fast steps with low variance, build steps with
  high variance. ETA design must not let build-step variance poison the
  fast steps — i.e. track history **per step**, never as one global total.

## 3. Critique of the plan

**Yes, this is a good idea.** It targets the highest-frequency boring wait
in Bryan's loop (the daily release train means `install-all` runs often and
almost always pulls *something*), and both asks are information the script
already has or can cheaply obtain. Risk is low: output-only changes to a
script whose failure semantics (exit codes, `FAILURES`/`WARNINGS` counts,
restart marker) need not change.

Adjustments and cautions:

1. **The "only if ever run" condition is correct — keep it, and extend it.**
   First run on a machine must show *position + elapsed*, never a fabricated
   ETA. I would go further: per-step ETA only for steps with history; a step
   never timed on this machine shows `~?` / no estimate while other steps
   show theirs. A global "you've never run this" gate would hide useful
   bob-plugins history from a user who has run steps 1–2 but always skipped
   step 3 (Linux users never run it).
2. **Do not try to make cargo's progress bar time-accurate.** Cargo reports
   completed/total *units*; remaining units are not uniform (codegen + link
   dominate the tail). Smoothing cargo's counter into a fake time-ETA is the
   most likely way to look *less* reliable ("it said 10s for 3 minutes").
   Use cargo's bar as-is for within-step liveness; use history only for the
   step-level ETA ("step 1 usually takes ~2m30; 1m10 elapsed").
3. **The commit digest must cover step 2, not just step 1.** Today the
   plugins pull detail is commit-count-only with no message path
   (`pull_detail_for_summary` returns the same `N new commits` string; the
   SHAs are captured in `PULL_DETAIL` but `old_sha`/`new_sha` are locals of
   `pull_repo` and discarded). The request explicitly includes the plugins
   step — plumbing the SHA range out of `pull_repo`/`fresh_clone_result` is
   required work, not polish.
4. **"Full messages if they all fit on one screen" needs a precise
   definition of "fit".** Screen height is knowable (`tput lines` /
   `$LINES`, default 24 when unknown), but the digest competes with output
   already on screen (cargo spew, ends scrolled off). The only sane
   definition: fit within the *remaining* viewport budget the script
   reserves for the digest section, computed at render time, with a hard cap
   (e.g. digest section ≤ 60% of `$LINES`). Anything beyond degrades to
   short lines + a pointer command (`git -C <dir> log a..b`). Never page
   (`less`) mid-install: it breaks non-interactive runs and the re-exec
   path.
5. **Beware scope creep into a TUI.** No cursor-addressing, no
   multi-line-progress redraw, no background spinner threads in bash. The
   script's output is also consumed piped/redirected (logs, SASE agent
   transcripts); every new element must degrade to plain sequential lines.
   A single-line `stderr` heartbeat ("still building bob-obsidian… 1m40
   elapsed, ~2m30 usual") on a timer is the maximum liveness affordance
   I'd accept, and even that is optional (see recommendation).

## 4. Design options considered

| Option | Sketch | Verdict |
|---|---|---|
| A. Plan header + per-step history ETA + digest section (bash, sequential output) | Header lists steps with last-run durations; each step banner gains `(step i/3 · ~2m last time)`; digest rendered per-step inline + consolidated in SUMMARY | **Recommended.** No new deps, survives re-exec, degrades cleanly. |
| B. Live progress bar wrapping cargo | Parse cargo's `[==>] n/m` stderr, render `install-all 40% · ~1m left` | Rejected. Fragile parsing of human output; unit≠time lies; risks garbling errors. |
| C. Heartbeat ticker during long steps | `sleep 30` loop printing elapsed-vs-usual to stderr while `cargo install` runs | Optional add-on to A, off by default or 60s cadence. Cheap but interleaves with cargo lines; keep minimal. |
| D. Rewrite `install_all` in Rust (a `bob install-all` subcommand) | Full control: progress rendering, JSON history, terminal handling | Rejected for this task. Large port of gnarly shell logic (osascript restart dance, clone offers, re-exec); bash is fine for sequential framing. Revisit only if interactive widgets are ever wanted. |
| E. Per-commit full bodies always | `git log` full format for every new commit | Rejected. Daily-train days can pull 5–15 commits with SASE trailers; blows past one screen. Fit-gated (option A) is the request's own instinct and it's right. |

## 5. Recommended solution

### 5.1 History + ETA

- **Store**: append-only JSONL at
  `${XDG_STATE_HOME:-$HOME/.local/state}/bob-cli/install-all/history.jsonl`,
  one record per run: `{ts, host, step, secs, result}` for steps
  `bob-cli`, `bob-plugins`, `bob-mac-capture` (+ `total`). Append at SUMMARY
  time (post re-exec, so exactly one write per run); best-effort (`|| true`)
  — history must never fail an install. Cap file (e.g. keep last 50 lines
  via tail-rewrite) so it can't grow unboundedly.
- **Estimate**: per step, median of last ≤5 records *from this host*
  (host field guards shared `$HOME`/NFS weirdness). Display `~2m30` when
  history exists; `~?` (no estimate) otherwise. Remaining-total ETA in the
  header = sum of medians of steps not yet run. Round to 5–10s; never show
  seconds-level false precision on minute-scale estimates
  (`~2m30`, not `~2m37`).
- **Header** gains a plan with memory, e.g.:
  `steps  bob-cli (~2m30) → bob-plugins (~10s) → obsidian restart if changed`
  plus `(based on N runs on this machine)` or `(first run here — showing
  elapsed only)` when cold. Each step banner gains a suffix:
  `BOB-CLI 1/3 · ~2m30 last time · 0s elapsed` is overkill; prefer
  `BOB-CLI  1/3 · usually ~2m30` on the banner and one elapsed line only if
  the step exceeds its median ("…still going · 3m10 elapsed · usually
  ~2m30" printed when the step crosses median+30s — a single line, not a
  ticker).
- **Overwrite rule**: never rewrite history on failed/cancelled steps beyond
  recording `result`; exclude `fail` records from medians (a failed 8s
  compile must not drag the ETA down).

### 5.2 Commit digest ("WHAT'S NEW")

- **Plumb the range**: have `pull_repo` also export `PULL_OLD`/`PULL_NEW`
  SHAs (and `fresh_clone_result` export the clone SHA as `PULL_NEW` with
  `PULL_OLD` empty). This is the one functional change; everything else is
  rendering.
- **Per-step inline**: after each `show_pull_result` with
  `PULL_STATE=updated`, print a dim digest block:
  - 1 commit → full message (`git log -1 --format=medium`) — subject,
    author/date one-liner, body, no patches. Almost always fits; this is the
    screenshot's exact case and deserves the royal treatment.
  - 2–7 commits → one `%h %s` line each (dim), full bodies withheld.
  - 8+ commits → first 7 short lines + `…and N more (git -C <dir> log
    <old>..<new> --stat)`.
  - `cloned` → `fresh checkout @ <sha>` + subject line of HEAD only.
    `current`/`warn`/`none` → no digest (nothing new / nothing known).
- **Consolidated section**: in/after SUMMARY, a `WHAT'S NEW` banner listing
  per-repo digests together (repos with updates only; "bob-plugins: no new
  commits" one-liners for the rest keep it scannable). Fit-gating applies to
  the *section*: budget = `min(needed, LINES*0.6)`; when over budget, prefer
  complete short-lines for all repos over full bodies for one (breadth beats
  depth in a summary). Bodies wrap at terminal width; strip SASE trailer
  lines (`SASE_BEAD`, `[1]:` link refs) from digest display — they're noise
  here; the SHA already links to the full message via the pointer command.
- **Width/height detection**: `${LINES:-$(tput lines 2>/dev/null || echo
  24)}`; never fail when unknown. All digest output through existing
  `dim_diagnostics`-style dimming so it reads as annotation, not as steps.

### 5.3 Liveness during the long build (small, optional)

- Keep cargo's output untouched (it *is* the within-step progress).
- After printing the step banner, print the command echo as today
  (`command_line`), so a silent tail still shows *what* is running.
- Optional: if a step exceeds its historical median by >60s, print one dim
  line: `still running <cmd> · <elapsed> elapsed · usually ~<median>`.
  Single line, once per step, to stderr-safe stdout — no ticker threads.

### 5.4 Reliability notes (must-haves, not nice-to-haves)

- Non-TTY / piped / `NO_COLOR`: all new lines are plain sequential text;
  no carriage returns, no ANSI-gated logic beyond existing `use_color`.
- Re-exec safety: history write happens once at SUMMARY; step timings use
  the existing `SECONDS`/`BOB_INSTALL_ALL_ELAPSED` passthrough unchanged.
- Copy-pasteable pointer commands use `display_path` like everything else.
- Tests: extend `scripts/test_install_migration`-style coverage or add a
  `test_install_all_digest` harness: (a) digest tiering with fake repos
  (1/3/10 new commits), (b) `LINES=5` tiny-screen fallback, (c) cold-history
  header, (d) history write is best-effort under read-only
  `XDG_STATE_HOME`. Pure-bash `bash -n` gate already covers syntax.

### 5.5 What changes for the screenshot's scenario

Before: silent cargo tail, no position, no ETA, `1 new commit` with no
content. After (warm history): header says
`bob-cli (~2m30) → bob-plugins (~10s) → mac-capture skipped (Linux)` +
`~2m40 total`; `BOB-CLI 1/3 · usually ~2m30` banner; cargo output as today;
inline digest shows the full `e0960045..ec39e1a0` message (1 commit ⇒ full
body, trailers stripped); SUMMARY repeats per-step durations as today plus
`total ~2m10 (usual ~2m40)`. Cold machine: same minus estimates, with
`(first run here — showing elapsed only)`.

## 6. Effort sketch

Small: ~100–150 lines of bash in `scripts/install_all` (history
read/write/median in awk-free shell, SHA plumb, digest renderer, header
lines) + a test harness. No new dependencies, no contract changes, no
justfile changes beyond what's already echoed. The SHA plumb (`PULL_OLD` /
`PULL_NEW`) is the only behavioral seam; the rest is additive output.
