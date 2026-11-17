# Stopping `bob plugins sync` Agent Blocking Safely: Root-Cause Analysis, Critique, and Architecture Options

## Executive Summary

SASE agents working on `bob-plugins` are **not** stalling on generic bash-command approval prompts (zero `CustomGate` requests exist for `bob plugins sync`). Instead, they are stalling inside **`UserQuestion` (`ace-gate`) prompts and multi-hour `sase_monitor` wait loops** triggered by `bob plugins sync`'s cross-checkout deploy guard (`src/native/plugins/deploy.rs`).

Across November 2026 up to 2026-11-16, `~/.sase/interaction_requests/question/` recorded **10 plugin-force-sync confirmation prompts**: 9 resolved waits totaling **1,691.0 minutes (28.18 hours)** of wall-clock blocking (several spanning overnight sessions) plus **1 prompt (`d8a8aeef` from `ei--6`) still pinned and unanswered** after a ~2h15m retry cascade (`ei--code` → `ei--mon..mon-4` → `ei--1..6`).

The underlying failure is a **structural phase inversion**:
1. `bob-plugins/AGENTS.md` (and `bob-cli/sase/memory/sase.md` / `bob-cli/sase/sase.yml`) instructs every coding agent to run `bob plugins sync` **before finishing its turn**.
2. SASE commits and pushes changes **after** the turn finishes via `builtin@commit` (`sase stitch create`).
3. Every agent that obeys `AGENTS.md` therefore deploys from an **uncommitted (`dirty`) worktree**, stamping `~/bob` plugins with `dirty` provenance — which causes the deploy guard in `src/native/plugins/deploy.rs` to block subsequent agents and trap them in wait/confirm loops.
4. This is compounded by four implementation defects in `bob-cli`: monorepo-wide `git status` dirtiness checks (`git_dirty`), un-scoped 11-plugin default syncs (`sync.rs`), gating `find_inclusion_proof` behind `incoming_clean == true`, and reading unset `SASE_AGENT_ID` instead of `SASE_AGENT_NAME`.

**Critique & Adjusted Requirements:**
Attempting to "stop asking permission to run `bob plugins sync`" inside the existing mid-turn flow is the wrong objective. Dropping the confirmation prompt or forcing `-F` silently destroys the anti-clobber guarantees introduced in `bob-cli-cu`, while running `bob plugins sync` mid-turn injects unreviewed WIP builds into the live `~/bob` vault even though `bob-plugins` automated E2E tests run in **isolated scratch vaults**. Instead, automated deployment to `~/bob` should be **removed from mid-turn coding agents** and either **executed post-commit from clean, pushed commits** or left exclusively to explicit/scheduled clean syncs (`just install-all`), alongside targeted hardening of `deploy.rs`.

**Recommended Solution:** **Option C (Post-Commit Clean Sync + Deploy Guard Hardening)**:
1. Remove the mandatory mid-turn `bob plugins sync` rule from `bob-plugins/AGENTS.md`, `bob-cli/sase/memory/sase.md`, and `bob-cli/sase/sase.yml`.
2. Deploy landed plugin builds **after `sase stitch create` commits and pushes**, pulling and syncing a dedicated clean checkout under an exclusive host `flock` (non-destructively skipping with a warning if Bryan holds a manual WIP deploy in `~/bob`), with **Option D (zero agent sync — `just install-all` / host timer only)** as a simpler alternative if immediate per-commit live-vault updates are not needed.
3. Harden `src/native/plugins/deploy.rs` (per-plugin dirtiness, decoupling `find_inclusion_proof` from `incoming_clean`, reading `SASE_AGENT_NAME`, clearer refusal version output) and clean up `bob-emoji` vault tracking.

---

## 1. Empirical Evidence: How `ei` and Parallel Agents Blocked

### 1.1 Measured Stall History (`~/.sase/interaction_requests/`)

Inspection of SASE interaction logs shows **0 `CustomGate` requests** for `bob plugins sync` and **10 `UserQuestion` requests** specifically asking Bryan whether to pass `--force` (`-F`) or wait on another agent's dirty plugin deploy:

