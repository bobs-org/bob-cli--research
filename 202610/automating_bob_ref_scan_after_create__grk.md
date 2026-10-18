# Automating `bob ref scan` after `bob ref create`

- **Researcher:** grk
- **Date:** 2026-10-18
- **Question:** Bryan runs `bob ref create` on any of the three tailnet machines and cannot use the generated PDF until he also runs `bob ref scan`. How should that second step become automatic, and is “always scan after create” even the right plan?
- **Verdict:** The goal is right. Wiring `create` to a full `bob ref scan` is the wrong plan. Repair the Mac-side drain that is already supposed to do this work, then add a *scoped ingest* of the new PDF so a create can become Highlights-ready in seconds without walking the whole library.

---

## Bottom line

Bryan already designed the missing automation. `create` writes a gitignored intake PDF under `xlib/`. The Mac is the Highlights host. A 15-minute Mac job is supposed to pull `xlib/` off athena and apollo (`bob_xlib_pull`), move those files into `lib/`, and write the `ref/` note (`bob highlights scan -w`). After that, Highlights can open the PDF and `bob ref list` / Obsidian `Cmd+Enter` can see it.

That Mac job is not running. On 2026-10-18, with the Mac awake:

| Job (all `*/15` in the same crontab) | Log mtime |
| --- | --- |
| `maybe_bob_highlights_sync -w` | **2026-09-14 08:30** (0 bytes) |
| `bob projects sync` | 2026-10-18 13:15 |
| `bob task reconcile` | 2026-10-18 13:15 |
| `com.bbugyi.bob-vault-sync` LaunchAgent | 13 269 successful runs; last log 12:17 |

`scan.lock` on the Mac was last touched **2026-10-09**. athena and Mac `xlib/` are both empty *now* because the last successful scan already drained them. New creates sit in `xlib/` until Bryan types `bob ref scan` or presses ⌘S in Bob Refs.

So the inconvenience is real, and the first fix is operational: move the highlights drain onto a LaunchAgent that actually fires (the same transport vault-sync already uses), with `RunAtLoad` so a lid-open drains the mailbox immediately.

After that, still do **not** make `bob ref create` invoke a full library `scan`. `scan` is a 469-PDF Highlights reconciliation with dirty-git refusal, marker write-back, and sidecar reads. athena currently sees **299 PDFs with no sidecar**. A Linux full scan is the wrong writer for that tree. Create should stay an intake producer. A new *single-PDF ingest* (promote this `xlib` file into `lib/`, then `bob ref sync` just that PDF) is the primitive create and the Mac watcher should call.

---

## 1. What “use the PDF” actually requires

`bob ref create` already produces a real, marker-stamped PDF. The file exists. The gap is *membership in the Highlights library and in the Bob reference index*.

Three consumers sit behind `scan`, and they need different things:

| Consumer | Needs the PDF in `lib/` | Needs the `ref/` note | Needs a full library walk |
| --- | --- | --- | --- |
| Highlights.app (`net.highlightsapp.universal`) on the Mac | Yes. It watches `~/bob/lib`, the archived library. | No | No |
| `bob ref list`, Bob Refs, daily REFERENCES review | Yes (`source_pdf` points at `lib/…`) | Yes | No (one new note is enough) |
| Obsidian `Cmd+Enter` via bob-navigation-hotkeys | Yes (opens `source_pdf` in Highlights) | Yes | No |
| Later Highlights annotations flowing back into the note | Yes | Yes | **Yes** — that is what periodic `scan` is for |

Create currently ends with `next: bob ref scan` for every intake or in-library PDF (`print_next_step` in `stamp.rs`). Capture jobs print the same dependency: the PDF is `clipped` in `xlib/`, and “the note appears in `ref list` after `bob ref scan`.” Bob Refs even labels an intake hit `waiting for bob ref scan`.

Two different jobs are jammed into one command:

1. **Intake promotion** — move `xlib/<rel>` → `lib/<rel>` (plus same-stem audio / sidecars) and birth the reference note from the page-1 marker.
2. **Annotation sync** — walk every PDF under `lib/`, read Highlights sidecars, update notes, optionally write markers back (`-w` / `--write-pdfs`).

Bryan’s pain is almost entirely (1). (2) can stay periodic. Treating them as one “run scan after create” step is what makes the plan feel both necessary and dangerous.

---

## 2. How the pipeline works today (verified)

