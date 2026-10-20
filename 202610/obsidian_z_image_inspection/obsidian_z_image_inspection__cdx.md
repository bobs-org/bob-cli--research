# Obsidian image inspection with `Z`: native lightbox first, a narrow Bob command for the remaining gap

Independent research by **cdx**, 2026-10-20. No other report or researcher findings from this swarm were consulted. This is a research recommendation, not an implemented change.

**Decision in brief.** The interaction is worthwhile: temporarily enlarge the image you are working with and return to precisely the same place. However, Obsidian already has a native fullscreen image lightbox as of public release 1.13. Start there. The custom work should address keyboard targeting and plain image links, rather than automatically introducing another comprehensive image plugin. Keep `Z` as a configurable Vim-normal-mode binding to a named **Inspect image at cursor** command. For the full requested behavior, favor a small Bob implementation over dependence on an undocumented third-party viewer. Native reuse is preferable only if an actual usable entry point is verified.

**The most consequential finding: native support changed recently.**

Obsidian 1.13 became public on July 30, 2026. Its release notes describe a fullscreen image viewer, clicking an image or its Zoom button, browsing embedded images in the current file, and drag-to-pan. The earlier 1.13.2 notes explicitly describe `Space` opening a selected image in Live Preview. Advice that Obsidian always requires an image zoom plugin is now outdated. [Public 1.13 release](https://obsidian.md/changelog/2026-07-30-desktop-v1.13.4/), [1.13.2 interaction details](https://obsidian.md/changelog/2026-07-14-desktop-v1.13.2/).

There is an important trap: when an image is selected in the **editor**, `+`, `-`, and `0` resize or reset its embedded size. The documented Vim `:image grow`, `:image shrink`, and `:image reset` commands likewise change presentation in the note. They are not documented as temporary lightbox magnification commands. Do not map `Z` to those operations. [Public 1.13 release](https://obsidian.md/changelog/2026-07-30-desktop-v1.13.4/).

The native lightbox establishes that a viewer exists, not that a stable plugin API opens any arbitrary image URL or image link. I inspected Obsidian's public API definitions, version **1.14.4**, commit `9abd9605ce081383674aae1ed111c456edde0688`. They expose the ordinary `Modal`, editor command callbacks, metadata link resolution, resource URLs, and keyboard scopes, but I found no exported image-lightbox class or opener. That is evidence against assuming a public entry point; it is not proof that no internal command exists. [Inspected public definitions](https://github.com/obsidianmd/obsidian-api/blob/9abd9605ce081383674aae1ed111c456edde0688/obsidian.d.ts).

I did not run a live Obsidian desktop session, verify Bryan's installed app version, or inspect the live vault's Vimrc/hotkeys. Thus native `Space` under Bryan's exact Vim configuration, native zoom controls, closing/focus behavior, and any internal command ID remain implementation-time checks. An arbitrary `nmap Z <Space>` is not a verified solution: it may invoke Vim's Space motion, and it says nothing about a plain image link in Source mode.

**Is this a good idea?**

Yes, particularly for diagrams, screenshots, and figures that are deliberately small inline. It removes the interruption of opening an attachment in another tab or application. The value comes from keeping reading position and editing state intact, not from maximizing the image at every opportunity.

The original proposal leaves three consequential ambiguities:

- **What is targeted?** A rendered image, an image source token, a plain link to an image, the first image on the line, and the image under the mouse are different targets. A keyboard command must have a predictable answer when these disagree.
- **What does zoom mean?** Opening a fitted large view, displaying original-size detail, and changing the stored embed width are different operations. Only the first two belong here.
- **Which modes count?** Live Preview, Source mode, Reading view, and an image attachment tab have different selection models. A Vim key alone cannot provide equivalent targeting in all four.

Avoid turning this into a media manager. Rotation, cropping, deleting attachments, OCR, gallery organization, PDF page inspection, and persistent per-image zoom would make a small reading aid substantially harder to maintain. If the recurring need is to compare a figure while writing for several minutes, a side pane or image tab is a better complementary workflow than holding a modal open.

**Requirements I would adjust, explicitly.**

| Original or implicit requirement | Proposed adjustment | Reason |
| --- | --- | --- |
| “Zoom in on images” | Define temporary image inspection: open fitted, allow magnification and pan, close back to the same editing context. | Prevents accidental embed resizing and removes ambiguity. |
| A new `Z` keymap | A named command plus a configurable, normal-mode-only `Z` binding. | Makes the feature discoverable and usable without Vim; isolates keymap conflicts. |
| “Images / inline image links” | Include local wiki embeds, Markdown embeds, and ordinary links whose destinations are images. Include rendered remote images; explicitly label remote-link limitations. | A click-only plugin does not cover a raw link or Source mode. |
| Unspecified targeting | Cursor/selected-image first; a sole image on the current logical line as fallback; otherwise ask the user to place the cursor on the desired image link. | Predictable behavior without another picker in v1. |
| Unspecified placement | A large overlay in the current Obsidian window, with margins and visible close control. No requirement for OS fullscreen. | Keeps desktop window behavior and closing simple. |
| Unspecified exit | `Esc`, `Ctrl+[`, and a visible close button; restore originating editor, caret/selection, scroll, and Vim mode. | A keyboard entry path needs an equally reliable keyboard return. |
| Potential scope across all media | Images only initially; no automatic traversal of arbitrary note links or webpage URLs to discover images. | Controls parser, networking, and maintenance costs. |

The sole-image-on-line fallback should apply only when the caret is in surrounding prose/whitespace. If it is on a non-image link or inside code, do not silently inspect a different image on that line. On two image links with no selected target, do nothing except a short explanation. Do not use “nearest image anywhere in the note”; it is surprising, and a virtualized editor may not render the intended image into the DOM.

`Z` is a reasonable mnemonic for this personal setup, with one qualification: in real Vim, uppercase `Z` prefixes `ZZ` and `ZQ`. Mapping the single key can replace those sequences or create prefix timing behavior. Whether Obsidian's current Vim engine and Bryan's own mappings use them must be checked. Lowercase `z` also has an existing family of commands, so moving to `z` is not automatically safer. If `Z` conflicts, choose a free leader chord after auditing the actual configuration. [Vim's writing-and-quitting commands](https://vimhelp.org/editing.txt.html#ZZ).

**Options and their tradeoffs.**

| Option | What it handles well | Main limitation for this request | Judgment |
| --- | --- | --- | --- |
| Native lightbox | Large temporary view of embedded images, existing mouse/keyboard entry, no extra viewer dependency. | Arbitrary source/plain-link targeting and a callable lightbox API were not established. | First thing to try; retain as normal click behavior. |
| Native opening of attachment / separate pane | Inspection that stays open while editing; little custom UI. | Extra navigation and tab management; remote links behave differently. | Useful complementary action, weaker default for a quick peek. |
| Image Toolkit | Zoom, move, rotation, flip, color inversion, copy, gallery, pinned images. | DOM/click driven; inspected version has no active command for an image at the text cursor. | Too much dependency for this narrow requirement. |
| Image Peek | Quick Look-style interaction, pan/zoom, closing back to thumbnail, page browsing. | Documented keyboard entry is mouse-hover + Space or Canvas selection, not Markdown-caret link resolution. | Good off-the-shelf choice if pointer-driven viewing is acceptable. |
| Small click-to-zoom plugin | Immediate mouse workflow with little configuration. | Does not establish raw-link or Source-mode `Z` support; overlaps core behavior. | Little benefit on current Obsidian unless native viewing has a concrete defect. |
| CSS-only enlargement | Very small initial change for rendered images. | No semantic cursor target, robust focus management, source-link support, or dependable keyboard pan/zoom. | Not an adequate implementation of the full request. |
| Small Bob command + public-API modal | Exact cursor semantics, plain links, predictable key handling and return. | Bob owns parsing, focus, and small viewer maintenance. | Best controllable extension if native entry cannot meet the full contract. |

Image Toolkit was examined from its migrated community repository at commit `334cfa3159a1999121515df6fee8b8496da6c5de`, manifest version **1.4.3**, minimum app **1.8.7**, desktop-only. In `src/main.ts`, `registerCommands()` contains only a commented example; the real opener handles an image click and passes the DOM element to `container.renderContainer`. Consequently “install it and bind its open-at-cursor command to Z” is not supported by the inspected source. Its private objects or synthetic clicks would add a compatibility layer while leaving source-link targeting to us. [Manifest](https://github.com/obsidian-community/obsidian-image-toolkit/blob/334cfa3159a1999121515df6fee8b8496da6c5de/manifest.json), [entry logic](https://github.com/obsidian-community/obsidian-image-toolkit/blob/334cfa3159a1999121515df6fee8b8496da6c5de/src/main.ts).

Image Peek advertises a pleasant alternative: desktop double-click, hover + Space, zoom/pan, Escape/Space dismissal, and Canvas selection support. Its documentation does not establish a command that resolves a Markdown image link at the editing caret. That makes it a pointer-oriented alternative, not a verified replacement for the proposed command. [Author-provided Image Peek listing](https://community.obsidian.md/plugins/image-peek).

Lightbox and Image Zoom advertise click-driven enlargement; the former explicitly describes Reading view and the latter Reading/Live Preview. This is why plugin availability alone does not resolve the keyboard and raw-link requirements. I reviewed these listings, not their source implementations, and do not make a maintenance-quality ranking from download counts. [Lightbox listing](https://community.obsidian.md/plugins/lightbox), [Image Zoom listing](https://community.obsidian.md/plugins/image-zoom).

**What the existing Bob code suggests.**

I inspected `bob-plugins` at commit `ff369873dab5b34c853b4201c6816ef1f362d6b8`. `bob-navigation-hotkeys` is the natural owner for a small editor inspection command: it already registers commands, manages modal interactions, and integrates Vim normal-mode actions. `src/620-plugin-dash-and-vim-jumps.js` demonstrates `defineAction` / `mapCommand` with `{ context: "normal" }`. These Vim bridges are existing compatibility machinery, not a reason to install a global document-level `Z` keydown handler. [Existing Vim integration](https://github.com/bobs-org/bob-plugins/blob/ff369873dab5b34c853b4201c6816ef1f362d6b8/plugins/bob-navigation-hotkeys/src/620-plugin-dash-and-vim-jumps.js).

Do not assume the existing generic link parser is already an image resolver. In `src/680-plugin-link-parse.js`, `parseMarkdownLinkAt` rejects a preceding `!`; `parseWikiLinkAt` rejects embeds unless explicitly allowed. The transclusion parser in `src/180-editor-transactions.js` recognizes additional spans, but serves a different operation and returns marker/range information rather than a complete image target. Reuse safe parsing primitives where appropriate, while giving image inspection its own pure resolver and tests. Do not broaden task/navigation behavior incidentally. [Link parser](https://github.com/bobs-org/bob-plugins/blob/ff369873dab5b34c853b4201c6816ef1f362d6b8/plugins/bob-navigation-hotkeys/src/680-plugin-link-parse.js), [transclusion parser](https://github.com/bobs-org/bob-plugins/blob/ff369873dab5b34c853b4201c6816ef1f362d6b8/plugins/bob-navigation-hotkeys/src/180-editor-transactions.js).

The Bob documentation distinguishes registered commands, custom vault hotkeys, and lower-level editor/Vim handlers. This matters: an app-wide unmodified letter shortcut could steal typing from editors, searches, and modals. The source scan found no image inspection implementation or explicit `Z` mapping in the inspected custom plugin source; this does not prove that `Z` is free in the live vault. I also checked the linked chezmoi checkout and found no Obsidian Vimrc there. [Keyboard-layer documentation](https://github.com/bobs-org/bob-cli/blob/master/docs/reference/plugins/bob-navigation-hotkeys.md).

Vimrc Support offers a conventional command mapping if that is the chosen configuration owner:

```vim
" Proposed command name; this command does not exist yet.
exmap inspectimage obcommand bob-navigation-hotkeys:inspect-image-at-cursor
nmap Z :inspectimage<CR>
```

The `exmap` bridge and trailing `<CR>` follow the plugin's documented mapping approach. Register the named command independently of the binding. Choose either this Vimrc mapping or the existing Bob normal-mode registration mechanism; do not bind it twice. Source selection state must survive command dispatch, especially when an image widget is selected. [Vimrc Support, inspected commit](https://github.com/esm7/obsidian-vimrc-support/blob/1ff5d97afcf3161f202aa460697233d550f6aa3f/README.md).

**Proposed implementation boundary.**

The command should have three separable parts: **identify target → resolve resource → display viewer**. This makes native viewer reuse possible later without rewriting selection semantics.

For target identification, use current editor content and positions. Metadata cache `links`/`embeds` are useful, but may lag a just-edited buffer; do not open an old target merely because the cached span still overlaps the caret. Handle the leading `!`, delimiters, aliases, width suffixes, angle-bracket destinations, escaped characters, and balanced parentheses. Exclude fenced and inline code. A broad regex over the document is not a sufficient Markdown parser.

For local resources, use Obsidian's link resolver with the **source note path**, then `vault.getResourcePath(TFile)`. Do not search all vault files by basename or construct `file://` paths. For an image inside an embedded note, its relative path belongs to that note, not necessarily the outer note. An already selected rendered image can supply its resource identity, but a document-wide “first img” selector is never an acceptable substitute. These public APIs are present in the inspected definitions. [Metadata and vault API definitions](https://github.com/obsidianmd/obsidian-api/blob/9abd9605ce081383674aae1ed111c456edde0688/obsidian.d.ts).

Scope v1 around PNG, JPEG, GIF, WebP, and SVG image targets. These are a proposed support floor, not a claim that Obsidian supports only these formats. Render SVG through an image element rather than injecting arbitrary SVG markup. Use image loading success/failure to report a corrupt or unsupported resource. Width syntax such as `![[figure.png|240]]` is a display hint, not part of the filename; the inspection view should load the original resource. Obsidian's embed documentation specifies these width forms. [Embed syntax](https://help.obsidian.md/embeds).

Rendered HTTP(S) images and explicit Markdown image URLs can reuse their actual image source. For an ordinary external link, support a clearly image-like URL path initially, ignoring query parameters for extension classification; do not fetch every web link to discover whether it is an image. A signed URL without a recognizable extension may work as an explicit `![...](url)` but be unsupported as a plain link in v1. Call this limitation out instead of guessing. Remote images naturally depend on network availability. Viewing should not download a permanent attachment, rewrite a URL, or invoke an external application unexpectedly.

For display, first check the installed Obsidian command catalogue and selected-image behavior. If a real native opener meets the target contract, use one isolated adapter with an explicit supported-version check and integration coverage. Do not invent an `image:zoom` command ID or call undocumented `app.*` methods based on guesswork. Do not momentarily insert an embed into the note to make a plain link openable; even restoring it creates undo and sync side effects.

If no dependable native opener exists, the default full-contract implementation should be a small `Modal` using public APIs. Start with a padded viewport, original image source, fit-to-window, an explicit original-size mode, bounded zoom, and pan. Display a filename/alt label and visible close/reset controls. `+`/`-` zoom **only within the viewer**; `0` fits; `1` shows natural-size display; arrow keys pan. Keep native gallery browsing as a separate existing workflow instead of introducing competing gallery shortcuts in v1. Fit should preserve aspect ratio and avoid automatic enlargement of already small bitmaps; manual zoom can exceed natural size, without pretending it creates new detail.

Modal focus containment and cleanup are essential: consume viewer keys, restore the originating editor state on close, avoid stealing focus if that editor was closed or changed, and cancel pending image-load callbacks after dismissal. Use the active window's document, not an assumed global main window. Obsidian has already shipped a specific pop-out-window image fullscreen fix, so this is a real integration edge to exercise. [1.13.7 release](https://obsidian.md/changelog/2026-08-12-desktop-v1.13.7/).

Keep the implementation in dedicated fragments within `bob-navigation-hotkeys`, not mixed into task lifecycle functions. If this grows into a general-purpose viewer, extract a separate plugin then. Follow the monorepo's fragment build, validation, generated docs, and `bob plugins sync` workflow when implementing; this research changed no plugin source or deployed vault configuration.

**Acceptance checks that decide whether it is ready.**

| Scenario | Expected result |
| --- | --- |
| Caret on `![[img/figure.png|240]]` in Source and Live Preview | Original image appears in a large temporary view; width hint and text unchanged. |
| Caret on `[[img/figure.png|Figure]]` or `[Figure](img/figure.png)` | Same inspection behavior without converting the link into an embed. |
| Two images on one line | Exact image under caret wins; ambiguous surrounding prose produces guidance. |
| Sole image elsewhere on the current line | Fallback opens it, except when caret is on another link or inside code. |
| Spaces, Unicode, escaped parentheses, duplicate basenames, relative paths | Resolves exactly as the source note's link does. |
| Typed URL/path changed immediately before `Z` | New buffer target is used; cached metadata does not open the old image. |
| Missing image, unsupported file, failed remote load | Brief recoverable feedback; no browser launch or note mutation. |
| Image enclosed by a hyperlink | Inspection shows the image and does not accidentally follow the enclosing link. |
| Insert/Visual mode, search box, command palette, unrelated modal | Typing `Z` retains existing behavior; normal-mode binding does not leak. |
| Open, zoom, pan, close repeatedly | Same note, caret/selection, scroll, and Vim mode; no accumulated listeners or pending actions. |
| Pop-out window, narrow pane, large diagram, transparent SVG/GIF | Correct window and fit behavior; visible controls and responsive close. |
| Normal editor `+`/`-` versus viewer `+`/`-` | Editor behavior is unchanged; viewer zoom never writes embed dimensions. |

Unit-test target parsing/resolution and mode guards. Use an actual Obsidian smoke test for selected image widgets, Vim interaction, focus, scrolling, and pop-outs; mocks cannot establish those behaviors. This report is based on source and documentation review, not a passing implementation test suite.

**Recommended solution.**

Keep the idea, but make the requirement **temporary image inspection**, not note resizing. First exercise the built-in lightbox on Bryan's installed Obsidian; it may already satisfy the rendered-image portion with no added viewer. For the complete `Z` plus plain-link workflow, add one **Inspect image at cursor** command to `bob-navigation-hotkeys`, with deterministic source-aware resolution and a configurable Vim-normal-mode `Z` binding. Reuse a native opener only after verifying it exists and meets that contract. On the evidence available now, budget for a small public-API modal as the reliable implementation, while preserving native click behavior. Do not make Image Toolkit, synthetic clicks, a global letter hotkey, or permanent embed resizing the foundation. This provides the desired one-key inspection without committing Bob to a second media-management system.
