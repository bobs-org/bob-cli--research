# Obsidian Sync Footprint Audit for bob-cli-1l.1

- **Phase:** `bob-cli-1l.1`
- **Audit timestamp:** 2026-08-27T14:10:16Z
- **Vault:** `bob`, Obsidian Sync vault `8a259ad922718b6d8400c1f0e3ba8abe`
- **Scope:** athena headless state DB, athena filesystem, MacBook filesystem over SSH, and the `bobs-org/bob` Git remote checkout
- **Detailed inventory:** `obsidian_sync_footprint_inventory_bob-cli-1l.1_20260827T141016Z.jsonl`
- **Summary JSON:** `obsidian_sync_footprint_summary_bob-cli-1l.1_20260827T141016Z.json`

This audit was read-only. It did not change sync settings, move vault files, delete or
create any remote vault, or run a bidirectional sync against a temporary tree. The
headless config was read only through redacted fields; auth tokens, encryption keys,
salts, passwords, and raw secret-bearing config were not copied into this report.

## Headline Findings

| Finding | Evidence |
| --- | --- |
| The live remote is small. | `server_files` currently has 5,804 live files plus 100 zero-byte folder markers, totaling 114,527,509 bytes / 109.222 MiB. This is a live-index total, not billed Storage usage. |
| The pending DB queue is empty. | `pending_files` has 0 rows. Recent sync-log upload attempts still repeatedly include `xlib/chat/AGENTS.pdf`, so the queue state and active retry pressure are distinct. |
| No live remote file is unique to the remote. | Every non-folder live remote path exists on Athena, the MacBook, or the Git remote checkout. Files absent from Athena are present on the MacBook. |
| The durable gap is Git, not device presence. | 96 live remote files / 22.759 MiB are absent from Git, mostly `_meta/migration/`, `xmind/`, recent plugin payloads, and `img/20260827_070810.png`. |
| MacBook filters differ from Athena. | Athena excludes only `old_lib` and allows `image,audio,pdf,video`. The MacBook IndexedDB sync record lists `ignoreFolders = lib, lit_review, old_lib` and `allowTypes = image,audio,pdf,video,unsupported`. |
| Billed usage still needs the desktop UI reading. | SSH could read desktop IndexedDB metadata but macOS accessibility denied UI text extraction (`osascript is not allowed assistive access`). The actual Settings -> Sync Storage usage is therefore marked awaiting Bryan's UI reading, not guessed from state DB bytes. |

## Source Inventory

| Source | Files/entries | Size |
| --- | ---: | ---: |
| Obsidian Sync live remote files | 5,804 files | 109.222 MiB |
| Obsidian Sync live folder markers | 100 markers | 0 MiB |
| Athena `local_files` state table | 6,544 rows | 1,741.082 MiB |
| Athena filesystem manifest | 6,434 files | 1,741.091 MiB |
| MacBook filesystem manifest | 6,945 files | 2,954.614 MiB |
| Git remote checkout at `aedc9f5e7ad01c006b2fa00c9038869bb4d96c4e` | 6,407 files | 1,461.989 MiB |
| State DB `pending_files` | 0 rows | 0 MiB |

Athena filesystem state and the `local_files` table differ by zero-byte folder marker
rows plus two filesystem-only files: `.gitignore` and
`.obsidian/plugins/obsidian-tasks-plugin/data.json.20260529092052.bak`.

## Live Remote by Root

| Root | Live files | Live size |
| --- | ---: | ---: |
| `img/` | 187 | 62.245 MiB |
| `_meta/` | 49 | 15.318 MiB |
| `.obsidian/plugins/` | 52 | 10.063 MiB |
| `lib/` | 27 | 5.850 MiB |
| year/daily-note trees | 2,964 | 5.484 MiB |
| `xmind/` | 20 | 3.947 MiB |
| `_generated/` | 1,131 | 3.232 MiB |
| vault-root files | 615 | 1.619 MiB |
| `ref/` | 393 | 0.519 MiB |
| all other roots | 366 | 1.144 MiB |

This accounts for the current live Sync index only. Obsidian version history and
recently deleted attachment retention are not represented by this table.

## Presence and Durability

