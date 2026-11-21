# Bank Row Notes From the Category Card — Design Research (cld)

**Question.** During the morning bank-row review, Bryan sometimes wants to leave a
note on a row ("what was this?", "why did I buy it?"). The proposal is a new `<space>`
keymap in the bank row Category card that prompts for a note, writes it to the row "in
some visually appealing way", and does **not** advance the `]b` walk. Is this a good
idea, what are the options, and what should we build?

**Short answer.** Yes, build it. It fills a gap the system already left room for. The
bank row grammar has an inline note (`— with Kelly`) that bob parses, emits in JSON,
and prints in `bob bank list`. But nothing makes a note quick to write or pleasant to
read, and the parsers have sharp edges a free-text writer would hit. Four changes to the
plan:

1. **Space is already taken** in the Category card: it files the row with no
   category, removes the category in set mode, and is the only acknowledge key in the
   restricted card. Keep Space for the note, as you asked, but move "no category /
   remove category" to `-`, the mirror of `+ new category`.
2. **A note is not an answer.** Writing one should not tick the row and not advance
   the walk. The card stays on the same row with Bob's suggestion still highlighted,
   so the next keystroke files the row.
3. **Store the note in the existing inline `— note` tail**, not in a new field, a child
   bullet, or a sidecar. A writer-side normalizer neutralizes the five sequences
   (`!!`, `⚑`, `[[`, `[k::`, trailing `^id`) that would otherwise flag, recategorize,
   link, or re-identify the row. One of them, `[[`, would also leak into future imports
   through learned links.
4. **Show the note as quiet prose, not a chip.** It renders as a muted italic
   `💬 LEGO for Max's birthday` in Live Preview and Reading view, in the card header,
   and in the queue card. Chips are for enumerations (category, account, subscription);
   a note is a sentence.

