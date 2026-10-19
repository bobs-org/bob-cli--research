# Screenshot selection: direct rectangle drawing with Command-drag movement

Independent research by **cdx**, 2026-10-19. No other researcher's report, transcript, or findings were consulted. This is research and an implementation recommendation; no screenshot configuration was changed or deployed.

The proposed interaction is a good fit for this tool. Extend the existing Hammerspoon selector so an ordinary drag can draw a replacement rectangle from inside the old selection as well as outside it, and require Command at the start of a movement gesture. Preserve corner handles for small corrections and Enter for capture. The main work is changing how a drag starts, with a few safeguards against accidental replacement.

**What the shortcut actually runs.**

The inspected chezmoi checkout is `bbugyi200/dotfiles` at commit `d90849608e4c4dc83286f08008cce541c4b119c2`. Its binding matches the requested Control-Shift-Option-S exactly. Hammerspoon invokes `ScreenshotRegion.pick`, and the confirmation callback invokes `~/bin/macscrot` with `x,y,w,h`. `macscrot` captures through `/usr/sbin/screencapture -R`, uploads to Apollo and Athena, and copies the screenshot's path to the clipboard. The clipboard contains a path, not the image. The selector is custom Lua code, not Apple's Screenshot toolbar. [Shortcut and callback](https://github.com/bbugyi200/dotfiles/blob/d90849608e4c4dc83286f08008cce541c4b119c2/home/dot_hammerspoon/init.lua#L14), [capture and upload script](https://github.com/bbugyi200/dotfiles/blob/d90849608e4c4dc83286f08008cce541c4b119c2/home/bin/executable_macscrot#L63).

The selector already has three drag modes. At mouse-down, it checks a corner handle first, the existing rectangle's interior second, and the rest of the selected screen last:

| Where an ordinary drag starts | Current behavior |
| --- | --- |
| Near an existing corner | Resize from that handle |
| Inside the existing rectangle | Move the rectangle without changing its size |
| Outside the rectangle, on the selector's screen | Draw a new rectangle between the starting and current pointer positions |

This explains the friction: a smaller target lying inside the remembered rectangle cannot be drawn directly. The geometry machinery for drawing it already exists. `normalizedRect` supports all four drag directions; `updateNewRegion` clamps the draft; `drag.mode` already separates movement, resizing, and new selection. The event handler never checks modifier flags. [Geometry](https://github.com/bbugyi200/dotfiles/blob/d90849608e4c4dc83286f08008cce541c4b119c2/home/dot_hammerspoon/screenshot_region.lua#L37), [new-region update](https://github.com/bbugyi200/dotfiles/blob/d90849608e4c4dc83286f08008cce541c4b119c2/home/dot_hammerspoon/screenshot_region.lua#L377), [gesture routing](https://github.com/bbugyi200/dotfiles/blob/d90849608e4c4dc83286f08008cce541c4b119c2/home/dot_hammerspoon/screenshot_region.lua#L421).

Other existing behavior matters when selecting an implementation:

- Opening restores `macscrotLastRegion` if it fits a connected screen; otherwise it creates a centered rectangle occupying about 60% of the chosen screen's width and height.
- Enter confirms, saves the coordinates, destroys the overlay, and schedules the callback after 80 ms. Mouse release ordinarily leaves the selector open.
- Escape cancels without overwriting the remembered coordinates.
- The four visible handles are 10 by 10 coordinate units, but their hit areas are 20 by 20.
- Starting a new selection immediately replaces the rectangle with at least 16 by 16. A release without reaching the three-unit movement threshold cancels the entire selector.
- Mouse-up clears the drag without applying that event's coordinates.

These are source observations, not assumptions about macOS defaults. [Initial region](https://github.com/bbugyi200/dotfiles/blob/d90849608e4c4dc83286f08008cce541c4b119c2/home/dot_hammerspoon/screenshot_region.lua#L97), [handle detection](https://github.com/bbugyi200/dotfiles/blob/d90849608e4c4dc83286f08008cce541c4b119c2/home/dot_hammerspoon/screenshot_region.lua#L276), [confirmation and cleanup](https://github.com/bbugyi200/dotfiles/blob/d90849608e4c4dc83286f08008cce541c4b119c2/home/dot_hammerspoon/screenshot_region.lua#L341), [release handling](https://github.com/bbugyi200/dotfiles/blob/d90849608e4c4dc83286f08008cce541c4b119c2/home/dot_hammerspoon/screenshot_region.lua#L453).

**Behavioral evidence and its limits.**

I executed the unmodified selector under Lua with stubbed Hammerspoon screen, canvas, settings, timer, and event-tap APIs. Each trace began with rectangle `(100,100,200,100)` on a `(0,0,1000,800)` screen. Confirmation used Enter after mouse-up where indicated.

| Trace | Observed result |
| --- | --- |
| Interior drag `(130,130)` to `(180,170)` | Confirmed `(150,140,200,100)`: movement |
| Same drag with `cmd=true` on mouse events | Identical result: modifiers currently make no difference |
| Outside drag `(500,500)` to `(650,575)` | Confirmed `(500,500,150,75)`: new rectangle |
| Same new rectangle drawn in reverse | Same confirmed rectangle |
| Click outside at `(500,500)`, no movement | Selector closed; nothing confirmed |
| Down `(500,500)`, drag `(600,550)`, up `(650,575)` | Confirmed `(500,500,100,50)`: last drag position wins over release position |

These probes corroborate the control flow and geometry. They do not establish real pointer-event delivery frequency, visual latency, permission behavior, Retina capture alignment, or live Mac configuration. I inspected the managed source from Linux and did not connect to the Mac. Confidence is high about the source-level cause and proposed routing change; the resulting feel still needs a brief Mac trial.

**Critique of the interaction proposal.**

Drawing between the desired corners removes the need to locate and adjust two old corners. It is particularly useful for a target nested inside the remembered selection. Retaining the remembered rectangle remains valuable for repeated screenshots of the same area: the user can still open the selector and press Enter immediately.

The cost is a learned-behavior change: an unmodified interior drag now replaces rather than moves. Command must therefore be visible in the on-screen instructions. Accidental clicks must be harmless, and re-selection should remain reversible until explicit confirmation. Expanding today's outside-drag behavior to the interior without fixing click cancellation would make this change unnecessarily frustrating.

Command is technically straightforward and respects the requested mapping. Hammerspoon exposes `event:getFlags().cmd` directly on events. Checking the mouse-down event gives the modifier state that belongs to that gesture; there is no need for a second global keyboard polling mechanism. [Hammerspoon event modifiers](https://www.hammerspoon.org/docs/hs.eventtap.event.html#getFlags).

Space is the strongest alternative. Apple's native region capture supports dragging a rectangle and holding Space during the drag to reposition it. It captures on release. That is useful precedent for the overall interaction, but it does not make Command wrong for this personal tool. [Apple's screenshot instructions](https://support.apple.com/en-us/102646).

I would use Command first. It avoids adding Space key-down/up state and temporary mid-drag transitions to a selector that currently has neither. A true Apple-style Space behavior would require rebasing pointer and rectangle anchors on entering and leaving movement mode, so the rectangle does not jump. Add it only if actual use shows a preference for that convention; do not implement two movement systems initially.

**Adjusted requirements, explicitly called out.**

1. **“Resize” means replace the rectangle from two chosen points.** Neither point needs to be an existing corner. Starting inside or outside the old selection should produce the same result, and all four directions must work.
2. **Keep ordinary corner-handle resizing as an exception.** This preserves fine adjustment after the initial draw. A literal “every unmodified drag creates a new rectangle” would require removing or changing those handles; that is a different tradeoff. The proposed contract is “drag the body or background to select; drag a visible handle to resize.” Avoid invisible edge-resize zones. Tighten today's oversized corner hit areas toward the visible handle footprint, and verify trackpad usability, so a nearby target corner is not unexpectedly intercepted.
3. **Command wins over handles.** Command-drag starting on the selection or one of its handles moves the whole rectangle. This avoids an unexpected resize when the user explicitly asked to move. Command-drag starting elsewhere is a consumed no-op, rather than a surprise new selection or a jump to the pointer.
4. **Choose the operation at mouse-down and retain it through mouse-up.** Command must be held when the gesture starts; releasing it early does not switch from moving to drawing. Pressing it halfway through a drawing gesture does not suddenly change modes. This is a deliberate simplification of “hold Command while dragging.”
5. **A click is not a new selection.** Save the pre-drag rectangle and wait for the existing three-unit movement threshold before replacing it. A click or tiny jitter leaves the old rectangle and selector intact. Escape remains the explicit cancellation action.
6. **Mouse release ends editing, not capture.** Apply the release event's position, then leave the rectangle available for inspection. Enter performs capture. Ignore Enter during an active mouse drag so the overlay cannot disappear while a button is still held.
7. **Keep the existing minimum size for the first change, but expose the limit.** The selector currently requires both dimensions to be at least 16 coordinate units. An undersized release should restore the previous rectangle and show a brief minimum-size hint, rather than silently capturing an inflated rectangle. Supporting thinner strips is a separate, small extension, not something to assume this change already solves.

The minimum-size rule is independent of the movement threshold: one identifies a deliberate drag; the other decides whether its rectangle is valid. During an in-progress draft, render the actual normalized bounds and guard decorative inset strokes against negative dimensions. Validate the final bounds on release. Do not reuse the current minimum-inflating `updateNewRegion` unchanged if adopting this rejection behavior.

**Options compared.**

| Approach | Benefits | Costs and fit |
| --- | --- | --- |
| Modify the existing Hammerspoon selector | Preserves remembered regions, confirmation, upload behavior, and the requested Command gesture; reuses existing geometry | Needs focused event-state tests and Mac verification; recommended |
| Use existing `macscrot` with no region argument | Its source already invokes native interactive `screencapture -i`; smallest route to native crosshair selection while retaining the script's downstream work | Bypasses this custom remembered-region preview and Enter-confirmation flow; native interaction does not implement the requested Command contract |
| Keep interior movement and add a dedicated “new selection” mode/key | Preserves existing movement muscle memory | Requires an extra action precisely where the user wants direct drawing; a reasonable fallback if accidental replacement proves common |
| Replace the selector with another application or a native app | Could supply richer editing or integrated magnification | Introduces migration and integration work without evidence the present tool is inadequate for this change |

The native alternative is worth knowing about because it is already wired into `macscrot`; there is no need to buy another tool to try that interaction. It is not my recommendation because remembered-region editing was intentionally added in commit `fde58338694f7d320be5dfac36d8c37ce8a62a78`, and the requested change can preserve it. [Original feature commit](https://github.com/bbugyi200/dotfiles/commit/fde58338694f7d320be5dfac36d8c37ce8a62a78), [interactive fallback](https://github.com/bbugyi200/dotfiles/blob/d90849608e4c4dc83286f08008cce541c4b119c2/home/bin/executable_macscrot#L73).

**Implementation shape.**

The production change belongs primarily in `home/dot_hammerspoon/screenshot_region.lua`. The shortcut, callback signature, settings key, and `macscrot` arguments can stay compatible.

At mouse-down, determine the handle once and record the start point and a copy of the rectangle. Route in this order:

```text
outside the selector's screen -> existing session-cancel behavior
Command + (inside selection or on handle) -> move
Command elsewhere -> no-op gesture
unmodified handle -> resize
otherwise -> pending new rectangle
```

For pending creation, retain the old rectangle until the movement threshold is crossed. Compute the draft from the original anchor and current pointer using min/abs normalization. Clamp endpoints in global screen coordinates before calculating the rectangle. On release, update from that event once more, accept a valid draft or restore the original, and clear the drag. Movement uses `startRegion + pointerDelta`; handle resizing uses the existing opposite-corner logic. Do not repeatedly mutate the movement anchor as events arrive.

Keep the existing event tap. It already receives left-button down, drag, up, and key-down events. Returning true consumes an event, so selection gestures should continue to be consumed rather than reaching the underlying application. Canvas callbacks are not needed to implement this change; their documented mouse tracking interface is different from the explicit dragged-event stream already in use. [Event-tap callback contract](https://www.hammerspoon.org/docs/hs.eventtap.html#new), [canvas mouse callbacks](https://www.hammerspoon.org/docs/hs.canvas.html#mouseCallback).

Update the instruction label with two short lines, for example:

```text
Drag to select · ⌘-drag to move · Corners resize
Enter to capture · Esc to cancel
```

The current hint is a fixed-width, single-line text element with clipping. Changing its string alone may hide the new gesture. Resize its background/text frame and test on a small screen. Keep the size readout useful; cursor changes or magnification can follow only if precision remains difficult.

Preserve cleanup before capture and the existing 80 ms delay. Preserve saving only on confirmation and cancellation without upload. Add a focused `tests/hammerspoon/screenshot_region_spec.lua` using the repository's established mocked-Hammerspoon style; the current `init_spec.lua` stubs out `screenshot_region` and does not exercise these gestures. The repository already runs this test directory via `just test-hammerspoon`. [Existing stub](https://github.com/bbugyi200/dotfiles/blob/d90849608e4c4dc83286f08008cce541c4b119c2/tests/hammerspoon/init_spec.lua#L330), [test recipe](https://github.com/bbugyi200/dotfiles/blob/d90849608e4c4dc83286f08008cce541c4b119c2/Justfile#L124).

**Screen boundaries and precision limits.**

The module uses `screen:frame()` for saved-region validation and the overlay. Hammerspoon defines this as the usable area excluding the menu bar and Dock; `fullFrame()` includes them. Consequently, the requested gesture change alone will not allow selecting every visible part of the display. If capturing those areas is desired, consistently change the selector's frame lookups to `fullFrame()` and test that separately. Do not change just the canvas while leaving saved-region validation and clamping on another frame. [Hammerspoon screen geometry](https://www.hammerspoon.org/docs/hs.screen.html#frame).

Only one screen hosts the current overlay. A valid remembered region can select a different display from the one under the pointer, and a mouse-down outside that screen cancels. Retain that policy for the first gesture change rather than quietly adding cross-display capture. If it causes friction in practice, choose a separate monitor policy deliberately. Preserve negative global coordinates for displays left of or above the primary display. Hammerspoon distinguishes logical points from native pixels; do not introduce Retina scale multiplication into the existing capture path without measuring the result. [Screen coordinates and scaling](https://www.hammerspoon.org/docs/hs.screen.html#availableModes).

These are limitations relevant to “a very specific rectangular space,” not reasons to replace the tool. Fine correction with handles remains useful even after direct drawing, and a pixel magnifier should be considered only after testing whether the new gesture actually leaves an accuracy problem.

**Validation before deployment.**

Automated coverage should test observable behavior through `pick`, the registered event callback, the rendered rectangle, settings writes, and the confirmation callback:

- New rectangles starting inside and outside the old selection, including a smaller nested rectangle and all four drag directions.
- Command movement preserving width/height, Command precedence on handles, Command outside no-op, and no mid-drag mode switching.
- Handle resizing with the opposite corner fixed; deterministic hit testing where small rectangles put handles close together.
- Click/jitter preservation, invalid-size rollback, final mouse-up coordinates, and screen-edge clamping with negative origins.
- Release not capturing; Enter confirming exactly once when idle; Enter during a drag ignored; Escape cancelling without settings or capture callbacks.
- Overlay/tap cleanup and confirmation occurring only after the deferred callback boundary.

Then run `just test-hammerspoon`, format the changed Lua files, and perform a real Mac smoke test with both mouse and trackpad. Capture a rectangle around known content, confirm that its edges match the PNG and that the overlay/hint is absent, repeat with the remembered region, and test Escape. Include Retina and an external display if available. The Lua probes in this report do not substitute for that visual test.

Deploy from chezmoi's source of truth. Its restart hook already hashes `screenshot_region.lua`, so a full apply/update on the Mac handles reloading the changed selector. A targeted `chezmoi apply ~/.hammerspoon` does not run the restart script; the repository documents the need for an explicit reload or full apply in that case. Follow the repository's required `chezmoi update -a --force` after the future implementation commit. No deployment was performed during this research. [Restart hook](https://github.com/bbugyi200/dotfiles/blob/d90849608e4c4dc83286f08008cce541c4b119c2/home/.chezmoiscripts/run_onchange_after_restart_hammerspoon.tmpl#L4), [deployment notes](https://github.com/bbugyi200/dotfiles/blob/d90849608e4c4dc83286f08008cce541c4b119c2/README.md#L31).

**Recommended solution.** Extend the existing Hammerspoon picker with ordinary drag-to-select on the body/background and Command-at-mouse-down drag-to-move. Retain visible corner handles for corrections, let Command override them, make clicks harmless, use the final release coordinates, and keep Enter as explicit capture confirmation. This directly solves the nested-rectangle problem while retaining the remembered-region and upload workflow. Treat Space movement, magnification, full-display bounds, and multi-monitor policy as separate decisions after a brief trial of the focused change.
