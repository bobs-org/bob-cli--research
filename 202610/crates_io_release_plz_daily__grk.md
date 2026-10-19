# Daily crates.io publishing for bob-cli with release-plz

- **Researcher:** `grk` (independent swarm member)
- **Date:** 2026-10-19
- **Question:** How should bob-cli start publishing a Cargo registry package with release-plz, at most once a day, only when CI is green? Is that a good idea, and what should change?
- **Registry name:** crates.io (there is no cargo.io registry)

## Verdict

Automating **version bumps, changelogs, git tags, and GitHub Releases** from the existing Conventional Commits history is a good idea. release-plz is the right tool for that job.

Publishing **to crates.io as the primary distribution channel**, on a daily timer, is a weak fit for this repository as it stands. The crate name `bob-cli` is already taken. The packaged tree is 30 MiB uncompressed and about 8.9 MiB gzipped against a 10 MiB crates.io cap. There is no license, no GitHub Actions workflow, no git tag, and no branch protection. Install today is `just install` / `cargo install --git`. The useful public artifact is a **prebuilt `bob` binary**, not a source crate that every user recompiles with QuickJS C bindings and a pile of embedded fonts.

**Recommended solution:** build GitHub Actions CI first; then use release-plz with `release_always = false` to cut at most one GitHub Release per green day; attach binaries with `dist` (cargo-dist) or `taiki-e/upload-rust-binary-action`; treat crates.io as an optional later step under a new package name (`bobs-cli`), after a license, a slimmer `package.include`, a size gate, and a one-time manual first publish.

---

## Critique of the proposed plan

The plan as stated is: publish a cargo.io/crates.io package for bob-cli using release-plz, at most once a day, when all CI checks are green.

### What is sound

- **Cadence cap.** This repo lands on the order of 10–40 commits per calendar day (341 commits in the 14 days before 2026-10-19). Default release-plz (`release_always = true`, run on every push to the default branch) would try to publish a new crates.io version per merge. Versions are permanent. A daily cap is the correct instinct.
- **Green-CI gate.** Publishing a yanked-or-broken CLI is worse than skipping a day. Gating on CI is right.
- **release-plz as the releaser.** The git log already speaks Conventional Commits (`feat:`, `fix:`, `docs:`, `feat(capture)!:`). release-plz is built for that dialect: it maintains one rolling Release PR, bumps `Cargo.toml`, writes a Keep-a-Changelog file via git-cliff, tags, creates a GitHub Release, and can run `cargo publish`.
- **Wanting an install path other than a local checkout.** `just install` and `cargo install --git git@github.com:bobs-org/bob-cli.git` both assume a Rust toolchain and, for the git form, SSH GitHub access. A published artifact is a real improvement for extra machines and for anyone who is not Bryan.

### What is a poor fit

