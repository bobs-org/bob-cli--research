# Bob Refs: a quick-open panel that opens Bob's reference PDFs in Highlights

> **Research query:** Finding and selecting reference PDFs in the Highlights app (via its
> `<ctrl+o>` open dialog) is too slow. Should I build `bob-mac-refs`, a Swift app inspired by
> bob-mac-capture, whose keymap opens a type-to-filter picker over the PDFs in `~/bob/lib/`
> that shows each PDF's kind (paper, chat, article…), sorts carefully with and without a filter,
> and describes the selected PDF in rich detail? Critique the plan, say whether you would take a
> different approach, call out any requirement adjustments, and end with a recommended solution
> that is intuitive, reliable and beautiful.

![Infographic "Bob Refs: a quick-open panel for Highlights": a library snapshot of 341 PDF-backed references, 92% chat or agent reports and 27 open references; "One app. A second panel." builds Bob Refs inside Bob Mac Capture, flowing from the Bob reference index through the Bob Refs panel to the original PDF in Highlights; a proposed interface with kind and reading state on every row, an outline and summary for chats and a page preview for papers, articles and docs; browse order Today, Just added, Reading, Next, Ready, Recently opened, Library, with each reference appearing once; search tiers exact, word, fuzzy and secondary metadata, with state and recency ranking only within a tier; fast, stable and honest behaviour; and phases 0 to 4 from a Mac spike to search extras](highlights_quick_open_refs_panel_infographic.png)

## Bottom line

