# Fast PDF opening for the Highlights app: picker design research (`bob-mac-refs`)

Researcher: mus (independent report in a 5-researcher swarm).
Question: Bryan reads everything in the Highlights app but hates its built-in
`<ctrl+o>` library lookup. Proposal: a new `bob-mac-refs` Swift menu-bar app,
inspired by `bob-mac-capture`, with a bindable global keymap that pops a
type-to-filter picker over the PDFs in `~/bob/lib/` (his reference system),
with a clear paper/chat/article/... badge per row, keyboard navigation,
thoughtful default-vs-filtered sorting, rich per-row + selected-row detail,
and an intuitive, reliable, beautiful design.
This report critiques the plan, adjusts requirements where justified, and ends
with a recommended solution.

## TL;DR

- Yes, the problem is real and worth solving, but **do not build a second
  full app from scratch**. Build `bob-mac-refs` as a thin second target that
  reuses `bob-mac-capture`'s proven picker infrastructure
  (`FuzzyMatcher`, picker state/view, `HotKeyManager`, `BobProcessClient`),
  ideally by extracting a shared Swift package or by adding a second panel
  mode to the existing app.
- The data source must be **`bob ref list --format json` (the reference
  library index), not a raw `~/bob/lib/**/*.pdf` filesystem scan**. The
  filesystem has no titles, authors, reading state, or annotation counts;
  the index has all of them. Filesystem scan is only a fallback/orphan
  detector.
- Opening the PDF is the easy part: `NSWorkspace.open(_:)` /
  `open -a Highlights <path>` bypasses Highlights' terrible `<ctrl+o>`
  entirely. There is no need to script Highlights' library window.
- Sorting: **default = recognition-optimized (reading queue first,
  most-recent first, grouped by type)**; **filtered = fuzzy-score first,
  recency as tiebreak, no grouping**. Details below.
- Ship in two slices: (0) a one-day `bob ref list | fzf | open -a Highlights`
  interim that validates the sorting/metadata choices, then (1) the Swift
  panel. Do not ship a new global-hotkey daemon before proving the sort
  order on real data.

## 1. What I actually inspected (evidence, not assumption)

All paths below are from the live checkout/vault on 2026-10-08.

### 1.1 The library is typed directories, not a flat PDF folder

`~/bob/lib/` contains four subdirectories, not one PDF pile:

| dir | entries observed | contents |
|---|---|---|
| `blogs` | 16 | article PDFs + `.md` sidecars + 2 `.mp3` |
| `chat` | 436 dir entries (`.md`+`.pdf` pairs, so ~200+ PDFs) | agent-report PDFs, the dominant class |
| `docs` | 23 | docs PDFs + sidecars |
| `papers` | 16 | paper PDFs + sidecars + 2 `.mp3` |

Total: **338 PDFs** under `~/bob/lib` (`find ~/bob/lib -name '*.pdf' | wc -l`).
The newest PDFs are hours old (`sase_md_instruction_delivery.pdf`,
`sase_listen_plugin_commands.pdf`, both 2026-10-08), so any "default sort"
that is not recency-aware will feel stale on day one.

Requirement adjustment #1: the request says "PDFs in `~/bob/lib/`" but the
meaningful unit is **`lib/<type>/<stem>.pdf` where `<type>` is the
`ref_type`**. The picker's badge should read that directory name through the
index (`papers` -> PAPER, `chat` -> CHAT, `blogs` -> ARTICLE, `docs` -> DOC),
not guess from filenames. `chat` is agent transcripts, not "chats" in a
social sense; label it accordingly (suggest `CHAT` with tooltip
"agent report / transcript").

### 1.2 The index already has every metadata field the panel wants

`bob ref list -R all -A -f json` returns 941 indexed notes on this vault
(168 `started`, 212 `queued`, 520 `finished`, 39 `dropped`, 2 `unknown`;
2 superseded hidden). Each `RefRow` carries exactly what a rich picker
needs:

- identity: `title`, `ref_type`, `path`, `link`, `source_pdf`
  (e.g. `lib/papers/ea_graph.pdf`), `author`, `published`, `captured`,
  `added` / `added_source`, `finished` / `finished_source`
- reading signal: `reading_state` (`started|queued|finished|dropped`),
  `status`, `parent`, `origin` (`external` vs `agent-report`)
