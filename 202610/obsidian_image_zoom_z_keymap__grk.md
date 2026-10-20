# Zoom images and image wikilinks from a Vim key in Obsidian

Researcher: `grk`. Independent report. Do not treat this as the swarm synthesis.

- **Question:** How should Bob let you see a large version of an image, or of an inline image wikilink, when you want one? The starting idea is a new `Z` keymap. Critique that plan, adjust requirements where justified, and recommend an implementation path.
- **Evidence:** Obsidian 1.13.2 / 1.13.4 changelogs (native lightbox); Obsidian 1.14.4 is the live Mac app (`research:202610/obsidian_1_14_upgrade_for_bob_setup`); WhiteNoise's documented Vim image maps (`g+` `g-` `g=` `g<CR>`) and the 1.13 Vim image thread; vault `obsidian_vimrc.md` + vimrc-support `data.json`; `.obsidian/{community-plugins,hotkeys}.json`; bob-navigation-hotkeys `toLineLinkCandidate` / `handleVimEnterLinkAction` / `\s` `mapCommand`; bob-ledger-tools `\p\P\o\O`; vault image census 2026-10-20; community plugins Image Toolkit, Click Image to Zoom, Fullscreen Image, Image Peek, Mousewheel Image zoom, Image Zoom & Drag.
- **Date of evidence:** 2026-10-20. bob-plugins @ linked checkout after `origin/master` fast-forward. Vault `~/bob` read-only.

## Bottom line

The want is real. The proposed `Z` keymap as a new lightbox product is the wrong shape.

You already have a first-party fullscreen image viewer: Obsidian 1.13 shipped a lightbox, and the Mac is on 1.14.4. Click the image or its **Zoom** button; in Live Preview, select the widget and press Space. Arrow keys step through embeds in the note; drag pans. That path is enough for **embeds**.

It is not enough for **your actual corpus**. A vault scan today:

| Kind | Count | Notes |
| --- | ---: | --- |
| Image files (`img/` and elsewhere) | 196 | 191 `.png`, 5 `.jpg` |
| `![[…png/jpg]]` embeds | 16 | 8 notes (`sase.md`, `sase_blog.md`, a few refs, `cash.md`, …) |
| `[[img/….png]]` wikilinks with **no** `!` | **329** | **152 notes** |
| Markdown `![](…)` images | 1 | an absolute `/Users/bbugyi/…` path, not a vault file |

Native lightbox only opens **rendered** images. `[[img/foo.png]]` is a link, so it never becomes a selectable widget and never grows a Zoom button. Vim `Enter` on that line also does nothing useful: `toLineLinkCandidate` drops any resolved file whose extension is not `md`, then Enter falls through to “next line.” `[[` / `]]` use the same helper, so they skip images too.

**Recommended solution:** do not install a community lightbox, and do not write a second pan/rotate viewer. Add one palette command on **bob-navigation-hotkeys** that resolves the image target on the current line (wikilink, embed, or markdown image) and opens a **read-only overlay** of that file. Bind it from `obsidian_vimrc.md` as `Z` if you still want that letter after seeing the native recipe. Prefer the plugin-owned `\z` as the default so `Z` does not eat Vim’s `ZZ`/`ZQ` prefix. No vault writes. No click hijack.

Try the native recipe on an embed first (`sase_blog.md` has several `![[img/…]]` lines). If that is the “nice large version” you wanted, stop. If the pain is the 329 bare `[[img/…]]` links, the command above is the work.

## Is this a good idea?

### What is right in the request

- **Peeking a screenshot without leaving the note is a real editor verb.** Screenshots land in `img/` as timestamped PNGs and get dropped into area notes, SASE notes, and old zorg dumps as `[[img/….png]]`. Opening a tab, then closing it, is the current “large version.” An overlay that Esc-dismisses is the right shape, the same family as the Task Card / decay card: look, then return.
- **A Vim key is the right trigger class.** You edit in Vim mode (`app.json` `vimMode: true`), vimrc-support is on, chord display is on, and the daily gestures already live in `obsidian_vimrc.md` (`-`, `!`, `]s`, `[[`, `]]`) plus plugin `mapCommand`s (`Enter`, `\p`, `\s`). A mouse-only Zoom button will not get used on a review walk.
- **The job is view-only.** Zoom-to-look is a different verb from `:image grow` / `g+`, which write `\|width` into the note. The 1.14 upgrade report already warned not to resize inside `<!-- highlights:begin/end -->` because the next scan rewrites that region. A peek must not touch the file.

