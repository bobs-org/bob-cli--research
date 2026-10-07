---
audio:
  edition: brief
  duration_s: 274.24
  chapter_count: 3
  episode_id: routing-bare-links-into-bob-s-reading-library-b56f99
---

# Routing URL-only capture and Google Keep input into `bob ref create`

> **Research query:** Now that `bob highlights create` supports URLs and has moved to `bob ref create` (epics bob-cli-4s and bob-cli-4w), how should `bob capture` and the Bob Mac Capture app route URL-only capture input (with bulk URL captures still supported) to `bob ref create` instead of capturing a note or task, and how should `bob gkeep pull` do the same for URL-only Google Keep notes instead of adding them to `~/bob/gkeep_inbox.md`? Critique the plan, call out any justified requirement adjustments, and end with a recommended solution.

<div class="listen">

♫ **Brief audio edition** · 5 min · 3 chapters · [Narration
script](url_capture_ref_intake_routing_narration.md)

</div>

![Infographic of the recommended design, "From bare URL to reading queue": a shared core recognizes reading intent with a strict classifier and offline library check; capture and the Mac app save a durable clip job and return immediately while a background worker clips, falling back to an inbox task on failure; Google Keep pull clips inline, then journals and archives, leaving retryable failures in Keep; both paths save an intake PDF that the existing 15-minute scan turns into a reference note](url_capture_ref_intake_routing_infographic.png)

## Bottom line