- Highlights signal: `annotation_count`, `comment_count`, `snapshot.synced_at`
- extras: `audio` (e.g. `lib/chat/....mp3`), `urls`, `identity.arxiv/doi`
- provenance: `added_source`, `finished_source`, `reading_state_source`

Example row (trimmed): `ref/chat/...` has `title`, `ref_type: chat`,
`reading_state: started`, `source_pdf: lib/chat/....pdf`,
`audio: lib/chat/....mp3`, `annotation_count`, `added: 2026-10-08`.
A raw filesystem scan gives none of this. Any design that lists PDFs by
walking `~/bob/lib` will have to re-derive titles from stems
(`humanize_stem`) and will mislabel dates — the exact work `bob ref`
already does.

Requirement adjustment #2: **scope the picker to "PDF-backed refs"**
(`source_pdf != null`, suffix `.pdf`, file exists), not "every file in
`~/bob/lib/`". That automatically excludes `.mp3`-only rows, legacy
URL-only rows with no PDF, and TextBundle sidecars, while including the
380-note reading queue plus finished papers worth re-opening. Provide an
"orphans" section (PDF on disk, no ref note) as a diagnostic, not as the
main list.

### 1.3 `bob-mac-capture` already solved 80% of this panel

From `sase/repos/linked/bob-mac-capture` (opened via `sase repo open
bob-mac-capture`):

- `Sources/CaptureCore/FuzzyMatcher.swift`: pure subsequence fuzzy matcher
  with affine gap penalties and boundary bonuses (`matchPoints 16`,
  `startBoundaryBonus 10`, `separatorBoundaryBonus 8`,
  `transitionBoundaryBonus 6`, `consecutiveBonus 8`). Multi-token queries,
  diacritic/case folding, match-highlight ranges. **Reuse as-is.**
- `Sources/BobMacCapture/CapturePickerState.swift`,
  `CapturePickerView.swift`, `CapturePanelController.swift`,
  `CapturePanelWindowSizer.swift`: snapshot + `filterText` + `selectedRowID`
  + fixed `visibleRowBudget` (filtering never resizes the panel), stale-draft
  refusal, Escape two-stage cancel, reopen chip, selection-preservation on
  filter change. **Copy the state machine, not just the visuals.**
