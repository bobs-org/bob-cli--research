# Replacing Obsidian Sync with GitHub as the Only Vault Sync Channel

- **Date:** 2026-08-27
- **Vault:** `~/bob` on athena, remote `git@github.com:bobs-org/bob.git` (branch `master`)
- **Devices:** athena (Debian 13, always-on home server) and a MacBook, frequently used
  *at the same time*
- **Question:** What is the best way to drop Obsidian Sync and make the vault's GitHub
  repo the primary and only sync channel between the two machines, with minimal friction
  and minimal resource use?

**Recommendation in one line:** do **not** use the Obsidian Git plugin as the sync
engine — put the whole reconcile cycle in a new cross-platform `bob vault-sync`
subcommand, drive it from a watch-plus-poll loop (systemd on athena, `launchd` on the
Mac), and resolve every conflict automatically with a **Syncthing-style conflict copy**
instead of conflict markers.

---

## 0. Executive Summary

| | Finding |
| --- | --- |
| **The cost objection is dead** | Measured on the real vault: `git status` = **0.01–0.05 s**, `git add -A --dry-run` = **0.02 s**, remote poll = **0.49 s**, or **0.22 s** with SSH connection multiplexing. A 15-second poll loop costs roughly 1.5 % of one core and nothing measurable in RAM. Resource use is a non-issue. |
| **The real cost is latency, not CPU** | Obsidian Sync is push-based and sub-second. Git must be polled. A well-tuned loop gives ~5–10 s local→remote and ≤15 s remote→local. That is 10–20× slower than today, and it is still fine for one human with two keyboards. |
| **The real risk is conflict *handling*, not conflict *frequency*** | Git's default behaviour on conflict — write `<<<<<<<` markers into the note and stop — is unacceptable for an unattended daemon editing files Obsidian has open. This is the single design decision that makes or breaks the project. §5 solves it. |
| **The Obsidian Git plugin is the wrong engine here** | It only runs while Obsidian is open, its finest interval is minutes, it has no unattended conflict policy, upstream docs never address multi-desktop use, and it would race `bob nightly`'s cron commits. Keep it installed as a *read-only* UI, not as the sync engine. |
| **One silent regression found** | Obsidian Sync currently carries your six custom `bob-*` plugins between machines via its `community-plugin` config type. Git **cannot**: they are explicitly `.gitignore`d. Under git-only sync the MacBook stops receiving plugin updates unless you run `bob plugins sync` there. §7.1. |
| **Repo hygiene is a prerequisite** | `.git` is **1.3 GB** and the working tree is **1.8 GB**, of which `old_lib/` alone is **1.7 GB**. 7,566 loose objects / 565 MiB are un-GC'd. Two `old_lib` PDFs exceed GitHub's 100 MiB hard limit and are already excluded. §6. |

---

## 1. What Exists Today (all verified on athena)

### 1.1 The sync path being replaced

`ob-sync-bob.service` (systemd user unit, `active/running`) runs
`~/.local/bin/ob-sync-bob-poll`, a bash loop that calls
`ob sync --path /home/bryan/bob` every **30 s** under a 120 s `timeout`. `ob` is the
`obsidian-headless` client, logged in to Obsidian Sync.

Live sync configuration (`ob sync-status --path ~/bob`):

```text
Vault:             bob (8a259ad922718b6d8400c1f0e3ba8abe)
Sync mode:         bidirectional
Conflict strategy: merge
Device name:       athena-headless
File types:        image, audio, pdf, video
Configs:           community-plugin, community-plugin-data, hotkey,
                   appearance, appearance-data
Excluded folders:  old_lib
```

Two facts from that block matter a lot later:

1. **`old_lib` is already excluded from Obsidian Sync.** The MacBook does not have the
   1.7 GB archive today, so keeping it off the Mac under git is *not* a regression — it
   is the status quo, and `git sparse-checkout` reproduces it exactly (§6.3).
2. **`community-plugin` is a synced config type.** That is how the custom `bob-*`
   plugins reach the Mac today, and git will not do it (§7.1).

### 1.2 The git path that already exists

Git is currently a *backup*, not a sync. `bob bulk-git-commit`
(`src/native/sync.rs:48`) does exactly three things:

```
git add -A .   →   git commit (if staged changes)   →   git push
```

It **never fetches or pulls**, and it holds an exclusive `flock` on
`${XDG_RUNTIME_DIR:-/tmp}/bob_sync.lock` (`src/native/ob.rs:250`, `:298`).

`bob nightly` (`src/native/nightly.rs`) takes that same lock, runs `ob sync` once as a
"shared gate", then runs `move-done-tasks` and `bulk-git-commit`. It is driven by cron:

```cron
30 3 * * * bash -c ". $HOME/.profile; . $HOME/.config/nvm/nvm.sh; nvm use --silent default; bob nightly" >> /var/tmp/bob_nightly.log 2>&1
```

