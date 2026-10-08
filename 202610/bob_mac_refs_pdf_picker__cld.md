---
title: "Bob Refs: a quick-open reference picker for Highlights"
author: cld
date: 2026-10-08
---

# Bob Refs: a quick-open reference picker for Highlights

**Question.** Highlights is a good reader but a bad library: choosing a PDF through its Open… dialog is
slow and gives no context. Bryan proposed a new `bob-mac-refs` Swift app, modelled on Bob Mac Capture.
A global hotkey would open a picker over the PDFs in `~/bob/lib/`. Each PDF would show what it is (paper,
chat, article…), the list would filter as he types, and the panel would be rich, intuitive, reliable and
beautiful. This report checks whether that is the right plan, proposes changes, and designs the feature.

## 1. Bottom line

- **The idea is good, and its value is concentrated.** The library already holds 339 PDF-backed reference
  notes and grows by roughly 10 a day: 82 were added in the first 8 days of October, almost all agent
  reports. Highlights on macOS has no library view, no quick-open and no AppleScript support. Nothing
  else on the Mac knows a PDF's reading state, kind, plan membership or annotations, so nothing else can
  rank them well. A native picker fills a gap that will keep widening.
- **Adjustment: build it as a second panel in the existing Bob Mac Capture app, not as a new app.**
  - The capture app already has nearly every part this needs: a Carbon hotkey, a prewarmed non-activating
    `NSPanel`, a picker card (sections, chips, detail strip), an fzf-style `FuzzyMatcher`, a key router, a
    `bob` process client (lanes, timeouts, concurrent pipe drain), an FSEvents vault watcher, a login item,
    an install pipeline, macOS CI and a 4.5k-line fake-`bob` test harness.
  - Most of that code is internal to the executable target. A second app would mean copying it or
    extracting a shared kit first, and it would add a second menu-bar icon, login item, Settings window,
    install path and CI pipeline.
  - What counts is the *module* boundary (a Foundation-only `RefsCore`), not a process boundary.