| Difference | Files | Size | Interpretation |
| --- | ---: | ---: | --- |
| Remote files absent from Athena | 79 | 19.060 MiB | All are present on the MacBook; none are remote-only material. |
| Remote files absent from the MacBook | 0 | 0 MiB | The MacBook filesystem has every non-folder live remote path. |
| Remote files absent from both devices | 0 | 0 MiB | No current live remote file would be lost solely by losing the remote, assuming the MacBook snapshot is preserved. |
| Remote files absent from Git | 96 | 22.759 MiB | Must be preserved before any rebuild/delete operation. |
| Athena filesystem paths absent from remote entries | 709 | 1,651.081 MiB | Almost entirely the excluded `old_lib/` tree. |
| MacBook filesystem paths absent from remote entries | 1,141 | 2,845.684 MiB | Dominated by excluded `old_lib/`, excluded `lit_review/`, larger local `lib/`, and a few eligible strays. |
| Athena eligible paths absent from remote entries | 3 | 0.110 MiB | `xlib/chat/AGENTS.pdf`, one Tasks plugin backup JSON, and `.obsidian/workspace.json`. |
| MacBook eligible paths absent from remote entries | 4 | 10.109 MiB | `_meta/migration/reports/asset_link_graph.tsv`, `.DS_Store`, `.obsidian/.DS_Store`, and `.obsidian/workspace.json`. |

The highest-value pre-rebuild preservation targets remain:

| Root | Why it matters |
| --- | --- |
| `_meta/migration/` | 49 live remote files / 15.318 MiB. Most are absent from Athena and Git, but present on the MacBook. The MacBook also has one extra 10.059 MiB eligible `_meta/` report absent from the remote. |
| `xmind/` | 20 live remote files / 3.947 MiB. All are absent from Athena and Git, present on the MacBook, and referenced by Markdown. Athena currently filters them as unsupported; the MacBook currently allows unsupported. |
| `.obsidian/plugins/` | 52 live remote files / 10.063 MiB. Present on both devices, but several recent plugin payloads are absent from Git and appear in retry logs. |
| `img/` | 187 live remote files / 62.245 MiB. One recent image is absent from Git; four images totaling 2.642 MiB are apparent orphans under the union-Markdown scan and need review, not automatic deletion. |

## Device Filter Classification

Current live remote files classify as:

| Classification | Files |
| --- | ---: |
| Eligible on both current devices | 5,698 |
| Eligible on Athena only | 27 |
| Eligible on MacBook only | 79 |

The 27 Athena-only files are the remote `lib/` files, because the MacBook currently
excludes `lib`. The 79 MacBook-only files are the remote files Athena filters or lacks,
mostly `xmind/` unsupported files and `_meta/migration/` artifacts.

The MacBook's `lib` and `lit_review` exclusions are a material policy drift from the
proposed rebuild policy in the design plan. Later phases should treat that as an
explicit approval/reconnect decision rather than assuming both devices share Athena's
filter set.

## Reference and Orphan Review

The reference pass scanned current Markdown on both Athena and the MacBook:

| Metric | Count |
| --- | ---: |
| Distinct Athena references | 15,783 |
| Distinct MacBook references | 15,788 |
| Resolved referenced paths | 5,438 |
| Remote attachment paths checked | 291 files / 87.249 MiB |
| Apparent remote attachment orphans | 40 files / 17.773 MiB |

Apparent orphan roots:

| Root | Files | Size | Notes |
| --- | ---: | ---: | --- |
| `_meta/` | 34 | 15.095 MiB | Migration reports/tools; likely archive-policy material, not active note content. |
| `img/` | 4 | 2.642 MiB | Recent screenshots needing visual/user review before any cleanup decision. |
| `ref/` | 1 | 0.036 MiB | One nested asset under `ref/docs`. |
| `_zorg_templates/` | 1 | ~0 MiB | Legacy template residue. |

The apparent image orphan list is:

- `img/20260715_182458.png`
- `img/20260715_203105.png`
- `img/20260814_122025.png`
- `img/20260814_122458.png`

This is a review list only. The scanner resolves exact paths, extensionless note paths,
and unambiguous basename/stem links across the union of Athena and MacBook Markdown,
but ambiguous references remain conservative.

## Recent History Pressure

