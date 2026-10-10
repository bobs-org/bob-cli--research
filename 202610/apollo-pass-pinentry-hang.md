# Apollo: why `pass show sase_listen_feed_token` hangs

Research date: 2026-10-10. Live observations: approximately 19:01–19:03 UTC
(15:01–15:03 EDT), as SSH user `bryan` on `apollo`.

**Finding:** an orphaned password read for **`gemini_cli_api_key`** left
`pinentry-curses` running against a deleted terminal. The prompt was consuming CPU,
and Apollo's GPG agent repeatedly reported failure to acquire the pinentry lock.
Other password reads, including a bounded probe of `sase_listen_feed_token`, then
blocked. This is strong evidence of a shared GPG/pinentry blockage, rather than a
problem specific to the feed token.

The immediate recovery is to cancel the abandoned prompt, then unlock GPG from a
real SSH terminal. The durable fix is to prevent unattended secret lookups from
opening interactive prompts and to give them an explicit deadline. For a service
that must survive reboot without a human unlock, provision a narrowly scoped
service credential instead of depending on the interactive GPG cache.

This investigation inspected process metadata, selected configuration, package
versions, and filtered agent logs. One five-second, no-prompt password-read probe
discarded all plaintext to `/dev/null`. No secret values were displayed or saved.
No existing processes were killed, configuration changed, credentials provisioned,
or services restarted. Recovery instructions below are recommendations, not an
applied or verified repair.

**Live evidence**

| Observation | Implication |
| --- | --- |
| Ubuntu 24.04.3 LTS; `pass` 1.7.4-6; GPG and agent 2.4.4-2ubuntu17.6; `pinentry-curses` 1.2.1-3ubuntu5 | Identifies the actual installed stack. |
| PID 386393 was `bash /usr/bin/pass show gemini_cli_api_key`, started 18:56:33 UTC, with parent PID 1 | The password-reader shell had lost its original parent. Its original launcher could no longer be identified from ancestry. |
| Its child, `gpg2` PID 386394, was decrypting `gemini_cli_api_key.gpg` and sleeping in `unix_stream_data_wait` | GPG was waiting on a Unix socket, consistent with waiting for its agent. |
| GPG inherited `GPG_TTY=/dev/pts/5`, `TERM=tmux-256color`, and `DISPLAY=localhost:10.0` | The operation carried terminal and SSH display state from an earlier session. |
| `pinentry-curses` PID 386399 was a child of agent PID 1916; file descriptors 5 and 6 pointed to `/dev/pts/5 (deleted)`; `/dev/pts/5` no longer existed | Direct evidence that the live prompt was attached to a dead terminal. |
| The prompt accumulated 4m31s CPU over 6m27s elapsed, about 70% lifetime CPU | It was actively spinning, not simply sitting at a visible prompt. |
| Agent logs repeatedly contained `failed to acquire the pinentry lock: Timeout`, followed by failed key-unprotect and `PKDECRYPT` operations | Direct confirmation of contention for the agent's prompt lock. |
| `gpg-connect-agent --no-autostart 'GETINFO version' /bye` promptly returned `D 2.4.4`, `OK`, exit 0 | The agent was reachable; a healthy control connection does not imply decryption is healthy. |
| The no-prompt target probe below returned 124 after five seconds | The requested feed-token read was also blocked during the incident. |

The probe was:

```sh
timeout -k 2s 5s env \
  PASSWORD_STORE_GPG_OPTS='--batch --pinentry-mode error' \
  pass show sase_listen_feed_token >/dev/null
```

Its only diagnostic was GPG acknowledging termination when the deadline expired.
A subsequent process check showed the original GPG and pinentry processes, with no
remaining GPG process from this probe.

The agent was systemd-supervised, active since 2026-10-09 12:55:09 UTC, using
`/run/user/1000/gnupg/S.gpg-agent`. No top-level `~/.gnupg/*.lock` files were found.
This was not an exhaustive keybox-lock audit, but the explicit pinentry-lock errors
make speculative lock-file deletion an inappropriate first response.

**How the failure fits together**

