# Open Highlights PDFs vs `bob ref scan` marker writes

- **Date:** 2026-10-23
- **Researcher:** `grk` (swarm `research.56`)
- **Question:** When `bob ref scan` on the MacBook rewrites a PDF marker's `status:` while that PDF is open in Highlights, the next annotation hits a document conflict. Is the right fix to have scan save, close the Highlights tab, rewrite the marker, reopen the PDF, and notify? Is that a good idea, what should change, and what should we ship?
- **Verdict in one line:** The diagnosis is right and the close/reopen prescription is the wrong tool. Make marker writes a well-behaved macOS file replacement, and skip them for documents Highlights still has open. Do not drive Highlights' GUI from `bob ref scan`.

---

## 1. Bottom line

Do **not** teach `bob ref scan` to close and reopen Highlights tabs.

The conflict is a textbook `NSDocument` race: scan replaces PDF bytes under an open Highlights document with an uncoordinated temp-file rename. Highlights is an `NSDocument` app (`Highlights.Document`), is **not scriptable**, and keeps PDFs in memory with **zero** file descriptors. Closing a tab from scan would fight all of that with Accessibility keystrokes, steal focus every 15 minutes, drop the reading page, and quit Highlights if the bounced tab is the last one.

Ship this instead:

1. **Never fail a note write because the PDF is open.** Today's `needs_write_pdfs` refusal is the wrong shape for "catch up later."
2. **On macOS, write markers through `NSFileCoordinator`.** Highlights already presents the file. A coordinated replace asks it to save, then tells it the file changed. That is the save path the request wants, without ⌘S injection.
3. **If coordination cannot finish (save sheet, timeout), skip that PDF's marker write** and keep the note. Report it. Notify. The next scan after the tab closes finishes the marker.
4. **Put the UX in Bob Refs**, which already owns Highlights tabs, scan JSON, and the refs-scan notification category. Scan itself stays a vault writer.

Close/reopen stays a **manual** recovery ("Close the PDF in Highlights first," already on the rename card) and a last-ditch spike fallback, never the 15-minute cron.

---

## 2. What actually happens today

### 2.1 The writer

`bob ref scan -w` is the Mac's full annotation pass. Two callers always pass `-w`:

| Caller | Cadence | Why `-w` |
| --- | --- | --- |
| `~/bin/maybe_bob_highlights_sync -w` | cron `0,15,30,45 * * * *`, gated on `lib/` mtime-today or a nonempty `xlib/` | Without `-w`, any note whose lifecycle status moved is a per-PDF `needs_write_pdfs` failure, so annotation sync for that PDF dies with the marker |
| Bob Refs ⌘S | on demand, 300 s `refs-scan` lane | Same `bob ref scan -w -f json` the cron runs |

The cron wrapper lives in chezmoi as `home/bin/executable_maybe_bob_highlights_sync` and still shells `bob highlights scan "$@"` (permanent hidden alias of `bob ref scan`). It runs whenever **any** file under `lib/` changed today. Annotating the PDF you are reading, or linking a different reference, is enough to arm the next quarter-hour.

A typical conflict sequence:

1. The PDF is open in Highlights (often clean; AutoSave may already have flushed annotations).
2. Something moves the reading-task status: Bob Refs "Link to Today," an Obsidian checkbox, `bob ref today`. The note now reads `status_sync: pending`.
3. The next `-w` scan renders a new page-1 marker and, because `rendered_marker != marker.contents`, sets `marker_write_needed`.
4. `write_pdf_marker` loads the PDF with lopdf, sets the `/Text` annotation `Contents`, `save`s a sibling temp file, `fsync`s, and `rename`s over the live path (`src/native/highlights_ref/marker.rs`).
5. Highlights still holds the old in-memory document. The next annotation dirties it. Save produces the conflict sheet. Revert-and-reapply is the only way out.

The docs already name this race, without a product fix:

> Keep Highlights and Obsidian idle while testing PDF marker writes so the apps do not race the CLI.
>
> — `docs/highlights-ref-sync.md`

The rename card already tells Bryan to close the PDF first. The failure table already says `changed during sync; rerun` after closing apps that may touch the file. The writer knows the race; it just keeps writing.