- **The registry name in the question is wrong, and the crate name is taken.** The registry is [crates.io](https://crates.io/). The package name `bob-cli` (equivalent to `bob_cli` — crates.io treats hyphen and underscore as the same crate) has been owned since 2026-03-25 by a different project, “CLI app for Bob - a general-purpose AI agent framework” ([longcipher/bob](https://github.com/longcipher/bob), newest 0.3.2, binary name `bob-cli`, 85 downloads). First-come-first-serve; a publish of *this* `bob-cli` will be rejected. `cargo install bob-cli` already installs that other tool.
- **There is no CI to be green.** The public GitHub repo `bobs-org/bob-cli` has Actions enabled and zero workflow files. The in-tree release checklist is a local `just check` / `just package-list` / `just install-smoke` ritual. “When all CI checks are green” currently means “when Bryan’s laptop said so.”
- **crates.io is a source archive, this is an application.** `cargo publish` uploads a `.crate` tarball. Users of `cargo install <name>` compile it. This package embeds `scripts/web_clip/vendor/mermaid.min.js` (5.2 MiB), print fonts under `assets/print_fonts/` (about 5.7 MiB), and compiles `rquickjs` 0.12.1 (a C library; missing `clang` has been enough to fail other rquickjs dependents). That is a 10+ minute source build with native toolchain needs, every install, on every machine. Prebuilt GitHub Release binaries plus `cargo binstall` (or a dist installer script) match how ripgrep, fd, just, and dist itself are consumed.
- **The `.crate` is already near the hard cap.** `cargo package --list` currently yields 954 files / 30.15 MiB raw. A tar.gz of those files is **8.85 MiB**. crates.io’s limit is **10 MiB** for the `.crate` file ([Cargo Book: Publishing](https://doc.rust-lang.org/cargo/reference/publishing.html)). `package.include` still ships `tests/**` (4.0 MiB) and `docs/**` (1.3 MiB), which `cargo install` does not need. One more font, a larger mermaid, or a fattier test fixture blows the cap. Publish would start succeeding and then start failing.
- **Metadata blockers.** `Cargo.toml` has `description` and `repository`, and no `license` / `license-file`, `authors`, `readme`, `keywords`, `categories`, or `rust-version`. crates.io requires a license field. GitHub `licenseInfo` is null. There is no `LICENSE` file in the tree. Vendored OFL fonts and MIT mermaid/defuddle files are already in-tree; the crate’s own license still has to be declared.
- **A public 0.1.0 daily dump of a personal vault CLI.** bob-cli’s contracts assume Bryan’s vault layout, Bob plugins, SASE listen, `pass`, Chrome/Playwright, XeLaTeX, and sibling checkouts of `bob-plugins` / `bob-mac-capture`. crates.io discovery of “bob-cli” already points at an AI-agent CLI. Daily versions of an unstable 0.x application create a permanent public history of every experiment. That is a cost, not a benefit, until there is an audience that installs from the registry.
- **release-plz’s default is “publish on every mainline push.”** The docs warn about `release_always` (default `true`) and squash-merge races. For this repo the default is the failure mode the “once a day” requirement is trying to prevent.

### Would I take a different approach?

Yes. I would invert the stack:

1. Make **CI real** on GitHub Actions (this is the prerequisite for any green-CI gate).
2. Use release-plz to produce **at most one git tag + GitHub Release per green day**, with `release_always = false`.
3. Attach **prebuilt binaries** to that GitHub Release (`dist`, or taiki-e’s upload action). That is the public install path.
4. Add crates.io later, under a free name, if `cargo install <name> --locked` is still wanted after the binary path exists.

release-plz stays. crates.io becomes optional. Daily remains. Green CI remains, and starts existing.

---

## Requirement adjustments

These change the original request. Each is justified by evidence in this repo or by crates.io/release-plz rules.

| # | Original | Adjustment | Why |
|---|----------|------------|-----|
| A | “cargo.io package” | Target **crates.io**, or skip the registry | There is no cargo.io. |
| B | Package name `bob-cli` | Rename the *package* (keep the `bob` binary) to a free name, recommended **`bobs-cli`** | `bob-cli` / `bob_cli` is taken. `bob` is a different crate (pkgsrc builder). Free names checked 2026-10-19: `bobs-cli`, `bob-obsidian`, `bob-obsidian-cli`, `bobcli`, `bob-gtd`, `obsidian-bob`. |
| C | “when all CI checks are green” | **Create** GitHub Actions CI, then gate on it. Required checks on `master` do not exist today (branch protection 404). | Vacuous otherwise. |
| D | release-plz publishes to crates.io from day one | **Phase 1:** release-plz in `git_only = true` (tags + GitHub Releases, no `cargo publish`). **Phase 3:** crates.io after name/license/size work. | Name taken, 10 MiB budget, no license, first trusted-publish version cannot use OIDC. |
| E | At most once a day | Keep. Implement as **`release_always = false` plus a rolling Release PR**, merged at most daily (cron or human), never as publish-on-push. | Matches release-plz’s designed two-job workflow. Avoids 10–40 versions/day. |
| F | Source crate as the install story | Prefer **GitHub Release binaries** (`dist` or `upload-rust-binary-action`) and `cargo binstall`. Keep `just install` for the maintainer path. | Compile-from-source of rquickjs + 8.9 MiB of assets is a bad public UX. release-plz itself tells you to attach binaries in a second workflow. |
| G | Silent daily auto-publish of breaking CLI | Stay on **0.x**. Disable `semver_check` (this is an application). Optionally refuse auto-merge of a Release PR that contains a `!:` / `BREAKING CHANGE` commit. | `feat(capture)!:` already appears in history. cargo-semver-checks would grade the incidental `pub mod runner` API, which is not the product. |
| H | Include everything currently in `package.include` | Drop `tests/**`, `docs/**`, and `justfile` from the published crate. Add a CI size assertion (`crate file < 8 MiB` to leave headroom). | Needed for the 10 MiB cap. `include_bytes!` still requires `scripts/**` and `assets/print_fonts/**`. |
| I | First publish via trusted publishing | **First version is a manual `cargo publish`** with a scoped token, then switch the crate to trusted publishing. | crates.io limitation, documented by release-plz and by third-party writeups (Ortham, 2025-10-02). |
| J | Default branch `main` as in upstream snippets | Trigger on **`master`**, this repo’s default branch. | All stock release-plz YAML uses `main`. Copy-paste would never fire. |

---

## Current-state audit (this checkout)

Evidence collected from workspace `bob-cli_20` and `gh` against `bobs-org/bob-cli` on 2026-10-19.

### Package

- `[package] name = "bob-cli"`, `version = "0.1.0"`, `edition = "2024"`, `default-run = "bob"`.
- Four binaries: `bob`, `bob_pomodoro`, `bob_notify`, `tmux_bob_pomodoro`.
- `include` lists `Cargo.toml`, `Cargo.lock`, `README.md`, `docs/**`, `assets/**`, `justfile`, `src/**`, `scripts/**`, `tests/**`.
- No `license`, `authors`, `readme` key, `keywords`, `categories`, `rust-version`, `publish`.
- Public lib (`src/lib.rs` exports `runner` and `scripts`) exists so tests and embedding work. It is not a supported Rust API.
- `clap_complete = { version = "=4.6.11", features = ["unstable-dynamic"] }` — exact pin. `cargo install <name>` **without** `--locked` can fail or pull a different clap_complete. `Cargo.lock` is already in `include`; document `--locked`.
- macOS-only deps: `plist`, `rusqlite` (bundled). Linux `cargo publish --verify` will not compile them. A macOS CI job is the only compile check for that graph.
- Local toolchain observed: rustc/cargo 1.95.0. No `rust-toolchain.toml`.

### Embedded assets that *must* ship in a source crate

`include_bytes!` pulls in:

- Shell fallbacks and Python/JS web-clip adapters under `scripts/`
- `mermaid.min.js` (5.24 MiB raw, 1.50 MiB gzip)
- `defuddle.full.js`
- web-clip woff2 fonts plus `DejaVuSans.ttf`
- twelve print fonts under `assets/print_fonts/` (Noto Emoji alone 0.84 MiB)

Those bytes are load-bearing for `bob ref create` PDF/HTML snapshot and mermaid rendering. They cannot be `exclude`d without a runtime-download redesign.

### Install and release as documented today

README installation is:

```bash
just install
# or
cargo install --git git@github.com:bobs-org/bob-cli.git --locked bob-cli && bob completion install
```

`just install` is `cargo install --path . --locked` into `CARGO_INSTALL_ROOT`/`CARGO_HOME`, then `bob completion install`. `just install-all` also pulls sibling plugin and Mac Capture repos. The [Release checklist](https://github.com/bobs-org/bob-cli/blob/master/README.md) is local: `just check`, `just check-scripts`, `just package-list`, `just install-smoke`. There is no `CHANGELOG.md` and `git tag` is empty.

### GitHub

| Fact | Value |
|------|--------|
| Visibility | public |
| Default branch | `master` |
| License | none |
| Actions | enabled, **no workflows** |
| Branch protection on `master` | none |
| Org plan | `bobs-org` free, 1 seat |
| Conventional Commits | yes, consistently |
| Push style | high-frequency commits on `master` (direct or stitch), not a slow GitHub-PR culture |

### Commit cadence (git log `--since='30 days ago'`)

Typical weekday: 19–41 commits. Quiet days still 7–14. A “release every green commit” policy is unbounded version spam. A “release every green day” policy yields on the order of 20–30 GitHub Releases per month, which is still chatty and is the right *upper* bound, not a goal. Skipping empty or docs-only days is available via `release_commits`.

---

## crates.io constraints that apply here

Sources: [Cargo Book — Publishing](https://doc.rust-lang.org/cargo/reference/publishing.html), [crates.io policies](https://crates.io/policies), [crates.io rate limits](https://crates.io/docs/rate-limits), [trusted publishing](https://crates.io/docs/trusted-publishing), RFC 3691 / Rust Blog 2025-07-11, Socket 2026-01-27.

- **Names are first-come-first-serve** and hyphen/underscore equivalent.
- **A published version is forever.** Yank hides it from *new* resolves; it does not delete bytes or secrets. Deletion is allowed only in a narrow window (under 72 hours, or single owner + low downloads + no reverse deps).
- **10 MiB `.crate` cap.** This tree is at 8.85 MiB gzipped *before* `Cargo.toml.orig` / `.cargo_vcs_info.json`.
- **License (or license-file), description, repository** are the practical minimum; homepage/readme/keywords/categories help lib.rs/crates.io listing.
- **Rate limits** (leaky bucket): 5 new *crates* burst then 1 / 10 min; 30 new *versions* burst then 1 / min. A 2022 crates.io change also caps **10 new versions per crate per day**. Once-a-day sits comfortably inside both.
- **Trusted publishing (OIDC)** is the 2025+ recommended CI path. Short-lived token (~30 minutes). Configured on the crate’s crates.io settings (GitHub repo, workflow filename, optional environment). `id-token: write` on the job. release-plz speaks this protocol itself — do **not** also run `rust-lang/crates-io-auth-action` in the same job.
- **First version of a new crate cannot use trusted publishing.** Manual token with `publish-new` + `publish-update`, then convert.
- As of early 2026, trusted publishing **rejects** `pull_request_target` and `workflow_run` as publisher triggers. Use `push` to `master`, `schedule`, `workflow_dispatch`, or `release`.
- Optional **trusted-publishing-only** mode disables token publishes after setup. Worth turning on once the GitHub App path is proven.

### Name collision in practice

`cargo install bob-cli` already installs Longcipher’s AI-agent CLI (binary `bob-cli`). Even after this project publishes under `bobs-cli`, README and `crates.io` description must say **package `bobs-cli`, binary `bob`**, the way `ripgrep` installs `rg`. Asking the current `bob-cli` owner for a transfer is possible (85 downloads, last publish 2026-04-07) and unlikely to be worth blocking on.

Recommended package name: **`bobs-cli`**, matching `bobs-org`. Runner-up if crates.io search matter more than org rhyme: **`bob-obsidian`**.

---

## How release-plz actually works

Sources: [release-plz.dev quickstart](https://release-plz.dev/docs/github/quickstart), [config](https://release-plz.dev/docs/config), [release](https://release-plz.dev/docs/usage/release), [GitHub token](https://release-plz.dev/docs/github/token), [releasing binaries](https://release-plz.dev/docs/extra/releasing-binaries), [why](https://release-plz.dev/docs/why).

Two commands, two jobs:

1. **`release-plz release-pr`** — opens or updates one rolling PR (`release-plz-*` branch) with the next `Cargo.toml` version, `CHANGELOG.md`, and lockfile bump. It folds every new `master` commit into that same PR. Merge = “cut a release.”
2. **`release-plz release`** — looks at unpublished versions (crates.io by default, git tags when `git_only = true`). For each, it `cargo publish`es (unless disabled), creates a git tag, and creates a GitHub Release from the changelog.

### Config knobs that matter here

| Knob | Recommended for bob-cli | Default |
|------|-------------------------|---------|
| `release_always` | **`false`** | `true` (publish on every run / every mainline push) |
| `git_only` | **`true` in phase 1** | `false` |
| `publish` | `false` until crates.io is ready | `true` |
| `semver_check` | **`false`** | on (cargo-semver-checks of the lib API) |
| `features_always_increment_minor` | `false` while 0.x (feat → patch); `true` after 1.0 | `false` |
| `git_tag_name` / `git_release_name` | `v{{ version }}` (single public package) | already that for one crate |
| `pr_labels` | `["release"]` | none |
| `release_commits` | optional; e.g. skip pure `chore:` / `docs:` if daily noise is too high | any commit |
| `publish_timeout` | `30m` or `1h` (rquickjs + verify build is slow) | `30m` |
| `dependencies_update` | `false` (do not `cargo update` the world inside a release PR) | `false` |

`release_always = false` is the whole “at most when we merge the Release PR” mechanism. Combine it with “we merge that PR at most once per day” and the original cadence requirement is met.

### Token / trigger trap

The default `GITHUB_TOKEN` **cannot start other workflows**. Consequences for this repo:

- CI on the Release PR will not run.
- A `on: release` / `on: push: tags` binary-build workflow will not run after `release-plz release`.

Fix: a **GitHub App** (`actions/create-github-app-token`) as release-plz itself uses, or a fine-grained PAT with Contents + Pull requests. App is better: bot authorship, no expiry, scoped install on `bobs-org/bob-cli`.

Also in the GitHub Actions org settings: allow GitHub Actions to create pull requests.

### 0.x version math

With Conventional Commits and `features_always_increment_minor = false`:

- `fix:` → patch (`0.1.0` → `0.1.1`)
- `feat:` → patch while 0.x
- `feat!:` / `BREAKING CHANGE:` → minor (`0.1.x` → `0.2.0`)

That is Cargo’s 0.x convention (minor is allowed to break). Stay on 0.x until the CLI is deliberately frozen. Do not declare 1.0 as a side effect of automation.

---

## Alternatives compared

| Approach | What it optimizes | Fit for bob-cli |
|----------|-------------------|-----------------|
| **release-plz, `release_always = true`, crates.io** | Library crates with sparse merges | Bad. Would publish ~daily *per commit*. Name taken. 10 MiB. |
| **release-plz Release PR + human merge, crates.io** | Maintainer-gated library releases | Decent *after* rename/license/size. Still a source-install UX. |
| **release-plz Release PR + daily cron merge, `git_only`** | Application tags/notes without a registry | **Best phase 1.** Implements “at most once a day when green.” |
| **`cargo-release` from a laptop** | One-shot CLI bump/tag/publish | Works; reintroduces the manual checklist. No green-CI gate unless wrapped. |
| **`dist` (cargo-dist) alone** | Tag-driven multi-platform binaries, installers, Homebrew | Excellent *distribution*. Weak *version/changelog* brain. Pair with release-plz. |
| **`taiki-e/upload-rust-binary-action` on `release`** | Smaller binary uploader | Good dist alternative if `dist` feels heavy. release-plz documents this pattern. |
| **`cargo-smart-release`** | Local cousin of release-plz | Author says it is not for CI. |
| **GitHub Releases only, handwritten tags** | Minimal | Bryan already has a long manual checklist; this is what automation is for. |
| **Homebrew tap / Nix later** | End-user package managers | Optional phase 4. `dist` can emit a tap. Not a substitute for tags. |

Orhun’s 2026 write-up of daktilo is the closest published recipe: git-cliff + release-plz + cargo-dist. That trio is the right shape. For bob-cli, delay the crates.io leg.

---

## Recommended solution

### Phase 0 — Make “green CI” a real predicate (do this regardless)

Add `.github/workflows/ci.yml`:

- Triggers: `pull_request` and `push` to `master`.
- `ubuntu-latest` (required) + `macos-latest` (required for `plist`/`rusqlite`).
- Install: `just`, `clang`/`build-essential` (rquickjs), Rust via `dtolnay/rust-toolchain` **or** a committed `rust-toolchain.toml` (pin stable, components `rustfmt`, `clippy`).
- Cache: `Swatinem/rust-cache`.
- Jobs (separate so they can be required independently):
  1. `just fmt` + `just lint`
  2. `just test` (or `cargo test --no-fail-fast --locked`)
  3. `just check-scripts`
  4. `cargo package --list` + a size assertion on `target/package/*.crate` after `cargo package --no-verify --locked`
- Optional / nightly: `just install-smoke` (slow; full `cargo install`).
- `if: github.repository_owner == 'bobs-org'` so forks do not burn minutes.

Pin the toolchain. Edition 2024 already implies a recent stable; an unpinned `dtolnay/rust-toolchain@stable` will one day surprise a publish.

Then turn on **branch protection for `master`**: require the Ubuntu `just check` equivalent. Public repo, free org: Actions minutes for public workflows are the usual GitHub fair-use pool.

Until this phase exists, do not wire `cargo publish`.

### Phase 1 — Daily GitHub Releases via release-plz (no crates.io)

`release-plz.toml`:

```toml
[workspace]
release_always = false
git_only = true
publish = false
semver_check = false
dependencies_update = false
changelog_update = true
pr_labels = ["release"]
git_tag_name = "v{{ version }}"
git_release_name = "v{{ version }}"
git_release_type = "auto"
publish_timeout = "1h"

# Optional: skip a day that is only chores.
# release_commits = "^(feat|fix|perf)(\\(.+\\))?(!)?:"
```

Workflow split:

1. **`release-plz.yml`** on `push` to `master`:
   - Job `release-pr`: GitHub App token, `command: release-pr`. Concurrency group `release-plz-${{ github.ref }}`, `cancel-in-progress: false`.
   - Job `release`: GitHub App token, `command: release`, `environment: release` (manual approval optional). Permissions: `contents: write`, `pull-requests: read`, and later `id-token: write` for crates.io.
2. **`daily-release.yml`** on `schedule` (pick a quiet hour, e.g. `cron: "0 11 * * *"` UTC) and `workflow_dispatch`:
   - Succeed only if the latest `master` CI run is `success`.
   - Succeed only if no `v*` tag exists with today’s date (belt and suspenders).
   - If a `release-plz-*` PR is open, merge it (`gh pr merge --squash` is the case release-plz documents `release_always = false` for). That push runs job `release`.
   - If the open Release PR contains a `!:` / `BREAKING CHANGE` commit, **stop and notify** (SASE notification, or a failed workflow that wants a human). Adjustment G.

GitHub App permissions: Contents R/W, Pull requests R/W. Install only on `bob-cli`. Store `APP_ID` + `APP_PRIVATE_KEY`.

This phase already delivers: versioned tags, a changelog, GitHub Release notes, an auditable “what shipped today” object. Bryan’s own machines can keep using `just install-all`.

### Phase 2 — Prebuilt binaries (the actual public install)

release-plz will not build binaries; it says so and points at `dist` and `taiki-e/upload-rust-binary-action`.

Prefer **`dist` (cargo-dist) 0.33+** if the extra generated workflow is acceptable: GitHub Release assets, shell/PowerShell installers, checksums, and `cargo binstall` compatibility. Otherwise the smaller taiki-e action on `on: release: types: [published]` is enough.

Target matrix that matches real hosts (athena/apollo Linux, Mac):

- `x86_64-unknown-linux-gnu`
- `aarch64-unknown-linux-gnu`
- `aarch64-apple-darwin`
- `x86_64-apple-darwin` if an Intel Mac still matters

Skip Windows initially (rquickjs + MSVC has a history of extra toolchain pain; Bryan does not need it).

The `on: release` workflow **requires the GitHub App token in phase 1**, or it never starts.

Public install snippet to put in README after the first tagged release:

```bash
# prebuilt (preferred)
cargo binstall bobs-cli
# or dist’s installer URL once generated
bob completion install
```

Maintainer path stays `just install` / `just install-all`.

### Phase 3 — crates.io, only after A–I are done

Checklist before `publish = true` / `git_only = false`:

1. Choose package name (`bobs-cli`). Keep `[[bin]] name = "bob"`.
2. Add `LICENSE` (MIT, Apache-2.0, or dual — compatible with vendored MIT mermaid/defuddle and OFL fonts; keep those license files in the crate).
3. Fill `license`, `readme = "README.md"`, `keywords`, `categories = ["command-line-utilities"]`, `rust-version`.
4. Shrink `package.include` to what `include_bytes!` and `--locked` need:

   ```toml
   include = [
       "/Cargo.toml",
       "/Cargo.lock",
       "/README.md",
       "/LICENSE",
       "/src/**",
       "/scripts/**",
       "/assets/**",
   ]
   ```

5. CI gate: `cargo package --locked --no-verify` and `test $(stat -c%s target/package/*.crate) -lt 8388608`.
6. `cargo publish --dry-run --locked` locally.
7. crates.io account, verified email, **one** manual `cargo publish` of `0.1.0` (or whatever the then-current version is) with a token scoped `publish-new` + `publish-update`. Revoke that token after trusted publishing is confirmed.
8. On the crate’s Trusted Publishing settings: owner `bobs-org`, repo `bob-cli`, workflow filename, environment `release`.
9. Flip release-plz: `git_only = false`, `publish = true`, job permission `id-token: write`, **no** `CARGO_REGISTRY_TOKEN` in the workflow. Do not combine with `crates-io-auth-action`.
10. README: `cargo install bobs-cli --locked && bob completion install`. Warn that `cargo install bob-cli` is a different project.
11. Optional: enable trusted-publishing-only mode on the crate.

If the gzipped `.crate` cannot be kept under ~8 MiB after trimming, **stop**. Do not raise `publish_no_verify` to sneak past a failed package; fix assets (runtime-fetch mermaid is the only large lever). crates.io is optional. GitHub Releases already ship the product.

### Phase 4 — nice-to-haves, not blockers

- Homebrew tap via dist.
- `package.metadata.binstall` if dist’s default layout is not enough.
- `release_commits` filter if daily notes are too noisy.
- A human approval GitHub Environment on the `release` job, instead of a fully automatic daily merge, for the first month.

---

## Suggested workflow shape (phase 1+2)

```text
push to master
    └─ ci.yml (ubuntu + macos)           required
    └─ release-plz.yml / release-pr      updates rolling PR

cron 11:00 UTC (and workflow_dispatch)
    └─ latest master CI green?
    └─ breaking !: in the pending PR? -> fail/notify
    └─ gh pr merge release-plz-* 

merge of Release PR
    └─ ci.yml again
    └─ release-plz.yml / release         tag vX.Y.Z + GitHub Release
         └─ (App token so this fires) cd.yml / dist
              └─ build linux/mac binaries, attach, installer
```

Default branch in every `on.push.branches` list: **`master`**.

---

## Risks and limits

- **10 MiB cliff.** 8.85 MiB today. Trim before any registry publish; keep a CI budget.
- **Name confusion.** `bob-cli` on crates.io is someone else. Binary `bob` can collide locally with [jperkin/bob](https://github.com/jperkin/bob) (`bob` 1.0.0, pkgsrc builder) if a user has that installed.
- **rquickjs / clang.** Source installs and CI both need a C compiler. Binary releases hide this from users; crates.io does not.
- **macOS-only crates.** Ubuntu-only CI will not catch `rusqlite`/`plist` breaks.
- **Exact `clap_complete` pin.** Unlocked `cargo install` is a footgun. `--locked` in every doc snippet.
- **Public Actions on a public repo.** Fine for this org; still pin actions by SHA when you care about supply chain (release-plz’s own workflow does).
- **Daily GitHub Releases still accumulate.** 20+/month is a lot of “latest”. That is acceptable for 0.x if the notes are generated; it is noisy if you later add Homebrew.
- **Secrets in the crate.** Yank does not erase. Never package vault fixtures with credentials. Current `include` of `tests/**` is extra attack surface for no compile-time gain.
- **SASE stitch vs GitHub PRs.** Feature work can stay on the current stitch/master flow. release-plz only needs GitHub for *its* Release PR and tags.
- **Trusted publishing environment.** If you set `environment: release` in crates.io, the GitHub job must use the same environment name.

---

## Open questions for Bryan (do not block phase 0–1)

1. Package name if/when crates.io happens: `bobs-cli` vs `bob-obsidian`.
2. License: MIT, Apache-2.0, or dual.
3. Fully automatic daily merge vs first-month GitHub Environment approval.
4. Whether docs-only days should skip a release (`release_commits`).
5. Windows binaries: skip (recommended) or pay the rquickjs/MSVC cost.
6. Whether a crates.io listing is actually desired once `cargo binstall` works. I would wait and see.

---

## Implementation order (short)

1. `LICENSE` + `rust-toolchain.toml` + GitHub Actions CI + package size gate.
2. GitHub App + `release-plz.toml` with `git_only = true`, `release_always = false`.
3. Daily cron that merges the Release PR only when CI is green.
4. Binary attach (`dist` or taiki-e) on `release` published.
5. Revisit crates.io: rename package, slim `include`, manual first publish, trusted publishing.

Do not start at step 5. The original plan’s valuable parts are steps 1–4.

---

## Sources

### This repository

- `Cargo.toml`, `Cargo.lock`, `src/lib.rs`, `src/scripts.rs`, `src/native/highlights_ref/note_snapshot/fonts.rs`
- `justfile` (`check`, `package-list`, `install`, `install-smoke`)
- `README.md` installation + release checklist
- `git log` cadence and Conventional Commit subjects, empty `git tag`
- `cargo package --list --allow-dirty` (954 files, 30.15 MiB raw; tar.gz estimate 8.85 MiB)
- `gh repo view` / Actions permissions / branch protection for `bobs-org/bob-cli`

### crates.io / Cargo

- https://doc.rust-lang.org/cargo/reference/publishing.html (10 MiB cap, permanence, license, cargo-release / release-plz / cargo-smart-release listed)
- https://crates.io/policies (name allocation, yank/delete)
- https://crates.io/docs/rate-limits
- https://crates.io/docs/trusted-publishing
- https://blog.rust-lang.org/2025/07/11/crates-io-development-update-2025-07/ (trusted publishing launch)
- https://socket.dev/blog/crates-security-tab-tightened-publishing-controls (2026-01-27: GitLab OIDC, trusted-publishing-only, `pull_request_target` / `workflow_run` removed)
- crates.io API, 2026-10-19: `bob-cli` / `bob_cli` = longcipher 0.3.2; `bob` = jperkin 1.0.0; `bobs-cli` and `bob-obsidian` 404
- https://github.com/rust-lang/crates.io/pull/5294 (10 versions/crate/day)

### release-plz / dist / binstall

- https://release-plz.dev/docs/github/quickstart
- https://release-plz.dev/docs/config (`release_always`, `git_only`, `semver_check`, `features_always_increment_minor`)
- https://release-plz.dev/docs/usage/release
- https://release-plz.dev/docs/github/token (GITHUB_TOKEN does not chain workflows; App vs PAT)
- https://release-plz.dev/docs/extra/releasing-binaries
- https://release-plz.dev/docs/why
- https://blog.orhun.dev/automated-rust-releases/ (2026-10-08: git-cliff + release-plz + cargo-dist)
- https://blog.ortham.net/posts/2025-10-02-rust-supply-chain-security/ (first crate version still needs a token)
- https://axodotdev.github.io/cargo-dist/book/install.html and cargo-dist 0.33.0 (2026-09-10)
- https://github.com/cargo-bins/cargo-binstall

### Native build

- https://github.com/DelSkayn/rquickjs/issues/589 (2026-01-03: missing clang breaks dependents)
- rquickjs 0.12.1 in this `Cargo.lock`; upstream 0.14 documents C compile + per-target bindings
