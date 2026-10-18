# Obsidian 1.12 → 1.14 Upgrade Review: What Matters For Bryan's Bob Setup

_Researcher: cld · Date: 2026-10-18 · Scope: Obsidian Desktop changelog 1.12.0 → 1.14.4
(public Oct 5, 2026), plus mobile notes, judged against the actual Bob vault, the
`bob-plugins` source, `bob-cli`, and Bob Mac Capture._

---

## TL;DR

- **Your Mac is on Obsidian 1.14.4 (installer 1.14.4), macOS 26.5.** The CLI symlink
  `/usr/local/bin/obsidian -> …/obsidian-cli` dates from **May 28**, so you have had the
  1.12.7+ CLI binary since late May. The CLI is therefore *not* new in this jump. Treat
  everything from **1.13.0 through 1.14.4** as new.
- **The one new feature that drops straight into your vault is the Bases Kanban layout
  plus the Group menu (1.14).** Your `projects.base` and `refs.base` already group by
  `status`. A board view is a few lines of YAML. There are sharp edges, though: for
  refs, and for projects moved to `done`, the `status` property is owned by bob. Details
  in §1.
- **The finding with the most leverage is not in the changelog.** I confirmed that
  **the Obsidian CLI works over SSH from apollo to the Mac's running Obsidian**
  (`ssh mac obsidian version` printed `1.14.4 (installer 1.14.4)`; `plugins:enabled`
  and `dev:errors` both worked). That gives agents on apollo/athena a real-app check
  loop for `bob-plugins` changes. `obsidian reload` / `plugin:reload` could also
  replace the osascript quit-and-relaunch in `scripts/install_all`.
- **The plugin-compatibility risk of the jump looks low.** Electron went 39 → 43 and
  CodeMirror was upgraded twice. Even so, `obsidian dev:errors` on the live Mac reports
  "No errors captured" with all 16 community plugins enabled. None of the breaking
  changes (`--callout-color`, `BaseOption#shouldHide`, `corner-shape`) touch your
  snippets or plugins.
- **Mostly irrelevant to you:** iOS Quick Capture (no iOS device writes to the vault and
  Sync is retired), Mermaid off-by-default (0 Mermaid blocks in the vault), the URI
  confirmation dialog (added in 1.13.0, removed in 1.13.6), RTL, and Sync UI work.

