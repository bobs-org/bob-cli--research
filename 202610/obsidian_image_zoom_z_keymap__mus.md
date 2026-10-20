# Zooming Images and Inline Image Links in Obsidian (`Z` Keymap): Research

**Researcher:** mus · **Date:** 2026-10-20 · **Vault/app:** Obsidian desktop, vimMode on

## TL;DR

Yes, build it — but not as a bare `Z` Obsidian hotkey. The right shape is a
cursor-context command ("zoom the image under the cursor") exposed as an
Obsidian command with **no default hotkey**, bound in the vim layer via
`obsidian-vimrc-support` (`nmap`), plus click-to-zoom as a complement. Do not
adopt a community plugin as the whole answer; the cheapest correct core is
~150 lines in `bob-navigation-hotkeys` reusing the overlay pattern proven by
`1spread/image-workflow`. Details and rationale below; recommendation in §7.

## 1. What the vault actually contains (evidence)

Two distinct image reference forms exist in `~/bob`, and the request names both:

- **Embeds, deliberately shrunk:** `![[img/20260717_090951.png|400]]` — task-list
  rows of sized-down screenshots. The `|400` sizing is exactly the pain: the
  note stays scannable, but detail is unreadable without a full-size view.
- **Inline (non-embed) image links:** `[[img/rust_attribute_syntax.png]]`,
  `[[img/pandoc_example_lists.png]]` — plain wiki-links to image files inside
  prose. Today these navigate away to the image file; a zoom should show the
  large version **without leaving the note**.

Corroboration: `bob query -q "LIST WHERE any(file.outlinks,
(o) => icontains(string(o), \"png\"))"` returns dozens of notes across
`2024/` and `2025/` (e.g. `2024/20240815.md`, `2025/20250209_done.md`),
confirming image references are vault-wide, not a corner case.

Environment facts that constrain the design:

- `app.json` has `"vimMode": true`; `obsidian_vimrc.md` maps normal-mode keys
  (`nmap`) through `obsidian-vimrc-support` exmaps. Any solution must work in
  Vim normal mode, not just plain Obsidian key handling.
- `hotkeys.json` currently binds **no** `Z` key — the letter is free at the
  Obsidian-hotkey layer. (It is *not* free at the Vim layer; see §4.)
- Plugin stack already includes `bob-navigation-hotkeys` (the natural home for
  a new navigation-ish command), `obsidian-vimrc-support`, and `mrj-jump-to-link`.

## 2. Native Obsidian behavior today (the baseline to beat)

- **Reading view / Live Preview:** clicking a rendered embedded image opens it
  in a dedicated image pane (navigates away from the note). There is no
  keyboard path to that view and no way back except `app:go-back`.
- **Source mode:** an embed is just text; nothing to "zoom" without resolving
  the link target first.
- **Hover preview (core Page Preview plugin, enabled):** hovering a *link*
  shows a small preview popover — sized to fit, not full-resolution, mouse-only,
  and it does not trigger on embeds in a useful large form.
- **External images** (`![](https://…)`) render inline but have no vault file to
  open; any zoom must work from the rendered `src`/URL, not file resolution.

So the gap is real: no keyboard-driven, stay-in-place, full-size image view
exists natively. A `Z` command fills it.

## 3. Community-plugin landscape (what exists, and why not just install one)

| Plugin | Mechanism | Verdict for this vault |
| --- | --- | --- |
| Image Workflow (`1spread/image-workflow`, succ. `obsidian-image-enlarge`) | Click any image → dark fullscreen overlay; wheel zoom with 100%-snap; copy/download; `Esc`/backdrop dismiss | Closest to desired UX; source studied (`main.ts`, ~1150 lines, click-capture via `registerDomEvent … capture:true`, `IMG_SELECTOR` covering markdown + image leaves). But: mouse-first (no cursor-context command), brings copy/paste machinery Bryan doesn't need, desktop-Electron-only clipboard deps |
| Image Hover Preview (`shin2w/obsidian-hover-preview`) | Hover `![]()`/image links → floating `position:fixed` preview, `pointer-events:none`, Shift+wheel zoom clamped to editor bounds | Nice zero-commitment glance, but hover-only: useless keyboard-side, and "clamped to editor bounds" is the opposite of "nice large version" |
| Mousewheel Image Zoom family | Ctrl/Shift+wheel resizes the inline image (writes `\|width` into the note) | Mutates the note to inspect — wrong trade for a read-only glance |
| CSS snippet (`img:hover { width:100% }` etc.) | Hover-enlarge via `styles.css`/snippet | Zero-code, but hover-only, no keyboard trigger, layout-janky, can't exceed column width meaningfully |

