# `<Ctrl+W>N` — jump to the Nth tab in the active split — research (`mus`)

## TL;DR

Yes, build it. A `<Ctrl+W>1`…`<9>` jump to the Nth tab of the **active
split** fills the one gap the shipped window prefix left behind: `h`/`l`
move *across* splits, but nothing in the prefix layer moves *within* a
split, so a six-tab split still forces sequential `Ctrl+Tab` or the
mouse. The execution primitive is the safest in the whole prefix family
(`setActiveLeaf` on an already-present leaf — no reparenting, no collapse
races, nothing to roll back), and the hint primitive is proven prior art:
the community Tab Numbers plugin already badges per-split tab numbers in
exactly the slot we need. Recommended v1: **1-indexed left-to-right
numbering scoped to the active split, badges rendered on the tab bar only
while the prefix is armed, one compact TABS group added to the existing
card, `9` means "last tab" when the split holds more than nine, `0` stays
unmapped.** Two adjustments to the request as written (transient badges,
not persistent; `9`-is-last) and one code-level catch (the current suffix
normalizer has no `DigitN`/`NumpadN` fallback, so `Ctrl+W Ctrl+3` would
miss without a fix). Details and the full critique below.

## 1. Context: what the m0 epic already shipped

The `bob-cli-m0` epic (Ctrl+W window prefix for Obsidian vertical splits,
all six phases closed) added a capture-phase `Ctrl+W` prefix to the
`bob-navigation-hotkeys` plugin in the `bob-plugins` linked repo:

- `h`/`l` focus the neighbouring split (directional, never wraps), `w` /
  second `Ctrl+W` cycles splits, `H`/`L` move the active *tab* across
  splits (join / create / collapse), `v` duplicates into a new right
  split, `Esc`/`Ctrl+[`/`q` cancel.
- Digits were explicitly **reserved for later**; today a digit suffix is
  consumed as unmapped ("`‹k›` isn't a window key") and the prefix stays
  armed. Adding `1`–`9` therefore changes no existing chord.
- The plan's out-of-scope list names "numbered splits" as designed-later,
  so this feature is the scheduled sequel, not scope creep.

Implementation landmarks (all under
`plugins/bob-navigation-hotkeys/src/`, fragments ≤1000 lines, built to
`main.js`, plugin version 2.83.1):

- `266-window-prefix-model.js` — pure snapshot/planner/key table
  (`WINDOW_PREFIX_KEY_TABLE`: `h l w H L v`), suffix normalizer
  `normalizeWindowPrefixKeydown`, arming verdict, view model.
- `267-window-prefix-actions.js` — live snapshot via
  `workspace.iterateRootLeaves`, lossless executor, upgrade canary.
- `473-window-hint-view.js` — pure painter (ring + card + minimap).
- `687-plugin-window-prefix.js` — prefix state machine
  (`idle → armed → carded → running → idle`, single-exit `disarm()`).
- `688-plugin-window-prefix-commands.js` — palette verbs + persistent
  focused-split underline.
- `styles.css` — `bob-wp-*` rules, theme-variable colors, key caps reuse
  `.bob-key-card-key`.

## 2. The gap this fills

Within one split, the prefix layer currently offers no tab navigation at
all. The alternatives Bryan has today are all outside the layer: native
`Ctrl+Tab` / `Ctrl+Shift+Tab` (sequential — fine for two tabs, tedious
for six), the mouse, or leaving the prefix and using native
`Ctrl/Cmd+1`…`9`. A direct `N` jump is the standard answer everywhere
tabs exist (browsers, VS Code, Obsidian native itself), and it composes
with the prefix the way Vim users expect: `Ctrl+W` then one more key,
hands never leaving home row. `h`/`l` answer "which column";
`N` answers "which tab". Both are needed.

## 3. Prior art and API facts

**Native Obsidian.** `Ctrl/Cmd+1`…`9` are "Go to tab" commands and
`Ctrl+Tab` / `Ctrl+Shift+Tab` step sequentially (hotkey cheat sheets and
forum reports agree). The Tab Numbers source comments that native `9`
always goes to the *last* tab, and its README states each split keeps its
own tab sequence — i.e. native numbering is already per-split, matching
the request's "same vertical window" scoping.

**Tab Numbers plugin** (`j4ckofalltrades/obsidian-tab-numbers`, read as an
external checkout) is the closest prior art and largely de-risks the hint
half of this feature. How it works:

- Resolves each leaf's header through the undocumented but widely used
  `leaf.tabHeaderEl` (fallback: `view.containerEl` → closest
  `.workspace-leaf` → `data-leaf-id` lookup). Pinned Tab Bar and New Tab
  Here rely on the same internals, so this is community-stable surface.
- Orders tabs by **DOM order** of `.workspace-tab-header` elements inside
  their parent, not by `WorkspaceTabs.children` order — the DOM is the
  visual truth after drags.
- Numbers only the **active split** (found via `closest('.workspace-tabs')`
  from the active leaf's header), badges `1`–`8`, badge node inserted
  **before the close button**, hidden by default and shown while `Ctrl`
  (non-Mac) / `Cmd` (Mac) is held. Refresh on `layout-change` plus
  `active-leaf-change`, debounced 50 ms, with a `Map` for cleanup.
- Styling is one small circle (18 px, bold 10 px digit). Functional, but
  its fixed purple default is exactly the kind of theming this project
  would never ship — ours must use theme variables like the `bob-wp-*`
  rules do.

**Public API limits.** `obsidian.d.ts` exposes `WorkspaceTabs` only as an
opaque `WorkspaceParent` — no header accessors, no tab-order API, no
select-tab-by-index. So badge rendering unavoidably touches the same
undocumented DOM surface Tab Numbers uses, while *jumping* stays 100% on
public API (`workspace.setActiveLeaf(leaf, { focus: true })`, plus
`loadIfDeferred` for background leaves — the same call the existing
focus actions already make).

**Vim conventions.** Vim itself has no `<C-w>{number}` tab jump
(`gt`/`gT`/`{count}gt` cover tabs; `<C-w>` is windows). Browsers define
the convention that matters here: `Ctrl+1`…`8` positional, `Ctrl+9` last.
Obsidian native follows it. Following it again under `Ctrl+W` is the
least surprising choice.

## 4. Critique: is this a good idea?

Yes — with the adjustments in §5. The strengths: it completes the
prefix layer (across-split *and* within-split navigation under one
leader), it reuses the layer's hardest-won machinery (arming verdict,
Scope ownership, two-tier hint, disarm paths) for near-zero marginal
complexity, and its executor cannot corrupt layout because it never
mutates layout. The main honest objection is **duplication**: on macOS,
`Cmd+1`…`9` already jumps within the active split. Three reasons the
duplication is justified rather than gratuitous: (a) layer consistency —
a Vim user who just armed `Ctrl+W` should not have to disarm, chord a
different modifier, and lose the hint to do the most common next thing;
(b) discoverability — native digits have no hints without a third-party
plugin, while ours are self-announcing; (c) Linux ownership — while the
prefix is armed Bob owns the keyboard, so passing digits through to
native would break one-action-per-arm, blocked reasons, and
announcements. Implementing the jump directly (one `setActiveLeaf`) is
about five lines and keeps every prefix invariant intact.

Approaches considered and rejected:

- **MRU / Harpoon-style numbering.** Stable positions beat recency for a
  visual badge: the digit next to the tab must equal the key, always.
  Recency belongs in Quick Switcher, not on the tab bar.
- **Multi-digit entry for 10+ tabs.** Requires an inter-key timeout or an
  Enter terminator inside a layer whose contract is one-action-per-arm.
  Splits with 10+ tabs are rare; tabs past the ninth stay reachable by
  click and native keys. Single-digit only.
- **Global (cross-split) numbering.** Contradicts the request and every
  precedent (native, Tab Numbers, browsers number per window/group).
  Per-split numbering also keeps every digit meaningful no matter how
  many splits exist.
- **Card-only mapping, no tab-bar badges.** Cheaper (pure painter, no DOM
  injection) but fails at the exact moment it matters: eyes on the tab
  bar, finger on the key. It also fails screen-zoom and screen-reader
  users less gracefully than a card list, but the badge is the primary
  mapping and the card is its accessible backup — see §6.
- **`0` as tab 10 / tab 1.** `0` is line-start in Vim and dead in native
  ("CTRL+0 did not" work, per forum). Leave it unmapped.

## 5. Adjustments to the requirements (called out)

**A1 — Badges are transient, visible only while the prefix is armed.**
The request says "a hint rendered next to each file's name in the tab
title bar", which could read as persistent. Persistent badges are
clutter 99% of the time, fight every theme's tab-bar spacing, collide
with Tab Numbers-style plugins, and need a live tracker. Transient
badges (painted at arm time from a fresh snapshot, removed on every
`disarm()` path) minimize DOM exposure to a ~second-long window the card
already makes visible. The mapping is still "rendered next to each
file's name" at the only moment it is needed.