### Where the request as written is the wrong product

- **A new `Z` keymap is not a design.** It names a key, not a viewer, not a target grammar, not a close chord, not a home plugin. The interesting question is “what opens, from which token, without a write.”
- **Native lightbox already exists and you are on a build that has it.** Public 1.13.4 (2026-07-30): “Click an image or the Zoom button to open it… navigate between all the images embedded in the current file, and click and drag to pan.” Catalyst 1.13.2: in Live Preview, with the image selected, Space opens the lightbox. The 1.14 upgrade synthesis already told you to try this on figure-heavy notes (`:image grow`, then Space). Building a parallel viewer for embeds duplicates core Obsidian and will fight it for clicks.
- **`Z` is a Vim prefix.** Default Vim: `ZZ` write-and-quit, `ZQ` quit. Mapping `Z` as a complete command makes those two-key sequences impossible. You do not use them in Obsidian today (the vimrc never mentions them), so the cost is small, but it is real, and it is the same class of override as remapping `-` (Vim: previous line) and `!` (Vim: filter). Those two earn the steal because they fire all day. Image peek is occasional. Occasional verbs belong on the backslash family you already own (`\p` `\P` `\o` `\O` `\s` `\<` `\>` `\\`), or on a vimrc `nmap` you can delete in one line.
- **Community click-to-zoom plugins are leftover 1.12 technology.** Image Toolkit (138k downloads, last update ~a year ago), Click Image to Zoom, Fullscreen Image, Image Peek, Mousewheel Image zoom (163k, writes width into the note). On 1.14 they either steal the native click or duplicate it. Image Peek’s double-click / hover+Space is the only one designed to coexist, and you still would not get a Vim-from-the-line gesture for wikilinks. Do not add a 17th community plugin for this.

### Would I take a different approach?

Yes. I would split the problem in two and only implement the second.

1. **Embeds (16 of them):** use the native lightbox. Recipe below. No code.
2. **Bare image wikilinks (329 of them):** a bob-navigation-hotkeys command that treats an image file as a first-class line target, the way Enter already treats a markdown wikilink and Cmd+Enter already treats a reading-task PDF.

I would not start a new plugin. I would not intercept clicks. I would not teach `:image grow` as a zoom stand-in. I would not make Enter the zoom key (Enter already means “follow the next markdown link on this line,” and mixing “open a note” with “peek a PNG” on a line that has both is a surprise).

## Current surface (what you can do this afternoon)

### Native lightbox (embeds only)

On 1.14.4, for a rendered `![[img/foo.png]]` or `![](foo.png)`:

| Mode | Open | Inside the lightbox | Close |
| --- | --- | --- | --- |
| Reading view | Click the image, or the Zoom button | Arrows = other embeds in this file; drag = pan; Ctrl-wheel zoom (community reports) | Esc, Space, click backdrop |
| Live Preview | Select the image widget, then click or Space | Same | Same |
| Vim Live Preview | `j`/`k` onto the line, `l` to select the widget, then Space | Same | Esc |

Selecting the widget is the Vim tax. WhiteNoise (Obsidian team, 2026-09-01) documented the bundled Vim maps that apply **once the widget is selected**:

```
g+     image grow     (writes size)
g-     image shrink   (writes size)
g=     image reset    (writes size)
g<CR>  image edit     (filename)
```

