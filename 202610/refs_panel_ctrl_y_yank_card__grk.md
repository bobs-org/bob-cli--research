# Ctrl+Y should open a Yank card on Bob Refs, not another NSMenu

Researcher: `grk`. Independent report. Do not treat this as the swarm synthesis.

- **Question:** Should Bob Mac Capture's Refs panel gain a `<ctrl+y>` keymap that opens a menu for copying one property of the selected reference (marker id, a note/highlight, wiki link, and so on) with a single keypress? Lead the design so it is intuitive, reliable, and beautiful. Critique the plan, adjust requirements where justified, and recommend a solution.
- **Evidence:** bob-mac-capture `Sources/BobMacCapture/Refs/{RefsKeyRouter,RefsActionsMenu,RefsPanel,RefsPanelModel,RefsFooter,RefsInspectorView,RefsInspectorLoader,RefsVisualTokens}.swift`; `Sources/RefsCore/{RefsModel,RefsInspector,RefsDecoding,RefsFetching}.swift`; README keymap and inspector contract; bob-cli `docs/ref.md`, `docs/highlights-ref-sync.md` (marker grammar, generated body, `h-` block ids); `src/native/ref_library/{row.rs,show.rs}` (`id` skipped in JSON); `src/native/highlights_ref/sidecar_render.rs`; decision `mac-capture-is-a-thin-client`; glossary Reference Note / Reference Task; prior research `research:202610/highlights_quick_open_refs_panel/highlights_quick_open_refs_panel.md`; Raycast Action Panel / CopyToClipboard HUD; the capture panel's overlay-mode key routing (`CaptureKeyCommandRouter`).
- **Date of evidence:** bob-mac-capture and bob-cli trees as of 2026-10-14 (workspace 14 linked checkout).

## Bottom line

Yes: give Refs a dedicated **yank** verb. No: do not implement it as a second `NSMenu` stuffed with every field on a `RefItem`.

