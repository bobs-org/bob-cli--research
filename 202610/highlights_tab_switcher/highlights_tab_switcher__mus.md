# Reference panel as a Highlights tab-switcher: open-PDF filter research

Researcher: mus (independent report in a 5-researcher swarm).
Question: should the bob-mac-capture reference panel grow a special mode/filter
that shows only the reference notes whose PDFs are currently open in the
Highlights app, so the panel doubles as a tab-switcher for Highlights?
Critique the plan, adjust requirements where justified, and end with a
recommended solution.

## TL;DR

- **Yes, build it — but as an orthogonal toggle, not a new scope, and not on
  window titles.** The request is a good idea aimed at a real pain (Highlights'
  built-in library lookup is weak; Bryan reads everything there), and the Refs
  panel is already the right launcher. The only hard problem is learning which
  PDFs Highlights has open.
- **Recommended detection, in order: Accessibility `AXDocument` (exact file
  URLs, one-time permission) with an `lsof` zero-permission fallback.**
  Explicitly reject `CGWindowListCopyWindowInfo` window titles: since macOS
  10.15 they require Screen Recording permission, which re-prompts monthly
  since Sequoia — an unacceptable burden for a tab-switcher. Reject scraping
  Highlights' private state files for the same fragility reason the thin-client
  decision rejects second implementations.
- **Enter on a filtered row must focus the existing Highlights window/tab
  (`AXRaise` + activate), not re-open the PDF.** Re-open is the fallback. That
  single behavior is what makes it a tab-switcher instead of a second launcher.
- No new `bob` endpoint is needed for v1: the join key (`source_pdf`) already
  ships in `bob ref list` JSON, and open-PDF detection is presentation-layer
  work that belongs in Swift per the accepted
  `mac-capture-is-a-thin-client` decision.
- Phase the work: half-day Mac probes first (tab model unknown), then a
  zero-permission slice (`lsof` + panel-tracked opens), then the exact
  Accessibility mode behind a Settings toggle.

## 1. What I actually inspected (evidence, not assumption)

All paths below are from the live checkouts on 2026-10-15.

### 1.1 The panel already has everything except the open-set

From `sase/repos/linked/bob-mac-capture` (opened via `sase repo open
bob-mac-capture`):

- `Sources/BobMacCapture/Refs/RefsPanelModel.swift` — the model owns
  `query`, `scope: RefScope`, the frozen `listing`, id-based selection, open
  dispatch (`RefsOpenTarget.highlights/.note/.reveal/.defaultApp`), and
  banners. `prepareForPresentation()` resets query + scope and re-ranks —
  the natural hook for snapshotting the open-set.
- `Sources/RefsCore/RefsModel.swift` — `RefItem.pdfPath` is the vault-relative
  `source_pdf` (e.g. `lib/papers/ea_graph.pdf`); `id` is the note path, never
  the PDF path, because PDF stems repeat. That sentence is the whole matching
  contract: join on resolved PDF path, display by note id.
- `Sources/BobMacCapture/Refs/RefsKeyRouter.swift` — `⌘1..⌘5` are taken by
  kind scopes (All/Chats/Papers/Articles/Docs); `⌘R` refresh, `⌘S` scan,
  `⌘K` actions, plain `Tab`/`Return` opens in Highlights. Any new toggle needs
  a free key (see §5.2).
- `Sources/RefsCore/RefsFetching.swift` (`BobRefsFetcher`) — the panel already
  refreshes from `bob ref list -R all -A -f json` (snapshot), `plan`, and `ref
  show`. Verified live: `bob ref list -R all -A -f json` returns 1033 rows,
  each carrying `source_pdf` (vault-relative), `reading_state`, `ref_type`,
  `annotation_count`, etc. The join key exists today; no CLI change required.
- `Sources/BobMacCapture/Refs/RefsLibrary.swift:320` — `pdfURL(for:)` already
  resolves a `RefItem` to an absolute vault PDF URL. Matching can reuse it.
- `Sources/BobMacCapture/HighlightsTakeover.swift`, `RefsHighlightsOpenKey.swift`
  — the app already knows Highlights' bundle id
  (`net.highlightsapp.universal`), tracks Highlights-frontmost state, and
  opens PDFs via `NSWorkspace` (`WorkspaceRefsOpener`). There is **no existing
  code that reads state back out of Highlights** — detection is greenfield.
- Prior research I wrote for the sibling questions
  (`highlights_quick_open_refs_panel__mus.md`, 2026-10-08) established that
  "open this PDF in Highlights" is an OS-level file open, not a
  Highlights-library operation — which is why the launcher works. The reverse
  direction (ask Highlights what is open) was never probed; §3 below is that
  probe plan.

### 1.2 What the web says about the candidate OS mechanisms

