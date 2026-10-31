# Capture drawers and percent directives: independent design research

Researcher: **cdx** · 2026-10-31

This report was researched independently. No other report, transcript, summary, or findings from this swarm were consulted. The investigation used the current bob-cli checkout, SASE-audited reads of `bob-cli-ep` and `plan:202610/capture_hash_type_marker.md`, the linked Mac and plugin checkouts, isolated command probes, and Apple documentation. This is a design recommendation, not an implementation or a claim that the proposed syntax already works.

**The proposed direction is good.** Giving `@file+id#drawer` one meaning removes a particularly troublesome ambiguity: adding or deleting body text currently changes the attached hash from a task type to a task section. Moving three special operations behind `%` also creates an obvious discovery point and frees a bare task-type `#` to open its menu immediately. I would implement this cleanup, but treat it as a coordinated language change, not a token replacement. The important additional work is parent-task retyping, template framing, safe automatic drawer creation, truthful clipboard preview, and protection against mismatched app and CLI versions.

The concise model to teach is: **`@` selects a destination or task; an attached `#` refines that destination; a separate `#` selects a task type; `%` selects an operation.** Existing Pomodoro syntax remains a specialized part of the language. Do not claim that every hash outside `@file+id` is a type marker.

**What the current system actually does.** Source inspection used these revisions:

| Repository | Inspected revision |
| --- | --- |
| bob-cli | `5e2d0856f3539fb632d418c6c1da3761cc3655dd` |
| bob-mac-capture | `ec3fff5fe056a2db78baa4fff3161eaf51018a15` |
| bob-plugins | `3942eb8190e4607ae99e977eea59dff44794a19c` |

The installed `bob 0.4.0` was also exercised against a disposable fixture inside this workspace, with its own vault, config, daily note, and state-directory override. Its exact build SHA was not established; the source findings below are independently checkable at the revisions above. All capture probes used dry-run, and no real vault content was read or changed by these probes.

| Probe | Observed result |
| --- | --- |
| `@foo+bar#requirements` | `task_toggle`, with `#requirements` parsed as `task_type` |
| `Some note goes here. @foo+bar#requirements` | `sub_bullet`, with section `requirements` |
| `Some note goes here. @foo+bar#requirements #fix` | Refused: `type_marker_not_applicable`; adding a child bullet cannot currently retype its parent |
| `Some note goes here. @foo+bar#missing` | Dry-run refuses because the section does not exist |
| `Some note goes here. @foo+bar#req` | Dry-run succeeds by prefix-matching `REQUIREMENTS` |
| Completion at `@foo+bar#` | Task types, even though the body-bearing equivalent offers sections |
| Completion at `Some note @foo+bar#` | `REQUIREMENTS`, `FUTURE WORK` |
| `A note #` | `pomodoro_note`; no completion candidates |
| `A note %c` and `A note %n` | Both currently parse as clipboard captures with headers |
| `Read {0} %t` followed by rows | Clipboard header `t`, with a warning that the template header is missing |

The exact example in the request therefore requires a new semantic combination, not merely a renamed completion context. The attached type lexer deliberately checks whether an item is marker-only, and existing-task type eligibility deliberately excludes body-bearing child captures. Both decisions must change together. [Type scanning and subject classification][s1], [type application][s2].

The existing task-section machinery is valuable. It already enumerates **direct-child plain ALL-CAPS bullets**, excludes checkbox children and managed log markers, reports child counts, preserves indentation, and locates insertion points before managed logs. Completion currently offers only sections already on the selected task. The write resolver chooses an exact slug or the first prefix match, then errors on absence. Reuse the structural scanner and insertion helpers; replace the resolution policy. [Task-section scanner][s3], [sub-bullet planner][s4], [completion candidates][s5].

Project conversion already promotes qualifying ALL-CAPS child bullets into title-cased H2 headings, including `REQUIREMENTS` → `## Requirements`. It requires at least one nested list item; an empty ALL-CAPS bullet is currently not promoted. Its title grammar is intentionally narrow, and `API DESIGN` becomes `Api Design`. This feature should preserve that existing conversion policy. A newly created drawer with its first captured bullet immediately satisfies the nonempty requirement. [Plugin conversion helpers][s6], [project seeding][s7].

