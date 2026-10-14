# Bob Refs `⌃Y` Copy Menu: what to copy, how to choose it, and how to make it reliable

- **Date:** 2026-10-14
- **Researcher:** `cld`, one of five independent researchers (`cdx`, `grk`, `mus`, `gem`, `cld`)
- **Question:** Add a `⌃Y` keymap to Bob Mac Capture's Bob Refs panel. It opens a menu where
  one keypress picks what goes on the clipboard: the marker note's ID, one of the
  notes/highlights, and so on. Is this a good idea? What should the menu contain? How should it
  look and behave? End with a recommended solution.
- **Evidence examined:**
  - bob-mac-capture at `44051a0`: `Sources/BobMacCapture/Refs/*`, `Sources/RefsCore/*`, and the
    README "Bob Refs" section.
  - bob-cli at `f24d5e7`: `src/native/ref_library/{row,mod,show,resolve}.rs`, `docs/ref.md`, and
    `docs/highlights-ref-sync.md`.
  - bob-plugins: `bob-navigation-hotkeys`, which has the Obsidian "yank path" picker.
  - Live `bob ref list` / `bob ref show` output against `~/bob` on apollo.
  - The `Highlights.app` `Info.plist` on the Mac.
  - Prior research `research:202610/highlights_quick_open_refs_panel/…__final.md`.
  - Decision `decisions:mac-capture-is-a-thin-client`.

---

## 1. Bottom line

1. **Build it.** Copying is the main way a reference leaves the panel without being opened, and
   Bob workflows constantly need a reference's link, ID, or path: Obsidian links, agent prompts,
   terminal commands. Today the panel offers exactly two copies (Copy Wiki Link, Copy PDF Path).
   Both sit in the middle of a 10-item `⌘K` `NSMenu` that you have to arrow through. `⌃Y` is
   unbound in the Refs router. The mnemonic also matches Bryan's own vocabulary: his Obsidian
   plugin already calls copying "yank" and binds its copy-path picker to `⌘Y`.
2. **Build it as a which-key style "Copy card", not an `NSMenu`.** `⌃Y` raises a card over the
   content well with fixed mnemonic letters (`L` wiki link, `I` ID, `T` title, `P` PDF path, …)
   and digits `1`–`9` for your notes. Each row shows a **live preview of the exact string** that
   will land on the clipboard. Pressing a key copies at once, the row flashes, the card dissolves,
   and the footer confirms "✓ Copied wiki link · `[[ref/chat/…]]`". The panel stays open.
3. **The headline item needs a bob-cli change.** The marker note's `id` exists in frontmatter for
   329 of 406 PDF-backed references, but bob deliberately keeps it out of JSON
   (`#[serde(skip_serializing)] pub id` in `row.rs`). The app is a thin client that "never parses
   frontmatter". So `bob ref list` must emit `id` additively before the app can copy it. The
   per-highlight block links, by contrast, are already in `bob ref show` JSON (`block_id`,
   `link`); the app just doesn't decode them yet.
4. **Six requirement adjustments** (§4, each called out):
   - fold `⌘K`'s copy items into the new menu;
   - keep the panel open after a copy;
   - freeze what each key copies when the card opens;
   - hide items that don't apply but never reassign their letters;
   - copy multi-format payloads (rich link, file);
   - split the work so bob-cli lands the ID field first.

---

## 2. What exists today (verified)

### 2.1 The panel and its keys

- `RefsKeyRouter` is a pure function from `(keyCode, modifiers, context)` to `RefsCommand?`. It
  binds `⌃N/⌃P/⌃J/⌃K` (move), `⌃D/⌃U` (inspector scroll), `⌃[` (escape), `⌘K` (actions),
  `⌘R`, `⌘S`, and `⌘1–5`. **There is no `Y` key code (16) anywhere in the app.** In a Cocoa text
  field `⌃Y` is `yank:` (paste the kill ring). The ring is effectively always empty in the Refs
  search field, because the router steals `⌃K` (kill-line) for "move up". So taking over `⌃Y`
  costs nothing.
