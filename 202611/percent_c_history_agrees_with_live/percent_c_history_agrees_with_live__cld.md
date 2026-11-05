# `%c<N>` clipboard history: why only entry 1 is right, and how to make it trustworthy

*Researcher: cld · 2026-11-05 · bob-cli `7e437418` · Mac checked live over Tailscale SSH*

## Bottom line

**Yes, bob reads the wrong clipboard manager.** On the MacBook, `%c<N>` takes entry 1 from
`pbpaste`, which is always live, and entries 2..N from **Clipy's** SQLite database. Clipy is
**not running**. Its history stopped updating on **2026-10-20 at 13:21**, 16 days ago. The
clipboard manager that is actually running, and that Bryan opens with ⌥C, is **Alfred 5**.
Alfred's newest history entry is byte-identical to `pbpaste` right now. None of Clipy's top
three entries match it. That fully explains the symptom: entry 1 is correct and every older
entry comes from a frozen October history.

Fixing the path alone is not enough, though. The deeper defect is that `%c<N>` **cannot tell
when its history source is stale, so it writes stale data without warning.** Clipy is still a
login item, so the next reboot brings it back and the bug "fixes itself" until it next quits.
Switching to Alfred would leave the same failure mode in place for the day Alfred quits or
Bryan changes managers.

**Recommendation.** Add a built-in, read-only **Alfred** history provider and pick providers
through bob's **config file** (`auto` by default, which prefers Alfred). Add a
provider-agnostic **agreement check**: a history read is trusted only if its newest entry
equals the live clipboard, allowing a short bounded wait for manager lag. Otherwise refuse
with a diagnosis. Also show **each entry's source and age** in the JSON and in the Mac
preview, so a stale entry is visible before Return. Fix Clipy's arbitrary tie-break while
we're there. Details are in [§7](#7-recommended-solution).

---

## 1. How `%c` / `%c<N>` works today

- `%c` and `%c1`: `read_clipboard()` runs `BOB_CLIPBOARD_CMD`, else `pbpaste` on macOS
  (`src/native/capture_clip/clipboard.rs`).
- `%c<N>` with N ≥ 2: `read_clipboard_history(N)` (`clipboard.rs:15`) works in three steps:
  1. It reads the live value through the same path (`pbpaste`).
  2. It reads history candidates (`read_history_candidates`, `clipboard.rs:57`):
     `BOB_CLIPBOARD_HISTORY_CMD` if set, else on macOS
     `~/Library/Application Support/com.clipy-app.Clipy/sqlite.db` (`clipboard.rs:68`),
     queried with `ORDER BY updateAt DESC, id DESC LIMIT N` (`clipy.rs:30`).
  3. `merge_history_candidates` (`clipboard.rs:35`) removes the first candidate equal to the
     live value, then returns `[live] + next N-1 candidates`.
- Call site: `read_capture_clipboard` (`src/native/capture/plan.rs:902`). Live preview in Bob
  Mac Capture runs the same dry run on every debounced keystroke once `capture-parse`
  reports a `clip` directive (`BobProcessClient.captureLivePreview`).

The original plan (`plan:202607/clipboard_history_count.md`, July 15) states the
assumption directly: *"The configured environment uses Clipy, but Clipy exposes no
supported command-line or URL API."* It chose the merge rule to tolerate a *lagging*
history, which is reasonable, but nothing guards against a *dead* history.

## 2. Root cause: evidence from the Mac

I gathered all of this read-only over `ssh mac`. **No clipboard contents were printed or
stored**: only schemas, counts, timestamps, lengths, and equality booleans. I never wrote to
the pasteboard.