The full recommendation is at the end ([§10](#10-recommended-solution)).

---

## 1. What exists today (evidence)

### 1.1 The Category card's key map

The card is `BankCategoryCardModal` in bob-plugins `bob-ledger-tools`. Its key
resolution is pure and lives in
`plugins/bob-ledger-tools/src/245-plugin-bank-category-card-model.js:271-300`:

| Key | Action today |
| --- | --- |
| `Enter`, `Ctrl+Enter` | accept the highlighted category (suggestion or row) |
| **`Space`** | **`no-category`**: tick the row without a category (close mode); **remove the category** (set mode) |
| `+`, `=`, `＋` | open the New category stage |
| `/` | open the subscription picker (`247-…-ui.js:380`) |
| `Esc`, `q`, `Q`, `Ctrl+[` | cancel (layered, per `decisions:q-and-ctrl-bracket-mirror-esc`) |
| arrows, `Ctrl+N/P` | move the highlight |
| `[a-z0-9]` (except `q`) | file the category with that hotkey |

The restricted card, used when bob or the categories are unavailable, shows only
`␣ acknowledge · esc cancel` (`245-…-model.js:215`). The user guide teaches Space
explicitly: "Space files the row with no category"
(`docs/guides/acknowledge-bank-transactions.md`, step 2). The troubleshooting section
says: "If the card opens restricted (Space and Esc only)…"

**So the proposal's literal ask collides with three existing meanings of Space.** This
is the main thing to resolve.

How much would moving it cost? Some evidence: in the live vault's only month note
(`bank/2026-11.md`), **all 44 rows carry a `[cat::]`**. None was filed with no
category. The current Space action exists but its outcome does not appear in Bryan's
data. (This is a ten-day snapshot. Bryan may have used Space and later corrected the
row, but nothing persisted.)

### 1.2 The row grammar already has notes

`docs/bank.md` § Row grammar (bob-cli):

```text
- [x] $13.71 Smashburger [cat:: dining] [acct:: card] [[eat/smashburger|🍽️]] ⚑ — with Kelly ^bank-8f3a2c1d
```

> **Tail**, in any order: `[cat:: key]`, `[acct:: alias]`, wikilinks, `⚑` or `!!`
> (flag), and a note after the first `—`, `--`, or flag. … Indented children are free
> notes.

The note is already end-to-end in bob:

- **Rust parser.** `src/native/bank/grammar.rs:373-455` (`parse_row_tail`), with note
  text cleaned by `strip_markers_fields_links` (`:484-521`).
- **JSON.** Every row object has `note` (`docs/bank.md` § JSON).
- **CLI.** `bob bank list` prints `— {note}` after the category chip
  (`src/native/bank/output.rs:179-184`).
- **Plugin tokenizer.** `241o-plugin-bank-marks-model.js:85-178` (`bankParseRowTail`)
  returns `note` and `noteSpan`.
- **Ownership.** "bob writes a row once"; the Category card's edits are "Bryan's edit
  in his editor" (`docs/bank.md` § Ownership). A note written through the editor is
  exactly that kind of edit, so the ownership contract does not need to change.

**What is missing:**

- **No writer.** Nothing writes a note except typing `— …` by hand in the editor.
- **No styling.** Live Preview replaces the amount, category, account, flag, ID, and
  🔁 with widgets (`241p-plugin-bank-marks.js:283-353`), but leaves the note as raw
  `— text`. In a dense statement it reads as leftover syntax, not as an annotation.
- **Not shown in the card or queue.** The card header and the `view: queue` card do
  not show notes.

### 1.3 Why notes are worth it (from the vault)

In the November month note:

- **Amazon rows are opaque.** 10 of 44 rows are `Amazon Reta* 125dt`,
  `Amazon Mark* Iy2bk`, and so on. `[cat:: kids]` or `[cat:: groceries]` says which
  bucket, not *what*. A week later, `$41.56 Amazon Reta* U09g8 🧸 Kids` cannot be
  reconstructed without opening Amazon order history.
- **Cash is a black hole.** `$100.00 ATM withdrawal [cat:: personal]` and
  `[cat:: cash]` ("destination unknown" in Totals) are the rows where *why* matters
  most.
- **Category alone can't explain a choice.** `Aroma Smoke Shop` is filed once as
  `shopping` and once as `personal`. A note records the reason, which a category
  cannot.

So the use case is real and recurring, roughly one row in five. And the morning review
(`]b` + Ctrl+Enter) is exactly when memory is freshest.

### 1.4 The walk and the card's write path

- **The commit path.** `248-plugin-bank-category-card-actions.js:229-368`
  (`bankCategoryCommit`) applies one whole-line `replaceRange` (one undo step), saves
  the note, finds the next waiting row, moves the cursor, records a Ctrl+O jump, and
  re-anchors the walk via `bankWalkHandOffOpenedRow`.
- **Row identity.** A row is re-found at commit time by `^bank-` ID, or for ID-less
  rows by **exact line text** at the captured line (`246-…-write.js:50-102`).
- **Walk keys.** The walk keys rows by `bank:<ackId>` when the ID is unique, and
  otherwise by `path|date|text` (`249-plugin-bank-walk-model.js:197-218`).

**Implication:** a note write changes the line text. For ID-less rows, both the card's
capture and the walk anchor go stale unless the note writer re-captures and re-anchors.
Every imported row has an ID. Only typed rows lack one, and those start ticked, so this
is an edge case — but it will happen in set mode on typed rows.

---

## 2. Is this a good idea?

**Yes, with the four corrections above.** Arguments for:

- **It completes an existing affordance.** The grammar, JSON, and CLI already carry
  notes, so this invents no new storage. The feature is a writer plus a renderer.
- **It sits in the right place in the flow.** The card is where Bryan is already
  looking at the payee, amount, and day, and where he decides what the row was. A note
  belongs at that moment.
- **It costs nothing when unused.** If a row needs no note, the filing flow is
  unchanged: one keystroke.
- **It is local and independent of bob.** Writing a note needs no spawn and no
  categories, so it works even in the restricted card.

Things to be careful about (each addressed below):

- **Key collision with Space** (§1.1).
- **Grammar hazards.** Free text in the tail can flag the row (`!!`, `⚑`), add or
  duplicate `[cat::]`, become a row link that later imports *learn* (§7.2), or forge a
  trailing block ID.
- **Parser parity.** The Rust and JS note cleaners disagree today (§7.1). Once notes
  become common, `bob bank list` and Obsidian would show different text for the same
  note.
- **Walk and identity staleness** after the line changes (§1.4).
- **Making the card heavier.** The card's value is one-key filing. The note must be a
  side door you open on purpose, never a field you have to step through.

### What I would *not* do

- **Do not make the note a prompt you pass through on every row.** That would slow
  filing and erase the card's main virtue.
- **Do not treat a note as a "stay" answer** the way Alt+F is in the task walk
  (`decisions:answering-advances-the-walk`). A note is orthogonal to answering: it
  neither acknowledges nor keeps the row.
- **Do not open a second modal on top of the card.** The card already has an in-card
  stage pattern (New category, subscription picker) with layered Esc, `q` pass-through
  in text fields, and focus management. A stacked prompt would re-solve all of that
  less well.

---

## 3. Requirement adjustments (explicitly called out)

| # | Original requirement | Adjusted requirement | Why |
| --- | --- | --- | --- |
| R1 | `<space>` opens the note prompt | **Keep Space → note**, and **move "no category" (close) / "remove category" (set) from Space to `-`**. The restricted card becomes `↵ acknowledge · ␣ note · esc cancel`. | Space has three meanings today (§1.1). The vault shows no persisted no-category filings. `-` pairs naturally with `+ new category` ("plus a category / minus the category"), and a dash means "none" in a ledger. |
| R2 | "prompts the user for a note" | The note is an **in-card stage**: a one-line input under the row header, with tiles dimmed below. It is not a separate modal. | Reuses the New category stage pattern, keeps the row visible while typing, and inherits layered Esc / `q` / `Ctrl+[` behavior. |
| R3 | "without progressing to the next bank row" | Saving a note **neither ticks nor advances**. The card returns to the tiles on the same row with the suggestion highlighted. Esc after a note leaves the row **waiting, with its note**. | A note is not an acknowledgment. Keeping them independent means Esc never loses the note and never files by accident. |
| R4 | (implicit) add a note | Space **adds or edits**. The input opens prefilled with the existing note, cursor at the end. **Enter on an empty input removes the note.** | One key for the whole lifecycle. Appending is safer than select-all, where one stray letter would wipe the old note. |
| R5 | (implicit) close mode only | Works in **close mode** (the `]b` walk), **set mode** (**Bank: set category** on acknowledged rows), and the **restricted card**. | Annotating an already-filed row later is as common as annotating during the walk, and needs no bob. |
| R6 | "visually appealing" | Note renders as **muted italic prose with a 💬 lead** (not a pill) in Live Preview, Reading view, the card header, and the queue card. The `— ` marker is hidden behind the widget. | Chips mark enumerations; a note is a sentence. See §6. |
| R7 | (new) | **Saving a note is its own undo step** and is written immediately on Enter. | It is robust to Esc, and Ctrl+Z on a later filing does not take the note with it. |
| R8 | (new) | The end-of-walk summary counts notes (`… · 2 notes`). | Cheap, and it makes the habit visible. |
| R9 | (scope cut) | **Not in v1:** wikilinks or `#tags` inside notes, multi-line notes, note autocomplete, and Ctrl+Enter "save note and accept". | Each needs a grammar or learning decision (§7.2) or adds a second effect to one key. |

---

## 4. Design space

### 4.1 Where the note lives

| Option | Example | Pros | Cons | Verdict |
| --- | --- | --- | --- | --- |
| **A. Inline tail note (existing grammar)** | `- [ ] $23.21 Amazon Reta* 125dt [cat:: kids] — LEGO for Max's birthday ^bank-1a2b3c4d` | Already parsed by bob and the plugin; already in JSON and `bob bank list`; one row stays one line, like a statement memo column; import matching and ID append leave it untouched (`docs/bank.md` § Ownership) | Tail grammar hazards need a normalizer (§5.4); long notes make long source lines (they soft-wrap) | **Recommended** |
| B. Indented child bullet | `- [ ] $23.21 Amazon …` then `\t- LEGO for Max's birthday` | Fully free text: links, tags, multiple lines; no grammar hazard; import already keeps children with their row | Invisible to bob's `note` field, JSON, `list`, and the queue card; doubles the statement's height; the card would edit a second line (two-line transaction); no precedent in the card writer | Keep as the "long-form" escape hatch, typed by hand. Not the card's target. |
| C. New `[note:: …]` field | `… [cat:: kids] [note:: LEGO for Max] ^bank-…` | Dataview-queryable | Today it's a `bank_field_unknown` warning; `]` inside the note breaks it; duplicates grammar that already exists; uglier source | Reject |
| D. Sidecar or journal | `.bob/bank/notes.jsonl` | No line edits | Breaks "the vault note is the truth" and "Bryan's edits win"; invisible in the editor; another sync surface | Reject |

### 4.2 Which key

Constraints:

- Hotkeys claim `[a-z0-9]`, so a letter like `n` is unavailable (it may be any
  category's derived hotkey).
- `q` is reserved.
- `+`, `=`, and `/` are taken.

| Key | Mnemonic | Ergonomics | Conflict | Verdict |
| --- | --- | --- | --- | --- |
| **Space** | "add a word"; it's what you asked for | Best: thumb, no reach | Yes: no category / remove / restricted acknowledge → **reassign those to `-`** | **Recommended** |
| `-` | The grammar's own `--` note marker | Number-row reach | None | Good fallback if you'd rather keep Space as is. I'd use `-` for "none" instead (below). |
| `'` or `"` | "quote / say" | Home-row pinky | None | Weaker mnemonic |
| `Tab` | — | Good | Fights focus traversal; less discoverable | No |
| `Shift+Space` | "Space, but more" | OK | Chords are slower and easy to mis-hit | No |

**Where "no category" goes:** `-`, so the card reads `+ new · − none`. In set mode,
`-` means "minus the category" (remove). `Delete` is an alias in set mode only,
because there "remove" is the verb. The slip risk of `-` next to `=` is low-cost: the
result is a ticked, uncategorized row that Ctrl+Z reverts in one step, and it stays
correctable via **Bank: set category**.

### 4.3 Write timing

| Option | Behavior | Verdict |
| --- | --- | --- |
| **Immediate** | Enter writes the note now, as its own undo step; the card stays | **Recommended.** The note survives Esc; the row behind the modal visibly gains its 💬, which confirms the save without advancing. |
| Staged | The note is held in the card and written with the category in one transaction | One undo for the whole filing is elegant, but Esc loses the note (or needs a "discard?" prompt), and set mode gets awkward. |

---

## 5. Recommended interaction spec

### 5.1 Flow

```text
 ]b ──► waiting row ──Ctrl+Enter──► Category card (tiles, suggestion ↵ highlighted)
                                       │
                         Space ────────┤
                                       ▼
                                Note stage (input focused, tiles dimmed)
                                       │
          Enter / Ctrl+Enter ──────────┤ write note (own undo step), re-capture row,
                                       │ re-anchor walk; row stays [ ]; no cursor move
                                       ▼
                                Category card, SAME row, header shows 💬 note,
                                suggestion still highlighted
                                       │
             letter / ↵ / − ───────────┘──► files (tick + [cat::]) and advances (unchanged)
             Esc ─────────────────────────► closes card; row stays waiting WITH its note
```

### 5.2 Keys inside the note stage

| Key | Effect |
| --- | --- |
| printable keys (including `q`, letters, digits, Space) | type into the input. Hotkeys never fire while the stage is open. |
| `Enter`, `Ctrl+Enter` | save and return to the tiles. On an empty input with an existing note, remove the note. On an empty input with no note, just return. |
| `Esc`, `Ctrl+[` | back out to the tiles without writing (layer one); a second Esc closes the card (`decisions:q-and-ctrl-bracket-mirror-esc`) |
| `q` | types (text-control exception in the same decision) |
| IME composition | never saves mid-composition. The card already ignores `isComposing` / keyCode 229 (`247-…-ui.js:365,370`); the stage must do the same. |

**Opening-key hygiene.** The Space keydown that opens the stage is consumed, so it never
types a leading space into the input. `event.repeat` is ignored, as it already is for
filing keys (`247-…-ui.js:397-400`). This mirrors the existing Enter chord-swallow
logic.

### 5.3 Card visuals

The resting card, with a note already on the row:

```text
╭─ Category ───────────────────────────────────────────────╮
│  $23.21   Amazon Reta* 125dt                   Thu Nov 19 │
│  💬 LEGO set for Max's birthday                           │   ← muted italic, one line, wraps
│  7 of 12 · November   ▓▓▓▓▓▓▓░░░░░                        │
│                                                           │
│  Everyday   [C ☕ Coffee] [G 🛒 Groceries] [K 🧸 Kids ↵]   │
│  Money moves [I 💵 Income] [R ↩️ Refund] [T ↔️ Transfer]   │
│                                                           │
│  ↵ 🧸 Kids · learned                                      │
│  ↵ accept · letter choose · ␣ edit note · − none ·        │
│  + new · / subscription · esc                             │
╰───────────────────────────────────────────────────────────╯
```

The note stage open (tiles stay in place, dimmed, so returning feels instant):

```text
╭─ Category ───────────────────────────────────────────────╮
│  $23.21   Amazon Reta* 125dt                   Thu Nov 19 │
│  💬 ┃LEGO set for Max's birthday▏                     ┃   │   ← input sits where the note renders
│     ↵ save · esc back · empty ↵ removes                   │
│  ⚠ "!!" saved as "‼" so the row isn't flagged            │   ← only when the normalizer changed text
│  7 of 12 · November   ▓▓▓▓▓▓▓░░░░░                        │
│  Everyday   [C ☕ Coffee] [G 🛒 Groceries] [K 🧸 Kids]     │   (dimmed, inert)
╰───────────────────────────────────────────────────────────╯
```

- **Placeholder:** `What was this for?` (close mode) or `Add a note` (set mode).
- **ARIA:** `aria-label="Note for $23.21 Amazon Reta* 125dt"`. The existing live
  region (`247-…-ui.js:481-494`) announces `Note saved`, `Note removed`, or
  `Note unchanged`.
- **Placement:** the input sits exactly where the note will render, so the eye never
  moves. Tiles stay visible but inert, so leaving the stage doesn't reflow the card.

### 5.4 The writer: placement, normalization, refusal

**Canonical tail order.** Document this in `docs/bank.md` § Row grammar:

```text
- [ ] $AMOUNT Payee [cat:: k] [acct:: a] [[links]] ⚑ — note ^bank-id
```

**Placement rules.**

- **Add (no note yet).** Insert ` — <text>` immediately before the space that
  precedes the trailing `^bank-…` or custom `^id`, or at line end. On a flagged row
  this yields `⚑ — text`. Both parsers already accept that: Rust strips the `—`, and
  the plugin's leading-dash trim strips it.
- **Edit.** Replace only the note's text region.
  - If the note span contains anything structural (`[k::]`, `[[…]]`, `⚑`, `!!`), which
    happens on hand-typed legacy rows, **refuse** with
    `Bank: this note has links or fields — edit it in the note`. Never rewrite bytes the
    writer doesn't own.
- **Remove.** Delete from the marker (`—` or `--`) through the note end, plus one
  preceding space. If the note was introduced by a flag (`⚑ with Kelly`), delete only
  the text after the flag. **The flag stays.**
- **Tokenizer support.** The plugin tokenizer needs a `noteMarkerSpan` (start of the
  marker) next to `noteSpan`, so add and remove are exact.

**Normalizer** (`bankNoteNormalize(text) → {text, changes[]}`), pure and table-tested:

| Input | Output | Why |
| --- | --- | --- |
| newlines, tabs, runs of spaces | single spaces, trimmed | one-line grammar |
| `!!` | `‼` (U+203C) | `!!` would **flag** the row (both parsers) |
| `⚑` | `⚐` | would flag the row |
| `[[x]]`, `[[x\|y]]` | `x`, `y` (brackets dropped) | would become a **row link**; see §7.2 |
| `[key:: v]` | `(key: v)` | would become a field (`[cat::]` recategorizes; others warn) |
| trailing `^word` | `^ word` (space after the caret) | would forge a block ID |
| `#task` | **refuse**: `bank rows can't carry #task` | `bank_row_task` error |

- **Visible changes.** Every change is shown in the stage's ⚠ line *before* saving.
  Nothing is silent.
- **The `^` rule is mostly theoretical.** The id regex is anchored at line end, and
  the note always sits before the id, so only a note on an ID-less row ending in
  `^word` can trigger it.
- **`$` signs** stay. Only the amount's `$` is math-protected
  (`241o-…-model.js:224,264-280`), but a single unpaired `$20` in a note does not form
  inline math, because the closing `$` must follow a non-space. Add `$20/$20` and
  `split $40 w/ Kelly` to the Live Preview test fixtures.

**Concurrency and identity:**

1. **Commit guard.** Resolve the row with `bankCategoryResolveForCommit` (ID first,
   exact text for ID-less rows), the same guard that protects filing. On mismatch,
   show `Bank: the row changed — nothing written`.
2. **Write.** Apply one whole-line `replaceRange` (one undo step), then
   `bankCategorySaveNote`.
3. **Re-capture.** Set `modal.context = bankCategoryContextAt(editor, view, line)`.
   Without this, the very next category filing on an **ID-less** row is refused,
   because `capture.lineText` no longer matches (`246-…-write.js:88-90`).
4. **Re-anchor the walk.** Call `bankWalkHandOffOpenedRow({path, line, date, text:
   newText})`, so text-keyed walk entries (`249-…-walk-model.js:206-218`) still find
   the row.
5. **Repaint and announce.** Do **not** move the cursor, record a jump, or touch the
   session counts (except `notes += 1`).

### 5.5 Elsewhere in Obsidian

- **Command.** Add **Bank: note this row** (`bank-note-row`, no default hotkey). It
  opens the card in set mode with the note stage already open. That gives a direct path
  from the editor without going through categories, and Command Mode and the palette
  get it for free.
- **Queue card** (`view: queue` on `bank.md`). Show the note as a second, muted line
  under the payee.
- **Walker footer** (`b` family). Optionally, when the cursor row has a note, add a 💬
  glyph in the detail slot. Never show the text there; the footer sheds content as it
  narrows.

---

## 6. Rendering: beautiful, but honest

**Principle.** Bob's row marks already form a visual grammar: the amount pill, the
category chip with emoji, the muted account text, the warning flag, the near-invisible
ID, and the 🔁 subscription chip. A note is the one piece of *authored prose* on the
row, so it should look like prose, not like a token.

**Live Preview** (row not under the cursor):

```text
☐  $23.21  Amazon Reta* 125dt   🧸 Kids                 💬 LEGO set for Max's birthday
☑  $100.00 ATM withdrawal       🏧 Cash out             💬 Kelly's birthday card + farmer's market
☑  $27.59  Aroma Smoke Shop     🛍️ Shopping   ⚑         💬 gift for Dad — ask about return
```

- **Widget.** `Decoration.replace` over `— note` (from `noteMarkerSpan.start` to
  `noteSpan.end`) with a `BankNoteWidget` that renders `💬 text`.
  - CSS: `font-style: italic; color: var(--text-muted);`, with a `margin-inline-start`
    gap after the last chip. No background or border; chips keep the pills.
  - `max-width` is unset, so the note wraps naturally with the line.
- **Cursor on the row.** As with every other bank mark, the widget yields to raw
  source, so `— text` is editable in place. That keeps the Category card *optional*,
  not the only way to edit.
- **Flagged rows.** `⚑ — note` renders as the existing amber ⚑ chip followed by the
  muted note. The pair reads as "look into this, because…", which is the flag's
  purpose.
- **Waiting rows** keep their hue accent. The note doesn't change row tone, because
  tone means *waiting*, not *annotated*.
- **Reading view** (`241q-plugin-bank-marks-reading.js`) gets the same `💬` span. The
  `stats.bank_marks` and `toggle-bank-marks` gates already cover it.
- **Accessibility.** The widget's `aria-label` is `Note: LEGO set for Max's birthday`.
  The 💬 is `aria-hidden`.

**Why 💬 and not ✎ or “ ”:**

- 💬 matches Bob's emoji-led marks (🔁, ⚑, 🏦) and reads "comment" at a glance in a
  dense list.
- ✎ reads "edit" (an action, not content).
- Quotation marks would add two glyphs and imply the text is someone else's words.

**Card header:** the same `💬 text` line under the payee (§5.3).

**CLI:** `bob bank list` already prints `— note`. Keep it.

---

## 7. Pre-existing defects and hazards found while researching

These matter more once notes become a one-keystroke habit. Fix 7.1–7.3 alongside the
feature.

### 7.1 Rust and JS note cleaners disagree

- **Rust** (`grammar.rs:484-521`) removes **every** `—` and `--` anywhere in the note
  body. `— gift for Dad — ask about return` becomes `gift for Dad  ask about return`,
  with a double space and the dash lost.
- **JS** (`241o-…-model.js:165`) removes **every `!`** (`/[⚑!]+/g`), not just `!!`.
  `— Thanks!` becomes `Thanks` in Obsidian but stays `Thanks!` in bob. JS also keeps
  internal `—`, so the two disagree in both directions.
- **Fix.** Note text is the tail from the first marker, minus whole inline fields,
  whole wikilinks, `⚑`, and `!!`, then trimmed. Internal single `!` and internal dashes
  are content.
  - Put one shared fixture table in both repos' tests, following the plugin's "parity
    with bob" convention.
  - This is a bob display change only. JSON `note` gains characters it used to drop,
    which is additive.

### 7.2 Wikilinks in notes would be *learned* into future imports

`naming.rs:129` builds the learned link from `learned.links.first()`: the first link on
the most recent acknowledged row from the same merchant. Both parsers treat **any**
`[[…]]` in the tail as a row link, including one typed inside a note.

**So a note like `— for [[max]]` on an Amazon row would make the next Amazon import
write `[[max]]` onto a new row.** That's why v1 normalizes `[[` away (§5.4).

To allow links in notes later, make it a grammar decision: links *after* the note
marker are note content, not row links, so learning, subscription attribution, and the
`links` array ignore them.

### 7.3 The 🔁 subscription linker inserts inside an existing note

`bankSubscriptionLinkWritePlan` inserts the link just before the trailing ID
(`241hc-plugin-bank-subscription.js:498-509`), so on a row with a note the result is
`— LEGO for Max [[subscriptions/x|🔁]] ^bank-…`.

That still parses, because links are stripped from note text. But it breaks the
canonical order and turns the note into a structural span, which the note editor
would then refuse to edit (§5.4).

**Fix:** insert before `noteMarkerSpan.start` when a note exists. Do the same for the
ghost 🔁 offset (`bankSubscriptionGhostOffset`, `241hc-…:153-158`).

### 7.4 Payee learning is safe

`payee_end` stops at `—` / `--` (`grammar.rs:353-362`; JS `bankPayeeEnd`), so notes
never leak into learned payees. Nothing to fix. Keep a regression test.

---

## 8. Implementation plan

### Phase 1 — bob-plugins (the feature; no bob release needed)

1. **Tokenizer** (`241o-plugin-bank-marks-model.js`).
   - Add `noteMarkerSpan` to `bankParseRowTail` and `bankTokenizeLine`.
   - Apply the §7.1 parity fix to the JS cleaner.
2. **Pure model** (`245-…-model.js`).
   - `bankCategoryResolveCardKey`: `" "` → `{action: "note"}`; `"-"` (and `Delete` in
     set mode) → `{action: "no-category"}`.
   - The restricted footer becomes `↵ acknowledge · ␣ note · esc cancel`, and Enter in
     restricted mode maps to acknowledge.
   - Header model gains `note`; session gains `notes`; the end-of-run summary detail
     gains `· N notes`.
   - Update the key hint text in `247-…-ui.js:657-664`, or in `bankCategoryCardKeysText`
     if that wins.
3. **Pure writer.** New `bankNoteNormalize` and `bankNoteWritePlan({capture,
   currentPath, currentSource, text})`.
   - Returns `{ok, action: insert|replace|remove|noop, edits, changes[]}`, or a
     refusal.
   - Reuses `bankCategoryResolveForCommit`. Keep it in a new fragment
     (`246a-plugin-bank-note-write.js`) so `246` stays under the 1000-line fragment
     cap.
4. **Stage UI.** New fragment `248m-plugin-bank-note-stage.js`, a prototype mixin
   modeled on `248g-plugin-bank-category-new-stage.js`.
   - Methods: `openNoteStage`, `closeNoteStage`, `shouldPassNoteKey`, `routeNoteKey`,
     `paintNoteStage`.
   - Wire it into `routeCardKey`, `scopeKeyListener` pass-through, `onEscapeKey`
     layering, and `paint`.
5. **Action** (`248-…-actions.js`). Add `bankNoteCommit(modal, text)`: guard, then
   apply, save, re-capture, re-anchor, announce, repaint. No advance.
6. **Marks.**
   - Add `BankNoteWidget` in `241p-plugin-bank-marks.js` (after the 🔁 widget), plus
     Reading view support in `241q`.
   - CSS goes in `styles.css` beside `.bob-bank-mark-*`:
     `.bob-bank-mark-note { font-style: italic; color: var(--text-muted); margin-inline-start: 0.6em; }`.
7. **Subscription linker.** Insert links before the note marker (§7.3).
8. **Command and queue card.** Register `bank-note-row`; add the note line to the
   queue card (`241m-plugin-bank-cards.js`).
9. **Tests.**
   - `scripts/test-ledger-tools-bank-category-card.cjs`: key resolution, including
     Space vs `-` in close, set, and restricted modes.
   - New `scripts/test-ledger-tools-bank-note-write.cjs`:
     - insert, replace, and remove on ID rows, ID-less rows, flagged rows, and rows with
       `[acct::]` and 🔁;
     - refusals on structural note spans;
     - the normalizer table.
   - `test-ledger-tools-bank-category-card-ui.cjs`:
     - Space opens the stage without typing a space;
     - `q` types;
     - Esc layering;
     - Enter saves and stays;
     - a following hotkey files the *same* row and then advances;
     - the ID-less re-capture path.
   - `test-ledger-tools-bank-walk.cjs`: the walk anchor survives a note on an ID-less
     row.
   - Obsidian e2e (`scripts/obsidian-bank-ui-e2e.cjs`): `]b` → Ctrl+Enter → Space →
     type → Enter → `k`. Assert the row text, a single undo step per gesture, and the
     cursor on the next row.
   - Then `npm run build`, `npm test`, and `bob plugins sync`.

### Phase 2 — bob-cli (small, rides the daily release train)

1. **Note cleaner parity** (`grammar.rs`), with the shared fixture table (§7.1).
2. **Docs.**
   - `docs/bank.md` § Row grammar: canonical tail order and the note's content rule.
   - `docs/guides/acknowledge-bank-transactions.md` step 2: Space note, `-` none.
   - `docs/reference/plugins/bob-ledger-tools.md`, and bob-plugins
     `docs/bob-ledger-tools.md`.
3. **Optional:** the Bank Badge tooltip's "largest outflows" could append the note
   (`$1,728.00 Kelly household — November rent share`). That's a natural second place
   the *why* pays off.

### Memory follow-ups (route through `/sase_memory_write`; not done here)

- **Glossary `Bank Row`.** Mention the note and Space in the card description.
- **Decision record.** Add one for the key change: "In the bank Category card, Space
  writes a row note and never answers; `-` files none."
  - Rejected alternatives: Space stays "none" with `-` as note; a separate prompt
    modal; child-bullet or `[note::]` storage.
  - Reopens when Bryan files many rows with no category, or wants links in notes.

---

## 9. Risks and open questions for Bryan

1. **Muscle memory.** If you *do* press Space to file "no category" today, the new
   Space opens a harmless input (Esc backs out). The fallback design keeps Space as is
   and uses `-` for notes. I still recommend the swap: notes will be far more frequent
   than uncategorized filings, and the vault shows zero of the latter.
2. **Do you want links or tags in notes** (`for [[max]]`, `#reimburse`)? Both are
   valuable, especially `#reimburse` and `#tax` as a lightweight follow-up list. Both
   need the §7.2 grammar decision first. v1 neutralizes them visibly rather than
   silently.
3. **Ctrl+Enter in the stage.** v1 makes it equal to Enter (save and stay). A later
   "save note and accept the suggestion" chord would save one keystroke per noted row,
   but gives one key two effects. Revisit after a few weeks of use.
4. **Note length.** There's no hard cap; the input is single-line and long notes wrap.
   If notes start running past ~120 characters, that's a signal for a hand-typed child
   bullet. The stage could show a quiet hint at that length.

---

## 10. Recommended solution

Ship **"Space writes a row note"** in the bank Category card as a plugin-only change,
plus a small bob parity fix:

1. **Keys.** Space opens a one-line **note stage** inside the card. `-` takes over
   "file with no category" (close) and "remove category" (set; `Delete` aliases it).
   In the restricted card, Enter acknowledges and Space still writes a note.
2. **Semantics.** Enter writes the note **immediately, as its own undo step**. The row
   is **not ticked**, the **walk does not advance**, and the cursor does not move. The
   card returns to the tiles on the **same row** with Bob's suggestion still
   highlighted, so the next key files it as usual. Space on a noted row edits it
   (prefilled, cursor at the end), and an empty Enter removes it. It works in close
   mode, set mode (**Bank: set category**), a new **Bank: note this row** command, and
   the restricted card.
3. **Storage.** Use the **existing inline tail note**:
   `… [cat:: k] [acct:: a] [[links]] ⚑ — note ^bank-id`.
   - A pure normalizer neutralizes `!!`, `⚑`, `[[…]]`, `[k:: v]`, and a trailing
     `^id`, and refuses `#task`, showing every change before saving.
   - The writer refuses to edit notes that contain structure and points to the editor
     instead.
4. **Reliability.**
   - Reuse the card's commit guard (ID first, exact text for ID-less rows).
   - After the write, **re-capture** the row and **re-anchor the walk**.
   - Respect IME composition and key repeat.
   - Make the 🔁 linker note-aware.
   - Fix the Rust/JS note-cleaner disagreement with a shared fixture table.
5. **Beauty.**
   - Render the note as **muted italic prose led by 💬**, never a pill. Use it in Live
     Preview (yielding to source under the cursor), Reading view, the card header, and
     the queue card.
   - The note input sits exactly where the note will appear, with the tiles dimmed in
     place.
   - The live region announces the save, and the end-of-walk summary counts notes.

The result: the morning walk stays one keystroke per row. When a row needs explaining,
it's `Space`, type, `Enter`, and then the usual hotkey. The explanation then sits on
the row as a quiet sentence, in the same place every Bob surface already knows to look.
