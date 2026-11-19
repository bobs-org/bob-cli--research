# Period intentions and property cards: independent design research

Researcher: **cdx** · 19 November 2026  
Status: design recommendation, not an implementation or approved migration.

## Assessment

**Yes: unify the vocabulary and interaction.** “Daily intentions,” “weekly intentions,” “quarterly intentions,” and “yearly intentions” form a useful family. Keep three distinct questions within that family:

- **Intentions — Bryan:** What do I want this period to be about?
- **Summary — agent:** What do the records show happened?
- **Reflection — Bryan:** What do I make of it?

The value is a consistent place to express those answers, not moving prose into YAML by itself. A card can make that place easier to use and calmer to read. The costs are real: multiline prose needs a proper editor, property hiding needs a safe fallback, and the existing period review pipeline has protections a new implementation must preserve.

I recommend the three requested frontmatter fields, a shared property-card presentation and editor shell, and Bob-owned writers. I would **not** store an instruction sentinel in `summary`, make intentions into tasks, require a daily summary before reflection, or begin with a wholesale rewrite of the existing cards.

A yearly intention can be a guiding theme or a concrete intended outcome. Unifying their name must not force an agent to turn a theme into a measurable deliverable or flatten nuanced planning text.

## Scope and confidence

I independently inspected bob-cli, bob-plugins, and bob-mac-capture. No peer swarm report, transcript, or finding was consulted.

| Repository | Revision inspected |
| --- | --- |
| bob-cli | `e07a26bf86b93fe12df571ac6cb00f8b71d28cca` |
| bob-plugins | `36d48017f9a16edaf21346fb0276c530836e08f4` |
| bob-mac-capture | `868672fc516996dc3a36c53ec0114f4139213720` |

I read relevant glossary, Obsidian, CLI, documentation, release, and client-ownership memories through audited SASE reads, and checked official Obsidian documentation. This is source research, not an Obsidian runtime experiment. I have not measured rendering performance or verified the proposed gestures in a running app.

The vault was not available as a registered `sase repo open bob` target; the registered-project inventory did not identify it either. I therefore did **not** inspect or change live `gtd_daily.md`, daily templates, YAML property-type configuration, or historic planning text. Exact GTD placement, recurrence syntax, and migration counts require an implementation-time inventory. No production code or memory definitions were changed.

## Existing behavior and implementation implications

| Finding | Evidence and implication |
| --- | --- |
| Daily Headline is Bryan's forward-looking text. | The parser recognizes both bold-label forms in the preamble, ignoring YAML, fences, and later sections. Its meaning moves into `intentions`. [S1] |
| Period Review also has a “Headline,” but it is retrospective. | The agent's Review lead appears in parent tables. That meaning belongs to `summary`; a global rename would conflate two owners. [S2][S3] |
| Year notes contain both Theme **and** Outcomes. | Migration must preserve both, not merely the theme named in the request. [S4] |
| Current period identity excludes days. | `PeriodId` is Week/Quarter/Year/AllTime. Current `brief` and `draft` do not accept daily subjects. A card alone cannot deliver daily summarization. [S5] |
| Reviews already have substantial protection. | Digests identify user edits; reflected/open-period checks, word caps, locking, re-read checks, and atomic writes guard drafts. [S3] |
| Current period YAML parsing is inadequate. | `parse_frontmatter` is a line-oriented scalar map that skips indented content. Lists and literal multiline scalars require typed YAML parsing. [S2] |
| Some card infrastructure is already shared. | `createRecordUpdateSession` wraps `createGuardedUpdateSession`; source excursions and close keys have reusable conventions. [S6][S7] |
| Current property hiding is selective. | Record source marks owned native property rows and restores them on teardown. Some documentation describes broader hiding; prefer the current scoped implementation. [S8] |
| `==` is not an ordinary Vim mapping. | A capture-phase handler intercepts the second `=` while `indentAuto` is pending. It excludes counted commands, Source mode, other Vim modes, IME, and unrelated notes. Extend it. [S9] |
| Bank and album behavior is domain-specific. | Bank setup is report-driven; album schemas have consequences and repairs. Share shell/lifecycle, not one undifferentiated operation model. [S10][S11] |
| The Mac consumes a scalar Daily Headline. | The CLI emits `headline: String?`; Swift decodes that type, labels it HEADLINE, and budgets a compact row. An array cannot replace it in place. [S12][S13] |
| Summary evidence extends beyond the daily file. | Existing briefs include dated completions, linked work, Work Logs, prior reflection, parent plans, and caveats. Current task state is not necessarily historical state. [S14] |

Obsidian's native property UI does not render Markdown in properties; a property's type applies to that key throughout the vault. The global Hidden setting hides the whole properties surface. Use a custom prose editor and note-scoped hiding, and do not redefine existing album/notebook `summary` ownership globally. [E1]

## Recommended data contract

### Three fields with distinct owners

Illustrative content, not a claim about a real day:

```yaml
intentions:
  - "Finish the [[capture|capture]] design decision."
  - "Leave room for a quiet evening."
summary: |-
  The capture design reached a concrete implementation recommendation.

  The notes record a comparison of the existing editors and a migration
  proposal. Implementation remained open at the day's end.
reflection: |-
  Comparing the existing interactions helped more than sketching a new one.
  Tomorrow I want to test the smallest useful change first.
```

Keep the requested top-level fields. Nested `period: { ... }` would add native-tool friction without a demonstrated benefit. Derive the period from Bob's canonical note identity, validating date/id metadata against it; do not add a separately editable `period:` field that can disagree. Expose kind, canonical id, bounds, note path, and parent through one resolver. A record with a field named `intentions` remains a record.

| Field | Contract | Normal writer |
| --- | --- | --- |
| `intentions` | Ordered list of strings; order is authored, not task priority. No automatic completion, deduplication, inheritance, or carry-forward. | Bryan, through editor or Source. |
| `summary` | Optional string; literal block scalar when multiline. A standalone opening paragraph plus useful paragraphs/bullets. | Agent, through guarded Bob writer. |
| `reflection` | Optional string preserving paragraph breaks; no automatic interpretation or scoring. | Bryan, through multiline editor or Source. |

New intention items can use single-line text with soft visual wrapping and ordinary internal links. Never split pasted prose on commas. A migration reader must preserve richer historic strings or flag them for review rather than force them through a simple row editor.

Specify a small prose-rendering subset: paragraphs, emphasis, lists, and safe internal/external links. Do not execute query blocks, embedded commands, arbitrary plugin processors, or raw HTML inside generated summaries. The YAML string remains the portable source; the card renders it.

### What “intentions is set” means

| Note state | Behavior |
| --- | --- |
| Canonical daily/period note, key absent | No inline card. `==` and a palette command can open its editor. Opening alone writes nothing. |
| `intentions: []` | Valid enabled empty card, with a quiet Add an intention action. |
| Nonempty string list | Show intentions in authored order. |
| Null, scalar, mixed list, duplicate keys, malformed YAML | No silent coercion or hiding; show repair guidance and retain native/Source access. |
| Unrelated note with `intentions` | Do not claim it with this card or change its existing editor. |

New daily and finite-period scaffolds should include `intentions: []`; summary and reflection can be absent until written. Clearing the last intention leaves `[]`, so the card does not disappear while someone edits it.

**Requirement clarification:** an empty list counts as “set.” An explicitly requested summary of a legacy note with no planning content may initialize `intentions: []` in the same transaction. That creates a display container, not a user intention, and the operation should disclose it. It must not silently convert nonempty legacy planning text or invalid YAML. Refusing all such writes until separate activation is safer but needlessly cumbersome; I prefer empty-container initialization.

A manually authored summary/reflection with no intentions key is an incomplete adoption state: keep those properties accessible, offer activation, and never hide them behind a missing card.

Keep all-time as a rollup, with optional intentions/reflection if explicitly enabled. It has no closed boundary and should not acquire a default summary job. Do not add monthly period notes; the existing ISO hierarchy remains intact.

### Ownership and provenance

Put provenance in separate machine fields, for example `summary_digest`, `summary_generated`, and `summary_instructions_version`. An evidence digest can travel through the brief/writer protocol for stale-input checks; persist it only if there is a defined audit or refresh use. Never put an instruction path, TODO marker, or sentinel in the summary itself.

Derive independent states:

- Summary: empty, generated (digest matches), or edited (nonempty without a matching digest).
- Reflection: empty or written.

Reflection must not falsely imply that a summary exists. Add these explicit states to parent models while preserving old combined-state consumers during rollout.

Allow an agent to fill an **empty** summary after reflection. Replacing a nonempty summary after reflection or a user correction requires an explicit redo request. This deliberately refines the current reflected-blocks-draft rule: the PRE agent may still be running when Bryan reaches POST.

When automatic archive/rename operations rewrite links inside an otherwise generated summary, carry its digest appropriately. Existing review-digest preservation addresses this class of change. Never restamp genuinely user-edited prose as agent-owned. [S2]

## A quiet inline card and a capable editor

### Appearance and placement

Use existing host conventions: after the first H1, or at the first body position when there is no H1, before ledger/parts content. Keep the note's title/navigation recognizable; avoid another oversized copy of the date.

Interaction wireframe, not a screenshot:

```text
Daily intentions                              Wed 18 Nov    Edit ==

• Finish the capture design decision.
• Leave room for a quiet evening.

SUMMARY · Agent
The capture design reached a concrete implementation recommendation.
Show more

REFLECTION · You
Comparing the existing interactions helped more than sketching a new one.
```

Use Obsidian theme tokens, a small muted period label, readable normal-weight prose, one thin separator between roles, and a restrained border or tinted edge. Intentions should not look like checkboxes or status chips. Avoid success percentages, day scores, confetti, and colors assigned to every paragraph. Ownership needs words, not color alone.

