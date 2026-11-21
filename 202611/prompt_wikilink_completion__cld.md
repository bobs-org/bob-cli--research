---
title: "`[[` wikilink completion in every Bob prose prompt"
researcher: cld
date: 2026-11-21
repos: bob-cli, bob-plugins, bob-mac-capture
---

# `[[` wikilink completion in every Bob prose prompt

**Question.** Bryan wants Obsidian link completion, triggered by `[[`, in every free-form
text prompt Bob shows (intentions, Work Log, and so on). It should be intuitive, reliable,
and beautiful. Is this a good idea, how should it be built, and what would I change?

**Short answer.** Yes, build it. It is high-value and low-risk if it is built **once**, as
a shared *prose-field* controller in bob-navigation-hotkeys. That controller owns both the
existing USED BEFORE recall band and a new LINK mode, so the two never fight over
`Ctrl+N/P`, arrows, Tab, Enter, or Esc.

- **Candidates** come from Obsidian's in-memory `metadataCache`, which is instant and
  always current.
- **Bob-owned policy** comes from a catalog fetched from `bob` once and kept fresh on vault
  events: which notes are living, archived, or hidden, and the link text to insert.
- **Ranking** happens locally on every keystroke.

Do **not** spawn `bob capture-complete` per keystroke from Obsidian. On the real vault it
takes about 0.5 s warm.

Fix two `bob` defects found here before the Mac side extends to more fields:

- An unclosed `[[` replaces through the end of the line.
- For `[[sase`, the top-20 ranking hides every root-level `sase_*` note.

Detailed recommendation in §9.

---

## 1. What exists today (evidence)

### 1.1 The Mac capture panel already does this

Bob Mac Capture has complete `[[` support. Its doc is `docs/wikilink-completion.md` in
bob-mac-capture. It covers:

- notes, embeds `![[`, aliases
- headings `[[note#…` and same-note `[[#…`
- blocks `[[note#^…` and same-note `[[#^…`
- vault-wide `[[##…` and `[[^^…`
- a separate `((` Task Wikilink picker

The pieces:

- **bob side.** `src/native/capture_links.rs` holds the whole engine: a `NoteIndex`,
  `MatchKind` ranking (exact → prefix → word-boundary → acronym → substring, each matched
  against alias, stem, and path), living/archive/hidden tiers from
  `src/native/note_catalog/tiers.rs`, and a 20-result cap.
- **Mac side.** It renders bob's rows in `CompletionList` / `CompletionRow`. Each row has
  an SF Symbol, an emphasised match, a muted path, and badges (`Alias`, `H2`, block
  preview).
- **Inserted text.** A vault-relative path without `.md`, or `path|Alias` when an alias
  matched. `]]` is appended when the link is still open.

The feature is therefore not new to Bob. The request really means: **bring `[[` parity to
every other place Bryan writes prose.** Bryan already writes links there by hand:

- This week's note, `2026-W47`, has three intentions, all linked:
  - `"Finish [[sase_blog_zettel]] album!"`
  - `"Finish sase-1n6 release train (see [[sase#^ref-sase-1n6-11-4-restart-readiness]])"`
  - `"Fix decisions memory issues (see [[sase#^fix-decision-memory-web]])!"`
- Rotten Log entries contain `— Made obsolete by [[sase_blog_zettel]] album!`.

Hand-typing exact stems and `^block-ids` is precisely what completion removes.

### 1.2 The prompts that would get it (bob-plugins)

A full sweep of `plugins/*/src` found that **every free-text prompt lives inside an
Obsidian `Modal`**. Note views only paint read-only cards. Each surface was classified as
prose written to the vault (P2V), a picker query, or an identifier.

