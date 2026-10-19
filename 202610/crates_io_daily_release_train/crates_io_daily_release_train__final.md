# Daily crates.io releases for bob-cli with release-plz: consolidated report

- **Date:** 2026-10-19
- **Repo state:** `bobs-org/bob-cli` `master` @ `bfca3419`
- **Inputs:** five independent reports (`__cdx`, `__cld`, `__grk`, `__mus`, `__gem` in this
  directory) plus the lead researcher's own verification. That verification covered the
  release-plz source at `release-plz-v0.3.173` (`907af6d0`), live crates.io API and
  sparse-index queries, the bob-cli checkout and the current crates.io blog posts.
- **Question:** Should bob-cli be published to "cargo.io" (crates.io) with release-plz, at
  most once a day and only when all CI checks are green? What is the best implementation,
  and what should change in the plan?

## Bottom line

1. **The idea is worth doing, but not in its current form.** Four blockers stand in the way
   today:
   - **The crate name `bob-cli` is taken** on crates.io by an unrelated project.
   - **There is no license.**
   - **There is no CI at all**, so "when CI is green" checks nothing.
   - **The `.crate` file is already 88% of crates.io's 10 MiB cap.** It nearly tripled in
     the past nine days.
2. **Most of the value comes from what the plan forces into existence**, not from
   crates.io. That means real CI, meaningful version numbers (`bob --version` has said
   `0.1.0` since June), a changelog and rollback points. crates.io adds a public
   `cargo install` path and a permanent public record. Those are modest benefits with
   one-way costs.
3. **Do not copy the release-plz quickstart.** It publishes on every push, which breaks the
   cap. Swapping the push trigger for a cron does not create a real cap either. The
   release-PR flow suits PR-based repos, and this repo has never had a PR or a merge
   commit. Every change is pushed straight to `master` by agents (about 4–38 commits a
   day).
4. **Recommended design: a scheduled "release train".** One workflow does everything in
   order:
   1. A registry-backed once-per-day guard and a pause switch.
   2. Full CI on the exact SHA (Linux and macOS).
   3. `release-plz update`.
   4. A fast-forward-only push of the version bump.
   5. `release-plz release` with crates.io Trusted Publishing.
   6. Later, prebuilt binaries built in the same workflow.

   This is cld's design with fixes taken from cdx's failure analysis. The full plan is in
   [§7](#7-recommended-solution).
5. **Roll it out in stages.** CI comes first and pays off on its own. Next, rehearse the
   train for one to two weeks in release-plz's `git_only` mode (tags and GitHub Releases,
   no registry). Switch to crates.io only after the name, license and size problems are
   fixed. Rehearsal mode differs from live mode only in config, so staging costs almost
   nothing and avoids burning permanent crate versions on pipeline bugs.

---

## 1. Established facts (all five reports agree; re-verified where marked ✓)

| Fact | Evidence | Consequence |
|---|---|---|
| The registry is **crates.io**; there is no cargo.io | — | — |
| ✓ **`bob-cli` is taken**: longcipher/bob, "CLI app for Bob - a general-purpose AI agent framework", v0.3.2, created 2026-03-25, 85 downloads. ✓ **`bob` is taken**: jperkin's pkgsrc builder, v1.0.0. | crates.io API, 2026-10-19 | The package needs a new name. The `bob` binary name can stay. `cargo install bob-cli` already installs someone else's tool. |
| ✓ Free on 2026-10-19 (HTTP 404): `bob-obsidian`, `bobsidian`, `bob-vault`, `bob-vault-cli`, `bobs-cli`, `bob-gtd`, `bobctl`, `bob-pkm` | crates.io API | Names are first-come, first-served. Re-check right before the first publish. |
| ✓ No `.github/`, zero workflows, no branch protection, no PRs, no merge commits, no tags | checkout, `gh api` | CI has to be built from scratch. The default branch is **`master`**, so upstream YAML examples that use `main` would never fire. |
| ✓ No license: no `LICENSE*` file, no `license` key, GitHub `license: null` | checkout, `gh api` | crates.io rejects the publish. This is also a real legal gap for a public repo. |
| ✓ The `.crate` is **9,256,837 bytes**: 956 files, 30.2 MiB raw | `cargo package` (cdx, cld) | The cap is **10,485,760 bytes (10 MiB)**, as quoted in crates.io's own HTTP 413 message. The crate uses 88% of it, leaving about 1.17 MiB of headroom. |
| ✓ The size jumped recently: the snapshot fonts were added 2026-10-16 (`ca88db38`) and the vendored Mermaid on 2026-10-17 (`54670b45`). cld measured 3.3 MiB → 8.9 MiB compressed from Oct 10 to Oct 19. | `git log` | Size growth is the most likely way for publishing to start failing silently some day. |
| Compressed size by directory (cld): assets 2.7M, scripts 2.7M, src 2.4M, tests 647K, docs 470K | `cargo package` | Trimming `tests/`, `docs/` and `justfile` saves about 1.1 MiB, leaving about 7.7 MiB (about 74% of the cap). |
| Commit subjects are 500/500 Conventional Commits. ✓ Only 1 `!` (breaking) marker in the last 30 days, out of 578 commits. | `git log` | release-plz works with no change to commit habits. But breaking-change signalling is effectively unused today. |
| One package with four binaries (`bob`, `bob_pomodoro`, `bob_notify`, `tmux_bob_pomodoro`) **and a library target** (`src/lib.rs`) | `Cargo.toml` | One release train for everything. A rename changes the default lib name, so pin `[lib] name = "bob_cli"`. |
| macOS-only dependencies (`rusqlite` bundled, `plist`). rquickjs compiles QuickJS (C). | `Cargo.toml` | CI needs a macOS job. Every `cargo install` compiles C code and takes minutes. |
| ✓ The exact `clap_complete = "=4.6.11"` pin | `Cargo.toml` | Every install snippet should use `--locked`. |
| Bryan's machines install from checkouts at HEAD (`just install`, `just install-all`). Bob Mac Capture builds against bob HEAD. | README, `~/.cargo/.crates.toml` (cld) | The crates.io audience today is *other people*, not Bryan's own hosts. |

