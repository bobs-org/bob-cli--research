# Reusable task-log input history: fast recall without changing task decisions

Independent research by **cdx**, 19 November 2026.

No other report, transcript, summary, or findings from this research swarm were consulted. This is a design recommendation based on source inspection and primary documentation, not an implementation or measured usability study.

## Assessment

**Yes: shared, per-log input history is a good improvement.** Repeated explanations are often legitimate, and typing them again adds little value. Reuse the user's language while preserving the current task decision, preview, and explicit submission.

I recommend **four vault-wide histories—Schedule, Work, Rotten, and Cancel—with reversible Ctrl+P/Ctrl+N recall, simple filtering, and the previews already present in Bob**. Store successfully submitted human text through a bob-owned, per-host journal. Keep the prompt empty until the user types or explicitly recalls an entry. Do not automatically insert a reason, infer a decision, or replay a whole logged event.

The biggest traps are deeper than the widget:

- A Schedule Log's date is the scheduled date, not the time its explanation was typed. Sorting those dates does not produce input history.
- Rotten entries combine a human reason with generated rung and keep-count information. Reusing the complete line would copy stale facts.
- Work Log entries can have nested details, and capture log text occupies only part of a structured draft. Replacing a whole line or subtree could change task assignment.
- Ctrl+N/P already belongs to completion and picker navigation elsewhere. A global shortcut would break existing interactions.
- Reasons can be staged before the task operation succeeds. Saving whenever a field receives Enter would remember canceled or failed operations.

These favor one shared input-history service with carefully scoped UI integration over independent histories bolted onto each modal.

## What the code actually does

Inspected revisions:

| Repository | Revision |
|---|---|
| bob-cli | `5b4c26360efe9d90d20b8371ac53a05bef7492b6` |
| bob-plugins | `ccfc12bb62cecbde3ee47310ad82a0ddb4031ac4` |
| bob-mac-capture | `868672fc516996dc3a36c53ec0114f4139213720` |

The following are confirmed integration surfaces, not a claim that every possible writer has been enumerated.

| Surface | Current behavior and implication |
|---|---|
| Obsidian Task Card scheduling review | `370-picker-schedule-work-log.js` renders a date-reason field and, when applicable, a separate Work summary. Each needs its own history state. Tab already cycles fields. [P1] |
| Obsidian cancellation and lane-release stages | `380-picker-cancel-and-lane.js` provides Cancel-reason and Work-summary stages with previews. Blank cancellation distinguishes no existing log from a fallback in an existing log. Preserve that behavior. [P2] |
| Obsidian unlink and Move to Next | `WorkSummaryPromptModal` in block-id-prompt and `TaskLinkLanePromptModal` have optional Work summaries and previews. Unlink closes only after its asynchronous writer reports success. [P3, P4] |
| Obsidian lane release | `LaneReleaseSummaryModal` is another Work-summary prompt. Its callback returns text before the downstream operation; modal close is too early to record history. [P4] |
| Obsidian keep, Stay, and batch refresh | `RottenKeepReasonStage` is shared by ordinary keep and decay-card Stay; batch refresh has a separate input. The stage already displays up to three **task-local earlier keeps/decisions** and a prospective log entry. This is useful context, but not reusable cross-task input history. [P5] |
| Capture Work Log text | The Rust close-log lexer recognizes inline, numbered, positional, and `- *` entries, with separate text and detail ranges. Mac capture renders typed Work Log previews. Recall the summary, not its task number or detail subtree. [B1, M1] |
| Capture successor cancellation | `CapturePullInReasonField` is a real Cancel-reason editor. Enter stages the reason; applying the overall choice is later. Cover this field, not only the main draft. [M2] |
| Capture key routing | Modal contexts precede generic completion. Ctrl+N/P already moves completion/picker selection; the focused pull-in reason has a separate routing branch. [M3] |

The Rust managed-log marker enum used for capture insertion includes Schedule, Work, and Rotten but deliberately excludes Cancel. Define an explicit four-kind history model instead of reusing that insertion enum as the complete taxonomy. [B2]

I did not find a standalone Mac Rotten-reason editor in the inspected paths. Do not invent a new prompt to achieve symmetry. Attach history to existing human-input surfaces; quiet automated log writes stay quiet.

## Requirements I would adjust