| # | Surface | Opened by | Element | Recall band | Written by |
|---|---|---|---|---|---|
| 1 | Rotten keep / decay Stay reason (`nav 195:502`) | Alt+F, Ctrl+Alt+F, decay card | input | `rotten` | CM6 transaction (Rotten Log) |
| 2 | Batch keep reason (`nav 192:77`) | counted Alt+F | input | `rotten` | CM6 |
| 3 | Cancel reason stage (`nav 380:2`) | Task Card `x`, schedule review | picker input | `cancel` | CM6 (Cancel Log) |
| 4 | Lane-release reason (`nav 380:229`) | Task Card lane row | picker input | `work` | Work Log |
| 5 | Scheduling Work Log (`nav 370:253`) | scheduling Pending/Next | picker input | `work` | Work Log |
| 6 | Schedule review reason + summary (`nav 370:47,80`) | explicit `scheduled` | 2 inputs, Tab cycles | `schedule` / `work` | Schedule Log + Work Log |
| 7 | Release task (`nav 190:759`) | Alt+N on `[/]` | input | `work` | Work Log |
| 8 | Move to Next (`nav 196:126`) | Alt+N on a Task Link | input | `work` | Work Log |
| 9 | Successor inline cancel reason (`nav 206d:321`) | Ctrl+J picker | input in a results row | `cancel` (dense) | Cancel Log |
| 10 | Unlink work summary (`block-id-prompt 090:438`) | Ctrl+Shift+Enter | input | `work` (through the nav API) | Work Log |
| 11 | Intention Card editor (`ledger 297cc:130`) | `==`, Edit intentions | intention and summary: inputs; reflection: textarea | — | `bob periods update` |
| 12 | Record Card text stage (`ledger 242q:125`) | Edit record | textarea, newlines refused | — | `bob records update` |
| 13 | Notebook create, Summary field (`nav 685:38`) | command | input | — | `bob notebooks create` |
| 14 | Task from this email (`bob-mail 040:16`) | command | input | — | `bob capture` |

Excluded on purpose, because completion would be wrong there:

- picker queries
- block IDs
- file, relation-label, and type renames
- bank categories
- album schema fields
- chip author (the literal code payload; a `[[` there must stay literal)
- New email To / Subject

No prose path escapes or strips `[[ ]] | # ^`. Those paths only trim text and collapse
whitespace or newlines, so inserted wikilinks survive verbatim.
`normalizeScheduleReasonText` (`nav 030:277`) says so explicitly.

### 1.3 Infrastructure we can reuse (and the one big conflict)

- **USED BEFORE recall band** (`nav 183–185`, `api.logRecall` v1 at `nav 480:915`).
  - Surfaces 1–10 already attach it.
  - It is stable-height (`pinnedSlots` / `--bob-log-recall-slots`), uses 24 px rows, and
    filters by the draft.
  - It owns **Ctrl+N / Ctrl+P and ↑/↓** in capture phase, and registers Esc on the modal
    scope.
  - **Any link completion that attaches independently will collide with it.** This is the
    single most important design constraint.
- **`((` Task Wikilink picker** (block-id-prompt `022`, `031`, `032`, `036`, `087`, `128`).
  - It is a JS mirror of bob's `((` grammar plus a `TaskWikilinkIndex`.
  - It is editor-only today, but reusable for `((` in prompts.
- **Record Card link stage** (`ledger 242q:27`). It does a substring match over files and
  writes `[[path]]`. This is a simpler, separate implementation that should eventually
  converge on the shared kit.
- **Cross-plugin APIs** are frozen `app.plugins.plugins[id].api` objects with a `version`
  that callers feature-detect. Every consumer already fails open when an API is missing.
- **Not used anywhere:** `AbstractInputSuggest`, `PopoverSuggest`, `SuggestModal`,
  `getLinkSuggestions`, `prepareFuzzySearch`. Bob's design language is inline,
  keyboard-first bands, not Obsidian popovers.

### 1.4 Measurements and defects found

| Probe (real vault `~/bob`, about 7k `.md` files, bob 0.5.0, apollo) | Result |
|---|---|
| `bob capture-complete -c 11 -- 'Read [[sase'`, three warm runs | **0.45–0.55 s** each, with an 0.81 s cold run. `NoteIndex::read` walks and fully reads every note on every call |
| `bob capture-complete -c 2 -- '//'` (living note catalog, 3,719 rows) | **0.21 s** once |
| `[[sase` top 20 | `sase`, then 19 rows from `chat/`, `plans/`, `prompts/` (`prompts/sase_accept`, …). **None of the root `sase_*` notes** (`sase_actstat`, `sase_art`, `sase_blog_zettel`, …) make the cut, because ties within a match kind sort alphabetically by full path |
| `bob capture-complete -b vault -c 9 -- 'Read [[da because of the outage'` | `replacement {start: 7, end: 31}`. Accepting `day]]` gives **`Read [[day]]`. The text `because of the outage` is deleted** |

