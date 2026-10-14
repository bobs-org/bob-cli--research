# Ctrl+Y should open a Refs yank card, not a second actions menu

- **Date:** 2026-10-14
- **Researcher:** `grk` (swarm `research.19`)
- **Question:** How should Bob Mac Capture's Refs panel grow a `<ctrl+y>` keymap that opens a single-keypress menu of clipboard payloads for the selected reference, and is that the right product at all?
- **Verdict in one line:** Yes, ship a dedicated **yank card** on `⌃Y`; no, do not grow ⌘K, do not pop another `NSMenu`, and do not flatten every highlight onto the first screen.

---

## 1. Recommendation

Add `⌃Y` as the Refs panel's **copy verb**. It opens a small glass **yank card** over the selected row. Each visible row has a single letter (or digit) accelerator. Pressing that key copies one bob-authored string, toasts the footer, and dismisses the card. The Refs panel stays up.

The card is a closed catalog of identity payloads with a live preview of the bytes that will land on the pasteboard. A second **Notes** layer, opened with `N`, is the only nested step, and only when the selected row has comments.

This is the same interaction family as the capture picker's letter-free rows and the Obsidian decay / task-action **card** (letter accelerators, no focused search box). It is the opposite of ⌘K, which is already an `NSMenu` of *opens and library verbs*.

**Do this in Bob Mac Capture only for v1.** Identity copies are already on `RefItem`. Notes copies reuse the inspector's `bob ref show -c` LRU. Do not spawn `bob ref marker` on the hot path. Do not invent capture grammar (`@route:id`) in Swift.

---

## 2. Critique of the original plan

The original plan is the right *verb* with the wrong *noun*.

What is right:

- Copying from Refs is a real gap. Return / ⌘Return / ⌥Return open things. ⌘K's middle section already has **Copy Wiki Link** and **Copy PDF Path**, but they are buried among Open Source URL, Open Narration, Open in Default App, Refresh, and Scan, they have empty `keyEquivalent`s, and they cannot preview the payload.
- A dedicated chord plus a **single extra keypress** is the right budget. Bryan already lives in that language: capture pickers, the freshness decay card, and Obsidian's `Yank … path` commands (`bob-navigation-hotkeys`: absolute, `~/`-absolute, relative, basename, stem, parent).
- The interesting payloads are richer than two strings. A paper such as `ref/papers/agentic_software_engineering.md` already carries a wiki link, a PDF path, a marker `id:`, a source URL, an arXiv id, a reading-task link, and commented highlights with vault block ids `h-…`.
- Beauty belongs in the brief. The Refs panel is a glass `NSPanel` with kind tints, keycap hints, and 1.5 s copy toasts. A system `NSMenu` on top of that glass is the ⌘K compromise, not a second product.

What is wrong, and should change:

| Original requirement | Problem | Adjustment |
| --- | --- | --- |
| "A new menu" | ⌘K is already `NSMenu.popUp` under the selected row, with `suspendHideOnResign`. A second `NSMenu` is a twin of ⌘K with copy items. It cannot show two-line payload previews, it does not snapshot in `RefsPanelDesignTests`, and it fights the glass. | **Yank card**: SwiftUI overlay in the panel, capture-picker chrome, letter accelerators, payload preview. |
| Every property on one screen (marker id, notes, highlights, …) | Hick's law. Live vault (2026-10-14): 406 PDF-backed rows; 358 have zero comments; 3 have 10–16. Dumping notes onto the identity screen punishes the common case. | **Two layers.** Identity is one chord + one letter. Notes is `N` then `1`–`9`. |
| "Be creative" as unbounded | Fifteen copy targets looks busy and trains nothing. `DOI` is present on **0** of 406 PDF-backed rows. Synthesizing `@sase:ref-…` capture tokens would violate `decisions:mac-capture-is-a-thin-client`. | Closed catalog of **bob-authored** strings, hide missing rows, format only citations. |
| `⌃Y` named as if it were free | The search field is a live `NSTextField`. Cocoa binds `⌃Y` to `yank:` (paste from the kill ring). Today `RefsKeyRouter` returns `nil` for `⌃Y`, so the event reaches the field editor. The panel already intercepts `⌃N/P/J/K/D/U/[` for this reason. | **Must consume `⌃Y` in the local key monitor**, even before the card exists. Treat the intercept as a bugfix. |
| Marker ID via PDF parse | `bob ref marker` reads the page-1 `/Text` annotation. That is a subprocess + PDF parse, not a 50 ms JSON field. Frontmatter `id` is already indexed and **skipped from JSON** (`RefRow.id` is `#[serde(skip_serializing)]`). `RefItem.stem` is the PDF filename stem and matches `id:` on every `bob ref create` paper/blog sampled. Agent-report chats often have no `id:` key at all. | v1 copies `item.stem`, labeled **Marker ID** when it equals the known id, **PDF stem** otherwise. Optional additive JSON later. Never parse the PDF in Swift. |

