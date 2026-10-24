# Relation card completion, hidden labels & label rename (`mus`)

Research date: 2026-10-24. Request: fix and extend the bob-mac-capture
relation card's label tab-completion (screenshot
`~/tmp/screenshots/20261024_093115.png`), add `<ctrl+n/p>` navigation,
hide/unhide of relation descriptions, show-all + re-enable, vault-wide
rename (card, CLI, Obsidian), and a new `~note:id||<desc>` capture spelling
that creates hidden labels with a warning when it hides an existing one.

## TL;DR

Yes, do this work — but not exactly as specified. The plan is directionally
right and the bug is real, with one adjustment to each bullet:

1. **Tab bug: confirmed, root-caused.** Tab doesn't just "do nothing" — on a
   one-suggestion list `(0+1)%1==0` rewrites the field with the same text and
   *invalidates* the fresh typed row, so the `Inserts …` line vanishes until
   the refetch lands. Second Tab walks a stale list whose responses are then
   dropped by the generation guard. Fix Tab by making it **insert** (macOS
   convention), not cycle; give cycling to `<ctrl+n/p>` **and** Up/Down.
2. **`<ctrl+n/p>`: endorse**, but they are currently swallowed on purpose by
   the shared `isolatedPromptCommand` helper — add card-scoped cases, don't
   change the helper (it serves three prompts).
3. **`<ctrl+d>` to hide: endorse with a scoping change.** In an NSTextField,
   `^D` is Emacs delete-char-forward. Bind hide to the *highlighted
   suggestion row*, not the field; add a visible per-row eye affordance so the
   feature is discoverable without the key.
4. **Show-all + re-enable: make `<ctrl+d>` a toggle** (hidden row highlighted
   + `^D` unhides) plus a persistent `Show hidden (N)` switch. Typing an exact
   hidden name must still offer it flagged — the theme-hide precedent.
5. **Rename: the only primitive that exists today is per-edge relabel.**
   Vault-wide rename needs a new `bob task relabel` verb (fits the `bob task`
   membership rule). Keep rename primarily CLI + Obsidian; the Mac card only
   needs a "rename everywhere" entry point, not its own engine.
6. **`||` syntax: viable and unambiguous** — `|` is forbidden in labels, so
   `||` lexically collides with nothing. Ship `||label` / `||"multi word"`
   with warn-on-hide-of-existing in all three surfaces' output contracts.
7. **Biggest design correction: there is no label registry.** Labels are
   inline free text on `LINKS` lines; the "catalog" is a count-ranked scan.
   Hide state therefore needs a new home. Recommended: a vault-synced
   per-host journal (`.bob/relations/<host>.jsonl`, last-writer-wins fold),
   copied from the theme-preference journal — because *two* suggestion
   pipelines (CLI `capture-complete` for Mac, ledger `relationIndex` for
   Obsidian) must both read it.

Details, evidence, and the recommended build order in §7.

## 1. What I verified and where it lives