`pass` stores entries as GPG-encrypted files and decrypts them through GPG and its
agent. Different entry names can therefore encounter the same agent-level problem.
[Official pass documentation](https://www.passwordstore.org/)

The evidence supports this sequence:

1. A read of the Gemini API key needed an interactive unlock.
2. Its pinentry opened the terminal identified by `/dev/pts/5`.
3. That terminal disappeared, while the password-reader shell became orphaned.
4. The prompt remained alive, spinning and holding up other prompt-dependent agent
   operations.
5. Later password reads appeared to hang, including the feed-token probe.

The exact event that removed the terminal—an SSH disconnect, closed tmux pane,
runner timeout, or another cancellation—was not established. `TERM=tmux-256color`
does not prove which of those occurred. Likewise, no surviving ancestry proves
that `sase-listen` launched the orphan, although its configured Gemini secret
command matches the observed entry.

GnuPG's troubleshooting documentation explains that curses pinentry requires a
correct terminal and that an existing prompt must be cleared before a future prompt
can use a different display. Merely refreshing terminal settings cannot move this
already-running prompt away from its deleted device.
[GnuPG common problems](https://www.gnupg.org/documentation/manuals/gnupg/Common-Problems.html)

The inherited `DISPLAY=localhost:10.0` is useful context, but a broken X11 connection
is not needed to explain this incident: the configured program is curses pinentry,
and its terminal descriptors are demonstrably dead. Absence of a controlling TTY
in `ps` alone would also be insufficient evidence, because agent-launched prompts
can open an explicitly supplied terminal.

Historical upstream reports describe invalid-TTY hangs and spinning curses
pinentry processes. Search-index excerpts were available for these reports, but
their full issue pages could not be fetched during this investigation. They are
corroborating leads, not proof of an identical bug or a particular fixed release.
[GnuPG T6723](https://static.dev.gnupg.org/T6723.html),
[GnuPG T2875](https://dev.gnupg.org/T2875.html)

**Recover now**

Run these steps yourself in an interactive terminal. They intentionally discard
password output; enter the GPG key passphrase only in the normal unlock prompt.

1. Connect with a terminal and avoid introducing X11 forwarding:

   ```sh
   ssh -t -x apollo
   ```

   Stop any repeatedly retrying secret consumer while recovering. Cancel your
   currently hung foreground `pass` command with Ctrl-C if it still exists.

2. Identify the abandoned prompt again; the PIDs in this report are historical:

   ```sh
   ps -u "$(id -u)" -o pid,ppid,tty,stat,etime,time,comm |
     grep -E '(PID|gpg|pinentry)'
   ```

   Inspect `/proc/PID/fd` for the candidate pinentry and confirm the deleted terminal
   before sending `kill -TERM PID`. Substitute the verified current PID. This
   cancels that prompt and causes its pending operation to fail; it does not delete
   keys or password entries. Recheck that it exited. If the same verified process
   ignores TERM, a targeted KILL is a last resort. Do not indiscriminately kill all
   `gpg`, `pass`, or `pinentry` processes.

3. Point new operations at the terminal you are actually using and unlock:

   ```sh
   unset DISPLAY
   export GPG_TTY="$(tty)"
   timeout -k 2s 5s gpg-connect-agent updatestartuptty /bye
   pass show sase_listen_feed_token >/dev/null
   ```

   `tty` must print a real device such as `/dev/pts/2`. If it reports that there is
   no terminal, reconnect interactively. Allow the unlock prompt to complete before
   closing this shell. `UPDATESTARTUPTTY` updates the agent's default display for
   future prompts; it does not repair an existing one.
   [GnuPG UPDATESTARTUPTTY](https://www.gnupg.org/documentation/manuals/gnupg/Agent-UPDATESTARTUPTTY.html)

4. If targeted cancellation does not recover the agent, reset it during a moment
   when interrupting other GPG operations is acceptable:

   ```sh
   timeout -k 2s 5s gpgconf --kill gpg-agent
   timeout -k 2s 5s gpg-connect-agent updatestartuptty /bye
   pass show sase_listen_feed_token >/dev/null
   ```

   This clears the in-memory unlock cache and interrupts other operations using
   Bryan's agent. GnuPG normally starts the agent on demand. If the supervised unit
   fails to return, inspect `systemctl --user status gpg-agent.service` before
   considering a user-service restart. A machine reboot should not be necessary.
   [GnuPG agent invocation](https://www.gnupg.org/documentation/manuals/gnupg/Invoking-GPG_002dAGENT.html)

5. Confirm unattended behavior after unlocking:

   ```sh
   timeout -k 2s 5s env \
     PASSWORD_STORE_GPG_OPTS='--batch --pinentry-mode error' \
     pass show sase_listen_feed_token >/dev/null
   printf 'exit=%s\n' "$?"
   ```

   Exit 0 confirms successful decryption at that moment. An immediate GPG error
   means it still needs an unlock or has another key-related problem; inspect the
   message. Exit 124 means the deadline expired; 137 can indicate forced killing.
   Then check for surviving pinentry processes and recent agent lock errors.
   [GNU timeout documentation](https://www.gnu.org/software/coreutils/manual/html_node/timeout-invocation.html)

If the intended workflow also renders Gemini audio, unlock/test
`gemini_cli_api_key` separately. Successful feed-token decryption does not prove
every entry uses the same key or is unlocked.

**Prevent recurrence in interactive sessions**

Apollo already has the normal terminal-refresh fix. Its installed `~/.zshrc`,
lines 386–390, matches the managed source:

```zsh
if [[ -n "${TTY}" && -c "${TTY}" ]]; then
  export GPG_TTY="${TTY}"
  command -v gpg-connect-agent &>/dev/null &&
    gpg-connect-agent updatestartuptty /bye &>/dev/null
fi
```

Therefore, adding another unconditional `export GPG_TTY=$(tty)` is not the missing
fix. Preserve this guard, refresh the terminal when moving between sessions, and
complete or cancel an unlock before closing its terminal. Interactive shell setup
does not make a detached process safe to prompt later. Avoid hardcoding a
`/dev/pts/N` path or globally exporting a fabricated terminal for services.

Apollo's installed `~/.gnupg/gpg-agent.conf` and the managed template contain:

```text
pinentry-program /usr/bin/pinentry-curses
default-cache-ttl 34560000
max-cache-ttl 34560000
no-allow-external-cache
```

Both cache lifetimes are already **400 days**. Increasing them will not address
this failure. A cache lifetime does not prevent loss of in-memory state on restart;
configuration reloads can flush it too. The managed configuration-change hook runs
`gpg-connect-agent reloadagent /bye`, so configuration deployment is another point
at which unattended consumers must tolerate needing an unlock. No evidence ties
this particular incident to a reload.
[GnuPG agent signals](https://www.gnupg.org/documentation/manuals/gnupg/Agent-Signals.html)

Add a finite prompt lifetime, for example `pinentry-timeout 60`, to the Linux branch
of the managed GPG-agent template, then apply/reload it and test. This is defense in
depth: GnuPG requests a timeout, but the pinentry implementation may not honor it.
It is not a substitute for an application deadline, and the dead-terminal path
needs explicit testing. Cache policy and prompt timeout are separate settings.
[GnuPG agent options](https://www.gnupg.org/documentation/manuals/gnupg/Agent-Options.html)

The installed and candidate pinentry versions were identical in Apollo's current
APT metadata. Routine package maintenance is sensible, but this investigation did
not identify an available upgrade proven to fix the incident. Switching to a GUI
pinentry on this headless server would introduce a different display dependency.

**Prevent recurrence in unattended commands**

The managed listener configuration contains both of these unqualified lookups:

```yaml
engines:
  gemini:
    api_key_command: pass show gemini_cli_api_key
feed:
  token_command: pass show sase_listen_feed_token
```

For background consumers, use a command that refuses interactive prompting and
has a deadline. An Apollo/Linux command form is:

```sh
timeout -k 2s 10s env \
  PASSWORD_STORE_GPG_OPTS=--pinentry-mode=error \
  pass show sase_listen_feed_token
```

Here stdout must go directly to the credential-consuming application; add
`>/dev/null` only when testing. Apply the same policy to the Gemini key lookup.
GPG's `error` pinentry mode returns an error when prompting would be necessary.
`--batch` by itself is insufficient: the original blocked GPG process already had
that flag. Do not set the no-prompt policy globally in interactive shells.
[GnuPG pinentry modes](https://www.gnupg.org/documentation/manuals/gnupg/GPG-Esoteric-Options.html)

Both controls matter. **The incident probe still timed out with pinentry disabled**,
so a no-prompt flag alone cannot be treated as a reliable wall-clock bound when the
agent is already obstructed. Conversely, killing a caller on timeout does not
necessarily remove its pinentry: the observed pinentry belonged to the long-lived
agent's session, not the orphaned caller's process group.

The consumer should fail with an actionable unlock/deadline error, reject an empty
credential, and avoid immediate retry loops. If implementing this in application
code, bound subprocess execution, clean up its process group, and avoid logging
captured stdout. Do not solve it by putting the GPG passphrase in an argument,
environment variable, or committed configuration.

These are proposed command-policy changes, not a verified listener patch. The
listener implementation and its subprocess cleanup were not inspected. No
`*listen*` units appeared in the system or user unit listings, which also does not
establish how every consumer is launched. GNU `timeout` is present on Apollo;
shared macOS configuration needs an installed equivalent or an application-level
deadline instead of assuming that executable exists everywhere.

**For unattended operation after reboot**

Decide whether a human unlock after restart is acceptable:

| Requirement | Recommended approach | Cost |
| --- | --- | --- |
| Interactive use or occasional background use after manual unlock | Keep `pass`; add no-prompt reads, deadlines, clear errors, and a documented unlock step | Work must wait for a human after cache loss. |
| Reliable autonomous feed/token use after reboot | Provision only the required service token into a protected credential file or a service credential facility | Introduces credential provisioning, rotation, and access-control responsibilities. |
| A systemd-managed consumer with suitable credential support | Evaluate `LoadCredential=` or `LoadCredentialEncrypted=` and a credential-file reader | Requires unit/application integration and testing on the installed systemd version. |

A practical file-backed variant would retain `pass` as the source of truth and
provision a dedicated token file outside the public feed directory, under a private
directory (0700), with file mode 0600. Update it atomically only after a successful
read; never overwrite a working token with empty output from a failed unlock.
An existing `token_command` interface can potentially read that file with
`cat /home/bryan/.config/sase-listen/secrets/feed-token`; verify the consumer's
command handling before deployment. Use a separate file for the Gemini key only
if that consumer also needs unattended access.

This makes the token readable to the owning account and root without a GPG unlock;
it does not protect against compromise of that account. Do not commit the file or
place it inside the served feed tree. Define how token rotation updates every
consumer. Scope any managed configuration by host instead of copying an Apollo
absolute path into all machines' configuration.

Systemd credentials provide a more structured alternative: applications receive
credential files through `$CREDENTIALS_DIRECTORY`; encrypted credentials can be
decrypted at activation using supported machine-bound key material. They still
require deliberate provisioning and do not make an arbitrary VM immune to host
compromise. Availability and user-service restrictions must be checked against
Apollo's installed version before choosing an exact unit configuration.
[Systemd service credentials](https://systemd.io/CREDENTIALS/)

**Validation for a lasting fix**

After implementing the selected policy, verify all of these conditions:

- Normal interactive unlock works in a fresh SSH terminal and a new tmux pane.
- With a cold cache during a maintenance window, an unattended lookup returns an
  understandable error within its deadline and creates no interactive pinentry.
- With an unlocked cache, both relevant entries can be read with stdout discarded.
- Cancelling a consumer or losing its session leaves no orphaned password-reader
  process or spinning pinentry. Exercise failure handling with a test key/entry
  rather than deliberately wedging the production agent.
- Following a planned restart, the workflow either succeeds using its provisioned
  service credential or explicitly reports that manual unlock is required.
- A simulated secret-read failure does not replace a valid credential or expose
  plaintext in logs.

Avoid deleting `~/.gnupg`, reinitializing `pass`, changing key trust, removing random
lock files, or rotating the feed token as initial remedies. None addresses the
observed deleted-terminal prompt and pinentry-lock contention.

**Configuration provenance and remaining limits**

The chezmoi repository was inspected at commit
`1dcd13fc852e7b8ad78081d635f7405ca59eb48a`. Relevant source paths are:

- `home/dot_zshrc:386` — guarded terminal refresh, also verified on Apollo.
- `home/private_dot_gnupg/gpg-agent.conf.tmpl` — curses pinentry, cache lifetimes,
  and external-cache policy, also verified on Apollo.
- `home/.chezmoiscripts/run_onchange_after_reload_gpg_agent.tmpl` — reload hook.
- `home/dot_config/sase-listen/config.yml:10` and `:16` — Gemini and feed secret
  commands. These establish managed-source intent; their deployed listener copy
  was not independently inspected.

The terminal-refresh change originated in commit
`b80edd96826169635dd531f6f5dfac9c80dee88d` on 2026-09-03, so it predates this incident.

The process/file-descriptor evidence and journal messages establish the immediate
failure mechanism with high confidence. The original launcher, why its terminal
closed, the feed token's state after clearing the blocker, and the effectiveness of
the proposed recovery remain unverified. At the end of live inspection the original
stuck processes were still present; this report did not silently repair Apollo.
