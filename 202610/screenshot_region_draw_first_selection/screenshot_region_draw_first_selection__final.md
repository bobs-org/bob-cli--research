# Screenshot region picker: drag to draw, ⌘-drag to move

- **Lead researcher:** consolidated from five independent reports (`cdx`, `cld`, `grk`,
  `mus`, `gem`) plus lead verification against the source and a Lua prototype
- **Date:** 2026-10-19
- **Code baseline:** chezmoi `d9084960` (picker last changed in `4375716e`); Hammerspoon
  source `23e387e2`
- **Question:** The `⌃⇧⌥S` screenshot selector makes you drag the old box's corners to
  frame a specific rectangle. Should a plain click-drag from one corner of the target to
  the other draw the box instead, with ⌘ held to move the box? Critique the plan, adjust
  the requirements where that is justified, and recommend an implementation.

## Recommendation in brief

**Build it.** All five researchers reached this verdict independently. The plan is a good
idea, and the change is small: about 40 changed lines in the event handler of
`home/dot_hammerspoon/screenshot_region.lua`, plus a new spec. `macscrot`, the hotkey,
the upload to apollo and athena, and the remembered region all stay unchanged.

The picker can already draw a new box. It does so only when the drag starts *outside*
the current box, and the box it preloads (your last capture, or 60% of the screen the
first time) usually covers the thing you want next. Your plan swaps the default. A plain
drag draws, and ⌘ is the explicit modifier for the rarer move.

Your plan needs these adjustments to work well. Each is listed in [§4](#4-requirement-adjustments):

1. **⌘ moves the box from anywhere, and ⌘ wins over the corner handles.** You don't have
   to grab the box. Small boxes stay movable even though their handle zones cover most of
   their interior.
2. **Corner handles keep resizing on a plain drag**, with a tighter hit area than today.
3. **A click, or a tiny accidental drag, does nothing.** Today a click on the dimmed area
   closes the picker. After the change only Esc cancels.
4. **Releasing the mouse never captures.** Enter captures, as it does today.
5. **⌘ only counts if it is held when you press the mouse button** (for v1).
6. **The hint must teach the new gestures.**

Keep the modifier you chose. Don't switch to Space (one researcher's proposal) and don't
add right-drag. Arrow-key nudging is the best follow-up if a trial shows that precision
is still a problem. Edge handles, a ⌘-held color cue, and mid-drag repositioning can wait
until a trial shows a need.

## 1. What the shortcut runs today

All five reports agree on the facts below, and I re-checked each one in the source.

| Stage | Where | What it does |
| --- | --- | --- |
| Hotkey | `home/dot_hammerspoon/init.lua:42-46` | `hs.hotkey.bind({ "ctrl", "alt", "shift" }, "s", …)` → `ScreenshotRegion.pick(runMacscrot)` |
| Selector | `home/dot_hammerspoon/screenshot_region.lua` (501 lines) | Full-screen `hs.canvas` at `screenSaver` level: a dimmed surround, a blue box, four corner handles, a `W x H` label, and the hint "Drag to adjust \| Enter to capture \| Esc to cancel". One `hs.eventtap` swallows mouse-down, drag, mouse-up, and key-down events. |
| Memory | `hs.settings` key `macscrotLastRegion` | The last box you *confirmed*. It is saved on Enter only and preloaded on the next open. |
| Capture | `home/bin/executable_macscrot` | `screencapture -R x,y,w,h` → PNG, uploaded to apollo and athena in parallel; the **path** (not the image) goes to the clipboard. With no region argument it falls back to native `screencapture -i`. |
| Deploy | `home/.chezmoiscripts/run_onchange_after_restart_hammerspoon.tmpl` | Already hashes `screenshot_region.lua`, so a full `chezmoi update`/apply on the Mac restarts Hammerspoon. |

**History.** On 2026-06-28 you tried the native Screenshot toolbar
(`screencapture -U -J selection`, `a3c1e454`) and reverted it two minutes later
(`060dfcca`). The commit message gives no reason. Eight minutes after that you added this
picker (`fde58338`, "remember screenshot capture region"). The picker exists so that
hotkey → Enter recaptures the last box. Any change must keep that working.

**Current gesture map.** The mouse-down handler, lines 422-451, applies the first rule
that matches:

| Mouse-down lands… | Current result |
| --- | --- |
| Within ±10 pt of a corner (`handleAt`: a 20×20 zone around a 10×10 visible handle) | Resize from that corner |
| Inside the box | **Move** the box |
| Outside the box, on the overlay's screen | **Draw** a new box from the press point. The old box is replaced *immediately* by a 16×16 stub (line 447). |
| Outside, then release with < 3 pt movement | **Close the picker** (lines 476-478) |
| On another screen | Close the picker |

**Why framing a specific rectangle is painful.** Your target is usually *inside* the
remembered box, so the natural corner-to-corner drag moves the box instead of drawing.
The only remaining tool is the corner handles. Nothing on screen tells you which mode a
press will get. Hammerspoon cannot set the cursor: `hs.mouse` only reads
`currentSystemCursor` (`extensions/mouse/libmouse.m:326`). The canvas ignores mouse
events by default (`libcanvas.m:891`), so the cursor you see is probably whatever the app
underneath shows. The hint never mentions drawing.

### Verified by execution

I ran the unmodified module under Lua with stubbed Hammerspoon screen, canvas, settings,
timer, and event-tap APIs on a 1000×800 screen. I also ran a prototype of the routing
recommended in §6. `cdx` ran a similar harness independently and got matching results for
the current behavior.