**Consequence:** `bulk-git-commit`'s commit-without-pull is safe *only* because Obsidian
Sync guarantees the tree is already converged when it runs. Remove Obsidian Sync and
that assumption evaporates — a cron commit at 03:30 on athena will diverge from whatever
the Mac pushed, and nothing in the current code path merges it. This is not optional
cleanup; it is a correctness fix that must ship with the switch.

### 1.3 Measured cost of a git-based cycle

Run against the live `~/bob` (git 2.47.3, 6,407 tracked files, 6,434 files on disk):

| Operation | Time | Notes |
| --- | --- | --- |
| `git status --porcelain` (cold) | **0.05 s** | |
| `git status --porcelain` (warm) | **0.01 s** | No `core.fsmonitor`, no `untrackedCache` configured |
| `git add -A --dry-run` | **0.02 s** | |
| `git fetch --dry-run` | 0.56 s | Dominated by the SSH handshake |
| `git ls-remote origin master` | 0.49 s / 0.52 s | Two consecutive runs |
| `git ls-remote` with `ControlMaster`/`ControlPersist` | **0.23 s / 0.22 s** | Warm multiplexed connection |

**Read this carefully:** the local half of a sync cycle is *already* fast enough that
`core.fsmonitor` and `core.untrackedCache` would be pure ceremony — 10 ms does not need
optimising. The entire cost of the loop is the network round trip, and SSH connection
multiplexing cuts that **in half** for one line of `~/.ssh/config`.

### 1.4 Vault shape

| Path | Size | Comment |
| --- | --- | --- |
| `~/bob` total | 1.8 GB | |
| `~/bob/.git` | 1.3 GB | 12,041 in-pack (689.59 MiB) + 7,566 loose (565.30 MiB) |
| `~/bob/old_lib` | **1.7 GB** | Archival PDFs/videos. Excluded from Obsidian Sync |
| `~/bob/img` | 63 MB | Screenshots pasted into notes |
| `~/bob/.obsidian` | 11 MB | |
| Everything else (the actual notes) | **< 25 MB** | `2024`–`2026`, `lib`, `ref`, `_generated`, route notes |

Commit history: 279 commits since 2026-05-30, currently a rigid **2 commits/day**
(`move-done-tasks` + `bulk-git-commit` from cron). Typical churn per commit:
6–18 files, ~150–290 insertions. **The notes themselves are tiny and change slowly** —
this vault is an ideal git-sync candidate once `old_lib` is handled.

### 1.5 Obsidian installations

| Machine | Install | Relevance |
| --- | --- | --- |
| athena | **snap `obsidian` 1.13.7, `classic` confinement** (verified via `snap info`) + `obsidian-headless` (`ob`) | See §3.2 — the plugin docs' snap warning is about *strict* confinement and does not literally apply, but snap remains an unsupported configuration upstream |
| MacBook | Assumed standard `.dmg` | Not directly verifiable from athena |

athena's `fs.inotify.max_user_watches` is **505,837** — far above the ~6.4 k the vault
needs, so a file watcher is safe to add.

`bob-cli` is **already cross-platform**: `Cargo.toml:33` declares
`[target.'cfg(target_os = "macos")'.dependencies]` (`plist`, `rusqlite`),
`src/native/capture_clip.rs` branches on `target_os`, and `docs/highlights-ref-sync.md`
contains a MacBook setup guide. Bob Mac Capture already shells out to `bob` on the Mac.
**A new `bob` subcommand is automatically available on both machines.**

---

## 2. What You Are Actually Giving Up

Obsidian Sync is not merely "a sync service"; it has three properties git does not.

| Property | Obsidian Sync | Git | Verdict |
| --- | --- | --- | --- |
| **Transport** | Push (websocket), sub-second | Pull (polled) | **Real loss.** Mitigated to 5–15 s in §5. |
| **Markdown merge** | Google `diff-match-patch` three-way merge — character/word granularity, auto-merges same-line edits | Line-based three-way merge — auto-merges different regions, **conflicts on same-line edits** | **Small loss.** Git's line merge is fine for prose and for the vault's list-structured notes. |
| **Non-markdown merge** | "Last modified wins" | Conflict | **No loss** — §5.3 makes git behave the same way. |
| **Failure mode** | Silent auto-merge, or an explicit conflict file if configured | Conflict markers written into the file, operation halted | **This is the dangerous one.** §5 replaces it. |
| **Mobile** | First-class | Upstream calls the mobile git implementation "**very unstable**" and recommends a different sync service | **Blocking, if a phone is in scope.** See the open question in §9. |
| **History** | Per-file version history UI | `git log` / `git blame` over the whole vault | **Net gain.** |

