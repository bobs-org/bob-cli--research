# Task types as a reliable routing contract

Independent research by **cdx**, 2026-10-29. Scope: design research and implementation guidance; no product code, vault data, glossary, or personal configuration was changed. No peer report, transcript, or findings were consulted.

**Recommendation:** adopt Task Type as the user-facing concept and make it the authoritative default for placing task links. Keep one effective type per task, allow a Pomodoro to contain several types, and apply type changes and live-link relocation as one reviewed operation. The rename and visual change are worthwhile; the consistency contract is the substantial engineering work.

The important qualification is that a task's current type describes its intended work category, while a completed Pomodoro records what happened. Those facts must be allowed to differ over time. A project can also contain several types: project identity should continue to come from the existing task-home system.

## Evidence and current behavior

I inspected these repository revisions, independently opened through `sase repo open`:

| Repository | Revision |
| --- | --- |
| bob-cli | `48253b7f225620f2cde10c856f458c31cd6f58d3` |
| bob-plugins | `68db3fbefa30e13767f58fcf18c9c0b3fccd4b53` |
| bob-mac-capture | `072055d01fea3f6e5e212b177f42f540d32f995b` |
| chezmoi / dotfiles | `8cdfe0440529bc2d25e89e0abb4913403786a63f` |

These are source and contract observations, not results from running the applications. I did not inventory the live vault or measure interaction latency. Consequently, migration counts, the prevalence of conflicting fields, and final appearance in Bryan's Obsidian theme remain implementation-time checks.

| What exists | Consequence for this proposal |
| --- | --- |
| The stored task field is **`[theme:: NAME]` / `(theme:: NAME)`**, not `type`. | The requested `[type:: NAME]` needs a real data compatibility strategy. A glossary rename alone will not do it. |
| Suggestions resolve from a task override, a reading-task rule, then a note/residence default; otherwise there is no suggestion. New-task suggestions currently use the destination note. | Add a global fallback and unify new/existing task resolution against the staged task contents. Preserve useful reading and note defaults. |
| Area/project frontmatter uses `theme: WRITE`; `theme: off` stops inheritance. `type: [[project]]` already describes a **note kind**. | Do not rename note defaults to frontmatter `type:`. Use a distinct name such as `task_type:`. |
| Explicit named capture can set or clear a theme field, but only under particular suggestion and single-non-exempt-component conditions. Implicit capture still chooses current/next. | Promote the suggestion into default routing and replace the limited field-write rule with one shared intent rule. |
| The Task Card explicitly rejects exempt themes. The underlying field parser can parse PLAN; the resolver can return it. | The PLAN restriction is a writer/UI policy, not a fundamental representation constraint. |
| Task Card field edits and Pomodoro bullet moves are separate plugin paths. Linked-task card edits even document possible partial results across notes. | Coupling them requires a broader transaction boundary, not an extra callback after a field write. |
| Rust capture has staged files, preimage checks, temporary files, and rollback. Its own comment says this is **not** cross-process locking or a fully serialized transaction. | Reuse the planner and writer infrastructure, but do not claim it already provides the stronger guarantee this feature needs. |
| Themes already have configured colors, ad-hoc warnings, normalized identity, history, hide/pin preferences, and composite names. | Preserve these assets rather than inventing a second category registry. |
| `#task` currently renders as a constant teal hash; reference and review-checklist tasks have specialized glyphs. Tasks query rows normally hide the ordinary task glyph. | The requested display affects several rendering surfaces and identity variants, not just the theme chip's CSS. |

Sources: [theme contract, especially PT12–PT13][theme-contract], [Rust task-field rules][task-theme], [suggestion resolver][suggest], [capture contract][capture-contract], [Task Card validation][card-validation], [Task Card writes][card-writes], [Pomodoro move writes][move-writes], [capture commit implementation][capture-commit], and [task-tag display contract][tag-contract].

Bryan's actual checked-in configuration already contains BUILD/yellow, CHORE/magenta, FIX/red, MEET/blue, PLAN/auto, READ/green, WRITE/violet. `plan.exempt` is `[PLAN]`, `plan.max_themes` is 3, `plan.max_links` is 13, and strict mode is false. CHORE is therefore an existing category with a stable color, making it a sensible personal fallback. [Personal configuration][personal-config]

## Is the idea good?

