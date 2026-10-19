**Today task markers: a quiet day signal backed by the existing ledger**

Independent research by **cdx**, 2026-10-19. I did not read or request the other swarm researchers' reports, transcripts, or findings. This report proposes a design; it does not implement or deploy the feature.

**Assessment.** This is a good idea if the marker answers one narrow question: **“Is this task on today's plan?”** It is especially useful while reviewing an area or project note, where today's ledger membership is otherwise invisible. The existing Next and In Progress checkboxes cannot answer that question: those lanes are sticky, and a task can remain in either lane after its last link is removed. The marker should make that independent relationship visible without adding another stored status.

My preferred design is a small, static, monochrome **sun glyph immediately after the task checkbox**, with the accessible name and tooltip **“On today's plan.”** It should appear on identifiable open task rows in Live Preview, Reading view, and Tasks query results. Reuse Bob's Today membership model, then add explicit open-task and cache-readiness checks. Do not write a tag, field, emoji, or new checkbox character into the vault.

**Clarifying the requirement before choosing an icon.** “Tasks that are in today's daily file” has at least three meanings. They should not become one boolean:

| Possible meaning | What it selects | Recommendation |
| --- | --- | --- |
| Physically stored in today's daily note | A daily checklist or task, even when absent from the plan | Do not use this for the proposed marker. |
| Mentioned anywhere in today's daily note | Prose references, work history, closed sessions, arbitrary links | Do not use this for the proposed marker. |
| In Bob's existing Today set | Open tasks with dedicated links under today's open Pomodoros | Use this. It agrees with the dashboard and `bob plan`. |

The third interpretation is an explicit proposed adjustment to the user's wording, supported by the existing decision **Today Is Read From The Ledger, Never Written To Tasks** and `docs/plan.md`. A project task can qualify while residing in `project.md`; a task physically in today's daily file can fail to qualify. If literal residence is the real intent, name that feature “In today's note” and design it separately. Do not silently change the meaning of Bob's established Today concept.

Additional proposed scope adjustments:

- Mark **task rows**, including identifiable transcluded task rows. Do not initially add Today marks to every arbitrary task link throughout the vault.
- Keep the daily ledger's plain Task Links unchanged. Their placement already conveys the plan relationship, while the amber half-ring and unlock mark provide additional information.
- Make the first version informational. Clicking a tiny sun should not complete, unlink, schedule, start, or move a task. Existing planning gestures continue to own those actions.
- Leave Source mode raw. A display-only indicator is not part of the Markdown document.
- Promise support for named surfaces, not “everywhere Obsidian displays text.” Custom Dataview output, Canvas, search snippets, exported PDFs, and third-party boards need separate identity adapters or explicit exclusions.

These adjustments reduce ambiguity and implementation scope while preserving the useful part of the request.

