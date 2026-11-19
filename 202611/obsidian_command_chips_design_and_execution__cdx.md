# Command chips for Bob: an actionable note surface over Command Mode

Independent research by **cdx**, 2026-11-19. This is a design recommendation, not an implementation or an approved plan. No peer research report, peer findings, or peer transcript was consulted. No product code, vault task, or canonical memory was changed.

**Recommendation:** Build command chips. Make them a second explicit chip kind in the existing plugin, displayed as **Bob Chips** while retaining the `bob-copy-chips` plugin ID. Use `run:` / `run[LABEL]:` inline spans and `bob-run` fences. Execute through a new, supported Command Mode API that shares its existing single-run and sequence paths. Integrate Cmd+Enter into the existing navigation dispatcher and its contextual hints. Begin adoption with the daily sync sequence, task reconciliation, and the Bob-only part of bank import.

The idea is good because it puts a repeatable action beside the instruction that explains when to perform it. The dangerous version would turn any apparent command in a note into executable text, implement another process runner, or confuse running a command with completing its task. Explicit syntax and a shared execution contract avoid those problems.

## Evidence and scope

I inspected these independently:

- `bob-cli-ni` through `sase bead read`, including its completed phases and landing notes; the approved `plan:202611/copy_chips.md` through `sase artifact read`.
- bob-cli at `a29a64f63884c9cfa960928c7a2d3c6b48693f36`.
- bob-plugins at `3968f0d70e8d45a1c225a6bb111df3f1805a956e`, opened through `sase repo open bob-plugins`.
- The vault repository at `ba65485844e17bf5f7e353dda2f4913797c4fbd7`, opened through `sase repo open gh:bobs-org/bob`. This is a remote-backed checkout, **not a claim about unsynced changes currently in `~/bob`**.
- The installed binary's read-only `bob __catalog --protocol 1` response, reporting version `0.5.0`.
- Official Obsidian editor-decoration documentation and W3C button guidance.

Source links below pin repository evidence to those revisions. The checked-out bob-cli copy-chip documentation mirror describes an early phase, while the linked plugin manifest is already `0.4.0` and the completed epic describes shipped authoring and cursor APIs. The implementation and audited landing evidence are the stronger references for current capabilities.

No real Obsidian session or macOS UI was available for this investigation. UI behavior below is a design, with an explicit acceptance matrix; it is not presented as visually tested.

## What the existing system already provides

### Copy chips are a useful foundation

