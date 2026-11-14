# Bank-row bracket walks: `[b` / `]b` / `[B` / `]B` plus a bank walker-footer panel

> **Researcher:** **mus** (independent swarm report, `__mus` suffix).
> Date: 2026-11-14. Question: should Bob gain `[b` / `]b` (step across bank
> rows, waiting-only when waiting rows exist, otherwise all rows), `[B` /
> `]B` (first bank row of the previous/next day), and a dedicated walker
> footer for them? Lead the design; critique the plan; adjust requirements
> where justified; end with a recommended solution.
>
> Goal: intuitive, reliable, beautiful.

## Bottom line

**Build it — with three adjustments.** The request is a good idea: bank rows
are the one Bob-edited content family with no keyboard walk, and the
bracket-walk grammar (`lowercase = step`, `UPPERCASE = group jump`,
`[[` / `]]` repeat, one walker-footer panel per family) extends to bank rows
almost without invention. No Rust/CLI change is needed: `bob bank list -a -f
json` already returns every row with `path`/`line`/`date`/`acknowledged`,
and the ledger bank-data service already memoizes and invalidates those
fetches.

The three adjustments (all called out, §2):

1. **(A1) `[b` / `]b` should walk waiting rows only — not fall back to all
   rows.** The requested "waiting-only when waiting exist, otherwise all" is
   the one requirement I would not ship: it makes queue membership depend on
   queue-global state, so acking the last waiting row silently redefines the
   walk under the user's feet (the `r/N` denominator jumps, the footer
   changes meaning). Every existing walk has a stable predicate: `]s` walks
   due tasks and says `Review clear` when empty; it never degrades into
   walking all tasks. The bank walk should do the same: waiting-only, plus a
   calm `Bank clear` state. All-rows browsing is already covered by the
   proposed `[B` / `]B` day jumps (which work whether or not waiting rows
   exist) and by the bank badge's click-to-oldest-waiting.
2. **(A2) One fourth walker-footer *panel*, not a second footer item.**
   "Their own walker footer" should mean a `b` panel inside the existing
   one-slot walker footer (now a documented glossary term with `s`/`w`/`n`
   panels), gated on a fourth bracket family `b` — not a new status-bar
   item. This reuses the settled one-host architecture and its reliability
   invariants verbatim.