The honest framing: git's *merge quality* is close enough, its *latency* is 10–20×
worse but still sub-half-minute, and its *failure behaviour* is unacceptable out of the
box and must be engineered around. That third point is the whole project.

---

## 3. Option Analysis

### 3.1 Option A — Obsidian Git plugin on both machines

The community plugin (`Vinzent03/obsidian-git`) with "Auto commit-and-sync interval",
"Auto commit-and-sync after stopping file edits", and "Auto pull interval". Community
guidance converges on 10–15 minute intervals for both, plus "pull on startup", with
shorter intervals when switching devices often.

**Why it fails for this vault specifically:**

1. **It only runs while Obsidian is open.** athena is a *server*. Its vault is mutated
   by `bob nightly` at 03:30, by `bob capture`, `bob move-done-tasks`, and by SASE
   agents — often with no GUI running. Any window where Obsidian is closed is a window
   where athena silently stops syncing.
2. **It would race `bob bulk-git-commit`.** Two independent processes doing
   `add -A`/`commit`/`push` on the same worktree, only one of which respects
   `bob_sync.lock`. Guaranteed intermittent non-fast-forward failures.
3. **Interval granularity is minutes, not seconds.** For "both machines at once", a
   10-minute pull interval means a 10-minute divergence window on every shared note.
4. **No unattended conflict policy.** On conflict it leaves markers in the note and
   requires you to resolve by hand — in a file you may currently be typing into.
5. **Upstream does not support this use case.** The official docs' "Getting Started"
   page covers initial setup and authentication only; it is silent on pull frequency,
   conflict strategy, and multi-device coordination. The plugin's own framing is
   explicit: *"Git is not meant to share your changes live to the cloud or another
   person."*

### 3.2 A note on the snap warning (a correction worth having)

The plugin's installation docs list Snap as "**not fully supported**" because "Snap puts
Obsidian in a kind of sandbox, so that Obsidian can't access Git", and Flatpak as not
recommended because it "can access Git, but not all system files". AppImage is the
supported Linux method.

**That reasoning does not apply to athena.** `snap info obsidian` reports
`1.13.7 (67) 116MB classic` — the publisher ships it under **classic confinement**,
which means no sandbox and full system access, so `git` and `~/.ssh` are reachable.
Chalk one common objection off the list. It remains an upstream-unsupported
configuration, and if you ever *do* want the plugin as more than a viewer, switching
athena to the AppImage is the low-drama move. This does not change the recommendation,
because the recommendation does not depend on the plugin.

### 3.3 Option B — External sync daemon on both machines *(recommended)*

A single reconcile routine invoked by an OS-native watch-and-poll loop, independent of
whether Obsidian is running.

**Pros:** works headless; shares `bob_sync.lock` with existing automation by
construction; conflict policy is entirely yours; measured cost is trivial; one
implementation serves both machines because `bob` is already installed on both; testable
in `bob-cli`'s existing Rust test suite.

**Cons:** you own the code. Roughly 300–400 lines of Rust plus two small unit files.
That is the price of the conflict policy in §5, and there is no off-the-shelf tool that
provides it.

**Prior art to borrow from, not depend on:** `simonthum/git-sync` (a careful
"safe and simple" one-script synchroniser, with a `git-sync-on-inotify` companion that
watches for events and still polls upstream on an interval) and `gitwatch` (inotify →
commit → push). Both validate the loop shape. Neither offers conflict-copy resolution or
integrates with the `bob` lock, which is why this is a build rather than an install. You
already run the same pattern for `pass`: `pass_git_sync` on an hourly cron does
`pass git pull` then `pass git push`, and its own help text concedes "merge conflicts in
the password store still require manual resolution" — that is exactly the gap the vault
version must close.

### 3.4 Option C — Hybrid *(recommended as a garnish)*

Option B as the engine, **plus** the Git plugin installed on both machines with *every*
automation setting disabled. You get its Source Control view, History view, and Line
Authoring (`git blame` in the gutter) as a read-only UI, and a graphical place to
inspect what the daemon did — without letting it commit anything.

### 3.5 Options rejected

| Option | Why not |
| --- | --- |
| **Syncthing (+ git for backup)** | The standard answer for frictionless concurrent editing, and genuinely better at it than git — but it is a second sync channel, which is precisely what you asked to eliminate. Worth knowing it exists if the git latency ever grates. |
| **Obsidian LiveSync (self-hosted CouchDB)** | Not git. Also a server to run and back up. |
| **Keep Obsidian Sync, add git** | The status quo. Rejected by the premise. |
| **athena as an SSH/NFS-mounted vault for the Mac** | Obsidian's file watchers are documented to be unreliable on network and FUSE mounts. Also fails when the MacBook is off-LAN. |

---

## 4. The Failure Mode That Must Be Designed Away