| Timestamp | Request ID | Agent | Outcome / Duration | Trigger Summary |
| :--- | :--- | :--- | :--- | :--- |
| `2026-11-16T20:42:25` | `f5589f1b` | `bob-cli-mg.land--code` (`bob-cli_13`) | Resolved after **9.9m** | Blocked on `bob-cli_14` (`ei`) dirty `bob-ledger-tools` deploy (`866bb77`) |
| `2026-11-16T20:10:25` | `d8a8aeef` | `ei--6` (`bob-cli_14`) | **Unanswered (active pin)** after **~2h15m** pre-question loop | Blocked on `bob-cli_10` (`bob-cli-mf.6`) dirty `bob-navigation-hotkeys` deploy (`866bb77c`, `2026-11-17T00:45:25Z`) |
| `2026-11-16T20:01:19` | `7c7ab360` | `bob-cli-mf.6--3` (`bob-cli_10`) | Resolved after **67.0m** | Blocked on `bob-cli_14` (`ei--code` at `23:34:42Z`) dirty `bob-ledger-tools` deploy |
| `2026-11-15` | `c281f194` | Earlier November run | Resolved after **550.9m** | Plugin force-sync `UserQuestion` (includes overnight wait) |
| `2026-11-14` | `b4e83c50` | Earlier November run | Resolved after **400.2m** | Plugin force-sync `UserQuestion` (includes overnight wait) |
| `2026-11-13` | `c34ae903` | Earlier November run | Answered `Keep no-force` in **0.8m** | Plugin force-sync `UserQuestion` |
| `2026-11-12` | `bff44bd3` | Earlier November run | Resolved after **7.2m** | Plugin force-sync `UserQuestion` |
| `2026-11-09` | `e2846dfd` | Earlier November run | Resolved after **103.2m** | Plugin force-sync `UserQuestion` |
| `2026-11-01` | `d97194ca` | Earlier November run | Resolved after **550.8m** | Plugin force-sync `UserQuestion` (includes overnight wait) |
| `2026-11-01` | `9368680c` | Earlier November run | Resolved after **1.0m** | Plugin force-sync `UserQuestion` |

Even accounting for overnight AFK intervals in the ~400–550 minute entries, the 9 resolved prompts total **1,691.0 minutes (28.18 hours)** before counting `ei`'s ~2h15m autonomous sleep/poll cascade (`ei--code` → `ei--mon`..`ei--mon-4` → `ei--1`..`ei--6`) and ongoing `ace-gate` freeze.

### 1.2 Case Study: The 2026-11-16 Mutual Deadlock (`ei` ↔ `bob-cli-mf.6` → `bob-cli-mg.land`)

Reconstructing agent transcripts alongside live `.bob-deploy.json` stamps in `~/bob/.obsidian/plugins/` exposes a textbook three-way deadlock:

1. **Phantom cross-plugin dirty lock from `bob-cli-mf.6` (`bob-cli_10`):**
   `mf.6` modified only `bob-emoji` and `bob-ledger-tools`, then ran bare `bob plugins sync` (without `-p`). Because the sync loop (`src/native/plugins/sync.rs:74–132`) iterates all 11 configured plugins (`plugins.sync` in `~/.config/bob/config.yml`) and `git_dirty` (`src/native/plugins/deploy.rs:793–812`) checks dirtiness across the **entire monorepo**, `mf.6` inadvertently copied and dirty-stamped **untouched** `bob-navigation-hotkeys` (`version: 2.85.2`) at `2026-11-17T00:45:25Z` (`source_head: 866bb77c`, `agent: null`).
2. **`ei--code` (`bob-cli_14`) splits its sync and takes a dirty lock on `bob-ledger-tools`:**
   `ei` edited both `bob-navigation-hotkeys` and `bob-ledger-tools`. At `23:31Z`, `bob plugins sync` hit deploy refusals. Following `docs/develop/plugins/deployment.md`, `ei` ran the `git stash`/clean-sync/`git stash pop` workaround *only* for `bob-ledger-tools`, then rebuilt and synced `bob-ledger-tools` **dirty** at `23:34:42Z` before discovering `bob-navigation-hotkeys` was dirty-locked by `bob-cli_10`.
