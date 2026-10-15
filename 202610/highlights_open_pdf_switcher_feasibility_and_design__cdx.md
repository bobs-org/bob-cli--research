# Highlights open-PDF switching in Bob Refs: feasibility, identity, and design

Researcher: **cdx**  
Date: **2026-10-15**  
Scope: Independent research and recommendation; no product code changed. No other report or researcher findings from this swarm were consulted.

## Assessment

**This is a useful addition to Bob Refs, and it is technically feasible on the Mac tested.** The important design choice is to make the new mode a view of **actual Highlights tabs**, enriched with reference-note information. Implementing it only as a filter over Bob's references risks an incomplete switcher and incorrect note associations.

The running Highlights instance provided unusually useful direct evidence: nine tabs, all discoverable through Accessibility, but only one document window and one full document URL. Every tab advertised an `AXPress` action. All nine tab filenames had exactly one candidate in Bob's PDF-backed reference library. This supports a small, native implementation. It also exposes the main limitation: **a background tab's filename is not proof of its file path**.

The technical recommendation is a Mac-owned Accessibility adapter, a separate “Open in Highlights” mode in the existing panel, and direct tab activation. Do not build an AppleScript document enumerator, infer openness from file handles, or put macOS application discovery into `bob-cli`.

## 1. Evidence and confidence

### 1.1 Repository baseline

I inspected these local checkouts, opened through `sase repo open`:

- `bob-mac-capture` at `9f58448a035b3592c2d7e5dbd5a3d0abf0a9f111`.
- `bob-cli` at `3f2b775a1d52eba29c2300ea96e6ae2ab9c33db0`.

Important existing behavior:

| Finding | Implementation evidence | Consequence |
| --- | --- | --- |
| Bob already supplies a complete library snapshot, including finished references. | `Sources/RefsCore/RefsFetching.swift`, `BobRefsFetcher.list`: `bob ref list -R all -A -f json`, schema 1. | No new CLI endpoint is required for the first version. |
| A reference row exposes `source_pdf`; the Mac converts it into a vault-relative `pdfPath`. | `RefsCore/RefsDecoding.swift`, `RefRecord`; `RefsCore/RefsModel.swift`, `RefItem.make`. | Join open documents to this existing identity, not to the human reference title. |
| The panel currently excludes records without a safe, nonempty `source_pdf`. | `RefItem.make`; `RefItem.isSafePDFPath`. | Ordinary references and switchable tabs are different universes of items. |
| The existing opener explicitly targets Highlights through `NSWorkspace`, with activation enabled. | `BobMacCapture/Refs/RefsPanelModel.swift`, `WorkspaceRefsOpener.openInHighlights`. | Existing library opening remains useful, but a tab switch needs a distinct target and failure policy. |
| Highlights is located by bundle identifier `net.highlightsapp.universal`, with a Settings app-path override. | `HighlightsLocator` in `RefsPanelModel.swift`. | Reuse the resolved target rather than matching process names. |
| The panel is nonactivating and does not call `NSApp.activate` when shown. | `BobMacCapture/Refs/RefsPanel.swift`, `show` and panel construction. | Showing the switcher can preserve Highlights as the frontmost app. |
| Command-O takeover while Highlights is frontmost already exists. | `HighlightsTakeover.swift`, `RefsHighlightsOpenKey.swift`, README “Opening Bob Refs”. | The feature needs no additional global shortcut to be useful. |
| Global Refs and Highlights takeover currently converge on the same `toggleRefs()` path. | `AppDelegate.swift`, hotkey dispatch. | Different defaults by entry point would require explicitly carrying entry context. |
| Opening the panel resets query and kind scope; rankings are frozen while visible. | `RefsPanelModel.prepareForPresentation`, `rerankSelectingFirst`, `libraryDidPublish`. | Add an independent mode and preserve stable selection rather than reordering on every observation. |
| “N open” currently means reading/next/ready reference states. | `RefsCore/RefsRanking.swift`, `RefsRanker.listing`; `RefsSearchBar.countText`. | This wording would become misleading beside a real application-open filter. |

