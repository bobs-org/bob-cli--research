# Screenshot region selector: click-drag to draw, modifier-drag to move

Research report — screenshot utility triggered by `<ctrl+shift+opt+s>`.
Researcher: mus (`__mus`).

## TL;DR

The plan is directionally right but the modifier is wrong and the
requirement as stated is under-specified. Implement **draw-first**:
plain click-drag anywhere draws a new rectangle (inside or outside the
preloaded box); **Space-drag or Cmd-drag moves** the existing box;
corner handles still resize; everything else (Enter/Esc, last-region
memory, `macscrot` upload pipeline) stays unchanged.

Do not implement Cmd-only move. Accept both Space and Cmd as move
modifiers, with Space primary in the hint text, because Space matches
native macOS `Cmd+Shift+4` muscle memory and Cmd-alone is harder to
discover, harder to hold during a trackpad drag, and easier to confuse
with window-drag conventions. The code change is small (one file,
`home/dot_hammerspoon/screenshot_region.lua`), low-risk, and fully
covered by the existing `busted` + bash harness pattern — but the tap
must also listen to `flagsChanged`, and the move-vs-draw decision must
be snapshotted at `leftMouseDown`, not re-evaluated mid-drag.

## 1. What exists today

### 1.1 Trigger and pipeline

| Piece | Location (chezmoi checkout) | Role |
|---|---|---|
| Hotkey | `home/dot_hammerspoon/init.lua:42` — `hs.hotkey.bind({"ctrl","alt","shift"}, "s", ...)` | `<ctrl+shift+opt+s>` (`opt` == `alt` in Hammerspoon). Calls `ScreenshotRegion.pick(runMacscrot)`. |
| Region picker | `home/dot_hammerspoon/screenshot_region.lua` (501 lines, added in `fde58338` "remember screenshot capture region", 2026-06-28; formatted in `4375716e`) | Full-screen `hs.canvas` overlay at `screenSaver` level with dim + blue selection rect + 4 corner handles + size label + hint. Persists confirmed rect in `hs.settings` under `macscrotLastRegion`, preloads it next time, clamps to the containing screen. |
| Capture/upload | `home/bin/executable_macscrot` | Takes optional `x,y,w,h`; runs `screencapture -R <region>` or falls back to `screencapture -i`; uploads in parallel to `apollo`/`athena` `~/tmp/screenshots/`, copies path to clipboard, posts notification. |
| Fetch macro | `home/bin/executable_sshot_fetch`, `home/sase/macros/sshot.yml` | Later retrieval of nth-newest screenshot for SASE prompts. |
| Tests | `tests/hammerspoon/init_spec.lua` (mocks `screenshot_region.pick`, asserts hotkey wiring only), `tests/bash/macscrot_test.sh` (stubbed `screencapture`/`ssh`/`scp`/`pbcopy`/`osascript`) | No unit tests for `screenshot_region.lua` drag logic itself. |

### 1.2 Current drag dispatch (the source of the complaint)

`M.pick` installs one `hs.eventtap` watching
`leftMouseDown | leftMouseDragged | leftMouseUp | keyDown`
(`screenshot_region.lua:398-405`). On `leftMouseDown`:

1. Click on a corner handle (`handleAt`, 20px grab box) → `mode="resize"`.
2. Else click strictly inside the preloaded rect (`pointInRect`) → `mode="move"` (translate by mouse delta, clamped to screen).
3. Else click outside → `mode="new"` with `anchor=point`; drag calls `updateNewRegion` (`normalizedRect` + `MIN_SIZE=16` clamp); mouse-up with `<3px` movement cancels (`finish(false)`).

Enter confirms, Esc or click-without-drag outside cancels, click on another
screen cancels (`frameContainsPoint` check). Key handling swallows all
`keyDown` (`return true`).

So the user's description is half-right: **outside-drag already draws a
new box**. The friction is that the picker preloads the *last* rect
(`loadInitialRegion`, 60%-of-screen default on first run), so most
invocations start with the cursor *inside* a large stale box, where drag
means move, and the only way to redefine the rect is to hunt 10px corner
handles. For the stated job — "a very specific rectangular space" that
rarely equals the last rect — that is exactly backwards.

## 2. Critique of the proposed plan

### 2.1 What the plan gets right

- **Draw-first matches the dominant job.** Native `screencapture -i`,
  Shottr, Cleanshot, and every drag-to-select idiom teach
  press-drag-release = define rect. Users invoking a screenshot key
  already have a target in mind; asking them to first discard/move a
  stale box is a mode error.
