# Gated walker footers: hide the review footer unless `s` is active, add `w` / `n` footers

> Researcher: **mus** (independent swarm report, `__mus` suffix).
> Date: 2026-11-12. Question: should the GTD review footer show only when the
> `s` walk is active, with new `w` and `n` footers for the other walks, and what
> should those footers contain? Goal: intuitive, reliable, beautiful.

## Bottom line

- **Yes, gate — but gate one shared walker-footer slot, not three independent
  footers.** The request as written ("only show the review footer when `s` is
  active, plus two new footers for `w`/`n`") is directionally right: today the
  status bar always shows `⟳ Review …` whenever anything is due, plus a separate
  always-on `[[ s w n ]]` bracket-mode indicator, so the bar carries two walk
  widgets that do not agree about which walk `[[` / `]]` will repeat. Gating the
  footer on the active bracket family makes the footer a *preview of what `[[`
  / `]]` will do*, which is the correct mental model and the beautiful outcome.
- **Do not ship three separate status-bar items.** Three items plus the existing
  `[[ s w n ]]` indicator is four walk widgets competing for ~300–600 px. The
  reliable and beautiful shape is **one `walker footer` status-bar item with
  three views (`s` / `w` / `n`) plus an integrated mode switch**, replacing both
  current items. Concretely: keep the existing `[[ s w n ]]` segmented control
  *inside* the walker footer (left edge) instead of as a second status-bar item,
  and swap the right-hand content by mode. This saves a slot, keeps the
  `click a letter to switch` affordance, and makes "which walk is active" and
  "what does this walk contain" one glance instead of two.
- **Scope adjustment I recommend:** keep a *quiet exception* for the morning
  due signal. Hiding `Review N due` entirely because the user last pressed `]w`
  risks missing NEW/ROTTEN on review mornings. The walker footer should still
  reserve a compact badged dot or a one-group overflow (e.g. `⟳ 3 due` in the
  `w`/`n` view's tooltip, or a dot on the `s` segment) when the `s` queue is
  nonempty but inactive. Full `s` content stays gated; the *existence* of due
  review work stays ambient. Call this out explicitly in the glossary and in
  the `none` (no mode yet) behavior: `none` should show the `s` view, not
  nothing, until the user picks a family.
- **`w` footer content:** mirror the `s` footer grammar, not new grammar:
  `⫽ Lanes r/N · PENDING i/A · NEXT j/B · READY k/C` (short labels `PEND/NEXT/READY`,
  counts from the existing `laneWalk` queue), current-lane context in that
  lane's hue, lane-colored groups, `]w next` hint, click = `]w`. Do **not**
  invent upkeep/budget meters or Alt+P chips for `w` — the lane walk has no
  quick-roll contract and no upkeep budget.
- **`n` footer content:** there is no `n` queue, so do not fake counts. Show the
  current note's first rendered `prev` / `next` targets:
  `‹ PrevLabel · NextLabel ›` truncated to fit, hint `]n / [n`, click = next
  link. When the note has neither, show `No prev/next links` and hide on
  narrow bars before the `s`/`w` content ever hides (it is the lowest-value
  view). This makes `n` useful (period-note and daily-note navigation) without
  pretending it has a walk queue.
- **Ownership:** keep all three views in `bob-ledger-tools` (it already owns
  both queues: `freshness` + `laneWalk`), and have it subscribe to a tiny new
  nav API `api.bracketRepeat v1` (`current()`, `onChange()`) instead of reading
  nav's `localStorage` key directly. Nav keeps owning `s`/`w`/`n` navigation,
  the `[[`/`]]` repeat plans, and the mode persistence. One painter, one
  `Fit` routine, one paint-key cache. This is the smallest reliable contract.

If the team wants the literal request (three separate items, review footer
strictly hidden when `s` is inactive, no ambient due signal), it can be built —
§5 lists exactly what changes — but I recommend the single-slot variant above
as the default because it is quieter, cheaper to test, and harder to miss a
morning review with.

## What I read (evidence, not assumption)

All paths below are in the linked `bob-plugins` checkout unless marked
`bob-cli`:

- Review footer model: `plugins/bob-ledger-tools/src/120-freshness-footer.js`
  (`freshnessFooterView`, `freshnessReviewEntryView`,
  `FRESHNESS_FOOTER_TIERS`, `freshnessFooterFit` shedding order,
  `freshnessFooterAnswerChip`).
- Review footer paint: `plugins/bob-ledger-tools/src/121-freshness-footer-paint.js`
  (`freshnessFooterPaint`, `freshnessFooterPaintGroups`,
  `freshnessFooterPaintHint`, `freshnessFooterFit`).
- Review footer wiring: `plugins/bob-ledger-tools/src/240-plugin-freshness-status.js`
  (`setupFreshnessStatusBar`, `updateFreshnessStatusBar`,
  `freshnessStatusClicked`, `freshnessNavigationAvailable`,
  `freshnessFooterCursor`, 150 ms debounce + 50 ms context-only path,
  `ResizeObserver` refit).
- Review footer styles: `plugins/bob-ledger-tools/styles.css` (~lines 319–560:
  `.bob-freshness`, per-tier `--bob-review-hue`, `color-mix` + `oklch` ink,
  answer-chip pill, `…` overflow marker).
- Lane queue (ledger side): `plugins/bob-ledger-tools/src/071-lane-walk-model.js`
  (`laneWalkQueueFromTasks`, lane-first order PENDING → NEXT → READY, then path,
  then line; `counts { pending, next, ready, total, todayPending, todayNext,
  todayReady, reviewReady }`; Today tasks counted then dropped).
- Lane model + notice (nav side): `plugins/bob-navigation-hotkeys/src/542-lane-walk-model.js`
  (`LANE_WALK_LANES`, `planLaneWalkJump`, `planLaneWalkLaneJump`,
  `buildLaneWalkNoticeModel`), `543-lane-walk-notice.js` (lane-colored toast,
  `P/N/R` rail dots + bar, `Ctrl+Shift+Enter today · Alt+N …` hint),
  `544-plugin-lane-walk.js` (`jumpToLaneTask`, `laneJump`, stale-queue retry).
- Bracket repeat + mode: `plugins/bob-navigation-hotkeys/src/546-plugin-bracket-repeat.js`
  (`BRACKET_REPEAT_PLANS` s/w/n, uppercase only s/w, `rememberBracketRepeatType`
  persisted via `app.saveLocalStorage(BRACKET_REPEAT_STORAGE_KEY)`),
  `547-bracket-mode-indicator.js` (always-visible `[[ s w n ]]` indicator,
  `buildBracketModeView`, `paintBracketModeIndicator`, click-to-switch,
  flash on repeat), `490-plugin-lifecycle.js` (key bindings: `]s/[s` review,
  `]S/[S` review-group jump, `]w/[w` lanes, `]W/[W` lane jump, `]n/[n` labeled
  links, `]]/[[` repeat, `]}/{[` uppercase repeat; every walk command calls
  `rememberBracketRepeatType`).
- Link walk: `plugins/bob-navigation-hotkeys/src/670-plugin-project-files.js`
  (`openLabeledBodyLink`, `findFirstRenderedLink` skipping frontmatter/fences),
  `680-plugin-link-parse.js` (`renderedLinkMatchesNavLabel`: exact `prev`/`next`
  or `‹…` / `…›` arrow labels; wikilink + Markdown links; first match in
  line order wins).
- Docs: `docs/bob-ledger-tools.md` (footer section ~lines 190–199: nonempty
  groups, `…` cut, TICKLER chip outlasts meter, click = next due task),
  `docs/bob-navigation-hotkeys.md` (keymap table `s → ]s/[s …`, `w`, `n`;
  `]}`/`[{` paragraph; `[[ s w n ]]` indicator paragraph).
- Memory: `sase/memory/glossary/morning-gtd-review-footer.md` via
  `sase memory read glossary:morning-gtd-review-footer` (status-bar item,
  `⟳ Review N due · K commitments`, `]s next` hint, Alt+P preview, short labels
  `WIP`/`RECUR`/`TICKS`, tier colors, hairline divider, hide-when-unavailable
  rules); `decisions:review-walk-is-tiered` + `glossary:task-freshness`
  (tier order PRE → NEW → PROJECTS → PENDING → NEXT → RECURRING → TICKLER →
  ROTTEN → POST; `s` = freshness queue; `w` = PENDING/NEXT/READY-off-Today;
  `n` = rendered-label links, no queue).
- `bob-cli` side: `docs/freshness.md` §§4/6 (shared tier order, lane intervals);
  no footer lives in `bob-cli` — all three footers are Obsidian-plugin work.
  No `walker footer` string exists yet in either repo (grep for
  `walker|Walker` hits only DOM `TreeWalker`).

## 1. Current state in one paragraph each

**Review (`s`) footer.** A read-only projection of the freshness queue. Off-row:
`⟳ Review N due · K commitments|Commitments done|Upkeep budget met · <groups> ·
✓ upkeep/budget · hint`. On-row: `⟳ Review r/N · TIER i/M · detail · hint`.
Hint is `]s next` except when nav `api.quickRoll v1` supplies an Alt+P preview
(on prioritized rows, and off-walk on prioritized tasks as a hint-only
`⟳ Nothing due · <preview>` footer). Groups list every nonempty tier in walk
order with short labels, current tier omitted from the summary and shown as the
colored context instead; hairline divider before ROTTEN/POST; `…` marks a
from-the-end cut, then detail → hint → meter shed (chip outlasts meter on TICK).
Click = `jump-to-next-due-task`, fallback open `rotten`. Hides when Tasks is
unavailable or nothing is due (except the hint-only case). Desktop-only.

**Bracket-mode indicator.** A second, always-visible status-bar item
`[[ s w n ]]` owned by nav. Shows which family `]]`/`[[` will repeat
(`s` = review, `w` = lane walk, `n` = links), persisted per device in
`localStorage`, click a letter to switch, flashes on repeat. Uppercase repeat
(`]}`/`[{`) exists only for `s`/`w` (group/lane jumps); `n` has no uppercase
walk. This is the "which walk is active" widget the proposal refers to.

**`w` walk.** `]w`/`[w` step through Pending/Next/Ready tasks off today's plan
(dash PENDING/NEXT/READY sections; READY = gated READY chip; Today-linked
dropped); `]W`/`[W` jump across lanes. Rich toast already exists (lane label,
`laneRank/laneTotal`, `rank/total`, dot/bar rail, work-log chip, `wrapped`
chip). No footer exists. Queue + counts already served by ledger
`api.laneWalk v2 …queue()` and mirrored by nav's planner — the data for a
footer is already computed.

**`n` walk.** Not a queue walk at all: `]n`/`[n` open the first rendered
`prev`/`next` link in the *current note* (exact label or `‹`/`›` arrows;
daily notes use `[[…|prev]] · [[…|next]]`, period notes use `‹ W44` /
`W46 ›`). Stateless, per-note, no counts, no "due", no uppercase jump. Any `n`
footer must reflect *this note's* links, not a vault-wide queue — that single
fact rules out mirroring the `s`/`w` count grammar for `n`.

## 2. Critique: is gating a good idea?

**Why it is a good idea (agree with the direction).**

1. *One active walk, one footer.* Today `[[` repeats the last-used family but
   the review footer always talks about `s`. After a `]w` session the bar says
   `Review 12 due` while `[[` walks lanes — the two widgets disagree. Gating
   restores the invariant "footer = what `[[` will do".
2. *Status-bar economy.* Two persistent walk widgets shrink the file-path /
   sync area on narrow windows. One walker slot with an integrated `s w n`
   switch is strictly narrower than footer + separate indicator.
3. *Teaches the bracket model.* Users learn `s` vs `w` vs `n` faster when the
   bar's content changes with the mode than when only a three-letter pill
   lights up.
4. *`w` counts are genuinely useful.* "How many Pending/Next/Ready are off
   Today" is the lane-triage question; the toast answers it per landing but
   there is no ambient view. A `w` footer fills a real gap.
5. *The data is already there.* `w` needs no new evaluator: `api.laneWalk v2`
   already returns entries + counts; `n` needs only the existing
   `findFirstRenderedLink(content, label)` scan on the active note.

**Risks and objections (why the literal proposal needs softening).**

1. *Hiding `s` hides the morning obligation.* The review queue is the only one
   with a daily-due obligation (NEW + ROTTEN + lanes). If the user ends Tuesday
   on `w`, Wednesday morning shows lanes while 15 NEW rot unseen. The current
   always-on footer is an ambient reminder; strict gating trades focus for
   forgetfulness. Mitigation (§4): keep a *signal without content* — a dot or
   count on the `s` segment + a tooltip line (`s: 12 due`) — when `s` is due
   but inactive. Cheap, no extra slot, preserves the nudge.
2. *`none` (fresh vault / new device) must not be empty.* `bracketRepeatType`
   starts `null` until the first `]s/]w/]n` or indicator click. Strict "show
   only the active walk" renders *no* footer on first run — the worst moment to
   hide the review. Default `none` to the `s` view (the morning review is the
   default walk; `s` is also the only walk with a due obligation).
3. *`n` has low ambient value and high churn.* Its content changes on every
   note switch and is empty on most notes (no prev/next links). An always-on
   `n` footer when `n` is active will mostly read `No prev/next links` — noise.
   Mitigation: let the `n` view collapse to just the mode switch + hint on
   narrow bars first (shed order §4), and consider auto-hiding the *content*
   while keeping the switch when the note has no links, rather than shouting
   emptiness.
4. *Three footers triple the contract surface.* Separate items mean three
   lifecycles, three `ResizeObserver`s, three paint keys, three click targets,
   and a cross-plugin visibility arbiter ("exactly one visible"). One slot with
   three *views* keeps one lifecycle and one `Fit` routine; the mode only swaps
   the view-model builder. Strongly prefer views-over-items.
5. *Cross-plugin coupling.* The footer lives in ledger-tools; the mode lives in
   nav. Gating couples them on every cursor move. Reading nav's `localStorage`
   key directly from ledger-tools is brittle (key rename, SSR/harness fakes,
   two devices). A versioned `api.bracketRepeat` namespace with push
   (`onChange`) beats polling and keeps the existing api-versioning discipline
   (`laneWalk v2`, `quickRoll v1`).
6. *Mobile.* Both current widgets are desktop-only. Keep the walker footer
   desktop-only too; do not let gating become the excuse to add a mobile
   status-bar item in the same change.

**Adjustments to the requirements I am making (explicit).**

- (a) Ship **one walker-footer slot**, not three items; the `[[ s w n ]]`
  switch moves *into* it. If reviewers insist on separate items, §5 gives the
  literal mapping, but the recommendation is the single slot.
- (b) `s` content gated, `s` *existence signal* ambient (dot + tooltip count).
  Strict hiding is a footgun on review mornings.
- (c) `none` → `s` view, not hidden. First-run and new-device behavior matters.
- (d) `w` footer shows lane counts + position (the request's "for example" is
  exactly right) but **no** upkeep meter, no Alt+P chip, no commitment-vs-upkeep
  divider — those are `s`-queue concepts. Lanes get their own divider (READY is
  the non-lane backlog; `PENDING · NEXT | READY` mirrors the dash).
- (e) `n` footer shows link *targets*, not counts, and is allowed to be terse
  (`No prev/next links` sheds first). Do not block the change on giving `n` a
  queue it does not have.

## 3. Proposed glossary term: walker footer

Draft to be filed as `sase/memory/glossary/walker-footer.md` (keyword
`Walker Footer`, alias `walker footer`; `review footer`, `lane footer`, `link
footer` as related aliases — not separate terms):

> The desktop status-bar item that previews the active bracket walk — the family
> `[[` / `]]` will repeat. It has three views sharing one slot and one mode
> switch (`s` review · `w` lanes · `n` links; click a letter to switch, `none`
> shows the review view). The **review footer** (`s`) projects the freshness
> queue (`⟳ Review r/N · TIER i/M …`, groups, upkeep meter, `]s next` / Alt+P
> hint, click = `]s`). The **lane footer** (`w`) projects the lane-walk queue
> (`⫽ Lanes r/N · PENDING i/A · NEXT j/B · READY k/C`, current lane tinted,
> click = `]w`). The **link footer** (`n`) previews the current note's labeled
> links (`‹ prev · next ›`, click = next link). Only the active view's content
> shows; a dot on the `s` segment plus a tooltip count keeps due review work
> ambient while another walk is active. All views are read-only projections
> (numbers are queue positions, never progress), hide when their source is
> unavailable (Tasks / Today plan / no Markdown note), and shed content
> end-first with `…` on narrow bars. See [[glossary/morning-gtd-review-footer]],
> [[glossary/task-freshness]], [[decisions/review-walk-is-tiered]].

Why this shape: one term, three views — matches the one-slot implementation,
lets the existing `review footer` strand stay as the `s`-view detail page (add
a "a kind of walker footer" line to it rather than rewriting it), and avoids
minting three top-level terms for one status-bar pixel. The `review footer is a
walker footer` subtype relation the request asks for falls out directly.

## 4. Detailed design

### 4.1 Mode model (the only new state)

- Source of truth stays nav: `bracketRepeatType: 's' | 'w' | 'n' | null`,
  in-memory + `localStorage`, set by every `]s/]w/]n`, `]S/]W`, `]]/[[`,
  `]}/{[`, and indicator clicks (existing `rememberBracketRepeatType`).
- New additive nav API (no behavior change to existing walks):
  `api.bracketRepeat v1 = { version: 1, current(): 's'|'w'|'n'|null,
  onChange(fn): unsub }`. Ledger-tools subscribes once at
  `setupFreshnessStatusBar` time; on change it re-runs the footer update with
  `{ contextOnly: true }`-style cheap path plus a queue refresh only when the
  newly active view needs data it does not have (`w` needs `laneWalk.queue()`,
  `n` needs the active note scan).
- Effective view = `current() ?? 's'` (adjustment (c)). The `s`-due dot shows
  when `freshness walk > 0` regardless of view.

### 4.2 Content specs (keep each view's grammar parallel, not identical)

Shared chrome (all views): `[[ s w n ]]` switch at the left (existing pill
markup/logic, moved, not rewritten) · `·` separators (existing
`::before` rule) · `…` overflow marker · tabular-nums · tooltip + `aria-label`
(full sentence even when the bar sheds text) · click on content jumps
(s → `jump-to-next-due-task`, w → `jumpToLaneTask(1)`, n → `openLabeledBodyLink("next")`).

`s` view: **unchanged content** from today (due/context/detail/hint/groups/meter,
answer chip, tier colors, divider before ROTTEN/POST, shed order
groups-end-first → stage→detail → hint → meter, TICK exception). Only the
*visibility rule* changes (§4.3). No redesign risk to the most-used view.

`w` view (new): `⫽ Lanes r/N · PENDING i/A · NEXT j/B · READY k/C · hint`.
- `r/N` = lane anchor position when the cursor sits on a lane entry
  (`rank/total` from `laneWalkQueueFromTasks`), else `N lanes` / `N due`.
  Lane position `i/A` uses `laneRank/laneTotal` (same fields the toast shows).
- Groups: three lane groups in lane order with lane hues
  (reuse `--task-status-in-progress` pending, `--task-status-next` next,
  `--color-blue` ready — the toast's exact tokens); current lane tinted +
  semibold like today's `bob-freshness-tier`; divider before READY
  (`PENDING · NEXT | READY`) because READY is the gated backlog, not a lane.
- Hint: `]w next`; on a lane row, the row's lane hint
  (`Ctrl+Shift+Enter today · Alt+N …`, same strings as the toast).
- Detail: task text / note name chip source = `buildLaneWalkNoticeModel`
  fields (already computed for toasts; reuse, do not re-derive).
- Shed order: READY group → NEXT group → detail → hint (PENDING context +
  `r/N` last, mirroring "current tier stays visible").
- Empty: `✓ Lanes clear` (+ `REVIEW n` / `TODAY n` chips in tooltip when the
  empty-notice model carries them — reuse `buildLaneWalkEmptyNoticeModel`).
  Click on empty still runs `]w` (lands or re-announces the empty notice).

`n` view (new): `⇄ ‹ PrevLabel · NextLabel › · hint` where labels are the
note's first rendered `prev`/`next` texts via the existing
`findFirstRenderedLink` scan (frontmatter/fence-safe, wikilink + Markdown,
arrow-aware). Truncate each label to ~24 chars with ellipsis; full targets in
tooltip. Hint: `]n / [n`. Click = next link (same as `openLabeledBodyLink`).
No counts, no colors beyond neutral ink (links have no lane/tier hue —
resist inventing one). Empty note / no links: `No prev/next links` text that
is first to shed; tooltip still names the note. Non-Markdown focus (graph,
settings): hide content, keep switch.

### 4.3 Visibility rules (replaces "always show `s` when due")

| Situation | Walker footer shows |
|---|---|
| Desktop, Tasks available, view `s`, `s` queue nonempty | `s` view (today's behavior verbatim) |
| View `s`, queue empty, cursor on prioritized task | hint-only `⟳ Nothing due · <Alt+P preview>` (today's behavior) |
| View `s`, queue empty, otherwise | hidden (today's behavior) |
| View `w`, lane queue nonempty | `w` view; `s` segment carries a dot + tooltip `s: N due` iff `s` queue nonempty |
| View `w`, lanes empty | `✓ Lanes clear` view (dot rule same) |
| View `n`, note with prev/next links | `n` view; dot rule same |
| View `n`, note without links | `No prev/next links` (sheds first); dot rule same |
| Tasks unavailable / Today plan loading | the *active* view's unavailable variant (`Review unavailable` / `Lanes unavailable` / `Links unavailable`), never another view's content |
| Mobile, or no status-bar host | nothing (unchanged; no new mobile surface) |
| Fresh install / `null` mode | `s` view (adjustment (c)) |

Switching views never writes, never stamps, never moves the cursor — it only
repaints. `[[`/`]]` behavior is untouched.

### 4.4 Beauty notes (what makes it look intentional, not bolted-on)

- **One icon per walk, same slot:** `⟳` review (existing) · `⫽` lanes (suggest;
  evokes the lane rail; falls back to text on fonts without it — verify in the
  target Electron build before locking) · `⇄` links. Same `bob-freshness-icon`
  muted-ink treatment; meaning still carried by text, never color alone
  (existing a11y rule).
- **Color discipline:** `s` keeps all nine tier hues; `w` uses only the three
  lane tokens; `n` uses none. Shared `color-mix`/`oklch` ink pipeline, same
  lightness normalization per theme (the existing `--bob-review-ink-l`
  mechanism generalizes to `--bob-walker-ink-l`; do not fork the CSS).
- **Same shed choreography:** reuse `freshnessFooterFit` generalized to
  (groups, detail, hint, meter?) with the `…` marker and the answer-chip/meters
  exception pattern. `n` has no groups/meter — it sheds labels first.
- **Fold the indicator in, don't stack it:** the `[[ s w n ]]` pill becomes the
  footer's leading element (same buttons, same `aria-pressed`, same flash
  animation on `[[`/`]]` repeat). One `ResizeObserver`, one paint key
  (`mode + view fields + tooltip + answer key`), one `is-instant` transition.
  The bar gets *narrower* than today in the common case, which is the visible
  payoff for the whole change.
- **Tooltips stay complete:** every shed state keeps the full sentence in
  `title`/`aria-label`, including the ambient `s: N due` line when inactive
  and the `WIP = PENDING`-style legend lines for whichever view is shown.

### 4.5 Reliability notes (what makes it not flaky)

- **No polling.** Push via `api.bracketRepeat.onChange`; footer updates ride the
  existing 150 ms debounce + 50 ms context-only cursor path. A missed event
  only delays a repaint until the next cursor/memo tick — never a wrong walk.
- **Version-gated degradation.** If nav lacks `api.bracketRepeat` (old
  install), fall back to today's behavior: always-on `s` view. If ledger lacks
  `api.laneWalk v2`, the `w` view shows its unavailable variant (same strings
  as `LANE_WALK_TASKS_NOTICE` / `LANE_WALK_TODAY_NOTICE`). If the active note
  scan throws, the `n` view shows unavailable, never an exception (both paint
  paths already never-throw; keep that invariant).
- **Test surface (harness-first, matching existing discipline):** pure
  view-model builders (`buildLaneFooterView`, `buildLinkFooterView`,
  `buildWalkerView(mode, …)`) tested in the ledger/nav harnesses like the
  existing `ledger-tools-harness.cjs` / `navigation-hotkeys-harness.cjs` cases;
  paint tests assert shed order + `…` + tooltip completeness; integration tests
  assert exactly-one-view-visible across mode switches, `null → s` default,
  click routing per view, and the `s`-dot-while-inactive rule. Docs
  (`docs/bob-ledger-tools.md` footer section, `docs/bob-navigation-hotkeys.md`
  keymap + indicator paragraphs) and the two glossary strands update in the
  same change — the repo's `docs-check.sh` / inventory tooling should cover the
  new strings.
- **Perf:** `w` queue reuses the memoized `laneWalk` result the toast path
  already caches; `n` scan is one active-note split (frontmatter/fence skip),
  debounced with cursor updates. No vault-wide scans on cursor move.

## 5. If the team prefers the literal request (three items, strict gating)

Same content specs as §4.2, but: keep the `[[ s w n ]]` indicator as its own
item; add `bob-lane-footer` and `bob-link-footer` status-bar items beside
`bob-freshness`; visibility arbiter in ledger-tools (`s` item `hidden` unless
view `s` and due; `w`/`n` items `hidden` unless their view active and
available). Cost vs §4: +2 status-bar slots, +2 lifecycles/observers/paint
keys, a three-way mutual-exclusion invariant to test, and the strict-hiding
footgun (§2.1) with no ambient `s` signal unless a fourth dot element is added
anyway. I advise against it, but it is fully specified by this report if chosen.

## 6. Recommended solution (phased)

1. **Phase 0 — contract (small, reviewable).** Add nav `api.bracketRepeat v1`
   (`current`, `onChange`, version constant, harness coverage). No UI change.
2. **Phase 1 — walker shell.** Move the `[[ s w n ]]` switch markup into the
   ledger-tools footer element as its leading segment (or a shared
   `walker-chrome` builder both items use during migration); effective view =
   `current() ?? 's'`; `s` view byte-identical to today; other views render an
   honest "coming soon" disabled variant. Ship visibility rules + `s`-dot.
   Docs + glossary `walker footer` strand land here.
3. **Phase 2 — `w` view.** `buildLaneFooterView` on `api.laneWalk v2` counts +
   anchor fields; lane hues, divider, shed order, click = `]w`; empty/clear
   states; harness + paint tests.
4. **Phase 3 — `n` view.** Per-note `findFirstRenderedLink` scan (reuse nav
   parser via additive `api.linkPreview v1` or a shared pure helper — do not
   duplicate the arrow/frontmatter/fence logic); terse layout; click = next
   link; shed-first emptiness.
5. **Phase 4 — remove the second status-bar item** (the standalone
   `[[ s w n ]]` indicator) once the integrated switch proves itself; keep the
   flash/repeat behavior. Announce in `docs` + tooltip copy, not silently.

Each phase is independently shippable and revertible; Phase 1 alone delivers
the requested gating with zero new-queue risk.

## 7. Open questions for Bryan (design input wanted, not blockers)

1. The ambient `s`-dot while `w`/`n` is active: dot-only, or a compact
   `· s: N due` text fragment in the inactive views? I recommend dot + tooltip
   (quietest), but a persistent one-group count is more honest on review
   mornings.
2. `n` footer click: next link (my default) vs alternating prev/next on
   successive clicks? Next-only matches `]]` semantics; say so in the tooltip.
3. Lane footer icon `⫽`: acceptable, or prefer reusing the lane checkbox glyphs
   (`/` pending, `*` next, hollow box ready) inline in the groups? The latter is
   more literal but noisier at 12 px.

---

### Appendix — file map for implementers

| Area | Files |
|---|---|
| `s` view (keep) | `plugins/bob-ledger-tools/src/120-freshness-footer.js`, `121-freshness-footer-paint.js`, `240-plugin-freshness-status.js`, `styles.css` `.bob-freshness*` |
| Mode state (extend) | `plugins/bob-navigation-hotkeys/src/546-plugin-bracket-repeat.js`, `547-bracket-mode-indicator.js`, `490-plugin-lifecycle.js` (remember-calls) |
| `w` data (reuse) | `plugins/bob-ledger-tools/src/071-lane-walk-model.js` + nav `542-lane-walk-model.js`, `543-lane-walk-notice.js`, `544-plugin-lane-walk.js` |
| `n` data (reuse) | `plugins/bob-navigation-hotkeys/src/670-plugin-project-files.js`, `680-plugin-link-parse.js` |
| Docs + memory | `docs/bob-ledger-tools.md` (~190–199), `docs/bob-navigation-hotkeys.md` (keymap + indicator), `sase/memory/glossary/morning-gtd-review-footer.md` (add "a kind of walker footer"), new `sase/memory/glossary/walker-footer.md` |

*Method note: this report was produced independently for the 5-researcher swarm.
I did not open, read, or consult any peer `__cdx` / `__cld` / `__grk` / `__gem`
report; shared sources above (code, docs, memory) were consulted directly. The
linked `bob-plugins` checkout was opened via `sase repo open bob-plugins`
(audit-logged) and read-only.*