Net: **adopt the overlay pattern, not a plugin.** The Image Workflow overlay
implementation is the reference design to copy (~the `openOverlay` + wheel-zoom
+ `Scope`-based `Esc` handling), while skipping its clipboard/copy scope. Relying
on a third-party plugin would add an external update/review burden to a 150-line
problem and wouldn't provide the vim-layer `Z` binding anyway.

## 4. Critique of the plan as stated ("a new `Z` keymap")

The idea is good; the literal proposal needs four adjustments:

1. **`Z` must not be a bare Obsidian hotkey.** Single-letter hotkeys with no
   modifiers fire while typing in the editor — pressing `z` mid-word would
   trigger zoom. Obsidian hotkeys are global chords, not mode-aware. The `Z`
   binding belongs in the **vim layer** (`nmap Z …` in `obsidian_vimrc.md`),
   which only fires in normal mode — exactly the "desirable, on-demand" semantics
   requested. The plugin itself should register a **hotkey-less command**
   (like most `bob-navigation-hotkeys` commands, which get their chords from
   `hotkeys.json`/vimrc, not `addCommand` defaults).
2. **Bare `Z` collides with Vim's `Z` prefix (`ZZ` save+quit, `ZQ` quit).**
   `vimMode: true` means muscle memory for `ZZ` exists. Mapping bare `Z` in
   normal mode shadows those two-key commands (vim waits on `Z`, then the
   mapping fires instead). Adjustment: pick one of (a) `nmap <Space>z` /
   `nmap gz` (zero conflict, still one-fluid-gesture), or (b) bare `Z` only if
   Bryan explicitly retires `ZZ`/`ZQ` (he uses `:w`-style flows far more than
   `ZZ`, but that is his call — default to (a)). Note `Z` is currently
   unmapped in the vimrc, so either is free.
3. **"Images / inline image links" needs a resolution order, not one behavior.**
   Under-cursor targets rank: (1) wiki embed `![[…]]` → vault file;
   (2) markdown image `![](…)` → vault-relative path or URL; (3) plain wiki-link
   to an image file `[[img/….png]]` → vault file; (4) bare URL to an image →
   remote src; (5) rendered `<img>` under a Reading-view cursor → its `src`.
   One command handling all five (first match wins left-to-right on the cursor
   line) covers embeds, links, and both edit modes. A click handler is the
   natural complement for mouse users, using the same overlay.
4. **Zoom ≠ navigate.** The value proposition over "click the image" is
   *stay-in-place*: overlay dismiss returns cursor and scroll to exactly where
   they were. If the implementation opens the image leaf or external app
   instead, it is barely better than status quo — the overlay (lightbox) form
   is the requirement, not an implementation detail.

Out of scope (say no now): editing/annotation in the overlay (the upstream
TODO for Image Workflow lists mosaic/arrows/crop — explicitly deferred there
too), copy/download buttons (phase 2 at most), persistent zoom level, mobile
support, PDF pages (Bryan's `open-reference-pdf-in-highlights` flow already
covers PDFs — images only).

## 5. Design: the command

**Home:** new fragment in `bob-navigation-hotkeys` (follows the
`src/fragments.json` + `npm run build` + `bob plugins sync` pipeline; never
hand-edit `main.js`). Command id suggestion: `zoom-image-under-cursor`.

- **Trigger resolution (editorCallback):** get cursor line text; scan for image
  references in the §4 priority order; prefer the match containing the cursor
  ch-offset, else first match on the line; `Notice("No image under cursor")`
  when none. In Reading view, fall back to the hovered/clicked `<img>` element.
- **Source resolution:** `metadataCache.getFirstLinkpathDest(linkpath,
  sourcePath)` → `vault.getResourcePath(tfile)` (handles `|400` suffix and
  subpath stripping); remote URLs pass through as `src`. Non-image targets
  (`.md`, `.pdf`) are ignored with a notice — PDFs defer to the existing
  Highlights flow.
