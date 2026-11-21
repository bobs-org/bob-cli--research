# Bank row notes from the Category picker: research and recommendation

## Summary

Adding a note affordance to the morning bank walk is a good idea, and the
vault already has somewhere for the note to live. A bank row's tail grammar
(`—` / `--` / `⚑` / `!!` + text) already parses a `note`, `bob bank
list`/`report` already emit it, and the plugin's bank source scanner already
computes a `noteSpan`. So this feature needs no vault-format change, no CLI
change, and no migration: it is a small, card-local editor transaction plus a
little paint.

The plan as stated — a new `<space>` keymap in the category picker that
prompts for a note — should not ship as stated. `Space` is already bound in
exactly that card, in all three card modes, and the binding is load-bearing
for the two-minute filing walk. The rest of the plan (note on the row, stay
on the row) is right, but the key, the modality, and "visually appealing"
all need tightening. Recommended adjustment:

- Bind note to a key categories can never claim (proposed: `.`), not `Space`
  and not any bare letter.
- Make note an inline stage inside the open Category card (same pattern as
  the existing `+` New-category stage): `Enter` saves and returns to the same
  card on the same row, `Esc` returns without writing. Filing still happens
  with the normal keys afterwards.
- Write the note as the canonical inline tail ` — NOTE` in the same single
  editor transaction discipline the card already uses; never tick, never
  advance, never count the row as filed.
- Paint the saved note, don't just store it: dim the `—` separator and render
  the note text muted/italic in Live Preview and Reading view from the
  existing `noteSpan`, following the Work Log / Rotten Log precedent of quiet
  metadata ink rather than a new color.

The remainder of this report traces the mechanism that forces these
conclusions, critiques the plan, and gives a buildable spec.

## What exists today

### 1. Row grammar already has notes

`docs/bank.md` ("Row grammar") and `src/native/bank/grammar.rs`
(`parse_tail`, `parse_row_tail`, `strip_markers_fields_links`) define a row
as a top-level checkbox whose body starts with an amount, with a tail of
`[cat:: key]`, `[acct:: alias]`, wikilinks, `⚑`/`!!`, and a note after the
first `—`, `--`, or flag:

```text
- [x] $13.71 Smashburger [cat:: dining] [acct:: card] [[eat/smashburger|🍽️]] ⚑ — with Kelly ^bank-8f3a2c1d
```

- `payee_end()` cuts the payee at the first ` [`, `[[`, `—`, `--`, `⚑`,
  `!!`.
- `parse_row_tail()` walks the tail, sets `flagged` on `⚑`/`!!`, records
  `note_start` at the first flag or `—`/`--`, and returns `note` stripped of
  markers, fields, and links.
- The existing test `flags_notes_and_ascii_spellings` pins this:
  `- [x] $13.71 Smashburger !! -- with Kelly` parses `flagged=true`,
  `note="with Kelly"`, `payee="Smashburger"`.