- **Build it. The problem is real and growing.** The library holds **341 PDF-backed reference
  notes**. 138 were added in September and 84 more on October 1–8, almost all agent reports.
  Highlights has no library view, no quick-open and no scripting ("Is Highlights scriptable? No,
  not yet."). Its Open… dialog shows about 310 snake_case filenames in `lib/chat/`, with no title,
  kind, reading state or date. Bob already knows all of those facts. The picker's whole job is to
  bring them to the moment of opening. All five researchers agree on this.
- **Adjustment 1: build it as a second panel inside Bob Mac Capture, not as a new app.** Three
  reports recommend this outright (cdx, cld, grk), and the other two (mus, gem) list it as a
  serious contender or end state. The capture app already has the Carbon hotkey, the prewarmed
  non-activating panel, the picker card, the `FuzzyMatcher`, the `bob` process client, the
  vault watcher, the login item, signing, macOS CI and a fake-`bob` test harness. A separate app
  would mean copying those or extracting them first, and it would add a second menu-bar icon,
  login item, Settings window and install path. The isolation that matters comes from a module
  (a Foundation-only `RefsCore` target), not a separate process. The user-facing name can still
  be **Bob Refs**.
- **Adjustment 2: list reference notes, not files.** The source of truth is
  `bob ref list -R all -A -f json`, filtered to rows with a `source_pdf`. A walk of `lib/` has no
  titles, kinds, states, authors or annotation counts. This also follows the accepted rule that
  Bob Mac Capture is a thin client of `bob`: the app may filter and rank what `bob` returns, but
  `bob` owns vault semantics. No new `bob` command is needed. Two small additive fields would help
  (see [small additive bob-cli changes](#small-additive-bob-cli-changes)).
- **The two sort modes answer different questions** (see [Sorting](#sorting)).
  - **Empty query:** "what am I most likely here to open?" It shows the working set in intent
    order: **Today → Just added → Reading → Next → Ready → Recently opened → Library**. The library
    tail stays reachable, but it sits below the fold.
  - **Typed query:** "find the one I'm thinking of." Sections collapse into one flat list ranked
    by **match tier**. Reading state, frecency and recency can only reorder rows *within* a tier,
    so a weak match never beats a strong one because it is recent or in progress.
- **Kind and reading state are separate axes, and every row shows both.** Kind uses a glyph tile
  and a word: Chat, Paper, Article, Doc. State uses the vault's own checkbox glyphs, which the
  capture palette already defines, including Blocked.
- **The [inspector](#inspector) adapts to the kind.** Page 1 of a pandoc agent report is a table
  of contents that looks the same in every report, so a Chat shows its **outline**. 266 of 312
  chat PDFs have one, and Highlights' in-place saves keep it. Papers, Articles and Docs show a
  **page-1 thumbnail**.
- **Open with [LaunchServices](#opening-in-highlights) and name Highlights explicitly:**
  `NSWorkspace.open([pdf], withApplicationAt: <Highlights>, …)` with bundle id
  `net.highlightsapp.universal` (cld checked this on the Mac's `Info.plist`). Opening never
  changes reading state.
- **Adjustment 3: also fix the pain where it happens.** Besides the global hotkey (⌃⇧⌘R), offer
  an opt-in **[⌘O takeover while Highlights is frontmost](#hotkeys)**. The key Bryan already
  presses inside Highlights would then open the good picker. The request says `<ctrl+o>`;
  Highlights' stock Open… key is ⌘O, so bind whichever key Bryan actually presses.

The full recommendation is in [Recommended solution](#recommended-solution), and the requirement
changes are tabulated in [Requirement adjustments](#requirement-adjustments).

## Critique of the plan

**Is this a good idea? Yes.** The diagnosis is precise: loading is fine, finding is slow. A
general-purpose open dialog organizes files, but Bryan retrieves references by meaning: titles,
kinds, what he is reading now, what arrived today. The value of a custom panel does not come from
moving a filename list into Swift. It comes from combining **Bob's metadata, predictable ranking,
and an always-ready keyboard surface**. Nothing else on the Mac knows a PDF's reading state, kind,
plan membership or annotations, so nothing else can rank these PDFs well. The gap widens by about
ten reports a day.

### Alternatives

| Option | What it buys | Why it is not the answer |
| --- | --- | --- |
| Highlights ⌘O / Open Recent | Nothing to build | It is the problem itself |
| Spotlight / Finder search | Free; finds embedded PDF titles | Opens the *default* app, mixes in everything, and knows no reading state or kind |
| Alfred Script Filter over `bob ref list` | About a day of work, global hotkey | Probably needs the Powerpack (0 workflows installed); no detail pane; a fine stopgap only |
| Raycast extension | Good `List` + detail view | Not installed; opaque ranking; a third-party dependency. A valid *second* client of the same JSON later |
| Hammerspoon `hs.chooser` | Already installed | A step backwards: capture just replaced a Hammerspoon pop-up |
| `bob ref list \| fzf \| open -a Highlights` (mus's interim) | Hours of work | Terminal-bound, with no hotkey from inside Highlights and no detail. Useful only as a ranking sandbox, and the athena ranking CLI in the [delivery plan](#delivery-plan) does that better |
| Obsidian quick switcher or plugin | Bryan lives in Obsidian | Opens the *note*, not the PDF. ⌘↵ in the picker covers this |
| Highlights Siri AI | Vendor-supported | Needs macOS 27; no Bob state; not deterministic |
| **Separate `bob-mac-refs` app** (as proposed) | Clean identity, independent releases | Duplicates the hotkey, panel, process client, install, CI, login item and menu bar, or forces a large extraction first |
| **Refs panel inside Bob Mac Capture** | Reuses everything; one icon and one Settings window; enables cross-panel actions | Hotkey routing and panel arbitration must be added cleanly (see [Hotkeys](#hotkeys)) |

### Would I take a different approach?

Same idea, with four changes:

1. **Different packaging:** one process with a second panel, as above.
2. **A different unit:** the reference note, which supplies identity and metadata, with the PDF
   as the thing opened.
3. **A different default view:** the working set first, and the archive one keystroke away.
4. **A second entry point:** ⌘O inside Highlights.

The design budget belongs to sort order, metadata density and reliability, not to platform code.

## Requirement adjustments

| # | Original | Adjusted | Why |
| --- | --- | --- | --- |
| R1 | A new `bob-mac-refs` Swift app | A **Refs panel inside Bob Mac Capture**, with its own hotkey, controller and Foundation-only `RefsCore` target | See [Critique of the plan](#critique-of-the-plan). Extract a shared kit into a second executable only if Bryan later needs Refs without Capture |
| R2 | "The PDFs in `~/bob/lib/`" | **PDF-backed reference notes** from `bob ref list`. A `lib/` PDF without a note shows in a dim "Unindexed" footer (0 today), and a note whose PDF is missing shows a warning instead of opening | Title, kind, state, dates and annotations live in the index; the thin-client rule |
| R3 | "Show whether it is a paper, a chat, an article…" | **Two axes on every row:** kind and reading state, plus a Today marker and an unopened marker | Kind alone cannot answer "what should I open next?" |
| R4 | Kind as a badge | Kind is also a **scope** (⌘1 All, ⌘2 Chats, ⌘3 Papers, ⌘4 Articles, ⌘5 Docs), shown as a removable token in the filter bar. **Bare kind words are never hard filters** | 92% of PDFs are chats, so scoping matters. But "blog" appears in today's two in-progress blog-post chats; grk's bare-word filter would hide exactly them |
| R5 | One keymap, near `<ctrl+o>` | **Global ⌃⇧⌘R** (configurable), **plus an opt-in ⌘O/⌃O takeover while Highlights is frontmost** | A global ⌃O or ⌘O would steal Open… from every app. ⌃⇧⌘R is free in Bryan's managed configuration |
| R6 | "As much data as possible" | **Progressive disclosure:** dense two-line rows and a rich, lazy, kind-adaptive inspector. Nothing may delay the panel or Return | The inspector is where the beauty budget belongs |
| R7 | Type to filter | Filter on **title, stem, author, arXiv/DOI, parent, and kind words** (low weight). Spotlight **full-text** results come later, in a separate "Found in text" section | Agents' snake_case stems are memorable; full text catches "which report mentioned X?" |
| R8 | (implicit) | **Opening never changes reading state**, task lanes, review state or the vault | The task-lane decision records keep lanes user-owned. An open is a retrieval, not a status gesture |
| R9 | (unstated) | **Rows never move under the cursor.** Late data updates row contents in place, and re-sorts happen only on the next keystroke or the next open | The most important reliability property of a "hotkey, ↵" picker |
| R10 | (unstated) | **No `xlib/` intake section in v1** | On the Mac `xlib/` is gitignored and normally empty: a 15-minute cron moves files to `lib/`. Revisit if that changes |

## Facts the design rests on

The "Who" column names the researcher who established each fact. **lead** marks facts that are
new in this consolidation or that the lead re-verified on athena on 2026-10-08. The Mac was
offline during consolidation, so Mac-only facts rely on cld's read-only SSH session from earlier
the same day.

| Fact | Who |
| --- | --- |
| 341 PDF-backed notes, 340 PDFs on disk, **0 orphan PDFs**, 1 note whose PDF is missing (`lib/chat/AGENTS.pdf`) | cld, grk; lead re-ran |
| By `ref_type`: chat 313, docs 11, blogs 9, papers 8. By origin: agent-report 313, external 28 | cld, grk; lead |
| Reading state: finished 295, dropped 19, queued 20, started 7. Open lanes: 7 Reading (`wip`), 8 Next (one is Blocked `[?]`), 12 Ready | lead |
| `bob ref list -R all -A -f json`: about 50–215 ms and 742 KB on athena; **127 ms on the Mac** | cld, grk; lead |
| Without `-g`, `added` is present on only **59 of 341** rows. With `-g` (git backfill) it is present on all of them, at 1.4 s on athena and 1.3 s on the Mac | cld; lead |
| **Git-backfilled `finished` dates are polluted:** 218 of 341 rows say finished `2026-10-03`, a bulk event; `finished_source` is `git` for 212 rows. Backfilled `added` dates are spread plausibly across months | **lead (new)** |
| File mtimes are useless as "added" dates: 203 chat PDFs share one mtime | cld |
| `bob plan -f json` → `today_tasks[].path` includes 3 `ref/chat/*.md` notes today, all under the `BLOG` Pomodoro | cld; lead |
| Blocked `[?]` reference tasks shipped today (`3d70446`). `bob ref list` reports such a row as `status: next`, and the `[?]` appears only inside the string `reading_state_source: "ref_task:[?]"` | **lead (new)** |
| Highlights bundle id is `net.highlightsapp.universal` (v2026.1.2). It is an NSDocument app and registers the `highlights` URL scheme. *gem's `com.sophia.Highlights` and mus's `com.highlightsapp.Highlights` are unverified guesses and wrong* | cld (`plutil` on the Mac) |
| The Highlights changelog documents `highlights://Users/test.pdf#page=3`, an absolute path without its leading slash (v1.2, 2015; "improved handling", 2023.2). Bob's sidecars use the stem form `highlights://<stem>#page=N`, and stem `harness_engineering.pdf` exists in both `blogs/` and `papers/` | grk, cld; lead (changelog) |
| Highlights "Siri AI" (2026.2, 2026-09-13) needs **macOS 27** and is demoed on iPadOS. The library's Highlights-saved PDFs carry the producer "macOS Version 26.5", so Siri search is not a near-term substitute | cdx raised it; **lead (new)** |
| Highlights' Open Recent list and its container preferences are TCC-protected and unreadable | cld |
| Spotlight indexes `~/bob/lib`. `kMDItemTitle`, page count, `kMDItemLastUsedDate` and `kMDItemUseCount` are populated, and `mdfind` finds full-text hits | cld |
| Outline coverage: Chat 266/312, Paper 7/8, Article 5/9, Doc 1/11. 45 of the 46 outline-less chats were printed from Chrome. **Highlights re-saves PDFs in place (111 chats show a Quartz producer) and keeps the outline** | cld; lead (Quartz check) |
| 222 of 312 chat PDFs have a "Bottom line"-style summary heading in their first three pages | **lead (new)** |
| Kind words appear inside titles: "blog" in 8 titles, including both of today's in-progress "First SASE Blog Post" chats; "article" in 3, "paper" in 2, "chat" in 2 | **lead (new)** |
| Capture's `HotKeyManager` uses a fixed `EventHotKeyID(id: 1)`, and its handler never reads the pressed key's id, so a second instance cannot tell two hotkeys apart | cdx; lead verified |
| The capture picker **wraps** ↑/↓, and **Tab accepts** like Return (`CapturePickerNavigation`, README) | **lead (new)** |
| The capture README calls local filtering "a deliberate presentation-only responsibility", so Swift-side ranking is precedented | cld; lead |
| The capture palette already maps `.blocked → pause.circle`, alongside `/ * ␣ x -` | lead |
| Capture already presents reading-queue `ref` items with an `in_library` verdict and an `openTargetPath` (`bf43ab2`, 2026-10-07) | **lead (new)** |
| Swift 6.0.3 is installed on athena, and `CaptureCore` builds there | cld; lead |
| Bryan's managed Hammerspoon binds only ⌃⌥⌘V and ⌃⌥⇧S. Capture owns ⌃⇧⌘I and ⌃⇧⌘O. Alfred 5 is installed with 0 workflows; Raycast is not installed | lead (chezmoi); cld (Mac) |

## Where the reports disagreed and how it is resolved

| Topic | Positions | Resolution |
| --- | --- | --- |
| Packaging | In capture (cdx, cld, grk); new app plus a shared package (mus); a unified "bob-mac" suite (gem) | **In capture.** Everyone agrees on one shared core. The process boundary buys nothing for two small panels. Revisit only if Refs must run without Capture |
| Data source | `bob ref list` (cld, grk, mus); a new `bob ref catalog` joining a PDF inventory (cdx); a new `bob ref picker` (gem) | **`bob ref list` for v1**, since there are 0 orphan PDFs today. Add two additive fields (see [small additive bob-cli changes](#small-additive-bob-cli-changes)). Build cdx's catalog only if orphans appear in practice |
| Empty-query scope | Queue only, hiding the 295 finished (grk); all PDFs, alphabetical tail (cdx); lifecycle tiers (gem, mus, cld) | **Working set first, library tail visible below the fold, ordered by recency**, not alphabetically and not by git-sourced `finished` dates (polluted; see [the facts](#facts-the-design-rests-on)) |
| Typed ranking | Additive score where state can beat match quality (gem); strict match tiers (cdx, cld); fuzzy score then tie-breaks (grk, mus) | **Tiers, with bounded priors only inside a tier.** gem's own example lets a "started" fuzzy hit outscore a stronger match; that is exactly the "feels random" failure |
| State as a prior | None (cdx); small within-tier prior (cld, grk, mus) | **A small within-tier prior.** A dropped item never needs to tie a Today item |
| Type filter syntax | Bare words (grk); `#papers` (mus); `@paper` (gem); ⌘-digit scopes (cld, gem, mus); chips only (cdx) | **⌘1–⌘5 scopes plus a visible token.** No bare-word hard filters ([R4](#requirement-adjustments) evidence). No operator language in v1 |
| Full-text search | Spotlight "Found in text" section (cld); defer (others) | **Phase 3**, as a separate secondary section that is never interleaved |
| Space key | Quick Look (gem); types a space (cld) | **Space types**, because queries are multi-token. Quick Look is **⌘Y** |
| ⌘↵ | Open the note (cdx, cld, grk, gem); reveal in Finder (mus) | **⌘↵ opens the note in Obsidian; ⌥↵ reveals in Finder** |
| ↑/↓ at the ends | Clamp (cdx); wrap (cld, grk) | **Wrap**, like the capture picker. PgUp/PgDn clamp, also like capture |
| Tab | Accept (cld); move into the inspector (grk); focus traversal (cdx) | **Tab accepts**, as in every capture picker |
| When to hide | Immediately (cld); after the open succeeds (cdx, grk) | **Hide immediately when the open is dispatched.** If the completion reports an error, show the panel again with the query and an error callout. Capture's "hide after success" rule exists to protect an unsent draft; nothing is lost here |
| Highlights missing | Fall back to the default app (gem, cld); show an error (cdx) | **Show an error with an explicit "Open in default app" action.** Never fall back silently |
| Visual for each row | Thumbnail for everything (cdx, grk, gem); outline for chats (cld) | **Adaptive by kind**, verified in [the facts](#facts-the-design-rests-on) |
| Reading-time estimate | Show it (cld); no source of truth, so omit it (cdx) | **Show it, labelled as an estimate** ("≈ 17 min · 1 Pomodoro") from the PDF's word count. The words are a real source; the label keeps it honest |
| Learned query→pick latching | Its own top tier (cld) | **Defer to phase 4**, once an open log exists. When it lands, it may only promote within T1 or better |
| Interim fzf slice | Ship first (mus) | **Skip it.** Tune ranking with a `RefsCore` CLI on athena against live JSON (see the [delivery plan](#delivery-plan)) |
| Bundle id | `net.highlightsapp.universal` (cld, verified); two unverified guesses (gem, mus) | `net.highlightsapp.universal` |
| What "chat" means | AI dialogue transcripts (gem, mus) | They are **agent research reports** (`origin: agent-report`, pandoc-rendered). Label them "Chat", Bryan's word and the folder name, with "Agent report" as the byline |

## Sorting

### Empty query

**Sections in intent order.** Each row appears once, in its highest section. "Opened" means
opened from the picker's own log; Spotlight's `kMDItemLastUsedDate` is a weak secondary signal for
opens made elsewhere.

| # | Section | Membership | Order within | Cap | Today's size |
| --- | --- | --- | --- | --- | --- |
| 1 | **Today** | `^ref` task linked under today's open Pomodoros (`bob plan` `today_tasks[].path`) | Ledger order | — | 3 |
| 2 | **Just added** | Queued (Ready or Next), `added` within 72 h, never opened | Newest first | 5 | 5 (about 12 eligible) |
| 3 | **Reading** | `wip` `[/]` | Last opened, then `added`, newest first | — | 4 left after Today |
| 4 | **Next** | `next` `[*]`; Blocked `[?]` rows last, with the pause glyph | Last opened, then `added` | — | ≤8 |
| 5 | **Ready** | `ready` `[ ]` | `added`, newest first | — | remainder of 12 |
| 6 | **Recently opened** | Finished or dropped, opened within 14 days | Last opened, newest first | 5 | 0 on day one |
| 7 | **Library** | Everything else | Last activity, newest first: `max(added, last_opened, finished*)` | — | ~295 |

`*` Use `finished` only when `finished_source` is not `git`; those dates are polluted (see
[the facts](#facts-the-design-rests-on)).

Why this order:

- **Today is the strongest commitment signal Bob has**, and it rarely holds more than three rows.
- **Just added covers the most common trigger:** "the report I was just notified about."
  Without it, a fresh report sits at about row 19, behind roughly 15 Reading and Next rows,
  well below the ~10 visible rows.
- **Lanes come before recency, but recency orders rows within each lane**, so "the one I had open
  yesterday" is still near the top.
- **The library stays visible.** grk would hide finished items, and cdx would list everything
  alphabetically. The resolution keeps the first screen to the working set and lets the archive
  scroll below it. Nobody browses 295 reports by name.
- The section caps keep the first screen to about 20 rows. Overflow from a capped section falls
  through to its natural section. ⌥↑ and ⌥↓ jump between sections.
- On first use, empty sections are omitted. Never show an empty header.

### Typed query

**Relevance first; priors only break ties.**

**Normalization.**

- Fold case, diacritics and width (`FuzzyMatcher` already does this).
- Strip Markdown punctuation, so `` `%auto` `` becomes `auto`.
- Treat `_ - / . :` as word separators, which makes stems and titles equally searchable.
- Split the query on spaces. **Every token must match somewhere** (AND semantics, as in fzf).

**Tiers.** A row's tier is the best tier its fields reach, and rows never cross tiers.

| Tier | Rule | Example |
| --- | --- | --- |
| T0 Exact | Normalized title or stem equals the query; or an arXiv id, DOI or URL equals it | `2610.04433` → "What Does a Harness Buy?" |
| T1 Word | Every token starts a word in the title or stem. Acronyms of word initials are scored lower within this tier | `omnigent` → all three Omnigent titles; `ase` → "**A**gentic **S**oftware **E**ngineering" |
| T2 Fuzzy | Every token is a subsequence with an fzf-style score above a length-relative floor. Only for tokens of 3+ characters | `omnimeta` → "Introducing **Omni**gent: A **Meta**-Harness…" |
| T3 Secondary | Tokens match only author, parent area, kind words, or cached outline headings | `liu` → the harness paper (author) |
| "Found in text" (phase 3) | Spotlight full-text hits not already shown, in a separate compact section | `omnigent` → reports whose body mentions it |

Short-query policy (cdx): one character matches prefixes only, two characters allow literal
matches, and fuzzy matching starts at three.

**Within-tier score** (cld's formula, adapted). These are named constants pinned by golden tests:

```text
score = m + P + W + L + 0.25·F + R
  m  match quality from FuzzyMatcher, normalized to [0,1] for the query length
  P  +0.15 if the match starts the title or stem
  W  +0.10 if every token matches a whole word
  L  lane prior: Today +0.20, Reading +0.15, Next +0.12, Ready +0.08, Read 0, Dropped −0.10
  F  picker frecency: log1p(f)/log1p(f_max), f = Σ_opens 0.5^(age_days/14)
  R  0.10 · 0.5^(days_since_added/30)
ties: shorter title, newer added, then path (deterministic)
```

**A title prefix is a bonus, not a tier.** A word happening to come first in the title is an
accident of wording, not a commitment. With prefix as a bonus, today's in-progress "Databricks
Job Fit…, After Omnigent" can beat the finished "Omnigent vs SASE…" on `omnigent`, while a fuzzy
hit can still never beat a word hit.

**Worked checks for the golden tests** (live library, 2026-10-08):

- `omnigent`: three T1 hits. "Databricks Job Fit…" (Chat, Reading, Today) leads.
- `blog post`: four T1 hits. Both of today's in-progress Today chats come first, then the
  finished "blog00 launch post review consolidated", then the dropped "Directed Zettelkasten…".
  This is the [R4](#requirement-adjustments) case that a bare-word `blog` filter would break.
- `harness`: eleven hits. The two `harness_engineering` stems are told apart by their kind tiles
  (Paper, Ready vs Article, Read). The dropped "harness for rsi" sinks despite its title-prefix
  bonus.
- A pasted arXiv id or DOI selects its exact reference first.
- Whitespace-only input falls back to browse ordering.

### Stability rules

These rules are tested in `RefsCore`.

1. Each query edit selects the first row of the new ranking. Opening the panel selects the first
   row of the first section. Once the user navigates, the selected **id** stays put until the
   next edit.
2. Data that arrives after the first paint (`-g` dates, `bob plan`, Spotlight, inspector
   hydration) changes row **content** in place. It changes **order** only on the next keystroke
   or the next open.
3. Panel height is fixed when the panel opens, and filtering never resizes it.
4. Identical inputs always produce the identical order, down to the path tie-break.
5. If the selected item disappears during a refresh, mark it unavailable. **Never open whatever
   row slid into its index.**

## The panel

### Layout

The panel is about **880 × 560 pt**, bounded by the screen's visible frame. Roughly 52% is the
list and 48% the inspector. Width is user-resizable and remembered; height is fixed while the
panel is open. The data below is real library data from 2026-10-08, shown with an empty query and
the Paper selected:

```text
╭───────────────────────────────────────────────────────────────────────────────────────╮
│ ⌕  Search references…                         [All ⌘1]       27 open · 341 · 2m ago    │
├──────────────────────────────────────────┬────────────────────────────────────────────┤
│ TODAY                                    │  ╭──────────╮  Paper  ○ Ready  arXiv        │
│ [💬] Databricks Job Fit for a SASE A… ◐  │  │ page-1   │                             │
│      Chat · Oct 7 · 11 pp · ⏱ BLOG  ♫   │  │ thumb-   │  What Does a Harness Buy?   │
│ [💬] The First SASE Blog Post: A Re… ◐  │  │ nail     │  Tokens, Mostly              │
│      Chat · Oct 7 · ⏱ BLOG              │  ╰──────────╯  Yangze Liu, Zhongyi Han      │
│ [💬] The First Paragraphs of the Fi… ◐  │                Published Oct 3 · arxiv.org  │
│      Chat · Oct 7 · ⏱ BLOG              │                                             │
│ JUST ADDED                               │                                             │
│▸[🎓] What Does a Harness Buy? Toke… ○  ●│  Added today · 22 pp · ≈ 70 min (3 Poms)    │
│      Paper · today · 22 pp  ♫           │  Never opened · 0 highlights · ♫ narration  │
│ [💬] `just install` (PyPI), `just …  ○  ●│  CONTENTS                                   │
│      Chat · today                       │   Introduction · Related Work · Setup ·     │
│ READING                                  │   Results · …                               │
│ [💬] `%auto` Autonomy: Split Into V… ◐  │  why here: added today, unopened            │
│      Chat · today · 9 pp                │  lib/papers/what_does_a_harness_buy_tok…pdf │
├──────────────────────────────────────────┴────────────────────────────────────────────┤
│ ↵ Open in Highlights   ⌘↵ Note   ⌥↵ Reveal   ⌘Y Quick Look   ⌘K Actions   esc Close    │
╰───────────────────────────────────────────────────────────────────────────────────────╯
```

The bracketed glyphs stand in for SF Symbol tiles. `◐ ○` stand in for the Reading and Ready
glyphs, `●` is the unopened dot, and `⏱ BLOG` is the Today pill showing the Pomodoro name.
Titles, kinds, states, dates, page counts (22 and 11), authors, narration marks and the paper's
outline are real. The reading-time estimate and the `%auto` page count are illustrative.

### Rows

- **Height:** 44 pt, two lines. This is denser than cdx's 58–68 pt and gem's 64 pt, and roomier
  than capture's single-line 34 pt. About ten rows fit under the section headers.
- **Line 1:** the kind tile, then the title. The title is semibold when the reference has never
  been opened, and matched characters use semibold accent like the capture picker. Trailing marks
  show reading state, the highlight count when it is above zero, `♫` narration, and the Today pill.
- **Line 2:** a secondary caption: `Kind · relative date · pages`, plus the author for papers and
  articles.
- **Duplicate titles:** two exist today ("Finalizer Integrity and Capabilities" and "Conditional
  launch admission with `%if`"). Each gets its stem appended, dimmed.
- **No thumbnails in the list.** A consistent kind glyph is easier to recognize at row size, and
  rendering 340 PDFs on every hotkey press would cost reliability. The largest PDF is 19.6 MB.

### Visual tokens

**Kind.** A glyph tile plus a label, never colour alone. The tints avoid the status hues.

| `ref_type` | Label | SF Symbol | Tint |
| --- | --- | --- | --- |
| `chat` | Chat (byline "Agent report") | `bubble.left.and.bubble.right` | purple |
| `papers` | Paper | `graduationcap` | teal |
| `blogs` | Article | `newspaper` | pink |
| `docs` | Doc | `book.closed` | brown |
| `books`, `slides`, other | Book, Slides, title-cased raw value | `books.vertical`, `rectangle.on.rectangle`, `doc` | secondary |

An unknown `ref_type` falls back to a generic tile instead of failing to decode.

**Reading state.** Reuse `CaptureEditorPalette.taskStatus` exactly, so both panels speak one
language: Reading `circle.lefthalf.filled` orange, Next `circle.inset.filled` blue, Ready
`circle`, Blocked `pause.circle`, Read `checkmark.circle` green, Dropped `xmark.circle`, unknown
or conflicting `circle.dashed`. Avoid the word **NEW**: Bob's review walk already uses a NEW chip
for unreviewed tasks, so the section is called "Just added".

### Inspector

The inspector is filled instantly from the list snapshot, then upgraded lazily. Lazy loading
waits until the selection has settled for about 80–150 ms, cancels when the selection moves, and
caches results.

| Block | Papers, Articles, Docs | Chats |
| --- | --- | --- |
| Visual | Page-1 thumbnail (PDFKit, off the main thread, cached by path + size + mtime) | **Outline** (PDFKit `outlineRoot`, top level, up to 6). Without one, the thumbnail |
| Header | Kind · state · Today pill · area (`parent` without `_ref`) | Same |
| Byline | Author · published · source host · arXiv/DOI links | "Agent report" · area. Add the swarm model or "Consolidated" only when the stem ends in `__<model>` (11 of 340 today) |
| Facts | Added (with its source: created, captured or git) · finished (only if sourced from the task) · pages · ≈ reading time · last opened and open count · highlights and comments with the snapshot age · narration | Same |
| Contents | Top-level outline headings, up to 6, when present (7 of 8 papers) | Already shown as the visual |
| Summary | Abstract excerpt when the PDF text has one | The first paragraph under "Bottom line" (222 of 312) |
| Your notes | The latest 3 commented highlights with page labels (`bob ref show -c`) and "furthest highlight p. N of M", clearly labelled | Same |
| Footer | The dim "why here" line, and the vault path (middle-truncated, monospaced) | Same |

Honesty rules (cdx):

- Absence stays absence.
- A publication date is not a file mtime.
- A scan snapshot is not reading progress.
- A highlight count is not a percent read.
- Mark git-backfilled dates as "≈" in the facts block.

### Keyboard

The bindings match the capture picker wherever both panels have the same action.

| Key | Action |
| --- | --- |
| Typing, paste, ⌘A/C/V/X/Z, ⌃A/E, ←/→ | Native filter-field editing. Text typed before the panel paints seeds the filter |
| ↑/↓, ⌃P/⌃N, ⌃K/⌃J | Move (wraps) |
| PgUp/PgDn, ⌘↑/⌘↓ | Page (clamped), first/last |
| ⌥↑/⌥↓ | Previous/next section |
| ↵ or Tab, double-click | Open in Highlights and hide |
| ⌘↵ | Open the reference note in Obsidian (existing `ObsidianOpenURL`) |
| ⌥↵ | Reveal the PDF in Finder |
| ⇧↵ (phase 4) | Open at the furthest-highlight page (`highlights://` deep link, after the spike) |
| ⌘Y | Quick Look |
| ⌘K | Actions: Copy `[[ref/…]]`, Copy path, Open source URL, Play narration, Capture follow-up…, Refresh |
| ⌘1–⌘5 | Kind scope |
| Esc / ⌃[ | Close the Actions menu if open, else clear a non-empty query, else close the panel |
| Global hotkey again | Close the panel |

During IME composition, Return belongs to the text system. A new invocation starts with a blank
query and the "All" scope; scopes never carry over invisibly.

### Visual language

- **Chrome:** Liquid Glass (`NSGlassEffectView`) only on the panel shell. The list and inspector
  sit on `.regularMaterial`, the material the capture picker uses, so the two panels read as one
  family. Glass on every row would hurt legibility. The panel must become key so glass renders in
  its active style.
- **Typography:** rows use 13.5 pt titles and 11.5 pt secondary captions. The inspector title uses
  `.title2`. Counts and dates use `.monospacedDigit()` so they don't jitter while typing.
- **Structure:** no row separators. Whitespace and the selection capsule carry the structure, and
  a 0.5 pt hairline splits the list from the inspector, as in capture.
- **Motion:** the panel fades in and scales from 0.98 to 1.0 over 120 ms. Selection moves
  instantly, with no animated scrolling under the keyboard. Reduce Motion turns everything into
  cross-fades.
- **Accessibility:** Reduce Transparency makes the panel opaque, and Increase Contrast raises the
  selection fill, as in capture. VoiceOver reads each row as "Title, Paper, Ready, added today,
  22 pages" and announces result counts after a pause, not on every keystroke. The thumbnail is
  `accessibilityHidden`.
- **Verification:** render-test light, dark and increased-contrast variants with capture's
  `BOB_MAC_CAPTURE_RENDER_DIR` PNG fixtures.

### States

| Situation | Behaviour |
| --- | --- |
| First launch, no cache | Skeleton rows; the panel stays interactive |
| Refresh failed | Keep the last good snapshot. The footer "lib 2m ago" turns amber, with Retry and Copy Diagnostic (capture's pattern) |
| No matches | "No references match 'xyz' in Papers", plus a one-key route back to All. Open is disabled |
| Note whose PDF is missing (1 today) | Amber row. ↵ is replaced by "Open note"; the inspector names the path |
| PDF without a note (0 today) | "Unindexed" footer section, using a humanized stem or the embedded PDF title, marked as such |
| Highlights not found | The panel stays open with "Locate Highlights…" and "Open in default app" |
| PDF fails to preview (encrypted, corrupt, slow) | Placeholder with the reason. Opening is unaffected |
| `bob` unresolved | Capture's red callout. The panel still opens on the last good data |
| Capture panel is open | Only one Bob panel is visible at a time. Capture's draft is preserved, and Refs work runs on separate process lanes, so a refresh can never cancel a capture submit |

## Architecture

### Ownership

| Concern | Owner |
| --- | --- |
| Which references exist; kind, state, lanes, dates, annotations, plan membership | **bob** (`ref list`, `ref show`, `plan`). Swift never parses frontmatter or `reading_state_source` |
| Filtering, ranking, sectioning, frecency, stability | **app** (`RefsCore`), the same presentation-only precedent as the capture pickers |
| PDF intrinsics: pages, outline, thumbnail, word count | **app** (PDFKit), cached. This is not vault semantics |
| Open log and learned picks | **app**, stored in Application Support per machine, never in the vault. Settings has "Reset history" |
| Opening the PDF | **app** (`NSWorkspace`) |

Once accepted, record this with `/sase_memory_write` as a decision that **extends the thin-client
rule to the Refs panel**: bob owns reference semantics, the app owns ranking and open history, and
opening never mutates anything.

### Data flow

```text
launch · FSEvents(ref/, lib/) debounced 0.5 s · panel open when the snapshot is > 60 s old
  → bob ref list -R all -A -f json        (~130 ms on the Mac)  → snapshot, in memory and on disk
  → bob ref list -R all -A -g -f json     (~1.3 s, background)  → merge added dates, persist
panel open
  → bob plan -f json                      (background; last value cached) → Today set
  → NSMetadataQuery(lib/**.pdf)           (live) → lastUsedDate, useCount
selection settles (~80–150 ms; previous request cancelled)
  → bob ref show <path> -f json -c        (~130 ms) → commented highlights, tasks (LRU cache)
  → PDFKit on a background queue          → outline, words, page-1 thumbnail (disk cache)
typing
  → RefsCore.rank(snapshot, query, scope, signals)   (well under 1 ms for 341 rows; no process)
```

- No process runs between the hotkey and the first paint. The panel is prewarmed, as in capture.
- A refreshed snapshot is swapped in atomically, only after a complete decode. A malformed
  response never erases the last good list.
- `schema_version` must be 1. Unknown fields are ignored, and new fields are read with
  `decodeIfPresent`.
- FSEvents only invalidate the snapshot. Wake from sleep and a manual Refresh also revalidate.

### Opening in Highlights

1. Resolve Highlights once at launch with
   `NSWorkspace.urlForApplication(withBundleIdentifier: "net.highlightsapp.universal")`. Settings
   can override it with a chosen `.app`.
2. On ↵, capture the selected **id** and its resolved file URL (`~/bob` + `source_pdf`), and
   check that the file exists.
3. Call `open([url], withApplicationAt:, configuration:)` with `activates = true`, then hide the
   panel. Never build a shell command from a title or path.
4. If the completion handler reports an error, show the panel again with the query and an error
   callout (see the "When to hide" row under
   [Where the reports disagreed](#where-the-reports-disagreed-and-how-it-is-resolved)).
5. On success, append to the open log. Do not record selections or previews as opens.
6. Never open a temporary copy. Highlights' annotations must land on the library original that
   Bob's scan reads.

Opening a PDF that is already open should focus its existing window, since Highlights is an
NSDocument app. That is inferred and goes into the phase-0 spike. Window-versus-tab behaviour
follows the macOS "Prefer tabs" setting, per the Highlights FAQ.

**Page deep links (phase 4).** Use the documented absolute-path form,
`highlights://<absolute path without leading slash>#page=N`. Unlike Bob's stem links, it is
unambiguous for duplicate stems such as `harness_engineering.pdf`. Spike whether it opens
untracked PDFs, and whether sending it after a file open creates a second window.

### Hotkeys

- **Prerequisite:** replace the single-purpose `HotKeyManager` with one registry. It assigns a
  distinct `EventHotKeyID` to each action, reads the id from the event in its single handler, and
  routes to Capture or Refs. Test that routing. Two instances of today's manager cannot tell the
  keys apart (see [the facts](#facts-the-design-rests-on)).
- **Global Refs hotkey:** ⌃⇧⌘R, configurable in Settings, with a conflict diagnostic shown if
  registration fails.
- **⌘O takeover (opt-in; Settings → References):** observe
  `NSWorkspace.didActivateApplicationNotification`. While Highlights is frontmost, register ⌘O
  (or ⌃O if that is the key Bryan uses), and unregister it when Highlights deactivates.
  - No Accessibility or Input Monitoring permission is needed, and a crash releases the key.
  - Highlights' own File › Open… stays reachable from its menu.
  - The panel is non-activating, so Highlights stays frontmost while it is shown; pressing the
    key again toggles the panel.
  - Verify in phase 0 that a Carbon hotkey takes precedence over Highlights' menu key equivalent.
    That is the standard behaviour, but test it.

### Small additive bob-cli changes

None of these block a prototype. Each is additive under the JSON contract rules, and each follows
the CLI rules memory for help text and flags.

1. **Expose Blocked explicitly**, for example as a `task_status` field (`blocked`, `next`, …) on
   list rows. The app must not parse `"ref_task:[?]"` out of `reading_state_source`.
2. **Mark git-backfilled finish dates.** `finished_source: "git"` already exists, so this may be
   documentation only. If possible, also cache the git backfill so `-g` costs about as much as a
   plain list.
3. **Optional:** a `pdf_exists` field, and a `--pdf` filter that skips the roughly 600 notes
   without a PDF and shrinks the 742 KB payload.

### Targets

These are proposed acceptance targets, not measurements:

- Warm hotkey to a focused, populated panel in under 50 ms (p95 under 100 ms).
- A query edit re-ranked in under 16 ms at 341 rows, and under 50 ms at 10,000.
- Return dispatches without waiting for any thumbnail, `bob` call or network request.
- A cached cold launch is usable immediately.

## Delivery plan

Each phase can land on its own.

| Phase | Scope | Gate |
| --- | --- | --- |
| **P0: Mac spike (about 1 hour)** | Verify on the Mac: NSWorkspace opens in Highlights, both cold and already running; an already-open PDF focuses its window; Carbon ⌘O beats Highlights' menu key; ⌃⇧⌘R is free system-wide; Spotlight last-used updates after NSWorkspace opens; the absolute-path `highlights://…#page=N` form works. Ask Bryan which key he presses for Open… (⌃O or ⌘O) | Findings recorded |
| **P1: `RefsCore`, test-driven on athena** | Foundation-only target: decoding, taxonomy, sections, tiers, frecency, stability rules. Add a tiny **`refs-rank` debug CLI** (`swift run refs-rank "<query>" < snapshot.json`) so ranking can be tuned on athena against live `bob ref list` output. Golden fixtures come from a sanitized snapshot and the [typed-query](#typed-query) worked checks. Land the bob-cli field for Blocked ([additive change](#small-additive-bob-cli-changes) #1) | Linux `swift test` |
| **P2: the useful panel** | Hotkey registry, the Refs panel and rows, empty and typed modes, scopes, open, error states, cache and refresh, the open log, the opt-in ⌘O takeover. Fake-`bob` fixtures for `ref list` and `plan`, plus render PNGs. **This already solves the stated problem** | macOS CI; Bryan uses it for a week |
| **P3: the inspector** | Thumbnail or outline by kind, Bottom-line excerpt, `ref show -c` highlights, reading time, "why here", Quick Look, ⌘K actions | macOS CI and render fixtures |
| **P4: only if missed retrievals justify it** | Spotlight "Found in text", learned picks, ⇧↵ page links, cross-panel actions (e.g. "Open in Highlights" on capture's "Already in your library" card, and "Capture follow-up…"), a `bob ref list --pdf` filter | Real failed-query examples |

**Validation before polish.** Time three real tasks from hotkey to open: reopen yesterday's
reference, find one by a partly remembered title or author, and retrieve an old finished one.
Compare each against Highlights' Open… dialog.

## Risks and open questions

| Risk or unknown | Mitigation |
| --- | --- |
| Is Bryan's Open… key ⌃O or ⌘O? | Ask in P0. The takeover binds whichever he actually uses |
| The ⌘O takeover loses to Highlights' menu or misbehaves around activation changes | P0 spike. It is opt-in, and the global hotkey still works |
| Highlights' already-open and deep-link behaviour | P0 spike. Primary opening never depends on the URL scheme |
| Default-view section caps and windows (72 h, 14 d, 5) are guesses | Named constants. Tune them with `refs-rank` and a week of use |
| `-g` costs 1.3 s on the Mac | Run it in a background lane and persist the dates. Optionally cache it in bob-cli (see [small additive bob-cli changes](#small-additive-bob-cli-changes)) |
| The library grows to thousands of rows | Ranking in memory is still well under 50 ms. Revisit SQLite or FTS only for measured full-text needs |
| Two panels fight over focus | Only one Bob panel is visible at a time; separate lanes; capture's draft is preserved |
| Mac CI is the only gate for AppKit code | `RefsCore` carries all logic and is tested on Linux, as `CaptureCore` is today |

## Recommended solution

**Build "Refs": a second hotkey panel inside Bob Mac Capture. It is a thin client of Bob's
reference index, and it opens the original PDF in Highlights.**

1. **Package.**
   - Add a Foundation-only `RefsCore` target and a Refs panel controller and views to the
     bob-mac-capture package.
   - Replace `HotKeyManager` with a registry that routes by event id.
   - Keep one menu-bar icon and one Settings window. The user-facing name is **Bob Refs**.
2. **Data.**
   - `bob ref list -R all -A -f json` is the snapshot, filtered to rows with a `source_pdf`.
   - A background `-g` pass supplies `added` dates. Never use git-sourced `finished` dates for
     ordering.
   - `bob plan -f json` supplies the Today set.
   - Inspector detail is fetched lazily with `bob ref show -c` and PDFKit.
   - The open log lives in Application Support.
   - The app never writes to the vault.
   - The bob-cli side adds one field so the app can show Blocked.
3. **[Sorting](#sorting).**
   - **Empty query:** Today → Just added → Reading → Next → Ready → Recently opened → Library,
     each row once, with the library tail ordered by recency.
   - **Typed query:** one flat list in match tiers T0–T3. Lane, frecency and recency priors are
     bounded inside a tier.
   - ⌘1–⌘5 kind scopes. No bare-word filters.
   - Rows never move under the cursor.
4. **[Presentation](#the-panel).**
   - Two-line 44 pt rows, each with a kind tile and label plus the vault's status glyph.
   - An inspector that adapts to the kind: the outline and Bottom line for Chats, a page-1
     thumbnail for everything else.
   - Today and Pomodoro context, honest facts, and a "why here" line.
   - Glass chrome over material content, matching the capture picker's family resemblance and
     keymap: wrapping ↑/↓, Tab accepts, Esc clears then closes.
5. **[Opening](#opening-in-highlights).**
   - `NSWorkspace` with `net.highlightsapp.universal`. Hide on dispatch, and show the panel again
     on error.
   - A global ⌃⇧⌘R hotkey, plus an opt-in ⌘O (or ⌃O) takeover while Highlights is frontmost.
   - Opening never changes reading state.
6. **[Order of work](#delivery-plan).**
   - **P0:** the Mac spike.
   - **P1:** `RefsCore` and a `refs-rank` tuning CLI on athena.
   - **P2:** the panel. This alone fixes the problem.
   - **P3:** the rich inspector.
   - **P4:** full text and deep links, only once real missed retrievals call for them.

**What would change this recommendation:**

- If Bryan wants Refs on a machine without Capture, extract a shared kit and build a second
  executable *in the same repository*. A new repository is the most expensive option.
- If orphan PDFs start appearing, adopt cdx's catalog command, which joins the PDF inventory with
  the notes inside `bob`.
- If the P0 spike shows that Highlights can't be driven reliably through LaunchServices, which is
  very unlikely, the picker still works and opens through the default app with a visible warning.

## About this report

- **Date:** 2026-10-08
- **Type:** consolidated research. The lead merged five independent reports (`__cdx`, `__cld`,
  `__grk`, `__mus`, `__gem`, all in this directory) and added its own verification.
- **Question:** Highlights is a good reader, but finding a PDF through its Open… dialog is slow.
  Bryan proposed `bob-mac-refs`, a Swift app modelled on Bob Mac Capture. A global hotkey would
  open a type-to-filter picker over the PDFs in `~/bob/lib/`. Each row would show its kind
  (paper, chat, article…), default and filtered sorting would each be considered carefully, and
  the selected PDF would get rich detail. Is that a good plan, what should change, and what
  should be built?

## Sources

- **Researcher reports in this directory:**
  - `highlights_quick_open_refs_panel__cdx.md`: the catalog contract, honesty rules, the
    hotkey-registry defect, and the short-query policy;
  - `__cld.md`: Mac verification, live-library metrics, sections, the tiered score, the outline
    insight, and the ⌘O takeover;
  - `__grk.md`: the queue-first default, inspector field inventory, and risks;
  - `__mus.md`: data plumbing, the scopes affordance, and the interim-slice argument;
  - `__gem.md`: multi-action dispatch, the taxonomy, and failure modes.
- **bob-cli** (`b0f2960`):
  - `docs/ref.md` and `docs/highlights-ref-sync.md`;
  - `src/native/ref_library/{row,list}.rs`;
  - commit `3d70446` (Blocked `[?]` references);
  - live `bob ref list -R all -A [-g] -f json` and `bob plan -f json` on athena, 2026-10-08.
- **bob-mac-capture** (`838e043`):
  - `Package.swift`;
  - `Sources/BobMacCapture/{HotKeyManager,CaptureEditorPalette}.swift`;
  - `Sources/CaptureCore/{CapturePickerPresentation,CaptureRefPresentation}.swift`;
  - README §§ hotkeys, pickers, local filtering;
  - commit `bf43ab2`.
- **chezmoi:** `home/dot_hammerspoon/init.lua` (hotkey inventory).
- **Memory:** decision `decisions:mac-capture-is-a-thin-client`; `tailnet.md` (the Mac was
  offline during consolidation).
- **Library measurements** on athena: `pdfinfo`, `pdftotext`, and `mutool show … outline`
  across `~/bob/lib/**.pdf`.
- **Highlights:**
  - [FAQ](https://highlightsapp.net/faq/) (not scriptable; tabs; window restore);
  - [Mac changelog](https://highlightsapp.net/changelog/mac/) (v1.2 URL scheme, 2023.2 link
    handling, 2026.2 Siri AI and macOS 27);
  - [Siri AI announcement](https://highlightsapp.net/blog/2026/09/14/Siri-AI/).
- **Apple:**
  - [`NSWorkspace.open(_:withApplicationAt:configuration:completionHandler:)`](https://developer.apple.com/documentation/appkit/nsworkspace/open(_:withapplicationat:configuration:completionhandler:));
  - [`PDFPage.thumbnail(of:for:)`](https://developer.apple.com/documentation/pdfkit/pdfpage/thumbnail(of:for:));
  - [`PDFDocument.outlineRoot`](https://developer.apple.com/documentation/pdfkit/pdfdocument/outlineroot);
  - [`NSGlassEffectView`](https://developer.apple.com/documentation/appkit/nsglasseffectview);
  - [Materials HIG](https://developer.apple.com/design/human-interface-guidelines/materials);
  - [FSEvents guide](https://developer.apple.com/library/archive/documentation/Darwin/Conceptual/FSEvents_ProgGuide/UsingtheFSEventsFramework/UsingtheFSEventsFramework.html).
- **Ranking precedents** (via cld): fzf `algo.go`, fzy `ALGORITHM.md`, the VS Code
  `fuzzyScorer`, [Firefox frecency](https://firefox-source-docs.mozilla.org/browser/urlbar/ranking.html),
  zoxide, telescope-frecency, and [Alfred result ordering](https://www.alfredapp.com/help/kb/understanding-result-ordering/).
