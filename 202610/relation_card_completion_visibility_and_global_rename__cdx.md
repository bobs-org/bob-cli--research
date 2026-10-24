# A reliable relation card: completion, hidden descriptions, and global rename

Independent research by **cdx**, 2026-10-24. This report was developed without reading or obtaining the findings of the other researchers in this swarm. This is a design recommendation, not an implementation or an approved change to existing contracts.

**Recommendation: proceed, with a clearer separation between choosing a description, editing this relationship, and managing the shared description library.** The reported completion problem has a concrete cause in the current code. Ctrl+N/P is a good addition, but changing key bindings alone will preserve the bug. The central fix is to make list navigation change selection without changing the search query. Keep descriptions as readable text on LINKS lines; add a small, synced preferences journal for visibility, and implement global rename as a previewed, verified operation owned by bob-cli.

The principal requirement adjustments are:

| Requested behavior | Recommended interpretation or adjustment | Reason |
| --- | --- | --- |
| Disable/hide descriptions | Call it **Hide from suggestions**; never disable the relationship itself. | Relations remain visible and meaningful in task history. |
| Tab completion | Ctrl+N/P and arrows navigate; Tab accepts instead of cycling and refiltering. | Navigation and commitment become predictable. |
| Ctrl+D hides | Support Ctrl+D only while an existing description is explicitly selected for browsing; otherwise preserve native text editing. | Ctrl+D is forward-delete in a macOS text field. |
| Show all and re-enable | A visible **Include hidden** control plus Ctrl+Shift+H; **Unhide** is the inverse action. | Recovery must be discoverable without remembering a shortcut. |
| Rename all tasks | **Rename everywhere…** is separate from changing the current relation’s description, and explicitly includes history. | A field edit must never unexpectedly rewrite other tasks. |
| Create hidden with `||` | Treat it as “use this description and hide its shared suggestion on successful capture.” | Hiding is a property of a description, not of one edge. |
| Temporary relationships | Interpret the request as temporary/one-off **wording**, not expiring links. | Automatic expiry would be a separate feature and contradict retained relation history. |
| Reliable rename across hosts | Guarantee a verified local/synced snapshot; detect old names that return from offline hosts. | A per-host preferences journal does not provide a distributed transaction over Markdown files. |

**The screenshot matches a query/selection feedback loop.** The supplied screenshot shows `inspired by` in the field, one remaining chip, and the instruction “Tab cycles suggestions.” In the Mac model, `cycleRelationLabelSuggestion(by:)` advances an integer index, copies that candidate into `authoredLabel`, and calls `fetchRelationLabelSuggestions()`. The fetch submits that new full label as the query. The backend filters suggestions by prefix/substring, removes the matching historical row, and inserts a typed row for the same description. When the reply arrives, the list often has one entry and its selected index is clamped to zero. Tab can now only select that same entry. Fast repeated Tabs can traverse the old list before a reply arrives, explaining the reported timing sensitivity. [M1][C1]

There are two adjacent problems in that path. The cycling function does not skip `disabledReason` or empty-replacement rows, and the card does not visually distinguish its selected chip: its enumerated `index` is not used for selection styling. A fresh empty-query list also starts with index zero and advances before selection, so it can skip the first real suggestion. These are source-level findings, not a claim that every symptom has been reproduced on macOS. [M1][M2]

The existing `testRelationCardTabCyclesSuggestions` creates a model with fixed preview candidates and no process client, then calls the cycle methods consecutively. It proves arithmetic over an unchanged array, but never allows a completion response to replace that array between key presses. Other tests already protect pending Return and stale responses; keep those protections when changing selection. [M3]

I also ran a read-only probe against a temporary three-description vault using the installed `bob 0.3.1` binary. The fixture was removed afterward; the real vault was not touched:

| Completion probe suffix after `New task ~tasks:target` | Returned descriptions |
| --- | --- |
| `|"` | `follow-up of`, `inspired by`, `see` |
| `|"follow-up of` | only typed `follow-up of` |
| `|"inspired by` | only typed `inspired by` |
| `||oneoff` | no completion context/candidates |
| `||"one off"` | no completion context/candidates |

