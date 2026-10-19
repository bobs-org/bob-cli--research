# Publishing bob-cli with release-plz: daily, CI-gated releases

_Researcher: cld · 2026-10-19 · Repo state: `bobs-org/bob-cli` master @ `bfca3419`_

## TL;DR

- **The idea is sound, but the plan skips steps.** A daily, automated, CI-gated
  release train suits this repo well: about 25 commits/day, 100% conventional
  commits, and a version that has said `0.1.0` since June. The plan as written
  assumes things that are not true yet:
  1. **There is no CI.** The repo has zero GitHub Actions workflows, no branch
     protection, no PRs, and no merge commits in 1,399 commits. "When all CI
     checks are green" has nothing to check today.
  2. **The crate name `bob-cli` is taken on crates.io** by an unrelated AI-agent
     project (v0.3.2, created 2026-03-25). `bob` is taken too. You need a new
     package name. The binary can stay `bob`.
  3. **There is no license.** crates.io refuses a publish without `license` or
     `license-file`, and the public GitHub repo has none either.
  4. **The crate is at 8.8 MiB compressed against a 10 MB hard cap.** It grew
     from 3.3 MiB to 8.9 MiB in the nine days from Oct 10 to Oct 19 (fonts and
     vendored Mermaid).
  5. **The test suite is not hermetic.** In a clean HOME with `TZ=UTC` and no
     `~/.local/bin` on PATH, 5,080 of 5,082 tests pass. 2 fail: one needs
     `~/.config/bob/config.yml`, the other needs `uv` on PATH. A fresh GitHub
     runner would start red.
- **Recommended approach (§8):** keep release-plz and crates.io, but do not use
  release-plz's release-PR flow. Run a **scheduled "release train" workflow**
  once a day in the quiet commit window (about 04:17 ET). It:
  1. Re-runs the full CI suite (Linux and macOS) on the exact master SHA it will
     release.
  2. Runs `release-plz update` and pushes the version and changelog commit to
     master. The push is fast-forward only.
  3. Publishes with `release-plz release`, using crates.io Trusted Publishing
     (OIDC, no stored token).
  4. Attaches prebuilt binaries to the GitHub release, so `cargo binstall` and
     `cargo install-update` stop compiling QuickJS, SQLite and `image` from
     source.

  A once-per-day throttle, a pause switch and a fast-forward-only push make
  "at most once a day, only when green" hold mechanically.
- **Do CI first, as its own milestone.** It pays off even if you never publish.

## 1. Scope and assumptions

The request: publish a package for bob-cli to crates.io (not "cargo.io"), using
release-plz, releasing at most once a day and only when CI is green. Critique
the plan, adjust requirements where justified, and recommend an implementation.

I could not ask questions in this single-turn run, so I assumed the following.
They are listed again as open questions in §9.

- **Main consumers are other people, plus your own non-dev machines.** athena
  and the Mac install bob from source checkouts through `just install` and
  `just install-all`, and track HEAD.
- **The commit workflow stays as it is.** Agents push straight to master with
  `sase stitch`, history stays linear, and there are no PRs.
- **The Mac app keeps tracking bob HEAD.** Bob Mac Capture keeps building
  against bob HEAD, not against releases.

## 2. What the repository looks like today (evidence)

