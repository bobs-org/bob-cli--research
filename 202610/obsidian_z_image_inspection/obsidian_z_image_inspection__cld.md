# A `Z` keymap to zoom images in Obsidian: research, critique, and recommendation

*Researcher: cld · 2026-10-20 · evidence pinned to bob-plugins @ `ff36987`, vault @
`7c3f51e1` (apollo git copy), bob-cli @ `8ced873d`, Obsidian **1.14.4** as installed on
the MacBook (read-only check of `Info.plist` and `obsidian-1.14.4.asar`, sha256 prefix
`146ef8470d8cbb4a`), `replit/codemirror-vim` @ `8640966`, `obsidian-api` @ `9abd960`.*

---

## TL;DR

- **The need is real.** New screenshots go into notes as `![[img/…png|400]]`, but the
  files are 1.4k–2.9k px wide Retina captures. For example, `img/20261020_074502.png` is
  2854×1686 and is shown at about 14% scale, so its text can't be read. The vault also
  has **239 plain image links** (`[[img/foo.png]]`, not embeds) across 117
  hand-written notes. Those render as text only.
- **Don't build a lightbox. Obsidian already ships one.** Desktop 1.13 (public July 30,
  2026; your Mac runs 1.14.4) added a native fullscreen image viewer. It has zoom, drag
  to pan, a filename title bar, and ←/→ to step through every image embedded in the
  note.
- **What's missing is a keyboard way in for Vim users.** No command opens the lightbox.
  The documented "select an image, press Space" path is **shadowed in Vim normal mode**.
  Obsidian installs Vim at the highest key precedence, and Vim treats `<Space>` as `l`
  before the image keymap sees it. (This comes from reading the 1.14.4 bundle and
  matches a Sep 2026 forum thread. It is not runtime-tested.) Plain `[[img.png]]` links
  never get a lightbox at all. Clicking one opens Obsidian's plain image tab, which has
  no zoom.
- **`Z` is a good key.** Uppercase `Z` (and `ZZ`/`ZQ`) is unbound in Obsidian 1.14.4's
  bundled Vim, in Obsidian's own Vim mappings, in your vault vimrc, and in every
  bob-plugin.
- **Recommendation:** add a small new plugin, `bob-image-zoom`. `Z` in Vim normal mode
  works out which image on the cursor line you mean.
  1. If it is an **embed in Live Preview**, `Z` opens the **native lightbox** through
     Obsidian's internal Live Preview image controller (`cm.livePreview.showImage`).
  2. Otherwise (a plain image link, Source mode, or Obsidian internals changed), `Z`
     opens a small fallback viewer owned by the plugin.

  Inside either viewer, `q` / `Z` / `Esc` / `Ctrl+[` close and `h` / `l` move between
  images. The plugin never writes to the vault.

---

## 1. What exists today (facts)

### 1.1 Your vault's images

| Fact | Value |
|---|---|
| Image files | 196 (190 under `img/`, mostly PNG; the rest in `ref/**.assets/` from Highlights/capture) |
| Wikilink image **embeds** `![[…png]]` | 16, of which 14 carry an explicit width (`|400` for capture screenshots; `|434`, `|549` in ref notes) |
| Plain image **links** `[[…png]]` (not embedded) | **239 in 117 hand-written notes** (329 including `_generated/` pages). These are mostly zorg-era references like `See [[img/vim_veteran_redir.png]]` |
| Markdown image embeds `![](…)` | Effectively none. One uses an absolute macOS path (`text/habit_slide_show.md`), which is out of scope |
| Typical source sizes | 2854×1686, 2422×798, 2370×940, 1642×830, 1486×762. Small ones exist too (243×244) |
| Where embeds live | List children (`- ![[img/…|400]]`), `>` blockquotes in ref notes, and one callout (`> [!quote] Image ![[…]]`) |

The trend is clear. **Newer content uses small-width embeds**: capture screenshots, and
ref-note figures from Highlights. Older content uses plain links. A zoom gesture
therefore has to handle both, or the user will keep hitting cases where it does nothing.

### 1.2 What Obsidian 1.13 and 1.14 give you natively

From the changelog:

- **1.13.2 (catalyst):** "New image lightbox for viewing images fullscreen. Click the
  image in reading mode to open it. Or in live preview, with an image selected, click
  or press `Space` to open it in the lightbox. Use arrow keys to navigate between all
  the images embedded in the current file."
