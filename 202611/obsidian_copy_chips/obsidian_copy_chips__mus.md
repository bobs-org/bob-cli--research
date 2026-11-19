# Click-to-Copy Buttons/Links in Obsidian — Research Report (__mus)

**Researcher:** mus · **Date:** 2026-11-19 · **Swarm:** 5-researcher (mus independent)
**Question:** *I wish there was some way to create a button/link in Obsidian that, when pressed, copied some (configurable at creation) text to my clipboard. It should be easy to create a new instance by typing. Lead the design: intuitive, reliable, beautiful. Is this a good idea? Would you take a different approach? Adjust requirements as justified. End with a recommended solution.*

---

## 1. TL;DR and recommended solution

**Yes — build it, but build it small.** The request is a good idea in its narrow form (static, author-defined text → clipboard on click). It is a bad idea in its expansive form (a snippet manager, template engine, or secret store). Scope it to the narrow form.

**Recommended solution: a tiny first-party Bob plugin (`bob-copy`) that treats a standard Markdown link as the button source, plus a one-command authoring flow and first-class button styling.**

Authoring syntax (what the user types):

```markdown
[📋 Deploy preview](copy:vercel --prod --yes)
```

- Standard Markdown link. Nothing new to learn. Renders as a link even with the plugin off (graceful degradation).
- Destination scheme is `copy:` + payload. If the payload is omitted — `[vercel --prod --yes](copy)` — the plugin copies the **label text itself**. This is the key typing optimization: the common cheat-sheet case requires zero duplication.
- For text with spaces, wrap the URL in angle brackets (standard Markdown, no new escaping to learn):

```markdown
[📋 Greeting](<copy:Hello world, this is Bryan>)
```

- A command **“Copy button: insert from clipboard / selection”** (hotkey-able) generates the link so the user never hand-encodes anything. Select text → hotkey → link is inserted. Copy something → hotkey with no selection → link with that payload is inserted.

Rendering (what the user sees):

- A `registerMarkdownPostProcessor` rewrites `a[href^="copy:"]` / `a[href="copy"]` into a pill button (clipboard icon + label) in **both Reading and Live Preview**. Not a code-block widget, so it works **inline inside a sentence**, in lists, tables, and callouts.
- Click → `navigator.clipboard.writeText` (with `execCommand` fallback) → inline morph to check + “Copied” + Obsidian `Notice` on failure only. No modal, no navigation, no new tab.
- Styling is ~60 lines of CSS using Obsidian variables (`--background-primary`, `--interactive-accent`, etc.), so it is automatically beautiful in every theme, dark/light, desktop/mobile, with a 32px+ touch target.

Why not just adopt an existing community plugin? Documented below, but in short:

| Option | Verdict |
|---|---|
| `copy-text-protocol` (`obsidian://copy?text=…`) | Closest existing fit; proves the link-shape works. But `obsidian://` links look like links (not buttons), need manual URL-encoding, and route through the OS protocol handler (slower, no inline success animation, fragile on mobile/sync). Good inspiration, wrong finish. |
| Meta Bind `BUTTON` + inline JS / Templater | Powerful but heavyweight: requires Meta Bind (+ often Templater/JS Engine), verbose block syntax, well-documented user confusion (forum threads show repeated failures wiring copy actions). Overkill for static copy and a reliability liability. |
| Buttons plugin (`shabegom/buttons`, `type: copy`) | Deprecated by its own maintainer in favor of Meta Bind; block-only, not inline; unmaintained. Do not adopt. |
| ClipBook / code-block snippet lists | Excellent for vaults of secrets/API keys (structured rows + mask + per-row copy). Wrong shape for this request: block-only, YAML-ish authoring, not inline-prose-friendly. Use it if the real need turns out to be a secrets cheat-sheet, not prose-embedded buttons. |
| Booklet `> [!copy]` callout | Block-only, Booklet-format-coupled. Elegant inside Booklet notes, irrelevant outside them. |
| OS-wide snippet expander (Raycast / Espanso / Alfred) | Better than any Obsidian button for “type short → expand long” **outside** Obsidian. Does not solve “click a button in a shared note and paste into a terminal/phone.” Complementary, not a substitute. |

**If you want zero new code tomorrow:** install `copy-text-protocol` and its “paste clipboard as link” command. If you want the thing actually requested — easy to type, intuitive, reliable, beautiful — build the ~200-line `bob-copy` plugin described in §6. It reuses the proven link-shape idea but fixes authoring (no hand-encoding), rendering (real button, inline, both modes), and feedback (inline morph, silent on success).

