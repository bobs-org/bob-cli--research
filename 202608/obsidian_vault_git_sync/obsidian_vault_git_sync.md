# Making GitHub the Only Sync Channel for the Bob Obsidian Vault

- **Date:** 2026-08-27
- **Vault:** `~/bob` on athena → `git@github.com:bobs-org/bob.git`, branch `master`
- **Devices:** athena (Debian 13, always-on headless server) and a MacBook, **frequently
  used at the same time**
- **Question:** what is the best way to drop Obsidian Sync and make the vault's GitHub
  repo the primary and only sync channel, with minimal friction and minimal resource use?

**Recommendation in one line:** build a `bob vault-sync` subcommand that owns the whole
reconcile cycle, run it on **both** machines from a watch-plus-poll loop (systemd on
athena, `launchd` on the Mac), resolve every conflict automatically as a **quarantined
conflict copy** rather than conflict markers, and keep the Obsidian Git plugin installed
with all automation **off** purely as a read-only viewer.

This report consolidates two independent research reports (`__a` = `research.1a.cdx`,
`__b` = `research.1a.cld`) plus fresh verification. Where they disagreed, the resolution
is stated with the evidence that settled it.

---

## 0. Executive summary

| | Finding |
| --- | --- |
| **This migration is no longer optional** | **Obsidian Sync has been failing continuously since 07:57:12 today** with `Vault limit exceeded` — 454+ consecutive failures. The two machines are diverging *right now*. Neither source report caught this. §1.1 |
| **The resource objection is empirically false** | Measured on the real vault: `git status` = **10 ms** warm, `git add -A --dry-run` = 20 ms, remote poll = 490 ms → **220 ms** with SSH `ControlMaster`. A 15 s loop is ~1.5 % of one core. §1.4 |
| **The real cost is latency, not CPU** | Obsidian Sync is push-based and sub-second; git must be polled. A tuned loop gives ~5–10 s out, ≤15 s in — 10–20× slower, and still fine for one person with two keyboards. |
| **The real risk is conflict *handling*, not conflict *frequency*** | Git's default — write `<<<<<<<` into the note and halt — is unacceptable for an unattended daemon editing files Obsidian has open and `bob` parses at 03:30. This one decision is the whole project. §4 |
| **The Obsidian Git plugin is the wrong engine** | It runs only while Obsidian is open (athena is a server edited by cron and agents), its finest interval is minutes, it would race `bob bulk-git-commit`, and it has no unattended conflict policy. §3 |
| **`bob bulk-git-commit` never fetches** | `src/native/sync.rs` is `add -A` → `commit` → `push`, verified. Safe *only* because Obsidian Sync converges the tree first. Removing Sync makes this a correctness bug that must ship **with** the cutover. §1.3 |
| **Report B's sparse-checkout recipe is broken** | Tested: `--cone` with `!old_lib` negation checks out **only top-level files**, silently dropping every note directory. The correct form is `--no-cone`. §6.3 |
| **Report B's "sentinel line" mitigation does not work** | Tested and disproved — both sides insert at the same anchor and still conflict. §8.2 |
| **Conflict copies would poison your dashboards** | `dash.md` runs **unscoped vault-wide** Tasks queries and Dataview has **no** exclusions configured. Naïve conflict copies inject phantom duplicate tasks. Fix in §5.4. Neither source report caught this. |
| **One silent regression** | Obsidian Sync carries your six custom `bob-*` plugins to the Mac via its `community-plugin` config type. Git cannot — they are explicitly `.gitignore`d. §7.1 |

---

## 1. What exists today (all verified on athena, 2026-08-27)

### 1.1 The transport being replaced is already broken

This is the most important new finding, and it reframes both source reports' migration
plans.

```text
Aug 27 07:56:40  ob-sync-bob-poll: Fully synced          ← last success
Aug 27 07:56     xlib/chat/AGENTS.pdf created (101 KB)
Aug 27 07:57:12  ob-sync-bob-poll: Sync error: Error: Vault limit exceeded.
…
Aug 27 10:10:48  ob-sync-bob-poll: Uploading file xlib/chat/AGENTS.pdf
                 Sync error: Error: Vault limit exceeded.
                 ob sync exited with status 1; sleeping 30s before retry
```

`journalctl` counts **454 consecutive `Vault limit exceeded` failures** in the last seven
days, all of them today, beginning 07:57:12 EDT. The service is still `active (running)`
and retrying every 30 s, so it *looks* healthy from `systemctl` — but no bytes have moved
in either direction for over two hours.

