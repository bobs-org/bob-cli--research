# Routing bare-URL captures (bob capture, Bob Mac Capture, bob gkeep pull) into `bob ref create`

Researcher: `cld` · 2026-10-07 · bob-cli `master` @ `6d2911c` · bob-mac-capture @ `4344a54`

## TL;DR

- **Your instinct is right, but don't do it the way you described.** Bare-URL captures
  are reading intents, and the ref library is the right home for them. It has dedupe,
  reading state, and a `^ref` tracker that already walks in the daily REFERENCES review
  tier. The vault shows what happens today: the only bare-URL task ever captured
  (`sase.md`, 2026-10-01) is still open, and it duplicates a ref note that `bob ref find`
  reports as **finished**.
- **Running `bob ref create` synchronously inside `bob capture` is the wrong execution
  model.** A web clip takes 10–150+ s, needs network, uv, and Chrome, and fails for
  normal reasons (login walls, bot walls, thin pages). Today a capture is offline, takes
  about 160 ms, and never loses input. The Mac app kills every `bob` call after 20 s,
  and its submit lane cancels an in-flight submit when a new one starts. Live preview
  runs `capture --dry-run` on every keystroke, so it must stay offline.
- **What I recommend instead:**
  - bob-cli gets one URL-intent classifier.
  - `bob capture` turns bare URL items into `kind: "ref"` items, previewed offline with
    a real library verdict (about 40 ms measured).
  - Submit writes a durable **clip job** and returns at once. A detached, single-flight
    worker runs `bob ref create -f json`.
  - A clip that cannot succeed **falls back to today's inbox task**, with the failure
    reason and a retry command as a child bullet. A URL is never lost.
  - `bob gkeep pull` clips **inline**, because it is already an attended batch drain.
    It archives a Keep note only after a terminal outcome: created, already in the
    library, or a fallback task written.
  - The Mac app stays a thin client. It only decodes and presents the new `ref` item,
    and needs no timeout or lane changes.
- **Requirement adjustments** (full list in §4):
  - A strict "Keep note contains only a URL" rule would miss the most common phone flow.
    Chrome's share-to-Keep fills the **title with the page title** and puts the URL in
    the body.
  - Corp short links (`http://go/…`, `http://cl/…`) must stay tasks. Bryan's history
    contains them.
  - A paste of several newline-separated URLs should work. Today it is a parse error.
  - A prerequisite is `bob ref create -f json`. Today create's output is unversioned
    text, and "already captured" exits 1 like every other failure.
- **Blocking fact for the Mac:** uv is installed only at `~/.local/bin/uv`. Both bob's
  `find_on_path("uv")` and the app's fixed PATH miss it. So any clip started from Bob
  Mac Capture fails today. Fix it in bob, add `~/.local/bin` in the app, or delegate Mac
  clips to athena (§6.4).

---

## 1. The request, restated

1. `bob capture` and Bob Mac Capture: when the capture input is only a URL, run the right
   `bob ref create` instead of capturing a task or note. Bulk captures that include URLs
   must work too.
2. `bob gkeep pull`: a Keep note that contains only a URL is not appended to
   `~/bob/gkeep_inbox.md`. The right `bob ref create` runs instead.
3. Critique the plan, adjust the requirements where justified, and recommend a solution.

## 2. What exists today (evidence)

### 2.1 `bob capture`

- **One grammar, shared by `bob capture` and `capture-parse`** (`capture_language/mod.rs:1-14`).
  It has no URL awareness:
  - `SpanKind` has wikilink kinds but no url/link kind (`capture_language/editor_model.rs:6-57`).
  - `bob capture-parse https://example.com/article?a=1#frag` returns `mode:"task"` with no
    spans and no diagnostics.
- **A bare URL captures as an ordinary inbox task.** Verified with the installed binary:
  `bob capture -d -f json -- https://example.com/article` produces
  `task_line: "- [ ] #task https://example.com/article [created::…]"`,
  `relative_target: "mac_inbox.md"`, `kind: "task"`. The default route is
  `INBOX_FILE = "mac_inbox.md"` (`capture/mod.rs:46`).
- **Batch shape.** One draft holds several items separated by blank lines
  (`capture_language/draft.rs:100-118`).
  - Every line of an item after the first must be a column-zero bullet
    (`draft.rs:429-463`).
  - So **pasting `URL\nURL\nURL` is a parse error today**, while `URL\n\nURL` gives two
    tasks.
  - A URL followed by `- URL` bullets is a valid task with child bullets.
- **Atomicity.** Planning stages edits in memory (`capture/batch.rs:4-138`). The commit
  validates disk preimages, writes temp files plus backups, renames, and rolls back on
  failure (`capture/commit.rs:19-31, 70-118, 120-254`).
  - Clipboard attachments are saved first and cleaned up if the batch write fails. This
    is the precedent for "a side effect outside the staged files, rolled back with the
    batch".
  - An external `bob ref create` would sit **outside** this rollback.