- `CGWindowListCopyWindowInfo` returns window id/bounds/owner with no
  permission, but **`kCGWindowName` (the title) requires Screen Recording
  permission**, and Screen Recording re-prompts monthly since macOS 15
  Sequoia — documented by third-party macOS window-API research (squeegee
  project specs, 2026). The panel targets macOS 26 (`@available(macOS 26.0,
  *)` throughout `Refs/`), so the strict regime applies.
- The Accessibility API exposes window titles via `kAXTitleAttribute`
  **without** Screen Recording, and exposes **`kAXDocumentAttribute` — a
  `file://` URL for the document behind a window in document-based apps**
  (Xcode, TextEdit, and per community reports, most NSDocument apps).
  Cost: one-time Accessibility permission prompt.
- `lsof -p <pid>` shows a process's open files with no special entitlement
  for same-user processes; used in practice as a diagnostic fallback for
  exactly this "which files does that app hold open" question.
- No evidence found that Highlights ships an AppleScript dictionary, URL
  scheme, or documented open-documents API (web search for its bundle id +
  scripting/automation returned nothing scriptable). Assume none until the
  5-minute probe in §3.1 says otherwise.

## 2. Critique: is this a good idea?

**Yes — with the adjustments in §4.** The diagnosis is sound: Bryan lives in
Highlights, its `<ctrl+o>` lookup is the same weak-library-browser complaint
that motivated the Refs panel in the first place, and a 2–6-tab working set is
exactly the case where the full ranked panel is overkill. Reusing the panel as
the switcher beats alternatives:

| alternative | verdict |
|---|---|
| Teach Highlights' own lookup / wait for vendor fix | No leverage; out of our control. |
| macOS App Exposé / `⌘`` window cycling | No ref metadata, no search, breaks when tabs share one window. |
| Separate menu-bar tab-switcher app | Second hotkey, bundle, and settings for ~30 lines of matching logic. |
| Filter inside the existing Refs panel | **Recommended.** One hotkey, one learned UI, metadata + search survive. |

Honest costs to keep in view:

1. **A new OS permission is the dominant cost, not the code.** The matching +
   toggle is small (a detector protocol, a filter predicate, a focus-open
   branch). The Accessibility prompt, its Settings copy, the denied-state
   banner, and the fallback path are most of the work. If Bryan dislikes
   permission prompts, the zero-permission slice (§6.2) still delivers ~70% of
   the value.
2. **Highlights' tab model is the chief unknown.** One window with tabs vs. N
   windows changes the focus implementation (`AXRaise` on a window vs.
   activate + hope) and whether "tab order" is even observable. Nothing should
   be built before the probes in §3.
3. **Scope creep into window management must be refused.** MRU ordering,
   "close tab from panel", "reveal tab index" — all tempting, all downstream
   of an exact open-set + focus. V1 lists and focuses; nothing more.

## 3. How to learn which PDFs Highlights has open

Ordered by recommendation. The Mac probes in §3.5 decide between options 1–2
in under an hour; options 4–5 are documented here so they stay rejected.

### 3.1 Option 0 — AppleScript document model (5-minute probe, expect failure)

```applescript
tell application "Highlights" to get name of every document
```

If Highlights has no scripting dictionary this errors immediately and the
option dies. No permission cost if it worked, but nothing suggests it will.
Probe it first only because it is cheap.

### 3.2 Option 1 (recommended primary) — Accessibility `AXDocument`

For each window of the Highlights process (`bundleIdentifier ==
"net.highlightsapp.universal"`), read `kAXTitleAttribute` (display) and
`kAXDocumentAttribute` (exact `file://` URL). Join the file URLs against
`RefItem.pdfPath` resolved through the existing `pdfURL(for:)` path.

- Pros: exact paths (no title fuzzy-matching), no Screen Recording, titles
  also available for the unmatched-open-files diagnostic (§5.4).
- Cons: one-time Accessibility permission; unknown whether Highlights (likely
  a non-NSDocument, library-style app) populates `AXDocument` at all — the
  probe decides.
- Precedent in-repo: `HighlightsTakeover` already observes Highlights-frontmost
  via `NSWorkspace` notifications; the detector rides the same signals plus a
  ~2 s poll while the panel is visible.

### 3.3 Option 2 (recommended fallback) — `lsof` open-files + panel-tracked opens

- `lsof -p <Highlights pid> -Fn` (or `/proc`-equivalent listing), filter to
  `*.pdf` under the vault `lib/` dir. No new permission, no new dependency
  (`lsof` ships on macOS).
- Union with PDFs the panel itself opened this session (the model already
  records `pendingOpen`; retain a bounded MRU of successful Highlights
  opens). This covers Bryan's dominant flow — open-via-panel — even where
  `lsof` over/under-approximates.
