**Automatic reference publication across the tailnet — independent cdx research**

Researcher: cdx. Date: 2026-10-18. Scope: research and recommendation; no production configuration or application code changed. No peer swarm report, transcript, summary, or findings were consulted.

Automating this is a good idea. The useful requirement is that a successfully captured reference reliably becomes available for reading, without remembering a second command. Merely running `bob ref scan` more often is an incomplete solution: the present workflow depends on an intermittently available Mac, transfers an ignored intake directory separately from Git, and combines initial publication with ongoing annotation reconciliation.

My preferred destination is **one supervised publisher on athena, durable intake from all three machines, and a separate Mac annotation-sync schedule**. There is a much smaller improvement worth making first: repair the current Mac automation's visibility and scheduling. These are distinct options with different availability guarantees, not evidence that a distributed service must be built immediately.

**What is established, and what remains uncertain.** I inspected bob-cli at `b2a73b68628d5b6adf941e58140dbdb22ff19a8d`, the authorized chezmoi checkout at `0ae51ea0e03b2326cc5dfe6233af46ea3d70a3c8`, the relevant SASE memory through audited reads, upstream scheduler/rsync documentation, and three read-only commands on the Mac: its crontab, the tail of its Highlights scan log, and its installed `launchd.plist(5)` manual. I did not run a production scan, change the vault, test an implementation, or verify that installed binaries/scripts match these source revisions. Consequently, the observations establish architectural failure modes and one live configuration discrepancy; they do not identify the exact cause of every delayed PDF.

The existing path is:

```text
create on athena/apollo  -> local xlib/ (Git ignores it)
                               |
                        Mac pulls over SSH/rsync
                               v
create on Mac           -> Mac xlib/
                               |
                        Mac ref scan
                               v
                    lib/ + ref/ + reading task
                               |
                          vault Git sync
                               v
                         other machines
```

`create` already produces a PDF that a PDF reader can open. What it does not complete is the stable library placement, reference note, and reading-task workflow. I interpret “use the PDF” as use through that integrated workflow, including companion audio where requested. If the actual requirement is only “open the local bytes immediately,” printing/opening the generated intake PDF is a substantially smaller solution; it still leaves library publication unresolved.

Several code details matter to the decision:

- The documented create contract writes to `xlib/<type>/<stem>.pdf`; its normal next-step message is literally `next: bob ref scan`. Explicit outputs outside intake/library instead require targeted sync. [Create documentation][B1], [target workflow and next-step output][B2].
- `scan_library` runs a pre-scan hook, plans intake, moves files, discovers the entire library, plans PDF synchronization, then writes notes and tasks. Native Rust reads PDF markers; a Highlights application process is not required for initial publication. `sync_pdf` handles one PDF but does not perform the intake move, so running it on an `xlib` PDF is not an equivalent completion operation. [Sync implementation][B3], [path mapping][B4].
- Git vault sync intentionally excludes `xlib`. The configured pre-scan hook calls `bob_xlib_pull`, which immediately exits on Linux. On the Mac it probes athena/apollo, then pulls into a shared destination with `rsync -a --remove-source-files --ignore-existing`. [Vault bridge][B5], [pull script][C1].
- The existing capture job spool solves URL clipping, not publication. Capture's worker and Google Keep use typed ingest; `bob ref create` has its own routes and does not call that ingest entrypoint. A post-success change in only one of those paths would miss others. [Job lifecycle][B6], [typed ingest][B7].
- Reading-task writes can precede the reference-note write. The existing v2 executor deliberately recovers by adopting an already-created task on a later run; it explicitly does not promise a multi-file transaction. Reuse that behavior rather than claiming one file rename makes the whole operation atomic. [Reading execution][B8].

**The live schedule already exists, but its evidence is weaker than the runbook suggests.** On this inspection the Mac returned:

```cron
*/15 * * * * ~/bin/maybe_bob_highlights_sync -w >> /var/tmp/maybe_bob_highlights_sync.log
*/15 * * * * ~/.cargo/bin/bob projects sync >> /var/tmp/bob_projects.log
*/15 * * * * ~/.cargo/bin/bob task reconcile >> /var/tmp/bob_task_status_hooks.log
```

Thus the jobs are not staggered as the checked-in runbook describes, and the scan line omits `2>&1`. The checked-in wrapper suppresses successful scan output and prints failures to stderr; the named log therefore does not capture those failures. Its last forty lines were empty. This does **not** prove cron failed: stderr may be going to cron mail, and the installed wrapper was not compared byte for byte. It does mean an empty log is not evidence of successful processing. [Wrapper][C2], [documented maintenance schedule][B5].

The Mac's installed manual confirms that cron misses sleep-time runs, `StartInterval` also misses an interval during sleep, and `StartCalendarInterval` coalesces missed sleep-time events into a run on wake. Apple recommends launchd for timed jobs and documents the same distinction. Use a calendar trigger plus startup/login activation when migrating this schedule; do not assume that replacing cron with an interval-only plist solves wake-up recovery. A sleeping Mac still cannot publish anything. [Apple scheduling guide](https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/ScheduledJobs.html).

**The reliability problems are broader than the trigger.**