The existing thin-client decision permits the Mac to filter and rank Bob's data and own native presentation/orchestration. A Mac Accessibility adapter fits that boundary: Bob still owns reference metadata and vault semantics; Swift owns the other application's live UI. The audited decision read was `decisions:mac-capture-is-a-thin-client`.

Source links: [Mac fetching contract](https://github.com/bobs-org/bob-mac-capture/blob/9f58448a035b3592c2d7e5dbd5a3d0abf0a9f111/Sources/RefsCore/RefsFetching.swift), [Mac model and opener](https://github.com/bobs-org/bob-mac-capture/blob/9f58448a035b3592c2d7e5dbd5a3d0abf0a9f111/Sources/BobMacCapture/Refs/RefsPanelModel.swift), [reference CLI contract](https://github.com/bobs-org/bob-cli/blob/3f2b775a1d52eba29c2300ea96e6ae2ab9c33db0/docs/ref.md).

### 1.2 Highlights' documented integration surface

Highlights' official FAQ answers whether the app is scriptable with **“No, not yet.”** It also documents native macOS document tabs and system-managed window restoration. Therefore a standard AppleScript `documents` collection cannot be assumed to exist, and restored documents must be rediscovered after app launch rather than reconstructed from Bob's open history. [Highlights FAQ](https://highlightsapp.net/faq/)

Apple documents `kAXDocumentAttribute` as the represented document's URL, encoded as a string. `kAXTabsAttribute` distinguishes a tab view's tabs from its other children. These are relevant public APIs; their availability in Highlights still needs direct observation. [Apple: document attribute](https://developer.apple.com/documentation/applicationservices/kaxdocumentattribute?language=objc), [Apple: tabs attribute](https://developer.apple.com/documentation/applicationservices/kaxtabsattribute?changes=_7)

### 1.3 Direct, read-only Mac observations

I connected to the configured `mac` SSH host and queried the **already-running** application. I did not open, close, select, reorder, or annotate any document, change permissions, or install an app. Short Swift probes imported AppKit and ApplicationServices and read Accessibility attributes. A separate read-only `bob ref list` supplied library metadata.

| Observation | Result |
| --- | --- |
| macOS | 26.5, build 25F71 |
| Installed Highlights | 2026.1.2; bundle identifier `net.highlightsapp.universal` |
| Running process found | Yes |
| Probe's Accessibility trust | `AXIsProcessTrusted() == true` |
| `AXWindows` | One `AXStandardWindow` |
| Window `AXDocument` | A full `file:///Users/.../bob/lib/...pdf` URL for the selected document |
| Window `AXTitle` | Filename plus a page indicator |
| Window `AXTabs` | Unsupported (`-25205`); querying only this would miss the tabs |
| Tab representation | A child `AXTabGroup`; its `AXTabs` contained nine elements |
| Individual tabs | `AXRadioButton` with subrole `AXTabButton` |
| Tab identity information | `AXTitle` and `AXHelp` both contained the PDF basename; the inspected tab attribute lists contained neither `AXDocument` nor `AXURL` |
| Selected tab | `AXValue == 1`; other tabs had `AXValue == 0` |
| Advertised tab actions | `AXPress`, `AXShowMenu` |
| Window menu | All nine documents appeared as filename plus page-indicator items; no path advantage over the tab bar was established |
| File-descriptor check | `lsof` reported 198 named open entries and **zero PDF descriptors**, despite nine live PDF tabs |
| Bob library returned | 1,033 reference records; 431 had `source_pdf` |
| Filename join | Each of the nine tab titles matched exactly one `source_pdf` basename among those 431 records |
| Single library-list duration | Approximately 266 ms, measured around the installed Bob subprocess and output collection |

Repeated structural discovery—windows, selected document URL, tab group, titles, and selected values—took approximately **28.2, 1.0, 0.9, 0.9, 0.9, 0.9, and 5.3 ms** across seven immediate runs. This excludes Swift startup, library fetching, enrichment, and rendering. It is evidence that lightweight discovery is promising, not a production latency guarantee.

`AXObserverCreate` succeeded. Registering window-created, focused-window-changed, destroyed-element, and title-changed notifications on the application, and selected-children/value/layout notifications on the tab group, returned success. **Registration success does not prove which notifications fire on each real operation.** Event delivery and coverage remain implementation validation work.

The installed bundle had no `.sdef`, `.scriptSuite`, or `.scriptTerminology` files in the search performed, and no `NSAppleScriptEnabled` Info.plist entry. The `sdef` command itself was unavailable with the Mac's Command Line Tools installation. These observations support the FAQ's warning but do not independently prove every possible Apple event is unsupported.

**Confidence limits:** The probe establishes discoverability of the present nine-tab session. It does not establish duplicate-name behavior, minimized windows, multiple tab groups, full-screen Spaces, hidden tab bars, app restoration timing, permission behavior of the signed Bob app, or successful `AXPress` activation. Those were deliberately not exercised on the user's live reading session. A current remote probe being trusted does not mean Bob Mac Capture has Accessibility permission.

## 2. Is this a good idea?

Yes, for a workflow that repeatedly returns to a modest working set of PDFs. Bob Refs already offers recognizable titles, search, keyboard navigation, note access, and an inspector. Reusing it avoids another launcher and connects reading context to notes. The existing Highlights-specific entry point makes the interaction especially natural.

There are three qualifications:

1. **A switcher is about current application state, not the reading queue.** A finished or abandoned reference may remain open for comparison. Its tab must not disappear because of reference status, age, Today membership, or a five-row “recently opened” cap.
2. **Opening a path and switching an existing tab are different actions.** The existing `NSWorkspace` opener opens URLs in a specified app; that API does not itself promise which existing Highlights tab is selected, whether a tab is reused, or whether the page stays unchanged. Directly target a discovered tab in the new mode. [Apple: opening URLs in a specified app](https://developer.apple.com/documentation/appkit/nsworkspace/open%28_%3Awithapplicationat%3Aconfiguration%3Acompletionhandler%3A%29?changes=____6%2C____6&language=objc%2Cobjc)
3. **The exact note-to-document join is the hard part.** Nine unique filename matches are encouraging for this library. They are not proof that an open `/Downloads/paper.pdf` is the same file as the only indexed `lib/papers/paper.pdf`.

For adjacent-tab navigation alone, native tab navigation is simpler. For searchable switching using Bob titles and context, this addition is worthwhile. I would not replace Highlights or add an independent window-switcher application just for this need.

## 3. Implementation approaches compared

| Approach | Strength | Limitation | Judgment |
| --- | --- | --- | --- |
| AppleScript/JXA document enumeration | Would offer the cleanest document-level model if supported | Highlights explicitly says it is not scriptable; scripting syntax cannot manufacture an absent API | Reject as the implementation premise |
| Native Accessibility tab discovery and activation | Observed all nine real tabs; selected URL; exact UI target; public API | Requires Accessibility permission; background tabs exposed filenames rather than paths; OS/app compatibility testing | **Best current mechanism** |
| Accessibility Window-menu scraping | Observed all nine document names; useful when tab-bar structure is absent | Page suffixes, localization, duplicate names; no demonstrated background full paths | Possible narrowly tested fallback, not the primary provider |
| Existing `NSWorkspace` opener after filtering | Already implemented and explicit about the app | Requires a trustworthy PDF identity and may reopen a stale tab's document; target-app reuse behavior needs testing | Retain for Library mode, not default switch semantics |
| `lsof` / process file descriptors | Easy prototype, apparently path-based | Failed to show any PDF in the actual nine-tab session; resource lifetime is not document lifetime | Reject |
| Core Graphics window lists | Useful for visible-window management | A window list is not a tab list; app-specific document URLs still absent | Reject as the source of open-PDF membership |
| Recent documents, Spotlight last-used, Bob open history | Existing infrastructure; no new live observer | Cannot tell whether a document was closed or opened outside Bob | Use only as history/ranking signals |
| Saved application state or undocumented bookmark stores | Might contain names or paths | Restoration artifacts are not an authoritative live document list; private formats and delayed updates | Do not ship against these |
| Track only PDFs opened through Bob | Very easy to add | Misses Finder opens, restored tabs, and closures in Highlights | Does not satisfy this request |
| Ask the Highlights developer for a document/activation API | Could eventually remove identity and compatibility uncertainty | No such supported contract was established in this research | Worth considering separately; do not block the first version |

The decisive distinction is that Accessibility gives a real **tab target**, even when it cannot give a full file identity. A switcher can safely select that target without guessing a path.

## 4. Requirements I would adjust

These are explicit proposed changes to the original “only reference notes whose PDFs are open” formulation.

### A. Show open PDF tabs, with optional reference enrichment

**Recommended adjustment:** In the new mode, show every discoverable open PDF tab. Use reference-note metadata when the association is confirmed; keep an unmatched or ambiguous tab as a plain filename row. A narrow strict-reference filter could remain an alternative, but then show coverage such as “7 linked references · 2 other tabs” so the user knows it is incomplete.

Why: the user goal is a reliable tab switcher. A PDF opened before scanning, outside the vault, or with a duplicate basename should still be switchable. Switching it must not create a reference, run `bob ref scan`, or mutate the vault.

This is a small product expansion, but it does require an explicit tab row type rather than pretending every row is a `RefItem`.

### B. Return means “switch this existing tab”

Do not reopen a file, silently open Obsidian, or fall back to the default PDF application when a switch target disappears. Report that it closed and refresh. An explicit “Open the reference PDF” action can be available on a confirmed reference if desired.

Why: otherwise a stale list violates the promise of “currently open” and may reopen something the user intentionally closed.

### C. Treat full paths and inferred filename matches differently

A single basename candidate may help identify a tab in this personal library, but it is an **inference**, not a verified relationship. Do not expose another PDF's annotations or jump to its note as though the association were certain.

A practical policy is:

- Confirmed full-URL match: show the normal reference title, inspector, and note actions.
- Unique basename candidate: keep the actual tab filename as the primary identity; optionally show the candidate reference title as a tentative secondary label. Note/annotation enrichment waits for verification.
- No candidate or several candidates: plain tab row; switching still works.

After an explicit user switch, read the selected window's `AXDocument` URL and verify the association. Keep that association in memory for the lifetime of the current tab/process observation. This gradually gives normal rich titles to background tabs without cycling through them automatically.

If Bryan prefers immediate full-title enrichment from unique basename matches, make that an acknowledged convenience tradeoff. It should still activate the tab object and should never silently choose between duplicate candidates.

### D. Define freshness as a snapshot on invocation, with safe invalidation

Discover on each panel open and explicit refresh. While the panel is visible, invalidate closed targets and refresh facts without moving rows underneath the keyboard selection. Newly discovered tabs can appear at the next deliberate refresh/open.

Why: this preserves the panel's existing stable-list behavior. It is a slight relaxation of a continuously reordered live list, with much more predictable keyboard navigation.

### E. Make the mode explicit and distinguish “open” meanings

Use a visible “Library / Open in Highlights” choice. Keep the existing kind filters as an independent dimension; the new mode is not another kind beside Papers or Chats. Default to Library until the user explicitly chooses otherwise, and remember the chosen mode across panel invocations so repeated switching is fast.

Use wording such as “9 tabs in Highlights” in the new mode. Rename the current library count to something like “N in reading queue” rather than using one “open” label for two unrelated concepts.

## 5. Proposed architecture

### 5.1 Mac-only live document service

Introduce a small injectable protocol, for example `HighlightsSessionProviding`, in the macOS layer. Its implementation should:

1. Resolve the target app using the existing locator and use its running PID. Never launch Highlights merely to discover whether it has documents open.
2. Check Accessibility trust without prompting on ordinary panel startup. Request permission only from an explicit Enable/Open Tabs action.
3. Enumerate document windows, read their `AXDocument`, and inspect structural tab groups and their `AXTabs`. Do not assume a top-level window has `AXTabs` itself—the live check demonstrated that it does not.
4. Read tab titles, selected state, and supported actions. Retain native target handles privately inside the service. Publish plain immutable row data to the model.
5. Handle standalone document windows too. A tab group is not required for a document to be switchable.
6. Deduplicate window/tab representations carefully. A window's selected document and its selected tab normally represent one switch target, not two rows.

A result should distinguish `ready`, `notRunning`, `permissionRequired`, `temporarilyUnavailable`, and `unsupportedLayout`; an empty successful result means no discoverable documents, not permission failure. Include a process generation and observation generation so stale async results cannot replace a newer session.

Keep foreign AX objects within one serialized macOS service rather than adding unchecked sendability across Swift concurrency boundaries. Discovery must run off the main UI path. Use a small global AX messaging timeout and an overall work budget: a timeout for every element can otherwise multiply into a long stall. Apple exposes `AXUIElementSetMessagingTimeout` for controlling these calls. [Apple: AX messaging timeout](https://developer.apple.com/documentation/applicationservices/1459345-axuielementsetmessagingtimeout?changes=l_4)

This design needs **no new Bob CLI flags, vault fields, persisted open-state file, or daemon**. Existing Bob JSON remains the authoritative source of reference information.

### 5.2 Identity resolution

Build a reverse index over existing `source_pdf` values resolved through `RefsLibrary.pdfURL(for:)`.

- Parse `AXDocument` as a URL and accept file URLs for path matching; decode URL escapes through Foundation.
- Standardize paths, resolve symlinks where available, and compare actual file identity when useful. Do not blindly lowercase paths because macOS can use case-sensitive volumes.
- Preserve the existing safe-vault-path checks for reference paths.
- Index exact basenames separately for tentative matching. Never fuzzy-match reference titles to establish file identity.
- Model one PDF mapping to multiple reference notes as an ambiguity rather than collapsing a dictionary entry arbitrarily.
- Keep native tab identity separate from reference-note identity. Reordered tabs must not change targets, and tab indices must never be used as durable identifiers.

Full-path matches and verified native handles should survive ordinary list filtering. Clear or revalidate learned associations when the app restarts, a tab is destroyed, its title changes, or the library's PDF path changes. Do not persist native handles or claim a previous app session's tab membership is current.

### 5.3 Activate the discovered UI target

For a tab, revalidate the retained target against the latest process/session, then request the tab's advertised `AXPress`. For a standalone window, use a tested raise/activation path. Bring the correct app/window forward when invoked globally; do not assume Highlights was already frontmost.

Hide the panel at the point needed for focus transfer, retaining its state for an error re-show. After the switch settles, verify selected state and, where possible, the selected `AXDocument` URL. `AXPress` being advertised and returning success is weaker evidence than observing that the expected target became selected. Apple explicitly notes that AX actions can time out during modal processing. [Apple: performing an AX action](https://developer.apple.com/documentation/applicationservices/1462091-axuielementperformaction?changes=_8)

Never automatically send key sequences to cycle through every tab to collect URLs. That would interrupt reading, alter the active document, and make discovery visible.

### 5.4 Refresh and caching

Start with fresh discovery on show and refresh. Given the measured cost, this does not justify a persistent background scanner. A cached in-memory snapshot may paint immediately while refreshing, but stale targets must be disabled or revalidated before activation.

A compact `AXObserver` can later invalidate the cache or learn full paths when the user naturally changes tabs in Highlights. The live registration results make this plausible, but validate actual notifications before relying on them. Reattach observers after PID changes and new tab groups. Use notifications as invalidation hints; take a structural snapshot as the authority. [Apple: Accessibility observers](https://developer.apple.com/documentation/applicationservices/1460133-axobservercreate?changes=_4)

No idle polling is necessary for the first release. If real event coverage requires a fallback, bound it to visible-panel use and stop it on hide.

### 5.5 Panel integration

Likely changes, all within `bob-mac-capture`:

| Area | Suggested responsibility |
| --- | --- |
| New macOS Highlights session adapter | Native discovery, trust status, process lifecycle, native target storage, activation |
| `RefsCore` | Pure tab snapshot, association-confidence, filtering, stable selection and ordering policy |
| `RefsPanelModel.swift` | Independent library/open mode, row kinds, selection, loading/error state, dispatch to switch or open |
| `RefsPanel.swift` | Start discovery on show; cancel/coalesce on hide; preserve current nonactivating presentation |
| `RefsSearchBar.swift`, footer, row/inspector views | Explicit mode, counts, basic tab rows, tentative association treatment, useful empty/error states |
| `RefsKeyRouter.swift` | One in-panel toggle, potentially Command-0, after checking reserved keys; retain Command-1 through Command-5 kind scopes |
| Settings and app lifecycle wiring | Explicit permission enable action; optional preference persistence; resolved-app changes invalidate the service |

Prefer native tab order within each window, with the frontmost group first, in an empty-query switcher. Do not use reading-lane sections or frecency to bury a live tab. Search can reuse Bob's textual matching on verified metadata, with native order as a stable tie-breaker; avoid reusing reading-state priors that are irrelevant to switching.

Kind filtering can include only confidently classified rows and explain when unclassified tabs are excluded. The default All view must retain every discoverable PDF tab. A selected/current badge helps orientation. Do not add tab closing, rearranging, multi-select, session restoration, or an MRU-navigation gesture to the first version.

## 6. Permissions and failure behavior

The new mode requires Accessibility access for **Bob Mac Capture itself**. Ordinary library browsing should remain available when access is denied. An explicit mode-selection action should explain why access is needed and offer a route to System Settings. Apple supports checking trust without prompting; its prompt option is asynchronous and does not change the immediate return value. [Apple: checking Accessibility trust](https://developer.apple.com/documentation/applicationservices/1459186-axisprocesstrustedwithoptions?changes=l_4)

Expected user-facing states include:

- “Highlights is not running.” Do not auto-launch it to discover an empty session.
- “Enable Accessibility access to show Highlights tabs.” Do not show a misleading zero count.
- “No PDFs are open in Highlights.” Only after a successful discovery.
- “Couldn’t read Highlights tabs. Retry.” Preserve a useful diagnostic without exposing document contents.
- “This tab closed. Refresh to update the list.” Do not open a replacement at the same index.
- Plain filename rows when the PDF has no verified Bob note. Do not turn a missing association into an import action.

Native Accessibility avoids adding an AppleScript/System Events subprocess and an unnecessary Automation-permission dependency. The signed/installed app's permission behavior still needs manual verification; a trusted SSH Swift probe is not a packaging test. Keep an unsupported app-path override honest: the existing opener can open a PDF in another configured app, but that does not promise its UI has the same tab structure.

## 7. Validation before shipping

First, a small scratch prototype should exercise discovery and activation against fixture PDFs in a **separate test session**, including two directories containing the same basename. This is the highest-value experiment still outstanding. Do not infer successful activation from the read-only probe.

Required behavior checks:

1. All nine presently observed tabs are represented in All, without activating any tab during discovery. Unique filename associations are tentative until path verification.
2. Selected and background tabs; one standalone window; several windows/tab groups; hidden tab bars; minimized windows; full-screen/other Spaces. Record any unsupported cases rather than broadening the promise without evidence.
3. A PDF outside the vault and a PDF not yet indexed by Bob remain switchable. Two same-basename PDFs never silently inherit each other's note or annotations.
4. Close or reorder a target between discovery and Return. A selected row must never switch whichever tab moved into its former index or reopen a closed PDF.
5. Switching preserves page position and existing annotations, creates no duplicate tab, and works from a global invocation when Highlights is backgrounded. Fail visibly if the target cannot be made active.
6. Permission denied/revoked, Highlights quit/relaunch, an unsupported override app, modal dialogs, and AX timeouts do not freeze the panel or disable Library mode.
7. Reference status, Today, scans, and late library refreshes cannot hide or reorder live targets unexpectedly. Note navigation and copy actions require the right association confidence.
8. Query/IME behavior, Escape, retained Capture drafts, nonactivating panel behavior, and existing hotkeys continue to work. Repeated invocation returns to the explicitly chosen mode.

Add pure tests for identity confidence, duplicate and unmatched cases, snapshot generations, stale-target selection, and mode/count policies. Use fakes for the native adapter. Then compile and test macOS integration: this repository's `AGENTS.md` forbids landing uncompiled Swift, requires `just portable-check` on non-Xcode hosts, and calls for scratch-copy `bundle.sh` plus `just typecheck-tests` on the Mac when changing macOS targets. Inspect the actual build command locations when implementing; never deploy the research prototype into Bryan's checkout or run `just install` there. A GUI/permission smoke test is still necessary even when CI is green.

Production signposts should separately measure discovery, association, first usable rows, and activation verification. Suggested targets are sub-100-ms warm discovery and no synchronous UI wait; those are proposed engineering targets, not measured end-to-end performance.

## 8. Reproducible observation recipe

These are investigation steps, not claims about an API contract for future versions:

1. Read Highlights bundle version and identifier with `PlistBuddy`.
2. Query `NSRunningApplication.runningApplications(withBundleIdentifier:)`; do not launch an application.
3. Check `AXIsProcessTrusted()` without setting a prompt option.
4. Create an application AX object from its PID and read `AXWindows`.
5. On each window read `AXDocument`, `AXTitle`, and immediate structural children.
6. Find `AXTabGroup`, then read its `AXTabs`. Read each tab's `AXTitle`, `AXHelp`, `AXValue`, advertised attributes, and advertised actions.
7. Run `bob ref list -R all -A -f json`; join only for analysis using exact `source_pdf` basenames, recording candidate counts rather than presuming full identity.
8. Optionally register observer notifications in the short-lived probe, recording return codes separately from event-delivery evidence.

Minimal read-only discovery core:

```swift
import AppKit
import ApplicationServices

func attribute(_ element: AXUIElement, _ key: String) -> CFTypeRef? {
    var value: CFTypeRef?
    guard AXUIElementCopyAttributeValue(element, key as CFString, &value)
        == .success else { return nil }
    return value
}

// Prototype guard only; production reports an explicit status to the panel.
guard AXIsProcessTrusted(),
      let app = NSRunningApplication.runningApplications(
          withBundleIdentifier: "net.highlightsapp.universal"
      ).first else { exit(0) }

let root = AXUIElementCreateApplication(app.processIdentifier)
AXUIElementSetMessagingTimeout(AXUIElementCreateSystemWide(), 0.4)
let windows = attribute(root, "AXWindows") as? [AXUIElement] ?? []
for window in windows {
    let selectedURL = attribute(window, "AXDocument") as? String
    let children = attribute(window, "AXChildren") as? [AXUIElement] ?? []
    for group in children
        where attribute(group, "AXRole") as? String == "AXTabGroup" {
        let tabs = attribute(group, "AXTabs") as? [AXUIElement] ?? []
        for tab in tabs {
            let filename = attribute(tab, "AXTitle") as? String
            let selected = attribute(tab, "AXValue") as? NSNumber
            // Return snapshot data; retain native targets inside the service.
            _ = (selectedURL, filename, selected)
        }
    }
}
```

The immediate-child layout was observed in this installed version. Production needs a bounded structural search and explicit unsupported-layout handling, not an unbounded recursive scan through PDF text/annotation accessibility nodes. Personal document names and contents are intentionally omitted from this report.

## 9. Recommended solution

**Build an explicit “Open in Highlights” mode in the existing Bob Refs panel, using a small native Accessibility service to enumerate and activate actual tabs/windows. Keep Bob's existing JSON snapshot for reference enrichment and retain ordinary Library mode.**

Make the mode tab-first: confirmed reference links get the rich Bob presentation; background filename matches stay tentative until verified; unmatched and ambiguous PDFs remain switchable as plain rows. Return should select the discovered native target and never silently reopen a closed PDF. Refresh on invocation, preserve stable keyboard selection, and require Accessibility only when the user opts into this mode.

This is a good fit for the current application and the observed nine-tab reading session. The justified requirement change is that completeness as a tab switcher takes precedence over hiding every PDF without a confidently identified reference note. Validate direct activation, duplicate names, and multiple-window/Space behavior in a small Mac prototype before committing to the complete UI. If the scope must remain a strict reference-only filter, retain the same AX discovery and activation design, expose its coverage limits, and do not present inferred filename matches as proven file identity.
