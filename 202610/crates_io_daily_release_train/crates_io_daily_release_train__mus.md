# Daily crates.io publishing for bob-cli via release-plz — research report

Researcher: mus. Date: 2026-10-19. Question: publish a package for
bob-cli (to crates.io?) with release-plz, releasing at most once a day
and only when all CI checks are green. Is this a good plan, and what is
the best implementation?

## TL;DR

- The plan is feasible, but **not as stated**: the crates.io name
  `bob-cli` is already taken by an unrelated project, the repo has no
  license (crates.io requires one), and the repo has no CI at all, so
  "when all CI checks are green" currently gates on nothing.
- With three adjustments — **rename the package**, **add a license**,
  and **create CI first** — release-plz on a daily cron schedule is a
  sound, low-maintenance setup, and this repo is unusually well suited
  to it (conventional commits already in use, single package,
  `just check` already the canonical gate).
- My critique: daily **crates.io** publishes buy Bryan almost nothing
  over what `cargo install --git` already does today, while adding
  public exposure and version churn for a vault-coupled personal tool.
  Recommended: implement the daily release-plz pipeline, but point it
  at **GitHub releases + git tags first**, and add crates.io only if a
  real consumer needs registry installs. Details in §7.

## 1. Current state of bob-cli (verified in-checkout)

| Fact | Evidence | Why it matters |
|---|---|---|
| Version is `0.1.0`, never released | `Cargo.toml` v0.1.0; `git tag` empty; `git log` shows only feat/fix/docs commits | First release needs one-time setup (see §4) |
| No CI exists | No `.github/` directory at all; default branch is `master`, not `main` | "When CI is green" requires building CI from scratch; all release-plz docs assume `main` — workflow triggers must say `master` |
| No license | No `LICENSE*` file; `Cargo.toml` has no `license` field; `cargo publish --dry-run` warns `manifest has no license` | crates.io rejects license-less publishes; also a legal prerequisite |
| Name `bob-cli` is taken on crates.io | crates.io API: `bob-cli` 0.3.2, owned by `Akagi201`, repo `longcipher/bob`, "CLI app for Bob - a general-purpose AI agent framework" | Publishing as `bob-cli` is impossible; rename is mandatory for any registry plan |
| Package is large but shippable | `cargo publish --dry-run`: 956 files, 30.2 MiB unpacked, **8.8 MiB compressed** | Under crates.io's 10 MB `.crate` limit ([Cargo Book](https://doc.rust-lang.org/cargo/reference/publishing.html)), but with only ~1 MB headroom — mostly vendored print fonts (`assets/`, 5.8 MB) |
| Conventional commits already used | `git log`: `feat(task-move): …`, `fix(ref): …`, `docs(…)`, all with scopes | release-plz's version inference works with zero commit-hygiene change |
| Git-based install already documented | `README.md:124`: `cargo install --git git@github.com:bobs-org/bob-cli.git --locked bob-cli` | The main distribution story already works without any registry |
| One package, four binaries | `[[bin]]`: `bob`, `bob_pomodoro`, `bob_notify`, `tmux_bob_pomodoro` | Single-version release train is simple; `cargo install <pkg>` drops all four binaries at once |
| Canonical local gate exists | `just check` = `cargo fmt --check` + `clippy -D unused …` + `cargo test --no-fail-fast` | CI can be one job that runs `just check` (+ `just check-scripts`) |

Two findings deserve emphasis. First, the name collision is a hard
blocker, not a preference: crates.io names are first-come, global, and
immutable. Second, the 8.8 MiB compressed size fits today, but any
growth in `assets/` (fonts, fixtures) risks hitting the 10 MB ceiling,
at which point the fix is excluding assets from the package or shipping
binaries another way (§6, option C).

## 2. How release-plz works (from upstream docs)

