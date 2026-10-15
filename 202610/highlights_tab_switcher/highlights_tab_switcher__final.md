# Bob Refs as a Highlights tab switcher: consolidated report

- **Date:** 2026-10-15
- **Lead:** consolidated from five independent reports (`__cdx`, `__cld`, `__grk`, `__mus`,
  `__gem`) plus the lead's own verification.
- **Question:** Add a mode or filter to Bob Mac Capture's reference panel (Bob Refs) that shows
  only reference notes whose PDFs are open in Highlights, so the panel works as a Highlights tab
  switcher. What is the best way to build it, is it a good idea, and which requirements should
  change?

## 1. Bottom line

- **Build it.** All five researchers agree it is a good idea, and so do I. Highlights' tab bar and
  Window menu show snake_case file names (one tab is literally
  `442a6bf555914893e9891c11519de94f.pdf`). Its own switching is ⌃Tab cycling or a thumbnail grid.
  Bob Refs already knows the title, kind, reading state and annotations for every one of those
  PDFs, and it already has the panel, the search, the inspector and a Highlights opener.
- **Only one detection mechanism works: the macOS Accessibility (AX) API.** Three researchers
  probed the live Mac independently. Highlights had **9 PDFs open and `lsof` showed zero PDF file
  descriptors**. Highlights is not scriptable. AX listed every tab:
  - the window's `AXDocument` gives the visible tab's full file URL;
  - its `AXTabGroup` gives every tab's file name and which one is selected.

  The gem report's headline recommendation, file-descriptor inspection through `libproc`, does
  not work: `lsof` reads the same `libproc` data, and that data showed no PDFs. The mus report's
  `lsof` fallback fails for the same reason.
- **The real cost is permission and signing, not code.**
  - The feature needs the Accessibility permission.
  - Bob Mac Capture is **ad-hoc signed**, and macOS ties an ad-hoc app's Accessibility grant to
    the binary's exact hash. Every `just install` would therefore **silently revoke the grant**,
    while System Settings still shows it switched on.
  - Fix signing first by using one stable self-signed identity (the cld finding, corroborated
    below).
- **Adjusted requirements (§5):**
  - Show **every open Highlights document**, not only those with reference notes.
  - Make it a **"Tabs" filter that combines with the kind scopes**, not a sixth scope.
  - Enter it with its **own key (⇧⌘O) while Highlights is frontmost**; ⌘O stays the library
    picker. ⌘T toggles it inside the panel.
  - **↵ switches to the existing tab**, pins the current tab first and pre-selects the previous
    one.
  - Switches **do not count as opens** in the open log.
- **Recommended solution:** §9.

## 2. Evidence

The Mac facts come from read-only probes the researchers ran over SSH on 2026-10-15: macOS 26.5,
Highlights 2026.1.2 (build 602), bundle id `net.highlightsapp.universal`, 9 tabs in one window.
When I tried to re-probe for this consolidation, the Mac was offline (SSH timed out), so no Mac
fact below is my own measurement. Facts that more than one researcher observed independently are
marked as such.