### 2.2 Why status is the field that moves

Marker writes are opt-in and semantic. Scan rewrites the PDF only when frontmatter (or a generated `^ref` mark) contributed a lifecycle field **and** the rendered marker text differs. Sidecar → note annotation sync does **not** need `-w`. The bytes that change on disk are almost always `- status: …` catching up after a note-side lane change.

`status_sync: pending` is the explicit lag: `bob ref today` and Ctrl+Shift+Enter leave the tracker ahead of the PDF until the next `-w` scan. That is by design. It is also why a quiet reading session still gets a marker write 0–15 minutes later.

### 2.3 What Highlights is

Measured on this Mac in the 2026-10-15 Tabs swarm (`research:202610/highlights_tab_switcher/highlights_tab_switcher.md`) and still current on the vendor FAQ (fetched 2026-10-23):

| Fact | Evidence |
| --- | --- |
| Native AppKit `NSDocument` app | `Info.plist` `NSDocumentClass` = `Highlights.Document` |
| Not AppleScriptable | FAQ: "Is Highlights scriptable? No, not yet." No `NSAppleScriptEnabled`, no `.sdef`. `tell application "Highlights" to get documents` → −1728 |
| Open PDFs are **not** in `lsof` | 9 tabs open, 0 PDF fds. `libproc` cannot enumerate them |
| Front tab exposes a `file://` path; background tabs expose **filename only** | Window `AXDocument`; `AXTabGroup` → `AXRadioButton` titles |
| Re-opening an already-open PDF **selects that tab** and keeps the page | `open -a Highlights <path>` / `NSWorkspace.open(_:withApplicationAt:)` |
| AutoSave exists | Changelog 2023.1.1: "document would be unnecessary reloaded while running AutoSave" |
| Closing the last document **quits Highlights** | Bob Refs tab-close contract; macOS may then restore every window on relaunch (FAQ: "Why does Highlights restore my windows when I re-open the app?") |
| Annotations are standard embedded PDF annotations | FAQ: "Highlights uses standard embedded annotations"; sidecar Markdown/TextBundle is an export |

Bob Mac Capture already speaks this UI: `AXHighlightsTabsReader` reads, selects, and closes tabs; `WorkspaceRefsOpener` reopens; close verification treats a save sheet as `.needsAttention` and **raises the sheet for Bryan** instead of dismissing it. There is no save API. There is no "reload this document" API. ⌘S is a System Events keystroke, the same trick the 2021 MPU Talk "Highlights is entirely and frustratingly unscriptable" script used.

### 2.4 What Bob Refs already reports

The scan JSON envelope (`schema_version: 1`) already carries `notes[].marker` and `summary.markers`. Hidden-panel scan outcomes already post through `NotificationService.refsScanCategoryIdentifier`, and a click opens Bob Refs on Just scanned. The missing piece is not a notification channel. It is a writer that does not stomp an open document, and copy that names the deferral.

---

## 3. Critique of the proposed plan

The proposed plan: on marker write, save Highlights (⌘S), close that PDF's tab, write, reopen, notify.

**The problem is real. The mechanism is the wrong layer, the wrong permission, and the wrong cadence.**

### 3.1 Scan is the wrong process

`bob ref scan` is a vault writer. It runs on athena and apollo (`--intake-only`), from Terminal, from cron with no GUI session guarantees, and from Bob Refs. Highlights UI state is macOS session state. `decisions:mac-capture-is-a-thin-client` already draws that line: bob owns grammar and vault mutation; the app owns presentation and process orchestration. Driving Highlights from the CLI repeats the Hammerspoon-era mistake in a new costume.