- Cons: `lsof` over-approximates (recently closed files may linger as held
  fds; library thumbnails/index may hold others) and under-specifies order
  (no tab order, only set membership). Acceptable for a filter; not for
  MRU ordering — do not promise order in this mode.

### 3.4 Option 3 — rejected: `CGWindowListCopyWindowInfo` titles

Gives owner PID + bounds freely but withholds `kCGWindowName` without Screen
Recording, which re-prompts monthly since Sequoia. A tab-switcher that nags
monthly is worse than no tab-switcher, and titles would still need fragile
fuzzy-matching onto stems. Reject outright.

### 3.5 Option 4 — rejected: Highlights' private state (SQLite/plist/saved-state)

Would need no permission but parses an undocumented format that can change per
release, may lag live tabs, and may live in a protected container. This is the
second-implementation trap the thin-client decision exists to prevent. Reject.

### 3.6 Mac probes (run before any implementation, ~30–60 min total)

1. Dictionary probe: Script Editor → File → Open Dictionary → Highlights;
   plus the osascript one-liner in §3.1.
2. AX probe: with Accessibility granted to Terminal, run
   `axcli windows --app net.highlightsapp.universal` (or a 20-line Swift
   `AXUIElement` dump) with 2 PDFs open in tabs and 1 in a second window;
   record whether `AXDocument` is populated, and whether tabs appear as
   windows, tab groups, or one window.
3. `lsof` probe: `lsof -p $(pgrep -f Highlights) | grep '\.pdf$'` with known
   tabs open/just closed; record over/under-approximation.
4. Focus probe: `open -a Highlights <already-open-pdf>` — does it focus the
   existing tab/window or open a duplicate? Decides whether `AXRaise` work is
   mandatory for v1 or merely nice.

## 4. Requirement adjustments (explicit)

1. **It is a toggle, not a scope and not a mode.** `RefScope` lanes
   (All/Chats/Papers/Articles/Docs, `⌘1..⌘5`) partition by *kind* with
   browse sections and ranking; an open-set is an orthogonal,
   usually-tiny (2–6 row) predicate that composes with kind scope + query.
   Implement as `showOpenInHighlightsOnly: Bool` on the model, applied after
   the existing scope filter, with its own footer chip — not as
   `RefScope.open`, which would burn `⌘6`, distort `openCount`, and tangle
   `RefsRanker`'s identical-inputs-identical-order contract.
2. **Enter focuses; it does not re-open.** In the filtered view the default
   open action for a matched row becomes focus-existing
   (`AXRaise` + `NSWorkspace.activate`, falling back to the current
   `openInHighlights` path when focus fails or the row has no window handle).
   Without this the feature is a short launcher, not a tab-switcher, and the
   request fails on its own terms.
3. **Order by Highlights tab order when known, else by panel rank — and say
   which.** In AX mode preserve the window/tab order Highlights reports; in
   fallback mode keep the existing rank order. The footer must label it
   ("in Highlights tab order" vs. "ranked"), or the order will feel arbitrary.
4. **Empty states are first-class, not an afterthought.** The common states —
   Highlights not running, no PDFs open, open PDFs with no matching ref note
   (orphans, non-vault PDFs), Accessibility denied — each need one line + one
   action (see §5.4). A filter that goes blank without explanation will read
   as broken.
5. **No `bob` changes for v1.** Detection + matching are presentation-layer
   (Swift), the join key already ships in `ref list` JSON, and the
   thin-client decision forbids re-implementing vault semantics in the app —
   but it equally forbids pushing Mac-only window state into `bob-cli`.
   A future `bob ref resolve-pdf <path> --format json` helper is reserved for
   the day path normalization (symlinks, case-insensitive APFS, percent
   encoding) proves too hairy for Swift — not for v1.