| Fact | Evidence |
|---|---|
| No CI at all | No `.github/` directory, and no history of one (`git log --all -- .github` is empty). `gh api repos/bobs-org/bob-cli/actions/workflows` returns `total_count: 0`. |
| No branch protection, PRs or merges | `branches/master/protection` returns 404 "Branch not protected". `gh pr list --state all` is empty. `git log --merges` finds 0 merges in 1,399 commits. |
| Repo is public with no license | `gh repo view` shows `visibility: PUBLIC, licenseInfo: null`. `cargo package` warns `manifest has no license or license-file`. |
| Package name is taken | crates.io API: `bob-cli` is "CLI app for Bob - a general-purpose AI agent framework" (longcipher/bob), v0.3.2, created 2026-03-25. `bob` is a pkgsrc package builder at v1.0.0. Free names include `bob-obsidian`, `bobsidian`, `bobs-cli`, `bob-vault`, `bob-vault-cli`, `bob-gtd` and `bobctl` (all 404). |
| Binary-name collision | `bob-nvim` (Neovim version manager, about 642k downloads) also installs a `bob` binary. A crates.io user who has it installed hits a cargo "binary already exists" conflict. Your machines are unaffected. |
| Crate size is near the cap | `cargo package`: 956 files, 30.2 MiB raw, **8.8 MiB compressed (9.3 MB `.crate`)**. Compressed by directory: assets 2.7M, scripts 2.7M, src 2.4M, tests 647K, docs 470K. Largest file: `scripts/web_clip/vendor/mermaid.min.js` at 5.5 MB raw. |
| Size is growing fast | Compressed size of the packaged dirs at the last commit before each date: Sep 15 785K → Oct 1 2.2M → Oct 10 3.3M → Oct 19 8.9M. |
| The package already builds standalone | `cargo package` with verification succeeds in 1m55s (debug, 16 cores). The only warning is the missing license. Fonts and scripts are embedded with `include_bytes!`, so the binary is self-contained, which suits prebuilt binaries. |
| Test suite size and runtime | 5,082 tests in 17 test binaries. Clean-env run: 3m00s compile plus about 2.5 min of tests on 16 cores, 5m34s total. A 4-vCPU hosted runner will be several times slower. |
| Two non-hermetic tests | `native::capture::task_blocks::tests::authored_children_and_schedule_log_are_added_in_order` panics at `src/native/capture/task_blocks.rs:567`: "priority levels need …/.config/bob/config.yml". `tests/gkeep_auth.rs:438` `doctor_all_ok_reports_the_checklist` fails with "uv not found on PATH". |
| Tool-dependent tests skip themselves | pandoc, xelatex, zsh and bash tests check for the tool and skip if it is missing (e.g. `tests/cli/highlights/create.rs:1720`). CI on a bare runner silently tests less than your machines do. |
| Commit hygiene fits release-plz | Last 500 subjects: **500/500 conventional**. 272 `feat`, 152 `docs`, 54 `fix`, 8 `refactor`, 7 `chore`, 5 `test`, 1 `perf`, 1 `feat!`. |
| Commit cadence | 10–39 commits/day over the last two weeks. 328 of 341 commits since Oct 5 touch packaged paths. Over the last 30 days the quietest hours are 00:00–06:00 ET (04:00–10:00 UTC), at roughly 4–8 commits per hour-of-day slot in total. |
| A library target exists | `src/lib.rs` exports `runner` and `scripts`. release-plz runs cargo-semver-checks by default on library packages, but this lib is an internal seam for the bins, not an API. |
| Renaming the package touches code | `src/main.rs` and `src/bin/*.rs` call `bob_cli::…`. A new package name changes the default lib crate name unless `[lib] name = "bob_cli"` is pinned. State and cache paths use the literal `"bob-cli"` (`src/native/env.rs:269`, `src/runner.rs:1226`), so they are unaffected. |
| How bob is installed today | `~/.cargo/.crates.toml` lists `bob-cli 0.1.0 (path+file:///home/bryan/projects/github/bobs-org/bob-cli)`. `cargo-update` (`cargo install-update`) is installed, so crates.io-installed tools already have an update path. |
| Version and contract coupling | `bob --version` reports `CARGO_PKG_VERSION`, which has been `0.1.0` since 2026-06-01 (`47f2bd1e`). Decision record `mac-capture-is-a-thin-client`: bob and the Mac app "are installed independently, so the JSON contract must grow additively". The app rejects a different `schema_version`. |

## 3. release-plz facts that shape the design

Sources are the release-plz docs (see §10). The latest CLI is v0.3.173,
released 2026-10-19, about 10 releases in the last six weeks. The project is
very active, so **pin the version**.

- **Two commands do the work.**
  - `release-plz update` bumps the version, writes `CHANGELOG.md` and runs
    `cargo update --workspace`. It first downloads the latest published package
    from the registry and compares it to the local package to find the new
    commits.
  - `release-plz release` publishes every package whose `Cargo.toml` version
    is not yet on the registry, creates a tag (`v{version}` for a
    single-package repo) and creates a GitHub release. It "doesn't edit your
    Cargo.toml files and doesn't push new commits". If everything is already
    published it does nothing.
- **`release-pr` is the idiomatic wrapper.** It runs `update` and opens or
  force-updates a PR on a `release-plz-*` branch. `release_always` (default
  `true`) publishes whenever an unpublished version is present. With `false`,
  it publishes only when the merged commit came from a release PR, which is
  GitHub-only. Squash merges break the "release exactly the PR commit" logic,
  and the docs say to use normal merges.
- **The GitHub Action** accepts only `command: release-pr | release`. There is
  no `update`. It has a `version` input to pin the CLI.
- **Version bumps on 0.x** (from the `next_version` crate): `feat` bumps the
  patch, and a breaking change (`!` or `BREAKING CHANGE:`) bumps the minor.
  `features_always_increment_minor` exists but breaks Cargo's 0.x semver
  convention.
- **`release_commits` (regex) controls whether a bump happens.** Commits that
  don't match still appear in the changelog. Use it to skip days that only
  have docs, test or chore commits.
- **`semver_check` runs cargo-semver-checks for library packages by default.**
- **`git_only = true`** takes versions from git tags instead of the registry
  and never publishes. It is a good rehearsal mode.
- **`max_analyze_commits` is 1000** for a package with no registry release. A
  first release-plz run with no published baseline would try to write a
  changelog from about 1,000 commits.
- **The crates.io name collision is a trap for release-plz.** With the package
  still named `bob-cli`, release-plz would download *longcipher's* `bob-cli`
  0.3.2 as the "previous release", compute a version above 0.3.2, and then
  fail at `cargo publish` on ownership.
- **Trusted publishing is built in.** release-plz does the crates.io OIDC
  exchange itself. It needs `id-token: write` and no `CARGO_REGISTRY_TOKEN`.
  The first publish of a new crate must be manual, which is a crates.io
  limitation.
