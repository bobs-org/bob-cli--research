# Bob Mac Refs: a Highlights PDF picker for the Bob library

- **Date:** 2026-10-08
- **Researcher:** `grk` (swarm `research.44`)
- **Question:** How should Bryan open PDFs from `~/bob/lib/` in the Highlights app, faster than Highlights' own File > Open (`⌃O`), with type, filter, sort, and rich selection metadata — and is a new `bob-mac-refs` Swift app the right shape?
- **Verdict in one line:** Yes, a dedicated Spotlight-like picker is the right product; no, it must not walk `~/bob/lib` as files, must not dump the whole library on an empty query, and must not be a from-scratch second Swift app. Build a thin client of `bob ref` that reuses Bob Mac Capture's panel language.

---

## 1. Recommendation

Ship **Bob Mac Refs** as a keyboard-first, pre-warmed `NSPanel` that:

1. Hotkey → focused filter field in under 50 ms (same budget as capture).
2. Lists **PDF-backed reference notes**, not directory entries.
3. Empty query shows the **reading queue plus Recents**, never the 295 finished PDFs.
4. Typed query fuzzy-ranks the full PDF-backed set, with type prefixes as hard filters.
5. Selecting a row fills a **right-hand inspector** (title, kind, state, authors, arXiv, dates, annotation quote, first-page thumbnail, audio, path).
6. Return opens that PDF **in Highlights specifically** via `NSWorkspace`, not via the system default PDF handler and not via Highlights' File > Open panel.

**Product shape (justified adjustment):** one macOS process, one menu-bar icon, two hotkeys — Capture and Refs — sharing `CaptureCore` (process client, fuzzy matcher, panel chrome, signing, login item). The dedicated picker UX the request describes does not require a second daemon or a second always-visible icon.

**CLI shape:** v1 uses `bob ref list -R all -A -f json` as the snapshot (~50 ms on this vault). No new bob verb is required to start. An additive `bob ref locate` that returns absolute PDF / note / audio paths can come later for Raycast and Shortcuts.

---

## 2. Critique of the original plan

The original plan is directionally right and locally wrong.

What is right:

- The bottleneck is **selection**, not PDF load time. Highlights' own documented Mac open path is File > Open ([How to Open and Read a PDF on Mac](https://highlightsapp.net/how-to/mac/open-and-read-pdf/)). That is a filesystem open panel. It cannot know Bob titles, reading state, type, or annotations.
- A global hotkey into a type-to-filter list is the correct interaction. Capture already proved this language on this machine: filter bar, pinned section headers, local fuzzy match, detail strip, `↑↓` / `↩` / `esc`.
- Kind must be visible per row. Among PDF-backed notes, 311 of 339 are `chat` / `agent-report`. Without a Paper / Article / Chat chip, every row looks the same.

What is wrong, and should change:

| Original requirement | Problem | Adjustment |
| --- | --- | --- |
| "Select one of the PDFs in `~/bob/lib/`" | Filenames are stems (`what_does_a_harness_buy_tokens.pdf`). Titles, type, state, authors, and annotation counts live on the `ref/` note. One indexed PDF is already missing from disk (`lib/chat/AGENTS.pdf`). | **Pick PDF-backed `bob ref` rows.** `source_pdf` is the open target; the note is the identity. |
| Show every PDF by default | 338 files on disk, 339 PDF-backed notes, **295 finished**. Dumping them is Highlights `⌃O` with nicer chrome. `bob ref list` already defaults to the reading queue for this reason. | **Empty query = Recents + started + next + queued (+ intake).** Finished/dropped appear only under a query or an explicit Library gesture. |
| New `bob-mac-refs` Swift app cloned from capture | Capture already owns Carbon hotkeys, non-activating `NSPanel`, `BobProcessClient`, `FuzzyMatcher`, signing, `SMAppService`, macOS CI, and the picker card. A second bundle duplicates all of that and adds a second menu-bar icon. The 2026-08 capture replacement research named duplication — not the widget — as the root failure of the Hammerspoon pop-up. | **Same process, second hotkey, shared `CaptureCore`.** A second *target* in the capture repo is acceptable if isolation is wanted; a second *daemon* is not. |
| Bind a keymap, possibly near `⌃O` | Global `⌃O` steals File > Open from every Mac app, including Highlights. Capture already uses `⌃⇧⌘I` (production) and `⌃⇧⌘O` (development / "insert line above"). | Configurable hotkey, default **`⌃⇧⌘H`** (Highlights) or **`⌃⇧⌘L`** (library). Never `⌃O`. |
| "As much useful data as possible" in a capture-style 80 pt strip | Capture's detail strip is 80 pt because an editor sits above it. This panel *is* the product. | **Two-pane inspector:** capture-like list on the left, selected-PDF inspector on the right. |
| Scan `lib/` for types from folder names | `ref_type` is already first-class JSON. Origin (`agent-report` vs `external`) is the other axis the user named ("paper, chat, article"). Folder names cannot express reading state. | Kind chips from `ref_type` + `origin`; state chips from `reading_state` / `status`. |