`bob-cli-ep` is closed. Its accepted choices were to open the free-standing type menu only after a letter, retire `t:` as prose, and add no decision-memory record. The bare-hash choice protected the old Pomodoro-note gesture. Moving that gesture to `%n` removes its reason to remain. The epic also deliberately retained attached `@route^id#type`; that form is outside the requested retirement. The audited epic and plan are the provenance for these statements, rather than another researcher's interpretation.

**Recommended language contract.** Keep context decisions entirely in Bob and make them independent of when or in which order the user typed the draft.

| Input | Recommended meaning |
| --- | --- |
| `Some note. @foo+bar#requirements` | Append a plain bullet to the target task's REQUIREMENTS drawer, creating that drawer if needed |
| `Some note. @foo+bar#requirements #fix` | The same append, plus retype the existing `^bar` task to FIX in the same transaction |
| `Some note. @foo+bar #fix` | Append directly under the target task and retype that task |
| `@foo+bar #fix` | Preserve the existing marker-only Ensure Next/retype action; show both effects in preview |
| `@foo+bar#requirements` with no authored content | Incomplete drawer capture; request content, never silently toggle the task or create an empty drawer |
| `Some note. %n` | Append to today's current timed Pomodoro, falling back to the last completed one as the old gesture does |
| `Investigate failure %c` | Capture clipboard material under this item's parent text |
| `Investigate failure %c3` | Capture three clipboard/history entries, retaining today's all-or-nothing history behavior |
| `Investigate failure %c:build_log` | Capture the current clipboard under the existing formatted BUILD LOG header |
| `Read {0} @books %t`, blank line, rows | Expand the first template block for those rows without moving `%t` |
| `Some task #` | Incomplete task-type marker with the full type menu immediately open |
| `Some note @foo+bar#` | Incomplete drawer selector with the drawer menu immediately open, even before body text exists |

The extensions `%c3` and `%c:build_log` are explicit recommendations. The directive identifier is still exactly one character; the suffix supplies arguments. A colon separates a named header from the directive, avoiding an open-ended `%canything` mini-language. `%n` and `%t` accept no arguments. Keep identifiers lowercase and do not introduce redundant long or uppercase aliases. Invalid counts and arguments should diagnose, rather than fall back to ordinary content.

Directives should use one shared marker-position rule: a whitespace-delimited token at an accepted leading or trailing marker edge, including authored child-line marker edges where item-wide modifiers already work. Protected code, links, URL bytes, escapes, and ordinary mid-sentence text remain literal. `%` at an eligible edge is an incomplete directive, not a clipboard capture. `50%`, URL percent encoding, and prose such as `use %s here` must not become directives. A trailing formatting token that really is prose can use the shared escape convention. Do not solve this by searching for every `%` anywhere in the string.

Hash completion still needs the existing context precedence:

| Context | Menu |
| --- | --- |
| Free-standing `#` at a type-marker edge | Task types |
| `@file+id#` | Task drawers, with or without body text |
| `@file#` | Note headings |
| `@file:id#` and applicable Pomodoro start forms | Pomodoro names |
| `@file^id#` | Existing explicit-ID task type behavior |
| Code, links, URL fragments, escaped hash, prose positions | Their existing literal or specialized behavior |

This is a necessary narrowing of “show task types whenever hash is not after `@file+id`.” Otherwise the change would break several unrelated, established hash contexts.

**Make drawers structurally boring and writes precise.** A drawer should remain a Markdown convention, with no new inline fields, UUIDs, or metadata on task lines. Use the existing direct-child scanner and its title predicate. Descendant ALL-CAPS bullets belonging to nested tasks are not drawers of their ancestors. Checkbox tasks, Markdown headings embedded in code fences, and managed logs are not drawers.

The requested example should produce this structure, assuming FIX differs from the parent's inherited type:

```markdown
- [ ] #task Existing target [type:: FIX] ^bar
    - REQUIREMENTS
        - Some note goes here.
```

The actual indentation and field placement follow existing writers. If FIX is inherited, the explicit field is cleared or omitted instead. If the parent has live Task Links, apply the existing type-relocation rules and show those changes too. This is one transaction: invalid type, ambiguous task ID, stale note, or failed ledger relocation must leave both the drawer and its new content unwritten. Body-bearing drawer capture must not accidentally invoke the marker-only Ensure Next action. Preserve ordinary note-append behavior on completed tasks, but retain existing retype eligibility restrictions when `#type` is present. [Type field and relocation integration][s2], [transaction guards and rollback][s8].

