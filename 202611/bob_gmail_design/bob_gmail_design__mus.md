# Gmail integration for bob-cli (`bob gmail`) — research and recommended design

Researcher: mus. Date: 2026-11-05. Account in scope: `bryanbugyi34@gmail.com`.
Question: add `bob gmail` integrating Google Mail into the Obsidian vault —
clip a `mail.google.com` link from capture into a beautiful note, rewrite the
capture link, compose/send from Obsidian, plus anything else objectively useful.

## TL;DR recommendation

Build `bob gmail` as a **gog-backed, capture-aware clip-and-compose command**,
not a Keep-style adapter and not a calendar-style sync:

- Transport: shell out to `gog` exactly like `bob gcal` does (isolated
  `--client bob-gmail`, `BOB_GMAIL_GOG` test hook, `login`/`doctor`/`logout`
  checklist). No new Python adapter is needed — Gmail has an official API and
  `gog gmail` already wraps `search`, `get`, `thread get`, attachments,
  `send`, `reply`, `drafts`, and mutating label ops.
- Clip path (the core feature): `bob gmail clip <mail.google.com URL>` (plus
  automatic capture detection) fetches one message via
  `gog gmail get <id> --sanitize-content`, writes one note under a new
  top-level `mail/` folder, and prints the wikilink replacement
  (`[[mail/…|Subject — Sender]]`). Capture replaces the bare Gmail URL with
  that wikilink instead of routing it through the public-URL `ref` job
  pipeline.
- Compose path: **draft-first, send-second**. An Obsidian note with
  `to/subject` frontmatter + body is previewed with
  `bob gmail send --dry-run --note <path>` and only sent with an explicit
  `--send` (or `bob gmail reply/forward`). Never auto-send from capture,
  hooks, or agents.
- Phase it: MVP = `clip` + `show/search` + draft-based `send/reply`. Defer
  inbox sync, auto-filing, and two-way label sync until the MVP proves the
  note format and auth story.

The plan as stated is a **good idea with three adjustments** (detailed in
§6): (1) clip privately, never through the public `ref create` browser
pipeline; (2) compose creates drafts by default and sends only on explicit
confirmation; (3) read and send use separately-granted scopes / opt-in
send enablement, not one broad grant.

## 1. What exists today (evidence)

- `bob gcal` talks to Google **only through `gog`** (`src/native/gcal/gog.rs`):
  common flags `--no-input --json --color never --readonly --client bob-gcal
  --account <email>`, isolated token bucket per `--client`, `login` reuses a
  stored Bob client or a `~/Downloads` Desktop-app client, `doctor` gates
  setup, `BOB_GCAL_GOG` replaces the binary in tests, docs in `docs/gcal.md`.
- `bob gkeep` exists because Keep has **no official API**: pinned
  `scripts/gkeep_adapter.py` (`gkeepapi==0.17.1`) speaks JSON-over-stdio with
  `ping/snapshot/archive/exchange` ops, content-guarded archive, vault-side
  import receipts, `login/doctor/status/pull` UX (`docs/gkeep.md`).
- Gmail needs **neither workaround**: `gog v0.44.0` (verified on PATH)
  exposes a full Gmail surface — `gmail search` (Gmail query syntax,
  `--max/--all/--fail-empty`), `gmail get <messageId> --format
  full|metadata|raw --sanitize-content`, `gmail thread get --full
  --sanitize-content`, `thread attachments`, `attachment … --out`,
  `send/reply/reply-all/forward/drafts`, plus `archive/mark-read/trash/modify`
  and `gmail url <threadId>`. Global safety flags `--readonly` and
  `--gmail-no-send` exist for agent-safe invocation.
- Capture today treats a **bare public URL** as a reference job under
  `mac_inbox` (`docs/reference/capture-syntax.md`, `docs/ref.md`,
  `bob ref create/scan/jobs`). That pipeline assumes a fetchable public page
  (browser load → PDF → `ref/` note + reading task). An authenticated Gmail
  URL must not enter it: the browser fetch would fail or leak session state,
  and a `ref/` reading task is the wrong shape for mail.
- The Obsidian vault (`~/bob`) already separates concerns: `ref/` (reading
  queue), daily notes with Pomodoros/Events, `xlib/` intake. Mail deserves its
  own top-level folder rather than overloading `ref/`.

