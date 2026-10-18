# Obsidian 1.12→1.14 for Bob on the MacBook

**Researcher:** `research.23.grk`
**Date:** 2026-10-18
**Question:** Which changelog items in the jump from Obsidian ~1.12 to 1.14 are worth adopting in Bryan's Bob vault, plugins, and Mac capture setup?
**Current install (inspected):** Obsidian **1.14.4** at `/Applications/Obsidian.app` on the MacBook (`mac` / `kellys-macbook-pro`). Bundle mtime 2026-10-02 12:51. The installer includes `ObsidianQuickLook.appex` and registers Markdown, Canvas, Base, and PDF document types.

## How this was ranked

The changelog is written for a generic vault. Bob is not that vault.

Live evidence used for ranking:

- Vault `~/bob/`: **6,396** Markdown files (large enough to hit every "large vault" performance note).
- Core plugins: Bases **on**, Canvas on, Sync **off**, Web viewer off, Slash command off, Note composer on, Outline / File explorer / Quick switcher / Bookmarks on.
- Six Bases files already in daily use: `refs.base`, `projects.base`, `articles.base`, `eat.base`, `podcasts.base`, plus leftover `Untitled.base`.
- Editor: Vim mode, `obsidian-vimrc-support`, relative line numbers, `alwaysUpdateLinks: true`.
- Community stack: Dataview, Tasks, Templater, Linter, Jump to Link (`Ctrl+L`), Metadata Menu, plus the `bob-*` plugins.
- Capture path: Bob Mac Capture → one `bob capture` call → default `mac_inbox.md`. Phone drain is already `gkeep_inbox.md`.
- Sync path: `bob vault-sync` (git). Obsidian Sync is retired. `appearance.json` and plugin lists are vault-tracked.
- Task model: checkbox `#task` lines with sticky Next/Pending lanes, derived Blocked, `]s` review walk, Pomodoro ledger Task Links. Status is **not** a per-file kanban field.
- Project `status:` frontmatter is written by `bob projects sync` from the `^prj` checkbox.
- Reference `status:` (`ready` / `next` / `wip` / `read` / `abandoned` / `legacy`) is a three-way contract among frontmatter, the PDF marker, and the `^ref` task (`docs/highlights-ref-sync.md`).
- Custom protocol handlers: `obsidian://bob-goto-task` and `obsidian://bob-open-notes` (Bob Mac Capture `/` picker and multi-note open).
- CSS snippets: `task-statuses`, `dataview-properties`, `inline-code`. None set `--callout-color`.
- Math: 4 notes with `$$`. Mermaid fenced blocks: **0** in the vault Markdown.
- iOS is in the picture only as a renderer for task-status glyphs (`docs/task-tag-marks.md`, `docs/projects.md`). Capture grammar does not live on iOS.

Previous version could not be read off the app bundle. Bryan's recollection is 1.12 → 1.14. That is treated as a **two-release jump**: everything in public 1.13 (2026-07-30, last patch 1.13.7 on 2026-08-12) plus public 1.14 (2026-10-05 = 1.14.4). Templater 2.25.1, Linter 1.33.0, and Jump to Link 0.6.2 now declare `minAppVersion: 1.13.0`, which is also consistent with a stay on 1.13 and a later plugin update. The ranked list therefore tags each item **1.14** (definite) or **1.13** (only new if 1.12 was the last public stay).