The idea is a good idea. A second ⌘K, or a kitchen-sink list of every highlight, would be a bad implementation of it.

### Would I take a different approach?

Three alternatives I considered and rejected as the *primary* design:

1. **Grow ⌘K** with letter key-equivalents (`l` wiki, `p` path, …). Cheapest. It keeps copy mixed with Scan, it cannot preview, and `⌃Y` in the search field stays a silent paste bug.
2. **Immediate copy on `⌃Y`** (wiki link) with no menu. Fastest for the 80% case, undiscoverable for marker id / citation / notes, and it trains the wrong muscle: "Y always copies one secret default."
3. **Unmodified `y` in browse mode**, Vim-style. Conflicts with typing `y` into an empty query the moment the user starts a search, and the panel's contract is "printables always fall through to the search field" (`RefsKeyRouter`).

Companion I *would* take, as a small extra, not a replacement: **⌘C copies the wiki link when the search field has an empty selection.** Native copy still wins when the query is selected. That is how many filter palettes behave. It does not replace the card.

---

## 3. What exists today (verified)

### 3.1 Keyboard table

`RefsKeyRouter` is the §12 table. Mapped control chords today:

| Chord | Command |
| --- | --- |
| `⌃N` / `⌃J` | next row |
| `⌃P` / `⌃K` | previous row |
| `⌃D` / `⌃U` | inspector page |
| `⌃[` | escape |
| `⌘K` | `showActions` → `NSMenu` |
| `⌘R` / `⌘S` | refresh / scan |
| `⌘1`–`⌘5` | scope |
| Return / ⌘Return / ⌥Return | open Highlights / note / Finder |

`y` is unmapped. `RefsKeyRouterTests` already enumerates every mapped chord; `⌃Y` is a one-case add.

⌘K (`RefsActionsMenu`) sections for a typical row:

1. Open in Highlights, Open Note, Reveal in Finder
2. **Copy Wiki Link**, **Copy PDF Path**, optional Open Source URL / Open Narration
3. Open in Default App, Refresh Library, Scan

Copy already writes through `RefsPasteboardWriting` (`clearContents` + `.string`) and toasts for 1.5 s (`Copied wiki link` / `Copied PDF path`). Tests inject `FakePasteboard`. That pipeline is the one to extend, not replace.

Footer hints (`RefsFooter.hintsText`):

```
↵ Open in Highlights  ⌘↵ Note  ⌥↵ Reveal  ⌘K Actions  ⌘S Scan  ⌘1–5 Scope  esc Close
```

It already truncates. When the yank card is open, **replace** this string with the card's own hints rather than appending `⌃Y Copy` into a line that cannot hold it. Idle footer can shorten `⌘K Actions` to `⌘K` and insert `⌃Y Copy` in that saved space.

### 3.2 The library, not the PDF folder

Live `bob ref list -R all -A -f json` on 2026-10-14:

| Quantity | Count |
| --- | --- |
| Indexed `ref/` notes | 1,008 |
| PDF-backed (what Refs lists) | 406 |
| PDF-backed chats / agent-reports | 362 |
| PDF-backed external | 44 |
| With a reading task + `task.link` | 405 |
| With comments | 48 (30 have 1–3, 15 have 4–9, 3 have 10–16, max 16) |
| With any annotations | 76 (max 29) |
| With `urls` | 27 |
| With arXiv | 9 |
| With DOI | **0** |
| With audio | 24 |
| With `research_ref` | 1 |

The Mac panel never lists non-PDF notes. Copy targets that only exist on zorg-era URL-only rows are out of scope.

`bob ref show -c -f json` already returns, per annotation:

```json
{
  "page_label": "Page 28",
  "kind": "highlight",
  "quote": "…",
  "comment": "Tale/epic plan frontmatter is missing “why”?",
  "block_id": "h-c014dc3c2edc",
  "link": "[[ref/papers/agentic_software_engineering#^h-c014dc3c2edc]]"
}
```

The Mac decoder (`RefsShowAnnotation`) currently keeps `page_label`, `kind`, `quote`, `comment` and **drops `block_id` and `link`.** Notes-layer wiki links are one additive `decodeIfPresent` away. Same for `research_ref` on `RefRecord` / `RefItem` (present in JSON, absent in Swift).

Inspector hydration already waits 120 ms after selection settle, then runs `bob ref show <path> -f json -c` with an LRU of 32. Yank must read that cache. It must not start a third show pipeline.

### 3.3 Marker ID is a YAML field, usually the stem

`bob ref marker` on `lib/papers/agentic_software_engineering.pdf`:

```
- status: ready
- parent: sase
- title: Agentic Software Engineering: Foundational Pillars and a Research Roadmap
- id: agentic_software_engineering
- source_url: https://arxiv.org/abs/2509.06216
- author: Ahmed E. Hassan et al.
- published: 2025-09-07
- captured: 2026-10-07
```

The note frontmatter `id:` is the same string. `RefItem.stem` is derived from the PDF filename and is also `agentic_software_engineering`.

Agent-report chats such as `ref/chat/xprompt_role_binding.md` have **no** `id:` key. Their Highlights identity is the PDF stem; their extra identity is frontmatter `research:` → JSON `research_ref` (`research:202608/xprompt_role_binding/xprompt_role_binding.md`).

So "copy the marker notes ID" in practice means: copy the stem, which is the marker `id` whenever `bob ref create` wrote one. Parsing the PDF to be sure is a reliability loss (timeout, missing Highlights, encrypted PDF) for a field the index already has.

### 3.4 Thin-client rule

`decisions:mac-capture-is-a-thin-client`: Bob Mac Capture owns presentation and pasteboard. `bob` owns identity. The app may format a citation from fields bob already sent. It may not parse marker YAML, mint `@route:id`, or regex wiki links.

Copy Wiki Link today already does the right thing: `pasteboard.copy(item.link)` verbatim.

### 3.5 Precedent inside Bryan's stack

- **Obsidian yank-path** (`bob-navigation-hotkeys`): a picker whose rows are `(title, preview, kind)` and whose accept writes the preview to the clipboard, then a Notice. That is the payload-preview pattern. Its chrome is the giant child-note palette, which is the wrong chrome for a closed set of about six formats — the same category error the Ctrl+Shift+P research called out.
- **Capture picker keycaps** (`CapturePickerKeyHints`): monospaced key in a 4 pt-radius rounded rect, caption action, footer swaps while the mode is open.
- **Refs copy toast**: footer text for 1.5 s, already tested.
- **⌘K anchor math**: `RefsPanelController.actionsAnchor` converts the selected row's SwiftUI rect into the unflipped content view. Reuse that point for the yank card's top-leading, then let the card flip up if it would clip the footer.

---

## 4. Copy catalog