Consequences: any ` — <text>` the card writes is round-tripped by bob, shown
in JSON, and preserved by `import`/`ack` (see "Ownership" below). There is no
need for a new field, a child bullet, or a sidecar. Child bullets ("Indented
children are free notes") are legal Markdown but the wrong tool here: they
turn a one-line transaction into a multi-line edit and complicate the
next-waiting finder, which is line-oriented.

### 2. The CLI already surfaces `note`; no CLI work needed

`src/native/bank/model.rs` (`BankRow`) carries `note: Option<String>`,
`flagged: bool`, `category`, `account`, `links`, `id`, and friends; `list`
and `report` return it. The plugin's fixtures
(`plugins/bob-ledger-tools/.../fixtures/bank/list-waiting.json`,
`report-month.json`) confirm the shape the card already consumes. `bob bank
ack` only ticks; `import` only appends ` ^bank-<hex>` to a matched typed row
("Ownership" in `docs/bank.md`: "A match changes only the trailing bank ID:
checkbox, wording, fields, links, notes, existing non-bank IDs, and child
bullets stay byte-identical"). So the note write belongs in the plugin's
editor transaction, exactly where category filing already lives ("The
Category card never writes rows itself: the category it files is Bryan's
edit in his editor"). A note feature that adds a `bob bank note` subcommand
would violate that ownership split and needs no justification: typing the
tail in the editor is already the CLI path, and `docs/cli_rules.md`-style
subcommand sprawl should not be paid for a single-line edit.

### 3. The Category card keymap: `Space` is taken three times over

Three independent sources agree on the current binding:

- `docs/guides/acknowledge-bank-transactions.md`: "a single key files the
  row's category, and the cursor lands on the next waiting row … letter
  picks another category, Space files the row with no category, and Esc
  cancels."
- `docs/bank.md` footer copy (rendered by
  `247-plugin-bank-category-card-ui.js`): `↵ accept · letter choose · Space
  no category · + new category · Esc cancel` (close mode) /
  `Space remove category` (set mode).
- Code, `245-plugin-bank-category-card-model.js`,
  `bankCategoryResolveCardKey()`:

```js
if (key === " ") {
  return { action: "no-category" };
}
```

with `q`/`Escape`/`Ctrl+[` cancel, `+`/`=`/`＋` new-category, `/`
subscription picker (in `247-...-ui.js` `routeCardKey`), arrows/`Ctrl+N`/
`Ctrl+P` move highlight, `Enter`/`Ctrl+Enter` accept. `q` is reserved
against category hotkeys everywhere (`bankCategoryKeyTable` skips `q`;
`docs/bank.md` hotkey rules refuse `hotkey_reserved (q)`).

The `Space` behavior is mode-dependent and every mode matters:

| Mode | `Space` today | Source |
|---|---|---|
| close (waiting row) | tick + strip `[cat::]` ("remove") if present, else tick-only; counts as `no-category` in the walk session | `246-...-write.js` `bankCategoryWritePlan` (`action: "remove"` / `"tick"`), `bankCategorySessionRecord(session, "no-category")` |
| set (`Bank: set category`, correction path) | strip category, no tick (`action: "remove"` / `"noop"`); never advances | same planner with `mode === "set"` |
| restricted (categories unavailable) | acknowledge-only: `␣ acknowledge · esc cancel` | `bankCategoryCardModel` restricted footer |

Rebinding `Space` to "prompt for note" would silently retrain the
highest-frequency key in the walk (every unclassified row ends in `Space`)
into a text-entry detour, break the documented two-minute ritual, and break
muscle memory for corrections. It is the one key in the card that must not
move. This is the plan's single blocking defect.

### 4. The filing walk always advances — except `set`

`248-plugin-bank-category-card-actions.js` (`bankCategoryCommit`):

1. `bankCategoryWritePlan(planInput)` builds character edits for one line
   (status byte + one `[cat::]` insert/replace/remove right after the payee
   span).
2. `bankCategoryApplyEdits` applies them as one whole-line `replaceRange`
   — one CodeMirror transaction, one undo step.
3. Close mode: `bankCategoryNextWaiting({ scan, filedLine: plan.line })`
   finds the next waiting row in document order (wrapping once, never
   leaving the file), moves the editor cursor, hands off
   (`bankWalkHandOffOpenedRow`, `bankCategoryRecordJump` for `Ctrl+O`), and
   calls `modal.setNext(nextContext, progress, lock)` — the card stays open
   on the next row. Only when no waiting rows remain does it show the
   end-of-run summary (`bankCategoryCompleteWalk`).
4. Set mode: `await saved; modal.close()` — no advance, one Notice.

So "without progressing to the next bank row" already has a precedent
spelling: do what `set` does (stay / close), not what `close` does
(advance). A note action must follow the `set` branch shape: re-resolve,
write, repaint the same card, no `bankCategoryNextWaiting`, no session
`filed++`, no progress bump.

### 5. The inline-stage precedent to copy

The `+` New-category stage (`248g-plugin-bank-category-new-stage.js`) is the
pattern for any text entry inside the card:

- `openNewCategoryStage()` opens a staged form in the same modal; letters
  type while staged and never file (`shouldPassNewCategoryKey` routes
  single chars, Backspace, Tab into the inputs).
- `routeCardKey` delegates to `routeNewCategoryKey` while staged; `Esc`
  closes the stage first (returns to the card), `Enter` applies-then-files.
- Dry-run / preview goes through a session object; cancel/ Esc writes
  nothing.

A note stage should reuse this choreography exactly (prefilled input,
`Enter` commits note and returns to card, `Esc` returns without writing),
not invent a second modal, an Obsidian `PromptModal`, or a pre-write
`Notice`. The subscription picker (`/` in `routeCardKey`,
`routeSubscriptionStageKey`) is the second instance of the same staged-modal
discipline.

### 6. Spans for paint already exist; paint does not

The plugin scanner (`241i-plugin-bank-source.js`, `241o-plugin-bank-marks-model.js`)
already tokenizes every row into `payeeSpan`, `category` span, `flagSpan`,
and `noteSpan` (with `flagged`, `note` text). `BankRow.noteSpan` is computed
even though nothing paints it today: `grep` for `noteSpan` consumers outside
the scanner finds no Live Preview decoration, and `styles.css` has
`bob-bank-*` card/section styles but no bank-note rule. In other words the
model anticipated this feature and the view never cashed it in.

Precedent for "quiet metadata ink": Work Log summaries (`*YYYY-MM-DD HH:MM*
entry` under WORK LOG), Rotten Log lines (`🥀 … kept in Next` counted in the
Task Card header tooltip), Cancel Log first-child lines, and the
date/priority/signal-bar marks — all muted, small, non-color-carrying. A bank
note should look like those, not like a category tile or a flag. The `⚑` flag
already means "look into this" (guide: "`⚑` or `!!` flags a row to look
into"); a clarification note ("coffee with Kelly, reimbursable") is not a
flag, so noting must not set `flagged` as a side effect.

## Critique

**Is it a good idea? Yes — with the key changed.** Morning review is exactly
when the "why" is cheapest to capture and most expensive to reconstruct: the
payee string is cryptic (`SQ *CORNERSTORE`, `PAYPAL *EBAY`), the receipt is
in hand or in memory, and the month note is already open. Alternatives
scatter the context: a daily-note line ("$13.71 was lunch with Kelly")
requires a later join by amount/date; a subscription record is for repeats,
not one-offs; flagging (`⚑`) says "suspicious" rather than "explained". An
inline note on the row keeps the explanation where `list`/`report`/JSON and
every future self will read it. The cost is one small editor transaction and
one paint rule — no format, journal, or sync change.

**What is wrong with the plan as written:**

1. **The key is a collision, not a gap.** `Space` files no-category in
   close mode, removes category in set mode, and acknowledges in restricted
   mode. Stealing it breaks the walk's fastest path and contradicts both the
   guide and the card footer. Any fix that keeps `Space` (double-press,
   long-press, `Shift+Space`) adds timing state to a card that already has a
   gesture lock (`BANK_CATEGORY_LOCK_MS = 300`) and an Enter-chord swallow;
   don't.
2. **A bare letter is the next collision.** Category hotkeys live in
   `[a-z0-9]` (case-insensitive — the resolver lowercases), plus built-ins
   `i`/`r`/`t`/`a`. `n`/`e`/`c` for "note/edit/clarify" will eventually
   shadow a real category and create the worst kind of bug: a key that files
   money into the wrong bucket instead of opening an editor. The note key
   must come from the punctuation the category system can never claim.
3. **Modality is underspecified.** "Prompts for a note … without progressing"
   reads like note-only, but the real morning flow is note-then-file ("this
   was Kelly's birthday lunch" → file as `dining`). The spec must say what
   happens to category/tick/progress when the note saves, and what `Enter`
   vs `Esc` mean in the prompt. Otherwise implementers will guess, and half
   the guesses tick or advance.
4. **"Visually appealing" is doing two jobs.** Storage (` — NOTE`) and
   display (how it looks in Live Preview/Reading) are separate decisions.
   The tail text alone is readable in source but gray-on-gray in rendered
   views; without a paint rule the feature will feel unfinished no matter
   how good the keymap is.

## Recommended solution

### Key: `.` (full stop) for note

- Proposal: `.` opens the note stage in both `close` and `set` modes.
  Footer becomes `↵ accept · letter choose · Space no category · . note ·
  + new · Esc cancel` (close) and the `set` analogue with `Space remove
  category`.
- Why `.`: single unshifted key on the home row's doorstep; currently
  `ignore`d by `bankCategoryResolveCardKey`, so zero behavior change for
  existing users; categorically unclaimable (hotkeys are `[a-z0-9]`, `q`
  reserved); mnemonic "dot = annotate this point"; pairs physically with
  `Space` without replacing it. Acceptable substitutes if Bryan dislikes
  the dot: `;` or `'` — same argument, same implementation; pick one and
  document it. Do not ship `n`/`e`/`N`/any letter, `Space`, or a chord that
  needs timing.
- While staged, `shouldPassNoteKey` mirrors `shouldPassNewCategoryKey`:
  printable chars, Backspace/Delete, and Tab go to the input; `Enter`
  commits; `Esc` backs out to the card; `Ctrl+Enter` must not file from
  inside the input.

### Interaction: a note stage, not a prompt modal

1. From an open card on a row, `.` opens the note stage prefilled with the
   row's current `note` (or empty). Header keeps showing amount/payee/date
   so the note has context. The stage shows the existing note verbatim when
   one exists — this is also the edit path for a note written last week.
2. `Enter` commits and returns to the same card on the same row (same
   highlight, same progress `filed of total`). It does not file, tick, or
   advance. The user then files with the normal key or closes with `Esc`.
   This gives note-then-file in two keys and note-and-stay for free.
3. `Esc` in the stage discards the draft and returns to the card; `Esc`
   again closes the card as today. Empty-string commit deletes the note tail
   (one undo restores it); to avoid surprise deletions, an empty commit on a
   row that already has a note should remove the whole ` — NOTE` segment
   and announce "note removed", not leave a bare `—`.
4. Byte discipline, mirroring `bankCategoryWritePlan`:
   - Re-resolve by `^bank-<hex>` when present, else path+line equality
     (`bankCategoryResolveForCommit`); refuse with
     `BANK_CATEGORY_WRITE_REFUSAL` on moved/edited rows.
   - One whole-line `replaceRange`, one undo step, combining with nothing
     else (note commits never bundle a category change — keep the two
     transactions separate so each is undoable).
   - Placement: canonical ` — NOTE` appended after existing tail fields and
     links, before the trailing ` ^bank-<hex>`; replacing in place when a
     note already exists; preserving `⚑`/`!!`, `[cat::]`, `[acct::]`,
     links, and ID bytes. If the row is flagged, keep the flag and write
     `⚑ — NOTE`, never merge the two.
   - Sanitize like a payee: single line, trim, reject `[[`, `[field::`,
     `#task`, `##`, leading `—` runs, and newlines (fold to spaces or
     refuse with the same refusal Notice — prefer fold-to-spaces for
     pasted receipts, refuse nothing silently).
   - Session accounting: do not touch `filed`/`accepted`/`picked`/
     `noCategory`, do not recompute progress, do not call
     `bankCategoryNextWaiting`, do not `recordJump`. Announce
     `Note saved · $13.71 — with Kelly` (or `Note removed`) via the card's
     existing `announce` path so screen-reader and Notice behavior match
     filing.
5. `Bank: set category` gets the same `.` stage for corrections on ticked
   rows. Restricted mode (no categories) keeps `Space` acknowledge-only and
   gains no note key — there is no card model to return to.

### Visual design: store plain, paint quiet

- Storage stays ` — NOTE` (em dash + single spaces), the canonical spelling
  in `docs/bank.md`. Accept `--` on read (grammar already does), always
  write `—`. Never write the note as a child bullet, a `#tag`, a field, or
  bold.
- Paint (plugin, `241o` marks + `styles.css`): in Live Preview and Reading
  view, wrap the separator + note in the row's `noteSpan` as
  `<span class="bob-bank-row-note">`, styled `color: var(--text-muted);
  font-style: italic; font-size: 0.92em`, separator opacity ~0.6. Do not add
  hue (notes are not lane/state), do not bold the amount, do not move the
  note. Flagged rows keep their existing flag paint; note and flag compose
  (`⚑ — note`) rather than competing.
- Card header: when the current row already has a note, show it under the
  payee in the same muted style (read-only preview) so `.` reads as "edit"
  and empty reads as "add". This closes the discoverability loop without a
  tutorial.
- Announce/summary strings reuse `bankCategoryAnnounceText` conventions
  (`Filed …` stays; add `Noted …`).

### Edge cases the implementer must handle (checklist)

- Row already has a note → prefill, `Enter` replaces in place.
- Empty commit on note-less row → no-op, return to card, no Notice.
- Empty commit on noted row → remove segment + preceding space, announce
  removal.
- Note with `^bank-` ID, links, `[cat::]`, `[acct::]`, flag → all preserved;
  duplicate-`[cat::]` rows still refuse as today.
- Pasted multi-line text → fold to one line; overlong input → cap at the
  same width the payee sanitizer tolerates (no new truncation rule).
- Concurrent external edit between open and commit → refusal Notice, stage
  stays open with draft intact (do not close the card on refusal).
- Undo → one `Ctrl+Z` removes the note transaction without touching the
  category/tick transaction before or after it.
- `bob bank list -f json` round-trip: note appears in `note`, `flagged`
  unchanged, `category` unchanged.

### What not to build

- No `bob bank note` CLI: the editor transaction is the writer; the CLI
  already reads. A writer subcommand would duplicate
  `bankCategoryResolveForCommit`'s safety checks in a second place.
- No auto-flag-on-note, no auto-tick-on-note, no note templates, no
  per-category default notes. Each adds a rule Bryan must remember during a
  two-minute walk.
- No child-bullet notes, no `#note` tags (rows must stay `#task`-free or
  they leak into `plan`/`ready`), no new hotkey namespace.

## Alternatives considered

- **`Space` for note, move no-category elsewhere**: rejected. No-category
  is the walk's common case (unclassified rows are normal); hiding it behind
  a new key punishes every session to benefit the rarer note action.
- **Note-and-file combined (one key writes note + files suggestion)**:
  rejected as the default. It saves one keypress but fuses two undo domains
  and forces the note stage to also resolve category intent. The staged
  return-to-card achieves the same flow in two explicit keys with clean
  undo.
- **Note as flag (`⚑ text`)**: rejected. Flag means "look into"; most notes
  mean the opposite ("explained: …"). Conflating them corrupts the `flagged`
  count in `Totals` and the walk's flag surfacing.
- **Note in a child bullet**: rejected (multi-line edit, finder churn, no
  JSON field today).

## Build and verify

- Plugin unit scope (follow existing pure-model test style):
  `bankCategoryResolveCardKey` gains `.` → `{ action: "note" }` with tests
  that every `[a-z0-9]`, `q`, `Space`, `Enter`, `Esc`, `+`, `/` mapping is
  unchanged; write-planner tests for insert/replace/remove of the ` — NOTE`
  segment with ID/links/flag preservation and the duplicate-`cat` refusal.
- Fixture walkthrough: open a month note with waiting rows, file one row,
  `.` on the next, `Enter` a note, assert cursor unmoved, progress
  unchanged, `Esc` closes, `Ctrl+Z` removes only the note; `bob bank list
  -f json` shows the note.
- Docs: one line in `docs/guides/acknowledge-bank-transactions.md` row
  basics ("`.` notes the row and stays"), footer copy in `docs/bank.md` Bank
  walk section, and the `bob-ledger-tools` card footer strings. No
  `mkdocs.yml` or `docs.md` front-door change (per `sase memory` docs rules,
  read `docs.md` before touching those files).

## Recommendation

Ship the note stage on `.` (or `;` if Bryan prefers the finger),
note-only/stay semantics, ` — NOTE` storage, and quiet muted-italic paint
from the existing `noteSpan`. Do not ship `Space`-for-note in any form.
The feature is small, safe, and worth building: it captures the one context
that evaporates fastest, exactly where the money already lives.