3. **(A3) Scope the walk vault-wide across `bank/*.md`, not to the current
   note.** The waiting queue is cross-month by definition (`bob bank list`
   groups waiting days across every month; import's `Next:` line names "the
   oldest month that still has waiting rows … and K more months"). An
   in-note-only walk would strand at every month boundary — exactly where the
   oldest waiting rows live.

With those changes the feature is: two nav commands + two day-jump commands
(fourth bracket family `b`, persisted, repeated by `[[` / `]]`, group-jumped
by `]}` / `[{`), one ledger-owned bank-walk queue model, one `b` footer
panel, a `b`-letter in the `[[ s w n ]]` selector (making it `[[ s w n b ]]`),
and a quiet `b` dot for waiting rows while another walk is active. Phased
plan in §6; open questions for Bryan in §7.

*Method note: produced independently for the 5-researcher swarm. I did not
open, read, or consult any peer `__cdx` / `__cld` / `__grk` / `__gem`
report; shared sources below (code, docs, audited memory) were consulted
directly. The linked `bob-plugins` checkout was opened via `sase repo open
bob-plugins` (audit-logged) and read-only; the `bob bank list` JSON shape
was read from checked-in fixtures plus `src/native/bank/cli.rs`.*

## 1. What I read (evidence, not assumption)

All `bob-plugins` paths below are in the linked checkout; `bob-cli` paths in
this workspace.

- **Bank row grammar** — `docs/bank.md` §§ "Row grammar", "Ownership",
  "Import" (lead-verified by reading): a row is a top-level checkbox list
  item under a day heading whose body starts with an amount; `[ ]` waiting,
  `[x]`/`[X]` acknowledged; trailing `^bank-<hex>` identity; indented
  children are free notes; non-amount checkbox lines are plain checklist
  lines, never rows. Day headings: `## Thu Nov 12` canonical, three more
  forms read, any other `##` heading is not a day, empty day headings legal.
- **Bank row memory** — `sase memory read glossary:"Bank Row"` (audited):
  typed rows start ticked, import writes the rest unchecked once, `ack`
  ticks waiting rows, Ctrl+Enter on a waiting row opens the Category card
  which ticks it and files `[cat:: key]`; the card stays open on the next
  waiting row. Rows never carry `#task`.
- **Bank month notes** — `glossary:bank-month-note` (audited):
  `bank/YYYY-MM.md`, filename authoritative, one `##` heading per day
  oldest-first, totals drawn at read time.
- **CLI contract** — `docs/bank.md` + `src/native/bank/cli.rs:87,216-220`:
  `bob bank list` is "the waiting queue across every month, grouped by day,
  oldest first"; `-a` shows all rows; `-m` limits to one month; read-only.
  Import's human `Next:` line points at the walk: "file the N waiting rows —
  Ctrl+Enter on each in bank/YYYY-MM.md (or bob bank to list them)" plus
  "and K more months". No CLI change needed for any of this research.
- **List JSON shape** — ledger fixture
  `scripts/fixtures/bank/list-waiting.json` (read in full): envelope
  `{filter, month, days[{date, heading, path, line, rows[]}], counts{rows,
  waiting, flagged}}`; each row carries `path`, `line`, `date`, `account`,
  `cents`, `payee`, `category`, `links`, `note`, `flagged`, `acknowledged`,
  `id`, `origin`, `suggestion`. This is a walk backend off the shelf:
  stable per-row locations plus the exact waiting/all split the walk needs.
- **Bank decode + data service** — ledger `241h-plugin-bank-decode.js`
  (`bankBuildArgs`, `bankDecodeList`, `bankNormalizeNavigation`) and
  `241j-plugin-bank-data.js` (memoized `apiBankFetch`, filtered
  invalidation, generation guards, `BANK_CACHE_SIZE`). The fetch, cache,
  and invalidation machinery the walk needs already exists and is
  bank-JSON-shaped.
- **Category card advance** — ledger `248-plugin-bank-category-card-actions.js:248`
  (`bankCategoryNextWaiting({scan, filedLine})`) and `245-…-model.js:50`
  (post-file "next $X waiting" copy): an acknowledge-*walk* already exists
  inside the card. `[b`/`]b` must complement it (navigation), not duplicate
  it (filing).
- **Bracket repeat + mode** — nav `546-plugin-bracket-repeat.js` (read in
  full): `bracketRepeatType ∈ {s, w, n}`, `BRACKET_REPEAT_PLANS` and
  `BRACKET_REPEAT_UPPERCASE_PLANS` (`n` has no uppercase), `]]`/`[[`
  repeat, `]}`/`[{` uppercase-repeat, persistence in per-device local
  storage. `482-walk-mode-nav-api.js` (read in full): `api.walkMode` v3
  (`current`/`select`/`links`/`setAttention` with per-member versioning).
- **Selector** — nav `547-bracket-mode-indicator.js` (read in full, 870+
  lines): always-visible desktop `[[ s w n ]]` segmented control,
  click-to-switch-without-walking, flash on repeat, tooltip/aria per
  family, attention-dot support on `s` only.
- **Lifecycle keymap table** — nav `490-plugin-lifecycle.js:260-345` (read):
  `]s`/`[s`, `]S`/`[S` (group jump), `]w`/`[w`, `]W`/`[W` (lane jump),
  `]n`/`[n` (links, no uppercase). Verified: **no `[b`/`]b`/`[B`/`]B`
  binding exists anywhere** in the plugin or its docs — the keys are free.
- **Walker footer** — `glossary:walker-footer` (audited): one
  bob-ledger-tools status-bar item, exactly one panel at a time chosen by
  the persisted family, shared slot anatomy (glyph + position, current
  group, detail, hint, remaining groups, meter), read-only projection,
  clear states distinct from loading/unavailable, quiet dot on `s` while
  review commitments are due off-`s`. Plus the 202611 `bracket_walk_footers`
  synthesis (prior swarm, read as unrelated prior research, not peer
  material): one host + view-models, generation-checked async, mode paint
  synchronous, no polling, both load orders tested.
- **Review tier order** — `decisions:review-walk-is-tiered` (audited):
  PRE → NEW → PROJECTS → PENDING → NEXT → TICKLER → REFERENCES → ROTTEN →
  POST; due-only; `]S`/`[S` cycle occupied tiers. This is the template for
  `[B`/`]B` day jumps (occupied-day stepping, §4.3).

## 2. Critique: is this a good idea?

**Yes — with the three adjustments above.** Reasons, in the request's own
terms (intuitive, reliable, beautiful):

**Intuitive.** The bracket grammar is already learned: lowercase steps items,
UPPERCASE steps groups, `[[`/`]]` repeats the family, the selector shows
which family is live. Bank rows slot into that grammar with zero new
concepts: `b` = bank, `[b`/`]b` = step rows, `[B`/`]B` = step days — exactly
parallel to `s`/`S` (tasks/tiers) and `w`/`W` (lane tasks/lanes). The
mnemonic is free and the keys are unbound. Two caveats: (i) Vim users may
expect unimpaired-style `[b`/`]b` = buffer cycling — but stock Vim does not
define them and Obsidian's Vim emulation does not implement buffer lists, so
there is no real conflict; still, list it as a verification item on the Mac
(§6, phase 6). (ii) The uppercase letter needs Shift (`[B` = `[` + Shift+b);
  Obsidian hotkeys distinguish `[b` from `[B`, same as the existing
  `]s`/`]S` pair, so the parallel holds on real keyboards.

**Reliable.** The data plane already exists (`list -a` JSON with
path/line/date per row; memoized, invalidated, generation-guarded fetch in
ledger). The risk is all in the walk predicate — hence A1. The rest of the
plan reuses the walker-footer's proven invariants (one snapshot per paint,
read-only paint, activation revalidates, both plugin load orders).