| # | Trace (old box `100,100,600,400` unless noted) | Today | Prototype |
| --- | --- | --- | --- |
| 1 | Plain drag inside the box, (200,200)→(350,280) | box **moved** → `250,180,600,400` | **new box** `200,200,150,80` |
| 2 | The same drag in reverse | box moved → `0,20,600,400` | same new box `200,200,150,80` |
| 3 | ⌘-drag inside the box, +50,+40 | moved (⌘ ignored) | moved → `150,140,600,400` |
| 4 | ⌘-drag starting outside the box, +50,+40 | **new 50×40 box** | moved → `150,140,600,400` |
| 5 | ⌘-drag from the small gap between the handles of a 24×24 box | moved (an inside drag, so ⌘ didn't matter) | moved |
| 6 | Plain drag on the SE handle | resized → `100,100,550,350` | same |
| 7 | Click inside, no movement | open, box unchanged | same |
| 8 | Click outside, no movement | **picker closed** | open, box unchanged |
| 9 | Release point differs from the last drag event | release point ignored | release point applied |
| 10 | Enter pressed while still dragging | captures mid-drag | Enter ignored until release |
| 11 | Plain drag starting 6 pt from the old NW corner | **resizes** NW corner | **resizes** NW corner (see R2) |
| 12 | ⌘-press on the NW handle of a 24×24 box | **collapses to 16×16** | moved → `500,340,24,24` |
| 13 | Accidental 8 pt drag inside the box | box moved by 6,5 | rolled back, box unchanged |
| 14 | Deliberate 300×8 strip | (moves the box) | `200,200,300,16` (raised to the 16 pt minimum) |

These traces confirm the control flow and geometry. They say nothing about how it feels,
how frequently pointer events arrive, trackpad behavior, or Retina alignment. Those need
a short trial on the Mac.

## 2. Is this a good idea?

Yes. All five reports agree, for these reasons:

- **Put the modifier on the rare action.** "Frame this new thing" is the common job.
  Recapturing the same box is already one key (Enter). Moving a box at the same size is
  the least common job, so it gets the modifier.
- **It removes a rule you can't see.** "Inside means move" works in Photoshop and in
  macOS ⌘⇧5 because the cursor changes shape over the selection. This overlay can't
  change the cursor, so a modifier is more predictable than a location boundary.
- **⌘ is the right modifier.** ⌃-click is right-click. ⇧ and ⌥ already mean "lock an
  axis" and "resize from the center" in native ⌘⇧4. ⌘ isn't part of the `⌃⇧⌥S` trigger.
  Every mouse event carries modifier state, so `event:getFlags().cmd` on mouse-down is
  enough (`libeventtap_event.m:416-424`) and no keyboard state tracking is needed. No
  window manager with modifier-drag (yabai, AeroSpace, BetterTouchTool) is configured in
  chezmoi, and the tap swallows the ⌘-click anyway.
- **It keeps everything the picker exists for**: the remembered box, Enter to confirm,
  the size readout, handle fine-tuning, and the `macscrot` contract.

**Gaps in the plan as written.** Each of these became an adjustment in §4.

- It doesn't say what a drag that starts on a **handle** does.
- It doesn't say what a **click without a drag** does. Under draw-first, today's "click
  outside closes the picker" rule would fire on every twitch.
- It doesn't say **when the old box gets replaced**. Today the replacement happens on
  mouse-down.
- It doesn't settle **"hold ⌘ while dragging"**: ⌘ held at press, or ⌘ pressed partway
  through?
- It doesn't mention **discoverability**. The hint still teaches the old behavior.

**The cost.** You lose two learned behaviors: a plain drag inside the box no longer moves
it, and a click on the dimmed area no longer closes the picker. Both are easy to re-learn
once the hint says so.

## 3. Where the reports disagreed, and how I resolved them

| Question | Positions | Resolution |
| --- | --- | --- |
| **Move modifier** | ⌘ (`cdx`, `cld`, `grk`, `gem`). Space first with a ⌘ alias (`mus`). Add right-drag (`gem`). | **⌘ only.** `mus`'s muscle-memory argument doesn't carry over. In native ⌘⇧4, Space repositions the *in-progress* box during a drag, which releases into a capture. Pressing Space *before* the drag switches to window-capture mode. Neither matches "move a box that is already drawn." Space also isn't a modifier flag, so it needs key-down/key-up tracking with autorepeat and a stuck-key risk. Right-drag on a MacBook trackpad is a two-finger press-and-drag, which is awkward. Two aliases also make the hint longer. |
| **Where ⌘-drag works** | Inside the box only (`gem`, `mus`). Anywhere (`cld`, `grk`). On the box or a handle, but a no-op elsewhere (`cdx`). | **Anywhere on the overlay's screen.** The move uses the drag delta, so you don't need to hit the box. That matters most when the box is small or partly off where you're looking. ⌘ has no other meaning here, so nothing is lost. |
| **⌘ vs. handles** | Handles win (`grk`, `mus`, `gem`). ⌘ wins (`cdx`, `cld`). | **⌘ wins.** A handle zone extends 10 pt inward from each corner. Together the four zones cover 25% of a 40×40 box, 44% of a 30×30 box, and all of a 20×20 box. If handles won, ⌘-drag on a small box would resize it. Trace 12 shows the box collapsing to 16×16. Letting handles win gains nothing, because a plain drag on a handle already resizes. |
| **Click with no drag** | Does nothing (`cdx`, `cld`, `gem`). Does nothing inside the box but closes the picker outside it (`grk`). Always closes the picker (`mus`). | **Does nothing, anywhere.** Under draw-first, every spot on the screen is a place you might start a drag. A twitch shouldn't throw away a box you've been adjusting. Esc is the one way to cancel. This also leaves a plain click free for a later "click selects the window" feature (`cld`). |
| **⌘ pressed partway through a drag** | Lock the mode at mouse-down (`cdx`, `grk`, `mus`). ⌘ pressed mid-draw repositions the new box (`cld`). Space mid-drag repositions it (`grk` ADJ-5, `gem`). | **Lock the mode at mouse-down for v1.** Mid-drag repositioning is essential in ⌘⇧4 *because releasing the mouse captures*. Here release only ends the drag, so a misplaced start is fixed afterwards with ⌘-drag or a handle. If you ever want it, map it to ⌘, not Space. Drag events carry live modifier flags, so it needs no extra key tracking (`cld` §4.2). |
| **Undo (⌘Z)** | Needed in v1 (`grk`). Not mentioned by the others. | **Not needed.** Esc followed by the hotkey already restores your last *confirmed* box, because the box is saved only on Enter. The only thing lost is unconfirmed fiddling. |
| **Arrow keys / edge handles** | Arrows in v1 (`grk`). Arrows in phase 2 with edge handles in v1 (`cld`). Edge handles in v1.1 (`grk`). Neither mentioned (`cdx`, `mus`, `gem`). | **Neither goes in v1.** Arrow nudges are the first follow-up if precision still falls short. Edge handles add more hit zones that steal draw starts (see R2), so wait for evidence. |

## 4. Requirement adjustments

These are explicit changes to what you asked for, or clarifications of it.

| # | Your requirement / today | Adjusted requirement | Why |
| --- | --- | --- | --- |
| **R1** | Click-drag from corner to corner resizes the area | **Kept, clarified.** "Resize" means *replace the box using the two points you drag between*. A drag can start inside or outside the old box and go in any direction. The only exception is a press on a handle (R2). | This is the core fix (traces 1 and 2). |
| **R2** | Today you have to drag the corners | **Corner handles keep resizing on a plain drag**, but their hit zone shrinks from ±10 pt to about ±6 pt (the visible handle is ±5 pt). | Handles are still the fine-adjustment tool. They also steal a new draw that starts near an old corner (trace 11), which is likely when you recapture nearly the same thing. A tighter zone shrinks that conflict. If it still bites, start the draw from the opposite corner. Check the zone size on the trackpad. |
| **R3** | Hold ⌘ while dragging to move the area | **⌘ held at mouse-down moves the box, from anywhere on the overlay, and overrides the handles.** | §3, rows 2-3 (traces 4 and 12). |
| **R4** | "Hold ⌘ while dragging" | **The mode is locked at mouse-down for v1.** Releasing ⌘ mid-move doesn't switch to drawing, and pressing it mid-draw doesn't switch to moving. | Simple and predictable. §3, row 5. |
| **R5** | Today a click outside the box closes the picker | **A click with no drag does nothing, anywhere. Only Esc cancels.** | §3, row 4 (trace 8). |
| **R6** | Today the old box is replaced on mouse-down | **The old box stays until the drag passes 3 pt.** If you release a draw that is under 16 pt in *both* directions, the old box comes back. | A misclick or jitter can't destroy a remembered box (trace 13). A deliberate thin strip still works, raised to the existing 16 pt minimum (trace 14). |
| **R7** | (implicit) | **Releasing the mouse never captures. Enter captures, and is ignored while the button is held. The release point is applied.** | This keeps draw → adjust → Enter and hotkey → Enter. It also fixes two small bugs that traces 9 and 10 show. |
| **R8** | (none) | **Rewrite the hint as two lines**, for example `Drag: new box · ⌘-drag: move · Corners: resize` and `Enter: capture · Esc: cancel`. Make the hint frame taller and wider to fit. | The current hint is one 348 × 24 pt clipped line that says "Drag to adjust". Changing only the string would clip the new text. |
| **R9** | (implicit) | **Everything downstream stays the same**: the hotkey, the `macscrot x,y,w,h` format in screen points, the upload, the clipboard path, and saving the box only on Enter. | `macscrot` and `#sshot` need no changes. |

**Out of scope for v1 (by consensus):** ⇧ to constrain or make a square, ⌥ to draw from
the center, a zoom loupe, snapping to windows or accessibility elements, capture on
release, and a second hotkey.

## 5. Alternatives considered

| Alternative | Verdict |
| --- | --- |
| **Keep the behavior, but fix the hint ("drag outside to draw")** | Still a location rule you can't see. A large remembered box leaves little "outside" near the target. |
| **Reverse it: a plain drag moves, ⌘-drag draws** | Puts the modifier on the common action. |
| **Space, or right-drag, as the move gesture** | Rejected. See §3, row 1. |
| **Capture on release, like ⌘⇧4** | Fastest for a one-off, but it removes handle fine-tuning and dimension checks, and it breaks hotkey → Enter recapture. |
| **Show the remembered box as a "ghost", then let a drag commit a real one** (`grk` B) | After the first draw, interior drags move again, and the original problem comes back. |
| **Shrink or expire the remembered box** | Fixes only the first open. One large capture brings the problem back, and it weakens the feature the picker exists for. |
| **Two hotkeys, "repeat last area" and "new area"** (CleanShot-style) | Another chord to remember, and you can't see the old box before you decide. Draw-first gives you both in one overlay. |
| **Separate move/draw modes on letter keys** | Modal state you have to track. A held modifier is better. |
| **Native `screencapture -i` or `-U -J selection`** | The native crosshair is already the no-argument path in `macscrot`. It can't remember a box, and the toolbar route was tried and reverted. |
| **Buy CleanShot X or Shottr** | Polished zoom and snapping, but paid, and it bypasses the `macscrot` upload, clipboard, and `#sshot` flow. Too much churn for a gesture problem. |

**What would change the recommendation:** if a trial shows that you move the preloaded
box more often than you redraw it, flip the default back. Don't add a setting for both
behaviors.

## 6. Implementation sketch

All production changes are in `home/dot_hammerspoon/screenshot_region.lua`. No new Lua
module is needed. (A new module would also need a hash line in the restart hook, and
`tests/bash/hammerspoon_restart_hook_test.sh` enforces that.) The event tap's event mask
does not change.

**Mouse-down routing** (replaces lines 428-449). It does not touch `region`:

```lua
local flags = event:getFlags() or {}
local handle = handleAt(point, region)        -- with the tighter hit zone (R2)
if flags.cmd then
  drag = { mode = "move", startPoint = point, startRegion = copyRect(region) }
elseif handle then
  drag = { mode = "resize", handle = handle, startRegion = copyRect(region) }
else
  drag = { mode = "new", anchor = point, moved = false, startRegion = copyRect(region) }
end
return true
```

The existing off-screen check stays above this: a press on another display still closes
the picker.

**Shared drag step.** Mouse-drag and mouse-up both call this, so the release point is
applied (R7):

```lua
local function applyDrag(p)
  if drag.mode == "move" then
    region = clampRegionToFrame({ x = drag.startRegion.x + p.x - drag.startPoint.x,
      y = drag.startRegion.y + p.y - drag.startPoint.y,
      w = drag.startRegion.w, h = drag.startRegion.h }, screenFrame)
  elseif drag.mode == "resize" then
    region = resizeFromHandle(drag.startRegion, drag.handle, p, screenFrame)
  elseif drag.mode == "new" then
    drag.moved = drag.moved or math.abs(p.x - drag.anchor.x) >= 3 or math.abs(p.y - drag.anchor.y) >= 3
    if drag.moved then updateNewRegion(drag.anchor, p) end
  end
end
```

**Mouse-up.** Run `applyDrag(point)`. If the drag was a draw that never moved, or is
under `MIN_SIZE` in both directions, restore `drag.startRegion` (R5, R6). Then redraw and
clear `drag`. The `finish(false)` on an unmoved click goes away.

**Enter.** If `drag` is set, swallow the key and return. Otherwise behave as today, with
the same 80 ms delay and saving only on confirm.

**Hint.** Use the two-line text from R8, with a taller and wider hint frame. Check it on
the smallest screen you use.

My prototype of this routing (the four parts above, without the R2 hit-zone change or
the R8 hint) produced the right-hand column of the §1 table. It changes about 40 lines.

**Tests.** `tests/hammerspoon/init_spec.lua` stubs out the whole picker, so nothing
exercises these gestures today. Add `tests/hammerspoon/screenshot_region_spec.lua`.
Either drive `pick()` through a stubbed `hs.eventtap.new` callback, which is how the
probes above ran, or test extracted pure helpers (`classifyMouseDown`, `applyDrag`)
following `ping_window_spec.lua`. Cover:

- a plain drag inside, outside, and reversed;
- ⌘-drag inside, outside, and on the handle of a tiny box;
- a plain handle resize;
- a click and a sub-16 pt jitter, both leaving the box unchanged;
- the release point being applied;
- Enter ignored during a drag, and Enter/Esc otherwise unchanged;
- clamping at the screen edges with negative origins.

Run `just test-hammerspoon` and `just fmt-lua`. On the Mac, try mouse and trackpad:

- draw inside the old box;
- ⌘-drag;
- a corner handle;
- a stray click;
- Esc, then Enter on the remembered box;
- check that the PNG's edges match the box and the overlay doesn't appear in the PNG.

**Deploy.** Commit in chezmoi, then run `chezmoi update -a --force` (repo rule). On the
Mac, the restart hook reloads Hammerspoon. A targeted `chezmoi apply ~/.hammerspoon` does
not run the hook.

## 7. Limits outside the gesture change

These limit "any specific rectangle", but they are separate fixes. Keep them out of the
gesture commit.

- **The menu bar and Dock can't be captured.** The picker uses `screen:frame()`, which
  excludes them, for the canvas, for clamping, and for checking the saved box. A press on
  the menu bar closes the picker. To fix this, switch all three to `fullFrame()`
  consistently (`cdx`, `cld`).
- **Multiple displays: the picker can get stuck on one display.** `loadInitialRegion`
  opens the overlay on the screen that holds the *saved* box, not the screen under the
  pointer. A press on any other screen closes the picker. So after one capture on
  display B, the hotkey can't select anything on display A until the saved box becomes
  invalid. On the MacBook alone this never comes up. If you dock, the fix is about five
  lines: prefer the pointer's screen, and preload the saved box only if it is on that
  screen. (Lead finding. `cld` and `grk` noted that the saved box's screen wins, but not
  that this leaves no way out.)
- **The minimum size is 16 pt** (32 px on Retina) in both directions. That is fine for
  almost everything, including a single line of text.
- **No cursor feedback is possible** without a canvas-drawn crosshair. Add one only if
  the hint isn't enough.

## 8. Recommended solution

**Keep the Hammerspoon picker and its remembered box → `macscrot` pipeline, and change it
to draw-first with ⌘ to move**, all in `home/dot_hammerspoon/screenshot_region.lua`:

1. **A plain drag anywhere draws a new box** from the press point to the release point,
   inside or outside the old box, in any direction. The old box is replaced only after
   the drag passes 3 pt, and it comes back if the result is under 16 pt both ways.
2. **⌘ held at mouse-down moves the box from anywhere on the overlay, and wins over the
   handles.** The mode stays locked until release.
3. **Corner handles still resize on a plain drag**, with a tighter ±6 pt hit zone.
4. **A click does nothing. Esc cancels. Enter captures, and is ignored mid-drag.** The
   release point is applied, and hotkey → Enter still recaptures the remembered box.
5. **A two-line hint** names the drag, ⌘-drag, and corner gestures.
6. **A new `screenshot_region_spec.lua`** covering the traces in §1, plus a short Mac
   checklist.

After about a week of real use, add the first follow-up that you turn out to need:

- arrow-key nudge (1 pt, ⇧ for 10 pt; ⌥ for resizing) for pixel-exact finishing;
- edge handles;
- a ⌘-held outline color cue (needs a pass-through `flagsChanged` event);
- ⌘ pressed mid-draw to reposition the box.

Fix full-frame capture and the multi-display issue (§7) separately, if they ever matter.

## Sources

- chezmoi `d9084960` (opened via `sase repo open chezmoi`):
  `home/dot_hammerspoon/screenshot_region.lua`, `home/dot_hammerspoon/init.lua`,
  `home/bin/executable_macscrot`,
  `home/.chezmoiscripts/run_onchange_after_restart_hammerspoon.tmpl`, `Justfile`
  (`test-hammerspoon`, `fmt-lua`), `tests/hammerspoon/`; commits `a3c1e454`, `060dfcca`,
  `fde58338`, `4375716e`.
- Hammerspoon `23e387e2` (opened via `sase repo open gh:Hammerspoon/hammerspoon`):
  - `extensions/eventtap/libeventtap_event.m`: `getFlags` with `cmd`, and the
    `flagsChanged` event type;
  - `extensions/mouse/libmouse.m:326`: the cursor can be read but not set;
  - `extensions/canvas/libcanvas.m:891, 2691-2735`: canvases ignore mouse events by
    default.
- [Hammerspoon `hs.eventtap.event` docs](https://www.hammerspoon.org/docs/hs.eventtap.event.html);
  [`hs.screen` frame vs fullFrame](https://www.hammerspoon.org/docs/hs.screen.html#frame);
  [Hammerspoon #2425 (canvas cursor)](https://github.com/Hammerspoon/hammerspoon/issues/2425).
- [Apple: Take a screenshot on Mac](https://support.apple.com/en-us/102646) (⌘⇧4 drag;
  Space while dragging moves the box; ⌘⇧5 remembered selection).
- [Macworld: better screenshot selections](https://www.macworld.com/article/233819/how-to-take-better-screenshot-selections-in-macos.html)
  (Space, Shift, and Option modifiers).
- [Shottr precision guide](https://shottr.cc/kb/precision);
  [Flameshot](https://github.com/flameshot-org/flameshot) (arrow nudges);
  [ScreenCoord](https://brettterpstra.com/projects/screencoord/) (an overlay that outputs
  `screencapture -R` points); [CleanShot "Capture Previous Area"](https://pie-menu.com/shortcuts/cleanshot).
  These were cited by the researcher reports; I did not re-fetch them.
- Researcher reports (same directory): `__cdx`, `__cld`, `__grk`, `__mus`, `__gem`.
- Lead verification: a Lua 5.x harness with stubbed `hs.*`, run against the unmodified
  module and against a prototype of §6 (scratch files only; chezmoi was not modified).