release-plz has two commands, normally run as two CI jobs on push to the
default branch ([quickstart](https://release-plz.dev/docs/github/quickstart)):

- `release-plz release-pr` — opens/updates a "release PR" bumping
  versions and changelogs (git-cliff, conventional-commit based).
- `release-plz release` — publishes every package whose local version
  is ahead of the registry: bumps `Cargo.toml`, writes changelog,
  commits, tags, pushes, runs `cargo publish`, creates a GitHub release.

Version inference follows semver from conventional commits
(`feat:` → minor once ≥1.0, `fix:` → patch; breaking → major). Two
config knobs matter most for this proposal ([config](https://release-plz.dev/docs/config)):

- `release_always` (default `true`): with `true`, `release` publishes
  on every run — i.e. on every push to the branch. With `false`, it
  publishes only when the latest commit belongs to a `release-plz-*`
  branch merge, i.e. only when the release PR lands.
- `release_commits = "<regex>"`: only prepare a release if some commit
  since the last tag matches, e.g. `"^feat:|^fix:"` to skip docs-only
  churn.

Authentication to crates.io has two options: a `CARGO_REGISTRY_TOKEN`
secret (needs `publish-new` + `publish-update` scopes), or
[trusted publishing](https://crates.io/docs/trusted-publishing) via
`id-token: write` — no long-lived secret. Caveat from the docs: **new
crates cannot be created via trusted publishing**; the first publish of
a new name must be done manually (token or `cargo publish` from a
machine), after which automation can take over updates.

Other facts that shape the design:

- `cargo publish` itself compiles the crate, so build breakage can
  never ship — but tests, clippy, and fmt are NOT run by publish.
  Upstream's preferred pattern is "CI runs on PRs; only merge green
  PRs" rather than re-running checks inside the release job
  ([advanced config](https://release-plz.dev/docs/github/advanced)).
- Tags pushed by the default `GITHUB_TOKEN` do not trigger further
  workflow runs (loop protection). The standard two-job push-triggered
  flow works around this deliberately; a cron-driven flow sidesteps it
  entirely.
- GitHub **disables scheduled workflows after 60 days of repo
  inactivity** — irrelevant for a daily-committed repo like this one,
  but worth knowing.

## 3. Implementing "at most once a day, only when CI is green"

There are two coherent architectures. I recommend A.

### Option A (recommended): one scheduled workflow, CI as a `needs` job

```yaml
on:
  schedule:
    - cron: "0 9 * * *"   # once daily; pick Bryan's morning
  workflow_dispatch: {}    # manual "ship now" escape hatch
jobs:
  ci:
    runs-on: ubuntu-latest
    steps: [ checkout, toolchain, run: just check ]
  release:
    needs: ci              # <-- the "only when green" gate
    permissions: { contents: write, id-token: write }
    steps: [ checkout (fetch-depth: 0), toolchain, release-plz `release` ]
```

With `release_always = true` (default), the daily `release` run
publishes **iff** releasable commits landed since the last tag — that is
already "at most once a day, and only when there is something to ship."
The `needs: ci` edge is the green gate, evaluated minutes before
publishing in the same run, which is stronger than "CI was green on the
last push." `concurrency: group: release-plz` with
`cancel-in-progress: false` prevents overlapping daily runs.

### Option B: keep the release-PR flow, merge it daily

Push-triggered `release-pr` job maintains the release PR;
`release_always = false` so merging it publishes; a scheduled job (or
Bryan) merges the release PR at most once a day. This preserves human
review of version bumps and changelogs, at the cost of three moving
parts (PR job, merge automation, publish-on-merge) and daily PR noise
for a single-maintainer tool. Only worth it if Bryan wants eyes on
every version bump.

Either way, two repo-specific adaptations are required: triggers must
target `master` (or rename the branch to `main` — the former is a
one-line change, the latter churns every checkout and script), and a CI
workflow (`just check` + `just check-scripts`) must exist before the
release workflow means anything.

## 4. Mandatory adjustments to the requirements

1. **Rename the package.** `bob-cli` is taken. Candidates in the same
   spirit: `bob-bugyi`, `bryan-bob`, `bob-vault-cli`. Verify
   availability via `https://crates.io/api/v1/crates/<name>` (404 =
   free) before committing. Binary names are unaffected: `[[bin]]
   name = "bob"` keeps installing the `bob` command, so the rename is
   invisible to users — only install commands change
   (`cargo install <new-name>`). Also update `README.md:124`'s
   `--git … bob-cli` reference.
2. **Add a license.** crates.io requires `license` (or
   `license-file`). No `LICENSE*` exists, so this is also a genuine
   legal gap, not just packaging. MIT-or-Apache-2.0 dual is the Rust
   default; single MIT is simplest for a personal tool. Bryan's call.
3. **Create CI before release automation.** There is no `.github/`
   directory. Minimum viable: one workflow running `just check` and
   `just check-scripts` on push/PR to `master`. The release job's
   `needs: ci` then has meaning.
4. **First publish is manual.** Either `cargo publish` from a logged-in
   machine (also proves the 8.8 MB package uploads cleanly) or a token
   publish; trusted publishing can own every subsequent daily release.
5. **Pin the "at most daily" semantics explicitly.** Cron gives "at
   most once a day" only together with `release_always = true` +
   publish-iff-changed (automatic) — document that a manual
   `workflow_dispatch` run can still ship intraday, which is a feature
   (hotfix escape hatch), not a violation.
6. **Decide the 0.x bump policy.** Default release-plz keeps `feat:`
   at patch level while `0.x` (correct per Cargo semver: `0.x → 0.x+1`
   is the breaking-change channel). The alternative,
   `features_always_increment_minor = true`, carries an upstream
   warning that it violates Cargo's semver rules. For a pre-1.0
   personal tool the default is fine; revisit at 1.0.

Optional but advisable: `release_commits = "^feat:|^fix:"` so docs- and
chore-only days produce no release at all, and a `CHANGELOG.md` at repo
root (release-plz generates it; review its first cut, since every
`feat:`/`fix:` subject since v0.1.0 will appear).

## 5. Critique: is daily crates.io publishing a good idea here?

Arguments for:

- Zero-touch releases match this repo's velocity (multiple conventional
  commits daily across capture/freshness/refs work).
- Version numbers + changelog become the shared language with the two
  downstream consumers (`bob-mac-capture` thin client speaks bob's JSON
  contract; `bob-plugins` syncs alongside it) — "fixed in 0.4.7" beats
  "fixed in some commit last Tuesday."
- Conventional-commit hygiene is already in place, so release-plz adds
  almost no process tax.

Arguments against (load-bearing):

- **No registry consumer exists.** Bryan's own machines install via
  `cargo install --path/--git` and `just install-all` from sibling
  checkouts; the README documents the git flow. Publishing to a public
  registry serves an audience of zero today while making every daily
  experiment a permanent public artifact (crates.io versions are
  immutable; yank exists but is a fire alarm, not undo).
- **Daily cadence erodes version meaning.** In `0.x`, every day mints a
  new "minor-or-patch" that downstream pins (`bob-mac-capture`,
  chezmoi-managed installs) must chase or ignore. For a tool whose real
  contract is the `bob` subprocess JSON surface, git SHAs or tags are
  already precise enough; registry versions add ceremony, not signal.
- **Public exposure of a personal tool.** Crates.io listing invites
  drive-by installs of something hard-coupled to Bryan's `~/bob`
  vault, Obsidian setup, and tailnet. Support/confusion cost with no
  upside.
- **Build cost stays local.** Registry publishing does not produce
  binaries — each Mac/tailnet install still compiles workspace deps
  including `rquickjs` from source. If install speed on athena/apollo/
  mac is the motivation, the answer is prebuilt binaries, not a
  registry version.

Net: the automation (release-plz + daily schedule + green-gated) is
good; aiming it at crates.io on day one is premature.

## 6. Alternatives considered

| Alternative | When it wins | Verdict here |
|---|---|---|
| A. release-plz → GitHub releases + tags only, no registry | Wants versioned artifacts + changelog with zero public surface | **Best starting point** (see §7) |
| B. `cargo install --git` + tags (status quo + discipline) | Zero new infrastructure | Viable, but manual tagging rots; release-plz automates exactly this |
| C. cargo-dist prebuilt binaries on GitHub releases | Slow compiles on tailnet Macs are the pain | Strong complement later; independent of registry decision |
| D. release-please (Google) instead of release-plz | Polyglot monorepo | No advantage: release-plz is Rust-native (semver check, `cargo publish` ordering) |
| E. Manual `cargo publish` on milestones | Rare, deliberate releases | Reasonable end-state for crates.io *if* a registry consumer ever appears |
| F. crates.io immediately, daily | External users need `cargo install <name>` | No such users today; revisit on demand |

Note on A: release-plz supports registry-less operation
(`publish = false`, tags + GitHub releases from the changelog pipeline),
which keeps the entire daily automation while skipping the rename
pressure for publishing purposes (a rename is still wise to reserve the
name, but stops being launch-blocking).

## 7. Recommended solution

**Phase 0 — prerequisites (one-time, ~1 hour):**

1. Choose and reserve the new package name (check 404 on the crates.io
   API); rename in `Cargo.toml`.
2. Add `LICENSE-MIT` (or dual MIT/Apache-2.0) + `license` field.
3. Add `.github/workflows/ci.yml`: `just check` + `just check-scripts`
   on push/PR to `master`.
4. Trim or justify `assets/` in the package: confirm the fonts are
   needed at *build/run* time by downstream installs; if they are
   render-time data better fetched elsewhere, `exclude` them and the
   8.8 MiB problem disappears permanently.

**Phase 1 — daily automated releases without the registry:**

5. Add `release-plz.toml` (`[workspace] publish = false`,
   `release_commits = "^feat:|^fix:"`, defaults elsewhere) and
   `.github/workflows/release-plz.yml` per Option A (§3) running on a
   daily cron + `workflow_dispatch`, release job `needs: ci`.
6. Let it run for 2–4 weeks. Evaluate: is the changelog readable? Is
   daily too noisy (then switch to weekly cron — one-line change)? Do
   downstream repos actually reference the versions?

**Phase 2 — expand only on evidence:**

7. If a machine or person genuinely benefits from `cargo install
   <name>`: do the one manual first publish, enable trusted publishing,
   flip `publish = true`. Nothing else changes.
8. If install *speed* on tailnet machines hurts: add cargo-dist for
   prebuilt `bob` binaries attached to the same daily GitHub releases.

Success criteria: releases happen with no human action; a red CI day
ships nothing (verify once by watching a cron run after a failing
push); `cargo install --git` and `just install-all` keep working
unchanged throughout.

## 8. Open questions for Bryan

- Preferred new crate name? (My shortlist: `bob-bugyi`, `bryan-bob` —
  confirm 404 first.)
- License preference: MIT only, or MIT-or-Apache-2.0?
- Is daily the right cadence, or would weekly releases with daily
  changelog accumulation be less noisy?
- Any real or anticipated consumer of a registry install (scripts,
  other machines, other people), or is GitHub releases + git install
  sufficient indefinitely?
- Should the daily release also cut a vault/Obsidian-visible note, or
  is the GitHub release page enough?

## Sources

- release-plz quickstart, advanced config, and configuration reference:
  `https://release-plz.dev/docs/github/quickstart`,
  `https://release-plz.dev/docs/github/advanced`,
  `https://release-plz.dev/docs/config` (notably the `release_always`
  field semantics and the `features_always_increment_minor` semver
  warning).
- crates.io API `GET /api/v1/crates/bob-cli` (2026-10-19): name taken,
  v0.3.2, owner Akagi201 / longcipher/bob — unrelated project.
- Cargo Book, "Publishing on crates.io": 10 MB `.crate` limit.
- In-checkout evidence: `Cargo.toml`, `justfile`, `README.md`
  (install docs at l.124, release checklist at l.1495),
  `docs/getting-started.md`, `cargo package --list` and
  `cargo publish --dry-run` output (956 files, 30.2 MiB / 8.8 MiB),
  `git log --oneline`, empty `git tag`, absent `.github/` and
  `LICENSE*`.
