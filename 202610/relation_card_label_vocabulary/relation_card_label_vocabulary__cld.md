# Relation card: reliable completion, hidden relations, global rename, and `||` one-offs

> **Request.** Bob Mac Capture's relation card Tab completion fills in one relation and then
> stops responding. Fix it and improve the card. Add Ctrl-N/P navigation; a way to
> hide relation descriptions (maybe Ctrl-D) for one-off relationships; a key that shows
> hidden ones and a way to unhide them; a reliable rename from the card, the CLI, and
> Obsidian that updates every task; and a `~file:id||<desc>` capture syntax that creates a
> description already hidden, with a clear warning when it would hide an existing one.
> Critique the plan, adjust requirements where justified, and recommend a solution.

Checked on **Saturday, October 24, 2026** against bob-cli `8628ce2f`, bob-mac-capture
`72cd721`, bob-plugins `3a7368a`, the screenshot `~/tmp/screenshots/20261024_093115.png`,
read-only `bob capture-complete` / `bob capture-parse` runs against `~/bob`, and a
read-only grep of the vault. I did not compile Swift or run the Mac app.

## Bottom line

1. **This is a design flaw, not a typo.** The card keeps one string that is both what
   you typed and the query sent to bob. Tab writes the chosen suggestion into that
   string, and bob filters the next list by it. After one Tab, bob returns a single row
   (the label just chosen), so the next Tab cycles a one-row list and nothing happens.
   Fast Tabs reach the "nth" label only because each refetch takes about **0.85 s** on
   apollo, and the old list stays on screen meanwhile. Two smaller bugs: the first Tab
   skips the top suggestion, and the selected chip is never highlighted.
2. **Fix: keep the query separate from the selection.** The field holds what you typed.
   A vertical list holds the rows. Ctrl-N/P (and ↓/↑, Tab/⇧Tab) move a highlight that
   never touches the field. Return inserts the highlighted row. The Obsidian relation field
   and every Mac picker already work this way. This step needs no bob change and should
   ship first, on its own.
3. **The rest of the plan is sound, but reuse the theme model instead of inventing a new
   one.** bob already has hide, unhide, and rename for Pomodoro themes: a per-host journal,
   a rule that hiding affects suggestions only, and bob as the only writer. Copy it:
   `bob relations list|hide|unhide|rename`, events in `.bob/relations/<host>.jsonl`, and
   Mac and Obsidian calling bob.
4. **Adjustments that matter most** (§3):
   - Say **hide**, never "disable": `disabled_reason` already means "cannot be inserted".
   - Say **relation label** in contracts, not "description": that word means task text in
     bob.
   - A hidden label stays valid, still renders, and is not unhidden by using it.
   - `||` on an existing label **warns but does not block**.
   - Rename is a previewed, verified, one-commit rewrite that includes `done/`, as an
     explicit exception to "relation writes never touch `done/`".
5. **Size the work to usage.** The vault holds 6 labelled links across 3 labels:
   `inspired by` ×3, `implements` ×2, and `duplicate of` ×1. Three days ago you cancelled
   epic `bob-cli-am` for "too little value… low usage".
   - Ship the fix now.
   - Hide and `||` are worth building next, because they keep the label list clean before
     it fills with one-offs.
   - Rename is the largest piece and the least urgent: build it last, as one
     `bob relations rename` implementation that the card and Obsidian call.

## 1. What is broken today

### 1.1 Tab rewrites the query, so the list collapses

The card keeps one string, `authoredLabel`, as both the field's text and the query sent to
bob.

- `cycleRelationLabelSuggestion` (bob-mac-capture
  `Sources/BobMacCapture/CapturePanelModel.swift:6631`) sets
  `prompt.authoredLabel = label` to the chosen suggestion (line 6641). It then calls
  `fetchRelationLabelSuggestions()`.
- That fetch (line 6846) inserts `|"<authoredLabel>` into a copy of the draft and asks
  `bob capture-complete` for the `relation_label` context.
- bob's `relation_label_suggestions` (bob-cli
  `src/native/capture_complete/candidates.rs:1592`) ranks the catalog by that query: prefix
  matches first, then substring matches (`support.rs:18`). It then drops the row equal to
  the query and puts one `typed` row in its place (line 1641).

Reproduced read-only against the live vault:

```text
query ""             → inspired by · 3   implements · 2   duplicate of · 1
query "inspired by"  → [typed] inspired by                (one row, no count)
```

