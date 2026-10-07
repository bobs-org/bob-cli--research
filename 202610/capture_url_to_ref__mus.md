# Routing URL-only input to `bob ref create`: capture, Mac Capture, and `gkeep pull`

Research report (mus). Question: how should bare-URL input to `bob capture`
(and the bob-mac-capture frontend) and URL-only Google Keep notes pulled by
`bob gkeep pull` be routed to `bob ref create` instead of becoming tasks?

## Summary of recommendation

Yes, do it, but route **per capture item**, implement detection **inside
`bob capture` (not in the Mac app)**, expose it through `capture-parse` for
previews, add a `--no-ref` escape hatch, and treat `gkeep pull` URL-notes as a
new plan action that archives only on success. Details in §6.

## 1. What exists today

### 1.1 `bob ref create TARGET` (post bob-cli-4w)

Single TARGET, classified syntactically first, network only for generic URLs
(`src/native/highlights_ref/target.rs`, `create.rs`):

- Local `.md` → pandoc render (default ref-type `chat`); local PDF → stamp
  as-is (default `papers`).
- `http(s)` URL → syntactic validate (`clip_url::validate_and_clean`: only
  http/https, no userinfo, **private hosts rejected**), arXiv check, dedupe
  against recorded `source_url`s **before any fetch**, legacy-only hits warn
  and re-capture, then fetch-and-route: PDF bytes → `papers`, HTML (2xx or
  bot-wall 403/429/503) → clip-engine article (`blogs`), anything else errors.
- Fetch uses curl with a **300-second timeout per URL** (`fetch.rs`:
  `fetch_url(url, dest, max_time_secs)` called with `300`).
- Dedupe is idempotent and safe to retry: a re-run of an already-captured
  URL reports "already captured" (or attaches `--listen`) instead of writing.
- Flags: `--dry-run`, `--force`, `--listen`, `--ref-type`, `--name`,
  `--title`, `--output`, `--status`, `--parent`. Notably, `create.rs` takes
  **no vault maintenance lock** (no `ob::` usage) — concurrent `capture` and
  `ref create` writes are uncoordinated.
- Config surface: `--bob-dir/--lib-dir/--ref-dir/--xlib-dir`; a caller must
  propagate `--bob-dir` at minimum.

### 1.2 `bob capture`

- `TEXT` is split into items on blank/whitespace-only lines; each item is
  **planned against in-memory snapshots before commit**, and any parse,
  clipboard, validation, staging, or replace failure **rolls the whole batch
  back** (`src/native/capture/mod.rs`, `batch.rs`, `cli.rs` long help).
- `CaptureRequest { raw_text, forced_route/section/task-flags, clip,
  no_clip, dry_run, bob_dir }` — there is no URL awareness anywhere in
  `capture_language` or `capture/`.
- Whole-item special forms already exist with JSON `kind` precedents:
  `pomodoro_link`, `task_complete`, `pomodoro_adjust`, `pomodoro_shift`.
  Multi-item JSON keeps the first result top-level plus an ordered
  `captures` array.
- A bare URL today is an ordinary task parent (`- [ ] #task https://…
  [created::DATE]` in `mac_inbox.md`). Nothing forbids or specially parses
  it.

### 1.3 Bob Mac Capture

Per `docs/capture.md`: the macOS menu-bar app "owns the hotkey and panel,
then delegates grammar, preview, completion, and vault writes to these `bob`
commands." Architecture decision
`decisions:mac-capture-is-a-thin-client` (always-loaded roster) says it never
parses grammar or writes the vault itself. So any routing rule implemented in
`bob capture` + `capture-parse` is inherited by the Mac app for free; putting
detection logic in the Mac app instead would violate that decision and fork
the contract across repos.

### 1.4 `bob gkeep pull`

Guarded drain transaction (`src/native/gkeep/pull.rs`): snapshot Keep →
`plan::classify` (archived → empty → pinned/shared → ledger/journal:
pending = archive-only, revised/new = write-then-archive) → render each note
as one task block appended to `gkeep_inbox.md` (configurable target) via
compare-and-swap + parse-verify → Git commit → **archive in Keep only when
the note's fingerprint matches a verified vault block** ("a duplicate is
always preferred over data loss").

