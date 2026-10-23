# Safe PDF marker updates while Highlights is open

Independent research by **cdx**, 2026-10-23. Scope: design research; no production code, settings, live PDFs, annotations, or tabs were changed. No other report or findings from this research swarm were consulted.

**Recommendation:** investigate and validate macOS **`NSFileCoordinator` with `.forMerging`** as the primary solution. It provides a native save-before-write handshake and may let Highlights refresh without closing its tab. When safe coordination cannot be established, defer the affected PDF update and explain why. Do **not** make unattended keystroke-driven save/close/reopen the default.

This is a recommendation for an architecture and a bounded validation experiment, **not a claim that Highlights has already passed that experiment**. Static inspection of the installed app makes native coordination promising; actual save, reload, and ongoing-edit behavior remains untested.

## 1. What is happening

Bob's `status:` is inside the contents of a page-one PDF text annotation. Updating it is a PDF content mutation, even though it looks like a tiny metadata change. The writer loads the PDF with `lopdf`, changes the annotation's `Contents`, saves a temporary PDF, fsyncs it, and renames it over the original path. It is not an extended-attribute update or a separate marker file. [Code: `bob-cli`, `src/native/highlights_ref/marker.rs:152–217`.]

That creates two versions of the document:

```text
Highlights: an open document, possibly containing annotations not yet saved
Filesystem: a newly installed PDF containing Bob's marker update
```

The reported conflict is consistent with Highlights trying to save its older in-memory document after this replacement. The replacement mechanism is confirmed in code; the exact Highlights conflict implementation was not instrumented or reproduced during this research.

Bob already has meaningful safeguards:

- Full scans serialize Bob maintenance and scanning with `bob_sync.lock → scan.lock`.
- The planner records a SHA-256 digest of the PDF bytes it parsed.
- The executor checks that digest again before marker writes.
- Git dirty-target checks protect existing vault files.
- PDF write-back requires `scan -w/--write-pdfs` or `sync -w/--write-pdf`. A plain scan is not implicitly authorized to rewrite markers.

These checks protect against several disk races, but neither a clean Git tree nor an unchanged file digest proves there are no pending edits in Highlights. The locks also do not serialize Highlights. There is still a check/read/write interval involving an independent application. [Code: `sync.rs:57`, `sync.rs:2009`, `guard.rs:99`; documentation: `docs/highlights-ref-sync.md`, “Round-trip” and scan locking.]

The documented Mac cron job runs `maybe_bob_highlights_sync -w` every 15 minutes. The wrapper invokes the legacy `bob highlights scan` alias and suppresses successful output. Bob Refs also invokes `bob ref scan -w -f json`. Thus a fix only in the Mac panel, or only in the cron wrapper, would leave another entry point exposed. The cron schedule was confirmed in repository documentation, not by inspecting the live crontab. [Sources: `docs/vault-git-sync.md:169`; chezmoi `home/bin/executable_maybe_bob_highlights_sync:116`; `docs/reference/mac-capture/refs.md:48`.]

## 2. Evidence from the actual Mac

Read-only SSH inspection of the installed app produced:

| Item | Observed value |
| --- | --- |
| macOS | 26.5, build 25F71 |
| Highlights version | 2026.1.2, build 602 |
| Bundle identifier | `net.highlightsapp.universal` |
| PDF document class in `Info.plist` | `Highlights.Document` |
| Related Markdown/TextBundle types | Also declare `Highlights.Document`, with `NSIsRelatedItemType` enabled |
| Scripting metadata | No `NSAppleScriptEnabled`, `OSAScriptingDefinition`, or `NSScriptingDefinition` key |
| Bundled scripting resources | No `.sdef`, `.scriptSuite`, or `.scriptTerminology` files found |

The `sdef` command itself could not run: this Mac has Command Line Tools, and that tool requested full Xcode. The independent bundle-resource inspection succeeded. Absence of those resources is **not proof that every Apple event is unsupported**. It does mean there is no inspected, supported document dictionary on which to base a promise that `save document …` or `close document … saving yes` will work.