- **1.13.2:** "Vim: Added a new `:image` Ex command…"
- **1.13.3:** "Added a 'zoom' button to image embeds." and "The image lightbox now
  supports click and drag to pan within an image."
- **1.13.4:** "The image lightbox now displays the file name of the current image."
- **1.13 public (1.13.4):** "Images are now easier to resize and can be viewed
  fullscreen. Click an image or the **Zoom** button to open it…"
- **1.13.6 and 1.13.7:** bug fixes (a `#` URL suffix, pop-out windows).
- **1.14:** no further lightbox changes.

What I found by reading the **1.14.4 bundle** (`app.js`, `lib/codemirror/vim.js`). These
are code-level findings, not runtime tests:

- **Lightbox controls:**
  - `Esc` closes.
  - `Space` (press and release) closes.
  - `=` zooms in and `-` zooms out, in ×1.2 steps from 1× to 10×.
  - `←` / `→` navigate.
  - The wheel zooms, double-click toggles 2.5×, and dragging pans.
  - There is **no** `+`, `0`, `q`, `h`/`l`, or keyboard panning.
- **Live Preview image controller.** This is an internal class, reached through the
  Vim adapter's `livePreview` getter (`window.CodeMirrorAdapter.prototype`). It
  exposes:
  - `imageWidgetAt(pos, predicate)`
  - `selectImage(widget)` and `setSelectedImage({start,end})`
  - `enterOrExitImage(forward)`
  - `showSelectedImage()` and **`showImage(widget)`**

  `showImage` collects every image-embed decoration in the document (computed from the
  syntax tree, which Obsidian parses at least to the viewport end plus 2000 chars). It
  then opens the lightbox at the requested image, blurs the editor, and refocuses the
  editor on close.
- **Reading view:** clicking any rendered `<img>` opens the lightbox over all images in
  the preview.
- **Plain image links:** `[[img/x.png]]` opens the core *image file view*. That view
  renders a plain `<img>` in `.image-container`, with **no zoom or pan**.
- **Commands:** none of the ~200 built-in command IDs opens the lightbox. The
  image-adjacent ones are `canvas:export-as-image`, `editor:attach-file`,
  `editor:download-attachments`, and window/webviewer zoom.
- **Public API:** `obsidian.d.ts` (through 1.14.4) has **no** lightbox or image-viewer
  API.

### 1.3 Vim specifics (why "just press Space" doesn't work for you)

- Obsidian registers its Vim plugin with **`Prec.highest`** (`Te.highest(GU)` in the
  bundle). In normal mode, Vim's key handler checks images only for `h`, `l`, `←` and
  `→`. Those keys *enter or exit* an image selection (`tryHandleKey` →
  `enterOrExitImage`). Every other key goes to Vim first. `<Space>` maps to `l`, so it
  moves the cursor and the selection clears before the image keymap (Space → lightbox,
  Enter → edit, and so on) can run.
- Obsidian's own Vim image mappings are only **`g+`, `g-`, `g=`, `g<CR>`**, plus
  `:image grow|shrink|reset|edit`. None of them opens the lightbox.
- A forum thread on 1.13.7 (Aug 31 – Sep 6, 2026) confirms the pattern. Enter doesn't
  edit a selected image in Vim normal mode ("The cursor simply jumps behind the image").
  An Obsidian-side poster explains: "We picked `g<Enter>`, because `<enter>` does
  something else already in Normal mode."
- **Correction to earlier research.** The Oct 18 "Obsidian 1.12 → 1.14" consolidated
  report told you to "select the image… then press Space for the lightbox". Based on
  the code above, that probably does **not** work in Vim normal mode. Your
  task-status-cycler also maps `<CR>` in normal mode, so Enter is taken twice over.

### 1.4 Is `Z` free?

- Upstream CodeMirror Vim and Obsidian's bundled `vim.js` define only `zz`, `zt`, `zb`,
  `z.`, `z<CR>` and `z-`. They have **no `Z`, `ZZ` or `ZQ`**.
- Obsidian's `app.js` adds only `g+`, `g-`, `g=`, `g<CR>`.
- `obsidian_vimrc.md` maps `-`, `[[`, `]]`, `!`, `[<Space>`, `]<Space>`, `<C-j>`,
  `<C-k>`, `\<`, `\>`, `\\`, `]s`, `[s`, `[S` and `]S`. No `Z`.
