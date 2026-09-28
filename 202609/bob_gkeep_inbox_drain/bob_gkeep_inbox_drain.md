# `bob gkeep`: Draining the Google Keep Inbox into Obsidian Tasks

- **Lead researcher:** consolidated report (lead + 5-researcher swarm)
- **Date:** 2026-09-28
- **Inputs:** [`__cdx`](bob_gkeep_inbox_drain__cdx.md) (Takeout-first migration),
  [`__cld`](bob_gkeep_inbox_drain__cld.md) (recurring pull, embedded adapter),
  [`__grk`](bob_gkeep_inbox_drain__grk.md) (pull via existing `keep-cli`),
  [`__mus`](bob_gkeep_inbox_drain__mus.md) (Takeout first, live sync second),
  [`__gem`](bob_gkeep_inbox_drain__gem.md) (decoupled backend, pinned-note protection), plus
  my own checks of the vault, `bob-cli`, `~/lib/keep_cli`, gkeepapi `1a94b25`, and the
  gkeepapi issue tracker.
- **Request:** Design a `bob gkeep` command that moves every Google Keep inbox note
  (`keep.google.com/#home`) into Obsidian tasks in `~/bob/gkeep_inbox.md`, archives each note
  in Keep once the move is known to have worked, and lists Keep items and/or those tasks.
  Critique the plan, adjust the requirements where that's justified, and recommend a solution.

---

## 0. Bottom Line

**Build it, as a daily inbox drain (`bob gkeep pull`) rather than a one-time migration.** You
already do this job by hand. `gtd_daily.md` has a daily repeating task, *"Import inbox tasks
from Google Keep"*. This morning (09:17–09:18) you moved the old content of `gkeep_inbox.md`
into a new `legacy_gkeep_notes.md` and left a stub that says *"The tasks below are pulled in
by the `bob gkeep` command."* The Google Docs overflow note and the May 2026 Keep dump show
what happens when the manual process falls behind.

Five decisions shape the design:

1. **Talk to Keep through gkeepapi, the unofficial client. No other route can do the job.**
   The official Keep API is only for Workspace administrators, and it has no archived field
   and no archive operation. Google Takeout can't archive and can't run every day. Browser
   automation is fragile.
2. **Rust owns everything you see and everything that affects safety.** That means rendering,
   vault writes, verification, the archive decision, and all output. A small, pinned Python
   adapter embedded in `bob` and run with `uv run --script` owns only the Keep protocol. It
   replaces your existing `keep-cli` for this job; §2 explains why `keep-cli` isn't used as is.
3. **Archive a note only if its current content is provably in the vault.** The write must
   be atomic, fsynced, re-read, and verified, and the archive call must refuse any note that
   changed in Keep during the run.
4. **The vault itself is the ledger.** Every migrated task gets a `Source:` child line, the
   same convention `mac_inbox.md` uses, with a hidden `%%gkeep:…%%` marker. Re-runs are
   therefore idempotent, even across machines.
5. **Safe defaults.** Pinned and shared notes stay in Keep unless you pass a flag. The first
   runs go dry-run, then no-archive, then normal.

**Command surface:** `bob gkeep [doctor | list | login | pull]`. Running `bob gkeep` with no
subcommand runs `list`, the same as `bob plugins`.

---

## 1. Evidence

### 1.1 The vault already runs this workflow by hand

| Finding | Evidence | Consequence |
| --- | --- | --- |
| Daily manual import | `~/bob/gtd_daily.md:16`: `- [ ] #task Import inbox tasks from Google Keep [repeat:: every day when done]` | The command will run **daily**. Design for a recurring drain. |
| Target note prepared today | Vault commits `70fc35cd…d2d1c60d` (2026-09-28 09:17–09:18, `kellys-mbp`) moved the legacy zorg text into a new `legacy_gkeep_notes.md` and left `gkeep_inbox.md` = intro bullets + an empty `## Tasks` | The destination and insertion point are settled. (grk said this sentence came from the zorg conversion. It was actually written this morning.) |
| `gkeep_inbox.md` is not an area note | Its frontmatter still has `generated_from_zorg`/`zorg_*` and no `type:`. `mac_inbox.md` has `type: "[[area]]"`, `id`, `done_tasks` | Without a `type`, `task-status-hooks` gives it no status groups or badges, and `capture-targets` doesn't list it (R8). |
| Earlier conversions and overflow | `legacy_gkeep_notes.md` (`@FRESHNESS` "clear my #gkeep inbox daily", "copy Keep to GDocs when backed up"). `gkeep_gdocs_inbox_dump.md` (converted 2026-05-29, `source: google_keep`, ~73 checkbox lines at first commit, now a `wip` project with one task left) | This is the failure mode automation fixes. The dump used a `[gkeep:: 2.a44]` inline field, so those tasks can't be deduplicated against Keep ids. |
| A gkeepapi CLI already exists | `~/lib/keep_cli/main.py` (1,080 lines, chezmoi, pins `gkeepapi==0.17.1`, `gpsoauth==2.0.0`, `keyring==25.7.0`): `auth`, `inbox`, `archive`, `backup`, `show`, … | Proves the building blocks, but see §2 (row 3) for why `bob` shouldn't depend on it directly. |
| Credential state | `pass` has `gkeep_oauth_token.gpg` (2026-09-03). `keep-cli` stores tokens in Python `keyring`, which has no backend on headless apollo (cld ran `keep-cli auth status`) | Store the token in `pass`. The entry's *name* suggests the short-lived `oauth2_4/…` cookie, not a master token (`aas_et/…`), so check this in the spike. |
| Tasks settings | `globalFilter: "#task"`, `taskFormat: "dataview"`. `~/.config/bob/config.yml` notes that Tasks parsers read trailing inline fields right to left and **stop at the first unknown one** | Don't put a custom `[keep_id:: …]` field on the task line (mus and gem proposed one). It would hide `[created::]`/`[scheduled::]` from Tasks, `bob query`, and the dash. |