- **Overlay:** fixed-position dark backdrop + centered `<img>` at natural size
  (downscaled only to fit viewport), wheel-to-zoom around cursor with a 100%
  snap (copy the constants from Image Workflow: `ZOOM_FACTOR`, snap threshold),
  `+`/`-`/`0` keys, drag-to-pan when zoomed, click-backdrop or `Esc` (via
  `Scope`) to dismiss with focus restored to the editor. Cap effort: this is the
  ~150-line core.
- **Bindings:** no `hotkeys:` default in `addCommand` (vault convention leaves
  chords to `hotkeys.json`/vimrc); add `exmap bob_zoom_image obcommand
  bob-navigation-hotkeys:zoom-image-under-cursor` + `nmap` per §4 decision;
  optionally mirror a `Ctrl/Cmd`-plus key in `hotkeys.json` for non-vim
  fallback (vim is always on here, so this is strictly optional).
- **Click complement (cheap, same overlay):** capture-phase click listener on
  rendered `img` (same selector approach as Image Workflow's `IMG_SELECTOR`),
  `preventDefault`/`stopPropagation` to suppress navigate-away. Include it —
  halves the "how do I…" support cost for mouse moments.

## 6. Edge cases and risks

- **Multiple images on one line** (the `![[img/…]]` task-list rows): cursor-offset
  disambiguation is required, not first-on-line. Test with the actual rows in
  `sase*.md`-style notes.
- **`|size` suffixes and `#^block` subpaths** must be stripped before
  `getFirstLinkpathDest`; unresolvable links get a notice, never a throw.
- **Remote images:** overlay from URL works; offline vaults degrade to a notice.
  No caching in v1.
- **Large screenshots:** natural-size-first with fit-to-viewport clamp; never
  upscale beyond 100% by default (pixel-peeping, not blur).
- **Performance:** overlay creates DOM on demand, zero per-note cost; no vault
  scan, no cache invalidation — unlike hover-preview's preload walk.
- **Sync/deploy:** standard `bob plugins sync` flow; no `data.json` settings in
  v1 (zoom factor constant), so nothing to migrate later.
- **What could still go wrong:** vimrc-support `nmap` timing (two-key `gz`
  vs bare `Z` — verify `ZZ` still works after binding); Reading-view cursor
  mapping (CM6 editor vs rendered DOM — the click path covers Reading, the
  command covers editing; document which works where).

## 7. Recommended solution

1. **Implement `zoom-image-under-cursor` as a new fragment in
   `bob-navigation-hotkeys`** (~150 lines: resolver + overlay + command
   registration), reusing the Image Workflow overlay interaction design
   (backdrop/Esc dismiss, wheel zoom with 100% snap, drag-pan) without its
   clipboard scope. Include the capture-phase click-to-zoom listener sharing
   the same overlay.
2. **Bind it in the vim layer, not as an Obsidian chord:** `exmap` +
   `nmap <Space>z` (recommended; zero Vim conflict) — or bare `Z` only with
   Bryan's explicit sign-off retiring `ZZ`/`ZQ`. No `hotkeys:` default in code.
3. **Handle all five target forms** in §4's priority order, with notices (never
   navigation) for non-images and unresolvable links.
4. **Defer:** overlay editing/annotation, copy/download buttons, settings UI,
   mobile, PDFs.

Why this over the alternatives: it is keyboard-first (matches a vim-driven
review-walk workflow), stay-in-place (the actual gap vs. click-to-open),
zero-dependency (no third-party plugin to audit/update), and sized to the
problem (one fragment, one vimrc line, standard sync). Total estimate: one
focused session to implement + test against the real `|400` rows, plus Bryan's
one-line vimrc preference (`<Space>z` vs `Z`).

## Sources inspected

- `bob-navigation-hotkeys` fragments (`490-plugin-lifecycle.js` command/hotkey
  conventions; `620-plugin-dash-and-vim-jumps.js` Vim bridging) and
  `obsidian_vimrc.md` (`nmap`/`exmap` patterns) via the linked `bob-plugins`
  checkout; `~/bob/.obsidian/hotkeys.json` (no `Z` bound), `app.json`
  (`vimMode: true`), `community-plugins.json`.
- External: `gh:1spread/obsidian-image-enlarge` (`main.ts` overlay, `README.md`,
  `TODO.md` — opened via `sase repo open`, read as checkout); 
- `gh:shin2w/obsidian-hover-preview` (`README.md` — hover design limits).
- Vault usage via `bob query` Dataview outlink scan corroborated by direct
  embed-form sampling.