- **Keeps move available.** Dropping move entirely would regress the
  legitimate "nudge last week's dialog box 20px" flow that motivated
  `fde58338`. A modifier-qualified move preserves it.
- **Small blast radius.** Only the `leftMouseDown` branch and the hint
  string change; `macscrot`, settings persistence, clamping, and
  confirm/cancel semantics are untouched.

### 2.2 Problems with the plan as stated

1. **Cmd is the wrong modifier.** Native macOS selection uses **Space
   to move** (hold Space mid-drag, selection follows cursor),
   **Shift to lock an axis, Option to resize around center**
   (verified against current Apple-documented `Shift+Cmd+4` behavior).
   Every Mac user who has ever repositioned a screenshot already knows
   Space. Cmd-drag means nothing in screenshot context, is undiscoverable
   without reading the hint, and is ergonomically worse: on a trackpad,
   holding Cmd with the left hand while dragging with the right is
   doable but stiffer than thumb-on-Space; on a one-handed laptop drag
   it is actively awkward.
2. **"Still need click-and-drag the area" is ambiguous.** Does a plain
   click (no drag) inside the box move nothing and cancel? Confirm?
   Keep the box? The current code cancels a no-move `new` click but
   commits nothing on a no-move `move` click (drag=nil, stays open).
   In draw-first mode the equivalent edge — click inside, release
   without moving — must be defined or users will lose captures to
   accidental cancels.
3. **No mid-drag correction.** Native flow lets you start drawing,
   realize the anchor is wrong, hold Space, reposition, release Space,
   keep drawing — all without lifting the button. A snapshot-at-mousedown
   Cmd check cannot do that. If you only implement the proposal
   literally, you fix the common case but stay strictly less forgiving
   than the tool users compare you to.
4. **Handle redundancy is not addressed.** If any-drag draws, corner
   handles become a secondary affordance (fine-motor resize, 1px
   tweaks). The plan should say so explicitly and keep them — removing
   them would regress keyboard-free pixel tweaks — but the hint must
   stop implying handles are the primary path.
5. **Multi-monitor and cross-screen drag are orthogonal but will be
   blamed on this change.** The overlay canvas is created once for the
   starting screen (`hs.canvas.new(screenFrame)`) and every point is
   clamped to that screen (`clampRegionToFrame`, `updateNewRegion`).
   Draw-anywhere does not let users span monitors. Call that out so it
   is not filed as a regression.
6. **Modifier-only discoverability.** A hint like "Cmd-drag to move" is
   easy to miss on a dimmed screen. Without a visual cue (cursor change
   or live hint swap on `flagsChanged`) most users will conclude move
   was deleted.

Verdict: **good instinct, adjust the modifier and the edge semantics.**

## 3. Technical feasibility

### 3.1 Reading Cmd (or Space) in the existing tap

Hammerspoon exposes modifiers per-event via
`event:getFlags()` → `{cmd=bool, alt=..., shift=..., ctrl=..., fn=...}`
with `contain`/`containExactly` helpers, and via the global
`hs.eventtap.checkKeyboardModifiers()`. Bare-modifier presses arrive as
`flagsChanged`, *not* `keyDown`, so the current tap (which does not
listen to `flagsChanged`) will not see Cmd/Space presses that occur
*after* mousedown unless that type is added. Two integration points:

- **At `leftMouseDown`**: `local flags = event:getFlags()` then
  `flags.cmd` / `flags.space`? Note: Space is **not** a modifier flag —
  it is a regular key (`keyDown`, keycode `hs.keycodes.map.space`).
  This is the critical asymmetry the plan misses: **Cmd is readable
  from mouse-event flags; Space is not.** Space state must be tracked
  separately (a boolean set/cleared by `keyDown`/`keyUp` for the Space
  keycode, or polled). Cmd is therefore *easier* to implement
  (one-line flags check, no extra state), Space is *better* UX but
  needs ~10 extra lines plus a `keyUp` listener.
- **During drag**: to support native-style hold-Space-to-move-mid-draw,
  also watch `flagsChanged` (for Cmd) and Space `keyDown`/`keyUp` and
  either (a) switch `drag.mode` live, or (b) simpler and recommended:
  snapshot at mousedown, document that the modifier must be held
  *before* pressing. Live-switching invites anchor-loss bugs (where
  does the "new" anchor go when you release Space mid-move?).

Recommended v1: **snapshot at mousedown, support both modifiers**:

```lua
-- add keyUp + flagsChanged to the tap's watched types
local eventTypes = hs.eventtap.event.types
tap = hs.eventtap.new({
  eventTypes.leftMouseDown,
  eventTypes.leftMouseDragged,
  eventTypes.leftMouseUp,
  eventTypes.keyDown,
  eventTypes.keyUp,        -- track Space release
  eventTypes.flagsChanged, -- keep Cmd state fresh; return false (don't swallow)
}, function(event) ... end)
```

```lua
-- mousedown branch (replaces handle/inside/outside priority)
local flags = event:getFlags() or {}
local moveHeld = flags.cmd or spaceHeld  -- spaceHeld from keyDown/keyUp tracker
  -- or: hs.eventtap.checkKeyboardModifiers().cmd as fallback
local handle = handleAt(point, region)
if handle then
  drag = { mode = "resize", ... }              -- handles win either way
elseif moveHeld and pointInRect(point, region) then
  drag = { mode = "move", ... }                -- explicit move
else
  drag = { mode = "new", anchor = point, ... } -- default: draw
end
```

`flagsChanged` events themselves should **not** be swallowed (`return
false`) or the user's Cmd keystrokes leak-state into other apps; mouse
and `keyDown`/`keyUp`-for-Space handling keeps current swallow behavior
(`return true`) so the overlay stays modal. Space `keyDown` while the
selector is open currently falls into the generic `return true` swallow
— add an explicit branch that sets `spaceHeld=true` and returns true
without confirming (Space is not Enter/Escape).

### 3.2 Effort and risk

- ~20–30 lines in one file, no `macscrot`/settings/pipeline changes.
- No new accessibility permissions: the eventtap already runs; adding
  watched types to an existing tap needs no re-consent.
- No conflict with the `<ctrl+shift+opt+s>` trigger or the `Cmd+Alt+V`
  paste binding in the same `init.lua`; the tap swallows mouse/keys
  only while the overlay is up and at `screenSaver` level.
- Main regression risks: (1) users who learned inside-drag=moves will
  draw over their box once — mitigated by hint + Esc-then-retry cost of
  ~2s; (2) `spaceHeld` stuck-true if Space `keyUp` is missed (e.g.
  selector cancelled while held) — mitigate by clearing on `finish` and
  on `flagsChanged`; (3) click-without-drag inside now cancels (if you
  map it to `new`+no-move→cancel) where it previously no-op'd — define
  explicitly (see §5).

## 4. Alternatives considered

| Option | Behavior | Pros | Cons | Effort |
|---|---|---|---|---|
| A. Proposal as stated (plain draws, Cmd moves) | Any-drag draws; Cmd+inside-drag moves | Tiny diff; fixes main pain | Cmd undiscoverable, un-native, awkward one-handed; Space users keep failing | ~10 lines |
| B. Native mirror (recommended core) | Any-drag draws; **Space and Cmd** move; handles resize; optional Shift-lock / Option-center later | Matches `Shift+Cmd+4` muscle memory; Cmd kept as alias for discoverability via hint | Space needs keyUp tracking; slightly more code than A | ~30 lines |
| C. Status quo + Space-move only | Keep inside=move, add Space-move-mid-draw | Zero relearning | Does not fix stale-box-first pain; handles still primary | ~20 lines |
| D. Drop memory, always crosshair | No preloaded box; every invocation starts empty like `screencapture -i` | Simplest mental model; no move needed | Loses the `fde58338` repeat-region win; every repeated capture redrawn | Small, but product regression |
| E. Two-click corner mode | First click sets anchor corner, second click sets opposite corner | Precise for "very specific rect" without drag-slip | Slow; breaks drag habit; accessibility-hostile | Medium |
| F. Replace with Shottr/Cleanshot | External app owns selection | Rich editing, scrolling capture | New dependency, new sync/upload glue, vault-adjacent data leaves `macscrot` pipeline; overkill for a 30-line fix | Large |

Native `screencapture -i` crosshair already implements B's grammar
(drag draws, Space moves, Shift locks, Option centers, Esc cancels),
which is strong evidence B is the learnable target. D is worth naming
because if telemetry ever shows the preloaded box is *never* reused,
deleting memory beats tuning its gestures — but no such evidence exists
today, so keep memory.

## 5. Justified adjustments to the requirements

1. **Move modifier: Space primary, Cmd alias.** Hint reads
   `Drag to select | Space/Cmd-drag to move | Enter to capture | Esc to cancel`.
   Rationale §2.2(1), §3.1.
2. **Handles keep working with or without modifiers.** They are now the
   precision path, not the only path. No behavior change inside
   `resizeFromHandle`.