1. **Include Rotten explicitly.** It appears in the request's opening but not its three-item storage requirement. Give it a fourth independent history: Work describes activity; Rotten explains keeping a task.
2. **Define global as one vault across tasks, notes, statuses, and supported clients.** Different vaults remain isolated. Cross-host availability follows normal vault sync, not instant cloud synchronization.
3. **Remember submitted text, not formatted log entries or keystrokes.** Exclude generated stamps, transitions, keep counts, blank fallbacks, calendar cancellations, and generated relation-cancel explanations. Explicit user input remains eligible even when its wording resembles boilerplate.
4. **Reuse the primary summary only in v1.** Do not copy Work details, task numbers, dates, IDs, or routing. Detail-tree reuse deserves a separate design.
5. **Treat this as input history, not a second task audit log.** A successfully used phrase survives subsequent task undo, archive, rename, or deletion. This is intentional: undoing a task action should not erase useful language. Explain it in settings.
6. **Keep existing blank and submit behavior.** Blank Work can still skip logging; blank Rotten still uses its current fallback. Never put the first history entry into an untouched field.
7. **Add filtering and reuse existing previews, but defer a large library UI.** No fuzzy ranking, favorites, AI paraphrasing, template parameters, or extra modal is needed initially.
8. **Bound active recall.** Start with the latest 200 distinct phrases per kind across all tasks. This proposed working-set limit does not imply deletion of older journal bytes or an all-time searchable archive.

The product risk is that effortless reuse of “still important” makes Rotten review mechanical. Keep the task, rung, keep tally, and earlier decisions visible and require explicit recall. Typing friction is a poor substitute for the existing decay decision.

## Interaction recommendation

### Direct, reversible recall