| # | Fact | Who |
| --- | --- | --- |
| E1 | Highlights is a native AppKit `NSDocument` app. It is **not scriptable**: the vendor FAQ says "No, not yet." It has no `NSAppleScriptEnabled` key and no `.sdef`, and `tell application "Highlights" to get documents` fails with −1728 | cdx, cld, grk |
| E2 | **`lsof -p <Highlights>` shows 0 PDFs** (198–199 entries) while 9 PDFs are open | cdx, cld, grk (independent) |
| E3 | `lsof` on macOS gets its file list from `libproc`, the same calls the gem report proposed (`proc_pidinfo` with `PROC_PIDLISTFDS`), so E2 rules out that approach as well. The gem report gave no measurement for its claim that PDFKit keeps the files open | lead ([Apple DTS forum on lsof's libproc module](https://developer.apple.com/forums/thread/728731)) |
| E4 | AX `AXWindows` returns **1 window**, the visible tab. Its `AXDocument` is the full `file:///Users/…/bob/lib/chat/third_wave_job_applications.pdf`. Its `AXTitle` adds "– Page 5 of 25" | cdx, cld, grk |
| E5 | That window's child **`AXTabGroup` → `AXTabs`** holds all 9 tabs as `AXRadioButton` elements (subrole `AXTabButton`). Each title is the file name, `AXValue` is 1 on the selected tab, and each tab advertises `AXPress`. **Tabs have no `AXDocument` or `AXURL`**. `AXTabs` on the window itself fails with error −25205 | cdx, cld, grk |
| E6 | The app's `AXChildren` include no hidden tab windows. `CGWindowListCopyWindowInfo` shows 9 windows with identical frames, so each tab is its own `NSWindow`, but window names are nil without the Screen Recording permission | cld, grk |
| E7 | An independent 2019 Apple forum report confirms the background-tab limit: a tabbed document's `AXDocument` cannot be read, "only the label of the tab". The same report says window handles kept from earlier stay valid after the window is covered | lead ([Apple forum 121114](https://developer.apple.com/forums/thread/121114)) |
| E8 | The full AX read took **67 ms** from a cold `swift` script. Warm structural reads took about **1 ms** after a 28 ms first run | cld, cdx |
| E9 | AX reads Highlights' windows **while Highlights is not frontmost** (Chrome was frontmost) | grk |
| E10 | **`open -a Highlights <already-open background PDF>` selected the existing tab.** It created no duplicate, the window count stayed 1, and the reading page stayed where it was. Afterwards the probe restored the tab Bryan had been on | grk (the only researcher who changed live state, then restored it) |
| E11 | File → Open Recent is a **different set** from the open tabs: it contained 3 PDFs that were not open | grk |
| E12 | Library: 1,033 notes, **431 with a PDF**, **430 distinct file names**. The only collision is `harness_engineering.pdf` (`lib/papers/` and `lib/blogs/`). **All 9 open tabs map to exactly one note each.** By state: 7 queued and 2 finished | cdx, cld, grk (independent) |
| E13 | Bob Mac Capture is **ad-hoc signed**. Its designated requirement is the `cdhash`, and the keychain holds **0 code-signing identities**. `just install` defaults to `identity="-"`, and `BundleSigningInspector` warns only about notifications | cld; lead confirmed `justfile`, `bundle.sh` and the inspector in source |
| E14 | Ad-hoc grants break on rebuild: "each rebuild-and-replace silently revoked the permission while the app stayed listed and ticked". A real certificate kept the grant through 6 rebuild cycles | lead/cld ([shannoncoat 0.0.8](https://git.bdeshi.space/bdeshi/shannoncoat/src/tag/0.0.8), [OpenClaw signing docs](https://cdn.jsdelivr.net/npm/openclaw@2026.7.1-2/docs/platforms/mac/signing.md)) |
| E15 | The app is **not sandboxed** and uses no AX API today. Carbon hotkeys need no permission | cld, grk |
| E16 | Open log: **122 opens over 7 days, 14 of them same-day repeats**. One open tab had been opened 4 times | cld |
| E17 | Both hotkeys run the same handler (`case .refs, .refsHighlightsOpen: toggleRefs()`), and `prepareForPresentation()` resets `query` and `scope = .all`. `HotKeyAction` uses ids 1–3 | grk, cdx; lead verified |
| E18 | The panel's key router binds ⌘1–⌘5, ⌘R, ⌘S, ⌘K and ⌘Y. **⌘T, ⌘6 and ⌘0 are free.** In Highlights' menus, **⇧⌘O, ⌘E and ⌘T are free** | lead (router source); cld (Highlights menu keys) |
| E19 | The search bar already prints `"\(openCount) open · \(totalCount)"`, where "open" means the Ready/Next/Reading lanes | cdx, cld, grk; lead verified |
| E20 | The global Refs hotkey is **⌃⇧⌘O** (README). The cld report's "⌃⇧⌘R" is Capture's rollback hotkey. The takeover key is ⌘O, ⌃O or Off | lead (README, `RefsHighlightsOpenKey.swift`) |
| E21 | ↵ on Highlights and default-app opens appends to `refs-open-log.json`. That log feeds frecency (weight 0.25) and the "Recently opened" browse section | lead (README "Sorting") |

**Still unverified.** No one tested these against the live session:

- `AXPress` actually switching a tab;
- windows on other Spaces or in full screen;
- several Highlights windows;
- a tab whose file extension is hidden;
- whether a kept window handle still returns `AXDocument` after its tab goes to the background;
- which AX notifications fire when the user switches tabs.

## 3. Where the reports disagreed, and how I resolved each point

| Question | Positions | Resolution |
| --- | --- | --- |
| How to detect open PDFs | AX (cdx, cld, grk). AX with an `lsof` fallback (mus). `libproc`, with AX dismissed as "fatal friction" (gem) | **AX only.** E2 and E3 rule out both file-descriptor routes. The permission is one-time once signing is stable (E14). The mus "zero-permission first slice" has no working mechanism, so it is dropped |
| How ↵ switches | `NSWorkspace.open` (cld, grk, gem). `AXPress` on the tab, never reopen (cdx). `AXRaise` plus activate, with reopen as fallback (mus) | **A hybrid.** Library-matched rows use the existing `openInHighlights`, which grk saw switch tabs and keep the page (E10). It also activates Highlights, already has error handling, and simply reopens a tab that was closed in the meantime. **`AXPress`** is used only for rows that have no single library path (unmatched files and name collisions) |
| What shape the feature takes | A `RefScope.tabs` scope token (cld). A filter that combines with the kind scopes (grk, mus, gem, cdx) | **A filter flag that combines with the kind scopes**, shown as a token like a scope. "Open in Highlights" is runtime state, not a kind. ⌘3 inside Tabs is free to support |
| How you enter it | ⌘O in Highlights opens Tabs by default (grk; gem when ≥1 tab is open). A dedicated ⇧⌘O key (cld). Explicit toggle only (mus). Remember the mode across shows (cdx) | **A dedicated ⇧⌘O while Highlights is frontmost, plus ⌘T in the panel. ⌘O is unchanged and nothing persists.** E16 shows most ⌘O presses open something new, so defaulting ⌘O to Tabs would tax the main use. Two chords for two intents avoids hidden mode state |
| Open PDFs with no note | Show them (cdx, cld, grk). Hide them or move them to a diagnostic (mus, gem) | **Show them**, dimmed and titled by file name; ↵ uses `AXPress`. A switcher that hides tabs cannot be trusted. Today there are 0 such rows, so the cost is small |
| Trust in file-name matches | Tentative until confirmed by path (cdx). A unique match counts (cld, grk) | **A unique file name inside the library counts as a match. A collision never does.** The library has 1 collision in 431 (E12), and the visible tab always resolves by full path (E4). The mismatch cdx feared (an outside PDF with a vault file name) is rare, visible and harmless: ↵ opens the vault copy in a new tab |
| Row order | Tab-bar order (grk, cdx, mus). Current first, then most recent, with the previous tab pre-selected (cld) | **cld's ⌘Tab-style order** (§6.3). It is the one ordering that makes ⇧⌘O ↵ do something tab-bar order cannot |
| Keeping the list fresh | Poll every 1 s (grk) or 2 s (mus). Snapshot on show (cdx, cld) | **Snapshot on show, on ⌘T and on ⌘R; no polling.** The panel is up for seconds and holds the keyboard, and a stale target is handled at ↵ |
| Zero matching tabs | Fall back to the library automatically (gem). Show an explicit empty state (others) | **Explicit empty state.** With a dedicated key, a silent fallback would be confusing |
| Counting switches in the open log | Yes, a switch is a use (cld). Not discussed by the others | **No (lead).** Switching among nine tabs many times a day would swamp frecency and "Recently opened" (E21). Tabs ordering keeps its own in-memory recency |
| Signing | Raised only by cld | **Adopted as a prerequisite** (E13, E14) |

## 4. Critique: is this a good idea?

**Yes.** Four things make it worthwhile:

- **The pain is real.** Tab labels are file stems (one is a hash), nine tabs is already past
  comfortable ⌃Tab cycling, and Bryan already re-opens notes from Bob Refs to get back to them
  (E16).
- **Most of it exists already.** The snapshot already carries `pdfPath`. The panel already has
  search tiers, stable selection, the inspector, the Copy card, the takeover hotkey and an opener
  that switches tabs (E10).
- **It respects the architecture.** Which PDFs Highlights has open is macOS UI state that `bob`
  cannot see. `decisions:mac-capture-is-a-thin-client` lets the app "filter or rank what `bob`
  returned", so a Mac-side reader that filters the snapshot fits that rule. **bob-cli needs no
  change.**
- **It does more than switch.** Knowing the current PDF puts "act on what I'm reading" one key
  away: the inspector, ⌘Y copy (marker ID, wiki link, highlights) and ⌘↵ for its note. Today
  Bryan has to search for a PDF he is already looking at.

**Costs and risks, each mitigated in §6:**

1. **The Accessibility permission is powerful.** It lets the app read and drive any app's UI, and
   the code is largely agent-written. Keep all AX use inside one small reader type that targets
   only Highlights' process and only reads or presses tab buttons. Treat any new AX call site as a
   review flag.
2. **Ad-hoc signing revokes the grant on every install** (E13, E14). This is the biggest practical
   risk: the feature would "randomly" stop working after most installs.
3. **Background tabs expose only file names** (E5, E7). This is acceptable with 1 collision in 431
   PDFs, given honest handling of collisions and unmatched files.
4. **AX coverage has gaps.** Other Spaces, full-screen windows and several windows are untested.
   In the main use case Highlights is frontmost, so its window is on the current Space.
5. **Highlights could change its UI.** The tab bar is AppKit's native one, so the risk is low.
   Matching by role rather than by English menu titles keeps it independent of localization.

**What would make it a bad idea:**

- building it as a new `bob` command or vault field (`bob` cannot see Highlights);
- using Screen Recording, Apple Events or `lsof`;
- building a separate switcher app or panel;
- shipping without the signing fix.

**Alternatives considered and rejected:**

| Alternative | Why not |
| --- | --- |
| Highlights' ⌃Tab, Show All Tabs or Window menu | File names, no search, no Bob metadata. This is the pain itself |
| Filter on the Bob open log | Records only opens made through Bob, sees no closes, and so misses opens from Finder or restored tabs |
| Open Recent, saved app state, Spotlight last-used date | Different sets from what is open (E11). Undocumented or protected formats |
| `CGWindowList` titles | Need Screen Recording, which re-prompts. One title per window, not per tab |
| System Events / AppleScript UI scripting | The same AX tree plus a second (Automation) permission |
| Private `_AXUIElementCreateWithRemoteToken` enumeration of hidden tab windows | Would give every tab's exact path, but it is a private API. Keep it in reserve only in case file-name collisions start to matter |
| A separate switcher window, or Raycast, Alfred or Hammerspoon | Duplicates the hotkey, opener and ranking, and still needs Bob's metadata. Capture already moved off Hammerspoon |
| An "In Highlights" browse section inside the normal library view | Pushes the reading queue down on every show. The open-tab glyph in §6.3 delivers that value more cheaply |

## 5. Requirement adjustments (explicit)

| # | As requested | Adjusted | Why |
| --- | --- | --- | --- |
| A1 | "Only reference notes whose PDFs are open" | **Every open Highlights document.** Matched notes render as normal rows. Unmatched files render as dim rows titled by file name and marked "Not in your library" | A switcher that silently omits tabs is incomplete. Outside PDFs (CVs, Downloads, intake before a scan) will happen |
| A2 | "Special mode / filter" | A **Tabs filter flag that combines with the kind scopes**, shown as a token in the search bar. ⌫ or Esc on an empty query removes it first, as with scope tokens. ⌘1–⌘5 still narrow inside it | Kind and runtime state are different axes (§3) |
| A3 | (entry point unstated) | **⇧⌘O while Highlights is frontmost** opens the panel in Tabs mode (configurable: ⇧⌘O, ⌘E or Off). **⌘T** toggles the mode inside the panel. **⌘O and the global ⌃⇧⌘O are unchanged** and open the library. Nothing persists between shows | Keeps the main ⌘O flow fast (E16). The filter is reachable from both entry points |
| A4 | "Tab switcher" | ↵ **switches to the existing tab** (§6.4). It never jumps pages (no `highlights://…#page=`), never changes reading state, lanes or the vault, and never runs a scan or creates a note | Existing rule R8 (opening is retrieval) plus switcher semantics |
| A5 | (order unstated) | **The current tab is first**, labelled "Current · p. 5/25". The rest follow **most recently active first**, then tab-bar order, with unmatched files last. If Highlights is frontmost, **row 2 is pre-selected**, so ⇧⌘O ↵ flips back like ⌘Tab; otherwise row 1 is | Gives the switcher a one-key "back" gesture. The current row stays because ⌘Y and ⌘↵ on it are useful |
| A6 | (naming) | Call it **Tabs**. The count reads "9 tabs" or "2 of 9 tabs", **never "open"**. The section header is "In Highlights" | "N open" already means reading lanes (E19). If confusion remains, rename that label later |
| A7 | (new prerequisite) | **Sign Bob Mac Capture with a stable self-signed identity before shipping Tabs** | E13, E14 |
| A8 | (permission) | **Ask lazily:** an in-panel card the first time Bryan enters Tabs, never at launch. Without the grant, library mode is unaffected | Bryan only meets a prompt when he asks for the feature |
| A9 | (freshness) | Take a snapshot on show, ⌘T and ⌘R, with no background polling. Detect a stale target at ↵ time | §3 |
| A10 | (new) | **Tabs-mode switches are not appended to `refs-open-log.json`** | Keeps the open log's meaning, which drives frecency and "Recently opened" (E21) |
| A11 | (non-goals) | No closing, reordering or moving tabs. No Screen Recording, Apple Events or private APIs. No bob-cli change. No persisted Highlights state. No page numbers for background tabs | Keeps AX use mostly read-only and the scope small |
| A12 | (optional, after v1) | A small "open in Highlights" glyph on library rows in every scope (only when the permission is granted) | Answers "is this already open?" at almost no cost |

## 6. Design

### 6.1 Reader (`BobMacCapture` target, AppKit + ApplicationServices)

Use a `HighlightsTabsReading` protocol, injected like `RefsOpening`, with a fake in tests. The
live `AXHighlightsTabsReader`:

1. Resolves the Highlights process ID from the resolved bundle id (`HighlightsLocator`, honouring
   the Settings override). **It never launches Highlights.**
2. Checks `AXIsProcessTrusted()` without prompting. It prompts only from the explicit button on
   the permission card.
3. Calls `AXUIElementCreateApplication(pid)` with a small messaging timeout (about 0.4 s; the
   default is several seconds) and an overall time budget. It runs off the main actor, on one
   serial queue that owns all AX objects.
4. For each element in `AXWindows`:
   - read `AXDocument` (the visible tab's file URL) and `AXTitle` (for the page caption);
   - search the immediate children, to a bounded depth, for the `AXTabGroup` and read its
     `AXTabs` (title, `AXValue`).
   - A window with no tab group is a single-document window: it yields one tab whose name comes
     from `AXDocument`.

   Never walk into PDF content nodes.
5. Returns `.notRunning`, `.notTrusted`, `.failed(reason)`, or
   `.snapshot(HighlightsTabsSnapshot)`. The snapshot carries a generation number, so an older
   asynchronous result can never replace a newer one.
6. Keeps snapshots in memory only. Tab names never go into logs, signposts or disk.

The snapshot is a Foundation-only value type in `RefsCore`:
`windows[] { isMain, pageCaption?, tabs[] { fileName, documentPath?, isSelected } }`.

**Never** cycle through tabs to collect their paths. That would steal the front document.

### 6.2 Matcher (`RefsCore`, pure, testable on Linux)

`HighlightsTabMatcher.match(snapshot, items, vaultRoot) -> [RefsOpenTab]` applies these rules in
order:

1. **Full path.** For a tab with a `documentPath`, standardize and percent-decode it, resolve
   symlinks, strip the vault root, and compare it with `item.pdfPath`. This always resolves the
   visible tab.
2. **Unique file name.** Compare the tab title, accepting both `stem.pdf` and `stem` in case the
   extension is hidden, with any trailing page suffix removed defensively, against the last path
   component of `pdfPath`. A single hit is a match (`match = .fileName`).
3. **Collision** (today only `harness_engineering.pdf`). Emit one row that still shows the file
   name as its title, with the candidate notes listed as secondary text. ↵ uses `AXPress`. Note
   actions (⌘↵, ⌘Y) require choosing a candidate. Never guess from the open log.
4. **No hit.** Emit an unmatched row (`itemID = nil`).

Each `RefsOpenTab` carries `itemID?`, `fileName`, `windowOrdinal`, `isCurrent`, `pageCaption?`
and `match ∈ {path, fileName, collision, none}`. Never use a tab's index as its identity.

### 6.3 Panel model and listing

- **State.** `RefsPanelModel` gains `tabsFilter: Bool` and a presentation source:
  - Split `case .refs, .refsHighlightsOpen` in `AppDelegate` so the new
    `HotKeyAction.refsHighlightsTabs = 4` can call `showRefs(source: .highlightsTabs)`.
  - `prepareForPresentation(source:)` sets `tabsFilter`.
- **Listing.** When `tabsFilter` is on, skip `browseSections`. Show one "In Highlights" section in
  the A5 order. A typed query runs the existing tiered ranker restricted to the tab set; tier rules
  and tie-breaks are unchanged.
  - Recency is an in-memory map from file name to time. It is sampled from the current tab on
    every panel show, on every switch Bob dispatches, and when Highlights deactivates
    (`HighlightsTakeover` already observes that).
  - The existing rule "rows never move under the cursor" still applies to late library refreshes.
    A new tab snapshot (⌘R or ⌘T) may re-rank, because the set of rows itself changed; it keeps
    `selectedID` when that row still exists.
- **Rows.**
  - The current tab gets a "Current · p. N/M" pill.
  - Unmatched and collision rows have a minimal inspector card ("Not in your library" or "Matches
    2 notes").
  - The footer reads "↵ Switch".
  - VoiceOver appends ", open in Highlights".
- **Search bar.** Shows a "Tabs" token, and the count reads "9 tabs" or "k of 9 tabs".

### 6.4 Switching

- **A row matched by path or unique file name:** the existing `openInHighlights(item)`, but
  skipping `recordOpen` (A10). LaunchServices hands the URL to Highlights. Highlights'
  `NSDocumentController` finds the open document and brings its tab forward with the page kept
  (E10). If the tab closed in the meantime, the PDF reopens, which is acceptable.
- **A collision or unmatched row:**
  - On ↵, find the tab again in a fresh snapshot by window and title, then call `AXPress` on its
    `AXTabButton`, activate Highlights, and raise the window.
  - If it is gone, show the existing banner style: "That tab was closed".
  - Never press whatever tab moved into its old position.
- **Optional check:** after a switch, a cheap re-read can confirm that the front window's
  `AXDocument` changed as expected. Log a mismatch; do not retry in a loop.

### 6.5 Keys

| Key | Where | Action |
| --- | --- | --- |
| **⇧⌘O** (configurable: ⇧⌘O, ⌘E or Off) | While Highlights or the override app is frontmost | Show Bob Refs in Tabs mode. With the panel open, switch to Tabs, or close the panel if it is already in Tabs |
| ⌘O / ⌃O (unchanged) | While Highlights is frontmost | Show Bob Refs in All |
| ⌃⇧⌘O (unchanged) | Global | Show Bob Refs in All |
| **⌘T** | In the panel | Toggle Tabs on or off. A letter suits it better than ⌘6, which would read as a sixth kind |
| ↵, Tab, double-click | Tabs mode | Switch (§6.4) |
| ⌘↵, ⌘Y, ⌘K, ⌥↵ | Tabs mode, matched rows | Unchanged |

### 6.6 States

| State | Tabs mode shows |
| --- | --- |
| Accessibility not granted, or a stale ad-hoc grant | A card: "Bob Refs needs Accessibility access to see Highlights' tabs." Buttons: **Open Accessibility Settings** (prompting variant) and **Show library** (⌘T). On ad-hoc builds it adds: "Grants reset when an ad-hoc build is reinstalled. Re-add the app, or run `tccutil reset Accessibility org.bobs.bob-mac-capture`." |
| Highlights not running | "Highlights isn't running." ⌘T returns to the library |
| Running with no documents | "No documents are open in Highlights." |
| The AX read failed or timed out | The last snapshot, dimmed, with "Couldn't read Highlights' tabs · ⌘R to retry" |
| A tab closed before ↵ | Matched rows reopen the PDF. Unmatched rows show the banner |

Settings › References gains two items:

- the tabs-key picker;
- a "Highlights tabs: Allowed / Not allowed" row next to the resolved-Highlights row.

`BundleSigningInspector`'s ad-hoc warning should mention Accessibility as well as notifications.

### 6.7 Signing (prerequisite)

1. On the Mac, create one long-lived self-signed code-signing certificate in the login keychain,
   e.g. "Bob Mac Capture Local". Use Keychain Access › Certificate Assistant, type Code Signing.
2. Make `just install` default to that identity when it exists. If it does not, fall back to `-`
   with a loud warning. `bundle.sh` already accepts `--identity`.
3. Check that `codesign -d -r-` now shows a certificate-leaf requirement, not a `cdhash`.
   Reinstall twice and confirm `AXIsProcessTrusted()` stays true.
4. Document this in the README. Side benefit: it also fixes the notification-permission drift the
   inspector already warns about.
5. Agent hosts build scratch copies and never install, so they are unaffected.

### 6.8 Tests and verification

- **`RefsCore` golden tests**, run with `just portable-check` on Linux:
  - today's real 9-tab snapshot (all matched);
  - a `harness_engineering.pdf` collision;
  - an unmatched `~/Downloads` PDF;
  - a hidden extension;
  - a single window without a tab bar;
  - two windows;
  - an empty snapshot;
  - A5 ordering and pre-selection;
  - snapshot generations;
  - the stale-target rule.
- **Optional tuning hook:** add `refs-rank --tabs snapshot.json`.
- **macOS target**, following the repo's `AGENTS.md`:
  - compile with the fake reader, using a scratch-copy `bundle.sh` and `just typecheck-tests` on
    the Mac;
  - do not run `just install` in Bryan's checkout.
- **Manual GUI smoke test after signing:**
  - the permission card;
  - a switch from Highlights frontmost and from Obsidian;
  - a tab closed under the panel;
  - Highlights quit and relaunched;
  - IME, Esc and the retained Capture draft still behave.

## 7. Open questions and spikes (about 1 hour on the Mac, in a test session)

Run these with fixture PDFs, not Bryan's live reading session.

1. **`AXPress` switching:** does pressing an `AXTabButton` select the tab when Highlights is
   frontmost, and when it is in the background (after activation)? This is the only switch
   behaviour no one observed. Only unmatched and collision rows depend on it.
2. **Coalescing, repeated:** run `open -a Highlights <background PDF>` (E10) with two windows, and
   for a PDF whose tab was dragged into a separate window.
3. **Spaces, full screen and minimized windows:** does `AXWindows` list them? If not, document the
   limit; the private remote-token enumeration stays in reserve.
4. **Kept window handles (lead idea, untested):** each tab is its own `NSWindow` (E6), and handles
   reportedly stay valid (E7). If a window handle kept while its tab was visible still returns
   `AXDocument` after the tab goes to the background, the reader can learn **exact paths for every
   tab Bryan has visited** while Bob was running, using only public API. That would remove
   file-name ambiguity over time. Worth 15 minutes; not required for v1.
5. **Recency notifications:** does `kAXMainWindowChangedNotification` or
   `kAXFocusedWindowChangedNotification` fire when a tab is selected? If so, an `AXObserver` can
   replace sampled recency in phase 3.

## 8. Optional follow-ups (Bryan's call; no beads filed)

- **Unique PDF file names in `lib/`.** Today only `harness_engineering.pdf` collides. bob-cli
  already treats a bare stem as ambiguous when it collides, but it does not prevent the collision
  at intake. Renaming one copy, or adding an intake guard, would make file-name matching exact by
  construction. It would also remove the stem ambiguity of `highlights://<stem>` deep links.
- **Decision record.** If Tabs ships, record that "Bob Mac Capture reads Highlights' UI through
  Accessibility and only selects tabs, never edits documents", so future agents do not widen AX
  use casually. Use `/sase_memory_write` if you adopt it.

## 9. Recommended solution

**Ship a "Tabs" filter in Bob Refs:**

- backed by a small, Highlights-only Accessibility reader of window `AXDocument` and native
  tab-bar titles;
- matched in `RefsCore` against the existing `bob ref list` snapshot;
- switching through the existing Highlights opener;
- after moving Bob Mac Capture to a stable signing identity.

No bob-cli change.

**Phase 0: stable signing (about 1 hour, Mac).**

- Create the self-signed identity.
- Default `just install` to it, with an ad-hoc fallback and a warning.
- Update the README and the `BundleSigningInspector` text.
- Verify the grant survives two reinstalls.

**Phase 1: spikes (about 1 hour, Mac test session).**

- Run §7 items 1–3, plus item 4 if time allows.
- Record the results in the implementation plan.

**Phase 2: `RefsCore`, pure.**

- Add the snapshot value, `HighlightsTabMatcher` (full path, then unique file name, then
  collision, then none) and the `tabsFilter` listing branch.
- Order the rows current first, then most recent, then tab-bar order, then unmatched, and add the
  pre-selection rule.
- Add the golden tests.

**Phase 3: `BobMacCapture`.**

- **Reader:** `AXHighlightsTabsReader` (off the main actor, with timeouts and generations).
- **Keys:** ⇧⌘O as `HotKeyAction.refsHighlightsTabs = 4`, registered only while Highlights is
  frontmost, and ⌘T in the panel.
- **Panel:** the Tabs token, the "N tabs" count, the current-tab pill, dim unmatched rows, and
  `AXPress` for unmatched and collision rows.
- **Permission:** the lazy permission card, the states table, and the Settings rows.
- **Open log:** switches skip `recordOpen`.
- **README:** a Tabs subsection.

**Later, only if wanted after use:**

- the open-tab glyph in every scope (A12);
- an `AXObserver` for exact recency;
- exact background paths through kept window handles, if spike 4 works;
- ⌘W to close a tab, behind a separate review.

**Why this over the alternatives:**

- It is the only mechanism measured to see every tab (E5) without Screen Recording.
- The parts that are hard to get right (matching, ordering, selection) are pure and testable on
  Linux.
- Switching uses a path already seen to switch tabs and keep the page (E10).
- The one real cost, the permission, is paid once because signing makes it stick.
- The dedicated ⇧⌘O keeps ⌘O fast for opening something new, and gives the "back to my other PDF"
  flip that Highlights' tab bar cannot.

**If you want to keep the original scope** (only notes, no unmatched rows, a plain filter): keep
the same reader, matcher and signing work, drop A1 and A5, and show the coverage in the count,
e.g. "7 tabs · 2 not in library", so the filter never looks complete when it is not.

## Sources

- **Swarm reports** (now under this directory):
  - `__cdx`: AX tree details, observer registration, identity-confidence policy;
  - `__cld`: signing and TCC, ⌘Tab-style ordering, Highlights menu keys, open-log analysis;
  - `__grk`: the coalescing test, Open Recent ≠ open tabs, the 9-tab mapping, the split of the
    takeover hotkey;
  - `__mus`: the combinable toggle, the empty-state table, the probe plan;
  - `__gem`: the escape and peel UX, the open glyph in browse mode. Its `libproc` detection is
    refuted by E2 and E3.
- **Prior research:**
  `research:202610/highlights_quick_open_refs_panel/highlights_quick_open_refs_panel__final.md`
  (Bob Refs design rules, R8 "opening never changes reading state", `highlights://` stem
  ambiguity).
- **Decision:** `decisions:mac-capture-is-a-thin-client`.
- **`bob-mac-capture` at `9f58448`**, verified by the lead:
  - `Sources/BobMacCapture/Refs/RefsKeyRouter.swift` (bound and free keys);
  - `RefsPanelModel.prepareForPresentation`;
  - `AppDelegate.swift:145` (shared hotkey case);
  - `HotKeyRegistry.swift` (`HotKeyAction` 1–3);
  - `RefsSearchBar.swift:158` (the "open" count);
  - `justfile` and `Scripts/bundle.sh` (`identity="-"` default);
  - `BundleSigningInspector.swift`;
  - `README.md` (global ⌃⇧⌘O, open-log and Sorting rules).
- **`bob-cli` at `f732097c`:** `src/native/ref_tasks/tests.rs` (a bare stem resolves only when it
  is unique).
- **Web:**
  - [Highlights FAQ](https://highlightsapp.net/faq/) ("Is Highlights scriptable? No, not yet.");
  - [Highlights Mac changelog](https://highlightsapp.net/changelog/mac/);
  - [Apple forum 121114: `kAXDocumentAttribute` of tabbed documents](https://developer.apple.com/forums/thread/121114);
  - [Apple forum 728731: lsof's libproc module](https://developer.apple.com/forums/thread/728731);
  - [shannoncoat 0.0.8: stable code identity keeps Accessibility](https://git.bdeshi.space/bdeshi/shannoncoat/src/tag/0.0.8);
  - [OpenClaw macOS signing docs](https://cdn.jsdelivr.net/npm/openclaw@2026.7.1-2/docs/platforms/mac/signing.md);
  - [Apple: AXUIElementSetMessagingTimeout](https://developer.apple.com/documentation/applicationservices/1459345-axuielementsetmessagingtimeout);
  - [Apple: kAXDocumentAttribute](https://developer.apple.com/documentation/applicationservices/kaxdocumentattribute);
  - [AltTab features (other Spaces through private API)](https://alt-tab.app/features).