1. **Mac availability bounds publication today.** Tailnet memory says the Mac may be offline with its lid closed. Decreasing a 15-minute interval cannot fix hours of unavailability. Waking or keeping someone else's laptop awake is an unnecessarily fragile requirement for initial publication.
2. **One transfer can obstruct independent work.** A real pre-scan hook failure aborts the invoking scan before intake. The pull script treats SSH exit 255 as an offline/no-work result, so connectivity or authentication failure can be indistinguishable from expected absence. A manual pull has different behavior: it attempts a local scan even after some transfer errors. [Hook implementation][B9], [pull script][C1].
3. **Current collisions do not automatically resolve.** If two origins have `blogs/example.pdf`, `--ignore-existing` preserves the later source during the first pull. Once the first PDF moves into `lib`, a later pull can deliver the second PDF to `xlib`; the next intake then refuses the existing library destination. This is an inference from the script and intake planner, not an observed live incident. Repeating the scan does not fix it, and one intake collision can stop the whole batch. [Intake planner][B10].
4. **A directory lock is not crash recovery.** The shell wrappers use `mkdir` locks removed by traps. SIGKILL or an abrupt interruption can leave a directory that later invocations treat as a running job. Bob's native scan lock uses an OS file lock and has a bounded wait, but it cannot help if the wrapper skips before starting Bob. [Wrapper][C2], [scan lock][B11].
5. **The locks cover different writers.** The scan lock is machine-local under Bob state. The shown `scan` and `sync` entrypoints do not acquire the vault-maintenance lock used by `vault-sync`. Targeted `sync` also does not acquire the scan writer lock in its entrypoint. These protections do not establish mutual exclusion with Git checkout/merge or with another machine. Existing preimage checks remain useful but are not a distributed transaction. [Sync][B3], [guards][B12], [vault-sync][B13].
6. **A failed scan may already have changed files.** Intake moves precede note planning and dirty-target preflight. Individual PDF failures may coexist with successful note writes. Recovery must inspect actual stage completion instead of equating a nonzero exit with “nothing happened.” [Sync][B3], [intake execution][B10].
7. **Transfer atomicity is per file, not per reference.** PDF, audio, Markdown sidecar, and TextBundle assets must stay associated. The rsync manual requires quiescent sources for source-removal mode and recommends publishing finished files by rename. Bob already has atomic/fsynced PDF/audio installation primitives, but recursively copying the whole intake directory does not supply an explicit completed-bundle boundary. [Atomic copy][B4], [rsync manual](https://download.samba.org/pub/rsync/rsync.1).

A full scan can also import annotation tasks, reconcile reading status, and, with `-w`, change PDF markers. The live schedule already uses `-w`; the older generic setup example advises leaving marker writes manual. The implementation decision must explicitly preserve or revise that existing policy. Initial publication should not silently authorize marker write-back across every previously annotated PDF.

**I would adjust the requirements as follows.** These are proposed changes, not facts supplied by the request.

| Proposed requirement | Reason |
| --- | --- |
| Define distinct states: PDF saved, received by publisher, published, replicated | “Created” currently hides the remaining handoff. Each state answers a different user question. |
| Permit eventual publication during outages, with durable pending work | Reliable automatic completion cannot imply availability while the origin or publisher is offline. |
| Target publication within about 1–2 minutes after a complete bundle is reachable, excluding rendering and transfer time | This is a proposed acceptance target to measure, not a measured current capability. |
| Keep the raw local PDF available while pending | Useful offline behavior should not require a central server to be reachable. |
| Separate new-reference publication from annotation/lifecycle reconciliation | New intake should not be blocked by an unrelated old PDF or trigger broad writes. |
| Require at-least-once delivery with idempotent completion | Retries must be safe after lost acknowledgments and crashes; exactly-once network delivery is unnecessary. |
| Reserve manual action for semantic conflicts, corrupt files, unsupported inputs, or explicit recovery | Retrying transient failures should not require a human; guessing through conflicting content should. |
| Apply the completion contract to create, capture jobs, and Keep intake | Otherwise the user encounters different readiness rules for the same reference library. |
| Preserve external-output and dry-run semantics | An explicit PDF export outside the managed library should not silently become a remotely published reference. |

Companion audio needs its own completion semantics: requested audio should either be included before declaring the requested bundle ready or reported as a distinct pending/failed companion. Do not silently downgrade a requested listen result to a completed PDF-only success.

**The credible alternatives have different costs.**

| Approach | Strength | Limitation | Assessment |
| --- | --- | --- | --- |
| Repair the Mac schedule and add a bounded best-effort kick | Small change; preserves present ownership and transport | Still waits for Mac availability; full-scan failures remain | Best immediate improvement if waiting for the Mac is acceptable |
| Append a local full scan to every create | Little initial code; may publish locally immediately | Whole-library work, broad writes, hook delays, multiple generated writers | Useful diagnostic experiment, poor default architecture |
| Finalize only the new bundle on its originating machine | Fast local readiness, works offline, avoids an extra transfer | Concurrent stale clones can allocate the same names/tasks; needs bundle-aware conflict handling | Strong alternative if offline integrated readiness outranks centralized consistency |
| Make athena the single initial publisher | Removes Mac availability dependency; one place for final namespace checks and receipts | Requires reliable transfer/state tracking; athena outages defer publication | Recommended for the stated emphasis on reliability across three machines |
| Push every source URL to an athena renderer | One runtime/toolchain | Local PDFs, vault snapshots, authenticated pages, and local assets complicate source access | Do not require this; keep rendering where inputs are available |
| Watch every vault tree and scan on all machines | Appears immediate | Event loss, incomplete copies, feedback loops, repeated work and conflicting writers | Reject as the correctness mechanism |

The local targeted-finalizer option deserves serious consideration; it is simpler than a central publisher if rare cross-machine conflicts are acceptable. However, local `scan.lock` files do not coordinate three Git clones. Pull-before-write narrows a race without eliminating it, and Git's remote-wins-plus-conflict-copy policy does not guarantee that every generated task remains in the active note. I prefer a single initial publisher over adding a distributed lease or making random suffixes the public identity policy. A central publisher still does not solve concurrent human edits across machines; it removes one avoidable class of generated-write contention.

**The recommended design can stay small and use existing infrastructure.** It needs a durable outbox, an SSH transfer worker, a narrow publisher, and OS schedules—not a database cluster, message broker, HTTP service, or leader election.

```text
Each origin:
  existing renderer -> durable complete bundle + publication request
                                 |
                   immediate best-effort transfer kick
                   plus periodic/startup reconciliation
                                 |
                                 v
Athena:
  per-origin staging -> verified ready bundle -> scoped publisher
                                                |
                                      lib/ + ref/ + reading task
                                                |
                                          vault Git sync
                                                |
                                                v
Mac:
  library available -> Highlights annotations -> scheduled library reconciliation
```

A proposed processing state machine is:

```text
preparing -> ready -> received -> publishing -> published -> replicated
               |         |            |
               +---------+------------+--> retry later / blocked with reason
```

“Replicated” should mean a confirmed Git publication/sync event with clearly stated scope. Pushing to the remote is not proof that every destination machine has pulled it.

The essential contracts are:

- **Publish a manifest last.** Record a random internal request ID, origin, logical vault identity, intended relative paths, parent/type, file sizes and digests, and requested companions. This request ID is transport identity, not the public reference `id`. Write temporary files outside the discoverable ready set, flush them, then expose the manifest atomically. The receiver validates names, containment, completeness, and digests before marking the bundle ready.
- **Isolate incoming origins.** Receive into `origin/request-id` staging, not a shared final basename directory. Repeated delivery of the same request returns the existing receipt. Different bytes or intent under one request ID are a conflict. Use SSH/rsync as transport without treating `--ignore-existing` as deduplication or a successful publication acknowledgment.
- **Acknowledge actual stages.** Record received separately from published. Keep the origin's recovery copy until a published receipt is confirmed; if replication is pending, make that visible and retain a recoverable publisher copy. A lost reply causes a receipt lookup/retry, not rerendering the article or deleting the only PDF.
- **Reuse the one-PDF planning/execution machinery.** Add a scoped publication operation that promotes one complete bundle and invokes the existing reference/task planner with the final library paths. It must also resume a PDF already moved to `lib` whose note was never completed. Neither `scan` over the entire library nor `sync xlib/file.pdf` is a drop-in implementation.
- **Enforce publisher ownership.** Athena publishes new managed intake. The Mac maintenance path handles existing library items and must not independently consume the new outbox. During rollout, separate the new queue from legacy scan-discoverable `xlib`, or add an explicit, tested intake-disable/role contract. Disabling the old pull hook alone is insufficient if Mac scans can still consume local new intake.
- **Serialize local mutation with Git maintenance.** Establish one documented lock order for the maintenance and reference writer locks and use it in every participating write entrypoint. Network transfer and rendering stay outside those critical sections. Reuse the existing lock-aware vault-sync entrypoints rather than recursively acquiring the maintenance lock. Revalidate inputs after acquiring locks; retain editor-race checks.
- **Handle conflicts per bundle.** A malformed or conflicting item enters a visible blocked state while others proceed. Repeat delivery of the same completed request is a no-op. Reuse existing source-deduplication semantics; do not collapse distinct snapshots merely because their source URLs match.
- **Keep names and embedded links coherent.** Accepted policy makes reference ids follow stems (with numbered suffixes for id collisions) while reading-task block identity remains stable. A received filename collision is not permission to rename only the PDF: note paths, audio links, marker identity, and generated links may need coordinated updates. First-version behavior should retain and report a genuine collision; an automatic allocator can follow only with tested whole-bundle rewriting. Existing annotated references must never be replaced to clear intake.
- **Retain narrowly authorized marker behavior.** New publication may stamp the new bundle as required by its create contract. Existing annotated PDF write-back remains with the Mac reconciliation policy; the new publisher does not perform a global `scan -w`.

The public naming rules above come from the audited decisions `decisions:reference-ids-follow-file-stems` and `decisions:reference-renames-keep-identity`. There is no proposal here to replace public ids with UUIDs.

Use a systemd user oneshot plus timer on athena, with a startup trigger and a roughly one-minute reconciliation cadence. `OnUnitInactiveSec` can avoid immediately rerunning a slow drain; if using `OnCalendar`, `Persistent=true` catches missed activations. Persistence does not apply to monotonic timers. A timer will not start a second instance of its already-active service, but Bob's own locks are still needed against manual commands. Verify the user manager survives logout/boots, using lingering if appropriate. [systemd timers](https://www.freedesktop.org/software/systemd/man/latest/systemd.timer.html), [user lingering](https://www.freedesktop.org/software/systemd/man/latest/loginctl.html).

Origins should retry transfers on a schedule/startup and kick after successful creation; athena may additionally poll reachable origin outboxes as recovery. Pick one transfer/receipt protocol for both paths. Avoid requiring the original terminal or detached worker to survive. SSH failures need bounded timeouts, backoff, and per-host status so an unavailable Mac does not hold athena's local queue hostage.

Filesystem events are optional latency improvements. The authoritative pending set is durable state, enumerated periodically. A permanently nonempty failed queue can repeatedly activate a systemd path unit until rate limiting stops it; the Mac's installed manual similarly warns that WatchPaths can miss events and observe inconsistent state. Put delayed/blocked items outside an always-ready trigger set if using such a trigger. [systemd path units](https://www.freedesktop.org/software/systemd/man/latest/systemd.path.html).

Extend existing `bob ref jobs`/doctor reporting or provide a similarly coherent view that includes create-originated publication work. Today those jobs are machine-local clipping records, so this needs an explicit model extension, not just different wording. Show oldest pending age, origin, stage, last attempt/error, next retry, publisher heartbeat, and actual PDF/note paths. Deduplicate notifications and alert on sustained failure or backlog age; routine completion need not produce a notification. Replace the hard-coded Mac timing footer with observed state. [Current jobs contract][B6].

There is also a real size boundary: vault sync warns at 50 MiB and refuses staging at 95 MiB. A large PDF or audio file can be published locally but fail to reach the other machines. Check this before claiming cross-machine readiness, and expose a distinct replication error. Do not add a second general-purpose sync engine or Git LFS silently as part of this feature. [Vault-sync limits][B13].

**A small improvement can ship before that design.** Make the existing Mac schedule chezmoi-managed, use calendar-based launchd scheduling with load activation, capture both stdout and stderr, and record a last-success/last-failure heartbeat. Replace stale-prone wrapper locks with OS-held locks or consolidate on native locking. Preserve the current `-w` policy deliberately. A create-triggered best-effort scheduler kick can shorten the wait, but its failure must leave the current durable intake intact and the timer must remain the fallback. Measure full-scan duration and dirty-target failures before shortening the cadence. This is enough if “automatic when the Mac is next awake” meets the real requirement.

Migration to athena needs an inventory of each origin's outstanding intake and any library PDF lacking its note. Preserve source copies, pause the old destructive pull path during ownership transfer, reconcile duplicates deliberately, and only then enable the new publisher. Keep the old manual scan as repair/backfill tooling. A simple rollback stops the new consumer while retaining every ready, blocked, and received bundle; it must not re-enable competing consumers against the same queue.

**The acceptance tests should demonstrate recovery, not just successful scheduling.**

| Scenario | Required result |
| --- | --- |
| Create on each host while the Mac is asleep | Athena publishes reachable completed bundles; no manual scan needed |
| Origin goes offline before transfer | Local PDF and request survive; publication resumes on reconnect |
| Lose acknowledgment after transfer/publication | Retry returns the same receipt; no duplicate task or note |
| Kill publisher after PDF promotion or task insertion | Restart completes the existing publication and adopts the task |
| Kill renderer or transfer midway through audio/TextBundle | Incomplete bundle is never eligible; no mismatched companions |
| Two hosts choose one basename for different content | Both inputs survive; conflict is explicit; unrelated requests proceed |
| Repeat the same request or capture an already-known source | Correct idempotent/deduplication result without overwriting an annotated PDF |
| Scan races vault-sync or editor save | Locks/preimage checks produce safe retry or a visible conflict |
| One host has bad SSH credentials | Other origins and local work continue; failure remains observable |
| A 95 MiB-or-larger attachment reaches publication | Replication failure is explicit and does not claim all-machine readiness |
| Scheduler restarts, user logs out, or Mac wakes | Pending work is rediscovered without a new create event |
| Dry run, custom vault, explicit external output, or audio-only backfill | Existing contract is preserved; no accidental cross-vault publication |

These are proposed implementation gates. No new tests or benchmarks were executed for this research. Remaining decisions are the acceptable offline delay, whether athena or apollo has the better actual uptime/storage profile, and how long to retain acknowledged origin copies. Athena is the default recommendation because it is the home server already hosting the workflow; switch the configured owner to apollo if operational evidence favors it. Use explicit owner migration, not automatic failover with two publishers.

Source links below identify the exact code inspected; local source reading was used rather than fetching repository files over the web.

[B1]: https://github.com/bobs-org/bob-cli/blob/b2a73b68628d5b6adf941e58140dbdb22ff19a8d/docs/highlights-create.md
[B2]: https://github.com/bobs-org/bob-cli/blob/b2a73b68628d5b6adf941e58140dbdb22ff19a8d/src/native/highlights_ref/stamp.rs#L795
[B3]: https://github.com/bobs-org/bob-cli/blob/b2a73b68628d5b6adf941e58140dbdb22ff19a8d/src/native/highlights_ref/sync.rs
[B4]: https://github.com/bobs-org/bob-cli/blob/b2a73b68628d5b6adf941e58140dbdb22ff19a8d/src/native/highlights_ref/io.rs
[B5]: https://github.com/bobs-org/bob-cli/blob/b2a73b68628d5b6adf941e58140dbdb22ff19a8d/docs/vault-git-sync.md
[B6]: https://github.com/bobs-org/bob-cli/blob/b2a73b68628d5b6adf941e58140dbdb22ff19a8d/docs/ref-jobs.md
[B7]: https://github.com/bobs-org/bob-cli/blob/b2a73b68628d5b6adf941e58140dbdb22ff19a8d/src/native/highlights_ref/ingest.rs
[B8]: https://github.com/bobs-org/bob-cli/blob/b2a73b68628d5b6adf941e58140dbdb22ff19a8d/src/native/highlights_ref/reading_execute.rs
[B9]: https://github.com/bobs-org/bob-cli/blob/b2a73b68628d5b6adf941e58140dbdb22ff19a8d/src/native/highlights_ref/hooks.rs
[B10]: https://github.com/bobs-org/bob-cli/blob/b2a73b68628d5b6adf941e58140dbdb22ff19a8d/src/native/highlights_ref/doctor.rs#L685
[B11]: https://github.com/bobs-org/bob-cli/blob/b2a73b68628d5b6adf941e58140dbdb22ff19a8d/src/native/highlights_ref/scan_json.rs#L119
[B12]: https://github.com/bobs-org/bob-cli/blob/b2a73b68628d5b6adf941e58140dbdb22ff19a8d/src/native/highlights_ref/guard.rs
[B13]: https://github.com/bobs-org/bob-cli/blob/b2a73b68628d5b6adf941e58140dbdb22ff19a8d/src/native/vault_sync.rs
[C1]: https://github.com/bbugyi200/dotfiles/blob/0ae51ea0e03b2326cc5dfe6233af46ea3d70a3c8/home/bin/executable_bob_xlib_pull
[C2]: https://github.com/bbugyi200/dotfiles/blob/0ae51ea0e03b2326cc5dfe6233af46ea3d70a3c8/home/bin/executable_maybe_bob_highlights_sync

**Recommended solution:** repair the current Mac schedule's supervision and diagnostics immediately, then implement automatic, durable publication of individual completed reference bundles on athena. Keep rendering local, use best-effort kicks plus periodic recovery, reuse Bob's existing reference/task logic, and retain Mac-only annotation reconciliation. This removes the laptop from the initial-publication dependency while keeping manual `bob ref scan` available for exceptional repair.
