# Screenshot Region Picker: Drag-to-Draw by Default, ⌘-Drag to Move

**Researcher:** cld · **Date:** 2026-10-19 · **Scope:** the `⌃⇧⌥S` screenshot selector in the
chezmoi repo (Hammerspoon + `~/bin/macscrot`)

## TL;DR

- The selector is a custom Hammerspoon overlay, `home/dot_hammerspoon/screenshot_region.lua`,
  bound in `home/dot_hammerspoon/init.lua:42` (`{ "ctrl", "alt", "shift" }, "s"`). It preloads
  the last confirmed rectangle and passes `x,y,w,h` to `macscrot`, which runs
  `screencapture -R`, uploads to apollo and athena, and copies the path to the clipboard.
- **Drag-to-draw already exists, but only when the drag starts outside the current box.** A
  drag that starts inside the box moves it (`screenshot_region.lua:435-440`). The preloaded box
  is large (the last region, or 60% of the screen the first time), so the natural "corner to
  corner" drag often starts inside it and moves the box instead. The overlay also can't change
  the cursor to warn you, and the hint text ("Drag to adjust") never mentions drawing.
- **Your plan is a good one, and I'd adopt it with a few changes:** a plain drag *anywhere*
  draws a new box, ⌘-drag moves it, and the corner handles still resize. The changes I made to
  your requirements are listed under [Requirement adjustments](#requirement-adjustments): ⌘-drag
  works from anywhere, not only inside the box; holding ⌘ partway through a draw repositions the
  new box; I added edge handles; a click with no drag stops cancelling the session; and the
  overlay shows which mode you're in.
- It's a small change (roughly 100 lines in one Lua file plus a new busted spec). It doesn't
  touch `macscrot` or the `#sshot` flow.

## 1. What exists today

### 1.1 Pipeline

| Stage                    | Where                                          | What it does                                                                                                                                                       |
| ------------------------ | ---------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Hotkey                   | `home/dot_hammerspoon/init.lua:42-46`          | `⌃⌥⇧S` → `ScreenshotRegion.pick(runMacscrot)`                                                                                                                      |
| Selector                 | `home/dot_hammerspoon/screenshot_region.lua`   | Full-screen `hs.canvas` dims everything outside the box and draws the box, 4 corner handles, a size label, and a hint. An `hs.eventtap` swallows mouse and key events. |
| Memory                   | `hs.settings` key `macscrotLastRegion`         | The last *confirmed* rectangle (saved on Enter only)                                                                                                               |
| Capture/upload           | `home/bin/executable_macscrot`                 | `screencapture -R x,y,w,h` → `~/tmp/screenshots/<ts>.png`, scp to apollo and athena in parallel, `pbcopy` the path, notify                                          |
| Consumer                 | `home/sase/macros/sshot.yml`, `bin/sshot_fetch` | `#sshot` macro injects the newest screenshot into a SASE prompt                                                                                                    |

History: `1e4b71b9` (2026-06-14) added `macscrot` using plain `screencapture -i` (the native
crosshair). `a3c1e454` (2026-06-28) tried the native Screenshot toolbar
(`screencapture -i -U -J selection`) to get a remembered, resizable frame, and `060dfcca`
reverted it the same day. The commit message doesn't say why. `fde58338`, also 2026-06-28,
then added this Hammerspoon picker ("remember screenshot capture region"). So the picker exists
mainly to **re-capture a remembered rectangle**, and that has to keep working.

### 1.2 Current gesture map (`screenshot_region.lua:398-485`)

| Input                                        | Current behavior                                                                  |
| -------------------------------------------- | --------------------------------------------------------------------------------- |
| Mouse-down within ±10pt of a corner          | Resize from that corner (`handleAt`, a 20×20 hit box centered on the corner)      |
| Mouse-down inside the box                    | **Move** the box                                                                  |
| Mouse-down outside the box (same screen)     | **Draw a new box** from that point                                                |
| Click outside the box with no drag (<3pt)    | **Cancels the whole session** (`finish(false)`, lines 475-478)                    |
| Mouse-down off the overlay's screen frame    | Cancels the session                                                               |
| Enter / keypad Enter                         | Capture (saves the region)                                                        |
| Esc                                          | Cancel                                                                            |
| Any other key                                | Swallowed, ignored                                                                |

### 1.3 Why it feels hard to use for a specific rectangle

1. **Whether a drag draws or moves depends on where it starts.** The box you're replacing is
   usually big and often overlaps the new target, so "start at the target's corner" lands inside
   it about as often as not, and you get a move.
2. **Nothing tells you which mode you're about to get.** macOS and Photoshop can make "drag
   inside = move" work because the cursor changes shape over the selection. Hammerspoon can't
   do that: `hs.mouse` only *reads* the cursor type (`hs.mouse.currentCursorType`), and
   `hs.canvas` has no cursor rects or tracking areas (checked in Hammerspoon source at
   `23e387e2`: `extensions/mouse/libmouse.m`, `extensions/canvas/libcanvas.m`). So the mode
   depends on location and you can't see the location boundary.
3. **The hint hides the draw gesture.** It says "Drag to adjust | Enter to capture | Esc to
   cancel" (line 262).
4. **Only corners can be adjusted.** Fixing one edge means dragging a corner along exactly one
   axis. That's the hardest drag to do precisely, and precise edits are exactly what this
   workflow needs.
5. **The mode switches at a 3pt threshold.** On mouse-down in "new" mode the remembered box is
   replaced right away with a 16×16 stub (line 447). If the pointer then moves less than 3pt,
   the whole session cancels.

## 2. How other tools handle it

| Tool                                  | Draw a new box                       | Move a box                                                                                                                     | Notes                                                                                                                                       |
| ------------------------------------- | ------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------- |
| macOS `⌘⇧4` crosshair                 | Plain drag                           | **Hold Space while dragging** freezes the size and moves the box. Release Space to resume sizing.                              | Shift locks an axis; Option resizes from the center (Macworld). Captures on mouse-up.                                                      |
| macOS `⌘⇧5` "Selected Portion"        | Drag                                 | Drag from inside the selection                                                                                                 | The `-U -J selection` route was tried and reverted (§1.1). Location-based modes, like the current picker.                                  |
| Photoshop Rectangular Marquee         | Drag outside the selection           | Drag inside the selection moves the outline (the cursor changes to show it). **Space while drawing** repositions.              | Arrow keys nudge; Shift+arrow nudges 10. Location-based, but backed by cursor feedback.                                                    |
| CleanShot X                           | "Capture Area"                       | n/a                                                                                                                            | Has a **separate** "Capture Previous Area" action/URL (`cleanshot://capture-previous-area`). It splits *repeat* and *new* into two commands. |
| Shottr                                | Drag                                 | n/a                                                                                                                            | Its precision guidance is "capture full screen, then crop with zoom". Precision comes from zoom and adjusting after the fact.              |

What this shows:

- **"Hold a key to move the box you're drawing"** is the standard trick (Space in both `⌘⇧4`
  and Photoshop). It moves the box you're drawing, not an existing one.
- **"Drag inside = move"** only works when the cursor shows it. This overlay can't change the
  cursor, so copying the convention without that cue causes exactly the mistake you're seeing.
- **Precision comes from adjusting after the draw** (handles, arrow-key nudges, zoom). The
  initial drag only gets you close. Your plan fixes how the gesture starts, but "a *very
  specific* rectangle" also needs better adjustment tools.
- CleanShot shows the "repeat the last area" vs "draw a new one" tension is real. It solves it
  with two commands. Here, one overlay with draw as the default does both: you see the old box,
  Enter reuses it, and any drag replaces it. That's better than adding a second hotkey.

## 3. Critique of the proposed plan

**What it gets right**

- **The modifier goes on the rare action.** Drawing a fresh box is the main job. Moving a box
  without resizing it is uncommon (mostly "same size, different place"). An unmodified drag
  should do the common thing.
- **It removes the location-based draw/move split**, which this overlay can't signal with the
  cursor (§1.3.2). One modifier is easier to predict than an invisible boundary.
- **⌘ is the best free modifier here.** ⌃-click is the macOS secondary click, ⌥ and ⇧
  conventionally mean "from center" and "constrain", and ⌘ isn't part of the `⌃⌥⇧S` trigger,
  so modifiers you're still holding from the hotkey can't flip you into move mode. Photoshop
  also treats ⌘ as "temporary Move tool" (general knowledge, not re-verified here). The
  eventtap swallows the mouse events, so ⌘-click never reaches the app underneath. No window
  manager with modifier-drag (yabai, AeroSpace, etc.) is configured in chezmoi.
- **It's cheap.** The draw path (`updateNewRegion`, `normalizedRect`, min-size handling) already
  exists. The core change mostly reorders the mouse-down branch.

**Gaps and risks in the plan as stated**

1. **"Hold ⌘ while dragging" can mean two things.** It could mean ⌘ held at mouse-down (move the
   existing box), or ⌘ pressed partway through a draw (move the box being drawn, like Space in
   `⌘⇧4`). Both are useful and they don't conflict. I specify both below.
2. **It only fixes how the gesture starts, not precision.** One drag rarely lands exactly. Edge
   handles (and, later, arrow keys) are what make "very specific" achievable.
3. **What a click does has to change.** Once a drag anywhere draws, every aborted drag (<3pt of
   jitter) anywhere would go down the current "click outside = cancel" path. Losing the session
   to a twitch is worse than today's behavior.
4. **Handles still claim their hit zones.** A new drag that starts within ~10pt of an old corner
   (or edge handle) resizes instead of drawing. That's rare, the handles are visible, and the
   result shows immediately, so I accept it. The alternative is an "⌥-drag always draws"
   escape hatch, which isn't worth the extra rule.
5. **No mode cue.** Without cursor control, holding ⌘ needs an on-canvas cue, or move mode is
   just as hard to see as the inside-the-box rule.

**Approaches I considered and rejected**

| Alternative                                                                   | Why not                                                                                                                                                                                                                                       |
| ----------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Keep the behavior and just fix the hint ("drag outside to draw")              | It's still location-based with no cursor cue, and a big remembered box leaves little "outside" near the target.                                                                                                                               |
| The reverse: plain drag moves, ⌘-drag draws                                   | Puts the modifier on the common action.                                                                                                                                                                                                       |
| Space-hold instead of ⌘                                                       | Needs keyUp tracking, and "hold Space, then press the mouse" is awkward to chord. ⌘ is a real modifier that shows up in each event's flags. Space could be added as an alias *during a draw* for `⌘⇧4` muscle memory; optional.               |
| Two hotkeys ("repeat last region" + "fresh crosshair", CleanShot-style)       | Another chord to remember, and you can't see the old box before deciding. Not needed once a drag anywhere draws.                                                                                                                              |
| Go back to the native `screencapture -i` crosshair for new regions            | Hammerspoon never learns the drawn rectangle, so it can't be remembered. The native toolbar route was already tried and reverted.                                                                                                             |
| Buy CleanShot X or Shottr                                                     | More polished (zoom, snapping), but paid, and it bypasses the `macscrot` upload/clipboard/`#sshot` flow unless you add a folder watcher. Too much churn for a gesture problem.                                                                 |

## Requirement adjustments

These are my changes to your requirements, each called out explicitly:

| #      | Your requirement / current behavior                       | Adjusted requirement                                                                                                                                                                                                    | Why                                                                                                                           |
| ------ | --------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| **A1** | Click-drag from one corner to the other draws the area    | **Kept**, and clarified: a plain drag starting *anywhere*, inside or outside the current box, draws a new box. The exception is a drag that starts on a handle.                                                        | This is the core fix.                                                                                                         |
| **A2** | Hold ⌘ while dragging to move the area                    | **Changed:** ⌘ held at mouse-down moves the current box **from anywhere on the overlay**, not only from inside it. The mode is locked at mouse-down; releasing ⌘ mid-move doesn't switch modes.                          | Removes the last location rule; a relative move doesn't need you to "grab" the box.                                           |
| **A3** | —                                                         | **Added:** pressing ⌘ *during* a draw freezes the new box's size and moves it with the pointer. Releasing ⌘ resumes sizing from the moved anchor.                                                                       | The `⌘⇧4`/Photoshop Space trick, mapped onto your modifier so "⌘ = move" holds everywhere. It fixes a misplaced starting corner without redrawing. |
| **A4** | —                                                         | **Added:** edge handles at the midpoints of the four sides (n/s/e/w) next to the corners. They resize one axis.                                                                                                        | Precise single-edge fixes. Same convention as macOS `⌘⇧5`.                                                                    |
| **A5** | Current: a click outside with no drag cancels the session | **Changed:** a click with no drag (<3pt) anywhere does nothing and restores the box from before the click. Esc is the only cancel.                                                                                     | Under A1, the old rule would cancel on every twitch.                                                                          |
| **A6** | —                                                         | **Added:** visible mode cues. While ⌘ is held, the outline changes color (e.g. orange) and the hint reads "Move". The idle hint lists the gestures.                                                                     | Hammerspoon can't change the cursor (§1.3.2).                                                                                  |
| **A7** | —                                                         | **Added (phase 2, optional):** arrow keys move the box 1pt (⇧: 10pt); ⌥+arrows resize from the right and bottom edges.                                                                                                 | Pixel-precise finishing without fine mouse control. The binding is my choice; I found no shared convention for keyboard resizing. |
| **A8** | —                                                         | **Flagged (separate fix):** the overlay uses `screen:frame()`, which excludes the menu bar and Dock (Hammerspoon `extensions/screen/screen.lua`). Those areas can't be captured, and clicking them cancels. It also picks the saved region's screen over the screen the pointer is on. | Not part of the gesture change, but it limits "any specific rectangle". Check on the Mac before fixing.                       |

Explicitly **out of scope** (YAGNI): ⇧ to constrain or make a square, ⌥ to draw from the
center, a zoom loupe, snapping to windows or AX elements. See §5 for when they'd be worth it.

## 4. Implementation notes

All changes are in `home/dot_hammerspoon/screenshot_region.lua`. No new Lua file is needed.
Adding one would also require a hash line in
`home/.chezmoiscripts/run_onchange_after_restart_hammerspoon.tmpl`, which
`tests/bash/hammerspoon_restart_hook_test.sh` enforces.

### 4.1 Mouse-down classification (replaces lines 428-449)

```lua
local function pressMode(point, region, flags)
	if flags.cmd then
		return "move"
	end
	local handle = handleAt(point, region) -- corners + n/s/e/w midpoints
	if handle then
		return "resize", handle
	end
	return "new"
end

-- leftMouseDown (after the off-screen check):
local mode, handle = pressMode(point, region, event:getFlags())
drag = {
	mode = mode,
	handle = handle,
	startPoint = point,
	lastPoint = point,
	anchor = point,
	startRegion = copyRect(region),
	moved = false,
}
return true -- don't touch `region` yet: no 16×16 flash, nothing to undo on a click
```

### 4.2 Drag handling

```lua
-- leftMouseDragged:
if not drag.moved then
	if math.abs(point.x - drag.startPoint.x) < 3 and math.abs(point.y - drag.startPoint.y) < 3 then
		return true
	end
	drag.moved = true
end
if drag.mode == "move" then
	-- existing code: startRegion + (point - startPoint), clamped
elseif drag.mode == "resize" then
	region = resizeFromHandle(drag.startRegion, drag.handle, point, screenFrame)
elseif drag.mode == "new" then
	if event:getFlags().cmd then -- A3: reposition the in-progress box
		local shifted = clampRegionToFrame({
			x = region.x + point.x - drag.lastPoint.x,
			y = region.y + point.y - drag.lastPoint.y,
			w = region.w,
			h = region.h,
		}, screenFrame)
		drag.anchor = { x = drag.anchor.x + shifted.x - region.x, y = drag.anchor.y + shifted.y - region.y }
		region = shifted
	else
		updateNewRegion(drag.anchor, point)
	end
end
drag.lastPoint = point
redraw()
```

Moving the anchor by the *clamped* delta keeps the anchor and box consistent at screen edges.
After a clamped move the free corner can sit a little away from the pointer, and it snaps back
on the next unmodified drag event. `⌘⇧4` behaves similarly.

### 4.3 Edge handles fold into the existing resize

`resizeFromHandle` gets simpler if it tests handle letters instead of naming each case, and then
it covers all eight handles:

```lua
if handle:find("w") then left = clamp(point.x, frame.x, right - MIN_SIZE) end
if handle:find("e") then right = clamp(point.x, left + MIN_SIZE, frame.x + frame.w) end
if handle:find("n") then top = clamp(point.y, frame.y, bottom - MIN_SIZE) end
if handle:find("s") then bottom = clamp(point.y, top + MIN_SIZE, frame.y + frame.h) end
```

`handleAt` and `buildElements` each gain four midpoint entries. Check corners first so they win
on small boxes.

### 4.4 Mouse-up (A5)

```lua
if drag and not drag.moved then
	region = drag.startRegion -- a click is a no-op; Esc cancels
	redraw()
end
drag = nil
```

### 4.5 Mode cue (A6)

- Add `eventTypes.flagsChanged` to the tap mask. When the ⌘ state flips, store `cmdHeld` and
  redraw, then **return `false`** so the modifier event still reaches the frontmost app.
  Swallowing modifier events risks stuck-modifier state there.
  `hs.eventtap.event:getFlags()` returns `{ cmd = true, ... }`, and `flagsChanged` is a tappable
  type (Hammerspoon `extensions/eventtap/libeventtap_event.m`).
- `buildElements(region, screenFrame, cmdHeld)`: when `cmdHeld`, use an orange stroke instead of
  blue and show the hint "Move".
- Idle hint, which also fixes discoverability:
  `Drag: new area · ⌘-drag: move · handles: resize · ↩ capture · esc cancel`. Widen `hintWidth`
  (currently 348) to fit.

### 4.6 Tests

There's no spec for `screenshot_region.lua` today (`tests/hammerspoon/init_spec.lua` stubs the
whole module). The repo's pattern (`ping_window_spec.lua`) is `assert(loadfile(PATH))()` plus
pure helpers. The module only touches `hs.*` inside functions, so it already loads under plain
busted. Expose the pure pieces (for example
`M._gesture = { pressMode, resizeFromHandle, dragStep, ... }`) and add
`tests/hammerspoon/screenshot_region_spec.lua` covering:

- a plain press inside, outside, or on a corner/edge → `new` / `new` / `resize:<h>`;
- a ⌘ press anywhere, including on a handle → `move`;
- a press then release without moving → the region is unchanged and the session is not cancelled;
- ⌘ during a draw keeps `w,h` and moves the anchor, and releasing ⌘ resumes from the moved
  anchor;
- clamping at the frame edges for the move, the ⌘-reposition, and each of the 8 handles.

Run with `just test-hammerspoon` and format with `just fmt-lua`. The overlay
itself can only be checked on the Mac (athena can't run Hammerspoon), so the implementer
should leave Bryan a short manual checklist:

- draw inside the old box;
- ⌘-drag;
- ⌘ during a draw;
- an edge handle;
- a stray click;
- Esc and Enter.

### 4.7 Phase 2: arrow keys (A7)

The tap already swallows every keyDown. Handle `left/right/up/down`: step = 10 when `flags.shift`
else 1. `flags.alt` changes `w`/`h` (right and bottom edges); otherwise move `x`/`y`. Clamp with
`clampRegionToFrame`, then redraw. Autorepeat works for free. Optionally show `x,y` in the size
label so nudges have visible feedback.

## 5. Bigger ideas, not recommended now

- **Click to select a window.** A no-drag click could select the frontmost window under the
  pointer (`hs.window.orderedWindows()`, skipping the overlay), like the window mode of
  `⌘⇧4`+Space. A later step could snap edges to window frames, or to pane boundaries via
  `hs.axuielement.systemElementAtPosition`. Worth it if your "specific rectangles" usually turn
  out to be a window or pane. A5 keeps the click free so this can be added later.
- **Zoom loupe.** Take one `hs.screen:snapshot()` before showing the overlay and draw a clipped,
  magnified crop near the pointer. That's the Shottr/CleanShot precision model. It costs real
  redraw performance in `hs.canvas`, and arrow-key nudges cover most of the need.
- **Full-frame and multi-monitor fix (A8).** Use `fullFrame()` for the canvas and clamp
  consistently. Open the overlay on the pointer's screen, and preload the saved region only if
  it's on that screen. Do this if the menu bar, Dock, or a second display ever matters.

## 6. Recommended solution

**Keep the Hammerspoon picker and its remembered-region + `macscrot` pipeline, and flip the
gesture map to draw-first with ⌘ to move**, all inside
`home/dot_hammerspoon/screenshot_region.lua`:

1. **Plain drag anywhere draws a new box** (A1). The box only changes once the pointer has moved
   3pt.
2. **⌘ held at mouse-down moves the current box from anywhere** (A2), locked until mouse-up.
3. **⌘ pressed during a draw repositions the new box at fixed size**, and releasing ⌘ resumes
   sizing (A3).
4. **Eight handles**: the four corners plus four edge midpoints, all resizing with a plain drag
   (A4).
5. **A click without a drag does nothing**. Only Esc cancels and Enter captures, which still
   reuses the remembered box instantly (A5).
6. **On-canvas mode cue and a hint that lists the gestures**, because Hammerspoon can't change
   the cursor (A6).
7. **A pure-helper busted spec**, plus a manual checklist for the Mac.

Then, if precision still falls short, add **arrow-key nudge and resize** (A7). Treat the
menu-bar/Dock/multi-monitor coverage (A8) as a separate small fix, after confirming on the Mac
that it matters. The core is about 100 changed lines in one file plus one new spec, and nothing
changes for `macscrot`, the upload hosts, or `#sshot`.

## Sources

- chezmoi repo (opened via `sase repo open chezmoi`): `home/dot_hammerspoon/screenshot_region.lua`,
  `home/dot_hammerspoon/init.lua`, `home/bin/executable_macscrot`, `home/sase/macros/sshot.yml`,
  `home/.chezmoiscripts/run_onchange_after_restart_hammerspoon.tmpl`, `Justfile`,
  `tests/hammerspoon/`; commits `1e4b71b9`, `a3c1e454`, `060dfcca`, `fde58338`, `8b00d930`.
- Hammerspoon source (opened via `sase repo open gh:Hammerspoon/hammerspoon`, HEAD `23e387e2`):
  `extensions/eventtap/libeventtap_event.m` (`getFlags`, `flagsChanged`),
  `extensions/mouse/libmouse.m` (cursor type is read-only), `extensions/canvas/libcanvas.m`,
  `extensions/screen/screen.lua` (`frame` vs `fullFrame`), `extensions/axuielement/axuielement.lua`.
- [Macworld: How to take better screenshot selections in macOS](https://www.macworld.com/article/233819/how-to-take-better-screenshot-selections-in-macos.html)
- [Macworld: Mac OS X screenshot secrets](https://www.macworld.com/article/215631/mac-os-x-screenshot-secrets.html)
- [screencapture(1) man page (leancrew mirror)](https://leancrew.com/all-this/man/man1/screencapture.html)
- [Photofocus: How to use marquee tools in Photoshop](https://photofocus.com/software/how-to-use-marquee-tools-in-photoshop/)
- [PetaPixel: 7 tricks for making basic selections in Photoshop](https://petapixel.com/2019/04/09/7-tips-for-making-basic-selections-in-photoshop/)
- [Shottr: How to take precise screenshots](https://shottr.cc/kb/precision)
- [Pie Menu: CleanShot X shortcuts (Capture Previous Area)](https://pie-menu.com/shortcuts/cleanshot)
- [skills.sh: CleanShot X URL scheme (`capture-previous-area`)](https://skills.sh/ljagiello/agent-skills/cleanshotx)
- [Apple: NSCursor](https://developer.apple.com/documentation/appkit/nscursor)