After the first Tab the list has one row, so `(index + 1) % 1` keeps selecting that row.
The screenshot shows exactly this state:

- The field reads `inspired by`.
- The only chip is `inspired by`, with no `· 3`, because it is the typed row.
- The caption still says `Tab cycles suggestions`.

### 1.2 Fast Tabs reach the "nth" row because each fetch is slow

Every keystroke and every Tab starts a new `bob capture-complete` process:

1. It calls `capture_dependency_tasks::discover` (`candidates.rs:1596`), which walks all
   6,472 notes and computes block-ID suggestions for every task.
2. It then reads every note that has tasks a second time to collect labels.

On apollo that takes **0.85 s warm and 2.5 s cold** per call. Until a response lands, the
old list stays on screen, so quick Tabs step through indexes 1, 2, 3… of that stale list.
When the last response arrives, the list collapses to the typed row.

`applyRelationLabelSuggestions` (line 6942) also keeps the numeric
`selectedSuggestionIndex` across lists. It resets the index to 0 only when it is out of
range (line 6962), so the index can point at a different row than the label in the field.

### 1.3 Smaller defects in the same card

- **Off-by-one.** `selectedSuggestionIndex` starts at 0 and the first Tab adds 1. An empty
  field has no typed row, so the first Tab skips the most-used label. With today's counts
  it selects `implements`, not `inspired by`. At 09:31, `implements` and `inspired by`
  were probably tied at 2, and ties sort alphabetically, so index 1 was `inspired by`. That
  explains why it looked as if Tab picked the first row.
- **No highlight.** The chips are identical `.bordered` buttons in a horizontal
  `ScrollView` (`CapturePanelView.swift:1802`). Nothing marks the selected one.
- **Ctrl-N/P and ↓/↑ do nothing.** The card routes keys through `isolatedPromptCommand`
  (`CaptureKeyCommandRouter.swift:654`), which swallows arrows and Ctrl-N/P
  (lines 672–675). Everywhere else in the app (completion list, stash, template shelf),
  Down/Ctrl-N and Up/Ctrl-P move a selection.
- **The test cannot catch the bug.** `testRelationCardTabCyclesSuggestions`
  (`Tests/BobMacCaptureTests/CaptureRelationPanelTests.swift:121`) installs a fixed list
  with no process client, so the refetch that collapses the list never runs.

### 1.4 Obsidian already works this way

The Obsidian relation field (bob-plugins
`plugins/bob-navigation-hotkeys/src/426-picker-relation-stage.js:624`) is a vertical
list:

- Row 0 is "Plain link (no relation)" or the typed label.
- Up to 12 suggestions follow, each with `used N×`.
- ↓/↑ and Ctrl+N/P move a highlight (`200-filtered-picker-modals.js:192`).
- The input keeps the query, and ↵ commits the highlighted row.

The Mac card is the only surface that works differently.

## 2. Is this a good idea?

### 2.1 What is worth building

- **The fix: yes, now.** The card is where most labels get entered, and its suggestions
  are what keep one meaning to one spelling. Without working suggestions, variants like
  `inspired by`, `inspired-by`, and `inspiration` creep in.
- **Hide: yes.** One-off labels such as "prompted the purchase of" are what you describe.
  Without hide, every one-off is suggested forever and the list fills with noise. Hide is
  cheap because bob already has the pieces: the theme journal fold, the sync lock, and the
  vault allowlist.
