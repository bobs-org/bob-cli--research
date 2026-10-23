# `bob ref scan` vs. open Highlights PDFs: conflict analysis and recommended design

Researcher: mus (independent swarm report, `__mus`).
Date: 2026-10-23.
Question: when `bob ref scan` runs on the MacBook it sometimes rewrites the
`status:` field of a ref PDF's page-1 marker; if that PDF is open in Highlights
and the user then annotates, Highlights reports a conflict and the user must
revert and re-apply annotations. Proposed fix: have scan auto-save (Cmd+S),
auto-close the Highlights tab, rewrite, re-open, and post a mac notification.
Is this a good idea, and if so how should it be built?

## TL;DR recommendation

Do **not** implement auto-close/re-open as the default scan behavior.
Implement instead **detect-open-and-defer**: scheduled/bulk `bob ref scan`
never rewrites a PDF that Highlights currently has open; it defers that PDF's
marker write, syncs everything else, reports the deferred set (human + JSON),
and posts **one** macOS notification. Marker write-back for a deferred PDF
happens later via an explicit, single-PDF `bob ref sync --write-pdf` run when
the PDF is closed (or via an explicit opt-in force flag for users who accept
the risk).

Concretely:

1. Keep bulk `scan` note-only by default (already the default: marker writes
   require `--write-pdfs`). Document that scheduled scans should stay
   note-only / dry-run — this matches the existing contract in
   `docs/highlights-ref-sync.md` ("Scheduled `scan` should stay dry-run or
   note-only unless bulk PDF marker writes are intentionally wanted").
2. Add open-PDF detection on macOS and a **defer, don't close** policy:
   any PDF needing `marker_write_needed` that is open in Highlights is
   skipped for the PDF write (note write proceeds as today), listed in the
   report, and surfaced once via Notification Center.
3. Add an explicit per-PDF path (`bob ref sync --write-pdf`, possibly with a
   `--close-highlights` opt-in later) for the deferred write, with
   pre-flight "Highlights still has this open" guidance instead of silent
   force-close.
4. Do not ship Cmd+S-via-keystroke as the save strategy. It is the least
   reliable part of the proposal (focus theft, Accessibility permission,
   wrong-window risk). Prefer "don't touch unsaved work at all."

The rest of this report explains the mechanism, why the as-proposed design is
risky, the alternatives considered, and the exact behavior/UX contract I would
build.

## What actually happens today (verified in this repo)

- The PDF marker is the first standalone `/Text` annotation on page 1
  (`src/native/highlights_ref/marker.rs:read_pdf_marker`). Its `Contents`
  is the `- key: value` projection (`parse_marker`), and `status` is one of
  the validated values (`validate_status_value`).
- During planning, scan resolves marker vs. note-frontmatter projections and
  renders the canonical marker (`src/native/highlights_ref/sync.rs:323-361`).
  A marker rewrite is planned only when frontmatter contributed to the
  resolution or a deprecated-status normalization applied **and** the
  rendered bytes differ:
  `marker_write_needed = (decision.frontmatter_contributed ||
  status_normalization.marker.is_some()) && rendered != current`.
- Execution rewrites the whole PDF file: `write_pdf_marker` loads with lopdf,
  sets `Contents`, and `atomic_save_pdf` writes a temp file + `fsync` +
  `rename` (`src/native/highlights_ref/marker.rs:152-215`). Post-write it
  re-hashes the PDF for `source_pdf_sha256 bookkeeping
  (`src/native/highlights_ref/sync.rs:1312-1321`, `1656+`).
- The write is opt-in: without `--write-pdf` / `--write-pdfs` (or dry run),
  a needed marker write is a hard `needs_write_pdfs` error, not a silent
  write (`src/native/highlights_ref/sync.rs:362-367`). Human and JSON reports
  distinguish `marker_action: none|updated|would-update`
  (`sync.rs:18-26`, `1366-1370`; `scan_json.rs`).
- There is a same-run guard against the PDF changing under bob
  (`ensure_pdf_unchanged_for_write`: re-hash at execute time, fail with
  "PDF changed during sync; rerun", `sync.rs:2009-2019`). But there is
  **no** guard against the reverse direction: bob changing the PDF under a
  running Highlights instance. That is this issue.
- Project memory already knows this hazard. `decisions:references-are-ingested-at-birth`
  keeps annotation sync on the Mac, and `decisions:reference-ids-follow-file-stems`
  records as an explicit cost: "A PDF left open in Highlights could later
  write back its stale marker" (also: an id change rewrites PDF bytes and
  breaks `bob ref find <old id>`). So any design that rewrites PDF bytes
  must treat "open in Highlights" as a first-class state.

Net: the `status:` rewrite path is real but narrow (frontmatter-driven or
deprecated-status normalization, bytes-differ), bulk-gated behind `-w`, and
already atomic on the filesystem. The conflict is not a torn write — it is a
**stale-holder write-back**: two writers (bob, Highlights) with no shared
lock, and Highlights holding pre-scan bytes.

## Conflict model (two losing directions)

Either order loses something:

1. **bob writes, then Highlights saves.** Highlights held pre-scan bytes
   (including the old marker). Its save either fails/conflicts (what Bryan
   sees) or succeeds and silently reverts bob's marker update. Next scan
   re-applies the marker write, so this can recur as a loop.
2. **Highlights saves (annotation), then bob writes.** bob planned from
   pre-annotation bytes; `ensure_pdf_unchanged_for_write` catches changes
   made *between plan and execute within the same run*, but an annotation
   saved after planning and before a later scan's planning is simply
   overwritten at the marker annotation only — annotations themselves live
   elsewhere in the PDF, so lopdf's full-file rewrite is the real danger
   (object IDs can renumber; Highlights' in-memory model no longer matches
   the file). The user-visible symptom is the same conflict dialog.

Key point for design: **no ordering of "save then close then write then
reopen" is safe unless every step is verified**, because each step can fail
halfway (save fails, close targets the wrong tab, reopen loses place).
A bulk cron scan cannot do this safely for N PDFs while the user is reading.

## Critique of the proposal as stated

### Auto-close + re-open the Highlights tab

- **Tab identity is the hard part.** I found no in-repo integration with
  Highlights' windowing (no AppleScript dictionary usage, no bundle-ID
  reference, no tab enumeration in `src/`; Highlights appears only as file
  formats, `highlights://` links, and library directories). Mapping
  `/Users/bryan/bob/lib/papers/foo.pdf` → "that Highlights tab" therefore
  requires GUI scripting or private state, both brittle. This needs
  verification on the Mac (`osascript -e 'id of app "Highlights"'`,
  Accessibility dictionary listing, `lsof`); do not assume a bundle ID or
  scriptability in the implementation plan.
- **Bulk + interactive don't mix.** A scheduled `scan` touching N open PDFs
  would close N reading tabs out from under the user, possibly while they
  are reading. That is hostile even when technically correct, and it
  violates the "scheduled scan stays note-only" guidance already in the
  docs.
- **Reopen loses context.** `open <pdf>` restores the file, not the scroll
  position, selected text, in-progress highlight drag, search state, or
  sidebar state. "Close and reopen" is not a no-op for a reading app.
- **Failure modes strand the user.** If close succeeds but the marker write
  fails (or the scan run is killed), the user's reading session is gone
  with nothing to show. Every close must be paired with verified reopen,
  which doubles the fragile surface.

### Cmd+S to "save unsaved annotations first"

This is the weakest link and I recommend cutting it:

- Sending Cmd+S means activating Highlights (stealing focus), targeting the
  right window/tab, and synthesizing a keystroke via System Events. That
  requires Accessibility permission, breaks under lock/screen-share-focus
  edge cases, misfires on non-US layouts, and can save the *wrong* tab.
- Worse, it saves **through** the conflict: if Highlights' in-memory model
  already disagrees with bob's planned bytes, Cmd+S may be exactly the
  write that produces the conflict dialog the feature was meant to avoid.
- The safe alternative is cheaper: if the PDF is open, **don't write it at
  all**. Unsaved work is then never at risk from bob, by construction.

### macOS notification

This part of the proposal is right, with scoping:

- Notify only when bob actually deferred or performed a Highlights-affecting
  action — never on clean scans — or notifications become wallpaper.
- One summary banner per run ("Ref scan: 12 notes synced, 2 PDFs deferred —
  close them in Highlights and rerun"), not one per PDF.
- Implementation precedent exists: `scripts/install_all` already uses
  `osascript display notification ... with title ... subtitle ... sound name`
  (lines ~142-150). A Rust implementation should shell out to `osascript`
  only on macOS, only when the event occurred, and respect `--format json`
  (notification to the user + machine-readable report to stdout are
  complementary, not substitutes).

## Alternatives considered

| Alternative | Verdict |
|---|---|
| Status quo: note-only scheduled scans, explicit `-w` runs | Good baseline; enshrine it. Scheduled scans should never pass `-w`. |
| Defer-open-PDFs (recommended) | Best default: safe, simple, no focus theft, no permission prompts. |
| Force-close opt-in flag (e.g. single-PDF `--close-highlights`) | Acceptable as explicit opt-in later; never the bulk default. |
| Pre-scan hook that quits Highlights entirely | Too coarse; kills the whole reading session to update one marker. |
| Move `status` out of the PDF marker | Attractive long-term (marker becomes cache; frontmatter/sidecar is truth) but contradicts the current two-way sync contract and the id-follows-stem decision; a migration, not a fix. Out of scope here. |
| File coordination / `lsof`-only warning | Detection via `lsof` (or AppleScript `is running` + open-file check) is the right *sensor*; the *actuator* should be deferral, not force-close. |
| Cmd+S-then-close (as proposed) | Reject as default: fragile, permission-gated, focus-stealing, can cause the conflict it prevents. |

## Recommended solution

### Behavior contract

1. **Scheduled/bulk scans stay note-only.** No `-w` on timers/cron. This
   alone stops the reported conflict for the common case, because without
   `-w` a needed marker write is a refusal, not a rewrite.
2. **When `-w` is passed and a PDF needing a marker write is open in
   Highlights: defer it.** Semantics per PDF:
   - Reference-note write proceeds exactly as today (notes are not the
     conflict source).
   - PDF marker write is skipped for this run; the per-PDF report marks
     `marker_action: deferred-open-in-highlights` (human) and a stable slug
     (JSON, e.g. `deferred_open_pdf`) alongside the existing
     `needs_write_pdfs` family.
   - Exit status: success with a deferred count (not a hard failure), so a
     timer run doesn't page the user while still surfacing the backlog.
3. **Single notification per run, only when deferred (or when a deferred
   write later completes).** Title `bob ref scan`, body with counts and the
   exact rerun hint (`bob ref sync <pdf> --write-pdf` after closing in
   Highlights). No sound by default; sound only for the explicit opt-in
   close path if ever built.
4. **Explicit single-PDF path for the deferred write.** `bob ref sync <pdf>
   --write-pdf` already exists; add a pre-flight check: if Highlights has
   the PDF open, print "close it in Highlights and rerun" (with `--dry-run`
   preview unchanged). This keeps the forceful action user-initiated,
   single-file, and confirmable — the only context where close/reopen is
   arguably acceptable.
5. **No Cmd+S automation.** Document why: "bob never synthesizes saves into
   Highlights; close the tab yourself so no annotation is at risk."

### Detection (needs Mac verification — do not hardcode)

- Candidate sensors, in preference order: (a) AppleScript query against
  Highlights *if* it exposes open documents (verify dictionary first);
  (b) `lsof` open-file check for the specific PDF path (no app cooperation
  needed, but maps "open file" not "open tab" — sufficient for deferral);
  (c) process-running check (`application id ... is running`, cf.
  `scripts/install_all:616`) as a fast pre-filter only.
- Verify on the MacBook before building: bundle ID (`osascript -e 'id of app
  "Highlights"'`), whether `lsof` sees Highlights-held PDFs, whether
  Highlights has any AppleScript dictionary at all, and what its conflict
  dialog actually says (screenshot the exact text for the notification
  wording). Record the answers in the implementation plan; the bulk design
  above does not depend on them, but any future force-close flag would.

### Output and flag shape (follows `cli_rules.md` / `docs.md`)

- No new bulk flag is strictly needed for deferral (it becomes the policy
  for `-w` runs). If a flag is wanted for discoverability, prefer an
  explicit, alphabetically-placed, short-aliased opt-in such as
  `--defer-open` (default on) — and never a silent force-close default.
- Any future force-close capability must be a separate, loudly-named opt-in
  (single-PDF only), documented in `docs/highlights-ref-sync.md` +
  `just docs-gen`, with dry-run preview of which tabs would be touched.
- JSON: add the deferred slug to the scan envelope's per-PDF status family
  so Mac Capture / timers can render "2 PDFs need Highlights closed"
  beautifully instead of parsing human text.

### Beauty and intuitiveness notes

- The user never learns a new workflow: scans keep working; occasionally a
  single banner says what happened and the one command that finishes it.
- The deferred list should print vault-relative PDF paths (matching existing
  scan report style) plus the exact rerun command — copy-pasteable.
- Never notify on success-without-deferral. The feature is invisible when
  there is nothing to know, which is the beautiful case.

## Verification plan (on the MacBook, before implementation)

1. Reproduce: open a ref PDF in Highlights, run `bob ref scan --dry-run
   --write-pdfs` (read-only preview of `would-update`), then a real
   `-w` run on a scratch copy; capture the exact Highlights conflict text.
2. Sensor check: `lsof` visibility of the open PDF; `osascript` app-id and
   dictionary probe; Accessibility-permission requirements for any keystroke
   approach (expected: required — another reason to reject Cmd+S).
3. Post-change matrix: scan with PDF closed (marker updates, no
   notification), scan with PDF open (deferred + one banner + JSON slug),
   rerun after closing (marker updates, "completed" line), Highlights
   annotation round-trip after each step (no conflict dialog, no reverted
   annotations).

## Open questions for Bryan (not blockers for the recommendation)

- Should the deferred write auto-retry on the next scheduled `-w` run, or
  only on explicit `sync --write-pdf`? I lean explicit-first (predictable),
  auto-retry as a later timer option.
- Is a per-PDF force-close opt-in ever wanted (single-PDF, user-invoked),
  or is "close it yourself" permanently sufficient? I would not build it
  until deferral proves annoying in practice.

## Sources consulted

- `src/native/highlights_ref/marker.rs` (marker read/write, atomic save),
  `src/native/highlights_ref/sync.rs` (planning `marker_write_needed`,
  `execute_pdf_sync_v1/v2`, `ensure_pdf_unchanged_for_write`),
  `src/native/highlights_ref/cli.rs` (`--write-pdf(s)` opt-ins),
  `src/native/highlights_ref/model.rs` (`SyncOptions`),
  `docs/highlights-ref-sync.md` (write-back contract, MacBook validation
  notes, scheduled-scan guidance), `scripts/install_all` (osascript
  notification precedent), project memory
  `decisions:references-are-ingested-at-birth`,
  `decisions:reference-ids-follow-file-stems` (stale-marker cost),
  `cli_rules.md` + `docs.md` (flag/docs conventions).
- Web search for Highlights AppleScript/bundle-ID specifics returned no
  authoritative result; all app-integration claims above are therefore
  marked unconfirmed and gated on Mac-side probes.