Build one pure function, `RefsYankCatalog.rows(item:inspector:) -> [RefsYankRow]`, Linux-testable in RefsCore. A row is `{ key, title, payload, preview, layer }`. Omit a row when `payload` is empty. Absence stays absence, same honesty rule as the inspector facts.

### 4.1 Identity layer (first screen)

Default selection is **Wiki link**. Return copies it.

| Key | Title | Payload | When |
| --- | --- | --- | --- |
| `L` | Wiki link | `item.link` verbatim, e.g. `[[ref/papers/agentic_software_engineering]]` | always |
| `W` | Wiki with title | `[[target\|title]]` where `target` is `item.link` with the wrapping `[[` `]]` stripped **only if** they are present as a wrapping pair; otherwise skip this row rather than guess | `item.link` is a wrapping wikilink |
| `P` | PDF path | Absolute path (`library.pdfURL`), and also put a `file://` URL flavor on the pasteboard so Finder / Terminal receive a file | PDF exists |
| `I` | Marker ID | `item.stem` (PDF stem). Label **Marker ID** when it matches a known `id`, **PDF stem** otherwise | always (stem is required to be in the catalog) |
| `U` | Source URL | First `item.urls` entry, unmodified | `urls` nonempty |
| `A` | arXiv | `item.arxivID` (the id, `2509.06216`). A second flavor, the abs URL `https://arxiv.org/abs/<id>`, is acceptable as the string we copy if Bryan pastes into browsers more than into `bob ref find`; **copy the id**. `bob ref find` accepts both. Prefer the id: it is what the JSON stores. | `arxivID` set |
| `T` | Title | `item.rawTitle` | always |
| `C` | Citation | Deterministic one-liner from fields that exist: `Author (YYYY). Title. <url or arXiv or wiki link>` | always, because title + wiki always exist |
| `K` | Reading task | `item.task.link` verbatim, e.g. `[[sase#^ref-agentic-software-engineering]]` | task with a link |
| `O` | Obsidian URI | `obsidian://open?path=` + percent-encoded vault-relative note path (`item.id`) | always |
| `R` | Research ref | `research_ref` as bob sent it (`research:202608/…`) | field present (today: 1 PDF-backed row) |
| `S` | Summary | Inspector excerpt paragraph, or the joined Bottom-line bullets | inspector has a summary/abstract |
| `N` | Notes… | *opens layer 2* | `commentCount > 0` or inspector already has commented highlights |

Do **not** put on the first screen: DOI (zero hits), BibTeX, SHA256, parent route, audio path, synthesized `@route:id`, the PDF binary, "all highlights", page count, dates as standalone rows.

`C` citation recipe, in order, skipping missing pieces:

```
{author} ({year}). {title}. {url | arXiv:{id} | {wiki link}}
```

Year is the first four digits of `published` when it looks like `YYYY-…`. Chats without author/url become `Title. [[ref/chat/…]]`.

### 4.2 Notes layer (second screen, `N`)

Numbered `1`–`9` in note order, the same order the inspector pages. 45 of 48 commented rows fit in nine keys; the three outliers (10, …, 16 comments) get `1`–`9` plus `A` for all.

Each numbered key copies a paste-ready Markdown block built from bob's fields, no extra wording:

```markdown
> {quote}

{comment}

{link}
```

Omit the quote line when `quote` is empty (standalone notes). Omit the comment line when empty. Always keep `link` (`[[ref/…#^h-…]]`) when the decoder has it, so a paste into a daily note stays a first-class vault pointer.

Layer-2 extras:

| Key | Title | Payload |
| --- | --- | --- |
| `A` | All notes | The numbered blocks joined by a blank line, in order, uncapped |
| `Q` | Quotes only | Quotes joined, no comments |
| `H` | Highlight links | Each `link` on its own line |
| `esc` | Back | Identity layer, nothing copied |

