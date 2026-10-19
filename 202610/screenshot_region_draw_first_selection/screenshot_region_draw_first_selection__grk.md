# Click-drag should redraw the macscrot region, with ⌘-drag to move

Researcher: `grk`. Independent report. Do not treat this as the swarm synthesis.

- **Question:** The Hammerspoon screenshot overlay bound to Ctrl+Shift+Opt+S is awkward when capturing a *specific* rectangle. The request is: unmodified click-and-drag from one corner of that rectangle to the other should resize/redraw the capture area; moving the existing box should require holding ⌘. Critique that plan, adjust requirements where justified, and recommend how to implement it.
- **Evidence:** chezmoi `home/dot_hammerspoon/screenshot_region.lua`, `home/dot_hammerspoon/init.lua`, `home/bin/executable_macscrot`; Hammerspoon `hs.eventtap` / `hs.eventtap.event:getFlags()` docs; git history of the picker (`a3c1e454`, `060dfcca`, `fde58338`); Apple Screenshot help (Shift-Command-4 vs Shift-Command-5); Shottr keyboard selection docs; Flameshot GUI shortcuts; ScreenCoord’s overlay model; Hammerspoon cursor-change limitation (issue #2425).
- **Date of evidence:** chezmoi linked checkout as of 2026-10-19.

## Bottom line

The request is the right product change. The overlay already *has* a rubber-band “new region” mode; unmodified drags inside the box run **move** instead, and a remembered (or default 60%) rectangle covers the thing you are trying to aim at, so the only remaining gesture is wrestling 10 pt corner handles. Invert that hit-test: unmodified drag draws a new marquee from the click, ⌘-drag moves the existing box, handles still resize. Keep last-region memory, Enter to capture, Esc to cancel, and capture-on-Enter (never mouse-up). Do this in `screenshot_region.lua`; leave `macscrot` and the hotkey alone.

## Current system

Ctrl+Shift+Opt+S is Hammerspoon, not a skhd/karabiner map:

```42:46:home/dot_hammerspoon/init.lua
hs.hotkey.bind({ "ctrl", "alt", "shift" }, "s", nil, function()
	ScreenshotRegion.pick(function(region)
		runMacscrot(region)
	end)
end)
```

`ScreenshotRegion.pick` shows a full-screen `hs.canvas` dim overlay with a blue rectangle, four corner handles, a `W x H` label, and the hint *Drag to adjust | Enter to capture | Esc to cancel*. On Enter it stores the rect in `hs.settings` under `macscrotLastRegion`, waits 80 ms for the overlay to disappear, then calls `macscrot x,y,w,h`. `macscrot` runs `/usr/sbin/screencapture -R` and uploads the PNG to apollo and athena.

The picker is a **crop widget that remembers the last shot**, not a **crosshair marquee**. That is a deliberate choice. On 2026-06-28 the tree tried native `screencapture -U -J selection` (Screenshot.app selected-portion mode, which itself remembers the last selection) in `a3c1e454`, reverted it two minutes later in `060dfcca`, and landed the custom overlay in `fde58338` (“remember screenshot capture region”). The upload pipeline needs a confirmed `x,y,w,h` before `screencapture -R`; the overlay exists so recapture-last-region is one key (Enter) after the hotkey.

### Pointer hit-test today

On `leftMouseDown` (`screenshot_region.lua` ~421–450) the first hit wins:

| Priority | Hit | Mode | Gesture |
| --- | --- | --- | --- |
| 1 | 20×20 px box around a corner (`HANDLE_SIZE = 10`, hit radius 10) | `resize` | that corner follows the pointer; opposite corner stays put |
| 2 | pointer inside the current rect | `move` | whole rect translates, clamped to the screen frame |
| 3 | pointer on the dimmed exterior | `new` | rubber-band from the click to the pointer (`normalizedRect`) |

`new` already does exactly “click one corner, drag to the other.” It is gated on clicking *outside* the current rect. Default first-run size is 60% of `hs.screen:frame()` centered (`defaultRegion`). After any real capture, `loadInitialRegion` restores that rect. A typical last region covers the content you next want, so gesture 3 is unreachable and gesture 2 (move) eats the click.

Other details that matter for the change:

- `new` requires 3 px of movement (`drag.moved`). An unmoved click in `new` **cancels the whole picker** on mouse-up. That is currently “click the dimmed margin to dismiss.”
- Every `keyDown` is swallowed (`return true`). Space, arrows, and ⌘Z do nothing.
- The canvas covers one screen. A mouse-down off that screen cancels the picker.
- There is no `screenshot_region` busted spec. `tests/hammerspoon/init_spec.lua` stubs `pick`. `just test-hammerspoon` runs `busted ./tests/hammerspoon`.

## Is this a good idea?

Yes. The pain is real, the proposed split matches how this overlay is actually used, and the implementation is a hit-test reorder plus a modifier read that Hammerspoon already exposes.

### What the request gets right

1. **The daily task is “frame this thing,” not “nudge the old frame.”** Recapture-same is already cheap (hotkey, Enter). The expensive path is a *different* rectangle whose both corners sit inside the remembered box. That is a marquee problem. Handle-dragging is a crop-tweak problem. The overlay currently serves the second problem as the default.
2. **⌘-drag as “this box is an object” is a coherent modifier.** Unmodified drag = draw. Modifier-drag = translate. That is stable for a *persistent* overlay, where a committed rectangle sits on screen until Enter. It is a different mapping from Shift-Command-4, which has no committed rectangle (mouse-up captures). For this widget, a modifier on the committed box is the right shape.
3. **Keep move.** Recapture-nearby (same size, shifted a few dozen pixels) is a real third task. Dropping it would force a full redraw for a translation.
4. **Do this in the existing picker.** Native `screencapture -i` is the crosshair, and it was already rejected as the interactive path. CleanShot / Shottr / ScreenCoord would not feed `macscrot`’s region+upload contract. The change belongs in `screenshot_region.lua`.

### Where the request as written is incomplete

- It does not say what happens if the drag starts on a **handle**. Handles must keep winning with no modifier, or fine-tuning one corner of a remembered rect gets worse.
- It does not say what a **click without a drag** does. Today, unmoved `new` (only possible on the dimmed exterior) cancels the session. If interior clicks become `new`, that same mouse-up rule would dismiss the overlay when you misclick inside the box. Interior click-without-drag must be a no-op. Exterior click-without-drag can stay cancel.
- It does not say **when the old rect is allowed to collapse.** Today `new` calls `updateNewRegion` on mouse-down, so the box jumps to 16×16 at the click before you have moved. For an interior miss that is visually destructive. Wait for the existing 3 px threshold before replacing the rect.
- It does not say whether capture still happens on **Enter**. Mouse-up capture (Shift-Command-4) is faster for a one-shot marquee and would throw away “draw, then handle-tweak, then Enter” and “hotkey, Enter” recapture. Keep Enter.
- It does not mention **⌘ as a flag on the mouse event**. Implementation is `event:getFlags().cmd` on `leftMouseDown` (Hammerspoon documents `cmd` / `alt` / `shift` / `ctrl` / `fn` on that table, with `contain` / `containExactly`). Latch the mode at mouse-down. Do not require a `flagsChanged` tap for v1.
- It does not mention the **hint**. The current string still says “Drag to adjust” and will teach the old move. The hint has to name both gestures the first time this ships.

### Risks of the plan as stated

- **Muscle memory:** interior-drag currently moves. After the change it redraws. Anyone who has been sliding the last PDF-page rect will need the hint, and will want undo (see ADJ-6).
- **Accidental redraw** of a carefully placed last region, if the 3 px threshold is skipped or if trackpad jitter counts as a drag. Keep the threshold; restore on ⌘Z.
- **Cursor affordance is weak.** Hammerspoon cannot reliably set the system cursor while a `screenSaver`-level canvas is up and Hammerspoon is not frontmost (Hammerspoon #2425, 2020, still the documented limitation: `hs.mouse` can *read* `crosshairCursor` / `closedHandCursor` via `currentCursorType`, and has no setter). Do not block the feature on a crosshair pointer. Teach with the hint and, if wanted later, a small canvas-drawn crosshair that follows the mouse.

## Comparable interaction models

Two Apple products are the template this overlay mixed together.

**Shift-Command-4** (Apple Mac User Guide, “Capture a portion of the screen”): pointer becomes a crosshair; click-drag defines the rectangle; **release captures**. While the button is down: **Space** moves the in-progress rect; **Shift** locks one axis; **Option** resizes from the center. There is no committed box and no last-region overlay. This is the right *draw* grammar.

**Shift-Command-5 → Capture Selected Portion** (same Apple page, Screenshot panel): a remembered frame appears; “drag the frame to reposition it or drag its edges to adjust the size”; Options include **Remember Last Selection**. There is no “click inside and draw a new rect.” This is the right *remember* grammar, and the wrong *draw* grammar. It is also the UX `a3c1e454` tried to reuse and `060dfcca` abandoned.

The custom picker cloned Shift-Command-5’s frame, then added a Shift-Command-4-style rubber-band that only runs on the dimmed margin. The request is to let the rubber-band run everywhere the handles are not.

Other tools, for calibration:

| Tool | Draw new rect | Move existing | Resize | Confirm |
| --- | --- | --- | --- | --- |
| Shift-Command-4 | unmodified drag | Space *during* the drag | Shift / Option during the drag | mouse-up |
| Shift-Command-5 portion | (none; handles/edges only) | drag the frame | drag edges | Capture / Enter |
| Current `screenshot_region` | drag on dimmed exterior | drag interior | 4 corner handles | Enter |
| Shottr editor selection | drag | arrows 1 px; Shift-arrows 10 px | ⌘-arrows; `[` `]` grow | Enter |
| Flameshot GUI | drag to create, then handles | arrows 1 px; Ctrl+M “move selection” | Shift+arrows; handle drag | tool action / Enter (save path differs) |
| ScreenCoord (Brett Terpstra, 2026) | drag out, then fine-tune | drag inside | corner **and edge** handles | Enter / Confirm |

Shottr and Flameshot both treat **arrow-key nudge** as part of “specific rectangle,” not a luxury. ScreenCoord is the closest cousin of this overlay (dim screen, live size, confirm/cancel, print `x,y,w,h` for `screencapture -R` in screen *points*, top-left of the primary display). It still uses interior-drag = move after the first marquee, which recreates the original problem the moment the new rect is large. That is why a **modifier-gated move**, rather than a two-phase “ghost then commit,” is the better end state: unmodified drag stays “draw” even after the box is large.

⌘ is a good move modifier on macOS for *this* widget:

- **Control** would collide with Control-click (right-click).
- **Option** is Apple’s “resize from center” during Shift-Command-4.
- **Shift** is Apple’s axis lock.
- **Space** is Apple’s “move the in-progress marquee” and, if pressed *before* a Shift-Command-4 drag, window capture. Keep Space for in-progress-move (ADJ-5). Do not make it the only way to move a *committed* box; a held letter is a worse mouse-down chord than ⌘.

## Alternatives considered

**A. User’s plan (unmodified drag = new, ⌘-drag = move).** Adopt, with the hit-test / threshold / Enter adjustments below. Smallest change that fixes the actual complaint.

**B. Two-phase ghost.** Hotkey shows the last rect as a dashed ghost; Enter recaptures; any drag draws a new committed box; after commit, interior-drag moves again. Recapture-same is pretty. After you draw a large new rect, “frame something else” is once again handle-wrestling. Reject as the end state. A ghost *look* for the last rect is still optional chrome on top of A.

**C. Shrink the default rect / expire last region.** Helps the first launch. After one large capture, `macscrotLastRegion` restores the problem. Too magical if last-region is the reason the overlay exists.

**D. Go back to `screencapture -i` or Screenshot.app `-U -J selection`.** Crosshair draw (D-interactive) or Shift-Command-5 handles (D-toolbar). Already tried and reverted. Neither produces the overlay’s “Enter recaptures last `x,y,w,h` into `macscrot`” loop.

**E. Capture on mouse-up, like Shift-Command-4.** Fastest one-shot. Destroys handle-tweak-then-Enter and hotkey-then-Enter. Reject for this tool. A later chord (for example Option-release) could add a quick path without replacing Enter.

**F. Replace Hammerspoon with Shottr / CleanShot / ScreenCoord.** Annotation, loupe, OCR are unrelated to `#sshot` / apollo / athena. Out of scope.

## Requirement adjustments

Call-outs the lead should adopt or explicitly reject.

| ID | Adjustment | Why it is justified |
| --- | --- | --- |
| **ADJ-1** | **Hit-test order:** (1) corner handle → `resize`, (2) ⌘ held → `move` from *anywhere* on this screen, (3) else → `new` rubber-band. | Handles are the precision tool for a remembered rect. ⌘-move from the dimmed margin means you do not have to start inside a small box. Unmodified drag is always “frame this.” |
| **ADJ-2** | **3 px threshold before `new` mutates the rect.** Interior unmoved click: no-op. Exterior unmoved click: cancel (keep today’s dismiss). | Prevents a misclick from collapsing a remembered region to `MIN_SIZE` (16 px) or from dismissing the overlay. |
| **ADJ-3** | **Latch mode at mouse-down** from `event:getFlags().cmd`. | Mouse events carry modifier flags. A `flagsChanged` tap is only needed for mid-drag Space (ADJ-5). |
| **ADJ-4** | **Keep Enter to capture, Esc to cancel, last-region memory, 80 ms hide delay.** Do not capture on mouse-up. | Those four are the overlay’s reason to exist versus `screencapture -i`. |
| **ADJ-5** | **Space while a button-down `new` or `resize` is in progress** translates the in-progress rect (Apple Shift-Command-4). Release Space and continue reshaping. | Complements ⌘-drag of a *committed* box. Cheap once `keyDown` / `keyUp` / `flagsChanged` stop being a total swallow. |
| **ADJ-6** | **⌘Z restores the rect from before the last completed drag.** | Unmodified drag now clobbers a remembered region. Shottr/Flameshot both treat undo as part of selection, not only annotation. |
| **ADJ-7** | **Arrow keys nudge 1 px; Shift+arrows 10 px** once a rect exists. | This is the actual “specific rectangular space” finisher. Shottr documents it; Flameshot ships it. Handle-drag cannot do 1 px reliably on a trackpad. |
| **ADJ-8** | **Rewrite the hint** to name both mouse gestures, e.g. `Drag new region · ⌘-drag moves · Enter captures · Esc cancels`. Widen `hintWidth` past 348 if the string needs it. | The overlay currently trains the old move. |
| **ADJ-9** | **Keep `macscrot` and the hotkey unchanged.** Region format stays `x,y,w,h` in screen points for `screencapture -R`. | Brett Terpstra’s ScreenCoord notes (2026) match what this pipeline already assumes: `-R` is points, origin top-left of the primary display, negative x/y legal. No conversion work in this change. |
| **ADJ-10** | **Do not block on a system cursor change.** Optional: draw a 16 px canvas crosshair that follows the pointer in `new` mode. | Hammerspoon has no supported global cursor setter for a non-frontmost overlay. |
| **ADJ-11** | **Edge handles (N/E/S/W) are v1.1**, not a blocker. Four corners plus arrows cover the request. | ScreenCoord’s edge handles are nicer for “this edge is one line off.” They are extra hit-test surface that can fight `new`. Add after the modifier split feels right. |
| **ADJ-12** | **Shift during `new` locks the first axis that exceeds a few pixels; Option resizes from the anchor (Apple).** v1.1. | Useful, and they must not steal ⌘. |
| **ADJ-13** | **Off-screen mouse-down can stay cancel for v1.** Relocating the canvas to the clicked display is a separate bugfix. | Single-laptop use (the MacBook this hotkey lives on) rarely hits it. Do not fold it into the modifier work. |
| **ADJ-14** | **Extract the hit-test into a pure function and add `tests/hammerspoon/screenshot_region_spec.lua`.** | `just test-hammerspoon` already runs busted on that directory. `pomodoro_countdown_spec.lua` is the pattern. The bug class here is “wrong mode for this point+flags,” which is unit-testable without a canvas. |
| **ADJ-15** | **Never use Control as the move modifier.** | Control-click is right-click. The request’s ⌘ choice is already the safe one. |

## How to implement it

Scope is `home/dot_hammerspoon/screenshot_region.lua` plus a new spec. `init.lua` only needs a comment if the hint is documented there (it is not). Chezmoi already restarts Hammerspoon when this file’s hash changes (`run_onchange_after_restart_hammerspoon.tmpl` includes `screenshot_region.lua`).

Suggested shape, all inside the existing `pick` eventtap:

```lua
local DRAG_SLOP = 3 -- already used by mode "new"

local function flagsCmd(event)
	local flags = event:getFlags()
	return type(flags) == "table" and flags.cmd == true
end

-- mouseDown, after the off-screen cancel:
local handle = handleAt(point, region)
if handle then
	drag = { mode = "resize", handle = handle, startRegion = copyRect(region) }
elseif flagsCmd(event) then
	drag = { mode = "move", startPoint = point, startRegion = copyRect(region) }
else
	drag = {
		mode = "new",
		anchor = point,
		moved = false,
		startRegion = copyRect(region),
		fromInterior = pointInRect(point, region),
	}
	-- do not call updateNewRegion until moved
end
```

On `leftMouseDragged` for `new`, keep the existing slop, then `updateNewRegion(drag.anchor, point)`.

On `leftMouseUp`:

- `new` and not `moved` and `fromInterior` → `drag = nil`, region unchanged.
- `new` and not `moved` and not `fromInterior` → `finish(false)` (today’s click-outside cancel).
- otherwise → `drag = nil`.

Export (or sibling-module) something like:

```lua
function M.classifyMouseDown(point, region, opts)
	-- opts.cmd, opts.handleName, opts.screenFrame
	-- returns "resize" | "move" | "new"
end
```

Spec cases worth locking:

- click inside, no ⌘ → `new` (pending)
- click inside, ⌘ → `move`
- click outside, no ⌘ → `new`
- click outside, ⌘ → `move`
- click on `se` handle, with and without ⌘ → `resize` / `se`
- `new` drag of 2 px inside → region unchanged
- `new` drag of 3+ px → rubber-band includes the anchor and the point, min 16 px
- unmoved interior mouse-up → picker still active
- unmoved exterior mouse-up → cancel
- ⌘Z after a completed `new` → `startRegion` restored

`keyDown` today returns true for every key. Keep swallowing, but handle `return` / `escape` as now, plus `z` with `flags.cmd` for undo, plus arrows (and Shift) for nudge. That is the same tap; no second eventtap.

Do not add a long-running `flagsChanged` tap unless ADJ-5 lands in the same patch. If it does, Space-down during `new`/`resize` snapshots the current rect and switches the remainder of the drag to translation; Space-up returns to reshape from the new opposite corner.

## Critique summary

The plan is a good idea. I would take the same approach, with ADJ-1–ADJ-4 as part of v1 rather than follow-ups: handle priority, drag slop, no interior-click cancel, Enter still captures. I would also take ADJ-6 (undo) and ADJ-7 (arrow nudge) in v1 because unmodified-draw makes them load-bearing. I would not replace the overlay, would not capture on mouse-up, and would not use Space or Control as the committed-move modifier.

## Recommended solution

Implement **marquee-first selection on the existing Hammerspoon overlay**.

1. Unmodified click-drag, including from inside the current box, rubber-bands a new capture rectangle from the press point to the pointer (the `new` path that already exists).
2. ⌘-click-drag moves the current rectangle, from anywhere on the overlay screen.
3. Corner handles still resize with no modifier, and still win over ⌘.
4. Enter captures, Esc cancels, last region still preloads, `macscrot x,y,w,h` is unchanged.
5. Interior click without a 3 px drag leaves the rect alone; exterior click without a drag still dismisses.
6. ⌘Z undoes the last completed drag; arrows nudge 1 px (Shift+arrows 10 px).
7. Update the on-canvas hint. Add `tests/hammerspoon/screenshot_region_spec.lua` around a pure `classifyMouseDown` / drag-apply helper.

That is a localized Lua change in chezmoi, applied on the Mac by the existing Hammerspoon restart hook. It keeps the overlay’s recapture superpower and gives the Shift-Command-4 draw gesture on top of it, which is the thing the handles cannot replace.

## Sources

- chezmoi `home/dot_hammerspoon/screenshot_region.lua` (hit-test, `new`/`move`/`resize`, hint, last-region)
- chezmoi `home/dot_hammerspoon/init.lua` (Ctrl+Alt+Shift+S → `pick` → `macscrot`)
- chezmoi `home/bin/executable_macscrot` (`screencapture -R` region path)
- git `a3c1e454` / `060dfcca` / `fde58338` (native Screenshot toolbar attempt, revert, custom picker)
- [Hammerspoon `hs.eventtap.event:getFlags()`](https://www.hammerspoon.org/docs/hs.eventtap.event.html)
- [Apple Mac User Guide: Take screenshots](https://support.apple.com/guide/mac-help/take-a-screenshot-mh26782/mac) (Shift-Command-4 drag; Shift-Command-5 remembered portion)
- [Macworld, screenshot selection modifiers](https://www.macworld.com/article/233819/how-to-take-better-screenshot-selections-in-macos.html) (Space / Shift / Option while dragging)
- [Shottr: manipulate selection with the keyboard](https://shottr.cc/)
- [Flameshot README, GUI shortcuts](https://github.com/flameshot-org/flameshot) (arrows, Ctrl+M move selection)
- [ScreenCoord](https://brettterpstra.com/projects/screencoord/) (`screencapture -R` in screen points; overlay then fine-tune)
- [Hammerspoon #2425](https://github.com/Hammerspoon/hammerspoon/issues/2425) (canvas cursor change)
- chezmoi `Justfile` `test-hammerspoon` → `busted ./tests/hammerspoon`