- **Adjustment: the source of truth is bob's reference index, not a directory listing of `lib/`.**
  - `bob ref list -A -R all -f json` already returns every reference note with title, `ref_type`, origin,
    reading state, parent, dates, PDF path, audio, and annotation and comment counts.
  - It took 127 ms on the Mac for a 740 KB payload.
  - Under the accepted rule [Bob Mac Capture Is A Thin Client Of bob](#sources), the app may filter and
    rank what `bob` returns but must not re-derive vault semantics. Version 1 needs **no bob-cli changes**:
    it consumes three existing JSON contracts (`ref list`, `ref show`, `plan`).
- **Sorting is two different problems, and I treat them that way.**
  - **Empty query:** intent-ordered sections that mirror bob's own lane order: **Today → Just added →
    Reading → Next → Ready → Recently opened → Library**. "Today" means PDFs whose `^ref` task is linked
    under today's open Pomodoros; three such PDFs exist right now.
  - **Typed query:** a flat list ranked by match tier: learned pick > exact > word match (prefix,
    word-boundary or acronym) > fuzzy > secondary field. Title-prefix, whole-word, lane and frecency
    bonuses only order rows *within* a tier. Spotlight full-text hits follow in a separate "Found in
    text" section.
- **Kind and reading state are two separate axes, and both are always visible.**
  - Kind is a tinted glyph tile plus a text label: Chat, Paper, Article, Doc.
  - Reading state is the vault's own checkbox vocabulary, using the glyphs Bob Mac Capture already uses:
    Reading `[/]`, Next `[*]`, Ready `[ ]`, Read `[x]`, Dropped `[-]`.
- **Adjustment: also take over ⌘O inside Highlights (opt-in)**, besides a global hotkey.
  - The app registers a Carbon hotkey only while Highlights is frontmost, so the shortcut Bryan already
    reaches for opens the good picker, and no other app loses ⌘O.
  - The request says ⌃O; Highlights' stock Open… shortcut is ⌘O. Bind whichever Bryan actually uses.
- **Open with LaunchServices** (`NSWorkspace.open(_:withApplicationAt:configuration:)` with bundle id
  `net.highlightsapp.universal`, verified on the Mac).
  - Use `highlights://<stem>#page=N` only for "jump to this highlight", and only when the stem is
    unique. The stem `harness_engineering.pdf` exists in both `lib/blogs/` and `lib/papers/`.

The full recommendation is in [§10](#10-recommended-solution).

## 2. What I verified

All of this was measured on athena and, read-only over Tailscale SSH, on the MacBook on 2026-10-08.

| Fact | Evidence |
| --- | --- |
| 338 PDFs in `~/bob/lib/{chat,papers,blogs,docs}`: 310 / 8 / 9 / 11; 340 a few hours later as new reports landed | `find` on athena; 338 on the Mac too |
| 339 PDF-backed ref notes; **0 orphan PDFs**; 1 note points at a missing PDF (`lib/chat/AGENTS.pdf`) | `bob ref list -A -R all -f json` joined with the filesystem |
| By `ref_type`: chat 311, docs 11, blogs 9, papers 8; origin: agent-report 311, external 28 | same |
| Reading state of PDF-backed notes: finished 295, dropped 19, queued 18, started 7 | same |
| `added` is present on only 57 of 339 notes without `-g`; with `-g` (git backfill) on 339 of 339 | `bob ref list … -g` |
| `bob ref list -A -R all -f json`: 54–67 ms on athena, **127 ms on the Mac**; with `-g`: 2.1 s athena, **1.3 s Mac** | timed |
| `bob ref show <path> -f json`: ~50 ms warm on athena (800 ms cold), 130 ms on the Mac | timed |
| `bob plan -f json` returns `today_tasks[].path`, including 3 `ref/chat/*.md` notes today, plus the Pomodoro `entry_name` | live output, 333 ms |
| File mtimes are useless as "added" dates: 203 chat PDFs share one mtime (Oct 3 14:01) | `ls -la` |
| Highlights: bundle id `net.highlightsapp.universal`, v2026.1.2, registers the URL scheme `highlights`, is an NSDocument app (`NSDocumentClass = Highlights.Document`), and lists `.md`/`.textbundle` as related items (the sidecar mechanism) | `plutil` on the Mac's `Info.plist` |
| Highlights exports page links as `highlights://<stem>#page=N` (stem only, no path) | real sidecars in `~/bob/lib/**.md` |
| Highlights is not scriptable ("No, not yet") and has no Mac library or quick-open | [Highlights FAQ](https://highlightsapp.net/faq/), [features](https://highlightsapp.net/features) |
| Spotlight indexes the library: `kMDItemTitle`, `kMDItemNumberOfPages`, `kMDItemLastUsedDate`, `kMDItemUseCount` are populated, and `mdfind -onlyin ~/bob/lib` finds full-text hits | `mdls` and `mdfind` on the Mac |
| Highlights' Open Recent list and its container prefs are TCC-protected ("Operation not permitted") | `ls` over SSH |
| New reports reach `lib/` through a Mac cron job (`*/15 * * * * maybe_bob_highlights_sync -w`); `xlib/` is gitignored and normally empty on the Mac | `crontab -l` on the Mac, `git check-ignore` |
| Alfred 5 and Hammerspoon run on the Mac (Alfred has 0 workflows); Raycast is not installed | `/Applications`, `pgrep` |
| `CaptureCore` (Foundation-only) **builds on athena** with Swift 6.0.3 for Linux in 14 s | `swift build --target CaptureCore` with a scratch path outside the repo |

The last row matters for planning. The thin-client decision record says agent hosts have no Swift
toolchain, and that is out of date for athena. Pure ranking and sectioning logic in a Foundation-only
target can be test-driven by agents here; only AppKit and SwiftUI need macOS CI.

## 3. Critique: is this a good idea?

**Yes, the problem is real.** The pain is not reading, it is *finding*.

- The Open… dialog shows 310 snake_case filenames in `lib/chat/` with no title, kind, status or date.
- Bryan's library has something better than filenames: a bob-maintained index with a status lifecycle,
  plan membership, annotations and provenance.
- The picker's whole job is to bring that index to the moment of opening.

### Alternatives considered

| Option | Global hotkey | Rich detail | Ranking control | Uses bob semantics | Effort | Verdict |
| --- | --- | --- | --- | --- | --- | --- |
| Highlights ⌘O / Open Recent | in-app only | none | none | no | 0 | the problem itself |
| Spotlight (⌘Space, file mode) | yes | none | none | no | 0 | finds titles (`kMDItemTitle` is set), but opens the *default* app, mixes in everything, no status |
| Alfred Script Filter → `bob ref list` JSON | yes | title + subtitle + icon only | some (`uid` learning) | yes | ~1 day | needs the Powerpack, which is probably not owned (0 workflows); no detail pane; fine as a stopgap |
| Hammerspoon `hs.chooser` | yes | text + subtext + image | full (Lua) | yes | ~1 day | a step back: Bob already replaced a Hammerspoon pop-up with a native app |
| Raycast extension | yes | good (`List` + `isShowingDetail`) | limited | yes | ~2 days | not installed; ranking is opaque; a third-party dependency |
| Obsidian command "Open in Highlights" + Quick Switcher | Obsidian only | note preview | none | partly | ~0.5 day | a nice complement, not a global picker |
| **New `bob-mac-refs` app (as proposed)** | yes | full | full | yes | high | duplicates hotkey, panel, process client, install, CI, login item and menu bar, or forces a big extraction first |
| **Refs panel inside Bob Mac Capture (recommended)** | yes | full | full | yes | medium | reuses everything; one app, one icon, one Settings; cross-panel synergies |

### Why one app beats two

1. **Reuse is real, but trapped.** The `CaptureCore` library product already exports `BobProcessClient`,
   `BobExecutableResolver`, `BobEnvironmentBuilder`, `FuzzyMatcher` and `CapturePickerNavigation`. The
   rest is internal to the executable target: `HotKeyManager`, the panel factory with its show/hide and
   key monitor, `CapturePickerFilterField`, `CapturePickerKeyHints`, row styling and
   `CaptureEditorPalette`.
   - A second app must either copy those (which drifts) or wait for an extraction.
   - Inside the same target they are simply available, and extraction can happen later, only if it pays.
2. **Operational surface.** Each separate app adds:
   - a menu-bar icon, a login item and a Settings window;
   - a `bob` path override that can drift out of sync with the capture app's;
   - an install/relaunch helper, a CI pipeline and a release process.
   For a single-user tool, those duplicates are where unreliability creeps in.
3. **Synergy.**
   - In the capture panel, a URL with verdict `in_library` can open the PDF in Highlights through the
     refs module.
   - From the refs panel, a "Capture follow-up…" action can open the capture panel pre-filled with
     `[[ref/chat/<stem>]]`.
   - Both panels share the vault watcher and `bob` health diagnostics.
4. **Isolation still exists where it matters.**
   - Keep the refs logic in a separate Foundation-only target (`RefsCore`, testable on Linux), and its UI
     in its own files and controller.
   - Crash isolation between two tiny panels is not worth two of everything.

**If Bryan still wants a separate app:** do the extraction first. Create a `BobMacKit` library target in
the same package, holding the process client, resolver, hotkey manager (generalized to N hotkeys), panel
shell, filter field, key hints and palette. Then build `BobMacRefs` as a second executable in the
*same repo*. A new repo is the most expensive option of all.

**Naming.** The repo stays `bob-mac-capture` for now. The README's first line becomes "menu-bar app for
Bob: capture and references". A rename can wait until a third panel exists.

## 4. Adjustments to the requirements

| # | Original | Adjusted | Why |
| --- | --- | --- | --- |
| R1 | New `bob-mac-refs` Swift app | A **Refs panel inside Bob Mac Capture** with its own hotkey, controller and `RefsCore` target | §3; less code, fewer moving parts, same isolation where it matters |
| R2 | List "the PDFs in `~/bob/lib/`" | List **PDF-backed reference notes** from `bob ref list`; any `lib/` PDF without a note shows in an "Unindexed" footer (0 today) so nothing is ever invisible | Status, kind, title, dates and annotations live in the index, not the file; the thin-client rule |
| R3 | "Make clear whether it is a paper, a chat, an article…" | Show **two orthogonal axes** on every row: *kind* (Chat, Paper, Article, Doc…) **and** *reading state* (Reading, Next, Ready, Read, Dropped), plus Today and Unopened markers | Kind alone can't answer "what should I open next?"; state can |
| R4 | One keymap | **Global hotkey** (default proposal ⌃⇧⌘R, configurable) **plus opt-in ⌘O takeover while Highlights is frontmost** | Fixes the pain at the moment it happens without stealing ⌘O system-wide |
| R5 | Type to filter | Type to filter **titles and stems**, plus **Spotlight full-text** as a secondary section, plus **kind scopes** on ⌘1–⌘5 | Agents' snake_case stems are memorable, so match them; full text catches the "which report mentioned X?" case |
| R6 | (implicit) opening marks progress | **Opening never changes reading state.** Status edits stay explicit (Obsidian or the Highlights marker); a later "Mark as Reading" action would need a new bob verb first | The decision records keep lanes user-owned; an open is not a status gesture |
| R7 | Kind label "chat" | Keep **"Chat"** as the label (Bryan's term and the folder name); the detail pane adds the origin, "Agent report", plus the swarm model or consolidated variant when the stem says so | Respects existing vocabulary while adding the accurate provenance |
| R8 | (unstated) | **Rows never move under the cursor.** Data that arrives after the panel is shown updates rows in place but re-sorts only on the next keystroke or the next open | The single biggest reliability property of a "hotkey, ↵" picker |

## 5. Architecture

### 5.1 Ownership

| Concern | Owner | Notes |
| --- | --- | --- |
| Which notes exist, their kind, status, reading state, dates, annotations, plan membership | **bob** (`ref list`, `ref show`, `plan`) | Never parse ref frontmatter in Swift |
| Filtering, ranking, sectioning, frecency, learned query→pick associations | **app** (`RefsCore`) | Same "presentation-only" precedent as the capture pickers (README l.355-362) |
| PDF intrinsics: page count, outline, thumbnail, word count | **app** (PDFKit / Spotlight), cached by content hash | Not vault semantics; zero bob cost |
| Open history | **app** (Application Support) | Per-machine, never in the vault, so no git churn |
| Opening the PDF | **app** (`NSWorkspace`) | LaunchServices grants the sandboxed Highlights access to the file |

### 5.2 Calls and caching

```text
launch / FSEvents(ref/, lib/) debounced 0.5 s / panel open if snapshot > 60 s old
  -> bob ref list -A -R all -f json          (~130 ms on Mac)  -> Snapshot (in memory + disk)
  -> bob ref list -A -R all -g -f json       (~1.3 s, background lane) -> merge added/finished dates
panel open
  -> bob plan -f json                        (~0.3 s, background) -> Today set (cached from last run)
  -> NSMetadataQuery(lib/**.pdf)             (live) -> lastUsedDate, useCount, pages
selection change (debounce 80 ms, lane "detail", cancels previous)
  -> bob ref show <path> -f json             (~130 ms) -> annotations, notes, tasks (LRU cache)
  -> PDFKit on a background queue             -> outline, word count, page-1 thumbnail (disk cache)
typing (no process)
  -> RefsCore.rank(snapshot, query, scope, signals)   (< 1 ms for 339 rows)
  -> NSMetadataQuery full-text, debounced 150 ms, only for queries of 3+ characters -> "Found in text"
```

- **Show latency target:** under 50 ms from hotkey to a painted, focused panel. The panel is prewarmed
  and the snapshot is already in memory, so no process runs on the hot path. Bob Mac Capture already
  prewarms its panel the same way.
- **Staleness:** a dim footer shows "Library as of 2 min ago". If a refresh failed, the footer turns
  amber with Retry and Copy Diagnostic (the capture app's error pattern).
- **The `-g` pass** is the only slow call. It runs in its own background lane, and its dates are
  persisted so a cold start shows correct dates instantly.
- **Two optional bob-cli follow-ups:**
  - expose `source_pdf_sha256` and `pdf_exists` on index rows, for cache keys and missing-file badges;
  - cache git-date backfill so `-g` costs about the same as a plain list.

  Both are additive. Neither blocks version 1.

## 6. Taxonomy and visual tokens

**Kind.** Shown as a glyph tile plus a label, never colour alone. Tints avoid the status hues.

| `ref_type` | Label | SF Symbol | Tint |
| --- | --- | --- | --- |
| `chat` | Chat | `bubble.left.and.bubble.right` | purple |
| `papers` | Paper | `graduationcap` | teal |
| `blogs` | Article | `newspaper` | pink |
| `docs` | Doc | `book.closed` | brown |
| `books` | Book | `books.vertical` | indigo |
| `slides` / `code` / other | Slides / Code / title-cased raw value | `rectangle.on.rectangle` / `chevron.left.forwardslash.chevron.right` / `doc` | secondary |

Only the first four have PDFs today. An unknown `ref_type` falls back gracefully instead of failing to
decode.

**Reading state.** This reuses `CaptureEditorPalette.taskStatus` exactly, so both panels speak one
language.

| Vault mark | Label | Glyph | Colour |
| --- | --- | --- | --- |
| `[/]` wip | Reading | `circle.lefthalf.filled` | orange |
| `[*]` next | Next | `circle.inset.filled` | blue |
| `[ ]` ready | Ready | `circle` | secondary |
| `[x]` read | Read | `checkmark.circle` | green |
| `[-]` abandoned | Dropped | `xmark.circle` | secondary |
| none / conflict | — | `circle.dashed` | secondary |

**Markers.**

| Marker | Rendering |
| --- | --- |
| Today | `timer` pill showing the Pomodoro name, e.g. "SASE V18" |
| Unopened | small accent dot before the title, like Mail's unread dot, and a semibold title |
| Highlights | `highlighter` + count; comments `text.bubble` + count |
| Narration | `waveform` |
| Diagnostics / missing PDF | `exclamationmark.triangle` in amber |

I deliberately avoid the word **NEW**, because bob already uses a NEW chip for unreviewed tasks; the
section is called "Just added" instead.

## 7. Sorting

### 7.1 Empty query: sections in intent order

The question the empty view answers is *"what am I most likely here to open?"* Seven sections, in bob's
own lane order (`TODAY → NEW → PENDING → NEXT → READY`), each row appearing once, in its highest section:

| # | Section | Membership | Order within | Cap |
| --- | --- | --- | --- | --- |
| 1 | **Today** | `^ref` task linked under today's open Pomodoros (`bob plan` `today_tasks[].path`) | ledger order | — |
| 2 | **Just added** | `added` within 72 h, never opened, not finished or dropped | newest first | 5 |
| 3 | **Reading** | `reading_state = started` (`[/]`) | last opened desc, then added desc | — |
| 4 | **Next** | status `next` (`[*]`) | last opened desc, then added desc | — |
| 5 | **Ready** | status `ready` (`[ ]`) | last opened desc, then added desc | — |
| 6 | **Recently opened** | finished or dropped, opened in the last 14 days | last opened desc | 5 |
| 7 | **Library** | everything else | last activity desc: `max(added, finished, last_opened)` | — |

Why this order:

- **Today** is the strongest commitment signal Bob has: Bryan has already decided to read it *now*. It
  usually holds 0–3 rows, so it rarely pushes anything far.
- **Just added** covers the most common daily trigger, "the report I was just notified about". Without
  it, a fresh report would sit at about row 19, behind 7 Reading and 8 Next rows.
- **Lanes before recency.** Things in flight matter more than things opened recently. But *within* a
  lane, last-opened floats to the top, so "the one I had open yesterday" is still near row 1.
- **Library sorts by last activity, not alphabetically.** Nobody browses 300 reports by name.

"Never opened" means no open in the picker's log, and no Spotlight `kMDItemLastUsedDate` later than
`added`.

**Section caps** keep the first screen to about 20 rows; overflow from a capped section falls through to
its natural section. **⌥↓ / ⌥↑** jump between sections.

### 7.2 Typed query: relevance first, priors only break ties

Typing means Bryan knows roughly *what* he wants, so match quality must dominate. Mixing in priors
blindly makes rankings feel random, which is the opposite of reliable. Sections collapse into one ranked
list, and every row keeps its status glyph.

**Normalization.** Fold case, diacritics and width (`FuzzyMatcher` already does this). Strip Markdown
punctuation (`` `%auto` `` → `auto`). Treat `_ - / . :` as word separators so the stem
`auto_autonomy_epic_roadmap` and the title "`%auto` Autonomy: Split Into Verifiable Epics" are both
searchable. The query splits on spaces and **every token must match** (AND semantics, as in fzf).

**Tiers.** A row's tier is the best tier any of its fields reaches. Rows never cross tiers.

| Tier | Rule | Example query → hit |
| --- | --- | --- |
| T0 Learned | Bryan previously picked this row after typing a query that the current query is a prefix of (Alfred-style latching, Raycast's prefix rule); minimum 2 characters, and the row must still match | earlier `agentic`→ASE paper, so `ag` puts it first |
| T1 Exact | normalized title or stem equals the query | `netclode` |
| T2 Word match | every token starts a word anywhere in the title or stem, or the query spells word initials (acronym, scored lower) | `omnigent` → all three Omnigent titles; `ase` → "**A**gentic **S**oftware **E**ngineering" |
| T3 Fuzzy | every token is a subsequence with an fzf-style score above a length-relative floor | `omnimeta` → "Introducing **Omni**gent: A **Meta**-Harness…" |
| T4 Secondary | tokens match only author, area (`parent`), kind words ("paper", "chat"), or cached outline headings | `mollick` → "The Dot and the Swarm" (author Ethan Mollick) |
| "Found in text" | Spotlight full-text hits not already shown, ordered by `NSMetadataQueryResultContentRelevanceAttribute`, then frecency | `omnigent` → 5 more PDFs whose body mentions it |

**A title prefix is a bonus inside T2, not a tier of its own.** A word happening to come first in the
title is a lexical accident, not a commitment. As a separate tier it would let "Omnigent vs SASE…"
(finished) outrank "Databricks Job Fit…, After Omnigent", which is on today's plan. As a bonus, Today can
win while a fuzzy hit still never beats a word hit.

**Within-tier score.** These are named constants, pinned by golden tests.

```text
score = m + P + W + L + 0.25·F + R
  m = fuzzy score normalized to [0,1] for this query length (FuzzyMatcher positions and bonuses)
  P = +0.15 when the match starts the title or stem (prefix)
  W = +0.10 when every token matches a whole word
  L = strongest lane prior: Today +0.20, Reading +0.15, Next +0.12, Ready +0.08, Read 0, Dropped −0.10
  F = log1p(f) / log1p(f_max),  f = Σ_opens 0.5^(age_days / 14)
      (picker opens; Spotlight last-used counts as one open weighted by min(useCount, 4)/4)
  R = 0.10 · 0.5^(days_since_added / 30)
ties: shorter title, newer added, then path (stable)
```

- **The 14-day half-life** matches how fast research reports lose relevance. It sits between Firefox's
  30 days and telescope-frecency's 3 days.
- **Spotlight's last-used and use-count** are a weak cross-surface signal: they also see opens from
  Finder or Obsidian. The picker's own log is the strong one.
- **Dropped rows** are demoted but never hidden; superseded notes are already excluded by bob.

**Worked examples** use the live library. The two claimed orderings that a large open-history
difference could change are marked as assuming similar frecency.

- **`omnigent`.** All three title hits are T2 whole-word matches.
  1. "Databricks Job Fit for a SASE Author, After Omnigent" — Chat, Reading, on today's plan under the
     BLOG Pomodoro. Today's +0.20 beats the next row's prefix +0.15, assuming similar frecency.
  2. "Omnigent vs SASE: What the Meta-Harness Teaches SASE" — Chat, Read, prefix.
  3. "Introducing Omnigent: A Meta-Harness…" — Article, Ready, 8 highlights.
  4. "Found in text" adds 5 PDFs that Spotlight on the Mac finds, including "Recent Reading to Steer
     SASE…" and "Harness Engineering: Anatomy…".
- **`auto`.** Everything is T2.
  1. "`%auto` Autonomy: Split Into Verifiable Epics" — Reading.
  2. "`%auto` Redesign…" — Ready.
  3. "`%auto` UX…" — Read; tied with row 4 on bonuses, newer added date.
  4. "Auto-advancing the `]s` morning review…" — Read.
  5. "Automating the `sase-core-rs`…" — prefix but not a whole word, so no W bonus.
- **`harness`.**
  - First comes "Harness Engineering: Anatomy…" (Paper, Ready, prefix + whole word), then "Harness
    engineering: leveraging Codex…" (Article, Read, prefix + whole word). The different kind tiles make
    the two `harness_engineering` stems instantly distinguishable.
  - Next come "What Does a Harness Buy?" (Paper, Ready, newest) and "Introducing Omnigent: A
    Meta-Harness…" (Article, Ready).
  - The dropped "harness for rsi" sinks below the finished reports despite its prefix bonus, assuming
    similar frecency.

**Scopes.** ⌘1 All, ⌘2 Chats, ⌘3 Papers, ⌘4 Articles, ⌘5 Docs. This follows Spotlight's own ⌘1–4
scope convention on macOS 26/27. Scopes apply in both modes, and the active scope shows as a token in the
filter bar, as the capture picker's scope token does.

### 7.3 Stability rules

These are tested in `RefsCore`:

1. Selection resets to row 1 on each keystroke, and to row 1 of the first section on open.
2. Data that arrives after first paint (`-g` dates, `bob plan`, Spotlight) updates row *content* in
   place. It changes *order* only on the next keystroke or the next open.
3. The panel height is fixed at open, as the capture picker's height budget is. Filtering never resizes
   the window.
4. With identical inputs, the ranking is deterministic, down to the path tie-break.

## 8. The panel: layout, content, interaction

### 8.1 Layout

The panel is 880 × 540 pt and split into a list column and a detail inspector. In the mockup, every
title, status, date, page count, Pomodoro name and full-text hit is real library data from 2026-10-08,
for the query `omnigent`:

```text
+--------------------------------------------------------------------------------------------+
| [All v]  omnigent|                                   3 matches + 5 in text    lib 1m ago   |
+-----------------------------------------------+--------------------------------------------+
| MATCHES                                       |  Databricks Job Fit for a SASE Author,     |
| > [Chat ] Databricks Job Fit for a SASE A…(/) |  After Omnigent                            |
|           Chat · Oct 7 · 11 pp · Today: BLOG  |  Agent report                              |
|   [Chat ] Omnigent vs SASE: What the Meta…(v) |  [Chat] [/ Reading] [Today: BLOG] [obsidian]|
|           Chat · Oct 7 · 20 pp                |                                            |
|   [Artcl] Introducing Omnigent: A Meta-Ha…(o) |  Added   Oct 7         Pages 11 · ~17 min   |
|           Article · Oct 7 · 4 pp · 8 hl       |  Opened  today 08:53 (2x)  Highlights 0     |
| FOUND IN TEXT                                 |  CONTENTS                                  |
|   [Chat ] Recent Reading to Steer SASE: R…(o) |   Bottom line                              |
|   [Chat ] The First SASE Blog Post: A Rec…(/) |   Omnigent and the teams around it         |
|   [Chat ] Developing One Project With Man…(v) |   How a hiring panel will see Bryan        |
|   [Paper] Harness Engineering: Anatomy, A…(o) |   Ranked fit for live postings  ...        |
|   [Chat ] Generic ACP Provider Plugin for…(v) |  why here: on today's plan (BLOG),         |
|                                               |  whole-word match "Omnigent"               |
+-----------------------------------------------+--------------------------------------------+
| ↵ Open in Highlights  ⌘↵ Open note  ⌘Y Quick Look  ⌘K Actions  ⌘1-5 Scope  esc Close        |
+--------------------------------------------------------------------------------------------+
```

`(o)`, `(/)` and `(v)` stand in for the Ready, Reading and Read glyphs. The kind tiles are SF Symbols on
a 15 %-tint rounded square. "Found in text" rows are compact single-line rows, so they read as secondary.

**Rows** are 44 pt with two lines:

- **Line 1:** the title, semibold when unopened, with fuzzy-match characters in semibold accent like the
  capture picker. Trailing glyphs: status, highlight count, narration, Today pill.
- **Line 2:** a secondary caption: `Kind · relative date · pages`.
- **Duplicate titles** (two exist today, for example "Finalizer Integrity and Capabilities") append the
  stem dimmed.

**The detail inspector** adapts to the kind:

| Block | Papers, Articles, Docs | Chats |
| --- | --- | --- |
| Visual | page-1 thumbnail (PDFKit, cached) | **the outline**, because page 1 of a pandoc report is a table of contents that looks the same in every report; browser-printed Chats with no outline get the thumbnail instead |
| Byline | author · published · source host | origin "Agent report" · swarm model (`__cld`, `__gem`, …) or "Consolidated" when the stem says so |
| Chips | kind · status · area (parent, `_ref` stripped) · Today (Pomodoro name) · Unopened | same |
| Facts | added (with source: created / captured / git) · finished · pages + reading time (words ÷ 230 wpm, also shown as "≈ 2 Pomodoros") · opened (last, count) · highlights / comments · narration | same |
| Contents | top-level outline headings (PDFKit `outlineRoot`), up to 6 | same, plus the first paragraph under "Bottom line" when present |
| Your notes | the latest 3 commented highlights with page labels (from `bob ref show -c`); "furthest highlight: p. 29 of 30" as a progress proxy | same |
| Footer | the dim "why here" ranking explanation; the vault path, middle-truncated, monospaced | same |

The outline-as-visual decision for Chats is the most important "beautiful *and* useful" call in this
design. A thumbnail would be pure decoration, while the headings are what actually identifies a report.

**Outline coverage, measured with `mutool`:**

| Kind | PDFs with an outline |
| --- | --- |
| Chat | 266 / 312 |
| Paper | 7 / 8 |
| Article | 5 / 9 |
| Doc | 1 / 11 |

The 45 Chats without one are almost all older reports printed from Chrome. Pandoc reports open with
`Bottom line`, papers with `Abstract` and `1 Introduction`.

When there is no outline, the inspector shows "Opening lines": about 240 characters of page-1 text after
the title, from PDFKit, cached.

### 8.2 Keyboard

The bindings stay consistent with the capture picker wherever both have the action:

| Key | Action |
| --- | --- |
| ↑ ↓ · ⌃N ⌃P · ⌃J ⌃K | move (wraps) |
| PgUp PgDn · ⌘↑ ⌘↓ | page · first/last |
| ⌥↑ ⌥↓ | previous/next section |
| ↵ (or Tab, as in capture) | open in Highlights and hide |
| ⇧↵ | open at the furthest-highlight page (`highlights://` deep link; disabled for non-unique stems) |
| ⌘↵ | open the reference note in Obsidian (`obsidian://open?path=…`, existing `ObsidianOpenURL`) |
| ⌘Y | Quick Look (`QLPreviewPanel`); Space types, so it is not used |
| ⌘K | actions: Reveal in Finder, Copy wikilink `[[ref/…]]`, Copy path, Open source URL, Play narration, Capture follow-up…, Open research report |
| ⌘1–⌘5 | kind scope |
| Esc / ⌃[ | clear the filter, then close |
| click · double-click | select · open |

**VoiceOver.** Each row reads, for example, "Harness Engineering…, Paper, Ready, added yesterday, 30
pages". Result counts are announced through `AccessibilityNotification.Announcement`.

### 8.3 Visual language ("beautiful")

- **Chrome.**
  - Use Liquid Glass (`NSGlassEffectView`, regular style, about 18 pt radius) for the panel shell only.
  - The list and inspector sit on `.regularMaterial` for legibility, the same material the capture
    picker uses, so the two panels read as one family.
  - Reduce Transparency switches to an opaque `windowBackgroundColor`; Increase Contrast raises the
    selection opacity from 0.16 to 0.30, as capture does.
  - Apple notes that glass in a non-key panel renders in the inactive style, so the panel must actually
    become key (it does, via `makeKeyAndOrderFront`).
- **Typography.**
  - Rows use 13.5 pt semibold for unopened titles and regular weight otherwise; captions use 11.5 pt
    secondary.
  - The inspector title is `.title2`.
  - Counts and dates use `.monospacedDigit()` so columns don't jitter.
- **Motion.** The panel fades in and scales from 0.98 to 1.0 over 120 ms ease-out. Selection moves
  instantly, with no animated scrolling under the keyboard. Reduce Motion turns everything into
  cross-fades.
- **Density.** There are no row separators; whitespace and the selection capsule carry the structure.
  The capture picker's 0.5 pt `primary.opacity(0.08)` hairline splits the list from the inspector.
- **Empty, loading and error states.**
  - **No matches:** "No references match 'xyz'", with a hint to try ⌘1 All or full text.
  - **First launch:** a skeleton.
  - **`bob` missing:** the capture app's red callout with Retry and Copy Diagnostic.
  - **Missing PDF** (one case today): an amber row; ↵ opens the note in Obsidian instead, and the toast
    says why.

## 9. Opening in Highlights

- **Primary path.**
  1. Resolve the app with `NSWorkspace.urlForApplication(withBundleIdentifier: "net.highlightsapp.universal")`,
     then call `open([pdfURL], withApplicationAt:, configuration:)` with `activates = true`.
  2. Hide the panel at once. Show an error notification only if the completion handler reports
     failure.
  3. LaunchServices gives sandboxed Highlights access to the file, so no bookmarks are needed.
  4. If Highlights is missing, open in the default app and post a one-time warning.
- **Already-open documents.** Highlights is an NSDocument app, so reopening should focus the existing
  window or tab. This is inferred and needs a Mac spike.
- **Page deep links.**
  - Highlights' own exports use `highlights://<stem>#page=N` (verified in real sidecars). The 2015
    changelog says the app tracks moved files by bookmark.
  - Use these links only for ⇧↵ and for clicking a highlight in the inspector, and only when the stem is
    unique across `lib/`.
  - Spike this before relying on it.
- **⌘O takeover.**
  - Observe `NSWorkspace.didActivateApplicationNotification`. Register a Carbon hotkey for ⌘O (or ⌃O)
    while Highlights is frontmost, and unregister it on deactivate.
  - No Accessibility or Input Monitoring permission is needed. A crash releases the hotkey.
  - Highlights' own Open… stays reachable from the menu. Remapping its key equivalent in System Settings
    → Keyboard → App Shortcuts is not needed.
  - This is opt-in under Settings → References.
  - To verify on the Mac: that a Carbon hotkey beats Highlights' menu key equivalent. This is the
    standard behaviour, but test it.
- **Not doing in v1:**
  - Detecting which PDFs are already open in Highlights. That needs Accessibility (AX) permission.
  - Reading Highlights' Open Recent list. It is TCC-protected, as verified.

## 10. Recommended solution

**Build "References": a second hotkey panel inside Bob Mac Capture**, a thin client over bob's
existing reference index, that opens PDFs in Highlights.

1. **Scope and boundaries.**
   - Add a Foundation-only `RefsCore` library target to the bob-mac-capture package, and a Refs panel
     controller and views in the app target.
   - `RefsCore` decodes `bob ref list`, `bob ref show` and `bob plan` JSON (lenient `decodeIfPresent`,
     strict `schema_version == 1`), and owns the taxonomy, sectioning, ranking, frecency, learned picks
     and the stability rules.
   - Make `BobProcessClient`'s typed decode public and give `HotKeyManager` a second hotkey id.
   - Nothing in the vault changes, and no bob-cli change is required for v1.
2. **Data.**
   - **Snapshot:** `bob ref list -A -R all -f json` on launch, on FSEvents and on stale open.
   - **Dates:** a background `-g` pass, persisted.
   - **Today:** `bob plan -f json` on open.
   - **Spotlight:** a live `NSMetadataQuery` for last-used dates, use counts and full text.
   - **Detail:** lazy `bob ref show` plus PDFKit outline, thumbnail and word count, cached by content
     hash.
   - **Open log and learned picks:** in Application Support, with "Reset ranking history" in Settings.
3. **Sorting.**
   - **Empty:** Today → Just added → Reading → Next → Ready → Recently opened → Library (§7.1).
   - **Typed:** tiers T0–T4 plus "Found in text", with bonuses and priors only inside a tier (§7.2).
   - Rows never move under the cursor (§7.3).
4. **Presentation.**
   - Kind tile + label and the vault status glyph on every row.
   - An inspector that adapts to the kind: outline for Chats, thumbnail for everything else.
   - Today and Pomodoro context, and the "why here" explanation.
   - Glass chrome over material content, and a full keyboard map that matches the capture picker.
5. **Opening.**
   - `NSWorkspace` with the Highlights bundle id.
   - Deep links only for unique stems.
   - Opt-in ⌘O takeover inside Highlights.
   - Opening never changes reading state.
6. **Delivery.** Each phase is independently landable:
   - **P0 Mac spike** (about 1 hour). Verify:
     - reopening a PDF that is already open focuses its existing window;
     - `highlights://<stem>#page=N` for library PDFs;
     - Carbon ⌘O precedence over Highlights' menu;
     - that Spotlight last-used dates update on NSWorkspace opens.
   - **P1 `RefsCore`, test-driven on athena** (Swift 6.0.3 builds `CaptureCore` there). Golden fixtures:
     - a sanitized snapshot of today's 339 rows;
     - the worked examples in §7.2 as ranking tests;
     - stability tests.
   - **P2 panel and inspector UI.** Add fake-`bob` fixtures for `ref list`, `ref show` and `plan`, and
     opt-in design-render PNGs (`BOB_MAC_CAPTURE_RENDER_DIR`) for light, dark and increased contrast.
   - **P3 extras:** ⌘O takeover, deep links, the "Found in text" section, and the ⌘K actions, including
     "Capture follow-up…" into the capture panel.
   - **Optional bob-cli follow-ups:** `source_pdf_sha256` / `pdf_exists` on index rows, a git-date
     cache, and a future explicit `bob ref` status verb if in-picker status actions are wanted.
7. **Record it.** Once accepted, write a decision record extending the thin-client rule to the
   References panel, through `/sase_memory_write`. It should cover: bob owns the reference semantics; the
   app owns ranking and open history; opening never mutates status.

**What would change this recommendation:**

- If the P0 spike shows Highlights cannot be driven reliably by LaunchServices (very unlikely), the
  panel still works as a picker but opens in Preview.
- If Bryan wants the refs picker on machines without the capture app, revisit the shared-kit,
  second-executable layout in §3.

## Sources

- Bob Mac Capture repo (linked, read 2026-10-08):
  - `README.md` l.1-6 (thin-client statement) and l.355-362 (local filtering is presentation-only);
  - `Package.swift`;
  - `Sources/BobMacCapture/{HotKeyManager,CapturePanelController,CapturePickerView,CaptureEditorPalette}.swift`;
  - `Sources/CaptureCore/{BobProcessClient,FuzzyMatcher,ObsidianOpenURL}.swift`.
- bob-cli: `docs/ref.md` (index, reading state, JSON envelope), `docs/highlights-ref-sync.md` (marker,
  sidecar link shapes, scheduled scan), `bob plan --help`.
- Decision record `decisions:mac-capture-is-a-thin-client`; glossary `reference-note`, `reference-task`;
  CLI rules memory.
- Highlights:
  - [App Store lookup](https://itunes.apple.com/lookup?id=1498912833)
  - [App Store page](https://apps.apple.com/us/app/highlights-extract-pdf-notes/id1498912833)
  - [FAQ (not scriptable; tabs)](https://highlightsapp.net/faq/)
  - [Mac changelog (URL scheme, `#page=`, bookmarks)](https://highlightsapp.net/changelog/mac/)
  - [Sidecar files](https://highlightsapp.net/how-to/mac/sidecar-files/)
  - [Features](https://highlightsapp.net/features)
- Launchers:
  - [Alfred File Filter](https://www.alfredapp.com/help/workflows/inputs/file-filter/)
  - [Alfred Script Filter JSON](https://www.alfredapp.com/help/workflows/inputs/script-filter/json/)
  - [Alfred result ordering](https://www.alfredapp.com/help/kb/understanding-result-ordering/)
  - [Raycast List API](https://developers.raycast.com/api-reference/user-interface/list)
  - [Raycast 1.40 ranking](https://www.raycast.com/changelog/macos-v1/1-40-0)
  - [Raycast shortcuts](https://manual.raycast.com/keyboard-shortcuts)
  - [hs.chooser](https://www.hammerspoon.org/docs/hs.chooser.html)
  - [Spotlight (macOS)](https://support.apple.com/guide/mac-help/mh26783/mac)
- Ranking:
  - [Firefox frecency](https://firefox-source-docs.mozilla.org/browser/urlbar/ranking.html)
  - zoxide `src/db/dir.rs`
  - fzf `src/algo/algo.go`
  - fzy `ALGORITHM.md`
  - VS Code `src/vs/base/common/fuzzyScorer.ts` and `anythingQuickAccess.ts`
  - telescope-frecency
  - [ordo-one/FuzzyMatch](https://github.com/ordo-one/FuzzyMatch)
- Apple:
  - [NSPanel `becomesKeyOnlyIfNeeded`](https://developer.apple.com/documentation/appkit/nspanel/becomeskeyonlyifneeded)
  - [NSGlassEffectView](https://developer.apple.com/documentation/appkit/nsglasseffectview)
  - [Adopting Liquid Glass](https://developer.apple.com/documentation/technologyoverviews/adopting-liquid-glass)
  - [glass in non-key panels (forum)](https://developer.apple.com/forums/thread/818901)
  - [PDFPage.thumbnail](https://developer.apple.com/documentation/pdfkit/pdfpage/thumbnail(of:for:))
  - [PDFDocument.outlineRoot](https://developer.apple.com/documentation/pdfkit/pdfdocument/outlineroot)
  - [Reduce Transparency](https://developer.apple.com/documentation/swiftui/environmentvalues/accessibilityreducetransparency)
  - [Accessibility announcements](https://developer.apple.com/documentation/accessibility/accessibilitynotification/announcement/post())
  - [KeyboardShortcuts](https://github.com/sindresorhus/KeyboardShortcuts) (for a future shortcut
    recorder)
