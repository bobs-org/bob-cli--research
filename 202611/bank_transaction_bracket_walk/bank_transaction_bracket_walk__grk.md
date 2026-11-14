# Bank transaction bracket walk: a fourth family `b`

> **Research query.** Add Obsidian keymaps `[b`, `]b`, `[B`, and `]B` to
> traverse bank transactions saved by `bob bank import`. Give them their
> own walker footer. Lowercase keys jump to the next/previous bank
> transaction, restricted to rows that need review when any exist,
> otherwise every bank row. Uppercase keys jump to the first bank row of
> the previous/next day. Lead the design so it is intuitive, reliable, and
> beautiful. Critique the plan; call out justified requirement changes;
> end with a recommended solution.

**Researcher:** grk. Independent swarm report. Did not read peer reports
from this swarm. Baselines: glossary *Bank Row*, *Bank Month Note*, *Bank
Badge*, *Walker Footer* (audited `sase memory read`); `cli_rules.md`,
`docs.md`, `sase_artifacts.md`; bob-cli `docs/bank.md`,
`docs/guides/acknowledge-bank-transactions.md`,
`docs/reference/plugins/bob-navigation-hotkeys.md`; bob-plugins
`546-plugin-bracket-repeat.js`, `547-bracket-mode-indicator.js`,
`482-walk-mode-nav-api.js`, `541-walk-landing.js`, `542-lane-walk-model.js`,
`539-plugin-review-walk-return.js`, `544-plugin-lane-walk.js`; ledger
`122-walker-footer-host.js`, `123-lane-walker-footer.js`,
`124-links-walker-footer.js`, `240-plugin-freshness-status.js`,
`241i-plugin-bank-source.js`, `241j-plugin-bank-data.js`,
`241k-plugin-bank-actions.js`, `241n-plugin-bank-badge-model.js`,
`246-plugin-bank-category-card-write.js`; vault `obsidian_vimrc.md`;
`src/native/bank/list.rs`; accepted walker-footers plan A1–A13; prior
unrelated research `bank_weekly_category_walk` (Category card same-file
walk). Mermaid CLI `@mermaid-js/mermaid-cli@12.0.0`. Figure 1: 577×496 px,
fit 100.0%. Figure 2: 746×879 px, fit 87.6%.

## Bottom line

**Build it as a fourth bracket-walk family `b`.** One more letter on the
existing `[[ s w n ]]` selector, one more panel on the existing walker-footer
host, four vault vimrc maps that are currently free. Reuse the landing,
repeat, counted-N, wrap, and origin machinery that already makes `]s` and
`]w` feel like one instrument.

The request is right about the gap. Bank rows never carry `#task`, so the
review walk will never see them. The Category card already files waiting
rows *inside one month note*. After a Monday import the waiting queue
spans days and can span months; after the last tick the month note is a
statement you still want to browse by day. That is a walk. The vault
already has a walk language. Teach it `b`.

Three requirement changes are load-bearing. Without them the feature
fights the muscle it is trying to join.

1. **Invert the prompt's "respectively."** In this vault, and in
   unimpaired-style maps, `]` is forward and `[` is backward.
   `]b` / `]B` go next; `[b` / `[B` go previous. The prompt swapped them.
2. **Own footer means a fourth panel, not a fourth status-bar item.**
   Walker footers are one host that swaps a view-model. A second
   `margin-right: auto` item would jitter the bar the way three review
   footers would have.
3. **"Need review" is waiting `[ ]` only.** Flagged-and-ticked rows are
   acknowledged investigation marks. Uncategorized-but-ticked rows are
   already filed. Dual-mode membership is automatic: if any waiting row
   exists anywhere under `bank/*.md`, lowercase and uppercase keys share
   that waiting queue; otherwise they share every recognized bank row,
   oldest first.

**Recommended design, in one sentence:** Navigation Hotkeys grows family
`b` with `]b` / `[b` / `]B` / `[B` (and therefore `]]` / `[[` / `]}` /
`[{`); Ledger Tools exposes `api.bankWalk` v1 from a live vault-plus-editor
scan and paints a magenta 🏦 panel on the existing walker-footer host.

