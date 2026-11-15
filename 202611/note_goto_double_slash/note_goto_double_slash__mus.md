# `//` note-file search in bob-mac-capture (`__mus`)

Research: allowing a second `/` as the first character(s) of the capture draft to
search all Obsidian note files, while a second `\` keeps typing a literal `\`.
Goal: decide the best implementation, with exclusions, and critique the plan.

## TL;DR

Yes, do it. `//` is currently free (verified below), mnemonic, and low-collision.
Implement it as a thin-client feature: a new additive `capture-complete` /
`capture-parse` context in bob-cli first, then a Mac presentation that reuses the
existing Go To card in a second scope. Do not reuse `wikilink_note` or `task_goto`
unchanged. Exclude system/generated/archive paths (list below). Keep every existing
`\` literal behavior exactly as-is, make Backspace peel one `/` at a time, and open
results with `obsidian://open?path=` (not the task `bob-goto-task` protocol).

## 1. What exists today (verified)

### 1.1 `/` and `\` open task search

- Typing `/` as the whole capture draft opens the Go To picker (`task_goto`
  context); typing `\` into a blank draft is converted into `/` by the Mac app.
  Documented in `sase/repos/linked/bob-mac-capture/docs/task-pickers.md` ("Go To
  Picker" section): scope `/`, caption Go To, `obsidian://bob-goto-task` dispatch,
  Command-X toggles open vs completed tasks, Escape clears filter then cancels to a
  reopen chip, Backspace on an empty filter removes `/`, `\` on an empty filter is
  consumed (or types a literal `\` right after `\` opened Go To).
- Mac key routing: `Sources/BobMacCapture/CaptureKeyCommandRouter.swift`
  `isTypedSlash` / `isTypedBackslash` / `typedHashAliasKey`, plus the backslash
  branch (`draftIsBlank || draftIsBareGotoSigil`, `backslashLiteralArmed`,
  `.openGotoFromBackslash`, `.typeLiteralBackslash`, `.consumeKey`).
- Blank-to-`/` rewrite: `Sources/BobMacCapture/CapturePanelController.swift`
  `insertGotoSigilForBackslashInEditableTextView` replaces the whole blank draft
  with `/` through `NSTextView` (undo/accessibility native) and arms the one-shot
  literal via `CapturePanelModel.armBackslashLiteral()` /
  `takeBackslashLiteralArm()`.
- Bare-goto predicate: `Sources/BobMacCapture/CapturePanelModel.swift`
  `draftIsBareGotoSigil` (`plainDraft` trimmed == `"/"`).
- bob-cli claim (single slash only): `src/native/capture_language/tokens.rs`
  `task_goto_query_token` requires exactly one `/` in the token and
  `item.source.trim() == token.text`. Completion field:
  `src/native/capture_language/completion.rs`
  `task_goto_completion_field_at` (query = text after sigil, replacement covers the
  whole token, multi-token and second-`/` drafts return `None` "exactly like the
  claim predicate"). Candidates: `src/native/capture_complete/candidates.rs`
  `task_goto_candidates` / `closed_task_goto_candidates`, engine wiring in
  `src/native/capture_complete/engine.rs`, rendering in
  `src/native/capture_complete/render.rs` (`task_goto_line`,
  `CompletionContext::TaskGoto`).

### 1.2 `//` is free today (measured, not inferred)

Against the live vault (`~/bob`, 7,266 `.md` files):

- `bob capture-parse --format json -- '//'` returns `mode: task`, no needs, no
  spans: plain prose.
- `bob capture-parse --format json -- '//cash'` returns the same prose result.
- `bob capture-complete --cursor 2 --format json -- '//'` returns `context: null`,
  zero candidates.