Putting Accessibility on `~/.cargo/bin/bob` is worse than putting it on Bob Mac Capture. The CLI is ad-hoc signed; every `cargo install` changes its cdhash; TCC Accessibility grants on ad-hoc binaries silently die (the Tabs research's signing finding). Bob Mac Capture already paid that cost.

### 3.2 Close/reopen is a hostile default

The 15-minute cron is the common writer. Automatically yanking the frontmost reading tab, even for a second, is the opposite of "beautiful":

- **Focus.** Close of a background tab already "briefly switches Highlights to it, closing it with the window's close button, and switching back." Scan would do that to whatever Bryan is reading, from a job he did not invoke.
- **Page and scroll.** `open -a` preserves page only for a tab that is **already open**. After close, reopen is a new `NSDocument`. Page 1, or whatever Highlights last persisted. The Tabs north star was "opening never changes reading state."
- **Last tab.** Close of the last document quits Highlights. macOS window restore may then bring **every** previously open PDF back, or none. Either way scan has become an app launcher.
- **Dirty documents.** Bob Refs already refuses to fake this: a save sheet is `.needsAttention`, the panel hides, Bryan decides. Scan cannot sit on that sheet. Injecting ⌘S first is the same dialog with worse timing.
- **Filename matching.** Background tabs have no path. Close/reopen from scan would match `stem.pdf`, and `lib/` already has one basename collision (`harness_engineering.pdf`).

### 3.3 ⌘S is not a save API

There is no `save` AppleEvent. Options:

| Method | Why it is a poor scan primitive |
| --- | --- |
| System Events `keystroke "s" using command down` | Needs Automation permission on top of Accessibility; hits whichever app is frontmost; races typing; dings if nothing to save |
| AX `File > Save` menu press | Same permission, a little less wrong-window, still a GUI gesture, still a sheet if the document is in conflict already |
| Close and hope the save sheet is "Don't Save" | Drops unsaved annotations. Unthinkable |
| Close and hope AutoSave already flushed | Often true, never guaranteed, and the sheet still appears when it is not |

The save the request wants is the one `NSDocument` already implements for other writers: `savePresentedItemChangesWithCompletionHandler(_:)`, invoked when a writer uses `NSFileCoordinator`. That path needs no keystroke and no tab identity.

### 3.4 Atomic rename is part of the bug

`atomic_save_pdf` writes a sibling and `rename`s over the presented URL. For an `NSFilePresenter`, a replace-without-coordination looks like the file vanished and a new inode appeared. `NSDocument` then compares `fileModificationDate` on the next save or AutoSave and raises "This document's file has been changed by another application since you opened or saved it." That sentence is the user's conflict.

A coordinated `.forReplacing` write is the API Apple documents for this exact replace. Close/reopen papers over an uncoordinated write. Fix the write.

### 3.5 What would make close/reopen the right call

Only after a Mac spike shows that:

- `NSFileCoordinator` does not make Highlights save-and-reload a clean document, **and**
- File > Revert / `open -a` on the still-open tab does not pick up the new marker, **and**
- the bounce is restricted to an explicit ⌘S, never cron, never the last tab, and restores page.

Until that spike fails, close/reopen is a recovery runbook, not a feature.

---

## 4. Requirement adjustments (called out)

These change the request. Each is justified.

**A1. Scan does not drive Highlights.**
No AX, no System Events, no `osascript`, no tab close, no reopen inside `bob ref scan`. The CLI may coordinate a file write. The app may describe what happened. The CLI may not puppet the reader.

**A2. Background scans never bounce a tab.**
The 15-minute cron is unattended. Unattended GUI automation is how you lose a highlight you had not saved yet. Cron may skip a marker or coordinate a write. It may not close windows.

**A3. Skipping an open PDF's marker is success, not `needs_write_pdfs`.**
Today a status-pending PDF without `-w` fails that PDF's plan. That is why every Mac scan passes `-w`. The new contract: write the note; leave the marker; set `status_sync: pending`; report `marker_deferred`. Annotation sync continues. The next eligible `-w` pass finishes the PDF.

**A4. Save through the file presenter, not ⌘S.**
On macOS, wrap marker installation in `NSFileCoordinator.coordinate(writingItemAt:options:.forReplacing)`. Highlights' `NSDocument` is the presenter; it is supposed to flush, then observe the replace. Linux keeps today's uncoordinated rename (no presenter).

**A5. Notify only when an open PDF was involved.**
"No new references" stays quiet. A deferred or coordinated open-PDF write is the one case that is invisible in the library list and painful in Highlights, so it earns a notification (hidden panel) or a footer/HUD line (visible Refs). Click opens Bob Refs with that row selected, using the existing refs-scan category.

**A6. Preserve reading position as a hard constraint.**
Any recovery that cannot keep the current page is opt-in and explicit. Default paths (skip, coordinated write) leave the tab alone.

**A7. Last-tab and save-sheet are hard stops.**
If a future bounce fallback ever ships, it must refuse when `documentCount == 1` and must surface a save sheet to Bryan, matching tab-close. Scan must not click Don't Save.

**A8. Keep `-w` on the cron.**
Dropping `-w` without A3 turns every pending status into a per-PDF failure and skips that PDF's sidecar import. After A3, `-w` still means "write markers that are safe." It does not mean "write markers under the user's cursor."

---

## 5. Alternatives

| Option | What it does | Why it is not the recommendation |
| --- | --- | --- |
| **P0. Close / save / reopen from scan** (the request) | AX close ladder + ⌘S + `NSWorkspace` open | Wrong process, wrong cadence, loses page, quits on last tab. See §3 |
| **P1. Drop `-w` from cron** | Background scans become note-only | Immediate mitigation **after A3**. Without A3 it fails pending PDFs. Status in the page-1 note would lag until ⌘S. Acceptable as a hotfix, incomplete as the design |
| **P2. Skip marker writes while Highlights is running** (all PDFs) | One `pgrep` | Over-broad: closed PDFs would also wait. Easy, but A3 + per-PDF skip is the same code with better catch-up |
| **P3. Skip marker writes for PDFs AX says are open** | Mac Capture lists tabs, scan takes `--defer-pdf` | Works, needs AX and filename matching, still does not save. Use as the **deferral detector** when coordination times out, not as the primary write path |
| **P4. Coordinated marker write** (recommended primary) | `NSFileCoordinator` around `atomic_save_pdf` | Uses the API `NSDocument` already implements. No tab identity required. Needs a Mac spike to confirm Highlights reloads a clean document |
| **P5. `open -a` the same path after write, no close** | Force Highlights to notice the file | For an already-open tab this **selects** it and keeps the page; it may not reload memory. Cheap follow-up if P4 reloads only after a tab switch |
| **P6. Stop putting `status` in the PDF marker** | Note is sole source of truth | Large contract change. The marker is the dual-source projection (`highlights_marker_base` / hash). Do not reopen that to fix a file-coordination bug |
| **P7. Incremental PDF update instead of lopdf `save`** | Append xref so object IDs stay | Worth a later pass if Highlights' reload after P4 drops annotations or rewrites the sidecar. Not required to stop the conflict |
| **P8. Pre-scan hook that bounces tabs** | chezmoi script + osascript | Same faults as P0, plus a retired-hook era we just left. Do not bring GUI into `highlights.pre_scan_hook` |

---

## 6. Recommended solution

Three layers. Each one is useful alone. Together they are the product.

### Layer 0 — Contract: deferrable marker writes (bob-cli, all hosts)

Change the writer so a needed marker update is no longer a hard error when it cannot be applied.

- Planning already knows `marker_write_needed`.
- Execution grows a third marker action next to `updated` / `none`: **`deferred`**.
- JSON (additive under `schema_version: 1`, `decodeIfPresent` on the app side):

  ```json
  "marker": false,
  "marker_deferred": "open_in_highlights"
  ```

  or `"presenter_busy"`, `"coordinator_timeout"`. Omit the key when the marker was written or not needed.
- `status_sync` stays `pending` until a later pass actually writes the PDF. That matches `bob ref today` today.
- Human summary: `1 marker deferred` / `N markers deferred`, colored, next to the existing marker count.
- Tests: a status-pending PDF without `-w` currently fails; after this change a note-only scan **updates the note** and reports deferred. A `-w` scan still writes when the write is safe.

This layer is the hotfix. It is also what makes P1 (cron without stomping) safe.

### Layer 1 — macOS: coordinated replace (bob-cli, `cfg(target_os = "macos")`)

Wrap `atomic_save_pdf` (and only that; intake moves stay as they are) in `NSFileCoordinator` with `.forReplacing`.

Intended sequence, all inside the OS:

1. Coordinator tells presenters a writer is coming.
2. Highlights' `NSDocument` saves unsaved annotations (`savePresentedItemChanges`).
3. bob writes the temp PDF and replaces the presented URL.
4. Highlights receives `presentedItemDidChange` / the replace. A clean document reloads. The tab, page, and scroll stay.

Timeout (recommend 8 s, overridable) → do not hang the 300 s scan: mark that PDF `deferred: coordinator_timeout`, write the note, continue.

bob-cli already has a `[target.'cfg(target_os = "macos")'.dependencies]` block (`plist`, `rusqlite`). `objc2-foundation`'s `NSFileCoordinator` fits there. A tiny Swift helper is the fallback if the Rust bindings are uglier than the write.

Linux and dry-run are unchanged.

### Layer 2 — Bob Refs: the visible moment (bob-mac-capture)

Mac Capture already runs the scan, already decodes `notes[]`, already posts refs-scan notifications, already knows which Highlights tabs are open.

**Detection.** After a scan (and, cheaply, before a `-w` write if we add a dry-run preflight later), match `notes` with `marker_deferred` or `marker: true` against `HighlightsTabsSnapshot`. Filename match is enough: one collision in the library, and the current tab has a full path.

**Copy, quiet when nothing happened, honest when an open PDF was touched.**

| Situation | Refs visible | Refs hidden |
| --- | --- | --- |
| Marker deferred for 1 open PDF | Footer: `Left “Wave 3…” open in Highlights` | Notification title `Left 1 PDF open in Highlights`, body the title, action Show in Bob Refs |
| Marker deferred for N | Footer: `Left N PDFs open in Highlights` | Title `Left N PDFs open in Highlights`, body first title `· +N-1 more` |
| Coordinated write reloaded 1 open PDF (if Layer 1 is confirmed) | Glass HUD 2.2 s, same hold as tab-close: `Updated open PDF` / title | Notification `Updated 1 open PDF` |
| Save sheet / timeout | Banner: `Highlights needs you to save “title” before Bob can update its marker.` Scan Again | Same as banner, refs-scan category |
| Nothing open involved | Today's quiet "No new references" / "Added N" | Today's rules (notify only on creates or failures) |

Click / Show in Bob Refs selects the first deferred row. If Tabs is off, turn it on only when that row is an open tab; otherwise keep the current view and select the library row. Do not reset the query.

**VoiceOver:** `Scan left Wave 3 open in Highlights so your annotations stay safe.`

**Do not** add a new Settings switch for v1. The default is the safe one. A later "Update open PDFs on ⌘S" can opt into a bounce **after** the spike in §8.

**Cron.** Layer 2 still sees cron scans if we want: Mac Capture is running as a login item and could watch the scan lock, but that is extra. Simpler: bob's JSON is enough when ⌘S runs; for cron, a small `UNUserNotification` from a `bob notify`-style helper is optional. Prefer teaching `maybe_bob_highlights_sync` to pass `-f json` and, on deferred markers, call `osascript` **only** to post a notification via Bob Mac Capture, or use `bob pomodoro notify`'s macOS path if one already exists. Do not have the cron script talk to Highlights.

Until that wiring exists, Layer 0+1 already stop the conflict. The notification is how Bryan learns a status is waiting, not how we prevent data loss.

### What Bryan sees (the beautiful path)

He is on page 14 of a paper. Fifteen minutes later the cron runs because he linked the ref to Today. The PDF does not blink. He highlights a sentence. It saves. No sheet.

Later he closes the tab, or presses ⌘S in Bob Refs. The marker catches up. If Refs is on screen, the footer mentioned the wait in one calm clause. If not, a notification named the paper and offered to show it.

That is intuitive: the app that is open is left alone; Bob talks about it, not through it. It is reliable: the OS save path, a timeout, a skip, a retry. It is beautiful: no puppetry, no page jump, copy that sounds like Bob Refs already sounds.

---

## 7. Implementation sketch

Order is the point. Do not start with AX.

### Phase 0 — Mac spike (about 1 hour, fixture PDFs, not the live session)

On the Mac, with Highlights 2026.x, two copies of a throwaway annotated PDF:

1. **Clean document, uncoordinated rename** (today's writer). Confirm the conflict sheet on the next annotation. This is the control.
2. **Clean document, coordinated `.forReplacing` write** of a one-line `status:` change. Does Highlights reload? Does the highlight still exist? Does the page stay? Does a new annotation save without a sheet?
3. **Dirty document** (one unsaved highlight), same coordinated write. Does Highlights flush the highlight into the file before bob writes? Or a save sheet? Or a timeout?
4. **AutoSave dirty**: wait for AutoSave, then coordinated write.
5. **`open -a Highlights` the same path after an uncoordinated write**, tab still open. Reload or stale memory?
6. **Last-tab close + reopen** as a negative test: confirm quit + window restore. Do not ship this.

Write the answers into the implementation plan. If (2) works, Layer 1 is the feature and close/reopen is dead. If (2) fails and (5) works, Layer 1 + a post-write `NSWorkspace` open of still-open paths is enough. If both fail, **then** discuss an explicit ⌘S bounce for dirty documents only.

### Phase 1 — bob-cli contract (Layer 0)

- `marker_deferred` in the scan JSON note object; human `markers deferred` count.
- Note writes proceed when the marker cannot.
- `needs_write_pdfs` remains for **intake** cases that truly cannot file a new PDF without a marker (existing queued reason). It leaves everyday status catch-up.
- Docs: `docs/highlights-ref-sync.md` conflict / `--write-pdfs` sections; `docs/reference/mac-capture/refs.md` scan footer copy. `just docs-gen` for the new JSON field.
- CLI tests on Linux with synthetic markers. No Highlights required.

### Phase 2 — bob-cli macOS coordinator (Layer 1)

- `cfg(target_os = "macos")` around the install path in `atomic_save_pdf`.
- Bounded wait; map timeout to deferred.
- Agent hosts have no Highlights; compile-check on the Mac (`just typecheck` is N/A for Rust — `cargo test --target aarch64-apple-darwin` if the Mac is up, else document unverified).

### Phase 3 — Bob Refs presentation (Layer 2)

- Decode `marker_deferred` with `decodeIfPresent`.
- Footer, HUD, banner, notification, VoiceOver strings in `RefsScanPresentation` (pure, Linux-tested).
- Match deferred PDFs to Tabs snapshot when trusted; filename fallback.
- Reuse `refsScanCategoryIdentifier`. Do not invent a second category.
- Renders: one light and one dark for "left open" footer; one for the save-sheet banner.

### Phase 4 — only if Phase 0 demands it

Explicit ⌘S bounce, in Mac Capture, never in scan:

- Save via coordinator or AX File > Save on **that** tab.
- Close via the existing close ladder.
- Wait for scan JSON `marker: true`.
- Reopen via `WorkspaceRefsOpener`.
- Refuse last tab. Surface save sheets. Restore the previously front tab if we bounced a background one.

Ship this only with a Settings opt-in after using Layers 0–2.

---

## 8. Open questions the spike must answer

These are not blockers for Phase 1. They decide whether Phase 2 is sufficient.

1. Does Highlights' `NSDocument` actually save on `relinquishPresentedItemToWriter` / `savePresentedItemChanges`? NSDocument does in Apple's implementation; a custom override could no-op.
2. After a coordinated replace, does a clean document reload in place, or only on next tab select?
3. Does lopdf's full `Document::save` rewrite annotation object IDs so Highlights' in-memory highlights detach even after a clean reload? If yes, incremental update (P7) moves up.
4. Does the sidecar TextBundle get rewritten on Highlights' presenter-save, so scan's **next** pass sees the flushed annotation? If presenter-save is PDF-only, scan should still read the sidecar after the coordinated write in the same invocation.
5. Cron + login session: `NSFileCoordinator` from a cron-launched `bob` in the user's GUI session should see Highlights as a presenter. Confirm. A LaunchAgent vs cron difference would argue for routing marker writes through Bob Mac Capture instead of the CLI.

---

## 9. Why this over close/reopen

Close/reopen tries to make Highlights forget the file so bob can pretend it was never open. File coordination tells Highlights the truth and lets it participate. Deferral is what we already do for `status_sync: pending`; we are extending that honesty to "the reader still has this open."

The existing product already contains every piece except the well-behaved write:

- tab identity (`AXHighlightsTabsReader`)
- save-sheet humility (`.needsAttention`)
- reopen that keeps the page (`WorkspaceRefsOpener`)
- scan report (`notes[].marker`)
- notification category (`refs-scan`)
- the thin-client rule

The new work is a marker action, a macOS coordinator, and a few strings. That is a smaller, safer, and kinder change than teaching a vault writer to click a window's close button.

---

## 10. Sources

### In-tree

- `src/native/highlights_ref/marker.rs` — `write_pdf_marker`, `atomic_save_pdf` (temp + `fsync` + `rename`)
- `src/native/highlights_ref/sync.rs` — `marker_write_needed`, `needs_write_pdfs` refusal
- `src/native/highlights_ref/scan_json.rs` — `notes[].marker`, `summary.markers`
- `docs/highlights-ref-sync.md` — write-pdfs contract; "Keep Highlights idle"; scheduled scan
- `docs/vault-git-sync.md` — Mac crontab `maybe_bob_highlights_sync -w`; gate on `lib/` / `xlib/`
- `docs/ref.md` — `status_sync: pending` until next `ref scan -w`
- `docs/reference/mac-capture/refs.md` — ⌘S = `bob ref scan -w`; Tabs close / save-sheet / last-tab quit
- chezmoi `home/bin/executable_maybe_bob_highlights_sync` — mtime-today gate, `bob highlights scan "$@"`
- bob-mac-capture `Sources/RefsCore/RefsScan.swift` — scan JSON, quiet success, refs-scan notifications
- bob-mac-capture `Sources/BobMacCapture/Refs/AXHighlightsTabsReader.swift` — close ladder, sheet detection
- bob-mac-capture `Sources/BobMacCapture/Refs/RefsPanelModel.swift` — `WorkspaceRefsOpener`
- `decisions:mac-capture-is-a-thin-client`
- `decisions:references-are-ingested-at-birth` — annotation sync remains the Mac's full scan
- `decisions:reference-ids-follow-file-stems` — already notes "a PDF left open in Highlights could later write back its stale marker"

### Prior research (independent of this swarm)

- `research:202610/highlights_tab_switcher/highlights_tab_switcher.md` — Highlights unscriptable; `lsof` empty; AX tab tree; `open -a` coalesces and keeps page; last-tab quit; signing/TCC
- `research:202610/highlights_quick_open_refs_panel/highlights_quick_open_refs_panel.md` — opener, "opening never changes reading state"
- `research:202610/macos_bob_background_activity_notification.md` — ad-hoc `bob` vs TCC/BTM identity
- `plan:202610/bob_refs_scan_keymap.md` — ⌘S north star, quiet success, hidden-panel notification

### External

- [Highlights FAQ](https://highlightsapp.net/faq/) — "Is Highlights scriptable? No, not yet."; window restore; embedded annotations (fetched 2026-10-23)
- [Highlights Mac changelog](https://highlightsapp.net/changelog/mac/) — AutoSave reload bugfix (2023.1.1)
- Apple File Coordination guide — `NSDocument` as `NSFilePresenter`; `savePresentedItemChanges`; coordinated writers
- Apple forums / NSDocument — "This document's file has been changed by another application since you opened or saved it" on uncoordinated replace
- [MPU Talk, 2021](https://talk.macpowerusers.com/t/batch-process-annotations-from-pdfs-out-to-obsidian/24470) — System Events keystrokes because "Highlights is entirely and frustratingly unscriptable"

---

## About this report

Independent swarm report for `research.56.grk`. It does not read peer `__cdx` / `__cld` / `__mus` / `__gem` drafts. Mac facts about Highlights' AX tree and `lsof` are taken from the 2026-10-15 Tabs swarm, which probed the live Mac; this turn did not re-probe the Mac. The vendor FAQ and the current bob-cli / bob-mac-capture / chezmoi trees were read in this turn.
