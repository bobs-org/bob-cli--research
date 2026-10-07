# Capture and Gkeep URL routing into `bob ref create`

- **Researcher:** grk
- **Date:** 2026-10-07
- **Question:** After `bob highlights create` gained URL targets (epic `bob-cli-4s`) and became `bob ref create` (epic `bob-cli-4w`), should `bob capture` / Bob Mac Capture and `bob gkeep pull` send URL-only input to `bob ref create` instead of writing an inbox task? Is that a good idea, and how should it be implemented?

## Headline

**Yes, with a narrower predicate and a hard split between recognizing a URL and fetching it.** Pasting a lone `https://…` into capture, or sharing a link into Google Keep, currently becomes an inbox *task*. That is a leak in the pipeline 4s/4w just finished: the library intake already knows how to stamp that URL. Close the leak.

Do not implement the request as "if the draft looks like a URL, shell out to `bob ref create`." Capture's live preview, Mac Capture's 20-second process timeout, gkeep's archive-after-verify invariant, and Keep's real share-to-Keep shape (page title plus URL) all break under that reading.

## Verdict

Build this as:

1. A shared, syntactic *lone-URL* predicate.
2. A new whole-item capture kind `ref_create`, following `!note:id`, `=x`, and `+N`.
3. A new gkeep `PlanAction::RefCreate` that never writes `gkeep_inbox.md`.
4. An in-process call into `highlights_ref::create` (extract `create_pdf` as crate-visible). No nested `bob` subprocess.
5. Parse and `--dry-run` stay local (syntax + dedupe). Fetch/clip/stamp run only on real submit/pull.

Mac Capture stays a thin client: it renders a new kind bob already reported, and raises the submit timeout from that kind. It does not parse URLs.

---

## Critique of the stated plan

The product intent is right. Several of the written requirements are underspecified or will ship a worse inbox than today if taken literally.

### 1. "The only capture input" vs bulk URLs vs mixed drafts

The request says a URL should be the *only* capture input, then adds that bulk URL capture should work. Those two statements agree if "input" means *the whole draft*, and bulk means several blank-line-separated URL items.

They do not say what happens when a URL item shares a draft with `buy milk`. Capture today is all-or-nothing: any item failure rolls the whole batch back (`src/native/capture/cli.rs` long_about; `plan_capture_batch` then `commit_capture_batch`). `bob ref create` is a network + PDF pipeline that cannot join that note transaction. Mixed drafts therefore need an explicit policy. Leaving it implicit will produce partial writes that Mac Capture treats as total failure (it keys off process exit and a single JSON envelope).

**Adjustment:** v1 accepts an all-URL draft (one or more URL items). A mixed URL+task draft fails with a teaching error before any write. That matches the wording and keeps capture's rollback contract.

### 2. "Run the appropriate `bob ref create` command"

Two readings, and the subprocess reading is the wrong one.

- **Wrong:** `std::process::Command` / Mac calling `bob ref create <url>` as a second binary. Capture already *is* the bob process Mac spawned. Nested bob inherits PATH/version/env bugs, has no capture JSON, and violates "submits each draft as one `bob capture` call" (`decisions:mac-capture-is-a-thin-client`; Bob Mac Capture README).
- **Right:** the same `create_pdf` engine `bob ref create` uses, called in-process, with results mapped onto capture JSON (`kind: "ref_create"` plus an additive `ref_create` object, the `task_complete` pattern in `src/native/capture/output.rs`).

`create_pdf` is currently a private function in `src/native/highlights_ref/create.rs`. The article route already calls the clip engine in-process (`create_article_route`). Extracting a crate-visible entry is a small, local refactor, not a new pipeline.

### 3. "Contains only a URL" will miss the common Keep note

Google Keep's share-from-browser note is almost never a title-less URL. Typical shape, from Keep/gkeepapi and from how `KeepContent` is modeled (`title`, `text`, `items` in `src/native/gkeep/model.rs`):