- bob-plugins map `<CR>`, `<BS>`, `o`, `O`, `#`, `<C-]>`, `<C-}>`, `<C-d>`, `<C-u>`,
  `<C-o>`, `<C-i>`, `\s`, `\p`, `\P`, `\o`, `\O`, and the surround operators. No `Z`.

So a bare `Z` fires immediately. No pending-prefix timeout applies, because nothing
starts with `Z`.

---

## 2. Critique: is this a good idea?

**Yes, with a re-scope.** As stated ("a `Z` keymap that triggers zoom"), the plan is
sound. The risk is building the wrong thing: a homemade lightbox that duplicates what
Obsidian shipped three months ago, and that then drifts from it.

What's right about it:

- **It matches how you work.** You drive Obsidian from Vim and counted keys (`]s`, `!`,
  `<CR>`, `N<Ctrl+Shift+B>`). Reaching for the mouse to click a 400 px thumbnail breaks
  that. Section 1.3 shows the keyboard path really is missing, so this isn't
  gold-plating.
- **Small thumbnails plus zoom on demand is the right pairing.** Keeping `|400` keeps
  notes scannable. The alternative, larger embeds, would bloat every daily and ref
  note. Zoom on demand lets you keep the thumbnails.
- **It's read-only and low risk.** It touches no task semantics, review walk,
  dependency, or ledger behavior, so none of the `decisions` records apply.

What I'd change or push back on:

1. **Reuse the native viewer for embeds.** You get gallery navigation across the
   note's images, the open/close animation from the thumbnail, a filename title,
   momentum pan, pinch, and future Obsidian improvements, all for free.
2. **The real gap includes plain image links.** 239 `[[img/…png]]` links have *no*
   good large view today: the image tab can't zoom. If `Z` handles only embeds it will
   do nothing on most of the vault's image references. The fallback viewer covers them.
3. **Don't solve it by converting links to embeds.** The `!` transclusion toggle
   already exists per line. A mass migration would inline 239 screenshots into prose
   bullets, and zooming should never need a write.
4. **Keys inside the viewer matter as much as the key that opens it.** The native
   lightbox has no `q`, no `Ctrl+[` and no `h`/`l`. Your Task Card closes with
   `Esc`/`q`/`Ctrl+[`. A thin key-translation layer gives both viewers the same Vim
   vocabulary.
5. **Avoid community lightbox plugins.** The options include:
   - Image Toolkit: last updated 2025-08-30, 63 open issues.
   - Image Zoom, Click Image to Zoom, Fullscreen Image, Lightbox: tens to a few hundred
     downloads each.

   They are all **click-triggered** and none offers "open the image at the cursor". They
   would also compete with the native lightbox for the same clicks.

---

## 3. Requirement adjustments (called out explicitly)

These are my changes to the original ask. Each can be accepted or dropped on its own.

| # | Adjustment | Why |
|---|---|---|
| **A1** | **Re-scope from "build zoom" to "keyboard bridge to Obsidian's native lightbox, plus a fallback viewer"** | The native viewer exists on your Mac (1.14.4). Reusing it means less code and better UX |
| **A2** | **`Z` works in Vim normal mode in Markdown editors (Live Preview and Source).** Visual and insert mode are untouched. A palette command "Zoom image on cursor line" ships too, with no default hotkey. Reading view stays click-only | Reading view has no Vim and no cursor, and native click already works there. The palette command makes the feature discoverable and bindable outside Vim |
| **A3** | **Targeting is line-scoped and predictable.** Order: (1) with a count, `NZ` picks the Nth image reference on the line; (2) the reference that contains the cursor; (3) the first reference after the cursor; (4) the last reference on the line; (5) otherwise show "No image on this line" | Counts match your other gestures. Never search beyond the line: a guess that jumps to an image three bullets away is worse than a notice |
| **A4** | **"Image reference" covers** `![[x.png|400]]`, `[[x.png]]`, `[[x.png|alias]]`, `![alt](path-or-url)`, and `[text](x.png)`. Image extensions are `png jpg jpeg gif bmp svg webp avif`, after stripping `#subpath` and `|alias/size` | This covers both of your syntaxes. Remote `https://` images work too |
| **A5** | **Close and toggle semantics: `Z`, `q`, `Esc` and `Ctrl+[` all close.** `h` / `l` move to the previous / next image in the native lightbox. `+` is an alias for `=` | Same vocabulary as the Task Card. Your Neovim reflex `ZZ` becomes a harmless open-and-close |
| **A6** | **Strictly read-only.** No cursor move, no jump-list entry, no selection change, no edits to `|400` sizes, no link-to-embed conversion | Viewing must never dirty a note. This also keeps clear of the Highlights-region rewrite rule |
| **A7** | **Degrade gracefully.** If the internal Live Preview controller is missing or changes shape, `Z` still works through the fallback viewer | The native path depends on undocumented internals. A broken Obsidian update should cost polish, not the feature |
| **A8** | **Ship as a new small plugin, `bob-image-zoom`,** rather than inside `bob-navigation-hotkeys` | Single responsibility; you can disable it alone if Obsidian internals move; it doesn't grow nav's task-centric surface |
| **A9** | **Out of scope for v1:** Mermaid, Canvas and PDF zoom; images inside transcluded notes; Reading-view keyboard zoom; mobile | These are different problems. Mobile already has native tap-to-lightbox and swipe-to-dismiss |

