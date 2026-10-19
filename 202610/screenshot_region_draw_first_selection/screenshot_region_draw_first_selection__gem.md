# Research: Drag-to-Resize and Move Ergonomics for Hammerspoon Screenshot Region Selector

**Date:** 2026-10-19  
**Researcher:** `research.50.gem`  
**Target File:** `home/dot_hammerspoon/screenshot_region.lua` (in linked repo `chezmoi`)  
**Trigger Hotkey:** `<ctrl+shift+opt+s>` (`home/dot_hammerspoon/init.lua`)

---

## 1. Executive Summary

This research investigates the screenshot workflow triggered by `<ctrl+shift+opt+s>` in the user's `chezmoi` repository, critiques the proposed plan to enable corner-to-corner drag-to-resize by default with `<cmd>`-gated box movement, evaluates alternative interaction patterns, and provides a concrete implementation blueprint.

### Key Conclusions:
1. **The Plan is a Strong, High-Value Idea:**  
   The user's intuition is spot on. The current implementation in `screenshot_region.lua` suffers from an inverted affordance hierarchy: clicking inside the preloaded capture rectangle defaults to translating (`mode = "move"`), while creating a new rectangle (`mode = "new"`) is only possible by initiating a drag from *outside* the preloaded rectangle. Because the preloaded region is typically large (defaulting to 60% of the screen or the previous capture window), target rectangular regions almost always lie inside the existing box. Users are thus trapped into dragging small 10×10 corner handles to frame new selections.

2. **Crucial Plan Refinements:**  
   A naive implementation of Bryan's proposal would introduce subtle UX regressions. Specifically, five adjustments are recommended:
   - **Deferred Canvas Mutation:** Do not collapse the existing rectangle to an anchor point on `leftMouseDown`. Only switch to `mode = "new"` after the mouse exceeds a drag threshold (e.g., 3–5 pixels). This prevents accidental clicks from destroying the preloaded box.
   - **Eliminate Click-to-Cancel:** In the current code, releasing a click without moving cancels the entire session. This must be removed; `Esc` should remain the explicit cancellation mechanism.
   - **Dual Move Trigger (`Cmd` + Drag and Right-Click Drag):** Support `<cmd>` + Left Drag, but also support Right-Click Drag inside the box. Right-click drag requires no keyboard hand, providing effortless one-handed trackpad/mouse repositioning.
   - **Keep Two-Phase Capture ("Enter to Capture"):** Keep the requirement of pressing `Enter` to confirm rather than auto-capturing on mouse-up. This preserves handle fine-tuning, dimension inspection, and the zero-keystroke "repeat last capture" workflow.
   - **Updated On-Screen Hint:** Update the floating hint bar to reflect the new controls: `"Drag corner-to-corner to select | ⌘-Drag to move | Enter to capture | Esc to cancel"`.

---

## 2. Architecture and Root-Cause Analysis

### 2.1 The Current Pipeline
The screenshot subsystem spans three coordinated components in `chezmoi`:
1. **`home/dot_hammerspoon/init.lua` (lines 42–46):**
   ```lua
   hs.hotkey.bind({ "ctrl", "alt", "shift" }, "s", nil, function()
       ScreenshotRegion.pick(function(region)
           runMacscrot(region)
       end)
   end)
   ```
2. **`home/dot_hammerspoon/screenshot_region.lua`:**
   - Preloads the last confirmed capture rectangle from `hs.settings.get("macscrotLastRegion")` (or a 60% screen centered box if unset).
   - Displays a fullscreen `hs.canvas` overlay (level `"screenSaver"`) that dims the surrounding screen, leaves the selection unshaded, draws a blue border with 4 corner handles (`nw`, `ne`, `sw`, `se`), shows a dimension badge (`W x H`), and displays a hint bar (`"Drag to adjust | Enter to capture | Esc to cancel"`).
   - Manages mouse and keyboard events via an `hs.eventtap`.
   - On confirmation, persists the rectangle and invokes the completion callback with `{x, y, w, h}`.
3. **`home/bin/executable_macscrot` (lines 78–82):**
   - Invokes macOS native screencapture with the exact rectangle:
     ```bash
     /usr/sbin/screencapture -R "$capture_region" -t png "$local_path"
     ```
   - Concurrently uploads the PNG to tailnet hosts `apollo` and `athena`, copies the path to macOS clipboard (`pbcopy`), and triggers a native notification.

### 2.2 Why Dragging Corners is Currently Required
Commit `fde58338` ("feat: remember screenshot capture region", June 2026) introduced region memory so users could repeat captures without redrawing. However, lines 428–450 of `screenshot_region.lua` implement mouse-down hit testing in this strict order:

```lua
local handle = handleAt(point, region)
if handle then
    drag = { mode = "resize", handle = handle, startRegion = copyRect(region) }
elseif pointInRect(point, region) then
    drag = { mode = "move", startPoint = point, startRegion = copyRect(region) }
else
    drag = { mode = "new", anchor = point, moved = false }
    updateNewRegion(point, point)
    redraw()
end
```

#### The UX Breakdown:
1. **Precedence of `pointInRect` over `mode = "new"`:**  
   If the user spots a UI element (e.g. a dialog, a button, a 300×200 code block) and tries to click at its top-left corner and drag to its bottom-right corner, the click almost invariably falls inside the preloaded region. Because `pointInRect(point, region)` evaluates to `true`, the utility enters `mode = "move"`. The existing box begins translating across the screen instead of drawing a new box.
2. **High Friction Workaround:**  
   To escape `mode = "move"`, the user cannot click and drag directly over their subject. They are forced to:
   - Identify which of the 10×10 px corner handles is closest.
   - Drag handle 1 (e.g., NW) to the top-left of the target area.
   - Drag handle 2 (e.g., SE) to the bottom-right of the target area.
   - If the aspect ratio or position was skewed, adjust the remaining handles.
3. **The Click-to-Cancel Trap (lines 476–478):**  
   ```lua
   if drag and drag.mode == "new" and not drag.moved then
       finish(false)
   end
   ```
   If a user attempts to click outside the box to clear it or start fresh, but releases without moving at least 3 pixels (`not drag.moved`), the selector aborts and closes the overlay entirely.

---

## 3. Critique of Bryan's Proposed Plan

### 3.1 Proposed Model
- **Primary action (unmodified Left-Click Drag anywhere):** Click corner A and drag to corner B to define a new capture rectangle.
- **Secondary action (`<cmd>` + Left-Click Drag inside region):** Move/translate the existing rectangle.
- **Corner handles:** Preserved for micro-adjustments.

### 3.2 Strengths
1. **Restores the Primary Mental Model:** In any screenshot utility (macOS `Cmd+Shift+4`, CleanShot X, Shottr), the fundamental user intent when activating the tool is *selection by dragging*. Making selection the unmodified default everywhere eliminates cognitive dissonance.
2. **Preserves the Core Value of Region Memory:** Remembering the last region is primarily useful for *repeating* captures (press hotkey -> hit `Enter`). In Bryan's plan, that workflow remains 100% intact: if the preloaded box is already where you want it, you press `Enter` immediately without touching the mouse.
3. **Preserves Nudge and Handle Fine-Tuning:** Corner handles remain available when the user wants to adjust an edge by 1–2 pixels without redrawing the entire box.
4. **Clean Capture Area:** Unlike tools that place an intrusive "move handle" or title bar in the middle of the screenshot area, holding `<cmd>` keeps the interior transparent and unobstructed.

### 3.3 Pitfalls, Hazards, and Edge Cases
If implemented naively, Bryan's proposal introduces several potential regressions that must be addressed:

| Hazard / Edge Case | Mechanism in Current Code | Consequence | Required Refinement |
| :--- | :--- | :--- | :--- |
| **Premature Region Destruction** | `updateNewRegion(point, point); redraw()` on `leftMouseDown` | Clicking inside the box instantly collapses the preloaded region into a 16×16 px dot before the user has dragged. | **Drag Hysteresis:** Do not change `region` on mouse down. Record `drag = { mode = "new", anchor = point, moved = false, originalRegion = copyRect(region) }`. Only mutate `region` when `dx >= 3` or `dy >= 3`. |
| **Accidental Click-to-Cancel** | `if not drag.moved then finish(false) end` | A click without drag would abort the entire session and dismiss Hammerspoon's overlay. | **Remove Click-to-Cancel:** Releasing without dragging should simply restore `originalRegion` and leave the session open. Only `Esc` cancels. |
| **Ergonomics of `<cmd>`** | The launch hotkey is `Ctrl+Shift+Opt+S` | Left hand fingers are on `Ctrl`, `Shift`, `Opt`. Reaching for `Cmd` to move requires shifting hand position. | **Dual Triggers:** Support `Cmd` + Left Drag, but also support **Right-Click Drag** inside the box (requires zero keyboard involvement). |
| **Mouse-Up Capture vs. Confirmation** | Native macOS captures immediately on mouse-up | Releasing mouse-up could capture prematurely before user checks dimensions or alignment. | **Keep Enter-to-Capture:** Keep the current model where releasing the mouse leaves the new box and handles active until `Enter` is pressed. |