## Is this a good idea?

Yes. The Category card closed the *filing* hunt. This walk closes the
*finding* hunt, and it does it with a key family Bryan already uses
without looking.

Four facts make the gap concrete.

1. **Bank rows are invisible to every task walk.** `docs/bank.md` and the
   *Bank Row* glossary strand both say a bank row never carries `#task`.
   `]s`, `]w`, freshness, plan, ready, and the Tasks global filter skip
   them on purpose. A bank-only walk is the only honest way to land on
   them from a daily note, a period note, or `dash.md`.
2. **The Category card is a same-file writer, not a vault walker.**
   `bankCategoryNextWaiting` in ledger `246-plugin-bank-category-card-write.js`
   searches the current month note, wraps once inside that file, and
   "Never opens another file." A Monday import of a 14-day window writes
   waiting rows under several day headings and, at a month boundary, into
   two files. The card will not cross that boundary. `]b` will.
3. **The month note is a statement.** Headings are days, oldest first,
   about six posted rows on a spending day historically. After waiting
   hits zero you still want to skip by day. `[B` / `]B` are the bank
   equivalent of `[W` / `]W` (first of the previous / next occupied
   lane) and `[S` / `]S` (first of the previous / next occupied review
   group). The uppercase jump is already in the family's grammar.
4. **The keys are free here.** Vault `obsidian_vimrc.md` maps `]s` /
   `[s` / `[S` / `]S`, `]w` / `[w` / `]W` / `[W`, `]n` / `[n`, `]]` /
   `[[`, and `]}` / `[{`. It does not map `[b`, `]b`, `[B`, or `]B`.
   Navigation commands for `s` / `w` / `n` ship with no default hotkeys;
   the vimrc is the bind. Bank should follow that exact pattern.

The dual-mode membership is the one place this walk *differs* from `]s`.
Review never falls back to "all tasks" when nothing is due: it paints
`Review clear` and stays put. Bank should fall back to every row because
bank has one walk, waiting often hits zero by Monday evening, and the
month note's job after filing is to be a statement. That is a justified
pattern break, and the footer must label it so the flip is visible.

## Critique of the plan as stated

The plan as stated is four keys, a footer, and a dual-mode queue. Those
are the right objects. The wording fights the existing grammar in three
places, and it leaves five traps unstated.

