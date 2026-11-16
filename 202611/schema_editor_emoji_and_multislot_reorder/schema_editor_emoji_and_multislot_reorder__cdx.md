# Bank and album schema editors: faster ordering, excellent emoji search, and a calmer design

Independent research by **cdx**, 2026-11-16. This report uses the supplied screenshot, independently inspected source, primary external references, and a small local search benchmark. No other report or finding from this research swarm was consulted. This is a design recommendation; no product code or vault content was changed.

**Recommendation:** keep Bob's guarded writers, reuse and improve its existing offline emoji engine, and replace repeated one-slot transactions with a dedicated reorder draft that previews immediately and saves once. Give both editors the same small set of interaction components, while retaining their different schema rules. A larger generic schema-builder rewrite or an autosave system would add risk without being necessary to solve the reported problems.

**The request is a good idea, with one important change in emphasis.** The expensive activity is not moving an item one position in an array. It is repeatedly entering a preview/apply transaction to express a single intention, such as “put Conclusion immediately after Intro.” Better arrows alone would leave that problem intact. Design around choosing the destination and seeing the resulting order immediately, with one explicit save after the arrangement is right.

The screenshot also reveals a hierarchy problem. A long breadcrumb dominates the title, usage information repeats, choices wrap into several rows, the active form appears below the entire schema, and a large toolbar presents many unavailable actions. An empty emoji input gives no clue that search or browsing is possible. These observations support a focused redesign, rather than merely attaching completion to the existing input.

**What the implementation already provides.** I inspected bob-cli at `0510aaf0e997ca97c10919ec21214b362a1b8c12` and bob-plugins at `91e909791a86fa30bba0b8b11c712e03a80e4dd4`. Repository paths below are relative to those repositories, not to a particular agent workspace.

| Finding | Evidence and implication |
| --- | --- |
| Emoji inputs are ordinary text controls. | `bob-plugins:plugins/bob-ledger-tools/src/242c-plugin-album-schema-edit.js`, `albumSchemaControl`, `albumSchemaAddInitialChoiceRow`, and the choice edit form. Add completion to normal inputs; the existing note-editor completer does not attach here. |
| Bob already ships a searchable offline emoji catalog. | `bob-plugins:plugins/bob-emoji/src/030-emoji-model.js`, `040-emoji-suggest.js`, `050-plugin.js`. It has aliases, tags, descriptions, ranked results, a 30-result cap, and persisted recents. Its integration is `EditorSuggest`, not a reusable input widget. |
| The album UI computes a neighboring position and replaces the draft with that one operation. | `bob-plugins:plugins/bob-ledger-tools/src/241y-plugin-album-schema-card.js:498–555`, `schemaQueueOp` and `schemaMoveSelected`. The computation uses `schemaModel`, not an accumulating proposed order. Repeating the gesture before applying does not constitute a multi-position reorder draft. |
| The backend already supports arbitrary destinations and multiple operations. | `bob-cli:docs/records.md:260–318`; `src/native/albums/update/protocol.rs`, `ops.rs`. `field.move` and `choice.move` accept final zero-based positions; the envelope applies ordered operations atomically. No new reorder CLI command is needed. |
| Bank has the same UI restriction, with domain-specific operations underneath. | `bob-plugins:plugins/bob-ledger-tools/src/248i-plugin-bank-setup-card-model.js:177–192`, `248k-plugin-bank-setup-card.js`. Category/group moves choose a neighboring anchor and open a confirmation stage. `bob-cli:docs/bank.md:175–227` documents arbitrary `before`/`after` anchors and `rule.move` positions. |
| Both editors share a strong transaction state machine. | `bob-plugins:plugins/bob-ledger-tools/src/242aa-plugin-guarded-update-session.js`, plus album and bank adapters. Successful preview is tied to revision, fingerprint, identity, epoch, and vault generation. Apply saves editors first, prevents duplicate writes, retains inverse operations, and refuses stale or unknown outcomes. Keep this machinery. |
| Both modals rebuild substantial DOM during repaint. | `241y-plugin-album-schema-card.js:141` empties and rebuilds the card; `248j-plugin-bank-setup-card-dom.js:424` does likewise. There is focus/caret restoration, but a picker and continuous drag should not depend on reconstructing their active elements. |

