# `bob ref scan` vs. PDFs open in Highlights: ending the save conflicts

- **Date:** 2026-10-23
- **Researcher:** cld (one of five independent researchers; lead synthesizes)
- **Question:** On the Mac, `bob ref scan` sometimes rewrites the `status:` line of a PDF's page‑1
  marker. If that PDF is open in Highlights, the next annotation save hits a conflict. Should
  `bob ref scan` save Highlights' unsaved annotations, close the tab, write, reopen the tab, and send
  a Mac notification? What is the best way to build it, is it a good idea, and what would I change?

---

## 1. Bottom line

1. **Root cause: two processes write the same PDF and never tell each other.**
   - bob replaces the PDF with a temp file plus `rename(2)`.
   - Highlights is an AppKit `NSDocument` app. AppKit ignores that kind of uncoordinated replace, so
     the open document stays stale.
   - The next save then fails with *"The document could not be saved. The file has been changed by
     another application"*, offering **Save Anyway / Revert / Save As…**. I reproduced exactly this
     dialog on your Mac (§2.4, case D).
2. **It is systematic, not bad luck.** In the last 30 days the vault saw **68 single‑PDF marker
   write‑backs**. Nearly all are lifecycle changes that happen *while you read*: `next→wip` (17),
   `…→read` (24), `ready→next` (8). The scan writes the PDF right when it is most likely open.
3. **Your plan has the right goals and the wrong mechanism.**
   - The goals are right: save Highlights' work first, refresh the document, and tell you.
   - The mechanism is wrong: UI‑scripting ⌘S, close and reopen from a cron‑launched CLI.
     - It needs an Accessibility grant that `cargo install` silently invalidates on every release.
     - It steals focus and can race your typing.
     - It cannot target background tabs reliably.
     - It reorders tabs and loses your place.
4. **macOS already has a protocol for this, and Highlights already speaks it.**
   - The protocol is `NSFileCoordinator` / `NSFilePresenter`, and every `NSDocument` takes part
     automatically.
   - I tested it on the Mac with a stand‑in `NSDocument` (§2.4, case G).
     - A **coordinated read** made the open document **save its unsaved edits to disk**.
     - A **coordinated write** then made it **reload in place**. It ended clean, with no dialog and
       nothing lost.
   - That is your "⌘S, close, reopen", done by the OS and limited to the one document.
   - It works for background tabs, needs **no Accessibility, no keystrokes and no focus change**, and
     runs fine from cron.
   - Highlights does not override any of the AppKit methods involved. Its save override calls
     `super` and passes autosaves through. It even uses `NSFileCoordinator` for its own sidecar
     writes.
5. **Recommendation (§11), in four steps:**
   1. Run a 30–45 minute acceptance test with a scratch PDF in real Highlights.
   2. Make bob's macOS PDF writes **coordinated read‑then‑write**. Check the marker itself inside the
      coordinated block, bound the wait with a timeout, and **hold** writes while you are actively in
      Highlights.
   3. Tell you through **Bob Mac Capture**: a quiet notification, only when the PDF was actually
      open.
   4. Keep your close‑and‑reopen choreography only as **Plan B**. If Highlights fails the test, run it
      from Bob Mac Capture on an explicit click.

---

## 2. Evidence

### 2.1 What bob does today (code, this repo at `5eed7df9`)

| # | Fact | Where |
| --- | --- | --- |
| B1 | The marker is the first standalone `/Text` annotation on page 1. Its `/Contents` holds `- key: value` lines, including `status` | `src/native/highlights_ref/marker.rs` (`read_pdf_marker`) |
| B2 | `write_pdf_marker` loads the whole PDF with lopdf, sets `/Contents`, and calls `atomic_save_pdf`. That function re‑serialises the **entire** PDF to a temp file next to it, fsyncs, `rename(2)`s it over the original, and fsyncs the directory. **No file coordination** exists anywhere in bob‑cli | `marker.rs:152–214` |
| B3 | A marker write is needed when vault‑side fields change the synced projection, usually `status` from the `^ref` reading task. v2 also refreshes the `parent` hint under `--write-pdfs` | `sync.rs:357` (v1), `sync.rs:660–700` (v2) |
| B4 | The marker write runs *before* the note write. A failure aborts that PDF and the next scan retries it | `sync.rs:1285–1330` |
| B5 | The write guard compares a **whole‑file SHA‑256** against the value from planning | `ensure_pdf_unchanged_for_write`, `sync.rs:2009` |
| B6 | Writing scans run from three places on the Mac. **(a)** Live crontab: `*/15 * * * * ~/bin/maybe_bob_highlights_sync -w`. **(b)** Bob Mac Capture's Refs scan: `bob ref scan -w -f json` (`RefsFetching.swift:90`). **(c)** By hand | `ssh mac crontab -l` (2026‑10‑23) |
| B7 | The cron wrapper throws away scan output on success. `/var/tmp/maybe_bob_highlights_sync.log` is **empty**, so there is no record of marker writes | `~/bin/maybe_bob_highlights_sync` on the Mac |
| B8 | The project already knows this hazard. A decision record lists as a cost: *"A PDF left open in Highlights could later write back its stale marker."* The Refs rename card says *"Close the PDF in Highlights first."* | `docs/develop/decisions.md:710`; `RefsRename.swift:406` (Mac Capture) |

