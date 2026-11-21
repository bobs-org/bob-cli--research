# Obsidian `[[` link completion in free-form prompts

Researcher: mus · 2026-11-21 · swarm `5o` (`__mus` report)

Request: support Obsidian link completion, triggered by typing `[[`, in any
free-form text input prompt shown to the user (examples given: intentions,
work log). Lead the design so it is intuitive, reliable, and beautiful.
Critique the plan, adjust requirements where justified, end with a recommended
solution.

## Verdict

Yes — do it, but narrow the requirement. Do not ship "`[[` in any prompt".
Ship "`[[` note/heading/block completion in the dozen human-sentence prompts,
behind one shared client helper, backed by Obsidian's own index, with Bob's
ranking and replacement grammar ported — not with a `bob` subprocess per
keystroke."

Concretely: build one shared `attachObsidianLinkSuggest()` for single-line
`<input>` and multi-line `<textarea>` prompt fields (intentions, summary,
reflection, work/schedule/rotten/cancel reasons, successor inline cancel),
that mirrors Obsidian core `[[` behavior and Bob's existing
`capture-complete` wikilink grammar. Back it with `app.vault` /
`app.metadataCache` on the client, not with `bob capture-complete` per
keystroke. Keep `[[` literal everywhere else (plugin settings, bank category,
email `To`, command sheet). This is a client UX feature with a small
grammar contract — not a new CLI command.

The rest of this report is the evidence and the design.

## 1. What "any free-form prompt" actually means today

The request names intentions and work log, but the plugin tree has many more
human-sentence fields. I inventoried every `createEl("input")` /
`createEl("textarea")` / `.addText()` prompt in `bob-plugins` (excluding
generated `main.js`). The ones that take human sentences — and therefore
plausibly take `[[` links — are:

**Work / lane / scheduling sentences (all single-line `<input>` + log-recall band):**

- `WorkSummaryPromptModal` (`plugins/block-id-prompt/src/090-prompt-modals.js:385`):
  `this.inputEl = fieldEl.createEl("input", ...)` with placeholder
  `"What did you get done?"`, plus `recallBandEl`, `logRecall.attach({ kind:
  "work", ... })`, live preview, `::` Dataview warning.
- `LaneReleaseSummaryModal` (`plugins/bob-navigation-hotkeys/src/190-summary-modals.js:735`):
  `"Release task"` / `"Optional: why is this pending? Saved to the Work Log."`,
  same `attach({ kind: "work" })` pattern.
- Task Link Lane + Lane Release prompts, Task Card schedule-review reason and
  schedule-work-log, lane-release-reason — see `docs/log-recall.md` "Surfaces"
  table and `plugins/bob-navigation-hotkeys/src/370-picker-schedule-work-log.js:47,80`
  (`reasonInput`, `summaryInput`).
- Successor inline cancel reason
  (`plugins/bob-navigation-hotkeys/src/206d-successor-picker-verdict-render.js:321`).

**Decay / keep sentences (single-line `<input>` + log-recall):**

- `RottenKeepReasonStage`
  (`plugins/bob-navigation-hotkeys/src/195-rotten-keep.js:502`):
  `inputWrap.createEl("input", ... placeholder: keep/stay reason)`,
  `attach({ kind: "rotten", ownKeys: true })`, history rows, `↵`/`esc` hints.
- Freshness refresh summary modal
  (`plugins/bob-navigation-hotkeys/src/192-freshness-refresh-summary-modal.js:77`).

**Intentions / summary / reflection (card editor stages):**

- Intention stage: single-line `<input class="bob-intention-stage-input">`
  (`plugins/bob-ledger-tools/src/297cc-plugin-intention-card-editor-paint.js:130-145`,
  `data-intention-input="intention"`), one-line paste normalization in
  `297ca-plugin-intention-card-editor-input.js` (`intentionCardEditorPaste`,
  `intentionCardNormalizeIntentionLine`).
- Summary stage: same single-line input with `data-intention-input="summary"`.
- Reflection stage: auto-growing `<textarea class="... is-reflection">`
  (`297cc...paint.js:130-133`, `intentionCardEditorAutogrow`), `rows="3"`,
  `Enter` saves / `Shift+Enter` newline.

