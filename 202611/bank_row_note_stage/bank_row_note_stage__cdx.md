# Bank row notes: a quiet annotation that keeps your place

Independent research by **cdx**, 2026-11-21. This report uses repository code, existing tests, and primary documentation. No other report, transcript, or finding from this research swarm was consulted. This is a design recommendation, not an implemented feature or a record of usability testing.

**The feature is a good idea.** The moment of reviewing a purchase is an appropriate time to capture its purpose, and keeping the current row in place preserves the distinction between explaining a transaction and acknowledging it. I recommend Space opening a small Note stage inside the Category card, explicit save returning to the same card and row, and a readable note immediately beneath the transaction. Two discoveries warrant changes to the initial proposal: Space already performs an advancing action, and the existing inline note grammar is not a safe container for arbitrary annotation text.

My recommended storage is one labeled Markdown child bullet, `  - **Note:** …`, rather than extending the transaction's inline tail. This costs a small child-note recognizer but avoids mixing annotation prose with account, category, flag, and identity syntax. Existing inline notes remain intact. The detailed behavior and tradeoffs follow.

**What the current implementation establishes.** The inspected revisions were bob-cli `020ad4e6207f81fd9c633db21c48e1b8efdf3bba` and bob-plugins `4e0ff78b1534e62a55e86f8c94632bc76f3cc84b`. Source references below use repository-relative paths and these revisions, so they do not depend on an ephemeral checkout.

| Finding | Evidence | Design consequence |
| --- | --- | --- |
| Space currently files without a category, ticks a waiting row, and advances. In correction mode it removes the category. | bob-cli `docs/guides/acknowledge-bank-transactions.md`; bob-plugins `245-plugin-bank-category-card-model.js`, `bankCategoryResolveCardKey`; `248f-plugin-bank-category-new-model.js`, `bankCategoryCardKeysText` | This is a key reassignment, not a new unused key. Preserve the displaced action explicitly. |
| The transaction grammar already has an inline `note`, and bank JSON includes it. | bob-cli `docs/bank.md:306`; `src/native/bank/grammar.rs`, `parse_row_tail`; `src/native/bank/model.rs`, `BankRow` and `row_json` | An inline implementation initially looks inexpensive, but its editing semantics need scrutiny. |
| Indented children are free notes, not bank rows. Import appends after row children and preserves existing rows. | bob-cli `docs/bank.md:306,346,451,470`; `src/native/bank/month.rs`, row insertion helpers and `append_row_lands_after_free_note_children` | A child note fits the existing document ownership contract and survives ordinary reimport. |
| Filing and navigation are coupled in the current commit callback. | bob-plugins `248-plugin-bank-category-card-actions.js`, `bankCategoryCommit` | Note saving must have its own action path. Calling ordinary filing and trying to undo navigation is unsafe. |
| The card already has New category and Subscription stages. | bob-plugins `247-plugin-bank-category-card-ui.js`; `248g-plugin-bank-category-new-stage.js`; `248h-plugin-bank-subscription-linker.js` | An in-card Note stage fits the established interaction vocabulary. A second modal is unnecessary. |
| Walk identity uses a unique bank ID, otherwise path/date/transaction text plus occurrence. | bob-plugins `249-plugin-bank-walk-model.js`, `bankWalkBuildEntries` | Keeping the transaction line unchanged also preserves the fallback identity of rows without bank IDs. |
| Ctrl+Enter opens the card only on waiting rows; the existing “Bank: set category” command also supports correction in place. | bob-plugins `248-plugin-bank-category-card-actions.js`, `bankCategoryOpenAtCursor`; `docs/bob-ledger-tools.md` | Editing a saved note must remain possible after acknowledgment. |

Plugin fragment names in this report are under `plugins/bob-ledger-tools/src/` unless otherwise stated.

**Why I would not simply append an em dash.** The current Rust and JavaScript parsers continue scanning the entire tail for fields, links, and flags even after a note marker. Their displayed note strings are derived by removing syntax, not by extracting a lossless editable field. The JavaScript `noteSpan` extends through the remainder of the tail and can include metadata and links. Replacing that span would risk deleting material the note editor does not own.