3. **Mutual deadlock + ripple:**
   - `ei` entered a ~2h15m wait loop (`ei--mon..mon-4` → `ei--1..6`, then `UserQuestion` `d8a8aeef`) waiting for `mf.6` to commit and land `bob-navigation-hotkeys` — which `mf.6` had never intentionally edited.
   - Simultaneously, `ei`'s dirty `bob-ledger-tools` stamp from `23:34:42Z` blocked **`bob-cli-mf.6--3`** (`7c7ab360`, 67.0m) from re-syncing `bob-ledger-tools` and finishing its turn!
   - A third agent, **`bob-cli-mg.land--code`** (`bob-cli_13`), later hit `ei`'s leftover `bob-ledger-tools` dirty lock too (`f5589f1b`, 9.9m).

Meanwhile, live `.bob-deploy.json` state on `apollo` showed:
- `8` plugins `clean` at `91e90979` (`/home/bryan/projects/github/bobs-org/bob-plugins`, `2026-11-16T18:49:05Z`)
- `bob-ledger-tools`: `clean` at `b5491d3b` (`bob-cli_13`, `2026-11-17T02:00:45Z`)
- `bob-emoji`: `dirty` at `2e87723b` (`bob-cli_15`, `2026-11-16T21:03:20Z`), also `vault_ignore.status == "tracked"` (4 files tracked in vault git and absent from `~/bob/.gitignore`)
- `bob-navigation-hotkeys`: `dirty` at `866bb77c` (`bob-cli_10`, `2026-11-17T00:45:25Z`), `manifest.json` `"version": "2.85.2"`, `agent: null`

---

## 2. Structural Root Causes in Code and Workflow

### 2.1 Mid-Turn Sync vs. Post-Turn `builtin@commit`

`bob-plugins/AGENTS.md` (lines 12–15) creates the hard loop:

> After any changes to files in this repo, you MUST run `bob plugins sync` to sync the repo changes to the vault.
> If `bob plugins sync` refuses to overwrite another checkout's deploy, never pass `-F` on your own and do not ask Bryan yet. Run `git fetch` and `git log --oneline HEAD..@{upstream} -- plugins/<id>`. ... If it has not landed and the agent named in the refusal is still running (`sase agent list`), wait for it to land instead of forcing. Ask Bryan only when the build is unlanded and abandoned.

Supporting instructions in `bob-cli` (`bob-cli/sase/sase.yml`, `bob-cli/sase/memory/sase.md`) repeat the rule that changes to `bob-plugins` must run `bob plugins sync` before completing.

However, SASE executes commits **after** the agent finishes its turn via `builtin@commit` (`sase stitch create`, orchestrated in `sase/src/sase/workflows/commit/workflow.py`). Consequently, **no SASE coding agent has committed its changes yet when it reaches the `bob plugins sync` step.** Every compliant agent writes a `DirtyState::Dirty` stamp, turning routine parallel work into forced contention.

### 2.2 Monorepo-Wide `git_dirty` + Un-Scoped Default Sync (`deploy.rs`, `sync.rs`)

- In `src/native/plugins/deploy.rs` (lines 793–812), `git_dirty(repo: &Path)` runs `git -C <repo> status --porcelain --untracked-files=all` across the entire `bob-plugins` repository root rather than scoping to `plugins/<id>/`.
- In `src/native/plugins/sync.rs` (lines 74–132), running bare `bob plugins sync` (when `-p`/`--plugin` / `options.only` is omitted) iterates all plugins listed in `options.configured` (`plugins.sync` in `~/.config/bob/config.yml`, 11 plugins).

Thus, modifying **any single file anywhere in `bob-plugins`** (for example `plugins/bob-emoji/`) marks **all 11 plugins** as `dirty` in their `.bob-deploy.json` stamps if bare `bob plugins sync` runs.

### 2.3 `incoming_clean` Blocks Safe Inclusion Proofs (`deploy.rs:940`)

In `src/native/plugins/deploy.rs` (`evaluate_guard`, lines 873–970):