Relevant model facts (`model.rs`, `render.rs`, `plan.rs`):

- `KeepNote { content: {title, text, items[]}, url: Option<String>,
  attachments[], labels[], … }`. Two distinct URL carriers: body text
  (title/text/items) and the `url` field (a link attached to the Keep note,
  currently rendered only as the `[Google Keep](…)` Source link).
- Title derivation: `title`, else first non-blank text line, else first list
  item. `is_empty` = no title/text/items/attachments (attachments always
  count, even without OCR).
- `pull --dry-run` previews exact Markdown; per-note verify already
  tolerates partial failure (`verified` vs `verify_failed`); JSON `list`
  already surfaces each note's `url` field.

## 2. Critique: is this a good idea?

Yes, with the adjustments below. The core argument is strong:

1. **Single home for URLs.** The ref library (with `source_url` dedupe,
   markers, and `ref find/list/show/doctor`) is now the canonical URL store.
   Capturing the same URL as both a ref note and an inbox task creates two
   divergent records and a triage burden.
2. **Retry safety comes free.** Dedupe-before-fetch means a half-finished
   batch can be re-run without duplicates — this is the load-bearing property
   that makes the atomicity compromises in §4 acceptable.
3. **Both entry points arePaste-heavy.** URL-only capture input and
   URL-only Keep notes (share-sheet / Keep-quick-capture habits) are almost
   always "file this link," not "make me a task."

But the plan as stated has five problems:

1. **"Only capture input" is ambiguous.** Read literally (whole draft must be
   one URL), it breaks the parenthetical ("bulk capture with URLs should be
   supported"). The only coherent reading is **per-item routing**: each
   URL-only item in a batch routes to `ref create`; mixed batches do both.
2. **Magic routing needs an escape hatch and offline behavior.** Today a bare
   URL is a fast, offline, predictable task. After this change it becomes a
   network call taking up to 300s per URL that fails without connectivity
   and rejects intranet hosts. There must be a `--no-ref` flag (capture) /
   `--no-ref` (pull) preserving the old behavior, and the failure mode must
   be a clear error naming `ref create`, never a silently-created task.
3. **Capture's all-or-nothing warranty cannot extend to ref creates.**
   `ref create` performs network I/O and installs PDFs/markers immediately;
   it cannot participate in the staged batch rollback. Order operations so a
   ref failure fails the batch *before* any vault write, and document the
   residual case (vault commit fails after refs were filed → orphan refs,
   recoverable via dedupe on retry).
4. **"Contains only a URL" needs a strict, shared definition.** Keep notes
   carry title, multi-line text, checklist items, attachments, and a link
   field; capture items carry markers, children, and clipboard tokens. A
   loose "looks link-ish" test will misfire on notes like a URL plus "read
   later". Define it as: after existing normalization, the entire payload is
   exactly one token that passes `validate_and_clean`.
5. **Don't split the contract across repos.** The Mac app must not implement
   its own URL detection. Ship detection + a `capture-parse` mode from
   bob-cli; the Mac app only renders the new JSON kind and optionally adds a
   "capture as task instead" toggle wired to `--no-ref`.

## 3. Proposed semantics

### 3.1 URL-only test (shared by capture and gkeep)

New small helper (owned by `highlights_ref`, e.g. `clip_url.rs` or
`target.rs`), used by both callers so the definition cannot drift:

- Trim; must be a single whitespace-free token; `looks_like_url` prefix
  check, then `validate_and_clean` must succeed (this folds in scheme,
  userinfo, and private-host rejection).
- Explicit non-goals for v1: markdown links `[t](url)`, `<url>` autolinks,
  trailing prose punctuation (`…paper.`, `…paper),`), multi-URL payloads,
  and title-plus-URL two-liners all stay tasks/notes. (Title-plus-URL is the
  obvious v2 — map to `ref create --title` — but it needs its own
  disambiguation design; don't smuggle it into v1.)

Per-item preconditions in `bob capture`: the item, after blank-line
splitting, must contain no `@route`/`@@`/`s:`/`p:`/`%`, no authored children,
no forced-destination flags, and no other text. Check URL-ness **before**
terminal-marker parsing so a URL can never be eaten by `s:`/`p:`-style
suffix rules. Non-`http(s)` single tokens (`obsidian://…`, `mailto:…`,
`file:…`) stay tasks.

For `gkeep pull`: a note is URL-only iff attachments are empty, all list
items are blank, at most one of title/text is non-blank after the
renderers' normalization (equivalently: title blank and text normalizes to
one line, or text blank and title is the token, or both equal the same
token), and that token passes the shared test. The `url` link-field alone
does **not** qualify — a described/linked note ("cool tool" + attached
link) is exactly the case where Keep-as-task-triage is wanted; only treat
`url` as a candidate when the body is otherwise empty (title/text/items all
blank), and even then validate it with the same test.

### 3.2 `bob capture` behavior

- During planning, classify each item; URL-only items get a new JSON kind
  (name: `ref_create`, following the `pomodoro_link`/`task_complete`
  precedent of kind + additive object: `{url, cleaned_url, dedupe_key,
  status}`).
- Execution order: run all `ref create`s **first** (in item order,
  in-process function call reusing the same `bob` binary's code — not a
  subprocess re-exec), then stage/commit the remaining vault batch. Any ref
  failure aborts before any vault write, preserving the all-or-nothing feel
  for the vault half; document that completed ref installs are not rolled
  back and that re-running is safe via dedupe.
- `ref create` options for this path: defaults (`blogs`/`papers` by route,
  `ready`, parent `obsidian_ref`), honoring capture's `--bob-dir` and
  `--dry-run` (thread dry-run into `CreateOptions`). No new per-URL flags in
  v1 except `--no-ref` (force legacy task capture). Consider
  `--ref-type/--no-…` only if the epic demands it.
- `capture-parse` gains a matching mode (e.g. `ref_create`) so editors and
  the Mac app can preview "will file as reference" **without fetching**
  (preview must be syntactic-only — never network).
- Human output: one line per URL item (`ref created <stem> ← <url>` /
  `already captured as …` on dedupe hits, mirroring `ref create`'s own
  messages).

### 3.3 `bob gkeep pull` behavior

- New `PlanAction::RefCreate` (sibling of `Write`/`ArchiveOnly`) assigned in
  `classify` for URL-only notes in New/Revised state; surfaced in
  `list`/dry-run output so users can see what will be filed as refs.
- URL-notes skip the `gkeep_inbox.md` write path entirely (no block, no
  marker, no ledger task entry). On successful `ref create`, record a
  journal event (e.g. `ref_created` with id/ref/fp/url) and **archive the
  Keep note through the existing guarded archive path** — same "provably
  filed before archive" warranty, just with the ref library as the
  proof-of-filing instead of a vault block.
- Failure policy differs from capture on purpose: one bad URL (offline,
  unsupported content-type, private host) must not block the whole inbox
  drain. Skip-with-warning per note, leave it in Keep, continue the batch
  (consistent with pull's existing per-note `verified`/`verify_failed`
  tolerance). Next pull retries it.
- Flags: `--no-ref` preserves today's write-everything behavior;
  `-i <ref>` selection and `--limit` treat URL-notes as actionable.
- Revised-state URL-notes (edited in Keep after a previous pull): if the
  previous filing was a normal task (ledger hit), current behavior stands;
  only New-state or journal-known notes take the ref path unless the design
  explicitly handles task→ref migration (recommend: out of scope for v1).

### 3.4 bob-mac-capture

No detection logic in the app. Contract change: handle the new
`ref_create` item kind in `capture`/`capture-parse` JSON (preview copy +
success copy), plus an optional per-draft "file links as tasks" toggle that
passes `--no-ref`. Coordinate across repos per the thin-client decision.

## 4. Risks and open questions

1. **Latency.** Worst case ~300s per URL, sequential. A 5-URL bulk capture
   can hang a menu-bar UI for 25 minutes. Mitigations: run refs first so
   failure is early; Mac app should stream per-item progress from JSON;
   consider a `--ref-timeout`/concurrency cap only if real usage shows pain
   (don't design the thread pool in v1).
2. **Offline/airplane mode.** `ref create` fails hard without network.
   The error must say how to keep the link (`--no-ref`), and the Mac app
   should offer one-tap "capture as task instead" on this error.
3. **Lock/race gap.** `ref create` takes no vault lock while `capture`
   stages vault files; a concurrent Obsidian edit + ref install could
   interleave. Same exposure as running the two commands by hand today —
   acceptable, but don't claim atomicity across the two halves.
4. **Dedupe vs. intent.** Dedupe-hit ("already captured") on a URL the user
   wanted as a *task reminder* will confuse. The `--no-ref` hatch and the
   preview mode are the answer; also print the existing ref identity on
   hits.
5. **Keep `url`-field semantics.** `note.url` may be set on notes whose body
   is commentary about the link; the §3.1 rule (body-empty required) guards
   this, but verify against real vault data — log how many inbox notes take
   each branch on first rollout (`--dry-run` census before enabling).
6. **Private-host and non-HTTP URLs** must fall back to tasks with a clear
   message, not an error that blocks a mixed batch. Decide: fallback-with-
   warning vs hard error — I recommend fallback-with-warning for *validation*
   rejections (private host, weird scheme) but hard error for *fetch*
   failures (user should know the ref didn't file), at least in capture.

## 5. Test and docs checklist

- Capture: single URL item; mixed URL+task batch ordering; URL item with
  markers stays a task (or errors per spec); `--no-ref`; `--dry-run`
  performs no fetch/install; dedupe-hit path; JSON `ref_create` shape;
  non-http single tokens unaffected.
- Gkeep: URL-only title/text/list/attachment matrix; `url`-field-only note;
  described-link note stays a task; ref failure leaves note in Keep and
  continues batch; journal `ref_created` entries; `--no-ref`; dry-run
  preview.
- Docs: `docs/capture.md` (new item kind + `--no-ref` + atomicity note),
  gkeep help/docs (new plan action + failure policy), Mac Capture contract
  note. `bob ref create` docs unchanged.

## 6. Recommended solution (concrete)

1. Add a small `is_url_only_input` helper (name TBD) in `highlights_ref` wrapping
   `looks_like_url` + `validate_and_clean`, returning the cleaned URL +
   dedupe key. Both callers use it.
2. `bob capture`: per-item URL classification in planning → new `ref_create`
   JSON kind + `capture-parse` mode → execute refs first via in-process
   `create` call with `--bob-dir`/`--dry-run` threaded through → then normal
   batch commit. Add `--no-ref`. No Mac-app logic changes beyond rendering
   the new kind and an optional toggle.
3. `bob gkeep pull`: `PlanAction::RefCreate` for URL-only New notes (body-
   empty `url`-field notes included); skip inbox write; ref-create then
   guarded archive; journal the filing; per-note skip-with-warning on
   failure; `--no-ref` opt-out.
4. Strict v1 scope: single-token payloads only; no title+URL mapping, no
   markdown-link unwrapping, no new timeout/concurrency machinery. Revisit
   after a `--dry-run` census of real URL capture/gkeep volume.

## Sources inspected

`src/native/highlights_ref/{create,target,clip_url,fetch,cli}.rs`,
`src/native/capture/{mod,cli,batch,output}.rs`, `docs/capture.md`,
`src/native/gkeep/{model,plan,render,pull,cli}.rs`. Deliberately did not
consult sibling swarm reports or the bob-mac-capture repo (per swarm
rules); Mac-app claims rest on `docs/capture.md` and the inlined
thin-client decision record.