I ran the existing JavaScript tokenizer directly on synthetic rows. These are observed results, not hypothetical examples:

| Input after the amount/payee | Result |
| --- | --- |
| `[cat:: groceries] — Birthday cake! ^bank-a1` | Parsed `note` is `Birthday cake`: the exclamation mark is removed. |
| `[cat:: groceries] — Birthday cake — blue icing ^bank-a1` | JavaScript retains the internal em dash. Rust's `strip_markers_fields_links`, inspected in source, removes em dashes throughout the extracted note. This Rust result was inferred from code, not executed. |
| `[cat:: groceries] — reimbursement [acct:: savings] [[person/alex]] ^bank-a1` | Account becomes `savings`; `note` is only `reimbursement`; `noteSpan` also contains the account field and link. |
| `— Surprise!! ^bank-a1` | The row becomes flagged and its parsed note is `Surprise`. |

Consequently, “prefill with `token.note`, replace `token.noteSpan`, save” is not reliable. It can change punctuation without the user editing it, remove links, or let explanatory text change financial metadata. These problems are in scope as design constraints; this report does not implement or broadly repair the legacy parser.

A truly lossless inline editor is possible, but it requires a shared escaping or terminal-note grammar, careful treatment of existing interleaved tails, Rust/JavaScript parity, and compatibility work. Making everything after `—` opaque immediately would violate the documented ability to put tail fields in any order. A ban on punctuation or bracketed text would instead make an ordinary note box surprisingly restrictive. Neither tradeoff is warranted just to keep the source on one physical line.

**The options are not equally attractive.**

| Approach | Benefit | Cost | Judgment |
| --- | --- | --- | --- |
| Existing inline `— text`, unchanged parser | Smallest apparent patch; existing JSON field | Lossy text and metadata overlap; needs restrictions or hidden semantic changes | Do not ship a naive version. |
| Inline note with a new lossless grammar | Compact source; one field for all clients | Two parsers, compatibility rules, and legacy-tail editing become central to a small feature | Reasonable if unifying inline notes is independently a priority. |
| One labeled child note | Ordinary Markdown; isolated prose; stable parent text; readable with plugins disabled | Adds a physical line and needs recognition/ownership rules | Recommended for this request. |
| Arbitrary child bullets with no designated note | Almost no storage convention | Cannot reliably distinguish the editable note from receipts or other handwritten children | Keep as the manual escape hatch. |
| New `[note:: …]` field | Explicit machine field | Escaping, bracket limits, and visible metadata noise; duplicates existing inline note concept | Unnecessary. |
| Sidecar JSON, comments, or a separate note per transaction | Can support rich metadata and histories | Separates note from transaction; more identity and orphan handling; weak Markdown fallback | Too much machinery. |

The child-note recommendation is a judgment based on these implementation costs, not an externally established universal UX rule. If Bryan values a one-line source more than unrestricted prose, the lossless inline option is the credible alternative; it should be estimated as grammar work rather than a prompt-and-append patch.

**The interaction should feel like a brief aside.** Keep the current transaction header, date/account context, and walk position visible. Space opens a Note stage within the same modal. Focus enters the note field, existing note text is prefilled, and the insertion point starts at the end. Saving returns to the category choices with the previous highlight and the current row still selected. A quiet inline message says “Note saved”; do not show a “Filed” notice or update filing counters.

The ordinary path becomes:

```text
Ctrl+Enter → Category card → Space → type note → Enter
           → same Category card, same row → category key → next row
```

Space also needs an explicit “Add note…” / “Edit note…” button near the transaction details. The key alone is not discoverable. A visible control gives pointer users and assistive technology a usable route. It should remain available when category suggestions are unavailable: writing a local annotation does not require a successful CLI category refresh.