```rust
let incoming_clean = captured.meta.kind == SourceGitKind::Worktree
    && captured.meta.dirty == DirtyState::Clean
    && captured.meta.head.is_some();
...
PriorStamp::Complete {
    stamp,
    matches_vault: true,
} if stamp.dirty == DirtyState::Dirty => {
    let same_checkout = stamp_root(stamp) == captured.meta.root;
    let same_host = stamp.host == current_host;
    if same_checkout && same_host { ... }
    else if incoming_clean
        && let Some(proving) =
            find_inclusion_proof(incoming_repo, plugin_id, stamp)
    {
        GuardDecision::Permit {
            stamp_action: StampAction::Write,
            proving_commit: Some(proving),
        }
    } else {
        // Refuses and requires --force / UserQuestion
    }
```

`find_holding_commit` (`deploy.rs:1112–1181`) scans up to `MAX_COMMITS = 500` commits (`git rev-list --max-count=500 <revs> -- plugins/<id>` + `git cat-file --batch`) to check whether the **currently installed vault bundle** already matches a committed ancestor in `HEAD`. That safety check verifies whether the *vault's* bytes are safely stored in Git — it does not depend on whether the *incoming* checkout happens to have unrelated dirty edits! Gating `find_inclusion_proof` behind `incoming_clean` forces agents with clean plugin dirs (or even after the prior holder actually landed) to run manual `git stash` dances or stall whenever their repo has *any* dirty file.

### 2.4 Concurrent Same-Plugin WIP Collisions Cannot Be Proven in Git

Even if `git_dirty` were scoped per plugin and `find_inclusion_proof` ran regardless of `incoming_clean`, two parallel agents modifying the **same** plugin (`ei` and `mf.6` both modifying `bob-ledger-tools`) cannot prove inclusion of each other's uncommitted local edits while both remain mid-turn. Pre-commit vault syncing guarantees mutual blocking whenever two agents touch the same plugin simultaneously.

### 2.5 Missing Agent Identity & Misleading Version Reporting

- `current_agent()` (`src/native/plugins/deploy.rs:191–196`) checks `bob_env::var("SASE_AGENT_ID")`, whereas SASE sets `SASE_AGENT_NAME` (`sase/src/sase/axe/run_agent_exec.py:285`, `run_agent_directive_identity.py:316`). Because `SASE_AGENT_ID` is unset, every `.bob-deploy.json` records `agent: null`, forcing waiting agents to correlate `workspace` numbers manually against `sase agent list`.
- In `d8a8aeef`, `ei--6` warned Bryan that forcing would replace version **`2.86.0`**, confusing the incoming checkout's `manifest.json` (reported via `bob plugins list -f json`) with what was actually on disk in the vault (`~/bob/.obsidian/plugins/bob-navigation-hotkeys/manifest.json` actually held `"version": "2.85.2"`).

---

## 3. Critique of the Original Plan & Adjusted Requirements

### 3.1 Critique: Is "Let Agents Sync Without Asking" a Good Idea?

**No — not as framed.** The question *"how do we stop agents from blocking to confirm `bob plugins sync` safely?"* assumes two things that turn out to be false upon inspecting `bob-plugins` and `sase`:

1. **Assumption 1: Coding agents need to sync `~/bob` during their turn.**
   In reality, `bob-plugins` E2E verification (`scripts/obsidian-startup-smoke.cjs`, `scripts/obsidian-closed-pomodoro-link-e2e.cjs`) creates and tests against **isolated scratch vaults**, not `~/bob`. Syncing your live personal vault mid-turn is almost never required by automated agent tests.
2. **Assumption 2: We can make mid-turn unlanded `bob plugins sync` conflict-free by tweaking confirmation policy.**
   - Simply permitting `--force` (`-F`), removing the confirmation rule from `bob-plugins/AGENTS.md`, or setting `autonomy.gates.question = auto` is **unsafe**: it reproduces the exact regression `bob-cli-cu` (`plans/202610/plugin_deploy_guard.md`) was built to stop — Agent B silently wiping Agent A's landed (or WIP) plugin bundle out of `~/bob`, only to rediscover bugs days later.
   - Conversely, preserving the guard *while still running `bob plugins sync` mid-turn* preserves the fundamental mismatch with `builtin@commit`: uncommitted builds collide by construction.
   - Even when unblocked, mid-turn agent syncs deploy **unreviewed, unmerged WIP** from ephemeral `bob-cli_<N>` checkouts into your live vault, leave `.bob-deploy.json` pointing to ephemeral workspace paths that SASE later recycles, run only on whichever host happened to execute the agent (`apollo` vs `athena`), and do not reload an already-open Obsidian window without restarting Obsidian anyway.