The last row is a real bug for prose. Inserting a link mid-sentence before existing text is
the normal case in a reason or summary field. The Mac panel has the same bug today.
Obsidian's editor replaces only up to the caret.

---

## 2. Critique: is this a good idea?

**Yes, and it is overdue.** Four reasons:

1. **Demand is proven.** Bryan already hand-writes links in intentions and log entries.
   That includes block links like `[[sase#^fix-decision-memory-web]]`, which are long,
   easy to typo, and silently dangle when wrong.
2. **It feeds existing machinery for free.** A block link to a task inside a Cancel,
   Schedule, Work, or Rotten Log entry already produces a **Task Mention** on the target's
   🪢 LINKED FROM line (glossary: Task Mention). Completion turns "I wrote a reason" into
   "the history is navigable both ways", with no new feature.
3. **Parity lowers cognitive load.** `[[` works in the Obsidian editor and in the Mac
   capture panel. It is surprising that it doesn't work in the prompts that pop up *from*
   those places.
4. **It costs nothing when unused.** Nothing about a prompt changes until `[[` is typed.
   Blank-reason and one-keystroke flows stay exactly as fast.

**Where the plan as stated is weak:**

- **"Any free-form text input prompt" is too broad.**
  - Picker queries, identifiers, and the chip payload must *not* complete.
  - The Mac app also has prose fields: the Cmd+E event-note editor and the Pull-In
    "Why cancel?" field. The plan doesn't mention them.
  - Scope needs a crisp rule (§3, A1).
- **"Triggered by `[[`" is under-specified.** It leaves open:
  - what Enter does while a link is half-typed, when Enter normally *submits and writes
    the vault*
  - what Esc closes
  - how recall's Ctrl+N/P coexists with link navigation
  - what an empty `[[` shows
  - what text is inserted
  
  These decide whether the feature feels reliable, so they belong in the requirements.
- **Per-prompt implementation would drift.** There are 14 surfaces across 4 plugins. The
  `q`/`Ctrl+[` decision record exists precisely because per-panel opt-in drifts. One kit
  is needed, with a declarative opt-in and a test that enumerates prose surfaces.
- **The obvious implementation is wrong.** Calling `bob capture-complete` per keystroke
  ("thin client, like the Mac") would be about 0.5 s of lag per character in Obsidian. It
  would also inherit the two bob defects in §1.4.

---

## 3. Requirement adjustments (called out explicitly)

| ID | Adjustment | Why |
|---|---|---|
| **A1** | **Scope = prose-to-vault fields**: the 14 surfaces in §1.2, plus the two Mac prose fields in a later phase. Explicitly *not* picker queries, identifiers, code payloads, or email headers. | Completion in an ID or rename field produces garbage. A rule beats a list. |
| **A2** | **Full Obsidian link grammar, not just `[[note`.** `![[`, `[[note#heading`, `[[note#^block`, `[[#…`/`[[#^…` (same note = the note the prompt writes into), `[[##…`/`[[^^…`, and `[[note\|` alias. | This matches the Obsidian editor and the Mac. Block links are what create Task Mentions. |
| **A3** | **Add `((` task links in prompts (phase 2).** | A reason like "superseded by ((bank import" is the most valuable link in a log entry. block-id-prompt already has the index and grammar. |
| **A4** | **Enter finishes the link; it never submits a half-typed link.** | In these prompts Enter writes the vault and closes the modal. Submitting `[[sase` by accident is the worst failure mode. |
| **A5** | **Fix bob first.** (a) An unclosed `[[` field ends at the caret. (b) Tie-break ranking within a match kind by shallower path, then inbound-link count, then alphabetically. | (a) is data loss in the Mac panel today. (b) makes `[[sase` useful on both surfaces. |
| **A6** | **Show a quiet, non-blocking unresolved-link note** when the draft holds a `[[…]]` that resolves to nothing. | Typos otherwise create dangling links silently. Bob never refuses Bryan's text, so this is info only. |
| **A7** | **One inserted-text rule across Bob**: bob's vault-relative `insert_target` (`[[2026/2026-11-21]]`, `[[sase]]`), plus `\|Alias` for alias matches. | Same output as the Mac panel. A path link can never be re-resolved to a different note by a later same-named file. Trade-off in §5.4. |
| **A8** | **Call it "wikilink completion"**, never just "completion". | `docs/completion.md` already reserves "shell completion". The Mac doc's title is "wikilink completion". |