- **[Yes, build it.](#critique-of-the-plan)** The ref library is the right home for a bare URL.
  - It provides dedupe, a reading queue (`bob ref list`), "have I read this?" answers for agents (the `bob_ref` skill), and the `^ref` tracker that already walks in the daily REFERENCES review tier.
  - A bare-URL inbox task has none of these. All five researchers agree.
- **Treat this as enabling a new habit, not as relieving an existing load** ([usage evidence](#read-only-usage-evidence)).
  - The whole vault has exactly **one** bare-URL task, and it duplicates a ref Bryan has already **finished**.
  - Since 2026-09-01, `bob gkeep pull` wrote about 138 Keep blocks. **None** contains a shared link.
  - So v1 must be cheap to be wrong about.
- **Do not implement it literally** ("run `bob ref create` instead of capturing").
  - A web clip takes 10–150+ s: the adapter budget is 150 s, and Rust kills it at 300 s. It needs network, uv, and Chrome, and it fails for ordinary reasons.
  - Today a capture takes about 0.2 s, works offline, and never loses input.
  - Bob Mac Capture kills every `bob` call after **20 s**, and a new submit **cancels** the one in flight. Live preview runs `capture --dry-run` after every edit.
- **[Recommended shape](#recommended-design):**
  1. **One shared core in bob-cli:**
     - a pure URL-intent classifier;
     - a typed, non-printing *ingest* function extracted from `ref create`;
     - an offline "already in library?" verdict.
  2. **`bob capture`:**
     - Bare-URL items become a new `ref` kind, previewed offline.
     - Submit writes a durable **[clip job](#clip-jobs-and-the-worker)** and returns at once. A detached, single-flight worker runs the ingest.
     - If a clip fails, the item **falls back to today's inbox task**, with the reason attached. A URL is never lost.
  3. **`bob gkeep pull`** ingests **inline**, because it is already an attended batch drain. It archives a Keep note only after a terminal outcome.
  4. **Bob Mac Capture** stays a thin client. It only presents the new kind and needs no timeout or lane change.
- **Adjustments to your requirements** (all in [Adjusted requirements](#adjusted-requirements)): per-item bulk and mixed drafts; Keep's share-sheet shape counts as URL-only; corp links stay tasks; a clip failure falls back to a task; capture *queues* the clip rather than running it inline.
- **Two environment facts block the Mac side:**
  - On the Mac, **uv exists only at `~/.local/bin/uv`**. bob's `find_on_path("uv")` and the app's fixed PATH both miss it, so any clip started from Bob Mac Capture fails today.
  - **`bob gkeep pull` also runs on the Mac.** Its journal is there, and athena has no gkeep state. So the Mac is the clip host for *both* entry points, and article clipping has never been live-verified on it.

## Critique of the plan

**Yes, on the merits.**
- A bare-URL inbox task carries little information, has no dedupe, and goes stale. The vault's only example is a duplicate of a finished reading.
- Routing reading intent into the library keeps it under GTD review (the REFERENCES tier).
- Clipping at capture time also protects against link rot.

**Caveats that shape the design:**

1. **[There is little demand data.](#read-only-usage-evidence)**
   - The value lies in a habit Bryan wants to start: share from the phone to Keep, or paste into the Mac panel, and the link lands in the reading queue.
   - Bare URLs are virtually never used as tasks today, so silently misrouting an existing habit is unlikely.
   - But nobody has seen the real Keep share shape in this vault ([open question 1](#open-questions-for-bryan)), and the design should not over-invest before use proves out.
2. **Not every URL is an article.** GitHub repos, YouTube, product pages, login-walled pages, and corp links either produce a useless PDF or fail. The classifier must be narrow, and failure must be graceful.
3. **`create` is not a ref note.**
   - `create` stamps an intake PDF. `bob ref scan` (the Mac's 15-minute cron) writes the note later.
   - Every message must say "queued" or "saved to intake", never "ref created".
   - No path should auto-run `scan`; all five reports agree.
4. **The literal synchronous plan breaks capture's three invariants:**
   - capture never blocks on the network;
   - a captured URL is never lost;
   - the preview tells the truth before submit.

   The recommended design keeps all three.
5. **Bulk is underspecified.** Taken literally, "the only capture input" conflicts with "bulk with URLs should be supported". The coherent reading is **per item**.

## Adjusted requirements

My changes are marked ⚠️.

- **R1 — What counts as a URL item (⚠️ tightened).** A capture item routes to the library only when all of these hold:
  - It is one whitespace-free token.
  - It is an `http(s)` URL, optionally wrapped in `<…>`.
  - It passes `validate_and_clean`.
  - Its host is dotted and public.
  - Its host does not match `exclude_hosts`.
  - The item has no other tokens: no `@route`, `#tag`, `s:`, `p:`, `%`, operators, or children.
  - No explicit destination applies: none of `-r/-s/-t/-S`, and no `@@` global destination.

  Markdown links, two URLs, and URL plus prose all stay ordinary capture. Corporate short links (`http://go/x`) and excluded hosts stay tasks.
- **R2 — Bulk (⚠️ extended).**
  - Routing is per item, and mixed drafts are allowed.
  - An item whose every line is an eligible URL (a pasted list, which is a parse error today) splits into one ref item per line.
- **R3 — Execution (⚠️ changed from "run `bob ref create` instead").** Capture records a durable clip job and returns at once. A worker runs the same ingest engine as `bob ref create`, with its defaults:
  - `blogs` for articles and `papers` for PDFs and arXiv;
  - status `ready` and parent `obsidian_ref`;
  - `--no-audio`.
- **R4 — Never lose a URL (⚠️ new).**
  - A failed capture clip writes exactly the task line capture writes today, to the same route, plus a child bullet: `⚠️ Clip failed (<kind>): <message> · retry: bob ref create <url>`.
  - A Keep clip that fails **permanently** is written to `gkeep_inbox.md` the same way. This is a deliberate exception to "never add it to `gkeep_inbox.md`".
- **R5 — Keep shape (⚠️ widened and narrowed).** A Keep note is URL-only when all of these hold:
  - it is a text note, not a list;
  - it has no attachments;
  - its body is exactly one R1-eligible URL, or its title is that URL and its body is empty;
  - its title is empty, equals the URL, or matches (normalized) the title of a `WebLink` annotation for that URL.

  A title Bryan wrote, a note with several URLs, or any commentary stays an inbox task. Shared notes never auto-clip, even with `-S`.
- **R6 — Already in the library = success (⚠️ decided).**
  - A PDF-backed ref or a queued intake PDF is a successful no-op. The preview says "already in your library: *Title* (finished)", and submit writes nothing.
  - For Keep, the note is journaled and archived.
  - A legacy-only hit still captures a fresh copy, per bob-cli-4w.9.
- **R7 — No `--listen`, no `scan`.** Listening costs money and minutes. `scan` is the Mac's 15-minute job, and it runs hooks.
- **R8 — Opt-outs.**
  - `-R/--no-ref` on `bob capture` and on `bob gkeep pull`.
  - Config toggles per entry point, plus `exclude_hosts`.
- **R9 — Thin client (unchanged).** All classification, preview, and execution live in bob-cli. The Mac app only decodes and presents.

## Recommended design

### Shared core in bob-cli

1. **Typed ingest, extracted from `create_pdf`.**
   - Signature: `ingest_url(config, &UrlIntent, &IngestOptions) -> Result<IngestOutcome, IngestError>`.
   - `IngestOutcome` is one of:
     - `Created { pdf, ref_type, title, route }`
     - `AlreadyInLibrary { note, pdf }`
     - `AlreadyQueued { pdf }`
   - `IngestError` has a `kind`, a `message`, and a `retryable` flag. Kinds: `network`, `timeout`, `http_status`, `blocked`, `thin`, `unsupported_content`, `browser`, `dependency`, `collision`, `render`, `internal`.
   - Progress goes to stderr only.
   - `bob ref create` renders the outcome, and its human output and exit codes stay byte-identical.
   - Before publishing, the PDF and its directory get a `sync_all`.
   - Callers build the config from the effective vault root, never from Clap. A `--bob-dir` run must never touch the live vault.
2. **`url_intent::classify(raw) -> Option<UrlIntent>`.**
   - Pure; it implements [R1](#adjusted-requirements).
   - It carries `{original, cleaned, dedupe_key, route_hint}`, where `route_hint` is `arxiv`, `pdf-suffix`, or `article`, and is **only** a hint.
   - It rejects internal whitespace before any parsing. It never trims guessed punctuation.
3. **`library_verdict(config, &UrlIntent)`.**
   - Offline and exact-identity: it reuses `sources::collect_recorded_source_urls` and the `ref find -i` index. cld measured `ref find -i` at about 0.04 s.
   - It returns `not_found`, `in_library`, `in_intake`, or `legacy`, plus a path and a reading state.
4. **`resolve_uv()`.** Check PATH, then `~/.local/bin`, `~/.cargo/bin`, and `/opt/homebrew/bin`. Use it in both `clip_adapter.rs` and `gkeep/adapter.rs`, and add a `bob ref doctor` row showing which uv was found.
5. **Config** (proposed defaults; Bryan confirms the list):

   ```yaml
   highlights:
     url_routing:
       capture: true
       gkeep: true
       exclude_hosts:
         [corp.google.com, googleplex.com, docs.google.com, drive.google.com, keep.google.com, youtube.com, youtu.be]
   ```

### `bob capture` and `capture-parse`

- **Grammar.**
  - Add a whole-item claim, "bare URL item", next to the existing whole-item operators and before ordinary task parsing (`capture_language/item.rs`).
  - Add the R2 list split in shared draft splitting, so that parse, preview, submit, and source ranges agree.
- **`capture-parse`** stays lexical. It reports `mode: "ref"` and a `ref_url` span. Both are additive, and the schema stays at v1.
- **`capture --dry-run`** classifies and adds the offline library verdict. Each item carries:
  - every required legacy field, with honest values;
  - `kind: "ref"` and `route: "ref"`;
  - `placement`: `queued`, or `unchanged` when the URL is already in the library;
  - `target` and `relative_target`: the existing ref note, or empty;
  - an optional `ref` object: `{url, cleaned_url, dedupe_key, route_hint, library{verdict,path,reading_state}, job{id,state}, fallback{relative_target,task_line}}`.

  The dry run makes no network calls. Tests should prove this with fake curl and adapter binaries that fail if they are invoked.
- **Commit.**
  - For each ref item, write `$XDG_STATE_HOME/bob-cli/ref-jobs/pending/<id>.json` atomically (temp file, fsync, rename), then the staged task files.
  - If the batch fails, delete the job files this run created, exactly like clipboard cleanup.
  - After the commit succeeds, kick the worker.
  - The output equals the dry run apart from `dry_run` and `job.id`.
- **Human output:** `queued reference example.com/post → reading queue (bob ref jobs)`, or `already in library: ref/ai/x.md (finished)`.
- **Flag:** add `-R, --no-ref` (bare URLs stay tasks).
  - Drop the `-w/--wait` flag cld proposed from v1. `bob ref jobs run` already covers the foreground case.

### Clip jobs and the worker

- **Job file.** It holds the URL, the cleaned URL, the dedupe key, and the source (`capture` plus client). It also holds the `bob_dir`, the creation time, and the fallback `{route, task_line}`. It lives outside the vault, which is git-synced.
- **Kick.**
  - `bob capture` spawns `current_exe() ref jobs run -q` **detached**: a new session, with stdin, stdout, and stderr redirected to `ref-jobs/worker.log`.
  - A child that inherited the Mac app's stdout pipe would hold the app's read open until the clip finished.
- **Worker.**
  - It is single-flight through a lock file. Before exiting, it releases the lock and re-checks `pending/`, which avoids a lost wakeup.
  - It processes jobs sequentially, holding no vault lock during the clip.
  - Success, `AlreadyInLibrary`, or `AlreadyQueued`: append to `ref-jobs/done.jsonl`.
  - Any error: write the fallback through the capture library in-process, with routing disabled and the normal preimage guard.
  - **v1 makes one attempt.** Offline capture therefore turns into a fallback task with a retry hint. Retrying retryable errors can follow later ([open question 7](#open-questions-for-bryan)).
- **Visibility.**
  - `bob ref jobs` (bare = a read-only list, which `cli_rules` allows) shows pending and recent jobs.
  - `bob ref jobs run` drains the queue in the foreground.
  - `bob ref doctor` warns about stale pending jobs.
  - Avoid the names "queue", "inbox", and "intake"; each already means something.

### `bob gkeep pull`

- **Adapter.** Emit `links: [{url, title}]` from `annotations.links`, under `#[serde(default)]`. The fingerprint and the archive guard stay unchanged.
- **Classify.**
  - After the ledger and journal checks, a `New` note that matches R5 becomes `PlanAction::CreateRef`.
  - A journal `ref_created` entry for the same id and fingerprint gives `ArchiveOnly`.
  - Ledger hits keep today's behavior: notes already written as tasks, and revisions.
  - `CreateRef` counts as actionable for `--limit`.
- **Execute.**
  - Run a pre-pass under the per-host pull lock, **before** taking the vault lock. The vault lock waits 60 s and is shared with vault-sync, so it must not be held across minutes of Chrome.
  - Clips run sequentially, with a spinner.
- **Outcomes.**
  - **Created, AlreadyInLibrary, or AlreadyQueued:** fsync, append `ref_created {id, fp, url, pdf|note}` to the journal, and add the note to the archive set.
  - **Retryable error:** leave the note in Keep, report it, and count it toward exit 1. The next pull retries it.
  - **Permanent error:** render the note exactly as today, plus the ⚠️ child bullet. It then goes through the normal write, verify, commit, and archive path.
- **Archive precondition (new).**
  - The live note must still have no attachments.
  - Today's archive guard ignores attachments, so an image added mid-pull would otherwise be archived without ever being captured (cdx).
- **Pulls with only URL notes** must not require `gkeep_inbox.md` to exist. Move the target-file checks into the task-write branch.
- **Surfaces.**
  - `list` and `pull -d` show `create_ref` and the offline verdict.
  - JSON gains `action: "create_ref"`, a per-note `ref{url,outcome,pdf,existing,error}`, and `summary.refs`.
  - Add `-R/--no-ref`.

### Bob Mac Capture (presentation only)

- Decode an optional `ref` object with the tolerant `try?` pattern used for `task_complete`.
- **Preview card:**
  - "Reference · example.com/post · new to library"
  - "Already in library: *Title* (finished)"
  - and a hint that the item becomes an inbox task if the clip fails.
- **Status line:** "Queued for clipping → reading queue".
- Give the `ref_url` span a link color.
- **Cmd-Return** opens `ref.library.path` when one is known. Otherwise it does nothing, because there is no note yet. **Never open an empty or guessed target.**
- Add `~/.local/bin` to `BobEnvironment` PATH, as defense in depth next to `resolve_uv()`.
- Leave timeouts, lanes, and the submit flow unchanged.
- Record fixtures from real bob output, and ship bob first. An older app shows a ref item as a generic item; an older bob keeps returning tasks.

### Docs and decision record

- **`docs/capture.md`:** a "URL items" section covering grammar, JSON, opt-outs, and the fallback.
- **`docs/gkeep.md`:** the new action, its outcomes, and the archive rules.
- **`docs/highlights-create.md`:** the ingest boundary, plus the `--max-time` drift fix ([Incidental findings](#incidental-findings)).
- **New `docs/ref-jobs.md`.**
- **After landing**, propose a decisions record through `/sase_memory_write`:
  - **Claim:** "A bare public URL is a reading intent. It becomes a ref through a background clip job and falls back to an inbox task. Capture never blocks on the network."
  - **Rejected alternatives:** inline sync, a longer app timeout, and a vault sweeper.

### Phasing

One epic, two repos.

| # | Phase | Size | Depends on |
| - | ----- | ---- | ---------- |
| 1 | Typed ingest extraction, `resolve_uv()`, doctor uv row, `sync_all`, doc drift fix | medium | — |
| 2 | URL-intent classifier, offline library verdict, `url_routing` config | small | 1 |
| 3 | gkeep: adapter links, `CreateRef`, pre-pass, journal, fallback, attachment precondition, JSON, `-R` | medium | 2 |
| 4 | Capture grammar, list split, `capture-parse` mode and span, offline dry-run JSON, `-R` | medium | 2 |
| 5 | Clip-job spool and worker, detached kick, fallback writer, `bob ref jobs`, doctor row | medium–large | 4 |
| 6 | Mac presentation, PATH, fixtures (macOS CI) | medium | 4's JSON frozen |
| 7 | Live verification on the Mac and athena | small | 3, 5, 6 |

Phase 7 covers:
- a real article, a direct PDF URL, and an arXiv URL;
- a blocked site, which should produce a fallback;
- a corp link, which should stay a task;
- a phone share-to-Keep sample;
- `bob ref doctor` run under the app's environment.

Phases 3 and 4 can run in parallel. Phase 3 delivers end-to-end value first, with no worker needed.

**Tests that matter:**
- the classifier table (corp links, IP literals, `<URL>`, trailing tokens, `@@`, children, uppercase scheme, query punctuation);
- dry runs offline, proven with fakes that fail when invoked;
- a batch rollback deletes job files;
- fallback task bytes;
- the Keep matrix: title or body URL, page title vs authored title, lists, attachments, pinned or shared notes, an attachment added mid-pull, retryable vs permanent failure, re-pull idempotency through the journal;
- single-object JSON on stdout;
- `--bob-dir` isolation.

## Open questions for Bryan

1. **Keep share shape.** Share one link from your phone to Keep. Once phase 3 makes the adapter emit `links`, run `bob gkeep list -f json` and confirm the title, body, and annotation shape before freezing R5.
2. **Clip host.** I recommend clipping locally on the Mac first, after the uv fix and a passing doctor run. Add `ssh athena bob ref create …` delegation only if Mac clipping proves flaky. cld leans toward athena, because the MacBook is shared and never clip-verified.
3. **`exclude_hosts` defaults.** Add `github.com`, `x.com`, or `twitter.com`?
4. **Status for captured refs:** `ready` (the reading queue) or `next`?
5. **Notifications.** Should a fallback raise a desktop notification (osascript or notify-send), or is the ⚠️ task in the inbox enough?
6. **Re-capturing a URL already in the library:** stay a no-op, or "bump" the ref? Bumping needs a ref write verb, which bob-cli-4w left out of scope.
7. **Retries in v2:** should retryable capture clips stay pending (for example, 3 attempts or 24 h) before falling back?

## Incidental findings

Fold into the epic; no beads filed.

- **Doc drift.** `docs/highlights-create.md:272` says curl runs with `--max-time 30`; `target.rs:80` passes 300.
- **Mac environment.** Every uv-backed command launched from the app (article clip, gkeep) fails until uv resolution is fixed.
- **SSRF.** bob-cli-4v is still open. The Rust guard checks only hostnames and IP literals, never resolved addresses. Add a resolved-address check in `fetch.rs` once Keep feeds URLs automatically.
- **Machine output for `ref create`.** If agents want JSON from `ref create`, it needs a short flag other than `-f`, which means `--force`.
- **Vault cleanup.** `sase.md:20` is a stale bare-URL task that duplicates a finished ref.

## Report scope and inputs

Consolidated report · 2026-10-07 · bob-cli `master` @ `6d2911c` · bob-mac-capture @ `4344a54`

**Inputs**
- Five independent reports in this directory: `__cdx`, `__cld`, `__grk`, `__mus`, `__gem`.
- My own verification against:
  - the bob-cli source;
  - the bob-mac-capture source;
  - the upstream gkeepapi checkout;
  - the live vault, read-only;
  - a read-only probe of the Mac.

**Question.** Should `bob capture`, Bob Mac Capture, and `bob gkeep pull` send URL-only input to `bob ref create` instead of writing a task? If so, how? This report also critiques the plan, adjusts the requirements, and ends with a recommendation.

## What exists today (verified)

### Capture and the Mac app

| Area | Fact | Evidence |
| --- | --- | --- |
| Capture grammar | One grammar serves `capture` and `capture-parse`, with no URL awareness. A bare URL captures as `kind:"task"` into `mac_inbox.md`. `URL⏎URL` is an `invalid_child_line` parse error; `URL⏎⏎URL` gives two tasks. | Reproduced with the installed `bob` (cdx, cld, and me) |
| Capture batches | All items are planned in memory before any write. The commit checks disk preimages, then writes via temp file and rename, with rollback. Clipboard attachments are the precedent for "a side effect outside the staged files, rolled back with the batch". | `capture/batch.rs`, `capture/commit.rs` |
| Capture JSON | `bob capture -f json` has no `schema_version` and grows additively. Every item must carry `ok, dry_run, routed, route_label, relative_target, target, text, task_line, kind, created, placement`. `capture-parse` is schema v1 and purely lexical: it never touches the vault. | `capture/output.rs`, `CaptureModels.swift:2106-2122` |
| Capture flags | Short flags in use: `-b -c -d -f -n -r -s -t -S`. `-r/--route` already forces a task. A subcommand under `bob capture` is forbidden. | `bob capture --help`, `cli_rules` memory |
| Mac app | Every call has a 20 s timeout, submit included. A new call cancels the previous process in its lane. Live preview runs a dry run 50 ms after each edit. Decoders treat `kind`, `mode`, and span kinds as plain strings. PATH is a fixed list without `~/.local/bin`. | `BobProcessClient.swift:17-20, 205-226, 583-599`, `BobEnvironment.swift:18-30` |
| Mac host | uv is only at `~/.local/bin/uv`, and Chrome is installed. A 15-minute cron runs `maybe_bob_highlights_sync -w`, which rsyncs athena's and apollo's `xlib/`, then scans. | Read-only `ssh mac` probe (cld and me) |

### `bob ref create`

| Area | Fact | Evidence |
| --- | --- | --- |
| Classification | Syntactic URL check, then `validate_and_clean`, then dedupe **before** any fetch. arXiv takes its own route; other URLs go through `fetch_and_route` (curl, 300 s), which picks the PDF route or the article clip. `--dry-run` still fetches generic URLs. | `create.rs:390-480`, `target.rs:80` |
| Output and errors | `create_pdf` is private, returns `Result<()>`, and prints directly (about 150 `println!` sites). A dedupe refusal is an error with exit 1, distinguishable only by its message ("already captured as…" or "already queued in…"). | `create.rs`, `sources.rs:425,446` |
| Flag collision | `-f` means **`--force`**, so a `-f/--format json` flag (as `__cld` proposes) would collide. | `bob ref create --help` |
| Result | Writes `xlib/<type>/<stem>.pdf`. The ref note comes later, from `bob ref scan`. The install path never calls `sync_all`. | `docs/highlights-create.md`, `marker.rs`, `io.rs` |
| Validator | Accepts http and https only and rejects userinfo. Rejects `localhost`, `.local`, `.internal`, and private IP literals, but **accepts single-label hosts** such as `http://go/x`. bob-cli-4v (open) tracks the IPv4-mapped IPv6 hole. | `clip_url.rs:43-190` |
| Clip hosts | athena is live-verified (Chrome and Xvfb). The adapter supports macOS (`headed_capability() → "macos"`), but no Mac clip has been verified. | `docs/highlights-clip.md`, `web_clip_adapter.py:590` |

### `bob gkeep pull`

| Area | Fact | Evidence |
| --- | --- | --- |
| Pipeline | Snapshot → classify (archived → empty → pinned → shared → ledger → journal → new) → render → compare-and-swap write → verify → commit → content-guarded archive. | `gkeep/pull.rs`, `gkeep/plan.rs` |
| State types | `PlanAction` is `{Write, WriteRevision, ArchiveOnly, Skip}`; `JournalEvent` is `{Written, Archived}`. | `gkeep/plan.rs`, `gkeep/ledger.rs` |
| Archive guard | Hashes title, text, and items, **not attachments**. | `gkeep/plan.rs`, `gkeep/ledger.rs` |
| `note.url` | This is the **Keep permalink** (`https://keep.google.com/u/0/#NOTE/<id>`), not the shared link. Shared-link previews live in `annotations.links` (each a `WebLink` with `url`, `title`, …), and the adapter does not emit them. | gkeepapi `node.py:1537-1543`, `312-399`, `628`; `gkeep_adapter.py` |
| Where it runs | **On the Mac, by hand.** The journal has 178 lines (89 `written`, 89 `archived` since 2026-09-28), with runs roughly daily. athena has no gkeep state, and no cron or launchd job runs a pull. | `ssh mac` probe (me) |

### Read-only usage evidence

- **Whole vault:**
  - One task is only a URL: `sase.md:20`.
  - `bob ref find` reports that URL as finished (cld; I reproduced the grep).
- **`mac_inbox.md` git history since 2026-05** (236 added task lines). URLs nearly always come with intent text: "Install …", "Explore …", "Call Morgan Stanley … to access https://…". Many are corporate links:
  - `http://go/…`, `http://cl/…`, `http://cs/…`
  - `*.corp.google.com`
  - `screenshot.googleplex.com`

  One is a URL used as a reminder: a utility-bill login page.
- **`gkeep_inbox.md` git history since 2026-09-01:** about 138 Keep-sourced blocks and zero non-Keep URLs.

## Where the reports disagreed, and how I resolved it

| Question | Positions | Resolution | Why |
| --- | --- | --- | --- |
| How capture executes the clip | Synchronous in-process: grk, mus, gem, cdx. Async clip job: cld. | **Async job plus a detached worker** | The 20 s Mac timeout and lane cancel would kill clips; the panel would stay open for minutes; offline capture would fail. Job files make batch rollback and mixed drafts trivial, and the real result matches the dry run. Synchronous only works if the app gets per-mode budgets, cancellation of process trees, and a "Clipping…" state. That moves complexity into Swift, which only macOS CI can verify. |
| What happens on failure in capture | Fail and keep the draft: grk, cdx. Fall back to a task: cld, gem. Split by error type: mus. | **A URL that fails plan-time validation is not claimed, so it stays a task and the preview shows that. A clip failure falls back to the inbox task plus a ⚠️ reason and retry hint.** | With async execution the panel is already gone, so fallback is the only way to lose nothing. Validating at plan time keeps the preview truthful. |
| Mixed URL + task drafts | Reject: grk. Allow: the others. | **Allow** | A job file is just one more staged side effect, rolled back with the batch. |
| A paste of one URL per line | Split into items: cdx, cld. | **Split, but only when every line of the item is an eligible URL** | That input is a parse error today, so the change is strictly additive. |
| Keep note with page title + URL | Strict, URL only: cdx, mus. Any non-URL title: grk, gem. Title must match the `WebLink` annotation: cld. | **cld's rule, frozen only after a live share sample** | Share-to-Keep autofills the page title. A title Bryan typed must stay a task, and so must the Keep note. |
| Keep's `note.url` field | Treated as the shared link: gem (Case 3), mus. | **Wrong** | It is always the Keep permalink (`node.py:1543`). Using it would route the wrong URL. |
| When to archive the Keep note | After the intake PDF: grk, gem, mus, cld. Only after a ref note exists, on a second pull: cdx. | **After a terminal outcome. Fsync the PDF, journal, then archive.** | Pulls are manual and roughly daily, so deferring would leave link notes in Keep for a day. Keep archive is reversible, and dedupe makes retries safe. On the Mac the PDF lands in the very `xlib/` the 15-minute scan reads. cdx's fsync point is adopted. |
| Keep note whose clip fails | Always leave it in Keep: grk, gem, mus, cdx. Split by error type: cld. | **Retryable (network, timeout, 5xx): leave in Keep. Permanent: write a fallback task, then archive.** | Otherwise a permanently unclippable note errors on every pull forever. |
| Journal record | Reuse `Written`: grk. New event: the others. | **New `ref_created` event, which the planner maps to `ArchiveOnly`** | Elsewhere, `Written` means "a task block exists in the vault". |
| In-process vs subprocess | In-process: grk, mus, gem, cdx. Subprocess `ref create -f json`: cld. | **In-process typed ingest** | The `-f` flag collides with `--force`. Rust already kills curl and the adapter at 300 s, and the worker is a separate process anyway. A JSON output for `ref create` is a nice-to-have for agents, not a prerequisite. |
| Mac timeout | Raise it for submit: grk, cdx. No change: cld. | **No change** | Capture returns at once. |
| Escape hatch | `--as-task`: grk. `--no-ref`: mus, cld. Existing `--route`: cdx. A `- [ ]` prefix: gem. | **Natural opt-outs, plus `-R/--no-ref` for scripts and agents** | Any extra word, `@route`, `@@`, schedule or priority, child line, or forced flag already means "task". `-R/--no-ref` mirrors `-n/--no-clip`. |
| Corporate short links | Only cld raised them. | **Require a dotted public host, plus a small exclude list** | The inbox history is full of go/, cl/, and cs/ links. |
| Name of the new kind | `ref`: cld. `ref_create`: grk, mus, gem. `reference`: cdx. | **`ref`** | Nothing is created at submit time, and `ref` matches the `bob ref` noun. |
| Dry-run target path | gem predicts an exact `xlib` path and stem. | **Never fabricate one** | An article's stem and title are known only after the fetch. |
| Latency figures | gem: 3–15 s per clip and a capture under 50 ms. | **10–150+ s per clip; a capture takes ~0.2–0.3 s** | The adapter's `OVERALL_TIMEOUT_SECS = 150`; I measured 0.32 s wall time for a dry run. |

## Recommended solution

Ship URL-to-library routing as **one shared ingest core with two front doors**: an async `ref` capture kind and an inline gkeep plan action.

1. **Core.**
   - Extract a typed, non-printing ingest function from `bob ref create` and keep the CLI byte-identical.
   - Add a pure URL-intent classifier (a single public dotted-host `http(s)` token, not excluded) and an offline library verdict.
   - Fix uv resolution.
2. **Capture.**
   - A bare-URL item, including each line of a pasted URL list, becomes `kind: "ref"`.
   - The preview is offline and honest ("new" or "already in library").
   - Submit writes a durable clip job inside capture's rollback and returns at once. A detached single-flight worker clips it.
   - Failure falls back to today's inbox task, plus a reason and a retry hint.
   - Mixed drafts work. Any extra word, route, modifier, child, `@@`, or forced flag (or `-R`) keeps the item a task.
3. **Keep.**
   - A text note with no attachments and a single URL (with an empty, URL, or page-title title) is clipped inline during `pull`, outside the vault lock.
   - Success or a library hit is fsynced, journaled as `ref_created`, and archived.
   - A retryable failure stays in Keep. A permanent failure becomes today's task plus a ⚠️ bullet.
   - Nothing else changes.
4. **Mac.**
   - Present the new kind and add `~/.local/bin` to PATH.
   - Make no timeout, lane, or parsing changes.
5. **Never** auto-`--listen`, never auto-`scan`, never open or fabricate a ref note that does not exist yet.

This honors your intent: a bare link lands in the reading queue, not an inbox. It keeps capture instant and lossless, keeps Keep's "archive only after it's ours" guarantee, and respects the thin-client decision. Build [phases 1–3](#phasing) first: they deliver the phone → Keep → library path with no new background machinery. Then land the capture front door (phases 4–6) on the same core.