---

## 4. Evaluation of Alternative Approaches

### Alternative 1: Direct Fallback to macOS `screencapture -i`
- **Concept:** Bypass Hammerspoon's custom selector and let `macscrot` run `/usr/sbin/screencapture -i` directly.
- **Why it was replaced in June 2026:** Native `screencapture -i` cannot remember the previous rectangle, provides no dimension display, does not support post-drag handle adjustments, and cannot be repositioned after drawing.
- **Verdict:** Inferior. Losing region memory and post-drag inspection is too steep a penalty.

### Alternative 2: Modal Mode Switcher (e.g., Press `M` for Move, `R` for Redraw)
- **Concept:** Pressing `M` puts the overlay into Move mode; pressing `R` or `D` puts it into Draw mode.
- **Critique:** Introduces modal state overhead. Users forget which mode is active, make mistakes, and have to remember extra keys. Spring-loaded modifiers (holding a key or using right-click) are provably superior to modal toggles.
- **Verdict:** Rejected.

### Alternative 3: Visual Move Bar / Center Drag Icon
- **Concept:** Render a small translucent "grip" icon or top title bar inside the rectangle that can be dragged to move the box.
- **Critique:** Any visual artifact placed inside or immediately bordering the rectangle obscures the text/graphics the user is attempting to capture.
- **Verdict:** Rejected.

### Alternative 4: Bryan's Proposed Modifier Approach with Recommended Adjustments
- **Concept:** Unmodified drag draws a new region; `Cmd` + Left Drag OR Right-Click Drag translates the box; corner handles resize; hysteresis prevents accidental erasure.
- **Verdict:** **Recommended Solution.**

---

## 5. Justified Adjustments to the Requirements

Below are the explicit adjustments to Bryan's original requirements:

### Adjustment 1: Drag Threshold Hysteresis (Non-Destructive Mouse Down)
- **Rationale:** If unmodified click anywhere begins a new selection, clicking down must NOT immediately wipe out the preloaded region. 
- **Specification:** When the left mouse button goes down, store the click coordinate as `anchor` and keep `originalRegion`. Only switch into active resizing and update `region` once the mouse moves at least 3 pixels (`dx >= 3 or dy >= 3`). If the mouse is released without exceeding this threshold, restore `originalRegion`.

### Adjustment 2: Eliminate Click-to-Cancel
- **Rationale:** A stray click inside or outside the region should never dismiss the overlay. 
- **Specification:** If `not drag.moved` on `leftMouseUp`, do nothing. The session remains open until the user presses `Enter` (capture) or `Esc` (cancel).

### Adjustment 3: Dual Movement Channels (`Cmd` + Left Drag and Right-Click Drag)
- **Rationale:** While `<cmd>` + drag is intuitive, Right-Click Drag inside the box provides a completely keyboardless way to reposition the box using only the mouse/trackpad.
- **Specification:** If `flags.cmd` is held during `leftMouseDown` inside `region`, OR if `rightMouseDown` occurs inside `region`, set `mode = "move"`.

### Adjustment 4: Spacebar-to-Pan During Drag (Bonus Enhancement)
- **Rationale:** Standard in macOS `Cmd+Shift+4` and design tools (Photoshop/Figma): if you are dragging a new selection and realize your starting corner was slightly off, holding `Spacebar` while keeping the mouse down freezes the selection dimensions and shifts the anchor with the cursor. Releasing `Spacebar` resumes resizing.
- **Specification:** Optional power-user enhancement during `mode = "new"`.

### Adjustment 5: Updated Floating Hints
- **Rationale:** Visual feedback confirms that `Cmd`-drag moves the box.
- **Specification:** Change hint string to:
  `"Drag to select | ⌘-Drag or Right-Drag to move | Enter to capture | Esc to cancel"`

---

## 6. Implementation Blueprint

### 6.1 Event Handling Flow in `screenshot_region.lua`

In Hammerspoon, `event:getFlags()` returns a table of active modifier keys (`flags.cmd`, `flags.alt`, `flags.shift`, `flags.ctrl`). Furthermore, `hs.eventtap.event.types` includes `rightMouseDown`, `rightMouseDragged`, and `rightMouseUp`.

#### Updated Event Tap Initialization:
```lua
local eventTypes = hs.eventtap.event.types
tap = hs.eventtap.new({
    eventTypes.leftMouseDown,
    eventTypes.leftMouseDragged,
    eventTypes.leftMouseUp,
    eventTypes.rightMouseDown,
    eventTypes.rightMouseDragged,
    eventTypes.rightMouseUp,
    eventTypes.keyDown,
}, function(event)
    -- ...
end)
```