## 2. The URL problem (smaller than it looks, but real)

The example link shape is:

`https://mail.google.com/mail/u/0/#inbox/FMfcgzQhWTsNRgxMhQNwhZDfgqwXpPsx`

Parsing rules for the design:

- The `/u/0/` segment is the **logged-in account index**, not identity —
  ignore it (multi-login users shift it). Identity comes from configured
  `gmail.account`, not the URL.
- The fragment after `#` is a **view + opaque id**: `#inbox/<id>`,
  `#all/<id>`, `#sent/<id>`, `#search/<query>/<id>`, `#thread/<id>`, etc.
  Only the trailing token matters; the label prefix (`inbox`, `all`, …) is
  cosmetic and must be accepted openly.
- The trailing token (`FMfcgz…` form) is the Gmail API message-or-thread id
  family. `gog` already owns both directions: `gmail get <messageId>` and
  `gmail thread get <threadId>`, plus `gmail url <threadId>` to print web
  URLs. So the robust resolution order is: try `messages.get`, fall back to
  `threads.get` + first (or all) messages, and on total failure emit a
  named error that keeps the original URL intact (never a dead wikilink).
- Edge cases to specify: short/legacy hex ids, `?compose=` URLs (not
  clippable — route to compose instead), `#settings/#label` URLs (refuse with
  a helpful message), multi-message threads (clip the **linked message** by
  default, offer `--thread` for the whole thread).

## 3. Proposed `bob gmail` surface (MVP + explicitly deferred)

MVP subcommands (mirroring `gcal`/`gkeep` verbs where they exist):

```bash
bob gmail clip <URL> [--thread] [-d|--dry-run] [-f|--format human|json] [-R|--no-commit] [-q|--quiet]
bob gmail show <id> [--full] [-f|--format human|json]     # read-only thread/message view
bob gmail search <query>... [--max N] [-f|--format table|json]
bob gmail send --note <path> [--send] [-d|--dry-run]      # draft-first compose
bob gmail reply <id> --note <path> [--send] [-d|--dry-run]
bob gmail forward <id> [--to ...] [--send] [-d|--dry-run]
bob gmail drafts [...]                                    # thin wrapper over gog drafts
bob gmail login [-a|--account EMAIL] [-c|--credentials FILE]
bob gmail logout [-a|--account EMAIL] [-y|--force]
bob gmail doctor [-f|--format human|json]
bob gmail status                                          # auth + last-clip/receipt counts
```

Conventions to copy verbatim: no-subcommand runs the read-only default
(`gcal` → `list`; here `bob gmail` → `status` or `search` helper, never a
write); `-d` previews exact bytes; JSON output is versioned for the Mac
capture client; `BOB_GMAIL_GOG` fakes the transport in tests; timeouts and
exit-2 setup errors match `gcal`.

Explicitly deferred (do not ship in MVP): continuous inbox sync onto daily
notes, automatic label/filing sync, watch/push, bulk backfill, trash/spam
management, open tracking. Each is discussed as a follow-up in §5.

## 4. Clip design (the heart of the feature)

### 4.1 Capture behavior

- Add a Gmail-URL recognizer to capture (host `mail.google.com`, path
  `/mail/...`): a bare Gmail URL **never enters the public ref-job queue**.
  Two behaviors are defensible; I recommend (a):
  - (a) **Inline clip at capture time** (recommended): capture calls the
    clip routine synchronously, files `mail/…md`, and writes the wikilink
    into the task text in one transaction. One step for the user, no
    background job to monitor, matches "replace the URL with a good label".
  - (b) Queued clip job like `ref jobs`: better for offline capture, but adds
    a second drain step and a pending-state UX for something users expect to
    "just work" while online. Revisit only if offline capture of mail proves
    common.
- Fallback when offline/unauthenticated: keep the original URL verbatim plus
  a `#gmail-pending`-style marker (or a queued job), never a broken wikilink.
- Label: `Subject — Sender` (sender display-name, not raw address) is right;
  truncate at a documented width (≈60 cols) with the full subject in the note
  title/frontmatter. Example rendered task line:
  `- [ ] Reply to [[mail/2026/2026-11-04-invoice-from-acme|Invoice #4821 — Acme Billing]]`.

### 4.2 Note format (beautiful + durable)

New top-level folder `mail/` (sibling of `ref/`, not inside it — mail is not
the reading queue). Path scheme:

`mail/<YYYY>/<YYYY-MM-DD>-<slug>[-<n>].md`

where `<slug>` derives from subject+sender (normalized like Pomodoro theme
slugs), `<n>` disambiguates collisions, and the Gmail `message-id` → path
receipt lives in `.bob/gmail/clips/` (mirroring `gkeep` import receipts) so
re-clipping the same URL is idempotent.

Suggested note body (Markdown that renders natively, no plugin required):

```markdown
---
gmail_message_id: 199f…
gmail_thread_id: 199f…
subject: Invoice #4821 is ready
from: Acme Billing <billing@acme.example>
to: [bryanbugyi34@gmail.com]
date: 2026-11-04T09:12:00-05:00
labels: [INBOX]
gmail_url: https://mail.google.com/mail/u/0/#inbox/199f…
---

> [!mail] Invoice #4821 is ready
> **From:** Acme Billing · **Date:** 2026-11-04 09:12 · [Open in Gmail](url)
> **To:** me · **Cc:** …

Body as sanitized Markdown (text part preferred; HTML stripped to
structure: paragraphs, lists, links with full URLs shown).

<details><summary>Rest of thread (2 more)</summary>…</details>

Attachments: [[attachments/…|invoice.pdf]] (downloaded on `--attachments`)
```

Decisions embedded here: **text-first body** (HTML email rarely survives
Markdown conversion beautifully; store structure, not pixels); attachments
opt-in (`--attachments`, filed under existing `attachments/` conventions);
thread context collapsed by default; the Gmail URL always retained for
"open in Gmail" escape hatch.

### 4.3 Reliability details

- Fetch with `gog gmail get --sanitize-content` (strips HTML, removes URLs,
  omits raw payloads) for the agent/CLI path; keep a `--full` escape hatch.
  Treat bodies as **untrusted input**: pass `--wrap-untrusted` through,
  never execute or follow instructions inside mail, scrub secrets from logs
  exactly like the Keep adapter's `scrub()`.
- Idempotency receipt before archive/mark-read: clip records the receipt
  **before** any Gmail-side mutation, and Gmail-side `mark-read`/`archive`
  after clip is **opt-in per invocation** (`--mark-read`, `--archive`), never
  default. Rationale: filing mail should not destroy inbox state by
  surprise; `gkeep`'s content-guarded archive is the model if auto-archive is
  ever added.
- Truncation policy: cap body bytes/lines per note with an explicit
  `<!-- truncated · open in Gmail -->` marker; cap thread expansion (first +
  target + last, collapse middle).

## 5. Compose design (send from Obsidian)

Recommended shape — a **mail-compose note**:

```markdown
---
to: [someone@example.com]
cc: []
bcc: []
subject: Re: Invoice #4821
in_reply_to: 199f…
---
Body in Markdown; bob converts to plain-text (and optional HTML) at send time.
```

- `bob gmail send --note <path>`: default prints the exact RFC822 preview
  and exits 0 without sending (dry-run by default); `--send` transmits via
  `gog gmail send/reply` and then appends a `sent:` stamp + Gmail URL to the
  note frontmatter/body. `reply`/`forward` resolve threading headers
  (`In-Reply-To`, `References`) through `gog gmail reply/forward` so threads
  stay intact — hand-rolling MIME is out of scope.
- Safety rails (non-negotiable): send requires a TTY or explicit `--send`
  (no `--no-input` sends from agents/hooks); `--dry-run` shows recipients,
  subject, and first N body lines; `doctor` reports whether the send scope is
  granted; `gog`'s `--gmail-no-send` stays available as the agent-safety lock.
  Log sends to an append-only journal (date, message-id, recipients) for
  auditability.
- Nice follow-on (post-MVP): "send from capture" (`%mail to:…` directive) and
  a Mac-capture compose sheet that delegates to `bob gmail send --note`,
  keeping with the thin-client decision (`mac-capture-is-a-thin-client`).

## 6. Critique of the request + adjustments

**Is it a good idea?** Yes, with boundaries. Email is where actionable
commitments hide; filing the few that matter as first-class vault notes with
backlinks beats forwarding-to-self or leaving Gmail URLs to rot. The risk is
turning the vault into a second inbox: unbounded sync duplicates Gmail,
bloats Git, and leaks private data into synced notes. The design above avoids
that by making clip **per-link and deliberate** rather than bulk-synced.