6. **Accessibility permission must degrade, never block.** Denied/absent
   permission falls back to option 2 with a dismissible banner ("Grant
   access for exact tabs"), never a modal or a dead toggle.

## 5. Design sketch (for the implementer)

### 5.1 New seams (all behind protocols, mirroring `RefsOpening` / `RefsHighlightsLocating`)

- `HighlightsOpenFilesProviding`: `func openPDFs() -> [OpenPDF]` where
  `OpenPDF { url: URL; windowID: CGWindowID?; title: String? }`. Two
  conformances: `AXHighlightsDetector` and `LsofHighlightsDetector`
  (plus `.trackedOnly` composition with the panel's own open MRU).
- Matching: normalize each URL (percent-decode, `resolvingSymlinksInPath`,
  case-fold on APFS) and intersect with in-memory `RefItem`s via the same
  resolution `RefsLibrary.pdfURL(for:)` uses. Unmatched opens feed the
  inspector/footer diagnostic, never the list.
- Refresh: snapshot in `prepareForPresentation()`, re-snapshot on
  `NSWorkspace.didActivateApplicationNotification` for Highlights, plus a 2 s
  poll while the panel is visible. Late snapshots update row content in
  place; only the toggle/query/scope re-rank (same rule as library
  publications today).

### 5.2 Interaction

- Toggle affordance: a footer chip ("● N open in Highlights") that toggles
  the filter on click, plus a free keybinding — `⌘1..⌘5`, `⌘R`, `⌘S`,
  `⌘K`, `Tab` are taken; propose `⌃O` ("open") or `⌘6` with the router's
  existing `scopeIsAll`-style context guard. Auto-enabling the filter when
  the panel is summoned Highlights-frontmost is explicitly *not*
  recommended: surprising, and it fights `prepareForPresentation`'s
  reset-to-All contract.
- Filtered list: no sections (2–6 rows don't need them), search still narrows
  within the open set, kind scope still applies. Rows keep badges, reading
  state, and annotation counts — the metadata is why switching via the panel
  beats Exposé.
- `Return`/`Tab` → focus existing tab (§4.2); `⌘↩` reveal-in-Finder and the
  `⌘K` menu keep current behavior.

### 5.3 Focus implementation notes

- Primary: `AXUIElementPerformAction(window, kAXRaiseAction)` then
  `NSRunningApplication.activate()`. If Highlights uses a single window with
  an internal tab bar, raising is insufficient — the probe (§3.6.2) must also
  check for an `AXTabGroup` and `AXPress` on the tab; budget that discovery
  inside Phase 1, and ship window-raise + activate if tab-press proves
  brittle.
- Fallback (always): current `openInHighlights` re-open path. Verify in the
  focus probe whether re-open duplicates tabs; if it does, say so in the
  footer when running in fallback mode ("opens may duplicate tabs").

### 5.4 States and copy

| state | list shows | action |
|---|---|---|
| Highlights not running | empty-state art + "Highlights isn't running" | "Open Highlights" |
| Running, no PDFs open | "No PDFs open in Highlights" | "Show all" (clear filter) |
| Open PDFs, none match library | "N open PDFs, none in your library" + titles | per-title "Reveal note?" only when a title matches a stem |
| Accessibility denied (AX mode) | banner, list still works via fallback | "Open System Settings" button |
| Stale snapshot (poll failed) | rows + "stale · retrying" chip | auto-retry, as scan does today |

### 5.5 Testing (per repo rules: never land Swift uncompiled)

- Unit-test the pure parts without Apple APIs: URL normalization, open-set ∩
  library intersection (including duplicate stems across `ref_type`s and
  orphan titles), toggle composition with scope + query, footer copy per
  state. Inject fake detectors through the protocol, as `RefsOpening` fakes
  do today.
- AX/`lsof` conformances get contract tests against canned fixtures, not live
  apps; the live probes in §3.6 are the Mac verification, run on the Mac per
  `AGENTS.md` (scratch-copy `bundle.sh` + `typecheck-tests`, never Bryan's
  checkout).
- CI-observable risk: macOS-only target, as with all `BobMacCapture` code —
  flag macOS-target verification status in the final report explicitly.

## 6. Recommended solution (build order)

**Phase 0 — probes (§3.6), half a day on the Mac.** Decides AX-vs-`lsof`,
window-vs-tab focus, and whether re-open duplicates. If `AXDocument` is empty
*and* `lsof` is unusably noisy, stop and re-scope to panel-tracked opens only
rather than building title fuzzy-matching — the rejected option stays
rejected.

**Phase 1 — zero-permission slice (no new entitlement).**
`showOpenInHighlightsOnly` toggle + footer chip + keybinding,
`LsofHighlightsDetector` ∪ panel-open MRU, rank-order listing, focus =
activate + re-open fallback, full empty-state table. Shippable on its own;
validates the interaction before any permission prompt exists.

**Phase 2 — exact mode (only if Phase 0 blesses AX).**
`AXHighlightsDetector`, Accessibility permission copy + Settings toggle +
denied banner, tab-order listing, `AXRaise`/tab-press focus. Falls back to
Phase 1 behavior at every failure point.

**Explicitly not in v1:** MRU ordering, closing/focusing by index, tab counts
as ranking signals, any `bob-cli` change, any Highlights private-format
reading, any Screen Recording permission.

Bottom line: the plan is a good idea — a 2–6-row "what am I reading right
now" view is the highest-leverage small addition to the Refs panel — provided
it ships as a focus-first toggle on exact file identity (AX, `lsof`
fallback), never on window titles, with the empty states designed up front
and the Mac probes run before the code.