```text
any host                         Mac (Highlights host)
────────                         ─────────────────────
bob ref create ──► ~/bob/xlib/  (gitignored mailbox)
bob capture URL ─► ref job ──► xlib/
bob gkeep pull ──► xlib/ (inline clip)

                 bob_xlib_pull
                 rsync --remove-source-files --ignore-existing
                 athena:bob/xlib/ ──┐
                 apollo:bob/xlib/ ──┴─► Mac ~/bob/xlib/

                 bob highlights scan -w
                   1. pre_scan_hook = bob_xlib_pull
                   2. intake moves xlib → lib
                   3. plan+write every lib PDF into ref/

                 ~/bob/lib/*.pdf  ── git (allowlisted !*.pdf)
                 ~/bob/ref/*.md   ── git
                 vault-sync every 15s on the Mac, inotify on Linux
```

Facts checked against source and live machines on 2026-10-18:

- Default create destination is `~/bob/xlib/<ref-type>/<stem>.pdf`. `--output` inside `lib/` is already a first-class `TargetWorkflow::Library` path; `--output` outside both trees needs `bob ref sync <pdf>` because recursive scan will not discover it.
- `xlib/` is gitignored. `lib/` PDFs, MP3s, and Markdown sidecars *are* tracked (`!*.pdf` in `~/bob/.gitignore`). `git ls-files lib/` is 667 paths on both hosts. The whole library is about 417 MiB on the Mac, 469 PDFs.
- `vault-sync` does `git add -A` and refuses files ≥ 95 MiB (GitHub’s 100 MiB cap). Ordinary article PDFs fit; that is why athena already has the same 469 PDFs as the Mac.
- `bob_xlib_pull` is Darwin-only (exits 0 on Linux). It probes athena and apollo in parallel with `ConnectTimeout=5`, treats SSH exit 255 as “host offline, skip”, drains nonempty queues with `rsync --remove-source-files --ignore-existing`, then runs `bob highlights --no-hooks scan -w` unless it *is* the pre-scan hook. Destination wins collisions; the later source keeps its copy.
- Managed config: `highlights.pre_scan_hook: PATH="$HOME/bin:$PATH" bob_xlib_pull`.
- Mac crontab (live, not the docs recipe):

  ```cron
  */15 * * * * ~/bin/maybe_bob_highlights_sync -w >> /var/tmp/maybe_bob_highlights_sync.log
  */15 * * * * ~/.cargo/bin/bob projects sync >> /var/tmp/bob_projects.log
  */15 * * * * ~/.cargo/bin/bob task reconcile >> /var/tmp/bob_task_status_hooks.log
  ```

  Docs still describe staggered `0,15,30,45` / `5,20,35,50` / `10,25,40,55` lines and a `2>&1` on the highlights job. Live, all three fire on the same minute, and the highlights line has **no** `2>&1`.
- Bob Refs ⌘S runs the same writer: `bob ref scan -w -f json`, 300 s timeout, serialized by `<state>/bob-cli/ref/scan.lock` (120 s wait, then `scan_busy`).
- `bob ref` docs: “The intended automation is a scheduled `scan`, not a live recursive watcher.” That sentence is about watching `lib/` (Highlights writes sidecars there constantly). It is not a veto on watching the `xlib/` mailbox.
- Prior intake research (`research:202610/url_capture_ref_intake_routing`, `research:202610/highlights_listen_intake`) already set the boundary: create stamps a PDF in `xlib/`; the Mac scan writes `ref/`. Capture and listen were told not to auto-run `scan`. That boundary still holds for *full* scan. It does not mean intake promotion has to stay a 15-minute (or manual) afterthought.

`scan` itself is conservative in the ways that make “just call it from create” painful:

- Writing scans take an exclusive `scan.lock`.
- Intake collisions abort the whole run before notes are written.
- Dirty target notes/PDFs refuse the write pass (`dirty_targets`). Intake has already happened by then, so a failed scan can leave PDFs in `lib/` with no note.
- `--write-pdfs` rewrites PDF bytes. The conservative docs say keep that manual; production cron and ⌘S both pass `-w` because v2 parent/status sync needs marker write-back. That is a live policy split, and it is one more reason create should not inherit a full `-w` scan.

---

## 3. Critique of “auto-run `bob ref scan` after create”

### The goal is good