---

## 4. Options considered

| Option | Keyboard (Vim) | Embeds | Plain `[[img]]` links | Uses internals | Code | Verdict |
|---|---|---|---|---|---|---|
| **0. Do nothing:** click the thumbnail or the native Zoom button | ✗ | ✓ native | ✗ (image tab, no zoom) | no | 0 | Baseline. Mouse-only, and misses links |
| **1. vimrc-only** (`nmap Z :something<CR>`) | — | — | — | — | — | **Impossible.** No command opens the lightbox, and `obcommand` can't reach it |
| **2. Community lightbox plugin** | ✗ click-only | ✓ (duplicate) | ✗ | n/a | 0 | Reject. Duplicates native, fights over clicks, some unmaintained |
| **3. Custom viewer only** (plugin modal for everything) | ✓ | ✓ (own UX) | ✓ | **no** | ~300 LOC | Viable and robust, but rebuilds gallery, animation, pinch and momentum, and drifts from native |
| **4. External viewer** (`app.openWithDefaultApp` → Preview.app, or `qlmanage -p`) | ✓ | ✓ | ✓ | `openWithDefaultApp` is internal | ~40 LOC | Great zoom, but leaves Obsidian and needs window juggling. macOS-flavored. Good as an *optional* `gx`, not as the main path |
| **5. Hybrid:** native lightbox for Live Preview embeds, own viewer for the rest | ✓ | ✓ native | ✓ | yes, feature-detected, falls back to 3 | ~300 LOC | **Recommended** |
| 6. Synthesize clicks on the embed's `<img>` (click twice: select, then open) | ✓ | ✓ native | ✗ | DOM only | small | Reject. The first click *moves the cursor* (`selectImage` dispatches a selection), and it only works for rendered lines |
| 7. Get the native lightbox class for arbitrary URLs | — | — | — | deep | — | **Not reachable.** The class is module-private and `showImage` only accepts widgets already in the document |

---

## 5. Recommended design

### 5.1 Placement and packaging

- Add `plugins/bob-image-zoom/` with `manifest.json`, a hand-edited `main.js`, and
  `styles.css`, the same shape as `bob-vim-surround`. The plugin is small enough not to
  need `src/fragments.json`.
- Manifest: `id: bob-image-zoom`, `isDesktopOnly: false` (it does nothing on mobile),
  `minAppVersion: 1.8.7`. Everything native is feature-detected, so there's no need to
  pin 1.13.
- Docs: add `docs/bob-image-zoom.md`, an entry in `docs/nav.yml`, and regenerate the
  inventory (`npm run docs:gen`). Run `npm run docs:check` and `npm test`.
- Deploy with `bob plugins sync`, then **enable the plugin once** in Obsidian (Settings
  → Community plugins). Sync copies plugin files but doesn't enable new IDs.

### 5.2 Entry points

```js
// Vim: same style as task-status-cycler / ledger-tools
vim.defineAction("bobImageZoom", (cm, actionArgs) =>
  this.zoomAtCursor(cm.cm6, explicitCount(actionArgs)));
vim.mapCommand("Z", "action", "bobImageZoom", {}, { context: "normal" });

// Palette (no default hotkey)
this.addCommand({
  id: "zoom-image-on-cursor-line",
  name: "Zoom image on cursor line",
  editorCallback: (editor) => this.zoomAtCursor(editor.cm, 0),
});
```