So `//` claims nothing and completes nothing. It is a clean slot. (One live
In-Progress task already tracks this request: `bob.md` block
`slash-slash-file-search`, "Add ability to use `//` in bob-mac-capture app to
search for specific note file".)

### 1.3 Thin-client rule governs the shape

Per `decisions:mac-capture-is-a-thin-client`, bob-cli owns grammar, completion
data, preview, and vault mutation; the app renders what `bob` returns, may filter
or rank locally, but never decides syntax. New behavior lands in bob-cli and
`docs/capture.md` first, then the app decodes and presents it. The wire grows
additively (`decodeIfPresent`, `schema_version` gate). The Mac capability table is
`sase/repos/linked/bob-mac-capture/docs/protocol.md`.

### 1.4 The closest existing note index

`src/native/capture_links.rs` `NoteIndex::read` + `collect_markdown_paths` +
`note_candidates` powers `wikilink_note` completion (`[[query`). Ranking tiers
(`MatchKind`: exact/prefix/word-boundary/acronym/substring over stem, path,
alias) are exactly the feel a `//` picker wants. But it is not a drop-in
snapshot API: it truncates to `RESULT_LIMIT = 20` ranked rows per keystroke, while
the task pickers fetch one full snapshot and filter locally for flicker-free
typing. `[[sase` measured ~0.5 s end-to-end on this vault, which is fine once per
`//` session but not per keystroke.

Exclusion precedent in that walker (`is_excluded_directory`): skip dot-directories
plus `is_always_excluded_note_directory_name` (`src/native.rs`):
`.bob, .git, .obsidian, _conflicts, _generated, _templates`. Note what it does
*not* exclude: `done/`, daily notes, `ref/`, `mail/`, `legacy_*`, `Untitled*.md`,
`_meta/`, `ref_history/`. Proof: `[[sase` results are dominated by
`done/sase_*_done.md` rows, and `[[cash` returns `cash.md`,
`done/cash_done.md`, `legacy_cash.md`.

### 1.5 Vault census (why exclusions matter)

- 7,266 `.md` files total. Top concentrations: ~3,096 daily notes
  (`2023/2024/2025/2026`), 826 `*_habit.md` companions, 54 `done/*_done.md`, 28
  `subscriptions/`, 23 `tv/`, 15 `podcasts/`, 12 `movies/`, 104 `eat/`, 81 `lit/`,
  59 `prompts/`.
- `ref/` holds 1,297 files (papers/notes/chat/zorg subtrees); `mail/2026/` holds
  21 note files; `_generated/` holds 1,131 files (already excluded from the index
  by name); `ref_history/` exists; `_meta/` holds 2 notes plus `migration/`;
  `_templates/` holds 6 templates; `_conflicts/` holds dated conflict copies plus
  `sync_conflicts.md`; `Untitled*.md` + `Untitled.base` + `Untitled.canvas` exist
  at root (canvas/base are non-`.md` and already ignored by the `.md` filter).

## 2. Critique: is `//` a good idea?

Yes, with two reservations handled below.

Strengths:

- Discoverable and mnemonic: `/` finds tasks, `//` finds files, the same way
  paths and URLs nest. Users already learn `/`-means-search once.
- Free and safe: `//` as a whole-draft single token is prose today, and capture
  drafts beginning with `//` are rare. Full URLs (`https://…`) do not collide
  because the claim requires the whole draft to be the token.
- Consistent with the walk: Go To already has open/completed modes via Command-X;
  a file mode completes the trilogy (tasks → files) without a new window or
  hotkey.
- Thin-client compatible: one new context, same card, same open-discard
  semantics (nothing minted, stamped, or captured; failed open keeps the picker).

Reservations and answers:

1. Mode confusion (`/` vs `//`). Mitigate with a visible scope capsule
   (`Go To · Tasks` vs `Go To · Notes`), distinct row icons (status glyph vs
   document glyph), distinct detail copy ("Opens note.md at line N" vs "Opens
   note.md"), and Backspace peeling one `/` at a time so users can always step
   back to task mode.
2. Swallowing `//comment`-style prose. Accept: capture items that are literally a
   `//…` single token are vanishingly rare, and Escape-to-chip plus Backspace
   gives a two-key exit. Do not add a preference or a "literal `//`" escape
   sequence; it would complicate the one-shot literal machinery that already
   exists for `\`.

Alternatives considered and rejected:

- Command-X-style toggle inside Go To (tasks ⇄ notes). Less discoverable, hides
  the mode, and overloads a key that already means open ⇄ completed. Keep
  Command-X exactly as-is inside `/` mode.
- A different sigil (`?`, `%`, `=`). All are taken by capture grammar
  (`decisions:capture-sigils-say-where-what-how`, plus `%n`/`@@` notebook rules
  and `=` relation alias). `//` is the only free mnemonic.
- Shelling out to Obsidian Quick Switcher. Loses the capture panel's context,
  hotkey, and discard semantics; also breaks the thin-client rule.
- Server-side per-keystroke `wikilink_note` reuse with no Mac snapshot. Simpler
  wire, but reintroduces per-keystroke spawn flicker the task pickers deliberately
  eliminated. Prefer one snapshot + local filtering.

## 3. Required adjustments to the request as stated

1. "Certain exclusions that you should decide on" needs to become an explicit
   list (Section 4), not a TODO for implementation. The implementer should not
   re-derive it from `ALWAYS_EXCLUDED` alone, because that list still admits
   `done/`, conflict-adjacent junk, templates-by-pattern, and placeholder files.
2. "A second `\` types a raw `\`" must be specified as preserving the existing
   one-shot literal machine, not as new behavior. No new `\` handling is needed;
   the work is to *not* disturb `backslashLiteralArmed`,
   `hashAliasLiteralArm`, and the `noteSeparatorToggleIntent` typing of
   `"\\" | "/"`.
3. "Trigger a search for all note files" must be scoped to *openable Markdown
   notes*, not literally all files. Non-`.md` (canvas, base, images, PDFs),
   dotfiles, and excluded directories never appear. The picker opens the file at
   top (or first line), never a task row.
4. The design must state the wire contract first (new context + need + grammar
   bump + `docs/capture.md` + `docs/protocol.md`), per the thin-client decision
   and `cli_rules.md` (additive `capture-complete` contexts; never a new
   `bob capture` subcommand since free text would swallow it). Mac-only
   implementation is not an option.

## 4. Exclusions (decided)

Principle: the picker lists every note Bryan could plausibly want to open, and
hides everything that is machine-owned, duplicated, templated, or a placeholder.
Ranking does the rest; exclusion is reserved for categories that are *never* the
right answer.

Exclude (in addition to the existing walker rules):

1. Dot-directories and files at any depth (already excluded; keep).
2. `ALWAYS_EXCLUDED` directories (already excluded; keep and share the helper):
   `.bob/`, `.git/`, `.obsidian/`, `_conflicts/`, `_generated/`, `_templates/`.
   Add `.sase/` for symmetry with the vault-sync and article pipelines if not
   already covered by the dot rule.
3. `done/` — 54 stale `*_done.md` duplicates. Task search already covers done
   tasks via Command-X; file search must stay live-only. This is the single
   highest-value exclusion (it dominates `[[…` results today).
4. `ref_history/` — superseded readings; opening them by accident is pure cost.
5. `_meta/` — pilot and migration scaffolding, not notes Bryan opens.
   (If a future `_meta` note becomes user-facing, allowlist it explicitly rather
   than opening the directory.)
6. `Untitled.md` and `Untitled <N>.md` — empty placeholders. Match by exact stem
   pattern, not by substring, so a real note titled e.g. `Untitled Essay` still
   appears.
7. Non-`.md` files — already excluded by `has_markdown_extension`; state it so
   canvas/base/images/PDFs are visibly out of scope.
8. Conflict copies that escape `_conflicts/` if any (defensive suffix match on
   `*.local-*.md`-style host-stamped names is unnecessary today; the directory
   exclusion covers every observed case, so do not add filename heuristics beyond
   item 6).

Explicitly include (do not exclude, rank instead):

- Daily notes (`2023/…/2027/`, `20250101.md` style) and `*_habit.md`. They are
  legitimate open targets and Go To already includes daily notes in completed
  mode. Rank them below named notes on equal match quality (below).
- `ref/`, `mail/`, `chat/`, `lit/`, `prompts/`, `bank/`, `eat/`, `tv/`,
  `podcasts/`, `movies/`, `text/`, `code/` notes, `triage/`, `plans/`,
  `sase_blog_zettel/`, area/project/inbox notes. All are user content.
- `legacy_*` notes. They are old but real; rank them low rather than hiding
  them, so migration cleanup can still find them.

## 5. Design: intuitive, reliable, beautiful

### 5.1 Trigger and editing model

- `blank + /` → task Go To (unchanged). `blank + \` → `/` + armed literal
  (unchanged).
- `"/" + /` → note-file mode. The draft becomes `"//"`, `capture-parse` reports
  a new need (e.g. `note_goto`), and `capture-complete` serves the note snapshot.
  The Mac switches the same card to the Notes scope without closing and
  reopening it (no focus jump, no filter loss beyond the added `/`).
- `"/" + \` → existing literal path only (consumed or literal `\` per the armed
  state). Never enters note mode. `"//" + \` types literally; no third mode.
- Typing a third `/` (`"///…"`) stays in note mode as filter text; it does not
  open a third scope and does not need a grammar error.
- Backspace: `"//query"` with non-empty filter clears the filter first (existing
  picker behavior); `"//"` with empty filter deletes one `/` back to `"/"`
  (task mode, filter preserved if any); `"/"` with empty filter removes the
  trigger and restores the idle agenda (unchanged). Escape: clears filter, then
  cancels to the reopen chip (unchanged); the chip preserves which scope
  (`/` vs `//`) it reopens.
- Multi-item drafts, multi-token drafts (`"// a b"` typed as literal draft text
  outside the picker), and `"//"` pasted mid-draft never trigger: the claim is
  whole-draft single-token only, mirroring `task_goto_query_token`.
- IME/marked text, Command/Control modifiers, and key repeat follow the existing
  `isTypedSlash` / `isTypedBackslash` gates; `//` adds no new modifier behavior.

### 5.2 bob-cli contract (implement first)

- New claim predicate `note_goto_query_token` beside `task_goto_query_token`:
  whole-draft single token starting with `//`, holding at least two leading
  slashes, treated assigil `//` + query. `task_goto_query_token` keeps requiring
  exactly one `/` so `/` behavior is byte-identical.
- New `CompletionContext` (suggested name `note_goto`, paralleling `task_goto`
  and `wikilink_note`; alternatives `goto_note`/`note_search` are acceptable but
  pick one and keep it). New parse need (same name), new
  `interactive_placeholder` span over the whole token, new picker error string,
  additive candidate fields: `replacement` (empty for picker rows, as in
  `task_goto`), `path` (vault-relative), `name` (stem), `target` (absolute),
  optional `alias`, `match_kind`, plus a small additive `note_kind` /
  directory subtitle for grouping. Never insert grammar on accept: replacement
  stays empty; the Mac opens instead of splicing.
- Snapshot semantics: one full catalog fetch per `//` session (reuse
  `NoteIndex::read` + `best_note_match` ranking, minus the 20-row truncation for
  the snapshot path, or a documented capped snapshot with local filtering over
  the cap clearly specified). Apply the Section 4 exclusions in the shared
  walker so `[[…`, `note_goto`, and any future note list agree. Rank empty-query
  rows by: capture-route notes first (inbox/area/project), then recent daily
  notes, then everything else alphabetical; non-empty queries use the existing
  `MatchKind` tiers with daily/habit and `legacy_*` demoted one tier on ties.
- Grammar bump, `docs/capture.md` update, `capture-complete --help` example
  (`bob capture-complete -c 2 -f json -- '//'`), protocol capability entry in
  the Mac `docs/protocol.md` table, and compatibility behavior: older `bob`
  answers `//` as prose (no context) → new Mac shows the existing calm
  "Update bob" hint, exactly like the Command-X fallback.
- Tests: claim predicate (`/`, `//`, `//q`, `///`, `// a`, multi-line),
  completion field ranges, exclusion unit tests (`done/`, `ref_history/`,
  `_meta/`, `Untitled`, dot dirs, non-md), ranking tie-breaks
  (named > daily > habit > legacy), and a golden `capture-complete` fixture for
  `//`.

### 5.3 Mac presentation (implement second)

- Reuse the Go To card. Scope capsule reads `Go To · Notes` (vs `Go To` /
  `Go To · Completed`); keep `Go To · Completed` exclusively a `/`-mode concept.
  Command-X stays a `/`-only key; in `//` mode it is consumed (or hidden from the
  footer) so users do not expect completed-task semantics on files.
- Rows: document icon (never a task status glyph), title = stem (or alias when
  matched, shown as `name | alias` like wikilink rows), subtitle = vault-relative
  directory breadcrumb, right side = `note.md` short path. No schedule capsules,
  no Pomodoro chips, no "pulls forward" warnings, no block-ID `⊕` prompts, no Add
  block ID flow: every row is directly openable, including ID-less notes.
- Detail strip: `↩ Opens <path>` (and `at line 1` only if a line is sent; prefer
  top-of-file opens). Filter: spaces as AND terms, ranked flat when non-empty;
  grouped sections when empty (capture routes, then recents/dailies).
- Accept (Return/Tab/click/Command-Return/Control-Return): all four open the file
  and hide the panel, discarding the draft — same "read-only, nothing captured"
  semantics as Go To. Dispatch `obsidian://open?path=<absolute>` via the
  existing `CaptureCore/ObsidianOpenURL.url(forAbsolutePath:)` helper, not the
  `bob-goto-task` task protocol (no plugin dependency, no line/ref validation).
  Failed dispatch keeps the picker open with "Couldn't open Obsidian"
  (existing copy).
- Footer keys line: `Return/Tab Open · Esc Clear/Cancel · ⌫ Removes a /`
  (plus the consumed-`\` note only if user testing shows confusion; default to
  silence since `\` behavior is unchanged).
- Filtering is local after the one snapshot (the `CaptureCore`-local fuzzy/AND
  matcher precedent from the `^` picker). Respect the 20-second
  `BobProcessClient.defaultTimeout`; on timeout show the calm browse hint, never
  a red grammar error, mirroring the `task_goto` need behavior.

### 5.4 Reliability notes

- Performance: one ~0.5 s snapshot per `//` session (measured for `[[…` on this
  vault) followed by instant local filtering is the budget. Do not refetch per
  keystroke. Cap empty-query rendering (e.g. first 50) while keeping the full
  snapshot in memory for filtering.
- Safety: `//` never captures, mints IDs, links tasks, or walks anything. The
  panel hides only after a successful open dispatch, mirroring Go To.
- Compatibility: unknown-context rendering stays generic; missing fields use the
  existing compatibility table. New `bob` + old Mac degrades to today's prose
  `//` (acceptable); old `bob` + new Mac shows "Update bob".

## 6. Recommended solution

1. bob-cli phase (required first): add the `//` claim, the new completion
   context + need + span + error copy, the exclusion-tightened note snapshot
   reusing `NoteIndex`, ranking with daily/habit/legacy demotion, grammar bump,
   `docs/capture.md` + help examples, and tests. Keep `/`, `\`, Command-X, and
   every `wikilink_note` behavior byte-identical.
2. Mac phase (second): trigger on second `/` in the same card, Notes scope UI
   per Section 5.3, local filtering, `obsidian://open` dispatch, footer/docs
   updates (`task-pickers.md`, `protocol.md`, `keyboard.md`, typing tips).
   Gate on macOS CI per repo rules.
3. Explicit non-goals: no `///` mode, no `\`-mode changes, no completed toggle in
   notes mode, no block-ID flow, no capture/preview/capture-target changes, no
   new top-level `bob` subcommand, no preferences flag.

Verdict: ship it. The cost is one additive context plus one presentation scope;
the payoff is the missing half of "go somewhere fast" (tasks today, files with
`//`), with exclusions that keep the list trustworthy and a trigger that stays
out of the way of every existing gesture.