- **`GITHUB_TOKEN` cannot trigger other workflows.** CI won't run on a release
  PR opened with it, and `on: release` or `on: push: tags` workflows won't fire
  for tags it creates. The fix is a PAT or a GitHub App token, or doing
  follow-up work in the same workflow.
- **release-plz does not build binaries.** The docs recommend a separate job,
  for example `taiki-e/upload-rust-binary-action` on a target matrix.
- **Schedules are supported.** The docs show a `schedule` trigger with a weekly
  cron example. They give no cadence recommendation.

## 4. crates.io constraints

- **Size: "crates.io currently has a 10MB size limit on the `.crate` file."**
  You are at 9.3 MB. Per-crate increases are reportedly granted on request to
  help@crates.io, but I could not verify that. Treat the limit as hard and
  budget against it.
- **Permanence.** "a publish is generally permanent. The version can never be
  overwritten, and the code cannot be deleted". Yanking does not delete code.
  Under the policy that came out of RFC 3660, an owner can delete a crate only
  within 72 hours of publishing, or if it has a single owner, no reverse
  dependencies and fewer than 500 downloads per month of its life. Anything in
  `tests/fixtures/**` that ships is effectively public forever. It is already
  public on GitHub, but GitHub history can be rewritten and crates.io cannot.
- **Required metadata:** `description` (present) and `license` or
  `license-file` (missing).
- **Rate limits** are roughly one publish per minute after a burst of about 30
  for existing crates. That is irrelevant at one release a day.
- **Trusted Publishing** has been GA since July 2025. You register owner,
  repo, workflow file and optional environment in the crate's settings. The
  token is short-lived and revoked when the job ends. The first version still
  needs a normal API token, and as of this research no 2026 change lifts that.
- **Storage is shared.** Each release adds about 7–9 MB of immutable storage
  and CDN replication on a shared, donated service, plus a docs.rs build
  (docs.rs builds crates that have a lib target). At about 300 releases a year
  that is about 2–3 GB a year for a tool with very few users. That is not
  against policy, but it argues for trimming the package and for releasing
  only on days with user-visible changes.

## 5. Critique: is this a good idea?

### What is good about it

1. **It forces CI into existence.** About 25 agent-authored commits land on
   master every day with no server-side verification. The two
   environment-dependent tests in §2 are exactly what CI exists to catch, and
   macOS-only code (`cfg(target_os = "macos")` with `rusqlite`/`plist`) is
   never checked off the Mac.
