# Bank badge: directional color and trustworthy period summaries

Independent research by **cdx**, 2026-11-14.

**Recommendation:** keep the bank badge as a small, read-only cash-flow summary. Show each positive direction independently, use teal for incoming and warm copper for outgoing, and render the same component below every supported stats strip. Calculate period totals in bob-cli using the existing bank accounting rules and the period calendar. Give the badge a compact summary data contract rather than making the plugin assemble transactions.

This is a good improvement: it removes visual noise, gives weekly and longer reviews a useful financial dimension, and makes one familiar element work consistently across notes. The substantial work is ensuring that the numbers and date ranges mean the same thing everywhere. A CSS-only implementation would miss those requirements.

This report is a proposal, not an implementation or an accepted decision. It includes proposed glossary wording; it does not prematurely add future behavior to canonical memory. I independently inspected bob-cli and bob-plugins and did not consult any other swarm researcher's report or findings.

## 1. What exists today

Source references below identify the inspected repository revisions, not moving workspace paths:

- **bob-cli:** `5b1b6d596338b2358f528759d67d36a71ee303a4`.
- **bob-plugins:** `415a33d7c43cc7e732b430dd3b9a5e294eac7ffe`.

| Finding | Evidence |
| --- | --- |
| The current chip lives in canonical daily-note `bob-plan` hosts, immediately after the day-strip host. It is not a general stats-strip component. | bob-plugins, `plugins/bob-ledger-tools/src/241n-plugin-bank-daily-chip.js:107` |
| It always prints both `out $…` and `in +$…` for a valid day model. Today also gets the waiting count across all months, even when that count is zero. | Same file, `bankDailyChipPaint`, line 187; `241l-plugin-bank-cards-model.js:275` |
| It hides on future daily notes, when `bank.md` is missing, or when `stats.bank_chip` is false. Bank visibility is independent of whether the day stats are enabled. | `241n-plugin-bank-daily-chip.js`; `scripts/test-ledger-tools-bank-cards.cjs:384` |
| Its color currently follows the bank root's area hue, with a magenta fallback; the amount does not determine color. | `plugins/bob-ledger-tools/styles.css`, `.bob-bank-daily-chip` and adjacent root-hue selectors |
| Values come from `bob bank report -D DAY -f json`. The existing bank service has bounded caching, subscriptions, invalidation, last-good values, and generation handling. | `241n-plugin-bank-daily-chip.js:174`; `241j-plugin-bank-data.js` |
| Day fences and period fences have separate mount/lifecycle paths. Period strips use `bob periods show`. | `239-plugin-day-strip-fence.js`; `239-plugin-period-strip-fence.js` |
| Bank reports support day, ISO week, calendar month, and **calendar year**, but not Bob quarters or all time. | bob-cli, `src/native/bank/report.rs:20`, `resolve_period`; `src/native/bank/dates.rs:92` |
| Period notes use ISO weeks, quarters composed of whole ISO weeks, ISO week-years, and all time. Existing Stats all-time starts at the week of the earliest canonical daily note. | `src/native/periods/calendar.rs`; `src/native/periods/report.rs:434`; audited glossary reads |

I ran the existing `node --test scripts/test-ledger-tools-bank-cards.cjs`: **13 tests passed**. This establishes the current behavior and useful test scaffolding; it does not validate the proposed feature.

## 2. Preserve the accounting meaning

“Incoming/outgoing transactions made that day” needs a more precise definition. These are amounts from recorded bank rows assigned to that day, using posted dates for imported rows. They are not necessarily purchase-time transactions, complete bank coverage, account balances, or changes in net worth.

The existing contract is appropriate and should remain the source of truth:

| Direction | Included | Excluded |
| --- | --- | --- |
| Out | Non-cash-account outflows, including uncategorized spending and ATM cash withdrawals | Explicit transfers and cash-account rows |
| In | Non-cash-account inflows explicitly categorized as income or refund | Explicit transfers, cash-account rows, and unclassified inflows |
| Net, if shown in details | In minus Out | It is not a balance or profit measure |