**Why it is worthwhile, and where it can disappoint.** The marker turns a cross-note lookup into a glance. It can prevent duplicate planning and makes it easier to review a project without losing track of the day's commitments. A separate daily selection is also an established product pattern: Microsoft's My Day lets users select tasks from existing lists and resets daily while retaining unfinished tasks elsewhere. That supports the conceptual separation; it is not evidence that a particular icon will work best for Bryan. [Microsoft: My Day and suggestions](https://support.microsoft.com/en-US/ToDo/my-day-and-suggestions)

The principal risk is semantic surprise, not icon rendering. A task worked on this morning can lose the marker after its last open Pomodoro closes, even though it is still In Progress. That is correct under Bob's Today definition: the remaining plan and completed work history are different. A scheduled date of today also does not qualify by itself. Explain the marker as **“On today's plan,”** rather than “Worked today,” “Due today,” or “Active.”

There is also a real visual cost. Bob already has status checkboxes, lane tints, a task identity glyph, priority marks, date marks, freshness marks, and tags. One more full-sized colored pill would make the task harder to read. The new signal earns its place only if it remains compact, appears on a limited subset of rows, and proves more useful than the existing TODAY dashboard. A one-week usage review should ask whether Bryan recognizes planned tasks faster and whether the marker ever appears wrong. If its only useful location turns out to be an existing Today list, the feature is mostly redundant.

**What the existing implementation actually provides.** I inspected bob-cli at `9217a475779fe0a7368f8ac99428fbca0bfbc100` and bob-plugins at `5ef8cbe4eb29c9a27a72623ec1ca5c7d9f639604`.

The existing machinery is a strong foundation, but it is not a drop-in renderer for source tasks:

| Existing component | Useful foundation | Boundary to preserve |
| --- | --- | --- |
| `src/native/plan_budget/today.rs` and `docs/plan.md` in bob-cli | Canonical membership, resolution, deduplication, shared examples | Today follows open ledger entries, not residence, schedule, or lane. |
| Ledger-tools `060-today.js` | JavaScript ledger parser and canonical task-key helpers | Use this membership parser; avoid a third implementation. |
| `180-plugin-plan-and-ready.js` | `todayCacheKey`, `isTodayTask`, `isTodayCacheReady` | `isTodayTask` alone is only a key lookup. It does not reject completed tasks or a previous-day cache. |
| `290-plugin-today-and-location.js` | Shared Today cache and membership-change notifications | Add marker refresh to this shared lifecycle rather than a new independent scanner. |
| `137-progress-marks.js`, `268-plugin-progress-marks.js`, `269-plugin-progress-marks-reading.js` | Inline widgets, one shared glyph, passive behavior, refresh patterns | Progress-link membership differs: it accepts trailing move-only `#`, excludes embeds, and checks `/`. Today excludes that `#` suffix and includes embeds. |
| `139-unblocked-glyph.js`, `271-plugin-unblocked-glyph.js` | Another display-only indicator with Tasks-cache input | Its prerequisite-completed-today model is not the Today model or simply the `[unblocked::]` field. |
| `264-plugin-task-tag-marks.js` and `docs/task-tag-marks.md` | Task-row styling and reversible display conventions | The teal hash means tracked-task identity and explicitly never encodes state. |
| `267-plugin-date-marks-tasks.js` | Narrow deferred rendering of asynchronous Tasks result rows | Its retry and ownership strategy is reusable; its date-text matching does not establish task identity. |

The color vocabulary is already occupied: red means Blocked, yellow In Progress, green Next/freshness, and teal tracked-task identity. Recoloring the checkbox or teal hash would collapse two independent facts into one visual channel. The existing task-tag contract expressly reserves the hash's constant identity meaning.

**The visual decision.** Choose a plain outlined sun with short rays, drawn as SVG and shared through one CSS mask. Use approximately a 16-unit viewBox, a 1.7–1.9-unit rounded stroke, a 0.9–1em glyph, and about 0.25em trailing spacing. These dimensions are starting values for visual acceptance, not measured final geometry. Match the existing mark family's optical weight; avoid a platform emoji whose color, baseline, and shape vary by host.

Use theme-derived neutral ink, with a dedicated override such as `--bob-today-mark-color`. Start from `--text-muted`, then verify contrast against actual backgrounds and task tints. Do not simply lower opacity until the glyph looks subtle. A subtle but legible stroke is preferable to a barely visible symbol. There is no resting background, border, pill, pulse, spin, or entrance animation. The distinctive shape carries the meaning without a new semantic color.

The following is an arrangement sketch, not a screenshot. `☼` stands for the proposed SVG; `⌗` stands for the existing teal hash. The Markdown checkbox symbols stand in for Obsidian's rendered checkboxes.

```text
Area / project note

[*] ☼ ⌗ Send the proposal           ▮▮   + Oct 12
[/]   ⌗ Wait for the review          ▮    + Oct 10
[/] ☼ ⌗ Finish the migration         ▮▮▮  + Oct 15
[ ]   ⌗ Explore the next design      ▮    + Oct 18

Tasks query result, where the task tag may be hidden

[*] ☼ Send the proposal             ▮▮   + Oct 12

Today's ledger, plain Task Links: unchanged

    ◐ Finish the migration   🔓
      Send the proposal
```

The actual layout should not reserve blank sun-width space on every unmarked row. Keep the checkbox column aligned; use the small inline addition only where it carries information. Preserve wrapping, indentation, and the existing tag order. Place it after the checkbox and before task content so scanning does not require reaching a far-right metadata tail. Do not attach it to the checkbox itself or give it the checkbox's hit target. A retained teal hash may reveal raw `#task` while editing; the separate Today sun should remain stable.

| Alternative | Strength | Reason not to make it the default |
| --- | --- | --- |
| Small neutral sun | Compact, day-oriented shape, distinct from current marks | Needs a clear tooltip and initial explanation; a sun can otherwise suggest a theme control. |
| `Today` text | Most immediately understandable | Adds repeated text and width to already dense rows. Good fallback if the glyph is not learned quickly. |
| Calendar with a dot | Clear calendar association | More likely to suggest a scheduled/due date; less distinguishable at very small sizes. |
| Colored dot or left rail | Visually restrained | Weak standalone meaning; rails vary across editor, nested lists, and query results. |
| Recolored checkbox/hash | No extra width | Conflicts with status/identity and loses the independent dimension. |
| Row background | Easy to notice | Competes directly with existing lane and blocked tints. |
| Star, tomato, half-ring, unlock | Familiar existing vocabulary | Each already carries another meaning: highlight, historical work, In Progress, or unblocking. |

For a self-identifying Bob-owned TODAY section, allow the host renderer to suppress repeated suns as a deliberate render option. Do not guess that a third-party query means Today by inspecting its heading or parsing arbitrary query text. In ordinary Tasks queries, consistent marking is safer than clever contextual suppression.

A passive mark can use `role="img"` and `aria-label="On today's plan"`, plus a tooltip reading “On today's plan — linked under an open Pomodoro.” Keep tooltip text free of `::`, following the existing Dataview round-trip precaution. It should add no tab stop and no live-region announcement on each refresh. If navigation is added later, it should become a properly labelled keyboard-operable control, not a hidden click side effect.

Shape must carry meaning independently of color. For a meaningful graphic, target at least 3:1 contrast against its adjacent background, including lane tints. Check the rendered stroke at normal scale rather than assuming a theme variable guarantees adequate legibility. These are grounded accessibility criteria; whether the precise sun is aesthetically successful still needs visual review. [W3C: Use of Color](https://www.w3.org/WAI/WCAG22/Understanding/use-of-color.html), [W3C: Non-text Contrast](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html)

**The semantic contract to implement.** The marker is present exactly when all of the following are established: the row identifies one tracked task, the task is open, the Today snapshot is valid for the current local calendar day and configured daily path, and the snapshot contains that task's canonical `(vault-relative path, block ID)` key.

| Scenario | Marker |
| --- | --- |
| Open task linked by a dedicated direct-child bullet under an open Pomodoro | Yes |
| Same task linked under two open Pomodoros | One mark per rendered task row; removing one link keeps it |
| Last qualifying link removed, struck, or moved into a closed Pomodoro | No, even if the sticky lane remains Next/Pending |
| Only linked under completed or cancelled Pomodoros | No |
| Only linked in prose, a deeper descendant, a code fence, or a move-only `#` line | No |
| Eligible embedded link `![[note#^id]]` under an open Pomodoro | Yes on the target task row |
| Dedicated link under exempt GTD or unnamed open entry | Yes |
| Same-note `[[#^id]]`, alias, or alternate spelling resolving to the same task | Same canonical membership |
| Task is completed/cancelled but the ledger link remains | No |
| Open Blocked task still has a qualifying link before reconcile removes it | Yes while that relation exists; preserve Blocked styling |
| Only scheduled/due today, unblocked today, or prerequisite of a planned task | No inheritance |
| Task physically resides in today's note but has no qualifying link | No |
| Recurrent task spawns a new occurrence | Re-evaluate the new occurrence's actual identity and links; no inheritance |
| Duplicate block ID within a note, unresolved target, or unidentifiable rendered row | No confident mark |

The Blocked row is intentionally included: `docs/plan.md` includes open Blocked tasks in Today, while reconciliation normally consumes their links. A renderer should not silently introduce a different membership rule. Similarly, do not filter membership through freshness, `#hide`, whole-lane budget eligibility, or priority. Those govern other views. A renderer decorates an already visible, identifiable task.

The JavaScript cache is currently a resolved **link-key set**, whereas Rust's `today_tasks` additionally resolves the target to a unique open tracked task. Build a small internal presentation predicate around the existing cache, with explicit identity, open-status, and readiness validation. Keep the established public `isToday` API backward compatible unless its consumers are separately reviewed. No new public API namespace is needed merely to render this feature.

Missing and unavailable must also be distinguished. A confirmed absent daily file or absent Pomodoros section implies no qualifying links. An unreadable file, unresolved initialization, stale date, or unsupported rendered identity is **unknown**, not evidence that the task is unplanned. In that case hide the positive mark, and allow a single status/diagnostic inspection to explain availability. Do not create warning badges or notices on every row. The current `readPlanBlockContent` returns `null` for both absence and read failure, so a richer shared read result is needed if this distinction is exposed to the user.

**Implementation architecture and the difficult surfaces.** Put the feature in **bob-ledger-tools**. It already owns Today, related marks, and their rendering lifecycle. Keep a pure presentation model, a small DOM/widget builder, and host-specific adapters. Follow the committed-fragment build; do not hand-edit generated `main.js`. The implementation would eventually ship through `bob plugins sync`; this research did not deploy anything.

For Live Preview, use a zero-length `Decoration.widget` anchored after the checkbox. Establish the task identity from the editor file path and the actual task line's standalone block ID. Respect syntax/fenced regions and task boundaries. Compute visible decorations from the current document and the shared Today snapshot; do not scan the vault during widget construction. Stable widget equality and explicit refresh effects avoid flicker and unnecessary work on cursor movement. This matches Obsidian's documented decoration mechanism and CodeMirror's widget/viewport model. [Obsidian: Decorations](https://docs.obsidian.md/Plugins/Editor/Decorations), [CodeMirror: Decorations](https://codemirror.net/examples/decoration/)

For Reading view and embeds, resolve the **originating task**, not the containing dashboard or transclusion host. Prefer a reliable rendered block identity, or validated source-section mapping plus metadata. Do not match visible task titles, and do not borrow a nested child's block ID. Existing progress-mark code explicitly warns that full-note Reading views can lack section info, so `ctx.getSectionInfo` cannot be the only strategy. Tasks-rendered tracked rows can use the query adapter described below; native Obsidian task rendering without Tasks needs its own identity acceptance check. If identity cannot be proven, omit the mark and document the unsupported case.

For Tasks query results, I inspected upstream **Tasks 8.4.0**, commit `9173205606e49846f456caf438fdc0e5baded77e`, rather than assuming its DOM semantics:

- `TaskLineRenderer.renderDescription` invokes the Markdown renderer with **`task.path`**. Capture that source path from the post-processing context.
- The renderer places the block link in its own **`.task-block-link`** component. In this version, block-link and description components are always shown by the normal layout options, even if CSS visually hides them.
- Wait until the enclosing `li.plugin-tasks-list-item` has finished rendering, then read its **own** block-ID component and combine it with the captured source path. Existing date-mark scheduling supplies a useful bounded-retry pattern.
- **Never treat `data-line` as the source line.** Tasks writes the task's index in the result list there. Sorting, grouping, and nesting make it unsuitable for source identity.
- Do not use visible backlinks for identity: their text is presentation, and the click handlers close over the Task object rather than supplying a guaranteed source URL.

This gives a concrete adapter to prototype without monkey-patching Tasks. It remains an internal DOM dependency, not a guaranteed public render-hook API. Test the exact installed Tasks version and capability-detect required structure. A Tasks update that removes the identity should leave ordinary task rendering intact. This inspection does not establish the actual installed version in the live vault.

Keep added spans idempotent and listener-free where possible. Remove or update only Bob-owned nodes. Refresh registered rendered containers as well as editor leaves: an editor-only refresh leaves open Reading panes stale. Use scoped lifecycle cleanup and, only if needed, a narrowly scoped observer for asynchronous result containers. Do not observe and rescan the whole document for every mutation. [Obsidian: Manage plugin lifecycle](https://docs.obsidian.md/plugins/guides/lifecycle-management)

**Reliability is part of the feature, not polish.** The current shared Today lifecycle listens to daily-note metadata changes, metadata resolution, relevant vault events, and a minute rollover tick. Extend it deliberately:

1. Refresh marks when membership changes **and** when a represented target's status or identity changes. Completing a task can invalidate the mark while leaving the link-key set unchanged.
2. Update open source buffers from their current text. Prefer the current daily editor buffer when available, then authoritative saved/cache data. A local checkbox change should not retain a stale positive mark until a background hook runs. Do not add a second full task parser to get this effect.
3. Refresh after rename, move, deletion, link rewriting, undo, and redo. Key by path plus block ID; never by title, bare block ID, or list position.
4. Guard asynchronous reads with a generation and requested day/path. A slower old read must not overwrite newer membership or resurrect yesterday's marks.
5. At local midnight invalidate the old snapshot and repaint existing hosts. Use a next-midnight timer plus focus/visibility revalidation, with the existing minute check as a fallback. Sleep, timezone change, and delayed timers should not leave yesterday's plan displayed indefinitely.
6. Coalesce event bursts. Reuse the existing roughly 150ms refresh convention as a starting point. Maintain targeted indexes and inspect only visible source rows/registered rendered rows; do no subprocess or full-vault I/O per task mark.
7. Clear owned decorations on disable/unload and cancel pending work. A session toggle, consistent with existing marks, makes the feature reversible.

The refresh paths are recommendations from source inspection, not claims of reproduced production races. In particular, I did not verify current runtime behavior after sleep or midnight. The asynchronous cache function has no explicit request-generation guard in the inspected method; the new feature should include a test of out-of-order completion before assuming it is safe.

**Verification and acceptance.** I ran the existing focused suites for Today, progress marks, unblocked glyphs, freshness mark surfaces, and Tasks date marks on the unchanged plugin checkout. Result: **89 tests, 85 passed, 4 failed**. All failures were in `test-ledger-tools-unblocked-glyph.cjs`: Live Preview placement, widget mousedown, rebuild triggers, and Reading-view deduplication. The fixture mixes a wall-clock `DAILY` with October 9 dates. This is the already tracked **bob-cli-6v**, independently corroborated here; the causally related active **bob-cli-5w** also received the evidence. These failures do not establish a defect in a new Today marker, which has not been implemented.

The test log is preserved as `file:explicit:0bc928bce76885083a493783`. Reproduction, from bob-plugins:

```sh
node --test \
  scripts/test-ledger-tools-today.cjs \
  scripts/test-ledger-tools-progress-marks.cjs \
  scripts/test-ledger-tools-unblocked-glyph.cjs \
  scripts/test-ledger-tools-freshness-mark-surfaces.cjs \
  scripts/test-ledger-tools-date-marks-tasks.cjs
```

For the proposed implementation, acceptance should concentrate on behavior that can silently lie:

| Area | Essential checks |
| --- | --- |
| Membership | Shared Today examples; two links/one unlink; embeds versus move-only links; done/cancelled targets; no dependency inheritance |
| Identity | Same title on different tasks; same block ID in different files; duplicate block ID within one file; aliases; renamed/moved tasks; nested rows |
| Timing | Late asynchronous read; unsaved daily edits; completion with unchanged ledger; midnight; wake; timezone change; unavailable cache |
| Rendering | Live Preview, full Reading view, block embed, sorted/grouped Tasks query, short mode, hidden tags/backlinks, repeated rerender, multiple open panes |
| Editor safety | Checkbox clicks; cursor placement; selection and copy; undo/redo; Vim motions; source-mode transition; no inserted Markdown or new undo entry |
| Appearance | Light/dark themes; status tints; 100%/200% scale; narrow pane; long wrapped title; dense metadata; screen reader label; no duplicated mark |
| Cleanup/performance | No vault read or subprocess per row; bounded refresh work; no retained detached containers or timers after disable/unload |

Freeze or inject the clock in these tests. The current baseline failures are a practical warning against combining hardcoded fixture dates with `new Date()`.

Do a small rendering prototype before broadening coverage: one source task, one embedded task, and one sorted Tasks result with a duplicate title. Validate identity and interaction first, then finalize the sun's geometry in actual Obsidian screenshots. I have not rendered the proposed design in live Obsidian, measured theme contrast, or benchmarked it. Those are explicit remaining implementation validations, not completed research claims. Do not infer visual quality from passing fake-DOM tests alone.

**Source ledger.** Internal citations below are stable repository/revision identifiers and file paths; external technical references are primary documentation or inspected upstream source.

- bob-cli `9217a475779fe0a7368f8ac99428fbca0bfbc100`: `docs/plan.md` (Today, lines 106–140; progress-mark contract, lines 214 onward; Today conformance examples), `docs/task-tag-marks.md`, `docs/date-marks.md`, `src/native/plan_budget/today.rs` (target validation and deduplication).
- bob-plugins `5ef8cbe4eb29c9a27a72623ec1ca5c7d9f639604`: `plugins/bob-ledger-tools/src/060-today.js`, `137-progress-marks.js`, `139-unblocked-glyph.js`, `170-plugin-lifecycle.js`, `180-plugin-plan-and-ready.js`, `264-plugin-task-tag-marks.js`, `267-plugin-date-marks-tasks.js`, `268-plugin-progress-marks.js`, `269-plugin-progress-marks-reading.js`, `271-plugin-unblocked-glyph.js`, `290-plugin-today-and-location.js`, and `plugins/bob-ledger-tools/styles.css` (progress and unblocked styling around lines 1614–1718).
- Audited SASE memory: `decisions:today-is-read-from-the-ledger`, `decisions:task-lanes-are-sticky`, `glossary:task-link`, `glossary:pomodoro`, plus artifact-publication and vault guidance. No memory was changed.
- [Tasks 8.4.0 TaskLineRenderer](https://github.com/obsidian-tasks-group/obsidian-tasks/blob/9173205606e49846f456caf438fdc0e5baded77e/src/Renderer/TaskLineRenderer.ts): source path passed to description rendering and `data-line` result index. Read through the audited local external checkout.
- [Tasks 8.4.0 TaskFieldRenderer](https://github.com/obsidian-tasks-group/obsidian-tasks/blob/9173205606e49846f456caf438fdc0e5baded77e/src/Renderer/TaskFieldRenderer.ts), [TaskLayoutOptions](https://github.com/obsidian-tasks-group/obsidian-tasks/blob/9173205606e49846f456caf438fdc0e5baded77e/src/Layout/TaskLayoutOptions.ts): block-link component class, absence of a canonical task-key data attribute, and always-shown block-link layout behavior. Read locally.
- [Tasks 8.4.0 HtmlQueryResultsRenderer](https://github.com/obsidian-tasks-group/obsidian-tasks/blob/9173205606e49846f456caf438fdc0e5baded77e/src/Renderer/HtmlQueryResultsRenderer.ts), [TasksApiV1](https://github.com/obsidian-tasks-group/obsidian-tasks/blob/9173205606e49846f456caf438fdc0e5baded77e/src/Api/TasksApiV1.ts): backlink event behavior and limited public API. Read locally.

**Recommended solution.** Implement a **display-only, passive sun mark meaning “On today's plan” in bob-ledger-tools**, placed just after the checkbox on identifiable open task rows. Derive it from the existing Today ledger cache with explicit current-day readiness, canonical identity, and open-task checks. Support Live Preview, Reading/embedded task rows, and a version-checked Tasks result adapter; leave raw Source mode and ordinary daily Task Links unchanged. Preserve all existing checkbox, lane, identity, freshness, and unblocked meanings. Ship only after duplicate-identity, asynchronous-refresh, rollover, and real Obsidian visual checks pass. This gives Bryan the useful context at the task's source without creating another task state to maintain.
