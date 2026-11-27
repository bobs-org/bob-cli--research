# Section-jump outline HUD (`Ctrl+J` / `Ctrl+K`): research report

Researcher: **mus** · 2026-11-27
Scope: losing one's place when using the `<C-j>` / `<C-k>` section-header
jumps in Obsidian, and whether a brief outline shown on each jump is the
right fix. Ends with a recommended solution.

Governing decisions consulted via `sase memory read roster:decisions`:
`decisions:successor-jump-parks-the-walk` (the `Ctrl+J` pin — a hard
keybinding constraint on this feature), `decisions:task-move-never-advances-the-walk`
(the park precedent), `decisions:answering-advances-the-walk` (walk-landing
toast precedent). No accepted decision covers section-header jumps or a
section outline HUD, so this report proposes new behavior; the closest
binding precedents are the walk toasts, the `bob-landing-flash` cue, and the
bracket-mode status-bar indicator. Release mechanics: bob-cli rides the
daily train (`decisions:bob-cli-releases-ride-a-daily-train`); this change
itself ships in `bob-plugins` (`bob-navigation-hotkeys`, currently
`2.107.14`) and deploys via `bob plugins sync`, not the CLI train.

---

## 1. TL;DR

Yes — build it, but **not a full-file outline**. Build a **small transient
context HUD**: on every `jump-to-next/prev-section-header`, show a
top-center floating card with a 3–5 header window (1–2 above, the landing
header highlighted, 1–2 below), a position counter (`4 / 17`), a direction
arrow, and a wrap badge (`↺`) when the jump cycled. Auto-dismiss after
~1.5 s; repeated presses update the card in place and reset the timer.
Pair it with a one-shot landing-line flash on the target header. Keep the
existing `Notice` only for the failure paths (no headers / no editor).
Do not steal focus, do not use a modal, do not use a `Notice` for the
success path, and resolve the `Ctrl+J` conflict with the successor-picker
pin before shipping.

---

## 2. Problem restatement

Bryan's vault keymaps bind `Ctrl+J` / `Ctrl+K` (Obsidian custom hotkeys) to
the plugin commands `jump-to-next-section-header` /
`jump-to-prev-section-header`. Each press moves the cursor to the next /
previous Markdown `#`–`######` header and scrolls that line to the top of
the editor. After the jump it is easy to forget which section you came
from and where you are in the file — especially because:

1. The jump **scrolls the old context off-screen** (`scrollEditorLineToTop`
   with `y: "start"`), so there is no visual trace of the move.
2. The jump **wraps around**: past the last header you land on the first
   (and vice versa) with no indication that a wrap happened, which is the
   single most disorienting case.
3. The success path shows **no feedback at all** — a `Notice` appears only
   when there is no previous/next header edge to report (which, given
   wrap-around, means effectively only when the file has zero headers).

The request: show a brief, non-intrusive but clearly visible outline of
the file's sections on each jump.

## 3. What exists today (verified in `bob-plugins`)

All paths below were read in the linked `bob-plugins` checkout; no peer
report was consulted.

- **Commands.** `490-plugin-lifecycle.js:426-436` registers
  `jump-to-next-section-header` and `jump-to-prev-section-header` with
  **no default hotkey** (`docs/bob-navigation-hotkeys.md` rows 49/54 show
  `—`). Bryan's `Ctrl+J` / `Ctrl+K` binding is therefore vault-local
  custom configuration, not a plugin default. Any HUD must work regardless
  of what key the user binds, i.e. trigger off the command, not the key.
- **Jump logic.** `610-plugin-jumps-and-counted-keys.js:178-205`
  (`jumpToSectionHeader`) → `130-fences-and-status.js:58-81`
  (`getSectionHeaderJumpLine`) → `170-open-task-jump.js:687-720`
  (`scrollEditorLineToTop`). Header detection (`010-requires-and-config.js:20`)
  is `SECTION_HEADER_RE = /^ {0,3}#{1,6}(?:[ \t]|$)/`, correctly skipping
  frontmatter and fenced code blocks (`getSectionHeaderLines`,
  `130-fences-and-status.js:13-56`). Wrap-around is deliberate: next from
  the last header returns `headerLines[0]`; previous from the first returns
  the last header. Cursor lands at column 0; target line scrolls to editor
  top via a CodeMirror 6 `EditorView.scrollIntoView(..., { y: "start" })`
  dispatch, best-effort with a `false` return on non-CM6 editors.