### 2.2 How often, and when (vault git history on athena, last 30 days)

A **marker write‑back** here is a commit that modifies `lib/X.pdf` and `ref/X.md` together without
touching the sidecar `lib/X.md`. That pattern is the scan writing both the note and the marker; a
Highlights save changes the sidecar instead.

- **596** such PDF/note pairs in **131** commits. Most came in bulk runs (one 2026‑10‑03 commit had
  213), and **68** commits contained exactly one PDF.
- Status transitions in those 68 single‑PDF events:

| Transition | Count | When it happens |
| --- | ---: | --- |
| `next → wip` | 17 | you start reading |
| `ready → read`, `wip → read`, `next → read` | 24 | you finish, often with the PDF still open |
| `ready → next` | 8 | you queue it, about to read |
| no status change (parent hint, etc.) | 10 | |
| other (`read→next`, `ready→wip`, …) | 9 | |

- Every write re‑serialises the whole PDF. For example, `lib/blogs/netclode.pdf` (19.6 MB) went
  `Bin 19610006 -> 19610002 bytes` for a status flip. Git packs may delta‑compress this, but every
  flip still creates a new full blob.

**Conclusion:** marker writes cluster in your reading sessions, about 2 a day. The conflict is a
predictable result of the design.

### 2.3 Highlights itself (read‑only inspection on the Mac)

| # | Fact | How |
| --- | --- | --- |
| H1 | Highlights 2026.1.2 (602) on macOS 26.5. Sandboxed (`~/Library/Containers/net.highlightsapp.universal`). `NSDocumentClass = Highlights.Document`. Declares an iCloud container | `Info.plist` |
| H2 | **`+[Highlights.Document autosavesInPlace]` returns YES.** The implementation is `mov w0, #0x1; ret` | `otool -oV` for the IMP, then `otool -tvV` |
| H3 | Document overrides: `init`, `fileURL`/`setFileURL:`, `canAsynchronouslyWriteToURL:…`, `makeWindowControllers`, `dataOfType:error:`, `fileWrapperOfType:error:`, `readFromData:ofType:error:`, `saveToURL:ofType:forSaveOperation:completionHandler:`, `fileAttributesToWriteToURL:…`, and printing. **It does not override** `presentedItemDidChange`, `relinquishPresentedItemToWriter:`, `savePresentedItemChangesWithCompletionHandler:` or `revertToContentsOfURL:…`, so AppKit's defaults apply | ObjC class metadata |
| H4 | The `saveToURL:` override first calls **`[super saveToURL:… forSaveOperation:<same op>]`**, so autosaves are not suppressed. Then, if `SaveSidecarMarkdownFile` is set, the type is `com.adobe.pdf` and the subscription is active, it writes the sidecar Markdown **through its own `NSFileCoordinator`** (`addFilePresenter:`, `initWithFilePresenter:`) | disassembly of the Swift body |
| H5 | File menu: Save (`saveDocument:`), Save As, **Revert to Saved** (`revertDocumentToSaved:`), Close (`performClose:`). The binary has `==> Reloading PDF document` / `PDF Document reloaded` and an `isFirstRead` ivar, which point to an in‑place reload path in `readFromData` | `MainMenu.nib` strings, binary strings |
| H6 | Not scriptable (−1728, no `.sdef`). Accessibility exposes the visible tab's path, but background tabs only by **file name** | prior research `research:202610/highlights_tab_switcher/highlights_tab_switcher__final.md` (E1, E4–E7) |
| H7 | URL scheme `highlights://<stem>#page=N`, which bob already emits in sidecar links | `Info.plist`, `docs/` |

### 2.4 What AppKit actually does: an experiment on your Mac

**Setup.**

- A Swift `NSDocument` subclass with `autosavesInPlace = YES`.
- No windows and `NSApplication` activation policy `.prohibited`, so nothing appeared on screen.
- It ran over SSH in `/tmp`, nowhere near Highlights or the vault. Files were cleaned up afterwards.
- A second process played bob and replaced the file using the method in each row.
- Source and full log are in Appendix A.

| Case | Document | bob's write | What AppKit did | Outcome |
| --- | --- | --- | --- | --- |
| **A** | clean | **uncoordinated** temp+rename (what bob does today) | `presentedItemDidChange` fired, **but no reload** | document stays stale; the next save conflicts |
| **D** | unsaved edit | **uncoordinated** (today) | nothing until save. Save failed: *"The document “doc.txt” could not be saved. The file has been changed by another application."* Options: **Save Anyway / Revert / Save As…** | **your bug, reproduced** |
| **C** | clean | coordinated write (`.forReplacing`) | relinquish → write → `revertToContentsOfURL` → `readFromData` | **reloads in place, clean** ✓ |
| **B** | unsaved edit | coordinated **write only** | relinquish → write → `dataOfType` (kept as an `NSFileVersion`) → revert | the edit **disappears from the live document**; it survives only as a Versions snapshot ✗ |
| **E** | unsaved edit | one combined `coordinate(readingItemAt:…, writingItemAt:…)` call | same as B; **no save first** | ✗ (a trap for implementers) |
| **F** | clean | combined read+write | same as C | ✓ |
| **G** | unsaved edit | **coordinated read, then a separate coordinated write** | `savePresentedItemChanges` → `dataOfType` (**edit saved to disk**) → the writer **saw the edit** and appended its change → revert → document clean | **edit kept, bob's change applied, no dialog** ✓✓ |