### 1.2 Ways to talk to Keep

| Route | Consumer Gmail | Sees Home vs Archive | Can archive | Verdict |
| --- | --- | --- | --- | --- |
| Official Keep API (`keep.googleapis.com/v1`) | No. Enterprise admin with domain-wide delegation; consumer OAuth is *Won't Fix* (issuetracker 210500028) | No. The `Note` resource has no `archived`/`pinned`; the list filter has only create/update/trash time and `trashed` | No. Only `create/get/list/delete`, and `delete` is permanent | **Ruled out** (all five reports agree) |
| Data Portability API | Keep isn't a published resource group | — | No | Ruled out. Check again later. |
| Google Takeout | Yes; the export includes pinned/archived, labels, list items, attachments | Snapshot only | No | Fine for a one-off backfill or a disaster fallback. **Not usable for a daily drain.** |
| **gkeepapi 0.17.1** (private Android sync protocol) | Yes | Yes (`find(archived=False, trashed=False)`) | Yes (`note.archived = True; keep.sync()`) | **Use it, behind an adapter** |
| Browser automation (Playwright/CDP) | Yes | Via the DOM | Via the DOM | Rejected. The DOM is fragile and there are MFA/risk challenges. Chrome 136+ refuses to automate the default profile (cdx). gem's claim that it "can't get the account banned" is unsupported. |
| Google Tasks (switch the phone inbox) | Yes, official OAuth API | — | "Complete" | The best *long-term hedge* if gkeepapi auth becomes painful (§3.2). |

### 1.3 gkeepapi facts that shape the design (verified in source and issues)

- **Maintenance is active.** mus says upstream is stale; that's wrong. 0.17.1 shipped on
  2026-01-05. #181 (archiving no longer changes the edited date) was fixed in 2025-11, and the
  #189 auth thread was resolved in 2026-03.