- `⌘K` pops an `NSMenu` (`RefsActionsMenu`) with sections opens / copies and sources / closing.
  Its copies are `copyWikiLink()` (bob's `link`, verbatim) and `copyPDFPath()` (absolute path).
  Each toasts the footer for 1.5 s ("Copied wiki link"). The menu needs a `suspendHideOnResign`
  hack while it tracks, because `NSMenu` steals key status from the non-activating panel.
- `RefsPasteboardWriting` is a protocol with one method, `copy(_ string:)`. Tests inject a fake.
- The inspector shows **YOUR NOTES**: commented highlights from `bob ref show <path> -f json -c`,
  3 per page, with `⌃D` revealing more. Each note shows its page label, the quote (italic,
  yellow 2 pt bar), and the comment.
- `RefsCore` (pure, Foundation + CaptureCore) has its own test target. That target runs on Linux
  under `just portable-check`, so logic placed there is verifiable on agent hosts. The view layer
  is macOS-only.

### 2.2 What each reference carries, and where it comes from

| Property | In the app today? | Source |
| --- | --- | --- |
| Wiki link `[[ref/chat/x]]` | yes (`RefItem.link`) | `ref list` `link` |
| Title (raw, may contain backticks) | yes (`rawTitle`) | `ref list` `title` |
| Note path `ref/…/x.md` | yes (`RefItem.id`) | `ref list` `path` |
| PDF path `lib/…/x.pdf` | yes (`pdfPath`, absolute via `RefsLibrary.pdfURL`) | `ref list` `source_pdf` |
| Reading-task block link `[[sase#^ref-…]]` | yes (`task.link`) | `ref list` `task.link` |
| Source URLs, arXiv ID, DOI, author, published | yes | `ref list` `urls`, `identity.*`, `author`, `published` |
| Narration audio | yes (`audioPath`) | `ref list` `audio` |
| **Marker/frontmatter `id`** | **no** | **bob reads it but skips it in JSON** (`row.rs`: "Frontmatter `id`, kept out of JSON; only query resolution reads it") |
| Each note's quote and comment | yes (`RefsShowAnnotation`) | `ref show -c` |
| **Each note's block ID / block link** `[[ref/x#^h-…]]` | **no, but bob already sends it** | `ref show` `annotations[].block_id`, `.link` |
| All highlights as Markdown | no | `bob ref show <ref> -f markdown` (exists, ~0.25 s on apollo) |
| Highlights page deep link `highlights://stem#page=N` | no | appears only in the Highlights sidecar export; bob parses the label and drops the URL |
| `research:` artifact ref | no | `ref list` `research_ref` (set on 1 of 406 rows) |

### 2.3 What the library actually looks like

These counts come from live `bob ref list` output for the 406 PDF-backed rows the panel shows:

| | Count | Share |
| --- | --- | --- |
| Chats (agent reports) | 362 | 89% |
| Blogs / papers / docs | 17 / 16 / 11 | 11% |
| Have a frontmatter `id` | 329 | 81% |
| `id` ≠ note stem | 6 | 1.5% (CV versions and one renamed report) |
| Have a reading task | 405 | ~100% |
| Have any highlight / any comment | 76 / 48 | 19% / 12% |
| More than 3 / more than 9 comments | 18 / 3 | (max 16) |
| Have source URLs / arXiv / DOI / author | 27 / 9 / 0 / 18 | 7% / 2% / 0% / 4% |
| Have narration audio | 24 | 6% |

The design consequence is that **the common case is a chat with no notes and no source**. For
that case the card must be compact and fast: about 8 rows, all of them identity, link, and path
formats. Source formats and notes matter for a minority, so they appear only when present.

The marker `id` is "intended for research hook execution". `bob ref create --include-id` embeds
the research report's filename stem (for example `xprompt_role_binding`). So **the ID is the
handle that ties a PDF back to its SASE research report**. `bob ref show <id>` resolves it, which
makes it the most useful string to paste into an agent prompt. That explains why Bryan named it
first.

### 2.4 Precedent in Bryan's own tools

`bob-navigation-hotkeys` registers **"Copy active file path" on `Mod+Y`**. It opens
`YankPathPickerModal`, a filtered picker that lists six path formats. Each row shows a **live
preview of the exact text** and an "Unavailable" status when a format can't be computed, and a
copy confirms with `Notice("Copied <label>")`. Three lessons carry over:

- "yank" is already Bryan's word for copy;
- previews of the exact value are expected;
- unavailable formats need a reason.

The difference here is that Bryan wants single-keypress selection, not type-to-filter.

---

## 3. Critique: is this a good idea?

**Yes, with caveats.** Here is the honest case against it, and what answers each point.

| Risk | Why it matters | Answer in this design |
| --- | --- | --- |
| **Menu sprawl.** "Be creative" invites 25 options. | A single-key menu only works if you can take it in at a glance. Past about 12 rows you scan instead of recognise, and the one-key promise dies. | Curate to 8 always-present rows plus conditional rows. Hide what doesn't apply. Defer the long tail (§5.3). |
| **Two copy paths.** `⌘K` already copies the link and PDF path. | Two implementations drift (the toast text, the missing-PDF rule, the absolute-vs-relative choice). | Adjustment A1: `⌘K` keeps one "Copy… ⌃Y" item that opens the card. |
| **Single-key menus punish mis-presses.** | A wrong key silently clobbers the clipboard. | The cost is low: copying is non-destructive and the toast names what was copied. Unknown keys are swallowed, never passed to the search field. |
| **`⌃Y` means different things in different worlds.** | In Emacs `C-y` *pastes*. In Vim `⌃Y` scrolls up one line, and `y` is yank (copy). | Bryan's context is Vim-flavoured (`⌃D/⌃U` scroll, an Obsidian Vim mode, the "yank" vocabulary). The Vim `y` = copy mnemonic wins. `⌃E/⌃Y` single-line scrolling in the inspector would be a weak claim on the key anyway. Keep `⌃Y`. |
| **The best items need bob changes.** | The thin-client rule means the app can't read the marker ID from the note itself. | Adjustment A6: ship the bob-cli `id` field first. It is additive under `schema_version` 1, the same way `blocked` and `task` were. |
| **Discoverability.** | Nobody finds `⌃Y` unless it is shown. | Add a footer hint (`⌃Y Copy`), a `⌘K` entry showing the shortcut, and a README row. |

**Would I take a different approach?** I weighed four alternatives (§8). Two of them contribute
pieces to the recommendation:

- The "hint badges in the inspector" idea (Vimium-style) is beautiful, but it fails when the panel
  is narrow and has no inspector, and many formats (wiki link, ID, Obsidian URL, file) have no
  on-screen element to badge. I recommend it only as polish (numbered badges on the inspector's
  notes while the card is up).
- Extending `⌘K`'s `NSMenu` is cheaper but can't preview values or morph them on modifiers, and
  it keeps the resign-key hack.

The card is the right core.

---

## 4. Requirement adjustments (explicitly called out)

> **A1: One home for copying.** Remove "Copy Wiki Link" and "Copy PDF Path" from `⌘K`. Put a
> single **"Copy…   ⌃Y"** item in their slot that opens the card. Mouse users still have a path
> in, and the shortcut is advertised exactly where people look for actions.
> *Why:* one implementation, one toast, one set of rules.

> **A2: The panel stays open after a copy.** The card closes and the footer confirms. The panel
> already hides on resign-key, so the natural next step (⌘-Tab or clicking into Obsidian or a
> terminal) dismisses it for free. Staying open allows "copy the ID, then the title". The current
> `⌘K` copies already behave this way.
> *Rejected:* Raycast's "copy and close the window". It would need a separate screen-level HUD,
> because the footer toast disappears with the panel.

> **A3: What you see is what you paste.** When the card opens, every entry's payload is computed
> and frozen. The preview is drawn from the same value (truncated visually only; a tooltip shows
> it in full). Library refreshes during the card's lifetime never change what a key copies.
> Notes may *arrive* after open (hydration), but they never re-number.

> **A4: Hide items that don't apply; never reassign letters.** `U` is always "Source URL". On a
> chat with no URL the `U` row is absent. Pressing `U` anyway shows "This reference has no source
> URL" instead of copying something else. This beats both alternatives: dimmed rows clutter the
> common chat case, and positional numbering kills muscle memory.

> **A5: Copy the right *kind* of thing, not just strings.**
> - "PDF file" puts the file itself on the pasteboard, so it pastes as an attachment in Mail,
>   Slack, and Messages and as a file copy in Finder.
> - "Markdown link" writes both `[Title](url)` as plain text and an HTML anchor, so it pastes as
>   a clickable title in rich-text apps and as Markdown in editors and terminals.

> **A6: Sequence the work across both repos.** First, bob-cli emits `id` in `ref list` JSON (and
> documents it). Then the app decodes `id`, `block_id`, and `link` with `decodeIfPresent` and
> builds the card. An older `bob` simply yields a card without the ID row. It falls back to
> "Stem" (see §5.2), never to an error.

---

## 5. What goes in the menu

### 5.1 Full candidate inventory (the "think hard" list)

Each candidate gets a verdict: **v1**, **later**, or **no**, with the reason.

| # | Candidate | Example | Verdict | Reason |
| --- | --- | --- | --- | --- |
| 1 | Wiki link | `[[ref/chat/second_wave_job_applications]]` | **v1 (default)** | The most Bob-native pointer. bob supplies it verbatim. |
| 2 | Wiki link with title alias | `[[ref/chat/x\|Wave 2: …]]` | later | Reads well in prose, but titles contain `\|`, `]`, `#`, `` ` `` that need escaping. bob should emit it (`link_titled`), not the app. Natural future `⌥L`. |
| 3 | Embed `![[…]]` | | no | Rare. Trivial to type by hand. |
| 4 | Obsidian URL | `obsidian://open?path=/Users/bryan/bob/ref/chat/x.md` | **v1** | Clickable from Slack, Things, a browser, or a terminal on this Mac. Reuses `ObsidianOpenURL`. |
| 5 | Reading-task link | `[[job_search_2026#^ref-second-wave-job-applications]]` | **v1** | Points at the *task* (status, lane), not the note. bob supplies it verbatim (`task.link`). 405/406 rows. |
| 6 | Title | `Wave 2: The Ten Applications to Send Next (October 2026)` | **v1** | Writing, messages, commit messages. Raw title verbatim. |
| 7 | **Marker ID** | `second_wave_job_applications` | **v1 (needs bob)** | The handle `bob ref show <id>` resolves. It ties the PDF to its research report. 81% coverage. |
| 8 | PDF / note stem | `second_wave_job_applications` | v1, as the ID fallback | `bob ref show` also resolves stems. For the 19% without an ID, the `I` row becomes "Stem". |
| 9 | Note path (absolute) | `/Users/bryan/bob/ref/chat/x.md` | **v1** | Agent prompts, `nvim`, `rg`. |
| 10 | PDF path (absolute) | `/Users/bryan/bob/lib/chat/x.pdf` | **v1** | Unchanged from today's `⌘K` (agents can read PDFs). |
| 11 | Vault-relative paths | `lib/chat/x.pdf` | later | The wiki link covers Obsidian. Could become `⌥P`/`⌥N`. |
| 12 | **PDF file** (pasteboard file URL) | *(the file)* | **v1** | Attach to Mail/Slack/Messages, drop into Finder. Better than any path for sharing. |
| 13 | Narration audio file | `x.mp3` | later | 6% coverage. `⌘K` → Open Narration already exists. |
| 14 | Source URL | `https://arxiv.org/abs/2509.06216` | **v1, when present** | Share the original. |
| 15 | Markdown source link (rich) | `[Agentic Software Engineering…](https://arxiv.org/abs/2509.06216)` | **v1, when present** | The most-wanted "cite this" form. Rich HTML too (A5). |
| 16 | arXiv ID / DOI | `arXiv:2509.06216` | **v1, when present** | Citation managers, search. Rare, so conditional. |
| 17 | Formatted citation / BibTeX | | later | Needs metadata bob doesn't have. Would be a bob feature (`bob ref cite`), never app-side formatting. |
| 18 | **Each note** (quote + comment, Markdown) | `> This is a LOT…` | **v1: digits 1–9** | Bryan's notes on agent reports are feedback ("List every supported CLI provider here."). Pasting quote and comment into an agent prompt is a real loop. |
| 19 | Each note, quote only | `Listing 2. A Consultation Request Pack…` | **v1: `⇧`+digit** | Quoting the author in writing. |
| 20 | **Each note's block link** | `[[ref/papers/agentic_software_engineering#^h-56c9652856d1]]` | **v1: `⌥`+digit** | Cite one highlight from any Obsidian note. bob already sends it. |
| 21 | All highlights & notes as Markdown | *(bob's `-f markdown` digest)* | **v1: `A`, when annotations exist** | Whole-reference context for an agent or a write-up. bob renders it, the app only copies it. |
| 22 | Highlights page deep link | `highlights://agentic_software_engineering#page=29` | **later (spike)** | Highlights *does* register the `highlights` scheme (`CFBundleURLSchemes = [highlights]`, role Editor, v2026.1.2). Whether it resolves by name and honours `#page=` is unverified, and bob currently drops the sidecar's page URL. High value if the spike passes. |
| 23 | Abstract / bottom-line excerpt | | no (for now) | The app's excerpt is capped (420/360 chars, with "…"). Copying a truncated excerpt breaks the inspector's honesty rules. |
| 24 | Outline headings, facts (pages, reading time) | | no | Low value as clipboard content. |
| 25 | SASE `research:` ref | `research:202610/…` | later | bob emits `research_ref`, but only 1 of 406 rows has it. Add when the research hook stamps it routinely. |
| 26 | Page-1 thumbnail image | | no | Cute, niche. |
| 27 | Raw JSON row | | no | A debugging need. `bob ref show -f json` exists. |

### 5.2 The v1 keymap

The letters are fixed per format and case-insensitive. A row is hidden when its condition fails.

| Key | Row label | Copies (exact payload) | Shown when | Data source |
| --- | --- | --- | --- | --- |
| **`L`**, `↵`, `⌃Y` again | Wiki link | `RefItem.link`, verbatim | always | bob `link` |
| `O` | Obsidian URL | `ObsidianOpenURL.url(forAbsolutePath: noteURL)` | always | app (existing helper) |
| `R` | Reading task | `task.link`, verbatim | `task != nil` | bob `task.link` |
| `T` | Title | `rawTitle`, verbatim | always | bob `title` |
| `I` | ID (or **Stem**) | frontmatter `id`; if absent, the note stem, labelled "Stem" | always | bob `id` (new); fallback is the path's stem |
| `P` | PDF path | absolute PDF path | PDF not missing | app (`pdfURL`) |
| `N` | Note path | absolute note path | always | app (`noteURL`) |
| `F` | PDF file | the PDF as a file on the pasteboard (`NSURL` file URL) | PDF exists on disk at press time | app |
| `U` | Source URL | `urls[0]` | `urls` non-empty | bob `urls` |
| `M` | Markdown link | plain `[rawTitle](urls[0])` + HTML `<a href>` | `urls` non-empty | composed from bob fields |
| `X` | arXiv ID | `arXiv:<id>` | `arxiv != nil` | bob `identity.arxiv` |
| `D` | DOI | `<doi>` | `doi != nil` | bob `identity.doi` |
| `1`–`9` | Note N | `> quote` + blank line + comment (Markdown) | the note is hydrated | bob `ref show -c` |
| `⇧1`–`⇧9` | Note N, quote only | the quote text | same | same |
| `⌥1`–`⌥9` | Note N, Obsidian link | the annotation `link`, verbatim | `link` decoded | bob `ref show` `annotations[].link` |
| `A` | All notes (Markdown) | stdout of `bob ref show <path> -f markdown` | `annotationCount > 0` | bob (new fetch lane) |
| `esc`, `⌃[` | Close the card only | — | — | — |

Why these letters:

- Every letter is the first letter of its label: **L**ink, **O**bsidian, **R**eading task,
  **T**itle, **I**D, **P**DF path, **N**ote path, **F**ile, **U**RL, **M**arkdown, **X** (as in
  arXiv), **D**OI, **A**ll.
- No two rows share a first letter, so there's nothing to memorise beyond reading the label.
- Digits are reserved for the one variable-length list (notes). Letters never shift and digits
  never collide with formats.

### 5.3 Deliberately left out of v1

These are alias links (`⌥L`), vault-relative paths (`⌥P`/`⌥N`), narration, citations/BibTeX,
Highlights page links, research refs, and excerpts. Each one is either rare in the current
library, needs bob to grow a field first, or would make the app format something bob should own.
The keymap leaves room for all of them without moving any v1 letter.

---

## 6. Interaction design

### 6.1 Opening

- **`⌃Y`** with an available selected row opens the card. Exception: if the field editor is
  composing (IME marked text), `⌃Y` passes through. This mirrors the `⌃D`/`⌃U` rule.
- With **no selection or an unavailable row**, the key is consumed (it must never reach the
  field's `yank:`) and the footer toasts "Nothing to copy". No card opens.
- On open, the model **snapshots** the entries (A3). It also kicks inspector hydration
  immediately for the selected row, skipping the 120 ms settle, so notes arrive while you read the
  card. When `annotationCount > 0` it **prefetches** the `A` digest on its own `refs-copy` lane.
  Prefetching hides the ~0.25 s `bob` spawn behind the user's reading time.

### 6.2 Choosing (single keypress)

- **`⌃` is transparent inside the card.** `⌃Y` then `L` and `⌃Y` then `⌃L` both copy the wiki
  link. Holding Control through a chord is idiomatic (Emacs `C-x C-s`), and people who keep
  their finger on `⌃` after `⌃Y` should not be punished.
- **`⇧` and `⌥` only modify digits.** On letters they are ignored (`⇧L` = `L`), so Caps Lock and
  stray Shift are harmless. Holding `⌥` or `⇧` **live-morphs the notes previews**: a 0.12 s
  crossfade to the block link or the bare quote, driven by a `.flagsChanged` monitor that is
  installed only while the card is up. The legend in the notes header highlights the active
  modifier. This follows the native macOS idiom of holding Option to reveal alternate menu items,
  rendered visibly.
- **`↵` or a second `⌃Y`** copies the default row (Wiki link, marked with a small `↵` badge).
  That is `yy` for Vim hands.
- **Known-but-hidden key** (`U` on a chat): the card stays open and the footer reads "This
  reference has no source URL". Copying nothing is better than copying the wrong thing.
- **Unknown key:** swallowed. While the card is open, **no key reaches the search field or the
  list.** Navigation keys (`⌃N`, `⌃P`, `↑`, `↓`) do nothing; the card has no cursor, because it
  is a keypress menu, not a list. Mouse users click a row, and VoiceOver users activate rows as
  buttons.
- **A digit whose note hasn't hydrated yet:** the notes section shows a shimmering placeholder
  row, and digits stay inert until notes arrive. If `ref show` fails, a dim "Notes unavailable"
  row appears and the digits stay inert.

### 6.3 Feedback and closing

1. The pressed key's keycap fills with the accent colour (80 ms) and the row background flashes
   the accent at 18% opacity.
2. The pasteboard is written, and the write's return value is checked.
3. The card fades out (120 ms `easeOut`, no scale under Reduce Motion).
4. The footer toast becomes a **success toast**: a green `checkmark.circle.fill`, "Copied wiki
   link", and a dim, middle-truncated preview of what was copied. It lasts 1.5 s, as today, and
   VoiceOver announces "Copied wiki link".
5. If the write fails, the card stays and the toast turns orange: "Couldn't copy. Try again."

For **`A`** (async):

- If the prefetch has finished, `A` behaves like any other key.
- Otherwise the `A` row shows a mini spinner and "Asking bob…", and the card stays until the
  fetch completes, then copies and closes.
- **If the card closes, the panel hides, or the selection changes before the fetch completes, the
  result is discarded and the pasteboard is never touched.** A late write that clobbers whatever
  the user copied in the meantime is the worst reliability bug this feature could have, and it is
  the one I'd test hardest.

**Esc / `⌃[`** closes the card and nothing else. The panel's Esc ladder (banner → query → scope →
close) resumes on the next press. Clicking the scrim outside the card also closes it. Hiding the
panel discards the card. `prepareForPresentation` resets it, matching how the panel's other
transient state resets on every show.

---

## 7. Visual design

### 7.1 Placement and chrome

- The card sits **over the content well, centred horizontally, top-aligned 20 pt below the
  search bar.** It always appears in the same place, so the eye learns where to land. It does
  not hang off the selected row (`⌘K`'s anchor), because a tall card near a low row would clip.
- **Width:** `min(wellWidth − 48, 600)`. **Height:** fits the content, capped at the well height
  minus 32 (the notes section scrolls if it ever exceeds that).
- **Card surface:** `.thickMaterial`, radius 14, hairline `.primary.opacity(0.10)` stroke, soft
  shadow (radius 24, y 8, opacity 0.18).
  - It does not use `.glassEffect`: the repo already notes that it blanks `ImageRenderer` design
    fixtures, and the panel's glass already lives on the `NSGlassEffectView` shell.
  - Under Reduce Transparency the card goes opaque `windowBackgroundColor`.
- **Scrim:** the list and inspector dim under `Color.black.opacity(0.10)` (light mode) or `0.28`
  (dark mode). There is no blur; blur costs frames on every show and adds little.
- **Motion:** 0.14 s fade plus a 6 pt rise on open; 0.12 s fade on close. Under Reduce Motion,
  fades only.

### 7.2 Rows and type

These choices reuse the app's existing tokens, so the card reads as part of the same family as
the picker and pull-in cards.

- **Header (44 pt):** the kind tile (28 pt, kind tint, same as list rows). Above the title, a
  small `COPY` label (`.caption2.weight(.semibold)`, secondary, tracking +0.5). The title is
  `.headline`, one line, tail-truncated. An `esc` keycap sits on the right.
- **Section labels:** `LINK`, `IDENTITY`, `FILES`, `SOURCE`, `YOUR NOTES` in `.caption.weight(
  .semibold)`, secondary. This is the inspector's "YOUR NOTES" style.
- **Row (30 pt):** keycap, label, preview, optional trailing badge.
  - **Keycap:** 22 × 20 pt, `.caption.monospaced().weight(.semibold)`, `.background.opacity(0.6)`
    in a 5 pt rounded rectangle with a 0.5 pt `.primary.opacity(0.12)` border. These are the
    `CapturePickerKeyHints` keycap tokens, slightly larger.
  - **Label:** fixed 104 pt column, `.callout`, primary.
  - **Preview:** `.callout`, secondary.
    - Monospaced `.footnote` for code-like values (links, IDs, paths, URLs).
    - Proportional for titles and quotes.
    - Paths and URLs truncate in the middle (the stem is the informative part); text truncates
      at the tail.
    - `.help(value)` shows the full value on hover.
- **Notes rows:** `[1]`, then a `p. 29` chip (`.caption2`, tertiary), then the quote in italics
  with the inspector's 2 pt yellow leading bar, then ` — ` and the comment in secondary. One line,
  tail-truncated.
- **Hover:** the row gets a `.primary.opacity(0.06)` rounded fill and a pointing-hand cursor. A
  click copies.
- **Card footer (24 pt, caption, tertiary):** `⌃Y again · wiki link     ⌥ link · ⇧ quote     esc
  close`. The `⌥`/`⇧` group appears only when notes are present.

### 7.3 Mockups (real data from the vault)

**A. The common case: a chat, no notes, no source** (89% of the library)

```text
╭──────────────────────────────────────────────────────────────────────────────────────╮
│ ⌕  wave 2                                          [All]               1 of 406       │
├──────────────────────────────────────────────────────────────────────────────────────┤
│░░░░░░░░╭────────────────────────────────────────────────────────────────╮░░░░░░░░░░░░│
│░░░░░░░░│ [💬]  COPY                                                 esc │░░░░░░░░░░░░│
│░░░░░░░░│       Wave 2: The Ten Applications to Send Next (October 20…   │░░░░░░░░░░░░│
│░░░░░░░░│                                                                │░░░░░░░░░░░░│
│░░░░░░░░│ LINK                                                           │░░░░░░░░░░░░│
│░░░░░░░░│ [L] Wiki link      [[ref/chat/second_wave_job_applications]] ↵ │░░░░░░░░░░░░│
│░░░░░░░░│ [O] Obsidian URL   obsidian://open?path=/Users/…ications.md    │░░░░░░░░░░░░│
│░░░░░░░░│ [R] Reading task   [[job_search_2026#^ref-second-wave-job-a…]] │░░░░░░░░░░░░│
│░░░░░░░░│ IDENTITY                                                       │░░░░░░░░░░░░│
│░░░░░░░░│ [T] Title          Wave 2: The Ten Applications to Send Next…  │░░░░░░░░░░░░│
│░░░░░░░░│ [I] ID             second_wave_job_applications                │░░░░░░░░░░░░│
│░░░░░░░░│ FILES                                                          │░░░░░░░░░░░░│
│░░░░░░░░│ [P] PDF path       /Users/bryan/bob/lib/chat/…_applications.pdf│░░░░░░░░░░░░│
│░░░░░░░░│ [N] Note path      /Users/bryan/bob/ref/chat/…_applications.md │░░░░░░░░░░░░│
│░░░░░░░░│ [F] PDF file       second_wave_job_applications.pdf · 1.6 MB   │░░░░░░░░░░░░│
│░░░░░░░░│ ─────────────────────────────────────────────────────────────  │░░░░░░░░░░░░│
│░░░░░░░░│ ⌃Y again · wiki link                                 esc close │░░░░░░░░░░░░│
│░░░░░░░░╰────────────────────────────────────────────────────────────────╯░░░░░░░░░░░░│
├──────────────────────────────────────────────────────────────────────────────────────┤
│ L T I P … copy  ·  esc close                                       Updated 2m ago      │
╰──────────────────────────────────────────────────────────────────────────────────────╯
```

**B. A paper with a source and notes**, with `⌥` held (the notes previews have morphed to block
links)

```text
╭────────────────────────────────────────────────────────────────╮
│ [🎓]  COPY                                                 esc │
│       Agentic Software Engineering: Foundational Pillars and…  │
│ LINK                                                           │
│ [L] Wiki link      [[ref/papers/agentic_software_engineering]] ↵│
│ [O] Obsidian URL   obsidian://open?path=/Users/…engineering.md │
│ [R] Reading task   [[sase#^ref-agentic-software-engineering]]  │
│ IDENTITY                                                       │
│ [T] Title          Agentic Software Engineering: Foundational… │
│ [I] ID             agentic_software_engineering                │
│ FILES                                                          │
│ [P] PDF path       /Users/bryan/bob/lib/papers/…engineering.pdf│
│ [N] Note path      /Users/bryan/bob/ref/papers/…engineering.md │
│ [F] PDF file       agentic_software_engineering.pdf · 5.3 MB   │
│ SOURCE                                                         │
│ [U] Source URL     https://arxiv.org/abs/2509.06216            │
│ [M] Markdown link  [Agentic Software Engineering: Fo…](https:…)│
│ [X] arXiv ID       arXiv:2509.06216                            │
│ YOUR NOTES  2                              ⇧ quote  [⌥ link]   │
│ [1] p. 28  [[ref/papers/agentic_software_engineering#^h-c014…]]│
│ [2] p. 29  [[ref/papers/agentic_software_engineering#^h-56c9…]]│
│ [A] All notes      Markdown digest from bob · 2 highlights     │
│ ─────────────────────────────────────────────────────────────  │
│ ⌃Y again · wiki link     ⌥ link · ⇧ quote          esc close   │
╰────────────────────────────────────────────────────────────────╯
```

With no modifier held, row 2 reads `[2] p. 29  ▍Listing 2. A Consultation Request Pack (CRP)… —
This is a LOT like gates!`.

**C. After pressing `2`** (the card is gone; the footer confirms)

```text
├──────────────────────────────────────────────────────────────────────────────────────┤
│ ✓ Copied note 2 · > Listing 2. A Consultation Request Pack (CRP) for an archi…        │
╰──────────────────────────────────────────────────────────────────────────────────────╯
```

### 7.4 Optional polish (phase 3)

- **Inspector echo:** while the card is up, the inspector's visible notes get matching `1`, `2`,
  `3` keycaps where the yellow bar starts. Pressing a digit pulses that note's yellow bar. The
  copied thing lights up where it lives, which is the most "beautiful" moment this feature can
  have. It is optional because the card is already self-sufficient (and must be, at narrow widths
  with no inspector).
- **Footer hint:** add `⌃Y Copy` to the footer hints, before `⌘S Scan`. Today's hint string is
  `↵ Open in Highlights  ⌘↵ Note  ⌥↵ Reveal  ⌘K Actions  ⌘S Scan  ⌘1–5 Scope  esc Close`.

### 7.5 Accessibility

- The card is one modal container: `accessibilityLabel("Copy menu for <title>")`,
  `.accessibilityAddTraits(.isModal)`.
- Each row is a button labelled `"<label>, <full value>, key <K>"`. For example: "Wiki link,
  [[ref/chat/…]], key L". The file row reads "PDF file, <name>, key F".
- On open, announce "Copy menu. Press a letter or number." On copy, announce "Copied <label>."
- Keycaps and previews keep `.monospacedDigit()`. Increased Contrast raises the keycap border to
  0.35 opacity, matching the divider rule in `RefsPanelView`.

---

## 8. Alternatives considered

| Approach | Verdict | Why |
| --- | --- | --- |
| **Extend `⌘K` (`NSMenu`) with key equivalents** | Rejected as the core | Native and cheap, but it can't show previews of values or morph them while a modifier is held. It keeps the resign-key suspension hack. Typed letters in an open `NSMenu` drive type-select rather than reliably firing items. It's also the menu Bryan is trying to get away from. |
| **Obsidian-style filtered picker** (the `YankPathPickerModal` pattern) | Rejected for the panel | Type-to-filter conflicts with the "single keypress" requirement and with the panel's own search field. It's still worth borrowing its *exact-value previews*. |
| **Vimium-style hint badges on the inspector** | Adopted as optional polish (§7.4) | Beautiful in place, but it fails without an inspector (< 760 pt), and most formats (wiki link, ID, Obsidian URL, file) have no visible element to badge. |
| **Direct chords, no menu** (`⌃⇧L` for link, …) | Rejected | Zero discoverability, and a dozen global-ish chords to remember. The card *teaches* the letters, so chord-like speed returns via `⌃Y` `L`. |
| **Copy app-side from the note file** (read frontmatter for `id`) | Rejected | Violates `mac-capture-is-a-thin-client` and the README's "never parses frontmatter or note bodies". It would also create a second, drifting definition of the ID. |

---

## 9. Architecture and contracts

### 9.1 bob-cli (phase 1, small)

- `src/native/ref_library/row.rs`: serialize `id` (drop `#[serde(skip_serializing)]`). Keep
  `null` when absent, the same as every other optional on the row. It is additive under
  `schema_version` 1, the same precedent as `blocked` and `task` ("`blocked` and `task` are
  additive under `schema_version` 1").
  - Name it `id`. That mirrors the frontmatter key and the `bob ref show <id>` vocabulary, the
    way `author`, `published`, and `captured` mirror theirs.
  - Document in `docs/ref.md` that it is the marker/frontmatter ID and **not** the row's key (the
    key is `path`).
- Update the JSON goldens and tests that pin the row shape (`ref_library/tests.rs`,
  `output.rs`).
- **No other bob change is needed for v1:**
  - `ref show` JSON already carries `annotations[].block_id` and `.link`;
  - `-f markdown` already exists.

### 9.2 bob-mac-capture (phases 2–3)

**Decoding (RefsCore, Linux-testable):**

- Add `id` to `RefRecord` as `markerID` (`decodeIfPresent`). Also add it to `encode(to:)`, or the
  snapshot cache drops it until the next refresh. Thread it through to `RefItem.markerID`,
  including the `RefsCatalog` rebuild that copies every field by hand (a classic place to forget
  one).
- Add `blockID` and `link` to `RefsShowAnnotation` (`decodeIfPresent`).
- Add `func showMarkdown(path:) async throws -> String` to `RefsFetching`. It runs on a new
  `refs-copy` lane, so inspector loads never cancel it and it never cancels them.

**The menu as a pure value (RefsCore):**

```swift
public enum RefsCopyPayload: Equatable, Sendable {
    case text(String)
    case richLink(plain: String, html: String)
    case file(path: String)                 // absolute; existence re-checked at press time
    case bobMarkdown(notePath: String)      // resolved through the refs-copy lane
}

public enum RefsCopyNoteVariant: Equatable, Sendable { case markdown, quote, link }

public enum RefsCopyFormat: Equatable, Hashable, Sendable {
    case wikiLink, obsidianURL, readingTask, title, markerID, stem
    case pdfPath, notePath, pdfFile, sourceURL, markdownLink, arxivID, doi
    case note(index: Int)                   // 1…9; the variant comes from the key's modifiers
    case allNotes
}

public struct RefsCopyEntry: Equatable, Sendable {
    public let format: RefsCopyFormat
    public let key: Character               // fixed per format; never reassigned
    public let label: String                // "Wiki link", "ID" or "Stem", "Note 2"…
    public let payload: RefsCopyPayload     // frozen at open (A3)
    public let preview: String              // drawn from payload; the view only truncates
    public let isDefault: Bool
}

public struct RefsCopySection: Equatable, Sendable {
    public let title: String                // LINK, IDENTITY, FILES, SOURCE, YOUR NOTES
    public let entries: [RefsCopyEntry]
}

public enum RefsCopyMenu {
    /// Pure: the item, resolved absolute paths, the missing-PDF flag, and
    /// hydrated notes in; sections out. Rows that don't apply are omitted.
    public static func sections(for item: RefItem, context: RefsCopyContext) -> [RefsCopySection]
    /// Why a known key has no row for this item ("no source URL"), or nil.
    public static func absenceReason(for key: Character, item: RefItem) -> String?
}
```

**Keys:**

- `RefsKeyRouter`: add `case KeyCode.y (16): flags == .control ? (marked ? nil : .showCopyMenu) :
  nil`.
- Add a sibling `RefsCopyKeyRouter.command(keyCode:characters:modifiers:)` that returns
  `.copy(key, variant)`, `.copyDefault`, `.close`, or `.ignore`.
  - Match mnemonic letters on `charactersIgnoringModifiers`, lowercased, so they follow the typed
    letter on non-QWERTY layouts.
  - Match digits on key code, so `⇧1` stays "1" on any layout.
  - Strip `⌃` before matching, except for `⌃[` and `⌃Y`.

**Model (`RefsPanelModel`):**

- `@Published private(set) var copyMenu: RefsCopyMenuState?`. The state holds the frozen sections,
  the item id, the held modifiers, and the pending `A` task.
- New commands: `.showCopyMenu` and `perform(_ copy: RefsCopyCommand)`.
- The toast becomes a small struct `{ kind: .success | .failure, title, preview? }`, and
  `prepareForPresentation()` clears `copyMenu`.

**Controller (`RefsPanelController.processKeyEvent`):**

- While `copyMenu != nil`, route *every* `keyDown` to `RefsCopyKeyRouter` and return `nil`, so
  nothing reaches the field.
- Add `.flagsChanged` to the local monitor mask while the card is up, so the `⌥`/`⇧` morph works.

**Pasteboard:** extend `RefsPasteboardWriting` to `copy(_:) -> Bool`, `copyRichLink(plain:html:)
-> Bool`, and `copyFile(_ url:) -> Bool`. The live implementations:

- `clearContents()` followed by `setString` (or `writeObjects([url as NSURL])` for files).
- For rich links, one `NSPasteboardItem` carrying both `.string` and `.html`.

The test fake records every call, which proves the bytes match the preview.

**View:** a `RefsCopyCard` overlay in `RefsPanelView` (a `ZStack` over `well`) with the scrim.
`RefsFooter` gains the success/failure toast and the `⌃Y Copy` hint.

**`⌘K`:** replace `.copyWikiLink` and `.copyPDFPath` with `.copyMenu` ("Copy…", key equivalent
`y` + `.control`, which displays as `⌃Y`). Update `RefsInspectorTests`' section assertions.

### 9.3 Reliability invariants (make these the tests)

1. **Preview = payload.** For every entry, the string that reaches the fake pasteboard equals
   `entry.preview` before visual truncation. This holds for fixtures covering a chat with no
   notes, a paper with a source and notes, a row with no ID (Stem fallback), a missing PDF, and a
   v1 tracker row.
2. **Frozen at open.** Publishing a changed library while the card is open changes no payload.
3. **No late writes.** The `A` fetch completes after Esc, after a hide, or after
   `prepareForPresentation`, and the pasteboard is never written.
4. **Keys never leak.** With the card open, printable keys, `⌫`, and `⌃N` leave the query and
   the selection unchanged.
5. **Letters are stable.** For any two items, a format has the same key. Absent formats produce
   an `absenceReason` and do not fall through to another format.
6. **IME:** `⌃Y` while marked text is present passes through (returns nil).
7. **Old bob:** a `ref list` row without `id` decodes, and the `I` row reads "Stem". A `ref show`
   annotation without `link` hides the `⌥` variant for that note.

---

## 10. Testing and verification

- **RefsCore (runs on apollo/athena via `just portable-check`):**
  - menu composition per fixture;
  - `absenceReason`;
  - key → format mapping;
  - Markdown note formatting;
  - decoding of `id`, `block_id`, and `link`;
  - snapshot round-trip of `markerID`.
- **BobMacCaptureTests (macOS CI):**
  - the router (`⌃Y` and the IME case);
  - copy-mode swallowing;
  - `perform(.copy…)` against the fake pasteboard, including the rich and file payloads;
  - toast text;
  - `A` prefetch, spinner, and late-discard;
  - the `⌘K` section shape.
- **Design fixtures (`RefsPanelDesignTests` via `ImageRenderer`):**
  - card A and card B;
  - `⌥` held;
  - Stem fallback;
  - narrow panel (no inspector);
  - dark mode;
  - Reduce Transparency;
  - the success and failure toasts.
- **Manual Mac checklist** (per `AGENTS.md`, compile a scratch copy on the Mac and never use
  Bryan's checkout). Check each of these by hand:
  - `F` pasted into Finder, Mail, Slack, and Messages;
  - `M` pasted into Slack, Obsidian, and Terminal;
  - `⌃Y` then `⌃L` with Control held throughout;
  - VoiceOver row labels;
  - `A` on the 16-comment report.
- **Highlights spike (5 minutes, on the Mac, by Bryan):**
  `open 'highlights://agentic_software_engineering#page=29'`. Note whether it opens that PDF at
  page 29 when Highlights is closed, open, or has the document open. If it does, bob can keep the
  sidecar's page URL per annotation, and `⌘`+digit can copy a page deep link in a later phase.

---

## 11. Phasing

| Phase | Repo | Scope | Size |
| --- | --- | --- | --- |
| 1 | bob-cli | Emit `id` in `ref list` JSON, docs, goldens | S |
| 2 | bob-mac-capture | RefsCore copy model and decoding (`markerID`, `blockID`, `link`, `showMarkdown`), routers, model, pasteboard writer, `⌘K` consolidation, footer hint and toast, tests | M |
| 3 | bob-mac-capture | `RefsCopyCard` visuals and motion, the `⌥`/`⇧` morph, accessibility, design fixtures, README keyboard table and a "Copying" subsection, optional inspector echo | M |
| 4 (optional) | both | Highlights page deep links (after the spike), `link_titled` alias links (`⌥L`), vault-relative paths, `research:` refs, `bob ref cite` | — |

Phase 2 can ship before phase 1 lands, because the ID row falls back to "Stem". That keeps the
cross-repo dependency soft.

**A follow-up worth considering:** give the Obsidian `⌘Y` yank picker (bob-plugins) the same
single-letter accelerators (`L`, `T`, `I`, `P`, `N`) when the active file is a ref note. The same
letter would then copy the same thing in both surfaces.

---

## 12. Open questions for Bryan

1. **Default format:** I chose the wiki link for `⌃Y ⌃Y` / `↵`. If you copy the ID more often,
   make the ID the default instead. The rest of the design is unaffected.
2. **What a note copies by default:** I chose quote + comment as Markdown, which matches what the
   inspector shows and feeds agent prompts. If you mostly quote authors, swap the plain and `⇧`
   variants.
3. **Path style:** absolute (today's `⌘K` behaviour) or `~`-compacted (your Obsidian picker lists
   "Absolute path with tilde" first)? I kept absolute for continuity. Either way, the preview
   shows exactly what gets copied.
4. **Should `A` copy all highlights (no `-c`) or only commented ones?** I chose all, labelled
   "All notes · N highlights". The digits are your commented notes.

---

## 13. Recommended solution

**Ship a which-key style Copy card on `⌃Y`.** It opens over the Bob Refs content well and maps
fixed, first-letter mnemonics to curated formats:

- **L**ink (the default; `↵` or a second `⌃Y` also copy it);
- **O**bsidian URL;
- **R**eading task;
- **T**itle;
- **I**D (marker `id`, falling back to the labelled Stem);
- **P**DF path;
- **N**ote path;
- the PDF **F**ile itself.

Conditional rows add **U**RL, **M**arkdown link (rich), ar**X**iv, and **D**OI when bob reports a
source, plus **`1`–`9`** for your notes (with `⇧` for the quote only and `⌥` for the Obsidian
block link) and **A**ll notes as bob's Markdown digest.

How it behaves:

- Every row previews its exact payload, and the payloads are frozen when the card opens.
- One keypress copies, flashes the row, closes the card, and confirms in the footer. The panel
  stays open.
- `⌃` is transparent inside the card, unknown keys are swallowed, and absent formats explain
  themselves instead of copying something else.
- The async digest never writes the clipboard after you've moved on.
- `⌘K`'s two copy items collapse into a single "Copy… ⌃Y" entry.

Build order: bob-cli first emits the marker `id` in `bob ref list` JSON (additive, schema 1).
The app then decodes `id`, `block_id`, and `link` and builds the card. Its logic lives in
Linux-testable `RefsCore`, and its visuals are pinned by `ImageRenderer` fixtures. Highlights
page deep links are the most exciting next step, gated on a five-minute spike: Highlights does
register the `highlights://` scheme, but its page behaviour is unverified.

---

### Sources

- bob-mac-capture `44051a0`:
  - `Sources/BobMacCapture/Refs/RefsKeyRouter.swift`, `RefsActionsMenu.swift`,
    `RefsPanelModel.swift`, `RefsPanel.swift`, `RefsPanelView.swift`, `RefsFooter.swift`,
    `RefsInspectorView.swift`, `RefsVisualTokens.swift`;
  - `Sources/RefsCore/RefsModel.swift`, `RefsDecoding.swift`, `RefsInspector.swift`,
    `RefsFetching.swift`;
  - `Sources/CaptureCore/ObsidianOpenURL.swift`;
  - `Sources/BobMacCapture/CapturePullInChoiceView.swift` (keycap tokens);
  - `README.md` §Bob Refs.
- bob-cli `f24d5e7`:
  - `src/native/ref_library/row.rs` (the `id` skip), `mod.rs`, `resolve.rs`, `show.rs`;
  - `docs/ref.md` (the `ref show` JSON and row contract, and the additive-field precedent);
  - `docs/highlights-ref-sync.md` (marker grammar, `--include-id`, `highlights://` sidecar
    links).
- bob-plugins: `plugins/bob-navigation-hotkeys/src/{010-requires-and-config,100-yank-and-paths,
  200-filtered-picker-modals,490-plugin-lifecycle,640-plugin-notes-and-task-move}.js` (the
  `Mod+Y` copy-path picker).
- Live data: `bob ref list -R all -A -f json` and `bob ref show … -f json|markdown` on apollo
  (2026-10-14); `PlistBuddy` on `/Applications/Highlights.app/Contents/Info.plist` (Mac,
  Highlights 2026.1.2).
- Prior research: `research:202610/highlights_quick_open_refs_panel/highlights_quick_open_refs_panel__final.md`.
- Decision: `decisions:mac-capture-is-a-thin-client`.
- Web:
  - [Highlights on the App Store](https://apps.apple.com/us/app/highlights-extract-pdf-notes/id1498912833)
    (no public URL-scheme docs found);
  - [GNU ELPA: which-key](https://elpa.gnu.org/packages/which-key.html) and
    [Emacs manual: Key Help](https://www.gnu.org/software/emacs/manual/html_node/emacs/Key-Help.html)
    (the prefix-then-popup pattern);
  - [one-key.el](https://github.com/vapniks/one-key) (the single-key popup menu precedent).
