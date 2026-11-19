# Copy chips in Obsidian: consolidated design and recommendation

**Date:** 2026-11-19 · **Lead:** consolidation of five independent swarm reports
(`__cdx`, `__cld`, `__grk`, `__mus`, `__gem`, in this directory) plus the lead's own
verification against the Bob vault config, the `bob-plugins` checkout, and the web.
Nothing was implemented or deployed.

## TL;DR

**Yes, build it — but as a *copy chip*, not a button framework.** All five researchers
independently reached the same verdict: the request is a real, recurring need (commands,
meeting URLs, account numbers, addresses, email/prompt templates that belong *in
context* in a note), no installed plugin covers it, and the off-the-shelf options all
fail at least one of the three stated bars (intuitive, reliable, beautiful).

**Recommended solution — a new, small `bob-copy-chips` plugin in `bob-plugins`:**

| You type | You see | A click copies |
| --- | --- | --- |
| `` `copy: ssh apollo` `` | ⧉ `ssh apollo` (monospace pill) | `ssh apollo` |
| `` `copy[Zoom]: https://zoom.us/j/123456789` `` | ⧉ Zoom (text-font pill) | the URL |
| a ` ```bob-copy Weekly status ` fence | a titled card with a Copy control | the fence body, byte-exact |

- **Authoring is ordinary Markdown**: an inline code span with a `copy:` prefix, or a
  `bob-copy` fence for multi-line text. Six characters of overhead, no encoding, no
  YAML, no IDs, no JavaScript. One hotkey — **Mod+Shift+Y**, "Make or edit copy chip",
  the sibling of the Copy card's Mod+Y — wraps a selection or the clipboard, takes an
  optional label, picks inline vs. block, and handles every escaping edge for you.
- **Rendering is a quiet, theme-native pill** (Lucide `copy` glyph, hairline border,
  Bob's existing chip tokens). On success the glyph becomes a green check and the chip
  pulses in the Bob Vim Yank Flash green — zero width change, no toast. Failures always
  show a Notice.
- **The payload is literal text, stored where it is used.** No variables, no secrets,
  no vault writes on render or click, and the exact text is always inspectable.
- **Keyboard parity:** the Mod+Y Copy card gains a `C` (Chip) row, and a palette
  command supports a vimrc exmap, so the feature is first-class in a Vim-mode vault.

## 1. Is this a good idea? (consensus critique)

**Yes, in its narrow form; no, in its expansive form.** The narrow form is: static,
author-chosen text → clipboard, in one gesture, from the note where the text already
makes sense. Reasons it is worth building (each held by ≥3 reports):

1. **The need recurs and the market proves it.** The community directory has at least
   ten single-purpose copy plugins (Copy Inline Code ~20k downloads, Copy Text Protocol
   ~3k, Clip Link, Easy Copy, Fast Copier, Prompt Block Copy, Callout Copy Buttons, …),
   and a 2022 forum thread asks for exactly this feature and never gets a working
   answer — its Buttons+Templater attempt made every button on a page copy the *last*
   payload ([forum #50005](https://forum.obsidian.md/t/i-want-to-make-a-button-to-copy-text-i-specify-to-the-clipboard/50005)).
2. **It fills the one empty cell in Bob's copy family.** `Mod+Y` (Copy card) copies
   *live context*: path, note name, block ID, `copy.templates`. Native fence copy
   handles *visible code blocks*. `bob ref code` copies *render-catalog code*. Capture
   `%c` moves the clipboard *into* the vault. Nothing today copies an *authored,
   note-local payload* on click. (cld's vault scan: of ~135k inline code spans outside
   fences, 8,196 start with `sase`, 4,022 with `bob` — the vault is full of payloads.)
3. **Selection-copy is the failing step.** In Live Preview, dragging a selection
   reveals the Markdown source under the cursor, so you grab stray backticks or miss an
   edge; on mobile it is worse. A chip removes precision selection entirely.
4. **Small blast radius.** Static text → clipboard is side-effect-free: no vault
   mutation, no network, no code execution. It is the safest possible first in-note
   control.
5. **Bob already owns every needed pattern**: CM6 Live Preview widgets, Reading-view
   post-processors, the `writeText → {ok, reason}` clipboard contract, chip CSS tokens,
   versioned cross-plugin APIs, xvfb/CDP e2e harnesses, and CPU budget tests.

**Where the original framing would go wrong** (adopted from all five critiques):

- *"Button" invites a button framework.* Meta Bind–style kits (YAML blocks, action
  catalogs, inline JS) are heavy to author, split definition from use, and put an
  application runtime inside notes. The right product is one verb: copy.
- *"Link" promises navigation.* An action rendered as a hyperlink makes readers
  hesitate ("where does this go?"), and link-scheme storage has concrete reliability
  problems in this vault (§3).
- *A mouse-only feature would rot in a Vim-mode vault.* Keyboard creation, activation,
  and editing are requirements, not polish.
- *It must not become a secret store.* The vault is plain text, git-synced across three
  hosts. Labels can hide a payload visually; they are presentation, not protection.
- *Scope creep is the main risk.* Variables, multi-payload, masking, history, and
  Publish support each roughly double the design. v1 copies one literal string,
  verbatim.

**Would we take a different approach?** Only at the margins. If the real corpus turns
out to be *dozens of reusable snippets used outside any note context*, an OS-level
expander (Raycast/Espanso/macOS Text Replacements) or a snippet-library picker is the
better retrieval interface — chips win for text that belongs beside its explanation.
And for a multi-line snippet that should already be *displayed* as code, the native
fence copy button is enough; `bob-copy` fences are for text that should read as a
titled card (prompts, emails, addresses), not a code listing.

## 2. Requirement adjustments (explicitly called out)

| # | Original | Adjusted | Why |
| --- | --- | --- | --- |
| A1 | "button/link" | **Inline chip** + **titled card** for multi-line | Fits prose, lists, tables; copies, never navigates or runs anything |
| A2 | "configurable text" | **Text + optional label**; unlabeled chips show their text | Short commands read best as themselves; long URLs/prompts need a short face; forcing both duplicates (`Copy ssh` → `ssh`) |
| A3 | "easy to create by typing" | **Memorable 6-char syntax + one make-or-edit hotkey**; no builder GUI, no autocomplete, no typing trigger | The text is new, so autocomplete has nothing to suggest; a global trigger (`;;`) adds vocabulary and collision surface for little gain |
| A4 | (unstated) | **Literal text only in v1** — no `{date}`, Templater, or JS | "What the file says is what gets copied"; Copy card `copy.templates` already does live substitution |
| A5 | (unstated) | **Keyboard parity**: Copy card `C` row, cursor commands, vimrc exmap | Click-only would be second-class here |
| A6 | (unstated) | **Exactness contract**: clipboard gets exactly the declared text, byte for byte; preview and clipboard never disagree | This is the operational meaning of "reliable", mirroring the Copy card rule |
| A7 | (unstated) | **Never hide the payload**: tooltip/preview always shows what will be copied | A chip that copies something you cannot see is how the wrong thing gets pasted |
| A8 | (unstated) | **Not a secret store**; documented non-goal | Plain text in git on three hosts |
| A9 | (unstated) | **Readable without the plugin** (GitHub, Bob site, PDF, plugin off) | Falls back to legible inline code / a fence, never YAML noise or a dead URL |
| A10 | (scope) | **Defer**: vault-wide snippet picker, `bob` CLI/Mac Capture integration, rich-text copy, Publish interactivity, `obsidian://copy` interop | Each is a named future, not a v1 slip |