**Beautiful.** A fourth panel in the one-slot footer keeps the status bar at
one walk widget + selector instead of adding chrome. Money already has ink
tokens (bank badge: In green, waiting amber, tabular numerals); the `b`
panel reuses them, so it looks like family, not a bolt-on.

### Where the literal plan goes wrong

1. **Conditional queue (A1).** "Waiting-only when waiting exist, otherwise
   all" makes membership a function of global state. Consequences: (a) the
   denominator changes without any local edit — ack the last waiting row and
   `2/3 waiting` becomes `14/24 rows` on the next press; (b) the footer must
   explain *which* walk is live on every paint, carrying a mode flag the
   `s`/`w` panels never need; (c) `]]` repeat becomes non-idempotent in a way
   no other family is: the same key does different things depending on
   vault-global ack state. The established pattern is stable predicates +
   clear states (`Review clear`, `Lanes clear`). Bank should be
   `Bank clear`, and the "browse everything" job belongs to `[B`/`]B`,
   which is unconditional by construction (days exist whether or not waiting
   rows do).
2. **"Their own walker footer" read as a second item (A2).** Two ledger
   status-bar items plus the selector = three walk widgets fighting for
   ~300–600 px, two lifecycles, two paint keys, and a mutual-exclusion
   arbiter. The whole point of the walker-footer work was one slot. A `b`
   panel is strictly cheaper and keeps "the bar tells the truth about `]]`".
3. **Unstated scope (A3).** The request never says whether `[b` stays in one
   month note or crosses months. The waiting queue is cross-month by CLI
   contract, and the oldest waiting rows (the ones the walk exists for)
   routinely live in older months. In-note-only scope would make the walk
   useless precisely when it is most needed. Vault-wide `bank/*.md` order
   (month, day heading, line) is the only scope consistent with `bob bank
   list`.

### Different approaches considered

- **No new walk; teach the Category card to open from the bank badge only.**
  Rejected: the badge already opens the oldest waiting row, and the card
  already advances — but there is no way to *look* at rows without filing
  them, no way to step backwards, and no day-level browsing. Navigation and
  filing are different jobs; the card covers filing.
- **`[b`/`]b` = all rows always, waiting surfaced by styling + wrap order**
  (e.g. waiting-first ordering). Rejected: waiting-first ordering breaks
  chronological narrative (a statement reads oldest-first; reordering it for
  walk convenience makes the footer position lie about note order), and
  styling alone doesn't shorten a 200-row month to the 3 rows that need
  action. Stable waiting-only predicate dominates.
- **Uppercase `[B`/`]B` = first/last waiting row (endpoints) instead of day
  jumps.** Rejected: endpoints duplicate what the badge (oldest waiting) and
  a footer click could do, and waste the one free uppercase slot. Day jumps
  parallel `]S`/`]W` group jumps and give the only all-rows browsing the
  design retains after A1 — they earn their keys.