Yes, for this vocabulary. BUILD, READ, WRITE, FIX, MEET, PLAN, and CHORE describe kinds of work more clearly than the word “theme” suggests. The issue-tracker analogy is useful: Jira's documentation describes work types as categories that support searching, sorting, and tracking work. That supports the terminology, without requiring Bob to inherit Jira's hierarchy or workflow machinery. [Atlassian: work types](https://support.atlassian.com/jira-cloud-administration/docs/what-are-issue-types/)

The productivity claim needs more restraint. Leroy and Glomb's four-study research supports attention-residue effects during interruptions and a brief plan for resuming interrupted work. It does not establish that grouping all BUILD tasks across unrelated projects is better than staying within one project. **My inference:** category defaults can reduce planning decisions, but project continuity should remain available. Do not present this specific taxonomy or its default routing as experimentally validated. [Leroy and Glomb, 2018](https://experts.umn.edu/en/publications/tasks-interrupted-how-anticipating-time-pressure-on-resumption-of/)

Three distinctions make the design coherent:

1. **Type:** what kind of work this task currently calls for, such as FIX.
2. **Home/project:** what the work belongs to, such as Bob Capture.
3. **Pomodoro:** when a selection of work is planned or recorded.

A type does not determine a task's status, project, priority, freshness, or dependencies. A Pomodoro can combine types. A task can change type as its intended work changes, although a large item that routinely needs PLAN, BUILD, and WRITE may be clearer as several tasks.

Project-focused sessions already fit this model. Tasks retain BUILD or FIX, a merged session can say `BUILD + FIX`, and Bob derives its project/home display from the linked tasks. That is preferable to making every project name a permanent task type. Ad-hoc project names remain possible, with the existing warning. [Pomodoro homes][homes-contract]

The main failure mode would be treating every physical relocation as an invitation to reinterpret the task. Users often move something merely to adjust their agenda. Make a move's reclassification visible before commit, preserve compatible types in mixed sessions, and leave neutral containers neutral.

## Explicit adjustments to the requested requirements

These are deliberate changes or clarifications, not details to leave to individual implementers.

| Requirement | Recommended adjustment | Reason |
| --- | --- | --- |
| Every task gets a type by default. | Every **tracked open Bob task** gets an effective type; do not bulk-write CHORE onto the backlog. Plain checklist bullets are outside this policy. | Covers manual task creation and keeps inherited defaults meaningful without metadata churn. |
| Rename Pomodoro Theme to Task Type. | Rename the concept and public UI, retain “Pomodoro Theme” and “theme” as glossary aliases, and distinguish task types from note kinds and SASE bead types. | Existing notes, commands, and users still use the old vocabulary. |
| A type update moves links or creates a Pomodoro. | Relocate **existing** live links. If the task has no live link, change its type only. | Reclassification should not schedule backlog work or manufacture Today membership. |
| Current/future links are always consistent. | Cover dedicated links in today's open sessions and existing future daily notes; preserve completed/cancelled sessions and past daily notes. Raw Markdown edits and sync merges need detection/reconciliation. | Avoid rewriting history; an editable, distributed vault cannot guarantee instantaneous invariants after every external edit. |
| Moving to a differently typed Pomodoro changes the task type. | A singleton destination retypes. A composite containing the current type preserves it. A composite without it needs one explicit component choice. | A merged session has no single type to infer. |
| Types appear as `#TYPE` when the property exists. | Show `#TYPE` for the **effective** type, including inherited/default types, with provenance in the tooltip/card. | Otherwise the default remains invisible even though it controls routing. |
| Exempt types can be authored. | Make exemption solely a budget attribute; allow PLAN in fields, defaults, menus, and routing. | “Not counted” must not mean “invalid category.” |
| Duplicate-type Pomodoros are out of scope. | Defer new duplicate-management UX, but define deterministic selection among existing duplicates and preserve an exact selected entry. | Existing data already allows duplicates; automation cannot be undefined on it. |
| `#type` should update the `task` property. | Interpret this as updating the task's **`type` property**; do not introduce a `task` field. | The wording appears to contain a typo. |

I also recommend retiring the current **Alt+Enter “link once without changing type” exception for mismatched typed destinations**. It conflicts directly with the new invariant. It can still mean a one-time placement in a compatible composite or neutral container. If intentional mismatches remain a product requirement, the honest model is a separate per-link work-mode override; that would be a different feature with extra state, and I would defer it.

## The data model

A task has one effective type. A named Pomodoro has a set of type components. Keep the existing key normalization: collapse whitespace and lowercase for identity; display names remain uppercase. `BUILD + FIX` has two components, never one task type called “BUILD + FIX.” Do not replace identity with slugs: existing names containing spaces and hyphens need to remain distinguishable.

Resolve open-task types in this order:

1. A valid explicit `[type:: X]`; legacy `[theme:: X]` is a compatibility input.
2. The existing reading-task rule, normally READ, unless disabled.
3. The nearest valid area/project default along the existing residence/root walk.
4. The configurable global fallback, CHORE for Bryan.

Use the same resolver for new tasks, existing tasks, previews, rendered rows, suggestions, moves, and reconciliation. For new captures, resolve from the **staged task after parsing**, so a newly created reading task or explicit field is not treated differently from the same task a moment later.

Return provenance, not just a string: effective key/name, explicit or inherited source, declaring note when applicable, fallback reason, validity warnings, configured/hidden status, and resolved hue. “Use default · CHORE” is much clearer than “No theme.”

There is a concrete Dataview integration hazard: tasks inherit their parent page's fields. A task without an inline override in a `type: [[project]]` note can therefore expose the note kind through a raw `task.type` lookup. **Inference from that documented inheritance:** neither `task.type` nor a simple `WHERE type = "CHORE"` query is a reliable effective-task-type API. Provide a Bob resolver/query adapter that parses task-local fields and applies the same defaults, with a separately named result such as `effective_type`; use it in Bob dashboards. Raw Dataview queries will not automatically discover virtual CHORE defaults. If native Dataview field queries are a hard requirement, materializing types is an alternative with real inheritance/churn costs, not a free consequence of this design. [Dataview task metadata](https://blacksmithgu.github.io/obsidian-dataview/annotation/metadata-tasks/)

For an initial low-churn release, add a proposed setting:

```yaml
# Proposed addition to home/dot_config/bob/config.yml in chezmoi:
tasks:
  default_type: CHORE
```

Keep the existing `themes:` color vocabulary and `plan.exempt` configuration operational during the terminology migration. Their internal spellings do not justify replacing journals, caches, and every client at once. A future canonical config rename should have explicit aliases and conflict validation; it is not necessary for the behavior requested here.

I would use CHORE as the product fallback as well, with user override. If a deployment explicitly configures a different fallback, honor it. A missing configuration uses the documented fallback. An invalid configured fallback must produce an actionable error for mutations that need it, rather than silently choosing a different category. Cosmetic color failures can remain warnings. A fallback outside a configured vocabulary is usable with the ordinary ad-hoc warning; it must not disappear from routing because it lacks history.

For note defaults, introduce `task_type: WRITE` and continue reading legacy `theme:`. Never overload frontmatter `type: [[project]]`. Preserve the meaning of `off` as “stop walking ancestors”; under the new total-type model it then falls back to the global type. **This is a behavior change for notes using `off`** and belongs in the migration preview. Supporting an untyped escape hatch instead would weaken “every task has a type”; I do not recommend it for the default experience.

Keep “Use default” distinct from selecting a concrete type in the Task Card. Selecting BUILD explicitly pins BUILD, even when the current default is BUILD. “Use default” removes the override. This intentionally changes the current “select inherited value to clear” rule and avoids a surprising future reclassification when a note default changes. An explicit link move needs to write a field only if it actually changes the effective type; ordinary inferred routing does not pin defaults.

Malformed or conflicting authored fields require visible repair. A display may explain the provisional fallback, but an automatic link/move must not silently repair conflicting intent. An explicit Task Card selection can replace the conflicting type fields after showing the outcome.

## Routing and consistency rules

For a tracked open task `t` and a managed live Task Link under a named work session `p`:

```text
effective_type(t) belongs to type_components(p)
```

Apply this to dedicated Pomodoro child-link rows, using the existing link parser and canonical target identity. Do not touch prose mentions, dependency links, relation links, code examples, or arbitrary backlinks. Inventory labels and unnamed sessions are neutral containers, not task types. Explicit placement there preserves type; automatic placement prefers a real type session. This is a declared exception to the scope of the equation, not a hidden mismatch.

A managed action succeeds only when its post-state satisfies the invariant for the affected task's live links. **The initiating gesture chooses the direction:** a Task Card type edit determines destinations; a deliberate move into a different singleton type determines the task type. A passive reconciler never alternates between these directions based on which file changed most recently. Task metadata/defaults are authoritative during reconciliation.

| Gesture | Task effect | Link effect |
| --- | --- | --- |
| Capture/link without a suffix | Preserve resolved type. | Reuse/create a matching session. Never choose an unrelated current session merely because it is running. |
| Explicit `#FIX`, resolving to a FIX session | Set FIX if it differs from the effective type. | Place the selected link there and relocate other incompatible live links. |
| Move into `PLAN` | Allow/set PLAN. | Use PLAN and reconcile other live links with the same rule. |
| Move BUILD task into `BUILD + FIX` | Keep BUILD. | Preserve the exact selected destination. |
| Move WRITE task into `BUILD + FIX` | Ask for BUILD or FIX in the move flow; no write until chosen. | Apply the selected component and the move together. |
| Card: change linked task to READ | Set READ. | Move incompatible live links to READ-compatible sessions on their original dates. |
| Card: change unlinked task to READ | Set READ. | Create no link and no Pomodoro. |
| Card: Use default | Clear the explicit override and resolve again. | Rehome existing links only if their compatibility changes. |
| Move task to another note/change root | Recompute inherited type; retain explicit pins. | Rehome affected live links if the inherited result changes. |
| Complete, cancel, archive, or view history | Preserve existing recorded type/history under existing rules. | Respect existing close/removal behavior; do not rewrite past sessions to match today's type. |

The same rules must cover the less obvious writers: Ensure Next, reference “Today,” successor selections, rollover, named session rename, session split/merge, counted moves, note-default edits, and config changes. A central postcondition makes missed paths detectable. Preserve existing dependency behavior, including capture's narrow prerequisite-dropping rule and the different plugin guard; type-routing is not permission to bypass either. Successors still require explicit selection. Type-only edits do not stamp freshness or advance the review walk.

### Destination selection

For automatic placement on each affected date:

1. If the task is already linked compatibly, keep that placement; repeated linking can be a no-op.
2. Otherwise prefer a unique compatible running session on that date, if one exists.
3. Otherwise prefer the first open single-type session with the exact normalized type.
4. Otherwise use the first compatible composite in ledger order.
5. Otherwise create an untimed singleton session for that type using the established placement rules.

The picker and preview must show the actual selected session. Existing duplicate names use deterministic ledger order within a tier; the explicitly selected entry always wins for an explicit move. Never “resolve” a chosen entry again by display name. Use its validated entry reference and preimage. Preserve the existing refusal for ambiguous multiple running sessions when implicit selection needs that information.

Automatic type routing uses exact component keys, **not** slug-prefix matching. Keep legacy capture selectors compatible, but interpret their actual resolved destination in the type planner. For example, a prefix that resolves to a longer session name must show that destination and resulting type change in preview. Generated client requests should use exact names or entry references whenever the contract supports them.

A task retyped today must retain its dates: a link in tomorrow's daily note stays tomorrow. If only tomorrow has a link, create a matching session tomorrow if needed and do not add anything today. Do not create unrelated missing daily files just because a type changed. A missing/inaccessible affected note makes a strict multi-note mutation fail with a useful diagnostic.

Relocate links as owned blocks, preserving their child content and source order. Deduplicate only when doing so cannot discard content; identical bare links can coalesce, while distinct work/log descendants require a preserving merge or a refusal that shows the conflict. Empty untimed source cleanup should follow the existing move policy and appear in preview. Never delete or restart a running session as a side effect of a type edit, or discard its timespan and other work notes.

### Merged sessions, exemptions, and budgets

Merged sessions are **sets of accepted types**, not a new type. `PLAN + BUILD` must preserve a PLAN task as PLAN. The current rule that discards exempt components and selects BUILD is specifically unsuitable for this model. Merge unions components; a split or component-removing rename must validate linked tasks and rehome incompatible ones in the same operation.

Exemption remains independent of type validity and color. PLAN can be explicitly authored, inherit from a note, receive links, and count toward Today membership while remaining exempt from the existing planning budget. The current implementation exempts an entry's links only when **all** its components are exempt; a mixed PLAN + BUILD session is not fully exempt. Preserve that budget behavior initially and describe it honestly. [Plan budget implementation][plan-budget]

Automatic creation can exceed a budget. With Bryan's `strict: false`, show the warning and complete the requested action. With strict mode enabled, refuse the entire change before touching the type or links and show how the destination would exceed the cap. Do not silently fall back to the current mismatched session or suppress the required field update. Review strict enforcement across all participating writers, rather than only the old explicit `#NAME` capture path.

Ad-hoc valid types remain first-class values with a nonblocking warning. Explicitly authoring an ad-hoc type should make subsequent default routing honor it. This revises the current “unknown suggestions are never preselected” rule: once the value is authoritative task intent, ignoring it would violate the user's instruction. Show the warning when authored/committed, not on every keystroke; hidden types remain valid and keep their colors and history.

## The interaction and visual design

The core visual should be compact text at the task identity position, with no resting capsule:

```text
[ ] #BUILD  Add quick capture                 ▮▮  tomorrow
[ ] #PLAN   Break down the launch
[ ] #CHORE  Renew the domain
```

The stored first line still contains `#task` and its optional `[type:: BUILD]`. `#BUILD` is a display projection, not a replacement stored tag. This preserves the Tasks global filter, raw task identity, grep, Markdown portability, and source editing; type-aware queries need the resolver described above. Suppress the separate type chip only when the integrated mark is successfully present.

Use the existing Bob-resolved hue as the identity input, but give text a contrast-tested foreground variant. Current theme pills deliberately use normal text on a tinted background; copying their yellow into small text would not establish legibility. Check every palette slot against light/dark backgrounds and the existing blocked/next/pending row tints. Standard-sized text should meet 4.5:1 contrast, and color must have an accompanying label. [W3C contrast guidance](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum), [W3C use-of-color guidance](https://www.w3.org/WAI/WCAG22/Understanding/use-of-color)

Use a medium-weight compact label, the existing hash geometry or a well-aligned textual hash, minimal horizontal padding, and no separate status color logic. On hover/focus, a faint tint can expose the affordance. Unconfigured types get a small dotted underline or warning indicator plus “not in your task types,” not an orange filled pill. PLAN/auto may remain neutral gray under the current palette rule; exemption does not make it less valid. Long and multiword names need ellipsis/full tooltip in constrained query rows, without turning spaces into a different stored identity.

The tooltip/card should explain:

```text
Type: CHORE
Uses your default
New task links go to CHORE
```

For an explicit type: “Type: FIX · set on this task.” For inheritance: “Type: WRITE · from sase_blog.” Put details there instead of extra badges on every row. In raw editing, reveal the underlying `#task` and field using existing selection/cursor conventions; copy/round-trip must not invent a literal `#BUILD` tag. Keep the current tag-search/editor behavior unless intentionally redesigning it, and provide the existing Task Card as the reliable way to change type.

Cover Live Preview, reading view, embeds, hover previews, Tasks results, Dataview task rows, print/export, and pop-out windows. Tasks results will now need a compact type identity even where the generic hash was hidden. Keep the reference book and PRE/POST checklist glyphs: append the type text to that identity family rather than erasing their special meaning. Closed tasks with explicit historical types can retain a quiet label; do not paint every legacy completed task CHORE based on today's newly configured fallback.

Rendering must use cached resolver results, batched invalidation, and lazy provenance details. Do not spawn one `bob` process per visible row. Avoid two competing decorations for `#task` and `[type::]`; a single row model should own which token ranges are hidden and which identity is displayed. Missing/stale data should reveal honest source text or the generic identity rather than a confidently wrong type.

A good Task Card preview is one sentence plus the destination:

```text
Type  FIX  →  BUILD
Move 2 planned links to BUILD · create 1 session tomorrow
```

For no live links: “Type BUILD · no scheduled links.” For capture: “CHORE · uses your default · new Pomodoro” or “FIX · changes type from BUILD.” Show the result before Return; do not add a confirmation dialog for every ordinary change. Composite ambiguity is the exceptional case that needs an additional choice. Offer one undo operation covering the field and all relocated links, with stale-state protection.

## Implementation architecture and reliability

I favor **one Rust policy/planning core and one coordinated mutation boundary**, consumed by capture and Obsidian. Retain plugin-side pure models for responsive projection where needed, with shared conformance fixtures, but do not independently invent retyping rules in Swift or in each plugin gesture.

A request should express intent and identity: set/use-default type, link by resolved default, or move to a specified entry. Its plan should include resolved before/after types, affected task identities, source/destination link blocks and dates, created/removed sessions, warning/budget results, and exact file preimages. The same plan powers dry-run UI and commit. Mac Capture continues to render Bob's result and submit one aggregate request.

Reuse `CaptureBatchPlanner` and existing task/link parsers. Extract a planner that can see every affected source note and live daily note; do not call a second independent capture command for each link after updating the task. The existing `vault_rewrite` machinery is relevant for maintenance/migrations, but its sync/commit workflow should not automatically be put on every keystroke-driven task gesture.

The write design needs all of the following:

- Validate task IDs, destination refs, config/default fingerprints, all touched file preimages, dependency guards, and budget results before writing.
- Serialize cooperating Bob writers with the established vault lock strategy; avoid nested locks. Recheck disk preimages immediately before replacement.
- Stage postimages and maintain a durable recovery record before the first replacement for these multi-file operations. A crash after file one must be distinguishable from success.
- Roll back only when the current file still matches this operation's postimage. If another writer changed it, preserve the competing data and report recovery needed; never blindly restore an old backup over someone else's edit.
- Re-read and verify the relevant postcondition before returning success. Incomplete recovery is an explicit failure, with enough information to finish or undo it.
- Make retries idempotent: an interrupted/retried request must not add a second link or create a second session. Use operation identity where recovery needs it, plus stable task/entry identity and semantic no-op checks.

Obsidian's unsaved editors are part of this problem. An implementation must coordinate affected buffers with the disk transaction: capture their revision and exact contents, save only affected buffers through Obsidian's normal save path, wait for matching disk preimages, and guard/revalidate edits during commit. If a buffer changes, replan or refuse rather than overwrite it. Reload only when it cannot discard newer edits. A JSON endpoint with “atomic” in its description does not solve this editor/disk race by itself.

These guarantees apply to cooperating managed actions. Uncoordinated Markdown edits and cross-host sync can still introduce mismatches. Add a read-only lint showing the task's effective type, incompatible live sessions, and a precise repair action. Reconciliation follows task intent and moves links; it never guesses that an accidental ledger edit should retag the task. No silent repair on hover/render. Hook reconciliation can handle unambiguous repairs through the same planner, while malformed fields, missing targets, or changed buffers require visible intervention.

Use a disposable index of canonical daily-note Task Links to find future placements, invalidated by file fingerprints and date/config changes. The index accelerates planning; commit still checks original files. Do not scan the whole vault for each keypress. Default changes or note moves can affect many inherited tasks, so preview/reconcile only tasks with live links; leave the unlinked backlog virtual. Configure the same default across Bryan's hosts via chezmoi, and include policy fingerprints in cache invalidation to prevent different hosts silently routing identical tasks differently.

## Compatibility, migration, and delivery boundaries

This should be a staged behavior rollout, with a migration preview, rather than a global search-and-replace.

**Readers first.** Accept canonical `[type::]` and legacy `[theme::]` in task context, including parenthesized fields. Accept `task_type:` and legacy `theme:` for note defaults. Mixed fields with the same normalized value can be reported as redundant; conflicting values are repair state, not “last field wins.” Leave note-kind frontmatter `type:` completely alone. Preserve code fences, prose, line endings, trailing metadata, and task/block identity.

**Update every writer before canonical writes.** Old plugins may read only `theme` and then overwrite or ignore `type`. Deploy compatible Bob/plugin/Mac versions before enabling new field writes. Do not dual-write both field names indefinitely. Advertise operation capabilities so an old backend cannot silently execute a partial version of the new behavior. Mac should decode additive data and keep a clear fallback when the required routing capability is absent.

**Canonical writes and backfill.** New managed writes emit one `[type:: NAME]`. Reading legacy syntax remains supported. Offer a previewed migration of existing eligible task fields and note defaults, with a list of conflicts and `off` behavior changes. Completed records may retain their legacy field spelling under compatibility reads; never reclassify them from current defaults. Preserve old daily session names and the `.bob/themes/<host>.jsonl` preference journal. Vocabulary renames and historical reclassification remain explicit maintenance operations.

**Terminology without unnecessary breakage.** Rename the glossary entry and UI labels, update the behavior contracts and examples, and retain old glossary aliases. Proposed glossary text:

> A Task Type is one named category of work, such as BUILD, READ, or CHORE. Every open tracked task has one effective type, resolved from an explicit task field or its defaults. A Pomodoro can accept one type or a `+`-separated set of types; its name records those components. Managed linking and type changes keep live planned links compatible. Exemption affects planning budgets, not whether a type is valid. Type identity, colors, ad-hoc warnings, hiding, and history use Bob's shared catalog. Formerly called Pomodoro Theme. A task type is distinct from a task's project, status, note kind, and a SASE task bead type.

The implementation plan should carry the required memory decisions for the glossary and any superseding policy records; accepted decision bodies should not be casually rewritten. Keep published documentation URLs working. Preserve old CLI commands as permanent hidden aliases if public command names change, as required by this project's CLI rules. There is no need to rename every Rust module, JSON key, CSS class, or journal event to ship the experience. If new JSON names are introduced, add them compatibly and keep old fields meaningful until clients are upgraded. Record behavioral CLI/JSON breaks appropriately for the daily release train.

**Personal setting.** Once the resolver supports it, add `tasks.default_type: CHORE` in `home/dot_config/bob/config.yml` in the opened chezmoi repository and apply the normal chezmoi deployment workflow. Do not write an unsupported setting in advance. This research leaves that requested implementation step pending.

A practical delivery boundary is: resolver and compatibility readers; common mutation planner and transaction checks; migration of capture and plugin writers; integrated type identity rendering and Mac previews; then the explicit data/config rollout. Full duplicate-session management, AI classification, project-specific type registries, and per-link work-mode overrides remain out of scope. Existing duplicates, composite sessions, crash recovery, and conflicting fields remain in scope because today's data can already contain them.

## Acceptance cases that determine whether this is ready

| Case | Required result |
| --- | --- |
| Untyped task, no note default, BUILD currently running | Implicit capture targets CHORE, creating an untimed session if needed; BUILD's timer remains unchanged. |
| A newly captured reading task | Resolves to READ using the same staged-task rule as an existing reading task. |
| Unlinked backlog task changes from CHORE to FIX | Only the type changes; no Today link, session, lane promotion, or freshness stamp. |
| Task has links today and tomorrow, plus a completed link yesterday | Type edit relocates today's/tomorrow's incompatible links within their respective dates; yesterday's bytes remain unchanged. |
| PLAN selected in card or via link move | Valid explicit type and destination; exemption and hue follow separate policies. |
| BUILD task moved into BUILD + FIX | Task remains BUILD; no needless override. |
| WRITE task moved into PLAN + BUILD | Explicit PLAN/BUILD choice; no automatic preference for the non-exempt component. |
| Two existing FIX sessions | Stable deterministic automatic choice; an exact user-selected second session is honored. |
| Same command retried or two captures in one batch need CHORE | No duplicate link/session introduced; later items see the staged earlier creation. |
| Task field/default/root changes, or task moves notes | Recompute effective type and reconcile existing live links; explicit pins survive inheritance changes. |
| Conflicting `[type:: FIX] [theme:: BUILD]` | Clear repair state; no silent data loss or automatic guess. |
| Task without an inline type in a `type: [[project]]` note | Bob's effective-type query/rendering API returns the resolved work category, never the inherited note-kind link. Raw-query limitations are documented. |
| Blocked task, guarded link, strict budget refusal, stale note, missing target | No partial type write, orphan session, or lost link. Existing guard semantics remain intact. |
| Failure on the second file, process crash, or concurrent editor update | Recoverable outcome, safe rollback rules, and no false success. |
| Hand edit or sync introduces mismatch | Visible lint and deterministic repair following task intent. |
| Light/dark/blocked rows; Tasks/Dataview; reference/checklist glyphs; plugin disabled | Readable, nonduplicated type identity; raw `#task` and metadata remain usable. |
| Global fallback changes | Inherited open tasks update predictably; affected live links are reconciled; historical time does not move between types. |

Use the existing Rust/JavaScript theme conformance vectors as a base and add cross-surface fixtures for intent, membership, aliases, inheritance, and exemptions. Add fault-injection tests at actual multi-file write boundaries. Verify exact unrelated-byte preservation, stale-preview rejection, and dry-run/commit equivalence. Compile and test Mac changes according to its repository instructions; portable checks alone do not verify macOS UI targets. Run relevant generated-plugin and documentation checks when implementing. No product tests were run for this research-only report.

One further reporting trap deserves an explicit test: current Stats attributes session time by the session's `+` components. Renaming the UI to “Task types” must not imply measured per-task time, and changing a task's current type must not rewrite the historical breakdown. Preserve the existing split arithmetic and explain mixed-session allocation. [Stats contract][stats-contract]

## Alternatives and recommended solution

| Approach | Assessment |
| --- | --- |
| Rename labels and change chips only | Pleasant but leaves the central routing inconsistency unresolved. |
| Stamp every task with CHORE and update it opportunistically | Simple local code, but creates churn, weakens inheritance, and still misses multi-file consistency. |
| Let task type and session mode differ freely | Valid conceptual alternative, especially for varied project work, but fails the requested invariant unless per-link override state is introduced. |
| One task type, composite session membership, coordinated intent-driven writes | Best match to the request and existing architecture; requires explicit transaction and migration work. |

**Recommended solution:** proceed with Task Types, a virtual CHORE fallback, the existing reading/note inheritance rules, and an integrated colored `#TYPE` identity. Make typed links follow the effective type by default and make deliberate incompatible singleton moves retype and reconcile the task's other live links in one operation. Accept PLAN normally, preserve mixed-session membership, and retain project identity through task homes. Keep completed history stable and never schedule an unlinked task merely because its type changed. Ship the shared resolver, coordinated writers, compatibility readers, and failure tests before enabling the new behavior across clients; that is the foundation that makes the simpler interface trustworthy.

[theme-contract]: https://github.com/bobs-org/bob-cli/blob/48253b7f225620f2cde10c856f458c31cd6f58d3/docs/pomodoro-themes.md
[task-theme]: https://github.com/bobs-org/bob-cli/blob/48253b7f225620f2cde10c856f458c31cd6f58d3/src/native/task_theme.rs#L85
[suggest]: https://github.com/bobs-org/bob-cli/blob/48253b7f225620f2cde10c856f458c31cd6f58d3/src/native/pomodoro_themes/suggest.rs#L82
[capture-contract]: https://github.com/bobs-org/bob-cli/blob/48253b7f225620f2cde10c856f458c31cd6f58d3/docs/capture.md#L1030
[card-validation]: https://github.com/bobs-org/bob-plugins/blob/68db3fbefa30e13767f58fcf18c9c0b3fccd4b53/plugins/bob-navigation-hotkeys/src/315-task-card-theme-stage.js#L104
[card-writes]: https://github.com/bobs-org/bob-plugins/blob/68db3fbefa30e13767f58fcf18c9c0b3fccd4b53/plugins/bob-navigation-hotkeys/src/352-picker-task-card-theme-stage.js#L430
[move-writes]: https://github.com/bobs-org/bob-plugins/blob/68db3fbefa30e13767f58fcf18c9c0b3fccd4b53/plugins/bob-navigation-hotkeys/src/650-plugin-move-commit.js#L3
[capture-commit]: https://github.com/bobs-org/bob-cli/blob/48253b7f225620f2cde10c856f458c31cd6f58d3/src/native/capture/commit.rs#L159
[tag-contract]: https://github.com/bobs-org/bob-cli/blob/48253b7f225620f2cde10c856f458c31cd6f58d3/docs/task-tag-marks.md
[personal-config]: https://github.com/bbugyi200/dotfiles/blob/8cdfe0440529bc2d25e89e0abb4913403786a63f/home/dot_config/bob/config.yml#L90
[homes-contract]: https://github.com/bobs-org/bob-cli/blob/48253b7f225620f2cde10c856f458c31cd6f58d3/docs/pomodoro-homes.md
[plan-budget]: https://github.com/bobs-org/bob-cli/blob/48253b7f225620f2cde10c856f458c31cd6f58d3/src/native/plan_budget/mod.rs#L418
[stats-contract]: https://github.com/bobs-org/bob-cli/blob/48253b7f225620f2cde10c856f458c31cd6f58d3/docs/stats.md#L287
