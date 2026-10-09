# An instant Pomodoro overview in Bob Mac Capture

Independent research by **cdx**, 2026-10-09. This report investigates the requested default preview; it proposes a design rather than implementing it. I did not consult this swarm's other reports, conversations, or findings.

The feature is a good idea. Opening Capture can become a quick answer to “what am I doing, and what comes next?” The ledger already carries that answer, and displaying task definitions removes a trip back to Obsidian. I would implement a read-only **Today’s Pomodoros** overview whenever the editor contains only whitespace. Typing immediately replaces it with the existing capture preview; clearing the draft restores it. Capture must remain ready to type into throughout.

I recommend three substantive adjustments: cache every input that affects the result, allow different tasks to use different detail levels when this preserves useful content, and permit scrolling as an explicit exceptional fallback. An unchanged daily file alone cannot establish freshness, and an arbitrarily long list cannot fit a finite screen even with one line per task. These are correctness constraints, not reasons to abandon the feature.

The main product risk is turning a lightweight capture surface into a wall of old task history. The requested full → no logs → headline progression is sensible, but a single long task should not force every other task into headlines. Nor should a popup visibly grow to full height and then shrink while discovering that content does not fit. Decide the layout against the screen budget before applying the window size.

**Evidence from the current implementation.** I inspected bob-cli at commit `4cc1281af196b39d8029fbaa85a17412450462fe` and bob-mac-capture at `ee19240cc7b123aae3e8b4ac9f7650ba01297f60`. Findings refer to these revisions, not assumptions about the installed Mac app.

