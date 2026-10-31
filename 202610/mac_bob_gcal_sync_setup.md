# Mac: make `bob gcal sync` work like it does on athena

Research date: 2026-10-31. Evidence comes from read-only checks on athena and on the
MacBook over SSH (`ssh mac`), the bob-cli source and docs, the chezmoi source repo, and
the bob-plugins source. Nothing on the Mac or in any repo was changed.

## TL;DR

- **What is missing (confirmed):** the Mac has never signed in to Google Calendar.
  `bob`, `gog`, the `bob-gcal` OAuth client, the default root, today's note, and the
  journal git rules are all ready. But gog holds **no Google account or token** on the
  Mac, so sync stops with `not_logged_in`. That happened today at 07:44:05. Athena
  synced the same note 16 seconds later.
- **Fix:** sit at the Mac (not over SSH), open a terminal, and run:

  ```bash
  bob gcal login -a bryanbugyi34@gmail.com
  bob gcal doctor
  bob gcal sync -d
  bob gcal sync
  ```

  The Mac already stores the same `bob-gcal` client that athena uses (Google Cloud
  project `780286831122`). Login skips client setup, opens the browser, and asks only
  for read-only Calendar access.
- **Then clean up:** run `chezmoi update` on the Mac. This deletes the retired
  `com.bbugyi.bob-gcal-sync` LaunchAgent plist. The plist is still on disk, and macOS
  would load it at your next login.