Use **exact resolution at commit**. Prefix and fuzzy matching belong in suggestions. Once creation is allowed, the current “first matching prefix” rule becomes surprising: `#req` could append to one existing drawer, pick another after a reorder, or create REQ in another task. Recommended behavior is deterministic: accepting REQUIREMENTS inserts its complete selector; submitting `#req` without accepting means the explicitly previewed new REQ drawer.

Keep two forms for names:

- A compact slug, such as `#future-work`, with a canonical title for newly created drawers of `FUTURE WORK`.
- A quoted exact title, such as `#"FOLLOW-UP"` or `#"Q&A"`, for punctuation, whitespace, and slug collisions.

For existing drawers, preserve the authored title. Resolve a slug only when its exact normalized slug identifies one drawer. For quoted titles, use case-insensitive, whitespace-normalized title equality while preserving punctuation. `FUTURE WORK` and `FUTURE-WORK` can share a slug under today's algorithm; never silently collapse those two existing nodes. Completion can emit a quoted exact selector to disambiguate their titles. Duplicate identical titles under one task should diagnose and identify the conflicting locations, not append twice or choose whichever appears first. [Current slug function][s9].

On creation, validate the resulting ALL-CAPS title with the shared section predicate before staging a plain child bullet and its contents. Insert alongside the parent's existing drawers, before managed logs, with the existing indentation and line-ending helpers. Re-resolve from staged text between items so two captures into the same new drawer in one batch create one drawer and two entries. Recheck on submission; menu state is not authority. A near miss may show “Similar drawer: REQUIREMENTS,” but must not silently redirect a typed new name.

The drawer catalog should unify **suggestions**, not invent a new project-targeting path. After project promotion, an ordinary project H2 remains targetable through the existing note-section route. Do not add magic that interprets `@project+prj#requirements` as a sibling H2 instead of a child of `^prj`; that makes the same syntax change meaning with the note's frontmatter.

**A completion menu that explains the destination.** Typing the attached hash should open the menu immediately, including on a marker-only draft. Show the target task as the menu's context, the drawer name as the primary label, and existing entry count or creation effect as secondary text.

```text
Drawer in foo · Existing target

ON THIS TASK
  REQUIREMENTS        4 notes
  FUTURE WORK         Empty

RECENTLY USED
  ACCEPTANCE          Add drawer here · used in checkout
  DESIGN              Add drawer here · used in release-plan

  Create “RISKS”      Add drawer here
```

The final Create row appears only for a nonempty valid query that has no exact local match. On an empty query, do not offer an empty drawer. Local candidates always occupy the first group. Within a group, rank exact, prefix, then substring matches; preserve document order for local empty-query rows and use actual recency for reused names. Keep the list bounded, with deterministic ties. A missing or ambiguous parent produces a useful diagnostic; it must not show a plausible “Create” row for an unresolved target.

Recent suggestions need more than filesystem mtimes. A file touched today does not prove that every heading in it was used today. Build a Bob-owned derived catalog of task drawers and eligible project H2s, with invalidation from changed note contents. Filter out fenced text, generated task/status sections, structural Tasks/Pomodoros headings, daily notes, and unrelated reference headings. Restrict project-derived candidates to names that can round-trip into the drawer title grammar. Deduplicate by title identity, preserving source labels and handling ambiguous slugs separately.

Track successful drawer/section capture usage in a small, bounded, vault-scoped local history, analogous in ownership to the saved-template shelf. Record only after a successful capture; completion, preview, retries that failed, and keystrokes are not usage. A disposable index can seed additional names from recently changed eligible project notes, but label those “Other project notes” rather than pretend their mtimes are usage timestamps. Task-local drawers remain available even if this auxiliary history fails. No synchronized preference journal or vault metadata is needed for a suggestion ranking feature. Exact ordering across machines is not a requirement I would add here.

On `%`, use three stable rows, always in `c`, `n`, `t` order:

```text
Capture directive
  %c   Clip Clipboard     Add clipboard content below this item
  %n   Add Pomodoro Note  Write a note in today's current or last completed session
  %t   Use Template       Repeat this block for the values below
```

