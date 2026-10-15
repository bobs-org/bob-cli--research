# Bob Refs as a Highlights tab switcher: a "Tabs" scope for the refs panel

- **Date:** 2026-10-15
- **Researcher:** cld, one of a five-researcher swarm (`__cdx`, `__grk`, `__mus`, `__gem`, `__cld`)
- **Question:** Add a mode or filter to Bob Mac Capture's reference panel (Bob Refs) that shows
  only the reference notes whose PDFs are open in Highlights, so the panel can work as a tab
  switcher for Highlights. What is the best way to build it? Is it a good idea? What should
  change?
- **Method:** I read the `bob-mac-capture` sources and README, plus the consolidated research
  that designed Bob Refs (`research:202610/highlights_quick_open_refs_panel/highlights_quick_open_refs_panel__final.md`).
  I ran live, read-only probes over SSH on the Mac, where Highlights was running with 9 PDFs
  open. I also ran `bob ref list -R all -A -f json` on apollo and did a few web searches. On the
  Mac I only read data: I opened, switched or closed nothing in Highlights, and changed no
  settings.

## 1. Bottom line

- **Build it. It is a good idea, and it is cheap apart from one cost.** Highlights' tab bar
  shows file names: snake_case stems, plus one tab named `442a6bf555914893e9891c11519de94f.pdf`
  for the reference Bob calls *karpathy/llm-wiki.md*. Native switching is linear (⌃Tab) or a
  thumbnail grid (⇧⌘\). Bryan already uses Bob Refs as a rough tab switcher: the open log on the
  Mac has **14 same-day repeat opens out of 122 opens in the last 7 days**. A dedicated mode
  turns that habit into a fast, complete switcher with Bob's titles, kinds, states and inspector.
- **The detection mechanism is settled by experiment: use the macOS Accessibility (AX) API.**
  - `lsof` shows **zero** PDF file handles in Highlights while 9 documents are open, because
    PDFKit reads each file and closes it. File-descriptor approaches are therefore ruled out.
  - Highlights has no AppleScript dictionary.
  - AX works well. Highlights' window reports the **full file URL** of the visible tab
    (`AXDocument`). Its native tab bar (an `AXTabGroup`) lists **every tab's file name**, with
    `AXValue = 1` on the selected one. The whole read took **67 ms**, measured from a cold
    `swift` script.
- **All 9 open tabs map to exactly one library row each by file name.** The library has 431
  PDF-backed notes and 430 distinct PDF file names; only `harness_engineering.pdf` occurs twice
  (in `lib/papers/` and `lib/blogs/`). Matching by file name is therefore reliable, with a
  simple rule for the rare collision.
- **The real cost is permission plus signing, not code.**
  - The app needs the Accessibility permission.
  - Bob Mac Capture is **ad-hoc signed**. On the Mac its designated requirement is
    `cdhash H"0c1f…"`, and there are **0 code-signing identities** in the keychain. macOS ties an
    ad-hoc app's Accessibility grant to that exact hash, so **every `just install` silently
    revokes the grant**, even though System Settings still shows it switched on. The app was last
    reinstalled today at 16:28, and the repo saw up to 74 commits a day this month.
  - **Fix signing first**: sign with one stable self-signed identity. Otherwise the feature will
    break after every reinstall.
- **Adjusted requirements** (called out in §5):
  - Make it a **"Tabs" scope token** (⌘T in the panel, plus an optional **⇧⌘O** key while
    Highlights is frontmost), not a separate mode.
  - Order rows **current tab first, then most recently used**, with the *previous* tab selected,
    so ↵ flips back like ⌘Tab.
  - Switch through the **existing ↵ open path**; nothing new is needed for library rows.
  - **Also list open PDFs that have no reference note**, dimmed, so the switcher is complete.
  - **Mark already-open rows in every scope.**
  - Never change reading state.
- **Recommended solution:** §9.

## 2. Facts the recommendation rests on

All Mac facts were measured on 2026-10-15 between 16:30 and 16:45 local time, read-only.