---

## 4. Approaches considered

| Approach | Verdict | Reason |
|---|---|---|
| **(a) Spawn `bob capture-complete` per keystroke** (Mac model) | ✗ | 0.45–0.55 s warm per keystroke on the real vault, plus spawn jitter. It inherits the end-of-line replacement bug, and capture grammar is irrelevant to a reason field. The thin-client decision binds only the Mac app and bob-cli. It also explicitly lets a client "filter or rank what bob returned", and the relation-card decision *requires* local instant ranking from a catalog fetched once ("navigation must be local and instant"). |
| **(b) Obsidian `AbstractInputSuggest` / `PopoverSuggest`** | ✗ | Public API, but: it treats the whole field value as the query; its typed target is `HTMLInputElement \| HTMLDivElement` only, so the reflection textarea is out; the popover anchors to the input's rect, not the caret; it pushes its own keymap scope (arrows/Enter only, no Ctrl+N/P, no Tab-accept) that races the recall band; and it looks like stock Obsidian, not a Bob band. |
| **(c) Replace the `<input>`s with embedded CodeMirror 6 editors** to get native `[[` and live link rendering | ✗ | Needs private APIs (embed registry / `MarkdownEditView` hacks). `vimMode: true` in the vault means Esc would enter normal mode instead of closing. It breaks the Enter-submits contract, and it is heavy for one-line reasons. |
| **(d) Auto-link plain-text mentions after submit** | ✗ | It guesses links, contradicting Bob's explicit-gesture ethos, and is unreliable. |
| **(e) Shared prose-field controller: metadataCache candidates + bob tier catalog + local ranking, rendered in the recall band's slot** | **✓** | Instant, always fresh, keyboard-consistent, zero layout shift, one place to get right. |

---

## 5. Recommended design

### 5.1 Architecture

```text
             (once, then on vault create/delete/rename, debounced 2 s)
  bob capture-complete -c 2 -f json -- '//'      → living paths   ─┐
  bob capture-complete -A -c 2 -f json -- '//'   → archived paths ─┼─► TierMap (path → living|archive|hidden)
                                                                   │   fail-open: done/ → archive, dot-dirs → hidden
  app.metadataCache  (files, frontmatter aliases,                  │
                      headings, blocks, resolvedLinks) ────────────┴─► LinkIndex (in-memory, incremental)
                                                                          │
  prose field (input/textarea) ──keystroke/caret──► LinkFieldModel ──query──► rank() ──► rows
           ▲                                       (pure: find [[ field,       (bob MatchKind ladder
           │                                        stage, replacement)        + tier + affinity)
           └──────────── accept: execCommand('insertText') ◄── ProseFieldController ◄── keys
                                                                   │
                                                   one band slot: LINK mode │ USED BEFORE mode
```

- **Owner: bob-navigation-hotkeys.** It already owns `api.logRecall`, the FilteredPicker
  kit, and 9 of the 14 surfaces.
- **New API: `api.proseField` v1.**

  ```js
  attach({ inputEl, sourcePath, recall: kind|null, links: true, bandHost, density, scope })
  ```

  It returns `{ handleKeydown, backOut, isBusy, detach }`.
- **Compatibility.** `api.logRecall.attach` stays v1 and becomes a thin wrapper that calls
  `proseField.attach({ recall: kind, links: true })`. Surfaces 1–10 therefore get wikilink
  completion with **no call-site change**. Every field with a USED BEFORE band is a log
  prose field by construction.
- **`sourcePath`** defaults to the active file and resolves `[[#…`. Hosts that know better
  pass it: Work Log → the task's note; intentions → the daily or period note.
- **Other plugins** feature-detect `api.proseField` and fail open, exactly like today's
  recall consumers:
  - ledger: Intention Card, Record Card
  - bob-mail
- **Repaint-safe.** The Intention Card editor rebuilds its input on every paint
  (`297ca` header comment). The controller therefore supports *delegated* attachment
  (`attachWithin(container, '[data-bob-prose]')`) through `focusin`, with state keyed by
  field kind, so a rebuilt input keeps its open band.
- **Proposed fragments** (each ≤1000 lines, per bob-plugins rules):
  - `186-prose-link-model.js`: pure, unit-tested
  - `187-prose-link-index.js`
  - `188-prose-field-controller.js`
  - `189-prose-link-band.js`: DOM