- In case G, the time from the start of bob's write to the completed reload was about 0.6 s.
- The test used a stand‑in document class, not Highlights. Highlights overrides none of these AppKit
  paths (H3, H4), so I expect the same behaviour.
- Two things still need checking in real Highlights (§8):
  - its own reload (`readFromData` on a later read);
  - whether page and scroll position survive the reload.

### 2.5 What Bob Mac Capture can already do

- **`AXHighlightsTabsReader`.**
  - Reads, selects and **closes** Highlights tabs through Accessibility.
  - The close path selects the tab, presses the window close button, verifies the close, detects a
    blocking sheet, and restores the previously selected tab.
  - Closed tabs go on an in‑memory **⇧⌘T reopen stack** (`RefsClosedTabs`).
- **`NotificationService`.** `UNUserNotificationCenter` with categories and actions; it already posts
  refs‑scan notifications.
- **Bundle identity and grant.** The bundle id `org.bobs.bob-mac-capture` holds the Accessibility
  grant (`AccessibilityTrust`).
- **No inbound channel from bob.** The app only spawns `bob` and watches the vault through FSEvents.
- **Open bead `bob-cli-6h`.** It wants Bob Mac Capture to say where reading tasks landed **after
  the scheduled Mac scan**. That needs the same bob → app channel this feature needs (§7.4).

### 2.6 Other probes (Mac, over SSH, no permissions needed)

- `lsappinfo front` reports the frontmost app's bundle id.
- `ioreg -c IOHIDSystem` reports `HIDIdleTime` (117 s at probe time).

Both work from a non‑GUI context, so a cron‑launched `bob` can tell whether you are *actively* in
Highlights.

---

## 3. Root cause

- When bob replaces the PDF without coordination, Highlights' `NSDocument` is told that something
  changed (case A) but **does not reload**. AppKit reloads documents only for **coordinated**
  writers. Its revert lives in the reacquire path of `relinquishPresentedItemToWriter:`.
- From then on Highlights shows an old copy.
- The next autosave or ⌘S notices the newer modification date and stops with the
  Save Anyway / Revert / Save As dialog. Both main answers are bad:
  - **Save Anyway** writes the stale marker back. The status regresses, and the next scan sees a
    marker‑side change that may conflict with the reading task. This is the hazard
    `decisions.md:710` already records.
  - **Revert** drops every annotation made since the last save (into Versions, at best). You then
    redo them by hand, which is what you are doing today.

---

## 4. Critique of the proposed plan

**What is right**

- **Save Highlights' in‑memory work before bob writes.** This is the critical ordering, and you
  spotted it. Without it any refresh loses annotations (case B).
- **Refresh the open document after the write.** Reloading is what removes the conflict.
- **Make it visible.** Anything that changes a document under your eyes should say so.

**What is wrong with "bob ref scan closes and reopens the tab"**

1. **Wrong process.**
   - Most marker writes come from **cron**, every 15 minutes. UI scripting (System Events
     keystrokes or AX presses) needs the **Accessibility permission for the process that does it**.
   - For a cron job that means granting it to cron itself, which is far too broad, or to the `bob`
     binary.
   - `bob` is ad‑hoc signed and replaced by `cargo install` with every daily release. macOS ties an
     ad‑hoc grant to the binary's hash, so **every release would silently revoke it**. Bob Mac
     Capture hit exactly this and had to move to stable signing.
   - bob‑cli already avoids Background Task Management tracking the ad‑hoc binary by launching its
     LaunchAgent through `/bin/sh` (`docs/vault-git-sync.md`).
2. **Focus and races.**
   - ⌘S and ⌘W go to the frontmost app's key window. bob would have to activate Highlights and
     select the right tab first, interrupting whatever you are doing, during reading sessions.
   - A synthetic keystroke racing your real typing can land in the wrong window.
3. **Background tabs can't be targeted well.** Accessibility exposes them by file name only (H6), and
   names can collide.
4. **Ordering traps.**
   - If the document is already stale, ⌘S itself raises the conflict sheet.
   - Closing a document with unsaved changes raises "Do you want to save?".
   - Every sheet needs its own handling.
5. **Disruption.** Close and reopen moves the tab and resets scroll, zoom, sidebar and selection,
   and possibly the page. Undo history goes either way.
6. **It re‑implements an OS protocol.** AppKit already implements both halves for Highlights:
   "save before someone reads" and "reload after someone writes". Highlights already uses
   coordination itself (H4).

**Verdict.** It is worth fixing: about two events a day, a real chance of losing annotations, and a
stale‑write‑back hazard. Keep the three goals and replace the mechanism.

---

## 5. Alternatives considered