The headless state DB does not expose billed history or per-file version-history events.
The available read-only history signal is Git activity since 2026-07-28T00:00:00Z:

| Root | File events | Unique paths |
| --- | ---: | ---: |
| vault-root files | 434 | 67 |
| year/daily-note trees | 117 | 34 |
| `ref/` | 81 | 64 |
| `old_lib/` | 39 | 39 |
| `done/` | 38 | 6 |
| `lib/` | 18 | 18 |
| `podcasts/` | 15 | 15 |
| `img/` | 7 | 7 |

There were 61 Git commits in that window. `_generated/` had no Git file events in this
last-30-day sample, matching the design plan's earlier observation. This does not prove
Sync history is small; it only says Git did not see recent `_generated/` churn.

## Pending Uploads and Retry Pressure

`pending_files` is empty, but the current sync log repeatedly retries uploads and then
records `Sync error: {}`. Top recent upload attempts in the log include:

| Path | Attempts observed in log |
| --- | ---: |
| `xlib/chat/AGENTS.pdf` | 230 |
| `.obsidian/plugins/bob-navigation-hotkeys/main.js` | 175 |
| `.obsidian/plugins/task-status-cycler/main.js` | 123 |
| `.obsidian/plugins/bob-navigation-hotkeys/manifest.json` | 59 |
| `gtd_daily.md` | 49 |

The only Athena eligible path absent from the remote with material size is
`xlib/chat/AGENTS.pdf` at 101,355 bytes / 0.097 MiB. The failure mode is therefore not
that a new live file exceeds the per-file limit.

## Billed Storage Usage

Do not use the 109.222 MiB live-index total as billed Storage usage. The plan requires
the actual desktop Obsidian Settings -> Sync value. I attempted a read-only MacBook SSH
accessibility query, but macOS returned:

```text
osascript is not allowed assistive access
```

The audit inventory therefore marks billed Storage usage as **awaiting Bryan's UI
reading**. Until that value is recorded, recommendations should continue to preserve
the distinction between:

- live remote bytes from `server_files`: 109.222 MiB;
- billed Storage usage from the Obsidian desktop UI: not available through this audit;
- historical/version bytes: not represented by the state DB.

## Recommendations for Later Phases

| Content class | Measured reclaim | Reference evidence | Activity evidence | Durability evidence | Current disposition |
| --- | ---: | --- | --- | --- | --- |
| `old_lib/` | 0 live remote MiB; 1,650.920 MiB local on both devices; 1,375.677 MiB in Git | Not part of live remote audit | 39 Git file events in last 30 days | Present on Athena, MacBook, and Git | Keep excluded. |
| `_meta/migration/` | 15.318 MiB live remote plus 10.059 MiB extra MacBook-local report | Mostly unreferenced by union Markdown | No Git activity in the last-30-day Git sample | Present on MacBook; much absent from Athena and Git | Archive and verify before excluding or deleting. |
| `xmind/` | 3.947 MiB live remote | Referenced by Markdown | No Git activity; unsupported content class | Present on MacBook only, absent Athena/Git | Preserve first; decide whether `unsupported` should sync in rebuilt vault. |
| `.obsidian/plugins/` | 10.063 MiB live remote | Config payload, not Markdown-linked | Heavy recent retry pressure in sync log | Present on both devices; several recent files absent Git | Keep syncing unless per-device plugin provisioning replaces Sync. |
| `img/` | 62.245 MiB live remote; only 2.642 MiB apparent orphan review list | Most images resolve from union Markdown | 7 Git events in last 30 days; one fresh image absent Git | Present on both devices; almost all Git-backed | Keep syncing; review four apparent orphans manually. |
| `lib/` | 5.850 MiB live remote; 62.804 MiB MacBook-local | Active reference/library content | 18 Git file events in last 30 days | Remote files present on both devices and Git | Resolve MacBook `lib` exclusion before reconnecting devices. |

## Done Condition

This report plus the JSONL inventory account for every live remote entry and every
local path absent from the remote, with presence, size, hash/blob identity, top-level
root, extension/kind, eligibility, reference count, and independent-copy evidence. The
only intentionally incomplete field is billed Storage usage, which is marked awaiting
the desktop UI reading because it was not safely accessible over SSH.