| Keep fields | Strict "only a URL"? | What the user meant |
| --- | --- | --- |
| title empty, text = URL | yes | library capture |
| title = URL, text empty | yes | library capture |
| title = page title, text = URL | **no** | still a saved link |
| title = page title, text = URL + a sentence | no | inbox task (commentary) |
| list with one URL item | no | inbox task |
| any attachment | no | inbox task |

`gkeep` already treats Keep text as data, never capture grammar (`docs/gkeep.md`, Rendering). Detection must be a content predicate on `KeepContent`, not "run this note through `bob capture`."

A live `gkeep_inbox.md` check on 2026-10-07 found three thought tasks and no URL-only notes (the only `http` hits are `Source: [Google Keep](https://keep.google.com/…)` children). That does not argue against the feature; it argues the inbox is already for *thoughts*, which is what URL routing should preserve.

**Adjustment:** a Keep note is a library URL when, after the existing renderer normalization, it has no attachments, is not a list, and is one of: lone URL in title or text with the other empty; the same URL in both; or a non-URL title plus a single URL body and nothing else. Pass the title to create as `-T` in the title-plus-URL case.

### 4. Live preview must not fetch

Mac Capture's typing loop is:

1. `bob capture-parse --format json` (lexical, no vault, no network — `src/native/capture_parse.rs`).
2. `bob capture --dry-run --no-clip --format json` for the live card (`BobProcessClient.captureLivePreview`).

`bob ref create` classifies generic URLs by *fetching* them (`fetch_and_route` in `src/native/highlights_ref/target.rs`). The web-clip adapter default timeout is **300 seconds** (`DEFAULT_TIMEOUT_SECS` in `clip_adapter.rs`). Mac's process timeout is **20 seconds**, with the comment that every bob invocation is "local, offline, and expected to finish in well under a second" (`BobProcessClient.defaultTimeout`).

If `--dry-run` on a URL item calls create's planner, every keystroke after `https://` will hang or time out, and the preview card will lie or go red.

**Adjustment:** parse and capture `--dry-run` for `ref_create` items are syntactic plus *local* dedupe (`sources::collect_recorded_source_urls` already scans `ref/` and `xlib/` with no network). Fetch, clip, pandoc, and stamp run only on a real submit / a real `gkeep pull`.

### 5. `create` does not write a ref note

`bob ref create` installs a marker-stamped PDF under `xlib/<ref-type>/` and prints `next: bob ref scan` (`print_next_step` in `src/native/highlights_ref/stamp.rs`). `scan` is what writes `ref/`. Routing capture/gkeep at create is the correct boundary (that was the 4s consensus). Do not also run `scan` from capture or pull. Surface the next step in capture JSON and in the Mac notification.

### 6. URL-as-todo is a real gesture

A lone URL in capture today becomes `- [ ] #task https://…` in `mac_inbox.md`. That is sometimes what Bryan wants: a *read this* task, not a library PDF. Auto-routing every URL-only item removes that gesture unless there is an escape hatch.

The cheap hatch is already in the grammar: any extra body text (`read https://…`), any `@route` / `s:` / `p:` / `%` / authored child, or any forced `--route`/`--section`/`--task` flag means the item is a task. Add `--as-task` for the rare "this exact URL, as an inbox task" case.

Invalid URLs (private host, userinfo, non-http scheme — `clip_url::validate_and_clean`) must **fail**, not fall back to the inbox. Fallback would hide create's safety checks (bob-cli-4v is the leftover private-host hole on IPv4-mapped IPv6).

### 7. Do not `--listen` from these gestures

`--listen` streams TTS and can run for minutes. Capture is a hotkey; gkeep pull is a drain. Attach mode already exists for a later `bob ref create <url> -L` on a captured target (4s.5). Default these paths to create without listen and without companion-audio discovery surprises (`--no-audio` is the conservative mapping).

### 8. gkeep must not call capture

gkeep's contract is: snapshot Keep → classify → write verified Markdown with `%%gkeep:v1:<id>:<fp>%%` → git commit → archive only with a content guard (`src/native/gkeep/pull.rs`). A URL note that never lands in `gkeep_inbox.md` still needs:

- a `written` journal record so a later pull is `ArchiveOnly` rather than a second create (the journal is the backstop when a marker is missing — `Journal::has` in `ledger.rs`);
- archive only after create succeeded;
- no vault-task verify step (there is no task to parse back).

Running `bob capture '<url>'` from pull would write `mac_inbox.md`, go through capture grammar, and skip the gkeep marker/journal. That is the wrong command.

---

## Justified requirement changes

These are deliberate diffs from the request. Each is required for the design above.

1. **All-URL drafts only in capture v1.** One or more blank-line-separated URL items. Mixed URL+task drafts error with a teaching message. Bulk URLs are supported; mixed batches are a later epic.
2. **Keep "URL note" includes title + single URL body.** Strict "the note contains only a URL" would miss share-to-Keep. Commentary, lists, and attachments stay inbox tasks.
3. **Recognize locally; fetch only on commit.** `capture-parse` and `capture --dry-run` never call `fetch_and_route` or the clip adapter. Submit and `gkeep pull` do.
4. **In-process `create`, not a `bob ref create` subprocess.** Same engine, capture/gkeep JSON and journal of our own.
5. **No auto-scan, no auto-listen.** Intake PDF + `next: bob ref scan`. Listen is a later, explicit `bob ref create -L` (attach).
6. **Escape hatch:** extra capture text/markers/flags, or `--as-task`. Invalid URLs error.
7. **gkeep journals a `written` event with the intake path** after a successful create, then archives. Create failure leaves the Keep note unarchived and unwritten. Dedupe hits that refuse (PDF-backed library copy) still count as success for archive: the URL is already in the library; do not retry clip forever.
8. **Mac Capture is in scope as a renderer and timeout, not a parser.** New `EditorMode`, span, additive JSON object, preview card, submit timeout. No Swift URL regex.

---

## What exists today (evidence)

### 4s and 4w already did the hard part

- **`bob-cli-4s`** (closed): `bob highlights create <TARGET>` accepts Markdown, local PDFs, PDF URLs, arXiv URLs, and web article URLs; articles go through the clip engine; `--listen` attaches on a duplicate.
- **`bob-cli-4w`** (closed): canonical command is `bob ref`; `highlights` / `highlights-ref` are permanent hidden aliases; **`bob-cli-4w.9`** made legacy-only `url:` hits warn-and-capture instead of dead-ending.
- Classification is syntactic first (`looks_like_url` = trimmed `http://` or `https://`), then URL validation (`clip_url::validate_and_clean`), then local dedupe, then fetch to split PDF-URL vs article (`src/native/highlights_ref/target.rs`).
- Defaults: articles → `-t blogs`, PDFs/arXiv → `papers`, parent `obsidian_ref`, status `ready` (`create.rs`).

Capture and gkeep should reuse that stack, not re-implement clipping.

### Capture is a whole-item operator grammar

`capture_language` is the single grammar for `bob capture` and `bob capture-parse`. Whole-item operators are claimed *before* the item becomes an inbox task: `!note:block-id`, `=x`, `=`/`=<X>`, `+N`/`-N`, `++N`/`--N`, solo `@route:id` links (`src/native/capture_language/item.rs`, `CaptureKind` in `model.rs`).

A URL-only item is the same shape: the entire item (after marker strip) is one http(s) URL, no children, no clip/schedule/priority/route. It should become `CaptureKind::RefCreate`, not a `Task` whose body happens to be a URL.

CLI rule that still applies: never add a subcommand under `bob capture` (TEXT would swallow it). This is a new *kind*, not `bob capture ref`.

`capture-parse` is "purely lexical and completely read-only: it never opens the vault, never reads the clipboard, never touches the filesystem." Dedupe during *parse* would violate that. Dedupe belongs on `capture --dry-run` (already reads the vault for every other kind) and on submit.

### Mac Capture is a thin client with a 20s ceiling

