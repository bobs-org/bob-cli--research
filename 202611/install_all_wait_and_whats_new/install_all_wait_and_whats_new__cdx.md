# An installer worth waiting for: progress, honest estimates, and readable changes

Independent research by **cdx**, 2026-11-06.

## Decision in brief

This is a good improvement. The principal problem is uncertainty during the wait, followed by poor visibility into what changed. A percentage bar alone would not solve either problem.

I recommend an **inline terminal transcript with one live status line**, explicit installation phases, elapsed time on every build, and an approximate remaining-time range only when comparable local history supports it. Print readable commit notes immediately after each successful pull, so there is something useful to read during compilation. Finish with a compact receipt that distinguishes source updates, installation, plugin deployment, and application restart. Preserve full messages and diagnostics in local files.

Keep the current sequential installation behavior. Use a small optional Python standard-library presentation helper alongside the existing Bash orchestration; retain a usable Bash/plain-output fallback. Add explicit build boundaries to Mac Capture's shell scripts so the presenter never competes with a keychain password prompt. Do not introduce a full-screen TUI, an LLM-generated changelog, or a build-percentage prediction system.

## Scope and evidence

I inspected the supplied screenshot, the current installer, its recipes and documentation, the linked Mac Capture installer and bundler, and recent commit messages from all three product repositories. I did not read another swarm researcher's report, transcript, or findings. No installs, pulls through the product installer, benchmarks of actual builds, signing operations, or vault mutations were performed.

The research checkout opener refreshed the linked product checkouts. Source observations below are pinned to these revisions; timing examples later in this report are illustrative, not measured on Bryan's Mac.

| Repository | Revision inspected | Relevant sources |
|---|---|---|
| bob-cli | `b6a962435aa73b8a06d1fe654ebcf1f58caa3658` | `scripts/install_all`, `justfile`, `Cargo.toml`, `scripts/lib/bob_shell.sh`, `docs/guides/install-everything.md` |
| bob-mac-capture | `a2aab306821f0dde7bb2c37b6edc11338b16e7d8` | `Scripts/install.sh`, `Scripts/bundle.sh`, `justfile` |
| bob-plugins | `5fbe82a96836b8b54c2424738b7e63831c15e033` | Recent Git history and repository instructions; deployment is orchestrated by bob-cli |

The supplied `~/tmp/screenshots/20261106_123927.png` shows `BOB-CLI 1/3`, a count and SHA range for one pulled commit, then Cargo at `253/258: bob-obsidian`. It lacks elapsed time and a useful indication of the remaining wait. The apparent proximity to the end of the task count is especially unfortunate: completing compilation units is not equivalent to completing an equal proportion of elapsed build time. The screenshot cannot establish whether that particular wait is compilation, linking, a resource bottleneck, or a hang.

### Existing behavior that constrains the design

