# A Bob command palette inside Obsidian

Independent research by **cdx**, 2026-10-26. No other report, transcript, or findings from this research swarm were consulted.

## Recommendation in brief

**Build it, as a focused Bob command palette rather than a terminal emulator.** A desktop `bob-commands` plugin should provide a fast searchable launcher, compact argument stages, and a durable run history with complete captured output. Bind `:` in Vim normal mode; retain native Ex access and expose the launcher through Obsidian's ordinary command palette and configurable hotkeys.

The strongest use cases are occasional operations whose terminal names are hard to remember: sync status, reconcile tasks, check references, inspect queued imports, import from Keep, rename a theme, and export the current note as a reading snapshot. For everyday editing, the palette should lead into existing Bob interfaces rather than implement another Task Card or article editor.

The difficult part is not fuzzy search. It is defining exactly what an action does, protecting unsaved notes, and distinguishing **command exited**, **work queued**, **work deferred**, and **work completed**. Bob already has enough infrastructure to make this practical, but it does not have one universal output or execution contract.

## 1. Evidence and limits

I inspected the bob-cli checkout at `e482520841bdc4939290066569d0972f41538287`, the linked bob-plugins checkout at `04c61c78fd854d8f50126d988df0c05304bfd1b1`, the command help of installed `bob 0.3.1`, official Obsidian API declarations, the Vimrc Support source, and primary documentation for subprocesses and accessible pickers. Repository files were opened through `sase repo`. No vault-changing command was run.

This is source and design research, not a tested Obsidian prototype. I did not inspect the live vault's Vimrc or hotkeys, or exercise the UI on Bryan's Mac. Chezmoi's opened source did not contain the Obsidian Vimrc in the filename/content searches performed. Actual installed Vim mappings, Obsidian's bundled Node version, and save/reload behavior require a short integration spike. Performance numbers below are proposed acceptance targets, not measurements.

### Findings that change the design

| Finding | Consequence |
| --- | --- |
| Obsidian already offers fuzzy command search, recent commands, and pins. [W1] | A second palette earns its place through Bob-specific arguments, context, previews, and run history. It should remain reachable from the native palette. |
| Bob's root help and completion share a registry; completion composes a much fuller Clap tree and has dynamic value providers. [C1] | Reuse command metadata and completion internals; do not scrape formatted `--help` or duplicate the command grammar in JavaScript. |
| `docs_catalog()` is a library helper for documentation, not an existing JSON CLI endpoint. The hidden `__complete` interface has shell-specific presentation and silently returns no candidates on some failures. [C1] | Neither is already a ready-made application command catalog. A supported application-facing adapter needs an explicit contract. |
| Plugins already resolve Bob paths and use direct subprocesses. The ledger JSON helper is buffered and decoder-oriented; the article helper is short-lived and has its own bounds. [P1] | Reuse resolution conventions, but build a separate streaming run service for arbitrary-duration user actions. Do not copy the article formatter's 1.5-second deadline. |
| Bob JSON is heterogeneous: capture is unversioned, plan is schema 2, freshness is schema 14, and vault-sync status has no `ok` envelope. [C2] | Normalize results through adapters per command family. Valid JSON, exit zero, and completed user intent are different facts. |
| `plugins list` normally performs a Git pull before comparison. [C3] | The automatic local-status recipe must use `--no-pull`; catalog discovery must not run this command in the background. |
| `task archive` has no dry-run option in the inspected interface. [C3] | Do not invent an archive preview. Add a real preview contract before presenting archive as a preview/apply workflow. |
| Capture of a public URL queues a detached reference job; its command finishes before clipping. The job spool is shared across vaults, and listing JSON does not expose its stored destination vault. [C4] | Say “Queued,” track the returned identity where available, and do not present this spool as a vault-scoped queue. Full background output needs more than the current rotated shared worker log. |
| `ref scan` can exit zero while PDF writes are held; `ref create` can exit successfully with intake queued. Some check/no-op outcomes use nonzero exits. [C5] | Completion notices need meaningful outcome labels and preserved exit details. A universal green/red wrapper will mislead. |
| Bob Articles already plans from the active editor's text and rejects an outdated result before applying an editor transaction. [P2] | “Format current article” should call that existing workflow, not ask a subprocess to rewrite the file behind an unsaved editor. |

## 2. Is a new mode the right idea?

Yes, with a narrower meaning of “mode”: **one temporary action surface, then a return to the note**. This reduces context switching without making Obsidian feel like a terminal application.

There are three useful alternatives:

| Approach | Strength | Limitation | Judgment |
| --- | --- | --- | --- |
| Register a small set of Bob actions in the native command palette | Familiar fuzzy search, existing hotkeys and pins; smallest UI investment | Arguments, previews, history, and full output still require custom surfaces | Good first vertical slice and permanent alternate entry point |
| Configure the Shell commands community plugin | Already exposes shell commands through the palette, with prompts, notifications, and output channels [W2] | Bob-specific result semantics, editor safety, queue following, and drift remain custom work | Good for a handful of personal shortcuts; insufficient as the long-term Bob interface |
| Embed a terminal | Broad command coverage and genuine TTY interaction | Still requires syntax knowledge; poor discovery and contextual argument selection; terminal lifecycle becomes part of Bob | Appropriate only if the real desire is a general terminal |
| Dedicated Bob palette backed by existing CLI and plugin workflows | Discoverable actions, contextual arguments, consistent results, room for polish | Requires catalog metadata, adapters, and lifecycle testing | **Recommended** |

Do not ship an independent action system hidden behind `:`. Register stable Obsidian command IDs for the launcher, run history, last output, and the most useful individual actions. All entry points should call the same action service. Users can pin those commands or assign their own keys.

### Explicit adjustments to the requested requirements

1. **“Any useful Bob command” means broad workflow coverage, not automatic exposure of every executable subcommand.** Every public command family should have an inclusion decision. Migration, service-loop, credential-entry, and protocol-helper commands need not become launcher rows. Unknown commands remain unavailable until their effects are classified.
2. **`:` is scoped to Vim normal mode.** Never consume a colon typed in prose, properties, search fields, forms, or capture drafts. Native Vim Ex remains available through a secondary mapping and a named action.
3. **The product is desktop-first.** Local subprocess execution is not a mobile capability. Do not introduce SSH or a remote execution server merely to preserve the shortcut on mobile.
4. **Completion has more than two outcomes.** In addition to success and failure, show queued, deferred, no change, canceled, and interrupted/unknown where appropriate. Always retain the raw exit code or signal.
5. **“Full output” means complete stdout/stderr of the retained invocation, plus separately identified child-job logs when those exist.** It does not mean that a capture receipt contains the later clip worker's output. Retention must be explicit; the UI must disclose incomplete logs.
6. **Closing the picker or output pane must not stop a run.** Initial release can require Obsidian to remain open. Surviving application exit is a separate execution capability, not something a detached child silently guarantees.
7. **No arbitrary shell input in the initial release.** Expert users can inspect and copy the exact invocation. An advanced argument editor can be added for reviewed commands without enabling pipelines, redirection, command substitution, or arbitrary executable names.

These adjustments preserve the intent while preventing the feature from becoming a second terminal, a second capture grammar, or an unreliable job dashboard.

## 3. Interaction design

### Entry and the colon conflict

Ship a registered `bob-commands:open` action. Make the Bob `:` binding configurable, enabled for Bryan's intended Vim workflow, and use the existing normal-mode Vim integration pattern. The navigation plugin already uses `defineAction`/`mapCommand` and handles adapter replacement for its jump bridge; this is useful precedent, not a guarantee that every mapping lifecycle is already solved. [P3]

Keep this integration isolated from the rest of the palette. Verify that disabling/reloading the plugin restores native behavior without removing another plugin's newer mapping. If the Vim adapter is unavailable, the normal Obsidian command remains usable.

Vimrc Support can invoke Obsidian commands using `obcommand` and aliases via `exmap`, but its README explicitly calls that bridge non-public and documents mapping pitfalls. [W3] Prefer a direct, narrowly scoped Vim action for the colon override; do not blindly map `:` to a sequence beginning with `:` and assume recursion cannot occur. Preserve native Ex through a tested alternate mapping, provisionally `\:`, and a visible “Open Vim command line” action. Keep visual-mode Ex ranges intact. The exact escape mapping is a prototype acceptance item, not a tested snippet in this report.

Avoid a document-wide colon keydown listener. If DOM handling is necessary, use the logical key value, not the US-keyboard assumption `Shift+;`, and reject repeats and composition events. [W4] The test matrix must include pop-out windows, tables, source view, Live Preview, and Vimrc reload.

### Search, selection, and arguments

The first screen is a searchable action list. A row has a human name, a short purpose or target, and the canonical Bob command in secondary monospace text. Searching either vocabulary works: `sync`, `vault-sync`, `bob vault-sync`, `archive`, `keep`, and older names such as `task-status-hooks` should lead to the canonical action.

Use a small fixed set of aliases, token matching across name/path/keywords, then fuzzy scoring. Exact canonical paths and strong word matches outrank recency. Recent actions help an empty query; they must not cause unrelated destructive commands to outrank a precise query. Never run a “best guess” when nothing matches.

The empty state shows a few pinned actions, recent actions, then the full catalog grouped by Bob's workflow sections. Contextual rows such as “Format this article” or “Create reading snapshot of this note” can appear first when applicable. Unavailable matches remain visible with a reason such as “Open a Markdown note” or “Requires a newer bob,” rather than disappearing inexplicably.

Keyboard contract:

| Key | Result |
| --- | --- |
| Up/Down or Ctrl+P/Ctrl+N | Move selection without changing the query |
| Enter | Run a simple ready action, or open its required argument/preview stage |
| Tab | Complete a highlighted command/argument; never execute a write |
| Shift+Tab | Move backward through argument controls |
| Escape / Ctrl+[ | Back one stage; close from the first stage; never cancel an already running job |
| Normal text editing keys | Continue to edit the input normally |

Do not assign `j`, `k`, or `q` as global controls inside text inputs. They are legitimate search and argument characters. Preserve selection by stable action ID when asynchronous context arrives. Once the user navigates, do not reorder the current list underneath them until they change the query.

After choosing an action, show only the missing information: a reference picker, note picker, theme picker, date/range field, or query editor. Defaults come from the context captured when the palette opened; display the note/target explicitly. A later tab switch must not silently retarget the action. Validate again immediately before execution.

Example: `:` → `snapshot` → Enter opens a card with the current note, destination parent, title, and an optional audio toggle. The primary button says **Preview snapshot**, then **Create snapshot** after Bob's preview. Advanced switches stay collapsed.

For capture, route to a dedicated draft stage using Bob's existing parse, complete, rewrite, and dry-run interfaces. Submit the entire draft once. Do not create a new JavaScript interpretation of `=`, `x`, task links, routes, or bulk capture. This extends the existing thin-client principle to Obsidian. [C6]

### Appearance

Use Obsidian's interface font, theme surfaces, accent, border, and radius tokens; Bob's existing picker styles already follow this approach. [P4] The visual identity should come from a small `:` mark, excellent spacing, clear type hierarchy, and restrained color, not another dashboard full of badges.

Proposed dimensions: about 660 px wide on a desktop, bounded by `min(92vw, 660px)`, with a stable search header and approximately eight visible rows. Use 48–56 px rows with one secondary line. Reserve monospace for command paths and raw output. A selected row gets the theme's selection tint and a narrow accent edge. Show write/network details in the selected row's detail area rather than every row.

```text
┌──────────────────────────────────────────────────────────┐
│  :  Bob                                      History   ↗ │
│  Search commands…                                        │
├──────────────────────────────────────────────────────────┤
│  Sync vault                                              │
│  Pull and push vault changes          bob vault-sync run │
│                                                          │
│  Check sync status                                       │
│  Last cycle and conflicts          bob vault-sync status │
│                                                          │
│  Preview task reconciliation                             │
│  Inspect derived status changes    bob task reconcile -d │
├──────────────────────────────────────────────────────────┤
│  ↑↓ select       Tab complete       Enter open/run   Esc  │
└──────────────────────────────────────────────────────────┘
```

This is a layout sketch, not a rendered or tested mockup. Narrow windows stack details; long labels wrap or expose the full value on focus. Respect reduced motion, visible keyboard focus, and text scaling. Use icon plus text for state, never color alone. Announce the selected item and final outcome without reading every line of streaming output. The combobox/listbox model is a useful accessibility starting point. [W5]

## 4. Command coverage

The catalog should distinguish **report**, **local edit**, **maintenance**, **external effect**, and **opens an existing interface**. These categories inform behavior, not a wall of warning badges.

### Everyday actions: prioritize these

| User-facing action | Existing command or workflow | Presentation / important detail |
| --- | --- | --- |
| Capture… | `bob capture` plus `capture-*` helpers | Dedicated draft stage; preserve the draft on error; explicit submission |
| Start next Pomodoro | `bob capture '='` | Show the actual target; use Bob's preview and result |
| Finish / adjust Pomodoro… | Capture's existing close and duration syntax | Guided input and preview; no invented `pomodoro start/stop` subcommands |
| Show Pomodoro status | `bob pomodoro status` | Empty stdout can legitimately mean no active session |
| Show today's plan | `bob plan -f json` | Readable summary and links; raw JSON remains available |
| Show review queue / Continue review | `bob freshness list -f json` / existing review-walk action | Distinguish a report from advancing the existing walk |
| Show crowded notes / This note's Ready lane | `bob ready` / `bob ready <NOTE>` | Read-only; avoid check mode for normal browsing |
| Show statistics… | `bob stats overview`, `show`, `metrics` | Range/metric controls; link to the existing Stats surface where useful |
| Show projects | `bob projects list` | Navigate to project notes from results |
| Find / browse references | `bob ref find`, `list`, `show` | Reference picker and existing Reading Board where it already serves the goal |
| Read this reference today… | `bob ref today` | Choose a Pomodoro using its stale-safe ref; this does not start the session |
| Sync vault / Check sync status | `bob vault-sync run`; `status --json` | Explicit write/network action versus a status report |
| Preview / Reconcile task status | `bob task reconcile --dry-run`; live command | Show scope; let Bob own locking, retries, and derived status rules |
| Manage Pomodoro themes | `bob themes list/hide/unhide/color/rename` | Reuse the existing manager; rename shows Bob's exact preview |
| Manage relation labels | `bob relations list/hide/unhide/rename` | Reuse existing manager; preserve history-wide rename semantics |
| Format / Convert current article | Existing Bob Articles commands | Delegate to editor-aware planner/apply workflow |
| Open Task Card / Move this task… | Existing navigation and move workflows | Preserve selection, undo, freshness, dependency, and review-walk semantics |

These rows are action families, not a requirement to display dozens of near-identical top-level entries. For example, “Manage themes” can lead to the existing manager while direct “Rename theme…” remains searchable.

### Less frequent but genuinely useful actions

| Action | Coverage recommendation |
| --- | --- |
| Create a reference from URL/PDF/Markdown | `ref create`, with explicit parent and target; show intake queued versus filed; audio is optional and may be long-running |
| Create a reading snapshot of this note | High-value contextual recipe for `ref create`; select sections, title, parent, and preview using Bob's actual contract |
| Rename a reference | `ref rename` dry-run then apply; show affected paths and identity changes from the current contract |
| Inspect reference import jobs | `ref jobs list`; label **This computer, all vaults** until vault filtering is supported |
| Process pending reference jobs | `ref jobs run`; advanced action with explicit all-vault scope; it is not “retry only this selected job” |
| File queued PDFs | `ref scan --intake-only`; distinguish remaining queued work from a total failure |
| Scan Highlights / Sync one PDF | `ref scan`, `ref sync`; show actual hook/network/write behavior; do not automatically add `--attended` or `--write-pdfs` |
| Diagnose references / Inspect PDF marker | `ref doctor`, `ref marker`; text output is acceptable; do not fabricate JSON flags |
| Inspect Keep inbox / Diagnose Keep | `gkeep list`, `gkeep doctor`; indicate network use; vault-only listing is a separate local recipe |
| Import Keep inbox | `gkeep pull` preview and apply; explain that verified notes are archived in Keep; explicit parent avoids a hidden TTY prompt/default |
| Inspect / Sync project metadata | `projects list`, `projects sync --dry-run` and apply; offer reconciliation afterward because project sync calls it out separately |
| Move tasks between notes | Existing plugin workflow for current tasks; `task move` adapter for explicit source/target selections, preview, and bulk operations |
| Re-roll due prioritized tasks | `task reroll --dry-run`, then apply with the preview's seed and options; re-preview if the input set changed |
| Archive completed tasks | Useful but advanced. Add a real preview contract before the polished workflow; until then show an explicit threshold/scope confirmation, never a fictional dry-run |
| Inspect / Format articles in bulk | `articles list`, `outline`, `format --check/--dry-run`; all-note apply is maintenance, unlike the current-note editor action |
| Run a Dataview / Tasks query | `query`, with a multiline editor, explicit origin, native engine by default, and structured output; never run code merely because a result displays it |
| Inspect plugin versions / Preview deployment | `plugins list --no-pull`; `plugins sync --no-pull --dry-run` for a local preview; make refresh from Git explicit |
| Deploy plugins | Advanced `plugins sync` workflow with changes previewed. Separate deployment from reload, especially when replacing the running commands plugin |
| Nightly maintenance | Advanced explicit action. Show the real sequence: sync, archive, articles, sync; partial completion needs a stage report |
| Saved capture templates | Surface through the capture stage using `capture-templates list/show/save/delete`; clearing all templates requires explicit confirmation |
| Show Bob version / Command help / Diagnose executable path | Local support actions; full help remains available even for unsupported action adapters |

All commands in these tables were identified from the current CLI registry, help, and contracts. [C1–C7] They need per-action capability checks; this table is a coverage decision, not a claim that every adapter already exists.

### Deliberately excluded from ordinary search

- `completion install/uninstall/bash/zsh`: shell setup does not become more useful inside the note editor. Expose help or diagnostics only if a concrete need appears.
- `pomodoro tmux` and the long-running `pomodoro notify` loop: these are presentation/service integrations, not interactive palette jobs.
- Hidden aliases as duplicate rows, the one-time freshness seed, and `ref`/`gkeep` migration commands: expert maintenance remains explicit and separate.
- `gkeep login`: credentials and cookie exchange should not enter searchable command history or captured logs.
- `capture-parse`, `capture-rewrite`, `capture-task-id`, and similar helper endpoints as independent user choices: they support a workflow; some also write. Helpers are not uniformly read-only. [C2]
- Force/overwrite/merge switches as defaults, arbitrary executable paths entered into the search field, and execution triggered by links or text inside notes/output.

Do not hide these exclusions behind an unsafe “Run anything” escape hatch. A supported advanced argument editor can later cover unusual options of reviewed commands while retaining the same result and effect rules.

## 5. Results, notifications, and full output

### One run record, several useful views

Every execution receives a run ID before launch. Persist command ID, resolved executable/version, argv, working directory, vault identity, start/end timestamps, exit code/signal, result classification, and paths to raw stdout/stderr. Store enough context to explain the target; avoid recording the entire process environment.

A plugin-owned RunService lives longer than any modal or view. It publishes updates to:

1. A small status-bar indicator while jobs are active.
2. A completion notice with **View output**.
3. A searchable **Bob Runs** history and a reusable Obsidian output pane.

Read-only reports open a result pane immediately because their output is the purpose of the action. For writes, return focus to the note after launch; notify on completion without stealing focus. Success notices can expire after about five seconds. Failures or deferred work leave a persistent unread indicator and a longer notice, not a permanently growing pile of toasts. Keyboard users can always invoke **Open last Bob output**.

The output pane has a short summary, the exact invocation and target, elapsed time, and **Output / Errors / Details** controls. Offer copy command, copy visible output, save complete log, search, wrap, and a deliberate run-again action. Rerun resolves current context or clearly uses the recorded target; it never silently replays a destructive action with stale arguments.

Capture raw stdout and stderr independently. A combined timeline can preserve observed chunk order, but must not claim a perfect global ordering across separate pipes. Render output as text; do not interpret arbitrary Markdown/HTML or terminal escape commands. Structured adapters can provide explicit validated note links and a human summary alongside the raw data.

### Outcome rules

| Evidence | User-facing result |
| --- | --- |
| Exit 0, adapter confirms requested work complete | Completed |
| Exit 0, no applicable work | No changes / No active Pomodoro, as appropriate |
| Exit 0, capture created a background ref job | Queued; follow its job identity separately |
| Exit 0, PDF write held / intake queued | Deferred, with the actual reason and next action |
| A documented check exit, e.g. `ready --check` code 3 | Check complete: crowded notes found; retain exit 3 in details |
| Typed `unchanged` result from hide/color | No change; preserve the nonzero code rather than inventing a process success |
| Other nonzero exit, spawn error, malformed expected output | Failed or unrecognized result, with stdout/stderr and recovery guidance |
| Process ends by requested cancellation | Canceled; do not claim rollback unless the command confirms it |
| Obsidian disappears before an authoritative terminal record | Interrupted / outcome unknown; inspect state before offering retry |

Do not infer success from an `ok` string, the absence of stderr, or valid JSON alone. Conversely, stderr often carries progress and warnings, not failure. [C2, C5]

### Queued reference imports need an explicit boundary

The current ref job spool is useful existing infrastructure, but it is not a generic command runner. Its `worker.log` combines jobs and rotates; its listing has host-wide scope. [C4] Never use it as proof that a particular command's full later output was retained.

Initial implementation can truthfully notify “Capture completed; reference queued” and expose the existing job report. To promise a later per-import completion notice plus complete output, add additive CLI support for a stable job receipt, destination-vault metadata/filtering, terminal lookup by ID, and a per-job retained log. Track only jobs launched by this action surface unless the user deliberately opens the broader job browser. An `already_queued` result needs correlation to an existing job, not a fabricated new run.

This follow-through is a requirement for the fully polished URL-capture workflow. It should not block simpler commands from shipping, nor be silently treated as already solved.

## 6. Architecture and reliability

### Ownership

Create a small desktop plugin, provisionally `bob-commands`, in the bob-plugins source repository. Its responsibilities are catalog presentation, argument UI, context capture, the subprocess boundary, run history, and notifications. Keep it independent of the large navigation plugin. Feature-detect optional plugin APIs; unavailable dependencies produce useful disabled rows.

Bob remains authoritative for capture grammar, task semantics, reference identity, locks, previews, writes, and recovery. Existing editor workflows remain authoritative for their in-memory transactions. Prefer versioned cross-plugin APIs to imports of generated `main.js` or direct calls to private methods. [P5]

For existing UI actions whose current registered callback returns no meaningful result, add a small additive API that resolves a typed outcome. “Opened Task Card” is a launch event, not proof that a task mutation succeeded. Do not add a second completion toast over a workflow that already owns its feedback.

### Catalog: generated syntax plus curated semantics

Add a supported, read-only catalog endpoint in bob-cli, provisionally `bob commands list -f json`. The group membership would be “descriptors for Bob actions exposed to interactive clients”; the bare group can default to its read-only list. The name is proposed, not existing.

Derive canonical paths, aliases, help, option definitions, and value kinds from the existing registry/completion tree. Add a deliberately reviewed recipe layer for UI labels, parameter choices, effects, preview behavior, output adapter, cancellation policy, and minimum capabilities. The fact that Clap describes a flag does not reveal whether it archives remote data or starts a worker.

A descriptor could contain:

```json
{
  "schema_version": 1,
  "id": "task.reconcile.preview",
  "label": "Preview task reconciliation",
  "command_path": ["task", "reconcile"],
  "fixed_args": ["--dry-run", "--format", "json"],
  "effects": ["read_vault"],
  "result_adapter": "task_reconcile",
  "cancel_policy": "read_only",
  "requires": ["desktop", "vault"]
}
```

This is an illustrative proposal, not a complete schema. Runtime catalog responses must remain metadata-only: opening the palette should not scan the whole vault, fetch URLs, pull Git, or start commands. Cache by resolved executable identity/version, refresh after replacement, and reject incompatible schema versions with a repair action.

Keep presentation overlays and optional Obsidian-only workflow actions in the plugin. Add a catalog coverage test requiring every new public command family to be classified as supported, advanced, helper, or excluded. This closes the maintenance gap without automatically exposing new writes.

Dynamic argument providers can reuse Bob's completion internals through a separately versioned request/response adapter. Do not couple the UI to a shell's tab-delimited presentation or hide provider errors as an empty list. Start with the existing domain JSON endpoints where they already fit.

### Process boundary

- Resolve an explicit configured Bob path, then known installation locations, then PATH, consistent with existing plugins. Verify that the chosen file is executable; show the resolved path and version in diagnostics. A wrong explicit path should produce an actionable error, not silently choose another binary.
- Use asynchronous `spawn(executable, argv, {shell: false, ...})`. Never interpolate shell command strings or invoke a login shell. Node's documentation distinguishes direct process creation from shell execution and explains buffered-output limits. [W6]
- Set the working directory and `BOB_DIR` from the actual filesystem-backed vault. Do not fall back to `~/bob` when the active vault cannot be resolved. Suppress color for raw machine output. Audit inherited Bob test/day/path overrides rather than accidentally letting `BOB_NOW`, `BOB_DAY_FILE`, or a script-fallback variable retarget a GUI action.
- Pass text through argv or a defined stdin protocol; close stdin after the request. Arbitrary stdin prompts are unsupported. Check action-specific prerequisites before starting jobs that might invoke Git, rendering tools, or audio utilities.
- Drain stdout and stderr continuously, write them to files, and keep only a bounded visible tail in memory. Use streaming decoding so UTF-8 split across chunks remains intact. Huge output must not freeze the editor or kill a healthy job merely because a callback buffer filled.
- Settle a run once after the subprocess has closed its streams; preserve spawn errors, exit code, and signal separately. Late events must not deliver duplicate terminal notices. [W6]

Store history/logs in a host-local application state directory keyed by vault, outside synced notes and plugin source files. Suggested initial policy: retain completed runs for 14 days with a configurable storage budget, pin/export useful records, never prune an active run, and show when an older log has expired. If logging fails or storage fills during execution, surface “output incomplete” and stop accepting additional jobs until repaired; do not silently call a truncated display the full output or abruptly kill a vault mutation to enforce a UI quota.

### Writes, locks, and unsaved buffers

Use one frontend mutation queue per vault, with limited parallel read-only reports. This prevents accidental duplicate launches and confusing local overlap. Bob's existing locks still arbitrate against timers, CLI invocations, other plugins, and other Obsidian windows; the frontend queue is not a substitute.

Do **not** acquire Bob's maintenance lock in JavaScript around a child that acquires the same lock. That creates self-deadlock. Preserve the command's own retry budget and show “Waiting for vault maintenance” when a typed signal supports it; otherwise use a truthful generic running state.

Current-note actions should prefer existing editor-aware APIs. For external maintenance, flush relevant open Markdown views with supported save methods and verify they have not changed during preflight. A save failure must prevent the write. A vault-wide action may require saving every open affected view, including pop-outs.

Saving once is not a concurrency solution: the user can type while a child is planning. Bob's snapshot guards and recovery remain necessary. New adapters need a demonstrated safe policy for active targets: editor transaction, bounded read-only protection during the actual write, or refusal when the relevant buffer changes. Do not promise global safety for every CLI writer just because some writers are guarded. Test archive, project sync, and other older paths individually before granting the same “safe to run while editing” behavior as newer transaction-based writers.

A preview is not a durable authorization token over a mutable vault. Record its inputs and targets; preserve reroll seeds; revalidate on apply; refresh the preview when the meaningful plan changes. Do not label every CLI action undoable: only offer revert information when the command actually created an appropriate scoped commit. Capture, editor undo, and transaction commits have different recovery semantics.

### Cancellation and application lifecycle

Closing the UI only unsubscribes it. A long run stays visible in status/history. Use short bounded timeouts for metadata and read-only previews; maintenance needs its own budget. A slow network operation is not necessarily hung.

Offer cancellation only where the adapter has a defined policy. Read-only processes are straightforward; write operations may have committed partial work or spawned children. “Request stop” must not imply rollback. Avoid automatic SIGKILL escalation during writes unless the CLI explicitly supports interruption/recovery at that point.

Persist completed records atomically. On reload, incomplete run records become “outcome unknown” until checked; never decide that a reused PID proves the old run is alive, and never automatically replay an uncertain mutation. Deployment of the commands plugin itself must finish and persist its receipt before offering reload.

Do not build a resident daemon in the first release. If runs must survive application exit with authoritative completion and later output, introduce a small CLI-owned run supervisor with durable receipts and logs, not a detached process with inherited UI pipes. That capability can be daemonless and shared by future clients, but it is additional product scope.

## 7. A sensible delivery sequence and acceptance criteria

First prove the riskier boundaries with a narrow vertical slice: normal-mode `:`, native Ex escape, a plan report, sync status, reconcile preview/apply, and a deliberately failing fake Bob process. Include the output pane and logs from the beginning. A launcher that lacks completion history cannot validate the central user requirement.

Then expand through the catalog above: planning/stats/reference browsing, editor workflow delegates, sync and maintenance, then the richer capture and import lifecycle. Introduce only the minimum CLI adapters needed by each slice. Do not begin by converting every Bob command to one new output protocol.

The feature is ready when these behaviors are demonstrated:

| Area | Acceptance evidence |
| --- | --- |
| Discovery | `sync`, `keep`, `ref`, `task-status-hooks`, and canonical CLI paths find the expected action; no unsupported write becomes executable merely because its name matches |
| Responsiveness | Target warm open below 100 ms and local filtering below 30 ms with a representative catalog; no subprocess spawned per search keystroke |
| Keyboard | Insert-mode colons remain text; normal-mode colon opens once; native Ex and visual ranges remain available; Escape restores the original selection and focus |
| Context | Switching notes while an argument form is open does not retarget it; renamed/deleted targets are revalidated; stale Pomodoro refs fail safely |
| Execution | Paths containing spaces, quotes, `$()`, and backticks remain literal arguments; stdout/stderr over 1 MiB and split Unicode are retained correctly |
| Result semantics | Exit 0 with queued/held work, nonzero check/no-op outcomes, malformed JSON, ENOENT, signal termination, and empty successful output produce distinct truthful results |
| Lifecycle | Closing/reopening the palette retains the run; duplicate Enter is single-flight; app reload leaves an honest unknown state; plugin deployment cannot lose its own receipt |
| Data safety | Save failures, edits during preview/apply, active-note formatting undo, lock contention, and concurrent external maintenance are exercised on synthetic vaults |
| Import lifecycle | Capture receipt is distinguished from clip completion; all-vault job scope is visible; full child output is promised only when per-job logging exists |
| Presentation | Light/dark themes, small windows, larger text, reduced motion, screen-reader selection announcements, and keyboard-only access to output all work |

Use synthetic vaults and fake Bob executables for deterministic integration tests, plus manual smoke tests on the actual supported Obsidian/OS combination. Source/build, plugin inventory, and documentation checks remain part of implementation. Changes belong in bob-plugins and deploy through `bob plugins sync`; a future CLI catalog or output-contract change also needs Bob's generated help and contract documentation. This report itself does not modify or deploy either product.

## 8. Sources

Repository citations identify the inspected revisions, not moving branch heads. They are included as links for review; repository contents were read from the authorized local checkouts.

- **[C1] CLI inventory and completion:** [runner registry and docs_catalog](https://github.com/bobs-org/bob-cli/blob/e482520841bdc4939290066569d0972f41538287/src/runner.rs), [completion tree](https://github.com/bobs-org/bob-cli/blob/e482520841bdc4939290066569d0972f41538287/src/native/completion/tree.rs), [completion runtime](https://github.com/bobs-org/bob-cli/blob/e482520841bdc4939290066569d0972f41538287/src/native/completion/mod.rs).
- **[C2] Machine-readable contracts:** [JSON outputs](https://github.com/bobs-org/bob-cli/blob/e482520841bdc4939290066569d0972f41538287/docs/reference/json-outputs.md).
- **[C3] Current command contracts:** [task commands](https://github.com/bobs-org/bob-cli/blob/e482520841bdc4939290066569d0972f41538287/docs/reference/cli/task.md), [plugins](https://github.com/bobs-org/bob-cli/blob/e482520841bdc4939290066569d0972f41538287/docs/reference/cli/plugins.md), [full CLI reference directory](https://github.com/bobs-org/bob-cli/tree/e482520841bdc4939290066569d0972f41538287/docs/reference/cli). Read-only `--help` invocations additionally checked ref scan/today/doctor/jobs, projects sync, gkeep pull, vault-sync run, and articles format.
- **[C4] Asynchronous imports:** [ref jobs](https://github.com/bobs-org/bob-cli/blob/e482520841bdc4939290066569d0972f41538287/docs/ref-jobs.md), [reference recovery guide](https://github.com/bobs-org/bob-cli/blob/e482520841bdc4939290066569d0972f41538287/docs/guides/recover-reference-job.md).
- **[C5] Partial and deferred outcomes:** [Highlights sync](https://github.com/bobs-org/bob-cli/blob/e482520841bdc4939290066569d0972f41538287/docs/highlights-ref-sync.md), [reference creation](https://github.com/bobs-org/bob-cli/blob/e482520841bdc4939290066569d0972f41538287/docs/highlights-create.md), [Ready CLI](https://github.com/bobs-org/bob-cli/blob/e482520841bdc4939290066569d0972f41538287/docs/reference/cli/ready.md), [theme writes](https://github.com/bobs-org/bob-cli/blob/e482520841bdc4939290066569d0972f41538287/src/native/pomodoro_themes/write.rs).
- **[C6] Capture semantics and ownership:** [capture contract](https://github.com/bobs-org/bob-cli/blob/e482520841bdc4939290066569d0972f41538287/docs/capture.md); audited memory reads of `decisions:mac-capture-is-a-thin-client` and the Capture/Pomodoro/freshness/link/relation glossary strands. The accepted thin-client decision specifically governs Mac Capture; applying the same ownership split here is a recommendation.
- **[C7] Effects and workflow constraints:** [vault Git sync](https://github.com/bobs-org/bob-cli/blob/e482520841bdc4939290066569d0972f41538287/docs/vault-git-sync.md), [Keep integration](https://github.com/bobs-org/bob-cli/blob/e482520841bdc4939290066569d0972f41538287/docs/gkeep.md), [reference workflows](https://github.com/bobs-org/bob-cli/blob/e482520841bdc4939290066569d0972f41538287/docs/ref.md); audited memory reads of `obsidian.md`, `cli_rules.md`, `docs.md`, and `decisions:relation-label-rename-rewrites-history`.
- **[P1] Existing subprocess boundaries:** [ledger Bob JSON helper](https://github.com/bobs-org/bob-plugins/blob/04c61c78fd854d8f50126d988df0c05304bfd1b1/plugins/bob-ledger-tools/src/236-plugin-stats-data.js), [article path resolver](https://github.com/bobs-org/bob-plugins/blob/04c61c78fd854d8f50126d988df0c05304bfd1b1/plugins/bob-articles/src/020-article-core.js).
- **[P2] Editor-aware article operations:** [article plugin](https://github.com/bobs-org/bob-plugins/blob/04c61c78fd854d8f50126d988df0c05304bfd1b1/plugins/bob-articles/src/030-plugin.js), [article UI documentation](https://github.com/bobs-org/bob-plugins/blob/04c61c78fd854d8f50126d988df0c05304bfd1b1/docs/bob-articles.md).
- **[P3] Existing Vim integration:** [navigation mappings and jump bridge](https://github.com/bobs-org/bob-plugins/blob/04c61c78fd854d8f50126d988df0c05304bfd1b1/plugins/bob-navigation-hotkeys/src/620-plugin-dash-and-vim-jumps.js).
- **[P4] Existing visual language:** [picker stylesheet](https://github.com/bobs-org/bob-plugins/blob/04c61c78fd854d8f50126d988df0c05304bfd1b1/plugins/block-id-prompt/styles.css).
- **[P5] Integration boundaries:** [cross-plugin APIs](https://github.com/bobs-org/bob-plugins/blob/04c61c78fd854d8f50126d988df0c05304bfd1b1/docs/develop/plugin-apis.md).
- **[W1] Obsidian native palette:** [official command palette help](https://obsidian.md/help/plugins/command-palette).
- **[W2] Existing shell integration alternative:** [Shell commands author's documentation](https://publish.obsidian.md/shellcommands/Index).
- **[W3] Vim command bridging:** [Vimrc Support README at inspected revision](https://github.com/esm7/obsidian-vimrc-support/blob/1ff5d97afcf3161f202aa460697233d550f6aa3f/README.md), [implementation](https://github.com/esm7/obsidian-vimrc-support/blob/1ff5d97afcf3161f202aa460697233d550f6aa3f/main.ts).
- **[W4] Keyboard event semantics:** [MDN KeyboardEvent.key](https://developer.mozilla.org/en-US/docs/Web/API/KeyboardEvent/key), [keydown and IME composition](https://developer.mozilla.org/en-US/docs/Web/API/Element/keydown_event).
- **[W5] Accessible selection interaction:** [WAI-ARIA combobox pattern](https://www.w3.org/WAI/ARIA/apg/patterns/combobox/).
- **[W6] Process execution and stream lifecycle:** [Node.js child_process documentation](https://nodejs.org/api/child_process.html). Verify the actual APIs against Obsidian's embedded runtime; do not assume the latest Node documentation is its shipped version.
- **[W7] Official Obsidian API:** [obsidian.d.ts at inspected revision](https://github.com/obsidianmd/obsidian-api/blob/9abd9605ce081383674aae1ed111c456edde0688/obsidian.d.ts). `SuggestModal`, `FuzzySuggestModal`, `Modal.scope`, selection restoration, `Notice` with a DocumentFragment, persistent notice duration, `ItemView`, and command registration provide the building blocks. Use a native `SuggestModal`/`FuzzySuggestModal` for the action stage and a `Modal` for richer argument stages; avoid private suggestion internals. Check the project's minimum Obsidian version before using newer APIs.

## 9. Recommended solution

Implement **Bob Commands** as a small desktop plugin with a native-feeling fuzzy palette, normal-mode `:`, guided action stages, and a persistent output/history pane. Support the broad command families above through explicit recipes, and delegate existing editor workflows to their current owners. Add a lightweight CLI catalog derived from the existing command tree, with curated effect and result metadata; use direct streaming subprocesses and per-family outcome adapters.

The first release should prove the complete select → run → notify → inspect-output loop with planning, sync, and reconciliation. Expand to capture and imports with honest queued/deferred states, adding per-job correlation and logs before promising background completion output. Keep native Ex available, keep ordinary typing untouched, and defer a general shell or application-independent supervisor until usage demonstrates the need. This delivers the user's core goal with an interface that is quick, calm, and trustworthy.