Concretely: it is 09:15. You are typing into `2026/20260827.md` on the MacBook. Ninety
seconds ago you added a Pomodoro to the same section on athena, and it has been pushed.
The Mac daemon fetches, merges, and hits a conflict on adjacent lines.

Default git behaviour writes this into the file you are typing in:

```markdown
    <<<<<<< HEAD
- [ ] 🍅 Review the capture grammar ^p3
    =======
- [ ] 🍅 Draft the sync design doc ^p3
    >>>>>>> origin/master
```

Obsidian reconciles external on-disk changes into open notes through its normal update
pipeline (it watches via chokidar), so **those markers appear live in your editor**, in
a file whose task syntax `bob` and the Tasks plugin both parse. Meanwhile the repo is
left mid-merge, and every subsequent sync cycle fails until you intervene.

Now add athena's automation to the same picture: `bob move-done-tasks` rewriting task
lines at 03:30, `bob task-status-hooks` reconciling dependency markers, `bob capture`
appending to route notes. A halted merge is not a nuisance here — it is a stalled sync
channel plus a corrupted ledger.

**Conclusion: an unattended vault sync must never leave conflict markers and must never
halt.**

---

## 5. Recommended Design — `bob vault-sync`

### 5.1 One reconcile cycle

Idempotent, lock-protected, safe to invoke at any time from any trigger.

Before staging anything, the command must refuse to proceed if a merge, rebase,
cherry-pick, or unresolved index is already present. It should report the exact state
and recovery command rather than layering a second operation over an interrupted one.
That guard is distinct from the conflict-copy policy below: the daemon may resolve a
conflict that *it* creates during the current cycle, but it must not guess at a human's
or another tool's unfinished Git operation.

```
1.  flock ${XDG_RUNTIME_DIR:-/tmp}/bob_sync.lock  (non-blocking; exit 0 if held)
2.  git add -A .
3.  if staged changes: git commit -m "vault sync <host> <ISO-8601>"
4.  git fetch origin master                       (GIT_SSH_COMMAND with ControlMaster)
5.  if HEAD == origin/master: done
6.  if HEAD is an ancestor of origin/master: git merge --ff-only origin/master; goto 9
7.  git merge --no-edit origin/master
8.  on conflict: resolve every conflicted path per §5.3, git add, git commit
9.  git push
10. if push rejected (non-fast-forward): goto 4, bounded to 3 retries
```

**Merge, not rebase.** A failed rebase leaves the worktree in a partially-replayed,
detached-HEAD state with an arbitrary number of remaining conflicts — the worst possible
thing to hand to a running Obsidian. A merge has exactly **one** conflict point, one
resolution pass, and one commit. History noise is irrelevant for a notes vault. Note
that the plugin's own pull tries rebase first and falls back to merge on conflict; skip
the first step and go straight to the reliable one.

**Reuse the lock, don't invent one.** `ob::acquire_lock()` already returns `Err(0)` when
another run holds it. Steps 2–3 are literally `sync::commit_and_push_vault` minus the
push, so most of this is refactoring, not new code.

### 5.2 Triggers

**athena (Linux)** — replace `ob-sync-bob.service` with `bob-vault-sync.service`, a
`Type=simple` user unit running one loop:

```bash
while true; do
  inotifywait -q -r -t 15 -e modify,create,delete,move \
    --exclude '(/\.git/|/\.obsidian/workspace|/\.trash/|/\.sase/)' \
    "$BOB_DIR" >/dev/null
  sleep 5                 # debounce: Obsidian writes ~2 s after you stop typing
  bob vault-sync
done
```

`inotifywait -t 15` returns either on a file event *or* on timeout, so **one process and
one blocking wait** gives you both edge-triggered local pushes and a 15-second remote
poll. When nothing happens, the loop costs one `git status` (10 ms) and one multiplexed
`ls-remote` (220 ms) per 15 s.

**MacBook (macOS)** — a `launchd` LaunchAgent with `KeepAlive`, running the same loop
with `fswatch` in place of `inotifywait`. Prefer this over `launchd`'s built-in
`WatchPaths`, which is unreliable for deep recursive trees and gives you no debounce
control. Consider gating on AC power / network reachability to be kind to the battery.

Latency budget: **local edit → remote ≈ 5–10 s** (2 s Obsidian write + 5 s debounce +
push); **remote edit → local ≤ 15 s + fetch**.

### 5.3 Conflict policy — the conflict copy

On conflict, for each conflicted path:

| Path type | Action |
| --- | --- |
| Text (`.md`, `.canvas`, `.base`) | Check out **`--theirs`** (the remote version) into place. Write the **local** version to `<dir>/<stem>.conflict-<host>-<YYYYMMDDTHHMMSS><ext>`. `git add` both. |
| Binary (images, PDFs, audio, video) | Same shape, but the decision is whole-file: remote wins in place, local is preserved as a conflict copy. Matches Obsidian Sync's "last modified wins" for non-markdown. |
| Delete/modify | Keep the file (never let an unattended daemon win a delete race). Log it. |