- **JSON contracts.**
  - `bob capture -f json` has no `schema_version`. It is stable plus additive.
    `CaptureItemResult` always carries `ok, dry_run, routed, route, route_label,
    relative_target, target, text, task_line, kind, created, scheduled, placement`
    (`capture/output.rs:222-315`).
  - `capture-parse` has `SCHEMA_VERSION = 1` (`capture_parse.rs:26-29`).
  - `EditorMode` is a closed Rust enum, serialized as snake_case strings
    (`editor_model.rs:152-198`).
- **Cost.** `bob capture --dry-run --no-clip -f json -- https://example.com/a` takes
  ≈ 0.16 s on athena (3 runs, real vault).

### 2.2 `bob ref create` (after bob-cli-4s and bob-cli-4w)

- **Targets.** Markdown, a local PDF, a PDF URL, an arXiv URL, or a web article URL
  (`docs/highlights-create.md`).
- **How a URL is classified.**
  - arXiv URLs are recognized syntactically.
  - **Every other URL is fetched with curl to decide** between PDF and article
    (`highlights_ref/target.rs:74-141`, 300 s cap at `target.rs:80`).
  - Articles then run the uv + Playwright + Chrome adapter (Defuddle, then a Chromium
    print). The adapter's overall timeout is 150 s; Rust kills it at 300 s
    (`clip_adapter.rs:29`).
  - The adapter retries headed under Xvfb on a bot challenge.
- **Output.** create puts a stamped PDF into `xlib/<type>/<stem>.pdf`. It never writes
  the ref note; `bob ref scan` does that later (`docs/highlights-clip.md` §pipeline
  step 5).
- **Dedupe** runs before any fetch, against ref-note `source_url`/`url:` and queued
  intake markers (`highlights_ref/sources.rs`).
  - A PDF-backed hit or an intake hit is **refused with exit 1**, the same code as a
    real failure. Only stderr wording tells them apart.
  - A legacy-only hit warns and captures a fresh copy.
- **No machine contract.**
  - There is no `-f json`. Output is unversioned `key: value` text from `println!`
    (`clip.rs:831-860`, `stamp.rs:506-518`).
  - There is no report struct. The only in-process entry is `highlights_ref::run(argv)`,
    which prints directly.
  - `--dry-run` still uses the network for non-arXiv URLs (`create.rs:461`).
- **Pure helpers I can reuse:**
  - `clip_url::validate_and_clean` (crate-visible): http(s) only, rejects userinfo,
    rejects `localhost`/`.local`/`.internal`/private IP literals, and returns
    `cleaned` and `dedupe_key`.
  - `ArxivPaper::parse`.
  - `ref_library` index/resolve (crate-visible).
  - Note that `validate_and_clean` **accepts single-label hosts**, so `http://go/foo`
    passes.
- **Offline "already in library?" lookup.** `bob ref find <URL> -i -f json` takes
  ≈ 0.04 s on athena's 595-note library (3 runs). It always exits 0 and returns a
  versioned envelope.

### 2.3 `bob gkeep pull`

- **Pipeline:** snapshot via the uv/gkeepapi adapter, then per-host pull lock, vault
  lock, ledger scan, classify, render, CAS write, verify, scoped git commit,
  **content-guarded archive**, and finally the journal (`gkeep/pull.rs:64-524`,
  `docs/gkeep.md`).
  - A Keep note is archived only after its content is provably in the vault.
  - Nothing is ever deleted from Keep.
- **Idempotency comes from the `%%gkeep:v1:<id>:<fp>%%` marker in the vault**
  (`gkeep/ledger.rs`). The journal (`$XDG_STATE_HOME/bob-cli/gkeep/journal.jsonl`) is
  the backstop.
  - A note routed to a ref would leave **no marker**. It would come back as `New` on
    every pull unless it is archived, or the journal records it.
- **Classify order** (`gkeep/plan.rs:170-228`): archived → empty → pinned → shared →
  ledger exact (Pending) / id (Revised) → journal → New. This is the extension point.
- **The adapter drops Keep's link annotations.**
  - `serialize_note` emits id, kind, content, pinned/archived/shared, labels,
    attachments, timestamps, and the note's own keep.google.com permalink
    (`scripts/gkeep_adapter.py:200-236`). It omits annotations.
  - gkeepapi exposes them as `node.annotations.links → list[WebLink]`, each with `url`,
    `title`, `description`, `image_url` and `provenance_url`. I verified this in the
    upstream checkout: `gkeepapi/node.py:312-399, 628`.
  - Adding them is protocol-compatible through `#[serde(default)]`.
- **How Keep stores a shared link.**
  - Sharing a page from Chrome or Android to Keep **autofills the title with the page
    title and puts the URL in the body** ([Android Police, 2016][ap];
    [9to5Google][9to5]).
  - The Chrome extension does the same, with the URL on the first body line
    ([GSMArena][gsm]).
- **Scheduling and flags.** Nothing schedules a pull; it is always a manual
  `bob gkeep pull` (`docs/gkeep.md:373-376`). Dry run, JSON, `--limit`, `--no-archive`
  and `--no-commit` already exist.

### 2.4 Bob Mac Capture