1. **The outer installer is already responsible for presentation.** It prints banners, pulls each repo, records component durations, and finishes with four rows: CLI, plugins, Mac Capture, Obsidian. It should remain the authority for the final outcome. [Installer source](https://github.com/bobs-org/bob-cli/blob/b6a962435aa73b8a06d1fe654ebcf1f58caa3658/scripts/install_all#L177)
2. **CLI self-update re-executes the installer.** `pull_repo` currently captures short SHAs and formats a human-readable count/range. On an update, environment variables carry that text and elapsed time across `exec`. Structured before/after revisions, history collection, and a run identifier must survive this handoff without duplication. [Pull handling](https://github.com/bobs-org/bob-cli/blob/b6a962435aa73b8a06d1fe654ebcf1f58caa3658/scripts/install_all#L219), [re-exec](https://github.com/bobs-org/bob-cli/blob/b6a962435aa73b8a06d1fe654ebcf1f58caa3658/scripts/install_all#L766)
3. **CLI installation already uses an incremental profile.** The recipe clears `RUSTC_WRAPPER`, runs `cargo install --path . --locked --profile local-install`, then installs completions. `local-install` inherits release optimization and enables incremental compilation. This proposal should preserve that existing speed improvement. [Recipe](https://github.com/bobs-org/bob-cli/blob/b6a962435aa73b8a06d1fe654ebcf1f58caa3658/justfile#L129), [profile](https://github.com/bobs-org/bob-cli/blob/b6a962435aa73b8a06d1fe654ebcf1f58caa3658/Cargo.toml#L106)
4. **Plugin source updates and deployment are separate.** The installer pulls the sibling, previews sync, deploys through `bob plugins sync --no-pull --repo`, and verifies sync counts. Some vault files can remain drifted. New repository commits must not be described as fully deployed when drift remains. Documentation-only commits can also produce no copied plugin files. [Plugin step](https://github.com/bobs-org/bob-cli/blob/b6a962435aa73b8a06d1fe654ebcf1f58caa3658/scripts/install_all#L355)
5. **Mac installation includes interactive and transactional work.** It checks signing access, may invoke `security unlock-keychain`, builds the app, signs it, builds an installation helper, verifies and swaps the bundle, and hands off a previously running instance. Its restart-warning status differs from installation failure. A wrapper that blindly hides all output would be dangerous to usability here. [Signing](https://github.com/bobs-org/bob-mac-capture/blob/a2aab306821f0dde7bb2c37b6edc11338b16e7d8/Scripts/install.sh#L156), [build and installation](https://github.com/bobs-org/bob-mac-capture/blob/a2aab306821f0dde7bb2c37b6edc11338b16e7d8/Scripts/install.sh#L332)
6. **The script is deliberately tolerant of some failures.** Pull failure warns and uses the local checkout; later component steps still run after an earlier install failure; plugin restart has a pending marker. The presentation work should not silently change those policies. [Installer guide](https://github.com/bobs-org/bob-cli/blob/b6a962435aa73b8a06d1fe654ebcf1f58caa3658/docs/guides/install-everything.md)

### A small commit-message study

I read the latest 30 messages from each product repository using `git log -30 --format=%B`. I estimated rows by wrapping each line to 72 characters and compared the whole message with the text preceding the first newline followed by `SASE_`. This is a descriptive sizing experiment, not the proposed production filtering algorithm; character wrapping also differs from terminal cell wrapping for some Unicode text.

| Repository | Messages containing SASE metadata | Median full-message rows | Median rows before SASE metadata | Largest full message |
|---|---:|---:|---:|---:|
| bob-cli | 30/30 | 11 | 1 | 26 rows |
| bob-plugins | 30/30 | 11 | 1 | 29 rows |
| bob-mac-capture | 28/30 | 11 | 1 | 27 rows |

In this sample, a single ordinary message can consume half a small terminal primarily with agent/bead references. The user-facing default should therefore favor subjects and useful prose. Full original messages should remain available, but “fits on the screen” alone is an insufficient editorial rule.

## What the external evidence supports

The CLI Guidelines recommend timely feedback for long commands, useful progress, restrained output, and terminal-aware presentation. NN/g warns that a bar that moves quickly and stalls near completion can undermine trust; its alternatives include coarse time estimates and named steps. These support a modest live indicator plus real phase information here. They do not establish that we can predict this build accurately. [CLI Guidelines](https://clig.dev/#robustness), [NN/g progress guidance](https://www.nngroup.com/articles/progress-indicators/)

Cargo supports structured messages for diagnostics, artifacts, and build completion, but those messages do not provide a universal percentage-of-wall-time contract. They can improve diagnostics and identify cached artifacts later. The installed command's exit remains authoritative, since build completion is only part of installation. [Cargo external-tool protocol](https://doc.rust-lang.org/cargo/reference/external-tools.html)

Cargo's `--timings` produces a report after the build; it is useful for investigating actual speed, not as an immediate live ETA interface. Its `--path` install also uses the local workspace target directory by default, which makes cache state relevant to repeated durations. [Cargo install reference](https://doc.rust-lang.org/cargo/commands/cargo-install.html)

The remaining design rules, thresholds, and layouts in this report are my recommendations. They need fixture tests and real Mac trials; they are not claimed as externally validated constants.

## Adjustments to the request

| Requested direction | Recommended adjustment | Why |
|---|---|---|
| Progress indication | Show phase, elapsed time, and process activity; do not claim a build percentage. | Task counts and elapsed-time fractions are not reliable fractions of completed work. |
| ETA after a previous run on that machine | Require comparable successful history, not merely any previous invocation. One comparable run shows “last time,” not a countdown. | A cold build, a no-op reinstall, and a release rebuild are different workloads. |
| One or more full messages if they fit | Default to commit notes with narrowly recognized automation metadata folded away; retain the complete original messages in a file. | Most sampled bodies are dominated by provenance rather than changes useful to the installer user. |
| One screen | Budget the final receipt and each component's change preview; let diagnostics and required actions exceed the budget when necessary. | Hiding failure information to meet a layout target would make the experience worse. |
| General installer improvement | Preserve sequencing and install semantics in the first implementation. | Parallel compilation, skipping work, and switching to binary releases are separate changes with different correctness risks. |
| Implementation choice | Use optional Python 3 for the enhanced presentation, with existing-dependency Bash fallback. | JSON history, sizing, timing, and pipe draining are awkward to maintain entirely in Bash; the source installer should still bootstrap without Python. |

## The proposed experience

### During a successful CLI build

The following is a layout example, not a recording. Only the last line changes. The commit body here is invented to illustrate spacing.

```text
Install Bob
CLI → Plugins → Mac Capture → Obsidian

1/3  bob-cli
     Pulled 2 commits · a10cb42 → b42c65d

     feat(capture): improve duplicate-task suggestions
       Show related tasks after typing settles.
     fix(cli): preserve completion settings on reinstall

  ⠋  Building CLI · 1m 24s elapsed · about 1–2m left
```

After success, replace the live line with a permanent outcome such as `✓ CLI installed · 2m 48s`. Then append the next component heading. Do not repaint the commit text, clear the screen, enter an alternate screen buffer, or pin a multirow dashboard over scrollback.

The three component ordinal labels mean ordering, not equal time shares. Obsidian is an explicit finishing action, rather than an invisible extra operation after “3/3.” Omit unavailable components from an optional startup path preview, while keeping an explicit skip in the receipt.

### First run and uncertain estimates

```text
  ⠋  Building CLI · 1m 24s elapsed · learning this build's duration
```

A returning machine with one comparable successful build gets context without false precision:

```text
  ⠋  Building CLI · 1m 24s elapsed · last similar build: 3m 40s
```

After an estimate has been exceeded:

```text
  ⠋  Building CLI · 6m 10s elapsed · taking longer than usual
```

Do not leave `0s remaining`, freeze a bar at 99%, or indefinitely add another 30 seconds. The animation means the supervisor is responsive and the child has not exited; it does not prove compiler progress. After a configurable long quiet interval, a factual secondary message can say `No new build output for 2m; process is still running`. Do not infer a deadlock or kill the compiler from silence.

### Mac signing and installation

Use explicit phases: checking signing access, building app, signing bundle, building install helper, installing/verifying, restarting the existing app.

When the signing check needs input, stop the live renderer before printing the prompt and give the original command the terminal. Display `Waiting for keychain unlock` only when that state is actually known. A keychain operation can also cause a GUI prompt, so show a static signing/access explanation before starting that operation; do not pretend to know whether the user is currently reading a dialog.

Exclude explicit input-wait time from learned build durations. Never record passwords, feed keyboard input through the progress UI, or replace the existing signing remediation with generic “installation failed.”

### Final receipt

Illustrative successful layout:

```text
Installed · 6m 42s

  ✓  CLI          installed b42c65d                       2m 48s
  ✓  Plugins      4 files copied · 21/21 in sync              5s
  ✓  Mac Capture  installed and restarted                 3m 46s
  ✓  Obsidian     restarted                                   3s

Changes pulled · 4 commits across 3 repositories
  CLI          feat(capture): improve duplicate-task suggestions
               fix(cli): preserve completion settings on reinstall
  Plugins      fix(cards): keep the selected task visible
  Mac Capture  fix(panel): restore focus after reopening

Full commit messages: ~/.local/state/bob-cli/install-all/runs/…/changes.txt
Build logs:           ~/.local/state/bob-cli/install-all/runs/…/
```

A failed installation must instead say, for example, `CLI source updated; installation failed`. A plugin warning must report copied files and remaining drift separately. If the verified Mac app installed but its restart failed, say `installed; restart needed`, preserving the existing warning behavior. Use the receipt's existing actionable details; do not collapse these outcomes into a universal green check.

### Visual rules

- Use a restrained accent for the current component, green for success, amber for warnings, and red for failures. Status text must carry the meaning without color.
- Keep labels aligned and changes left aligned. Avoid a giant border, repeated full-width banners, competing spinners, or a colorful line for every underlying command.
- Animate a small glyph at about 4 Hz; update elapsed time at 1 Hz and estimates no faster than roughly every 10 seconds. Fast steps finish without an elaborate animation.
- Size to the actual output terminal, including a tmux pane. At narrow widths, drop the estimate first and wrap stable prose. The live line must never reach the terminal's autowrap column.
- Use an ASCII spinner and status words for terminals/locales where glyph widths are uncertain. Keep existing `NO_COLOR` behavior; animation control is separate from color control.
- Put progress on stderr. In automatic mode, prefer plain output if the overall invocation is redirected, even if one stream remains attached to a terminal. `TERM=dumb`, non-TTY output, and explicit plain mode get no cursor escapes.
- Plain mode emits phase start/end lines and an occasional heartbeat, approximately every 30 seconds during otherwise silent work. It must remain useful in CI, a captured log, and a screen reader.

## Estimation: useful history without pretending to know the future

### Store the right measurements

Use `${XDG_STATE_HOME:-$HOME/.local/state}/bob-cli/install-all/`, beside the current restart marker. Keep records out of Git and the vault. XDG explicitly places persistent logs and action history in state storage. If a configured state path is relative, ignore it in favor of the default rather than writing relative to a checkout. [XDG Base Directory Specification](https://specifications.freedesktop.org/basedir/latest/)

Store versioned, per-run records with phase boundaries, outcome, elapsed duration, revision context, and a small workload fingerprint. Separate the displayed whole-run duration from durations used to predict build work. Write run records atomically, then derive a bounded history from them. A corrupt or unwritable history file removes estimates; it must not prevent installation.

Recommended matching inputs:

| Input | Treatment |
|---|---|
| Machine/install scope | Local state plus a machine identity discriminator if home/state can be synchronized. Do not reuse a copied Mac history on Linux. |
| Component and phase | CLI build, Mac app build, helper build, and non-build work are distinct. |
| Toolchain and target | Rust or Swift compiler version; architecture/target; selected SDK/toolchain for Mac. |
| Configuration | Cargo profile, relevant build flags and jobs setting; Swift configuration; fingerprint relevant recipe behavior. |
| Cache scope | Actual effective target/build directory and whether usable cache is known absent, present, or unknown. Do not assume `target/` if configuration redirects it. |
| Workload context | Dependency/manifest changes versus ordinary source changes; same-input reinstall versus changed input. Dirty content matters too. |

Avoid an exact-HEAD history key: each ordinary update would erase comparability. Conversely, do not merge an unchanged-input quick reinstall with a changed-source build merely because both use the same profile. Cache presence is only a rough feature, not proof that all cache entries are usable. If the current workload cannot be classified confidently, show historical context without a remaining-time estimate.

### A deliberately simple first estimator

1. Retain the most recent 10 comparable successful samples, with an age limit such as 60 days. These are proposed defaults, to tune against real data.
2. With zero samples: elapsed only, plus a short learning message.
3. With one sample: show `last similar build: …`.
4. With two to four samples: optionally show a static recent duration band, but no countdown.
5. With at least five sufficiently consistent samples: show a coarse remaining-time band derived from empirical duration quantiles, rounded to tens of seconds or whole minutes. Call it approximate, not a confidence interval.
6. With large dispersion, a known cache reset, or a changed toolchain/profile: withdraw the countdown and keep the elapsed time and historical context.

For example, let `L` and `U` be the 20th and 80th percentiles of comparable total phase durations and let `e` be elapsed phase time. While `e < L`, the display can use the coarsely rounded interval `[L-e, U-e]`. Once the lower end has passed, prefer a static `similar builds: 3–5m` indication rather than showing an interval starting at zero. Once `e > U`, show `taking longer than usual`. This is a small-sample heuristic, not a probabilistic guarantee or a continuously reconditioned survival model.

Exclude failed and cancelled phases, explicit user-input waits, and known machine-sleep interruptions from the predictor. Preserve them in run history for diagnostics. Keep genuinely slow successful builds; removing inconvenient samples would make estimates systematically optimistic. Use a monotonic timer for intervals, not wall-clock subtraction; record wall time separately for human-readable run dates. Suspension behavior needs platform testing rather than assuming every monotonic clock handles laptop sleep identically. [Python timing reference](https://docs.python.org/3/library/time.html#time.monotonic)

### Scope the ETA clearly

For the first version, the live line estimates the **current named build phase**. It must not say “installation complete in…” while future pulls, signing prompts, plugin drift, or restart actions remain unresolved.

A whole-run estimate is optional follow-up work. Only display one when all enabled remaining phases have usable history and no unbounded input wait is active. If summing empirical phase bands, label the result as a rough sum, not an 80% confidence interval; individual quantiles do not add into a joint confidence statement. Show a phase estimate when the rest of the run is unknown.

Do not turn `elapsed / expected_duration` into a progress percentage. That estimates how much of a prior duration has elapsed, not how much current work has completed.

## Commit presentation that stays readable and correct

### Capture the exact source range

Capture full `HEAD` object IDs before and after each pull. Generate the report from `old..new` only after a successful source update. Use abbreviated IDs only for display. Retain complete message text and IDs immediately, rather than asking Git for “the last N commits” at the end of the entire run.

For machine-readable extraction, use a NUL-delimited Git format with fields such as full ID and `%B`, disable color and paging, and read the byte stream in the helper rather than a Bash variable. Do not parse `git pull` prose or assume `ORIG_HEAD` is the intended baseline. Git documents literal-byte formatting and the effect of history traversal options. [Git log reference](https://git-scm.com/docs/git-log)

Keep the exact all-commit range as the receipt's authoritative count. A first-parent presentation can be a later optional view, but it must not silently hide merged commits while calling its row count “all commits.” Use a stable traversal order, preferably newest first for the compact receipt, and make omissions explicit.

Handle these cases deliberately:

| Case | Correct description |
|---|---|
| No new revision | Up to date; do not replay an unrelated recent log. |
| First clone | Initial checkout at the current revision; do not dump the repository's entire history. |
| Pull failed | Using local checkout; show the warning and no invented incoming change list. |
| Missing range object or incomplete history | Changes unavailable for this range; show the known revisions. Never substitute a different range. |
| Dirty checkout | Source includes local changes; the commit list describes only the pulled part. |
| Pull succeeded, build failed | Source updated, installation failed. Retain the change record for recovery. |
| Plugins partially synced | Commits pulled; deployment has remaining drift. Do not attribute a commit to a deployed plugin unless that mapping is actually known. |

A useful adjacent improvement is a last-successful-install watermark per component. On a retry after a failed build, it can identify pending changes even if the second pull is already current. Keep `pulled this run` separate from `since the last recorded successful install`. An unknown baseline must stay unknown. Mac restart-only warnings should not erase evidence that the verified app installed, and partial plugin sync must not advance an “all deployed” watermark.

### Fold automation metadata, not meaning

Default visible notes contain the actual subject and useful body text. Preserve scopes such as `fix(capture):` and every breaking-change marker; do not rewrite the commit's meaning or claim an AI-generated release note is authoritative.

For this repository family, implement a narrow recognizer for the known trailing SASE metadata block, including its associated generated Markdown reference definitions. Hide only recognized metadata and definitions referenced exclusively by it. If a body paragraph uses the same link, retain the definition. If the block is malformed or mixed with real prose, leave it alone. Never truncate a message at the first occurrence of `SASE_`, and never strip all Git trailers: `BREAKING CHANGE` and migration instructions can matter.

Label filtered output `Commit notes` and, when filtering occurs, explain once that automation metadata is omitted. Reserve the term `full commit messages` for the complete saved originals. Do not silently remove tests/docs/build commits either; those subjects can explain an update that copies no plugin files.

### Define “fits” as a rendering budget

At display time, obtain terminal columns and rows. Measure the formatted output in terminal cells after wrapping and indentation; bytes, code points, and newline counts are insufficient. Use conservative handling for wide or combining characters and tabs. A fallback ASCII layout avoids cursor corruption when width cannot be established.

For each component's preview, budget no more than roughly half the terminal height and cap it at around 16 rows. For the final receipt:

1. Lay out the outcome, component rows, warnings/actions, log locations, and a small allowance for the next shell prompt.
2. Compute the remaining height for commit notes. Cap even a very tall terminal's notes area, for example at 32 rows, to avoid a wall of text.
3. If every visible subject and filtered body fits, show them all.
4. Otherwise, if all subjects fit, show all subjects and omit bodies.
5. Otherwise, allocate at least one subject to each changed repository when possible, then distribute remaining rows fairly in stable repository order. Add explicit per-repo `+N more` counts and the full-message path. Account for those omission rows before choosing subjects.
6. If the terminal is too short even for the base receipt, preserve outcome and action information, permit scrolling, and collapse changes to counts plus the saved file path.

An explicitly identified breaking change gets an action row in the receipt even if its full body is omitted. The file remains the source for lengthy migration details. Terminal resizing changes the next layout decision and the live line; it should not trigger a redraw of earlier scrollback.

Never start a pager while compilation or installation still needs the terminal. Do not block the default success path on “press Enter to view changes.” Save a plain-text `changes.txt` and print its path. The user can open it with a pager independently, during a build from another pane or after completion.

## Implementation architecture and alternatives

### Recommended split

Keep `scripts/install_all` as the orchestration layer and add a small Python 3 helper for presentation, timed build execution, run-record serialization, and change-note layout. Use only the standard library; do not bootstrap pip packages or compile a new UI executable at the moment the user is waiting for Bob to compile.

The helper should have a small internal interface: initialize/resume a run; collect a source range; run a named noninteractive build command; record a phase outcome; render the receipt. Pass argv arrays, not shell-evaluated command strings. Python's subprocess API provides return codes and pipes, and selectors can drain output without waiting for a complete newline. [Subprocess documentation](https://docs.python.org/3/library/subprocess.html), [selectors documentation](https://docs.python.org/3/library/selectors.html)

At startup, detect a supported Python 3 interpreter. If absent, retain Bash installation behavior and plain commit subjects/ranges; elapsed phase messages can remain available with existing shell facilities. Do not download a runtime automatically or fail an otherwise supported install solely because the enhanced presenter is unavailable. This is an explicit tradeoff: the richest experience is conditional on Python, and the fallback needs coverage. If Python becomes an accepted installer prerequisite later, remove the duplicate fallback only through a separate compatibility decision.

The helper is not the installed `bob` binary: this must work before Bob exists or when the existing Bob is broken.

### Own output only where it is safe

Wrap compiler/build commands at their real call sites. In bob-cli, that means the Cargo invocation inside `just install`, while keeping the installation-root migration and completion behavior intact. In Mac Capture, wrap the app build in `bundle.sh` and the install-helper build in `install.sh`. Signing, keychain unlocking, Git authentication, cloning, and other potentially interactive commands retain the real terminal with animation suspended.

Use a versioned, opt-in helper path/environment contract so direct `just install` in either repository still works independently. A sibling with no compatible support falls back to its original output, with coarse phase start/end messages around the whole component. Do not assume every user has updated all sibling checkouts atomically.

During a wrapped build, one process owns terminal rendering. Drain stdout and stderr continuously into bounded buffers and local logs. Keep compiler warnings and errors visible; suppress only well-understood routine chatter. Unknown output should remain accessible and should be surfaced conservatively. Explicit `--verbose` can stream the complete build log, with progress redrawn safely between complete output chunks or replaced by periodic elapsed lines.

Disable Cargo's nested animated bar in managed mode using its supported progress configuration; do not parse its carriage-return bar. This setting is local to the child invocation. Leave direct installs and fallback mode alone. [Cargo progress configuration](https://doc.rust-lang.org/cargo/reference/config.html#termprogresswhen)

Structured Cargo diagnostics are an optional second increment: they can identify warnings and cached artifacts, but do not justify a count-derived ETA. Swift's human-readable output likewise should not become a mandatory parser contract. Named phases can be emitted from shell boundaries under our control.

### Failure and lifecycle contracts

- Preserve existing success, warning, failure, and skip classifications. A spinner ending is not success; a process exit and the existing verification determine success.
- Preserve stdin and process-group behavior. Ctrl-C must cancel the active build and its descendants, stop later installation steps, restore terminal state, and mark the phase interrupted. Test Ctrl-C from a real pseudo-terminal; simply trapping it in the renderer is insufficient.
- Never wait for newline output before updating elapsed time. Conversely, continuous output must not starve the timer or fill a pipe and block the child.
- Cosmetic errors should fall back to readable output within the running supervisor. Never rerun a potentially successful install because its display failed. If the supervisor itself dies, report an interrupted/unknown outcome rather than guessing completion.
- Restore cursor visibility and stop animation on normal exit, failure, interruption, and output closure. Avoid changing terminal modes unless necessary; no hotkey interception is required for this design.
- Capture diagnostics with private permissions and bounded retention, for example 20 recent runs or 30 days. Do not store interactive input. State/log-write failures must degrade presentation rather than replace an install result.
- Prevent multiple install-all invocations from mutating the same installation targets simultaneously, or explicitly detect and reject that case before mutation. At minimum, unique per-run files and atomic writes must prevent history corruption. Locks need stale-owner handling and must survive installer re-exec without deadlock.
- Treat commit text as data. Escape terminal control sequences for display; do not let message content move the cursor or forge receipt rows. Retain original message payloads separately when needed for exact recovery.

### Re-exec deserves a dedicated test

Persist a run ID, full before/after revisions, already-recorded source changes, and timing state before self-update exec. Resume rather than initialize again. Stop any old presenter before exec and let the updated script start its compatible helper. Avoid a long-lived presenter importing source files that the pull is replacing.

The very first upgrade from today's installer needs a migration path: the old script exports only formatted pull detail and elapsed time. Either recognize that exact legacy range format, resolve both abbreviations locally, and verify the range, or explicitly report that the range is unavailable for this upgrade. Do not silently guess using the latest reflog entry. Future runs should use only structured state. A cautious one-time omission is preferable to an incorrect changelog, but support for the known legacy format is feasible and improves this first rollout.

### Alternatives considered

| Approach | Benefit | Cost or objection | Assessment |
|---|---|---|---|
| Add a Bash spinner around existing commands | Small initial diff | Competing terminal writers, prompts, logs, and accurate wrapping become difficult; spinner alone adds little context | Suitable only as a limited first increment |
| Entire enhancement in Bash | No runtime dependency | Structured history, Unicode sizing, signal ownership, and buffered output add substantial fragile shell code | Keep Bash orchestration; avoid implementing the whole presenter here |
| Optional standard-library Python helper | Fast startup, straightforward records/timers/layout, no package installation | Requires a fallback and a carefully tested subprocess wrapper | Recommended |
| Rich/Textual or a full-screen TUI | Polished widgets and sophisticated layout | Extra dependencies, lost scrollback expectations, more input/prompt complexity | Too much for this workflow |
| Rust UI crate built at install time | Matches the main language | Creates another bootstrap build; cannot rely on Bob already being installed | Poor fit for solving this wait |
| PTY around every child | Preserves many TTY behaviors | Terminal emulation, passwords, nested animation, and signal forwarding become the project's problem | Avoid; instrument controlled noninteractive boundaries |
| Weighted build-task percentage | Looks precise | Needs compiler/dependency/cache modeling; equal task weights recreate the screenshot problem | Do not ship |
| Parallel CLI and Mac builds | Could reduce total latency on some machines | Resource contention can lengthen builds; complicates estimates, output, and failure ordering | Measure separately before considering |
| Install prebuilt binaries | Can genuinely eliminate compilation | Different source/release semantics; local edits and Mac signing complicate it | A separate distribution decision, not the default answer here |

## Verification and rollout

The main risks are behavioral regression and misleading claims, not the spinner glyph. Test the presentation with fake child commands and temporary Git repositories before running expensive real installs.

| Area | Required cases |
|---|---|
| Terminal rendering | 80×24, narrow 40-column pane, tall pane, resize during a long build, Unicode subjects, tabs, long unbroken paths, monochrome, dumb terminal, redirected streams |
| Child I/O | Silence for a long interval, partial lines, carriage returns, high-volume stdout/stderr, warnings during progress, malformed byte sequences |
| History | First run, one sample, several stable samples, broad variance, cache absent, changed profile/toolchain, same-input reinstall, dirty source, invalid JSON, unwritable state, interruption and sleep |
| Git | Zero/one/many commits, merge history, first clone, failed fast-forward, missing objects, long metadata-only messages, real body references to metadata links, breaking-change notes, terminal-control bytes |
| Installation semantics | Missing sibling/vault, plugin drift, failed CLI followed by existing later-step behavior, Mac signing failures, installed-but-restart-needed outcome, pending Obsidian restart |
| Lifecycle | Self-pull re-exec exactly once, legacy-to-new migration, interrupted child tree, renderer/logging failure, concurrent invocation, no Python |

For layout tests, assert terminal-cell bounds and visible outcome/action content, not only giant string snapshots. For estimation, use a fake monotonic clock and explicit samples. For process tests, verify child termination and exact outcomes; a screenshot cannot prove cancellation works.

A real Mac trial should cover a warm source update, a same-input reinstall, a deliberately cold scratch build, an available signing identity, a locked keychain, and both a running and stopped app. Do not clear Bryan's actual build cache merely to obtain a measurement. Record predicted versus observed duration to assess whether five comparable samples and the proposed quantiles are useful. Baseline compile-time profiling can use Cargo's timing report independently of the UI work.

Suggested increments:

1. Add exact revision capture, source-change files, and compact adaptive commit notes. Preserve existing build output initially.
2. Add the single-line managed build display, real phase boundaries, logs, and reliable prompt/cancellation behavior. Record durations but initially show only elapsed/previous time.
3. Enable coarse remaining-time ranges for comparable history after fixture tests and actual Mac trials. Keep total-run ETA out until it adds clear value.

This research did not implement those increments or run the proposed verification. The main remaining empirical question is how stable Bryan's warm build durations are under normal Mac use; the screenshot and repository alone cannot answer it.

## Recommended solution

Build a restrained inline installer: useful commit notes above one live phase line, truthful elapsed time on every run, and a concise final receipt. Let comparable machine-local history earn a coarse ETA; when it cannot, say what is running and how long it has run. Keep complete messages and diagnostics available without forcing a pager or prompt.

Implement the presentation as a small optional Python helper while preserving Bash orchestration and a plain fallback. Instrument the actual Cargo and Swift build boundaries, give signing/authentication the terminal, and preserve self-update, warning, deployment, and restart semantics. This delivers the requested polish without making uncertain estimates or an elaborate terminal interface part of installation correctness.