### release-plz facts verified in source and docs (v0.3.173)

- **`release-plz release` never bumps versions.** It publishes versions that are already in
  `Cargo.toml` and not yet on the registry, then tags and creates a GitHub Release. Only
  `update` and `release-pr` bump versions and write the changelog.
- **`release_always`** (default `true`): with `false`, `release` publishes only when HEAD
  is associated with a `release-plz-*` PR. In `should_release()`, a normal merge publishes
  the PR's last commit. A squash merge falls back to the checked-out commit, and the docs
  warn about races.
  - This setting checks *where* a release came from. **It is not a time limit.**
- **Already-bumped versions are safe to retry.** When the local version is ahead of the
  registry, `update` logs "Only changelog will be updated" and does not bump again. A
  failed publish therefore retries cleanly on the next run.
- **Trusted Publishing is built in.** On GitHub Actions, with no token supplied and
  crates.io as the target, release-plz performs the OIDC exchange itself and revokes the
  token afterwards. The quickstart says: **don't** add
  `rust-lang/crates-io-auth-action`, **don't** set `CARGO_REGISTRY_TOKEN`, and set
  `id-token: write`. A new crate's first version must be published manually, which is a
  crates.io limitation.
- **`git_only = true`** takes versions from git tags and skips `cargo publish`. Combining
  `publish = true` with `git_only = true` is a config error.
- **`release_commits`** (regex) controls whether a bump happens at all, so a docs-only day
  can produce no release.
- **CLI flags:** `release-plz release --git-token <t> -o json` prints
  `{"releases":[{"package_name","prs","tag","version"}]}`.
- **The GitHub Action only supports `command: release-pr | release`.** The train calls
  `update`, so it installs the CLI directly.
- **Pin the release-plz version.** The CLI ships often: v0.3.172 came out 2026-10-12 and
  v0.3.173 on 2026-10-19, according to the sparse index `pubtime`.

### crates.io and GitHub facts that shape the design

- **Versions are permanent.** Yanking hides a version from new dependency resolution but
  deletes nothing. A crate can only be deleted within 72 hours of publishing, or if it has
  one owner, no reverse dependencies and low monthly downloads (RFC 3660, crates.io
  policies). Anything shipped stays public forever.