- **Index cost.**
  - Built lazily on the first `[[`: about 7k files, aliases through
    `parseFrontMatterAliases`, roughly 10 ms.
  - Updated incrementally on `metadataCache` `changed`/`deleted` and vault `rename`.
  - Headings and blocks are read per target on demand from `getFileCache`. Block previews
    come from `vault.cachedRead` plus the block's position.
  - Ranking 7k entries in JS is well under 5 ms per keystroke.
- **Privacy.** Mirror the Mac rule: note paths, aliases, headings, and previews are never
  logged, persisted, or put in notices.

### 5.2 Field model (pure, mirrors `capture_links.rs` except the bug)

- **Field opens** at the last unescaped `[[` (or `![[`) before the caret on the same line
  that is not closed before the caret and not inside a backtick code span. This uses the
  same protected-range rules as bob (`\[[` and code spans are skipped).
- **Stages:**
  - target: until `#` or `|`
  - heading: after `#`
  - block: after `#^`
  - alias: after `|`; there are no rows here, and the band shows a hint instead
- **Field end:**
  - If the matching `]]` follows the caret before any newline or `[[`, the field ends at
    it, and accepting replaces through it.
  - **Otherwise the field ends at the caret.** That is fix A5(a), and it is what
    Obsidian's editor does.
- **Accept.**
  - Replace the field with `insert_target` (`|Alias` when an alias matched; `#Heading` or
    `#^id` in those stages) and add `]]` if it was absent.
  - The caret lands after `]]`.
  - Insert with `document.execCommand('insertText')`, falling back to
    `setRangeText` + `input`, so **Ctrl+Z restores the typed `[[sas`**. The recall band's
    value-assignment approach loses undo; don't copy it.
- **Ignored:** IME composition (`isComposing`) and paste. A pasted complete `[[x]]` never
  opens the band.
- **Re-evaluated on:** `input`, `selectionchange` (click, ←/→, Home/End), and focus. When
  the caret leaves the field the band returns to recall mode.

### 5.3 Ranking

The ranking stays faithful to bob, plus the fix:

1. **Tier**: living → archive → hidden, from the bob TierMap.
2. **Match kind**: bob's 15-step ladder: exact, then prefix, then word-boundary, then
   acronym, then substring, each checked against alias → stem → path.
3. **Affinity tie-break** (new; propose the first two upstream in bob as A5(b)):
   - shallower path first (root area/project notes beat `prompts/…`)
   - then inbound-link count from `metadataCache.resolvedLinks`, computed once at build
   - then recently opened (`workspace.getLastOpenFiles()`)
   - then alphabetical
4. **Empty query** (just typed `[[`): a short "Suggested" list:
   - *This note* (`sourcePath`)
   - its root area/project
   - the 5 most recently opened notes
   
   It never dumps the alphabetical vault.

Keep a **parity fixture**: about 30 `(query, expected top-5 paths)` vectors generated by a
bob test over the `vault/` fixture and checked in to bob-plugins. A ranking change in
either repo then fails CI in the other's fixture review instead of drifting silently.

### 5.4 Inserted text (A7) and its trade-off

- **Bob's rule** is vault-relative path without `.md`.
  - Root notes, which are most of Bryan's hand-written targets, come out identical to
    Obsidian's "shortest" form: `[[sase_blog_zettel]]`.
  - Nested notes differ: Bob writes `[[2026/2026-11-21]]`, the native editor writes
    `[[2026-11-21]]`.
- **Path form wins** because:
  - it matches every machine-written Bob link (about 7.3k path-style links in `2026/`,
    mostly `2026/…` and `done/…`)
  - it matches the Mac panel
  - it can never become ambiguous
  - `alwaysUpdateLinks: true` keeps both forms correct across renames
- **Alternative:** if Bryan prefers prompts to match the Obsidian editor byte-for-byte, use
  `metadataCache.fileToLinktext(file, sourcePath, true)`. It is a one-line switch, and it
  should be a single setting that both surfaces honour.

### 5.5 Keys: one arbiter, Esc layering preserved

The controller handles keys in this order: **LINK mode → recall → host (picker, stage,
submit)**. It listens in capture phase on the modal root, so it runs before the input's
own listeners. While the band is open it also pushes a keymap `Scope`, so Esc beats the
Modal's own Esc.