**Should NOT get `[[` completion (adjustment to the request):**

- Plugin settings `.addText()` rows (`bob-command-mode/src/090-plugin.js:710,733,748`,
  `bob-articles/src/040-modal-settings.js:120`, `bob-mail/src/050-plugin.js:27`):
  machine identifiers, not prose.
- Bank category suggest (already an `EditorSuggest`, `241k-plugin-bank-actions.js:894-962`):
  a closed vocabulary, not vault links.
- Email compose `To` / `Subject`
  (`bob-mail/src/045-compose.js:200-202`): recipients, not vault paths.
- Command sheet input (`bob-command-mode/src/170-sheet.js:279`,
  `175-args-vim.js:450`): its own grammar; `[[` there would collide.
- Picker search fields (`080-picker-ui-and-task-link-modal.js:225`,
  `085-pomodoro-link-picker-modal.js:260`,
  `087-task-wikilink-picker-modal.js:76`,
  `200-filtered-picker-modals.js:102`): they already *are* pickers.

Adjustment 1: change "any free-form prompt" to "the sentence-prompt allowlist
above." Everything else keeps literal `[[`.

## 2. How `[[` works today (two separate systems)

### 2a. In the Markdown editor: Obsidian core owns it

Vault editing views get core `[[` completion for free. Plugins only get it in
real editors via `EditorSuggest`:

- `EditorSuggest<T> extends PopoverSuggest<T>` (`obsidian.d.ts:4078`):
  `onTrigger(cursor, editor, file) -> { start, end, query } | null`,
  `getSuggestions(context)`, `renderSuggestion(value, el)`,
  `selectSuggestion(value, evt)`, `limit`, `setInstructions()`.
- `onTrigger` runs on every keypress — "keep it simple, return null early."
- Precedents in this repo: `BobEmojiSuggest extends EditorSuggest`
  (`bob-emoji/src/040-emoji-suggest.js`) with `emojiFindTrigger` regex
  `/(^|\s):([A-Za-z0-9_+-]*)$/` plus a CodeMirror `syntaxTree` guard that
  refuses code/math/frontmatter/comment
  (`030-emoji-model.js:emojiContextAllows`, `emojiFindTrigger`). Bank category
  suggest defensively imports `EditorSuggest`
  (`241k-plugin-bank-actions.js:8-17`) and no-ops when absent (mobile).

Modal `<input>` / `<textarea>` elements are **not** editors, so
`registerEditorSuggest` never fires there. Every prompt in §1 is a `Modal`
with a plain DOM input — that is why `[[` does nothing in them today, and why
this feature is custom UI work, not a one-line registration.

### 2b. In capture drafts: `bob` owns it (`capture-complete`)