The idea is a good idea. A filesystem walker of `~/bob/lib` would be a bad implementation of it.

---

## 3. What exists today (verified)

### 3.1 The library, not the folder

Measured 2026-10-08 against the live vault via `bob ref list -R all -A -f json`:

| Quantity | Count |
| --- | --- |
| Indexed `ref/` notes | 941 (943 files, 2 superseded hidden) |
| PDF-backed notes (`source_pdf` set) | 339 |
| PDFs on disk under `~/bob/lib/` | 338 |
| Intake PDFs under `~/bob/xlib/` | 0 |
| Missing file (`source_pdf` set, file absent) | 1 (`lib/chat/AGENTS.pdf`) |
| PDF-backed by type | chat 311 · docs 11 · blogs 9 · papers 8 |
| PDF-backed by origin | agent-report 311 · external 28 |
| PDF-backed by reading state | finished 295 · dropped 19 · queued 18 · started 7 |
| PDF-backed with companion audio | 20 |
| PDF-backed with annotations | 67 (266 highlights total) |
| PDF-backed with comments | 43 |
| PDF-backed with arXiv id | 7 |
| PDF bytes | 193 MB total, median 163 KB, max 19.6 MB |

`bob ref list` with no flags already prints the reading queue, grouped STARTED then QUEUED, with status chips, dates, titles, type, and a `♫` audio mark — and it **hides 355 zorg-era legacy notes** unless `-s legacy`. That default is the empty-query UX. The JSON snapshot of the full index is **~50 ms, 741 KB** on this host (warm cache, Linux). That is the same order as capture's `bob capture --dry-run` measurements from the 2026-08 replacement research, and it is fast enough to fetch on panel open.

Human default (truncated):

```
bob ref · reading queue · 25 open · 941 in library
  STARTED  7   (all chat, all WIP, dates 2026-10-07..08)
  QUEUED  18   (NEXT then READY, including three fresh papers)
```

A picker that opens on "every PDF in `lib/`" would put those 7 in-progress chats under 295 finished reports. That is the bug.

### 3.2 `bob ref` JSON is already the picker model

Each list row already carries (`src/native/ref_library/row.rs`):

`path`, `link`, `title`, `origin`, `ref_type`, `era`, `status`, `status_sync`, `reading_state`, `parent`, `urls`, `identity.{keys,arxiv,doi}`, `author`, `published`, `captured`, `added`, `finished`, `source_pdf`, `audio`, `annotation_count`, `comment_count`, `snapshot.{synced_at,highlights_count}`, `research_ref`, `diagnostics`.

`bob ref show` adds `annotations[]` (page, kind, quote, comment, block id, link), `own_notes`, `tasks`, `also`. `-c` restricts to commented highlights. Show is also ~50 ms per note.

Default list order (`compare_rows` in `src/native/ref_library/list.rs`):

1. reading state: started → queued → finished → dropped → unknown
2. modern before legacy
3. within queued: `next` before `ready`
4. row date newest first (`added` for open states, `finished` for finished/dropped); undated last
5. title, then path