| # | Approach | Clean open doc | Unsaved edits | Disruption | Permission | Verdict |
| --- | --- | --- | --- | --- | --- | --- |
| A | **Your plan, in bob:** UI‑script ⌘S, close, write, reopen | fixed | fixed if the ordering is right | high (focus, tab order, place) | Accessibility for cron or bob, which churns | **No** |
| B | Same choreography in **Bob Mac Capture**, which already has Accessibility and a close ladder, triggered by bob | fixed | fixed | medium (tab churn, focus) | existing grant | **Plan B only, user‑initiated** (§9) |
| C | **Coordinated read, then coordinated write** (`NSFileCoordinator`) | fixed (C) | fixed (G) | low: in‑place reload, no focus change | none | **Recommended** |
| D | Hold marker writes while *that* PDF is open | fixed | fixed | none | needs per‑PDF open detection. Only Bob Mac Capture's Accessibility grant can see tabs, there is no channel, and `lsof` shows 0 PDFs (H6) | used only as an **activity hold** (§7.3) |
| E | Stop mirroring lifecycle `status` into the PDF | fixed for status | fixed for status | none | none | A larger contract change, and other PDF writes still need C. Revisit separately (§10) |
| F | Drop `-w` from cron and write markers only on demand | partly | partly | none | none | **No.** A refused marker write blocks the PDF's whole note sync (`needs_write_pdfs`) |
| G | Write uncoordinated, then "nudge" with an empty coordinated write | fixed | **not fixed** (behaves like B) | low | none | Worse than C |

---

## 6. Requirement adjustments (explicit)

| # | As asked | Adjusted | Why |
| --- | --- | --- | --- |
| R1 | Close the Highlights tab and reopen it | **Reload in place through file coordination.** bob never closes, reopens, selects or reorders tabs | Same effect without UI scripting, a permission, focus changes or tab churn (cases C, G) |
| R2 | Save unsaved annotations first, perhaps with ⌘S | **Ask Highlights to save through a coordinated read**: macOS's standard "save before others read" request. No keystrokes | Case G; H4 shows Highlights passes autosaves to AppKit |
| R3 | Send a Mac notification when this happens | **Yes, from Bob Mac Capture** (real app identity, an action button, Settings toggle). It is **quiet** (`.passive`, no sound), **sent only when the PDF was open in Highlights**, and grouped per scan. bob's CLI and JSON report it too | A notification from bob under cron would come from Script Editor (`osascript`) and cannot know what is open. Noise control |
| R4 *(new)* | — | **Never refresh while you are in the middle of something.** If Highlights is frontmost and input was under 30 s ago, hold marker writes until the next scan | Protects a half‑typed note or a drag (§7.3) |
| R5 *(new)* | — | **Bounded.** Coordination gets a 10 s budget, then `cancel()` and a hold. Never hang the scan or Highlights | A presenter can stall or sit behind a sheet |
| R6 *(new)* | — | **Run an acceptance test against real Highlights before shipping.** Plan B if it fails | The experiment used a stand‑in document |
| R7 *(scope)* | `bob ref scan` | Also `bob ref sync --write-pdf` (same writer). Later, every bob PDF mutation on macOS | One primitive. Retires "Close the PDF in Highlights first" |

---

## 7. Recommended design

### 7.1 What you will experience

**A typical morning:**

1. **10:02.** You link "Attention Is All You Need" into today's Pomodoro. The reading task moves
   Ready → Next.
2. **10:04.** You open it in Highlights and make three highlights. They are unsaved.
3. **10:15.** The cron scan runs. Highlights is frontmost and you scrolled 4 s ago, so bob **holds**
   the marker write. The ref note and everything else still sync normally.
4. **10:30.** You are in Obsidian when the next scan runs.
   - bob makes a **coordinated read**, and Highlights saves your three highlights to disk.
   - bob rewrites the page‑1 marker (`status: next`).
   - Highlights **reloads that tab in place**: same tab, no dialog.
5. A quiet banner arrives (below). Back in Highlights, the page‑1 note says `status: next`, your
   highlights are all there, and the document is clean. The only visible cost is that ⌘Z history
   for that document starts fresh.

**The notification, posted by Bob Mac Capture:**

```text
┌──────────────────────────────────────────────────────┐
│ ◆ Bob Mac Capture                               now  │
│ Refreshed in Highlights                              │
│ Attention Is All You Need                            │
│ Next → Reading · your unsaved highlights were saved  │
│ first                                                │
│                                 [ Show in Bob Refs ] │
└──────────────────────────────────────────────────────┘
```

**Copy rules:**

- **Title.** "Refreshed in Highlights". For more than one PDF in a scan: "Refreshed 3 PDFs in
  Highlights", with the titles in the body.
- **Subtitle.** The reference title.
- **Body.**
  - Use the Refs vocabulary: Ready / Next / Reading / Read / Dropped (`RefState`).
  - Add "· your unsaved highlights were saved first" only when bob observed that save.
  - Non‑status changes read "Updated the page‑1 marker".
- **Behaviour.**
  - `interruptionLevel = .passive`, no sound.
  - A `threadIdentifier` groups these banners.
  - The action "Show in Bob Refs" opens the panel with that note selected.
- **Setting.** Settings › References gains a toggle, "Tell me when Bob refreshes an open PDF"
  (on by default).

**CLI (human):**