- **The January 2026 crates.io update** ([blog](https://blog.rust-lang.org/2026/01/21/crates-io-development-update)):
  - Trusted Publishing is **blocked** for the `pull_request_target` and `workflow_run`
    triggers. Never build the publisher around `workflow_run`.
  - Each crate can enable **Trusted-Publishing-only** mode.
  - Index entries gained a **`pubtime`** field. ✓ It is RFC 3339 UTC, for example
    `"2026-10-19T19:56:53Z"`.
- **The July 2026 update** says nothing about first-publish via Trusted Publishing, size
  limits or rate limits.
- **Events from the default `GITHUB_TOKEN` don't start other workflows**, apart from
  `workflow_dispatch` and `repository_dispatch`. A merge, tag or release created with it
  will not fire `on: push`, `on: release` or `on: push: tags` workflows. Put follow-up
  steps in the same workflow, or use a GitHub App token.
- **GitHub cron is best-effort.** Runs can be late or dropped, especially on the hour. A
  cron schedule offers chances to run; it is not a rate limit.
- **Hosted runners, including macOS, are free for public repos.**

### Test-suite hermeticity (cld's finding; consistent with the code)

cld ran the suite in a clean `HOME`, with `TZ=UTC` and without `~/.local/bin`. 5,080 of
5,082 tests passed. Two failed:

- `native::capture::task_blocks::tests::authored_children_and_schedule_log_are_added_in_order`
  uses a `$1` priority. Priority levels are read from `~/.config/bob/config.yml`
  (`src/native/config/mod.rs:287`).
- `tests/gkeep_auth.rs` `doctor_all_ok_reports_the_checklist` reaches the
  `uv not found on PATH` path in `src/native/gkeep/doctor.rs`.

Tests that need pandoc, xelatex, zsh or bash skip themselves when the tool is missing. A
bare runner would start red and also test less than Bryan's machines do.

---

## 2. Errors in individual reports (resolved here)

| Report | Claim | Resolution |
|---|---|---|
| **mus** | Option A: a daily cron running `release-plz release` with `release_always = true` and `needs: ci` gives "at most once a day". mus also says `release` "bumps `Cargo.toml`, writes changelog, commits". | **Wrong.** `release` never bumps. That workflow would publish nothing, because nothing ever bumps the version. It needs `update` (the train) or `release-pr` (the PR flow). |
| **gem** | Shrink `include` to `/src/**` plus metadata, giving "~50 files, <250 KiB". | **Breaks the build.** `src/` uses `include_bytes!`/`include_str!` on 28+ files under `scripts/` (adapters, the vendored Mermaid and Defuddle) and on the print fonts. `assets/**` and `scripts/**` must ship. |
| **gem** | "bob-cli has no [lib]" | Wrong. `src/lib.rs` exists, and the bins call `bob_cli::…`. |
| **gem** | The daily cron merges the release PR with `GITHUB_TOKEN`. `release-publish.yml` runs on that push, and binaries build `on: release`. | **Nothing would fire.** A push made with `GITHUB_TOKEN` doesn't trigger `on: push`, and a release it creates doesn't trigger `on: release`. As written, the pipeline never publishes. |
| **grk** | A 2022 crates.io change caps each crate at 10 new versions per day | Not verified. No source found; the documented limits are per-minute burst limits. Irrelevant at one release a day, so it is dropped. |
| **grk / gem** | The daily job checks "latest `master` CI is green", then merges the release PR | **Gates the wrong SHA.** The merged tree is the PR branch (an older `master` plus the bump), not `master` HEAD. The check is also racy against agent pushes. |
| **grk** | Squash-merge is "the case release-plz documents `release_always = false` for" | Upstream recommends normal merges. Squash only falls back to the checked-out commit and comes with a race warning. |
| **cld** | The release job uses `crates-io-auth-action` and sets `CARGO_REGISTRY_TOKEN` | The release-plz docs say explicitly not to. Let release-plz do the OIDC exchange. |
| **cld** | The daily guard reads the newest **GitHub Release** `createdAt`. A "nothing new" check skips when the HEAD author is the bot. | If a publish succeeds but release creation fails, the guard allows a second publish the same day. Use the **registry's `pubtime`** instead (cdx). The bot-author check can strand an unpublished bump; skip only when HEAD is already tagged. |
| **cld** | The publish step only runs when this run made a bump | It should run unconditionally. Then a bump left over from a failed run gets published (`release` is a no-op when nothing is pending). |

---

## 3. Critique: is this a good idea?

### What is right about the plan

- **A daily ceiling fits the commit rate.** Releasing on every commit would mean 4–38
  versions a day. Weekly releases would each bundle about 150 commits. Daily releases
  give readable changelogs (about 25 lines) and narrow, bisectable releases ("which day's
  release broke reconcile?").
- **Gating on CI is right.** It also forces CI into existence. About 25 agent-written
  commits a day currently reach `master` with no server-side check, and the macOS-only
  code is never compiled anywhere except the Mac.
- **release-plz is the right tool.** The repo already writes perfect Conventional Commits,
  has one package, and has a canonical `just check` gate. The alternatives each fall
  short:
  - **cargo-release** has no changelog support and is laptop-driven.
  - **release-please** is not registry-aware.
  - **cargo-smart-release** is not meant for CI.
  - **cargo-dist** is a distribution tool, not a versioning tool.
- **Versions start to mean something.** Bug reports, the Mac app's diagnostics and Bryan's
  hosts can all name a version instead of a SHA.

### What is wrong or risky as stated

1. **The plan cannot run today** because of the four blockers above.
2. **"At most once a day" and "all CI green" are undefined.**
   - "Green" must mean green for *the exact commit being released*. At about 25 pushes a
     day, "master was green at some point" is not the same thing.
   - An empty or skipped set of checks must count as *not* green.
   - "Once a day" needs a definition (calendar day or rolling 24 hours) and a durable
     source of truth. A cron schedule alone is neither.
3. **The idiomatic release-PR flow fits this repo poorly.**
   - It keeps a permanent bot PR that is force-pushed about 25 times a day.
   - It needs a GitHub App or PAT for CI to run on that PR, and for a merge to trigger
     publishing.
   - It adds merge commits to a history that has none.
   - No human will realistically review a release PR every day in an agent-driven repo.
4. **Publishing to crates.io is a set of one-way doors:**
   - **Permanence:** every daily version, including bad ones, stays public forever.
   - **The name:** the chosen name is permanent and public.
   - **The license:** the code becomes public under that license for good.
   - **A size cliff:** an innocent font or fixture commit can break publishing days after
     it lands.
5. **Building from source is a poor way to install an application.** `cargo install`
   compiles QuickJS (C), `image`, `lopdf` and, on macOS, bundled SQLite. That takes minutes
   per machine for each update. Users of `cargo install-update` would pay this every day.
6. **crates.io does little for Bryan's own machines.** The dev hosts and the Mac app track
   HEAD, and a release always lags HEAD by up to a day. Be honest that crates.io is
   distribution and hygiene for other people.
7. **CI only covers the Rust API.** bob's real contracts are command syntax, JSON and
   subprocess output for Bob Mac Capture and the plugins, and vault conventions.
   `cargo-semver-checks` sees only the incidental `bob_cli` Rust API. Breaking changes
   need `!` discipline in commit messages plus contract tests.

### Where the researchers split, and the resolution

- **crates.io now (cdx, cld) vs later or optional (grk, mus, gem).** In the train design,
  "GitHub Releases only" and "crates.io" differ by a few config lines. So the
  disagreement becomes one of *ordering*, not architecture:
  1. Rehearse with `git_only = true`.
  2. Fix the blockers.
  3. Switch to crates.io.

  If crates.io downloads after a month show no outside users, drop crates.io to an
  occasional or weekly cadence, or stop publishing there. GitHub Releases stay daily.
- **Release PR (cdx, grk, gem) vs no PR (cld, mus).** The resolution is no PR: see point 3
  above. cdx's design is the most rigorous. It reviews a release PR, then an hourly
  publisher selects the PR head and applies a rolling 24-hour registry guard. That is a
  good fit for a team repo with review discipline. Here, its custom candidate selector
  would be the most complex part of the system, and it would protect a review step that
  won't happen.
- **`semver_check` on (cdx) vs off (cld, grk, gem).** Turn it **off**. The library is an
  internal seam for the binaries. Semver checks would add minutes per run and produce
  spurious "breaking" bumps. Also, `update` only runs the check when cargo-semver-checks is
  installed. Replace it with `!` discipline for CLI and JSON contract breaks.
- **Rolling 24 hours (cdx) vs calendar day (cld).** Use a **calendar day in
  America/New_York**, with scheduled runs only in a fixed early-morning window. A rolling
  24-hour window with a fixed daily cron drifts: a release from the retry slot blocks the
  next day's main slot. cdx's worry about two releases minutes apart across midnight
  cannot happen when the only scheduled slots are about 04:00–07:00 ET and manual runs
  obey the same guard. What matters more than which definition is chosen is that the
  guard reads **registry data**, not cron timing or GitHub Releases.

---

## 4. Proposed changes to the requirements

| # | Original | Adjusted | Why |
|---|---|---|---|
| R1 | Publish to "cargo.io" | Publish to **crates.io** | There is no cargo.io. |
| R2 | Package `bob-cli` | **A new package name.** The default suggestion is **`bob-obsidian`**: the GitHub description is "Bugyi's Obsidian - CLI Client", it is descriptive and searchable, and it is not a near-homograph of the taken `bob-cli`. Runners-up are `bob-vault` and `bobs-cli`. Keep the binary `bob` and the three shims. Pin `[lib] name = "bob_cli"`. | The name is taken. Avoid `bobs-cli`/`bobcli`-style names that a single typo turns into the other project's crate. |
| R3 | Use release-plz | Use the release-plz **CLI (`update` + `release`) in one scheduled workflow, not the release-PR flow**. | The repo pushes directly to `master` and has no PRs, and the train needs no App or PAT. |
| R4 | At most once a day | **At most one new version per America/New_York calendar day.** The guard reads the registry's `pubtime` (yanked versions included) inside a serialized workflow. Releases happen only when something user-visible changed (`release_commits`). This is a **ceiling, not a quota**. Manual dispatch obeys the same guard. | A cron schedule is not a cap. A guard based on GitHub Releases can double-publish after a partial failure. |
| R4a | (new, Bryan's call) | Allow one **explicit hotfix override**: a `workflow_dispatch` input that requires a written reason and records it as a run warning. Drop it if "strictly once a day" is a hard rule. | A bad release otherwise waits until the next day to be fixed. |
| R5 | When all CI is green | Run a **named required set on the exact SHA being released, inside the release workflow** (a reusable `ci.yml`): fmt, clippy and tests on **Linux and macOS**, `check-scripts`, a `cargo package` integrity check and a size budget. Missing or skipped checks count as failure. | CI doesn't exist yet. Reading another workflow's status for a moving `master` is racy. |
| R6 | (new) | **Make the tests hermetic before CI becomes required.** Fix the two failures and install `uv` on the runners. Install zsh, pandoc, TeX and poppler on the full release-gate run so self-skipping tests actually run. | Otherwise CI is red from day one, or silently weaker than local runs. |
| R7 | (new) | **Choose a license**, for example `MIT OR Apache-2.0`. Keep the bundled third-party notices (OFL fonts, DejaVu, Mermaid, Defuddle, Moment) in the package. | crates.io requires a license, and the public repo has none. |
| R8 | (new) | **Add a size budget** to per-push CI: fail above 9 MiB, warn above 8 MiB. Trim `include`: drop `tests/**`, `docs/**` and `justfile`; keep `src/`, `assets/` and `scripts/`. | The crate is at 88% of the cap and growing. |
| R9 | (new) | **Use Trusted Publishing** after one manual first publish, behind a `release` environment restricted to `master`. Then enable Trusted-Publishing-only mode. | No long-lived secret, and no token-based way around the guard. |
| R10 | (dropped) | **No per-release human review and no cargo-semver-checks.** Instead, agents mark CLI and JSON contract breaks with `!`. Agents never edit `version` or `CHANGELOG.md`. | Review won't happen in practice, and the lib API is not the product. |
| R11 | (new, phase 2) | **Prebuilt binaries** for Linux x86_64 and macOS arm64 (plus x86_64 if needed), built in the same workflow, with `[package.metadata.binstall]`. | `cargo binstall` and `cargo install-update` then skip the C toolchain and the build. |
| R12 | (clarified) | **Publishing is not deploying.** No auto-upgrades. Dev hosts keep `just install-all` at HEAD, and companion repos are not released implicitly. | The Mac app and plugins track HEAD, and their JSON contract must keep growing additively. |

---

## 5. Architectures compared

| | Quickstart (push → publish) | Release PR + daily cron merge (grk, gem) | Reviewed release PR + hourly guarded publisher (cdx) | **Scheduled release train (cld, fixed)** |
|---|---|---|---|---|
| Honors the daily cap | ✗ publishes on every push | ✓ if merged at most once a day | ✓ rolling 24 hours, from the registry | ✓ calendar day, from the registry |
| Gates the exact published SHA | ✗ | ✗ checks `master`'s CI, not the merged PR tree | ✓ | ✓ CI runs on the SHA; the bump commit adds only the version, lockfile and changelog |
| Fits direct-to-master, linear history | ✓ | ✗ permanent bot PR and merge commits | ✗ | ✓ one bot commit a day |
| Extra credentials | none | GitHub App or PAT (or the merge never triggers the release) | GitHub App | **none** (`GITHUB_TOKEN` + OIDC) |
| Custom code | none | merge script | candidate selector, ancestry checks, guard | a ~20-line guard |
| Human checkpoint | — | optional | ✓ | pause switch (plus an optional environment approval at first) |
| Main weakness | violates the requirement | silent no-op traps around `GITHUB_TOKEN` | heavy for a single maintainer | an agent pushing during the ~20-minute gate rejects the push, so nothing ships that slot and a retry slot covers it |

---

## 6. Is crates.io worth it at all?

- **Do it if:** Bryan wants Bob to be installable by others, discoverable, and on
  `cargo install-update`/`binstall`. Or if he simply wants the hygiene of public,
  versioned releases.
- **Skip it if:** the only consumers are Bryan's hosts. Stay on `git_only` (tags, GitHub
  Releases and binaries) indefinitely. Every benefit except registry installs remains, and
  every step is reversible.
- **Revisit after about a month** of live publishing. If downloads are essentially Bryan's
  own, stop daily publishing to crates.io (go occasional or weekly) and keep daily GitHub
  Releases.
- **The long-term size lever:** if the crate approaches the cap again after trimming, the
  biggest fix is to **split the embedded assets (fonts, Mermaid) into a separate
  `<name>-assets` crate**. It gets its own 10 MiB budget and is published only when the
  assets change. Do not rely on getting a per-crate size increase from help@crates.io,
  which is unverified. Never use `publish_no_verify` to force a publish through.

---

## 7. Recommended solution

### Phase 0: decisions (Bryan)

1. **Crate name:** `bob-obsidian` (default), `bob-vault` or `bobs-cli`. Re-check for a 404
   on the crates.io API right before publishing.
2. **License:** `MIT OR Apache-2.0` is the Rust convention, or MIT alone.
3. **Hotfix override:** keep it (R4a) or make once a day strict.
4. **Binary targets for phase 6:** Linux x86_64 and macOS arm64; Intel macOS only if
   needed.

### Phase 1: CI (worth doing even if nothing is ever published)

- Fix the two non-hermetic tests. Give the `task_blocks` test its own config through an
  XDG override, and stub or install `uv` for the gkeep doctor test.
- Pin the toolchain: `rust-toolchain.toml` at 1.95.0 plus `rust-version`. Otherwise a new
  stable clippy lint turns `master` red overnight, which silently stops releases.
- Add `.github/workflows/ci.yml`. Use cld's sketch (`__cld` §8, Phase 1) as the base, with
  these properties:
  - It triggers on `push` to `master`, `pull_request` and `workflow_dispatch`, plus
    `workflow_call` with `sha` and `full` inputs so the release train can call it.
  - **lint:** `just fmt`, `just lint` and `just check-scripts`, matching the local
    `just check` gate.
  - **test:** `cargo test --locked --no-fail-fast` on `ubuntu-latest` and `macos-latest`,
    with `setup-uv`. When `full` is set, also install zsh, pandoc, xelatex and poppler.
  - **package:** `cargo package --locked`, then fail if `target/package/*.crate` exceeds
    9 MiB and warn above 8 MiB.
  - Pin third-party actions to commit SHAs, and use `Swatinem/rust-cache`.
- Let CI run for about a week. The red rate it shows predicts how often the train will
  skip a day.
- Branch protection: **do not** require PRs or status checks on `master`, because agents
  push directly. Use a ruleset that only blocks force-pushes and deletion of `master` and
  protects `v*` tags.

### Phase 2: package hygiene

```toml
[package]
name = "bob-obsidian"            # Phase 0 decision; the binary stays `bob`
version = "0.2.0"                # first public version; 0.1.0 = unversioned dev builds since June
license = "MIT OR Apache-2.0"    # Phase 0 decision
rust-version = "1.95"            # whatever CI proves
readme = "README.md"
keywords = ["obsidian", "gtd", "pomodoro", "cli"]
categories = ["command-line-utilities"]
include = [
    "/Cargo.toml", "/Cargo.lock", "/README.md", "/LICENSE*",
    "/src/**", "/assets/**", "/scripts/**",   # assets + scripts are include_bytes!'d — required
]

[lib]
name = "bob_cli"                 # keeps `bob_cli::…` imports compiling after the rename
```

Notes:

- **Unit tests won't run from the published crate.** Several tests under `src/` read
  `tests/fixtures/...`, so dropping `tests/**` means they cannot run from the extracted
  crate. That is acceptable for an application: package verification only *builds* the
  crate. Trim `scripts/**` further to just the embedded subset (no `dev/` or migrations)
  if needed.
- **Rename migration.** Run `cargo uninstall bob-cli` once on each host before the next
  `just install`. Otherwise Cargo refuses with "binary `bob` already exists … as part of
  `bob-cli`", and the README rightly forbids `--force`. Update the README install section
  and `scripts/install_all` to match.
- **Agent guidance.** Agents never edit `version` or `CHANGELOG.md`, and CLI or JSON
  contract breaks get `!` in the commit subject. Propose this through
  `/sase_memory_write` or as a decision record when the train goes live; it is not done
  here.
- **Seed `CHANGELOG.md`** with a short "0.2.0: first public release" entry.

### Phase 3: release train, rehearsal mode (`git_only`)

`release-plz.toml`:

```toml
[workspace]
git_only = true                   # rehearsal: tags + GitHub Releases only (publish must stay unset/false)
semver_check = false              # src/lib.rs is an internal seam, not a public API
dependencies_update = false       # dependency bumps are ordinary commits
publish_timeout = "30m"           # rquickjs verify build is slow
# Only bump when something user-visible landed; docs/test/chore-only days skip.
release_commits = "^(feat|fix|perf|revert)(\\(.+\\))?!?:|^[a-z]+(\\(.+\\))?!:"
```

`.github/workflows/release.yml` (sketch, untested; the flags were checked against the
v0.3.173 source):

```yaml
name: Release
on:
  schedule:
    - cron: "17 8 * * *"     # 04:17 EDT / 03:17 EST — the quietest commit window
    - cron: "47 10 * * *"    # retry slot; the daily guard makes it a no-op after a release
  workflow_dispatch:
    inputs:
      override_reason: { description: "Hotfix: bypass the once-per-day guard", type: string, default: "" }

concurrency: { group: release, cancel-in-progress: false }   # serializes cron, retry and manual runs
permissions: { contents: read }
env: { CRATE: bob-obsidian }

jobs:
  plan:
    runs-on: ubuntu-latest
    outputs: { sha: "${{ steps.p.outputs.sha }}", go: "${{ steps.p.outputs.go }}" }
    steps:
      - uses: actions/checkout@<sha>
        with: { ref: master, fetch-depth: 0 }
      - id: p
        env:
          PAUSED: ${{ vars.RELEASES_PAUSED || 'false' }}     # kill switch: repo variable
          OVERRIDE: ${{ inputs.override_reason || '' }}
          GH_TOKEN: ${{ github.token }}
        run: |
          set -euo pipefail
          sha=$(git rev-parse HEAD); echo "sha=$sha" >> "$GITHUB_OUTPUT"
          go=true
          [ "$PAUSED" = true ] && { echo "paused"; go=false; }
          git describe --tags --exact-match --match 'v*' HEAD >/dev/null 2>&1 && { echo "HEAD already released"; go=false; }
          # Daily guard. LIVE: newest pubtime of any version (yanked included) from the registry;
          # a failed lookup fails the job, so nothing ships (fail closed).
          last=$(curl -fsS -A "bobs-org/bob-cli release" "https://index.crates.io/${CRATE:0:2}/${CRATE:2:2}/$CRATE" \
                 | jq -rs 'map(.pubtime // empty) | max // empty')
          # REHEARSAL (git_only, crate not on the registry yet): use the newest GitHub Release instead:
          # last=$(gh release list -L 1 --json createdAt --jq '.[0].createdAt // empty')
          if [ -n "$last" ] && [ "$(TZ=America/New_York date -d "$last" +%F)" = "$(TZ=America/New_York date +%F)" ]; then
            if [ -n "$OVERRIDE" ]; then echo "::warning::daily guard overridden: $OVERRIDE"
            else echo "already released today ($last)"; go=false; fi
          fi
          echo "go=$go" >> "$GITHUB_OUTPUT"

  ci:                                   # "all CI green" = the required set, on the exact SHA we ship
    needs: plan
    if: needs.plan.outputs.go == 'true'
    uses: ./.github/workflows/ci.yml
    with: { sha: "${{ needs.plan.outputs.sha }}", full: true }

  release:
    needs: [plan, ci]
    runs-on: ubuntu-latest
    environment: release                # must match the crates.io Trusted Publisher config
    permissions: { contents: write, id-token: write }
    outputs: { tag: "${{ steps.publish.outputs.tag }}" }
    steps:
      - uses: actions/checkout@<sha>
        with: { ref: "${{ needs.plan.outputs.sha }}", fetch-depth: 0 }
      - uses: taiki-e/install-action@<sha>
        with: { tool: release-plz@0.3.173 }          # pin; bump deliberately
      - id: bump
        run: |
          set -euo pipefail
          release-plz update
          [ -z "$(git status --porcelain)" ] && exit 0
          v=$(cargo metadata --no-deps --format-version 1 | jq -r '.packages[0].version')
          git config user.name  "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
          git add -A && git commit -m "chore(release): v$v"
          git push origin HEAD:refs/heads/master   # fast-forward only: if master moved, fail → nothing ships
      - id: publish                                # always runs: also ships a bump left by a failed run
        env: { GIT_TOKEN: "${{ github.token }}" }  # NO CARGO_REGISTRY_TOKEN: release-plz does the OIDC exchange
        run: |
          set -euo pipefail
          release-plz release -o json | tee release.json
          echo "tag=$(jq -r '.releases[0].tag // empty' release.json)" >> "$GITHUB_OUTPUT"
```

Notes on the sketch:

- **No-PAT design.** Everything happens in one workflow, so the `GITHUB_TOKEN`
  no-chaining rule never applies.
- **Same-SHA consistency.** The CI'd SHA is the parent of the release commit. The release
  commit changes only `version`, the lockfile's self-entry and `CHANGELOG.md`, and
  `cargo publish` verifies it builds.
- **Cost.** Expect about 15–25 minutes per gated run on hosted runners. That is an
  estimate extrapolated from 5.5 minutes on 16 local cores, and it is free for public
  repos.
- **Optional optimization.** Have `plan` run `release-plz update` and skip CI when nothing
  would change. This avoids a CI run on docs-only days.

Run the rehearsal for one to two weeks. Check:

- Version math: `feat`/`fix` → patch and `!` → minor while on 0.x.
- Changelog grouping, plus `commit_parsers` to drop `chore(release)`, test and chore
  entries.
- The guard: retry and manual runs must not double-release.
- How often an agent push races the gate.

### Phase 4: first crates.io publish (manual, once)

1. From a clean checkout of the latest green, tagged release commit, run
   `cargo publish --locked`. Use a crates.io token scoped `publish-new` + `publish-update`
   to this crate name. Publish from a committed SHA, not a dirty tree, so
   `.cargo_vcs_info.json` records the source.
2. Revoke the token.
3. In the crate's settings, add a Trusted Publisher: owner `bobs-org`, repo `bob-cli`,
   workflow `release.yml`, environment `release`. Create the GitHub `release`
   environment, limited to `master`.
4. Change `release-plz.toml` to `git_only = false` (publishing is the default). Switch the
   guard to the registry `pubtime` lookup. Keep `id-token: write`.
5. Watch the first two automated releases. Then enable **Trusted-Publishing-only** mode
   on the crate.
6. Update the README install section:

   ```sh
   cargo install bob-obsidian --locked && bob completion install
   ```

   Add a note that `cargo install bob-cli` installs a different project.

### Phase 5: runbook

| Situation | What happens / what to do |
|---|---|
| CI red | The train ships nothing. Tomorrow's run tests the new HEAD. |
| Push rejected (an agent pushed during the gate) | Nothing ships. The retry slot (about 06:47 ET) tries again. |
| Bump pushed, publish failed (outage, size) | `master` carries an unpublished version. The next run's `update` only refreshes the changelog (verified in source), and `release` publishes it. The guard allows it because nothing was published today. |
| Published, but the tag or GitHub Release is missing | release-plz skips versions that are already published. Create the tag and release by hand for *that* version at the release commit. The registry-based guard prevents a second publish that day. |
| Bad release | `cargo yank --version X.Y.Z`, then fix forward and use `workflow_dispatch` with an override reason. Yanking does not reset the guard, because `pubtime` counts yanked versions. |
| Size breach | Per-push CI fails at the 9 MiB budget long before the train does. Trim, or split out an assets crate. |
| Pause | Set the repo variable `RELEASES_PAUSED=true`. |

### Phase 6 (optional): prebuilt binaries

Add a `binaries` job to `release.yml` with `needs: release` and
`if: needs.release.outputs.tag != ''`. It runs `taiki-e/upload-rust-binary-action` over
`{ubuntu-22.04: x86_64-unknown-linux-gnu, macos-latest: aarch64-apple-darwin}` (add
`x86_64-apple-darwin` if needed) for all four binaries. It runs in the same workflow, so no
PAT is needed. Add the matching `[package.metadata.binstall]` `pkg-url` so
`cargo binstall` and `cargo install-update` use the archives.

- **Why not cargo-dist:** it wants its own tag-triggered workflow and ownership of the
  GitHub Release, which needs an App or PAT plus coordination with release-plz. Revisit it
  only if shell or Homebrew installers become a goal.
- **Skip Windows.**

### Acceptance checks before calling it done

- A red required check, or an **empty** set of checks, publishes nothing.
- Two cron slots plus a manual run on the same ET day produce at most one new version.
  An override is the only exception, and it is visible in the run summary.
- A commit pushed during the gate is never included in that release. The push is
  rejected instead.
- A publish-succeeded/tag-failed state is repaired without a second upload.
- `cargo package` from CI shows no `sase/`, `vault/`, `tests/` or `docs/`, and does
  include every `include_bytes!` input and every third-party license notice.
- Installing the crate into a temporary root produces all four executables and working
  shell completion, without `--force`.

---

## 8. Open questions for Bryan

1. **Audience:** should anyone besides Bryan install from crates.io? This decides whether
   phase 4 happens at all and whether phase 6 is required.
2. **Name:** `bob-obsidian`, `bob-vault`, `bobs-cli` or another?
3. **License:** `MIT OR Apache-2.0`, or MIT?
4. **Hotfix override:** keep it, or make once a day strict?
5. **Release hour:** about 04:17 ET, or after the evening wrap-up?

---

## Sources

**Repository evidence (2026-10-19):**

- `Cargo.toml`, `README.md`, `src/lib.rs`, `src/scripts.rs`
- `src/native/config/mod.rs:287`, `src/native/gkeep/doctor.rs:277`
- the `include_bytes!`/`include_str!` inventory under `src/`
- `git log` (cadence, Conventional Commits, asset additions `ca88db38` and `54670b45`)
- `gh api repos/bobs-org/bob-cli`
- `cargo package` measurements and the clean-environment test run reported by cdx and cld

**release-plz** (source at `release-plz-v0.3.173`, opened with `sase repo open`):

- `crates/release_plz_core/src/command/release.rs`: `should_release()` and the
  trusted-publishing selection
- `.../command/trusted_publishing.rs`
- `.../command/update/updater.rs`: the "local version > registry version" handling
- `crates/release_plz/src/args/release.rs`: `--git-token` and `-o json`
- docs: `config.md` (`release_always`, `git_only`, `release_commits`),
  `github/quickstart.md` (Trusted Publishing tip), `github/advanced.md` (schedule),
  `usage/update.md`, `usage/release.md` (JSON output)
- online: <https://release-plz.dev/docs/config>,
  <https://release-plz.dev/docs/github/quickstart>,
  <https://release-plz.dev/docs/github/token>,
  <https://release-plz.dev/docs/extra/releasing-binaries>

**crates.io and Cargo:**

- crates.io API `/api/v1/crates/<name>` and sparse index `index.crates.io/bo/b-/bob-cli`
  plus `re/le/release-plz` (`pubtime`), queried 2026-10-19
- [Cargo Book: Publishing](https://doc.rust-lang.org/cargo/reference/publishing.html) (size
  limit, permanence, required metadata)
- [crates.io development update, 2026-01-21](https://blog.rust-lang.org/2026/01/21/crates-io-development-update)
  (blocked triggers, Trusted-Publishing-only mode, `pubtime`)
- [crates.io development update, 2026-07-13](https://blog.rust-lang.org/2026/07/13/crates-io-development-update)
  (silent on first-publish Trusted Publishing and on limits)
- [crates.io development update, 2025-07-11](https://blog.rust-lang.org/2025/07/11/crates-io-development-update-2025-07)
  (Trusted Publishing launch)
- [RFC 3660](https://rust-lang.github.io/rfcs/3660-crates-io-crate-deletions.html) and
  [crates.io policies](https://crates.io/policies) (deletion rules)
- the HTTP 413 "max upload size is: 10485760" error quoted in a third-party build log
  (via search), for the exact cap
- [crates.io issue #3229](https://github.com/rust-lang/crates.io/issues/3229) (publish
  rate limits)

**GitHub:**

- [Events that trigger workflows / schedule](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule)
- [Triggering a workflow from a workflow (`GITHUB_TOKEN` rule)](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow)
- [Concurrency](https://docs.github.com/en/actions/concepts/workflows-and-actions/concurrency)

**Distribution tools:**

- [cargo-dist book](https://axodotdev.github.io/cargo-dist/book/)
- [cargo-binstall](https://github.com/cargo-bins/cargo-binstall)
- `taiki-e/upload-rust-binary-action` (as cited by the release-plz binaries guide)

**Input reports:** `crates_io_daily_release_train__{cdx,cld,grk,mus,gem}.md` in this
directory.
