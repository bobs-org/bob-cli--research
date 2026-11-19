# Click-to-Copy Buttons & Pills in Obsidian: Critique, Tradeoffs, and Design

> **Question:** What is the best way to create clickable buttons/links in Obsidian that copy configurable text to the clipboard—making creation by typing effortless while keeping the UX intuitive, reliable, and visually cohesive—and is the premise itself sound?

---

## Executive Summary

**Verdict on the idea:** Yes, with focused refinements. Click-to-copy elements solve three real gaps that Obsidian's native UI and Vim yanking do not cover cleanly: (1) **inline copyable commands/IDs/snippets** inside prose and checklists, (2) **collapsed/labeled payloads** that hide noisy multi-line AI prompts or long shell pipelines behind a crisp label, and (3) **one-tap, zero-selection, format-safe copying** in Live Preview, Reading View, and Mobile without fighting cursor mode or copying Markdown prefixes. However, using them to duplicate ordinary visible code blocks—or implementing them via `obsidian://` links, raw HTML `<button>` tags, or split-definition Meta Bind registries—creates significant UX and vault-hygiene friction.

**Recommended solution:** Build a lightweight, standalone, mobile-compatible plugin (**`bob-copy-buttons`**) in `bob-plugins` (`isDesktopOnly: false`) backed by a **self-contained, plain-Markdown dual syntax**:

1. **Inline Copy Pill** (single-line, Bob/Dataview/Tasks-safe):
   - Self-labeled: `` `copy>> ssh bryan@athena` ``
   - Custom-labeled: `` `copy[SSH Athena]>> ssh bryan@athena` ``
2. **Copy Card Block** (multi-line prompts, scripts, templates):
   - Plain: ```` ```copy\n<verbatim text>\n``` ````
   - Titled / collapsible: ```` ```copy\n::: Weekly Review Prompt\n<verbatim text>\n``` ````