- The summary gains clauses only when they apply, e.g.
  `… · 1 marker · 1 held (Highlights in use) · writes: …`.
- `-v` prints per‑PDF lines:
  - `pdf_marker_action: update (coordinated; open editor saved first)`
  - `pdf_marker_action: held (Highlights in use; retrying next scan)`

**JSON (additive, schema stays 1):**

- Per note: `marker_write: {"mode": "coordinated" | "plain", "editor_saved_first": bool}`.
- Top level: `held: [{"pdf", "note", "reason": "editor_active" | "coordination_timeout" | "marker_changed"}]`.

### 7.2 bob‑cli: one coordinated‑replace primitive (macOS only)

Add a new module, `native::file_coordination`.

- **macOS:** uses `objc2`, `objc2-foundation` (features `NSFileCoordinator`, `NSURL`, `NSError`) and
  `block2`, all under `cfg(target_os = "macos")`.
- **Elsewhere:** a pass‑through that just calls the closure.

```rust
pub(crate) struct Coordinated { pub editor_saved_first: bool }

pub(crate) fn replace_coordinated<T>(
    path: &Path,
    budget: Duration,
    rewrite: impl FnOnce(&Path) -> Result<T>,
) -> Result<(T, Coordinated)>;
```

**Algorithm** (each step is backed by the spike):

1. `pre = sha256(path)`.
2. **Flush.** Call `coordinateReadingItemAtURL(url, options: [])` with an empty accessor. Open
   presenters run `savePresentedItemChanges`, so Highlights autosaves in place (case G).
   - This **must be a separate call.** The combined read+write method does *not* flush (case E).
3. `editor_saved_first = sha256(path) != pre`.
4. **Write.** Call `coordinateWritingItemAtURL(url, .ForReplacing)`. Inside the accessor, call
   `rewrite(new_url)`, which does today's load, edit, temp, fsync and `rename` unchanged.
5. **Bound it.** A watchdog thread calls `coordinator.cancel()` after `budget` (default 10 s). The
   pending call returns `NSUserCancelledError`, which maps to a **hold**.
6. On return, presenters reacquire the file and AppKit reloads the open document (cases C and G).

**Changes to the marker writer.** Run `write_pdf_marker` inside `rewrite`:

- Load the **fresh** bytes, which now include the annotations Highlights just saved.
- Find the marker again (the first page‑1 `/Text` annotation). A full save by Highlights can renumber
  objects, so do not reuse the planned `ObjectId` blindly.
- Compare its contents with `plan.marker.contents` (line endings normalized):
  - **Equal:** set `/Contents` and save.
  - **Different:** you edited the marker sticky note. Return `marker_changed` and hold; the next
    scan's three‑way merge handles it.

**Changes to the guard.**

- On macOS, the whole‑file SHA check (`ensure_pdf_unchanged_for_write`, B5) is replaced *for the
  marker step* by the marker‑level check inside the coordinated block. The flush legitimately
  changes the file's bytes. Linux keeps the old check.
- The existing post‑write rehash of `source_pdf_sha256` still runs, and now records the
  post‑flush, post‑marker digest.

**Holds are not failures.** A held PDF skips its note write this run, just as today's "PDF changed
during sync; rerun" path does. It is reported under `held`, the exit code stays 0, and the cron
wrapper stays silent.

**Kill switch.** `highlights.coordinate_pdf_writes: false`, or `BOB_HIGHLIGHTS_COORDINATE=0`,
restores today's behaviour.

### 7.3 Activity hold

- **Rule.** Before executing writes, if any plan has `marker_write_needed`, hold those plans when
  **both** of these are true:
  - Highlights (the resolved bundle id) is frontmost (`lsappinfo front`);
  - HID idle time is under 30 s (`ioreg -c IOHIDSystem`).
- **No knowledge of open tabs needed.** bob cannot see which PDFs are open, and the rule does not
  need to.
- **Cost.** A held PDF syncs on the next scan once you pause or switch apps (at most 15 minutes in
  practice).
- **User‑initiated runs are naturally exempt.** A terminal `bob ref sync`, or ⌘S in the Refs panel,
  has its own window frontmost.
- **Tuning.** The acceptance test (§8, step 4) decides the threshold. If reloading mid‑typing proves
  harmless, it can drop to about 10 s or go away.

### 7.4 One bob → Bob Mac Capture channel (shared with `bob-cli-6h`)

The decision `decisions:mac-capture-is-a-thin-client` gives presentation to the app and vault
mutation to bob.