| Key | LINK band open | LINK band closed (unchanged today) |
|---|---|---|
| `[[` | opens / refreshes | — |
| ↑/↓, Ctrl+P/Ctrl+N | move link selection (first row preselected) | recall navigation |
| **Tab** | accept selected row (relation-card rule: Tab accepts) | host behaviour (field cycling in surface 6) |
| **Enter** | accept selected row. With **no** rows: close the link as typed (`]]`). **Never submits.** | host submit |
| Shift+Enter (textarea) | newline, closes band | newline |
| Ctrl+Enter (Intention reflection) | accept, then save and close | save and close |
| **Esc / Ctrl+[** | close the band only (one layer, per the `q`/`Ctrl+[` decision); the band stays closed until the next keystroke inside the same field | recall back-out, then close |
| `q` | types (text control) | types |
| `#`, `^`, `\|` | typed; switch stage | typed |
| Backspace | edits; deleting a `[` closes the band | host behaviour |

**Why Enter never submits mid-link.** In every surface Enter writes the vault and closes
the modal. Turning "I hit Enter to pick the link" into "I wrote `[[sase` into the Rotten
Log" is the one failure the feature must make impossible. The cost is one extra Enter
when Bryan really wants a literal unclosed `[[`, which is essentially never.

### 5.6 Visual design ("beautiful")

The link list renders **in the recall band's slot, at the same pinned height**. Switching
between USED BEFORE and LINK therefore causes **zero layout shift**, and the modal never
jumps. Bob's Mac panel follows the same "fixed eye line" principle. Hosts without recall
(Intention, Record, Notebook, Mail) get the same band, sized to five 24 px rows, appearing
under the field with the recall band's 120 ms fade.

```text
 Release task — In Progress → Ready
 ┌───────────────────────────────────────────────────────────────┐
 │ Unblocked by the [[sase_bl▌                                   │
 └───────────────────────────────────────────────────────────────┘
 🔗 LINK  sase_bl                                        3 notes
 ▍ 󰈙  sase_blog_zettel                              album · 41 ⇠
    󰈙  sase_blog                                    ref/
    󰈙  sase_blog_zettel_waves              done/ · Archived
    ↵ inserts [[sase_blog_zettel]]
 ⇥ ↵ Insert · ⌃N ⌃P Move · # Heading · ^ Block · esc Close
```

- **Rows** use the Mac `CompletionRowContent` grammar, so both surfaces read alike:
  - a Lucide icon: `file-text` for a note, `hash` for a heading, `pilcrow` for a block,
    and a status glyph for a task row in phase 2
  - the primary name with the matched span emphasised, using the existing
    `appendHighlighted` helper (`nav 190:201`, safe text nodes, never innerHTML)
  - the muted folder, middle-truncated so the filename survives
  - right-aligned capsule badges: `Alias`, `H2`, `^id`, a block preview, `Archived`
  - archive-tier rows at reduced opacity
- **Selection** uses the recall band's treatment: a 10% `--interactive-accent` mix plus a
  2 px accent left border. Use theme variables only.
- **Detail line**: `↵ inserts [[…]]` shows the exact bytes before they are written. The
  Mac panel has the same detail strip, and it is the best reliability affordance in the
  design.
- **Empty states**:
  - Alias stage: "Alias — type the label, `]]` to finish".
  - No matches: "No note matches `xyz` — ↵ keeps `[[xyz]]` as typed".
- **Links strip (A6)**: once the draft holds a complete link, one quiet line sits under
  the field. Each link shows as a chip in `--text-accent`. An unresolved link shows as a
  faint warning chip, "`foo` — no such note". It never blocks.
- **Accessibility**: `role=listbox` / `aria-activedescendant` on the input, and the recall
  band's existing live region announces "3 notes, sase_blog_zettel".

### 5.7 Mac parity (phase 3)

- Two more Mac prose fields should get the same behaviour:
  - the event-note editor (`GcalNoteNSTextView`, Cmd+E)
  - the Pull-In "Why cancel?" field
- To keep the app a thin client, bob adds one **additive** flag:
  `capture-complete -L/--links-only`.
  - It runs only the wikilink (and `((`) providers and ignores capture grammar.
  - The `capture-*` names may only grow additively; every long option needs a short alias
    (cli_rules).
- The app reuses `CompletionList` unchanged.
- If per-keystroke latency bothers Bryan on the Mac, the same catalog-plus-local-rank model
  is allowed by the thin-client decision, since the client may rank what bob returned.
  That decision should then be revisited explicitly.

---

## 6. Reliability checklist (what makes it trustworthy)

1. Never destroys text after the caret (A5a; covered by unit vectors with trailing prose).
2. Never submits a half-typed link (A4).
3. Undo restores the typed query.
4. Survives Intention Card repaints (delegated attach).
5. Fails open in three cases:
   - no nav plugin → the prompt works unchanged
   - no `bob` or a slow tier fetch → heuristic tiers
   - an index error → no band, never a thrown modal
6. Stays quiet: no band in identifier fields, code spans, `\[[`, or paste.
7. Is drift-proof:
   - prose fields opt in with `data-bob-prose` (or through recall attachment)
   - a bob-plugins contract test lists the 14 surfaces
   - a lint fails when a new Modal `<input>` declares neither `data-bob-prose` nor
     `data-bob-ident`

---

## 7. Phasing

| Phase | Repo | Content |
|---|---|---|
| 0 | bob-cli | Fix the unclosed-`[[` replacement range. Add depth and inbound-link tie-breaks. Docs: `docs/capture.md` contract note. (The Mac benefits immediately.) |
| 1 | bob-plugins (nav, block-id-prompt) | `api.proseField` v1, LinkIndex + TierMap, LINK band. `logRecall.attach` gains links by default. Covers surfaces 1–10. Pure-model unit tests, parity fixture, `bob plugins sync`. |
| 2 | bob-plugins (ledger, nav, mail) | Intention Card (intention/summary/reflection), Notebook summary, Record Card text, Task-from-email. Links strip. `((` task links in prompts through block-id-prompt's `TaskWikilinkIndex`. Converge Record Card's link stage onto the kit. |
| 3 | bob-cli + bob-mac-capture | `capture-complete -L/--links-only`. Wire the event-note editor and the Pull-In reason. macOS CI gate. |

After Bryan accepts the Enter rule and the scope rule, record them as a decision:
"`[[` completes in every Bob prose field; Enter finishes a link, never submits it". The
next prose prompt then inherits the rule instead of re-deciding it.

---

## 8. Risks and open questions for Bryan

- **Link text form** (§5.4): bob's path form (recommended) or Obsidian "shortest"?
- **Should a band-closed Enter on a draft with an unclosed `[[` still submit?** The
  recommendation is yes (A4 covers only the band-open case). The unresolved-link strip
  makes the state visible.
- **`((` in prompts can write a block ID into another note** when an ID-less task is
  chosen, which is a side effect from inside a modal. The editor flow already does this
  safely, so reuse its transaction rather than inventing one.
- **Ranking divergence** between Obsidian and the Mac until phase 0 lands. The parity
  fixture bounds it afterwards.

---

## 9. Recommended solution

Build **one prose-field controller in bob-navigation-hotkeys** (`api.proseField` v1) that
owns every free-text prompt's band and keys. Give it two modes in the same pinned-height
slot: today's USED BEFORE recall and a new **LINK** mode that opens on `[[`.

- **Candidates** come from Obsidian's `metadataCache`.
- **Bob owns the policy**: which notes are living, archived, or hidden, and what link text
  to insert. It supplies this through a cached `capture-complete '//'` catalog.
- **Ranking** is local, using bob's MatchKind ladder plus depth, inbound-link, and recency
  tie-breaks.
- **Accept** inserts `[[vault/path]]` (or `|Alias`, `#Heading`, `#^block`) with native
  undo, and never touches text after the caret.
- **Tab and Enter accept, Esc closes one layer, and Enter never submits a half-typed
  link.**

Ship it through the existing `logRecall.attach` so the 10 Work, Rotten, Cancel, and
Schedule Log prompts get it with no call-site edits. Then add Intentions, Notebook,
Record, and Mail. Then add `((` task links, which turn log entries into Task Mentions.
Finally add the Mac's two prose fields through an additive `capture-complete -L`.

Before any of that, fix bob's two defects: the unclosed-`[[` range that deletes trailing
text, and the path-alphabetical tie-break that hides root notes. Both already hurt the Mac
capture panel today.

This keeps one keyboard contract and one link-text rule across Bob, stays instant on a
7k-note vault, and is visually native to Bob's existing bands.