Primary sources: [Obsidian Changelog](https://obsidian.md/changelog/), the 1.12 / 1.13 / 1.14 desktop pages linked from it, [Basic formatting syntax § Highlight colors](https://obsidian.md/help/Editing+and+formatting/Basic+formatting+syntax), [Bases kanban](https://obsidian.md/help/bases/views/kanban), [Obsidian CLI](https://obsidian.md/help/cli), and the [declarative settings migration guide](https://docs.obsidian.md/plugins/guides/migrate-declarative-settings).

## Version map

| Public desktop | Date | Headline |
| --- | --- | --- |
| [1.12](https://obsidian.md/changelog/2026-02-27-desktop-v1.12.4/) (1.12.4; last patch [1.12.7](https://obsidian.md/changelog/2026-03-23-desktop-v1.12.7/) 2026-03-23) | 2026-02-27 | Obsidian CLI, Live Preview image drag-resize, attachment cleanup prompt, Bases search toolbar |
| [1.13](https://obsidian.md/changelog/2026-07-30-desktop-v1.13.4/) (1.13.4; last patch [1.13.7](https://obsidian.md/changelog/2026-08-12-desktop-v1.13.7/) 2026-08-12) | 2026-07-30 | Searchable Settings window, image lightbox + Vim `:image`, mermaid opt-in banner, `--callout-color` CSS break, Electron 43.1.1 installer |
| [1.14](https://obsidian.md/changelog/2026-10-05-desktop-v1.14.4/) (1.14.4 public) | 2026-10-05 | Open Markdown outside the vault, macOS Quick Look, Bases kanban + Group menu, highlight colors, large-vault input-lag fix, Electron 43.7.5 installer |

Catalyst 1.14.4 desktop landed 2026-10-01; the Mac bundle is dated 2026-10-02, so this install is the 1.14.4 app with the Quick Look installer already present. In-app update alone would not have shipped `ObsidianQuickLook.appex`.

## 1.14 — what actually moves the needle

### 1. Large-vault typing and search (silent, already on)

[1.14.0 / public 1.14.4](https://obsidian.md/changelog/2026-10-05-desktop-v1.14.4/) fixed periodic input lag caused by properties recomputing in the background, frozen `[[##` heading search, and slow fuzzy matching in the Quick switcher.

This vault is property-heavy: Tasks statuses, Dataview inline fields, Metadata Menu, Bases formulas, `parent` / `type` / `status` frontmatter on almost every note, plus bob-plugin work that reads the same cache. A 6k-note vault with that metadata load is exactly the lag pattern. No setting to flip. Worth noticing so a "Obsidian feels snappier" impression is attributed correctly, and so a regression after the next plugin update is easier to bisect.

Related 1.14.2 change: link suggestions and the Quick switcher keep fuzzy matching above 10,000 files. This vault is still under that cap (~6.4k), so the algorithm was already fuzzy; the **ranking** change still applies: matches whose letters start words rank higher.

### 2. Collapsible groups in the Bases Bryan already has

1.14 adds collapsible groups in **table, cards, and list** layouts, plus a toolbar **Group** menu to pick the grouping property, reorder, hide, and add groups by hand. This is the highest-leverage 1.14 UI change that needs no new file type and no new workflow.

Current grouping already in the vault:

| Base | Existing `groupBy` |
| --- | --- |
| `eat.base` | `formula.cuisine` (All / Favorites / Gallery), `formula.town` |
| `podcasts.base` | `formula.topic`, `formula.subscription` |
| `projects.base` | `parent`, `status` |
| `refs.base` | `status`, `parent` |

Folding empty or stale groups (canceled projects, unsubscribed podcasts, abandoned refs) is the first thing to try. Embedded kanban height is no longer fixed (1.14.3), which matters if a Base is ever transcluded into an area note.

### 3. File Explorer / Bookmarks / Outline / Tags path search

Search in those views now matches the **full path**, keeps children of a matching folder visible, hides empty groups, and treats `-Archive` as "hide this folder and everything in it."

Bob's tree is path-semantic: `ref/papers/`, `ref/blogs/`, `done/`, `_conflicts/`, area notes at the root, daily notes under `2026/`. File Explorer search that only matched the basename was weak here. Useful queries to try: `ref/papers`, `-done`, `-_conflicts`, `202610`. Bookmarks search got the same treatment; Bookmarks also gained search itself in 1.13.

File Explorer drag-near-edge autoscroll (1.14) is minor next to `Ctrl+Shift+M` task moves, and still nice when dragging a Base row into a folder (that drag-from-Base-to-explorer path landed in 1.13.2).

### 4. macOS Quick Look and "Open file from outside the vault"

Public 1.14's other headline. The Mac installer already has the Quick Look appex, so Finder **Space** on `.md` / `.base` / `.canvas` should preview without launching Obsidian. New document icons for those extensions come with the same installer.

The command is **Open file from outside the vault…**. The file opens in the current window. Outline and Outgoing links work on it (1.14.4). Image embeds and local links resolve relative to **that file's folder**. A metadata-cache leak after opening external files was fixed in 1.14.4.

This is useful for files that are Markdown and **not** vault notes: SASE research reports, `bob-cli` / `bob-plugins` READMEs, chezmoi-managed Markdown, agent transcripts. It is a viewer/editor for a single file, not a second vault.

Constraints that match this setup:

- `alwaysUpdateLinks` is on. Treat external files as read-mostly until it is clear Obsidian will not rewrite their wikilinks.
- `obsidian://bob-goto-task` refuses paths outside the vault (plugin Notice: "is outside this vault"). External tabs will not participate in Go To / capture landing.
- Making Obsidian the OS default for `.md` would intercept git, editor, and agent files. Leave the default handler as it is; use **Open with → Obsidian** when wanted.
- `lit_review/` and `xlib/` are gitignored **inside** the vault, so they are already visible to Obsidian if they sit under `~/bob/`. External-open does not change that.

`Settings → General` now shows a notice when a newer installer is available. Worth a glance after future in-app updates, because Quick Look and Open-with live in the installer, not in `app.asar`.

### 5. Bases kanban — useful on some Bases, harmful on others

Kanban is a layout over **files**, grouped by a property. Dragging a card writes that property (or moves the file, when grouped by `file.folder`). 1.14.2 added folder-column moves, create-in-column-to-folder, and error feedback for invalid properties / missing folders.

Mapping onto Bob's Bases:

**`eat.base` and `podcasts.base` — best first kanban.** `status` here is `liked` / `not_liked` and `subscribed` / `unsubscribed`. Nothing in bob-cli reconciles those fields from a checkbox. A cuisine-column or subscribed/unsubscribed board is a pure UI upgrade on data Bryan already maintains.

**`refs.base` Reading Queue — strong view, careful drag.** The queue already filters `next` / `wip` / `ready` and groups by `status`. A kanban with those three columns plus `read` / `abandoned` is the board the table is pretending to be. Dragging **writes frontmatter `status`**. Highlights ref-sync treats frontmatter status as a real side of a three-way merge with the PDF marker and the `^ref` task (`[ ]`→ready, `[*]`→next, `[/]`→wip, `[x]`→read, `[-]`→abandoned). A drag to `read` that leaves the PDF task open will conflict on the next `bob ref` sync/`scan`. Use kanban as the Reading Queue **view**; change lifecycle with the `^ref` checkbox / existing gestures, or drag only when a sync run is about to follow.

**`projects.base` — keep as tables.** `bob projects sync` sets `status: done` / `canceled` / `wip` from the `^prj` checkbox. A kanban drag would write frontmatter and leave `^prj` stale until the next sync, which then overwrites or fights the drag. Group-collapse on the existing status/parent tables is the 1.14 win here.

**GTD tasks — kanban cannot replace `]s`.** Native kanban cards are notes. Bob's Ready / Next / Pending / Blocked / ROTTEN / TICKLER pool is checkbox lines inside area and project notes, with Today coming from the Pomodoro ledger. There is no Bases grouping property that is the task lane. Leave the walk, Task Card (`Ctrl+Shift+P`), and ledger as the task UI.

### 6. Highlight colors — optional, for prose, in emoji-in-`==` form

Syntax (from [help](https://obsidian.md/help/Editing+and+formatting/Basic+formatting+syntax)):

```text
==🔴Important==
==🟠Follow up==
==🟡Remember this==
==🟢Completed==
==🔵Reference==
==🟣Idea==
```

Typing `==` suggests colors. Live Preview shows a swatch when the cursor is inside a **colored** highlight (a 1.14.4 quirk: the swatch is missing on plain `==text==`; reported on the forum 2026-10-11). The formatting menu and dedicated highlight-color commands exist; those commands are the Vim-friendly path.

This is portable Markdown (emoji inside `==`), so git sync is fine. It does **not** replace `task-statuses.css`, which colors `[/]` / `[*]` / `[?]` / `[-]` checkboxes. Mixing the two as a second status system would split the GTD model.

Best fit: article notes (`bob-articles`), lit notes, meeting notes, where a colored mark is cheaper than a task. Linter has almost every body-text rule disabled, so it is unlikely to strip the emoji. PDF Highlights intake remains the Highlights app → `bob ref` path; these colors do not flow into PDFs.

### 7. Editor and Vim fixes that match existing muscle memory

Already on, no adoption step:

- Pasting a list item onto a line that already has `- [ ]` no longer duplicates the marker. Directly relevant to capture/task editing.
- Vim: deleting and pasting a numbered list item no longer inserts blank/empty numbered items.
- macOS `Option-Shift-↑/↓` in long paragraphs no longer resets scroll / corrupts the selection.
- Inline formatting commands (Toggle bold, etc.) extend over the rest of the line instead of getting stuck on a half-wrapped mark.
- Property suggestions no longer accept an **old** query on Enter. That used to be a footgun anywhere Enter confirms a link (Task Card, Metadata Menu, Bases filters).
- Source mode `↑` on line 1 moves into the inline title, matching Live Preview.

### 8. Font size is now per device

"Increase font size" / "Decrease font size" commands. Base font size left `appearance.json` and now lives in device local storage, so it no longer rides Obsidian Sync — and, more importantly here, no longer rides **git vault-sync** either. Mac vs any other machine can keep different sizes without dirtying `appearance.json`. That is the right default for this sync engine.

### 9. iOS Quick Capture (1.14 mobile) — parallel inbox, not a Bob capture

On iOS 26, Quick Capture writes from Lock Screen / Control Center / widgets / Shortcuts without loading the vault, with Locations (new note, daily note, bookmarked note, chosen note) and templates.

Bob capture is a grammar: tasks, routes, `=x` Pomodoros, `@` / `*` / `&` links, all-or-nothing writes, live preview via `bob capture --dry-run`. iOS Quick Capture has none of that. A Location pointed at `mac_inbox.md` would still create **notes or daily-note appends**, not capture items.

The phone already drains through Google Keep → `gkeep_inbox.md`. Adding Quick Capture creates a third inbox with a weaker contract. The 1.14 mobile accessibility / widget work is fine to enjoy; the capture feature is the wrong intake for this system.

URI confirmation dialogs appeared in 1.13.0 and were **removed** in 1.13.6. On 1.14, `obsidian://bob-goto-task` and `obsidian://bob-open-notes` should fire as before, without an allow-list prompt.

## 1.13 — the skipped-release package

If the last public stay was 1.12.x, these are new. If the Mac was already on 1.13.7, treat this section as already landed.

### Searchable Settings window, with Vim keys

Settings open in a pop-out window (toggle: **Settings → Interface → Open settings in new window**). Search covers core settings and core plugins. Arrow keys, Enter, `Cmd-F` to re-focus search, and **Vim bindings** in that window. Escape closes it (1.13.5). Fullscreen Obsidian no longer spawns a second fullscreen settings window (1.13.5). 1.14 made closing pop-out windows much faster, which is the follow-on if settings-in-a-window felt laggy.

Community plugins appear in that search only after they migrate to the [declarative Settings API](https://docs.obsidian.md/plugins/guides/migrate-declarative-settings). In `bob-plugins`, **only `bob-articles`** registers a `PluginSettingTab`. The other bob plugins are keymap/behavior plugins with little or no settings UI. Migrating `bob-articles` is a developer nicety, not a daily-driver need.

Debug gift: Restricted Mode can be exited **without** re-enabling every plugin. That is the right tool when a bob-plugin change is suspected.

1.13.5 also waits for configuration files to finish saving on quit. For a git-synced `.obsidian/`, that is a real corruption hedge (`community-plugins.json` mtime on this vault is 2026-10-16; hotkeys 2026-10-17).

### Image lightbox and Vim `:image`

Click (reading) or Space (Live Preview, image selected) opens a fullscreen lightbox; arrow keys walk images in the file; click-drag pans. Selected image: `+` / `-` resize, `0` reset, Enter to edit, Tab to edit size. Vim:

```text
:image grow
:image shrink
:image reset
:5image grow
```

`obsidian_vimrc.md` already bridges a lot of `obcommand`s. Adding `:image` maps is optional; the Ex commands work without a vimrc change. Fits article notes and any note that embeds screenshots. PDF reading stays in Highlights (`Cmd+Enter` → `bob-navigation-hotkeys:open-reference-pdf-in-highlights`).

1.13 Live Preview also made images keyboard-selectable (Backspace/Delete removes the embed, `Cmd-C`/`Cmd-X` copy/cut) and stopped auto-expanding the filename. Changelog says this supports Vim out of the box.

### `Ctrl-N` / `Ctrl-P` in every suggestion list

These now work on all platforms, including macOS. That is the Vim completion habit in Quick switcher, command palette, and `[[` suggestions. On this machine `Ctrl+N` is also **create project note** via `bob-navigation-hotkeys` when not inside a suggestion list — same chord, different context. Worth a five-second check that project-note creation still wins when the palette is closed.

### macOS 26 control styling, special-character filenames, CSS snippets

- 1.13 restyled buttons/inputs toward macOS 26 defaults.
- 1.13.7: files whose names contain special characters sometimes vanished from the vault on macOS. If anything "came back" after this upgrade, that is why.
- Disabling a CSS snippet now actually removes it from pop-out windows. Relevant to `task-statuses.css` while Settings is open in a window.
- 1.13.6: wait-for-config-on-quit (already noted) and "Undo close tab" restores the correct tab group and stops eating the New Tab page.

### Breaking / one-time 1.13 items

**`--callout-color` now wants a full CSS color** (`#ff0000` or `rgb(255,0,0)`), not an `R,G,B` triplet. Vault snippets do not set it. Theme/plugin CSS that still uses the triplet will render callouts wrong. Base colors moved to OKLCH; the three snippets use `color-mix(in srgb, var(--color-…))` and should keep working, but task-status tints are the place to look if a color shifts.

**Mermaid is off until a one-time banner is accepted** (1.13.0); 1.13.1 renders immediately after allow, without reload. This vault currently has zero ` ```mermaid ` fences, so the banner is a one-click no-op unless `bob ref create` mermaid figures land later.

**URI action confirmation** (1.13.0) was pulled in 1.13.6. 1.14 is back to quiet protocol handlers — good for Bob Mac Capture's Go To picker.

**Installer Electron 43.1.1** (1.13 public). 1.14 then moved the installer to **Electron 43.7.5**. The Mac bundle is already on a Chromium 150 Electron framework with Quick Look, so both installer generations appear to have been applied.

**CodeMirror upgrade** (1.13). Vimrc, `bob-vim-surround`, relative line numbers, and Jump to Link all sit on the editor. They are loading on 1.14.4; any new Vim widget glitch would show up as the "ghost character on widgets" bug that 1.13.2 already fixed.

### 1.12 leftovers, only if the jump started before 1.12.7

Public 1.12 already shipped Obsidian CLI (bob-cli uses it for `bob query --engine obsidian` and Linux `obsidian restart`), Live Preview drag-resize for images, and the attachment-delete prompt. **1.12.7** replaced the slow "call the Electron binary" CLI with a bundled CLI binary and fixed the macOS socket path (dotfile). If CLI invocations on the Mac still felt sluggish before this upgrade, reinstall-from-website (already done, given Quick Look) is what actually switched that binary.

## Developer / plugin notes (bob-plugins)

- New CSS variables: `--tooltip-`, `--notice-`, `--hotkey`, `--tab-inner-`, `--tab-container-`. Optional polish for Task Card / Go To landing cue; not required.
- `SettingDefinitionItem#id` and the declarative settings API: only `bob-articles` has a settings tab.
- Math blocks: each `$$` line now has `.HyperMD-math`. Irrelevant at 4 math notes.
- Math renderer: 1.14.0 briefly used Temml; 1.14.1 / public 1.14.4 use **MathJax 4.1.3**. Fine.
- `minAppVersion: 1.13.0` on Templater, Linter, Jump to Link is why those three would have refused to load on a true 1.12 stay. They are compatible with the current 1.14.4.

## Ranked list — be aware of / consider adopting

Rank is "value for this Mac + this vault," highest first. Tags: **1.14** = new even if 1.13 was already installed; **1.13** = new only on a 1.12 stay.

1. **Feel the large-vault editor/search fix (1.14).** Property recompute lag, `[[##` freeze, faster fuzzy switcher. No setting. This is the upgrade's biggest gift to a 6k-note Tasks+Dataview+Bases vault.

2. **Collapse groups in existing Bases tables (1.14).** `eat.base`, `podcasts.base`, `projects.base`, `refs.base` already `groupBy`. Use the new Group menu to hide empty columns/groups. Zero workflow change.

3. **File Explorer / Bookmarks / Outline path search (1.14).** Try `ref/papers`, `-done`, `-_conflicts`. Full-path match plus `-folder` exclusion is built for this tree.

4. **Quick Look for `.md` / `.base` / `.canvas` in Finder (1.14, installer already present).** Spacebar preview of research reports and vault notes with Obsidian closed. Confirm once; then it is free.

5. **Open file from outside the vault… (1.14).** Point it at SASE research Markdown and repo READMEs. Keep it off the OS default-for-`.md` role. Treat those tabs as outside Go To / capture / `alwaysUpdateLinks` until proven otherwise.

6. **Quick switcher word-start ranking (1.14).** Same command, better order. Daily.

7. **Kanban view on `eat.base` / `podcasts.base` (1.14).** Low coupling to bob-cli. Good place to learn the Group menu, hide-column, and drag-to-edge scroll.

8. **`refs.base` Reading Queue as a kanban *view* (1.14).** Columns `next` / `wip` / `ready` match the table Bryan already has. Lifecycle changes still belong on the `^ref` task so highlights-ref-sync stays consistent; a drag is a frontmatter write that can conflict with the PDF task.

9. **Settings search + Vim navigation in the settings window (1.13).** `Cmd-,` then search, `j`/`k` or arrows, Escape to close. Restricted Mode "leave plugins off" is the debug mode this plugin set needs.

10. **Vim `:image grow|shrink|reset` and the image lightbox (1.13).** Optional vimrc maps. Useful in article/screenshot notes. PDFs stay in Highlights.

11. **`Ctrl-N` / `Ctrl-P` in suggestion lists on macOS (1.13).** Confirm it does not steal `Ctrl+N` create-project-note when the palette is closed.

12. **Per-device font size commands (1.14).** Bind Increase/Decrease font size if the Mac wants a different size than git-synced `appearance.json` would have allowed.

13. **Highlight colors for prose / lit / article notes (1.14).** `==🔵…==` etc., or the highlight-color commands from Vim. Leave task lanes on checkbox CSS.

14. **List-paste and Vim numbered-list paste fixes (1.14).** Already active; they match capture/task editing.

15. **Quit-waits-for-config-save (1.13.5) and macOS special-character filenames (1.13.7).** Awareness: git-synced `.obsidian/` is safer; missing files with odd names may reappear.

16. **Obsidian CLI bundled binary (1.12.7, needs installer).** Already implied by this 1.14 installer. `bob query --engine obsidian` and Linux `obsidian restart` are the consumers.

17. **Declarative settings for `bob-articles` (1.13 API).** Only if Settings search for that plugin starts to matter. The other bob plugins have no settings tab to migrate.

18. **iOS Quick Capture Locations (1.14 mobile).** Fine as a toy. Intake for tasks remains Bob Mac Capture and Keep → `gkeep_inbox.md`.

### Leave as they are

- **`projects.base` status** stays a table (or collapsed groups). `bob projects sync` owns `status:` via `^prj`.
- **Task lanes / `]s` / Pomodoro ledger / Task Card** stay the GTD UI. Bases kanban has no model for checkbox tasks.
- **Obsidian Sync** stays off. Git `bob vault-sync` remains the only sync engine (see vault memory).
- **OS default app for Markdown** stays with the current handler. Obsidian is available via Open With.
- **Callout CSS** needs no snippet edit (`--callout-color` unused).
- **Custom `obsidian://bob-*` URIs** need no allow-list on 1.14 (the 1.13.0 prompt was removed in 1.13.6).

## Suggested first hour on the MacBook

1. In Finder, Space on a `~/bob/*.md` and on a `sase/repos/research/202610/*.md` to confirm Quick Look.
2. Command palette: **Open file from outside the vault…** on a bob-cli `README.md`. Close without saving.
3. Open `refs.base` → Group menu → collapse Archive groups; optionally duplicate the Reading Queue view as type `kanban` without dragging cards yet.
4. File Explorer search: `ref/papers` and `-done`.
5. Open Settings (`Cmd-,`), type `vim`, confirm search + Escape-to-close.
6. In a note with an image, `v` over the image (Vim) and try `:image grow`.
7. Type `==` in a throwaway line and pick 🔵; confirm the swatch on the colored mark.

## Sources

- Changelog index: https://obsidian.md/changelog/
- Desktop 1.14 public: https://obsidian.md/changelog/2026-10-05-desktop-v1.14.4/
- Desktop 1.14.0–1.14.3 catalyst: https://obsidian.md/changelog/2026-09-02-desktop-v1.14.0/ and siblings
- Desktop 1.13 public: https://obsidian.md/changelog/2026-07-30-desktop-v1.13.4/
- Desktop 1.13.0–1.13.7: https://obsidian.md/changelog/2026-05-28-desktop-v1.13.0/ through https://obsidian.md/changelog/2026-08-12-desktop-v1.13.7/
- Desktop 1.12 public / 1.12.7: https://obsidian.md/changelog/2026-02-27-desktop-v1.12.4/ , https://obsidian.md/changelog/2026-03-23-desktop-v1.12.7/
- Highlight colors: https://obsidian.md/help/Editing+and+formatting/Basic+formatting+syntax
- Bases kanban: https://obsidian.md/help/bases/views/kanban
- CLI: https://obsidian.md/help/cli
- Settings API: https://docs.obsidian.md/plugins/guides/migrate-declarative-settings
- Live Mac install: `/Applications/Obsidian.app` 1.14.4, `ObsidianQuickLook.appex`, document types Markdown/Canvas/Base/PDF
- Live vault: `~/bob/.obsidian/{app,appearance,core-plugins,community-plugins,hotkeys}.json`, `~/bob/*.base`, `~/bob/obsidian_vimrc.md`, plugin manifests
- Bob contracts: `docs/projects.md`, `docs/highlights-ref-sync.md`, `docs/capture.md`, bob-plugins README URI section
