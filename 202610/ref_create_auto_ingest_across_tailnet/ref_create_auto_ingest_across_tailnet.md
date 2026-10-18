# Making `bob ref create` usable without a manual `bob ref scan`

> **Research query:** I run `bob ref create` from any of the three machines on my tailnet, but the PDF it generates isn't usable until `bob ref scan` runs somehow. How can I make this convenient and automatic, reliably, so I rarely need to run `bob ref scan` by hand? Is this plan a good idea, would a different approach be better, and which requirement adjustments are justified, ending with a recommended solution?

![Infographic: today a PDF created on any host waits in local xlib/ until the Mac pulls and scans it (4.6 min median delay, 11.6 h longest, 24% of PDF commits missing their note); the proposal runs one locked intake transaction on the creating host (lock and pull, re-check and ingest one PDF, commit and push the PDF, ref note, and reading task together), keeps the PDF queued in local xlib/ for a local intake-only timer when it cannot ingest safely, leaves annotation sync on the Mac, and rolls out in phases 0 to 3](ref_create_auto_ingest_across_tailnet_infographic.png)

## Bottom line

- **The goal is right. The literal plan, running `scan` automatically and more often, is [the wrong mechanism](#critique-of-the-plan).** `scan` does two jobs with different owners:
  1. **Intake:** move one new PDF from `xlib/` into `lib/`, write its ref note, and file its reading task.
  2. **Annotation sync:** walk all 469 library PDFs and fold Highlights sidecars into notes.

  Your pain is entirely job 1. Job 2 belongs on the Mac on a schedule.
- **Recommendation: have `create` finish its own intake on the host that made the PDF ("[ingest at birth](#phase-1-create-finishes-its-own-intake)").** It should use the same lock-and-sync pattern `bob ref rename` already uses:
  1. take the vault-maintenance lock (`bob_sync.lock`), then the scan lock;
  2. pull;
  3. ingest just that PDF;
  4. commit and push as one commit.

  Git then delivers a complete reference (PDF, note, reading task) to every host in seconds, even while the Mac is asleep.
- **When inline ingest can't run, the PDF stays queued in local `xlib/`.** That covers lock busy, offline, collisions, and the size limit. [A per-host `bob ref scan --intake-only` timer](#phase-2-close-the-window-in-scan-and-retire-the-bridge) drains leftovers. The Mac's `bob_xlib_pull` rsync bridge is retired once every host runs the new binary.
- **Ship a small fix to `scan` with it.** Today `scan` moves PDFs into `lib/` before writing their notes, and the Mac's vault-sync regularly pushes the PDF alone. I measured this in [24% of the PDF-adding commits](#lead-researcher-findings-that-change-the-picture). `scan`'s write phase should hold `bob_sync.lock` too.
- **Fastest relief today, with no code:** [fix the Mac cron's stderr logging](#phase-0-today-with-no-bob-cli-change). For interactive creates on Linux, optionally run `ssh mac bob_xlib_pull` afterwards (works only while the Mac is awake).

## What actually happens today

Verified current flow:

```text
create on athena/apollo ─► host xlib/ (gitignored)
                               │  Mac cron */15: bob_xlib_pull (rsync --remove-source-files)
create on the Mac ───────► Mac xlib/
                               │  Mac `bob ref scan -w` (cron, Bob Refs ⌘S, or by hand)
                               ▼
                      lib/ PDF + ref/ note + reading task ──vault-sync (git)──► every host
```

- **`create` stops at the spool.** It renders and stamps `xlib/<type>/<stem>.pdf`, then prints `next: bob ref scan` (`print_next_step`, `stamp.rs:795`).
  - The same stop happens on every producer path: four call sites in `create.rs`, plus `clip.rs` and `collection.rs`.
  - The typed `ingest_url` path behind the `bob capture` worker and `gkeep pull` also stops there (`ingest.rs:1126`).
- **What "usable" needs.**
  - **The PDF in the Mac's `lib/`:** Highlights watches `lib/`.
  - **The ref note and reading task:** needed by `⌘↩` from Obsidian, Bob Refs, `bob ref list`/`today`, and agents.
  - Both exist only after a scan.
- **What git carries.**
  - `xlib/` is gitignored, so it moves between hosts only through the Mac's rsync pull.
  - `lib/` (PDFs, MP3s, sidecars) and `ref/` are tracked.
- **Only the Mac drains intake.** `bob_xlib_pull` exits 0 on Linux. On the Mac it probes athena and apollo over SSH, rsyncs, then scans.
- **Measured delay from render to library (cld, n = 286 bob-rendered PDFs since 2026-09-20):**

  - **Delay:** Median 4.6 min · p75 10.6 min · p90 29.9 min · Max 11.6 h
  - 18 PDFs waited more than an hour, all overnight with the lid closed.
  - 38% arrived within 2 min, which is consistent with ⌘S or a manual scan right after `create`.
- **Scan cost.** A full read-only scan takes about 7–8 s (469 PDFs). A one-PDF `bob ref sync` takes about 0.07–0.08 s (cld and gem agree).

### Lead-researcher findings that change the picture

1. **The Mac cron scan *is* running.** grk's headline claim, that the job "has not started since 2026-09-14", is wrong.
   - 114 of 268 lib-PDF commit events since 2026-09-20 (43%) landed on minute :00/:15/:30/:45. A uniform spread would put about 18 on those minutes.
   - The pattern continues through today (06:45:36, 11:45:38, 12:45:08).
   - The 0-byte log is explained by the wrapper staying silent on success, plus a cron line with no `2>&1` (cdx's reading). `scan.lock` is an flock file, so its mtime is not evidence of anything.
   - The Mac's cron mailbox is empty (0 bytes, reset 07:01 today), so there is no captured error output either.
   - **What is broken is observability, not the schedule.**
2. **The "half-committed" state is real and frequent, not hypothetical.**
   - In **65 of 268** PDF-adding commits (24%), the Mac's vault-sync pushed the `lib/` PDF *without* its ref note. The note followed 16–687 s later (median 19 s).
   - Example: `113cbf90` (12:45:08, PDF only), then `0de1c54d` (12:45:43, note plus `sase.md` reading task).
   - Cause:
     - `scan_library` runs `execute_xlib_intake` *before* planning all 469 PDFs (`sync.rs:46–56`).
     - The scan holds only `scan.lock`.
     - The Mac's vault-sync LaunchAgent runs every 15 s and takes only `bob_sync.lock`.
   - This is harmless only because one host writes notes today. A full `bob ref scan` on another host inside that window would plan `note_action: create` and a duplicate reading task (cld reproduced this in a scratch vault). Any multi-host design must close this window.
3. **The exclusion primitive already exists.**
   - `vault-sync`'s `run_cycle` silently skips its cycle when `bob_sync.lock` is held (`acquire_lock_quiet_if_held`, `vault_sync.rs:199`).
   - `bob ref rename` already does exactly what ingest needs (`rename/plan.rs:190–260`):
     1. maintenance lock, then scan lock;
     2. pre-sync pull;
     3. write;
     4. commit;
     5. post-sync push.
   - The lock file follows `${XDG_RUNTIME_DIR:-/tmp}`. I verified it is consistent between the sync service and interactive or agent shells on athena (`/run/user/1000`) and on the Mac (`/tmp`). Any new timer must run in that same environment.
4. **cld's `bob ref sync` relative-path bug reproduces.**
   - From `~/bob`, `bob ref sync lib/chat/<x>.pdf --dry-run` plans a **new** `ref/<x>.md` and a duplicate `^ref-…-2` reading task.
   - The absolute path correctly reports `note_action: none`.
   - Cause: `required_path` only expands `~`, and `pdf_path_metadata` (`io.rs:10`) strips the absolute `lib_dir` prefix from an unresolved relative path.
   - Any scoped-ingest code must canonicalize paths. The bug is tracked as `bob-cli-9a` (filed by cld; I added an independent reproduction).
5. **Fresh ingest rarely trips the dirty-target guard.** `ensure_safe_to_write` exempts v2 default reading-task destinations and ignores targets that don't exist yet (`guard.rs:99`). A new note plus a default reading task is almost never vetoed. cld's "sync again on dirty target" step is a corner case, not the main path.
6. **Git's size ceiling is not a practical issue, but it has to be checked.**
   - The largest library PDF is 19.6 MB (p99 3 MB).
   - A file of 95 MiB or more in `lib/` makes `vault-sync` fail the *whole* cycle on that host (`preflight_one_file`, `vault_sync.rs:600`).
   - Inline ingest must refuse such files and leave them queued.

## Where the reports disagreed and how I resolved it

Each item gives the question, the reports' positions, and the resolution.

- **Is the Mac drain dead?**
  - *Positions:* grk: yes, fix it first. cld and cdx: logging is invisible, can't prove failure.
  - *Resolution:* **It runs** ([finding 1](#lead-researcher-findings-that-change-the-picture)). Fixing stderr capture is hygiene, not the cure.
- **Live crontab**
  - *Positions:* gem quoted the documented staggered `0,15,30,45 … 2>&1` line
  - *Resolution:* gem described the docs, not the machine. Live: three `*/15` jobs on the same minute, no `2>&1` (cdx, cld, grk, and my own `crontab -l`).
- **Where intake runs**
  - *Positions:* cld and gem: the creating host. cdx: athena as the sole publisher. grk: keep the Mac and add a nudge.
  - *Resolution:* **The creating host, under the maintenance lock** (see [requirement adjustments](#requirement-adjustments) and [options compared](#options-compared)).
- **Write straight into `lib/`?**
  - *Positions:* gem: yes, plus `sync_pdf` under `scan.lock` (5 s). cld: no, that publishes the half-state.
  - *Resolution:* Both are partly right. Writing into `lib/` is fine **only** while holding `bob_sync.lock` from the move until the note is written. gem's design omits that lock, and the 24% split-commit rate shows vault-sync will interleave.
- **Filesystem watchers on `xlib/`**
  - *Positions:* grk: yes (`WatchPaths`/`QueueDirectories`). cld, cdx, gem: no.
  - *Resolution:* **No, as the correctness mechanism.** `scan` leaves empty `xlib/<type>/` directories behind, so `DirectoryNotEmpty`/`QueueDirectories` would fire forever. Apple documents that `WatchPaths` can miss changes. Timers are the backstop.
- **Mac wake recovery**
  - *Positions:* grk: `RunAtLoad` drains on lid-open
  - *Resolution:* Incorrect. `RunAtLoad` fires when the job loads (login), not on wake, and `StartInterval` drops intervals missed during sleep. Only `StartCalendarInterval` coalesces missed runs into one run on wake (cdx, from `launchd.plist(5)`).
- **SSH nudge to the Mac**
  - *Positions:* grk: the main fast path. cld: a stopgap. gem: rejected.
  - *Resolution:* **Stopgap only.** It can't wake the Mac (`womp 0`), and agents' creates won't use it.
- **gem's reliability table ("100%", "40%")**
  - *Positions:* —
  - *Resolution:* Unsupported figures. I ignored them.
- **Machine roles**
  - *Positions:* gem: athena is a "Linux desktop"
  - *Resolution:* Per tailnet memory, athena is the home server and apollo is the DigitalOcean rendezvous server.

## Critique of the plan

**What's right.**

- Two commands for one intent is a bad seam. You think "create = add to my library"; the system thinks "create = drop in a spool".
- Every producer pays for that seam: `create`, `bob capture` URL jobs, `gkeep pull`, and `--listen` attach.

**What I'd change.**

1. **Automate intake, not `scan`.** Automating the full scan drags along:
   - Mac-only annotation work;
   - marker write-back (`-w`);
   - whole-library dirty-target vetoes;
   - a pre-scan SSH hook;
   - 7–8 s of work per article.
2. **"Any of three machines" must not become "any machine runs full scans."**
   - Two hosts rendering the same sidecar write different `highlights_synced_at` values, which causes git conflicts (cld C3).
   - Linux full scans also widen the half-state window.
3. **Don't make a laptop a hub.**
   - The Mac sleeps with its lid shut, and it is a shared machine ("Kelly's MacBook Pro").
   - Every athena or apollo PDF currently waits on it.
4. **Don't build a distributed queue for a one-person, three-host vault, at least not yet.** cdx's athena-publisher design (outbox, manifests, receipts, a state machine) solves races that the lock-plus-pre-sync design already shrinks to about a second. It also makes athena, which had outages this week, the single point of failure.

## Requirement adjustments

*Proposed; not in your request.*

1. **Reframed goal.** A successful `create` means the reference is *in the library*: PDF in `lib/`, ref note written, reading task filed, pushed. "Scan runs automatically" is no longer the goal.
2. **New hard invariant.** Each reference is born by exactly one host, with no half-committed states. The PDF, note, and task land in one commit. This also fixes today's 24% split commits.
3. **Graceful degradation.** If inline ingest can't run, `create` still succeeds (exit 0), says `queued: <reason>`, and a local drain finishes the job later. The Mac is never required for intake.
4. **Wider scope: every producer.** `create` (all variants), the ref-jobs worker, `gkeep pull`, and `--listen` attach share one ingest step.
5. **Narrower scope: annotation sync is unchanged.** It stays a Mac-only full scan on a schedule plus ⌘S. New-reference ingest never writes PDF bytes (`-w`), because `create` already stamped the marker. cld observed `pdf_marker_action: none` on the first scan.
6. **Contract change.** `create` on athena or apollo now produces vault commits, including SASE agents' creates. `-k/--keep-intake` and a per-host config switch preserve today's behavior.
7. **Honest offline bound.** If the creating host can't pull first (it's offline), the PDF queues and does not ingest blind. You can still force a local intake with `bob ref scan`. Reading in Highlights still needs the Mac awake; that limit can't be engineered away.

## Options compared

Each option lists its latency for an athena-made PDF to reach the Mac, whether it works while the Mac sleeps, and the verdict.

- **A. Tighter Mac cron (1–5 min)**
  - *Latency for an athena-made PDF to reach the Mac:* Minutes, while awake
  - *Works while the Mac sleeps?* No
  - *Verdict:* Interim at best. A 7–8 s full scan each tick on battery.
- **B. SSH nudge after `create`**
  - *Latency for an athena-made PDF to reach the Mac:* Seconds, while awake
  - *Works while the Mac sleeps?* No
  - *Verdict:* Zero-code stopgap for interactive use.
- **C. Watchers (`.path`, `WatchPaths`, `QueueDirectories`)**
  - *Latency for an athena-made PDF to reach the Mac:* Seconds
  - *Works while the Mac sleeps?* Linux only
  - *Verdict:* Reject as the mechanism (see [where the reports disagreed](#where-the-reports-disagreed-and-how-i-resolved-it)).
- **D. `create && scan`, or a full scan on every host**
  - *Latency for an athena-made PDF to reach the Mac:* Seconds
  - *Works while the Mac sleeps?* Yes
  - *Verdict:* **Reject.** Violates single-writer for annotations, widens the half-state, and full-library vetoes block the new PDF.
- **E. Track `xlib/` in git with athena ingesting**
  - *Latency for an athena-made PDF to reach the Mac:* 30–60 s (two hops)
  - *Works while the Mac sleeps?* While athena is up
  - *Verdict:* Reject. Doubles binary churn in git (an `xlib` add, then a `lib` move) and moves the single point of failure to athena.
- **F. athena as sole publisher with an outbox protocol (cdx)**
  - *Latency for an athena-made PDF to reach the Mac:* ~1–2 min target
  - *Works while the Mac sleeps?* Yes
  - *Verdict:* Sound but heavy. Revisit only if F's narrower cousin, G, shows real cross-host collisions.
- **G. Ingest at birth under the maintenance lock** (cld, with gem's direction plus the lock)
  - *Latency for an athena-made PDF to reach the Mac:* **~2–15 s** (push, then the Mac's 15 s pull); 0 s on the Mac
  - *Works while the Mac sleeps?* **Yes.** The note and task exist everywhere immediately; the PDF reaches the Mac on wake.
  - *Verdict:* **Adopt.** (Phases below: [recommended solution in phases](#recommended-solution-in-phases).)

## Recommended solution in phases

### Phase 0 today with no bob-cli change

*Scope: chezmoi.*

- Fix the Mac crontab to match `docs/vault-git-sync.md`:
  - stagger the three jobs;
  - add `2>&1` to the highlights line;
  - add `--retry-timeout 120` to `task reconcile`.

  An empty log is not evidence of success.
- Optional interactive stopgap on athena and apollo:

  ```sh
  bob ref create … && ssh -o BatchMode=yes -o ConnectTimeout=5 mac \
    'PATH="$HOME/bin:$HOME/.cargo/bin:/opt/homebrew/bin:$PATH" bob_xlib_pull'
  ```

  It does nothing useful while the Mac sleeps. Agents' creates still wait for the cron.

### Phase 1 create finishes its own intake

*Scope: bob-cli, medium.*

Add one shared step, e.g. `finish_intake(config, &TargetPlan, opts) -> IntakeOutcome`, under `src/native/highlights_ref/`.

- **Where it's called:**
  - It replaces `print_next_step` for the `Intake` and `Library` workflows.
  - `ingest_url` calls it after a successful clip.
  - `External` output keeps today's `next: bob ref sync …`.
- **What it does, in order** (modeled on `rename/plan.rs`):

1. **Render and stamp outside any lock.** This is unchanged; it's the slow part.
2. **Take the locks.** First `ob::acquire_lock_waiting(bob_sync.lock, ~60 s)`, then `acquire_scan_writer_lock_with_timeout`. This lock order (maintenance before scan) becomes the documented order everywhere.
3. **Pre-sync.** Call `vault_sync::run_cycle_with_existing_lock_report`. If it fails (offline or conflict), **queue** and stop.
4. **Re-check the destination against the freshly pulled tree.**
   - Re-run the stem and occupant check from `plan_default_target`, the intake collision preflight (`plan_xlib_intake` filtered to this source), and a size check below 95 MiB.
   - The stem was chosen before a render that can take minutes. A different reference that took the stem in the meantime means **queue**, not rename (cdx: a rename has to rewrite marker, note, and audio links together).
5. **Plan before moving.**
   - Run `plan_pdf_sync` against the *library destination*, then `ensure_safe_to_write`.
   - A refusal leaves the PDF untouched in `xlib/`.
   - Use canonical absolute paths (see [the relative-path bug](#lead-researcher-findings-that-change-the-picture), `bob-cli-9a`).
6. **Write.** Move the PDF, plus companion audio and sidecars, into `lib/`, then call `execute_pdf_sync`. Note and reading task only; no PDF byte writes.
7. **Post-sync.** Run one more `run_cycle_with_existing_lock_report`, so the PDF, note, and task go out as a single commit. If the push fails, report "ingested; push pending". The background vault-sync retries.
8. **Release the locks and report.**
   - Success: `ingested: ref/<type>/<stem>.md · task → <parent>.md`.
   - Fallback: `queued: xlib/<type>/<stem>.pdf (<reason>) · next: bob ref scan`.
   - The exit code stays 0 either way. `--dry-run` prints the plan and `writes: none`.

**Surface** (checked against `cli_rules.md`; `-k` is unused on `create` today):

- `bob ref create -k, --keep-intake` keeps today's behavior.
- `highlights.ingest_on_create: true` in `config.yml`, plus `BOB_HIGHLIGHTS_INGEST_ON_CREATE=0`, provides a per-host kill switch. The ref-jobs worker and `gkeep pull` read it too.

**Companion audio:**

- When `--listen` audio is part of the request, ingest it in the same locked step.
- If audio is still pending, ingest the PDF and report audio as pending. The drain pairs a late MP3 the same way `scan` does today.
- Never report a requested listen as complete when only the PDF is in.

### Phase 2 close the window in scan and retire the bridge

*Scope: bob-cli + chezmoi, small. Close the window in `scan`, drain locally, retire the bridge.*

- **Make `scan` atomic with vault-sync.**
  - In `scan_library`, acquire `bob_sync.lock` (before `scan.lock`, per the lock order) for any writing scan.
  - Alternatively, at least move intake after planning and hold the lock from the intake move through the last note write.
  - This removes the 24% split commits on the Mac. vault-sync skips a cycle or two during an 8 s scan, which is harmless. ⌘S and cron both benefit.
- **Add `bob ref scan -i, --intake-only`.**
  - It ingests local `xlib/` PDFs through `finish_intake` (pairing late audio), skips the annotation pass, and refuses `-w`.
  - `-i` is unused on `scan`.
- **Add per-host drains.**
  - athena and apollo: a chezmoi-managed systemd user timer runs `bob ref scan -i` (e.g. `OnCalendar=*:0/10` with `Persistent=true`, or `OnBootSec` plus `OnUnitInactiveSec`). Use a timer, not a `.path` unit.
  - The Mac keeps its full `scan -w` schedule for annotations, which also drains its own `xlib/`.
- **Retire `bob_xlib_pull`** (`highlights.pre_scan_hook: ""`) once all three hosts run the new binary.
  - Rule: **each host's `xlib/` has exactly one drainer.**
  - A Mac rsync racing a local intake on the same file would birth two notes.
  - If the bridge must stay during rollout, have it skip files younger than about 2 minutes.
- **Optional:** move the Mac's annotation scan from cron to a chezmoi-managed LaunchAgent with `StartCalendarInterval` (catches up once on wake), stdout and stderr logs, and Apple-signed `/bin/sh` as the program. It matters less once the Mac stops being on the intake path.

### Phase 3 visibility and docs

- `bob ref doctor`:
  - warn when the oldest `xlib/` PDF is older than 1 h (the same threshold as ref-job pending age);
  - show the last scan success and failure.
- Add a `queued` or `ingested` stage to `bob ref jobs` output for capture-originated work.
- Update:
  - `docs/highlights-ref-sync.md` (typical order);
  - `docs/ref.md` ("Choose a command");
  - the Highlights bridge in `docs/vault-git-sync.md`;
  - the scan sentences in `docs/ref-jobs.md`.
- Once accepted, record the invariant as a `decisions` record through `/sase_memory_write`: *references are ingested by the host that creates them, atomically with vault sync; annotation sync stays on the Mac*.

## Acceptance tests

Scratch-vault integration tests, like `tests/cli.rs`, plus a one-time tailnet check. Each item gives the scenario, then its required result:

- **`create` with defaults:** PDF in `lib/`, note written, task filed, `xlib/` empty, one commit. A follow-up `scan` reports `writes: none` (cld C5).
- **`bob_sync.lock` held (`BOB_VAULT_SYNC_LOCK_FILE`, short wait):** `queued: … (lock busy)`, exit 0, PDF intact
- **Pre-sync fails (offline remote):** Queued. `bob ref scan` still ingests locally on demand.
- **Another host took the stem during the render:** Queued with a collision reason. Nothing is overwritten.
- **Library destination occupied by an annotated PDF:** Refused. The annotated copy is untouched.
- **File ≥ 95 MiB:** Queued with a size reason. vault-sync is not wedged.
- **`-k`, config switch, env switch:** Today's output and behavior
- **`--dry-run`:** Plan printed, `writes: none`
- **Process killed after the move, before the note:** Next drain or scan completes it and adopts any task already inserted (the existing v2 adoption behavior)
- **Writing `scan` racing vault-sync on the Mac:** No commit contains a new `lib/` PDF without its note
- **Live: create on athena with the Mac asleep:** Note and task on every host within ~30 s; PDF in Highlights after the Mac wakes and pulls

## Residual risks and open questions

**Risks**

- **Same-stem race.** Pre-sync under the lock shrinks it to about a second between two hosts. If it happens, the existing conflict policy applies (remote wins, local copy kept in `_conflicts/`). If it ever shows up in `_conflicts/sync_conflicts.md`, that is the trigger to revisit cdx's single-publisher design.
- **Lock contention.** `bob nightly` (03:30) holds `bob_sync.lock` for minutes. Creates during that window queue, and the drain picks them up.
- **Parent-note merges.** A reading task inserted on athena while you edit the same parent note in Obsidian on the Mac relies on git's line merge. This exposure already exists for every non-Mac writer (`nightly`, `rename`).
- **Agent commits.** SASE agents running `create` on athena will now make vault commits ([requirement 6](#requirement-adjustments)).

**Open questions for you**

1. Do you ever *want* a PDF to sit unfiled first, for example to preview an agent report? `-k` covers that. If it's common, flip the default.
2. Do you read in Highlights on an iPad or iPhone too? If so, "in the Mac's `lib/`" isn't the only target, and those devices' sync path needs checking.
3. On an offline host, should `create` queue (recommended) or ingest locally and accept a small conflict risk?

## Recommended solution

Don't automate `bob ref scan`. Make `bob ref create` and every other PDF producer **finish their own intake** on the host that rendered the PDF:

- take `bob_sync.lock` and then the scan lock, exactly as `bob ref rename` does;
- pull, re-check the destination, and ingest only that one PDF;
- commit and push the PDF, note, and reading task as one commit.

When that can't happen, leave the PDF queued in local `xlib/` with a visible reason, and let a per-host `bob ref scan --intake-only` timer drain it. In the same change, make writing scans hold `bob_sync.lock` so no commit ever carries a library PDF without its note. Then retire the Mac's cross-host rsync bridge. Keep the Mac's scheduled full scan purely for Highlights annotation sync. Fix its stderr logging today, and use the SSH nudge only as a stopgap until [Phase 1](#phase-1-create-finishes-its-own-intake) ships.

Expected outcome:

- Creates on athena or apollo land on every host within seconds, with the note and task present even while the Mac sleeps.
- Creates on the Mac are readable in Highlights when `create` returns.
- `bob ref scan` becomes a repair tool, not a daily step.

## Report inputs and sources

- **Date:** 2026-10-18
- **Inputs:** four independent reports (cdx, cld, grk, gem), merged with lead-researcher verification against bob-cli `674c9f5`, the live vault history on athena, and read-only checks on the Mac.
- **Question:** `bob ref create` runs on athena, apollo, or the Mac, but the PDF is not usable until `bob ref scan` runs. How should that become automatic and reliable? Is the plan sound?

**Constituent reports** (same directory): `__cdx.md` (athena publisher, launchd/systemd semantics, size limit, acceptance matrix), `__cld.md` (measured latency, scratch-vault constraints C1–C7, ingest at birth), `__grk.md` (scan's two jobs, consumer table, scoped-ingest primitive), `__gem.md` (O(1) vs O(N) framing, create-and-sync flow).

**Lead-researcher verification (2026-10-18)**

- Vault history on athena:
  - lib-PDF add commits by minute mod 15 (114/268 on the cron boundary);
  - PDF-without-note commits (65/268, gap 16–687 s);
  - sample commits `113cbf90` and `0de1c54d`.
- Mac (read-only):
  - `crontab -l`;
  - the `/var/mail/bbugyi` mailbox (empty);
  - `launchctl list` (only `com.bbugyi.bob-vault-sync` plus Bob Mac Capture);
  - `pmset -g` (`womp 0`; Amphetamine holds sleep while open);
  - the vault-sync plist `StartInterval 15`;
  - the lock path `/tmp/bob_sync.lock`.
- athena:
  - `bob-vault-sync.service` (inotify, 15 s timeout, 5 s debounce);
  - the lock path `/run/user/1000/bob_sync.lock`;
  - library sizes (max 19.6 MB).
- bob-cli `674c9f5`:
  - `highlights_ref/{sync.rs (scan_library, sync_pdf), stamp.rs (plan_default_target, print_next_step), io.rs (pdf_path_metadata), guard.rs (ensure_safe_to_write), ingest.rs, create.rs, clip.rs, collection.rs, rename/plan.rs}`;
  - `ob.rs` (`acquire_lock_waiting`, `acquire_lock_quiet_if_held`);
  - `vault_sync.rs` (`run_cycle`, `preflight_one_file`).
- Reproduced bug: `bob ref sync lib/chat/<x>.pdf --dry-run` vs the absolute path (dry run, no writes). Corroborated on `bob-cli-9a`.
- Memory: `tailnet.md`, `obsidian.md`, `cli_rules.md`.
