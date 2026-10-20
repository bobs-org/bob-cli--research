# `Z` to zoom an image in Obsidian: keep the key, own a small viewer, leave native clicks alone

> **Research query:** What is the best way to zoom in on images and inline image links
> in Obsidian, to see a nice large version when desirable, possibly triggered by a new
> `Z` keymap? Is this plan a good idea, or would a different approach be better? Call
> out any justified requirement adjustments and end with a recommended solution.

![Infographic: Z to inspect images in Obsidian. Keep the native mouse lightbox; close the gaps for 239 plain image links and for Vim, which consumes Space; press Z on the image line to open an owned, read-only viewer and return to the same place; check the native viewer first.](obsidian_z_image_inspection_infographic.png)

## Bottom line

**[The idea is good](#critique-of-the-plan), and `Z` is a fine key. Make it a read-only
"inspect the image on this line" command that opens a small viewer bob owns.**

1. **[Obsidian already has a fullscreen image lightbox](#what-obsidian-gives-you-natively)**
   (1.13, public 2026-07-30; your Mac runs 1.14.4). You can open it with the mouse:
   click an image in Reading view, click an image twice in Live Preview, or use its
   hover **Zoom** button. Don't add a community lightbox plugin, and don't intercept
   clicks.
2. **The lightbox does not cover your two real cases:**
   - **[No keyboard way in from Vim.](#why-vim-users-cannot-reach-the-native-lightbox-from-the-keyboard)**
     No command opens the lightbox. Its `Space` shortcut is consumed by Vim in normal
     mode.
   - **[Plain image links never reach it.](#images-in-the-vault)** The vault has **239**
     links like `[[img/foo.png]]` across 117 hand-written notes, against only **16**
     embeds. Opening one of those links today gives a bare image tab with no zoom.
3. **[`Z` is free.](#whether-z-is-free)** `Z`, `ZZ` and `ZQ` are unbound everywhere in
   Obsidian's Vim stack: CodeMirror Vim, Obsidian's own mappings, your vimrc, and
   bob-plugins. [Three reports](#disagreements-resolved) warned of a `ZZ`/`ZQ` clash or
   a wait-for-the-next-key delay. That applies to real Vim, not Obsidian. Keep `Z`.
4. **[Recommendation:](#recommended-solution)** add a "Zoom image on cursor line"
   command to **bob-navigation-hotkeys** and bind it with `nmap Z` in
   `obsidian_vimrc.md`.
   - **What it opens:** it finds the image reference on the cursor line (embed, plain
     link, or Markdown image) and opens it in a **plugin-owned `Modal` viewer** built
     only on public APIs.
   - **Viewer controls:** it opens fitted to the window, with zoom, pan, and 1:1 for
     Retina screenshots. `Esc`, `q`, `Ctrl+[` or `Z` closes it.
   - **No writes:** it never changes the vault.
   - **Native lightbox:** reusing it for embeds, through an undocumented internal, is a
     reasonable later option but not v1
     ([why not the hybrid now](#why-not-the-hybrid-now-and-when-to-reopen-it)).

## Critique of the plan

**Is this a good idea? Yes, once it is scoped as a read-only inspection gesture.** All
five reports agree the need is real, and the evidence supports them.

- **Small thumbnails need zoom on demand.** `|400` keeps notes scannable, and a peek
  lets you keep it.
- **You drive Obsidian from Vim** (`]s`, `!`, `<CR>`, `\p`). A mouse-only Zoom button
  won't get used in a review walk.
- **Two-thirds of your image references can't be zoomed at all today.** The work isn't
  gold-plating.

Where the original framing goes wrong, or could:

1. **"Zoom" has two meanings, and only one is wanted.** Obsidian's `+`/`-`, `g+`/`g-`,
   `:image grow` and the "Mousewheel Image Zoom" plugin all **resize the embed**, which
   writes `|width`. A peek must never write. That rule also keeps it clear of the
   `<!-- highlights:begin/end -->` regions that the scan rewrites.
2. **A key isn't a design.** The open questions are what gets targeted, what opens, how
   it closes, and where the code lives. [The recommended design](#recommended-design)
   answers each.
3. **Don't rebuild what Obsidian shipped.** mus and gem assumed there was no native
   lightbox and proposed click-to-zoom plugins or click interception. On 1.14 that would
   fight core Obsidian for the same click. The mouse path is already solved.
4. **Don't make the mouse the main trigger.** gem argued that because the eye is
   already on the image, clicking beats moving the cursor. That's true, and native
   clicks already cover it. `Z` exists for the moments your hands are on the keyboard.
   It doesn't replace clicking.
5. **Keep it a reading aid, not a media manager.** Leave out rotate, flip, crop, copy
   and download toolbars, galleries, and persistent zoom.

## What exists today

This section is verified. All code-level findings come from reading code. I did not
drive the Obsidian UI, and
[the risks and checks](#risks-and-checks-before-and-after-building) list what still
needs a hands-on check.

### Images in the vault

Image references, by form:

- **Plain image wikilink `[[img/x.png]]` (not an embed)**
  - *Hand-written notes:* **239 in 117 notes**
  - *Incl. `_generated/`:* 329 in 152
  - *Notes:* Mostly root, `ref/`, `lit/` and `2024/` notes, e.g.
    `See [[img/vim_veteran_redir.png]]`
- **Image embed `![[img/x.png|400]]`**
  - *Hand-written notes:* **16 in 8 notes**, 14 with a width
  - *Incl. `_generated/`:* 16
  - *Notes:* Mostly `- ![[img/2026…png|400]]` capture screenshots, plus a few in ref
    notes and blockquotes
- **Markdown image `![](…)`**
  - *Hand-written notes:* 1
  - *Incl. `_generated/`:* 1
  - *Notes:* Absolute `/Users/bbugyi/…` path. Not a vault file, so out of scope
- **Lines with more than one image reference**
  - *Hand-written notes:* **0**
  - *Incl. `_generated/`:* —
  - *Notes:* Simple targeting is enough ([resolving the target](#resolving-the-target))

More about the images and references:

- **Image files:** 196, nearly all PNG. Typical captures are 1.4k–2.9k px wide Retina
  screenshots. At `|400`, about 14% scale, their text can't be read.
- **Context:** 168 references sit on list lines, 83 in prose, and 4 in blockquotes.
- **Both forms are still growing.** Since June the vault history added about 37 embed
  lines and 64 plain-link lines. These are counts of added diff lines, so moved lines
  count too.

These counts come from my census and match cld's and grk's exactly. mus's Dataview scan
agrees in direction.

### What Obsidian gives you natively

Confirmed in the Obsidian 1.14.4 bundle.

- **Lightbox.** This is a module-private class (`qF`) appended to `activeDocument.body`.
  Its controls:
  - `Esc` closes. `Space` closes when the key is released.
  - `=` zooms in and `-` zooms out, in ×1.2 steps from 1× to 10×.
  - `←` and `→` step through the images.
  - The wheel zooms, double-click zooms, and dragging pans.
  - There is no `+`, `q`, `0`, `hjkl`, or keyboard pan.
- **It is opened from exactly two places:**
  - **Live Preview.** `livePreview.showImage(widget)` builds the gallery from the image
    embeds currently in the decoration set. If the widget isn't among them, it **does
    nothing, silently**. Two things call it: the hover **Zoom** button (hidden on images
    narrower than 80 px), and a second click on an image that is already selected.
  - **Reading view.** `handleMediaClick` runs on a click on any rendered `<img>`.
- **No way to open an arbitrary URL.** The class isn't exported, it isn't a command,
  and the public `obsidian.d.ts` (cdx, cld @ `9abd960`) has no image viewer. cdx's
  inspection is consistent with this.
- **The image keymap.** It sits at `Prec.high` and only works on a selected image:
  - `Space` opens the lightbox.
  - `+`, `-` and `=` resize the embed, which **writes `|width` into the note**.
  - `Enter` edits the link and `Tab` edits the alias.
  - `Backspace` deletes the embed.
- **The image file view** (what opens when you follow `[[img/x.png]]`) is a bare `<img>`
  in `.image-container`, with no zoom or pan.

### Why Vim users cannot reach the native lightbox from the keyboard

- **Vim runs first.** Obsidian installs Vim with `Prec.highest`
  (`isVimEnabled() && push([…, Te.highest(GU), …])`), above the image keymap.
- **Only a few keys reach the image controller.** In normal mode, `tryHandleKey` passes
  only `h`, `l`, `←` and `→` to `enterOrExitImage`, which is how `l` selects an image.
- **Space never gets there.** CodeMirror Vim's default keymap maps `<Space>` to `l`. Vim
  consumes it before the image keymap can open the lightbox. The 1.13.7 forum thread
  reports the same pattern for `Enter`.
- **Enter is taken twice over.** Your task-status-cycler maps normal-mode `<CR>` anyway.
- **Obsidian's own Vim image commands only resize or edit:** `g+`, `g-`, `g=`, `g<CR>`,
  and `:image grow|shrink|reset|edit`. None of them opens the lightbox.

**This settles a disagreement.** grk expected "`l` to select, then Space" to work. On
the code, it does not. That claim is code-level and was not runtime-tested;
[the risks and checks](#risks-and-checks-before-and-after-building) have the 10-second
check.

### What bob does with an image link today

- **`Enter`, `[[` and `]]` skip images.** They share
  `toLineLinkCandidate` (`640-plugin-notes-and-task-move.js:237`), which returns `null`
  for any resolved file that isn't Markdown.
- **`!` (toggle-line-transclusions) turns a link into an embed.** That is a vault write.
  It is the "make this image visible" gesture, not a way to zoom.
- **Reusable helpers already exist:**
  - `parseWikiLinkAt(line, i, { allowTransclusion: true })` in `680-plugin-link-parse.js`
  - `parseTransclusion*At` in `180-editor-transactions.js`
  - `resolveLinkTargetFile`
  - `getVimRepeat`
  - The Cmd+Enter → PDF command, `677-plugin-ref-pdf-open.js`. It is the natural
    sibling of an image command.

### Whether Z is free

`Z…` bindings in each layer:

- **CodeMirror Vim default keymap (`8640966`, and the bundled `vim.js`):** None. Only
  lowercase `zz`, `zt`, `zb`, `z.`, `z<CR>`, `z-`
- **Obsidian `app.js` Vim additions:** Only `g+`, `g-`, `g=`, `g<CR>`, and Ex `:image`
- **`obsidian_vimrc.md`:** None (`-`, `[[`, `]]`, `!`, `[<Space>`, `]<Space>`, `<C-j>`,
  `<C-k>`, `\<`, `\>`, `\\`, `]s`, `[s`, `[S`, `]S`)
- **vimrc-support plugin, `hotkeys.json`, bob-plugins `mapCommand`s:** None

Because nothing starts with `Z`, a `Z` mapping fires immediately, with no wait for a
second key. A Neovim reflex `ZZ` currently does nothing in Obsidian. With the viewer, it
becomes a harmless open-then-close ([viewer controls](#viewer-controls)).

## Requirement adjustments

These adjustments are explicit, and each can be accepted or rejected alone. Each item
names the original or implied requirement, then what it is adjusted to and why.

- **A1. "Zoom in on images"**
  - *Adjusted to:* **Temporary, read-only inspection.** It opens a large view and closes
    back to exactly where you were. No `|width` edits, no link-to-embed conversion, no
    cursor move, no jump-list entry, no vault write of any kind
  - *Why:* Separates peeking from Obsidian's resize verbs, and protects Highlights
    regions
- **A2. "images / inline image links"**
  - *Adjusted to:* **Plain image wikilinks are a first-class target, alongside embeds
    and `![](…)`/`[](…)` with an image path.** Explicit `http(s)` image URLs pass
    through. Nothing is fetched just to find out whether a link is an image
  - *Why:* 239 vs 16. Native mouse paths can't reach plain links
- **A3. "a new `Z` keymap"**
  - *Adjusted to:* **Keep `Z`, normal mode only, set in `obsidian_vimrc.md`.** Insert
    and Visual modes are untouched. Also ship a palette command, "Zoom image on cursor
    line", with no default hotkey
  - *Why:* `Z` is verifiably free ([whether Z is free](#whether-z-is-free)). The palette
    command makes it discoverable and bindable without Vim
- **A4. Targeting unspecified**
  - *Adjusted to:* **Scoped to the line:** the image ref containing the cursor, else the
    first one after the cursor, else the last one before it, else
    `Notice("No image on this line")`. Never look beyond the current line. Ignore refs
    inside inline or fenced code
  - *Why:* Predictable. A guess three bullets away is worse than a notice
- **A5. Viewer unspecified**
  - *Adjusted to:* **One owned viewer for every `Z` target.** Native click and
    Zoom-button behavior stays exactly as it is
  - *Why:* One key vocabulary, public API only, covers all four editor situations
    (embed, link, Live Preview, Source)
- **A6. Exit unspecified**
  - *Adjusted to:* **`Esc`, `q`, `Ctrl+[` and `Z` close.** Viewer keys never reach the
    note
  - *Why:* Same close vocabulary as the Task Card and decay card. Makes `ZZ` harmless
- **A7. Scope**
  - *Adjusted to:* **Out of v1:** Reading-view keyboard trigger (native click covers
    it), galleries, rotate/copy/download/yank toolbars (gem's `y`), PDFs (Highlights
    owns them), Mermaid, Canvas, mobile, absolute filesystem paths, images inside
    transcluded notes
  - *Why:* Each is a separate problem. Keeps the change to one focused session
- **A8. Implied: "build it"**
  - *Adjusted to:* **Spend 10 seconds on the native check first
    ([risks and checks](#risks-and-checks-before-and-after-building), step 1).** If the
    mouse plus Zoom button was all you were missing, the command is optional
  - *Why:* Avoids building for a changelog item you hadn't seen

## Recommended design

### Placement

- **Home:** new fragments in `plugins/bob-navigation-hotkeys/src/`, listed in
  `src/fragments.json` next to `677-plugin-ref-pdf-open.js`. For example:
  - an image-target resolver and command fragment
  - a separate `ImageZoomModal` fragment, kept extractable
- **Build:** run `npm run build`, and never hand-edit the generated `main.js`. Keep each
  fragment at or under 1000 lines.
- **Validate and deploy:** `npm test`, `npm run docs:check`, then `bob plugins sync`.
- **Repo scope:** no bob-cli changes, and no bob-mac-capture changes (this isn't part of
  the capture contract).

### Command and binding

```js
this.addCommand({
  id: "zoom-image-on-line",
  name: "Zoom image on cursor line",
  editorCallback: (editor, view) => this.zoomImageOnLine(editor, view),
});
```

```vim
" obsidian_vimrc.md
exmap bob_zoom_image obcommand bob-navigation-hotkeys:zoom-image-on-line
nmap Z :bob_zoom_image<CR>
```

Bind the key in one place only, not also in the plugin through `mapCommand`. If you
later want counted `NZ`, move the binding to a plugin `vim.mapCommand("Z", …,
{ context: "normal" })` that uses `getVimRepeat`. This is the only reason to prefer the
plugin layer.

### Resolving the target

The resolver is pure and unit-testable.

1. **Read the line.** Take the current editor line's text, the cursor's `ch`, and
   `view.file.path`. Use the live buffer, not the `metadataCache` links, which can lag a
   just-typed edit.
2. **Find the image refs on the line.** Use the existing parsers, with transclusion
   allowed: `![[t]]`, `[[t]]`, `[[t|alias]]`, `![[t|400]]`, `![alt](dest)`,
   `[text](dest)`.
   - Handle angle-bracket destinations, balanced or escaped parentheses, and
     `%20`-decoding.
   - Strip `#subpath` and `|size` or `|alias`.
   - Skip spans inside inline code or a fenced block.
   - Don't use a whole-line regex like gem's sample code.
3. **Pick one ref** using the [A4 order](#requirement-adjustments).
4. **Resolve it.**
   - **Vault targets:** `resolveLinkTargetFile(target, sourcePath)`, then require an
     image extension (`png jpg jpeg gif webp svg bmp avif`), then
     `vault.getResourcePath(file)`. The resolver must use the **source note's** path.
     Never search by basename, and never build `file://` URLs.
   - **`http(s)` targets:** use them as-is, but only in `![]()` syntax or when the URL
     path ends in an image extension.
   - **Failures** produce a notice and do nothing else: "Image not found: …" or "Not an
     image: …". PDFs are left to Cmd+Enter / Highlights.

[The source-aware resolution diagram](#figure-source-aware-image-resolution) traces the
proposed command's branches from the live line's image references to the owned modal or
a notice, resolving vault targets against the source note.

<div id="figure-source-aware-image-resolution">

```mermaid
flowchart TD
  S["Live-line image references"]
  S -->|"none on line"| N["Notice; stop"]
  S -->|"vault target"| V["Resolve from source note"]
  S -->|"HTTP(S): image syntax / extension"| U["URL as-is"]
  V -->|"image file: getResourcePath"| M["Owned modal"]
  V -->|"missing / non-image"| N
  U --> M
```

_Proposed resolution: use the source note for vault images; accept only eligible HTTP(S) targets._

</div>

### The viewer

The viewer is `ImageZoomModal`, about 150–250 lines plus CSS.

- **Structure.** An Obsidian `Modal` with its own `bob-image-zoom-*` classes. Don't
  reuse `.lightbox`, because native CSS and themes target it.
  - A full-viewport dark backdrop (match native's ~0.9 opacity, so the two feel like one
    feature).
  - The filename as a title.
  - One `<img>` whose source is the original file, so the `|400` hint is ignored.
- **Opening state.** Fit to a padded viewport (`contain`). Never upscale automatically
  past the image's natural size.
- **Load failure.** Show a notice and close.
- **Window.** Mount in the active window's document, so pop-outs work (1.13.7 had to fix
  exactly this for the native viewer).
- **Cleanup on close.** Remove every listener and cancel pending image loads. gem's
  sample code leaks `window` listeners; don't copy it.
- **Focus on close.** Return focus to the original editor: same note, cursor, scroll,
  and Vim normal mode. If that editor is gone, don't steal focus.

### Viewer controls

All keys are registered on the modal's `scope`, so none of them reaches the note. Each
input and its action:

- **`Esc`, `q`, `Ctrl+[`, `Z`:** Close
- **`+` or `=` / `-`:** Zoom in / out, bounded. Inside the viewer only; never resizes
  the embed
- **`0`:** Fit to window
- **`1`:** **Device-pixel 1:1**: natural size ÷ `devicePixelRatio`, which is how a
  Retina screenshot looked when it was captured (cld's idea)
- **`h` `j` `k` `l`, arrow keys:** Pan when zoomed. There's no gallery in v1, so
  `h`/`l` have nothing else to do
- **Wheel, or trackpad pinch (`wheel` + `ctrlKey`):** Zoom toward the pointer
- **Drag:** Pan
- **Double-click:** Toggle fit ↔ 1:1
- **Click on the backdrop:** Close

### Tests and docs

- **Unit tests** (`node --test`, added to `npm test`):
  - **Parser** fixtures taken from real vault lines:
    - `- ![[img/20260901_085041.png|400]]`
    - `See [[img/vim_veteran_redir.png]]`
    - `> ![[ref/….assets/….png|549]]`
    - `> [!quote] Image ![[…]]`
    - an image link inside backticks
    - `[[note]]`
    - a `.pdf`
    - two refs on one line
    - no image
  - **Picker order**, including a cursor before, inside, and after a ref.
  - **Resolution** against a fake `metadataCache` and `vault`, covering duplicate
    basenames, a relative path, and Unicode or spaces.
  - **Keys** inside the modal.
- **Docs:** a "Zoom image on cursor line" section in bob-plugins
  `docs/bob-navigation-hotkeys.md` (mounted into the site), then run `npm run docs:gen`
  and `docs:check`. Say that it never writes, that native click and the Zoom button still
  own embeds, and that `Z` comes from the vimrc.

**Effort:** one focused agent session. Roughly 250–350 lines of JS, about 60 lines of
CSS, about 150 lines of tests, and one docs section.

## Options considered

Each option is rated on Vim `Z`, embeds, the 239 plain links, and internals, with a
verdict:

0. **Do nothing: native click or Zoom button**
   - *Vim `Z`:* ✗
   - *Embeds:* ✓
   - *239 plain links:* ✗ (bare image tab)
   - *Internals:* —
   - *Verdict:* Baseline for mouse moments. Keep it
1. **vimrc-only mapping to a native command**
   - *Vim `Z`:* —
   - *Embeds:* —
   - *239 plain links:* —
   - *Internals:* —
   - *Verdict:* **Impossible.** No command opens the lightbox
2. **Community lightbox plugin (Image Toolkit, Image Workflow, Click Image to Zoom,
   Fullscreen Image, Lightbox, Image Zoom)**
   - *Vim `Z`:* ✗
   - *Embeds:* duplicates native
   - *239 plain links:* ✗
   - *Internals:* —
   - *Verdict:* Reject. Fights native clicks, adds a third-party dependency
3. **Image Peek (hover + Space) / core Page Preview (Cmd-hover popover)**
   - *Vim `Z`:* ✗
   - *Embeds:* ✓ / small
   - *239 plain links:* ✗ / small popover
   - *Internals:* —
   - *Verdict:* Mouse-only. Not "a nice large version"
4. **Mousewheel Image Zoom, `:image grow`, `g+`**
   - *Vim `Z`:* —
   - *Embeds:* resizes
   - *239 plain links:* —
   - *Internals:* —
   - *Verdict:* Wrong verb: writes `|width`
5. **`!` to embed the link, then the native lightbox**
   - *Vim `Z`:* ✗
   - *Embeds:* —
   - *239 plain links:* after a write
   - *Internals:* —
   - *Verdict:* Reject: two gestures plus a vault write
6. **Owned `Modal` viewer behind `Z`**
   - *Vim `Z`:* ✓
   - *Embeds:* ✓
   - *239 plain links:* ✓
   - *Internals:* none
   - *Verdict:* **Recommended**
7. **Hybrid: native lightbox for Live Preview embeds through `livePreview.showImage`,
   owned viewer for the rest**
   - *Vim `Z`:* ✓
   - *Embeds:* ✓ native
   - *239 plain links:* ✓
   - *Internals:* yes
   - *Verdict:* Credible later upgrade
     ([why not the hybrid now](#why-not-the-hybrid-now-and-when-to-reopen-it))
8. **External viewer (`openWithDefaultApp` → Preview.app, `qlmanage -p`)**
   - *Vim `Z`:* ✓
   - *Embeds:* ✓
   - *239 plain links:* ✓
   - *Internals:* `openWithDefaultApp` is internal
   - *Verdict:* Leaves Obsidian. Possible follow-on as `gx`
9. **Synthetic clicks or DOM-clicking the Zoom button**
   - *Vim `Z`:* ✓
   - *Embeds:* ✓
   - *239 plain links:* ✗
   - *Internals:* DOM
   - *Verdict:* Reject: the first click moves the selection, and it only works on
     rendered lines

### Why not the hybrid now and when to reopen it

cld makes the best case for option 7:

- **You get native features for free:** the gallery, the open animation, momentum pan,
  and future Obsidian improvements.
- **It degrades safely:** feature detection plus fallback means a broken internal costs
  polish, not the feature.

I'd still defer it:

- **The benefit is small here.** It applies to 16 embeds in 8 notes, and no line holds
  two images.
- **It's fragile.** It depends on an undocumented getter
  (`CodeMirrorAdapter.prototype.livePreview` → `imageWidgetAt` / `showImage`). It also
  needs an "did a `.lightbox` actually appear" check, because `showImage` silently does
  nothing when the widget isn't in the decoration set.
- **It splits the controls.** Native has no `q`, `Ctrl+[`, `0`, `1` or keyboard pan, so
  `Z` would behave differently on an embed than on a link, unless you also add cld's
  synthetic-key translation layer.

**Reopen it if** you prefer the native viewer's feel for embeds after using v1. The
implementation is then additive:

1. Embed refs in Live Preview try
   `lp.showImage(lp.imageWidgetAt(pos, w => w.start === pos))`.
2. Check that a lightbox actually opened.
3. If not, fall back to the owned modal.
4. Warn once in the console when the internals are missing.

## Disagreements resolved

Each question the reports disagreed on, with their positions, the resolution, and its
basis:

- **Does Obsidian have a native lightbox?**
  - *Positions:* cdx, cld, grk: yes. mus, gem: no ("opens image pane", "no built-in
    lightbox")
  - *Resolution:* **Yes, since 1.13. mus and gem are out of date.**
  - *Basis:* Changelogs, plus the `qF` class and its two openers in the 1.14.4 bundle
- **Does `Z` collide with `ZZ`/`ZQ`, or add a timeout delay?**
  - *Positions:* grk, mus, gem: yes, so use `\z`, `<Space>z` or `Alt+Z`. cdx: check
    first. cld: free
  - *Resolution:* **Free, with no delay. Keep `Z`.**
  - *Basis:* [Whether Z is free](#whether-z-is-free). All three alternatives are worse:
    `<Space>z` makes `Space` a pending prefix; `Alt+Z` is a global chord that steals
    Option-Z (Ω) while typing; `\z` is fine but needless
- **Does native "select, then Space" work in Vim normal mode?**
  - *Positions:* grk: yes. cld: no
  - *Resolution:* **No** (code-level)
  - *Basis:* Vim at `Prec.highest`, `<Space>`→`l`, `tryHandleKey` only routes
    `h`/`l`/arrows
- **Reuse the native lightbox for embeds (internal `showImage`) or own a viewer?**
  - *Positions:* cld: hybrid with a key-translation layer. cdx: own a viewer unless a
    real native opener is verified. grk: own a viewer
  - *Resolution:* **Own a viewer for v1. Native reuse is deferred
    ([why not the hybrid now](#why-not-the-hybrid-now-and-when-to-reopen-it)).**
  - *Basis:* The owned viewer is needed anyway, for 239 links and Source mode. The
    native path covers 16 embeds in 8 notes, through an undocumented internal that fails
    silently, and gives a different key vocabulary
- **Intercept clicks on rendered images?**
  - *Positions:* mus, gem: yes. cdx, cld, grk: no
  - *Resolution:* **No**
  - *Basis:* Native lightbox owns clicks and the Zoom button
- **Install a community plugin (Image Toolkit, Image Workflow, Image Peek, …)?**
  - *Positions:* gem: trial Image Workflow first. Others: no
  - *Resolution:* **No**
  - *Basis:* All are click or hover driven. None opens the image at the text cursor
    (cdx read Image Toolkit 1.4.3's source: no such command). They duplicate the native
    lightbox
- **Plugin home**
  - *Positions:* cld: new `bob-image-zoom` plugin. cdx, grk, mus:
    bob-navigation-hotkeys
  - *Resolution:* **bob-navigation-hotkeys, in its own fragments**
  - *Basis:* Reuses the link parsers and resolver, and sits next to Cmd+Enter→PDF. No
    manual enable step (`bob plugins sync` never edits `community-plugins.json`). Easy
    to extract later
- **Where the binding lives**
  - *Positions:* cld: plugin `mapCommand("Z")`. grk, mus: vimrc `nmap`. gem: plugin
    `\z`, `<CR>` and `Alt+Z`
  - *Resolution:* **vimrc `exmap`/`nmap Z`**
  - *Basis:* It is the pattern most nav-hotkeys commands use (`-`, `!`, `[[`, `]s`). The
    user owns it, and removing it is one line. Counts aren't needed
    ([resolving the target](#resolving-the-target))
- **Targeting rule**
  - *Positions:* cld: counted `NZ`, then the ref containing the cursor, then the next
    one, then the last. cdx: the cursor's ref, else the line's only image. grk:
    line-link picker
  - *Resolution:* **The ref containing the cursor, else the next on the line, else the
    previous one. No counts and no picker in v1**
  - *Basis:* 0 lines in the vault have two image refs. In Live Preview the cursor can't
    sit inside a rendered embed (atomic range), so a rule scoped to the line is required

## Risks and checks before and after building

1. **Native check (10 seconds, do it first).** In `sase_blog.md`, in Live Preview and
   Vim normal mode:
   - Move onto a `![[img/…|400]]` line and press `l` until the image is selected. Then
     press `Space`. The code says the cursor moves and no lightbox opens.
   - Then click the image twice, or hover and click **Zoom**.

   If the mouse path is all you need, stop here ([A8](#requirement-adjustments)).
2. **Cursor next to a Live Preview embed.** The rendered embed is an atomic range, so
   the Vim cursor sits before or after it. The line-scoped rule
   ([A4](#requirement-adjustments)) handles this. Smoke-test the list-child and
   blockquote/callout cases.
3. **Smoke checklist on the Mac.**
   - **Plain link and embed:** `Z` opens the viewer. Check that `1` is crisp.
   - **Close keys:** `Esc`, `q`, `Ctrl+[` and `Z` each close back to the same cursor,
     scroll and normal mode. `ZZ` opens then closes.
   - **No image on the line:** a notice, and nothing else.
   - **Insert and Visual mode:** `Z` types or behaves as before.
   - **Other windows and modes:** a pop-out window works, Source mode works, and the
     palette command works with Vim off.
   - **No writes:** `git diff` on the vault is empty afterwards.
4. **Future Obsidian Vim binds `Z…`.** Low likelihood. Re-point the `nmap` to `\z`.
5. **`g+`/`g-` are easy to hit** once you start selecting images, and they write. Worth
   a vimrc comment. Don't unmap them unless they bite you.

## Corrections to earlier research

- `obsidian_1_14_upgrade_for_bob_setup__final.md` says (§4 and §7 step 4): "select the
  image, run `:image grow`, then press Space for the lightbox." That has two problems:
  - `:image grow` **writes** `|width` into the note.
  - Per the 1.14.4 code, `Space` in Vim normal mode is consumed as `l` and won't open
    the lightbox.
  - **Use instead:** in Reading view, click the image. In Live Preview, click the image
    twice or use the hover Zoom button. Once built, use `Z`.
- **mus and gem:** native click doesn't navigate to an image pane on 1.13 and later. It
  opens the lightbox (Reading view) or selects the image (Live Preview).
- **gem, grk and mus:** in Obsidian, `ZZ`/`ZQ` don't exist, and a `Z` mapping adds no
  timeout delay.

## Follow-ons

These are not v1; file them only if they're missed.

- A gallery in the owned viewer covering every image reference in the note, links and
  embeds alike. Use `]`/`[` so it doesn't collide with `hjkl` pan.
- Counted `NZ`. Only worthwhile if lines with several images ever appear.
- `Enter`, `[[` and `]]` treating image links as targets. This would change shared
  link-picking semantics and needs its own decision (grk ADJ-9).
- `gx`: open the image in Preview.app for crop or markup.
- Native-lightbox delegation for embeds
  ([why not the hybrid now](#why-not-the-hybrid-now-and-when-to-reopen-it)).

## Recommended solution

**Build a read-only "Zoom image on cursor line" command in bob-navigation-hotkeys and
bind it to `Z` in `obsidian_vimrc.md`.**

1. **Check native first.** Spend 10 seconds confirming the native lightbox and its mouse
   paths: click in Reading view, click twice or use the Zoom button in Live Preview.
   Keep using them. Don't install a lightbox plugin, and don't intercept clicks.
2. **Add the command** in new bob-navigation-hotkeys fragments. It parses the cursor
   line's image references from the live buffer:
   - forms: `![[x|400]]`, `[[x]]`, `![](x)`, `[](x)`
   - which one: the reference containing the cursor, else the next, else the previous;
     otherwise a notice
   - resolution: against the source note, using `vault.getResourcePath`
3. **Open the image in a small public-API `Modal` viewer.** It opens fitted to the
   window, with `+`/`=`/`-` zoom, `0` fit, `1` device-pixel 1:1, `hjkl` and drag pan,
   and wheel or pinch zoom at the pointer. `Esc`, `q`, `Ctrl+[` and `Z` close it, with
   the cursor, scroll and Vim mode restored. It never writes to the vault.
4. **Bind it** with `exmap bob_zoom_image obcommand
   bob-navigation-hotkeys:zoom-image-on-line` and `nmap Z :bob_zoom_image<CR>`. `Z` is
   verifiably free in Obsidian's Vim. The palette command covers non-Vim use.
5. **Defer** native-lightbox delegation for embeds
   ([why not the hybrid now](#why-not-the-hybrid-now-and-when-to-reopen-it)), galleries,
   counts, and Enter-on-image-links until v1 has been used and one of them is actually
   missed.

## Method and inputs

> **Research request (paraphrased).** Bryan wants a way to zoom images and inline image
> links in Obsidian, so he can see a large version when he needs one. He suggested a new
> `Z` keymap to trigger it. He asked for research to help pick an implementation, a
> critique of the plan, clearly flagged adjustments to the requirements, and a
> recommended solution.

**Consolidated report** · lead researcher · 2026-10-20

**Inputs**

- Five independent reports in this directory: `__cdx`, `__cld`, `__grk`, `__mus`, `__gem`.
- My own checks, aimed at the points where the reports disagreed:
  - **Obsidian 1.14.4 app bundle.** Copied read-only from the MacBook (asar sha256 prefix
    `146ef8470d8cbb4a`, the same build cld read). I extracted `app.js` and
    `lib/codemirror/vim.js` and read the lightbox class, the Live Preview image
    controller, the Vim key path, and Obsidian's own Vim mappings.
  - **`replit/codemirror-vim` @ `8640966`.** I read its default keymap.
  - **Vault `~/bob` @ `9e4db516`.** I re-ran the image-reference census and read
    `obsidian_vimrc.md`, `app.json`, `hotkeys.json`, `community-plugins.json`, and
    `core-plugins.json`.
  - **bob-plugins @ `ff36987`.** I read the bob-navigation-hotkeys link parsers,
    `toLineLinkCandidate`, the Vim `mapCommand` inventory, and the fragment layout.
  - **bob-cli `src/native/plugins/`.** Confirmed that `bob plugins sync` reads
    `community-plugins.json` but never writes it.
  - **Prior research.** `research:202610/obsidian_1_14_upgrade_for_bob_setup/…__final.md`.
    Its lightbox advice is corrected in
    [Corrections to earlier research](#corrections-to-earlier-research).

## Sources

- **Obsidian changelogs:**
  - [1.13.2 catalyst, 2026-07-14](https://obsidian.md/changelog/2026-07-14-desktop-v1.13.2/): lightbox, Space in Live Preview, `:image`
  - [1.13.3, 2026-07-21](https://obsidian.md/changelog/2026-07-21-desktop-v1.13.3/): Zoom button, drag to pan
  - [1.13 public (1.13.4), 2026-07-30](https://obsidian.md/changelog/2026-07-30-desktop-v1.13.4/)
  - [1.13.7, 2026-08-12](https://obsidian.md/changelog/2026-08-12-desktop-v1.13.7/): pop-out lightbox fix
  - [1.14.4, 2026-10-05](https://obsidian.md/changelog/2026-10-05-desktop-v1.14.4/)
- **Obsidian forum:** [Unable to use Vim-mode to edit the markdown of previewed images](https://forum.obsidian.md/t/unable-to-use-vim-mode-to-edit-the-markdown-of-previewed-images/117839) (Aug 31 – Sep 6, 2026)
- **Obsidian 1.14.4 bundle** (Mac, asar `146ef8470d8cbb4a`):
  - `app.js`: the lightbox class and its key handler, `livePreview.showImage`,
    `handleMediaClick`, the image keymap at `Prec.high`, Vim at `Prec.highest`,
    `tryHandleKey`, and the `g+`/`g-`/`g=`/`g<CR>` and `:image` mappings
  - `lib/codemirror/vim.js`: `<Space>`→`l`, and no `Z` bindings
- **`replit/codemirror-vim` @ `8640966`:** `packages/codemirror-vim-core/vim.js`
  default keymap
- **`obsidianmd/obsidian-api` @ `9abd960`:** no lightbox API (per cdx and cld)
- **bob-plugins @ `ff36987`:**
  - `bob-navigation-hotkeys/src/640-plugin-notes-and-task-move.js:237`
  - `680-plugin-link-parse.js`, `180-editor-transactions.js`,
    `677-plugin-ref-pdf-open.js`, `090-local-task-ids.js` (`getVimRepeat`)
  - the `mapCommand` inventory
- **bob-cli** `src/native/plugins/model.rs` (`community-plugins.json` is read only)
- **Vault @ `9e4db516`:** `obsidian_vimrc.md`, `.obsidian/{app,hotkeys,community-plugins,core-plugins}.json`,
  and the image census
- **Community plugins surveyed** (via the reports):
  - Image Toolkit (source @ `334cfa3`, read by cdx)
  - Image Workflow (`1spread/obsidian-image-enlarge`, read by mus)
  - Image Hover Preview (`shin2w`)
  - Image Peek, Lightbox, Image Zoom, Click Image to Zoom, Fullscreen Image,
    Mousewheel Image Zoom
