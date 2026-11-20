# Explicit micro tasks: commitments inside tasks

Independent research by **cdx**, 2026-11-20. This report was researched independently; no other report or finding from this swarm was consulted. It recommends a design, not an implemented feature.

**Recommendation:** introduce `TASK:` as the canonical micro-task prefix. Render it as a quiet `##` badge, adding a hash for each micro-task ancestor. Treat unmarked authored bullets as notes; write new captured notes into `NOTES`. Model nested micro tasks as a tree of commitments owned by an ordinary task. At managed completion, show the direct micro roots in the successor panel, defaulting to **Done with parent**; allow **Keep open**, optionally **Pull in**, or **Cancel**. Apply those decisions together with the parent close in one guarded operation. Reuse split for materialization and successor machinery for placement, but do not disguise micro tasks as existing ordinary tasks.

The idea is good. Its value is making the boundary between information about the work and work still owed explicit. The difficult parts are closure semantics, migration, and preserving structure, not the prefix. A micro task should mean a subordinate commitment, not a task that takes fewer than five minutes.

## 1. What the current system actually does

I inspected bob-cli, bob-plugins, and Bob Mac Capture at these snapshots:

| Repository | Commit inspected |
| --- | --- |
| bob-cli | `620270d116a0d0c8fb0f546959dc230eff06d488` |
| bob-plugins | `a68e29be2b0bb50aee47a19d65a3485c207b59bb` |
| bob-mac-capture | `6d54cb0f42ef19cd6679a5e493671748274f28cd` |

Findings are based on source and contract inspection. I did not run the UI, change the vault, benchmark rendering, or test a prototype.

1. **Project promotion distinguishes structure implicitly.** `buildProjectSeedFromChildBullets` converts eligible direct child bullets to project tasks. A qualifying ALL-CAPS child with nested list items becomes a section; managed logs are handled separately. Descendants of a converted child are retained below that task rather than recursively converted. This feature replaces a real implicit rule, but “all sub-bullets become tasks” would overstate current behavior. [S1]
2. **Capture supports only two authored bullet levels.** `AuthoredDepth` and `classify_authored_line` distinguish column-zero bullets from bullets with exactly two leading ASCII spaces. Deeper, tab-indented, and other nonempty shapes are invalid. Mac Tab/Shift-Tab enforces the same ceiling. Nested micro tasks with their own notes require a grammar change. [S2]
3. **Leading `#` already names a drawer.** At the first-level task-child position, `- #future-work` is a shortcut for an ALL-CAPS drawer with nested notes. On notebook routes similar syntax selects a section. `#task` therefore competes with an established capture grammar. [S3]
4. **Default note capture writes a direct child.** `plan_sub_bullet_capture` ensures a drawer only when supplied a selector; otherwise it chooses a plain-child insertion slot. Default NOTES placement must change writers for existing tasks and newly captured task bodies. [S4]
5. **Split is a strong starting point.** It creates a task, moves children, mints or reuses an anchor, leaves a link stub, handles reverse mentions, routes daily-note owners to a root note or inbox, and has stale-selection and guarded-undo contracts. Its ordinary birth semantics do not inherit priority, schedule, dependencies, lane, freshness, or explicit type from the owner. Micro extraction should reuse these primitives. [S5]
6. **Merge creates the basic shape we want.** The shared engine writes a plain source-title bullet and copies authored descendants beneath it, preserving source history and repairing dependents. The task-target title can become a micro task, but subtree classification and preservation also need attention. [S6]
7. **Successor verdicts already exist.** Ordinary rows support Leave, Pull in, Done, and Cancel. Ctrl+X stages Done; Ctrl+Shift+X stages Cancel. Bob supplies eligibility and consequence copy. Existing Obsidian verdict application can be best-effort after the predecessor closes, whereas capture is all-or-nothing. This distinction matters for newly materialized micro tasks. [S7]
8. **The shortcuts are not entirely vacant.** Ctrl-G is a one-key editor leader with `u` bound and `t` available. Fast `..` already escapes certain dot aliases, and `- .` has a Move-picker meaning in project-note capture. The new alias needs an exact context. [S8]
9. **The visual language has an existing home.** Bob Ledger Tools renders tracked-task identity as a quiet hash mark, with Live Preview decorations, rendered-view processing, code exclusions, and accessible labels. Extend that system. [S9]