Acknowledged and waiting rows both count. Acknowledgment is a review state, not a financial inclusion filter. A positive uncategorized credit is not silently promoted to income. A correctly categorized card payment remains a transfer, avoiding counting both purchase and payment as spending. These are existing Bob rules, not new financial advice. Sources: bob-cli `docs/bank.md`, “Totals,” and `src/native/bank/model.rs:129`.

**Consequence:** no badge means “no included In or Out amount,” not “no transactions.” A transfer-only day, a cash-account-only day, or an unclassified-credit-only day can legitimately have no money badge. Explain this in the documentation and drill-down; do not change the accounting to make the badge appear.

Use integer cents throughout. A value of 1 means $0.01 and must appear. Never decide visibility by a formatted dollar string or a rounded compact amount. Reject malformed, fractional, negative-direction totals, unsafe JavaScript integers, and overflow as invalid data; do not repair them with `Math.abs` or convert them to zero.

## 3. Visual design: a quiet badge with two clear directions

Keep one recognizable BANK group with independently colored directional spans:

```text
Neither:      [nothing]

Outgoing:     BANK   OUT $48.70
Incoming:     BANK   IN +$2,150.00
Both:         BANK   OUT $48.70  ·  IN +$2,150.00
Equal totals: BANK   OUT $50.00  ·  IN +$50.00
```

This is a layout sketch, not a screenshot. Preserve today's Out-then-In order to minimize relearning and match the bank report's ordering. Render separators only between present spans. Keep BANK and separators neutral, and tint each direction's label and amount together. Use tabular numerals, normal interface type, modest semibold amounts, and the existing strip's compact spacing.

### Why these colors

| Approach | Benefit | Cost | Verdict |
| --- | --- | --- | --- |
| Entire badge green when In exceeds Out, red when Out exceeds In | Fast net direction | Ordinary rent and grocery days look like failure; payday timing dominates; hides the fact that both flows occurred | Reject |
| Green In, red Out | Familiar signed-money convention | Treats normal spending like an error and competes with actual error indicators | Acceptable convention, weaker fit here |
| **Teal In, warm copper Out; neutral shell** | Stable direction mapping, restrained visual contrast, both flows remain legible | The mapping is learned; requires explicit labels | **Recommend** |
| Existing area hue everywhere | Matches bank ownership | Adds no directional information | Keep area identity in the larger bank cards |
| Saturation or width proportional to amount | Suggests magnitude | No common scale across day, week, and all time; adds unsupported “good/bad” intensity | Reject for this badge |

The choice of teal/copper is a design judgment, not a universal financial standard. Copper must be a dedicated money-direction token, not an alias for the application's warning token. Reserve warnings and errors for actual data or command problems.