**The "respectively" mapping is backwards.** The prompt says `[b` / `]b`
jump to the next / previous transaction. Every other bracket family in
this vault, and vim-unimpaired itself, uses `]` for forward and `[` for
backward. Teaching the opposite for one letter would make `]]` after
`]b` feel like a coin flip. Invert it. Call this out as [A1](#requirement-adjustments).

**"Need review" is underspecified.** Waiting `[ ]` is the only status the
grammar gives a bank row. A ⚑ / `!!` flag on a ticked row is "look into
this later," which is ALL-mode browsing. A ticked row with no `[cat::]`
is a filed row whose category is missing; the Category card's **set**
command already repairs that without a checkbox walk. Dual-mode should
key off `acknowledged === false` from `bankScanSource`, matching
`bob bank list` (waiting) versus `bob bank list -a` (all). [A2](#requirement-adjustments).

**"Their own walker footer" will be misread as a new status item.** The
accepted walker-footers research was unanimous: one host, three panels,
persisted family. Adding `b` is a fourth panel on that host. A dedicated
bank status item would fight Keep and the selector for the left edge,
and it would still need the family to know when to show. [A3](#requirement-adjustments).

**The walk's scope is unstated.** The Category card is note-local. `bob
bank list` is vault-wide over `bank/*.md`. The finding hunt only exists
because waiting can live in last month. The walk is vault-wide.
[A5](#requirement-adjustments).

**The walk's writes are unstated.** A tempting merge is "`]b` lands and
opens the Category card." That steals Ctrl+Enter's ritual, surprises
anyone browsing ALL, and couples a read-only walk to a writer. The walk
never writes and never opens the card. The footer hints `Ctrl+Enter
file` on a waiting row. [A6](#requirement-adjustments).

**Day-jump membership is unstated.** If `[B` / `]B` always used every
day's first row while `[b` / `]b` used waiting only, uppercase would
strand you on a ticked row in the middle of a filing session. Both pairs
share the current membership. Empty days in that membership are skipped,
the way `[W` skips an empty lane. [A7](#requirement-adjustments).

**Spawning `bob bank list` per keypress is the reliability trap.** Ledger
already has `api.bank` v2 for JSON totals, and it already has
`bankScanSource` for live editor bytes. A CLI spawn is disk-only, misses
the unsaved Category-card tick you just made, and is too slow for a
counted `9]b`. The walk reads the vault plus open editors. [A9](#requirement-adjustments).

**Unimpaired `[b` is a documented collision, unused here.** In
vim-unimpaired, `[b` / `]b` are `:bprevious` / `:bnext` and `[B` / `]B`
are `:bfirst` / `:blast`. This vault does not enable that plugin, and
Obsidian's unit of "buffer" is a tab with its own maps (`\<` `\>` `\\`).
Ship commands with no default hotkeys; bind them in the vault vimrc;
mention the collision in the Navigation Hotkeys reference so a future
unimpaired user is not surprised.

## Requirement adjustments

Explicitly called out. "Prompt" means the research request as written.

| # | Adjustment | Why |
| --- | --- | --- |
| **A1** | **`]b` / `]B` are forward; `[b` / `[B` are backward.** Invert the prompt's "respectively." | Matches `]s` / `]w` / `]n`, `]]` / `[[`, and unimpaired. |
| **A2** | **"Need review" = waiting `[ ]` only.** Flagged-ticked and uncategorized-ticked rows live in ALL. | Matches `bob bank list` versus `-a`, and `bankScanSource.acknowledged`. |
| **A3** | **Own footer = fourth panel of the one walker-footer host**, family `b`. | Walker-footers A1. A new status item would jitter the bar. |
| **A4** | **Selector becomes `[[ s w n b ]]`.** Generalize the DOM reuse check from `segments.length === 3` to `BRACKET_MODE_FAMILIES.length`. | `547-bracket-mode-indicator.js:423` hardcodes 3. The families array is otherwise data-driven. |
| **A5** | **Walk is vault-wide over `bank/*.md`.** Hub `bank.md` is never a walk entry. | `bankDiscoverMonthPaths` already enumerates canonical month paths; list.rs is vault-wide. |
| **A6** | **The walk never writes and never auto-opens the Category card.** Footer hints `Ctrl+Enter file` on a waiting landing. | Ctrl+Enter is the filing ritual; `]b` is the finding ritual. |
| **A7** | **`[B` / `]B` = first membership row of the previous / next occupied day**, skipping empty, wrapping, from mid-day, like `[W` / `]W`. | Occupied = at least one row in the *current* membership. Shared with lowercase. |
| **A8** | **Quiet attention dot on selector `b` when waiting > 0 and family ≠ `b`.** ~5px, warning/magenta tint, no number, no motion. Tooltip `Bank: 9 waiting — click to show`. | Walker-footers A4 gave `s` a commitment dot and rejected a `w` pip because lanes are almost never empty. Waiting *is* often zero, so a `b` dot is seasonal and honest. |
| **A9** | **Live plugin scan + open-editor overlay** (`api.bankWalk` v1). No `bob bank list` spawn per key. | Editor overlay is how the Category card already sees a tick it just wrote. |
| **A10** | **`]]` / `[[` and `]}` / `[{` include `b`.** Uppercase repeat is the day jump. | Family `n` is the one without uppercase; bank has one, so `]}` is live. |
| **A11** | **Return-to-landed-row on lowercase only, plus counted `N]b` / `N]B`.** `[B` / `]B` never return. | Copies `]s` / `[s` (`539-plugin-review-walk-return.js`) and counted lane jumps. |
| **A12** | **No new CLI in v1.** `bob bank list` / `list -a` stay the terminal projection. | `cli_rules.md` is unused here; spawning bob is the reliability bug, not a missing subcommand. |
| **A13** | **Commands with no default hotkeys; vault vimrc maps.** Keys are free in this vimrc. | Matches every other bracket family. Documents the unimpaired collision. |
| **A14** | **Automatic dual-mode, labeled WAITING / ALL in the footer and toast.** No manual toggle in v1. | The request asked for automatic membership. A pin-ALL click on the label is a later extra, not v1. |
| **A15** | **Oldest-first chronological.** No-origin `]b` lands the oldest membership row; `[b` lands the newest. | Matches `list.rs` day sort and `planLaneWalkJump`'s no-origin ends. |
| **A16** | **Bank-badge click that opens the oldest waiting row also selects family `b`** (still does not walk). | The badge is already a bank-walk entry point (`bankBadgeTarget` prefers `navigation.waiting`). Selecting `b` makes `]]` continue from there. Cheap, honest, optional-feeling but recommended. |

## Design

### Which rows the walk visits

![Which rows does the bank walk visit? If any waiting bank rows exist, lowercase and uppercase keys share that waiting queue. Otherwise both keys share every bank row, oldest first.](fig-membership__grk.svg)

**Figure 1.** Membership is one question with two answers. Waiting, when
it exists, is the whole walk — row steps and day jumps together.
Rendered size: 577 × 496 px; fit scale: 100.0%.

A recognized bank row is a top-level checkbox under a parsed `##` day
heading in a canonical month note, as `bankScanSource` already defines:
fences, stubs, indented children, and non-day sections are out.
Unparsed amounts on an unchecked checkbox still wait — they are broken
rows that still need a look.

Membership is recomputed on every jump and every footer paint:

- If any scanned row has `acknowledged === false`, the queue is those
  waiting rows, oldest date then line.
- Otherwise the queue is every recognized row, same order.

When the last waiting row is filed, the next `]b` is already in ALL. The
toast prefix flips from `WAITING` to `ALL` so the change is a sentence,
not a mystery. Do not freeze WAITING for the rest of the session: that
would empty-notice while the statement still has rows.

This is the justified pattern break versus `]s`. Review's empty state is
"nothing due." Bank's empty-waiting state is "the statement is the
walk." One family, two densities, one label.

### Keys, family, and repeats

| Key | Command id (proposed) | Jump |
| --- | --- | --- |
| `]b` | `jump-to-next-bank-row` | Next membership row, wrapping |
| `[b` | `jump-to-prev-bank-row` | Previous membership row, wrapping |
| `]B` | `jump-to-next-bank-day` | First membership row of the next occupied day, wrapping |
| `[B` | `jump-to-prev-bank-day` | First membership row of the previous occupied day, wrapping |
| `]]` / `[[` | existing repeat | Last family's lowercase |
| `]}` / `[{` | existing uppercase repeat | Last family's uppercase; for `b`, the day jump |

Record family `b` on the four bank commands, on a selector letter click,
and on a bank-badge waiting open ([A16](#requirement-adjustments)).
Repeats and internal advances never change the family — the walker-footers
A9 rule, extended.

No-origin (cursor not on a membership row, no live landing): `]b` and
`]B` land the oldest membership row; `[b` and `[B` land the newest.
From mid-day, `[B` leaves the day entirely and lands the first row of
the previous occupied day. There is no "first of *this* day" key; days
are short.

Counted `N]b` steps N rows with wrap. Counted `N]B` steps N occupied
days. A return-to-landed press consumes the count and ignores it, same
as `]s`.

Wrap toasts a single word `wrapped` in the existing notice chrome, then
the landing line.

### The `b` walker-footer panel

One host, four members. `walkerFooterWalkMode` today accepts `"s" | "w"
| "n" | null`; it grows `"b"`. `240-plugin-freshness-status.js` already
routes `n` then `w` then review; add `b` beside them. Unset family still
shows no panel. Mobile still hides the host.

Every panel fills the same slots. For `b`:

| Slot | Waiting membership | All-rows membership | Clear (zero rows) |
| --- | --- | --- | --- |
| Glyph + position | `🏦 WAITING 3/9` | `🏦 ALL 12/142` | `🏦 No bank rows` |
| Current group | `Wed Nov 12` (landed day) | same | — |
| Detail | `$12.40 Coffee` (⚑ suffix if flagged) | same | `import a QFX` |
| Hint | `Ctrl+Enter file` on a waiting landing; `]] next` off-row | `]] next` | — |
| Remaining groups | other occupied days, oldest→newest, current omitted | same | — |
| Meter | quiet `9 waiting` only while WAITING (the position already carries the fraction) | — | — |

Chrome tint is magenta, the default bank-card hue
(`bankCardRootHue` falls back to `"magenta"`). WAITING ink is the same
warning tone the bank badge already uses for waiting. Color never
carries the mode alone: the word `WAITING` or `ALL` is always present.

Shed order, end-first, matching the host choreography: remaining days
(`…`), then detail, then hint, then meter. The last thing to go is
`🏦 WAITING 3/9`. A selected `b` always paints, including the clear
state, matching walker-footers A5. Clear is "no month notes, or month
notes with no recognized rows," with the import hint. ALL with rows is
never clear.

Footer click runs the family's forward lowercase jump (`]]`). Day-group
chips, once visible, click as `]B` / `[B` toward that day.

### Who owns what

![Who owns the bank walk? Navigation Hotkeys owns keys, family, and landings. Ledger Tools owns the live queue and the b footer panel on the shared walker-footer host.](fig-ownership__grk.svg)

**Figure 2.** Cross-plugin split copies lanes: nav walks, ledger knows
the queue. Rendered size: 746 × 879 px; fit scale: 87.6%.

| Owner | Owns | Does not own |
| --- | --- | --- |
| **Navigation Hotkeys** | Commands, vimrc-facing ids, family `b`, `]]` / `]}` plans, `landOnWalkEntry`, return-to-landed, toasts, selector letter `b`, `api.walkMode` v4 (`current`/`select` accept `"b"`; `setAttention("b", …)`) | Scanning month notes, totaling cents, painting the panel |
| **Ledger Tools** | `api.bankWalk` v1 queue, live scan + editor overlay, `b` panel view-model, pushing `b` attention, badge-selects-`b` | Keymaps, family persistence, opening files (nav lands; ledger's `bankOpenMonthPathAtLine` stays the badge's opener) |

Legacy: nav absent or `walkMode` < v1 → today's ungated review footer,
no `b` panel. Ledger absent → nav commands still jump if they can read a
degraded scan, or they notice `Bank walk needs Ledger Tools`. Each
plugin ships and rolls back alone (walker-footers A11).

`api.bank` v2 stays the JSON fetch / `claimRowClose` namespace. Do not
overload it. `api.bankWalk` v1 is additive:

```text
bankWalk.version = 1
bankWalk.queue() -> {
  available: bool,
  membership: "waiting" | "all",
  entries: [{ path, line, date, cents, payee, acknowledged, flagged,
              ackId, key, rank, total, dayRank, dayTotal, text }],
  counts: { waiting, all, days },
}
```

Identity key: `ackId` (`^bank-<hex>`) when present, else
`path + "\0" + line + "\0" + text` so a typed row that later gains an
id does not strand the landing. Overlay: for each canonical month path,
prefer the unsaved editor buffer when that file is open.

### Landing, origin, toast

Reuse `landOnWalkEntry`. It already opens another month note, records a
`<C-o>` jump, and resolves the line against live buffer text. Bank
entries carry `path` / `line` / `text` in the same shape review and
lanes already land on.

Origin resolution copies lanes (`resolveLaneWalkOrigin`): cursor on a
membership row, else today's live landing, else no-origin ends. A
stale landing (row ticked out of WAITING, or text changed) falls through
to the next-by-tuple gap, then to wrap.

Return-to-landed (A11): lowercase `]b` / `[b` away from the row the
walk last landed on today first come back, toast
`Back to current bank row`, consume the count, and re-arm. Uppercase
day jumps never return. The current bank row dies when a new landing
replaces it, the row leaves the current membership, the plugin reloads,
or the day changes. Filing the landed waiting row via Ctrl+Enter ends
it, because the row is no longer in WAITING; the next `]b` steps, it
does not bounce onto a ticked line.

Toast, replacing the previous bank-walk notice rather than stacking
(lane-walk pattern in `543-lane-walk-notice.js`):

```text
WAITING  3 of 9
Wed Nov 12  ·  $12.40 Coffee
Ctrl+Enter file
```

Header wears magenta. ALL swaps the prefix and drops the Ctrl+Enter
hint. A day jump adds a quiet `→ Thu Nov 13` so uppercase feels like a
skip, not a stuck repeat.

### Category card coexistence

The card remains the writer. The walk remains the finder.

| Surface | Scope | Writes | Next |
| --- | --- | --- | --- |
| Category card Ctrl+Enter | Current month note | Tick + `[cat::]` | Next waiting in this file, wrap once, never another file |
| `]b` / `[b` | All `bank/*.md` | Never | Next membership row, possibly another file |
| `]B` / `[B` | All `bank/*.md` | Never | First row of next/prev occupied day |

v1 while the Category card modal is open: bank-walk commands no-op. The
card owns the keyboard (letters file categories; Ctrl+Enter accepts).
Do not dual-bind `]b` inside the card, and do not close the card. After
Esc, `]b` is live on whatever row the card left the cursor on.

Ctrl+Enter on a ticked row continues to only untick, with no card and no
jump — the acknowledge guide's existing contract.

### Selector, attention, and the `s` dot

`BRACKET_MODE_FAMILIES` gains a fourth entry:

```text
type: "b"
letter: "b"
name: "bank walk"
keys: "]b / [b"
tooltip: "]] / [[ repeat the bank walk (]b / [b)"
upperTooltip: "]} / [{ jump to the first row of the next / previous bank day (]B / [B)"
segmentAria: "Bank walk (]b / [b)"
```

`normalizeBracketRepeatType` accepts `"b"`. Empty-repeat copy becomes
`Nothing to repeat yet — press ]s, ]w, ]n, or ]b first`. The
no-uppercase notice stays `n`-specific.

`ensureBracketModeDom` currently reuses the tree only when
`segments.length === 3`. That check must track `BRACKET_MODE_FAMILIES.length`
or a cold rebuild on length mismatch will fight the sliding thumb. The
fragment is 911 lines, under the 1000-line cap; the change is small.

`setAttention` today refuses every type except `"s"`. v4 accepts `"s"`
and `"b"`. Ledger pushes `b` attention when `counts.waiting > 0` and
the family is not `b`, and clears it otherwise — including while `b` is
selected, so the letter does not wear a dot and a panel at once. The
`s` commitment dot is unchanged. Two dots can light together (`s` due
and bank waiting while you are in `w`); that is two independent
obligations, and each tooltip names its own.

The four-letter track is wider. Verify in real Obsidian that the thumb
still lands, especially next to Keep. If the track wraps on a narrow
bar, drop segment padding before dropping a letter.

### What not to build in v1

- A `bob bank walk` CLI, a JSON schema bump, or a per-keypress spawn.
- A manual WAITING/ALL toggle. Automatic membership is the request; a
  footer-label pin is a follow-up if ALL-while-waiting proves real.
- Auto-opening the Category card.
- Walking flagged-ticked rows as waiting.
- A "first of the current day" key.
- Default plugin hotkeys.
- A second status-bar item.
- Merging this walk into `]s` with a fake bank tier.
- Mobile walker-footer chrome (commands still work from the palette).

## Alternatives considered

**A bank-only walker outside the family.** Rejected. `]]` / `[[` would
not repeat it, the selector would lie, and the footer host would have
nothing to route on. The whole point of walker footers is that the bar
explains the family.

**Always-waiting, with a modifier for all.** Rejected for v1. Waiting
hits zero. The statement browse *is* the rest of the product. A sticky
modifier is a second mode to remember. Dual-mode with a labeled footer
is one mode that changes density.

**Always-all, waiting emphasized in the footer.** Rejected. The request
asked to traverse only review rows when they exist. Filing 40 waiting
rows through ALL would skip across already-ticked neighbors and feel
like a broken `]s`.

**Tie the walk to the Category card.** Rejected as the only walk. The
card is the right writer and the wrong finder. Keep both.

**Spawn `bob bank list`.** Rejected. Disk-only, slow, disagrees with the
unsaved tick the card just wrote. `api.bank` stays the totals pipe.

**Context-sensitive footer keyed on cursor-in-`bank/`.** Rejected by the
walker-footers research already: cursor inference is hidden state, and
a bank row is never also a review row, but the *family* is what `]]`
repeats. Gate on family.

**Reuse `[b` as Obsidian buffer-previous when no bank rows exist.**
Rejected. Empty bank should clear-state and stay put, like `Review
clear`. Falling through to buffers would make one key mean two things.

Would I take a different approach overall? **I would still build family
`b`, with the adjustments above.** I would not wait for SimpleFIN, a
weekly-only scope, or a new CLI. The QFX import already writes the
rows. The missing instrument is the walk.

## Architecture sketch

New fragments, because existing ones are either at the cap or owned by
another walk. Proposed numbers check the tree as of this research:
ledger has `071-lane-walk-model.js` and no `072`; footer host is
`122`–`124` with no `125`; nav `545-plugin-review-journal.js` already
exists, so bank walk is `548`.

| Fragment | Plugin | Role |
| --- | --- | --- |
| `072-bank-walk-model.js` | ledger | Pure membership, ordering, day occupancy, overlay merge |
| `125-bank-walker-footer.js` | ledger | Pure `b` view-model, shed list, attention payload |
| `548-plugin-bank-walk.js` | nav | Commands, origin, return-to-landed, toast, `landOnWalkEntry` |

Edits, small on purpose:

- nav `546-plugin-bracket-repeat.js`: `normalizeBracketRepeatType`,
  `BRACKET_REPEAT_PLANS.b`, `BRACKET_REPEAT_UPPERCASE_PLANS.b`, empty
  notice copy.
- nav `547-bracket-mode-indicator.js`: fourth family, length-agnostic
  DOM reuse, `b` attention in the view key, hint copy.
- nav `482-walk-mode-nav-api.js`: version 4, `select("b")`,
  `setAttention("b", { tier, label })`.
- ledger `122-walker-footer-host.js`: `walkerFooterWalkMode` accepts
  `"b"`.
- ledger `240-plugin-freshness-status.js`: route `b` to the new panel;
  push `b` attention from the queue counts.
- ledger `241na-plugin-bank-badge.js`: on a waiting target open, call
  `walkMode.select("b")` when v4 is present.
- vault `obsidian_vimrc.md`: four `nnoremap`s and a comment that `]]` /
  `[[` now also repeat bank.
- docs: Navigation Hotkeys command table and facts blurb; acknowledge
  guide step 2 grows one sentence (`]b` finds waiting across months;
  Ctrl+Enter still files); `docs/bank.md` one sentence under the ritual.
- glossary *Walker Footer*: four members (`s` / `w` / `n` / `b`); *Bank
  Row*: `]b` / `[b` traverse waiting, else all. Decision record
  `bank-walk-is-a-bracket-family` once the plan is accepted.

Line-budget notes: `547` is 911 lines (cap 1000) — keep the family
table data-driven and do not grow painters here. `122` is 192 lines.
Lane-walk nav plugin is 239 lines plus a 696-line pure model; bank can
be smaller (no work-log chip, no lane caps).

### Planner contract (pure, unit-tested)

Mirror `planLaneWalkJump` / `planLaneWalkLaneJump`:

```text
planBankWalkJump(entries, { direction, cursor, anchor, repeat })
  -> { kind: "empty" }
   | { kind: "jump", entry, rank, total, wrapped, origin, membership }

planBankWalkDayJump(entries, { direction, cursor, anchor, repeat })
  -> { kind: "empty" }
   | { kind: "jump", entry, rank, total, wrapped, origin, membership,
        fromDate, toDate, dayJump: true }
```

Occupied days = unique `entry.date` in the *current* membership array,
sorted oldest-first. Day jump lands `findIndex(e => e.date === target)`,
the first row of that day. Wrap around the day ring.

Empty queue: notice `No bank rows — run bob bank import` in WAITING's
absence-of-files sense, or `Bank walk clear` if that distinction helps;
one string is enough if the footer already shows the import hint.

### Tests

New `scripts/test-navigation-bank-walk.cjs` and
`scripts/test-ledger-tools-bank-walk-footer.cjs`, plus extensions to
`test-navigation-bracket-mode-indicator.cjs`:

- Membership: one waiting row anywhere → waiting-only queue; tick it in
  the overlay → ALL on the next plan.
- Day jump skips a day that has rows in ALL but none in WAITING.
- Cross-month: last waiting in `bank/2026-11.md` then first in
  `bank/2026-12.md`.
- No-origin ends; wrap; counted N; uppercase ignores return-to-landed.
- Editor overlay beats disk for the same path.
- Identity prefers `ackId`; typed rows use path+line+text.
- Footer WAITING / ALL / clear; shed drops remaining days first.
- Selector has four segments; reuse check survives a fourth family;
  `setAttention("b", …)` paints the dot only off-family.
- `]]` after `]b` is a row step; `]}` after `]b` is a day jump.
- `n` still has no uppercase plan.
- Category-card `bankCategoryNextWaiting` still never leaves the file
  (existing tests stay green).

### Beauty notes

Beauty here is the same as the other walks: one chrome, honest labels,
seasonal attention, magenta that already means bank.

- The word `WAITING` is the star of the panel, in warning ink, while
  the fraction `3/9` is the position. Do not replace the word with a
  yellow pip.
- Amounts use `bankFormatCents` so `$12.40` and `+$2,500.00` match the
  badge, the card, and `bob bank list`.
- Day groups use the heading's weekday+date (`Wed Nov 12`), the same
  text the month note already shows — do not invent `2026-11-12` in the
  bar.
- The toast and the footer say the same rank/total. Disagreement is a
  bug.
- `🏦` is the bank hub's own H1 glyph. Using it once in the bar is a
  callback, not a new metaphor.

## Recommended solution

1. **Fourth bracket family `b`**, persisted with `s` / `w` / `n`,
   selected by `]b` / `[b` / `]B` / `[B` or a letter click, repeated by
   `]]` / `[[` / `]}` / `[{`.
2. **Automatic dual-mode queue** from a live `bank/*.md` scan plus open
   editors: waiting-only when any `[ ]` exists, otherwise every
   recognized row, oldest first. Footer and toast label `WAITING` or
   `ALL`.
3. **Day jump** is first membership row of the previous / next occupied
   day, skipping empty, wrapping, from mid-day.
4. **Fourth walker-footer panel** on the existing host: magenta 🏦,
   position, day, amount+payee, `Ctrl+Enter file` hint, remaining days
   shed end-first, calm clear state.
5. **Quiet `b` dot** while waiting > 0 off-family. Keep the `s`
   commitment dot. Reject a `w` pip, still.
6. **Nav lands, ledger queues.** `api.walkMode` v4 + `api.bankWalk` v1.
   Reuse `landOnWalkEntry`. Lowercase return-to-landed. Counted N.
7. **Walk never writes.** Category card stays the same-file filing
   ritual. v1 no-ops while the card is open. Badge waiting-open selects
   `b`.
8. **No default hotkeys, no new CLI.** Map the four keys in the vault
   vimrc. Document the unimpaired `[b` collision.
9. **Amend *Walker Footer* and *Bank Row*;** add decision
   `bank-walk-is-a-bracket-family` when the plan is accepted. Update the
   Navigation Hotkeys reference and one sentence of the acknowledge
   guide.

Ship in that order: pure model and tests, `api.bankWalk`, nav commands
and family, footer panel and attention, selector fourth letter, vimrc,
docs and memory. Each slice is demoable. The first slice that feels
like the product is nav commands over a real queue, even before the
panel exists — but the panel should land in the same change set so `]]`
and the bar never disagree.

That is the whole feature: four keys Bryan can type with his eyes on a
payee, a footer that says whether he is filing or browsing, and a
selector letter that makes `]]` keep doing the same thing until he
picks another walk.