### 3.2 Justified Requirement Adjustments

Before designing the implementation, the requirements should be explicitly adjusted as follows:

| Original Framing | Adjusted Requirement | Rationale |
| :--- | :--- | :--- |
| **"Allow SASE agents to run `bob plugins sync` without blocking on confirmation prompts."** | **Remove `bob plugins sync` from ordinary mid-turn coding workflows altogether.** | Agents verify in scratch vaults and commit via `builtin@commit` at turn end; syncing mid-turn produces dirty stamps and polluted live state by design. |
| **"Keep `bob plugins sync` safe during multi-agent work."** | **Only landed, committed, clean `origin/master` states should auto-deploy to `~/bob`** (with an explicit opt-out / non-destructive skip if a human developer currently holds an intentional dirty WIP deploy in `~/bob`). | Eliminates `DirtyState::Dirty` contention among agents, aligns `.bob-deploy.json` with git ancestry, and ensures `~/bob` never runs unmerged WIP from dead workspaces. |
| **Implicit single-fix focus on prompt suppression.** | **Fix `deploy.rs` provenance & guard precision as defense-in-depth** (per-plugin dirtiness, decoupling `find_inclusion_proof` from `incoming_clean`, `SASE_AGENT_NAME`, clear vault-version output, `-p` scoping). | Protects human manual deploys and future interactive `bob plugins sync` runs from phantom locks (`bob-emoji` never locks `bob-navigation-hotkeys`) and makes refusal diagnostics truthful. |
| **Implicit assumption that agents coordinate via polling/waiting (`sase_monitor` + `sase agent list`).** | **Serialize host vault updates mechanically (Git pull + `flock`), never via LLM wait loops.** | Multi-hour `sase_monitor` loops burn quota and still cannot safely merge two uncommitted worktrees. |

---

## 4. Options Analysis

### Option A: Relax Prompt Policy / Auto-`--force` (Rejected)
- **Mechanism:** Remove the `UserQuestion` rule from `bob-plugins/AGENTS.md` or instruct agents to pass `-F`.
- **Pros:** One-line change; zero blocking immediately.
- **Cons:** Completely defeats the `bob-cli-cu` deploy guard. Silent last-writer-wins overwrites wipe landed fixes and human WIP from `~/bob`.
- **Verdict:** **Reject.**

### Option B: Harden `deploy.rs` + `AGENTS.md` Only, Keeping Mid-Turn Sync
- **Mechanism:** Keep pre-commit `bob plugins sync` in `AGENTS.md`, but scope `git_dirty` per-plugin, pass `-p <changed_plugins>`, allow `find_inclusion_proof` even when incoming tree has unrelated dirty edits, and fix `SASE_AGENT_NAME`.
- **Pros:** Eliminates **phantom cross-plugin locks** (the `bob-emoji` → `bob-navigation-hotkeys` half of the `ei`/`mf.6` deadlock) and automatically clears stale dirty stamps once the prior holder's commit reaches `HEAD`.
- **Cons:** **Fails whenever two agents edit the same plugin concurrently before committing** (`ei` + `mf.6` on `bob-ledger-tools`). Both still generate `DirtyState::Dirty` builds mid-turn, so waiting loops and `UserQuestion` prompts still trigger on every same-plugin overlap — and `~/bob` still receives uncommitted WIP builds from ephemeral `bob-cli_<N>` paths.
- **Verdict:** **Insufficient as the primary solution; valuable as Layer 2 hardening inside Option C.**

### Option C: Post-Commit Clean Sync + Deploy Guard Hardening (**Recommended**)
Move deployment out of agent turns into **`sase`'s post-commit pipeline**, synchronized through a **clean, `flock`-serialized host sync**, combined with `deploy.rs` hardening.

