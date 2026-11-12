# Walker footers that follow bracket mode

Independent design research by **cdx** · 2026-11-12

## Recommendation in brief

This is a good idea. The footer should explain the navigation that `[[` and `]]` will actually perform. Keep the existing `[[ s w n ]]` selector and replace the ambient review display with **one contextual footer slot**, presenting Review, Lanes, or Links according to the selected family. Preserve the review footer's established visual language. Give the lane footer exact Pending/Next/Ready counts, and give the links footer previous/next destination previews.

The essential distinction is **selected walk**, not “review session in progress.” The selected family already persists per device and vault, including across restarts. Neither a current landing nor a nonempty queue should decide which family owns the footer.

The most important requirement adjustment: **`n` is not a list walk**. It follows the first matching previous/next body link in the active note. It has no meaningful global total, rank, or completion percentage. A beautiful Links footer is a small directional map, not a task counter.

This report is research, not an implementation. No product code or canonical memory was changed. I did not consult the other swarm reports or their findings.

## What the current implementation establishes

The primary checkout was `bob-cli` **753b4e48f97203b9fdaa404af625b1f10a681df3**. The opened linked checkout was `bob-plugins` **00edf762b9856c1d935faf587ee2da670a87cc74**. Source references below identify those snapshots rather than depending on an ephemeral workspace path.

| Finding | Why it matters | Evidence |
| --- | --- | --- |
| Navigation already owns `bracketRepeatType`, restricted to `s`, `w`, `n`, or unset. The in-memory value is authoritative; local storage is persistence. | Do not introduce another “active walker” flag, infer it from focus, or parse the selector's DOM. | C1 |
| Family command callbacks select their family before attempting navigation. Clicking a selector letter selects without moving. Internal advances do not select. | An empty or unsuccessful family command still changes the footer. A click must update it immediately even though no landing event follows. | C1, C2 |
| The current review footer is independent of bracket mode. It already hides for unavailable Tasks and usually for an empty queue, except a prioritized off-walk task can retain an Alt+P preview. | “Always shown” means ambient across walk modes, not literally unconditional visibility. Preserve this distinction when evaluating regressions. | C3 |
| `api.laneWalk` v2 returns both the actual navigation entries and `pending`, `next`, `ready`, `total`, Today-excluded counts, and `reviewReady`. | Counts should come directly from this API, not from checkbox scanning, review tiers, or dashboard text. | C4 |
| `w` walks Pending → Next → Ready off today's open Pomodoros. Ready excludes NEW/ROTTEN review buckets. Pending and Next can also be due in the `s` review walk. | The two task walks serve different purposes and are not mutually exclusive task sets. Do not present their numbers as a partition of the vault. | C4, C5, M1 |
| Lane navigation uses cursor, live anchor, or an insertion point from the anchor's former lane/path/line. It deliberately preserves the old lane origin after a lane change. | A removed/moved task must not leave a fabricated current rank or silently “teleport” the footer to its new lane. | C5 |
| `n` reads the active Markdown editor's unsaved content when available, otherwise cached note content. It finds the first matching body link, skipping frontmatter and fenced code. | A second regex or a cached saved-only parse would disagree with the key. | C6 |
| `n` accepts exact `prev`/`next` labels and the existing directional arrow-label forms. Missing safe Markdown targets can be created; period notes delegate to Bob, ordinary notes to Templater. | Preview destinations and creation intent. Never run the opening/creation path while painting. | C6, C7 |
| Review rendering already has pure models, an idempotent DOM painter, a width-fitting algorithm, tests, and a Chromium preview. | Extend proven machinery rather than replacing the mature review design. | C3, C8 |

## Critique: the benefit and the real costs

**The benefit is contextual honesty.** Today the switcher can promise a lane or link walk while the large adjacent display continues to describe morning review. The proposed change makes the visible state and the repeated action agree. It also lowers persistent review pressure when Bryan is choosing work or moving between period notes.