- **Decision record `mac-capture-is-a-thin-client`.**
  - bob-cli is the only implementation of grammar, preview, and vault mutation.
  - New capture behavior lands in bob-cli and `docs/capture.md` first.
  - The app decodes JSON additively, and one aggregate `bob capture` is submitted per
    draft.
- **Submit.**
  - Submit is one `bob capture --format json -- <draft>` call. The panel hides only on
    success (`CapturePanelModel.swift:745-790, 4496-4559`).
  - **Every call has a 20 s timeout**, followed by SIGTERM (`BobProcessClient.swift:17-20,
    277-282`). The code comment says every `bob` call is "local, offline, and expected
    to finish in well under a second".
  - A new call **cancels the previous process in the same lane**
    (`BobProcessClient.swift:581-599`).
  - On timeout the app shows an error with **Retry**. If bob had half-run, Retry could
    duplicate the work.
- **Live preview** runs `capture --dry-run --no-clip` after every edit with a 50 ms
  debounce (`CapturePanelModel.swift:249`). The app asserts that live preview never
  drops `--dry-run` (`BobProcessClient.swift:371-376`).
- **Decoders are tolerant:**
  - `kind`, `placement`, `mode` and span `kind` are plain `String`s.
  - An unknown `kind: "ref"` already renders as a generic item.
  - The required per-item fields are `ok, dry_run, routed, route_label, relative_target,
    target, text, task_line, kind, created, placement` (`CaptureModels.swift:2106-2122`).
    A ref item must still send all of them.
  - The pattern for a new optional object is the "never fails the decode" `try? …`
    style used for `task_complete` (`CaptureModels.swift:2178-2200`).
- **Environment.**
  - The app's PATH is a fixed GUI-safe list:
    `/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin:/usr/local/bin:~/.cargo/bin:~/bin`
    (`BobEnvironment.swift:18-64`). It has **no `~/.local/bin`**.
  - Only a few `BOB_*` variables pass through; `BOB_CHROME` and proxy variables do not.

### 2.5 Host topology (why "where does the clip run?" matters)

- **The vault syncs by git** across athena, apollo and the MacBook. `xlib/` is
  **gitignored**: each Linux host keeps a source queue.
- **The Mac's 15-minute cron** (`maybe_bob_highlights_sync -w`) runs `bob highlights
  scan`. Its pre-scan hook `bob_xlib_pull` rsyncs athena's and apollo's `xlib/` into the
  Mac, and the scan writes ref notes (`docs/vault-git-sync.md:178-215`).
  - athena is the proven clip host: it has Chrome and Xvfb and passed live verification
    in `docs/highlights-clip.md`.
- **Read-only probe of the Mac** (`ssh mac`, 2026-10-07):
  - bob is at `~/.cargo/bin/bob`.
  - `/Applications/Google Chrome.app` is present.
  - **uv is only at `~/.local/bin/uv`**.
  - The crontab carries the 15-minute highlights sync, `bob projects sync` and
    `bob task reconcile`.
- **So a clip started from the Mac app fails today.** bob resolves uv with
  `find_on_path("uv")` (`highlights_ref/clip_adapter.rs:110`, `gkeep/adapter.rs:106`),
  and the app's PATH does not contain `~/.local/bin`.
- **The MacBook is Kelly's machine.** It is offline unless the lid is open
  (`tailnet` memory), so it is a weaker clip host than athena.

### 2.6 Usage evidence from the vault (read-only)

- **Whole vault** (3,353 `#task` lines): exactly **one** task whose text is only a URL.
  - It is `sase.md:20`: `- [ ] #task https://openai.com/index/open-source-codex-orchestration-symphony/`.
  - `bob ref find` reports that URL as `in_library`, reading state **finished**. So the
    task is a stale duplicate of a finished reading.
  - Vault git history since 2026-05 shows only this URL as ever being captured bare.
- **Inbox done archives:** 51 tasks in `gkeep_inbox_done.md` and 125 in
  `mac_inbox_done.md`. Their URL tasks all carry intent text ("Install …", "Explore …",
  "Read through …").
  - Several use **corp short links**: `http://go/bidder-floor-tcpm`, `http://cl/873100546`,
    `http://cs/f:…`, and `*.corp.google.com`.
- **What this means:**
  - A bare URL is almost never meant as a task, so implicit detection has a near-zero
    false-positive base rate.
  - "URL plus words" is common and must stay a task.
  - Corp links appear in this vault and must never be routed to the clipper.

## 3. Is this a good idea? Critique

**Yes, on the merits.**

- A bare-URL task is a low-information inbox row. Its title is a URL, it has no
  dedupe, and it goes stale. The vault's only example is a duplicate of a finished
  reading.
- The ref library is where reading intent belongs:
  - dedupe across URL spellings and arXiv identity;
  - a reading queue (`bob ref list`);
  - agent-visible "have I read this?" answers (`bob_ref` skill);
  - the `^ref` tracker, which still walks in the daily **REFERENCES** tier
    (`docs/freshness.md:485, 505`).

  Routing URLs to refs therefore does **not** drop them out of GTD review.
- Clipping at capture time also preserves the article against link rot and paywall
  drift.

**But the literal plan has real problems:**