W3C advises conveying meaning with text or another cue in addition to color; the visible IN and OUT labels provide that redundancy. [W3C: Use of Color](https://www.w3.org/WAI/WCAG22/Understanding/use-of-color.html). Carbon distinguishes categorical color use from alert palettes; treating direction as a stable category is consistent with that distinction, although Carbon does not prescribe this exact pair. [Carbon: Color palettes](https://www.carbondesignsystem.com/building-blocks/data-visualization/color-palettes).

Suggested reference tokens:

| Token | Light reference | Dark reference | Contrast against reference badge surface |
| --- | --- | --- | --- |
| Badge surface | `#F6F5F3` | `#232323` | — |
| Incoming text | `#0F766E` | `#5EEAD4` | 5.02:1 / 10.62:1 |
| Outgoing text | `#9A4B16` | `#FDBA74` | 5.68:1 / 9.32:1 |
| Neutral label | `#57534E` | `#D6D3D1` | 7.00:1 / 10.55:1 |

I calculated these ratios using sRGB relative luminance. They are verified reference pairs, not proof of contrast in an arbitrary Obsidian theme. Use local semantic CSS tokens, test the actual composited background in light/dark themes, and fall back to readable neutral text if theme adaptation compromises contrast. Small badge text should meet at least 4.5:1. [W3C: Contrast Minimum](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html).

Avoid a red/green full-badge background, gradient, rainbow border, money emoji, net arrow, or tiny bar chart. The neighboring stats already carry charts and color. One soft neutral container with two crisp amounts is enough.

### Layout and interaction

- Place the badge below the strip's final chart/bar tier, above the daily plan badges or the period parts table. Preserve a consistent position across strip kinds.
- Remove the empty host's spacing when both directions are zero. Do not leave a decorative line or an empty chip.
- Use one focusable control for the entire money badge, with real button behavior, visible focus, Enter/Space activation, and a full accessible name containing period, directions, and exact amounts. The spans inside it are not separate tiny targets.
- Make the target at least 24 CSS pixels high and wide; a compact 28-pixel control is a reasonable starting point. W3C also permits spacing exceptions, but there is little reason to depend on them here. [W3C: Target Size Minimum](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html).
- Keep each label/amount pair intact. At narrow widths, wrap between directions rather than clipping digits, dropping cents, shrinking the font, or ellipsizing money. For an exceptionally long amount, allow horizontal overflow within the control rather than silently changing its value.
- Keep exact dollars and cents in the first version, including annual and all-time totals. If compact notation later becomes necessary, make that a deliberate responsive design decision with exact values available without hover.
- Retain natural $0.00 formatting in details, but never render a zero directional segment in the badge.

The preview harness already models Obsidian's global fixed-height button styling because it previously clipped strip content. Explicitly reset inherited button height, wrapping, alignment, padding, and shadow for this component. Source: bob-plugins `scripts/preview-day-strip.cjs`.

## 4. Visibility, review work, and data quality are separate concerns

The normal money badge obeys a simple truth table:

| Data condition | Money badge |
| --- | --- |
| Valid In = 0, Out = 0 | Absent |
| Valid In > 0, Out = 0 | In only, teal |
| Valid In = 0, Out > 0 | Out only, copper |
| Both > 0 | Both, each its own color |
| Equal nonzero totals | Both; zero net does not hide activity |
| Bank disabled or not configured | Absent |
| Future period | Absent |
| Request failed, no usable data | No invented amounts; a separate quiet “Bank unavailable · Retry” status |
| Refresh failed with last-good data | Retain prior badge and visibly mark values as stale |
| Last-good data was zero and refresh fails | Badge remains absent; status still explains the failure |

Loading, unavailable, and stale states must not be treated as zero. On the initial fetch, use a quiet loading state only while needed; do not flash both zero amounts. On routine background refresh, keep the last-good layout. A small “stale” text marker is preferable to color-only dimming or a tooltip-only warning.

Import staleness and UI cache staleness are different. A freshly calculated summary may describe incompletely imported bank history. Retain existing account-status evidence in details, and say “recorded bank rows”; do not label a successful query “complete” or “balanced” unless the underlying evidence supports that claim. Current collection skips unparsed rows, and existing bank checks diagnose malformed data. The new summary should expose scoped omitted-row/diagnostic evidence where available, or show an incomplete-data notice, rather than implying that parse success proves complete coverage. Reuse existing diagnostics; do not invent a second reconciliation engine for this feature.

**Explicit requirement adjustment:** remove the global waiting count from the money badge. It currently describes all months, not the displayed period. Repeating it on historical and period strips would be misleading. Preserve the workflow through the bank queue and, on today's plan, a separate plain “N bank rows waiting” action when N > 0. That action opens the queue; it is not a zero-dollar bank badge. Do not append “0 waiting.”

This keeps the user's zero rule intact while retaining a way to notice transfer-only or unclassified incoming rows that still need acknowledgment. A period detail panel can show its own scoped waiting and flagged counts; it should not inherit today's global count.

## 5. Every stats strip must mean the same period

Include all supported strip hosts:

1. The canonical daily `bob-plan` mount.
2. An explicit `bob-day-stats` fence.
3. A `bob-stats-strip` fence selecting a day.
4. Week, quarter, year, and all-time `bob-stats-strip` fences, both in canonical period notes and with explicit period selectors.

Honor each host's existing desktop/spawn and embed eligibility rules. “Every stats strip” means every strip the application actually renders; it does not require a new mobile execution path or enabling currently suppressed hover previews. Do not add a second bank badge to `bob-period-parts`, which is a separate table surface. Multiple deliberate strip instances may each show their own badge, but each instance mounts exactly once.

Keep `stats.bank_chip: false` as the existing master opt-out and apply it to the new hosts. A new visual name does not justify breaking the configuration key. Preserve today's behavior that disabling daily stats does not itself disable the bank badge. The Worked/Off-clock/Total selector and Roots/Types switch must not affect bank totals or their cache identity.

### Date boundaries are a correctness requirement

Reuse `PeriodId` for fixed periods; do not reconstruct quarters with month arithmetic in JavaScript.

| Period | Required span |
| --- | --- |
| Day | The selected bank-row date |
| ISO week | Monday through Sunday |
| Bob quarter | W01–13, W14–26, W27–39, or W40–52/53 |
| ISO year | All days belonging to that ISO week-year |
| Current fixed period | Its start through Bob's local today; show “so far” in the scoped explanation |
| All time | All recorded eligible bank rows through Bob's local today |

For example, **2026's ISO year is 2025-12-29 through 2027-01-03**, and its Q4 begins **2026-09-28**. A calendar `-y 2026` bank report covers 2026-01-01 through 2026-12-31 instead. These spans were independently checked using Python's `date.fromisocalendar` in addition to reading the period implementation. Using the existing `-y` selector for a year note would silently give the wrong answer.

**Explicit requirement clarification:** all-time bank history must not be truncated at the first Pomodoro/daily note. Existing Stats all-time derives its lower bound from daily notes. For bank summaries, all time is conceptually unbounded; its available history may begin earlier. Show “Recorded bank history since DATE” in details so the coverage difference is visible, without changing unrelated Stats metrics. Fixed periods still use exactly the same nominal interval as their strip.

Include valid bank rows even when no corresponding daily note or generated period note exists. The bank source is authoritative for money. Use Bob's date/time context, including `BOB_NOW` in tests, for current/future cutoffs. Do not let browser UTC conversions move a transaction between days.

## 6. Recommended implementation boundary

This is a moderate cross-repository feature, not a small styling patch. There are three credible ways to supply period totals:

| Option | Assessment |
| --- | --- |
| Fetch day/month reports and add them in the plugin | Reject: repeated processes and larger payloads, duplicated date logic, easy partial-month and stale-response mistakes |
| Add a bank object to `bob periods show` and a parallel daily Stats response | Viable, but couples work-stat availability and bank configuration, duplicates entry points, and still needs independent bank invalidation |
| **A compact bank summary command consumed by one bank service** | **Recommend:** bank owns accounting, period calendar owns intervals, plugin owns presentation |

Proposed public interface, subject to the repository's normal CLI review:

```sh
bob bank summary -D 2026-11-14 -f json
bob bank summary -p 2026-W46 -f json
bob bank summary -p 2026-Q4 -f json
bob bank summary -p 2026 -f json
bob bank summary -p all -f json
```

Use `-D/--day` and `-p/--period` as mutually exclusive explicit selectors; reuse standard vault and output options. These are **proposed commands**, not commands available today. Keep existing `bob bank report -y` calendar-year semantics unchanged. Help should explain ISO periods and the contrast with report's calendar year. Every public long flag needs a short alias under the project's CLI rules.

The new command should call a shared Rust bank summary function that scans bank inputs, selects rows, and delegates to `compute_totals`. Reuse the exact accounting helper used by existing reports. Do not route the badge through Stats metric formulas, acknowledgment-only lists, or JavaScript parsing of bank Markdown.

Its versioned response needs, at minimum:

- Resolved period identity, kind, start/end, effective observed-through date, and current/future state.
- Exact nonnegative `in_cents` and `out_cents`, plus other existing totals needed to explain exclusions in details.
- Availability/diagnostic information that distinguishes no bank setup, a valid zero result, partial or unavailable data, and unsupported protocol.
- Period-scoped waiting/flagged counts and existing account/import evidence for detail presentation.

Keep the automatic badge response compact: **no transaction rows and no dense day array**. The current report builder walks every calendar day and embeds rows. Extending that report shape blindly to decades of all-time history increases process output and decode work for two numbers. Initially one scan over the bank files is adequate; measure before adding persistent indexes. Fetch detail lists lazily and page or bound them. Do not fan out one subprocess per month or day.

In bob-plugins, extend the bank service's command dispatch, argument builder, decoder, and subscription specification explicitly for summary reads. The current service distinguishes list/report in several locations, so changing the renderer alone will not be enough. A pure shared presentation model should decide the two visible spans and their labels; one painter should render all day/period instances.

Use narrow host adapters for the daily plan, day fence, and period fence. Retain the existing day-only API as a compatibility adapter if another plugin consumes it. Update committed source fragments and regenerate `main.js`; never hand-edit the generated bundle.

### Refresh behavior worth preserving

- Coalesce identical requests across windows and embedded strips.
- Key by canonical scope and relevant input generation; clock view is not part of the bank scope.
- Invalidate on bank hub and month-file edits, creation, deletion, renames, and category changes.
- Account/import-health metadata also depends on the per-host bank journal; handle journal-only changes or revalidate that evidence on the existing focus path. The present `bankRelevantPath` recognizes hub/month notes, not journal files.
- Refresh current/all-time scopes on local midnight and resolve explicit historical scopes correctly.
- Keep generation checks so late replies cannot replace fresher values.
- Stop subscriptions on unload; hidden panes should not create unbounded repeated reads.
- A bank failure must not erase or prevent the work stats from rendering.

## 7. Drill-down should preserve scope

A value is more trustworthy when its source is one action away.

For a day, preserve the existing exact-day bank-note navigation and keyboard semantics. Rendering remains read-only; do not ensure or create bank notes during mounting. The current click path explicitly calls `ensureOpenDay`; keep that gesture's existing behavior unless deliberately changing navigation as a separate decision.

A multi-month period has no single bank heading to open. Do not jump to the first day or an unrelated current month. Open a small read-only period detail panel showing:

- The explicit period label and date range, with “so far” when appropriate.
- In, Out, and optional Net, explaining that Net is a flow difference.
- The inclusion/exclusion rules and available import/coverage caveats.
- Month navigation scoped to the selected interval, loaded on demand; month summaries must use only the overlapping part of the period.
- Links to relevant existing bank headings and the bank queue.

Keep initial detail presentation bounded, with further months/rows loaded as requested. The goal is explanation and navigation, not a new budgeting dashboard. Period details are a justified addition to the requested rendering work because the daily badge's existing destination cannot simply generalize to quarters or all time.

## 8. Proposed glossary entry and documentation

Add a new `glossary:bank-badge` strand when implementing the accepted design. Suggested definition:

> **Bank Badge** (bank badge; bank chip): The compact, read-only bank-flow summary associated with a [[stats-strip]], including the [[day-strip]]. Bob computes its totals from [[bank-row]]s for the selected day or period. It shows Out and In independently only when their totals exceed zero cents, and is absent when both are zero. Out follows Bob's non-transfer, non-cash-account outflow rule; In includes income and refunds. Incoming is teal and outgoing is copper, with explicit text labels. Activating it opens the day's [[bank-month-note]] location or scoped period details. It shows recorded flows, not an account balance, a budget judgment, or bank-data completeness.

Keep this a proposed definition until the feature ships. The user's explicit request covers adding the term. Use the memory-write workflow and regenerate the glossary roster/instructions rather than editing generated `AGENTS.md`. If the eventual accepted palette differs, update the proposed wording before publishing it.

Document observable behavior in `docs/bank.md`, the stats/period contracts where appropriate, the JSON contract reference, and bob-plugins' owned documentation. Generate CLI references for the new command, and document that `stats.bank_chip` now covers all strip hosts. Keep detailed threshold/state tables in docs rather than loading them into core memory.

## 9. Acceptance criteria and risks

The following checks matter more than a large collection of superficial renderer snapshots:

| Area | Essential cases |
| --- | --- |
| Visibility | 0/0; one-cent In; one-cent Out; both; equal nonzero flows; no orphan separator or empty spacing |
| Accounting | Waiting and acknowledged rows; refunds; transfer pairs; cash accounts; ATM withdrawals; unclassified inflows; recategorization changing In |
| Invalid input | Missing fields, unsafe/fractional/negative cents, unsupported schema, subprocess failure, malformed bank rows; none become zero-dollar success |
| Periods | Cross-month week, ISO year boundary, W53/Q4, leap day, current-period cutoff, future period, all-time bank rows predating daily notes |
| Source independence | Bank rows count without daily notes; bank data ignores Worked/Off-clock/Total and chart switches |
| Lifecycle | Duplicate mounts/windows, late replies, rename/delete, category edits, journal evidence refresh, local midnight, config opt-out, unload |
| Navigation | Exact day preserved; multi-month detail keeps its scope; no note writes during paint; keyboard and focus behavior |
| Visual | Light/dark, common theme overrides, grayscale, 320-pixel pane, large amounts, 200% zoom, Reading/Live Preview, Obsidian button CSS |

For fixed periods on the same input snapshot, sum the child-period totals and assert equality with the parent; zeros omitted from presentation must not affect arithmetic. For all time, test the union of bank history rather than the set of existing period-note files. Use synthetic fixtures, not personal transaction data.

Add focused Rust tests near bank totals and period resolution; extend the existing bank decoder/data/card tests and strip-host tests in bob-plugins. Add a small browser visual fixture matrix using the repository's existing preview/e2e infrastructure. Then run required repository checks and deploy plugin changes through `bob plugins sync` under its existing deployment rules. No tests or deployment of the proposed feature were performed in this research turn.

The principal risks are misleading zeros from missing data, wrong ISO boundaries, accidentally hiding review work, uncontrolled all-time payloads, and theme contrast drift. Each has a specific mitigation above. Defer budgets, spending targets, forecasts, trend colors, and currency expansion; none is needed to satisfy this request.

## 10. Sources and limits of the research

Local evidence was gathered directly from the revisions in section 1, plus audited memory reads of Day Strip, Stats Strip, Period Note, Bank Row, Bank Month Note, CLI rules, documentation rules, and artifact rules. Other especially relevant code locations:

- bob-cli: `src/native/bank/model.rs`, `report.rs`, `dates.rs`, `cli.rs`; `src/native/periods/calendar.rs`, `report.rs`; `docs/bank.md`.
- bob-plugins: `241n-plugin-bank-daily-chip.js`, `241l-plugin-bank-cards-model.js`, `241h-plugin-bank-decode.js`, `241j-plugin-bank-data.js`, `241i-plugin-bank-source.js`; the day/period strip host and fence fragments; `styles.css`; `scripts/test-ledger-tools-bank-cards.cjs`; `scripts/preview-day-strip.cjs`.

External primary sources are linked beside the claims they support. They establish accessibility constraints and design distinctions; they do not establish that users prefer this exact palette. No live-vault financial data was read, and no actual Obsidian screenshot/user study or latency benchmark was conducted. The palette calculations and 13 passing baseline tests are the empirical checks performed here.

## Recommended solution

Proceed with the feature, with five explicit refinements: preserve Bob's existing In/Out accounting rather than counting every credit; color each direction teal/copper rather than grading the whole badge by net; move today's global waiting count into a separate queue action; use Bob's ISO boundaries and all recorded bank history for all time; and distinguish failed or incomplete data from a valid zero result.

Implement one compact Rust bank-summary contract, one shared badge model/painter, and adapters for every supported stats-strip host. Keep exact cents, show only positive directional totals, hide the money badge at zero/zero, provide a scoped drill-down, and publish the Bank Badge glossary entry with the accepted behavior. This gives the user a calmer and more useful financial glance while keeping the numbers explainable and the implementation maintainable.