Use short action labels, one explanatory line, consistent spacing, and familiar keyboard behavior. Existing app navigation should remain: arrows/Ctrl-N/Ctrl-P select; Tab or Return accepts one completion; accepting does not also submit; Escape dismisses. A later Return submits the complete draft. Type coloring can remain for task types; drawer and directive meaning must remain understandable without color. VoiceOver should read the row's title, effect, and destination. Apple recommends clear action labels and discoverable unavailable commands; that supports this presentation, but the particular groupings above are a design proposal for Bob. [Apple menu guidance](https://developer.apple.com/design/human-interface-guidelines/menus).

The preview should tell the truth in one compact block:

```text
foo → Existing target → REQUIREMENTS     New drawer
  • Some note goes here.
Type: BUILD → FIX
```

If a ledger link moves, include that effect beneath the type change. Reuse the existing task-block preview and layout rather than create a separate wizard or modal for adding a drawer.

**Keep Bob authoritative across all surfaces.** The accepted thin-client decision makes Bob responsible for grammar, completion replacements, semantic spans, destination resolution, and preview. Swift should receive a directive completion context and drawer candidate metadata, not infer “the character before the caret was `%`” and parse the draft itself.

Suggested additive fields include a candidate's `origin`, `effect` (`append` or `create`), canonical title, source label, and last-used value when known. Continue to use `task_section` internally if that minimizes churn; present “Drawer” to users. Naming every internal struct `Drawer` is not required for a good public vocabulary. Extend the existing type-subject contract so body-bearing `@file+id` captures report `subject: existing`, resolve that parent's current and inherited type, and propose the correct set/clear/keep effect.

Bob should return exact replacement ranges and complete replacement text, including quotes when needed. Maintain UTF-8 byte offsets and nonoverlapping semantic spans; Mac converts these to editor ranges. Completion results must be guarded by draft generation, caret position, target identity, and process identity so delayed answers cannot overwrite a newer draft. Accepting a suggestion must invalidate any preview of the previous text. The current architecture already separates parse, completion, preview, and submit; extend that contract rather than creating a second parser in the app. [Mac process client][s10], [type completion subject logic][s11].

**Templates need a framing decision.** The old system requires `@@template:` on the first nonblank line. Typing `@@@` can delete that token and insert a new header at the top of the draft. The template engine already has row validation, placeholder expansion, source maps, size limits, and per-row editor diagnostics. Preserve those mechanisms while replacing the header assumption. [Template parser][s12], [rewrite gesture][s13].

I recommend **one template block per draft**. The first nonblank block is the template definition and contains exactly one `%t` in an eligible marker position. It can sit at either edge of the parent line or at a marker edge on an authored child line; it stays exactly there. A directive-only first line followed immediately by the template parent is also allowed. Strip `%t` semantically, not by rewriting the editor buffer. The first blank separator after the definition begins the value rows.

```text
Send {0} a follow-up @clients %t
- Context: {1}

Alice "Pricing discussion"
Bob "Delivery date"
```

This expands two captures with their own child context. Leading `%t Send …` means the same thing. For a fresh draft, selecting Template inserts `%t` at the caret and displays “Add a template with {0}; blank line; then values.” It does not insert a distant header or relocate the cursor.

A `%t` on a later value row is an error, not a request to reinterpret preceding rows. Multiple template directives, mixed ordinary capture blocks before the definition, and nested template expansion should refuse. These restrictions are an explicit scope adjustment: “leave it where typed” is not a promise of arbitrary template scoping anywhere in a multi-item document. That broader language would require a new delimiter design and is unnecessary for replacing the current facility.

Preserve dense zero-based placeholders, quoting, escaped braces, existing one-field row splitting, all-or-nothing expansion, the 1,000-row and 1 MiB expansion limits, and source locations into the original draft. Masking must preserve source lengths when deriving editor spans. Parameter substitution must not recursively activate a second `%t` or resurrect retired global declarations. The same expansion must feed `-E`, `capture-parse`, completion, related-task analysis, dry-run, and submission.

Keep clipboard acquisition forbidden in template expansion initially: `%t` plus `%c`, including a `%c` introduced by a row value, should diagnose rather than repeatedly read a changing clipboard. `%t` plus `%n` can produce one Pomodoro note per row through the ordinary planner. Drawer destinations inside templates are useful and should work, including repeated rows targeting the same newly created drawer. Reject duplicate mode directives and conflicts such as `%n` plus an explicit task destination or a task type; preserve `%n %c` as a note with clipped child material where the existing planner supports that composition.