| Risk | Why it matters | Mitigation in the recommendation |
| --- | --- | --- |
| Latency | A clip takes 10–150+ s. Capture is meant to be instant, and the Mac app has a 20 s hard timeout. | Submit enqueues a durable job and returns at once. A worker clips. |
| A capture can now fail | Login or bot walls, thin pages, video pages, network, a missing browser or uv. Today a capture never fails for these reasons. | **Fall back to today's inbox task** with the failure and a retry hint. A URL is never lost. |
| Preview lies or hits the network | Live preview runs on every keystroke. create's own dry run fetches. | Offline classification plus an offline library verdict. The route (article/PDF) is a hint until the clip runs. |
| Batch atomicity | create's writes are outside capture's staged-file rollback. | Job files are written in the commit step and rolled back with the batch, like clipboard files. Clips run after the commit. |
| Surprise "I meant a task" | Any implicit rule can misfire. | Only a bare public URL routes. Any extra word, tag, route or modifier keeps it a task. `-R/--no-ref` is an escape hatch. |
| Corp and private links | `http://go/x` passes `validate_and_clean`. | A dotted public host is required, plus an `exclude_hosts` list. |
| Keep share shape | A page title in the Keep title fails "only a URL". | Accept title == WebLink title (or empty). A user-written title stays a task. |
| Re-pull loops (Keep) | A ref leaves no `%%gkeep%%` marker. | A journal `ref_created` event, plus create's dedupe as a second line of idempotency. |
| Cross-host duplicates | Dedupe sees only local `xlib/` plus synced ref notes. | Small window. Use one clip host; Mac clips may delegate to athena (§6.4). |
| Unattended fetch of URLs from Keep | Headless Chrome visits whatever lands in Keep. | Keep shared notes skipped as today. Never auto-clip shared notes, even with `-S`. |

**My answer:** good idea, *if* three invariants hold:

1. A capture never blocks on the network.
2. A URL is never lost: it ends as a ref or as an inbox task.
3. The preview tells the truth before submit.

The literal "run `bob ref create` in place of capture" plan breaks (1) and (2).

## 4. Adjusted requirements (my changes are marked ⚠️)

- **R1 — What counts as a URL item (⚠️ tightened).** An item routes to ref only when
  all of these hold:
  - It is exactly one token: an `http(s)` URL, optionally wrapped in `<…>`.
  - It passes `validate_and_clean`.
  - Its host is dotted and public: no single-label hosts such as `go`, `cl`, `b`, `cs`,
    and no IP literals.
  - Its host is not matched by `exclude_hosts`.
  - The item has no other tokens: no `@route`, `#tag`, `p:`, `s:`, `%`, `+id` or
    operators.
  - The item has no child lines.
  - No explicit destination applies: none of the CLI flags `-r/-s/-t/-S`, and no `@@`
    global destination.

  An explicit destination means "this is a task".
- **R2 — Bulk (⚠️ extended).** Each bare-URL item in a multi-item draft becomes its
  own ref, while other items capture as usual in the same submit.
  - **New:** an item whose every line is a bare URL (a newline-separated paste, which
    is a parse error today) splits into one ref item per line.
  - This is strictly additive. The only previously valid input whose meaning changes is
    "an item that is exactly one bare public URL".
- **R3 — Execution (⚠️ changed from "run `bob ref create` instead").**
  - Capture records a durable **clip job** and returns at once. A detached single-flight
    worker runs `bob ref create`.
  - A permanent failure, or a transient failure that exhausts its retries, **falls back
    to the exact task line capture writes today**, plus a child bullet with the error
    and a retry command.
  - `-w/--wait` makes the CLI block and report the outcome.
- **R4 — Keep shape (⚠️ widened).** A Keep note is URL-only when all of these hold:
  - It is a text note (not a list).
  - It has no attachments.
  - Its body is exactly one URL that meets R1.
  - Its title is empty, equals the URL, or equals (case- and whitespace-normalized) the
    title of a Keep `WebLink` annotation for that URL.

  A title the user wrote stays a task. Multi-URL Keep notes stay tasks in v1
  (follow-up).
- **R5 — Keep archive gate (⚠️ made explicit).**
  - Archive only after a terminal outcome: created, already captured or queued, or a
    fallback task written and verified.
  - Record `ref_created` in the gkeep journal before archiving, so a crash cannot cause
    a re-clip.
- **R6 — Machine contract (⚠️ new prerequisite).** `bob ref create -f/--format
  human|json` with a versioned envelope:
  - an `outcome`;
  - stable `error.kind` values, with a `retryable` flag;
  - an `existing` object for dedupe refusals.

  Exit codes are unchanged.
- **R7 — Thin client (unchanged, restated).**
  - All classification, preview and execution lives in bob-cli.
  - The Mac app decodes an optional `ref` object, presents it, and adds `~/.local/bin`
    to PATH.
  - The app needs **no timeout or lane changes**, because capture returns fast.
- **R8 — Defaults (⚠️ decided).**
  - Status `ready`, so the ref joins the reading queue and the REFERENCES review.
  - No `--listen`: it costs money (≈ $0.15 per paper), takes minutes, and can prompt.
  - Routing can be turned off per entry point in config, and per run with
    `-R/--no-ref`.