Then commit and push, and record one line per conflict in a `sync_conflicts.md` inbox
note (plus a desktop notification — `bob notify` already exists).

**Why this is the right call:** nothing is ever lost, the sync channel never stalls, no
markers ever appear in a live note, and the conflict copy is an ordinary vault note you
can open, diff, and merge in Obsidian at your leisure. This is exactly Obsidian Sync's
own "Create conflict file" strategy, which is an offered first-class option there — you
are re-implementing a supported behaviour, not inventing a hack.

Remote-wins-in-place is the correct default direction: the remote version is the one the
*other* machine already considers committed, while your local version is the one you are
still sitting in front of and can most easily re-apply.

### 5.4 Do NOT use `merge=union`

It is the tempting one-line "fix" (`*.md merge=union` in `.gitattributes`) and it is a
trap. Union merge concatenates both sides of every conflicting hunk with no
understanding of content. On this vault that means **silently duplicated task lines** in
the Pomodoro ledger and in route notes — duplicated `^blockid`s, duplicated checkboxes,
double-counted Pomodoros. A conflict you can see beats a corruption you cannot.

### 5.5 `.gitattributes` (currently absent — add it)

```gitattributes
* text=auto eol=lf
*.png binary
*.jpg binary
*.jpeg binary
*.gif binary
*.webp binary
*.pdf binary
*.PDF binary
*.mp3 binary
*.mp4 binary
*.mov binary
*.m4a binary
*.webm binary
*.mkv binary
```

`binary` is shorthand for `-diff -merge -text`, which guarantees git never tries a
textual merge on an image and never corrupts one with markers. With 63 MB of `img/` and
1.7 GB of `old_lib/`, this is cheap insurance.

### 5.6 SSH

Add to `~/.ssh/config` on both machines:

```sshconfig
Host github.com
  ControlMaster auto
  ControlPath ~/.ssh/cm-%r@%h:%p
  ControlPersist 10m
  AddKeysToAgent yes
  IdentitiesOnly yes
  IdentityFile ~/.ssh/id_ed25519
```

`ControlMaster` is the measured 2× win on poll cost (§1.3). On macOS add
`UseKeychain yes` and run `ssh-add --apple-load-keychain`, so a `launchd`-started daemon
with no TTY can authenticate.

`pass_git_sync` shows what happens without this: it carries a whole
`ensure_usable_ssh_agent` routine that probes `/tmp/ssh-*` sockets, and its own docs
admit "after a reboot, no agent may hold the unlocked GitHub key until you log in and
use SSH once". **Do not inherit that failure mode for the vault.** Use a passphraseless
`ed25519` deploy key scoped to `bobs-org/bob` with write access, or the macOS keychain
path above. A sync daemon that silently stops working after every reboot until you
happen to SSH somewhere is the opposite of frictionless.

---

## 6. Repo Hygiene (do before flipping the switch)

### 6.1 Garbage-collect

`git count-objects -vH` reports **7,566 loose objects / 565.30 MiB** alongside 12,041
in-pack / 689.59 MiB. Run `git gc` (or `git maintenance start` for ongoing incremental
repacks). Expect a substantial shrink, and do it before any fresh clone on the Mac.

### 6.2 The `old_lib` problem

| Fact | Implication |
| --- | --- |
| `old_lib/` is 1.7 GB of the 1.8 GB working tree | It dominates clone time and disk on any second machine |
| `.git` is already 1.3 GB | GitHub recommends keeping repos **under 1 GB** for good performance and reaches out above **5 GB** |
| `old_lib/docs/nvim_help_lua_intro.pdf` and `old_lib/docs/vim_help_netrw.pdf` are `.gitignore`d for exceeding **100 MiB** | GitHub's hard per-file limit; warnings start at 50 MiB |

Add a staged-object preflight to `bob vault-sync`: warn on any new object above 50 MiB
and refuse one at or above 95 MiB, leaving margin below GitHub's 100 MiB hard limit.
The error must name the path and leave the local commit untouched so the user can move,
ignore, compress, or intentionally route the file through LFS. This catches the problem
before a long upload and rejected push.

Since GitHub becomes the *only* channel, **those two PDFs become permanently
athena-only**. They are not in the repo and cannot be pushed without Git LFS. Today that
is invisible because `old_lib` is excluded from Obsidian Sync too, but it means "the
GitHub repo is a complete copy of my vault" will be false. Three ways out, in order of
preference:

1. **Move `old_lib/` out of the vault entirely** into a separate archive repo or plain
   backup. It is an archival library, not live notes; it does not need to live inside a
   vault that syncs every 15 seconds.