| # | Fact | How checked |
| --- | --- | --- |
| F1 | Highlights 2026.1.2 (build 602), `net.highlightsapp.universal`. It is a **native AppKit NSDocument app** (`NSPrincipalClass = NSApplication`, `NSDocumentClass = Highlights.Document`, `Main` storyboard), not Catalyst | `plutil -p Info.plist` |
| F2 | **No AppleScript support**: `Info.plist` has no `NSAppleScriptEnabled` and no `OSAScriptingDefinition`. Highlights is also absent from community lists of scriptable apps | `plutil`; web search |
| F3 | The system tab preference is `AppleWindowTabbingMode = always` ("Prefer tabs when opening documents: Always") | `defaults read -g` |
| F4 | `CGWindowListCopyWindowInfo` shows **9 Highlights document windows with identical frames, only one on screen**. That is the native-tab signature: each tab is its own `NSWindow` | JXA probe (window names hidden without Screen Recording) |
| F5 | **`lsof -p <Highlights>` lists no PDFs at all** (199 descriptors, none under `~/bob`) while 9 documents are open | `lsof` |
| F6 | **AX `AXWindows` returns 1 window**, the visible tab only. Its `AXDocument` is `file:///Users/bbugyi/bob/lib/chat/third_wave_job_applications.pdf`, and its `AXTitle` is `third_wave_job_applications.pdf – Page 5 of 25` | Swift AX probe |
| F7 | That window's **`AXTabGroup` lists all 9 tabs** as `AXRadioButton`s. Each title is the file name with `.pdf`, `AXValue` is 1 on the selected tab and 0 elsewhere, and **tabs carry no `AXDocument`** | Swift AX probe |
| F8 | The app's `AXChildren` are `[AXWindow, AXMenuBar, AXFunctionRowTopLevelElement]`, so hidden tab windows are not reachable through public AX | Swift AX probe |
| F9 | The full AX read (app lookup, windows, tab group, 9 tabs) took **67 ms** from a cold `swift` script | Probe timing |
| F10 | `bob ref list`: **1,033 notes, 431 PDF-backed, 430 distinct PDF file names**. The only collision is `harness_engineering.pdf` (`lib/papers/`, `lib/blogs/`). No PDF is shared by two notes | Python over the JSON on apollo |
| F11 | **All 9 open tabs map to exactly one note each.** By state: 7 queued/Ready, 2 finished/Read, **0 "started"**. Highlights' open set is a working-set signal that Bob's lanes do not capture | Same |
| F12 | The tab bar shows `442a6bf555914893e9891c11519de94f.pdf`; Bob titles that note *karpathy/llm-wiki.md*. Others read `docs_backed_memory_and_agent_maintained_docs.pdf` and similar | F7 + F10 |
| F13 | Highlights' menu: **⌘O** Open… (Bob Refs already takes it over), **⌃Tab / ⌃⇧Tab** Next/Previous Tab, **⇧⌘\\** Show All Tabs, ⌘0–⌘5 view modes, ⌘I metadata, ⌥⌘T Hide Toolbar. **⇧⌘O, ⌘E, ⌘T, ⌘G, ⌘J, ⌘L are free** | AX read of menu-bar key equivalents |
| F14 | Bob Mac Capture is **ad-hoc signed**: `Signature=adhoc`, `designated => cdhash H"0c1f6124…"`. `security find-identity -p codesigning` finds **0 valid identities**. `just install` defaults to `identity="-"` | `codesign -dv`, `codesign -d -r-` |
| F15 | The app is **not sandboxed** (no entitlements file, so AX client calls are allowed) and **uses no AX API today**. Its Carbon hotkeys need no permission | `Scripts/bundle.sh`, grep |
| F16 | The installed app was rebuilt today at 16:28. The repo had 2–74 commits a day over the past two weeks | `stat`, `git log` |
| F17 | Open log: **122 opens over 7 days (about 17 a day), 93 distinct notes, 14 same-day repeat opens of the same note**. `second_wave_job_applications`, open right now, was opened 4 times | `refs-open-log.json` (counts only) |
| F18 | The takeover key is at its default (**⌘O**); no refs keys are overridden in `defaults` | `defaults read org.bobs.bob-mac-capture` |
| F19 | The search bar's count already uses "open" for the open *lanes*: `"\(openCount) open · \(totalCount)"`. A mode called "Open" would collide with it | `RefsSearchBar.swift:158` |
| F20 | `RefScope` (`RefsModel.swift:177`) is kind-only (`contains(_ kind:)`). `RefsRanker.listing` filters with `scope.contains($0.kind)`. `RefsSignals` already carries per-item side data (`today`, `opens`, `missingPDFs`, `scan`…) | Source |
| F21 | ↵ already opens through `NSWorkspace.open([pdf], withApplicationAt: Highlights, activates: true)` (`WorkspaceRefsOpener`). `HotKeyAction` has ids 1–3. `HighlightsTakeover` registers keys only while Highlights is frontmost | Source |

