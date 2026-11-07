# Managing crontabs via chezmoi: research and recommendation

Researcher: mus (independent swarm report). All live-system claims below were
verified by the author on 2026-11-07 from athena unless marked otherwise.

## Summary

The plan — one checked-in crontab source in the chezmoi repo, applied per
machine by `chezmoi update -a`, with agent-friendly read/write from any
machine — is sound and worth building. The core mechanism exists in the repo
already (`{{ if eq .chezmoi.hostname ... }}` templating plus
`run_onchange_after_*` installer scripts). The main work is handling four
things the original sketch glosses over: crontab is a database, not a file;
one live crontab line is ephemeral and must not be captured; macOS cron is
deprecated in favor of launchd; and "agents can write crontab" needs a
documented contract, not just SSH access. Details and a concrete recommended
layout are below.

## Current state (verified)

- This session runs on **athena** (Debian 13, `chezmoi v2.13.1` via nix,
  source dir `~/.local/share/chezmoi`, `.chezmoiroot` = `home/`).
- `crontab -l` on athena today contains: boilerplate comments, four env vars
  (`DISPLAY`, `DBUS_SESSION_BUS_ADDRESS`, `HOME`, `MAILTO`, `XDG_RUNTIME_DIR`
  — actually five), two commented-out jobs (`tman`, `init-bg`), and three live
  jobs: `bob nightly` (03:30), `pass_git_sync` (hourly), and one
  `sase-epic-watchdog` line. **That watchdog line is ephemeral agent
  infrastructure and must be excluded from any checked-in source.**
- `ssh apollo 'crontab -l'` (BatchMode, tested): `no crontab for bryan`.
  Apollo (Ubuntu 6.8) has `cron`, `crontab`, and working `systemd --user`
  timers (`bob-ref-intake.timer` active). So apollo is a clean, low-risk pilot
  target.
- `ssh mac` (alias for `kellys-macbook-pro.tail297af1.ts.net`): **timed out**
  during this session (tailscale showed it offline / relay, last seen ~6 min
  prior). No mac crontab contents could be verified. The mac's chezmoi
  hostname is the awkward `Kellys-MacBook-Pro` (confirmed in repo templates);
  `mac` is only an ssh alias.
- Chezmoi repo already manages a macOS launchd agent
  (`Library/LaunchAgents/com.bbugyi.bob-vault-sync.plist`, 15s vault sync)
  and Linux systemd user timers (`bob-ref-intake`, `poseidon-cache-watch`)
  via `.chezmoiscripts/run_onchange_after_*` scripts. The pattern to copy is
  `run_onchange_after_enable_bob_ref_intake_timer.sh.tmpl`: template-guarded
  by hostname/OS, hash-comments of the managed files embedded so content
  changes re-trigger, `set -eu` body that enforces target state.
- Legacy context: `~/Sync/bin/cron.jobs/` still exists on athena
  (`jobs.sh`, `cron.{hourly,daily,weekly,monthly}/`, `backup.sh`) with
  `vcron`-style aliases pointing at it. Whatever the new system is, it should
  either absorb or explicitly retire that directory to avoid two sources of
  scheduling truth.

## Critique of the plan

**Verdict: good idea, with adjustments.** Version-controlled, reviewed,
per-machine cron state plus a uniform agent interface is strictly better than
today's `crontab -e` on two machines with no shared record. The "only
machine-specific part is the machine name" instinct is also right — it maps
directly onto chezmoi's `.chezmoi.hostname` templating, which this repo
already uses in ~10 places.

Gaps and risks in the plan as stated:

1. **Chezmoi manages files; crontab is not a file.** Checking in a config
   file alone changes nothing until something runs `crontab <file>`. The
   missing piece is a `run_onchange_after_*` installer script (the standard
   chezmoi idiom, confirmed against upstream docs and this repo's own timer
   scripts). `chezmoi update -a` then works exactly as the user expects:
   pull, render per-host template, detect content change by hash, install.
   This is a small addition, not a redesign.
2. **Full-overwrite vs. merge.** The naive installer (`crontab rendered`)
   destroys anything not in source — including the live sase watchdog line
   and any future ephemeral entries. Two options: (a) full ownership with a
   documented "never `crontab -e`" rule plus a drift check; (b) marker-block
   merge (`# BEGIN CHEZMOI-MANAGED` … `# END`), preserving outside lines.
   I recommend (a): merges silently bless drift and complicate agents'
   mental model; the watchdog should move to a `CRON_PRESERVE_PATTERN`
   allowlist only if it must survive (better: watchdog installers should
   re-install their own line, independent of chezmoi).
3. **macOS: cron vs. launchd.** `cron` still ships and runs on macOS but is
   officially deprecated; `launchd` agents are the native scheduler and the
   repo already manages one. A single crontab source applied everywhere is
   still defensible — uniformity beats native-ness for three personal
   machines, and cron semantics (five-field lines) are the lingua franca
   agents already understand. But the report should record this as a
   conscious tradeoff (see adjustments), with a named reopen condition
   (Apple removes cron).
4. **Agent access is already possible; what is missing is a contract.**
   Verified this session: agents on athena can run `crontab -l` directly and
   reach apollo over BatchMode tailscale SSH (`ssh apollo 'crontab -l'`
   succeeded). So "make sure agents have support" does not mean provisioning
   credentials — it means checking in one wrapper + documenting it where
   agents look (repo `AGENTS.md`/memory + `~/bin`), so that from any machine
   every agent does the same thing: **read via wrapper, write only by
   editing the chezmoi source, never by `crontab` or `ssh … crontab`
   directly.** Direct remote `crontab` writes must be forbidden by the
   contract or the source stops being the source of truth.