**Adjustments I would make (all reflected in the recommendation):**

1. Do not route Gmail URLs through `bob ref create` / public capture jobs.
   Authenticated fetch is a different trust domain; give it its own folder,
   receipt store, and error taxonomy.
2. Do not auto-send. The request's "write and send new emails directly from
   Obsidian" should land as drafts-first. One accidental send costs more than
   ten extra `--send` confirmations.
3. Do not request one maximal OAuth grant. Use `gmail.readonly` for
   clip/search/show and request `gmail.send` (or `gmail.compose`) only when
   the user runs `login --send-scope` / first `send`. `doctor` must show the
   two grants independently. This mirrors the isolated `--client bob-gmail`
   bucket: removing the send grant must never break clipping.
4. Prefer `Subject — Sender` labels but keep the Gmail URL in frontmatter and
   mark the wikilink target stable (path receipt, not re-slug on re-clip).
5. Defer inbox→daily-note sync. `gcal` sync works because calendar days map
   cleanly onto daily notes; inbox has no such natural mapping, and a daily
   digest would need deduplication, read-state, and volume controls that
   dwarf the clip feature. Ship clip first, then evaluate a narrow
   opt-in digest (e.g. `bob gmail digest --query 'is:unread newer_than:1d'
   --max 10`).

## 7. Other objectively useful features (ranked)

1. `search` + `show` from the vault/CLI (find that invoice without opening
   Gmail) — nearly free once transport exists.
2. Attachment filing into `attachments/` with vault links — small, high
   value for receipts/invoices.
3. Opt-in `--mark-read` / `--archive` on clip — closes the triage loop.
4. Thread-aware follow-ups: clip offers "link this mail under today's
   Pomodoro" (`ref today` analogue: `bob gmail today <id>`), connecting mail
   to planning without copying tasks by hand.
5. Narrow digest for morning review (`is:unread` + label filter, capped,
   dry-run first) — only after MVP.
6. `drafts` management (list/send/discard) — composes with the draft-first
   flow; thin wrapper, low risk.

## 8. Auth, config, security

```yaml
gmail:
  account: bryanbugyi34@gmail.com
  client: bob-gmail          # isolated gog token bucket; never bob-gcal's
  timeout_secs: 60
  mail_dir: mail             # override only in tests
  clip_mark_read: false
  clip_archive: false
```

- `login` walks the same Cloud Console Desktop-app flow as `gcal login`
  (documented in `guides/connect-google-calendar.md`); request readonly
  scopes first, send scope only on demand.
- Secrets live in gog's store/keyring, never in config or logs; add a
  `gmail:` redaction pass to any debug dump.
- Tests mirror `gcal`: `BOB_GMAIL_GOG` fake executable, golden JSON for
  `clip --dry-run`, no live Gmail in CI; macOS-only targets gated the same
  way as other capture-contract changes.

## 9. Test / rollout sketch

1. `bob gmail login` → `doctor` all-ok (mirrors gcal checklist).
2. `clip <URL> -d` golden test on canned `gmail get` JSON (no network).
3. Live clip of 2–3 real messages (plain-text, HTML-heavy, threaded) and
   visual check of rendered notes in Obsidian.
4. `send --note` dry-run → real send to self → reply/forward round-trip.
5. Capture end-to-end: paste Gmail URL in a draft, confirm wikilink
   replacement and idempotent re-clip.
6. Docs: `docs/gmail.md` + `docs/guides/drain-gmail.md` (mirroring
   `drain-google-keep.md`), CLI help text, and a decisions record if any
   rejected alternative from §6 is revisited.

## Sources consulted (this session)

- `src/runner.rs` (`gcal`/`gkeep` subcommand wiring), `src/native/gcal/gog.rs`
  (gog transport, isolated `--client`, `BOB_GCAL_GOG` hook),
  `scripts/gkeep_adapter.py` (adapter protocol v1, secret scrubbing),
  `docs/gcal.md`, `docs/gkeep.md`, `docs/reference/capture-syntax.md`,
  `docs/ref.md` — all in the local checkout.
- `gog v0.44.0 --help` surfaces for `gmail search/get/thread/send/drafts`
  (help text only; no message content fetched for this report beyond one
  auth-status lookup via the `sase_gmail` read-only procedure).