Two behaviours are **inferred, not observed**. I chose not to switch Bryan's live tabs to test
them:

- **Re-opening an already-open document through LaunchServices selects its existing tab.** This
  is standard `NSDocumentController` behaviour: the controller finds the document already open
  and shows its window, which selects the tab. F17 is consistent with it, since four opens of
  one note left only one tab.
- **AX may not return windows on other Spaces.** This is commonly reported (AltTab works around
  it with private API) but is unverified here: today all of Highlights' windows sit in one tab
  group.

## 3. Is this a good idea?

**Yes.** The friction is real:

- **The native tab bar names tabs by file name.** For agent reports that means long snake_case
  stems, truncated at 9 tabs. One tab is a 32-character hash.
- **Native switching is weak.** ⌃Tab is linear, ⇧⌘\ shows page thumbnails, and the Window menu
  lists the same file names.
- **Bob already knows what Highlights doesn't:** titles, kind, reading state, Today membership,
  annotations and outline. The panel, ranking, inspector and Copy card already exist.
- **Bryan already uses Bob Refs for this** (F17): about one open in nine re-opens a note he
  opened earlier that day.

**It is cheap.**

- Detection is one small AX reader.
- Mapping uses the `pdfPath` already on every `RefItem`.
- Switching reuses the ↵ path unchanged.
- The tier ranker, the selection rules and the stable-order rules all apply as they are.
- `bob-cli` needs no change. Which PDFs Highlights has open is macOS UI state, not vault
  semantics, so the thin-client decision (`decisions:mac-capture-is-a-thin-client`) is respected:
  the app filters what `bob` returned, using a signal only the Mac can see.

**It is worth more than switching.** Knowing the current document makes "act on the PDF I'm
reading" one keystroke away:

- the inspector shows it;
- ⌘Y copies its marker ID, wiki link or highlights;
- ⌘↵ opens its note in Obsidian.

That is arguably as useful as switching itself. Today Bryan has to search for a PDF he is already
looking at.

**Costs and risks.** Each has a mitigation in §9.

1. **Accessibility is a powerful permission.** It lets the app read and drive any app's UI, and
   Bob Mac Capture is mostly agent-written code. Mitigation: confine AX to one small type that
   only reads Highlights, plus an `AXPress` on a Highlights tab button. Flag any new AX call
   site in review.
2. **Ad-hoc signing revokes the grant on every reinstall** (F14, F16). This is the biggest
   practical risk. Without a stable identity Bryan would see "needs Accessibility" after most
   installs, while System Settings still shows the app as allowed. Recovery would be remove,
   re-add, or `tccutil reset Accessibility org.bobs.bob-mac-capture`.
3. **Background tabs expose only file names** (F7, F8). This is good enough today: 1 collision
   in 431 PDFs. Unmatched names, such as a PDF opened from `~/Downloads`, need an honest
   presentation.
4. **AX coverage gaps.** Windows on other Spaces, and possibly Highlights' ⇧⌘\ overview state,
   may be invisible. In the main use case Highlights is frontmost, so its active window is on the
   current Space.
5. **Highlights could change its UI.** The tab bar is AppKit's native `NSTabBar`, which is
   stable. A custom tab bar would break the tab list but not the `AXDocument` of the visible
   window.

**Would I take a different approach?** Same idea and same panel, with these changes:

1. Make it a **scope**, not a separate mode or panel.
2. List **open PDFs**, including ones without a note, not just "reference notes".
3. Order and select **like ⌘Tab**: current tab first, previous tab selected.
4. **Fix signing before shipping.**
5. **Mark open documents everywhere.**

I would not build a separate switcher panel, use Screen Recording or `lsof`, or route through
Hammerspoon (§4).

## 4. How to find which PDFs Highlights has open: options

