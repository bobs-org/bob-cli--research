# Bob Refs as a Highlights tab switcher

- **Date:** 2026-10-15
- **Researcher:** grk
- **Type:** independent swarm report (`__grk`)
- **Question:** Add a special mode / filter to Bob Mac Capture's reference panel that shows only reference notes whose PDFs are currently open in Highlights, so the panel can act as a Highlights tab switcher. Is that a good idea, how should it be built, and what should change?

## 1. Bottom line

Build it. The job is real, small, and already 80% implemented. Do not add a kind-scope, a `bob` subcommand, or a second app.

Tonight Highlights is running on the Mac with **nine PDFs open as tabs in one window**. The Window menu and tab bar list snake_case filenames (`third_wave_job_applications.pdf – Page 6 of 25`). Bob already has the human titles (`Wave 3: Twelve More Roles to Apply For (October 2026)`), kinds, reading state, and inspector for every one of them. Return on an already-open PDF **switches to that tab** and keeps the reading page. That is the whole product: enumerate live tabs, match them to the existing `bob ref list` snapshot, and reuse the opener the panel already has.

**The original request is the right problem with the wrong default shape.** A sticky filter on the full library is weaker than a **session mode that the Highlights takeover already enters**. ⌘O while Highlights is frontmost should open Bob Refs on the open tabs. The global hotkey should keep showing the full library. ⌘6 (free today) toggles the mode from either entry.

Recommended name: **Tabs**. The search bar already prints ``N open · M`` for *reading-state* open (Ready / Next / Reading). Calling this mode "Open" would collide with that count.

## 2. Facts this recommendation rests on

Verified on `mac` (macOS 26.5, Highlights 2026.1.2 build 602, bundle id `net.highlightsapp.universal`) on 2026-10-15, plus the current bob-mac-capture and bob-cli trees.