Copy is already a real Refs action — ⌘K already copies bob's `link` verbatim and the absolute PDF path, then toasts for 1.5 s — but those two payloads share a mixed opens-and-library menu, carry empty key equivalents, and hide the values the inspector already spent a column rendering (title, author, DOI, arXiv, source URL, summary, your notes, highlight block ids). Ctrl+Y is free in `RefsKeyRouter`. The panel's emacs/vim chords already stole Ctrl+K / Ctrl+J / Ctrl+P / Ctrl+N / Ctrl+D / Ctrl+U from the search field; taking Ctrl+Y (Cocoa's emacs yank) is the same kind of takeover, with a vim-shaped mnemonic: **Y for yank**.

**Recommended solution:** a compact in-panel **Yank card** (the decay-card / pull-in-choice family, not `NSMenu`), opened with Ctrl+Y on a selected row.

1. Stage 1 is a closed set of about eight *present* payloads, each with a visible keycap and a truncated preview of the bytes that will land on the pasteboard. Wiki link is the default. Enter copies the highlighted row; a letter copies immediately; a second Ctrl+Y copies the default (wiki link). Esc dismisses the card and returns to search.
2. Stage 2 (`h`) is "one of your notes": numbered commented highlights from the already-hydrated inspector, plus keys for quote, comment, block wiki link `[[stem#^h-…]]`, and the `h-<12 hex>` block id.
3. The app copies only values it already holds (list snapshot + inspector hydration). Absence omits the row. The card never parses a vault note or a PDF marker.
4. Two small additive JSON reads make the creative options real: serialize frontmatter `id` from `bob ref list` / `show` (today it is `skip_serializing`), and decode annotation `block_id` / `link` that `ref show` already emits.

⌘K stays the mouse-and-discoverability menu. Its Copy Wiki Link / Copy PDF Path rows remain. Ctrl+Y is the keyboard copy operator.

## Is this a good idea?

### What is right in the request

- **Copy is a daily Refs verb that the keyboard cannot reach.** Opening a PDF is Return. Opening the note is ⌘↵. Revealing in Finder is ⌥↵. Copying the two things you actually paste — a wikilink into capture or a daily note, a POSIX path into a terminal — is buried in ⌘K with no accelerators (`RefsAction.keyEquivalent` is `""` for both copy rows). A dedicated chord plus one letter is the missing operator.
- **A closed chooser with visible accelerators is the right shape.** The request already says "select with a single keypress." That is the decay-card pattern (`1`–`4`, `n`, `s`, …) and Raycast's Action Panel: open the panel to learn, then fire by shortcut. A Spotlight-style filter box on a set of eight items would steal the letters the chooser needs, which is exactly the failure `research:202610/ctrl_shift_p_task_card` diagnosed on the property picker.
- **The payloads are sitting on screen.** The inspector already shows title, byline (author · published · host · arXiv/DOI), facts, SUMMARY/ABSTRACT excerpts, outline, YOUR NOTES with page labels, quotes, and comments, the vault-relative PDF path, and the reading-task residence. Yank makes those values portable. Inventing a second data source would violate `decisions:mac-capture-is-a-thin-client`.
- **Ctrl+Y is a good chord on this panel.** `RefsKeyRouter` maps no `y`. Printable keys fall through to search, so an unbound Ctrl+Y currently reaches the field editor, where Cocoa's emacs bindings yank the kill ring. Ctrl+K is already remapped to move-previous, so that kill ring is already half-broken. Consuming Ctrl+Y is consistent, unused, and mnemonic. The capture panel is never visible at the same time (`BobPanelCoordinator`), so there is no cross-panel clash.
- **Beauty belongs in the brief.** ⌘K pops a system `NSMenu` below the selected row (`RefsPanel.showActionsMenu`), with `suspendHideOnResign` so tracking does not hide the glass. It is reliable. It is also chrome from a different app: no payload preview, no kind tint, no yellow quote bar, no way to page through notes. A copy menu whose whole job is "show me the bytes" needs to *show the bytes*.

### Where the request as written is underspecified

- **"A new menu" defaults to a second `NSMenu`.** That would ship fast and look like ⌘K with more rows. It cannot preview a highlight, cannot wait on inspector hydration, and cannot omit empty fields without rebuilding the menu on every selection. The product is the preview, so the chrome has to be a card.
- **"Be creative about options" is unbounded.** Hick–Hyman time grows with every extra row. Dumping marker id, every highlight, DOI, arXiv, both path spellings, an Obsidian URL, a file URL, APA, BibTeX, and a markdown digest produces a picker nobody memorizes. The bound is: *one key after Ctrl+Y for the trained set; a second stage only for the open set (notes).*
- **The marker id is not on the wire the app reads.** `RefRow.id` is parsed from frontmatter and used for `bob ref find` resolution, then `#[serde(skip_serializing)]` with the comment "kept out of JSON; only query resolution reads it" (`src/native/ref_library/row.rs`). `bob ref show` flattens that row, so the inspector never sees `id` either. `bob ref create --include-id` is what stamps `- id: xprompt_role_binding` into the page-1 marker (`docs/highlights-ref-sync.md`). Copying that value is a great option. Getting it by parsing the PDF in Swift is the wrong option.
- **Highlight identities are already in `ref show` JSON and then dropped.** Each annotation carries `block_id` (`h-` plus 12 hex chars from SHA-256 of pdf + kind + page + ordinal + text, `sidecar_render.rs`) and `link` (`[[{stem}#^{block_id}]]`). The Mac decoder keeps `page_label`, `kind`, `quote`, `comment` and ignores the rest (`RefsShowAnnotation`). The fixture in `RefsInspectorTests.testShowUnknownFieldsAreIgnored` even includes `"block_id":"^a"` and `"link":"[[x#^a]]"` as proof they are ignored. Stage 2 is a decode, not a new bob command.
- **The inspector asks `bob ref show … -c`.** Yank of "one of the notes" therefore sees commented highlights and standalone notes, matching YOUR NOTES. Uncommented quotes are absent unless we drop `-c` or add a second fetch. Keep `-c` for v1: the card copies what the inspector shows.
- **Search-field focus is the enabling constraint.** Letter accelerators only work if Ctrl+Y puts the panel in yank mode and the local key monitor consumes those keys, the way capture's picker overlay sets `pickerVisible`. An `NSMenu` gets this for free during `popUp` tracking. A custom card has to earn it with a mode flag on `RefsKeyContext`.

### Would I take a different approach?

I would still ship Ctrl+Y. I would make the chrome a **Yank card overlay inside the existing glass panel**, reuse `SystemRefsPasteboard` and the 1.5 s footer toast, and keep ⌘K's two copy rows as aliases for pointer users.

I would skip: a new `bob ref copy` subcommand; parsing markers in Swift; copying on chord-down with no confirmation; flattening every highlight onto stage 1; adding one global hotkey per payload; putting yank on the capture panel.

## Requirement adjustments

Call-outs the lead should adopt or explicitly reject.

| ID | Adjustment | Why it is justified |
| --- | --- | --- |
| **ADJ-1** | Implement a **Yank card** overlay (SwiftUI, in-panel), not a second `NSMenu`. | Payload preview is the product. `NSMenu` cannot show a quote, a citation, or a loading notes stage. The panel already has overlay-mode routing in capture; Refs needs the same for letters to beat the search field. |
| **ADJ-2** | Bound the chooser: **one letter after Ctrl+Y** for the closed set; **stage 2 only for notes**. Omit absent rows (honesty rule already used by the inspector facts grid). | An unbounded "creative" list is slower than ⌘K. Raycast groups Copy actions; it does not put twelve copy rows on the primary panel. |
| **ADJ-3** | **Default payload is bob's `link`** (`[[ref/…]]`). Enter copies the highlighted row; a second Ctrl+Y copies wiki link. | That is the value you paste into capture, a daily, or an agent prompt. It is also the only copy the snapshot always has. |
| **ADJ-4** | Copy **only decoded snapshot + inspector fields**. Additive `decodeIfPresent` for new keys. No vault reads, no PDF marker parser, no new bob verb. | `mac-capture-is-a-thin-client`. Citation and markdown packs are presentation of fields bob already returned. |
| **ADJ-5** | **Serialize frontmatter `id` in `ref list` / `show` JSON** (additive, `schema_version` 1). The app copies it as "Marker ID". Omit the row when null. Do not silently substitute the PDF stem. | Stem ≠ marker id. `--include-id` exists specifically so research hooks can round-trip that token. `bob ref marker <pdf>` is a spawn per yank and still returns human text. |
| **ADJ-6** | **Decode `block_id` and `link` on `RefsShowAnnotation`.** Stage 2 can then copy the highlight wiki link and the raw `h-…` id. | Already on the wire. The Mac client currently throws them away. |
| **ADJ-7** | Stage 2 lists **commented highlights in note order**, the same set YOUR NOTES pages with Ctrl+D. Keys `1`–`9` copy that note as quote + comment; `q` quote only; `c` comment only; `b` block wiki link; `i` block id. `a` copies all comments as a markdown pack. | Matches the inspector. Expanding to uncommented highlights means dropping `-c` and flooding chats that have dozens of raw quotes. |
| **ADJ-8** | Identity copies are **instant**. Notes and summary wait on the existing 120 ms hydration + LRU. `h` / `s` open a loading stage rather than spawning a second `ref show`. | The loader already caches 32 shows. A parallel fetch would race the inspector and violate "one semantic implementation." |
| **ADJ-9** | Label truncated excerpts as excerpts. Copy the extractor's text (with its ellipsis) under "Abstract excerpt" / "Summary excerpt". | Honesty rules: a 420-character ABSTRACT is not the paper's abstract. |
| **ADJ-10** | Keep **⌘K Copy Wiki Link / Copy PDF Path**. Add a footer hint `⌃Y Copy`. Do not move opens onto the yank card. | Opens already have dedicated chords. Mixing them into yank recreates ⌘K. |
| **ADJ-11** | Esc ladder grows one rung: **yank card → banner → query → scope → close**. Stage 2 Esc returns to stage 1. | Same as capture picker / pull-in choice. Today's Esc (`RefsPanelModel.perform(.escape)`) has no overlay rung. |
| **ADJ-12** | Write **both** `NSPasteboard` string and `file://` URL when yanking a PDF path, so Finder and Terminal both paste well. Keep the toast "Copied PDF path". | Today's `SystemRefsPasteboard` only sets `.string`. Absolute path stays the string; the file URL is extra, not a second menu row. |
| **ADJ-13** | IME: Ctrl+Y itself is fine while composing; **letter accelerators pass through when `markedTextPresent`**. | Matches Return / Ctrl+D. A composing `h` must not fire stage 2. |
| **ADJ-14** | Do not copy on an unavailable row, a missing selection, or an empty listing. Consume Ctrl+Y anyway so it does not yank the kill ring. | Dimmed rows "never open whatever slid into their index" (README). Yank follows the same rule. |
| **ADJ-15** | Do not add BibTeX, APA, RIS, or a Highlights deep link in v1. One **Bob citation** line is enough. | Citation managers are a different product. The card should paste into capture, chat, and agents. |

## What is already true

| # | Fact | Evidence |
| --- | --- | --- |
| E1 | Refs key table has no Ctrl+Y. Ctrl+K is Actions only with ⌘; with Ctrl it moves previous. | `RefsKeyRouter.swift`; README keymap |
| E2 | ⌘K is an `NSMenu` popped below the selected row. Copy Wiki Link writes `item.link`. Copy PDF Path writes the absolute vault-joined PDF path. Toast 1.5 s. | `RefsPanel.showActionsMenu`; `RefsPanelModel.copyWikiLink` / `copyPDFPath`; `SystemRefsPasteboard` |
| E3 | Copy rows have empty key equivalents. Opens show ↵ / ⌘↵ / ⌥↵; Refresh ⌘R; Scan ⌘S. | `RefsAction.keyEquivalent` |
| E4 | Footer hints: `↵ Open in Highlights  ⌘↵ Note  ⌥↵ Reveal  ⌘K Actions  ⌘S Scan  ⌘1–5 Scope  esc Close`. | `RefsFooter.hintsText` |
| E5 | `RefItem` already holds `link`, `rawTitle` / `title`, `stem`, `pdfPath`, `author`, `published`, `urls`, `arxivID`, `doi`, `audioPath`, `parentLabel`, `task`, annotation/comment counts. No marker `id`, no `research_ref`. | `RefsModel.swift`; `RefRecord` coding keys |
| E6 | Inspector hydrates after 120 ms via `bob ref show <path> -f json -c` (LRU 32) plus PDFKit intrinsics (summary/abstract/outline/reading time). | `RefsFetching.swift`; `RefsInspectorLoader.swift` |
| E7 | YOUR NOTES is commented highlights only (`hasComment`). Ctrl+D at the bottom reveals the next page (default 3). | `RefsShowAnnotation.hasComment`; `RefsNotesPage` |
| E8 | `ref show` JSON annotations include `page_label`, `kind`, `quote`, `comment`, `asset`, `block_id`, `link`. | `docs/ref.md`; `ShowAnnotation` in `show.rs` |
| E9 | Highlight block ids are `h-` + first 12 hex of SHA-256 over pdf + kind + page + ordinal + normalized text. Links render `[[{stem}#^{block_id}]]`. | `annotation_block_id` in `sidecar_render.rs`; `show.rs` `format!("[[{stem}#^{}]]", …)` |
| E10 | Marker note is the first standalone `/Text` on page 1. Standard keys: `status`, `parent`, `title`, `id`, `research`, `aliases`, `topics`, `source_url`, `author`, `published`, `captured`, `return_links`. | `docs/highlights-ref-sync.md` Marker Note Grammar / Synced Properties |
| E11 | Frontmatter `id` is parsed onto `RefRow` and then skipped in JSON. | `row.rs` `#[serde(skip_serializing)] pub id` |
| E12 | `research_ref` *is* serialized on the list row. The Mac client does not decode it. | `docs/ref.md` JSON field list; `RefRecord` has no `research_ref` |
| E13 | Reading task already has `task.link` (`[[path#^id]]`) on the snapshot. | `RefTaskView`; `RefTask` |
| E14 | Esc ladder today: banner, then query, then scope, then close. | `RefsPanelModel.perform(.escape)` |
| E15 | Local key monitor runs only while the panel is key; nil router result falls through to the search field. | `RefsPanelController.processKeyEvent` |
| E16 | Thin client: bob owns grammar and vault mutation; the app decodes with `decodeIfPresent` and presents. | `decisions:mac-capture-is-a-thin-client`; `BlockIDRules.swift` comment |
| E17 | Raycast: ⌘K opens Action Panel; first action is ↵; Copy is a first-class action with HUD; Copy Path / Copy Name are distinct shortcuts; Esc is back. | Raycast Manual, Action Panel; `Action.CopyToClipboard` |

## Design: the Yank card

### Chrome

A 360 pt-wide card, height to content, floating over the content well at the selected row (same anchor math as ⌘K, `RefsPanel.actionsAnchor`). The well behind it dims to ~40% (instant under Reduce Motion). Material, radius 12, and type match the inspector: caption-weight section labels, callout body, monospaced keycaps in a 22 pt rounded rectangle.

Header, one line:

- Kind chip (existing tint: purple chat, teal paper, brown article, indigo doc)
- Truncated title
- Quiet word **Copy**

Rows, 32 pt, two columns:

- **Keycap** (one character, or `↵`)
- **Label** plus a tertiary truncated preview of the payload (`[[ref/papers/ea_graph]]`, `lib/papers/ea_graph.pdf`, `1706.03762`, first 60 characters of a quote)

The default row (wiki link) carries a 2 pt accent bar on the leading edge, the same accent the list uses for selection. VoiceOver reads "Copy wiki link, [[ref/papers/ea_graph]], selected."

Footer of the card, caption secondary: `↵ Wiki link  h Notes  esc Close`. Stage 2 footer: `1–9 Note  b Block link  esc Back`.

Animation: 0.12 s ease-out scale from the row, matching panel show. Reduce Motion: appear fully opaque at rest.

This is the same family as the freshness decay card and the successor pull-in choice: a closed set, visible accelerators, Esc writes nothing.

### Stage 1 — closed set (omit a row when its value is missing)

Mnemonic: **yank, then a motion**, like vim.

| Key | Label | Payload | Source | Shown when |
| --- | --- | --- | --- | --- |
| `w` / `↵` / second `⌃Y` | Wiki link | `item.link` verbatim | snapshot | always |
| `p` | PDF path | absolute POSIX path, plus `file://` flavor | `library.pdfURL` | PDF resolves |
| `n` | Note path | vault-relative `item.id` (`ref/papers/ea_graph.md`) | snapshot | always |
| `t` | Title | `item.title.text` (display text, code spans flattened) | snapshot | always |
| `i` | Marker ID | frontmatter / marker `id` | **additive JSON** | non-empty `id` |
| `u` | Source | first `urls[]`, else `https://doi.org/{doi}`, else `https://arxiv.org/abs/{arxiv}` | snapshot | any of those present |
| `c` | Citation | `{title} — {author} ({published}). {source}` | derived from snapshot | always (degrades to title) |
| `k` | Reading task | `task.link` | snapshot | `task.link` present |
| `r` | Research ref | `research:{research_ref}` | additive decode of existing JSON | agent reports that carry it |
| `s` | Summary | ABSTRACT or SUMMARY excerpt text | inspector | hydrated excerpt exists |
| `h` | Notes… | opens stage 2 | inspector | `commentCount > 0` or hydrated notes, or still loading |

Absent rows collapse; the card stays short. A paper with DOI, URL, author, and three comments shows every row above. A chat with no `id`, no URL, and no comments shows wiki, PDF, note path, title, citation, maybe research ref and task — about six rows.

**Citation format (v1, one line, Bob-native):**

```
Attention Is All You Need — Vaswani et al. (2017). arXiv:1706.03762
```

Fallbacks in order for the tail: arXiv id, DOI, first URL, wiki link. Chats skip author/year and use `Agent report · {parent}` when that is the byline. This is presentation of bob fields, not a second bibliography engine.

**Not on stage 1 (on purpose):** BibTeX, Obsidian `obsidian://open` (⌘↵ already opens the note), vault-relative PDF (wiki link + absolute path cover paste-into-note and paste-into-terminal), audio path, page count, added date, outline headings, Highlights URL scheme. Each of those can join later without changing the chord.

### Stage 2 — one of your notes

Opens on `h`. Header becomes **Copy a note** plus `N comments`.

Rows `1`–`9` are the first nine commented highlights in note order (the inspector's order). Each preview is `Page 12 · first 50 chars of comment or quote`. Copying a numbered row writes:

```
Page 12
> quoted text

comment text
```

Blank parts omit their lines. A standalone note is just the comment, no quote fence.

Extra keys, always visible when they have work:

| Key | Payload |
| --- | --- |
| `q` | quote of the highlighted note only |
| `c` | comment of the highlighted note only |
| `b` | `[[ref/papers/ea_graph#^h-ab12cd34ef56]]` (`annotation.link`) |
| `i` | `h-ab12cd34ef56` (`annotation.block_id`) — the "marker notes ID" sibling the request asked for, at highlight grain |
| `a` | all comments as markdown (`### Page N`, `>` quotes, `Comment:` lines) |

More than nine notes: `0` pages the next nine, matching Ctrl+D's "next page" idea without stealing Ctrl+D from the inspector (the inspector is dimmed). v1 may ship `1`–`9` plus `a` only; paging is polish.

If hydration has not landed: a three-line skeleton and the word "Loading notes…". Keys other than Esc are consumed and do nothing until the loader publishes. If `showFailed`: "Notes unavailable", same copy as the inspector.

### Key routing

Extend `RefsKeyContext` with `yankStage: none | menu | notes` (names TBD). Extend `RefsCommand` with `showYank`, `yank(RefsYankAction)`, `yankEscape`.

```
Ctrl+Y, yankStage none, a selected available row → .showYank
Ctrl+Y, yankStage menu                         → yank wiki link (fast path)
plain letter / digit / Return while yankStage ≠ none → .yank(…)
Esc / Ctrl+[ while yankStage notes             → back to menu
Esc / Ctrl+[ while yankStage menu              → close card
```

Unbound letters while the card is up are consumed (beep optional, default silent) so they cannot leak into search. Arrows move the highlighted row on stage 1, matching ⌘K's type-select-plus-arrows habit.

`RefsKeyRouter` stays a pure function. Tests assert the table without building `NSEvent`, as they do today.

### Pasteboard and feedback

Reuse `RefsPasteboardWriting`. On success:

1. `pasteboard.copy(payload)`
2. Footer toast `"Copied wiki link"` / `"Copied marker id"` / `"Copied note 3"` / `"Copied block link"` (existing 1.5 s)
3. VoiceOver announcement, same string
4. Card dismisses immediately (Raycast HUD pattern: copy closes the panel of actions, the parent Refs panel stays up)

PDF path additionally sets `.fileURL`. Nothing else needs a second flavor in v1.

### Esc, hide, and the search field

`suspendHideOnResign` stays for ⌘K. The yank card is in-process SwiftUI, so resign-key hide is unchanged: clicking outside still closes Refs, which is Spotlight-like and correct. The card is state on `RefsPanelModel`; `prepareForPresentation` and `panelDidHide` clear it.

Search keeps first-responder the whole time. Yank mode simply swallows keys in the local monitor. Repair-focus logic is untouched.

### ⌘K coexistence

Leave Copy Wiki Link and Copy PDF Path. Optionally, later, a third copy-section row **Copy…** that calls `showYank`. v1 does not need it. Do not add ten copy rows to ⌘K.

## Implementation sketch

Stay in bob-mac-capture for the card. Touch bob-cli only for ADJ-5.

**RefsCore (Linux-testable, no AppKit):**

- `RefsYankItem` / `RefsYankMenu` — pure builder from `RefItem` + optional `RefsInspectorContent` + optional `id` / `research_ref`
- Payload strings and "shown when" live here so tests never boot a panel
- Citation formatter, note markdown pack, block-link passthrough

**BobMacCapture:**

- `RefsKeyRouter` — keyCode `y` = 16 with `.control` → `showYank`
- `RefsPanelModel` — yank stage, highlighted index, `performYank`, toast reuse
- `RefsYankCard.swift` — the view, design-fixture snapshots like `RefsPanelDesignTests`
- `RefsPanelView` — overlay when stage ≠ none
- `RefsFooter` — append `⌃Y Copy` (truncates with tail, already the policy)
- `RefsShowAnnotation` — `blockID` / `link` via `decodeIfPresent`
- `RefRecord` / `RefItem` — `id` and `research_ref` via `decodeIfPresent`

**bob-cli (tiny, additive):**

- Stop skipping `id` on `RefRow` JSON (or serialize it as `null`). Document in `docs/ref.md`. Older apps ignore unknown keys; this app uses `decodeIfPresent`.
- No new subcommand. `cli_rules.md` wants additive protocol growth, not a `bob capture` nested verb, and `ref copy` would be a third writer of the same strings.

**Tests:**

- Router: Ctrl+Y maps; Ctrl+Y while composing still maps (Y is not an IME confirm); letters map only in yank context
- Builder: omits empty DOI; citation fallbacks; note pack formatting; nine-note cap
- Model: copy writes pasteboard + toast; Esc rung; hide clears stage; unavailable row consumes
- Decoder: `block_id` / `link` / `id` / `research_ref` round-trip; older fixtures without them still decode
- Design fixtures for stage 1 and stage 2

`just portable-check` covers RefsCore. AppKit overlay needs `just typecheck-tests` on the Mac per `AGENTS.md`.

## Critique of alternatives

| Approach | What it buys | Why it loses |
| --- | --- | --- |
| More rows on ⌘K | Zero new chrome | Empty key equivalents, no preview, mixed with Scan/Refresh, search field still eats letters unless `popUp` is tracking |
| `NSMenu` popped on Ctrl+Y | Tracking swallows keys for free; matches ⌘K | Ugly on glass; no quote preview; no loading stage; type-select is first-letter, not vim motions |
| Copy wiki link immediately on Ctrl+Y, menu on hold | Fast 80% path | Hold is undiscoverable; the card *is* the 80% path once `⌃Y ⌃Y` copies wiki |
| `bob ref copy --kind wiki` | One implementation for every client | Spawn latency on a chord; new CLI surface; the app already has the bytes |
| Parse the PDF marker in Swift | Marker id without bob-cli | Second marker parser; rejected by the thin-client decision |
| Drop `-c` so every highlight is yankable | Creative completeness | Chats with 40 raw quotes; inspector and yank disagree |
| Global macOS clipboard manager / Alfred snippet | Nothing to build | Knows no `[[ref/…]]`, no `h-` ids, no TODAY row |

## Risks

- **Footer overflow.** Adding `⌃Y Copy` to an already-long hint string truncates on narrow clamps. Accept truncation; the card teaches the letters.
- **Older `bob` without `id`.** Row omitted. Fine.
- **Stem vs path in annotation `link`.** `show.rs` uses the note stem, so the copied block link is `[[ea_graph#^h-…]]`, which Obsidian resolves if the stem is unique. If a collision exists, prefer building `[[{path-without-md}#^{block_id}]]` in the app from `item.id` + `block_id` — still presentation of decoded fields. Pin this in a test against a real `ref show` fixture.
- **Ctrl+Y muscle memory from emacs paste.** On this panel Ctrl+K already does not kill. Document in the README keyboard table. Do not add a setting in v1.
- **Stage 2 vs inspector paging.** Yanking note 4 while the inspector has only revealed 3 is allowed: the card lists up to nine from the hydrated array, independent of `RefsNotesPage`. The inspector remains the reading surface; the card is the copy surface.

## Recommended solution

Ship **Ctrl+Y → Yank card** on Bob Refs.

**v1, in order:**

1. Router + model stage + in-panel card chrome with wiki link, PDF path (string + file URL), note path, title, source, citation, reading-task link.
2. Additive bob-cli JSON for `id`; Mac decode; Marker ID row.
3. Decode annotation `block_id` / `link`; stage 2 notes (`1`–`9`, `b`, `i`, `a`).
4. Summary excerpt row once hydration is in.
5. README keymap, footer hint, VoiceOver, design fixtures, `decodeIfPresent` tests.

**Default trained path:** `⌃Y` `w` or `⌃Y` `↵` or `⌃Y` `⌃Y` copies `[[ref/…]]` and toasts "Copied wiki link." The panel stays up so the next Return can still open Highlights.

**Beauty:** a short glass card, kind-tinted header, keycaps, live previews, yellow quote bar on stage 2 matching YOUR NOTES, 0.12 s scale, Esc back, omitted empties. It should feel like the inspector grew a keyboard.

**Reliability:** one pasteboard helper, one toast, no vault I/O, no second `ref show`, no copy of truncated UI labeled as full text, no action on unavailable rows.

That is the feature. The request's chord is right. The request's "menu" should be this card.