| Option | Exact paths? | Background tabs? | Permission | Verdict |
| --- | --- | --- | --- | --- |
| **AX: window `AXDocument` + `AXTabGroup` tab titles** | Visible tab: yes. Others: file name | **Yes** (F7) | Accessibility | **Chosen.** Measured to work; 67 ms cold |
| `lsof` / `proc_pidinfo` file descriptors | — | — | None | **Ruled out by experiment** (F5): PDFKit closes the file after reading |
| `CGWindowListCopyWindowInfo` window names | File name only | Yes (hidden tab windows are listed, F4) | **Screen Recording** | Worse permission (macOS re-asks periodically, and the system label reads "record your screen"), less data than AX |
| AppleScript / Apple Events | — | — | Automation | **Not available** (F2). System Events UI scripting is AX with an extra permission layer |
| Highlights' Open Recent / saved state | Recent ≠ open | — | Container is protected by Apple's privacy controls (prior research) | Wrong question and unreadable |
| Bob Refs' own open log as a proxy | Yes | Only tabs opened from Bob, and it never learns of closes | None | **No-permission fallback only.** It would list closed PDFs and miss others |
| Private `_AXUIElementCreateWithRemoteToken` brute force (AltTab-style) | **Yes, for every tab window** | Yes | Accessibility | Keep in reserve. Private API; only worth it if file-name collisions become real |
| Ask Hammerspoon (which likely has AX) over IPC | As AX | As AX | Hammerspoon's | Rejected: couples to a tool the capture app just replaced |
| `bob` (Rust) doing the AX read | As AX | As AX | Attributed to the parent app anyway | Rejected: no permission benefit, and AX is native in Swift |

**Why AX is enough without private API.** File names identify 430 of 431 library PDFs uniquely
(F10). The visible tab, which is where ambiguity hurts most, always has an exact path (F6).

## 5. Requirement adjustments

| # | As requested | Adjusted | Why |
| --- | --- | --- | --- |
| A1 | A "special mode / filter" | A **scope token, "Tabs"**, beside the kind scopes. Entered with **⌘T** in the panel or the new **⇧⌘O** takeover key while Highlights is frontmost. Esc or ⌫ on an empty query removes it, like any scope token | Same mechanics, keys and stability rules as ⌘1–⌘5 (F20). Typing still filters within it. Following the existing rule, scopes never carry over between invocations |
| A2 | "Only shows reference notes that correspond with PDF files open" | **Show every open PDF.** Matched notes render as normal rows. A PDF with no note renders as a dim **"Not in your library"** row titled by its file name, and ↵ selects that tab with `AXPress` | A switcher that silently omits tabs can't be trusted. Today's count is 0 such rows, so the cost is small |
| A3 | (unstated) order | **Current tab first, labelled "Current"** (with "p. 5/25" from the window title). Then **most recently active**, then tab-bar order. **The second row is selected**, so ⇧⌘O ↵ flips back to the previous document | The ⌘Tab / VS Code ⌃Tab convention. The current row stays in the list because ⌘Y and ⌘↵ on it are valuable (§3) |
| A4 | Tab switcher | **Switch with the existing ↵ path** (`NSWorkspace.open … withApplicationAt: Highlights`). Use `AXPress` only for "Not in your library" rows | The existing path is idempotent: a tab closed in the meantime simply re-opens. It already logs opens and already handles missing PDFs and missing Highlights |
| A5 | (new) | **Mark open documents in every scope**: a small tab glyph on rows open in Highlights. ↵ on them already switches | Same data, near-zero cost; answers "is this already open?" when ⌘O is used to open something |
| A6 | (unstated) naming | Call it **"Tabs"**. The section header is **"In Highlights"** and the count is **"9 tabs"** / **"2 of 9 tabs"**. Never "Open" | "Open" already means open lanes in the count (F19) and is the ↵ verb |
| A7 | (implicit) | **The Tabs scope never changes reading state, lanes, or the vault.** Seeing that 7 of 9 tabs are still "Ready" (F11) is information, not a trigger | Same rule as every Bob Refs open (prior research R8; the lane decision records) |
| A8 | (new prerequisite) | **Sign Bob Mac Capture with a stable identity before shipping Tabs** | F14 and F16: otherwise the grant is lost on every install |
| A9 | (new) | **Ask for permission lazily**: only when Bryan first enters Tabs, through an in-panel callout with an explicit "Open Accessibility Settings" button. **Never prompt at launch.** Without the grant, A5's glyphs simply don't appear | Users who never use Tabs never see a permission prompt |
| A10 | (non-goal) | **No closing, moving, or reordering tabs from Bob** in v1. A ⌘W "close this tab" could come later | Keeps AX use read-mostly (§3, risk 1) |

## 6. Design

### 6.1 Reading the tabs (BobMacCapture target, AppKit + ApplicationServices)

Put a small `HighlightsTabsReader` behind a protocol, like `RefsOpening`, so tests can inject a
fake. It returns one of `.notRunning`, `.notTrusted`, `.failed(String)` or
`.snapshot(HighlightsTabsSnapshot)`. The algorithm is the one the probe verified:

```swift
// Off the main actor. Bundle id from HighlightsLocator / the Settings override.
guard let app = NSRunningApplication.runningApplications(withBundleIdentifier: id).first
else { return .notRunning }
guard AXIsProcessTrusted() else { return .notTrusted }        // never the prompting variant here
let axApp = AXUIElementCreateApplication(app.processIdentifier)
AXUIElementSetMessagingTimeout(axApp, 0.4)                   // default is ~6 s; Highlights may be busy rendering
for window in axApp[kAXWindowsAttribute] {                   // visible tab of each window (F6)
    let doc = window[kAXDocumentAttribute] as? String        // file URL of the visible tab
    let tabGroup = window[kAXChildrenAttribute].first { $0[kAXRoleAttribute] == "AXTabGroup" }
    if let tabs = tabGroup?[kAXTabsAttribute] ?? tabGroup?[kAXChildrenAttribute] {
        // AXRadioButton: title = file name, value 1 = selected (F7)
    } else {
        // A single-document window has no tab bar: one tab, title from the AXDocument file name
    }
}
```

Snapshot shape, a Foundation-only value in RefsCore:

```swift
struct HighlightsTabsSnapshot {
    struct Tab { var fileName: String; var documentPath: String?; var isSelected: Bool }
    struct Window { var tabs: [Tab]; var isMain: Bool; var pageCaption: String? } // "Page 5 of 25" from AXTitle
    var windows: [Window]          // AX order: main window first
}
```

**When to read:**

- on every panel show, in every scope, because A5's glyph needs it;
- on entering Tabs;
- on ⌘R;
- when Highlights resigns active. `HighlightsTakeover` already observes
  `didDeactivateApplication`; that read only updates recency (§6.3).

Keep the last snapshot in memory only: never on disk, and never in signposts, since titles are
private.

**Budget.**

- In Tabs mode, wait up to about 120 ms for the read before the first paint; the probe measured
  67 ms cold, and an in-process read should be faster.
- Past that, paint the cached snapshot and apply the fresh one under the existing "rows never
  move under the cursor" rule: content updates in place, and re-ranking happens only if the user
  hasn't moved yet.
- In other scopes, never wait. Glyphs fill in place.

### 6.2 Matching tabs to references (RefsCore, pure, testable on Linux)

`HighlightsTabMatcher.match(snapshot, items, vaultRoot) -> [RefsOpenTab]`:

1. **Exact path.** For a tab with `documentPath`, standardize the path, strip the vault root, and
   compare it to `item.pdfPath` case-insensitively (APFS default). This always resolves the
   visible tab.
2. **File name.** Otherwise compare the tab title against the last path component of
   `item.pdfPath`, case-insensitively. As a defensive step, strip a trailing ` – Page N of M` if
   one ever appears. A unique hit is a match.
3. **Collision** (today only `harness_engineering.pdf`). Emit every candidate, each flagged
   "matched by file name". ↵ on the wrong one merely opens that PDF as a new tab, which is
   harmless and honest. *Do not* guess from the open log.
4. **No hit.** Emit an orphan tab: `itemID = nil`, title = file name, and a window/tab index for
   `AXPress`.

Each `RefsOpenTab` carries `itemID?`, `fileName`, `windowIndex`, `tabIndex`, `isCurrent`,
`pageCaption?` and `match ∈ {path, fileName, collision, none}`. Feed it to the ranker as a new
`RefsSignals.highlightsTabs` field. That fits how `today`, `missingPDFs` and `scan` already flow.

### 6.3 Ordering, selection, and the ranker

- **Scope.** Add `RefScope.tabs`. A tabs-aware filter is needed because `contains(_ kind:)`
  cannot see signals. Either add `contains(_ item:, signals:)` or special-case `.tabs` in
  `RefsRanker.listing` (F20). Orphan tabs need a small row type, or a synthetic `RefItem`-like
  row in the listing; keep them out of `library.items`.