- **`b` walk inside `bob-ledger-tools` instead of nav.** Rejected for motion,
  kept for data — same split as lanes: ledger owns the queue model
  (`api.bankWalk v1`), nav owns commands/anchors/repeat/selector. Nav already
  owns every bracket family; a fifth motion owner would fork the repeat
  tables and the selector.

## 3. Requirement adjustments (explicit)

| # | Adjustment | Rationale |
|---|-----------|----------|
| A1 | `[b`/`]b` walk waiting rows only, always; when none, paint `Bank clear` and re-announce (no silent fallback to all rows) | Stable predicate; matches `]s`-due-only + `Review clear`; kills the teleporting-denominator problem (§2.1) |
| A2 | The "own walker footer" is a fourth panel in the one-slot walker footer, gated on family `b` | Reuses the shipped one-host architecture, paint pipeline, and shed choreography; no new status-bar item |
| A3 | Walk scope is vault-wide over `bank/*.md` in (month, day, line) order, Day-jumps cross months | Matches the CLI waiting queue; oldest waiting rows live in older months |
| A4 | `[B`/`]B` land on the first *waiting* row of the previous/next *day that has waiting rows*; when the walk is clear (no waiting anywhere), they land on the first row of the previous/next *occupied* day | Keeps day jumps useful in both states without reintroducing a conditional row predicate: the *day* predicate adapts, the *row* walk stays waiting-only; when clear, day jumps become the browse-everything path |
| A5 | Footer position `r/N` counts waiting rows in the A1 walk; day jumps show a day fraction (`day 3/9`) not a row fraction | Positions are queue membership, never progress (walker-footer invariant); day jumps are group jumps like `]S`/`]W`, which show group landings, not rank/total |
| A6 | Add a quiet `b` attention dot (waiting-count, amber) on the selector's `b` letter while another family is active — symmetric with the `s` dot | Waiting money is a due obligation like review commitments; without it, ending Tuesday on `s` hides Wednesday's new waiting rows. Cheap, static, reversible |
| A7 | Clicking the `b` panel behaves like `]b` (next waiting); the panel never files, ticks, or opens the Category card — filing stays on Ctrl+Enter / the card | Read-only projection invariant; activation only navigates (same rule as `s`/`w` panels) |

What I am **not** changing: the four keys, their mnemonics, the lowercase/UPPERCASE
step/group split, the dedicated footer surface, or the spirit of the fallback
(A4 preserves browse-everything through day jumps rather than through a
redefined row walk).

## 4. Detailed design

### 4.1 Mode model (the only new state)

- `bracketRepeatType` gains `"b"` alongside `s`/`w`/`n` in nav
  (`546-plugin-bracket-repeat.js`): `normalizeBracketRepeatType`,
  `BRACKET_REPEAT_PLANS.b` → `jumpToBankRow(±1)`,
  `BRACKET_REPEAT_UPPERCASE_PLANS.b` → `jumpToBankRow(±1, {dayJump: true})`.
  The `n`-only "no uppercase walk" notice copy updates to name `n` as the
  sole exception.
- `api.walkMode` v3 → **v4** (additive, per-member versioning as before):
  `current()` may return `"b"`; `select("b")` records and never walks;
  `setAttention` accepts `"b"` with `{tier: "waiting", label}` for the A6
  dot; `links()` untouched. Doorbell event unchanged (fires on real change +
  once at setup).
- Selector becomes `[[ s w n b ]]` (`547`): one new segment reusing the
  existing button/aria/flash machinery. Fragment is at ~870/1000 lines —
  the `b` segment config is a data row in `BRACKET_MODE_FAMILIES`, not new
  painter logic.
- Effective view: no `?? 's'` default change — unset still shows no panel
  (settled walker-footer ruling). First `[b` press both selects `b` and
  walks, like every other family.

### 4.2 Queue model (ledger owns it)

New `api.bankWalk v1` in bob-ledger-tools, mirroring `api.laneWalk v2`:

- **Source:** memoized `bob bank list -a -f json` (all rows) — one fetch,
  both predicates derived client-side (waiting = `acknowledged === false`;
  all = every row). No new CLI, no new subprocess shape; the bank-data
  service's cache/invalidation/generation machinery is reused, not forked.
