# Publishing Bob with release-plz: readiness, daily limits, and a recommended design

Independent research by **cdx**, 2026-10-19.

**Conclusion:** release-plz is a good fit for versioning and publishing this Rust project, but copying its quickstart would not satisfy the requested release policy. First establish CI and resolve publication blockers. Then maintain one reviewed release PR and publish its exact tested source through a separate scheduler with a registry-backed daily limit. Use crates.io Trusted Publishing after the initial release. Add prebuilt binaries later if easier installation is the real objective.

The registry is **crates.io**, not cargo.io. More significantly, **the crates.io name `bob-cli` is already taken by an unrelated project**. This repository cannot be published under that name without an ownership arrangement that I do not recommend pursuing as the default.

## Evidence and scope

I inspected the bob-cli checkout at commit `bfca3419c3f5c4caa9a609c6e4f64a2dc6a86111`, queried GitHub repository/workflow/check metadata, queried the crates.io API, read current upstream documentation, and opened release-plz through `sase repo open` to inspect its implementation. The inspected release-plz commit was `907af6d031bbb69d392354803c04cd75bb6e6fa0`, also the commit of tag `release-plz-v0.3.173`.

No peer research report or peer findings were consulted. No release was published, remote setting changed, or production code edited. The packaging experiment below deliberately skipped compilation; this report is not a certification that the current tree passes CI or can already be published.

## 1. What is true of this repository today

| Finding | Evidence | Consequence |
| --- | --- | --- |
| One Cargo package, version `0.1.0`, edition 2024 | `Cargo.toml` | A straightforward release-plz use case; no multi-package release ordering is needed. |
| Four executable targets: `bob`, `bob_pomodoro`, `bob_notify`, `tmux_bob_pomodoro` | `Cargo.toml` | Registry installation can retain all existing executable names. |
| There is also a Rust library | `src/lib.rs` exports runner/script APIs | Do not assume this is a binary-only crate when deciding semver-check settings. |
| Public GitHub repo, default branch **`master`** | Live repository API | Examples using `main` need adaptation. Public Actions and source publication are feasible. |
| No `.github` directory and no registered Actions workflows | Checkout and live workflows API returned an empty list | CI must be implemented before “all CI green” is a meaningful release condition. |
| No check runs or status contexts on the inspected commit | GitHub check-runs and combined-status APIs | An empty set of checks must never be treated as release approval. |
| No package `license`/`license-file`; no root license file found | Manifest, tracked files, packaging warning | Choose a license and include its text before first publication. |
| No `rust-version` declaration | Manifest | Establish and test a supported Rust version; edition alone does not establish dependency MSRV. |
| Broad explicit package inclusion | `/docs/**`, `/assets/**`, `/scripts/**`, `/src/**`, `/tests/**`, etc. | Package size and release noise deserve attention. |
| Native and embedded integrations remain significant | README runtime dependencies; `src/scripts.rs` | A registry package installs Bob, not Obsidian, the Mac app, plugins, browsers, TeX, or every external command. |