## 3. The decisive choice: where the text lives

This was the only substantive disagreement between the five reports, and it determines
most of the "intuitive, reliable, beautiful" outcome.

- **Code-span camp** (cdx, cld, gem): an inline code span with a prefix
  (`` `copy: text` ``, `` `copy[Label]: text` ``; gem proposed `copy>>` instead of
  `copy:`).
- **Link-scheme camp** (grk, mus): a Markdown link `[Label](copy:payload)`, with
  `[text](copy)` as a label-copies-itself shorthand and `<…>` for spaces.

**Resolution: the code span wins**, on evidence rather than taste:

1. **No escaping, ever.** CommonMark already delimits code spans (longer backtick runs
   handle literal backticks), so the plugin never guesses where text ends and authors
   never percent-encode. Link destinations need `<…>` for spaces and encoding for `)`
   — exactly the "hostile to type" tax the request forbids.
2. **The payload is inert to every other parser in this vault.** Obsidian, Dataview,
   Tasks, Metadata Menu, and bob-cli all mask code spans. A `#tag`, `[due:: …]`, or
   `[[link]]` inside a payload stays dead text. Inside link syntax it can become a real
   tag, field, or graph node.
3. **Custom-scheme links render inconsistently across modes.** Clip Link's own source
   comments that Obsidian's renderer leaves unknown schemes as raw text and falls back
   to fragile regex/DOM rewriting; a current forum bug report shows `<foo://bar>`
   rendering as a link in Reading mode but *not* in editing modes
   ([forum #95952](https://forum.obsidian.md/t/link-with-custom-uri-scheme-e-g-foo-bar-does-not-render-in-editing-modes/95952)).
   Code spans render as `<code>` in every mode, embed, hover preview, and PDF export.
4. **Jump to Link is installed and hotkeyed** (lead-verified in
   `community-plugins.json`/`hotkeys.json`). A chip that is still an `<a href="copy:…">`
   shows up in the jumper, and activating it without the plugin asks the OS to open an
   unknown protocol. grk's own report had to design around this; code spans make the
   problem not exist.
5. **Degradation is better.** With the plugin off, `` `copy[Zoom]: https://…` `` reads
   as code that says what it is; `[Zoom](copy:https%3A%2F%2F…)` is a dead, encoded link.
6. **Community convention agrees.** Dataview (`` `= …` ``) and Meta Bind
   (`` `BUTTON[…]` ``) both put widget syntax in inline code; users already read
   "prefixed code span = plugin widget".

**Prefix: `copy:`, not gem's `copy>>`.** gem worried `copy:` collides with YAML-ish
documentation snippets (`` `copy: true` ``). cld *measured* it: 3 of ~135k inline spans
in the vault start with `copy:`, all inside the hidden `.bob/ref-sources/` folder, two
of them blank-payload (excluded by grammar rule anyway). Measured near-zero collision
beats a hypothetical; `copy:` is more readable, easier to type, and self-naming. If
real collisions ever appear, a per-note opt-out is the escape hatch (phase 3).

**Fence: `bob-copy`, label in the info string.** Reports split between ` ```copy `
(cld, gem) and ` ```bob-copy ` (cdx, grk). Lead call: **`bob-copy`** — it matches the
existing Bob fence namespace (`bob-plan`, `bob-stats-strip`), cannot clash with another
plugin registering `copy`, and the make-or-edit card types it for you anyway. The label
is the rest of the info string (bare or `[bracketed]`); when Obsidian cannot supply the
info string (`getSectionInfo` "may return null in many circumstances" — callouts,
embeds), the card falls back to a generic `Copy · N lines` label while the payload stays
byte-exact. gem's alternative (`::: Title` as the first body line, which dodges the
`getSectionInfo` null entirely) was rejected because it makes the body no longer purely
payload and needs sentinel escaping; graceful label degradation is the cheaper cost.

## 4. Prior art (merged, conflicts resolved)

| Option | Verdict | Why |
| --- | --- | --- |
| **Copy Text Protocol** (`obsidian://copy?text=…`, ~3k downloads) | Closest existing fit; **best zero-code stopgap, wrong finish** | Right gesture (clipboard/selection → link command), wrong artifact: URL-encoded source you cannot type or pleasantly edit; renders as a hyperlink, not a button; routes through the OS protocol handler; cdx's source inspection found the label is interpolated unescaped (a `]` in the label breaks the link) and the hover preview flattens newlines |
| **Meta Bind** | Reject | Verified by three reports independently: **no first-class copy action** among its 14 action types — copying requires `inlineJS` plus the JS Engine plugin and enabling JavaScript; authoring is a 6+ line YAML fence or a `BUTTON[id]` reference split from its definition; the largest possible dependency for a one-verb feature |
| **Buttons** (`shabegom/buttons`) | Reject | Reports disagreed on its status; reconciled: its source *does* have a native `navigator.clipboard.writeText` copy action (cdx read `src/buttonTypes/copy.ts` at 0.9.13, which doesn't await the promise), **and** the author publicly pinned "Meta Bind is better" and told users to migrate ([buttons#208](https://github.com/shabegom/buttons/issues/208)). Block-shaped, ID-indirected, stagnant — wrong regardless |
| **Copy Inline Code** (~20k downloads) | Reject for v1; the only migration-free stopgap | Decorates *every* inline code span (~135k in this vault = icon noise), no label≠payload, icon is a span without button semantics; its 18-issue tracker (double backticks, `&`→`&amp;`, only-first-span, tab indents, embeds, a Vim-mode crash) is a free checklist of edge cases the new plugin must pass |
| **Clip Link** | Reject | Custom-scheme link parsing via regex on the clicked line; `)` in payload truncates; `clip: text` with a space is not a valid CommonMark destination |
| **`{!text!}`** (copy-text-to-clipboard) | Reject | Invalid Markdown, no label, 1 star — but its Figma click-the-swatch *feel* is the right UX target |
| **`> [!copy]` callout / Booklet** | Reject as syntax | Block-only; raw-vs-rendered ambiguity; `>` prefixes must be stripped; the callout family's LP copy is known-broken (Callout Copy Buttons) |
| **ClipBook** | Not this feature | Great shape for a masked secrets/API-key table; wrong shape for inline prose. Compose later if a secrets page is ever wanted |
| **DataviewJS / Templater buttons** | Reject | JS in notes, load-order bugs (forum #50005's every-button-copies-last-payload), opposite of typing |
| **OS text expanders** (Raycast, Espanso, macOS) | Complementary | Better for type-anywhere personal snippets; do not travel with the note or help Reading view/mobile readers |

## 5. The design

### 5.1 Grammar (v1) and text contract

**Inline chip** — a CommonMark code span (any backtick run length) whose *content*,
after CommonMark's own normalization, matches:

```text
copy [ "[" LABEL "]" ] ":" [ " " ] TEXT
```

- `copy` is lowercase and first; anything else stays ordinary code.
- `LABEL` is optional, non-blank, trimmed, no `]` or newline (`\]`/`\\` escapes
  available). With a label the chip shows the label; without, it shows `TEXT`.
- `TEXT` is everything after the colon and one optional space, **verbatim and
  non-blank** (so `` `copy:` `` never becomes a chip and half-typed spans never steal
  clicks). Interior/trailing spaces are kept. No custom escapes: `\n` copies two
  characters. No interpolation.
- Literal backticks use a longer run (``` ``copy: run `bob plan` first`` ```); the
  serializer, not the human, picks run length and edge padding. Inside tables the
  serializer escapes `\|` and the parser unescapes it.
- Inline chips are single-line by definition — CommonMark normalizes physical newlines
  in code spans to spaces, so the card routes multi-line text to the fence
  ([CommonMark code spans](https://spec.commonmark.org/0.31.2/#code-spans)).

**Block card** — a `bob-copy` fence (backticks or tildes, any length ≥ longest
fence-like run inside the body):

````markdown
```bob-copy Weekly status email
Hi team —
Here is where things stand this week:
```
````

- Body is the payload exactly as Obsidian hands it to the code-block processor: line
  endings normalized to LF, container indentation removed, and **exactly one structural
  final LF stripped** — an extra blank line before the closing fence deliberately
  preserves one trailing newline. Never `trim()`. The card UI reveals line count and
  any trailing newline.

**Round trip.** `parse(serialize(label, text)) ≡ {label, text}` for everything the card
accepts, pinned by a shared JSON conformance-vector file plus a property test over
random strings — the same pattern bob-plugins already uses for walker footers. One
grammar module serves every surface, so Live Preview, Reading view, and the keyboard
path cannot disagree about what a chip copies.

### 5.2 Authoring ("easy by typing", end to end)

1. **Type it.** `` `copy: `` + text. The chip renders when the cursor leaves the span.
   The syntax names itself; after the card shows you the Markdown once, you know it.
2. **Mod+Shift+Y — "Make or edit copy chip"** (lead-verified free: no vault hotkey
   binds the `Y` key at all; the plugin-registered Copy card default is `Mod+Y`):

   | Context | Card opens with | Enter does |
   | --- | --- | --- |
   | One-line selection | Text = selection, focus on Label | Replace selection with inline chip |
   | Multi-line selection | Text = selection | Replace lines with a `bob-copy` fence, indented to the list column |
   | Cursor on a chip/fence | Label + text prefilled | Rewrite in place |
   | No selection | Clipboard text prefilled and pre-selected (typing replaces it) | Insert at cursor |

   Card rules: live preview of the rendered chip **and** the exact Markdown it will
   write (which teaches path 1); inline validation ("labels can't contain ]",
   "nothing to copy"); serializer picks fences/escapes; Enter commits (Shift+Enter =
   newline, second Mod+Shift+Y also commits, like the Copy card's second Mod+Y); one
   undo step touching only the replaced range; closes with Esc, `q`, and `Ctrl+[` per
   `decisions:q-and-ctrl-bracket-mirror-esc`, with `q` typing normally inside fields.
3. **Vim.** `exmap bob_copy_chip obcommand bob-copy-chips:make-or-edit` beside the
   existing `bob_*` exmaps; a visual-mode mapping wraps the selection. Do not overload
   `bob-vim-surround`.

**Rejected authoring ideas** (called out because two reports proposed variants):
a global typing trigger (gem's `;;` composer) and an EditorSuggest autocomplete. The
text of a new chip is *new*, so completion has nothing to suggest; a trigger adds
editor vocabulary, a collision audit, and IME/Vim guards for at most one saved chord.
cdx and cld rejected these independently; the hotkey card keeps the same composer
benefits (gem's clipboard import, auto inline-vs-block, live preview) behind an
explicit, collision-free gesture. If daily use later proves the chord too slow, gem's
`;;` design is the documented fallback.

### 5.3 Look and feedback ("beautiful means quiet")

Steal from Bob's dependency/relation chips, not from button kits. Theme variables only
(`--background-secondary`, `--background-modifier-border`, `--interactive-accent`,
`--radius-s`, `color-mix`), no hardcoded hex, no per-chip color settings.

- **Rest:** hairline pill, faint Lucide `copy` glyph (the same glyph as Obsidian's own
  code-block copy button — never 📋), padding `0 .45em`, font-size `.92em`, inherited
  line height. Labeled chips render in the **text font** (they name a thing, like a
  link); unlabeled chips render in **monospace** (they *are* the literal text). Long
  unlabeled chips wrap like inline code with `box-decoration-break: clone` — wrapping
  never truncates what gets copied.
- **Hover/focus:** border tints toward the accent, cursor `copy`, `:focus-visible`
  outline. Tooltip: "Click to copy", plus (for labeled chips) a payload preview with
  `⏎` for newlines, truncated at ~60–120 chars *in the preview only* — the label must
  never hide what will be copied (requirement A7).
- **Success:** the glyph swaps in place to a green `check` for ~1 s and the chip pulses
  once in `--bob-yank-flash-bg` (lead-verified: the variable exists in
  `bob-vim-yank-flash/styles.css`, green `rgba(80,200,120,.35)`), so a click-copy and a
  Vim yank look alike. **Zero reflow** — the pill's width never changes and no toast
  appears (resolving grk's toast-for-consistency vs. the majority's no-toast: success
  is frequent, in-place feedback suffices; a polite `aria-live` region still announces
  "Copied"). `prefers-reduced-motion` drops the pulse and scale, keeping the glyph swap.
- **Failure:** `alert-triangle` glyph + a Notice with the reason. Never silent — a
  silent failure means pasting stale clipboard contents.
- **Block card:** titled header (glyph, label, line/char count, fixed-min-width Copy
  button that flips to "Copied ✓"), text-font body with `white-space: pre-wrap`,
  fold after ~8 lines behind a "Show all N lines" toggle (session-only state). Clicking
  the body selects text; only the header/button copies.

### 5.4 Interaction and click model

| Surface | Chip click | Edit path | Keyboard |
| --- | --- | --- | --- |
| Live Preview, cursor elsewhere | Copies; widget `ignoreEvent() → true` + `mousedown` `preventDefault`, so the caret never jumps into the source and a drag that starts on a chip selects, never copies | Move the cursor in with any motion (standard LP reveal, like links) or Mod+Shift+Y | "Copy chip on cursor line" command; Copy card `C` row |
| Reading view | Real `<button type="button">`; Enter/Space activate; `aria-label="Copy <label>"` | n/a | Tab-focusable |
| Source mode | No widget; raw Markdown | Edit directly | cursor commands work from the live buffer |
| Mobile | Tap copies; `isDesktopOnly: false` | card | — |

- **Clipboard contract** (identical to the Copy card's existing pattern):
  `navigator.clipboard.writeText(payload)` inside the click gesture, awaited; success
  shown only after fulfillment; failures return `{ok: false, reason}` and show a
  Notice ([MDN writeText](https://developer.mozilla.org/en-US/docs/Web/API/Clipboard/writeText)).
  Parse the payload from **source**, never from rendered `innerText`/`innerHTML` — the
  rendered layer folds whitespace (the same reason the PDF code catalog exists,
  `decisions:code-copy-reads-render-time-catalog`).
- **Copy card `C` row** (phase 2): with the cursor on a chip (or one chip on the line),
  `Mod+Y C` previews label + text and copies. Lead-verified: reserved keys are derived
  from the built-in rows (path/absolute/file/note/block-id) and the close key is `q`;
  `C` is free, and the row rides the versioned `api.copyChips` API so Navigation
  Hotkeys degrades gracefully when the chips plugin is absent.
- **No `obsidian://copy` protocol handler in v1** (resolving grk's interop suggestion
  vs. cdx/cld's rejection): no Copy Text Protocol links exist in this vault (the plugin
  was never installed), and a global clipboard-writing protocol would let any app or
  web page overwrite the clipboard with one crafted link. If CTP compatibility is ever
  wanted, build a one-shot importer that rewrites those links into chip syntax instead.

### 5.5 Reliability contract

Each rule answers a documented real-world failure (mostly Copy Inline Code's tracker
and forum #50005):

| # | Rule | Prevents |
| --- | --- | --- |
| R1 | One grammar module + conformance vectors for every surface | LP and Reading view disagreeing |
| R2 | Read source slices/`textContent`, never `innerHTML` | `&` copied as `&amp;`, HTML in clipboard |
| R3 | Any backtick run length | double-backtick spans failing |
| R4 | Every chip on a line works independently | only-first-span bugs |
| R5 | Indent-agnostic: tabs, lists, blockquotes, callouts, tables | indent/TAB breakage |
| R6 | Works in embeds, hover previews, PDF export via the post-processor | embed failures (also the 2022 forum bug) |
| R7 | Vim-safe: decorations rebuilt from editor state only; no DOM mutation outside widgets; no cross-mode state | a known insert→normal mode crash |
| R8 | Render and click never write the vault; only the card writes, one undo step | surprise edits riding git sync across three hosts |
| R9 | `writeText → {ok, reason}`; failure always Notices | silently pasting stale clipboard |
| R10 | Click is not an edit; drags never copy | clicks revealing source instead of copying |
| R11 | Coexists with Dataview (`=`/`$=` prefixes untouched), Tasks, Bob Ledger Tools marks; keep `::` out of unguarded DOM attributes Dataview rescans | plugin-interference bugs |
| R12 | LP scans only inline-code syntax nodes in `visibleRanges`, inside the bob-plugins CPU budget harness | lag in long daily notes |
| R13 | Labels/text inserted via `textContent` only; no protocol handler; no JS/eval from note content | markup injection from synced notes; external clipboard writes |
| R14 | Empty payload never renders interactive; whitespace-only payloads flagged in preview | clobbering the clipboard with nothing |

### 5.6 Placement, tests, and phases

**New plugin `bob-plugins/plugins/bob-copy-chips/`** (all five reports converged on a
new small plugin; names differed — `bob-copy`, `bob-copy-buttons` — the chip metaphor
won). Committed source-fragment build (`src/fragments.json`, `npm run build`, never
hand-edit `main.js`), `isDesktopOnly: false`, settings-free to start, deployed with
`bob plugins sync`. Not Bob Ledger Tools (ledger-specific, already at v1.140) and not
Navigation Hotkeys (owns keys and cards, not rendering); `bob-vim-yank-flash` is the
precedent for a small clipboard-adjacent plugin. No bob-cli change, no capture-grammar
change, no Mac Capture work (`decisions:mac-capture-is-a-thin-client`); no `%` sigil —
capture `%c` already means clipboard→vault, the opposite direction.

**`api.copyChips` v1:** `parse(source)`, `serialize({label, text, form})`,
`chipAt(editor, pos)`, `copy(text) → Promise<{ok, reason?}>` — consumed by Navigation
Hotkeys for the `C` row.

**Tests:** grammar vectors + round-trip property tests (plain `node --test`, no
Obsidian); an `obsidian-copy-chips-e2e.cjs` in the existing xvfb/CDP harness covering
wrap, LP click, Reading click, fence body with interior blank line, empty-payload
refusal, stubbed `writeText` rejection, embeds, and Vim mode switches; a Live Preview
CPU budget case on a long daily note. Docs page `docs/bob-copy-chips.md` cross-linked
from `docs/copy-card.md` ("authored payloads live on chips; live context lives on the
Copy card"), passing `npm run docs:check`.

| Phase | Scope |
| --- | --- |
| 1 · MVP | Grammar module + vectors; LP widget; Reading post-processor; `bob-copy` fence card; clipboard + feedback; CSS; docs; e2e; CPU budget |
| 2 · Authoring & keyboard | Mod+Shift+Y make-or-edit card; Copy card `C` row via `api.copyChips`; "Copy chip on cursor line" command + vimrc exmap; Alt+Click / hover-`✎` edit affordance |
| 3 · After a month of real use | Vault-wide "Copy a snippet…" fuzzy picker (turns chips into a snippet library); optional `bob` CLI listing / Mac Capture snippet mode (a cross-repo contract); rich-text (`text/html`) copy for cards; per-note opt-out; masked-preview `copy*` variant for semi-sensitive values |

Ship phases 1 and 2 together; decide on phase 3 from observed use.

## 6. How the five reports' disagreements were resolved

| Question | Positions | Resolution |
| --- | --- | --- |
| Storage syntax | code span (cdx, cld, gem) vs. `copy:` link (grk, mus) | **Code span** — encoding-free typing, parser inertness, mode-consistent rendering, Jump to Link conflict avoided (§3) |
| Inline prefix | `copy:` (cdx, cld) vs. `copy>>` (gem) | **`copy:`** — measured 3-in-135k benign collision rate beats the hypothetical |
| Label-is-payload shorthand | mus's `[text](copy)` | Subsumed: an unlabeled `` `copy: text` `` chip already shows its payload with zero duplication |
| Creation UX | `;;` composer (gem) vs. hotkey card (cld) vs. plain wrap command (grk, mus, cdx) | **Mod+Shift+Y make-or-edit card** with gem's composer niceties folded in; no global typing trigger, no autocomplete |
| Fence name & label | `copy` + info string (cld), `copy` + `:::` body title (gem), `bob-copy` + info string (cdx, grk) | **`bob-copy` + info string**, generic-label fallback where `getSectionInfo` is null; body stays pure payload |
| Success feedback | no-toast in-place (cdx, cld, gem, mus) vs. Copy-card Notice (grk) | **No toast**; in-place check + yank-flash pulse + `aria-live` announcement; failures always Notice |
| Buttons plugin status | "deprecated" (mus, grk) vs. "has a native copy action; deprecation unproven" (cdx) | Both partly right: native copy action exists in source (unawaited promise); author pinned "use Meta Bind". Rejected on shape either way |
| `obsidian://copy` interop | honour as reader (grk) vs. never register (cdx, cld) | **Not in v1**; importer instead, if ever needed |
| Trailing-newline rule | strip one structural LF, extra blank line opts back in (cdx) vs. "no trailing newline" (cld, grk) | **cdx's rule** — it is the only one that lets an author deliberately keep a trailing newline, and the card surfaces it |

## 7. Lead verification performed

- **Vault config** (read-only): no entry in `~/bob/.obsidian/hotkeys.json` binds the
  `Y` key at all → `Mod+Shift+Y` is free; `community-plugins.json` confirms the curated
  list (Dataview, Tasks, Templater, Metadata Menu, **Jump to Link**, Linter, vimrc
  support, relative line numbers, ten `bob-*` plugins) and that Meta Bind, Buttons,
  Copy Text Protocol, and Copy Inline Code are **not** installed.
- **bob-plugins checkout** (via `sase repo open`): `--bob-yank-flash-bg` exists with the
  green fallback cld's CSS assumes; the Copy card registers `Mod+Y` as its default
  hotkey, derives reserved keys from its built-in rows, and closes on `q` — `C` is
  available for the chip row.
- **Web:** custom-scheme link rendering is mode-inconsistent in current Obsidian
  ([forum #95952](https://forum.obsidian.md/t/link-with-custom-uri-scheme-e-g-foo-bar-does-not-render-in-editing-modes/95952),
  corroborating Clip Link's source comment and settling the syntax disagreement), and
  threads confirm custom schemes also depend on OS handlers and URL-encoding
  ([forum #83505](https://forum.obsidian.md/t/custom-schemas-may-not-work/83505),
  [forum #11226](https://forum.obsidian.md/t/obsidian-urls-arent-clickable-links-in-view-mode/11226)).

## 8. Open questions for Bryan (none block the design)

1. **Mobile:** do you read this vault on a phone/tablet? Taps work either way; mobile
   has no hover, so a labeled chip's payload is visible only via the card/source there.
2. **Hotkey:** `Mod+Shift+Y` is free and sits beside `Mod+Y` — confirm you like the
   chord before it ships bound (otherwise ship unbound with a docs recommendation).
3. **Semi-sensitive values** (account numbers): is a label-as-mask
   (`` `copy[Acct ••••4821]: …` ``) enough, or is the phase-3 masked-preview variant
   worth pulling forward? (Either way the text is plain in git — not a secret store.)
4. **Decision record:** if you accept this design, consider recording "copy chips are
   code spans; payloads are literal" through the memory-write flow so a later agent
   doesn't reopen the rejected link/button syntaxes.

## 9. If you want relief this week (before anything is built)

- **Zero new syntax:** install Copy Inline Code with hover-only icons — nothing to
  migrate, uninstall the day chips ship.
- **Closest to the requested UX:** install Copy Text Protocol and its
  paste-clipboard-as-link command — but every link it writes is encoded `obsidian://`
  syntax you would migrate later, with the label-escaping and preview caveats above.
- Neither is recommended as the end state; both are fine as a two-week trial that also
  reveals which payloads recur (seed data for the phase-3 picker).

## Report index

| Suffix | File | Distinct contribution |
| --- | --- | --- |
| cdx | `obsidian_copy_chips__cdx.md` | Source-pinned inspection of all four prior-art plugins; CommonMark parsing experiments; the text/newline contract; accessibility semantics |
| cld | `obsidian_copy_chips__cld.md` | Vault-scale measurements (135k spans, collision audit); issue-tracker-derived reliability rules; make-or-edit card; Copy card `C` row; `api.copyChips` |
| grk | `obsidian_copy_chips__grk.md` | Bob-internal evidence ledger (Copy card, dep/relation chips, yank-flash, Jump to Link, capture `%c`); the copy-family placement; link-syntax design (rejected but mined) |
| mus | `obsidian_copy_chips__mus.md` | Sharpest scope critique (non-goals, secrets, snippet-library reframing threshold); acceptance criteria; label-is-payload idea |
| gem | `obsidian_copy_chips__gem.md` | Composer UX detail (clipboard Tab-import, auto inline/block); zero-reflow feedback rule; `getSectionInfo` pitfall; CM6/Dataview implementation hazards |
