# Athena Plex breach: what was exposed, was root reached, and what the plan misses

Research date: 2026-10-17, live checks 07:43–09:45 EDT, run as `bryan` on athena (no root).
This report complements the response plan `202610/athena_plex_compromise_response.md` in the
plans sidecar (there is no file named `plex_miner_incident_response.md`; the Athena plan is the
Plex-miner plan). No secret values appear here. The per-account rotation list is kept
**privately** on apollo at `~/incidents/athena-20261017/exposed-credentials-checklist.md`
(mode 600), because this repository is public.

## Bottom line

- **Who and how long.** The attacker ran code as the `plex` user (uid 998) from 01:48 until
  Gate A stopped Plex at about 07:55 EDT. `plex` could read anything world-readable on
  athena, and `/home/bryan` is `755`.
- **Confirmed stolen:** only the Plex owner token for `bryanb87`. Everything else below was
  _readable_ by the attacker. No logs show whether it was read, so treat it as leaked.
- **Password store: the store itself is safe, but many of its passwords leaked anyway.**
  - The GPG private key was unreadable, so the store's encrypted files could not be decrypted.
  - However, **95 pass entries have their password sitting in plain text** in world-readable
    files: shell-history archives, AI-agent transcripts, vim undo files, and similar.
  - One of them is **your current athena login/sudo password** (checked against PAM).
- **Root access: no evidence of it, but not ruled out.**
  - Gate A's root tripwires are clean.
  - Its log checks could not see the breach window: athena's systemd journal now starts at 08:02.
  - The attacker could read your sudo password, and `su bryan` → `sudo` (or the `docker`
    group) is a working path to root. `/var/log/auth.log` still covers the window and decides it.

## 1. Which credentials were exposed

| Credential | Where `plex` could read it | Status |
| --- | --- | --- |
| Plex account token (`bryanb87`) | Leaked by the SSRF exploit, then used over the WAN | **Stolen.** The plan handles it. |
| athena login/sudo password (+ ~11 other accounts reusing it) | 5 Gemini Antigravity transcripts, 2 shell-history archive logs, IPython history | **Current. Rotate now.** |
| Google account (`bryanbugyi34@gmail.com`) | Gmail password in `~/.mutt/passwd`; Google Keep master token in the shell-history archive; a `gog` OAuth refresh token in an Antigravity transcript | Live: rotate |
| Router admin password (192.168.1.1) | `~/.mcfly/history.db`, shell-history archive | Live. The attacker was inside the LAN. |
| Gemini API key (`AIza…`, not in pass) | Environment dumps in ~43 Codex/muse transcripts | Live: rotate |
| Anthropic API key (`primaryApiKey`, not in pass) | `~/.claude.json.backup` (644) | Live: revoke |
| Alibaba/Qwen API key | `~/.qwen/settings.json` (+ `.orig`), Codex transcripts, shell history | Live: rotate |
| GitHub `gh` CLI token; GitHub password (reused) | muse transcript; see the reused password above | Live: rotate |
| OpenAI keys (2), Zotero key, Codecov token | `zorg/.aider.chat.history.md`, an Auto-GPT `.env`, a 2024 sandbox script, shell history | Rotate if still valid |
| Brokerage 2FA backup code | One Codex transcript | Regenerate |
| Transmission RPC credentials | `/etc/transmission-daemon/settings.json`, readable via the `debian-transmission` group | Rotate |
| ~60 older website passwords (≈5 reused passwords) | Shell-history archive (2018–2021), vim undo, a 2019 DD-WRT backup | Rotate any still in use |
| Old employer credentials, 2018 Slack tokens, 2018 taskd key, 2021 GHE `hub` token | vim undo, shell history, `~/.config/hub`, `~/db/home/.task` | Probably dead: confirm |

**Not exposed** (directory `700` or file `600`):

- `~/.ssh` keys and the GPG private key (`~/.gnupg`)
- `gh` `hosts.yml`
- Claude, Codex, and Gemini OAuth credential files
- `.netrc`, `.git-credentials`, `.pgpass`, Docker config
- browser profiles
- Tailscale state, PIA account, `/etc/shadow`, `~/.vnc/passwd`, `~/.Xauthority`
- `~/.taxes.gpg`: readable, but public-key encrypted, so safe.

Scope of the scan: 2.3 M world-readable files under `~`, `/tmp`, `/etc`, `/opt`, and the
Plex media share. A file counted as readable only if every parent directory was `o+x`
and the file itself was `o+r`.

## 2. Password store specifically

- **Store contents: safe.**
  - `~/.gnupg` and the gpg-agent socket directory are `700`, so the attacker could not decrypt.
  - They could copy the 37 world-readable `.gpg` files and list entry names in the 42
    traversable (`755`/`775`) store directories. That leaks metadata only.
  - chezmoi never renders pass secrets into files.
- **Plaintext copies: leaked.** Each entry was decrypted in memory and searched for
  verbatim. Result: **95 of 267 entries** appear in world-readable files. Four more hits
  were labels or usernames, not passwords. The 95 collapse into about 7 reused passwords.
  The plaintext lives in:
  - `~/db/var/logs/shell-history/` (archived shell history)
  - `~/.codex/sessions`, `~/.gemini/antigravity-cli`, `~/.local/share/muse` (agent transcripts)
  - `~/.vim/undo`, `~/.mcfly/history.db`, `~/db/home/.ipython`
  - `~/.mutt/passwd`, `~/.config/hub`, `~/.qwen/settings.json`
  - a DD-WRT backup in `~/db/var/backup/`
