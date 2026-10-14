# Bob Refs `⌃Y` Copy Card: Consolidated Design Recommendation

> **Research query:** What is the best way to add a new `<ctrl+y>` keymap to the
> bob-mac-capture app's ref panel that opens a menu where a single keypress selects what
> to copy to the clipboard, with creative options (such as the marker note's ID value or
> one of the notes/highlights) drawn from the properties of a reference note or PDF a user
> might want to copy, designed to be intuitive, reliable, and beautiful? Critique the plan
> (is it a good idea, or would you take a different approach?), clearly call out any
> justified requirement adjustments, and end with a recommended solution.

![Infographic of the proposed Ctrl+Y Copy Card for Bob Mac Capture: the four-step flow (select a reference, Ctrl+Y opens the card, press a letter or digit, Refs closes and a HUD confirms the copy), the copy catalog grouped into identity, sources, files and handles, and your notes, the marker-ID and note-count measurements, the reliability rules, and the bob-cli, RefsCore, and app build order](refs_panel_ctrl_y_copy_card_infographic.png)

## Bottom line

**Build it, and build it as a card rather than a menu.** The Refs panel is good at *finding* a
reference. Today it can only *open* one, or copy two formats from inside `⌘K`. Copying is the
missing step from finding a reference to using it elsewhere: in a daily note, a capture
draft, an agent prompt, Slack, or a terminal. Most of the data is already in memory, so the
feature is cheap.

The recommended shape:

1. **`⌃Y` turns the inspector column into a Copy card.** The selected list row stays visible,
   so it is always clear which reference you are copying from.
2. **Every row has a fixed keycap, a label, and a literal preview** of the exact text that will
   be copied. One more keypress copies that row.