Plus Ex: `:image grow`, `:image shrink`, `:image reset`, with counts (`:5image grow`). These are **resize-the-embed**, not **peek**. They are also unavailable as `obcommand`s, so vimrc-support cannot bind them with `exmap … obcommand editor:image-edit` (Thomas_Schmall tried; the command is not in the palette). Forum thread: [Unable to use Vim-mode to edit the markdown of previewed images](https://forum.obsidian.md/t/unable-to-use-vim-mode-to-edit-the-markdown-of-previewed-images/117839).

Bob already remaps `<CR>` in normal mode (`task-status-cycler` → `handleVimEnterLinkAction`). Native “Enter edits the selected image” therefore never fires for you in normal mode. Space is still free in `obsidian_vimrc.md` (it only appears inside `[<Space>` / `]<Space>` blank-line maps). Native Space-to-lightbox should work after `l` selects the widget.

### What Bob already does on a line that mentions an image

```javascript
// bob-navigation-hotkeys src/640-plugin-notes-and-task-move.js
if (resolvedFile) {
  if (!this.isMarkdownFile(resolvedFile)) {
    return null;  // png/jpg/pdf/… dropped
  }
}
```

`isMarkdownFile` is `file.extension === "md"`. Consequences:

- Vim `Enter` on `[[img/foo.png]]` or `![[img/foo.png]]`: no candidate, fall through, cursor moves down.
- `[[` / `]]` (`open-prev-link` / `open-next-link`): same helper, images skipped.
- `!` (`toggle-line-transclusions`): **will** turn `[[img/foo.png]]` into `![[img/foo.png]]`. That is a vault write. It is the existing “make this visible as an image” gesture. It is the wrong zoom gesture, because 329 embeds would bloat notes and the next `!` would strip them again.

Cmd+Enter on a reading task opens the PDF in Highlights (`hotkeys.json` binds `bob-navigation-hotkeys:open-reference-pdf-in-highlights` to `Meta+Enter`). Images have no sibling.

Jump to Link is bound to Ctrl+L. Hinting a `[[img/foo.png]]` opens it as a file tab, which is a large view you then have to dismiss. That is the closest keyboard path today, and it is the wrong chrome.

### Keymap neighborhood

`obsidian_vimrc.md` is the live vimrc (`vimrcFileName: "obsidian_vimrc.md"`; there is no `.obsidian.vimrc`). JavaScript vimrc commands are off. No `Z`, `z`, or `\z` map. Fold maps (`za`/`zo`/`zz`) are still core Vim, so **do not steal lowercase `z`**.

Plugin `mapCommand` extras already take:

| Keys | Owner | Job |
| --- | --- | --- |
| `\p` `\P` `\o` `\O` | bob-ledger-tools | Pomodoro units / shift |
| `\s` | bob-navigation-hotkeys | Pin current tab |
| `\<` `\>` `\\` | vimrc | Close tabs |
| `<CR>` `<BS>` `o` `O` `#` | task-status-cycler | Links, open line, move-only |

A new image command belongs next to Enter-on-link and Cmd+Enter-on-PDF, in bob-navigation-hotkeys.

## Options compared

| Option | Covers 329 wikilinks? | Covers 16 embeds? | Vim from the line? | Fights native click? | Vault writes? | Verdict |
| --- | --- | --- | --- | --- | --- | --- |
| **A. Use native lightbox as-is** | No | Yes | Only after `l` selects the widget, then Space | No | No | Do this for embeds. Stop if that was the whole want. |
| **B. Community lightbox (Image Toolkit, Click Image to Zoom, Fullscreen Image)** | No (click on rendered `<img>` only) | Yes, by stealing click | No | Yes | No | Reject on 1.14. |
| **C. Image Peek (hover + Space / double-click)** | No | Yes, coexistence-minded | Hover is not a Vim line gesture | No (double-click) | No | Still misses wikilinks. Skip. |
| **D. Mousewheel Image zoom** | No | Resizes the embed | No | No | **Yes** (`\|width`) | Wrong verb. |
| **E. CSS click-and-hold (Kepano snippet)** | No | Crude | No | Sort of | No | Toy. |
| **F. `!` then native lightbox** | Yes, after a write | Yes | Two gestures + a write | No | **Yes** | Reject as the zoom path. |
| **G. Enter follows image files into a tab** | Yes | Opens the file view, not overlay | Yes (already on `<CR>`) | No | No | Useful follow-link. Different from peek. Optional extra, not the zoom product. |
| **H. Plugin overlay command + `\z` / vimrc `Z`** | Yes | Yes (same overlay, one path) | Yes | No | No | **Do this.** |
| **I. New bob plugin that reimplements Image Toolkit** | Could | Could | Could | Likely | No | Overkill. One command, not a product. |
| **J. `qlmanage -p` / Preview.app** | Yes (Mac) | Yes | Via a command | No | No | Leaves Obsidian. Highlights-shaped, but PDFs already have a dedicated app; images do not need a second one. |

## Requirement adjustments

Call-outs the lead should adopt or explicitly reject.

| ID | Adjustment | Why it is justified |
| --- | --- | --- |
| **ADJ-1** | Treat **bare image wikilinks** as the primary target; embeds are already served natively. | 329 vs 16. The request’s “inline image links” matches `[[img/foo.png]]`, which is how screenshots actually appear. |
| **ADJ-2** | The viewer is a **read-only overlay**. It must not write `\|width`, alt text, or embed markers. | `:image grow` / Mousewheel Image zoom / `!` are different verbs. Highlights regions must not be rewritten by a peek. |
| **ADJ-3** | **Do not intercept clicks** on rendered images. | Native 1.13 lightbox owns click and the Zoom button. A second click handler is a fight you will lose on the next app update. |
| **ADJ-4** | **Do not install a community lightbox plugin.** | 16 community plugins, none of them image viewers, on purpose. Adding Image Toolkit on 1.14 is a regression. |
| **ADJ-5** | Ship a **palette command** first (`bob-navigation-hotkeys:open-line-image` or `zoom-line-image`). Bind keys in `obsidian_vimrc.md`, the way `-` / `!` / `]s` work. | Image peek is occasional and user-owned. Plugin `mapCommand("Z")` is harder to unmap than one vimrc line. Palette gives Reading view / mouse users a path without Vim. |
| **ADJ-6** | **Default Vim binding is `\z`, not `Z`.** Offer `nmap Z :bob_zoom_image<CR>` as an opt-in in the vimrc if you still want the letter after a week of `\z`. | `\z` matches the extra-command family and leaves `ZZ`/`ZQ` and lowercase `z` folds/`zz` intact. `Z` is a prefix steal that `-` and `!` only get because they are daily. |
| **ADJ-7** | Resolve **the image nearest the cursor on the current line**. If several, reuse the existing line-link picker (the Enter-on-link chooser), do not invent a second UI. | Same grammar as `extractLineLinks` / `allowTransclusion: true`. Counted `2Z` is unnecessary in v1. |
| **ADJ-8** | Close with **Esc, `q`, Ctrl+[**, click-backdrop. Optional: wheel zoom inside the overlay. No rotate/flip/invert/copy toolbar in v1. | Task Card already taught those close keys. Image Toolkit’s chrome is how a one-command overlay becomes a plugin you have to maintain. |
| **ADJ-9** | **Do not extend Enter in v1** to open images. File a follow-up if following `[[img/foo.png]]` into a tab (or into this overlay) still feels missing after the peek exists. | Enter currently means “next markdown note.” Mixing peek and follow on one key is the Task Card property-picker failure mode. Cmd+Enter is already the media exception, and it is PDFs. |
| **ADJ-10** | **Out of scope for v1:** Mermaid fences (vault still has ~0), remote/absolute paths (the one `![](/Users/bbugyi/…)` image), note-wide galleries, Canvas, PDFs. | PDFs already have Highlights. Mermaid figures from `bob ref create` land as print PDFs, not as note embeds you zoom. |
| **ADJ-11** | Smoke-test native Space-on-selected-image **before** writing code. If the only pain was “I never found the Zoom button,” the command is optional. | The 1.14 report already queued this. Spending a plugin on a missed changelog is the failure mode to avoid. |

## Recommended solution

### 0. Ten-minute native trial (no code)

1. Open `sase_blog.md` (several `![[img/…]]` embeds).
2. Live Preview, Vim normal mode: `j` to an embed line, `l` until the image widget is selected, Space.
3. Esc. Arrow keys while open. Drag.
4. Click the Zoom button with the mouse once, so you know it exists.

If that is the product, write a vimrc comment pointing at it and stop. Optionally:

```
" Native: select the image widget (l on the embed line), then Space.
" Resize the embed (writes |width):  :image grow  /  g+  g-  g=
```

### 1. If the trial leaves the 329 wikilinks unsolved: one command, one overlay

**Home:** `bob-navigation-hotkeys` (same plugin as Enter-on-link and Cmd+Enter PDF). No new plugin folder.

**Command:** `bob-navigation-hotkeys:zoom-line-image` — “Zoom image on line.”

**Resolve (v1):**

1. Current markdown editor line.
2. `extractLineLinks` with transclusions on, plus markdown `![](…)` / `[](…)` whose target is an image extension.
3. `resolveLinkTargetFile`; accept `png|jpg|jpeg|gif|webp|svg` (svg is rare here; keep it in the allow-list so a future mermaid PNG/SVG drop works).
4. Prefer the candidate whose range contains the cursor; else the first on the line.
5. Zero candidates: `Notice("No image on this line")`.
6. Several equally plausible: the existing line-link picker.

**Open:** a `Modal` (not a new leaf, not a popout window) with:

- `app.vault.getResourcePath(file)` as `<img>` `src`
- `object-fit: contain`; max-width/height 100vw/100vh
- dimmed backdrop
- Esc / `q` / Ctrl+[ / backdrop click close
- focus trap so Vim does not keep moving the note underneath

Optional cheap extras, only if they stay in the same modal: wheel to scale, `0` to reset scale. Skip toolbars.

**Do not** click-dispatch into the native lightbox. There is no documented palette command for it (`editor:image-edit` is not an `obcommand`; WhiteNoise said these are editor-internal). DOM-clicking the Zoom button is a private UI that will break. A 40-line modal you own is cheaper than a private API.

**Keys:**

```
" obsidian_vimrc.md — plugin-owned default is also mapCommand("\\z")
exmap bob_zoom_image obcommand bob-navigation-hotkeys:zoom-line-image
nmap \z :bob_zoom_image<CR>
" Opt-in letter (eats ZZ/ZQ):
" nmap Z :bob_zoom_image<CR>
```

I would ship `\z` from the plugin via `vim.mapCommand("\\z", …)` so it exists even if the vimrc is stale, **and** document the commented `nmap Z` for you to uncomment. That is the smallest disagreement with the original “new `Z` keymap” idea: you can still have `Z`; it should be your vimrc, not a prefix the plugin steals from every Bob vault.

**Tests:** unit-test the resolver (line with `[[img/a.png]]`, `![[img/a.png]]`, mixed note+image, no image, cursor on the second of two images). Plugin fragment tests already cover line-link parsing; extend those fixtures rather than a browser suite.

**Docs:** a short section on bob-navigation-hotkeys: “Zoom image on line.” State that it does not write, that native click/Space still owns embeds, and that `\z` is the default.

### 2. What I would not do

- A 17th community plugin.
- `mapCommand("Z")` inside the plugin.
- Lowercase `z` (folds, `zz` center).
- Making `!` the zoom key (it already toggles embeds and writes).
- Teaching `:image grow` as zoom (it resizes the note).
- A note-wide gallery, rotate/flip, copy-to-clipboard, “open in Preview.”
- CLI (`bob` has no business opening an Obsidian overlay). `cli_rules.md` does not apply.

## Risks

- **Native lightbox and a custom overlay will look slightly different.** Accept that. One chrome for wikilinks, native chrome for embed clicks. Do not try to theme them into one.
- **`g+` / `g-` remain easy to hit by accident** once you start selecting image widgets. They write. Worth a vimrc comment. Out of scope to unmap unless they bite you.
- **Remote / absolute images** (the poker `![](/Users/bbugyi/…)` line) will miss `resolveLinkTargetFile`. Notice, do not fetch arbitrary URLs.
- **Source mode** has no widget; the modal still works because it uses the vault resource path. Good.
- **Reading view:** palette command should walk the preview DOM or re-parse the file text the same way. Parse-the-line from the current file cache; do not depend on CM6 widgets.

## Sources

- Obsidian 1.13.2 catalyst changelog, 2026-07-14: native lightbox; Live Preview Space; `:image grow|shrink|reset`.
- Obsidian 1.13.4 public changelog, 2026-07-30: Zoom button; pan; keyboard image selection.
- Obsidian 1.14.4 public (Mac app as of 2026-10-18 upgrade research).
- WhiteNoise, forum 2026-09-01, Vim `mapCommand` dump for `g+` `g-` `g=` `g<CR>`.
- [Unable to use Vim-mode to edit the markdown of previewed images](https://forum.obsidian.md/t/unable-to-use-vim-mode-to-edit-the-markdown-of-previewed-images/117839).
- `research:202610/obsidian_1_14_upgrade_for_bob_setup` (lightbox already recommended; 16 community plugins listed; Vim on).
- Vault: `obsidian_vimrc.md`; `.obsidian/plugins/obsidian-vimrc-support/data.json`; `.obsidian/community-plugins.json`; `.obsidian/hotkeys.json`.
- bob-plugins: `plugins/bob-navigation-hotkeys/src/640-plugin-notes-and-task-move.js` (`toLineLinkCandidate`), `620-plugin-dash-and-vim-jumps.js` (`\s`), `670-plugin-project-files.js` (`isMarkdownFile`, `openLabeledBodyLink`); `plugins/bob-ledger-tools/src/300-plugin-vim-and-snippets.js`; `plugins/task-status-cycler/src/140-plugin-vim.js`.
- Community: [Image Toolkit](https://community.obsidian.md/plugins/obsidian-image-toolkit), [Click Image to Zoom](https://community.obsidian.md/plugins/sfb-click-image-to-zoom), [Fullscreen Image](https://community.obsidian.md/plugins/fullscreen-image), [Image Peek](https://community.obsidian.md/plugins/image-peek), [Mousewheel Image zoom](https://community.obsidian.md/plugins/mousewheel-image-zoom), [Image Zoom & Drag](https://community.obsidian.md/plugins/diagram-zoom-drag).