- **Feedback today.** Success: none. Failure: `new Notice("No next section
  header")` / `"No previous section header"` — reachable in practice only
  for header-less files. The landing line gets no highlight.
- **Keybinding conflicts (important).** `Ctrl+J` is **already taken inside
  the successor picker**: `206e-successor-picker-jump.js` and
  `206g-successor-requirements.js:221` document the `Ctrl+J` pin
  (`decisions:successor-jump-parks-the-walk`). `Ctrl+Alt+J/K` walks the
  freshness review queue (docs §368), and `Ctrl+Shift+J/K` navigates
  Ready/In-Progress/Next `#task` lines (docs §149). So `Ctrl+J/K` for
  section jumps is only unambiguous when no Bob modal is open. The HUD must
  not fire (or must yield) when the successor picker / Task Card owns
  `Ctrl+J`.
- **Existing visual-feedback precedents in this codebase** (reuse these,
  do not invent a fourth style):
  - `bob-landing-flash` (`styles.css:129-145`): a 1.2 s `background +
    inset-accent-bar` animation on `.cm-line`, with a
    `prefers-reduced-motion` fallback. The exact pattern to reuse for the
    header landing cue.
  - `bob-vim-yank-flash/main.js`: CM6 `StateField` + `Decoration.line`
    flash (~200 ms), viewport-bounded, never guesses. The pattern to copy
    if the flash should be decoration-based rather than class-based.
  - Bracket-mode status-bar indicator (`547-bracket-mode-indicator.js`,
    `547a-bracket-mode-view.js`): persistent `addStatusBarItem()` chip
    `[[ s w n b ]]` with attention dots. Proof the codebase already owns
    the status-bar surface — and that it is occupied.
  - Walk / unblocked / keep-moving notice cards (`285-unblocked-notice.js`,
    `styles.css:1686+`, `nav api.notice v3`): rich HTML `Notice`s for
    review walks. They stack bottom-right, live ~4 s, and are the wrong
    vehicle for a 1.5 s orientation cue (see §5, option A).
  - Window-prefix (`Ctrl+W`) state machine (`687-plugin-window-prefix.js`):
    precedent for a mode with a catch-all `Scope`, an overlay-suppression
    matrix (`WINDOW_PREFIX_OVERLAY_SELECTORS`), blur/mousedown cancel, and
    per-event teardown. Copy its cancel hygiene for the HUD timer.

## 4. Critique of the plan as stated