Use **Ctrl+P = previous/older; Ctrl+N = next/newer, eventually back to the draft**. GNU Readline uses those bindings and retains a current-input position at the end of history. This is a useful precedent for repeated text entry. [GNU history commands](https://www.gnu.org/software/bash/manual/html_node/Commands-For-History.html)

This intentionally differs from Bob's list pickers, where Ctrl+N/P means down/up. Scope and label it clearly. Avoid a newest-first dropdown that visually implies the opposite direction; use a compact recall strip.

| Action or state | Required result |
|---|---|
| Open prompt | Existing value/caret remain unchanged. Show a quiet `History · Ctrl+P` affordance or loading/empty state. |
| First Ctrl+P | Save exact draft text, selection, and replacement span. Freeze the filtered candidates and recall the newest match. |
| Further Ctrl+P | Recall older distinct matches. Clamp at the oldest; never wrap. |
| Ctrl+N during recall | Move newer; beyond the newest restore the exact draft and selection. |
| Ctrl+N at the draft | Leave it unchanged. Consume the key inside an eligible history field so it cannot move a picker behind that field. |
| Enter | Run the host's existing action with the visible text. An ordinary modal may commit; the pull-in reason only stages; capture retains its existing submit behavior. |
| Escape / Ctrl+[ during recall | Restore the draft and end recall, without also canceling the host. A subsequent dismissal follows existing layering. |
| Type, paste, or edit recalled text | Adopt it as an ordinary draft, then edit. Never modify the stored phrase. A new recall session uses the edited draft as its origin. |
| Tab / Shift+Tab | Keep displayed text and preserve existing focus traversal. No new acceptance meaning. |
| Blur | End transient recall, keep displayed text, preserve one undo step to the original draft. |
| No matches | Keep the draft/selection and show `No matching history`; never substitute an unrelated entry. |

`Ctrl+P → Enter` reuses the last reason with two keys. There is no extra acceptance step: the field and effect preview already show the recalled phrase. The task action remains explicit. This is input-history recall, not an automatically selected autocomplete result.

Make all preview replacements in a recall session one reversible edit, not ten undo entries. Escape restoration should leave no meaningless undo/redo trail. Editing a recalled phrase must still allow recovery of the pre-recall draft. Verify this in the real editors; string assignment alone is insufficient.

### Filtering that stays predictable

Use the original field text as the filter when recall starts. Empty text matches everything. Otherwise split on whitespace and require every term to appear as a case-insensitive literal substring. Keep recency order among matches. Do not add fuzzy scores, frequency boosts, or task-dependent ranking.

`waiting review` can find `Waiting for design review` without requiring a remembered prefix. Search must not rewrite the candidate's punctuation, Markdown, links, or case. Duplicate identity can remain case-sensitive after existing field normalization; matching is case-insensitive independently.

**Freeze the query and results while cycling.** Re-filtering on each recalled sentence would collapse the list to that sentence. Show `matching “waiting review”` to explain the state. Restore and edit the draft to change the query; clear the field before recall to browse all recent entries.

New data must not reorder an active session. Refresh on the next session. Ordinary typing must never automatically replace text.

### Appearance: a quiet addition to existing previews

**Figure 1 — Schedule-reason recall.** The strip explains the candidate, and the current operation's preview shows the new entry. The neighboring Work field has independent history.

```text
Reason for this date (optional)
┌───────────────────────────────────────────────────────┐
│ Waiting for design review                             │
└───────────────────────────────────────────────────────┘
↶ Schedule history  2 of 6 · matching “waiting”
   Last used yesterday             ⌃P older · ⌃N newer

Will add to Schedule Log
  Nov 19 → Nov 24 — Waiting for design review

Work summary (optional)
┌───────────────────────────────────────────────────────┐
│                                                       │
└───────────────────────────────────────────────────────┘
                                      History · ⌃P
```

This is illustrative; existing formatters remain authoritative for actual log bytes and dates.

Use each host's font scale, spacing, borders, and subtle backgrounds. Keep the input baseline and capture panel's fixed eye line stable. Reserve a small strip instead of animating a large results area on every key. Identify history by icon and log-kind text, not color alone. Keep the full recalled text editable and its effect preview legible.

Provide clickable Older, Newer, and Restore draft controls. Put **Hide this suggestion** in a secondary menu with undo; do not steal Ctrl+D from text deletion or existing picker actions.

Keep the Rotten stage's task-local “Earlier decisions” block. Label reusable text “Rotten history” or “Previously used reasons” so a phrase from another task is not mistaken for this task's justification.

Announce the recalled value and position politely; retain text focus. If a later expanded list is added, implement actual editable-combobox/listbox semantics and explicit selection rather than assigning ARIA roles to decoration. W3C distinguishes manual from automatic selection and describes exploration without losing original input. [W3C combobox pattern](https://www.w3.org/WAI/ARIA/apg/patterns/combobox/)

Respect IME composition and exact modifiers. Native macOS text editing also uses Ctrl+P/N for vertical movement: intercept only in declared history-capable fields/spans, leaving other multiline text alone. [Apple text-editing shortcuts](https://support.apple.com/en-us/102650)

## Storage recommendation

### Compare the alternatives

| Approach | Strength | Main cost | Verdict |
|---|---|---|---|
| Per-plugin/app preference arrays | Fast prototype | Histories fragment across prompts, clients, and hosts | Reject as final design |
| Scan all task logs on every prompt | Immediate old phrases | I/O, ambiguous provenance, incorrect Schedule recency | Reject |
| Incremental index of task logs | Rebuildable; follows edits and undo | Cannot recover true Schedule input time or always identify human text | Optional legacy discovery only |
| One shared JSON array in the vault | Simple format | Concurrent host writes can overwrite each other | Reject |
| Per-host append journals plus local folded cache | Shared identity, actual use time, raw text, existing Bob precedent | Commit hooks and explicit retention semantics | Recommend |

Bob already uses `.bob/themes/<host>.jsonl` and `.bob/relations/<host>.jsonl`, with bob as writer and deterministic folds. Reuse its journal infrastructure. The raw append helper alone is **not** a complete concurrency or crash design: retain the established lock discipline and validate torn tails. [B3; journal decisions]

Proposed namespace: `.bob/log-history/<host>.jsonl`. Separate histories can be logical partitions; four files per host are unnecessary. Define an explicit kind enum: `schedule`, `work`, `rotten`, `cancel`.

A proposed event, not an existing API:

```json
{
  "v": 1,
  "event": "log_history.used",
  "id": "unique-commit-receipt-id",
  "ts": "2026-11-19T10:42:13Z",
  "host": "mac",
  "kind": "schedule",
  "text": "Waiting for design review",
  "via": "obsidian.schedule-review"
}
```

Keep task titles and note paths out of the normal journal. Recall needs text, category, and time, not another task graph. Surface provenance is sufficient.

Deduplicate event IDs, then fold by normalized phrase within each kind. Reuse moves one candidate to the front. Applying the same phrase to twenty tasks in one batch is one use; two kinds in one form are separate uses. Give retries a stable commit-receipt ID, while deliberate later reuse gets a new ID.

Normalize with existing target-field rules; preserve Markdown and case. Record only the human summary, before adding timestamps, transitions, or rung/count suffixes. Work details remain in the task log. Do not infer authorship by blacklisting generic words when the writer already knows whether input was explicit. [B1, P1, P5]

Use deterministic tie-breaking compatible with existing journals. Preserve same-host write order if the wall clock repeats. Cross-host recency is approximate under clock skew; do not promise perfect global ordering. Freeze active UI snapshots regardless.

Keep a disposable, versioned, vault-keyed folded cache under Bob's cache directory. The theme catalog offers an existing vault-aware cache/atomic-write precedent. Corruption rebuilds the cache, never clears journal history. Do not sync this cache. [B4]

### Learn at the successful write boundary

The boundary is **successful task/log mutation**, not accepting a field, closing a modal, generating a preview, or staging a choice.

- Rust capture may collect candidate receipts while planning, but records only after the complete transaction succeeds. Dry runs and failed aggregate captures teach nothing.
- Obsidian uses a shared adapter called from successful writer outcomes. A callback returning text is not proof of a committed write. Lane release and batches require their outer success boundary.
- Mac pull-in cancellation records after the later cancellation succeeds through bob, not when Swift accepts the inline reason.
- No-ops and operations that write no eligible human text teach nothing. Neither do machine-authored log events.

History is ancillary. If the task saves but history persistence fails, do not return a task-operation failure that invites duplication. Show a separate nonblocking state such as “Task saved; history not saved,” with an idempotent retry of the history receipt alone. Session-local recall may retain the accepted phrase meanwhile.

For v1, accept the narrow crash window between a task write and its history record. Do not claim exactly-once durability across Obsidian editor transactions, subprocesses, and vault sync. If lost history proves material, add a durable commit-receipt/outbox design later. A new distributed transaction system is disproportionate to a typing aid. Normal concurrency and explicit retries must still be reliable and deduplicated from day one.

### Control, retention, and existing logs

Use **Hide this suggestion**, with undo, rather than calling visibility changes deletion. It hides one phrase in one category, never a task's log. Later typed use should not silently unhide it. Persist explicit hide/restore decisions in the journal with defined ordering against uses. Provide a per-vault option to disable history learning/display.

The 200-entry working set bounds recall, **not physical retention**. The journal duplicates user text inside the vault, potentially retained in Git history. Explain that in settings; never send phrase contents to analytics or general process diagnostics. Send text through structured stdin/JSON, not shell interpolation or command-line arguments. Physical erasure and compaction need honest separate semantics.

**Do not automatically populate history by scraping old logs at upgrade.** Offer legacy discovery later, or as an optional import if immediate cold-start coverage is worth the added scope. Scan canonical direct-child logs across active and archived tasks, ignore fenced examples and generated fallbacks, use strict kind-specific parsers, and allow candidate review. Skip unknown forms instead of heuristically stripping them into plausible reasons.

Imported phrases have unknown input recency, especially Schedule reasons. Put them below genuine uses as “Existing log text,” without invented last-used dates. The first real reuse gives a proper timestamp. Old logs cannot always prove authorship. This is a deliberate scope adjustment: reliable history going forward, not perfect reconstruction of every past input.

## Integration and keyboard ownership

bob-cli should own storage, normalization, deduplication, and the query contract. A possible top-level noun is `bob log-history`, whose members all manage reusable log-input phrases. Do not nest it beneath `bob task`, which project rules reserve for vault-wide task-line rewrites. Do not add subcommands beneath free-text `bob capture` or invent another frozen `capture-*` sibling. Final public options/help must follow normal CLI rules.

Minimum operations: read a category snapshot, record successful uses, hide/restore a suggestion. Existing `capture-parse`/`capture-complete` may grow additively to expose eligible log-text spans and replacements. Use versioned JSON; distinguish empty, unavailable, unsupported, and malformed responses.

The Mac stays a thin client: Rust identifies log text and gives ranges; Swift renders/applies them. Use the shared close-log lexer's text/detail ranges and unfinished-entry structure rather than a Swift grammar. Validate draft revision and expected source bytes before applying a replacement. Exercise UTF-8/UTF-16 conversion with emoji and combining characters. [B1, M3; thin-client decision]

Make routing precedence explicit:

1. IME handling and the existing topmost modal context.
2. The focused dedicated log field's history handler, if present.
3. An active semantic completion/picker inside capture log text, such as a link-token picker.
4. History for a bob-declared plain log-text span.
5. Existing generic completion or native editing.

Do not claim history shortcuts in date pickers, task lists, relation pickers, Work detail children, or the entire capture draft. If a token completion owns the caret, history waits until it finishes; show the correct hint. Reset transient state when field, kind, item, vault, or replacement span changes.

Use one tested pure recall state machine and reusable DOM adapter across Obsidian prompts. A shared plugin data API can follow the Ledger Tools theme-fetch pattern, with feature detection for older/missing components. Swift should share interaction fixtures, not reimplement storage or grammar. [P6]

Fetch once on prompt opening/on demand, share in-flight fetches, and cache per vault/kind. Never spawn bob for every key or character. Filter and cycle against an immutable in-memory snapshot. Service failure must leave normal typing and submission usable.

On cold loading, show a quiet loading state and require a fresh recall gesture after readiness; never replay an old key later into a changed draft. Reject stale replies by field, vault, request generation, and draft revision. Warm navigation should feel immediate; roughly 100 ms for a warm snapshot is a proposed target, not a measurement.

## Verification and rollout

| Area | Required evidence |
|---|---|
| Scope | Reuse across different tasks and clients; no leakage across kinds or vaults. |
| Four kinds | All categories work, including independently focused Schedule/Work fields in one form. |
| Draft safety | Empty/partial drafts, selections, boundaries, no matches, repeated keys, escape, blur, and undo preserve expected text. |
| Filtering | Query remains frozen while cycling; asynchronous updates cannot reorder active candidates. |
| Save boundary | Canceled dialogs, dry runs, refusals, failed captures, abandoned staged choices, and no-ops create no use events. Batch use deduplicates. |
| Failure isolation | History retry never repeats a successful task operation. |
| Generated content | Blank fallbacks, roll text, Rotten counters, relation/Google cancellation boilerplate stay out of automatic learning. |
| Capture structure | Inline, numbered, positional, star, incomplete, Unicode, and multi-item cases replace only the summary span, preserving directives and details. |
| Key conflicts | Completion, date, relation, pull-in, and native editing retain ownership outside the designated history scope. |
| Persistence | Concurrent writers, host sync, duplicate IDs, malformed/torn rows, wrong versions, inaccessible storage, and cache rebuild do not destroy history. |
| Accessibility | Announced values/positions, stable text focus, IME, and Escape/Ctrl+[ parity work. `q` types in fields and mirrors Escape outside text controls. |
| Visuals | Narrow/long layouts, light/dark, reduced motion, and dual-field prompts remain readable without baseline jumps. |

Use shared JavaScript/Swift interaction vectors and Rust parser fixtures. Preserve existing task/log writer behavior, and verify supported older/newer bob/client combinations degrade to plain fields when history is unavailable.

Roll out backend capability before UI adapters. Plugin implementation must rebuild source fragments and follow its validation/deployment workflow. Swift must compile and pass macOS gates; portable checks cannot validate AppKit dispatch. These are future implementation obligations, not checks performed for this report.

Validate the product with a short realistic exercise: repeat Schedule and Cancel reasons across tasks, reuse/edit a Work summary, and recall a Rotten reason with its task context visible. Compare keystrokes, time, abandoned recall, and accidental replacement. Do not treat suggestion counts as success or collect phrase contents in telemetry.

## Evidence and limits

Repository findings come from opened checkouts at the pinned revisions. These links identify exact evidence, not pages used to bypass local repository access.

- **[P1]** [Scheduling fields](https://github.com/bobs-org/bob-plugins/blob/ccfc12bb62cecbde3ee47310ad82a0ddb4031ac4/plugins/bob-navigation-hotkeys/src/370-picker-schedule-work-log.js) and [keyboard handling](https://github.com/bobs-org/bob-plugins/blob/ccfc12bb62cecbde3ee47310ad82a0ddb4031ac4/plugins/bob-navigation-hotkeys/src/450-picker-keydown.js).
- **[P2]** [Cancel/lane stages](https://github.com/bobs-org/bob-plugins/blob/ccfc12bb62cecbde3ee47310ad82a0ddb4031ac4/plugins/bob-navigation-hotkeys/src/380-picker-cancel-and-lane.js).
- **[P3]** [Unlink WorkSummaryPromptModal](https://github.com/bobs-org/bob-plugins/blob/ccfc12bb62cecbde3ee47310ad82a0ddb4031ac4/plugins/block-id-prompt/main.js#L13870).
- **[P4]** [Move-to-Next summary](https://github.com/bobs-org/bob-plugins/blob/ccfc12bb62cecbde3ee47310ad82a0ddb4031ac4/plugins/bob-navigation-hotkeys/src/196-task-link-lane-modal.js) and [lane-release modal](https://github.com/bobs-org/bob-plugins/blob/ccfc12bb62cecbde3ee47310ad82a0ddb4031ac4/plugins/bob-navigation-hotkeys/src/190-summary-modals.js#L739).
- **[P5]** [Rotten formatting/history/reason stage](https://github.com/bobs-org/bob-plugins/blob/ccfc12bb62cecbde3ee47310ad82a0ddb4031ac4/plugins/bob-navigation-hotkeys/src/195-rotten-keep.js) and [batch refresh](https://github.com/bobs-org/bob-plugins/blob/ccfc12bb62cecbde3ee47310ad82a0ddb4031ac4/plugins/bob-navigation-hotkeys/src/192-freshness-refresh-summary-modal.js).
- **[P6]** [Shared theme-fetch service](https://github.com/bobs-org/bob-plugins/blob/ccfc12bb62cecbde3ee47310ad82a0ddb4031ac4/plugins/bob-ledger-tools/src/279-plugin-pomodoro-themes.js).
- **[B1]** [Close-log lexer](https://github.com/bobs-org/bob-cli/blob/5b4c26360efe9d90d20b8371ac53a05bef7492b6/src/native/capture_language/close_log.rs), [Work writer](https://github.com/bobs-org/bob-cli/blob/5b4c26360efe9d90d20b8371ac53a05bef7492b6/src/native/capture_work_log.rs), and [Schedule dates/generated reasons](https://github.com/bobs-org/bob-cli/blob/5b4c26360efe9d90d20b8371ac53a05bef7492b6/src/native/capture_schedule_log.rs).
- **[B2]** [Insertion marker taxonomy](https://github.com/bobs-org/bob-cli/blob/5b4c26360efe9d90d20b8371ac53a05bef7492b6/src/native/capture/sub_bullet.rs#L315).
- **[B3]** [Shared journal mechanics](https://github.com/bobs-org/bob-cli/blob/5b4c26360efe9d90d20b8371ac53a05bef7492b6/src/native/pref_journal/mod.rs).
- **[B4]** [Vault-aware cache precedent](https://github.com/bobs-org/bob-cli/blob/5b4c26360efe9d90d20b8371ac53a05bef7492b6/src/native/pomodoro_themes/cache.rs).
- **[M1]** [Close-log presentation](https://github.com/bobs-org/bob-mac-capture/blob/868672fc516996dc3a36c53ec0114f4139213720/Sources/CaptureCore/CapturePomodoroClosePresentation.swift).
- **[M2]** [Inline Cancel field](https://github.com/bobs-org/bob-mac-capture/blob/868672fc516996dc3a36c53ec0114f4139213720/Sources/BobMacCapture/CapturePullInChoiceView.swift#L978) and [staged reason state](https://github.com/bobs-org/bob-mac-capture/blob/868672fc516996dc3a36c53ec0114f4139213720/Sources/BobMacCapture/CapturePullInChoice.swift).
- **[M3]** [Key routing](https://github.com/bobs-org/bob-mac-capture/blob/868672fc516996dc3a36c53ec0114f4139213720/Sources/BobMacCapture/CaptureKeyCommandRouter.swift) and [replacement/Unicode handling](https://github.com/bobs-org/bob-mac-capture/blob/868672fc516996dc3a36c53ec0114f4139213720/Sources/BobMacCapture/CapturePanelModel.swift).

Audited project-memory reads included `task-decay-is-one-ladder`, `mac-capture-is-a-thin-client`, `q-and-ctrl-bracket-mirror-esc`, theme/relation per-host-journal decisions, Capture/Capture Panel/Schedule Log/Work Log/Rotten Log definitions, and CLI rules. This recommendation does not amend those decisions.

No live vault contents or user phrases were inspected. Examples are invented. I did not run graphical clients, measure latency, compile Swift, or modify product code. Remaining uncertainties are real history volume, demand for whole Work-detail reuse, and whether shell-style previous/next beats list-style navigation for this user's habits. Validate these through the focused exercise; none blocks the architecture recommendation.

## Recommended solution

**Build four separate, vault-wide histories of successfully submitted human log text, shared through a bob-owned per-host journal.** Add Ctrl+P/Ctrl+N recall to existing log-entry surfaces, exact draft restoration, frozen literal filtering, a small history strip, and the existing live effect preview. Preserve Enter, blank-reason rules, task decisions, capture syntax, and focus traversal.

Ship this focused version before fuzzy search, saved templates, automatic legacy backfill, or a history-management browser. The defining quality should be that the last useful sentence is two keys away—and trying history never costs the user their draft or quietly changes what happens to the task.