#### Detailed Event Logic:
```lua
local eventType = event:getType()
local flags = event:getFlags()
local point = eventPoint(event)

-- 1. Key handling
if eventType == eventTypes.keyDown then
    local code = event:getKeyCode()
    if code == hs.keycodes.map.escape then
        finish(false)
        return true
    end
    if code == hs.keycodes.map["return"] or code == hs.keycodes.map.padenter then
        finish(region.w >= MIN_SIZE and region.h >= MIN_SIZE)
        return true
    end
    return true
end

-- 2. Mouse Down (Left or Right)
if eventType == eventTypes.leftMouseDown or eventType == eventTypes.rightMouseDown then
    if not frameContainsPoint(screenFrame, point) then
        return true
    end

    local handle = (eventType == eventTypes.leftMouseDown) and handleAt(point, region) or nil
    local isMoveRequested = (eventType == eventTypes.rightMouseDown) or (flags.cmd and pointInRect(point, region))

    if handle then
        drag = {
            mode = "resize",
            handle = handle,
            startRegion = copyRect(region),
        }
    elseif isMoveRequested and pointInRect(point, region) then
        drag = {
            mode = "move",
            startPoint = point,
            startRegion = copyRect(region),
        }
    elseif eventType == eventTypes.leftMouseDown then
        -- Default: Start new region selection with hysteresis
        drag = {
            mode = "new",
            anchor = point,
            moved = false,
            originalRegion = copyRect(region),
        }
        -- Note: Do NOT call updateNewRegion or redraw yet!
    end
    return true
end

-- 3. Mouse Dragged (Left or Right)
if (eventType == eventTypes.leftMouseDragged or eventType == eventTypes.rightMouseDragged) and drag then
    if drag.mode == "move" then
        local dx = point.x - drag.startPoint.x
        local dy = point.y - drag.startPoint.y
        region = clampRegionToFrame({
            x = drag.startRegion.x + dx,
            y = drag.startRegion.y + dy,
            w = drag.startRegion.w,
            h = drag.startRegion.h,
        }, screenFrame)
        redraw()
    elseif drag.mode == "resize" then
        region = resizeFromHandle(drag.startRegion, drag.handle, point, screenFrame)
        redraw()
    elseif drag.mode == "new" then
        local dx = math.abs(point.x - drag.anchor.x)
        local dy = math.abs(point.y - drag.anchor.y)
        if not drag.moved and (dx >= 3 or dy >= 3) then
            drag.moved = true
        end
        if drag.moved then
            updateNewRegion(drag.anchor, point)
            redraw()
        end
    end
    return true
end

-- 4. Mouse Up (Left or Right)
if eventType == eventTypes.leftMouseUp or eventType == eventTypes.rightMouseUp then
    if drag and drag.mode == "new" and not drag.moved then
        -- Click without drag: restore original region, do NOT exit
        region = drag.originalRegion
        redraw()
    end
    drag = nil
    return true
end
```

### 6.2 Updated Hint Elements in `buildElements`
In `screenshot_region.lua` (lines 171–175, 261–268):
- Increase `hintWidth` from `348` to `420` to comfortably fit the expanded explanation.
- Update hint text:
  ```lua
  text = "Drag to select | ⌘-Drag or Right-Drag to move | Enter to capture | Esc to cancel"
  ```

---

## 7. Recommended Solution Summary

1. **Adopt Bryan's Inversion:** Modify `home/dot_hammerspoon/screenshot_region.lua` so that unmodified left-click and drag anywhere on the screen creates a new rectangular selection from click to release.
2. **Implement `<cmd>` + Drag for Move:** Gate translation on `flags.cmd` when clicking inside the existing region.
3. **Add Right-Click Drag for Move:** Allow right-mouse drag inside the region to translate as well, enabling single-handed mouse/trackpad repositioning.
4. **Incorporate Drag Hysteresis:** Prevent accidental destruction of the preloaded region on mouse down by waiting for 3 pixels of movement before updating `region`.
5. **Remove Single-Click Cancellation:** Preserve the preloaded region if a click does not move, keeping `Esc` as the single clear cancellation path.
6. **Deploy via Chezmoi:** The changes are confined strictly to `home/dot_hammerspoon/screenshot_region.lua`. Once committed in `chezmoi`, `chezmoi apply` triggers `run_onchange_after_restart_hammerspoon.tmpl` and reloads Hammerspoon automatically.