**Likely cause** (inference from correlated evidence, not directly measurable — `ob` does
not report remote usage): Obsidian's Standard plan is capped at **under 1 GB of total
storage**, and remote version history counts toward it
([Plans and storage limits](https://help.obsidian.md/Obsidian+Sync/Plans+and+storage+limits)).
`docs/obsidian-sync-exclusions.md` in this repo records the load-bearing rule —
*"Obsidian Sync exclusions are not remote delete commands"* — so the recent `old_lib`
exclusion stopped **future** sync consideration without removing the already-uploaded
copies from the remote vault. The remote is therefore still carrying archival weight it
will never shed on its own, and the 101 KB `AGENTS.pdf` at 07:56 was simply the straw.

**Three consequences for the plan:**

1. **Both source reports' runbooks open with "wait until both machines say fully
   synced."** That is currently impossible. The migration must instead begin with an
   explicit, manual reconciliation of whatever diverged since 07:57 today.
2. The usual "keep Obsidian Sync as a rollback during the soak" advice is much weaker
   than it reads — the rollback target is itself broken until the quota is resolved.
3. Urgency is real but bounded: git is the *only* thing currently protecting the vault,
   and git on athena is healthy (§1.5). The Mac is the exposed side.

### 1.2 Current sync configuration

```text
Vault:             bob (8a259ad922718b6d8400c1f0e3ba8abe)
Sync mode:         bidirectional          Conflict strategy: merge
Device name:       athena-headless        File types: image, audio, pdf, video
Configs:           community-plugin, community-plugin-data, hotkey,
                   appearance, appearance-data
Excluded folders:  old_lib
```

Two facts matter later: **`old_lib` is already excluded**, so keeping it off the Mac
under git is the status quo, not a regression; and **`community-plugin` is a synced
config type**, which is how the custom `bob-*` plugins reach the Mac today (§7.1).

`ob-sync-bob.service` runs `~/.local/bin/ob-sync-bob-poll` — a bash loop calling
`ob sync` every 30 s. Live cost: **16.9 MB resident (112.5 MB peak), 3 m 54 s CPU over
1 h 38 m ≈ 4 % of one core.** Any replacement should beat this, and the recommended
design does.

### 1.3 The git path that already exists

Git is currently a *backup*, not a sync. `bob bulk-git-commit` (`src/native/sync.rs`,
`commit_and_push_vault`) does exactly three things, verified by reading the source:

```
git add -A .   →   git commit (if staged changes)   →   git push
```

It **never fetches, pulls, merges, or retries a rejected push**, and it holds an
exclusive `flock` on `${XDG_RUNTIME_DIR:-/tmp}/bob_sync.lock`. `bob nightly` takes that
same lock, runs `ob sync` as a "shared gate", then `move-done-tasks` and
`bulk-git-commit`, driven by cron at 03:30.

**Consequence:** commit-without-pull is safe *only* because Obsidian Sync guarantees the
tree has already converged. Remove Sync and the 03:30 cron commit diverges from whatever
the Mac pushed, and nothing merges it. This is not cleanup to schedule later; it is a
correctness fix that must ship with the switch.

There is no existing `vault-sync` command — `grep -rn "vault.sync" src/` returns nothing.

### 1.4 Measured cost of a git-based cycle

Against the live `~/bob` (git 2.47.3, 6,407 tracked files, 6,434 files on disk):

| Operation | Time | Notes |
| --- | --- | --- |
| `git status --porcelain` (cold / warm) | 0.05 s / **0.01 s** | No `fsmonitor`, no `untrackedCache` configured |
| `git add -A --dry-run` | **0.02 s** | |
| `git ls-remote origin master` | 0.49 s | Dominated by the SSH handshake |
| `git ls-remote` with `ControlMaster` | **0.22 s** | Warm multiplexed connection |

**Conflict resolved (A vs B):** report A recommends `core.untrackedCache` and
`core.fsmonitor`; report B calls them "pure ceremony." **B is right.** The local half of
the cycle is already 10 ms — there is nothing to optimise. The entire cost is the network
round trip, and SSH connection multiplexing halves it for one stanza of `~/.ssh/config`.
Skip the git performance knobs; ship `ControlMaster`.

### 1.5 Vault shape (reconciling the two reports' numbers)

Both reports measured correctly but reported different things. Verified totals:

| Path | Size | Files |
| --- | --- | --- |
| Working tree excl. `.git` | **1741.1 MiB** | 6,434 |
| `old_lib/` | **1650.9 MiB** | 700 |
| `img/` | 62.2 MiB | 187 |
| `.obsidian/` | 10.1 MiB | 68 |
| `lib` + `ref` + `_generated` + `2026` (the actual notes) | **~10.3 MiB** | 2,073 |
| `.git` | 565.30 MiB loose (**7,566 un-GC'd objects**) + 689.59 MiB in-pack | |

`old_lib/` is **95 % of the working tree**. The notes themselves are ~10 MiB and change
slowly (6–18 files, 150–290 insertions per commit). **This vault is an ideal git-sync
candidate once `old_lib` is handled.**

On large files, both reports were right about different objects:

- Largest **tracked** file: `old_lib/books/adtech_book.pdf` at **86.5 MiB** — under
  GitHub's 100 MiB hard limit but above its 50 MiB warning (report A's finding, and the
  motivation for a preflight guard).
- Two files **already `.gitignore`d** for exceeding the limit (`.gitignore:84-85`):
  `vim_help_netrw.pdf` **138.7 MiB** and `nvim_help_lua_intro.pdf` **136.6 MiB** (report
  B's finding). Under git-only sync these become permanently athena-only. §6.2.

### 1.6 Current git state — and one landmine

`~/bob` is on `master`, **exactly level with `origin/master` (0 ahead, 0 behind)**, with
16 dirty paths. The git side is healthy, which makes cutover much easier than §1.1
implies.

But three paths are **untracked and *not* ignored**:

```text
?? 2026/20260827.md      ?? img/20260827_070810.png      ?? xlib/
```

`xlib/` is new (its only file, `AGENTS.pdf`, was created at 07:56 today — the file that
broke Obsidian Sync). `git check-ignore` confirms the `!*.pdf` negation **un-ignores**
it. **The first `git add -A .` a sync daemon runs will sweep `xlib/` into the repo
permanently.** Decide before cutover whether `xlib/` belongs in the vault repo or in
`.gitignore`. Neither source report caught this.

### 1.7 Platform notes

- athena runs **snap `obsidian` 1.13.7 under `classic` confinement**. The Obsidian Git
  docs warn that Snap sandboxes Obsidian away from git — **that reasoning does not apply
  here**, because classic confinement has full system access. It remains
  upstream-unsupported, but the objection is void. (Moot under this recommendation,
  which does not depend on the plugin.)
- `fs.inotify.max_user_watches` = **505,837**, far above the ~6.4 k needed. A watcher is
  safe.
- `bob-cli` is **already cross-platform**: `Cargo.toml` declares macOS-specific
  dependencies, `src/native/capture_clip.rs` branches on `target_os`, and Bob Mac Capture
  already shells out to `bob`. **A new `bob` subcommand is automatically available on
  both machines** — this is what makes the "build it" option cheap.

---

## 2. What you are actually giving up

| Property | Obsidian Sync | Git | Verdict |
| --- | --- | --- | --- |
| **Transport** | Push (websocket), sub-second | Pull (polled) | **Real loss**, mitigated to 5–15 s in §5 |
| **Markdown merge** | `diff-match-patch`, character granularity — auto-merges same-line edits | Line-based three-way | **Small loss.** Fine for prose and list-structured notes |
| **Non-markdown merge** | "Last modified wins" | Conflict | **No loss** — §5.3 reproduces the same behaviour |
| **Failure mode** | Silent auto-merge, or an explicit conflict file if configured | **Markers written into the file, operation halted** | **The dangerous one.** §5 replaces it |
| **Mobile** | First-class | Upstream calls the mobile git implementation "very unstable" | **Blocking if a phone is in scope** — §9 |
| **Storage quota** | **Currently exceeded and hard-failing** (§1.1) | GitHub: 1 GB soft / 5 GB outreach | **Net gain** |
| **History** | Per-file version-history UI | `git log` / `git blame` over the whole vault | **Net gain** |
| **Encryption** | End-to-end encrypted | Private repo = access control, **not** E2EE | **Real privacy regression.** Treat GitHub as trusted with plaintext |

Honest framing: git's *merge quality* is close enough, its *latency* is 10–20× worse but
still sub-half-minute, and its *failure behaviour* is unacceptable out of the box and must
be engineered around. Upstream is explicit — *"Git is not meant to share your changes live
to the cloud or another person. Meaning it should not be used to work with someone live on
the same note"* ([Obsidian Git docs](https://publish.obsidian.md/git-doc/Start+here),
verified). Frequent syncing narrows the conflict window; it does not make simultaneous
editing of the same paragraph safe.

---

## 3. Which engine? (the reports' main disagreement)

**Report A** recommends the Obsidian Git plugin on the Mac + a `bob vault-sync` systemd
job on athena. **Report B** recommends `bob vault-sync` on both, with the plugin as a
read-only viewer. **B is correct**, and A's underlying concern is satisfied anyway.

Both agree the plugin cannot serve athena. The disagreement is only about the Mac, where
A's argument is in-app visibility and less code to own. That does not survive contact with
four facts:

1. **It only runs while Obsidian is open.** Even on the Mac, closing the laptop lid stops
   sync — including receiving. Report A's design leaves the Mac unable to *pull* athena's
   03:30 maintenance commits until you next open the app.
2. **Interval granularity is minutes, not seconds.** Community guidance converges on
   10–15 minute intervals; A's own recommendation is 1 minute, which is the plugin's floor
   and 4× worse than the measured achievable latency.
3. **No unattended conflict policy.** On conflict it leaves markers in the note and waits
   for you — in a file you may be typing into. This is the failure mode §4 exists to
   eliminate, and it is unfixable from settings.
4. **Two engines, two conflict policies.** A's design has the Mac using the plugin's
   rebase-then-merge-fallback and athena using Bob's merge-only transaction. Divergent
   policies on the two sides of one repo is exactly the class of bug that is hardest to
   reproduce.

**A's real requirement — "the Mac needs a visible failure surface" — is legitimate and is
satisfied without making the plugin the engine.** Install it on both machines with *every*
automation setting disabled and use its Source Control, History, and Line Authoring
(`git blame` in the gutter) views to see what the daemon did. You get A's visibility and
B's correctness.

**Cost of building it:** ~300–400 lines of Rust plus two unit files. Steps 2–3 of the
cycle are literally `sync::commit_and_push_vault` minus the push, so much of it is
refactoring. Prior art to borrow from but not depend on: `simonthum/git-sync` and
`gitwatch` validate the loop shape; neither offers conflict-copy resolution or integrates
with `bob_sync.lock`. You already run this pattern for `pass` (`pass_git_sync` on hourly
cron), whose own help text concedes "merge conflicts in the password store still require
manual resolution" — precisely the gap the vault version must close.

**Rejected outright:** Syncthing (genuinely better at concurrent editing, but it is a
second sync channel — the thing you asked to eliminate); Obsidian LiveSync (not git, plus
a CouchDB server to run and back up); keeping Obsidian Sync (rejected by the premise, and
currently broken anyway); network-mounting the vault (Obsidian's file watchers are
unreliable on network/FUSE mounts, and it fails off-LAN).

---

## 4. The failure mode that must be designed away

It is 09:15. You are typing into `2026/20260827.md` on the MacBook. Ninety seconds ago you
added a Pomodoro to the same section on athena and it has been pushed. The Mac daemon
fetches, merges, and hits a conflict on adjacent lines. Default git writes this into the
file you are typing in:

```markdown
<<<<<<< HEAD
- [ ] 🍅 Review the capture grammar ^p3
=======
- [ ] 🍅 Draft the sync design doc ^p3
>>>>>>> origin/master
```

Obsidian reconciles external on-disk changes into open notes through its normal update
pipeline, so **those markers appear live in your editor**, in a file whose task syntax
`bob` and the Tasks plugin both parse. The repo is left mid-merge and every subsequent
cycle fails until you intervene. Add `bob move-done-tasks` rewriting task lines at 03:30
and `bob capture` appending to route notes, and a halted merge is not a nuisance — it is a
stalled sync channel plus a corrupted ledger.

**This is not hypothetical.** Verified in a scratch repo: two machines each appending one
task to the end of the same list produces exactly the markers above (§8.1).

**Conclusion: an unattended vault sync must never leave conflict markers and must never
halt.**

---

## 5. Recommended design — `bob vault-sync`

### 5.1 One reconcile cycle

Idempotent, lock-protected, safe to invoke at any time from any trigger.

```
0.  if a merge/rebase/cherry-pick is already in progress: abort it, log loudly, continue
1.  flock ${XDG_RUNTIME_DIR:-/tmp}/bob_sync.lock   (non-blocking; exit 0 if held)
2.  preflight: reject any newly-staged object ≥ 95 MiB (§6.2)
3.  git add -A .
4.  if staged changes: git commit -m "vault sync <host> <ISO-8601>"
5.  git fetch --no-tags origin master             (GIT_SSH_COMMAND with ControlMaster)
6.  if HEAD == origin/master: goto 10
7.  if HEAD is an ancestor of origin/master: git merge --ff-only origin/master; goto 10
8.  git merge --no-edit origin/master
9.  on conflict: resolve every conflicted path per §5.3, git add, git commit
10. git push
11. if push rejected (non-fast-forward): goto 5, bounded to 3 retries
12. record last-success timestamp, local/remote SHAs, retry count, conflict state
```

**Step 0 is mine, and both reports missed it.** Report A's design *refuses to proceed*
when it finds a merge in progress; report B's design assumes it can never happen because
it auto-resolves. Neither is right: a `SIGKILL`, an OOM, or a laptop lid closing mid-merge
leaves the worktree mid-merge, and A's "refuse and wait for a human" means sync is dead
until you notice. Recover automatically — abort, log, continue — because §5.3 guarantees
the next pass can resolve without help.

**Merge, never rebase.** A failed rebase leaves a partially-replayed, detached-HEAD
worktree with an arbitrary number of remaining conflicts — the worst possible thing to
hand to a running Obsidian. A merge has exactly one conflict point, one resolution pass,
one commit. History noise is irrelevant for a notes vault. Both reports agree here; note
the plugin's own pull tries rebase first, which is a further reason not to use it.

**Never** use `reset --hard`, `push --force`, `-X ours/theirs`, or `merge=union` (§5.5).

**Reuse the lock, don't invent one.** `ob::acquire_lock()` already returns `Err(0)` when
another run holds it.

### 5.2 Triggers

**athena (Linux)** — replace `ob-sync-bob.service` with `bob-vault-sync.service`,
`Type=simple`, running one loop:

```bash
while true; do
  inotifywait -q -r -t 15 -e modify,create,delete,move \
    --exclude '(/\.git/|/\.obsidian/workspace|/\.trash/|/\.sase/|/old_lib/)' \
    "$BOB_DIR" >/dev/null
  sleep 5                 # debounce: Obsidian writes ~2 s after you stop typing
  bob vault-sync
done
```

`inotifywait -t 15` returns on **either** a file event or the timeout, so one process and
one blocking wait gives you both edge-triggered local pushes and a 15-second remote poll.
Idle cost per cycle: one `git status` (10 ms) + one multiplexed `ls-remote` (220 ms) per
15 s ≈ **1.5 % of one core** — better than the 4 % `ob-sync-bob.service` burns today.

**MacBook (macOS)** — a `launchd` LaunchAgent with `KeepAlive`, same loop with `fswatch`
instead of `inotifywait`. Prefer this over `launchd`'s built-in `WatchPaths`, which is
unreliable for deep recursive trees and offers no debounce control. Gate on AC power or
network reachability to be kind to the battery.

**Latency budget:** local edit → remote ≈ **5–10 s**; remote edit → local **≤ 15 s + fetch**.

**Conflict resolved (A vs B):** A proposes 60 s polling with no watcher, arguing a systemd
*timer* leaves no resident process. B proposes 15 s watch-plus-poll. **B wins on
measurement** — the resident process is a blocked `inotifywait` holding ~1 MB, versus
athena's current 16.9 MB service, and 60 s quadruples the divergence window for no
resource saving. A's separate point stands and is folded in: also fire `vault-sync`
asynchronously after Bob commands that mutate the vault, so local captures publish
immediately.

**Also fix `bob nightly`:** drop the `ob sync` gate and make the sequence
`vault-sync → move-done-tasks → vault-sync`.

### 5.3 Conflict policy — the conflict copy

On conflict, for each conflicted path:

| Path type | Action |
| --- | --- |
| Text (`.md`, `.canvas`, `.base`) | Check out **`--theirs`** (remote) into place; write the **local** version to the quarantine path (§5.4). `git add` both. |
| Binary (images, PDFs, audio, video) | Same shape, whole-file. Matches Obsidian Sync's "last modified wins" for non-markdown. |
| Delete/modify | **Keep the file.** Never let an unattended daemon win a delete race. Log it. |

Then commit, push, log one line to a `sync_conflicts.md` inbox note, and fire `bob notify`.

**Verified:** `git checkout --theirs` works for the both-added (`AA`) case — the most
common daily-note scenario, where each machine independently creates
`2026/20260828.md`. Confirmed in a scratch repo: `git ls-files -u` shows stages 2 and 3
with no stage 1 (no common ancestor), and `--theirs` correctly extracts stage 3.

**Why remote-wins-in-place is the right direction:** the remote version is the one the
*other* machine already considers committed; your local version is the one you are sitting
in front of and can most easily re-apply. Nothing is ever lost, the channel never stalls,
no markers appear in a live note. This is exactly Obsidian Sync's own "Create conflict
file" strategy — you are re-implementing a supported behaviour, not inventing a hack.

### 5.4 Quarantine the conflict copies (critical — neither report caught this)

Report B places conflict copies beside the original as
`<stem>.conflict-<host>-<timestamp>.md`. **That will corrupt your dashboards.** Verified:

- `dash.md` runs **unscoped, vault-wide** Tasks queries (`status.type is IN_PROGRESS`,
  `status.name includes Next`, `status.type is TODO`) with no `path` filter.
- Dataview's `data.json` has **no exclusions configured at all** (`{}`).
- `2026/` alone contains **753 task lines**.

A conflict copy of a daily note is a second markdown file containing the same task lines,
so every one of those tasks appears **twice** in `dash.md`, `blocked.md`, and any Pomodoro
rollup — and `bob move-done-tasks` would process both copies at 03:30.

**Fix — write conflict copies to a dedicated `_conflicts/` directory** (preserving the
original relative path inside it), and close all three query surfaces:

1. **Tasks plugin:** set `globalQuery` to `path does not include _conflicts`. Verified
   currently empty (`''`), so it is free to use, and one setting covers every `tasks`
   block with no per-query edits. (Note `globalFilter` is `#task`, and only 56 of the 753
   task lines carry it — so the Tasks plugin sees a minority, but Dataview and `bob` see
   all of them.)
2. **Dataview:** add `_conflicts` to its excluded folders.
3. **`bob`:** skip `_conflicts/` in the vault walkers, alongside the existing `old_lib`
   handling. This is the one that cannot be fixed from plugin settings, and it is the one
   that matters most — `move-done-tasks` mutates what it finds.

Zero-config fallback if you would rather not touch settings: give conflict copies a
**non-`.md` extension** (`…​.conflict-athena-20260827T101500.txt`). Obsidian will not index
them as notes, no query will see them, and `bob`'s `*.md` globs skip them for free — at the
cost of in-app readability.

### 5.5 Do **not** use `merge=union`

The tempting one-line "fix" (`*.md merge=union`) concatenates both sides of every
conflicting hunk with no understanding of content. On this vault that means **silently
duplicated task lines** in the Pomodoro ledger and route notes — duplicated `^blockid`s,
duplicated checkboxes, double-counted Pomodoros. A conflict you can see beats a corruption
you cannot.

### 5.6 `.gitattributes` — currently absent, add it

**Conflict resolved (A vs B):** A says absence is "correct for now"; B says add it.
**B is right.** Once an unattended daemon is performing merges across 62 MiB of `img/` and
1.65 GiB of `old_lib/`, you want it structurally impossible for git to attempt a textual
merge on a PNG.

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

`binary` is shorthand for `-diff -merge -text`. Cheap insurance. (`*.PDF` matters —
commit `ac31423 fix: track uppercase old_lib PDFs` shows the case variant is real here.)

### 5.7 SSH

On both machines, in `~/.ssh/config`:

```sshconfig
Host github.com
  ControlMaster auto
  ControlPath ~/.ssh/cm-%r@%h:%p
  ControlPersist 10m
  AddKeysToAgent yes
  IdentitiesOnly yes
  IdentityFile ~/.ssh/id_ed25519
```

`ControlMaster` is the measured 2× win on poll cost (§1.4). On macOS add `UseKeychain yes`
and run `ssh-add --apple-load-keychain` so a `launchd`-started daemon with no TTY can
authenticate.

`pass_git_sync` shows the failure mode to avoid: it carries an entire
`ensure_usable_ssh_agent` routine probing `/tmp/ssh-*` sockets, and its own docs admit
"after a reboot, no agent may hold the unlocked GitHub key until you log in and use SSH
once." **Do not inherit that.** Use a passphraseless `ed25519` deploy key scoped to
`bobs-org/bob` with write access, or the keychain path above. A daemon that silently stops
after every reboot is the opposite of frictionless.

Polling cost against GitHub is a non-issue: 2 machines × 4 polls/min = 8/min, far under
GitHub's documented guidance of ~15 read operations per second per repository
([repository limits](https://docs.github.com/en/repositories/creating-and-managing-repositories/repository-limits)).

---

## 6. Repo hygiene (do before flipping the switch)

### 6.1 Garbage-collect

`git count-objects -vH` reports **7,566 loose objects / 565.30 MiB** alongside 12,041
in-pack / 689.59 MiB. Run `git gc` (or `git maintenance start` for ongoing incremental
repacks) **before** any fresh clone on the Mac. Expect a substantial shrink — roughly a
third of `.git` is currently un-packed.

### 6.2 The `old_lib` problem

`old_lib/` is 1650.9 MiB of the 1741.1 MiB tree; `.git` is already ~1.2 GiB against
GitHub's 1 GB "keep under" guidance and 5 GB outreach threshold. Two files
(`vim_help_netrw.pdf` 138.7 MiB, `nvim_help_lua_intro.pdf` 136.6 MiB) are `.gitignore`d
for exceeding GitHub's **100 MiB hard limit**, and the largest tracked file
(`adtech_book.pdf`, 86.5 MiB) sits uncomfortably close to it.

Since GitHub becomes the *only* channel, those two PDFs become **permanently athena-only**
— "the GitHub repo is a complete copy of my vault" will be false. Three ways out, in order
of preference:

1. **Move `old_lib/` out of the vault entirely** into a separate archive repo or plain
   backup. It is an archival library, not live notes; it does not belong in a repo that
   syncs every 15 seconds. *(Recommended.)*
2. **Git LFS for `old_lib/`.** Solves the 100 MiB limit but adds an LFS dependency on both
   machines, consumes GitHub LFS quota, and introduces pointer-file failure modes.
   **Do not attempt this during the sync cutover** — it rewrites or bifurcates 1.2 GiB of
   history and solves no synchronization bug. Separate project, if ever.
3. **Accept it** and document that two PDFs are athena-only. Cheapest, and honest.

Regardless of choice, ship the **95 MiB preflight guard** (§5.1 step 2): warn at 50 MiB,
refuse at 95 MiB, leaving margin below GitHub's hard limit so the daemon fails locally with
a clear message rather than on push.

### 6.3 Sparse-checkout on the MacBook — corrected recipe

Do not clone 1.65 GiB of PDFs onto a laptop. **Report B's recipe is wrong and I verified
it in a scratch repo:**

```bash
# ✗ BROKEN — report B §6.3. Cone mode does not support "!" negation.
git sparse-checkout set --cone --skip-checks '/*' '!old_lib'
```

Result: the worktree contained **only top-level files**. Every note directory was silently
missing. `git sparse-checkout list` showed the patterns were recorded (`!old_lib`, `*`) but
cone-mode matching ignores the negation, so `/*` matched only root-level entries.

Two recipes actually work. Tested both:

```bash
# ✓ Option A — non-cone with negation (RECOMMENDED)
git clone --filter=blob:none git@github.com:bobs-org/bob.git ~/bob
cd ~/bob
git sparse-checkout set --no-cone '/*' '!/old_lib/'

# ✓ Option B — cone mode, allowlisting directories to INCLUDE
git sparse-checkout set --cone 2026 lib ref _generated img .obsidian
```

**Option A is the right choice**, and the deciding test is one neither report ran: what
happens when a *new* top-level directory appears on the remote — as `2027/` will next
January?

| Recipe | After remote adds `2027/` |
| --- | --- |
| **Option A** (`--no-cone`) | `2027/n.md` **appeared automatically** ✓ |
| **Option B** (`--cone` allowlist) | `2027/n.md` **silently missing** ✗ |

Cone mode requires you to remember to extend the list every time the vault grows a
top-level folder, and the failure is silent data-invisibility on the Mac. Use `--no-cone`.

**The safety claim checks out.** Report B flagged `git add -A` behaviour under
sparse-checkout as unverified and "the one place where a mistake is destructive." I tested
it end-to-end: out-of-cone paths are marked `S` (skip-worktree) in the index, `git add -A`
stages **nothing** for them, and after the Mac edited a note and pushed, the remote tree
still contained every `old_lib/` file. **The Mac's daemon cannot wipe `old_lib` from the
remote.** Still re-verify on a throwaway clone of the real repo before trusting it with
1.65 GiB.

`--filter=blob:none` (partial clone) additionally skips downloading historical blobs until
needed, which materially shrinks the initial clone given the pack size.

---

## 7. Migration

### 7.1 Fix the custom-plugin gap first (the one real regression)

`git status --ignored` shows six plugin directories present-but-excluded, at
`.gitignore:48-53`, with the comment *"Bryan's custom Obsidian plugins are sourced from
~/projects/github/bbugyi200/bob-plugins and should not be tracked here"*:

```text
.obsidian/plugins/block-id-prompt/        .obsidian/plugins/bob-project-tasks/
.obsidian/plugins/bob-ledger-tools/       .obsidian/plugins/bob-vim-surround/
.obsidian/plugins/bob-navigation-hotkeys/ .obsidian/plugins/task-status-cycler/
```

Obsidian Sync's `community-plugin` config type is carrying these to the MacBook today.
Kill Sync and that stops. Pick one:

- **(a)** Install `bob-plugins` on the MacBook and run `bob plugins sync` there after each
  plugin change. Preserves the monorepo-is-source-of-truth rule; adds a manual step —
  the thing you said you want to avoid.
- **(b) Track the built artifacts** (`main.js`, `manifest.json`, `styles.css`) in the vault
  repo and let `bob plugins sync` on athena be what updates them. Deployment becomes a
  vault commit that flows to the Mac automatically. **Recommended.**

**Report B framed (b) as "loosening" the rule. It is not — it is the existing rule.**
Verified: the vault already tracks **51 files under `.obsidian/`**, including
`main.js`, `manifest.json`, `styles.css`, and `data.json` for *every* third-party plugin
(dataview, metadata-menu, mrj-jump-to-link, …). Exactly **zero** of the six `bob-*`
plugins are tracked. Option (b) makes the custom plugins consistent with every other
plugin in the vault, and the "don't edit them in `~/bob`" rule survives untouched, because
you still never *edit* them there — `bob plugins sync` writes them.

### 7.2 Sequence

Step 0 is new and is forced by §1.1.

| # | Step | Notes |
| --- | --- | --- |
| **0** | **Reconcile the divergence Obsidian Sync has been unable to close since 07:57 today.** Diff the Mac's vault against athena's by hand, decide per file, and get both trees to a known-equal state. | Both source reports assume you can start from "fully synced." **You cannot.** Do this first, with automation stopped. |
| 1 | Resolve the §7.1 (plugins), §6.2 (`old_lib`) and §1.6 (`xlib/`) decisions | These change what is in the repo |
| 2 | `git gc`; add `.gitattributes` (§5.6); commit | |
| 3 | Implement `bob vault-sync` (§5.1); `cargo install` on both machines | Refactors `sync::commit_and_push_vault` |
| 4 | **Change `bob nightly` to drop the `ob sync` gate**; make `bulk-git-commit` fetch-and-merge or delegate to `vault-sync` | `src/native/{nightly,sync}.rs` — correctness fix, not cleanup |
| 5 | Configure SSH (§5.7) on both; verify a keyless `git fetch` from a bare `env -i` shell | Catches the `pass_git_sync` agent problem before it bites |
| 6 | Set up `_conflicts/` quarantine: Tasks `globalQuery`, Dataview exclusion, `bob` walker skip (§5.4) | Must precede the first real conflict |
| 7 | MacBook: sparse clone (§6.3 Option A); verify on a throwaway clone that `git add -A` stages no `old_lib` deletions | |
| 8 | **Dry-run window:** run `bob vault-sync` on both machines in a commit-and-push-only mode that never checks out remote changes | Proves half the cycle without two engines fighting |
| 9 | **Cutover:** `systemctl --user disable --now ob-sync-bob.service`; turn off Sync in the Mac GUI; enable `bob-vault-sync` on both | **Exactly one sync engine may run.** With both live, a delete propagated by one is resurrected by the other, forever |
| 10 | Soak 2 weeks. **On day 1, deliberately create a conflict** and confirm you get a quarantined conflict copy, not markers | |
| 11 | Only then `ob sync-unlink --path ~/bob`, `ob logout`, remove `ob-sync-bob-poll`, cancel the subscription | |

Keep `ob-sync-bob.service` and `ob-sync-bob-poll` on disk (disabled) through step 11.

**Rollback caveat.** Both source reports treat Obsidian Sync as a safe rollback target
during the soak. Given §1.1, **it is not** — the remote vault is over quota and rejecting
writes. Your real rollback is git itself: every state is a commit, and `git reflog` plus
the pre-migration tag will get you back. Take an independent filesystem backup of `~/bob`
on both machines before step 9 and do not rely on the Sync remote.

---

## 8. Conflict reality check for *this* vault

### 8.1 Where collisions will actually happen

| File | Risk | Why |
| --- | --- | --- |
| `2026/YYYYMMDD.md` (daily note) | **High** | The Pomodoro ledger. Both machines append and rewrite task lines in the same section. |
| Route notes — `dev.md`, `sase.md`, `bob.md`, `cash.md`, `job.md` … | **Medium** | 13 were modified in the current uncommitted set alone; `bob capture` appends from either machine |
| `.obsidian/*.json` | **Low–Medium** | Change rarely, but they are whole-file JSON rewrites — a conflict is total. The conflict-copy policy handles them cleanly. |
| `mac_inbox.md` | **Low** | Bob Mac Capture only; no second writer |
| `img/*` | **Low** | Unique filenames (`20260827_070810.png`); creates, not edits |
| `old_lib/`, `lib/`, `ref/` | **Very low** | Archival; `old_lib` not on the Mac at all |

### 8.2 The "sentinel line" mitigation does not work

Report B §8 proposes adding a trailing sentinel line to append-heavy managed sections
(Pomodoros, Schedule Log, Work Log) so both sides have an unchanged anchor, calling it "a
genuinely effective trick and it is cheap."

**Tested and disproved.** With `<!-- end pomodoros -->` after the list and each machine
inserting immediately before it, the merge **still conflicts** with markers in exactly the
same place. The sentinel changes nothing, because both sides insert at the *same* anchor —
git's line-based merge conflicts whenever two sides insert different content at the same
offset, regardless of what follows.

There is no cheap textual trick here. **The conflict-copy policy in §5.3–5.4 is the
mitigation**, which is precisely why it is the load-bearing part of the design. The one
structural mitigation that does work is scheduling: keep athena's cron work at 03:30, away
from Mac working hours.

---

## 9. Open questions

1. **Is Obsidian on a phone or tablet in scope?** The only finding that could invalidate
   the plan. Upstream calls the mobile git implementation "very unstable" and recommends a
   different sync service. **Evidence says no:** `.obsidian/workspace-mobile.json` does not
   exist in the vault. It *is* listed at `.gitignore:60`, which suggests someone once
   anticipated one — but per this repo's own `docs/obsidian-sync-exclusions.md`, desktop
   Obsidian stores state outside the vault, so a `.gitignore` entry is weak evidence
   either way. **Confirm directly. If a phone is in the picture, git-only sync does not
   work.**
2. **What exactly is over quota on the Obsidian Sync remote (§1.1)?** Worth knowing before
   you cancel, in case you want a working rollback during the soak. Likely `old_lib`
   remnants the exclusion never deleted, plus version history.
3. **Does `xlib/` belong in the vault repo (§1.6)?** It is untracked, un-ignored, and will
   be swept in by the first `git add -A`.
4. **§7.1 (a) or (b) for the custom plugins?** Recommendation is (b), and §7.1 argues it is
   consistent with existing policy rather than an exception.
5. **§6.2 — move `old_lib` out, LFS it, or accept two athena-only PDFs?** Recommendation is
   to move it out.
6. **Does the MacBook already have a clone of `bobs-org/bob`?** Not verifiable from athena.
   If so, reconcile it with §6.3 *before* cutover.

---

## 10. Recommended solution

**Build `bob vault-sync` and drive it from a watch-plus-poll loop on both machines. Do not
make the Obsidian Git plugin your sync engine.**

1. **Reconcile the machines by hand first.** Obsidian Sync has been hard-failing since
   07:57 today (§1.1); you are not starting from a converged state, and every plan that
   assumes you are will silently lose whichever side loses the first merge.
2. **Add a `bob vault-sync` subcommand** implementing §5.1, reusing `bob_sync.lock` and
   refactoring `sync::commit_and_push_vault`. **Merge, never rebase.** Auto-recover from
   an interrupted merge rather than halting.
3. **Resolve every conflict as a quarantined conflict copy** (§5.3–5.4): remote wins in
   place, local is preserved under `_conflicts/`, one line to a `sync_conflicts.md` inbox
   note, one `bob notify`. **Never markers. Never a halted merge. Never `merge=union`.**
   Close all three query surfaces — Tasks `globalQuery`, Dataview exclusions, and `bob`'s
   own walkers — or your dashboards will double-count every task in a conflicted note.
4. **Trigger it** from `inotifywait -t 15` under systemd on athena (replacing
   `ob-sync-bob.service`) and `fswatch` under `launchd` on the Mac, with a 5 s debounce,
   plus an async fire after Bob commands that mutate the vault. Target 5–10 s out,
   ≤15 s in — at ~1.5 % of one core, cheaper than the 4 % the current service burns.
5. **Enable SSH `ControlMaster`** on both machines (measured 2× cut in poll cost) and fix
   credential availability properly — keychain on macOS, passphraseless scoped deploy key
   on athena. Skip `core.fsmonitor`/`untrackedCache`; at 10 ms they are ceremony.
6. **Fix `bob nightly`** to stop calling `ob sync`, and make the cron path fetch-and-merge
   instead of commit-and-push-blind. This must ship *with* the cutover, not after.
7. **Before cutover:** `git gc` (7,566 loose objects), add `.gitattributes`, decide the
   `old_lib` and `xlib/` questions, and **solve the custom-plugin gap** by tracking the
   six `bob-*` plugins' built artifacts — which is what the vault already does for every
   third-party plugin.
8. **On the MacBook, sparse-clone with `--no-cone`**, not cone mode
   (`git sparse-checkout set --no-cone '/*' '!/old_lib/'`). Cone mode with negation
   checks out almost nothing, and a cone allowlist silently misses every new top-level
   directory. Verified: `git add -A` in a sparse checkout cannot delete `old_lib` from the
   remote.
9. **Install the Git plugin on both machines with all automation off**, purely for Source
   Control, History, and Line Authoring. This is what gives the Mac the visible failure
   surface that report A correctly insisted on, without the costs of making it the engine.
10. **Run exactly one sync engine at a time.** Soak two weeks with Obsidian Sync merely
    stopped, backed by independent filesystem backups rather than the Sync remote, then
    cancel.

**Why this and not the plugin:** the plugin syncs only while Obsidian is open, and athena
is a server whose vault is edited by cron and by agents; its finest interval is minutes
where you need seconds; it would race the existing `bulk-git-commit`; and — decisively —
it has no unattended conflict policy, so its failure mode is markers in a note you are
typing into and a stalled channel. Everything expensive about this project is that one
design decision, and owning the reconcile loop is what lets you get it right.

**Why this is affordable:** the measurements say so. `git status` on this vault is 10 ms
and the notes are ~10 MiB — it is `old_lib/` at 95 % of the tree that makes the repo look
heavy, and sparse-checkout keeps it off the laptop entirely. The only real recurring cost
is a 220 ms multiplexed SSH round trip every 15 s. The resource objection to git-based
vault sync is, for this vault, simply not true.

**What you are accepting:** ~5–15 s propagation instead of sub-second; a conflict copy
instead of a character-level auto-merge when you edit the same paragraph on two machines
within one cycle; GitHub holding your notes as plaintext under access control rather than
end-to-end encryption; and ~300–400 lines of Rust you own. Against that, you get a
transport that is not currently broken, full history, and one channel instead of two.

---

## 11. Acceptance tests

Use a local bare repo and two test clones for the automated cases; use the real vault only
for final smoke tests.

- Mac-only edit appears on athena within 30 s; athena-only edit appears on the Mac within 30 s.
- Concurrent edits to **different notes** merge and arrive on both machines.
- Concurrent **non-overlapping** edits to one note merge and arrive on both machines.
- Concurrent **same-line** edits produce a quarantined conflict copy — never markers,
  never a halted merge — and the copy does **not** appear in `dash.md`. *(§5.4)*
- Both machines independently create the same daily note (`AA` conflict) → conflict copy.
- A push race is retried without user intervention.
- Offline edits on both devices reconcile after reconnecting.
- Delete-versus-edit keeps the file; rename-versus-edit stops safely.
- A binary changed differently on both devices produces a conflict copy, uncorrupted.
- A 96 MiB new file is rejected **locally** before GitHub rejects the push. *(§5.1 step 2)*
- **Kill the daemon mid-merge; confirm the next cycle auto-recovers.** *(§5.1 step 0)*
- A no-change cycle creates no commit.
- Mac sleep/wake and athena service restart both resume syncing; **reboot both and confirm
  sync resumes with no interactive SSH login.** *(§5.7)*
- The Mac's sparse checkout never stages an `old_lib` deletion, and a new top-level
  directory created on athena appears on the Mac. *(§6.3)*
- `bob nightly` pulls before maintenance and pushes the resulting maintenance commit.

Instrument the first week with: last successful sync timestamp, local/remote SHAs, retry
count, duration, files committed, conflict/error state. A `bob vault-sync status`
subcommand should make "are my notes current?" answerable without reading journals or git
internals — and would have surfaced §1.1 within minutes instead of hours.

---

## 12. Sources

**Obsidian**

- [Sync your notes across devices](https://obsidian.md/help/sync-notes)
- [Plans and storage limits](https://help.obsidian.md/Obsidian+Sync/Plans+and+storage+limits)
- [Sync limitations](https://help.obsidian.md/Obsidian+Sync/Sync+limitations)
- [Sync conflict behavior](https://obsidian.md/help/sync/troubleshoot)
- ["Vault limit exceeded" — Obsidian Forum](https://forum.obsidian.md/t/vault-limit-exceeded/117343)
- [Obsidian Sync now starts at $4/month — Standard plan](https://obsidian.md/blog/standard-plan/)

**Obsidian Git plugin**

- [Start here](https://publish.obsidian.md/git-doc/Start+here) · [Features](https://publish.obsidian.md/git-doc/Features) · [Installation](https://publish.obsidian.md/git-doc/Installation) · [Authentication](https://publish.obsidian.md/git-doc/Authentication) · [Tips and Tricks](https://publish.obsidian.md/git-doc/Tips-and-Tricks)
- [Vinzent03/obsidian-git](https://github.com/Vinzent03/obsidian-git) · [issue #872 — auto-merge prioritising remote](https://github.com/Vinzent03/obsidian-git/issues/872)

**Git and GitHub**

- [`git pull`](https://git-scm.com/docs/git-pull) · [`git sparse-checkout`](https://git-scm.com/docs/git-sparse-checkout) · [`git status` performance](https://git-scm.com/docs/git-status) · [`core.fsmonitor`](https://git-scm.com/docs/git-config)
- [GitHub: repository limits](https://docs.github.com/en/repositories/creating-and-managing-repositories/repository-limits) · [large files](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github) · [repository visibility](https://docs.github.com/en/repositories/creating-and-managing-repositories/about-repositories)

**Prior art**

- [simonthum/git-sync](https://github.com/simonthum/git-sync) · [gitwatch](https://github.com/gitwatch/gitwatch)
- [SSH keys in the macOS keychain](https://github.com/jirsbek/SSH-keys-in-macOS-Sierra-keychain)

**Local evidence (athena, 2026-08-27)**

`journalctl --user -u ob-sync-bob.service`; `systemctl --user status ob-sync-bob.service`;
`ob sync-status`/`sync-list-remote --path ~/bob`; `~/bob` git metrics (`count-objects -vH`,
`ls-files`, `check-ignore`, `rev-list --left-right`, `status --porcelain --ignored`);
`find`-based tree sizing; `~/bob/.gitignore`; tracked `.obsidian/**` inventory;
`.obsidian/plugins/{obsidian-tasks-plugin,dataview}/data.json`; `dash.md` query blocks;
`~/.config/systemd/user/ob-sync-bob.service`; `~/.local/bin/ob-sync-bob-poll`; `crontab -l`;
`~/bin/pass_git_sync`; `bob-cli` `src/native/{sync,nightly,ob}.rs`;
`bob-cli` `docs/obsidian-sync-exclusions.md`; and scratch-repo experiments verifying
sparse-checkout semantics, `git add -A` deletion safety, append-conflict behaviour, the
sentinel-line hypothesis, and `checkout --theirs` on both-added conflicts.