These observations reproduce the backend collapse that the Swift cycle triggers. They do not establish the installed binary’s exact source commit. The current parser source also confirms that it consumes only one separator and treats a second pipe as part of an invalid label. [C2]

**The relation card should become a small, calm description chooser.** Replace horizontally scrolling chips with a vertical list, about five visible rows, inside the current card. Keep the mint relation accent, but use it for the selected row and the relation phrase rather than a redundant syntax preview. Use one knot icon rather than the current combination of a knot and a bidirectional arrow. Relations are directed: the source/target sentence should make that direction unmistakable, including for `~~`.

A conceptual layout, with illustrative counts:

```text
🪢 Relation                                  Include hidden  ⌃⇧H
Buy new SSD for athena
  inspired by → What was athena doing at 07:57?

[ Search descriptions or write a new one                       ]

▸ inspired by                                  8 uses     ⋯
  follow-up of                                12 uses     ⋯
  see                                          4 uses     ⋯

⌃N / ⌃P move · Tab / Return use                 Hide ⌃D
                                         Cancel    Use description
```

This is an interaction sketch, not a final pixel specification. Keep the card’s top edge and input position stable as results arrive; reserve a bounded list region rather than moving the surrounding capture controls. Long task titles can wrap or truncate with an accessible full value. A selected row needs a shape/background and accessible selection state, not color alone. Counts are secondary and should say “uses”; one task can contain several labelled edges. Hidden rows have an eye-slash symbol and **Hidden** text when included, with sufficient contrast and no strikethrough that suggests a deleted relationship.

Remove the always-visible `Inserts |"…"` line from the normal user flow. The sentence already explains the result. Exact syntax belongs in help or an optional details view; show it where it explains `||` or an error, not as the card’s main feedback. Use the button label **Use description**, which edits the draft, while **Capture** remains the later vault write.