Local source references can be reproduced from that commit: [manifest](https://github.com/bobs-org/bob-cli/blob/bfca3419c3f5c4caa9a609c6e4f64a2dc6a86111/Cargo.toml), [verification/install recipes](https://github.com/bobs-org/bob-cli/blob/bfca3419c3f5c4caa9a609c6e4f64a2dc6a86111/justfile), [README](https://github.com/bobs-org/bob-cli/blob/bfca3419c3f5c4caa9a609c6e4f64a2dc6a86111/README.md), [library exports](https://github.com/bobs-org/bob-cli/blob/bfca3419c3f5c4caa9a609c6e4f64a2dc6a86111/src/lib.rs), and [embedded assets](https://github.com/bobs-org/bob-cli/blob/bfca3419c3f5c4caa9a609c6e4f64a2dc6a86111/src/scripts.rs). Repository contents were read locally, not fetched through those links.

### The crate-name collision is a real blocker

A live request to the [crates.io `bob-cli` API](https://crates.io/api/v1/crates/bob-cli) returned version `0.3.2`, repository `https://github.com/longcipher/bob`, and description “CLI app for Bob - a general-purpose AI agent framework.” It is not this repository. The registry allocates names first come, first served. [Cargo publishing documentation](https://doc.rust-lang.org/cargo/reference/publishing.html)

The same API returned HTTP 404 for `bob-vault` and `bob-vault-cli` during this research. Those are **candidate names, not reservations or guaranteed future availability**. My preference is **`bob-vault`**: it distinguishes the product without requiring a repository rename. Keep the user-facing executable `bob` and the three compatibility shims.

Renaming `[package].name` also changes the default library crate name. Existing binary entry points call `bob_cli::...`; explicitly setting `[lib] name = "bob_cli"` can preserve those imports while changing the registry package name. Update the lockfile, install documentation, and any package-name assumptions together.

There are two different installation collisions to handle:

- Existing users installed this checkout as package `bob-cli`. After the package rename, Cargo sees a different package owning the same executable paths. Document a deliberate migration after confirming the installed package and installation root; do not silently add `--force` to every install.
- Other software also uses the command name `bob`; the registry includes the unrelated [bob-nvim package](https://crates.io/crates/bob-nvim). Keeping `bob` is reasonable for existing users, but installation should diagnose an existing owner instead of overwriting it.

Cargo documents both binary-name conflicts and selective `--bin` installation. [Cargo install documentation](https://doc.rust-lang.org/cargo/commands/cargo-install.html)

### Packaging already works mechanically, but has little size margin

Read-only/local-output experiments, using Cargo 1.95.0:

```text
cargo package --list --offline
  success; warning: manifest has no license or license-file
  956 packaged files

cargo package --no-verify --locked --offline
  success; same license warning
  956 files, 30.2 MiB uncompressed, 8.8 MiB compressed
  actual .crate file: 9,256,837 bytes
```

The explicit include list excluded `sase/` from the package listing. The largest individual file was the embedded Mermaid bundle at 5,494,801 uncompressed bytes. Directory payload totals included approximately 6.0 MB of assets, 7.9 MB of scripts, 12.0 MB of Rust/source-tree content, and 4.2 MB of integration tests. These are uncompressed figures, not estimates of upload savings.

The Cargo book documents a **10 MB `.crate` limit**. The current archive is below that limit, but close enough that growing fixtures or fonts could break publishing. Add an archive-size check and seek more margin; do not assume a bigger limit will be granted. [Cargo publishing documentation](https://doc.rust-lang.org/cargo/reference/publishing.html)

Start by reviewing packaged docs, development scripts, and fixtures. Preserve every `include_bytes!`/`include_str!` input and third-party notice. Some unit tests include fixture files at compile time, so blanket removal of `tests/**` can also break package verification tests. Build and test an extracted archive after changing includes. The package's own license does not replace the OFL, DejaVu, Moment, Mermaid, and other bundled notices.

## 2. Is this a good idea?

**Yes, if the objective is a versioned public source distribution and a dependable installation command.** The project is already a single Cargo package with conventional-looking commit subjects, an install smoke recipe, and an explicit release checklist. release-plz removes repetitive manifest/changelog/tag work and makes each proposed release reviewable. It is a better fit than a custom script that increments numbers and invokes `cargo publish`.

**It is only a partial solution if the objective is effortless installation on Bryan's machines or for non-Rust users.** `cargo install` still compiles Rust and native dependencies. It does not install the rest of the Bob environment or update the companion repositories. A future binary distribution should be evaluated separately. Do not promise that a crate release replaces `just install-all`.

A daily maximum is reasonable: it batches rapid development and bounds update noise. It should be a **ceiling, not a quota**. No relevant change, no reviewed candidate, failed checks, or uncertain registry state should mean no new version. A changelog full of daily documentation/fixture churn is not an improvement by itself.

CI provides necessary evidence, not a complete compatibility guarantee. Bob exposes command syntax, JSON/subprocess contracts, filesystem conventions, and behavior consumed by the Mac app and Obsidian plugins. `cargo-semver-checks` analyzes Rust library APIs; it cannot certify those external contracts. Keep it enabled initially for the existing library, and add explicit CLI/JSON compatibility coverage and breaking-change review. [Release-plz semver-check documentation](https://release-plz.dev/docs/semver-check)

## 3. Proposed changes and clarifications to the requirements

These are my recommendations, not facts supplied by the original request:

1. **Use a new crate name**, provisionally `bob-vault`; retain executable names and the GitHub repository name.
2. **Interpret “at most once a day” as at most one successful new crate version in a rolling 24-hour period.** This is stricter and avoids a pair of releases minutes apart on opposite sides of midnight. If calendar-day batching is preferred, explicitly choose UTC instead; it is a different rule.
3. **Allow hourly eligibility checks, not hourly releases.** An off-hour cron such as `37 * * * *`, combined with the 24-hour guard, gives retry opportunities after a failure. Most runs should exit before building. A single daily cron is simpler but can miss a day after delays or a failed check.
4. **Define “all CI” as a named, version-controlled set of required release checks on the actual source commit being published.** Exclude the publisher itself and unrelated informational workflows. Missing, cancelled, or unexpectedly skipped required jobs are not success.
5. **Keep a human review of release PRs for the first several releases.** Consider automatic merging only after compatibility and version-bump behavior have been demonstrated. Publication after a reviewed merge can be automatic from day one.
6. **Initially support the platforms already reflected in the code and usage: Linux and macOS.** Confirm architectures during implementation; do not imply Windows support merely because crates.io accepts the package.
7. **Do not auto-install new releases or coordinate companion releases implicitly.** Publishing Bob and deploying the Bob environment are separate operations.

The cap applies to ordinary publication, including manual workflow dispatch and reruns. Repairing missing GitHub metadata for an already-published version is not a new crate release. A true emergency override would need a separately documented policy; it should not be an unnoticed `force` input.

## 4. What release-plz does—and where the policy must live

release-plz separates version preparation from publication:

- `release-plz release-pr` proposes manifest, lockfile, and changelog updates.
- `release-plz release` publishes versions already present in the checkout; it does not invent a fresh version on every invocation.
- `release-plz update` performs preparation locally without opening a PR.

[Release-plz command overview](https://release-plz.dev/docs/usage) and [update behavior](https://release-plz.dev/docs/usage/update)

Its default quickstart runs on pushes. Merely replacing a push trigger with a cron neither defines a hard daily cap nor establishes the required checks. GitHub scheduling can be delayed or dropped, runs from the default branch, and public-repository schedules can be disabled after inactivity. Treat cron as an opportunity to evaluate eligibility. [GitHub scheduled workflow behavior](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule)

Set `release_always = false` to restrict publishing to commits associated with a release PR. This is a release-origin check, **not a time limiter**. Checking out the latest `master` on a later schedule can cause it to skip: newer ordinary commits need not be associated with the release PR. Leaving it true to avoid that skip can publish an unintended source snapshot. Solve candidate selection explicitly. [Release-plz configuration](https://release-plz.dev/docs/config#the-release_always-field)

There is another subtlety: with a normal merge, release-plz can move from the merge commit to the last commit on the release PR before publishing. With a squash merge, that original PR commit is generally not an ancestor, so it uses the checked-out commit. Therefore “we tested the checkout before calling release-plz” is insufficient unless checkout selection matches this behavior. [Release-plz source-commit selection](https://release-plz.dev/docs/usage/release#what-commit-is-released)

I verified that behavior in upstream `should_release()` and `release()`, rather than assuming the action always publishes `github.sha`. [Inspected implementation](https://github.com/release-plz/release-plz/blob/907af6d031bbb69d392354803c04cd75bb6e6fa0/crates/release_plz_core/src/command/release.rs#L804)

## 5. Recommended architecture

Use three responsibilities with separate permissions and explicit inputs:

```text
push / pull request
        │
        ├── reusable CI checks
        │
        └── maintain one release PR ── review + required checks ── merge
                                                                    │
                              registry history + merged PR metadata ─┤
                                                                    ▼
hourly schedule / manual dispatch ── select eligible candidate SHA
                                          │
                                  run release CI on that SHA
                                          │
                                  acquire publisher serialization
                                          │
                                  recheck candidate + 24-hour guard
                                          │
                                  release-plz release using OIDC
                                          │
                                  reconcile registry / tag / release
```

This contains a small amount of custom orchestration: candidate discovery and the cadence guard. Those are the genuinely missing capabilities. Keep them in short, testable repository scripts rather than duplicating release-plz's versioning logic.

### A. Establish a reusable release CI gate

Create CI for PRs and pushes to `master`, and expose the same checks to the publishing workflow for a supplied, validated commit SHA. Use a protected workflow definition and check out the selected source by full SHA. Test jobs need no registry credential or repository write permission.

The initial required set should cover:

| Check | Proposed scope |
| --- | --- |
| Format, lint, tests | Preserve the `just check` semantics, including existing warning policy; run on Linux and macOS. |
| Shell tooling | `just check-scripts`. |
| Embedded adapters | Existing `check-adapter` and `check-web-clip-adapter`; provision browser prerequisites where required so a silent optional skip does not masquerade as browser coverage. |
| Package integrity | `cargo package --list`; inspect allowlist and notices; generate the archive and enforce its compressed-size budget. |
| Distribution build | `cargo publish --dry-run --locked`, followed by installation from an extracted package into a temporary root. |
| Installation/contracts | Help, version, all four binaries, completion protocol, and representative fixture-based JSON commands; no real vault or authenticated service access. |

`just install-smoke` currently installs from the checkout. Reuse its assertions for the extracted archive as well; a successful checkout build does not establish that the crate contains everything users need.

Add `--locked` to the relevant Cargo CI invocations or equivalent dedicated CI recipes, and assert that lockfile/content remain unchanged. The existing canonical gate does not currently pass `--locked` to all Cargo commands. Do not mix dependency upgrades into every release; dependency refreshes should be their own reviewed changes.

A final aggregate check must explicitly require success from every required dependency. Branch protection and the publisher should both depend on that result. In a multi-workflow arrangement, resolve each expected check on the chosen SHA and the expected workflow/App identity; do not use “some successful CI run exists” or `.all()` over an empty list.

### B. Maintain one release PR

Run `release-plz release-pr` on `master` updates, using its own concurrency group. Keep one accumulating proposal. Avoid a narrow `feat|fix` release filter initially: a dependency, script, asset, or packaging fix can be a legitimate release even with another commit type. Tighten inclusion and changelog policy after observing noise.

Pause creation of another release candidate while a merged candidate is unpublished or has unresolved publication metadata. This single-candidate rule simplifies delayed releases, retries, and the daily cap. Do not silently collect several unpublished version bumps and publish them together later.

Use a repository-scoped GitHub App installation token for PR creation/updates, with Contents and Pull requests write access. A fine-grained PAT is a workable simpler fallback, but has a personal ownership/rotation cost. [Release-plz GitHub token setup](https://release-plz.dev/docs/github/token)

**Documentation discrepancy:** release-plz's token guide says default `GITHUB_TOKEN` PRs do not run CI. Current GitHub documentation is more nuanced: `opened`, `synchronize`, and `reopened` PR events can produce approval-required workflow runs. It still does not give unattended PR validation. A GitHub App avoids relying on that human approval path. [Current GitHub workflow-trigger rules](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow)

### C. Select the source candidate explicitly

For the initial implementation, standardize release PRs on **normal merge commits**, matching upstream's recommended model. The selector should:

1. Identify the one pending merged release PR in this repository, targeting `master`, with the configured release branch prefix and expected bot identity. A label or branch prefix alone is insufficient authorization.
2. Obtain the PR's final head SHA and merge SHA. Verify that the final head is an ancestor of the protected branch. Require the release branch to be up to date before merging; fail if the merge introduced a different source tree from the proposed release head.
3. Read the package name/version from that head, ensure it is the selected renamed package, and determine whether the version already exists in the registry.
4. Check out that **PR head SHA** for CI and publication. At that SHA, release-plz's internal source-selection step should stay on the same commit. Record PR number, source SHA, version, and check results in the run summary.

For a future squash-only policy, select the actual squash merge SHA and verify that alternative with integration tests. Do not casually support both merge strategies in an opaque script.

This publishes the reviewed release snapshot even if ordinary commits subsequently advance `master`; those changes wait for the next version. It also avoids requiring that `master` happen to end at a release commit when cron fires.

### D. Enforce the cap at the publisher

Use one repository-wide publisher concurrency group, shared by schedule, dispatch, and recovery paths, with `cancel-in-progress: false`. After acquiring it, **recheck** all eligibility. A check performed only before waiting for the lock can be stale.

GitHub concurrency is a mutual-exclusion mechanism, not a clock or durable publication record. Its default pending queue can replace older pending runs. That is acceptable here because every new scheduler invocation rediscovers the same durable merged candidate; it does not depend on preserving a unique push event. [GitHub concurrency behavior](https://docs.github.com/en/actions/concepts/workflows-and-actions/concurrency)

Proposed guard logic:

```text
candidate absent                         -> successful no-op
registry unavailable / ambiguous         -> fail closed; publish nothing
candidate version already published      -> reconcile metadata; no new upload
candidate inconsistent or superseded     -> stop for review
any required candidate check not success -> publish nothing
newest publication is less than 24h old  -> successful no-op, report next eligibility
otherwise                                -> publish this one version
```

Use actual registry publication timestamps, including yanked and prerelease versions, not GitHub release dates, tag commit dates, workflow start times, or the highest semantic version. If querying a paginated endpoint, do not assume the first item is the newest publication. Query through the registry's supported API/index metadata and handle errors explicitly. The registry now also exposes publication time in its index. [crates.io publication-time announcement](https://blog.rust-lang.org/2026/01/21/crates-io-development-update/)

The hourly schedule exits early unless there is a pending candidate and the cap is likely open; expensive CI is then followed by the authoritative in-lock recheck. This generally yields a release about every 24–25 hours when work is available, rather than promising a fixed wall-clock release time. A daily schedule remains an option if occasional skipped days are acceptable.

After an ambiguous upload failure, freeze that candidate and reconcile the registry before preparing another version. Do not interpret a missing success output as proof no upload happened. Avoid caching the cadence decision across runs. All ordinary publishing paths must use this gate; out-of-band owner actions can defeat any workflow policy.

### E. Authenticate publication with Trusted Publishing

The first publish requires a crates.io account/verified email and suitable initial token authorization; current release-plz guidance says new crates cannot use Trusted Publishing for that initial upload. Make this a deliberate bootstrap of the actual useful package after all checks, not a placeholder name reservation. [Release-plz first-publish and OIDC guidance](https://release-plz.dev/docs/github/quickstart)

Afterward, configure the crate's Trusted Publisher for the exact GitHub owner, repository, publishing workflow filename, and optional release environment. Restrict that environment to the protected branch and validate all candidate inputs inside the workflow. Give the publisher `id-token: write`, `contents: write`, and `pull-requests: read`; keep OIDC and write permissions out of test and PR-generation jobs.

Current release-plz implements the OIDC exchange itself. Do not also inject a long-lived `CARGO_REGISTRY_TOKEN` or add the separate crates-io auth action when using that supported integration. Pin a release-plz version that contains this behavior and pin actions to reviewed commit SHAs. The PR-generation App credential is separate from crates.io publishing authorization. [Release-plz OIDC guidance](https://release-plz.dev/docs/github/quickstart)

**Do not design the publisher around `workflow_run`.** crates.io explicitly blocks Trusted Publishing from `workflow_run` and `pull_request_target`. Use the scheduled/dispatched workflow and `needs`/reusable jobs instead. After bootstrap, consider enforcing Trusted Publishing Only mode to remove ordinary token-based bypasses. [crates.io January 2026 security changes](https://blog.rust-lang.org/2026/01/21/crates-io-development-update/)

For the first few releases, a protected release environment can provide a final human pause if desired, but it is not necessary to ask for a second approval forever once release-PR review is established.

### F. Keep release-plz configuration small

Illustrative starting point, after the new package name is selected:

```toml
[workspace]
release_always = false
dependencies_update = false
publish_allow_dirty = false
publish_no_verify = false
semver_check = true
```

These settings express intentional policy; several are already defaults. Keep standard pre-1.0 version semantics initially: breaking compatibility changes advance the minor component; compatible changes advance the patch component. Review CLI/JSON behavior manually because a clean Rust API comparison is insufficient. Do not set `features_always_increment_minor = true` merely to make every feature look like a larger release. [Release-plz configuration](https://release-plz.dev/docs/config)

Keep `release-pr` and `release` as explicit separate commands/jobs. The upstream documentation discourages using the action's combined mode because its concurrency behavior makes release events harder to reason about. [Release-plz single-job warning](https://release-plz.dev/docs/extra/single-job-workflow)

## 6. Failure recovery is part of the design

Publishing to crates.io, creating a tag, and creating a GitHub Release are separate remote effects. They are not one transaction.

In the inspected release-plz implementation, an existing tag can cause a package to be skipped, and an already-published registry version is also skipped before the normal tag/release creation path. Therefore **do not promise that simply rerunning release-plz will repair every partial failure**. Verify behavior at the pinned tool version. [Upstream skip/publication logic](https://github.com/release-plz/release-plz/blob/907af6d031bbb69d392354803c04cd75bb6e6fa0/crates/release_plz_core/src/command/release.rs#L710)

| Observed state | Recovery |
| --- | --- |
| CI fails before upload | Keep the candidate; fix the cause or explicitly supersede it through a reviewed candidate. Retry without publishing automatically from a new `master`. |
| Upload times out | Check the candidate version in the registry before any new upload/version bump. |
| Crate exists, tag or GitHub Release missing | Verify package provenance and recreate only missing metadata for the same version and source SHA. The daily publication slot is already consumed. |
| Tag exists, crate absent | Investigate the tag's origin and source; do not let its existence silently mark the release complete. |
| Bad version successfully published | Revert/fix forward as a new version; assess yanking separately. Existing installs are not rolled back by yanking. |
| Two schedule/manual runs race | Serialization plus the in-lock registry recheck allows at most one new version. |
| Registry outage or inconsistent state | Fail closed and retain the candidate; report enough state for repair. |

A publish timeout can occur after the upload succeeded; Cargo documents that waiting for the index is a separate stage. [Cargo publish behavior](https://doc.rust-lang.org/cargo/commands/cargo-publish.html)

Save the version, source SHA, package checksum, registry timestamp, tag, release URL, and workflow run URL as release evidence. A missing GitHub Release should not erase evidence that the crate was published. Tag protection should also prevent silent retargeting.

## 7. Alternatives and when I would choose them

| Approach | Strength | Main cost | My judgment for Bob |
| --- | --- | --- | --- |
| crates.io + release-plz + gated publisher | Public versioned source installs, reviewable changelogs, little manual version work | Initial naming/license/CI work; small custom scheduler policy | Recommended for the stated objective. |
| Tagged Git installs, release-plz git-only mode | Avoid registry publication while gaining release tags and changelogs | Users still compile; weaker package discovery | Best fallback if public registry distribution is premature. |
| Manual `cargo publish` or cargo-release | Fewer background workflows for infrequent releases | Human coordination remains; not an unattended daily policy | Reasonable if releases will actually be rare. |
| Prebuilt binaries with cargo-dist | Better installation experience without compiling Bob locally | Target builds, system-dependency policy, signing/installer/release integration | Valuable second phase, or first priority if installation speed is the real need. |
| Publish on every successful push | Minimal scheduling logic | Breaks the requested cap and generates release noise | Not recommended. |

Current release-plz supports `git_only = true`, using tags rather than the registry as the version baseline. This is a real alternative; it is not equivalent to setting only `publish = false`. [Release-plz git-only configuration](https://release-plz.dev/docs/config#the-git_only-field)

cargo-dist focuses on building and distributing application binaries and installers. It complements version preparation; it does not remove the need to decide which source/version is eligible. If added, give one tool clear ownership of GitHub Release creation and make binary upload an explicit dependency/output-driven step. Do not assume tags created with `GITHUB_TOKEN` automatically trigger another release workflow. [cargo-dist introduction](https://axodotdev.github.io/cargo-dist/book/) and [GitHub token event rules](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow)

For just Bryan's existing development environment, I would not claim crates.io is necessary: pinned/tagged Git installs may suffice. I still favor crates.io here because the requested direction is public packaging and the existing layout is already close to supporting it.

## 8. Practical rollout and acceptance evidence

**Readiness first:** select the crate name and license; preserve executable/library identities as needed; document Linux/macOS prerequisites and package-rename migration; establish CI; reduce archive size where justified; verify a clean extracted-archive install. Preserve the existing developer checkout path for coordinated plugin/Mac-app development.

**Bootstrap second:** manually approve the first real version after dry-run checks. Publish once, verify registry installation, and create matching source tag/release metadata. Configure Trusted Publishing and verify a subsequent controlled release before removing the fallback credential.

**Automate third:** enable the PR generator and scheduled/dispatched publisher. Keep review manual initially. Test candidate selection, throttling, and recovery using mocked APIs or a disposable test repository/registry arrangement; do not burn real public versions to exercise failure cases.

Important acceptance cases:

- A changed commit after the release PR merge is excluded from that release.
- CI is run against the PR head actually published; merge-only green checks cannot substitute silently.
- A missing or skipped required check blocks publication, including an entirely empty check set.
- Nothing publishes for an open/unmerged PR or an unrecognized branch/actor.
- Two invocations, manual reruns, and delayed runs cannot publish two new versions within 24 hours.
- A registry outage is not treated as “no release yet”; yanking does not reset the timer.
- A publish-success/tag-failure state repairs metadata without another upload or version bump.
- Package tests pass outside the checkout, with no `sase/` content and all embedded assets/notices present.
- Installation into a temporary root produces all four executables and working completion; it never requires `--force` to overwrite another product.
- A release with no meaningful unpublished changes is a no-op.

The eventual install documentation, assuming the proposed name is chosen, can lead with:

```sh
cargo install bob-vault --locked
bob completion install
```

`--locked` uses the packaged lockfile rather than resolving newer dependency versions at installation time. Installing the package does not run shell-completion setup automatically. Keep upgrades user-driven and show a pinned-version install for rollback. [Cargo install documentation](https://doc.rust-lang.org/cargo/commands/cargo-install.html)

Unresolved owner choices are the final registry name, project license, exact supported platforms/Rust version, and whether “daily” means rolling 24 hours or UTC calendar days. No account ownership or publishing permission was assumed or exercised during this research. The live registry name checks should be repeated before implementation.

## Recommended solution

**Proceed with crates.io and release-plz, provisionally publishing as `bob-vault` while retaining the `bob` command.** Complete the license, package-margin, and Linux/macOS CI work first. Bootstrap one reviewed real release, then use Trusted Publishing from a dedicated scheduled/dispatched workflow. Maintain one reviewed release PR, select and test its actual publication SHA, serialize publication, and enforce one successful new version per rolling 24 hours using registry history. Poll eligibility hourly so failures can recover without weakening the cap.

Keep release-PR review until several releases establish confidence; postpone automatic upgrades and companion-repository deployment. Add cargo-dist afterward if avoiding local Rust builds matters. This delivers the requested release automation without pretending that a cron expression, a green branch badge, or the release-plz quickstart alone implements the policy.