Bob Mac Capture:

- Parses nothing. `captureParse` / `captureLivePreview` / `capture` are the three bob calls (`BobProcessClient.swift`).
- Live-preview falls through to `standardPreviewItem` for unknown kinds (`CapturePanelView.previewItem`). A URL that is still `kind: "task"` will preview as an inbox task in `mac_inbox.md` — a lie — until Mac learns `ref_create`.
- Additive JSON is the established contract (`CaptureParseResponse` and `CaptureCommandSuccess` decode missing keys as nil; schema version 1 is never bumped for new optional fields).
- Submit uses the same 20s timeout as parse. A real article clip can take up to 300s. Submit must pick a longer timeout *from bob's parse mode*, not from a Swift URL check.

### gkeep pull is a guarded drain, not a capture frontend

Pipeline (docs + `pull.rs`):

1. Host pull lock + vault maintenance lock.
2. Snapshot Keep.
3. Classify: archived / empty / pinned / shared / pending / revised / new (`plan.rs`).
4. Render new/revised notes as `#task` blocks with a `Source:` child and `%%gkeep:v1:…%%` marker (`render.rs`).
5. Atomic write, re-read, parse-verify, optional git commit of `gkeep_inbox.md`.
6. Archive each verified note with a content fingerprint guard.

`note.url` on `KeepNote` is the Keep UI link (`https://keep.google.com/u/0/#NOTE/…`), not the shared article. Do not treat it as the capture target.

Empty notes are skipped and never archived. A URL note is not empty.

`bob gkeep` is not on `nightly` (`src/native/nightly.rs` has no gkeep reference). Pull stays a hand-run drain; making it slower for URL notes is acceptable if `list` / `pull -d` preview the routing and `--limit` still caps work. Do not parallelize create (xlib races, clip adapter).

---

## Recommended design

```text
                    ┌─ capture-parse ── syntactic lone-URL → mode ref_create
                    │
  typed/pasted URL ─┼─ capture --dry-run ── validate + local dedupe, no fetch
                    │
                    └─ capture (submit) ── create_pdf in-process ── xlib/…pdf
                                                                      │
Keep note ── gkeep classify ── PlanAction::RefCreate ── same create_pdf
                                      │                      │
                                      │                      ├─ journal written (intake path)
                                      │                      └─ archive Keep
                                      └─ (non-URL notes) existing inbox write
```

### Shared predicate

Put one helper next to `clip_url`, used by capture *and* gkeep:

```text
lone_http_url(text) -> Option<WebUrl>
```

Rules:

- Trim; accept a single token.
- Optional wrapping `<>` (mail paste).
- Must pass `validate_and_clean` (http/https, no userinfo, no private host).
- Reject `www.example.com` without a scheme (create already requires `http://` or `https://`).
- Reject two URLs on one line, markdown `[title](url)`, and trailing prose.

Keep wrapper:

```text
keep_library_url(note) -> Option<(WebUrl, Option<title>)>
```

using the table in the critique. Labels do not disqualify. Pinned/shared skips stay as they are.

### Capture

Insert the claim in `parse_capture_item` after the existing whole-item operators and before ordinary task parse:

- Parent body is a lone URL.
- No authored children, clip, `s:`, `p:`, `@route` / `@@`, or forced destination flags.
- `--as-task` disables the claim.

On that claim:

| Surface | Behavior |
| --- | --- |
| `capture-parse` | `mode: "ref_create"`, span kind `url` over the URL bytes, additive `ref_create: { url, cleaned }`. Still no IO. |
| `capture --dry-run` | Validate; local dedupe; JSON `kind: "ref_create"` with `already_in_library` / `legacy_path` / planned `-t` when knowable without fetch (arxiv vs generic URL). Human: `would capture reference https://…`. |
| `capture` (write) | `create_pdf` with `--no-audio`, default parent/status, `-T` omitted unless we add a later grammar for it. Map create's report onto `ref_create` (source_kind, target PDF, next step). Human: `captured reference → xlib/blogs/<stem>.pdf` plus `next: bob ref scan`. |
| Bulk | Sequential creates. Stop on first failure. Earlier PDFs stay (same as a shell loop of `bob ref create`). Document that bulk is not atomic across URLs. |
| Mixed draft | Usage error: `URL items cannot mix with tasks; capture the URL alone, or add prose so it stays a task.` |