**The reported Apply delay is credible, but its dominant cause is not measured here.** The inspected album path is: save open editors → wait for an existing album sync if necessary → spawn the writer → preflight snapshot/planning → maintenance lock → pre-sync → fresh planning → install/verify/scoped commit → post-sync → fresh album report → return to the card. Bank uses the same transaction lifecycle and also waits for a report refresh. Sources are `242a-plugin-album-update-service.js`, `248e-plugin-bank-config-update-service.js`, `bob-cli:src/native/albums/update/run.rs`, `src/native/bank/config_update/run.rs`, and `src/native/host_catalog/txn.rs:945–1033`.

Album preview itself loads a complete snapshot and the album's record catalog, validates the schema, plans the generated index, and records read dependencies. Bank preview loads its scan, journal, and subscription references. These are meaningful correctness checks. The existing 250 ms debounce reduces calls during quick typing; it is not evidence that debounce accounts for several seconds of Apply latency. There is no measured basis here to blame network sync alone, to remove the lock, or to promise a particular end-to-end save time.

**A small experiment confirms that local emoji search is a good foundation, with quality gaps.** I called the existing exported model through `scripts/bob-emoji-test-helpers.cjs`, without opening Obsidian or changing a vault. On this Linux research host with Node v24.15.0, the index contained 1,870 entries and built in 10.008 ms. After 100 warmup searches, 1,000 searches across ten queries measured p50 1.058 ms, p95 1.733 ms, and maximum 29.064 ms. This measures the pure search helper, not input-to-paint latency, Electron, or Bryan's Mac.

| Query passed directly to the helper | Observed result |
| --- | --- |
| `fire` | 🔥 first, followed by related aliases |
| `:fire:` | No results |
| `white check mark` | No results |
| `white_check_mark` | ✅ |
| `check` | 🏁 first, then ✅, ☑️, ✔️ |
| `money` | Several appropriate results |
| `writing` | ✍️ |
| `conclusion` | No results |
| `👍` | No results |
| `smiel` | No results |

The colon result is not a defect in the existing note-editor integration: its trigger strips the colon before searching. It shows why a new input adapter must normalize whole-field queries instead of passing arbitrary input unchanged. The other examples motivate token matching, direct-glyph handling, modest typo recovery, and a small tested synonym set. They do not justify a remote semantic-search service.

I also ran five existing test files covering the emoji model/suggestions, album updates, bank config updates, and bank setup. **82 tests passed, zero failed or skipped.** This verifies the current helper/session baseline. It is not a test of the proposed UI, a real-vault Apply benchmark, or proof of screen-reader compatibility.

**Design the emoji control as an optional icon value with a searchable chooser.** Show the selected glyph in a compact button next to the label input. Clicking it or focusing its search field opens a small anchored panel. The placeholder should say “Search emoji or paste one,” not just “Emoji.” An empty query shows recents and a small useful default set; typing immediately filters descriptive rows. Each row has a large native glyph, a readable name, and a quieter shortcode or matching synonym. Eight to twelve visible rows are easier to inspect than a dense wall of tiny icons; permit scrolling through up to roughly thirty matches. Keep an explicit “No emoji” action.

The chosen emoji and the search query must be separate state. Typing `rocket` should not become the schema's literal icon. Enter accepts the highlighted result; it never also applies the schema edit. Tab should move focus normally without silently choosing a highlighted result. Escape closes the chooser first and restores focus without discarding the surrounding form. Clicking away closes it without adopting an unconfirmed query. Arrow keys navigate results only when the chooser owns them. Respect composition events. Wire this into the modal's existing capture-phase keyboard dispatcher; a child listener alone cannot reliably prevent a parent from applying or closing first.