Waiting for a second, easy-to-forget command after an otherwise complete create is bad UX. The PDF is not a draft; it is already stamped. Capture jobs have the same gap. Bryan’s actual want, restated: **a create on any tailnet machine should become a Highlights library PDF and a Bob reference without a second gesture, whenever the Mac can see it.**

### The literal mechanism is a bad idea

**1. Full scan is the wrong width.** Doctor on both hosts today: 469 PDFs, 170 sidecars, 299 missing sidecars, 1072 ref notes. Create needs to ingest one file. `scan` plans every PDF, then `ensure_safe_to_write` over the whole plan. One dirty note or one PDF that needs marker write-back without `-w` can fail the run that was only trying to promote the new article.

**2. Linux is the wrong scan host.** `bob_xlib_pull` is Darwin-only because Highlights, sidecars, and TextBundles live on the Mac. A `create` on athena that shells out to `bob ref scan` would move the PDF into *athena’s* `lib/` and then walk 469 PDFs using athena’s sidecar set (299 missing). Notes are git-synced; a Linux scan that rewrites managed bodies from “no sidecar” would drop Mac annotation content. The Mac-as-library-scanner rule is load-bearing.

**3. Create would inherit scan’s failure modes.** A successful create that then exits 1 because `scan` hit `dirty_targets` / `scan_busy` / `hook_failed` (apollo SSH timeout while athena had the file) teaches Bryan that create is flaky. Intake PDFs would still be in `xlib/` or half-moved. Today create’s contract is: the PDF is in `xlib/`, here is `next: bob ref scan`. That is honest. Coupling them hides the seam until it breaks.

**4. Capture and gkeep would still be broken.** `bob capture '<URL>'` queues a ref job; the worker clips into `xlib/` and never scans (`docs/ref-jobs.md`). `gkeep pull` clips inline the same way. Teaching only `create` to scan leaves the other two producers as manual. The drain belongs at the mailbox, once, for every producer.

**5. Blocking create on scan is slow.** Bob Refs already budgets 300 s for a scan. Web-article create is already 10–150 s. Appending a library walk makes the command feel broken even when it works. Capture research rejected inline clipping for this reason; inline scanning fails the same test.

**6. The Mac-offline bound does not go away.** Highlights runs on the Mac. The Mac is the lid-closed machine (`tailnet.md`). No create-time scan on athena can open Highlights. The honest bound is: **the PDF becomes usable in Highlights once the Mac is awake and has the file in `lib/`.** Automation should make *that* happen without a gesture, including “Mac was asleep at create time.”

### What I would do instead of the literal plan

Keep create as the producer. Make the Mac *react to `xlib/`* (and, for “I want it while I wait,” let create *nudge* the Mac). Give intake promotion its own small command so a new PDF does not have to pass a 469-PDF preflight.

---

## 4. Options

| Option | What it does | Verdict |
| --- | --- | --- |
| **A. `create` shells out to `bob ref scan [-w]`** | Literal request | Reject. Wrong host, wrong width, wrong failure domain. |
| **B. `create --scan` opt-in** | Same as A, hidden behind a flag | Reject as the main path. Bryan would pass it every time, including on athena. |
| **C. Write create output straight into `lib/`** | Skip `xlib/` so Highlights/git see the PDF without intake | Tempting on the Mac. On Linux it git-syncs a library PDF before the Mac scan has birthed the note; also skips the collision/mailbox design. Keep `xlib/` as the staging queue. `--output` into `lib/` already exists for deliberate in-library installs. |
| **D. Add `xlib/` as a second Highlights library folder** | PDF usable before scan | Reject. Scan *moves* the file. Highlights would hold a path that then vanishes. |
| **E. Syncthing / replica of `xlib/`** | Continuous copy instead of queue drain | Reject. `bob_xlib_pull` is a mailbox (`--remove-source-files --ignore-existing`). A replica fights that. |
| **F. Repair the Mac scheduler only** | LaunchAgent running today’s `maybe_bob_highlights_sync -w` | **Do this first.** Highest ROI. Restores the design that is already documented and coded. Still a 15-minute (plus sleep) delay. |
| **G. LaunchAgent + `RunAtLoad` + `WatchPaths`/`QueueDirectories` on `xlib/`** | Drain as soon as the Mac is awake or the mailbox is nonempty | **Do this with F.** This is the reliable automatic path for every producer. |
| **H. Create-time nudge: `ssh mac bob_xlib_pull` (5 s timeout)** | After a Linux create, ask the Mac to pull+scan now; on Darwin, run the pull locally | **Do this as the “I just created it, I want it now” path.** Offline Mac → PDF stays in `xlib/` for G. |
| **I. Scoped ingest: promote *this* PDF, `sync` *this* PDF** | New primitive under `bob ref` | **Build this** so F/G/H do not walk 469 PDFs for one article, and so a dirty unrelated note cannot block the new one. |
| **J. Linux create writes the `ref/` note itself** | Note appears in `bob ref list` before the Mac is awake | Skip for v1. Notes are the Mac scan’s job (sidecar-safe). Git-syncing a note whose `source_pdf` is still on another machine’s `xlib/` is a worse half-state. After I, the note is written on the Mac as soon as the PDF lands in `lib/`. |