The Mac client should **reuse this order for the grouped (empty) view**, then replace it with fuzzy rank when a query is typed. Do not invent a third sort.

### 3.3 Bob Mac Capture already solved the hard Mac parts

From the capture README and `decisions:mac-capture-is-a-thin-client`:

- `LSUIElement` menu-bar app, bundle `org.bobs.bob-mac-capture`.
- Carbon `RegisterEventHotKey`, production `⌃⇧⌘I`.
- Pre-warmed non-activating `NSPanel`. Subprocess work stays off the hotkey path.
- `CaptureCore` is Foundation-only and Linux-testable. `BobProcessClient` spawns `bob` with argv arrays, a GUI-safe environment, and a 20 s timeout. No login shell.
- Local `FuzzyMatcher` (subsequence, boundary bonuses, spaces as AND tokens). Bob sends one snapshot; keystrokes never re-query.
- Picker card: 46 pt filter bar, 34 pt rows, 26 pt pinned headers, 80 pt detail strip, 12 pt corner radius, `.regularMaterial`, key-hint chips, VoiceOver announcements, Increase Contrast fills.
- Grouped vs filtered is already a first-class mode (`CapturePickerMode`). Empty filter keeps Bob's groups; nonempty filter is one ranked list with match highlights. The Complete picker is the one exception: it keeps Today / All headers while filtering.
- Opening Obsidian is already `obsidian://open?path=…` (`ObsidianOpenURL.swift`).
- Signing, `SMAppService` login item, ad-hoc vs Apple Development, macOS CI — all paid for.

The 2026-08 capture replacement research (`research:202608/bob_mac_capture_replacement/bob_mac_capture_replacement.md`) is still the architectural north star: native Swift panel, grammar/identity in bob-cli, direct subprocess, signed bundle. A refs picker has **no grammar**. That makes the thin-client split even cleaner than capture: bob owns the index, the app owns presentation and `NSWorkspace`.

### 3.4 Highlights as an open target