Audited memory confirms that Bob owns capture semantics and mutations, clients must not implement another capture grammar, and daily links require explicit selection. This design preserves those rules. It reopens the two-level capture/drawer decision, whose stated reconsideration condition includes a third authored level. [M1]

## 2. One stored marker, separate from its visual badge

| Candidate | Advantages | Costs | Recommendation |
| --- | --- | --- | --- |
| `TASK: Publish notes` | Readable without plugins; no tag pollution; precise prefix | Longer source; must outrank the ALL-CAPS drawer classifier | **Canonical spelling** |
| `#task Publish notes`, no checkbox | Familiar and compact | Drawer shortcut collision; same token means tracked tasks elsewhere; tag indexing; broad tag-based tools may misread it | Reject |
| `#micro Publish notes` | Distinct from tracked-task tag | Still occupies tag/drawer syntax; adds a tag taxonomy for structure | Reject |
| `- [ ] Publish notes`, no `#task` | Native checklist familiarity | Depends on global-filter settings; invites independent checkbox state instead of inherited lifecycle | Reject as canonical |
| `## Publish notes` in a bullet | Looks like the requested badge | Markdown heading syntax; duplicates depth already encoded by indentation | Render only |
| `.. Publish notes` stored literally | Fast | Cryptic source; existing alias escape conflicts; typing convenience becomes storage grammar | Editor alias only |