The saved-template shelf stores canonical definition text **without the old header**, keyed by a content hash. That is good news: ordinary saved entries need not be discarded or maintained through an old-syntax parser. Update rendering of a saved entry to insert a new in-place `%t` marker; exclude that marker from canonical body identity so reuse does not create duplicate shelf entries. Definitions containing removed syntax need repair rather than a compatibility execution path. Audit retained/canceled raw drafts as well; they differ from canonical saved definitions and may contain old tokens. [Template storage][s14], [saved-draft rendering][s15].

**Clipboard preview should become semantic first, resolved second.** Today Mac live preview calls `capture --dry-run --no-clip`. Bob uses `--no-clip` to disable clipboard marker parsing, leaving the marker in body text. An explicit preview uses a different path that reads the clipboard. Simply replacing `%` with `%c` preserves this mismatch. [Planner options and clipboard acquisition][s16], [Mac live/explicit preview][s10].

Separate two decisions in Bob: whether the draft requests a clip, and whether this invocation may acquire its payload. Always parse `%c` in the new app's semantic preview. With acquisition deferred, return a structured pending clip effect and a correct destination preview; never render `%c` as text that will actually be written. Introduce a clear preview acquisition option instead of quietly changing `--no-clip`'s existing literal-text meaning. Read the CLI-rules memory before choosing or adding that option during implementation.

When a complete `%c` request settles, the app can automatically request a resolved read-only preview. Do not read clipboard data merely because `%` opened the directive menu. Cache the response for the request, invalidate it on relevant draft changes, app reactivation, clipboard changes, or explicit refresh, and reuse Bob's rendered clip lines/attachments. Mac may observe the pasteboard change count for invalidation; Apple documents it as a counter of pasteboard ownership changes. It is not a complete version of clipboard-history data or files referenced by a clipboard path. [Apple `changeCount` documentation](https://developer.apple.com/documentation/appkit/nspasteboard/changecount).

For reliable preview-to-submit behavior, return a Bob-computed fingerprint of the resolved clipboard inputs and applicable attachment contents. Submit can supply an expected fingerprint; Bob re-reads once, compares, and plans from those same acquired values. If the clipboard/history/file content changed, refuse before vault writes and refresh the preview with a clear “Clipboard changed” message. Do not silently submit the changed material. A plain CLI capture without a previous preview still reads current contents as today. This avoids introducing a persistent clipboard snapshot service merely to support previews.

Fingerprint checks must cover history order and file bytes, not just a live pasteboard counter. Keep existing attachment classification, limits, collision handling, and rollback. Preview must create no vault attachments or directories and no usage-history events. An unresolved preview may explain an unavailable clipboard without breaking parse or destination completion. The Linux test seams already exist through `BOB_CLIPBOARD_CMD` and `BOB_CLIPBOARD_HISTORY_CMD`; exercise them rather than depending on a developer's real clipboard. [Clipboard readers][s17], [clip planning][s18].

**One overlooked percent use needs an explicit choice.** Eligible URL-only captures currently interpret `URL %` as a companion-audio request, before clipboard parsing; `URL @` is another accepted spelling. This is separate from the clipboard feature, and leaving it untouched would mean `%` still sometimes performs an immediate operation instead of opening the three-directive menu. [Reference-intent marker][s19].

My recommendation is to remove the bare-percent audio spelling too, keep the existing `URL @` audio spelling as the sole shorthand for that operation, and document it as such rather than as a compatibility alias. Then `URL %c` unambiguously uses the clipboard/task path, while `URL @` requests reference audio. Do not make `%c` mean audio for URLs. Adding `%l` would be a reasonable future language extension, but it violates the requested three-letter set and should not be smuggled into this cleanup. This adjustment needs to be visible in the implementation scope and tests.

**Retirement should remove behavior, not erase evidence.** Remove old executable grammar, old completion and rewrite branches, active help examples, positive fixtures, generated documentation, and obsolete diagnostics that teach the removed forms. Specifically cover bare-percent clipboard capture, `%N`/`%header`, the bare-hash Pomodoro note, `@@template:`, the `@@@` expansion gesture, shared-parent `@@file+id`, and attached `@file+id#type` as a type operation. Remove parent-global inheritance from relationship ownership as well as ordinary routing; the old declaration participates in both.