- **Authentication:**
  - Password and app-password login has failed since about 2026-01-31 (#189).
  - A master token `aas_et/…` works and does not expire.
  - The `oauth2_4/…` cookie from `accounts.google.com/EmbeddedSetup` is single-use and must
    be *exchanged* for a master token.
  - Passing the cookie straight to `authenticate()` fails with `LoginException` (#180/#189).
  - The master token can mint OAuth tokens for the whole account, so treat it like a
    password.
- **Device id:**
  - `authenticate()` defaults `device_id` to the host's MAC address, so apollo and the Mac
    would register as different devices.
  - Persist one hex `device_id` in config.
  - `keep-cli` doesn't do this.
- **Note ids contain a dot.** `_generateId` produces `"{ms:x}.{rand:016x}"`, and server-side
  ids differ from these. A dot is **not** a legal Obsidian block-ID byte (`is_block_id_byte` =
  `[A-Za-z0-9-]`). grk's proposed `^gk-<keep-id>` block ID therefore doesn't work as written.
- **URL:** `note.url` is `https://keep.google.com/u/0/#NOTE|LIST/<id>` built from the client
  `id`. Whether that link opens the note on the web, or whether `server_id` is needed, is a
  spike item (cld).
- **What the protocol exposes:**
  - Home is `archived == False && trashed == False` and includes pinned notes.
  - `deleted` nodes must be filtered out.
  - Lists have `checked` items with one level of `indented` nesting.
  - Image and drawing blobs carry OCR `extracted_text`. `Keep.getMediaLink(blob)` can download
    media.
- **Known losses:**
  - Reminder sync is commented out in `Keep.sync()`, so reminders aren't trustworthy.
  - Keep's 2025 rich-text formatting isn't exposed; text comes back plain (#177, still open
    2026-08).
  - These gaps are why **archive, never delete**. The original stays in Keep.
- **Performance:**
  - Every `authenticate()` pulls the whole tree, including archived notes, which can be slow
    (#174).
  - `dump()`/`authenticate(..., state=…)` makes later syncs incremental.
  - `keep-cli` doesn't use this and logs in again for every command.

### 1.4 bob-cli plumbing to reuse (and the gaps)

- **Reuse:**
  - `bob plugins` dispatches `None => run_list` (default subcommand).
  - `Styler`: color plus `NO_COLOR`/TTY handling.
  - `schema_version: 1` JSON outputs.
  - `ob::try_acquire_lock` (shared `bob_sync.lock`).
  - capture's `format_task_line` (`- [ ] #task <body> [created::YYYY-MM-DD]`) and
    `insert_task_line` (under `## Tasks`).
  - `note_tasks::scan` for parse-back.
  - `sha2`, `serde_json`, `chrono`, and `fs2` are already dependencies.
  - `BOB_*_CMD`-style test overrides.
- **Gaps:**
  - `collect_done::atomic_write` does temp + rename but **no fsync**, so add a durable variant.
  - bob-cli has **no Python and no HTTP stack** today. The README says native commands don't
    need Bash/Perl. Embedded assets exist (`scripts.rs` `SUPPORT_ASSETS`, extracted to the
    cache dir), so shipping a `.py` asset is cheap, but it adds a runtime dependency on `uv`
    that `doctor` must check.
- **Per `cli_rules.md`:**
  - Keep subcommands and options sorted.
  - Give every public long option a short alias.
  - Write excellent `--help`.
  - Prefer color.
- **Existing `--format` values:** `human|json` for action commands and `table|json` for list
  views.

---

## 2. Where the Reports Disagreed, and How I Resolved It

| # | Question | Positions | Resolution |
| --- | --- | --- | --- |
| 1 | One-time migration or recurring drain? | cdx, mus: one-way migration utility. cld, grk: daily drain. gem: daily. | **Daily drain.** The `gtd_daily.md` recurring task settles it. |
| 2 | Primary backend | cdx, mus: Takeout first, live later. cld, grk, gem: gkeepapi. | **gkeepapi.** Takeout's hours of latency and inability to archive make the requested workflow impossible every day. Keep Takeout as a *documented fallback*, not v1 code (§3.2). cdx's policy concern is legitimate. At this scale it is a personal account-risk choice, and §4.7 limits the exposure. |
| 3 | Where the Keep code lives | cld: embedded PEP 723 adapter under `uv`. grk: shell out to existing `keep-cli`. gem: venv bridge (or CDP). | **Embedded adapter owned by bob-cli** (§4.6), with `BOB_GKEEP_ADAPTER` as an override. `keep-cli` as is logs in and syncs the full tree **once per archived note**, can't check content before archiving, has no persisted `device_id` or state cache, and uses a keyring that's broken on apollo. Its contract also lives in another repo (chezmoi), so it would drift from bob's. grk's own list of required `keep-cli` upgrades is most of an adapter anyway. Keep `keep-cli` as your ad-hoc power tool, pointed at the same `pass` token and `device_id`. |
| 4 | Identity marker | mus, gem: inline `[keep_id::]`. grk: `^gk-<keep-id>` block ID + `#gkeep` tag. cdx: digest block ID + HTML comment. cld: `Source:` child with `%%gkeep:<id>:<fp>%%`. | **cld's `Source:` child.** An inline field breaks Tasks parsing (§1.1). Raw ids aren't legal block IDs (§1.3). A hashed block ID is opaque noise on the line you read most. The `Source:` line matches `mac_inbox.md`, travels with the task when triage moves it, and carries a content fingerprint that enables the archive guard. No `#gkeep` tag, because the `Source:` line already records provenance. |
| 5 | Archive default | cld, grk, gem: automatic after verification. mus: opt-in `--archive` per run. cdx: separate command with the user doing Select All + Archive. | **Automatic after verification**, which is what you asked for. Trust is built by a staged first run (`--dry-run` → `--no-archive` → normal), not by adding friction every day. cdx's guided manual archive is reasonable only if the adapter fails. |
| 6 | Pinned notes | cld, grk, gem, mus: skip by default. cdx: include (Home literally includes them). | **Skip pinned and shared by default** and show them in `list`/`pull` as `pinned`/`shared` (R2). This is an explicit adjustment; see open question 1. |
| 7 | Keep labels | grk, mus: turn into `#tags`. cdx, cld: metadata only. | **Metadata on the `Source:` line.** A label like `errands` silently becoming a Bob tag changes meaning and may collide with `#car`/`#dad` conventions. Add an explicit `label_tags:` map later if you want it. |
| 8 | Checked checklist items | gem: drop them. Others: keep as `[x]`. | **Keep `[x]`.** Dropping is lossy, and the note is archived afterwards. |
| 9 | Attachments | cdx: copy + hash, or block. grk: download, else leave in Keep. cld, mus: placeholder. | **v1: a `📎` child line linking to the Keep note plus any OCR `extracted_text`.** Archive keeps the media, so nothing is lost. **v1.1:** download images into `img/gkeep/` via `getMediaLink`. |
| 10 | Vault commit before archive | cld: scoped commit (the `move-done-tasks` precedent). Others: silent. | **Commit by default when the vault is a Git repo** (`-C/--no-commit` to skip). It's an undo point that doesn't depend on Obsidian's buffer. Open question 4. |
| 11 | Hold the vault lock across network calls? | cld: lock first. grk: don't hold it across Keep calls. | **grk.** Fetch Keep before taking the lock, hold `bob_sync.lock` only for plan → write → verify → commit, then archive after releasing it. A separate `gkeep.lock` stops two pulls from running at once. |
| 12 | Automation | All: not in v1. | Agreed. Once it's trusted, run it from an **apollo-only** timer or `bob nightly`. grk's worry that a note captured at 11 pm vanishes before morning triage doesn't apply, because it lands in the vault. |

Other corrections:

- gem's mockups show gkeepapi `v0.14.4`; the current version is 0.17.1.
- mus maps Keep reminders to `tick::`. That's a legacy zorg field, and gkeepapi doesn't sync
  reminders anyway.
- mus proposed a separate `import` subcommand and per-run `--archive`. Both add surface area
  without adding safety.

---

## 3. Critique and Requirement Adjustments

### 3.1 Is this a good idea?

**Yes.** It automates a daily ritual that already exists and keeps falling behind. Keep stays
the zero-friction phone capture surface, and Obsidian stays the system of record. Archive is
the right terminal action: it's reversible, searchable, and keeps the media.

It's **only** a good idea with these conditions, which all five reports agree on:

- Archiving is gated on a verified vault write.
- Re-runs are idempotent.
- Pinned, shared, and media-heavy notes are never silently swallowed.
- Keep text is never interpreted as `bob capture` grammar. This is cld's catch: a Keep note
  that reads `=x` would close your running Pomodoro, `+5` would extend it, `%` would paste
  the clipboard, and `@x` would reroute the note. `pull` must use a **literal renderer**.

The dominant risk isn't the Markdown. It's **auth and the private protocol**. mus is right
that token setup, storage, and diagnostics will be more code and more support than the
migration logic, so budget for `login` and `doctor` from day one.

### 3.2 Would I take a different approach?

Only at the edges:

- **Long-term hedge.** If gkeepapi auth becomes a recurring chore, the most robust bridge is
  an *official* consumer API. Point phone capture (widget, Gemini/Assistant lists) at
  **Google Tasks**, or at a small capture endpoint on apollo that calls `bob capture`, and
  retire Keep as an inbox.
  - Design the renderer and ledger around a generic "source note" model so that a
    `bob gtasks` or a Takeout reader could reuse them. Don't build either one now.
- **Takeout fallback.** If the protocol breaks, the manual path is: Takeout → a Takeout
  reader feeding the same planner and renderer → Keep's documented Select All (`Ctrl+A`) +
  Archive (`e`) by hand. That's cdx's guided archive.
  - This keeps the feature degradable instead of dead. Leave it as a documented plan until
    it's needed.

### 3.3 Requirement adjustments (called out explicitly)

| # | Your requirement | Adjustment | Why |
| --- | --- | --- | --- |
| **R1** | A "migrate" subcommand | **`pull`**, a recurring drain | You run it daily, and the stub already says "pulled in". |
| **R2** | Migrate **all** `#home` items | All Home notes **except pinned and shared**. Opt in with `-p/--include-pinned` and `-S/--include-shared`. Empty notes are skipped. | Pinned notes are usually reference material, and shared lists are living documents. "Pin it to keep it in Keep" is a rule you can see in the app. |
| **R3** | Archive "once we are sure" | "Sure" means the **core invariant**: a note is archived only if its *current* content fingerprint matches a task block that was atomically written, fsynced, re-read, and parse-verified, and committed when the vault is Git-backed. | This turns "sure" into something the code can check. |
| **R4** | List Keep and/or vault items | One **reconciliation view**: `-s both\|keep\|vault` (default `both`). Keep defaults to Home. `-a/--all` adds archived notes and done tasks. Each note gets a state (`new`, `pending`, `revised`, `pinned`, `shared`, `empty`). | The most useful answer to "what's in Keep?" is "what will `pull` do?" |
| **R5** | Two subcommands | Add **`doctor`** (read-only diagnostics) and **`login`** (one-time token exchange). | Auth is the most likely failure point. |
| **R6** | "Obsidian tasks" (unspecified shape) | One Keep note = **one** top-level `#task` in capture's format, with `[created::]` = **the Keep created date**. Body lines and list items become children, list items without `#task`. Add a `Source:` child with the hidden marker. No custom inline fields, no automatic label → tag mapping. | Preserves when you had the thought and matches the May dump and `mac_inbox.md`. Stays safe for the Tasks parser. |
| **R7** | (unspecified) attachments | v1: text + `📎` link + OCR text. Media stays in Keep. v1.1: download. | Nothing is lost, because archive keeps the media. Blocking these notes would stall the inbox. |
| **R8** | (unspecified) target note schema | **Suggested vault change (your call):** make `gkeep_inbox.md` an area like `mac_inbox.md` (`type: "[[area]]"`, `id: gkeep_inbox`, `done_tasks: "[[done/gkeep_inbox_done]]"`), drop the stale `zorg_*` keys, and add it to the `capture-targets` Inbox group. | Status groups, badges, `move-done-tasks`, and picker discoverability. |
| **R9** | (unspecified) scheduling | No automation in v1. Later, add an apollo-only timer or `bob nightly` step, and change the `gtd_daily.md` chore to "review `gkeep_inbox`". | Build trust first. Running on a single host avoids races between hosts. |
| **R10** | (implicit) lossless | Accept, in writing, that **rich-text formatting and reminders aren't carried over** (gkeepapi limits). | Archive, never delete, so the original stays one click away via the `Source:` link. |

---

## 4. Recommended Design

### 4.1 Command surface

```text
$ bob gkeep --help
Drain your Google Keep inbox into Obsidian tasks

Usage: bob gkeep [OPTIONS] [COMMAND]

Commands:
  doctor  Check credentials, adapter, Keep reachability, and the target note
  list    Show Keep inbox notes and gkeep_inbox.md tasks with their pull state
  login   Exchange a browser oauth_token for a stored Google master token
  pull    Write Keep inbox notes to gkeep_inbox.md, then archive them in Keep

Running `bob gkeep` with no command runs `list`.
```

| Subcommand | Options (alphabetical; every long option has a short alias) |
| --- | --- |
| `doctor` | `-f, --format table\|json` |
| `list` | `-a, --all` · `-b, --bob-dir DIR` · `-f, --format table\|json` · `-s, --source both\|keep\|vault` |
| `login` | `-e, --email EMAIL` · `-o, --oauth-token -` (read from stdin; default is a hidden TTY prompt) |
| `pull` | `-b, --bob-dir DIR` · `-C, --no-commit` · `-d, --dry-run` · `-f, --format human\|json` · `-i, --id ID` (repeatable) · `-l, --limit N` · `-n, --no-archive` · `-p, --include-pinned` · `-q, --quiet` · `-S, --include-shared` |

**Exit codes:**

- `0`: success, including "nothing to pull".
- `1`: runtime, auth, or partial failure. The output names every note that stayed in Keep.
- `2`: usage error, or a missing prerequisite such as `uv`, config, or the token.

### 4.2 `bob gkeep list`: both sides on one screen

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
  6d   [ ]     Hardware store  ☐ 3

2 new · 1 pending archive · 1 pinned (stays in Keep)  →  bob gkeep pull
```

- **Keep states:**
  - `new`: not in the vault yet.
  - `pending`: already in the vault but still active in Keep, after a crash or
    `--no-archive`. `pull` archives it without writing it again.
  - `revised`: in the vault, but edited in Keep since. `pull` writes a revision.
  - `pinned` / `shared` / `empty`: skipped.
- **Styling:**
  - Section titles are cyan, `new` is green, `pending`/`revised` are yellow, skipped notes
    are dim, and failures are red.
  - The footer always ends with the next command.
  - `NO_COLOR` and piped output are plain and fit the terminal width.
- **Sources:**
  - `-s vault` makes no network call, which is fast enough for a tmux or dash widget.
  - `-f json` prints `{schema_version: 1, keep: {account, fetched_at, notes: […]}, vault:
    {path, tasks: […]}, summary}`.

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

When a note fails partway, the output says so plainly and nothing is lost:

```text
  ! Hardware store                  written · NOT archived: edited in Keep during pull
warning 1 note changed while pulling; it stays in Keep and the next pull adds the revision
```

**Pipeline:**

1. **Guard.** Take a per-host `gkeep.lock` so two pulls can't overlap.
2. **Snapshot Keep** (no vault lock held). The adapter's `snapshot` returns every
   non-trashed, non-deleted note, using the cached incremental state. Apply a hard timeout
   and show a spinner on a TTY.
3. **Lock the vault.** Take `bob_sync.lock` (`ob::try_acquire_lock`) so `vault-sync`,
   `nightly`, and `task-status-hooks` can't run at the same time.
4. **Plan (pure function).**
   - Scan the vault for `%%gkeep:%%` markers and classify each Home note.
   - Apply `--id`/`--limit`.
   - Order by Keep `created`, oldest first.
   - `--dry-run` stops here and prints the plan plus the exact Markdown it would insert.
5. **Write.**
   - Insert the rendered blocks under `## Tasks` using capture's insertion rules.
   - Compare-and-swap against the content hash read in step 4, because Obsidian doesn't
     honor bob's lock. If the file changed, re-plan once, then abort.
   - Write the temp file, **fsync it**, rename it, and **fsync the directory**.
6. **Verify.** Re-read from disk and parse with `note_tasks`. Every planned note must appear
   exactly once as a `#task` block whose bytes match the render. Any note that fails is
   dropped from the archive set, and the run exits 1.
7. **Commit** (Git vault; `-C` skips it). Stage only `gkeep_inbox.md` and commit with a
   message like `bob gkeep pull: 2 notes`. Don't push; `vault-sync` pushes. Then **release
   the vault lock**.
8. **Guarded archive.**
   - Send `[{id, expect}]` to the adapter, where `expect` is the canonical content.
   - The adapter syncs, re-reads each note, and archives it **only if its canonical content
     equals `expect`**, in one sync.
   - It syncs again and confirms `archived == true`.
   - Each note gets `archived | changed | missing | error`.
9. **Journal + report.**
   - Append to `$XDG_STATE_HOME/bob-cli/gkeep/journal.jsonl`: id, fingerprint, action,
     commit. Store no note bodies.
   - Print the human summary or `schema_version: 1` JSON.

**Core invariant:** *A Keep note is archived only when its current content fingerprint matches
a task block in the vault that was fsynced and parse-verified (and committed, when the vault is
Git-backed).*

| Failure point | State afterwards | Next `pull` |
| --- | --- | --- |
| Auth or network failure (step 2) | Nothing changed | Clear error pointing at `bob gkeep doctor`/`login`; exit 1 |
| Crash in steps 4–6 | File unchanged (atomic rename) | Normal run |
| Crash after step 6/7, before 8 | Tasks in vault, notes still in Keep | Shown as `pending` → archive only. **No duplicates.** |
| Partial archive failure | Some notes archived | The rest are `pending` |
| Note edited on the phone mid-run | Vault has the old version; the note stays in Keep | The guard refuses. The next run writes a revision, then archives. **A duplicate beats data loss.** |
| Obsidian edits the file between plan and write | Compare-and-swap detects it | Re-plans once, then aborts safely |
| Pulls on apollo and the Mac at the same moment | Per-host locks | A duplicate is possible and `list` flags it. Automate on **one host only**. |

### 4.4 Rendering: Keep note → Obsidian task (a pure, golden-tested function)

```markdown
- [ ] #task Call dentist about crown [created::2026-09-27]
  - They close at 5 on Fridays
  - Source: [Google Keep](https://keep.google.com/u/0/#NOTE/…) · 2026-09-27 21:14 %%gkeep:v1:<id>:3f9c2e1d0a7b%%

- [ ] #task Hardware store [created::2026-09-26]
  - [ ] wood screws
    - [ ] #8 × 1¼"
  - [x] sandpaper
  - Source: [Google Keep](https://keep.google.com/u/0/#LIST/…) · 2026-09-26 08:02 · 🏷 errands %%gkeep:v1:<id>:9b1e44c07a2d%%
```

**Task text:**

- Use the title. If there's no title, use the first non-blank text line. Failing both, use
  `Untitled Google Keep list (N items)` or `Google Keep image note`.
- Normalize whitespace. **Never** truncate or split heuristically.

**Children:**

- Remaining text lines become one bullet each, with existing `- `/`* `/`• ` markers
  stripped.
- List items become `- [ ]`/`- [x]` children, keeping order and Keep's one level of
  nesting.
- Attachments become `- 📎 1 image stays in Google Keep`, followed by quoted OCR text.
- The `Source:` line is always last.

**Status:** always open `[ ]`. Being moved out of an inbox is not the same as being done.
Reminders are never guessed.

**Escaping.** Keep text is data, never markup and never capture grammar:

| Keep text | Risk in the vault | Rule |
| --- | --- | --- |
| `#task` anywhere | Phantom Tasks task | `\#task` |
| Trailing ` ^abc` | Becomes a block ID | `\^abc` |
| `%%` | Hidden comment swallows the rest of the text | `\%\%` |
| `key:: value`, `[k:: v]`, `(k:: v)` | Dataview fields | `\:\:` |
| Leading `#`, `>`, `1.`, `\|` on a child line | Heading, quote, list, or table | Backslash-escape the leading character |
| `\r`, tabs, zero-width characters | Break the block structure | Normalize |
| `[[links]]`, URLs | Intended by you | Keep as is |

### 4.5 Identity and idempotency: the vault is the ledger

- **Marker:** `%%gkeep:v1:<keep-id>:<fp12>%%` on the `Source:` line. Obsidian comments are
  invisible in Live Preview and Reading view.
  - The raw id (dot included) lives inside the comment, never in a block ID.
  - Store `server_id` there too if the spike shows the URL needs it.
- **Fingerprint:** `fp12` is the first 12 hex digits of SHA-256 over canonical JSON
  `{title, text, items:[[checked, indent, text]…]}`.
  - The adapter's snapshot serializer defines the canonical shape.
  - Rust computes the hash.
  - The archive guard compares canonical JSON structurally, so hashing lives in exactly one
    language.
  - A shared golden test vector keeps the two sides aligned.
- **Classification:**
  - The marker scan covers the **whole vault**, including `done/`. Tasks keep their `Source:`
    child through triage and through `move-done-tasks`.
  - Same `(id, fp)` → `pending`.
  - Same `id` with a different `fp` → `revised`.
  - Neither → `new`.
  - The vault syncs through Git, so this works across hosts without local state.
- **Journal backstop:** the local journal is a second ledger for one case only: you deleted a
  task *and* its marker during triage while the Keep note was still unarchived. A matching
  `(id, fp)` in the journal also counts as `pending`, so the note is never re-imported.
- **First real run:** the May dump's `[gkeep:: 2.a44]` ids are Google Docs numbering, not Keep
  ids, so they can't be matched. Check `list` and `pull -d` first, and archive any leftovers
  by hand or with `pull -i`.

### 4.6 Architecture

```text
bob gkeep (Rust, src/native/gkeep/)                embedded, pinned Python adapter
┌───────────────────────────────────────────┐       ┌────────────────────────────────┐
│ mod.rs      clap CLI, dispatch (None→list)│ stdin │ scripts/gkeep_adapter.py       │
│ config.rs   [gkeep] config + env overrides│ JSON  │ # /// script (PEP 723)         │
│ adapter.rs  spawn, timeout, typed errors ─┼──────►│ # gkeepapi==0.17.1             │
│ model.rs    KeepNote, canonical form, fp  │◄──────┼ # gpsoauth==2.0.0              │
│ render.rs   note → Markdown (pure, golden)│ stdout│ ops: snapshot | archive |      │
│ plan.rs     new/pending/revised/skipped   │ JSON  │      exchange | ping           │
│ ledger.rs   vault marker scan + journal   │       │ state: $XDG_CACHE_HOME/bob-cli/│
│ pull.rs     lock→CAS write→fsync→verify   │       │   gkeep/state.json (0600)      │
│             →commit→guarded archive       │       └────────────────────────────────┘
│ list.rs     reconciliation tables + JSON  │        run: uv run --quiet --script <path>
└───────────────────────────────────────────┘
reuses: capture::{format_task_line, insert_task_line}, note_tasks::scan, ob::try_acquire_lock,
        style::Styler, scripts.rs SUPPORT_ASSETS extraction, BOB_NOW
```

**Adapter protocol v1.** One JSON request goes in on stdin and one JSON response comes out
on stdout. Logs go to stderr. The token never appears in argv or logs.

- **Operations:**
  - `snapshot`: returns `{account, notes: [{id, server_id, kind, title, text, items, pinned,
    archived, trashed, shared, labels, attachments: [{kind, extracted_text}], created,
    edited, url}]}`.
  - `archive`: takes `{notes: [{id, expect}]}` and returns `{results: [{id, status,
    detail}]}`.
  - `exchange`: takes `{email, oauth_token, device_id}` and returns `{master_token}`.
  - `ping`.
- **Error types:** `auth`, `network`, `rate_limit`, `protocol`, `resync_required`.
  - Rust uses these to print targeted guidance, such as "this looks like an `oauth2_4/`
    cookie; run `bob gkeep login`".
- **Why `uv run --script`:**
  - Dependencies are declared inside the file (add `exclude-newer` for reproducibility).
  - Environments are cached and built atomically, with no hand-managed venv. `keep-cli`'s
    `pybash` venv broke during cld's research.
  - It needs Python ≥3.10.
- **Test hook:** `BOB_GKEEP_ADAPTER` swaps in a fake adapter that serves fixture JSON and can
  simulate `changed`, `missing`, auth errors, and crashes. Together with `BOB_NOW`, the
  integration tests in `tests/cli.rs` are deterministic and never touch live Keep. **No new
  Rust crates are needed.**
- **Later:** if a short spike shows gpsoauth's `perform_oauth` works from Rust (it pins
  ciphers, disables ALPN, and needs a particular TLS fingerprint), the adapter can become
  native with no user-visible change. That's not v1.

### 4.7 Auth, secrets, and configuration

```yaml
# ~/.config/bob/config.yml
gkeep:
  email: bryanbugyi34@gmail.com
  token_command: pass show gkeep/master_token             # prints the aas_et/… master token
  token_store_command: pass insert -m -f gkeep/master_token  # used by `bob gkeep login`
  device_id: 3f9c0a1b2c3d4e5f                              # one hex id reused on every host
  target: gkeep_inbox.md
  skip: [pinned, shared]
```

- Env overrides: `BOB_GKEEP_EMAIL`, `BOB_GKEEP_TOKEN_COMMAND`, `BOB_GKEEP_ADAPTER`,
  `BOB_GKEEP_STATE_DIR`. Document them in the README "Environment" section.
- **`login` flow:**
  1. It prints the EmbeddedSetup steps.
  2. It reads the `oauth2_4/…` cookie from a hidden prompt or stdin.
  3. The adapter exchanges the cookie for `aas_et/…`.
  4. `login` stores the token via `token_store_command` and runs `ping`.
- **`doctor`:**
  - Checks config, `uv`, adapter deps, token shape (`oauth2_4/` means exchange it; `aas_et/`
    is correct), Keep reachability, state-cache age, target note, and `## Tasks`.
  - Warns when `gkeep_inbox.md` has no `type`.
  - Warns when `pass` needs an interactive pinentry, which matters for unattended runs.
  - Never prints a token.
- **Risk containment:**
  - The token is stored gpg-encrypted in `pass` and passed only on stdin.
  - The state cache is mode `0600` because it contains note text.
  - Keep request rates low (manual or hourly runs, incremental sync, gkeepapi's 429 backoff).
  - To revoke, remove the "Android device" from your Google account's device list.
  - Point `keep-cli` at the same token and `device_id` so there's one credential.

### 4.8 Tests

- **Golden render tests** for every note shape:
  - titled and untitled notes
  - multiline, Unicode, and Markdown-looking text
  - capture-grammar lookalikes (`=x`, `+5`, `%`, `@x`)
  - lists with checked, nested, and empty items
  - pinned, shared, labeled, and image notes
  - empty notes
- **Planner tests:**
  - `new`/`pending`/`revised`/skip
  - the journal backstop
  - duplicate detection
- **Pull integration tests** with the fake adapter and a temporary `BOB_DIR`:
  - dry-run and apply produce the same plan
  - a second run is a no-op
  - crash injection between write and archive leads to an archive-only retry
  - the `changed`, `missing`, and `error` results
  - the compare-and-swap conflict
  - `--no-archive` followed by a normal pull
- **Output tests:** stable ANSI-free output when not on a TTY, stable JSON schemas, and no
  mutating code path reachable from `list`, `doctor`, or `--dry-run`.

---

## 5. Rollout

| Phase | Deliverable | Exit criteria |
| --- | --- | --- |
| **0. Spike (1–2 h)** | Check what `gkeep_oauth_token` holds (exchange it if it's a cookie). Run a throwaway `snapshot` on the real inbox. Confirm which id opens `keep.google.com/#NOTE/<id>`. Archive and unarchive one test note. Check how a shared note's archive state behaves. | Real snapshot JSON; archive round trip confirmed |
| **1. Read-only** | Config and token plumbing, embedded adapter `snapshot` + state cache, `doctor`, `list` (both sides) | `bob gkeep` shows both tables; JSON tests pass with the fake adapter. Useful on its own. |
| **2. Plan + render** | `pull --dry-run`: pure planner, literal renderer, escaping, vault marker scan | Golden tests; the dry run on your real inbox looks right |
| **3. Write path** | Locks, compare-and-swap, durable atomic write, verify, scoped commit, `--no-archive`, journal | Crash-injection tests show no partial files and no duplicates |
| **4. Guarded archive** | Adapter `archive` with `expect`, post-archive confirmation, per-note report | Every `changed`/`missing`/`error` path behaves as in §4.3 |
| **5. Polish** | `login`, README + `docs/gkeep.md` contract, R8 vault tweak (with your OK), capture-targets Inbox entry, `gtd_daily.md` chore wording | `just all` passes; help follows `cli_rules.md` |
| **Later** | Apollo-only timer / `bob nightly` step · attachment download · explicit `label_tags` map · optional `restore <id>` (unarchive) · Takeout reader if the protocol breaks · native Rust adapter after a successful TLS spike | — |

---

## 6. Open Questions for You

1. Do you use **pins** or **shared lists** (for example, family groceries) in Keep Home? That
   decides whether the R2 defaults fit your habits.
2. Should a checklist be **one task with checkbox children** (recommended; matches the May
   dump), or **one task per unchecked item** (a possible `--split-lists` later)?
3. Is a **scoped vault commit before archiving** acceptable, or should commits be left entirely
   to `vault-sync`?
4. Does `pass` unlock on apollo without a prompt (gpg-agent cache)? That decides whether R9
   automation can ever run unattended.
5. OK to convert `gkeep_inbox.md` into an area note (R8) and drop its `zorg_*` frontmatter?

---

## 7. Recommended Solution

1. **Add `bob gkeep` with `list` (the default), `pull`, `doctor`, and `login`,** following the
   `bob plugins` dispatch pattern and `cli_rules.md`.
2. **Talk to Keep only through a small embedded PEP 723 adapter** (gkeepapi 0.17.1 /
   gpsoauth 2.0.0) run by `uv run --script`.
   - It speaks a versioned JSON-over-stdin protocol with typed errors.
   - It keeps a cached incremental state and one persisted `device_id`.
   - The master token comes from `pass` via `token_command` and is passed on stdin.
   - `BOB_GKEEP_ADAPTER` swaps in a fake for tests.
   - Don't use the official Keep API, Takeout, or browser automation for v1, and don't depend
     on `keep-cli` as is.
3. **Keep every visible and safety-critical piece in Rust:**
   - a literal, escaped renderer (never the capture grammar)
   - one note = one `#task` in capture format with the Keep created date
   - list items as plain checkbox children
   - a `Source:` child with a Keep link and a hidden `%%gkeep:v1:<id>:<fp>%%` marker
   - insertion under `## Tasks`
4. **Make `pull` a guarded transaction:**
   - snapshot → vault lock → pure plan → compare-and-swap durable write → parse-verify →
     scoped commit → unlock → **content-guarded archive** → confirm → journal
   - The vault is the ledger (`new`/`pending`/`revised`), so re-runs are idempotent and
     crashes are harmless.
   - Pinned and shared notes are skipped by default.
   - `--dry-run` shows the exact Markdown.
   - A duplicate is always preferred over losing data.
5. **Make `list` a reconciliation view** of both sides, with the pull state of each note and
   a footer naming the next command. Output is a styled table by default, plus
   `schema_version: 1` JSON.
6. **Ship it in phases:** spike → read-only → dry-run → write → archive → polish.
   - First runs go `pull -d` → `pull -n` → `pull`.
   - After a few weeks of clean manual runs, move the drain to an apollo-only timer, so phone
     captures reach Obsidian on their own and the daily chore becomes "triage
     `gkeep_inbox`".
   - If gkeepapi auth ever becomes a burden, move phone capture to Google Tasks or a direct
     Bob capture endpoint instead of fighting the private protocol.

---

## Sources

- **Local vault (read-only):**
  - `~/bob/gtd_daily.md:16`, `gkeep_inbox.md`, `legacy_gkeep_notes.md`
  - `gkeep_gdocs_inbox_dump.md`, `mac_inbox.md`
  - vault Git log for `gkeep_inbox.md` (commits `70fc35cd`…`d2d1c60d`, 2026-09-28)
  - `~/.config/bob/config.yml` (Tasks trailing-field caveat)
- **Local tools:**
  - `~/lib/keep_cli/main.py` (`login_keep`, `mutate_note`, `serialize_note`, keyring storage)
  - `~/lib/keep_cli/requirements.txt`
  - `~/.password-store/gkeep_oauth_token.gpg` (existence only)
  - `uv`, Python 3.12 on apollo
- **bob-cli:**
  - `src/scripts.rs` (`SUPPORT_ASSETS`), `src/native/collect_done.rs` (`atomic_write`, no
    fsync; `is_block_id_byte`)
  - `src/native/ob.rs` (`try_acquire_lock`), `src/native/capture.rs` (`format_task_line`,
    `insert_task_line`)
  - `src/native/note_tasks.rs`, `src/native/plugins.rs` (`None => run_list`)
  - `Cargo.toml`, `README.md` runtime dependencies
  - SASE memory `cli_rules.md`
- **gkeepapi source** (opened as `gh:kiwiz/gkeepapi` at `1a94b25`, 2026-01-05):
  - `node.py`: `_generateId`, `url`, `archived`, `extracted_text`
  - `__init__.py`: `authenticate` device-id default, `dump`/`restore`, `getMediaLink`,
    reminder sync disabled
- **gkeepapi issues:**
  - [#177](https://github.com/kiwiz/gkeepapi/issues/177) rich formatting not exposed
  - [#180](https://github.com/kiwiz/gkeepapi/issues/180) `LoginException` with a non-master
    token
  - [#181](https://github.com/kiwiz/gkeepapi/issues/181) archive no longer changes the edited
    date
  - [#189](https://github.com/kiwiz/gkeepapi/issues/189) app passwords dead since 2026-01; the
    `aas_et/` master token works
  - [#174](https://github.com/kiwiz/gkeepapi/issues/174) slow full sync
- **Google:**
  - [Keep API overview](https://developers.google.com/workspace/keep/api/guides)
  - [Note resource](https://developers.google.com/workspace/keep/api/reference/rest/v1/notes)
  - [notes.list](https://developers.google.com/workspace/keep/api/reference/rest/v1/notes/list)
  - [issuetracker 210500028](https://issuetracker.google.com/210500028)
  - [Keep export via Takeout](https://support.google.com/keep/answer/10017039)
  - [Keep keyboard shortcuts](https://support.google.com/keep/answer/12862970)
  - [Data Portability scopes](https://developers.google.com/data-portability/user-guide/scopes)
- **Other:**
  - [Playwright persistent context (Chrome 136+ default-profile restriction)](https://playwright.dev/docs/api/class-browsertype)
  - [gpsoauth](https://github.com/simon-weber/gpsoauth) (via cld)
  - [keep-it-markdown](https://github.com/djsudduth/keep-it-markdown) (export-then-archive
    prior art, via grk)
- **Swarm reports:** the five `bob_gkeep_inbox_drain__*.md` files in this directory.
