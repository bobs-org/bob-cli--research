# `bob gkeep`: Draining the Google Keep Inbox into Obsidian Tasks

- **Researcher:** cld (one of five in the research swarm)
- **Date:** 2026-09-28
- **Request:** Design a `bob gkeep` command with (1) a subcommand that moves every Google Keep
  inbox note (`keep.google.com/#home`) into Obsidian tasks in `~/bob/gkeep_inbox.md` and archives
  each Keep note once the move has definitely succeeded, and (2) a subcommand that lists Keep
  items and/or the `gkeep_inbox.md` tasks. Critique the plan, adjust the requirements where that
  is justified, and recommend a solution.

---

## 0. TL;DR

**Build it.** This fixes a problem your vault has already recorded: the `legacy_gkeep_notes.md`
freshness reminder, the "copy Keep to a Google Doc when it overflows" workaround, and the one-off
`gkeep_gdocs_inbox_dump.md` conversion on 2026-05-29 all show the Keep inbox falling behind. A
reliable one-command drain is a real improvement to your GTD loop.

**What should change about the approach:**

1. **Treat it as a recurring drain (`bob gkeep pull`), not a one-time migration.** You capture
   into Keep on your phone every day, so this command will run every day.
2. **Use only the unofficial API.** The official Google Keep API is limited to Workspace accounts
   and has no archive operation, so it cannot do this job. The only practical route is
   **gkeepapi**, the maintained unofficial client (0.17.1, released 2026-01-05). Keep it behind a
   **thin, pinned Python adapter embedded in `bob`** and run it with `uv run --script`. Rust should
   own everything you actually see and everything that affects safety: rendering, vault writes,
   verification, the archive decision, and output. Don't port the private protocol to Rust yet
   (see §2.3 for why).
3. **Make archiving provably safe.** Archive a Keep note only if *its current content* is already
   durably in the vault: written, fsynced, re-read and verified, and committed to vault Git. The
   archive call must also refuse any note that changed in Keep during the run. Every step can be
   repeated safely or undone, so a crash at any point costs nothing.
4. **Use the vault as the ledger.** Each migrated task gets a `Source:` child line (the same
   convention `mac_inbox.md` already uses) that links back to the Keep note and carries a hidden
   version marker. That makes re-runs deduplicate across machines and survives triage moves and
   `move-done-tasks`.
5. **Add safe defaults and two small helper subcommands.** Pinned notes (and shared notes) stay in
   Keep by default, so "pin = keep it in Keep" becomes an easy rule to remember. Add
   `bob gkeep doctor` and `bob gkeep login`, because authentication is the most likely failure
   point. Your existing `pass` entry is named `gkeep_oauth_token`, which may not be a master token
   at all (see §1.1).

Final recommended command surface: `bob gkeep [doctor | list | login | pull]`, where plain
`bob gkeep` runs `list`, following the `bob plugins` convention.

---

## 1. What I Found

### 1.1 Your current setup (local evidence)

| Finding | Evidence | Why it matters |
| --- | --- | --- |
| The target note already exists and is prepared | `~/bob/gkeep_inbox.md` has `parent: "[[inbox]]"`, a `## Tasks` heading, and the line "The tasks below are pulled in by the `bob gkeep` command." | The target and the insertion point are settled. The note has **no `type:`** frontmatter, unlike `mac_inbox.md` (`type: "[[area]]"`), so `task-status-hooks` won't add status groups or badges to it. It still carries stale zorg frontmatter. |
| Keep is a long-running GTD inbox that falls behind | `legacy_gkeep_notes.md` holds a daily `@FRESHNESS` reminder to "clear my #gkeep inbox" and an "overflow gdocs" workaround for "when you inevitably fall off the #gtd wagon" | This is the failure mode automation fixes. |
| A one-off Keep conversion already happened (2026-05-29) | The first vault commit of `gkeep_gdocs_inbox_dump.md` (`source: google_keep`) has about 73 checkbox lines. It used `- [ ] #task <title> [gkeep:: 2.a44] …`, rendered untitled notes as "Review untitled Google Keep note", and made checklist items `- [ ]` children | This is prior art for the rendering you've already accepted. It also shows a fragile choice to avoid: a custom inline `[gkeep:: …]` field (see §5.4). |
| **A Python Keep CLI already exists in your dotfiles** | chezmoi `home/lib/keep_cli/main.py` (1,080 lines, commit `3a20457d`, 2026-05-29) plus `home/bin/keep-cli` → `pybash ~/lib/keep_cli`. It pins `gkeepapi==0.17.1`, `gpsoauth==2.0.0`, `keyring==25.7.0` and has `auth exchange`, `inbox`, `archive`, `backup`, `show`, and more. | This confirms gkeepapi works for your account and shows the auth flow you used. It also has problems (next two rows). |
| `keep-cli` can't read its token on apollo | `keep-cli auth status --json` on apollo: *"No recommended backend was available"*. Python `keyring` has no Secret Service backend on this headless host. | Don't use Python `keyring` for storing the token. |
| Your token lives in `pass` | `~/.password-store/gkeep_oauth_token.gpg` (modified 2026-09-03). `pass` is already your cross-machine secret store (the `gog` wrapper and `macos.sh` aliases use `pass show`). | Read the token through a configurable `token_command` (default `pass show …`). **Caveat:** the name suggests the browser `oauth_token` cookie (`oauth2_4/…`), which is short-lived and must be *exchanged* for a master token (`aas_et/…`). gkeepapi issue #180 is exactly someone passing a non-master token to `authenticate()` and getting `LoginException: Unknown`. I did not decrypt the entry. |
| The `pybash` venv bootstrap is fragile | While researching, a truncated `keep-cli` run left a half-built venv, and a rerun then failed in `ensurepip` until a clean third run rebuilt it. The venv is working again now. | The bob adapter should use `uv run --script` (reproducible, cached, atomic environments) instead of a hand-rolled venv. `uv` is installed on both machines through chezmoi. |
| bob-cli conventions to reuse | `bob plugins` runs `list` when no subcommand is given. Output is a `Title · counts · path` header, an ALL-CAPS table, and a `· `-separated footer, with `Styler` colors and `NO_COLOR` support. JSON outputs carry `schema_version: 1`. Also available: the shared `bob_sync.lock` (`ob::try_acquire_lock`), `collect_done::atomic_write` (temp + rename, **no fsync**), capture's `insert_task_line` (inserts under `## Tasks` after the last top-level `#task` block), embedded assets extracted to `$XDG_CACHE_HOME/bob-cli/scripts/`, and command-override env hooks like `BOB_CLIPBOARD_CMD` for tests | Most of the plumbing already exists. Per `cli_rules.md`, every public long option needs a short alias and options stay alphabetized. |
| Tasks plugin settings | `globalFilter: "#task"`, `taskFormat: "dataview"`, capture writes `- [ ] #task <body> [created::YYYY-MM-DD]` | Checklist children *without* `#task` stay plain checkboxes, not Tasks tasks. A literal `#task` inside Keep text must be escaped. |