F+G+H+I is the set. A/B/D/E are traps. C is already available as `--output` for special cases.

---

## 5. Requirement adjustments

These change the request as stated. Each is load-bearing.

**A1. “Rarely run `bob ref scan` by hand” means rarely run *intake promotion* by hand.** Periodic full scan stays for Highlights sidecar → note sync. ⌘S stays as “sync annotations now.” Success is: new creates show up in Highlights and `bob ref list` without a second command.

**A2. `create` must not invoke a full library `scan`.** Same rule for the capture worker and `gkeep pull`. The drain is host-side and producer-agnostic.

**A3. Only the Mac walks `lib/`.** athena and apollo may write `xlib/`. They must not reconcile Highlights sidecars.

**A4. Accept the Mac-offline bound, and make wake-up drain automatic.** While the lid is closed, Highlights cannot open anything. The mailbox on athena/apollo is the right holding pattern. `RunAtLoad` plus the existing vault-sync LaunchAgent means that when the Mac wakes, `xlib/` is pulled, PDFs land in `lib/`, notes are written, and git catches up — without Bryan typing `scan`.

**A5. Split the primitive.** Today the only way to promote one intake PDF is a whole-library `scan`. Add a scoped ingest (promote + `sync` of named PDFs, default “all pending in `xlib/`”). Full `scan` keeps annotation reconciliation.

**A6. Fix the scheduler before adding create-time magic.** A post-create SSH nudge on top of a dead cron still leaves Mac-asleep creates stuck, and still leaves capture jobs stuck. The LaunchAgent is the backbone; the nudge is latency.

**A7. Keep `-w` off the create-time ingest.** Brand-new PDFs already carry a correct page-1 marker from `create`. Marker write-back is for later annotation/status sync. The 15-minute job may keep `-w` (current production policy). Create-time ingest should be note-only, like the docs’ default `scan` without `--write-pdfs`.

**A8. Cover all three producers.** Any design that only patches `bob ref create` leaves `bob capture '<URL>'` and `gkeep pull` as manual. Watching `xlib/` covers all three.

---

## 6. Recommended solution

Three layers. Ship them in this order. Layer 1 alone may already match “I rarely run scan.” Layers 2 and 3 make it feel immediate.

### Layer 1 — Make the Mac drain real (chezmoi, no bob-cli change)

Replace the dead user-cron highlights line with a LaunchAgent modeled on `com.bbugyi.bob-vault-sync`:

- Label: `com.bbugyi.bob-highlights-scan`
- Program: `/bin/sh -c 'exec /Users/bbugyi/bin/maybe_bob_highlights_sync -w'` (Apple-signed `sh`, so BTM does not alert on every `cargo install`; see `research:202610/macos_bob_background_activity_notification.md`)
- `RunAtLoad: true` — lid-open / login drains `xlib/` immediately
- `StartInterval: 900` — same 15-minute cadence as today’s intent
- `WatchPaths: /Users/bbugyi/bob/xlib` and/or `QueueDirectories` on that tree — local Mac creates (and files that just arrived via rsync) start a drain without waiting for the interval
- `ThrottleInterval` ~15–30 s so a multi-file create does not launch five scans
- stdout/stderr under `/var/tmp/com.bbugyi.bob-highlights-scan.{out,err}` (the current highlights cron line has no `2>&1`, so failures vanish)
- PATH and HOME as in the vault-sync plist (`~/.cargo/bin`, `~/bin`, Homebrew)
- Keep using `maybe_bob_highlights_sync` so the existing `maybe_bob_highlights_sync.lock` still serializes with `bob_xlib_pull`’s inner scan and with ⌘S

