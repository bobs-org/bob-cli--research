# Can an agent read bryanbugyi34@gmail.com right now?

_Checked 2026-11-05 on **apollo**, from a SASE agent workspace, using the
`sase_gmail` skill (the `gog` CLI)._

## Answer

**Yes. Nothing needs fixing.** The agent can search the inbox and open full messages
for `bryanbugyi34@gmail.com`. Access is **read-only**: the OAuth token holds only the
`gmail.readonly` scope, so sending, labeling, archiving, or trashing mail is impossible
even if an agent is asked to.

## Evidence

| Check | Command (abridged) | Result |
| --- | --- | --- |
| Account | `gog --json auth status` | `bryanbugyi34@gmail.com`, OAuth, `file` keyring |
| Health | `gog auth doctor` | `status ok`: keyring opened, 1 of 1 tokens readable, client credentials present |
| Scopes | `gog --json auth list` | `gmail.readonly`, `userinfo.email`, `email`, `openid`; token created 2026-10-27 |
| Search | `gog … gmail search "in:inbox newer_than:2d" --max 3` | exit 0; 3 threads, newest 2026-11-05 15:31Z, `has_more: true` |
| Read | `gog … gmail get <id> --sanitize-content` | exit 0; full message (headers and body) |

`…` is the skill's safe flag set: `--json --no-input --gmail-no-send --wrap-untrusted
--enable-commands gmail.search,gmail.get,gmail.thread.get,gmail.thread.attachments,gmail.attachment`.

## Why it works

Each link below has to hold. When access breaks, one of them has broken.

1. **Wrapper.** `~/bin/gog` runs `~/.local/bin/gog` (v0.44.0) with
   `GOG_KEYRING_PASSWORD` set. `~/bin` comes before `~/.local/bin` on `PATH`
   (positions 11 and 12), so agents get the wrapper.
2. **OAuth client.** `~/.config/gogcli/credentials.json`.
3. **Refresh token.** Stored encrypted in the file keyring at
   `~/.config/gogcli/keyring/`. The keyring files were refreshed today.
4. **Account selection.** `SASE_GMAIL_ACCOUNT` is unset, so the skill falls back to
   `gog auth status`, which returns `bryanbugyi34@gmail.com`.

The token is 9 days old and still works. Google expires refresh tokens after 7 days for
OAuth apps in "Testing" mode, so that common cause of failure does not apply to this
client.

## Limits

- **Verified on apollo only.** athena and the Mac each have their own gog config,
  keyring, and token. An agent on another host needs that host's setup to pass the
  same checks.
- **Read-only.** Drafting, sending, and label changes are blocked three ways: by the
  OAuth scope, by `--gmail-no-send` and `--enable-commands`, and by the skill's rules.
- **The claude.ai Gmail connector is not used.** This session also loads claude.ai's
  Gmail tools, which include write actions like trash, spam, and labels. The
  `sase_gmail` skill says to use `gog` only, so they were not used or tested.

## If it ever stops working

Run `gog auth doctor` first. It names the failing link. Then match the symptom:

| Symptom | Cause | Exact fix |
| --- | --- | --- |
| Keyring won't open, or asks for a password | `gog` ran without the wrapper (for example, `~/.local/bin` came first on `PATH`) | Put `~/bin` before `~/.local/bin` on the agent's `PATH`. Or export `GOG_KEYRING_PASSWORD` with the same value the wrapper uses. |
| `invalid_grant`, token expired, or token revoked | Refresh token is dead (revoked in Google Account settings, password change, or a Testing-mode client) | `gog auth add bryanbugyi34@gmail.com --services gmail --gmail-scope readonly --force-consent --manual`. Open the printed URL, approve, and paste back the redirect URL. Then rerun `gog auth doctor`. |
| No OAuth client credentials | `credentials.json` is missing | Download the Desktop OAuth client JSON from Google Cloud Console, run `gog auth credentials set <file.json>`, then do the `auth add` step above. |
| Agent reads the wrong mailbox | Another account became the default | `export SASE_GMAIL_ACCOUNT=bryanbugyi34@gmail.com` in the agent environment. |
| `gog executable not found` | Binary missing on this host | Install gog to `~/.local/bin/gog` (Linux) or `/opt/homebrew/bin/gog` (Mac). |