**A2 — `9` means "last tab" when the split holds more than nine tabs;
`1`–`8` are positional.** The request says "`N`th tab" plainly. Pure
positioning strands tabs 10+ with no key and wastes `9`'s universal
"last" meaning. Mirroring native/browser behavior costs one sentence in
the card footer and surprises nobody.

**A3 — Digits count pinned tabs in position order.** Pinned tabs occupy
the first positions and native `Ctrl+N` counts positions, not
"unpinned offsets". Skipping them would make badge `3` jump to the
fourth visual tab — a lie next to the very tab it labels. Pinned badges
get a compact treatment (§6) since pinned headers are narrow, but the
numbers stay honest. (Spike must confirm native counts pinned; if it
does not, revisit.)

**A4 — No palette commands for digits.** The existing pattern registers
one palette command per key, but nine `window-go-to-tab-N` commands is
palette noise for an interface designed around the prefix. Discovery
runs through the card and the `window-keys` command that already exists.
If users demand it later, add them then.

**A5 — `0`, and any digit past the tab count, is a blocked no-op that
keeps the prefix armed.** Consistent with the existing blocked-key
contract (nudge + reason, stay armed), not a cancel. Reasons: "only N
tabs here", "`0` isn't a tab key".

## 6. Recommended design

**Numbering.** Active split only; visual left-to-right DOM-header order;
1-indexed; `1`–`8` positional; `9` positional when ≤9 tabs, last-tab
otherwise; `0` unmapped. One action per arm, then `disarm()` like every
other key. Held-Ctrl digits (`Ctrl+W Ctrl+3`) work, matching the rest of
the table.

**Key handling fix (required).** `normalizeWindowPrefixKeydown` in
`266-window-prefix-model.js` currently recovers letters from `event.code`
only for `KeyX`, plus `BracketLeft`. Under held Ctrl, `event.key` for a
digit can arrive as a control character, so the normalizer needs a
`DigitN`/`NumpadN` → `N` fallback or `Ctrl+W Ctrl+3` silently misses. This
is the one non-obvious implementation catch found in review. Shift-digit
needs no special case (`Shift+1` arrives as `!`, naturally unmapped), and
Meta/Alt/repeat/IME handling stays exactly as the other suffixes.

**Planner.** Extend the pure model, not the executor: snapshot gains the
active split's ordered leaf ids in DOM-header order (spike confirms the
`tabHeaderEl` + DOM-order technique against drags, overflow scroll, and
deferred leaves); `planWindowPrefixKey` gains `1`–`9` entries returning
`{ action: 'go-to-tab', targetLeafId, index }` or a blocked plan with the
A5 reasons; the existing canary (`focus` capability) gates it, since
jumping *is* focusing. No new capability flag, no layout mutation, no
rollback path — the invariant check is "active leaf is the target".

**Executor.** `setActiveLeaf(target, { focus: true })` after
`loadIfDeferred` when `isDeferred`, reusing the exact focus helper in
`267-window-prefix-actions.js`. Records no `Ctrl+O` jump (window/tab
motions never do, per A9 of the consolidated research). Receipt: none
beyond the existing focus pulse — the screen already changed.

**Hint — two halves, matching the layer's two-tier philosophy.**