2. **Git LFS for `old_lib/`.** Solves the 100 MiB limit; adds an LFS dependency on both
   machines and consumes GitHub LFS quota.
3. **Accept it** and document that two PDFs are athena-only. Cheapest, and honest.

### 6.3 Sparse-checkout on the MacBook

Do not clone 1.7 GB of PDFs onto a laptop. Cone-mode sparse-checkout excluding
`old_lib/` reproduces exactly today's Obsidian Sync exclusion:

```bash
git clone --filter=blob:none git@github.com:bobs-org/bob.git ~/bob
cd ~/bob
git sparse-checkout set --cone --skip-checks '/*' '!old_lib'
```

`git add -A` respects sparse-checkout and will **not** stage deletions for paths outside
the cone, so the Mac's daemon cannot accidentally wipe `old_lib` from the remote.
**Verify this behaviour explicitly with a throwaway clone before trusting it** — it is
the one place where a mistake is destructive rather than merely annoying.

`--filter=blob:none` (partial clone) additionally skips downloading historical blobs
until needed, which materially shrinks the initial clone given the pack size.

---

## 7. Migration Plan

### 7.1 Fix the plugin gap first *(this is the one real regression)*

`git status --ignored` on the vault shows these present-but-untracked paths:

```text
.obsidian/plugins/block-id-prompt/
.obsidian/plugins/bob-ledger-tools/
.obsidian/plugins/bob-navigation-hotkeys/
.obsidian/plugins/bob-project-tasks/
.obsidian/plugins/bob-vim-surround/
.obsidian/plugins/task-status-cycler/
.obsidian/plugins/obsidian-tasks-plugin/data.json.20260529092052.bak
.obsidian/workspace.json
.sase/
gkeep_gdocs_inbox_dump.txt
needs_attn_notes.txt
old_lib/docs/nvim_help_lua_intro.pdf
old_lib/docs/vim_help_netrw.pdf
sdd/beads/{beads.db,config.json,issues.jsonl}
```

The six plugin directories are deliberately excluded — the `.gitignore` says they "are
sourced from `~/projects/github/bbugyi200/bob-plugins` and should not be tracked here."
But Obsidian Sync's `community-plugin` config type **is** carrying them to the MacBook
today. Kill Obsidian Sync and that stops.

Pick one before migrating:

- **(a)** Install `bob-plugins` on the MacBook and run `bob plugins sync` there after
  each plugin change. Preserves the "monorepo is the source of truth" rule. Adds a
  manual step, which is the thing you said you want to avoid.
- **(b)** Track the built plugin artifacts (`main.js`, `manifest.json`, `styles.css`) in
  the vault repo, and let `bob plugins sync` on athena be the thing that updates them.
  Deployment becomes a vault commit that flows to the Mac automatically. **Recommended
  — it is the only option that is actually frictionless**, and the "don't edit them in
  `~/bob`" rule survives untouched because you still never *edit* them there.

The other ignored entries need no action: `.txt` dumps, `.sase/`, and `sdd/beads/*` are
not in Obsidian Sync's file-type list either, so they are already athena-local.

### 7.2 Sequence

| # | Step | Notes |
| --- | --- | --- |
| 1 | Resolve §7.1 and §6.2 decisions | These change what is in the repo |
| 2 | `git gc`; add `.gitattributes` (§5.5); commit | |
| 3 | Implement `bob vault-sync`; `cargo install` on both machines | Refactors `sync::commit_and_push_vault` |
| 4 | **Change `bob nightly` to drop the `ob sync` gate** | `src/native/nightly.rs`; also make `bulk-git-commit` fetch-and-merge, or delegate to `vault-sync` |
| 5 | Configure SSH (§5.6) on both machines; verify a keyless `git fetch` from a bare `env -i` shell | Catches the `pass_git_sync` agent problem before it bites |
| 6 | MacBook: sparse clone (§6.3), verify `git add -A` does not stage `old_lib` deletions | **Do this on a throwaway clone first** |
| 7 | **Dry-run window:** run `bob vault-sync` on both machines *while Obsidian Sync is still on*, in a mode that commits and pushes but never checks out remote changes | Proves the commit/push half without letting two sync engines fight |
| 8 | **Cutover:** `systemctl --user stop ob-sync-bob.service` (and `disable`); turn off Sync in the Mac GUI; enable `bob-vault-sync` on both | **Exactly one sync engine may run.** With both live, a delete propagated by one is resurrected by the other, forever |
| 9 | Soak for 2 weeks. Deliberately create a conflict on day 1 and confirm you get a conflict copy, not markers | |
| 10 | Only then `ob sync-unlink --path ~/bob`, `ob logout`, remove `ob-sync-bob-poll`, cancel the Obsidian Sync subscription | Keep the remote vault as a rollback for the whole soak |