| Claim | Evidence |
|---|---|
| Relations contract (grammar, vectors, JSON) | `docs/task-relations.md` §§3–15; capture execution §8, `relation_label` context `suggestions[] {label, count, replacement}` §12 |
| Capture grammar for `~`/`~~` + `\|label` | `docs/capture.md` "Linking tasks with '~' and '~~'"; `docs/reference/capture-syntax.md` `#tilde-link`; guide `docs/guides/link-related-tasks.md` |
| `~` scanner: label runs to whitespace, `\|`-leading label fails validation | `src/native/capture_language/relations.rs` `scan_relation_block_id` (~line 380–490): unquoted label scanned to whitespace, then `normalize_relation_label` rejects `\|…` as `ForbiddenCharacter` |
| Label rules (1–40 chars, forbidden set incl. `\|`) | `src/native/task_relations/label.rs` |
| Suggestion catalog: count-desc scan, case-insensitive dedupe | `src/native/capture_complete/candidates.rs` `task_links_catalog` + `relation_label_suggestions` (~line 1403–1650) |
| Suggestion ranking: empty query keeps count order; else prefix-then-substring | `src/native/capture_complete/support.rs` `rank()`; typed row inserted at index 0 |
| Mac relation card view (horizontal chips, no selection highlight) | `Sources/BobMacCapture/CapturePanelView.swift` `RelationLabelPromptCard` (~line 1760–1860 in `BobMacCapture/`) |
| Mac card state machine (freshness guards, pending-submit) | `Sources/BobMacCapture/CapturePanelModel.swift` `CaptureRelationLabelPromptState`, `cycleRelationLabelSuggestion`, `fetch/applyRelationLabelSuggestions` (~lines 185–230, 6444–6900) |
| Tab/Shift-Tab cycle; `^N/^P`/arrows swallowed by shared helper | `Sources/BobMacCapture/CaptureKeyCommandRouter.swift` `relationLabelPromptCommand` (~line 519) + `isolatedPromptCommand` (~line 654); shared by task-ID, Pomodoro-name, relation-label prompts |
| Obsidian relation-label stage: filterable list, fuzzy match, arrows, inline validation — no Tab cycling | `plugins/bob-navigation-hotkeys/src/426-picker-relation-stage.js` `showRelationLabelStage`, `getRelationLabelPreviewItems` (`bob-plugins` linked repo) |
| Live Obsidian suggestions from ledger index | `api.relationIndex.labelSuggestions` (`docs/task-relations.md` §11; `bob-ledger-tools` `145-relation-index-model.js`) |
| Per-edge relabel exists; vault-wide rename does not | `docs/task-relations.md` §4 ("re-linking … relabels in place"), LG4; `bob task` has only `archive/move/reconcile/reroll` |
| Hide precedent: hide removes from Recent only, never unhides on use, per-host journal | memory `decisions:theme-hide-is-recent-only`, `decisions:theme-prefs-live-in-per-host-journal`; `src/native/pomodoro_themes/` (`write.rs` `run_hide`/`run_unhide`, `journal.rs`) |
| CLI rules constraining new commands | memory `cli_rules.md`: `bob task <verb>` = vault-wide task-line rewrites; never add under `bob capture`; `-h` excellence; hidden aliases, never renames |
| Prior art: unquoted multi-word guide example is wrong; labels must be quoted | `sase/repos/research/202610/task_relation_labels.md` §"Gotcha" |

## 2. The Tab bug, precisely

The screenshot shows the steady state, not a freeze: field `inspired by`,
one chip `inspired by`, `Inserts |"inspired by"`. Two compounding defects in
`CapturePanelModel.cycleRelationLabelSuggestion(by:)`:

1. **Cycle mutates the query it cycles over.** Tab copies the suggestion's
   label into `authoredLabel`, clears `suggestionAuthoredLabel`, and fires an
   async `capture-complete` probe. Consequences:
   - *One suggestion:* `(0+1)%1==0` — the field is rewritten with identical
     text, freshness is voided, and the `Inserts …` line disappears until the
     refetch lands. A second Tab before that walks the *stale* list and its
     response is then dropped by the generation + `authoredLabel` guard in
     `applyRelationLabelSuggestions`. Net: "completes the first entry, then
     nothing happens." The "fast enough `<tab>` hits nth entry" observation is
     the stale-list walk winning a race with the refetch.
   - *Several suggestions:* each Tab re-prefix-filters the list (`rank()`:
     prefix matches, then substring), so the list shrinks/reorders under the
     user's fingers and `selectedSuggestionIndex` resets to 0.
2. **Cycling is invisible.** `selectedSuggestionIndex` is never rendered —
   every chip is `.bordered` with no highlight — so even a working cycle gives
   no feedback. The card also never announces wraps or counts.

The freshness protocol itself (`suggestionAuthoredLabel`, `pendingSubmit`,
in-flight generation guards — the `bob-cli-al` comments) is correct and
load-bearing: submit can never commit a candidate fetched for a previous
label. Keep it. The bug is that *navigation* was built on top of *editing*.

Fix shape (see §7): separate **highlight** (moves with `^N/^P`/arrows/Tab…
  no — Tab inserts) from **field text** (only changes on explicit accept or
typing). Highlight moves must never fire a probe or void freshness.

## 3. Critique and adjustments, requirement by requirement