- `Sources/BobMacCapture/HotKeyManager.swift`: Carbon
  `RegisterEventHotKey`, production `Ctrl-Shift-Cmd-I`, development
  `Ctrl-Shift-Cmd-O`. Proves the global-keymap mechanism and the dev/prod
  split the new app needs (it must not steal capture's hotkey).
- `Sources/CaptureCore/BobProcessClient.swift`: every `bob` call is a short
  local subprocess with a generous 20 s timeout, cancellation by generation,
  JSON `--format json` + `expectedSchema`. This is the thin-client pattern
  the accepted decision `mac-capture-is-a-thin-client` mandates: **the Swift
  app never parses grammar, never computes previews, never writes the
  vault**; `bob-cli` owns data.
- `Sources/CaptureCore/ObsidianOpenURL.swift`: precedent for "bob returns a
  filesystem path, the app builds the open URL itself"
  (`obsidian://open?path=<abs>`). Same shape works for Highlights: bob
  returns `source_pdf`, the app opens it.

### 1.4 How Highlights opening actually works

- Highlights links inside sidecars look like
  `highlights://agentic_software_engineering#page=1`; the scan/sync docs
  (`docs/highlights-ref-sync.md`) confirm the app round-trips a page-1
  marker and a sidecar `.md` per PDF.
- Nothing in `bob ref` drives the Highlights GUI today; the workflow is
  file-based (`xlib/` intake -> `lib/` library -> `ref/` note). Highlights
  itself watches files. So "open this PDF in Highlights" is an OS-level
  file open, **not** a Highlights-library search. That is precisely why a
  launcher fixes the complaint: it replaces "find it in Highlights'
  `<ctrl+o>`" with "tell the OS to open this exact path in Highlights".
- On macOS this is `NSWorkspace.shared.open([url])` or equivalently
  `open -a Highlights <path>`. If Highlights is already running, the file
  opens in place; if not, it launches. No URL scheme, AppleScript
  dictionary, or library-database poking is required. (Verify on the Mac at
  build time; keep a fallback to default-`open` when Highlights is absent.)

## 2. Critique: is a new Swift app the right call?

### 2.1 The diagnosis is correct

The complaint is precisely scoped: load speed is fine, *finding* is slow.
That is a launcher problem, and launchers beat in-app library browsers
whenever the corpus is large (here 338 PDFs and growing ~5–10/day in `chat`)
and the app's own search is weak. A global keymap + fuzzy picker is the
standard fix (Spotlight, Raycast, fzf, Obsidian quick-switcher) and fits
Bryan's keyboard-first workflow.

### 2.2 But a from-scratch second app is the most expensive correct answer

Costs of `bob-mac-refs`-as-brand-new-app:

- A second menu-bar app means a second hotkey registration, second login
  item, second signing/bundling pipeline (`Scripts/bundle.sh`,
  `install.sh`), second settings window, and duplicate picker/filter/fuzzy
  code to keep in sync.
- The corpus is small enough (338 PDFs, 941 index rows, JSON ~740 KB) that
  no new indexing infrastructure is needed; the app is a view over
  `bob ref list` output. The risk is not performance but drift: two apps
  embedding two copies of `FuzzyMatcher` + picker behavior.

Alternatives considered:

| alternative | verdict |
|---|---|
| `bob ref list -f json \| fzf \| open -a Highlights` shell function | Ship as day-0 interim. Validates sort/metadata; stays as headless fallback. Not the end state (no badges, no detail pane, no global keymap). |
| Raycast / Alfred / Hammerspoon script over `bob ref list` | Cheapest GUI. Loses the beautiful detail pane and match highlighting; hostage to a third-party launcher Bryan may not want. Good stopgap, not the product. |
| Obsidian quick-switcher / plugin | Wrong host: the goal is to open Highlights, not Obsidian. Obsidian already finds notes fine. |
| Extend `bob-mac-capture` with a second panel/mode | **Serious contender.** One menu-bar app, two hotkeys, two panels sharing `FuzzyMatcher`, window sizing, and `BobProcessClient`. Cheapest to maintain; slightly muddies "capture" branding. |
| New `bob-mac-refs` app sharing a Swift package with capture | **Recommended end state.** Clean branding ("Refs" in menu bar), shared `RefsPickerCore` package so behavior never diverges. Accept the extra bundle cost once the interim proves the design. |

Requirement adjustment #3: **do not authorize a fully independent
implementation**. Charter `bob-mac-refs` as a thin client over `bob-cli`
JSON (per `mac-capture-is-a-thin-client`) that reuses capture's picker core
by extraction, not by copy-paste. If extraction proves awkward, fall back to
"second panel in the existing app" rather than duplicating the matcher.

### 2.3 The one requirement I would strengthen

"Make it clear whether each PDF selection is a paper, a chat, an article,
etc." is currently a badge. Make it a **first-class filter axis**: typing
`#papers`, `#chat`, `#blogs`, `#docs` (or `type:papers`) narrows to that
lane, and `Cmd-1..4` toggles lanes. With `chat` at ~60%+ of the corpus,
lane-scoping is the difference between "fuzzy over 338" and "fuzzy over
the 30 papers I actually mean". This mirrors how capture's pickers use
sigils (`^`, `:`, `+`) and `FuzzyQuery`'s leading-sigil stripping — reuse
that exact affordance.

## 3. Design

### 3.1 Interaction shape (small, fixed, fast)

- Global bindable hotkey (default: free, suggest `Ctrl-Shift-Cmd-R` for
  Refs; never `I`/`O` which capture owns). Hotkey shows a floating panel,
  centered-ish near the menu bar, focused filter field, list below, detail
  footer/side. `Esc` closes (two-stage: clear filter first, then dismiss,
  matching capture). `Enter` opens the selected PDF in Highlights;
  `Cmd-Enter` reveals in Finder; `Opt-Enter` copies the `source_pdf` path /
  `[[link]]`.
- Filter-as-you-type over a preloaded index (no per-keystroke subprocess).
  Full keyboard nav: `Up/Down` or `Ctrl-p/n`, `j/k` when the field is empty,
  `PgUp/PgDn`, type-ahead highlight with matched-substring emphasis from
  `FuzzyMatcher` positions. Selection is sticky: when the filter changes,
  keep the selected row if still visible, else select the top row.
- Panel never resizes while filtering (fixed `visibleRowBudget`, e.g. 9
  rows; capture uses the same rule). Footer shows `N of M`, lane counts,
  and the active sort explanation ("sorted by recent · started first") so
  the order never feels arbitrary.

### 3.2 What each row shows (density without noise)

Row (single line + subline):

- Lane badge: `PAPER` / `CHAT` / `ARTICLE` / `DOC` (color + 1-letter
  shortcut hint). Color-blind-safe: badge shape/label, not color alone.
- Title (truncated middle, match highlights bolded).
- Right-aligned compact signals: reading-state dot (`●` started,
  `○` queued, `✓` finished — with text label on the detail pane, never
  color-only), `⦿ n` annotation count when > 0, `♪` when audio exists,
  relative date (`2h`, `3d`).
- Subline (dimmed): `author · year` when known, else `stem.pdf`; never
  empty — fall back to filename so every row is identifiable.

Selected-row detail pane (the "especially" requirement): full title,
author, published/captured/added dates with sources, `ref_type` lane +
`status`/`reading_state`/`parent`/`origin`, `source_pdf` vault-relative
path, audio presence, `annotation_count` + `comment_count` +
`snapshot.synced_at`, arXiv/DOI/URL chips when present, and the first
line of the ref note or latest annotation quote when cheap to fetch
(`bob ref show <id> -f json` lazily on selection change, debounced;
never block the list on it).

### 3.3 Sorting: default vs filtered (the hard question)

Principles: default view optimizes **recognition** ("what was I just
reading / what is due next"); filtered view optimizes **recall**
("the thing matching these letters"). Never mix the two rankings, and
always label which mode is active.

Default (empty filter) — recency-weighted reading queue:

1. Partition: `started` first, then `queued`, then `finished-recently`
   (finished in last 30 d, dimmed), then everything else. `dropped` never
   in default; accessible via filter or a "show all" toggle. Rationale:
   the panel's job on open is "resume", not "archive search". This mirrors
   `bob ref list`'s own default (queue = started+queued).
2. Within partition: `added`/`captured` descending (most recent first),
   using `row_date` semantics (`finished` date for finished rows, else
   `added`). Rationale: the corpus grows daily in `chat`; recency is the
   best proxy for "you probably mean this".
3. Group headers by lane (`PAPERS`, `CHAT`, …) only in default view, each
   group internally recency-ordered, groups ordered by newest member.
   Rationale: groups aid scanning when unfiltered; they hurt when
   filtered (they scatter top matches).
4. Cap: show top ~100 with "and N more — type to narrow". Full 941-row
   scroll is a trap; the default is a *working set*.

Filtered (non-empty query) — score first, recency breaks ties:

1. `FuzzyMatcher` score over weighted fields: title ×3, author ×2,
   stem/filename ×1.5, arXiv/DOI/URL ×1. Multi-token queries AND across
   tokens (every token must match somewhere, as capture does).
2. Tiebreak: `started` > `queued` > `finished`, then recency descending.
   Never boost `finished`-old above a fresh `queued` on equal score —
   freshness is intent.
3. No lane grouping; one flat ranked list with the lane badge still
   visible. Lane tokens (`#papers`, `type:chat`) act as hard filters
   before scoring.
4. Empty-result state must say why ("no PDF-backed refs match 'xyz' in
   #papers — try all lanes") with one keystroke to clear the lane.

Why not pure recency / pure alpha / pure frequency: pure alpha scatters
related work; pure frequency rewards old finished items the user will
never re-open; pure recency buries the paper from last month they clearly
mean. The hybrid above matches how Obsidian quick-switcher, fzf, and
capture's own pickers behave, and it degrades gracefully (a one-character
filter already beats the default for recall).

### 3.4 Data plumbing (thin client, reliable)

- Primary: `bob ref list -R all -A -f json` at panel open (or at login +
  refresh on hotkey if < 60 s stale), parsed once into rows, filtered in
  memory with the shared `FuzzyMatcher`. 941 rows / ~740 KB JSON parses in
  milliseconds; no new `bob` endpoint is needed for v1.
- Consider a future `bob ref pick --format json --pdf-only --fields
  minimal` only if profiling shows `ref list` is too slow or too wide
  (it won't be at this scale — but the option keeps the app thin: any new
  ranking field still ships in `bob-cli`, never in Swift).
- Freshness without fragility: `FSEvent`/mmap watch on `~/bob/lib` +
  `~/bob/ref` triggers a background re-index (debounced 2 s); a failed
  re-index keeps the last good snapshot with a "stale · retrying" footer
  chip. Missing file at open time → inline row error ("PDF moved — reveal
  note?") instead of a silent no-op.
- Open path: resolve `source_pdf` (vault-relative) to absolute via
  `BOB_DIR` (default `~/bob`), verify existence, then
  `NSWorkspace.shared.open([pdfURL], withAppBundleIdentifier:
  com.highlightsapp.Highlights)` with fallback to default `open`. Log the
  open (optional `bob ref` "touched" hook — explicitly out of v1 to avoid
  write-path scope creep).
- No writes in v1: no status changes, no annotation edits, no `#now`-style
  mutations. The panel is a launcher; capture owns mutation.

### 3.5 Beauty (last but not least, per the brief)

- Native SwiftUI, respects light/dark + accent color, Dynamic Type.
  Monospaced numerals for counts/dates so rows don't jitter while typing.
- Match highlighting in accent color, lane badges as subtle pills
  (PAPER indigo, CHAT teal, ARTICLE amber, DOC gray — plus labels).
- Generous-enough row height (title 13 semibold + subline 11 dimmed),
  8 pt corner radius, panel shadow, 60 fps filter (filter on background
  actor, publish top-N; the corpus is small but typing must never drop a
  frame).
- Accessibility: full VoiceOver labels ("Paper, Agentic Software
  Engineering, started, 2 annotations"), visible focus ring, reduced-motion
  respected.

## 4. Requirement adjustments (explicit list)

1. Badge source = `ref_type` via the index, not filename sniffing; label
   `chat` as agent transcripts in help text.
2. Corpus = PDF-backed refs (`source_pdf` exists), not every file in
   `~/bob/lib/`; on-disk orphans get a diagnostic section, not main-list
   status.
3. Type is a filter axis (`#papers` / `Cmd-1..4`), not just a badge.
4. No new Swift-side ranking/indexing logic; any new signal ships as a
   `bob ref list` field first (thin-client rule).
5. v1 is read-only (open/reveal/copy only); no reading-state writes.
6. Hotkey defaults avoid capture's `Ctrl-Shift-Cmd-I/O`; propose
   `Ctrl-Shift-Cmd-R`, user-rebindable in Settings with conflict warning.
7. Interim deliverable: shell `ref-fzf-highlights` function first, to
   validate sort + metadata before the Swift build.

## 5. Recommended solution

**Phase 0 (days, in `bob-cli`):** add `ref-fzf-highlights` (or `bob ref
open --fzf` if it earns a subcommand): `bob ref list -R all -A -f json` →
`jq` to `badge | title | author | date | path` lines → `fzf --ansi` with
default queue-first/recency order pre-sorted and live fuzzy on top →
`open -a Highlights`. Success criterion: Bryan opens 10 PDFs without
touching Highlights' `<ctrl+o>`, and the default-vs-filtered order feels
right. Tune the partition weights here, where iteration is seconds.

**Phase 1 (the app):** `bob-mac-refs` menu-bar app, new target + shared
`PickerCore` package extracted from `bob-mac-capture` (`FuzzyMatcher`,
picker state machine, window sizer, process client, hotkey manager).
Panel as §3.1–§3.5. Data = `bob ref list` JSON; open via
`NSWorkspace`→Highlights. Read-only v1. Settings: hotkey recorder,
default lane, default scope (queue vs all), "show finished" toggle,
vault path override.

**Explicitly not in v1:** annotation display/editing, reading-state
mutation, Highlights library sync/repair, non-PDF targets, Spotlight
importer, iOS companion.

Risks to verify on the Mac: Highlights bundle id + `open -a` behavior when
the app is closed; Carbon hotkey vs Shortcuts conflicts; notarization for
a second login item; `chat` PDFs with identical titles (stem disambiguation
in subline). None is architectural — all are one-afternoon probes.

Bottom line: the plan is a good idea aimed at the right layer (a launcher,
not a Highlights clone), but its value is entirely in sort order +
metadata density + keymap reliability. Prove those with the fzf slice,
then build the smallest beautiful thin client that reuses capture's picker
core instead of reinventing it.