- **`||`: yes, and it is small.** `|` is already forbidden in labels. Today
  `bob capture-parse 'Buy SSD ~sase:x||oneoff'` reports `invalid_relation` ("relation label
  '|oneoff' contains a forbidden character"), so claiming `||` breaks nothing. It also
  saves a hide step for labels you already know are one-offs.
- **Rename: yes, but last.** Rename merges synonyms, which is the long-term cleanup
  problem. With 3 labels and 6 links, though, a hand edit plus `bob task reconcile` takes a
  minute. Rename is also by far the largest piece: a vault-wide transaction with sync,
  verification, a commit, and mirror rewrites.

### 2.2 Usage check

Today the vault has 8 LINKS lines (excluding `_conflicts/`), holding 9 entries:

- 6 of the 9 entries have labels.
- There are 3 distinct labels.

On October 21, the `bob-cli-am` review counted 2 unlabelled relations, so usage has roughly
tripled in three days, and all of the growth is labelled. That supports investing in
labels. `bob-cli-am`'s close reason still argues against one large epic: split the work
into phases that each stand alone (§6).

### 2.3 Alternatives I considered and rejected

| Alternative | Why not |
| --- | --- |
| **Auto-hide one-offs** (hide labels used once and older than N days) | It needs no effort, but it produces the "why did my label vanish?" confusion. Bob's decision records prefer explicit user gestures (`unblocked-tasks-are-offered`; "nothing decays silently"). Keep ranking smart and keep row caps (5 rows for an empty query, 12 for a typed one, like themes PT7), but make hiding a gesture. |
| **Store the flag on the LINKS entry** | Hiding belongs to the label vocabulary, not to one link. It would also add a second grammar to lines that are meant to read as plain English. |
| **`relations.hidden_labels` in `config.yml`** | chezmoi manages that file, so changes the Mac app wrote there would be overwritten by the next chezmoi apply. |
| **Machine-local state** | Hiding on the Mac would never reach Obsidian on apollo. Themes rejected this for the same reason. |
| **Rename as a journal alias** (show OLD as NEW, leave the bytes) | LINKS lines must read as English without plugins. Themes rejected aliases for the same reason. |
| **Tab completes the field, shell-style** | That is today's bug: completing rewrites the query, so a second Tab has nothing left to complete. |
| **Field mirrors the highlighted row** (vim/zsh menu-complete) | It needs separate base-query and preview state, plus undo and IME handling, and Obsidian does not do it. The live sentence already shows the highlighted label. |
| **Make `||` on an existing label need a second Return** | Hiding is cheap to undo and loses nothing. A confirmation step only slows down the rare case where you mean it. |

## 3. Requirement adjustments

**A1. Call it "hide", never "disable".** The capture contract already uses
`disabled_reason` for rows that *cannot* be inserted, and a hidden label can still be
inserted. UI words: **Hide**, **Unhide**, **Show hidden**.

**A2. Contracts and code say "relation label"; the UI says "relation".** In bob,
"description" means task text (`mint_block_id(description)`). The card and Obsidian
already say "Link with a relation".

**A3. Hiding changes suggestions only**, as for themes (PT9). A hidden label:

- still appears on chips and LINKED FROM mirrors;
- still counts in `bob relations list -a`;
- is still accepted when typed;
- is **not unhidden by using it**.

If you type a hidden label exactly, its row is marked `hidden`, so you can tell it
already exists.

**A4. Tab moves the highlight; it never completes.** Tab/⇧Tab work like Ctrl-N/P and
↓/↑. Navigation never changes the field, so the list never collapses.

**A5. Ctrl-D acts on the highlighted row, and the footer always says what it will do.**

- On an existing relation, it hides or unhides it immediately. The row stays in place,
  greyed out, and pressing Ctrl-D again undoes it.
- On the row you are about to insert, it toggles **one-off**, which inserts `||label`.

Typing `|` into the field also toggles one-off, so typing `~note:id||` in one go does
what you expect.

**A6. Ctrl-H shows hidden relations** (matching `bob themes list -H`). A row reading
`◌ 2 hidden · ⌃H` makes this easy to discover.

**A7. `||` on an existing visible label warns but does not block.** The card footer, the
preview row, and the success notification all say it also hides “inspired by”
(3 links) from suggestions.

**A8. Rename rewrites the vault, not just the card.** It:

- shows a preview first (`--dry-run`);
- refuses to merge into an existing label until you confirm;
- rewrites both LINKS labels and LINKED FROM mirrors;
- includes `done/`;
- verifies the result and lands as one commit you can `git revert`.

Touching `done/` breaks contract guarantee LR7 ("no relation write touches `done/`"). The
exception is justified because this is maintenance you start yourself, like
`bob themes rename` rewriting past daily notes. If rename skipped `done/`, OLD would stay in
the catalog because archived links still count.

**A9. Label suggestions must be fast.** The per-keystroke 0.85 s fetch has to go (§4.8).

**A10. Prevent case drift.** If the typed label matches an existing label ignoring case,
insert the existing spelling (`Inspired By` → `inspired by`). Preventing variants is
cheaper than renaming them later.

## 4. Design

### 4.1 Model

```text
catalog(key)  = derived from every LINKS entry in the vault: count, display spelling   ← bob scans
prefs(key)    = fold of .bob/relations/*.jsonl: hidden, renamed_to                     ← bob writes
suggestions   = catalog − hidden (unless "show hidden"); exact, prefix, substring; count desc, name
```

- **Key:** the label after collapsing whitespace and lowercasing. Suggestions already
  dedupe this way.
- **Display spelling:** today it is the first spelling seen. Prefer the most common one,
  with ties going to the first seen.
- **Journal events:** these mirror `pomodoro_themes::journal::serialize_event`:

```json
{"v":1,"ts":"2026-10-24T09:41:07-04:00","host":"mac","kind":"relation_label.hide","key":"prompted the purchase of","name":"prompted the purchase of","via":"bob-mac-capture"}
{"v":1,"ts":"…","host":"apollo","kind":"relation_label.unhide","key":"implements","name":"implements","via":"bob-cli"}
{"v":1,"ts":"…","host":"apollo","kind":"relation_label.rename","key":"inspired by","name":"inspired by","to_key":"prompted by","to_name":"prompted by","via":"bob-cli"}
```

- **Fold:** the same rules as themes PT4:
  - Read every `*.jsonl` file and skip malformed lines with a bounded warning.
  - Sort by `(ts, host, line)`; the last writer wins per key.
  - A rename moves the hidden state to the new key unless that key already has its own.
- **Vault allowlist:** add `!/.bob/relations/*.jsonl` to `.gitignore` and a
  `merge=union` rule in `.gitattributes`, as for themes.
- **Engineering:** turn `pomodoro_themes::journal` into a shared preferences-journal
  module keyed by namespace (`themes`, `relations`) rather than copying it.

### 4.2 The card: interaction

The card keeps two separate pieces of state:

- `query` is the field's text.
- `highlight` is the highlighted row, stored by **label key, not index**.

Because the highlight is stored by key, it survives list refreshes. If its key disappears,
it falls back to row 0.

The rows, top to bottom:

1. Row 0 is **Plain link — no relation** when the field is empty. Otherwise it is the
   **typed row**:
   - `✦ new` when no existing label matches;
   - the existing label, with its count and `hidden` flag, when the query matches one
     exactly.
2. Matching visible labels follow, ranked.
3. Last is a disclosure row, `◌ N hidden · ⌃H`. Once you press Ctrl-H it becomes a
   **Hidden** section listing the hidden labels.

Typing moves the highlight back to row 0. Existing-label rows insert immediately, because
their replacement text does not depend on the query. Only row 0 waits for bob's fresh
typed row, using the existing `pendingSubmit` guard from bob-cli-al.

Keys (the Obsidian relation field gets the identical set):

| Key | Action |
| --- | --- |
| ↓ · Ctrl-N · Tab | Highlight the next row (wraps) |
| ↑ · Ctrl-P · ⇧Tab | Highlight the previous row (wraps) |
| Return | Insert the highlighted row (row 0 = the typed text, or a plain link when the field is empty) |
| Ctrl-D | **Existing row:** hide or unhide now, keeping the row in place greyed out; Ctrl-D again undoes. **Typed row:** toggle one-off (`||`). **Plain-link row:** beep |
| `\|` | Toggle one-off; the character never enters the field |
| Ctrl-H | Show or hide the hidden relations |
| Ctrl-R | Rename the highlighted relation: preview, then ↩ to apply |
| Escape · Ctrl-[ | Leave rename mode first; otherwise leave the card unchanged (back to the picker or the editor, as today) |

In macOS text fields, Ctrl-D (delete forward) and Ctrl-H (delete backward) are Emacs
editing keys. Giving them up in this one-line field is acceptable, since fn-Delete and
Backspace still work. The capture editor already overrides Ctrl-A, Ctrl-E, Ctrl-U, and
Ctrl-T. Ctrl-R has no default text binding.

Hide and unhide from the card run
`bob relations hide|unhide LABEL --via bob-mac-capture -f json`. If the call fails, the
row reverts and bob's message appears inline.

Rename from the card works like this:

- While you type the new name, it runs `bob relations rename OLD NEW -d -f json`, waiting
  for a pause in typing.
- Return runs the same command without `-d`. The row shows a spinner, and Insert is
  disabled until rename finishes.
- On success the list reloads, and if the field held OLD it now holds NEW.

### 4.3 The card: what it looks like

These are the default view (A), a highlighted row (B), a new label marked one-off (C),
one-off on an existing label (D), a just-hidden row (E), the Hidden section (F), and
rename mode (G).

```text
A. Opened, empty field
╭─ 🪢 Link with a relation ──────────────────────────────────────────────╮
│  “Buy new SSD for athena!”  ─────────────▶  “What was athena doing…”  │
│ ┌───────────────────────────────────────────────────────────────────┐ │
│ │ inspired by, implements, …                                        │ │
│ └───────────────────────────────────────────────────────────────────┘ │
│ ▌ ⌁  Plain link — no relation                                         │
│      inspired by                                            3 links   │
│      implements                                             2 links   │
│      duplicate of                        ⇄ duplicated by    1 link    │
│   ◌  1 hidden                                               ⌃H show   │
│                                                                       │
│  ↩ link   ⌃N ⌃P move   ⌃D hide   ⌃R rename   esc back                 │
╰───────────────────────────────────────────────────────────────────────╯

B. Ctrl-N twice: the sentence carries the label as a pill
│  “Buy new SSD for athena!”  ── implements ──▶  “What was athena…”     │
│ ▌    implements                                             2 links   │
│  ↩ inserts |implements   ⌃D hide “implements”   ⌃R rename             │

C. A new label marked one-off (typed `|`, or Ctrl-D on row 0)
│ │ prompted the purchase of▌                              ◌ one-off  │ │
│ ▌ ✦  prompted the purchase of                       new · one-off     │
│  ↩ inserts ||"prompted the purchase of" — won’t be suggested later    │

D. One-off on an existing visible label: the warning
│ │ inspired by▌                                           ◌ one-off  │ │
│ ▌    inspired by                                  3 links · one-off   │
│  ⚠ Also hides “inspired by” (3 links) from suggestions · ⌃D keeps it  │

E. Just hidden with Ctrl-D: the row stays where it was
│ ▌ ◌  implements                                  hidden · ⌃D undo     │

F. Show hidden (Ctrl-H)
│      inspired by                                            3 links   │
│   ── Hidden ───────────────────────────────────────────────────────   │
│ ▌ ◌  duplicate of                                           1 link    │
│  ↩ inserts |"duplicate of" (stays hidden)   ⌃D unhide   ⌃H hide them  │

G. Rename (Ctrl-R on “inspired by”)
│ ▌ ✎  Rename “inspired by” to [ prompted by▌                       ]   │
│      Rewrites 3 links in 3 notes · sase, dev, sase_post_blog · 1 commit│
│  ↩ rename   esc cancel                                                │
│  (if NEW exists: “Merges into “implements” (2) → 5 links · ↩ merge”)  │
```

Visual rules:

- **One icon.** Use 🪢 in the mint relation accent that the `~` sigil already uses. Drop
  the duplicate `arrow.left.arrow.right` SF Symbol next to it.
- **The sentence is the hero.**
  - The owner and target appear in primary text, truncated in the middle.
  - The label sits on the arrow as a muted small-caps pill, as on Obsidian chips.
  - It updates live with the highlight, so you always see what Return will write.
- **Rows match picker rows.**
  - Same row height, accent highlight, and bold matched text as other pickers.
  - Counts right-aligned in tertiary text.
  - Known inverse phrases (`⇄ duplicated by`) in quaternary text.
- **Hidden rows** use `eye.slash` (◌ above) and secondary text. They are never red.
- **Colors:** warnings are amber; red is reserved for invalid labels.
- **The footer** shows key caps, like Obsidian's `bob-cnp-kbd` hints. It changes with the
  highlighted row and shows at most five hints. It replaces today's
  `Tab cycles suggestions · esc back to picker` caption. Keep Cancel/Insert for pointer
  users, renamed Cancel/Link.
- **Motion:**
  - Rows never move under the highlight until you edit the query.
  - A just-hidden row stays in place, greyed out.
  - The highlight animates with a short spring.

### 4.4 Capture grammar: `||`

```text
~note:id|label           relation with a label
~note:id||label          relation with a label, and hide that label from suggestions
~note:id||"multi word"   same, quoted
~~note:id||label         reverse direction, same meaning
~note:id||               incomplete: needs relation_label (one-off)
```

- **Parse.** `relations[]` entries gain `hide: true`. The `relation_label_separator` span
  covers both pipes. For `~note:id||`, the `relation_label` need carries `hide: true`.
- **Dry run.** Each item in `capture --dry-run -f json` gains
  `relation_label_hides[] {label, key, existing_count, was_hidden, action: "hide"|"already_hidden"}`.
  When `existing_count > 0` and the label was visible, `warnings[]` also gets
  `{code: "hides_existing_relation_label", label, count, message}`.
- **Human preview.**
  - Existing label: `🪢 would link to "…" · inspired by · ◌ also hides "inspired by" from
    suggestions (3 links)`.
  - New label: `· ◌ one-off (not suggested)`.
- **Commit.**
  - Only after the vault write succeeds does bob append `relation_label.hide`, with `via`
    set to `capture` or `bob-mac-capture`.
  - A failed append (such as `lock_busy`) never fails the capture. It reports
    `relation_label_hide_failed` with the exact `bob relations hide …` command to retry.
  - A dry run never writes the journal.
- **Mac.** The preview row gets an amber `· also hides “inspired by”` suffix. The success
  notification adds `· hid “inspired by”`.
- **Using `|label` on a hidden label** leaves it hidden (A3).

### 4.5 `capture-complete` contract (`relation_label` context; additions only)

- **Each row adds:**
  - `hidden`;
  - `hide_replacement` (for example `||"inspired by"`), so the app never builds the
    one-off token itself (the thin-client rule);
  - `inverse` when the label has a built-in inverse phrase.
- **The typed row** adds `existing`, `count`, and `hidden` when it matches a catalog key.
  Its `label` then uses the catalog spelling (A10).
- **Top level** adds `hidden_count`.
- **Hidden rows are always returned**, after the visible ones, so Ctrl-H responds
  instantly. The thin-client decision allows the app to filter what bob returns. Shell
  completion still leaves hidden rows out.
- **Older versions:** an older bob without these fields leaves the card a plain list
  without ⌃D, ⌃H, or one-off hints (`decodeIfPresent`). An older app still benefits,
  because bob is the grammar authority for `||` in the editor.

### 4.6 `bob relations` CLI

```text
bob relations [list] [-a/--all] [-f/--format human|json] [-H/--hidden] [-n/--limit N] [-q/--query Q]
bob relations hide LABEL…   [-f/--format human|json]
bob relations unhide LABEL… [-f/--format human|json]
bob relations rename OLD NEW [-d/--dry-run] [-f/--format human|json] [-m/--merge] [-o/--offline]
```

- **Help placement:** under *Tasks and projects*, between `projects` and `task`
  (alphabetical).
- **Bare `bob relations` runs `list`.** `cli_rules.md` allows a bare group to default to a
  read-only member that takes only flags.
- **Not under `bob task`:** that group is reserved for commands that rewrite task lines
  across the vault, and list, hide, and unhide do not.
- **`--via`** is a hidden internal argument, as for themes.
- **Human list:** the label is colored in the mint relation hue on a TTY, counts are dim,
  and the words still carry the meaning under `NO_COLOR`.

```text
RELATIONS  3 labels · 6 links · 1 hidden
  🪢 inspired by     3 links
  🪢 implements      2 links
  ◌  duplicate of    1 link    hidden · ⇄ duplicated by
```

- **Filters:** the default view leaves hidden labels out, `-a` shows everything with
  hidden labels flagged, and `-H` shows only hidden labels.
- **JSON:**
  `{schema_version: 1, counts: {labels, links, hidden}, labels: [{key, name, count, hidden, inverse, spellings}], renamed_reappeared: [], warnings: []}`.
  `spellings` lists case variants, so drift is visible.
- **Refusal codes** mirror themes: `unknown_label`, `invalid_label`, `unchanged`,
  `label_exists`, `malformed_links_line`, `lock_busy`, `dirty_paths`, `not_a_worktree`,
  `sync_failed`, `verify_failed`, `stale_note`.

### 4.7 The rename transaction

This follows `bob themes rename` (PT10) and `bob ref rename`.

1. **Lock and sync.** Take `bob_sync.lock`, sync first unless `--offline`, then plan from
   the synced files.
2. **Plan.**
   - Find every LINKS entry whose label key equals OLD's key. Search every note bob scans,
     including daily notes and `done/`, but skip fenced lines and `_conflicts/`.
   - Relabel each entry in place with the existing planner (contract test vector LW4,
     which keeps entry order).
   - For each affected link whose target is writable, rewrite the target's LINKED FROM
     `(label)` through the mirror planner in the same batch.
3. **Refusals.**
   - `malformed_links_line`, listing paths, when a malformed LINKS line mentions OLD.
   - `label_exists` when NEW is a different existing label, unless `--merge`.
   - `unchanged` when every occurrence already matches NEW byte for byte.
   - A case-only rename (same key, new spelling) is allowed, because it standardizes the
     spelling.
4. **Write and verify.**
   - Snapshot the files, write them atomically, and append `relation_label.rename`.
   - Rescan to verify: OLD's key is gone, the entry count is unchanged, and only labels
     differ.
   - Restore the snapshots on any failure.
   - Make one commit, `bob relations rename: inspired by → prompted by`, then sync again.
   - To undo, `git revert` the commit.
5. **Preview.** The dry run lists:
   - files and entries, with before and after lines;
   - whether hidden state moves to the new name;
   - inverse-phrase changes, for example: renaming `follow-up of` means LINKED FROM chips
     read `(S) · followup → this` instead of `followed up by`.
6. **Reappearance.** `bob relations list` reports OLD in `renamed_reappeared` if an offline
   host writes it after the rename. It only reports, never rewrites.

Engineering note: the theme rename is 1,739 lines (`src/native/pomodoro_themes/rename.rs`).
Extract the lock, sync, snapshot, atomic write, verify, commit, and rollback steps into a
shared vault-rewrite transaction instead of writing a third copy.

### 4.8 Performance

- **Mac:**
  - Fetch the whole catalog, hidden labels included, once when the card opens and again
    after any hide, unhide, or rename.
  - Filter it locally with bob's documented rule: case-insensitive, prefix matches before
    substring matches.
  - Ask bob on each keystroke only to validate the typed row. The list never waits on that
    call.
- **bob:** `relation_label_suggestions` should stop calling `discover`. Walk the note paths,
  skip files that do not contain `**LINKS`, and parse only the rest.
  - Reading all 6,472 notes takes about 0.17 s warm, against 0.85 s for today's path.
  - A per-file fingerprint cache, like themes PT3, would bring a call down to roughly the
    cost of starting `bob`.

### 4.9 Obsidian

- **Relation field** (`426-picker-relation-stage.js`): add Tab/⇧Tab, Ctrl+D, Ctrl+H,
  Ctrl+R, and the `|` one-off toggle, exactly as on the Mac. Use the same row layout,
  footer key caps, and warning wording.
- **Writes** start bob the way the theme manager does (`themesWriteSpawn`,
  `279-plugin-pomodoro-themes.js:608`):
  `bob relations hide|unhide|rename … --via bob-navigation-hotkeys -f json`. This works on
  desktop only, and rename always previews with `-d` first.
- **Reads:** `api.relationIndex.labelSuggestions()` must leave out hidden labels and add a
  `hidden` field to each row. To support this, bob-ledger-tools folds
  `.bob/relations/*.jsonl` as it already folds the theme journal, checked against shared
  fold test vectors.
- **Chips are unchanged.** A later option: right-click a label pill to reach
  "Rename relation…".

## 5. Risks and edge cases

- **Rename racing a capture.** bob's snapshot check aborts with `stale_note`, and the card
  says "Vault changed — try again".
- **Hosts without the allowlist.** Hide events stay local until vault-sync delivers the
  `.gitignore` change. Themes accepted the same cost.
- **Two hosts toggling the same label.** The last write by timestamp wins, which is fine
  for a suggestion preference.
- **A failed hide call.** The greyed-out row reverts and bob's message appears inline.
- **The `|` key.** Because it toggles one-off, it can never enter a label, which is
  already the rule.
- **Version mismatch.** A new app with an old bob shows a plain list, and an old app with
  a new bob still parses `||` typed in the editor (§4.5).
- **Inverse phrases.** Renaming away from a built-in label changes how chips read, and
  the preview says so.
- **Regression test.** Use a fake process client that filters by query, as real bob
  does, so collapsing the list fails the test. Also test that Ctrl-N from an empty field
  highlights the most-used label, and that the highlight survives a refresh by key.

## 6. Recommended solution

Build the vocabulary model bob already uses for themes, in six phases that each land on
their own:

| # | Repo | Scope | Size |
| --- | --- | --- | --- |
| 1 | bob-mac-capture | Vertical list with separate query and highlight (highlight stored by label key); Ctrl-N/P, ↓/↑, Tab/⇧Tab; row 0 is the plain link or the typed label; a drawn highlight; the catalog fetched once and filtered locally; a regression test with a filtering fake client. **No bob change: this fixes the reported bug.** | small |
| 2 | bob-cli | Fast label scan (skip files without `**LINKS`; no `discover`); a shared preferences journal; `bob relations list/hide/unhide`; the new `capture-complete` fields (`hidden`, `hide_replacement`, `existing`, catalog spelling, `hidden_count`, `inverse`); the vault allowlist; `docs/task-relations.md` §3.2 and §12 | medium |
| 3 | bob-cli | `||` grammar, parse and dry-run fields, the warning, the journal append on commit, shell completion, `docs/reference/capture-syntax.md` | small–medium |
| 4 | bob-mac-capture | Ctrl-D hiding with the row kept in place, the Ctrl-H Hidden section, the one-off toggle (`|` or Ctrl-D), warnings in the card, preview, and notification, and the visual refresh (§4.3); `docs/keyboard.md`, `docs/relationship-pickers.md` | medium |
| 5 | bob-cli | `bob relations rename`, built on a shared vault-rewrite transaction | medium–large |
| 6 | bob-plugins + bob-mac-capture | Obsidian keys, journal fold, and test vectors; Ctrl-R rename in both apps | medium |

How I'd sequence it:

- **Ship phase 1 now.** It fixes the reported bug.
- **Run phases 2–4 as one small epic** ("relation vocabulary"), because hide and `||`
  share the journal and the card.
- **Do phases 5–6 last.** Rename is the most expensive and least needed today; until it
  exists, a hand edit followed by `bob task reconcile` covers it.

Decision records to write with `/sase_memory_write` once you accept this:

- **"Hiding a relation label removes it from suggestions only."** A twin of
  `theme-hide-is-recent-only`.
- **"Relation label preferences live in the per-host journal."** Alternatively, widen
  `theme-prefs-live-in-per-host-journal` into one record for all catalog preferences.
- **"Relation label renames rewrite history in one commit."** Records the `done/`
  exception to LR7.

## Sources

- bob-mac-capture `72cd721`:
  - `Sources/BobMacCapture/CapturePanelModel.swift` (lines 6631–6650, 6846–6975);
  - `CapturePanelView.swift:1762–1860`;
  - `CaptureKeyCommandRouter.swift:519–537, 654–685`;
  - `Tests/BobMacCaptureTests/CaptureRelationPanelTests.swift:121–137`;
  - `docs/relationship-pickers.md`, `docs/keyboard.md`.
- bob-cli `8628ce2f`:
  - `src/native/capture_complete/candidates.rs:1403–1495, 1592–1654`;
  - `src/native/capture_complete/support.rs:18`;
  - `src/native/task_relations/label.rs`;
  - `src/native/capture_language/relations.rs:428–620`;
  - `src/native/pomodoro_themes/journal.rs`;
  - `docs/task-relations.md` (§3.2, §6, §10, LR7, LW4), `docs/pomodoro-themes.md`
    (PT4, PT7, PT9, PT10).
- bob-plugins `3a7368a`:
  - `plugins/bob-navigation-hotkeys/src/426-picker-relation-stage.js`;
  - `200-filtered-picker-modals.js:192`;
  - `450-picker-keydown.js`;
  - `plugins/bob-ledger-tools/src/279-plugin-pomodoro-themes.js:608–740`;
  - `docs/task-relations.md`.
- Memory:
  - decisions `mac-capture-is-a-thin-client`, `theme-hide-is-recent-only`,
    `theme-prefs-live-in-per-host-journal`, `unblocked-tasks-are-offered`;
  - `cli_rules.md`.
- Prior work:
  - `research:202610/task_relation_labels.md`;
  - `research:202610/bob_cli_am_undirected_relations_review.md`;
  - bead `bob-cli-am` (cancelled 2026-10-21);
  - `plan:202610/relation_pipe_card.md`, `plan:202610/task_relations.md`.
- Live checks, all read-only:
  - `bob capture-complete -f json` with the queries `""` and `"inspired by"`;
  - `bob capture-parse -f json` on a `||oneoff` draft;
  - three timed `capture-complete` runs (2.52 s, 0.86 s, 0.85 s);
  - `grep` for `**LINKS:**` across `~/bob`.