| Context / gesture | Recommended result |
| --- | --- |
| Category card command surface: Space | Open Add/Edit note; write nothing. |
| Category card: Shift+Space | Perform the former Space action. In filing mode, label it “File without category”; in correction mode, “Remove category.” |
| Note field: Space, letters, `/`, `+`, `=` | Insert text. Never choose a category or open another stage. |
| Note field: Enter or Ctrl+Enter | Save the note, consume the event, return to the same card/row. |
| Note field: Esc or Ctrl+[ | Cancel the draft and return one stage to the card. No write. |
| Note field: `q` | Insert `q`. Outside text controls, `q` follows Esc's one-stage behavior. |
| Category card: Esc | Close the card, retaining any note already saved. |
| Blank new draft: save | No write and return to the card. |
| Unchanged existing draft: save | No write and return to the card. |
| Existing note emptied: save | Remove only the designated note; primary button changes to “Remove note” before submission. |
| Save fails or conflicts | Keep the editor and draft open; explain the problem inline. |

Shift+Space is preferable to taking a letter or digit that a configured category might own. It also preserves a connection to the previous gesture. Do not add another no-category letter alias, reserve `q`, or replace “file without category” with “skip”: acknowledging and leaving a row waiting have different meanings. Update every normal, restricted, and correction-mode hint; the restricted card currently advertises Space as acknowledgment too.

The modifier must be recognized explicitly. Today `bankCategoryUiEventKey` returns the raw key for Shift+Space, so both Space variants would otherwise take the same action. Confine the shifted shortcut to the category stage. In note input it should never file a row.

One further detail matters: focused native buttons have their own Space/Enter activation semantics. Scope the mnemonic to the card's command surface and prioritize the focused control when a user has tabbed into a button. Otherwise Space on a focused Cancel button could unexpectedly open the note. This follows the keyboard model described by the [W3C button pattern](https://www.w3.org/WAI/ARIA/apg/patterns/button/).

**Beautiful means legible and calm here.** The note should look like transaction context, not a warning, another category, or a new task. Use one modest “Note” label and body text, with a small indentation and restrained spacing. Avoid a colorful badge per row, speech-bubble chrome, a large callout, mandatory timestamps, or an icon that competes with the category emoji. No empty note placeholder should appear on every unannotated ledger row.

Proposed card and ledger composition, using fictional transaction data:

```text
Category                                      4 of 12 waiting

$42.70   Hardware Store
Sat Nov 21 · Checking

Note
┌──────────────────────────────────────────────────────────┐
│ Replacement latch for the back gate — old one snapped.   │
└──────────────────────────────────────────────────────────┘

[ Save note ↵ ]   [ Cancel Esc ]
Saves this note; keeps this transaction waiting.
```

```text
☐  $42.70  Hardware Store                     Home
      Note  Replacement latch for the back gate — old one snapped.
```

This is a composition sketch, not a tested screenshot. Match the existing card's width, typography, focus ring, radius, and theme variables. Let the input wrap visually as it grows. After save, show the note in the same position under the transaction header so the change is visible before the user resumes categorizing. Keep the complete note readable in the ledger; long text wraps instead of disappearing into a hover-only tooltip.

The source should remain equally understandable:

```markdown
- [ ] $42.70 Hardware Store [cat:: home] ^bank-a1b2c3d4
  - **Note:** Replacement latch for the back gate — old one snapped.
```

Reading view can style this child as a modest secondary line. Live Preview should favor simple marks and natural list rendering over a block widget that hides or duplicates source text. Reveal editable Markdown normally when the cursor enters it. Source mode remains ordinary Markdown. Plugin-disabled and mobile viewing retain a useful note without decoration or an executable fence.

Use readable secondary ink, not tiny faint text. The current stylesheet applies `opacity: 0.72` to acknowledged bank rows, so children inherit dimming in Reading view. Do not compound that with another low-opacity note rule. Check the composed result in both themes and aim for normal-text contrast of at least 4.5:1, consistent with [WCAG contrast guidance](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html). A note remains useful after acknowledgment.

**The document contract should be small and explicit.** For the initial feature, support one editable paragraph per row. This is a deliberate scope adjustment from an unspecified “note”: sufficient for purchase purpose or clarification, without building an annotation journal, attachment manager, or rich-text editor. Visual wrapping is unlimited; there is no need for an arbitrary 140/280-character storage limit. If multiline text is pasted, normalize paragraph breaks to spaces in the visible draft before saving, so the stored result is evident. Do not silently truncate. Users can still hand-author additional Markdown children for longer material.

Write the designated note as the first immediate child, using the exact label `**Note:**`. All other child bullets and their order remain untouched. Recognize only this label at the direct-child level, outside fences. Do not steal a receipt bullet, a nested grandchild, an indented checkbox, or prose elsewhere in the day section. A single existing handwritten child with that exact shape is editable; multiple matching children or a hand-expanded multiline form should yield a specific “This row has a note structure the quick editor cannot safely edit” message with a source-edit route. Never silently pick the first or discard the rest.

Association stops at the next peer row or another block outside the parent's child block; it does not run until the next day heading. Recognizers must respect list nesting, blank lines, fences, and section boundaries. This boundary logic deserves fixtures; a global regex over the month note does not.

Keep existing inline `— …`, `-- …`, and flag-associated prose byte-identical. Do not automatically move it into the new child or change its meaning. Display any existing inline detail in the card as row context, separately from the new editable Note. For a row with only legacy inline detail, Space says “Add note”, not “Edit” followed by a misleading copy of lossy `token.note`. This is the main compatibility cost of my recommendation: legacy row detail and the new editable note can coexist. A future explicit conversion can unify them after a safe inline-span model exists; that conversion is not a prerequisite or an automatic migration.

There is also an API boundary to acknowledge. Today `row.note` means the parsed inline tail; neither the CLI month model nor the card's row model automatically treats child prose as that field. Do not silently redefine `row.note` to prefer the new child. If machine consumers need the new annotation in this delivery, add a clearly separate optional field such as `annotation: {text, line}` to bank list/report rows, defaulting to null, and preserve legacy `note`. Its absence in an older CLI must not block the plugin editor, which reads the current editor buffer. The current user-facing scope can ship with local note recognition and Markdown rendering without a CLI write command or JSON extension; exposing annotations in reports is a separately identified extension, not something this report claims already works.

**Reliability comes from keeping the action independent.** A note save must preserve the transaction's amount, payee, account, category, flags, acknowledgment byte, bank/custom block IDs, links, and legacy inline detail. It must also preserve the current row selection, card highlight, active walk family, walk membership/counts, and filing-session counters. Adding a child moves later physical line numbers; it must not change their identity or logical order.

A synthetic before/after scan confirmed the current JavaScript scanner finds the same two waiting transactions when a labeled child is inserted. Their transaction text and IDs are unchanged; only the following row's line number moves. Even child text containing `[acct:: savings]` does not become a field on the parent. This supports the storage choice, but does not replace end-to-end navigation tests for a new writer.

Implement a pure note edit planner and a dedicated note-save callback. Reuse the editor transaction infrastructure and row recognition, not `bankCategoryCommit`'s filing lifecycle. In particular, a note save must not call the session-record, next-waiting, completion-summary, or jump-history paths. A cache refresh is allowed; advancing the walk is not. After mutation, re-read the current row's context and refresh its captured spans so a second edit works.

Capture the file, parent identity, parent text, and designated-note preimage when the stage opens. At save time:

1. Re-resolve the parent in the current editor buffer. A unique bank ID can locate a shifted row; an ID alone is not permission to overwrite concurrent edits.
2. Verify that the parent and old note still match the captured preconditions, including the absence of a note if adding. Preserve unrelated sibling changes. For an ID-less row, use a mapped editor location plus exact parent/context checks; if mapping is unavailable and the row moved, refuse instead of searching for a plausible purchase.
3. Refuse duplicate IDs, changed parent context, ambiguous note ownership, vanished files, or concurrent note edits. Retain the draft and offer refresh/retry or copying it out.
4. Insert, replace, or remove only the designated child in one undoable editor transaction, preserving BOM, newline style, children, and EOF behavior. Revalidate parent-row invariants after planning and before application.
5. Refresh the same row/card, and report success accurately. A write already applied to the editor but not persisted must not be represented as a verified disk save; retry persistence without inserting another note.

The existing `bankCategoryResolveForCommit` allows a uniquely identified bank row to change without checking equality to its captured text. A note writer needs the stronger note precondition. Similarly, the existing `bankCategorySaveNote` catches persistence errors without surfacing them. Despite its name, it saves the month document; it is not an annotation feature or a sufficient success-reporting contract to copy unchanged.

Treat the editor buffer as authoritative for this local authoring gesture. A subprocess that rewrites a stale disk version could clobber unsaved text and would add latency to a brief aside. Existing ownership already treats Category-card mutations as the user's editor edits. Ordinary vault persistence and sync should carry the child note; no new journal or per-note Git commit is needed. Reimports preserve existing notes, but deliberate deletion of a whole transaction also deletes its child; force-restoring a transaction from the import journal cannot recover private annotations that were never journaled. This feature is not a separate backup system.

**Keyboard and focus handling are part of correctness.** Route the note stage before category hotkeys. The existing modal-wide scope swallows keys unless a stage explicitly passes them through, so a textarea and key handler alone are insufficient. Pass normal editing, clipboard, selection, Tab/Shift+Tab, and composition input through; no synthetic character-appending implementation is needed. Ignore command handling during IME composition, including the established `keyCode === 229` compatibility check. [MDN's keydown documentation](https://developer.mozilla.org/en-US/docs/Web/API/Element/keydown_event) describes the composition issue.

Consume the Space that opens the stage so it does not become the first character. Consume the save Enter and hold off category acceptance until its keyup; merely ignoring `event.repeat` is weaker than a stage-transition release guard. Rapid save/Enter sequences must never tick a row. Category refreshes must not replace the draft, focus, selection, or note-stage state. Keep the input DOM stable while typing.

Use the card's existing escape dispatch for Esc, Ctrl+[, and `q` outside text fields, following the audited `decisions:q-and-ctrl-bracket-mirror-esc` rule. Focus enters the note field, remains within the modal, and returns to the invoking Note control or stable card command surface when the stage closes. Include a proper label, visible focus, accessible action buttons, and one polite success/error announcement. These focus recommendations follow the [W3C modal-dialog pattern](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/); they do not require adding another nested dialog.

**Where the work belongs.** The primary implementation is in bob-plugins, with a narrowly scoped optional CLI projection change.

| Surface | Proposed work |
| --- | --- |
| `245-plugin-bank-category-card-model.js` and key hint helpers | Add note action; distinguish Shift+Space; revise all card-mode hints. |
| New note model/planner fragments beside `246-plugin-bank-category-card-write.js` | Recognize the owned child note and plan guarded, minimal edits. Keep these helpers pure and share them with presentation. |
| `247-plugin-bank-category-card-ui.js` and a dedicated stage fragment | Note state, accessible form, key routing/pass-through, cancellation, focus restoration, and save feedback. Use the existing stage pattern. |
| `248-plugin-bank-category-card-actions.js` | Independent save callback, persistence outcome, context refresh, and no advancement. Do not add a note flag to the ordinary filing callback. |
| `241i-plugin-bank-source.js`, bank marks model/renderers, and `styles.css` | Shared row-child association; readable Note rendering in Live Preview and Reading view; retain raw source editing. |
| `249*` walk integration | Validate invalidation and shifted line positions while preserving anchor identity and active family. Change only what those checks require. |
| User entry points | Space and a button in both filing/correction cards. Add a “Bank: edit row note” Obsidian command without a global shortcut so acknowledged rows can be edited directly. This is a plugin command, not a new CLI subcommand. |
| bob-cli `month.rs`, `model.rs`, output/decode fixtures, if API projection is included | Recognize the designated child and expose it separately; keep legacy inline `note` semantics intact. |
| Documentation and shipping | Update the bank workflow, key reference, correction/restricted-mode hints, and note ownership examples. Follow repository docs rules; build fragments, run checks, and deploy through `bob plugins sync` during implementation. |

The plugin source instructions require editing source fragments rather than generated `main.js` and keeping handwritten fragments at or below 1,000 lines. The Note stage belongs in its own fragment. This research changed no product code and performed no plugin deployment.

**What would demonstrate that the design works.** Existing tests are useful baselines, not acceptance evidence for an unimplemented feature. I ran these unchanged suites:

```sh
node --test scripts/test-ledger-tools-bank-category-card.cjs \
  scripts/test-ledger-tools-bank-category-card-ui.cjs \
  scripts/test-ledger-tools-bank-marks.cjs
```

Result: **54 tests passed, 0 failed, 0 skipped.** I also ran the synthetic tokenizer and child-insertion probes described above. No real vault transactions were inspected or modified. No Obsidian visual session, screen-reader session, Rust test suite, or implementation benchmark was run for this report.

The implementation should add behavior-focused checks:

| Test | Required observation |
| --- | --- |
| Add, edit, remove, unchanged save, blank save, Esc cancel | Exact expected Markdown; no stray label/blank child; one undo step for a real change and zero for a no-op. |
| Save on a waiting row and an acknowledged row | Checkbox, category, financial values, bank/custom IDs, links, flags, and inline detail unchanged. |
| Save on the last waiting row | No summary, no month transition, no switch to ALL, and no acknowledgment. |
| Then choose a category | Filing advances exactly once and keeps the saved note attached. |
| Space, Shift+Space, save-key release, repeated keys | Correct stage/action; no save event leaks into filing; old no-category behavior remains reachable. |
| `q`, Ctrl+[, spaces, category letters, `/`, clipboard, emoji, CJK composition | Text controls behave normally and cancellation follows one layer. |
| Note with `!`, `!!`, em dashes, brackets, wikilinks, amount-looking text, or a caret | Parent row metadata and identity unchanged; annotation text round-trips. |
| Other children, duplicate designated notes, fences, blank lines, nested bullets | Only the unambiguous direct child is edited; unsupported shapes refuse without loss. |
| Concurrent import, parent/note edit, shifted line, duplicate bank ID, changed file | Correct row retained or explicit refusal with the draft preserved. |
| BOM, LF/CRLF, EOF without newline, undo/redo | Unrelated document bytes preserved; subsequent source and walk refreshes remain consistent. |
| Read/Live Preview/Source, narrow pane, light/dark, acknowledged-row dimming | Readable note, no duplicate rendering, normal source editability, correct focus and contrast. |
| CLI missing/stale report; persistence failure | Local editor opens when safe; draft and outcome remain accurate; retry cannot append twice. |

A short real workflow trial should answer the remaining aesthetic question: annotate several purchases, cancel one, revise one after filing, and finish the walk. Observe whether the user can find the feature without remembering the new key, whether the return to category choice feels natural, and whether longer notes make the ledger too tall. That trial should refine spacing or preview density, not weaken the no-advance guarantee.

**The justified requirement adjustments are explicit.** Space changes an existing binding, with Shift+Space and a labeled button preserving the old action. A note save is a separate operation from acknowledgment. The initial editor manages one paragraph, with edit/remove and post-acknowledgment access included. The note is stored under the row, not appended to its inline tail. Legacy inline details are preserved without automatic migration. Existing JSON `note` is not silently repurposed; new annotation projection is optional additional scope. These changes make the requested interaction safer and the resulting ledger more readable while keeping the implementation focused.

**Recommended solution:** build the in-card Note stage, opened by Space or “Add/Edit note…”, with Enter saving a single labeled Markdown child note and returning to the same transaction. Move the former Space action to Shift+Space with explicit wording. Preserve transaction bytes and walk state through a dedicated guarded editor transaction, provide editing after acknowledgment, and render the note as a quiet, readable second line. This keeps the useful part of the proposal—the low-friction aside during review—and avoids turning annotation text into transaction syntax or an accidental filing action.