- **Ordering:** `(path month, day date, line)` — chronological, oldest
  first, matching note order and the CLI's "oldest first" queue. (Month
  filename order == chronological for `YYYY-MM` stems.)
- **Waiting view:** rows with `acknowledged === false`, excluding empty
  stubs (the CLI already yields no findings for `- [ ] $` bare stubs; the
  model must not resurrect them — verify against `bankDecodeList`).
- **Day index:** occupied days (days with ≥1 row) and waiting-days (days
  with ≥1 waiting row) derived from the same snapshot — one snapshot per
  paint, per the reliability invariants.
- **Cursor matching:** entries carry `path`/`line`; reuse the existing
  queue-cursor matcher pattern (validated current-member only — no
  fabricated `r/N`, same rule as lanes). Dirty-editor case: when the active
  note is a bank month note with unsaved changes, line numbers from JSON
  (disk) may be stale — generation-check against the vault event that
  produced the snapshot, and on mismatch fall back to scanning the live
  editor content with the row grammar (top-level checkbox + amount; §1
  grammar) for that note only. Never silently land on a wrong line: on
  unresolvable mismatch, re-announce rather than jump.
- **Non-rows:** plain checklist lines under day headings (no amount),
  fenced code, `total:` legacy lines, and `## Notes`-style non-day
  sections are never entries — the CLI grammar decides, the model mirrors
  it.

### 4.3 Motion semantics (nav owns it)

`jumpToBankRow(direction, {dayJump})`, pure planners tested like
`planLaneWalkJump` / `planReviewGroupJump`:

- **Step (`[b`/`]b`):** next/previous waiting row in vault-wide order from
  the resolved origin (cursor → anchor → anchor-gap tuple → list end,
  same origin ladder as lanes). Wrap with `wrapped` chip. Vim-count `N`
  steps N rows with remainder arithmetic (no loop — same as group steps).
  Empty (no waiting anywhere): re-announce the clear notice; do not move.
- **Day jump (`[B`/`]B`):** first waiting row of the previous/next
  waiting-day (A4); when no waiting rows exist anywhere, first row of the
  previous/next occupied day. Skips empty day headings and non-day `##`
  sections. Cycling, wrap chip on wrap. This is the `]S`/`]W` analog: group
  stepping over occupied groups, landing on the group's first member.
- **Landing:** open `bank/YYYY-MM.md` if not active (bank notes only —
  never retarget a non-bank note), set cursor to the row line, record the
  anchor `{day: todayText, key: path:line, …}` for repeat/origin. Never
  write, never tick, never open the Category card. If the row's checkbox is
  no longer waiting at activation time (acked from the CLI mid-walk),
  re-resolve against a fresh snapshot rather than landing stale.
- **Repeat:** `]]`/`[[` repeat the `b` family once selected; `]}`/`[{`
  repeat its uppercase (day) jump. Family commands and selector clicks
  record the mode; internal advances never change it.

### 4.4 Footer panel (ledger paints it)

Fourth walker-footer view reusing the shared slot anatomy and shed order
(groups-end-first → detail → hint → meter). Proposed copy (amounts from the
fixture shape):

| State | Reads | Activation |
|---|---|---|
| Off-row, N waiting | `$ Bank 3 waiting · Thu Nov 12 2 · ]] next` | `]b` |
| On a validated waiting row | `$ Bank 2/3 · ShopRite $61.20 · Ctrl+Enter file · Thu Nov 12` | `]b` |
| Clear (nothing waiting) | `$ Bank clear · ✓ 0 waiting` (+ `Ctrl+Enter` never hinted here) | `]b` re-announces |
| Day jump landing | `$ Bank · Thu Nov 12 1/3 · oldest waiting day` (day fraction, A5) | `[B`/`]B` continue |
| Data untrustworthy (bob missing/slow, Tasks N/A irrelevant) | `$ Bank unavailable` — never a success-like zero | none |
| Non-bank note + family `b` | panel still paints (vault-wide walk, A3); cursor row simply yields no position | `]b` |

- **Glyph:** `$` — ASCII-clean, renders in every font, and means money at
  12 px better than 🏦 does. Same muted-ink treatment as `⟳`/`⫽`/`⇄`;
  meaning carried by text, never color alone.