**The instinct is right.** Losing one's place on section jumps is a real
orientation bug, not a cosmetic wish: scroll-to-top plus silent wrap is
precisely the combination that destroys spatial memory. A transient
orientation cue is the standard fix (VS Code's breadcrumb + `editor:
reveal`, JetBrains' breadcrumbs, Obsidian's own Outline pane, the
community *Auto Heading* section strip and *Another Sticky Headings*
plugins all exist because of this need). Doing it inside
`bob-navigation-hotkeys` rather than adopting a community plugin is also
right: the jump command, the header parser, and the scroll call are all
already Bob-owned, so the HUD is ~100 lines of DOM plus a model function,
with no new dependency and no cross-plugin coordination.

**But "outline of the file's markdown sections" as stated should not be
built literally.** Four adjustments, each called out as required:

1. **Show a context window, not the file outline.** A daily note or long
   spec can have 30–80 headers; rendering all of them on every `Ctrl+J`
   is the opposite of non-intrusive and recreates the Outline pane as a
   popup. What orients you is *prev → current → next*, not the whole tree.
   **Adjustment: cap the HUD at 5 rows** (2 above when they exist, the
   landing header, 2 below), with H-level indentation and a `n / total`
   counter carrying the global position instead.
2. **The wrap case needs explicit signaling.** The plan does not mention
   wrap, but wrap is the most disorienting jump. **Adjustment: a `↺ top` /
   `↺ bottom` badge plus a distinct position-counter transition (e.g.
   `17 / 17 → 1 / 17`) is a release-blocking requirement, not polish.**
3. **"Brief" needs a number and repeat semantics.** Without them you get
   either a cue that vanishes before it is read or a stack of stale cards
   when the user holds `Ctrl+J`. **Adjustment: 1500 ms auto-dismiss,
   single HUD instance, every repeat press updates in place and resets the
   timer** (same discipline as `scheduleOpenTaskJumpCenter` /
   `pendingOpenTaskJumpCenterDeferred`).
4. **Scope the trigger.** Firing on cursor movement, hover, or file open
   would nag constantly. **Adjustment: fire only from the two section-jump
   commands** (plus an optional explicit "show outline HUD" command for
   discoverability). Never on `Ctrl+Alt+J/K` freshness walks, never on
   `Ctrl+Shift+J/K` task jumps, never when a Bob modal owns `Ctrl+J`.

One further consideration — **consider a persistent breadcrumb first as a
complement, not a substitute.** A one-line sticky breadcrumb (current
header ancestry, e.g. `Spec › HUD › Timing`) permanently solves "where am
I" at near-zero attention cost, à la *Auto Heading*'s section strip; the
transient HUD solves "where did I just go". The HUD is the right v1
because it is bounded, dismissal-safe, and touches nothing when idle. If
Bryan later wants persistence, add the breadcrumb as a separate setting
defaulting off — do not make the HUD persistent to cover both jobs.

## 5. Options considered

| Option | What it is | Verdict |
|---|---|---|
| **A. `Notice` toast with header context** | Reuse `nav api.notice` card: `✓ Landed · ## Timing · 4/17` | Rejected for success path. Toasts stack, live too long (~4 s), sit bottom-right out of the gaze path, and offer no positional cue. Keep `Notice` for the zero-headers failure only. |
| **B. Status-bar readout** | Write `## Timing · 4/17` into `addStatusBarItem()` | Rejected as primary. Peripheral, competes with the bracket-mode chip, truncates badly, invisible in full-screen writing. Viable as an *accessory* (one line, cheap) but not the fix. |
| **C. Center-top floating HUD (transient)** | Absolute-positioned card in the Markdown view, 5-row window, auto-dismiss | **Recommended.** Foveal, dismisses itself, clickable, theme-aware, testable. §6 specifies it. |
| **D. CM6 cursor-anchored tooltip** | `showTooltip` / hover-widget at the cursor line | Rejected. Fights the scroll-to-top dispatch, obscures the landed text, tooltip lifecycle is fiddly under rapid repeats. Cursor anchoring is worse than view-top anchoring here because the eyes go to the top after a top-scroll. |
| **E. Full outline picker modal** | `FuzzySuggestModal` listing every header, filterable | Rejected as the J/K behavior; accepted as a *separate* future command ("Go to section…"). Modals steal focus and break the rapid-tap flow that makes J/K valuable. |
| **F. Always-on sticky breadcrumb bar** | Like *Auto Heading* strip / *Another Sticky Headings* | Deferred complement. Solves a adjacent problem well but adds permanent chrome; needs its own design (folding, Reading view, mobile). Do after the HUD. |

Prior art checked: Obsidian *Quiet Outline*, *Breadcrumbs*, *Hovered Table
of Content* (floating TOC on hover), *Auto Heading* (sticky section strip
with breadcrumb + word count), *Another Sticky Headings*, *Extended
Headings* (hover breadcrumbs); editor-side, CodeMirror 6 `showTooltip` /
`scrollIntoView` semantics and the in-repo yank-flash decoration pattern.
None of them does "transient 5-row context on section jump" — the gap is
real and small enough to own.

## 6. Recommended solution

### 6.1 Behavior

- **Trigger.** Only the two commands `jump-to-next-section-header` /
  `jump-to-prev-section-header`. Compute the full header list once per
  invocation with the existing `getSectionHeaderLines` (fences +
  frontmatter aware — do not reimplement parsing).
- **Content (5-row window).**
  - Rows: up to 2 headers above the landing index, the landing header, up
    to 2 below. Each row: H-level indent (levels 1–6 → 0–5 × ~12 px),
    title text truncated to ~80 chars with ellipsis, `#` count or subtle
    level numeral. Non-landing rows dimmed (`--text-muted`); landing row
    `--text-normal` + accent left bar (`--interactive-accent`).
  - Header: direction arrow (`↓ J` / `↑ K`) + position `4 / 17` + wrap
    badge when applicable (`↺ wrapped to top` / `↺ wrapped to bottom`).
  - Footer (tiny, muted): `J/K move · click jumps · Esc dismisses`.
- **Timing.** Show ≤1 frame after the scroll dispatch. Visible 1500 ms
  (constant, e.g. `SECTION_HUD_VISIBLE_MS = 1500`), fade 180–220 ms.
  Repeat press while visible: update rows/counter in place, restart the
  timer — never a second card. Any editor edit, view switch, or `Esc`
  dismisses immediately. Honor `prefers-reduced-motion`: no slide/fade,
  still auto-dismiss.
- **Placement.** Top-center of the *active Markdown view's* container
  (`MarkdownView.containerEl`, `position: relative` scope), ~48 px below
  the view header, `z-index` above `.cm-editor` but below `.modal`.
  `pointer-events: none` on the shell, `auto` on rows so clicks work but
  stray clicks fall through. Fixed width ~380 px (max 60% of view width),
  never covering the cursor line for more than the fade duration — top
  placement plus scroll-to-top landing makes overlap essentially
  impossible.
- **Interaction.** Click a row → jump to that header (same code path,
  HUD refreshes). `J`/`K` held → HUD tracks. `Esc` → dismiss without
  moving. Focus never leaves the editor (HUD uses no focusable elements
  except click handlers with `tabindex="-1"`; `role="status"`
  `aria-live="polite"` for screen readers).
- **Landing cue.** Simultaneously add `bob-landing-flash`-style highlight
  to the landed header line for 1.2 s (reuse `styles.css:129-145`
  verbatim, new class `bob-section-landing-flash` or reuse). The flash
  marks *where*; the HUD tells *where among what*.
- **Edge cases.**
  - Zero headers → today's `Notice`, no HUD (unchanged behavior).
  - Exactly one header → HUD shows `1 / 1` single row; wrap badge on
    every press would nag — show it only when the press actually wrapped
    *across distinct headers*; single-header files get no badge.
  - Folded headers / folded sections: jump still works on line numbers;
    HUD lists logical headers regardless of fold state; do not unfold.
  - Long files (5k+ lines): `getSectionHeaderLines` is O(n) per press —
    fine at Markdown scale, but cache per `(file.path, doc-length,
    change-counter)` and invalidate on edit; HUD render is capped at 5
    rows so DOM cost is constant.
  - Reading view: commands are editor-only today; keep the HUD editor-only
    for v1. If Reading-view jumps are added later, anchor the HUD to the
    preview container with the same model.
  - Mobile (`isDesktopOnly: false`): HUD is touch-safe by construction
    (tap row = jump, tap elsewhere falls through); ensure no hover-only
    affordance. The footer hint should read `tap a row to jump` on touch.
  - Empty titles (`##` alone), trailing `#`s (`## Title ##`), inline
    formatting/links in titles: strip to plain text for the row (reuse
    the vault's existing title-cleaning if any; otherwise trim `#`s and
    collapse whitespace).

### 6.2 Implementation sketch (in `bob-navigation-hotkeys`)

1. New fragment `6xx-section-jump-hud.js` (pure, unit-tested):
   `buildSectionHudModel(headerLines, titles, landingIndex, direction,
   wrapped)` → `{ rows: [{line, level, title, isLanding}], position,
   total, direction, wrapped }`. No DOM, no Obsidian imports.
2. New mixin `6xy-plugin-section-hud.js`: `ensureSectionHud(container)`,
   `paintSectionHud(model)`, `scheduleSectionHudHide()` with a single
   token + `clearTimeout` (mirror `scheduleOpenTaskJumpCenter` /
   window-prefix timer hygiene), `dismissSectionHud(reason)`. Creates one
   `div.bob-section-hud` per Markdown view container; destroys it on
   `onunload` / layout change.
3. Patch `jumpToSectionHeader` (`610:178-205`): after computing
   `targetLine`, resolve its index in the header list, build the model,
   call scroll (unchanged), flash, paint HUD. On the `null` path keep the
   `Notice` and paint nothing.
4. Guard: if a Bob modal that owns `Ctrl+J` is open (successor picker,
   Task Card, command mode — reuse `WINDOW_PREFIX_OVERLAY_SELECTORS`-style
   detection), the section command should keep today's behavior of *not*
   firing when the modal consumes the key; the HUD must never appear over
   a modal.
5. Styles in `styles.css`: `.bob-section-hud` card — `var(--background-primary)`,
   `var(--background-modifier-border)` 1 px, 10 px radius, `var(--shadow-s)`,
   backdrop blur where supported, dark/light via existing vars only (no
   hardcoded colors; the codebase's notice cards already follow this rule).
6. No new dependency, no settings UI for v1 beyond a single
   `sectionJumpHud: true` toggle + `sectionHudMs` for tuning (default on,
   default 1500). A per-vault CSS snippet can restyle everything since all
   styling is class-driven.

### 6.3 Why this shape is beautiful (and calm)

- **One glance, zero parsing:** the landing row is the only bright row;
  everything else recedes. Level indentation gives structure without tree
  lines; the counter gives scale without a scrollbar.
- **Motion with manners:** card fades/scales in over ~120 ms from 4 px up,
  holds still (no marquee, no progress shimmer by default — an optional
  1.5 s hairline decay bar under the header is the most animation ever
  allowed), fades out. Reduced-motion users get a clean cut.
- **It teaches the wrap instead of hiding it:** the `↺` badge plus the
  counter snap (`17/17 → 1/17`) turns the most confusing moment into the
  most legible one.
- **It matches Bob's existing visual language:** same card treatment as
  the unblocked/keep-moving notices, same accent-bar flash as the landing
  cue, same status-bar restraint (persistent chrome stays in the status
  bar; transient news floats briefly and leaves).

### 6.4 Verification

- Unit: `getSectionHeaderLines` fence/frontmatter cases (already covered
  — extend with `##`-in-fence, `---` inside code, setext edge);
  `buildSectionHudModel` windowing at file start/end, single-header,
  wrap-flag correctness, title truncation.
- Manual QA script: daily note with 20+ headers across H1–H4 + fences;
  hold `Ctrl+J` 10× (one card, tracking, then clean dismiss); `Ctrl+K`
  back; wrap in both directions (badge appears); `Esc` dismiss; click a
  non-landing row (jumps); type mid-HUD (dismisses, edit unaffected);
  Reading view (no HUD, no error); mobile emulator (tap targets ≥ 32 px);
  dark + light themes; `prefers-reduced-motion` on.
- No vault writes, no network, no indexer involvement — the feature reads
  `editor.getValue()` only, so `bob plugins sync` deploy risk is minimal.

## 7. Requirements adjustments (explicit)

| # | Original implication | Adjusted requirement |
|---|---|---|
| 1 | Full-file outline on each jump | 5-row context window + `n / total` counter |
| 2 | Unspecified wrap behavior | Mandatory `↺` wrap badge + counter snap |
| 3 | "Brief" undefined | 1500 ms, single instance, repeat resets timer |
| 4 | Fires on the keymap | Fires on the *command* (key-agnostic); suppressed when a Bob modal owns `Ctrl+J` |
| 5 | Outline only | Outline HUD **plus** landing-line flash (reuse `bob-landing-flash`) |
| 6 | No a11y/motion scope | `role="status"` live region; `prefers-reduced-motion` cut; editor focus never moves; touch-safe rows |
| 7 | Ships whenever | `bob-navigation-hotkeys` minor; toggle default-on; no CLI-train involvement |

## 8. Open questions for Bryan (non-blocking)

1. Is 1500 ms the right hold, or do you want it to linger slightly longer
   on wraps only (e.g. 2200 ms when `↺` shows)? I lean yes — wraps carry
   more news.
2. Should rapidly holding `Ctrl+J` through a long file accelerate (skip
   the HUD repaint every other step for perf) or is per-step repaint
   (5 rows — trivially cheap) fine? I lean repaint every step; simpler
   and already constant-cost.
3. Future: same HUD reused for `Ctrl+Shift+J/K` task jumps and
   `Ctrl+Alt+J/K` freshness walks, or keep section jumps visually
   distinct? I lean distinct (different accent tint per family, matching
   the `s/w/b` attention hues) — but only after v1 proves the pattern.

---

*Evidence base: `bob-navigation-hotkeys` `src/610` (jump), `src/130`
(parser), `src/170` (scroll), `src/490` (command registration),
`src/010` (header regex), `src/206e/206g` (`Ctrl+J` pin),
`src/547*` (status-bar chip), `src/677d` (hints chip), `src/285`
(notice cards), `styles.css` (landing flash, notice cards),
`bob-vim-yank-flash/main.js` (decoration flash), `docs/bob-navigation-hotkeys.md`
(command table + keybinding docs), community plugins Quiet Outline /
Breadcrumbs / Hovered Table of Content / Auto Heading / Another Sticky
Headings / Extended Headings, CodeMirror 6 tooltip/scroll docs.*