Use the repo's existing `getVimRepeat` / `repeatIsExplicit` convention for the count.
Register the mapping in `onLayoutReady`, with the same "register once,
`window.CodeMirrorAdapter.Vim` may be late" guard the other plugins use.

### 5.3 Resolving the target

1. `line = doc.lineAt(selection.main.head)` and `ch = head - line.from`.
2. `refs = findImageRefs(line.text)`. This is a pure function returning
   `{from, to, embed, kind: "wiki"|"md", target}`. Reuse or mirror nav's
   `parseTransclusionWikiLinkAt` / `parseTransclusionMarkdownLinkAt` bracket and paren
   rules (angle-bracket destinations, nested parens, `%20`).
3. `ref = pickImageRef(refs, ch, count)` using the A3 order. If nothing matches, show a
   `Notice`: "No image on this line".
4. Resolve the source:
   - Wiki links, and markdown links without a URL scheme, go through
     `metadataCache.getFirstLinkpathDest(decode(path), sourcePath)` and then
     `vault.getResourcePath(file)`.
   - `http(s)` URLs are used as-is.
   - If resolution fails, show `Notice("Image not found: <target>")`.

### 5.4 Opening: native first, then fallback

```js
openNative(view, pos) {
  const getter = Object.getOwnPropertyDescriptor(
    window.CodeMirrorAdapter?.prototype ?? {}, "livePreview")?.get;
  const lp = getter?.call({ cm6: view });       // works even with Vim off
  if (!lp || typeof lp.imageWidgetAt !== "function" ||
      typeof lp.showImage !== "function") return false;
  const widget = lp.imageWidgetAt(pos, (w) => w.start === pos);
  if (!widget) return false;                    // Source mode, unparsed line, etc.
  const doc = view.dom.ownerDocument;
  const before = doc.querySelectorAll("body > .lightbox").length;
  lp.showImage(widget);
  return doc.querySelectorAll("body > .lightbox").length > before; // verify it opened
}
```

- Try `openNative` only when `ref.embed` is true. Otherwise, or when it returns false,
  open the fallback `ImageZoomModal`.
- On the Vim path `cm.livePreview` gives the same object directly. The getter trick
  lets the palette command work with Vim turned off.
- If the internals are missing, `console.warn` once per session, so a broken Obsidian
  update shows up in the console instead of failing silently.
- Don't call `selectImage`. It moves the cursor and breaks A6. `showImage(widget)`
  alone opens the viewer and leaves the selection untouched.

### 5.5 Vim keys inside the native lightbox (≈30 lines)

The lightbox focuses its own container, which has `class="lightbox"`. Its handler reads
only `event.key`. So:

1. Add a capture-phase `keydown` listener on each window's document: the main document
   through `registerDomEvent`, pop-out windows through `workspace.on("window-open")`.
2. When `event.target.closest(".lightbox")` matches, translate the key:

   | Key | Becomes |
   |---|---|
   | `q`, `Z`, `Ctrl+[` | `Escape` |
   | `h` | `ArrowLeft` |
   | `l` | `ArrowRight` |
   | `+` | `=` |

3. Swallow the original event and dispatch a synthetic
   `KeyboardEvent("keydown", {key, bubbles: true})` on the `.lightbox` element.

This depends only on the `lightbox` class name, which themes already target. If the
lightbox ever adds its own `q` or `h`/`l` handling, remove the matching rows.

### 5.6 Fallback viewer (`ImageZoomModal`, ≈150–200 lines plus CSS)

- An Obsidian `Modal` with a full-viewport dark backdrop, the filename as its title,
  and a single `<img>`.
- **Initial scale:** fit to the window, but don't upscale tiny images beyond 2×.
- **Keys:**

  | Key | Action |
  |---|---|
  | `Esc`, `q`, `Z`, `Ctrl+[` | Close |
  | `=` or `+` | Zoom in |
  | `-` | Zoom out |
  | `0` | Fit |
  | `1` | **Device-pixel 1:1**: scale `1/devicePixelRatio` of natural size, which is exactly how a Retina screenshot looked when captured |
  | `h`/`j`/`k`/`l` | Pan, when zoomed |

- **Mouse and trackpad:** wheel zoom at the pointer (macOS pinch arrives as
  `wheel` + `ctrlKey`), drag to pan, double-click toggles fit ↔ 1:1, and clicking the
  backdrop closes.