| Fact | Evidence |
| --- | --- |
| Highlights is an `NSDocument` app (`Highlights.Document`) for PDF, MultiMarkdown, and TextBundle | `Info.plist` `CFBundleDocumentTypes` / `NSDocumentClass` |
| Highlights is not AppleScriptable | Vendor FAQ, still current as of 2026-10-13: "Is Highlights scriptable? No, not yet." `NSAppleScriptEnabled` and `OSAScriptingDefinition` unset; no `.sdef`. `tell application "Highlights" to get documents` / `windows` → error −1728 |
| Tabs have been a Highlights feature since v1.5.1 (macOS Sierra, 2016-09-21) | [Highlights Mac changelog](https://highlightsapp.net/changelog/mac/) |
| Prefer-tabs is a *system* setting, not an app setting | FAQ: Desktop & Dock → Windows → "Prefer tabs when opening documents" |
| Live session: **9 tabs, 1 window** | Window menu document items and `AXTabGroup` radio buttons agree |
| Front window exposes a full `file://` path | `AXDocument` = `file:///Users/bbugyi/bob/lib/chat/third_wave_job_applications.pdf` |
| Background tabs expose **filename only** | Each `AXRadioButton`/`AXTabButton` has `AXTitle` = `stem.pdf`, no `AXDocument` / `AXURL` |
| `lsof` sees **zero** PDF file descriptors on the Highlights PID | Sandboxed container cwd; PDFs are not visible as classic fds. `lsof` cannot enumerate open documents |
| `CGWindowListCopyWindowInfo` window names are **nil** | Screen Recording not granted to this process; even with it, CGWindowList would name the front window, not background tabs |
| Open Recent is a **different set** than open tabs | Open Recent includes `BryanBugyi_CV_extended_v3.pdf`, `bulk_capture_template_drafts.pdf`, `ref_create_multi_url_collections.pdf`, which are not among the 9 tabs |
| Re-opening an already-open PDF **selects that tab**, does not duplicate | `open -a Highlights ~/bob/lib/chat/sase_blog_subproject_retirement.pdf` moved front from `third_wave…` to `sase_blog…`; window count stayed 1; page stayed at 2 of 12. Restored afterward |
| Accessibility reads Highlights while it is **not** frontmost | Chrome was frontmost; `name of window 1` of process Highlights still returned |
| Library: **1033** notes, **431** with `source_pdf`; panel already drops notes without a PDF | `bob ref list -R all -A -f json` on the Mac |
| Basename collisions in `lib/` and in `source_pdf`: **1** (`harness_engineering.pdf` in `blogs/` and `papers/`) | 430 PDFs / 429 unique names on disk; same collision in the index |
| All 9 currently open tabs match the index uniquely | See §2.1 |
| Bob Refs already opens Highlights via `NSWorkspace.open([pdf], withApplicationAt: Highlights)` | `WorkspaceRefsOpener.openInHighlights` |
| Takeover and global hotkeys share one handler | `AppDelegate`: `case .refs, .refsHighlightsOpen: toggleRefs()` |
| Presentation always resets to All scope and empty query | `RefsPanelModel.prepareForPresentation()` |
| Kind scopes occupy ⌘1–⌘5; ⌘6 is free | `RefsKeyRouter` |
| Bob Mac Capture is **not sandboxed** (adhoc + hardened runtime, empty entitlements) | `codesign -d -vv` on `~/Applications/Bob Mac Capture.app`. Apple's position: Accessibility APIs do not work from a sandboxed app; this app can use them once TCC Accessibility is granted |
| Thin-client rule: the app may filter and rank what `bob` returns; it does not parse the vault | `decisions:mac-capture-is-a-thin-client`; Bob Refs README |

### 2.1 The nine open tabs, mapped

| Highlights tab (filename) | Bob title | `ref_type` | `reading_state` | note |
| --- | --- | --- | --- | --- |
| `third_wave_job_applications.pdf` (front, p.6/25) | Wave 3: Twelve More Roles to Apply For (October 2026) | chat | queued | `ref/chat/third_wave_job_applications.md` |
| `second_wave_job_applications.pdf` | Wave 2: The Ten Applications to Send Next (October 2026) | chat | finished | `ref/chat/second_wave_job_applications.md` |
| `docs_backed_memory_and_agent_maintained_docs.pdf` | Docs as Memory: Move Facts to `docs/`, Keep Rules in Memory, Generate the Tables | chat | queued | `ref/chat/docs_backed_memory_and_agent_maintained_docs.md` |
| `project_docs_as_managed_memory_reading_list.pdf` | Project Docs as Managed Memory: Consolidated Reading List | chat | queued | `ref/chat/project_docs_as_managed_memory_reading_list.md` |
| `442a6bf555914893e9891c11519de94f.pdf` | karpathy/llm-wiki.md | blogs | queued | `ref/blogs/442a6bf555914893e9891c11519de94f.md` |
| `diataxis_fr_compass_and_howto.pdf` | diataxis fr compass and howto | blogs | queued | `ref/blogs/diataxis_fr_compass_and_howto.md` |
| `sase_launch_post_introduction.pdf` | The First Paragraphs of the First SASE Blog Post | chat | finished | `ref/chat/sase_launch_post_introduction.md` |
| `sase_launch_sprint_threshold_funding.pdf` | Funding a sase Sprint at Launch with Threshold Pledges: Critique, Adjusted Terms, and a Recommendation | chat | queued | `ref/chat/sase_launch_sprint_threshold_funding.md` |
| `sase_blog_subproject_retirement.pdf` | Retiring `sase_blog_0`: one blog post, one project | chat | queued | `ref/chat/sase_blog_subproject_retirement.md` |

That table is the argument. Highlights shows the left column. Bob Refs already knows the rest.

Related prior work, used as shared input only: `research:202610/highlights_quick_open_refs_panel/highlights_quick_open_refs_panel__final.md` (2026-10-08). That swarm built the picker this request wants to specialize. Library size then was 341 PDF-backed notes; it is 431 today. The "Highlights is not scriptable" finding still holds.

## 3. Critique: is this a good idea?

**Yes, with a tighter product definition than "a filter on the reference panel."**

The original Refs panel solved *finding*. This request solves *switching among what is already open*. Those are different questions that happen to share a surface. Nine tabs is already past comfortable Control-Tab cycling, and Highlights' own Window menu still shows filenames. Nothing else on the Mac knows Bob titles, kinds, or the inspector. The gap is the same one the 2026-10-08 research named, now inside a working set of size ~10 instead of ~400.

The idea is cheap because the expensive parts exist:

- Snapshot, ranker, inspector, Copy card, non-activating panel
- Highlights-frontmost ⌘O takeover (`HighlightsTakeover`)
- `NSWorkspace` open that, tonight, coalesces onto the existing tab
- `RefItem.stem` / `pdfPath` already derived from `source_pdf`

What would make it a *bad* idea is treating it as a new library query, a new `bob` command, or a kind chip. Those would either lie (the vault does not know Highlights' document set) or fight the thin-client rule.

### 3.1 Alternatives

| Option | What it buys | Why it is not the answer |
| --- | --- | --- |
| Highlights Window menu / Show Next Tab | Zero work | Filenames, no search, no inspector. The pain being solved |
| Control-Tab / Control-Shift-Tab | Zero work | Blind cycle; no titles |
| Filter the panel by `refs-open-log.json` | No Accessibility permission | Log is "opened from Bob Refs", not "open in Highlights". Closes are invisible. Opens from Highlights itself are invisible |
| Filter by File → Open Recent | Easy AX scrape of names | Different set than live tabs (verified tonight) |
| `lsof` on the Highlights PID | No TCC | Zero PDF fds tonight; will miss documents |
| `CGWindowList` / ScreenCaptureKit | Window titles | Names nil without Screen Recording; still one title per window, not per tab |
| AppleScript `every document` | Clean API | Vendor: not scriptable; live −1728 |
| `highlights://` URL scheme | Open-by-path, optional `#page=N` | Useful as an opener, not an enumerator. Do not pass `#page=` when switching; LaunchServices already preserves page |
| Siri AI in Highlights 2026.2 | Vendor search | Needs macOS 27; Mac is on 26.5; not a deterministic tab list |
| Alfred / Raycast / Hammerspoon chooser | Fast prototype | Same metadata problem, plus a third client. Capture already left Hammerspoon |
| Separate switcher window | Cleaner job separation | Duplicates panel, hotkey, opener, ranking. The takeover *is* the switcher entry |
| New `bob ref open-tabs` / catalog | CLI symmetry | `bob` cannot see Highlights. The live set is a Mac-only AX read |
| Walk `lib/` and hope mtimes | No AX | mtimes were already rejected as "added" dates in the 2026-10-08 research |

### 3.2 Would I take a different approach?

Same destination, four changes from the request as written:

1. **Entry point first, filter second.** The Highlights takeover (⌘O) should *enter* Tabs mode. A filter you have to remember to enable will not get used as a tab switcher. The global ⌃⇧⌘O hotkey stays the library picker.
2. **Session mode, not a `RefScope`.** ⌘1–⌘5 are kinds. Open-in-Highlights is a different axis. Encode it as `tabsFilter: Bool` (or a small `RefsSessionFilter`) orthogonal to `RefScope`. Kind scopes can still apply inside the tab set (⌘3 among open papers) because that is one extra `filter` and costs nothing.
3. **Enumerate with Accessibility, activate with LaunchServices.** AX is the only API that listed all nine tabs tonight. Activation should keep `WorkspaceRefsOpener.openInHighlights`, which already coalesces. Clicking an `AXTabButton` is the fallback for unmatched filenames, not the primary switch.
4. **Show unmatched open PDFs.** A switcher that hides a tab because it has no reference note is an incomplete switcher. Render those rows dim, titled from the filename, still Return-able via the tab button.

I would not build a dedicated tiny switcher, would not persist the mode across shows, and would not wait for Highlights scripting.

## 4. Requirement adjustments

Call-outs from the original request. Each is a change I would make.

| # | Original | Adjusted | Why |
| --- | --- | --- | --- |
| A1 | "A special mode / filter" on the panel | A **Tabs session filter**, default-on when the panel is opened via `.refsHighlightsOpen`, default-off for the global hotkey and the menu-bar item | A filter that starts at All is a library picker with extra work. The takeover is already the "I am in Highlights" gesture |
| A2 | Only reference notes whose PDFs are open | The live Highlights document set, **joined** to the snapshot. Unmatched tabs still appear | Completeness of a switcher. Tonight all 9 match; that will not stay true for CVs, intake, or files outside `lib/` |
| A3 | Kind-like scope, or a chip among Chats/Papers/… | **Not** a sixth `RefScope`. Token in the search bar, independent of ⌘1–⌘5 | Kind and "currently open" answer different questions. Esc/Backspace already peels scope; peel Tabs the same way, outermost |
| A4 | Name it "open" / "currently opened" | Name the token **Tabs**. Count reads `9 tabs`, never `N open` | ``N open · M`` already means reading-state open (`RefsRanker.openCount`) |
| A5 | (implicit) Filter the existing browse ranking | Empty query in Tabs mode is **one section**, frontmost first, then Highlights tab order. Typed query uses the existing ranker on that subset | Browse sections (Today, Just added, Library, …) are meaningless on nine rows and would hide the front tab under "Ready" |
| A6 | (unstated) New bob command or vault walk | **No bob-cli change.** Match AX filenames / `AXDocument` paths to `RefItem.pdfPath` / `stem` | Thin client. The vault does not know Highlights' documents |
| A7 | (unstated) Opening behavior | Return keeps `openInHighlights`. It must **not** jump page (`highlights://…#page=` is forbidden on switch). Opening still does not mutate reading state | Verified coalescing + page preservation; lane-ownership decisions still apply |
| A8 | (unstated) Permission | Accessibility TCC for Bob Mac Capture. If denied or Highlights is not running, **degrade to today's full library** with a banner, and still let ⌘O open Refs | Never make the takeover worse than it is today |
| A9 | (unstated) Selection | On enter, select the **frontmost** tab | A switcher that lands on row 1 of tab-bar order is wrong when the front document is the last tab |
| A10 | (unstated) Live updates | Re-read AX on show, and while the panel is visible (~1 s). If the set changes, refresh content; keep selection when the id still exists | Tabs close under the panel. Frozen listings are correct for library search; they are wrong for a live document set |
| A11 | (unstated) Distinguish hotkeys | Split `case .refs, .refsHighlightsOpen` so takeover can pass a presentation source | Today both call `toggleRefs()` and `prepareForPresentation()` resets to All |

## 5. How to enumerate open documents

Ranked. Only the first is viable as the source of truth.

### 5.1 Accessibility (recommended)

Direct `AXUIElementCreateApplication(pid)` on Highlights, not `osascript` / System Events. Bob Mac Capture is an `LSUIElement` with hardened runtime and **no App Sandbox**, so AX is allowed once Accessibility is granted. `AXIsProcessTrustedWithOptions` with `kAXTrustedCheckOptionPrompt` is the prompt. Do not add Apple Events entitlements or talk to System Events; that is a second TCC (Automation) for no gain.

Enumeration algorithm:

1. Resolve Highlights PID from `NSWorkspace.runningApplications` matching `HighlightsLocator.bundleIdentifier` (or the Settings override).
2. Copy `kAXWindowsAttribute`.
3. For each window: read `kAXDocumentAttribute` (full `file://` when present) and `kAXTitleAttribute` (`stem.pdf – Page N of M` tonight).
4. Walk descendants (or the window's `AXTabGroup` / `AXTabButton` children) for tab titles and `kAXValueAttribute` (true = selected).
5. Unique by lowercase filename. Prefer a `file://` path when any window supplied one.

Tonight that produced every tab. Roles (`AXTabGroup`, `AXTabButton`, `AXDocument`) are stable across localization; English menu titles are not. Do not scrape the "Window" menu by name as the primary path.

Fallback activation for a tab with no library path: `AXPress` on the matching `AXTabButton`. Primary activation stays LaunchServices on the matched `source_pdf`.

### 5.2 Rejected enumerators

- **AppleScript documents/windows:** not implemented.
- **lsof:** 0 PDFs.
- **CGWindowList:** names nil; no tabs.
- **Saved Application State / container preferences:** container listing tonight did not yield a readable recent-documents list; prior research also found Open Recent backing stores TCC-protected. Even if readable, restored-but-closed is the wrong set (FAQ: Highlights restores windows because of a *system* setting).
- **Spotlight `kMDItemLastUsedDate`:** last used, not open.
- **`refs-open-log.json`:** Bob-initiated opens only.

### 5.3 Matching to reference notes

`RefItem` already carries `pdfPath` (vault-relative `source_pdf`) and `stem`. Matching is a pure function in `RefsCore`, with a fake listing in tests:

1. If AX supplied `file:///Users/bbugyi/bob/lib/chat/foo.pdf`, suffix-match against `pdfPath` (`lib/chat/foo.pdf`) after standardization (`/private` prefix, case).
2. Else unique match on `stem.pdf` / `stem` against `RefItem.stem`.
3. Else collision: show both notes, caption "also `lib/papers/…`", Return opens the selected note's PDF (LaunchServices coalesces whichever is actually open).
4. Else unmatched: synthetic row, filename as title, dim, Return presses the tab.

Collision budget: **one pair in 431 PDFs**. Do not over-design it.

`RefsCore` stays Foundation-only. The AX reader lives in `BobMacCapture` behind `RefsHighlightsOpenListing`, injected like `RefsOpening` / `RefsHighlightsLocating`.

## 6. How the panel should behave

### 6.1 Entry

| Source | Tabs filter | Query | Kind scope | Selection |
| --- | --- | --- | --- | --- |
| Highlights takeover ⌘O / ⌃O | on | empty | All | frontmost tab |
| Global ⌃⇧⌘O, menu bar, scan notification | off | empty | All | current first-row policy |
| Toggle while already visible | hide (unchanged) | — | — | — |

Closing with the same takeover key still hides the panel (`HighlightsTakeover` already registers only while Highlights is frontmost; the panel never activates).

### 6.2 Keys

- **⌘6** toggles Tabs. Visible token, same capsule pattern as kind scopes, `doc.on.doc` (or similar) glyph. Backspace on empty query clears Tabs then kind scope then closes, matching today's Esc peel order with Tabs outermost when it was auto-applied.
- ⌘1–⌘5 keep working inside the tab set.
- Return / Tab / double-click: existing Highlights open.
- Everything else (⌘↵ note, ⌥↵ reveal, ⌘Y copy, inspector) stays.

### 6.3 Empty and error states

| Condition | Panel |
| --- | --- |
| Highlights not running | Banner "Highlights isn't running"; Tabs token present; list is the ordinary library so the gesture still does something |
| Accessibility denied | Banner with **Enable Accessibility** (`AXIsProcessTrustedWithOptions` prompt) and **Show library**; list is the ordinary library |
| Highlights running, zero document tabs (browser-only window) | Empty well: "No open Highlights tabs"; second line "⌘6 shows the library" |
| AX succeeded, 9 tabs | One "Tabs" section, `9 tabs` in the count slot |

### 6.4 Ranking

Empty query: **do not** call `RefsRanker.browseSections`. Order = frontmost, then remaining AX tab order. Why-here line: "Open in Highlights" / "Frontmost".

Typed query: existing tiered ranker on the tab subset. A title match among nine rows is the actual search a switcher needs (`wave 3`, `karpathy`, `diataxis`).

Late library refresh still must not reorder (existing freeze rule). A *tab-set* change may reorder because the universe changed; keep `selectedID` when it still exists.

### 6.5 Privacy

AX reads window titles, tab names, and the front document path. Those strings are already Highlights UI. Do not write them to `refs-open-log.json` or the snapshot. Signposts stay event names only. README Privacy + Troubleshooting get one bullet: "Tabs mode needs Accessibility; without it, ⌘O still opens the full library."

## 7. Implementation sketch (for whoever builds it)

Keep this in bob-mac-capture. No bob-cli PR.

1. **`RefsHighlightsOpenTab`** (`Sendable`): `filename`, `fileURL?`, `pageLabel?`, `isFrontmost`, `tabIndex`.
2. **`RefsHighlightsOpenListing` protocol** + `AccessibilityHighlightsOpenLister` using `AXUIElement`. Tests inject a fake.
3. **`RefsOpenTabMatcher.match(tabs:items:)`** in `RefsCore`: returns ordered `RefItem` ids plus unmatched filenames.
4. **`RefsPanelModel`**: `tabsFilter: Bool`; `prepareForPresentation(source:)` ; ranking branch when `tabsFilter`; select frontmost id.
5. **`AppDelegate` hotkey switch:** `.refsHighlightsOpen` → `showRefs(source: .highlightsTakeover)`; `.refs` → `showRefs(source: .global)`.
6. **`RefsKeyRouter`:** ⌘6 toggles; Backspace/Esc peel Tabs.
7. **`RefsSearchBar`:** Tabs token; count `N tabs` while the filter is on.
8. **Banner / TCC:** first takeover without trust shows the prompt once per session, not on every keystroke.
9. **Tests:** matcher collisions and unique stems; model presentation source; key router; fake lister; design fixture for the token. No live Highlights in CI.

Out of scope for v1: walking each tab to harvest `AXDocument` (would steal the front document), Screen Recording, Apple Events, a bob JSON field, persisting Tabs across launches, page numbers on background tabs, clicking Window-menu items.

## 8. Risks

| Risk | Likelihood | Mitigation |
| --- | --- | --- |
| Highlights changes the AX tree (tab bar roles) | Medium over years; low for v1 | Role-based walk + filename unique-set; integration probe on the Mac in README |
| Accessibility denied | Certain on first launch | Degrade to current picker; banner |
| LaunchServices stops coalescing and opens a duplicate tab | Low (NSDocument + verified tonight) | Keep a test note; AXPress fallback if window count rises |
| Stem collision (`harness_engineering.pdf`) | One pair today | Show both; path match wins when `AXDocument` is known |
| Hardened runtime blocks AX | Low (app is unsandboxed; AX is not Apple Events) | Verify on the Mac after install; adhoc builds must be the same binary TCC granted |
| Panel resign-key vs AX | Low | Panel is already non-activating; AX worked with Chrome frontmost |
| Locale | Low if roles are used; high if Window-menu English is used | Do not parse "Window" / "Show Next Tab" |

## 9. Recommended solution

Ship **Tabs mode** in Bob Mac Capture as a presentation filter over the existing snapshot.

1. Split the takeover hotkey from the global hotkey. ⌘O in Highlights opens Bob Refs with Tabs on, front tab selected, type-to-filter among open documents. Return calls the existing Highlights opener, which already switches tabs and keeps the page.
2. Enumerate with `AXUIElement` on the Highlights PID (windows' `AXDocument` + tab-bar `AXTabButton` titles). Match to `RefItem.pdfPath` / `stem`. Leave `RefsCore` free of AppKit. Leave bob-cli unchanged.
3. ⌘6 toggles Tabs from the full library. Denied Accessibility or a quit Highlights never breaks today's picker.
4. Empty Tabs listing is tab order, not Today/Ready/Library browse sections. Unmatched open PDFs stay visible.

That is the smallest change that actually makes the panel a tab switcher. The request as a "filter that only shows matching reference notes" is the right instinct and the wrong default: bind it to the Highlights entry point, name it Tabs, and treat Highlights' live document set as the universe.

### Sources

- Live inspection, Kelly's MacBook Pro, 2026-10-15: Highlights 2026.1.2 (602), `net.highlightsapp.universal`; AX tree, Window menu, Open Recent, `lsof`, `CGWindowList`, `open -a Highlights` coalescing test; `bob ref list -R all -A -f json` (1033 refs, 431 with `source_pdf`).
- [Highlights FAQ](https://highlightsapp.net/faq/) ("Is Highlights scriptable? No, not yet."; prefer-tabs and window-restore are system settings). Fetched 2026-10-15; FAQ page stamped 2026-10-13.
- [Highlights Mac changelog](https://highlightsapp.net/changelog/mac/) (tabs since 1.5.1; `highlights://` URL scheme; 2026.2 Siri AI / macOS 27).
- bob-mac-capture: `HighlightsTakeover.swift`, `RefsHighlightsOpenKey.swift`, `WorkspaceRefsOpener`, `RefsPanelModel.prepareForPresentation`, `RefsKeyRouter`, `RefsRanker`, `RefItem.stem` / `pdfPath`, `AppDelegate` hotkey routing, `Resources/Info.plist` (`LSUIElement`).
- `decisions:mac-capture-is-a-thin-client`.
- Prior consolidated research: `research:202610/highlights_quick_open_refs_panel/highlights_quick_open_refs_panel__final.md`.
- Apple Developer Forums: Accessibility APIs are unsupported in sandboxed apps (threads 749494, 794253). Bob Mac Capture is not sandboxed.