Show short intentions in full, followed by summary/reflection leads. Expand longer text explicitly in place; never make hover the only route to content. An absent Summary does not need a conspicuous failure panel. An empty Reflection can offer Add reflection. An all-empty enabled card should remain compact.

At narrow widths, stack labels above prose; let dates and actions wrap. Preserve text selection, normal link behavior/previews, visible focus, accessible names, and usable button targets. Use a labelled region, disclosure `aria-expanded`, and polite save/error announcements. Test light/dark, enlarged text, long unbroken strings, and 320–375px panes. Do not hard-code a card height.

Reading view and Live Preview should share their content model. Collapse state belongs to the session, keyed by note/pane as appropriate, never YAML. Rendering, hover, folding, and tab changes must not write or launch an agent.

### Hiding with a reliable fallback

Hide only `intentions`, `summary`, `reflection`, and recognized machine metadata in the eligible note surface **after its card mounts successfully**. Do not globally hide every summary property or the entire native Properties block. Preserve unrelated parent/type/user properties unless another existing surface owns them.

Follow record-card ownership/cleanup. On invalid data, unsupported capability, mount failure, or unload, restore native access. Source remains available. Do not affect the global Properties sidebar or an unrelated embed. On mobile or unsupported clients, retain native data access if a reliable card/editor is unavailable. [S8]

Official Obsidian guidance describes decorations for editor widgets and direct/state-field provision when decorations affect layout. Keep the proven host mechanism where possible instead of inserting unmanaged DOM into CodeMirror's document. [E2]

### Shared `==`, specialized editing

Make `==` mean edit this note's supported property card, while retaining existing command IDs and familiar album/record/bank labels. The inline display and the editor are separate surfaces in one family.

On a daily/period note, open a small browse-mode editor:

| Gesture | Action |
| --- | --- |
| `i` | Edit intentions. |
| `r` | Open Reflection directly. |
| `s` | Read/expand Summary; normal editor does not invite rewriting agent prose. |
| Arrows/Tab and buttons | Navigate the same fields/actions. |
| `y` or Source action | Open the corresponding YAML location. |
| Esc / `q` / Ctrl+[ | Same layered back/close behavior; `q` types in text controls. |

Intentions use ordered rows with add/edit/remove and explicit move controls. Preserve draft text through preview and error refreshes. Give each stage clear Save/Cancel actions; Enter should not unexpectedly both append an item and close the editor.

Reflection needs a true multiline textarea: **Enter inserts a newline; Ctrl/Cmd+Enter saves**. This intentionally differs from the record editor's text stage, which saves on Enter and refuses newlines. Reusing that stage unchanged would make reflection uncomfortable. Tab moves focus rather than silently committing a paragraph. A visible Save button keeps keyboard shortcuts optional.

Retain dirty drafts or provide a clear discard choice; do not lose them on a refresh or accidental close. A save applies exactly once after a current successful preview. Preserve field, caret, and selection on stale responses. Reuse the guarded session's editor-save, cancellation, status, and inverse-operation Undo behavior. [S6][S7]

Extend the existing second-equals dispatcher. Preserve counted `N==`, Source, other modes, IME, and unrelated notes. A `.vimrc` mapping alone will not work with this Vim operator. [S9]

### `[n==r` and previous-day reflection

The mnemonic is good: previous note → property editor → reflection. But `[n` follows a labelled previous link; it does not intrinsically calculate yesterday. [S15]

Show the absolute date in the editor and bind the path when navigation resolves. A slow open must never edit the old pane. Once the correct path is known, mount the modal shell promptly so `r` can select Reflection while data loads. Avoid a global speculative keystroke queue across arbitrary navigation.

Also expose **Reflect on yesterday** in the palette/command sheet. Resolve the previous calendar day using Bob's configured day timezone, then open that exact Reflection stage. A missing note or failed navigation must not fall back to today's note. This direct action is the dependable route for fast keyboard execution and nonstandard navigation links; ordinary `[n` semantics should stay unchanged.

Bob already uses configured `timezone`, host-local fallback, and `BOB_NOW`. Use that resolver, not server UTC or “24 hours ago.” Pin the target once per editor/agent session so crossing midnight cannot redirect the write. [S16]

## Architecture and proposed interfaces

Keep the feature in `bob-ledger-tools`, which already owns the card family and `==`; another plugin would introduce lifecycle/keybinding competition.

| Layer | Responsibility |
| --- | --- |
| Bob period-property model | Canonical identity, typed parsing, validation, ownership, and day/ISO-period resolution. |
| Bob writers | Preview/apply with expected state; separate user-property editing from agent summary writes. |
| Shared property-card host | Reading/Live Preview mounting, cleanup, safe property hiding, refresh/focus rules. |
| Shared editor shell | Title, fields, status/hints, close keys, stage lifecycle, guarded save/Undo, Source excursion. |
| Intention adapter | Ordered intention list, multiline reflection, summary read view, period labels. |
| Existing adapters | Album schema/details, record values, bank setup; retain their own validation and operations. |

Concrete seams include `242aa-plugin-guarded-update-session.js`, `242m-plugin-record-update-session.js`, `242ka-plugin-record-sheet-properties.js`, `241xc-plugin-card-close-keys.js`, and `248m-plugin-schema-double-equals.js`. Bank/album hosts demonstrate mounting/refresh conventions. [S6–S11]

First share styles, dispatcher, guarded session, and a small host helper. Extract further common behavior only where the intention card proves it useful. Do not make a universal declarative form language, arbitrary custom cards, or an album-schema conversion prerequisites.

Avoid a subprocess per rendered card. Refresh local presentation from relevant note metadata/buffer events; use a validated Bob read/preview when opening and applying. Subscribe narrowly. Metadata changes must not erase unsubmitted text.

The following interfaces are **proposals, not available commands**:

- Extend `bob periods brief` to daily subjects and return the policy plus evidence contract.
- Extend `bob periods draft` so its canonical destination is `summary`, with temporary compatibility for body-based notes.
- Add focused `bob periods update` operations for intentions/reflection, following the existing versioned JSON-envelope style with expected fingerprint. The human editor cannot obtain agent-write authority merely by naming `summary` in an operation.
- Expose the shipped policy through a read-only `bob periods instructions <subject>` member, or an equivalent documented read-only route if CLI design favors fewer members.

A common `PeriodRef = Day | ExistingPeriod` resolver is a lower-risk starting point than forcing Day through every exhaustive `PeriodId` match. Audit before deciding whether to extend the existing enum instead. Keep calendar-year daily folders distinct from ISO-week-year parents.

Follow CLI alias/help conventions; do not hard-remove `draft` in favor of a new spelling. Exact options need the normal CLI review and short aliases.

The writer contract should require typed YAML parsing, duplicate-key refusal, pane-save reconciliation, exact preview, expected destination state, a short apply-time maintenance lock, re-read comparison, minimal span edits, atomic replacement, and guarded Undo. Preserve body bytes, unrelated keys, supported comments, and line endings. No-op updates write nothing. Stale state retains the draft and requires a fresh preview. Retry sync separately; never replay a successful edit after sync failure.

Record code already validates YAML and preserves unrelated spans, but its field-value rules do not automatically support prose scalars. Extract primitives and explicitly test multiline handling. Avoid round-tripping all YAML through a serializer that silently reformats unrelated content. [S17]

A whole-note fingerprint is a safe initial guard. If ongoing ledger writes make it too restrictive, introduce field-level comparison with explicit tested rebase semantics; do not silently weaken protection.

## Hidden instructions that agents can actually discover

### Do not overload `summary`

A value like `summary: "@instructions/..."` is nonempty to state checks, can leak into tables/search, and vanishes as an instruction pointer after the first summary. It still requires a separate rule explaining what it means.

Repeated folded/hidden callouts are also a poor permanent source of truth. Bob currently versions and refreshes full callouts in each period note. That can drift and leaves visible chrome even when folded. [S4]

### One source, explicit discovery routes

Keep a canonical Markdown policy in bob-cli, for example `docs/reference/agents/period-summary.md`, and package it with the binary. Provision a generated copy into a hidden vault path such as `.bob/instructions/period-summary.md`. Both come from the same source with version/hash; they are not independently edited policies.

Use three complementary discovery routes:

1. A short always-loaded Bob task-routing instruction: when asked to summarize a canonical daily/period note, read the policy and obtain a period brief before writing. Keep the policy body in reference context, not core memory. Publish the routing change through SASE memory generation.
2. `bob periods brief` includes a separated policy section for agents, with version/hash and policy text in JSON. Evidence remains labelled as data, not instructions.
3. The PRE task's launch prompt names the route and target explicitly, so an agent launched outside the vault still has an entry point.

The writer can validate supported policy version, expected destination state, and an evidence fingerprint. None proves that the model obeyed the prose. Nor can a separate file's existence guarantee discovery by an arbitrary external agent given only a note snippet. Reliability comes from supported launch/brief/write paths and tests of those paths.

No instruction text, sentinel, or folded callout needs to appear in ordinary daily-note Reading view or Live Preview. Source and the explicit instructions route remain inspectable.

### Draft daily-summary policy

This is proposed policy substance, not installed instructions:

> **Purpose.** Give Bryan and a later reader a compact, factual account of the named day's recorded work. The summary is evidence for reflection, not a replacement for Bryan's intentions or reflection.
>
> **Resolve once.** Obtain Bob's canonical date, timezone, path, closed/current status, instruction version, existing summary ownership, and evidence fingerprint. Yesterday means the previous local calendar date. Stop on a missing/malformed note or unexpanded template tokens; do not invent a past daily note.
>
> **Scope.** Prefer closed days. A current-day summary needs an explicit “so far” request and must say so. Never replace a user-edited summary or a nonempty reflected summary without redo authorization. An empty summary may be filled after reflection, leaving it unchanged.
>
> **Evidence.** Begin with the deterministic daily brief: recorded sessions/notes, task links, completions dated to the day, relevant Work Logs, project completions, intentions, and coverage caveats. Read linked source notes only to verify a consequential claim. Consult referenced agent/repository artifacts only when tied to that day and needed to substantiate an outcome. A launch marker proves a launch, not completed work.
>
> **Historical accuracy.** Use the day's end as cutoff. A later completion is not a completion yesterday. Calendar plans and unstarted placeholders do not prove activity. Quote Bob's aggregates rather than summing overlapping or repeated task links. Keep off-clock totals separate where reported. Current lane, task title, or today's mtime is not historical evidence.
>
> **Selection.** Lead with what changed or was produced, then a few consequential outcomes or open threads. Connect intentions to evidence where available, distinguishing completed, partial, and insufficient evidence in plain language. An intention need not be measurable. Do not invent completion percentages or a day score.
>
> **Voice.** Plain, factual, restrained. No praise, blame, productivity grading, inferred motives, guessed feelings, or unsolicited advice. Attribute a recorded explanation to Bryan. Never write first-person reflection on his behalf.
>
> **Length and evidence links.** Aim for 80–160 words on an ordinary day; a proposed 200-word ceiling is not a target. Open with a standalone sentence of at most 25 words for parent views. Add only useful paragraphs/bullets. Link consequential claims to specific stable evidence. Do not invent anchors or treat present task state as proof of past state. Keep links in stored prose even when compact display strips formatting.
>
> **Uncertainty.** Say that available records do not establish a claim when it matters. Missing evidence is not zero work. An empty ledger does not prove rest, failure, or inactivity. Name material coverage gaps and do not pad thin evidence with speculation.
>
> **Write.** Submit only the summary through Bob's guarded writer. Never change intentions, reflection, task states, ledger, or another day. Re-brief after a stale-evidence refusal. Do not hold a maintenance lock during research/model generation.
>
> **Respond.** State the resolved date, concise lead, write outcome, and material omissions. Do not mark the GTD task complete unless separately instructed.

Retain scale-specific practices from current instructions: weekly selection, quarterly synthesis, yearly arcs/context, and established 250/400/600-word caps. Rename forward-looking headings to Intentions. Do not require every daily summary before a weekly review; weekly briefs must still read primary evidence and expose missing summaries as coverage, not a blocked workflow.

Child summaries help navigation and synthesis, but should not be a parent's sole evidence. Repeated model compression can lose qualifications. Preserve routes to original records; a summary is replaceable generated prose, not the authoritative work ledger.

## Two daily GTD chores

Proposed wording, to be fitted to the live file's recurrence/ID conventions:

```markdown
- [ ] #gtd #pre #periods Launch an agent to summarize yesterday's recorded work using Bob's period-summary instructions.
- [ ] #gtd #post #periods Write yesterday's reflection — from today's daily note: [n, then ==, then r.
```

Use the requested `#periods` and PRE/POST tags. Preserve existing repeat fields, stable IDs, and group syntax after inspection. Check for semantic duplicates. Document the navigation caveat and direct Reflect on yesterday command rather than promising raw `[n==r` works with every previous link.

The PRE chore is complete when Bryan launches the agent, not when it finishes. POST is his reflection gesture and remains available if the agent is slow or fails. Keep current walk semantics. Do not create dependencies between the chores, launch a model on note opening, or auto-complete a task merely because a field is nonempty.

Suggested launch text:

```text
Use Bob's period-summary instructions and daily brief to summarize yesterday's
recorded work. Resolve the date with Bob, state the absolute target, and write
only that day's summary through the guarded writer. Leave my intentions and
reflection unchanged.
```

The implementation should pin/substitute the absolute date once, rather than having multiple processes re-resolve yesterday around midnight.

## Migration and compatibility

### Preserve the actual content

| Existing content | Destination and guard |
| --- | --- |
| Daily preamble Headline | One intention item, using the established parser. Preserve links/wrapped text; ignore fenced and later-section examples. |
| Weekly Intentions | Intentions list. Straightforward bullets map one-to-one; preserve or flag nested/prose structures. |
| Quarterly Outcomes | Intentions list. Intended outcomes must not become retrospective claims. |
| Yearly Theme and Outcomes | Preserve both, Theme before Outcomes. Where needed, preview explicit “Theme:”/“Outcome:” prefixes to retain meaning; do not silently flatten ambiguity. |
| Review | Entire `summary` string, not merely its Headline. Do not truncate rich history to fit a new default. |
| Reflection | Full `reflection` string with paragraphs intact. |
| Generated agent callout | Central policy, only after discovery works. Customized callouts require review, not blind deletion. |
| Review digest/draft date | Summary provenance, preserving generated-versus-edited ownership. Never bless an edited review as generated. |

Use temporary dual reading, not dual writing. A present new field wins even when deliberately empty. Legacy fallback applies only when absent. If old and new nonempty values disagree, report a conflict and leave both intact; do not concatenate or select by guesswork.

Migration should be dry-run-first with per-note diffs, conflict diagnostics, bounded checked application, and rollback. It must be idempotent. Exclude archives, template examples, fenced text, duplicate/ambiguous headings, and unrecognized shapes unless explicitly selected. Inventory inbound links to retired section headings/anchors and preserve or rewrite their meaning before removing them.

Update templates/scaffolds so they stop reintroducing old sections. `structure_ok`, problems/list/show, brief neighbors, instruction refresh, and draft validation currently assume those sections. Update them as a unit while retaining temporary legacy readers. Do not deploy hiding before the renderer/migration can expose the content. [S2–S5][S14]

### Parent views and Mac agenda

Expose intentions, compact intention display, summary lead, reflection lead, and independent states. For current/future children show intentions prominently; for closed children with summaries show a clearly labelled Summary lead, keeping intentions accessible. Do not let one unlabeled column silently alternate between “planned” and “happened.” Compact leads are derived, not another authored headline property.

Add an optional intentions representation to `capture-pomodoros --tasks` while retaining nullable scalar `headline` during compatibility. Its documented fallback can be the first intention's display text. Never change its JSON type to array or populate it from retrospective summary.

The updated Mac can show the first intention plus a small +N affordance, with an accessible way to reveal the whole list, while preserving agenda fit/eye-line behavior. Bob provides facts; Swift must not read YAML. Cover old/new CLI and app combinations. A later contract removal follows the project's breaking-change release convention; agents do not hand-bump Cargo.toml or CHANGELOG.md. [S12][S13]

## Proposed glossary wording

These six definitions are reviewable proposals, not installed memory. Canonical **Intention Card**, alias **intentions card**; visible headings use “Daily intentions,” etc.

**Intention.** A Bryan-authored statement of what he wants a named day, ISO week, quarter, or year to be about. Its note stores an ordered `intentions` list; the period follows the note's identity. An intention can name an outcome, focus, or guiding theme. It is not a task, status, agent assessment, promise of completion, or inherited plan. Bryan controls its wording/order. Summary records what evidence says happened; Reflection records what Bryan makes of it.

**Property Card.** A Bob-rendered view of a supported note's structured properties, paired with a keyboard-first editor for the properties that surface may change. It replaces only native property rows it safely represents; Source stays available. Opening/rendering does not write. `==` opens the relevant editor in supported Vim normal-mode contexts, with buttons/commands providing equivalent access. Album, Record, Bank, and Intention Cards share this family while retaining different domain fields and write rules.

**Intention Card.** The Property Card on a canonical daily/period note with a valid `intentions` list, including an empty list. It presents the period, Bryan's intentions, the agent's Summary, and Bryan's Reflection with distinct ownership. Its editor changes intentions/reflection; Summary is normally read-only there and comes through Bob's guarded period writer. It creates no tasks, grades no period, and generates nothing on open.

**Album Card.** The Property Card at the top of an Album Note, presenting collection identity and its record schema. Its editor changes album details, field definitions, choices, grouping, and supported schema settings through validated album operations. It describes the collection and shape of its records, not an individual record's values or the generated index. Existing “album header” and “Schema Card” denote its display and editor surfaces.

**Record Card.** The Property Card for one canonical Record Note, presenting title, album context, and schema-defined values. The existing record sheet is its display; the Record Card editor changes values through guarded `bob records update` operations with preview and Undo. Editing the album schema is a separate Album Card action. Record fields are facts about an item, not task properties.

**Bank Card.** The Property Card on `bank.md`, presenting bank setup and supported account/category configuration, with an editor backed by validated bank configuration operations. It is distinct from the period Bank Badge, bank-month statement/totals surface, and transaction acknowledgment/category editor. Those may share primitives without becoming aliases for the hub card.

Current terminology sometimes uses “card” only for a modal and “sheet/header” for display. Explain the umbrella transition without breaking familiar commands. Reconcile stale Daily Headline and Period Note glossary definitions too. A formal implementation plan needs the corresponding per-note SASE memory decisions, quoting the user's requested additions and exact claims made stale. Do not hand-edit generated AGENTS.md.

## Delivery sequence and validation

This is a recommendation for a later implementation plan, not a submitted SASE plan or a vault mutation.

1. Inventory real legacy content, GTD recurrence, property types, and inbound heading links. Agree on activation, multiline format, ownership, and all-time behavior.
2. Implement typed Bob model/writers, day resolution, legacy readers, summary provenance, evidence brief, and policy delivery.
3. Build the intention card/editor with shared session/close/dispatch primitives. Validate actual Reading/Live Preview and keyboard behavior before hiding/migrating content.
4. Update tables, briefs, and Mac additively. Change scaffolds/templates, instruction routing, and requested glossary definitions through the proper memory workflow.
5. Preview migration, resolve ambiguous content, apply bounded batches, then add GTD chores in the established live format. Remove generated callouts only after discovery is verified.
6. Verify summarize → reflect → weekly review across compatible clients and preserve a recovery path. Avoid permanent dual writing.

| Area | Meaningful acceptance evidence |
| --- | --- |
| YAML | Lists/empty/null/missing, block/folded strings, quotes/colons/Unicode, multiline text, duplicate keys, malformed YAML, CRLF, comments, and preservation of untouched bytes. |
| Scope/dates | Canonical daily/week/quarter/year, unrelated summary fields unaffected, all-time behavior, configured timezone versus UTC, DST, midnight, ISO week 53, calendar-year folder mismatch. |
| Ownership | Agents cannot alter authored intentions/reflection; corrected summaries are protected; empty summary allowed after reflection; nonempty reflected summary requires redo. |
| Concurrency | Two panes, unsaved Source edits, ledger refresh, another agent, stale preview, double-save, delayed responses, lock timeout, sync failure after apply. No duplicate mutation or lost draft. |
| Migration | Idempotence, entire Review retained, both annual sections retained, rich text flagged, conflicting fields refused, anchors handled, fixture-vault rollback. |
| UI | Light/dark, narrow panes, large text, long prose, frontmatter-only note, card removal/unload, invalid metadata, embeds, Source/native fallback, no write on render/fold. |
| Keys | `==`, `N==`, Source/insert/visual/IME preservation, direct `r`, multiline Enter/save, close-key parity, dirty-draft recovery, correct-date navigation. |
| Agent quality | Policy delivered with brief, thin evidence marked uncertain, calendar plans not counted as work, later completion not backdated, launch marker not output, no fabricated reflection. |
| Clients | Old/new Bob and Mac combinations, absent/null/empty/list cases, whole-list accessibility, stable fit, no Swift YAML parsing. |

Use relevant CLI/unit/integration and docs checks. Plugin implementation requires fragment builds/build checks and deployment through `bob plugins sync`. Swift changes require the prescribed portable and macOS compilation/CI gates on the exact pushed SHA; portable checks alone do not verify macOS targets. This research ran no feature tests because it changed no feature code.

## Alternatives and explicit requirement adjustments

| Alternative | Assessment |
| --- | --- |
| Rename headings and keep prose in Markdown | Lowest migration risk, best native editing. Sensible fallback if maintaining a multiline property editor is not worthwhile, but only partly delivers the requested card experience. |
| Store everything in YAML with native Properties only | Poor reflection editing and presentation; misses the purpose of the change. |
| Keep a short Summary property plus a separate permanent full Review | Creates overlapping agent narratives. Prefer one full summary string, visually folded. |
| Model intentions as an album schema | Reuses machinery at the cost of wrong identity/evidence/ownership semantics. |
| Build a universal card engine first | Excess scope. Share proven primitives and interaction rules now. |
| Put an instruction sentinel in Summary | Contaminates data/state and loses discovery after the first write. Reject. |
| Central versioned policy with explicit brief/writer routes | Recommended: maintainable instructions, reliable supported workflow, no daily-note boilerplate. |

Recommended adjustments, called out explicitly:

1. Empty `intentions: []` counts as enabled; explicit summary requests may initialize that empty container on suitable legacy notes, never authored intention content.
2. Hide only safely represented fields on mounted eligible surfaces, with Source/native fallback. Hidden must not mean inaccessible after plugin failure.
3. Support multiline summary/reflection and a paragraph editor, rather than copying record text-stage restrictions.
4. Decouple first summary creation from reflection so PRE/POST timing has no data-loss race.
5. Leave all-time outside automatic closed-period summarization and do not add monthly notes.
6. Add Reflect on yesterday alongside `[n==r`, which depends on actual previous links.
7. Preserve full historic Reviews and both yearly Theme/Outcomes; never truncate or silently reinterpret them.
8. Use policy routing rather than a sentinel. Supported workflows can reliably supply instructions; arbitrary agents cannot be forced to discover a file by its existence.
9. Do not block weekly review on every daily summary, or make generated summaries the authoritative work history.

## Sources

Repository files were read from checkouts opened through `sase repo open`; these links identify the inspected revisions.

- **[S1]** [Daily Headline parser](https://github.com/bobs-org/bob-cli/blob/e07a26bf86b93fe12df571ac6cb00f8b71d28cca/src/native/daily_headline.rs).
- **[S2]** [Period parser, digest, structure checks, YAML reader](https://github.com/bobs-org/bob-cli/blob/e07a26bf86b93fe12df571ac6cb00f8b71d28cca/src/native/periods/note.rs).
- **[S3]** [Guarded period drafting](https://github.com/bobs-org/bob-cli/blob/e07a26bf86b93fe12df571ac6cb00f8b71d28cca/src/native/periods/draft.rs).
- **[S4]** [Period contract](https://github.com/bobs-org/bob-cli/blob/e07a26bf86b93fe12df571ac6cb00f8b71d28cca/docs/periods.md), [scaffolds](https://github.com/bobs-org/bob-cli/blob/e07a26bf86b93fe12df571ac6cb00f8b71d28cca/src/native/periods/scaffold.rs), and [versioned instructions](https://github.com/bobs-org/bob-cli/blob/e07a26bf86b93fe12df571ac6cb00f8b71d28cca/src/native/periods/instructions.rs).
- **[S5]** [Period identity/calendar](https://github.com/bobs-org/bob-cli/blob/e07a26bf86b93fe12df571ac6cb00f8b71d28cca/src/native/periods/calendar.rs) and [CLI contract](https://github.com/bobs-org/bob-cli/blob/e07a26bf86b93fe12df571ac6cb00f8b71d28cca/src/native/periods/cli.rs).
- **[S6]** [Record guarded-update adapter](https://github.com/bobs-org/bob-plugins/blob/36d48017f9a16edaf21346fb0276c530836e08f4/plugins/bob-ledger-tools/src/242m-plugin-record-update-session.js).
- **[S7]** [Record display/editor contract](https://github.com/bobs-org/bob-plugins/blob/36d48017f9a16edaf21346fb0276c530836e08f4/docs/record-card.md).
- **[S8]** [Scoped property hiding](https://github.com/bobs-org/bob-plugins/blob/36d48017f9a16edaf21346fb0276c530836e08f4/plugins/bob-ledger-tools/src/242ka-plugin-record-sheet-properties.js).
- **[S9]** [Double-equals Vim dispatch](https://github.com/bobs-org/bob-plugins/blob/36d48017f9a16edaf21346fb0276c530836e08f4/plugins/bob-ledger-tools/src/248m-plugin-schema-double-equals.js).
- **[S10]** [Bank setup hosts](https://github.com/bobs-org/bob-plugins/blob/36d48017f9a16edaf21346fb0276c530836e08f4/plugins/bob-ledger-tools/src/248c-plugin-bank-setup-hosts.js).
- **[S11]** [Album surfaces/editor](https://github.com/bobs-org/bob-plugins/blob/36d48017f9a16edaf21346fb0276c530836e08f4/docs/albums.md).
- **[S12]** [CLI agenda headline contract](https://github.com/bobs-org/bob-cli/blob/e07a26bf86b93fe12df571ac6cb00f8b71d28cca/src/native/capture_pomodoros.rs).
- **[S13]** [Swift agenda decoding](https://github.com/bobs-org/bob-mac-capture/blob/868672fc516996dc3a36c53ec0114f4139213720/Sources/CaptureCore/CaptureAgendaModels.swift) and [presentation](https://github.com/bobs-org/bob-mac-capture/blob/868672fc516996dc3a36c53ec0114f4139213720/Sources/CaptureCore/CaptureAgendaPresentation.swift).
- **[S14]** [Evidence brief and neighbors](https://github.com/bobs-org/bob-cli/blob/e07a26bf86b93fe12df571ac6cb00f8b71d28cca/src/native/periods/brief.rs).
- **[S15]** [Navigation semantics](https://github.com/bobs-org/bob-plugins/blob/36d48017f9a16edaf21346fb0276c530836e08f4/docs/bob-navigation-hotkeys.md).
- **[S16]** [Bob timezone and date resolution](https://github.com/bobs-org/bob-cli/blob/e07a26bf86b93fe12df571ac6cb00f8b71d28cca/src/native/env.rs).
- **[S17]** [Validated, span-preserving record YAML edits](https://github.com/bobs-org/bob-cli/blob/e07a26bf86b93fe12df571ac6cb00f8b71d28cca/src/native/records/render.rs).
- **[E1]** [Official Obsidian Properties documentation](https://obsidian.md/help/properties), checked 19 November 2026.
- **[E2]** [Official Obsidian Decorations documentation](https://docs.obsidian.md/Plugins/Editor/Decorations), checked 19 November 2026.

Audited memory included Daily Headline, Period Note, Album Note, Record Note, Bank Badge, Bank Month Note, Morning GTD Review Footer, `obsidian.md`, `cli_rules.md`, `docs.md`, and decisions on close-key parity, idle agenda, thin Mac client, and daily releases. Glossary additions above are proposals, not claims that these terms already exist.

## Recommended solution

**Proceed with a period-aware intention card backed by `intentions`, `summary`, and `reflection` frontmatter.** Make Bryan's intentions/reflection easy to edit through `==`, keep summaries factual and protected, and reuse the card family's guarded session, lifecycle, and keyboard conventions.

Ship typed Bob data and reliable writer/instruction paths before hiding or migrating content. Use `intentions: []` for an enabled empty card, a proper multiline reflection editor, independent summary/reflection states, a central versioned policy, and additive Mac compatibility. Preserve historical Reviews and yearly Theme+Outcomes, then add the two lightweight GTD chores. This yields a coherent, attractive experience without making generated prose, hidden instructions, or a new universal framework responsible for the notes' integrity.