3. **The [catalog](#the-copy-catalog) is closed and fixed.** `I` Marker ID · `T` Title · `W` Wiki link · `U`/`L`/`X`/`D`
   source handles · `N`/`P`/`F`/`R` note, PDF path, PDF file, reading task · `S` research
   ref · `1`–`9` your notes · `A` all your notes. Rows a reference lacks are hidden, and the
   remaining rows keep their letters.
4. **A copy hides Refs immediately and confirms with a small glass HUD** that names what was
   copied, so [the next `⌘V` lands in the app you came from](#after-a-copy).
5. **The marker ID comes from bob, not from a guess.** bob-cli adds an additive `marker_id`
   field to the `ref list`/`ref show` JSON first. The PDF stem is wrong or missing for
   [83 of the 406 rows](#live-library-measurements).
6. **`⌘K`'s two copy items fold into one item, "Copy… ⌃Y".** That leaves one copy surface with
   one behaviour.

## Critique of the plan

**Is this a good idea? Yes.** All four researchers agree, and the code and library data
support them.

### Why it earns a dedicated key

- **It closes a real loop.** The handles Bryan passes to other tools are the marker ID (for
  `bob ref show` and agent prompts), the wiki link, the reading-task link, the PDF, and
  Bryan's own notes. Some of these are hard to rebuild by hand. Two cannot be seen at all
  without opening the note: the reading-task block link, and the ID whenever it differs from
  the file stem.
- **`⌃Y` = yank is already Bryan's convention.** The Obsidian "Copy active file path" picker
  in `bob-navigation-hotkeys` is bound to **Mod+Y**
  (`src/490-plugin-lifecycle.js:280`). The Refs router already uses Readline/Vim control
  chords (`⌃N/P/J/K/D/U/[`).
- **The design system already has the right pieces.** The newest Capture surface is an
  in-panel SwiftUI card: the pull-in choice card with keycap hints and a footer
  (`CapturePullInChoiceView.swift`). `CapturePickerKeyHints` defines the keycap style. Refs
  already has a pasteboard abstraction with a test fake, and a 1.5 s footer toast.

### Risks that shape the design

The risks, which shape everything below:

| Risk | What would go wrong | Design answer |
| --- | --- | --- |
| Kitchen-sink menu | Fifteen formats are slow to scan and teach nothing | A closed catalog with absent rows hidden. A chat reference shows a calm 7-row card |
| Wrong "ID" | Copying the PDF stem or `RefItem.id` (the note path) and calling it the marker ID | A bob-authored `marker_id`, plus a tag when the ID is shared ([measurements](#live-library-measurements)) |
| `⌘V` lands in the wrong place | The Refs panel stays key after a copy, so `⌘V` pastes into its own search field | Copying hides the panel ([A3](#requirement-adjustments-explicitly-called-out)) |
| `⌃Y` leaks into the search field | Cocoa binds `⌃Y` to `yank:`, and today the router returns `nil` for it | The router always consumes `⌃Y` in Refs ([A9](#requirement-adjustments-explicitly-called-out)) |
| Stale or wrong target | A late `ref show` result, a refresh, or the loader's first-row fallback copies another reference | Freeze the target when the card opens, and require an exact path match ([reliability contract](#reliability-contract)) |
| Silent failures | Showing "Copied" when the pasteboard write failed, or clearing the clipboard because a fetch failed | Build the payload first, write once, check the result, and only then confirm ([reliability contract](#reliability-contract)) |

### Alternatives considered

**Would I take a different approach?** I keep the request's core idea: one key opens a
chooser and one more key copies. I change the implementation: a card instead of an
`NSMenu`, hiding Refs after a copy, one copy surface, and the ID coming from bob.
Alternatives I rejected as the primary design:

- **Grow `⌘K`:** copy items keep competing with opens and Scan, and `⌘K` has no previews.
- **Immediate copy on `⌃Y`:** the default is invisible, and the other values can't be
  discovered.
- **Smart `⌘C` with no selection:** invisible, and it fights text-editing habits. gem and grk
  liked it; cld and cdx did not. It can be revisited later as "`⌘C` copies the default row".
- **A full filter-to-select palette:** typing to filter is slower than a mnemonic when there
  are about 14 fixed rows.

One adjacent idea for the backlog: when Refs was opened over a Capture draft, a copy could
bring Capture back so `⌘V` lands in the draft.

## Requirement adjustments explicitly called out

| # | Original | Adjustment | Why |
| --- | --- | --- | --- |
| **A1** | "Open a new menu" | Use an **in-panel SwiftUI Copy card** that replaces the inspector column. Do not pop up a second `NSMenu`. | A card can show literal previews, hold a loading row, render in the `RefsPanelDesignTests` PNG fixtures, and route keys through the existing local monitor. `NSMenu.popUp` runs its own tracking loop (hence `suspendHideOnResign`), and whether bare-letter key equivalents fire reliably during tracking is unverified ([why a card](#why-a-card-instead-of-a-menu)) |
| **A2** | "Select with a single keypress" | Kept for every fixed value, and for the **notes that fit on the card** (`1`–`9`). A second step (an `H` picker) only reaches long-tail and uncommented highlights | 45 of 48 commented references have 9 or fewer comments. One reference has 29 annotations, and no single-key scheme reaches all of them honestly |
| **A3** | (unstated) | **A copy hides Refs** and shows a non-key glass **HUD** (about 1.2 s) naming what was copied | The panel is a key, non-activating `NSPanel`. While it is up, `⌘V` goes to its search field. After `orderOut`, key focus returns to the frontmost app on its own (`RefsPanel.swift`, `hide()`) |
| **A4** | "Copy the marker note's ID" | **bob-cli first:** serialize the frontmatter `id` as an additive **`marker_id`** JSON field. The app never derives the ID from the PDF stem | In 77 rows the field is absent, in 6 it differs from the stem, and 3 IDs are shared by 9 rows ([measurements](#live-library-measurements)). The thin-client rule forbids the app from reading frontmatter |
| **A5** | "Be creative" | A **closed catalog of 13 letters plus digits**. Absent rows are hidden but **never re-lettered**. Pressing a hidden row's letter explains why it is missing | Fixed muscle memory, and a small common card. The panel's own honesty rule is that absence stays absence |
| **A6** | "One of the notes/highlights" | Digits index **YOUR NOTES** (commented highlights, in inspector order). `A` copies all your notes, standalone notes, and the note body. `H` picks any highlight, including uncommented ones (phase 4) | The numbers match what the inspector shows. Uncommented highlights matter mostly as a set |
| **A7** | — | **Excluded:** formal citation, BibTeX, or APA; summary or abstract excerpts; shell-escaped paths; synthesized capture tokens; bob's full digest; thumbnails | Metadata is too sparse (18 of 406 rows have an author, 14 have a date). Excerpts are clipped at 360 or 420 characters. No path contains a space. Tokens would violate `decisions:mac-capture-is-a-thin-client`. Agents can run `bob ref show` on the ID themselves |
| **A8** | — | `⌘K`'s **Copy Wiki Link** and **Copy PDF Path** become one **Copy… `⌃Y`** item | One copy surface with one behaviour. The menu item also teaches the shortcut |
| **A9** | — | `⌃Y` is **always consumed** in Refs: it opens the card, or does nothing when no row is selected. It passes through only while an IME is composing | Otherwise Cocoa's `yank:` reaches the search field |
| **A10** | — | A **fixed default row** for `↵` and `⌃Y ⌃Y`: the Marker ID, or the Wiki link when there is no ID. No last-used memory | Vim's `yy` reflex with a value you can see. A sticky default becomes a trap the next morning |
| **A11** | — | **Plain-text payloads, except `F`**, which writes a file URL. The HTML flavour for `L` is deferred | Predictable pastes into Obsidian, terminals, and LLM chats |

## Why a card instead of a menu

cdx made the strongest case for the native menu. On macOS 26, `NSMenuItem.subtitle` allows
two-line rows, and native menus give placement, appearance, and accessibility for free.
Four things still favour the card over an `NSMenu`:

1. **Single-letter activation is unverified inside a tracking menu.** Bare-letter key
   equivalents set with `keyEquivalentModifierMask = []` may fire, or may type-select by
   title. My search found no authoritative answer: an [old cocoa-dev thread](#sources) covers only
   ⌘-modified equivalents, and Chromium's tests call Cocoa's behaviour inconsistent. Menu
   tracking also runs outside the panel's local key monitor. That is why `⌘K` already needs
   `suspendHideOnResign`. A card keeps every key in `RefsPanelController.processKeyEvent`,
   which is pure and tested.
2. **Previews have to show the actual bytes,** including multi-line note excerpts and the
   "shared ×5" tag. A menu subtitle is one line of secondary text.
3. **Async rows.** A notes row that is still loading, or a queued `1`, needs live updates. An
   `NSMenu` blocks in `popUp` while it tracks.
4. **House style and tests.** The pull-in choice card already established the in-panel card
   with keycaps and a footer. `RefsPanelDesignTests` can render a SwiftUI card to PNG, but it
   cannot render an open `NSMenu`.

Keep `⌘K` as an `NSMenu`: it is a mixed list of verbs, and mouse users expect a menu there.

## The copy catalog

Rows are shown in this order. Hairlines separate the groups, and only YOUR NOTES has a header,
matching the inspector's label. Every payload is either a bob-authored string copied verbatim
or a deterministic presentation format of bob fields. Nothing is parsed from Markdown or from
the PDF.

| Key | Label | Exact payload (real example) | Source | Shown when | Rows today | Phase |
| --- | --- | --- | --- | --- | --- | --- |
| **I** | Marker ID | `second_wave_job_applications` (+ `shared ×5` tag when duplicated) | bob `marker_id` (**new**) | field present | 329 | 3 (needs 1) |
| **T** | Title | `Wave 2: The Ten Applications to Send Next (October 2026)` | `title`, raw and complete | always | 406 | 3 |
| **W** | Wiki link | `[[ref/chat/second_wave_job_applications]]` | bob `link`, verbatim | always | 406 | 3 |
| — | | | | | | |
| **U** | Source URL | `https://hamel.dev/blog/posts/evals-faq/` | `urls[0]`, unmodified | URL present | 27 | 3 |
| **L** | Markdown link | `[AI Evals: Everything You Need to Know](https://hamel.dev/…)` | title + `urls[0]`; escape `[ ] \` in the title, percent-encode `( )` and spaces in the URL | URL present | 27 | 3 |
| **X** | arXiv | `arXiv:2509.06216` (same form as the inspector byline) | `identity.arxiv` | present | 9 | 3 |
| **D** | DOI | bare DOI | `identity.doi` | present | 0 | 3 |
| — | | | | | | |
| **N** | Note path | `ref/chat/second_wave_job_applications.md` (vault-relative, the form `bob ref show` and agents accept) | `path` | always | 406 | 3 |
| **P** | PDF path | `/Users/bryan/bob/lib/chat/second_wave_job_applications.pdf` (absolute, as `⌘K` copies today) | `library.pdfURL(for:)` | resolves (tagged `missing` when not on disk) | 406 | 3 |
| **F** | PDF file | the file itself, as a file URL, for Slack, Mail, Finder, or LLM chats | `pdfURL` written via `writeObjects([NSURL])` | file exists | ≈406 | 3 |
| **R** | Reading task | `[[job_search_2026#^ref-second-wave-job-applications]]` (label adds "· archived" when archived) | `task.link`, verbatim | task with link | 405 | 3 |
| **S** | Research ref | `research:202608/xprompt_role_binding/xprompt_role_binding.md` | `research_ref`, verbatim | present | 1 | 3 |
| — | **YOUR NOTES** | | | | | |
| **1–9** | p. N ↳ comment | [note block](#note-block-format) (below) | inspector's `commentedHighlights` | loaded, and the row fits | 48 refs | 3 |
| **A** | All your notes | note blocks joined, then standalone notes, then `own_notes` | same show response | any comment, note, or `own_notes` | 48+ | 3 |
| **H** | Pick a highlight… | opens the picker layer | unfiltered `ref show` | any annotation | 76 | 4 |

### Note block format

**Note block** (one highlight). It uses bob's digest prefixes, keeps every line of a multi-line
comment, and never invents a page:

```markdown
> the dolla dolla bills didn't hurt

Comment: Replace with cash and cool 😎 .

— Page 11 · [[ref/chat/sase_launch_post_introduction#^h-bf02e5a34bcb]]
```

A standalone note uses `Note: …` with no quote. Omit the page segment when `page_label` is
absent. `A` joins blocks with a blank line in stored order and appends `own_notes` under
`### Notes`, exactly as bob's digest does. Distinct comments are never deduplicated.

### Phase-4 alternates

**Phase-4 alternates** (cld's idea, the native menu-alternate idiom): holding `⌥` swaps previews
in place. `⌥W` gives `[[path|Title]]`, `⌥P` the `~/bob/…` path, `⌥N` the absolute note path,
`⌥1–9` the quote only, and `⌥F` the narration MP3. `O` (an `obsidian://open?vault=…&file=…`
URL, built with a URL builder) joins as a plain letter.

### Formats considered and rejected

**Considered and rejected:** BibTeX, APA, or citation lines (sparse metadata; belongs in bob if
ever); summary or abstract (clipped heuristics); shell-escaped path (0 paths with spaces);
`@route:id` capture tokens (thin-client violation); bob's full `-f markdown` digest (agents can
take the ID or note path and call bob themselves); page-1 thumbnail; SHA or checksums; an
"agent prompt" template (personal, and drifts).

## Interaction design

### Opening

- **`⌃Y`** with a selected, available row opens the card synchronously. There is no
  which-key delay: the preview is what gives the user confidence. Because the state is set
  synchronously, a fast `⌃Y I` typed before the first frame still copies correctly.
- With **no selection**, `⌃Y` is consumed and does nothing. While an **IME is composing**,
  it passes through, like `⌃D`/`⌃U`.
- Opening **freezes the target**: the note path, the `RefItem` snapshot, and an invocation
  token. A library refresh never changes what a letter copies mid-gesture.
- Opening requests inspector hydration **immediately**, skipping the 120 ms settle. The notes
  section fills in at the bottom when it arrives, without moving the rows above it.

### Keys while the card is open

The card captures **every** keyDown, so nothing leaks into the query.

| Key | Action |
| --- | --- |
| Letter or digit of a visible row | Copy that row, then hide Refs and show the HUD |
| Letter of a hidden row | The card's message line explains, e.g. "No source URL for this reference" or "No marker ID — N copies the note path" |
| Digit while notes are still loading | Queue it: the notes header shows a spinner, and the copy happens when data lands. `esc` cancels. After a 5 s timeout or an error, show a red message and **leave the clipboard untouched**. If the note does not exist once loaded, say "No note 4" |
| Any other printable key | "Nothing on 'q'" for 1.5 s. No beep, no shake |
| `↵`, `⌃Y` | Copy the selected row. The selection starts on the default row ([A10](#requirement-adjustments-explicitly-called-out)) |
| `↑`/`↓`, `⌃N`/`⌃P`, `⌃J`/`⌃K` | Move the selection (wraps), with the same keys as the list |
| `esc`, `⌃[` | Close the card and return to the inspector. The query, scope, and selection are untouched |
| `⌘K` | Close the card, then open Actions |
| Mouse | Hover highlights a row, a click copies it, and a click outside closes the card |

Letters match on `charactersIgnoringModifiers`, lowercased, so mnemonics follow the printed
layout and Caps Lock or Shift changes nothing. The Esc ladder becomes: **card → banner →
query → scope → close**. Hiding Refs (resign key, hotkey toggle, takeover, or Capture showing)
closes the card, and `prepareForPresentation` resets it.

### After a copy

1. Build the payload. If it is empty or unavailable, stop with a message and leave the
   clipboard untouched.
2. Write it once and check the result.
3. On success, hide Refs, show the HUD, and post a VoiceOver announcement ("Copied marker
   ID").
4. If the write fails (rare), keep the card open with "Couldn't copy". `↵` retries the
   **frozen** payload.

### Reliability contract

- `RefsPasteboardWriting` becomes `write(_ payload: RefsClipboardPayload) -> Bool`, where the
  payload is plain text or a file URL. Keep `copy(_:)` for diagnostics. Writing on the main
  actor makes success observable. Optionally add the `org.nspasteboard.source` marker (the
  bundle ID) so clipboard managers attribute the entry.
- Copying never reads `response.refs.first`. A show result counts only when its `path` equals
  the frozen target. Remove the loader fallback in the same change: if bob ever returns a
  different path, the inspector should show nothing rather than another reference's notes.
- One pending copy at most. `esc`, hide, or a newer `⌃Y` revokes the right to write: a late
  subprocess result may finish, but it can never reach the clipboard.
- An older `bob` without `marker_id` decodes to no ID. The row hides, and pressing `I` says
  "Needs a newer bob". The rest of the library decoding is unaffected (additive under
  schema 1).

## Visual design

### Principles

1. **What you see is what you copy.** The preview and the payload come from the same function.
   Truncation with an ellipsis is the only difference, and a test checks it.
2. **Absence stays absence.** No "Unknown", no dimmed placeholders.
3. **One family.** The card is the inspector turned over: the same `RefsKindTile`, inspector
   typography, the list's selection capsule, the Capture keycap style, and the panel's glass.
   It adds no second glass surface and never resizes the panel.

### Typical agent-report chat

The typical agent-report chat (89% of rows):

```text
╭────────────────────────────────────────────────────────────────────────────────────────╮
│ ⌕  wave 2                                         [All ⌘1]                    3 of 406 │
├────────────────────────────────────────────┬───────────────────────────────────────────┤
│▸[💬] Wave 2: The Ten Applications to Se… ◐ │ [💬]  COPY                                 │
│      Chat · yesterday · job_search_2026     │       Wave 2: The Ten Applications to Se… │
│ [💬] Wave 1: The First Ten Applications  ✓ │                                           │
│      Chat · Oct 2                           │ ▌[I]  Marker ID    second_wave_job_appl…  │
│ [💬] Waveform Rendering Notes            ○ │  [T]  Title        Wave 2: The Ten Appl…  │
│      Chat · Sep 12                          │  [W]  Wiki link    [[ref/chat/second…ns]] │
│                                             │  ──────────────────────────────────────── │
│                                             │  [N]  Note path    ref/chat/second…ns.md  │
│                                             │  [P]  PDF path     /Users/bryan/bob/…pdf  │
│                                             │  [F]  PDF file     second_wave_job_a….pdf │
│                                             │  [R]  Reading task [[job_search_2026#^…]] │
│                                             │                                           │
│                                             │  ↵ copies Marker ID · ↑↓ choose · esc back│
├────────────────────────────────────────────┴───────────────────────────────────────────┤
│ Copy — press a key                                                     Updated 2m ago  │
╰────────────────────────────────────────────────────────────────────────────────────────╯
```

### Annotated external paper

The annotated external paper (the dense case):

```text
 [🎓]  COPY
       Agentic Software Engineering: Foundational Pil…
 ▌[I]  Marker ID     agentic_software_engineering
  [T]  Title         Agentic Software Engineering: Fou…
  [W]  Wiki link     [[ref/papers/agentic_s…ineering]]
 ──────────────────────────────────────────────────────
  [U]  Source URL    https://arxiv.org/abs/2509.06216
  [L]  Markdown link [Agentic Software Engine…](https…)
  [X]  arXiv         arXiv:2509.06216
 ──────────────────────────────────────────────────────
  [N]  Note path     ref/papers/agentic_softw…ering.md
  [P]  PDF path      /Users/bryan/bob/lib/pap…ring.pdf
  [F]  PDF file      agentic_software_engineering.pdf
  [R]  Reading task  [[sase#^ref-agentic-softwa…ring]]
 YOUR NOTES 2 · quote + comment + link
  [1]  p. 28  ↳ Tale/epic plan frontmatter is missing…
  [2]  p. 31  ↳ …
  [A]  All your notes   2 notes · Markdown
 ↵ copies Marker ID · ↑↓ choose · esc back
```

Note rows preview **Bryan's own comment** (`↳`), which is the most recognizable text. The full
block shows on hover (`.help`). When notes overflow the column, the last line reads "+N more —
A copies all" (and, in phase 4, "H picks one"). The visible count comes from the layout, never
from scrolling.

### Tokens

| Element | Spec |
| --- | --- |
| Placement | The inspector column (panels ≥ 760 pt wide). Below that width, the card covers the list column |
| Header | `RefsKindTile` 28 pt; "COPY" in `.caption.weight(.semibold)`, `.secondary`; title in `.headline`, one line, tail-truncated |
| Row | 24 pt: keycap, then a 92 pt `.callout` label, then a preview that fills the rest |
| Keycap | 18×18 pt, radius 4.5, fill `.primary.opacity(0.06)`, stroke `.primary.opacity(0.14)` at 0.5 pt (1 pt under Increase Contrast), SF Mono 11 semibold, uppercase glyph. On the selected row: accent fill and a white glyph |
| Preview | SF Mono 11.5, `.secondary`. `.middle` truncation for IDs, paths, and links; `.tail` for titles and notes |
| Shared-ID tag | Orange capsule, `.caption2`, "shared ×5", with help text "bob ref show needs the note path for this one — press N" |
| Message line | The card footer in `.caption`, `.secondary`. It doubles as the hint and error line (red for errors) |
| Panel footer | While the card is open, it reads "Copy — press a key". When idle, it adds `⌃Y Copy` after `⌥↵ Reveal`, using `ViewThatFits` fallbacks as the pull-in footer does |
| Motion | Cross-fade plus a 6 pt rise over 0.14 s easeOut. Reduce Motion: cross-fade only. Selection moves instantly |
| HUD | A borderless non-activating `NSPanel` (`canBecomeKey = false`, `ignoresMouseEvents = true`, the Refs collection behaviour) holding a glass capsule: a green `checkmark.circle.fill`, "Copied Marker ID" (13 pt semibold), and the value (SF Mono 11.5, middle-truncated, max 380 pt). It is centered on the panel's former frame. Fade in 0.1 s, hold 1.0 s, fade out 0.3 s. Reopening Refs removes it at once |
| Accessibility | The card is one container ("Copy menu for {title}, 7 options"). Each row reads "Marker ID, second_wave_job_applications, key I" and is a button. Hidden rows are absent from the accessibility tree. Announcements: on open, "Copy menu. Press a letter or number."; on success, "Copied …" |

## Verified facts that drive the design

### Code facts

Code inspected: bob-mac-capture `44051a0`, bob-cli `ae9e6ef`.

| Fact | Where | Consequence |
| --- | --- | --- |
| `⌃Y` (keyCode 16) is unmapped. The router returns `nil`, so the key reaches the search field | `RefsKeyRouter.swift` | One new case, which must consume the key |
| `⌘K` uses `NSMenu.popUp`. Its copy items have empty key equivalents, and the panel needs `suspendHideOnResign` while the menu tracks | `RefsPanel.swift` `showActionsMenu`, `RefsActionsMenu.swift` | A menu is a modal side-loop outside the panel's key router |
| Copies call `clearContents()` + `setString` and **discard the Bool result**, then toast 1.5 s and **leave the panel open** | `RefsActionsMenu.swift` `SystemRefsPasteboard`; `RefsPanelModel.swift` `copyWikiLink` | The feedback does not check success. The protocol must return a result |
| The panel is a `.nonactivatingPanel` with `canBecomeKey = true`. `hide()` is `orderOut`, and key status returns to the frontmost app | `RefsPanel.swift` | Hide-on-copy makes `⌘V` work immediately |
| `prepareForPresentation()` resets the query, scope, and selection on every show | `RefsPanelModel.swift` | Hide-on-copy means a second copy from the same reference needs a new search. This is the accepted cost of A3 |
| `RefItem.id` is the vault-relative **note path**. `stem` is the **PDF** filename stem | `RefsModel.swift` | Neither is the marker ID |
| Frontmatter `id` is `#[serde(skip_serializing)]`, with the comment "kept out of JSON; only query resolution reads it" | `src/native/ref_library/row.rs:48` | The additive JSON change in A4 |
| The inspector runs `bob ref show <path> -f json -c` with a 120 ms settle and an LRU of 32. On a path mismatch it falls back to `response.refs.first` | `RefsFetching.swift`, `RefsInspectorLoader.swift:591–592` | Copy reuses the cache but must require an exact path match |
| `ref show` JSON has annotation `block_id` and `link` (`[[ref/…#^h-…]]`), plus `own_notes` and `research_ref`. The Swift decoder drops all four | `show.rs`, `RefsInspector.swift` (`RefsShowAnnotation`) | Additive `decodeIfPresent` work |
| The inspector's YOUR NOTES section uses `commentedHighlights`, which keeps highlights only (not standalone notes or images) | `RefsInspector.swift:83,131` | Digits mirror exactly what the inspector shows |
| bob's Markdown digest formats `> quote`, then `Comment: …`, and `Note: …` for standalone notes | `show.rs` ~L1002–1048 | The note payload reuses bob's convention, so single and bulk copies read the same |
| Geometry: panel 880×560, list 52%, inspector shown at ≥ 760 pt, search bar 52, footer 30, well radius 12 | `RefsVisualTokens.swift` | The card gets about 380×420 pt, enough for about 10 identity rows plus 3–7 notes |
| No HUD or toast window exists outside the panel. A capture success only pulses the status item | `AppDelegate.swift`, `StatusItemController.swift` | The HUD is new, but small (one borderless non-activating `NSPanel`) |

### Live library measurements

Live library on apollo, 2026-10-14. I independently confirmed cld's counts and added the
detail-level numbers no report measured.

| Quantity | Value | Design consequence |
| --- | --- | --- |
| Indexed `ref/` notes / PDF-backed (what Refs lists) | 1,008 / **406** | Only PDF-backed rows matter |
| Rows with frontmatter `id` | **329** (77 without) | `I` hides on 19% of rows. The default then falls back to `W` |
| `id` ≠ PDF stem | **6** (e.g. `sase_task_bead_48h_impact_rating` → `task_bead_48h_impact_ranking`; `obsidian_sync_footprint_audit_bob-cli-1l` → `…-1l.1_20260827`) | Stem-guessing (grk, gem) is wrong |
| Shared IDs | **3 groups, 9 rows** (`BryanBugyi_CV_extended` ×5, `harness_engineering` ×2, `task_bead_48h_impact_ranking` ×2) | Show a "shared ×N" tag, because `bob ref show <id>` is ambiguous for these |
| Source URL / multiple URLs / arXiv / DOI | 27 / **0** / 9 / **0** | Source rows are rare. `D` stays defined but never shows today |
| Author / published | 18 / 14 | No formal citations ([A7](#requirement-adjustments-explicitly-called-out)) |
| Reading task with `link` | 405 | `R` almost always shows |
| `research_ref` | 1 | `S` is cheap but rare |
| Narration audio | 24 | A later `⌥F` candidate |
| Any annotation / any comment | 76 / **48** | 88% of cards have no notes section |
| Comments per commented reference | 1–3: 30, 4–9: 15, 10+: 3 (max 16), 168 total | Inline `1`–`9` covers 94% of commented references |
| Annotation kinds (all rows) | highlight 304, note 4, image 1 | Standalone notes are rare. Images are deferred |
| Rows with non-empty `own_notes` | **6** | Include them in `A` |
| Multi-line comments / multi-line quotes / missing page label | 15 / 0 / 3 | Keep comment lines intact. Never invent a page |
| `bob ref show <path> -f json` (unfiltered) latency | median 0.196 s, p90 0.224 s, max 0.271 s | A load in flight is short. Queue the copy rather than refusing it |
| Unfiltered show JSON size | median 1.7 KB, max 13.6 KB | Dropping `-c` later (for `H`) costs almost nothing |
| Title length median / p90 / max | 56 / 84 / 123 characters | Previews truncate titles at the tail and paths in the middle |
| Paths containing a space | 0 | No shell-escaped variant is needed |

## Where the researchers disagreed and the resolution

| Question | cdx | cld | grk | gem | **Resolution** |
| --- | --- | --- | --- | --- | --- |
| Surface | Native `NSMenu` with subtitles, plus a SwiftUI picker | Card replacing the inspector | Glass card over the row | Centered glass HUD palette | **cld's card in the inspector column.** It needs no anchor or clipping math, the row stays visible, and it is house style ([why a card](#why-a-card-instead-of-a-menu)) |
| Marker ID source | New `reference_id` field | New `id` field, with a shared-ID flag | `item.stem` (labelled "PDF stem" when unsure) | `item.stem` | **A bob field named `marker_id`.** The stem is wrong or missing for 83 of 406 rows. `id` would collide conceptually with the path-valued `RefItem.id`, and the docs already say "stable marker ID" (`--include-id`) |
| After a copy | Stay open, footer toast | **Hide**, glass HUD | Stay open, toast | Stay open, toast | **Hide + HUD.** Verified: the panel is key, so `⌘V` would hit its search field, and the Esc ladder can take 2–3 presses |
| Notes | `h` opens a searchable picker | Inline `1`–`9` + `A` (bob digest) | `N` opens a layer, then `1`–`9` | Inline `1`–`3` + `A` | **Inline `1`–`9` for the notes that fit**, `A` for all, and `H` picker in phase 4 for everything else. This keeps the single-keypress promise for the 94% case |
| `A` payload | App-built from JSON | bob's `-f markdown` digest (async) | App-built joined blocks | App-built | **App-built from the same formatter as `1`–`9`**, following bob's digest conventions. It is synchronous, consistent, and skips the digest's metadata and task noise |
| Single note format | Quote, "My note:", "Source:" line, block link | Quote + `Comment:`; block link as `⌥1–9` in phase 2 | Quote, comment, block link | `> "quote" (Page)` + comment | **`> quote`, `Comment: …`, `— Page N · [[…#^h-…]]`.** Use bob's prefix, and always keep the bob-authored block link for provenance |
| Default row (`↵`, `⌃Y ⌃Y`) | none | Marker ID, else Wiki | Wiki link | Wiki link | **Marker ID, else Wiki link.** Bryan named the ID first, and it is the shortest universal handle. Open question [Q1](#open-questions-for-bryan) |
| Citation | "Reference card" Markdown | Rejected | Deterministic one-liner | Formatted citation | **Rejected for v1.** Too sparse (18 authors). If wanted, add it to bob as `bob ref cite`, never as app-side formatting |
| `⌘K` copy items | Keep, add "Copy…" | Fold into "Copy… ⌃Y" | Keep as aliases | Keep | **Fold** ([A8](#requirement-adjustments-explicitly-called-out)). Hide-on-copy would otherwise make `⌘K` copies behave differently |
| Smart `⌘C` | Preserve native | Reject | Companion | Adopt | **Not in v1** ([alternatives considered](#alternatives-considered)) |
| Cocoa `⌃Y` | — | Moot (`⌃K` already remapped) | Live bug, consume it | Moot | **Consume it either way** ([A9](#requirement-adjustments-explicitly-called-out)). Correctness should not depend on the kill buffer being empty |
| Obsidian URI | Include | Defer (`⌥W`) | Include | Include | **Defer to phase 4** as its own letter, `O`. It is rare in this library and clutters the common card |

## Implementation plan

Follow bob-mac-capture's `AGENTS.md`. Never land Swift that has not been compiled. Use
`just portable-check` for RefsCore. App-target changes are type-checked on a scratch copy on
the Mac (`bundle.sh` + `just typecheck-tests`, never Bryan's checkout), and CI runs the tests.

Sizes: phase 1 is small; phases 2 and 3 are medium (one view, one small window, one key map,
a pasteboard protocol change, and fixtures); phase 4 is small to medium.

### Phase 0 Mac checks

About 30 min, before [phase 3](#phase-3-app-target) lands.

1. `⌃Y` reaches the Refs local monitor, and no Karabiner, Hammerspoon, or system binding eats
   it.
2. After `hide()`, `⌘V` pastes immediately in Highlights, Obsidian, and Terminal.
3. A file-URL pasteboard write attaches the PDF in Finder, Slack, Mail, Messages, Claude, and
   ChatGPT. Record what text-only targets receive.
4. The HUD never takes key, and it shows on the active Space over full-screen Highlights.

### Phase 1 bob-cli

Small. In `src/native/ref_library/row.rs`, serialize the frontmatter
`id` as `marker_id` (`#[serde(rename = "marker_id")]` in place of `skip_serializing`), as
`null` when absent. It is additive under `REF_SCHEMA_VERSION` 1, and `ref show` inherits it.
Update the JSON field list in `docs/ref.md` and the JSON tests. Query resolution keeps reading
the same struct field.

### Phase 2 RefsCore

Linux-testable.

- Additive `decodeIfPresent` for `marker_id` (into `RefItem.markerID`, round-tripped through
  the snapshot cache encoder), `research_ref`, annotation `block_id`/`link`, and `own_notes`.
- `RefsCopyCatalog.rows(item:notes:sharedIDCount:pdfExists:) -> [RefsCopyRow]`, a pure
  function giving a fixed key, label, payload, and preview for each row, with hidden rows
  omitted.
- `RefsCopyFormat`: the note block, all notes, Markdown-link escaping, preview truncation, and
  the default-row rule.
- `RefsCopyKeyMap.command(characters:keyCode:modifiers:rows:)`, returning one of `.copy(row)`,
  `.copySelected`, `.move(±1)`, `.close`, `.explainHidden(key)`, or `.unknown`.
- A shared-ID index built from the snapshot.
- Tests: payload equals the untruncated preview; fixed letters; hidden rows; marker ID ≠
  stem; shared IDs; an older bob without `marker_id`; chat versus paper catalogs;
  multi-line comments; missing page labels.

### Phase 3 app target

- `RefsKeyRouter`: `⌃Y` maps to `.showCopyCard`. It is consumed with no selection and passes
  through while an IME is composing.
- `RefsPanelModel`: `copyCard: RefsCopyCardState?`, holding the frozen target, rows, selection,
  pending copy, and message. Update the Esc ladder and the `prepareForPresentation` reset.
- `RefsPanelController.processKeyEvent`: while the card is open, route every key to
  `RefsCopyKeyMap` first.
- `RefsInspectorLoader`: hydrate immediately on open and require an exact path match (remove
  the `refs.first` fallback).
- `RefsPasteboardWriting.write(_:) -> Bool`, `RefsCopyCardView`, and `RefsCopyHUD`.
- `⌘K`: replace the two copy items with **Copy…** (key equivalent `⌃Y`).
- Update the footer hints, the README key table, the Esc-ladder line, and the `⌘K` section.
- Tests: router (`⌃Y`, IME); model (open/close, frozen target, queued digit, failure leaves
  the clipboard untouched, hide on success) with `FakePasteboard`; design PNG fixtures in
  light, dark, and Increase Contrast for the chat card, the annotated paper, a shared ID, a
  missing PDF, and notes overflow.

### Phase 4 follow-ups

The `H` highlight picker: drop `-c` from the inspector fetch (at most
13.6 KB) while keeping the `commentedHighlights` projection; list rows show kind, page, and
excerpt; digits index the visible page; arrows/Return reach everything. Also: `⌥` alternates,
`O` Obsidian URI, an HTML flavour for `L`, the `org.nspasteboard.source` marker, and dragging
a row out of the list.

## Open questions for Bryan

1. **Default row:** Marker ID (recommended) or Wiki link for `↵` and `⌃Y ⌃Y`? Either way it is
   one constant.
2. **Hide on copy:** confirm. It changes today's stay-open `⌘K` copies, and a second copy from
   the same reference needs a new search.
3. **Note format:** keep the `— Page · [[block link]]` provenance line by default, or make it a
   `⌥` alternate?
4. **Missing IDs:** 77 PDF-backed rows have no `id`. Should the research hook's
   `bob ref create` always pass `--include-id`, and also stamp `research:` refs so `S` lights
   up for new agent reports? This is a separate bob-cli change.
5. **Global `⌃Y`:** does any Mac-side tool bind it? ([Phase-0 check](#phase-0-mac-checks).)

## Recommended solution

**Ship the Refs `⌃Y` Copy card in three steps: bob-cli, then RefsCore, then the app. Gate the
app step on a [30-minute Mac check](#phase-0-mac-checks).**

- **bob-cli:** expose the frontmatter `id` as an additive `marker_id` JSON field.
- **RefsCore:** decode `marker_id`, `research_ref`, annotation `link`/`block_id`, and
  `own_notes`. Build a pure catalog, formatter, key map, and shared-ID index, all
  Linux-tested.
- **App:**
  - `⌃Y` turns the inspector column into a **Copy card**. Each row has a fixed keycap and a
    literal preview: `I T W · U L X D · N P F R S · YOUR NOTES 1–9 · A`.
  - Absent rows are hidden and never re-lettered.
  - One keypress copies, **hides Refs**, and confirms with a glass **HUD**. `↵` and
    `⌃Y ⌃Y` copy the Marker ID (or the Wiki link when there is none). `esc` returns to the
    inspector.
  - The target is frozen. Payloads are bob-authored or deterministic formats of bob fields.
  - The clipboard is written once, checked, and never touched on failure.
  - `⌃Y` never leaks into the search field.
  - `⌘K`'s copy items fold into **Copy… ⌃Y**.
- **Next:** the `H` highlight picker, `⌥` alternates, and the Obsidian URI.

This keeps the core of the request (one key opens a chooser, and one more key copies) while
meeting the three goals:

- **Intuitive:** the house "Y = yank" convention, fixed mnemonics, and a preview of every
  value.
- **Reliable:** a real marker ID, a frozen target, every key captured, checked writes, and
  `⌘V` landing where you expect.
- **Beautiful:** the inspector turns over in the panel's own type and materials; the common
  card is a calm 7 rows; and a glass HUD confirms the copy instead of a panel that lingers.

## Report scope and inputs

- **Date:** 2026-10-14
- **Lead:** consolidation of `research.19` (cdx, cld, grk, gem) plus independent verification
- **Request:** add `<ctrl+y>` to Bob Mac Capture's Refs panel. It should open a menu where a
  single keypress chooses what to copy. Be creative about the options, lead the design so it
  is intuitive, reliable, and beautiful, critique the plan, adjust requirements where
  justified, and end with a recommended solution.
- **Inputs:** [`__cdx`](refs_panel_ctrl_y_copy_card__cdx.md) (native `NSMenu` plus a
  highlight picker), [`__cld`](refs_panel_ctrl_y_copy_card__cld.md) (in-panel copy card, ID
  first, dismiss-on-copy HUD), [`__grk`](refs_panel_ctrl_y_copy_card__grk.md) (yank card with
  a notes layer), [`__gem`](refs_panel_ctrl_y_copy_card__gem.md) (glass HUD palette plus smart
  `⌘C`).
- **Code inspected:** bob-mac-capture `44051a0`, bob-cli `ae9e6ef`, bob-plugins (Yank Path
  picker). Live library: `bob ref list -R all -A -f json` and `bob ref show -f json` for every
  PDF-backed row, run on apollo on 2026-10-14.
- **Not done:** nothing was run on the Mac, no product code changed, and no usability study was
  done. The [Phase-0 checks](#phase-0-mac-checks) cover the Mac-only unknowns.

## Sources

- Researcher reports: `research:202610/refs_panel_ctrl_y_copy_card/refs_panel_ctrl_y_copy_card__cdx.md`,
  `…__cld.md`, `…__grk.md`, `…__gem.md`.
- Code, read in audited local checkouts: bob-mac-capture `44051a0` (`Refs/RefsKeyRouter.swift`,
  `RefsActionsMenu.swift`, `RefsPanel.swift`, `RefsPanelModel.swift`,
  `RefsInspectorLoader.swift`, `RefsFooter.swift`, `RefsVisualTokens.swift`,
  `CapturePullInChoiceView.swift`, `CapturePickerView.swift`, `BobPanelCoordinator.swift`;
  `RefsCore/RefsModel.swift`, `RefsInspector.swift`, `RefsFetching.swift`; `AGENTS.md`);
  bob-cli `ae9e6ef` (`src/native/ref_library/row.rs`, `show.rs`, `docs/ref.md`,
  `docs/highlights-ref-sync.md`); bob-plugins `bob-navigation-hotkeys`
  (`src/100-yank-and-paths.js`, `src/490-plugin-lifecycle.js:280`).
- Decision record: `decisions:mac-capture-is-a-thin-client`.
- Live library measurements: `bob ref list -R all -A -f json` and `bob ref show <path> -f json`
  for all 406 PDF-backed rows, plus a read-only frontmatter `id` scan, apollo, 2026-10-14.
- Platform and precedent:
  [Apple — Mac keyboard shortcuts (⌃Y yank)](https://support.apple.com/en-us/102650);
  [Apple HIG — Context menus](https://developer.apple.com/design/human-interface-guidelines/context-menus);
  [AppKit `NSMenuItem.subtitle`](https://developer.apple.com/documentation/appkit/nsmenuitem/subtitle);
  [AppKit `NSPasteboard`](https://developer.apple.com/documentation/appkit/nspasteboard);
  [Raycast API — HUD](https://developers.raycast.com/api-reference/feedback/hud);
  [nspasteboard.org markers](https://nspasteboard.org/);
  [Obsidian URI](https://obsidian.md/help/uri);
  [W3C APG menu pattern](https://www.w3.org/WAI/ARIA/apg/patterns/menubar/).
- Inconclusive evidence on bare-letter key equivalents in an open `NSMenu`:
  [cocoa-dev, "menus and key equivalents" (2004)](https://lists.apple.com/archives/cocoa-dev/2004/Mar/msg00697.html);
  [Chromium `nsmenuitem_additions_unittest.mm`](https://chromium.googlesource.com/chromium/src/+/main/ui/base/cocoa/nsmenuitem_additions_unittest.mm).
