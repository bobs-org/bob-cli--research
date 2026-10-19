# Why athena keeps hitting vault conflicts: a git background-cleanup race feeding a conflict loop

- **Research date:** 2026-10-19 (about 12:30–12:40 EDT), on athena.
- **Question:** Why do Bob vault conflicts keep happening on athena, and what is the fix?
- **Evidence:** the `~/bob` reflog and history, `_conflicts/`, `journalctl --user` output from
  `bob_vault_sync_watch`, timestamps under `~/bob/.git`, `src/native/vault_sync.rs`, and four
  throwaway-repo tests run with athena's git. I changed nothing in `~/bob`.

---

## Short answer

> **Two bugs chain together. Both incidents (Oct 15 and today) follow the same path.**
>
> 1. **Trigger.** athena's git (2.47.3) runs its routine cleanup (`git gc`) in a **detached
>    background process**. For a moment that process holds `.git/HEAD.lock`. If `bob vault-sync`
>    fast-forwards at that moment, git updates the files but cannot move `HEAD`. The next sync
>    cycle sees the Mac's new edits as *athena's* edits and commits them. That commit then
>    conflicts with the Mac's real commits.
> 2. **Loop.** One conflicting file is the Mac's review journal (`.bob/stats/review/*.jsonl`).
>    bob saves its local copy to `_conflicts/.bob/stats/review/…jsonl`, but `.gitignore` ignores
>    that path. `git add` fails, so the merge is left half-done. The next cycle aborts the merge
>    and tries again. It gets the same result every ~21 s until a person steps in.
>
> **Nothing was lost.** All 60 of today's `sase.md` "local copies" are byte-identical to the
> Mac's own commit `18c22602`.
>
> **Fix now:** `git -C ~/bob config maintenance.autoDetach false` (plus `gc.autoDetach false`)
> on athena. **Fix in bob-cli:** union-merge the journals, never let an ignored conflict copy
> abort a merge, and stop retrying after the same failure repeats.

## What happened

|                                      | Oct 15                                      | Oct 19 (today)                                 |
| ------------------------------------ | ------------------------------------------- | ---------------------------------------------- |
| Fast-forward half-applied            | 05:38:57 (fetch of `172d136b`)              | 12:06:18 (fetch of `18c22602`)                 |
| Background gc wrote a new pack       | 05:39:10                                    | 12:06:24                                       |
| athena commits the Mac's edits       | 05:39:30: journal, `bob.md`, `cash.md`      | 12:06:47: journal, `sase.md`, 3 other notes    |
| Loop length                          | **~10 h 45 min** (to 16:23), ~1,820 cycles  | **21 min** (to 12:27), 60 cycles               |
| How it ended                         | manual `git reset` to `origin/master`       | a manual merge commit at 12:27:18              |

While a loop runs, athena neither pushes nor pulls, because each cycle undoes its own merge.
Each failed cycle also runs `bob notify` and commits one more conflict copy.

The sync journal shows the trigger directly:

```text
12:06:18 error: git merge --ff-only refs/remotes/origin/master failed: Updating 9089b66a..18c22602
         Fast-forward
         fatal: update_ref failed for ref 'HEAD': cannot lock ref 'HEAD':
         Unable to create '/home/bryan/bob/.git/HEAD.lock': File exists.
```

After that, every cycle prints the same lines:

```text
warning: aborting interrupted merge before reconciling
warning: resolved .bob/stats/review/2026-10.kellys-mbp.jsonl with remote version; quarantined local copy at _conflicts/.bob/stats/review/…jsonl
warning: resolved sase.md with remote version; quarantined local copy at _conflicts/sase.athena-….md
error: git failed: The following paths are ignored by one of your .gitignore files:
_conflicts/.bob/stats/review/2026-10.kellys-mbp.athena-….jsonl
```

## Why each step happens

### 1. git's background cleanup races bob's fast-forward

- From git 2.47 on, commands such as `fetch` and `commit` start automatic maintenance
  **detached** (`maintenance.autoDetach`, on by default). The detached `git gc --auto` runs
  `pack-refs` and `reflog expire --all`. Rewriting `HEAD`'s reflog takes `HEAD.lock`.
- bob runs `git fetch` and then `git merge --ff-only` straight after it. If that fetch started a
  gc, the merge can run into it. git updates the working tree and index first, then fails to
  move `HEAD`.
- **Evidence that gc held the lock at 12:06:18:** all three reflog directories (`.git/logs`,
  `logs/refs/heads`, `logs/refs/remotes/origin`) were rewritten at 12:06:18.67–.69. A new pack
  (`pack-3466f6…`) appeared at 12:06:24, then loose objects were pruned and `info/refs` was
  written at 12:06:25. On Oct 15 a gc pack appeared at 05:39:10, 13 s after that day's bad fetch.