### 3a. `<ctrl+n/p>` navigation — accept, widen slightly

`^N/^P` is the right Emacs-consistent choice and matches the pickers
(`pickerCommand` already maps `^N/^P/^J/^K` to row movement). But today
`isolatedPromptCommand` maps `^N/^P` to `.consumeKey` for *all three*
prompts that share it. Add explicit `case KeyCode.n/p` handling in
`relationLabelPromptCommand` *before* the shared fallthrough; do not touch
the helper, or task-ID and Pomodoro-name prompts change behavior silently.
Also bind Up/Down to the same movement — they are currently consumed too,
and arrows are what trackpad users will try first.

### 3b. Hide via `<ctrl+d>` — accept, rescope to the row

Two problems with a bare field-scoped `^D`:

- macOS reserves `^D` in text fields (delete character forward). Stealing it
  inside the label field breaks muscle memory and fights the field's native
  binding.
- "Hide *what*?" is ambiguous while typing a half-formed label.

Recommended: `^D` acts on the **highlighted suggestion row**. No highlight +
  non-empty field = `^D` does nothing (or a calm hint). Every row also gets a
visible eye affordance on hover/selection so the feature exists for users who
never read footer hints. This mirrors the chips' existing hover-`×` unlink
pattern (`docs/task-relations.md` §10), so it feels native, not bolted on.

### 3c. Show-all + re-enable — accept, make hide a toggle

Hiding must never strand a label. Recommended trio:

- A persistent footer switch, `Show hidden (N)`, clickable and keyboard
  reachable, that reveals hidden rows rendered distinctly (dimmed + eye-closed
  + `hidden` tag).
- `^D` on a highlighted hidden row **unhides** it. Toggle symmetry means one
  keymap to learn and no separate "re-enable key."
- Typing a hidden label's exact text still surfaces it, flagged hidden (copy
  the theme-hide rule: *using a hidden name never unhides it*). This is the
  escape hatch if the switch is ever missed.

### 3d. Vault-wide rename — accept, but relocate most of it

Today rename does not exist: Links-stage `⇧↵` on a CURRENT row relabels one
edge (LG4); capture re-add with a new label relabels one edge (§4). A rename
*description* operation is: for every `LINKS` entry whose normalized label
equals Old (case-insensitive, matching the catalog dedupe), rewrite the label
to New in place (order kept, LW4 semantics per edge); mirrors converge via the
existing `reconcile_relation_lines` pass. Adjustments:

- **New verb `bob task relabel <old> <new>`** with `--dry-run`, human `🪢`
  rows plus JSON (`relation_updates[]`-style rows), and `--include-hidden`
  semantics for hidden labels (rename carries the hidden flag to the new
  normalized name; renaming *onto* an existing different label is refused with
  a teaching error — same "first wins" spirit as LW9/LK8).
- **Obsidian gets the same operation** (a rename action on the relation-label
  stage), because per-edge relabel already lives there and users will look
  for rename beside it.
- **Mac card and CLI capture do NOT get a rename engine.** The card gets a
  "Rename everywhere…" affordance that hands off (runs the verb / opens the
  Obsidian stage). Three rename engines will drift; the planner already exists
  once in Rust with a JS twin pinned by shared vectors (`docs/task-relations.md`
  §8) — reuse that pattern, don't triple it.
- Case-only renames (`follow-up of` → `Follow-up Of`) must work: compare on
  the folded form, replace with the authored form.

### 3e. `~note:id||<desc>` hidden-at-birth — accept, fix the spelling note

(Note: the request writes `~file:id`; the actual grammar is
`~note:block-id` — keep the proposal in the real spelling:
`~note:block-id||label`, `~note:block-id||"multi word"`.)

Why it is safe: `|` is a forbidden label character, so today
`~note:id||desc` scans the label as `|desc` and fails with
`invalid_relation` (ForbiddenCharacter). The `||` prefix collides with no
valid label — reclaiming it is purely additive. Quoted form needs the same
treatment (`||"multi word"`: today the second `|` poisons the scan the same
way). `relation_grammar` stays the `~`-byte rule, so drafts without `~` are
still byte-identical (LP18). Adjustments:

- **Hide-on-existing warns, never refuses.** Hiding an existing visible label
  via capture is supported (per the request) but must be loud: CLI prints a
  `🪢 … now hidden` row and a JSON `label_hidden[]`-style entry; the Mac card
  preview gains a banner ("`inspired by` is visible — capturing will hide it
  everywhere"); Obsidian shows the notice beside the preview. Refusing would
  strand one-off flows; staying silent would cause "where did my label go"
  mysteries.
- **Hide is a property of the label, not the edge.** `||` on capture sets the
  journal flag; the edge itself is authored normally. Unhiding later must not
  require touching any task.
- **One-off relationships need no new syntax to *use*.** The request frames
  hide as "support for temporary/one-off relationships" — correct, with the
  emphasis that the one-off label stays a normal label, just unlisted. Typing
  it still works everywhere (theme-hide rule again).

## 4. Where hidden state should live

Options considered:

| Store | Verdict |
|---|---|
| Inline marker on `LINKS` entries | Reject. Pollutes the §3 grammar, breaks LK vectors, and per-edge flags can't express "this description is hidden" (a label is shared across edges). |
| `~/.config/bob/config.yml` knob | Reject. Config is per-machine and hand-edited; hide is per-label data that two suggestion engines must read identically on every host. |
| Vault-synced per-host journal (themes model) | **Recommend.** `.bob/relations/<host>.jsonl`, append-only `{label, hidden, at}` events, last-writer-wins fold per folded label — exactly `decisions:theme-prefs-live-in-per-host-journal`. Vault-synced so hide follows Bryan across athena/apollo/mac; per-host files so concurrent hides never conflict-merge. |
| Single vault-global file | Runner-up. Simpler reads, but concurrent appends from two hosts conflict where per-host files don't. The themes system already solved this; copy it. |

Consequences of the recommendation: `capture-complete` filters hidden labels
post-rank (filter after ranking, per the theme decision's "Cost" note — never
drop catalog rows), and `api.relationIndex.labelSuggestions` gains the same
filter from the same journal, so Mac and Obsidian agree. `bob task relabel`
transfers the flag. Reconcile never touches the journal (it owns mirrors, not
opinions — §7 of the contract).

## 5. Is this a good idea? What would I change?

**Yes — with the adjustments above, this is the right next step for
relations.** Labels are the only free-text namespace in the relations system
with no curation tools: no completion that works, no way to retire a typo'd
description, no way to rename one. Every week of use mints more near-duplicate
descriptions (`follow up`, `follow-up`, `follow-up of`), and the suggestion
list degrades linearly. Hide + rename are curation for that namespace, and the
Tab fix is owed regardless.

What I would affirmatively *not* do:

- **Don't build a label registry/CRUD UI.** Labels must stay free text
  (contract §3.2). A registry turns every capture into a schema migration.
  Hide + rename + counts are the whole curation surface.
- **Don't put hide/show/rename keymaps on the *field*.** Field keys are
  macOS's (Emacs bindings, Tab-to-next-field). The card's list gets the keys;
  the field keeps them. This is also why Tab must insert: in every native
  completion menu on macOS, Tab accepts.
- **Don't mirror hidden labels into chips or mirrors.** Hide affects
  *suggestions only* — stored edges, chips, counts, and Stats-equivalents are
  untouched (theme-hide-is-recent-only, applied to labels).
- **Don't auto-unhide on use, don't delete-on-hide.** Both rejected for themes
  for reasons that transfer verbatim (history preservation, fighting the
  user's gesture).

Open questions for Bryan: (1) per-host vs vault-global hide — I recommend
per-host files; if you always want hides everywhere instantly, say so and take
the single-file runner-up. (2) Should `bob task relabel` refuse case-only
collisions or fold them? (3) Is `^D`-on-row acceptable, or do you want hide on
a different key entirely (e.g. `^H`, accepting the Emacs-backspace tradeoff)?

## 6. Beauty and feel (lead design)

The current card is a sentence + field + horizontal chip strip + two buttons.
Recommended card, top to bottom:

1. `🪢 Relation` header (keep) + live sentence `S — label → T` (keep, it's
   the best element on the card).
2. Field (keep), placeholder `follow-up of` (keep).
3. **Vertical suggestion list** replacing the horizontal chip strip: one row
   per label, `label · count` + eye state; highlighted row fills with the
   accent; hidden rows (when shown) dim with `hidden` tag. Vertical lists are
   what `^N/^P` hands expect, and they scale past a dozen labels where chips
   wrap into soup.
4. `Inserts …` line (keep) — it is the commit preview; keep the stale-hiding
   discipline exactly as is.
5. Optional amber banner slot for the hide-on-existing warning (new).
6. Footer hints, updated: `tab insert · ^N/^P move · ^D hide · esc back`.
   Keep `esc back to picker` (existing contract); add the two new hints only.

Motion: highlight moves instantly, no animation; list updates never steal
field focus; empty-state keeps today's calm hint. No new palette — reuse
`CaptureEditorPalette` relation-sigil color and the neutral row accent, per
the chips' "no new palette" rule (§10).

## 7. Recommended solution and build order

**Phase 1 — fix completion (Mac only, no contract change).**
Separate highlight from field text; Tab inserts highlighted (or typed) row;
`^N/^P`/Up/Down move highlight without probing; render highlight; keep the
freshness protocol untouched. Vectors: single-suggestion Tab inserts;
rapid-Tab stress; stale-response drop; Esc/empty-submit behavior unchanged
(LG3). This alone closes the reported bug.

**Phase 2 — hidden labels (contract + CLI + both clients).**
Grammar `||` (LP/LX vectors), journal format + fold, `capture-complete`
filter + `show_hidden` escape, ledger `labelSuggestions` filter, hide-related
JSON/human outputs, warn-on-hide-of-existing in all three surfaces, decisions
record (immutable; supersedes nothing — new ground). Card gains eye toggles,
`Show hidden (N)`, `^D`-on-row.

**Phase 3 — rename (`bob task relabel` + Obsidian action).**
Vault-wide rewrite reusing the §8 planner, `--dry-run`, JSON, teaching errors
on collisions; Obsidian rename beside per-edge relabel; Mac card handoff only.
Conformance vectors in the LW/LR style.

**Phase 4 — docs.** `docs/task-relations.md` (labels + hide + rename
vectors), `docs/capture.md` linking section, `docs/reference/capture-syntax.md`
`#tilde-link`, guide `link-related-tasks.md` (also fixing its unquoted-label
examples per the prior finding), plugin relation docs, Mac Capture help.

Non-goals: label registry UI, auto-decay of unused labels, inverse-phrase
extension, touching mirrors/chips/Stats for hidden labels.

## Sources

- Code read (no behavior changed): `src/native/capture_language/relations.rs`,
  `src/native/task_relations/label.rs`, `src/native/capture_complete/`
  (`candidates.rs`, `support.rs`, `engine.rs`, `render.rs`, `shell.rs`),
  `src/native/capture_complete/tests/relations.rs`,
  `src/native/pomodoro_themes/` (`write.rs`, `journal.rs`),
  `Sources/{BobMacCapture,CaptureCore}/` (`CapturePanelView.swift`
  `RelationLabelPromptCard`, `CapturePanelModel.swift` relation-label block,
  `CaptureKeyCommandRouter.swift`, `CaptureModels.swift`
  `CaptureCompletionCandidate`), `plugins/bob-navigation-hotkeys/src/`
  (`426-picker-relation-stage.js`, `427-relation-stage-plugin.js`),
  `plugins/bob-ledger-tools/src/` (`145-relation-index-model.js`,
  `171-relation-index-lifecycle.js`).
- Docs: `docs/task-relations.md`, `docs/capture.md`,
  `docs/reference/capture-syntax.md`, `docs/guides/link-related-tasks.md`,
  `docs/reference/plugins/task-relations.md`.
- Memory: `decisions:theme-hide-is-recent-only`,
  `decisions:theme-prefs-live-in-per-host-journal`, `cli_rules.md`,
  `sase/repos/research/202610/task_relation_labels.md`.
- Screenshot: `~/tmp/screenshots/20261024_093115.png` (viewed; shows the
  one-suggestion steady state described in §2).
