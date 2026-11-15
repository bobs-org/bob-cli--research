# `//` in Bob Mac Capture: go to any note

*Researcher cld · 2026-11-15 · bob-cli @ `476c5440`, bob-mac-capture @ `9bf9050`,
bob-plugins @ `b34074a` · vault measurements are read-only scans of `~/bob` on apollo*

## 1. Bottom line

**Build it.** The idea is sound, and most of the machinery already exists. Three
parts need more care than the request suggests:

1. **"All note files" is the wrong set.** Bob's existing note walk sees **5,728**
   Markdown files. About **1,900** are legacy zorg companions and archives, and
   **205** more are machinery or duplicates. If they are all listed, a short query such
   as `cash` matches **151 reference notes** and only 14 real notes. The fix is
   three tiers, all owned by bob:
   - **Live:** listed. About 3,600 notes.
   - **Archive:** behind ⌘X, the same key that shows completed tasks in `/`. 1,935
     notes.
   - **Hidden:** never listed. Machinery, Highlights sidecars, and attachments.
2. **The second `/` should be a bob grammar token, typed through a mechanism that
   already exists.** bob already uses `action_continuation_keys` so that `!` → `!!`
   and a lone `+` hand a keystroke from an open picker back to the draft. bob would
   advertise `/` as the continuation key of a bare `/` Go To. The app then types it
   into the draft, and bob reads `//query` as a new `note_goto` need. The app makes no
   grammar decision, and fast typing (`//foo` before any picker appears) lands in the
   same place.
3. **"Beautiful" depends on three things:**
   - the `/` → `//` transition must not blink;
   - an empty `//` must show a useful map, not a 3,600-row scroll;
   - rows must say what each note *is*.

   The recommendation therefore includes a picker hand-off that keeps the card on
   screen, a warm in-memory snapshot, and kind glyphs tinted with Bob's area hue.

**Recommended shape:**

- **bob-cli** adds `note_goto`: claim, parse, refusal, completion, a note-catalog
  module with the tier rules, and a `task_goto` picker descriptor carrying
  `action_continuation_keys: ["/"]`.
- **bob-plugins** adds a read-only `obsidian://bob-goto-note` handler next to
  `bob-goto-task`.
- **bob-mac-capture** adds a `.noteGoto` picker source with a fast hand-off.

**Effort:** about 3.5–4.5 days across three repos. Every step is additive and safe
when versions are mismatched (§9.5).

## 2. What exists today (verified)