- *Tab-bar badges (primary mapping).* At arm time, paint one badge per
  numbered tab in the active split only, inserted before each header's
  close button (the Tab Numbers slot — proven not to disturb layout).
  Compact key-cap styling: 16–18 px, interface-font digit at ~10–11 px
  semibold monospace, accent-tinted background
  (`color-mix(--interactive-accent 18%, transparent)` text/border in
  `--text-normal`-ish tones — full spec belongs to the painter phase,
  but fixed colors like Tab Numbers' purple are out). Pinned tabs get
  the same badge at reduced padding. `aria-hidden="true"` (decorative;
  the card announces). Removed synchronously on every `disarm()` path;
  a `layout-change` or `active-leaf-change` the prefix did not cause
  already cancels the prefix, so no live re-tracking is needed.
- *Card TABS group (accessible backup + discovery).* Add one group to
  `buildWindowPrefixViewModel` listing the active split's tabs as rows:
  key cap `N`, title (`leaf.getDisplayText()`, ellipsized), unavailable
  rows dimmed past the tab count / for `0`, `9`-is-last annotated in the
  footer ("`1`–`9` jump to tabs in this split · `9` is last past nine").
  Cap the list at nine rows with an overflow counter, mirroring the
  minimap's `+N` convention. This keeps keyboard-only and screen-reader
  users first-class and preserves the layer's rule that every key owns a
  card row with a preview/reason.

**Beauty notes.** Badges must survive light/dark, Minimal-style themes,
and narrow pinned headers; verify against the existing 12-state preview
harness with three new states (badged split light/dark, pinned-heavy
split, 9+ tab overflow). The ring does not move on a tab jump (same
split) — instead pulse the *badge* of the destination tab once, reusing
the 220 ms yank-flash timing, then disarm and remove all badges.

**Coexistence.** If Bryan also runs Tab Numbers, both plugins briefly
badge the same slot while armed. Benign (distinct classes, ours removed
on disarm), but use a `bob-wp-tab-badge` class and never touch foreign
badge nodes.

## 7. Reliability and edge cases

- **Ordering truth:** DOM-header order at arm time. Spike must confirm it
  survives tab drags, overflow scrolling (hidden tabs still numbered —
  fine, the key still works), and window resize.
- **Deferred leaves:** `loadIfDeferred` before focus; empty/placeholder
  tabs are countable leaves like any other.
- **Non-file views:** PDF, image, canvas, graph, empty tabs all jump the
  same way — the jump is leaf-agnostic.
- **Single-tab split:** digits `2`–`9` blocked ("only 1 tab here"); `1`
  refocuses (harmless no-op that still disarms — or blocked as
  "already there"? recommend blocked-with-reason to teach; spike-phase
  call, keep consistent with how `w` behaves solo).
- **Leak safety:** badges are DOM the model never sees, so the painter
  phase must add a `destroyBadges()` covered by the existing ElementStub
  tests plus a "disarm removes every badge" assertion on each exit path.
- **Upgrade canary:** reuse the focus canary; no new internals probed.
  (Badge painting reads `tabHeaderEl`/DOM queries that may change shape
  across Obsidian versions — treat a missing header as "skip that badge",
  never as fatal.)
- **Linux:** unaffected — digits were never bound to Close tab; the
  `linux_ctrl_w = keep` decision stands as is.

## 8. Test plan (follows the m0 phase pattern)

- **Model unit tests** (`test:unit`): index mapping for 1/2/6/9-tab
  splits, 12-tab split (`9` → twelfth), out-of-range blocked reasons,
  `0` unmapped, pinned-inclusive positions, held-Ctrl digit
  normalization (`Digit3` with `ctrlKey`, `Numpad9`), parity — every new
  row's `plan` deep-equals `planWindowPrefixKey` output.
- **Painter tests** (ElementStub): badge insert position (before close
  button), text/numbering, `aria-hidden`, theme-variable-only styling
  (assert no hardcoded colors), idempotent repaint, full cleanup on
  `hide()`/`destroy()`, card TABS rows/reasons/overflow counter.
- **Real-Obsidian e2e on athena** (extend the existing harness, same
  scratch-vault/CDP rules): arm, screenshot badges, send `3`, assert
  active leaf + focus + no layout mutation + badges gone; pinned split;
  deferred background tab; 10-tab split (`9` → last); light + dark +
  reduced-motion. Screenshots reviewed by eye — the "beautiful" gate.

## 9. Effort and rollout

Small — roughly one phase-sized change, no spike-scale unknowns except
the half-day DOM-order confirmation, which rides the existing e2e
harness. Touch only: `266-window-prefix-model.js` (key table,
normalizer, planner, view model), `267-window-prefix-actions.js` (focus
by planned leaf — likely zero lines, reuse), `473-window-hint-view.js`
(badge painter + TABS group), `687-plugin-window-prefix.js` (paint on
arm, clean on disarm), `688-plugin-window-prefix-commands.js` (nothing —
per A4), `styles.css` (`bob-wp-tab-badge`), tests + previews. No
manifest bump unless the painter phase judges otherwise; no `bob.md`
edits; sync via `bob plugins sync` per `AGENTS.md`. This is also
independently shippable: if badges prove ugly in previews, the planner +
card rows alone are a coherent smaller release.

## 10. Open questions for the implementing spike

1. Confirm native `Cmd/Ctrl+N` counts pinned tabs (decides A3 finally).
2. Confirm DOM-header order equals visual order with overflow scroll and
   after drags in 1.15.x.
3. Confirm `DigitN` control-character behavior under held Ctrl on macOS
   and Linux (decides the exact normalizer fallback).
4. Single-tab `1`: no-op refocus or blocked-with-reason?