3. **Plain click (press+release <3px, any location) always cancels.**
   Extends the existing `new`-click-cancel rule to inside-clicks so
   there is no dead click that "does nothing" and no accidental confirm.
   Cheap to learn, safe against stray clicks.
4. **Modifier must be held before mousedown (v1).** Document in hint
   order ("Space-drag", not "drag+Space"). Mid-drag modifier switch is
   explicitly deferred — file as follow-up, do not half-implement.
5. **Double-click or Enter still confirms; no click-to-confirm.**
   Prevents the new hair-trigger draw from accidentally capturing on a
   shaky release.
6. **Hint swaps live when a move modifier is held** (requires
   `flagsChanged` + Space tracking; repaint hint line or cursor). Turns
   an invisible mode into a visible one.
7. **`MIN_SIZE`, clamping, persistence, Enter/Esc unchanged.**
   No reason to retune what is not complained about.

## 6. Recommended solution

**Ship B-v1: draw-first with Space/Cmd-move, snapshot at mousedown.**

Concrete work list (all in chezmoi; no `bob-cli` changes):

1. `home/dot_hammerspoon/screenshot_region.lua`
   - Add `spaceHeld` local + `keyUp`/`flagsChanged` to tap types.
   - Replace mousedown dispatch with handle → modifier+inside=move → else new (§3.1 sketch).
   - Update `hintFrame` text to `Drag to select | Space/Cmd-drag to move | Enter to capture | Esc to cancel` (widen `hintWidth` cap from 348 if needed; measure at 13pt).
   - Optional but cheap: on `flagsChanged`/Space state change while no drag is active, redraw hint in an "armed" style so users see the mode.
   - Clear `spaceHeld`/`drag` in `finish`/`cleanup`.
2. Tests (`tests/hammerspoon/`, `busted ./tests/hammerspoon` via `just test-hammerspoon`):
   - New `screenshot_region_spec.lua` with injected `hs` mock (follow the `init_spec.lua` `make_hs` pattern): mousedown-inside-without-modifier starts `new` (assert region follows drag endpoint), mousedown-inside-with-Cmd starts `move` (assert translate preserves size), handle grab still resizes with Cmd held, no-move click cancels, Enter confirms / Esc cancels unchanged.
   - No `macscrot_test.sh` changes (region-string contract `x,y,w,h` unchanged) — run `just test-bash` as regression.
3. Manual QA on the Mac (cannot be covered by `busted`): stale-box start → plain inside-drag redraws; Cmd-drag and Space-drag move; corner handles resize with and without modifiers; sub-3px click cancels; Enter captures and `hs.settings macscrotLastRegion` updates; Esc cancels; second invocation preloads last rect; multi-monitor start clamps (known limitation, unchanged).
4. Docs: one-line `home/dot_hammerspoon/` comment + hint string are the docs; no wiki needed. Mention in commit message that Space matches native `Shift+Cmd+4`.

Deferred (do not bundle): Shift axis-lock, Option resize-from-center,
live mid-drag Space switching, cross-monitor selection, cursor-shape
feedback. Each is a coherent follow-up against the same file.

## 7. Open questions for Bryan

- Do you ever *move* the preloaded box more often than you redraw it?
  If moves dominate, consider swapping the default back per a setting
  (`macscrotDrawFirst=true` default, opt-out to old behavior) rather
  than a flag day.
- Is Space acceptable given you trigger with the left hand already on
  modifiers, or does Cmd genuinely feel better on your keyboard/trackpad
  split? Shipping both costs nothing, but the hint can only lead with one.
- Should a plain inside-click (no drag) keep the old box selected
  (no-op, current `move`-click behavior) instead of cancelling? I
  recommend cancel for uniformity, but if your miss rate on tiny drags
  is high, no-op is kinder.

## Sources inspected

- `home/dot_hammerspoon/screenshot_region.lua` (full 501-line read),
  `home/dot_hammerspoon/init.lua:1-46` (trigger + `runMacscrot`),
  `home/bin/executable_macscrot`, `home/bin/executable_sshot_fetch`.
- `git log --follow` for `screenshot_region.lua` (`fde58338`,
  `4375716e`); `Justfile` test targets (`test-hammerspoon`,
  `test-bash`); `tests/hammerspoon/init_spec.lua:298-353`,
  `tests/bash/macscrot_test.sh`.
- Hammerspoon `hs.eventtap.event:getFlags` / `flagsChanged` semantics
  (event flags tables, `containExactly`, bare-modifier `flagsChanged`
  behavior) and native `Shift+Cmd+4` Space/Shift/Option grammar via web
  search for this report.