#### How Option C Works
1. **Agent Turn (`bob-plugins/AGENTS.md`, `bob-cli/sase/memory/sase.md`, `bob-cli/sase/sase.yml`):**
   - Stop requiring `bob plugins sync` after edits during agent turns.
   - Agents build (`npm run build`), typecheck/test, run scratch-vault smoke checks (`scripts/obsidian-startup-smoke.cjs` / E2E tests), and finish their turn cleanly. Note in `AGENTS.md` that manual/ad-hoc syncs from a dirty checkout must scope explicitly with `-p <plugin_id>`.
2. **Post-Commit Clean Deployment (`commit_hooks.after`):**
   - When SASE finishes the turn, `builtin@commit` runs `sase stitch create` in each modified repo, committing and pushing `bob-plugins` sequentially onto `origin/master`.
   - `sase/src/sase/workflows/commit/command_hooks.py` executes `commit_hooks.after` *after* push succeeds (`workflow.py:404`).
   - There are two ways `commit_hooks.after` can invoke `bob plugins sync`:
     - **Sub-variant C1 (Sync from the committed linked checkout `$PWD`):** Because `sase stitch create` just committed, rebased, and pushed, `$PWD` in `sase/repos/linked/bob-plugins` is guaranteed **clean** and on the latest `origin/master` commit. Running `flock ... bob plugins sync --repo "$PWD" --no-pull` needs no extra clone, **but** `.bob-deploy.json` records ephemeral `bob-cli_<N>/sase/repos/linked/bob-plugins` as `source_root` (fine for Git ancestry checks, slightly noisy in status output).
     - **Sub-variant C2 (Recommended — Serialized Clean Deploy Mirror):** Maintain a dedicated clean deploy checkout per host (e.g., `~/.local/share/bob/bob-plugins-deploy`, distinct from Bryan's personal editable `~/projects/github/bobs-org/bob-plugins` so personal dirty work there never blocks pulls). Under an exclusive `flock`, `commit_hooks.after` fast-forwards that mirror (`git fetch origin && git merge --ff-only origin/master`) and runs `bob plugins sync --repo "$mirror" --no-pull`. Every agent push updates the exact same canonical clean root (`DirtyState::Clean`, advancing strictly along clean Git ancestry), never leaving ephemeral `bob-cli_<N>` paths in `.bob-deploy.json`.
3. **Critical Implementation Details & Edge Cases Identified:**
   - **SASE Local-Config Trust (`files-and-merging.md`):** `commit_hooks.after` defined inside `<repo>/sase/sase.yml` is governed by `local_config_command_trust`. Unregistered or ambiguous checkouts (which currently includes `bob-plugins`, since it is a linked repo rather than a registered standalone SASE project) receive **checkout-scoped trust** — meaning ephemeral `bob-cli_<N>/sase/repos/linked/bob-plugins` checkouts would not automatically inherit trust unless either:
     - `bob-plugins` is registered as a SASE project / workspace-inherited trust rule in `sase`, **or**
     - the post-commit hook wrapper is configured in a trusted scope (e.g., user/project `sase.yml` / `sase` per-repo `commit_hooks` support, or registering `bob-plugins` in SASE).
     - *(Note: `builtin@command` finalizers in `sase/src/sase/finalizers/executor_command.py:262` currently reject any `cwd` other than `"primary"`, so `commit_hooks.after` — or extending `commit_hooks` trust/config — is the right hook point.)*
   - **Non-Destructive Handling of Human WIP & Headless Hosts:** `command_hooks.py` treats non-zero exit from `commit_hooks.after` as a hook failure (checkpointed so `sase stitch create --resume` retries `after_hook`). Therefore the hook script must:
     1. Exit `0` immediately on hosts without a local vault (`[ -d "${BOB_DIR:-$HOME/bob}/.obsidian" ] || exit 0`).
     2. **Not** force-overwrite if Bryan manually deployed an unlanded dirty plugin from his human checkout into `~/bob`! Instead, if `bob plugins sync` refuses (`exit 1`) because of a human dirty deploy, log a concise notification/warning and return `0` (so the git commit/push isn't marked failed) rather than hanging an agent or clobbering Bryan's active dev build. (Every other clean/proven deploy succeeds cleanly with `exit 0`.)
   - **Merged Bundle Freshness on Rebase:** When two agents concurrently modify *different* TypeScript files in the same plugin, `git rebase` during `sase stitch create` may merge `.ts` sources cleanly while built bundles (`main.js`) collide or grow stale relative to one agent's build. Running a build / build-freshness verification before commit or push (or rebuilding if conflict/rebase occurred) ensures `main.js` always matches the rebased commit before pushing and deploying.
   - **Note on Obsidian Reload:** `bob plugins sync` updates files on disk; running `just install-all` still handles pulling across checkouts and restarting Obsidian when `copied > 0`, just as `scripts/install_all` does today.
4. **Layer 2 (`bob-cli/src/native/plugins/`) Hardening:**
   - Scope `git_dirty` per plugin (`plugins/<id>/` plus shared build/root manifests such as root `package.json` / `package-lock.json` / build scripts — verify build inputs conservatively so shared build edits still flag dirtiness accurately).
   - Remove the `incoming_clean` prerequisite before calling `find_inclusion_proof` when prior stamp is `Dirty` (`deploy.rs:940`).
   - Read `SASE_AGENT_NAME` as fallback alongside `SASE_AGENT_ID` in `current_agent()`.
   - Surface the installed vault's `manifest.json` version explicitly alongside the incoming repo version in refusal/list diagnostics.
   - Untrack `bob-emoji` in `~/bob` git and add `.obsidian/plugins/bob-emoji` to `~/bob/.gitignore`.

### Option D: Zero Agent Sync — Manual `just install-all` or Host Timer Only
- **Mechanism:** Remove mid-turn `bob plugins sync` from `AGENTS.md` / `sase` docs cleanly (same as Option C step 1) and also apply Option C Layer 2 (`deploy.rs` hardening), **without** wiring `commit_hooks.after`. Live `~/bob` updates only when Bryan runs `just install-all` or via a periodic host cron/systemd timer pulling clean `origin/master`.
- **Pros:**
  - Simplest architecture with zero SASE hook/trust plumbing (`command_hooks.py` trust rules untouched).
  - Cross-host consistent: `athena` workers and `mac` get synced on pull/timer rather than only on whichever host ran the agent (`apollo`).
  - Protects multi-phase epics (`bob-cli` + `bob-plugins` contract changes) from landing half-way into a running `~/bob` session before Bryan is ready to restart Obsidian.
- **Cons:** Agent commits don't appear in `~/bob` automatically on the second the turn finishes; Bryan waits for the timer (e.g., 1–5 min) or `just install-all`.

### Comparison Matrix

| Criterion | Option A (Auto `-F`) | Option B (`deploy.rs` + `AGENTS.md` Only) | Option C (Post-Commit Clean Sync + Guard Fixes) | Option D (Zero Agent Sync + Timer / `install-all`) |
| :--- | :--- | :--- | :--- | :--- |
| Eliminates phantom cross-plugin locks | Yes | Yes | Yes | Yes |
| Eliminates same-plugin concurrent deadlocks | Yes (by clobbering) | **No** | **Yes** | **Yes** |
| Prevents silent overwrite of landed/human WIP | **No** | Yes | Yes | Yes |
| Keeps uncommitted agent WIP out of `~/bob` | **No** | **No** | **Yes** | **Yes** |
| Clean linear `.bob-deploy.json` provenance | **No** | **No** | **Yes** | **Yes** |
| Needs `sase` hook/trust setup | No | No | Yes (one-time) | No |
| Instant `~/bob` deploy upon commit landing | Mid-turn | Mid-turn | **Yes (post-push)** | On `install-all` / timer |

---

## 5. Recommended Solution & Concrete Rollout Plan

**Recommendation:** Adopt **Option C (Sub-variant C2: Serialized Post-Commit Clean Mirror Sync + `deploy.rs` Hardening)**.
If you prefer zero hook complexity and already rely on `just install-all` when restarting Obsidian (or want cross-host symmetry across `apollo`, `athena`, and `mac`), **Option D** shares Phases 1 and 2 identically and simply swaps Phase 3's hook for a host clean-pull timer.

### Phase 1 — Immediate Unblock (Policy + Hygiene, Low Risk)
1. **`bob-plugins/AGENTS.md`:** Replace the mandatory *"After any changes to files in this repo, you MUST run `bob plugins sync`"* directive with:
   - Agents **do not** run `bob plugins sync` during normal coding turns (verify via build + scratch-vault E2E scripts instead).
   - Sync to `~/bob` happens post-commit from clean `origin/master` (or manually via `just install-all`).
   - Reserve mid-turn `bob plugins sync -p <plugin_id>` strictly for explicit `--deployed-vault` smoke tasks, always scoped to `-p <id>`.
2. **`bob-cli` instructions (`bob-cli/sase/sase.yml`, `bob-cli/sase/memory/sase.md`):** Update the `bob-plugins` repo description and check rules so agents are no longer told to run `bob plugins sync` before ending turns. (Do not edit generated `AGENTS.md` directly; regenerate via `sase memory init`.)
3. **Vault `.gitignore` cleanup (`~/bob`):** Untrack `.obsidian/plugins/bob-emoji` in `~/bob` Git and add `.obsidian/plugins/bob-emoji` to `~/bob/.gitignore`.
4. **Clear the current stuck queue (`apollo`):** Once `mf.6` lands or after verifying `~/bob/.obsidian/plugins/bob-navigation-hotkeys/manifest.json` (`2.85.2` vs `ei`'s branch), unblock `d8a8aeef` cleanly rather than letting stale `bob-cli_10` state linger.

### Phase 2 — Harden `bob-cli` Deploy Guard (`src/native/plugins/`)
1. **Per-plugin dirtiness in `deploy.rs`:** Replace global `git_dirty(repo)` in per-plugin evaluation with a scoped check covering `plugins/<id>/` (plus shared root manifest/build-config inputs so cross-cutting build script edits remain flagged as dirty).
2. **Decouple `find_inclusion_proof` from `incoming_clean` (`deploy.rs:940`):** Whenever prior stamp is `Dirty` and vault bytes match a commit found by `find_inclusion_proof(incoming_repo, plugin_id, stamp)`, permit overwriting cleanly regardless of unrelated dirtiness in the incoming tree.
3. **Agent attribution (`deploy.rs:191–196`):** Update `current_agent()` to read `SASE_AGENT_NAME` when `SASE_AGENT_ID` is absent so every `.bob-deploy.json` records the real SASE agent name.
4. **Truthful version display:** Include the vault's installed `manifest.json` version alongside the incoming repo version in refusal errors and `bob plugins list -f json` so agents never conflate incoming and installed versions (`2.86.0` vs `2.85.2`).

### Phase 3 — Post-Commit Clean Sync (or Host Timer Fallback)
1. **Clean mirror helper script** (in `bob-plugins` or `bob-cli`, e.g. `bob-plugins/scripts/post-commit-deploy.sh`):
   - Check `[ -d "${BOB_DIR:-$HOME/bob}/.obsidian" ] || exit 0` (no-op on headless/vaultless hosts).
   - Acquire exclusive `flock` on a user runtime lockfile.
   - Ensure a dedicated clean deploy mirror (e.g., `~/.local/share/bob/bob-plugins-deploy`) is fast-forwarded to `origin/master` (`git fetch origin && git merge --ff-only origin/master`).
   - Run `bob plugins sync --repo "$MIRROR" --no-pull`. If it exits non-zero because a human dev currently holds an intentional dirty WIP deploy in `~/bob`, emit a warning/notification and exit `0` rather than failing `sase stitch create` or forcing `-F`.
2. **Wire post-commit execution cleanly with SASE trust:**
   - Verify/resolve linked-repo `commit_hooks.after` trust (register `bob-plugins` in SASE or support workspace-inherited/trusted hook invocation so `bob-cli_<N>/sase/repos/linked/bob-plugins` executes reliably without per-workspace manual `sase config trust allow`).
   - Pair with pre-push build verification (`npm run build` / build-freshness check, or CI gate) so merged `main.js` bundles always reflect the final pushed commit even after multi-agent rebases.
   - *(Alternative if preferring Option D: skip step 2 and run the exact same `flock` clean-mirror `bob plugins sync` via `just install-all` plus a lightweight host timer on `apollo`, `athena`, and `mac`.)*