### 1.2 Ways to talk to Google Keep

| Option | Consumer Gmail? | Can archive? | Verdict |
| --- | --- | --- | --- |
| **Official Keep API** (`keep.googleapis.com/v1`) | **No.** Workspace only, enabled by an admin through domain-wide delegation | **No.** The Note resource has no `archived` field. The only methods are `create`, `get`, `list`, and `delete` (permanent) | Ruled out |
| `gog` (gogcli) Keep commands | No. Its README says Keep is "Workspace only … service account + domain-wide delegation" | No (read-only) | Ruled out |
| **gkeepapi** (unofficial; reverse-engineered Android sync protocol) | **Yes** | **Yes**: `note.archived = True; keep.sync()`. Since issue #181, archiving doesn't touch the edit timestamp | **Recommended**, behind an adapter |
| Native Rust port of the same private protocol | Yes | Yes | Possible later (see §2.3). Not for v1 |
| Your existing `keep-cli` as a subprocess | Yes | Yes, but one full login and sync per note | Not recommended as the engine: dotfiles-versioned contract, keyring broken on apollo, `pybash` fragility, no guarded archive |
| Browser automation (Playwright on `keep.google.com`) | Yes | Yes | Fragile DOM plus 2FA. Ruled out |
| Google Takeout | Yes | No | Manual one-shot export. Ruled out |
| **Switch the phone inbox to Google Tasks** | Yes, *official* consumer OAuth API (`gog` already supports Tasks) | "Complete" works as archive | The strongest *alternative* if the unofficial Keep API ever becomes a burden (see §3) |

### 1.3 Protocol facts that shape the design

- **One endpoint.** gkeepapi POSTs to `https://www.googleapis.com/notes/v1/changes` with the
  client's `targetVersion` and any dirty nodes. The server returns changed nodes, a `toVersion`,
  and a `truncated` flag for paging. **Archive** means sending the top-level node back with
  `isArchived: true` and a fresh `updated` timestamp. Title and text aren't re-sent, because the
  text lives in child nodes that aren't dirty.
- **Auth has two layers.** A long-lived **master token** (`aas_et/…`, full account access) is
  exchanged for short-lived OAuth tokens through gpsoauth `perform_oauth` against
  `android.clients.google.com/auth`, posing as the Keep Android app. The master token comes from
  a one-time browser flow: sign in at `accounts.google.com/EmbeddedSetup`, copy the `oauth_token`
  cookie, then call `gpsoauth.exchange_token(email, oauth_token, android_id)`. Password login no
  longer works.
- **Google checks the TLS fingerprint on the auth call.** gpsoauth pins a cipher list, disables
  ALPN, and re-enables session tickets, because otherwise "Google … return[s] 403 Bad
  Authentication". This is the main risk of a Rust port.
- **Device ID.** gkeepapi defaults `device_id` to the host MAC address, so apollo and the Mac
  would look like different devices. Persist one hex `device_id` in config and reuse it on every
  host.