The interaction should follow an editable combobox model: exploring suggestions can leave the typed input intact, Enter accepts a selected value, Escape restores/cancels without accepting it, and ordinary text editing remains available. W3C describes these distinctions for web comboboxes; they are useful design guidance here, not a prescription to put ARIA attributes into SwiftUI. [W3C combobox pattern](https://www.w3.org/WAI/ARIA/apg/patterns/combobox/)

| Input | Behavior in the description card |
| --- | --- |
| Type, paste, delete | Edit `queryText`; clear explicit selection; request new results. |
| Ctrl+N / Down | Select next eligible historical description; from no selection choose the first. |
| Ctrl+P / Up | Select previous eligible description; from no selection choose the last. |
| At list ends | Clamp, rather than wrap invisibly. Both key pairs behave the same. |
| Tab | Accept selected description; if none is selected, accept the first eligible historical match. If none exists, leave normal focus traversal available. |
| Return | Use explicit selection; otherwise validate/use typed text. Empty text keeps a plain relation with no description. |
| Shift+Tab | Normal backwards focus traversal; no reverse completion cycle. |
| Escape | Cancel the card and restore its saved draft/caret or preceding picker. |
| Ctrl+Shift+H | Toggle Include hidden while preserving query and selection by key where possible. |
| Ctrl+D in browse selection | Hide the selected visible description, or unhide the selected hidden description. |
| Ctrl+R in browse selection | Open Rename everywhere… for that description. |
| Click a row | Use that description, matching keyboard acceptance. |
| Row menu / visible action | Hide, Unhide, Rename everywhere…; every action has a mouse and accessibility path. |

Keep known descriptions separate from the “Use new description ‘…’” action and invalid-input message. Ctrl+N/P should traverse historical suggestions, not a synthetic typed validation row. Default browsing excludes hidden rows and rows that cannot be inserted. Include hidden intentionally admits hidden rows: hidden means usable but omitted by default, whereas `disabled_reason` means not insertable. A management view must still expose disabled historical entries for repair/rename through its ordinary accessible controls.

Apple documents Ctrl+D as forward-delete and Ctrl+N/P as line movement. Therefore Ctrl+D must not become a global text-field hide command. An explicit row selection arms library actions; typing or moving the text caret returns to editing mode. Show the selected-row action in the footer. Do not swallow Command+A/C/V/X/Z or IME composition, and do not hijack Control+Option combinations used by VoiceOver. [Apple keyboard shortcuts](https://support.apple.com/en-us/102650)

**The model needs independent query, selection, and acceptance state.** A suitable state shape is `queryText`, `candidateSnapshot`, `selectedKey?`, `includeHidden`, `promptID`, `requestGeneration`, `catalogRevision`, and an optional pending acceptance bound to those values. Backend candidates need stable keys; replacement text and array offsets are unsuitable identity because spelling, visibility, or ordering can change.

Navigation changes `selectedKey` and the sentence preview only. It does not edit `queryText`, launch a subprocess, reset pending validation, or rewrite the draft. A genuine edit makes old results visibly stale and ineligible for acceptance until refreshed. Requests must match prompt ID, draft snapshot, query, visibility mode, and generation. Preserve a selection by key on harmless refresh, never merely by its old index. If the selected key disappears, clear it; do not silently commit the row that inherited its position.

Accepting a known suggestion uses its backend-authored replacement from a current snapshot. Accepting typed text uses a current backend validation result, preserving the current pending-Return behavior. Revalidate operation scope for hide and rename with a revision token. Ignore auto-repeat for mutation keys; one held Ctrl+D must not hide a sequence of rows as each disappears. Keep a busy state per action and make retries idempotent. The normal capture editor should not regain focus or submit while a management operation is still pending.

**Hide should be a shared suggestion preference, not data deletion.** A hide leaves every LINKS and LINKED FROM description unchanged. It does not remove an edge, alter status/freshness, affect dependencies, conceal task rows, or change relation rendering. Typing a hidden phrase or explicitly selecting it in Include hidden remains allowed and does not automatically unhide it. This resembles Bob’s accepted theme-hide behavior, although relation defaults should suppress hidden historical suggestions for both empty and nonempty queries; direct typed use remains available. [C3][C4]

When the user types the exact name of a hidden description, the typed-use action should say **Existing description · Hidden**. Do not present it as a newly created label. Similarly, an exact visible match should retain its usage count and management actions rather than losing all catalog metadata when the typed row replaces the historical row.

Use one preferences namespace such as `.bob/relation-labels/<host>.jsonl`, adapting the theme journal’s deterministic fold and single backend writer. Events are hide, unhide, and rename/state-transfer; relation visibility must not share theme keys. Add the directory to the vault sync allowlist, and invalidate client caches when its files change. Keep historical hidden entries discoverable even when their use count falls to zero by retaining their names in journal metadata. The library is authored-label observations plus retained preference records; generated mirrors must never double the use count. [C4]

Use a backend-defined key compatible with existing Rust grouping: collapse whitespace, strip one trailing colon, and use locale-independent lowercase. Preserve display spelling. Audit the current Rust `to_lowercase`, ASCII-only exact-row dedupe, and JavaScript `toLocaleLowerCase` differences; clients should consume the backend key, not invent their own. Do not quietly introduce NFC normalization or full Unicode case-fold equivalence in this feature: that could merge existing labels that currently differ. Add multilingual identity vectors and deterministic display-spelling tie breaks. [C1][C3][P1]

Hiding an existing suggestion is an immediate library operation. Show **Hidden from suggestions · Undo** and update the list after success. Cancelling the surrounding draft does not undo an explicitly completed library edit; that scope should be visible in the feedback. Unhide appends the inverse preference. A delayed Undo should check the expected preference revision instead of overwriting a newer change from another client.

For a new typed description, provide a small **Hide from future suggestions** option. It stages a capture intent; it does not create a journal entry while the card is open. This distinction lets Escape and failed captures remain side-effect free.

**`||` is workable, but its global effect must be unmistakable.** Keep the existing single-pipe grammar and add a two-pipe separator in the Rust parser. The same meaning applies to both relation directions:

```text
Task ~tasks:target|see
Task ~tasks:target|"inspired by"
Task ~tasks:target||"one-off workaround"
Task ~~tasks:source||"one-off workaround"
```

The stored Markdown remains `one-off workaround [[…]]`; the second pipe is an instruction to hide a shared description, not a character in the label and not an edge annotation.

| Existing description state | `|description` | `||description` |
| --- | --- | --- |
| Unknown | Create/use; visible by default. | Create/use; hidden after successful capture. |
| Visible | Use; retain visibility. | Use and hide everywhere in suggestions; warn about existing usage. |
| Hidden | Use; remain hidden. | Use; remain hidden; no redundant hide event. |

For a new label, show quiet eye-slash feedback: **Hidden from future suggestions**. For an existing visible label, show an amber inline warning: **“inspired by” already labels 8 links across 6 tasks. Capturing will hide this description from suggestions everywhere. Existing links stay unchanged.** Offer **Keep visible**, which asks Bob to rewrite `||` to `|`, and make the capture action’s effect explicit, for example **Capture & hide description**. An already-hidden name gets neutral feedback, not another warning.

The warning comes from the backend plan and includes a stable code, key, counts, and before/after visibility. Show it on the card, aggregate capture preview, and final CLI JSON/human result. A warning buried only in a toast after capture is insufficient. CLI use should not require an interactive question: explicitly supplying `||` authorizes hiding; human output must show the scope warning before the write, with structured warnings in JSON. Shell examples must quote the whole draft so the shell does not interpret `||` itself.

Preview has no side effects. Add the preference event to the same capture write set as notes and mirrors. Calling a standalone hide command when the card closes, or appending a journal event after the note commit without rollback, would violate aggregate capture behavior. The existing staged text-file batch is an appropriate starting point, but the new journal path needs same-host serialization, before-image checks, and error recovery. Test note failure, journal failure, and process termination separately; rollback on a caught error is not crash atomicity. [C5]

Within a multi-item draft, collapse repeated hide requests for the same key to one effective change. A single-pipe use never unhides, so mixed `|name` and `||name` consistently finish hidden regardless of item order. Resolve existence and warning counts against the pre-capture catalog; a second new use in the same draft should not suddenly be described as pre-existing history. Different spelling variants resolving to the same key receive one warning.

If another operation makes a supposedly new name an existing visible label between preview and capture, an upgraded GUI should receive `preview_changed` and display the newly expanded effect before retrying. A raw CLI invocation can warn and apply using its fresh plan. This is a targeted check on changed global scope, not an extra confirmation for every capture.

Handle incomplete `||`, quoted multiword labels, both separators’ byte spans, Unicode cursor offsets, and existing whitespace-before-pipe rewrite behavior together. An unfinished second pipe should keep the card open without a red invalid-label flash. Three pipes are an error. Empty `||` on submission is incomplete; do not write an empty preference. Do not reinterpret Markdown table text, fenced examples, URL pipes, or unrelated tokens. Update parse, completion, rewrite, syntax highlighting, dry-run, and commit contracts together. [C2]

**Global rename is the highest-risk part and deserves a dedicated operation.** Today, relabelling one `(source, target)` edge is already supported. It is not a global description rename. Existing descriptions are free text, not relation-type objects with IDs. Preserve that model: a new database of UUID-backed relation types would require Markdown migration and obscure hand editing without helping the immediate completion problem. [C3]

Use **Rename everywhere…** in the selected row’s menu and Ctrl+R while browsing. Open a small sheet with old name, new name, current hidden state, and backend-calculated scope:

> Rename “follow-up of” to “continues” on 12 links across 9 source tasks and 6 notes, including 3 archived links. Update 10 stored backlink labels. Hidden state will stay hidden.

Counts here are illustrative. “Links,” “tasks,” “notes,” and “backlink labels” must be separate quantities. Show actual affected files in expandable details. Editing the current relation’s field never implies this operation. The draft stays intact when the sheet is cancelled; after success, refresh candidates and explicitly replace any matching description in the current draft through backend-provided rewrites. Mark other stale previews for refresh.

Define “same description” by the canonical key above. Rename every corresponding case/whitespace variant to the requested canonical display spelling. A case-only rename is allowed. A normalized identical spelling is a no-op. An existing different destination key is a collision, refused by default; offer a separately named **Merge descriptions…** action or CLI `--merge`. Never silently merge. For explicit merge, keep the destination’s visibility as shown in preview; for rename to an unused key, transfer the source’s visibility. Preserve edges and their order.

The scan must cover all task-bearing notes, all statuses, `done/`, historical daily notes, nested projects, references, and tasks without block IDs. Do not derive the rename scope solely from the resolved live graph: a valid authored label beside an unresolved target still needs renaming. Count labels in source LINKS entries, and derive or update corresponding stored LINKED FROM descriptions without treating mirrors as independent uses. Existing consumers already have different discovery and ranking paths, so the new catalog must state its scope explicitly. [C1][C6][P1]

This deliberately extends existing write policy. Normal relation capture and reconcile treat `done/` and certain historical notes as read-only, and generally maintain mirrors only where writable. A literal “rename everywhere” cannot reuse that narrow policy unchanged. The dedicated rename command must be explicitly permitted to change **description spans only** in historical LINKS and valid stored LINKED FROM lines. It must not reopen tasks, mint IDs, prune edges, reorder entries, rewrite task prose, or run unrelated status reconciliation. Include this exception in the relation contract before shipping it. [C3]

Keep existing exclusions for `_templates`, `_generated`, `_conflicts`, hidden metadata directories, and fenced examples; they are not authored task records in the live catalog. State these exclusions in preview/help. Source aliases accepted by the current parser also need coverage: rename semantic labels in accepted legacy entries, not a blind substring replacement. A known inverse phrase in a rendered backlink remains presentation-only; renaming to a custom phrase may legitimately fall back to generic directional copy. [C3]

The safe operation is:

1. Build a fresh, strict scan and preview with a revision/fingerprint covering the selected key, preference state, target files, and relevant file inventory. Completion may tolerate incomplete data, but “rename everywhere” must not report success after silently skipping unreadable notes or malformed relation lines that prevent proving coverage.
2. Acquire Bob’s existing maintenance lock and the necessary write coordination; pre-sync through the established rename workflow unless explicitly offline. The GUI must compare the new scope with the approved preview and refresh it when changed.
3. Check snapshots immediately before writing; build exact parsed label-span edits and the preference-state move. Reuse parsing and transaction primitives, not a whole-vault string substitution.
4. Stage the complete write set, keep before-images, and use atomic per-file replacement. Recover or roll back known writes on failure. A persistent transaction receipt is needed if recovery after process death is part of the reliability claim; per-file atomic rename alone cannot make a multi-file update atomic.
5. Rescan and verify: old key absent from covered source entries, new key has the expected uses, edge identities/counts unchanged, backlink labels agree, and unrelated bytes are preserved. Report all touched paths.
6. Record a scoped vault commit using the existing application rename machinery, then sync. Return local-commit and sync states separately: post-sync failure is **renamed locally; sync pending**, not “nothing happened.”

The theme rename implementation already provides a close precedent: maintenance locking, pre/post sync, fresh planning, snapshot checks, atomic file writes, journal transfer, verification, a scoped Git commit, and reporting for names that reappear. Reuse its proven components and vocabulary, but do not assume it supplies relation coverage or crash recovery automatically. [C7]

Obsidian adds an extra concurrency boundary: its relation index overlays unsaved editor text. A subprocess sees disk. The Obsidian command should flush the current editor and coordinate or refuse affected dirty editors before preview/apply; a disk hash cannot protect text that has not reached disk yet. External CLI operations should honor available editor/quiet-window coordination and refuse uncertain affected files. The Mac client cannot independently inspect Obsidian’s vault. [P2]

Do not promise instantaneous global rename on offline machines. Pre-sync/post-sync covers the reachable snapshot, not future offline edits. Detect reappearance of old names after sync and offer to repair remaining occurrences, following the existing theme model. Avoid silently replaying historical rename events as aliases in v1: that requires conflict rules for cycles, chained renames, name reuse, and concurrent rename-to-different-target operations. If seamless offline convergence becomes essential, stable IDs and a migration can be revisited as a separate architecture change. [C7]

Undo should be scoped. Hide/unhide gets an immediate inverse operation with revision checks. A rename can expose a transaction receipt and restore exact changed spans when their post-images still match; otherwise show the conflict rather than overwriting later edits. A reverse global rename is not a safe undo after a merge or after new uses have appeared. Keep the existing scoped-commit recovery route available in the CLI.

**One backend service should support all three interfaces.** Introduce a narrowly defined group, tentatively `bob relation-labels`, whose members inspect or manage the shared description catalog. This avoids making `bob relations` ambiguously mean edge editing as well as library management. Suggested commands—not existing commands—are:

```sh
bob relation-labels list
bob relation-labels list -a -f json
bob relation-labels list -H
bob relation-labels hide "inspired by"
bob relation-labels unhide "inspired by"
bob relation-labels rename "follow-up of" "continues" -d
bob relation-labels rename "follow-up of" "continues"
```

A bare group may default to the read-only list. Public options need short aliases and alphabetic help ordering; examples include `-a/--all`, `-H/--hidden`, `-d/--dry-run`, `-f/--format`, and `-m/--merge`. Keep capture protocol endpoints as their existing frozen siblings rather than inventing a subcommand under `bob capture`. These choices follow the audited CLI rules.

Make catalog data additive: `key`, `label`, `usage_count`, `source_task_count`, `hidden`, `existing`, and an insertion-disabled reason separate from visibility. Include a catalog revision and capability/version information. Parse results need a hidden-on-capture intent; completion needs backend-authored replacements for both visibility choices and a way to request hidden candidates; dry-run/results need structured preference effects and warnings. Exact matches should carry full catalog metadata even when represented by the typed-use action.

The Mac app remains a thin client: it renders rows/warnings, tracks selection and request generations, and submits backend replacements. It must not duplicate normalization, quote rules, usage counts, warning scope, or Markdown writes. Preserve `schema_version` compatibility through optional fields and explicit feature capabilities. The existing `relation_grammar` marker only tells the current app that relation grammar exists; it is not sufficient evidence that double-pipe effects or management commands are supported. [C8]

Old backends should continue to support ordinary relations. Disable new management controls and hidden-on-create UI when unavailable; never silently downgrade `||` to `|`. Because hiding an existing phrase changes shared preferences, test old-app/new-backend behavior explicitly. Prefer capability-aware invocation and a structured unsupported-feature response where the client cannot present the effect; direct CLI use still gets the backend warning.

For Obsidian desktop, add **Manage relation descriptions** to the command palette and the relation stage’s contextual actions, invoking the same bob-cli service. Reuse the existing `api.themes` subprocess/cache/notification pattern where useful. Keep the live relation index for graph display and unsaved local edge rendering, but stop using its separate locale-sensitive suggestion catalog as the authority for global labels. Invalidate both relevant caches after a successful operation. On mobile, synced hidden state can have a tested read-only mirror; global writes should clearly explain their desktop/backend requirement instead of inventing a separate writer. [P1][P2][P3]

**Acceptance should test user journeys and failures, especially timing.** The following are release criteria, not evidence that these tests have already passed:

| Area | Essential checks |
| --- | --- |
| Completion regression | Three labels; pause long enough for a response between every navigation key; slow and rapid input yield the same selected sequence. Navigation sends zero new completion calls and leaves query text unchanged. |
| Focus and selection | First/last selection from no selection; clamped boundaries; typed value vs selected value; invalid and hidden skips; same-key selection survives reorder; disappearing key clears selection; Escape restores the draft. |
| Async acceptance | Older response arrives last; two identical queries in different prompt instances; query/include-hidden changes during a fetch; Return before validation; dismissal during pending acceptance. |
| Hide | Default lists omit hidden; All exposes them; explicit typed hidden use stays hidden; unhide restores discovery; no task bytes change; zero-use hidden names remain manageable; failed hide leaves the row and explains why. |
| Keyboard and access | Ctrl+D edits text outside explicit selection; Ctrl+D auto-repeat performs one mutation; Ctrl+N/P and arrows agree; keyboard-only recovery works; VoiceOver announces selection/count/hidden state; IME composition and Full Keyboard Access work. |
| Grammar | `~` and `~~`, `|` and `||`, quoted multiword labels, quoted note paths, Unicode UTF-8 ranges, partial separators, three-pipe errors, whitespace rewrites, pasted drafts, unrelated pipes, and shell quoting. |
| Existing-name warning | Visible existing, already hidden, unknown, case-equivalent, malformed catalog, changed-since-preview, and the same label used several times in a bulk capture. |
| Transactions | Dry-run and Escape write nothing; journal failure rolls back notes; note failure emits no preference; stale note is refused; retry is idempotent; crash recovery reports exact state. |
| Rename scope | Open/closed/cancelled/hidden/archived tasks; historical notes; id-less sources; broken targets; accepted aliases; generated mirrors; both directions; no duplicate count from mirrors. |
| Rename safety | Case-only rename; collision refusal; explicit merge and visibility policy; malformed/unreadable files; dirty editor; inventory change after preview; untouched prose/fences; no status/ID/freshness change; post-sync failure; old name reappears. |
| Cross-client compatibility | Same backend keys/counts in Mac, CLI, and Obsidian; missing capabilities; optional-field decoding; older app behavior; hidden journal syncing and invalidation on a second host. |

Land the navigation fix first because it is independently useful. Next implement the catalog/preferences API and shared identity rules; then the hidden capture intent and warnings; then strict global rename and both management interfaces. Rename should not ship with an “active tasks only” shortcut under an “everywhere” label. A bounded vertical card and real selected state are part of the navigation fix, not decoration deferred to the end.

Run focused Rust relation grammar/completion/capture tests, plugin relation-index/navigation tests, and asynchronous Mac model/router tests. Compile changed Swift: the Mac repo explicitly requires portable checks plus macOS compilation for app targets, with test execution in CI; type-checking against a stub alone is not runtime validation. Exercise visual states in light/dark appearance, increased contrast, long labels/titles, empty results, loading, error, hidden, and rename preview. Measure completion cost with the representative vault before adding a cache; navigation itself should be local and immediate. No source code was changed or Swift compiled during this research.

**Evidence and limits.** I inspected the supplied screenshot, local source and tests from the following snapshots, audited project memory, and two primary external interaction references. Repository links below are pinned to the inspected revisions; they identify the local-checkout evidence, not files fetched from GitHub. The existing macOS UI was not run here, and disk-write race behavior was not experimentally tested.

| Reference | Source and relevance |
| --- | --- |
| M1 | [Mac model at 72cd721](https://github.com/bobs-org/bob-mac-capture/blob/72cd721e591a02cd686af3951fcbbdb41d22f6ae/Sources/BobMacCapture/CapturePanelModel.swift#L6440): relation prompt state, cycling at 6631, fetching at 6846, response application at 6942. |
| M2 | [Mac card view](https://github.com/bobs-org/bob-mac-capture/blob/72cd721e591a02cd686af3951fcbbdb41d22f6ae/Sources/BobMacCapture/CapturePanelView.swift#L1762) and [key router](https://github.com/bobs-org/bob-mac-capture/blob/72cd721e591a02cd686af3951fcbbdb41d22f6ae/Sources/BobMacCapture/CaptureKeyCommandRouter.swift#L519): horizontal suggestions and Tab-only cycling. |
| M3 | [Relation panel tests](https://github.com/bobs-org/bob-mac-capture/blob/72cd721e591a02cd686af3951fcbbdb41d22f6ae/Tests/BobMacCaptureTests/CaptureRelationPanelTests.swift#L121): fixed-array cycling test and later stale-response tests. |
| C1 | [CLI candidate catalog and suggestions at 8628ce2](https://github.com/bobs-org/bob-cli/blob/8628ce2f7acdf9a27f4d8ba1c6117638afe34371/src/native/capture_complete/candidates.rs#L1403) and [ranking](https://github.com/bobs-org/bob-cli/blob/8628ce2f7acdf9a27f4d8ba1c6117638afe34371/src/native/capture_complete/support.rs#L18): label counting, filtering, typed-row substitution. |
| C2 | [Capture relation parser](https://github.com/bobs-org/bob-cli/blob/8628ce2f7acdf9a27f4d8ba1c6117638afe34371/src/native/capture_language/relations.rs#L414): current single-pipe separator and quoted-label parsing. |
| C3 | [Task relation contract](https://github.com/bobs-org/bob-cli/blob/8628ce2f7acdf9a27f4d8ba1c6117638afe34371/docs/task-relations.md) and [label normalization](https://github.com/bobs-org/bob-cli/blob/8628ce2f7acdf9a27f4d8ba1c6117638afe34371/src/native/task_relations/label.rs): inertness, edge identity, historical write limits, label constraints, inverse display phrases. |
| C4 | [Theme journal](https://github.com/bobs-org/bob-cli/blob/8628ce2f7acdf9a27f4d8ba1c6117638afe34371/src/native/pomodoro_themes/journal.rs) and [theme contract](https://github.com/bobs-org/bob-cli/blob/8628ce2f7acdf9a27f4d8ba1c6117638afe34371/docs/pomodoro-themes.md): existing visibility and per-host preference pattern. |
| C5 | [Capture batch planner](https://github.com/bobs-org/bob-cli/blob/8628ce2f7acdf9a27f4d8ba1c6117638afe34371/src/native/capture/batch.rs): staged snapshots and text-file write set. |
| C6 | [Vault-wide task discovery](https://github.com/bobs-org/bob-cli/blob/8628ce2f7acdf9a27f4d8ba1c6117638afe34371/src/native/capture_dependency_tasks.rs): broad task-bearing note scope and exclusions. |
| C7 | [Theme rename implementation](https://github.com/bobs-org/bob-cli/blob/8628ce2f7acdf9a27f4d8ba1c6117638afe34371/src/native/pomodoro_themes/rename.rs): transaction precedent and `renamed_reappeared` detection. |
| C8 | [Mac protocol compatibility](https://github.com/bobs-org/bob-mac-capture/blob/72cd721e591a02cd686af3951fcbbdb41d22f6ae/docs/protocol.md): additive contracts and relation capabilities. |
| P1 | [Plugin relation catalog at 3a7368a](https://github.com/bobs-org/bob-plugins/blob/3a7368a1c8cc94bfde9fe6c5ac217c16f5bf6e49/plugins/bob-ledger-tools/src/145-relation-index-model.js#L325) and [description stage](https://github.com/bobs-org/bob-plugins/blob/3a7368a1c8cc94bfde9fe6c5ac217c16f5bf6e49/plugins/bob-navigation-hotkeys/src/426-picker-relation-stage.js#L706): separate locale-sensitive/prefix-only suggestion path and per-edge relabel flow. |
| P2 | [Live relation index lifecycle](https://github.com/bobs-org/bob-plugins/blob/3a7368a1c8cc94bfde9fe6c5ac217c16f5bf6e49/plugins/bob-ledger-tools/src/171-relation-index-lifecycle.js) and relation contract §11: unsaved editor overlay and generation updates. |
| P3 | [Plugin theme API](https://github.com/bobs-org/bob-plugins/blob/3a7368a1c8cc94bfde9fe6c5ac217c16f5bf6e49/plugins/bob-ledger-tools/src/279-plugin-pomodoro-themes.js): existing subprocess-owned preference management precedent. |

Audited memory consulted: `glossary:task-relation`, `glossary:capture`, `decisions:mac-capture-is-a-thin-client`, `decisions:theme-hide-is-recent-only`, `decisions:theme-prefs-live-in-per-host-journal`, `cli_rules.md`, and `sase_artifacts.md`. No peer report or peer transcript was consulted. The work does not require a new expiry system, inverse-description editor, per-note description scopes, automatic semantic grouping, or a permanent relation-type database.

**Recommended solution.** Build a backend-owned description library over the existing readable LINKS labels, with a separate synced hide/unhide journal. Make the card a vertical combobox whose Ctrl+N/P selection never rewrites its query, whose Tab/Return acceptance is explicit, and whose hidden state is recoverable from a visible Include hidden control. Support `||` as a transactional, warning-bearing “use and hide this shared description” capture intent. Add a distinct, previewed Rename everywhere operation shared by the CLI, Mac card, and Obsidian, including historical label spans and verifiable recovery. This directly fixes the observed bug, supports one-off wording without erasing relationships, and keeps the interface small enough to remain beautiful and predictable.