- **Hues:** waiting counts in the bank badge's warning/amber token;
  acknowledged/clear states in calm muted ink; day context in neutral ink
  (days have no tier hue — resist inventing one, same ruling as links).
  Reuse badge tokens, don't fork the CSS.
- **Groups slot:** waiting-day groups are wrong for the groups slot (days
  are what `[B` jumps, not a walk queue) — the panel shows the *current
  day* as context and total-waiting as the meter, keeping all six slots
  filled without inventing a queue the walk doesn't have. This is the one
  place the panel deliberately differs from the `s`/`w` grammar, and the
  tooltip says why.
- **Hint slot:** on a waiting row, `Ctrl+Enter file` (existing gesture that
  opens the Category card) + `]b next`; off-row, `]] next` (the A12 ruling
  from the walker-footer synthesis: hints read `]] next` whenever a footer
  is visible). The `s`-panel Alt+P preview has no bank analog — don't invent
  one.
- **Tooltip:** full sentence always: waiting count with exact cents
  (`3 waiting · $1,323.41`), oldest-waiting day + note path, scope line
  ("walks waiting rows across all bank months, oldest first"), family keys
  + day-jump keys, and the A1 rule in one clause ("`[b`/`]b` walk waiting
  rows only; `[B`/`]B` browse days").
- **A6 dot:** amber dot on the selector's `b` letter when `waiting > 0`
  and family ≠ `b`; tooltip/aria carry the count ("Bank: 3 waiting — click
  to show"). Pushed on the same path as the `s` dot (ledger attention push
  on every mode/data event so load order can't lose it).

### 4.5 Beauty notes

- One icon per walk, same slot: `⟳` review · `⫽` lanes · `⇄` links ·
  **`$` bank**. Same size, same muted treatment, tabular numerals.
- Mode switch crossfades panel content ~120 ms (existing motion token);
  count changes never animate; `prefers-reduced-motion` kills the fade;
  fixed height; stable selector geometry across `s→w→n→b` (extend the
  existing bounding-rect e2e assertion to four families).
- Narrow-bar shed for `b`: day context → detail → hint → meter; minimum
  legible state `$ Bank 3 waiting`. Ellipsis never makes a missing month
  look present (truncate payees, never paths).
- Forced-colors: dot gets a ring in bar-background; amber-vs-green never
  the sole carrier (counts are text).

### 4.6 Reliability notes

The walker-footer invariants apply verbatim; bank-specific instantiations:

1. One snapshot per paint — waiting list, day index, counts, and position
   from the same immutable `list -a` result.
2. Generation-checked async — a fetch response paints only if family is
   still `b` and the vault generation hasn't moved; switching families
   invalidates.
3. Mode paint synchronous; data join coalesced on the existing debounce
   paths; no polling, no full-vault rescan on cursor move (bank months
   only, memoized).
4. Lifecycle explicit — both plugin load orders, unload/reload, missing
   provider either direction (nav without `bankWalk` → `b` commands
   announce unavailable; ledger without nav `walkMode` v4 → legacy
   behavior, no `b` panel), thrown listeners never break motion.
5. Activation rechecks — target month note, revision, and row still-waiting
   revalidated before cursor move; stale activation rejected, never landed.
6. Read-only paint — paint/hover/focus/resize/selection never write rows
   or open the card; only explicit Ctrl+Enter (existing command) writes,
   via the existing guarded path.
7. Dirty-note guard (§4.2) — disk-vs-editor mismatch never lands wrong.

## 5. What changes, file by file (for the implementer)

No `bob-cli` Rust change. All in `bob-plugins` (fragments capped at 1000
lines — new models go in new fragments):

- **nav** `546-plugin-bracket-repeat.js` — `"b"` in normalize/plan tables
  (step + day-jump uppercase); `490-plugin-lifecycle.js` — four commands
  (`jump-to-next/prev-bank-row`, `jump-to-next/prev-bank-day`; vault
  keybindings `[b`/`]b` bound via hotkeys, `[B`/`]B` uppercase pair);
  `547-bracket-mode-indicator.js` — `b` family row (letter, name "bank",
  keys, tooltips);
  `482-walk-mode-nav-api.js` — `walkMode` v3→v4 (`current`/`select` admit
  `b`, `setAttention` admits `b`); new `54x-bank-walk-model.js` (pure
  step/day-jump planners) + `54x-plugin-bank-walk.js` (command impl,
  anchor, landing, notices) mirroring the `542/544` lane pair.
- **ledger** — new `bank-walk-queue` fragment (queue + day index over the
  memoized `list -a` result; cursor matcher; clear/unavailable models) +
  `api.bankWalk v1 {version, queue()}` consumed by nav; walker-host routes
  family `b` to a new `bankFooterView` (+ paint entries, sharing the
  painter and fit routine with per-panel drop lists); `b`-dot attention
  push; badge click path untouched.
- **Tests** — extend `test-navigation-bracket-repeat.cjs` (repeat tables,
  `select("b")`, uppercase dispatch, `n`-only no-uppercase copy);
  `test-navigation-bracket-mode-indicator.cjs` (fourth segment, dot);
  new `test-ledger-tools-bank-walk.cjs` (waiting-only predicate, stub
  exclusion, non-day-section exclusion, empty-day skip, wrap + Vim-count
  arithmetic, cross-month order, clear/unavailable states, footer copy +
  shed order + tooltip completeness, dash-parity pin of counts against
  `bob bank list` fixtures); e2e selector-rect stability across four
  families; real-Obsidian Mac smoke (`[b` swaps the panel within a frame).
- **Docs + memory + deploy** — `docs/bob-navigation-hotkeys.md` (keymap
  table + indicator), `docs/bob-ledger-tools.md` (walker-footer section),
  bob-cli `docs/bank.md` (walk paragraph: keys, waiting-only rule, day
  jumps, footer) + `docs/guides/acknowledge-bank-transactions.md`
  (teach `[b` before Ctrl+Enter); new `glossary:bank-walk` strand + one-line
  pointer in `glossary:walker-footer`'s member list; `bob plugins sync`.
  Optional decision record (`bank-walk-is-waiting-only`) capturing A1 and
  its rejected fallback — ask Bryan rather than inferring (decisions-web
  rule).

## 6. Recommended solution (phased)

Each phase shippable; the legacy fallback makes each safe alone.

1. **Contract** — nav `api.walkMode` v4 (`b` in `current`/`select`/
   `setAttention`) + doorbell; ledger `api.bankWalk` v1 over memoized
   `list -a`. No visible change. Extends the bracket-repeat tests.
2. **Motion** — `[b`/`]b`/`[B`/`]B` commands, pure planners, anchors,
   landing, wrap/counts, clear re-announce. Selector shows `b`.
3. **Footer panel** — `bankFooterView`, `$` glyph, amber waiting meter,
   shed order, tooltips/aria; `b` attention dot; gated-`b` routing.
4. **Visual + e2e + placement** — walker-preview extension (waiting,
   on-row, clear, day-landing, unavailable × light/dark × three widths),
   four-family selector-rect assertion, Mac smoke incl. Vim-mode `[b`
   conflict check and Shift-`B` binding check.
5. **Docs + memory + sync** — pages above, `glossary:bank-walk`, optional
   decision record, `bob plugins sync`.

Acceptance that matters most: predicate truth (waiting-only incl. stubs,
plain checklists, fences, non-day sections, empty days); scope truth
(cross-month order == CLI queue order); position honesty (no fabricated
`r/N`, no stale fraction after ack/delete/undo/midnight); link between
surfaces (footer counts == badge waiting == `list` waiting, pinned by
fixture); side-effect zero (paint never writes; preview never opens the
card); lifecycle (both load orders, unload, missing APIs); fit (narrow
bars, long payees, large waiting counts, reduced motion, forced colors).

## 7. Open questions for Bryan

1. **A1 confirmation** — waiting-only + `Bank clear`, dropping the
   fall-back-to-all-rows? (Recommended.) If you keep the fallback, it needs
   an explicit footer mode flag and a specified transition rule — say which
   copy you'd want.
2. **A4 when clear** — should `[B`/`]B` browse all occupied days when
   nothing is waiting (my recommendation), or also re-announce clear?
3. **Dot tint** — waiting-amber (recommended, matches badge) or neutral?
4. **Click behavior** — panel click = `]b` next waiting (recommended, matches
   `s`/`w` click semantics), or open the Category card on the current row?
5. **Decision record** — record `bank-walk-is-waiting-only`, or glossary
   strand only?