If `N` is pressed before `ref show` has landed: keep the identity card up, show **Notes…** as `Loading notes…` with no accelerator until the LRU fills, then enable `N`. Do not block identity copies on the show spawn. Do not start a second show.

### 4.3 Worked example

Selected: *Agentic Software Engineering: Foundational Pillars and a Research Roadmap*.

```
┌ Copy · Paper · Agentic Software Engineering… ─────────────┐
│ L  Wiki link     [[ref/papers/agentic_software_engineering]] │
│ W  Wiki + title  [[ref/papers/agentic_software_engineering│  │
│                  Agentic Software Engineering…]]             │
│ P  PDF path      /Users/…/lib/papers/agentic_software_eng…   │
│ I  Marker ID     agentic_software_engineering                │
│ U  Source URL    https://arxiv.org/abs/2509.06216            │
│ A  arXiv         2509.06216                                  │
│ T  Title         Agentic Software Engineering: Foundational… │
│ C  Citation      Ahmed E. Hassan et al. (2025). Agentic…     │
│ K  Reading task  [[sase#^ref-agentic-software-engineering]]  │
│ O  Obsidian URI  obsidian://open?path=ref%2Fpapers%2Fagen…   │
│ N  Notes…        2 comments                                  │
│                                                              │
│  L copies   ↩ wiki link   N notes   esc close                │
└──────────────────────────────────────────────────────────────┘
```

`N` then `1` copies:

```markdown
> # Section 1: Goal & Why goal : objective : " Add rate limiting…

Tale/epic plan frontmatter is missing “why”?

[[ref/papers/agentic_software_engineering#^h-c014dc3c2edc]]
```

A chat such as `xprompt_role_binding` drops `U`/`A`/`K`'s blocked overlay does not matter, shows `I` as **PDF stem** (`xprompt_role_binding`), and shows `R` once `research_ref` is decoded.

---

## 5. Interaction design

### 5.1 Why a card, not `NSMenu`

⌘K must stay an `NSMenu`. It is a mixed verb list, it already works, and mouse users expect a menu there.

`⌃Y` is one verb, copy, with payloads that are the point of the UI. The row has to show the **bytes**. That is a two-line list (title + monospaced preview, truncation `.middle` on paths and URLs, `.tail` on titles). `NSMenuItem.view` can fake this and then VoiceOver, key-equivalents, and design-test snapshots all get worse.

The card:

- Width 420 pt, max height ~ 12 identity rows × 36 pt + 44 pt header + 30 pt footer, corner radius 12, `.regularMaterial`, 0.5 pt stroke, kind-tint 3 pt leading bar.
- Header: `Copy` + kind chip + two-line title.
- Rows: 22 pt keycap (capture picker's keycap language) + title + preview.
- Default row (wiki link) uses the same selection fill as the list.
- Arrow keys / `⌃N` `⌃P` `⌃J` `⌃K` move the selection inside the card. Return copies the selection. Letters copy that row even if another row is selected (accelerator wins, like a menu).
- `⌃Y` toggles: second press dismisses with no copy.
- `esc` / `⌃[` dismisses the card, then a second escape closes Refs, matching the existing Esc ladder (banner first, then panel).
- IME marked text: `⌃Y` passes through, same as Return.
- No selection / empty snapshot: consume the key, no card, no toast.
- After a successful copy: dismiss card, keep Refs, toast `Copied {title}` for 1.5 s on the existing footer path.
- Reduce Motion: instant appear. Increase Contrast: stronger fill, keycap stroke. VoiceOver: `Copy, N items. Wiki link, [[…]], selected.` Each row is a button.

Anchor: reuse `actionsAnchor`. If the card would clip the footer or the right inspector, flip it above the row and/or shift left. The panel is a fixed 880×560; do not resize it. The card is an overlay, not a second window, so Highlights stays frontmost and `resignKey` does not fire.

### 5.2 Mode in the key monitor

Today `processKeyEvent` maps through `RefsKeyRouter` and, on `nil`, returns the `NSEvent` to the search field. While the yank card is open, printable letters would otherwise type into the query.

Add an explicit mode, consulted first:

```
if model.yank != nil { return yankCommand(event) }
return RefsKeyRouter.command(...)
```

While open, swallow every key the card understands **and** the unused printables (consume, do not type). Leave unmodified arrows, Return, Esc, `⌃Y`, and the letter accelerators as the only productive keys. `⌘K` dismisses the card and then opens actions (copy verb yields to the actions verb). `⌘C` copies the selected yank payload, which is the one case where standard Copy should mean "copy this row," not "copy the query."

### 5.3 ⌘K relationship

Keep Copy Wiki Link and Copy PDF Path on ⌘K. They call the same `copyWikiLink()` / `copyPDFPath()` the card uses. Discoverability for mouse users stays. Do not add the whole catalog to ⌘K.

Optional, cheap: a ⌘K item **Copy…** with no key-equivalent that simply `showYank()`. Skip it in v1; `⌃Y` plus the footer is enough.

### 5.4 Pasteboard

Keep `RefsPasteboardWriting.copy(String)` for tests.

For PDF path only, a production writer should:

1. `clearContents()`
2. `setString(absolutePath, forType: .string)`
3. `writeObjects([pdfURL as NSURL])` so the file-URL flavor is present

Do not put the PDF bytes on the pasteboard. Do not promise files that `isMissingPDF`.

Everyone else is a single UTF-8 string. Newline-normalize notes blocks to `\n`.

---

## 6. Implementation shape

All in `bob-mac-capture`. No bob-cli change required to ship.

### 6.1 Files

| Piece | Where | Notes |
| --- | --- | --- |
| Catalog | `Sources/RefsCore/RefsYankCatalog.swift` | Pure. Linux `portable-check` covers it. |
| Decoder adds | `RefsDecoding.swift`, `RefsInspector.swift`, `RefsModel.swift` | `decodeIfPresent` for `research_ref`, annotation `block_id`/`link`. Older bob still works. |
| Command | `RefsCommand.showYank` | Router maps keyCode `16` (`y`) + `.control`. |
| Model | `RefsPanelModel` | `yank: RefsYankState?`, `copyYank(row)`, toast reuse. |
| Card | `Sources/BobMacCapture/Refs/RefsYankCard.swift` | SwiftUI, previewMode for design tests. |
| Overlay | `RefsPanelView` | Overlay on the well, not a child `NSPanel`. |
| Monitor | `RefsPanelController.processKeyEvent` | Mode first, then existing router. |
| Footer | `RefsFooter` | Swap hints while `yank != nil`; idle line gains `⌃Y Copy`. |
| Tests | router, catalog, model, decoder, design PNG | `BOB_MAC_CAPTURE_RENDER_DIR` snapshots: paper, chat, notes layer, missing-PDF, Reduce Transparency. |

### 6.2 Optional bob-cli follow-up (not a v1 gate)

Un-skip `RefRow.id` as additive JSON, or add `identity.marker_id`. The Mac labels `I` **Marker ID** when that field is present and **PDF stem** when it is not. Until then, stem is the honest v1.

Do **not** add a `bob ref yank` verb. Clipboard is a GUI concern. JSON already has the strings.

### 6.3 What not to do

- Parse `bob ref marker` output in Swift.
- Walk `~/bob/lib` for stems.
- Copy Highlights' internal annotation object ids.
- Auto-copy on `⌃Y` with a delayed palette (VS Code peek). Accidental copies into a password manager / chat are worse than one extra key.
- Remember last-used payload across shows. Wiki link as the stable default is teachable; a sticky `P` is a footgun the next morning.
- Open the card when the query field has marked IME text.

### 6.4 Test matrix (minimum)

- `⌃Y` with a selection opens; with none is consumed.
- `⌃Y` while composing returns `nil` from the router.
- `L` / Return copies `item.link` bytes-identical.
- `P` copies the absolute path the library already resolves; missing PDF omits the row.
- `I` copies the stem of `lib/papers/agentic_software_engineering.pdf`.
- `N` omitted when `commentCount == 0` and inspector notes are empty.
- `N` then `1` copies quote + comment + `[[…#^h-…]]` once `block_id`/`link` decode.
- Catalog hides `U`/`A`/`R`/`S` when absent.
- Toast text matches the row title.
- Design PNG: paper with arXiv, chat without URL, notes layer, missing PDF.
- `just portable-check` covers RefsCore catalog + decoder. Mac typecheck for the card.

---

## 7. Requirement adjustments (call these out)

The lead should adopt or explicitly reject each of these.

1. **The surface is a yank card, not "a new menu."** ⌘K keeps the system menu. `⌃Y` gets glass, previews, and accelerators.
2. **Two layers, not one.** Identity first. Notes behind `N`. Highlights never occupy `1`–`9` on the first screen.
3. **Closed catalog, hide missing.** Creativity is in choosing the *right* twelve payloads, not listing every field on `RefRecord`.
4. **Consume `⌃Y` so Cocoa cannot paste into the query.** This is a bugfix bundled with the feature.
5. **Copy bob's bytes.** `item.link`, `task.link`, annotation `link`, `research_ref`, first URL. Format only the citation and the notes Markdown wrapper.
6. **Marker ID v1 = PDF stem.** Do not spawn `bob ref marker`. Optional later: serialize frontmatter `id`.
7. **Do not synthesize capture tokens.** No `@sase:ref-…`. The reading-task row is `task.link`.
8. **Do not put DOI or BibTeX on the first screen** until the library actually has DOIs on PDF-backed rows (today: zero).
9. **⌘C-when-unselected-copies-wiki** is a companion, not the feature.
10. **Keep ⌘K's two copy items** as aliases. Do not duplicate the whole catalog there.
11. **Footer swaps** while the card is open rather than growing the idle hint line without bound.
12. **No last-used memory in v1.**

---

## 8. Is this a good idea?

Yes.

Refs is a *finder*. Capture is a *writer*. The missing motion is **finder → clipboard → writer** (daily note, capture draft, chat, `bob ref find`, a browser). ⌘K already admitted that by growing Copy Wiki Link. A dedicated copy chord is the version of that admission that can be beautiful and complete.

The risk is menu sprawl and a Cocoa `yank:` footgun. The design above bounds both: a closed catalog, a consumed chord, a card that shows the bytes before they leave.

If the lead wants the smallest possible ship: **card with `L P I T K` only**, still on `⌃Y`, still intercepting Cocoa, still decoding annotation links for a later `N`. That is a valid slice. It is not the right stopping point; `U`/`A`/`C`/`N` are the payloads that make the chord worth learning.

---

## 9. Recommended solution

Ship **Refs yank card** in Bob Mac Capture:

1. `RefsKeyRouter` maps `⌃Y` to `showYank`. The local monitor consumes it.
2. `RefsYankCatalog` in RefsCore lists the identity rows in §4.1, omitting empties, defaulting to wiki link.
3. `RefsYankCard` overlays the selected row with kind tint, keycaps, payload previews, and swapped footer hints.
4. `N` opens the notes layer from the inspector LRU; `1`–`9` copy quote + comment + highlight wikilink.
5. Pasteboard reuses `RefsPasteboardWriting`; PDF path also writes a file-URL flavor.
6. Additive Swift decodes: annotation `block_id`/`link`, row `research_ref`.
7. ⌘K copy items stay as aliases. Cocoa `⌃Y` paste into the search field dies.
8. Tests: router, catalog, decoder, model/toast, design PNGs. `portable-check` for RefsCore; Mac typecheck for the card.

That is intuitive (one verb, visible accelerators, preview of the bytes), reliable (bob-authored strings, no PDF parse, consume the Cocoa chord), and beautiful (glass card in the Refs language, not a second system menu).
