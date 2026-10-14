# Bob Refs `⌃Y` Copy Card: Design Research and Recommendation (cld)

> **Request.** Add a `<ctrl+y>` keymap to Bob Mac Capture's Refs panel. It opens a menu where
> one keypress picks what to copy to the clipboard. Be creative about the options (marker `id`,
> one of the notes or highlights, …). Lead the design so it is intuitive, reliable, and
> beautiful. Critique the plan, adjust the requirements where that is justified, and end with a
> recommended solution.

---

## 0. TL;DR

**Build it.** The idea is good, and it is cheap to build because almost everything it needs is
already in memory. The Refs panel is the fastest way to *find* a reference: ranked search over
406 PDF-backed refs. Today it can only *open* one, or copy two formats from three levels inside
⌘K. The things Bryan actually hands to other tools are **identity handles** (the ID, the note
path, the wiki link), **the file itself**, and **his own notes**. A single-key copy card turns
the panel into a reference-handle dispenser: from a found row to the clipboard in two
keystrokes.

My recommended shape, with each adjustment to the request called out in §5:

1. **`⌃Y` opens a "Copy card" inside the panel, not an `NSMenu`.** The card replaces the
   inspector column. The selected row stays visible in the list, so it is always clear which
   reference you are copying from.
2. **Every row is a fixed mnemonic key, a label, and a live preview of the exact text that will
   be copied.** `I` ID · `T` Title · `W` Wiki link · `U` Source URL · `L` Markdown link ·
   `X`/`D` arXiv/DOI · `N` Note path · `P` PDF path · `F` PDF file · `R` Reading-task link ·
   `1`–`9` one of your notes · `A` all highlights as Markdown.
3. **Absent rows are hidden, never re-lettered.** A typical agent-report chat shows a calm
   7-row card. Pressing a hidden row's letter explains itself, for example "No source URL for
   this reference".
4. **`⌃Y ⌃Y` (or `↵`) copies the default row:** the ID, or the wiki link when there is no ID.
5. **A copy dismisses the panel at once and confirms with a small non-key glass HUD**
   ("✓ Copied ID · `second_wave_job_applications`"), so `⌘V` lands in the app you came from
   immediately.
6. **The ID needs a bob-cli change first.** `bob ref list`/`show` deliberately keep
   frontmatter `id` out of JSON (`#[serde(skip_serializing)]`). The thin-client rule forbids
   the app from reading frontmatter itself, and the ID is *not* the stem in 6 rows and *not
   unique* in 9 rows (3 groups). The card flags shared IDs.
7. **⌘K's two copy items fold into one "Copy… ⌃Y" item,** leaving one copy surface with one
   behaviour.

---

## 1. Evidence base

| Source | What I used it for |
| --- | --- |
| `bob-mac-capture` @ `44051a0` (2026-10-13) | `Refs/RefsKeyRouter.swift`, `RefsActionsMenu.swift`, `RefsPanelModel.swift`, `RefsPanel.swift`, `RefsInspectorView.swift`, `RefsFooter.swift`, `RefsVisualTokens.swift`; `RefsCore/RefsModel.swift`, `RefsDecoding.swift`, `RefsInspector.swift`, `RefsFetching.swift`; README "Bob Refs"; `AGENTS.md` |
| `bob-cli` @ `ae9e6ef` | `src/native/ref_library/row.rs` (the JSON row model), `mod.rs`, `docs/ref.md`, `docs/highlights-ref-sync.md` (marker grammar, `--include-id`) |
| `bob-plugins` @ `5e4bfae` | The existing Obsidian **Yank Path picker** (`bob-navigation-hotkeys`, bound to Mod+Y) as house precedent |
| Live library (vault checkout on apollo, 2026-10-14) | `bob ref list -R all -A -f json` plus a read-only frontmatter scan, for coverage counts and real values in the mocks; `bob ref show` timing and output shape |
| Prior research | `research:202610/highlights_quick_open_refs_panel/highlights_quick_open_refs_panel.md` (the original panel design and keyboard table) |
| Decision record | `decisions:mac-capture-is-a-thin-client` |
| Web | Raycast HUD guidance, the nspasteboard.org markers, which-key conventions (see Sources) |

Nothing here was verified on the Mac. The Mac-only checks are listed in §10, Phase 0.

---

## 2. What exists today

### 2.1 Keys and copy paths

- `RefsKeyRouter` is a pure keyCode→command table. `⌃K` is already *Move up*, which displaces
  Cocoa's Emacs-style kill. `⌘K` shows actions, and `⌃D`/`⌃U` scroll the inspector.
  **`⌃Y` (keyCode 16) is unbound** in both the Refs router and the Capture router, and nothing
  else in the app uses it.
