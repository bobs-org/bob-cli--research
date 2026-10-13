# Mac: stop the "App Background Activity — “bob” can run in the background" alert

Research date: 2026-10-13. Evidence comes from read-only SSH checks on the MacBook
(macOS 26.5, build 25F71) and the chezmoi source repo. Nothing on the Mac was changed.

## TL;DR

- **Cause (confirmed):** the `com.bbugyi.bob-vault-sync` LaunchAgent runs
  `~/.cargo/bin/bob` directly. `cargo install` produces a new **ad-hoc-signed** `bob`
  on every rebuild. macOS Background Task Management (BTM) identifies ad-hoc code by its
  exact hash, so it sees each new `bob` as a new background item and shows the alert.
- **Fix (recommended):** have the LaunchAgent start `bob` through `/bin/sh`. BTM then
  tracks `/bin/sh`, which Apple signs and which never changes, so rebuilding `bob`
  should no longer trigger the alert. This is a one-line chezmoi change plus a reload.
- **Avoid:** turning the "bob" switch off in Login Items & Extensions. That stops vault
  sync. Also avoid `sfltool resetbtm`, which resets every item and only lasts until the
  next rebuild.

## What happens

1. `just install-all` → `just install` → `cargo install --path .` replaces
   `~/.cargo/bin/bob`.
2. The new binary carries only the linker's ad-hoc signature. It has no Team ID, so its
   only identity is its code hash (cdhash), and that hash changes every build.
3. Within about 15 seconds, launchd runs the vault-sync agent with the new binary. BTM
   drops the old record for the agent, creates a new one, and posts the alert.
4. The alert uses the **Alerts** style (the BTM agent's notification flags decode to
   "alert"), so it stays on screen until you click X.

## Evidence

| Observation | What it shows |
| --- | --- |
| `codesign -dv ~/.cargo/bin/bob` → `flags=0x20002(adhoc,linker-signed)`, `TeamIdentifier=not set` | There is no stable signing identity, only a per-build hash |
| `launchctl print gui/503/com.bbugyi.bob-vault-sync` → `program = /Users/bbugyi/.cargo/bin/bob`, `managed_by = com.apple.xpc.ServiceManagement`, `BTM uuid = C8A5…` | The agent's executable is `bob` itself, and BTM manages the agent |
| `bob` was installed at 04:59. At 04:59:59 BTM logged `invalidateLaunchItem … type=legacy agent … com.bbugyi.bob-vault-sync.plist` (old item `BB4A…`). At 05:00:00 it logged `Posting advisory … identifier=C8A5…, body='“bob” can run in the background…'` | The install directly triggered the alert, which matches the screenshot time (05:00) |
| Nine of these alerts appear in the logs from 2026-10-12 06:53 to 2026-10-13 05:00, each with a **different** item ID | BTM creates a new record for every rebuilt `bob` |
| The plist has not changed since chezmoi first added it (one commit) | The binary changes, not the plist |
| `security find-identity -v -p codesigning` → `0 valid identities found` | The Mac has no signing certificate, so "just sign it properly" is not a quick fix |

## Recommended fix

In the chezmoi repo, edit `home/Library/LaunchAgents/com.bbugyi.bob-vault-sync.plist`
and replace the `ProgramArguments` array with:

```xml
<key>ProgramArguments</key>
<array>
  <string>/bin/sh</string>
  <string>-c</string>
  <string>exec /Users/bbugyi/.cargo/bin/bob vault-sync -q</string>
</array>
```

`exec` makes `sh` replace itself with `bob`, so launchd still supervises a single
process, and exit codes and logs behave as before. Leave the rest of the plist as it is.

Apply it on the Mac. chezmoi has no reload hook for this agent, so reload it by hand:

```bash
chezmoi apply ~/Library/LaunchAgents/com.bbugyi.bob-vault-sync.plist
launchctl bootout gui/$(id -u)/com.bbugyi.bob-vault-sync
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.bbugyi.bob-vault-sync.plist
launchctl print gui/$(id -u)/com.bbugyi.bob-vault-sync | grep 'program ='   # expect /bin/sh
```

Expect **one last alert** when the agent is reloaded, probably naming `sh`. Dismiss it.
To verify, run `just install-all` after bob-cli has new commits. No alert should
appear. To check the logs:

```bash
/usr/bin/log show --last 1h --style compact \
  --predicate 'process == "BackgroundTaskManagementAgent" AND eventMessage CONTAINS "Posting advisory"'
```

**Confidence:** the cause is confirmed by the logs above. The fix is a strong inference
from how BTM identifies items: it keeps a record while the executable's identity stays
the same, and `/bin/sh`'s Apple identity never changes. It has not been tested on this
Mac yet. If an alert still appears after a rebuild, the fallback is the signing option
below.

## Other options considered

| Option | Verdict |
| --- | --- |
| Sign `bob` with a stable certificate (for example, a free "Apple Development" cert) after every `cargo install` | Should also work, because BTM tracks signed code by its stable signature rather than its hash. It needs a certificate (none exists today) and an extra signing step in `just install`. Use it only as a fallback. |
| Switch the "bob" item off in System Settings → General → Login Items & Extensions | Blocks the agent, so vault sync stops. Don't do this. |
| `sfltool resetbtm` plus a reboot | Clears BTM's whole database and re-enables everything. The next rebuild brings the alert back. |
| Silence the alerts with an MDM Notifications payload for `com.apple.btmnotificationagent` | Requires an enterprise-style managed profile, and it would also hide real warnings, such as malware adding itself to startup. |
| Replace the LaunchAgent with cron (the other bob jobs already use cron) | Cron's smallest interval is one minute, so it can't replace the 15-second sync. Not worth it. |

## Sources

- Eclectic Light, [Controlling login and background items in Ventura](https://eclecticlight.co/2023/02/15/controlling-login-and-background-items-in-ventura/)
  and [How Ventura is changing login and background items](https://eclecticlight.co/2023/02/16/how-ventura-is-changing-login-and-background-items)
  (BTM, LaunchAgents as background items, `sfltool`).
- Apple Developer Forums, [What are "Login Items Added by Apps" in Ventura?](https://developer.apple.com/forums/thread/709157)
  (launchd agents appear under "Allow in the Background").
- Michael Tsai, [Ventura's Open at Login vs. Allow in the Background](https://mjtsai.com/blog/2022/10/27/venturas-open-at-login-vs-allow-in-the-background).
- Jamf Community, [Background login items — Ventura](https://community.jamf.com/general-discussions-2/background-login-items-ventura-28667/index2.html)
  (MDM Notifications payload for `com.apple.btmnotificationagent`).
- PiunikaWeb, [Ventura "Background Items Added" notification issue](https://piunikaweb.com/2023/01/30/macos-13-ventura-background-items-added-notification-issue/)
  (`sfltool resetbtm` workaround and its side effects).