Declaring a document class is good evidence that the app uses Cocoa's document architecture. Apple documents that `NSDocument` implements file-presenter behavior. It does **not** prove that this particular subclass handles external saves, annotation editors, reload, or sidecars correctly. Those are the central validation questions. [Apple: [NSDocument](https://developer.apple.com/documentation/appkit/nsdocument/), [file coordinators and presenters](https://developer.apple.com/library/archive/documentation/FileManagement/Conceptual/FileSystemProgrammingGuide/FileCoordinators/FileCoordinators.html).]

The public [Mac release notes](https://highlightsapp.net/changelog/mac/) list a later 2026.2 release. I found no verified claim there that upgrading fixes this conflict. Test the installed version and the intended deployment version; do not substitute an upgrade assumption for the experiment.

No Apple events, simulated keystrokes, Accessibility actions, coordinated writes, application launches, or save/reload experiments were sent to Highlights during this investigation. Its live working documents were left alone.

## 3. Critique of save, close, modify, reopen

The intuition is reasonable: an application that reloads the new PDF should stop using the old snapshot. The ordering, however, is essential:

```text
identify document → save and confirm → close and confirm
→ reread and replan → mutate PDF → reopen and verify
```

Saving **after** Bob has replaced the PDF is too late: that is precisely when the existing conflict can appear. Reopening the same URL while the tab remains open may simply select the old document. Closing before confirmed saving can discard the user's work.

Automatic tab cycling also introduces costs that a background status update should avoid:

1. **Saving is an operation, not a keystroke.** Cmd-S can encounter a conflict, read-only error, permission prompt, or unfinished annotation popover. A returned key event and a one-second delay are not acknowledgements that all annotations reached disk. A disabled Save menu or stable mtime alone is also insufficient.
2. **The correct document must be identified.** Titles can collide, change, or omit paths. Tabs can move between discovery and action. One document may have multiple windows.
3. **The reading context can be lost.** Page, scroll, zoom, selection, active annotation, undo history, tab grouping, fullscreen state, and frontmost application matter. Reopening a URL does not establish restoration of these states.
4. **The user can keep editing.** An automation that selects a tab and issues Cmd-S/Cmd-W races with the user's input and focus changes.
5. **A modal sheet must stop automation.** It must never guess “Replace,” “Discard,” “Revert,” or “Don't Save.” A stale document already in conflict is a recovery case, not a safe save-and-close candidate.
6. **Failure can strand the document.** If the process dies after close, the user has a missing tab. If it dies after the write but before reopen, retrying blindly can repeat mutations or lose restoration information.

Apple explicitly describes UI scripting as a fallback requiring Accessibility access and inspection of an application's UI hierarchy. That is a real maintenance and deployment cost for scheduled scans. [Apple: [Automating the User Interface](https://developer.apple.com/library/archive/documentation/LanguagesUtilities/Conceptual/MacAutomationScriptingGuide/AutomatetheUserInterface.html).]

### Existing tab support is useful, but not enough

Bob Mac Capture already has `AXHighlightsTabsReader`. It reads tabs without launching Highlights, checks Accessibility trust without prompting, bounds messaging time, rechecks targets, closes tabs, and recognizes situations needing attention. Reusing its infrastructure is better than writing an unrelated shell script.

However, its snapshot attaches the window's `AXDocument` path **only to the selected tab**; inactive tabs have a name and `documentPath: nil`. Its close machinery also uses filename counts and may select a tab before closing it. These are useful for explicit human tab actions, but are not yet sufficient evidence of exact-file identity for unattended document mutation. [Code: `bob-mac-capture`, `Sources/BobMacCapture/Refs/AXHighlightsTabsReader.swift:448–525`, close path starting at line 143.]

A background writer must not resolve an ambiguous basename by taking the first match. `lsof` is not a reliable substitute: a document app can keep an in-memory document after closing its file descriptor. Neither “no fd found” nor a failed Accessibility read means “safe to overwrite.”

## 4. The more promising native mechanism

`NSFileCoordinator` coordinates access with registered file presenters, including presenters in other processes. Low-level reads and writes bypass that protocol. Native coordination is therefore directly relevant to the gap in Bob's current writer. [Apple: [NSFileCoordinator](https://developer.apple.com/documentation/foundation/nsfilecoordinator), [NSFilePresenter](https://developer.apple.com/documentation/foundation/nsfilepresenter).]

The crucial option is **`.forMerging`**. Apple says this requests the presenters' save callback before the external writer acts. The save callback has a completion result; an error preparing access should prevent the accessor from running. The name does not mean macOS merges arbitrary PDF contents: Bob still owns its normal marker reconciliation. [Apple: [forMerging](https://developer.apple.com/documentation/foundation/nsfilecoordinator/writingoptions/formerging), [savePresentedItemChanges](https://developer.apple.com/documentation/foundation/nsfilepresenter/savepresenteditemchanges%28completionhandler%3A%29).]

**Do not use `.forReplacing` simply because Bob installs a temporary file by rename.** Apple distinguishes changing the contents of an existing document from replacing it with a different document. The Mac's installed `NSFileCoordinator.h` explicitly covers the write-temporary-file-and-rename case as a content update. `.forReplacing` uses deletion-like presenter behavior and can ask the existing document to accommodate replacement. Use `.forMerging` for this save-before-update experiment, not a combination of the two options. [Apple: [forReplacing](https://developer.apple.com/documentation/foundation/nsfilecoordinator/writingoptions/forreplacing); installed Foundation SDK header, `NSFileCoordinatorWritingOptions`.]

Conceptually:

```text
Bob's candidate plan
    ↓
Request coordinated content update with .forMerging
    ↓
Highlights gets a chance to save; preparation must succeed
    ↓
Inside the granted accessor: validate current PDF and other inputs
    ├── changed / dirty / conflict → no Bob write; defer or replan
    └── still valid → perform existing marker update under coordination
    ↓
Release access; Highlights receives the relevant change notification
    ↓
Report the actual outcome
```

This can avoid focus changes, tab reconstruction, global save-all, and Accessibility permission. It is a protocol with cooperating apps, not a universal lock against arbitrary processes. Success also does not report “Highlights saved three annotations”: there may be no presenter, or no changes to save. Product copy must not claim that fact without additional evidence.

### What still needs proof

- Does Highlights flush a comment while its popover remains open, or only annotations already committed into its document model?
- Does it reload Bob's content update and allow the next annotation save without conflict?
- Does it preserve recent edits made while the writer is waiting or executing?
- Does the PDF save callback finish before the Markdown/TextBundle sidecar has finished changing?
- Does the handshake work from cron, a shell, and the Bob Refs subprocess equally well?
- Are page, zoom, scroll, active tab, and undo behavior acceptable after reload?

A returned coordinator call cannot answer all of these questions. They need a controlled Mac experiment with disposable documents. Until that passes, do not enable writes to live open documents on the strength of the app's `NSDocumentClass` alone.

## 5. Comparing the alternatives

| Approach | Main benefit | Main cost or failure mode | Judgment |
| --- | --- | --- | --- |
| Unattended Cmd-S, close, write, reopen | Fits the proposed workaround | Focus, identity, save confirmation, restoration, and permission races | Reject as default |
| Native `.forMerging` coordination | Save handshake and change notification without tab cycling | Highlights-specific behavior must be verified; native integration required | Preferred experiment and intended architecture |
| Defer writes to open/unknown documents | Preserves current reading session | PDF status can lag; exact open-document detection may be incomplete | Mandatory fallback |
| Stop mirroring mutable status into PDFs | Removes the common reason to mutate an open PDF | Changes the round-trip contract and standalone PDF meaning | Sensible separate product decision, not a silent fix |
| Change bytes in place / incremental PDF append | May reduce replacement or file churn | Does not make Highlights' in-memory state current or save pending annotations | Not a concurrency solution |
| Quit and relaunch Highlights | Avoids identifying an individual tab | Interrupts all documents; broad save/restore failures | Reject |
| Pre-scan save-all hook | Small amount of code | Gap between save and write, affects unrelated docs, no paired cleanup | Insufficient |

The existing pre-scan hook runs before intake and discovery, before Bob knows which PDFs need marker changes. It has no transaction tied to each affected document. App coordination belongs at the actual write boundary. `--no-hooks` must never become a way to bypass the safety mechanism.

Deferral needs honest detection. For an unsupported/unvalidated Highlights version, the conservative initial behavior can defer all marker writes while the Highlights process is running, unless an independently reliable exact-document check is available. That is broader than ideal but safer than treating incomplete tab data as proof of absence. A process check alone still has an app-start race; it is an interim mitigation, not the final synchronization protocol.

Dropping PDF status write-back is a larger design option. It trades live status portability and marker-side editing for a single owner of lifecycle state. It requires an explicit reconciliation/migration decision: simply ignoring status writes while continuing to advance the stored synchronization base would be incorrect. I would not combine that contract change with this focused repair.

## 6. Recommended behavior and implementation boundaries

### A. Preserve the current authority and opt-in rules

Keep reconciliation and vault mutation in bob-cli. macOS coordination should be a narrow platform adapter invoked by the common per-PDF execution path, shared by human and JSON scans and targeted sync. Bob Mac Capture renders outcomes and owns UI interactions. This respects the existing thin-client decision.

Do not introduce a new public “refresh Highlights” switch for ordinary safe behavior. Existing `-w` continues to authorize PDF writes; it never implies permission to discard annotations. Dry-run remains genuinely observational: no save request, tab action, notification, or write. Even a native coordinated read can request a save by default, so do not accidentally use that in dry-run.

Both v1 and v2 note branches matter. The v2 executor writes reading-task and routed-note changes before the marker. A guard added only inside `atomic_save_pdf` is too late to defer the whole reference operation cleanly. Enter the coordination/precondition phase **before any per-PDF v2 writes**. Keep the shared low-level PDF writer covered too, but do not confuse a safe final rename with a safe multi-file operation. [Code: `sync.rs:1272`, `sync.rs:1597`.]

Avoid a helper process that takes Bob's locks again while its parent holds them. Prefer a small macOS Foundation bridge callable from the existing execution layer. The macOS-specific dependency boundary already exists in `Cargo.toml`, and CI includes macOS. The Rust implementation remains the only marker/planning implementation; a Swift or Objective-C bridge must not grow a second PDF reconciliation engine.

### B. Saving invalidates old plans

Requesting an app save can change the PDF, sidecar, object IDs, and Git status. A critical invariant is:

> Never write using the old annotation object ID or rendered plan after a save changed its source bytes.

The first implementation can safely return a typed `source_changed_after_save` deferral and let the next scan build a new plan. That is preferable to a complicated immediate retry that forgets scan-wide annotation-task deduplication, output collisions, or reserved IDs. If immediate retry is later added, rebuild the relevant scan context and rerun all affected finalization and write guards; do not just replace the expected digest.

Perform current-byte validation inside the granted accessor. Use the coordinator-provided URL, but refuse an unexpected move outside the planned library target and replan instead of continuing with stale note paths. Retain the existing digest checks and atomic temporary-file installation. File coordination complements those protections.

The Git guard is a separate constraint: a successful Highlights save can make the target dirty. **Do not whitelist arbitrary dirty PDF bytes to make this feature seem seamless.** Preserve the saved annotations, defer Bob's mutation, and let the normal vault-sync cycle commit them before a later scan. The maintenance lock prevents that sync from running concurrently, so waiting indefinitely for it while holding the lock would deadlock the intended progress. Release locks normally and retry later. An automatic scoped commit would be a separate policy change requiring a careful design.

### C. Treat annotation sidecars as owned by Highlights

The vendor documents sidecar generation during PDF save/autosave and says external sidecar edits are overwritten. Do not “fix” this by editing the Markdown/TextBundle that Highlights owns. [Highlights: [Autosave notes as sidecar files](https://highlightsapp.net/how-to/mac/sidecar-files/).]

After a forced/native save, reread the sidecar and affected assets before deriving note content. Snapshot and revalidate inputs, and defer/retry unstable input. Two matching observations are a useful readiness check, not proof of a cross-file atomic transaction. The real-app experiment must establish the save/sidecar ordering. Bob's documentation also records a TextBundle creation limitation for image selections; a missing bundle must not be mistaken for a successful complete annotation export. [Local source: `docs/highlights-ref-sync.md`, “Known Highlights TextBundle Creation Bug”.]

For the conservative first release, defer the entire affected per-PDF sync plan when coordination cannot proceed. Continue other eligible PDFs. Do not advance `highlights_marker_base`, the marker hash, or synchronization timestamps for the deferred plan. The existing `status_sync: pending` concept can continue to represent the outstanding status reconciliation. Safely splitting annotation import from deferred marker write-back is possible, but is additional design work, not a free consequence of skipping the PDF write.

### D. Bounded operations and truthful recovery

Set a measured per-document coordination deadline and a scan-level waiting budget; do not let one unresponsive application hold maintenance locks for the entire scan timeout. A first trial could use a few seconds per document, tuned using large-PDF measurements.

Cancellation needs a real state machine: before the accessor starts, cancel means no Bob write; after it starts, cancellation does not undo filesystem effects. Apple warns that cancellation can race with an already-running accessor. Check cancellation at the write boundary and report actual completion or partial failure. Never time out a wrapper and leave its worker free to write later. [Primary evidence: installed Foundation SDK `NSFileCoordinator.h`, cancellation comments; [Apple cancel API](https://developer.apple.com/documentation/foundation/nsfilecoordinator/cancel()).]

Preserve the current handling of partial multi-file execution failures rather than claiming the whole reference is atomic. Report the PDF's actual post-write hash and whether note finalization succeeded. A scan retry must converge without duplicated follow-up tasks.

No error, unsupported version, failed save, or denied permission should fall back silently to today's uncoordinated PDF overwrite.

### E. Report pending work without breaking old clients

Current scan JSON is schema version 1. The Mac decoder ignores unknown fields, but the outcome logic treats `ok: false` or any failures as partial. A compatible first extension can add structured reason/outcome details while retaining a `failures` entry and exit 1 for an unfulfilled requested write. Older clients then see an understandable partial result; newer ones can present a calm waiting state. Preserve existing summary counts rather than counting deferrals as completed marker writes.

Suggested per-PDF reason values are `document_busy`, `save_failed`, `source_changed_after_save`, `dirty_after_save`, and `coordination_unavailable`. These are proposed additions, not existing API fields. Keep any new deferred-write collection distinct from `queued`, which currently describes intake-only work. Make additions optional in the Swift decoder; do not gratuitously bump a schema version that old clients reject. If implementation changes existing exit semantics or field meanings, treat that as a contract change rather than calling it additive. [Code: `scan_json.rs:106`; `bob-mac-capture/Sources/RefsCore/RefsScan.swift:11`, `RefsScanOutcome`.]

Expose readiness through the existing `bob ref doctor`: detected Highlights version, supported coordination mode, and notification availability. It should not trigger a save or permission prompt merely to inspect readiness.

## 7. An intuitive and quiet experience

The best successful interaction is that the reader stays on the same page and can keep annotating. “Beautiful” here means continuity, accurate language, and a single useful explanation rather than visible automation.

| Situation | Suggested visible result |
| --- | --- |
| Marker safely updated through native coordination | “Updated PDF status” / “Updated 2 PDF markers.” |
| Highlights could not safely yield the document | “PDF update waiting” / “Close ‘Paper title’ when you're ready. Bob will retry on its next scan.” |
| Save produced new bytes that require a fresh scan | “Annotations saved; PDF update pending.” **Only use “saved” if that fact is independently established.** Otherwise say “The PDF changed while preparing the update.” |
| Save failed or conflict sheet already exists | “Highlights needs attention” / “‘Paper title’ was left open. Bob did not update its PDF.” |
| Explicit fallback actually closed and reopened a document | “Refreshed ‘Paper title’ in Highlights.” Mention restored position only if verified. |

Show one summary per scan, with at most a few names and a remaining count. No sound by default; no progress modal; no notification for a no-op. Deduplicate repeated pending messages by document identity and reason, so a 15-minute schedule does not produce a wall of identical notices. Show a new notice when the reason changes or the pending update completes.

Bob Refs already has an inline scan status, warning banner, VoiceOver announcement, and `NotificationService.notifyRefsScan` for scans finishing while the panel is hidden. Extend those rather than adding a second progress surface. A visible panel should receive the inline result; a hidden panel should receive the macOS notification. Clicking a notice should open the relevant result or reference, not automatically rerun save/close actions. [Code: `NotificationService.swift:139`; documentation: `docs/reference/mac-capture/refs.md:315`.]

**Scheduled scans need their own delivery path.** Current cron success output is discarded, and the existing app notification service is invoked for app-originated scans. Merely improving that service will not notify on cron writes. A small CLI macOS notifier can use Apple's documented `display notification` mechanism initially, with a fixed script and payload passed as arguments, while app-originated scans designate the app as notification owner to avoid duplicates. Test the sender attribution and delivery under the real cron context; a generic scripting sender is a polish limitation compared with Bob's app identity. If unified branding is required, use a narrow notification bridge to the existing Bob app, with structured results rather than shell commands. Neither transport should own PDF reconciliation. [Apple: [Displaying Notifications](https://developer.apple.com/library/archive/documentation/LanguagesUtilities/Conceptual/MacAutomationScriptingGuide/DisplayNotifications.html).]

Always retain a human/JSON result and a bounded local last-scan receipt; notifications can be disabled or suppressed. Permission setup belongs in an explicit interactive setting, not a cron-triggered prompt. Notification failure must be reported as a presentation problem without rerunning the PDF write or falsely claiming the document operation failed. [Apple: [requestAuthorization](https://developer.apple.com/documentation/usernotifications/unusernotificationcenter/requestauthorization%28options%3Acompletionhandler%3A%29), [authorization status](https://developer.apple.com/documentation/usernotifications/unnotificationsettings/authorizationstatus).]

## 8. If explicit refresh is eventually necessary

If native coordination fails the real-app reload tests, ship deferral first. Only add a “Save and refresh in Highlights” user action if the remaining demand justifies it.

That action needs stronger guarantees than the current general tab-close command:

- Resolve exact canonical file identity; handle duplicate names and multiple windows. Unknown identity means no close.
- Establish an interactive GUI session and already-granted required permissions.
- Save through a verified document API if one is discovered; otherwise invoke a verified app-specific Save action. Do not use global Save All.
- Confirm save completion and handle an active annotation editor; stop on any sheet or uncertain state.
- Capture the recoverable reading position and window/tab context, close only the matching document, and verify it is gone before Bob writes.
- Replan from the saved PDF and sidecar and respect the dirty-target guard.
- Persist a small recovery record before closing. Reopen the original if mutation fails, or the new version if it succeeds. On restart, offer recovery rather than unexpectedly reopening a deliberately closed tab.
- Restore what the tested API exposes. Do not promise preservation of undo history or exact tab position without evidence.

Do not quit the application as part of this transaction. Never click destructive conflict choices automatically. Never “fix” an already-conflicted live document by reverting it.

## 9. Validation that should decide the implementation

Use disposable copies in a temporary test vault and a controlled Highlights session. Do not run this experiment against Bryan's working library. The decisive comparison is the existing uncoordinated writer versus a minimal `.forMerging` wrapper around the same marker edit.

| Test | Required evidence |
| --- | --- |
| Clean open PDF | Marker update visible; next annotation saves without conflict |
| Unsaved highlight and unsaved sticky-note text | Both survive the update, reopen, and a subsequent manual save |
| Comment popover still editing | Latest typed text preserved, or the operation safely refuses |
| User edits while coordination is waiting/executing | No lost annotations or silent rollback of the marker |
| App reload behavior | Page, scroll, zoom, selected tab and acceptable undo behavior recorded |
| Markdown, TextBundle, image annotation | Sidecar and exported note remain correct; no missing-image or stale-plan overwrite |
| Two same-named PDFs, inactive tabs, multiple windows | No wrong-document action or mistaken “closed” classification |
| Save error, read-only PDF, existing conflict sheet | No Bob write; document remains available to the user |
| Save changes Git state | Guard preserved; pending state resolves after normal vault-sync and a later scan |
| Headless/locked session, app launch/quit, unresponsive app | Bounded result with no keystrokes sent and no delayed surprise write |
| Cancellation and process interruption at each boundary | Honest write outcome; rerun converges; no orphaned worker |
| CLI, cron, Bob Refs, targeted sync; v1 and v2 notes | Same safety policy and correct reporting across entry points |
| Dry-run and `--no-hooks` | Dry-run has no app effects; hook suppression cannot disable write safety |
| Second scan with no new edits | No marker churn or duplicate notification |

Inspect annotation **contents**, counts, identities, marker values, PDF readability and sidecar output; a lack of visible error dialog is not enough. Check a manual save after the test, because the user's reported failure appears at the next annotation/save. Compare both the installed Highlights build and the version planned for deployment.

Automated tests should cover the coordination adapter state machine, save-induced plan invalidation, cancellation boundaries, guard placement before v2 writes, JSON compatibility, deduplicated notices, and partial-run recovery. Linux tests can cover these through a fake adapter; actual NSDocument/Highlights behavior needs macOS integration and manual acceptance evidence. Existing macOS CI can compile the native bridge, but compilation is not evidence of Highlights compatibility.

**Go/no-go rule:** promote native coordination only if the unsaved-popover and subsequent-save tests pass, not merely the clean-document case. If they fail, the first supported behavior is waiting until the document is safely closed. A UI close/reopen prototype has its own additional acceptance gate.

## 10. Requirement adjustments

1. **Replace “automatically close and reopen” with “preserve the reading session while safely updating, or defer.”** Closing is a possible explicit fallback, not the success criterion.
2. **Strengthen “attempt to save” to “a successful save/access handshake is a prerequisite; uncertainty means no PDF write.”** This directly protects the annotations the user values.
3. **Accept temporary marker lag.** Pending status is preferable to losing annotations; it must remain visible and converge on later scans.
4. **Cover all Bob marker-write entry points and fields.** Fixing only `status:` or only the Mac panel would leave the same race elsewhere. Other PDF mutation commands and vault-sync replacement deserve a follow-on audit, not an unproven blanket safety claim.
5. **Preserve dry-run and current write opt-in.** No app save side effect during preview, and no safety bypass through `--no-hooks`.
6. **Make notification plus durable status the requirement.** A banner alone is not reliable state; avoid repetitive notices and claims about annotation preservation that the protocol cannot prove.
7. **Require real Mac validation before unattended enablement.** The installed app supplies promising static evidence, not a completed compatibility guarantee.

## Evidence inventory and limits

Repository evidence was read from these revisions:

- `bob-cli`: `5eed7df96a7ce1ca2d07d13c9859e434c34a73ec` — marker writer, both execution branches, guards, scan JSON, ref/vault-sync/Mac Refs documentation, CI and target dependencies.
- `bob-mac-capture`: `73202c8142ca2fd4b3335d524df6153bc9ed3ef0` — Accessibility tab reader/closer, scan response decoding, outcomes, notification service.
- `chezmoi`: `eafb7a20a532006d571a9bbe2a198d2207867b29` — scheduled-scan wrapper and managed Bob configuration.

Audited project memories reviewed: reference note/task definitions, Obsidian sync conventions, reference ingestion ownership, Mac thin-client ownership, CLI rules, artifact handling, and tailnet access. Relevant constraints: annotation sync remains the Mac's full scan; marker semantics stay in bob-cli; sidecars remain owned by Highlights.

Primary external documentation is linked near the claims above. Read-only live evidence came from `/Applications/Highlights.app/Contents/Info.plist`, a scripting-resource filename walk of that bundle, `sw_vers`, and the installed Foundation `NSFileCoordinator.h`. No UI behavior tests or code tests were run because this turn produced research only. No compatibility or successful-save result is inferred from a build number or dictionary absence.

The hypothesis does not explain every possible PDF conflict. A Git pull replacing an open PDF, another editor, or a remote annotation writer can create related conflicts. The proposed scan repair should not be marketed as fixing those automatically; its first guarantee is about Bob's own coordinated marker writes on the Mac.

## Recommended solution

**Build a small, controlled `.forMerging` experiment first, then make verified native file coordination the common macOS marker-write path. Keep the tab open, retain all existing disk/Git checks, and invalidate the plan whenever saving changes its inputs. Defer uncertain operations with one clear pending result and a restrained notification.**

If Highlights cannot reliably flush and reload in that experiment, ship deferral while documents are open instead. Offer explicit save-and-refresh only after exact document identity, save acknowledgement, and recovery have been demonstrated. This best matches the real goal: a status update should not cost an annotation, a reading position, or the reader's attention.