Use the editable combobox interaction model, with an accessible name, expanded state, controlled popup, active option, and concise result announcements. The W3C pattern distinguishes exploratory navigation from accepting a value, which fits an optional icon well. A list of results can remain simple; a browsable emoji grid would require its own coherent focus model. [W3C combobox pattern](https://www.w3.org/WAI/ARIA/apg/patterns/combobox/)

Recommended search ordering is exact pasted glyph or alias, exact normalized name, matching tokens/prefixes across name and aliases, keyword matches, then conservative typo suggestions. Normalize surrounding colons and treat spaces, underscores, and hyphens equivalently for search. Match multiple query tokens across indexed fields, rather than requiring the whole phrase to appear in one alias. Use recency only within relevance bands so an old selection never outranks an exact query. Keep deterministic tie-breaking. Add a few explicit, tested domain aliases such as `done`, `draft`, `idea`, and `conclusion`; present suggestions as choices, not automatic assignments from the field label.

Reuse the existing gemoji data and its generator first. Supplement weak keyword coverage with a pinned CLDR annotation dataset if query tests justify it. CLDR supplies descriptive short names and search keywords for emoji characters and sequences; this is preferable to a second hand-maintained dictionary of thousands of names. Keep provenance and required license notices, and update through the build process rather than downloading data when a modal opens. [Unicode CLDR names and keywords](https://cldr.unicode.org/translation/characters/short-names-and-keywords)

**Unicode round trips need attention before calling the picker excellent.** One displayed emoji may contain variation selectors, skin-tone modifiers, regional indicators, keycap combining marks, or a zero-width-joiner sequence. Preserve the selected or pasted sequence, and never use `slice(0, 1)`, a UTF-16 length limit, or a “one code point” check. Emoji composition and presentation are defined in the Unicode emoji specification. Grapheme segmentation can help recognize one displayed cluster, but it is not by itself validation that the cluster is an emoji. [Unicode Emoji standard](https://www.unicode.org/reports/tr51/), [ECMA-402 Segmenter specification](https://tc39.es/ecma402/#segmenter-objects)

There is a concrete integration issue: the album UI's `albumSchemaChoiceParts` uses an emoji-oriented regex that recognizes digit keycaps, whereas Rust's `albums/output.rs:179` `split_icon` treats a leading ASCII digit as label text and otherwise accepts a broad non-ASCII-alphanumeric prefix. Bank imports that Rust splitter. Thus a UI that cleanly displays `1️⃣` does not establish that every backend read/write path will split it the same way. A strict new UI whitelist would also narrow the existing permissive label contract.

Prefer explicit structured display components from Bob, preserving the original combined label when untouched. Where a parser change is needed, make Rust's split/combine behavior authoritative and exercise both languages with shared round-trip fixtures. Preserve legacy icons and multi-character prefixes rather than silently normalizing them. An unfamiliar pasted sequence must not be rejected merely because the bundled catalog predates it. For a genuinely ambiguous legacy prefix, retain the original value and make replacement explicit. Include ✅, ❤️, 👍🏽, 👩🏽‍💻, 🇺🇳, `1️⃣`, a subdivision-flag sequence, no emoji, and legacy symbols in tests. Do not split a combined bank label in the browser and blindly write only the text part back; an edit to “Coffee” must retain ☕ unless the user explicitly clears it.

**Share implementation without making the card depend on another enabled plugin.** Extract a pure catalog/search core and a reusable input adapter from `bob-emoji`; use the same source in the note completer and schema controls. Prefer build-time generation into each consuming plugin, with a consistency check, over reaching into `app.plugins.plugins['bob-emoji']` or requiring its generated `main.js`. Disabling a separate note-completion plugin should not remove a schema editor's advertised search.

This requires a small build integration: the current fragment builder rejects paths escaping each plugin's `src/`, including symlinks. A manifest entry pointing into a sibling plugin is therefore not a drop-in solution. Generate local fragments from one canonical source with `--check` coverage, or introduce a deliberately supported shared-source facility. Do not maintain independent hand-copied search engines. Keep picker history in ordinary plugin preferences, not in album schemas; cross-plugin recent-history synchronization can wait. A third-party full picker is worth reconsidering only if a broader emoji browser is requested; it is unnecessary for these two forms and does not solve their event-routing and schema-contract problems.

**Reordering should be a small, explicit local editing session.** Selecting “Reorder fields” or “Reorder choices” opens the relevant sibling list in an ordered, vertical arrangement, within the existing modal. Do not drag wrapped choice chips as a two-dimensional grid: the visible row breaks obscure the schema's one-dimensional order. Show row numbers, full labels, restrained usage counts, and a clear insertion marker. Use stable field keys and stored choice values for identity; position is never identity.

Provide three equivalent ways to move:

1. A visible **Move to…** control offers First, Last, Before…, After…, and optionally a one-based position. Destination search uses labels, so “after Intro” takes a few keystrokes and no dragging. Positions displayed to the person are one-based; the adapter converts to the writer's zero-based convention.
2. Existing Alt+J/K gestures move the selected item repeatedly in the local draft. Add discoverable Up/Down controls and, after checking host shortcut conflicts, an equivalent arrow-key shortcut. Keep selection and focus attached to the moved item, and scroll it into view. Holding a move key should accumulate positions without waiting for Bob.
3. A drag handle offers direct manipulation with a placeholder and insertion line. Move the local item on drop; allow Escape or pointer cancellation to restore its pre-drag position. Auto-scroll only near the list edges, and avoid interpreting a small pointer movement as a drag.

Move to… is essential even if dragging is included: it is both faster for distant destinations and a pointer-only alternative. Keyboard support alone does not satisfy the need for a non-dragging pointer interaction. W3C's rearrangeable-list example also demonstrates retaining focus on the moved option and announcing its new position. Use these principles, not the example code verbatim; the example itself calls for assistive-technology testing. [W3C dragging guidance](https://www.w3.org/WAI/WCAG22/Understanding/dragging-movements.html), [W3C rearrangeable list](https://www.w3.org/WAI/ARIA/apg/patterns/listbox/examples/listbox-rearrangeable/)

The list itself is the immediate visual preview. Add a quiet summary such as “Conclusion: 14 → 2, after Intro,” and distinguish it from Bob's confirmed consequences. The footer shows **Discard**, **Undo move**, and **Save order**. Save remains disabled until the current complete draft has passed Bob's validation. The person can continue moving while validation runs. A new move immediately invalidates the previous approval. One drag, one destination selection, or one held-key burst should be one local undo step; returning to the original order leaves no dirty draft and creates no save transaction.

During a reorder session, keep add/remove/rename out of the same draft in the first release. This bounds complexity: all identities already exist, the final permutation is unambiguous, and one undo can restore the entire saved order. Entering another editor must first resolve the local reorder draft through Save, Discard, or Keep editing. The close button and Escape must not silently lose a long rearrangement. Escape first cancels an active drag or popup; a later close gesture presents an inline unsaved-order choice. This intentionally adjusts today's quick-cancel behavior for a potentially larger draft.

Show all reorderable siblings, including hidden items with a quiet Hidden badge where applicable. Keep filtering in the destination picker rather than sorting an incomplete visible subset. A drop must not inadvertently move across items omitted by a search filter. Do not allow choices to cross field boundaries, or category reordering to silently change group membership. Moving a category to another group is a separate explicit edit.

**Order has different meanings in the two editors.** The local visual preview must never pretend to know all consequences.

| Scope | Required behavior |
| --- | --- |
| Album fields | Keep all keys and values unchanged. Show Bob's `group_before`/`group_after` result: absent a choices field named `status`, moving the first choices field can change which field groups the generated index. This is not always merely cosmetic. |
| Choices within an album field | Move within that field; retain stored values, usage counts, defaults, and record frontmatter. Reflect the proposed choice order in the local list. Let Bob plan the resulting index. |
| Bank categories | Move declared categories within the selected group initially. Show the backend's derived hotkey shifts; do not silently pin every hotkey to suppress them. Hidden categories and undeclared built-ins need explicit handling. |
| Bank groups | Move members as a block, preserving their internal order. Do not treat the protected Money moves group or the synthetic Hidden section as ordinary reorderable groups. |
| Bank rules | Reuse the same controls, but clearly say that order changes future rule precedence. The naming engine uses the first configured matching rule. Keep the guarded `index`/`match_was` semantics when compiling a batch. |
| Bank accounts | Do not add drag handles. The first account supplies attribution for rows without an explicit account, and the guarded writer refuses account moves/default changes. A general reorder widget must respect this boundary. |

These constraints are documented in `bob-cli:docs/bank.md:116–227`, `docs/records.md:275–318`, `src/native/bank/naming.rs:1–18`, and `src/native/albums/update/ops.rs:188–205,2152–2170`. They are reasons to share components and transaction mechanics, not to flatten the two editors into one generic data model.

**A calmer layout makes the changes discoverable.** Keep the album name prominent, with the ancestry breadcrumb smaller and truncated independently. Put counts in one quiet line. Separate navigation from editing: a compact field list at the left, the selected field and its choices in the main area, and a persistent status/action footer. On a narrow desktop window, the same sections stack; selection reveals the local editor immediately below its row. Existing mobile read-only behavior can remain in this scope.

An illustrative wide layout for the screenshot's Section field is:

```text
SASE Blog Zettel                                      Schema     ×
dev › SASE › sase_blog                           2 records

FIELDS                 SECTION — choices                  Reorder
Status    Required     01  🪝 Intro                     0 records
Claim     Text         02  🏁 Conclusion                0 records  ⋮
Section   Choices      03  🧱 What is SASE?              1 record
+ Add field            04  📜 Prompt language (macros)   1 record
                       …
                       + Add choice

                       Label   [Conclusion                     ]
                       Emoji   [🏁 ▾]   Search or paste an emoji

Order preview: Conclusion moved from 14 to 2, after Intro
Bob validation: Ready · consequences available
Undo move                       Discard              Save order
```

This is a layout sketch, not a screenshot of an implemented feature. In normal editing, render choices as readable rows with a compact icon well, label, quiet count, and overflow action. In reorder mode, the same rows gain numbers/handles rather than changing into unfamiliar objects. Hide irrelevant actions instead of maintaining the screenshot's wall of disabled buttons. Keep YAML in an Advanced/overflow action with a visible escape route for invalid schemas. Place usage counts away from the choice label so “Intro 0” cannot be mistaken for an authored name.

Use Obsidian theme variables for surface, text, border, focus, and accent. Reserve accent color for selection, insertion, and the primary action. A thin border and restrained selected-row tint communicate structure more clearly than making every surface a gray button. Keep glyphs large enough to recognize, rows comfortable to target, and keyboard focus visible independent of color. A short position animation can help track the moved item; honor reduced motion and never delay interaction until the animation ends. At 200% zoom and in a 375 px-wide window, labels should wrap and the footer remain reachable without horizontal scrolling. Native semantic lists with row controls are a reasonable default; do not apply listbox roles to rows full of independently focusable controls without designing the corresponding interaction model.

**Implement the draft as order intent, then compile once for the existing writer.** Maintain `baseOrder`, `draftOrder`, stable selection, and a local undo history for one sibling collection. A single item moved fourteen positions is one move operation, not fourteen intermediate operations. For several rearrangements, compile the final permutation deterministically by simulating each emitted move on a working copy; omit redundant moves and assert that simulation exactly reproduces the draft. A simple prefix-fixing algorithm is sufficient for these list sizes; minimizing every operation with a sophisticated diff is not needed initially.

For albums, emit existing `field.move` or `choice.move` operations. For example, moving the stored choice `conclusion` to first emits `{ "op": "choice.move", "field": "section", "value": "conclusion", "position": 0 }`. For bank categories/groups, choose stable before/after anchors from the simulated canonical order. For rules, update the guarded index as earlier moves change the working sequence; never reuse every rule's original numeric index. Submit the entire operation array against the base fingerprint, dry-run it, and apply the exact successfully previewed envelope. Do not add a parallel UI YAML writer.

Separate a small pure reorder controller and emoji input from the shared guarded session and the two domain adapters. The UI controller projects intent; Bob remains the source of validation, hotkeys, grouping, affected counts, derived keys, and all writes. Patch rows and status areas in place rather than clearing the whole modal on search input, pointer movement, or preview completion. Stable input nodes preserve caret, composition, popup ownership, selection, and scroll more reliably than reconstruction.

Use at most one running read-only preview plus one latest queued draft per editor. The current session discards superseded responses, but the inspected request path does not itself bound concurrent preview processes. Debounce settled typing/keyboard bursts, and launch preview after a drop or chosen destination rather than on every pointer movement. If a stale preview is already running, let it finish and then validate only the newest draft, or cancel it only through a known-safe read-only cancellation path. An Apply process has different semantics and must never be treated as disposable search work.

**Make reliability visible without burdening ordinary edits.** The local order can respond immediately while the status reads “Checking changes…”; it must not claim the vault is already saved. After Bob confirms the committed result, show success even if a subsequent UI report refresh is still pending, but hold additional writes until the fresh report is available. Today the service awaits that refresh before returning; splitting those observable states is a possible adapter improvement, not an existing feature. Pre/post-sync phase labels require actual progress signals; do not fabricate them from elapsed time or display a made-up percentage.

Retain the existing protections: save every affected open editor before Apply; reject stale fingerprint/generation; let double clicks share one apply flight; retain a draft on refusal; offer explicit refresh and re-preview after an external change; reconcile unknown timeout outcomes before retrying; and retry only vault sync after a confirmed saved-local/post-sync failure. Saved Undo should continue using Bob's returned inverse operations and the saved fingerprint. Local Undo move and Undo saved change should be visibly distinct. Do not silently apply retained numeric positions against a changed schema; a new order needs a fresh review, especially if its target or anchor disappeared.

**Measure performance before changing transaction semantics.** Instrument preview and Apply with correlated local timing spans: editor saves, queue/wait time, subprocess startup, snapshot/scan, plan, lock wait, pre-sync, install/verification/commit, post-sync, report refresh, and UI paint. Record durations and collection sizes rather than sensitive bank labels. Benchmark representative synthetic vaults first; observe a normal authorized edit for the real user-vault case rather than generating benchmark writes there.

Use these as proposed acceptance budgets, not measured promises:

| Interaction | Proposed target and method |
| --- | --- |
| Warm emoji input to filtered paint | p95 below 50 ms, including DOM work; no subprocess or network request. |
| First emoji chooser open | Below 100 ms after editor resources are ready; measure cold data/index setup separately. |
| Keyboard reorder to visible position | p95 below 50 ms; no writer call per repeated key. |
| Drag preview | Remain within the frame budget on the supported Mac/Obsidian build; batch pointer work with animation frames. |
| Settled authoritative preview | Aim for p95 below 500 ms including debounce on a representative local fixture; investigate if real data cannot meet it. Editing must remain responsive regardless. |
| Apply acknowledgement | Immediate visible busy state; exactly one writer transaction and one final revalidation per batch. Measure actual wall time before setting a total-save SLO. |
| Long distant move | One destination selection or one drag, one confirmed preview, one Apply; no intermediate commits. |

The response/frame budgets are informed by browser performance guidance, while the exact thresholds above are proposed product criteria. [web.dev response and animation guidance](https://web.dev/articles/rail)

Batching removes repeated transaction cost even if a single transaction still takes seconds. If measurements then show scanning dominates, investigate safe snapshot/cache reuse or a narrower dependency-aware plan for selected operations, retaining fresh apply-time validation. If sync dominates, treat changing the commit/sync lifecycle as a separate architecture decision with recovery tests. Do not make “skip sync for presentation edits” the first optimization: ordering may change grouping, hotkeys, or rule precedence. A daemon, generalized schema compiler, or database-backed editor is not justified by the evidence collected here.

**The requirements I would adjust are explicit.**

- Replace “move up/down multiple spots” with “choose any destination, preview continuously, and save an entire reorder once.” Keep the familiar arrows as local nudges.
- Make non-dragging Move to… and keyboard navigation part of the core feature. Dragging is a useful additional input method, not the sole solution.
- Require emoji search in both add and edit forms, including initial choices in a new field and bank category icons. Do not assume the existing note-editor completer covers ordinary inputs.
- Include Unicode label round trips and preservation of existing values as release requirements. Do not silently impose a new one-character schema restriction.
- Distinguish local visual preview from Bob's authoritative consequence preview, and interactive responsiveness from durable-save latency.
- Limit the first transaction expansion to reordering existing siblings. Defer mixed add/remove/rename/reorder batches, multi-selection drag, cross-field moves, a universal emoji browser, and mobile writing support.
- Preserve account/default and built-in group restrictions. Shared aesthetics do not authorize new schema semantics.

**A bounded implementation sequence is practical.** First add timing spans, query fixtures, and round-trip fixtures; use them to settle the parser/structured-display boundary. Next extract the shared emoji core and attach a small chooser to existing forms, with keyboard event tests. Then implement the local reorder controller, Move to…, repeated nudges, local undo, deterministic operation compilation, and one guarded batch save. Add drag handles against that same controller and simplify the modal layout; dragging should introduce no separate persistence path. Finally use measurements to remove proven redundant work and validate the full interaction in Obsidian. Follow the plugin repository's source-fragment build rules, regenerate entrypoints, run its prescribed checks, and deploy through `bob plugins sync` when implementation is authorized.

A useful acceptance walkthrough is Bryan's actual example: add a Section choice with a searched emoji, find and select an existing choice with a long label, move Conclusion directly after Intro, make two more adjustments before saving, undo the last adjustment, inspect the final order and Bob's consequences, then save once. Repeat in bank setup with a move that changes a derived hotkey. Add cases for no-op return to the starting order, first/last boundaries, duplicate display labels with distinct identities, 100 choices, hidden entries, delayed/out-of-order previews, a dirty Source pane, an external edit while preview runs, rapid double Apply, lost apply response, post-sync failure, and refresh failure after a confirmed commit. Verify keyboard-only operation, VoiceOver in the target desktop environment, light/dark themes, zoom, and reduced motion. Assert preserved frontmatter values/comments and exactly one transaction, not just that rows visually moved.

The largest remaining uncertainties are the actual timing breakdown on Bryan's machine, desired catalog coverage beyond the existing 1,870 entries, the target Obsidian/Electron accessibility behavior, and the complete compatibility surface of Rust's permissive icon splitter. None blocks the recommended local-draft design; each has a concrete measurement or fixture test above. I did not profile a live Obsidian session or mutate the real bank/album data, so the latency diagnosis remains a source-backed hypothesis rather than a measured root cause.

**Recommended solution:** ship a shared offline emoji chooser backed by Bob's improved search core, together with a dedicated reorder draft for existing fields, choices, bank categories/groups, and appropriately labeled rule order. Make Move to… the dependable fast path, repeated keyboard moves immediate, and dragging an equivalent convenience. Use stable rows, clear destination feedback, a quiet persistent footer, and one exact-preview guarded save. Preserve the backend's identity, validation, grouping, hotkey, and sync guarantees; optimize measured costs after eliminating the needless per-slot transactions. This delivers the requested convenience and beauty with a small, understandable interaction model and substantially less implementation risk than a wholesale editor rewrite.