- v1 shows a single image, so `h`/`l` don't navigate here. A gallery over every image
  reference in the note could come later.

### 5.7 Tests and verification

Add `scripts/test-image-zoom.cjs` to the `npm test` list.

**Unit tests (`node --test`):**

- `findImageRefs`:
  - sized embeds, aliases, `#subpath`, `%20` and angle-bracket destinations
  - `[[note]]` and `![[note]]` are ignored (not images)
  - `.pdf` is ignored
  - two refs on one line
  - inline code spans: decide whether to ignore them. I'd ignore refs inside backticks
- `pickImageRef`: the A3 order and count edge cases, including N greater than the
  number of refs.
- Resolution against a fake `metadataCache` and `vault`.
- The key-translation table.
- Vim registration through the existing `scripts/cm6-mapping-editor.cjs` harness, the
  same way `test-ledger-tools-vim-mappings.cjs` does it.

**Mac smoke checklist (Obsidian 1.14.4):**

1. A `- ![[img/…|400]]` child bullet. `Z` should open the native lightbox, with `h`/`l`
   stepping through the note's other screenshots (for example in `sase_blog.md`).
2. Close with `q`, then `Z`, then `Ctrl+[`. The cursor, mode (normal) and scroll should
   be unchanged, and the jump list should have no new entry.
3. A ref note `> ![[….assets/…png|549]]` blockquote, and the `> [!quote] Image ![[…]]`
   callout.
4. A plain link `See [[img/vim_veteran_redir.png]]`. Should open the fallback viewer.
   Check that `1` shows crisp 1:1.
5. Two images on one line: cursor on the second gives the second; `2Z` gives the
   second.
6. A line with no image shows the notice and makes no edits. `git diff` on the vault
   should be empty.
7. Source mode on an embed should open the fallback viewer.
8. A pop-out window.
9. The palette command, both with Vim off and with Vim on.

### 5.8 Risks and mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| Obsidian renames or reshapes `livePreview`, `imageWidgetAt` or `showImage` (all undocumented, introduced in 1.13) | Medium over a year | Feature detection, a check that the lightbox actually opened, automatic fallback to the plugin's viewer, and a one-time console warning. Recheck after each Obsidian upgrade (one smoke step) |
| Obsidian later binds `Z…` in Vim | Low | Section 1.4 shows nothing today. `g<Space>` is the fallback key: it matches Obsidian's `g+`/`g-`/`g=`/`g<CR>` image family and native Space-to-open |
| Native gallery misses far-off embeds in very long notes (decorations follow the parsed syntax tree) | Low, cosmetic | Accept. `Z` on that line still opens the right image |
| The key layer double-handles a key the lightbox later supports natively | Low | Map only keys the lightbox ignores today. Revisit on upgrade |
| Plugin enable step forgotten after sync | One-time | Note it in the docs page and the hand-off |