Keep ordinary `@@file` global routing unless the user separately chooses to remove it. Only shared-parent declarations were requested for retirement. Consequently, do not delete the entire global-declaration or rewrite module: trim the affected branches. Keep independent explicit CLI flags such as `--task` and `--task-section`; they remain useful direct APIs. Changing displayed “task section” language to “drawer” does not require gratuitously renaming those flags.

A malformed global declaration should fail generically, never become captured content merely because its old handler was deleted. `%` and bare `#` have their new incomplete meanings. Unknown directives fail under the new directive grammar. Escaping allows deliberate literal text. The exact string `@foo+bar#fix` cannot be globally forbidden: under the new language FIX can legitimately be a drawer. Its old type meaning disappears; its new meaning is made visible by context and preview.

I would explicitly exempt immutable research/plans, accepted historical decisions, Git history, and narrowly scoped negative tests from “remove all reference.” Rewriting history is unrelated to the product cleanup, and regression tests need examples of syntax that must no longer execute. There should be no runtime compatibility alias or “try the old parser” fallback. A one-time data repair, if later needed for retained drafts, is a separate operation rather than permanent language support.

**The proposed glossary entry** is ready to use when the feature is implemented:

> **Task Drawer** — aka drawer. A named context container directly under a task, written as a plain ALL-CAPS child bullet, with its contents nested beneath it. It has no checkbox and is not a task type, a task dependency, or a managed log. Capture selects it with `@file+id#drawer` and creates it with the first captured content when absent. When a task becomes a Project Note, a populated drawer becomes a corresponding H2 section, preserving its contents. Project H2 sections provide drawer-name suggestions. An empty qualifying child bullet is selectable as a drawer, but current project conversion promotes it only after it contains a nested list item.

I used the SASE memory-writing guidance to prepare this definition, but have not edited canonical memory as part of a research-only deliverable. The future implementation should add the user-requested glossary strand and correct affected Capture wording, including any statement that live preview universally uses literal `--no-clip` behavior. A formal implementation plan should carry the applicable per-note memory decisions.

**Where implementation effort belongs.** The change touches a coherent set of existing seams; a new parser framework, resident daemon, or Swift grammar port would increase risk without solving the present problem.

| Work area | Existing seams and required behavior |
| --- | --- |
| Lexing and classification | `capture_language/{type_marker,markers,line,item,tokens,editor_classify,completion}.rs`: one drawer interpretation; immediate bare-type completion; shared directive scanner and conflict rules |
| Drawer planning | `capture_task_sections.rs`, `capture/sub_bullet.rs`: exact unique resolution, canonical creation, staged re-resolution, preserved indentation/log boundaries |
| Type effects | `capture/plan.rs`, `capture/task_theme.rs`, `capture_complete/task_types.rs`: body-bearing existing-parent subject, atomic retype/append/ledger effects |
| Suggestions | `capture_complete/{candidates,model,engine}.rs`: local drawers first, derived project/task catalog, usage provenance, explicit create candidates |
| Template behavior | `capture_language/{template,rewrite,draft}.rs`, `capture_templates/*`: in-place marker, source maps, retained expansion limits, saved-definition identity |
| Preview | `capture/plan.rs`, `capture_clip/*`, JSON output: parse/acquire split, pending effect, resolved fingerprint and submit validation |
| Mac presentation | `BobProcessClient.swift`, `CaptureModels.swift`, `CapturePanelModel.swift`, menu/preview views: decode new contract, stable menu rows, generation checks, capability gate |
| Plugin alignment | Existing project conversion helpers and fixtures: verify populated drawer promotion and title/empty-node parity; change source only if a demonstrated mismatch requires it |
| Cleanup | CLI help, generated docs, Mac docs, fixture generators, fake Bob, shell completion, saved-draft output, memory vocabulary |

**Shipping safely requires a language capability check.** Old Bob already recognizes `%n` and `%t` as clipboard headers. JSON schema 1 alone cannot distinguish old and new semantics. Add an explicit capture-language capability/revision advertised by Bob and cache it by executable identity. A new Mac build must require the new capability before permitting the new capture experience; an unsupported backend should show an actionable update message and retain the draft. Do not translate to old syntax or probe by executing a capture. Capability negotiation belongs in process orchestration, not in Swift grammar detection.