---

## 2. Is this a good idea? Critique of the plan

### 2.1 What is good about it

1. **Real, recurring pain.** Cheat-sheets (commands, prompts, email boilerplate, addresses, query strings), prompt libraries, and onboarding notes all have the same loop: find the text → select precisely → copy → switch app → paste. A one-click target removes the precision-selection step, which is the step that fails on mobile and trackpads.
2. **Shareable.** Unlike a personal Raycast snippet, a button in a note travels with the vault (Sync, Publish excerpt, shared cheat-sheet). The recipient gets the affordance without installing your system-wide toolchain.
3. **Small blast radius.** Static text → clipboard is side-effect-free (no vault mutation, no network). It cannot corrupt notes the way template-insert or command-run buttons can. That makes it a safe first custom-button primitive.
4. **Precedent exists.** The forum request “I want to make a button to copy text I specify to the clipboard” (Obsidian Forum #50005) and the 3k-download `copy-text-protocol` plugin confirm independent demand. The idea is not idiosyncratic.

### 2.2 Risks and why the plan needs adjustments

1. **“Button/link” hides two different UX contracts.** A *link* promises navigation; a *button* promises action. Rendering an action as a blue underlined link is unintuitive (users hesitate: “where will this take me?”). **Adjustment: author as a link (easy to type), render as a button (clear affordance).** Authoring shape and rendered shape should differ deliberately.
2. **“Configurable at creation” will creep.** The first follow-up requests are predictable: variables (`copy my name here`), multiple payloads, “copy rendered Markdown vs source,” history, and secrets masking. Each one doubles the design. **Adjustment: v1 copies one static string verbatim. No variables, no templating, no multi-copy, no masking.** Document the non-goals explicitly (see §5).
3. **Typing UX is the whole game, and raw URLs lose it.** `obsidian://copy?text=Hello%20world%21` is hostile to type by hand. Any design that requires the author to URL-encode by hand fails the “easy by typing” requirement no matter how pretty the button is. **Adjustment: make hand-typing the common case work with zero encoding** (label-copies-itself shorthand + angle-bracket spaces + authoring command that encodes for you).
4. **Reliability has a long tail.** Clipboard writes require a user gesture and a secure context; `navigator.clipboard` can reject (permissions, iframe sandbox, mobile WebView quirks); Live Preview and Reading mode have different DOM lifecycles; badly-escaped payloads break Markdown parsing. A naive implementation works in the demo note and fails in tables, footnotes, and on iOS. **Adjustment: require both-modes support, a fallback path, and failure feedback as acceptance criteria** (§6.4).
5. **Secrets in plain text.** Copy buttons are tempting for passwords/tokens. Those payloads then live in plain-text Markdown, sync everywhere, and leak into search/Publish/backlinks. **Adjustment: explicitly non-goal v1 for secrets; point secret-heavy use at ClipBook (masking + dedicated UI) and document “do not use copy buttons for high-value secrets.”**
6. **Beauty is not optional chrome.** An ugly button will not be trusted (“will this navigate away?”) and will not be used in shared notes. Budget the CSS and the success micro-interaction from day one; they are the feature, not polish.

### 2.3 Would I take a different approach?

For the stated need — **clickable, in-note, paste-elsewhere text** — no: an in-note button is the right shape. I would *not* reframe it as:

- **A Templater/QuickAdd template** (inserts text *into the note*, does not put it on the clipboard for use elsewhere — wrong destination).
- **A Commander hotkey** (global action, not contextual to a note position; undiscoverable to readers of a shared note).
- **An OS snippet expander** (better for personal typing expansion everywhere, but does not travel with the note and does not help on mobile readers of the vault).

The one reframing worth naming: **if the actual corpus is 50+ reusable snippets rather than a handful of in-prose buttons, build/adopt a snippet library (ClipBook-style list + fuzzy-find copy command) instead of scattering 50 inline buttons.** Inline buttons win for ≤ ~a dozen contextual copies; a library wins past that. The recommended plugin supports both ends by also registering a “copy any button payload in vault” fuzzy command for free (payload index is trivial once links are parsed).

---

## 3. Landscape: what exists today

Researched via Obsidian community plugin listings, forum threads, and plugin docs (November 2026).

### 3.1 Buttons plugin (`shabegom/buttons`)

- Block syntax (` ```button … type copy … ``` `), supports `copy` among `command / link / template / calculation` types, chainable.
- **Status: deprecated by its own author** (“Don’t use this! Use Meta Bind instead”). Last meaningful update February 2024. Do not adopt for new work.
- Shape mismatch anyway: block-only, verbose to type, cannot sit inline in a sentence.

### 3.2 Meta Bind (`mProjectsCode/obsidian-meta-bind-plugin`)

- The current community standard for note-embedded controls (`INPUT`, `BUTTON`, `VIEW`, `TABLE`). Button builder emits:

```yaml
```meta-bind-button
label: Greeting
icon: ""
style: primary
action:
  type: inlineJS
  code: "navigator.clipboard.writeText('Hello world')"
```
```

- **Pros:** maintained, styled buttons, huge action surface (commands, Templater, JS, notebooks).
- **Cons for this request:** (a) block-only, 6+ lines to author one copy — fails “easy by typing”; (b) copy requires inline-JS or a Templater shim, which is exactly the construct confused users struggle with in Forum #50005 and #101664; (c) pulls a large dependency (plus often Templater) for a static-string job; (d) inline-JS execution widens the trust surface of every note.
- **Verdict:** right tool for *programmable* buttons; wrong tool for *static copy* buttons.

### 3.3 `copy-text-protocol` (`jldiaz/copy-protocol-plugin`, ~3k downloads)

- Registers `obsidian://copy?text=…`. Clicking copies + shows a confirmation notice. Ships a command that converts clipboard/selection into a ready-made link (this command is the best authoring idea in the existing landscape).
- Syntax: `[Click to copy](obsidian://copy?text=Your-text-here)`; spaces need `<…>` wrapping; other characters need encoding.
- **Pros:** proves link-shaped authoring works; tiny; authoring command included.
- **Cons:** (a) renders as a plain link (no button affordance) unless the user adds CSS; (b) `obsidian://` round-trips through the protocol handler rather than an in-note click handler — no inline success state, extra failure modes, and it *navigates* (even if silently), which is surprising; (c) hand-authoring still requires encoding; (d) protocol links in Publish/exports are dead or confusing.
- **Verdict:** best stopgap to install today; design to surpass, not to adopt as the permanent answer.

### 3.4 ClipBook (`zkbkb/obsidian-ClipBook`)

- ` ```clipbook ` fenced blocks render as structured key-value lists with per-row copy buttons (`navigator.clipboard.writeText` + icon-swap feedback), masking, inline edit, fuzzy “copy value…” command.
- **Pros:** superb for the secrets/API-keys cheat-sheet; masking, search, and mobile-friendly rows.
- **Cons:** block/table shape only; authoring is a mini-format, not “type in a sentence.” Overkill for one-off inline copies.
- **Verdict:** adopt *alongside* the recommended plugin if the vault needs a secrets page; do not stretch it to cover inline prose buttons.

### 3.5 Booklet `> [!copy]` callout (format 0.19+)

- `> [!copy|id of:a,b,c] Button label` renders one Obsidian-styled button; pressing copies the callout body. Mobile-tested, theme-aware.
- **Pros:** beautiful, zero-JS authoring, body can be multi-line prose.
- **Cons:** Booklet-note-coupled and block-level only. Useless for “copy this command mid-sentence in a daily note.”
- **Verdict:** copy the *interaction polish* (single button, body-as-payload, confirmation), not the syntax.

### 3.6 Templater `tp.system.clipboard()` / `navigator.clipboard` in templates, Commander, QuickAdd, Code Block Copy

- All solve adjacent jobs (insert-at-cursor, run-command, copy-codeblock). None provides “author an inline, labeled, static copy target by typing.” Commander hotkeys are undiscoverable in shared notes; Templater inserts into the note rather than onto the clipboard; Code Block Copy only decorates code fences.
- **Verdict:** complementary. The recommended plugin should not duplicate them.

### Comparison matrix

| Approach | Inline in prose? | Typing cost | Both modes? | Feedback | Dependency weight | Maintainability |
|---|---|---|---|---|---|---|
| Recommended `bob-copy` link-button | Yes | 1 line; label-shorthand | Yes (postProcessor) | Inline morph + Notice on fail | None (Bob-owned) | Bob-owned, ~200 LOC |
| `copy-text-protocol` | Yes (as link) | 1 line + encoding | Yes (protocol) | Notice only | 1 small plugin | Third-party |
| Meta Bind + JS | No (block) | 6+ lines YAML | Yes | Configurable | Meta Bind (+Templater) | Heavy |
| Buttons `type: copy` | No (block) | Block + args | Partial | Basic | Deprecated | Dead end |
| ClipBook | No (list rows) | Mini-format | Reading-focused | Icon swap | 1 plugin | Good for secrets |
| Booklet `copy` callout | No (block) | 2 lines | Booklet view | Button + confirm | Booklet | Niche |

---

## 4. Requirements (adjusted)

Keep the user’s three adjectives as acceptance gates, with these adjustments called out:

1. **Easy to create by typing (tightened).** “Type a link” must be the whole skill. Concretely: (a) one-line standard link syntax; (b) zero-encoding common case (`[text](copy)` copies `text`); (c) spaces work via `<…>` with no encoding; (d) a selection-to-button command so encoding is never done by hand; (e) graceful degradation to a readable link with the plugin off. *Adjustment: explicitly require the label-shorthand and the authoring command — the original “configurable at creation” under-specified typing cost.*
2. **Intuitive (tightened).** Must *look* like a button, not a navigation link; must not navigate, open tabs, or edit the note on click; success must be visible within 200ms at the button itself; failure must explain itself. *Adjustment: add “never navigates, never mutates the note” as a hard rule.*
3. **Reliable (new explicit gate).** Works in Reading + Live Preview (+ mobile), handles multi-line/code/Unicode/emoji payloads, never breaks surrounding Markdown, reports clipboard denial instead of failing silently, and does not execute arbitrary JS from note content. *Adjustment: the original request implied reliability; make it testable acceptance criteria.*
4. **Beautiful (tightened).** Theme-aware pill (icon + label), visible hover/focus/active states, keyboard-focusable with `:focus-visible` ring, success morph, reduced-motion respect, 32px+ touch target. *Adjustment: beauty includes motion and accessibility, not just static CSS.*
5. **Explicit non-goals for v1 (new).** No variables/interpolation, no multi-payload or chained copies, no vault writes, no secrets masking, no history/clipboard manager, no Publish execution (render as disabled with tooltip). Each is a named future, not a v1 slip.

---

## 5. Design: `bob-copy`

### 5.1 Authoring syntax (normative)

Two forms, both standard Markdown links:

```markdown
<!-- Form 1: label IS the payload (cheat-sheet case, zero duplication) -->
[vercel --prod --yes](copy)

<!-- Form 2: label differs from payload -->
[📋 Deploy preview](copy:vercel --prod --yes)

<!-- Spaces / punctuation: angle-bracket destination (standard Markdown) -->
[📋 Greeting](<copy:Hello world, this is Bryan>)

<!-- Multi-line payload: reference-style link keeps prose readable -->
[📋 Standup template][standup-tpl]

[standup-tpl]: <copy:Today I…%0ABlockers: …%0APlan: …>
```

Rules:

- Scheme is exactly `copy:` or bare `copy`. Case-insensitive. Leading/trailing whitespace in payload is preserved verbatim except one optional trailing newline strip (documented).
- Payload transport is the link destination; the authoring command percent-encodes on insert, and the renderer percent-decodes (plus `%0A` → newline). Hand-typed payloads without encoding work until they hit `)` — at which point the author uses `<…>` or the command. This matches how Markdown authors already handle URLs with spaces/parens, so there is nothing new to memorize.
- Reference-style links are the blessed multi-line pattern: the payload lives at the bottom of the note (or in a dedicated “copy library” note via `![[…]]`? no — v1 keeps definitions local; cross-note payloads are a named future), keeping prose scannable.
- Payload cap: 8 KB v1 (generous for commands/prompts; prevents accidental whole-note pastes). Over-cap renders as a disabled button with tooltip “payload too long.”
- No JS, no template tags, no field lookups in payloads. What you type is what gets copied, byte-for-byte. This is a deliberate trust decision: note content stays data.

Why this shape wins the “easy by typing” test:

- **Fewest keystrokes for the common case.** `[text](copy)` is 8 characters of overhead — shorter than any code fence, callout, or YAML block, and it uses only characters already on mobile keyboards.
- **No mode switch.** Links are typed in every Obsidian mode already; codeblocks and callouts require remembering fences and identifiers.
- **Autocompletion-friendly.** Link brackets already participate in Obsidian’s editor behaviors; a future autocomplete can suggest `(copy…)` after `[`.
- **Degrades gracefully.** With the plugin disabled the source still reads as a link with a `copy:…` destination — odd but legible — whereas a `meta-bind-button` block with the plugin off is dead YAML noise.

### 5.2 Rendering

- Implement with **`registerMarkdownPostProcessor`** (inline-capable), not `registerMarkdownCodeBlockProcessor` (block-only). Walk `a.internal-link, a.external-link` candidates, match `href === "copy"` or `href.toLowerCase().startsWith("copy:")`, replace the anchor with a `<button class="bob-copy-btn">` carrying the decoded payload in a `data-` attribute (never in an executable context).
- Must run in **Reading and Live Preview**. (Source mode shows raw Markdown — acceptable and expected.)
- Visual: `<svg clipboard icon> Label` pill. CSS sketch (theme-aware, no hardcoded colors):

```css
.bob-copy-btn {
  display: inline-flex; align-items: center; gap: 0.45em;
  padding: 0.15em 0.7em; border-radius: 999px;
  border: 1px solid var(--background-modifier-border);
  background: var(--interactive-normal, var(--background-secondary));
  font: inherit; font-size: 0.92em; line-height: 1.6;
  min-height: 32px; cursor: pointer;
  transition: transform 80ms ease, background 120ms ease;
}
.bob-copy-btn:hover { background: var(--interactive-hover); transform: translateY(-1px); }
.bob-copy-btn:active { transform: translateY(0) scale(0.98); }
.bob-copy-btn:focus-visible { outline: 2px solid var(--interactive-accent); outline-offset: 2px; }
.bob-copy-btn.is-success { border-color: var(--color-green); }
@media (prefers-reduced-motion: reduce) { .bob-copy-btn { transition: none; } }
```

- Success micro-interaction: icon swaps clipboard → check, label appends “Copied” for 1.2s, then reverts. Failure: shake-free — keep the button steady, show `new Notice("Copy failed: …")` with the reason (denied, too long, empty). Never use `alert`.
- Keyboard: real `<button>`, tab-focusable, `Enter`/`Space` activates. Screen-reader label: `aria-label="Copy <label> to clipboard"`.
- Publish/exports: payloads render as disabled buttons with `title="Copy buttons are inert in published pages"` — never attempt clipboard writes outside the app sandbox, and never leak payloads into `href`s that crawlers follow.

### 5.3 Clipboard implementation (reliability)

```ts
async function copyText(text: string): Promise<void> {
  try {
    await navigator.clipboard.writeText(text);
  } catch {
    // Fallback for older WebViews / denied async API: hidden textarea + execCommand.
    const ta = document.createElement("textarea");
    ta.value = text; ta.setAttribute("readonly", "");
    ta.style.cssText = "position:fixed;opacity:0;top:0";
    document.body.appendChild(ta); ta.select();
    try { if (!document.execCommand("copy")) throw new Error("execCommand returned false"); }
    finally { ta.remove(); }
  }
}
```

- Click is the user gesture, so permissions are satisfied in the normal case. The fallback covers the long tail (some mobile WebViews, restricted contexts).
- Verify byte fidelity with tests: trailing newlines, leading spaces, tabs, emoji/Unicode, `%`, `|`, `"`, `'`, backticks, and 8 KB boundary. Multi-line via `%0A` round-trips to real newlines.
- Do not `trim()` payloads silently. If trimming, document exactly what is trimmed (recommendation: strip at most one trailing `\n` from reference-style definitions, since editors add it).

### 5.4 Authoring command (the typing story, end to end)

| Gesture | Result |
|---|---|
| Select text, run “Copy button: wrap selection as copy button” (hotkey, e.g. `Ctrl/Cmd+Shift+C`) | Selection becomes `[selection](copy)` if no custom label wanted, or opens a two-field modal (Label defaults to selection, Payload defaults to selection) and inserts `[Label](<copy:encoded>)`. |
| No selection, clipboard non-empty, run “Copy button: insert from clipboard” | Inserts `[📋 <first-30-chars>](<copy:encoded-clipboard>)` at cursor; label text selected for immediate retype. |
| Type manually | `[label](copy)` or `[label](copy:payload)` with `<…>` for spaces — no command needed. |

Both commands percent-encode correctly, so hand-encoding is never required. This is the direct answer to “think hard about typing”: **optimize the zero-duplication case in syntax, and automate encoding in commands.**

### 5.5 Placement in Bryan’s stack

- Implement as a new small plugin in the **`bob-plugins` monorepo** (source of truth; deploy via `bob plugins sync` — never edit `~/bob/` directly). Name: `bob-copy`.
- No new `bob-cli` subcommand is needed for v1. A future `bob copy` CLI (fuzzy-find any copy payload in the vault and copy it) is a natural phase 2 and falls out of the payload index for free.
- Coordinate with `bob-mac-capture` only to the extent that capture previews must not execute copy buttons (render inert in preview panes) — a one-line guard via the same disabled-render path as Publish.

### 5.6 Edge cases and decisions

- **Empty payload** (`[x](copy:)`): render disabled, tooltip “nothing to copy.” Do not copy empty string silently (destroys clipboard).
- **`|` and `]` in labels:** standard Markdown escaping applies; document it once with an example. Do not invent a new escape character.
- **Nested formatting in labels** (`[**bold**](copy:x)`): renderer uses `textContent` of the anchor as the fallback payload for bare `(copy)` and preserves inner HTML for display in explicit-payload form. Simple, predictable.
- **Tables, lists, callouts, footnotes:** postProcessor handles all uniformly since it operates on rendered anchors. Add tests for each container.
- **Sync/conflict:** payloads are plain note text — no journal, no last-writer-wins state, no conflicts beyond normal Markdown merge. This is a feature relative to stateful button plugins.
- **Security:** payloads are inert strings. No `eval`, no `Function()`, no `innerHTML` insertion of payload. `textContent` / `data-*` only. Content-Security-Policy-safe.

---

## 6. Alternatives considered and why they lose for this brief

1. **“Just use Meta Bind.”** Loses on typing cost (6+ lines vs 1), dependency weight, and documented user confusion for exactly the copy action. Revisit only if copy buttons later need logic (conditionals, vault writes) — at which point Meta Bind becomes the execution layer and `bob-copy` remains the authoring shorthand that *emits* Meta Bind blocks for complex cases (a viable phase 3, not v1).
2. **“Just use `copy-text-protocol`.”** Loses on affordance (link vs button), protocol-handler indirection, and hand-encoding. Adopt today as a stopgap; supersede with `bob-copy`.
3. **“Snippet expander / Raycast.”** Loses on shareability and mobile-vault contexts; wins on system-wide typing. Do both — they solve different destinations (cursor-expansion vs clipboard-via-click).
4. **“Callout / codeblock button.”** Loses on inline placement, which the request’s “button/link in Obsidian by typing” phrasing implies matters (links are inline; blocks are not). Keep block shapes for libraries (ClipBook), inline shape for prose.

---

## 7. Acceptance criteria (what “done” means)

- [ ] `[text](copy)` and `[label](copy:payload)` / `[label](<copy:payload with spaces>)` render as pill buttons in Reading **and** Live Preview, inline in sentences, lists, tables, callouts.
- [ ] Click copies bytes verbatim (fidelity tests: Unicode, emoji, newlines, tabs, 8 KB boundary) with `execCommand` fallback; failure shows a `Notice`, never silence.
- [ ] Success morph (icon → check, “Copied” 1.2s) at the button; `prefers-reduced-motion` respected; keyboard + screen-reader operable.
- [ ] Both authoring commands work (wrap-selection, insert-from-clipboard) with correct encoding; manual typing needs no encoding for the common cases.
- [ ] With plugin off, source remains legible Markdown links (no YAML noise).
- [ ] Disabled states for empty payload, over-cap payload, Publish/preview contexts.
- [ ] No vault writes on click; no JS execution from note content; theme-aware CSS only via Obsidian variables.

---

## 8. Recommended solution (restated for the decision)

**Build `bob-copy`: a ~200-line Bob-owned plugin (in `bob-plugins`, deployed via `bob plugins sync`) implementing §5 exactly.** Author as a standard link, render as a button, automate encoding with two commands, copy verbatim with fallback, confirm inline.

- **If Bryan wants value this week with zero code:** install `copy-text-protocol`, assign its “paste clipboard as link” hotkey, and live with link-styled copies while `bob-copy` is built. Treat it as a prototype to validate which payloads recur — that usage log becomes the seed library for `bob-copy`’s phase-2 fuzzy command.
- **If the real corpus turns out to be secrets-heavy:** add ClipBook for the secrets page; keep `bob-copy` for inline prose. They compose.
- **Do not** adopt Buttons (deprecated), do not standardize on Meta Bind for static copies, and do not expand v1 scope to variables/masking/history. Those are the traps this research identifies; the recommendation avoids all three.

*Report independence note: this report was written without consulting peer swarm reports (`__cdx`, `__cld`, `__grk`, `__gem`); any convergence with them comes from shared sources (community plugin listings, Obsidian forum threads, clipboard API docs), not from peer content.*