| Existing behavior | Design implication | Source |
| --- | --- | --- |
| The hotkey shows a prewarmed nonactivating panel. `show()` prepares the model, requests a Pomodoro link count, orders the panel, and focuses the editor. | Preserve this path. Read memory and show the window without waiting for files or a subprocess. Reuse the overview snapshot for the link count rather than making another equivalent request. | [CapturePanelController.swift](https://github.com/bobs-org/bob-mac-capture/blob/ee19240cc7b123aae3e8b4ac9f7650ba01297f60/Sources/BobMacCapture/CapturePanelController.swift#L249) |
| An empty draft resets analysis to idle, leaving no preview. A retained nonempty draft reruns its capture analysis on reopening. | Introduce separate overview state; do not manufacture a fake capture response for empty input. Preserve retained drafts. | [CapturePanelModel.swift](https://github.com/bobs-org/bob-mac-capture/blob/ee19240cc7b123aae3e8b4ac9f7650ba01297f60/Sources/BobMacCapture/CapturePanelModel.swift#L1158) |
| `capture-pomodoros` lists today's open entries in ledger order, with refs, names, timing, warnings, and current-session identification. It supplies counts rather than full linked task contents. | Extend this read-only protocol instead of inventing another ledger scanner. | [capture_pomodoros.rs](https://github.com/bobs-org/bob-cli/blob/4cc1281af196b39d8029fbaa85a17412450462fe/src/native/capture_pomodoros.rs#L166) |
| Capture already returns full task blocks with verbatim lines and relative depth. The app renders them; its automatic folds target unchanged diff context rather than task history. | Reuse extraction and visual tokens, but give the overview its own fold policy and read-only styling. | [Task block contract](https://github.com/bobs-org/bob-cli/blob/4cc1281af196b39d8029fbaa85a17412450462fe/docs/capture.md#L3447), [CaptureTaskBlockPresentation.swift](https://github.com/bobs-org/bob-mac-capture/blob/ee19240cc7b123aae3e8b4ac9f7650ba01297f60/Sources/CaptureCore/CaptureTaskBlockPresentation.swift) |
| The panel measures content, grows to the screen's visible height minus 24-point top/bottom margins, and preserves its top edge. The auxiliary region scrolls. | Extend current sizing. Reduce overview detail before ordinary scrolling becomes necessary. | [Window sizer](https://github.com/bobs-org/bob-mac-capture/blob/ee19240cc7b123aae3e8b4ac9f7650ba01297f60/Sources/BobMacCapture/CapturePanelWindowSizer.swift), [Panel view](https://github.com/bobs-org/bob-mac-capture/blob/ee19240cc7b123aae3e8b4ac9f7650ba01297f60/Sources/BobMacCapture/CapturePanelView.swift#L430) |
| The FSEvents watcher debounces changes, but its callback discards paths and flags and refreshes broadly. | It can provide initial invalidation; selective refresh needs richer event data and dropped-event recovery. | [VaultTargetWatcher.swift](https://github.com/bobs-org/bob-mac-capture/blob/ee19240cc7b123aae3e8b4ac9f7650ba01297f60/Sources/BobMacCapture/VaultTargetWatcher.swift#L58) |

The accepted `decisions:mac-capture-is-a-thin-client` memory assigns grammar, resolution, and preview semantics to bob-cli, and presentation/process orchestration to Swift. I reviewed it through audited memory access, together with the Pomodoro, Task Link, Work Log, Schedule Log, ledger-derived Today, CLI, and artifact conventions. The proposal respects that division.

I ran a read-only benchmark using the installed Linux `bob 0.1.0`, an isolated temporary vault, and subprocess wall time. The fixture had 20 open Pomodoros, 40 dedicated task links, ten target notes, and a 1,366-byte daily note. Tasks had requirements and a Work Log. The fixture was removed; no real vault was read or changed.

| Command | Runs | Median | p95 | Output |
| --- | ---: | ---: | ---: | --- |
| `bob capture-pomodoros -b <fixture> -f json` | 100 | 1.85 ms | 2.77 ms | 20 entries, 4,077 bytes |
| `bob plan -b <fixture> -f json` | 40 | 5.08 ms | 6.32 ms | 40 Today tasks, 9,817 bytes |

These are warm filesystem measurements on Linux, not Mac latency guarantees. The installed binary does not expose its source revision. Neither command implements the proposed hydrated overview, and the fixture has no large vault or large histories. This supports trying the current subprocess transport first; it does not settle end-to-end responsiveness.

**The behavior I would specify.** Current means the single open timed Pomodoro identified by Bob, even after its planned stop time passes. Upcoming means open placeholder Pomodoros in today's selected daily file, in ledger order. These are queued sessions, not necessarily calendar appointments; do not invent their start times. Show Current first and every upcoming entry afterward, including empty and unnamed entries. Closed Pomodoros remain history.

This follows the scanner: exactly one open timed entry becomes current; multiple such entries produce a warning and no current marker. A future selector chooses an open untimed placeholder. Swift should use these classifications rather than infer them from checkbox characters or the clock. [Scanner and future selection](https://github.com/bobs-org/bob-cli/blob/4cc1281af196b39d8029fbaa85a17412450462fe/src/native/capture_pomodoros.rs#L403).

A multiple-current ledger remains visible with “Multiple open timed sessions” and neutral Open labels. Do not silently choose one, discard conflicting entries, or label every noncurrent timed entry Upcoming. Preserve unexpected open entries with warnings rather than hiding malformed authoring behind a tidy empty state.

Use dedicated direct-child Task Links, including supported embeds, as the association rule. Bob extracts the start lineup by stripping Pomodoro markers, accepting a sole block link, and excluding mixed prose, deeper descendants, struck links, and fenced lines. Reuse this behavior rather than treating every wikilink as a task. Preserve each occurrence under its Pomodoro, while memoizing the resolved definition once. The same task can legitimately occur in two sessions. [Queued link extraction and resolution](https://github.com/bobs-org/bob-cli/blob/4cc1281af196b39d8029fbaa85a17412450462fe/src/native/capture_pomodoro_start.rs#L59).

Retain a linked task that has since been completed, displaying its actual status discreetly: silently removing it conceals a stale ledger link. `today_tasks()` is useful resolution precedent but an inadequate final data source: it filters closed tasks, deduplicates across sessions, and returns only headlines. [Today engine](https://github.com/bobs-org/bob-cli/blob/4cc1281af196b39d8029fbaa85a17412450462fe/src/native/plan_budget/today.rs#L96).

For each resolved occurrence, retain the complete task block through Bob's structural boundary, including nested tasks, prose continuations, blank lines, and code. Do not recursively transclude other notes or dependency tasks; dependency links are content, not permission to expand a graph. Unresolved, ambiguous, deleted, or non-task targets get a visible compact row with the original link and warning. One broken target must not remove the overview.

| Requirement adjustment | Proposed rule | Why |
| --- | --- | --- |
| Daily-file-only cache | Validate the daily note, resolved task notes, relevant settings, and resolution dependencies. | Task content/status changes independently of the ledger. |
| Unlimited no-scroll guarantee | Auto-fit normal cases; use one vertical scroll region when headlines exceed the screen. | Finite geometry cannot fit unbounded rows. Never omit upcoming sessions or shrink text to unreadability. |
| Uniform folding, if intended | Permit mixtures of the same three task views, preferring meaningful detail over history. | A huge task should not suppress every smaller task's detail. |
| “Full task definition” | Preserve authored content/structure, render Markdown readably, and offer the original task in Obsidian. | IDs and technical syntax should not dominate a glanceable overview. |
| Frequent opening | Retain the in-memory overview across hide/show and prefetch after Bob resolves at startup. | Ordinary opening shows content immediately; a first-use miss gets a compact loading state. |

**The visual design should be quiet and familiar.** Keep the existing editor at the top and capture footer at the bottom. Between them, use a compact “Today’s Pomodoros” title and date. The current session gets one subtle accent rail, theme, authored time range, and Current label. Upcoming groups get lighter dividers and an Upcoming section label; names do most of the work. Use “Untitled Pomodoro” for an unnamed entry and “No linked tasks” for an empty one.

A representative arrangement:

```text
[ Capture a thought…                                      ]

Today’s Pomodoros                                  Fri 9 Oct

│ Current · 09:00–09:30 · CAPTURE
│ ◐ Make the empty panel useful                bob-mac-capture
│   • Keep keyboard focus in the editor
│   • Refresh task contents independently of the daily note
│   ▸ History hidden

  Upcoming
  DOCS
  ○ Document the preview contract                         bob-cli
    • Describe unsupported-Bob behavior

  ADMIN
  ○ Renew the certificate                              personal

[ existing capture footer                                ]
```

Use native readable text sizes, familiar status symbols, modest indentation, and adaptive separator colors. Keep source notes visible but subordinate; suppress raw IDs in ordinary display. Preserve useful schedule/priority metadata without converting every field into a badge. An idle snapshot needs neither diff colors nor a fake “will capture” destination. Reuse the palette/card primitives while distinguishing it from mutation previews.

Hidden content needs a disclosure affordance: “History hidden” or “4 detail lines hidden.” Opening the original task in Obsidian should be deliberate and must not hijack Return. A disclosure may explicitly enter a detail-reading state with scrolling and a clear route back to Auto, or open the task externally. Automatic folding must not immediately undo the user's expansion.

A countdown is unnecessary in version one. The authored range and Current label avoid a second timer surface. If remaining/overdue time comes later, Bob should supply structured timestamps; Swift can tick locally without invoking Bob or invalidating content every second.

**Keep the semantic implementation in Rust.** Prefer this additive opt-in interface:

```text
bob capture-pomodoros --with-tasks -f json
```

The proposed `--with-tasks` flag also gets public short alias `-t`, excellent help, and documented unsupported behavior. The command without it retains lightweight picker output. Do not add a subcommand under `bob capture`, whose free-text grammar would swallow it. The flag is a proposal, not an existing feature.

Return the existing version-1 envelope plus an optional overview payload containing:

- Daily file identity, selected local day, source revision, and warnings.
- Ordered Pomodoro entries with Bob's classification and ordered task occurrences.
- A table of unique task definitions, keyed by canonical note path plus block ID.
- Each definition's display headline, actual status, location, raw lines, relative depth, and structured history ranges.
- A dependency manifest with content digests and existence states for files consulted, plus information needed to detect changed link resolution.

Occurrences belong to sessions; definitions are shareable. Do not use a task line number or headline digest as the complete content revision: changing a child bullet leaves the headline unchanged. Preserve ledger ordering and duplicate occurrences.

Read each target note once and scan it once per snapshot, resolve its requested IDs together, and extract blocks using `NoteTask.block_end`. Reuse `VaultLinkResolver`, which tries exact paths before lazily building a basename index. A basename lookup can still walk the vault; avoid doing that separately for every task. [Block extraction](https://github.com/bobs-org/bob-cli/blob/4cc1281af196b39d8029fbaa85a17412450462fe/src/native/capture/task_blocks.rs#L452), [Resolver](https://github.com/bobs-org/bob-cli/blob/4cc1281af196b39d8029fbaa85a17412450462fe/src/native/vault_links.rs#L151).

History recognition belongs in Bob. Its managed-log recognizer already accepts legacy capitalization, optional emoji, and colon forms. Annotate recognized subtree ranges rather than assigning Swift a regex. Include recognized logs within nested tasks in the displayed block; never hide prose merely mentioning “work log.” Unknown structures remain visible. [Managed-log recognition](https://github.com/bobs-org/bob-cli/blob/4cc1281af196b39d8029fbaa85a17412450462fe/src/native/capture/sub_bullet.rs#L284).

Swift owns decoding, caching, and fitting. Preserve schema-version rejection and defensive additive decoding. A genuinely unsupported flag gets one lightweight legacy listing and a quiet upgrade hint, with capability results keyed to executable identity. Do not mistake timeouts, permissions, or malformed responses for an older Bob; do not retry unsupported functionality on every opening.

Hash the same bytes used to construct the snapshot. If a watched input changes during hydration, reject or promptly revalidate that result rather than claim freshness for mixed versions. Bound retries so active sync cannot block Capture. A transactional filesystem snapshot is unnecessary, but marking a known-racing result fresh is avoidable.

**Cache data and layout separately.** A resident app's in-memory cache is enough initially. Disk persistence adds invalidation/versioning to save a cold read at launch; justify it with Mac measurements. A daemon or FFI is likewise premature under the current evidence and accepted thin-client decision.

The data key includes vault/daily-file selection, local date, executable/contract identity, and relevant environment overrides. Its value contains a last-good immutable snapshot, dependency manifest, freshness state, and one shared in-flight refresh. The layout key additionally includes content revision, actual width, screen budget, font/text settings, and appearance settings that affect geometry. Data can remain valid while a smaller display demands new folding.

| Input/event | Cache action |
| --- | --- |
| Same daily/dependency bytes | Reuse parsed data; reuse fitted layout if geometry matches. No Bob spawn. |
| Daily note rewritten with identical bytes | Rehash off the main thread; retain the semantic snapshot. Mtime change alone is not content change. |
| Linked task changes, daily bytes unchanged | Refresh; keep old content visibly Updating until replacement arrives. |
| Known unrelated note content changes | No overview refresh. |
| Creation/deletion/rename affecting basename or unresolved links | Re-resolve; a new duplicate basename can introduce ambiguity. |
| Settings, vault/configuration, executable, day override, or local day changes | Invalidate the affected key. Never label yesterday's snapshot today. |
| Watcher overflow/root change/failure | Mark freshness unknown, restore watching, and reconcile. |
| Successful capture | Immediately dirty affected data and refresh; do not rely solely on delayed events. |

Metadata prioritizes work; content hashes establish byte equality. To honor a strict unchanged-content contract, asynchronously validate known dependency contents on presentation even without a file event. Metadata alone can miss same-size or timestamp-preserving replacements. This is raw byte verification in Swift, not vault parsing. Hashing and JSON decoding stay off the main actor.

Watch directories or the vault tree so atomic-save replacement does not detach a watch from its inode. Extend the watcher to supply paths and flags, coalesce changes, and share one refresh. FSEvents signals invalidation; it does not prove content equality. Apple's guide requires rescanning after coalesced/dropped events and handling watched-root changes. [Apple FSEvents guidance](https://developer.apple.com/library/archive/documentation/Darwin/Conceptual/FSEvents_ProgGuide/UsingtheFSEventsFramework/UsingtheFSEventsFramework.html).

Existence dependencies matter: a missing daily note must populate when created; an unresolved task may resolve when another note appears. Basename resolutions depend on the namespace, not just the selected file. If namespace validity cannot be established cheaply after downtime or uncertain events, ask Bob to reconcile; do not perpetuate an old resolution.

Open by publishing cached content synchronously, showing/focusing the panel, then validating asynchronously. Replace only when semantic content changed. During uncertainty use a small Updating indicator, not a spinner replacing useful content. After validation fails, retain the last good snapshot with “Couldn’t refresh · Retry.” Empty and failed are distinct states. On a different day, use a current-day loading state rather than yesterday's plan.

The first miss bypasses the editor's typing debounce. Prefetch when Bob becomes available at launch. Repeated opening and watcher bursts join one operation. Generation checks cover source/configuration changes and panel modes: an overview arriving after typing cannot replace the draft preview. Give it a separate process lane so it cannot cancel submission, completion, or draft analysis.

Apple recommends keeping non-UI work away from the main thread and identifies approximately 100 ms as a noticeable discrete interaction delay. A task created in a main-actor context can still perform synchronous work there: wrapping file hashing in `Task {}` is insufficient. [Apple responsiveness guidance](https://developer.apple.com/documentation/xcode/improving-app-responsiveness).

**Fit the content to the screen, then resize once.** The budget is maximum usable panel content height minus the measured editor, footer, title/date, safe-area inset, padding, warnings, and group spacing. Use the hosting screen's visible frame and existing margins, not the headless 720-point fallback. Derive available space from the screen rather than current panel height to prevent a feedback loop.

Measure the same rendered content at its actual constrained width. Line counts cannot predict wrapping, emoji metrics, code, or metadata. The three task representations are:

1. **Full:** complete definition including recognized history subtrees.
2. **Details:** complete definition except Work/Schedule Log subtrees.
3. **Headline:** one visual line with ellipsis, source, actual status, and detail affordance.

A one-line view inevitably truncates long titles. Make full titles available through accessibility and task/detail actions; never shrink fonts to squeeze them in. Full/Details preserve nested content rather than clipping at an arbitrary depth.

Use a deterministic Auto allocator:

1. If all Full views fit, show all and expand only as far as needed.
2. Otherwise, if all Details views fit, show them. Restore whole history sections into spare space, current first and then upcoming ledger order.
3. Otherwise, begin with every Headline visible. Upgrade whole tasks to Details where they fit, current-session tasks first and then upcoming ledger order. Skip oversized upgrades so smaller later tasks can gain detail. Restore no history while any task body remains collapsed.
4. If Headlines themselves exceed the budget, use a single vertical scroll region at the screen ceiling with an explicit overflow cue.

This sacrifices history before task definitions and preserves more than a global single-line switch. It is an understandable priority rule, not an expensive knapsack optimum. Mixed detail levels need per-task disclosure labels. Global Full → Details → Headline is an acceptable simpler milestone, but is weaker than the request to retain as much task content as possible.

Use native ideal-size measurement or a small custom SwiftUI Layout with cached measurements. `ViewThatFits` evaluates alternatives in order and picks the first whose ideal size fits; it is a useful prototype, although per-task allocation needs explicit budgeting. Measure unscrolled content against the maximum preview budget. A constrained ScrollView fitting its frame does not establish that all its content fits. This last point is an inference from the layout model and current panel architecture. [Apple ViewThatFits](https://developer.apple.com/documentation/swiftui/viewthatfits).

Prewarm likely variants and retain height measurements. A safe lower bound can bypass enormous Full candidates without rendering thousands of history rows simply to prove they do not fit; retain their source data. Apply one settled height, anchored at the top as today. Keep layout during validation; never visibly cycle through candidates. Allow a small margin for fractional error and remeasure on width, font, display, or content changes.

Auto-fitting governs the default overview. Deliberate detail expansion may scroll. In overflow mode, use one scroll container with normal keyboard/pointer behavior and an obvious continuation. Apple recommends discoverable overflow and avoiding nested same-axis scroll views. [Apple scroll-view guidance](https://developer.apple.com/design/human-interface-guidelines/scroll-views).

**Alternatives and implementation risk.**

| Approach | Assessment |
| --- | --- |
| `bob plan -f json` on every opening | Useful precedent, but loses occurrences/full definitions and includes unrelated lane work. Poor final interface. |
| Blank input as dry-run `=` or `=x` | Describes mutations, varies with ledger state, and inherits time-sensitive capture semantics. Wrong read-only model. |
| Swift link/history parsing | Duplicates semantics and violates the thin-client decision. |
| Daily mtime/size cache only | Stale when tasks change; cannot prove byte equality. |
| One subprocess per task | Process/parsing overhead grows with task count. Batch instead. |
| Daemon or backend persistent cache first | Adds lifecycle/distribution/invalidation before Mac evidence warrants it. |
| Current-only overview | Compact but conceals the upcoming plan. Retain all upcoming sessions and fold detail. |

The main risks are incomplete dependencies, layout oscillation, enormous blocks, and independently installed Bob/app versions. Address them with contract fixtures and native performance/rendering checks, not speculative infrastructure.

Implement in order: extract reusable read-only block/history helpers and define the additive Bob contract; add Mac snapshot caching/invalidation; connect the blank-editor overview and layout allocator; verify rendering and latency on a Mac. No plugin or vault-writing changes are inherently required.

Acceptance criteria:

- Warm opening is visible and ready to type within a proposed p95 target of 50 ms on Bryan's Mac. No disk access, process wait, or synchronous hashing occurs on the show path. Unchanged warm openings spawn no Bob process for this overview.
- Measure first overview availability separately. An initial proposed p95 budget is under 150 ms for eight sessions and twenty ordinary linked tasks. This is a target to test, not an achieved measurement.
- Add metadata-only signposts for validation, hydration, layout, fit mode, cache hits, and subprocess count. The app already has signposts. Profile with Instruments and real large histories.
- Verify identical rewrites, child/status changes without daily changes, same-size edits, atomic replacement, missing-note creation, deleted IDs, ambiguous basenames, and task settings changes.
- Semantic fixtures cover multiple current entries, unnamed/empty upcoming entries, repeated tasks, closed linked tasks, embeds, mixed prose, struck links, fences, nested tasks, CRLF, and no final newline.
- Native rendering checks cover detail thresholds, narrow/wide widths, small screens/display changes, large text, Unicode titles, light/dark and increased contrast. Auto must have zero settled vertical overflow in normal cases; exceptional overflow keeps every occurrence reachable.
- Test typing/clearing during refresh, retained drafts, successful/failed submit, midnight, sleep/wake, unavailable Bob, unsupported flags, watcher recovery, and late callbacks. They must not steal focus or publish the wrong pane.
- VoiceOver reports session/task status, visible detail level, disclosure actions, and refresh errors. Empty-editor Return cannot accidentally act on an overview task.

Native validation is outstanding because research ran on Linux. The arrangement above is a design sketch, not a verified SwiftUI render. I have not inspected Bryan's real daily note or assumed its actual history sizes. These limits particularly affect the final fit policy and cold-load budget.

**Recommended solution:** implement a default read-only Today’s Pomodoros overview through additive `capture-pomodoros --with-tasks`. Keep semantics in Bob, batch hydration, retain a dependency-aware in-memory snapshot, and show it immediately while validating in the background. Fit the existing panel with Full, history-free Details, and Headline views, retaining current-task detail first and permitting a clear single-scroll fallback only when necessary. Require Mac latency and layout evidence before adding disk persistence, a daemon, or a second timer.