Remove the highlights crontab line once the agent’s log mtime advances. Leave `projects sync` and `task reconcile` on cron for now, or stagger them; they *are* firing.

**Acceptance:** after a `bob ref create` on athena with the Mac awake, the PDF is in Mac `lib/` and a `ref/` note exists within one interval (and within seconds if WatchPaths is live), with no manual `scan`. After a create while the Mac is asleep, opening the lid is enough.

This is the same architecture the docs already describe. It is just on a transport that actually runs on this Mac.

### Layer 2 — Scoped ingest (bob-cli)

Add a small Highlights-pipeline command, e.g. `bob ref ingest [PDF…]`, that:

1. Takes `scan.lock` (same lock, same wait).
2. Does **not** run the pre-scan hook unless asked (`--pull` for the Mac agent).
3. Promotes only the named intake PDFs, or every pending `xlib/` PDF if none are named, using the existing `plan_xlib_intake` / `execute_xlib_intake` collision rules restricted to that set.
4. Runs `sync` on just those library destinations, **without** `--write-pdf`.
5. Leaves the other 468 PDFs untouched.

CLI shape (cli_rules.md): nest under `bob ref` in the Highlights pipeline group; give the long options short aliases; keep `scan` as the recursive library walk. Hidden alias unnecessary — this is new.

`bob ref sync` staying “one already-in-library PDF” is fine. Teaching `sync` to silently move out of `xlib/` would change a currently-documented self-heal (“sync an xlib path, scan later rewrites `source_pdf`”) and would make it easier to open an `xlib/` file in Highlights before the move. Prefer an explicit ingest.

Use ingest from:

- the LaunchAgent fast path (WatchPaths → `bob ref ingest --pull`, which pulls then promotes pending)
- a slower hourly `bob ref scan -w` if annotation sync should stay less chatty than today’s every-15-minutes `-w` walk (optional follow-up; not required to solve create)

### Layer 3 — Create-time nudge (latency, all producers)

After a successful intake install, best-effort:

```text
ssh -o BatchMode=yes -o ConnectTimeout=5 -o ConnectionAttempts=1 mac \
  'PATH="$HOME/bin:$HOME/.cargo/bin:/opt/homebrew/bin:$PATH" bob_xlib_pull'
```

On Darwin, skip SSH and run `bob_xlib_pull` (or `bob ref ingest --pull`) in-process / as a sibling. On SSH failure or timeout, print one line: `queued on this host; the Mac will ingest at next wake`. Do not fail create.

Implement as `highlights.post_create_hook` in config (same style as `pre_scan_hook`) so tests can disable it, rather than hardcoding `mac` in Rust. Chezmoi sets it to the SSH nudge on Linux and to `bob_xlib_pull` on Darwin.

Point the capture worker and `gkeep pull` at the same hook after a successful clip. Then every producer shares one nudge.

Create stays fast: the hook is a 5-second SSH. The Mac does the lock, pull, ingest. If a scan is already running, `bob_xlib_pull` sees `maybe_bob_highlights_sync.lock` and exits 0 — “the in-flight scan will pick up our files.”

### What success looks like

| Situation | After this design |
| --- | --- |
| Create on the Mac, Highlights open | WatchPaths / local hook → ingest this PDF → Highlights sees `lib/…` in seconds; note exists; ⌘S unused |
| Create on athena, Mac awake | Nudge SSH → pull → ingest; same as above, plus a few seconds of rsync |
| Create on athena, Mac asleep | PDF waits in athena `xlib/`; lid-open `RunAtLoad` pulls and ingests; no command from Bryan |
| `bob capture '<URL>'` | Worker writes `xlib/`, same nudge/watch path |
| Bryan wants annotation sync now | ⌘S / `bob ref scan -w` unchanged |
| Dirty unrelated ref note | Scoped ingest of the new PDF still succeeds |

Bryan still *can* run `bob ref scan`. He should almost never *need* to for new creates.

---

## 7. Why not promote to `lib/` on the creating host via git?

`lib/` PDFs *do* travel on `vault-sync`. A Linux create that moved `xlib/` → local `lib/` would commit the PDF on athena, and the Mac would receive it on the next pull without `bob_xlib_pull`. Highlights would see the file once the Mac was awake, even if athena were then off.

I would still keep `xlib/` as the create destination:

- Collision checks and listen-audio pairing are intake-stage work; `scan` / ingest is the promotion gate.
- A git commit of a PDF with no note yet is two-phase anyway; rsync of a mailbox is the faster Mac-awake path and does not need a 95 MiB-safe git push before Highlights can open the file.
- `bob_xlib_pull --ignore-existing` plus git-tracked `lib/` would double-deliver if create also wrote `lib/` on Linux.
- Prior research’s Mac-as-note-writer rule stays simpler if the Mac is also the one that first places the file in `lib/`.

Revisit git-side promotion only if LaunchAgent + rsync mailbox proves too weak for Mac-asleep creates (for example if Bryan wants the PDF on the git remote even when the Mac never comes back). That is a different reliability story than “I hate typing scan.”

---

## 8. Risks and open questions

**Risks**

- WatchPaths on `xlib/` can fire on attribute changes. `ThrottleInterval` plus the existing scan lock are the mitigation; do not WatchPaths `lib/`.
- `bob_xlib_pull` still waits on the slower of {athena, apollo} SSH. A lid-open with apollo down costs one 5 s timeout today (exit 255 is skip). Keep that.
- Scoped ingest plus a concurrent full `scan -w` from ⌘S will serialize on `scan.lock`. 120 s wait is already implemented.
- Layer 3’s SSH from apollo to the Mac will often time out; that is expected. Mailbox + RunAtLoad covers it.
- Production `scan -w` every 15 minutes on 469 PDFs is heavier than intake needs. After Layer 2, consider slowing full `-w` scan to hourly and letting ingest handle the mailbox. Out of scope for the first patch.

**Open questions for Bryan**

1. When you say you cannot *use* the PDF, is the blocking consumer Highlights (file not in `lib/`), or the Bob note (`ref list` / `Cmd+Enter`)? The recommendation covers both; if it is only Highlights, Layer 1 + promote-without-note would be enough and notes could wait.
2. Is “within 15 minutes while the Mac is awake” acceptable once the scheduler works, or do you want the create-time SSH nudge in v1?
3. Should the first LaunchAgent keep `scan -w` (current cron intent) or switch to ingest-without-`-w` plus a rarer full scan?

---

## 9. Evidence (2026-10-18)

Live, read-only:

- athena `hostname` = athena; Mac `Kellys-MacBook-Pro.local` reachable over Tailscale.
- `~/bob/xlib` pending files: 0 on both hosts.
- `bob ref doctor --no-hooks`: `pdf_count: 469`, `sidecars_found: 170`, `sidecars_missing: 299`, `xlib_pending: 0`, `library: 1072 notes`, git clean. Same sidecar counts on the Mac.
- `git -C ~/bob check-ignore -v xlib` → `.gitignore:46:xlib/`; `lib` is not ignored. `git ls-files lib/ | wc -l` → 667.
- Mac crontab as quoted above. Highlights log `stat`: `Sep 14 08:30:00 2026`, size 0, flags none. Sibling cron logs written at 13:15 today. `scan.lock` mtime Oct 9 14:00. `/usr/sbin/cron` running. Highlights.app id `net.highlightsapp.universal`.
- `maybe_bob_highlights_sync` and `bob_xlib_pull` present under `~/bin` on the Mac (chezmoi).
- Vault-sync LaunchAgent `runs = 13269`, `last exit code = 0`.

Code and docs: `docs/highlights-ref-sync.md` (scheduled scan, intake, lock), `docs/vault-git-sync.md` (Highlights bridge), `docs/ref-jobs.md` (capture does not scan), `docs/ref.md` (⌘S), `src/native/highlights_ref/{sync,stamp,hooks,doctor}.rs`, chezmoi `home/bin/executable_{bob_xlib_pull,maybe_bob_highlights_sync}`, `home/Library/LaunchAgents/com.bbugyi.bob-vault-sync.plist`, `home/dot_config/bob/config.yml`.

---

## 10. Recommendation, one paragraph

Do not teach `bob ref create` to run `bob ref scan`. Restore the Mac drain that is already designed — a LaunchAgent with `RunAtLoad`, a 15-minute interval, and a watch on `~/bob/xlib` — because the current cron line has not started since 2026-09-14 while every sibling job still runs. Then add `bob ref ingest` so promotion of a new PDF does not walk 469 files, and a 5-second post-create nudge to `bob_xlib_pull` on the Mac so an attended create becomes Highlights-ready immediately when the laptop is open. Full `scan -w` remains the annotation reconciler and the ⌘S gesture, not the create epilogue.
