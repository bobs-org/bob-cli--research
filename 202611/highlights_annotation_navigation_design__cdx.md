# From an annotation to its page in Highlights

Independent research and design recommendation · **cdx** · 2026-11-08

## Recommendation in brief

**Build this.** Opening the original page is the natural next action after following a task’s annotation backlink. Keep `Cmd+Enter` as the contextual “open the source” gesture, preserve reading-task behavior, and show a compact, clickable **Highlights · p. 12 · ⌘↵** status-bar pill while a supported annotation or reading task is active.

The important change is deeper than recognizing a quote: **preserve the actual PDF page destination during sync.** Bob’s sidecar parser distinguishes the displayed page label from the link’s page index, but generated reference notes discard the latter. A plugin-only implementation that searches upward for `### Page N` can open the wrong page. Preserve a versioned, block-keyed navigation projection in the managed note region, then use one resolver for the shortcut, availability pill, and toast.

Use Highlights’ documented `highlights://…#page=N` transport, rebuilt from the current local PDF path. Verify it on the installed Mac app first. Do not add keystroke automation, another PDF viewer, or a new “open” CLI command for this feature.

## Evidence and limits

I researched independently and did not locate or consult the other swarm researchers’ reports, chats, or findings. I inspected the primary checkout, the `bob-plugins` checkout opened through `sase repo open`, project memory through audited reads, and public vendor documentation. No product code or vault content was changed.

Inspected revisions:

- `bob-cli`: `e5a7b2a32ac7195f11914e0e85cdd50b5e1386d9`.
- `bob-plugins`: `9003569c6aea6b31d16da0e4ada017c05218bbd5`.

I ran `node --test scripts/test-navigation-hotkeys-ref-pdf.cjs`: **14 passed, 0 failed**. These are harness tests of the existing resolver and launcher, not proof of real Highlights page navigation. I did not run Highlights or interactive Obsidian on the Mac. UI dimensions below are proposed design values, not usability-test results.

## What exists today

### Preserve the existing shortcut’s contract