3. **Typing-First Creation (`;;` → Micro-Composer + Zero-Modal Fast Path):**
   - Typing `;;` in prose opens a focused, keyboard-first Composer Card (mirroring `block-id-prompt`'s `((` workflow) with **live preview**, **auto-detection of Inline vs. Block**, **optional Label**, and a **one-key `Tab` clipboard import** when text is already on your clipboard.
   - Selecting text + invoking the command/hotkey wraps/prefills it in place; typing `` `copy>> ...` `` directly works with zero modal.

---

## 1. Critique of the Plan & Justified Requirement Adjustments

Before picking an implementation, it helps to challenge the framing *"create a button/link ... configurable at the point of button/link creation"*. Several implicit assumptions in that phrasing break down under Obsidian's editor model and Bob's plain-Markdown vault constraints.

### Where the Idea Shines vs. Where It Is an Anti-Pattern

| Use Case | Value of a Copy Button | Why |
| --- | --- | --- |
| **Long/noisy prompt or pipeline collapsed behind a label** | High | Turns a 12-line AI prompt or 180-char URL into a single clean `Weekly Review Prompt` button/card without visual clutter. |
| **Short command/token embedded inside prose or a `#task` checklist** | High | Fenced code blocks break list/paragraph flow across 3+ lines; an inline pill keeps `` - [ ] Run `copy>> ...` and check logs `` compact and one-click. |
| **Runbooks / recurring checklists / Obsidian Mobile** | High | Eliminates visual-mode selection (`v...y`) and accidental copying of bullet markers, callout `> ` prefixes, or trailing whitespace. |
| **Ordinary multi-line code snippet you already want visible in full** | Low (redundant) | Obsidian natively renders a Copy button in the top-right corner of fenced code blocks (` ```bash `). Duplicating content into a separate button creates two sources of truth that drift. |
| **Desktop Vim copy of an ordinary inline `` `code` `` word** | Moderate | In Vim normal mode, `yi\`` (with clipboard integration) already yanks inline code without reaching for a mouse; buttons still win for Reading View, labeled payloads, and mouse/mobile use. |

### Six Justified Adjustments to the Requirements

1. **Decouple "button/link UX" from Markdown link syntax (do not use `obsidian://` links).**
   *Why:* Standard `[Label](obsidian://...)` links look attractive because Reading View natively routes clicks to `registerObsidianProtocolHandler`. In practice, they fail on four fronts:
   - *Live Preview click trap:* Clicking a Markdown link in Live Preview places the editor cursor inside the link and expands raw `[Label](obsidian://...)` text instead of activating it (requiring `Cmd/Ctrl+Click` or a CodeMirror 6 widget anyway).
   - *Percent-encoding corruption:* Spaces, newlines (`%0A`), quotes, `#`, `&`, `=`, and `)` turn readable payloads into unreadable `%20%0A%29` soup in Source mode and Git diffs.
   - *OS protocol round-trip & length limits:* Dispatching `obsidian://` routes through the OS URI handler (`xdg-open` / LaunchServices / ShellExecute), hitting practical 2–4 KB command-line limits on Linux `.desktop` (`%u`) and Windows, risking focus bounce, and exposing copied secrets/text in OS launcher arguments.
   - *No inline visual feedback:* A bare `<a>` tag cannot morph cleanly in place to confirm `✓ Copied` without custom DOM listeners anyway.

2. **Support two distinct payload shapes—*Inline Pill* and *Block Card*—under one workflow.**
   *Why:* An inline token cannot cleanly carry a 15-line prompt containing blank lines, `#headings`, or backticks; conversely, a 3-line fenced block is far too heavy for an inline IP address or SSH command inside a bullet list. Unifying them in the composer (auto-promoting to a Block Card whenever the input has newlines) gives the best of both worlds.

3. **Make the payload *self-labeled by default*, with an optional custom label.**
   *Why:* For short text (`ssh bryan@athena`), forcing the user to configure both a label and the text creates tedious duplication (`Copy ssh -> ssh`). Leaving Label blank should display the text itself as a sleek clickable code-pill; adding a Label hides the payload behind a human title and reveals the payload on hover.

4. **Strictly forbid out-of-place registry indirection (`BUTTON[id]`) and embedded JavaScript.**
   *Why:* Tools like Meta Bind encourage a `hidden: true` definition block paired with inline `BUTTON[id]` tokens. In a Bob vault—where `Ctrl+Shift+M` moves tasks across notes, `Ctrl+Shift+T` splits bullets into tasks, and `bob task archive` moves closed tasks to `done/`—splitting a button from its definition breaks portability, causes ID collisions, and orphans definitions. Storing executable JS inside notes (`type: js`) also introduces an unnecessary security surface. Every copy widget must be **100% self-contained in place** and **purely declarative text**.

5. **Design for Bob vault & Vim ecosystem safety from day one.**
   *Why:* Bob notes are parsed by `bob-cli`, Obsidian Tasks, and Dataview, and edited heavily in Vim mode (`bob-navigation-hotkeys`, `bob-vim-surround`, `bob-vim-yank-flash`) as well as synced via Git (`bob vault-git-sync`). Our stored syntax must never leak `#tags`, `[[wikilinks]]`, `[field:: value]` Dataview fields, or `^block-id` tokens into vault metadata, and must stay completely human-readable in raw Markdown diffs.

6. **Optimize typing creation for both *clipboard-ready* and *typed-from-scratch* workflows.**
   *Why:* Often the text you want to turn into a copy button is *already on your clipboard* (copied from a terminal or browser) or *already typed and selected* in your note. Treating "create by typing" purely as typing raw delimiters misses the fastest path: a lightweight typing trigger that opens a focused composer with a one-key `Tab` clipboard import, plus selection-wrapping and zero-modal inline shorthand.

---

## 2. Evaluation of Implementation Approaches

| Criterion | A. Community Plugin: Meta Bind (`type: js`) | B. Community Plugin: Buttons | C. Standard Link + `obsidian://` Handler | D. Raw Inline HTML (`<button>`) | E. Custom Bob Plugin (`bob-copy-buttons`) |
| --- | --- | --- | --- | --- | --- |
| **Works inline in prose/tasks** | Only via split `hidden: true` block + `BUTTON[id]` | Poor (block-first; ID indirection needed) | Yes (with CM6 live-preview friction) | Breaks to raw HTML on cursor line | **Yes (native inline CM6 pill + Reading DOM)** |
| **Multiline payloads** | Yes (codeblock) | Awkward | **No** (ugly `%0A`, URL length caps) | **No** (breaks Markdown blocks) | **Yes (` ```copy ` verbatim fence)** |
| **Easy creation by typing** | Poor (verbose YAML + JS boilerplate) | Poor (multi-line block syntax) | Moderate (needs generator modal anyway) | Poor (manual HTML + escaping) | **Excellent (`;;` composer + inline shorthand + selection)** |
| **Self-contained (survives `Ctrl+Shift+M` task move)** | No when inline (`BUTTON[id]` separates definition) | No when using IDs | Yes | Yes | **Yes (100% self-contained)** |
| **Bob / Dataview / Tasks safe** | Mostly (hidden block leaves noise) | Codeblock safe | Risk of `[label](...)` vs task formatting; `%` noise | Raw HTML noise in text | **Yes (CommonMark code spans shield all inner tokens)** |
| **Security (no arbitrary JS in notes)** | Uses `type: js` eval | Safer if static, limited clipboard support | Safe | `onclick` stripped by DOMPurify | **100% declarative data, zero JS eval** |
| **Git diff & plain-text readability** | Verbose YAML/JS | Verbose | Ugly `%20`/`%0A` URL soup | Cluttered HTML tags | **Clean, human-readable Markdown** |
| **Mobile compatibility** | Depends on Meta Bind mobile JS | Largely unmaintained | OS URI dispatch quirks | Stripped/flaky | **Full (`isDesktopOnly: false`)** |
| **Visual polish & feedback** | Generic plugin button | Dated theme | Plain link blue; no in-place `✓ Copied` morph | Unstyled / fragile | **Bespoke Bob/Obsidian theme-native pill + morph** |

### Why Community Plugins Fall Short
- **Buttons:** Historically popular, now largely superseded by Meta Bind with stalled maintenance; lacks a crisp built-in copy-text primitive without external Templater/script glue and relies on block-level syntax.
- **Meta Bind:** Actively maintained and supports inline `BUTTON[id]` syntax, *but* lacks a native `type: clipboard` action—requiring a multi-line `meta-bind-button` codeblock with `action: { type: js, code: "navigator.clipboard.writeText(...)" }`. That forces two-location editing per inline button, embeds executable JS in plain notes, and makes quick creation while typing cumbersome without also writing Templater/QuickAdd scripts on top.
- **DataviewJS (`$= ...`):** Requires enabling JS execution, shows raw JS whenever the cursor touches the line in Live Preview, cannot be authored effortlessly by typing, and adds evaluation overhead on every render.

---

## 3. Canonical Storage Design: Bob-Safe Dual Syntax

Using standard CommonMark **inline code** for single-line pills and **fenced code blocks** for multi-line cards solves the hardest parser edge cases automatically: Obsidian, Dataview, Obsidian Tasks, and `bob-cli` all treat code spans and fenced code blocks as inert literal text.

### 3.1 Inline Copy Pill

```markdown
Self-labeled:   - [ ] Connect via `copy>> ssh bryan@athena` and tail logs
Custom-labeled: - [ ] Connect via `copy[SSH Athena]>> ssh bryan@athena` and tail logs
```

**Why `copy>>` and `copy[Label]>>` beat alternatives:**

| Alternative | Why It Is Worse |
| --- | --- |
| `` `copy: ...` `` | Collides with documentation notes containing YAML/JSON snippets like `` `copy: true` `` or `` `copy: always` ``. |
| `` `copy\|...` `` or `` `copy: label \| payload` `` | Collides with shell pipes (`cat a \| grep b`) inside the copied payload! Putting `[Label]` *before* `>> ` ensures **zero delimiter characters are reserved inside the payload**. |
| `{{copy: ...}}` or `[[copy:...]]` | Outside backticks, Obsidian and Bob parse `#tags`, `[[wikilinks]]`, and `[key:: val]` inside the payload as live vault tags, links, and Dataview fields! `[[...]]` also triggers unresolved-link warnings. |
| `` `📋 ...` `` | Harder to type manually in raw ASCII; Unicode glyphs vary across fonts/terminals. (The rendered widget still shows a crisp Lucide copy icon!) |

**Exact inline grammar & escaping rules:**
- **Prefix:** Starts immediately with `copy>> ` (or `copy>` + whitespace) or `copy[Label]>> ` (where `Label` is non-empty and does not contain unescaped `]>>`; `\]` escapes a literal `]` if needed).
- **Payload:** Everything after `>> ` up to the closing backtick(s). Any pipes (`|`), colons (`:`), quotes (`"`, `'`), parentheses, `#tags`, `$vars`, or `[brackets]` in the payload stay 100% literal with zero escaping.
- **Backticks inside payload:** CommonMark natively handles literal backticks inside inline code by wrapping with `N+1` backticks and single-space edge padding when the content starts or ends with `` ` ``:
  ````markdown
  ``copy>> echo `date +%F` ``
  ````
  Our serializer emits this automatically; our parser strips CommonMark outer backticks and symmetric single-space padding per CommonMark §6.1, preserving the exact payload bytes.
- **Safety guard:** An empty payload (`copy>> `) does not render as an interactive button (shows a subtle muted invalid/empty pill or leaves raw code) so half-typed spans never steal clicks.

### 3.2 Block Copy Card (Multi-Line Payloads)

```markdown
```copy
Review my open tasks in #sase and summarize:
1. What moved forward
2. What is blocked
```
```

With an optional title / collapsed header:

```markdown
```copy
::: Weekly Review Prompt
Review my open tasks in #sase and summarize:
1. What moved forward
2. What is blocked
```
```

**Crucial Obsidian API Detail (`getSectionInfo` pitfall):**
In Obsidian's `registerMarkdownCodeBlockProcessor("copy", (source, el, ctx) => ...)`, `source` only contains the body inside the fence—not the opening fence line (` ```copy ...`). Reading the opening fence line requires `ctx.getSectionInfo(el)`, which **returns `null` inside callouts (`> [!note]`), nested lists in certain views, and transcluded embeds (`![[note]]`)**.

Placing the optional title on line 1 inside `source` (`::: Title` or `:::collapsed Title`) guarantees the card renders identically everywhere—including inside callouts and embeds—without ever depending on `ctx.getSectionInfo(el)`. If an untitled payload literally needs its first line to start with `:::`, a bare `:::` sentinel line escapes it, and payloads containing triple backticks ```` ``` ```` automatically wrap in a 4-backtick fence (````` ````copy `````).

---

## 4. Typing-First Creation & Editing UX

Making creation effortless by typing requires avoiding both traps: (a) forcing the user to manually type tricky backtick/delimiter syntax every time, and (b) popping up intrusive menus on ordinary prose or code.

### 4.1 Collision Audit Against Bryan's Existing Obsidian Triggers

| Existing Trigger | Owner / Function | Collision Risk |
| --- | --- | --- |
| `[[` / `![[` | Obsidian wikilinks / embeds | Reserved |
| `^^` / `[[note#^` | `block-id-prompt` | Reserved |
| `((` | `block-id-prompt` Task Wikilink Picker | Reserved |
| `:` (BOL / after whitespace) | `bob-emoji` (`EditorSuggest`) | Reserved |
| `:` / `==` (Vim normal mode) | `bob-command-mode` / `bob-ledger-tools` | Normal-mode only |
| `d0`, `D0`, `-`, `se<X>`, `#t` + `Tab` | `bob-ledger-tools` (`Expand Bob snippet`) | Reserved |
| `[cat:: ` | `bob-ledger-tools` Bank Category Suggest | Reserved |
| `/` | Obsidian Slash Commands (optional) | Avoid for modal-free typing |

**Chosen primary typing trigger: `;;`** (two semicolons typed consecutively in Insert/Edit mode, configurable in settings).
- **Ergonomics:** Unshifted home-row key on US/standard layouts, faster than `((` or `^^`, and does not steal `:` (`bob-emoji`), `[[`, `((`, or `^^`.
- **False-positive immunity:**
  - Almost never appears in English prose or Markdown notes.
  - Strictly gated using the exact same CodeMirror 6 `syntaxTree` + `userEvent: "input.type"` pattern as `block-id-prompt` (`128-plugin-task-wikilinks.js`) and `bob-emoji`: **never triggers** inside fenced code blocks, inline code, YAML frontmatter, URLs, HTML comments, during IME composition, or on Vim normal-mode commands/undo/disk reloads.
  - Pressing `Esc` (or `Ctrl+[`) leaves `;;` untouched in the buffer (if you genuinely meant `;;`, say in Bash `case` text outside a fence); pressing `Backspace` on an empty input removes `;;` cleanly, mirroring `((`.

### 4.2 The Two-Gear Creation Flow

```
  Typing `;;` in prose ──┐
  Selection + Hotkey ────┼──▶  [ Copy Button Composer ]  ──(Enter / Cmd+Enter)──▶  Inserts canonical Markdown
  Command Palette ───────┘        │                                                at caret, cursor after pill
                                  ├─ Clipboard chip (`Tab` to paste)
                                  ├─ Text to copy (auto-grows multiline → Block)
                                  ├─ Optional Label (blank = self-labeled pill)
                                  └─ Live preview of rendered pill/card

  Zero-modal fast path:
  Type `copy>> ...` directly  ──────────────────────────────────────────────────▶  Renders on cursor leave
```

1. **Gear 1 — `;;` → Focused Micro-Composer Card:**
   - **Auto-focused `Text to copy` input:** Single-line by default, automatically expanding into a multi-line textarea if you paste multi-line text or press `Shift+Enter`.
   - **Clipboard Quick-Import Chip:** When the clipboard holds text, a subtle chip directly above the input shows `📋 From clipboard: "<first 48 chars>" · Tab`. Pressing `Tab` while the text field is empty (or clicking the chip) pastes the clipboard in one keystroke without cluttering the input when you want to type from scratch.
   - **Optional `Label` field:** Leave blank for a self-labeled inline pill (or auto-titled block card); fill in (`SSH Athena`, `Weekly Review Prompt`) to hide the payload behind a clean label.
   - **Auto Mode Switch (`Inline pill` ↔ `Block card`):** Automatically chooses Inline when single-line and Block when multi-line (with a manual toggle pill if you want a compact block card for a single long line or a collapsed block!).
   - **Live Preview Strip:** Shows the exact rendered pill or card header in real time before insertion.
   - **Zero-friction Commit:** `Enter` (in single-line mode) or `Cmd/Ctrl+Enter` (always) inserts the canonical Markdown in a single undoable editor transaction, closes the composer, and places the cursor immediately *after* the closing backtick (or on the blank line below the closing fence) so Live Preview renders the new button immediately and you can keep typing without interruption.

2. **Gear 2 — Selection & Direct Inline Shortcuts:**
   - **Wrap Selection (`Insert / convert copy button` command):** If text is selected (e.g., Vim visual mode `v...`), invoking the command opens the Composer pre-filled with that exact selection (and a 1-key `Enter` immediately replaces the selection with the copy pill/card in one undo step).
   - **Direct Typing:** Anyone in Source mode or wanting zero popups can simply type `` `copy>> foo` `` or `` `copy[Label]>> foo` `` (or ```` ```copy ````); as soon as the cursor leaves the span, it renders into a pill/card.

3. **Editing Existing Buttons (No Raw-Syntax Wrestling):**
   - Moving the keyboard cursor inside a pill (`h`/`l`/arrows) reveals the raw Markdown automatically (matching Obsidian Live Preview and `bob-ledger-tools`'s `[type::]` / `[fresh::]` marks).
   - Clicking the subtle hover `✎` edit icon (or `Alt+Click` on a pill / clicking `Edit` on a block card / running `Edit copy button under cursor`) re-opens the Composer pre-filled with the current Label & Payload and commits updates in one undoable transaction.

---

## 5. Visual & Interaction Design ("Intuitive, Reliable, Beautiful")

Every visual token should strictly inherit Obsidian CSS variables (`--interactive-accent`, `--background-primary`, `--background-secondary`, `--background-modifier-border`, `--background-modifier-hover`, `--text-normal`, `--text-muted`, `--color-green`, `--radius-s`/`m`, `color-mix(in srgb, ...)`), with zero hardcoded hex colors and full `prefers-reduced-motion` support—matching `bob-ledger-tools/styles.css` and `bob-navigation-hotkeys/styles.css`.

### 5.1 Inline Copy Pill Anatomy & Tactile Feedback

```
  Resting (self-labeled):    [ ⧉  ssh bryan@athena ]
  Resting (custom-labeled):  [ ⧉  SSH Athena ]
  Hover:                     [ ⧉  SSH Athena  ✎ ]   ──▶ Tooltip: "Click to copy: ssh bryan@athena · Alt-click to edit"
  Clicked (1.2s pulse):      [ ✓  SSH Athena ]       (green icon + soft green ring/tint; ZERO width change!)
```

**Three critical visual/UX polish rules:**

1. **Zero-Reflow Click Morph (No Text Jitter):**
   Never change the pill's text string to `"Copied!"` inside an inline paragraph—changing text width shifts every word after it on the line. Instead, swap the leading Lucide `copy` icon (`⧉`) in place to a green Lucide `check` icon (`✓`), pulse a soft green border/tint (`color-mix(in srgb, var(--color-green) 16%, transparent)`), and optionally show a brief Obsidian `Notice("Copied: ssh bryan@athena")` (truncated cleanly at ~60 chars). Surrounding text stays pixel-stationary!
2. **Distinguish Action Pills from Static Inline Code:**
   - Plain inline code stays flat muted monospace; Copy Pills use a crisp `1px solid` border (`color-mix(in srgb, var(--interactive-accent) 28%, var(--background-modifier-border))`), a delicate `6%` accent tint, a subtle `copy` glyph on the left (`13px`), `pointer` cursor, and gentle `translateY(-0.5px)` lift on hover.
   - Self-labeled pills render in `--font-monospace` (`0.88em`) so commands look like commands; custom-labeled pills render in `--font-interface` (`0.9em`, weight `500`) so they read like tactile UI chips.
   - Very long self-labeled pills cap around `max-width: 48ch` with `text-overflow: ellipsis`, showing the full value in the hover tooltip.
3. **Click = Copy, Never Accidental Unfold:**
   In Live Preview, `WidgetType.ignoreEvent()` returns `true` and `mousedown` calls `preventDefault()`. That guarantees clicking the pill **always copies** and never drops the CM6 cursor into the span mid-click. Only keyboard navigation (`h`/`l`/arrows), `Alt+Click`, or the hover-only trailing `✎` icon edits it.

### 5.2 Block Copy Card Anatomy

```
┌────────────────────────────────────────────────────────────────────┐
│ ⧉  Weekly Review Prompt   4 lines · 118 chars        [✎] [⧉ Copy] │
├────────────────────────────────────────────────────────────────────┤
│ Review my open tasks in #sase and summarize:                       │
│ 1. What moved forward                                              │
│ 2. What is blocked                                                 │
└────────────────────────────────────────────────────────────────────┘
```

- **Header:** Compact interface bar (`0.4em 0.7em`), tabular-nums line/char counter in `--text-muted`, optional collapse toggle (`:::collapsed Title` renders *only* the sleek header bar as a clickable compact banner!), subtle `✎` edit button, and a crisp fixed-width `Copy` → `✓ Copied` button on the right.
- **Body:** Pre-wrapped (`white-space: pre-wrap`), comfortable max-height (`~16em` with clean scroll) so giant 50-line prompts never hijack an entire note view, and subtle `user-select: text` in case you want to inspect or copy a single word.

---

## 6. Reliability, Edge Cases & Architecture Details

1. **Live Preview Rendering (`ViewPlugin` + `Decoration.replace`):**
   - Scan only `view.visibleRanges` (matching `bob-ledger-tools`), verify `editorLivePreviewField` is active (never replace in Source mode!), check `syntaxTree(view.state)` for `InlineCode` nodes (skipping `FencedCode`, `Frontmatter`, `Comment`), and reveal raw Markdown whenever any selection range overlaps `[from, to]`.
   - Mark the `WidgetType` with `ignoreEvent() { return true; }` and validate `eq(other)` on `(label, payload, isSelfLabeled)` so typing elsewhere in the note never flickers or drops active `✓ Copied` pulse state.
2. **Reading View, Callouts, Tables & Embeds (`registerMarkdownPostProcessor`):**
   - Post-processor scans `el.querySelectorAll("code")` excluding `pre > code`, parses matching `copy>>` / `copy[Label]>>` inner text, and replaces the `<code>` element with the identical DOM builder (`buildCopyPillElement`).
   - Uses `registerMarkdownCodeBlockProcessor("copy", ...)` for multi-line cards, registering a `MarkdownRenderChild` to clear active feedback timers cleanly on unload.
   - **Dataview DOM Safety (Bob-specific lesson):** As documented in `bob-plugins`'s `279-plugin-task-theme-marks.js` and `138-task-tag-marks.js`, Dataview re-scans `innerHTML` for `::` inline fields. Keep tooltips (`aria-label` / `title`) sanitized or free of raw `::` (and store payload in a JS `WeakMap`/closure or sanitized attribute rather than raw unguarded DOM text when Dataview could scan it).
3. **Clipboard Write Resilience (Desktop & Mobile):**
   - Primary write via `await navigator.clipboard.writeText(payload)` inside the direct click gesture.
   - Desktop fallback: if `navigator.clipboard.writeText` fails in an Electron edge case, try `require("electron")?.clipboard?.writeText(payload)` when `!Platform.isMobileApp`.
   - Never show `✓ Copied` unless the write succeeds; on failure, flash a muted warning pulse and `Notice("Could not copy to clipboard")`.
4. **Accessibility & Keyboard Parity:**
   - Render pills as real `<button type="button">` (or keyboard-focusable `role="button"` with `Enter`/`Space` activation and `:focus-visible` `outline: 2px solid var(--interactive-accent)`).
   - Add palette commands `Copy button under cursor` and `Edit copy button under cursor` so Vim/keyboard users can trigger or edit any pill/card without touching a mouse.
   - Add `Toggle copy button rendering` (session toggle, matching `bob-ledger-tools` mark toggles) to temporarily inspect raw Markdown across a note.

---

## 7. Recommended Placement & Implementation Blueprint

### Repo & Plugin Placement

Create a new, focused plugin **`plugins/bob-copy-buttons/`** inside `bob-plugins` (`isDesktopOnly: false`), deployed via `bob plugins sync`, rather than folding this into `bob-ledger-tools` (already 329 fragments) or `bob-navigation-hotkeys`:
- Keeps copy-button rendering completely decoupled from `bob` CLI subprocesses and GTD ledger state, so it works reliably on **Linux, macOS, and Obsidian Mobile**.
- Gives users a clean toggle in Obsidian Community Plugins and follows the `bob-emoji` / `bob-vim-yank-flash` pattern.

### Proposed Module Layout (Following `bob-plugins` Source-Build Pattern)

```text
plugins/bob-copy-buttons/
├── manifest.json             # id: "bob-copy-buttons", minAppVersion: "1.8.7", isDesktopOnly: false
├── styles.css                # Theme-native pill, card, hover edit, zero-reflow pulse, composer modal
├── main.js                   # Generated by `npm run build`
└── src/
    ├── fragments.json
    ├── 010-parser.js         # Pure CommonMark backtick unwrap/wrap, inline & ```copy block parse/serialize
    ├── 020-trigger.js        # Pure `;;` trigger detection + syntax-tree/code/frontmatter exclusions
    ├── 030-clipboard.js      # Safe clipboard write (navigator.clipboard + Electron desktop fallback) + pulse DOM
    ├── 040-dom-widgets.js    # Shared pill & card DOM builders + Live Preview WidgetType
    ├── 050-composer-modal.js # Keyboard-first Composer modal (clipboard Tab-paste, auto inline/block, live preview)
    └── 060-plugin.js         # ViewPlugin, MarkdownPostProcessor, CodeBlockProcessor, commands, settings
```

### Phased Rollout

1. **Phase 1 — Core Parser, Inline Pills, Block Cards & `;;` Composer:**
   Pure parser/serializer + unit tests in `node --test` (covering backtick escaping, pipes/colons/`::`/`#tags`/`[[links]]` inside payloads, `::: Title` block headers, and `;;` trigger guards), Live Preview CM6 `ViewPlugin`, Reading View post-processor & `copy` codeblock processor, and the `;;` Composer Modal with `Tab` clipboard import and selection wrapping.
2. **Phase 2 — Ergonomic Polish & Keyboard Parity:**
   `Alt+Click` and hover `✎` edit-in-composer, `Copy/Edit button under cursor` commands, `:::collapsed` banner mode for long prompts, and optional recent-snippets history in the composer.
3. **Phase 3 (Optional Future Enhancement) — Parameterized / Dynamic Tokens:**
   Only if a real need emerges later, consider opt-in date placeholders (e.g., `{{date}}`)—explicitly kept **out** of v1 so every button remains 100% literal, predictable, and WYSIWYG ("what you configured is byte-for-byte what lands on your clipboard").

---

## Summary Recommendation

Do **not** implement this with `obsidian://` links, raw `<button>` HTML, or Meta Bind `BUTTON[id]` + JS blocks. Build **`bob-copy-buttons`** in `bob-plugins` using **CommonMark-shielded inline pills (`` `copy>> ...` `` / `` `copy[Label]>> ...` ``) + ` ```copy ` verbatim cards**, created effortlessly via a **collision-guarded `;;` typing trigger into a live-preview Composer** (with 1-key `Tab` clipboard import and selection wrapping), rendered as **zero-reflow, theme-native tactile pills** across Live Preview, Reading View, Desktop, and Mobile.