- **R9 — Already in the library.** Preview and result say "already in your library:
  `<ref note>` (finished/queued…)". Submit is a successful no-op that writes no task.

## 5. Options considered

### 5.1 Execution model

| Option | How it works | Verdict |
| --- | --- | --- |
| **A. Inline sync** (your plan) | `bob capture` runs create, then commits. | ✗ for capture. It breaks the Mac's 20 s timeout and lane cancel, capture becomes slow and fallible, real results stop matching the dry run (`capture_json_dry_run_matches_real` in `tests/cli/support.rs:565`), and a batch would wait minutes. ✓ for **gkeep**, which is an attended batch drain whose archive needs a terminal outcome now. |
| **B. Inline sync plus a longer Mac timeout** | The app passes about 330 s for drafts with ref items, shows "Clipping…", and allows Escape-to-background. | ✗. It puts complexity in the app, which can only be verified on macOS CI. Lane cancel would SIGTERM an in-flight clip when the next capture is submitted. The Mac stays a weak clip host. |
| **C. Clip-job spool plus detached worker, with fallback task** | Capture writes `ref-jobs/pending/<id>.json` in its commit step, kicks a detached `bob ref jobs run`, and returns. | ✓ **Recommended for capture.** It is instant, never loses input, matches the dry run, and needs no app changes beyond presentation. Cost: a worker, a lock, and a log. |
| **D. Vault sweeper** | Capture writes bare-URL tasks as today. A scheduled job on athena converts untouched bare-URL inbox tasks into refs and closes them. | Credible: it covers every surface for free, including Obsidian and agents. ✗ as the primary design. It edits inbox files from a background host while the Mac appends to them (git-merge churn), the preview cannot tell you anything, and bare URLs show up in the NEW tier until swept. It could serve as a one-off cleanup. |
| **E. Vault-resident cross-host queue** (Mac enqueues, athena drains) | One job file per request inside the vault, carried by git. | ✗ for now. It introduces a new vault concept and depends on sync and timer latency. §6.4's configurable clip command gets athena's reliability without it. |

### 5.2 How to invoke create: subprocess or in-process

Recommendation: **subprocess `bob ref create <url> -f json`** through `current_exe()`,
in its own process group with a timeout and kill. Reasons:

- create already shells out to curl and the Python adapter, so in-process saves nothing.
- A hung Chrome must be killable without killing capture or gkeep.
- The worker has to be a separate process anyway.
- `-f json` is valuable on its own for agents and scripts.

In-process would need create's ~150 `println!` sites (`create.rs` 97, `clip.rs` 50)
refactored into a report anyway. Do
that refactor (`CreateReport`), but use it to *print* both formats rather than calling
create in-process.

Provide a test seam, `BOB_REF_CREATE_COMMAND`, following the existing
`BOB_GKEEP_ADAPTER` pattern. With the real binary, the existing `BOB_WEB_CLIP_ADAPTER`
and `BOB_HIGHLIGHTS_CURL` fakes already allow end-to-end CLI tests.

### 5.3 Explicit sigil or implicit detection

An explicit opt-in (`ref: URL`, or a separate hotkey) costs a keystroke on every
capture to avoid a misfire the vault suggests almost never happens (§2.6). Use implicit
detection with natural opt-outs: add any word, tag or route. Keep `-R/--no-ref` for
scripts and agents that capture arbitrary strings.

## 6. Recommended solution

### 6.1 `bob ref create -f json` (prerequisite; also benefits agents)

- **Add `-f, --format human|json`**, following the house `-f/--format` convention and
  `bob-cli-4a`. Initially it conflicts with `-L`, because listen streams to stdout.
  Stdout carries only JSON; TTY progress stays on stderr.
- **Envelope sketch:**

  ```json
  {"schema_version":1,"ok":true,"command":"ref create","dry_run":false,
   "outcome":"created|attached",
   "target":{"input":"…","route":"article|pdf_url|arxiv|pdf|markdown","source_url":"…","dedupe_key":"…"},
   "pdf":"…/xlib/blogs/foo.pdf","ref_type":"blogs","stem":"foo","title":"…",
   "author":null,"published":null,"captured":"2026-10-07","status":"ready",
   "warnings":["already in the library as ref/ai/x.md, a note without a Highlights PDF; …"],
   "existing":null,
   "error":null}
  ```

  - On failure: `ok:false` plus `error:{kind,message,hint,retryable}`.
  - `kind` is one of: `already_captured` and `already_queued` (both filling `existing`
    with the ref note and PDF), `invalid_url`, `private_host`, `network`, `timeout`,
    `http_status`, `unsupported_content`, `blocked`, `thin`, `browser`, `dependency`,
    `collision`, `render`, `internal`.
  - **Exit codes stay 0, 1, 2 and 130.**
- **Fix uv resolution once.** A shared `resolve_uv()` checks PATH, then `~/.local/bin/uv`
  (the uv installer default), `~/.cargo/bin/uv`, then `/opt/homebrew/bin/uv`. Use it in
  `clip_adapter.rs` and `gkeep/adapter.rs`. `bob ref doctor` prints which uv it found.