Obsidian treats `#keyword` as a tag with search and navigation behavior, an unnecessary second meaning for this structural marker. [Obsidian tag documentation](https://obsidian.md/help/tags). Tasks also uses `#task` as an example global filter, although it is not the default setting. [Tasks introduction](https://publish.obsidian.md/tasks/Introduction). Bob's scanner currently requires a checkbox plus its configured filter, so a plain `- #task ...` would **not automatically become a Bob task today**. The objection is ambiguity and integration risk, not an existing scanner bug. [S10]

Hash runs followed by whitespace are Markdown heading syntax, including inside list-item content. Do not emit literal `##` as storage for micro tasks. [CommonMark heading specification](https://spec.commonmark.org/0.31.2/#atx-headings).

Recognize exact, case-sensitive `TASK:` followed by whitespace and a nonempty title, only at the start of an eligible non-checkbox bullet body. `TASK: WRITE DOCS` is a micro task before drawer classification. `Task:`, mid-sentence `TASK:`, code, quoted examples, and escaped `\TASK:` remain literal. Empty `TASK:` is an editable placeholder but an incomplete micro task at submission. Avoid accepting several competing spellings indefinitely.

The badge has **2 + the number of micro-task ancestors** hashes. Notes and drawer depth do not add hashes. Moving a subtree changes its badge without rewriting the marker. Source remains `TASK:` at every level.

## 3. Define the tree before the keymaps

A micro task has a title and owned body. It may own notes, drawers, and other micro tasks. While embedded, it has no independent lane, schedule, priority, dependency edges, review age, Pomodoro links, or task-count contribution. Work needing those properties should become an ordinary task through split or Keep open.

```markdown
- [ ] #task Release the service ^release
  - NOTES
    - The staging account is shared with analytics.
  - TASK: Verify recovery
    - NOTES
      - Use last night's database snapshot.
    - TASK: Restore a snapshot
    - TASK: Run the smoke test
  - TASK: Publish the runbook
    - REQUIREMENTS
      - Include the rollback owner and paging channel.
```

There are two direct micro tasks and two nested micro tasks. Direct roots are the completion-review units. Nested roots become independent review units only after their immediate micro parent becomes an ordinary task.

**Recommended containment rule:** an active micro bullet is a direct child of an ordinary task or another micro task. Notes and drawers hold information, not hidden actionable commitments. A marker inside NOTES must not silently become a successor. Give an explicit marker inside an ordinary drawer a diagnostic and a conversion action that moves the whole bullet out beside the drawer. Markers in code, quoted examples, and managed logs remain literal.

This is a deliberate restriction beyond the request. It keeps ownership obvious and avoids work appearing from quoted material. It does not restrict micro-on-micro nesting. Ctrl-G T should perform the structural move from a drawer rather than requiring manual reindentation.

**Notes by default** has two parts:

- Old bare authored bullets are notes belonging to their nearest task or micro owner, equivalent to implicit NOTES. Do not physically rewrite the entire vault merely to express this interpretation.
- New capture writes ordinary note payloads into the owner's explicit NOTES drawer, using the shared resolver. Explicit drawers keep their destination; explicit micro markers write at the owner-child level. Preserve order within each destination. Do not move old notes or managed lines when adding one new note.

A micro task's notes belong to that micro task, not the outer task. Add contextual drawer recognition for micro owners; the glossary's current direct-child-of-`#task` restriction needs a documented extension.

The stored-note parser should preserve existing indentation styles. Capture can emit two spaces per level, but replace its two-state depth with numeric depth and a parent stack. Reject depth jumps without a possible parent. Extend depth for task and micro authored bodies, not automatically for record fields, work-log grammar, or notebook section rules.

## 4. Fast, predictable capture

The primary authoring form is ordinary draft structure:

```text
@work+release
- staging uses the shared analytics account
- TASK: Verify recovery
  - use last night's snapshot
  - TASK: Restore a snapshot
    - TASK: Verify row counts
- TASK: Publish the runbook
```

Preview shows explicit NOTES placement and the hierarchy before submission. The same behavior works beneath a newly captured task. A one-line existing-task note, `@work+release TASK: Publish the runbook`, can express a direct micro task too. `TASK:` at the beginning of a new top-level task title stays title text because it is not a task-child position.

**`..` alias.** Typing `- .. ` at an eligible task-child bullet start expands to `- TASK: `. Require a delimiter after the second dot so `...` and `../path` remain literal. At that exact position, the first dot must remain pending/literal long enough to distinguish the sequence; it must not first open a route or dependency picker. Bob's rewrite context decides this reservation; Swift must not parse it independently.

Preserve dot behavior in project-note Move bullets and other route/link contexts. A direct task-creation bullet inside project-note capture already represents a real task: the micro alias applies only to its eligible child body. Undo restores literal dots without immediate re-expansion. Pasted text, templates, CLI input, and `capture-parse` keep literal `..`, consistent with existing typing-only aliases. The portable spelling is `TASK:`. Do not advertise `..` as a universal grammar token.

**Ctrl-G T.** Extend the existing leader. An eligible plain bullet becomes a micro task; an active micro task becomes notes. Preserve caret, selection, body bytes, and one-step Undo. A direct drawer entry is lifted with its subtree beside the drawer under the owning task/micro task; preview says “Make micro task · move out of NOTES.” Remove an emptied drawer with the normal helper.

Do not silently erase nested commitments. Turning a micro task into a note while it owns active micro descendants should refuse with “Move or convert its nested micro tasks first.” Terminal receipts need an explicit reopen/review action, not the marker toggle. In code, managed logs, task headlines, and unsupported routes, leave text intact and explain unavailability. Also provide a named command/menu action.

Ctrl-G T is semantic, unlike Ctrl-G U's case-only edit. Have Bob return eligibility and text replacements. Hold dependent Return/edit processing until the response is applied, using the existing meaning-changing rewrite pattern. A slow or older binary must not cause submission under a different interpretation. [S8]

## 5. Completion reviews remaining commitments

Keep the requested default: direct micro tasks begin as **Done with parent**. Make this an explicit proposed outcome, not a collapsed row, an unchecked selection box, or a completed ordinary task created before the user decides.

Separate **disposition** from **pull-in selection**:

| Root disposition on Apply | Ordinary task created? | Daily Task Link? | Source result | Descendants |
| --- | --- | --- | --- | --- |
| Done with parent, default | No | No | Terminal Done receipt | Inherit Done, except already settled descendants |
| Keep open | One task for this root | No | Struck title, Continued receipt, forward link | Move as active micro tasks and notes beneath the new task |
| Keep open + checked | The same one task | Yes, normal placement | Same Continued receipt | Same owned subtree; no separate descendant links |
| Cancel | No | No | Struck title, Cancelled receipt | Inherit cancellation, except already settled descendants |

Space/Tab controls pull-in **only after Keep open**. On Done/Cancel rows it must not silently create work; say “Ctrl-X to keep this work open first.” Ctrl-A selects only eligible open roots and ordinary selectable successors, never nested rows. Returning Keep open to Done/Cancel clears pull-in selection.

Ctrl-X toggles a micro root between Done with parent and Keep open. Ctrl-Shift-X stages Cancel with the existing optional reason convention. Ordinary successor rows retain Ctrl-X → Done. Since the same key has opposite-looking consequences, the footer must follow the highlighted row: **“Ctrl-X keep open”** on a default-Done micro root, **“Ctrl-X done”** on an open ordinary successor. Text buttons use the same verbs. Never show a global “Ctrl-X done” legend over default-Done micro rows.

Nested rows show indentation, depth badges, and **“Follows Verify recovery”**. They have no selection box or independent verdict controls. They can be focused for reading/expansion; action keys skip them. Expand the micro tree initially, subject to scrolling/virtualization, so nested commitments are available for review. Counts distinguish direct decisions from inherited descendants.

Illustrative state after opening one root and selecting its pull-in:

```text
Close “Release the service”

MICRO TASKS                      2 direct · 2 nested
 ✓  ## Verify recovery           Done with parent
      ### Restore a snapshot     Follows Verify recovery
      ### Run the smoke test     Follows Verify recovery
 ☑  ## Publish the runbook       Keep open · pull in → BUILD

OTHER SUCCESSORS
 ☐  Document the release metrics

1 done · 1 kept open · 1 pull-in
Ctrl-X done    Ctrl-Shift-X cancel    Tab pull in and move
Enter close and apply    Esc back
```

Do not create completed ordinary tasks for default outcomes: that inflates counts, creates anchors, and turns lightweight structure into a shadow task database.

The request's note “next to” the old micro bullet linking to its original parent is ambiguous. Useful provenance is **two-way**: the old micro bullet links forward to the new task; the new task links back to the original parent. A self-link to the parent on its own child adds little.

## 6. Persist clear outcomes; a strike is not a status

Strikethrough can mean completed, abandoned, or moved elsewhere. Store explicit receipts on settled roots and render distinct outcomes. Proposed source:

```markdown
- [x] #task Release the service [completion:: 2026-11-20] ^release
  - TASK: Verify recovery [micro:: done]
    - TASK: Restore a snapshot
    - TASK: Run the smoke test
  - TASK: ~~Publish the runbook~~ [micro:: continued] [micro_to:: [[work#^runbook|Publish the runbook]]]
  - TASK: ~~Tune the legacy cache~~ [micro:: cancelled]
```

`micro` and `micro_to` are proposed fields, not existing Bob syntax. They apply only to parsed micro nodes. No receipt means an active embedded commitment. `continued` requires exactly one target or a reported broken-reference state; it never means silently create another task. Reject contradictory or unknown receipt values for mutations. Dates can come from the enclosing close initially; a separate micro-event date is unnecessary for this flow.

Rendered mode folds receipts into **✓ Done**, **↗ Continued**, and **⊘ Cancelled**. Keep title strikes for Continued and Cancelled as requested, and a forward link beside Continued. Source words remain meaningful without plugins.

The extracted task gets the root's title without `TASK:`, receipt fields, or presentation strikethrough. Its active children and notes become its body. A retained historical copy below the old Continued root is inactive history, never another active micro tree. Do not duplicate live anchors across new body and old snapshot: transfer/rebase anchored descendants, repair references, and omit anchors from the historical copy. This needs transplant/link repair, not string substitution.

Reuse split's destination rules: below the owner in an ordinary note; for a daily-note owner, into the root note's Tasks intake or inbox. Use existing reverse-mention policy for the backlink. Do not invent a dependency on the parent or copy its completion date, schedule, priority, or keep count. An unpicked continuation is a normal new task; a checked continuation uses the existing selected-birth/pull-in policy. Do not mistakenly freshen it as an existing task just because it now appears in the scan.

Existing terminal descendants stay terminal. Reopening the parent does not resurrect cancelled, continued, or explicitly settled micro work, matching ordinary successor verdict behavior. A later explicit micro-root reopen action can restore work. If a continued target disappears, report the broken link; do not mint another task.

## 7. Close and extraction must succeed together

Necessary correctness properties:

- A micro subtree has exactly one active owner after success.
- Continued means the target was successfully created; Cancelled means explicit cancellation.
- The API rejects independent verdicts on nested rows, even from a buggy client.
- Task Links require explicit eligible pull-in selection.
- Preview, opening the panel, and Escape do not allocate persistent task identities or mutate notes.
- Repeated Apply/retry cannot duplicate tasks or daily links.
- Notes, code, managed links/logs, and real nested tasks are never silently promoted or discarded.

For a close involving active micro tasks: **preview → choose → revalidate → one guarded write plan**. Include parent status, receipts, extracted tasks, provenance, and selected ledger links. Bind selectors to owner identity, node structural path or anchor, and a digest of the displayed subtree/preimage. Identical titles remain distinguishable. Reordering/editing a subtree invalidates stale selection; never substitute similar text.

Use current locks, staged writes, preimage checks, recovery evidence, and guarded Undo. One operation does not imply filesystem-level multi-file atomicity: detect failures, roll back partial writes when safe, and surface unresolved recovery. Persist the target before retiring the source, with recovery evidence connecting the writes. Never report the parent fully settled while a requested continuation failed to materialize.

**This changes the Obsidian micro-close boundary.** Ordinary successor verdicts can currently fail individually after predecessor closure. [S7] Creating the only surviving active representation of unfinished work needs a stronger boundary. Stage parent closure until Apply. Compute ordinary successors against the hypothetical post-close state, then apply the combined plan. Delegate this path to Bob's planner/write shell rather than adding another ad hoc client writer.

Therefore **Esc backs out of the micro-close and leaves the parent open**. This differs from today's ordinary “Esc means no pull-ins; predecessor remains closed.” Say so in the footer. Enter explicitly accepts default-Done roots, even if no row was touched. With micro decisions present, Enter must never fall back to selecting the highlighted row when none are marked.

Without micro work, preserve today's ordinary flow. Suspend the review-walk gesture across the micro card and advance exactly once after success; Escape and stale refusal do not answer the walk.

Audit task hotkeys, capture closes, Pomodoro closes, relation-driven completion, successor-card completion, and bulk closes. If resolving an ordinary successor reveals micro children, include them in the staged tree or refuse with “Review its micro tasks first.” Do not bypass review through nested completion.

Parking is not completion: keep micro work embedded and unsettled. Parent cancellation is not Done: use the same review machinery with Cancel as inherited default if retaining work is supported, or explicitly cancel the embedded subtree. Recurrence needs separate scrutiny; never copy terminal receipts into the next occurrence. Until reset semantics are tested, refuse managed micro-settlement on recurring tasks with a focused explanation.

Raw Markdown and third-party checkbox writers cannot be assumed to call Bob's API. Detect closed owners with active receipt-less micro roots as **micro review needed**, with a recovery action. Reconcile must not mark them Done, extract them, or erase them. This is a repair path, not a substitute for covering supported Bob gestures.

## 8. Promotion and merge preserve one model

**Task → project:** convert each active direct micro root into one ordinary project task. Nested micro tasks remain nested under it; its notes/drawers remain its body. Outer bare notes become the project's Notes section; explicit drawers become sections. Preserve existing managed-line/log handling. Settled receipts remain history, never new open work.

Promote **one ownership level at a time**, rather than flattening descendants. Flattening loses containment; recursively creating subprojects now exceeds scope and needs identity, schedule, dependency, and naming rules. A promoted micro root can itself become a project later.

Existing real nested `- [ ] #task ...` rows stay real tasks; do not demote them implicitly. Preserve IDs, outcomes, and applicable existing behavior. If lossless placement is unavailable, preview/refuse instead of dropping content. Test narrow existing project→task reversal with the new output even though arbitrary project collapse is out of scope.

**Task-target merge:** write `TASK: <source description>`, retain plain notes under its local NOTES semantics, drawers beneath that root, and existing micro children one level deeper. Keep terminal receipts terminal. An ALL-CAPS source title still means work because the prefix wins.

Apply through the shared engine for relation `merge_labels`, capture transfer `>`, and merge-in `<` whenever the target is an ordinary task. The result should not depend on the invoking gesture. This expands the request, which only mentions merge labels, for consistency.

Preserve source tombstones, dependent repair, managed history, cycle checks, anchor sanitation, and selected replacement-link rules. Do not silently transfer prerequisites or successors: current merge intentionally leaves those with warnings. [S6] Change commitment representation, not the whole graph policy.

**Drawer/section targets express different intent.** Preserve their note-filing behavior: merging explicitly into a drawer or note section produces notes, not actionable micro work buried in a note container. Preview “Merge as notes into REQUIREMENTS”; task targets say “Merge as micro task.” This is an explicit scope choice. Making every merge destination retain executable work would require changing drawers and sections too.

Thus merge needs more than adding six bytes. Test nested micro trees, mixed notes/drawers, source cancellation history, terminal descendants, repeated merges, anchors, and target kinds. Share child classification across merge, promotion, split, capture, and rendering.

## 9. Calm, accessible presentation

Use current task-mark typography and baseline for `##`, `###`, and deeper badges. Titles stay body-sized; the badge is neither a heading nor a tag link. Hover can say “Micro task · level 2 · part of Verify recovery.” Accessible names expose role and depth rather than asking a screen reader to count hashes.

Prefer compact indentation guides and full titles over extra chrome. Done uses a check, Cancelled a slash, Continued an arrow plus target, each with text in the panel. Use existing outcome hues, but maintain contrast for inherited rows. Non-actionable does not mean unreadable.

Cover Live Preview, reading view, embedded task blocks, and capture preview. Expose source markers/receipts when the caret enters their ranges, following the mark pattern. Copy raw Markdown faithfully. Check formatting-disabled fallback, zoom, light/dark themes, selection, IME, and mobile reading. Avoid literal field syntax in tooltip HTML because Dataview can rescan it. [S9]

For unusually deep trees, preserve semantics and offer scrolling or a compact depth readout rather than refusing content because badges grow wide. Start with repeated hashes as requested; cap their visible run only if usability checks justify it, while exposing exact depth. Avoid a separate dashboard, percentages, or progress bars: this is containment and closure review, not another planning layer.

## 10. Migration, compatibility, and verification

Migration is the highest semantic risk. Existing bare bullets mix notes and work. No syntax-only transformation can infer intent. Do not heuristically mark every verb-looking sentence.

Before enabling new promotion behavior in an existing vault, offer a read-only inventory using the **old converter's exact eligibility rule**. Let the user select actual commitments. Preserve text, order, and anchors, preview changes, and make them reversible. New capture writes explicit structure. Do not retain a permanent “legacy unmarked bullets are tasks” fallback: it preserves the ambiguity being removed. Equally, do not silently reclassify a large vault and claim intent cannot be lost merely because bytes survived.

Use capability negotiation across Bob, navigation, cycler, Ledger Tools, and Mac. Grammar revision and successor-row schema need explicit consideration; grammar is currently revision 28, but choose the actual next revision when landing. [S2] Add fields where compatible, but do not assume an older picker can safely consume a new row kind. Unsupported clients should refuse micro-aware mutations clearly rather than treating roots as ordinary offers or notes. Ship compatible consumers through existing release/deployment workflows and the daily release train.

The main seam is a parsed authored-body tree separating notes, drawers, micro tasks, real tasks, managed links, and managed logs. Canonical capture recognition, validation, transformation, and write planning belong in bob-cli. Reuse `task_children`, split/transplant helpers, and successor placement. Obsidian needs a small local parser/projection for immediate decoration; share Rust/JavaScript fixtures without making the presentation parser a second write policy. Swift consumes Bob's spans, rewrite edits, outcomes, and eligibility.

Suggested dependency order: semantic contracts and tree fixtures; parse/write/preview support; split-based extraction and guarded closure; client presentation; conversion/merge adoption; reviewed migration and glossary publication. These are dependency boundaries, not independently shippable incompatible interpretations.

| Area | Required acceptance evidence |
| --- | --- |
| Marker | Exact prefix, uppercase titles, escapes, inline/fenced code, quoted examples, unknown receipts, existing checkboxes |
| Tree | At least three micro levels with notes/drawers; stored indentation styles; invalid capture jumps; moving a subtree changes badge depth only |
| Notes | Single-line `@foo+bar`, note-less multi-bullet capture, new task, existing NOTES, explicit drawer, micro-local notes |
| Input | `.. ` and Undo; `...`, `../`, paste; project Move `- .`; old dot escapes; Ctrl-G U; IME, selection, timeout, stale edits |
| Close | Every disposition × selection; no tasks for Done/Cancel; no child verdicts; identical titles; no highlighted fallback |
| Extraction | Ordinary/daily owners; anchored descendants; same-note links; backlinks; one active copy; birth/freshness/Next semantics |
| Concurrency | Owner/descendant edits; changed destination/ledger; retries; duplicate Apply; partial-write recovery; guarded Undo |
| Promotion | Notes-only owner creates no spurious work; drawer sections; nested micros preserved; terminal receipts stay terminal; narrow reversal |
| Merge | All task-target gestures agree; drawer/section intent; nested micros; existing refusals, dependencies, and history |
| Surfaces | Task hotkeys, capture, Pomodoro/bulk closes, relation Done, successor Done, parent cancellation, recurrence gate, raw-edit repair |
| Compatibility | Old/new binary/client combinations, mixed plugins, source fallback, deep-tree and keyboard rendering |

Use shared golden vectors for Rust/JavaScript parity and end-to-end write-plan tests. Cross-note failure injection is more valuable than many tests mirroring the prefix regex. Swift must pass the required macOS build/CI workflow; visual claims require actual Obsidian and Mac checks. This research has not established those runtime results.

## 11. Proposed glossary entry

**Micro Task** — aka *micro task*, *embedded commitment*.

> An explicitly marked unit of work inside an ordinary task or another micro task. Its source is a plain bullet beginning `TASK:`; Bob displays that marker as `##`, adding one `#` for each micro-task ancestor. A micro task belongs to its containing task: it can hold notes, drawers, and smaller micro tasks, but has no independent planning lane, schedule, dependency edges, or Pomodoro Task Link while embedded.
>
> When its owning ordinary task is completed through Bob, each direct micro task is reviewed in the successor panel. It defaults to Done with parent. Keep open turns its entire active subtree into one new ordinary task; a separate pull-in selection links that task into today's plan. Cancel records abandoned work. Nested micro tasks follow their root's decision. Promoting the owner to a project turns direct active micro tasks into project tasks while preserving their nested micro structure.
>
> An unmarked bullet is a note, even when it describes an action. A micro task is not an ordinary nested checkbox task, a Task Dependency Link, or a duration estimate. “Micro” describes where the commitment lives, not how quickly it can be finished.

When implementing, use glossary links for established terms and add the requested `micro-task` strand. Review Task Drawer, Task Successor, Successor Offer, Task Merge, and Capture Alias for objective changes. Record superseding decisions for changed capture/default-note semantics rather than rewriting accepted historical decisions. This report proposes the entry; it does not publish an unimplemented feature into live memory.

## 12. Evidence map and limits

Paths are relative to the named repository at the commits above; no ephemeral checkout paths are embedded.

| Ref | Evidence |
| --- | --- |
| S1 | bob-plugins `plugins/bob-navigation-hotkeys/src/110-project-seed.js:1`, direct-child conversion around line 193; `plugins/bob-navigation-hotkeys/src/100-yank-and-paths.js:508`; `plugins/bob-navigation-hotkeys/src/667-plugin-project-promotion.js`; bob-cli `docs/projects.md`, Promotion successors and following conversion rules |
| S2 | bob-cli `src/native/capture_language/draft.rs:920`, `:940`; `src/native/capture_language/model.rs:908`; `src/native/capture_language/mod.rs:63`; bob-mac-capture `docs/keyboard.md:375` |
| S3 | bob-cli `src/native/capture_language/drawer_bullet.rs`, especially `finish_execution_drawer_bullets` and `is_all_caps_drawer_title`; `src/native/capture_language/completion.rs` |
| S4 | bob-cli `src/native/capture/sub_bullet.rs:44`, `plan_sub_bullet_capture`; `src/native/capture_drawers.rs` |
| S5 | bob-cli `docs/task-split.md` §§1–4; `src/native/task_split/plan.rs`; bob-plugins `plugins/bob-navigation-hotkeys/src/256-task-split-plan.js`, `257-task-split-apply.js`, `653-plugin-task-split.js` |
| S6 | bob-cli `docs/task-merge.md` §§1–5; `src/native/task_merge/payload.rs:465`, `source_payload`, and `build_payloads`; `src/native/task_children.rs` |
| S7 | bob-cli `docs/task-dependencies.md:3638`, §12.22 and §12.23; `src/native/task_complete/successors.rs:102`; `src/native/task_complete/offer_close.rs`; bob-plugins `plugins/bob-navigation-hotkeys/src/206c-successor-picker-verdicts.js`, `206d-successor-picker-verdict-render.js`; `plugins/task-status-cycler/src/137a-successor-offer-close-integration.js` |
| S8 | bob-cli `src/native/capture_language/rewrite.rs`, `alias_tip.rs`; bob-mac-capture `Sources/BobMacCapture/CaptureKeyCommandRouter.swift:979`; `docs/keyboard.md:381`; audited Capture Alias glossary |
| S9 | bob-cli `docs/task-tag-marks.md`; bob-plugins `plugins/bob-ledger-tools/src/138-task-tag-marks.js`, `264-plugin-task-tag-marks.js` |
| S10 | bob-cli `src/native/note_tasks.rs:365`, `parse_task_line`, requiring checkbox syntax and configured global filter |
| M1 | Audited reads of `glossary:task-drawer`, `task-merge`, `successor-offer`, `task-successor`, `task-link`, `project-note`, `capture-alias`; `decisions:capture-bullets-mirror-the-task-block`, `unblocked-tasks-are-offered`, `mac-capture-is-a-thin-client` |

External sources support Markdown/tag/filter interoperability points, not claims about how Bob should behave. Lifecycle, hierarchy, migration, and transaction recommendations are design conclusions from the request and implementation. No peer research, unrelated historical report, or private vault content was used.

## 13. Critique and recommended solution

The proposal's strongest part is explicit intent: information stays information, and commitments are visible at closure. It also makes task→project promotion predictable. Its weakest interpretation would treat micro tasks as cheap full tasks with metadata, then try to hide that complexity. That recreates a project inside every task.

Default-Done is efficient but does not prove completion. Keep it because it matches the requested workflow, while requiring explicit Apply, showing nested work, and reporting outcome counts. Do not describe it as a hard completion checklist. If experience reveals accidental completion, change that review default later rather than adding mandatory per-row acknowledgment now.

The future project→equivalent-task direction is sensible, but this feature alone cannot make arbitrary collapse lossless. Projects carry file identities, incoming links, blocking, sections, independent tasks, schedules, and subprojects. Future collapse needs an explicit mapping for all of them. Preserve containment and reference handling now; do not claim an outline already equals the original project graph.

**Requirements I would adjust:** choose `TASK:` instead of `#task`; render hashes without storing them; distinguish Done, Continued, and Cancelled; stage parent closure until micro review applies; make Escape abort that close; promote one ownership level at a time; use micro roots across task-target merge gestures while preserving drawer/section note merges; narrowly scope `.. `; and require reviewed migration instead of guessing which old notes were commitments. These changes strengthen the goals while keeping micro tasks lightweight.

**Recommended solution:** build explicit `TASK:` micro trees, implicit NOTES for old unmarked prose, and explicit NOTES for new captured notes. Add contextual `.. ` and Ctrl-G T editing with compact hash-badge rendering. Extend the successor card with default-Done roots, read-only nested context, Keep open plus independent Pull in, and explicit Cancel. Materialize with split/transplant primitives, settle with parent closure under guarded writes, and retain clear provenance receipts. Adopt one classification contract in promotion and task-target merge, ship compatible clients and reviewed migration, and publish the Micro Task glossary with the implemented behavior. This delivers closure review and a foundation for future structural conversion without turning every sub-bullet into another task to manage.