Keep JSON shapes additive where possible, with optional fields decoded normally, while acknowledging that the text-language change is breaking. If a payload truly changes shape incompatibly, version that payload rather than pretend it is additive. Exercise both install orders; an old app with new Bob must either have a demonstrated safe path for the new responses or be excluded by the coordinated upgrade contract. This cannot be solved solely by teaching the new app about old Bob. Use a breaking-change commit marker and the existing daily release train; do not hand-edit Cargo versions or the changelog to force a release.

**Acceptance evidence should cover interactions, not only happy-path token examples.**

| Area | Required cases |
| --- | --- |
| User example | Existing/missing REQUIREMENTS drawer; FIX inherited vs explicit; linked parent requiring relocation; one atomic result |
| Stable meaning | Add/remove body text around `@foo+bar#`; always drawer completion; no type/toggle fallback; content-required state |
| Matching | Exact slug, no prefix commit matching, near miss, duplicate title, colliding slugs, quoted punctuation, escaped directive |
| Structure | Tabs/spaces, CRLF, EOF, nested tasks, fenced text, empty existing drawer, managed logs, project conversion |
| Batch safety | Two rows create the same drawer once; later invalid item rolls everything back; parent or daily note changes before commit |
| Types | Correct existing-parent suggestions; configured-type refusal; no child metadata; no unsolicited Ensure Next for body-bearing captures |
| Directives | Bare `%` menu; incomplete/unknown directive; count/header parameters; `%n` fallback; no-session error; duplicate/conflicting directives |
| Template | Leading/trailing/child-line `%t`; standalone introductory line; rows unchanged; missing separator, repeated marker, row-value injection, limits, original-source error spans |
| Clipboard | Deferred semantic preview; real resolved preview; changed live text/history/file bytes; absent history; attachment collision; no files/events from preview; rollback |
| Retired forms | No successful old behavior, including URL bare-percent audio, global-parent dependencies, old template gesture, and obsolete generated examples |
| UI and protocol | Empty-query menus, Return accepts only once, Escape, stale responses, Unicode ranges, VoiceOver labels, unknown capability, both upgrade orders |
| Shelf | Existing headerless definitions still usable; same body retains identity; returned drafts contain `%t`; incompatible retained raw drafts do not silently execute |

Reuse Rust grammar/planner/CLI fixtures, the Mac real-Bob fixture generators and hosted editor tests, and plugin conversion tests where the shared Markdown convention matters. Verify dry-run and commit effects with deterministic clock/clipboard inputs, and fail after each staged-write boundary to test rollback. Measure cold and warm completion and resolved-preview latency with a representative vault; suggested targets such as a sub-100 ms warm response are product goals to validate, not measurements established by this research. Mac changes require the repository's portable checks plus actual macOS compilation/typechecking and hosted CI; source inspection on this Linux host does not verify native UI behavior.

**The requirement adjustments are deliberate and limited.**

| Adjustment | Why I recommend it |
| --- | --- |
| Exact drawer resolution at commit; prefix/fuzzy only in completion | Automatic creation makes silent prefix resolution unpredictable |
| Quoted drawer titles alongside slugs | Existing title grammar permits punctuation and slug collisions |
| Preserve clip history and headers as `%cN` and `%c:header` | “Works like current `%`” otherwise loses existing functionality |
| Preserve current-or-last-completed behavior for `%n` | That is the existing action; changing it would be a separate behavior change |
| Remove URL bare-percent audio; retain `URL @` | Bare `%` must become a reliable discovery point; `%c` must always mean clip |
| Restrict `%t` to one first definition block and explicit following rows | Leaving text in place still needs an unambiguous boundary |
| Preserve existing specialized hash menus and ordinary `@@file` | The request names narrower retirements, and these features remain useful |
| Add backend capability gating and a clipboard fingerprint check | Existing parsers can silently misinterpret new text; live data can change after preview |
| Preserve historical records and negative retirement tests | Remove supported legacy behavior without damaging provenance or regression coverage |

The main uncertainties left for implementation are latency on the real Mac/vault, the exact capability transport, and how many retained raw drafts contain removed syntax. Those should be measured or inventoried through the authorized app/CLI interfaces. They do not require broadening the grammar or keeping legacy aliases. I did not inspect the personal vault, run a native UI build, or benchmark the proposed implementation; it does not exist yet.