The existing plugin has a pure grammar, label escaping and serialization, inline Live Preview widgets, Reading-view buttons, `bob-copy` fence cards, source reveal, an authoring modal with stale-write checks, and a frozen `api.copyChips` namespace. Live Preview already suppresses click actions for drags and distinguishes Alt+Click editing. Rendering does not write the note. The copy-chip epic also established the visual vocabulary: restrained borders, theme colors, fixed icon slots, and visible keyboard focus. [Copy-chip source](https://github.com/bobs-org/bob-plugins/tree/3968f0d70e8d45a1c225a6bb111df3f1805a956e/plugins/bob-copy-chips/src), [manifest](https://github.com/bobs-org/bob-plugins/blob/3968f0d70e8d45a1c225a6bb111df3f1805a956e/plugins/bob-copy-chips/manifest.json), [epic](https://github.com/bobs-org/bob-cli--beads/blob/main/pages/bob-cli-ni/README.md).

Reuse that infrastructure, but preserve the distinction: copying arbitrary text is cheap and reversible; activating a command may change several notes or a remote service. A command chip needs a different icon, an explicit action label, source validation, and execution feedback.

### Command Mode already owns the hard execution work

Command Mode has catalog-driven policy, direct `spawn` without a shell, saved run records, output capture, writer serialization, save-open-editors checks, duplicate detection, receipts and reload adoption, output pagers, notifications, and invalidation events. Its sequence driver runs **all steps in order, including reads**, stops on failed/unknown/stopped, and continues on completed/needs-attention. Sequence summaries support Output, Rerun, and Resume. These are existing capabilities, not a new command-chip engine to build. [Runner](https://github.com/bobs-org/bob-plugins/blob/3968f0d70e8d45a1c225a6bb111df3f1805a956e/plugins/bob-command-mode/src/060-runner.js), [sequence driver](https://github.com/bobs-org/bob-plugins/blob/3968f0d70e8d45a1c225a6bb111df3f1805a956e/plugins/bob-command-mode/src/065-sequence-runner.js), [sequence integration](https://github.com/bobs-org/bob-plugins/blob/3968f0d70e8d45a1c225a6bb111df3f1805a956e/plugins/bob-command-mode/src/095-plugin-sequences.js).

There are three gaps to address deliberately:

1. **The public API exposes single runs and previews, but not sequence execution.** Calling its private plugin methods from chips would create an undocumented dependency. Publish a supported entry point around the existing orchestration. [API](https://github.com/bobs-org/bob-plugins/blob/3968f0d70e8d45a1c225a6bb111df3f1805a956e/plugins/bob-command-mode/src/080-api.js).
2. **The existing tokenizer does not parse command lists.** A probe returned `['gcal','sync','-n','2','&&','bob','gmail','sync']` for a supposed two-command string. Add a quote-aware list splitter; do not pass that string to `run()` and expect a sequence. [Tokenizer](https://github.com/bobs-org/bob-plugins/blob/3968f0d70e8d45a1c225a6bb111df3f1805a956e/plugins/bob-command-mode/src/175-args-vim.js).
3. **The runner is lower-level than a safe persisted-command interface.** In `runInner`, an unknown catalog entry does not itself cause rejection, options can override metadata, and a supplied entry ID bypasses raw-command exclusions. A chip API must validate known entries and exclusions before reaching this escape hatch. Authored Markdown must never supply `entryId`, `effect`, `policy`, executable paths, or arbitrary run options.

### Cmd+Enter is already occupied—and already has hints

The vault explicitly binds Meta+Enter to `bob-navigation-hotkeys:open-reference-pdf-in-highlights`. That command dispatches PDF/highlight opening, Gmail opening, or opening a link in a new tab. Its source even explains why a default hotkey lost to Obsidian's built-in binding. A separate chip binding would be unreliable. [Vault binding](https://github.com/bobs-org/bob/blob/ba65485844e17bf5f7e353dda2f4913797c4fbd7/.obsidian/hotkeys.json#L242), [registration](https://github.com/bobs-org/bob-plugins/blob/3968f0d70e8d45a1c225a6bb111df3f1805a956e/plugins/bob-navigation-hotkeys/src/490-plugin-lifecycle.js#L102), [dispatcher](https://github.com/bobs-org/bob-plugins/blob/3968f0d70e8d45a1c225a6bb111df3f1805a956e/plugins/bob-navigation-hotkeys/src/677-plugin-ref-pdf-open.js).

The existing Highlights hints provide a status-bar keycap, cursor-context updates, stale async-result protection, and a line rail. Extend this into a shared contextual-action hint model. Its current implementation is Mac-only; command hints must use the actual configured binding and must not inherit a blanket Mac-only visibility check. [Hints](https://github.com/bobs-org/bob-plugins/blob/3968f0d70e8d45a1c225a6bb111df3f1805a956e/plugins/bob-navigation-hotkeys/src/677d-highlights-hints.js).

## Product design

### A small, explicit source language

Recommended forms:

| Purpose | Markdown source | Rendered face |
| --- | --- | --- |
| One literal command | `` `run: bob task reconcile` `` | ▷ `bob task reconcile` |
| Named command | `` `run[Reconcile tasks]: bob task reconcile` `` | ▷ Reconcile tasks |
| Compact bulk action | `` `run[Sync inboxes]: bob gcal sync -n 2 && bob gkeep pull && bob gmail sync` `` | ▷ Sync inboxes · 3 |
| Longer sequence | A `bob-run` fence with one command per line | A small titled card with Run 3 |

Example fence under a task:

````markdown
- [ ] #task Refresh inboxes
  ```bob-run Sync inboxes
  bob gcal sync -n 2
  bob gkeep pull
  bob gmail sync
  ```
````

Use the established optional-label escaping and longer-backtick serializer. The source remains legible when the plugin is disabled. Avoid additional aliases such as `cmd:`, `exec:`, and executable links in the first version. A bounded search of active note material outside reference, archive, and internal stores found no existing `run:` chip or `bob-run` fence collision; implementation should repeat the census against the live vault.

The payload is a sequence of Bob argv lists, **not shell source**:

- Each step starts with literal `bob`, which the parser removes before catalog resolution. No executable paths, environment prefixes, `sudo`, or other programs.
- Inline `&&` separates steps only outside quotes and escapes. Fences also allow newline separators. Quoted `"A && B"` remains one argument. A trailing operator or empty step is invalid; blank fence lines may be ignored.
- Arguments use Command Mode's quoting and escape semantics. An unclosed quote or unfinished escape invalidates the whole chip. Physical multiline quoted arguments and shell line continuations are outside v1.
- Unsupported unquoted shell operators such as `|`, `||`, `;`, redirection, and background `&` should produce a clear diagnostic. There is no variable, command, or template expansion. Quoted argument text remains literal, as it does in Command Mode.
- Do not ban legitimate `~`, `*`, or `?` arguments globally. Individual Bob commands may interpret them: `bank import` explicitly does its own tilde/glob expansion.
- `&&` is familiar authoring shorthand for a **Command Mode sequence**. Its continuation rule is outcome-based; it is not a promise of shell exit-code semantics. Needs-attention continues, exactly as it does in the sheet.

One visual chip can contain several commands. Three separate command chips remain three separate actions; the shortcut must not silently collect and run them.

### Activation should mean “run now”

Clicking a command chip, activating its focused button, or invoking the eligible Cmd+Enter action should have the same execution meaning as **Ctrl+Enter in Command Mode**: run now, bypassing its preview/confirmation interaction, while preserving catalog restrictions, host checks, save guards, queueing, and outcome handling. The request explicitly asks for this parity; adding a mandatory confirmation on every click would undermine it.

Provide inspection separately: the tooltip/focus detail shows the commands in order; a context-menu action opens them in Command Mode for review. A single command can use the existing preview API when supported. Do not pretend that a sequence of dry runs is an atomic preview of dependent writes.

Running a chip does **not** complete, reschedule, freshen, or advance the owning task or its walk. A successful sync is evidence that the sync ran, not evidence that the entire recurring chore is done. The user still completes the task with the existing gesture. Of course a deliberately authored Bob command can itself modify task state; chips add no extra task-state behavior.

### Exact shortcut targeting

Resolve the target from the live editor buffer, with one shared function used for both the hint and activation:

1. Require one collapsed caret in the active Markdown editor. Do not fire through a modal, search box, multicursor state, or arbitrary selection. A focused rendered chip button has its own direct activation.
2. If the current line contains exactly one command chip, use it. A cursor on or inside a closed `bob-run` fence resolves that whole fence as one chip.
3. If the current line contains multiple command chips, report ambiguity and stop. Even a caret inside one does not override the requested single-chip rule; clicking the desired chip remains available.
4. If the line contains none, find its nearest owning task using the existing Markdown/list-aware task resolver. Search that task's own line and owned non-task children, excluding nested tasks and their subtrees. Exactly one chip qualifies.
5. No chip means the existing PDF/Gmail/link behavior remains available. Ambiguous, malformed, unsupported, or unavailable chip intent is a handled refusal, not permission to unexpectedly open a link.

Exclude frontmatter, comments, ordinary code examples, inline code payloads nested inside copy chips, and generated history/log drawers from fallback discovery. An unterminated command fence is invalid rather than an invitation to run the rest of the note. Do not follow arbitrary task links or reference links to find a hidden command in another note in v1.

A chip on the current line takes precedence over links on that line, matching the requested behavior; the hint must make that precedence visible. This matters for the Bank task, which also contains a website and a `[[bank]]` link. With no chip candidate, existing navigation remains unchanged.

For nested tasks, a child without a chip must never borrow its parent's chip. A plain child bullet may use its owning task's chip. The existing `findOwningTaskLine` is a useful starting point, but command-chip eligibility needs its own tested result type: `none`, `ready`, `ambiguous`, `invalid`, or `unavailable`. [Task ownership helper](https://github.com/bobs-org/bob-plugins/blob/3968f0d70e8d45a1c225a6bb111df3f1805a956e/plugins/bob-navigation-hotkeys/src/070-recommended-roll-batch.js#L442).

### Appearance and discoverability

Use the copy chip's dimensions and typography, with a Lucide play glyph and a pointer cursor. Unlabeled commands remain monospace; labels use the note font. Bulk chips add a quiet command count. Use the theme's border, background, accent, success, and error variables; no user-authored colors or large saturated buttons.

On the eligible line, tint the target's border subtly and show a contextual keycap without requiring hover. The shared status hint should name the exact action:

```text
Note:      ☐ Refresh inboxes  [▷ Sync inboxes · 3]
Hint:      [⌘↵] Run Sync inboxes · 3 commands
Running:   [◌ Sync inboxes · 2/3]       Command Mode: 2/3 · Keep inbox · 00:08
Halted:    [! Sync inboxes · 2/3]       Output · Resume from 2
```

If fallback selected a chip elsewhere in the task, the hint says `Run task command · Sync inboxes` and a restrained rail associates it with the task. Keep one contextual action hint; do not show contradictory “Open PDF” and “Run” keycaps. For source mode or revealed inline code, the status hint remains useful even when the button is not rendered. If the hotkey was removed or rebound, display the actual binding or a click/palette hint, never a false `⌘↵` promise.

Use a fixed icon slot for ready, queued/running, completed, attention, and failed states so the text does not move. A success check is temporary and explicitly means the last run completed; it is never a recurring-task completion badge. Detailed errors and output stay in Command Mode's existing summary/pager, avoiding a second notification system. Respect reduced motion.

Reading-view actions should be real buttons with accessible names such as “Run Sync inboxes, 3 commands,” Enter/Space activation, visible focus, and disabled reasons. Keep focus in the originating context unless the user requests output. These choices follow the [W3C button pattern](https://www.w3.org/WAI/ARIA/apg/patterns/button/).

Live Preview should reuse the viewport-scoped decoration approach; source selection reveals Markdown and dragging selects rather than runs. Obsidian documents view plugins for viewport-local decorations and state fields for decorations that affect layout outside that viewport. A block card must use the appropriate mechanism rather than an inline replacement spanning newlines. [Obsidian decorations](https://docs.obsidian.md/Plugins/Editor/Decorations).

## Architecture and reliability contract

### Keep the plugin identity stable

Rename the **display name** to Bob Chips and extend the existing package. Retain its directory/manifest ID `bob-copy-chips`, existing command IDs, `api.copyChips`, and copy-specific behavior. Add a separate `api.commandChips` namespace. This gives users one coherent chip feature while avoiding migration of the sync allowlist, installed-plugin list, vimrc mappings, hotkeys, API consumers, and deployment directories.

A full ID rename to `bob-chips` offers little user benefit now. If undertaken later, make it a dedicated migration with compatibility and deployment tests; do not register two active renderers as a shortcut. A new standalone command-chip plugin would duplicate grammar, widgets, authoring, and deployment work. Keep process execution in `bob-command-mode`, regardless of where rendering lives.

The existing copy plugin supports mobile. Preserve that: copy chips keep working, command chips render legibly with “Run on desktop” or the missing-engine reason, and desktop-only modules are loaded only by the command engine. Do not make all copy functionality desktop-only merely because a new chip can execute a command.

### Publish an execution boundary, not private-method access

An illustrative additive API is:

```javascript
commandMode.prepareCommands(text) // pure, against the cached catalog
// -> ready steps, display/availability metadata, or structured diagnostics

commandMode.executeCommands(text, { intent: "run-now", source })
// -> revalidated single run or sequence, with existing feedback and history
```

Names are provisional; the boundary is the recommendation. Preparation must be usable by authoring and hint code without launching Bob or reading the vault on every caret move. Execution reparses and validates, then routes one step through the normal run path and two or more through the existing sequence orchestration. An `onExecutionChanged` subscription or equivalent handle should let all rendered instances observe queued/running/finished state. Consumers feature-detect the added methods.

Keep command-list tokenization, alias expansion, catalog classification, and execution policy in Command Mode. The chips plugin owns Markdown grammar and presentation. Navigation owns the shared Cmd+Enter dispatch. Resolve actual command names through the binary's catalog, not a second list in the chip plugin. [Catalog contract](https://github.com/bobs-org/bob-cli/blob/a29a64f63884c9cfa960928c7a2d3c6b48693f36/docs/command-catalog.md).

Required invariants:

- **Validate every step before starting step one.** Reject malformed syntax, non-Bob commands, exclusions, unknown entries, unavailable hosts, and statically known missing arguments. Catalog v1 does not describe every flag's full grammar, so do not claim this proves every CLI invocation valid; runtime validation remains Bob's job.
- **Keep policy bypass narrow.** Only the explicit run-now interaction bypasses preview/confirmation. It does not bypass saving notes, writer serialization, host restrictions, or exclusion checks. Never hand authored options to the runner.
- **Snapshot intent.** At activation, re-resolve source and compare it with what the widget represents. If it changed, refresh and require a fresh activation. Once accepted, run an immutable argv sequence, even if the first step changes the source note.
- **No replay surprises.** Hold a synchronous in-flight latch before the first await; use shared command-engine duplicate protection as well. Key repeat and double clicks must not enqueue duplicate work. Duplicate activation should identify/open the live execution.
- **Partial success is visible.** Completed earlier steps remain committed. No all-or-nothing promise, automatic rollback, or automatic retry. Preserve the existing Resume and Rerun distinctions. An unknown result after reload never justifies automatic repetition.
- **Saving at the right time matters.** The current runner saves before queue insertion. Audit queued writers against edits made while waiting; a save guard at actual writer dispatch is stronger. Fix any demonstrated gap centrally for sheet and chip runs together, not in a chip-only runner.
- **Rendering has no side effects.** No execution on note open, hover, scroll, focus, parsing, query rendering, or export. Preserve source association in embeds. If a rendered surface cannot establish reliable source identity, show the chip as inspectable but unavailable, or send the user to its source; do not execute an unverified stale DOM payload.
- **Failure is explicit.** Missing Command Mode, stale/unsupported API, missing binary, save failure, malformed Markdown, or catalog mismatch produces an explanation and no fallback shell.
- **Keep execution state host-local.** Run IDs, timestamps, progress, and logs belong to Command Mode, not synced note text. Source path/block ID/line may be optional provenance; a line number alone is not stable identity.

Do not promise global transaction isolation across a bulk sequence: the current engine serializes writers and orders that sequence's steps, but unrelated work may run between steps. Changing that would be a separate engine policy decision.

### Authoring

Extend the existing make-or-edit card with an explicit Copy / Command choice, defaulting to Copy for new arbitrary text and preserving the kind of existing chips. Never infer execution merely because selected text begins with `bob`. Command authoring shows a label field, one-command-per-line editor, rendered preview, exact Markdown, and per-step validation. Alt+Click edits without running; Save never runs.

The serializer chooses inline form for a short single-line sequence and a fence for multiline source. One editor transaction changes only the selected source range, with the existing stale-write guard and one undo step. Preserve Esc/q/Ctrl+[ behavior from the accepted panel decision; q types in text fields. Reuse Command Mode completion where practical, but avoid making a new completion system a prerequisite for the first release.

## Recurring-task adoption: the actual candidates

The inspected `gtd_daily.md` has two direct-fit chores, one splittable shell workflow, one terminal-only workflow, and six copy-chip prompt references. The direct-fit rows omit the word `bob`, so a search only for backticked `bob …` would miss the most valuable migration. A bounded scan of open recurring task lines outside archives/reference/internal stores found these matches in `gtd_daily.md`; it is not an exhaustive AST inventory of every possible task child. [Inspected note](https://github.com/bobs-org/bob/blob/ba65485844e17bf5f7e353dda2f4913797c4fbd7/gtd_daily.md#L17).

| Existing instruction | Recommended treatment |
| --- | --- |
| `gcal sync -n 2` + `gkeep pull` + `gmail sync` | One `run[Sync inboxes]` chip with three ordered Bob commands. |
| `task reconcile` | One `run[Reconcile tasks]: bob task reconcile` chip. |
| `bob bank import ~/Downloads/*.qfx && rm ~/Downloads/*.qfx` | One import-only command chip; retain explicit cleanup prose after successful import. Never execute `rm` through chips. |
| `bob gcal ack -n 7` with a/n/s review instructions | Keep the terminal instruction; optionally make it a copy chip. Do not imply a run chip can perform the interactive review. |
| `bob periods show …` inside six agent-prompt copy chips | Leave these intact. They are instructions to an agent, not separately runnable actions for the user. |

The Bank nuance is already handled in Bob: `bank import` expands `~` and globs in its own CLI implementation, specifically for shell-free callers. Thus `bob bank import ~/Downloads/*.qfx` is a valid chip candidate without adding plugin-side filesystem expansion. Retain “on the Mac” because Downloads is host-local. Reword cleanup deliberately as “after a successful import, trash the imported QFX files”; do not silently delete a shell step from a supposedly equivalent automated sequence. [Bank CLI](https://github.com/bobs-org/bob-cli/blob/a29a64f63884c9cfa960928c7a2d3c6b48693f36/src/native/bank/cli.rs#L228).

The calendar nuance cannot be solved by catalog membership alone. `gcal ack` is catalogued, but `ack.rs` explicitly refuses an explicit `-n` walk without a TTY unless listing, preview, or JSON mode is selected. Command Mode spawns with stdin ignored. Adding `-l` or JSON would inspect the queue, **not perform the requested interactive acknowledgement**. A native acknowledgement card could later use Bob's noninteractive interfaces; building a pseudo-terminal is disproportionate to this chip feature. [Acknowledgement validation](https://github.com/bobs-org/bob-cli/blob/a29a64f63884c9cfa960928c7a2d3c6b48693f36/src/native/gcal/ack.rs#L143).

Migration should re-read the live vault, preserve unrelated edits and every status/ID/date/repeat field, modify open recurring sources only, and leave completed history and copy payloads alone. Deploy compatible plugins before converting notes. Verify that task parsing, recurring cloning, walk display, and task-title surfaces retain the intended text. Existing copy-chip landing notes already identify raw source appearing in some plain-text task surfaces; do not claim the new chip magically solves that wider rendering problem.

## Requirement adjustments, called out explicitly

1. **Combine the feature under Bob Chips, but defer the internal ID rename.** This retains compatibility at almost no product cost.
2. **“Bulk commands” means a Command Mode sequence of Bob commands.** Shell programs, pipelines, interpolation, interactive terminal sessions, and parallel execution are outside the first release.
3. **Extend the existing Cmd+Enter action instead of assigning a competing hotkey.** Preserve PDF/Gmail/link fallback and distinguish Cmd from Ctrl on macOS. On other platforms use an explicitly configured binding; do not automatically map to Ctrl+Enter, which already has task semantics.
4. **Keep the requested single-chip rule strict.** Multiple candidates refuse, even when one appears runnable and another is invalid. A multi-step chip counts as one candidate.
5. **Migrate semantically eligible instructions, not every `bob` substring.** Preserve agent prompts and the terminal acknowledgement workflow. Split bank import from shell cleanup and document that change.
6. **Success does not check off the task.** Automatic completion or walk advancement would be a separate, riskier feature.
7. **Add full-sequence preflight and stale-source checks.** Persisted executable text merits these stronger entry checks even where the current low-level API is permissive.

## Alternatives and critique

**Command palette favorites or saved sequences:** useful for frequent global commands, but they separate the action from the task explaining when to run it. Chips can also be the portable saved form of an existing Command Mode sequence. A future “Save as command chip” action in the sheet would be a natural extension, not essential to ship.

**A generic button framework or `obsidian://` command link:** adds another grammar, dependency, escaping scheme, or dispatch layer without giving Bob's catalog and sequence semantics for free. It also obscures the useful distinction between navigation and execution. The current code-span family is better aligned with the shipped copy feature.

**Automatic execution on completing a recurring task:** eliminates one gesture but introduces hidden side effects, unclear error behavior, and confusion about whether completion happened before or after a partial batch. Keep running and task completion separate.

**A new shell-capable automation language:** would handle the Bank `rm`, but would sacrifice portability, provenance, and the existing engine contract to solve one cleanup action. Not justified.

**A broad generic chip architecture before shipping:** unnecessary. Share source parsing, serialization, appearance, and authoring where they are already common; retain explicit Copy and Command namespaces. Avoid an extensible registry, per-chip YAML policies, workflow branching, parameters, scheduling, and macros in v1.

The largest product risk is accidental expectation, not difficult rendering: a friendly label can hide substantial writes, and “run” can be mistaken for “finish this chore.” A consistent play glyph, visible exact commands on inspection, the Cmd+Enter hint, and separate completion behavior are essential. The strongest benefit is the morning review: one visible action per chore, with familiar run history and recoverable partial failures.

## Implementation order and evidence needed to ship

This is a suggested order for a later implementation plan, not a task/bead creation request:

1. Add and test the supported Command Mode preparation/execution API, quote-aware command-list parsing, whole-list preflight, single/sequence parity, and execution-state observation.
2. Extend chip grammar, serializer, rendering, and authoring while keeping copy APIs and plugin identity compatible.
3. Integrate command-target resolution into the existing navigation dispatcher and one shared hint model; explicitly test all old Cmd+Enter targets.
4. Verify real Obsidian behavior, deploy compatible plugins, then migrate the eligible recurring tasks and publish documentation/glossary changes.

The implementation belongs mainly in bob-plugins' source fragments. Its generated `main.js` must be rebuilt, not hand-edited. Use the repository's build/check/validation and documentation-inventory checks, then `bob plugins sync` as required by its instructions. No new public Bob subcommand is inherently necessary; any future argv-validation or TTY-capability protocol addition should remain a central Bob/Command Mode decision.

Acceptance coverage should include:

| Area | Required evidence |
| --- | --- |
| Parsing | Labels, escapes, backticks, table pipes, quoted/escaped `&&`, newline lists, empty steps, unclosed fences/quotes, excluded commands, and inert examples/copy payloads. |
| Targeting | One line chip, task fallback, nested-task isolation, multiple chips, invalid plus valid candidates, source mode, multiple selections, and no accidental link fallback on refusal. |
| Execution | Exact argv/policy parity with Ctrl+Enter; no shell; save refusal; queued writer edits; rapid repeat; complete/attention/failure/unknown/stop; partial success; explicit resume; reload without auto-replay. |
| UI | Live Preview and Reading buttons, source reveal, drag selection, focus, reduced motion, light/dark themes, actual hotkey remapping, missing engine, mobile degradation, and source identity in embeds/query results. |
| Compatibility | `gy`, Copy card C, copy authoring, old API clients, PDF opening, Gmail opening, ordinary links, and task Ctrl+Enter retain their contracts. |
| Adoption | Only intended source spans change; repeat fields and statuses survive; next recurrence keeps the chip; sync/reconcile run order is exact; terminal-only acknowledgement remains explicit. |

Research verification completed: **34/34** existing targeted tests passed across `test-command-mode-sequence-engine.cjs`, `test-command-mode-args-vim.cjs`, and `test-copy-chips-grammar.cjs`. A separate harness probe confirmed that `&&` is currently an ordinary argv token and that only completed/attention outcomes continue a sequence. Directly requiring the plugin first failed because Node has no `obsidian` module; the existing repository harness supplies the appropriate fake runtime. These checks establish reuse points, not implementation acceptance.

## Proposed glossary addition

Add `sase/memory/glossary/command-chip.md` during implementation, with title **Command Chip**, canonical keyword `command-chip`, and restrained aliases such as `bob-run`. Do not claim the generic alias `chip`, which the existing Copy Chip entry already uses.

Suggested definition:

> A user-authored action in an Obsidian note, written as a `run:` or `run[LABEL]:` inline code span, or a `bob-run` fence. Its payload names one or more Bob commands. Clicking the chip or using Cmd+Enter on an unambiguous current-line/current-task target runs them through Command Mode with its run-now behavior. Multiple commands form one ordered sequence with the same outcomes, history, output, and recovery as Command Mode. It runs no shell, never runs merely by rendering, and adds no task-completion behavior. A Copy Chip copies literal text; a Command Chip executes an explicit Bob action.

Link Command Mode and Copy Chip using the memory web's link conventions, and link the final plugin documentation. The user's sentence “As a part of this change, we should add a new glossary term for ‘command chip’” supplies the requested scope; a later formal plan should carry the exact original sentence in its memory decision and republish with `sase memory init`. This research proposes the text without prematurely adding documentation for an unshipped feature.

## Recommended solution

Ship a narrow, polished **Bob Chips** extension: explicit `run:` inline chips and `bob-run` cards, a supported Command Mode API for both single commands and ordered sequences, and one context-aware Cmd+Enter dispatcher whose visible hint predicts exactly what will run. Keep `bob-copy-chips` as the internal identity, preserve copy behavior and mobile rendering, and never add a second process engine.

Start with **Sync inboxes**, **Reconcile tasks**, and **Import bank transactions**. Keep the acknowledgement walk in the terminal, preserve copy-chip agent prompts, and retain explicit bank-file cleanup. This delivers the central benefit—acting directly from recurring instructions—while keeping execution, recovery, and the meaning of task completion understandable.