| Check | Clipy | Alfred |
| --- | --- | --- |
| Version | Clipy 1.4.0 | Alfred 5.8.1 (Powerpack) |
| Process running? | **No** (still listed as a login item) | **Yes** (pid started Oct 13) |
| Store | `com.clipy-app.Clipy/sqlite.db` (GRDB, WAL), **713 MB** | `Alfred/Databases/clipboard.alfdb` (SQLite, `journal_mode=delete`), 5.8 MB |
| Rows | 10,000 (its `kCPYPrefMaxHistorySizeKey`) | 8,337 |
| Newest entry | **2026-10-20 13:21:09** (`max(updateAt)`); db and WAL mtime Oct 20 | **2026-11-05 09:03:04** (today) |
| Clipboard history enabled | n/a (not running) | `enabled`, `enabledFiles`, `enabledImages` all true; text kept 3 months; hotkey ⌥C |
| Newest entry == `pbpaste` (after bob's normalization)? | **No** for each of the top 3 | **Yes, byte-identical** (raw and normalized) |

Timeline reconstructed from file mtimes and the repo history:

- **Jul 5.** Clipy 1.4.0 migrates from Realm to GRDB/SQLite: `default.realm` freezes on Jul 5,
  and `sqlite.db` holds a `grdb_migrations` table.
- **Jul 15.** `e6b70be4` ships counted history against Clipy's SQLite store. That was correct
  for the setup at the time: Clipy and Alfred were both recording.
- **Oct 8.** The Mac boots (uptime 28 days). Clipy is relaunched as a login item.
- **Oct 20 13:21.** Clipy stops. There is no crash report in `~/Library/Logs/DiagnosticReports`,
  so it was most likely quit.
- **Oct 31.** `6ae5df00` adds the `%c` / `%c<N>` spelling. Every `%c<N>` since then has read
  October history for entries 2..N.

So `%c3` today returns `[live clipboard, Clipy's newest entry from Oct 20, its second-newest]`,
exactly matching "only the first seems to ever be correct". It probably **did** work
between July 15 and October 20, and will work again for a while after the next reboot. That
intermittency is why this has to be fixed with a guard, not just a path change.

## 3. Secondary defects found along the way

These are independent of the root cause. All of them should be fixed or decided as part of
"make `%c` resilient".

1. **The merge cannot detect a stale source** (design flaw, high severity). When the live
   value isn't in the candidates, `merge_history_candidates` assumes the manager is lagging.
   It cannot tell lag (milliseconds) apart from a dead or wrong manager (days). The result is
   silently wrong data written to the vault.
2. **Clipy ordering is arbitrary within a second** (correctness, medium). `updateAt` is
   whole seconds, and the tie-break `id DESC` sorts on Clipy's 64-character content-hash id,
   which is effectively random. The live database has **382 distinct seconds with tied
   rows**. Two copies within one second come back in arbitrary order. `rowid DESC` is the
   right tie-break: the table is a rowid table, and Clipy's `ON CONFLICT REPLACE` gives a
   re-copied item a fresh rowid.
3. **The documented override can't reach the main frontend** (operability, medium). Bob Mac
   Capture launches `bob` with a minimal environment: `HOME`, a fixed `PATH`, locale, and an
   allowlist of keys (`BobEnvironment.swift:56`). The allowlist doesn't include
   `BOB_CLIPBOARD_CMD` or `BOB_CLIPBOARD_HISTORY_CMD`, and launchd-started GUI apps don't
   see shell rc files anyway. Setting `BOB_CLIPBOARD_HISTORY_CMD` in `.zshrc` would fix
   terminal captures and leave Mac Capture broken, which is confusing. Provider selection
   belongs in `~/.config/bob/config.yml`, which `bob` reads no matter who launched it.
4. **No visibility** (UX, medium). Neither JSON nor the preview says *where* history entries
   came from or *how old* they are. A per-entry age such as "16 days" would have exposed this
   bug on day one.
5. **Inconsistent representation between entry 1 and later entries** (minor). For a file
   copied in Finder, `pbpaste` returns only the file *name* (plain text), while Clipy's
   decoder returns the *path* (an attachment). An image-only pasteboard makes `%c<N>` fail
   up front, because `read_clipboard()` errors before history is consulted, even though the
   manager has the image. This is acceptable for now, but the agreement check in §7 has to
   allow for it.
6. **Two managers record everything** (housekeeping). Clipy keeps 10,000 items (713 MB)
   alongside Alfred's 3-month history: two plaintext copies of everything copied, including
   anything a password manager didn't mark as concealed. This is a user decision, not code.

## 4. Critique of the request

**Making `%c` more resilient is the right call.** `%c<N>` writes into the vault, and a
silent wrong write is worse than a refusal, especially because the Mac panel hides on
success and Bryan may not re-read the note.

I would sharpen what "resilient" means. **The goal should be "correct or loud", not "always
returns N values".** Trying harder to produce *something*, for example by falling back from
a dead manager to a different one, makes silent wrongness more likely, not less. Every
history read should carry evidence that it tracks the live pasteboard, and should refuse
with a precise diagnosis when it doesn't.

Hypothesis check: "integrated with the wrong clipboard manager" is **confirmed** (§2).
Swapping Clipy for Alfred is still only half the fix, as explained in the bottom line.

## 5. Requirement adjustments (proposed changes, called out)

| # | Adjustment | Why |
| --- | --- | --- |
| **R1** | **New invariant: a history read is valid only if the provider's newest entry equals the normalized live clipboard**, after a short bounded wait (about 1.5 s, polled every ~150 ms). Otherwise `%c<N>` fails with a diagnosis. This **replaces** the unbounded "lagging history is fine" tolerance in the current merge. | It is the one cheap, provider-agnostic signal that the history is tracking *this* pasteboard *now*. It catches the exact bug in §2. The wait still covers real manager lag. |
| **R2** | **Provider selection moves to config** (`capture.clipboard_history`, default `auto`). `BOB_CLIPBOARD_HISTORY_CMD` stays as the highest-precedence override for tests and power users. | §3.3: env vars don't reach `bob` from Mac Capture. |
| **R3** | **Add a built-in Alfred provider**, preferred by `auto` on macOS. Keep Clipy as a provider with a fixed tie-break. | Alfred is what is running and what Bryan looks at (⌥C). Clipy support is already written and tested, so keeping it is cheap. |
| **R4** | **Expose provenance**: per-entry `provider`, `age_seconds`, and source `app`, added to clip JSON and shown in the Mac preview header. | It turns invisible staleness into something visible at a glance. This is an additive cross-repo contract change. |
| **R5** | **Add a read-only diagnostic command**, for example top-level `bob clipboard`, to show the chosen provider, its health, and the next N values with their ages. Previews are redacted by default. | It answers "what will `%c5` grab?" without composing a capture. CLI rules forbid subcommands under `bob capture` and keep read-only reports top-level. |
| **R6** | **Unchanged on purpose:** `%c` / `%c1` never touch history; exact-N or fail; whole-capture atomicity; entry 1 comes from the live source (prefix-stable). | These were good decisions in the July plan. |
| **R7** | **Accepted consequence:** if the live item was **concealed or transient**, for example from a password manager, Alfred won't record it, R1 fails, and `%c<N>` refuses. `%c` still works. | Refusing to batch a password into the vault is a feature. The error message names the likely cause. |
| **R8** | **Still out of scope:** images and file lists from *history* (Alfred `dataType ≠ 0`), a generic plugin system, a Bob-owned recorder (see §6), and Windows. A non-text history entry fails with an indexed, actionable error, as Clipy entries do today. | Keeps the change to one cohesive tale. Alfred's non-text row format is unverified (§8). |

## 6. Options considered

| Option | Verdict | Notes |
| --- | --- | --- |
| **A. Hard-code a switch from Clipy to Alfred** | Not enough on its own | Fixes today's symptom. The silent-staleness failure mode remains (Alfred quits, Bryan changes managers, history is disabled). |
| **B. Config + `auto` (Alfred → Clipy) + agreement check + provenance** | **Recommended** | Self-validating and cheap to run: one indexed SQLite query on a 5.8 MB file, plus `pbpaste`. Reads only what Alfred already stores, so there is no new data copy. |
| **C. Bob-owned recorder**: Mac Capture (or a `bob` launchd agent) polls `NSPasteboard.changeCount` into a ring buffer | Deferred | Independent of third-party schemas, but it adds an always-on writer and a third plaintext copy of clipboard history. It also has to honor `org.nspasteboard.ConcealedType`/`TransientType` correctly, misses history while it isn't running, and the CLI would need a path to the app's buffer. The July plan rejected recording inside Bob, and `decisions:mac-capture-is-a-thin-client` keeps data-producing logic out of the app. Apple's programmatic-paste privacy alert (previewed in macOS 15.4, opt-in on 26) is a future risk for any poller. **Reopen if** Alfred's history becomes unreadable (Alfred 6 schema or encryption) or Bryan drops a history manager entirely. |
| **D. Alfred workflow using `{clipboard:N}` placeholders via External Trigger** | Rejected | That is an official Alfred surface, but workflows run asynchronously and would hand data back through a temp file. It adds latency and race conditions, and needs a workflow installed in Alfred's synced preferences. |
| **E. User script via `BOB_CLIPBOARD_HISTORY_CMD`** (for example a chezmoi script that reads Alfred) | Rejected as the primary path | It doesn't reach Mac Capture (§3.3), duplicates schema logic outside tests, and still has no staleness guard unless R1 applies to it, which this design does. |
| **F. macOS 26 Spotlight clipboard history** | Not viable | There is no developer API and the storage is private. |
| **G. Drop `%c<N>`; use `%c` repeatedly** | Fallback only | Always correct, but loses the feature. |

## 7. Recommended solution

### 7.1 Provider model (bob-cli, `src/native/capture_clip/`)

Replace `read_history_candidates -> Vec<String>` with providers that return richer entries:

```rust
struct HistoryEntry { text: String, at: Option<SystemTime>, app: Option<String> }
enum HistoryProvider { Command(String), Alfred(PathBuf), Clipy(PathBuf) }
```

**Alfred adapter** (new `alfred.rs`, same style as `clipy.rs`):

- Path: `~/Library/Application Support/Alfred/Databases/clipboard.alfdb`. Open with
  `SQLITE_OPEN_READ_ONLY | NO_MUTEX` and set **`busy_timeout(≈250 ms)`**. Alfred uses a
  rollback journal, not WAL, so a read can collide with a write. Never use `immutable=1`,
  which could read a torn state.
- Schema check: table `clipboard` with columns `item`, `ts`, `app`, `dataType`. Fail as
  "unsupported Alfred clipboard database" on mismatch, as Clipy does today.
- Query: `SELECT item, ts, app, dataType FROM clipboard ORDER BY ts DESC, rowid DESC LIMIT ?`.
  `ts` is whole seconds since 2001-01-01, so convert with `+ 978_307_200`. This matches
  today's wall clock on the device.
- Semantics, verified on device: Alfred **dedupes by content** (8,337 rows, 8,337 distinct
  `item`s) and **bumps `ts` when an item is copied again**, with 429 rows out of rowid
  order. So `%c3` gives three *distinct* values in most-recently-used order. That matches the
  ⌥C viewer and should be documented.
- `dataType = 0` is text. Any other `dataType` is an indexed error per R8.
- Optional health hint: read `Alfred.alfredpreferences/preferences/local/<hash>/features/clipboard/prefs.plist`.
  If `enabled == false`, report "Alfred clipboard history is disabled" instead of a generic
  mismatch.

**Clipy adapter**: change the tie-break to `ORDER BY updateAt DESC, rowid DESC` and return
`updateAt` as `at`.

**Command adapter**: unchanged protocol. It doesn't provide ages. An additive object form
with ages could come later if wanted.

### 7.2 Selection

Precedence:

1. `BOB_CLIPBOARD_HISTORY_CMD`, if non-empty.
2. Config `capture.clipboard_history`.
3. `auto`.

```yaml
capture:
  clipboard_history: auto        # auto | alfred | clipy | command | off
  clipboard_history_command: ~/bin/clip-history   # required when clipboard_history: command
```

On macOS, `auto` tries **Alfred, then Clipy**, skipping any whose store is missing, and takes
the **first provider that passes the agreement check**. Elsewhere, `auto` keeps today's
"no provider, set the command" error. `off` makes `%c<N>` refuse cleanly. Invalid values are
configuration errors.

### 7.3 Agreement check (the actual resilience fix)

```text
live = read_clipboard()                                  # unchanged; %c/%c1 stop here
for provider in candidates(selection):
    deadline = now + 1.5s
    loop:
        head = provider.read(N + 1)
        if normalize(head[0].text) == live: return [live] + head[1..N] (exact-N or fail)
        if now >= deadline: record diagnosis(provider, head); break
        sleep(150ms)
fail("clipboard history doesn't match the live clipboard", diagnoses)
```

- Once the head matches, `[live] + head[1..]` equals `head[0..N]`. Results are prefix-stable
  and identical to what the ⌥C viewer shows.
- The diagnosis is per provider: running or not (via `pgrep -x`, for the message only),
  newest entry age, and "head differs". An example message from today's state:
  `Clipy: not running, newest entry 16 days old, doesn't match the live clipboard`.
  Alfred would pass.
- The only `%c<N>` call that *ever* waits is a capture fired within about a second of copying.
  Typing `%c3` in the panel already takes longer than Alfred's polling interval.
- **Known limitation:** a match only proves the *head* is current. A manager that was down for
  a while and then restarted has a gap further back. R4's per-entry ages make such a gap
  visible ("4 s · 2 min · 16 days"). Pinning `alfred` in config avoids `auto` choosing a
  freshly restarted Clipy.
- **Regression test for this bug:** the live value is `new`, the provider's newest entry is
  `old` from 16 days ago, and the capture must refuse without writing anything.

### 7.4 Provenance and diagnostics

- **JSON (additive).** History captures gain `clip.history = { provider, entries: [{ age_seconds, app }] }`.
  Single `%c` JSON stays byte-identical. Human output adds one line, for example
  `from Alfred · newest 3 s · oldest 4 min`.
- **Mac Capture (follow-up, additive).** Decode with `decodeIfPresent` and show the provider
  and ages in the clip header. Per the thin-client decision, bob does the work and the app
  only presents it. This needs a macOS CI run (see the `bob-mac-capture` note in AGENTS).
- **`bob clipboard`** (new, top-level, read-only, per R5): `-n/--count`, `-f/--format`, and
  `--show` for unredacted previews. By default it prints lengths and first characters only,
  so running it doesn't splash secrets into terminal scrollback.

### 7.5 Docs and tests

- Update `docs/capture.md#clipboard`, `docs/reference/cli/capture.md` (the "Clipboard source
  order" block at line 230), and `docs/reference/configuration.md` (`capture.*` keys, and the
  `BOB_CLIPBOARD_HISTORY_CMD` row that currently says "Clipy … on macOS").
- Tests: an Alfred fixture database (ordering, ties, epoch conversion, non-text rows, schema
  mismatch, busy database), the Clipy `rowid` tie-break, the selection matrix
  (env > config > auto; missing stores), and the agreement logic with an injected clock and
  sleep (match, lag-then-match, stale, concealed). Existing merge tests that encode the
  lagging-history tolerance need updating for R1.
- Commit flavor: R1 changes `%c<N>` failure behavior (lag becomes a bounded wait and stale
  becomes an error). Per `decisions:bob-cli-releases-ride-a-daily-train`, decide whether that
  counts as a CLI contract break that needs `!`. I lean toward `feat(capture)!`, since some
  previously succeeding invocations now refuse.

### 7.6 Mac housekeeping (Bryan's call, no code)

Quit Clipy and remove it from Login Items, or uninstall it and delete its 713 MB store.
Alfred already covers the same need, and two plaintext histories double the exposure. With
the agreement check in place, leaving Clipy alone is safe, but it serves no purpose.

## 8. Open questions and unverified points

- **Alfred non-text rows.** There are currently 0 rows with `dataType ≠ 0`; image and file
  retention is shorter. The usual mapping (1 = image stored under `clipboard.alfdb.data/`
  keyed by `dataHash`, 2 = file paths) is **not documented by Alfred** and couldn't be checked
  passively. Verify by copying a file in Finder on the Mac before supporting it.
- **Alfred's polling interval** is undocumented. The 1.5 s window is a conservative guess.
  Measure it once on the Mac with a scripted copy and tune the constant.
- **Alfred concealed/transient handling.** Alfred is widely reported to skip
  `org.nspasteboard.ConcealedType`/`TransientType` items. R7 assumes that behavior and refuses
  safely either way.
- **Linux (optional).** On a display-less tmux host, the live source is `tmux show-buffer`,
  and tmux's buffer stack is a natural built-in history provider
  (`tmux list-buffers` / `show-buffer -b`). That is a small, separable follow-up if `%c<N>` is
  wanted on athena.

## 9. Recommended solution (summary)

1. Treat the root cause as **confirmed**: bob reads Clipy, which has been dead since Oct 20,
   while Alfred is the live manager.
2. Ship one bob-cli tale with these parts:
   - an **Alfred read-only provider**;
   - **config-based selection** (`capture.clipboard_history: auto|alfred|clipy|command|off`,
     env override kept);
   - the **agreement invariant** with a bounded lag wait and per-provider diagnosis;
   - Clipy's **`rowid` tie-break fix**;
   - additive **provenance** (provider plus per-entry age and app) in JSON and human output;
   - a read-only **`bob clipboard`** diagnostic;
   - docs and tests, including a regression test for the stale-provider case.
3. Follow up in Bob Mac Capture to **show provider and ages** in the clip preview header.
4. Defer a Bob-owned clipboard recorder unless Alfred's store becomes unreadable.
5. Housekeeping: retire Clipy on the Mac.

## Sources

- Code: `src/native/capture_clip/{clipboard.rs,clipy.rs}`, `src/native/capture/plan.rs:902`,
  `docs/reference/cli/capture.md:228-230`, `docs/reference/configuration.md`
  (`capture`, `BOB_*`), Bob Mac Capture `Sources/CaptureCore/{BobEnvironment.swift,BobProcessClient.swift}`.
- History: commits `e6b70be4` (counted history, Jul 15) and `6ae5df00` (`%c` lexer, Oct 31);
  plan `plan:202607/clipboard_history_count.md`; decision `decisions:mac-capture-is-a-thin-client`.
- Device evidence: read-only `sqlite3`, `defaults`, `plutil`, `ps`, `launchctl`, and `uptime`
  on `mac` (macOS 26.5), plus an equality-only `pbpaste` comparison. No contents recorded.
- External:
  [Searching Alfred's Clipboard history programmatically (rmoff)](https://rmoff.net/2020/05/18/searching-alfreds-clipboard-history-programatically/),
  [Alfred Forum: opening clipboard.alfdb](https://www.alfredforum.com/topic/10392-is-there-anyway-to-open-the-clipboardalfdb-in-a-text-editor-terminal-or-script/),
  [mjtsai: NSPasteboard.org conventions](https://mjtsai.com/blog/2014/01/02/nspasteboard),
  [mjtsai: pasteboard privacy preview in macOS 15.4](https://mjtsai.com/blog/2025/05/12/pasteboard-privacy-preview-in-macos-15-4),
  [DEV: macOS Tahoe clipboard history has no API](https://dev.to/jrw0ng/macos-tahoe-has-built-in-clipboard-history-heres-what-its-still-missing-for-developers-2026-4eko),
  [MacRumors: how Spotlight clipboard history is stored](https://forums.macrumors.com/threads/does-anyone-know-how-spotlight-clipboard-history-is-stored-internally.2483728/).