- **Sandbox tests with athena's git:**
  - `git commit` returns, and only **after that** do a detached `maintenance run --detach`,
    then `gc --auto --no-detach`, `pack-refs`, and `reflog expire --all` run. With
    `maintenance.autoDetach=false`, `reflog expire` finished *before* `git commit` returned.
  - With `HEAD.lock` present, `git merge --ff-only` updated the file and left `HEAD` behind.
    The update then showed up as a staged local edit, which is exactly the state bob committed
    at 12:06:47. Running the merge again after the lock cleared finished it cleanly.
- `bob_sync.lock` cannot prevent this. The lock holder is git's own background child, started
  by bob's own `git fetch`.
- athena runs git 2.47.3. apollo runs 2.43.0 and the Mac runs Apple Git 2.50.1. Both loops
  happened on athena. I did not test the race on the other two machines.

### 2. The next cycle mistakes the Mac's edits for local edits

A bob cycle commits whatever `git status` shows before it merges. After a half-applied
fast-forward, those "changes" are simply the Mac's newer file versions. bob committed them as
`vault(athena)` (`2132d58c`) while the Mac kept editing the same files. Both sides had now
changed `sase.md` and the journal, so the merge conflicted.

### 3. An ignored conflict copy turns one conflict into an endless loop

- `resolve_conflicts` in `src/native/vault_sync.rs` writes the local copy to
  `_conflicts/<same path>` and then runs `git add` on it.
- The vault `.gitignore` starts with `*`. Its `!/.bob/stats/**/*.jsonl` exception is anchored at
  the vault root, so `_conflicts/.bob/stats/review/*.jsonl` stays ignored. `git check-ignore`
  confirms this (`.gitignore:3:*`).
- `git add` refuses ignored paths, so `resolve_conflicts` errors out and the merge stays in
  progress. The next cycle runs `merge --abort`, commits the leftover `_conflicts/sase…md` copy,
  merges again, and hits the same conflict. Nothing in the cycle breaks the loop.

### Leftovers

- 61 tracked files in `_conflicts/`: 60 copies of `sase.md`, all identical to Mac commit
  `18c22602`, plus `sync_conflicts.md`.
- About 1,884 untracked journal copies under `_conflicts/.bob/stats/review/`, from both loops.
- 60 junk `vault(athena): … _conflicts/…` commits in today's history. Oct 15's ~1,820 were
  discarded by that day's reset and remain only in the reflog.

## Recommendation

**1. Now, on athena (config only, takes effect right away):**

```bash
git -C ~/bob config maintenance.autoDetach false
git -C ~/bob config gc.autoDetach false
```

git's automatic cleanup then finishes before the command that started it returns. It runs
inside bob's sync cycle and lock instead of racing it. The cost: a cycle that triggers gc runs a
few seconds longer (gc took about 7–13 s in these incidents). Setting the same values on apollo and
the Mac is harmless and keeps the three machines consistent.

**2. Clean up, after a quick look:**

```bash
rm ~/bob/_conflicts/sase.athena-2026-10-19T*.md   # all 60 identical to Mac commit 18c22602
rm -r ~/bob/_conflicts/.bob                       # untracked journal copies, never synced
```

The next `bob vault-sync` commits the deletions.

**3. Fix in bob-cli, so a repeat cannot loop whatever triggers it:**

1. **Union-merge the journals.** Add `.bob/stats/**/*.jsonl merge=union` to the vault
   `.gitattributes`. Each journal is append-only and has a single writer host, so a union merge
   is correct. Tested on today's exact case: local `A B` against remote `A B C` merged cleanly
   to `A B C`.
2. **Never let a conflict copy abort the merge.** Either force-add copies (`git add -f`), or
   keep ignored copies local and only log them. Either way the resolved merge always gets
   committed.
3. **Add a circuit breaker.** If a cycle has to abort an interrupted merge against the same
   `origin/master` SHA a second time, stop: set `last_error`, notify once, and write no new
   conflict copies. That turns ~1,820 retries into one alert.
4. **Retry a fast-forward that hit a lock.** On `cannot lock ref`, wait briefly and run
   `git merge --ff-only` again; the test above shows the retry completes it. bob can also pass
   `-c maintenance.autoDetach=false` on its own git calls, so the fix does not depend on
   per-machine config.

Item 1 by itself would have turned each loop into one ordinary `sase.md`/`bob.md` conflict copy.
Item 4, or the config change, removes the trigger.