Keep `ob-sync-bob.service` and `ob-sync-bob-poll` on disk (disabled) through step 10.

### 7.3 Rollback

Through step 9, rollback is: stop `bob-vault-sync` on both machines, `systemctl --user
start ob-sync-bob.service`, re-enable Sync in the Mac GUI. The Obsidian Sync remote
vault still holds a converged copy, and `old_lib` was never in its scope, so nothing is
at risk.

---

## 8. Conflict Reality Check for *This* Vault

Which files will actually collide, given both machines are in use at once?

| File | Risk | Why |
| --- | --- | --- |
| `2026/YYYYMMDD.md` (daily note) | **High** | The Pomodoro ledger. Both machines append and rewrite task lines in the same section. |
| Route notes — `dev.md`, `sase.md`, `bob.md`, `cash.md`, `job.md`… | **Medium** | 13 were modified in the current uncommitted set alone. `bob capture` appends to them from either machine. |
| `mac_inbox.md` | **Low** | Written by Bob Mac Capture, i.e. Mac-only. No second writer. |
| `img/*` | **Low** | New unique filenames (`20260827_070810.png`); creates, not edits. |
| `.obsidian/*.json` | **Low–Medium** | Hotkeys/appearance change rarely, but they are whole-file JSON rewrites — a conflict is total. The conflict-copy policy handles them cleanly. |
| `old_lib/`, `lib/`, `ref/` | **Very low** | Archival; `old_lib` is not on the Mac at all. |

Two structural mitigations worth having:

1. **Append-only sections tend to conflict on the last line.** Two machines appending to
   the end of the same list touch adjacent lines, which git treats as a conflict even
   though the intent is compatible. A trailing sentinel line in append-heavy managed
   sections (the Pomodoros section, Schedule Log, Work Log) gives both sides an
   unchanged anchor line and converts most of these into clean auto-merges. This is a
   genuinely effective trick and it is cheap.
2. **Move athena's cron work away from Mac working hours.** `bob nightly` at 03:30
   already achieves this. Keep it there.

### 8.1 Acceptance tests and operational visibility

Exercise the transaction against two temporary clones and a local bare remote before
letting it touch the live vault. At minimum, verify:

- edits from either device arrive on the other within the latency budget;
- changes to different files and non-overlapping regions of one Markdown file merge;
- a same-hunk conflict produces two intact notes, no marker text, and a notification;
- delete-versus-edit, rename-versus-edit, and binary conflicts preserve both versions;
- a rejected push is fetched, merged, and retried without force;
- offline edits reconcile after reconnecting;
- a 96 MiB staged object is rejected locally with its path reported;
- a no-change cycle creates no commit; and
- service restart and Mac sleep/wake resume polling cleanly.

Record the last successful sync time, local and remote commit IDs, retry count,
duration, files committed, and current conflict/error state. Expose them through
`bob vault-sync status` so "are my notes current?" has an answer without reading system
journals or Git internals.

GitHub as the only sync transport is also a privacy and recovery policy change. A
private repository is access-controlled, but it is not equivalent to Obsidian Sync's
client-held end-to-end encryption. Audit newly tracked plugin settings for credentials
and machine-local paths, keep two-factor authentication and repository membership
tight, and retain independent versioned backups on both machines. Backup copies do not
create a competing live sync channel because they never write changes back into the
working vault.

---

## 9. Open Questions

1. **Is Obsidian on a phone or tablet in scope?** This is the only finding that could
   invalidate the whole plan. Upstream's own documentation calls the mobile git
   implementation "**very unstable**" and recommends a different sync service. No
   `.obsidian/workspace-mobile.json` exists in the vault, which is weak evidence that no
   mobile device is in play — but the `.gitignore` lists it, which suggests someone
   anticipated one. **If a phone is in the picture, git-only sync does not work and the
   answer changes.**
2. **Does the MacBook already have a clone of `bobs-org/bob`?** Not verifiable from
   athena. If it does, reconcile it with §6.3 before cutover rather than after.
3. **§7.1(a) or §7.1(b) for the custom plugins?** The recommendation is (b), but it
   loosens the "plugins are not tracked in the vault repo" rule and that is your call.
4. **§6.2 — move `old_lib` out, LFS it, or accept two athena-only PDFs?** Recommendation
   is to move it out; it does not belong in a repo that syncs every 15 seconds.

---

## 10. Recommendation

**Build `bob vault-sync` and drive it from a watch-plus-poll loop on both machines.
Do not make the Obsidian Git plugin your sync engine.**

Concretely:

1. Add a `bob vault-sync` subcommand implementing §5.1, reusing `bob_sync.lock` and
   refactoring `sync::commit_and_push_vault`. **Merge, never rebase.**