**The cost is lost ambient review information.** Review obligations and the review footer's off-walk Alt+P preview will no longer remain visible in `w` or `n`. That is an intentional tradeoff, not a bug to repair by adding an always-visible review badge elsewhere. Review remains discoverable through the existing `s` selector, `]s`, commands, and review surfaces. Keep Alt+P itself unchanged. Initially, keep its footer preview within the `s` variant; do not expand this request into a universal task-action bar.

**A family selector is not a session tracker.** Starting a Pomodoro, editing another note, finishing the review queue, opening a modal, or waiting five minutes must not silently choose another footer. A restored `s` selection should restore the Review footer. If a different “currently conducting review” concept is later wanted, that would need a separate product decision.

**More footers could make the interface worse if implemented literally.** Three independently mounted status widgets, independent refresh timers, and three different definitions of “current” would produce crowding and races. The product should have three presentations of one contextual area. There is no need for a new extensible walker framework, additional settings matrix, or arbitrary plugin provider registry.

**Do not turn the display into a progress dashboard.** Both task queues change after edits; rank is location in the current queue. Repeatedly pressing `]]` does not finish work. `n` follows local links that need not be reciprocal or form a finite chain. Avoid completion bars, “percent done,” and invented link totals.

As a design precedent, VS Code recommends short status labels, restrained icons, and few contributed items because the area is shared. I apply that principle to Bob, while retaining Bob's established semantic tier/lane colors. This is a design inference, not evidence that VS Code's exact layout should be copied. [VS Code status-bar guidance](https://code.visualstudio.com/api/ux-guidelines/status-bar)

## Proposed experience

### One stable selector, one changing context

Retain the familiar switcher, including its selected thumb, keyboard flashes, and click-without-navigation behavior. Give the contextual area a consistent family label: **Review**, **Lanes**, **Links**. Use the same baseline, typography, spacing, and divider vocabulary across all three.

The following are content wireframes, not pixel-accurate screenshots. A bracket around a letter indicates the existing active thumb. Numbers are synthetic examples.

```text
Review, off a due row
⟳ Review 18 due · 12 commitments · PRE 2  NEW 4  WIP 3  NEXT 3 … | ✓ 2/5 today   [[ [s] w n ]]

Review, on a tickler
⟳ Review 11/18 · TICKS 1/3 · scheduled today · [Alt+P roll P2 1/1] | ✓ 2/5 today [[ [s] w n ]]

Lanes, off a member row
Lanes 24 · off Today · PENDING 4  NEXT 7  READY 13                              [[ s [w] n ]]

Lanes, on a member row
Lanes 6/24 · PENDING 4  [NEXT 2/7]  READY 13 · Alt+N release                    [[ s [w] n ]]

Links, both directions available
Links · [[ Prev: 2026-W45       2026-W46       Next: 2026-W47 ]]                [[ s w [n] ]]

Links, next note can be created
Links · [[ Prev: Nov 11        Nov 12         Create: Nov 13 ]]                [[ s w [n] ]]
```

The last column represents the existing selector, not a second new selector. The target previews in Links are direction controls; the family letters only select. In production avoid redundant brackets where the directional button styling already communicates the keys.

The context area should grow into available space and shed optional content. Keep the selector fixed and visible. Do not move its letters horizontally as counts change. Arrange the two existing plugin-owned items intentionally beside each other, validating ordering in Obsidian rather than depending on plugin load order. Do not reparent another plugin's DOM or use broad selectors against unrelated status items. A single shared DOM host can be reconsidered if actual host layout prevents reliable adjacency; it is not a prerequisite for the first release.

### Review footer: preserve expertise, gate ownership

The `s` variant keeps the nine-tier order, commitment/upkeep boundary, stage names, current row detail, tier colors, upkeep meter, and TICKLER Alt+P answer chip. Keep the existing interpretation of `Review r/N` and `TIER i/M` as queue positions. Do not modify review answer/advance semantics, freshness eligibility, or task writes.

When `s` is selected but the cursor is off the queue, show the existing queue overview and applicable off-walk Alt+P preview. A parked review anchor is not the same thing as a current cursor row. Do not keep displaying a current-tier fraction after the cursor has left that row.

**Recommended change beyond the literal request:** when the selected review queue is valid and empty, show a quiet `Review clear` state, retaining a valid Alt+P preview if one exists. This makes successful completion legible without disappearing. “Clear” describes the current eligible queue; it does not assert that every task or weekly commitment is done. No celebration animation and no automatic switch to `w`.

Keep the main Review activation as forward walk navigation, equivalent to one `]]` while `s` is selected. In a clear or unavailable state, make the contextual navigation control inactive. The mode selector remains usable.

### Lane footer: exact inventory, optional position

At normal width, show **all three lane counts, including zeros**, in fixed Pending → Next → Ready order. A stable three-part inventory is easier to learn than chips that appear and disappear. Unlike review's nine tiers, this is only three groups.

The count contract is:

```text
PENDING = queue.counts.pending
NEXT    = queue.counts.next
READY   = queue.counts.ready
TOTAL   = queue.counts.total = queue.entries.length
```

Each count means tasks the `w` walk can actually visit now. None is a lane cap, all-vault checkbox count, number reviewed, or number still unvisited. Explain `off Today` as “not linked under today's open Pomodoros” in the tooltip. Ready uses the existing freshness gate. Preserve the queue's own handling of hidden, blocked, scheduled, recurring, and other eligibility cases; never reimplement those rules in the footer.

On a validated current member, change that lane's count to its local position, such as `NEXT 2/7`, and show `Lanes 6/24`. Its other two chips retain counts. In the tooltip say “position 6 of 24; Next task 2 of 7.” If no current member is validated, return to `Lanes 24`; do not manufacture `0/24` or present the last anchor as the current row.

For a live resume anchor or an anchor gap, an optional wide-only caption can say `resume in Next` or `resume after Next`; derive it from navigation's origin resolver. It is lower priority than all lane counts. In particular, after releasing an anchored task from Next to Ready, do not call the changed row the walk's new Ready origin when navigation deliberately continues from its old Next tuple.

Reuse existing lane colors. Pending may abbreviate to **WIP** under pressure, consistent with the existing review footer and official alias. Prefer full **PENDING** when it fits. Current lane gets a subtle tint or underline plus the explicit fraction, so color is not the only cue.

The main Lanes activation takes one forward step through the normal command path. Keep count chips informational in version one. Clicking “Ready 13” should not unexpectedly skip the remaining Next work or change filters. Lane jumps already have `]W`/`[W` and `]}`/`[{`; teach these in the tooltip. Keep detailed Work Log content and task titles in existing landing notices, not in this one-line footer. An optional last-priority action hint can reuse the landed-row semantics: Pending/Next `Alt+N release`, Ready `Alt+N next`.

For an empty queue, reuse the existing empty-notice classification:

| Available queue condition | Compact footer | Expanded explanation |
| --- | --- | --- |
| `reviewReady > 0` | `Lanes clear · 9 Ready in review` | Those Ready tasks are waiting in NEW/ROTTEN review; `]s` visits them. Include excluded Today count if relevant. |
| No review-held Ready, some excluded Today tasks | `Lanes clear · 8 on Today` | All otherwise eligible lane tasks are already on today's plan. |
| Neither | `Lanes clear` | No eligible Pending, Next, or Ready tasks. |

These are explanations of why `w` is empty, not an automatic request to switch modes. Leave `w` selected. Counts must never silently become zero while Tasks or Today is loading.

### Links footer: preview the two actual destinations

Use previous and next target labels, with the current note between them when space allows. Prefer the resolved target's readable basename over the literal alias `prev` or `next`; give the full vault path and subpath in a tooltip. Render file names as text, not HTML or Markdown. Duplicate basenames need enough path context to distinguish them.

Each direction has a separate state:

| State | Presentation | Activation |
| --- | --- | --- |
| Existing supported Markdown target | `Prev: W45` / `Next: W47` | Existing labeled-link command in that direction. |
| Missing target eligible for existing creation behavior | `Create: W47` | Existing creation/opening route, only on activation. |
| No matching label | `No previous link` / `No next link` | Disabled. |
| Matching but unsupported/unsafe target, or a known missing creation provider | Quiet unavailable state | Disabled; tooltip explains the reason. |
| No usable Markdown context | `Links · Open a note` | No direction enabled. |

A creation candidate is not a promise that I/O will succeed. Runtime failures remain handled by the existing command. Preview can inspect capabilities but must not call `ensureNote`, create folders, load templates for writing, or open destinations. Missing period notes continue through Bob; generic safe Markdown notes continue through Templater. Preserve the current first-match rule even if a later same-labeled link would resolve successfully.

Refresh as the active note changes. `n` is not restricted to daily or period notes, and cannot infer a target from calendar arithmetic when no matching link exists. Do not add upward navigation, backlinks, sibling enumeration, a history list, or an uppercase `N` walk in this change. Counts remain ignored by `n`, as today.

A footer destination click should take the same direction as the corresponding key. Revalidate the source note, source revision, mode, and destination before activation; if they changed, refresh instead of opening a stale preview. The footer should not create a note from a destination that vanished while a cached read was outstanding.

## Explicit state contract

“Active” means the family selected by the existing bracket-repeat state. Persist only that existing selection. Footer counts, positions, render state, and target previews are derived, not stored in notes or plugin settings.

| Event or condition | Required behavior |
| --- | --- |
| No saved/used family | Keep the unselected `[[ s w n ]]` indicator; contextual footer is absent. Do not default silently to `s`. |
| Startup with saved `s`/`w`/`n` | Restore that variant before the first walk; load its data independently. |
| Explicit family command or selector click | Update selection and footer immediately, including when the walk is empty or cannot navigate. |
| Internal review answer advances while another family is selected | Do not steal selection back to `s`. |
| User leaves a landed task | Keep selected family; drop current-row claims that no longer validate. |
| Review or lane data loading | Keep the family identity with `Loading…`; hide numeric claims. No success-like zero. |
| Dependency unavailable | Selected family plus a concise unavailable explanation; inactive movement control. |
| Tasks unavailable, `n` selected | Links still works through navigation; never gate it on Tasks availability. |
| Navigation state API absent/unloaded/incompatible | Hide the contextual footer because its selected family cannot be established reliably. Do not resurrect ambient review. |
| Ledger Tools unavailable | Its contextual area disappears; Navigation's selector and original commands retain their existing capabilities and notices. |
| Midnight | Keep the selected family; invalidate day-sensitive queues and anchors using existing local-day rules. |
| Active leaf/window changes | Derive position and link targets from the same context the key command will use. Never show another leaf's links as actionable here. |

Loading/error labels and the quiet empty Review state are deliberate refinements to the existing hide-on-unavailable/empty behavior. The selector alone remains the fallback when the footer provider itself is absent.

## Visual and accessibility direction

The current production preview has a compact, typographic character: a strong leading label, quieter detail, colored group text, a thin division before upkeep, and a clearly distinct Alt+P answer chip. Extend that language rather than drawing three unrelated widgets.

- Keep the established interface font and roughly 12px status-bar scale; use tabular numerals. Do not shrink text further to force the full state into a narrow slot.
- Use one small family icon at most. A Review rotation mark is already meaningful; Lanes and Links can lead with text. Avoid adding emoji trains, a mini Kanban board, or decorative progress rails.
- Use existing tier/lane tokens, normal text for primary facts, and theme-aware muted text for secondary facts. A zero is quieter, still legible. Full-width warning backgrounds are excessive for indexing or a missing local link.
- Keep height fixed. Family changes replace content without a width animation or delayed crossfade that briefly displays the wrong mode. Retain the existing selector animation, respecting reduced-motion preferences.
- Prefer stable controls and DOM nodes; update text only when changed. Do not rebuild the footer on every cursor tick or move focus during background paints.

Use measured available width, not only viewport breakpoints:

| Priority | Review | Lanes | Links |
| --- | --- | --- | --- |
| Always retained when content can fit | Family, total/clear/unavailable state | Family, total/clear/unavailable state | Family, direction availability |
| High | Current tier and essential answer chip | Three lane counts, current lane identifiable | Previous/next readable targets |
| Lower | Other groups, stages/detail, upkeep according to existing tested fit rules | Whole-walk position, off-Today caption, action hint/resume caption | Current note, long folder prefixes |
| Minimum | Compact family summary; selector still visible | `Lanes 24 · WIP 4 N 7 R 13`, then total if unavoidable | `Links · Prev / Next`, preserving missing/create distinctions in accessible labels |

The proposed lane collapse order deliberately protects the user-requested lane counts ahead of the optional position and hint. Ellipsis must never make a missing destination appear present. Full values and definitions stay available in tooltips and accessible labels. Test the minimum presentation with large counts and long Unicode note names.

Obsidian treats status items as either informational or interactive, so a few clear controls fit the host's established model. [Obsidian status bar](https://obsidian.md/help/status-bar)

Use real buttons for movement and mode selection, visible keyboard focus, descriptive names, and appropriate selected/disabled states. Do not turn every text chip into a button. Ensure meaningful status changes can be announced without moving focus, while avoiding a live-region announcement on every cursor motion. [W3C status messages](https://www.w3.org/WAI/WCAG22/Understanding/status-messages.html)

The active mode and current lane need text/shape cues as well as color. Ordinary small text should meet a 4.5:1 contrast target against its actual background in both themes; the theme's faint token is not automatically acceptable for meaningful counts. These are proposed accessibility acceptance criteria, not a claim of tested conformance. [W3C use of color](https://www.w3.org/WAI/WCAG22/Understanding/use-of-color.html), [W3C contrast](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html)

## Recommended implementation boundary

### Preserve ownership and share facts

The smallest reliable design keeps **Navigation responsible for navigation state and interpretation**, and **Ledger Tools responsible for the contextual status-bar item**. The latter already hosts the review painter, queue snapshots, cursor refresh, resize observer, and lifecycle cleanup. Add two variant models there. Navigation's independent selector remains useful if the contextual item is unavailable.

| Approach | Assessment |
| --- | --- |
| CSS hides review based on the lit selector; unrelated widgets implement `w`/`n` | Reject. DOM becomes an accidental API; snapshots and startup ordering can disagree. |
| Move all footer rendering and review data into Navigation | Coherent eventual ownership, but unnecessary migration and risk to mature review behavior. |
| Extend Ledger's one context item; publish a small Navigation state/preview API | **Recommended.** Keeps existing strengths and makes cross-plugin dependencies explicit. |

Add an additive, versioned Navigation namespace, tentatively `api.walkers` v1. Its exact names are implementation choices; its responsibilities should remain narrow:

1. Read the normalized selected family from `readBracketRepeatType()`.
2. Subscribe to changes and return an unsubscribe function. Publish after the authoritative in-memory change even if persistence fails. Read the current snapshot when subscribing so late plugin startup is correct.
3. Describe the active note's previous/next link candidates without opening or creating anything. Reuse `getActiveMarkdownContext()`, `findFirstRenderedLink()`, and `toLineLinkCandidate()`; annotate known provider availability without side effects.
4. Describe the lane cursor/origin against the caller-supplied queue snapshot using the same resolver as actual lane navigation. This prevents a second interpretation of anchor gaps or lane changes.

Keep the top-level API compatibility convention already used by `quickRoll`; version the added namespace. Do not expose the raw local-storage key as a contract. Do not mirror selection into Ledger's settings. Keep APIs listener-safe: a failing footer callback must never break a command or prevent navigation.

Refactor the current status controller into a family router before asking for family-specific data. `s` uses its existing memo/model/painter. `w` uses `apiLaneWalkQueue()` and its immutable result. `n` asks Navigation for link context and has no Tasks/Today dependency. Reuse the review painter internally rather than making `freshnessFooterView()` understand lanes and links.

Known implementation touchpoints:

- Navigation `546-plugin-bracket-repeat.js`: authoritative selection and notification.
- Navigation `547-bracket-mode-indicator.js`: existing selector behavior; coordinated visual placement.
- Navigation `480-review-jump-and-nav-api.js`: additive API assembly; keep its source-fragment size limit in mind.
- Navigation `542-lane-walk-model.js`, `670-plugin-project-files.js`, `680-plugin-link-parse.js`: shared origin and link interpretation.
- Ledger `240-plugin-freshness-status.js`: route selected mode, own async generation checks and active-family lifecycle.
- Ledger `120-freshness-footer.js` and `121-freshness-footer-paint.js`: preserve review presentation; add the clear-state variant deliberately.
- Ledger `071-lane-walk-model.js` and `180-plugin-plan-and-ready.js`: consume existing queue/counts; no new membership logic.
- Ledger `220-plugin-heading-and-review.js` and `290-plugin-today-and-location.js`: hook the consolidated live-widget refresh and active-view/cursor paths.
- Both plugin lifecycles and stylesheets: subscribe/unsubscribe, late availability, cleanup, width allocation, accessible controls.

Create separate bounded source fragments for new models/painters where useful. Edit `src/`, rebuild generated `main.js`, and maintain the repository's fragment size rule. No Rust evaluator change, new CLI command, release/version change, or Mac Capture change is required by this design.

### Reliability invariants

**One snapshot per paint.** Obtain queue counts and positions from the same immutable result. Do not combine today's counts with yesterday's rank, or an old Tasks array with a newly invalidated Today set.

**Generation-checked async work.** Tag a link preview request with family, source file, editor/document revision, and a generation counter. A response can paint only if that identity is still current. Changing to `w` must immediately invalidate an outstanding `n` read. Disposing/reloading plugins invalidates all pending work.

**Mode change is immediate; data work is coalesced.** Preserve fast mode acknowledgement, with a neutral loading state if necessary. The existing controller has approximately 50ms cursor-context and 150ms data refresh coalescing; reuse those as starting points, not contractual latency guarantees. Cursor-only updates reuse queues. No full-vault rescan on every keypress and no new periodic polling loop.

**Dependency lifecycle is explicit.** Read the state on layout ready and on provider-ready notification; detach on unload. Test both plugin load orders. A temporarily missing provider cannot mean “the selected mode is Review.” A callback from an old provider cannot revive a disposed footer.

**Activation rechecks context.** Route movement through existing commands, with a mode guard; do not synthesize cursor movement, consume a review answer, or mutate selection as a side effect of painting. A stale `s` button must never activate after the selector has become `n`. Clicking a direction uses one step, not an unrelated pending Vim count; keyboard repeat retains existing count semantics.

**Read-only means rendering.** Reading, hovering, focusing, switching mode, and resizing never change tasks or create notes. An explicit Links activation can invoke existing note creation. This distinction belongs in the glossary and tests.

## Proposed glossary integration

Add `Walker Footer` as the parent concept, with the existing `Morning GTD Review Footer` / `review footer` as its `s` subtype. Do not rename the existing glossary key or break its inbound references. “Active” in the entry should explain selected repeat behavior so later agents do not reinvent session state.

Suggested new strand body, to publish with the feature rather than as an assertion that it exists now:

> # Walker Footer
>
> The contextual item in Obsidian's desktop status bar that explains the selected bracket walk: the family that `[[` repeats backward and `]]` repeats forward. Beside the `[[ s w n ]]` selector, it shows one of three views: the [[morning-gtd-review-footer]] for `s`, the lane footer for `w`, or the links footer for `n`. Selection follows the existing per-device, per-vault bracket-repeat mode; it does not depend on the cursor staying on a task, on work remaining, or on an inferred review session.
>
> A walker footer answers “What will these keys walk, and what is available here?” The review footer shows the due review queue, its current tier, and commitment/upkeep context. The lane footer counts Pending, Next, and freshness-eligible Ready tasks off today's open Pomodoros, showing position only when a current member is validated. The links footer previews the active note's first matching previous and next body links, including whether following one would create a note. Task fractions are positions in a changing queue, never completion percentages; links have no invented queue total.
>
> An empty walk stays selected and reports its empty state. Loading or unavailable data is distinct from zero. The footer's display is read-only: rendering and selecting a family never stamp tasks, change lanes, or create notes. Explicit navigation uses the existing walk commands; following a missing eligible link may create its note. The selector chooses a family without moving, while the footer's navigation controls move within that family.

In the existing review entry, change the opening to identify it as the `s` walker-footer variant; preserve its specialized tier, stage, answer-chip, and meter details. If adopting the recommendations above, replace its currently accurate “hides when Tasks is unavailable” and conditional empty-hide statements with the new unavailable/clear behavior. Keep the `review footer` alias.

The user's request explicitly asks for the new term and subtype relationship. A later formal implementation plan should carry the per-note memory decisions required by `/sase_memory_write`: one for the new strand and one for the existing review strand correction. Regenerate instructions through `sase memory init` when publishing those canonical changes. This research only proposes wording; it does not publish an unimplemented contract.

Update the plugin references for bracket repeat, lane walking, and the Ledger footer, plus the affected footer passages in `bob-cli/docs/freshness.md`. No new generic “walker” term is necessary unless other usage develops.

## Evidence and verification

### Checks performed in this research

The following six existing targeted test files passed together under Node's test runner at the inspected plugin snapshot:

```text
scripts/test-navigation-bracket-repeat.cjs
scripts/test-navigation-bracket-mode-indicator.cjs
scripts/test-navigation-lane-walk.cjs
scripts/test-ledger-tools-lane-walk.cjs
scripts/test-ledger-tools-freshness-footer.cjs
scripts/test-navigation-period-links.cjs
```

I also ran `scripts/preview-review-footer.cjs`. Its six light/dark and width renders reported **zero failed checks**, and I visually inspected the production 700px light-theme rendering. This substantiates reuse of the current footer implementation. It does not validate the proposed new layouts, real Obsidian status-item ordering, accessibility conformance, or pop-out window behavior. No live vault census was needed; all example counts above are illustrative.

### Acceptance tests that matter for implementation

| Area | Required evidence |
| --- | --- |
| Mode truth | Cold/unset and invalid storage; restored `s/w/n`; selector click without movement; failed family command; palette commands; lowercase/uppercase repeats; internal advances do not change mode. |
| Isolation | At most one contextual variant visible; an old async `n` result cannot paint over `w`; no review detail in `w/n`; no Tasks requirement for `n`. |
| Lane truth | Footer counts equal the exact queue snapshot; zero lanes; Today exclusion; NEW/ROTTEN exclusion from Ready; due Pending/Next overlap with review; release/link/move/delete/undo; anchor gaps and midnight. |
| Position | Current member, off-row, parked anchor, ambiguous/stale line, changed lane, repeated text with different block IDs; no stale fraction after a row leaves. |
| Link truth | Unsaved content, Reading view, first-match ordering, frontmatter/fence decoys, exact and arrow labels, one/no directions, subpaths, duplicate basenames, unsupported targets, generic/period creation, provider unavailable, source switched during read. |
| Side effects | Zero writes on paint/resize/selection; activation delegates once; preview never calls period ensure or Templater creation; stale destination refuses. |
| Lifecycle | Both plugin load orders, unload/reload, missed initial event, listeners disposed, missing APIs, thrown listener, no duplicate status item. |
| Visual fit | All variants, light/dark, narrow remaining space, long names, large counts, theme text size, keyboard focus, reduced motion, existing Keep indicator and other status items present. |
| Host behavior | Real Obsidian checks for editor focus, active pane and pop-out windows, source versus reading view, and identical key/click destination. |

Extend the existing production-code Chromium preview rather than maintain an unrelated hand-drawn mockup as the only visual gate. Add an integrated status bar fixture containing the selector and neighboring items, since the existing isolated footer render does not prove available width in the real shell. Run build consistency, relevant tests, and the repository docs gates; deploy changed plugins using `bob plugins sync` according to repository instructions during implementation.

### Source ledger

All code entries below are from the plugin commit stated above unless explicitly marked bob-cli. Paths are repository-relative.

- **C1 — Mode authority and repeat dispatch:** `plugins/bob-navigation-hotkeys/src/546-plugin-bracket-repeat.js`, especially `rememberBracketRepeatType`, `readBracketRepeatType`, and `repeatBracketWalk`; `src/490-plugin-lifecycle.js:158` onward for family command wrappers. `scripts/test-navigation-bracket-repeat.cjs` verifies persistence, dispatch, counts, and excluded internal callers.
- **C2 — Existing selector:** `plugins/bob-navigation-hotkeys/src/547-bracket-mode-indicator.js`, especially `buildBracketModeView`, `setupBracketModeIndicator`, `selectBracketModeFromIndicator`, and teardown. `styles.css:4125` onward and `scripts/test-navigation-bracket-mode-indicator.cjs` cover visual state, focus, startup, and cleanup.
- **C3 — Review display and controller:** `plugins/bob-ledger-tools/src/120-freshness-footer.js`, especially `freshnessFooterView` and `freshnessFooterHintOnlyView`; `src/121-freshness-footer-paint.js`, especially `freshnessFooterFit`; `src/240-plugin-freshness-status.js:119` onward for coalescing, context, painting, and click fallback. `styles.css:324` onward.
- **C4 — Lane membership, counts, and readiness:** `plugins/bob-ledger-tools/src/071-lane-walk-model.js`; `src/180-plugin-plan-and-ready.js:900` onward (`apiLaneWalkQueue`, `laneWalkApi`). `scripts/test-ledger-tools-lane-walk.cjs` checks count parity, memoization, and unavailable reasons.
- **C5 — Lane navigation/empty semantics:** `plugins/bob-navigation-hotkeys/src/542-lane-walk-model.js:118` onward (`resolveLaneWalkOrigin`) and `:593` onward (`buildLaneWalkEmptyNoticeModel`); `src/544-plugin-lane-walk.js`; `docs/bob-navigation-hotkeys.md:455` onward. `scripts/test-navigation-lane-walk.cjs` checks runtime/planner behavior.
- **C6 — Labeled-link lookup and source:** `plugins/bob-navigation-hotkeys/src/670-plugin-project-files.js:151`, `:673`, and `:794`; `src/680-plugin-link-parse.js:1` onward. `scripts/test-navigation-period-links.cjs` covers arrow matching and period links.
- **C7 — Candidate/creation boundary:** `plugins/bob-navigation-hotkeys/src/640-plugin-notes-and-task-move.js:221` onward (`toLineLinkCandidate`, `openOrCreateLinkCandidate`, `createNoteFromLinkCandidate`); `src/670-plugin-project-files.js:24` and `:118` onward for safe creation paths and Bob-owned periods.
- **C8 — Existing visual verification:** `scripts/preview-review-footer.cjs`, `scripts/preview-review-footer.template.html`, and `scripts/test-ledger-tools-freshness-footer.cjs`.
- **C9 — Documented contracts:** `docs/bob-navigation-hotkeys.md:497` onward (selection, counts, uppercase behavior, link semantics, and selector); `docs/bob-ledger-tools.md:190` onward (review footer). **bob-cli:** `docs/freshness.md:593`, `:595`, and `:786` onward (review tiers, positions, stages, preview).
- **M1 — Audited project memory:** `glossary:morning-gtd-review-footer`, `glossary:task-freshness`, `decisions:review-walk-is-tiered`, `decisions:recurring-occurrences-walk-when-due`, and `decisions:task-lanes-are-sticky`, read through `sase memory read`. Superseded portions were interpreted using the current recurring-tier decision and current code.

## Recommended solution

Implement **one mode-selected contextual footer, beside the existing selector**, using Navigation's bracket-repeat state as the sole authority and Ledger Tools' existing footer controller as the rendering owner. Preserve the `s` review presentation; add a `w` variant driven directly by the lane queue's three counts; add an `n` variant previewing the active note's real previous/next targets and creation intent. Share the existing navigation resolvers rather than recreating their rules.

Adopt three explicit refinements: keep a quiet selected-family empty state, distinguish unavailable data from zero, and scope the current ambient review/Alt+P footer to `s`. Keep task membership, keymaps, persistence, and answer semantics unchanged. Publish the new **Walker Footer** glossary concept with the existing review footer as its subtype when the feature lands.

This gives Bryan a useful, restrained display whose content answers the same question as the keys: **what am I walking now?**