- `⌘K` pops up an `NSMenu` with **Copy Wiki Link** (bob's `link`, verbatim) and **Copy PDF
  Path** (absolute). Each copy toasts the footer for 1.5 s ("Copied wiki link") and **leaves
  the panel open** (`RefsPanelModel.swift:775–806`).
- The menu needed a workaround: `suspendHideOnResign` stops the panel from hiding while the
  menu tracks (`RefsPanel.swift:137–189`). In other words, `NSMenu` runs its own modal loop
  outside the panel's key router.
- Pasteboard writes go through `RefsPasteboardWriting.copy(_ string:)`, which clears the
  pasteboard and then sets `.string`. The protocol exists so tests can inject a fake. It only
  handles strings, not file URLs or rich text.

### 2.2 Data the app has, and data it lacks

| Datum | In `bob` JSON? | Decoded by the app? | Notes |
| --- | --- | --- | --- |
| Note path, `link`, title, kind, state | ✓ | ✓ | `RefItem.id` is the vault-relative note path |
| `source_pdf` | ✓ | ✓ | Resolved to an absolute URL by `RefsLibrary.pdfURL(for:)` |
| `task` (`path`, `block_id`, `link`, `mark`, `archived`) | ✓ | ✓ | The reading-task link is `task.link`, e.g. `[[job_search_2026#^ref-second-wave-job-applications]]` |
| `urls`, `identity.arxiv`, `identity.doi` | ✓ | ✓ | |
| `author`, `published` | ✓ | ✓ | Sparse |
| **Frontmatter / marker `id`** | **✗** (`row.rs:48–49`: "kept out of JSON; only query resolution reads it") | ✗ | **Blocks the headline option** |
| `research_ref` (`research:<path>`) | ✓ | ✗ | Only 1 of 406 PDF rows has it today |
| `captured` | ✓ | ✗ | Not needed |
| Annotation `quote`, `comment`, `page_label`, `kind` | ✓ (`ref show`) | ✓ | The inspector loads `ref show <path> -f json -c` (commented only) |
| Annotation `link` / `block_id` (`[[ref/x#^h-…]]`) | ✓ | ✗ | Additive decode needed for block links (phase 2) |
| Markdown digest (`ref show -f markdown`) | ✓ (stdout text) | ✗ | `BobProcessClient.run` can carry it; about 0.21 s on apollo |

### 2.3 House precedent: Obsidian's Yank Path picker

`bob-navigation-hotkeys` already ships a **"Copy active file path"** picker on **Mod+Y**
(`490-plugin-lifecycle.js:280`). It covers six formats (absolute with tilde, absolute,
basename, basename without extension, parent directory, relative), and each row shows the exact
preview plus a "Copy"/"Unavailable" status (`200-filtered-picker-modals.js:885`). Three
consequences:

- **"Y = yank = copy" is already Bryan's convention.** Choosing `⌃Y` here is consistent, not
  arbitrary.
- **Each row previews the literal value.** I keep that, and make it a hard rule (§8.1).
- **That picker is filter-to-select.** Bryan now explicitly wants single-key selection, which
  is better for a short, fixed catalog: no typing, no Return.

---

## 3. Library facts that shape the design

These are the panel's 406 PDF-backed rows from the vault checkout on apollo, 2026-10-14:

| Fact | Count | Design consequence |
| --- | --- | --- |
| Agent-report chats | **362 (89%)** | Optimize the default card for chats: ID, path, wiki link, file |
| External refs (blogs, papers, docs) | 44 | Source rows (`U`, `L`, `X`) appear only for these |
| Rows with a marker `id` | **329 (81%)** | ID is the right default row |
| `id` == PDF stem | 323 of 329 | Usually derivable from the stem, but **not always** (6 differ, e.g. `sase_task_bead_48h_impact_rating` has id `task_bead_48h_impact_ranking`), so the app must not guess |
| Duplicate IDs | **3 groups, 9 rows** (`BryanBugyi_CV_extended` ×5, `harness_engineering` ×2, `task_bead_48h_impact_ranking` ×2) | `bob ref show BryanBugyi_CV_extended` fails with `ambiguous_reference`, so the card must flag shared IDs and point at `N` |
| Rows with a source URL | 27 | `U`/`L` are hidden most of the time |
| arXiv IDs / DOIs | 9 / 0 | `X` rarely shows and `D` never does today. The rows are cheap, so keep them |
| Rows with any highlight / any comment | 76 / 48 | The notes section is absent in 88% of cards, so the common card stays small |
| Comments per commented ref | 168 total, about 3.5 average, max 16 | Up to 9 digits is plenty; `A` covers the long tail |
| Rows with a reading task / archived | 405 / 26 | `R` almost always shows |
| Title length (median / p90 / max) | 56 / 84 / 123 chars | Previews must truncate; tail truncation for titles |
| Note path length (median / p90 / max) | 41 / 53 / 93 chars | Middle truncation for paths keeps the distinctive stem visible |
| `bob ref show … -f markdown` latency | ≈ 0.21 s (apollo, 1,010-note index) | Prefetch it when the card opens. `A` is then effectively instant |

**Data-quality caveat.** Some older sidecars carry malformed Highlights exports. In
`lib/chat/sase_hacker_news_popularity_strategy_consolidated.md`, quote lines lose their `>`, so
bob parses the continuation as a comment ("prefix." becomes the comment). Copying reproduces
whatever bob parsed. That is the right behaviour for a thin client, but expect a few odd notes
on pre-August references.

---

## 4. Critique: is this a good idea?

**Yes, with the following caveats.**

Why it earns a key:

- **It closes the loop between reading and acting.** Bryan reads agent reports in Highlights
  and then works through agents and Obsidian. The handles those tools need (the ID, the note
  path for `bob ref show`, the wiki link, the reading-task link) are tedious to reconstruct by
  hand. Two of them are impossible to see without opening the note: the reading-task block
  link, and the ID whenever it differs from the stem.
- **"PDF file" is the sleeper hit.** Pasting the actual PDF into Slack, Mail, or an LLM chat
  normally takes a Finder detour. The panel already knows the absolute URL.
- **Copying a note, meaning Bryan's highlight plus his own comment, is the most personal
  option.** The inspector already shows these notes and has them in memory.

Risks, and how the design absorbs them:

| Risk | Mitigation |
| --- | --- |
| A grab-bag menu becomes slow to scan | The catalog is data-driven: only rows the reference actually has. Fixed letters; previews do the explaining; the common card has 7 rows |
| Overlap and inconsistency with ⌘K's copy items | Fold both into "Copy… ⌃Y" (A3) |
| The ID is not in bob's JSON, may differ from the stem, and may not be unique | bob-cli serializes `id` first (A4); the card flags shared IDs |
| The panel stays key after a copy, so `⌘V` pastes into the Refs search field | A copy dismisses the panel at once (A2) |
| A failed async copy (the digest) clobbers the clipboard | Write only after the payload exists (§8.1) |
| `⌃Y` collides with something | Cocoa's field-editor `⌃Y` (yank from the kill ring) is moot, because `⌃K` is already remapped so nothing ever fills the kill ring. Vim's `⌃Y` (scroll one line) is a weaker association than `y` = yank in a panel that does not line-scroll. The Mac check in Phase 0 confirms no global tool intercepts it |
| Future `⌘Y` Quick Look (proposed in the original panel research) sits next to `⌃Y` with a different meaning | If Quick Look ever lands, avoid `⌘Y`. Flagged, not blocking |

**Would I take a different approach?** I would keep the request's shape: one key opens a
chooser, and one more key copies. I would change four things about *how* it is built: an
in-panel card rather than a menu, dismiss with a HUD, a single copy surface, and a bob-first ID.
§9 compares the alternatives I rejected. One complementary idea for later: **drag a row out of
the list** to drop the PDF into Slack or the wiki link into Obsidian, using multi-representation
item providers. It belongs in the backlog, not this feature.

---

## 5. Requirement adjustments (explicitly called out)

| # | Adjustment | Why |
| --- | --- | --- |
| **A1** | The "menu" is an **in-panel SwiftUI card**, not an `NSMenu` popup. | `NSMenu` tracking runs outside the panel's key router (hence `suspendHideOnResign`). Bare letters in an open menu drive type-select by title rather than reliably firing an item (as I understand AppKit; not verified on the Mac). A menu cannot show a rich value preview, cannot hold an async row, and cannot be unit-tested or rendered in the `ImageRenderer` design fixtures. A card is all of those, and it reuses the existing key monitor |
| **A2** | **A copy dismisses the panel immediately** and confirms with a **non-key glass HUD** for about 1.2 s. | After copying, the next step is to paste somewhere else. A panel that stays key would catch `⌘V` in its own search field. Raycast's guidance is the same: when an action closes the window, confirm it with a HUD |
| **A3** | ⌘K's **Copy Wiki Link** and **Copy PDF Path** are replaced by one **Copy… `⌃Y`** item that opens the card. | One copy surface with one behaviour (copy, dismiss, HUD), and ⌘K stays the discoverable path to `⌃Y` |
| **A4** | **The ID ships bob-cli first:** serialize `id` in `ref list`/`ref show` JSON (additive under schema 1). | Thin-client rule. The app can neither read frontmatter nor derive the ID from the stem (6 mismatches). Older `bob` decodes to no ID, so the row simply hides |
| **A5** | **Fixed letters; absent rows hidden but never re-lettered.** Pressing a hidden row's letter explains why the row is missing. | Muscle memory: `I` always means ID. A dimmed row for every absent field would bloat the 89% chat case |
| **A6** | **Scope of "notes/highlights":** digits `1`–`9` are the inspector's **YOUR NOTES** (commented highlights, in note order). `A` copies **all highlights with comments** as bob's Markdown digest. Individual *uncommented* highlights are not separately selectable. | The numbers match what the inspector shows, which is predictable. Uncommented highlights matter as a set, not one by one, and 9 digits can't index 27 of them |
| **A7** | **`⌃Y ⌃Y`** (and `↵`) copy the pre-selected default row: the ID, or the wiki link when there is no ID. | The fastest path for the commonest handle; reads like Vim's `yy` |
| **A8** | **Deliberately excluded:** BibTeX/APA citations, the Summary/Abstract excerpt, the outline, prompt templates, the thumbnail. | Honesty rules. Metadata is too sparse for correct citations (18 of 406 rows have an author). The inspector's excerpts are heuristic and truncated to 360/420 characters, so copying them would hand over clipped text as if it were complete. Prompt templates are personal and drift. The note path already serves agents |

---

## 6. What to copy: the catalog

Visual order is shown below. Hairlines separate the groups; only YOUR NOTES has a header,
matching the inspector's own label.

| Key | Row label | Exact payload (real values) | Source | Shown when | Rows today |
| --- | --- | --- | --- | --- | --- |
| **I** | ID | `second_wave_job_applications` | bob `id` (**new field**) | `id` present | 329 |
| **T** | Title | `Wave 2: The Ten Applications to Send Next (October 2026)` | `title` (raw, verbatim, backticks kept) | always | 406 |
| **W** | Wiki link | `[[ref/chat/second_wave_job_applications]]` | bob `link`, verbatim | always | 406 |
| — | | | | | |
| **U** | Source URL | `https://hamel.dev/blog/posts/evals-faq/` | `urls[0]` | URL present | 27 |
| **L** | Markdown link | `[AI Evals: Everything You Need to Know](https://hamel.dev/blog/posts/evals-faq/)` plus an HTML flavor | title + `urls[0]` | URL present | 27 |
| **X** / **D** | arXiv / DOI | `arXiv:<id>` (same form as the inspector byline) / bare DOI (format examples, not library rows) | `identity` | present | 9 / 0 |
| — | | | | | |
| **N** | Note path | `ref/chat/second_wave_job_applications.md` | `path` | always | 406 |
| **P** | PDF path | `/Users/bryan/bob/lib/chat/second_wave_job_applications.pdf` | `pdfURL(for:)` | PDF resolves | 406 |
| **F** | PDF file | *(the file itself, as a file URL)* | `pdfURL(for:)` | PDF exists on disk | ≈406 |
| **R** | Reading task | `[[job_search_2026#^ref-second-wave-job-applications]]` | `task.link`, verbatim | task present (label gains "· archived" when archived) | 405 |
| — | **YOUR NOTES** | | | | |
| **1**–**9** | p. N | `> {quote}` + blank line + `Comment: {comment}` | inspector `ref show -c` notes | commented highlights loaded | 48 refs |
| **A** | All highlights | bob's `ref show <path> -f markdown` output | bob (stdout) | `annotation_count > 0` | 76 |

Format details:

- **Notes.** The `Comment:` prefix mirrors bob's own Markdown digest
  (`docs/ref.md`, `ref show` Markdown output), so a single note and the full digest read the
  same. A multi-line quote prefixes every line with `> `. Phase 2 adds `⌥1`–`⌥9` for the
  Obsidian block link (`[[ref/…#^h-04d5acf4e72f]]`, bob's annotation `link`, verbatim).
- **Markdown link escaping.** Escape `[`, `]` and `\` in the title, and percent-encode `(`, `)`
  and spaces in the URL. Titles do contain code spans and brackets. The HTML flavor is
  `<a href="…">{escaped title}</a>`, so Mail, Notes, Slack and Google Docs get a rich link,
  while Obsidian, editors and terminals get the Markdown.
- **PDF file.** Write an `NSURL` file URL (`writeObjects`). Do not add a separate string flavor
  unless the Phase 0 check shows a target that needs one, because some apps prefer the string
  flavor and would paste a path instead of attaching the file.
- **PDF path is absolute.** It matches today's ⌘K behaviour and works in every context; `~`
  does not expand inside quoted shell arguments. The `~` form becomes the `⌥P` alternate in
  phase 2, mirroring the Obsidian picker's "with tilde" variant.
- **Note path is vault-relative,** because that is what `bob ref show` and agents take. The
  absolute form becomes `⌥N` in phase 2.
- **Shared IDs.** When another reference shares the ID, the row shows a small orange
  `shared ×5` tag. Its help text reads "bob ref show needs the note path for this one — press
  N". `I` still copies the ID, because Bryan asked for exactly that value; the tag is the honest
  warning.
- **A safety net for `research:` refs.** If a row carries `research_ref`, a phase-2 row `S`
  ("Research artifact", e.g. `research:202608/x/x.md`) can appear. See Q6 for making that
  common.

### 6.1 Candidates considered and rejected (v1)

| Candidate | Verdict |
| --- | --- |
| BibTeX / APA citation | Rejected. Sparse metadata would produce confident-looking but wrong citations. If wanted, it belongs in bob as `bob ref cite`, never as app-side formatting |
| Summary / Abstract excerpt | Rejected. It is heuristic and truncated (`RefsSummaryExtractor` caps at 360/420 characters) |
| Contents outline | Rejected. Low value and capped at 6 headings |
| `obsidian://open?path=…` URL | Deferred to `⌥W` in phase 2. Useful outside Obsidian, but rare |
| Uncommented highlight N | Covered by `A` (A6) |
| "Agent prompt" snippet (`Read my notes: bob ref show … -c -f markdown`) | Rejected. Personal and drifts; `N` plus the agent's own skill already covers it |
| Page-1 thumbnail image | Rejected. Novelty, not a workflow |
| Narration MP3 file | Deferred. 24 rows; could be `⌥F` later |

---

## 7. Interaction design

### 7.1 Opening

- **`⌃Y`** with a selected, available row opens the card. With no selected row it returns nil
  and passes through, exactly like `⌘K`. While the IME is composing it passes through, like
  `⌃D`/`⌃U`.
- The card opens with **no delay**. Which-key popups often wait about 0.5–1 s, because
  experienced users rarely need them. Here the card also serves as the **preview of what will
  be copied**, so it should be visible at once. Model state is set synchronously, so fast
  typists can press `⌃Y I` before the first frame and still get the right copy.
- Opening the card requests inspector hydration immediately, skipping the 120 ms debounce, so
  the notes section fills quickly. It also prefetches the `A` digest when
  `annotation_count > 0`.
- The rows' **values are frozen when the card opens**, like the frozen listing. A library
  refresh never changes what a letter copies mid-gesture. Notes still loading fill in when they
  arrive, without moving existing rows.

### 7.2 Keys while the card is open

The card captures **every** keyDown, so nothing leaks into the query.

| Key | Action |
| --- | --- |
| Letter or digit of a visible row | Copy that row, then dismiss and show the HUD |
| Letter of a hidden row | The card footer explains, e.g. "No source URL for this reference" or "No ID for this reference — N copies the note path" |
| Any other printable key | The card footer reads "Nothing on ‘q’" for 1.5 s. No beep, no shake |
| `↵`, `⌃Y`, `Y` | Copy the selected row. The default selection is ID, else Wiki link |
| `↑`/`↓`, `⌃P`/`⌃N`, `⌃K`/`⌃J` | Move the selection (wraps). Same keys as the list |
| `esc`, `⌃[` | Close the card and return to the inspector. The query, scope and selection are untouched |
| Mouse | Hover highlights a row; click copies it. A click outside the card closes it |

Letters match on `charactersIgnoringModifiers` (lowercased), so the mnemonic follows the
keyboard layout's printed letter. `⌃Y` itself stays a keyCode entry in `RefsKeyRouter`, like
every existing binding. `charactersIgnoringModifiers` ignores `⌥`, so the phase-2 `⌥`
alternates fit without remapping.

The **Esc ladder** becomes: card → banner → query → scope → close.

### 7.3 After a copy

1. **Synchronous rows** (`I T W U L X D N P F R 1–9`): build the payload, write the pasteboard,
   check the result, hide the panel, show the HUD, and post a VoiceOver announcement
   ("Copied ID").
2. **`A` (async):** if the prefetched digest is ready, the same as above. If not, the `A` row
   shows a spinner and "Copying…", every key except `esc` is swallowed (`esc` cancels), and the
   copy happens the moment bob returns. After a 5 s timeout, or on a non-zero exit, the card
   stays open with a red footer ("Couldn't load highlights · {bob's message}") and **the
   clipboard is untouched**.
3. **`F` with a file that vanished since the snapshot:** the card stays open, and its footer
   reads "PDF not found on disk".
4. **A pasteboard write that fails** (rare): the HUD turns orange and reads "Couldn't copy".

### 7.4 Interplay

- Hiding the panel (resign key, the global hotkey toggle, or the takeover key) closes the card.
  `prepareForPresentation` resets it, so the next show never opens with the card up.
- Reopening the panel while the HUD is up removes the HUD at once.
- ⌘K → **Copy… `⌃Y`** opens the card. The `NSMenuItem` also carries `⌃Y` as its key
  equivalent, so `⌃Y` inside the open menu does the same thing.

---

## 8. Visual design

### 8.1 Principles

1. **What you see is what you copy.** Previews come from the same function that builds the
   payload (`RefsYankRow.payload`). Truncation with an ellipsis is the only difference, and it
   is tested.
2. **Absence stays absence.** This is the panel's existing honesty rule: no "Unknown", no
   dimmed placeholders.
3. **One family.** The card reuses the inspector's typography, the `RefsKindTile`, the list's
   selection capsule, and the footer's caption style. It should read as the inspector "turned
   over", not as a foreign modal.
4. **Never clobber the clipboard on failure.** Write only once the payload exists.

### 8.2 Typical agent-report chat (89% of rows)

Real values; the two neighbouring list rows are illustrative.

```text
╭────────────────────────────────────────────────────────────────────────────────────────────╮
│ ⌕  wave 2                                               [All ⌘1]                  3 of 406 │
├──────────────────────────────────────────────┬─────────────────────────────────────────────┤
│▸[💬] Wave 2: The Ten Applications to Se…  ◐  │ [💬]  COPY                                   │
│      Chat · yesterday · job_search_2026       │       Wave 2: The Ten Applications to Send…  │
│ [💬] Wave 1: The First Ten Applications   ✓  │                                              │
│      Chat · Oct 2                             │ ▌[I]  ID            second_wave_job_applica… │
│ [💬] Waveform Rendering Notes             ○  │  [T]  Title         Wave 2: The Ten Applica… │
│      Chat · Sep 12                            │  [W]  Wiki link     [[ref/chat/second…ions]] │
│                                               │  ─────────────────────────────────────────── │
│                                               │  [N]  Note path     ref/chat/second…ions.md  │
│                                               │  [P]  PDF path      /Users/bryan/bob/…ns.pdf │
│                                               │  [F]  PDF file      second_wave_job_a….pdf   │
│                                               │  [R]  Reading task  [[job_search_2026#^r…]]  │
│                                               │                                              │
│                                               │  ↵ copies ID · ↑↓ choose · esc back          │
├──────────────────────────────────────────────┴─────────────────────────────────────────────┤
│ Copy — press a key                                                          Updated 2m ago │
╰────────────────────────────────────────────────────────────────────────────────────────────╯
```

### 8.3 Annotated external reference (the dense case)

```text
 [🎓]  COPY
       2026 goals as first class abstractions in hum…
 ▌[I]  ID            2026_goals_as_first_cla…tionxp26
  [T]  Title         2026 goals as first class abstr…
  [W]  Wiki link     [[ref/papers/2026_goal…tionxp26]]
 ─────────────────────────────────────────────────────
  [U]  Source URL    https://www.microsoft.com/…0982.pdf
  [L]  Markdown link [2026 goals as first class…](…)
 ─────────────────────────────────────────────────────
  [N]  Note path     ref/papers/2026_goals_as…xp26.md
  [P]  PDF path      /Users/bryan/bob/lib/pap…xp26.pdf
  [F]  PDF file      2026_goals_as_first_cl….pdf
  [R]  Reading task  [[sase_goals#^ref-2026-goals-a…]]
 YOUR NOTES 13 · quote + comment
  [1]  p. 1   ↳ “at any altitude”!
  [2]  p. 2   ↳ #task Planner agents should run the `sa…
  [3]  p. 3   ↳ #task Goals should be used to maintain…
  [A]  All highlights   27 highlights · 13 comments · Markdown
       +10 more notes — A copies them all
 ↵ copies ID · ↑↓ choose · esc back
```

Note rows preview **Bryan's comment** (`↳`, matching bob's human output). His own words are the
most recognizable to him. The full quote and comment show on hover (`.help`), and the section
header states the payload format.

### 8.4 Tokens

| Element | Spec |
| --- | --- |
| Placement | The inspector column (≥ 760 pt panels, effectively always). Below that width, the card covers the list column. The card never resizes the panel |
| Header | `RefsKindTile` at 28 pt; "COPY" in `.caption.weight(.semibold)` `.secondary` (inspector section-label style); the title in `.headline`, one line, tail-truncated |
| Row | 24 pt, single line: keycap, then label (92 pt fixed, `.callout`), then preview (fills the rest) |
| Keycap | 18 × 18 pt, radius 4.5, fill `.primary.opacity(0.06)`, stroke `.primary.opacity(0.14)` at 0.5 pt (1 pt under Increase Contrast), SF Mono 11 pt semibold, uppercase glyph (pressed without Shift, like menu key equivalents). On the selected row: accent fill, white glyph |
| Preview | SF Mono 11.5 pt, `.secondary`. `.middle` truncation for IDs, paths and links; `.tail` for titles and notes |
| Groups | 0.5 pt hairlines (the inspector divider style) with 4 pt vertical padding. Only YOUR NOTES gets a header, counted with `.caption2.monospacedDigit()` like the inspector |
| Notes capacity | As many note rows as fit the fixed column height, at most 9, then the "+N more — A copies them all" line. Computed from geometry, never by scrolling |
| Shared-ID tag | An orange capsule, `.caption2`, "shared ×5" |
| Card footer | `.caption` `.secondary`; it doubles as the inline message line (hidden-row hints, errors in red) |
| Panel footer | While the card is up, the hints read "Copy — press a key". Otherwise the hints gain `⌃Y Copy` after `⌘K Actions` |
| Motion | Cross-fade plus a 6 pt rise over 0.14 s easeOut, the inspector's note-reveal vocabulary at a faster tempo. Reduce Motion: cross-fade only. Selection moves instantly |
| HUD | A borderless non-activating `NSPanel` with `canBecomeKey = false`, `ignoresMouseEvents = true`, the Refs panel's collection behaviour, and an `NSGlassEffectView` capsule. Content: `checkmark.circle.fill` (green), "Copied ID" (13 pt semibold), and the value (SF Mono 11.5, `.secondary`, middle-truncated, max 380 pt). Centered on the panel's former frame. Fade in 0.1 s, hold 1.0 s, fade out 0.3 s; Reduce Motion: no scale |
| Accessibility | The card is one container ("Copy menu for {title}, 7 options"). Each row reads "ID, second_wave_job_applications, key I". Opening announces "Copy menu. Press a letter or number." A copy announces "Copied ID". Hidden rows are absent from the accessibility tree too |

---

## 9. Alternatives considered

| Alternative | Verdict |
| --- | --- |
| **`NSMenu` with key equivalents** (a ⌘K clone) | Rejected (A1). It needs a modal tracking loop, its letter behaviour is unreliable, it cannot show previews or an async row, and it cannot be rendered in a fixture |
| **A "Copy" submenu inside ⌘K** | Rejected for the same reasons, plus a third level of depth |
| **A filter-to-select picker** like the Obsidian Yank Path picker | Rejected for this surface. Bryan asked for single-key selection, and with ≤ 14 fixed rows typing a filter is slower than a mnemonic. Its preview-per-row discipline is kept |
| **Which-key with a show delay** (`⌃Y` then a letter, the popup only after about 0.5 s) | Partially adopted: keys work before the paint. Rejected the delay, because the preview is the confidence |
| **`⌃Y` copies the ID directly, `⌃⇧Y` opens the menu** | Rejected. Two keys to learn, and an invisible default. `⌃Y ⌃Y` gives the same speed and shows the value |
| **"Smart" `⌘C`** (copy the wiki link when the search field has no text selection) | Rejected for now. It is invisible and surprises text-editing muscle memory. Could be revisited later as `⌘C` meaning "the default row" |
| **Copy and keep the panel open** (today's ⌘K behaviour), or `⇧`+letter to stay | Rejected. `⌘V` would hit the search field, the Esc ladder costs up to 3 presses, and the clipboard holds one item anyway |
| **Most-recently-used preselection** (`⌃Y ⌃Y` = "same kind as last time") | Deferred. It is a nice repeat-yank, but a fixed default is more predictable. Revisit if Bryan finds himself batch-copying IDs |
| **Drag a row out** (file or wiki link by drop target) | Complementary. Backlog |

---

## 10. Implementation plan

The work follows the `bob-mac-capture` `AGENTS.md` rules: never land Swift that has not been
compiled; RefsCore builds on Linux through `just portable-check`, while the app target needs
the Mac or CI.

**Phase 0: Mac checks (about 30 min, before Phase 3 lands).**

1. `⌃Y` reaches the Refs local monitor; no system, Karabiner or Hammerspoon binding intercepts
   it.
2. After hide, `⌘V` pastes immediately in Highlights, Obsidian and Terminal, confirming key
   status returns to the frontmost app.
3. A file-URL paste attaches the PDF in Finder, Slack, Mail, Messages, the Claude desktop app
   and ChatGPT. Record what text-only targets receive.
4. The HTML flavor gives a rich link in Mail, Notes and Slack, and Markdown in Obsidian.
5. The HUD never takes key, and it appears on the active Space and over full-screen Highlights.

**Phase 1: bob-cli (small).** In `src/native/ref_library/row.rs`, drop `skip_serializing` from
`id` and place it after `title`. It serializes as `null` when absent, additive under
`REF_SCHEMA_VERSION` 1. Update the `docs/ref.md` JSON-envelope field list and the JSON tests.
`ref show` inherits the field.

**Phase 2: RefsCore (Linux-testable).**

- Decode `id` into `RefRecord.id` and `RefItem.markerID` with `decodeIfPresent`, and round-trip
  it through the snapshot cache encoder.
- Decode annotation `link` and `block_id` (additive) for phase-2 block links.
- Add `RefsYankCatalog.rows(item:notes:sharedIDCount:pdfExists:) -> [RefsYankRow]`: a fixed
  key, label, payload kind and value per row; hidden rows omitted.
- Add `RefsYankFormat`: the Markdown-link and HTML escaping, the note blockquote, preview
  truncation, and the default-row rule.
- Add `RefsYankKeyMap.command(characters:keyCode:modifiers:rows:)`, which returns
  `.copy(row)`, `.copySelected`, `.move(±1)`, `.close`, `.explainHidden(key)` or `.unknown`.
- Build a shared-ID index from the snapshot.
- Unit tests: payload equals the untruncated preview, escaping, hidden rows, fixed letters,
  shared IDs, an older `bob` without `id`, chat versus external catalogs.

**Phase 3: app target.**

- `RefsKeyRouter`: add `⌃Y`, which becomes `.showCopyCard` (IME pass-through).
- `RefsPanelModel`: `@Published var copyCard: RefsCopyCardState?`, holding the frozen rows,
  the selection, the async digest status and the message line. The Esc ladder and
  `prepareForPresentation` reset are updated.
- `RefsPanel`: while the card is open, route all keys to `RefsYankKeyMap`.
- `RefsFetching`: `showMarkdown(path:)` via `BobProcessClient.run` on a `refs-yank` lane with a
  5 s timeout and a small LRU keyed by path and snapshot time.
- Pasteboard: grow `RefsPasteboardWriting` to
  `write(_ payload: RefsClipboardPayload) -> Bool`, with plain text, optional HTML and optional
  file URL, and add the `org.nspasteboard.source` marker (bundle ID). Keep `copy(_:)` for
  diagnostics.
- `RefsCopyCardView`, which replaces the inspector column; `RefsCopyHUD`.
- ⌘K: replace the two copy items with **Copy… `⌃Y`**.
- Footer hints, README key table, Esc-ladder line, and the ⌘K section.
- Tests: router (`⌃Y`, IME), model (open/close, frozen rows, async success, failure,
  clipboard untouched, hide on copy) with the fake pasteboard; design fixtures in light, dark
  and Increase Contrast for the chat card, the annotated paper, the shared ID, and a missing
  PDF.

**Phase 4: polish (optional).** `⌥` alternates. Holding `⌥` live-swaps the previews, which is
the macOS menu alternate idiom and needs a `.flagsChanged` monitor: `⌥P` path with `~`, `⌥N`
absolute note path, `⌥W` `obsidian://` URL, `⌥1–9` block link, `⌥A` comments-only digest, `⌥F`
narration file. The card footer gains "⌥ more formats".

Size estimate: Phase 1 is small (one field, docs, tests). Phases 2 and 3 are medium (one new
view, one small window, one router table, a pasteboard protocol bump, tests and fixtures).
Phase 4 is small.

---

## 11. Open questions for Bryan

1. **Default row:** is the ID the right `⌃Y ⌃Y` target, or do you paste wiki links more often?
   The default selection is one constant either way.
2. **Note format:** `> quote` + `Comment: …` (bob's digest convention), or the quote alone?
3. **PDF path:** absolute (today's ⌘K) or `~/bob/…` by default?
4. **Copy dismisses the panel:** confirm. This is the one behavioural change to existing ⌘K
   copies.
5. **Shared IDs:** keep copying the shared ID with a warning (recommended), or make `I` copy the
   note path when the ID is ambiguous? The second is safer for agents but surprising.
6. **`research:` handles:** should `bob ref create --include-id`, run from the research hook,
   also stamp the repo-relative `research` path? That would make an `S` row
   (`research:202610/…/x.md`) light up for every new agent report, the handle agents can
   `sase artifact read` directly. It is a separate bob-cli change and out of scope here.

---

## 12. Recommended solution

**Ship the `⌃Y` Copy card in three steps: bob-cli first, then RefsCore, then the app.**

- **Phase 1 (bob-cli):** serialize the marker/frontmatter `id` in `bob ref list`/`ref show`
  JSON, additive under schema 1, with docs and tests.
- **Phase 2 (RefsCore, testable on Linux):** decode `id` and the annotation `link`; build the
  pure catalog, formatter, key map and shared-ID index, with tests.
- **Phase 3 (app):**
  - `⌃Y` opens an in-panel **Copy card** that replaces the inspector column.
  - Each row is a fixed mnemonic **keycap**, a **label** and a literal **preview**:
    `I T W · U L X/D · N P F R · YOUR NOTES 1–9 · A`.
  - Absent rows are hidden but never re-lettered.
  - `↵`, `⌃Y ⌃Y` or `Y` copy the default row (ID, else Wiki link). Arrows and `⌃N`/`⌃P` move
    the selection. `esc` returns to the inspector.
  - **A copy hides the panel immediately** and confirms with a non-key glass **HUD** showing
    what was copied.
  - `A` uses bob's Markdown digest, prefetched when the card opens, and never touches the
    clipboard on failure.
  - `F` puts the PDF itself on the pasteboard.
  - `L` carries both Markdown and HTML.
  - ⌘K's copy items fold into **Copy… `⌃Y`**.
- **Gate** Phase 3 on the 30-minute Mac checks in §10, and keep **`⌥` alternates** as an
  optional Phase 4.

This keeps the request's core idea (one key opens the chooser, one key copies) and makes it
*intuitive* (fixed mnemonics, house "Y = yank" precedent, literal previews), *reliable*
(the ID comes from bob, frozen rows, every key captured, the clipboard is never clobbered,
`⌘V` lands where you expect), and *beautiful* (the inspector "turns over" in the panel's own
type and materials, a calm 7-row card for the common case, a glass HUD instead of a
lingering panel).

---

## Sources

- [Raycast API — HUD](https://developers.raycast.com/api-reference/feedback/hud): use a HUD to
  confirm an action that closes the main window, such as a clipboard copy
- [Raycast API — Clipboard](https://developers.raycast.com/api-reference/clipboard)
- [Raycast API — Actions](https://developers.raycast.com/api-reference/user-interface/actions)
- [nspasteboard.org — Identifying and Handling Transient or Special Data on the Clipboard](https://nspasteboard.org/):
  the `org.nspasteboard.source` marker, and the transient/concealed markers deliberately *not*
  used here
- [Emacs Redux — which-key is now built in](https://emacsredux.com/blog/2026/07/18/which-key-is-now-built-in/):
  which-key idle-delay conventions
- [GNU which-key.el source](https://doc.emacsen.de/30.2/src/which-key.el.html): the default
  1.0 s idle delay
- Local: `bob-mac-capture` @ `44051a0`, `bob-cli` @ `ae9e6ef`, `bob-plugins` @ `5e4bfae`,
  `research:202610/highlights_quick_open_refs_panel/highlights_quick_open_refs_panel.md`,
  `decisions:mac-capture-is-a-thin-client`