### 6.2 One URL-intent classifier plus config

- **Pure function**, e.g. `crate::native::url_intent::classify(raw) -> Option<UrlIntent
  { web: WebUrl, route_hint: Article|PdfUrl|Arxiv }>`. It needs no filesystem or network.
  - It implements R1's URL tests.
  - `route_hint` is syntactic (arXiv parse, `.pdf` path suffix). It is reported as a
    *hint*, never as fact.
  - Capture's grammar layer and gkeep's planner both call it.
- **Config** (house `highlights:` section, beside `listen_command`):

  ```yaml
  highlights:
    url_routing:
      capture: true          # bare-URL capture items become refs
      gkeep: true            # URL-only Keep notes become refs
      exclude_hosts:         # suffix match; these stay tasks
        - corp.google.com
        - docs.google.com
        - drive.google.com
        - keep.google.com
        - youtube.com
        - youtu.be
      # Optional: how a clip job runs (placeholders shell-quoted by bob, like listen_command)
      clip_command: bob ref create {url} -f json
  ```

  The default exclusion list is a proposal for Bryan to confirm (§7).

### 6.3 `bob capture` and `capture-parse`

- **Grammar.** Add a whole-item claim, "bare URL item", just before the generic
  `resolve_line` (`capture_language/item.rs:220`). Add the R2 split for items made only
  of URL lines. In `capture-parse`, report `mode: "ref"` and a span kind `ref_url`. Both
  are additive; the app tolerates unknown strings.
- **Plan and dry run (offline).**
  - For each ref item, call the classifier, then do an offline library lookup that
    reuses the `ref find -i` index (≈ 40 ms).
  - The item JSON fills the required legacy fields so older app builds keep decoding,
    and adds an optional `ref` object:

  ```json
  {"ok":true,"dry_run":true,"routed":true,"route":"ref","route_label":"Reading queue",
   "relative_target":"ref/","target":"/Users/…/bob/ref","text":"https://…",
   "task_line":"https://example.com/post","kind":"ref","created":"2026-10-07",
   "scheduled":null,"placement":"queued",
   "ref":{"url":"https://…","cleaned_url":"…","dedupe_key":"…","route_hint":"article",
          "library":{"verdict":"not_found|in_library|in_intake|legacy","path":null,"reading_state":null},
          "job":{"id":null,"state":"planned"},
          "fallback":{"relative_target":"mac_inbox.md","task_line":"- [ ] #task https://… [created::…]"}}}
  ```

  - An `in_library` or `in_intake` verdict sets `placement: "unchanged"`, and submit
    writes nothing for that item (R9).
- **Commit.**
  - Write one job file per ref item to `$XDG_STATE_HOME/bob-cli/ref-jobs/pending/`,
    atomically (temp file, fsync, rename), then write the staged task files.
  - If the batch write fails, delete the job files this run created. This mirrors
    clipboard cleanup in `commit.rs:19-31`.
  - Then kick the worker.
  - The result reports `placement: "queued"` and `ref.job.id`. This JSON equals the dry
    run apart from the job id and `dry_run`.
- **New flags** (alphabetical, each with a short alias, per `cli_rules`):
  - `-R, --no-ref`: capture bare URLs as tasks.
  - `-w, --wait`: run this draft's clip jobs in the foreground and report the outcomes.
    It still falls back.

### 6.4 Clip jobs: spool and worker

- **Job file:**
  - Fields: `{v, id, url, cleaned_url, dedupe_key, source:{kind:"capture",client}, created_at,
    attempts:[…], fallback:{route, task_line}}`.
  - It stays outside the vault, because the vault is git-synced.
  - The finished-jobs log is `ref-jobs/jobs.jsonl`.
- **Kick.**
  - `bob capture` spawns `current_exe() ref jobs run -q` **detached**: new session or
    process group, with stdin, stdout and stderr redirected to `ref-jobs/worker.log`.
    The redirect matters: a child that inherited the Mac app's stdout pipe would hold
    the app's read open until the clip finished.
  - The worker is single-flight through a lock file, like gkeep's `pull.lock`. Before it
    exits, it releases the lock and re-checks `pending/`, which closes the classic
    lost-wakeup race.
- **Run one job.**
  - Run `clip_command` (default `bob ref create {url} -f json`) with a timeout of about
    360 s and a process-group kill. Then map the JSON:
    - `created`, `already_captured` or `already_queued` → done. Log it and optionally
      notify.
    - `retryable` (network, timeout) → leave the job pending. After 3 attempts or 24 h
      → fallback.
    - Anything else → fallback now.
  - **Fallback** goes through the capture library in-process, with routing disabled. It
    reuses the stale-preimage guard. It writes the original task line plus a child
    bullet such as:
    `- ⚠️ Clip failed (blocked: the page needs a login) · retry: bob ref clip <url> -H saved.html`