`bob-navigation-hotkeys` owns `open-reference-pdf-in-highlights`. The vault’s custom `Meta+Enter` binding overrides Obsidian’s built-in `Mod+Enter`; it is deliberately not a plugin default. Changing it to generic `Mod` would also affect `Ctrl+Enter` on other platforms. Keep the command ID and binding. [Registration](https://github.com/bobs-org/bob-plugins/blob/9003569c6aea6b31d16da0e4ada017c05218bbd5/plugins/bob-navigation-hotkeys/src/490-plugin-lifecycle.js#L83), [current user contract](https://github.com/bobs-org/bob-plugins/blob/9003569c6aea6b31d16da0e4ada017c05218bbd5/docs/highlights.md).

The resolver accepts recognized `#task #ref` rows, dedicated links to those tasks, and managed embeds. It reads an explicit PDF link or a note’s `source_pdf`, validates the vault-relative path and existence, and invokes `/usr/bin/open` through `execFile`. It tries bundle ID `net.highlightsapp.universal`, then app name `Highlights`, with a timeout. Other contexts delegate to Obsidian’s new-tab action; recognized errors show notices. It currently works with an editor in Source/Live Preview, not arbitrary Reading-view DOM selections. [Resolver and launcher](https://github.com/bobs-org/bob-plugins/blob/9003569c6aea6b31d16da0e4ada017c05218bbd5/plugins/bob-navigation-hotkeys/src/677-plugin-ref-pdf-open.js#L81).

The Reading Board already calls additive `api.openReferencePdf(path)`. Preserve that document-level API. Its current “Opened x.pdf in Highlights” notice reports successful launch dispatch, not confirmation of the displayed page. [Public API](https://github.com/bobs-org/bob-plugins/blob/9003569c6aea6b31d16da0e4ada017c05218bbd5/plugins/bob-navigation-hotkeys/src/480-review-jump-and-nav-api.js#L905), [existing tests](https://github.com/bobs-org/bob-plugins/blob/9003569c6aea6b31d16da0e4ada017c05218bbd5/scripts/test-navigation-hotkeys-ref-pdf.cjs).

### Annotations have stable addresses, but complicated boundaries

Annotation-created tasks contain links such as `[[ref/books/example#^h-…|🔖]]`. The `h-` identifies the whole annotation, including nested comments and image notes. It differs from a reading task’s `ref-` identity and legacy task-specific `ht-` anchors. Generated annotations live between `<!-- highlights:begin -->` and `<!-- highlights:end -->`. They include quote, note, and image callouts; sections; continuation groups spanning pages; and removed or redirected blocks. [Generated formats and backlinks](https://github.com/bobs-org/bob-cli/blob/e5a7b2a32ac7195f11914e0e85cdd50b5e1386d9/docs/highlights-ref-sync.md#L1440).

“Selected annotation” cannot safely mean “current line contains `>`.” Resolve the unique enclosing managed annotation, including its title, body, nested comments, images, and trailing block-ID line. That last line is especially important when following a task backlink.

### Displayed page and destination are different data

`SidecarAnnotation` carries both `page_label` and `page_index`. The parser prefers the page-heading link’s `#page=` value over a number in its label. A regression test explicitly parses `[Page 12](highlights://example#page=99)` as label **Page 12**, index **99**. Generated display structures and `bob ref show` retain labels but not that destination index. [Parser](https://github.com/bobs-org/bob-cli/blob/e5a7b2a32ac7195f11914e0e85cdd50b5e1386d9/src/native/highlights_ref/sidecar_render.rs#L2654), [counterexample test](https://github.com/bobs-org/bob-cli/blob/e5a7b2a32ac7195f11914e0e85cdd50b5e1386d9/src/native/highlights_ref/tests/continuations.rs#L470), [renderer](https://github.com/bobs-org/bob-cli/blob/e5a7b2a32ac7195f11914e0e85cdd50b5e1386d9/src/native/highlights_ref/sidecar_render.rs#L1322), [show model](https://github.com/bobs-org/bob-cli/blob/e5a7b2a32ac7195f11914e0e85cdd50b5e1386d9/src/native/ref_library/show.rs#L34).

Consequently:

- Page links in sidecar fixtures are not retained as navigation links in ordinary generated ref-note headings.
- Printed page labels, Roman-numbered front matter, and cover pages make label guessing unsafe.
- “Pages 11–12” represents several continuation pieces, not a single destination.
- A section’s page summary does not locate every member annotation.
- Calling today’s `bob ref show` does not recover the missing destination.

### Historical annotations may need an archived PDF

Annotated overwrite freezes the old note and PDF under `ref_history/`, records `annotated_pdf`, and rewrites inbound `#^h-` links onto the frozen note. Opening the new live PDF for such an old annotation would be wrong. Recognize this case explicitly; never substitute the newest reading with the same title. [Archive contract](https://github.com/bobs-org/bob-cli/blob/e5a7b2a32ac7195f11914e0e85cdd50b5e1386d9/docs/highlights-ref-sync.md#L693), [archive/backlink tests](https://github.com/bobs-org/bob-cli/blob/e5a7b2a32ac7195f11914e0e85cdd50b5e1386d9/src/native/highlights_ref/overwrite/execute.rs#L3519).

## Critique and explicit requirement adjustments

This is a good idea: task → cited annotation → original page forms a coherent workflow. It makes source checking inexpensive without inventing a new gesture. The main risk is **false precision**: a polished page badge that opens another page, a last-viewed location, or a newer PDF edition.

I recommend these explicit adjustments:

1. **Define selection.** A caret or selection wholly within one managed annotation qualifies, including the block-ID line and nested comments. Multiple annotations or multiple carets produce a concise explanation, not an arbitrary first match. Ordinary authored quotes remain ordinary Obsidian contexts.
2. **Require trustworthy page evidence.** Without it, show “page unknown” and offer document-only opening explicitly. Do not call a file-only launch a successful page jump.
3. **Keep the two-step task workflow.** Do not make the whole annotation-created task row open Highlights. Follow its bookmark to the annotation, then use the shortcut. This preserves access to Obsidian context and avoids hijacking ordinary task links. Reading tasks retain whole-document opening.
4. **Scope the first release to Source and Live Preview.** Reading-view keyboard selection is a separate interaction contract. A remembered last-clicked block must not become a hidden global target. An explicit Reading-view button can follow later; do not advertise universal view support prematurely.
5. **Handle historical sources deliberately.** A managed frozen annotation uses its `annotated_pdf`. Older archives without page metadata can offer document-only opening. Never silently use the live replacement PDF.
6. **Opening is read-only.** No task status, freshness, reading state, review-walk position, annotation sync, or PDF bytes change as part of the gesture.

These are reliability and scope clarifications, not a reason to replace the requested workflow with a larger reference-management feature.

## Proposed interaction and visual design

### One small, truthful contextual action

Add one active-context status-bar pill beside the existing bracket-mode indicator. The navigation plugin already has a status-bar lifecycle and focused-editor update hooks. Reuse the lifecycle pattern without overloading the bracket indicator’s meaning. [Existing indicator](https://github.com/bobs-org/bob-plugins/blob/9003569c6aea6b31d16da0e4ada017c05218bbd5/plugins/bob-navigation-hotkeys/src/547-bracket-mode-indicator.js#L569).

Use a small `book-open` icon where this wireframe says `[book]`:

```text
Reading task selected        [book] Highlights          [⌘↵]
Annotation selected          [book] Highlights · p. 12  [⌘↵]
Later continuation piece     [book] Highlights · p. 13  [⌘↵]
No exact destination         [book] Highlights · page unknown
Missing local PDF            [book] PDF unavailable
```

The icon, app name, page, and keycap form one button. Clicking invokes the same resolved action as the shortcut. In the page-unknown state, clicking offers **Open PDF without page**. The keyboard gesture displays the same explanation and explicit action, rather than launching while promising a page.

Show the actual active shortcut if available from the hotkey manager; an unbound command should not display a fictitious keycap. The tooltip includes the document title and full action. When the label differs from physical numbering, say “Page 12 · PDF page 99” in the tooltip and toast; keep the familiar printed label in the compact pill.

Proposed visual specification:

- Native theme colors and typography, a subtle neutral border, small book icon, compact keycap, and approximately 24–28 px hit height.
- Readable text; accent color on hover/focus rather than a permanent bright badge competing with lane colors.
- Visible keyboard focus and a complete accessible name: “Open Systems Performance, page 12, in Highlights; Command Enter.” Do not rely solely on color or tooltips.
- No pulse, bounce, or cursor-move toast. Update only when the semantic target changes.
- Hide when focus leaves the supported editor, another pane becomes active, or selection is ambiguous. Support pop-outs using the active view’s owning document.
- On narrow windows shorten detail before removing the app name. Preserve the shortcut while space permits.

Why start here instead of putting buttons on every quote? A single pill gives reading tasks and annotations the same stable affordance without changing note content, adding height to every callout, or colliding with editing widgets. Its weakness is peripheral discoverability. Test that directly after following a bookmark. If Bryan misses it, add a **single active-callout header action** backed by the same resolver, rather than permanently repeating buttons throughout the note.

### Toasts: show intent before the app switch

The existing notice appears after `open` returns; Highlights may already have focus. Create one notice immediately before dispatch and let Obsidian paint it before yielding to the OS. Avoid a noticeable fixed delay, and never steal focus back just to display the toast.

| Situation | Proposed copy | Behavior |
|---|---|---|
| Annotation launch | “Opening Systems Performance · page 12 in Highlights…” | Before dispatch; about 4 seconds |
| Label/index differ | “Opening Systems Performance · page 12 (PDF page 99) in Highlights…” | Explain the mapping |
| Reading task | “Opening Systems Performance in Highlights…” | Same component; no invented page |
| Page unknown | “This annotation has no exact page destination. Open its PDF without a page?” | Explicit action; no automatic fallback |
| Missing PDF | “The PDF isn’t available on this Mac: systems-performance.pdf.” | Longer-lived; pill retains error state |
| Launch failure | “Couldn’t open Highlights. Check that Highlights is installed.” | Update same notice; expose concise detail |
| Removed annotation | “This annotation was removed from the source.” | No claimed page jump |
| Ambiguous selection | “Select one annotation to open its page.” | No launch |

Successful dispatch needs no second success toast. “Opening…” accurately describes a handoff without claiming confirmation from Highlights. Replace the notice on failure rather than stacking messages. Repeated presses for the same in-flight target reuse its operation and notice.

Use Obsidian’s Notice mechanism and verify screen-reader behavior in the installed app. If additional custom announcements are necessary, use a polite status region and avoid duplication. W3C recommends exposing status changes without moving focus and cautions against excessively chatty announcements. [Status-message guidance](https://www.w3.org/WAI/WCAG22/Understanding/status-messages.html).

An Obsidian toast cannot be guaranteed visible while another application is frontmost. The contextual pill when returning provides supporting feedback. Native notifications would be disproportionate.

## Technical design

### First prove the native page transport

Highlights’ own release notes document `highlights://Users/test.pdf#page=3` for opening a specific page. Its current formatting guide describes source-page links in note headers. This establishes a native route, but not every encoding detail or the installed version’s behavior. [Documented scheme](https://highlightsapp.net/changelog/2015/01/03/Version-1.2/), [page-header behavior](https://highlightsapp.net/how-to/mac/format-pdf-notes/).

Before building UI, test a disposable PDF on the Mac:

- Exact slash/host syntax, percent encoding, and page numbering convention.
- First/last page and a PDF with different printed labels and physical page numbers.
- Spaces, Unicode, `%`, `#`, `?`, and parentheses in paths.
- Cold launch and an already-open PDF currently on another page.
- Two open PDFs sharing a basename in different directories.
- Whether `/usr/bin/open -b net.highlightsapp.universal <highlights-url>` delivers the intended URL; app-name fallback must preserve that destination.
- Missing application, missing file, and out-of-range page behavior.

Capture the verified URL serialization as a fixture. Use `execFile` argument arrays, not shell interpolation. A filesystem path with `#page=N` appended is not a filename to pass to the existing file-opening code. An arbitrary `file://…#page=N` URL is also not a verified Highlights page contract.

Build the destination from the **current resolved local PDF path**, not the path/nickname embedded in an old export URL. Encode the path once, append only a validated page integer, and verify how the vendor scheme handles the first path segment before relying on URL utilities that may interpret it as a hostname. This matters across renames and different hosts’ vault roots.

If the installed app fails this experiment, investigate its native contract before implementing the jump. Do not substitute scripted “Go to Page” keystrokes: they add focus races, window ambiguity, and Accessibility dependence. The existing PDF-write decision rejects UI automation for coordination; navigation is a different operation, but the reliability concerns are similar. This feature performs no PDF write and needs no write-coordination scope.

### Preserve a small navigation projection during sync

Recommended storage: a **versioned generated comment inside the existing managed Highlights region**, keyed by published `h-` ID. It travels with the note and frozen archive without a new database, extra companion file, or machine-specific absolute URL.

Illustrative shape, not an existing format:

```json
{
  "version": 1,
  "blocks": {
    "h-example": {
      "page": 99,
      "page_source": "sidecar_link",
      "pieces": [
        {"page": 99, "page_source": "sidecar_link"},
        {"page": 100, "page_source": "sidecar_link"}
      ]
    }
  }
}
```

Put this in a named HTML-comment envelope. Serialize deterministically; teach the managed-region parser to exclude it from quote text, counts, and identity. Associate destinations by stable ID, not quote substring or document line number. Piece ordinals correspond to rendered continuation pieces and regenerate atomically with them. Single annotations need only the block destination, without a redundant pieces array.

The current `page_index` lacks provenance: its value can come from either an explicit URI or label-number fallback. Carry that distinction internally. Only advertise exact navigation from an explicit source-link destination, or a label independently checked against the PDF. A first version can withhold exact navigation for unverified numeric labels.

Give the public field a documented numbering convention established by the Mac experiment; do not propagate ambiguous `page_index` terminology across the plugin boundary. Reject zero, negatives, non-integers, overflow, malformed records, duplicate IDs, and unsupported versions. Validate against a trustworthy page count if available; otherwise do not claim that integer validation proves the page exists.

Update the renderer and managed-region reader together. Prove that metadata does not churn `h-` IDs, recreate follow-up tasks, alter annotation text, or enter PDF marker/property synchronization. Exposing the same projection additively through `bob ref show` is useful for future consumers, but the editor should not run a vault-wide CLI index on cursor movement.

Migrate through ordinary annotation regeneration. Old notes remain readable with a page-unknown state. Do not run a writing sync from the keypress. A controlled one-time regeneration can be offered at rollout. For new frozen archives, retain metadata with the old body and resolve `annotated_pdf`; old archives without it retain document-only behavior. An externally replaced PDF can still make previously valid page metadata stale: this design does not claim exact annotation matching and should not hash PDFs on every cursor event.

### Share one resolver across command, cue, and feedback

Use a pure navigation-context resolver and a narrow launcher. Suggested result variants:

```text
none
recognized-unavailable(reason, optionalDocument)
ready(documentPath, notePath, blockId?, piece?, page?, pageLabel?, title)
```

The pill, command, tooltip, and toast consume the same result. Distinguish “recognized annotation but missing destination” from “not an annotation” so failures cannot fall through to unrelated actions.

Resolution rules:

1. Read the active editor’s current buffer, including unsaved changes. Exclude frontmatter, fenced examples, and arbitrary comments when locating annotation boundaries.
2. Preserve an unrelated explicit link’s normal action when the caret is actually on that link. Otherwise resolve the enclosing annotation before task-row parsing, so `#task` in its comment is not mistaken for a reading task.
3. A selection wholly inside one annotation selects it. A caret inside a later continuation piece or its comment uses that piece’s destination. A selection spanning pieces, or a backlink landing on the outer block ID, uses the first piece; show that start page in the cue.
4. Recognize quote, standalone-note, and image annotations. A section summary has no single annotation page and gets no exact-page action.
5. Follow only recognized generated redirects through a bounded, cycle-checked chain. Genuine tombstones remain unavailable. Never inherit a previous block’s page. Legacy `ht-` anchors require fixture-backed containing-annotation resolution or a clear unavailable result.
6. Outside annotation context preserve existing reading-task, Task Link, and managed-embed resolution. Unrelated contexts delegate exactly once to the native new-tab command.

At activation capture the intended target, then validate the current source/path before dispatch. A delayed availability lookup must not paint another leaf or newer selection; use document revision and request tokens. Clicking the pill retains its captured context despite momentary button focus.

Cache the active document’s parsed annotation ranges by revision. Resolve linked task content only when the target changes. Check file existence asynchronously, invalidate on relevant vault events, and recheck at activation. Keep PDF parsing, whole-vault scans, and subprocess launches out of the selection-update path. Remove subscriptions, UI, and timers on unload and leaf teardown.

### Keep the launch boundary compatible

Retain vault-relative path validation and traversal refusal, bundle/app fallback, and timeout. A retry must preserve the **same page URL**; never silently degrade to a plain file open. Preserve `api.openReferencePdf(path)` for the Reading Board. Add another public method only when a real consumer needs it; internal destination support alone does not require a top-level API version bump.

Represent unsupported platform, missing local PDF, missing page, malformed metadata, missing archive, and launch failure distinctly. Hide the enabled macOS shortcut on unsupported platforms. Do not repeatedly probe installed applications while the cursor moves: use cached capability information or learn from bounded launch failure.

## Alternatives considered

| Approach | Attraction | Assessment |
|---|---|---|
| Scan upward for `Page N` | Smallest patch | Reject as final design: wrong with label/index differences, sections, and continuation groups |
| Open raw sidecar URLs | Appears to preserve a page | Reject as authority: stale/machine-specific path and unresolved stable-block mapping |
| Generated block destinations in note | Atomic with annotations, follows archives | **Recommended**; needs renderer/parser compatibility tests |
| External annotation-index JSON | Rich metadata outside note source | Viable for a broader service; extra sync, retention, and archival work now |
| CLI lookup for every gesture | Central parsing | Today’s `ref show` lacks destinations; a new hot-path process is unnecessary |
| Buttons on every callout | Obvious | Repetitive; first try one active-context pill |
| Status-bar action | Stable, calm, shared by tasks and annotations | **Recommended first UI**; test peripheral discoverability |
| AppleScript/UI keystrokes | Mimics manual page entry | Reject due to focus, permissions, and window targeting |
| Open Obsidian PDF viewer | Avoids app switch | Only an explicitly chosen fallback; changes the desired workflow |
| Launch from every annotation task | Saves a step | Defer; skips the linked evidence note and changes ordinary task/link behavior |

## Implementation sequence and acceptance criteria

This is a modest change across two repositories, not a safe one-file shortcut patch. The following sequence is a recommendation, not work performed in this research.

1. **Mac transport experiment:** establish URL behavior, encoding, page convention, warm/cold launch, and errors on disposable fixtures. Record app/macOS versions.
2. **Bob navigation metadata:** carry source-link provenance through rendering and region parsing; preserve block identities, tasks, and archives; test old-note compatibility.
3. **Plugin resolver/launcher:** extend `677-plugin-ref-pdf-open.js` through separate fragments as needed, respecting fragment size limits; keep command ID and public document-opening API.
4. **Availability and feedback:** integrate the pill, shared target model, pre-handoff notice, and bounded failure states; test discoverability in actual Obsidian.
5. **Docs and integration:** update `bob-plugins/docs/highlights.md` and Bob’s managed-format documentation, regenerate plugin inventories/build outputs, run required checks, and deploy through `bob plugins sync` when implementation is authorized. Follow Bob’s release train; no manual version/changelog change belongs in this research.

| Layer | Essential acceptance cases |
|---|---|
| Page projection | Label 12 / URI page 99; no URI; Roman label; malformed/zero/overflow destination; quote/note/image; continuation pieces; section regrouping |
| Compatibility | Stable `h-` IDs; metadata excluded from text and identity; no duplicate tasks; old notes parse; deterministic rerender; unsupported version fails clearly |
| Selection | Backlink lands on block ID; nested comment; folded callout; first/later piece; cross-piece selection; cross-annotation selection; multiple carets; fence; unrelated inline link |
| History | Rename; same-title reread; frozen annotated PDF; old archive without metadata; redirect/cycle; tombstone; section summary |
| Async/UI | Rapid cursor movement; edit during resolution; deleted/renamed file; pane switch; pop-out; unload; remapped/unbound shortcut; click retains target |
| Launch | Encoded special characters; argument-array safety; fallback preserves page; timeout; repeated press; unsupported platform; no vault/state writes |
| Regression | Existing 14 tests; Reading Board API; new-tab delegation; Ctrl+Enter still performs its existing task action |
| Real Mac | Correct PDF/page on warm and cold launch; two same-named PDFs; pre-handoff notice; caret/scroll preserved on return; task and review state unchanged |

Visually test light/dark themes, narrow panes, larger text, reduced motion, and keyboard-only operation. Acceptance is not merely “a chip exists”: after following the task bookmark, the available action and intended page should be legible, and activation should open that source without changing the task.

## Recommended solution

**Extend the existing command, preserve exact destinations during sync, and expose one contextual Highlights action.** Use stable annotation IDs and per-piece page metadata, resolve the current or retained historical PDF, and dispatch through Highlights’ verified native page URL. Reading tasks remain document-level. A quiet clickable status-bar pill serves both contexts, with one honest “Opening…” toast before the app handoff.

Ship exact jumps only where the destination is trustworthy; offer document-only opening explicitly elsewhere. Preserve normal link behavior and the task → annotation → source workflow. This gives the requested convenience a predictable interaction, a calm visual presence, and a destination the user can trust.