- **Command lines.** `$(pass show …)` aliases (`grip`, `bbssh`, `gpr`) put secrets on
  command lines. Every user can read those, because `/proc` has no `hidepid`. That only
  mattered if one of them ran during the window.

## 3. Did the attacker get root?

**Verdict: no evidence of root, but not ruled out until `/var/log/auth.log` is checked.**

- **Against root:**
  - Every attacker process ran as uid 998.
  - Gate A (07:52–07:58) found no tampered package files (`dpkg --verify` shows only config
    files) and no new SUID files beyond package updates.
  - No `ld.so.preload`, no `plex` crontab.
  - `passwd`/`shadow`/`sudoers`/`authorized_keys` were last changed before the incident.
  - No `plex`-owned files exist outside the Plex tree and `/tmp`, and no odd root processes.
  - The kernel is current (6.12.111, built 2026-09-28).
- **Gaps:**
  1. **Gate A's journal checks were blind.** Its `su`/`sudo`/`pkexec`/kernel/ssh files
     say "No entries" because the journal now starts at 08:02. sshd runs at
     `LogLevel DEBUG3` and flooded the journal, rotating the window out.
     `/var/log/auth.log` (rsyslog, root:adm) still covers 01:48–08:00 and has not been checked.
  2. **Your current sudo password was readable.** With it, `plex` could `su bryan`, then
     `sudo` or use `docker` (you are in the `docker` group). SSH needs a public key, so the
     password alone does not allow SSH logins.
  3. The `/mnt/hercules` sweep for `plex`-owned files timed out (incomplete).

## 4. Manual steps the plan does not cover

The plan already handles: the Plex account, UPnP and port forwards, patching, the firewall
guard, home-directory permissions, apollo's sshd logs, and the apt source. Its Step 5
secret sweep matches file names and token patterns, and skips bulky caches. It will miss
most of the plaintext passwords and transcript-embedded keys above. Do these yourself:

1. **Settle the root question.** Run
   `sudo grep -aE ' (su|sudo|pkexec|polkitd|unix_chkpwd)(\[|:)' /var/log/auth.log` for
   2026-10-17 01:48–08:00. Also check `/var/log/syslog` and `kern.log` for oopses. Any
   `su`, `sudo`, or `pkexec` activity in that window that is not yours means rebuild.
   - The `unix_chkpwd` check for `bryan` at about 09:30–09:40 is this research (one
     failure, then one success).
2. **Change your athena login/sudo password now.** Then change it on every account that
   shares it (see the private checklist).
3. **Google account.**
   - Change the password. This also kills the Keep master token and Gmail-scoped OAuth tokens.
   - Sign out other sessions and review recent security activity.
   - Remove third-party access you don't recognize, and re-authorize `gog`.
   - Delete `~/.mutt/passwd`. The mutt hooks already use `pass`.
4. **Router.** Change the admin password. Check the DNS servers, remote administration,
   and firmware, and look for unknown devices or DHCP reservations.
5. **Revoke and reissue keys and tokens:**
   - Gemini, Anthropic, Alibaba/Qwen, OpenAI, Zotero, and Codecov keys
   - the GitHub `gh` token (and review GitHub's security log)
   - brokerage 2FA backup codes
   - Transmission RPC password
   - Confirm the old SASE Telegram bot token is dead. The leaked value differs from
     today's pass entry, so it was probably already rotated.
6. **Rotate the remaining reused passwords** (mostly 2018-era sites). Do finance, health,
   and email first. Confirm the old employer credentials are dead.
7. **Purge plaintext copies.** Locking `~` to `750` stops other local users, but the
   copies remain, and `~/db` and `Sync/` may sync elsewhere. Delete or `chmod 700` these:
   - the shell-history archive, `~/.mcfly`, `~/.vim/undo`
   - the transcript directories (`~/.codex/sessions`, `~/.gemini`, `~/.local/share/muse`)
   - `~/.claude.json.backup`, `~/.config/hub`, the IPython history, and the DD-WRT backup
8. **Optional hardening.**
   - Mount `/proc` with `hidepid=invisible`.
   - Return sshd to `LogLevel INFO` so logs stop rotating out within an hour.
   - Treat `docker` group membership as root.
   - Set `~/.password-store` subdirectories to `700`.

## Method notes

- All checks ran as `bryan` without root, plus read-only use of Gate A's redacted triage
  copy in `~/ir-athena-20261017/`.
- **Pass check:** entries were decrypted only through the already-unlocked agent
  (`--pinentry-mode error`), matched with `grep -F` from a `700` tmpfs file, then
  discarded. Only entry names were recorded.
- **Other secret patterns:** compared by `sha256` fingerprint, so no values were displayed.
- **Login password:** checked once against PAM with `unix_chkpwd` over stdin.
- **One handling slip:** after containment, four non-secret label lines from pass were
  briefly passed as process arguments on athena.
- All temporary files on athena and apollo were removed.