**Effort:** one focused agent session. Roughly 250–350 LOC of JS, 50–70 lines of CSS,
about 150 lines of tests, and a docs page. No bob-cli changes, and no
bob-mac-capture changes (image zoom isn't part of the capture contract).

### 5.9 Optional follow-ons (not in v1)

- **`gx` → open in the default app** (Preview.app), through `app.openWithDefaultApp`
  (internal; feature-detect it). This matches Vim's "open externally" meaning, for when
  you want Preview's annotation or crop tools.
- **A gallery in the fallback viewer** over every image reference in the note, links
  and embeds, so `h`/`l` work there too.
- **Reading view `Z`** through a capture-phase key listener scoped to
  `.markdown-reading-view`. Only worth it if you find yourself reading screenshot-heavy
  notes in Reading view.

---

## 6. What I could not verify

- **Runtime behavior.** Everything about the 1.14.4 internals (`livePreview`,
  `showImage`, Vim precedence, lightbox keys) comes from reading the shipped bundle.
  Obsidian isn't installed on apollo, and I did not drive the Mac's UI. The
  "Space is shadowed in Vim normal mode" claim is strongly supported by the code and
  the forum thread, but it is not tested. Confirm it in 10 seconds: `l` onto an image,
  then press Space.
- **Whether `imageWidgetAt(pos, w => w.start === pos)` matches embeds inside callouts
  when the cursor is on the callout's source line.** If it doesn't, the fallback viewer
  takes over, so the feature still works.
- **Whether athena also runs Obsidian desktop.** All bob-plugins are cross-platform
  JS, so it doesn't change the design.

---

## 7. Recommended solution

1. **Build `bob-image-zoom`,** a new, small, read-only bob-plugin, deployed with
   `bob plugins sync` and enabled once.
2. **`Z`** (Vim normal mode, count-aware) **and the palette command "Zoom image on
   cursor line"** pick the image reference on the cursor line:
   - with a count, the Nth one;
   - otherwise the one under the cursor, then the first after it, then the last on the
     line;
   - otherwise a notice.
3. **Embeds in Live Preview open Obsidian's native lightbox** through the
   feature-detected internal `livePreview.showImage(widget)`. You get the gallery,
   pan, zoom, title and animation for free.
4. **Everything else** (plain `[[img/x.png]]` links, markdown image links, Source
   mode, and any internals breakage) opens a **small built-in fallback viewer**: fit,
   `=`/`-`/`0`, `1` for device-pixel 1:1, `hjkl` pan, and wheel/pinch zoom.
5. **One shared key set in both viewers:** `q` / `Z` / `Esc` / `Ctrl+[` close,
   `h` / `l` move between images, `+` is an alias for `=`.
6. **Don't** install a community lightbox plugin, don't convert links to embeds, and
   don't enlarge the `|400` thumbnails. Zoom on demand is the complement to small
   thumbnails, not a replacement for them.

---

## Sources

- Obsidian changelog:
  - [1.13.2 Desktop (catalyst, 2026-07-14)](https://obsidian.md/changelog/2026-07-14-desktop-v1.13.2/): lightbox, Space, arrow navigation, `:image`
  - [1.13.3 Desktop (2026-07-21)](https://obsidian.md/changelog/2026-07-21-desktop-v1.13.3/): Zoom button, drag-to-pan
  - [1.13 Desktop public (1.13.4, 2026-07-30)](https://obsidian.md/changelog/2026-07-30-desktop-v1.13.4/)
  - [1.13.4 Mobile public](https://obsidian.md/changelog/2026-07-30-mobile-v1.13.4/)
  - [1.13.6 Desktop public](https://obsidian.md/changelog/2026-08-10-desktop-v1.13.6/)
  - [1.13.7 Desktop public](https://obsidian.md/changelog/2026-08-12-desktop-v1.13.7/)
  - [1.14 Desktop public (1.14.4)](https://obsidian.md/changelog/2026-10-05-desktop-v1.14.4/)
- Obsidian forum: ["Unable to use Vim-mode to edit the markdown of previewed images"](https://forum.obsidian.md/t/unable-to-use-vim-mode-to-edit-the-markdown-of-previewed-images/117839) (Aug 31 – Sep 6, 2026)
- Community plugins surveyed:
  - [Lightbox](https://community.obsidian.md/plugins/lightbox)
  - [Fullscreen Image](https://community.obsidian.md/plugins/fullscreen-image)
  - [Image Zoom](https://community.obsidian.md/plugins/image-zoom)
  - [Click Image to Zoom](https://community.obsidian.md/plugins/sfb-click-image-to-zoom)
  - [Mousewheel Image Zoom](https://community.obsidian.md/plugins/mousewheel-image-zoom)
  - [Image Tab Zoom](https://community.obsidian.md/plugins/image-tab-zoom)
  - [Image Toolkit (obsidianstats)](https://obsidianstats.com/plugins/obsidian-image-toolkit)
  - [ImageFull](https://community.obsidian.md/plugins/imagefull)
- Local evidence:
  - Obsidian 1.14.4 bundle from the Mac (`app.js`, `lib/codemirror/vim.js`, `app.css`)
  - `replit/codemirror-vim` @ `8640966` (`packages/codemirror-vim-core/vim.js` default keymap)
  - `obsidianmd/obsidian-api` @ `9abd960` (no lightbox API)
  - bob-plugins @ `ff36987` (Vim mapping inventory, `parseTransclusion*At` helpers, test harnesses)
  - vault `obsidian_vimrc.md`, `.obsidian/*.json`, image and link counts
- Prior (non-swarm) research: `research:202610/obsidian_1_14_upgrade_for_bob_setup/obsidian_1_14_upgrade_for_bob_setup__final.md` (its Space-for-lightbox tip is corrected in §1.3)