| Fact | Evidence |
| --- | --- |
| `/` Go To is a whole-draft bob token. It claims only a token holding **no second `/`**. `//`, `/Users/x`, and `/r/rust` are prose by design (prior requirement R7). | `task_goto_query_token` in `src/native/capture_language/tokens.rs`; test `goto_claim_leaves_prose_byte_identical` (`tests/goto.rs:99`); table in `docs/capture.md` "Going to a task with '/'". |
| Today `//`, `//sase`, and `//ref/chat` parse as `mode: task`, `needs: []`. **No `#task` line in the vault starts with `//`.** | Live `bob capture-parse` probes; vault grep returned 0. |
| The hash alias already leaves `//` alone: "A `/` at a line start, glued to a word, or right after another `/` stays literal." | `docs/capture.md` §directive/section aliases. |
| bob already has a picker-to-draft keystroke handoff. A bare `!` answers `action_continuation_keys: ["!", "["]`; a lone `+` and `- ^` send keys plus aliases. On an empty filter, the app closes the picker, types the key into the draft at the caret, and re-analyses. | `engine.rs:1629`; `CapturePanelModel.continuePickerOperator` (`:9881`); router `continuePickerOperator` cases (`CaptureKeyCommandRouter.swift:1320`, `:1370`). Today only Parent Task, Complete, and Move sources accept continuation keys. |
| `task_goto` responses carry **no `picker` descriptor** today. The app decodes `picker.kind` as a free string with `decodeIfPresent` everywhere, so adding a descriptor cannot break an older app. | `docs/capture.md`; `CapturePickerDescriptor.init(from:)` (`CaptureModels.swift:9640`). |
| `\` on a blank draft becomes `/` and arms a one-shot literal. A second `\` then replaces the `/` with a literal `\`. A `\` on an empty Go To filter is otherwise consumed. | `insertGotoSigilForBackslashInEditableTextView`, `replaceGotoSigilWithLiteralBackslash`; router `:590–602`, `:1228–1240`; `docs/keyboard.md` "Going to a task from any app (Command-\ then \)". |
| Go To's ⌘X already swaps the snapshot **in place**, with a session ID, request generations, and stale-request invalidation. The chip keeps the scope. | `CaptureTaskGotoScopeState.swift`; `capture-complete -C/--closed-tasks`. |
| Today's local fuzzy filter strips one leading sigil from the seeded filter. A second `/` typed into the Go To filter is therefore **silently stripped and does nothing**, so the keystroke is free to claim. | `FuzzyQuery.init(_:leadingSigil:)` in `FuzzyMatcher.swift`. |
| bob's only vault note walk (`NoteIndex::read`, used by `[[` completion) skips dot-directories and `_conflicts`, `_generated`, and `_templates`, but **lists everything else**. It reads every file in full, including headings and blocks. `bob capture-complete -- '[[sas'` takes **0.40 s** on apollo. | `capture_links.rs` `collect_markdown_paths` / `is_excluded_directory`; `src/native.rs` `ALWAYS_EXCLUDED_NOTE_DIRECTORY_NAMES`; timing. |
| The plugin's `obsidian://bob-goto-task` **requires `line`**. `bob-open-notes` accepts entries without a line but opens a **new tab** unless the note is already open. The plugin keeps an in-memory `filePositions` map, used today to restore the cursor when switching to the alternate file. | `675-plugin-goto-task-uri.js` `parseGoToTaskParams`; `docs/open-notes-uri.md`; `670-plugin-project-files.js:202–210`. |
| bob already resolves a hue for each area and root (`bob areas` reports `hue` and `hue_source`). The Mac app paints Pomodoro homes with it. | `src/native/areas/report.rs:55`; `pomodoro_homes/palette.rs`. |
| Obsidian's own exclusion setting is vault-wide. Excluding folders from the Quick Switcher also hides them from search, link suggestions, and Bases, so Bryan cannot tidy Obsidian's switcher without those side effects. | [Forum: Excluding folders from Quick Switcher also excludes them from Bases](https://forum.obsidian.md/t/excluding-folders-from-quick-switcher-also-excludes-them-from-bases/110121); `~/bob/.obsidian/app.json` has no `userIgnoreFilters`. |

## 3. Is this a good idea?

**Yes, but only as a Bob-aware jump, not as a copy of Obsidian's Quick Switcher.**

### Why it earns its place

- **It works from any app.** `⌘\` then `\` already reaches tasks from anywhere;
  `⌘\ \ /` (or `⌘\ / /`) will reach any note the same way, without first switching to
  Obsidian and pressing ⌘O.
- **It fits the house idiom.** Bob already doubles a sigil to *widen scope*:
  - `[[#` searches one note's headings, and `[[##` searches the whole vault;
  - `[[^` / `[[^^` do the same for block IDs;
  - `@` routes one item, and `@@` routes the whole draft.

  So `/` (tasks) → `//` (whole notes) reads as "go to, one level wider". The same
  pattern appears in VS Code's Quick Open, where a prefix in one box switches
  between files, commands, and symbols.
- **bob can curate better than Obsidian can.** bob knows note kinds (area, project,
  notebook, album, record, reference, daily, and period notes), project status, the
  parent tree, and area hues. It can hide machinery without touching Obsidian's global
  ignore list.
- **It is cheap.** The picker card, filtering, fuzzy matcher, handoff, in-place
  scope swap, URI handler, and Go To lifecycle all exist.

### Real costs and risks

1. **Scale.** About 3,600 rows, against `:`'s 464 (prior report: 206 KB). A
   naive per-keystroke scan costs about 0.4–0.6 s, which would make `//` feel worse
   than `/`. The fix is a frontmatter-only scan, a bob mtime cache, and an in-memory
   snapshot in the app that is fetched in advance (§9.3, §9.4).
2. **Noise.** References are 36% of live notes, and their long stems match almost
   anything by subsequence. "cash" matches 14 notes and 151 references; "plan"
   matches 18 and 104. Ranking must favour title, stem, and alias matches over path
   matches, and break ties by kind (§6.4).
3. **Mode creep.** `/`, `//`, ⌘X, and `\` together form a small language. Keep it
   at two levels. **Reserve `///`**: consume it in the picker and leave it as prose
   in the grammar, so it can later mean something deliberate such as full-text
   search.
4. **Overlap with Bob Refs.** Reference *notes* belong in `//`, because they are
   notes with annotations. Opening the *PDF* stays Bob Refs' job. A later ⌥↩ can
   bridge the two (§11).
5. **Three repos again.** The thin-client rule and Obsidian-side landing make that
   unavoidable, as they did for `/`. Each piece is small and additive.

### Alternatives I considered

| Option | Verdict |
| --- | --- |
| **App-only mode switch inside the Go To picker.** `/` on an empty filter refetches notes while the draft stays `/`. | **Rejected as the source of truth.** The draft would no longer say what is shown. A fast-typed `//foo` would be prose (an inbox task on submit), and no other client could use the mode. **Its in-place swap is adopted** as the hand-off polish (§7.2). |
| **A different sigil** (`?`, `[[` as a whole draft, `@`). | Rejected. `[[` already inserts links, and `@`/`?` are not "go to". `//` is what was asked for and fits the doubling idiom. |
| **A global hotkey that opens Obsidian's Quick Switcher** (Advanced URI or a plugin command). | Rejected. It has to switch to Obsidian first, and gets none of Bob's kinds, tiers, or ranking. Obsidian's exclusions are global. |
| **Full-text search** (qmd or ripgrep over bodies). | Out of scope. It is a different feature with different latency and ranking (see `202610/qmd_agent_vault_search`). Its natural future home is the reserved `///`. |
| **Per-keystroke bob queries** like `[[` (top 20). | Rejected for the picker. Local filtering over one snapshot is the house pattern for picker cards (`:`, `/`, `!`, `((`): it is instant, never flickers, and has stable selection. |

## 4. Which notes: the exclusion design

### 4.1 The rule

> `//` lists the documents Bryan **writes or reads as notes**.
>
> - It **hides** what bob or Obsidian owns as machinery, files that duplicate a
>   listed note, and attachments that have their own opener.
> - It never hides a real note just because it is old. Old notes move to an
>   **Archive** scope behind ⌘X.
> - It uses no filename heuristics: no "Untitled", no "tmp".

### 4.2 Measured tiers (apollo vault, 2026-11-15)

| Tier | What | Count | Why |
| --- | --- | ---: | --- |
| **Hidden** | Dot paths (`.bob/` with 396 `.md` under `ref-sources`, `.git`, `.obsidian`, `.trash`, `.sase`) | — | Already excluded by bob. Machinery. |
| Hidden | **Every path segment starting with `_`.** Today: `_generated` (1,131: 975 tag pages, 156 query pages), `_meta` (13 zorg migration reports, including a stale "Bob Home"), `_templates` (6), `_conflicts` (4), `_zorg_templates` (1) | 1,155 | Underscore folders are the vault's machinery convention. Generalising beyond bob's named list also catches `_meta` and `_zorg_templates`, which `[[` lists today. Conflict copies are a shell recovery task, not a navigation target. |
| Hidden | **Highlights sidecars**: `lib/**/<stem>.md` with a same-stem `.pdf` sibling | 191 of 192 | Highlights' Markdown export, which bob re-renders into `ref/<kind>/<stem>.md`. Listing them would show every annotated reference twice. |
| Hidden | `xlib/` (intake queue) | 0 `.md` now | In flight; it moves to `lib/` on scan. |
| Hidden | Non-Markdown files: PDFs (1,374), images, audio, JSON/JSONL, CSS/JS | — | Attachments. PDFs open through Bob Refs. **Exception:** `.base` views (§4.4). |
| **Archive (⌘X)** | Legacy daily companions `YYYY/YYYYMMDD_{habit,done,poms,events}.md` | 1,836 | All zorg-converted (`generated_from_zorg: true`). The newest is 2026-05-27. Nothing creates them now. |
| Archive | `done/**` task archives (`type: [[done]]`) | 54 | Closed-task history. `/` ⌘X already reaches their tasks. |
| Archive | Retired monthly notes `YYYYMM.md` | 27 | "Monthly notes are retired" (`glossary:period-note`). |
| Archive | Other legacy files in year folders (`2023_week_NN`, `_habit_wNN`, `2023_september`, …) | 18 | zorg-era period files that Bob's period tree does not own. |
| **Live** | Area notes (including inboxes), project notes, notebooks, albums, the bank hub, and untyped notes | 1,044 | The core of the vault. |
| Live | Reference notes (`type: [[ref]]`; 619 `ref/chat`, 322 `ref/zorg`, 282 `ref/ai`, …) | 1,294 | Real notes with annotations, ranked behind other notes at equal score (§6.4). |
| Live | Period notes (weekly, quarterly, yearly, `all_time`) | 59 | Bob creates and uses them. |
| Live, **date-keyed** | Daily notes `YYYY/YYYYMMDD.md` | 1,191 | See §4.3. |
| Live | Obsidian Bases (`*.base`) | 12 | Adjustment A3 (§4.4). |
| | **Total live / archive / hidden (of bob's 5,728)** | **3,600 / 1,935 / 205** | |

### 4.3 Daily notes: listed, but found only by date

Daily notes are the one family where "listed or not" is the wrong question:

- **Listed normally,** their aliases (`2026-11-14 Sat`) and ids would flood
  short queries. `sat`, `mon`, and digits would return hundreds of rows.
- **Hidden in Archive,** "yesterday's note" would need ⌘X.

**Recommendation:** list them as Live, but bob gives each one **only date match
keys**: the stem (`20261114`) and the ISO date (`2026-11-14`).

- A query made of letters never matches a daily note.
- `//1114` finds every Nov 14 note, newest first.
- `//2026-11` finds the month.
- The empty state pins **Today** and **This week** at the top (§6.2), which covers
  the most common case without typing.

### 4.4 Explicit non-exclusions

- **Vault-root agent files** (`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `OPENCODE.md`)
  and **`Untitled N.md`** stay listed. They are real files Bryan may edit or clean
  up. Name rules would break the "no heuristics" principle, and there are only a
  handful of them.
- **Templates outside `_templates`** (`template.md`, `chat_template.md` at the
  root) stay listed for the same reason. Move them to `_templates/` to hide them.
- **`.base` views** (`projects.base`, `refs.base`, `articles.base`, …) are listed as
  kind *View*. They are Obsidian-native dashboards and natural jump targets. This is
  adjustment A3. The plugin already opens non-Markdown files through
  `bob-open-notes`.

### 4.5 Who owns the rule

The rule lives in one bob module (`native/note_catalog.rs`) with documented,
golden-tested tiers. The Mac app never classifies a path. The hidden-tier rule for
underscore directories applies to `//` only. Changing the shared
`ALWAYS_EXCLUDED_NOTE_DIRECTORY_NAMES` would also change `[[` completion and other
scans, and that is a separate decision. File a follow-up if `[[` should match.

## 5. The keystroke model (intuitive)

| You type (blank draft) | Draft | Shows |
| --- | --- | --- |
| `/` | `/` | Go To · Tasks (unchanged) |
| `\` | `/` (backslash armed) | Go To · Tasks (unchanged) |
| `\` `\` | `\` | A literal backslash (unchanged; capture escapes like `\#fix` still work) |
| `/` `/` | `//` | **Go To · Notes** |
| `\` `/` | `//` | **Go To · Notes** (the first key may be the `\` alias; the second must be a real `/`, as requested) |
| `/` `\` | `/` | Consumed, as today; `\` never opens notes |
| `/` `/` `/` | `//` | The third `/` is consumed (reserved) |
| `//` then Backspace on an empty filter | `/` | **Steps back to Go To · Tasks.** It does not go back to a blank draft. |
| `/` then Backspace on an empty filter | (blank) | Idle agenda (unchanged) |
| `/fix` then `/` | `/fix` | A `/` inside a non-empty filter is filter text. The mode switch only happens at the start. |
| fast `//cash` before any picker appears | `//cash` | bob claims it, and Notes opens with `cash` seeded |

From any app: `⌘\` then `\` `/`, or `⌘\` then `/` `/`.

**Discoverability.** While the `/` filter is empty, its footer shows one extra
key-hint chip, **`/ Notes`**. The `//` footer shows **`⌫ Tasks`**. The ladder
teaches itself in both directions.

## 6. The card (beautiful)

### 6.1 Frame and transition

- **Scope token and caption.** The filter bar's scope token reads `//` and the
  caption reads **Go To · Notes**. With ⌘X it reads **Go To · Archive**. The `/` card
  keeps **Go To**.
- **No blink on `/` → `//`.** The card stays mounted, and its frame and row budget
  stay fixed ("filtering never resizes the panel"):
  - the scope token animates `/` → `//`;
  - the task rows cross-fade into note rows;
  - this is drawn from the warm snapshot (§9.4), so it is normally instant. When cold,
    a quiet "Loading notes…" placeholder fills the list, not a spinner.

  Today's continuation path calls `closePickerForAccept()` and then re-analyses,
  which would flash the idle agenda. §9.4 specifies the hand-off.
- Backspace back to `/` uses the same cross-fade in reverse.

### 6.2 Empty filter: a map, not a dump

Groups come from bob, in bob's order, under pinned headers:

1. **Today**: today's daily note and this week's note (bob's notion of today, the
   same one `capture-pomodoros` uses).
2. **Recent**: up to 10 notes most recently opened in Obsidian on this Mac. bob reads
   `lastOpenFiles` from the device-local `.obsidian/workspace.json`. That file is
   gitignored and the format is undocumented, so if it is missing or malformed the
   group is omitted silently (§10, risk 3).
3. **Areas**: in the `bob areas` tree order, indented by depth, inboxes included.
4. **Projects**: open projects first (WIP, then the rest), with a status capsule.
5. **Collections**: notebooks and albums.
6. A closing hint row: **"Type to search 3,412 more notes · ⌘X archive"**. The
   number is bob's count.

This is about 180 rows: a readable table of contents for the vault, with the
current context at the top.

### 6.3 Filtered: one ranked list

One flat list, like `:`, `/`, and `((`. Each row has:

- **Glyph**, tinted with the row's **root area hue** (bob reports it; the same hue
  as Pomodoro themes):

  | Kind | SF Symbol |
  | --- | --- |
  | Area | `square.stack.3d.up` |
  | Inbox | `tray` |
  | Project | `hammer` (matches the vault's WIP project presentation) |
  | Notebook | `book.closed` |
  | Album | `rectangle.stack` |
  | Record | `doc.richtext` |
  | Reference | `book` (already the reference glyph in pickers) |
  | Daily | `calendar` |
  | Period | `calendar.badge.clock` |
  | Mail | `envelope` |
  | Bank month | `banknote` |
  | View | `tablecells` |
  | Plain note | `doc.text` (already Note's glyph in `[[` rows) |

  Archive rows use the same glyph, desaturated.
- **Primary line**: bob's `title`, with matched characters emphasised the way `:`
  rows emphasise them.
  - For references and records, the title is the frontmatter `title:`.
  - For daily and period notes, it is a friendly date (`Sat, Nov 14 2026`,
    `2026 · W46`).
  - For everything else, it is the stem, which is Obsidian's identity for the note.
- **Secondary line**, dim: the parent breadcrumb (`cash › bank`), or the note's
  `summary:` when it has one.
- **Trailing locator**: the vault path, middle-truncated so the basename stays
  intact (`middleTruncatedPath`). It is always shown, because **204 basenames are
  duplicated** in the vault.
- **Capsules**, at most one or two: project status (WIP / Done / Canceled), `Archive`,
  `View`.
- **Detail strip**: "↩ Opens cash.md in Obsidian". An archive row reads
  "↩ Opens done/body_done.md · archive".
- **Footer**: `↑↓ Move · ↩ Go To · ⌘X Archive · ⌫ Tasks · esc Clear/Cancel`.
- **VoiceOver** reads the kind, title, parent, and path, then "double-tap to open in
  Obsidian".

### 6.4 Ranking

The app's existing `FuzzyMatcher` scores a filtered query against bob-supplied match
fields. In priority order:

1. title, stem, and aliases;
2. path, at a lower weight, so `ref/chat/…` segments cannot flood results;
3. date keys, for daily notes only.

Ties at equal score break by bob's per-row `rank`. That value encodes:

- kind weight: area/project > notebook/album > note > record > period > reference >
  daily;
- then Recent;
- then the path.

The app adds no Bob semantics; it applies bob's numbers. ⌘X Archive rows rank the
same way, within their own scope.

## 7. Requirement adjustments (called out)

| # | As requested | Adjusted to | Why |
| --- | --- | --- | --- |
| **A1** | "search for all note files" | **Live notes by default.** Archive behind ⌘X, and machinery, sidecars, and attachments never (§4). | Of 5,728 files, 1,935 are legacy or archive and 205 are machinery or duplicates. Listing them buries real notes. |
| **A2** | — | **Daily notes are live but date-keyed** (§4.3), and **Today / This week** are pinned in the empty state. | Gives date navigation without alias noise. |
| **A3** | "note files" | **Include `.base` views** as kind *View*. | They are Obsidian-native hubs (12 files). It costs almost nothing. Optional; see Q1. |
| **A4** | "a second `/` … triggers" | The second key must be a real `/` (as asked). **The first key may be `/` or the `\` alias**, so `\/` opens notes. `\\` stays a literal, and `/\` stays consumed. | Keeps `⌘\ \ /` from any app and leaves the literal escape untouched. |
| **A5** | — | **Backspace on an empty `//` filter steps back to `/`.** It does not clear the draft. | One rung per key. bob sends `trigger_removal_range` covering only the second `/`. |
| **A6** | — | A **`//query` may contain `/`** (`//ref/chat` narrows by path), but **`///` is reserved**: the picker consumes it and the grammar keeps it as prose. | Path narrowing is useful, and it leaves room for a future deliberate mode. |
| **A7** | — | **Accept never writes.** It opens the note by reusing a leaf that already shows it, otherwise the active leaf. It restores the plugin's remembered cursor for that note if one exists this session, otherwise the top. It records a Vim jump, then hides the panel and discards the draft without stashing it. | This is the same contract as `/`. Restoring the cursor makes a jump back to a note feel like Vim's `'"` mark. |
| **A8** | — | **⌘X toggles Archive** in `//`, mirroring "Completed" in `/`. | One key, one meaning: "the other drawer". |
| **A9** | — | **No note creation** from `//`. | "Go To never writes". New notes need a `parent`, which belongs in capture or Obsidian. |

## 8. Open questions for Bryan

1. **`.base` views (A3).** Include them? I recommend yes.
2. **⌘↩.** Keep it equal to ↩, which is parity with `/` and what I recommend for v1?
   Or make ⌘↩ "open in a new tab" for **both** `/` and `//`, following Quick
   Switcher's convention? That needs no plugin work, because the existing
   `bob-open-notes` already opens new tabs and takes `line`, `ref`, and `block`.
3. **Daily notes (A2).** Date-keyed Live (recommended), or Archive-only?
4. **Underscore folders.** Is anything under `_meta/` something you still open? If
   so, it moves to Archive instead of Hidden.
5. **Landing.** Restore the last in-session cursor (recommended), or always land at
   the top under the H1?

## 9. Recommended solution

### 9.1 bob-cli: `note_goto` (contract first)

**Claim.** Add `note_goto_query_token(item)` next to `task_goto_query_token`. It is
the one predicate used by execution, the editor parse, and completion. It matches
when all of these hold:

- the draft has exactly one item, and that item is one physical line holding one
  whitespace-delimited token;
- the token starts with `//`;
- the third byte is **not** `/`;
- the token is the whole trimmed draft.

The query may contain further `/` characters. `task_goto_query_token` stays
unchanged, since it already rejects `//`.

**Parse.** Mode `incomplete`, `needs: ["note_goto"]`, and one
`interactive_placeholder` span over the token (sigils included), with no
diagnostics.

**Execute.** Refuse first, in the same place `/` is refused, with teaching error T4:

```text
`//dee` opens the note Go To picker; pick a note to open it in Obsidian — it never captures
```

**Complete** (context `note_goto`):

- **Replacement.** It covers the whole token. The query is the text between `//`
  and the cursor.
- **Response.** It carries a `picker` descriptor with:
  - `kind: "note_goto"` and `scope_token: "//"`;
  - `trigger_removal_range` covering only the second `/`, so Backspace steps back
    (A5);
  - `action_continuation_keys: []`. The app consumes `/` itself under A6, and `[]`
    keeps bob the authority on that.
- **Top-level fields:** `vault_root`, and `counts { live, archive, hidden }`.
- **Rows:**
  - `replacement: ""`, so the shared decoder works;
  - `note_path`, `kind`, `title`, optional `subtitle` (`summary:` or a cleaned H1),
    `parent_chain` (stems up to the root area), optional `status` (projects), and
    optional `date` (daily and period notes);
  - `hue`;
  - `match` (an ordered list of `{field, text}`: title, stem, aliases, path, date
    keys);
  - `group` (`today|recent|areas|projects|collections|notes`) and `rank`;
  - `scope` (`live|archive`).
- **Target path.** Send `target` only if the app needs it. Otherwise the app joins
  `vault_root` and `note_path`. This keeps the payload about 40% smaller.

**`-A/--archived-notes`** (note_goto only, sorted alphabetically in help, with a short
alias per `cli_rules.md`) lists the Archive scope instead of Live. This mirrors
`-C/--closed-tasks`.

**`task_goto` gains** an additive `picker` descriptor whose
`action_continuation_keys` is `["/"]` on a **bare** `/` only, and `[]` once a
query exists. Older apps ignore it.

**The catalog module** `native/note_catalog.rs`:

- **Walk.** Use the hidden-tier rules in §4.2.
- **Read.** Read at most about 8 KB per file: frontmatter plus the first H1.
- **Classify.** Get kind, status, and parent from the existing areas and
  capture-targets discovery.
- **Recent.** Read `lastOpenFiles` from `.obsidian/workspace.json`, best effort.
- **Cache.** Keep an mtime and size keyed cache under
  `$XDG_CACHE_HOME/bob-cli/notes/`, so a warm run only stats files. Proxy timing for
  a cold frontmatter scan: about 265 ms (Python, apollo). The target is under
  100 ms warm on the Mac.
- **Never write.**

**Docs and tests:**

- Add a "Going to a note with '//'" subsection to `docs/capture.md`, including the
  tier table and the claim and prose table.
- Update the `/` table row "`//` → Prose" to point at the new section.
- Extend the help text of `capture-parse` and `capture-complete`.
- Add goldens:
  - `//`, `//cash`, `//ref/chat`, and the T4 error;
  - `///`, `//a b`, `Buy //x`, and multi-item drafts staying prose;
  - the JSON shape of a row;
  - a tier fixture vault covering a sidecar, a companion, `done/`, `_meta`, a daily
    note, and `.base`.

### 9.2 bob-plugins: `obsidian://bob-goto-note` (build first)

**URI v1:**

```text
obsidian://bob-goto-note?path=<absolute>
```

Reserve `heading=` and `line=` for later.

**Implementation:**

- Register it in `490-plugin-lifecycle.js` next to `bob-goto-task`.
- Put the handler in a new fragment of at most 1,000 lines (`677-plugin-goto-note-uri.js`).
- Reuse `resolveGoToVaultRelativePath`, `resolveGoToVaultFile`, and
  `captureGoToTaskJumpContext`.

**Landing:**

1. Reuse a leaf that already shows the note, keeping its cursor.
2. Otherwise open it in the active leaf via `openMarkdownFileWithLeafReuse`.
3. Restore `filePositions.get(path)` if present. Otherwise use line 0, or the first
   line after the frontmatter.
4. Ensure an editing view, centre the cursor, and record a Vim jump.
5. Open `.base` files with Obsidian's default view.

**Notices:**

- `Bob Go To: <path> is outside this vault`
- `… not found`
- `… could not open <name>`

**Tests, docs, and deploy.** Add tests for leaf reuse, position restore, an outside
path, a missing file, and `.base`. Write `docs/goto-note-uri.md`. Deploy with
`bob plugins sync`, then check it by hand from Terminal on the Mac:

```bash
open 'obsidian://bob-goto-note?path=…'
```

Check both warm and cold starts.

### 9.3 bob-mac-capture: `.noteGoto` source

**CaptureCore:**

- Add `CapturePickerSource.noteGoto` with trigger `//` and caption
  "Go To · Notes".
- Add `NoteGotoPickerIndex`, which builds `FuzzyField`s from bob's `match` list with
  the field weights in §6.4, groups by bob's `group`, and breaks ties by `rank`.
- Add the row content for each kind in §6.3.
- Add `ObsidianOpenURL.noteGotoURL(target:)`, built with `URLComponents`.
- Generalise `CaptureTaskGotoScopeState` into `CaptureGotoScopeState`, so that
  "Completed" and "Archive" share the session, generation, and invalidation logic.

**Panel model:**

- Add `note_goto` to `completionNeeds` and `pickerNeed`, and add
  `handleNoteGotoCompletion`, which mirrors `handleTaskGotoCompletion`.
- **Accept** goes down the Go To branch:
  1. check the stale-draft guard and block a double accept;
  2. dispatch through the injectable opener with
     `NSWorkspace.OpenConfiguration(activates: true)`;
  3. on success, hide the panel and discard the draft without stashing it;
  4. on failure, keep the picker open with "Couldn't open Obsidian".
- **Continuation.** Add `.taskGoto` to the sources that `continuePickerOperator`
  and `pickerOperatorContinuationKeys` accept, using bob's descriptor keys.

**Router:**

- In `//`, a `/` on an empty filter is consumed (A6).
- `\` on an empty filter is consumed. A `\`-armed literal is cleared once `/`
  continues.
- ⌘X toggles Archive.
- Backspace on an empty filter removes bob's `trigger_removal_range`.
- In the editor, `noteSeparatorToggleIntentIfEligible` must not record a `/` typed
  onto a draft that is exactly `/`. Otherwise `//` completion is gated behind a
  capture-rewrite call, the same reason it already skips a `/` on a blank draft.
  This needs to be verified in the implementation.

**Docs.** Add a "Go To Notes" section to `docs/task-pickers.md` (or a new
`docs/note-goto.md` linked from `pickers.md`), plus rows in `keyboard.md`
("Going to a note from any app") and a requirements bullet.

### 9.4 Fast and seamless: snapshot and hand-off

**Warm snapshot.** The app keeps the last `note_goto` snapshot **in memory only**,
following the privacy rule: it is never logged, never written to UserDefaults, and
never shown in Diagnostics. It refetches in these cases:

- **on `/` open**: `//` can only be reached through `/` (or by fast typing), so this
  prefetch usually wins the race;
- **on panel show**, as stale-while-revalidate;
- **on filtered vault events**, reusing `VaultTargetWatcher` (visible `.md`, `.base`,
  and `.obsidian/workspace.json`).

A byte-identical refetch publishes nothing. A changed snapshot that arrives while
`//` is open re-filters and keeps the selection by `note_path`.

**Hand-off.** When the continuation key is `/` from `.taskGoto`, the app:

1. sets `pickerHandoff = .noteGoto` and leaves the card mounted;
2. edits the draft and re-analyses as `continuePickerOperator` does today;
3. if the warm snapshot exists, installs the `.noteGoto` session from it at once,
   then replaces it with bob's authoritative response when that arrives;
4. otherwise shows the placeholder.

The reverse hand-off (Backspace back to `/`) does the same with the task snapshot.
If bob's parse disagrees (for example an old bob reports no `note_goto`), the
hand-off cancels and the draft state wins.

### 9.5 Rollout and compatibility

1. Plugin `bob-goto-note`, verified from Terminal.
2. bob-cli catalog, grammar, completion, docs, and goldens. Install `bob` on the Mac.
3. The Mac source, gated by macOS CI and watched to green.

| Mismatch | Result |
| --- | --- |
| Old bob, new app | No descriptor on `task_goto`, so the second `/` is stripped exactly as today. `//` stays prose. |
| New bob, old app | The `task_goto` descriptor is ignored. `//` reports `note_goto`, which the old app does not know, so no picker opens; the preview shows T4 and submit refuses. No junk task is filed. |
| New app, old plugin | The URI does nothing. Step 1 ships first. If it bites later, add a plugin-version probe. |

**Effort:**

| Repo | Days |
| --- | --- |
| bob-cli | 1.5 (catalog, tiers, cache, grammar, docs, goldens) |
| bob-plugins | 0.5 |
| bob-mac-capture | 1.5–2.5 (source, index, rows, hand-off, warm cache, CI loop) |

## 10. Risks and Mac acceptance checks

1. **Latency.** Time `//` cold and warm on the Mac. The bob warm scan should be
   under 100 ms, and the card swap should take one frame from cache.
2. **Snapshot size.** About 3,600 rows. Measure JSON bytes and decode time. If the
   payload exceeds about 1 MB, drop `target` and send `vault_root` once.
3. **`workspace.json`.** The format is undocumented, and forum reports describe it
   being truncated to 0 KB. Parse defensively, cap it at 1 MB, and omit Recent on
   any failure.
4. **Tier drift.** A new folder convention, such as a future `_inbox/`, would be
   hidden silently. The rule is documented and covered by goldens. `bob doctor`
   could report hidden counts.
5. **Hand-off races.**
   - Type `/` `/` faster than bob answers.
   - Backspace mid-fetch.
   - Press Escape during the hand-off.
   - Accept twice.
   - Hide the panel with an open in flight.

   None of these may open Obsidian late or capture anything.
6. **No writes.** Accepting any row leaves the vault byte-identical. Check with
   `git status` on the Mac vault.
7. **Landing.** Check each of these:
   - a note already open in a split;
   - a background tab;
   - Reading view;
   - `.base`;
   - Unicode and spaces in paths;
   - Vim `<C-o>` returning to where you were;
   - position restore after visiting another note.

## 11. Follow-ups (not v1)

- **⌥↩ on reference rows**: open the PDF in Highlights, the same as Bob Refs'
  Return.
- **`//note#heading`**: land on a heading, reusing `[[##` heading data and the
  reserved `heading=` URI parameter.
- **`///`**: full-text search, once a content index exists (qmd research).
- **⌘↩ = new tab** for `/` and `//` through `bob-open-notes` (Q2).
- **Decision record** (through `/sase_memory_write` once shipped): **"Note Go To
  lists live notes; archive behind ⌘X; machinery never."** It would record the tier
  rule, date-keyed dailies, `//` as a continuation of `/`, and that navigation never
  writes.
- **Decide whether `[[` completion should adopt the same hidden tier**, especially
  sidecars and `_meta`. Today `[[` can offer `lib/…` sidecars and zorg migration
  reports.

## Sources

**Code: bob-cli**

- `src/native/capture_language/{tokens,editor_parse,completion,markers,item}.rs`
- `src/native/capture_language/tests/goto.rs`
- `src/native/capture_complete/{engine,model,candidates,cli}.rs`
- `src/native/capture_links.rs` (`NoteIndex`, `collect_markdown_paths`)
- `src/native.rs` (`ALWAYS_EXCLUDED_NOTE_DIRECTORY_NAMES`)
- `src/native/areas/report.rs`, `src/native/pomodoro_homes/palette.rs` (hues)
- `docs/capture.md` ("Going to a task with '/'", aliases),
  `docs/highlights-ref-sync.md` (sidecars)

**Code: bob-mac-capture**

- `Sources/BobMacCapture/{CaptureKeyCommandRouter,CapturePanelController,CapturePanelModel,CapturePickerState}.swift`
- `Sources/CaptureCore/{CaptureModels,FuzzyMatcher,TaskLinkPickerPresentation,CompletionRowContent,ObsidianOpenURL,CaptureTaskGotoScopeState}.swift`
- `docs/{task-pickers,pickers,wikilink-completion,keyboard,refs}.md`

**Code: bob-plugins**

- `plugins/bob-navigation-hotkeys/src/{490-plugin-lifecycle,675-plugin-goto-task-uri,676-plugin-open-notes-uri,670-plugin-project-files,682-plugin-parent-change}.js`
- `docs/{open-notes-uri,goto-task-uri,bob-navigation-hotkeys}.md`

**Memory**

- `decisions:mac-capture-is-a-thin-client`
- `decisions:idle-capture-shows-ledger-agenda`
- `obsidian.md`
- `glossary:{area-note,project-note,period-note,reference-note,notebook,record-note,album-note,bank-month-note,inbox-file}`

**Prior research**

- `research:202610/slash_task_goto_in_obsidian/slash_task_goto_in_obsidian__final.md`

**Vault measurements** (read-only, apollo, 2026-11-15)

- Python scans of `~/bob`: frontmatter `type`, path shapes, sibling PDFs, and
  `generated_from_zorg`.
- `bob capture-parse` and `bob capture-complete` probes, and timings.

**External**

- [Forum: Excluding folders from Quick Switcher also excludes them from Bases](https://forum.obsidian.md/t/excluding-folders-from-quick-switcher-also-excludes-them-from-bases/110121)
- [Forum: List most recently opened files in initial quick switcher suggestions](https://forum.obsidian.md/t/list-most-recently-opened-files-in-initial-quick-switcher-suggestions/505)
- [Forum: workspace.json wiped to 0 KB](https://forum.obsidian.md/t/data-loss-layout-workspace-json-wiped-to-0kb-when-closing-obsidian-all-tabs-and-windows-lost/101989)
- [Quick Switcher++ (mode triggers, exclude folders)](https://community.obsidian.md/plugins/darlal-switcher-plus)
- [VS Code default keybindings (Quick Open)](https://code.visualstudio.com/docs/reference/default-keybindings)
- [Sigasi: Quick Open prefixes](https://www.sigasi.com/manual/creating-editing-exploring-code/navigation/quick-open/)