- **bob writes a scan receipt.** After every writing scan or sync on macOS, it writes the
  **same JSON envelope as `bob ref scan -f json`** atomically to a host‑local receipt file (for
  example `last-scan.json` under bob's state directory). Then it posts a Darwin notification with
  libSystem's plain C `notify_post("org.bobs.bob.ref.scan-finished")`.
- **The app reacts.** Bob Mac Capture registers with `notify_register_dispatch` and reads the
  receipt with its **existing** `RefsScanOutcome` decoding. It notifies about a refreshed PDF when
  either:
  - Accessibility is trusted and the PDF's file name is among Highlights' open tabs (its existing
    read‑only reader); or
  - the receipt says `editor_saved_first` (so the PDF was certainly open).

  Everything else goes to Recent Activity only.
- **Why a receipt file:**
  - It works when bob ran from cron.
  - It is debuggable (`cat` it).
  - It closes the observability gap from B7.
  - It also unblocks `bob-cli-6h`'s "reading task landed" notification.
- **Safe when the app is off.** If Bob Mac Capture is not running, nothing is shown and the write is
  still safe.
- **Docs.** Document the receipt and the notification name in
  `docs/reference/mac-capture/protocol.md` as an additive contract.
- **Accessibility stays read‑only.** This feature only reads tab names. That matches the intent of
  `bob-cli-8c`, although the existing Close Tab feature has already widened Accessibility use.

### 7.5 Failure modes

| Situation | Behaviour |
| --- | --- |
| Highlights not running | No presenters, so coordination returns at once. Normal write, no notification |
| PDF open and clean | Reloads in place. Notification |
| PDF open with unsaved annotations | Highlights saves them, bob writes on top, reload. Notification says "saved first" |
| You are actively in Highlights | **Held**; retried on the next scan |
| Highlights hung, or a sheet blocks its save | 10 s budget, then `cancel()`, then **held** |
| You edited the marker note in Highlights | `marker_changed`, then **held**. The next scan's three‑way merge applies it |
| An edit lands in the roughly 50 ms between flush and write | AppKit keeps it as a Versions snapshot and reloads (case B). Unlikely given the hold. Documented |
| Kill switch set, or not macOS | Today's behaviour |
| macOS 27 | A 2026‑09 forum report says a **SwiftUI** `DocumentGroup` app hangs when another process replaces its file through coordination. Highlights is classic AppKit, but **retest after upgrading** |

### 7.6 Tests, docs, decision

- **Unit tests (Linux and macOS):**
  - the hold predicate (with injected probes);
  - marker re‑validation against fresh bytes, including renumbered objects;
  - JSON and human report fields.
- **macOS CI integration test.** bob‑cli already runs `cargo test` on `macos-latest`.
  - Compile the roughly 60‑line Swift presenter fixture from Appendix A with `swiftc` in a
    `cfg(target_os = "macos")` test, and skip if `swiftc` is missing.
  - Run bob's primitive against it and assert cases A, C and G: the flush happened, the contents
    are merged, and the document is clean after the reload.
- **Docs.**
  - `docs/highlights-ref-sync.md`: replace "Keep Highlights and Obsidian idle while testing PDF
    writes so the apps do not race the CLI" with the coordination contract.
  - `docs/vault-git-sync.md`: fix the crontab drift (§10).
  - `docs/reference/mac-capture/protocol.md`: the receipt.
- **Decision record** (through `/sase_memory_write`): *"bob writes Highlights PDFs through file
  coordination and never UI‑automates Highlights."* Rejected alternatives: scripted save, close and
  reopen; per‑PDF holds through Accessibility; dropping status from the marker.

---

## 8. Acceptance test (about 30–45 minutes on the Mac, before building)

**Setup.**

- Use a scratch copy **outside the vault** (`/tmp/coord-test/X.pdf`) with a marker note.
- The writer is a tiny Swift tool, adapted from Appendix A:
  1. coordinated read;
  2. coordinated write whose accessor uses PDFKit to change the page‑1 `/Text` annotation contents,
     writes to a temp file, and renames it over the original.

**Steps.**

1. Open the PDF, add two highlights, and **don't save**. Run the writer from Terminal (Highlights in
   the background). **Pass if:**
   - no dialog appears;
   - both highlights survive;
   - the marker text changed;
   - the document is not marked edited;
   - the tab stays in place.

   Also **record whether the page and scroll position held.**
2. Repeat with Highlights frontmost: `sleep 5; writer`.
3. Repeat with the PDF in a **background tab**.
4. Repeat with a **note popover open and half‑typed**. This sets the activity‑hold threshold.
5. Repeat with a modal sheet up (e.g. ⌘P). The writer must return within the budget.
6. Run the writer from **SSH or cron** context, not the GUI, to confirm that coordination reaches
   Highlights' GUI session.
7. **Control.** An uncoordinated `cp` over the open file must show the conflict, as a baseline.

**Decision.**

- Steps 1–3 and 6 pass: build Plan A (§7).
- Only the page jumps: still Plan A. Add a page‑restore follow‑up to Bob Mac Capture. It knows the
  visible tab's page from `AXTitle` ("– Page 5 of 25") and can reopen `highlights://stem#page=N`
  with `open -g`.
- Annotations are lost or a dialog appears: **Plan B**.

---

## 9. Plan B: your choreography, run by the app that can do it safely

Use this only if Highlights fails §8.

- **bob holds instead of writing.** On macOS, bob holds marker writes while Highlights is running and
  lists them in the receipt (`held`, reason `highlights_running`).
- **Bob Mac Capture offers the refresh.** It posts *"Attention Is All You Need has a Bob update
  waiting"* with **[Apply now]**. Applying:
  1. select the tab;
  2. press File › Save through Accessibility and verify the document is clean;
  3. close it with the existing close ladder (sheet detection included);
  4. run `bob ref sync --write-pdf <pdf>`;
  5. reopen with `open -g highlights://<stem>#page=N`, using the page captured from `AXTitle`;
  6. re‑select the previously active tab;
  7. show a toast.