- **Visibility.**
  - `bob ref jobs` (bare = read-only list, allowed by `cli_rules`) shows pending and
    recent jobs. Avoid naming it "queue": `queued` is already a ref reading state.
    Avoid "inbox" and "intake", which are also taken.
  - `bob ref doctor` gains a `clip jobs` row warning about stale pending jobs.
  - Notifications are optional: `notify-send` already exists in `notify.rs:204`, and
    `osascript display notification` would serve the Mac.
- **Clip host choice (Mac).** Two equally simple settings:
  - **Local** (default): fix uv resolution (§6.1), then run `bob ref doctor` on the Mac
    under the app's environment until the web-clip rows are green. PDFs land directly in
    the Mac's `xlib/`, and the 15-minute scan writes the note.
  - **Delegate to athena:** `clip_command: ssh athena bob ref create {url} -f json`.
    athena is the proven clip host. Its `xlib/` is already drained to the Mac by
    `bob_xlib_pull`, through the same ssh trust path the Mac cron uses.
  - I lean towards **delegating**: the MacBook is shared, often asleep, and has never
    been clip-verified. Bryan decides (§7).

### 6.5 `bob gkeep pull`

- **Adapter.** Emit `links: [{url, title}]` from `note.annotations.links`, with
  `#[serde(default)]` on `KeepNote`. The fingerprint and the archive guard are
  unchanged, because both hash only title, text and items.
- **Classify.** After the ledger and journal checks, a `New` note matching R4 becomes
  `PlanAction::CreateRef`. Ledger hits (notes already written as tasks) keep today's
  behavior. A journal `ref_created` match becomes `ArchiveOnly`.
  - Count `CreateRef` as actionable, so `--limit` covers it.
  - The exhaustive matches in `plan.rs` and `list.rs` guide the compiler. The
    non-exhaustive `matches!` sites in `pull.rs` (lines 240, 726, 936, 1034, 1191,
    1276) need a manual review.
- **Execute.**
  - Run clips **before taking the vault lock**, in a pre-pass under the per-host pull
    lock. The vault lock waits 60 s and is shared with vault-sync and nightly, so it
    must not be held across minutes of Chrome.
  - Run them sequentially, with the spinner showing "clipping `<host>`…".
  - Map the same outcomes as §6.4: success or dedupe → append `ref_created` to the
    journal; failure → the note joins the normal write set, rendered exactly as today
    plus the ⚠️ child bullet.
  - Then run the normal locked write, verify and commit. The archive set becomes
    verified writes ∪ `ArchiveOnly` ∪ ref successes (`pull.rs:717-736`).
- **Dry run** stays offline: `action: "create_ref"` plus the library verdict.
- **JSON** additions (documented in `docs/gkeep.md`):
  - `action: "create_ref"`;
  - a per-note `ref:{url,outcome,pdf,existing,error}`;
  - `summary.refs`.
- **Human row:** `✓ ↗ ref  example.com/post → xlib/blogs/post.pdf`.
- **Flags.** `-R/--no-ref` for symmetry. Shared notes never auto-clip, even with `-S`.

### 6.6 Bob Mac Capture (presentation only)

- **Decode** an optional `ref` object with the tolerant `try?` pattern, plus a
  `CaptureRefPresentation` gated on `kind == "ref"`.
- **Preview card** examples:
  - "Reading queue · clip **example.com/post** · new to library"
  - "Already in library: *Title* (finished)"
- **Status line:** "Queued for clipping → reading queue".
- **Notification wording:** "Queued: example.com".
- **Cmd-Return** opens `ref.library.path` when the URL is already in the library, and
  does nothing otherwise. There is no ref note to open yet.
- **`ref_url` span** gets a link color category.
- **Environment:** add `~/.local/bin` to `BobEnvironment` PATH as defense in depth.
- **Fixtures:** record real `bob capture -f json` output for ref items from a bob-cli
  build, following the repo's existing practice.
- **No change** to the timeout, lanes or submit flow.

### 6.7 Docs and decisions

- **`docs/capture.md`:** a "URL items" section covering grammar, JSON and opt-outs.
- **`docs/gkeep.md`:** classification, outcomes and JSON.
- **`docs/highlights-create.md`:** `-f json`, and fix the drift noted in §8.
- **New `docs/ref-jobs.md`.**
- **After landing**, propose a `decisions` record through `/sase_memory_write`. Its
  claim: "A bare public URL is a reading intent: it becomes a ref through a background
  clip job and falls back to an inbox task. Capture never blocks on the network."
  Rejected alternatives: inline sync, a longer app timeout, and the vault sweeper.

### 6.8 Phasing (one epic)

| # | Phase | Size |
| - | ----- | ---- |
| 1 | `ref create -f json`: `CreateReport` refactor, error kinds, `retryable`, `resolve_uv()`, doctor uv row | medium |
| 2 | URL-intent classifier plus `highlights.url_routing` config and exclusions | small |
| 3 | Capture grammar, `capture-parse` mode and span, offline plan and dry-run JSON, R2 split, `-R`, docs | medium |
| 4 | Clip-job spool and worker (`bob ref jobs`, `jobs run`), detached kick, retry and fallback writer, `-w`, doctor row, `clip_command` | medium–large |
| 5 | gkeep: adapter links, `CreateRef`, pre-pass execution, journal event, fallback, JSON and human output, `-R`, docs | medium |
| 6 | Mac app presentation, PATH, and fixtures (macOS CI) | medium |
| 7 | Live verification on athena and the Mac: article, arXiv, PDF URL, blocked site → fallback, corp link → task, Keep share-sheet sample | small |