PDF-backed dedupe refusal on submit is a *successful* capture item with `already_in_library: true` and no new PDF (mirror create's attach-without-listen outcome). Legacy-only hits warn and still capture, as 4w.9 specified.

### Mac Capture

Thin-client work, all driven by bob JSON:

1. Decode additive `ref_create` on parse and on capture success (tolerate absence).
2. Preview card: "Reference" / cleaned URL / "xlib/…" or "already in library", never `mac_inbox.md`.
3. Footer status from that object, same pattern as `soleTaskCompletePresentation`.
4. `submit` timeout: if the last parse mode (or any item mode) is `ref_create`, use ~300s+ (clip's ceiling), not 20s. Live preview stays 20s because dry-run does not fetch.
5. Notification: intake path + "next: bob ref scan". Open-note action can target the PDF or wait for scan; do not pretend a `ref/` note exists yet.

No URL regex in Swift. If an older bob omits the kind, the app keeps today's inbox-task preview — version skew is already how every additive kind works.

### gkeep

New `PlanAction::RefCreate` (and a `NoteState` if list/JSON need a distinct glyph; otherwise reuse `new`/`revised` with a different action).

`pull -d` prints `would capture reference <url> [-T title]` instead of the Markdown task block.

`pull` write path:

1. Split planned notes into inbox writes vs ref-creates.
2. Existing CAS write/verify/commit for inbox notes only. If that set is empty, skip the write exactly as today's pending-only pull does.
3. For each `RefCreate` note, sequentially: `create_pdf` (with `-T` when we have a page title); on success or PDF-backed dedupe hit, append `JournalEvent::Written` with `path` = intake PDF (or existing library path); then include that note in the archive batch.
4. Create failure: no journal, no archive, note stays in Keep, pull exits 1 after finishing the rest (or stop — prefer *continue*, report per note, like archive_refused). Inbox writes already committed stay committed.
5. `list` shows these Keep rows as `ref` / `would capture` so the drain is visible before pull.

Do not put a `%%gkeep%%` marker in the PDF or the future ref note. The journal is the idempotency store for this path. A later `scan` writing `ref/` must not be required for the next pull to treat the Keep note as pending.

### Library API

Make `create_pdf` (or a URL-only wrapper) `pub(crate)` with a structured result:

```text
CreateOutcome { source_kind, target, sidecar, title, already_in_library, legacy_path, next_step }
```

CLI `bob ref create` keeps printing human text. Capture and gkeep consume the struct. Tests stub `BOB_WEB_CLIP_ADAPTER` / fake curl the same way 4s CLI tests already do.

---

## Alternatives considered

| Approach | Why not v1 |
| --- | --- |
| Mac detects URL and calls `bob ref create` | Breaks the thin-client decision; duplicates validation; two processes; no capture JSON. |
| `bob capture --ref` flag | Extra gesture; loses paste-URL magic; still needs parse/preview work. |
| Keep URL notes as inbox tasks tagged for a later `bob gkeep refs` | Pollutes `gkeep_inbox.md`, which the request wants to avoid; second command to remember. |
| Queue URLs to a file, create asynchronously | Archive timing and failure retry become a new product. Pull is already a batch. |
| Mixed capture batches with partial commit | Breaks capture's rollback contract and Mac's single-envelope submit. Revisit later. |
| Auto `bob ref scan` after create | Scan is the Mac-side Highlights step with hooks; 4s/4w kept create/scan split. |
| Auto `--listen` | Minutes of TTS on a hotkey / drain. Attach exists. |
| Fall back to inbox on create failure | Hides clip/private-host errors; reintroduces the inbox pollution this feature exists to stop. Leave in Keep / fail the capture item. |
| Prefix `https` onto `www.` / bare arXiv ids | Surprising. Type the real URL, or add prose to keep it a task. |

---

## Risks

- **Clip latency and failure.** Bot-walled pages already route to the clip engine (403/429/503). A phone-shared Substack/Twitter URL can sit in the 300s timeout and still fail. Pull must show progress per URL; capture must not freeze the live preview (it will not, if dry-run stays local).
- **Intake vs library.** After this ships, a captured URL is in `xlib/` until Bryan runs `bob ref scan`. Agents using `bob ref find` will see `in_intake` or `not_found` depending on timing. That is existing create semantics; the Mac notification has to say so.
- **Dedupe + journal.** If we archive on create success but forget the journal, a failed archive retries create and 4w.9 will *warn and capture a fresh copy* for legacy-only hits. Journal first, then archive.
- **Keep title noise.** Some share-to-Keep titles are "Notes" or the raw URL with tracking params. Pass `-T` only when the title is a non-URL string; let create derive the title from the page otherwise.
- **Two-repo rollout.** bob-cli can ship the kind first; an older Mac app will preview URL items as inbox tasks until the Swift side lands. Prefer one epic that lands both, Mac second, so the CLI kind exists for the app to decode.

---

## Suggested epic shape

Roughly one epic, two repos:

1. **create-lib** — crate-visible `create_pdf` / `CreateOutcome`; no behavior change for `bob ref create`.
2. **lone-url** — `lone_http_url` + `keep_library_url` + tests (Keep title/body table, `<>` wrap, private host, two URLs).
3. **capture-kind** — grammar, parse spans, dry-run, submit, `--as-task`, mixed-draft teaching error, CLI tests with fake clip/curl.
4. **mac-capture** — decode, preview card, submit timeout, notification. Linked repo `bob-mac-capture`.
5. **gkeep-ref** — `PlanAction::RefCreate`, list/dry-run copy, pull journal+archive, tests with `BOB_GKEEP_ADAPTER` + `BOB_WEB_CLIP_ADAPTER`.
6. **live-verify** — Mac paste of an article URL; `gkeep pull -d` then pull of a title+URL fixture; confirm `gkeep_inbox.md` unchanged and `xlib/` gained a PDF.

Phases 3 and 5 can overlap after 1–2. Phase 4 depends on 3's JSON.

---

## Recommended solution

Ship URL-to-library routing, but as a new capture *kind* and a new gkeep *plan action* that share one in-process `create` call.

1. **Predicate.** A capture item is a library URL when the whole item, after marker strip, is a single validated `http(s)` URL with no children and no destination/schedule/priority/clip flags. A Keep note is a library URL when it is a non-list, attachment-free note whose normalized content is that URL, or a non-URL title plus that URL as the only body. Everything else stays a task.
2. **Recognize vs fetch.** `capture-parse` is lexical. `capture --dry-run` validates and locally dedupes. Only real `bob capture` and `bob gkeep pull` fetch, clip, and stamp. Never `--listen`. Never `scan`.
3. **Capture drafts.** All-URL drafts (bulk allowed) run sequential creates. Mixed URL+task drafts fail closed. `--as-task` and any extra prose keep today's inbox task. Invalid URLs error.
4. **gkeep pull.** URL notes skip `gkeep_inbox.md`. On create success or a refusing library hit, journal `written` with the intake/library path, then archive. On create failure, leave the note in Keep. Inbox notes in the same pull keep the existing CAS path.
5. **Mac Capture.** Render `ref_create` from bob JSON; raise submit timeout from that mode; keep the 20s live-preview timeout. Do not parse URLs in Swift.
6. **Boundary with 4s/4w.** This feature does not extend `bob ref create`. It is a new *front door* onto the engine those epics shipped.

That is the smallest design that honors the request, the thin-client decision, capture's rollback contract, and gkeep's "archive only after the bytes are ours" rule.