Highlights ([highlightsapp.net](https://highlightsapp.net/faq/)):

- Mac PDF reader with embedded annotations and sidecar Markdown. That is why Bob's library exists.
- **Not scriptable.** FAQ: "Is Highlights scriptable? No, not yet." AppleScript and a Highlights dictionary are off the table.
- File > Open is the documented Mac open path. That is the `⌃O` the request names.
- URL scheme, shipped in v1.2 (2015) and still maintained ("Improved handling of `highlights://` links", 2023.2):
  - Open file: `highlights://Users/test.pdf` (leading slash stripped)
  - Open at page: `highlights://Users/test.pdf#page=3`
- Bob's generated notes use a **stem** form, `highlights://<stem>#page=N`, which only resolves if Highlights already knows the document. That is fine for in-note page links. It is the wrong primary open for a picker that must work on a PDF Highlights has never seen.
- Highlights is not the macOS default PDF handler unless the user set "Change All…" in Finder Get Info. The picker must name Highlights explicitly.
- Highlights is not a reference manager. Bookends/Papers integrations exist; Bob is the library. The picker should not pretend to be Zotero.

Reliable open:

```text
NSWorkspace.shared.open(
  [fileURL],
  withApplicationAt: highlightsAppURL,  // Highlights.app
  configuration: NSWorkspace.OpenConfiguration()
)
```

Keep `highlights://<absolute-path-minus-leading-slash>#page=N` as a secondary "reopen at last page" for rows the picker itself has opened before. Do not use the stem URL as the primary.

---

## 4. Alternatives, and why they lose

| Approach | Why it looks tempting | Why it loses |
| --- | --- | --- |
| Teach Highlights `⌃O` a default folder | Zero code | Still a filesystem panel. Stems, no state, no type, no fuzzy title match, no inspector. |
| Spotlight / Finder search on `~/bob/lib` | Already on the Mac | Indexes filenames and maybe PDF content, not `reading_state`, not `ref_type` as Bob means it, not the queue. Chat PDFs have long titles inside the file and short stems on disk. |
| Alfred / Raycast file search | Fast to try | Same metadata hole unless a custom extension calls `bob ref list`. A Raycast extension is a *valid second client* of the JSON (the thin-client decision explicitly names Raycast as a free follow-on). It is a worse daily driver than a capture-matching panel, and it does not give Bryan the inspector he asked for. |
| Hammerspoon `hs.chooser` | Already on the Mac, days not weeks | Capture just escaped Hammerspoon. Login-shell spawn, unsigned notifications, HTML-in-Lua aesthetics, no Liquid Glass. A chooser that shells out to `bob ref list` would work, and would still be the wrong long-term surface. |
| Obsidian Quick Switcher on `ref/` | Bryan lives in Obsidian | Opens the **note**, not the PDF. The job is Highlights. A secondary `⌘↩` to the note is enough. |
| `open -a Highlights ~/bob/lib/…` from a zsh widget | Tiny | No UI, no types, no filter, no inspector. Fine as an escape hatch, not as the product. |
| New Swift app that `readdir`s `lib/` | Matches the request literally | Recreates `⌃O`. Loses titles, state, origin, annotations. Misses the one already-missing PDF. Violates the thin-client rule. |
| New Swift app that reimplements capture's panel stack | Matches "inspired by bob-mac-capture" literally | Second icon, second Settings, second signing identity, second CI job, two copies of `FuzzyMatcher`. The capture replacement research's whole point was to stop paying that tax. |

Raycast as a **prototype** of the JSON contract is reasonable. Raycast as the shipped picker is not, given that capture already established the visual and keyboard language Bryan likes.

---

## 5. Requirement adjustments (explicit)

These change the request. They are justified.

1. **Identity is the reference note, target is `source_pdf`.** The picker is "open this reference's PDF in Highlights", not "open this file from `lib/`". Intake (`xlib/`) rows are allowed as an Unscanned section; zorg-era notes without a PDF are out of v1 (they cannot open in Highlights).

2. **Empty query is the queue, not the library.** Recents (local, user-owned) + started + next + queued + unscanned intake. The 295 finished PDFs are one query away. This is the same product decision `bob ref list` already made.

3. **One process, two hotkeys, one menu-bar icon.** Call the surface "Bob Mac Refs". Implement it as a second panel in Bob Mac Capture (or a second SwiftPM target in that repo that shares `CaptureCore`). Do not ship a second `LSUIElement` daemon unless isolation is later proven necessary (independent quit, independent login item). The user-facing name can still be Bob Mac Refs.

4. **Two-pane inspector, not an 80 pt strip.** Capture's strip is a constraint of the capture editor. This panel has no editor. The right pane is where "as much useful data as possible" actually fits.

5. **Hotkey is `⌃⇧⌘H` (or `L`), configurable, never `⌃O`.** Settings mirrors capture's production/development hotkey toggle.

6. **No new bob verb in v1.** `bob ref list -R all -A -f json` is the snapshot; `bob ref show <path> -f json` fills the inspector's annotation quote. Add `--pdf` / `bob ref locate` only if a second client (Raycast) needs a smaller envelope.

7. **Always open with Highlights by bundle, never with the default PDF role.** Bryan's research PDFs are a Highlights library. Random other PDFs may still belong to Preview.

8. **Do not search annotation full text in v1.** 339 `show` calls would blow the 50 ms budget. Search title, stem, author, arXiv, type, parent. Load quotes only for the selected row.

9. **Local Recents are a section, not a filtered-rank boost.** Mixing frecency into fuzzy score buries an exact title match under a recently opened loosely matching chat. Capture's filtered pickers already rank by match score, then original order.

---

## 6. Design

### 6.1 Panel

A pre-warmed non-activating `NSPanel`, same activation rules as capture (Carbon hotkey, no `NSEvent` global monitor, `willPresent` if we notify). Approximate size: **780 × 560 pt**, width user-resizable, height content-owned and stable across filters (capture's "grow once, never while typing" rule).

```
┌─ Bob Mac Refs ──────────────────────────────────────────────┐
│ [Refs]  Filter by title, type, author, arXiv…    7 of 339   │
│ ○ Paper  ○ Article  ○ Chat  ○ Doc     queue · 25            │
├──────────────────────────────┬──────────────────────────────┤
│ OPEN NOW  7                  │  ┌ page-1 thumbnail ───────┐ │
│  ●  `%auto` Autonomy…  Chat  │  │                         │ │
│  ●  sase-listen plugin… Chat │  │                         │ │
│ UP NEXT  8                   │  └─────────────────────────┘ │
│  ◉  `%auto` Redesign…  Chat  │  Paper · Queued · Next       │
│ QUEUE  10                    │  What Does a Harness Buy?    │
│  ○  What Does a Harness…    │  Tokens, Mostly              │
│     Paper  arXiv 2610.04433  │  Yangze Liu and Zhongyi Han  │
│                              │  arXiv:2610.04433            │
│                              │  Added 2026-10-08 · 0 marks  │
│                              │  lib/papers/what_does_a_…    │
│                              │  “If I’ve mischaracterized…” │
│                              │                              │
│                              │  ↩ Open in Highlights        │
│                              │  ⌘↩ Note   ⌥↩ Reveal   ♫    │
├──────────────────────────────┴──────────────────────────────┤
│ ↑↓ Move   ↩ Open   ⌘↩ Note   ⌥↩ Reveal   esc Clear / Close │
└─────────────────────────────────────────────────────────────┘
```

Reuse capture tokens: 46 pt filter bar, 34 pt rows, 26 pt pinned headers, 12 pt corner radius, `.regularMaterial`, 18 pt shadow, accent match highlights, status glyphs from `CaptureEditorPalette.taskStatus` mapped onto reading state:

| State / status | Glyph | Color |
| --- | --- | --- |
| started / wip | `circle.lefthalf.filled` | orange (In Progress) |
| queued / next | `circle.inset.filled` | blue (Next) |
| queued / ready | `circle` | secondary |
| finished / read | `checkmark.circle` | green |
| dropped / abandoned | `xmark.circle` | secondary |

Kind chips, independent of state:

| `ref_type` | Origin | Kind label | Symbol |
| --- | --- | --- | --- |
| `papers` | any | Paper | `doc.richtext` |
| `blogs` | any | Article | `globe` |
| `chat` | `agent-report` | Chat | `bubble.left.and.bubble.right` |
| `chat` | `external` | Chat | same |
| `docs` | any | Doc | `doc.text` |
| `books` | any | Book | `book` |
| `slides` | any | Slides | `rectangle.on.rectangle` |
| other | any | Title-case `ref_type` | `doc` |

Color is never the only signal: every chip has a word. Increase Contrast strengthens fills, same as capture.

Sticky kind toggles sit under the filter (Paper / Article / Chat / Doc). They are hard filters, persist for the panel session, and compose with typed queries. They exist because 91% of PDFs are chats: without a one-key Paper pin, the queue is a chat list.

### 6.2 Sorting — empty vs typed

This is the load-bearing product decision.

**Empty filter (`FuzzyQuery.isEmpty`, no sticky kind, or kind-only):** grouped mode, Bob's list order inside each section.

1. **Recents** (0–8 rows). Paths the picker has successfully opened, newest first, stored in `UserDefaults` under the refs bundle (or a dedicated suite if this stays inside capture). Survives quit. User-owned: nothing else writes it. A finished paper Bryan reopened yesterday belongs here even though it is not in the queue. Cap 8; opening a ninth drops the oldest. Missing files stay visible with Open disabled.
2. **Open now** — `reading_state == started`. Today: 7 chats. Newest `added` first.
3. **Up next** — `status == next`. Today: 8.
4. **Queue** — remaining queued. Newest `added` first.
5. **Unscanned** — PDFs in configured `xlib/` with no matching `lib/` row. Today: none. Still design it; intake is how new papers arrive.

Do not render finished or dropped in grouped mode. A footer line, dim, can read `339 in library · type to search`. That teaches the filter without drowning the queue.

A typed `/` or a `Library` chip (optional, v1.1) would switch grouped mode to type sections (Paper, Article, Chat, …) with finished included. Not needed for v1; the filter covers it.

**Nonempty filter:** one ranked flat list, capture-style, with kind and state chips on every row so the lost headers are still readable.

Tokenisation (reuse `FuzzyQuery`):

- Whitespace splits AND tokens.
- A token that exactly matches a kind alias is a **hard type filter**, not a scored field: `paper` / `papers` / `p`, `article` / `blog` / `blogs`, `chat`, `doc` / `docs`, `book` / `books`. Same for `is:started`, `is:queued`, `is:finished`, `is:audio`, `is:ann`, `arxiv:2608`.
- Remaining tokens must all match at least one searchable field.

Field weights (best field per token, then sum), analogous to `TaskCompletePickerPresentation`'s `score * weight / 100`:

| Field | Weight | Why |
| --- | --- | --- |
| Title | 100 | What Bryan remembers |
| Filename stem | 90 | What he types when he remembers the slug (`ea_graph`) |
| arXiv id | 85 | Unique, short |
| Kind label / `ref_type` | 80 | Only if not already consumed as a hard filter |
| Author | 75 | Sparse (7 of 339 today) but high signal on papers |
| Parent | 40 | `sase_ref`, `obsidian_ref` |

Rank:

1. Exact stem match pins first (Block ID picker precedent).
2. Fuzzy score descending.
3. Reading-state rank (started → queued → finished → dropped).
4. Recents hit as a boolean (opened-from-this-picker), not a magnitude.
5. Row date newest.
6. Title A–Z.

**Do not** fold "how recently opened" into the score. A query `harness` must put *What Does a Harness Buy?* above a chat that happens to contain the word and was opened an hour ago, if the title match is stronger. Recency is a grouped-mode section and a last-place tiebreak.

**Type-only query special case:** if every token was consumed as a hard filter (`paper`, `is:queued paper`), keep grouped-by-state order. All remaining rows would otherwise share a dummy score of 0 and shuffle. This is the Complete picker's "keep Today / All headers while filtering" exception, applied to kind. Sticky kind toggles with an empty text field use the same path.

### 6.3 Navigation

Copy capture's picker keys, then swap the accept action from "insert" to "open":

| Key | Action |
| --- | --- |
| Printable / paste / ⌘A/C/V/X/Z / ⌃A/E / ← → | Native filter edit |
| ↑ / ⌃P / ⌃K, ↓ / ⌃N / ⌃J | Move, wrapping |
| Page Up / Page Down | Page |
| ⌘↑ / Home, ⌘↓ / End | First / last |
| ↩ / keypad Enter | Open PDF in Highlights, close panel |
| ⌘↩ | Open the `ref/` note in Obsidian (`ObsidianOpenURL`) |
| ⌥↩ | Reveal PDF in Finder |
| ⌘C with empty selection in the filter | Copy absolute PDF path (when a row is selected) |
| ⌘⇧C | Copy `highlights://` page URL |
| Space on a row with audio | Play / pause companion via `NSSound` or default player — do not steal ↩ |
| esc | Clear nonempty filter, else close |
| Tab | Move into inspector (or cycle sticky kind chips), not accept |

The filter field is first responder on open, same `requestFirstResponder` trick as `CapturePickerFilterField`. Fast typing before the snapshot arrives seeds the filter.

### 6.4 Inspector (selected row)

Populate immediately from the list snapshot; upgrade asynchronously with `bob ref show` and PDFKit.

From the list row, always:

- Kind + origin + reading state + status capsules
- Title (two lines, full)
- Author, published, captured, added, finished (present fields only)
- arXiv / DOI / first URL, as links
- `annotation_count` · `comment_count` · snapshot `synced_at`
- Companion audio mark and stem
- Vault-relative `source_pdf`, file size, mtime (from `FileManager`)
- Parent
- Missing-file or Highlights-not-installed callout

From `bob ref show` (debounced ~50 ms after selection settles):

- First commented highlight, else first highlight: `page_label`, quote (two lines), comment
- `own_notes` excerpt if nonempty
- Open-tasks under the note, if any (usually the `^ref` line)

From PDFKit, selected row only, cached by path + mtime:

- Page-1 thumbnail (~240 × 320 pt, rounded, shadow, dark/light)
- Page count

Do **not** thumbnail the list. Median PDF is 163 KB and would be fine; the 19.6 MB outlier and a 338-file burst on every hotkey would not. Selection-only is the reliable beautiful path.

VoiceOver: the inspector is a complementary region; moving the list announces `kind, title, state`, and the thumbnail is hidden from accessibility (`accessibilityHidden`).

### 6.5 Opening Highlights, reliably

Order of operations on ↩:

1. Resolve `~/bob/` + `source_pdf` to an absolute file URL. Refuse if missing; keep the panel open with the callout.
2. Locate `Highlights.app` via `NSWorkspace.urlForApplication(withBundleIdentifier:)` (probe at launch, cache). If missing, keep the panel open: "Highlights is not installed."
3. `open(..., withApplicationAt: highlightsURL)`. Do not `open(fileURL)` and hope the default handler is Highlights.
4. Record Recents (path, title, `opened_at`, last page if known).
5. Close the panel only after `open` returns success, matching capture's "hide only after bob reports success."
6. Optional v1.1: also open `highlights://<path-minus-slash>#page=N` when Recents has a last page. Measure on the Mac whether the file open plus the URL double-opens a window. If it does, use only the URL when Highlights already has the document, else only `NSWorkspace`.

Highlights restores windows by default (FAQ). That is their setting, not ours; do not try to quit and relaunch Highlights.

### 6.6 Snapshot, freshness, failure

- Launch: resolve `bob`, prefetch `bob ref list -R all -A -f json`, keep last-good snapshot.
- Panel open: reuse if younger than ~2 s and no FSEvents invalidation; else refresh. 50 ms is inside the "snapshot fetch spinner" already designed for capture pickers.
- FSEvents on `ref/`, `lib/`, `xlib/` coalesced, same as `VaultTargetWatcher`.
- Client-side filter: `source_pdf != nil`, drop `superseded_by`.
- `schema_version` must be 1; unknown fields `decodeIfPresent`.
- Partial snapshot: "Showing Bob's matches only" (capture copy).
- `bob` unresolved: menu row "bob Not Resolved — Open Settings…", panel still opens with last-good data plus a banner.
- Never parse PDF filenames as titles. If the note title is missing (0 of 339 today), fall back to stem, dimmed.

Linux-testable `RefCore` (Foundation only) owns: JSON decode, kind mapping, grouped/filtered presentation, fuzzy rank, Recents merge, empty states. AppKit/SwiftUI owns: panel, PDFKit thumbnail, `NSWorkspace`. That is the capture split, and it is how Linux agents keep shipping Mac UX.

---

## 7. Beauty, without a second aesthetic

Capture already has a design system Bryan accepted: Spotlight-like bar, material, pinned headers, status glyphs, locator colors, key-hint chips, Pulse on success. Refs should look like a sibling, not a new product line.

Where it should diverge, on purpose:

- **No editor, so the inspector can be large.** That is the beauty budget. A 80 pt strip cannot show a page thumbnail and a quote.
- **Kind color is a second axis next to state color.** Capture rows are all tasks. These rows are papers and chats. Kind chips carry the identity the request asked for.
- **Thumbnail is the "this is a document" signal.** Capture has no equivalent and should not grow one.
- **Menu-bar glyph.** If this stays in the capture process, keep the bullet-b. Do not add a second icon. If a separate target is forced, a monochrome highlighter-mark "h" (stem + mark, template image, no assets) is the parallel of `StatusItemGlyph`. One icon is the better product.

Render-test the panel the way capture does (`BOB_MAC_CAPTURE_RENDER_DIR` PNG fixtures, light/dark, 2x). That is how the capture picker stayed honest.

---

## 8. Implementation plan

**Phase 0 — contract, no Swift UI yet**

- Confirm on the MacBook: `NSWorkspace` open of a `lib/papers/*.pdf` lands in Highlights; `highlights://Users/…#page=3` jumps page; double-open behavior; bundle id.
- Confirm hotkey `⌃⇧⌘H` is free against capture, Hammerspoon, and Magnet-class tools.
- Snapshot decode tests in a new `RefCore` (or `CaptureCore` extension) against checked-in `bob ref list` JSON.

**Phase 1 — picker that opens**

- Panel, filter, grouped queue, local fuzzy, Recents, `NSWorkspace` open, missing-PDF and missing-Highlights states.
- Sticky kind chips.
- Same install path as capture (`just bundle`, `just install`).

**Phase 2 — inspector**

- `bob ref show` on selection, PDFKit thumbnail and page count, audio action, Obsidian / Reveal / copy.
- VoiceOver, Increase Contrast, Reduce Motion (skip any thumbnail animation).

**Phase 3 — only if a second client wants it**

- Additive `bob ref list --pdf` (skip 600 non-PDF notes) and/or `bob ref locate`.
- A Raycast extension that is another thin client of the same JSON. Not a replacement.

Estimated size: one SwiftPM target, on the order of the capture picker (the picker card + `FuzzyMatcher` + `BobProcessClient` are the expensive parts, and they already exist). The new work is presentation mapping, Recents, PDFKit, and Highlights open. That is weeks, not a new repo's worth of platform code.

macOS CI remains the gate: agents on athena cannot compile the AppKit half. `RefCore` tests must pass on Linux.

---

## 9. Risks

| Risk | Mitigation |
| --- | --- |
| Mac spawn of `bob ref list` is slower than 50 ms (cold vault, iCloud, Spotlight) | Prefetch at launch; last-good snapshot; spinner already in the capture filter bar. Reopen the daemon/FFI question only if warm Mac p95 exceeds ~150 ms. |
| `highlights://` path form vs stem form vs `NSWorkspace` double-opens | Phase 0 on the MacBook. Primary path is `NSWorkspace` with the Highlights bundle. |
| Highlights not scriptable, so "focus existing window" is best-effort | Accept it. File open of an already-open PDF should reuse the window; if it does not, that is Highlights. |
| 91% of PDFs are chats; empty queue looks like a chat picker | Sticky Paper / Article chips; kind glyphs on every row; `paper` as a type-only grouped filter. |
| Missing PDF (`AGENTS.pdf` today) | Row remains; Open disabled; inspector names the path. Do not hide it — hiding is how libraries rot. |
| Second hotkey collides | Settings toggle; default `⌃⇧⌘H`; capture keeps `I`/`O`. |
| Second app identity splits notifications and login items | Do not ship a second daemon in v1. |
| Annotation search expected later | v2 can add a bob-side `--with-quotes` snippet field. Do not scan 339 notes on the hotkey path. |
| PDFKit on a 19.6 MB file stalls the inspector | Thumbnail off the main thread, placeholder until ready, cache by mtime. |
| Signing / notification ghosts | Same as capture: signed bundle, stable id, `willPresent` if we notify at all. Opening a PDF may not need a banner; in-panel confirmation is enough. |

---

## 10. Recommended solution

**Do it.** Highlights File > Open cannot be taught Bob's library. The 25-item reading queue plus a fuzzy search over 339 titled PDFs is a small, beautiful problem, and capture already solved the Mac half of it.

**Do it as a thin client of `bob ref`, in the capture process:**

1. Global hotkey `⌃⇧⌘H` opens a pre-warmed two-pane panel.
2. Snapshot = `bob ref list -R all -A -f json`, locally filtered to PDF-backed rows, locally fuzzy-matched with the existing `FuzzyMatcher`.
3. Empty: Recents, Open now, Up next, Queue, Unscanned — Bob's list order inside each section.
4. Typed: one ranked list, type/`is:` prefixes as hard filters, score then state then recency, exact stem pinned.
5. Inspector: list metadata immediately, `bob ref show` + PDFKit for the selection.
6. ↩ opens the file with Highlights by bundle id; ⌘↩ opens the note in Obsidian.
7. No `lib/` directory walk, no second menu-bar icon, no global `⌃O`, no Hammerspoon, no Raycast as the primary.

That is the design I would implement.