Order: 1 → 2 → 3 → 4. Phase 5 can start after 1 and 2. Phase 6 can start once 3's JSON
is frozen.

### 6.9 Tests

- **Unit tests:**
  - the classifier table: corp links, IP literals, `<URL>`, trailing tokens, `@@`,
    child lines;
  - gkeep classification (`plan.rs` helpers);
  - job-state transitions.
- **CLI tests:**
  - capture dry run vs real for ref items;
  - batch rollback deletes job files;
  - `-w` with `BOB_REF_CREATE_COMMAND`, or the real create with
    `BOB_WEB_CLIP_ADAPTER`/`BOB_HIGHLIGHTS_CURL` fakes;
  - fallback task bytes;
  - gkeep pull with `FakeAdapter` link annotations: archive gating, journal re-pull
    idempotency, JSON.

## 7. Open questions for Bryan

1. **Clip host for Mac captures:** local Mac (after uv and doctor fixes), or delegate to
   athena through `clip_command`? I recommend athena.
2. **Default `exclude_hosts`:** confirm the list in §6.2. Add `x.com`/`twitter.com`?
3. **Status for captured refs:** `ready` (reading queue) or `next`?
4. **Already-in-library recaptures:** keep them a no-op, or "bump" the ref (for example
   to `next`)? This needs a ref write verb, which bob-cli-4w ruled out of scope.
5. **Keep share-sheet shape:** please share one link from your phone to Keep, then run
   `bob gkeep list -f json` (after the adapter emits `links`) to confirm the
   title/body/annotation shape before R4 is frozen.
6. **Notifications** for background clips: wanted, or is the fallback task enough?
7. **Later:** an opt-in listen operator, or multi-URL Keep notes?

## 8. Incidental findings

- **Doc drift:** `docs/highlights-create.md:272` says curl runs with `--max-time 30`, but
  the code passes 300 (`highlights_ref/target.rs:80`). This came from the bob-cli-4s
  landing fix "300s PDF timeout".
- **Mac environment:** the app's fixed PATH (`BobEnvironment.swift`) lacks `~/.local/bin`,
  and bob resolves uv only from PATH. Every uv-backed command run from the app (article
  clip, gkeep) would fail on this Mac.
- **Vault cleanup:** `sase.md:20` holds a bare-URL task that duplicates a finished ref
  note. Bryan can close or delete it.
- **SSRF hardening:** the Rust-side guard (`clip_url::reject_private_host`) checks only
  hostname suffixes and IP literals. A public-looking hostname that resolves to a
  private address reaches curl's classification fetch before the adapter's DNS check
  runs. This was low risk with manual targets, but it matters more once Keep feeds URLs
  automatically. It is worth a resolved-address check in `fetch.rs`.

I filed no beads: the lead synthesizes five reports, and these items belong in the
resulting plan.

## Sources

- bob-cli source and docs at `6d2911c`: `src/native/capture/*`, `src/native/capture_language/*`,
  `src/native/highlights_ref/*`, `src/native/gkeep/*`, `scripts/gkeep_adapter.py`,
  `docs/{capture,gkeep,highlights-create,highlights-clip,highlights-ref-sync,vault-git-sync,freshness}.md`.
- bob-mac-capture at `4344a54` (opened via `sase repo open`): `Sources/CaptureCore/{BobProcessClient,BobEnvironment,CaptureModels}.swift`,
  `Sources/BobMacCapture/{CapturePanelModel,NotificationService}.swift`.
- Plans and epics: `plan:202610/bob_ref_reference_library.md`, `plan:202610/highlights_create_listen.md`,
  beads `bob-cli-4s`, `bob-cli-4w`. Decision `decisions:mac-capture-is-a-thin-client`.
- gkeepapi upstream checkout (`gh:kiwiz/gkeepapi`, `src/gkeepapi/node.py`): `WebLink`, `NodeAnnotations.links`.
- Measurements on athena (2026-10-07):
  - `bob ref find … -i -f json` ≈ 0.04 s;
  - `bob capture -d --no-clip -f json` ≈ 0.16 s;
  - read-only vault scans of `~/bob` and its git history;
  - read-only `ssh mac` probe.
- Keep share behavior: [Android Police — Keep shares links as new notes][ap],
  [9to5Google][9to5], [GSMArena — Keep Chrome extension][gsm].

[ap]: https://www.androidpolice.com/2016/04/20/google-keep-now-shares-links-as-new-notes-creates-labels-using-hashtags-gains-an-official-chrome-extension-and-more/
[9to5]: https://9to5google.com/?p=139398
[gsm]: https://www.gsmarena.com/google_keep_chrome_extension_lets_you_create_notes_linked_to_the_websites_you_visit-blog-17861.php