- **Browse (empty query).** Show one section, **In Highlights**:
  1. the current tab (the main window's selected tab);
  2. then the others by **last active**, newest first;
  3. then by window order and tab-bar order;
  4. orphans last.

  "Last active" is an in-memory map, `fileName → Date`, sampled from the current tab at three
  moments: each panel show, each switch dispatched from Bob, and each Highlights deactivation.
  That captures most switches without an AX observer. ⌃Tab switches made inside Highlights are
  caught at the next sample.
- **Typed query.** Use the existing tiered search, restricted to the tab set. Tier rules, the
  within-tier score and the path tie-break are unchanged.
- **Selection.** On entering Tabs, select **row 2** when row 1 is the current tab; otherwise
  select row 1. After any query edit, select the first row (existing rule).
- **Glyphs in all scopes.** A row open in Highlights gets a small tab glyph (e.g. SF Symbol
  `square.on.square`) next to the state glyph. VoiceOver appends ", open in Highlights". The
  current tab adds a "Current" pill in Tabs scope.

Mock-up with today's real tabs, an empty query, and the selection on the previous document:

```text
╭──────────────────────────────────────────────────────────────────────────────────────╮
│ ⌕  Switch to…                               [Tabs ⌘T]                         9 tabs  │
├───────────────────────────────────────────────┬──────────────────────────────────────┤
│ IN HIGHLIGHTS                                 │  Chat  ✓ Read                          │
│ [💬] Wave 3: Twelve More… ○ Current p.5/25    │                                        │
│▸[💬] Wave 2: The Ten Applications to Send…  ✓ │  Wave 2: The Ten Applications to       │
│ [💬] Docs as Memory: Move Facts to `docs/`… ○ │  Send Next (October 2026)              │
│ [💬] Project Docs as Managed Memory: Cons… ○  │  …inspector as today…                  │
│ [📰] karpathy/llm-wiki.md                  ○  │                                        │
│ [📰] diataxis fr compass and howto         ○  │                                        │
│ [💬] The First Paragraphs of the First SA… ✓  │                                        │
│ [💬] Funding a sase Sprint at Launch with… ○  │                                        │
│ [💬] Retiring `sase_blog_0`: one blog pos… ○  │                                        │
├───────────────────────────────────────────────┴──────────────────────────────────────┤
│ ↵ Switch   ⌘↵ Note   ⌘Y Copy   ⌘K Actions   ⌘T All references   esc Close             │
╰──────────────────────────────────────────────────────────────────────────────────────╯
```

### 6.4 Switching

- **Library row.** Unchanged: `openInHighlights(item)`. The panel hides, LaunchServices hands
  the URL to Highlights, and `NSDocumentController` finds the open document and brings its tab
  forward. If the tab was closed in the meantime, the PDF re-opens. The switch also appends to
  the open log, as today. That is fair, because switching to a document is a use; revisit only if
  frecency skews.
- **Orphan row.** `AXPress` on the tab's `AXRadioButton`, then `AXRaise` its window. To survive a
  stale snapshot, re-resolve the tab by `(window index, file name)` at press time. If it is gone,
  show the existing "no longer available" banner.
- **Verify on the Mac before merging.** Re-opening an open, background-tab PDF through
  `NSWorkspace.open` must select the existing tab and not create a duplicate. It should, as
  §2 explains, but this is the one behaviour I did not observe.

### 6.5 Entry points and keys

| Key | Where | Action |
| --- | --- | --- |
| **⇧⌘O** (configurable: ⇧⌘O / ⌘E / Off) | While Highlights, or the override app, is frontmost | Show Bob Refs in the Tabs scope. Pressed again, it closes the panel. With the panel open in All, ⇧⌘O switches to Tabs, and ⌘O switches back to All |
| ⌘O (unchanged) | While Highlights is frontmost | Show Bob Refs in All |
| ⌃⇧⌘R (unchanged) | Global | Show Bob Refs in All |
| **⌘T** | In the panel | Toggle the Tabs scope (Tabs ↔ All) |
| ↵ / Tab | Tabs scope | Switch (§6.4) |

Notes on the keys:

- ⇧⌘O is free in Highlights (F13), sits next to the ⌘O habit, and reads as "open, among the
  already open". It is registered as `HotKeyAction.refsHighlightsTabs = 4`, alongside
  `refsHighlightsOpen = 3` in `HighlightsTakeover`, and only while Highlights is frontmost. It
  never steals ⇧⌘O from other apps.
- ⌘T is free in both Highlights and Bob Refs. A letter suits Tabs better than ⌘6, because it is
  not a kind.

### 6.6 States

| State | What the Tabs scope shows |
| --- | --- |
| Accessibility not granted | A centered card: "Bob Refs needs Accessibility access to see Highlights' tabs." Buttons: **Open Accessibility Settings** (calls `AXIsProcessTrustedWithOptions` with the prompt, or opens the Privacy › Accessibility pane) and **Back to all references** (⌘T). When the build is ad-hoc signed, a quiet second line adds "Grants reset when Bob Mac Capture is reinstalled with an ad-hoc signature" |
| Highlights not running | "Highlights isn't running." ⌘T returns to All |
| No documents open | "No PDFs are open in Highlights." |
| AX read failed or timed out | Keep the last snapshot, dimmed, with "Couldn't read Highlights' tabs · ⌘R to retry" in the footer |

Settings › References shows **Highlights tabs: Allowed / Not allowed**, next to the existing
resolved-Highlights row. `BundleSigningInspector`'s ad-hoc diagnostic should also mention
Accessibility, not only notifications.

## 7. Signing: the prerequisite

- **The problem.** `Scripts/bundle.sh` already takes `--identity`, and `just install` already
  takes an `identity` argument, but it defaults to `-` (ad-hoc). With ad-hoc signing the
  designated requirement is the cdhash (F14), which changes on every build. TCC compares that
  requirement, so the Accessibility grant stops applying after each reinstall.
- **The fix.**
  1. Create one long-lived **self-signed code-signing certificate** in the Mac's login keychain,
     e.g. "Bob Mac Capture Local". Keychain Access › Certificate Assistant › Create a
     Certificate, type Code Signing; this is the same remedy other projects that need persistent
     TCC grants document.
  2. Make the justfile's `install` default to that identity when it exists, falling back to `-`
     with a warning.
  3. Document this in the README.
  4. Grant Accessibility once after the first install with the new identity.
- **The result.** The designated requirement becomes `identifier "org.bobs.bob-mac-capture" and
  certificate leaf = H"…"`, which stays the same across rebuilds.
- **Side benefit.** It also fixes the notification-permission drift that `BundleSigningInspector`
  already warns about.
- **Agent hosts are unaffected.** They build scratch copies and never install.

## 8. Open questions and spikes

1. **Re-open selects the tab (§6.4).** Before merging, run on the Mac:
   `open -g -a Highlights <a background-tab PDF>` and confirm through the AX probe that
   `AXValue` moved and the tab count is unchanged.
2. **Other Spaces and full screen.** Open a second Highlights window on another Space and check
   whether `AXWindows` lists it. If not, document the limitation. The private remote-token
   enumeration (§4) is the fallback, but only if it matters in practice.
3. **The ⇧⌘\ overview and minimized windows.** Check that the reader degrades to "last snapshot"
   rather than an empty list.
4. **Recency without sampling gaps.** If sampled recency feels wrong after ⌃Tab-heavy sessions,
   add an `AXObserver` on Highlights for `kAXFocusedWindowChangedNotification` and
   `kAXMainWindowChangedNotification` (each tab is its own window, so a tab switch should
   change the main window). Unverified; phase 3.
5. **Optional bob-cli follow-up, not needed for this feature.** Make PDF file names unique
   across `lib/` (today only `harness_engineering.pdf` collides). That would remove the last
   matching ambiguity and also the stem ambiguity of `highlights://<stem>` deep links that the
   prior research noted. Bryan's call; I did not file a bead.
6. **Decision record.** Consider recording "Bob Mac Capture may read Highlights' UI through
   Accessibility; it only selects tabs, never edits documents", so future agents don't widen AX
   use casually.

## 9. Recommended solution

**Build a "Tabs" scope in Bob Refs, backed by a read-only Accessibility reader of Highlights'
windows and native tab bar, after moving Bob Mac Capture to a stable signing identity.**

**Phase 0: stable signing (prerequisite, about an hour, Mac only).**

- Create the self-signed "Bob Mac Capture Local" identity on the Mac.
- Default `just install` to it, with an ad-hoc fallback and a warning.
- Update the README and the `BundleSigningInspector` diagnostic text.
- Verify that `codesign -d -r-` shows a certificate-leaf requirement, then reinstall twice and
  confirm `AXIsProcessTrusted()` stays true.

**Phase 1: RefsCore (Foundation-only; `just portable-check` on athena).**

- Add the `HighlightsTabsSnapshot` value and `HighlightsTabMatcher`:
  - exact path, then file name;
  - collisions show every candidate;
  - orphans kept.
- Add `RefsSignals.highlightsTabs` and the in-memory last-active map.
- Add `RefScope.tabs`, with a tabs-aware filter in `RefsRanker.listing`.
- In Tabs browse, one "In Highlights" section: current, then most recently active, then tab
  order, then orphans. Tabs search uses the existing tiers.
- Add selection policy: row 2 when row 1 is the current tab.
- Golden tests from today's real snapshot (9 tabs, all matched) and from synthetic cases:
  - a `harness_engineering.pdf` collision;
  - an orphan `~/Downloads` PDF;
  - a single window with no tab bar;
  - two windows;
  - an empty snapshot.
- Extend `refs-rank` with `--tabs snapshot.json` for tuning.

**Phase 2: BobMacCapture (compile on the Mac per AGENTS.md; CI runs the tests).**

- **Reader.** `AXHighlightsTabsReader`:
  - off the main actor, with a 0.4 s messaging timeout;
  - honours the Settings override app's bundle id;
  - reads on show, on Tabs entry, on ⌘R, and on Highlights deactivation (recency only).
- **Panel.**
  - ⌘T toggles the scope; the scope token reads "Tabs".
  - The count reads "N tabs" / "k of N tabs".
  - Rows get the "Current · p. N/M" pill, the open-in-Highlights glyph in every scope, and
    VoiceOver text.
  - The footer reads "↵ Switch".
  - Orphan rows switch with `AXPress` + `AXRaise`.
  - The states follow §6.6, including the lazy permission card.
- **Takeover.** Add `HotKeyAction.refsHighlightsTabs = 4`, default ⇧⌘O, configurable to ⌘E or
  Off. `HighlightsTakeover` registers it only while Highlights is frontmost. ⌘O and ⇧⌘O switch
  scope when the panel is already open.
- **Settings › References.** Add the tabs-key picker and the "Highlights tabs: Allowed / Not
  allowed" status row.
- **README.** Add a "Tabs" subsection, update the key table, and document the Accessibility
  rationale and its read-only scope.
- **Spikes.** Run §8 items 1–3 on the Mac before merging.

**Phase 3: optional, only if wanted after use.**

- An `AXObserver` for exact recency.
- ⌘W on a Tabs row to close that tab: `AXPress` its close button, behind A10's review.
- "Current PDF" affordances elsewhere, such as Capture offering the current reference as a link
  target.
- Private remote-token enumeration, only if Spaces gaps or file-name collisions bite.

**Why this over the alternatives.**

- It is the only mechanism measured to see every tab (F7) without Screen Recording.
- Detection, matching and ordering are pure and testable on Linux.
- Switching reuses a path that already works ↵ by ↵ today.
- The one real cost, the permission, is paid once, because the signing identity makes it stick.
- The scope design keeps ⌘O's "open something new" fast while giving ⇧⌘O ↵ the "back to my other
  PDF" flip that the tab bar can't offer.

## Sources

- Prior Bob research: `research:202610/highlights_quick_open_refs_panel/highlights_quick_open_refs_panel__final.md`
  (Highlights is not scriptable, bundle id, Open Recent unreadable, Bob Refs design rules).
- `bob-mac-capture` at `9f58448`: `README.md` (Bob Refs), `Sources/RefsCore/RefsModel.swift`,
  `Sources/RefsCore/RefsRanking.swift`, `Sources/BobMacCapture/Refs/RefsPanelModel.swift`,
  `Sources/BobMacCapture/Refs/RefsSearchBar.swift`, `Sources/BobMacCapture/HighlightsTakeover.swift`,
  `Sources/BobMacCapture/HotKeyRegistry.swift`, `Sources/BobMacCapture/BundleSigningInspector.swift`,
  `Scripts/bundle.sh`, `justfile`.
- Live read-only probes on the Mac (2026-10-15): `plutil`, `lsof`, `defaults read`, `codesign`,
  `security find-identity`, a JXA `CGWindowListCopyWindowInfo` probe, and Swift AX probes of
  Highlights' windows, tab group and menu bar. Each probe script was copied to `/tmp` and deleted
  after it ran.
- `bob ref list -R all -A -f json` on apollo (2026-10-15T20:39).
- Ad-hoc signing and TCC grants:
  [shannoncoat 0.0.8, "Sign builds and releases with a stable code identity"](https://git.bdeshi.space/bdeshi/shannoncoat/src/tag/0.0.8),
  [OpenClaw macOS signing docs](https://docs2.openclaw.ai/platforms/mac/signing),
  [OpenClaw macOS permissions docs](https://docs.openclaw.ai/de/platforms/mac/permissions),
  [Macworld: resetting macOS privacy preferences](https://www.macworld.com/article/1378183/how-to-reset-macos-privacy-preferences-when-other-options-dont-work.html).
- Highlights scripting:
  [Late Night Software forum, apps that support AppleScript](https://forum.latenightsw.com/t/apps-that-support-applescript-by-category/3890)
  (Highlights absent);
  [Highlights on the App Store](https://apps.apple.com/us/app/highlights-extract-pdf-notes/id1498912833).
- Cross-Space window listing as a known AX limitation that third-party switchers work around:
  [AltTab features](https://alt-tab.app/features).