5. **Hostname fragility.** `.chezmoi.hostname` values are `athena`,
   `apollo`, `Kellys-MacBook-Pro` — the last is rename-hostile (caps,
   dashes) and differs from the ssh alias (`mac`) agents will naturally
   type. The wrapper must map friendly names (`mac`) to both ssh targets
   and chezmoi hostnames, and templates should isolate the ugly string in
   one place.
6. **Cron's minimal environment.** Every job needs the `. $HOME/.profile`
   preamble (already the convention in the live crontab) and explicit
   `MAILTO`/logging paths. The template should enforce this structurally
   (shared header include), not rely on each contributor remembering.
7. **No secrets in the source.** `crontab -l` output is world-readable on
   the machine and the repo is shared context for many agents. Secrets go in
   existing chezmoi/gpg-managed files or env files referenced by path, never
   inline. The repo already uses `encryption = "gpg"` for genuinely
   sensitive files — cron lines stay plaintext and secret-free.

## Alternatives considered

| Option | Upside | Downside | Judgment |
|---|---|---|---|
| Chosen: one crontab template + installer script | Uniform, tiny, agent-legible, matches repo idioms | Non-native on mac; drift possible | Recommended |
| Systemd timers (Linux) + launchd (mac) | Native, logging, already partially built | Two systems, N files per job, mac launchd editing is agent-hostile XML | Reject for cron-type jobs; keep for sub-minute/daemonish work |
| `/etc/cron.d` fragments | File-native, no installer | Needs root, not per-user, mac lacks it | Reject |
| Daemon runner (supercronic etc.) | File-native, portable | New dependency on all machines, no real need | Reject |
| Status quo (`crontab -e` + notes) | Zero work | No history, no sharing, agent-opaque | Reject |

## Requirement adjustments (explicit)

1. **Add an installer script to the requirements.** A checked-in crontab
   file without a `run_onchange_after_*` applier is a dead letter. The
   deliverable is file + installer + verifier, not the file alone.
2. **Declare full ownership, excluding one ephemeral line.** Source owns the
   whole user crontab; the sase watchdog line is out of scope and its
   installer must tolerate periodic removal (or be allowlisted explicitly).
3. **Record the cron-on-macOS tradeoff in writing** (one paragraph in the
   repo), with reopen condition "Apple removes cron or a job needs
   launchd-only features (e.g. calendar-interval wake-from-sleep)".
4. **Agent write path is source-edit only.** Adjust "easy ability to
   read/write my crontab" to: easy ability to *read* any machine's live
   crontab and *propose/land* changes through the chezmoi source, from any
   machine. Direct `crontab` writes (local or over ssh) are out of bounds
   except during the initial migration and documented break-glass.
5. **Canonical host map.** Friendly name ↔ ssh target ↔ chezmoi hostname
   mapping lives in exactly one checked-in place consumed by both templates
   and the wrapper (`mac → Kellys-MacBook-Pro` today).
6. **Retire or absorb `~/Sync/bin/cron.jobs/`.** State its fate in the plan
   so two schedulers do not coexist silently.

## Recommended solution

- **Source:** one template, e.g. `home/dot_config/cron/crontab.tmpl`,
  with a shared env/header include and per-host blocks:
  `{{ if eq .chezmoi.hostname "athena" }}…{{ end }}`,
  `{{ if eq .chezmoi.hostname "apollo" }}`,
  `{{ if eq .chezmoi.hostname "Kellys-MacBook-Pro" }}` (mac). One new host
  = one new block; nothing else branches.
- **Applier:** `home/.chezmoiscripts/run_onchange_after_apply_crontab.sh.tmpl`
  (unguarded — every host installs its own rendering; or host-guarded during
  rollout). Body embeds `{{ include "<crontab template>" | sha256sum }}` so
  any source change re-runs; `set -eu`; `crontab` the rendered file;
  `crontab -l` verification echoed to apply output. Idempotent by
  construction (chezmoi hashes the script including the embedded checksum).
- **Agent interface:** one checked-in executable, e.g.
  `home/bin/executable_cron-ctl`, subcommands `get [--host H]`, `diff
  [--host H]`, `status [--host H]`, `edit` (opens source, never live state).
  Reads use `crontab -l` locally / `ssh <target> crontab -l` remotely;
  `diff` compares live vs. `chezmoi cat <template>` rendering; writes happen
  only via source edit + `chezmoi apply` (local) or "land source, then run
  `chezmoi update -a` on target" (remote). Document it in the chezmoi
  `AGENTS.md` core memory and the shared agent docs so every provider's
  agents find it.
- **Drift handling:** `cron-ctl status` (live-vs-rendered diff) run
  manually and, optionally, as a daily cron job itself that mails on
  mismatch; `chezmoi verify` as a second opinion.
- **Rollout:** migrate athena's three live jobs into the template first;
  pilot `apply` on apollo (empty crontab — nothing to clobber, verifies the
  installer end to end); then athena; then mac when reachable over
  tailscale. Keep commented-out `tman`/`init-bg` lines as comments in source
  (history preserved) or drop them with a note — decide at migration time.
- **Security posture:** no change to SSH posture required (tailscale +
  existing keys already suffice, as verified); no secrets in cron source;
  installer runs as the user, never root; break-glass `crontab -e` allowed
  only with a same-day source sync, flagged by the drift check.