`bob capture-complete` already completes wikilinks inside capture text, with
precedence over capture markers ("when the cursor is inside an Obsidian
wikilink, wikilink completion takes precedence", `capture_complete/cli.rs:341`).
Verified live this session:

```text
$ bob capture-complete -c 5 -f json -- '[[sas'
→ {"ok":true,"context":"wikilink_note","replacement":{"start":2,"end":5},
   "candidates":[{"replacement":"chat/sase_fix_tests_prompt]]","cursor_after":30,
   "path":"chat/sase_fix_tests_prompt.md","name":"sase_fix_tests_prompt",
   "match_kind":"prefix_stem"}, ...]}
```

Grammar and ranking live in `src/native/capture_links.rs`:

- `completion_field_at(raw, cursor, current_note_path)` → `LinkCompletionField
  { context, query, replacement: (start, end), target, suffix_close,
  existing_close_end }`; `scan_links` + `code_ranges` keep completions out of
  code spans and alias ranges (`cursor > alias.start` completes nothing).
- `note_candidates` / `heading_candidates` / `block_candidates` over
  `NoteIndex::read(bob_dir)`: stem + path + frontmatter `aliases`
  (`aliases_from_frontmatter`), `RESULT_LIMIT = 20`, tier-then-score-then-path
  order (`tier_order`, `compare_score_rank`), `match_kind` from
  `Empty/ExactAlias/ExactStem/.../SubstringPath`.
- Replacement owns the missing close: `replacement_text()` appends `"]]"` when
  `suffix_close`, and every row reports `cursor_after`.
- Scopes: `[[note`, `[[note#Head`, `[[note#^block`, `[[#Head` (current),
  `[[##Head` / `[[^^block` (vault-wide), `[[target#...` (target-qualified).
  Living notes first; archived/hidden follow.
- `((query` opens the separate `wikilink_task` context
  (`capture_complete/engine.rs:248`, `capture_task_wikilinks.rs`): vault task
  catalog, `[[target#^id]]` inserts, shell completion returns nothing.

Two deliberate interactions already exist with free text:

- `work_log` phrase completion explicitly refuses summaries containing `[[`
  ("summaries containing `[[` never complete as `work_log`", `cli.rs`
  work-log paragraph; `docs/log-recall.md`: "queries the summary text ...
  summaries containing `[[` never complete as `work_log`").
- Inline capture text otherwise still completes note/heading wikilinks.

So Bob already decided: `[[` means "link", not "recall phrase", and task links
are `((`, not `[[`. New prompt completion must preserve both.

## 3. Requirements the request leaves open (proposed answers)

| # | Question | Proposed answer (justified, §5) |
|---|----------|----------------------------------|
| 1 | Which syntax? | `[[note`, `[[note#Heading`, `[[note#^block]]`, `[[#Head`, `[[##Head`, `[[^^block]]`, `[[alias\|shown]]` passthrough. No `((` tasks, no embeds `![[`, no code-span links. |
| 2 | Which fields? | §1 sentence allowlist only. |
| 3 | Insert text? | Bob `insert_target` (relative path without `.md`), plus `#Heading` / `#^block` suffix; append `]]` when unclosed; preserve a typed `\|alias` tail (complete only the target side, as today). |
| 4 | Ranking? | Port Bob's order: tier → match tier (exact > prefix > word > substring; alias/stem/path) → path. Do not use Obsidian default sort, or capture-box and prompt-box disagree. |
| 5 | Keyboard? | Mirror core: `↑`/`↓` move, `Tab`/`Enter` accept, `Esc` dismisses popup first (prompt second), type-to-filter, click fills without committing. |
| 6 | Log recall coexistence? | `[[` popup outranks the USED BEFORE band while open. `Ctrl+N/P` stay with log recall; `↑`/`↓`/`Tab`/`Enter`/`Esc` go to the link popup while open; plain typing after a fill becomes the new draft (existing log-recall rule). |
| 7 | Offline / no bob? | Must work with no `bob` binary at all (pure client index). Never block typing; on index failure `[[` stays literal. |
| 8 | Frontmatter safety? | Intentions live in frontmatter (`intentions/fields.rs`, `protocol.rs` ops `intentions.set/insert/replace`). `[[a|b]]` contains `:`? No — but `\|` and `#`/`^` are YAML-safe inside a quoted string; writers must keep using the existing quoted-string path (verify with `periods update -i` dry run). |
| 9 | Reflection newline? | In the reflection `<textarea>`, `Enter` without an open popup saves (existing); with popup open, `Enter`/`Tab` accepts, `Shift+Enter` newline still works, `Esc` dismisses popup first. |

## 4. Critique: is `[[` in prompts a good idea?

**Yes, with three caveats.**

For: intentions, summaries, reflections, and work/schedule/rotten/cancel
reasons are the exact sentences that later get re-read (period briefs,
`docs/plan.md`, review footers). Letting Bryan name the note at write time —
`Shipped [[sase_loop]] fix`, `Blocked on [[plans/sase_xprompt_jinja]]` —
beats post-hoc linking, matches what the editor already teaches his fingers,
and makes Dataview/Backlinks actually useful on his own words. The capture box
already proves the grammar; extending it to prompts removes a gratuitous
inconsistency ("`[[` works there but not here").

Against / risks:

1. **Recall pollution.** Log-recall phrases are vault-derived
   (`docs/log-recall.md`: markers `🗓️ SCHEDULE LOG`, `🛠️ WORK LOG`, `🥀
   ROTTEN LOG`, `❌ CANCEL LOG`; `bob logs list` frecency). If `[[`-bearing
   sentences are ingested verbatim, every note rename litters history with
   stale `[[old]]` strings. Mitigation: store the literal text (links are
   content), but exclude `[[`-bearing phrases from the recall index — or
   normalize them to plain text for matching. This matches today's
   `work_log`-vs-`[[` mutual exclusion; extend the rule to the prompt side.
2. **Frontmatter fragility.** Intentions are YAML, not Markdown body. A naive
   string splice that breaks quoting breaks the whole note. Mitigation: reuse
   the existing intention ops path (`intentionOpsSet/Insert/Replace` in
   `297c-plugin-intention-card-editor.js:154-168`) — completion only edits the
   DOM input value; the save path is unchanged and already validated
   (`intentionCardEditorBlockingWarning`, guarded session retries).
3. **Every-prompt scope creep.** Settings, bank, email, command sheet, and
   picker search boxes look like inputs but are not sentences. Giving them
   `[[` popups is confusing and collides with their own grammars (bank
   `EditorSuggest`, command sheet args, picker filters). Hence Adjustment 1.

A rejected alternative: make prompts spawn `bob capture-complete` per
keystroke and render its rows. It reuses ranking exactly, but it forks a
process and rescans the vault on every keypress (`NoteIndex::read` walks and
parses every note; shell completion itself carries a 150 ms deadline,
`docs/completion.md:132`, precisely because vault scans cannot block typing).
Prompts are keystroke-driven UI; a subprocess round-trip with a 30-second
reusable scan (the log-recall allowance, `docs/log-recall.md`) is the wrong
latency profile, fails on mobile/no-bob, and duplicates the index Obsidian
already holds in memory. Use `bob`'s grammar, not its process.

## 5. Design

### 5a. Trigger grammar (port, do not reinvent)

Port `capture_links.rs` link scanning to JS, reduced to what prompts need:

- Detect the innermost `[[...` containing the caret: `[[` opener, optional
  target, optional `#head` / `#^block` / `##` / `^^` scope markers, optional
  `|alias` tail (caret in alias → no popup, mirroring
  `completion_field`'s alias guard), optional `]]` close (caret past close →
  no popup). Refuse inside code spans — prompts rarely contain backticks, but
  the rule is one function and prevents `[[` in `` `[[x]]` `` surprises.
- Queries: target query for `wikilink_note`, heading query after `#`/`##`,
  block query after `#^`/`^^`. Replacement range = inner span (target through
  query end, excluding `|alias`); `suffix_close` appends `]]`; report
  `cursor_after` like `cursor_after(replacement_len)`.
- `((` stays the task trigger and is out of scope here; if a `((` popup
  exists later it must own `((` exactly as this owns `[[`.

Keep the canonical test vectors next to the implementation (Bob precedent:
`tests/fixtures/task_wikilinks/vectors.json` mirrored in
`031-task-wikilink-rules.js:7-8`). Add `__tests__/link-trigger-vectors.json`
with opener/closer/alias/code-span cases.

### 5b. Index source (client, Bob-ranked)

Primary: Obsidian `app.vault.getMarkdownFiles()` + `app.metadataCache` —
file paths, basenames, frontmatter aliases, headings
(`metadataCache.getFileCache(file).headings`), blocks
(`...blocks` / `getFileCache` block IDs). Synchronous, no subprocess, works
on mobile, respects Obsidian's exclusion list. Debounce 100–150 ms; cache per
vault generation (listen to `metadataCache.on("changed")` / `vault.on(...)`
to invalidate, mirroring the 30 s reusable-scan allowance).

Ranking: port `compare_score_rank` tiers (exact > prefix > word-boundary >
acronym > substring × alias/stem/path) and living-first tiering
(`path_tier`/`tier_order` in `note_catalog`). Do not ship Obsidian fuzzy
order here — capture-box and prompt-box must agree or Bryan learns two
orderings for one vault.

Blocks: Obsidian's block cache is sparser than Bob's `BlockEntry` scan
(preview text). Ship note + heading + alias completion first; blocks
(`#^id`) second, with preview omitted or sourced lazily. This staging is the
only acceptable ranking gap, and it must be called out in the UI ("notes &
headings; blocks next") rather than silently partial.

### 5c. UI: one shared popup, beautiful and boring

New shared module, e.g. `plugins/shared/obsidian-link-suggest.js`
(owned by whichever plugin hosts `attachLogRecall` today —
`bob-navigation-hotkeys` — and imported by `block-id-prompt` and
`bob-ledger-tools`, following the existing `getNavigationLogRecallApi`
cross-plugin pattern in `184-log-recall-band.js:27-44`):

```js
attachObsidianLinkSuggest({ inputEl, textareaEl, app, scope })
→ { detach(), isOpen() }
```

Behavior:

- Popup anchored under the caret (mirror-div measurement for `<input>`;
  same for `<textarea>` with row offset). Max ~8 rows (Bob `RESULT_LIMIT 20`
  is capture-box scale; prompts want 8), living-first grouping with dim
  path + alias/head/block meta, `match_kind`-aware highlight (reuse
  `logRecallHighlight` style: `bob-log-recall-match` span).
- Keyboard: `↑`/`↓` (and `Ctrl+N`/`Ctrl+P` only when log recall has no rows —
  otherwise log recall keeps them; document the split), `Tab`/`Enter` accept,
  `Esc` dismisses popup first, second `Esc` follows the host prompt's
  back-out path (existing Esc ladders in `090-prompt-modals.js`,
  `196-...-modal.js`, `195-rotten-keep.js`). IME composition: no popup
  key handling while `isComposing`. Click fills without committing or moving
  focus (log-recall rule, `docs/log-recall.md`).
- Coexistence contract with `attachLogRecall`: link popup is modal to the
  field while open. Concretely: when `isOpen()`, the recall band ignores
  `↑`/`↓`/`Tab`/`Enter`/`Esc` (it already ignores `Tab`, IME, and chords;
  extend the guard to "a link popup is open"); when closed, keys fall
  through unchanged. Both popups never paint at once — link popup floats at
  caret, recall band stays in its `bandHost` slot.
- Visuals: reuse Bob picker rows (icon + title + dim meta + `kbd` hints in
  footer: `↑↓ navigate · ⏎/⇥ accept · esc dismiss`). Dark/light via existing
  CSS variables; no new palette. Heading rows show `Note › Heading` with `#`
  level dots; block rows show `^id` + preview; alias rows show
  `alias → stem`. Empty query shows recent notes (from `metadataCache`
  recency or last-opened), never a "create note" row (prompts must not create
  notes — capture's create-row semantics do not transfer).
- Accessibility: `role="listbox"`, `aria-activedescendant`, `aria-live`
  polite status (`N results`), same as intention editor host
  (`297cc...paint.js: status role="status"`).

### 5d. Reliability contract

- Never blocks typing: sync trigger check + cached index; no `await` on the
  keystroke path; async heading/block enrichment fills in place.
- Never loses text: accept splices `[targetStart, targetEnd)` → replacement,
  restores caret to `cursor_after`; cancel restores draft (log-recall rule:
  "moving above the first row or pressing Esc restores the draft").
- Never writes the vault: popup only edits the DOM field; host `submit()`
  paths unchanged (`submitPomodoroWorkSummary`,
  `intentionOps*` preview/apply with generation retries).
- Degrades to literal `[[` when: no index, mobile API missing (same defensive
  `require("obsidian")` pattern as `010-load.js`), timeout, or `[[` inside
  code/alias. No error notice — a notice on every failed suggest would be
  worse than no suggest.
- Multi-byte safe: operate on JS string offsets with `Array.from`-style
  care at the splice points (Bob uses byte offsets + `is_char_boundary`;
  JS port must not split surrogates).

## 6. Recommended solution (phased)

**Phase 0 — contract (small, in `bob-cli` docs only).** Document the prompt
`[[` grammar as "client renders of `capture-complete` wikilink contexts"
in `docs/reference/cli/capture-complete.md` + `docs/log-recall.md` surfaces
table: same trigger, same replacement/close/cursor_after semantics, same
`[[`-excludes-recall-phrase rule. No CLI change.

**Phase 1 — shared trigger + popup (the feature).** Add
`shared/obsidian-link-suggest.js` + vectors test + styles; wire to the §1
sentence allowlist (work/lane/schedule/successor-cancel/rotten/intention/
summary/reflection). Note + heading + alias first; blocks behind the same
flag with an honest "blocks next" note if deferred. Coexistence guards with
`attachLogRecall` both directions. Ship behind no flag — but only on the
allowlist, so blast radius is bounded.

**Phase 2 — ranking parity tests.** Cross-check top-8 prompt results against
`bob capture-complete -f json -- '[[q'` for a sampled query list (the same
way `log_recall/vectors.json` keeps Rust/JS/Swift aligned). Any systematic
divergence is a bug in the port, not a difference of opinion.

**Phase 3 (follow-ups, not this bead).** Mac Capture equivalent (Swift,
same grammar, same tests); block-preview enrichment; recent-notes empty-query
source; audit whether `[[`-bearing phrases should enter `bob logs list`
(the recommendation here: exclude, matching today's `work_log` rule).

## 7. Open questions for Bryan

1. Should `[[` in *intentions* (frontmatter) resolve aliases the same way as
   body links? (Recommend yes — same grammar — but frontmatter alias
   display `[[path|alias]]` renders literally on the card until Reading view
   resolves it; confirm that rendering is acceptable.)
2. May prompt `[[` offer archived/hidden notes at the bottom (capture parity),
   or hide them entirely in prompts? (Recommend parity: show dimmed, bottom.)
3. Is a no-create-row rule right for prompts, or should empty-query offer
   "create `[[new]]`"? (Recommend no creation — prompts edit sentences, not
   the vault tree.)

## Sources checked

- `src/native/capture_links.rs` (`completion_field_at`, `note_candidates`,
  `heading_candidates`, `block_candidates`, `aliases_from_frontmatter`,
  `RESULT_LIMIT`, `suffix_close`/`cursor_after`); `src/native/capture_complete/cli.rs:341`
  wikilink precedence + `((` paragraph; `engine.rs:248`
  `wikilink_task` branch; `capture_task_wikilinks.rs` (`completion_field_at`,
  `WikilinkTaskCandidate`); `capture_complete/render.rs:740-888`.
- `docs/log-recall.md` (catalog, `USED BEFORE` band contract, surfaces table,
  inline `work_log` + `[[` exclusion); `docs/completion.md:132` (150 ms vault
  deadline); `docs/reference/json-outputs.md` catalog shape.
- `bob-plugins`: `block-id-prompt/src/090-prompt-modals.js`
  (`BlockIdPromptModal`, `WorkSummaryPromptModal:385`); `bob-navigation-hotkeys/src/`
  `190-summary-modals.js` (`LaneReleaseSummaryModal`), `195-rotten-keep.js`
  (`RottenKeepReasonStage`), `370-picker-schedule-work-log.js`,
  `184-log-recall-band.js` + `183-log-recall-model.js` (`attachLogRecall`),
  `206d-successor-picker-verdict-render.js:321`; `bob-ledger-tools/src/`
  `297cc-plugin-intention-card-editor-paint.js:100-165` (stage input/textarea),
  `297ca-plugin-intention-card-editor-input.js` (caret/paste),
  `297c-plugin-intention-card-editor.js` (ops); `bob-emoji/src/`
  `040-emoji-suggest.js`, `030-emoji-model.js:703` (`emojiFindTrigger`),
  `010-load.js` (defensive `EditorSuggest` import),
  `241k-plugin-bank-actions.js:894-962` (existing `EditorSuggest` precedent).
- `obsidian-api/obsidian.d.ts:4078-4180` (`EditorSuggest`), `4941+`
  (`FuzzySuggestModal`), `9601+` (`SuggestModal`).
- Live probe: `bob capture-complete -c 5 -f json -- '[[sas'` →
  `context: wikilink_note`, `replacement: {start,end}`, `replacement` +
  `cursor_after` + `match_kind` rows (quoted §2b).
- `src/native/intentions/{fields,protocol}.rs`, `capture_work_log.rs`
  (frontmatter ops, Work Log writer) for the YAML-safety constraint.