Sources below are pinned to the checkouts read during this investigation. The SASE epic and plan were consumed through their audited artifact interfaces. External documentation supports the narrow platform claims where it is linked; the language and interface proposals are this researcher's conclusions.

[s1]: https://github.com/bobs-org/bob-cli/blob/5e2d0856f3539fb632d418c6c1da3761cc3655dd/src/native/capture_language/type_marker.rs
[s2]: https://github.com/bobs-org/bob-cli/blob/5e2d0856f3539fb632d418c6c1da3761cc3655dd/src/native/capture/task_theme.rs
[s3]: https://github.com/bobs-org/bob-cli/blob/5e2d0856f3539fb632d418c6c1da3761cc3655dd/src/native/capture_task_sections.rs
[s4]: https://github.com/bobs-org/bob-cli/blob/5e2d0856f3539fb632d418c6c1da3761cc3655dd/src/native/capture/sub_bullet.rs
[s5]: https://github.com/bobs-org/bob-cli/blob/5e2d0856f3539fb632d418c6c1da3761cc3655dd/src/native/capture_complete/candidates.rs
[s6]: https://github.com/bobs-org/bob-plugins/blob/3942eb8190e4607ae99e977eea59dff44794a19c/plugins/bob-navigation-hotkeys/src/100-yank-and-paths.js
[s7]: https://github.com/bobs-org/bob-plugins/blob/3942eb8190e4607ae99e977eea59dff44794a19c/plugins/bob-navigation-hotkeys/src/110-project-seed.js
[s8]: https://github.com/bobs-org/bob-cli/blob/5e2d0856f3539fb632d418c6c1da3761cc3655dd/src/native/capture/commit.rs
[s9]: https://github.com/bobs-org/bob-cli/blob/5e2d0856f3539fb632d418c6c1da3761cc3655dd/src/native/capture_language/line.rs
[s10]: https://github.com/bobs-org/bob-mac-capture/blob/ec3fff5fe056a2db78baa4fff3161eaf51018a15/Sources/CaptureCore/BobProcessClient.swift
[s11]: https://github.com/bobs-org/bob-cli/blob/5e2d0856f3539fb632d418c6c1da3761cc3655dd/src/native/capture_complete/task_types.rs
[s12]: https://github.com/bobs-org/bob-cli/blob/5e2d0856f3539fb632d418c6c1da3761cc3655dd/src/native/capture_language/template.rs
[s13]: https://github.com/bobs-org/bob-cli/blob/5e2d0856f3539fb632d418c6c1da3761cc3655dd/src/native/capture_language/rewrite.rs
[s14]: https://github.com/bobs-org/bob-cli/blob/5e2d0856f3539fb632d418c6c1da3761cc3655dd/src/native/capture_templates/store.rs
[s15]: https://github.com/bobs-org/bob-cli/blob/5e2d0856f3539fb632d418c6c1da3761cc3655dd/src/native/capture_templates/command.rs
[s16]: https://github.com/bobs-org/bob-cli/blob/5e2d0856f3539fb632d418c6c1da3761cc3655dd/src/native/capture/plan.rs
[s17]: https://github.com/bobs-org/bob-cli/blob/5e2d0856f3539fb632d418c6c1da3761cc3655dd/src/native/capture_clip/clipboard.rs
[s18]: https://github.com/bobs-org/bob-cli/blob/5e2d0856f3539fb632d418c6c1da3761cc3655dd/src/native/capture_clip/plan.rs
[s19]: https://github.com/bobs-org/bob-cli/blob/5e2d0856f3539fb632d418c6c1da3761cc3655dd/src/native/url_routing/intent.rs

**Recommended solution:** adopt `@file+id#drawer` with a separate `#type`, auto-create only validated, explicitly previewed drawers, and resolve writes by exact identity. Introduce `%c`, `%n`, and in-place `%t` through one authoritative Bob grammar, preserving clipboard parameters and template safeguards. Give the Mac app immediate explanatory menus and truthful clipboard previews, protected by language capability checks and submit-time input validation. Ship the CLI and app as one coordinated breaking change, remove the obsolete behavior completely, and use the existing Markdown scanner, transactional planner, and preview system as the foundation.