2. **It makes versions mean something.** Every install has reported `0.1.0`
   for 4.5 months. Daily versions give `bob --version` a value you can
   compare. They also give you rollback points ("which day's release broke
   reconcile?"), a changelog, and something for Bob Mac Capture or bug reports
   to cite.
3. **The repo already fits release-plz.** Commit discipline is perfect, and
   release-plz's changelog and next-version logic will produce good output
   without tuning.
4. **The cadence fits the commit rate.** Releasing per commit would mean 25
   releases a day, and weekly would bundle about 175 commits. Daily gives
   readable changelogs of about 25 lines and bisection-friendly releases.

### What is wrong or risky as stated

1. **"When all CI checks are green" is undefined** until CI exists and covers
   both platforms. "Green" also has to mean green *for the exact commit being
   released*. With 25 pushes a day, "master was green at some point today" is
   not the same thing.
2. **release-plz's default release-PR flow fits this repo badly.**
   - Running `release-pr` on push means 25 force-pushes a day to a permanently
     open bot PR.
   - Getting CI to run on that PR needs a PAT or GitHub App.
   - The safe merge strategy (a merge commit) breaks a history that has never
     had a merge.
   - Auto-merge needs required status checks. Under branch protection those
     also block your direct pushes unless you add bypass rules.
   - Nobody is going to review a daily PR in an agent-driven repo, so the
     release PR is ceremony here.
3. **The name.** You cannot publish as `bob-cli`. A different crate name means
   README and install changes, `[lib] name` pinning, and a one-time
   `cargo uninstall bob-cli` on each machine. Without that, the next
   `just install` stops with "binary `bob` already exists … as part of
   `bob-cli`", and the README forbids `--force`.
4. **Size will break publishing without warning.** One more font family or
   vendored JS bundle pushes the crate over 10 MB, and the daily release fails
   at `cargo publish` days after the commit that caused it. You need a budget
   check in per-push CI.
5. **Installing from source is heavy.** `cargo install` builds QuickJS (C),
   `image`, `lopdf` and, on macOS, bundled SQLite. That takes minutes per
   machine per day for anyone using `cargo install-update`. Daily releases
   without prebuilt binaries are a poor experience.
6. **Crates.io adds little for your own machines.** athena and the Mac build
   from checkouts at HEAD. Bob Mac Capture is built from HEAD and depends on
   the newest bob JSON fields. Releases will always lag HEAD by up to a day,
   so you won't install them on your dev hosts. The real crates.io audience is
   other people and possibly apollo. Be honest that this is mostly
   distribution and hygiene, not something you need.
7. **License and assets.** You must choose a license for your own code. The
   crate also ships OFL-1.1 fonts and MIT JS (Mermaid, Defuddle). Their
   notices are in-tree (`assets/print_fonts/OFL.txt` and the
   `scripts/web_clip/{fonts,vendor}` license files) and must stay in the
   package.
8. **The `!` marker becomes meaningful.** Only 1 `!` commit appeared in the
   last month, yet capture and JSON contract changes are frequent. Once
   versions are published, agents must mark CLI or JSON contract breaks with
   `!` so 0.x minor bumps carry signal.

### Verdict

**Yes, do it, in the right order and in a shape that fits a direct-to-master,
agent-driven repo.** Most of the value comes from what the plan forces: CI,
hermetic tests, real versions and a changelog. crates.io itself is a modest
add-on that is worth it mainly for `cargo binstall` and `cargo install-update`
users and for discoverability. It carries real one-way-door costs: permanence,
the name, size and a license. If you find you don't want outside users, run
the same pipeline in `git_only` mode and skip crates.io entirely (Option D).

## 6. Adjusted requirements (called out explicitly)

| # | Your requirement | Adjusted requirement | Why |
|---|---|---|---|
| R1 | Publish a package for bob-cli (crates.io) | Publish to crates.io **under a new package name** (e.g. `bob-obsidian`). The binary stays `bob` and the lib name stays `bob_cli`. | `bob-cli` and `bob` are taken. A name mismatch is normal: `fd` ships as `fd-find`. |
| R2 | Use release-plz | Use the release-plz **CLI** (`update` + `release`) in one scheduled workflow, **not the release-PR flow** | No PRs, linear history and agent pushes make the release PR ceremony. The CLI keeps release-plz's version, changelog, publish and tag logic. |
| R3 | At most once a day | At most once per **America/New_York calendar day**, cut in the quiet window (about 04:17 ET), **only if there are user-visible changes** (`feat`/`fix`/`perf`/`revert` or any `!`). Add a pause switch, plus a manual `force` input for hotfixes. | Makes the throttle precise and avoids docs-only releases. Hotfixes need an escape hatch. |
| R4 | When all CI checks are green | **Create CI first.** "Green" means fmt, clippy, the full test suite on **Linux and macOS** and a package/size check, all **run on the exact SHA being released**, by re-running CI inside the release workflow. | CI doesn't exist yet. Reading cross-workflow status for a moving master is racy, and re-running costs one CI run a day. |
| R5 | (new) | Tests must be **hermetic** before CI is required. Fix the 2 failures, and install `uv` (and optionally zsh, pandoc, TeX, poppler) on gate runners so self-skipping tests actually run. | Otherwise CI is red from day one, or quietly weaker than local runs. |
| R6 | (new) | **Prebuilt binaries** (Linux x86_64, macOS arm64, plus x86_64 if needed) attached to each GitHub release, with `[package.metadata.binstall]` | Building from source is slow and needs a C toolchain. binstall and cargo-update use the binaries automatically. |
| R7 | (new) | **Trusted Publishing** with no stored crates.io token, behind a `release` GitHub environment limited to master. The first publish is manual. | Removes the long-lived secret. The manual first publish is required by crates.io. |
| R8 | (new) | Add a **package size budget** (fail above 9 MiB) to per-push CI, and trim `include` to what the build needs | You are at 8.8 MiB of a 10 MB cap and growing. |
| R9 | (new) | **Choose a license** (e.g. `MIT OR Apache-2.0`) and keep third-party notices in the package | crates.io requires a license, and the public repo currently has none. |
| R10 | (dropped) | No per-release human review and no cargo-semver-checks (`semver_check = false`) | Review doesn't happen in practice, and the lib API is internal. Semver checks would add minutes and false "breaking" bumps. |

## 7. Design options

| | **A. Canonical release-PR** | **B. Scheduled release train (recommended)** | **C. Event-driven (`workflow_run`)** | **D. Git-only (no crates.io)** |
|---|---|---|---|---|
| How it works | Cron `release-pr` opens or updates the PR once a day. It is merged by you or by auto-merge. `release` runs on merge with `release_always=false`. | Cron runs the full CI on HEAD, then `release-plz update`, a fast-forward push, and `release-plz release`, with binaries in the same workflow. | On every green CI run on master: if nothing was released today and HEAD is the SHA that went green, release it. | Same as B but with `git_only=true, publish=false`: tags, GitHub releases and binaries only. |
| Fits a no-PR, linear repo | ✗ Needs merge commits, a permanent bot PR, and an App or PAT for PR CI | ✓ One bot commit a day, linear | ✓ | ✓ |
| Exact-SHA gating | ✓ With merge commits it publishes the PR commit | ✓ CI re-runs on the released SHA | ✓ Uses the SHA that just went green | ✓ |
| Extra secrets or setup | GitHub App or PAT, ruleset with bypass, "allow Actions to create PRs" | None (GITHUB_TOKEN plus OIDC) | None, but filters needed so the gate doesn't count its own checks | None |
| Human checkpoint | ✓ Optional | ✗ Pause switch instead | ✗ | ✗ |
| Release time | Whenever it is merged | Predictable (~04:17 ET) | First green run after midnight, during agent hours, so push races are likelier | Predictable |
| Reversibility | Permanent (crates.io) | Permanent (crates.io) | Permanent (crates.io) | Fully reversible |
| Install story for others | crates.io + binstall | crates.io + binstall | crates.io + binstall | `cargo install --git … --tag` (builds from source) or manual download. binstall `--git` support is unconfirmed. |

Tooling alternatives I considered and rejected:

- **cargo-dist** is maintained (v0.33.0, 2026-09-11). It generates its own
  tag-triggered release workflow and wants to own the GitHub Release and
  installers. Pairing it with release-plz needs a PAT or App so the tag push
  triggers dist, plus turning off one side's GitHub-release creation. For
  three targets, `upload-rust-binary-action` inside the same workflow is
  simpler. Revisit dist if you want curl-pipe-sh or Homebrew installers.
- **release-please** needs manifest files and treats a package as published
  only when a git tag exists. It is not registry-aware.
- **cargo-release** is CLI-first, has no changelog support, and would need
  custom version logic.
- **None of the three** offers release-plz's mix of conventional commits,
  registry diffing and git-cliff.

**Recommendation: B.** Its one weakness is that a release attempt fails if an
agent pushes during the roughly 20-minute gate. The quiet window plus a second
cron slot handles that, and the throttle makes retries safe. Choose **A** only
if you later move to PRs or branch protection. Choose **D** first if you can't
settle the license or name yet, then flip to B. B and D differ only in
`release-plz.toml` and the publish step.

## 8. Recommended solution

### Phase 0: decisions (you)

1. **Crate name.** Suggestions, all free on 2026-10-19: `bob-obsidian` (says
   what Bob is), `bobsidian`, `bobs-cli` (mirrors `bobs-org`) or `bob-vault`.
   Reserve it with the first manual publish (Phase 3).
2. **License.** For example `MIT OR Apache-2.0` for your code, keeping the
   bundled OFL and MIT notices. Add `LICENSE-MIT` and `LICENSE-APACHE`.
3. **Mac architecture** for binaries: arm64 only, or Intel too? This depends on
   Kelly's MacBook Pro.

### Phase 1: CI (worth it even if you never publish)

- **Fix the two hermeticity bugs.**
  - `task_blocks` test: give the test its own config or an XDG override,
    instead of reading `~/.config/bob/config.yml`.
  - `gkeep_auth` doctor test: stub `uv` on PATH inside the test, the way other
    gkeep tests stub tools, or have CI install uv.
- **Pin the toolchain** (`rust-toolchain.toml` or explicit CI inputs) and set
  `rust-version` to match. Edition 2024 needs at least 1.85. Otherwise a new
  stable clippy lint can turn master red, which silently stops releases.
- **`.github/workflows/ci.yml`** (sketch, untested):

```yaml
name: CI
on:
  push: { branches: [master] }
  pull_request:
  workflow_dispatch:
  workflow_call:            # release.yml re-runs CI on the exact SHA it will ship
    inputs:
      sha:  { type: string,  required: true }
      full: { type: boolean, default: true }   # macOS + optional tools

jobs:
  lint:
    runs-on: ubuntu-latest
    concurrency: { group: "lint-${{ github.event_name }}-${{ github.ref }}", cancel-in-progress: true }
    steps:
      - uses: actions/checkout@v6
        with: { ref: "${{ inputs.sha || github.sha }}" }
      - uses: dtolnay/rust-toolchain@master
        with: { toolchain: "1.95.0", components: "rustfmt, clippy" }   # pin; bump deliberately
      - uses: Swatinem/rust-cache@v2
      - uses: taiki-e/install-action@v2
        with: { tool: just }
      - run: just fmt && just lint && just check-scripts   # same gate as local `just check`

  test:
    strategy:
      fail-fast: false
      matrix:
        os: ${{ inputs.full && fromJSON('["ubuntu-latest","macos-latest"]') || fromJSON('["ubuntu-latest"]') }}
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v6
        with: { ref: "${{ inputs.sha || github.sha }}" }
      - uses: dtolnay/rust-toolchain@master
        with: { toolchain: "1.95.0" }
      - uses: Swatinem/rust-cache@v2
      - uses: astral-sh/setup-uv@v6
      - if: inputs.full && runner.os == 'Linux'      # make self-skipping tests actually run at release time
        run: sudo apt-get update && sudo apt-get install -y zsh pandoc texlive-xetex poppler-utils
      - run: cargo test --locked --no-fail-fast

  package:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
        with: { ref: "${{ inputs.sha || github.sha }}" }
      - uses: dtolnay/rust-toolchain@master
        with: { toolchain: "1.95.0" }
      - uses: Swatinem/rust-cache@v2
      - run: cargo package --locked            # verifies the tarball builds on its own
      - name: crate size budget (crates.io hard cap is 10 MB)
        run: |
          size=$(stat -c %s target/package/*.crate); echo "crate: $size bytes"
          [ "$size" -le 9437184 ] || { echo "::error::crate is $size bytes (> 9 MiB budget)"; exit 1; }
```

- Standard hosted runners, including macOS, are free for public repos. On
  4-vCPU runners, expect very roughly 15–25 minutes per cold run and less with
  `rust-cache`. Extrapolating from the 5m34s / 16-core local run, this is an
  estimate, not a measurement.
- Let per-push CI bake for about a week. The red-rate it reveals decides how
  often the daily train will skip.

### Phase 2: package hygiene (`Cargo.toml` and repo)

```toml
[package]
name = "bob-obsidian"            # placeholder: whatever Phase 0 picks; binary stays `bob`
version = "0.2.0"                # first public version; 0.1.0 = "unversioned dev builds since June"
license = "MIT OR Apache-2.0"    # Phase 0 decision
rust-version = "1.85"            # >= edition-2024 minimum; set to what CI proves
readme = "README.md"
keywords = ["obsidian", "gtd", "pomodoro", "notes", "cli"]
categories = ["command-line-utilities"]
include = [                      # drop /tests/**, /docs/**, /justfile (~1.1 MiB compressed)
    "/Cargo.toml", "/Cargo.lock", "/README.md", "/LICENSE-*",
    "/src/**", "/assets/**", "/scripts/**",   # assets + scripts are include_bytes!'d
]

[lib]
name = "bob_cli"                 # keep `bob_cli::run_bob()` etc. compiling after the rename

[package.metadata.binstall]      # must match the archive names produced in release.yml
pkg-url = "{ repo }/releases/download/v{ version }/bob-{ target }{ archive-suffix }"
bin-dir = "{ bin }{ binary-ext }"
pkg-fmt = "tgz"
```

- **Docs links still work.** crates.io rewrites relative README links against
  `repository`, so `docs/*.md` links keep working without shipping `docs/`.
- **Trim `scripts/**` further.** Ship only the embedded subset, not `dev/`,
  `migrations/` or `install_all`.
- **Rename migration:** run `cargo uninstall bob-cli` once on athena, apollo
  and the Mac before the next `just install`. Update README "Installation" and
  `scripts/install_all`.
- **Agent guidance.** Propose these through `/sase_memory_write`, or put them
  in AGENTS.md:
  - Agents never edit `version` or `CHANGELOG.md`.
  - CLI or JSON contract breaks get a `!` in the commit subject.

### Phase 3: first publish (manual, one time)

1. Seed `CHANGELOG.md` with a short "0.2.0: first public release" entry, so
   release-plz never tries to summarize 1,000 historical commits.
2. Create a crates.io API token scoped `publish-new` for the chosen name. From a
   clean checkout at a green SHA, run `cargo publish --locked`. Tag `v0.2.0`.
3. Revoke the token.
4. Register Trusted Publishing in the crate's settings: owner `bobs-org`, repo
   `bob-cli`, workflow `release.yml`, environment `release`. If crates.io
   offers a "trusted publishing only" toggle for the crate, enable it. I did
   not confirm that such a toggle exists.
5. Create the GitHub environment `release` and limit deployments to `master`.

### Phase 4: the daily train

`release-plz.toml`:

```toml
[workspace]
semver_check = false              # src/lib.rs is an internal seam, not a public API
dependencies_update = false       # default; deps move via normal commits
git_release_enable = true         # tag vX.Y.Z + GitHub release (binaries attach to it)
publish_timeout = "15m"
# Only bump when something user-visible landed; docs/test/chore-only days skip.
release_commits = "^(feat|fix|perf|revert)(\\(.+\\))?!?:|^[a-z]+(\\(.+\\))?!:"

[changelog]
# git-cliff syntax; group by type and drop noise (verify field names against the docs)
commit_parsers = [
  { message = "^chore\\(release\\)", skip = true },
  { message = "^feat", group = "Features" },
  { message = "^fix", group = "Fixes" },
  { message = "^perf", group = "Performance" },
  { message = "^docs", group = "Documentation" },
  { message = "^(test|chore|ci|style|refactor)", skip = true },
]
```

`.github/workflows/release.yml` (sketch, untested. Check flag names with
`release-plz release --help` and the action READMEs before relying on it):

```yaml
name: Release
on:
  schedule:
    - cron: "17 8 * * *"     # 04:17 EDT / 03:17 EST: quietest commit window
    - cron: "47 10 * * *"    # retry slot; the throttle makes it a no-op after a release
  workflow_dispatch:
    inputs:
      force: { description: "Bypass once-per-day throttle (hotfix)", type: boolean, default: false }

concurrency: { group: release, cancel-in-progress: false }   # never cancel a release mid-flight
permissions: { contents: read }

jobs:
  plan:
    runs-on: ubuntu-latest
    outputs: { sha: "${{ steps.p.outputs.sha }}", go: "${{ steps.p.outputs.go }}" }
    steps:
      - id: p
        env:
          GH_TOKEN: ${{ github.token }}
          REPO: ${{ github.repository }}
          FORCE: ${{ inputs.force || false }}
          PAUSED: ${{ vars.RELEASES_PAUSED || 'false' }}       # kill switch: repo variable
        run: |
          set -euo pipefail
          sha=$(gh api "repos/$REPO/commits/master" --jq .sha)
          author=$(gh api "repos/$REPO/commits/$sha" --jq .commit.author.name)
          today=$(TZ=America/New_York date +%F)
          last=$(gh release list -R "$REPO" -L 1 --json createdAt --jq '.[0].createdAt // empty')
          last_day=""; [ -n "$last" ] && last_day=$(TZ=America/New_York date -d "$last" +%F)
          go=true
          [ "$PAUSED" = "true" ] && go=false
          [ "$author" = "github-actions[bot]" ] && go=false                 # nothing new since last train
          [ "$last_day" = "$today" ] && [ "$FORCE" != "true" ] && go=false   # at most once per day
          echo "sha=$sha" >> "$GITHUB_OUTPUT"; echo "go=$go" >> "$GITHUB_OUTPUT"

  ci:                                    # "all CI checks green" for the exact SHA we ship
    needs: plan
    if: needs.plan.outputs.go == 'true'
    uses: ./.github/workflows/ci.yml
    with: { sha: "${{ needs.plan.outputs.sha }}", full: true }

  release:
    needs: [plan, ci]
    runs-on: ubuntu-latest
    environment: release                 # trusted-publisher binding + master-only deployments
    permissions: { contents: write, id-token: write }
    outputs: { tag: "${{ steps.publish.outputs.tag }}" }
    steps:
      - uses: actions/checkout@v6
        with: { ref: "${{ needs.plan.outputs.sha }}", fetch-depth: 0 }
      - uses: dtolnay/rust-toolchain@master
        with: { toolchain: "1.95.0" }
      - uses: taiki-e/install-action@v2
        with: { tool: release-plz@0.3.173 }      # pin; bump via Dependabot/Renovate
      - id: bump
        run: |
          set -euo pipefail
          release-plz update
          if [ -z "$(git status --porcelain)" ]; then echo "changed=false" >> "$GITHUB_OUTPUT"; exit 0; fi
          version=$(cargo metadata --no-deps --format-version 1 | jq -r '.packages[0].version')
          git config user.name  "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
          git add -A && git commit -m "chore(release): v$version"
          # Fast-forward only. If an agent pushed during the gate this is rejected,
          # nothing is published, and the retry slot / tomorrow tests the new HEAD.
          git push origin "HEAD:refs/heads/master"
          echo "changed=true" >> "$GITHUB_OUTPUT"
      - if: steps.bump.outputs.changed == 'true'
        id: auth
        uses: rust-lang/crates-io-auth-action@v1     # OIDC -> short-lived crates.io token
      - if: steps.bump.outputs.changed == 'true'
        id: publish
        env:
          CARGO_REGISTRY_TOKEN: ${{ steps.auth.outputs.token }}
          GITHUB_TOKEN: ${{ github.token }}
        run: |
          set -euo pipefail
          release-plz release --git-token "$GITHUB_TOKEN" -o json | tee release.json
          echo "tag=$(jq -r '.releases[0].tag // empty' release.json)" >> "$GITHUB_OUTPUT"

  binaries:                              # same workflow, so the GITHUB_TOKEN no-trigger rule doesn't bite
    needs: release
    if: needs.release.outputs.tag != ''
    strategy:
      fail-fast: false
      matrix:
        include:
          - { os: ubuntu-22.04, target: x86_64-unknown-linux-gnu }   # older glibc baseline
          - { os: macos-latest, target: aarch64-apple-darwin }
          - { os: macos-latest, target: x86_64-apple-darwin }        # only if an Intel Mac matters
    runs-on: ${{ matrix.os }}
    permissions: { contents: write }
    steps:
      - uses: actions/checkout@v6
        with: { ref: "${{ needs.release.outputs.tag }}" }
      - uses: dtolnay/rust-toolchain@master
        with: { toolchain: "1.95.0", targets: "${{ matrix.target }}" }
      - uses: taiki-e/upload-rust-binary-action@v1
        with:
          bin: bob,bob_pomodoro,bob_notify,tmux_bob_pomodoro
          target: ${{ matrix.target }}
          archive: bob-$target                       # matches the binstall pkg-url above
          ref: refs/tags/${{ needs.release.outputs.tag }}
          checksum: sha256
          token: ${{ github.token }}
```

Why this shape:

- **Exact-SHA gate.** The workflow tests the SHA it ships by calling `ci.yml`
  as a reusable workflow. It never has to decide whether some other run's
  checks count, and that run can't be cancelled by later pushes. The gate can
  also be *stricter* than per-push CI: macOS plus the optional tools.
- **Ordering.** The bump commit is pushed before publishing. If the push is
  rejected, nothing is published. If publishing then fails, master already
  carries the unpublished version, and the next `release-plz release` run
  publishes it.
- **Never publish a commit that is off master.** release-plz finds "commits
  since the last release" by diffing the local package against the registry
  package. Off-master release commits would confuse that walk.
- **No PAT or GitHub App.** The binary jobs run in the same workflow, and
  nothing needs to trigger another workflow.
- **"At most once a day" is enforced by data, not hope.** The throttle reads
  the last GitHub release's date in ET. Two cron slots and manual reruns can't
  double-release, and `force` is the only bypass.

### Phase 5: rehearse, then go live

1. **Rehearse first.** Run release.yml for 3–5 days with
   `git_only = true, publish = false` (Option D) on a throwaway tag prefix, or
   with the push and publish steps replaced by `git diff` plus
   `cargo publish --dry-run`. Check the version math, changelog grouping,
   throttle and binaries.
2. **Flip to live.** Remove the rehearsal settings and watch the first two
   real releases. Confirm `cargo binstall <name>` on a scratch box picks up
   the prebuilt archive.
3. **Runbooks:**
   - **Pause:** set the repo variable `RELEASES_PAUSED=true`.
   - **Bad release:** run `cargo yank --version X.Y.Z`, then
     `git revert` → push → `workflow_dispatch` with `force: true`.
   - **Size breach:** CI fails before the train does. Trim or externalize
     assets.
4. **Reopen criteria.** After about a month, check crates.io download counts.
   If nobody but you installs it:
   - drop to `git_only` (reversible), or
   - drop crates.io to weekly releases while GitHub releases stay daily.

## 9. Open questions for Bryan

1. **Audience.** Who should install from crates.io: other people, apollo, the
   Mac? This decides between B and D, and whether binaries for Intel macOS
   are needed.
2. **Name.** `bob-obsidian`, `bobsidian`, `bobs-cli`, `bob-vault` or another?
3. **License.** `MIT OR Apache-2.0`, or something else?
4. **Release hour.** Is about 04:17 ET right, or would you rather releases
   follow your evening wrap-up?
5. **Hotfixes.** Do you want the `force` override at all, or is "strictly at
   most once a day" a hard rule?

## 10. Sources

Repository evidence: commands run in this workspace on 2026-10-19:

- `gh repo view`, `gh api …/actions/workflows`, `…/branches/master/protection`
- `cargo package --list`, `cargo package` with and without `--no-verify`
- a scrubbed-environment `cargo test --no-fail-fast --locked`
  (HOME=empty temp dir, TZ=UTC, PATH without `~/.local/bin`)
- `git log` statistics
- the crates.io API (`/api/v1/crates/<name>`) for name availability
- the decision record `decisions:mac-capture-is-a-thin-client`

External:

- release-plz docs:
  - [config](https://release-plz.dev/docs/config)
  - [quickstart](https://release-plz.dev/docs/github/quickstart)
  - [token](https://release-plz.dev/docs/github/token)
  - [advanced (schedule)](https://release-plz.dev/docs/github/advanced)
  - [usage/release](https://release-plz.dev/docs/usage/release)
  - [usage/release-pr](https://release-plz.dev/docs/usage/release-pr)
  - [usage/update](https://release-plz.dev/docs/usage/update)
  - [GitHub action input](https://release-plz.dev/docs/github/input)
  - [GitHub action output](https://release-plz.dev/docs/github/output)
  - [releasing binaries](https://release-plz.dev/docs/extra/releasing-binaries)
  - [semver-check](https://release-plz.dev/docs/semver-check)
  - [FAQ](https://release-plz.dev/docs/faq)
  - [why release-plz](https://release-plz.dev/docs/why)
- [release-plz releases](https://github.com/release-plz/release-plz/releases)
  (v0.3.173, 2026-10-19)
- [next_version crate docs](https://docs.rs/next_version/latest/next_version/)
  (0.x bump rules)
- Cargo book:
  [publishing](https://doc.rust-lang.org/cargo/reference/publishing.html)
  (10 MB limit, permanence, yank) and
  [manifest](https://doc.rust-lang.org/cargo/reference/manifest.html)
  (license and description required, include semantics)
- Trusted publishing:
  [crates.io development update, July 2025](https://blog.rust-lang.org/2025/07/11/crates-io-development-update-2025-07)
  (first release must be manual) and
  [Simon Willison's note](https://simonwillison.net/2025/Jul/12/cratesio-trusted-publishing)
- Crate deletion:
  [RFC 3660](https://rust-lang.github.io/rfcs/3660-crates-io-crate-deletions.html)
  and the [crates.io policies](https://crates.io/policies) (72 h /
  500-downloads-per-month deletion rule)
- Publish rate limits:
  [crates.io issue #3229](https://github.com/rust-lang/crates.io/issues/3229)
  and the
  [users.rust-lang.org thread](https://users.rust-lang.org/t/i-may-have-messed-up-with-crates-io/86567)
  (about 1/min, burst 30; dated)
- [GitHub Actions pricing update, Dec 2025](https://github.blog/changelog/2025-12-16-coming-soon-simpler-pricing-and-a-better-experience-for-github-actions/)
  (public-repo hosted runners stay free)
- cargo-dist: [book](https://axodotdev.github.io/cargo-dist/book/) and
  [releases](https://github.com/axodotdev/cargo-dist/releases) (v0.33.0,
  2026-09-11)
- cargo-binstall: [project page](https://github.com/cargo-bins/cargo-binstall)
  (crates.io-metadata lookup, `pkg-url` templates, cargo-update integration)
- binstall `--git` support: unconfirmed. See the
  [mise cargo backend docs](https://mise.jdx.dev/dev-tools/backends/cargo.html),
  which route git sources to plain `cargo install`.

Unverified items, flagged inline:

- exact `release-plz release` token flag names
- `upload-rust-binary-action` input names
- concurrency semantics inside reusable workflows
- a crates.io "trusted-publishing-only" toggle
- per-crate size-limit increases