- **Full syncs are slow for big accounts.** Every `authenticate()` pulls the entire tree,
  archived notes included (see issue #174, "Master Token authentication taking forever").
  `keep.dump()` / `authenticate(..., state=…)` makes syncs incremental. The adapter should cache
  that state (mode 0600, since it contains note text).
- **Home = `find(archived=False, trashed=False)`**, excluding `deleted`. Pinned notes appear in
  home too. Node types are `Note` (text) and `List` (items with `checked` and one level of
  indentation). Blob children can be images (with OCR `extracted_text`), drawings, or audio.
- gkeepapi already backs off on HTTP 429 and refreshes OAuth on 401 (upstream fixes from 2025),
  which is a good reason to depend on it rather than re-derive it.

---

## 2. Critique: Is This a Good Idea?

### 2.1 Yes, for these reasons

- **It closes the GTD "collect → process" gap your vault has already documented.** Keep is the
  best capture surface on your phone (widget, share sheet, Gemini voice, Wear OS). Obsidian is
  your system of record. Your vault syncs only through Git, so the phone has no direct path into
  it. Something has to bridge the two, and doing it by hand is exactly what fell behind.
- **Archive is the right action, not trash.** It's reversible, searchable, and keeps images and
  voice audio in Keep. It also means migrating a note can't destroy anything.
- **It fits bob.** bob-cli already has the vault writer, the task insertion logic, locks, styled
  tables, JSON contracts, and an embedded-asset mechanism.

### 2.2 Risks and how the design handles them

| Risk | Likelihood | Impact | Mitigation |
| --- | --- | --- | --- |
| Google changes the private protocol or auth | Medium over years | `pull` stops working, but **no data is lost** because nothing is archived without verification | Adapter boundary, pinned versions, upstream gkeepapi fixes, `doctor`. Fallback plan: Google Tasks (§3) |
| Master token leaks (full-account credential) | Low | High | Keep it in `pass`/gpg. Send it to the adapter on **stdin**, never argv (`ps` shows argv to other users). Never log it. Revoke it by removing the fake "Android device" in your Google account's device list |
| Account flagged for an unofficial client | Low | Medium | Low request rate (manual or hourly runs), incremental state cache, gkeepapi's backoff |
| Archiving "reference" notes you meant to keep in Keep | Medium without filters | Medium, but reversible | Pinned and shared notes are skipped by default. `--dry-run`. `list` shows exactly what `pull` would take |
| Data loss between vault and Keep | Very low by design | High | The invariant in §5.3: fsync, re-read verify, and a scoped commit before archiving, plus a content-guarded archive |
| Duplicate tasks | Low | Low | The vault acts as the ledger, with a version marker. Automated runs happen on one host |
| **Keep text misread as bob capture grammar** | **High if you reuse `bob capture`** | **High**: a note that is just `=x` closes your running Pomodoro, `+5` extends it, `%` pastes the clipboard, `@x` re-routes the note, and a trailing `#` becomes a Pomodoro note | Never send Keep text through the capture grammar. Use a literal renderer with explicit escaping (§5.4) |
| Inbox sprawl (`inbox.md`, `mac_inbox.md`, `gkeep_inbox.md`, the dump) | Already present | Low | Keep `gkeep_inbox.md` separate, since knowing a task came from Keep is useful, but add it to the `capture-targets` Inbox group so the pickers show one "Inbox" family |

### 2.3 Would I take a different approach?

The goal stays the same, with four changes to how it's built:

1. **Adapter, not reimplementation.** A native Rust client is appealing, since the README says
   commands are "native Rust by default", and the protocol is small: one form POST for auth and
   one JSON POST for sync. But:
   - The auth call depends on a TLS fingerprint that nobody has verified from `rustls`.
   - bob-cli has no HTTP or TLS dependencies today.
   - You would give up gkeepapi's ongoing fixes.

   bob-cli has been through this transition before: it moved from embedded shell scripts to
   native Rust once each contract settled. Do the same here. Ship v1 with an embedded, pinned
   Python adapter behind a small versioned JSON protocol. If a 1–2 hour spike shows Rust
   `perform_oauth` works, swap the adapter for Rust later with **no user-visible change**.
2. **A "pull" with a ledger, not a "migrate".**
3. **A literal renderer, not the capture grammar** (see §2.2).
4. **Long-term hedge.** If gkeepapi authentication becomes painful (for example, repeated
   `BadAuthentication`), the most robust capture bridge is an *official* API: Google Tasks (point
   Gemini/Assistant's list provider at it), or a tiny self-hosted endpoint on apollo that calls
   `bob capture`. Design the renderer and ledger around a generic "source note" model so a
   `bob gtasks` or other source can reuse them. Don't build that now.

---

## 3. Requirement Adjustments (called out explicitly)

| # | Your requirement | My adjustment | Rationale |
| --- | --- | --- | --- |
| **A1** | "Migrate **all** current inbox items" | Migrate every home note **except pinned notes and notes shared with collaborators**. Opt in with `--include-pinned` / `--include-shared` | Pinned notes are usually reference notes (Wi-Fi password, standing lists), and shared lists are living documents. "Pin it to keep it in Keep" is a rule you can remember and see in the app |
| **A2** | "Archive once we are sure the migration was successful" | Make "sure" mean: atomic write → **fsync** → re-read and parse → **scoped Git commit** of the target file → archive **only if the note's content in Keep still matches what was written** | This turns "sure" into something the code can check. The commit also gives you an undo point that isn't affected by Obsidian's live buffer |
| **A3** | Subcommand names | `pull` (not `migrate`). Plain `bob gkeep` runs `list` | It is a recurring drain. The `bob plugins` precedent. Git-like, so it reads naturally |
| **A4** | Two subcommands | Add **`doctor`** (read-only diagnostics) and **`login`** (one-time token exchange) | Auth is the most likely failure point, and your current `pass` entry may not hold a master token |
| **A5** | "Obsidian tasks" | Tasks use the capture line format, with `[created::]` set to **the Keep note's created date**, plus a `Source:` child that links to the note and carries a hidden version marker. No custom inline `[gkeep:: …]` field | Keeps when you actually had the thought. Matches `mac_inbox.md`'s `Source:` convention. Your `config.yml` notes that Tasks parsers stop at the first unknown trailing inline field, which would hide `[created::]`/`[scheduled::]` |
| **A6** | "List all items in Keep and/or tasks" | One `list` command with `-s both\|keep\|vault` (default `both`), `-a/--all` to include archived notes and done tasks, and **reconciliation states** (`new`, `pending`, `pinned`, …) | The most useful answer to "what's in Keep?" is "what will `pull` do?" |
| **A7** | — | Optionally give `gkeep_inbox.md` `type: "[[area]]"` (like `mac_inbox.md`), add it to the `capture-targets` Inbox group, and drop the stale zorg frontmatter | Status groups, badges, and picker discoverability, all consistent with `mac_inbox` |
| **A8** | — | Notes with images or drawings are migrated as text plus a visible `📎` marker linking back to Keep. Downloading the attachments into the vault can come in v2 | Archive keeps the media in Keep, so nothing is lost. Skipping these notes would block the inbox |
| **A9** | — | Automatic scheduling is **out of scope for v1**. Once you trust it, add a `bob nightly` step or an apollo systemd timer (single host) | Build trust first. Running on one host avoids races between machines |

---

## 4. Design

### 4.1 Command surface

```text
$ bob gkeep --help
Drain your Google Keep inbox into Obsidian tasks

Usage: bob gkeep [OPTIONS] [COMMAND]

Commands:
  doctor  Check credentials, adapter, Keep reachability, and the target note
  list    List Keep inbox notes and gkeep_inbox.md tasks with pull status
  login   Exchange a browser oauth_token for a stored Google master token
  pull    Write Keep inbox notes to gkeep_inbox.md, then archive them in Keep

Running `bob gkeep` with no command runs `list`.
```

| Subcommand | Options (alphabetical; every long option has a short alias) |
| --- | --- |
| `list` | `-a, --all` (archived Keep notes and done/canceled tasks too) · `-b, --bob-dir DIR` · `-f, --format table\|json` · `-s, --source both\|keep\|vault` |
| `pull` | `-b, --bob-dir DIR` · `-C, --no-commit` · `-d, --dry-run` · `-f, --format human\|json` · `-i, --id ID` (repeatable) · `-l, --limit N` · `-n, --no-archive` · `-p, --include-pinned` · `-S, --include-shared` · `-q, --quiet` |
| `doctor` | `-f, --format table\|json` |
| `login` | `-e, --email EMAIL` · `-o, --oauth-token -` (read the token from stdin rather than a TTY prompt) |

Exit codes follow the other bob commands: `0` for success, including "nothing to pull"; `1` for a
runtime, auth, or partial failure (the output says which notes stayed in Keep); `2` for usage
errors.

### 4.2 `bob gkeep list`: one screen showing both sides

```text
$ bob gkeep
Google Keep · 4 in inbox · bryanbugyi34@gmail.com

  AGE  TYPE  STATE    NOTE
  3h   note  new      Call dentist about crown  +1 line
  1d   list  new      Hardware store  ☐ 2 ☑ 1
  2d   note  pending  Look into 529 plan options
  9d   note  pinned   Wi-Fi guest password

gkeep_inbox.md · 5 open · 2 done · ~/bob/gkeep_inbox.md

  AGE  STATUS  TASK
  2d   [ ]     Look into 529 plan options
  4d   [?]     Renew passport  ⏳ 2026-10-05
  6d   [*]     Email Sam about the trip
  6d   [ ]     Hardware store  ☐ 3
  8d   [/]     Draft blog intro

2 new · 1 pending archive · 1 pinned (stays in Keep)  →  bob gkeep pull
```

- **Keep states:**
  - `new`: not in the vault yet.
  - `pending`: already written to the vault but still active in Keep, after a crash or
    `--no-archive`. `pull` archives it without writing it again.
  - `revised`: in the vault, but edited in Keep since; `pull` writes a revision.
  - `pinned` / `shared`: skipped by default.
  - `empty`: skipped.
- Colors come from `Styler`: section titles cyan, `new` green, `pending`/`revised` yellow, skipped
  dim, failures red. Ages and counts are dim. With `NO_COLOR` or a pipe the output is plain,
  truncated to the terminal width.
- `-s vault` makes no network call and returns instantly, which suits a tmux or dash widget.
  `-s keep` skips the vault. `-f json` prints
  `{schema_version: 1, keep: {account, notes:[…]}, vault: {path, tasks:[…]}, summary}`.

### 4.3 `bob gkeep pull`: the transaction

```text
$ bob gkeep pull
Google Keep → gkeep_inbox.md · 3 to process

  ✓ Call dentist about crown        written · archived
  ✓ Hardware store                  written · archived
  ✓ Look into 529 plan options      archived (already in vault)
  · Wi-Fi guest password            skipped · pinned

ok 2 written · 3 archived · 1 skipped · vault commit 4e1f2a9
```

When something goes wrong mid-run, the output says so plainly and nothing is lost:

```text
  ✓ Call dentist about crown        written · archived
  ! Hardware store                  written · NOT archived: edited in Keep during pull
warning 1 note changed while pulling; it stays in Keep and `bob gkeep pull` will add the revision
```

**Pipeline (each step can be repeated safely):**

1. **Lock.** Take the shared `bob_sync.lock`, so `pull` never runs concurrently with itself,
   `vault-sync`, `nightly`, or `task-status-hooks`.
2. **Snapshot.** The adapter's `snapshot` operation returns every non-trashed note using the
   cached incremental state. bob applies a hard timeout (for example 120 s) and shows a spinner
   on TTYs.
3. **Plan (pure function).** Classify each home note as `new`, `pending`, `revised`, or
   `skipped(reason)` by scanning the vault's `Source:` markers (§4.5). Apply `--id` and
   `--limit`. Order the notes by Keep `created` ascending, so the inbox reads oldest to newest.
   `--dry-run` stops here and prints the plan plus the exact Markdown it would write.
4. **Write.** Insert the rendered blocks under `## Tasks` using capture's `insert_task_line`
   rules. Compare-and-swap against the file hash read in step 3 (if Obsidian changed the file
   meanwhile, re-plan once, then abort). Write atomically (temp file + rename) and **fsync the
   file and its directory**. The existing `atomic_write` doesn't fsync, so add a durable variant.
5. **Verify.** Re-read the file from disk and parse it with bob's own task parser. Every `new` or
   `revised` note must appear as a `#task` block whose bytes match the render and whose marker
   matches. Anything that doesn't verify is dropped from the archive set, and the command exits 1.
6. **Commit** (default when the vault is a Git repo; `-C` skips it). Stage only
   `gkeep_inbox.md` and commit as `bob gkeep pull: 2 notes` without pushing; `vault-sync` pushes.
   This follows the `move-done-tasks` scoped-commit precedent.
7. **Guarded archive.** The adapter's `archive` operation receives
   `[{id, expect: canonical_content}]`. It syncs, re-reads each note, and **archives only notes
   whose canonical content equals `expect`**. It then syncs again and confirms
   `isArchived == true`. Each note gets a result: `archived`, `changed`, `missing`, or `error`.
8. **Report.** Print the human summary or JSON
   (`schema_version: 1`, per-note `action`, `archived`, `vault_line`, `commit`). If the vault
   isn't a Git repo, the report says there was no commit.

**Core invariant:** *A Keep note is archived only when its current content fingerprint exactly
matches a task block that is fsynced, verified, and committed in the vault.*

**Failure matrix:**

| Failure point | State afterwards | Next `pull` |
| --- | --- | --- |
| Auth or network failure in step 2 | Nothing changed | Clear error with a hint (`bob gkeep doctor` / `bob gkeep login`), exit 1 |
| Crash or error during steps 3–5 | File unchanged (atomic write) | Normal run |
| Crash after step 5 or 6, before step 7 | Tasks in vault, notes still active in Keep | Shown as `pending`, so archive-only. **No duplicates** |
| Partial failure in step 7 | Some notes archived | The rest are `pending` |
| Note edited on the phone mid-run | Vault has the old version, note still active | The guard refuses to archive. The next run writes a *revision*, then archives. **A duplicate is preferred over losing data** |
| `pull` on apollo and the Mac at the same moment | The lock is per host | Possible duplicate, which `list` flags because the same id and version appear twice. Run automated pulls on one host only |

### 4.4 Rendering: Keep note → Obsidian task

These rules are a pure, golden-tested function. Keep text is always treated **literally**.

**Untitled text note** (the most common kind of phone capture):

```markdown
- [ ] #task Call dentist about crown [created::2026-09-27]
  - They close at 5 on Fridays
  - Source: [Google Keep](https://keep.google.com/#NOTE/1Wx4zj…) · 2026-09-27 21:14 %%gkeep:1Wx4zj…:3f9c2e1d0a7b%%
```

**Titled checklist:**

```markdown
- [ ] #task Hardware store [created::2026-09-26]
  - [ ] wood screws
    - [ ] #8 × 1¼"
  - [ ] wall anchors
  - [x] sandpaper
  - Source: [Google Keep](https://keep.google.com/#LIST/…) · 2026-09-26 08:02 %%gkeep:…:9b1e…%%
```

**Rules:**

- **Task text** is the title if there is one, otherwise the first non-blank text line, otherwise
  `Untitled Google Keep list (N items)` / `Google Keep image note`. Whitespace is normalized. Long
  text is **never** truncated or split heuristically, because staying faithful beats being clever.
- **Children:**
  - Remaining text lines become one child bullet each, with blank lines dropped. Existing `- `,
    `* `, and `• ` markers are stripped so bullets aren't doubled.
  - List items become `- [ ]` / `- [x]` children, preserving Keep's one indentation level. They
    have no `#task`, so the Tasks global filter keeps them as plain checkboxes, matching the May
    dump.
  - Attachments become `- 📎 1 image · 1 drawing stay in Google Keep` plus any OCR
    `extracted_text` as a quoted child.
  - Labels are appended to the Source line (`· 🏷 errands`). Mapping labels to tags or routes
    should be an explicit config map in v2 and never automatic.
- **Status** is Ready (`[ ]`). Keep reminders aren't synced by gkeepapi, so v1 doesn't guess a
  schedule.
- **Escaping:** Keep text is data, not Markdown instructions.

  | Keep text | Risk in the vault | Rule |
  | --- | --- | --- |
  | `#task` anywhere | Creates phantom Tasks tasks | `\#task` |
  | trailing ` ^abc` | Becomes a block ID | `\^abc` |
  | `%%` | Opens a hidden comment and swallows the text after it | `\%\%` |
  | `key:: value`, `[key:: value]`, `(key:: value)` | Become Dataview fields on the task | `\:\:` |
  | leading `#`, `>`, `1.`, `|` on a child line | Heading, quote, list renumbering, or table | Backslash-escape the leading character |
  | `\r`, tabs, zero-width characters | Break the block structure | Normalize |
  | `[[wikilinks]]`, URLs | Intended by you | Keep as-is (Obsidian autolinks URLs) |

### 4.5 Identity and idempotency: the vault is the ledger

- The `Source:` child is the durable identity. It shows a link and the Keep timestamp, and hides
  a machine marker in an Obsidian comment: `%%gkeep:<keep-id>:<fp12>%%`. The comment is invisible
  in Live Preview and Reading view.
- `fp12` is the first 12 hex characters of a SHA-256 over canonical JSON of
  `{title, text, items:[[checked, indent, text]…]}`. The Rust side computes it, and the adapter
  only compares canonical content structurally, so the canonicalization lives in one place.
- The dedupe scan covers **the whole vault**, including `done/`. A task keeps its `Source:` child
  when you move it to another note during triage or when `move-done-tasks` archives it, so the
  scan still finds it:
  - Same `(id, fp)` in the vault → `pending` (archive only).
  - Same `id` but a different `fp` → `revised`. Write a new block whose Source line says
    "revised after earlier pull", then archive.
  - Not found → `new`.
- The vault syncs through Git, so this works across apollo and the Mac without any local state.
  An optional append-only local journal (`$XDG_STATE_HOME/bob-cli/gkeep/journal.jsonl`) can keep
  an audit trail, but correctness shouldn't depend on it.
- **Simpler fallback, if you dislike the hidden comment:** use the id alone, taken from the URL.
  You lose `revised` detection, and a note edited after a failed archive would be archived with
  only its old content in the vault. I recommend keeping the marker.
- **Spike item:** confirm which id Keep's web URL expects. gkeepapi builds `note.url` from `id`,
  but public examples show long server-style ids (`#NOTE/1Wx4zj…`). Store whichever one opens
  the note, and put both in the marker if needed.

### 4.6 Architecture

```text
bob gkeep (Rust)                                   embedded, pinned Python adapter
┌──────────────────────────────────────────┐       ┌───────────────────────────────┐
│ gkeep/mod.rs      clap CLI, dispatch      │ stdin │ scripts/gkeep_adapter.py      │
│ gkeep/config.rs   config.yml [gkeep], env │ JSON  │ # /// script (PEP 723)        │
│ gkeep/adapter.rs  spawn, timeout, errors ─┼──────►│ # deps: gkeepapi==0.17.1,     │
│ gkeep/model.rs    KeepNote, canonical, fp │◄──────┼ #       gpsoauth==2.0.0       │
│ gkeep/render.rs   note → Markdown (pure)  │ stdout│ ops: snapshot | archive |     │
│ gkeep/plan.rs     new/pending/revised     │ JSON  │      exchange | ping          │
│ gkeep/ledger.rs   vault-wide marker scan  │       │ cache: $XDG_CACHE_HOME/       │
│ gkeep/pull.rs     lock→write→fsync→verify │       │   bob-cli/gkeep/state.json    │
│                   →commit→guarded archive │       │   (0600, gkeepapi dump)       │
│ gkeep/list.rs     tables + JSON           │       └───────────────────────────────┘
└──────────────────────────────────────────┘        run: uv run --quiet --script <path>
reuses: capture::insert_task_line, ob::try_acquire_lock, style::Styler,
        embedded-asset extraction (runner.rs), config.rs, BOB_NOW
```

- **Adapter protocol, version 1.** One JSON request on stdin and one JSON response on stdout.
  Logs go to stderr, and the token never goes in argv or logs.
  - `snapshot`: request `{email, master_token, device_id, state_path}`, response
    `{account, notes:[{id, server_id, kind, title, text, items, pinned, archived, trashed, shared,
    labels, attachments, created, edited, url}]}`.
  - `archive`: request `{notes:[{id, expect}]}`, response `{results:[{id, status, detail}]}`.
  - `exchange`: request `{email, oauth_token, device_id}`, response `{master_token}`.
  - Errors are typed (`auth`, `network`, `rate_limit`, `protocol`, `resync_required`), so the Rust
    side can print targeted guidance such as "token looks like an oauth_token; run
    `bob gkeep login`".
- **Why `uv run --script`:** the dependencies are declared inside the file (optionally with
  `exclude-newer` or a `.lock` for reproducibility). Environments are cached and built
  atomically, and you get no hand-managed venv (compare the `pybash` breakage in §1.1). It
  needs Python ≥3.10, and `uv` is already on both machines.
- **Test hook:** `BOB_GKEEP_ADAPTER` overrides the adapter command, the same idea as
  `BOB_CLIPBOARD_CMD`. Integration tests in `tests/cli.rs` then drive `list` and `pull` through a
  fake adapter that serves fixture JSON. That fake can also simulate crashes, `changed` results,
  and auth errors. With `BOB_NOW` the tests are fully deterministic. No new Rust crates are
  needed: `serde_json`, `sha2`, and `chrono` are already dependencies.

### 4.7 Auth and configuration

```yaml
# ~/.config/bob/config.yml
gkeep:
  email: bryanbugyi34@gmail.com
  token_command: pass show gkeep/master_token      # any command that prints the master token
  token_store_command: pass insert -m -f gkeep/master_token   # used by `bob gkeep login`
  device_id: 3f9c0a1b2c3d4e5f                       # hex; reused on every host
  target: gkeep_inbox.md
  skip: [pinned, shared]
```

Environment overrides would be `BOB_GKEEP_EMAIL`, `BOB_GKEEP_TOKEN_COMMAND`, `BOB_GKEEP_ADAPTER`,
and `BOB_GKEEP_STATE_DIR`. They should be documented in the README "Environment" section, like
every other bob variable.

```text
$ bob gkeep login
1. Open https://accounts.google.com/EmbeddedSetup and sign in as bryanbugyi34@gmail.com.
2. Click "I agree", then copy the `oauth_token` cookie (starts with oauth2_4/).
Paste oauth_token: ••••••••
✓ exchanged for a master token (aas_et/…)
✓ stored via: pass insert -m -f gkeep/master_token
✓ Google Keep reachable · 4 notes in inbox

$ bob gkeep doctor
Google Keep doctor

  ✓ config    ~/.config/bob/config.yml · gkeep
  ✓ account   bryanbugyi34@gmail.com · device 3f9c…
  ✓ token     pass show gkeep/master_token · master token (aas_et/…)
  ✓ adapter   uv · gkeepapi 0.17.1 · gpsoauth 2.0.0
  ✓ keep      reachable · 4 in inbox · state cache 2m old
  ✓ vault     ~/bob/gkeep_inbox.md · Tasks section found
  ! vault     gkeep_inbox.md has no type frontmatter (status groups off)
```

`doctor` recognizes token *shapes*: `oauth2_4/` means "exchange me", and `aas_et/` means a master
token. It never prints the token itself. For unattended runs, it also warns when `token_command`
needs an interactive gpg pinentry.

---

## 5. Rollout Plan

| Phase | Deliverable | Exit criteria |
| --- | --- | --- |
| **0. Spike (≈1–2 h)** | Check what `gkeep_oauth_token` holds (re-exchange if it's a cookie). Run a throwaway adapter `snapshot`. Confirm which id opens `keep.google.com/#NOTE/<id>`. Archive and unarchive one test note. Optionally try `perform_oauth` from Rust with `ureq`/`rustls` | Snapshot JSON of your real inbox. The archive round trip is confirmed |
| **1. Read-only** | `doctor`, `list` (Keep and vault), config and token plumbing, embedded adapter `snapshot`, state cache | `bob gkeep` prints both tables. JSON tests pass with the fake adapter |
| **2. Plan and render** | `pull --dry-run`: the pure planner, renderer, escaping, and vault marker scan | Golden tests for every note shape. The dry run on your real inbox looks right |
| **3. Write path** | Lock, compare-and-swap, durable atomic write, verify, scoped commit, `--no-archive` | Crash-injection tests show no partial files and no duplicates |
| **4. Guarded archive** | Adapter `archive` with `expect`, post-archive confirmation, result reporting | The fake adapter's `changed`/`missing`/`error` paths each behave as in §4.3 |
| **5. Polish** | `login`, README section and `docs/gkeep.md` contract, the `gkeep_inbox.md` frontmatter tweak, capture-targets Inbox entry | `just all` passes. The help output follows `cli_rules.md` |
| **Later** | `bob nightly` step or apollo timer · attachment download · explicit label→tag map · opt-in routing-only grammar (`@route`, `s:N`, `p:N`, never Pomodoro markers) for Keep notes labeled `bob` · optional `restore <id>` (unarchive) · native Rust adapter if the spike succeeded | — |

**First real run:** the May 2026 dump used Google-Docs numbering (`[gkeep:: 2.a44]`), not Keep ids,
so those tasks can't be deduplicated automatically. If any of those Keep notes are still active in
Keep, look at `bob gkeep list` and `pull --dry-run` first and archive the leftovers by hand (or
use `pull -i`) before the first full pull.

---

## 6. Open Questions for You

1. Do you use **pins** or **shared lists** (for example, family groceries) in Keep home? That
   decides whether the A1 defaults fit your habits.
2. Should a checklist become **one task with checkbox children** (the default, matching the May
   dump) or **one task per unchecked item**? That could be an opt-in `--split-lists` later.
3. Does `pass` on apollo unlock without a prompt (gpg-agent cache or a dedicated subkey)? That
   decides whether automation (A9) can run unattended.
4. Is a scoped vault commit before archiving acceptable, or do you want commits left entirely to
   `vault-sync` (`-C` by default)?
5. Should `keep-cli` stay as your ad-hoc Keep power tool? If so, point its auth at the same
   `pass` entry so you have one credential and one `device_id`.

---

## 7. Recommended Solution

1. **Add `bob gkeep` with `list` (the default), `pull`, `doctor`, and `login`**, following the
   `bob plugins` CLI conventions and `cli_rules.md`.
2. **Talk to Keep through gkeepapi 0.17.1 / gpsoauth 2.0.0 in a small embedded PEP 723 adapter
   run by `uv run --script`,** behind a versioned JSON-over-stdin protocol with typed errors and a
   `BOB_GKEEP_ADAPTER` test override. Cache gkeepapi state for fast incremental syncs. Pass the
   master token (from `token_command`, default `pass show gkeep/master_token`) on stdin, and use
   one persisted `device_id` everywhere. Revisit a native Rust client only after a successful TLS
   spike.
3. **Keep everything you see and everything safety-critical in Rust:** a literal renderer (never
   the capture grammar) with explicit escaping; tasks in the capture line format with the Keep
   created date; a `Source:` child with a Keep link and a hidden `%%gkeep:<id>:<fp>%%` marker;
   insertion under `## Tasks` using capture's rules.
4. **Make `pull` a lock-protected transaction:** snapshot → pure plan → compare-and-swap atomic
   write → fsync → re-read verify → scoped Git commit → **content-guarded archive** →
   confirmation. The vault is the ledger (`new` / `pending` / `revised`). Pinned and shared notes
   are skipped by default. `--dry-run` shows the exact Markdown. A duplicate is preferred over
   losing data.
5. **Make `list` a reconciliation view** of both sides (`-s both|keep|vault`) with the pull
   status of each note, a styled table by default, and `schema_version: 1` JSON.
6. **Ship it in phases** (spike → read-only → dry-run → write → archive → polish). Once a few
   weeks of manual runs have gone cleanly, add the drain to `bob nightly` or an apollo-only timer
   so phone captures reach Obsidian on their own.

---

## Sources

- Google Keep API, Note resource and methods (no archive field; create/delete/get/list only):
  <https://developers.google.com/workspace/keep/api/reference/rest/v1/notes>
- Google Keep API overview (Workspace/enterprise scope):
  <https://developers.google.com/workspace/keep/api/guides>
- Google community thread on Keep API access for non-Workspace users:
  <https://support.google.com/docs/thread/256969151/will-the-google-keep-api-ever-become-accessible-to-non-workspace-users?hl=en>
- gogcli README (Keep is Workspace-only through a service account):
  <https://github.com/steipete/gogcli?tab=readme-ov-file>
- gkeepapi on PyPI (0.17.1, 2026-01-05; Python ≥3.10): <https://pypi.org/project/gkeepapi/>
- gkeepapi documentation (master-token auth, `find`, archive, `dump`/`restore`):
  <https://gkeepapi.readthedocs.io/en/latest/>
- gkeepapi source, opened as an external repo at `1a94b25`: `src/gkeepapi/__init__.py`
  (`changes` endpoint, `APIAuth.refresh`, 429 backoff, `_sync_notes`) and `src/gkeepapi/node.py`
  (`isArchived`, `url`, blob types). Commit `855be68` is "Issue #181: Dont change edit date when
  archiving/pinning".
- gkeepapi issues: #174 slow master-token auth
  <https://github.com/kiwiz/gkeepapi/issues/174>; #180 `LoginException: Unknown` from a
  non-master token <https://github.com/kiwiz/gkeepapi/issues/180>; open issue list
  <https://github.com/kiwiz/gkeepapi/issues>
- gpsoauth README, alternative `oauth_token` → `exchange_token` flow:
  <https://github.com/simon-weber/gpsoauth>. Source opened as an external repo at `429b7f9`:
  `gpsoauth/__init__.py` (cipher pinning, ALPN suppression, `OP_NO_TICKET`, `perform_oauth` form
  fields).
- Go port status (a stub: list only, no archive):
  <https://pkg.go.dev/github.com/kjedeligmann/gkeepapi>
- Keep note URL format example: <https://notes.joeldare.com/linking-google-keep-notes>
- Local evidence (read-only unless noted): `~/bob/gkeep_inbox.md`, `~/bob/legacy_gkeep_notes.md`,
  `~/bob/gkeep_gdocs_inbox_dump.md` (plus its first vault commit `2557d3cc`),
  `~/bob/mac_inbox.md`, `~/bob/.obsidian/plugins/obsidian-tasks-plugin/data.json`,
  `~/.config/bob/config.yml`, chezmoi `home/lib/keep_cli/` (commit `3a20457d`) and
  `home/bin/executable_keep-cli`, and `keep-cli auth status` on apollo (its `pybash` venv was
  rebuilt as a side effect). bob-cli sources: `src/runner.rs`, `src/scripts.rs`,
  `src/native/{plugins,style,ob,collect_done,capture}.rs`, `README.md`, `docs/capture.md`, and
  SASE memory `cli_rules.md`.