- **Or apply when you close it.** Bob Mac Capture notices the PDF has left the tab set and runs
  the sync.
- **Costs.** Coarser holds, Accessibility doing writes (a decision‑record change), and tab churn.
  That is why it is Plan B.

---

## 10. Residual risks and follow‑ups

- **Other uncoordinated writers remain.**
  - `bob ref rename` and the id stamp should become a coordinated **move**, so Highlights'
    `NSDocument` follows the file (`presentedItemDidMoveToURL:`). That lets the rename card drop
    "Close the PDF in Highlights first".
  - `create --force` should use the same coordinated replace.
  - Git checkouts by `bob vault-sync` can still replace an open PDF when a remote host changed it.
    This is rare, and out of scope here.
- **Optional "pending marker" refinement.** On a hold, write the note now but leave
  `highlights_marker_base/hash` at the state both sides last agreed on. The next scan then sees a
  frontmatter‑only change and writes the marker. Holds would no longer delay the note. This needs
  careful three‑way‑merge tests.
- **Status in the PDF has a cost.** Each flip re‑serialises the whole PDF and commits a new blob
  (2.2). Consider a separate decision on whether lifecycle `status` belongs in the marker at all,
  since the vault's `^ref` task is now authoritative. Coordination is still needed for `parent`,
  `id` and other writes.
- **Undo.** A reload clears that document's undo history. It is documented, and acceptable.
- **Observability.** Even before this ships, the cron wrapper should log a one‑line summary on
  success (B7).
- **Doc drift found.**
  - The live Mac crontab runs all three Bob jobs at `*/15` (the same minute) with only `>> log`.
  - `docs/vault-git-sync.md` says they are staggered at :00, :05 and :10, and that the highlights and
    projects jobs redirect `2>&1`.
  - Either the crontab or the docs should change.

---

## 11. Recommended solution

**Fix the root cause, not the symptom: make bob a polite co‑writer.**

On macOS, bob changes PDFs only through a **coordinated read, then a coordinated write**. macOS asks
Highlights to save your unsaved annotations first and to reload the document in place afterwards.

- **No tab closing or reopening and no keystrokes.** Background tabs are covered too.
- **No Accessibility for bob.**
- **No focus change.**

**Phases:**

1. **Phase 0 (Mac, about 45 min, with you present).** The §8 acceptance test with a scratch PDF.
   Choose Plan A or Plan B, and set the activity‑hold threshold.
2. **Phase 1 (bob‑cli).**
   - `native::file_coordination::replace_coordinated`: flush read, then write, with a timeout and
     `cancel()`.
   - Marker‑level re‑validation inside the block.
   - The activity hold.
   - `held` and `marker_write` report fields.
   - A kill switch.
   - The macOS CI presenter test.
   - Docs and the decision record.
3. **Phase 2 (bob‑cli + Bob Mac Capture).**
   - bob: the scan receipt and `notify_post`.
   - Bob Mac Capture: observer, read‑only open‑tab check, a passive grouped notification with
     "Show in Bob Refs", and the Settings toggle. The same channel then serves `bob-cli-6h`.
4. **Phase 3 (later, optional).**
   - Route `ref rename` (coordinated move) and `create --force` through the primitive, and retire
     the rename card's hint.
   - The pending‑marker refinement.
   - A decision on keeping `status` in the marker.

**Changes to your requirements:**

- Close and reopen becomes an in‑place reload.
- ⌘S becomes the coordinated‑read save request.
- The notification comes from Bob Mac Capture, quietly, and only when the PDF was actually open.
- Added: never refresh while you are actively in Highlights.
- Added: bounded waits.
- Added: a real‑Highlights acceptance test before shipping.

---

## Appendix A: the AppKit experiment

**Environment:** macOS 26.5 on `mac`, `xcrun swiftc -O`, run over SSH in `/tmp/cld-nsdoc-spike`
(since deleted). The document class:

```swift
final class Doc: NSDocument {
    var text = ""
    override class var autosavesInPlace: Bool { true }
    override class var readableTypes: [String] { ["public.plain-text"] }
    override class var writableTypes: [String] { ["public.plain-text"] }
    override class func isNativeType(_ type: String) -> Bool { true }
    override func data(ofType typeName: String) throws -> Data { /* log */ text.data(using: .utf8)! }
    override func read(from data: Data, ofType typeName: String) throws { /* log */ text = String(decoding: data, as: UTF8.self) }
    // savePresentedItemChanges / relinquishPresentedItem(toWriter:) / presentedItemDidChange /
    // revert(toContentsOf:ofType:) overridden only to log, then call super.
}
// Opened with Doc(contentsOf:ofType:) + NSDocumentController.shared.addDocument(doc),
// NSApplication activation policy .prohibited (no windows, no Dock icon).
```

The writer (a second process) that plays bob:

```swift
func replace(_ target: URL) {             // read current bytes, append a tag, temp + rename
    let cur = (try? String(contentsOf: target, encoding: .utf8)) ?? "?"
    let tmp = target.deletingLastPathComponent().appendingPathComponent(".spike.tmp")
    try! (cur + "+" + tag).write(to: tmp, atomically: false, encoding: .utf8)
    _ = rename(tmp.path, target.path)
}
let c = NSFileCoordinator(filePresenter: nil); var err: NSError?
switch mode {
case "plain":         replace(url)                                                     // today
case "coordinated":   c.coordinate(writingItemAt: url, options: .forReplacing, error: &err) { replace($0) }
case "readwrite":     c.coordinate(readingItemAt: url, options: [], writingItemAt: url,
                                   options: .forReplacing, error: &err) { _, w in replace(w) }
case "readthenwrite": c.coordinate(readingItemAt: url, options: [], error: &err) { _ in }  // flush
                      c.coordinate(writingItemAt: url, options: .forReplacing, error: &err) { replace($0) }
}
```

Log, excerpted (`[t thread]`; `userX` is an unsaved user edit and `bobX` is the writer's change):

```text
== A: clean doc, UNCOORDINATED temp+rename write
    [writer] read inside: v0
[ 1.32 bg]   presentedItemDidChange
[ 4.32 main] A: doc.text=v0 edited=false                       <- stale, no reload
== B: DIRTY doc (unsaved user edit), COORDINATED write
[ 5.37 bg]   relinquishPresentedItemToWriter
    [writer] read inside: v0+bobA                              <- user's edit NOT on disk
[ 5.91 main]   dataOfType (save) -> v0+bobA+userB              <- preserved as a version
[ 5.93 main]   revertToContentsOf
[ 9.39 main] B: doc.text=v0+bobA+bobB edited=false             <- userB gone from the live doc
== C: clean doc, COORDINATED write
[ 9.96 main]   revertToContentsOf
[13.49 main] C: doc.text=v0+bobA+bobB+bobC edited=false        <- reloaded in place
versions of item after B/C: 1
== E: DIRTY doc, COORDINATED READ+WRITE (one call)
    [writer] read inside: v0+bobA+bobB+bobC                    <- no flush; same as B
== G: DIRTY doc, coordinated READ then coordinated WRITE
[21.66 bg]   savePresentedItemChanges (edited=true, unautosaved=true)
[21.67 main]   dataOfType (save) -> …+bobF+userG               <- edit flushed to disk
    [writer] coordinated READ saw: …+bobF+userG
    [writer] read inside: …+bobF+userG
[22.24 main]   readFromData <- …+bobF+userG+bobG               <- reload with both changes
[25.75 main] G: doc.text=…+userG+bobG edited=false disk=…+userG+bobG
== D: DIRTY doc, UNCOORDINATED write (today's bob behaviour), then save
[28.87 main] D: save ERROR: The document “doc.txt” could not be saved. The file has been changed by
             another application. | Click Save Anyway to keep your changes and save the changes made
             by the other application as a version, or click Revert to keep the changes from the
             other application and save your changes as a version. You can also click Save As to save
             your changes to a different file. | options=["Save Anyway", "Revert", "Save As…"]
```

## Appendix B: read‑only Mac commands used

- `crontab -l` and `cat ~/bin/maybe_bob_highlights_sync`.
- `plutil -p /Applications/Highlights.app/Contents/Info.plist`, `DefaultPreferences.plist`, and
  `strings` on `MainMenu.nib`.
- `otool -oV` / `otool -tvV` on the Highlights binary, for the `Document` class methods,
  `autosavesInPlace` (IMP `0x1000361e4`: `mov w0, #0x1; ret`) and the `saveToURL:` body.
- `lsappinfo front` and `ioreg -c IOHIDSystem` (`HIDIdleTime`).
- `NSDocument.h` header comments from the Command Line Tools SDK.

## Sources

- Apple, *File System Programming Guide: The Role of File Coordinators and Presenters* —
  https://developer.apple.com/library/mac/documentation/FileManagement/Conceptual/FileSystemProgrammingGuide/FileCoordinators/FileCoordinators.html
- Apple, *Document‑Based App Programming Guide for Mac: Core App Behaviors* (autosave in place;
  "Document-based Cocoa apps use file coordination automatically") —
  https://developer-rno.apple.com/library/archive/documentation/DataManagement/Conceptual/DocBasedAppProgrammingGuideForOSX/StandardBehaviors/StandardBehaviors.html
- Apple Developer Forums 845923, *SwiftUI `Document` app hangs on macOS 27 when another process
  changes its file*. Its stack shows `-[NSDocument relinquishPresentedItemToWriter:]` →
  `revertToContentsOfURL:` — https://developer.apple.com/forums/thread/845923
- Apple Developer Forums 96551, *iCloud NSDocument save warnings* (spurious "changed by another
  application") — https://developer.apple.com/forums/thread/96551
- Apple Developer Forums 678309 (`presentedItemDidChange` with uncoordinated writers) —
  https://developer.apple.com/forums/thread/678309
- `objc2-foundation` `NSFileCoordinator` bindings —
  https://docs.rs/objc2-foundation/0.3.2/objc2_foundation/struct.NSFileCoordinator.html
- Prior research (unrelated swarm):
  `research:202610/highlights_tab_switcher/highlights_tab_switcher__final.md` (Highlights is not
  scriptable; Accessibility tab facts; `open -a` selects an existing tab).