2. Resolve every conflict automatically as a **conflict copy** (§5.3): remote wins in
   place, local is preserved beside it as `<stem>.conflict-<host>-<timestamp>.md`, one
   line logged to a `sync_conflicts.md` inbox note, one desktop notification. **Never
   conflict markers. Never a halted merge. Never `merge=union`.**
3. Trigger it from `inotifywait -t 15` on athena (systemd user unit, replacing
   `ob-sync-bob.service`) and the `fswatch` equivalent under `launchd` on the Mac, with
   a 5-second debounce. Target 5–10 s out, ≤15 s in.
4. Enable SSH `ControlMaster` on both machines — a measured 2× cut in poll cost — and
   fix credential availability properly (keychain on macOS, passphraseless scoped deploy
   key on athena) rather than inheriting `pass_git_sync`'s agent-probing workaround.
5. Fix `bob nightly` to stop calling `ob sync`, and make the cron path fetch-and-merge
   instead of commit-and-push-blind.
6. Before cutover: `git gc`, add `.gitattributes`, decide the `old_lib` question, and
   **solve the custom-plugin gap** — track built plugin artifacts in the vault repo so
   plugin updates keep flowing to the Mac without a manual step.
7. Install the Git plugin on both machines with **all automation off**, purely for its
   Source Control, History, and Line Authoring views.
8. Run one sync engine at a time. Soak two weeks with Obsidian Sync merely stopped, not
   unlinked, then cancel.

**Why this and not the plugin:** the plugin syncs only while Obsidian is open, and
athena is a server whose vault is edited by cron and by agents; the plugin's finest
interval is minutes where you need seconds; the plugin would race the existing
`bulk-git-commit`; and — decisively — the plugin has no unattended conflict policy, so
its failure mode is markers in a note you are typing into and a stalled sync channel.
Everything expensive about this project is that one design decision, and owning the
reconcile loop is what lets you get it right.

**Why this is affordable:** the measurements say so. `git status` on this vault is 10 ms
and the notes are under 25 MB. The only real cost is a 220 ms multiplexed SSH round trip
every 15 seconds, which is roughly 1.5 % of one core on an always-on server and
negligible on a laptop. The resource objection to git-based vault sync is, for this
vault, simply not true.

---

## Sources

- [Git - Obsidian Plugin (community listing)](https://community.obsidian.md/plugins/obsidian-git)
- [Obsidian Git docs — Start here](https://publish.obsidian.md/git-doc/Start+here)
- [Obsidian Git docs — Installation](https://publish.obsidian.md/git-doc/Installation)
- [Obsidian Git docs — Getting Started](https://publish.obsidian.md/git-doc/Getting+Started)
- [Obsidian Git docs — Features](https://publish.obsidian.md/git-doc/Features)
- [Vinzent03/obsidian-git](https://github.com/Vinzent03/obsidian-git)
- [Auto-merge option to prioritize remote changes · Vinzent03/obsidian-git#872](https://github.com/Vinzent03/obsidian-git/issues/872)
- [Synchronization and Conflict Resolution — obsidianmd/obsidian-help (DeepWiki)](https://deepwiki.com/obsidianmd/obsidian-help/2.3-synchronization-and-conflict-resolution)
- [Troubleshoot Obsidian Sync](https://retypeapp.github.io/obsidian/sync/troubleshoot/)
- [GitHub Docs — Repository limits](https://docs.github.com/en/repositories/creating-and-managing-repositories/repository-limits)
- [GitHub Docs — About repositories and private-repository access](https://docs.github.com/en/repositories/creating-and-managing-repositories/about-repositories)
- [Git — `git pull` integration strategies](https://git-scm.com/docs/git-pull)
- [simonthum/git-sync](https://github.com/simonthum/git-sync)
- [Vault File Refresh — Obsidian plugin (on chokidar watcher gaps)](https://community.obsidian.md/plugins/vault-file-refresh)
- [Simple guide to setting up git sync in Obsidian — Andrew Morris](https://ahmorris.org/posts/obsidian-git/)
- [obsidian-git Setup Guide — Auto-Sync Configuration and Troubleshooting](https://ob-lite.app/guide/en/obsidian-git)
- [Automated Obsidian vault sync with git and inotify-tools (gist)](https://gist.github.com/dbalmain/8f178cd8c2aa935f0b215aad8771bb71)
- [SSH keys in macOS keychain — jirsbek](https://github.com/jirsbek/SSH-keys-in-macOS-Sierra-keychain)
- Local evidence: `~/bob` git metrics, `ob sync-status --path ~/bob`,
  `snap info obsidian`, `~/.config/systemd/user/ob-sync-bob.service`,
  `~/.local/bin/ob-sync-bob-poll`, `crontab -l`, `~/bin/pass_git_sync`,
  `bob-cli` `src/native/{sync,nightly,ob}.rs`, `~/bob/.gitignore`,
  `docs/obsidian-sync-exclusions.md`