- **Pinning one writer is optional, and the label in the config comment is wrong.** The
  commented `gcal:` block in `~/.config/bob/config.yml` says
  `writer: kellys-macbook-pro`. Bob calls the Mac **`kellys-macbook-pro-local`**. On
  some days it calls it **`kellys-mbp`**, because the Mac's hostname is not fixed. If you
  pin the writer before fixing the hostname, sync will fail on the Mac on alternate days.
  See [Optional: make the Mac the only writer](#optional-make-the-mac-the-only-writer).

## How athena and the Mac compare today

Both columns come from `bob gcal doctor` and direct probes run on 2026-10-31.

| Check | athena (works) | Mac (fails) |
| --- | --- | --- |
| `bob` | 0.4.0, `~/.cargo/bin/bob` | 0.4.0, `~/.cargo/bin/bob` |
| `gog` (needs ≥ v0.44.0) | v0.44.0, `~/bin/gog` | v0.47.1, `~/bin/gog` |
| gog config dir | `~/.config/gogcli` | `~/.config/gogcli` (only because `XDG_CONFIG_HOME` is set; see [pitfall 4](#4-launch-environment-xdg_config_home-and-path)) |
| gog keyring backend | `file` (set in gog's `config.json`) | `auto`, which means macOS Keychain |
| `bob-gcal` client | ✓ project 780286831122 | ✓ project 780286831122 (stored 2026-10-30 12:32) |
| `bob-gcal` account and token | ✓ `bryanbugyi34@gmail.com`, `calendar.readonly` | ✗ **none** (`gog auth list` → `[]`, both buckets) |
| Token refresh, calendars | ✓ refreshes, `primary` reachable | skipped: no account |
| Default root, today's note, journal rules | ✓ | ✓ |
| `writer` check | `athena` · no writer pin | `kellys-macbook-pro-local` · no writer pin |
| Last sync (host-local `status.json`) | 07:44:21 · `written` · +1 task | 07:44:05 · `error` · `not_logged_in: no Google account is configured` |
| `gcal:` block in `~/.config/bob/config.yml` | commented out, so defaults apply | commented out, so defaults apply (same chezmoi file) |

Neither host needs config changes for sync to work. With no `gcal:` block, Bob uses
`calendars: [primary]` and `root: meet`, and allows sync on any host. It takes the
account from the only `bob-gcal` account gog holds. On athena that account exists. On the
Mac it does not.

## Steps

### 1. Sign in on the Mac itself

Use a terminal on the Mac (kitty), not an SSH session from athena:

```bash
bob gcal login -a bryanbugyi34@gmail.com
```

What to expect:

1. **Google client:** `✓ bob-gcal · project 780286831122`. No Cloud Console steps, since
   the client is already stored in `~/.config/gogcli/credentials-bob-gcal.json`.
2. **Sign in:** macOS always counts as a desktop session, so Bob opens the browser.
   Choose `bryanbugyi34@gmail.com` and allow "See and download any calendar you can
   access". If you see "Google hasn't verified this app", click Advanced → Go to ….
   I could not confirm that the consent screen is published. Athena's grant dates from
   2026-10-30T17:46Z, which is still inside Google's 7-day Testing limit. If either host
   hits `invalid_grant` around 2026-11-06, publish the screen (Audience → In
   production) and run `bob gcal login` again.
3. **Check:** `✓ N calendars · syncing 1: primary`.

Why `-a`: with no account in either gog bucket, login stops at a
`Number or email ›` prompt. Passing `-a` skips it. Use the same address as athena. Today's
`## Events` stamp already names `bryanbugyi34@gmail.com`. A different account would make
sync refuse the day with `account_changed` (exit 2).

Why not over SSH: from SSH, Bob switches to the paste-URL flow (`SSH_CONNECTION` /
`SSH_TTY`). gog's `auto` keyring on macOS stores the refresh token in the login
Keychain. A read-only Keychain probe over SSH returned `User interaction is not allowed`,
so a token write from SSH may fail. A paste-flow login on 2026-10-30 12:32 stored the
client but left only an `oauth-manual-state-*.json` file and no token. That fits an
abandoned or failed SSH sign-in. The leftover file is harmless.

If macOS later shows "gog wants to use your confidential information stored in …",
choose **Always Allow**. gog is Developer ID signed, and `gog auth doctor` reports
`keychain.trust application trust enabled`, so this should not normally appear. If it
does appear during an Obsidian-triggered sync, the sync hangs until its 30-second
timeout.

### 2. Verify

```bash
bob gcal doctor          # every check ✓; "account" and "token" now pass
bob gcal sync -d         # preview: today's note is already synced by athena
bob gcal sync            # first Mac write
bob gcal doctor          # "last sync" goes green with this host's label
```

Expect today's first Mac sync to change little: usually just the `↻ synced HH:MM` stamp,
because every run at a new minute rewrites it. Bob reads every host's journal
(`.bob/gcal/*.jsonl`), so the Mac picks up athena's rows, links, and tombstones from
`athena.jsonl` and will not add them again. The Mac then appends to its own
`.bob/gcal/<host>.jsonl`. Vault-sync commits the note and the journal as usual.

### 3. Remove the stale LaunchAgent

```bash
chezmoi update
```

chezmoi commit `fd96796e` ("retire the unused bob-gcal-sync LaunchAgent", today) deleted
the plist from the source and added it to `.chezmoiremove`. The Mac has not applied that
yet: `~/Library/LaunchAgents/com.bbugyi.bob-gcal-sync.plist` (from 2026-10-30 09:31) is
still there. `launchctl print gui/503/com.bbugyi.bob-gcal-sync` shows it is not loaded,
because the Mac has been up for 23 days. macOS loads every plist in that folder at
login, though. If it loads, it runs `bob gcal sync -q` every 5 minutes without
`XDG_CONFIG_HOME`, so gog looks in the wrong config dir (pitfall 4) and every run fails.
If it ever found a token, it would rewrite the stamp, and so commit today's note, every
5 minutes.

### 4. How sync runs once it works

Once you are signed in, the Mac syncs the same ways athena does, with no scheduler:

- **On demand:** `bob gcal sync` (or `-D tomorrow`) in a terminal, or the `gcal-sync`
  run in Bob Command Mode (`Calendar · +2 tasks, +1 context, MEET +2 links`).
- **On note creation:** Bob Ledger Tools runs `bob gcal sync -q -f json` once, when
  today's daily note appears and has `## Pomodoros` (it waits up to 15 s). This is on by
  default (session toggle: "Toggle Google Calendar sync on daily-note creation"). Setup
  and writer errors (exit 2) go only to the developer console. Runtime failures (exit 1)
  show one Notice per day.

There is no periodic sync on either host. Invitations accepted later in the day appear on
the next run.

## Optional: make the Mac the only writer

The accepted decision `bob-gcal-is-read-only-and-proposes-once` says "the Mac is the
single writer". `docs/gcal.md` § Where it runs explains why. Templater creates daily
notes on the Mac. If another host writes today's note while you edit it there,
vault-sync's remote-wins conflict policy can set aside your live ledger edits. Right now
neither host is pinned, and athena has been the de facto writer (`athena.jsonl` entries
on 10-30 and 10-31). After step 2 works, choose one:

- **Leave it unpinned.** Both hosts can sync. This is fine if you run sync on only one
  host at a time.
- **Pin the Mac.** Uncomment the `gcal:` block in the chezmoi source
  `home/dot_config/bob/config.yml` and run `chezmoi apply` on both hosts. Athena then
  refuses `sync` with exit 2 (`this host is athena; gcal.writer is …`). `list`,
  `calendars`, `doctor`, and `sync -d` still work there.

Before pinning, fix two problems:

1. **Use the right label.** Bob takes the host label from `$HOSTNAME`, then from
   `hostname`. It lowercases the name and turns other characters into `-`
   (`vault_sync::hostname_slug`). On the Mac, `hostname` is `Kellys-MacBook-Pro.local`, so
   the label is `kellys-macbook-pro-local`. The comment's `kellys-macbook-pro` is the
   Tailscale name and would never match. `bob gcal doctor` prints the label in its
   header.
2. **Fix the Mac's hostname first.** `scutil --get HostName` returns `not set`, so macOS
   picks the hostname from the network. Vault-sync commit subjects show the label
   switching almost daily:

   | From | To | Label |
   | --- | --- | --- |
   | 10-28 06:17 | 10-28 12:30 | `kellys-mbp` |
   | 10-28 13:37 | 10-29 20:29 | `kellys-macbook-pro-local` |
   | 10-29 20:41 | 10-30 14:30 | `kellys-mbp` |
   | 10-30 15:09 | 10-31 10:46 | `kellys-macbook-pro-local` |

   Neither the vault-sync LaunchAgent nor the shell profiles set `HOSTNAME`, so the
   switch comes from macOS itself. With `writer: kellys-macbook-pro-local`, every
   `kellys-mbp` day would fail with exit 2. The Ledger Tools trigger would log that only
   to the console. Fix the name once on the Mac:

   ```bash
   sudo scutil --set HostName Kellys-MacBook-Pro.local
   hostname   # → Kellys-MacBook-Pro.local on every network
   ```

   Then set `writer: kellys-macbook-pro-local`. Side effect: vault-sync commit labels,
   and the per-host `.bob/themes/` and `.bob/relations/` journals, stop splitting
   across two names.

Pinned block (chezmoi source):

```yaml
gcal:
  account: bryanbugyi34@gmail.com
  writer: kellys-macbook-pro-local
  root: meet
  calendars:
    - id: primary
  tentative: context
  timeout_secs: 60
```

## Pitfalls

### 1. Wrong writer label in the config comment

`writer: kellys-macbook-pro` in the chezmoi config comment (added in `13744456`) does not
match any label Bob computes on the Mac. Copying it as is would block sync everywhere,
on the Mac included.

### 2. The Mac's hostname changes

See above. This only matters for `gcal.writer`. The journal fold reads every
`.bob/gcal/*.jsonl`, so a split journal does not cause duplicate rows.

### 3. Keychain and SSH

Sign in from the Mac's own session (step 1). Fallback if the Keychain cannot store the
token: switch the Mac's gog to the file keyring, as athena does (`gog auth keyring
file`), then run `bob gcal login` again. This moves the Calendar refresh token out of
the Keychain and into `~/.config/gogcli/keyring`. That is a weaker place for it, so use
it only if the Keychain path fails.

### 4. Launch environment: `XDG_CONFIG_HOME` and `PATH`

gog picks its config dir from `XDG_CONFIG_HOME`:

| Environment | gog config file | Clients found |
| --- | --- | --- |
| Login shell (`~/.profile` exports `XDG_CONFIG_HOME=$HOME/.config`) | `~/.config/gogcli/config.json` | `bob-gcal` |
| `XDG_CONFIG_HOME` unset (launchd default; `launchctl getenv XDG_CONFIG_HOME` is empty) | `~/Library/Application Support/gogcli/config.json` | none (dir does not exist) |

Bob finds `gog` only through `BOB_GCAL_GOG` or `PATH`. Ledger Tools passes Obsidian's
own environment to `bob`, adding only `BOB_DIR` and `NO_COLOR`. The running Obsidian
(pid 22516) has your full shell environment: `~/bin` is on `PATH` and
`XDG_CONFIG_HOME=/Users/bbugyi/.config`. So sync on note creation will work as Obsidian
is launched today. If Obsidian is ever started from the Dock, Spotlight, or a login item,
it gets launchd's minimal environment. Sync then fails with exit 2, either `gog not
found` or `no_client`/`not_logged_in`, and only the console shows it. Optional
hardening, so it works however Obsidian starts:

```bash
ln -s ~/.config/gogcli "$HOME/Library/Application Support/gogcli"   # same gog dir with or without XDG
```

The `PATH` gap needs `sudo launchctl config user path "<path incl. /Users/bbugyi/bin>"`
plus a reboot, or always launching Obsidian from the shell as you do now.

### 5. Account must match the day's stamp

Use `bryanbugyi34@gmail.com` (step 1). A different account makes sync refuse any note
whose `↻ synced` stamp names the other account (`account_changed`).

## Evidence

| Observation | Source |
| --- | --- |
| Mac `bob gcal doctor`: `✗ account no Google account is configured`, token and calendars skipped, client ✓ project 780286831122, writer `kellys-macbook-pro-local · no writer pin` | `ssh mac`, 2026-10-31 |
| Mac `status.json`: `{"outcome":"error","error":"not_logged_in: …","ts":"2026-10-31T07:44:05-04:00"}` | `~/.local/state/bob/gcal/status.json` on the Mac |
| athena `status.json`: `written`, +1 task, `07:44:21`. Vault commit `d4dcbc03a vault(athena): .bob/gcal/athena.jsonl, 2026/20261031.md` | athena |
| Mac `gog auth list --json` and `gog --client bob-gcal auth list --json` both return `"accounts": []` | `ssh mac` |
| Mac `gog auth doctor`: keyring `auto`, `keychain.trust application trust enabled (developer-id signed)`, `warn tokens no OAuth tokens stored` | `ssh mac` |
| `env -u XDG_CONFIG_HOME gog --help` → `~/Library/Application Support/gogcli/config.json`; `auth credentials list` there → `[]` | `ssh mac` |
| `com.bbugyi.bob-gcal-sync.plist` present, `launchctl print` → `Could not find service`; no `/var/tmp/com.bbugyi.bob-gcal-sync.*` logs | `ssh mac` |
| chezmoi `fd96796e` retires the plist via `.chezmoiremove`; `13744456` added it plus the commented `writer: kellys-macbook-pro` | chezmoi repo |
| Host label = `$HOSTNAME` or `hostname`, slugged | `src/native/vault_sync.rs` `hostname_slug` |
| Journal fold reads every `*.jsonl` in `.bob/gcal/` | `src/native/pref_journal/mod.rs` `read_raw`, `src/native/gcal/journal.rs` `load_state` |
| Writer check: `this host is {host}; gcal.writer is {writer}` (exit 2) | `src/native/gcal/sync.rs` |
| Account resolution with zero accounts: TTY picker on login, `not_logged_in` elsewhere | `src/native/gcal/account.rs` |
| Ledger Tools spawns `bob gcal sync -q -f json` with `process.env` + `BOB_DIR` + `NO_COLOR`; exit 2 → `console.info` only | bob-plugins `plugins/bob-ledger-tools/src/291-plugin-gcal-events.js`, `236-plugin-stats-data.js` |
| Mac host labels in vault history: `kellys-macbook-pro-local` (4956 commits), `kellys-mbp` (2669), `macbookpro` (11), alternating in blocks | `git log` in `~/bob` |
| `scutil --get HostName` → `not set`; `LocalHostName` → `Kellys-MacBook-Pro` | `ssh mac` |

## Side finding

`bob gcal doctor` prints the gog version as `vv0.44.0` / `vv0.47.1`. `doctor.rs` adds
`v` in front of a version string that gog already starts with `v`. The doc example shows
`v0.44.0`. This is cosmetic only.

## Sources

- bob-cli `docs/gcal.md` (Setup, Login, Where it runs, Exit status, Environment) and
  `docs/guides/connect-google-calendar.md`
- Decision records `bob-gcal-is-read-only-and-proposes-once`,
  `synced-meetings-link-by-phase`
- bob-plugins `docs/bob-ledger-tools.md` § Calendar Events, `docs/bob-command-mode.md`
- chezmoi `home/dot_config/bob/config.yml`, `home/.chezmoiremove`