The ranked list is at the end ([§ Ranked list](#ranked-list-what-to-be-aware-of--adopt)).

---

## What I checked about your setup

Every claim below rests on something I read or ran. All of it was read-only.

| Fact | Evidence |
|---|---|
| App/installer version | `ssh mac obsidian version` → `1.14.4 (installer 1.14.4)`; `obsidian-1.14.4.asar` dated Oct 5; `/Applications/Obsidian.app` replaced Oct 2 |
| Prior baseline ≥ 1.12.7 | `/usr/local/bin/obsidian -> /Applications/Obsidian.app/Contents/MacOS/obsidian-cli`, symlink created May 28. The standalone `obsidian-cli` binary shipped with the 1.12.7 installer. |
| CLI enabled | `~/Library/Application Support/obsidian/obsidian.json` has `"cli":true`, `"openSchemes":{"file":true}` |
| macOS | `sw_vers` → 26.5 (relevant to the 1.13 macOS 26 restyle and 1.14 Quick Look) |
| Vault size (Mac) | `obsidian vault info=files` → 8,151 files (6,394 `.md`, 1,442 `.pdf`), ~3.5 GB |
| Core plugins | Bases, Canvas, Daily notes, Templates, Note composer, Outline, Bookmarks, Workspaces, File recovery, Publish on; Sync, Slides, Web viewer, Unique note off |
| Community plugins | dataview 0.5.68, obsidian-tasks-plugin 8.4.0, templater 2.25.1, metadata-menu, obsidian-linter, vimrc-support, relative-line-numbers, note-refactor, mrj-jump-to-link, plus 7 bob plugins (block-id-prompt, bob-articles, bob-ledger-tools, bob-navigation-hotkeys, bob-project-tasks, bob-vim-surround, task-status-cycler) |
| Editor config | `app.json`: `vimMode: true`, `showLineNumber: true`, `promptDelete: false`, `alwaysUpdateLinks: true` |
| Config travels by git | Vault `.gitignore` allows `.obsidian/**/*.json` and `.css`, so `app.json`, `appearance.json`, `hotkeys.json`, and snippets sync across machines. Only the Mac runs the Obsidian app; apollo/athena hold git copies. |
| Bases in use | `projects.base` (grouped by `parent`, status `wip`/`waiting`/`done`/`canceled`), `refs.base` ("🔖 Reading Queue" grouped by `status`), `articles.base`, `podcasts.base`, `eat.base` |
| CLI already used by bob | `bob query --engine obsidian` shells out to `obsidian eval code=…` (`src/native/dataview/obsidian.rs`) |
| URI handlers | bob-navigation-hotkeys registers `obsidian://bob-goto-task` and `obsidian://bob-open-notes`. Bob Mac Capture dispatches both. Ref notes link `highlights://…#page=N` (166 files). |
| Plugin settings tabs | Only `bob-articles` has a `PluginSettingTab` (5 settings). All bob plugins declare `minAppVersion: 1.8.7`. |
| Vim internals used | bob-ledger-tools and bob-vim-surround reach `window.CodeMirrorAdapter.Vim` (`defineAction`, `mapCommand`) |
| Pickers | bob pickers are custom `Modal`s (`FilteredPickerModal`, 44 subclasses) that already handle Ctrl-N/Ctrl-P themselves |
| Not used | 0 Mermaid blocks; 4 files with `$$` math; ~0 real `==highlight==` usage. The legacy `====…` Pomodoro banners stopped in May 2026. No snippet or plugin uses `--callout-color`. 0 non-ASCII filenames. |

---

## Release timeline (Desktop)

| Version | Public date | Headline |
|---|---|---|
| 1.12.4 | Feb 27 | **Obsidian CLI**, Live Preview image resize, delete-attachments prompt |
| 1.12.7 | Mar 23 | Bundled fast `obsidian-cli` binary, TUI `id=` autocompletion |
| **1.13.4** | **Jul 30** | **Settings revamp** (window, search, Vim keys, declarative Settings API), image editing and lightbox, URI and Mermaid guardrails, Electron 43 |
| 1.13.6 | Aug 10 | **URI-approval dialog removed**, settings polish |
| 1.13.7 | Aug 12 | macOS special-character filename fix |
| **1.14.4** | **Oct 5** | **Bases Kanban and Group menu**, **highlight colors**, **open `.md` from outside the vault, Quick Look**, fuzzy-search ranking, input-lag fix, MathJax 4 |

Changelog source pages are listed in [§ Sources](#sources).

---

## Analysis by theme, in your terms

### 1. Bases: Kanban layout, Group menu, collapsible groups (1.14.0–1.14.4) — NEW, directly applicable

**What shipped.** There is a new `type: kanban` view. `groupBy` defines the columns, and
`groupOrder` sets their order and visibility (`null` adds the "None" column). Dragging a
card **writes the grouped frontmatter property** of that note. Grouping by `file.folder`
**moves the file** to the target folder. A column's "+"/"New" button creates a note with
that column's value. The new toolbar **Group** menu reorders, hides, and adds groups in
*any* view, and groups now collapse in table, cards, and list layouts. Cards cannot be
dragged when you group by a formula or by a file property other than `file.folder`.

**Why it fits.** `refs.base` → "🔖 Reading Queue" already does
`groupBy: {property: status}` in a table, and `projects.base` already filters
`status.containsAny("wip", "waiting")`. Both are a kanban board waiting to happen. Even
without kanban, the collapsible groups and Group menu improve the existing table views.

**Where it collides with bob, and how to adopt safely:**

- **Projects board: safe for `wip` ↔ `waiting` only.** Per `docs/projects.md` (Sync
  Rules), `bob projects sync` owns the terminal states. A checked `^prj` sets `done`, a
  `[-]` sets `canceled`, and "an open `^prj` task on a terminal project … reopens it to
  `status: wip`". Dragging a card into a `done` column without closing `^prj` gets
  reverted on the next sync. Restrict the board's columns to the states you author by
  hand:

  ```yaml
  # add to projects.base → views:
    - type: kanban
      name: 🗂️ Project Board
      filters:
        and:
          - status.containsAny("wip", "waiting")
      groupBy:
        property: note.status
        direction: ASC
      groupOrder:
        - wip
        - waiting
      order:
        - formula.title_link      # first property = card title
        - formula.priority_badge
        - formula.tasks
  ```

- **Refs board: treat it as view-only.** Ref `status` is a three-way synced field: PDF
  marker, frontmatter, and the reading-task checkbox (`[ ]` ready, `[*]` next, `[/]` wip,
  `[x]` read, `[-]` abandoned). Per `docs/highlights-ref-sync.md`'s conflict policy, a
  frontmatter-only status change that disagrees with the visible lifecycle task is
  reported as a **conflict**. A drag also sidesteps the sticky-lane gestures that
  `decisions:task-lanes-are-sticky` reserves for raising and releasing Next. A board
  grouped by `note.status` with `groupOrder: [next, wip, ready]` is still a nice
  at-a-glance reading queue. Just don't drag on it; change status through the `^ref`
  task as today.
- **Never group by `file.folder` on refs or area/project notes.** A drag would move the
  note. That breaks the `ref/<ref_type>/` ↔ `lib/<ref_type>/` mirroring that `bob ref`
  assumes, and for tasks it would change residence, which is what Bob's area/project
  semantics are built on.
- **Don't use the column "+"/"New" buttons.** They create a note with only the grouped
  property. Vault notes must carry `parent` (and usually `type`), so these would violate
  the vault convention. Keep creating notes through `bob capture`, `bob ref`, or your
  templates.

Also new in Bases (smaller): `file.linksTo()` counts Canvas embeds (1.12.2). The "+"
button writes correct frontmatter for unresolved links (1.14.0). Date rendering in group
headers is better (1.14.3). A `groupOrder` that is not a list no longer breaks loading
(1.14.4). The table cell menu has Copy/Paste and a single-row file menu (1.11.6/1.12).

### 2. Obsidian CLI: not new to you, but newly actionable from your servers

The CLI arrived in 1.12, and you have had it enabled since May. The changelog's later CLI
work is minor (flatpak fix in 1.13.0). I include it because of something I confirmed
today that the changelog doesn't mention: **the CLI is reachable over SSH from apollo**:

```text
$ ssh mac obsidian version
1.14.4 (installer 1.14.4)
$ ssh mac obsidian plugins:enabled filter=community versions   # all 16 listed
$ ssh mac obsidian dev:errors
No errors captured.
$ ssh mac obsidian dev:console level=error
Error: Debugger not attached. Use "dev:debug on" to start capturing console messages.
```

Three concrete uses, ordered by value:

1. **A real-app check loop for `bob-plugins` agents.** Today plugin changes are checked
   by Node harnesses (`scripts/*-harness.cjs`) against mocks. After `bob plugins sync`
   reaches the Mac (via vault git sync), an agent on apollo could run
   `ssh mac obsidian plugin:reload id=<id>`, then `dev:errors`. With `dev:debug on` it
   can also read `dev:console level=error`. It can check DOM state with `eval` or
   `dev:dom selector=…`, and capture the window with `dev:screenshot path=…`. That catches
   load-time exceptions and CM6/Vim breakage that mocks can't. Caveats: the Mac is
   offline when the lid is closed. This is your live vault, so restrict agents to
   read-only and dev commands. I did **not** test `dev:screenshot` over SSH.
2. **Replace the osascript quit/relaunch in `scripts/install_all`.** It currently uses
   `osascript -e 'application id "md.obsidian" is running'` and then restarts the app.
   The CLI offers `obsidian reload` ("Reload the vault"), `obsidian restart`, and
   per-plugin `obsidian plugin:reload id=<id>`. Prefer `reload` over `plugin:reload` for
   plugins that register Vim mappings through the global
   `CodeMirrorAdapter.Vim.mapCommand/defineAction` (bob-ledger-tools, bob-vim-surround).
   That Vim state lives outside the plugin. I have not verified whether a
   `plugin:reload` leaves stale or duplicate mappings behind, so test before relying on
   it.
3. **File Recovery from scripts.** `obsidian history`, `history:read version=N`, and
   `history:restore` expose File Recovery snapshots, which you have enabled. Snapshots
   can recover an edit lost to a sync race. That is a useful addition to the conflict
   runbook in `docs/vault-git-sync.md`, which today relies on `_conflicts/` copies.

`bob query --engine obsidian` already uses `obsidian eval`. Pointing
`BOB_DATAVIEW_OBSIDIAN_COMMAND` at a `ssh mac obsidian` wrapper would make the live
Dataview oracle usable from apollo. The `code=<javascript>` argument would need careful
remote quoting, so this is speculative. Separately, **Obsidian Headless (`ob`)** is the
headless *Sync/Publish* client, not a headless app. You already used it and retired it
(`docs/obsidian-sync-exclusions.md`), so there is nothing new there.

### 3. Vim and keyboard ergonomics (1.13.x, 1.14.x) — NEW, passive wins

- **Ctrl-N / Ctrl-P navigate every built-in suggestion list on all platforms** (1.13.0):
  `[[` link suggest, quick switcher, command palette, property suggestions. Your bob
  pickers already implement Ctrl-N/P, so native and bob UIs now share one muscle memory.
  `hotkeys.json` has no bare Ctrl+N/Ctrl+P bindings that could conflict. (A small gap:
  `bob-navigation-hotkeys`' successor-picker modal, `206-successor-picker-modal.js`,
  appears to handle only ArrowUp/ArrowDown, not Ctrl-N/P.)
- **Settings are keyboard-navigable "with Vim key bindings"** (1.13). Ctrl/Cmd-F focuses
  settings search, Alt-↑/↓ reorders list items (1.13.1), and Escape closes Settings
  (1.13.5). Settings open in a **separate window by default**. Turn that off at
  Settings → Interface → "Open settings in new window" if the window juggling annoys
  you.
- **Images are keyboard-editable in Live Preview** (1.13). Select an image, then use
  Backspace/Delete, Cmd-C/Cmd-X, `+`/`-` to resize, `0` to reset, Enter to edit, and
  Space to open the lightbox. There are also **Vim Ex commands**: `:image grow`,
  `:image shrink`, `:image reset`, with counts (`:5image grow`).
- **Vim fixes:** numbered-list `dd`/`p` no longer leaves blank or empty numbered items
  (1.14.1), and the "ghost character" over widgets is gone (1.13.2).
- **Editor command fixes** that touch your surround and list habits: "Toggle bold"
  handles a cursor inside bold and partial selections correctly (1.13.2/1.14.0), cursor
  placement with nested markers like `**__x__**` is fixed, and pasting a `- [ ] …` item
  onto a line that already has a marker no longer duplicates it (1.14.0).
- Watch for: in **Source mode**, ↑ on the first line now moves into the inline title
  (1.14.3/1.14.4). It's arrow-key behaviour, so Vim `k` should be unaffected, but I have
  not verified that.

### 4. Open Markdown from outside the vault, Quick Look, "Open with" (1.14.2–1.14.4) — NEW, useful for agent output

**What shipped.** A new **"Open file from outside the vault…"** command (desktop) opens
any `.md` in the current window without importing it. Obsidian now appears in Finder's
**Open with** menu and can be the **default app for `.md`**. **Quick Look** (Space in
Finder) previews Markdown even when Obsidian is closed. Embeds and links resolve
relative to the file's folder, and Outline and Outgoing links work. This needs the
latest installer, which you have (1.14.4 on macOS 26.5).

**Why you'd care.** A lot of what you read is Markdown that deliberately lives
*outside* the vault: SASE research reports like this one, plan files, bob-cli and
bob-plugins docs and READMEs. Quick Look and "Open with → Obsidian" give you rendered
callouts, tables, and Live Preview without copying them into `~/bob`, which would also
trip the `parent`-frontmatter convention. Caveats: wikilinks into the vault won't
resolve from an outside file. Making Obsidian the system default for `.md` would also
capture double-clicks you may want in nvim.

### 5. Reliability and performance fixes for a vault edited from outside Obsidian — awareness

Your vault is written behind Obsidian's back all day by `bob capture` (Mac Capture),
`bob task-status-hooks`, `bob projects sync`, `bob ref scan`, and `bob vault-sync` pulls.
These fixes land squarely on that pattern:

- **1.13.4:** "Fixed a rare race that could leave a file stuck unsaved until restart."
- **1.13.5:** the app waits for configuration files to finish saving on quit. That
  matters because `.obsidian/*.json` is git-synced, and a half-written `hotkeys.json` or
  `app.json` would be committed by the sync service.
- **1.14.0:** fixed "periodic input lag in large vaults from background property
  recomputation". bob-project-tasks continuously rewrites frontmatter counts, and
  metadata-menu and Dataview watch properties, so you are exactly the profile this
  affected.
- **1.14.4:** fixed a metadata-cache memory leak after opening and editing external
  files, and stale property suggestions.
- **1.13.5:** the window now focuses on a vault-open URI. That helps Bob Mac Capture's
  Control-Return landing via `obsidian://bob-open-notes` / `bob-goto-task`.
- Not applicable: 1.13.7's macOS fix for special-character filenames (you have 0
  non-ASCII filenames). 1.14.2's "always fuzzy above 10,000 files" also doesn't apply:
  the Mac vault is 8,151 files, but it's growing (1,442 PDFs), so it will matter later.

**Action:** none required. If you had worked around "Obsidian didn't notice bob's write"
symptoms (for example, by re-opening notes after `bob capture`), re-test without the
workaround.

### 6. Plugin-developer changes, checked against bob-plugins

| Change | Version | Impact on you |
|---|---|---|
| **Declarative Settings API** (`PluginSettingTab.getSettingDefinitions()`, `control: {type, key}`, groups/lists/pages, `disabled`/`visible` predicates, `validate`). Settings search indexes only migrated plugins. The imperative `display()` API stays supported "indefinitely". | 1.13.0, 1.13.1, 1.13.5, 1.14.0 | Only **bob-articles** has a settings tab: 5 settings (`formatOnSave`, `formatOnLeave`, `articleTypeface`, `staleNumberHints`, `bobPath`), i.e. toggle, toggle, dropdown, toggle, text. Migrating is ~30 lines and makes them findable in Settings search. "Path A" requires bumping `minAppVersion` to `1.13.0`. That's fine, since only the Mac runs Obsidian. Low priority. |
| New **`ConfirmationModal`** component | 1.13.0 | Optional: some of your 24 hand-rolled `extends Modal` classes may be plain confirmations. Not worth churning working, tested modals. |
| **Electron 39.8 → 43.7.5**, CodeMirror upgraded (1.13.0, 1.13.1) | 1.13.4–1.14.3 | This is where the real risk would be: CM6 decorations in ledger-tools and project marks, and the `CodeMirrorAdapter.Vim` internals. `dev:errors` shows none, and all plugins are enabled. Smoke-test your Vim mappings (`\p`, `\P`, `\o`, `\O`, `ys`/`cs`/`ds`) once by hand. |
| `--callout-color` must be a valid CSS color, not an RGB triplet (breaking) | 1.13.0 | **No impact.** No snippet or plugin CSS uses it. |
| `BaseOption#shouldHide` no longer receives config (breaking) | 1.12.0 | **No impact.** No bob plugin registers a Bases view. |
| `.HyperMD-math` class on `$$` lines, MathJax 4.1.3 | 1.14.x | Negligible (4 files with `$$`). |
| `appendBinary` on vault/adapter | 1.12.3 | Probably already available on your 1.12.7 baseline. |
| New CSS vars `--tooltip-*`, `--notice-*`, `--hotkey*`, `--tab-inner-*`, `--tab-container-*`; OKLCH base colors | 1.13.0, 1.14.3 | If a snippet or plugin style overrides tooltip, notice, or tab colors, the new vars are cleaner hooks. Base colors moved to OKLCH, so eyeball `task-statuses.css` and `dataview-properties.css` once. |

### 7. Search and navigation (1.14.x) — small daily wins

- **Fuzzy search ranks word-start matches higher** in the quick switcher and link
  suggestions. With ~6.4k notes and many similar stems (dated dailies, `ref/papers/…`),
  this should reduce mis-picks.
- **File Explorer, Bookmarks, Outline, Tags, and Sync search match the full path**, and
  `-term` exclusion hides matching folders and their contents. Filtering with `-done`,
  `-2024`, or `-lib` is now practical in the File Explorer.
- Heading search `[[##` no longer freezes large vaults (1.14.3/1.14.4).
- 1.12-era (probably already familiar): File Explorer Cmd-C/Cmd-V, quick-switcher results
  can be dragged out, Alt-click multi-select.

### 8. Highlight colors (1.14.0) — NEW, low current fit

The syntax is a color emoji right after the opening `==`: `==🔴…==`, `==🟠…==`, `==🟡…==`,
`==🟢…==`, `==🔵…==`, `==🟣…==`. Typing `==` suggests colors, and Live Preview shows a
swatch. It stays plain Markdown, so bob's parsers, nvim, and git see the emoji
literally.

You barely use `==` today. A speculative fit: Highlights.app supports multiple
annotation colors, but `bob ref` renders annotations as `> [!quote]` callouts, and the
current Highlights Markdown sidecars carry no color. Mapping annotation color to
highlight color would need a richer export first. Don't build anything for this now.

### 9. Images (1.12.0, 1.13.2–1.13.4) — moderate

There are 192 tracked images, and `bob ref` copies TextBundle images into ref notes. You
get a **lightbox** (click in Reading mode, Space in Live Preview; arrows move between
images, drag pans, the file name is shown), **corner-drag resizing** (writes `|width`
into the embed), keyboard resize, and Reading-mode support for sized external images
without alt text. The lightbox is the useful part for reading diagram-heavy ref notes.

### 10. Appearance and settings plumbing (1.14.2–1.14.3) — minor

- **Base font size moved out of `appearance.json` into device-local storage.** Since
  `appearance.json` is git-synced, this removes a future cross-device flip-flop. Today
  it's moot, because only the Mac runs Obsidian.
- New **"Increase font size" / "Decrease font size"** commands can be bound to hotkeys.
- Settings → General shows an update notice when a newer *installer* exists. That's
  handy because Quick Look and the CLI binary depend on the installer, not the asar
  auto-update.

### 11. URIs and Bob Mac Capture — awareness only

1.13.0 added a confirmation dialog in front of every `obsidian://` URI, with an
allow-list. **1.13.6 removed it** ("creating even more confusion"). Bob Mac Capture's
`obsidian://bob-goto-task` / `bob-open-notes` flows are therefore unaffected on 1.14.4.
Separately, 1.12.2 added "confirmation before opening files in an external application".
The `"openSchemes":{"file":true}` entry in your `obsidian.json` looks like an approval you
have already given. If clicking a `highlights://…#page=N` link in a ref note ever starts
prompting, approve it once. I did not trigger one to confirm.

---

## Things you can safely skip

- **iOS Quick Capture, Live Activity, widgets, share-sheet Locations (1.14 mobile).** No
  iOS device has ever committed to the vault (hosts: kellys-macbook-pro-local, kellys-mbp,
  macbookpro, apollo, athena), and Sync is retired. Your mobile capture path is Google
  Keep → `bob gkeep pull`. Only revisit this if you put the vault on iOS, which would
  break the "one sync engine" rule unless git is the engine there.
- **Mermaid off by default / one-time banner (1.13).** There are 0 Mermaid blocks in the
  vault. You might see the banner once when opening an outside-vault research report
  that has Mermaid in it (§4).
- **The URI approval dialog.** It was removed in 1.13.6 (§11).
- **RTL workspace flipping, translation and localized-link changes, Sync UI features,
  Slides iframe fix, and the Web viewer Google sign-in fix.**
- **Obsidian Headless (`ob`).** You already used it and retired it along with Sync.
- **The delete-attachments prompt (1.12.0).** You likely already had it. It's still worth
  one deliberate choice, though. Ref notes embed `lib/…/*.mp3`. Choosing "Always delete
  attachments" when deleting a ref note in Obsidian could remove library audio that
  `bob ref` treats as companion files. Prefer "Ask every time" or "Never" under
  Settings → Files & links. I did not verify the default or whether
  `fileManager.trashFile` calls from bob plugins trigger the prompt.

---

## Ranked list: what to be aware of / adopt

1. **Bases Kanban + Group menu + collapsible groups (1.14).** *Adopt.* Add a
   `wip`/`waiting` **Project Board** view to `projects.base` and a **view-only** reading
   board to `refs.base`. Don't drag ref cards, don't group by `file.folder`, and don't use
   column "New" buttons. bob owns the terminal project states, ref status, and note
   creation (§1).
2. **Obsidian CLI over SSH as an agent check loop (1.12 feature, newly actionable).**
   *Adopt in bob-cli and bob-plugins workflows.* `ssh mac obsidian …` works today. Use
   `plugin:reload` / `reload` + `dev:errors` (+ `dev:debug on` / `dev:console`, `eval`,
   `dev:dom`) after `bob plugins sync`. Consider replacing the osascript restart in
   `scripts/install_all` with `obsidian reload` (§2). This is not new in your jump, but
   it's the highest-leverage item here.
3. **Reliability and performance fixes for externally written vaults (1.13.4, 1.13.5,
   1.14.0, 1.14.4).** *Be aware.* These are the stuck-unsaved race, config-save-on-quit
   (your `.obsidian` JSON is git-synced), the property-recompute input lag, and the
   metadata-cache leak. Re-test any workarounds for "Obsidian missed bob's write" (§5).
4. **Vim and keyboard upgrades (1.13–1.14).** *Use.* Ctrl-N/P in all native
   suggestions, Vim-navigable settings, keyboard image editing and `:image grow/shrink/reset`,
   numbered-list paste and toggle-bold fixes. Optionally turn off "Open settings in new
   window", and add Ctrl-N/P to the successor picker for consistency (§3).
5. **Open `.md` from outside the vault + Quick Look + "Open with" (1.14).** *Adopt
   casually.* Read SASE research reports, plans, and repo docs rendered in Obsidian or
   Finder without importing them into `~/bob` (§4).
6. **Plugin-API changes (1.13).** *Mostly be aware.* Smoke-test the Vim mappings and CM6
   decorations once after the Electron 43 / CodeMirror jump. Optionally migrate
   bob-articles' 5 settings to the declarative Settings API so they appear in Settings
   search. No breaking change hits you (§6).
7. **Search improvements (1.14).** *Use.* Word-start fuzzy ranking, full-path matching,
   and `-folder` exclusion in File Explorer, Outline, and Bookmarks search (§7).
8. **Image lightbox and resizing (1.13).** *Use when reading ref notes with figures* (§9).
9. **Per-device font size + font size commands (1.14).** *Minor.* This stops a git-synced
   `appearance.json` from carrying font size between devices. Bind the new commands if
   you like (§10).
10. **Highlight colors `==🟡…==` (1.14).** *Be aware, don't build on it yet.* Little
    current use, and Highlights sidecars carry no color to map (§8).

---

## Open questions / not verified

- Whether `obsidian plugin:reload` cleanly replaces Vim mappings registered via
  `CodeMirrorAdapter.Vim.mapCommand`. If it doesn't, use `obsidian reload` instead.
- Whether `obsidian dev:screenshot` works over SSH from a non-GUI session. Not tested,
  out of respect for what might be on screen.
- The default for the Files & links "delete attachments" setting, and whether
  plugin-initiated `trashFile` calls trigger it.
- Whether `highlights://` links prompt under the 1.12.2 external-app confirmation.
- `dev:errors` captures only since the current app session started, so "No errors
  captured" is a snapshot, not proof of zero regressions.
- Whether 1.13.x ever ran on the Mac between 1.12.7 and 1.14.4. The evidence shows a
  ≥1.12.7 installer by May 28 and 1.14.4 by Oct 5, nothing in between.

## Sources

- Changelog: https://obsidian.md/changelog/ ,
  https://obsidian.md/changelog/page/2/ , https://obsidian.md/changelog/page/3/ ,
  https://obsidian.md/changelog/2026-10-05-desktop-v1.14.4/ ,
  https://obsidian.md/changelog/2026-05-28-desktop-v1.13.0/
- CLI docs: https://obsidian.md/help/cli
- Settings API: https://docs.obsidian.md/Plugins/User+interface/Settings ,
  https://docs.obsidian.md/plugins/guides/migrate-declarative-settings
- Obsidian help source (opened as external repo `gh:obsidianmd/obsidian-help` @
  `08ef563f`, 2026-10-11): `en/Bases/Layouts/Kanban view.md`, `en/Bases/Bases syntax.md`,
  `en/Bases/Views.md`, `en/Editing and formatting/Basic formatting syntax.md` (Highlight
  colors), `en/Files and folders/Manage notes.md` (Open files outside your vault, Quick
  Look), `en/Extending Obsidian/Obsidian URI.md`, `en/Extending Obsidian/Obsidian
  Headless.md`, `en/Obsidian Sync/Headless Sync.md`
- Local evidence: `~/bob/.obsidian/{app,appearance,core-plugins,community-plugins,hotkeys,types}.json`,
  `~/bob/*.base`, vault `.gitignore` and git log; bob-cli `docs/{projects,highlights-ref-sync,plugins,dataview,vault-git-sync,obsidian-sync-exclusions}.md`,
  `src/native/dataview/obsidian.rs`, `scripts/install_all`; bob-plugins `plugins/*/manifest.json`
  and `src/*.js`; Bob Mac Capture `README.md` and `Sources/CaptureCore/ObsidianOpenURL.swift`
- Live read-only checks on the Mac via `ssh mac`: `obsidian version`,
  `obsidian plugins:enabled filter=community versions`, `obsidian dev:errors`,
  `obsidian dev:console level=error`, `obsidian help`, `obsidian vault info=files|size`,
  `obsidian files ext=md|pdf total`, `defaults read …/Info.plist`, `obsidian.json`
