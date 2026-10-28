# bob ref scan -w refusals: duplicated project notes in the vault

Date: 2026-10-28

## Question

`bob ref scan -w` on the MacBook refuses 13 PDFs with `multiple_open_ref_tasks`. What
must change for it to stop failing?

## Short answer

bob-cli is not at fault. The vault is in a bad state. At 2026-10-28 09:31 EDT the
MacBook's auto-commit `8ca09ee75` replaced `sase_agent_recovery.md` (the agent-recovery
project note) with a near-copy of `sase.md` (the sase project note). Every open reading
task in `sase.md` now also appears in `sase_agent_recovery.md`. Each of the 13 affected
reference notes therefore has two open claimants, so bob refuses to sync those PDFs.

Fix: restore `sase_agent_recovery.md` to its content just before that commit, repoint
one dangling link, then re-run the scan. I checked this on a scratch copy of the vault,
where it turns the 13 refusals into 0 failures. I did not change the real vault.

## How the error arises

- `src/native/ref_tasks/select.rs:124-125`: when two or more open reading-task lines
  outside `done/` link to the same ref (open means the mark is not `x`, `X`, or `-`),
  selection returns no task and emits `multiple_open_ref_tasks`.
- `src/native/highlights_ref/sync.rs:1057`: that diagnostic sets
  `refuse_status_parent_writes`, and the scan returns `refusing to sync <pdf>`. The
  refusal is per PDF; the other 535 PDFs are unaffected.
- Reproduction: on athena, `bob ref scan --dry-run --no-hooks` (bob 0.4.0 from cargo)
  reports the same 13 refusals with the same `sase.md` and `sase_agent_recovery.md` line
  numbers as the MacBook output. Writes: none. So the vault state matches.

## What is duplicated

- 14 `#ref` reading-task blocks, with their child lines, are byte-identical in
  `sase.md` and `sase_agent_recovery.md`. Thirteen are open and refuse. The fourteenth,
  `footprint_feature_usage_tracking`, is `[x]` in both, so it does not refuse, but it is
  still a duplicate.
- The duplication is wider than those 14 blocks. `sase_agent_recovery.md` (411 lines)
  has zero lines that are absent from `sase.md` (416 lines). Both carry the sase
  project's `^prj` line (`created: 2026-06-01`, `task_count: 68`).
- All 13 affected reference notes have frontmatter `parent: "[[sase]]"`, so `sase.md` is
  the correct residence for those tasks.

History, from `git -C ~/bob log`:

| Commit | When (EDT) | What it did to `sase_agent_recovery.md` |
|---|---|---|
| `1b4b09ffd` | 10-19 | `bob task move sase.md -> sase_agent_recovery.md (7 tasks)`. The file became an 80-line agent-recovery project note with its own `^prj` line ("Failed, killed, or interrupted agents ..."). |
| `8ca09ee75` | 10-28 09:31 (`kellys-mbp`) | Rewrote the file: `@@ -1,80 +1,416 @@`. The agent-recovery content was replaced with sase project content. The same commit also contains legitimate `sase.md` edits (task statuses and dates), so reverting the whole commit would undo them too. |
| `25f329313` | 10-28 09:45 | Further edits to that sase content inside `sase_agent_recovery.md`. Every line it leaves in the file also exists in `sase.md`. |

The agent-recovery `^prj` line and its seven tasks are not in any current vault file.
They exist only in `8ca09ee75^`.

The `_conflicts/sase.kellys-mbp-2026-10-23T224729-0400.md` copy also contains the
astra line. `_conflicts/` is not scanned and is not part of the problem.

## Verification

Each variant was run as `bob ref scan --dry-run --no-hooks` against a scratch copy of the
vault in `/tmp`, which I deleted afterward.

| Variant | Result |
|---|---|
| Current vault | 13 failures, `multiple_open_ref_tasks` |
| Delete only the 14 duplicate ref blocks (46 lines) from `sase_agent_recovery.md` | 0 failures |
| Restore `sase_agent_recovery.md` to its `8ca09ee75^` content | 0 failures |

I recommend the restore over deleting only the 14 blocks. Deleting only the blocks would
leave 69 duplicated `#task` lines, including a second sase `^prj` line.

After the fix, `bob ref scan -w` will still apply one update and one marker, for
"stripe industry screen prep" (dry run: `1 updated`, `1 marker`). That is expected
work, not a failure.

## What to do

1. Make sure `sase_agent_recovery.md` is not open in Obsidian on any host. An open buffer
   could re-save the sase content over the restored file.
2. Restore the pre-overwrite agent-recovery note in the vault:

   ```bash
   git -C ~/bob show 8ca09ee75^:sase_agent_recovery.md > ~/bob/sase_agent_recovery.md
   ```

   Do not `git revert 8ca09ee75`, because the same commit carries legitimate `sase.md`
   edits.
3. Fix the dangling link at `sase_pypi_releases.md:35`. Its BLOCKS line links
   `[[sase_agent_recovery#^ref-gascity-advantages-over-sase-and-what]]`, an anchor the
   restored file no longer has. Delete that second link and keep
   `[[sase#^ref-gascity-advantages-over-sase-and-what]]`.
4. On athena, confirm `bob ref scan --dry-run` shows no `multiple_open_ref_tasks`. Then
   sync with `bob vault-sync`, as described in `docs/vault-git-sync.md`.
5. On the MacBook, pull, run `bob ref scan --dry-run`, then run `bob ref scan -w`.

## Caveats and open questions

- Git records only the result of the 10-28 overwrite, not the mechanism. Before relying
  on the fix, check whether anything on the MacBook could write `sase_agent_recovery.md`
  again: a stale editor buffer, or a second sync engine. `obsidian.md` says Obsidian Sync
  is retired and must not run alongside git sync. I did not check whether it is still
  linked. If the file is rewritten, the scan will refuse again.
- I did not inspect the MacBook checkout directly. Its refusal lines match this vault
  checkout (HEAD `f4df78c62`) exactly, so I assume the two are in sync.
- Restoring the file loses no content present in the current file. I compared content
  only, not line order.
- I did not edit the vault, commit, or sync. The steps above are recommendations.
